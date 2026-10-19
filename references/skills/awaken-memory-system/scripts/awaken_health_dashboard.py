#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""awaken-memory-system 8.0 D 方向 — 记忆健康仪表盘（patrol.md §5·D-1 数据源收敛 + D-2 趋势行动建议）

输入：无参数（默认趋势窗口 2 周）；--weeks N 覆盖趋势窗口；--summary 输出单行摘要（巡检弹窗用）
数据源（全部只读·⛔不越界写入）：快照「最近变更摘要」最新日期 / 自画像目录最新月份 /
     蒸馏中心三级状态（import 复用 awaken_distill_due_check·单一真源） / 巡检日志趋势
输出：📊 记忆健康仪表盘文本——D-3 三处入口（巡检弹窗摘要/小美详情/全量报告）同源输出
退出码：0=成功（含数据缺失降级标注）；1=关键文件缺失（快照/自画像目录）
设计约束：⛔只读不写（跨 Skill 边界·patrol.md §5）；⛔不硬编码蒸馏类型（import 复用·patrol.md §2）；
         标准库 only（无第三方依赖）；调用方须 env -u PYTHONHOME -u PYTHONPATH 前缀（环境污染防护·2026-08-19 第二刀）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
SCRIPT_DIR = Path(__file__).resolve().parent
SNAPSHOT = HOME / "[记忆共享中心]" / "情境层" / "动态状态快照.md"
PORTRAIT_DIR = HOME / "[记忆共享中心]" / "最伟大的我" / "自画像"
PATROL_LOG = HOME / "buluotuo_bin" / "log" / "awaken_patrol.log"
TODAY = datetime.date.today()

LEVEL_ORDER = ["🔴严重逾期", "🟡已逾期", "🔵即将到期"]


def snapshot_status():
    """快照「最近变更摘要」表格最新日期 → (日期, 滞后天数)。
    日期双格式（2026-09-20 回灌群友 Windows 端实测）：
      · MM-DD 无年份（包内 update_snapshot 写入格式·按当前年补全·跨年回退）
      · YYYY-MM-DD 带年份（跨端变体·直接解析不补年）"""
    try:
        lines = SNAPSHOT.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None, "快照读取失败"
    in_table = False
    for line in lines:
        s = line.strip()
        # 层级解析（B1 根治·2026-10-10 刚叔提请单 F1）：原判据写死 `###`，而本包 step5
        # 合成用的模板 `references/templates/情境层-动态状态快照.md` 产的是 `## 📝 最近变更摘要`
        # ——包自己的合成链保证每个新装用户该维恒失明（"数据来源形状↔解析器断言形状"无配对校验）。
        # 判据改按标题层级族匹配并以标题文本定位，⛔不认某一级。
        if re.match(r"^#{2,6}\s", s) and "最近变更摘要" in s:
            in_table = True
            continue
        if in_table and re.match(r"^#{1,6}\s", s):
            break  # 进入下一章节：表格已结束，⛔越界把后文表格当本段数据
        if not in_table or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or cells[0] == "日期":
            continue
        # 带年份格式优先（YYYY-MM-DD）
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", cells[0])
        if m:
            try:
                d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                return None, "快照表格日期非法"
            return d, (TODAY - d).days
        # 无年份格式（MM-DD·官方写入口径）
        m = re.match(r"^(\d{2})-(\d{2})$", cells[0])
        if not m:
            continue
        try:
            d = datetime.date(TODAY.year, int(m.group(1)), int(m.group(2)))
            if d > TODAY:
                d = datetime.date(TODAY.year - 1, int(m.group(1)), int(m.group(2)))
            return d, (TODAY - d).days
        except ValueError:
            return None, "快照表格日期非法"
    return None, "快照表格无数据行"


def portrait_status():
    """自画像目录最新月份 → (年月, 滞后月数)。frontmatter month 优先·文件名兜底·_模板.md 排除。"""
    if not PORTRAIT_DIR.is_dir():
        return None, "自画像目录缺失"
    best = None
    for p in PORTRAIT_DIR.glob("*.md"):
        if p.name == "_模板.md":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")[:400]
        m = re.search(r"^month:\s*(\d{4})-(\d{2})\s*$", text, re.M)
        if m:
            cur = (int(m.group(1)), int(m.group(2)))
        else:
            m2 = re.search(r"(\d{4})-(\d{2})", p.name)
            if not m2:
                continue
            cur = (int(m2.group(1)), int(m2.group(2)))
        if best is None or cur > best:
            best = cur
    if best is None:
        return None, "自画像无月份文件"
    ym = datetime.date(best[0], best[1], 1)
    months_lag = (TODAY.year - ym.year) * 12 + (TODAY.month - ym.month)
    return ym, months_lag


