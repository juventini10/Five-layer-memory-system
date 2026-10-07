#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_reconcile_report.py v0 — 8/22 两账对账·机械层（引擎·统计）

定位：路由家族 8/22 对账节点的「算」部分——所有数字脚本机械产出（填值权归脚本，
AI 只回显+做决策）。决策层（扩张/回滚判断）不在此脚本内，由 AI 消费报告后执行。

数据源（全部只读）：
  A 账 = route_audit 基线    [记忆共享中心]/脚本中心/logs/route_audit.jsonl
  B 账 = 注入命中状态        /tmp/route_state.json
  C 账 = 护栏事件            .guard/guard_events.jsonl
  D 账 = 文件系统事件        .snapshots/events.log（基线观测 f 来源）

纪律：
  - 填值权归脚本：统计值全部机械产出；数据源缺失/不可解析 → 报告标注"缺数据"，⛔不编造
  - 幂等：正式报告已存在 → exit 0 跳过（重跑安全）
  - 日期守卫：非 2026-08-22 运行 → exit 0 静默（crontab 年触发语义下的自守卫）
  - 只读契约：不写任何业务数据，只写报告文件

用法：
  python3 route_reconcile_report.py            # 正式（日期守卫+幂等）
  python3 route_reconcile_report.py --force    # 绕过守卫（测试用，输出到 --out）
  python3 route_reconcile_report.py --force --out /tmp/test_report.md
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, json
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]/脚本中心")
REPORT_DIR = os.path.join(BASE, ".reconcile")
REPORT_PATH = os.path.join(REPORT_DIR, "对账报告_2026-08-22.md")
TARGET_DATE = (2026, 8, 22)

SOURCES = {
    "A_route_audit": os.path.expanduser("[记忆共享中心]/脚本中心/logs/route_audit.jsonl"),
    "B_route_state": "/tmp/route_state.json",
    "C_guard_events": os.path.join(BASE, ".guard", "guard_events.jsonl"),
    "D_fswatch_events": os.path.join(BASE, ".snapshots", "events.log"),
    "E_patrol_heartbeat": os.path.join(BASE, ".patrol", "last_run.ts"),
    "E_patrol_log": os.path.join(BASE, ".patrol", "patrol.log"),
}


def load_jsonl(path):
    """容错读 JSONL：坏行跳过计数，返回 (rows, bad_lines)"""
    rows, bad = [], 0
    if not os.path.isfile(path):
        return rows, -1  # -1 = 文件缺失
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    return rows, bad


def stat_route_audit(rows):
    """A 账：potential_miss 统计 + reconciliation 对账记录"""
    s = {"total": len(rows), "potential_miss": 0, "reconciliation": 0,
         "recon_confirmed_true": 0, "recon_confirmed_false": 0, "by_src": {}}
    for r in rows:
        if r.get("action") == "reconciliation":
            s["reconciliation"] += 1
            if r.get("confirmed") is True:
                s["recon_confirmed_true"] += 1
            elif r.get("confirmed") is False:
                s["recon_confirmed_false"] += 1
            continue
        if r.get("potential_miss") is True:
            s["potential_miss"] += 1
        src = r.get("src", "unknown")
        s["by_src"][src] = s["by_src"].get(src, 0) + 1
    return s


def stat_route_state(rows):
    """B 账：注入命中分布"""
    s = {"total": len(rows), "hit": 0, "zero_hit": 0}
    for r in rows:
        matched = r.get("matched") or []
        if matched:
            s["hit"] += 1
        else:
            s["zero_hit"] += 1
    return s


def stat_guard_events(rows):
    """C 账：护栏命中/配置告警分布"""
    s = {"total": len(rows), "guard_hit": 0, "config_missing": 0, "by_rule": {}}
    for r in rows:
        action = r.get("action")
        if action == "guard_hit":
            s["guard_hit"] += 1
            rule = r.get("rule", "?")
            s["by_rule"][rule] = s["by_rule"].get(rule, 0) + 1
        elif action == "guard_config_missing":
            s["config_missing"] += 1
    return s


def stat_fswatch(rows):
    """D 账：文件系统事件（f=变化频率基线观测）"""
    s = {"total": len(rows), "changed": 0, "deleted": 0, "initial": 0}
    for r in rows:
        if "\tchanged\t" in r:
            s["changed"] += 1
        elif "\tdeleted\t" in r:
            s["deleted"] += 1
        elif "initial_snapshot" in r:
            s["initial"] += 1
    return s


