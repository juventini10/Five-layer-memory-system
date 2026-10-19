#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_live_gate.py —— 活插件三关闸门（⛔ 由 2026-10-02 重大事故逼出来的）

## 为什么有这个文件

给 16 个插件注入 `rp()` 路径解析头后，作者在跑的 Hermes 端**当场全挂**
（16/16 `TypeError: 'NoneType' object is not callable`）。
根因不是语法——`py_compile` 全绿。**根因是"语法对 ≠ 能跑"。**

⇒ 本闸门把承重标准**固化成机械检查**，⛔ 不再依赖"下次记得实跑"。

## 三关（缺一不可）

| 关 | 检查 | 抓什么 |
|:--|:---|:---|
| **G1 语法** | `ast.parse` / `py_compile` | 写坏了 |
| **G2 实导** | 真 `exec_module` 加载每个插件 | 头部解析失败·`rp = None`·import 链断 |
| **G3 真取值** | `rp("devtools")` 返回**存在的绝对路径** | 声明缺键·解析器落到错文件 |

⚠️ **G2/G3 是本闸门的核心**——只跑 G1 会给出"全绿"的假安全感
（这正是 09:55 事故的判据形态：台账 §1「恒真判据」）。

## 用法

```
python3 plugin_live_gate.py                # 全检
python3 plugin_live_gate.py --json         # 机器可读
```

⛔ 退出码：`0`=全过 · `1`=有失败（发布/部署前必须为 0）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import importlib.util as il
import json
import os
import subprocess
import sys

# 🔴 2026-10-11 隔离根治（沙箱实测逮到）：原为硬编码 `~/.hermes/...` ⇒ 隔离验证时
#    闸门仍去读**真机**声明与插件目录 ⇒ ①验的不是本次部署（假绿）②真机被间接消费。
#    铁律「会写/会读运行面的闸须带隔离 cfg_root」在本件的欠账。
#    ✅DO 取值优先级：`--cfg-root` 显式参数 › `DOENGLINGZ_CONFIG_DIR` 环境变量 › 默认 `~/.hermes`。
#    ⛔DO NOT 回落时静默——回落是恒真判据的制造机，故回落值打印一行来源。
def _resolve_cfg(argv):
    cfg = None
    if "--cfg-root" in argv:
        i = argv.index("--cfg-root")
        if i + 1 < len(argv):
            cfg = argv[i + 1]
    if not cfg:
        cfg = os.environ.get("DOENGLINGZ_CONFIG_DIR") or None
    if cfg:
        return os.path.expanduser(cfg), "--cfg-root/DOENGLINGZ_CONFIG_DIR"
    return os.path.join(os.path.expanduser("~"), ".hermes"), "默认值(~/.hermes)"

_CFG_ROOT, _CFG_SRC = _resolve_cfg(sys.argv[1:])
PLUG = os.path.join(_CFG_ROOT, "plugins")
# 声明文件落点（安装器生成）——闸门要验的就是它
CFG = os.path.join(_CFG_ROOT, "doenglingz")
DECL = os.path.join(CFG, "runtime_paths.json")
RESOLVER = os.path.join(CFG, "runtime_paths.py")

# 冒烟取值用的键（必须存在于声明，且落点应真实存在）
SMOKE_KEYS = ("archive_root", "devtools", "worklog")


def plugins():
    if not os.path.isdir(PLUG):
        return []
    return sorted(
        os.path.join(PLUG, d, "__init__.py")
        for d in os.listdir(PLUG)
        if os.path.isfile(os.path.join(PLUG, d, "plugin.yaml")))


def g0_prereq():
    """前置：解析器与声明必须都在（否则 G2/G3 必然失败，先说清原因）。"""
    out = []
    for label, p in (("解析器", RESOLVER), ("声明", DECL)):
        out.append((label, os.path.isfile(p), p))
    return out


