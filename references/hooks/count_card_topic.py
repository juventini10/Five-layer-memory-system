#!/usr/bin/env python3
"""
count_card_topic.py — 新领域判定脚本
统计AI学习库中包含指定主题关键词的立场卡数量，
≥3张则非新领域，<3张则新领域。
用于分层终审机制中的自动通过阈值判定。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import re
from pathlib import Path

AI_LIB_PATH = Path.home() / "~/个人AI档案/知识库/AI学习库/"
THRESHOLD = 3  # ≥3张则非新领域

def count_cards_by_topic(topic_keyword):
    """统计包含指定主题关键词的立场卡数量"""
    count = 0
    matched_cards = []
    keyword_lower = topic_keyword.lower()
    
    for f in AI_LIB_PATH.iterdir():
        if not f.name.startswith('立场卡#') or not f.suffix == '.md':
            continue
        
        try:
            # 只读取前50行（frontmatter+标题），不读整个文件，提升性能
            with open(f) as fp:
                lines = []
                for i, line in enumerate(fp):
                    if i >= 50:
                        break
                    lines.append(line)
                content = ''.join(lines)
            
            # 在frontmatter的topic字段和文件名中搜索关键词
            topic_match = re.search(r'^topic:\s*(.+)$', content, re.MULTILINE)
            topic_text = topic_match.group(1) if topic_match else ''
            
            # 文件名也包含主题信息
            filename_topic = f.name.replace('立场卡#', '').replace('.md', '')
            
            # 搜索关键词（不区分大小写）
            if (keyword_lower in topic_text.lower() or 
                keyword_lower in filename_topic.lower()):
                count += 1
                # 提取card_id
                card_id_match = re.match(r'立场卡#(S\d+[a-z]?)-', f.name)
                card_id = card_id_match.group(1) if card_id_match else f.name
                matched_cards.append(card_id)
        except Exception as e:
            print(f"⚠️ 读取文件失败 {f.name}: {e}", file=sys.stderr)
            continue
    
    return count, matched_cards

def main():
    if len(sys.argv) < 2:
        print("用法: python3 count_card_topic.py <主题关键词>")
        print("示例: python3 count_card_topic.py 碰撞机制")
        print("      python3 count_card_topic.py 数字分身")
        sys.exit(1)
    
    topic_keyword = sys.argv[1]
    count, matched_cards = count_cards_by_topic(topic_keyword)
    
    is_new_domain = count < THRESHOLD
    
    print(f"🔍 新领域判定 — 关键词: '{topic_keyword}'")
    print(f"")
    print(f"📊 包含该关键词的立场卡: {count} 张")
    print(f"📋 匹配的卡: {', '.join(matched_cards[:10])}{'...' if len(matched_cards) > 10 else ''}")
    print(f"")
    print(f"🎯 判定阈值: ≥{THRESHOLD}张 = 非新领域")
    print(f"")
    if is_new_domain:
        print(f"🔴 判定: 新领域（{count} < {THRESHOLD}）")
        print(f"   → 童灵在该领域的初审准确率尚未验证，需你确认")
        print(f"   → 该领域的卡不可自动通过，需你抽检")
    else:
        print(f"🟢 判定: 非新领域（{count} ≥ {THRESHOLD}）")
        print(f"   → 童灵在该领域有足够的初审经验")
        print(f"   → 该领域的卡可参与自动通过判定（还需满足其他条件）")
    print(f"")
    
    # 输出机器可读的结果（供其他脚本调用）
    result = {
        'topic': topic_keyword,
        'count': count,
        'threshold': THRESHOLD,
        'is_new_domain': is_new_domain,
        'matched_cards': matched_cards
    }
    print(f"--- JSON ---")
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # exit code: 0=非新领域, 1=新领域, 2=错误
    sys.exit(1 if is_new_domain else 0)

if __name__ == '__main__':
    main()
