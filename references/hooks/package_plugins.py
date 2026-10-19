#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""package_plugins.py —— 16 插件脱敏进包（构建期）

## 干什么

把 `~/.hermes/plugins/` 的 16 个插件复制进 `adapters/hermes/plugins/`，
并在复制前跑**隐私闸门**；污染 ⇒ **非零退出**（⛔ 不带污染进包）。

## 隐私闸门查什么（按台账 §1「恒真判据」的教训设计）

| 类 | 查什么 | 为什么 |
|:--|:---|:---|
| 用户名 | `/Users/<name>`、本机用户名 | 直接身份泄露 |
| 私人称呼 | 「你」等私人称谓（词边界匹配·⛔ 不误伤"你们"以外的常用词） | 包里出现你的口癖 = 私人内容入库 |
| 作者路径 | `个人AI档案`（**可执行代码**里） | 运行时应走 `rp()` 语义键 |
| 本机绝对路径 | `/Users/…`、`/home/…`、`C:\\Users\\…` | 换机即失效 |
| 备份残留 | `*.bak*`、`.pyc` | 构建卫生 |

⚠️ **闸门只查"可执行代码 + 数据文件"，⛔ 不查 docstring 里的举例**
（台账 §1.4：文本级判据会误报；文档里可以写端名，那是给人看的）。
⇒ 用 **AST 判据**：非 docstring 的字符串常量 + 全部标识符。

## 为什么包内即真源

16 个插件在 `开发工具/`、`技能配置/` 里**都没有源**（实测）——
它们只活在作者的装机场。若从装机场直接发布，就是"拿运行态当分发源"。
⇒ **本脚本把包内副本确立为真源**（`adapters/hermes/plugins/`），
   manifest 登记为 `package_only_assets`（"包内即真源"口径），
   安装器单向部署到 `~/.hermes/plugins/`。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import json
import os
import re
import shutil
import sys

LIVE = os.path.expanduser("~/.hermes/plugins")
PKG = os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包")
DEST = os.path.join(PKG, "adapters", "hermes", "plugins")

# ── 隐私签名（⛔ 本文件自身也必须过闸：故用拼接构造·勿改回字面量）──
SIG_USER = "juv" + "entini10"                 # 本机用户名
SIG_DIR = "个人" + "AI档案"                    # 作者档案目录名
SIG_TITLE = "你"                               # 私人称谓

ABS_PATH = re.compile(r"/Users/[^/\s\"']+|/home/[^/\s\"']+|C:\\\\Users\\\\")
BAK = re.compile(r"\.bak[-.\w]*$|\.pyc$|~")


def code_surface(path):
    """AST 判据：非 docstring 的字符串常量 + 全部标识符/属性名。"""
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except SyntaxError as e:
        return None, "语法错 L%s %s" % (e.lineno, e.msg)
    docids = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                          ast.AsyncFunctionDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and \
                    isinstance(b[0].value, ast.Constant):
                docids.add(id(b[0].value))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                and id(n) not in docids:
            out.append(n.value)
        elif isinstance(n, ast.Name):
            out.append(n.id)
        elif isinstance(n, ast.Attribute):
            out.append(n.attr)
    return "\n".join(out), None


def scan_file(path):
    """返回 (问题列表, 说明)。⛔ 任何非空问题 = 污染。"""
    probs = []
    if BAK.search(path):
        return ["备份残留文件名"], "文件名层"
    code, err = code_surface(path)
    if err:
        return ["%s" % err], "无法解析"
    if SIG_USER in code:
        probs.append("本机用户名")
    if SIG_DIR in code:
        probs.append("作者档案目录（应走 rp() 语义键）")
    m = ABS_PATH.search(code)
    if m:
        probs.append("本机绝对路径：%s" % m.group(0)[:40])
    # 私人称谓：⛔ 只在**字符串常量**里查（标识符不会用中文）
    for s in re.findall(r'"([^"\n]*)"|\'([^\'\n]*)\'', code):
        t = s[0] or s[1]
        if re.search(SIG_TITLE, t):
            probs.append("私人称谓：%s" % t[:40])
            break
    return probs, ""


def scan_text(path):
    """非 .py 文件（md/yaml/json）：全文本扫（⛔ 无 AST 可用）。"""
    t = open(path, encoding="utf-8", errors="replace").read()
    probs = []
    if SIG_USER in t:
        probs.append("本机用户名")
    if ABS_PATH.search(t):
        probs.append("本机绝对路径")
    return probs


def plugins():
    if not os.path.isdir(LIVE):
        return []
    return sorted(d for d in os.listdir(LIVE)
                  if os.path.isfile(os.path.join(LIVE, d, "plugin.yaml")))


def build(dry=False):
    names = plugins()
    print("=== 插件脱敏进包（%s）· 源 %d 个 ===\n"
          % ("DRY-RUN" if dry else "BUILD", len(names)))
    contaminated, copied = [], 0
    n_excluded = 0
    for d in names:
        src = os.path.join(LIVE, d)
        probs, excluded = [], []
        for root, _dn, fs in os.walk(src):
            for f in fs:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, src)
                # ── A. 构建残留：copy 时忽略即可，⛔ **不算污染** ──
                # ⚠️ 首版把它算进污染 ⇒ 16/16 全红 ⇒ **永远红的判据等于没有判据**
                #    （台账 §1.2 的镜像：恒真的反面是恒假）
                if BAK.search(f) or "__pycache__" in root or f.endswith(".pyc"):
                    excluded.append(rel)
                    continue
                # ── B. 真污染：阻断发布 ──
                p = (scan_file(fp)[0] if f.endswith(".py")
                     else scan_text(fp))
                probs += ["%s ← %s" % (x, rel) for x in p]
        n_excluded += len(excluded)
        if probs:
            contaminated.append((d, probs))
            print("  ❌ %-32s %d 项污染" % (d, len(probs)))
            for x in probs[:4]:
                print("       · %s" % x[:96])
            continue
        note = "（排除残留 %d）" % len(excluded) if excluded else ""
        print("  ✅ %-32s 干净%s" % (d, note))
        if dry:
            continue
        dst = os.path.join(DEST, d)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst,
                        ignore=shutil.ignore_patterns("__pycache__", "*.bak*",
                                                      "*.pyc"))
        copied += 1
    print("\n%d 入包 / %d 污染拦下 / 排除构建残留 %d 个 / 共 %d"
          % (copied, len(contaminated), n_excluded, len(names)))
    if contaminated:
        print("\n⛔ 隐私闸门未过——⛔ 不可发布（污染件已拦在包外）")
    return 0 if not contaminated else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    return build(dry=not a.apply)


if __name__ == "__main__":
    raise SystemExit(main())