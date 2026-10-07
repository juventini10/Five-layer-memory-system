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
# version: v0.1
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


def check(old_string, new_string):
    if not old_string or new_string is None:
        return None
    first = old_string.split("\n", 1)[0]
    if not is_structural(first):
        return None
    if first in new_string:
        return None
    return ("[BLOCK] edit_heading_guard: old_string first line is a structural line '"
            + first[:40] + "' but new_string does not re-include it -- 4 prior swallow incidents."
            " Re-include the original line in new_string.")


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
    args = ap.parse_args()

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
