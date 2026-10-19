#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
doenglingz_tsl_selfheal.py —— TSL 自愈检测器（TSL闭环冲刺·段3）

设计定位
--------
自动检测闭环断点 → **生成修订建议 + 台账留痕 → 你终审**。
复用 doenglingz_tsl_report.py 的聚合逻辑（⛔零新建统计口径）。

⛔ 红线（任务书 §8.1 · 铁律-022）
--------------------------------
只备料、不改契约——⛔DO NOT 自动改写 W1 契约措辞直接生效。
价值层（契约措辞）永不委托，童灵可生成建议供你终审。

上线门禁（立场卡 S271 · C-008 门槛判据前置 · 任务书 §8.4）
--------------------------------------------------------
本脚本是**高风险机制**（自动动作影响全会话状态位）→
⛔DO NOT 在段2 于真实环境跑通完整周期（≥1 轮：检测→报告→比对→无异常）之前挂 launchd 调度。
开发期仅允许 `--check` 手动跑 + `--state` 指向隔离副本测试。

检测项
------
1. guard_stall      台账沉默 > 24h → 守卫疑似停摆
2. w1_rate_drop     有效会话 ≥ MIN_SESSIONS_FOR_RATE 且会话级兑现率 < 85%
                    （样本不足时**不判**，防 n=1 误触发自愈——段2 实测 n=1 的教训）
3. channel_dropout  某通道历史有命中但今日零命中（观察域律 §3.4·扩D 核查）

用法
----
  python3 doenglingz_tsl_selfheal.py --check              # 手动检测（真实台账）
  python3 doenglingz_tsl_selfheal.py --state /tmp/x.json  # 隔离压测
  python3 doenglingz_tsl_selfheal.py --json               # 机器可读
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doenglingz_tsl_report as rpt  # 复用：单一统计口径，不抄第二份

SELFHEAL_STATE = os.path.expanduser("~/.workbuddy/doenglingz_selfheal_state.json")
MIN_SESSIONS_FOR_RATE = 5   # 样本不足不判兑现率（段2 实测 n=1 教训·防误触发）
STALL_HOURS = 24
DROPOUT_DAYS = 3           # 连续 3 天零命中才算掉线（单日零命中=低频通道正常静默·首版实测误报）

# 真问题类型（写台账留痕）；信息型（insufficient_sample）只 stdout，不写台账防噪声
ACTIONABLE = {"guard_stall", "w1_rate_drop", "channel_dropout"}


def detect(rows, now=None):
    now = now or datetime.now()
    issues = []
    today = now.strftime("%Y-%m-%d")

    # 1) 守卫停摆
    if rows:
        last = max(str(d.get("ts", "")) for d in rows)
        try:
            last_dt = datetime.strptime(last, "%Y-%m-%dT%H:%M:%S")
            gap_h = (now - last_dt).total_seconds() / 3600
            if gap_h > STALL_HOURS:
                issues.append({
                    "type": "guard_stall",
                    "detail": f"台账末条 {last}，沉默 {gap_h:.1f}h > {STALL_HOURS}h",
                    "advice": "检查 settings.json Stop 链挂载 + registry_guards.sh 自动发现（铁律-016：查实盘不查看板）",
                })
        except ValueError:
            pass  # 时间格式异常不误报

    # 2) 会话级兑现率（样本充足才判）
    agg = rpt.aggregate(rows)
    s = agg["session"]
    if s["total"] >= MIN_SESSIONS_FOR_RATE:
        if s["rate"] is not None and s["rate"] < rpt.T2_MIN_RATE:
            issues.append({
                "type": "w1_rate_drop",
                "detail": f"会话级兑现率 {s['rate']*100:.0f}% < {rpt.T2_MIN_RATE*100:.0f}%（有效会话 n={s['total']}）",
                "advice": "先核注入台账 doenglingz_inject_state.json 的 w1:true 是否真实到达（宿主收讫律·别拿自己这侧动作当对侧结果）；到达而未兑现 → 生成 W1 契约措辞修订建议（备料·台账留痕·你终审，⛔不自动生效）",
            })
    else:
        issues.append({
            "type": "insufficient_sample",
            "detail": f"有效会话 {s['total']} < {MIN_SESSIONS_FOR_RATE}，兑现率判定跳过（防小样本误触发）",
            "advice": f"继续累积会话级样本（转正门槛 T1≥{rpt.T1_MIN_SESSIONS} 才有统计意义）",
        })

    # 3) 通道掉线（历史有命中 · 连续 DROPOUT_DAYS 天零命中·今日不计——天未结束）
    #    首版判"今日零命中"实测误报：ts_l3_slice_report/ts_l4_loaded 属低频通道，
    #    单日无触发场景 ≠ 掉线（2026-09-09 真实台账 2 条误报实证）→ 改连续 N 天。
    dates = sorted({str(d.get("ts", ""))[:10] for d in rows}, reverse=True)
    for k in rpt.TSL_8:
        had = any(k in (d.get("tsl_hits") or "") for d in rows)
        if not had:
            continue
        zero_days = 0
        for dt in dates:
            if dt >= today:
                continue  # 今日不计（天未结束·防半日误判）
            day_rows = [d for d in rows if str(d.get("ts", ""))[:10] == dt]
            if any(k in (d.get("tsl_hits") or "") for d in day_rows):
                break
            zero_days += 1
        if zero_days >= DROPOUT_DAYS:
            issues.append({
                "type": "channel_dropout",
                "detail": f"通道 `{k}` 连续 {zero_days} 天零命中（历史曾有·≥{DROPOUT_DAYS} 天）",
                "advice": "按守卫编写规范 §3.4·扩D 观察域律核查：pattern 死 / 产出物域变化 / 真无触发场景（三者定性不同，处置不同）",
            })
    return issues, agg


def record(issues, state_path):
    """真问题写台账留痕（JSONL append·O_APPEND）。返回写入条数。"""
    n = 0
    with open(state_path, "a", encoding="utf-8") as f:
        for it in issues:
            if it["type"] not in ACTIONABLE:
                continue
            f.write(json.dumps(
                {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                 "status": "suggestion_pending_review", **it},
                ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="TSL 自愈检测器（段3·只备料不改契约）")
    ap.add_argument("--check", action="store_true", help="手动检测一次")
    ap.add_argument("--state", default=None, help="覆盖台账路径（隔离压测用）")
    ap.add_argument("--out-state", default=None, help="覆盖自愈台账路径（测试用）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    if a.state:
        rpt.STATE = os.path.expanduser(a.state)  # 隔离：只改读源，不碰真实台账
    out_state = os.path.expanduser(a.out_state) if a.out_state else SELFHEAL_STATE

    rows = rpt.load_rows(None)
    issues, agg = detect(rows)

    if a.json:
        print(json.dumps({"issues": issues,
                          "recorded": record(issues, out_state),
                          "selfheal_state": out_state},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"🩺 TSL 自愈检测（{datetime.now().strftime('%Y-%m-%d %H:%M')}）")
    print(f"   台账 {agg['rows']} 条 · 有效会话 {agg['sessions']} · "
          f"历史无 session_id {agg.get('legacy_turns', 0)} 条（已排除会话级）")
    if not issues:
        print("✅ 无闭环断点")
        return 0
    for it in issues:
        tag = "🔴" if it["type"] in ACTIONABLE else "ℹ️"
        print(f"\n{tag} [{it['type']}] {it['detail']}")
        print(f"   → 建议：{it['advice']}")
    recorded = record(issues, out_state)
    if recorded:
        print(f"\n📌 {recorded} 条建议已留痕 → {out_state}（status=suggestion_pending_review·待你终审）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
