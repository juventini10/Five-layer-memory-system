#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
script_compliance_gate.py — 脚本合规门禁（版本标识 + 在册性 · 只拦变更集）
============================================================
家族：守卫（守） ｜ 部署形态：按需
版本：v0.1

为什么存在（根因）：
  脚本体系生成端已有骨架（预防），缺事中拦截（防御）。本门禁复用体检器同一版本判据，
  对指定文件集做阻断式校验，把'看得见'升级为'过不去'（对齐自动化六环之④自动防御）。

判据单一真源：
  版本标识判据从 script-family-check/script_family_check.py 动态导入 has_version_marker；
  导入失败时降级为内置复现，并在输出中显式声明所用来源——⛔不做静默双本账。

子命令：
  --help                 用法
  --self-test            负例自测（放行侧 + 拦截侧双向）
  check --recent N       校验最近 N 分钟修改的脚本（默认 60）
  check --files A B ...  校验指定文件集

退出码约定：
  0 = 全合规（或变更集为空）
  1 = 存在不合规（无版本标识 / 未入册）
  2 = 参数错误
  3 = 内部错误

设计原则：
  - 只拦变更集：⛔不扫全库（存量债豁免·S572 门禁密度按回收轴分档）
  - 失败可辨：异常与非合规走不同退出码，⛔不静默吞错
  - 自测双向：正常样本放行 + 造错样本被拦（C-007 守卫负例测试）
  - 宁可假阳性不可假阴性（漏报比误报危险），输出分级防疲劳
  - 失败默认放行（仅供挂 hook 时使用；手动/门禁模式如实返回退出码）

用法：
  python3 script_compliance_gate.py --self-test
  python3 script_compliance_gate.py check --recent 60
  python3 script_compliance_gate.py check --files a.py b.py
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import importlib.util
import json
import os
import re
import sys
import time

__version__ = "v0.1"

HOME = os.path.expanduser("~")
DEV_DIR = os.environ.get("GATE_DEV_DIR") or os.path.join(HOME, "[记忆共享中心]/脚本中心")
MANIFEST = os.environ.get("GATE_MANIFEST") or os.path.join(DEV_DIR, "scripts_manifest.json")
JUDGE_SRC = os.path.join(DEV_DIR, "script-family-check/script_family_check.py")


def _fallback_judge(path):
    """内置复现（仅在体检器不可达时启用）。"""
    try:
        head = open(path, encoding="utf-8", errors="replace").read(4000)
    except Exception as e:
        return f"不可读：{e}"
    if (re.search(r"^version:", head, re.M)
            or re.search(r"#.*v?\d+\.\d+(\.\d+)?", head)
            or re.search(r'"""[\s\S]{0,800}?v\d+\.\d+', head)
            or re.search(r"版本[:：]", head)):
        return None
    return "无版本标识（头部/docstring/frontmatter 均未声明）"


def load_judge():
    """版本判据单一真源：优先体检器，失败降级内置。返回 (fn, 来源标签)。"""
    try:
        spec = importlib.util.spec_from_file_location("_sfc", JUDGE_SRC)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.has_version_marker, "体检器 script_family_check.has_version_marker"
    except Exception:
        return _fallback_judge, "内置复现（体检器不可达·已显式声明）"


def load_registered():
    with open(MANIFEST, encoding="utf-8") as f:
        return {s["name"] for s in json.load(f)["scripts"]}


def collect(recent_min, files):
    if files:
        return [os.path.abspath(p) for p in files]
    cut = time.time() - recent_min * 60
    out = []
    for fn in sorted(os.listdir(DEV_DIR)):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(DEV_DIR, fn)
        if os.path.isfile(p) and os.path.getmtime(p) >= cut:
            out.append(p)
    return out


def check(recent_min=60, files=None) -> int:
    judge, src = load_judge()
    try:
        registered = load_registered()
    except Exception as e:
        print(f"❌ 清单不可读：{e}", file=sys.stderr)
        return 3

    targets = collect(recent_min, files)
    if not targets:
        print(f"✅ 门禁通过（变更集为空·判据来源：{src}）")
        return 0

    bad = []
    for p in targets:
        name = os.path.basename(p)
        reasons = []
        why = judge(p)
        if why:
            reasons.append(why)
        if name not in registered:
            reasons.append("未入册 scripts_manifest")
        if reasons:
            bad.append((name, reasons))

    print(f"🔎 门禁扫描变更集 {len(targets)} 个 · 判据来源：{src}")
    if not bad:
        print("✅ 全部合规")
        return 0

    print(f"🔴 发现 {len(bad)} 个不合规：")
    for name, reasons in bad:
        print(f"  - {name}：{'；'.join(reasons)}")
    return 1


def self_test() -> int:
    """负例自测：放行侧 + 拦截侧双向（缺一侧 = 假绿灯）。"""
    import tempfile
    failures = []
    judge, _ = load_judge()

    with tempfile.TemporaryDirectory() as td:
        sample = os.path.join(td, "sample.py")
        with open(sample, "w", encoding="utf-8") as f:
            f.write('#!/usr/bin/env python3\n# version: v0.1\n"""合格样本"""\n')
        if judge(sample) is not None:
            failures.append("放行侧失败：合格样本被判不合规")

        with open(sample, "w", encoding="utf-8") as f:
            f.write('#!/usr/bin/env python3\n"""没有版本标识的样本"""\n')
        if judge(sample) is None:
            failures.append("拦截侧失败：无版本标识样本被放过")

    if failures:
        for x in failures:
            print(f"[self-test] FAIL: {x}", file=sys.stderr)
        return 1
    print("[self-test] ✅ 双向断言通过（放行侧 1/1 · 拦截侧 1/1）")
    return 0


def main(argv) -> int:
    if not argv or argv[0] in ("--help", "-h"):
        print(__doc__)
        return 0
    if argv[0] == "--self-test":
        return self_test()
    if argv[0] == "check":
        ap = argparse.ArgumentParser(prog="check", add_help=False)
        ap.add_argument("--recent", type=int, default=60)
        ap.add_argument("--files", nargs="*", default=None)
        ns, _ = ap.parse_known_args(argv[1:])
        return check(ns.recent, ns.files)
    print(f"未知子命令: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
