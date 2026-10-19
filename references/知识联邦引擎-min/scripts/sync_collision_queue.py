#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_collision_queue.py — 碰撞候选队列 ↔ INDEX 对账同步（根治回写失真）

问题根因（2026-08-25 发现）：
  collision_candidates.json 的 status 靠碰撞消费时手动回写，无机械强制点（C-072 同构：
  纸面规则无机械执行=零），39 轮实战大量消费未回写队列 → 781/1181 pending 实为 INDEX
  已综合的"假 pending"，筛选时 87% 撞重复综合。

解法（单一事实源原则）：
  INDEX.md 碰撞来源列 = 权威历史（[C-X × C-Y] → 立场卡#Sxxx）
  collision_candidates.json = 派生数据，由本脚本幂等对账对齐：
    - pending 且 pair 已在 INDEX → status=consumed + collided_to=对应卡 + synced_from=index
    - 其余不动（consumed / 真 pending 保持）

用法：
  python3 sync_collision_queue.py            # 执行对账（幂等·可重复跑）
  python3 sync_collision_queue.py --dry-run  # 只报告影响面，不写回
  python3 sync_collision_queue.py --stats    # 只输出统计（含真 pending 合格数）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import re
import sys
from collections import Counter, defaultdict

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, FED, AILIB_DIR
QUEUE_PATH = os.path.join(FED, "collision_candidates.json") if FED else None
INDEX_PATH = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None


def load_index_pairs():
    """INDEX 权威：碰撞来源 pair → [卡号...]（按 INDEX 出现顺序）"""
    pairs = defaultdict(list)
    with open(INDEX_PATH) as f:
        for line in f:
            m = re.search(r"\|\s*(立场卡#S\d+)\s*\|.*?\[(C-\d+) × (C-\d+)\]", line)
            if m:
                card, a, b = m.group(1), m.group(2), m.group(3)
                pairs[tuple(sorted([a, b]))].append(card)
    return pairs


def main():
    args = set(sys.argv[1:])
    dry_run = "--dry-run" in args
    stats_only = "--stats" in args

    if not INSTALLED or not QUEUE_PATH or not INDEX_PATH:
        print("[sync_collision_queue] 未安装态（记忆共享中心自推导失败）——跳过对账，不污染暂存目录")
        return 0
    if not os.path.exists(QUEUE_PATH) or not os.path.exists(INDEX_PATH):
        print("[sync_collision_queue] 队列或 INDEX 尚不存在（先跑 collision_scan/regen_ailib_index）——跳过")
        return 0

    index_pairs = load_index_pairs()

    with open(QUEUE_PATH) as f:
        data = json.load(f)
    cands = data["candidates"]

    status_count = Counter(c.get("status") for c in cands)
    pending = [c for c in cands if c.get("status") == "pending"]
    false_pending = [c for c in pending if tuple(sorted(c["pair"])) in index_pairs]
    true_pending = [c for c in pending if tuple(sorted(c["pair"])) not in index_pairs]
    true_eligible = [c for c in true_pending if c.get("cross_domain") and c.get("cross_owner")]

    print(f"[sync_collision_queue] INDEX 权威 pair: {len(index_pairs)} | 队列候选: {len(cands)}")
    print(f"  队列状态: consumed={status_count.get('consumed',0)} pending={status_count.get('pending',0)}")
    print(f"  假 pending（INDEX 已综合·本次将回写）: {len(false_pending)}")
    print(f"  真 pending: {len(true_pending)}（其中跨域跨主体合格: {len(true_eligible)}）")

    if stats_only:
        return 0

    if dry_run:
        print(f"\n[dry-run] 将回写 {len(false_pending)} 条 pending→consumed（未写文件）")
        for c in false_pending[:8]:
            cards = index_pairs[tuple(sorted(c["pair"]))]
            print(f"    {c['pair']} → {cards[0]}")
        if len(false_pending) > 8:
            print(f"    ... 等共 {len(false_pending)} 条")
        return 0

    # 执行对账
    updated = 0
    for c in cands:
        if c.get("status") != "pending":
            continue
        key = tuple(sorted(c["pair"]))
        if key in index_pairs:
            c["status"] = "consumed"
            c["collided_to"] = index_pairs[key][0]
            c["synced_from"] = "index"
            updated += 1

    with open(QUEUE_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 对账完成: {updated} 条 pending→consumed（collided_to 已填 + synced_from=index）")
    print(f"   剩余真 pending: {len(true_pending)}（合格可碰: {len(true_eligible)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
