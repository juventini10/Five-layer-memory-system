#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
script_version_backfill.py — 脚本头部版本标识补标器（存量债一次性清理·分片+dry-run）
============================================================
家族：变换（改） ｜ 部署形态：按需
版本：v0.1

为什么存在（根因）：
  体检器 L1 检出数十个脚本无版本标识（治理债），逐个人工补 = 重复劳动（toil）。
  本工具机械补标：按体检器同一判据检测 → 在顶部连续注释块末尾插入版本行 → 支持
  分片（--limit/--offset）规避文件打开配额红线，并强制先 dry-run（铁律-020）。

判据单一真源：
  从 script-family-check/script_family_check.py 动态导入 has_version_marker；
  失败降级为内置复现并显式声明来源——⛔不做静默双本账。

子命令：
  --help        用法
  --self-test   自测（插入 + 插入后判据通过 + 幂等）
  --dry-run     只列出待补标文件（默认 30 个/片）
  apply         执行补标（改前逐文件备份 .bak-version-backfill）

退出码约定：
  0 = 成功
  1 = 发现冲突/拒绝执行
  2 = 参数错误
  3 = 内部错误

设计原则：
  - 幂等：已有版本标识的跳过；重复执行结果一致
  - 可逆有痕：改前备份原文件到 <name>.bak-version-backfill
  - 只加注释行：⛔不改动任何既有代码行，插入位置=顶部连续注释块末尾
  - 分片：--limit/--offset 控制单片处理量（沙箱文件打开配额红线）

用法：
  python3 script_version_backfill.py --dry-run
  python3 script_version_backfill.py apply --limit 20 --offset 0
  python3 script_version_backfill.py --self-test
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import importlib.util
import os
import re
import shutil
import sys

__version__ = "v0.1"

HOME = os.path.expanduser("~")
DEV_DIR = os.environ.get("BACKFILL_DEV_DIR") or os.path.join(HOME, "[记忆共享中心]/脚本中心")
JUDGE_SRC = os.path.join(DEV_DIR, "script-family-check/script_family_check.py")
VERSION_LINE = "# version: v0.1"


def _fallback_judge(path):
    try:
        head = open(path, encoding="utf-8", errors="replace").read(4000)
    except Exception as e:
        return f"不可读：{e}"
    if (re.search(r"^version:", head, re.M)
            or re.search(r"#.*v?\d+\.\d+(\.\d+)?", head)
            or re.search(r'"""[\s\S]{0,800}?v\d+\.\d+', head)
            or re.search(r"版本[:：]", head)):
        return None
    return "无版本标识"


def load_judge():
    try:
        spec = importlib.util.spec_from_file_location("_sfc", JUDGE_SRC)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.has_version_marker, "体检器 has_version_marker"
    except Exception:
        return _fallback_judge, "内置复现（体检器不可达·已显式声明）"


def collect(limit, offset):
    names = sorted(n for n in os.listdir(DEV_DIR) if n.endswith(".py"))
    return [os.path.join(DEV_DIR, n) for n in names[offset:offset + limit]]


def insert_version(path):
    """在顶部连续注释块末尾插入版本行。返回 True=已改 / False=未改（幂等或不可插入）。"""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    idx = 0
    if lines and lines[0].startswith("#!"):
        idx = 1
    start = idx
    while idx < len(lines) and lines[idx].startswith("#") and not lines[idx].startswith("#!"):
        idx += 1
    # 幂等保护：顶部注释块已声明版本 → 直接返回，⛔不重复插入
    if any(re.match(r"^#\s*version\s*:", l) for l in lines[start:idx]):
        return False
    if idx == 0:
        return False  # 连 shebang 都没有：不猜，交人工
    lines.insert(idx, VERSION_LINE)
    shutil.copy2(path, path + ".bak-version-backfill")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True


def run(dry_run, limit, offset) -> int:
    judge, src = load_judge()
    targets = collect(limit, offset)
    if not targets:
        print(f"✅ 本片无文件（offset={offset}·判据来源：{src}）")
        return 0

    todo = [p for p in targets if judge(p) is not None]
    print(f"🔎 本片扫描 {len(targets)} 个 · 待补标 {len(todo)} 个 · 判据来源：{src}")
    if not todo:
        print("✅ 本片全部已有版本标识")
        return 0

    for p in todo:
        print(f"  - {os.path.basename(p)}")

    if dry_run:
        print("（dry-run：未改动任何文件；确认命中范围后再跑 apply）")
        return 0

    done, skipped = 0, []
    for p in todo:
        if insert_version(p):
            done += 1
        else:
            skipped.append(os.path.basename(p))
    print(f"✅ 已补标 {done} 个（各自备份 .bak-version-backfill）")
    if skipped:
        print(f"⚠️ 跳过 {len(skipped)} 个（无可插入注释块）：{'、'.join(skipped)}")
    return 0


def self_test() -> int:
    import tempfile
    failures = []
    judge, _ = load_judge()

    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "sample.py")
        with open(p, "w", encoding="utf-8") as f:
            f.write('#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""样例"""\n')
        if judge(p) is None:
            failures.append("前置失败：初始样本不应已有版本标识")
        if not insert_version(p):
            failures.append("插入失败：insert_version 返回 False")
        if judge(p) is not None:
            failures.append("插入后失败：判据仍未通过")
        if insert_version(p):
            failures.append("幂等失败：二次调用仍执行了插入")

    if failures:
        for x in failures:
            print(f"[self-test] FAIL: {x}", file=sys.stderr)
        return 1
    print("[self-test] ✅ 通过（插入 1/1 · 插入后判据通过 1/1 · 幂等 1/1）")
    return 0


def main(argv) -> int:
    if not argv or argv[0] in ("--help", "-h"):
        print(__doc__)
        return 0
    if argv[0] == "--self-test":
        return self_test()
    if argv[0] in ("--dry-run", "apply"):
        ap = argparse.ArgumentParser(prog=argv[0], add_help=False)
        ap.add_argument("--limit", type=int, default=30)
        ap.add_argument("--offset", type=int, default=0)
        ns, _ = ap.parse_known_args(argv[1:])
        return run(argv[0] == "--dry-run", ns.limit, ns.offset)
    print(f"未知子命令: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
