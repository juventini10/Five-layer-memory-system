#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
confidence_calibration_audit.py v1.0 · 童灵置信度按档对账（只读）
================================================================
来源：三明智 FU-54 双轨修正版（2026-09-21·皮叔批准"按建议推荐"）
定位：修正点①+③——把「置信度标签→真实命中率」从惯例变成可测量。

只读审计 step3-first-review-log.md（台账两列：自报标签 × 你复核结果），
按档 group-by 输出：n / 你复核覆盖 / 推翻 / 校准判定。
⛔ 只读台账，不写任何台账内容；报告独立落盘 steps/。

口径（③ 阈值语义显式化）：
- 每档 你复核覆盖 n>=20 才出校准值；否则判「不可判定」。
- 0 推翻档只报 Clopper-Pearson 95% 单侧上界，不报点估计（对齐 gray_release_stats.py）。
- 未校准期（覆盖<20）：batch_auto_pass 阈值语义=惯例值·⛔不新增授权面（降级声明随报告输出）。
- 「平行校验记录」区行不计分母（台账自带声明：不计推翻率分母）。
- 批次聚合行（置信度="高×8/中高×40"）单独计为 batch 口径，可解析 ×N 则拆分，标记 batch=True。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
from pathlib import Path

LOG_PATH = Path.home() / "~/[记忆共享中心]/数字分身/steps/step3-first-review-log.md"
REPORT_DIR = Path.home() / "~/[记忆共享中心]/数字分身/steps"
TIERS = ("中高", "高", "中", "低")  # 匹配顺序：中高 必须先于 高/中
CAL_N_MIN = 20
EXCLUDE_SECTION_KEY = "平行校验"


def parse_confidence(cell: str):
    """返回 (tier, count, batch)。tier=None 表示无法归档（混合/异常）。"""
    c = cell.strip().replace("🟢", "").replace("🟡", "").strip()
    # 批次聚合形态：高×8/中高×40
    parts = [p for p in re.split(r"[/、]", c) if p.strip()]
    if len(parts) > 1 or "×" in c:
        total_flag = False
        out = []
        for p in parts:
            m = re.match(r"^(中高|高|中|低)\s*[×x]\s*(\d+)$", p.strip())
            if m:
                out.append((m.group(1), int(m.group(2))))
                total_flag = True
        if total_flag:
            return out  # list of (tier,count)
        return None  # 混合不可归档（如 "高/中高"）
    for t in TIERS:
        if c == t:
            return t
    return None


def classify_review(cell: str):
    """你复核列分类（口径对齐 gray_release_stats.py：认可/已质证/亲裁=真质证）。
    返回 upheld/overturned/self_return/no_review/other。"""
    c = cell.strip()
    if not c or c in {"无", "-", "—", "⬜", "⬜待复核"}:
        return "no_review"
    if "推翻" in c or c.startswith("❌"):
        return "overturned"
    if "自查退回" in c:
        return "self_return"
    if "认可" in c or "已质证" in c or "亲裁" in c or "通过" in c or "✅" in c:
        return "upheld"
    return "other"


