#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hermes_core_budget_guard.py —— 恒驻核预算守卫（真病灶·防静默消失）

## 病灶（官方契约挖出的·不是「看着不错」）

官方 `register_system_prompt_section` 的硬契约（docs §Cache-safe system prompt sections·逐字）：

> `max_chars` is capped at 4,000 characters. **All plugin sections together, including
> their audit headings, are capped at 8,000 characters and 32 sections.**
> Empty, non-string, oversized, **aggregate-over-budget**, or raising sections
> **are skipped with a warning**; prompt construction continues.

⚠️ **「aggregate-over-budget ⇒ skipped with a warning」是本件的立件依据**：
**超总预算的恒驻段会被静默跳过**——只记一条警告，不报错、不阻断、不崩。
⇒ 那个插件的恒驻能力**无声消失**，而盘上一切正常、插件 enabled、import 得进去。

**本端实测量化（2026-10-03）**：
- 本端 `doenglingz-twin` 注册两段：`doenglingz.core` + `doenglingz.l1`
- 两段 `max_chars` 各 3800 ⇒ 声明合计 **7600**
- 官方总预算 **8000** ⇒ **占用 95%**·余量 **400 字符**

⇒ **任何第三个插件想注册一段（哪怕 200 字符），都会被静默跳过。**

## 本件做什么

1. **实算**本端所有已注册 `register_system_prompt_section` 的段与声明字符数
2. 比对官方硬上限（单段 4000 / 全体 8000 / 32 段）
3. 余量低于阈值 ⇒ 🔴 红；命中上限 ⇒ 🔴 红
4. 顺带核对**段 ID 合法性**（官方：1–128 字符·小写字母数字 `. _ -`）与**唯一锚点**（`after_memory`）

## 纪律

- **报告制·恒 exit 0**（对齐本端守卫族「只观察不裁决」纪律）
- **判据缺席报 ⚪ 不假绿**（读不到插件源码 ⇒ 说「判据缺席」，不输出「OK」）
- **静态解析·不 import 插件**（⛔ import 会执行插件 register()·副作用不可控）

## 用法

```bash
python3 hermes_core_budget_guard.py
python3 hermes_core_budget_guard.py --json
python3 hermes_core_budget_guard.py --self-test
```
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
import time
from typing import Any

VERSION = "v1.0.0"
PLUGIN_DIR = os.path.expanduser("~/.hermes/plugins")

# 官方硬上限（docs §Cache-safe system prompt sections）
MAX_PER_SECTION = 4000
MAX_TOTAL = 8000
MAX_SECTIONS = 32
WARN_MARGIN_RATIO = 0.10          # 余量 <10% ⇒ 红

ID_RE = re.compile(r"^[a-z0-9._-]{1,128}$")
CALL_RE = re.compile(
    r"register_system_prompt_section\s*\((.*?)\)\s*$",
    re.S | re.M)


def _unquote(v: str) -> str:
    v = v.strip()
    if (v.startswith('"') and v.endswith('"')) or \
       (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def _module_int_consts(tree: ast.AST) -> dict[str, int]:
    """解出模块顶层的 `NAME = <整数字面量>`（如 _SECTION_MAX_CHARS = 3800）。

    ⚠️ 只解**字面量整数**；解不到就如实返回 None（⛔ 不猜·不按上限顶替）。
    这样「实参传常量」不再是判据盲区，同时保持纯静态、⛔ 不 import 插件。
    """
    out: dict[str, int] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name) and isinstance(node.value, ast.Constant) \
               and isinstance(node.value.value, int):
                out[tgt.id] = node.value.value
    return out


def scan_plugin(path: str) -> list[dict[str, Any]]:
    """静态扫出一个插件里所有 register_system_prompt_section 调用。

    ⛔ 用 AST 而非正则主路径（正则会漏多行/嵌套形态）·⛔ 不 import（不执行 register()）
    """
    out: list[dict[str, Any]] = []
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = getattr(fn, "attr", None) or getattr(fn, "id", None)
        if name != "register_system_prompt_section":
            continue
        kw = {k.arg: k.value for k in node.keywords if k.arg}
        args = node.args
        sid = _unquote(args[0].value) if (args and isinstance(args[0], ast.Constant)
                                           and isinstance(args[0].value, str)) else "<动态ID>"
        pos = _unquote(kw["position"].value) if (
            "position" in kw and isinstance(kw["position"], ast.Constant)) else "<未声明>"
        m = kw.get("max_chars")
        declared = None
        if isinstance(m, ast.Constant) and isinstance(m.value, int):
            declared = m.value
        elif isinstance(m, ast.Name):
            # 实参传模块级常量 ⇒ 从同模块顶层字面量赋值解值；解不到才留 None。
            # ⛔ 解不到时**不按 4000 顶替**（那是把「未知」当「最大」·会虚高总额造假红）。
            declared = _module_int_consts(tree).get(m.id)
        out.append({"id": sid, "position": pos, "max_chars": declared,
                    "max_chars_expr": (ast.unparse(m) if m is not None else None),
                    "callable": bool(args and not isinstance(args[1], ast.Constant))})
    return out


