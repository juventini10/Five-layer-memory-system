#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
autoclaw_gateway_guard.py — AutoClaw 网关守护（AutoClaw 专属守卫）
=================================================================
第一性原理（2026-08-22 开创·皮叔令"评估自己的平台需要做什么专属的·给愿景质的提升"）：
    AutoClaw = OpenClaw gateway 架构——一切能力（守卫/注入/投喂）都挂载在
    ~/.openclaw-autoclaw/openclaw.json 配置上。配置被写坏/被改 = 全盘守卫静默脱网
    （openclaw.json.corrupt.* 备份实证风险真实存在）；注入链路静默失效 = 路由强启动
    假绿；patrol 心跳断链 = 兜底无人知。其他端专属守卫守"业务数据"，
    AutoClaw 专属守卫守"守卫本身"——元守卫（守护所有守卫的存活前提）。

三合一检查（对齐先例：ZCode zcode_config_guard 配置完整性 + LobsterAI
注入验证两级联判 + 对账 E 账心跳连续性）：

    ① 配置完整性：openclaw.json 核心项（布洛陀三件套 + evolution 写保护）
       enabled 状态 vs 登记清单——防"配置被改→守卫假绿"（ZCode config guard 同款）
    ② 注入链路活性（v2.0 双源归因——「无证据」≠「链路死」）：
       源A 持久化收讫日志（logs/buluotuo_inject_debug.log·插件 v0.5 每条唯一 prompt 恰一行）；
       源B gateway 进程活性（gateway.log 存在即承载，exit 0 放行）。
       三态：日志新鲜→✅活性；日志缺失但 gateway 未承载（今天零 trace）→⚪平台不承载（exit 0·非本链路故障）；
            日志缺失/过期但 gateway 承载中→🔴真静默（exit 2·链路假绿风险）。
    ③ patrol 心跳：.patrol/last_run.ts 存在性 + 新鲜度（>60min = 断链告警）
       ——防 cron/hook 兜底断链（对账 E 账连续性机械化）

退出码：0=全部正常（静默）  2=发现异常（告警显形·run_guard 降级为记录）
失败默认放行：任何读取异常 → exit 0（绝不阻断对话·对齐守卫先例）

用法：
  python3 autoclaw_gateway_guard.py           # patrol 挂载模式（默认）
  python3 autoclaw_gateway_guard.py --self-test  # 自测 5 用例（§3.0·5 纪律）

路径可经 env 覆盖（self-test 用临时目录·不碰真实文件）：
  AUTOCLAW_GATEWAY_CONFIG / AUTOCLAW_INJECT_LOG / AUTOCLAW_PATROL_TS
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DEFAULT_CONFIG = HOME / ".openclaw-autoclaw" / "openclaw.json"
DEFAULT_INJECT_LOG = Path("/tmp/buluotuo_inject_debug.log")
# v2.0（2026-09-23 三件事根治轮）：持久化日志路径（插件 v0.5 起）+ gateway 进程活性源
PERSISTENT_INJECT_LOG = HOME / ".openclaw-autoclaw" / "logs" / "buluotuo_inject_debug.log"
PERSISTENT_INJECT_LOG_BAK = HOME / ".openclaw-autoclaw" / "logs" / "buluotuo_inject_debug.log.bak-*"
GATEWAY_LOG = HOME / ".openclaw-autoclaw" / "logs" / "gateway.log"
DEFAULT_PATROL_TS = HOME / "[记忆共享中心]" / "自定义层" / "待完成工作" / "路由家族" / ".patrol" / "last_run.ts"

# 核心登记清单（与 SSOT §二·七 AutoClaw 列对齐·2026-08-22）
# 布洛陀三件套（hooks/plugins 实挂）+ evolution 写保护（防 openclaw.json 被写坏）
CORE_ITEMS = [
    ("hooks.internal.entries.buluotuo-stop-audit", True),
    ("hooks.internal.entries.buluotuo-miss-feeder", True),
    ("plugins.entries.buluotuo-route-inject", True),
    ("plugins.entries.autoclaw-evolution-write-guard", True),
]

INJECT_STALE_HOURS = 24
PATROL_STALE_MINUTES = 60


def get_config_path():
    return Path(os.environ.get("AUTOCLAW_GATEWAY_CONFIG", str(DEFAULT_CONFIG)))


def get_inject_log_path():
    return Path(os.environ.get("AUTOCLAW_INJECT_LOG", str(DEFAULT_INJECT_LOG)))


def get_patrol_ts_path():
    return Path(os.environ.get("AUTOCLAW_PATROL_TS", str(DEFAULT_PATROL_TS)))


