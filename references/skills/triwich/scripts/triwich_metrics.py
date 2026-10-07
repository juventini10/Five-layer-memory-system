#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triwich_metrics.py —— 三明智指标机械计算器（③自评指标独立复核·机械署名层）

职责（2026-09-17 童灵上岗落地·皮叔认可三项方案之③）：
  把"指标计算"从"AI 逐条读 + 手写数字"升级为"常驻脚本机械输出"——
  凡能量化的指标一律脚本产出，⛔AI 不得手写数字（手写=标注权与执行权合一=可自我拔高）。

第一性原理依据：指标虚高的根因＝定义权/执行权/标注权三权合一。
  其中**标注权与执行权可机械分离**（脚本无利益·可复跑·可审计），故先把可机械的部分机械掉。
  定义权（口径选择）必然在人/AI——保留但留痕（见采样清单头部口径段·变更须留痕）。

三指标（双账）：
  ① A 值（G2）——已回访条目中 `发起方式:mechanism` 占比（口径源：状态行·非 body 登记行）
  ② M3 有效登记数——decision-room 有效登记（扣作废条目）
  ③ 行为级分母——**判定账 / 参考账双账**：
     · 判定账：编号 > `--judge-since` 且带等级后缀的环标注（⛔不含回标批次·用于定级判定）
     · 参考账：全部带等级后缀的环标注（含 2026-09-17 回标批次·仅看趋势·⛔不用于定级）

用法：
  python3 triwich_metrics.py                    # 人读格式
  python3 triwich_metrics.py --json             # 机器可读（供守卫/面板消费）
  python3 triwich_metrics.py --judge-since 38   # 指定判定账起算编号（默认=台账当前最大编号）

退出码：0（纯只读·不判定·不下结论）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import sys

__version__ = "1.0.0"

HOME = os.path.expanduser("~")
DECISION_ROOM = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置/triwich/references/decision-room.md")
SAMPLE_LEDGER = os.path.join(os.path.expanduser("[记忆共享中心]"), "自定义层/待完成工作/阶段A采样清单-三明智4.0.md")
SKILL_MD = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置/triwich/SKILL.md")
DIFF_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "自定义层/待完成工作")
CHANGELOG_MD = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置/triwich/references/CHANGELOG.md")


def calc_status():
    """⑤ 版本与已知欠账——⛔防"现状靠 AI 口述"。

    版本号、未落地候选数**由脚本读出**，不由我叙述——对齐 2026-09-17 教训
    （当日"现状陈述"曾把标签增长说成进展；而版本/欠账本可机械读取）。
    """
    out = {}
    t = _read(SKILL_MD) or ""
    m = re.search(r"^version:\s*(\S+)", t, re.MULTILINE)
    out["SKILL.md version"] = m.group(1).strip("\"'") if m else "?"
    c = _read(CHANGELOG_MD) or ""
    cand = re.findall(r"^### 候选\s*(\d+)", c, re.MULTILINE)
    out["待并入候选（未落地）"] = f"{len(cand)} 条" + (f"（#{','.join(cand)}）" if cand else "")
    latest = re.search(r"^### (v[\d.]+)", c, re.MULTILINE)
    out["CHANGELOG 最新条目"] = latest.group(1) if latest else "?"
    out["说明"] = "候选区状态从 CHANGELOG 候选区机械读取·⛔不静默跳过（处置规则见该区头部）"
    return out


