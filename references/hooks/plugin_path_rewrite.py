#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_path_rewrite.py —— 16 插件路径参数化（AST 节点级改写·⛔ 不按行正则）

## 为什么必须 AST 节点级（两次失败换来的）

| 失败 | 症状 | 对应台账 |
|:---|:---|:---|
| v1 按**行**正则 | 0 命中——实际形态是**跨行**的 `expanduser(\\n "…"\\n)` | §3.1 锚点 |
| v1 按 `ast.walk` 找 import 锚点 | 抓到**函数内**的 import ⇒ 头部插进 `try/except` 中间 ⇒ **11/16 语法炸** | §1.4 判据自身写错 |

⇒ **正解**：AST 找目标 `Call` 节点 → 取精确源码区间整体替换 → **倒序**施加。
⇒ ⛔ **正则只用来在字符串字面量里认路径，不用来定位代码结构。**
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import ast
import os
import re
import shutil
import sys
from typing import List, Tuple

PLUG = os.path.expanduser("~/.hermes/plugins")

MARK = "── BULUOTUO-PATH-PARAM"

HEADER = '''# ── BULUOTUO-PATH-PARAM ───────────────────────────────────────
# 布洛陀发布包·路径参数化：作者态落点（"~/<记忆中心>/…"）改为读
# runtime_paths 声明的**语义键**——键表达职责，落点由安装器填，
# 所以用户的记忆中心叫什么都行。⛔ 公共件不得含端名/作者路径。
try:
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "scripts"))
    from runtime_paths import rp
except Exception as _rp_exc:   # ⛔ 解析器不可用 = 安装不完整·必须显形（2026-10-09 根治）
    raise RuntimeError(
        "布洛陀运行路径解析器（runtime_paths）不可用：%s: %s ⇒ 运行路径声明缺失/损坏或解析器不在探测路径，运行安装器重新生成。⛔ 不回落 rp=None——否则下游只报 NoneType（不指向根因）。"
        % (type(_rp_exc).__name__, _rp_exc)
    ) from _rp_exc
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────
'''

KEYMAP = [
    ("开发工具/知识联邦引擎", "kb_engine"),
    ("开发工具/路由家族", "custom_route"),
    ("开发工具/Skill路由引擎", "devtools"),
    ("开发工具", "devtools"),
    ("工作日志/系统日志", "worklog"),
    ("工作日志", "worklog"),
    ("数字分身/K2切片蒸馏/slices", "twin_slices"),
    ("数字分身/K2切片蒸馏", "k2_slices"),
    ("数字分身", "twin"),
    ("知识库", "knowledge"),
    ("技能配置", "skills"),
    ("记忆蓝图", "blueprint"),
    ("脚本中心", "script_center"),
    ("记忆琥珀", "memory_amber"),
    # 自定义层下的路由家族（作者态有两种落点，用户侧统一走 custom_route）
    ("自定义层/待完成工作/路由家族", "custom_route"),
    ("自定义层/路由家族", "custom_route"),
]

SKIP_FUNCS = ("selftest", "self_test")


def key_for(tail: str):
    """作者路径尾巴 → (语义键, 剩余子目录元组)。⛔ 未命中返回 (None, ())。"""
    t = (tail or "").strip("/")
    if not t:
        return "archive_root", ()
    for pref, key in KEYMAP:
        if t == pref:
            return key, ()
        if t.startswith(pref + "/"):
            return key, tuple(t[len(pref) + 1:].split("/"))
    return None, ()


def _cs(node):
    return node.value if isinstance(node, ast.Constant) and \
        isinstance(node.value, str) else None


def find_author_calls(tree) -> List[Tuple]:
    """找出参数里含作者路径的 expanduser / join 调用（⛔ 跳过自测夹具）。"""
    skip_lines = set()
    for n in ast.walk(tree):
        nm = getattr(n, "name", "")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                any(k in nm.lower() for k in SKIP_FUNCS):
            for s in ast.walk(n):
                if isinstance(s, ast.Constant) and isinstance(s.value, str):
                    skip_lines.add(s.lineno)

    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Attribute):
            continue
        if n.func.attr not in ("expanduser", "join"):
            continue
        strs = [_cs(a) for a in n.args]
        strs = [s for s in strs if s is not None]
        hit = None
        for s in strs:
            if n.func.attr == "expanduser" and s.startswith("~/个人AI档案"):
                # ⛔ 必须剥掉整个 "~/个人AI档案"（首版只剥 "~/" 留下 "个人AI档案/…"，
                #    而 key_for 的键不含该前缀 ⇒ 全部落空 ⇒ route-audit-hook 0 改 18 残留）
                hit = s[len("~/个人AI档案"):].strip("/")
                break
            if n.func.attr == "join" and s == os.path.expanduser("~"):
                hit = ""
                break
            if n.func.attr == "join" and s.startswith("个人AI档案/"):
                hit = s[len("个人AI档案/"):]
                break
        if hit is None:
            continue
        if any(ln in skip_lines for ln in
               range(n.lineno, (n.end_lineno or n.lineno) + 1)):
            continue
        if n.func.attr == "join" and hit == "":
            parts = []
            for a in n.args[2:]:
                sv = _cs(a)
                if sv is None:
                    parts = None
                    break
                parts.append(sv)
            if parts:
                hit = "/".join(parts)
        key, rest = key_for(hit)
        if key:
            out.append((n, key, rest))
    return out


def _selftest_ranges(src):
    """自测函数的行区间（⛔ 其内的路径是**测试输入**，不能改·台账 §3.3）。"""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        nm = getattr(n, "name", "")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                any(k in nm.lower() for k in SKIP_FUNCS):
            out.append((n.lineno, n.end_lineno or n.lineno))
    return out


