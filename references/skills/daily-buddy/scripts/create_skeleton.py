#!/usr/bin/env python3
"""
create_skeleton.py — 日记骨架生成器 + 灵感闪现注入

用法：
  # 推荐：自动写盘（幂等——文件已存在则跳过）
  python3 create_skeleton.py --date 2026-07-03 --out ~/Local_Obsidian_Vault/.../2026-07-03.md

  # 兼容旧用法：stdout 输出（供 AI 手动 Write）
  python3 create_skeleton.py --date 2026-07-03

功能：
  1. 生成完整的日记骨架 Markdown
  2. 自动读取昨日日记 → 提取关键词 → 匹配核心启发库（无个人库则回退随包 daily_quotes_cache.json 名言池）→ 注入灵感闪现行
  3. --out 模式：Python 直接写盘（幂等），AI 只跑一条命令；不传 --out 则 stdout 兼容旧用法

输出：完整的日记骨架，AI 拿到后只能填充待填字段（目标/感悟/决策/总结），禁止手写 day_of_week。
"""

import argparse
import datetime
import sys
import os
import re
import json
import hashlib
from pathlib import Path


# === 路径常量 ===
DIARY_BASE = Path(os.path.expanduser(
    "~/Local_Obsidian_Vault/1-每日计划/01-日记"
))
INSPIRATION_LIB = Path(os.path.expanduser(
    "~/Local_Obsidian_Vault/2-知识库/01-读书笔记/核心启发库.md"
))
SCRIPT_DIR = Path(__file__).resolve().parent
INSPIRATION_CACHE = SCRIPT_DIR / "daily_quotes_cache.json"


def weekday_cn(d: datetime.date) -> str:
    """返回中文星期，如 '周一'"""
    return '周' + '一二三四五六日'[d.weekday()]


def is_monday(d: datetime.date) -> bool:
    return d.weekday() == 0


def is_first_of_month(d: datetime.date) -> bool:
    return d.day == 1


def diary_path_for_date(d: datetime.date) -> Path:
    """返回日记文件路径：.../YYYY-MM/YYYY-MM-DD.md"""
    return DIARY_BASE / d.strftime("%Y-%m") / f"{d}.md"


def extract_diary_context(diary_text: str) -> tuple[str, list[str]]:
    """
    从昨日日记中提取最有价值的上下文片段 + 关键词。
    返回 (最佳感悟片段, 关键词列表)
    """
    keywords = []
    context_parts = []

    # 优先取 rating_reason（含金量理由）
    m = re.search(r'rating_reason:\s*"(.+?)"', diary_text)
    if m:
        reason = m.group(1).strip()
        context_parts.append(("含金量", reason))
        keywords.extend(re.findall(r'[\u4e00-\u9fff]{2,6}', reason))

    # 取今日含金量行（标题下方的 > [!tip]）
    m = re.search(r'🏆\s*今日含金量[：:]\s*\*{0,2}(.+?)\*{0,2}', diary_text)
    if m:
        context_parts.append(("评级", m.group(1).strip()))

    # 取S级顿悟专区标题+第一句
    m = re.search(r'(?:S级顿悟专区|S级顿悟)[^\n]*\n\s*\*{0,2}"(.+?)"', diary_text, re.DOTALL)
    if m:
        insight = m.group(1).strip()
        context_parts.append(("S级顿悟", insight[:60]))
        keywords.extend(re.findall(r'[\u4e00-\u9fff]{3,8}', insight[:60]))

    # 取今日感悟正文的第一段
    m = re.search(r'## 5️⃣?\s*💡\s*今日感悟\s*\n{2,}(.*?)(?:\n---|\n###|\n<!--)', diary_text, re.DOTALL)
    if m:
        para = m.group(1).strip().split('\n')[0].strip()
        if para and '暂无' not in para:
            context_parts.append(("感悟", para[:80]))
            keywords.extend(re.findall(r'[\u4e00-\u9fff]{3,8}', para[:80]))

    # 取今日最佳决策
    m = re.search(r'今日最佳决策.*?\n(?:\*{0,2})(.*?)(?:\*{0,2})(?=\n---|\n<!--|\Z)', diary_text, re.DOTALL)
    if m:
        decision = m.group(1).strip()
        if decision and '待填写' not in decision:
            context_parts.append(("决策", decision[:60]))
            keywords.extend(re.findall(r'[\u4e00-\u9fff]{3,8}', decision[:60]))

    # 取项目里程碑
    m = re.search(r'项目里程碑.*?\n(.*?)(?=\n---|\n<!--|\Z)', diary_text, re.DOTALL)
    if m:
        milestone = m.group(1).strip()
        if milestone and '待' not in milestone:
            context_parts.append(("里程碑", milestone[:60]))
            keywords.extend(re.findall(r'[\u4e00-\u9fff]{3,8}', milestone[:60]))

    # 从context_parts选最佳上下文片段
    best_snippet = ""
    if context_parts:
        # 优先用含金量理由
        for label, text in context_parts:
            if label == "含金量" and text:
                best_snippet = text
                break
        if not best_snippet:
            best_snippet = context_parts[0][1]

    # 去重、去停用词、取长度≥2的中文词
    stop_words = {'今日', '明天', '昨天', '完成', '需要', '可以', '没有', '不是',
                  '这个', '那个', '什么', '怎么', '一个', '一些', '自己', '时候',
                  '之后', '然后', '所以', '但是', '因为', '如果', '虽然', '而且'}
    seen = set()
    result = []
    for kw in keywords:
        kw = kw.strip()
        if kw and kw not in seen and kw not in stop_words and len(kw) >= 2:
            seen.add(kw)
            result.append(kw)

    return best_snippet, result


