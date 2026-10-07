#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
derive_reading_status.py — reading_status 事件派生脚本（质证回写管道根治方案·三期）
职责: 从卡片内「质证事件记录」机械派生 reading_status（L2 判定），更新 INDEX.md status 列。
      ⛔只读卡片+只写 INDEX.md；卡片 frontmatter 零改动（与 regen_ailib_index.py 同构）。
      ⛔只认明确模式，不猜——无法判定的标"待人工"。
      二期升级（2026-08-23·三明智L3评估后）：
        - 新增只升不降 rank 校验（防 S006 被错误降级）
        - 新增 L4 派生规则（引用≥3 且 至少1次用户决策引用 = 高置信内化）
      三期升级（2026-08-23·负反馈回路）：
        - 新增负反馈事件检测（应用失败/用户质疑/新反证）
        - 负反馈不自动降级，标记"待用户复审"（audit_recheck）
        - 用户确认后手动降级（保守设计：降级权归用户）

L2 判定规则（card-schema 原定义"用户质疑后卡片存活/修正"）:
  卡内存在 ≥1 个用户质证事件 → L2。
  用户质证事件模式（任一行匹配）:
    a) 「质证修正」「质证记录」上下文行中含「用户锤」或「用户宣告」或「用户拍板」
    b) 行内含「信息性反证生效」且行内含「用户」
    c) ⚠️ 未实现「用户质证/用户已质证」裸词识别——一次 dry-run 误升 764 张（误命中"待用户质证""用户质证/自动化断言"等描述性/待质证语境）。实际仅识别上方明确动作（用户锤/用户宣告/用户拍板/质证修正…用户/信息性反证…用户）及分身质通过等。如需以"用户质证"表达质证，请手标 frontmatter reading_status。
  ⛔「只接受一半」式 AI steelman 回应不构成用户质证事件（那是 AI 的回应段）。

用法:
  python3 derive_reading_status.py             # 全量派生+写 INDEX
  python3 derive_reading_status.py --dry-run   # 只报告，不写
  python3 derive_reading_status.py --ge-report  # 用户质证事件统计（选题反哺信号）
