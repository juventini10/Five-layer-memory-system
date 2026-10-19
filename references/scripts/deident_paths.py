#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""deident_paths.py —— 把作者目录名换成既有占位符 `~/个人AI档案`

## 为什么不是「发明新机制」

包里**早就有**占位符机制：`install_scripts.py:46` `PLACEHOLDER = os.path.expanduser("~")`,
`_fill()` 在**写盘时**替换，**274 个文件**在用。
⇒ 本脚本**只做一件事**：把漏用占位符、写成作者目录名的地方补上。
⛔ 不引入第二套机制（台账 §1.7：同一事实两套实现 ⇒ 结论相反）。

## 替换规则（⛔ 逐条都有排除，不做无脑 sed）

| 形态 | 处理 | 理由 |
|:---|:--|:---|
| `[记忆共享中心]/…` | → `[记忆共享中心]/…` | 路径形态·写死=用户机器上不存在 |
| `os.path.expanduser("~")` 作 `os.path.join` 段 | → `os.path.expanduser("~")` | 同上 |
| **候选探测列表**（`(…, os.path.expanduser("~"), …)` 多个并列候选） | ⛔ **跳过** | 那是**有意的多候选**（探测用户记忆中心叫啥）·⛔ 不是泄露 |
| **脱敏/检测脚本本体** | ⛔ 跳过 | 它必须写着要检测的模式 |
| 散文里提到书名号《》 | ⛔ 跳过 | 是文档引用不是路径 |
| 本文件自身 | ⛔ 跳过 | 签名构造用拼接·本文件不该出现字面量 |

## 干跑优先 + 逐件报告

⚠️ **默认 DRY**：`--apply` 才写盘。写前备份（铁律005）。
⚠️ 改完**必跑**：`pkg_cleanliness_check` + `privacy_audit` + 承重回归。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import os
import re
import shutil
import sys

PKG = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIGD = "个人" + "AI档案"
PH = os.path.expanduser("~")
TEXT_EXT = (".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".md", ".txt")
EXEMPT_FILES = ("deident_paths.py", "privacy_audit.py", "pkg_cleanliness_check.py",
                "desensitize-guard", "deident_plugins.py", "test_runtime_paths.py")
SKIP_DIR = {"__pycache__", ".git", "node_modules"}

# 候选探测：同一行里出现 ≥2 个记忆中心候选名 ⇒ 是探测列表，跳过
CAND = re.compile(r"记忆共享中心|记忆中心|个人AI档案")

# S11-a 方向断言(2026-10-04)：PKG 解析越界=立即中止。此工具只允许清洗"发布包"树，
# ⛔禁对生产树(家目录根/[记忆共享中心]/脚本中心)就地改写——12:0x 模板逆向污染事件根治。
_PKG_FORBID = {os.path.expanduser("~"), os.path.expanduser("~"),
               os.path.expanduser("[记忆共享中心]/脚本中心"), os.path.expanduser("[记忆共享中心]/脚本中心")}
if os.path.abspath(PKG) in _PKG_FORBID or os.path.abspath(PKG) == "/":
    print("ABORT(deident_paths): PKG=%s 解析到生产树，方向违规（本工具仅允许发布包根·见S11-a）" % PKG, file=sys.stderr)
    sys.exit(3)



def is_candidate_line(line: str) -> bool:
    """同一行出现 ≥2 个不同候选名 ⇒ 多候选探测列表 ⇒ 跳过该行。"""
    names = set()
    for m in CAND.finditer(line):
        names.add(m.group(0))
    return len(names) >= 2


def convert(text: str):
    out_lines, n, skipped = [], 0, 0
    for ln in text.split("\n"):
        if SIGD not in ln:
            out_lines.append(ln)
            continue
        if is_candidate_line(ln):
            out_lines.append(ln)
            skipped += 1
            continue
        # 散文引用（《》内）不改
        if ("《%s》" % SIGD) in ln or ("「%s」" % SIGD) in ln:
            out_lines.append(ln)
            skipped += 1
            continue
        cnt = ln.count(SIGD)
        out_lines.append(ln.replace(SIGD, PH))
        n += cnt
    return "\n".join(out_lines), n, skipped


def targets():
    for sub in ("adapters", "references"):
        for r, dn, fs in os.walk(os.path.join(PKG, sub)):
            dn[:] = [d for d in dn if d not in SKIP_DIR]
            for f in fs:
                if not f.endswith(TEXT_EXT) or ".bak" in f:
                    continue
                p = os.path.join(r, f)
                if any(x in p for x in EXEMPT_FILES):
                    continue
                if SIGD in open(p, encoding="utf-8", errors="replace").read():
                    yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    dry = not a.apply
    files = list(targets())
    print("=== 作者目录名 → 占位符（%s）· 命中 %d 文件 ===\n"
          % ("DRY" if dry else "APPLY", len(files)))
    tot = ok = bad = 0
    for p in files:
        rel = os.path.relpath(p, PKG)
        src = open(p, encoding="utf-8", errors="replace").read()
        out, n, sk = convert(src)
        if n == 0:
            continue
        tot += n
        if out != src and p.endswith(".py"):
            try:
                ast.parse(out)
            except SyntaxError as e:
                print("  ❌ %-56s 改后语法坏 L%s" % (rel[:54], e.lineno))
                bad += 1
                continue
        if not dry:
            shutil.copy2(p, p + ".bak-predeidentpath")
            open(p, "w", encoding="utf-8").write(out)
        ok += 1
        print("  %-4s %-56s 替换 %d 处%s"
              % ("DRY" if dry else "OK", rel[:54], n,
                 ("·跳过候选行 %d" % sk) if sk else ""))
    print("\n%d 文件处理 / %d 处替换 / %d 语法坏" % (ok, tot, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())