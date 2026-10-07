#!/usr/bin/env python3
# version: v1.0.0
"""WorkBuddy 端注入链健康守卫（端薄适配器·对齐 qodercn/hermes_inject_chain_guard 族）。

## 存在理由（§二·七·〇 动作 3「先查可复用」）

族内 Qoder CN / Hermes 各有 inject_chain_guard，**WB 端没有**——
而 WB 恰是**注入链最重的一端**：UserPromptSubmit 实挂 5 条注入
（route_inject / kb_inject / rule_fragment / doenglingz_inject / session_tail）
+ 1 条投喂（route_miss_feeder）。链越重越需要"链本身"的守卫。

## ⛔ 与 guard_heartbeat_check.py 的分工（防重复造轮子）

| 件 | 管什么 |
|---|---|
| `guard_heartbeat_check.py` | **派发态**：宿主真派发了吗（心跳留痕） |
| 本件 | **链本体**：注入脚本在不在·能不能加载·**数据依赖齐不齐** |

⇒ 两腿互补·⛔ 不互相顶账（Hermes 段判据沉淀②：注册态只证名册有名字，
   不证打卡机有记录；本件管的是"名册里的东西本体是否完好"）。

## 检测项

| # | 项 | 级别 |
|:-:|---|:--:|
| 1 | 注入脚本实体缺失（挂了但文件没了） | RED |
| 2 | 脚本语法不可解析（改坏了·静默失败） | RED |
| 3 | **数据依赖缺失**（脚本引用的路径资产不存在） | RED |
| 4 | 依赖路径无法判定（f-string/拼接·看清再说） | ⚪ 统计 |

## 为什么第 3 项最关键（Hermes 段判据沉淀①）

"接一个组件要连它的数据依赖一起接——**脚本能跑 ≠ 闭环**"。
注入脚本常依赖 router.py / rule_triggers.yaml / K2 切片 / 知识索引——
依赖没了，脚本照样 exit 0，只是**永远注入不了东西**。这是最难发现的静默失效。

⇒ 依赖清单**从脚本源码机械提取**（正则扫路径字面量），⛔ 不手抄清单（防漂移）。

## 纪律

- 只记录不拦截：报告制·默认 exit 0（`--strict` 时 RED 才 exit 1）
- 只读：⛔ 不写任何文件
- 自测：`--self-test` 临时夹具（含变异：好脚本不得凭空告警）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".workbuddy", "settings.json")
INJECT_EVENTS = ("UserPromptSubmit",)
# 路径字面量：只认作者域 / .workbuddy 域（本端资产面·作者域走 _AI_DIR 转义）
_AI_DIR = "\u4e2a\u4ebaAI\u6863\u6848"
_PATH_RE = re.compile(
    r"""["'](~?/[^"']*?(?:%s|\.workbuddy)[^"']*?)["']""" % _AI_DIR)
# 含格式串/拼接的无法静态判定 → 计入 unknown，⛔ 不猜
_DYNAMIC = re.compile(r"[{}+\s]|%s|\.format|join\(")


def _extract_deps(src: str):
    """从脚本源码机械提取本端域路径字面量（⛔ 不手抄依赖清单）。"""
    deps, unknown, runtime = [], 0, 0
    for m in _PATH_RE.finditer(src):
        raw = m.group(1)
        if _DYNAMIC.search(raw):
            unknown += 1
            continue
        # ⛔ 尾部标点剥离：中文全角括号/句号紧贴路径会被正则吃进字面量
        #   （01 规范 §二·九 乙类同族；实跑实证 `…hook_crash.log）` 误判缺失）
        raw = re.sub(r"[^\w\-./~一-鿿]+$", "", raw)
        if not raw:
            continue
        p = os.path.expanduser(raw)
        # ⛔ 运行时产物不判缺失：`/logs/`、`.log`、`.jsonl` 是脚本**写出来**的，
        #    首次运行前不存在属正常（实跑实证 hook_crash.log 误判 RED）。
        #    ⇒ 计入统计不告警，⛔ 不把它当输入型依赖。
        if "/logs/" in p or "/log/" in p \
                or p.endswith((".log", ".jsonl", ".log.lock")):
            runtime += 1
            continue
        deps.append(p)
    return sorted(set(deps)), unknown, runtime


