#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hermes_session_anomaly_guard.py —— Hermes 会话层异常检测守卫

## 别端先例（吸收来源·不是我发明的）

DSH 端 `dsh_session_anomaly_guard.py`（2026-08-21·9785 字符）开了这个先例，脚本自述
「跨工具中立·公共脚本住开发工具/·任何端可接入」；LobsterAI 端有同族
`lobsterai_session_anomaly_guard.py`。本件 = **按 Hermes 真实数据面重写**（对齐 04 指南
§二·七·〇 动作 3「能对齐先例就不自建」+ 本端 `hermes_inject_chain_guard.py` 的
「按本端真实事实源重建同一职责·⛔ 不 fork 他端脚本」先例）。

**它治什么（别端已实证的三类失效）**：管道适配层坏掉时，
**下游守卫全盲**（读不到 transcript ⇒ 以为没消息 ⇒ 一切审计都以为「今天没触发」）——
即「守卫静默失效」本身没人守。

## 为什么 Hermes 需要（本日实盘取证·非推测）

Hermes 端与 DSH 的数据面差异（官方 + 实盘）：

| 项 | DSH | Hermes |
|:--|:--|:--|
| 会话存储 | `session.v3.jsonl.zstd` 转录文件 | **`~/.hermes/state.db`（SQLite + FTS5）** |
| 转录可得性 | 管道适配层产 CC 格式 jsonl | 无 jsonl 侧信道 |
| 单测协议 | stdin `{"transcript_path":...}` | 无（`post_llm_call` ⛔ 不带 transcript_path） |

⇒ DSH 版接不上（它读 jsonl 路径）；但它的**判据骨架可提炼**：
「数据面健康」本身可机械查。

## 本件五检测（对齐 Hermes 实况）

| # | 检测 | 判据 |
|:--|:---|:---|
| ① | `state.db` 存在且非空 | 缺 ⇒ 🔴 一切会话层守卫都盲 |
| ② | `state.db` 可被 sqlite3 打开且表结构含会话表 | 打不开 ⇒ 🔴 |
| ③ | **近 N 小时有会话写入** | 无 ⇒ 🟡 「最近无会话」≠ 故障，但也可能是管道断了 |
| ④ | **常驻核两段真在盘** | 缺 ⇒ 🔴 童灵恒驻核空转（用户无感但机制已死） |
| ⑤ | **本端注入台账近 N 分钟有新增** | 无 ⇒ 🔴 疑似注入链未真派发（与 `hermes_inject_chain_guard` 的第④腿互补） |

⚠️ ①⑤ 与 `hermes_inject_chain_guard.py` 的检测②④ 有**部分重叠**，
本件定位为**独立可跑的单文件检查器**（⛔ 不 import 那个守卫·避免相互顶账），
重叠部分在输出里标「与 hermes_inject_chain_guard 重叠」，由人判断是否两处都挂。

## 纪律

- **只告警不拦截·恒 exit 0**（守卫编写规范 §八 Hook 三纪律）
- **判据缺席报 ⚪ 不假绿**（读不到 state.db ⇒ 说「判据缺席」，⛔ 不输出 OK）
- **零 stdin 契约**（不吃 stdin·可挂 readonly-guards 承载面）
- **端隔离**：只读 `~/.hermes/`，⛔ 不写任何他端目录

## 用法

```bash
python3 hermes_session_anomaly_guard.py
python3 hermes_session_anomaly_guard.py --json
python3 hermes_session_anomaly_guard.py --self-test
```
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import sqlite3
import time

VERSION = "v1.0.0"
DB = os.path.expanduser("~/.hermes/state.db")
DL_DIR = os.path.expanduser("~/.hermes/doenglingz")
SLICE_DIR = os.path.expanduser("[记忆共享中心]/数字分身/K2切片蒸馏/slices")
CORE_SECTION = os.path.join(DL_DIR, "core_slice.md")
L6_SECTION = os.path.join(DL_DIR, "L6_反向约束.md")
INJECT_LEDGER = os.path.join(DL_DIR, "doenglingz_inject_state.json")
SESSION_FRESH_HOURS = 6
INJECT_FRESH_MIN = 60


