#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_cross_link.py — 成长箱跨域日报器（Phase 4 跨域闭环 · 步骤4.2 · v1.0.1）

定位（设计：[记忆共享中心]/自定义层/待完成工作/成长箱升级/phase4-design.md）：
  读三棒（采集/裁决/预测）状态快照 + 守卫域/评估域实时信号 → 追加一行跨域日报到
  成长箱/跨域日报.md——成长箱↔守卫体系↔评估体系联动的可观测载体（自主≠黑箱）。
  同日幂等（G15）；写域极小：只写日报+自身状态（G16·自测断言）。

用法：
  python3 growth_cross_link.py              # 生成今日日报（幂等）
  python3 growth_cross_link.py --check      # 健康检查 JSON
  python3 growth_cross_link.py --self-test  # 自测（夹具自清理）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import shutil
import sys
import tempfile
from datetime import date, datetime

VERSION = "1.0.1"

HOME = os.path.expanduser("~")
BASE = os.path.expanduser("[记忆共享中心]")
DAILY = os.path.join(BASE, "成长箱", "跨域日报.md")
STATE = os.path.join(BASE, "成长箱", "learnings", "growth_cross_link_state.json")
COLLECTOR_STATE = os.path.join(BASE, "成长箱", "learnings", "growth_signal_collector_state.json")
GATE_STATE = os.path.join(BASE, "成长箱", "learnings", "growth_decision_gate_state.json")
PREDICTOR_STATE = os.path.join(BASE, "成长箱", "learnings", "growth_pattern_predictor_state.json")
CANDIDATES = os.path.join(BASE, "成长箱", "learnings", "CANDIDATES.md")
FORECAST = os.path.join(BASE, "成长箱", "预测预警.md")

WRITE_FORBIDDEN = [CANDIDATES, FORECAST]

