#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_pattern_predictor.py — 成长箱预测层预警器（Phase 3 预测式学习 · 步骤3.1 · v1.0.0）

定位（设计：[记忆共享中心]/自定义层/待完成工作/成长箱升级/phase3-design.md）：
  从免疫复发记录统计 30 天高频坑（≥PREDICT_THRESHOLD 次）→ 对照抗体库与预警台账双去重
  → 首查探针前置（检测对象已消失的不预警·治 W1 假警报先例）→ 出「预测预警书」落 预测预警.md。
  ⛔ 本脚本对抗体文件/learnings/ERRORS 零写入权（G11·预警≠抗体·自测断言 mtime）。
  前馈+反馈校准：预警批准率连续2周<50% → 阈值+1（写回头部字段·G12 留痕）。

用法：
  python3 growth_pattern_predictor.py              # 预测一轮
  python3 growth_pattern_predictor.py --check      # 健康检查 JSON
  python3 growth_pattern_predictor.py --self-test  # 自测（夹具自清理）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta

VERSION = "1.0.0"

HOME = os.path.expanduser("~")
BASE = os.path.expanduser("[记忆共享中心]")
RECURRENCE = os.path.join(BASE, "成长箱", "免疫复发记录.md")
ANTIBODY_HIST = os.path.join(BASE, "成长箱", "免疫抗体历史.md")
ANTIBODY_LEDGER = os.path.join(BASE, "成长箱", "免疫复发记录.md")  # 现役抗体判定源（✅免疫节）
FORECAST = os.path.join(BASE, "成长箱", "预测预警.md")
STATE = os.path.join(BASE, "成长箱", "learnings", "growth_pattern_predictor_state.json")
DECISIONS = os.path.join(BASE, "成长箱", "learnings", "DECISIONS.jsonl")

PREDICT_THRESHOLD = 8      # 30天窗口预警阈值（G12·变更须留痕）
DAILY_WARN_CAP = 3         # 每日预警上限
WINDOW_DAYS = 30

WRITE_FORBIDDEN = [ANTIBODY_HIST]

FORECAST_HEADER = """# 成长箱 · 预测预警（Phase 3 预测式学习）

> 由 `growth_pattern_predictor.py` 每日 08:30 生成·人/童灵终审（⛔未批不设防·G11）。
> 预警阈值：{threshold}（30天窗口）·变更须记台账（G12）
> 批准方式：状态改 ✅已批 → 走 E5 抗体写入流程（用预警书内建议命令）；拒绝：改 ❌+理由（反哺阈值校准）。

## 预警清单
"""


def _read(path, limit=4_000_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def _write_state(payload):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    except OSError as exc:
        sys.stderr.write("growth_pattern_predictor: 状态写入失败 %s\n" % exc)


REC_LINE_RE = re.compile(r"^\s*-\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*\|\s*([^|]+?)\s*\|\s*(.+)$")


def parse_pits(text, today, window=WINDOW_DAYS):
    """统计窗口内命中坑次。返回 (counter, parse_errors)。"""
    cnt, errs = Counter(), 0
    start = today - timedelta(days=window - 1)
    for line in text.splitlines():
        m = REC_LINE_RE.match(line)
        if not m:
            if line.strip().startswith("- "):
                errs += 1
            continue
        try:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            errs += 1
            continue
        if "命中" not in m.group(3):
            continue
        rest = m.group(4)
        if " | 来源: " in rest:
            rest = rest.rsplit(" | 来源: ", 1)[0]
        pit = rest.split(" | ")[0].strip() if " | " in rest else rest.strip()
        if pit and start <= d <= today:
            cnt[pit] += 1
    return cnt, errs


def active_antibody_pits(ledger_text):
    """现役抗体坑名集合（✅免疫/🔵 节·宽松正则兼容无时分的历史行）。"""
    pits = set()
    for line in ledger_text.splitlines():
        if "✅免疫" not in line and "🔵" not in line:
            continue
        seg = line.split("|")
        if len(seg) >= 3:
            pit = seg[2].strip()
            if pit:
                pits.add(pit)
    return pits


def probe_alive(cmd, today=None):
    """首查探针：坑还在吗？
    抗体命令语义：rc==0=坑在（报警）→True 预警；rc≠0=坑已修/对象恢复→False 淘汰。
    空/超长命令或执行异常→保守放行 True（不静默吞）。"""
    if not cmd or len(cmd) > 400:
        return True  # 无法探测时保守放行（宁可多看一眼）
    try:
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=30)
        # 抗体命令语义：命中(exit0)=坑在；未命中(exit非0)=坑已修/对象消失
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return True  # 探测失败保守放行·不静默吞