def load_quote_pool() -> tuple[list, str]:
    """
    返回 [(金句, 书名), ...] 及来源标识。
    优先核心启发库；不存在则用随包分发的名人名言缓存（daily_quotes_cache.json），
    使 Skill 在无个人库时仍能自包含生成灵感。
    """
    if INSPIRATION_LIB.exists():
        text = INSPIRATION_LIB.read_text(encoding="utf-8")
        lines = []
        current_book = ""
        for line in text.split("\n"):
            book_m = re.search(r'<!-- BOOK:\s*(.+?) -->', line)
            if book_m:
                current_book = book_m.group(1).strip().replace("《", "").replace("》", "")
                continue
            if line.startswith("> ") and "来源：" not in line and "💡" not in line:
                quote = line[2:].strip()
                if quote:
                    lines.append((quote, current_book))
        if lines:
            return lines, "library"
    if INSPIRATION_CACHE.exists():
        try:
            data = json.loads(INSPIRATION_CACHE.read_text(encoding="utf-8"))
            quotes = []
            # 主源：quote_library（完整名人名言池，随包分发）
            for entry in data.get("quote_library", []):
                q = entry.get("quote", "").strip()
                b = entry.get("book", "").strip().replace("《", "").replace("》", "")
                if q:
                    quotes.append((q, b))
            # 兜底：早期 daily_quotes（按日期稀疏填充的少量条目）
            if not quotes:
                for entry in data.get("daily_quotes", {}).values():
                    q = entry.get("quote", "").strip()
                    b = entry.get("book", "").strip().replace("《", "").replace("》", "")
                    if q:
                        quotes.append((q, b))
            if quotes:
                return quotes, "cache"
        except Exception:
            pass
    return [], "none"


def get_recent_quotes(target_date: datetime.date, window: int = 14) -> set:
    """扫描近 window 天日记的灵感闪现，返回近期已用金句集合（14天内防重复）。"""
    recent = set()
    for i in range(1, window + 1):
        d = target_date - datetime.timedelta(days=i)
        p = diary_path_for_date(d)
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(r'💡\s*\*\*灵感闪现\*\*：([^\n——]+)', text)
        if m:
            q = m.group(1).strip()
            if q and "待填入" not in q:
                recent.add(q)
    return recent


