#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# edit_heading_guard.py -- Edit structural-line swallow guard (batch6 item1, ledger #264/#265/#268)
# Disease: Edit replacing a heading/structure line without re-including the original line
#   -> original heading swallowed (3 real incidents on CHANGELOG 2026-09-05, prose-discipline catch rate 0/4).
# Verdict (mechanical, zero AI judgment):
#   if old_string first line is a heading (#{1,6}) or version-entry line:
#     new_string MUST contain that first line verbatim, else block.
# Usage:
#   hook mode (stdin JSON, PreToolUse):
#     CodeBuddy/WorkBuddy shape: {"tool_name":"Edit","tool_input":{"old_string":..,"new_string":..}}
#     ZCode CLI shape:            {"toolName":"Edit","input":{"old_string":..,"new_string":..}}
#     (extract_event normalizes both -- backward compatible, zero behavior change on known platforms)
#     -> violation exit 2 (physical block), ok exit 0
#   CLI mode: edit_heading_guard.py --old-file f1 --new-file f2
#     -> violation exit 1, ok exit 0
# Boundary: only blocks "old first line is structural AND new lost that exact line";
#   heading renames need human review -- this guard only targets the exact 4-time incident shape.
# version: v0.2（2026-10-05 判据粒度收窄：同结构签名仍在即放行——version 行改值/标题粘连拆分
#   属规范强制动作，旧版要求逐字回含致其被硬拦；真吞行照拦。自测 S1-S6 6/6 拦放双向）
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import json
import re
import argparse

HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
VERSION_ENTRY_RE = re.compile(r"^\s{0,3}(#{1,6}\s+v\d+\.\d+|version:)")


def is_structural(first_line):
    return bool(HEADING_RE.match(first_line) or VERSION_ENTRY_RE.match(first_line))


def _sig(line):
    """结构签名：标题=「# 号数 + 标题首段（截到边界符）」；版本行=「version:」键。

    v0.2 判据粒度收窄（2026-10-05 实证）：本守卫原要求 new_string **逐字**回含 old 首行，
    而规范强制的「frontmatter version 随条目派生」本质就是**改这一行的值** ⇒ 合法动作被硬拦
    （实测 rc=2）。收窄为同签名即放行：吞行（签名消失）照拦，改值/拆行放行。
    ⛔ 不是放宽到"随便改"——签名必须仍在。"""
    s = line.strip()
    if s.startswith("version:"):
        return "version:"
    m = re.match(r"^#{1,6}\s+(\S+)", s)
    if m:
        hashes = s.split(" ", 1)[0]
        title = m.group(1)
        pref = re.split(r"[（(\-—:：|*`]", title, 1)[0] or title
        return hashes + " " + pref[:12]
    return s


def check(old_string, new_string):
    if not old_string or new_string is None:
        return None
    first = old_string.split("\n", 1)[0]
    if not is_structural(first):
        return None
    if first in new_string:
        return None
    sig = _sig(first)                                  # 同结构签名仍在 ⇒ 合法改值/拆分
    for l in new_string.split("\n"):
        if is_structural(l) and _sig(l) == sig:
            return None
    return ("[BLOCK] edit_heading_guard: old_string first line is a structural line '"
            + first[:40] + "'（签名 " + sig[:24] + "）but new_string 既未逐字回含、也保留该签名"
            " —— 4 prior swallow incidents. Re-include the line or keep its signature.")


# ————————————————— 自测（§3.0·5 纪律①·拦/放双向对立=自带变异） —————————————————
def self_test():
    ok = bad = 0

    def ck(name, cond):
        nonlocal ok, bad
        print(("  ✅ " if cond else "  ❌ ") + name)
        if cond:
            ok += 1
        else:
            bad += 1

    # S1 真吞行必拦（原案：## 变更记录 消失）
    ck("S1 标题整行消失→拦", check("## 变更记录\n- x", "- x") is not None)
    # S2 合法版本派生必放（改值不换键）
    ck("S2 version 行改值→放", check("version: v1.1.17\ndate: a", "version: v1.1.18\ndate: a") is None)
    # S3 标题粘连拆行必放（签名仍在）
    ck("S3 粘连标题拆分→放", check("## 变更记录- **v1.0**：x\n", "## 变更记录\n- **v1.1**：y\n") is None)
    # S4 版本行整行删掉必拦
    ck("S4 version 行被吞→拦", check("version: v1.0\ndate: a", "date: a") is not None)
    # S5 非结构行不受影响
    ck("S5 普通行→放", check("- **工具**：Qoder CN\n", "- **工具**：ZCode\n") is None)
    # S6 换标题文字（签名变）必拦——防"改名式吞行"
    ck("S6 标题改到签名不存在→拦", check("## 六、变更记录\nx", "## 附：日志\nx") is not None)
    print("自测结果: %d/%d 通过" % (ok, ok + bad))
    return 0 if bad == 0 else 1



def extract_event(data):
    """Normalize PreToolUse payload across platforms.

    CodeBuddy/WorkBuddy family: tool_name + tool_input{old_string,new_string}
    ZCode CLI family:            toolName  + input{old_string,new_string}
    Returns (tool, old_string, new_string). Unknown shapes degrade to ("", "", None)
    so check() returns None -> exit 0 (fail-open, never mutates).
    """
    if not isinstance(data, dict):
        return "", "", None
    tool = data.get("tool_name") or data.get("toolName") or ""
    ti = data.get("tool_input") or data.get("input") or {}
    if not isinstance(ti, dict):
        ti = {}
    return tool, ti.get("old_string", ""), ti.get("new_string")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-file")
    ap.add_argument("--new-file")
    ap.add_argument("--hook", action="store_true", help="stdin JSON hook mode")
    ap.add_argument("--self-test", action="store_true", help="S1-S6 拦/放双向夹具")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    if args.hook or (not args.old_file and not sys.stdin.isatty()):
            try:
                data = json.load(sys.stdin)
            except Exception:
                data = {}
            _tool, old_string, new_string = extract_event(data)
            reason = check(old_string, new_string)
            if reason:
                print(reason)
                sys.exit(2)
            sys.exit(0)

    old_s = open(args.old_file, encoding="utf-8").read() if args.old_file else ""
    new_s = open(args.new_file, encoding="utf-8").read() if args.new_file else ""
    reason = check(old_s, new_s)
    if reason:
        print(reason)
        sys.exit(1)
    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