# ⛔ 正则**只用来在文本里认调用**，⛔ 不用来定位代码结构。
#    `\s*` 天然跨多行 ⇒ `expanduser(\n  "…"\n)` 一次命中；
#    匹配范围只是那个调用本身 ⇒ 行内/结构里的逗号括号必然存活。
_PATTERNS = (
    # os.path.expanduser("[记忆共享中心]/<尾巴>")
    re.compile(r"os\.path\.expanduser\(\s*[\"']~/个人AI档案([^\"']*)[\"']\s*\)"),
    # os.path.join(X, "个人AI档案/<尾巴>")
    re.compile(r"os\.path\.join\(\s*[A-Za-z_]\w*\s*,\s*[\"']个人AI档案/?"
               r"([^\"']*)[\"']\s*\)"),
    # os.path.join(X, os.path.expanduser("[记忆共享中心]"), "<尾巴>" [, "<尾巴2>" …])
    re.compile(r"os\.path\.join\(\s*[A-Za-z_]\w*\s*,\s*[\"']个人AI档案[\"']"
               r"((?:\s*,\s*[\"'][^\"']*[\"'])*)\s*\)"),
)


def rewrite(src: str):
    """把作者路径改写成 rp("<语义键>")。返回 (新源码, 改了几处, 残留几行)。

    **为什么不用 AST 偏移**（v2/v3 各栽一次）：
      v2 行+列混算 → 多行节点折叠后行号移位
      v3 行内字符串替换 → 列表元素尾随逗号被吞
    ⇒ 本版：AST **只用来圈出"不许改的行区间"**（自测体），
      替换本身走文本正则——正则的匹配边界就是调用的边界，
      **结构里的逗号/括号/续行天然不受影响**。
    """
    skip = _selftest_ranges(src)
    lines_at = [0]
    for ln in src.split("\n"):
        lines_at.append(lines_at[-1] + len(ln) + 1)

    def in_skip(off):
        for lo, hi in skip:
            if lines_at[lo - 1] <= off < lines_at[hi]:
                return True
        return False

    def rp_expr(tail):
        key, rest = key_for(tail)
        if not key:
            return None
        return "rp(%s)" % ", ".join(['"%s"' % key] + ['"%s"' % p for p in rest])

    n = [0]

    def sub1(m):
        if in_skip(m.start()):
            return m.group(0)
        e = rp_expr(m.group(1))
        if e is None:
            return m.group(0)
        n[0] += 1
        return e

    def sub3(m):
        if in_skip(m.start()):
            return m.group(0)
        parts = re.findall(r"[\"']([^\"']*)[\"']", m.group(1) or "")
        e = rp_expr("/".join(p for p in parts if p))
        if e is None:
            return m.group(0)
        n[0] += 1
        return e

    out = src
    for i, pat in enumerate(_PATTERNS):
        out = pat.sub(sub3 if i == 2 else sub1, out)

    left = sum(1 for ln in out.split("\n")
               if os.path.expanduser("~") in ln and not ln.strip().startswith("#"))
    return out, n[0], left


def last_toplevel_import_end(tree) -> int:
    """⛔ **只取模块级** import（`tree.body`）。

    v1 用 `ast.walk` 抓到函数内的 import，把头部插进 try/except 中间
    ⇒ 11/16 件语法炸（台账 §1.4：判据自身写错比不判更危险）。
    """
    last = 0
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            last = max(last, getattr(n, "end_lineno", None) or n.lineno)
    return last


def patch_plugin(path: str, dry: bool):
    src = open(path, encoding="utf-8", errors="replace").read()
    already = MARK in src
    try:
        tree = ast.parse(src)
        body, n_chg, n_left = rewrite(src)
    except SyntaxError:
        return "FAIL", 0, 0
    if already:
        # 已有头部 ⇒ 本轮只补路径（⛔ 不重复插头部·幂等）
        out = body
    else:
        anchor = last_toplevel_import_end(tree)
        hl = HEADER.split("\n")
        out = "\n".join(body.split("\n")[:anchor] + hl + body.split("\n")[anchor:])
    try:
        ast.parse(out)                      # ⛔ 写盘前必验（台账 §3.1）
    except SyntaxError:
        return "FAIL", 0, 0
    if dry:
        return ("SKIP" if (already and not n_chg) else
                "RESCAN" if already else "DRY"), n_chg, n_left
    if already and not n_chg:
        return "SKIP", 0, 0
    try:
        shutil.copy2(path, path + ".bak-preparam2")
    except Exception:
        pass
    open(path, "w", encoding="utf-8").write(out)
    return ("RESCAN" if already else "OK"), n_chg, n_left


def main() -> int:
    dry = "--apply" not in sys.argv
    plugins = sorted(d for d in os.listdir(PLUG)
                     if os.path.isfile(os.path.join(PLUG, d, "plugin.yaml")))
    print("=== 插件路径参数化（%s）· 插件数 %d ===\n"
          % ("DRY-RUN" if dry else "APPLY", len(plugins)))
    print("%-34s %-6s %6s %6s" % ("插件", "状态", "已改", "残留"))
    print("-" * 60)
    ok = fail = skip = 0
    left = []
    for d in plugins:
        p = os.path.join(PLUG, d, "__init__.py")
        if not os.path.isfile(p):
            continue
        st, n, lf = patch_plugin(p, dry)
        ok += st == "OK"
        fail += st == "FAIL"
        skip += st == "SKIP"
        if lf:
            left.append("%s×%d" % (d, lf))
        print("%-34s %-6s %6d %6d" % (d, st, n, lf))
    print("\n%d 应用 / %d 跳过 / %d 失败" % (ok, skip, fail))
    if left:
        print("\n⚠️ 残留（⛔ 不自动改·需逐条看）：%s" % ", ".join(left))
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())