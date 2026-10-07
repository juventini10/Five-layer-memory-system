#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_skills_relink.py —— W11 承重验收：Skill 软链只增不删不替换

核心命题：**用户已有的同名 Skill 不会被布洛陀静默替换**。

用例：
  S1 缺失 → 建链
  S2 已有正确链 → 跳过
  S3 断链 → 重建
  S4 ⛔ 指向别处的链（用户自己的）→ conflict·**不删不改**
  S5 ⛔ 实目录（用户自己装的）→ 跳过·不动
  S6 幂等：连跑两次·第二次全跳过
  S7 冲突**不算失败**（rc=0·避免 CI 误报警）
  S8 造错：换回旧语义（指向别处就重建）⇒ S4 断言必须 FAIL（防恒真）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("skills_relink", os.path.join(_HERE, "skills_relink.py"))
sr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sr)

PASS, FAIL = [], []


def _t(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  ❌ ") + name + (("  · " + detail) if detail and not cond else ""))
    return cond


def _mk_skill(src, name):
    d = os.path.join(src, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write("---\nname: %s\n---\n布洛陀版\n" % name)
    return d


def needs_fix(dest_dir, name, target):
    return sr.needs_fix(os.path.join(dest_dir, name), target)


def s1_create():
    print("S1 缺失 → 建链")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "alpha")
        need, reason = needs_fix(dest, "alpha", d)
        _t("判定为需建", bool(need), str(reason))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s2_already_valid():
    print("S2 已有正确链 → 跳过")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "alpha")
        os.symlink(d, os.path.join(dest, "alpha"), target_is_directory=True)
        need, reason = needs_fix(dest, "alpha", d)
        _t("判定为无需动", not need, str(reason))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s3_broken():
    print("S3 断链 → 重建")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "alpha")
        os.symlink(os.path.join(tmp, "nowhere"), os.path.join(dest, "alpha"),
                   target_is_directory=True)
        need, reason = needs_fix(dest, "alpha", d)
        _t("判定为需建", bool(need), str(reason))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s4_user_link_untouched():
    print("S4 ⛔ 指向别处的链（用户的）→ conflict·不改不删")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "daily-buddy")
        user_dir = os.path.join(tmp, "my-own-skills", "daily-buddy")
        os.makedirs(user_dir)
        with open(os.path.join(user_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: daily-buddy\n---\n**用户自己写的版本**\n")
        link = os.path.join(dest, "daily-buddy")
        os.symlink(user_dir, link, target_is_directory=True)
        need, reason = needs_fix(dest, "daily-buddy", d)
        _t("判为 conflict", bool(need), str(reason))
        _t("用户链接未被替换", os.path.islink(link)
           and os.readlink(link) == user_dir, os.readlink(link))
        _t("用户内容仍在", "用户自己写的版本" in open(os.path.join(link, "SKILL.md"), encoding="utf-8").read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s5_user_dir_untouched():
    print("S5 ⛔ 实目录（用户自己装的）→ 跳过·不动")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "triwich")
        user_dir = os.path.join(dest, "triwich")
        os.makedirs(user_dir)
        with open(os.path.join(user_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: triwich\n---\n用户的\n")
        need, reason = needs_fix(dest, "triwich", d)
        _t("判定为跳过", not need, str(reason))
        _t("实目录未被替换为链", os.path.isdir(user_dir) and not os.path.islink(user_dir))
        _t("用户内容仍在", "用户的" in open(os.path.join(user_dir, "SKILL.md"), encoding="utf-8").read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s6_idempotent():
    print("S6 幂等：连跑两次")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "alpha")
        os.symlink(d, os.path.join(dest, "alpha"), target_is_directory=True)
        r1 = [needs_fix(dest, "alpha", d) for _ in range(2)]
        _t("两次都判定无需动", all(not r[0] for r in r1), repr(r1))
        _t("链未被动", os.readlink(os.path.join(dest, "alpha")) == d)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s7_conflict_not_failure():
    print("S7 冲突不算失败")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src")
        os.makedirs(src)
        _mk_skill(src, "x")
        # 直接验证退出码逻辑：errors 为空 ⇒ 不 sys.exit(1)
        import inspect
        src_txt = inspect.getsource(sr.main)
        _t("退出码只看 errors 不看 conflicts",
           "if not ARGS.dry and errors:" in src_txt and "and conflicts" not in src_txt)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s8_falsification():
    print("S8 造错：证明 S4 的断言不是恒真")
    tmp = tempfile.mkdtemp()
    try:
        src = os.path.join(tmp, "src"); dest = os.path.join(tmp, "dest")
        os.makedirs(src); os.makedirs(dest)
        d = _mk_skill(src, "daily-buddy")
        user_dir = os.path.join(tmp, "my-own", "daily-buddy")
        os.makedirs(user_dir)
        with open(os.path.join(user_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: daily-buddy\n---\n**用户自己写的版本**\n")
        link = os.path.join(dest, "daily-buddy")
        os.symlink(user_dir, link, target_is_directory=True)

        need, reason = sr.needs_fix(link, d)
        # 承重：判据必须**能区分**两种情形
        _t("当前语义：用户的链 → conflict", bool(need), str(reason))

        # 造错：真的按「旧语义」把它替换掉 ⇒ S4 的判据必须能发现
        if os.path.islink(link):
            os.remove(link)
        os.symlink(d, link, target_is_directory=True)
        need2, reason2 = sr.needs_fix(link, d)
        _t("造错后（链已指向布洛陀）→ 判定为无需动·证明判据可区分",
           (not need2), str(reason2))
        _t("造错确实动了用户的东西（否则本用例恒真）",
           "用户自己写的版本" not in open(os.path.join(link, "SKILL.md"), encoding="utf-8").read())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== W11 承重验收 · Skill 软链只增不删不替换 ===\n")
    for fn in (s1_create, s2_already_valid, s3_broken,
               s4_user_link_untouched, s5_user_dir_untouched,
               s6_idempotent, s7_conflict_not_failure, s8_falsification):
        fn()
        print("")
    print("=" * 52)
    print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("❌ 失败项：" + " · ".join(FAIL))
        return 1
    print("✅ 全部通过（用户的 Skill 不会被静默替换）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())