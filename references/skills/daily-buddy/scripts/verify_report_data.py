#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_report_data.py — 月报数据回读校验（数据可信度闭环·第三层）

设计哲学：报告写完后，自动把报告中的关键数字与数据快照/源头对比，
不一致就报错拦截，不允许交付。从"靠AI自觉核实"变成"靠脚本机械校验"。

校验流程：
  1. 读取月报文件，逐行扫描
  2. 对每个校验规则，用正则提取月报中的数字
  3. 与快照中的值对比（支持容差）
  4. 输出不一致项（行号+月报值+快照值+规则名）
  5. 退出码：0=全部通过，1=有不一致，2=参数错误（argparse缺参），7=环境自检失败（沙箱假python·审查P2-3补）

用法：
  python3 verify_report_data.py --report /path/to/monthly_report.md --snapshot /path/to/snapshot.json
  python3 verify_report_data.py --report 2026-08-月总结.md --month 2026-08
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

# === 环境自愈（第一性原理根治·Hermes 沙箱 HOME 劫持·与其他脚本同律）===
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv

HOME = str(dbenv.HOME)
DEFAULT_SNAPSHOT_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "daily-buddy", "data_snapshots")


def extract_number(text, pattern, group=0):
    """从文本中用正则提取数字，返回float或None。
    优先使用捕获组（group 1+），只有无捕获组时才用整个匹配（group 0）。
    """
    m = re.search(pattern, text)
    if not m:
        return None
    try:
        # 优先使用捕获组（如果有）
        if m.lastindex and m.lastindex >= 1:
            for g in range(1, m.lastindex + 1):
                if m.group(g):
                    val = m.group(g)
                    num_m = re.search(r"[\d.]+", val)
                    if num_m:
                        return float(num_m.group(0))
        # 无捕获组或捕获组都为空，用整个匹配
        val = m.group(0)
        num_m = re.search(r"[\d.]+", val)
        return float(num_m.group(0)) if num_m else None
    except (IndexError, AttributeError):
        return None


def compare_values(report_val, snapshot_val, tolerance=0.1):
    """比较两个值，支持容差。返回(是否一致, 差异描述)"""
    if report_val is None:
        return False, "月报中未提取到该数字"
    if snapshot_val is None:
        return True, "快照中无此值（跳过）"
    diff = abs(report_val - snapshot_val)
    if diff <= tolerance:
        return True, f"一致（差异{diff}≤容差{tolerance}）"
    return False, f"不一致（月报={report_val}, 快照={snapshot_val}, 差异={diff}）"