def distill_status():
    """蒸馏三级状态 → (计数 dict, 明细列表)。import 复用 awaken_distill_due_check 解析（patrol.md §2 单一真源）。
    DISTILL_CENTER_PATH 环境变量可覆盖中心路径（与 patrol.sh 传递口径对齐）。"""
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import awaken_distill_due_check as ddc
    except ImportError:
        return None, None
    center = Path(os.environ.get("DISTILL_CENTER_PATH") or ddc.DEFAULT_CENTER)
    rows = ddc.parse_center(center)
    if rows is None:
        return None, None
    counts = {level: 0 for level in LEVEL_ORDER}
    details = []
    for typ, (_month, nxt) in ddc.latest_expected(rows).items():
        level, detail = ddc.classify(nxt)
        if level:
            counts[level] += 1
            details.append(f"{level}|{typ}|{nxt.isoformat()}|{detail}")
    details.sort(key=lambda x: LEVEL_ORDER.index(x.split("|", 1)[0]))
    return counts, details


def patrol_trend(weeks):
    """巡检日志近 N 周趋势 → dict。行格式：[完成]/[快照]/[蒸馏]/[触达] 四段留痕（patrol.md §3.1）。"""
    try:
        lines = PATROL_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    window_start = TODAY - datetime.timedelta(days=7 * weeks)
    entries = []
    for line in lines:
        m = re.match(r"^(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} \[(\w+)\] (.*)$", line)
        if not m:
            continue
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if d < window_start:
            continue
        entries.append((d, m.group(2), m.group(3)))
    runs = sum(1 for _, t, _ in entries if t == "完成")
    snap_gaps = sum(1 for _, t, txt in entries if t == "快照" and ("失败" in txt or "缺失" in txt))
    due_alerts = sum(1 for _, t, txt in entries if t == "蒸馏" and "DUE|" in txt and ("🔴" in txt or "🟡" in txt))
    notify_count = sum(1 for _, t, txt in entries if t == "触达" and "已弹通知" in txt)
    last_notify = next((txt for _, t, txt in reversed(entries) if t == "触达" and "已弹通知" in txt), None)
    half = max((TODAY - window_start).days // 2, 1)
    cutoff = window_start + datetime.timedelta(days=half)
    recent = sum(1 for d, t, txt in entries if t == "蒸馏" and d >= cutoff
                 and "DUE|" in txt and ("🔴" in txt or "🟡" in txt))
    earlier = sum(1 for d, t, txt in entries if t == "蒸馏" and d < cutoff
                  and "DUE|" in txt and ("🔴" in txt or "🟡" in txt))
    trend = "↑" if recent > earlier else ("↓" if recent < earlier else "→")
    if runs < 2:
        trend = "—"
    return {"runs": runs, "snap_gaps": snap_gaps, "due_alerts": due_alerts,
            "notify": notify_count, "trend": trend, "last_notify": last_notify,
            "window_days": 7 * weeks}


def snap_level(lag):
    if lag is None:
        return "?"
    if lag <= 1:
        return "🟢"
    if lag <= 3:
        return "🟡"
    return "🔴"


def portrait_level(months_lag):
    if months_lag is None:
        return "?"
    return "🟢" if months_lag <= 1 else "🔴"


def build_advice(snap_lag, portrait_lag, counts, trend):
    adv = []
    if counts is not None and (counts["🔴严重逾期"] + counts["🟡已逾期"]) > 0:
        trend_note = "（检出趋势上升·优先安排）" if trend == "↑" else ""
        adv.append(f"蒸馏逾期{trend_note} → 说对应触发词立即蒸馏（📊系统日志蒸馏→'系统月报'/📓日记月报→'月报'/🧠成长箱蒸馏→'成长箱蒸馏'）")
    if isinstance(snap_lag, int) and snap_lag > 1:  # v8.1.4：失败态snap_lag为文案串，str>int会TypeError
        adv.append(f"快照滞后 {snap_lag} 天 → 输入『我美吗』全量加载+行为刷新（写动作入口·自愈引擎修复）")
    if isinstance(portrait_lag, int) and portrait_lag >= 2:  # v8.1.4：同上
        adv.append(f"自画像滞后 {portrait_lag} 月 → 说'补跑自画像'一键补跑")
    if not adv:
        # v8.1.4b·R4-NP-4收口：所有数据源均不可用时不出"健康正常"（逐行已标降级，建议行不得反向造假绿）
        if isinstance(snap_lag, int) or isinstance(portrait_lag, int) or counts is not None:
            adv.append("记忆健康正常 · 无需紧急动作")
        else:
            adv.append("⚠️ 全部数据源不可用 · 无法判定健康（见各行降级标注）")
    return adv


def next_advice(counts):
    if counts is not None and (counts["🔴严重逾期"] + counts["🟡已逾期"]) > 0:
        return "处理蒸馏待办后建议跑一次『我美吗』全量（刷新行为层·闭环）"
    suggest = TODAY + datetime.timedelta(days=3)
    return f"下次『我美吗』全量建议 {suggest.isoformat()}（周期性深度体检）"


def render_dashboard(weeks):
    snap_date, snap_lag = snapshot_status()
    portrait_ym, portrait_lag = portrait_status()
    counts, details = distill_status()
    trend = patrol_trend(weeks)

    lines = []
    lines.append("📊 记忆健康仪表盘（v8.0 D-1·快照+自画像+蒸馏+巡检趋势一屏）")
    if snap_date is not None:  # v8.1.4审查F附案：失败态返回(None,文案串)，守卫键必须是数据位（串也 is not None→strftime崩）
        lines.append(f"├─ 快照：最新 {snap_date.strftime('%m-%d')} · 滞后 {snap_lag} 天 {snap_level(snap_lag)}")
    else:
        lines.append(f"├─ 快照：{snap_lag} {snap_level(None)}")
    if portrait_ym is not None:  # v8.1.4审查F附案：同上，守卫键改数据位
        lag_note = "（月报驱动·滞后1月正常）" if portrait_lag == 1 else ""
        lines.append(f"├─ 自画像：最新 {portrait_ym.strftime('%Y-%m')} · 滞后 {portrait_lag} 月 {portrait_level(portrait_lag)}{lag_note}")
    else:
        lines.append(f"├─ 自画像：{portrait_lag} {portrait_level(None)}")
    if counts is not None:
        lines.append(f"├─ 蒸馏：🔴 {counts['🔴严重逾期']} / 🟡 {counts['🟡已逾期']} / 🔵 {counts['🔵即将到期']}")
    else:
        lines.append("├─ 蒸馏：检测不可用（蒸馏中心读取失败）")
    if trend is not None:
        lines.append(f"└─ 巡检趋势（近 {trend['window_days']} 天·运行 {trend['runs']} 次）：")
        lines.append(f"   ├─ 快照缺口 {trend['snap_gaps']} 次 · 蒸馏逾期检出 {trend['due_alerts']} 次 · 告警弹窗 {trend['notify']} 次 · 趋势 {trend['trend']}")
        if trend["last_notify"]:
            lines.append(f"   └─ 最近告警：{trend['last_notify']}")
        else:
            lines.append("   └─ 最近告警：无（近窗口无弹窗）")
    else:
        lines.append("└─ 巡检趋势：日志不可用（巡检未运行或日志被清理）")
    lines.append("建议：")
    for adv in build_advice(snap_lag, portrait_lag, counts, trend if trend else None):
        lines.append(f"├─ {adv}")
    lines.append(f"└─ {next_advice(counts)}")
    return "\n".join(lines)


def render_summary(weeks):
    """单行摘要（巡检弹窗用·D-3 ①入口）——只输出核心状态，与完整仪表盘同源。"""
    snap_date, snap_lag = snapshot_status()
    portrait_ym, portrait_lag = portrait_status()
    counts, _details = distill_status()
    parts = []
    parts.append(f"快照{snap_level(snap_lag if isinstance(snap_lag, int) else None)}滞后{'N/A' if not isinstance(snap_lag, int) else snap_lag}天")
    parts.append(f"自画像{'N/A' if not isinstance(portrait_lag, int) else f'滞后{portrait_lag}月'}")
    if counts is not None:
        parts.append(f"蒸馏🔴{counts['🔴严重逾期']}🟡{counts['🟡已逾期']}")
    else:
        parts.append("蒸馏不可用")
    return "📊 记忆健康 | " + " · ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="awaken 记忆健康仪表盘")
    parser.add_argument("--weeks", type=int, default=2, help="趋势窗口周数（默认 2）")
    parser.add_argument("--summary", action="store_true", help="输出单行摘要（巡检弹窗用）")
    args = parser.parse_args()
    weeks = max(args.weeks, 1)
    try:
        if args.summary:
            print(render_summary(weeks))
        else:
            print(render_dashboard(weeks))
    except Exception as exc:
        print(f"⚠️ 仪表盘生成异常：{exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
