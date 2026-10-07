#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triwich_improve_gen.py —— 三明智自主改进③ 引擎 M2 生成器（diff 草稿生成）

职责（对齐 立项文档 `自定义层/待完成工作/三明智4.0-自主改进引擎-立项.md` M2）：
  读两个既有台账（⛔不新造数据源）→ 机械统计 → 生成方法论改动 **diff 草稿**，
  呈你批改（采纳/修改/回滚）。只生成不采纳——裁决层永远在你（自主≠黑箱·价值层永不裁决）。

两个数据源：
  ① decision-room.md        —— 决策卡回访唯一 source（偏差类型 B1-B9 + 归因描述）
  ② 阶段A采样台账           —— 卡点观察（[证据]/[推理]/[表达]/[执行]/[输入] 环节标注）

v0.2.0（2026-09-17）：接「行为级证据锚分级」（阶段A采样清单头部定义·L0/L1/L2），为 M4 提供可 count 的分母：
  - 台账卡点列解析等级后缀 `[证据][L1]`（L0=自评·L1=内证·L2=外证）
  - 统计**行为级分母**（L1+L2 条数与占比）→ 替代"总频次"作方法论改动候选的裁决依据
  - 候选改动分两区：**A 有行为级支撑（进批改）** / **B 待补行为级证据（不进批改·转实测量采样）**
  - 阈值外置 `--min-behavior`（默认 2）——⛔脚本不手写判据（防镀金 S160），阈值=可批改项

v0.3.0（2026-09-17·童灵裁决·皮叔授权）：A 区加**独立性门**——候选进人批改须同时满足
  ① 该环节 L1+L2 ≥ min-behavior ② 该环节 L2 ≥ min-l2（默认 1）。
  理由：纯 L1 由执行者自产，≥2 条 L1 可以同时错（S847 自审自过）——至少 1 条 L2（独立评估者/
  外部源/跨源交叉/回访对账）才构成"执行者与评估者分离"的最低门。新增 `--min-l2` 外置参数。

⛔ 防镀金（S160）：本脚本⛔不手写方法论判据——所有"候选改动"必须由数据锚点机械触发：
  - 高频失守环节由台账环节频次统计得出（<threshold 不出候选）
  - 「归因失聪」候选触发条件 = 某高频环节相关轮次在 decision-room 归因里全部落 B0/无
    （台账已证薄弱但决策卡不认账 = 数据自相矛盾 = 判定层失聪的可机检信号）
  - 行为级分母由等级后缀机械计数得出（无等级后缀=不计入·⛔不猜）
  候选产出后一律标「⛔待批改·非结论」，🔴回滚闸不变。

用法：
  python3 triwich_improve_gen.py                      # 生成默认 diff 草稿（待完成工作/三明智5.0-diff草稿-{日期}.md）
  python3 triwich_improve_gen.py --out {路径}          # 指定输出路径
  python3 triwich_improve_gen.py --json                # 机器可读（供守卫/面板消费）
  python3 triwich_improve_gen.py --no-write            # 只打印统计不写文件（预览）
  python3 triwich_improve_gen.py --min-behavior 3      # 调整"行为级支撑"阈值（默认 2）

退出码：0（只读/预览/草稿生成——不判定采纳，裁决在你）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import sys
from datetime import datetime

__version__ = "0.3.0"

HOME = os.path.expanduser("~")
DECISION_ROOM = os.path.join(
    HOME, "[记忆共享中心]/技能配置/triwich/references/decision-room.md"
)
SAMPLE_LEDGER = os.path.join(
    HOME, "[记忆共享中心]/自定义层/待完成工作/阶段A采样清单-三明智4.0.md"
)
DEFAULT_OUT_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "自定义层/待完成工作")

# 行为级支撑阈值（外置可批改项·⛔脚本不手写判据）
MIN_BEHAVIOR = 2
# A 区独立性下限（2026-09-17 童灵裁决·皮叔授权）：≥1 条 L2（独立评估者/外部源/跨源交叉/回访对账）
# 才算"执行者与评估者分离"的最低门——纯 L1 由执行者自产，≥2 条 L1 可以同时错（S847 自审自过）
MIN_L2 = 1

