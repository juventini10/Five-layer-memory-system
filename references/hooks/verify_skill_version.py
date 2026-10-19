#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.2
"""Verify a skill's SKILL.md frontmatter `version` equals its
references/CHANGELOG.md top version.

Single source of truth = references/CHANGELOG.md. The frontmatter `version`
is a redundant copy that drifts when a version bump updates CHANGELOG but
forgets the frontmatter.

v0.2（2026-10-17·Qoder CN·V2.2.0 发版轮 rv7c·条文60 形态域同步）：
  仪器形态盲区把 3 件账一致的件误判 MISMATCH（sucair/system-logger/triwich·
  包面入账时拦 commit 实锤；此件随包分发，端用户 verify 链会撞同款假红，
  故必须修在发布前）。扩形三处：
  ①changelog 顶部标题从只认「### v」扩为 ##／### 两级；
  ②新式日期标题「## <日期>…：SKILL.md vA→vB」取箭头右侧目标值；
  ③fm version 容忍前导 v（"version: v4.5.3" 形态）。
  负例自证：真漂移仍抓红（--selftest 内置·防「扩形洗红」）。
Usage: python3 verify_skill_version.py <skill_dir> | --selftest
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import io
import os
import re
import sys


def frontmatter_version(skill_md):
    txt = io.open(skill_md, encoding="utf-8").read()
    m = re.search(r"^---\s*\n(.*?)\n---", txt, re.S)
    if not m:
        return None
    fm = m.group(1)
    vm = re.search(r'^version:\s*["\']?v?([0-9][0-9.]*)\s*["\']?', fm, re.M)
    return vm.group(1).strip() if vm else None


def changelog_top_version(changelog_md):
    if not os.path.exists(changelog_md):
        return None
    for line in io.open(changelog_md, encoding="utf-8", errors="replace"):
        if not re.match(r"^#{2,3}\s", line):
            continue
        m = re.match(r"^#{2,3}\s*v([0-9][0-9.]*)", line)
        if m:
            return m.group(1).strip()
        m = re.search(r"v[0-9][0-9.]*\s*(?:→|->)\s*v([0-9][0-9.]*)", line)
        if m:
            return m.group(1).strip()
    return None


def check(skill_dir):
    skill_md = os.path.join(skill_dir, "SKILL.md")
    changelog = os.path.join(skill_dir, "references", "CHANGELOG.md")
    if not os.path.exists(skill_md):
        print("no SKILL.md in %s" % skill_dir, file=sys.stderr)
        return 1
    fv = frontmatter_version(skill_md)
    cv = changelog_top_version(changelog)
    print("frontmatter version : %s" % fv)
    print("CHANGELOG top      : %s" % cv)
    if cv is None:
        print("skip: no CHANGELOG top version found (no single-source conflict)")
        return 0
    if fv != cv:
        print("MISMATCH: frontmatter %s != CHANGELOG %s" % (fv, cv))
        return 1
    print("OK: frontmatter == CHANGELOG top (single source of truth enforced)")
    return 0


def selftest():
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="vsv-selftest-")
    pos = [
        ("h3v", '---\nversion: "1.2.3"\n---\n', "### v1.2.3\n"),
        ("h2v", '---\nversion: "1.2.3"\n---\n', "## v1.2.3 — 2026-10-13\n"),
        ("arrow", '---\nversion: "1.2.3"\n---\n',
         "## 2026-10-17 · WB：SKILL.md v1.2.2→v1.2.3\n"),
        ("vfx", '---\nversion: "v1.2.3"\n---\n', "### v1.2.3\n"),
    ]
    passed, total = 0, len(pos) + 1
    try:
        for name, sk, cl in pos:
            d = os.path.join(root, name)
            os.makedirs(os.path.join(d, "references"))
            io.open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(sk)
            io.open(os.path.join(d, "references", "CHANGELOG.md"), "w",
                    encoding="utf-8").write(cl)
            if check(d) == 0:
                passed += 1
            else:
                print("SELFTEST FAIL(pos): %s 合法形态被误判=扩形没生效" % name)
        d = os.path.join(root, "neg")
        os.makedirs(os.path.join(d, "references"))
        io.open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(
            '---\nversion: "9.9.9"\n---\n')
        io.open(os.path.join(d, "references", "CHANGELOG.md"), "w",
                encoding="utf-8").write("### v1.2.3\n")
        if check(d) == 1:
            passed += 1
        else:
            print("SELFTEST FAIL(neg): 真漂移未抓到=扩形洗红了")
        print("SELFTEST %d/%d" % (passed, total))
        return 0 if passed == total else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print("usage: verify_skill_version.py <skill_dir>|--selftest",
              file=sys.stderr)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    return check(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())