def calc_closure():
    """④ 闭环进度——**只能靠外部动作增长**（⛔改口径/贴标签无法放大）。

    设计缘由（2026-09-17 实证）：当日"分母 0→27/46""M4 成立"属**标签当进展**——
    数字是真的，错在解读。凡"可被口径改大"的指标都不是进展指标；
    只有**需要外部动作**（人批改·真改文件·真回访）才能增长的数字才是。

    三要件（缺一即"闭环未跑完一圈"）：
      ① diff 已产出   —— 存在 ③引擎 diff 草稿
      ② diff 已落正文 —— SKILL.md 在草稿产出**之后**被改过（代理判据·⛔非精确）
      ③ 回访已验证    —— decision-room 存在含 diff/采纳/落正文 关键词的**已回访**归因
    """
    out = {}
    # ① diff 草稿
    drafts = []
    if os.path.isdir(DIFF_DIR):
        drafts = [f for f in os.listdir(DIFF_DIR)
                  if f.startswith("三明智5.0-diff草稿-") and f.endswith(".md")]
    draft_mt = min((os.path.getmtime(os.path.join(DIFF_DIR, f)) for f in drafts), default=None)
    out["① diff 已产出"] = f"✅ {len(drafts)} 份" if drafts else "❌ 无草稿"

    # ② 是否落正文（SKILL.md 晚于草稿被改）
    skill_mt = os.path.getmtime(SKILL_MD) if os.path.isfile(SKILL_MD) else None
    ver = None
    t = _read(SKILL_MD)
    if t:
        m = re.search(r"^version:\s*(\S+)", t, re.MULTILINE)
        ver = m.group(1).strip("\"'") if m else None
    if draft_mt and skill_mt:
        landed = skill_mt > draft_mt
        out["② diff 已落正文"] = (
            f"✅ SKILL.md version={ver}" if landed
            else f"❌ 未落（SKILL.md version={ver}·仍早于草稿·代理判据）"
        )
    else:
        out["② diff 已落正文"] = "🔵 悬置（缺 mtime）"

    # ③ 回访验证
    dr = _read(DECISION_ROOM) or ""
    resolved_n = len([s for s in re.findall(r"^## FU-\d+\s*·\s*状态:([^\n]*)$", dr, re.MULTILINE)
                      if "已回访" in s])
    body_hits = bool(re.search(r"归因[:：][^\n]*(?:diff|采纳|落正文)", dr))
    out["③ 回访已验证"] = (
        f"✅ 命中（已回访 {resolved_n} 条·含 diff/采纳/落正文 归因）" if body_hits
        else f"❌ 未见（已回访 {resolved_n} 条·均无 diff/采纳 归因）"
    )

    done = all(str(v).startswith("✅") for v in out.values())
    out["闭环是否跑完一圈"] = "✅ 是" if done else "❌ 未（5.0 不成立·见三要件）"
    out["诚实边界"] = "②为代理判据（mtime 比较·⛔非精确）——其他原因改 SKILL.md 亦会命中"
    return out

FU_HEAD_RX = re.compile(r"^## FU-(\d+)\s*·\s*状态:([^\n]*)$", re.MULTILINE)
STATUS_MECH_RX = re.compile(r"发起方式[:：]\s*(\w+)")
VOID_KW = "作废"
RESOLVED_KW = "已回访"

LEDGER_ROW_RX = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)
HOP_LEVEL_RX = re.compile(r"\[(证据|推理|表达|执行|输入)\]\[(L[012])\]")


def _read(p):
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def calc_decision_room(text, baseline=()):
    """① A 值 ② M3 有效登记。A 值口径=状态行（非 body 登记行）·剔除作废。

    双报口径（⛔脚本不自选达标口径——由文档定死，脚本只报数）：
      · A值（全含）      = 最保守·默认口径
      · A值（剔存量基线）= 需显式传 --a-baseline（G2 立项 §三"存量既往任务不计入分子做基线"）
    """
    rows = []
    for m in FU_HEAD_RX.finditer(text):
        seq, status = m.group(1), m.group(2).strip()
        mm = STATUS_MECH_RX.search(status)
        rows.append({
            "seq": seq,
            "status": status,
            "void": VOID_KW in status,
            "resolved": RESOLVED_KW in status,
            "mechanism": (mm.group(1) == "mechanism") if mm else None,
        })
    valid = [r for r in rows if not r["void"]]
    resolved = [r for r in valid if r["resolved"]]
    mech = [r for r in resolved if r["mechanism"] is True]
    manual = [r for r in resolved if r["mechanism"] is False]
    a_value = (len(mech) / len(resolved)) if resolved else None
    base = {str(b) for b in baseline}
    ex = [r for r in resolved if r["seq"] not in base]
    mech_ex = [r for r in ex if r["mechanism"] is True]
    a_ex = (len(mech_ex) / len(ex)) if ex else None
    return {
        "FU总数": len(rows),
        "有效登记(M3分子)": len(valid),
        "作废": len(rows) - len(valid),
        "已回访": len(resolved),
        "待回访": len(valid) - len(resolved),
        "A值分子mechanism": len(mech),
        "A值分母已回访": len(resolved),
        "A值（全含·最保守）": round(a_value, 3) if a_value is not None else None,
        "A值达标(==1.0)": (a_value == 1.0) if a_value is not None else None,
        "A值（剔存量基线）": round(a_ex, 3) if a_ex is not None else None,
        "A值剔基线分子/分母": f"{len(mech_ex)}/{len(ex)}",
        "剔除的基线条目": sorted(base) or "（未指定·默认全含）",
        "manual条目": [f"FU-{r['seq']}" for r in manual],
        "未标注发起方式": [f"FU-{r['seq']}" for r in resolved if r["mechanism"] is None],
    }