DAILY_HEADER = """# 成长箱 · 跨域日报（Phase 4 跨域闭环）

> 由 `growth_cross_link.py` 每日 08:45 生成·三棒联动实况一行一条（G15 同日幂等）。
> G17（v1.0.1）：上游三棒非当日产出 → 行内显形「上游未当日跑」，⛔不把滞后数据当今日实况读。
> 数据源：三棒状态快照 + CANDIDATES/预测预警 实时计数。异常态（缺失/超时）显式标注不静默。

"""


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _read(path, limit=200_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def build_row(today):
    """汇总三棒+队列状态→一行日报。返回 (row, anomalies)。"""
    anomalies = []
    col = _read_json(COLLECTOR_STATE)
    gate = _read_json(GATE_STATE)
    pred = _read_json(PREDICTOR_STATE)

    col_last = col.get("last_run", "—")
    gate_last = gate.get("last_run", "—")
    pred_last = pred.get("last_run", "—")
    if col_last == "—":
        anomalies.append("采集器状态缺失")
    if gate_last == "—":
        anomalies.append("裁决器状态缺失")
    if pred_last == "—":
        anomalies.append("预测器状态缺失")

    cand_text = _read(CANDIDATES)
    pending = cand_text.count("**状态**：⏳")
    warn_text = _read(FORECAST)
    warn_pending = warn_text.count("**状态**：⏳")

    s1 = (col.get("sources") or {}).get("S1", "—")
    s3 = (col.get("sources") or {}).get("S3", "—")

    # G17 上游当日新鲜度（2026-09-18 实测假绿根治：RunAtLoad 登录批次四棒同刻齐发，
    # 本棒 11:22:25 先于采集棒 11:24:07 → 09-18 行照抄了 09-17 18:49 的上游态却标"今日"）
    stale = [n for n, v in (("采集", col_last), ("裁决", gate_last), ("预测", pred_last))
             if v != "—" and not str(v).startswith(today.isoformat())]
    if stale:
        anomalies.append("上游未当日跑：%s（本行=其最后产出的滞后态·⛔不当今日实况读）" % "、".join(stale))

    row = "| %s | %s | %s | %s | ⏳候选%d · ⏳预警%d | S1:%s · S3:%s |%s" % (
        today.isoformat(),
        col_last[:16] if col_last != "—" else "—",
        gate_last[:16] if gate_last != "—" else "—",
        pred_last[:16] if pred_last != "—" else "—",
        pending, warn_pending, s1, s3,
        (" ⚠️" + "；".join(anomalies) if anomalies else ""),
    )
    return row, anomalies


def run(today=None, dry_run=False):
    today = today or date.today()
    row, anomalies = build_row(today)
    stats = {"anomalies": anomalies, "written": False}
    if not dry_run:
        os.makedirs(os.path.dirname(DAILY), exist_ok=True)
        text = _read(DAILY)
        if not text:
            with open(DAILY, "w", encoding="utf-8") as f:
                f.write(DAILY_HEADER)
        elif ("| %s |" % today.isoformat()) in text:
            print("growth_cross_link: 今日日报已存在（G15 幂等跳过）")
            _write_state(today, stats)
            return 0
        with open(DAILY, "a", encoding="utf-8") as f:
            f.write(row + "\n")
        stats["written"] = True
    print("growth_cross_link: 日报%s（⏳候选·预警见行内；异常%d项）" % (
        "已追加" if stats["written"] else "幂等跳过", len(anomalies)))
    for a in anomalies:
        print("  ⚠ " + a)
    if not dry_run:
        _write_state(today, stats)
    return 0


def _write_state(today, stats):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump({"version": VERSION, "last_run": datetime.now().isoformat(timespec="seconds"),
                       "today": today.isoformat(), **stats}, f, ensure_ascii=False, indent=1)
    except OSError as exc:
        sys.stderr.write("growth_cross_link: 状态写入失败 %s\n" % exc)


def health_check():
    state = _read_json(STATE)
    out = {"version": VERSION, "last_run": state.get("last_run", ""),
           "daily_file": os.path.isfile(DAILY),
           "last_anomalies": state.get("anomalies", []),
           "alarm": bool(state.get("anomalies"))}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def self_test():
    failures = []
    N_CASES = 7  # 与本文件 T1..T7 断言条数同源，⛔不得写死于成功语里
    tmp = tempfile.mkdtemp(prefix="gcl_selftest_")
    today = date(2026, 9, 16)
    global DAILY, STATE, COLLECTOR_STATE, GATE_STATE, PREDICTOR_STATE, CANDIDATES, FORECAST, WRITE_FORBIDDEN
    real = (DAILY, STATE, COLLECTOR_STATE, GATE_STATE, PREDICTOR_STATE, CANDIDATES, FORECAST, WRITE_FORBIDDEN)
    try:
        DAILY = os.path.join(tmp, "跨域日报.md")
        STATE = os.path.join(tmp, "state.json")
        COLLECTOR_STATE = os.path.join(tmp, "c.json")
        GATE_STATE = os.path.join(tmp, "g.json")
        PREDICTOR_STATE = os.path.join(tmp, "p.json")
        CANDIDATES = os.path.join(tmp, "CANDIDATES.md")
        FORECAST = os.path.join(tmp, "预警.md")

        with open(COLLECTOR_STATE, "w", encoding="utf-8") as f:
            f.write('{"last_run": "2026-09-16T08:00:00", "sources": {"S1": "ok strict_rc=0", "S3": "ok fresh24h=0"}}')
        with open(GATE_STATE, "w", encoding="utf-8") as f:
            f.write('{"last_run": "2026-09-16T08:15:00"}')
        with open(PREDICTOR_STATE, "w", encoding="utf-8") as f:
            f.write('{"last_run": "2026-09-16T08:30:00"}')
        with open(CANDIDATES, "w", encoding="utf-8") as f:
            f.write("**状态**：⏳待审\n**状态**：⏳待审\n**状态**：✅\n")
        with open(FORECAST, "w", encoding="utf-8") as f:
            f.write("**状态**：⏳待批\n")

        forbidden_before = {p: os.path.getmtime(p) for p in (CANDIDATES, FORECAST)}

        devnull = open(os.devnull, "w")
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            run(today=today)
            text1 = _read(DAILY)
            run(today=today)  # G15 幂等
            text2 = _read(DAILY)
        finally:
            sys.stdout = old_stdout
            devnull.close()

        if text1.count("| 2026-09-16 |") != 1:
            failures.append("T1 日报行数=%d≠1" % text1.count("| 2026-09-16 |"))
        if "⏳候选2" not in text1:
            failures.append("T2 候选计数错误")
        if "⏳预警1" not in text1:
            failures.append("T3 预警计数错误")
        if text1 != text2:
            failures.append("T4 G15幂等失效")
        for p, mt in forbidden_before.items():
            if os.path.getmtime(p) != mt:
                failures.append("T5 G16违规：%s 被写" % os.path.basename(p))
        # 异常态：三棒状态全缺→行尾显式标注
        os.remove(COLLECTOR_STATE); os.remove(GATE_STATE); os.remove(PREDICTOR_STATE)
        if os.path.isfile(DAILY):
            os.remove(DAILY)
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            run(today=today)
            text3 = _read(DAILY)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        row3 = [l for l in text3.splitlines() if l.startswith("| 2026-09-16 |")]
        if not row3 or "⚠️" not in row3[-1] or "采集器状态缺失" not in row3[-1]:
            failures.append("T6 异常态未在数据行显形")
        # T7 G17 负例：三棒齐全但全是昨日时间戳 → 必须显形"上游未当日跑"
        for p, v in ((COLLECTOR_STATE, "2026-09-15T08:00:00"),
                     (GATE_STATE, "2026-09-15T08:15:00"),
                     (PREDICTOR_STATE, "2026-09-15T08:30:00")):
            with open(p, "w", encoding="utf-8") as f:
                f.write('{"last_run": "%s", "sources": {"S1": "ok strict_rc=0", "S3": "ok fresh24h=0"}}' % v)
        if os.path.isfile(DAILY):
            os.remove(DAILY)
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            run(today=today)
            text4 = _read(DAILY)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        row4 = [l for l in text4.splitlines() if l.startswith("| 2026-09-16 |")]
        if not row4 or "上游未当日跑" not in row4[-1]:
            failures.append("T7 G17失效：滞后上游未在数据行显形（假绿）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        DAILY, STATE, COLLECTOR_STATE, GATE_STATE, PREDICTOR_STATE, CANDIDATES, FORECAST, WRITE_FORBIDDEN = real

    if failures:
        print("SELF-TEST FAIL（%d）:" % len(failures))
        for f_ in failures:
            print("  ✗ " + f_)
        return 1
    print("SELF-TEST PASS（%d 例全绿·含G15幂等/G16写域断言/G17上游新鲜度·夹具已自清理）" % N_CASES)
    return 0


def main():
    ap = argparse.ArgumentParser(description="成长箱跨域日报器 v%s" % VERSION)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return health_check()
    return run()


if __name__ == "__main__":
    sys.exit(main())
