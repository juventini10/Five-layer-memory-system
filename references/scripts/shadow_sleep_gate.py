#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shadow_sleep_gate.py v1.0 — 机械睡眠闸自动触发器（补「何时写」那一半）

背景（本脚本存在的唯一理由）：
  2026-09-29 上线的 shadow_append.py 解决了「怎么写」——解锁→插入→回锁的合法入口。
  但「何时写」一直是人肉环节：晚间复盘时 AI 得自己记得"检查一下睡眠连续天数"。
  结果 2026-10-02 审计发现 SHADOW 漏了两整段：
    · 9/19-9/24 连续6晚<6h（闸在 9/23 已达标，零写入）
    · 9/28-9/30 连续2晚<4h（9/29=2h59h 季度最低）
  shadow_append.py 是合法写入口，不是自动触发器——两件事，不能互相顶替。

机制：
  扫 Obsidian 日记的 sleep_duration 字段 → 算连续<6h天数 → 达阈值(≥5晚)即：
    ① 判定闸是否已触发（对比 SHADOW 已有条目，防重复写）
    ② 若已达标但未写入 → 输出待写入建议（--emit-draft）
    ③ 配 launchd 定时跑，达标即提醒；⛔ 不自动写盘（写入须过 shadow_append.py，
       且内容含归因等需判断的字段，AI 不过目就写=伪造你的行为记录）

用法：
  python3 shadow_sleep_gate.py              # 状态报告
  python3 shadow_sleep_gate.py --days 14    # 扫更长窗口
  python3 shadow_sleep_gate.py --emit-draft # 达标未写时输出待写入草稿
  python3 shadow_sleep_gate.py --json       # 机读（供其他守卫/面板消费）

出口：0=未达标或已写；3=达标但未写入（需人工/AI 补写·提醒级）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

SSOT = os.path.expanduser("[记忆共享中心]/潜意识层/SHADOW.md")
DIARY_DIR = os.path.expanduser("~/[日记仓库]/1-每日计划/01-日记")

GATE_THRESHOLD = 5   # shadow-protocol v3.7：连续≥5晚<6h 自动写入
HARD_FLOOR = 4.0     # 单晚<4h = 严重不足，无论连续几天都值得单独记


def read_sleep_days(days):
    """读最近 N 天日记的 sleep_duration，返回 [(date_str, hours)] 按日期升序。"""
    out = []
    today = date.today()
    for i in range(days, 0, -1):
        d = today - timedelta(days=i)
        path = os.path.join(DIARY_DIR, "{}-{:02d}.md".format(d.year, d.month), "{}.md".format(d.isoformat()))
        # 兼容两种目录结构
        if not os.path.exists(path):
            path = os.path.join(DIARY_DIR, "{}-{:02d}".format(d.year, d.month), "{}.md".format(d.isoformat()))
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                m = re.search(r"sleep_duration:\s*([0-9.]+)", f.read())
            if m:
                v = float(m.group(1))
                if v > 0:  # 0 = 未封口/占位
                    out.append((d.isoformat(), v))
        except OSError:
            continue
    return out


def compute_streak(data):
    """从最新往回数连续<6h 的天数，返回 (streak, streak_days)。"""
    streak = 0
    days = []
    for ds, v in reversed(data):
        if v < 6.0:
            streak += 1
            days.append((ds, v))
        else:
            break
    return streak, list(reversed(days))


def already_written(days_list):
    """检查这些日期是否已在 SHADOW 中有条目——防重复写。

    ⛔ 教训（2026-10-02 单测实证）：v1.0 初版只认「标题含'机械睡眠闸'」的条目，
    于是 9/30 那条标题是「睡眠连续2晚<4h·季度最低」的真实条目被判为"未写"，
    守卫会把刚补写的段再报一次要写——漏写过一次的地方，防重复写同时失效。
    判据改为【日期锚定】：机械闸条目的标题必以该段最后一天日期开头，
    不论标题怎么措辞都能命中。附加『连续N晚』的模糊匹配只作次级证据。
    """
    if not os.path.exists(SSOT) or not days_list:
        return False
    try:
        with open(SSOT, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return False

    # 主判据：段内最后一天的日期作为标题开头出现过（锚定，措辞无关）
    last_day = days_list[-1][0]
    if re.search(r"^### {}\s+\S".format(re.escape(last_day)), content, re.M):
        return True

    # 次级判据：段内任一天 + 连续晚数同时出现在同一区域
    span = len(days_list)
    for ds, _ in days_list:
        if ds in content and ("连续{}晚".format(span) in content):
            return True
    return False


def main():
    args = sys.argv[1:]
    days = 14
    if "--days" in args:
        days = int(args[args.index("--days") + 1])

    data = read_sleep_days(days)
    if not data:
        print("[shadow_sleep_gate] ⚠️ 未读到任何 sleep_duration 数据（日记目录：{}）".format(DIARY_DIR))
        return 0

    streak, streak_days = compute_streak(data)
    recent = data[-days:]

    gate_hit = streak >= GATE_THRESHOLD
    hard = [(d, v) for d, v in data if v < HARD_FLOOR]
    written = already_written(streak_days) if gate_hit else False

    if args and "--json" in args:
        print(json.dumps({
            "streak_below_6h": streak,
            "streak_days": streak_days,
            "gate_threshold": GATE_THRESHOLD,
            "gate_hit": gate_hit,
            "already_written": written,
            "hard_floor_events": hard,
            "last_day": data[-1],
        }, ensure_ascii=False, indent=2))
        return 3 if (gate_hit and not written) else 0

    print("=" * 62)
    print("[shadow_sleep_gate] 机械睡眠闸状态   扫描窗口 {} 天 · 样本 {} 天".format(days, len(data)))
    print("=" * 62)
    print("  数据截止日：{}（最新样本 {}h）".format(data[-1][0], data[-1][1]))
    print("  连续<6h：{} 晚   闸阈值：≥{} 晚".format(streak, GATE_THRESHOLD))
    if streak_days:
        print("  连续段明细：" + " · ".join("{}({}h)".format(d[5:], v) for d, v in streak_days))
    print("  单晚<4h（严重）：{}".format(
        ", ".join("{}({}h)".format(d[5:], v) for d, v in hard[-5:]) if hard else "无"))

    print()
    if gate_hit and not written:
        print("  🔴 闸已达标但 SHADOW 未见对应条目 → 需补写")
        print("     跑 --emit-draft 出草稿，用 shadow_append.py 写入")
        if "--emit-draft" in args:
            print()
            print("  ─── 建议草稿（⛔归因字段须由 AI/你判断补全，勿直接套用）───")
            avg = sum(v for _, v in streak_days) / len(streak_days)
            print("  --date {} --icon 🔴 --title \"机械睡眠闸应触发未触发·连续{}晚<6h（回填）\"".format(
                streak_days[-1][0], len(streak_days)))
            print("  --type 作息违背 --quadrant 未知已知")
            print("  --fact \"{}-{} 连续{}晚睡眠<6h（{}）·均值{}h\"".format(
                streak_days[0][0], streak_days[-1][0], len(streak_days),
                "/".join(["{}h{:02d}m".format(int(v), round((v % 1) * 60)) for _, v in streak_days]),
                round(avg, 2)))
        return 3
    elif gate_hit and written:
        print("  ✅ 闸已达标且已写入（无需动作）")
        return 0
    else:
        print("  ✅ 未达闸阈值，无需写入")
        return 0


if __name__ == "__main__":
    sys.exit(main())