def rotate_pick(pool: list, date_str: str) -> tuple:
    """按目标日期确定性轮换选取，保证同日期结果稳定、跨天铺开到全库（不总取首条）。"""
    h = int(hashlib.md5(date_str.encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def select_inspiration(keywords, pool, recent, date_str) -> tuple:
    """
    从 pool 选金句：先排除近期已用 → 按关键词打分取最佳 → 无匹配则按日期确定性轮换。
    返回 (金句, 书名, 是否关键词命中)。
    """
    filtered = [(q, b) for (q, b) in pool if q not in recent]
    if not filtered:
        filtered = pool  # 全近期用过则退而用全量，避免空选
    if keywords:
        scored = []
        for q, b in filtered:
            score = sum(1 for kw in keywords if kw in q)
            if score > 0:
                scored.append((score, q, b))
        if scored:
            scored.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
            return scored[0][1], scored[0][2], True
    q, b = rotate_pick(filtered, date_str)
    return q, b, False


def build_inspiration_block(date_str: str) -> str:
    """
    从昨日日记提取灵感闪现货源，返回 Markdown 格式的灵感闪现块。
    优先核心启发库；无个人库时自动回退到随包分发的名人名言缓存。
    始终产出真实金句（14天内防重复 + 无匹配按日期轮换），不残留占位符。
    """
    try:
        d = datetime.date.fromisoformat(date_str)
        yesterday = d - datetime.timedelta(days=1)
        diary_path = diary_path_for_date(yesterday)

        snippet, keywords = "", []
        if diary_path.exists():
            diary_text = diary_path.read_text(encoding="utf-8")
            snippet, keywords = extract_diary_context(diary_text)

        pool, source_kind = load_quote_pool()
        if not pool:
            return (
                "💡 **灵感闪现**：{{灵感闪现_待填入}}\n\n"
                "<!-- 格式: 金句 —— 书名 -->\n"
                "<!-- 核心启发库与名人名言缓存均不可用，请今日复盘后手动补入 -->"
            )

        recent = get_recent_quotes(d)
        quote, book, matched = select_inspiration(keywords, pool, recent, date_str)

        # 来源说明：区分关键词命中与轮换兜底，保持诚实（不编造匹配关系）
        if snippet and matched:
            display = snippet[:50]
            if len(snippet) > 50:
                punct_positions = [display.rfind(c) for c in "，。？！；"]
                trunc_at = max(punct_positions) if any(p >= 0 for p in punct_positions) else -1
                if trunc_at > 30:
                    display = snippet[:trunc_at + 1] + "……"
                else:
                    display = display + "……"
            quote_char = '"'
            source_text = f"> 来源：昨日{quote_char}{display}{quote_char}——金句匹配《{book}》。\n"
        elif matched:
            source_text = f"> 来源：金句匹配《{book}》。\n"
        else:
            source_text = f"> 来源：灵感轮换《{book}》（昨日无强匹配，按日期轮换选取，14天内不重复）。\n"

        return (
            f"💡 **灵感闪现**：{quote}\n"
            f"\n"
            f"{source_text}"
        )

    except Exception as e:
        return (
            "💡 **灵感闪现**：{{灵感闪现_待填入}}\n\n"
            f"<!-- 自动匹配异常: {e}，请今日复盘后手动补入 -->"
        )


def build_skeleton(date_str: str) -> str:
    """构建日记骨架 Markdown"""
    d = datetime.date.fromisoformat(date_str)
    wd = weekday_cn(d)
    inspiration = build_inspiration_block(date_str)

    return f"""---
date: {d}
day_of_week: {wd}
tags: [daily-buddy, pomodoro, goal, review]
rating: 待评定
rating_reason: ""
achievement_data:
  tomato: 0
  sleep_time: ""
  wake_time: ""
  sleep_duration: 0
  sleep_quality: ""
  energy_pred: 0
  energy_actual: 0
  calm_pred: 0
  calm_actual: 0
  satisfaction: 0
  physiological: ""
---

# {d}({wd}) 每日计划

> [!tip] 🏆 今日含金量：**[待评定]**

{inspiration}
<!-- SECTION: SLEEP -->
## 1️⃣ 😴 睡眠质量

> 数据来源：Apple Watch
> ⚠️ 待明早数据

| 指标 | 数值 | 状态 |
|------|------|------|
| 入睡时间 | — | — |
| 醒来时间 | — | — |
| 总时长 | — | — |
| 清醒 | — | — |
| REM | — | — |
| 浅睡 | — | — |
| 深睡 | — | — |

---

<!-- SECTION: GOALS -->
## 2️⃣ 🎯 今日工作

### 续接锚点
> 📌 昨天说今天要做：（待填写）
> 📌 今天实际做了：（待填写）

### 核心主表
| 序号 | P1核心任务（最多3件） | 可验证完成标准 | 计划时段 | 时间象限（Q1-Q4） | 预判能量 | 实际完成 | 实际能量 |
|------|----------------------|---------------|----------|------------------|---------|---------|---------|
| 1 | （待填写） |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |

---

<!-- SECTION: MILESTONES -->
## 3️⃣ 📊 项目里程碑

| 项目 | 最新状态 | 变更日期 |
|------|---------|:--------:|
| — | — | — |

---

<!-- SECTION: ACHIEVEMENTS -->
## 4️⃣ 🏆 今日成就达成

> 待晚间复盘填充

---

<!-- SECTION: MOOD_ENERGY -->
## 5️⃣ 😊 心情与能量

### 三分维度
> ⚠️ 待晚间复盘

### 今天刻意没做的事
> 待填写

---

<!-- SECTION: INSIGHTS -->
## 6️⃣ 💡 今日感悟

---

<!-- SECTION: BEST_DECISION -->
## 7️⃣ 🎯 今日最佳决策

> 待填写

---

<!-- SECTION: CONSISTENCY_REVIEW -->
## 8️⃣ 🪞 言行一致性复盘

> 待晚间复盘

---

<!-- SECTION: SUSPENSION -->
## 🌀 悬置/残差（认知盲区轴 · 按需填写）

> 待晚间复盘（按需·非必填，确有残差才填；数据契约见 ~/个人AI档案/未知未知/悬置区.md）

| 序号 | 触发(T1-T5) | 归属(用户/AI/双方共盲) | 毛坯描述（仅现象） | 状态 |
|------|------------|---------------------|-------------------|------|
| 1 | | | | 悬置(未闭合) |
| 2 | | | | 悬置(未闭合) |

---

<!-- SECTION: SUMMARY -->
## 9️⃣ 📝 今日总结

> 待晚间复盘

---

<!-- SECTION: TOMORROW -->
## 🔟 🎯 明日目标

> 待晚间复盘

---

<!-- SECTION: BUDDY_ADVICE -->
## 1️⃣1️⃣ 🦞 每日伙伴建议

> 待晚间复盘

---
"""


def main():
    parser = argparse.ArgumentParser(description='生成日记骨架')
    parser.add_argument('--date', required=True, help='日期，格式 YYYY-MM-DD')
    parser.add_argument('--out', required=False, help='输出文件路径（幂等——文件已存在则跳过；不传则 stdout 兼容旧用法）')
    args = parser.parse_args()

    # 幂等写盘
    if args.out:
        out_path = Path(args.out)
        if out_path.exists():
            print(f"骨架已存在，跳过（幂等）：{out_path}", file=sys.stderr)
            sys.exit(0)
        out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        skeleton = build_skeleton(args.date)
    except ValueError as e:
        print(f"日期格式错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 额外输出元信息供 AI 引用
    d = datetime.date.fromisoformat(args.date)
    wd = weekday_cn(d)
    print(f"<!-- META: date={d} weekday={wd} -->", file=sys.stderr)

    if args.out:
        out_path.write_text(skeleton)
        print(f"✅ 骨架已写入：{out_path}", file=sys.stderr)
    else:
        print(skeleton)


if __name__ == '__main__':
    main()
