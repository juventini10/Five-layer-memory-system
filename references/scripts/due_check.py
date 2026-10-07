#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
due_check.py — 数字分身「到期检查」汇总器（2026-09-21 立·皮叔批准）

问题：日历闸散落四处（岗位台账 / 漂移体检 state / launchd plist / 进度看板文档），
     "什么时候到期"每次都得人去翻 → 依赖人记得（违背愿景①全自动化）。
本脚本：读四源 → 一句话输出「今日到期 / 近 N 天到期」。只读，不改任何文件。

四源（权威度降序·铁律-016「查实盘不查看板」）：
  1. 岗位台账  数字分身/job_probation_ledger.json      —— probation_end（试用期/灰度期满）
  2. 漂移体检  数字分身/scripts/drift_check_state.json —— last_check + 30 天
  3. launchd   ~/Library/LaunchAgents/com.buluotuo.*.plist —— StartCalendarInterval（日历型·月/年）
                 仅 Hour/Minute 的每日型跳过（日常巡检非"到期"语义）
  4. 进度看板  数字分身设计哲学/03-进度看板.md —— 「日历闸」行 + 「触发条件」表
                 ⛔ 文档源·二手·必须显式标注，且只取未来项（含"已结案"标记的行跳过）

设计约束：
  - 源不可达 → 显式打印「源不可达」（⛔不静默降级·对齐 verify_checklist_gate 先例）
  - 退出码：默认恒 0（查询器非门禁）；--strict 时「今日有到期」→ exit 1
用法：
  python3 due_check.py            # 摘要 + 明细
  python3 due_check.py --brief    # 只输出一行摘要（供会话/AI 快速读）
  python3 due_check.py --days 14  # 自定义近 N 天窗口（默认 7）
  python3 due_check.py --strict   # 今日有到期则 exit 1
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import json
import os
import re
import sys
from datetime import date, timedelta

HOME = os.path.expanduser("~")
# 数字分身中心路径：可用环境变量覆盖（对齐 doenglingz_drift_check_remind.py 的 DIGITALTWIN_HOME 先例·
# 便于脱敏入包／换机；⛔不发明第二个变量名，同一体系同一变量）
DT = os.path.expanduser(
    os.environ.get("DIGITALTWIN_HOME") or os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身")
)
LEDGER = os.path.join(DT, "job_probation_ledger.json")
DRIFT_STATE = os.path.join(DT, "scripts", "drift_check_state.json")
LAUNCH_AGENTS = os.path.join(HOME, "Library", "LaunchAgents")
DASHBOARD = os.path.join(
    HOME, "~/个人AI档案", "记忆蓝图", "04_系统文件设计", "数字分身设计哲学", "03-进度看板.md"
)
DRIFT_INTERVAL_DAYS = 30
OVERDUE_LOOKBACK_DAYS = 30  # 逾期项只报近 30 天，避免历史刷屏


def _d(y, m, d):
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _next_calendar(today, day, month):
    """由 launchd StartCalendarInterval 的 Day/Month 推算下次触发日。"""
    day = day or 1
    if month:  # 年度型
        for y in (today.year, today.year + 1):
            x = _d(y, month, day)
            if x and x >= today:
                return x
        return None
    y, m = today.year, today.month  # 月度型：只给 Day
    for _ in range(14):
        x = _d(y, m, day)
        if x and x >= today:
            return x
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return None