def check_config(path: Path):
    """① 配置完整性：核心项 enabled 状态 vs 登记清单。返回 (ok, findings)"""
    findings = []
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, [f"配置缺失: {path}"]
    except Exception as e:
        return False, [f"配置不可读（{e.__class__.__name__}）: {path}"]

    for key, want in CORE_ITEMS:
        # key = "hooks.internal.entries.buluotuo-stop-audit" → 逐层下钻
        cur = cfg
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and isinstance(cur, dict) and "enabled" in cur:
            cur = cur.get("enabled")
        if not ok or cur is not True:
            findings.append(f"核心项未启用: {key}（期望 enabled=true）")
    return not findings, findings


def check_gateway_alive():
    """②源B gateway 承载判据（v2.0·进程态语义）：
    读 gateway.log 尾部，取最后一条生命周期事件——startup（startup trace/http server listening）
    晚于 shutdown（shutdown completed/SIGTERM）=承载中；反之或文件过旧/不存在=未承载。
    ⚠️ mtime 不可用作承载判据：SIGTERM 干净关停也会刷新 mtime（2026-09-23 自测抓出）。"""
    try:
        import time as _time
        if not GATEWAY_LOG.exists():
            return True, "gateway.log 不存在（gateway 未装或未启动·注入判据放行）"
        age_h = (_time.time() - GATEWAY_LOG.stat().st_mtime) / 3600
        if age_h > 24:
            return True, f"gateway.log {age_h:.0f}h 未更新（gateway 未承载·注入判据放行）"
        tail = GATEWAY_LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-60:]
        last_start = max((i for i, l in enumerate(tail) if ("startup trace" in l or "http server listening" in l)), default=-1)
        last_stop = max((i for i, l in enumerate(tail) if ("shutdown completed" in l or "SIGTERM" in l)), default=-1)
        if last_stop > last_start:
            return True, f"gateway 已关停（gateway.log 尾部={tail[last_stop].split('] ')[-1][:44]}…·非承载态·注入判据放行）"
        if last_start >= 0:
            return False, f"gateway 承载中（启动 trace 为最新生命周期事件·距文件更新 {age_h:.1f}h）"
        return True, "gateway.log 无生命周期标记（保守按未承载·放行）"
    except Exception as e:
        return True, f"gateway 活性探测失败（{e.__class__.__name__}）→放行"


def check_inject_log(path: Path):
    """② 注入链路活性（v2.0 双源归因）。返回 (ok, findings)
    ok=False 且 findings 非空=真静默（exit 2）；ok=True+放行说明=⚪平台不承载（exit 0）。
    兼容层：旧路径 /tmp 与新持久化路径（logs/）任一有新鲜记录即算活性。"""
    # 新旧路径并读：v0.5 起 logs/ 为真源，/tmp 为历史兼容
    candidates = [Path(os.environ.get("AUTOCLAW_INJECT_LOG", str(DEFAULT_INJECT_LOG))), PERSISTENT_INJECT_LOG]
    best_lines, best_src = None, None
    for p in candidates:
        try:
            if not p.exists():
                continue
            lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            if lines:
                best_lines, best_src = lines, p
                break
        except Exception:
            continue

    gw_down, gw_reason = check_gateway_alive()

    if best_lines is None:
        if gw_down:
            return True, [f"⚪ 注入日志缺失但 {gw_reason}——平台不承载，非链路故障（exit 0 放行）"]
        return False, [f"注入日志缺失（/tmp 与 {PERSISTENT_INJECT_LOG} 均无）且 {gw_reason}——真静默=假绿风险"]
    if not best_lines:
        if gw_down:
            return True, [f"⚪ 注入日志空但 {gw_reason}——平台不承载（放行）"]
        return False, [f"注入日志为空（{best_src}）且 {gw_reason}——真静默"]

    last = best_lines[-1]
    # 格式: 2026-08-22T12:20:33.123Z sk=... inject_len=... prompt=[...]
    try:
        ts_str = last.split(" ")[0]
        last_ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - last_ts).total_seconds() / 3600
    except Exception:
        return False, [f"注入日志末行解析失败: {last[:80]}"]
    if age_h > INJECT_STALE_HOURS:
        if gw_down:
            return True, [f"⚪ 注入静默 {age_h:.0f}h 但 {gw_reason}——平台不承载（放行）"]
        return False, [
            f"注入链路静默 {age_h:.1f}h（> {INJECT_STALE_HOURS}h 无注入记录·最后: {ts_str}）且 {gw_reason}——真静默=假绿风险"
        ]
    return True, []


