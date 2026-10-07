#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_liveness_check.py —— 在跑守卫的存活对账（元守卫·治「装了没夹具=坏了没人知道」）

## 病灶（2026-10-03 实证·不是「看着不错」）

`guard_selftest_check.py` 报「80 个守卫无 self-test 夹具」——但那个差集是**全量**的，
混着「一次性工具」「cron 巡检」「他端专属」，**没有回答本端最该知道的那件事**：

> **挂在运行链上、每轮真跑、却没有任何自测夹具的守卫有哪些？**
> 它们改坏了不会自己报警，而且没人会去跑它们（跑一次 90s+）。

实测锁定 **9 件**（`readonly-guards` 挂载面 20 件 ∩ 无夹具差集），
当场真跑 → **查出 2 件真缺陷**：

| 件 | 实测 | 性质 |
|:--|:--|:--|
| `devtools_single_source_guard.py` | rc=1 · 报 20+ 文件「真相源路径硬编码」 | 🔴 **真红**（它在挂载面上=每轮都跑） |
| `change_reflux_guard.py` | **>280s 未完** | 🔴 **重件误挂 on_session_end**（每轮通道跑重件） |

⇒ 「无夹具」这一条差集本身是**有信息量的**——它直接指向真缺陷。
但它报得**太粗**（80 个混在一起），所以需要一个**收窄到运行面的对账器**。

## 第一性原理：为什么是「三层对账」而不是「逐件补夹具」

逐件给 9 个（乃至 80 个）守卫补自测夹具 = **打地鼠**：
夹具本身也会腐坏、也会漏写、也不会自己告警 ⇒ 造下一个漂移源
（同 `kb-index` 沉默死 / 守卫文档≠实挂 / 手工名单漂移的**同一病根**）。

⇒ 复用 `gate_runner.py` 已验证的范式（它 2026-08 就写过）：
**文件系统是唯一真相源，不信任手工名单；用「声称/注册/实跑」三方对账代替枚举。**

## 本件三层判据

| 层 | 方 | 来源 | 含义 |
|:--|:--|:--|:--|
| L1 | **在跑面** | `buluotuo-readonly-guards/__init__.py` 的 `_GUARDS` 清单（**解析插件本体·⛔ 不维护第二份名单**） | 哪些守卫每轮真跑 |
| L2 | **夹具面** | `guard_selftest_check.py --diff-only` 的差集（注册表有但自测清单无） | 哪些没有自测夹具 |
| L3 | **存活面** | 本件按插件实际 argv 真跑（限时） | 哪些**真的跑不动 / 跑红 / 慢到拖垮通道** |

**三方不一致 ⇒ 红**：
- L1 ∩ L2（**在跑 ∧ 无夹具**）⇒ ⚠️ **高危**：坏了没人知道
- L1 ∩ L3 红 ⇒ 🔴 **正在失败**：它就在本端挂着
- L1 ∩ L3 超时 ⇒ 🔴 **重件误挂**：拖慢每轮通道（`on_session_end` 有 20s 预算）

## ⛔ 为什么 L3 默认**不跑**（诚实边界·别把「跑过」说成「验过」）

真跑 9 件实测 **63s**，而 `change_reflux_guard` 单件 **>280s**。
若每次都真跑 ⇒ 本件自己变成新的重件 ⇒ 又是一个「装了没人跑得起」的元问题。

⇒ **默认只做静态对账（L1 ∩ L2）**（<1s），
`--live` 才跑 L3（明确标 ⛔ 重、耗时、且**结果不跨会话有效**）。
`--live-timeout` 可调（默认 90s）。

## 纪律（守卫编写规范 §八 Hook 三纪律）

- **报告制·恒 exit 0**（`--strict` 才非零·供巡检承载）
- **判据缺席报 ⚪ 不假绿**（插件本体读不到 ⇒ 说「读不到」，⛔ 不输出「通过」）
- **静态优先·⛔ 不 import 插件**（import 会执行 register()·副作用不可控）
- **端隔离**：只读 `~/.hermes/plugins/` 与本端脚本中心，⛔ 不写他端

## 用法

```bash
python3 guard_liveness_check.py                    # 静态对账（L1∩L2）·<1s
python3 guard_liveness_check.py --json
python3 guard_liveness_check.py --live             # 加 L3 实跑（⛔ 重·>60s）
python3 guard_liveness_check.py --live-timeout 180
python3 guard_liveness_check.py --strict           # 有红 ⇒ exit 1
python3 guard_liveness_check.py --self-test
```
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import subprocess
import sys
import time

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")
PLUGIN = os.path.join(HOME, ".hermes", "plugins", "buluotuo-readonly-guards", "__init__.py")
SELFTEST = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "guard_selftest_check.py")
SCRIPT_CENTER = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心")
DEVTOOLS = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具")
LOG = os.path.join(DEVTOOLS, "logs", "guard_liveness_check.log")

