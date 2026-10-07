#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_gates.py —— 发包前**全闸聚合**（编排已有闸门·⛔ 不重造判据）

## 为什么是「编排」而不是「再造一道」

台账 §1.7：**同一事实两套实现 ⇒ 结论相反**。
本包已有三道闸门（各有职责），⛔ 不再写第四道去"顺便都查一遍"。

| # | 闸门 | 查什么 | 归属 |
|:--|:---|:---|:---|
| 1 | `pkg_cleanliness_check.py` | 发布卫生：私人称呼/用户名/.bak/临时残留/状态文件 | 已有·单一真源 |
| 2 | `package_plugins.py` | 插件隐私（AST 判据）+ 构建残留 | 已有 |
| 3 | `plugin_live_gate.py` | 插件三关：语法/实导/真取值 | 已有 |
| 4 | `verify_hermes_runtime.py` | 端上真跑：注册/加载/派发（--expect-from 抓装漏） | 已有 |

⚠️ **任一红 ⇒ 整体红**（⛔ 不做"多数通过就算过"）。
⚠️ 第 3/4 关需要**端上已装**；未装时显 ⚪「跳过·未验证」⛔ 不充绿。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(os.path.dirname(HERE))
PLUGDIR = os.path.join(os.path.expanduser("~"), ".hermes", "plugins")

GATES = [
    # 🔴 发布卫生**带 --fix-cache**（2026-10-02 四踩后根治）：
    #   包内脚本被运行 ⇒ Python 写 __pycache__ ⇒ 本闸报自己造出来的污染。
    #   已修一层（子进程 PYTHONDONTWRITEBYTECODE），但**闸门管不住外部调用方**
    #   （CI / 回归测试 / 人手动跑）⇒ 这里兜底自清，可再生缓存·零风险·幂等。
    #   ⛔ 只清 pycache 一类，其余 7 类污染照报（清一半说干净＝把红读成绿）。
    ("发布卫生", [sys.executable, os.path.join(HERE, "pkg_cleanliness_check.py"),
                  "--fix-cache"]),
    ("插件隐私+残留", [sys.executable, os.path.join(HERE, "package_plugins.py")]),
]
RUNTIME = [
    # 🔴 **用户机夹具**排第一：作者机有 `[记忆共享中心]/脚本中心`，用户机没有。
    #    ⛔ 任何在作者机上跑的验证，对"用户能不能顺利装完"都不成立（2026-10-02 两个真缺陷实测）。
    ("用户机夹具", [sys.executable, os.path.join(HERE, "user_machine_fixture.py")]),
    ("插件三关", [sys.executable, os.path.join(HERE, "plugin_live_gate.py")]),
    ("运行态三层", [sys.executable, os.path.join(HERE, "verify_hermes_runtime.py"),
                    "--expect-from", os.path.join(PKG, "adapters/hermes/plugins")]),
]


def run(label, cmd):
    if not os.path.isdir(PLUGDIR):
        print("  ⚪ %-16s 跳过（端上未装插件·⛔ 不充绿）" % label)
        return None
    # 🔴 **闸门自己不许污染被闸对象**（2026-10-02 实测三次踩）：
    #    子进程 import 同目录模块 ⇒ Python 自动写 __pycache__ 到包内
    #    ⇒ 上一道闸刚跑完，下一道闸（发布卫生）就报"包内污染"——
    #    **闸门制造了它自己要检的缺陷**，人被迫反复手工清理（假绿治理）。
    #    修法=子进程禁写字节码。⛔ 不是豁免 pycache 检查（那是对的），
    #    是让检查方不再生产垃圾。
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200,
                       env=env)
    ok = r.returncode == 0
    print("  %s %-16s rc=%s" % ("✅" if ok else "❌", label, r.returncode))
    if not ok:
        for ln in (r.stdout or r.stderr).strip().split("\n")[-8:]:
            print("      " + ln[:110])
    return ok


def main() -> int:
    print("=== 发包前全闸 ===\n")
    print("[构建期闸门]")
    res = [run(l, c) for l, c in GATES]
    print("\n[端上闸门]")
    res += [run(l, c) for l, c in RUNTIME]
    red = sum(1 for x in res if x is False)
    gray = sum(1 for x in res if x is None)
    print("\n%s" % ("✅ 全闸通过" if red == 0 and gray == 0
                    else ("❌ %d 道红——⛔ 不可发包" % red if red
                          else "⚪ %d 道未验证——⛔ 不可声称'已验证'" % gray)))
    return 1 if (red or gray) else 0


if __name__ == "__main__":
    raise SystemExit(main())