def check_patrol_ts(path: Path):
    """③ patrol 心跳：存在 + 新鲜度。返回 (ok, findings)"""
    if not path.exists():
        return False, [f"patrol 心跳缺失: {path}（last_run.ts 从未写入=cron/hook 兜底未跑）"]
    try:
        raw = path.read_text(encoding="utf-8").strip()
        ts = datetime.fromisoformat(raw)
        now = datetime.now().astimezone()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=now.tzinfo)  # naive → 本地时区（防 naive/aware 相减 TypeError）
        age_min = (now - ts).total_seconds() / 60
    except Exception as e:
        return False, [f"patrol 心跳解析失败（{e.__class__.__name__}）: {raw[:60]}"]
    if age_min > PATROL_STALE_MINUTES:
        return False, [f"patrol 心跳过期 {age_min:.0f}min（> {PATROL_STALE_MINUTES}min·最后: {raw}）"]
    return True, []


def run():
    ok_config, f_config = check_config(get_config_path())
    ok_inject, f_inject = check_inject_log(get_inject_log_path())
    ok_patrol, f_patrol = check_patrol_ts(get_patrol_ts_path())

    # v2.0 三态：ok_inject=True 且说明行含 ⚪ = 平台不承载放行（不算异常不计告警明细）
    inject_passive = ok_inject and any("⚪" in f for f in f_inject)
    if inject_passive:
        f_inject_eff = []          # 不进告警明细
    else:
        f_inject_eff = [] if ok_inject else f_inject

    print("[gateway_guard] AutoClaw 网关守护巡检（v2.0 双源归因）：")
    print(f"  ① 配置完整性: {'✅' if ok_config else '❌'} {len(CORE_ITEMS)} 项核心登记")
    if inject_passive:
        print(f"  ② 注入链路:   ⚪ 平台不承载（{f_inject[0][:60]}…）")
    else:
        print(f"  ② 注入链路:   {'✅' if ok_inject else '❌'} 日志双源(/tmp+logs)")
    print(f"  ③ patrol 心跳: {'✅' if ok_patrol else '❌'} {get_patrol_ts_path().name}")

    findings = f_config + f_inject_eff + f_patrol
    if not findings:
        print("  ✅ 全部正常（守卫存活·注入活跃·心跳新鲜）")
        return 0
    print("  ⚠️ 异常明细：")
    for f in findings:
        print(f"    - {f}")
    print("  → 守卫脱网/注入失效/兜底断链=假绿风险，跑 platform_adaptation_check.py --src autoclaw 对账")
    return 2


