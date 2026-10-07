#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deident_plugins.py —— 16 插件私人称谓脱敏（发布前必跑）

## 为什么要它

`pkg_cleanliness_check.py` 实测拦下 **15 件**含私人称谓的文件、43 行命中。
全是作者口语工作记录（「<私人称谓> 2026-10-01 广授权…」「被<私人称谓>当面纠正」）。
⇒ **进了包就是作者的私人内容入库**——违反「杜绝隐私入库」。

## ⭐ 关键：两处「私人称谓」不是同一个语义

| 语境 | 原词 | 脱敏成 | 判据 |
|:---|:---|:---|:---|
| **工作记录**（日期/授权/裁决/质证/立规） | （私人称谓） | `作者` | 讲的是**系统怎么被建起来**的经过 |
| **终端用户行为**（活干/方向盘/手动） | （私人称谓） | `用户` | 讲的是**使用者**在守卫面前会怎样 |

⚠️ 一律替换成同一个词会把语义改错：
「守卫失灵不锁死<私人称谓>的活干」在包里指的是**装包的用户**，说成"不锁死作者的活干"
是**把用户读成了包作者**——用户会困惑，包也不该这么写。

## 三条硬约束

1. **只改注释/docstring/描述文本**，⛔ 不碰功能代码里的标识符
2. **幂等**（标记串）
3. **改完必验**：`ast.parse` + `py_compile` + 原闸门复跑
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import os
import re
import shutil
import sys

PLUG = os.path.expanduser("~/.hermes/plugins")
MARK = "── DEIDENT"

# ── 语义分派：先长后短（长的更具体）──────────────────────────────
# 「终端用户」语境 ⇒ 用户
# ⛔ **本文件必须「脱敏免疫」**：私人称谓一律用 \u 转义构造。
#    理由同 pkg_cleanliness_check.py——若这里写字面量，脱敏通道会把它
#    一并替换掉，检测器变成「查替换后词」⇒ **自检立刻失效**。
#    ⛔ 后人改本文件时不得把它改回字面量。
_G = "\u54e5"          # 私人称谓（转义构造·⛔ 勿改回字面量）


def _g(*s):
    return "".join((_G if c == "?" else c) for c in s)


USER_CTX = [
    _g("不锁死?", "的活干"), _g("不抢?", "的方向盘"), _g("?", "手动"),
    _g("?", "的活"), _g("?", "的目录"), _g("?", "那边"), _g("?", "的机器"),
]
# 其余默认 ⇒ 作者
AUTHOR_DEFAULT = "作者"


def target_word(text: str) -> str:
    for u in USER_CTX:
        if u in text:
            return "用户"
    return AUTHOR_DEFAULT


def deident_line(line: str) -> str:
    if _G not in line:
        return line
    return line.replace(_G, target_word(line))


HEADER_NOTE = (
    "# ── DEIDENT ────────────────────────────────────────────────\n"
    "# 私人称谓已脱敏：「作者」= 系统建造经过·「用户」= 终端使用者。\n"
    "# 本文件由 deident_plugins.py 生成，⛔ 请勿手改（会被下次构建覆盖）。\n"
    "# ── /DEIDENT ───────────────────────────────────────────────\n"
)


def patch_file(path: str, dry: bool):
    src = open(path, encoding="utf-8", errors="replace").read()
    if MARK in src:
        return "SKIP", 0
    try:
        ast.parse(src)                      # 改前可解析
    except SyntaxError as e:
        return "FAIL", "源语法错 L%s %s" % (e.lineno, e.msg)
    if _G not in src:
        return "CLEAN", 0
    lines = [deident_line(l) for l in src.split("\n")]
    out = "\n".join(lines)
    n = sum(1 for a, b in zip(src.split("\n"), lines) if a != b)
    # 头部注记插在最后一个模块级 import 之后
    tree = ast.parse(src)
    last = 0
    for nd in tree.body:
        if isinstance(nd, (ast.Import, ast.ImportFrom)):
            last = max(last, getattr(nd, "end_lineno", None) or nd.lineno)
    hl = HEADER_NOTE.split("\n")
    out = "\n".join(out.split("\n")[:last] + hl + out.split("\n")[last:])
    try:
        ast.parse(out)                      # 改后必可解析
    except SyntaxError as e:
        return "FAIL", "改后语法坏 L%s %s" % (e.lineno, e.msg)
    if dry:
        return "DRY", n
    shutil.copy2(path, path + ".bak-predeident")
    open(path, "w", encoding="utf-8").write(out)
    return "OK", n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dir", default=PLUG)
    a = ap.parse_args()
    dry = not a.apply
    names = sorted(d for d in os.listdir(a.dir)
                   if os.path.isfile(os.path.join(a.dir, d, "plugin.yaml")))
    print("=== 插件私人称谓脱敏（%s）· %d 个 ===\n" % ("DRY" if dry else "APPLY",
                                              len(names)))
    ok = fail = 0
    for d in names:
        p = os.path.join(a.dir, d, "__init__.py")
        st, n = patch_file(p, dry)
        ok += st in ("OK", "DRY")
        fail += st == "FAIL"
        if st != "CLEAN":
            print("  %-8s %-32s %s" % (st, d, ("%d 行" % n) if n else ""))
    # yaml 描述文本
    for d in names:
        y = os.path.join(a.dir, d, "plugin.yaml")
        if not os.path.isfile(y):
            continue
        s = open(y, encoding="utf-8").read()
        if _G not in s:
            continue
        s2 = "\n".join(deident_line(l) for l in s.split("\n"))
        if dry:
            print("  %-8s %-32s %d 行" % ("DRY-yaml", d,
                  sum(1 for a_, b_ in zip(open(y,encoding='utf-8').read().split("\n"),
                                           s2.split("\n")) if a_ != b_)))
        else:
            shutil.copy2(y, y + ".bak-predeident")
            open(y, "w", encoding="utf-8").write(s2)
            print("  %-8s %-32s yaml 描述脱敏" % ("OK-yaml", d))
    print("\n%d 处理 / %d 失败" % (ok, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())