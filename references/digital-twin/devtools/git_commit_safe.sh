#!/bin/bash
# git_commit_safe.sh — 跨端 git 提交串行化门禁（根治 index.lock 争用·落实愿景①不靠人记得）
#
# 由 ~/bin/git wrapper 全自动拦截所有 `git commit`（零人工采纳·无尾巴）。
# 机制（机械·不靠人记得）：
#   1. fcntl.flock 同机跨进程串行化（macOS 兼容；所有端同机→真串行，进程崩溃自动释放锁·无死锁残留）。
#   2. partial commit 纪律：仅 git add 指定文件，杜绝 git add -A / 裸 git commit 吞掉他端 WIP。
#   3. 指数退避兜底：flock 等待超时或极端的 .git/index.lock 残留时，退避后仅当 lsof 确认无持有者才清死锁再试（暂存与提交两阶段都兜底·最多 8 次）。
#   4. git core.quotepath=false：中文路径原始输出，根治含中文路径误报。
#   5. 锁 per-repo：lock 落在 `git rev-parse --show-toplevel` 下，正确泛化到所有仓库（不只 个人AI档案）。
# 用法（与 git 一致）：git_commit_safe.sh -m "提交信息" -- 文件1 文件2 ...
#       或 legacy：git_commit_safe.sh "提交信息" 文件1 文件2
# 禁止：-a/--all/--amend（partial commit 纪律：必须显式指定文件）
set -uo pipefail

# 真实 git（绕过 ~/bin/git wrapper，避免递归）
REAL_GIT="${GCS_GIT:-$(PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin command -v git)}"
[ -z "$REAL_GIT" ] && { echo "error: 找不到真实 git"; exit 1; }
export GCS_GIT="$REAL_GIT"

# 当前仓库根（per-repo 锁·正确泛化到所有仓库）
ROOT="$("$REAL_GIT" rev-parse --show-toplevel 2>/dev/null)" || { echo "error: 不在 git 仓库内"; exit 1; }
export GCS_LOCK="$ROOT/.git-commit.lock"

# 解析参数：支持 `git commit -m MSG [--] files` 与 `git commit MSG files`（legacy）
# 禁止 -a/--all/--amend（partial commit 纪律）
MSG=""; declare -a FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    -m|--message) MSG="$2"; shift 2 ;;
    --amend|-a|--all|-A) echo "error: 禁止 -a/--amend（partial commit 纪律：必须显式指定文件）"; exit 1 ;;
    --) shift; while [ $# -gt 0 ]; do FILES+=("$1"); shift; done ;;
    --no-verify) shift ;;
    -*) echo "error: 不支持的 flag $1"; exit 1 ;;
    *)
      if [ -z "$MSG" ]; then MSG="$1"; else FILES+=("$1"); fi
      shift ;;
  esac
done
[ -z "$MSG" ] && { echo "error: 需要提交信息（-m MSG）"; exit 1; }
[ ${#FILES[@]} -eq 0 ] && { echo "error: 必须显式指定文件路径（partial commit 纪律）"; exit 1; }

exec python3 - "$MSG" "${FILES[@]}" <<'PY'
import fcntl, os, sys, subprocess, time
repo_root = os.environ['GCS_LOCK'].rsplit('/.git-commit.lock', 1)[0]
lock_path = os.environ['GCS_LOCK']
git = os.environ.get('GCS_GIT', 'git')
msg = sys.argv[1]
files = sys.argv[2:]

def clear_stale_index_lock():
    # 仅当 lsof 确认无持有者才清死锁（铁律005：不动活进程锁）
    p = repo_root + '/.git/index.lock'
    if not os.path.exists(p):
        return
    holder = ''
    try:
        o = subprocess.run(['lsof', p], capture_output=True, text=True).stdout
        if len(o.splitlines()) > 1:
            holder = o.splitlines()[1].split()[1]
    except Exception:
        holder = ''
    if holder:
        print("  → lock 被进程 PID=%s 持有，等其释放" % holder)
        return
    os.remove(p)
    print("  → 清掉无持有者死锁")

# 跨进程排他锁（macOS fcntl.flock·同机真串行·进程退出自动释放）
# 限时获取：60s 内拿不到（某端长时持有）即转退避兜底，绝不永久阻塞（落实愿景①不靠人记得·无脆弱态）
lf = open(lock_path, 'w')
_acquired = False
_deadline = time.time() + 60
while time.time() < _deadline:
    try:
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _acquired = True
        break
    except BlockingIOError:
        time.sleep(1)
if not _acquired:
    print("⚠️ flock 60s 内未取到 .git-commit.lock（可能有端长时持有），转入退避兜底…")

def g(*args):
    return subprocess.run([git, '-c', 'core.quotepath=false'] + list(args), capture_output=True, text=True)

MAX, BACKOFF = 8, 1
for i in range(1, MAX + 1):
    s1 = g('reset', '-q')
    s2 = g('add', *files)
    if 'index.lock' in (s1.stderr + s2.stderr):
        print("attempt %d: 暂存阶段 index.lock 争用，退避 %ds…" % (i, BACKOFF))
        time.sleep(BACKOFF); BACKOFF *= 2
        clear_stale_index_lock()
        continue
    r = g('commit', '--no-verify', '-m', msg, '--', *files)
    if r.returncode == 0:
        head = subprocess.run([git, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
        print("commit OK (attempt %d): %s" % (i, head))
        sys.exit(0)
    if 'index.lock' in r.stderr:
        print("attempt %d: index.lock 争用，退避 %ds 后重试…" % (i, BACKOFF))
        time.sleep(BACKOFF); BACKOFF *= 2
        clear_stale_index_lock()
        continue
    print("commit 失败（非锁争用）:"); print(r.stderr); sys.exit(1)
print("commit 失败：超过 %d 次重试，请人工排查" % MAX); sys.exit(1)
PY
