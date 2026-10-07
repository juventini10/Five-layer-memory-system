#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
due_check_remind.py — 到期检查·提醒器 v1.0（2026-09-21 立·你"照 drift_check_remind.py 的路子"）

职责（单一·机械触发层）：调 due_check.collect() 取四源到期项，
  「今日到期 / 近 N 天（默认 2）/ 逾期未结」任一非空，或源不可达 → 写提醒日志；否则清空（静默）。
  ⛔ 本脚本不做「到期该干什么」的语义执行——那是会话代理的事。
  （分工红线：判定归脚本、语义执行归 LLM · 同 doenglingz_drift_check_remind.py 先例）

⛔ 判据单一实现：四源解析一律 import 同目录 due_check —— ⛔DO NOT 在本文件另写一套解析。
  复制=第二本账=判据漂移，正是 2026-09-21 刚根治的那个病。

设计对齐（照 drift 提醒器的四条纪律）：
  · 单一职责：只判定+写 log，不执行
  · 输出：{DT}/scripts/due_check_remind.log —— 到期=非空提醒；未到期=空文件（静默）
  · 退出码：恒 0（提醒器不阻塞系统）
  · 源不可达：保守原则——视为「可能到期」写提醒（不知道 ≠ 没有；对齐 drift「state 缺失=视为超期」）

与 drift 提醒器的**关键差异**（有意为之）：drift 是 30 天周期、提醒后由执行代理刷新 state；
  本提醒器是**滚动窗口**，无法靠 state 去重（窗口内每天都命中）。故把窗口收窄到 2 天——
  每项最多响 3 次（T-2/T-1/T），既保住"提前知道"又不制造每日重复噪音。
  逾期未结项则持续响直到处理（欠账该响）。

路径：数字分身中心可用 DIGITALTWIN_HOME 覆盖（同 due_check.py / drift 提醒器·便于脱敏入包）
用法：
  python3 due_check_remind.py             # 默认窗口 2 天
  python3 due_check_remind.py --days 7    # 自定义提前量
  python3 due_check_remind.py --dry-run   # 只打印，不写 log
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import due_check as dc  # noqa: E402  （同目录·判定单一实现）

NEAR_DAYS = 2


def _fmt(items, with_date=True):
    if not items:
        return "无"
    parts = []
    for i in items:
        if with_date:
            parts.append("%s %s [%s]" % (i["date"].strftime("%m-%d"), i["name"], i["src"]))
        else:
            parts.append("%s [%s]" % (i["name"], i["src"]))
    return "；".join(parts)


def main():
    args = sys.argv[1:]
    days = NEAR_DAYS
    if "--days" in args:
        try:
            days = int(args[args.index("--days") + 1])
        except (IndexError, ValueError):
            print("⚠️ --days 需跟整数，回落默认 %d" % NEAR_DAYS)
    dry = "--dry-run" in args

    t_items, s_items, _later, overdue, errors, today = dc.collect(days)
    log_path = os.path.join(dc.DT, "scripts", "due_check_remind.log")

    triggered = bool(t_items or s_items or overdue or errors)
    lines = []
    if triggered:
        lines.append("🔔 到期提醒（%s · 提前量 %d 天）" % (today.isoformat(), days))
        lines.append("· 今日到期：%s" % _fmt(t_items, with_date=False))
        lines.append("· 近 %d 天：%s" % (days, _fmt(s_items)))
        lines.append("· 逾期未结（近 30 天）：%s" % _fmt(overdue))
        if errors:
            lines.append("· ⚠️ 源不可达（保守视为可能到期）：" + "；".join(errors))
        lines.append(
            "执行：到期项该做什么见 03-进度看板「触发条件」表；明细 python3 %s"
            % os.path.basename(os.path.abspath(dc.__file__))
        )
    content = "\n".join(lines) + ("\n" if lines else "")

    if dry:
        print("[dry-run] 触发=%s" % triggered)
        print(content if content else "(静默·log 将被清空)")
        return 0

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("[due-check-remind] %s" % (
            "到期提醒已写入: %s" % os.path.basename(log_path) if triggered
            else "未到期（提前量 %d 天），日志已清空" % days
        ))
    except Exception as e:  # noqa: BLE001
        # log 不可写（DT 目录缺失/无权限等）→ 退回 stdout，保证提醒不因落盘失败而静默丢失
        print("[due-check-remind] ⚠️ 写 log 失败: %s → 退回 stdout：" % e)
        print(content if content else "(静默·无到期且源全可达)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
