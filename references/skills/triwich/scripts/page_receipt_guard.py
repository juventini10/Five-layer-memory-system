#!/usr/bin/env python3
# REG: skip triwich Skill 包内回执对账件（非脚本中心守卫族）·版本纪律走本 Skill CHANGELOG·先例=triwich_scan.py 同口径
# -*- coding: utf-8 -*-
"""
page_receipt_guard.py — 翻页回执对账（V3·回执缺失→封口判红接线·H3 硬条款兑现）
设计根：回执=可观测性（工程控制论 能控⇔能观）——没读页就写不出页指纹；
      缺行/错指纹在封口对账处显形，伪造=manifest 重算判红。
接线：triwich_closeout.py 封口前置调用本件；run.sh 常驻套件（tests/test_page_receipt.py）双向验证。
判据：
  · 只对 RECEIPT_SINCE 之后铸造的键文件硬判（存量轮次无此锁——v4.4.15 防"永久红"同构基线纪律）
  · 必载页：全档 pages/p05-assumption-gates.md（装载表"Step0后·全档位"）；
            L3 轮追加 pages/p-mechanism.md（十锁全文页）
  · 回执行：`已读 pages/<页> @<8位指纹>`，指纹必须 == manifest 表内值（改版即漂=判红提示重读）
退出码：0=OK/SKIP-legacy；1=FAIL（stderr 逐条）；2=输入不可达（键文件/manifest 缺）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, json, argparse, glob

# M1 分家（内核 47KB+回执制）实落窗口 15:5x；分家前最后一枚真实键=20261021_153149（L2 设计轮）
RECEIPT_SINCE = "20261021_155500"
ALWAYS = "pages/p05-assumption-gates.md"
L3_EXTRA = "pages/p-mechanism.md"

def key_ts(path):
    m = re.search(r"step0-determination-(\d{8}_\d{6})", os.path.basename(path))
    return m.group(1) if m else None

def required_pages(text):
    pages = [ALWAYS]
    if re.search(r"三明智 L3", text) or re.search(r"判\s*L3", text):
        pages.append(L3_EXTRA)
    return pages

def check(key_file, root):
    """返回 (verdict, detail)：verdict ∈ OK / SKIP-legacy / FAIL"""
    if not os.path.isfile(key_file):
        return "INPUT", "键文件不可达: %s" % key_file
    ts = key_ts(key_file)
    if ts is None:
        return "INPUT", "键文件名无法解析时间戳: %s" % os.path.basename(key_file)
    if ts < RECEIPT_SINCE:
        return "SKIP-legacy", "ts=%s < 接线基线 %s（存量轮不判——防永久红）" % (ts, RECEIPT_SINCE)
    mf_path = os.path.join(root, "pages", "manifest.json")
    if not os.path.isfile(mf_path):
        return "FAIL", "manifest 缺失——先跑 make_manifest.py build（页表真源不在，回执无从对账）"
    tab = {e["path"]: e["fingerprint"] for e in json.load(open(mf_path, encoding="utf-8"))["pages"]}
    text = open(key_file, encoding="utf-8").read()
    receipts = {m.group(1): m.group(2)
                for m in re.finditer(r"已读\s+(pages/\S+\.md)\s+@([0-9a-f]{8})", text)}
    problems = []
    for pg in required_pages(text):
        if pg not in tab:
            problems.append("页不在表内 %s（manifest 与装载表脱节）" % pg)
            continue
        if pg not in receipts:
            problems.append("缺回执 %s（按§生命周期装载表读页后在键文件落 `已读 %s @<指纹>`）" % (pg, pg))
        elif receipts[pg] != tab[pg]:
            problems.append("指纹不符 %s: 回执=%s 表内=%s（页已改版或凭印象伪造——重读页取 frontmatter 新指纹）" % (pg, receipts[pg], tab[pg]))
    if problems:
        return "FAIL", " ｜ ".join(problems)
    return "OK", "必载页 %d 项回执指纹全对" % len(required_pages(text))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    a = ap.parse_args()
    v, d = check(a.key_file, os.path.abspath(a.root))
    if v == "FAIL":
        print("RECEIPT:FAIL " + d, file=sys.stderr); print("RECEIPT:FAIL"); return 1
    if v == "INPUT":
        print("RECEIPT:INPUT " + d, file=sys.stderr); print("RECEIPT:INPUT"); return 2
    print("RECEIPT:%s %s" % (v, d))
    return 0

if __name__ == "__main__":
    sys.exit(main())