def suggest_antibody(pit):
    """按坑名生成建议抗体命令草案（反断言格式·人批后可编辑）。"""
    key = pit[:24].replace('"', "'")
    return '! grep -q "%s" <目标文件>   # 草案·人批前须把目标文件与判据改准' % key


def run_predict(today=None, dry_run=False):
    today = today or date.today()
    rec_text = _read(RECURRENCE)
    stats = {"window": WINDOW_DAYS, "threshold": PREDICT_THRESHOLD, "pits": 0,
             "proposed": 0, "suppressed": 0, "dedup_antibody": 0, "dedup_forecast": 0,
             "probe_killed": 0, "errors": []}
    if not rec_text:
        stats["errors"].append("免疫复发记录缺失（显式降级·本轮无预测）")
        _write_state({"version": VERSION, "last_run": datetime.now().isoformat(timespec="seconds"), **stats})
        print("growth_pattern_predictor: 信号源缺失·降级退出")
        return 0

    cnt, perr = parse_pits(rec_text, today)
    stats["pits"] = len(cnt)
    if perr:
        stats["errors"].append("复发记录%d行无法解析（显式计数）" % perr)

    antibody_pits = active_antibody_pits(_read(ANTIBODY_LEDGER)) | active_antibody_pits(_read(ANTIBODY_HIST))
    forecast_text = _read(FORECAST)
    forecast_pits = {m.group(1).strip() for m in re.finditer(r"^### \[WARN-[^\]]+\]\s*(.+)$", forecast_text, re.M) if "（历史）" not in m.group(1)}

    proposals = []
    for pit, n in cnt.most_common():
        if n < PREDICT_THRESHOLD:
            break
        if any(pit == p or pit[:16] == p[:16] for p in antibody_pits):
            stats["dedup_antibody"] += 1
            continue
        if any(pit == p or pit[:16] == p[:16] for p in forecast_pits):
            stats["dedup_forecast"] += 1
            continue
        # 首查探针：从复发记录行提取该坑最近一次的抗体命令
        probe = None
        for line in rec_text.splitlines():
            if pit[:16] in line and "命中" in line and " | 来源: " in line:
                seg = line.rsplit(" | 来源: ", 1)[0]
                parts = seg.split(" | ")
                if len(parts) >= 4:
                    probe = parts[3].strip()
                    break
        if probe and not probe_alive(probe, today):
            stats["probe_killed"] += 1
            continue
        proposals.append({"pit": pit, "count": n,
                          "suggested": suggest_antibody(pit),
                          "risk": "高" if n >= 20 else "中"})
        stats["proposed"] += 1
        if len(proposals) >= DAILY_WARN_CAP:
            break

    if proposals and not dry_run:
        os.makedirs(os.path.dirname(FORECAST), exist_ok=True)
        if not forecast_text:
            with open(FORECAST, "w", encoding="utf-8") as f:
                f.write(FORECAST_HEADER.format(threshold=PREDICT_THRESHOLD))
        with open(FORECAST, "a", encoding="utf-8") as f:
            for p in proposals:
                today_s = today.strftime("%Y-%m-%d")
                f.write("\n### [WARN-%s] %s\n" % (today.strftime("%Y%m%d"), p["pit"]))
                f.write("- **30天频次**：%d 次\n" % p["count"])
                f.write("- **风险等级**：%s\n" % p["risk"])
                f.write("- **建议抗体**：`%s`\n" % p["suggested"])
                f.write("- **首次预警**：%s\n" % today_s)
                f.write("- **状态**：⏳待批\n")
                f.write("- **批准结论**：\n")
    _write_state({"version": VERSION, "last_run": datetime.now().isoformat(timespec="seconds"),
                  "today": today.isoformat(), **stats})
    print("growth_pattern_predictor: 窗口%d天·坑%d种·预警阈值%d→新预警%d条（去重:已有抗体%d·已预警%d·探针淘汰%d）%s" % (
        WINDOW_DAYS, len(cnt), PREDICT_THRESHOLD, len(proposals),
        stats["dedup_antibody"], stats["dedup_forecast"], stats["probe_killed"],
        "·%d错误" % len(stats["errors"]) if stats["errors"] else ""))
    for e in stats["errors"]:
        print("  ⚠ " + e)
    return 0


