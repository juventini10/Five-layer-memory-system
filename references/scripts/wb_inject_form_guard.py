#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v1.0
"""wb_inject_form_guard.py — WB 端 UserPromptSubmit 注入形态守卫（防复发·2026-10-07）

## 为什么存在（判据面补齐·不是重复造轮子）

2026-10-07 病根：WB 端 UPS 实挂 11 条钩子，其中 6+ 条走 json envelope。
引擎（`app.asar.unpacked/cli/dist/codebuddy-lite-wb.mjs`）源码实证：

| 环节 | 行为 | 语义 |
|:---|:---|:---|
| `aggregateSettledResults` | `hookSpecificOutput={...旧,...新}` | **同 key 覆盖** |
| `aggregateSettledResults` | `stdout = 旧+"\n"+新` | **拼接共存** |
| UPS 消费 | 有 additionalContext → 覆盖赋值；否则走 stdout | 二选一 |

⇒ **json envelope = 竞争（last wins）；裸文本 = 共存**。
⇒ WB 端任何一条注入钩子发 envelope ⇒ 排在它前面的注入块**结构性必被覆盖**
（童灵块排第 4，其后还有 5 个 emitter）→ AI 收不到上岗仪式块 → 自由发挥 → 「老不按模板」。

`workbuddy_inject_chain_guard.py` 只验「脚本在不在·依赖齐不齐」（注册态/链本体），
**不验形态** ⇒ 本件是它的补面（形态面），两者互补不互顶账（守卫编写规范 · §二·七·〇 动作 3）。

## 检测项

| # | 项 | 级别 |
|:-:|---|:---|
| 1 | WB 端 UPS 钩子命令**未显式声明** `--hook-protocol=text` | RED |
| 2 | WB 端 UPS 钩子命令声明了 `json` | RED |
| 3 | 脚本源码内**自造** `hookSpecificOutput` 字面量（绕过单一真源） | RED |
| 4 | 实跑探针：某钩子在本端载荷下**实际吐出 json envelope** | RED |

第 4 项是本件的**可执行判据**——前三项都是静态读配置，只有实跑能证"改完真的生效"。

## 纪律

- 只读：⛔ 不改settings.json（形态错是配置错，守卫只报不改·修法交人/AI 显式执行）
- 只记录不拦截：报告制·默认 exit 0（`--strict` 时 RED 才 exit 1）
- fail-open：探针超时/异常 → 计入unknown，⛔ 不假红
- 自测：`--self-test`（含变异夹具·绿灯须有负例证据）
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
import tempfile
from datetime import datetime

VERSION = "v1.0"
HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".workbuddy", "settings.json")
UPS = "UserPromptSubmit"
LEDGER = os.path.join(HOME, ".workbuddy", "wb_inject_form_state.jsonl")

# WB 端必须 text 的判据串（与 hook_protocol v0.2 的 TEXT_HOSTS_BY_PATH 同源）
WB_PATH_FRAG = "/.workbuddy/"
PROTO_FLAG = "--hook-protocol"
# 会写 stdout 的注入类钩子（标题命名类不产上下文，不在此列）
INJECT_ROLE_HINT = ("inject", "notify", "guard", "echo", "feeder", "fragment", "tail")
# 单条钩子探针预算（秒）——宿主默认超时 60s，这里留足余量不与之竞争
PROBE_TIMEOUT = 45


def _load_settings():
    with open(SETTINGS, encoding="utf-8") as f:
        d = json.load(f)
    h = d.get("hooks", {})
    return h.get("events", h)


def _ups_commands():
    """列 WB 端 UPS 全部 command 型钩子 → [(脚本名, 完整命令, argv列表)]。"""
    out = []
    try:
        events = _load_settings()
    except Exception as e:
        return [("<settings读取失败>", str(e), [])]
    for grp in events.get(UPS, []) or []:
        for hk in (grp.get("hooks") or []):
            cmd = hk.get("command", "")
            if "python" not in cmd:
                continue
            parts = cmd.split()
            i = 0
            while i < len(parts) and "=" in parts[i] and not parts[i].startswith("/"):
                i += 1          # 跳过 VAR=val 环境前缀
            argv = parts[i:]
            name = os.path.basename(argv[1]) if len(argv) > 1 else "<?>"
            out.append((name, cmd, argv))
    return out


def _is_inject_role(name):
    n = name.lower()
    return any(k in n for k in INJECT_ROLE_HINT)


def _probe_payload():
    """模拟 WB 端 UPS 载荷（transcript_path 含 /.workbuddy/= 真实形态）。"""
    return json.dumps({
        "session_id": "probe-inject-form",
        "hook_event_name": UPS,
        "transcript_path": os.path.join(HOME, ".workbuddy", "projects", "probe.jsonl"),
        "cwd": os.path.dirname(os.path.expanduser("~/WorkBuddy")) or HOME,
        "prompt": "启动童灵，测试注入形态",
    }, ensure_ascii=False)


def _probe(argv):
    """实跑一条钩子 → (kind, bytes, head)。kind ∈ json/text/empty/err/timeout/skip。"""
    if not argv:
        return "skip", 0, ""
    try:
        r = subprocess.run(argv, input=_probe_payload(), capture_output=True,
                           text=True, timeout=PROBE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return "timeout", 0, "probe timeout %ss" % PROBE_TIMEOUT
    except Exception as e:
        return "err", 0, type(e).__name__ + ": " + str(e)[:80]
    o = (r.stdout or "").strip()
    if not o:
        return "empty", 0, ""
    if o.startswith("{") and "hookSpecificOutput" in o:
        return "json", len(o), o[:80]
    return "text", len(o), o[:80]


def scan(run_probe=True):
    rows = []
    for name, cmd, argv in _ups_commands():
        declared = None
        m = re.search(re.escape(PROTO_FLAG) + r"[=\s]+(\w+)", cmd)
        if m:
            declared = m.group(1).lower()
        inline_json = False
        try:
            src = open(argv[1], encoding="utf-8", errors="replace").read() if len(argv) > 1 else ""
            # 「自造 envelope」判据 v1.1（2026-10-07 修正·聚合器上线后暴露的假红）：
            #   v1.0 只看「源码含 hookSpecificOutput 字面量且未 import hook_protocol」
            #   ⇒ **误判聚合器**（它含该字面量是为了**剥离** provider 的envelope，不是构造）。
            #   收窄为「**构造输出**」：hookSpecificOutput 与 json.dumps/print 出现在同一语句内
            #   （写出动作）；纯读取/剥离语境（in / .get / startswith）⛔ 不算。
            inline_json = bool(
                re.search(r"(print|stdout\.write|json\.dumps)\s*\([^)]*hookSpecificOutput",
                          src, re.S)
            ) and ("import hook_protocol" not in src and "hook_protocol as _hp" not in src)
        except Exception:
            src = ""
        kind, n, head = (_probe(argv) if run_probe else ("skip", 0, ""))
        rows.append({
            "name": name, "declared": declared, "inline_envelope": inline_json,
            "probe_kind": kind, "probe_bytes": n, "probe_head": head,
            "inject_role": _is_inject_role(name),
        })
    return rows


def _verdict(r):
    """→ (level, [issues])。RED 判据三条 + 实跑面。"""
    issues = []
    if r["inject_role"] and r["declared"] is None:
        issues.append("未显式声明 --hook-protocol（形态靠env 猜·2026-10-07 病根）")
    if r["declared"] == "json":
        issues.append("WB 端声明 json（⇒ 同 key 覆盖·注入块必丢）")
    if r["inline_envelope"]:
        issues.append("源码自造 hookSpecificOutput（绕过 hook_protocol 单一真源）")
    if r["probe_kind"] == "json":
        issues.append("实跑吐出 json envelope（WB 端实测·结构性覆盖）")
    return ("RED" if issues else "GREEN"), issues


def _ledger(rec):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def report(run_probe=True):
    rows = scan(run_probe=run_probe)
    red = []
    print("=== WB 端 UPS 注入形态守卫 v%s ===（真源=引擎 aggregateSettledResults 覆盖语义）"
          % VERSION)
    print("  %-30s %-9s %-12s %-9s %s" % ("钩子", "声明", "自造envelope", "实跑", "判定"))
    for r in rows:
        lvl, iss = _verdict(r)
        if lvl == "RED":
            red.append((r["name"], iss))
        print("  %-30s %-9s %-12s %-9s %s" % (
            r["name"][:30],
            r["declared"] or "-",
            "是" if r["inline_envelope"] else "否",
            r["probe_kind"],
            lvl))
    print("  小计：%d 条 UPS 钩子 · RED %d" % (len(rows), len(red)))
    for n, iss in red:
        print("  ⛔ %s：%s" % (n, "；".join(iss)))
    _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "total": len(rows), "red": len(red),
             "red_names": [n for n, _ in red],
             "probed": bool(run_probe)})
    print("  台账：%s" % LEDGER)
    print("  修法：WB 端每条 UPS 钩子命令追加 `--hook-protocol=text`"
          "（argv 优先级最高·构造权在配置不在推断）；⛔ 不改宿主·不改引擎。")
    return 1 if red else 0


def _self_test():
    """负例夹具（守卫编写规范 原则3：绿灯需要负例证据）。"""
    ok = fail = 0

    def chk(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
            print("  ✅ %s" % name)
        else:
            fail += 1
            print("  ❌ %s" % name)

    good = {"name": "x_inject.py", "declared": "text", "inline_envelope": False,
            "probe_kind": "text", "probe_bytes": 10, "probe_head": "", "inject_role": True}
    chk("S1 合规行→GREEN", _verdict(good)[0] == "GREEN")
    for field, val, why in [
        ("declared", None, "未声明"),
        ("declared", "json", "声明json"),
        ("inline_envelope", True, "自造envelope"),
        ("probe_kind", "json", "实跑json"),
    ]:
        bad = dict(good)
        bad[field] = val
        chk("S2 变异[%s]→RED（%s）" % (why, field), _verdict(bad)[0] == "RED")
    # 非注入角色（标题命名类）不因缺声明判红
    nr = dict(good)
    nr["inject_role"] = False
    nr["declared"] = None
    chk("S3 非注入角色·未声明 → 不判红", _verdict(nr)[0] == "GREEN")
    # 探测失效不得假红
    for k in ("empty", "timeout", "err", "skip"):
        row = dict(good)
        row["probe_kind"] = k
        chk("S4 实跑 %s 不判红（仪器失效≠违规）" % k, _verdict(row)[0] == "GREEN")
    print("自测结果：%d 通过 / %d 失败" % (ok, fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="RED 时 exit 1")
    ap.add_argument("--no-probe", action="store_true", help="跳过实跑探针（只查配置面）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(_self_test())
    try:
        rc = report(run_probe=not a.no_probe)
    except Exception as e:
        print("守卫自身异常（fail-open·不阻断）：%s: %s" % (type(e).__name__, e))
        sys.exit(0)
    sys.exit(rc if a.strict else 0)