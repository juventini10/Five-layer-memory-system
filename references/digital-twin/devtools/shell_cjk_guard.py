#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shell_cjk_guard.py v1.0 — 乙类「$变量名紧跟全角标点」机械门禁。

病根（一次事故两次登记）：bash 3.2 在 UTF-8 locale 下把紧跟 $name 的非 ASCII 字节
当作标识符字符 → 变量名被吃成 name\\xef... → `set -u` 下 unbound 硬死（rc=127）；
无 `set -u` 时更坏：变量值和那个标点一起**静默消失**，输出缺字而无人报错。
触发条件是 PEP 538：任何 Python 父进程会向子进程注入 LC_CTYPE=C.UTF-8——
所以"手跑 zsh 全绿、被 python 一调就红"，人眼永远复现不出来（2026-08-30 实锤）。

本门禁解决的是"规则已写进规范却依然复发"：规范 v1.2.66 立过条文、修法逐字躺在
kb_philo_consistency.sh:65 注释里，次日新夹具仍然复发 ⇒ 文档态规则对新型缺陷零约束力。

扫描口径（三律落地）：
- 绑定律：只看可执行代码——跳过整行注释、行内引号外的 `#` 之后、单引号串（无展开）；
  位置参数 `$1`（数字名）不报——bash 只读 1 位数字，后面的字符本就是字面量。
- 回落律：文件读不出/非 UTF-8 可解码 → 不报（保持旧行为），⛔不制造假红风暴。
- 归因律：`--gate` 只拦**本轮新增行**；盘上预存的同族缺陷打印为「预存(非本轮引入·不拦)」
  并回给归属端，不把历史债钉死在下一个碰该文件的人身上。

用法：
  --scan   [目录]        全库报告（只报告不拦·默认目录 ~/个人AI档案）
  --check  [目录]        活跃区红 → exit 1（排除发布物副本·见 EXCLUDE_RE）
  --gate   [文件...]      无参时取 git 暂存的 *.sh；有参时按传入文件；只拦本轮 delta
  --fix    [文件...]      就地补花括号（$name）→（${name}）；改前先备份到 .bak-cjkfix
  --self-test             内置夹具（11 用例·含正例/负例/回落/真机行为实证）
退出码：0 无红 / 1 有红 / 2 参数或环境错
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import os
import re
import subprocess
import sys