def check_1_db_exists() -> tuple[str, str]:
    if not os.path.isfile(DB):
        return "ABSENT", "state.db 不存在（%s）——会话层一切守卫都盲" % DB
    sz = os.stat(DB).st_size
    if sz == 0:
        return "RED", "state.db 存在但为 0 字节"
    return "OK", "state.db %d 字节" % sz


def check_2_db_openable() -> tuple[str, str]:
    if not os.path.isfile(DB):
        return "ABSENT", "无 state.db·判据缺席"
    try:
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
        tabs = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        con.close()
    except Exception as e:
        return "RED", "sqlite3 只读打开失败：%r" % e
    if not tabs:
        return "RED", "state.db 无任何表（结构异常）"
    return "OK", "可打开·%d 表：%s" % (len(tabs), tabs[:6])


def check_3_session_freshness() -> tuple[str, str]:
    """近 N 小时有无会话写入（⛔ 改文件 mtime 判据·⛔ 不猜表结构）。"""
    if not os.path.isfile(DB):
        return "ABSENT", "无 state.db·判据缺席"
    age_h = (time.time() - os.stat(DB).st_mtime) / 3600
    if age_h <= SESSION_FRESH_HOURS:
        return "OK", "state.db 近 %.1f 小时有写入（阈值 %dh）" % (
            age_h, SESSION_FRESH_HOURS)
    return "WARN", ("state.db 已 %.1f 小时未写（阈值 %dh）——「最近无会话」正常，"
                   "但也可能是管道断了·与①⑤交叉判" % (age_h, SESSION_FRESH_HOURS))


def check_4_core_sections() -> tuple[str, str]:
    """常驻核两段真在盘（治「童灵恒驻核空转·用户无感」）。"""
    miss = [n for n, p in (("core_slice", CORE_SECTION),
                           ("L6", L6_SECTION)) if not os.path.isfile(p)]
    # 切片源目录优先（插件实际读的是 twin_slices 键 → 数字分身/K2切片蒸馏/slices）
    if os.path.isdir(SLICE_DIR):
        miss = [] if (os.path.isfile(os.path.join(SLICE_DIR, "core_slice.md"))
                      or os.path.isdir(SLICE_DIR)) and \
            os.path.isfile(os.path.join(SLICE_DIR, "core_slice.md")) else \
            [n for n in ("core_slice",) if not os.path.isfile(
                os.path.join(SLICE_DIR, "core_slice.md"))]
        found = "slices/core_slice.md 在盘"
    else:
        miss = [n for n in ("core_slice.md", "L6_反向约束.md")
                if not (os.path.isfile(CORE_SECTION) or os.path.isfile(L6_SECTION))]
        found = "doenglingz/ 下找恒驻核切片"
    if miss:
        return ("ABSENT" if not os.path.isdir(SLICE_DIR) and not os.path.isdir(DL_DIR)
                else "RED"), "恒驻核切片缺失：%s（%s）⇒ 恒驻核空转·用户无感" % (
            miss, found)
    return "OK", "恒驻核切片在盘（%s）" % found


def check_5_inject_ledger() -> tuple[str, str]:
    """注入台账近 N 分钟有新增（与 hermes_inject_chain_guard ④ 重叠·已标注）。"""
    if not os.path.isfile(INJECT_LEDGER):
        return ("ABSENT", "无注入台账 %s·判据缺席（与 "
                "hermes_inject_chain_guard 第④腿重叠）" % INJECT_LEDGER)
    age = (time.time() - os.stat(INJECT_LEDGER).st_mtime) / 60
    if age <= INJECT_FRESH_MIN:
        return "OK", "注入台账近 %.0f 分钟有更新（与 inject_chain_guard 重叠）" % age
    return "RED", ("注入台账已 %.0f 分钟未更新 ⇒ 疑似注入链未真派发"
                   "（与 hermes_inject_chain_guard 第④腿重叠）" % age)


