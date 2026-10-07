#!/usr/bin/env python3
# version: v0.1
"""delivery_boundary_guard.py — Stop 钩子：交付边界声明守卫（WB-20260909-001 教训机制化）。
检测：回复含"排除/保留/未动"类静默取舍词却无"刻意/范围/声明"交代 → 追加违规台账 + stdout 提示。
设计（防误报优先）：只在"取舍词在、声明词缺"时告警；全量无取舍的正常交付不响。
安全：转录缺失/解析失败→静默；异常 exit 0。"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, os, sys

_EXCLUDE = ["除了", "保留", "未动", "跳过", "不碰", "没动", "排除", "但", "只改", "其余"]
_DECLARE = ["刻意", "范围", "声明", "待决", "如有需要", "待拍板", "未纳入", "回滚", "备份在"]
LEDGER = os.path.expanduser("[记忆共享中心]/脚本中心/logs/delivery_boundary_violations.log")


def last_assistant_text(transcript_path: str):
    if not transcript_path or not os.path.isfile(transcript_path):
        return ""
    texts = []
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                role = o.get("role") or (o.get("message") or {}).get("role", "")
                if role != "assistant":
                    continue
                c = o.get("content") or (o.get("message") or {}).get("content", "")
                if isinstance(c, list):
                    c = " ".join(str(x.get("text", "")) for x in c if isinstance(x, dict))
                if isinstance(c, str) and c.strip():
                    texts.append(c.strip())
    except Exception:
        return ""
    return texts[-1] if texts else ""


def main():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        sys.exit(0)
    tp = str(payload.get("transcript_path", "")).strip()
    text = last_assistant_text(tp)
    if not text:
        sys.exit(0)
    try:
        has_excl = any(w in text for w in _EXCLUDE)
        has_decl = any(w in text for w in _DECLARE)
        # 排除词常误中"但/只改/其余"，收紧：需同时出现 2+ 个排除词 或 含明确保留词
        excl_cnt = sum(1 for w in _EXCLUDE if w in text)
        strong_excl = excl_cnt >= 2 or any(w in text for w in ["保留", "跳过", "未动", "没动", "不碰"])
        if strong_excl and not has_decl:
            msg = (f"⚠️ 交付边界缺失：回复含取舍词（{'/'.join([w for w in _EXCLUDE if w in text][:3])}）"
                   f"但未声明「刻意跳过什么/为什么」——静默取舍=从皮叔位置看与漏做无异（WB-20260909-001）")
            try:
                os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
                with open(LEDGER, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
            print(msg)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
