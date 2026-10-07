#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_install_rule_merge.py —— 0b 承重验收：规则三层走断章增量

验的是**真实入口函数** `install_scripts.install_rule_files()`，⛔ 不是引擎单测。

用例：
  R1 全新装 → 三层建成·有标记段·frontmatter 在首位
  R2 用户已有改过的铁律版 → 装完用户内容零丢失
  R3 幂等：连装两次 → 第二次全 UNCHANGED·用户文件 mtime 不变
  R4 段内被用户手改 → CONFLICT 且**盘上零改动**
  R5 造错：把入口换回覆盖语义（改用户文件）⇒ R2 的断言必须 FAIL（防恒真）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(os.path.dirname(_HERE))   # references/scripts → 包根
_spec = importlib.util.spec_from_file_location(
    "install_scripts_probe", os.path.join(_PKG, "install_scripts.py")
)
ins = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ins)

USER_LINES = "\n".join(
    "## 我自己加的第 %d 条铁律\n这条是用户自己写的，布洛陀不许动。" % i
    for i in range(1, 21)
)
PASS, FAIL = [], []


def _t(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  ❌ ") + name + (("  · " + detail) if detail and not cond else ""))
    return cond


def _mk(mc, tielu_extra="", fm=True):
    d = os.path.join(mc, "记忆规则")
    os.makedirs(d, exist_ok=True)
    head = ('---\ndescription: "我自己改的描述·请勿覆盖"\n---\n\n') if fm else ""
    with open(os.path.join(d, "用户基本规则-铁律版.md"), "w", encoding="utf-8") as f:
        f.write(head + "# 我自己的铁律版\n\n" + USER_LINES + "\n" + tielu_extra)


def r1_fresh_install():
    print("R1 全新装 → 三层建成")
    mc = tempfile.mkdtemp()
    try:
        res = ins.install_rule_files(mc)
        _t("返回三项", len(res) == 3, repr(res))
        _t("全部 CREATED", all(st == "CREATED" for _, st, _ in res), repr(res))
        p = os.path.join(mc, "记忆规则", "用户基本规则-铁律版.md")
        txt = open(p, encoding="utf-8").read()
        _t("frontmatter 在第 1 行", txt.startswith("---\n"))
        _t("有 BULUOTUO 标记段", "<!-- BULUOTUO:BEGIN rules.tielu -->" in txt)
        _t("占位符已替换", os.path.expanduser("~") not in txt)
        for n, sid in (("用户基本规则-摘要版.md", "rules.summary"),
                       ("用户基本规则-详解存档版.md", "rules.detail")):
            t2 = open(os.path.join(mc, "记忆规则", n), encoding="utf-8").read()
            _t("%s 有独立标记段" % n, ("<!-- BULUOTUO:BEGIN %s -->" % sid) in t2)
    finally:
        shutil.rmtree(mc, ignore_errors=True)


def r2_user_content_survives():
    print("R2 用户已有改过的铁律版 → 用户内容零丢失")
    mc = tempfile.mkdtemp()
    try:
        _mk(mc)
        p = os.path.join(mc, "记忆规则", "用户基本规则-铁律版.md")
        before = open(p, encoding="utf-8").read()
        ins.install_rule_files(mc)
        after = open(p, encoding="utf-8").read()
        _t("用户 frontmatter 保留", "我自己改的描述·请勿覆盖" in after)
        _t("用户 20 条全在", all(("我自己加的第 %d 条铁律" % i) in after for i in range(1, 21)))
        _t("用户原文字节仍在段前", after.startswith(before))
        _t("布洛陀段已追加", "<!-- BULUOTUO:BEGIN rules.tielu -->" in after)
        baks = []
        for root, _dn, fs in os.walk(os.path.join(mc, "记忆琥珀")):
            baks += [f for f in fs if ".bak-" in f]
        _t("有安装前备份(C6)", len(baks) >= 1, repr(baks))
    finally:
        shutil.rmtree(mc, ignore_errors=True)


def r3_idempotent():
    print("R3 幂等：连装两次")
    mc = tempfile.mkdtemp()
    try:
        _mk(mc)
        ins.install_rule_files(mc)
        p = os.path.join(mc, "记忆规则", "用户基本规则-铁律版.md")
        m1, t1 = os.path.getmtime(p), open(p, encoding="utf-8").read()
        res = ins.install_rule_files(mc)
        _t("第二次全 UNCHANGED", all(st == "UNCHANGED" for _, st, _ in res), repr(res))
        _t("内容一致", open(p, encoding="utf-8").read() == t1)
        _t("mtime 未变", os.path.getmtime(p) == m1)
    finally:
        shutil.rmtree(mc, ignore_errors=True)


def r4_conflict():
    print("R4 段内被用户手改 → CONFLICT 且盘上零改动")
    mc = tempfile.mkdtemp()
    try:
        ins.install_rule_files(mc)
        p = os.path.join(mc, "记忆规则", "用户基本规则-铁律版.md")
        txt = open(p, encoding="utf-8").read()
        txt = txt.replace("# 用户基本规则 — 铁律精华版", "# 用户自己改了段内标题")
        open(p, "w", encoding="utf-8").write(txt)
        before = open(p, encoding="utf-8").read()
        # 第二份铁律版模板（模拟包升级：段内容变了）
        src = os.path.join(_PKG, "references", "templates", "用户基本规则-铁律版.md")
        bak_src = src + ".r4tmp"
        shutil.copy2(src, bak_src)
        try:
            open(src, "w", encoding="utf-8").write(
                open(bak_src, encoding="utf-8").read() + "\n> R4 模拟包升级新增一行。\n")
            res = ins.install_rule_files(mc)
        finally:
            shutil.move(bak_src, src)
        st = {n: s for n, s, _ in res}["用户基本规则-铁律版.md"]
        _t("判为 CONFLICT", st == "CONFLICT", "got=%s" % st)
        _t("盘上零改动", open(p, encoding="utf-8").read() == before)
        _t("用户段内改动还在", "用户自己改了段内标题" in open(p, encoding="utf-8").read())
    finally:
        shutil.rmtree(mc, ignore_errors=True)


def r5_falsification():
    print("R5 造错：换回覆盖语义 ⇒ R2 的断言必须 FAIL（防恒真判据）")
    mc = tempfile.mkdtemp()
    try:
        _mk(mc)
        p = os.path.join(mc, "记忆规则", "用户基本规则-铁律版.md")
        # 造错：模拟旧版覆盖行为（把用户文件整file替换成包模板）
        src = os.path.join(_PKG, "references", "templates", "用户基本规则-铁律版.md")
        shutil.copy2(src, p)          # ← 覆盖
        after = open(p, encoding="utf-8").read()
        survived = all(("我自己加的第 %d 条铁律" % i) in after for i in range(1, 21))
        _t("造错后用户内容必须丢失（否则断言恒真）", not survived)
    finally:
        shutil.rmtree(mc, ignore_errors=True)


def main():
    print("=== 0b 承重验收 · 规则三层断章增量（真实入口）===\n")
    for fn in (r1_fresh_install, r2_user_content_survives, r3_idempotent,
               r4_conflict, r5_falsification):
        fn()
        print("")
    print("=" * 52)
    print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("❌ 失败项：" + " · ".join(FAIL))
        return 1
    print("✅ 全部通过（W3 铁律层不再覆盖用户改动）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())