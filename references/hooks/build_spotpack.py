#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# build_spotpack.py v1.1 — 童灵抽检包生成器（校准飞轮补燃料·工序端机械封装）
# 创建: 2026-10-08 (Qoder CN·校准飞轮第二圈补燃料 T3)
# v1.1: 2026-10-08 (豆包办公·K007融入飞轮 T11-3)——新增「合并操作抽查」分层：
#   扫描 AI学习库/合并台账.md 的"确认人=童灵"行，作为抽检包额外section（童灵合并的
#   卡是否正确？主卡是否保留次卡精华？）。合并台账不存在=该分层静默跳过（不影响
#   现有卡片抽检功能·向后兼容）。数据真源=去重/融合机制#8合并台账（9字段Markdown表格）。
#
# 职责（工序可代·判据不可代·02§一法理裁决）:
#   分层抽 N 张「待你抽检」卡 + 台账原文转录 + 机械预筛信号 + 复核栏生成 → 抽检包.md
#   ⛔ 本脚本不做语义判断：「建议你重点看」列只输出机械信号（含⚠️提请/升级非空/久候天数），
#      语义预筛/判词由童灵会话补写，认/翻的参照系永远是你（防 S006 全绿幻觉）。
# 分层口径（对齐第1期·20261008 手工包；行级判据同 gray_release_stats，
#   台账表格行间有空行→连续块纪律断表，2026-10-08 实测根因改用行级结构）:
#   ①档覆盖：按置信度档分层，高/中高各保底 MIN_PER_PRIMARY 张
#   ②日期散布：贪心优先未用过的日期，覆盖 ≥min(n, 日期桶数) 个日期
#   ③未决项：≥1 张带 ⚠️/提请 信号的卡（若池中存在）
#   ④平行校验区不计（口径同 confidence_calibration_audit / gray_release_stats）
# 可回溯性: 每张样本登记台账源行号（footer 索引，验收判据"行号可回溯台账原文"）。
# 只读台账；包文件落 steps/抽检包-YYYYMMDD.md，已存在则自动 -v2 递增，⛔不覆盖。
# 用法: python3 build_spotpack.py [--n 10] [--out PATH] [--seed SEED]

try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import os
import random
import re
import sys
from datetime import date, datetime
from pathlib import Path


def _base_dir() -> Path:
    env = os.environ.get("DIGITALTWIN_HOME")
    return Path(env).expanduser() if env else Path('[记忆共享中心]') / "数字分身"


TIERS = ("中高", "高", "中", "低")  # 匹配顺序：中高 必须先于 高/中（同 calibration）
PRIMARY_TIERS = ("高", "中高")
MIN_PER_PRIMARY = 3
PENDING_MARK = "待你抽检"
EXCLUDE_SECTION_KEY = "平行校验"
MERGE_LEDGER = Path.home() / "[记忆共享中心]" / "知识库" / "AI学习库" / "合并台账.md"  # v1.1 合并操作抽查数据真源（去重/融合机制#8）
MAX_MERGE_SAMPLES = 3  # v1.1 合并操作抽查最大样本数（避免挤占卡片抽检预算）


def parse_tier(cell: str) -> str | None:
    c = cell.strip().replace("🟢", "").replace("🟡", "").strip()
    for t in TIERS:
        if c.startswith(t):
            return t
    return None


def scan_pending(ledger: Path) -> list[dict]:
    """行级结构判据扫描（对齐 gray_release_stats.parse_review：台账表格行间有空行，
    连续块纪律会断表——2026-10-08 实测根因；改走行级正则+9列schema+卡号形态守卫）。
    假阳性隔离：平行校验区不计；双盲审处置表因末列非「待你抽检」自然过滤。"""
    rows: list[dict] = []
    section = ""
    for lineno, raw in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if EXCLUDE_SECTION_KEY in section:
            continue
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*([A-Za-z]+\d+)\s*\|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 9 or not cells[-1].startswith(PENDING_MARK):
            continue
        try:
            d = datetime.strptime(m.group(2), "%Y-%m-%d").date()
        except ValueError:
            continue
        rows.append({
            "line": lineno, "date": d, "card": m.group(3),
            "tier": parse_tier(cells[4]),
            "verdict": cells[5], "escalate": cells[7],
        })
    return rows


