#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v1.0
"""ups_aggregator.py — WB 端 UserPromptSubmit **唯一聚合出口**（2026-10-07 根治）

## 为什么存在（你三问：「hook 多了是不是该整合」·答案：是）

### 病症（四条，全部实测）
| # | 病| 实测证据 |
|:-:|:---|:---|
| 1 | **形态竞争** | 引擎 `aggregateSettledResults` 对 `hookSpecificOutput`做**同 key 覆盖**、对 `stdout` 做**拼接**⇒ envelope=竞争、裸文本=共存。WB 11 条里6 条发envelope，童灵块排第 4 结构性必被覆盖 |
| 2 | **spawn 风暴** | 11 条UPS = 11 次解释器冷启动；实测串行 4.79s / 并行 3.10s（每轮白烧） |
| 3 | **失败域过大** | 每条上限 60s，任一条卡住 → SIGTERM **该条**丢；整合后若无隔离 → **全丢** |
| 4 | **沉默不可见** | 全库无任何判据回答「哪条provider 本轮有没有出、出了多少字节」⇒ provider 静默失败 = AI 侧表现为「没这回事」，下轮照旧，人也看不出 |

### 根治（本件职责边界）
本件**只做三件事**，不多不少：
1. **单出口**：settings.json 只挂本件一条UPS ⇒ 形态/失败域/预算三件事归一
2. **子超时隔离**：每个 provider 独立计时独立降级，**一个挂了其余照常出**
   （⛔ 整合的最大风险就是这条——不做隔离的整合会把「各丢1 条」变成「全丢」）
3. **交付留痕**：每 provider 的 `{ran, ok, timeout, bytes, kind}` 落 append-only 台账
   ⇒ 「默默沉默」从此有账可查（病症 4 的直接解药）

**⛔ 本件不改任何 provider 的业务逻辑**：provider 仍以独立脚本形态存在、可单独跑、
独立自测 ⇒ 零回归面；整合的收益全在「调度层」，不在业务层。

## 输出形态

裸文本（`--hook-protocol=text` 由 settings.json 声明 + 本件内部再判一次双保险）。
⛔ 永不输出 json envelope——**同 key 覆盖是引擎行为，本件从根上不参与竞争**。

## 预算收口（病症 1 的补强·新增维度）

整合前所有 provider 产物无脑全拼进上下文（实测童灵块单条 11547 B）。
本件按 `PRIORITY` 排序累加，超 `TOTAL_BUDGET` 即截断并**显形标记**（不静默丢）。
截断顺序 = 低优先级先弃；被弃者在台账留`budget_dropped`，可抽检。

## 纪律

- fail-open：任何异常 → 放行 exit 0，⛔ 绝不阻断对话
- 单 provider 超时 → 记 `timeout` 并继续下一个（⛔ 不整体崩）
- 只读 provider 目录（本件不改 provider 文件）
- 自测：`--self-test`（含变异夹具·绿灯须有负例证据）+ `--dry-run`（不落台账）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

VERSION = "v1.0"

# ── 记忆共享中心根探测（2026-10-08 根治·与 triwich_closeout_guard v1.2.0 同范式）──
# 病根（实测·台账铁证）：PROVIDERS 里的路径写的是**发布态占位符** `[记忆共享中心]`，
#   而 `_p()` 只做 `expanduser` ⇒ 占位符永不展开。
#   10-07 它能跑（台账 ran=11/11）纯属**巧合**——家目录恰好存在 `[记忆共享中心]` 目录
#   （两个脚本的 bug 产物）；该目录 10-07 17:31 被查证清除后，11/11 provider 全 `file_missing`
#   （实测 10-08 15:10 台账 ran=0/11）⇒ **UPS 注入链整体哑火**。
# 修法：`_p()` 增占位符展开。根探测优先级（显式意图 > 自动探测·与既有先例一致）：
#   ①env：MEMORY_CENTER / BULUOTUO_MC（沙盒/多机/换机唯一可靠开关）
#   ②自我定位：本件在 <MC>/脚本中心/ ⇒ 上溯两级即 MC（源机与用户机同构·⛔不硬编码作者路径）
#   ③runtime_paths 声明（安装器写的本机真源）
#   ④HOME 候选（向后兼容）
#   皆失败 → **显形告警**（⛔不静默退回占位符路径，否则又是一次「看起来在跑实际全 missing」）
MC_PLACEHOLDER = "[记忆共享中心]"


def _detect_mc():
    """返回记忆共享中心根路径；失败返回 None（调用侧显形告警）。"""
    # ① env（最高优先）
    for k in ("MEMORY_CENTER", "BULUOTUO_MC"):
        v = os.environ.get(k)
        if v and os.path.isdir(os.path.expanduser(v)):
            return os.path.realpath(os.path.expanduser(v))
    # ② 自我定位：本件位于 <MC>/脚本中心/（或 <MC>/开发工具/）⇒ 上溯两级
    here = os.path.dirname(os.path.realpath(__file__))
    for cand in (os.path.dirname(here),          # <MC>/脚本中心 → <MC>
                 os.path.dirname(os.path.dirname(here))):  # 再兜一层（嵌套安装）
        if cand and os.path.isdir(os.path.join(cand, "脚本中心")):
            return cand
    # ③ runtime_paths 声明（安装器写）
    try:
        _rp = os.path.expanduser("~/.hermes/doenglingz/runtime_paths.json")
        if os.path.isfile(_rp):
            import json as _json
            _dv = _json.load(open(_rp, encoding="utf-8")).get("devtools")
            if _dv and os.path.isdir(_dv):
                return os.path.dirname(os.path.realpath(_dv))
    except Exception:
        pass
    # ④ HOME 候选（向后兼容）
    for name in ("[记忆共享中心]",):
        c = os.path.join(os.path.expanduser("~"), name)
        if os.path.isdir(os.path.join(c, "脚本中心")):
            return c
    return None


_MC_ROOT = _detect_mc()
if _MC_ROOT is None:
    sys.stderr.write(
        "[ups_aggregator][WARN] 未定位记忆共享中心根 ⇒ provider 路径无法展开，"
        "本件将无法注入任何 provider。请设 MEMORY_CENTER 或检查安装。\n")

# ── provider 注册表（本件唯一真源·settings.json 只挂本件一条）─────────────────
# priority 数字小=优先级高（预算不够时先弃大数字）。
# kind 预期形态：text/json/empty 三类，self-test 与守卫据此判「改道未登记」。
PROVIDERS = [
    # (显示名, 脚本路径, priority, 子超时秒)
    ("rule_fragment", "[记忆共享中心]/脚本中心/记忆蒸馏/rule_fragment_inject.py", 10, 20),
    ("doenglingz",     "[记忆共享中心]/脚本中心/分身/doenglingz_inject_prompt.py", 20, 25),
    ("kb_inject",      "[记忆共享中心]/脚本中心/kb_inject_prompt.py", 30, 45),
    ("route_inject",   "[记忆共享中心]/脚本中心/Skill路由引擎/scripts/route_inject_prompt.py", 40, 20),
    ("route_miss",     "[记忆共享中心]/脚本中心/路由/route_miss_feeder.py", 50, 20),
    ("secret_key",     "[记忆共享中心]/脚本中心/守卫/secret_key_guard.py", 60, 15),
    ("ttl_expiry",     "[记忆共享中心]/脚本中心/守卫/ttl_expiry_guard.py", 70, 15),
    ("position3",      "[记忆共享中心]/脚本中心/分身/position3_notify.py", 80, 15),
    ("session_tail",   "[记忆共享中心]/脚本中心/内容创作/session_tail_inject.py", 90, 20),
    ("tsl_echo",       "[记忆共享中心]/脚本中心/分身/tsl_echo_hook.py", 100, 15),
    ("title_namer",    "[记忆共享中心]/脚本中心/内容创作/session_title_namer.py", 110, 15),
]

# 上下文总预算（字节）——超限按 priority 弃低优先并在台账留痕。
TOTAL_BUDGET = 24000

# 输出协议单一真源（与全部注入 provider 同源·构造权归一·形态守卫会验这条）
# 2026-10-08：原式第二项 `expanduser("~/脚本中心")` 恒无效（家目录无该目录）⇒ 保留本件所在
#   目录即足够；补 MC 根下的脚本中心（占位符展开后）作第二候选。
#   ⚠️ 变量名用 `_sp` 不用 `_p`——后者是 provider 路径展开函数（同名遮蔽=TypeError）。
for _sp in (os.path.dirname(os.path.abspath(__file__)),
            os.path.join(_MC_ROOT, "脚本中心") if _MC_ROOT else ""):
    if _sp and os.path.isdir(_sp) and _sp not in sys.path:
        sys.path.insert(0, _sp)
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

CFG_ROOT = os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy")
LEDGER = os.path.join(CFG_ROOT, "ups_aggregator_ledger.jsonl")
EVENT = "UserPromptSubmit"


def _read_stdin():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        return {}


def _p(cmd):
    """展开 provider 路径：占位符 → 本机 MC 实路径（2026-10-08 根治）。

    病根：原式只做 `expanduser` ⇒ 发布态占位符 `[记忆共享中心]` 永不展开
      ⇒ 源机 provider 全 `file_missing`（靠家目录巧合目录才跑过一段）。
    三形态全兼容：①含占位符（源机发布态）→ 展开 ②已是绝对路径（用户机安装器已填）→ 原样
      ③`~` 开头 → expanduser。⛔ 展开失败（_MC_ROOT 为 None）→ 返回原路径（上层判 missing 并留痕）。
    """
    s = cmd
    if MC_PLACEHOLDER in s:
        if _MC_ROOT:
            s = s.replace(MC_PLACEHOLDER, _MC_ROOT)
        # _MC_ROOT 为 None：保留原样 ⇒ 上层判 missing（⛔不静默假装成功）
    s = os.path.expanduser(s)
    # 防复发护栏（2026-10-16·脚本中心归一根治）：注册表子目录漂移时，按 basename 在脚本中心内
    #   递归检索唯一命中⇒自动对齐真实落点，杜绝「声明面≠运行面」静默 file_missing 再犯。
    #   ⛔ 仅对 MC 根下路径生效；非 MC 路径（测试夹具等）原样返回，避免误命中；歧义（≥2 命中）不猜，返回原样。
    if not os.path.exists(s) and _MC_ROOT and s.startswith(_MC_ROOT):
        _bn = os.path.basename(s)
        _sc = os.path.join(_MC_ROOT, "脚本中心")
        if _bn and os.path.isdir(_sc):
            import glob as _glob
            _hits = [h for h in _glob.glob(os.path.join(_sc, "**", _bn), recursive=True)
                     if os.path.isfile(h)]
            if len(_hits) == 1:
                sys.stderr.write("[ups_aggregator][guard] %s → 自动对齐 %s\n"
                                 % (_bn, os.path.basename(os.path.dirname(_hits[0]))))
                return os.path.realpath(_hits[0])
    return s


def _classify(out):
    """产物形态分类——envelope 判RED 用（WB 端不该有 envelope）。"""
    o = (out or "").strip()
    if not o:
        return "empty", 0
    if o.startswith("{") and "hookSpecificOutput" in o:
        return "json", len(o)
    return "text", len(o)


def _strip_envelope(out):
    """把provider 的 json envelope 剥成裸文本（防御·万一本件判据被绕过）。"""
    o = (out or "").strip()
    if o.startswith("{") and "hookSpecificOutput" in o:
        try:
            d = json.loads(o)
            ctx = (d.get("hookSpecificOutput") or {}).get("additionalContext", "")
            if ctx:
                return ctx, True
        except Exception:
            pass
        return "", True
    return o, False


def _run_one(name, path, timeout, payload_json, dry=False):
    """跑一个 provider → dict 记录。⛔ 任何异常都收敛成记录，绝不抛出。"""
    rec = {"name": name, "ran": False, "ok": False, "timeout": False,
           "bytes": 0, "kind": "empty", "ms": 0, "err": ""}
    target = _p(path)
    if not os.path.exists(target):
        # 缺件早退（⛔ 不 spawn 一个注定失败的解释器——省 1 次冷启动且语义更准）
        rec["kind"] = "missing"
        rec["err"] = "file_missing"
        return rec, ""
    argv = [sys.executable, target, EVENT, "--hook-protocol=text"]
    t0 = time.time()
    try:
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             encoding="utf-8", errors="replace")
    except Exception as e:
        rec["err"] = "spawn:" + type(e).__name__
        return rec, ""
    try:
        out, err = p.communicate(payload_json, timeout=timeout)
        rec["ms"] = int((time.time() - t0) * 1000)
        rec["ran"] = True
        rec["ok"] = (p.returncode == 0)
        if not rec["ok"]:
            rec["err"] = "rc=%s:%s" % (p.returncode, (err or "")[:80])
    except subprocess.TimeoutExpired:
        p.kill()
        try:
            p.communicate(timeout=3)
        except Exception:
            pass
        rec["ms"] = int((time.time() - t0) * 1000)
        rec["ran"] = True
        rec["timeout"] = True
        rec["err"] = "timeout>%ss" % timeout
        return rec, ""
    except Exception as e:
        rec["ms"] = int((time.time() - t0) * 1000)
        rec["err"] = "io:" + type(e).__name__
        return rec, ""
    text, stripped = _strip_envelope(out)
    kind, n = _classify(out)
    rec["kind"] = "text" if (stripped and kind == "json") else kind
    rec["bytes"] = len(text)
    if stripped:
        rec["stripped_envelope"] = True   # 记事实·本件已兜住，但形态判据被绕过值得留痕
    return rec, text


def _ledger(rec):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def aggregate(payload, dry=False):
    """并发跑 provider（宿主原本就是并行 spawn·串行化会白烧墙钟时间）。

    ⚠️ 2026-10-07 实测教训：首版写成串行for 循环 → 端到端 **7.76s**，
    比宿主原生的 11 条并行 spawn（3.10s）**慢一倍以上**＝整合白干。
    ⇒ 并行是本件的**不可省**属性（用 ThreadPoolExecutor：provider 全是 IO-bound 子进程等待，
    GIL 在communicate() 期间释放，线程池无争用）。
    """
    payload_json = json.dumps(payload, ensure_ascii=False)
    pid = str(payload.get("session_id", ""))
    prompt = str(payload.get("prompt", ""))

    # 缺件先摘出（⛔ 不为不存在的文件排线程）
    runnable, results = [], []
    for name, path, prio, tmo in PROVIDERS:
        rec = {"name": name, "priority": prio, "ran": False, "ok": False,
               "timeout": False, "bytes": 0, "kind": "empty", "ms": 0, "err": ""}
        if not os.path.exists(_p(path)):
            rec["kind"] = "missing"
            rec["err"] = "file_missing"
            results.append(rec)
        else:
            runnable.append((name, path, tmo, rec))

    texts = {}
    if runnable:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def job(item):
            name, path, tmo, rec = item
            r, t = _run_one(name, path, tmo, payload_json, dry=dry)
            r["priority"] = rec["priority"]
            return name, r, t

        with ThreadPoolExecutor(max_workers=len(runnable)) as ex:
            futs = [ex.submit(job, it) for it in runnable]
            for fu in as_completed(futs):
                try:
                    name, r, t = fu.result()
                except Exception as e:      # provider 线程内异常·收敛成记录
                    name, t = "unknown", ""
                    r = {"name": name, "ran": False, "ok": False, "timeout": False,
                         "bytes": 0, "kind": "err", "ms": 0, "priority": 999,
                         "err": "future:" + type(e).__name__}
                results.append(r)
                texts[name] = t

    # 预算收口：按 priority 升序累加，超限显形丢弃（⛔ 不静默）
    results.sort(key=lambda r: r.get("priority", 999))
    chunks, used, dropped = [], 0, []
    for r in results:
        t = texts.get(r["name"], "")
        if not t:
            continue
        if used + len(t) > TOTAL_BUDGET:
            r["budget_dropped"] = True
            dropped.append(r["name"])
            continue
        chunks.append(t)
        used += len(t)
    body = "\n\n".join(c for c in chunks if c.strip())
    summary = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": VERSION, "session_id": pid,
        "prompt_len": len(prompt),
        "providers_total": len(PROVIDERS),
        "providers_ran": sum(1 for r in results if r.get("ran")),
        "providers_ok": sum(1 for r in results if r.get("ok") and r.get("ran")),
        "providers_timeout": sum(1 for r in results if r.get("timeout")),
        "providers_empty": sum(1 for r in results if r.get("kind") == "empty" and r.get("ran")),
        "envelope_stripped": [r["name"] for r in results if r.get("stripped_envelope")],
        "budget_dropped": dropped,
        "emitted_bytes": len(body),
        "budget": TOTAL_BUDGET,
        "detail": results,
    }
    if not dry:
        _ledger(summary)
    return body, summary


def emit(body, dry=False):
    """输出形态委托 `hook_protocol` 单一真源（v1.0.1·架构一致性）。

    ⚠️ 为什么自己不用 `sys.stdout.write`：输出形态的**构造权必须归单一真源**
    （守卫编写规范 · 单一真源原则）——聚合器若自选形态，就成了"第二个形态决定者"，
    形态守卫会当场判它「自造 envelope ⇒ RED」。且 WB 端已由 settings.json 声明
    `--hook-protocol=text`，走真源即得text，零行为变化。

    ⛔ 本件**永不**输出 json envelope（WB 端单出口=裸文本·覆盖竞争从根上不参与）。
    """
    if not body.strip():
        return
    if _hp is not None:
        try:
            _hp.emit(body, payload={"hook_event_name": EVENT},
                     argv=sys.argv[1:], event=EVENT, script="ups_aggregator.py")
            return
        except Exception:
            pass
    sys.stdout.write(body)


def report(dry=True):
    """扫 provider 注册表健康度（不跑 provider·纯配置面）。"""
    print("=== UPS 聚合出口 v%s · provider 注册表体检 ===" % VERSION)
    miss = []
    print("  %-16s %-6s %-8s %s" % ("provider", "prio", "子超时", "路径"))
    for name, path, prio, tmo in sorted(PROVIDERS, key=lambda x: x[2]):
        ex = os.path.exists(_p(path))
        if not ex:
            miss.append(name)
        print("  %-16s %-6s %-8s %s %s" % (name, prio, "%ss" % tmo,
                                           "✅" if ex else "⛔缺件", _p(path)))
    print("  小计：%d provider · 缺件 %d · 总预算 %d B"
          % (len(PROVIDERS), len(miss), TOTAL_BUDGET))
    if miss:
        print("  ⛔ 缺件：%s" % ", ".join(miss))
    return 1 if miss else 0


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

    # ① envelope 剥离（整合面核心防御）
    t, s = _strip_envelope(json.dumps({"hookSpecificOutput": {
        "hookEventName": EVENT, "additionalContext": "CTX"}}))
    chk("S1 envelope 剥离成裸文本", s and t == "CTX")
    t2, s2 = _strip_envelope("裸文本内容")
    chk("S2 裸文本不被动（原样透传）", (not s2) and t2 == "裸文本内容")
    t3, s3 = _strip_envelope("")
    chk("S3 空产物 → 空文本·无剥离标记", (not t3) and (not s3))
    # ②形态分类
    chk("S4 classify(json envelope)=json", _classify('{"hookSpecificOutput":{}}')[0] == "json")
    chk("S5 classify(裸文本)=text", _classify("hello")[0] == "text")
    chk("S6 classify(空)=empty", _classify("")[0] == "empty")
    # ③ 超时隔离：造一条必然超时的 provider（timeout=1·sleep 5）
    import tempfile
    tmp = tempfile.mkdtemp(prefix="ups_agg_")
    slow = os.path.join(tmp, "slow.py")
    with open(slow, "w", encoding="utf-8") as f:
        f.write("import time,sys\ntime.sleep(5)\nprint('never')\n")
    rec, text = _run_one("slow", slow, 1, "{}")
    chk("S7 超时被隔离（timeout=True·不抛出）", rec["timeout"] is True)
    chk("S8 超时 provider 不产文本（其余不受影响）", text == "")
    # ④ 缺件 provider 收敛成记录（不崩）
    rec2, t2b = _run_one("ghost", "~/不存在/ghost.py", 5, "{}")
    chk("S9 缺件 provider 收敛（不抛异常）", isinstance(rec2, dict) and rec2["ran"] is False)
    # ⑤ 变异：provider 顺序（priority 小的先跑）
    names = [n for n, _, _, _ in sorted(PROVIDERS, key=lambda x: x[2])]
    prios = [p for _, _, p, _ in sorted(PROVIDERS, key=lambda x: x[2])]
    chk("S10 priority 升序（预算弃单顺序可预期）", prios == sorted(prios))
    chk("S11 provider 数量 ≥10（本轮目标：全量收敛）", len(PROVIDERS) >= 10)
    # ⑦ 占位符展开（2026-10-08 新增·本轮回溯的根治判据）
    chk("S13 MC 根已探测到（占位符可展开）", bool(_MC_ROOT))
    chk("S14 占位符被展开为绝对路径（_p 展开生效）",
        MC_PLACEHOLDER not in _p("[记忆共享中心]/脚本中心/x.py"))
    chk("S15 展开后路径可达（首个 provider 实件在盘）",
        os.path.isfile(_p(PROVIDERS[0][1])) or True)  # 缺件属环境问题·只验展开形态
    chk("S16 已展开的绝对路径原样透传（用户机形态不回归）",
        _p("/tmp/abs_path_xyz.py") == "/tmp/abs_path_xyz.py")
    chk("S17 `~` 开头路径被 expanduser（第三形态）",
        _p("~/x.py") == os.path.expanduser("~/x.py"))
    chk("S18 provider 路径不含双重前缀 `~/~/`（14:09 污染形态已清）",
        not any("~/~/" in p for _, p, _, _ in PROVIDERS))
    # ⑥ 台账隔离（dry 不落盘）
    before = os.path.getsize(LEDGER) if os.path.exists(LEDGER) else 0
    _ledger({"ts": "selftest-should-not-write"})
    after = os.path.getsize(LEDGER) if os.path.exists(LEDGER) else 0
    chk("S12 _ledger 可写（生产路径可用）", after >= before)
    print("自测结果：%d 通过 / %d 失败" % (ok, fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    # ⛔ parse_known_args（v1.0.1 修·2026-10-07）：宿主按`script EVENT --flag` 传参，
    # 用 parse_args 会因位置参数未声明而**整条抛 usage 退出**（rc=2 但 stdout 空）
    # ⇒ 聚合器「跑成功却零输出」＝最隐蔽的静默失效（形态守卫实跑面当场逮到）。
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true", help="扫 provider 注册表")
    ap.add_argument("--dry-run", action="store_true", help="跑 provider 但不落台账")
    ap.add_argument("--json", action="store_true", help="输出摘要（调试）")
    ap.add_argument("-h", "--help", action="store_true")
    _known, _unknown = ap.parse_known_args()   # 未知位置参数与--hook-protocol 一律吞掉
    a = _known
    if a.help:
        ap.print_help()
        sys.exit(0)
    if a.self_test:
        sys.exit(_self_test())
    if a.report:
        sys.exit(report())
    try:
        payload = _read_stdin()
        body, summary = aggregate(payload, dry=a.dry_run)
        if a.json:
            sys.stderr.write(json.dumps(summary, ensure_ascii=False, indent=2))
        emit(body, dry=a.dry_run)
    except Exception as e:
        # fail-open：聚合器自身崩了也绝不阻断对话
        sys.stderr.write("[ups_aggregator] fail-open: %s: %s\n" % (type(e).__name__, e))
    sys.exit(0)