def check(settings_path: str = SETTINGS) -> dict:
    rep = {"version": VERSION,
           "ts": datetime.now().isoformat(timespec="seconds"),
           "settings": settings_path, "scripts": [], "findings": [],
           "red": 0, "warn": 0, "unknown": 0}
    add = lambda lv, k, d: rep["findings"].append(
        {"level": lv, "kind": k, "detail": d})

    if not os.path.isfile(settings_path):
        add("RED", "settings_missing", f"配置文件不存在：{settings_path}")
        rep["red"] = 1
        return rep
    try:
        cfg = json.load(open(settings_path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        add("RED", "settings_unreadable", f"配置不可解析：{e}")
        rep["red"] = 1
        return rep

    cmds = []
    for ev in INJECT_EVENTS:
        for item in cfg.get("hooks", {}).get(ev, []):
            for h in item.get("hooks", []):
                c = h.get("command", "")
                if c:
                    cmds.append(c)
    if not cmds:
        add("WARN", "no_inject_mounted",
            f"{'/'.join(INJECT_EVENTS)} 无注入脚本挂载")

    seen = set()
    for c in cmds:
        m = re.search(r"([^\s]+\.py)", c)
        if not m:
            continue
        sp = os.path.expanduser(m.group(1))
        if sp in seen:
            continue
        seen.add(sp)
        rep["scripts"].append(sp)
        name = os.path.basename(sp)

        # ① 实体存在
        if not os.path.isfile(sp):
            add("RED", "script_missing", f"挂载的注入脚本不存在：{name}")
            continue
        # ② 语法可解析
        try:
            src = open(sp, encoding="utf-8", errors="replace").read()
            ast.parse(src)
        except (OSError, SyntaxError) as e:
            add("RED", "script_unparsable",
                f"注入脚本语法不可解析（改坏即静默失效）：{name} · {e}")
            continue
        # ③ 数据依赖存在性（机械提取）
        deps, unknown, runtime = _extract_deps(src)
        rep["unknown"] += unknown
        rep["runtime"] = rep.get("runtime", 0) + runtime
        for d in deps:
            if not os.path.exists(d):
                add("RED", "dep_missing",
                    f"{name} 依赖缺失：{d}")

    rep["red"] = sum(1 for f in rep["findings"] if f["level"] == "RED")
    rep["warn"] = sum(1 for f in rep["findings"] if f["level"] == "WARN")
    return rep


def _self_test() -> int:
    """夹具：坏脚本（缺依赖）/ 好脚本（不得凭空告警）·⛔ 不碰真实配置。"""
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        # self-test 夹具 = tempdir 运行时生成件 ⛔非包内运行时件；
        #   腿A 静态解析对其误判"执行型引用"→ 已走 --update-baseline 棘轮登记（定性=已豁免）
        good = os.path.join(td, "good_inject.py")
        open(good, "w").write(
            "# 好脚本：依赖指向真实存在的本端资产\n"
            f'P = "{os.path.join(HOME, _AI_DIR)}"\n')
        bad = os.path.join(td, "bad_inject.py")
        open(bad, "w").write(
            "# 坏脚本：依赖指向不存在的路径\n"
            f'P = "{os.path.join(HOME, _AI_DIR, "__nonexistent__")}"\n')
        cfgp = os.path.join(td, "settings.json")
        json.dump({"hooks": {"UserPromptSubmit": [
            {"hooks": [{"type": "command", "command": f"python3 {good}"}]},
            {"hooks": [{"type": "command", "command": f"python3 {bad}"}]},
            {"hooks": [{"type": "command",
                        "command": "python3 ~/__ghost__/nope.py"}]},
        ]}}, open(cfgp, "w"))

        rep = check(cfgp)
        kinds = {f["kind"] for f in rep["findings"]}
        print(f"  self-test 检出：{sorted(kinds)}")
        for k in ("dep_missing", "script_missing"):
            hit = k in kinds
            print(f"    {'✓' if hit else '✗'} {k}")
            ok &= hit
        # 变异：只挂好脚本 ⇒ 除 unknown 外不得有告警
        json.dump({"hooks": {"UserPromptSubmit": [
            {"hooks": [{"type": "command", "command": f"python3 {good}"}]}]}},
            open(cfgp, "w"))
        r2 = check(cfgp)
        extra = [f for f in r2["findings"]]
        print(f"  好脚本变异：额外告警={[f['kind'] for f in extra] or 'NONE ✓'}")
        ok &= not extra
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="WorkBuddy 端注入链健康守卫")
    ap.add_argument("--settings", default=SETTINGS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="有 RED 时 exit 1（默认恒 0·报告制）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()

    rep = check(a.settings)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"WorkBuddy 注入链健康 · {rep['ts']} · {VERSION}")
        print(f"  配置：{rep['settings']}")
        print(f"  注入脚本 {len(rep['scripts'])} 个 · "
              f"依赖无法静态判定 {rep['unknown']} 处（⛔不猜）")
        print(f"  运行时产物（不判缺失）：{rep.get('runtime',0)} 处")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    if a.strict and rep["red"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