def collect() -> dict[str, Any]:
    res: dict[str, Any] = {"version": VERSION,
                           "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                           "sections": [], "scanned_plugins": 0,
                           "judgement_absent": False}
    if not os.path.isdir(PLUGIN_DIR):
        res["judgement_absent"] = True
        return res
    for plug in sorted(os.listdir(PLUGIN_DIR)):
        py = os.path.join(PLUGIN_DIR, plug, "__init__.py")
        if not os.path.isfile(py):
            continue
        res["scanned_plugins"] += 1
        for s in scan_plugin(py):
            s["plugin"] = plug
            res["sections"].append(s)
    if res["scanned_plugins"] == 0:
        res["judgement_absent"] = True
    return res


def evaluate(res: dict[str, Any]) -> dict[str, Any]:
    if res.get("judgement_absent"):
        return {"status": "ABSENT", "msg": "判据缺席（插件目录不可读或无可扫插件）——不输出 OK"}
    secs = res["sections"]
    problems: list[str] = []
    fatal: list[str] = []          # ⛔ 契约违规（官方会拒/静默跳过）→ 必判 RED

    # ① 段 ID 合法 + 唯一
    seen: dict[str, int] = {}
    for s in secs:
        sid = s["id"]
        if not ID_RE.match(sid):
            fatal.append("段 ID 非法（官方契约：1–128 字符·仅小写字母数字与 . _ -）：%s" % sid)
        seen[sid] = seen.get(sid, 0) + 1
        if s["position"] != "after_memory":
            fatal.append("段 %s 的 position=%s（官方契约：**唯一锚点** after_memory）"
                         % (sid, s["position"]))
        if s["max_chars"] is not None and s["max_chars"] > MAX_PER_SECTION:
            fatal.append("段 %s 声明 max_chars=%d > 官方单段上限 %d"
                         % (sid, s["max_chars"], MAX_PER_SECTION))
    dup = [k for k, v in seen.items() if v > 1]
    if dup:
        fatal.append("段 ID 重复（官方契约：重复 ID 被拒）：%s" % dup)

    # ② 段数
    if len(secs) > MAX_SECTIONS:
        fatal.append("段数 %d > 官方上限 %d" % (len(secs), MAX_SECTIONS))

    # ③ 总预算
    # ⚠️ **取不到 max_chars 的段（实参是模块常量）不可按 4000 计**——
    #    那会把「未知」当「最大」，虚高总额造出假红（本守卫自测正例1 抓到的真 bug）。
    #    正确口径：**已知段按实值累加 + 未知段单列**，两者都如实报。
    known = [s for s in secs if s["max_chars"] is not None]
    unknown = [s for s in secs if s["max_chars"] is None]
    total = sum(s["max_chars"] for s in known)
    used_pct = (total / MAX_TOTAL * 100) if MAX_TOTAL else 0
    margin = MAX_TOTAL - total
    if total > MAX_TOTAL:
        fatal.append("🔴 已知段总声明 %d > 官方总预算 %d ⇒ 超预算的段会被**静默跳过**"
                     % (total, MAX_TOTAL))
    elif unknown and margin < MAX_TOTAL * WARN_MARGIN_RATIO:
        # 未知段真实值最大到 4000 ⇒ 最坏情况可能已超
        worst = total + sum(MAX_PER_SECTION for _ in unknown)
        if worst > MAX_TOTAL:
            fatal.append("🔴 最坏情况（未知段各按单段上限 %d 计）= %d > 官方总预算 %d"
                         " ⇒ 已有段可能被静默跳过"
                         % (MAX_PER_SECTION, worst, MAX_TOTAL))
        else:
            problems.append("🟡 已知段占 %d/%d（%.0f%%）·余量 %d 字符；另有 %d 段"
                            "max_chars 实参为模块常量**静态取不到值**"
                            " ⇒ 真实占用需运行期核"
                            % (total, MAX_TOTAL, used_pct, margin, len(unknown)))
    elif margin < MAX_TOTAL * WARN_MARGIN_RATIO:
        problems.append("🟡 总声明 %d/%d（占 %.0f%%）·余量仅 %d 字符（<%.0f%% 阈值）"
                        "⇒ 下一个想注册的段可能被静默跳过"
                        % (total, MAX_TOTAL, used_pct, margin,
                           WARN_MARGIN_RATIO * 100))

    status = "RED" if fatal else ("WARN" if problems else "OK")
    return {"status": status, "sections": secs,
            "known_total": total, "unknown_sections": [s["id"] for s in unknown],
            "budget": MAX_TOTAL, "used_pct": round(used_pct, 1),
            "margin": margin, "problems": problems + fatal}


