#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
report_backlog_guard.py — 评估报告积压自动检测守卫

本质分类：守卫类（守）
部署形态：Hook/管道（Stop 钩子链）
真相源：test_results/ 文件数量 vs 上次 L3 沉淀时点
时序协议：只读检测（守卫不修改任何评估文件）

职责：每当 Stop 事件触发时，扫描评估报告目录(test_results/skill_tests/)，
     与上次 L3 沉淀时间戳对比，若新报告数 ≥ 3 则在输出中显形告警。
     ≥ 5 则标记 L3 沉淀 overdue。
     纯 clock-loop 自身生效（其他 Skill 评估不影响 clock-loop 自身升级冻结）。

处置级别：中低损失审计层——命中→报告到日志（不拦截·Hook纪律）

设计依据：2026-09-22 你拍板"loop 安装包"应走 clock-loop G 路径；
     批判验证实证 G 路径设计上不经过阶段 4→报告积压检查天然被跳过。
     本脚本用事件驱动替代"AI 记得做"——报告产生=自动触发检测=结果进日志。

作者：Qoder CN
版本：v1.0.0
日期：2026-09-22

用法：
  python3 report_backlog_guard.py [--json] [--threshold-warn 3] [--threshold-trigger 5]

参数：
  --json              输出 JSON 格式（供 Stop hook 链消费）
  --threshold-warn    告警阈值（默认 3，自上次 L3 起新增 ≥3 份报告→⚠️提醒）
  --threshold-trigger L3 沉淀触发阈值（默认 5，≥5 触发 check_selfimprove_gate）
"""

import json
import os
import sys
import re
import glob
import argparse
from datetime import datetime

# ── 路径常量 ──
HOME = os.path.expanduser("~")
TEST_RESULTS_DIR = os.path.join(os.path.expanduser("[记忆共享中心]/评估知识库/test_results/skill_tests"),)
L3_EVOLUTION_DIR = os.path.join(os.path.expanduser("[记忆共享中心]/评估知识库/evolution"),)
SKILL_EVAL_SCRIPT = os.path.join(os.path.expanduser("[记忆共享中心]/技能配置/clock-loop/scripts/check_selfimprove_gate.py"),)
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def find_latest_l3_timestamp():
    """找最近一次 L3 沉淀的时间戳（文件名中的日期 或 文件内 l3_report_count 字段）。"""
    if not os.path.isdir(L3_EVOLUTION_DIR):
        return None, 0
    l3_files = sorted(glob.glob(os.path.join(L3_EVOLUTION_DIR, "L3_沉淀_*.md")))
    if not l3_files:
        return None, 0
    latest = l3_files[-1]
    # 从文件名提取日期 (L3_沉淀_2026-09-15*.md)
    m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(latest))
    date_str = m.group(1) if m else None
    # 从文件内容提取 l3_report_count
    count = 0
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            content = f.read(2000)
        cm = re.search(r'l3_report_count\s*[:：]\s*(\d+)', content)
        if cm:
            count = int(cm.group(1))
    except Exception:
        pass
    return date_str, count


def count_reports_since(last_date_str):
    """统计 test_results 中在 last_date_str 之后的评估报告数量。"""
    if not os.path.isdir(TEST_RESULTS_DIR):
        return 0, []
    all_reports = []
    for f in os.listdir(TEST_RESULTS_DIR):
        if '评估报告' in f and f.endswith('.md'):
            # 从文件名提取日期
            m = re.search(r'(\d{4}-\d{2}-\d{2})', f)
            if m:
                all_reports.append((m.group(1), f))
    all_reports.sort()
    if not last_date_str:
        return len(all_reports), [r[1] for r in all_reports]
    new_reports = [r for r in all_reports if r[0] > last_date_str]
    return len(new_reports), [r[1] for r in new_reports]


def run():
    parser = argparse.ArgumentParser(description="评估报告积压自动检测守卫")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    parser.add_argument("--threshold-warn", type=int, default=3)
    parser.add_argument("--threshold-trigger", type=int, default=5)
    args = parser.parse_args()

    # Step 1: 找最近 L3 沉淀时点
    l3_date, l3_count = find_latest_l3_timestamp()

    # Step 2: 统计其后的新报告数
    new_count, new_files = count_reports_since(l3_date)

    # Step 3: 判定
    if new_count >= args.threshold_trigger:
        verdict = "TRIGGER_L3"
        severity = "🔴"
        msg = f"L3沉淀 overdue——自上次沉淀({l3_date or '从未'})以来新增{new_count}份报告(≥{args.threshold_trigger})，下次阶段4须执行L3沉淀"
    elif new_count >= args.threshold_warn:
        verdict = "WARN"
        severity = "⚠️"
        msg = f"报告积压提醒：自上次L3沉淀({l3_date or '从未'})以来已新增{new_count}份报告(距触发阈值{args.threshold_trigger}还差{args.threshold_trigger - new_count}份)"
    else:
        verdict = "OK"
        severity = "✅"
        msg = f"报告积压正常({new_count}/{args.threshold_trigger})"

    result = {
        "guard": "report_backlog_guard",
        "version": "1.0.0",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "l3_last_date": l3_date,
        "l3_report_count": l3_count,
        "new_reports_since_l3": new_count,
        "verdict": verdict,
        "severity": severity,
        "message": msg,
        "new_files_sample": new_files[:5],  # 最多展示5个
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{severity} {msg}")
        if verdict != "OK" and new_files:
            print(f"  新增报告(前5): {', '.join(new_files[:5])}")

    # 始终 exit 0（不阻断·只报告）
    sys.exit(0)


if __name__ == "__main__":
    run()