def calc_ledger(text, judge_since):
    """③ 行为级分母双账：判定账（编号 > judge_since）vs 参考账（全部）。"""
    counts = {"参考账": {"L0": 0, "L1": 0, "L2": 0}, "判定账": {"L0": 0, "L1": 0, "L2": 0}}
    max_no = 0
    rows_ref, rows_judge = 0, 0
    lines = text.split("\n")
    for ln in lines:
        m = LEDGER_ROW_RX.match(ln)
        if not m or "任务简述" in ln or "----" in ln:
            continue
        try:
            no = int(m.group(1))
        except ValueError:
            continue
        max_no = max(max_no, no)
        attached = bool(re.search(r"\[(证据|推理|表达|执行|输入)\]\[L[012]\]", ln))
        for lvl in HOP_LEVEL_RX.findall(ln):
            counts["参考账"][lvl[1]] += 1
            if no > judge_since:
                counts["判定账"][lvl[1]] += 1
        if attached:
            rows_ref += 1
            if no > judge_since:
                rows_judge += 1
    out = {"台账最大编号": max_no, "判定账起算(>此编号)": judge_since}
    for acct in ("参考账", "判定账"):
        c = counts[acct]
        beh = c["L1"] + c["L2"]
        tot = beh + c["L0"]
        out[acct] = {
            "环标注总数": tot, "L0": c["L0"], "L1": c["L1"], "L2": c["L2"],
            "行为级(L1+L2)": beh,
            "行为级占比": f"{(beh / tot * 100):.1f}%" if tot else "n/a",
        }
    out["参考账"]["带等级行数"] = rows_ref
    out["判定账"]["带等级行数"] = rows_judge
    return out


def main():
    args = sys.argv[1:]
    dr = _read(DECISION_ROOM)
    lg = _read(SAMPLE_LEDGER)
    if dr is None or lg is None:
        missing = [p for p, t in ((DECISION_ROOM, dr), (SAMPLE_LEDGER, lg)) if t is None]
        print(f"error: 数据源不可达: {missing}", file=sys.stderr)
        return 1
    # 先解析台账最大编号（判定账默认起算点），再算双账
    max_no = 0
    for ln in lg.split("\n"):
        m = LEDGER_ROW_RX.match(ln)
        if m and "任务简述" not in ln and "----" not in ln:
            try:
                max_no = max(max_no, int(m.group(1)))
            except ValueError:
                pass
    judge_since = max_no
    if "--judge-since" in args:
        i = args.index("--judge-since")
        if i + 1 < len(args):
            try:
                judge_since = int(args[i + 1])
            except ValueError:
                print(f"error: --judge-since 需整数，得到 {args[i+1]!r}", file=sys.stderr)
                return 2

    baseline = []
    if "--a-baseline" in args:
        i = args.index("--a-baseline")
        if i + 1 < len(args):
            baseline = [x.strip() for x in args[i + 1].split(",") if x.strip()]

    metrics = {
        "生成器": f"triwich_metrics.py v{__version__}",
        "口径说明": "本文件所有数字由脚本机械计算·⛔AI 不得手写（手写=三权合一=可自我拔高）",
        "decision_room": calc_decision_room(dr, baseline),
        "ledger": calc_ledger(lg, judge_since),
        "closure": calc_closure(),
        "status": calc_status(),
    }
    if "--json" in args:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
        return 0

    d = metrics["decision_room"]
    print(f"📊 三明智指标（{metrics['生成器']}·机械署名·⛔禁手写）")
    print(f"\n【① A 值 / ② M3】源=decision-room.md")
    print(f"  A值（全含·最保守） = {d['A值（全含·最保守）']}  ({d['A值分子mechanism']}/{d['A值分母已回访']})  达标(=1.0): {'✅' if d['A值达标(==1.0)'] else '❌ 未达标'}")
    print(f"  A值（剔存量基线）   = {d['A值（剔存量基线）']}  ({d['A值剔基线分子/分母']})  剔除={d['剔除的基线条目']}")
    print(f"  manual 条目: {', '.join(d['manual条目']) or '无'}")
    print(f"  M3 有效登记 = {d['有效登记(M3分子)']}（作废 {d['作废']}·FU总数 {d['FU总数']}）")
    print(f"  回访状态: 已回访 {d['已回访']} / 待回访 {d['待回访']}")
    print(f"  ⛔ 达标判据采用哪个口径须由文档定死·脚本不自选（默认报最保守）")
    l = metrics["ledger"]
    print(f"\n【③ 行为级分母·双账】源=阶段A采样台账（台账最大编号 {l['台账最大编号']}·判定账起算 >{l['判定账起算(>此编号)']}）")
    for acct in ("判定账", "参考账"):
        c = l[acct]
        print(f"  {acct}: 行为级 {c['行为级(L1+L2)']}/{c['环标注总数']} ({c['行为级占比']})  L0={c['L0']} L1={c['L1']} L2={c['L2']}  带等级行={c['带等级行数']}")
    print(f"  ⛔ 定级判定只看【判定账】；参考账含 2026-09-17 回标批次·仅看趋势")
    c = metrics["closure"]
    print(f"\n【④ 闭环进度】⛔ 只能靠外部动作增长（人批改/真改文件/真回访）——改口径无法放大")
    for k, v in c.items():
        print(f"  {k}: {v}")
    s = metrics["status"]
    print(f"\n【⑤ 版本与已知欠账】⛔ 由脚本读出·不由 AI 口述")
    for k, v in s.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
