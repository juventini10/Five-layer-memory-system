#!/usr/bin/env python3
"""
dedup_recall.py — Step 2.0 去重合并门·确定性召回脚本（v4.0.0 · Wave 3 建）

职责（方案§5.4 ①）：按 category + tags 交集检索 05-知识池 已有卡片，
输出小候选集供 AI 做 ADD/MERGE/SKIP 语义判断。
⛔不做语义判断——可规则化的交脚本，需判断的交模型。

用法：
  python3 dedup_recall.py <知识池根目录> --category <领域> --tags "词1,词2,..."
输出：候选卡列表（路径+card_id+title+tags 交集命中数），exit 0；无候选输出 EMPTY。

实体归一（G4 落项）：比较前全部归一化——小写 + 去空格/连字符/下划线，
「Agent 记忆 / Agent记忆 / agent memory」类变体命中同一候选集。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse, os, re, sys

# 单一 frontmatter 解析器来源：note_validator.parse_frontmatter（v4.2.0 · L9 修复）
# ⛔DO NOT 在此文件再写一份 parse_frontmatter——v4.2.0 前这里有一份分叉实现，
# 缺类型还原且多行数组处理有 bug，与 note_validator 漂移导致召回口径不一致。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from note_validator import parse_frontmatter

def normalize(s: str) -> str:
    """G4 实体归一：小写 + 剥空格/连字符/下划线。"""
    return re.sub(r'[\s\-_]+', '', s.lower())

def recall(pool_root: str, category: str, tags: list) -> list:
    """category 归一相等 且 tags 归一交集非空 → 候选。"""
    cat_n = normalize(category)
    tags_n = {normalize(t) for t in tags if t.strip()}
    hits = []
    for root, _, files in os.walk(pool_root):
        for f in files:
            if not f.endswith('.md') or f == 'INDEX.md':
                continue
            p = os.path.join(root, f)
            try:
                fm, _ = parse_frontmatter(open(p, encoding='utf-8').read())
            except Exception:
                continue
            if fm.get('type') != 'reading-card':
                continue
            if normalize(fm.get('category', '')) != cat_n:
                continue
            # tags 在 note_validator 解析后为 list（多行/行内数组），也兼容旧式逗号字符串
            raw_tags = fm.get('tags', [])
            if isinstance(raw_tags, str):
                card_tags = {normalize(t) for t in re.split(r'[,，\[\]]', raw_tags) if t.strip()}
            else:
                card_tags = {normalize(str(t)) for t in raw_tags if str(t).strip()}
            inter = tags_n & card_tags
            if inter:
                hits.append((p, fm.get('card_id', f), fm.get('title', ''), len(inter), sorted(inter)))
    hits.sort(key=lambda h: -h[3])
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pool_root')
    ap.add_argument('--category', required=True)
    ap.add_argument('--tags', required=True, help='逗号分隔')
    a = ap.parse_args()
    tags = [t for t in re.split(r'[,，]', a.tags) if t.strip()]
    hits = recall(a.pool_root, a.category, tags)
    if not hits:
        print('EMPTY — 候选为空，全部 ADD（按 dedup-merge-gate.md ③）')
        return
    print(f'候选 {len(hits)} 张（按 tags 交集命中数降序）：')
    for p, cid, title, n, inter in hits:
        print(f'  [{n}命中] {cid or title}  tags∩={inter}  ← {p}')

if __name__ == '__main__':
    main()
