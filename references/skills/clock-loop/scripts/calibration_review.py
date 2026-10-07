#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# calibration_review.py — 校准台账聚合器 v1.0.2 (v3.38.0·2026-09-12)
# 定位: 补学习闭环断点(留痕→蒸馏→作用未来)——双盲分歧记录后无消费端, 本脚本做"蒸馏"端
# 功能: 读 calibration_ledger.json → 按 audit/date/归因三分 分组聚合 → 输出分歧清单 + 高频信号
# 变更: v1.0.2 消费端兼容 attribution 字段(归因三分: skill_defect/case_defect/judge_defect/待归因)
#       仅新增聚合维度与分组显示, 核心聚合逻辑不变; 旧台账无该字段时 get() 返回 None → 归"未标注"
#       语义根因提取(divergence 文本)由 AI 在双盲完成后读本报告提出候选→你确认
# 用法: python3 calibration_review.py [--ledger <路径>] [--min-count N]
# 退出: 0=正常(信息输出) 1=ledger 缺失/损坏
# 说明: 只聚合不裁决——修正候选须 AI 提出、你确认后改 skill_eval + 跑回归(判据不得自创原则)
# ============================================================
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, sys
from collections import Counter
from pathlib import Path

LEDGER_DEFAULT = "[记忆共享中心]/评估知识库/test_results/calibration_ledger.json"


def main() -> int:
    ledger_path = LEDGER_DEFAULT
    if "--ledger" in sys.argv:
        ledger_path = Path(sys.argv[sys.argv.index("--ledger") + 1])
    min_count = 1
    if "--min-count" in sys.argv:
        min_count = int(sys.argv[sys.argv.index("--min-count") + 1])

    if not ledger_path.exists():
        print(f"[FAIL] 校准台账不存在: {ledger_path}")
        return 1
    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] 校准台账解析失败: {e}")
        return 1

    entries = data if isinstance(data, list) else data.get("entries", [])
    if not entries:
        print("[i] 校准台账为空——暂无双盲分歧记录")
        return 0

    # 按 audit(第几次双盲)/date 分组(确定性部分)
    by_audit = Counter()
    by_date = Counter()
    by_attr = Counter()
    for e in entries:
        by_audit[e.get("audit") or "未标注"] += 1
        by_date[str(e.get("date") or "未知")[:10]] += 1
        by_attr[e.get("attribution") or "未标注"] += 1

    print(f"=== 校准台账聚合报告(共 {len(entries)} 条分歧) ===")
    print("\n按双盲轮次:")
    for k, v in by_audit.most_common():
        flag = " ← 需关注" if v >= min_count else ""
        print(f"  {k}: {v} 条{flag}")
    print("\n按日期:")
    for k in sorted(by_date):
        print(f"  {k}: {by_date[k]} 条")
    print("\n按归因三分(skill_defect/case_defect/judge_defect·待归因须闭环补归):")
    for k, v in by_attr.most_common():
        print(f"  {k}: {v} 条")

    print("\n=== 分歧清单(供 AI 语义根因提取→提修正候选→你确认) ===")
    for i, e in enumerate(entries, 1):
        div = (e.get("divergence") or "无分歧描述")[:120]
        act = (e.get("actions") or "无整改记录")[:60]
        print(f"  [{i}] {e.get('audit') or '?'} {e.get('date') or '?'}")
        print(f"      分歧: {div}")
        print(f"      整改: {act}")

    hot = [k for k, v in by_audit.items() if v >= min_count]
    print("\n=== 修正候选提示(供 AI 提候选·皮叔确认后执行) ===")
    if hot:
        for h in hot:
            print(f"  ⚠️ 「{h}」分歧 {by_audit[h]} 条——建议 AI 读上述分歧清单提取根因，提出检查项/考题修正候选")
    print("\n⛔ 本脚本只聚合不裁决——修正候选须 AI 提出、你确认后改 skill_eval + 跑回归(test_skill_eval)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
