#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v0.1
"""guard_registry_check.py — 守卫登记一致性检查（根治"上线新守卫漏登记注册表"）。

第一性原理（抄 registry_guards.sh 已验证范式·2026-08-11 根治笔记）：
  "手工维护的名单不是单一真相源，必然漂移；根治=让文件系统/实盘当真相源。"
  本脚本的实盘真相源 = ①settings.json hooks 实挂脚本 ②守卫目录磁盘文件
  比对对象 = 守卫编写规范.md §四注册表（机器可扫表）。
  分级：硬（实挂在 hook 链的 *guard* 未登记）→ alarm；软（仅磁盘存在未登记）→ 提示。
用法：python3 guard_registry_check.py [--report] [--strict]
  --strict 时 alarm → exit 1（默认 exit 0 不阻断对话链）。
"""
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
CFG_ROOT = Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or (HOME / ".workbuddy"))
SETTINGS = CFG_ROOT / "settings.json"
REGISTRY = HOME / os.path.expanduser("[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md")

GUARD_DIRS = [
    HOME / os.path.expanduser("[记忆共享中心]/脚本中心"),
    HOME / os.path.expanduser("[记忆共享中心]/脚本中心"),
    HOME / os.path.expanduser("[记忆共享中心]/脚本中心"),
    CFG_ROOT / "hooks",
]

_GUARD_HINT = re.compile(r"guard|守卫", re.I)
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


def hooked_guards():
    """实挂真相源：settings.json hooks 中文件名含 guard/守卫 的脚本 basename。"""
    out = set()
    try:
        d = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return out
    for _ev, groups in (d.get("hooks") or {}).items():
        for g in groups or []:
            for h in (g.get("hooks") or []):
                cmd = str(h.get("command", ""))
                for tok in cmd.split():
                    base = os.path.basename(tok)
                    if base.endswith((".py", ".sh")) and _GUARD_HINT.search(base):
                        out.add(base)
    return out


def disk_guards():
    """磁盘真相源：守卫目录下 *guard* 文件 basename（排除备份/pycache）。"""
    out = set()
    for d in GUARD_DIRS:
        if not d.is_dir():
            continue
        for p in d.glob("*guard*"):
            if p.is_file() and not any(x in p.name for x in (".bak", "~", ".pyc", "!")) \
                    and not p.name.startswith("."):
                if p.suffix in (".py", ".sh"):
                    out.add(p.name)
    return out


def registered():
    """注册表真相源：守卫编写规范 §四 表格第一列文件名。"""
    out = set()
    try:
        t = REGISTRY.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return out
    in_table = False
    for line in t.splitlines():
        if "STRIP_START:守卫注册表" in line:
            in_table = True
            continue
        if "STRIP_END" in line:
            in_table = False
        if not in_table or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        name = cells[0]
        if name in ("守卫", "------") or set(name) <= set("-: "):
            continue
        m = re.match(r"[\w\-.]+\.(py|sh)", name)
        if m:
            out.add(m.group(0))
    return out


def main():
    report = "--report" in sys.argv
    strict = "--strict" in sys.argv
    hooked = hooked_guards()
    disk = disk_guards()
    reg = registered()

    hard_missing = sorted(n for n in hooked if n not in reg)
    soft_missing = sorted(n for n in disk if n not in reg and n not in hooked)
    alarm = bool(hard_missing)

    if report or alarm:
        print("🧾 守卫登记一致性检查（真相源=settings 实挂 + 磁盘；比对=守卫规范§四注册表）")
        print(f"   实挂守卫 {len(hooked)} · 磁盘守卫 {len(disk)} · 注册表 {len(reg)}")
        if hard_missing:
            print(f"   ❌ 硬缺口（实挂未登记·必须补）：{', '.join(hard_missing)}")
        if soft_missing:
            print(f"   ⚠️ 软提示（磁盘存在未登记·建议补）：{', '.join(soft_missing[:12])}"
                  + (" …" if len(soft_missing) > 12 else ""))
        if not hard_missing and not soft_missing:
            print("   ✅ 全部已登记")
    else:
        print("✅ 守卫登记一致性：通过（实挂守卫均已登记）")

    if strict and alarm:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