# === 校验规则定义 ===
# 每条规则：(规则名, 快照字段路径, 月报提取正则, 容差, 严重级别, 是否可选)
# 可选规则：月报中没有该指标不算错误，有则校验
# 快照字段路径用点号分隔，如 "diary.total_tomato.value"
VERIFICATION_RULES = [
    # === 日记维度 ===
    ("日记总天数", "diary.total_days.value",
     r"(\d+)/31.*100%|完整率[^\d]*(\d+)\s*/\s*\d+", 0, "high", False),  # 2026-10-01修复：原正则硬编码/31，30天月份（如9月）永远无法匹配（30/30写法被拒）

    ("番茄总数", "diary.total_tomato.value",
     r"番茄[^\d]*(\d+(?:\.\d+)?)[^\d]*(?:日均|$)", 0, "high", False),  # 2026-10-01修复：原(\d+)吞不掉小数（如525.5），半番茄总数永远差0.5过不了容差0

    ("日均番茄", "diary.avg_tomato.value",
     r"日均\s*([\d.]+)", 0.2, "medium", False),

    ("睡眠日均", "diary.avg_sleep_hours.value",
     r"睡眠日均\s*([\d.]+)\s*h|日均.*?([\d.]+)h", 0.1, "high", False),

    ("睡眠总时长", "diary.total_sleep_hours.value",
     r"(?:总睡眠|睡眠总时长|睡眠合计)[^\d]*([\d.]+)\s*h", 0.5, "medium", True),

    ("睡眠≥7h天数", "diary.sleep_ge7_days.value",
     r"(?:≥7h|7h达标)[^\d]{0,10}~?\s*(\d+)\s*天", 0, "medium", False),

    ("睡眠<6h天数", "diary.sleep_lt6_days.value",
     r"<6h天?\s*\|\s*(\d+)|<6h[^\d<]{0,10}(\d+)\s*天", 0, "medium", False),

    ("睡眠<5h天数", "diary.sleep_lt5_days.value",
     r"<5h[^\d]*(\d+)\s*天", 0, "medium", False),

    ("A级天数", "diary.rating_distribution.value.A",
     r"(\d+)A|A[^\d]*(\d+)\s*天|A级[^\d]*(\d+)", 0, "medium", False),

    ("B级天数", "diary.rating_distribution.value.B",
     r"(\d+)B|B[^\d]*(\d+)\s*天|B级[^\d]*(\d+)", 0, "medium", False),

    ("C级天数", "diary.rating_distribution.value.C",
     r"(\d+)C|C[^\d]*(\d+)\s*天|C级[^\d]*(\d+)", 0, "medium", False),

    # === 概念库维度 ===
    ("概念卡总数", "concept_health.concept_total.value",
     r"概念(?:卡|全集)[^\d]*(\d+)", 0, "high", False),

    ("碰撞队列总数", "concept_health.collision_queue_total.value",
     r"总候选[^\d]*(\d+)|候选配对[^\d]*(\d+)", 0, "medium", True),

    ("碰撞队列consumed", "concept_health.collision_queue_consumed.value",
     r"consumed[=:：]\s*(\d+)|(\d+)对假pending.*?已对账", 0, "medium", False),

    ("碰撞队列pending", "concept_health.collision_queue_pending.value",
     r"真?pending[^\d]*(\d+)|待碰撞[^\d]*(\d+)", 0, "high", False),

    ("合格可碰pending", "concept_health.collision_queue_qualified_pending.value",
     r"合格[^\d]*(\d+)|跨域跨主体[^\d]*(\d+)", 0, "medium", False),

    ("碰撞产出卡(.md)", "concept_health.collision_output_cards_md.value",
     r"碰撞产出[^\d]*(\d+)\s*张|产出卡[^\d]*(\d+)\s*张", 0, "high", False),

    ("概念碰撞覆盖率", "concept_health.collision_coverage_rate.value",
     r"覆盖率[^\d]*([\d.]+)\s*%", 0.5, "high", False),

    ("参与碰撞概念数", "concept_health.concepts_in_collision.value",
     r"参与碰撞的不同概念[^\d]*(\d+)|参与碰撞[^\d]*(\d+)\s*个", 0, "medium", False),

    ("未参与碰撞概念数", "concept_health.concepts_not_in_collision.value",
     r"(\d+)个概念未参与|未参与碰撞[^\d]*(\d+)", 0, "medium", False),

    # === 视频维度 ===
    ("视频发布条数", "video.video_publish_count.value",
     r"视频发布[^\d]*(\d+)\s*条|发布.*?(\d+)\s*条.*?视频", 0, "high", False),

    # === 系统日志维度 ===
    ("系统日志篇数", "syslog.syslog_count.value",
     r"系统日志[^\d]*(\d+)\s*篇", 0, "low", False),
]


def get_snapshot_value(snapshot, path):
    """从快照中按点号路径取值"""
    keys = path.split(".")
    val = snapshot
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return None
    return val


def verify_report(report_path, snapshot_path):
    """执行校验，返回结果列表"""
    # 读取快照
    with open(snapshot_path, encoding="utf-8") as f:
        snapshot = json.load(f)

    # 读取月报
    with open(report_path, encoding="utf-8") as f:
        report_lines = f.readlines()
    report_text = "".join(report_lines)

    results = []
    for rule_name, snapshot_path_key, pattern, tolerance, severity, optional in VERIFICATION_RULES:
        snapshot_val = get_snapshot_value(snapshot, snapshot_path_key)
        # 从月报全文提取（优先全文，因为数字可能跨行或在表格中）
        report_val = extract_number(report_text, pattern)

        # 如果全文没提取到，尝试逐行提取并记录行号
        line_num = None
        if report_val is None:
            for i, line in enumerate(report_lines, 1):
                val = extract_number(line, pattern)
                if val is not None:
                    report_val = val
                    line_num = i
                    break
        else:
            # 全文提取到了，找第一次出现的行号
            for i, line in enumerate(report_lines, 1):
                if extract_number(line, pattern) is not None:
                    line_num = i
                    break

        # 可选规则：月报中没有该指标不算错误
        if optional and report_val is None:
            is_match = True
            desc = "可选规则·月报未包含该指标（跳过）"
        else:
            is_match, desc = compare_values(report_val, snapshot_val, tolerance)
        results.append({
            "rule": rule_name,
            "snapshot_value": snapshot_val,
            "report_value": report_val,
            "line": line_num,
            "match": is_match,
            "desc": desc,
            "severity": severity,
            "pattern": pattern,
            "optional": optional,
        })

    return results


