#!/usr/bin/env python3
# version: v1.0.0
"""Hermes 端注入链健康守卫（端专属·替代误接的 qodercn_inject_chain_guard）。

## 为什么存在（2026-10-02·皮叔授权「注入质检按符合愿景最优解处理」）

**病根**：上轮横切全端资产时，我把 `qodercn_inject_chain_guard.py` 当"跨端中立件"接进了
Hermes 端收口集群——**只因脚本名含 "guard"**。复核源码 L307-308 才发现它硬编码扫
`~/.qoder-cn/projects/*/*.jsonl` ⇒ **Qoder CN 专属**。装在本端的后果：
它等的 `--record` 动作只有 QoderCN 端会做 ⇒ **恒报「注入自检 24h 未跑」= 纯假红**
（且每轮刷屏=告警疲劳）。

**判据沉淀**：跨端横切时**脚本名不等于端中立**——必须读源码确认它读的数据面
（同「真身待定位」那次：凭名字/凭印象判断 = 猜测）。

**⇒ 本守卫按 Hermes 端真实事实源重建同一职责**（对齐 QoderCN 版的四项：
软链 / 路径 / 引用 / 注入实证对账），⛔ 不 fork 那个脚本（它是他端资产）。

## 四项检查（对齐 qodercn_inject_chain_guard 的职责分解）

1. **注入链载体存在性**：`doenglingz-twin` 插件在 `config.yaml plugins.enabled` 里
   （⛔ 缺席 ⇒ 童灵通道整条断·最高危）
2. **三通道声明完整**：插件 `__init__.py` 同时注册 `pre_llm_call` / `post_llm_call`
   （少一个 = 注入或守护缺腿）
3. **注入台账新鲜度 + 档位字段**：`doenglingz_inject_state.json` 近 N 小时有写入
   且每行带 `d_tier`（**TSL 门控的数据源**·缺失则 TSL 树退化为"全局最新行"=跨会话串台）
4. **session_id 落库率**（**本端特有的真缺陷·2026-10-02 实测**）：台账行 `session_id`
   非空占比——此前插件走 argv 传参致注入器 `_PAYLOAD={}` ⇒ **恒空** ⇒ 门控串台。
   这是 Hermes 端接入 TSL 后**必须机械监控**的一条。

## 纪律（守卫编写规范 §八）

- 只记录不拦截：报告制恒 exit 0（`--strict` 时 RED 才 exit 1·仅供人工/CI）
- 保守判定：⛔ 判据全在本文件（端专属·无共脚本可复用·如实声明）
- 端隔离：⛔ 只读 `~/.hermes/`
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
import re
import sys
import time
from datetime import datetime, timedelta

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")
HERMES = os.path.join(HOME, ".hermes")
CONFIG = os.path.join(HERMES, "config.yaml")
TWIN = os.path.join(HERMES, "plugins", "doenglingz-twin", "__init__.py")
INJECT_STATE = os.path.join(HERMES, "doenglingz", "doenglingz_inject_state.json")

# 注入台账新鲜度阈值（小时）——按本端真实频率：pre_llm_call 每轮写
STALE_HOURS = 12
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"[记忆共享中心]/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def _enabled() -> list:
    try:
        import yaml
        cfg = yaml.safe_load(open(CONFIG, encoding="utf-8")) or {}
        return [str(x) for x in ((cfg.get("plugins") or {}).get("enabled") or [])]
    except Exception as exc:
        return [f"__read_error__:{exc!r}"]


def check() -> dict:
    findings = []
    now = datetime.now()

    # ① 注入链载体在册
    en = _enabled()
    if en and en[0].startswith("__read_error__"):
        findings.append({"level": "RED", "kind": "config_unreadable",
                         "detail": en[0]})
    elif "doenglingz-twin" not in en:
        findings.append({"level": "RED", "kind": "twin_not_enabled",
                         "detail": "doenglingz-twin 不在 config.yaml plugins.enabled"
                                   "⇒ 童灵注入/守护通道整条断（pre_llm_call+post_llm_call 皆失效）"})

    # ② 三通道声明
    if os.path.isfile(TWIN):
        src = open(TWIN, encoding="utf-8").read()
        hooks = set(re.findall(r"register_hook\(\s*[\"']([^\"']+)[\"']\s*,", src))
        for need, why in (("pre_llm_call", "注入腿"), ("post_llm_call", "守护腿")):
            if need not in hooks:
                findings.append({"level": "RED", "kind": "twin_hook_missing",
                                 "detail": f"doenglingz-twin 缺 {need}（{why}）·实有={sorted(hooks)}"})
    else:
        findings.append({"level": "RED", "kind": "twin_file_missing",
                         "detail": f"插件文件不存在：{TWIN}"})

    # ③ 台账新鲜度 + d_tier 字段
    rows = []
    if os.path.isfile(INJECT_STATE):
        try:
            age = now - datetime.fromtimestamp(os.path.getmtime(INJECT_STATE))
            if age > timedelta(hours=STALE_HOURS):
                findings.append({"level": "RED", "kind": "inject_state_stale",
                                 "detail": f"注入台账已 {age.seconds // 3600}h 未更新"
                                           f"（阈值 {STALE_HOURS}h）·pre_llm_call 可能停摆"})
        except OSError:
            pass
        for line in open(INJECT_STATE, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        if rows and not any(r.get("d_tier") for r in rows[-20:]):
            findings.append({"level": "RED", "kind": "d_tier_missing",
                             "detail": "近 20 行台账无 d_tier 字段 ⇒ TSL 门控"
                                       "（session_d_tier）拿不到档位·非D3也会产树/或D3不产"})
    else:
        findings.append({"level": "RED", "kind": "inject_state_missing",
                         "detail": f"注入台账不存在：{INJECT_STATE}（童灵注入从未跑过？）"})

    # ④ session_id 落库率（本端特有真缺陷的机械监控）
    if rows:
        recent = rows[-50:]
        with_sid = sum(1 for r in recent if str(r.get("session_id") or "").strip())
        rate = with_sid / len(recent)
        if rate < 0.5:
            findings.append({
                "level": "RED", "kind": "session_id_dropout",
                "detail": f"近 {len(recent)} 行台账仅 {with_sid} 行带 session_id"
                          f"（{rate:.0%}）⇒ 注入器走 argv 分支（_PAYLOAD={{}}）·"
                          f"TSL 档位门控退化为「全局最新行」= 跨会话串台。"
                          f"正解：插件走 stdin 载荷传 session_id"})

    return {
        "version": VERSION,
        "ts": now.isoformat(timespec="seconds"),
        "enabled": en,
        "state_rows": len(rows),
        "findings": findings,
        "red": sum(1 for f in findings if f["level"] == "RED"),
        "warn": sum(1 for f in findings if f["level"] == "WARN"),
    }


def _self_test() -> int:
    import tempfile
    passed = failed = 0

    def case(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print(f"  ❌ {name}")

    # 夹具 1：session_id 全空 ⇒ 必须报 dropout
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        for _ in range(5):
            f.write(json.dumps({"ts": "2026-10-02T00:00:00", "d_tier": "D1",
                                "session_id": ""}) + "\n")
        p1 = f.name
    old = INJECT_STATE
    try:
        globals()["INJECT_STATE"] = p1
        r1 = check()
        case("session_id 全空 → dropout",
             any(f["kind"] == "session_id_dropout" for f in r1["findings"]))
    finally:
        globals()["INJECT_STATE"] = old
        os.unlink(p1)

    # 夹具 2：session_id 齐 ⇒ 不得报 dropout
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        for i in range(5):
            f.write(json.dumps({"ts": "2026-10-02T00:00:00", "d_tier": "D1",
                                "session_id": f"s{i}"}) + "\n")
        p2 = f.name
    try:
        globals()["INJECT_STATE"] = p2
        r2 = check()
        case("session_id 齐 → 不报 dropout",
             not any(f["kind"] == "session_id_dropout" for f in r2["findings"]))
    finally:
        globals()["INJECT_STATE"] = old
        os.unlink(p2)

    # 夹具 3：d_tier 全缺 ⇒ 必须报 d_tier_missing
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        for i in range(3):
            f.write(json.dumps({"ts": "x", "session_id": f"s{i}"}) + "\n")
        p3 = f.name
    try:
        globals()["INJECT_STATE"] = p3
        r3 = check()
        case("d_tier 全缺 → d_tier_missing",
             any(f["kind"] == "d_tier_missing" for f in r3["findings"]))
    finally:
        globals()["INJECT_STATE"] = old
        os.unlink(p3)

    print(f"  self-test: {passed} passed, {failed} failed")
    print("MUT:OK" if failed == 0 else "MUT:FAIL")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Hermes 端注入链健康守卫")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return _self_test()

    rep = check()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"Hermes 注入链健康 · {rep['ts']} · {VERSION}")
        print(f"  台账行数 {rep['state_rows']}·插件 {len(rep['enabled'])} 个")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    if a.strict and rep["red"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())