#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_hermes_runtime.py —— Hermes 端**运行态**三层验证（注册/加载/派发）

## 为什么需要它（`plugin_live_gate.py` 不够）

`plugin_live_gate` 验的是「文件能被 import、能取到路径」——
**那是分发物层面的自洽，不是端上真的在跑**。
一个插件可以 import 成功、路径全对，而 Hermes **压根没加载它**
（不在 `plugins.enabled` 里 / manifest 坏了 / 加载时抛异常被吞）。

⇒ 本脚本**用 Hermes 自己的 API** 验三层，逐层对应"用户能不能真的用上"：

| 层 | 问的问题 | 判据（真源） |
|:--|:---|:---|
| **L1 注册** | 端配置里挂了吗 | `config.yaml` → `plugins.enabled` 含全部 16 |
| **L2 加载** | Hermes 真的加载了吗 | `get_plugin_manager().discover_and_load()` → `_plugins[k].enabled is True` 且 `.error` 为空 |
| **L3 派发** | 钩子真挂上事件面了吗 | `pm._hooks` 四个事件里，本包插件的 `hooks_registered` 非空 |

⚠️ **三层缺一即失败**——这是台账 §1「恒真判据」的正面写法：
每一层都能单独红，⛔ 不存在"综合通过但其实没跑"。

## 端中立

⚠️ 本脚本**只在 Hermes 端跑**（它 import `hermes_cli`）。
公共面⛔ 不放它；各端各有一份，公共部分抽 `_runtime_probe.py` 时再说。
⇒ 这是**端适配层资产**，不是公共件——与 cross-platform 的分层一致。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import argparse
import glob
import json
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
CFG = os.environ.get("DOENGLINGZ_CONFIG_DIR") or os.path.join(HOME, ".hermes")
PLUGDIR = os.path.join(CFG, "plugins")
AGENT_SRC = os.path.join(CFG, "hermes-agent")
CONFIG_YAML = os.path.join(CFG, "config.yaml")
PKG = os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包")