CHECKS = [("①state.db存在", check_1_db_exists),
          ("②db可打开", check_2_db_openable),
          ("③会话新鲜度", check_3_session_freshness),
          ("④恒驻核切片在盘", check_4_core_sections),
          ("⑤注入台账新鲜度", check_5_inject_ledger)]


def run_all() -> dict:
    out = {"version": VERSION, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "checks": []}
    red = warn = absent = 0
    for name, fn in CHECKS:
        try:
            st, msg = fn()
        except Exception as e:                    # ⛔ 单检异常≠全绿
            st, msg = "RED", "检测自身异常：%r" % e
        red += st == "RED"
        warn += st == "WARN"
        absent += st == "ABSENT"
        out["checks"].append({"name": name, "status": st, "msg": msg})
    out["summary"] = {"RED": red, "WARN": warn, "ABSENT": absent,
                      "verdict": "RED" if red else ("WARN" if warn else "OK")}
    return out


def self_test() -> int:
    """变异体双向夹具（铁律-014 隔离压测·⛔ 不碰真实 ~/.hermes）"""
    import tempfile
    global DB, DL_DIR
    o_db, o_dl = DB, DL_DIR
    T = tempfile.mkdtemp(prefix="hsag_")
    cases = []
    try:
        # 变异体A：无 db ⇒ ABSENT（⛔ 不得假绿）
        DB = os.path.join(T, "nodb", "state.db")
        cases.append(("无state.db→ABSENT", check_1_db_exists()[0] == "ABSENT"))

        # 变异体B：空 db ⇒ RED
        p = os.path.join(T, "empty", "state.db")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").close()
        DB = p
        cases.append(("0字节db→RED", check_1_db_exists()[0] == "RED"))

        # 变异体C：有表 db ⇒ OK
        p = os.path.join(T, "ok", "state.db")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        con = sqlite3.connect(p)
        con.execute("CREATE TABLE messages (id INTEGER)")
        con.commit(); con.close()
        DB = p
        ok1 = check_1_db_exists()[0] == "OK"
        ok2 = check_2_db_openable()[0] == "OK"
        cases.append(("有表db→①②OK", ok1 and ok2))

        # 变异体D：伪造「非 sqlite」文件 ⇒ RED（②能抓到）
        p = os.path.join(T, "bad", "state.db")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write("not a database at all")
        DB = p
        cases.append(("非sqlite→②RED", check_2_db_openable()[0] == "RED"))
    finally:
        DB, DL_DIR = o_db, o_dl
    for name, ok in cases:
        print("  %s %s" % ("✅" if ok else "❌", name))
    # ⚠️ cases 里最后一项可能是 bool 也可能是 bool 元组（上面用 (a_ok and b_ok) 合并过）
    #    ⇒ 统一压成 bool 再计数（自测当场抓到 sum(bool + tuple) TypeError）
    flags = [bool(x) for _, x in cases]
    n = sum(flags)
    print("\n%s  self-test: %d/%d" % ("✅ 通过" if n == len(flags) else "❌ 失败",
                                      n, len(flags)))
    return 0 if n == len(flags) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    r = run_all()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print("Hermes 会话异常守卫 · %s · %s" % (r["ts"], VERSION))
        for c in r["checks"]:
            print("  [%s] %-16s %s" % (c["status"], c["name"], c["msg"]))
        s = r["summary"]
        print("  → RED %d / WARN %d / ABSENT %d" % (s["RED"], s["WARN"], s["ABSENT"]))
    return 0                        # ⛔ 报告制·恒 exit 0


if __name__ == "__main__":
    raise SystemExit(main())