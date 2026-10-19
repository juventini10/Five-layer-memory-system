#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_blind_eval_v28.py -- Step 2.8 retest round builder (spec v1.1.0).
Reuses build_blind_eval.py machinery; overrides: seed 20260823, N=20
(10 in-spec from CURRENT v1.1.0 citations not blind-tested before,
10 fresh out-of-spec), excludes all 62 cards used in rounds 2/2.5/2.6
plus protocol hard-excludes S812/S813. History script untouched."""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import io, os, re, sys, random
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_blind_eval as base

HOME = Path.home()
MC = HOME / "\u4e2a\u4ebaAI\u6863\u6848"
SPEC = MC / "\u6570\u5b57\u5206\u8eab" / "\u7eb2\u5e16\u4fa0\u00b7\u4eba\u683c\u89c4\u683c\u4e66.md"

USED = {4,6,21,22,29,40,52,61,65,66,68,71,73,79,84,85,87,92,95,96,97,99,104,106,
        114,123,124,132,179,183,233,276,297,307,346,369,380,384,385,387,390,391,
        392,403,427,434,441,511,546,551,553,594,599,619,643,687,712,718,724,771,
        810,811,814}
HARD = {812, 813}

def main():
    txt = SPEC.read_text(encoding="utf-8")
    cited = sorted({int(m) for m in re.findall(r"S(\d{3})", txt)})
    pool_in_ids = [s for s in cited if s not in USED and s not in HARD]
    print("[v1.1.0 cited] total=%d  fresh-in-spec pool=%d -> %s" % (len(cited), len(pool_in_ids), ["S%03d"%s for s in pool_in_ids]))

    base.SEED = 20260823
    base.N_IN_SPEC = min(10, len(pool_in_ids))
    base.N_OUT_SPEC = 20 - base.N_IN_SPEC
    base.IN_SPEC_POOL = pool_in_ids
    # out-of-spec excludes: everything spec-cited ever + used + hard
    base.SPEC_CITED = sorted(set(cited) | USED)
    base.READ_EXCLUDE_KEYS = {"S%03d" % s for s in HARD}
    base.READ_EXCLUDE = HARD
    # 2026-10-14 A7 同族根治：原写法 `HERE.parent / "steps"` 把输出落点绑在"自身目录的父目录"上——
    # 本件从 脚本中心 根层搬进 记忆蒸馏/ 后，落点会由 `个人AI档案/steps/` 静默漂移成 `脚本中心/steps/`（不存在）。
    # 病名与 install_script_center / k2 生成器同族：路径语义绑自身位置 ⇒ 搬家即漂移。
    # 改为绝对锚：与兄弟件 build_blind_eval.py 的 OUT_FILE 口径一致，且与盘上在存产物同址
    # （实测真件 = [记忆共享中心]/数字分身/steps/step2.8-blind-items.md·本行取数于 2026-10-14 find 结果）。
    base.OUT_FILE = Path('[记忆共享中心]') / "数字分身" / "steps" / "step2.8-blind-items.md"
    base.main()

    # post-fix header to step2.8 identity (main() hardcodes round-1 header)
    p = base.OUT_FILE
    t = p.read_text(encoding="utf-8")
    t = t.replace("# Step 2 \u76f2\u9898\u96c6\uff0840\u6761\uff09",
                  "# Step 2.8 \u76f2\u9898\u96c6\uff08v1.1.0 \u91cd\u6d4b\u00b720\u6761\uff09", 1)
    t = t.replace("\u79cd\u5b50=20260821 \u00b7 \u6784\u9020=build_blind_eval.py \u00b7 2026-08-21",
                  "\u79cd\u5b50=20260823 \u00b7 \u6784\u9020=build_blind_eval_v28.py(\u5bf9\u8c61=\u89c4\u683c\u4e66v1.1.0) \u00b7 2026-08-23", 1)
    p.write_text(t, encoding="utf-8")
    print("[header] step2.8 identity applied")

if __name__ == "__main__":
    main()