"""
import sys, os, re, glob
from datetime import datetime

from _paths import AILIB_DIR

INDEX_FILE = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None
LEDGER_FILE = os.path.join(AILIB_DIR, "引用台账.md") if AILIB_DIR else None

DRY_RUN = "--dry-run" in sys.argv

# 用户质证事件模式（保守·只认明确动作+质证上下文）
GE_PATTERNS = [
    re.compile(r"(?:用户|用户|我)锤"),                                    # 强：用户锤=质证打回动作
    re.compile(r"质证修正[^|]*(?:用户|用户|我)"),                          # 质证修正上下文含用户（修正由用户驱动）
    re.compile(r"(?:用户|用户|我)宣告"),                                   # 用户明示通过
    re.compile(r"(?:用户|用户|我)拍板[^|]*?(?:质证|L2|卡片)"),              # 用户拍板且与质证相关
    re.compile(r"信息性反证生效[^|]*(?:用户|用户|我)"),                     # 让步判据触发+用户同语境
    re.compile(r"分身质(?:证)?通过"),                         # 强：分身初审通过=代理用户质证（兼容"分身质通过/分身质证通过"两种写法）
    re.compile(r"分身宣告"),                                # 分身（分身）明示通过
    re.compile(r"分身初审[^|]*通过"),                         # 分身初审通过
    re.compile(r"分身[^|]*认可"),                            # 分身认可
]
# 分层终审「机制层自动通过」标记（2026-09-21 新增档）——用户 2026-09-08 授权：
#   低风险机制层/方法层 + 高置信度 → 分身自动通过（既非用户亲质证、也非 pending 待抽检）。
#   根治实证：该档缺失 → 14 张卡（S976-S990）被写成"待用户抽检" → 门禁判"认可未闭环"
#   → 9/20 转正体检记为尾债（伪债）。一档缺位，全链误判。
MECH_PASS_PATTERN = re.compile(r"机制层自动通过")
# 排除行（描述性引用·非事件记录）
EXCLUDE_PATTERN = re.compile(
    r"等用户质证|待用户质证|用户质证升级|待用户终审|终审交用户|"
    r"用户质证对话|用户质证记录|用户质证历史|用户质证反馈|"
    r"精细加工标记.*用户质证|"
    r"待分身质证|分身质证升级|分身.*待审核"
)

# 负反馈事件模式（三期新增）：检测到后标记"待用户复审"，不自动降级
# 触发条件：应用失败/用户质疑/新反证 → 降级权归用户（保守设计）
NF_PATTERNS = [
    re.compile(r"应用失败"),                                  # 立场被应用但决策失败
    re.compile(r"立场[^|]*已过时"),                           # 立场被新证据推翻
    re.compile(r"(?:用户|用户|我)质疑[^|]*降级"),                           # 用户明确要求降级
    re.compile(r"质证回退"),                                  # 质证结论：回退到低级
    re.compile(r"(?:用户|用户|我)宣告[^|]*降级"),                           # 用户宣告该立场不再适用
    re.compile(r"与[^|]*新证据矛盾"),                         # 新证据与立场矛盾
]
# 排除行（非负反馈）
NF_EXCLUDE_PATTERN = re.compile(
    r"等用户复审|待复审|复审中|复审记录"
)


def has_ge_event(text):
    """判定卡内是否存在用户质证事件（保守·只认明确动作+质证上下文）"""
    lines = text.split("\n")
    for line in lines:
        # 先过排除过滤器
        if EXCLUDE_PATTERN.search(line):
            continue
        for pat in GE_PATTERNS:
            if pat.search(line):
                return True, line.strip()[:80]
    return False, ""


def has_nf_event(text):
    """判定卡内是否存在负反馈事件（三期新增）
    返回 (是否负反馈, 证据行)
    负反馈不自动降级，仅标记待用户复审
    """
    lines = text.split("\n")
    for line in lines:
        if NF_EXCLUDE_PATTERN.search(line):
            continue
        for pat in NF_PATTERNS:
            if pat.search(line):
                return True, line.strip()[:80]
    return False, ""


def parse_index_table(text):
    """解析 INDEX 表格，返回行列表（保留原行文本）"""
    rows = []
    for line in text.split("\n"):
        if not line.startswith("| 立场卡") and not line.startswith("| 技能卡"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        rows.append({"raw": line, "cid": cells[0], "cells": cells})
    return rows


def load_ledger():
    """读引用台账，返回 {card_id: [分类列表]}"""
    ledger = {}
    if not os.path.exists(LEDGER_FILE):
        return ledger
    with open(LEDGER_FILE, encoding="utf-8") as f:
        for line in f:
            if not line.startswith("|") or "卡号" in line or "---" in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not cells[0].startswith("#S"):
                continue
            cid = "立场卡" + cells[0]
            cat = cells[3]
            ledger.setdefault(cid, []).append(cat)
    return ledger


def derive_status(card_text):
    """从卡内质证事件派生 status（v1.4·2026-08-23 用户纠正标签虚报）

    标签必须如实区分质证主体：用户亲质证 vs 分身质通过。
    分身质通过 ≠ 用户已质证——把分身代批标成"用户已质证"=虚报用户的动作。
    """
    found, evid = has_ge_event(text=card_text)
    if found:
        # 区分质证主体：用户亲质证（用户锤/用户宣告/用户拍板）vs 分身质通过
        # ⛔ 排除「依据链/来源卡」行——那里的用户拍板/用户宣告是描述权威来源，
        #    不是本次质证事件（2026-09-11 S995/S999 来源标注误升实证）
        SOURCE_LINE_MARK = ("- 权威", "- 推理", "- 反例", "来源卡", "source_", "依据链")
        ge_personal = False
        for line in card_text.split("\n"):
            if line.startswith(SOURCE_LINE_MARK):
                continue
            for p in [
                re.compile(r"(?:用户|用户|我)锤"), re.compile(r"(?:用户|用户|我)宣告"),
                re.compile(r"(?:用户|用户|我)拍板"), re.compile(r"质证修正[^|]*(?:用户|用户|我)"),
                re.compile(r"信息性反证生效[^|]*(?:用户|用户|我)"),
            ]:
                if p.search(line):
                    ge_personal = True
                    break
            if ge_personal:
                break
        if ge_personal:
            return "L2（用户已质证）", evid
        # 机制层自动通过（用户 09-08 分层终审授权）——优先于 pending 标签：
        #   不冒充用户亲质证、也不制造"待用户抽检"假债。
        for line in card_text.split("\n"):
            if MECH_PASS_PATTERN.search(line):
                return "L2（机制层自动通过·用户09-08授权）", line.strip()[:80]
        return "L2（分身已质证·待用户抽检）", evid
    return None, ""  # 无事件 → 不改变（保持现 status）


# 只升不降：status 阶梯 rank（L1 < L2 < L3 < L4）
STATUS_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}


def status_rank(status_str):
    """从 status 字符串提取 rank（未知=0）"""
    for k, v in STATUS_RANK.items():
        if status_str.startswith(k):
            return v
    return 0


def derive_upper_status(cid, ledger, card_text):
    """从引用台账派生 L3/L4（升级后：多维信号）
    规则（2026-09-11 修正·AI依据不再升L3）：
      - L3 = 用户决策引用≥1（用户真实决策引用=已应用唯一高置信信号）
      - L4 = 用户决策引用≥3（高置信内化证据）
      - ⛔ AI 依据引用（AutoClaw 自动登记）不再触发 L3/L4 升格——
        它是"AI 工作时引用过这张卡"，不是"用户已认可"。
        根因：2026-09-11 实测全库 137 张 L3 卡中 135 张仅有 AI 依据引用，
        与进度表语义"L3=用户已认可·已应用"冲突（S838/S842/S866/S886/S897 误标实证）。
        上轮（2026-09-11）门禁 REVIEW_MARKERS 已补 L3/L4 作兼容，本修正为规则根治。
    """
    cats = ledger.get(cid, [])
    ge_decisions = [c for c in cats if "用户决策引用" in c]
    ai_basis = [c for c in cats if "依据型" in c and "用户决策" not in c]
    total_ge = len(ge_decisions)

    # L4: 用户决策引用≥2（高置信内化证据）
    if total_ge >= 2:
        return "L4（已内化）", f"引用台账：用户决策×{total_ge}（≥2次用户决策引用=高置信内化）"
    # L3: 用户决策引用≥1（用户真实采纳）
    if total_ge >= 1:
        return "L3（已应用）", f"引用台账：用户决策引用×{total_ge}"
    return None, ""


def ge_report():
    """用户质证事件统计（选题反哺信号·三期）"""
    cards = {}
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "*.md"))):
        base = os.path.basename(p)
        if base == "INDEX.md" or not (base.startswith("立场卡") or base.startswith("技能卡")):
            continue
        with open(p, encoding="utf-8") as f:
            cards[base] = f.read()
    events = []
    for base, text in cards.items():
        found, evid = has_ge_event(text)
        if found:
            # 提取锤点/宣告主题
            m = re.search(r"用户锤[^）]*[“\"]([^”\"]+)", text) or re.search(r"用户宣告[^）]*", text)
            topic = m.group(0)[:60] if m else evid
            events.append((base.split("-")[0], topic))
    print(f"🔨 用户质证事件统计: {len(events)} 张卡")
    for cid, topic in events:
        print(f"   {cid}: {topic}")
    return 0


def main():
    if "--ge-report" in sys.argv:
        return ge_report()
    cards = {}
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "*.md"))):
        base = os.path.basename(p)
        if base == "INDEX.md" or not (base.startswith("立场卡") or base.startswith("技能卡")):
            continue
        with open(p, encoding="utf-8") as f:
            cards[base] = f.read()

    with open(INDEX_FILE, encoding="utf-8") as f:
        index_text = f.read()

    rows = parse_index_table(index_text)
    ledger = load_ledger()
    changes = []
    audit = []  # 有质证段但无用户事件的卡（待人工关注）
    nf_audit = []  # 负反馈标记（三期新增）：待用户复审降级

    for row in rows:
        cid = row["cid"]
        # 卡文件名 = cid-主题.md，匹配目录里的文件
        card_text = None
        for base, text in cards.items():
            if base.startswith(cid + "-") or base.startswith(cid + "."):
                card_text = text
                break
        if card_text is None:
            continue
        cur = row["cells"][4] if len(row["cells"]) > 4 else ""
        cur_rank = status_rank(cur)
        # 优先级：L3/L4（台账派生） > L2（质证事件派生）
        upper, upper_evid = derive_upper_status(cid, ledger, card_text)
        if upper and status_rank(upper) > cur_rank:
            changes.append((cid, cur, upper, upper_evid))
            continue
        new_status, evid = derive_status(card_text)
        # 只升不降：status rank 必须更高才应用；但标签虚报修正（同rank不同主体标签）也须纠正
        if new_status and (status_rank(new_status) > cur_rank or (new_status != cur and status_rank(new_status) == cur_rank)):
            changes.append((cid, cur, new_status, evid))
        # 有质证上下文但无用户事件 → 审计提示
        elif not new_status and ("质证修正" in card_text or "质证记录" in card_text):
            if "用户锤" not in card_text and "用户宣告" not in card_text and "用户拍板" not in card_text:
                audit.append(cid)
        # 负反馈检测（三期新增）：标记待用户复审
        nf_found, nf_evid = has_nf_event(card_text)
        if nf_found and cur_rank >= 3:
            nf_audit.append((cid, cur, nf_evid))

    print(f"📚 扫描卡片: {len(cards)} 张 | INDEX 行: {len(rows)} 行 | 台账条目: {sum(len(v) for v in ledger.values())} 条")
    print(f"🔧 派生变更: {len(changes)} 张")
    for cid, cur, new, evid in changes:
        print(f"   {cid}: {cur} → {new}")
        print(f"      证据: {evid}")
    print(f"👁️  有质证段但无用户事件（保持现状态）: {len(audit)} 张")
    for cid in audit:
        print(f"   - {cid}")
    print(f"⚠️  负反馈标记（待用户复审·不自动降级）: {len(nf_audit)} 张")
    for cid, cur, nf_evid in nf_audit:
        print(f"   - {cid} [{cur}]: {nf_evid}")

    if DRY_RUN:
        print("ℹ️  dry-run 模式：不写入 INDEX")
        return 0

    if changes:
        new_text = index_text
        for cid, cur, new, evid in changes:
            # 更新该行的 status 列（第6列）
            pattern = re.compile(r"^(\| " + re.escape(cid) + r" \|.*?\n)", re.M)
            for m in pattern.finditer(new_text):
                line = m.group(1)
                cells = line.strip().strip("|").split("|")
                cells = [c.strip() for c in cells]
                if len(cells) >= 5 and cells[4] != new:
                    cells[4] = new
                    new_line = "| " + " | ".join(cells) + " |\n"
                    new_text = new_text.replace(line, new_line, 1)
                    break
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"✅ INDEX.md 已更新（{len(changes)} 处 status 派生写入）")
    else:
        print("✅ 无变更（所有卡 status 已与事件记录一致）")
    return 0


if __name__ == "__main__":
    from _paths import INSTALLED
    if not INSTALLED:
        print("❌ 未安装态：请先完成安装（需 [记忆共享中心]/脚本中心 布局）")
        sys.exit(1)
    sys.exit(main())