def main():
    if not LOG_PATH.exists():
        print(f"[FAIL] 台账不存在: {LOG_PATH}")
        sys.exit(1)
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()

    section = ""
    header_cols = None  # {name: idx}——只在连续表格块内有效（防他表借用表头）
    stats = {t: {"n": 0, "batch_n": 0, "upheld": 0, "overturned": 0,
                 "self_return": 0, "no_review": 0, "excluded_parallel": 0}
             for t in TIERS}
    mixed_rows = 0
    sections_seen = set()

    def header_map(cells):
        m = {}
        for i, name in enumerate(cells):
            name = name.strip()
            if name in ("置信度", "你复核", "结果", "卡号"):
                m[name] = i
        # 结构性判据：台账表必须同时有 卡号+置信度 双锚（缺卡号的"置信度"表
        # = 他类表格借用表头，排除）
        return m if ("置信度" in m and "卡号" in m) else None

    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:].strip()
            sections_seen.add(section)
            header_cols = None  # 区段切换=表格块终止（结构性防误判）
            continue
        if not line.startswith("|"):
            # 非表格行=表格块终止——表头只对紧随其后的连续行生效
            # （实证：L3盲审抽检区复用同款9列表头、'| 高 |'出现在评审打分列，
            #   表头跨块存活会把评审矩阵误扫成台账——2026-09-21 实测根因）
            if not line.startswith(">"):  # 引用行紧贴表格属同块元信息，不断块
                header_cols = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # 分隔行
        if line.startswith("| #") or line.startswith("| 批") or "日期" in cells[:2]:
            header_cols = header_map(cells)
            continue
        if not cells or all(not c for c in cells):
            continue
        if header_cols is None or "置信度" not in header_cols:
            continue
        idx_c = header_cols["置信度"]
        if idx_c >= len(cells):
            continue
        excluded = EXCLUDE_SECTION_KEY in section
        conf = parse_confidence(cells[idx_c])
        # 复核结果列：详表取 你复核，批次表取 结果
        ridx = header_cols.get("你复核", header_cols.get("结果"))
        review = classify_review(cells[ridx]) if (ridx is not None and ridx < len(cells)) else "no_review"

        if isinstance(conf, list):  # 批次聚合 ×N
            for tier, cnt in conf:
                stats[tier]["batch_n"] += cnt
            continue
        if conf is None:
            mixed_rows += 1
            continue
        s = stats[conf]
        if excluded:
            s["excluded_parallel"] += 1
            continue
        s["n"] += 1
        if review == "upheld":
            s["upheld"] += 1
        elif review == "overturned":
            s["overturned"] += 1
        elif review == "self_return":
            s["self_return"] += 1
        elif review == "no_review":
            s["no_review"] += 1

    # sanity：解析结果非空
    total = sum(s["n"] for s in stats.values())
    if total == 0:
        print("[FAIL] 解析到 0 行数据——判据或格式漂移，拒绝出报告（铁律-021①）")
        sys.exit(2)

    def cp_upper(n, k):
        """Clopper-Pearson 95% 单侧上界（k=0 时精确式）。"""
        if n == 0:
            return None
        if k == 0:
            return 1 - 0.05 ** (1.0 / n)
        # 通用情形粗上界（本轮预期 k=0；k>0 时提示用 scipy）
        return None

    out = []
    out.append("# 置信度按档对账报告（只读审计·数据截止本报告生成时刻）\n")
    out.append(f"- 台账：`{LOG_PATH}`")
    out.append(f"- 扫描区段：{len(sections_seen)} 个 · 混合不可归档行：{mixed_rows}")
    out.append(f"- 口径：详表逐卡行计主账；批次 ×N 聚合行单列（batch·无逐卡复核）；「{EXCLUDE_SECTION_KEY}」区不计分母")
    out.append("- 表头有效性：仅限连续表格块内（结构性防误判·2026-09-21 根治 L3盲审抽检区借用表头混入）")
    out.append("\n> **📌 口径勘误（2026-09-21）**：此前对话引用「高98/中高148/中2」系 `grep '| 高 |'` 污染口径——232 行来自「三明治L3双盲审·价值层10卡抽检」评审矩阵表（'| 高 |' 出现在评审打分列·非置信度列），非初审台账。本报告为结构性判据修正后的真实口径（数据截止 2026-09-21）。你真质证 n=41 的总量口径由 `gray_release_stats.py` 承载（含批次级质证记录），本报告只做「逐卡 标签×复核」交叉对账——两者分工不混。\n")
    out.append("| 档 | 逐卡n | 批量n | 你复核认可 | 推翻 | 自查退回 | 未复核 | 平行区(不计) | 命中率 | 校准判定 |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for t in TIERS:
        s = stats[t]
        covered = s["upheld"] + s["overturned"]
        if s["overturned"] == 0 and covered > 0:
            rate = f"0推翻·CI上界{cp_upper(covered, 0):.1%}"
        elif s["overturned"] > 0:
            rate = f"{s['upheld']}/{covered}={s['upheld']/covered:.1%}"
        else:
            rate = "—"
        verdict = ("✅可出校准值" if covered >= CAL_N_MIN
                   else f"❌不可判定（覆盖{covered}<{CAL_N_MIN}）")
        out.append(f"| {t} | {s['n']} | {s['batch_n']} | {s['upheld']} | "
                   f"{s['overturned']} | {s['self_return']} | {s['no_review']} | "
                   f"{s['excluded_parallel']} | {rate} | {verdict} |")
    out.append("\n## 阈值语义声明（修正点③）\n")
    any_calibrated = any((s["upheld"] + s["overturned"]) >= CAL_N_MIN for s in stats.values())
    if not any_calibrated:
        out.append("⚠️ 当前无任何档位达到校准样本门槛。**未校准期规则**：")
    else:
        out.append("已达门槛档位以实测命中率校准阈值；未达门槛档位适用：**未校准期规则**：")
    out.append("- `batch_auto_pass.py` 的「高→自动通过」阈值在本报告覆盖期内 = **惯例值**，无校准含义；")
    out.append("- ⛔ 未校准期内不得以任何标签为依据**新增**授权面（扩自动通过范围/提自动通过层级）；")
    out.append("- 校准生效条件：该档 你复核覆盖 n≥" + str(CAL_N_MIN) + " 且命中率达标（阈值线由你拍板）。")

    report = "\n".join(out) + "\n"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rpath = REPORT_DIR / "calibration-audit-latest.md"
    rpath.write_text(report, encoding="utf-8")
    print(report)
    print(f"[OK] 报告已落盘: {rpath}")
    print(f"[SANITY] 逐卡合计={total} · 批量×N合计={sum(s['batch_n'] for s in stats.values())} · 口径=结构性判据修正后（grep 污染口径已勘误·见报告）")


if __name__ == "__main__":
    main()