def from_ledger(errors):
    items = []
    if not os.path.exists(LEDGER):
        errors.append("岗位台账不可达: %s" % LEDGER)
        return items
    try:
        data = json.load(open(LEDGER, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append("岗位台账解析失败: %s" % e)
        return items
    for jid, job in (data.get("jobs") or {}).items():
        if job.get("monitor_mode") == "post_probation":
            continue  # 已转正持续监控岗，无试用期满日
        end = job.get("probation_end")
        if not end:
            continue
        try:
            dt = date.fromisoformat(end)
        except ValueError:
            continue
        items.append({
            "date": dt,
            "name": "%s %s 试用期止" % (jid, job.get("job_name", "")),
            "src": "岗位台账",
            "note": "status=%s" % job.get("status", "?"),
        })
    return items


def from_drift(errors):
    items = []
    if not os.path.exists(DRIFT_STATE):
        errors.append("漂移体检 state 不可达（未初始化？）: %s" % DRIFT_STATE)
        return items
    try:
        data = json.load(open(DRIFT_STATE, encoding="utf-8"))
        last = date.fromisoformat(data["last_check"])
    except Exception as e:  # noqa: BLE001
        errors.append("漂移体检 state 解析失败: %s" % e)
        return items
    items.append({
        "date": last + timedelta(days=DRIFT_INTERVAL_DAYS),
        "name": "人格漂移体检（%d 天周期）" % DRIFT_INTERVAL_DAYS,
        "src": "漂移state",
        "note": "上次 %s" % last.isoformat(),
    })
    return items


def from_launchd(errors):
    items = []
    if not os.path.isdir(LAUNCH_AGENTS):
        errors.append("LaunchAgents 目录不可达: %s" % LAUNCH_AGENTS)
        return items
    files = sorted(glob.glob(os.path.join(LAUNCH_AGENTS, "com.buluotuo.*.plist")))
    if not files:
        errors.append("未发现 com.buluotuo.*.plist（launchd 源为空）")
    today = date.today()
    for p in files:
        base = os.path.basename(p)
        if ".bak" in base or base.endswith(".disabled") or not base.endswith(".plist"):
            continue
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:  # noqa: BLE001
            continue
        m = re.search(r"<key>StartCalendarInterval</key>\s*<dict>(.*?)</dict>", t, re.S)
        if not m:
            continue  # 非日历型（StartInterval 等）→ 跳过
        blk = m.group(1)

        def num(key):
            mm = re.search(r"<key>%s</key>\s*<integer>(\d+)</integer>" % key, blk)
            return int(mm.group(1)) if mm else None

        day, month = num("Day"), num("Month")
        if day is None and month is None:
            continue  # 每日型（仅 Hour/Minute）→ 日常非"到期"
        nxt = _next_calendar(today, day, month)
        if nxt is None:
            continue
        items.append({
            "date": nxt,
            "name": base[:-6].replace("com.buluotuo.", ""),
            "src": "launchd",
            "note": "下次 %s" % nxt.isoformat(),
        })
    return items


def from_dashboard(errors, today):
    """看板源：⛔文档源·二手。只取未来项；标「已结案/已完成」的行跳过。"""
    items = []
    if not os.path.exists(DASHBOARD):
        errors.append("进度看板不可达: %s" % DASHBOARD)
        return items
    txt = open(DASHBOARD, encoding="utf-8").read()
    for line in txt.split("\n"):
        # ① 「日历闸」行：形如 灰度期满 **09-20**、岗位3 期满 **09-26**
        if "日历闸" in line:
            for mm in re.finditer(r"\*\*(\d{2})-(\d{2})\*\*", line):
                m2, d2 = int(mm.group(1)), int(mm.group(2))
                seg = re.split(r"[、，,]", line[:mm.start()])
                name = re.sub(r"[\|\*\s]+", "", seg[-1])[-16:] or "日历闸项"
                d = _d(today.year, m2, d2)
                if d and d < today - timedelta(days=180):
                    d = _d(today.year + 1, m2, d2)
                if d and d >= today:
                    items.append({"date": d, "name": name, "src": "看板(文档源)", "note": "日历闸行"})
        # ② 「触发条件」表：只取未来项
        if not line.startswith("|") or "2026-" not in line:
            continue
        if any(k in line for k in ("已结案", "已完成", "✅ 已")):
            continue
        m = re.search(r"20\d{2}-(\d{2})-(\d{2})", line)
        if not m:
            continue
        d = _d(today.year, int(m.group(1)), int(m.group(2)))
        if d is None or d < today:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        name = (cells[0] if cells else "触发条件")[:20]
        items.append({"date": d, "name": name, "src": "看板(文档源)", "note": "触发条件表"})
    return items


def collect(window_days=7, today=None):
    """四源汇总 + 跨源去重 + 窗口分组。

    ⛔ 本函数是「到期判定」的唯一实现——due_check_remind.py 必须 import 它，
    ⛔DO NOT 另写一套解析（复制=第二本账=判据漂移，正是 2026-09-21 根治的那个病）。
    返回 (today_items, soon_items, later_items, overdue, errors, today)
    """
    today = today or date.today()
    errors = []
    items = []
    items += from_ledger(errors)
    items += from_drift(errors)
    items += from_launchd(errors)
    items += from_dashboard(errors, today)

    # 去重（同日 + 名称前 6 字近似 → 视为同一事；优先保留实盘源，双源并标）
    SRC_LIVE = {"launchd", "岗位台账", "漂移state"}
    best = {}
    for it in sorted(items, key=lambda x: (x["date"], x["name"])):
        k = (it["date"], it["name"][:6])
        cur = best.get(k)
        if cur is None:
            best[k] = it
            continue
        keep, drop = (it, cur) if (it["src"] in SRC_LIVE and cur["src"] not in SRC_LIVE) else (cur, it)
        if drop["src"] != keep["src"] and "｜" not in keep["src"]:
            keep["src"] = keep["src"] + "｜" + drop["src"]
        best[k] = keep
    uniq = [best[k] for k in sorted(best, key=lambda x: (x[0], x[1]))]

    end = today + timedelta(days=window_days)
    today_items = [i for i in uniq if i["date"] == today]
    soon_items = [i for i in uniq if today < i["date"] <= end]
    later_items = [i for i in uniq if end < i["date"] <= today + timedelta(days=30)]
    overdue = [
        i for i in uniq
        if today - timedelta(days=OVERDUE_LOOKBACK_DAYS) <= i["date"] < today
    ]
    return today_items, soon_items, later_items, overdue, errors, today


def main():
    args = sys.argv[1:]
    window = 7
    if "--days" in args:
        try:
            window = int(args[args.index("--days") + 1])
        except (IndexError, ValueError):
            print("⚠️ --days 需跟整数，已回落默认 7")
    brief = "--brief" in args
    strict = "--strict" in args

    today_items, soon_items, later_items, overdue, errors, today = collect(window)

    def fmt(i):
        return "  · %s  %s   [%s]" % (
            i["date"].strftime("%m-%d"), i["name"][:30], i["src"]
        )

    head = "📅 到期检查（%s·窗口 %d 天）  今日 %d 项 · 近 %d 天 %d 项" % (
        today.isoformat(), window, len(today_items), window, len(soon_items)
    )
    if brief:
        tail = " · ".join(
            "%s %s[%s]" % (i["date"].strftime("%m-%d"), i["name"][:18], i["src"])
            for i in (today_items + soon_items)
        ) or "无"
        print(head + " —— " + tail)
        if errors:
            print("⚠️ " + "；".join(errors))
        return 1 if (strict and today_items) else 0

    print(head)
    print()
    print("今日到期：%s" % ("无" if not today_items else ""))
    for i in today_items:
        print(fmt(i))
    print("近 %d 天：%s" % (window, "无" if not soon_items else ""))
    for i in soon_items:
        print(fmt(i))
    if later_items:
        print("再往后（%d-30 天）：%s 项" % (window + 1, len(later_items)))
        for i in later_items:
            print(fmt(i))
    if overdue:
        print("⚠️ 已逾期未结（近 %d 天）：%d 项" % (OVERDUE_LOOKBACK_DAYS, len(overdue)))
        for i in overdue:
            print(fmt(i))
    if errors:
        print()
        print("⚠️ 源不可达（⛔不静默·按源降级不报错）：")
        for e in errors:
            print("  - %s" % e)
    else:
        print()
        print("源状态：4/4 可达（岗位台账 / 漂移state / launchd / 看板）")
    return 1 if (strict and today_items) else 0


if __name__ == "__main__":
    sys.exit(main())
