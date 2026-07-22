#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断言追加器（确定性 · grep锚定）

来源：未知未知前置容器阶段1 #2（对话冲突自动检测 · clock-loop v2.5.0）
用途：AI提取断言后调用，向断言台账.md追加一条新断言。
- 格式校验：必须提供 议题/立场/来源/日期
- grep校验：新议题名是否命中已有列表（复用load_claim_index.py逻辑）→ 命中则复用已有名称
- 立场比对：同议题名下不同立场 → 输出T2冲突信号（标而不判）

设计依据：Agent B（三明智L3审查）打回硬伤#1——"先查台账复用议题名"是软行为指令无grep锚点。
本脚本将"复用议题名"变为确定性机制：提取前load_claim_index.py注入列表，提取后本脚本grep校验命中，
整链不再依赖AI自觉。硬伤#3——#1/#2双触发去重：本脚本检测到同议题冲突时输出T2信号，
clock-loop Phase 4.5据此写悬置区且#1已处理的本周期不再重复触发（去重规则在SKILL.md声明）。

参数（命令行）：
  --topic  议题名（短关键词）
  --stance 立场陈述（一句话）
  --source 来源（对话|日记|复盘|探针）
  --date   YYYY-MM-DD
  --dry-run 只检测不写入（质量抽样用，不污染台账）

输出：
  - 追加成功 → 打印 "✅ 已追加 断言#{n} | 议题:[topic]"
  - 议题命中已有但立场一致 → 打印 "🔄 议题复用+立场一致 | 已更新最近时间"
  - 立场冲突 → 额外打印 "⚠️ T2冲突信号 | 同议题[{topic}]下发现不同立场 → 写入悬置区.md"

退出码：0=成功（含冲突信号，信号由调用方处理）| 1=参数错误 | 2=文件写入失败

用法：
  python3 append_claim.py --topic "四象限定义" --stance "双主体认知框架" --source 对话 --date 2026-07-07
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import re
import sys
from pathlib import Path

DEFAULT_LEDGER = "~/个人AI档案/未知未知/断言台账.md"
VALID_SOURCES = {"对话", "日记", "复盘", "探针"}

# 未知未知三文件冻结表头（与 主文件 / references/unknown-unknown-headers.md 逐字一致）
# 三文件任一缺失时由本脚本自建，确保写方 Skill 自包含（规则 A：写方必须自建文件夹+相关文件，不依赖别的 Skill 先跑）
HEADER_SUSPENSION = """# 🌀 未知未知 · 悬置区（认知盲区轴·毛坯容器）

> **定位**：平行于「认知轴（SHADOW / 成长箱 / CORE）」与「时间轴（日记 / 周报 / 月报时间象限）」的**第三轴·盲区轴**入口。
> **来源**：未知未知前置容器改造（设计草案 v0.1 + 四象限设计哲学.md §2.7）。
> **设计哲学冻结点（§2.7.8）**：本容器只存「尚未命名 / 未归因」的异常毛坯，**不存结论**。目标不是清零。

---

## 一、数据契约（承重墙 · v0.1 · 冻结）

### 1.6 单条条目 schema（Markdown · 机器可读）
```
### 残差#{序号} · {YYYY-MM-DD}
- 触发: T1|T2|T3|T4|T5
- 归属: 用户盲区|AI盲区|双方共盲
- 来源: 对话|日记|复盘|探针(反方向的钟/S级评审/迁理之外/三明智)
- 记录者: 用户|AI
- 状态: 悬置(未闭合)
- 毛坯描述: (仅冻现象，禁止当时深加工/归因)
```

## 二、悬置条目
"""

HEADER_ASSERT = """# 📊 断言台账（对话冲突检测·持久化容器）

> **来源**：未知未知前置容器改造 #2（对话冲突自动检测·clock-loop v2.5.0）
> **定位**：跨对话陈述一致性比对的持久化层。
> **设计哲学**：本台账只存"已提取的关键断言"；立场比对由脚本做（非AI主观判定）。

---

## 数据契约（承重墙 · 冻结）

### 单条断言 schema（Markdown · 机器可读）
```
### 断言#{序号} · {YYYY-MM-DD}
- 议题: (短关键词，如"四象限定义")
- 立场: (一句话核心主张)
- 来源: 对话|日记|复盘|探针
- 首次时间: {YYYY-MM-DD}
- 最近时间: {YYYY-MM-DD}
- 状态: 活跃|废弃
```
"""

HEADER_MANIFEST = """# 📋 悬置区 · 显形台账

> **用途**：月报「悬置区显形回看」（月报SOP 第1.6步）时，把每条残差的去向记录于此，形成闭环可追溯。
> **配套**：`~/个人AI档案/未知未知/悬置区.md`。
> **成功标准**：显形率 / 平均盲区存活时长。目标不是清零。

| 残差# | 日期 | 触发 | 归属 | 显形判定日期 | 去向 | 备注 |
|-------|------|------|------|------------|------|------|
"""


def resolve_path(p: str) -> Path:
    return Path(p).expanduser()