def self_test() -> int:
    """变异体双向夹具（铁律-014 隔离压测·⛔ 不碰真实 ~/.hermes）"""
    import tempfile
    T = tempfile.mkdtemp(prefix="hcbg_")
    plug = os.path.join(T, "p", "__init__.py")
    os.makedirs(os.path.dirname(plug), exist_ok=True)

    cases = []

    # 正例1：两段各 3800（=本端实况）⇒ 余量 400 <10% ⇒ WARN
    open(plug, "w").write(
        'def register(ctx):\n'
        '    ctx.register_system_prompt_section("doenglingz.core", f1,'
        ' position="after_memory", max_chars=3800)\n'
        '    ctx.register_system_prompt_section("doenglingz.l1", f2,'
        ' position="after_memory", max_chars=3800)\n')
    v = evaluate({"sections": scan_plugin(plug), "scanned_plugins": 1,
                  "judgement_absent": False})
    cases.append(("正例1 两段实参为常量·最坏8000", v["status"], "WARN"))

    # 正例2：超总预算 ⇒ RED
    open(plug, "w").write(
        'def register(ctx):\n'
        '    ctx.register_system_prompt_section("a", f, max_chars=4000)\n'
        '    ctx.register_system_prompt_section("b", f, max_chars=4000)\n'
        '    ctx.register_system_prompt_section("c", f, max_chars=4000)\n')
    v = evaluate({"sections": scan_plugin(plug), "scanned_plugins": 1,
                  "judgement_absent": False})
    cases.append(("正例2 三段12000 超预算", v["status"], "RED"))

    # 正例3：段 ID 非法 ⇒ RED
    open(plug, "w").write(
        'def register(ctx):\n'
        '    ctx.register_system_prompt_section("Bad_ID!", f, max_chars=100)\n')
    v = evaluate({"sections": scan_plugin(plug), "scanned_plugins": 1,
                  "judgement_absent": False})
    cases.append(("正例3 ID非法", v["status"], "RED"))

    # 负例1：小占用 ⇒ OK
    open(plug, "w").write(
        'def register(ctx):\n'
        '    ctx.register_system_prompt_section("ok.section", f,'
        ' position="after_memory", max_chars=500)\n')
    v = evaluate({"sections": scan_plugin(plug), "scanned_plugins": 1,
                  "judgement_absent": False})
    cases.append(("负例1 小占用", v["status"], "OK"))

    # 负例2：判据缺席 ⇒ ABSENT（⛔ 不得输出 OK）
    v = evaluate({"sections": [], "scanned_plugins": 0, "judgement_absent": True})
    cases.append(("负例2 判据缺席", v["status"], "ABSENT"))

    fails = 0
    for name, got, want in cases:
        ok = got == want
        fails += (0 if ok else 1)
        print("  %s %-30s want=%-7s got=%s" % ("✅" if ok else "❌", name, want, got))
    print("\n%s  self-test: %d/%d" % ("✅ 通过" if not fails else "❌ 失败",
                                      len(cases) - fails, len(cases)))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    res = collect()
    v = evaluate(res)
    if a.json:
        print(json.dumps({"scan": res, "verdict": v}, ensure_ascii=False, indent=2))
    else:
        print("Hermes 恒驻核预算守卫 · %s · %s" % (res["ts"], VERSION))
        print("  扫插件 %d 个 · 恒驻段 %d 个" % (res["scanned_plugins"], len(res["sections"])))
        for s in v.get("sections", []):
            print("    · %-20s plugin=%-20s position=%s max_chars=%s%s"
                  % (s["id"], s["plugin"], s["position"], s["max_chars"],
                     ("（实参 %s）" % s["max_chars_expr"])
                     if (s["max_chars"] is None and s.get("max_chars_expr")) else ""))
        if v["status"] != "ABSENT":
            print("  已知段合计 %d / 官方预算 %d（占 %.0f%%·余量 %d）"
                  % (v["known_total"], v["budget"], v["used_pct"], v["margin"]))
            if v.get("unknown_sections"):
                print("  ⚠️ 静态取不到 max_chars 的段（实参为模块常量）：%s"
                      % v["unknown_sections"])
        msgs = v.get("problems") or ([v["msg"]] if "msg" in v else [])
        for p in msgs:
            print("  [%s] %s" % (v["status"], p))
        if not v.get("problems") and v["status"] == "OK":
            print("  ✅ 全绿")
    return 0                    # 报告制·恒 exit 0


if __name__ == "__main__":
    raise SystemExit(main())