#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/devtools_script_resolve_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""devtools 脚本解析守卫（Hermes 端 · 2026-10-02 立）

病根（实证）：`runtime_paths.json` 的 `devtools` 键指向 `脚本中心`，而布洛陀脚本族
**历史上散落在两个目录**（`脚本中心/` 与 `开发工具/`），且无任何同步机制——
实测 64 件两边都有但内容不同、**91 件只在 `开发工具/`**。

后果：插件按 `runtime_paths` 去 `脚本中心` 找 ⇒ 找不到 `doenglingz_inject_prompt.py`
⇒ **每轮 pre_llm_call 静默 fail-open**（插件日志 `inject empty rc=2` 连报十小时）
⇒ 注入器停摆 ⇒ **AI 拿不到档位判据 ⇒ 自己顶位宣布「D3 上岗」**。
典型假绿：机制坏了，行为看着还「合规」（每轮都在贴档位标签，只是贴错了）。

判据（三条·全机械可跑）：
  ① `runtime_paths.devtools` 解析到的目录存在
  ② Hermes 插件引用的每个脚本在该目录下真实可达
  ③ 注入器可执行（最小实跑 · 出档位块）

出口：rc=0 全绿 / rc=1 有缺口（逐条列出·⛔ 不静默跳过）
用法：python3 devtools_script_resolve_guard.py [--strict]
"""
from __future__ import annotations

# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HOME = os.path.expanduser("~")
HG = os.path.join(HOME, ".hermes")
RP = os.path.join(HG, "doenglingz", "runtime_paths.json")
PLUGINS = os.path.join(HG, "plugins")
# v1.x修复(2026-10-07 单源守卫判据②红清偿)：旧形 join(expanduser("~"), "/Users/<机器名>/…")
#   第二参绝对路径覆盖第一参 = 机器名硬编码退化（与 fidelity L60 注释点名的 A 型病灶同形）。
FALLBACKS = [
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具"),
]

QUOTE = r"""['"]"""
RE_JOIN = re.compile(r"os\.path\.join\(\s*_DEVTOOLS\s*,\s*" + QUOTE + r"([^'\"]+)" + QUOTE)
RE_TUPLE = re.compile(r"^\s*\(\s*" + QUOTE + r"([a-z0-9_\-]+\.(?:py|sh))" + QUOTE + r"\s*,", re.M)


def devtools_root() -> str:
    try:
        with open(RP, encoding="utf-8") as fh:
            return json.load(fh).get("devtools", "")
    except Exception:
        return ""


def referenced_scripts() -> set:
    refs = set()
    for dp, dn, fn in os.walk(PLUGINS):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            if not f.endswith(".py"):
                continue
            try:
                with open(os.path.join(dp, f), encoding="utf-8", errors="ignore") as fh:
                    t = fh.read()
            except OSError:
                continue
            refs |= set(RE_JOIN.findall(t))
            refs |= set(RE_TUPLE.findall(t))
    # 排除 runtime_path_keys 的**键名**（如「路由家族」）——它们不是文件名
    return {r for r in refs if r and "/" not in r and re.match(r"^[\w.\-]+\.(py|sh)$", r)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="候选目录存在同名件也算缺口（更严·治双副本）")
    args = ap.parse_args()

    root = devtools_root()
    gaps = []
    if not root:
        print("❌ runtime_paths.json 读不到或无 devtools 键")
        return 1
    if not os.path.isdir(root):
        print(f"❌ devtools 目录不存在：{root}")
        return 1

    refs = referenced_scripts()
    print(f"devtools = {root}")
    print(f"Hermes 插件引用脚本 = {len(refs)} 个")

    missing = sorted(r for r in refs if not os.path.exists(os.path.join(root, r)))
    for m in missing:
        where = [d for d in FALLBACKS if os.path.exists(os.path.join(d, m))]
        tag = "/".join(os.path.basename(d) for d in where) or "全域无"
        gaps.append(f"{m}（仅存于：{tag}）")
        print(f"  ❌ {m}  ← {tag}")
    if not missing:
        print("  ✅ 全部可达")

    inj = os.path.join(root, "doenglingz_inject_prompt.py")
    if os.path.isfile(inj):
        env = dict(os.environ)
        # 🔴 2026-10-08 探针**不得写被测对象的生产台账**（实测：本端台账 722 行里 290 行=40% 是它造的噪声；
        #   且本件排在 hermes_session_anomaly_guard 之前 ⇒ 探针的写把注入链死活盖成假绿）。
        #   修法=探针落隔离根（守卫规范 §3.9「夹具须可指向空目录」推广）·⛔判据不放松（仍要求 stdout 含「童灵」）。
        _iso = tempfile.mkdtemp(prefix="dsrg_probe_")
        env["DOENGLINGZ_CONFIG_DIR"] = _iso
        env["WORKBUDDY_CONFIG_DIR"] = _iso
        try:
            # 🔴 2026-10-04 根治探针用词错误（实测·假红）：
            #   旧探针喂 prompt="探测"，而注入器的门是 w1_fired(prompt)——
            #   「探测」不在 W1 触发词表 ⇒ 注入器**正确地什么都不输出**
            #   ⇒ 守卫读 stdout 找不到「童灵」⇒ 误判「注入器停摆」。
            #   实测注入器当时完全正常：`--prompt 启动童灵` → 4297 字节含童灵。
            # ⇒ 探针改用**真 W1 触发词**·⛔ 不放宽判据（仍要求 stdout 含「童灵」）。
            p = subprocess.run(
                [sys.executable, inj, "--prompt", "启动童灵"],
                capture_output=True, text=True, timeout=60, cwd=root, env=env,
            )
            ok = p.returncode == 0 and "童灵" in p.stdout
            print(f"  {'✅' if ok else '❌'} 注入器可执行：rc={p.returncode} 出档位块={'童灵' in p.stdout}")
            if not ok:
                gaps.append(f"doenglingz_inject_prompt.py 不可执行 rc={p.returncode}")
        except Exception as exc:
            print(f"  ❌ 注入器实跑异常：{exc!r}")
            gaps.append(f"doenglingz_inject_prompt.py 实跑异常 {exc!r}")
        finally:
            shutil.rmtree(_iso, ignore_errors=True)
    else:
        print("  ❌ 注入器缺失：doenglingz_inject_prompt.py")
        gaps.append("doenglingz_inject_prompt.py 缺失")

    if args.strict:
        for d in FALLBACKS:
            if os.path.abspath(d) == os.path.abspath(root) or not os.path.isdir(d):
                continue
            dup = sorted(
                f for f in os.listdir(d)
                if os.path.isfile(os.path.join(d, f)) and ".bak" not in f
                and f in refs and os.path.exists(os.path.join(root, f))
            )
            for f in dup:
                gaps.append("双副本：%s 同时存在于 %s 与 %s" % (
                    f, os.path.basename(root), os.path.basename(d)))

    print()
    if gaps:
        print(f"❌ 缺口 {len(gaps)} 项：")
        for g in gaps:
            print("   · %s" % g)
        return 1
    print("✅ devtools 解析全绿")
    return 0


if __name__ == "__main__":
    sys.exit(main())