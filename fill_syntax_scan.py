#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""fill_syntax_scan.py — 装后语法面全量扫描器（本 docstring 用 raw：初版非 raw 时自己中了 \U 雷=本病第三例活证据）

职责：对记忆中心的**装机产物面**（技能配置/脚本中心/知识联邦引擎/数字分身/记忆规则）
全量 .py compile + .json loads——把 _fill 转义雷（\a→BEL、\U→SyntaxError）与任何
填后语法破损从"用户首触即死"左移为"verify 当轮显形"。与 install_scripts.fill_syntax_guard
构成双保险：前者管装机当轮（增量），本件管跨版本存量（全量）。

用法：python3 fill_syntax_scan.py <MC路径> [--quiet]
退出码：0=全绿 1=有雷（逐行明细） 2=参数/路径错误
只读：不修改任何文件。
"""
import sys
import os
import json

# Windows 控制台 cp1252/cp936 守卫（同包 install_scripts.py/data_contamination_check.py 先例；
# 2026-10-11 真机 run32 V9 腿逮出本件缺守卫=首犯，print 🔴/✅ 在 Win 控制台必崩）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

TARGET_DIRS = ["技能配置", "脚本中心", "知识联邦引擎", "数字分身", "记忆规则"]
# 作者机/装机面里不属于"安装产物"的噪声目录（含个人历史备份，炸了也不算装机雷）
SKIP_DIR_NAMES = {".venv", ".venv-st", "__pycache__", "node_modules", "记忆琥珀",
                  "发布库", "_archive", "缓存", "cache"}
SKIP_EXT_FALLBACK = {".pyc", ".pyo"}


def _skip_path(p):
    parts = p.replace("\\", "/").split("/")
    for seg in parts:
        if seg in SKIP_DIR_NAMES or ".bak" in seg or seg.startswith("_archive"):
            return True
    return False


def scan(mc):
    red, checked = [], 0
    for top in TARGET_DIRS:
        root_dir = os.path.join(mc, top)
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and ".bak" not in d]
            if _skip_path(root):
                continue
            for fn in files:
                if ".bak" in fn:
                    continue
                ext = os.path.splitext(fn)[1]
                if ext in SKIP_EXT_FALLBACK:
                    continue
                p = os.path.join(root, fn)
                if ext == ".py":
                    try:
                        # utf-8-sig：BOM 开头 .py 在 import 层合法（文件 I/O 剥 BOM），
                        # 直读 utf-8 会把 BOM 当源码字符误报（2026-10-11 实跑首扫逮到）
                        compile(open(p, encoding="utf-8-sig").read(), p, "exec")
                        checked += 1
                    except (UnicodeDecodeError, OSError):
                        continue                       # 非 utf-8/不可读：不在本判据面
                    except SyntaxError as e:
                        red.append("PY雷 %s: %s" % (p, e))
                elif ext == ".json":
                    try:
                        json.load(open(p, encoding="utf-8-sig"))
                        checked += 1
                    except (UnicodeDecodeError, OSError):
                        continue
                    except json.JSONDecodeError as e:
                        red.append("JSON雷 %s: %s" % (p, str(e)[:80]))
    return red, checked


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    if len(args) != 1:
        print("用法: python3 fill_syntax_scan.py <MC路径> [--quiet]")
        return 2
    mc = os.path.abspath(os.path.expanduser(args[0]))
    if not os.path.isdir(mc):
        print("错误：MC 路径不存在：%s" % mc)
        return 2
    red, checked = scan(mc)
    if not quiet:
        print("装后语法面扫描：%d 件（.py compile + .json loads）" % checked)
        for r in red:
            print("  🔴 " + r)
        if red:
            print("❌ 语法雷 %d 件——逐行明细见上（转义雷形态=路径含 \\a/\\U 等被填字面）" % len(red))
        else:
            print("✅ 装后语法面全绿")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
