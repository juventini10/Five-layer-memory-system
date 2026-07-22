#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断言台账议题名索引加载器（确定性 · grep锚定）

来源：未知未知前置容器阶段1 #2（对话冲突自动检测 · clock-loop v2.5.0）
用途：从断言台账.md抽取所有"活跃"状态条目的议题名，输出JSON供AI提取断言时强制注入prompt。
不做AI语义判定——纯正则解析Markdown字段，可grep可复现。

设计依据：Agent B（三明智L3审查）打回硬伤#4——"台账加载链路缺失，若靠'AI记得去看'则违背铁律精神"。
本脚本将"加载台账"变为确定性步骤：Phase 0运行本脚本 → 拿到议题名列表 → 强制注入提取prompt。

输出格式（JSON）：
{
  "topics": ["议题名1", "议题名2", ...],
  "active_entries": M,
  "ledger_exists": true|false
}

失败处理：
- 台账文件不存在 → 返回 {"topics": [], "active_entries": 0, "ledger_exists": false}
- 解析异常 → 打印错误到stderr，返回空列表（不崩溃）

用法：
  python3 load_claim_index.py [--ledger PATH]
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_LEDGER = "~/[记忆共享中心]/未知未知/断言台账.md"


def resolve_path(p: str) -> Path:
    return Path(p).expanduser()


def load_topics(ledger_path: Path) -> dict:
    """从断言台账提取活跃条目的议题名列表。"""
    if not ledger_path.exists():
        return {"topics": [], "active_entries": 0, "ledger_exists": False}

    text = ledger_path.read_text(encoding="utf-8")

    # 匹配 ### 断言#{n} · DATE 块
    claim_blocks = re.split(r'(?m)^###\s+断言#\d+', text)
    topics = []
    active_count = 0

    # 改进：按块解析，每块提取议题+状态
    blocks = re.findall(
        r'(?ms)^###\s+断言#\d+.*?(?=^###\s+断言#\d+|\Z)',
        text,
    )
    for block in blocks:
        topic_m = re.search(r'^- 议题:\s*(.+)$', block, re.M)
        status_m = re.search(r'^- 状态:\s*(.+)$', block, re.M)
        if not topic_m:
            continue
        topic = topic_m.group(1).strip()
        status = status_m.group(1).strip() if status_m else "活跃"
        if status == "活跃" and topic:
            topics.append(topic)
            active_count += 1

    # 去重保序
    seen = set()
    deduped = []
    for t in topics:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    return {
        "topics": deduped,
        "active_entries": active_count,
        "ledger_exists": True,
    }


def main():
    parser = argparse.ArgumentParser(description="断言台账议题名索引加载器")
    parser.add_argument(
        "--ledger",
        default=DEFAULT_LEDGER,
        help="断言台账.md路径（默认：~/[记忆共享中心]/未知未知/断言台账.md）",
    )
    args = parser.parse_args()

    try:
        ledger = resolve_path(args.ledger)
        result = load_topics(ledger)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: 台账解析失败: {e}", file=sys.stderr)
        print(json.dumps({"topics": [], "active_entries": 0, "ledger_exists": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
