#!/usr/bin/env python3
"""
path_migration_sweep_guard.py — 批量路径/改名迁移残留扫查闸（三明治裁决B·闸1·v1.0）

病根（2026-10-06 同日实证·同批施工 5 处误伤）：
  批量路径迁移产生 `~//Users/...` 双斜杠形态，expanduser 展开为
  /Users/<user>//Users/<user>/... 幽灵路径。当天 4 处 P0（注入器×3行/G2门禁×2行/
  裁决台账×2行/档位守卫×1行）+ symlink_guard.sh 整件 + 幽灵树 /Users/<user>/Users/
  全由此生。深度审计漏 2 处、10 分钟模式扫查全获——故同源律立第五维：
  「批量迁移必须附全仓模式残留扫查，残留=非零退出」（triwich FU-138·seal 965057b1）。

三模式：
  --gate       pre-commit 口径：只扫本轮 staged delta（归因律——新增行拦·预存行打印不拦，
               对齐 md_table_shape_guard 口径）+ 幽灵树实存检查（恒查）
  --full       收口扫查口径：全仓文本扫（收口/施工批次收尾时人工或流程调用）
  --self-test  自检：临时注入病灶样例→检测→清理→报结果（G2 验证方法1的机械化）

v1 诚实边界：
  - 只做模式扫描 + 幽灵树实存（纯机械判据）；"expanduser 读路径实存验证"留 v2
    （需要读路径白名单设计，否则合法的"运行时创建目录"会假红——Agent B G2 缺口⑤
    指向的 manifest hash 是端副本完整性的正解，本闸不越位）。
  - 豁免清单须带理由与日期（S151：流转启动不豁免实录闸——豁免≠静默）。

退出码：残留/病灶 >0 → exit 1（清单+修法）；清白 → exit 0（写心跳）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import sys
import json
import fnmatch
import subprocess
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

__version__ = "v1.0"

REPO_ROOT = Path(os.path.expanduser("[记忆共享中心]"))
EXEMPT_FILE = REPO_ROOT / "开发工具" / "path_migration_sweep_exemptions.json"
HEARTBEAT = REPO_ROOT / "开发工具" / "logs" / "path_migration_sweep.heartbeat"
SELF = Path(__file__).name

# ── 病灶模式（v1）──
# P1 双斜杠tilde：expanduser("~/x//y") → /Users/<u>/x//y（P0 家族的全部形态）
BAD_PATTERN = "~//"
# P3 幽灵树：/Users/<user>/Users/ 目录实存 = 历史写入事故产物在盘
def ghost_tree_root() -> Path:
    # v1.1(2026-10-07 Qoder CN·platform_compat检查①红清偿)：幽灵树是macOS /Users 事故产物，
    # pwd 为 Unix-only 裸导入在 Windows 必崩；非Darwin 返回不可能路径=检查恒空等价跳过
    if not sys.platform.startswith("darwin"):
        return Path(os.devnull) / "no-ghost-tree-non-darwin"
    import pwd
    user = pwd.getpwuid(os.getuid()).pw_name
    return Path(f"/Users/{user}/Users")

# 扫描的文本扩展名（--full 用；--gate 对 staged 全类型文本扫）
TEXT_EXTS = {".py", ".sh", ".yaml", ".yml", ".json", ".md", ".plist", ".txt",
             ".html", ".js", ".ts", ".rb", ".pl", ".toml", ".cfg", ".ini"}
# --full 排除目录
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "__pycache__", "logs"}
# 单文件大小上限（--full 防大文件拖垮）
MAX_BYTES = 1_000_000


def load_exemptions():
    """豁免清单：[{path, reason, since}]——path 相对仓根，fnmatch 匹配。"""
    if not EXEMPT_FILE.exists():
        return []
    try:
        data = json.loads(EXEMPT_FILE.read_text(encoding="utf-8"))
        return data.get("exemptions", [])
    except Exception as e:
        print(f"⚠️ 豁免清单解析失败（按无豁免处理·Fail-Closed）: {e}", file=sys.stderr)
        return []


def is_exempt(rel_path: str, exemptions) -> bool:
    for ex in exemptions:
        if fnmatch.fnmatch(rel_path, ex.get("path", "")):
            return True
    return False


def scan_lines(path: Path, source_label: str):
    """单文件扫描，返回命中行 [(lineno, line_text)]。"""
    hits = []
    try:
        if path.stat().st_size > MAX_BYTES:
            return hits
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return hits
    for i, line in enumerate(text.splitlines(), 1):
        if BAD_PATTERN in line:
            hits.append((i, line.strip()[:120]))
    return hits


def staged_new_lines(repo: Path):
    """staged delta 的新增行号映射 {relpath: set(lineno)}——归因律判据。"""
    new_lines = {}
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--no-color"],
            cwd=repo, capture_output=True, text=True, timeout=30,
        ).stdout
    except Exception:
        return new_lines
    cur = None
    new_start = new_count = 0
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:]
            new_lines.setdefault(cur, set())
        elif line.startswith("@@"):
            # @@ -a,b +c,d @@  → 新侧从 c 起 d 行
            try:
                plus = line.split("+")[1].split("@@")[0]
                c, _, d = plus.partition(",")
                new_start = int(c)
                new_count = int(d) if d.strip() else 1
                if new_count > 0 and cur:
                    new_lines[cur].update(range(new_start, new_start + new_count))
            except Exception:
                continue
    return new_lines


def staged_files(repo: Path):
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--no-color"],
            cwd=repo, capture_output=True, text=True, timeout=30,
        ).stdout
        return [l.strip() for l in out.splitlines() if l.strip()]
    except Exception:
        return []


def check_ghost_tree(roots):
    """幽灵树实存检查（恒查·机械判据：目录存在即病灶产物）。"""
    g = ghost_tree_root()
    findings = []
    if g.exists():
        files = list(g.rglob("*"))[:5]
        findings.append(("幽灵树", str(g),
                         f"历史双斜杠写入事故产物在盘（含 {len(list(g.rglob('*')))} 项·样例 {files[:2]}）。"
                         f"修法：整棵 mv 进废纸篓（铁律005 trash 不 rm）→ 复跑回清白"))
    return findings


def run_gate():
    """pre-commit 口径：staged delta 扫描（新增行拦·预存行打印）+ 幽灵树恒查。"""
    exemptions = load_exemptions()
    blocking, warned, exempted = [], [], 0
    new_lines = staged_new_lines(REPO_ROOT)
    for rel in staged_files(REPO_ROOT):
        p = REPO_ROOT / rel
        if not p.is_file() or is_exempt(rel, exemptions) or p.name == SELF \
                or rel == EXEMPT_FILE.name or p.suffix not in TEXT_EXTS:
            continue
        for lineno, text in scan_lines(p, rel):
            if lineno in new_lines.get(rel, set()):
                blocking.append((rel, lineno, text))
            else:
                warned.append((rel, lineno, text))
    ghost = check_ghost_tree(None)
    for rel, lineno, text in warned:
        print(f"⚠️ [迁移扫查·预存态不拦·归因律] {rel}:{lineno}: {text}")
    if exempted or exemptions:
        pass  # 豁免计数在 full 模式报
    if blocking or ghost:
        print("🔴 [迁移扫查闸·pre-commit] 本轮暂存 delta 存在批量路径迁移残留：")
        for rel, lineno, text in blocking:
            print(f"   ❌ {rel}:{lineno}: {text}")
        for kind, loc, hint in ghost:
            print(f"   ❌ [{kind}] {loc}\n      {hint}")
        print("   修法：还原该行到 HEAD 已知好形态（git show HEAD:<file>）；")
        print("         确属合法样例（夹具/注释）→ 登记豁免 path_migration_sweep_exemptions.json（带理由+日期）。")
        print("   ⛔勿 --no-verify 绕过。")
        return 1
    _beat(len(staged_files(REPO_ROOT)))
    return 0


def run_full():
    """收口扫查口径：全仓文本扫 + 幽灵树恒查。豁免命中显形计数（不静默）。"""
    exemptions = load_exemptions()
    blocking, exempted = [], 0
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            rel = str(p.relative_to(REPO_ROOT))
            if p.suffix.lower() not in TEXT_EXTS or p.name == SELF \
                    or rel == str(EXEMPT_FILE.relative_to(REPO_ROOT)):
                continue
            ex_hit = is_exempt(rel, exemptions)
            hits = scan_lines(p, rel)
            if not hits:
                continue
            if ex_hit:
                exempted += len(hits)
                reason = next((e.get("reason", "") for e in exemptions
                               if fnmatch.fnmatch(rel, e.get("path", ""))), "")
                print(f"🟡 [豁免·留痕] {rel} × {len(hits)} 行 · 理由: {reason}")
            else:
                blocking.extend((rel, ln, t) for ln, t in hits)
    ghost = check_ghost_tree(None)
    if blocking or ghost:
        print(f"🔴 [迁移扫查闸·全仓] 残留 {len(blocking)} 行 + 幽灵树 {len(ghost)} 处：")
        for rel, lineno, text in blocking:
            print(f"   ❌ {rel}:{lineno}: {text}")
        for kind, loc, hint in ghost:
            print(f"   ❌ [{kind}] {loc}\n      {hint}")
        print("   修法：还原到 HEAD 已知好形态；合法样例→登记豁免（带理由+日期，S151 留痕律）。")
        _beat(0)
        return 1
    print(f"✅ [迁移扫查·全仓] 清白（豁免显形 {exempted} 行·幽灵树 0）")
    _beat(exempted)
    return 0


def run_self_test():
    """G2 验证方法1机械化：临时注入病灶→检测→清理→报结果。"""
    ok = True
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad_sample.py"
        bad.write_text('P = os.path.expanduser("~//Users/x/个人AI档案/y.md")\n', encoding="utf-8")
        hits = scan_lines(bad, "bad_sample.py")
        if not hits:
            print("❌ 自检：病灶样例未被检出（模式失明）"); ok = False
        good = Path(td) / "good_sample.py"
        good.write_text('P = os.path.expanduser("[记忆共享中心]/y.md")\n', encoding="utf-8")
        if scan_lines(good, "good_sample.py"):
            print("❌ 自检：合法路径被误报（模式过宽）"); ok = False
        if not ghost_tree_root.__name__:
            ok = False
    g = ghost_tree_root()
    print(("✅" if ok else "❌") + f" [迁移扫查·自检] 模式检出/无误报{'/幽灵树当前不存在' if not g.exists() else '/⚠️幽灵树在盘'}")
    return 0 if ok else 1


def _beat(scanned: int):
    try:
        HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT.write_text(json.dumps(
            {"ts": datetime.now().isoformat(timespec="seconds"),
             "mode_self": __version__, "staged_or_exempt": scanned},
            ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--gate"
    if mode == "--gate":
        return run_gate()
    if mode == "--full":
        return run_full()
    if mode == "--self-test":
        return run_self_test()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
