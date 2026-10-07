#!/usr/bin/env python3
"""
batch_auto_pass.py — 批量标记立场卡自动通过（分层终审机制）
读取step3-first-review-log.md，按自动通过阈值判定每张卡：
- 价值层 → 你必检
- 机制层/方法层 + 置信度高 → 自动通过
- 机制层/方法层 + 置信度中 → 你抽检
输出你必检清单和自动通过统计。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
from pathlib import Path

LOG_PATH = Path.home() / "~/[记忆共享中心]/数字分身/steps/step3-first-review-log.md"

def parse_reviews(log_path):
    """解析step3初审台账，返回每张卡的初审信息"""
    reviews = {}
    with open(log_path) as f:
        content = f.read()
    
    # 匹配表格行：| 序号 | 日期 | 卡ID | 层级归属 | 置信度 | 裁决+边界 | 依据 | 升级声明 | 你复核 |
    pattern = r'\|\s*(\d+[a-z]?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(S\d+[a-z]?)\s*\|\s*(\S+?)\s*\|\s*(\S+?)\s*\|'
    matches = re.findall(pattern, content)
    
    for seq, date, card_id, level, confidence in matches:
        if card_id not in reviews:  # 只取第一次初审记录
            reviews[card_id] = {
                'seq': seq,
                'date': date,
                'level': level,
                'confidence': confidence,
            }
    return reviews

def classify(review):
    """按自动通过阈值分类"""
    level = review['level']
    confidence = review['confidence']
    
    # 高置信度 = 高 或 中高（中高=中偏高，算高置信度）
    is_high_confidence = confidence in ['高', '中高', '高🟢']
    
    if '价值' in level:
        return '你必检（价值层）'
    elif is_high_confidence:
        return '自动通过（低风险机制层/方法层）'
    else:
        return '你抽检（高风险机制层/方法层）'

def main():
    if not LOG_PATH.exists():
        print(f"❌ 台账文件不存在: {LOG_PATH}")
        sys.exit(1)
    
    reviews = parse_reviews(LOG_PATH)
    print(f"📊 共解析 {len(reviews)} 张卡的初审记录（全库范围）")
    print()
    
    # 分类
    categories = {'你必检（价值层）': [], '自动通过（低风险机制层/方法层）': [], '你抽检（高风险机制层/方法层）': []}
    for card_id, review in sorted(reviews.items()):
        cat = classify(review)
        categories[cat].append((card_id, review))
    
    # 输出统计
    print("=" * 60)
    print("📈 分层终审统计")
    print("=" * 60)
    for cat, cards in categories.items():
        print(f"  {cat}: {len(cards)} 张")
    print()
    
    # 输出你必检清单
    print("=" * 60)
    print("🔴 你必检清单（价值层，不可替代）")
    print("=" * 60)
    for card_id, review in categories['你必检（价值层）']:
        print(f"  {card_id} | 序号{review['seq']} | {review['date']} | 置信度{review['confidence']}")
    print()
    
    # 输出你抽检清单
    print("=" * 60)
    print("🟡 你抽检清单（高风险机制层/方法层，置信度中）")
    print("=" * 60)
    for card_id, review in categories['你抽检（高风险机制层/方法层）']:
        print(f"  {card_id} | 序号{review['seq']} | {review['date']} | 置信度{review['confidence']}")
    print()
    
    # 输出自动通过清单（前10张示例）
    print("=" * 60)
    print(f"🟢 自动通过清单（低风险机制层/方法层，共{len(categories['自动通过（低风险机制层/方法层）'])}张，前10张示例）")
    print("=" * 60)
    for card_id, review in categories['自动通过（低风险机制层/方法层）'][:10]:
        print(f"  {card_id} | 序号{review['seq']} | {review['date']} | 置信度{review['confidence']}")
    if len(categories['自动通过（低风险机制层/方法层）']) > 10:
        print(f"  ... 还有 {len(categories['自动通过（低风险机制层/方法层）']) - 10} 张")
    print()
    
    # 你实际工作量
    must_check = len(categories['你必检（价值层）'])
    spot_check = len(categories['你抽检（高风险机制层/方法层）'])
    auto_pass = len(categories['自动通过（低风险机制层/方法层）'])
    total = must_check + spot_check + auto_pass
    print("=" * 60)
    print(f"💡 你实际工作量：{must_check + spot_check}/{total} 张（必检{must_check}+抽检{spot_check}），自动通过{auto_pass}张")
    print(f"   减负比例：{auto_pass/total*100:.1f}%")
    print("=" * 60)

if __name__ == '__main__':
    main()
