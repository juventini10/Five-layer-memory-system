#!/usr/bin/env python3
# version: v0.1
"""Verify a skill's SKILL.md frontmatter `version` equals its references/CHANGELOG.md top version.

Single source of truth = references/CHANGELOG.md. The frontmatter `version` is a
redundant copy that drifts when a version bump updates CHANGELOG but forgets the
frontmatter (实测 sucair frontmatter 1.5.0 vs CHANGELOG 4.5.0). This script
mechanically checks the two agree.

Exit codes: 0 = match / no CHANGELOG (no conflict) · 1 = mismatch or missing SKILL.md · 2 = usage.

Usage: python3 verify_skill_version.py <skill_dir>
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys


def frontmatter_version(skill_md):
    txt = open(skill_md, encoding="utf-8").read()
    m = re.search(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        return None
    fm = m.group(1)
    vm = re.search(r'^version:\s*["\']?([0-9][0-9.]*)\s*["\']?', fm, re.M)
    return vm.group(1).strip() if vm else None


def changelog_top_version(changelog_md):
    if not os.path.exists(changelog_md):
        return None
    txt = open(changelog_md, encoding="utf-8").read()
    m = re.search(r"^###\s*v([0-9][0-9.]*)", txt, re.M)
    return m.group(1).strip() if m else None


def main():
    if len(sys.argv) < 2:
        print("usage: verify_skill_version.py <skill_dir>", file=sys.stderr)
        return 2
    d = sys.argv[1]
    skill_md = os.path.join(d, "SKILL.md")
    changelog = os.path.join(d, "references", "CHANGELOG.md")
    if not os.path.exists(skill_md):
        print(f"no SKILL.md in {d}", file=sys.stderr)
        return 1
    fv = frontmatter_version(skill_md)
    cv = changelog_top_version(changelog)
    print(f"frontmatter version : {fv}")
    print(f"CHANGELOG top      : {cv}")
    if cv is None:
        print("skip: no CHANGELOG top version found (no single-source conflict)")
        return 0
    if fv != cv:
        print(f"MISMATCH: frontmatter {fv} != CHANGELOG {cv}")
        return 1
    print("OK: frontmatter == CHANGELOG top (single source of truth enforced)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