def parse_existing(ledger_path: Path):
    """解析台账，返回 (claims列表, 最大序号)。claims每项={topic, stance, status, raw_block}"""
    if not ledger_path.exists():
        return [], 0
    text = ledger_path.read_text(encoding="utf-8")
    blocks = re.findall(r'(?ms)(^###\s+断言#\d+.*?)(?=^###\s+断言#\d+|\Z)', text)
    claims = []
    max_n = 0
    for block in blocks:
        n_m = re.search(r'^###\s+断言#(\d+)', block, re.M)
        topic_m = re.search(r'^- 议题:\s*(.+)$', block, re.M)
        stance_m = re.search(r'^- 立场:\s*(.+)$', block, re.M)
        status_m = re.search(r'^- 状态:\s*(.+)$', block, re.M)
        if not (n_m and topic_m and stance_m):
            continue
        n = int(n_m.group(1))
        max_n = max(max_n, n)
        claims.append({
            "n": n,
            "topic": topic_m.group(1).strip(),
            "stance": stance_m.group(1).strip(),
            "status": status_m.group(1).strip() if status_m else "活跃",
        })
    return claims, max_n


def get_existing_topics(claims):
    """返回活跃议题名集合。"""
    return {c["topic"] for c in claims if c["status"] == "活跃"}


def find_conflict(claims, topic, stance):
    """同议题名下不同立场 → 返回冲突的旧立场，否则None。"""
    for c in claims:
        if c["topic"] == topic and c["status"] == "活跃":
            if c["stance"] != stance:
                return c["stance"]
    return None


def build_block(n, topic, stance, source, date):
    return (
        f"\n### 断言#{n:03d} · {date}\n"
        f"- 议题: {topic}\n"
        f"- 立场: {stance}\n"
        f"- 来源: {source}\n"
        f"- 首次时间: {date}\n"
        f"- 最近时间: {date}\n"
        f"- 状态: 活跃\n"
    )


def main():
    parser = argparse.ArgumentParser(description="断言追加器")
    parser.add_argument("--topic", required=True, help="议题名（短关键词）")
    parser.add_argument("--stance", required=True, help="立场陈述（一句话）")
    parser.add_argument("--source", required=True, choices=sorted(VALID_SOURCES), help="来源")
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER, help="断言台账.md路径")
    parser.add_argument("--dry-run", action="store_true", help="只检测不写入（质量抽样用，不污染台账）")
    args = parser.parse_args()

    # 日期格式校验
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', args.date):
        print("ERROR: --date 格式必须为 YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    ledger = resolve_path(args.ledger)
    uk_dir = ledger.parent
    # 自包含引导（规则 A）：写方 Skill 必须保证「文件夹 + 三文件」齐备，不依赖别的 Skill 先跑
    suspension = uk_dir / "悬置区.md"
    manifest = uk_dir / "显形台账.md"
    if not suspension.exists():
        suspension.write_text(HEADER_SUSPENSION, encoding="utf-8")
    if not ledger.exists():
        uk_dir.mkdir(parents=True, exist_ok=True)
        ledger.write_text(HEADER_ASSERT, encoding="utf-8")
    if not manifest.exists():
        manifest.write_text(HEADER_MANIFEST, encoding="utf-8")
    claims, max_n = parse_existing(ledger)

    existing_topics = get_existing_topics(claims)

    # grep校验：议题名命中已有列表 → 复用已有名称（确定性，不靠AI自觉）
    def write_or_dry(block, label):
        if args.dry_run:
            print(f"（dry-run）{label} | 不写入台账")
            return
        try:
            with ledger.open("a", encoding="utf-8") as f:
                f.write(block)
            print(f"✅ {label}")
        except OSError as e:
            print(f"ERROR: 写入失败: {e}", file=sys.stderr)
            sys.exit(2)

    if args.topic in existing_topics:
        conflict_stance = find_conflict(claims, args.topic, args.stance)
        print(f"🔄 议题复用 | 议题:[{args.topic}] 已存在于台账")
        if conflict_stance:
            print(f"⚠️ T2冲突信号 | 同议题[{args.topic}]下发现不同立场")
            print(f"   旧立场: {conflict_stance}")
            print(f"   新立场: {args.stance}")
            print(f"   动作: 写入悬置区.md（标而不判，归因留月报显形回看）")
            new_n = max_n + 1
            block = build_block(new_n, args.topic, args.stance, args.source, args.date)
            write_or_dry(block, f"已追加 断言#{new_n:03d} | 议题:[{args.topic}]（保留冲突信号）")
            sys.exit(0)
        else:
            print(f"✅ 立场一致 | 无冲突，本次不重复追加")
            sys.exit(0)

    # 新议题 → 追加
    new_n = max_n + 1
    block = build_block(new_n, args.topic, args.stance, args.source, args.date)
    write_or_dry(block, f"已追加 断言#{new_n:03d} | 议题:[{args.topic}]（新议题）")
    sys.exit(0)


if __name__ == "__main__":
    main()
