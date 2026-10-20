#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb_query_trail.py — 单次查询完整命中路径观测器（C1·OpenViking 借鉴落地·2026-09-07）

OpenViking 借鉴 L3 深评（键 20260907_203041）唯一过闸项 C1 的落地组件：
「单次查询完整命中路径审计/回放」——每次知识激活记录：任务 → 意图桶 → 召回卡
（src/title/score/matched 命中词，含 ⚡语义#N 纯向量标记）→ 候选总数 → 时间。

设计约束：
- ⛔ 不修改 search_kb.py 一行（单一真源零回归——eval 24/24 由 eval_search_kb 直调 search 保障）。
- 观测点 = kb_inject_prompt.py 的 _inject() 成功路径（真实 UserPromptSubmit 流量汇聚：
  快通道 kb_serve 或回退本地冷跑，两者都产出 (scores, buckets)）。
- 消费端（Agent B 修正①·防"并入即消解"）：v1.6 语义路由质变立项时读本 jsonl 做
  路由质量分析（哪桶召回差/纯向量占比/matched 词分布），驱动 route_table 关键词调优
  + MAB 自进化。本文件=观测层实体，消费对接在 v1.6。
- 仅 stdlib 依赖（json/os/time/datetime）——kb_inject_prompt 快通道 import 零开销。

用法:
  python3 kb_query_trail.py --tail N        # 看最近 N 条查询链路
  python3 kb_query_trail.py --replay "串"    # 回放含该串 task/ts 的查询链路
"""
import json
import os
import sys
import time
from datetime import datetime

# Windows 控制台守卫（V9·包内判据）：cp1252/cp936 控制台下中文/emoji print 必崩
try:
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
# logs 目录在引擎根（知识联邦引擎/logs/），非 scripts/logs/——与 kb_degrade.jsonl 同位
ENGINE_ROOT = os.path.dirname(BASE)
TRAIL_LOG = os.path.join(ENGINE_ROOT, "logs", "kb_query_trail.jsonl")


def _serialize_hit(item):
    """统一快通道/本地冷跑的 scores 元素 → dict。元素形态:
    - 本地冷跑: (s, p, d, matched)  d 含 src/title/summary
    - 快通道:   (score, path, {src,title,summary}, matched)
    两者结构同构（score/path/doc/summary/matched），兼容处理。"""
    try:
        s, p, d, matched = item
    except Exception:
        return None
    if isinstance(d, dict):
        src = d.get("src", "")
        title = d.get("title", "")
        summary = d.get("summary", "")[:60]
    else:
        src = title = summary = ""
    return {"score": round(float(s), 4), "path": p,
            "src": src, "title": title, "summary": summary,
            "matched": (matched or [])[:8]}


def append_trail(task, scores, buckets, source="inject", nat=None):
    """记录一次查询的完整命中路径。失败静默（观测层不阻断检索主流程·对齐 _log_degrade）。
    buckets 形态兼容: kb_inject 本地冷跑传 [桶名,...] 列表; 快通道传 resp.get('buckets') 同列表。"""
    try:
        rec = {
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task": task[:200],
            "buckets": list(buckets) if buckets else [],
            "n_candidates": len(scores),
            "source": source,
            "hits": [h for h in (_serialize_hit(x) for x in scores[:10]) if h],
            **({"nat_rank": nat} if nat else {}),  # A4 2026-10-17 强插卡自然名次(缺省=无插位,老行格式兼容)
        }
        with open(TRAIL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def _tail(n=5):
    if not os.path.isfile(TRAIL_LOG):
        print("trail 日志尚不存在（尚无查询被记录）")
        return
    lines = open(TRAIL_LOG, encoding="utf-8").read().splitlines()
    for line in lines[-n:]:
        try:
            d = json.loads(line)
        except Exception:
            continue
        print("─" * 60)
        print(f"[{d.get('ts')}] 桶={','.join(d.get('buckets') or [])} | 候选={d.get('n_candidates')} | 源={d.get('source')}")
        print(f"任务: {d.get('task')}")
        for h in (d.get("hits") or [])[:3]:
            print(f"  · {h.get('score')} | {h.get('src')} | {h.get('title')}")
            print(f"    命中: {', '.join(h.get('matched') or [])[:80]}")


def _replay(needle):
    if not os.path.isfile(TRAIL_LOG):
        print("trail 日志尚不存在")
        return
    found = 0
    for line in open(TRAIL_LOG, encoding="utf-8"):
        if needle not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        found += 1
        print("═" * 60)
        print(f"任务: {d.get('task')}")
        print(f"时间: {d.get('ts')} | 意图桶: {', '.join(d.get('buckets') or [])} | 候选: {d.get('n_candidates')} | 源: {d.get('source')}")
        for h in (d.get("hits") or []):
            print(f"[{h.get('score')}] {h.get('src')} | {h.get('title')}")
            print(f"    命中词: {', '.join(h.get('matched') or [])[:100]}")
    print(f"\n共回放 {found} 条")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--tail":
        _tail(int(args[1]) if len(args) > 1 else 5)
    elif args and args[0] == "--replay" and len(args) > 1:
        _replay(args[1])
    else:
        print(__doc__)
        print("用法见上。观测自动生效于 kb_inject_prompt 知识激活路径。")


if __name__ == "__main__":
    main()