def print_results(results, report_path):
    """打印校验结果"""
    total = len(results)
    passed = sum(1 for r in results if r["match"])
    failed = total - passed
    high_failed = sum(1 for r in results if not r["match"] and r["severity"] == "high")
    optional_skipped = sum(1 for r in results if r["optional"] and r["report_value"] is None)

    print(f"\n{'='*60}")
    print(f"📊 月报数据校验报告")
    print(f"{'='*60}")
    print(f"报告文件: {report_path}")
    print(f"校验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"校验规则: {total}条（其中可选{optional_skipped}条已跳过）")
    print(f"通过: {passed}条 | 未通过: {failed}条 (其中高优先级{high_failed}条)")
    print(f"{'='*60}\n")

    # 有痕跳过（审查P2-8）：快照缺值的"跳过"不得静默——快照脚本改字段名/漏采时规则会整组失效
    snapshot_skipped = sum(1 for r in results if r["match"] and r["snapshot_value"] is None and not r["optional"])
    if snapshot_skipped > 0:
        print(f"⚠️ 有痕跳过：{snapshot_skipped}条规则因快照缺值未实际比对（非通过·快照可能漏采，建议核查monthly_data_snapshot输出）")
    if failed > 0:
        print("❌ 未通过项：")
        print("-" * 60)
        for r in results:
            if not r["match"]:
                severity_mark = "🔴" if r["severity"] == "high" else "🟡"
                line_info = f"行{r['line']}" if r["line"] else "全文未匹配"
                optional_mark = " [可选]" if r["optional"] else ""
                print(f"{severity_mark} [{r['rule']}]{optional_mark} {line_info}")
                print(f"   月报值: {r['report_value']} | 快照值: {r['snapshot_value']}")
                print(f"   说明: {r['desc']}")
                print()
    else:
        print("✅ 全部校验通过！月报数据与快照一致。")

    print("-" * 60)
    print(f"校验结果: {'❌ 未通过（需修正后重新校验）' if failed > 0 else '✅ 通过'}")
    return 1 if failed > 0 else 0


def main():
    if not dbenv.self_check(verbose=True):
        sys.exit(9)
    parser = argparse.ArgumentParser(description="月报数据回读校验")
    parser.add_argument("--report", required=True, help="月报文件路径")
    parser.add_argument("--snapshot", help="数据快照JSON路径（默认从data_snapshots目录按月份查找）")
    parser.add_argument("--month", help="月份YYYY-MM，用于自动查找快照（与--snapshot二选一）")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    args = parser.parse_args()

    # 确定快照路径
    if args.snapshot:
        snapshot_path = args.snapshot
    elif args.month:
        snapshot_path = os.path.join(DEFAULT_SNAPSHOT_DIR, f"{args.month}_data_snapshot.json")
    else:
        print("❌ 必须提供 --snapshot 或 --month", file=sys.stderr)
        return 1

    if not os.path.exists(snapshot_path):
        print(f"❌ 快照文件不存在: {snapshot_path}", file=sys.stderr)
        return 1
    if not os.path.exists(args.report):
        print(f"❌ 月报文件不存在: {args.report}", file=sys.stderr)
        return 1

    # 执行校验
    results = verify_report(args.report, snapshot_path)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        failed = sum(1 for r in results if not r["match"])
        return 1 if failed > 0 else 0
    else:
        return print_results(results, args.report)


if __name__ == "__main__":
    sys.exit(main())
