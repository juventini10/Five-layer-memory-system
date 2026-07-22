#!/usr/bin/env python3
"""growth-box/stats.py — 从错误源文件重算 INDEX.md 模式目录表

用法：
  python3 stats.py --learnings-dir ~/[记忆共享中心]/成长箱/learnings/ --index ~/[记忆共享中心]/成长箱/learnings/INDEX.md

功能：
  1. 扫描 learnings/ 下所有 *_errors.md / LEARNINGS.md / ERRORS.md / skill_errors.md
  2. 按 PAT-XXX 统计出现次数 + 最新发生日期
  3. 保留 INDEX.md 中现有的「状态」「关联铁律」元数据
  4. 输出更新后的模式目录表（Markdown 格式）

设计原则（指令§6.1 单一来源）：
  INDEX.md 的模式目录表是从错误源文件派生的数据。手工维护计数=双本账迟早漂移。
  本脚本只读源文件、实时计算派生数据，不另建独立写入源。
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import re
import os
from pathlib import Path
from datetime import date


# PAT 编号正则（PAT-001, PAT-002, ...）
PAT_PTN = re.compile(r'PAT-(\d{3,})')


def scan_error_files(learnings_dir: Path) -> dict:
    """扫描错误文件，返回 {pat_id: {count, latest_date}}"""
    error_files = []
    for pattern in ['*_errors.md', 'LEARNINGS.md', 'ERRORS.md', 'skill_errors.md']:
        error_files.extend(learnings_dir.glob(pattern))

    pats = {}
    for f in error_files:
        text = f.read_text(encoding='utf-8')
        # 按 PAT-XXX 分块
        for m in PAT_PTN.findall(text):
            pat_id = f'PAT-{m}'
            if pat_id not in pats:
                pats[pat_id] = {'count': 0, 'latest': None}
            pats[pat_id]['count'] += 1
            # 提取最新日期
            dates = re.findall(r'(\d{4}-\d{2}-\d{2})', text)
            for d in dates:
                try:
                    dt = date.fromisoformat(d)
                    if pats[pat_id]['latest'] is None or dt > pats[pat_id]['latest']:
                        pats[pat_id]['latest'] = dt
                except ValueError:
                    pass
    return pats


def read_index_meta(index_path: Path) -> dict:
    """读取 INDEX.md 现有模式目录表，提取状态和关联铁律"""
    text = index_path.read_text(encoding='utf-8')
    meta = {}
    # 匹配表行：| PAT-XXX | 名称 | 次数 | 日期 | 状态 | 铁律 |
    row_ptn = re.compile(
        r'^\|\s*(PAT-\d{3,})\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|',
        re.MULTILINE
    )
    for m in row_ptn.finditer(text):
        pat_id = m.group(1)
        name = m.group(2).strip()
        status = m.group(5).strip()
        rule = m.group(6).strip()
        meta[pat_id] = {'name': name, 'status': status, 'rule': rule}
    return meta


def generate_table(pats: dict, meta: dict) -> str:
    """生成模式目录表（Markdown）"""
    header = '| 编号 | 模式名称 | 累计次数 | 最新发生 | 状态 | 关联铁律 |\n|------|---------|---------|---------|------|---------|'
    rows = []

    # 按 PAT 编号排序
    for pat_id in sorted(pats.keys()):
        info = pats[pat_id]
        m = meta.get(pat_id, {})
        name = m.get('name', '（未知·请手动填写）')
        status = m.get('status', 'pending')
        rule = m.get('rule', '-')
        latest = info['latest'].isoformat() if info['latest'] else '未知'
        count = f"{info['count']}+"
        rows.append(f'| {pat_id} | {name} | {count} | {latest} | {status} | {rule} |')

    return header + '\n' + '\n'.join(rows) if rows else '(无 PAT 条目)'


def main():
    parser = argparse.ArgumentParser(description='从错误源文件重算 INDEX.md 模式目录表')
    parser.add_argument('--learnings-dir', required=True, help='成长箱 learnings/ 目录')
    parser.add_argument('--index', required=True, help='INDEX.md 文件路径（用于读取元数据状态/铁律）')
    args = parser.parse_args()

    learnings = Path(args.learnings_dir).expanduser().resolve()
    index = Path(args.index).expanduser().resolve()

    if not learnings.is_dir():
        print(f"❌ learnings 目录不存在: {learnings}", file=__import__('sys').stderr)
        __import__('sys').exit(1)

    pats = scan_error_files(learnings)
    meta = read_index_meta(index) if index.exists() else {}

    # 合并：保留 INDEX 中的 PAT（即使 error 文件中暂时没扫到）
    for pat_id in meta:
        if pat_id not in pats:
            pats[pat_id] = {'count': 0, 'latest': None}

    table = generate_table(pats, meta)
    print(table)


if __name__ == '__main__':
    main()
