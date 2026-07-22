#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动计算番茄数
"""

import glob
import pathlib
import re

DIARY_DIR = pathlib.Path.home() / 'Local_Obsidian_Vault/1-每日计划/01-日记'

files = sorted(glob.glob(str(DIARY_DIR / '**' / '2026-*.md'), recursive=True))
total = 0

print("开始计算番茄数...")
print("=" * 60)

for f in files:
    if '备份' in f:
        continue
    
    try:
        with open(f, 'r', encoding='utf-8') as fobj:
            content = fobj.read()
        
        # 提取总实际番茄数
        m = re.search(r'总实际[：:]*\s*(\d+(?:\.\d+)?)\s*🍅', content)
        if m:
            tomato = float(m.group(1))
            total += tomato
            print(f"{f.split('/')[-1]:<20} | 番茄数: {tomato:>5} | 累计: {total:>6}")
        else:
            # 尝试其他格式
            m = re.search(r'番茄总数[*]+[：:]*\s*(\d+(?:\.\d+)?)\s*🍅', content)
            if m:
                tomato = float(m.group(1))
                total += tomato
                print(f"{f.split('/')[-1]:<20} | 番茄数: {tomato:>5} | 累计: {total:>6}")
            else:
                print(f"{f.split('/')[-1]:<20} | 番茄数: {0:>5} | 累计: {total:>6}")
    except Exception as e:
        print(f"{f.split('/')[-1]:<20} | 番茄数: {'错误':>5} | 累计: {total:>6}")

print("=" * 60)
print(f"最终总计: {total}")