# —— 环节 → 方法论域 映射（纯标签映射·非判据）——
HOPS = {
    "证据": "证据纪律（事实vs解释/替代原因/证据效力）",
    "推理": "推理链（前提→结论·主要矛盾）",
    "表达": "呈现（结论块直击要点/签名一致）",
    "执行": "执行（延误/卡壳/挂账代打）",
    "输入": "输入（目标含糊/缺参数）",
}
HOP_RX = re.compile(r"\[(证据|推理|表达|执行|输入)\]")
# 等级后缀：`[证据][L1]`（行为级证据锚分级·阶段A采样清单头部定义）
HOP_LEVEL_RX = re.compile(r"\[(证据|推理|表达|执行|输入)\]\s*\[(L[012])\]")
# 疑似等级格式错（写了 [L...] 但不合 L0/L1/L2 规范·如 [L1/L2]）——防格式漂移静默失明
LEVEL_LIKE_RX = re.compile(r"\[L[^\[\]]*\]")
LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2}

# —— decision-room FU 块解析 ——
FU_BLOCK_RX = re.compile(
    r"^## FU-(\d+)\s*·\s*状态:[^\n]*\n(.*?)(?=^## FU-|\Z)",
    re.MULTILINE | re.DOTALL,
)
BIAS_RX = re.compile(r"偏差类型：\s*(B\d+|—|（待回访）)")
ATTRIB_RX = re.compile(r"归因：\s*(.+)")
STATUS_RX = re.compile(r"^## FU-(\d+)\s*·\s*状态:([^·\n]+)", re.MULTILINE)
VOID_KW = "作废"
PENDING_KW = "待回访"

# —— 采样台账行解析（编号行·卡点环节）——
LEDGER_ROW_RX = re.compile(r"^\|\s*(\d+)\s*\|", re.MULTILINE)


def _has_path(p):
    return os.path.isfile(p)


def load_decision_room(path=DECISION_ROOM):
    """返回 [ {seq,status,bias,attribution,void,pending} ] 决策卡条目。"""
    if not _has_path(path):
        return None
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for m in FU_BLOCK_RX.finditer(text):
        seq = int(m.group(1))
        head_match = STATUS_RX.search(m.group(0))
        status = head_match.group(2).strip() if head_match else ""
        block = m.group(2)
        bm = BIAS_RX.search(block)
        am = ATTRIB_RX.search(block)
        out.append({
            "seq": seq,
            "status": status,
            "bias": bm.group(1).strip() if bm else "",
            "attribution": am.group(1).strip() if am else "",
            "void": VOID_KW in status,
            "pending": PENDING_KW in status,
        })
    return out


def load_sample_ledger(path=SAMPLE_LEDGER):
    """返回 [{row, hops, levels, malformed_level, line}] 采样台账行（只统计存在的编号行）。

    hops    = 该行出现的环节（去重保序）
    levels  = {环节: "L0"|"L1"|"L2"}（仅"带等级后缀"的环节；同环多标取最高级）
    未在 levels 中的环节 = 未标等级（不计入行为级分母）
    """
    if not _has_path(path):
        return None
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    out = []
    for idx, ln in enumerate(lines):
        m = LEDGER_ROW_RX.match(ln)
        if not m:
            continue
        if "任务简述" in ln or "----" in ln:
            continue
        hops = list(dict.fromkeys(HOP_RX.findall(ln)))
        levels = {}
        for hop, lvl in HOP_LEVEL_RX.findall(ln):
            if hop not in levels or LEVEL_RANK[lvl] > LEVEL_RANK[levels[hop]]:
                levels[hop] = lvl
        # 疑似格式错：出现 [L...] 但不被 HOP_LEVEL_RX 认下
        malformed = len(LEVEL_LIKE_RX.findall(ln)) - len(HOP_LEVEL_RX.findall(ln))
        out.append({
            "row": int(m.group(1)),
            "hops": hops,
            "levels": levels,
            "malformed_level": max(malformed, 0),
            "line_no": idx + 1,
        })
    return out