def scan_merge_operations() -> list[dict]:
    """v1.1 扫描合并台账，找"确认人=童灵"的合并操作（童灵做的判定，需你抽查）。
    合并台账格式=去重/融合机制#8定义的9字段Markdown表格：
    | 合并ID | 日期 | 主卡号 | 次卡号 | 合并原因 | 确认人 | 主卡版本变化 | 次卡归档路径 | 备注 |
    split("|")后索引：0='' 1=合并ID 2=日期 3=主卡 4=次卡 5=原因 6=确认人 7=主卡版本 8=次卡归档 9=备注 10=''
    合并台账不存在=返回空列表（该分层静默跳过·不影响现有功能·向后兼容）。"""
    if not MERGE_LEDGER.exists():
        return []
    ops: list[dict] = []
    for lineno, raw in enumerate(MERGE_LEDGER.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        if cells[0] == "合并ID" or cells[5] == "确认人":  # 跳过表头
            continue
        if cells[5] != "童灵":  # 只抽童灵判定的（你确认的不需要再抽查）
            continue
        try:
            d = datetime.strptime(cells[1], "%Y-%m-%d").date()
        except ValueError:
            continue
        ops.append({
            "line": lineno, "merge_id": cells[0], "date": d,
            "primary": cells[2], "secondary": cells[3],
            "reason": cells[4], "version_change": cells[6] if len(cells) > 6 else "",
        })
    return ops


def mech_signals(row: dict, today: date) -> str:
    sig = []
    v = row["verdict"]
    if "⚠️" in v or "提请" in v:
        sig.append("含⚠️/提请项")
    esc = row["escalate"]
    if esc and esc not in ("无", "-", "—") and not esc.startswith("无"):
        sig.append(f"升级声明非空({esc[:12]}…)" if len(esc) > 12 else f"升级声明非空({esc})")
    wait = (today - row["date"]).days
    sig.append(f"久候{wait}天")
    return "·".join(sig)


def stratified_sample(rows: list[dict], n: int, rng: random.Random) -> list[dict]:
    """①未决项保底1 ②高/中高各保底 ③档内按日期散布贪心 ④余量按池占比轮询补齐。"""
    pool = [r for r in rows if r["tier"]]
    picked: list[dict] = []
    used_dates: set = set()

    def take(cands: list[dict]) -> dict | None:
        if not cands:
            return None
        spread = [r for r in cands if r["date"] not in used_dates]
        chosen = rng.choice(spread if spread else cands)
        picked.append(chosen)
        cands.remove(chosen)
        used_dates.add(chosen["date"])
        return chosen

    # ③未决项槽（全池优先带⚠️/提请的档内卡）
    flagged = [r for r in pool if ("⚠️" in r["verdict"] or "提请" in r["verdict"])
               and r["tier"] in PRIMARY_TIERS]
    if flagged and n > 0:
        take(flagged)

    # ①高/中高保底
    for t in PRIMARY_TIERS:
        cands = [r for r in pool if r["tier"] == t and r not in picked]
        for _ in range(min(MIN_PER_PRIMARY, n - len(picked))):
            if not take(cands):
                break

    # ④余量：剩余池按档轮询（档大小降序），日期散布
    remaining = {t: [r for r in pool if r["tier"] == t and r not in picked]
                 for t in TIERS}
    while len(picked) < n and any(remaining.values()):
        for t in TIERS:
            if len(picked) >= n:
                break
            take(remaining[t])
    return picked[:n]


def build_pack(rows: list[dict], n: int, seed: str, today: date, out: Path, base: Path, merge_ops: list[dict] | None = None) -> Path:
    rng = random.Random(seed)
    samples = stratified_sample(rows, n, rng)
    if not samples:
        print("[FAIL] 抽样结果为空——池里没有可抽的待抽检卡，拒绝出空包（铁律-021）")
        sys.exit(2)

    path = out
    v = 2
    while path.exists():
        path = out.with_name(f"{out.stem}-v{v}{out.suffix}")
        v += 1

    dates_cov = len({r["date"] for r in samples})
    tiers_cov = sorted({r["tier"] for r in samples if r["tier"]})
    lines = []
    lines.append(f"# 童灵抽检包 · 生成日 {today.isoformat()}（种子 {seed}）\n")
    lines.append("> **用途**：给校准飞轮补燃料。你的动作=每张只做一个二元选择：**✅认可 / ❌推翻**（推翻须一句理由，那句理由就是反向训练数据）。")
    lines.append("> **口径**：认可/推翻回写本文件后，按回写规则同步 step3 台账；calibration-audit 的「你复核」n 即计入；累计 n≥20 的档位触发校准判定。")
    lines.append(f"> **预筛签名**：本包 {len(samples)} 张由 `build_spotpack.py` 机械分层抽取（档覆盖 {'/'.join(tiers_cov)} · 日期覆盖 {dates_cov} 个点 · 未决项槽={'有' if any('⚠️' in r['verdict'] or '提请' in r['verdict'] for r in samples) else '池内无'}）。机械预筛≠语义预筛——童灵代工序（筛卡/转录/机检），不代判据（认/翻只能是你）。")
    lines.append("")
    lines.append("| # | 卡 | 日期·档 | 台账裁决摘要（原文转录） | 机械预筛信号 | 你复核 |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(samples, 1):
        vd = r["verdict"].replace("|", "\\|")
        lines.append(f"| {i} | {r['card']} | {r['date'].isoformat()}·{r['tier']} | {vd} | {mech_signals(r, today)} | ☐ |")
    lines.append("")

    # v1.1 合并操作抽查section（童灵做的合并判定·需你抽查·合并台账不存在时跳过）
    if merge_ops:
        merge_samples = sorted(merge_ops, key=lambda x: x["date"], reverse=True)[:MAX_MERGE_SAMPLES]
        lines.append(f"## 合并操作抽查（童灵判定·共{len(merge_ops)}笔·抽最近{len(merge_samples)}笔交你复核）\n")
        lines.append("> **用途**：童灵在去重/融合验收中做的合并判定，你抽查是否正确（主卡是否保留了次卡精华？次卡是否应该被合并？）。✅=合并正确 / ❌=合并有误（须一句理由→回滚+反哺童灵判定标准）。")
        lines.append("")
        lines.append("| # | 合并ID | 日期 | 主卡 | 次卡 | 合并原因 | 主卡版本变化 | 你复核 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for i, op in enumerate(merge_samples, 1):
            reason = op["reason"].replace("|", "\\|")[:60]
            lines.append(f"| {i} | {op['merge_id']} | {op['date'].isoformat()} | {op['primary']} | {op['secondary']} | {reason} | {op['version_change']} | ☐ |")
        lines.append("")
        lines.append("## 合并操作回写规则\n")
        lines.append("- ✅合并正确 → 合并台账该行「确认人」从「童灵」改为「你」（你抽查确认）。")
        lines.append("- ❌合并有误 + 理由 → 触发回滚流程（任务书§八①：主卡恢复合并前版本+次卡从归档移回AI学习库），理由进反向训练数据（反哺童灵验收判定标准）。")
        lines.append("")

    lines.append("## 回写规则（复盘时对账用）\n")
    lines.append("- ✅认可 → 在 `step3-first-review-log.md` 把该行状态改「你已复核（日期）」，calibration 覆盖 n +1。")
    lines.append("- ❌推翻 + 理由 → 理由原文进反向训练数据队列（下次蒸馏轮消化，规格书增量须绑此实录），台账记「推翻」。")
    lines.append("- 本包看完即弃卡不追改——推翻的卡走蒸馏，不手改判词（防\"推翻只记录不反喂\"反模式，02§七）。")
    lines.append("")
    lines.append("## 溯源索引（台账行号·可回溯原文）\n")
    for i, r in enumerate(samples, 1):
        lines.append(f"- {i}. {r['card']} ← `step3-first-review-log.md:L{r['line']}`")
    lines.append("")
    merge_info = f" · 合并操作={len(merge_ops)}笔（童灵判定）" if merge_ops else ""
    lines.append(f"*生成：build_spotpack.py v1.1 · {today.isoformat()} · 样本池={len(rows)}张待你抽检{merge_info} · 台账=`{base/'steps/step3-first-review-log.md'}`*")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="童灵抽检包生成器（只读台账·分层抽样出包）")
    ap.add_argument("--n", type=int, default=10, help="抽样张数（默认10·你10分钟预算）")
    ap.add_argument("--out", type=str, default=None, help="输出路径（默认 steps/抽检包-YYYYMMDD.md）")
    ap.add_argument("--seed", type=str, default=None, help="随机种子（默认=当日日期，逐日不同样本）")
    args = ap.parse_args()

    base = _base_dir()
    ledger = base / "steps" / "step3-first-review-log.md"
    if not ledger.exists():
        print(f"[FAIL] 台账不存在: {ledger}")
        return 1
    today = date.today()
    seed = args.seed or today.isoformat()
    out = Path(args.out).expanduser() if args.out else base / "steps" / f"抽检包-{today.strftime('%Y%m%d')}.md"

    rows = scan_pending(ledger)
    print(f"[POOL] 待你抽检池 = {len(rows)} 张（行级判据：序号+ISO日期+卡号形态+9列+末列待你抽检 · 平行区不计）")
    if not rows:
        print("[FAIL] 池为空——无积压可抽，不出包")
        return 2
    merge_ops = scan_merge_operations()  # v1.1 合并操作抽查（合并台账不存在时返回空列表·静默跳过）
    if merge_ops:
        print(f"[MERGE] 合并操作池 = {len(merge_ops)} 笔（童灵判定·抽最近{min(MAX_MERGE_SAMPLES, len(merge_ops))}笔入包）")
    pack = build_pack(rows, args.n, seed, today, out, base, merge_ops=merge_ops)
    print(f"[OK] 抽检包已生成: {pack}")
    print(f"[SANITY] 抽样 {args.n if args.n <= len(rows) else len(rows)} 张 · 种子 {seed} · 溯源行号见包尾索引")
    return 0


if __name__ == "__main__":
    sys.exit(main())