# on_session_end 通道的每轮预算（官方插件回调超时·plugins_dispatch fail-closed 语义）
CHANNEL_BUDGET_S = 20.0


def _log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def read_mounted() -> tuple[dict, str]:
    """L1 在跑面：从**插件本体**解析 `_GUARDS` 清单（⛔ 不维护第二份名单）。

    返回 ({件名: argv}, 状态说明)。读不到 ⇒ ({}, "⚪ 插件本体读不到（判据缺席）")
    """
    if not os.path.isfile(PLUGIN):
        return {}, "⚪ 插件本体不存在（%s）" % PLUGIN
    try:
        text = open(PLUGIN, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return {}, "⚪ 插件本体读取失败：%r" % e
    m = re.search(r"_GUARDS:\s*List\[Tuple\[str,\s*List\[str\]\]\]\s*=\s*\[(.*?)\n\]",
                  text, re.S)
    if not m:
        return {}, "⚪ 插件本体里找不到 _GUARDS 清单（版式变了·判据缺席·⛔ 不假绿）"
    out: dict[str, list] = {}
    for name, args in re.findall(r'\("([^"]+)",\s*(\[[^\]]*\])?\)', m.group(1)):
        argv = []
        if args:
            argv = re.findall(r'"([^"]*)"', args)
        out[name] = argv
    if not out:
        return {}, "⚪ _GUARDS 解析出 0 条（判据缺席·⛔ 不假绿）"
    return out, "✅ 从插件本体解析到 %d 条" % len(out)


def read_selftest_gap() -> tuple[set, str]:
    """L2 夹具面：元守卫的差集（注册表有·自测清单无）。读不到 ⇒ (set(), ⚪)。"""
    if not os.path.isfile(SELFTEST):
        return set(), "⚪ 元守卫不在取件面（%s）" % SELFTEST
    try:
        r = subprocess.run([sys.executable, SELFTEST, "--diff-only"],
                           capture_output=True, timeout=200, cwd=os.path.dirname(SELFTEST))
        txt = (r.stdout or b"").decode("utf-8", "replace")
        gap = {l.strip()[2:].strip() for l in txt.split("\n")
               if l.strip().startswith("⚠️ ")}
        gap = {g for g in gap if g.endswith((".py", ".sh"))}
        gap.discard("guard_selftest_check.py")     # 它自己是元守卫·自比无意义
        if not gap:
            return set(), "✅ 无差集（全部守卫都有夹具）"
        return gap, "✅ 元守卫差集 %d 件" % len(gap)
    except Exception as e:
        return set(), "⚪ 元守卫执行失败（判据缺席）：%r" % e


def resolve(name: str) -> str | None:
    for root in (SCRIPT_CENTER, DEVTOOLS):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            return p
    return None


def run_live(mounted: dict, timeout: float) -> list[dict]:
    """L3 存活面：按插件实际 argv 真跑。⛔ 重·结果不跨会话有效。"""
    out = []
    for name, argv in mounted.items():
        path = resolve(name)
        if not path:
            out.append({"name": name, "status": "ABSENT", "detail": "取件面无实体"})
            continue
        cmd = (["bash", path] if name.endswith(".sh") else [sys.executable, path]) + list(argv)
        t0 = time.time()
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                               cwd=os.path.dirname(path))
            cost = time.time() - t0
            if r.returncode == 0:
                st, detail = ("OK", "%.1fs" % cost)
                if cost > CHANNEL_BUDGET_S:
                    st, detail = "SLOW", ("%.1fs·超通道预算 %.0fs" % (cost, CHANNEL_BUDGET_S))
            else:
                err = (r.stderr or b"").decode("utf-8", "replace").strip().split("\n")[-1][:90]
                out_txt = (r.stdout or b"").decode("utf-8", "replace").strip().split("\n")[-1][:90]
                st, detail = "RED", ("rc=%d %.1fs · %s" % (r.returncode, cost, err or out_txt))
            out.append({"name": name, "status": st, "detail": detail, "cost_s": round(cost, 1)})
        except subprocess.TimeoutExpired:
            out.append({"name": name, "status": "TIMEOUT",
                        "detail": ">%ds·⛔ 重件误挂每轮通道" % timeout,
                        "cost_s": timeout})
    return out


