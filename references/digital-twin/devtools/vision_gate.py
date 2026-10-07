#!/usr/bin/env python3
# version: v0.1
"""vision_gate.py —— 愿景三问门禁（PAT-044 晋升的配套机械化手段）

🔴 立脚本原因（2026-08-29 PAT-044 晋升·候解法落地）：
  PAT-044「愿景判据被动显影」实证：皮叔一天内三次强调"符合愿景做最优解"，
  每次都是被提醒后才补验，没有一次是交付前主动过愿景三问的。
  → 晋升只写进规则文件不够——**判据挂在人的提醒上，还是会漏**。
  → 机械化：交付类回复缺愿景三问 → 提示（warn，不阻断，避免噪音）。

判据：
  1. 仅对**交付类**回复生效——回复含结论块/下一步建议/方案等交付标记时才检查
     （闲聊、纯问答不检查，否则噪音=守卫被忽略）
  2. 检测到交付标记但缺愿景三问 → 🟡 提示（非阻断）
  3. 愿景三问任一表述命中即通过：强化闭环 / 减少人工 / 更懂皮叔

契约：--check(JSON,含 alarm) / --report / --selfcheck
⛔ 本门禁是**提示级**，alarm 恒为 false——它的作用是"提醒别漏"，不是"拦住交付"。
    （与童灵规格书零问题门禁 G1–G4 的 block 级区分）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
from datetime import datetime

HEARTBEAT = "/tmp/vision_gate.heartbeat"

# 交付标记：命中任一即认为这是"交付类回复"，需要过愿景三问
DELIVERY_MARKERS = [
    r"\*\*下一步建议\*\*", r"下一步建议[：:]", r"## L\d .*结果",
    r"📦 成长箱", r"\| 结论 \| 说明 \|", r"\*\*\{?✅/🟡/❌",
    r"落地步骤", r"建议[：: ]", r"方案[：: ]",
]

# 愿景三问任一命中即通过
VISION_MARKERS = [
    r"强化闭环", r"减少人工", r"更懂皮叔",
    r"愿景(?:三问|四方向|①|②|③|④)", r"符合愿景",
]


def beat():
    try:
        with open(HEARTBEAT, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds")}, f)
    except OSError:
        pass


def get_text():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        if not raw.strip():
            return ""
        try:
            d = json.loads(raw)
            for k in ("text", "prompt", "content", "message"):
                v = d.get(k)
                if isinstance(v, str) and v.strip():
                    return v
            return json.dumps(d, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return raw
    except Exception:
        return ""


def check(text):
    is_delivery = any(re.search(m, text) for m in DELIVERY_MARKERS)
    has_vision = any(re.search(m, text) for m in VISION_MARKERS)
    return is_delivery, has_vision


def mode_check(text):
    beat()
    is_delivery, has_vision = check(text)
    miss = is_delivery and not has_vision
    print(json.dumps({
        "alarm": False,  # 提示级门禁，不阻断
        "is_delivery": is_delivery,
        "has_vision_block": has_vision,
        "reminder": ("⚠️ 交付类回复缺【愿景三问】块——补一句：强化闭环吗？减少人工吗？更懂皮叔吗？"
                     if miss else None),
        "note": "PAT-044 配套·提示级不阻断（阻断级噪音=守卫被忽略）",
    }, ensure_ascii=False, indent=2))
    return 0


def main():
    a = sys.argv[1:]
    if "--selfcheck" in a:
        print("交付标记数:", len(DELIVERY_MARKERS), "| 愿景标记数:", len(VISION_MARKERS))
        print("用法: vision_gate.py [--check|--selfcheck]")
        return 0
    sys.exit(mode_check(get_text()))


if __name__ == "__main__":
    main()
