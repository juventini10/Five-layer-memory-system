#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_citation_candidates.py — 引用候选检测（质证回写管道根治方案·二期）
职责: 扫系统日志 → 提取「引用 S0XX」上下文行 → 输出候选清单（带上下文+日期），供月报人工确认。
      ⛔不自动升 L3——信噪比问题（残差#076：引用≠采纳，有罗列/否定/测试场景）。
      人工确认后写入引用台账（citation_ledger.md），derive_reading_status.py 从台账派生 L3/L4。

引用质量分类（供人工确认参考）:
  依据型   —— 卡被用作结论支撑（真应用）
  罗列型   —— 卡出现在清单/枚举中（弱信号）
  否定型   —— 卡被判定为错误/无关（反信号）
  测试型   —— 卡出现在 eval/测试场景（非真实任务）

用法:
  python3 scan_citation_candidates.py                 # 扫最近30天
  python3 scan_citation_candidates.py --days 90       # 扫最近90天
  python3 scan_citation_candidates.py --all           # 扫全部日志
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, glob
from datetime import datetime, timedelta

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, SYSLOG_DIR
LOG_DIR = SYSLOG_DIR

DAYS = 30
if "--days" in sys.argv:
    DAYS = int(sys.argv[sys.argv.index("--days") + 1])
ALL = "--all" in sys.argv

# 引用模式：S后跟3位数字（立场卡#SXXX / 技能卡#KXXX 的引用）
CARD_RE = re.compile(r"(?:立场卡#|#)?([SK]\d{3})")
# 排除模式：涉及文件行（路径列表）、INDEX、派生脚本输出等
EXCLUDE_CTX = ("涉及文件", "INDEX", "派生", "regen", "derive", "lint")


def scan():
    if not INSTALLED or not LOG_DIR:
        print("未安装态（记忆共享中心自推导失败）——跳过扫描")
        return {}
    now = datetime.now()
    cutoff = now - timedelta(days=DAYS)
    hits = {}  # card_id -> list of (date, context)
    for p in sorted(glob.glob(os.path.join(LOG_DIR, "系统日志_*.md"))):
        base = os.path.basename(p)
        m = re.search(r"系统日志_(\d{4}-\d{2}-\d{2})\.md", base)
        if not m:
            continue
        date = m.group(1)
        if not ALL:
            try:
                d = datetime.strptime(date, "%Y-%m-%d")
                if d < cutoff:
                    continue
            except ValueError:
                continue
        with open(p, encoding="utf-8") as f:
            for line in f:
                if not line.startswith("- "):
                    continue
                if any(x in line for x in EXCLUDE_CTX):
                    continue
                for cid in CARD_RE.findall(line):
                    if cid.startswith("S") and int(cid[1:]) > 800:
                        continue  # 超出实际卡号范围的噪声
                    hits.setdefault(cid, []).append((date, line.strip()[:100]))

    print(f"📚 扫描日志: {DAYS if not ALL else '全部'} 天 | 引用命中: {len(hits)} 张卡")
    print()
    for cid in sorted(hits, key=lambda c: (-len(hits[c]), c)):
        events = hits[cid]
        print(f"━━ {cid} × {len(events)} ━━")
        for date, ctx in events[:5]:  # 每卡最多展示5条
            print(f"  [{date}] {ctx}")
        print()
    return hits


if __name__ == "__main__":
    scan()
