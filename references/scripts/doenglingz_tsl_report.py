#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/doenglingz_tsl_report.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
# version: v0.1
"""
doenglingz_tsl_report.py —— TSL 消费端对账报告器（TSL闭环冲刺·段2）

设计定位
--------
把 guard 台账的**逐回合原始观测**聚合成**会话级指标**（判据 = 皮叔 2026-09-09 拍板 A 会话级）。
段2 验收：报告器实跑出数，指标可追溯。

数据单一真源
------------
~/.workbuddy/doenglingz_guard_state.json（单行 JSON 追加台账）
⛔ 不建第二份台账、不落派生库——报告永远是台账的即时投影（防双本账）。

防镀金约束（立场卡 S030「改机制不镀金」）
--------------------------------------
每个指标必须给出**分子/分母 + 数据源条数**，⛔DO NOT 只给百分比。
样本不足时显式标 ⚠️ 并给出门槛差距，⛔不粉饰。

口径
----
- 会话级（决策口径）：同一 session_id 内**任一回合 honored → 该会话 honored**
- 回合级（对照口径）：逐条统计，用于异常定位
两者并列输出，决策以会话级为准。

用法
----
  python3 doenglingz_tsl_report.py                 # 全量，markdown 到 stdout
  python3 doenglingz_tsl_report.py --days 7        # 近 7 天
  python3 doenglingz_tsl_report.py --json          # 机器可读
  python3 doenglingz_tsl_report.py --out FILE      # 落盘
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import collections
import json
import os
import sys
from datetime import datetime, timedelta

STATE = os.path.expanduser("~/.workbuddy/doenglingz_guard_state.json")
# 2026-09-09（LobsterAI·皮叔令「能做的都做完」）：--ledger 参数化——各端台账共用同一报告器（⛔不建第二套）
STATE_OVERRIDE = None

TSL_8 = [
    "ts_l3_ritual", "ts_l3_slice_report", "ts_l4_loaded", "ts_l5_selfcheck",
    "ts_l6_sync", "ts_l7_growth", "ts_l7_syslog", "ts_l7_reflection",
]

# 转正证据门槛（任务书 §四）——报告只做对照，不代判
T1_MIN_SESSIONS = 30
T2_MIN_RATE = 0.85
T3_COVERAGE = 8


def load_rows(days=None):
    """读台账；days 为 None = 全量。⛔只读，绝不写台账。"""
    rows = []
    if not os.path.exists(STATE):
        return rows
    cutoff = None
    if days:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    with open(STATE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if cutoff and str(d.get("ts", ""))[:10] < cutoff:
                continue
            rows.append(d)
    return rows


def aggregate(rows):
    # ── 回合级（对照口径）──
    t_hon = sum(1 for d in rows if d.get("w1_not_honored") == "honored")
    t_not = sum(1 for d in rows if d.get("w1_not_honored") == "not_honored")
    t_total = t_hon + t_not

    # ── 会话级（决策口径）──
    sess = collections.defaultdict(list)
    for d in rows:
        sid = d.get("session_id") or "(无session_id)"
        sess[sid].append(d)

    s_hon = s_not = s_none = 0
    legacy_turns = 0  # 段0（2026-09-09）改动前台账无 session_id → 无法按会话切分
    for sid, ds in sess.items():
        if sid == "(无session_id)":
            legacy_turns += len(ds)
            continue  # ⛔ 历史组合并会把 N 条挤成 1 个假会话→会话级指标失真
        vals = [d.get("w1_not_honored") for d in ds]
        if "honored" in vals:
            s_hon += 1
        elif "not_honored" in vals:
            s_not += 1
        else:
            s_none += 1  # 该会话无 W1 触发（不计入分母）
    s_total = s_hon + s_not

    # ── 8 通道覆盖（按会话计：会话内任一回合命中 = 该会话覆盖）──
    cov = {}
    for k in TSL_8:
        cov[k] = sum(1 for sid, ds in sess.items()
                     if sid != "(无session_id)"
                     and any(k in (d.get("tsl_hits") or "") for d in ds))
    covered = sum(1 for k in TSL_8 if cov.get(k))

    # ── 守卫检出率 ──
    detected = sum(1 for d in rows if d.get("tsl_hits") or d.get("w1_not_honored"))

    return {
        "rows": len(rows),
        "sessions": len(sess) - (1 if "(无session_id)" in sess else 0),
        "legacy_turns": legacy_turns,
        "turn": {"honored": t_hon, "not_honored": t_not, "total": t_total,
                 "rate": (t_hon / t_total) if t_total else None},
        "session": {"honored": s_hon, "not_honored": s_not, "no_trigger": s_none,
                    "total": s_total,
                    "rate": (s_hon / s_total) if s_total else None},
        "coverage": cov,
        "covered_channels": covered,
        "detected": detected,
    }


def gate_status(a):
    """对照转正门槛 T1/T2/T3——只报达标与否，⛔不代你裁决转正。"""
    s_rate = a["session"]["rate"]
    return {
        "T1_sessions": {"value": a["sessions"], "need": T1_MIN_SESSIONS,
                        "pass": a["sessions"] >= T1_MIN_SESSIONS},
        "T2_rate": {"value": s_rate, "need": T2_MIN_RATE,
                    "pass": (s_rate is not None and s_rate >= T2_MIN_RATE)},
        "T3_coverage": {"value": a["covered_channels"], "need": T3_COVERAGE,
                        "pass": a["covered_channels"] >= T3_COVERAGE},
    }


def render_md(a, g, days):
    def pct(v):
        return "—" if v is None else f"{v*100:.1f}%"

    rng = f"近 {days} 天" if days else "全量"
    L = []
    L.append(f"# TSL 消费端对账报告（{rng}）")
    L.append("")
    L.append(f"> 生成：{datetime.now().strftime('%Y-%m-%d %H:%M')} · "
             f"数据源 `{STATE}` · 台账 {a['rows']} 条 · 会话 {a['sessions']} 个")
    L.append("> ⛔ 报告=台账即时投影（时点快照非真相源），指标均可回台账逐条复核。")
    L.append("")
    L.append("## 一、W1 上岗兑现率（双口径）")
    L.append("")
    L.append("| 口径 | 兑现 | 未兑现 | 分母 | 兑现率 | 说明 |")
    L.append("|---|---|---|---|---|---|")
    L.append(f"| **会话级（决策口径）** | {a['session']['honored']} | "
             f"{a['session']['not_honored']} | {a['session']['total']} | "
             f"**{pct(a['session']['rate'])}** | 会话内任一回合 honored 即该会话 honored |")
    L.append(f"| 回合级（对照口径） | {a['turn']['honored']} | "
             f"{a['turn']['not_honored']} | {a['turn']['total']} | "
             f"{pct(a['turn']['rate'])} | 逐条统计，用于异常定位 |")
    if a["session"].get("no_trigger"):
        L.append("")
        L.append(f"> 另有 {a['session']['no_trigger']} 个会话无 W1 触发，不计入分母。")
    if a.get("legacy_turns"):
        L.append("")
        L.append(f"> ⚠️ **历史数据 {a['legacy_turns']} 条无 `session_id`**（段0 改动前产生）→ "
                 f"无法按会话切分，**不参与会话级统计**（若并入会把它们挤成 1 个假会话、指标失真）。"
                 f"该部分仍计入回合级对照口径。")
    L.append("")
    L.append("## 二、TSL 八通道覆盖")
    L.append("")
    L.append("| 通道 | 覆盖会话数 | 状态 |")
    L.append("|---|---|---|")
    for k in TSL_8:
        c = a["coverage"].get(k, 0)
        L.append(f"| `{k}` | {c} | {'✅' if c else '❌ 零覆盖'} |")
    L.append("")
    L.append(f"**覆盖 {a['covered_channels']}/8 通道**。")
    L.append("")
    L.append("## 三、守卫检出率")
    L.append("")
    L.append(f"- 有观测产出（tsl_hits 或 w1 判定）的记录："
             f"**{a['detected']}/{a['rows']}**"
             f"（{(a['detected']/a['rows']*100):.1f}%）" if a["rows"] else "- 无数据")
    L.append("")
    L.append("## 四、转正门槛对照（只报数，不代裁决）")
    L.append("")
    L.append("| 门槛 | 当前 | 要求 | 判定 |")
    L.append("|---|---|---|---|")
    L.append(f"| T1 有效会话样本 | {g['T1_sessions']['value']} | ≥{g['T1_sessions']['need']} | "
             f"{'✅' if g['T1_sessions']['pass'] else '⚠️ 未达（差 %d）' % (g['T1_sessions']['need']-g['T1_sessions']['value'])} |")
    L.append(f"| T2 W1 兑现率 | {pct(g['T2_rate']['value'])} | ≥{int(g['T2_rate']['need']*100)}% | "
             f"{'✅' if g['T2_rate']['pass'] else '⚠️ 未达'} |")
    L.append(f"| T3 通道覆盖 | {g['T3_coverage']['value']}/8 | {g['T3_coverage']['need']}/8 | "
             f"{'✅' if g['T3_coverage']['pass'] else '⚠️ 未达'} |")
    L.append("")
    if not all(x["pass"] for x in g.values()):
        L.append("> ⚠️ **样本/指标未达门槛**：按你拍板 ②=B 延长试用期，"
                 "转正绑门槛不绑日历，达标前继续按门槛复测。")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="TSL 消费端对账报告器（段2）")
    ap.add_argument("--days", type=int, default=None, help="近 N 天（默认全量）")
    ap.add_argument("--ledger", default=None, help="台账路径（默认 WB/AutoClaw 共用台账；LobsterAI=~/.workbuddy/doenglingz_guard_state_lobsterai.json）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--out", default=None, help="落盘路径（默认仅 stdout）")
    a = ap.parse_args()
    global STATE
    if getattr(a, "ledger", None):
        STATE = os.path.expanduser(a.ledger)

    rows = load_rows(a.days)
    agg = aggregate(rows)
    g = gate_status(agg)

    if a.json:
        out = json.dumps({"aggregate": agg, "gate": g}, ensure_ascii=False, indent=2)
    else:
        out = render_md(agg, g, a.days)

    if a.out:
        with open(os.path.expanduser(a.out), "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"OK: 报告已落盘 → {a.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