def gather_stats(fus, rows, min_behavior=MIN_BEHAVIOR, min_l2=MIN_L2):
    """机械统计：归因分布 / 环节频次 / 环节↔归因交叉（失聪检测）/ 行为级分母（M4 判据）。"""
    bias_dist = {}
    for f in fus:
        if f["void"]:
            continue
        key = f["bias"] or "（无标注）"
        bias_dist[key] = bias_dist.get(key, 0) + 1

    hop_dist = {}
    for r in rows:
        for h in r["hops"]:
            hop_dist[h] = hop_dist.get(h, 0) + 1
    hop_sorted = sorted(hop_dist.items(), key=lambda kv: -kv[1])

    # —— 行为级分母（M4 判据）：按"环标注"计（一行可多环），并按行去重报"含行为级行数" ——
    level_per_hop = {}
    for h in hop_dist:
        level_per_hop[h] = {"L0": 0, "L1": 0, "L2": 0, "未标": 0}
    total_tagged = 0
    for r in rows:
        for h in r["hops"]:
            total_tagged += 1
            lvl = r["levels"].get(h)
            level_per_hop[h][lvl if lvl else "未标"] += 1
    l1 = sum(v["L1"] for v in level_per_hop.values())
    l2 = sum(v["L2"] for v in level_per_hop.values())
    l0 = sum(v["L0"] for v in level_per_hop.values())
    unlabeled = sum(v["未标"] for v in level_per_hop.values())
    behavior = l1 + l2
    rows_with_behavior = sum(1 for r in rows if any(v in ("L1", "L2") for v in r["levels"].values()))
    malformed_total = sum(r["malformed_level"] for r in rows)
    behavior_denom = {
        "环标注总数": total_tagged,
        "L0（自评·不计入）": l0,
        "L1（内证·行为级）": l1,
        "L2（外证·行为级）": l2,
        "未标等级": unlabeled,
        "行为级（L1+L2）": behavior,
        "行为级占比": f"{(behavior / total_tagged * 100):.1f}%" if total_tagged else "n/a",
        "含行为级行数": rows_with_behavior,
        "台账行数": len(rows),
        "疑似等级格式错": malformed_total,
        "行为级支撑阈值(min-behavior)": min_behavior,
        "L2独立性下限(min-l2)": min_l2,
    }

    # 归因失聪检测：高频失守环节的相关轮次，在 decision-room 里是否全被判"无偏差(B0/空)"
    # 相关轮次 = 该环节出现 ≤2 环的"专一失守"轮次（越集中越可信）
    focus_rows = [r for r in rows if r["hops"] and len(r["hops"]) == 1]
    # 失败样本判定只看「已回访·非作废」条目——待回访占位（偏差=（待回访））不证明有失败样本
    resolved = [f for f in fus if not f["void"] and not f["pending"]]
    non_b0 = [f for f in resolved if f["bias"] not in ("", "B0")]
    deaf = []
    for hop, cnt in hop_sorted:
        if cnt < 2:
            continue
        focus_hop_rows = [r for r in focus_rows if r["hops"] == [hop]]
        if not focus_hop_rows:
            continue
        # 失聪判定：高频环节(≥2) + 已回访非作废条目归因区整体无失败标注
        if not non_b0:
            deaf.append({
                "hop": hop,
                "源环节频次": cnt,
                "专一失守轮次": len(focus_hop_rows),
                "信号": "该环节在采样台账高频失守，但 decision-room 已回访归因全部落 B0/无——归因标注很可能未真正区分失败样本（判定层失聪）",
            })
    return {
        "归因分布": bias_dist,
        "环节频次": dict(hop_sorted),
        "环节等级分布": level_per_hop,
        "行为级分母": behavior_denom,
        "归因失聪信号": deaf,
    }


