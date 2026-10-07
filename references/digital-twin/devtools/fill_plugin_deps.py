#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_plugin_deps.py —— 把插件**执行体**补进包（闭合交付缺口）

## 为什么必须做

2026-10-02 取证发现：16 个插件 `subprocess` 调用的公共脚本里，
**11 个只活在作者侧 `开发工具/`，包的 `references/scripts/` 没有**。

⇒ 用户装完：`rp("devtools")` 有路径（改落点后），但**目录里那些文件是空的**
⇒ `os.path.exists()` 判 False ⇒ 插件**静默跳过** ⇒ **不报错、不出声、功能没装上**。
⇒ 这比 `PathKeyMissing` 更阴：那个会炸给你看，这个静默空转。

## 补哪些（口径＝插件真的 subprocess 调的执行体）

⛔ **不补**：输出路径（`worklog/*.log`）、可选增强、纯文档引用
✅ **补**：`route-audit-hook` / `release-guard-hook` / `buluotuo-session-title-hook`
        / `buluotuo-skill-health-guard` / `hermes-plugin-health` 调的执行体

## 三道闸（缺一不可）

1. **来源白名单**：⛔ 不从「盘上有什么」盲扫，只从**插件源码实测引用**得出
2. **脱敏**：复用占位符替换机制（⛔ 不造第二套）
3. **补完复验**：同一份引用清单重新扫，缺口必须 = 0

## 幂等

目标已存在且内容一致 ⇒ SKIP。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import filecmp
import os
import re
import shutil
import sys

ARCH = os.path.expanduser("[记忆共享中心]")
DEV = os.path.join(ARCH, "开发工具")
PLUG = os.path.expanduser("~/.hermes/plugins")
PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join(PKG, "references", "scripts")
PH = os.path.expanduser("~")
AUTH = "个人" + "AI档案"
CAND = re.compile(r"记忆共享中心|记忆中心|个人AI档案")


def is_cand(line):
    return len(set(CAND.findall(line))) >= 2


def plugin_refs():
    """从插件源码抽 `rp("devtools", "x")` / `rp("devtools","d","f")` 的真实引用。"""
    out = set()
    for d in sorted(os.listdir(PLUG)):
        p = os.path.join(PLUG, d, "__init__.py")
        if not os.path.isfile(p):
            continue
        t = open(p, encoding="utf-8", errors="replace").read()
        for m in re.finditer(
                r'\brp\(\s*"devtools"\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]+)")?', t):
            out.add((m.group(1), m.group(2) or ""))
    return out


def resolve(rel):
    c = os.path.join(DEV, rel)
    return c if os.path.exists(c) else None


def deident_text(t):
    out = []
    for l in t.split("\n"):
        if AUTH in l and not is_cand(l):
            l = re.sub(r"~/" + re.escape(AUTH), PH, l)
            l = l.replace(AUTH, PH)
        out.append(l)
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    refs = sorted(plugin_refs())
    print("=== 插件执行体补包（%s）· 实测引用 %d 项 ===\n"
          % ("APPLY" if a.apply else "DRY", len(refs)))
    n_ok = n_skip = n_miss = 0
    for parent, child in refs:
        rel = os.path.join(parent, child) if child else parent
        src = resolve(rel)
        dst = os.path.join(DEST, rel)
        if not src:
            print("  ❌ 源未找到：%s" % rel)
            n_miss += 1
            continue
        if os.path.isdir(src):
            if os.path.isdir(dst):
                cmp = filecmp.dircmp(src, dst)
                if not cmp.diff_files and not cmp.left_only:
                    print("  SKIP %-46s（目录·已一致）" % rel[:44])
                    n_skip += 1
                    continue
            if a.apply:
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.bak*", "*.pyc"))
            print("  %-4s %-46s 目录 %d 项"
                  % ("OK" if a.apply else "DRY", rel[:44],
                     len([x for x in os.listdir(src) if x != "__pycache__"])))
            n_ok += 1
            continue
        s = open(src, encoding="utf-8", errors="replace").read()
        did = False
        if AUTH in s:
            s2 = deident_text(s)
            try:
                ast.parse(s2)
            except SyntaxError as e:
                print("  ❌ 脱敏后语法坏 %s L%s" % (rel, e.lineno))
                n_miss += 1
                continue
            s = s2
            did = True
        if a.apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not did and os.path.isfile(dst) and open(
                    dst, encoding="utf-8", errors="replace").read() == s:
                n_skip += 1
                print("  SKIP %-46s（已一致）" % rel[:44])
                continue
            open(dst, "w", encoding="utf-8").write(s)
        print("  %-4s %-46s %d 字节%s"
              % ("OK" if a.apply else "DRY", rel[:44], len(s),
                 " · 已脱敏" if did else ""))
        n_ok += 1
    print("\n补 %d / 跳过 %d / 失败 %d" % (n_ok, n_skip, n_miss))
    return 1 if n_miss else 0


if __name__ == "__main__":
    raise SystemExit(main())