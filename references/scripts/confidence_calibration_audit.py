#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
confidence_calibration_audit.py v1.1 · 童灵置信度按档对账（只读）
================================================================
来源：三明智 FU-54 双轨修正版（2026-09-21·皮叔批准"按建议推荐"）
v1.1：2026-10-08 Qoder CN 抽检包代判回写后 n 未计入——实锤 v1.0 连续块纪律
  对"表格行间有空行"的台账断表漏行（与 build_spotpack 同型病·台账 L60/311/…
  九列逐卡行全部丢失，逐卡n 严重偏低）。根治=改行级结构判据（序号+ISO日期+
  卡号形态+9列schema），污染防控改走：①区段排除（平行校验/预筛记录两区自带
  不计声明）②schema过滤（双盲审2列处置表不匹配九列）③「童灵自动通过」不入
  质证分子。双盲审区头为陈旧容器（L300+全是合法初审行含真推翻），不整区排除。

只读审计 step3-first-review-log.md（台账两列：自报标签 × 你复核结果），
按档 group-by 输出：n / 你复核覆盖 / 推翻 / 校准判定。
⛔ 只读台账，不写任何台账内容；报告独立落盘 steps/。

口径（③ 阈值语义显式化）：
- 每档 你复核覆盖 n>=20 才出校准值；否则判「不可判定」。
- 0 推翻档只报 Clopper-Pearson 95% 单侧上界，不报点估计（对齐 gray_release_stats.py）。
- 未校准期（覆盖<20）：batch_auto_pass 阈值语义=惯例值·⛔不新增授权面（降级声明随报告输出）。
- 「平行校验/预筛记录」区行不计（台账该区自带不计声明）；「童灵自动通过」末列不计质证（v1.1堵「通过」关键词误入分子）。
- 批次聚合行（置信度="高×8/中高×40"，五列卡号区间形态）单独计为 batch 口径，标记 batch=True。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
from pathlib import Path

LOG_PATH = Path.home() / "[记忆共享中心]/数字分身/steps/step3-first-review-log.md"
REPORT_DIR = Path.home() / "[记忆共享中心]/数字分身/steps"
TIERS = ("中高", "高", "中", "低")  # 匹配顺序：中高 必须先于 高/中
CAL_N_MIN = 20
EXCLUDE_SECTION_KEYS = ("平行校验", "预筛记录")  # 双盲审区头实为陈旧容器：L300+全是合法初审行（含真推翻），整区排除=错杀，2026-10-08 二次实跑纠正

ROW_RE = re.compile(r"^\|\s*\d+\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([A-Za-z]+\d+)\s*\|")
BATCH_RE = re.compile(r"^\|\s*\d+\s*\|\s*S\d+-S\d+")


def parse_confidence(cell: str):
    """返回 (tier, count, batch)。tier=None 表示无法归档（混合/异常）。"""
    c = cell.strip().replace("🟢", "").replace("🟡", "").strip()
    parts = [p for p in re.split(r"[/、]", c) if p.strip()]
    if len(parts) > 1 or "×" in c:
        out = []
        for p in parts:
            m = re.match(r"^(中高|高|中|低)\s*[×x]\s*(\d+)$", p.strip())
            if m:
                out.append((m.group(1), int(m.group(2))))
        if out:
            return out  # list of (tier,count)
        return None
    for t in TIERS:
        if c.startswith(t):
            return t
    return None


def classify_review(cell: str):
    """你复核列分类（口径对齐 gray_release_stats.py：认可/已质证/亲裁=真质证）。
    返回 upheld/overturned/self_return/no_review/other。"""
    c = cell.strip()
    if c.startswith("童灵自动通过") or "童灵自动通过" in c:
        return "no_review"  # 自动通过≠你复核，含「通过」字样不得入质证分子（v1.1堵口）
    if not c or c in {"无", "-", "—", "⬜", "⬜待复核"} or c.startswith("待你抽检") or c.startswith("待你抽检"):
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
    stats = {t: {"n": 0, "batch_n": 0, "upheld": 0, "overturned": 0,
                 "self_return": 0, "no_review": 0, "excluded_parallel": 0}
             for t in TIERS}
    unparsed_flag_rows = 0
    sections_seen = set()

    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:].strip()
            sections_seen.add(section)
            continue
        if not line.startswith("|"):
            continue
        excluded = any(k in section for k in EXCLUDE_SECTION_KEYS)

        if BATCH_RE.match(line):  # 批次聚合行：| N | S62-S109（48张） | ... | 高×8/中高×40 | ...
            cells = [c.strip() for c in line.strip("|").split("|")]
            for cell in cells:
                conf = parse_confidence(cell)
                if isinstance(conf, list):
                    for tier, cnt in conf:
                        stats[tier]["batch_n"] += cnt
                    break
            continue

        m = ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        conf = parse_confidence(cells[4]) if len(cells) >= 9 else None
        if conf is None or isinstance(conf, list):
            if len(cells) >= 9:
                unparsed_flag_rows += 1
            continue
        review = classify_review(cells[-1])
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
        return None

    out = []
    out.append("# 置信度按档对账报告（只读审计·数据截止本报告生成时刻）\n")
    out.append(f"- 台账：`{LOG_PATH}`")
    out.append(f"- 扫描区段：{len(sections_seen)} 个 · 九列但置信度格不可归档行（已计异常）：{unparsed_flag_rows}")
    out.append("- 口径：详表逐卡行计主账；批次 ×N 聚合行单列（batch·无逐卡复核）；「平行校验/预筛记录」区不计；童灵自动通过行不入质证分子")
    out.append("- 表头有效性：v1.1 起改**行级结构判据**（序号+ISO日期+卡号+9列schema）——v1.0 连续块纪律对本台账"
               "「表格行间空行」断表漏行（2026-10-08 实锤：代判回写9行不计数）；双盲审区头为陈旧容器不整区排除，其2列处置表由schema过滤")
    out.append("\n> **📌 口径勘误（2026-09-21·v1.0 立）**：此前对话引用「高98/中高148/中2」系 `grep '| 高 |'` 污染口径——232 行来自「三明治L3双盲审·价值层10卡抽检」评审矩阵表，非初审台账。本报告为结构性判据修正后的真实口径。**v1.1 追加勘误（2026-10-08）**：v1.0 的「真实口径」同时因断表而**严重少计**逐卡行（漏计方向与污染相反）——两错并陈，v1.1 行级判据为准。\n")
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
    print(f"[SANITY] 逐卡合计={total} · 批量×N合计={sum(s['batch_n'] for s in stats.values())} · 判据=v1.1行级（断表漏行已根治·区段排除防污染）")


if __name__ == "__main__":
    main()
