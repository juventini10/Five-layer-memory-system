#!/usr/bin/env python3
"""x15_pair_collect.py v0.1 — ×1.5倍率滚动重估采集器（2026-10-08 建·补规格书§3.5「≥10对后回归分品类」的机械载体）
数据源：~/[日记仓库]/1-每日计划/01-日记/YYYY-MM/*.md 今日工作表（est=预计N🍅 / act=✅ N�� 同行配对）
落点：steps/x15-pairs.jsonl（幂等去重追加）+ steps/x15-recalib-report.md（读数报告）
判据：n≥10 → 报告标注「触发重估：说“启动成长箱月度蒸馏”或等月度轮消化·规格书§3.5行须更新」；n<10 → 还差几对。
铁律021：输入空列表报错退出；--selftest 用已知真值行自检解析器。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os, re, sys, json, glob, statistics
from datetime import datetime

DIARY_BASE = os.path.expanduser("~/[日记仓库]/1-每日计划/01-日记")
PAIRS = os.path.expanduser("[记忆共享中心]/数字分身/steps/x15-pairs.jsonl")
REPORT = os.path.expanduser("[记忆共享中心]/数字分身/steps/x15-recalib-report.md")
RE_EST = re.compile(r"预计\s*(\d+)\s*🍅")
RE_ACT = re.compile(r"[✅✓]\s*(\d+)\s*(?:🍅|$)")
RE_ROW = re.compile(r"^[|]\s*(\d+)\s*[|](.+)$")

def parse_row(text):
    cells = [c.strip() for c in text.split("|") if c.strip()]
    if len(cells) < 6: return None
    joined = " ".join(cells[1:])
    est = RE_EST.search(joined)
    if not est: return None
    tail = joined[est.end():]
    act = RE_ACT.search(tail)
    if not act: return None
    e, a = int(est.group(1)), int(act.group(1))
    if e <= 0 or a <= 0 or a > 20 or e > 20: return None
    task = cells[1][:24]
    return {"task": task, "est": e, "act": a, "ratio": round(a / e, 2)}

def selftest():
    r1 = "| 1 | 上午：系统修补（W33周报/检索根治） | 预计7🍅 | 上午 | Q2 | 3 | ✅ 7🍅 | 3 |"
    r2 = "| 2 | 下午：去AI味三版/收口 | 预计7🍅 | 下午 | Q2 | 3 | ✅ 10🍅（超预期） | 3 |"
    p1, p2 = parse_row(r1), parse_row(r2)
    assert p1 and p1["est"] == 7 and p1["act"] == 7, p1
    assert p2 and p2["est"] == 7 and p2["act"] == 10, p2
    assert parse_row("| 3 | 无预估行 | 标准 | 上午 | Q1 | 中 | ✅完成 | 中 |") is None
    print("selftest 3/3 PASS")

def collect():
    files = sorted(glob.glob(os.path.join(DIARY_BASE, "*", "20*.md")))
    if not files:
        print("❌ 日记输入为空（路径没挂上=仪器没电，不是没数据）", file=sys.stderr); sys.exit(2)
    existing = set()
    if os.path.exists(PAIRS):
        for line in open(PAIRS):
            try: d = json.loads(line); existing.add((d["date"], d["task"], d["est"], d["act"]))
            except Exception: pass
    new = 0
    est_only = 0
    for fp in files:
        m = re.search(r"(20\d{2}-\d{2}-\d{2})\.md$", fp)
        if not m: continue
        date = m.group(1)
        in_work = False
        for line in open(fp, encoding="utf-8"):
            if re.match(r"^## .*今日工作", line): in_work = True; continue
            if in_work and line.startswith("## ") and "今日工作" not in line: in_work = False
            if not in_work: continue
            rm = RE_ROW.match(line.strip())
            if not rm: continue
            if RE_EST.search(line) and not parse_row(line.strip()): est_only += 1
            p = parse_row(line.strip())
            if not p: continue
            key = (date, p["task"], p["est"], p["act"])
            if key in existing: continue
            rec = {"date": date, "source": fp.replace(os.path.expanduser("~"), "~"), **p,
                   "ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
            with open(PAIRS, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            existing.add(key); new += 1
    report(new, est_only)

def report(new, est_only=0):
    recs = [json.loads(l) for l in open(PAIRS)] if os.path.exists(PAIRS) else []
    ratios = [r["ratio"] for r in recs]
    n = len(ratios)
    lines = ["# ×1.5 倍率滚动重估报告（x15_pair_collect.py 机械产出）", "",
             f"- 生成：{datetime.now():%Y-%m-%d %H:%M} · 本次新增配对 {new} · 累计 **n={n}** 对",
             f"- 实测中位倍率：{round(statistics.median(ratios),3) if ratios else '—'} · 均值：{round(statistics.mean(ratios),2) if ratios else '—'} · 最大：{max(ratios) if ratios else '—'}"]
    if n >= 10:
        by = {}
        for r in recs:
            t = r["task"]
            cat = "工程" if re.search(r"系统|安装|脚本|修|收口|根治|发布|检索", t) else "创作" if re.search(r"视频|文案|PPT|写作|去AI味|读书", t) else "维护"
            by.setdefault(cat, []).append(r["ratio"])
        lines.append(f"- **n≥10 达标 → 触发重估**。分品类（关键词粗分类·v0.1待质证）：")
        for c, v in by.items(): lines.append(f"  - {c}：n={len(v)} 中位 {statistics.median(v)}")
        lines.append("- 下一步：本结果作为反向训练数据进月度蒸馏轮，规格书§3.5 ×1.5 行据实更新（机械不代判·蒸馏须过完整步序）")
    else:
        lines.append(f"- 未达重估门槛：还差 **{10-n}** 对（规则源=规格书§3.5 L242「≥10对后回归分品类」）")
        lines.append(f"- 供给率诊断：另有 {est_only} 行有「预计N🍅」但实际列没带数字（配对断在记录端，不是采集端——规划要求X🍅预估是 daily-buddy L390 既有纪律）")
    lines += ["", "> ⚠️ 已知边界：仅采「今日工作表」中带 预计N🍅+✅N🍅 双数的行；单缺任一不凑对（宁缺勿假）。8月旧三对以规格书L242实录为真源，不重复入库。"]
    with open(REPORT, "w") as f: f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:4]) + f"\n📄 报告落盘：{REPORT}")

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    else: collect()