def build_diff(stats, fus, rows, min_behavior=MIN_BEHAVIOR, min_l2=MIN_L2):
    """据机械统计生成候选 diff（改点/理由数据锚点/反方/验证计划）。纯数据触发·不手写判据。

    候选分两区（v0.2.0·v0.3.0 加独立性门）：
      A 有行为级支撑 —— 该环节 L1+L2 ≥ min_behavior **且** L2 ≥ min_l2（进人批改）
      B 待补行为级证据 —— 仅 L0/未标、或行为级够但缺 L2 独立性（⛔不进批改·转实测量采样）
    """
    now = datetime.now()
    date_s = now.strftime("%Y-%m-%d")
    denom = stats["行为级分母"]
    lvl_per_hop = stats["环节等级分布"]

    def hop_behavior(hop):
        d = lvl_per_hop.get(hop, {})
        return d.get("L1", 0) + d.get("L2", 0)

    def hop_l2(hop):
        return lvl_per_hop.get(hop, {}).get("L2", 0)

    def gate_a(hop):
        """A 区双条件：行为级够量 + 至少 1 条 L2（执行者与评估者分离）"""
        return hop_behavior(hop) >= min_behavior and hop_l2(hop) >= min_l2

    cands_a, cands_b = [], []

    # 候选①：归因失聪（若触发）——定性信号，按行为级支撑度归区
    for d in stats["归因失聪信号"]:
        c = {
            "改点": f"偏差归因标注未区分失败样本：{d['hop']} 环节高频失守（源环节频次 {d['源环节频次']}·专一失守轮次 {d['专一失守轮次']}），但 decision-room 归因区无任何非 B0 失败标注",
            "理由": f"数据锚点——采样台账『{d['hop']}』环节失守 {d['源环节频次']} 次（≥2 阈值·立项 §三防镀金），对应决策卡归因却 100% B0/无 → 两账矛盾·决策卡读不出失败规律·无法支撑自主改进",
            "反方": "可能 B0 系真实（部分轮次预测确实成立）——台账『失守』是过程层卡点、卡片 B0 是结果层无偏差，两者度量对象不同，未必矛盾；需逐轮人工复核归因后再定",
            "验证计划": "人批改采纳后：对当前 decision-room 全量非作废条目做归因复检——若存在[证据]环节对应轮次原 B0 实应有偏差 → 修正标注并落口径修订；随后以新归因分布为基线重跑本生成器，对比复检前后候选改动是否更线。可证伪：若复检后仍全 B0 且环节失守消失，则撤销本候选",
        }
        (cands_a if gate_a(d["hop"]) else cands_b).append(c)

    # 候选②：环节高频呈现（通用·数据触发·理由用各环节自身锚点·不强套模板）
    for hop, cnt in stats["环节频次"].items():
        if cnt < 2:
            continue
        bh = hop_behavior(hop)
        c = {
            "改点": f"{hop} 环节为高频卡点（{cnt} 次）·方法论域『{HOPS.get(hop,'?')}』疑似最薄弱",
            "理由": f"数据锚点——采样台账『{hop}』环节出现 {cnt} 次（≥2 阈值）·在该环节内部为最高频；行为级支撑：L1+L2={bh}·L2={hop_l2(hop)}（门槛 {min_behavior}/{min_l2}）",
            "反方": "台账标注是 AI 收尾自评（判断层假设·事件后回访校准）——非行为级实测，可能存在标注偏差（把别的环节误标到本环）；且频次高≠损益大",
            "验证计划": f"人批改采纳后：锁定『{hop}』环节,后续 N 轮三明智对该环节强制加证据锚（疑似+证据锚标注法·防伪设计），回访统计环比下降 → 支撑归因;无下降则撤销并查标注真实性",
        }
        (cands_a if gate_a(hop) else cands_b).append(c)

    if not cands_a and not cands_b:
        cands_b.append({
            "改点": "（当前无 ≥2 频次的高频失守模式）",
            "理由": "数据锚点——环节频次全 <2·归因无失败样本·样本不够支撑改动建议",
            "反方": "样本不足时强行出候选 = 镀金（S160）·宁可不出",
            "验证计划": "继续积累数据·满阈值后重跑本生成器",
        })

    lines = []
    lines.append(f"# 三明智自主改进③ · 月度 diff 草稿（{date_s}）")
    lines.append("")
    lines.append(f"> **状态**：🟡 待你批改（采纳/修改/回滚）——本文件由 `triwich_improve_gen.py` v{__version__} 数据驱动生成，⛔AI 未手写判据")
    lines.append(f"> **数据窗**：decision-room 有效登记 {len([f for f in fus if not f['void']])} 条 · 采样台账 {len(rows)} 行")
    lines.append("")
    lines.append("## 一、归因分布（decision-room·口径表#1 有效条目）")
    lines.append("")
    lines.append("| 偏差类型 | 次数 |")
    lines.append("|---|---|")
    for k, v in stats["归因分布"].items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## 二、卡点环节分布（采样台账）")
    lines.append("")
    lines.append("| 环节 | 频次 |")
    lines.append("|---|---|")
    for hop, cnt in stats["环节频次"].items():
        lines.append(f"| {hop} | {cnt} |")
    lines.append("")
    lines.append("## 三、行为级分母（M4 判据 · 机械统计）")
    lines.append("")
    lines.append("> 口径源=阶段A采样清单头部「行为级证据锚分级」（L0 自评 ⛔不计 / L1 内证 / L2 外证）。")
    lines.append("> 台账卡点列须带等级后缀 `[环节][L1]`；⛔缺等级=不计入行为级统计（防自评当实测·S006）。")
    lines.append("")
    lines.append("| 指标 | 值 |")
    lines.append("|---|---|")
    for k, v in denom.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("| 环节 | 行为级(L1+L2) |")
    lines.append("|---|---|")
    for hop in stats["环节频次"]:
        lines.append(f"| {hop} | {hop_behavior(hop)} |")
    lines.append("")
    lines.append("## 四、候选改动（⛔待批改·非结论·裁决层=你）")
    lines.append("")
    lines.append(f"### A. 有行为级支撑（进人批改·门槛：该环节 L1+L2 ≥ {min_behavior} **且** L2 ≥ {min_l2}）")
    lines.append("")
    if cands_a:
        for i, c in enumerate(cands_a, 1):
            lines.append(f"#### A{i} · {c['改点']}")
            lines.append("")
            lines.append(f"- **理由（数据锚点）**：{c['理由']}")
            lines.append(f"- **反方（≥1）**：{c['反方']}")
            lines.append(f"- **验证计划（可证伪）**：{c['验证计划']}")
            lines.append("")
    else:
        lines.append(f"（无）——无环节同时满足 L1+L2 ≥ {min_behavior} 与 L2 ≥ {min_l2}；方法论改动不足以进批改。")
        lines.append("")
    lines.append(f"### B. 待补行为级证据（⛔不进批改 · 转实测量采样累积）")
    lines.append("")
    if cands_b:
        for i, c in enumerate(cands_b, 1):
            lines.append(f"#### B{i} · {c['改点']}")
            lines.append("")
            lines.append(f"- **理由（数据锚点）**：{c['理由']}")
            lines.append(f"- **反方（≥1）**：{c['反方']}")
            lines.append(f"- **验证计划（可证伪）**：{c['验证计划']}")
            lines.append("")
    else:
        lines.append("（无）")
        lines.append("")
    lines.append("---")
    lines.append(f"> 🔴 红线：本草稿不落 SKILL.md 正文——须你批改通过后才走 ④ 验证回填（正文+eval-set+固化快照+守卫回归）。产生={date_s} by triwich_improve_gen.py v{__version__}")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    min_behavior = MIN_BEHAVIOR
    if "--min-behavior" in args:
        i = args.index("--min-behavior")
        if i + 1 < len(args):
            try:
                min_behavior = int(args[i + 1])
            except ValueError:
                print(f"error: --min-behavior 需整数，得到 {args[i+1]!r}")
                return 2
    min_l2 = MIN_L2
    if "--min-l2" in args:
        i = args.index("--min-l2")
        if i + 1 < len(args):
            try:
                min_l2 = int(args[i + 1])
            except ValueError:
                print(f"error: --min-l2 需整数，得到 {args[i+1]!r}")
                return 2
    fus = load_decision_room()
    rows = load_sample_ledger()
    if fus is None or rows is None:
        missing = []
        if fus is None:
            missing.append(DECISION_ROOM)
        if rows is None:
            missing.append(SAMPLE_LEDGER)
        print(f"error: 数据源不可达: {missing}")
        return 1
    # 自验（铁律-021①）：输入非空 + 样本抽核
    if not rows:
        print("error: 采样台账解析到 0 行——解析器疑有误，拒绝下结论")
        return 1

    stats = gather_stats(fus, rows, min_behavior, min_l2)
    doc = build_diff(stats, fus, rows, min_behavior, min_l2)

    if "--json" in args:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0
    if "--no-write" in args:
        print(doc)
        return 0

    date_s = datetime.now().strftime("%Y%m%d")
    default_out = os.path.join(DEFAULT_OUT_DIR, f"三明智5.0-diff草稿-{date_s}.md")
    out = default_out
    if "--out" in args:
        i = args.index("--out")
        if i + 1 < len(args):
            out = args[i + 1]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"📄 已生成 diff 草稿（⛔待你批改·不落正文）：{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