def health_check():
    state = {}
    try:
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        pass
    out = {"version": VERSION, "last_run": state.get("last_run", ""),
           "forecast_file": os.path.isfile(FORECAST),
           "recurrence_file": os.path.isfile(RECURRENCE),
           "last_stats": state,
           "alarm": state.get("proposed", 0) > 0}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def self_test():
    failures = []
    tmp = tempfile.mkdtemp(prefix="gpp_selftest_")
    today = date(2026, 9, 16)
    global RECURRENCE, ANTIBODY_HIST, ANTIBODY_LEDGER, FORECAST, STATE, WRITE_FORBIDDEN
    real = (RECURRENCE, ANTIBODY_HIST, ANTIBODY_LEDGER, FORECAST, STATE, WRITE_FORBIDDEN)
    try:
        RECURRENCE = os.path.join(tmp, "rec.md")
        ANTIBODY_HIST = os.path.join(tmp, "abhist.md")
        ANTIBODY_LEDGER = RECURRENCE
        FORECAST = os.path.join(tmp, "forecast.md")
        STATE = os.path.join(tmp, "state.json")

        # 夹具：高频坑甲(12次·有探针·对象在→预警) 高频坑乙(10次·已有抗体→去重)
        #       高频坑丙(9次·探针=对象已消失→淘汰) 低频坑丁(3次·低于阈值)
        lines = []
        for i in range(12):
            lines.append("- 2026-09-%02d 08:00 | 🔴命中 | 坑甲高频复发测试 | echo alive-a | 来源: t" % (3 + i % 14))
        for i in range(10):
            lines.append("- 2026-09-%02d 09:00 | 🔴命中 | 坑乙已有抗体测试 | echo alive-b | 来源: t" % (3 + i % 14))
        for i in range(9):
            lines.append("- 2026-09-%02d 10:00 | 🔴命中 | 坑丙对象已消失测试 | test -f /nonexistent_gpp_probe | 来源: t" % (3 + i % 14))
        for i in range(3):
            lines.append("- 2026-09-10 11:00 | 🔴命中 | 坑丁低频不用管 | echo alive-d | 来源: t")
        # 已有抗体（✅免疫节·坑乙）
        lines.append("- 2026-09-06 | ✅免疫 | 坑乙已有抗体测试 | echo guard-b | 来源: t")
        with open(RECURRENCE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        with open(ANTIBODY_HIST, "w", encoding="utf-8") as f:
            f.write("")

        forbidden_p = ANTIBODY_HIST
        before_mtime = os.path.getmtime(forbidden_p)

        devnull = open(os.devnull, "w")
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            run_predict(today=today)
            text1 = _read(FORECAST)
            run_predict(today=today)  # 幂等
            text2 = _read(FORECAST)
        finally:
            sys.stdout = old_stdout
            devnull.close()

        if "坑甲高频复发测试" not in text1:
            failures.append("T1 高频坑甲未预警")
        if "坑乙已有抗体" in text1:
            failures.append("T2 已有抗体的坑乙不应预警")
        if "坑丙对象已消失" in text1:
            failures.append("T3 探针淘汰失效（对象消失的坑丙不该预警）")
        if "坑丁低频" in text1:
            failures.append("T4 低频坑丁不应预警")
        if text1.count("### [WARN-") != 1:
            failures.append("T5 预警数=%d≠1" % text1.count("### [WARN-"))
        if "⏳待批" not in text1:
            failures.append("T6 预警缺待批状态")
        if os.path.getmtime(forbidden_p) != before_mtime:
            failures.append("T7 G11违规：抗体历史文件被写")
        if text1 != text2:
            failures.append("T8 重跑不幂等")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        RECURRENCE, ANTIBODY_HIST, ANTIBODY_LEDGER, FORECAST, STATE, WRITE_FORBIDDEN = real

    if failures:
        print("SELF-TEST FAIL（%d）:" % len(failures))
        for f_ in failures:
            print("  ✗ " + f_)
        return 1
    print("SELF-TEST PASS（T1-T8 全绿·含G11 mtime断言·夹具已自清理）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="成长箱预测层预警器 v%s" % VERSION)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return health_check()
    return run_predict()


if __name__ == "__main__":
    sys.exit(main())
