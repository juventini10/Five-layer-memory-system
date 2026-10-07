#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v1.0
"""
reply_tail_guard.py —— 回复「留尾巴」对账（Stop·公共·advisory 不阻断）

病（皮叔反复强调「不要留尾巴」「有风险就解决，不然我今晚不用睡了」）：
  AI 收尾时把未收口的事**抛回给皮叔**（"需你拍板/待你定/下轮再/待确认"）——
  把决策与焦虑转嫁给皮叔，而非自己收口。= "交付自主化"（童灵 W1④）的反向违约。

判（机械·零 AI 判断）：Stop 读回复文本 → 命中尾巴模式 → 台账留痕 + alarm。
真相所有权（守卫规范§二）：尾巴模式 = TAIL_PATTERNS 常量（唯一住所）。
端中立（公共件）：不绑端；各端 settings.json Stop 接入即可用。
契约：exit 0 恒定（advisory·不阻断）；失败放行。
台账：~/.workbuddy/reply_tail_state.json（append-only·单行 JSON）。
用法：--check(stdin JSON) / --report(明细)
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
import re
from datetime import datetime

STATE = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
                     "reply_tail_state.json")

# 尾巴模式（窄集·防误报）：把球踢回给皮叔的表述
TAIL_PATTERNS = [
    r"需你拍板", r"待你拍板", r"待你定", r"等你确认", r"待你确认", r"待确认",
    r"下轮再", r"下轮做", r"下轮处理", r"下轮补", r"下次再", r"留到下次",
    r"待你裁决", r"等你定", r"留待.*拍板", r"pending",
]
TAIL_RE = re.compile("|".join(TAIL_PATTERNS))


def _text(obj):
    if not isinstance(obj, dict):
        return ""
    for k in ("text", "prompt", "content", "response", "last_message", "output"):
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _ledger(rec):
    try:
        with open(STATE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def check():
    try:
        obj = json.load(sys.stdin)
    except Exception:
        return 0
    txt = _text(obj)
    if not txt.strip():
        return 0
    hits = sorted(set(m.group(0) for m in TAIL_RE.finditer(txt)))
    alarm = bool(hits)
    _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "tail": hits, "alarm": alarm, "head": txt[:70]})
    if alarm:
        print(json.dumps({"alarm": True,
                          "reason": f"回复留尾巴（{'/'.join(hits)}）——交付自主化要求：能收口的当场收口，"
                                    f"只有真需你拍板的才抛（童灵 W1④）"},
                         ensure_ascii=False))
    return 0


def report():
    if not os.path.exists(STATE):
        print("（台账为空）")
        return 0
    rows = []
    for ln in open(STATE, encoding="utf-8"):
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    tot = len(rows)
    al = sum(1 for r in rows if r.get("alarm"))
    print(f"留尾巴对账：回合 {tot} · 命中 {al} · 合规率 {(tot-al)/tot*100:.1f}%" if tot else "（无数据）")
    for r in rows[-8:]:
        print(("  ⛔ " if r.get("alarm") else "  ✅ ") + f"{r['ts']} {r.get('tail')} | {r.get('head','')[:46]}")
    return 0


if __name__ == "__main__":
    try:
        if "--report" in sys.argv:
            report()
        else:
            check()
    except Exception:
        pass
    sys.exit(0)
