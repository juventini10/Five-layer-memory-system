#!/usr/bin/env python3
# version: v0.2
# v0.2：输出协议委托 hook_protocol 单一真源（Qoder CN 裸 stdout 判 winner=none 丢弃·JSON 端收 additionalContext／text 端裸文本零回归·双端夹具实测）
"""secret_key_guard.py — UserPromptSubmit 钩子：疑似密钥/Token 粘贴自动提醒（隐私红线机械层）。
规则：窄正则命中→stdout 注入提醒；⛔只报类型与处置建议，绝不回显/落盘密钥内容（隐私红线④）。
安全：异常 exit 0 静默；命中不阻断（提醒不拦路）。"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import json, re, sys

_PATTERNS = [
    ("OpenAI/Anthropic sk- 密钥", r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    ("GitHub Token ghp_", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    ("AWS Access Key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("私钥 PEM", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("JWT", r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ("Slack xox 令牌", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("腾讯云/通用长密钥形态", r"\b[A-Za-z0-9]{32,64}\b"),
]

def check(prompt: str):
    hits = []
    for name, pat in _PATTERNS:
        if re.search(pat, prompt):
            hits.append(name)
    return hits

def main():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
        prompt = str(payload.get("prompt", "")).strip()
    except Exception:
        sys.exit(0)
    if not prompt:
        sys.exit(0)
    try:
        hits = check(prompt)
        if hits:
            # 只报类型不报内容——密钥正文永不回显/不落盘
            msg = (f"【🔒 密钥提醒】检测到疑似：{'、'.join(hits)}。"
                   f"若非有意发给目标服务，请勿让密钥外流；本提醒不展示密钥内容。")
            # 输出协议委托 hook_protocol 单一真源（2026-09-18 Qoder CN 挂载轮）：
            #   本端裸 stdout 被产品判 winner=none 整轮丢弃（143/143 实测先例），
            #   text 端（WorkBuddy）由真源维持裸文本 ⇒ 各端零回归，⛔不在本脚本自选形态。
            try:
                import hook_protocol as _hp
                _hp.emit(msg, payload=payload, argv=sys.argv[1:],
                         event="UserPromptSubmit", script="secret_key_guard.py")
            except Exception:
                sys.stdout.write(msg)  # 真源缺失=降级留痕不静默（对齐 route_inject_prompt 姿势）
    except Exception:
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()