def build_report():
    lines = []
    lines.append("# 8/22 两账对账报告（机械层·脚本产出）")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 生成者：route_reconcile_report.py（引擎·统计）")
    lines.append("> 填值权声明：本报告所有数字由脚本机械统计，AI 只回显；标注「缺数据」项=数据源未就绪，⛔不得由 AI 补值。")
    lines.append("")
    lines.append("## 一、四账数据")
    lines.append("")
    lines.append("| 账 | 数据源 | 状态 | 关键数字 |")
    lines.append("|:--|:--|:--|:--|")

    # A 账
    a_rows, a_bad = load_jsonl(SOURCES["A_route_audit"])
    if a_rows or a_bad >= 0:
        sa = stat_route_audit(a_rows)
        miss_note = f"（坏行 {a_bad}）" if a_bad > 0 else ""
        lines.append(f"| A·route_audit 基线 | {SOURCES['A_route_audit']} | {'✅' if a_rows else '⚠️缺数据'} | 总 {sa['total']} ｜ potential_miss {sa['potential_miss']} ｜ reconciliation {sa['reconciliation']}（真漏判 {sa['recon_confirmed_true']}/误报 {sa['recon_confirmed_false']}）{miss_note} |")
        src_line = " ｜ ".join(f"{k}={v}" for k, v in sorted(sa["by_src"].items()))
        lines.append(f"  - 分源：{src_line or '无'}")
    else:
        lines.append(f"| A·route_audit 基线 | 缺失 | ⚠️缺数据 | — |")

    # B 账
    b_rows, b_bad = load_jsonl(SOURCES["B_route_state"])
    if b_rows or b_bad >= 0:
        sb = stat_route_state(b_rows)
        lines.append(f"| B·注入命中状态 | {SOURCES['B_route_state']} | {'✅' if b_rows else '⚠️缺数据'} | 总 {sb['total']} ｜ 命中 {sb['hit']} ｜ 零命中 {sb['zero_hit']} |")
    else:
        lines.append(f"| B·注入命中状态 | 缺失 | ⚠️缺数据 | — |")

    # C 账
    c_rows, c_bad = load_jsonl(SOURCES["C_guard_events"])
    if c_rows or c_bad >= 0:
        sc = stat_guard_events(c_rows)
        rule_line = " ｜ ".join(f"{k}={v}" for k, v in sorted(sc["by_rule"].items()))
        lines.append(f"| C·护栏事件 | {SOURCES['C_guard_events']} | {'✅' if c_rows else '⚠️缺数据'} | 总 {sc['total']} ｜ guard_hit {sc['guard_hit']} ｜ 配置告警 {sc['config_missing']} ｜ 规则分布：{rule_line or '无'} |")
    else:
        lines.append(f"| C·护栏事件 | 缺失 | ⚠️缺数据 | — |")

    # D 账（TSV 文本，非 JSONL——单独读取；含轮转归档 events.log.1 合并统计）
    d_lines = []
    for src_path in (SOURCES["D_fswatch_events"], SOURCES["D_fswatch_events"] + ".1"):
        if os.path.isfile(src_path):
            with open(src_path, encoding="utf-8", errors="replace") as f:
                d_lines += [l.rstrip("\n") for l in f if l.strip()]
    if d_lines:
        sd = stat_fswatch(d_lines)
        lines.append(f"| D·文件系统事件 | {SOURCES['D_fswatch_events']} | ✅ | 总 {sd['total']} ｜ changed {sd['changed']} ｜ deleted {sd['deleted']} ｜ initial {sd['initial']}（变化频率 f≈{sd['changed']} 次/观察期） |")
    else:
        lines.append(f"| D·文件系统事件 | {SOURCES['D_fswatch_events']} | ⚠️缺数据 | — |")

    lines.append("")
    lines.append("## 二·五、E 账·巡检连续性（AutoClaw 统一接入层 patrol）")
    lines.append("")
    hb = None
    if os.path.isfile(SOURCES["E_patrol_heartbeat"]):
        try:
            hb = datetime.strptime(open(SOURCES["E_patrol_heartbeat"], encoding="utf-8").read().strip(), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            hb = None
    if hb:
        age_min = (datetime.now() - hb).total_seconds() / 60
        status = "✅ 正常" if age_min <= 60 else f"🔴 断链 {int(age_min)} 分钟（>60min 告警）"
        lines.append(f"- 心跳：{hb.strftime('%Y-%m-%d %H:%M')}（距现在 {int(age_min)} 分钟）→ {status}")
    else:
        lines.append("- 心跳：**缺数据**（patrol 未运行或心跳文件缺失 → 🔴 接入层断链）")
    # patrol.log 各守卫调用结果统计
    if os.path.isfile(SOURCES["E_patrol_log"]):
        from collections import Counter
        guards, exits = [], Counter()
        for ln in open(SOURCES["E_patrol_log"], encoding="utf-8"):
            ln = ln.strip()
            if "exit=" not in ln or not ln.startswith("["):
                continue
            # 格式：[HH:MM:SS] guard_name exit=N（或 exit=N（格式/结论不合规→告警））
            name = ln.split("]")[1].strip().split()[0]
            code = ln.split("exit=")[1].split()[0].split("（")[0]
            guards.append(name)
            exits[(name, code)] += 1
        by_guard = {}
        for g in set(guards):
            ok = sum(v for (n, e), v in exits.items() if n == g and e == "0")
            by_guard[g] = f"{ok}/{guards.count(g)}"
        lines.append(f"- 各守卫调用成功次数（{len(by_guard)} 个守卫）：" + " ｜ ".join(f"{k}={v}" for k, v in sorted(by_guard.items())))
    else:
        lines.append("- patrol.log：**缺数据**")
    lines.append("")
    lines.append("## 二、两账对账（A↔B）")
    lines.append("")
    if (a_rows or a_bad >= 0) and (b_rows or b_bad >= 0):
        sa = stat_route_audit(a_rows)
        sb = stat_route_state(b_rows)
        lines.append(f"- A 账 potential_miss：**{sa['potential_miss']}** 条（路由'应该命中'但无执行证据）")
        lines.append(f"- B 账零命中：**{sb['zero_hit']}** 条（注入未命中任何 Skill）")
        lines.append(f"- 对账结论：两组数字交叉验证漏判可见性——potential_miss 需逐条回看是否对应零命中记录（机械层只出数字，判定留 AI）")
    else:
        lines.append("- ⚠️ A/B 账缺数据，无法对账")
    lines.append("")
    lines.append("## 三、机会成本列（v1.2 新增·不扩张损失了多少）")
    lines.append("")
    lines.append(f"- 报告期被确认的 potential_miss：**{stat_route_audit(a_rows)['potential_miss'] if (a_rows or a_bad >= 0) else '缺数据'}** 条（每次漏判=一次手动补做）")
    lines.append(f"- 护栏误拦/漏拦：见 C 账（guard_hit {stat_guard_events(c_rows)['guard_hit'] if (c_rows or c_bad >= 0) else '缺数据'} 条待人工 confirmed）")
    lines.append("- 手动归档/cp 动作计数：**缺数据**（采集源未建，方案待办：机会成本口径已下沉数据层）")
    lines.append("- 跨端手动转发次数：**缺数据**（同上）")
    lines.append("")
    lines.append("## 四、决策输入（事实陈述·判定留 AI/皮叔）")
    lines.append("")
    lines.append("- 扩张判定依据：D 账 f 值 vs POC 达标线登记表（时间回收类=回收期≤30 天）")
    lines.append("- 回滚判定依据：D 账事件缺失/双源漂移/路由误拦（偏离回滚条款）")
    lines.append("- 调参依据：B 账零命中分布 + route_semantic_eval 评测集回归（引擎规范原则3）")
    lines.append("- 机会成本双向决策：扩张失败损失 vs 不扩张损失（本报告三、四节数字）")
    lines.append("")
    lines.append("---")
    lines.append("*本报告由机械层产出；扩张/回滚/调参决策须由 AI 消费本报告后形成建议，交你拍板（守门禁：不自动改配置）。*")
    return "\n".join(lines) + "\n"


def main():
    args = sys.argv[1:]
    force = "--force" in args
    out = None
    if "--out" in args:
        out = args[args.index("--out") + 1]

    now = datetime.now()
    if not force:
        # 日期守卫：非 8/22 静默退出（crontab 年触发语义）
        if (now.year, now.month, now.day) != TARGET_DATE:
            return 0
        # 幂等：报告已存在则跳过
        if os.path.isfile(REPORT_PATH):
            return 0

    report = build_report()
    dest = out or REPORT_PATH
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"✅ 对账报告已产出：{dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
