#!/usr/bin/env python3
"""
日记标题格式检查脚本
验证所有日记是否符合规则：# YYYY-MM-DD(周X) 每日计划
"""

import os
import re
from datetime import datetime

def check_diary_titles():
    diary_dir = os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/Local_Obsidian_Vault/1-每日计划/01-日记/"))
    
    weekday_map = {
        0: "周一", 1: "周二", 2: "周三", 3: "周四",
        4: "周五", 5: "周六", 6: "周日"
    }
    
    errors = []
    success = []
    
    for root, dirs, files in os.walk(diary_dir):
        for filename in sorted(files):
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(root, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取日期
            match = re.search(r'date: (\d{4}-\d{2}-\d{2})', content)
            if not match:
                errors.append(f"❌ {filename}: 无法提取日期")
                continue

            date_str = match.group(1)

            # 计算正确的星期
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                correct_weekday = weekday_map[date_obj.weekday()]
            except Exception:
                errors.append(f"❌ {filename}: 日期格式错误")
                continue

            # 检查标题
            correct_title = f"# {date_str}({correct_weekday}) 每日计划"

            if correct_title in content:
                success.append(f"✅ {filename}: {correct_title}")
            else:
                # 查找实际标题
                title_match = re.search(r'^# \d{4}-\d{2}-\d{2}.*', content, re.MULTILINE)
                if title_match:
                    actual_title = title_match.group(0)
                    errors.append(f"❌ {filename}: 标题错误\n   期望: {correct_title}\n   实际: {actual_title}")
                else:
                    errors.append(f"❌ {filename}: 缺少标题")
    
    # 输出结果
    print("=" * 60)
    print("📋 日记标题格式检查结果")
    print("=" * 60)
    
    if success:
        print(f"\n✅ 通过检查 ({len(success)} 个):")
        for s in success:
            print(f"  {s}")
    
    if errors:
        print(f"\n❌ 检查失败 ({len(errors)} 个):")
        for e in errors:
            print(f"  {e}")
    
    print("\n" + "=" * 60)
    if not errors:
        print("🎉 全部日记格式正确！")
    else:
        print(f"⚠️ 发现 {len(errors)} 个错误，需要修复")
    print("=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = check_diary_titles()
    exit(0 if success else 1)
