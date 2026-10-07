#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# grep_sandbox_guard.py — PreToolUse 守卫·拦本沙箱不可用的 grep 正则语法
# version: v1.0（2026-09-20·WorkBuddy·LRN-20260920-009 落地）
#
# Disease（LRN-20260920-009·单日 4 次实例）：
#   本沙箱 / 环境（toybox / BSD grep）**不支持** `\|` `\w` `\+` `\{n\}`——
#   命令**不报错**，但把它们当字面量 → **静默零命中**。
#   零命中被读成"不存在"→ 污染结论（实证：误判 "SKILL.md 缺 version 字段" 并向皮叔报出）。
#   知识早已写在 memory 里，但"提示层知识"未转成"动作层约束"= 知道≠做到。
#
# Verdict（mechanical·只做机器能做的）：
#   PreToolUse 收到 Bash 命令 → 若命令含 `grep` 且命中危险转义 → **exit 2 物理阻断** + 给改法。
#   （该形态的命令必然给错结论，非"可能"，故不设 advisory 档）
#
# Usage（stdin JSON·PreToolUse·与同域 skill_write_gate_guard.py 接口对齐）：
#   ZCode shape: {"toolName":"Bash","input":{"command":..}}
#   WB shape:    {"tool_name":"Bash","tool_input":{"command":..}}
#   -> block exit 2 / ok exit 0
#
# 契约（守卫规范）：--check(JSON·含 alarm) / --report(明细)；失败放行；
#   ⛔ 取不到输入/解析失败亦**写台账负痕**（读不到必须可见·同域教训 2026-09-20）。
# 台账：~/.workbuddy/grep_sandbox_guard_state.json（append-only·单行 JSON）
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, json, os, re
from datetime import datetime

GUARD = "grep_sandbox_guard.py"
STATE = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
                     "grep_sandbox_guard_state.json")

# 危险转义：BSD/toybox grep 不支持（须用 -E / python 正则 / Grep 工具）
DANGEROUS = re.compile(r"\\\||\\w|\\\+|\\\{[0-9]")


def extract_event(obj):
    """与同域 skill_write_gate_guard.py 同接口：双形状归一。"""
    tool = obj.get("toolName") or obj.get("tool_name") or ""
    inp = obj.get("input") or obj.get("tool_input") or {}
    return tool, inp


def _ledger(rec):
    try:
        with open(STATE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def check():
    raw = ""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    except Exception:
        raw = ""
    try:
        obj = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "parse_error": str(e)[:120]})
        return 0

    tool, inp = extract_event(obj)
    cmd = inp.get("command") or inp.get("cmd") or "" if isinstance(inp, dict) else ""

    if tool != "Bash" or not cmd:
        _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "skip": "非 Bash 或无命令", "tool": tool})
        return 0

    hit = bool("grep" in cmd and DANGEROUS.search(cmd))
    _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "tool": tool, "hit": hit, "cmd_head": cmd[:120]})

    if hit:
        print(json.dumps({
            "alarm": True,
            "reason": "grep 命令含本环境不支持的转义（\\| / \\w / \\+ / \\{n}）——"
                      "命令不会报错但会**静默零命中**，零命中≠不存在（LRN-20260920-009 实证误判）",
            "fix": "改用 Grep 工具（ripgrep·支持完整正则），或 python3 -c 正则；"
                   "仅需多关键词或（alternation）时也可用 grep -E 'a|b'"
        }, ensure_ascii=False))
        return 2
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
    hits = sum(1 for r in rows if r.get("hit"))
    print(f"grep 沙箱语法闸对账：回合 {tot} · 拦截 {hits} · 放行 {tot-hits}")
    for r in rows[-8:]:
        flag = "⛔" if r.get("hit") else "✅"
        print(f"  {flag} {r.get('ts')} | {str(r.get('cmd_head') or r.get('skip') or r.get('parse_error'))[:70]}")
    return 0


if __name__ == "__main__":
    try:
        if "--report" in sys.argv:
            report()
        else:
            sys.exit(check())
    except Exception:
        pass
    sys.exit(0)