def self_test() -> int:
    """变异体双向夹具（⛔ 不碰真实插件本体·用临时夹具）"""
    import tempfile
    cases = []
    # ① 插件本体缺失 ⇒ 必须「⚪ 判据缺席」⛔ 不得输出 ✅ 通过
    global PLUGIN
    real = PLUGIN
    try:
        PLUGIN = os.path.join(tempfile.mkdtemp(), "nonexistent.py")
        got, why = read_mounted()
        cases.append(("插件缺失→⚪不假绿", got == {} and why.startswith("⚪")))
        # ② 版式变了（无 _GUARDS）⇒ 同样 ⚪
        p2 = os.path.join(tempfile.mkdtemp(), "x.py")
        open(p2, "w", encoding="utf-8").write("# 没有清单\n")
        PLUGIN = p2
        got2, why2 = read_mounted()
        cases.append(("版式变→⚪不假绿", got2 == {} and why2.startswith("⚪")))
        # ③ 正常版式 ⇒ 解析出条数
        p3 = os.path.join(tempfile.mkdtemp(), "ok.py")
        open(p3, "w", encoding="utf-8").write(
            '_GUARDS: List[Tuple[str, List[str]]] = [\n'
            '    ("a_guard.py", ["--check"]),\n'
            '    ("b_guard.sh", []),\n]\n')
        PLUGIN = p3
        got3, why3 = read_mounted()
        cases.append(("正常版式→解析2条", len(got3) == 2 and got3["a_guard.py"] == ["--check"]))
        # ④ 空清单 ⇒ ⚪（0 条 ≠ 通过）
        p4 = os.path.join(tempfile.mkdtemp(), "empty.py")
        open(p4, "w", encoding="utf-8").write(
            '_GUARDS: List[Tuple[str, List[str]]] = [\n]\n')
        PLUGIN = p4
        got4, why4 = read_mounted()
        cases.append(("空清单→⚪不假绿", got4 == {} and why4.startswith("⚪")))
    finally:
        PLUGIN = real
    for name, ok in cases:
        print("  %s %s" % ("✅" if ok else "❌", name))
    n = sum(bool(x) for _, x in cases)
    print("\n%s  self-test: %d/%d" % ("✅ 通过" if n == len(cases) else "❌ 失败", n, len(cases)))
    return 0 if n == len(cases) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--live", action="store_true", help="加 L3 实跑（⛔ 重·>60s）")
    ap.add_argument("--live-timeout", type=float, default=90.0)
    ap.add_argument("--strict", action="store_true", help="有红 ⇒ exit 1")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    mounted, s1 = read_mounted()
    gap, s2 = read_selftest_gap()
    # L1 ∩ L2 = 在跑 ∧ 无夹具 ⇒ 高危（坏了没人知道）
    risky = sorted(n for n in mounted if n in gap)
    res = {
        "version": VERSION,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "mounted": sorted(mounted),
        "gap_total": len(gap),
        "risky_no_selftest": risky,
        "status": {"L1_mounted": s1, "L2_selftest_gap": s2},
        "live": [],
    }
    if a.live:
        res["live"] = run_live(mounted, a.live_timeout)
    live_bad = [x for x in res["live"] if x["status"] in ("RED", "TIMEOUT", "ABSENT")]
    res["summary"] = {
        "mounted": len(mounted),
        "risky": len(risky),
        "live_bad": len(live_bad),
        "verdict": "RED" if (live_bad or s1.startswith("⚪")) else
                   ("WARN" if risky else "OK"),
    }
    _log("verdict=%s risky=%d live_bad=%d" % (res["summary"]["verdict"], len(risky), len(live_bad)))

    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("守卫存活对账 · %s · %s" % (res["ts"], VERSION))
        print("  L1 在跑面  %s（%d 件）" % (s1, len(mounted)))
        print("  L2 夹具面  %s" % s2)
        print("  ── 在跑 ∧ 无夹具（坏了没人知道）: %d 件" % len(risky))
        for n in risky:
            print("      ⚠️ %s" % n)
        if a.live:
            print("  ── L3 存活面（⛔ 本次实跑·结果不跨会话有效）")
            for x in res["live"]:
                if x["status"] != "OK":
                    print("      %-8s %-38s %s" % (x["status"], x["name"][:36], x["detail"][:60]))
            print("      （OK 件 %d 个未列）" % sum(1 for x in res["live"] if x["status"] == "OK"))
        v = res["summary"]["verdict"]
        print("  → %s%s" % ({"RED": "🔴 红", "WARN": "🟡 高危件待夹具", "OK": "✅ 全绿"}[v],
                             "" if not a.live else ""))
        if not a.live:
            print("  💡 加 --live 可真跑存活面（⛔ 重·>60s·本件默认不跑）")
    return 1 if (a.strict and res["summary"]["verdict"] == "RED") else 0


if __name__ == "__main__":
    raise SystemExit(main())