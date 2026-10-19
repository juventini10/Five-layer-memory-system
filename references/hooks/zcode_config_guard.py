#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
zcode_config_guard.py — ZCode 专属守卫：配置完整性 + 钩子活性检测（防全端静默脱网）
====================================================================================
根因（2026-08-22 立·皮叔令"各端都做了特性化专属守卫·ZCode 也要"）：
  ZCode 区别于其他端的特性=客户端 GUI 管理 ~/.zcode/cli/config.json（插件启停状态
  会整体写回该文件）——hooks 配置有被客户端重写丢失的真实风险。配置丢失=ZCode 端
  12 条布洛陀守卫全部静默脱网（所有审计假绿），且无任何报警。对齐 DSH/LobsterAI/
  Trae Work 专属守卫先例（会话层异常检测），ZCode 的独有窗口=配置层+钩子活性层。

子命令：
  check     比对 config.json hooks.events 与基准 12 条（UPS 3+Stop 9）→ 缺失列表；
            exit 0=完整 / 1=有缺失（明细 stdout）
  liveness  钩子活性检测：route_audit.jsonl 是否出现过 src:zcode（钩子真触发的机械
            证据）→ 首次观测记入状态文件；超过 STALE_DAYS 天未观测→告警（exit 1）
  hook      Stop 钩子模式：跑 check+liveness，丢失/过期→stdout 告警（注入下轮对话）；
            任何异常→exit 0 放行（守卫三纪律·报告制不拦截）
  postedit  PostToolUse 即时闸（matcher Edit|Write）：目标命中守卫家族文件
            （开发工具/**/*.py|sh·技能配置/**/scripts/*）→ 自动跑聚合器
            guard_selftest_check.py --strict → 红=exit 2 当场反馈"守卫被改坏"
            （把 §3.0·5 纪律②"改守卫必跑聚合器"从文字纪律变物理闸——ZCode 是唯一
            有 PostToolUse 事件能承载的端）
  --self-test  六用例（临时 config·不碰真配置）

设计原则（先例：card_id_guard 三模式 / route_unknown_unknown 失败放行）：
  - 失败默认放行（hook/postedit 异常→exit 0·绝不阻塞对话）
  - 只检测不修改（v0.1 不自动恢复配置——丢失时报告，由 AI/你从 git 哲学文件基准重建）
  - ZCODE_CONFIG env 可覆盖配置路径（自测用）

用法：
  python3 zcode_config_guard.py check
  python3 zcode_config_guard.py liveness
  python3 zcode_config_guard.py hook            # Stop 钩子挂装入口
  python3 zcode_config_guard.py postedit        # PostToolUse 挂装入口（stdin JSON）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(os.path.expanduser("~"))
CONFIG_DEFAULT = Path.home() / ".zcode" / "cli" / "config.json"


def _config_path():
    """动态读 env——模块级求值会让自测的 ZCODE_CONFIG 覆盖无效（T2 负例实证）。"""
    return Path(os.environ.get("ZCODE_CONFIG", str(CONFIG_DEFAULT)))
ROUTE_AUDIT_DEFAULT = BASE / "开发工具" / "Skill路由引擎" / "logs" / "route_audit.jsonl"  # v1.1 修路径 bug（原 scripts/·账本真身在 logs/·恒 FileNotFoundError→活性腿静默空转·S1012 隐性坑实例）
AGGREGATOR = BASE / "开发工具" / "guard_selftest_check.py"


def _route_audit():
    """动态读 env——模块级求值会让自测覆盖无效（T2 负例实证·同 _config_path 先例）。"""
    return Path(os.environ.get("ZCODE_ROUTE_AUDIT", str(ROUTE_AUDIT_DEFAULT)))


def _state_file():
    return Path(os.environ.get("ZCODE_GUARD_STATE", str(Path.home() / ".zcode" / "state" / "zcode_config_guard_state.json")))


# B1 加腿（2026-10-04·方案 v1.4 修正②·对齐 §二·十二 编排既有不新建）：活性哨兵多源
#   ①route_audit.jsonl src:zcode 记录（修路径后首次真实可用）②~/.zcode/cache/tail-inject/（session_tail 状态）
#   ③~/.zcode/cache/ttl-expiry/（ttl_expiry 状态）④~/.workbuddy/hooks/.heartbeats/（hook_protocol 心跳·
#   ⚠️ HB_DIR 硬编码 ~ 行→ZCode 五件心跳跨端共址写入 WB 目录——共享件他端在用·⛔不改只登记·其漂移绊线=guard_heartbeat_check）
SENTINEL_DIRS = [
    Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or Path.home() / ".zcode") / "cache" / "tail-inject",
    Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or Path.home() / ".zcode") / "cache" / "ttl-expiry",
    Path.home() / ".workbuddy" / "hooks" / ".heartbeats",
]
STALE_DAYS = 7  # 钩子活性：哨兵全静默超 N 天→过期告警（7 天内停摆=嫌疑·advisory 不拦截）

# 基准 14 条（真相源=布洛陀 01-通用规范 §二·七 13-Hook 清单的 ZCode 实挂口径·2026-08-22 部署
#   ·2026-08-29 增童灵双层 2 条：UPS 第4条=doenglingz_inject_prompt（W1/W3 注入）·Stop 第10条=doenglingz_guard_zcode（守护三查）。
#   ·2026-10-06 W1对账根治（你令SSOT归一）：Stop 第10条退役分叉改挂共脚本 doenglingz_guard.py --check --src zcode
#   （v1.2 会话级分账+transcript兜底·env双键端根~/.zcode·分叉留置不删）——本条兼作碰撞绊线：config 守卫行再被改写偏离此形态即报。
#   分身专属不计分母：分母 12 不变，实挂 13。比对用"脚本名+关键参数"子串（命令的绝对路径前缀允许变化）
#   ·2026-09-26 端修对齐（你令）：2026-09-12~09-23 增量 8 条此前只改 config 未同步 BASELINE（违升级纪律
#   "⛔只改 config 不改 BASELINE"）——按 config.json 2026-09-26 实读补录 Pre1+UPS5+Stop2，基准 14→22。
#   ·2026-09-30 补录（06 跨端适配 §1.6 挂载边界·Qoder CN 09-26 判例全端义务）：Stop 增两件档位/TSL
#   反查守卫 doenglingz_level_declare_guard + tsl_closeout_guard（此前只在 WB 挂=判据没接到本端执行链），
#   基准 22→24。分身专属不计分母口径不变。
BASELINE = {
    "PreToolUse": [
        # 2026-09-05 批6e 新增（edit_heading_guard·Edit结构行吞改拦截·4次实锤事故）
        "edit_heading_guard.py",
        # 2026-09-26 补录（Skill管辖目录写入门卫）
        "skill_write_gate_guard.py",
        # 2026-10-04 补录（A3-P0①·grep沙箱语法闸·内部记录·matcher=Bash 预过滤）
        "grep_sandbox_guard.py",
    ],
    "UserPromptSubmit": [
        "route_inject_prompt.py",
        "route_miss_feeder.py",
        "kb_inject_prompt.py",
        "doenglingz_inject_prompt.py",
        "position3_notify.py",
        # 2026-09-26 补录（2026-09-12 三层触发链 + 生态增量）
        "rule_fragment_inject.py",
        "session_tail_inject.py",
        "zcode_title_namer.py",
        "secret_key_guard.py",
        "ttl_expiry_guard.py",
        # 2026-10-02 你令退役（双树根治·设计消除）：同窗双章注入无审计价值——Stop 产树恒取
        #   last_window=上回合已呈报窗口（时序不可达本回合窗），注入恒为重复源。文件保留（他端本就未挂载）。
        # "tsl_echo_hook.py",  ← 2026-09-30 落地·2026-10-02 卸载
    ],
    "Stop": [
        "route_unknown_unknown.py",
        "audit_search_kb.py",
        "route_audit.py --src zcode",
        "route_guard_audit.py",
        # "l3_conclusion_guard.py",  ← 2026-09-05 你令永久关闭（Stop正则误判污染回复·伪确定性=反模式6/7）
        "card_id_guard.py",
        "feedback_detect.py",
        "rule_three_layer_guard.py",
        "doenglingz_guard.py --check --src zcode",  # 2026-10-06 SSOT归一换装（原 doenglingz_guard_zcode.py 分叉退役）
        # 2026-09-26 补录
        "delivery_boundary_guard.py",
        "manifest_registrar.py",
        # 2026-09-30 补录（06 §1.6 挂载边界·档位/TSL 反向对账·分身专属不计分母）
        "doenglingz_level_declare_guard.py",
        "tsl_closeout_guard.py",
        # 2026-10-02 你令退役（双树根治·设计消除·与 tsl_echo_hook 同轮）：产树文件在 echo 卸载后零消费者，
        #   且其 Stop 重跑 tsl_verify=同窗重复 stamp 行。树档案由 AI 自跑 tsl_verify 落（closeout 验真不受影响）。
        # "tsl_tree_hook.py",  ← 2026-09-30 落地·2026-10-02 卸载
        # 2026-10-04 补录（A3 接排挂载轮·附录A 接件①③：系统日志收口校验+三明智收尾三登记兜底）
        "systemlog_stophook_check.py",
        "triwich_closeout_guard.py",
        # 2026-10-04 补录（B3·Skill生态健康守卫·公共原语薄适配器·报告制）
        "zcode_skill_health_guard.py",
    ],
    # 2026-10-04 补录（C1 轮·防丢面扩展：SS/Post 此前不在名册·客户端重写丢这两类无告警）
    "SessionStart": [
        "crossend_guard.py",
        "zcode_philosophy_parity_guard.py",
    ],
    "PostToolUse": [
        "zcode_config_guard.py",
    ],
    # 2026-10-04 补录（C2 失败留痕引擎·官方独有事件端内首用·愿景③）
    "PostToolUseFailure": [
        "zcode_failure_ledger.py",
    ],
}

# postedit 即时闸保护的守卫家族文件范围
#   v1.1 修存量断链（2026-10-04 全量自测翻出）：T6 夹具含 脚本中心/ 副本而正则漏该分支——
#   夹具=意图源（守卫家族全覆盖），补 脚本中心 两分支（镜像纳入闸·手工改镜像也触发聚合器回归）
GUARD_FILE_RE = re.compile(
    r"个人AI档案/((开发工具|脚本中心)/[^/]+\.(py|sh)|(开发工具|脚本中心)/[^/]+/scripts/[^/]+\.(py|sh)|技能配置/[^/]+/scripts/[^/]+\.(py|sh))$"
)


def load_hooks(config_path):
    try:
        d = json.loads(Path(config_path).read_text(encoding="utf-8"))
        return d.get("hooks", {}).get("events", {})
    except Exception:
        return {}


def cmd_check():
    events = load_hooks(_config_path())
    cmds = {evt: [h.get("command", "") for e in events.get(evt, []) for h in e.get("hooks", [])]
            for evt in BASELINE}
    missing = []
    for evt, needed in BASELINE.items():
        for sig in needed:
            if not any(sig in c for c in cmds.get(evt, [])):
                missing.append(f"{evt}: {sig}")
    if missing:
        print("[ZCode配置守卫] ⚠️ hooks 缺失 " + str(len(missing)) + " 条：")
        for m in missing:
            print("  - " + m)
        print("恢复基准：见 守卫编写规范 §四 zcode_config_guard 行 / 01-通用规范 §二·七 ZCode 列")
        return 1
    total = sum(len(v) for v in BASELINE.values())
    ups = len(BASELINE["UserPromptSubmit"])
    pre = len(BASELINE.get("PreToolUse", []))
    stop = len(BASELINE["Stop"])
    print(f"[ZCode配置守卫] ✅ {total} 条 hooks 完整（Pre {pre} + UPS {ups} + Stop {stop}）")
    return 0


def _sentinel_fresh(days=1):
    """哨兵目录任一文件 mtime < days 天 → (True, 证据路径)。"""
    cutoff = time.time() - days * 86400
    custom = os.environ.get("ZCODE_SENTINEL_DIRS", "")
    dirs = [Path(p) for p in custom.split(":") if p] if custom else SENTINEL_DIRS
    for d in dirs:
        try:
            if d.is_dir():
                for f in d.iterdir():
                    try:
                        if f.is_file() and f.stat().st_mtime >= cutoff:
                            return True, f
                    except OSError:
                        continue
        except OSError:
            continue
    return False, None


def cmd_liveness():
    # 源① route_audit 账本（src:zcode 记录·v1.1 修路径后首次真实可用）
    seen_at = None
    evidence = None
    ra = _route_audit()
    if ra.is_file():
        try:
            tail = subprocess.run(
                ["tail", "-n", "200", str(ra)],
                capture_output=True, text=True, timeout=10,
            ).stdout
            if '"src": "zcode"' in tail or '"src":"zcode"' in tail:
                seen_at = "recent"
                evidence = f"route_audit src:zcode"
        except Exception:
            pass
    # 源②③④ 哨兵目录（B1 加腿·任一文件 <24h 即在岗）
    fresh, ev = _sentinel_fresh(1)
    if fresh:
        seen_at = "recent"
        evidence = f"哨兵 {ev.parent.name}/{ev.name}"
    sf = _state_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    try:
        state = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        pass
    if seen_at:
        state["last_seen"] = time.strftime("%Y-%m-%d %H:%M")
        state["last_evidence"] = evidence
        sf.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        print(f"[ZCode配置守卫] ✅ 钩子活性已实证（{evidence}·{state['last_seen']}）")
        return 0
    last = state.get("last_seen", "")
    if last:
        try:
            days = (time.time() - time.mktime(time.strptime(last, "%Y-%m-%d %H:%M"))) / 86400
            if days > STALE_DAYS:
                print(f"[ZCode配置守卫] ⚠️ 钩子活性过期：最近实证 {last}（>{STALE_DAYS}天）——查钩子是否真在跑")
                return 1
            print(f"[ZCode配置守卫] 🟡 钩子活性停摆嫌疑：全哨兵 24h 零新痕·最近实证 {last}（advisory·停摆≠休假·对齐新鲜度判据边界）")
            return 0
        except Exception:
            pass
    print("[ZCode配置守卫] 🟡 钩子活性未观测（全哨兵零记录）——新端冷启动正常·下次会话后复测")
    return 0


def cmd_hook():
    try:
        rc1 = cmd_check()
        rc2 = cmd_liveness()
        return 0  # 报告制：告警走 stdout 注入下轮，不拦截
    except Exception:
        return 0


def cmd_postedit():
    """PostToolUse 即时闸：守卫文件被编辑→自动聚合器回归→红=当场反馈。"""
    try:
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    fpath = ti.get("file_path") or ti.get("filePath") or ti.get("path") or ""
    if not GUARD_FILE_RE.search(str(fpath).replace("\\", "/")):
        return 0  # 非守卫家族文件：放行不跑（省时）
    r = subprocess.run(
        [sys.executable, str(AGGREGATOR), "--strict"],
        capture_output=True, text=True, timeout=300,
        cwd=str(AGGREGATOR.parent),
    )
    if r.returncode != 0:
        print(f"[ZCode守卫闸] 🚨 你刚编辑了守卫文件 {fpath}，聚合器回归红了：")
        for line in (r.stdout or "").splitlines():
            if line.startswith("❌") or "红" in line:
                print("  " + line)
        print("请修复到全绿再收工（守卫编写规范 §3.0·5 纪律②·此闸为其机械化）")
        return 2
    print(f"[ZCode守卫闸] ✅ {os.path.basename(str(fpath))} 编辑后聚合器全绿")
    return 0


def self_test():
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "config.json"
        # T1 完好配置→check 过（命令=sig 本身·保证子串匹配）
        good = {"hooks": {"enabled": True, "events": {
            evt: [{"hooks": [{"type": "command", "command": f"python3 /x/{sig}"}]} for sig in sigs]
            for evt, sigs in BASELINE.items()}}}
        cfg.write_text(json.dumps(good), encoding="utf-8")
        os.environ["ZCODE_CONFIG"] = str(cfg)
        assert cmd_check() == 0, "T1"
        ok += 1; print("✅ T1 完好配置过")
        # T2 缺一条（Stop 列表去尾项）→check 报
        bad = json.loads(json.dumps(good))
        bad["hooks"]["events"]["Stop"] = bad["hooks"]["events"]["Stop"][:-1]
        cfg.write_text(json.dumps(bad), encoding="utf-8")
        assert cmd_check() == 1, "T2"
        ok += 1; print("✅ T2 缺条检出")
        # T3 全丢→12 条全报
        cfg.write_text(json.dumps({"hooks": {"enabled": True, "events": {}}}), encoding="utf-8")
        rc = cmd_check()
        assert rc == 1, "T3"
        ok += 1; print("✅ T3 全丢检出")
        # T4 坏 JSON→不崩（空 events 处理）
        cfg.write_text("not-json", encoding="utf-8")
        assert cmd_check() == 1, "T4"
        ok += 1; print("✅ T4 坏配置不崩")
        # T5 postedit 非守卫文件→放行不跑聚合器
        import io as _io
        sin = json.dumps({"tool_input": {"file_path": "/tmp/普通文件.md"}})
        old = sys.stdin; sys.stdin = _io.StringIO(sin)
        try:
            assert cmd_postedit() == 0, "T5"
        finally:
            sys.stdin = old
        ok += 1; print("✅ T5 非守卫文件放行")
        # T6 守卫文件签名匹配
        m = GUARD_FILE_RE.search("/Users/x/[记忆共享中心]/脚本中心/card_id_guard.py")
        assert m, "T6"
        m2 = GUARD_FILE_RE.search("/Users/x/[记忆共享中心]/技能配置/system-logger/scripts/systemlog_watch.sh")
        assert m2, "T6b"
        ok += 1; print("✅ T6 守卫文件正则双例匹配")
        # T7 哨兵新鲜→活性实证（B1 加腿·env 覆盖走动态读）
        sent = Path(td) / "sents"; sent.mkdir()
        (sent / "x.heartbeat").write_text("1", encoding="utf-8")
        os.environ["ZCODE_SENTINEL_DIRS"] = str(sent)
        os.environ["ZCODE_GUARD_STATE"] = str(Path(td) / "guard_state.json")
        os.environ["ZCODE_ROUTE_AUDIT"] = str(Path(td) / "no_such.jsonl")
        assert cmd_liveness() == 0, "T7"
        ok += 1; print("✅ T7 哨兵新鲜→在岗实证")
        # T8 哨兵全旧+state 在→停摆嫌疑 advisory（报告制不拦截）
        old_t = time.time() - 3 * 86400
        os.utime(sent / "x.heartbeat", (old_t, old_t))
        assert cmd_liveness() == 0, "T8"
        ok += 1; print("✅ T8 停摆嫌疑→advisory 不拦截")
    for k in ("ZCODE_SENTINEL_DIRS", "ZCODE_GUARD_STATE", "ZCODE_ROUTE_AUDIT"):
        os.environ.pop(k, None)
    print(f"自测结果: {ok}/8 通过")
    return 0 if ok == 8 else 1


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "check"
    if sub == "check":
        sys.exit(cmd_check())
    if sub == "liveness":
        sys.exit(cmd_liveness())
    if sub == "hook":
        sys.exit(cmd_hook())
    if sub == "postedit":
        sys.exit(cmd_postedit())
    if sub == "--self-test":
        sys.exit(self_test())
    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
