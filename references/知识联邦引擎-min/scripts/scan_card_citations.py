#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_card_citations.py — 新卡依据链引用自动登记 + 立场冲突检测

背景（2026-08-26 童灵执行·L1-L4 管道最优解方案）：
  L2→L3 通道依赖"引用入台账"，而碰撞卡依据链里天天产生真实引用（"（S829 已立：…）"
  式），从未被登记——引用不是稀缺的，登记的引用才稀缺。本脚本把引用登记自动化：
  每批碰撞卡产出后扫依据链 → 自动追加引用台账（幂等）→ derive_reading_status 派生 L3。
  同时检测新卡与既有 L3/L4 卡的立场冲突（反向循环守卫）。

用法：
  python3 scan_card_citations.py                      # 扫全部卡（增量：按 mtime 与台账比对）
  python3 scan_card_citations.py --cards 立场卡#S860-*.md   # 指定卡文件（可通配）
  python3 scan_card_citations.py --dry-run             # 只报告，不写台账
  python3 scan_card_citations.py --conflict-only       # 只跑冲突检测

幂等：按（被引卡号+引用来源卡号+日期）去重，重复运行不追加。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import os
import re
import sys
from datetime import date

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, AILIB_DIR
LEDGER_FILE = os.path.join(AILIB_DIR, "引用台账.md") if AILIB_DIR else None

# 引用语义词（依据链里"S0XX"出现且附近有这些词=真实引用）
REF_WORDS = ("已立", "同构", "呼应", "参见", "参照", "已有", "已综合", "覆盖", "见 ", "源自", "对应", "已裁定", "在案")
# 冲突语义词（主要矛盾/立场/推翻段里出现=立场冲突）
CONFLICT_WORDS = ("推翻", "反驳", "修正", "否定", "冲突", "不成立", "作废")


def load_ledger_keys():
    """读台账已有条目（卡号+上下文前20字）用于幂等"""
    keys = set()
    if not os.path.exists(LEDGER_FILE):
        return keys
    with open(LEDGER_FILE, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and "#S" in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 3 and cells[0].startswith("#S"):
                    keys.add((cells[0], cells[2][:20]))
    return keys


def extract_refs(card_path):
    """从卡片提取引用：返回 [(被引卡号, 上下文摘要)] 和 [(被引卡号, 冲突上下文)]"""
    with open(card_path, encoding="utf-8") as f:
        text = f.read()

    card_id_m = re.search(r"card_id:\s*(立场卡#S\d+)", text)
    card_id = card_id_m.group(1) if card_id_m else os.path.basename(card_path)

    refs = []
    conflicts = []

    # 依据链段：从"**依据链**"到下一段标题（带括号后缀，用前缀匹配）
    m = re.search(r"\*\*依据链\*\*(.*?)(?=\*\*让步合法条件|\*\*反方最强论证)", text, re.S)
    if m:
        chain = m.group(1)
        for line in chain.split("\n"):
            for m2 in re.finditer(r"S(\d{3,4})", line):
                s_id = f"#S{m2.group(1)}"
                if f"立场卡{s_id}" == card_id:
                    continue  # 自引跳过
                # 引用语义判定：行内含引用词 或 括号包裹
                if any(w in line for w in REF_WORDS):
                    ctx = line.strip()[:70]
                    refs.append((s_id, ctx))

    # 冲突检测段：主要矛盾/立场/推翻段
    for seg_name in ("主要矛盾", "立场（结论）", "推翻了我哪个旧认知"):
        m = re.search(rf"\*\*{seg_name}\*\*(.*?)(?=\*\*|$)", text, re.S)
        if m:
            seg = m.group(1)
            for m2 in re.finditer(r"S(\d{3,4})", seg):
                s_id = f"#S{m2.group(1)}"
                if f"立场卡{s_id}" == card_id:
                    continue
                # 行上下文含冲突词
                line_start = max(0, seg.rfind("\n", 0, m2.start()))
                line_end = seg.find("\n", m2.end())
                line = seg[line_start:line_end if line_end != -1 else len(seg)].strip()
                if any(w in line for w in CONFLICT_WORDS):
                    conflicts.append((s_id, line[:70]))

    return card_id, refs, conflicts


def append_ledger(entries):
    """追加台账行（幂等：卡号+摘要去重）"""
    existing = load_ledger_keys()
    today = date.today().isoformat()
    new_rows = []
    for s_id, ctx, cat in entries:
        key = (s_id, ctx[:20])
        if key in existing:
            continue
        # 摘要去引号（表格转义）
        ctx_clean = ctx.replace("|", "｜").replace('"', "'")
        new_rows.append(f"| {s_id} | {today} | {ctx_clean} | {cat} | {today} | AutoClaw 自动登记（扫描卡片依据链） | 依据链引用 |")  # v0.3 第7字段引用场景（2026-10-09 任务书#7）
        existing.add(key)
    if new_rows:
        with open(LEDGER_FILE, "a", encoding="utf-8") as f:
            f.write("\n".join(new_rows) + "\n")
    return len(new_rows)


def main():
    args = set(sys.argv[1:])
    dry_run = "--dry-run" in args
    conflict_only = "--conflict-only" in args

    if not INSTALLED or not AILIB_DIR:
        print("未安装态（记忆共享中心自推导失败）——跳过登记")
        return 0

    # 目标卡文件
    if "--cards" in args:
        idx = sys.argv.index("--cards")
        patterns = sys.argv[idx + 1:]
    else:
        patterns = [os.path.join(AILIB_DIR, "立场卡#S*.md")]

    files = []
    for p in patterns:
        files.extend(glob.glob(p))
    files = sorted(set(files))
    print(f"[scan_card_citations] 扫描 {len(files)} 张卡")

    all_refs = []    # (s_id, ctx)
    all_conflicts = []  # (s_id, ctx, source_card)
    for fp in files:
        card_id, refs, conflicts = extract_refs(fp)
        for s_id, ctx in refs:
            all_refs.append((s_id, ctx, card_id))
        for s_id, ctx in conflicts:
            all_conflicts.append((s_id, ctx, card_id))

    print(f"  依据链引用: {len(all_refs)} 条")
    for s_id, ctx, src in all_refs[:15]:
        print(f"    {s_id} ← {src}：{ctx[:50]}")

    if conflict_only:
        print(f"\n  ⚠️ 立场冲突信号: {len(all_conflicts)} 条")
        for s_id, ctx, src in all_conflicts:
            print(f"    {src} → 冲突 {s_id}：{ctx[:60]}")
        return 0

    if dry_run:
        print(f"\n[dry-run] 将登记 {len(all_refs)} 条引用（未写台账）")
        return 0

    entries = [(s_id, ctx, "依据型（AI引用）") for s_id, ctx, _ in all_refs]
    n = append_ledger(entries)
    print(f"\n✅ 已登记 {n} 条新引用（幂等去重）")
    if all_conflicts:
        print(f"⚠️ 冲突信号 {len(all_conflicts)} 条（已输出，待使用者复审）：")
        for s_id, ctx, src in all_conflicts:
            print(f"    {src} → {s_id}：{ctx[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
