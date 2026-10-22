#!/usr/bin/env python3
# REG: skip triwich Skill 包内 eval 对账件（非脚本中心守卫族）·版本纪律走本 Skill CHANGELOG·先例=triwich_scan.py 同口径
# -*- coding: utf-8 -*-
"""
eval_anchor_check.py — eval 68 断言（M3首批56·随版增补） × 分家现位 逐条机械对账（M3·防"迁移表=第二本账"）
输入：references/eval-migration-map.md 表格（真源=本表，逐行 `现位`×`校验token`）
判据：现位每文件必含 token；`-`=人眼自锚跳过；不一致逐行显形。
用法：python3 eval_anchor_check.py [--skill-root DIR] [--verbose]
退出码：0=全对账；1=存在断锚行；2=表不可达。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.skill_root)
    mp = os.path.join(root, "references", "eval-migration-map.md")
    if not os.path.isfile(mp):
        print("EVALMAP:FAIL 迁移表不可达 %s" % mp, file=sys.stderr)
        return 2
    rows = []
    for line in open(mp, encoding="utf-8"):
        m = re.match(r"^\|\s*(\d+)\s*\|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        rows.append((int(m.group(1)), cells[3], cells[4]))  # (#, 现位, token)
    total = len(rows)
    if total != 68:  # v4.10.1：模板同构齐闸断言（67→68）；单常量可回落（SINCE 族同款）
        print("EVALMAP:FAIL 迁移表行数=%d ≠ 68（eval-set 与表脱节，先补行再对账）" % total, file=sys.stderr)
        return 1
    bad = []
    cached = {}
    for num, locs, tok in rows:
        if locs == "-":
            continue  # 人眼自锚层
        for f in locs.split("+"):
            f = f.strip()
            if f not in cached:
                p = os.path.join(root, f)
                cached[f] = open(p, encoding="utf-8").read() if os.path.isfile(p) else None
            if cached[f] is None:
                bad.append("#%d 现位文件不存在 %s" % (num, f))
            elif tok not in cached[f]:
                bad.append("#%d token「%s」不在 %s" % (num, tok, f))
    if bad:
        print("EVALMAP:FAIL %d 处断锚：" % len(bad), file=sys.stderr)
        for b in bad[:20]:
            print("   " + b, file=sys.stderr)
        return 1
    n_auto = sum(1 for _, l, _ in rows if l != "-")
    print("EVALMAP:OK %d/%d 对账（机械可验 %d · 人眼自锚 %d）" % (total, total, n_auto, total - n_auto))
    return 0

if __name__ == "__main__":
    sys.exit(main())