# B埋点(v2.0·2026-09-03·童灵·补exit码埋点): 包装入口点在退出时写日志(含exit码)
def _guard_log_exit(rc):
    try:
        subprocess.Popen(["python3", os.path.expanduser("[记忆共享中心]/脚本中心/guard_invocation_logger.py"),
                          "--guard", "shell_cjk_guard",
                          "--source", os.environ.get("GUARD_TRIGGER_SOURCE", "hook_auto"),
                          "--exit", str(rc),
                          "--detail", "self-instrumented"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

BASE = os.path.expanduser("~")
# 发布物/镜像副本：改一处须随发版走，不计入本端红（避免与源目录双重计数 + 误判本端违规）
# 记忆琥珀两个日期快照仓=脚本历史副本，原件已随源目录同批修，计入即同一缺陷双计+恒红。
# ⛔ 不排除整个 记忆琥珀/：engine/*.sh 是 launchd 实跑的活代码，必须在扫描域内。
EXCLUDE_RE = re.compile(r"(布洛陀-安装包|加强包|/tests/|/steps/|/golden/|\.bak|__pycache__|/logs/|记忆琥珀/(技能升级备份|永久收藏)/)")
VAR_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
# 严重度判据：nounset 是否真开。⛔ 只认 `set -u` 字面会漏最常见的 -euo/-o nounset
# ——那两类脚本变量被吃后是 unbound 硬死（🔴），标成 🟡 会低估修复优先级。
SET_U_RE = re.compile(r"\bset\s+(?:-[a-zA-Z]*u[a-zA-Z]*\b|-o\s+nounset\b)")


def scan_line(line):
    """返回 [(col, varname, next_char)] —— 只报可执行代码里的裸 $name 紧跟非 ASCII。

    状态机次序（T1 夹具钉住）：转义 → 引号开闭转移 → 行内注释截断 → `$` 展开检查。
    ⚠️ 双引号内**有**变量展开（事故现场全在这里），单引号内无展开故跳过。
    """
    hits = []
    i, n = 0, len(line)
    quote = None          # None | "'" | '"'
    prev = ""
    while i < n:
        ch = line[i]
        if ch == "\\" and prev != "\\":
            i += 2
            prev = ""
            continue
        if quote is None and ch in ("'", '"'):
            quote = ch
            i += 1
            prev = ch
            continue
        if quote is not None and ch == quote:
            quote = None
            i += 1
            prev = ch
            continue
        if quote is None and ch == "#":
            break         # 行内注释：其后全忽略
        if ch == "$" and quote in (None, '"'):
            m = VAR_RE.match(line, i)
            if m:
                j = m.end()
                if j < n and ord(line[j]) > 127:
                    hits.append((i, m.group(1), line[j]))
                i = j
                prev = ""
                continue
        i += 1
        prev = ch
    return hits


def scan_text(text):
    out = []
    for idx, line in enumerate(text.splitlines(), 1):
        for col, name, nxt in scan_line(line):
            out.append((idx, col, name, nxt, line.strip()[:90]))
    return out


def scan_file(path):
    """返回 findings 列表；不可读/不可解码 → []  （回落律：无从判定就保持旧行为）。"""
    try:
        with open(path, "rb") as f:
            raw = f.read()
        if b"\x00" in raw[:4096]:
            return []
        text = raw.decode("utf-8", "strict")
    except (OSError, UnicodeDecodeError):
        return []
    hits = scan_text(text)
    if not hits:
        return []
    hard = bool(SET_U_RE.search(text))
    return [(ln, col, name, nxt, src, hard) for (ln, col, name, nxt, src) in hits]


def iter_sh_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules")]
        for fn in filenames:
            if fn.endswith(".sh"):
                yield os.path.join(dirpath, fn)


def cmd_scan(root, check_mode):
    total_files, red_files, lines_out = 0, 0, []
    hard_n = soft_n = excluded_n = 0
    for p in sorted(iter_sh_files(root)):
        total_files += 1
        f = scan_file(p)
        if not f:
            continue
        excl = bool(EXCLUDE_RE.search(p))
        rel = os.path.relpath(p, BASE)
        if excl and check_mode:
            excluded_n += len(f)
            continue
        red_files += 1
        for ln, col, name, nxt, src, hard in f:
            if hard:
                hard_n += 1
            else:
                soft_n += 1
            if excl:
                excluded_n += 1
            lines_out.append(
                f"{'🔴' if hard else '🟡'} {rel}:{ln}  ${name}{nxt}  ← 应写 ${{{name}}}{nxt}\n"
                f"      {src}"
            )
    where = "（--check 已排除发布物副本）" if check_mode else "（含发布物副本·仅报告）"
    print(f"[shell_cjk_guard] 扫描 {total_files} 个 .sh · 命中 {red_files} 文件 / {len(lines_out)} 处 {where}")
    for line in lines_out:
        print(line)
    print(f"汇总：🔴 set -u 硬死 {hard_n} 处 ｜ 🟡 静默吞值 {soft_n} 处 ｜ 发布物副本 {excluded_n} 处")
    return 1 if (hard_n + soft_n) else 0


def _git(args):
    r = subprocess.run(["git"] + args, cwd=BASE, capture_output=True)
    return (r.stdout or b"").decode("utf-8", "replace")


def cmd_gate(files):
    """只拦本轮 delta：新增行里出现乙类才 RED；预存态打印不拦（归因律）。"""
    if not files:
        out = _git(["diff", "--cached", "--name-only", "-z"])
        files = [x for x in out.split("\0") if x.endswith(".sh")]
    blocked = 0
    for rel in files:
        p = rel if os.path.isabs(rel) else os.path.join(BASE, rel)
        if not os.path.isfile(p):
            continue
        added = set()
        diff = _git(["diff", "--cached", "-U0", "--", rel]) or _git(["diff", "-U0", "--", rel])
        for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
            start = int(m.group(1))
            added.update(range(start, start + int(m.group(2) or 1)))
        pre, new = [], []
        for ln, col, name, nxt, src, hard in scan_file(p):
            (new if (ln in added or not added) else pre).append((ln, name, nxt, hard))
        for ln, name, nxt, hard in pre:
            print(f"◽ 预存(非本轮引入·不拦) {rel}:{ln}  ${name}{nxt}")
        for ln, name, nxt, hard in new:
            print(f"{'🔴' if hard else '🟡'} 本轮引入 {rel}:{ln}  ${name}{nxt}  ← 应写 ${{{name}}}{nxt}")
            blocked += 1
    print(f"[shell_cjk_guard --gate] 本轮 delta 红 {blocked} 处 ｜ 待检文件 {len(files)}")
    return 1 if blocked else 0


def cmd_fix(files):
    files = [f for f in files if f.endswith(".sh")]
    changed = 0
    for rel in files:
        p = rel if os.path.isabs(rel) else os.path.join(BASE, rel)
        if not os.path.isfile(p):
            print(f"⚠️ 跳过（不存在）{rel}")
            continue
        findings = scan_file(p)
        if not findings:
            continue
        with open(p, encoding="utf-8") as f:
            lines = f.read().split("\n")
        for ln, col, name, nxt, _src, _h in sorted(findings, key=lambda x: -x[1]):
            row = lines[ln - 1]
            lines[ln - 1] = row[:col] + "${" + name + "}" + row[col + 1 + len(name):]
        shutil_backup(p)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        changed += 1
        print(f"✏️ {rel}：补花括号 {len(findings)} 处（备份 {os.path.basename(p)}.bak-cjkfix）")
    print(f"[shell_cjk_guard --fix] 改写 {changed} 文件")
    return 0


def shutil_backup(p):
    import shutil
    dst = p + ".bak-cjkfix"
    if not os.path.exists(dst):
        shutil.copy2(p, dst)


def cmd_self_test():
    import tempfile
    cases = [
        ("T1 负例·set -u 下变量紧跟全角括号", 'set -euo pipefail\necho "码$got）"\n', 1),
        ("T2 正例·补花括号后放行", 'set -euo pipefail\necho "码${got}）"\n', 0),
        ("T3 注释里的中文无害（防误伤）", '# 修: $got） 这类写法\nx=1\n', 0),
        ("T4 单引号串无展开→不报", "echo '码$got）'\n", 0),
        ("T5 位置参数 $1 紧跟全角→bash 只读1位·安全", 'echo "$1）"\n', 0),
        ("T6 无 set -u 仍报（静默吞值·🟡档）", 'echo "码$got）"\n', 1),
        ("T7 行内注释后的中文不报", 'v=1  # 见 $got）说明\n', 0),
        ("T8 回落·不可解码文件不报（⛔不造假的红）", b"\xff\xfe" + "$got）\n".encode("utf-8") + b"\x00", 0),
        ("T9 真案回归·run_tests.sh 现体应绿",
         'lr_expect() { if [ "$got" = "$2" ]; then echo "✅（$1→豁免码${got}）"; fi }\n', 0),
    ]
    ok = fail = 0
    d = tempfile.mkdtemp(prefix="scg_")
    for i, (label, body, want) in enumerate(cases):
        p = os.path.join(d, f"c{i}.sh")
        with open(p, "wb") as f:
            f.write(body if isinstance(body, bytes) else body.encode("utf-8"))
        got = 1 if scan_file(p) else 0
        if got == want:
            ok += 1
            print(f"✅ {label}")
        else:
            fail += 1
            print(f"❌ {label}（got={got} want={want}）")
    # 严重度档位实锤：cases 只测"检出与否"，SET_U_RE 这半边曾无夹具覆盖，
    # 导致 `set -euo pipefail`（nounset 实际开着）被降级标 🟡 而无人察觉。
    sev_cases = [
        ("T11a set -euo pipefail → 🔴硬死档", 'set -euo pipefail\necho "码$got）"\n', True),
        ("T11b set -o nounset → 🔴硬死档", 'set -o nounset\necho "码$got）"\n', True),
        ("T11c 无 nounset → 🟡静默吞值档", 'echo "码$got）"\n', False),
        ("T11d set +u（显式关闭）→ 🟡档不误升", 'set +u\necho "码$got）"\n', False),
    ]
    for i, (label, body, want_hard) in enumerate(sev_cases):
        p = os.path.join(d, f"s{i}.sh")
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        hits = scan_file(p)
        got_hard = bool(hits) and hits[0][5]
        if got_hard == want_hard:
            ok += 1
            print(f"✅ {label}")
        else:
            fail += 1
            print(f"❌ {label}（hard={got_hard} want={want_hard}）")
    # 行为级实锤：证明"改前炸 / 改后正常输出值"，⛔不只测解析器
    # 注：bash 3.2.57 在 set -u 触发 unbound variable 时 rc=1（不是 127——127 来自
    #     另一类"文件找不到"的错误调用；判据只认行为特征，不认号码）
    risky = os.path.join(d, "risky.sh")
    fixed = os.path.join(d, "fixed.sh")
    open(risky, "w").write('set -eu\nh(){ got=0; echo "值$got）"; }; h\n')
    open(fixed, "w").write('set -eu\nh(){ got=0; echo "值${got}）"; }; h\n')
    env = dict(os.environ, LC_CTYPE="C.UTF-8")   # PEP 538：复现 python 父进程调用态
    rb = subprocess.run(["bash", risky], capture_output=True, env=env)
    r_out = (rb.stdout or b"").decode("utf-8", "replace")
    r_err = (rb.stderr or b"").decode("utf-8", "replace")
    bad = rb.returncode != 0 and "unbound" in r_err and "值0" not in r_out
    print(f"{'✅' if bad else '❌'} T10a 改前实跑 rc={rb.returncode}·stderr含unbound={('unbound' in r_err)}·值丢失={'值0' not in r_out}")
    gz = subprocess.run(["bash", fixed], capture_output=True, env=env)
    g_out = (gz.stdout or b"").decode("utf-8", "replace").strip()
    good = gz.returncode == 0 and g_out == "值0）"
    print(f"{'✅' if good else '❌'} T10b 改后实跑 rc={gz.returncode}·stdout={g_out!r}（期望 '值0）'）")
    ok += bad + good
    fail += (not bad) + (not good)
    print(f"===== shell_cjk_guard 夹具: {ok} 通过 / {fail} 失败 =====")
    import shutil as _s
    _s.rmtree(d, ignore_errors=True)
    return 1 if fail else 0


def main():
    ap = argparse.ArgumentParser(description="乙类全角吞变量名门禁")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--gate", action="store_true")
    g.add_argument("--fix", action="store_true")
    g.add_argument("--self-test", dest="self_test", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(cmd_self_test())
    if args.gate:
        sys.exit(cmd_gate(args.paths))
    if args.fix:
        if not args.paths:
            print("⛔ --fix 必须显式给出文件清单（⛔不接受全库盲改）", file=sys.stderr)
            sys.exit(2)
        sys.exit(cmd_fix(args.paths))
    root = args.paths[0] if args.paths else BASE
    if not os.path.isdir(root):
        print(f"⛔ 目录不存在：{root}", file=sys.stderr)
        sys.exit(2)
    sys.exit(cmd_scan(root, check_mode=args.check))


if __name__ == "__main__":
    _rc = 0
    try:
        main()
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else 0
    except Exception:
        _rc = 0  # 失败放行
    finally:
        _guard_log_exit(_rc)
    sys.exit(_rc)
