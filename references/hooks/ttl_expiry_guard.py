import os
#!/usr/bin/env python3
# version: v0.2
# v0.2：输出协议委托 hook_protocol（同 secret_key_guard 法·双端实测 JSON/text 各归其位）
"""ttl_expiry_guard.py — UserPromptSubmit 钩子：规则文件 TTL 过期自动提醒（每会话首prompt一次）。
扫描 ~/[记忆共享中心]/记忆规则/*.md 头部「过期：YYYY-MM-DD」→ 已过期则注入提醒；无过期静默。
防重入：cache/ttl-expiry/<sid>.json（对齐 title/tail 状态机）。异常 exit 0。"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, os, re, sys
from datetime import datetime
from pathlib import Path

RULES_DIR = os.path.expanduser("[记忆共享中心]/记忆规则")
STATE_DIR = Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or (Path.home() / ".workbuddy")) / "cache/ttl-expiry"


def overdue_rules():
    out = []
    today = datetime.now().date()
    if not RULES_DIR.is_dir():
        return out
    for p in sorted(RULES_DIR.glob("*.md")):
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:800]
        except Exception:
            continue
        m = re.search(r"过期[:：]\s*(\d{4}-\d{2}-\d{2})", head)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        if d < today:
            out.append((p.name, m.group(1), (today - d).days))
    return out


def main():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
        sid = str(payload.get("session_id", "")).strip()
    except Exception:
        sys.exit(0)
    if not sid:
        sys.exit(0)
    state = STATE_DIR / f"{sid}.json"
    if state.exists():
        sys.exit(0)  # 本会话已查过
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        ov = overdue_rules()
        state.write_text(json.dumps({"checked": True, "n": len(ov)}, ensure_ascii=False))
        if ov:
            lines = "；".join(f"{name} 过期{d}天" for name, _, d in ov[:6])
            msg = f"【⏰ TTL 过期提醒】{lines}——引用其内容前先声明已过期或更新（铁律-010）"
            # 输出协议委托 hook_protocol 单一真源（2026-09-18 Qoder CN 挂载轮·对齐 secret_key_guard）：
            #   本端裸 stdout 判 winner=none 整轮丢弃；text 端由真源维持裸文本，零回归。
            try:
                import hook_protocol as _hp
                _hp.emit(msg, payload=payload, argv=sys.argv[1:],
                         event="UserPromptSubmit", script="ttl_expiry_guard.py")
            except Exception:
                sys.stdout.write(msg)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
