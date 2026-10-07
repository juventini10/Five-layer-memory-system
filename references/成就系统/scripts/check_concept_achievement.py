#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_concept_achievement.py — 概念碰撞成就 · 幂等检测器

数据源: [记忆共享中心]/知识库/AI学习库/INDEX.md 碰撞来源列 `[C-X × C-Y]`
产出:
  1) 计算 X(立场卡数) / Y(已碰撞不同概念卡数) / 全集 / 缺口
  2) 对照四阶里程碑(铜/银/金/钻 · 10万封顶)，更新 概念碰撞成就.md 的 STATE + LOG 段
  3) 新跨里程碑 → 重写 SEAL + 写 最伟大的我/成就证据/{date}-concept_{thr}.md + 宣告解锁
设计(对齐 记忆蓝图/02_设计理念/成就系统设计哲学.md v1.2):
  - §3.3 指数/加速阈值 + 四阶等级(铜1-99每~10 / 银100-999每~100 / 金1000+每~1000尾部稀疏 / 钻特殊里程碑)
  - §3.5 幂等：LOG 段已解锁去重，不重复触发
  - §3.6 单向联动：成就系统 → 最伟大的我(只写不读)
  - §3.1 检测不激励：只检测记录，无任何推送催促
用法:
  python3 check_concept_achievement.py            # 检测 + 更新
  python3 check_concept_achievement.py --status   # 仅打印，不写文件
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import hashlib
from datetime import datetime

HOME = os.path.expanduser("~")
INDEX = os.path.join(HOME, "[记忆共享中心]", "知识库", "AI学习库", "INDEX.md")
CONCEPT_DIR = os.path.join(HOME, "[日记仓库]", "2-知识库", "08-概念层")
ACH_FILE = os.path.join(os.path.expanduser("[记忆共享中心]"), "成就系统", "概念碰撞成就.md")
EVIDENCE_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "最伟大的我", "成就证据")
SEAL_SALT = "concept-achievement-seal-v1"

# 四阶里程碑（Y=已碰撞不同概念卡数；对齐成就哲学 §3.3 指数/加速阈值，10万封顶）
# (阈值, 名称, 等级)
MILESTONES = [
    (10, "🌱 概念萌芽", "🟢 铜牌"),
    (20, "🌿 概念新芽", "🟢 铜牌"),
    (30, "🌳 概念成林", "🟢 铜牌"),
    (40, "🍀 概念初网", "🟢 铜牌"),
    (50, "🌴 概念小径", "🟢 铜牌"),
    (60, "🍃 概念织网", "🟢 铜牌"),
    (70, "🌲 概念之森", "🟢 铜牌"),
    (80, "🏞 概念原野", "🟢 铜牌"),
    (90, "🌄 概念大地", "🟢 铜牌"),
    (100, "🕸 概念百联", "🥈 银牌"),
    (200, "🗺 概念联网", "🥈 银牌"),
    (300, "⭐ 概念星图", "🥈 银牌"),
    (400, "🌌 概念星云", "🥈 银牌"),
    (500, "🌠 概念星海", "🥈 银牌"),
    (600, "🌃 概念星河", "🥈 银牌"),
    (700, "🛰 概念星域", "🥈 银牌"),
    (800, "🔭 概念星系", "🥈 银牌"),
    (900, "🌌 概念星穹", "🥈 银牌"),
    (1000, "🌟 概念宇宙", "🥇 金牌"),
    (2000, "✨ 概念多重宇宙", "🥇 金牌"),
    (3000, "🪐 概念维度", "🥇 金牌"),
    (5000, "🔮 概念奇点", "🥇 金牌"),
    (7000, "⚛️ 概念引力", "🥇 金牌"),
    (9000, "☄️ 概念时空", "🥇 金牌"),
    (10000, "💎 概念万物", "💎 钻石"),
    (50000, "💎 概念星海", "💎 钻石"),
    (100000, "💎 概念之巅", "💎 钻石"),
]


