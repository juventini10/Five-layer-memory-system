#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_overlay_batch.py —— 把覆盖层**批量应用**到 17 件作者态脚本

## 干什么

给每个目标文件在**模块级常量定义之后**插入：

```python
# ── 布洛陀发布包·路径覆盖层（装包时生成本机实况；作者侧运行=无操作）──
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass
```

## 为什么是「插入」而不是「重写」

- 作者侧 `开发工具/` 继续维护**唯一真源**（933 行原样不动）
- 包侧靠生成的 `path_override.py` 改值
- ⛔ **无第二份清单 ⇒ 无漂移**（cross-platform §二·七 SSOT 单一真源）

## 插入点怎么定（⛔ 不能瞎插）

必须落在**所有模块级赋值之后、第一个 `def`/`class` 之前**。
理由：插早了 ⇒ 后面的常量定义会把覆盖值**又写回作者路径** ⇒ 覆盖层静默失效。

⇒ 本脚本**逐件校验插入点**：
1. 插完后 AST 里必须能读到 `apply_override` 调用
2. 该行必须**晚于**最后一个 `模块级 = ...` 赋值
3. 语法必须仍可解析（`ast.parse`）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import os
import re
import shutil
import sys

ARCH = os.path.expanduser("[记忆共享中心]")
DEV = os.path.join(ARCH, "开发工具")
PKG_S = os.path.join(ARCH, "发布库/五层记忆系统/布洛陀-全平台安装包/references/scripts")

# A 类 12 + B 类 5 = 17（端中立 / 多端共用）
TARGETS = [
    "_hermes_transcript_adapter", "change_reflux_guard", "content-gate",
    "evolution_deviation", "guard_index_pointer", "guard_registry_check",
    "hermes_read_evidence_guard", "registry_precheck_guard",
    "report_backlog_guard", "route_evolution_suggest",
    "self_optimization_engine", "triwich_closeout_guard",
    "platform_adaptation_check", "panel_snapshot", "hermes_inject_chain_guard",
    "hermes_plugin_health_guard", "record_card_trigger",
]

MARK = "── 布洛陀发布包·路径覆盖层"
SNIPPET = '''

# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass
'''


def find_src(base: str):
    for root, _dn, fs in os.walk(DEV):
        if base + ".py" in fs and "site-packages" not in root:
            return os.path.join(root, base + ".py")
    return None


def already_patched(text: str) -> bool:
    return MARK in text


def last_module_assign_end(tree) -> int:
    """最后一个**模块级**赋值的**结束**行号（1-based·可安全作为插入点）。

    ⚠️ ⛔ **必须用 `end_lineno` 而不是 `lineno`**——首版用 `lineno`，
    对多行赋值会插在语句**中间**，直接把语法劈坏（实测 4/17 件当场炸）：
        DEV = os.path.expanduser(     ← 插在这里
            os.path.expanduser("~/脚本中心")    ← 变成孤儿
        )
    """
    last = 0
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            last = max(last, getattr(n, "end_lineno", None) or n.lineno)
    return last


def first_def_or_class_lineno(tree) -> int:
    """首个函数/类定义的行号；没有则返回 0（⛔ 不返回 None·调用方要拿它比大小）。"""
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return n.lineno
    return 0


def patch_one(path: str, dry: bool = False):
    """返回 (状态, 说明)"""
    src = open(path, encoding="utf-8", errors="replace").read()
    if already_patched(src):
        return "SKIP", "已有覆盖块"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return "FAIL", "源文件语法错：%s" % e

    last_assign = last_module_assign_end(tree)
    first_def = first_def_or_class_lineno(tree)
    if not last_assign:
        return "FAIL", "找不到模块级赋值（插入点无从判断）"

    if first_def and last_assign > first_def:
        # 常量定义在 def 之后（少见）——退而求其次插在文件末尾
        insert_at = len(src.split("\n"))
        where = "文末（模块级赋值晚于首个 def）"
    else:
        insert_at = last_assign
        where = "L%d 后（末个模块级赋值）" % last_assign

    lines = src.split("\n")
    new_lines = lines[:insert_at] + SNIPPET.strip("\n").split("\n") + lines[insert_at:]
    out = "\n".join(new_lines)

    # ── 校验：语法仍可解析 ──
    try:
        ast.parse(out)
    except SyntaxError as e:
        return "FAIL", "插入后语法坏：%s" % e

    if dry:
        return "DRY", where
    # 写前备份（铁律005）
    try:
        shutil.copy2(path, path + ".bak-preoverlay")
    except Exception:
        pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    return "OK", where


def main() -> int:
    dry = "--apply" not in sys.argv
    ok = fail = skip = 0
    print("=== 覆盖层批量应用（%s）===\n" % ("DRY-RUN" if dry else "APPLY"))
    print("%-34s %-7s %s" % ("件", "状态", "插入点"))
    print("-" * 72)
    for base in TARGETS:
        p = find_src(base)
        if not p:
            print("%-34s %-7s 源未找到" % (base, "FAIL"))
            fail += 1
            continue
        st, msg = patch_one(p, dry=dry)
        if st == "OK":
            ok += 1
        elif st == "SKIP":
            skip += 1
        else:
            fail += 1
        print("%-34s %-7s %s" % (base, st, msg))
    print("\n%d 应用 / %d 跳过 / %d 失败" % (ok, skip, fail))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())