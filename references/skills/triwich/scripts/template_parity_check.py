#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""template_parity_check.py — 结论块模板同构位齐闸（v1.0·2026-10-21·皮叔令「L1/L2/L3 每层都要改·要统一」）

TRUTH_OF: 模板同构位清单与必备件清单唯一真源=本文件常量（⛔不在别处复制清单）。
判据：每个模板位文件必含全部必备 token；缺任一件=FAIL（exit 1）。
覆盖：SKILL 共用模板 + L1×3 + L2 + L3 骨架 + 结果块示例（11 处同构族的机检面）。
用法：python3 scripts/template_parity_check.py [--skill-root DIR]
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import io, os, sys, argparse

FILES = [
    "SKILL.md",
    "references/l1/first-principles.md",
    "references/l1/abstraction.md",
    "references/l1/critical-verify.md",
    "references/l2/dual-routes.md",
    "references/l3/full-flow.md",
    "references/shared/result-block-examples.md",
]
NEED = ["认知格", "依据（含档位", "证据等级", "下一步·待你", "下一步·系统", "负担闸", "单签名行"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    a = ap.parse_args()
    root = os.path.abspath(a.skill_root)
    bad = []
    for f in FILES:
        p = os.path.join(root, f)
        if not os.path.isfile(p):
            bad.append((f, ["文件缺失"])); continue
        s = io.open(p, encoding="utf-8").read()
        miss = [n for n in NEED if n not in s]
        if miss: bad.append((f, miss))
    if bad:
        print("PARITY:FAIL 模板同构位缺件：", file=sys.stderr)
        for f, m in bad:
            print("   %s → %s" % (f, "、".join(m)), file=sys.stderr)
        return 1
    print("PARITY:OK %d 文件 × %d 必备件 全齐（L1×3/L2/L3/示例/SKILL 同构）" % (len(FILES), len(NEED)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