def compute():
    """抽 INDEX.md 碰撞来源列 → X(有碰撞记录的卡数), Y(参与碰撞的不同概念数), total, gap, all_cards。"""
    x = 0
    all_cards = 0
    concepts = set()
    if os.path.exists(INDEX):
        for line in open(INDEX, encoding="utf-8"):
            if not (line.startswith("| 立场卡") or line.startswith("| 技能卡")):
                continue
            all_cards += 1
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 6:
                continue
            src = cells[-1]
            m = re.search(r"\[(C-[0-9]+)\s*[×x]\s*(C-[0-9]+)\]", src)
            if m:
                x += 1
                concepts.add(m.group(1))
                concepts.add(m.group(2))
    total = 0
    if os.path.isdir(CONCEPT_DIR):
        total = len([f for f in os.listdir(CONCEPT_DIR)
                     if f.startswith("C-") and f.endswith(".md")])
    y = len(concepts)
    gap = total - y
    return x, y, total, gap, all_cards


def current_milestone(y):
    reached = [name for thr, name, _ in MILESTONES if y >= thr]
    return reached[-1] if reached else "未达成"


def next_milestone(y):
    for thr, name, _ in MILESTONES:
        if y < thr:
            return thr, name
    return None, None


def compute_seal(date_only, y, x, gap, cm):
    seed = f"{date_only}|Y={y}|X={x}|gap={gap}|milestone={cm}|{SEAL_SALT}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def read_prev_block():
    if not os.path.exists(ACH_FILE):
        return None
    txt = open(ACH_FILE, encoding="utf-8").read()
    m = re.search(r"<!-- CONCEPT_ACH_STATE -->(.*?)<!-- /CONCEPT_ACH_STATE -->",
                  txt, re.S)
    return m.group(1) if m else None


def parse_field(block, label):
    if not block:
        return None
    m = re.search(rf"{label}\s*\|\s*([^\|\n]+?)\s*\|", block)
    return m.group(1).strip() if m else None


def read_unlocked():
    """从 LOG 段解析已解锁阈值集合（幂等去重依据）。"""
    if not os.path.exists(ACH_FILE):
        return set()
    txt = open(ACH_FILE, encoding="utf-8").read()
    m = re.search(r"<!-- CONCEPT_ACH_LOG -->(.*?)<!-- /CONCEPT_ACH_LOG -->",
                  txt, re.S)
    if not m:
        return set()
    return {int(t) for t in re.findall(r"\((\d+)\)\s*\|", m.group(1))}


def render_state_block(y, x, total, gap, cm, date_str, seal, all_cards=0):
    coverage = f"{y/total*100:.1f}%" if total > 0 else "N/A"
    collision_rate = f"{x/all_cards*100:.1f}%" if all_cards > 0 else "N/A"
    return (
        "| 指标 | 数值 | 说明 |\n"
        "|------|------|------|\n"
        f"| 参与碰撞的不同概念数 (Y) | {y} | 主度量·概念覆盖率={coverage}（非碰撞次数） |\n"
        f"| 有碰撞记录的立场卡/技能卡数 (X) | {x} | 副度量·占总卡数{collision_rate} |\n"
        f"| 立场卡/技能卡总数 | {all_cards} | INDEX.md总行数 |\n"
        f"| 概念卡全集 | {total} | 持续抽取，无上限 |\n"
        f"| 未参与碰撞概念数 | {gap} | 已抽未碰的概念数 |\n"
        f"| 当前里程碑 | {cm} | 见里程碑表 |\n"
        f"| 最后更新 | {date_str} | 来源：check_concept_achievement.py |\n"
        f"| SEAL | {date_str}:{seal} | 物理签名·篡改即失效 |\n"
    )


