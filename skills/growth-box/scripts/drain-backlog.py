#!/usr/bin/env python3
"""growth-box/scripts/drain-backlog.py — 反哺管道排空脚本

用法：
  python3 drain-backlog.py --check          # 只数数量，输出 ALARM/NORMAL
  python3 drain-backlog.py --report         # 逐条输出排空报告

功能：
  --check: 扫描 规范反哺日志.md 总追踪表，统计 🔴待整合 数量。
           输出 JSON: {backlog:N, alarm:true/false, since_last_drain:days}
           由 growth-box SKILL.md 启动时调用，决定是否触发排空。

  --report: 扫描全部 🔴待整合 条目，逐条提取 {日期/标题/落点/内容摘要}。
            输出 Markdown 表格，供 AI 呈现给用户逐条 y/n。

设计原则：
  SKILL.md 不重复写阈值和逻辑——所有逻辑在脚本里。
  SKILL.md 只写一句：✅DO 启动时调 drain-backlog.py --check，按结果执行。
  依据：指令§6.1 单一来源（阈值/判定规则只存在一处）。
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import re
import json
import sys
from pathlib import Path
from datetime import date, datetime

FEEDBACK_LOG = Path.home() / "[记忆共享中心]/成长箱/experience/规范反哺日志.md"
ALARM_THRESHOLD = 15


def count_backlog(text: str) -> int:
    """统计总追踪表中 🔴待整合 条目数"""
    in_table = False
    count = 0
    for line in text.split('\n'):
        if line.startswith('## 总追踪表'):
            in_table = True
            continue
        if in_table and line.startswith('## '):
            break
        if in_table and '🔴 待整合' in line:
            count += 1
    return count


def days_since_last_drain(text: str) -> int | None:
    """从总追踪表找最后一次 ✅已整合 的日期，返回距今天数"""
    in_table = False
    last_ok = None
    for line in text.split('\n'):
        if line.startswith('## 总追踪表'):
            in_table = True
            continue
        if in_table and line.startswith('## '):
            break
        if in_table and '✅ 已整合' in line:
            dates = re.findall(r'(\d{2}-\d{2})', line)
            if dates:
                try:
                    d = datetime.strptime(f"2026-{dates[0]}", "%Y-%m-%d").date()
                    if last_ok is None or d > last_ok:
                        last_ok = d
                except ValueError:
                    pass
    if last_ok is None:
        return None
    return (date.today() - last_ok).days


def parse_detailed_entries(text: str) -> list[dict]:
    """从详细反哺条目段提取 🔴待整合 条目的元数据"""
    entries = []
    # 定位到 "## 详细反哺条目" 之后
    detail_start = text.find("## 详细反哺条目")
    if detail_start == -1:
        return entries
    detail_text = text[detail_start:]

    # 按 "### 2026-" 分块
    blocks = re.split(r'\n(?=### 2026-)', detail_text)
    for block in blocks:
        if '🔴 待整合' not in block:
            continue
        entry = {}
        # 兼容两种格式：**🔖 反哺标题**：value 和 | 🔖 反哺标题 | value |
        m = re.search(r'(?:^\|\s*)?🔖\s*反哺标题[*\s]*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['title'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*)?📅\s*日期[*\s]*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['date'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*)?📚\s*建议落点[*\s]*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['target'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*)?📝\s*反哺内容[*\s]*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['summary'] = m.group(1).strip().rstrip('|').strip()[:120]
        m = re.search(r'(?:^\|\s*)?⚡\s*重要度[*\s]*[：:|]?\s*(高|低)', block, re.MULTILINE)
        if m:
            entry['priority'] = m.group(1)

        if entry.get('title'):
            entries.append(entry)
    return entries


def cmd_check():
    """--check: 输出 JSON 状态"""
    if not FEEDBACK_LOG.exists():
        print(json.dumps({"backlog": 0, "alarm": False, "since_last_drain": None, "error": "feedback log not found"}))
        sys.exit(0)
    text = FEEDBACK_LOG.read_text(encoding='utf-8')
    n = count_backlog(text)
    days = days_since_last_drain(text)
    alarm = n >= ALARM_THRESHOLD or (days is not None and days >= 30)
    result = {"backlog": n, "alarm": alarm, "since_last_drain": days}
    print(json.dumps(result))
    sys.exit(0 if not alarm else 1)


def cmd_report():
    """--report: 输出排空报告 Markdown 表格"""
    if not FEEDBACK_LOG.exists():
        print("规范反哺日志不存在")
        sys.exit(1)
    text = FEEDBACK_LOG.read_text(encoding='utf-8')
    entries = parse_detailed_entries(text)
    if not entries:
        print("✅ 无 🔴待整合 条目")
        return

    print(f"## ⚠️ 反哺管道积压：{len(entries)} 条 🔴待整合\n")
    print("| # | 日期 | 重要度 | 标题 | 建议落点 | 内容摘要 |")
    print("|:-:|:----:|:------:|------|---------|---------|")
    for i, e in enumerate(entries, 1):
        title = e.get('title', '?')[:50]
        d = e.get('date', '?')
        p = e.get('priority', '?')
        target = e.get('target', '?')[:45]
        summary = e.get('summary', '?')[:80]
        print(f"| {i} | {d} | {p} | {title} | {target} | {summary} |")


def main():
    parser = argparse.ArgumentParser(description='反哺管道排空脚本')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='统计 🔴待整合 数量，输出 JSON')
    group.add_argument('--report', action='store_true', help='逐条输出排空报告')
    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.report:
        cmd_report()


if __name__ == '__main__':
    main()
