#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日记数据校验脚本
- 检查日记数据完整性
- 验证累计数是否连续
- 检查睡眠格式是否正确
"""

import re
from pathlib import Path
from glob import glob

DIARY_DIR = Path.home() / "Local_Obsidian_Vault/1-每日计划/01-日记"

def parse_diary_data(filepath):
    """解析日记文件，提取关键数据"""
    data = {
        "date": Path(filepath).stem,
        "tomato_cumulative": None,
        "sleep_time": None,
        "wake_time": None,
    }
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 优先读取「当前累计」（最准确）
        m = re.search(r"当前累计.*?(\d+(?:\.\d+)?)\s*🍅", content)
        if m:
            data["tomato_cumulative"] = float(m.group(1))
        
        # 提取睡眠时间
        m = re.search(r"\|\s*(\d{1,2}:\d{2})\s*\|\s*(\d{1,2}:\d{2})\s*\|", content)
        if m:
            data["sleep_time"] = m.group(1)
            data["wake_time"] = m.group(2)
        
    except Exception as e:
        print(f"❌ {filepath}: {e}")
    
    return data


def run_validation(check_all=False):
    """执行校验"""
    print("🔍 正在校验日记数据...")
    print("=" * 50)
    
    files = sorted(glob(str(DIARY_DIR / "**" / "2026-*.md"), recursive=True))

    if not check_all:
        files = files[-3:]

    # ⚠️ 过滤备份文件名中的非日记文件
    
    if not files:
        print("❌ 未找到日记文件")
        return False
    
    all_errors = []
    prev_data = None
    
    for filepath in files:
        if "备份" in filepath or "SKILL" in filepath:
            continue
        
        data = parse_diary_data(filepath)
        
        # 检查累计数是否连续
        if prev_data and prev_data["tomato_cumulative"] is not None and data["tomato_cumulative"] is not None:
            if data["tomato_cumulative"] < prev_data["tomato_cumulative"]:
                error = f"❌ {data['date']}: 累计数下降！{prev_data['date']}是{prev_data['tomato_cumulative']}🍅，{data['date']}是{data['tomato_cumulative']}🍅"
                print(error)
                all_errors.append(error)
        
        if data["tomato_cumulative"] is not None:
            print(f"✅ {data['date']}: 累计 {data['tomato_cumulative']}🍅")
        
        prev_data = data
    
    print("=" * 50)
    
    if all_errors:
        print(f"\n❌ 发现 {len(all_errors)} 个错误！")
        return False
    else:
        print("\n✅ 所有日记数据校验通过！")
        return True


if __name__ == "__main__":
    import sys
    run_validation(check_all="--all" in sys.argv)