def g1_syntax(paths):
    bad = []
    for p in paths:
        try:
            ast.parse(open(p, encoding="utf-8", errors="replace").read())
        except SyntaxError as e:
            bad.append((os.path.basename(os.path.dirname(p)),
                        "L%s %s" % (e.lineno, e.msg)))
    return bad


def g2_import(paths):
    """真加载：⛔ 这一关是 09:55 事故的直接拦截点。"""
    bad = []
    for p in paths:
        d = os.path.basename(os.path.dirname(p))
        code = ("import importlib.util as il,sys;"
                "s=il.spec_from_file_location('m',sys.argv[1]);"
                "m=il.module_from_spec(s);s.loader.exec_module(m);"
                "sys.exit(0 if callable(getattr(m,'rp',None)) else 3)")
        r = subprocess.run([sys.executable, "-c", code, p],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            continue
        if r.returncode == 3:
            bad.append((d, "rp 不可调用（解析器未载入）"))
        else:
            last = (r.stderr or "").strip().split("\n")[-1][:90]
            bad.append((d, last))
    return bad


def g3_values():
    """声明真能取值且落点存在。"""
    if not os.path.isfile(RESOLVER):
        return [("runtime_paths", "解析器缺失：%s" % RESOLVER)]
    code = ("import sys;sys.path.insert(0,%r);"
            "from runtime_paths import rp;"
            "import os,json;"
            "out={};"
            "\nfor k in %r:\n"
            "    try:\n"
            "        v=rp(k); out[k]=(v, os.path.isdir(v))\n"
            "    except Exception as e:\n"
            "        out[k]=('ERR:'+str(e)[:60], False)\n"
            "print(json.dumps(out,ensure_ascii=False))"
            % (CFG, list(SMOKE_KEYS)))
    r = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        return [("runtime_paths", (r.stderr or "").strip()[-90:])]
    data = json.loads(r.stdout.strip().split("\n")[-1])
    bad = []
    for k, (v, ok) in data.items():
        if not ok:
            bad.append((k, "取值失败或落点不存在：%s" % v))
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cfg-root", default=None,
                    help="配置根（隔离验证用）·缺省回落 DOENGLINGZ_CONFIG_DIR 再回落 ~/.hermes")
    a = ap.parse_args()
    print("[plugin_live_gate] 配置根=%s（来源：%s）" % (_CFG_ROOT, _CFG_SRC))

    paths = plugins()
    res = {"plugin_count": len(paths), "g0": [], "g1": [], "g2": [], "g3": []}

    for label, ok, p in g0_prereq():
        if not ok:
            res["g0"].append([label, "缺失：%s" % p])
    res["g1"] = [list(x) for x in g1_syntax(paths)]
    if res["g0"]:
        # ⛔ 前置没过就不跑 G2/G3——否则报一堆下游噪音，掩盖真因
        res["g2"] = [["<skipped>", "前置未过，跳过实导（否则全是下游噪音）"]]
        res["g3"] = [["<skipped>", "前置未过，跳过取值"]]
    else:
        res["g2"] = [list(x) for x in g2_import(paths)]
        res["g3"] = [list(x) for x in g3_values()]

    total = sum(len(res[k]) for k in ("g0", "g1", "g2", "g3"))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("=== 活插件三关闸门 ===\n插件数：%d\n" % res["plugin_count"])
        for g, name in (("g0", "G0 前置（解析器+声明在位）"),
                        ("g1", "G1 语法"),
                        ("g2", "G2 实导（真 exec_module）"),
                        ("g3", "G3 真取值")):
            items = res[g]
            print("%-32s %s" % (name, "✅ 全过" if not items
                                else "❌ %d 项" % len(items)))
            for k, v in items:
                print("    · %-30s %s" % (k, v))
        print("\n%s" % ("✅ 三关全过" if total == 0
                        else "❌ 共 %d 项失败——⛔ 不可发布/部署" % total))
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())