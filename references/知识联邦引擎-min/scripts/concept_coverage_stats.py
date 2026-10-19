#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
concept_coverage_stats.py — 立场卡「概念卡下游覆盖率」全量基线统计（只读·零新建数据）
设计依据: 去重/融合机制任务书 #6（2026-10-08 童灵D3代行·使用者认可）+ §3.10 第一阶方案（简单入度）
数据来源: [记忆共享中心]/知识库/AI学习库/INDEX.md「碰撞来源」列——解析逻辑与 concept_projection.py
          parse_index() 同构（同一正则口径，防双源判据漂移）
输出指标: ①总立场卡数 ②入度=0卡数及占比（闲置候选率）③入度分布(0/1/2/3+)
          ④平均入度 ⑤中位入度
判读纪律（三明治L1核心修正·⛔越界）:
  覆盖率=闲置【候选信号】，≠闲置【判定标准】。入度0的卡可能是独特好卡——
  本脚本只出候选清单口径，⛔不做任何归档决策；处置走 collision-consumption.md §十
  （童灵读卡判断+使用者抽查人工兜底）。
数据质量声明（最大熵·诚实标注）: 概念卡文件存在截断（约75张未参与投影，任务书 §3.10），
  统计基于 INDEX 碰撞来源列全量文本，入度值为【下限估计】（实际≥统计值）。
用法: python3 concept_coverage_stats.py
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import statistics

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, AILIB_DIR
INDEX = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None

# 与 concept_projection.parse_index 同口径（带方括号的碰撞来源对）
PAIR_RE = re.compile(r"\[(C-[0-9]+)\s*[×x]\s*(C-[0-9]+)\]")
LOOSE_RE = re.compile(r"C-[0-9]+\s*[×x]\s*C-[0-9]+")


def collect():
    """扫 INDEX 全部立场卡行 → {card_id: set(concepts)}；技能卡/表头/分隔行不计"""
    deg = {}
    bad_format = []
    for line in open(INDEX, encoding="utf-8"):
        if not line.startswith("| 立场卡"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        cid = cells[0]
        src = cells[-1]  # 碰撞来源列（末列）
        m = PAIR_RE.search(src)
        if m:
            deg.setdefault(cid, set()).update((m.group(1), m.group(2)))
        elif LOOSE_RE.search(src):
            # 不合规格式（缺方括号）——投影也会漏它，单列报告不静默吞
            bad_format.append(cid)
        else:
            deg.setdefault(cid, set())  # 非碰撞卡/占位文本 → 入度0（候选）
    return deg, bad_format


def main():
    if INDEX is None or not os.path.exists(INDEX):
        raise SystemExit(f"❌ INDEX 不存在: {INDEX}（未安装态或先跑 regen_ailib_index.py）")
    deg, bad_format = collect()
    total = len(deg)
    if total == 0:
        raise SystemExit("❌ 未解析到任何立场卡行（INDEX 结构变了？先查仪器再下结论）")
    degrees = sorted(len(v) for v in deg.values())
    zero_cards = [c for c, v in deg.items() if not v]
    z = len(zero_cards)
    dist = {k: sum(1 for d in degrees if d == k) for k in (0, 1, 2)}
    dist[3] = sum(1 for d in degrees if d >= 3)

    print("=== 概念卡下游覆盖率·全量基线（第一阶·简单入度）===")
    print(f"① 总立场卡数（INDEX 行·含新卡·分母不排新卡=简单即是美）: {total}")
    print(f"② 入度=0 卡数: {z}（{z / total * 100:.1f}%）← 闲置【候选】占比·非判定 ⚠️下限估计（约75张概念卡截断未投影）")
    print("③ 入度分布:")
    for k, label in ((0, "0（极可能闲置候选）"), (1, "1（可能闲置候选）"), (2, "2"), (3, "3+（活跃）")):
        print(f"   {label}: {dist[k]} 张（{dist[k] / total * 100:.1f}%）")
    print(f"④ 平均入度: {statistics.mean(degrees):.2f}")
    print(f"⑤ 中位入度: {statistics.median(degrees)}")
    if bad_format:
        print(f"⚠️ 碰撞来源缺方括号（投影同样漏·先修格式再算数）: {len(bad_format)} 张 → {', '.join(bad_format[:10])}{'…' if len(bad_format) > 10 else ''}")
    print("---")
    print("判读纪律: 入度0/1=候选清单，处置必须走童灵读卡+使用者抽查人工兜底（§十/§10.2），⛔本脚本输出不直接触发归档。")
    print(f"阈值校准参照（任务书§3.9·闲置率>30%触发存量去重审计·经验值待校准）: 当前候选闲置率 {z / total * 100:.1f}%")


if __name__ == "__main__":
    main()