# 钩子事件面 = 官方 `VALID_HOOKS` 真源（hermes_cli/plugins.py:109）
#
# 🔴 2026-10-04 根治（原实现在此写死 5 个事件）:
#   ① 写死清单会随官方新增事件而**过时** ⇒ 新插件挂官方事件反被判红
#      （假红·2026-10-04 实测：buluotuo-transform-gate 挂 transform_tool_result /
#       transform_llm_output ⇒ 被判「不在四事件面内」·install 因此 rc=1）
#   ② 「四事件面」这个说法本身就错——官方三类共 33 个事件面
#      （Directive 4 + Transform 4 + Observer 25）
# ⇒ 修法：**从官方源码动态读 VALID_HOOKS**；读不到 ⇒ 空元组 ⇒ L3 不因事件名判红
#    （宁可少判·⛔ 不可用写死清单卡官方新增事件——那是假红源）
def _official_events() -> tuple:
    """从 Hermes 源码读 VALID_HOOKS 真源。⛔ 读不到返回空 tuple（调用方降级）。"""
    cands = []
    env = os.environ.get("HERMES_AGENT_ROOT")
    if env:
        cands.append(env)
    home = os.path.expanduser("~")
    cands += [os.path.join(home, ".hermes/hermes-agent"),
              os.path.join(home, ".hermes/agent")]
    for root in cands:
        p = os.path.join(root, "hermes_cli", "plugins.py")
        if not os.path.isfile(p):
            continue
        try:
            src = open(p, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            tgt = None
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                tgt = node.target.id
            elif (isinstance(node, ast.Assign) and len(node.targets) == 1
                  and isinstance(node.targets[0], ast.Name)):
                tgt = node.targets[0].id
            if tgt != "VALID_HOOKS" or not isinstance(node.value, ast.Set):
                continue
            out = [el.value for el in node.value.elts
                   if isinstance(el, ast.Constant) and isinstance(el.value, str)]
            if out:
                return tuple(sorted(out))
    return ()


EVENTS = _official_events()
def _candidate_pythons() -> list:
    """解释器候选：静态三个 + **本机 Hermes 自带 venv 动态发现**。

    🔴 为什么必须动态发现（2026-10-02 实测·接手即撞）：
       `hermes_cli` 依赖 `ruamel`，系统 `python3` **没有** ⇒ 探针 import 必挂；
       而 Hermes 真正的解释器在 `~/.hermes/installs/*/environments/*/venv/` 下，
       **静态候选里一个都没有** ⇒ 探针 100% 假失败（运行态其实好着）。
       首版报的 `TypeError: type | type` 来自**最后一个候选**（3.9 不支持 X|Y 注解），
       把真因（缺 ruamel）覆盖了——**错误信息误导 = 比不报更坏**。
    ⚠️ 写死 `installs/1ad7ba54.../` 的哈希目录 = 下次升级即失效 ⛔ 必须 glob。
    """
    cands = [sys.executable, "python3", "/usr/bin/python3"]
    for pat in ("installs/*/environments/*/venv/bin/python3",
                "tools/python-*/bin/python3"):
        for p in sorted(glob.glob(os.path.join(CFG, pat)), reverse=True):
            if os.access(p, os.X_OK) and p not in cands:
                cands.append(p)
    return cands


PROBE = r'''
import sys, json
sys.path.insert(0, sys.argv[1])
out = {"ok": False}
try:
    from hermes_cli.plugins import get_plugin_manager
except Exception as e:
    out["err"] = "import hermes_cli.plugins 失败：%s: %s" % (type(e).__name__, e)
    print(json.dumps(out, ensure_ascii=False)); raise SystemExit(2)
try:
    pm = get_plugin_manager()
    pm.discover_and_load()
except Exception as e:
    out["err"] = "discover_and_load 抛错：%s: %s" % (type(e).__name__, e)
    print(json.dumps(out, ensure_ascii=False)); raise SystemExit(2)

want = json.loads(sys.argv[2])
P = getattr(pm, "_plugins", {}) or {}
out["loaded_total"] = len(P)
out["plugins"] = {}
for name in want:
    v = P.get(name)
    if v is None:
        out["plugins"][name] = {"loaded": False, "why": "不在 _plugins（未被加载/未启用）"}
        continue
    hooks = getattr(v, "hooks_registered", None)
    out["plugins"][name] = {
        "loaded": True,
        "enabled": bool(getattr(v, "enabled", False)),
        "error": str(getattr(v, "error", "") or ""),
        "hooks": sorted(map(str, hooks.keys())) if isinstance(hooks, dict)
                  else ([str(x) for x in hooks] if hooks else []),
    }
H = getattr(pm, "_hooks", {}) or {}
out["event_faces"] = {e: len(H.get(e) or []) for e in sys.argv[3].split(",")}
out["ok"] = True
print(json.dumps(out, ensure_ascii=False))
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugins-dir", default=PLUGDIR)
    ap.add_argument("--expect-from", default=None,
                    help="**包内**插件目录——用于抓「装漏了」："
                         "⛔ 只验已部署的会漏判（目录少一个照样全绿）")
    ap.add_argument("--config", default=CONFIG_YAML)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if not os.path.isdir(a.plugins_dir):
        print("❌ 插件目录不存在：%s——⛔ 无法验证（不是'没插件'，是'查不了'）"
              % a.plugins_dir)
        return 2
    try:
        names = sorted(d for d in os.listdir(a.plugins_dir)
                       if os.path.isfile(os.path.join(a.plugins_dir, d,
                                                      "plugin.yaml")))
    except OSError as e:
        print("❌ 读插件目录失败：%s: %s" % (type(e).__name__, e))
        return 2
    if not names:
        print("❌ %s 下无插件——⛔ 无法验证" % a.plugins_dir)
        return 2
    # ── 装漏检测：已部署 ⊇ 包内应有 ────────────────────────────
    missing_deploy = []
    if a.expect_from:
        if not os.path.isdir(a.expect_from):
            print("❌ --expect-from 目录不存在：%s" % a.expect_from)
            return 2
        exp = sorted(d for d in os.listdir(a.expect_from)
                     if os.path.isfile(os.path.join(a.expect_from, d,
                                                    "plugin.yaml")))
        have = set(names)
        missing_deploy = [x for x in exp if x not in have]
        if missing_deploy:
            print("❌ 装漏 %d 个（包内有、端上没有）：%s"
                  % (len(missing_deploy), ", ".join(missing_deploy)))
            print("   ⇒ 这正是「装完看起来成功、实际少装」的那类假绿·⛔ 不可交付")
            return 1
        print("装漏检测：✅ 包内 %d 个全部在端上" % len(exp))

    # ── L1 注册 ────────────────────────────────────────────────
    # ⚠️ **复用 mount_plugins 的解析器**（单一真源）。
    #    首版自己写了一套正则 → 报"16 未挂载"，而 mount_plugins 说"全部已挂载"
    #    ⇒ 两个解析器对同一份 YAML 给出相反结论。
    #    这正是台账 §2.1「写 A 处读 B 处」的同族：**同一事实两套实现 = 迟早分裂**。
    l1_bad = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from mount_plugins import find_enabled_lines          # noqa: E402
        lines = open(a.config, encoding="utf-8").read().split("\n")
        idx, items, _ind = find_enabled_lines(lines)
        if idx is None:
            l1_bad = ["config.yaml 未找到 plugins.enabled（⛔ 不猜结构）"]
        else:
            have = {n for _i, n in items}
            for n in names:
                if n not in have:
                    l1_bad.append("未挂载：%s" % n)
    except Exception as e:
        l1_bad = ["L1 解析失败：%s: %s" % (type(e).__name__, e)]

    # ── L2/L3 加载 + 派发（走 Hermes 自己的 API）────────────────
    probe = {"ok": False, "plugins": {}, "err": ""}
    if os.path.isdir(AGENT_SRC):
        # ⚠️ 解释器**逐个试**——`sys.executable` 可能是无第三方依赖的内核解释器
        #    （实测：缺 ruamel ⇒ hermes_cli 根本 import 不了 ⇒ 探针假失败）
        #    2026-10-02：静态三个候选全部失败，真解释器在 Hermes 自带 venv
        #    ⇒ 加动态发现（_candidate_pythons）。
        # 🔴 **错误必须聚合不能覆盖**（台账 §1.6 同族）：旧版 `probe = cand` 每轮覆盖
        #    ⇒ 只留最后一个解释器的错，把真因掩盖成"3.9 语法错"。看不清 ⇒ 修不对。
        probe_errs = []
        r = None
        for py in _candidate_pythons():
            try:
                r = subprocess.run(
                    [py, "-c", PROBE, AGENT_SRC, json.dumps(names),
                     ",".join(EVENTS)],
                    capture_output=True, text=True, timeout=600, cwd=AGENT_SRC)
            except (OSError, subprocess.SubprocessError) as e:
                probe_errs.append("%s：起不来 %s" % (os.path.basename(py), e))
                continue
            cand = None
            for line in reversed((r.stdout or "").strip().split("\n")):
                if line.startswith("{"):
                    try:
                        cand = json.loads(line)
                    except json.JSONDecodeError:
                        pass
                    break
            if cand and cand.get("ok"):
                probe = cand
                probe["_py"] = py
                break
            if cand and cand.get("err"):
                probe_errs.append("%s：%s" % (os.path.basename(py), cand["err"][:80]))
            else:
                probe_errs.append("%s：无探针输出" % os.path.basename(py))
        if not probe.get("ok"):
            if probe_errs:
                probe["err"] = "所有 %d 个解释器均失败：" % len(probe_errs) \
                    + " ｜ ".join(probe_errs)
            else:
                probe["err"] = ((r.stderr if r is not None else "")
                                or "probe 无输出").strip()[-200:]
    else:
        probe["err"] = "找不到 Hermes 源码：%s" % AGENT_SRC

    l2_bad, l3_bad, l3_detail = [], [], {}
    n_l2_unknown = 0
    for n in names:
        info = probe.get("plugins", {}).get(n)
        if not info or not info.get("loaded"):
            # 🔴 **无判据 ≠ 通过**（台账 §1.6）：探针没拿到这个插件的加载态
            #    ⇒ L3 对它**没有判定能力**，必须计入"无法判定"，
            #    ⛔ 不能让它继续躺在 L3 的分母里当"✅ 已过"。
            l2_bad.append("%s：%s" % (n, (info or {}).get("why", "未探测到")))
            n_l2_unknown += 1
            continue
        if not info.get("enabled"):
            l2_bad.append("%s：已加载但 enabled=False" % n)
        if info.get("error"):
            l2_bad.append("%s：加载报错 %s" % (n, info["error"][:60]))
        hooks = info.get("hooks") or []
        l3_detail[n] = hooks
        if not hooks:
            l3_bad.append("%s：未注册任何钩子" % n)
        else:
            for h in hooks:
                # ⛔ EVENTS 为空 = 读不到官方真源 ⇒ 不因事件名判红
                if EVENTS and h not in EVENTS:
                    l3_bad.append("%s：钩子事件 %s 不在官方 VALID_HOOKS 内" % (n, h))

    faces = probe.get("event_faces", {})
    # 🔴 faces 为空 = 探针**一个事件面都没测到** ≠ "四事件面都为空" ≠ 通过。
    #    空 dict 与 {e: 0} 在 `c == 0` 面前同义 ⇒ 旧版漏判（恒真·台账 §1.6 同族）。
    # 🔴 2026-10-04 修正判据语义（本条一直存在·EVENTS 从 5 扩到官方 41 后暴露）：
    #   原意 = 「探针**一个事件面都没测到**」⇒ 防空 dict 恒真（上方注释直书）。
    #   ⛔ **不是**「官方每个事件面都必须被本端挂上」——官方 41 个里本端只用 6 个
    #      （Directive 3 + Transform 3 + Observer 3）⇒ 按「全挂」判 = 恒红 35 个空面
    #      = **假红**（2026-10-04 实测·setup rc=1·install 连带失败）。
    # ⇒ 正确两层判据：
    #   ① 探针有效性：faces 非空（探针真的测到了东西）——防恒真放行
    #   ② 本包插件**自己声明**的事件面必须有注册数（我挂的必须真挂上）
    _declared = sorted({h for hs in l3_detail.values() for h in (hs or [])})
    _undeclared = ([e for e in _declared if faces.get(e, 0) == 0] if faces else [])
    if _undeclared:
        l3_bad.append("本包声明的事件面无注册：%s" % ", ".join(_undeclared))
    face_empty = ([] if faces else ["__probe_measured_nothing__"])

    ok = not (l1_bad or l2_bad or l3_bad or probe.get("err") or face_empty
              or n_l2_unknown)
    if a.json:
        print(json.dumps({"ok": ok, "n": len(names), "l1": l1_bad, "l2": l2_bad,
                          "l3": l3_bad, "l3_detail": l3_detail,
                          "event_faces": faces, "err": probe.get("err", "")},
                         ensure_ascii=False, indent=2))
    else:
        print("=== Hermes 运行态三层验证 ===\n插件数：%d\n" % len(names))
        print("L1 注册（config.plugins.enabled）  %s"
              % ("✅ %d/%d" % (len(names) - len(l1_bad), len(names))
                 if not l1_bad else "❌ %d 项" % len(l1_bad)))
        for x in l1_bad:
            print("    · %s" % x)
        print("L2 加载（Hermes 真实加载表）      %s"
              % ("✅ %d/%d" % (len(names) - len(l2_bad), len(names))
                 if not l2_bad else "❌ %d 项" % len(l2_bad)))
        for x in l2_bad:
            print("    · %s" % x)
        if probe.get("err"):
            print("    · probe：%s" % probe["err"][:120])
        # 🔴 L3 的分母 = **有判据的插件数**，不是 len(names)。
        #    把"L2 没拿到数据"的算进分母，等于让它在 L3 记一次"已过"（台账 §1.8）。
        n_l3_judged = len(l3_detail)
        if n_l2_unknown:
            print("L3 派发（钩子挂上事件面）          ⚪ 部分无法判定"
                  "（%d/%d 个插件 L2 未拿到数据·无判据≠通过）"
                  % (n_l2_unknown, len(names)))
        else:
            print("L3 派发（钩子挂上事件面）          %s"
                  % ("✅ %d/%d" % (n_l3_judged - len(l3_bad), n_l3_judged)
                     if not l3_bad else "❌ %d 项" % len(l3_bad)))
        for x in l3_bad:
            print("    · %s" % x)
        print("   事件面注册数：%s"
              % (", ".join("%s=%d" % (k, v) for k, v in sorted(faces.items()))
                 or "（未探测到·⛔ 不充绿）"))
        if face_empty:
            print("   ❌ 事件面探针异常：%s" % ", ".join(face_empty))
        print("\n%s" % ("✅ 三层全过——装完真能用" if ok
                        else "❌ 未通过——⛔ 不可视为交付"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())