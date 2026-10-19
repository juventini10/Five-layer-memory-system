#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1（2026-10-04 T0 D3-P2-9b）
"""qodercn_subagent_evidence_guard.py — 子代理产出物存在性核验（报告制·本端特性×愿景③质变钩子）。

质变点：子代理在结论里声称"读了/写了/产出了 <路径>"→ 机械核验该路径物理存在，
死指针自动落账本，不靠 triwich 闸3 人工偶然发现（S988 单卡不是复利·落账才是）。
判据对象=路径指针的文件存在性（物理事实），⛔不读不评判正文内容——禁令#1（格式/内容
警察永久禁止）合规位：本件零语义扫描。
投递=纯留痕 jsonl（growth-box/日报按需消费），⛔不进报警面⛔不阻断（禁令#3 告警疲劳、
Stop 类钩子三纪律）；恒 exit 0。
合成行口径（施工单§14）：session_id 非 task- 前缀直接静默。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, json, os, re
from datetime import datetime

LEDGER = os.environ.get("QSE_LEDGER") or os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime/subagent_evidence_ledger.jsonl")  # 端侧约定=脚本中心(2026-10-02 RUNTIME_PATH_DIRS教训:端用户机无开发工具目录)·作者机同名存在
PATH_RE = re.compile(r"(?:/Users/[^\s'\"`,;:()（）\[\]|]+|~/[^\s'\"`,;:()（）\[\]|]+)")
MAX_CHECK = 15


def main():
    try:
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    sid = str(payload.get("session_id") or "")
    if not sid.startswith("task-"):
        return 0  # 合成载荷隔离（§14）
    msg = str(payload.get("last_assistant_message") or "")
    if not msg:
        # 2026-10-06 实测形制（questWindow/hooks.log 回执+探针账本对账）：本端 SubagentStop
        #   payload keys 无消息正文键，旧读法恒空=检测静默空转（真缺陷）。正解=从 transcript_path 取末条 assistant text。
        tp = str(payload.get("transcript_path") or "")
        if tp:
            tp = os.path.expanduser(tp)
            if not os.path.isfile(tp):
                cand = os.path.expanduser("~/.qoder-cn/projects")
                for root, _, files in os.walk(cand):
                    if os.path.basename(tp) in files:
                        tp = os.path.join(root, os.path.basename(tp)); break
            try:
                last_txt = ""
                with open(tp, encoding="utf-8", errors="replace") as tf:
                    for line in tf:
                        try:
                            d = json.loads(line)
                        except Exception:
                            continue
                        if (d.get("type") or d.get("role")) != "assistant":
                            continue
                        for blk in (d.get("message") or {}).get("content") or []:
                            if isinstance(blk, dict) and blk.get("type") == "text" and blk.get("text"):
                                last_txt = blk["text"]
                msg = last_txt
            except Exception:
                msg = ""
    if payload.get("session_id"):
        try:  # 收讫心跳（append-only·config_guard never 判据的证据面·检测空转也留在场证明）
            os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
            with open(LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                    "kind": "ack", "agent": str(payload.get("agent_type", "")),
                                    "msg_chars": len(msg)}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    if not msg:
        return 0
    seen, checked, dead = set(), 0, []
    for m in PATH_RE.finditer(msg):
        raw = m.group(0).rstrip(".。,，:：;")
        if raw in seen:
            continue
        seen.add(raw)
        checked += 1
        if not os.path.exists(os.path.expanduser(raw)):
            dead.append(raw[:120])
        if checked >= MAX_CHECK:
            break
    if dead:
        rec = {"ts": datetime.now().isoformat(timespec="seconds"),
               "agent": str(payload.get("agent_type", "")),
               "dead_pointers": dead[:10], "checked_paths": checked,
               "transcript": str(payload.get("agent_transcript_path", ""))[:100]}
        try:
            os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
            with open(LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass  # 留痕失败绝不阻塞
    return 0


def _self_test():
    import subprocess, tempfile
    fd, led = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    cases = [
        ("S1 合成sid→静默", {"session_id": "behav-x", "last_assistant_message": "/nonexistent"}, 0),
        ("S2 全存活路径→零留痕", {"session_id": "task-a", "last_assistant_message": sys.argv[0]}, 0),
        ("S3 死指针→落账1行", {"session_id": "task-b", "last_assistant_message": "已产出 ~/不存在-XYZ.txt"}, 1),
    ]
    # S4：transcript 兜底取末条 assistant text 死指针→落账（transcript_path 传 basename 亦验回退搜索）
    fd2, tr = tempfile.mkstemp(suffix=".jsonl"); os.close(fd2)
    with open(tr, "w", encoding="utf-8") as g:
        g.write(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "已产出 /Users/xx/不存在-S4.txt"}]}}) + "\n")
    cases.append(("S4 transcript兜底→死指针落账", {"session_id": "task-s4", "transcript_path": tr}, None))
    ok = True
    for name, payload, want_lines in cases:
        env = dict(os.environ, QSE_LEDGER=led)
        subprocess.run([sys.executable, __file__], input=json.dumps(payload),
                       text=True, env=env, capture_output=True)
        lines_ = [l for l in open(led, encoding="utf-8") if l.strip()]
        n = len([l for l in lines_ if '"kind": "ack"' not in l])
        good = (n == want_lines) if want_lines is not None else (n >= 1)
        ok = ok and good
        print(("  ✅ " if good else "  ❌ ") + name)
    os.unlink(led)
    try: os.unlink(tr)
    except Exception: pass
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    sys.exit(main())
