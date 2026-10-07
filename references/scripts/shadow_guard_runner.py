#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""shadow_guard_runner.py v1.0 — SSOT 四守卫统一跑口（收口回合自检器）

为什么有这个（2026-10-02·愿景①「全自动化·不依赖人记得」）：
  今天所有 SHADOW 回流补齐全靠我手动逐个跑守卫。下一个人（或下一个我）不记得跑，
  就又是"看起来都对"。本件把四个守卫收口成一个入口，一个命令跑全部，
  任意一条红即 exit 非零——收口回合挂进 launchd 或 Stop 钩子即可自动核。

四个守卫与分工（回流链三段闭合判据见 01-脚本架构设计通用规范 §二·十九）：
  1. shadow_ssot_guard.py     「怎么写」侧的 SSOT 唯一性（软链/副本）
  2. shadow_sleep_gate.py     「何时写」侧的机械睡眠闸（达标未写则 exit 3）
  3. shadow_reflux_guard.py   「写完谁看」侧的蒸馏回流校验
  4. shadow_shadowcheck.py    自检：真源可读+444 锁+元数据新鲜度（本件引入）

⛔ 设计边界（别改坏）：
  · 本件【只跑不改】——不写 SHADOW、不回锁、不补数据。四守卫各自的语义不变。
    本件是编排层，不是第六个守卫。
  · 不碰 TSL/档位任何逻辑（那是 TSL 专项的范围，勿跨界）。
  · 退出码不是简单 and：任一红即红，但会把每条的红/绿原样列出来，
    避免"一个红掩盖另一个红"。

用法：
  python3 shadow_guard_runner.py            # 跑全部并汇总
  python3 shadow_guard_runner.py --json     # 机读
  python3 shadow_guard_runner.py --quiet    # 只在有红时输出
退出：0=全绿；1=有守卫报红（明细见输出）；2=某守卫脚本缺失/不可执行
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = "python3"

GUARDS = [
    ("SSOT唯一性", "shadow_ssot_guard.py", [], {0: "✅ 唯一", 1: "🔴 分叉", 2: "🔴 真源损坏"}),
    ("睡眠闸", "shadow_sleep_gate.py", ["--days", "14"], {0: "✅ 未达标或已写", 3: "🔴 达标未写入"}),
    ("蒸馏回流", "shadow_reflux_guard.py", [], {0: "✅ 全回流", 1: "🔴 有断回流", 2: "🔴 表结构不可解析"}),
    ("元数据自检", "shadow_shadowcheck.py", [], {0: "✅ 真源健康", 1: "🔴 元数据异常"}),
]


def run_one(label, script, args, code_map):
    path = os.path.join(HERE, script)
    if not os.path.exists(path):
        return {"label": label, "script": script, "state": "MISSING", "rc": None,
                "verdict": "⚠️ 脚本缺失", "out": ""}
    try:
        r = subprocess.run([PY, path] + args, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"label": label, "script": script, "state": "TIMEOUT", "rc": None,
                "verdict": "🔴 超时", "out": ""}
    except OSError as e:
        return {"label": label, "script": script, "state": "ERROR", "rc": None,
                "verdict": "🔴 无法执行", "out": str(e)}

    rc = r.returncode
    verdict = code_map.get(rc, "⚪ 未知退出码 {}".format(rc))
    state = "RED" if rc != 0 else "GREEN"
    return {"label": label, "script": script, "state": state, "rc": rc,
            "verdict": verdict, "out": (r.stdout or "").strip() or (r.stderr or "").strip()}


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    quiet = "--quiet" in args

    results = [run_one(*g) for g in GUARDS]

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 1 if any(x["state"] != "GREEN" for x in results) else 0

    reds = [x for x in results if x["state"] != "GREEN"]
    if quiet and not reds:
        return 0

    print("=" * 66)
    print("[shadow_guard_runner] SSOT 四守卫收口自检")
    print("=" * 66)
    for x in results:
        print("  {:<12} {:<26} {}".format(x["label"], x["verdict"], "({})".format(x["script"]) if x["script"] else ""))
        if x["state"] != "GREEN" and x["out"]:
            for line in x["out"].splitlines():
                print("      │ " + line)

    print()
    if reds:
        print("  🔴 {} 条红：{}".format(len(reds), "、".join(x["label"] for x in reds)))
        print("     ⛔ 收口回合不得声明「已完成」——先修红，或如实报出未修项与原因。")
        return 1
    print("  ✅ 四守卫全绿")
    return 0


if __name__ == "__main__":
    sys.exit(main())