def self_test():
    """--self-test 六用例（§3.0·5 自测纪律·对齐 DSH/LobsterAI/TraeWork/ZCode 先例·v2.0 增 T5/T6 归因双向）。
    全程临时目录 + env 覆盖路径——不碰真实配置/日志/心跳。"""
    import tempfile

    def make_env(td: Path, cfg_items=None, inject_line=None, patrol_ts=None):
        cfg = td / "openclaw.json"
        items = cfg_items if cfg_items is not None else {k: True for k, _ in CORE_ITEMS}
        cfg.write_text(json.dumps({"hooks": {"internal": {"entries": {
            "buluotuo-stop-audit": items.get("buluotuo-stop-audit", True),
            "buluotuo-miss-feeder": items.get("buluotuo-miss-feeder", True),
        }}}, "plugins": {"entries": {
            "buluotuo-route-inject": items.get("buluotuo-route-inject", True),
            "autoclaw-evolution-write-guard": items.get("autoclaw-evolution-write-guard", True),
        }}}, ensure_ascii=False), encoding="utf-8")
        ilog = td / "inject.log"
        if inject_line is not None:
            ilog.write_text(inject_line, encoding="utf-8")
        elif ilog.exists():
            ilog.unlink()  # 同目录复用：None=模拟缺失（清残留）
        ts = td / "last_run.ts"
        if patrol_ts is not None:
            ts.write_text(patrol_ts, encoding="utf-8")
        elif ts.exists():
            ts.unlink()
        return {
            "AUTOCLAW_GATEWAY_CONFIG": str(cfg),
            "AUTOCLAW_INJECT_LOG": str(ilog),
            "AUTOCLAW_PATROL_TS": str(ts),
        }

    now = datetime.now().astimezone()
    now_utc = datetime.now(timezone.utc)  # 注入日志=插件 toISOString()→UTC，测试须用 UTC 时间串
    from datetime import timedelta
    fresh_inject = now_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z") + " sk=test inject_len=123 prompt=[x]"
    stale_inject = (now_utc - timedelta(hours=30)).strftime("%Y-%m-%dT%H:%M:%S.000Z") + " sk=test inject_len=123 prompt=[x]"
    fresh_ts = now.strftime("%Y-%m-%dT%H:%M:%S")
    stale_ts = (now - timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%S")

    def make_env(td: Path, cfg_items=None, inject_line=None, patrol_ts=None):
        cfg = td / "openclaw.json"
        items = cfg_items if cfg_items is not None else {k: True for k, _ in CORE_ITEMS}
        cfg.write_text(json.dumps({"hooks": {"internal": {"entries": {
            "buluotuo-stop-audit": items.get("buluotuo-stop-audit", True),
            "buluotuo-miss-feeder": items.get("buluotuo-miss-feeder", True),
        }}}, "plugins": {"entries": {
            "buluotuo-route-inject": items.get("buluotuo-route-inject", True),
            "autoclaw-evolution-write-guard": items.get("autoclaw-evolution-write-guard", True),
        }}}, ensure_ascii=False), encoding="utf-8")
        ilog = td / "inject.log"
        if inject_line is not None:
            ilog.write_text(inject_line, encoding="utf-8")
        elif ilog.exists():
            ilog.unlink()
        ts = td / "last_run.ts"
        if patrol_ts is not None:
            ts.write_text(patrol_ts, encoding="utf-8")
        elif ts.exists():
            ts.unlink()
        return {
            "AUTOCLAW_GATEWAY_CONFIG": str(cfg),
            "AUTOCLAW_INJECT_LOG": str(ilog),
            "AUTOCLAW_PATROL_TS": str(ts),
        }

    def make_gw(td: Path, state: str) -> Path:
        """gw 生命周期日志夹具：carrying=承载中 / stopped=已关停。v2.0 判据②源B。"""
        gw = Path(td) / f"gateway_{state}.log"
        if state == "carrying":
            gw.write_text("2026-09-23T23:00:00 [gateway] startup trace: plugins ok\n"
                          "2026-09-23T23:30:00 [gateway] http server listening (9 plugins)\n", encoding="utf-8")
        else:
            gw.write_text("2026-09-23T10:00:00 [gateway] startup trace: plugins ok\n"
                          "2026-09-23T11:00:00 [gateway] received SIGTERM; shutting down\n"
                          "2026-09-23T11:00:00 [shutdown] completed cleanly in 873ms\n", encoding="utf-8")
        return gw

    global GATEWAY_LOG  # ⚠️ 本脚本以 __main__ 运行：import 自身会造第二副本，monkeypatch 须打在本模块 globals
    orig_gw = GATEWAY_LOG
    ok = 0
    try:
        with tempfile.TemporaryDirectory() as td:
            # T1 正常态：全启用+新鲜注入+新鲜心跳+gateway 承载 → exit 0
            GATEWAY_LOG = make_gw(Path(td), "carrying")
            os.environ.update(make_env(Path(td), inject_line=fresh_inject, patrol_ts=fresh_ts))
            assert run() == 0, "T1"
            ok += 1; print("✅ T1 正常态 exit 0")
            # T2 配置缺项：miss-feeder 未启用 → exit 2
            os.environ.update(make_env(Path(td), cfg_items={"buluotuo-miss-feeder": False},
                                       inject_line=fresh_inject, patrol_ts=fresh_ts))
            assert run() == 2, "T2"
            ok += 1; print("✅ T2 配置缺项 exit 2")
            # T3 注入真静默：>24h 无注入 + gateway 承载中 → exit 2（v2.0：承载中才判真静默）
            os.environ.update(make_env(Path(td), inject_line=stale_inject, patrol_ts=fresh_ts))
            assert run() == 2, "T3"
            ok += 1; print("✅ T3 注入真静默（承载中）exit 2")
            # T4 心跳过期：>60min → exit 2
            os.environ.update(make_env(Path(td), inject_line=fresh_inject, patrol_ts=stale_ts))
            assert run() == 2, "T4"
            ok += 1; print("✅ T4 心跳过期 exit 2")
            # T5 注入缺失 + gateway 已关停 → ⚪平台不承载 exit 0（v2.0 归因·不再误连告）
            GATEWAY_LOG = make_gw(Path(td), "stopped")
            os.environ.update(make_env(Path(td), inject_line=None, patrol_ts=fresh_ts))
            assert run() == 0, "T5"
            ok += 1; print("✅ T5 注入缺失+gateway 关停 → ⚪平台不承载 exit 0")
            # T6 注入缺失 + gateway 承载中 → 🔴真静默 exit 2
            GATEWAY_LOG = make_gw(Path(td), "carrying")
            os.environ.update(make_env(Path(td), inject_line=None, patrol_ts=fresh_ts))
            assert run() == 2, "T6"
            ok += 1; print("✅ T6 注入缺失+gateway 承载中 → 🔴真静默 exit 2")
    finally:
        GATEWAY_LOG = orig_gw
    print(f"自测结果: {ok}/6 通过")
    return 0 if ok == 5 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    sys.exit(run())