def write_evidence(thr, name, level, y, date_only):
    """§3.6 单向联动：新成就 → 写最伟大的我/成就证据/{date}-concept_{thr}.md。"""
    if not os.path.isdir(EVIDENCE_DIR):
        return
    path = os.path.join(EVIDENCE_DIR, f"{date_only}-concept_{thr}.md")
    if os.path.exists(path):
        return  # 幂等：已存在则跳过
    content = (
        f"# 成就证据 · {name}\n\n"
        f"- **达成日期**：{date_only}\n"
        f"- **成就ID**：concept_{thr}\n"
        f"- **等级**：{level}\n"
        f"- **达成值**：{y}\n"
        f"- **来源**：成就系统自动检测（概念碰撞成就线）\n\n"
        "---\n\n"
        f"{name}\n\n"
        "> 由 `check_concept_achievement.py` 自动写入最伟大的我·成就证据\n"
    )
    open(path, "w", encoding="utf-8").write(content)


def main():
    status_only = "--status" in sys.argv
    x, y, total, gap, all_cards = compute()
    now = datetime.now()
    date_only = now.strftime("%Y-%m-%d")
    date_str = now.strftime("%Y-%m-%d %H:%M")
    cm = current_milestone(y)
    nthr, nname = next_milestone(y)
    seal = compute_seal(date_only, y, x, gap, cm)

    reached = [m for m in MILESTONES if y >= m[0]]
    unlocked = read_unlocked()
    new_ones = [m for m in reached if m[0] not in unlocked]

    # 数据自解释输出（v2.0·根治字段歧义：2026-09-01 AI误读"已碰撞78"为碰撞次数）
    coverage = f"{y/total*100:.1f}%" if total > 0 else "N/A"
    collision_rate = f"{x/all_cards*100:.1f}%" if all_cards > 0 else "N/A"
    print(f"[概念碰撞健康] 立场卡/技能卡总数={all_cards} | 有碰撞记录的卡={x}（占比{collision_rate}）| 概念卡总数={total} | 参与碰撞的不同概念={y}（覆盖率{coverage}）| 未参与碰撞概念={gap}")
    print(f"当前里程碑: {cm}" + (f"  (下一站: {nname}@{nthr}，差{nthr - y})"
                                 if nthr else "  (已满级)"))
    print(f"SEAL: {date_str}:{seal}")

    if status_only:
        print("[--status] 未写文件")
        return 0

    if not os.path.exists(ACH_FILE):
        print(f"ERR 成就文件不存在: {ACH_FILE}")
        return 1

    txt = open(ACH_FILE, encoding="utf-8").read()

    # 新解锁：追加 LOG 行 + 写最伟大的我 + 宣告
    if new_ones:
        rows = "".join(
            f"| {name}({thr}) | {date_only} | {y} | {'初始存量追溯' if thr <= 100 else '碰撞解锁'} |\n"
            for thr, name, _ in new_ones
        )
        if re.search(r"<!-- CONCEPT_ACH_LOG -->.*?<!-- /CONCEPT_ACH_LOG -->",
                     txt, re.S):
            txt = re.sub(
                r"(<!-- CONCEPT_ACH_LOG -->\n)",
                r"\1" + rows, txt, count=1)
        else:
            txt = txt.rstrip() + "\n\n## 📅 里程碑记录\n\n<!-- CONCEPT_ACH_LOG -->\n" \
                + rows + "<!-- /CONCEPT_ACH_LOG -->\n"
        for thr, name, level in new_ones:
            write_evidence(thr, name, level, y, date_only)
        for thr, name, _ in new_ones:
            print(f"🏆 解锁新里程碑: {name} (Y={y})")

    new_block = ("<!-- CONCEPT_ACH_STATE -->\n"
                 + render_state_block(y, x, total, gap, cm, date_str, seal, all_cards)
                 + "<!-- /CONCEPT_ACH_STATE -->")
    prev_block = read_prev_block()
    if prev_block == new_block and not new_ones:
        print("无变化，跳过重写（幂等）")
        return 0

    txt = re.sub(r"<!-- CONCEPT_ACH_STATE -->.*?<!-- /CONCEPT_ACH_STATE -->",
                 new_block, txt, flags=re.S)
    open(ACH_FILE, "w", encoding="utf-8").write(txt)
    print("状态已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
