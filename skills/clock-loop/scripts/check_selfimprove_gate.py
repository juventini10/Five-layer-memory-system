#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自进步门禁触发器（确定性 · 文件计数锚定）

来源：clock-loop v2.5.3 阶段4 收尾门禁
用途：确定性统计 test_results/ 下评估报告数量，输出 L3沉淀是否必须运行。
v3.0.0新增：双盲审计到期检测（每10份评估报告触发一次双盲+人类锚审计）。
v3.0.4修复：L3触发从"整除5"改为"增量≥5"——自上次L3以来新积累5份报告即触发，
  解决多源写入导致计数器非线性跳变时漏触发的问题（实测22份报告，15/20两个5的倍数均被跳过）。
不做AI语义判定——纯路径计数 + 日期解析，可grep可复现。

设计依据：L3沉淀原靠"AI数文件 + post-delivery SHOULD"触发，实测10份报告零产物
（AI漏跑/数错）。本脚本将"是否触发L3"变为确定性决策：门禁以 `l3_required`
字段为准，不靠AI自觉或算术。与对话冲突管道同哲学（修复#4：脚本确定性加载，
不靠"AI记得去看"）。

双盲审计触发依据：反方向的钟设计哲学§九#8——自指不可消除，用常态外部审计
压缩自指偏差存续时间。触发机制在脚本里不在prose里（机制代替意志力）。

输出格式（JSON）：
{
  "report_count": N,
  "l3_required": true|false,   # v3.0.4: 自上次L3以来新积累 >=5 份报告 → true
  "last_l3_date": "YYYY-MM-DD" | null,
  "last_l3_n": int | null,     # v3.0.4: 上次L3时的报告数
  "days_since_l3": int | null,
  "double_blind_due": true|false,  # v3.0.0: N>=10 且双盲报告数不足时触发
  "double_blind_count": int,       # 已完成的双盲审计报告数
  "next_double_blind_at": int      # 下次双盲到期时的报告数阈值
}

失败处理：
- test_results 目录不存在 → 返回 {"report_count":0,"l3_required":false,...,"double_blind_due":false}
- 解析异常 → 打印错误到stderr，返回安全默认（l3_required=false, double_blind_due=false），不崩溃
- 日期解析失败 → last_l3_date=null, days_since_l3=null

用法：
  python3 check_selfimprove_gate.py [--test-results PATH] [--evolution PATH]
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path

DEFAULT_TEST_RESULTS = "~/[记忆共享中心]/评估知识库/test_results"
DEFAULT_EVOLUTION = "~/[记忆共享中心]/评估知识库/evolution"


def resolve_path(p: str) -> Path:
    return Path(p).expanduser()


def count_reports(test_results: Path) -> int:
    """统计 test_results/ 下所有评估报告（*评估报告*.md），排除 progress 等非报告文件。"""
    if not test_results.exists():
        return 0
    return len(list(test_results.rglob("*评估报告*.md")))


def _parse_l3_count_from_file(evolution_dir: Path, l3_date: str) -> "int | None":
    """从最新L3沉淀文件头部解析 l3_report_count 字段（v3.0.4新增）。"""
    latest = None
    for f in evolution_dir.rglob("L3_沉淀_*.md"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if m and m.group(1) == l3_date:
            latest = f
            break
    if latest is None:
        return None
    try:
        with open(latest, 'r', encoding='utf-8') as fh:
            for line in fh:
                m = re.search(r"l3_report_count:\s*(\d+)", line)
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    # 向后兼容：旧沉淀文件无 l3_report_count 字段，尝试从「触发：...N份」推断
    try:
        with open(latest, 'r', encoding='utf-8') as fh:
            for line in fh:
                m = re.search(r"触发.*?report_count[：:=]\s*(\d+)|累计.*?(\d+)\s*份|报告数\s*=\s*(\d+)", line)
                if m:
                    for g in m.groups():
                        if g:
                            return int(g)
    except Exception:
        pass
    return None


def last_l3_info(evolution: Path) -> "tuple[str|None, int|None]":
    """返回 (最新L3日期, 当时报告数)。"""
    if not evolution.exists():
        return None, None
    dates = []
    for f in evolution.rglob("L3_沉淀_*.md"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if m:
            dates.append(m.group(1))
    if not dates:
        return None, None
    latest_date = max(dates)
    latest_n = _parse_l3_count_from_file(evolution, latest_date)
    return latest_date, latest_n


def count_double_blind_reports(test_results: Path) -> int:
    """统计 test_results/ 下双盲审计报告数量（*双盲*.md）。
    
    v3.0.0新增：每10份评估报告应触发1次双盲审计。
    双盲报告数不足 → double_blind_due=true。
    """
    if not test_results.exists():
        return 0
    return len(list(test_results.rglob("*双盲*.md")))


# 双盲审计触发阈值：每10份评估报告触发1次
DOUBLE_BLIND_THRESHOLD = 10

# L3沉淀阈值：自上次L3以来新积累5份报告即触发
L3_INCREMENT_THRESHOLD = 5


def main():
    ap = argparse.ArgumentParser(description="自进步门禁触发器（确定性计数）")
    ap.add_argument("--test-results", default=DEFAULT_TEST_RESULTS, help="评估报告根目录")
    ap.add_argument("--evolution", default=DEFAULT_EVOLUTION, help="L3沉淀目录")
    args = ap.parse_args()

    try:
        test_results_path = resolve_path(args.test_results)
        evolution_path = resolve_path(args.evolution)
        n = count_reports(test_results_path)
        l3_date, last_l3_n = last_l3_info(evolution_path)
        days = None
        if l3_date:
            try:
                days = (date.today() - datetime.strptime(l3_date, "%Y-%m-%d").date()).days
            except ValueError:
                days = None
        
        # v3.0.4: 增量触发——自上次L3以来新积累 >=5 份报告即触发
        if n >= L3_INCREMENT_THRESHOLD and last_l3_n is not None:
            l3_required = (n - last_l3_n) >= L3_INCREMENT_THRESHOLD
        elif n >= L3_INCREMENT_THRESHOLD and last_l3_n is None:
            # 有报告但没有 L3 沉淀记录 → 首次触发
            l3_required = True
        else:
            l3_required = False
        
        # v3.0.0: 双盲审计到期检测——每10份报告应有1次双盲审计
        db_count = count_double_blind_reports(test_results_path)
        expected_db = n // DOUBLE_BLIND_THRESHOLD  # 应有的双盲审计次数
        double_blind_due = (n >= DOUBLE_BLIND_THRESHOLD and db_count < expected_db)
        next_db_at = ((n // DOUBLE_BLIND_THRESHOLD) + 1) * DOUBLE_BLIND_THRESHOLD if n > 0 else DOUBLE_BLIND_THRESHOLD
        
        out = {
            "report_count": n,
            "l3_required": l3_required,
            "last_l3_date": l3_date,
            "last_l3_n": last_l3_n,
            "days_since_l3": days,
            "double_blind_due": double_blind_due,
            "double_blind_count": db_count,
            "next_double_blind_at": next_db_at,
        }
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        print(json.dumps(
            {"report_count": 0, "l3_required": False, "last_l3_date": None, "last_l3_n": None,
             "days_since_l3": None,
             "double_blind_due": False, "double_blind_count": 0,
             "next_double_blind_at": DOUBLE_BLIND_THRESHOLD},
            ensure_ascii=False,
        ))


if __name__ == "__main__":
    main()
