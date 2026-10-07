#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v1.0
"""
skill_spec_read_guard.py —— 改 Skill 前必读规范守卫（PreToolUse·公共·硬拦）

病（2026-09-19 皮叔亲问「改 Skill 前必须先看规范，可以设 hook 吗」）：
  AI 改 SKILL.md 时**不读**《Skill架构规范》《指令编写规范》→ 违规落地（规范写在文件里，无人读）。
  = 典型"只写正面规则、缺反向校验"（执规-008 判据：不读文档也被拦才算机制化）。

判（机械·零 AI 判断）：
  · 见 Read/Grep/Glob 命中**规范文件** → 记标记 `~/.cache/skill_gate/spec_read.active`（mtime<4h）
  · 见 Edit/Write/MultiEdit 命中 **SKILL.md**（技能配置/*/SKILL.md 或 */skills/*/SKILL.md）
      → 有标记 → exit 0 放行；无标记 → exit 2 物理阻断 + 引导语

真相所有权（守卫规范§二）：规范文件清单=SPECS 常量（唯一住所·本文件）；⛔不在守卫里内联规范内容。
端中立（公共件）：不绑端；各端 settings.json PreToolUse 接入即可用。@0/scripts 豁免。
契约：exit 2=拦 / exit 0=放行；失败放行（守卫规范§三 Hook 三纪律）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
import re
import time

GUARD_NAME = "skill_spec_read_guard.py"
GATE_DIR = os.path.expanduser("~/.cache/skill_gate")
SPEC_MARKER = os.path.join(GATE_DIR, "spec_read.active")
TTL = 4 * 3600

# 规范文件（名字特征）——命中任一即视为"已读规范"
SPECS = ("Skill架构规范", "指令编写规范", "守卫编写规范", "文件格式规范", "脚本架构设计通用规范")
# 受管目标：SKILL.md（改 Skill 本体）
SKILL_RE = re.compile(r"(?:技能配置|skills)/[^/]+/SKILL\.md$")
EXEMPT = (GUARD_NAME, "append_log_entry.py", "/growth-box/scripts/", "/数字分身/scripts/")


def _paths(tool, inp):
    out = []
    for k in ("file_path", "path", "pattern", "glob"):
        v = inp.get(k)
        if isinstance(v, str) and v:
            out.append(v)
    if tool in ("Bash", "bash"):
        out.append(str(inp.get("command", "")))
    return out


def _touch_spec():
    try:
        os.makedirs(GATE_DIR, exist_ok=True)
        open(SPEC_MARKER, "w").close()
    except Exception:
        pass


def main():
    try:
        obj = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(obj, dict):
        return
    tool = obj.get("toolName") or obj.get("tool_name") or ""
    inp = obj.get("input") or obj.get("tool_input") or {}
    if not isinstance(inp, dict):
        return
    full = json.dumps(inp, ensure_ascii=False)
    if any(x in full for x in EXEMPT):
        return
    paths = _paths(tool, inp)
    joined = " ".join(paths)
    # ① 读规范 → 记标记
    if tool in ("Read", "Grep", "Glob") and any(s in joined for s in SPECS):
        _touch_spec()
        return
    # ② 改 Skill → 查标记
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        if any(SKILL_RE.search(p) for p in paths):
            fresh = False
            try:
                fresh = (time.time() - os.path.getmtime(SPEC_MARKER)) < TTL
            except OSError:
                fresh = False
            if fresh:
                return
            print("⛔ Skill规范读取门卫：本次将改 SKILL.md，但本会话未见「读规范」记录。"
                  "→ 请先读《Skill架构规范》+《指令编写规范》（读一次即留痕·4h 有效），再改。",
                  file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
