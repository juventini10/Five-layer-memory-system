#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""self_improvement_guard.py v0.1 — 自我改进守卫（规则诱导器 MVP·Top1 候选）

触发条件：当对话中出现以下信号之一时激活：
  1. 命令/操作失败（非零退出码·异常·超时）
  2. 皮叔纠正（"不对""应该是…""其实…"）
  3. 发现更好的方法（与既有做法不同且更优）
  4. 知识过时（文档与实际不符·API 行为变化）
  5. 皮叔请求的能力不存在

行为：激活后调用 self-improvement Skill，按该 Skill 规范记录到 .learnings/。
触发词（EVIDENCE_WORDS）：
  - 英文：error|fail|wrong|correction|learning|outdated|better approach|best practice
  - 中文：错误|失败|纠正|不对|其实|过时|更好|优化|改进|学到了

验收条件：
  - [ ] 触发后 self-improvement Skill 被调用
  - [ ] 生成了符合格式的 learning entry
  - [ ] entry 包含 Summary + Details + Suggested Action + Metadata
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re, json, os
from datetime import datetime

# 触发模式
TRIGGER_PATTERNS = [
    r"(?i)(error|fail|wrong|correction|learning|outdated|better approach|best practice)",
    r"(错误|失败|纠正|不对|其实|过时|更好|优化|改进|学到了|应该是)",
    r"(?i)(exception|timeout|unexpected|stack trace)",
    r"(异常|超时|意外|堆栈)",
]

def should_trigger(transcript: str) -> bool:
    """判断对话是否满足 self-improvement 触发条件"""
    for pat in TRIGGER_PATTERNS:
        if re.search(pat, transcript):
            return True
    return False

def generate_learning_entry(transcript: str, context: dict) -> dict:
    """生成符合 self-improvement Skill 规范的 learning entry"""
    return {
        "id": "LRN-{}".format(datetime.now().strftime("%Y%m%d-001")),
        "category": context.get("category", "correction"),
        "priority": context.get("priority", "medium"),
        "status": "pending",
        "area": context.get("area", "config"),
        "summary": context.get("summary", ""),
        "details": context.get("details", ""),
        "suggested_action": context.get("action", ""),
        "metadata": {
            "source": context.get("source", "conversation"),
            "triggered_by": "self_improvement_guard.py v0.1",
            "radar_hits_30d": 85,
        }
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        if should_trigger(text):
            entry = generate_learning_entry(text, {"summary": "CLI trigger test"})
            print(json.dumps(entry, ensure_ascii=False, indent=2))
        else:
            print("未触发")
