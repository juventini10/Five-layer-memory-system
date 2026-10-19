#!/usr/bin/env python3
"""
童灵预筛统计脚本（v1.0·2026-09-19）

功能：
1. 记录预筛结果（日期/卡ID/卡类型/结果/原因）
2. 自动统计（总数/通过数/挡掉数/挡掉率）
3. 阈值提醒（攒够100张被挡卡时提醒你复核）

统计文件：[记忆共享中心]/数字分身/预筛统计.md
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import sys
from datetime import datetime

# 路径配置
HOME = os.path.expanduser("~")
STATS_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身", "预筛统计.md")

# 阈值
THRESHOLD_BLOCKED = 100  # 攒够100张被挡卡提醒

def init_stats_file():
    """初始化统计文件"""
    if os.path.exists(STATS_FILE):
        return
    
    content = """# 童灵预筛统计

> 自动统计童灵预筛岗的工作数据，机械代意志，不靠AI自觉记录。
> 统计文件：本文件
> 脚本：`[记忆共享中心]/脚本中心/pre_screen_stats.py`

---

## 📊 总览统计

| 指标 | 数量 |
|:---|:---|
| 总预筛次数 | 0 |
| 通过 | 0 |
| 挡掉 | 0 |
| 挡掉率 | 0.0% |

### 按卡类型分

| 卡类型 | 总预筛 | 通过 | 挡掉 | 挡掉率 |
|:---|:---|:---|:---|:---|
| 立场卡 | 0 | 0 | 0 | 0.0% |
| 概念卡 | 0 | 0 | 0 | 0.0% |

---

## 📝 预筛记录

| 日期 | 卡ID | 卡类型 | 结果 | 原因/备注 |
|:---|:---|:---|:---|:---|

---

*最后更新：暂无*
"""
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已初始化统计文件：{STATS_FILE}")

def add_record(card_id, card_type, result, reason=""):
    """添加一条预筛记录"""
    init_stats_file()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 读取现有内容
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到预筛记录表格的位置
    record_idx = None
    for i, line in enumerate(lines):
        if '| 日期 | 卡ID | 卡类型 | 结果 | 原因/备注 |' in line:
            record_idx = i + 2  # 跳过表头和分隔线
            break
    
    if record_idx is None:
        print("❌ 找不到预筛记录表格位置")
        return
    
    # 插入新记录
    new_line = f"| {today} | {card_id} | {card_type} | {result} | {reason} |\n"
    lines.insert(record_idx, new_line)
    
    # 写回
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ 已记录：{card_id} | {card_type} | {result}")

def update_stats():
    """重新计算总览统计"""
    if not os.path.exists(STATS_FILE):
        print("❌ 统计文件不存在")
        return
    
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析记录
    records = []
    in_table = False
    for line in content.split('\n'):
        if '| 日期 | 卡ID | 卡类型 | 结果 | 原因/备注 |' in line:
            in_table = True
            continue
        if in_table and ('---' in line and '日期' not in line):
            continue
        if in_table and line.startswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) >= 4 and parts[0] and parts[1]:
                records.append({
                    'date': parts[0],
                    'card_id': parts[1],
                    'card_type': parts[2],
                    'result': parts[3],
                    'reason': parts[4] if len(parts) > 4 else ''
                })
        elif in_table and not line.startswith('|'):
            break
    
    # 统计
    total = len(records)
    passed = sum(1 for r in records if r['result'] == '通过')
    blocked = sum(1 for r in records if r['result'] == '挡掉')
    pass_rate = (passed / total * 100) if total > 0 else 0
    block_rate = (blocked / total * 100) if total > 0 else 0
    
    # 按卡类型分
    stance_total = sum(1 for r in records if '立场卡' in r['card_type'])
    stance_passed = sum(1 for r in records if '立场卡' in r['card_type'] and r['result'] == '通过')
    stance_blocked = sum(1 for r in records if '立场卡' in r['card_type'] and r['result'] == '挡掉')
    stance_block_rate = (stance_blocked / stance_total * 100) if stance_total > 0 else 0
    
    concept_total = sum(1 for r in records if '概念卡' in r['card_type'])
    concept_passed = sum(1 for r in records if '概念卡' in r['card_type'] and r['result'] == '通过')
    concept_blocked = sum(1 for r in records if '概念卡' in r['card_type'] and r['result'] == '挡掉')
    concept_block_rate = (concept_blocked / concept_total * 100) if concept_total > 0 else 0
    
    # 替换总览统计（用正则表达式，不管之前统计是什么）
    import re
    
    # 匹配从 "## 📊 总览统计" 到下一个 "---" 之间的内容
    pattern = r'## 📊 总览统计.*?(?=\n---)'
    
    new_stats = f"""## 📊 总览统计

| 指标 | 数量 |
|:---|:---|
| 总预筛次数 | {total} |
| 通过 | {passed} |
| 挡掉 | {blocked} |
| 挡掉率 | {block_rate:.1f}% |

### 按卡类型分

| 卡类型 | 总预筛 | 通过 | 挡掉 | 挡掉率 |
|:---|:---|:---|:---|:---|
| 立场卡 | {stance_total} | {stance_passed} | {stance_blocked} | {stance_block_rate:.1f}% |
| 概念卡 | {concept_total} | {concept_passed} | {concept_blocked} | {concept_block_rate:.1f}% |"""
    
    content = re.sub(pattern, new_stats, content, flags=re.DOTALL)
    
    # 更新最后更新时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    content = content.replace("*最后更新：暂无*", f"*最后更新：{now}*")
    
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已更新统计：总{total}次，通过{passed}，挡掉{blocked}（{block_rate:.1f}%）")
    
    # 阈值提醒
    if blocked >= THRESHOLD_BLOCKED:
        print(f"\n⚠️ 阈值提醒：已攒够{blocked}张被挡卡（目标{THRESHOLD_BLOCKED}张）")
        print(f"   你，来复核一下预筛准确率吧！")
    
    return {
        'total': total,
        'passed': passed,
        'blocked': blocked,
        'block_rate': block_rate,
        'stance_total': stance_total,
        'stance_blocked': stance_blocked,
        'concept_total': concept_total,
        'concept_blocked': concept_blocked
    }

def show_stats():
    """显示当前统计"""
    if not os.path.exists(STATS_FILE):
        print("❌ 统计文件不存在")
        return
    
    stats = update_stats()
    if stats:
        print(f"\n📊 童灵预筛统计总览：")
        print(f"   总预筛：{stats['total']} 次")
        print(f"   通过：{stats['passed']} 次")
        print(f"   挡掉：{stats['blocked']} 次（挡掉率 {stats['block_rate']:.1f}%）")
        print(f"   立场卡：{stats['stance_total']} 次（挡掉 {stats['stance_blocked']} 次）")
        print(f"   概念卡：{stats['concept_total']} 次（挡掉 {stats['concept_blocked']} 次）")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：")
        print("  添加记录：python3 pre_screen_stats.py add <卡ID> <卡类型> <结果> [原因]")
        print("  查看统计：python3 pre_screen_stats.py stats")
        print("  初始化：python3 pre_screen_stats.py init")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'init':
        init_stats_file()
    elif cmd == 'add':
        if len(sys.argv) < 5:
            print("❌ 参数不足：add <卡ID> <卡类型> <结果> [原因]")
            sys.exit(1)
        card_id = sys.argv[2]
        card_type = sys.argv[3]
        result = sys.argv[4]
        reason = sys.argv[5] if len(sys.argv) > 5 else ""
        add_record(card_id, card_type, result, reason)
        update_stats()
    elif cmd == 'stats':
        show_stats()
    else:
        print(f"❌ 未知命令：{cmd}")
        sys.exit(1)
