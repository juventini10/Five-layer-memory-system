#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_inject_prompt.py — UserPromptSubmit 钩子：调用 router.py 硬匹配，置信门控注入上下文。

设计定位（路由家族 step③·风险有界版）：
- 单一真源：import router.route()（触发词从 15 个 SKILL.md desc 自动提取，v3.0.0 起含语义标签散列兜底）。
- 置信门控：
  · 唯一命中（len==1）→ 注入该 Skill 路由提示 + SSOT 格式契约。
  · 多命中（>1）→ v3.0.1/v3.0.2 起改为**非指令候选提示**（且不下发任一候选的格式契约）（列出全部候选·不指定调用谁）+ 歧义告警写入
    route_state.json。原「⚠️歧义…请调用该 Skill 执行」属自相矛盾指令：自己都判不了档还下祈使句，
    等于每轮把裁定负担推给模型（2026-09-20 better-harness 复盘 finding hooks-inject-conflicting-instructions）。
  · 显式命令轮（载荷含 <command-name> 或以 / 开头）→ 唯一命中也降级为提示，⛔与你显式命令抢方向盘
    （v3.0.0 修复：原"多命中静默不注入"是连锁盲区——router 修语义兜底后"写文案"类指令
     变为多命中反被门控丢弃，scriyore 仍不触发；现改为降级注入+告警而非黑箱丢弃）。
  · 0 命中 → 不注入，交软路由（feeder）语义召回。
- 格式契约注入（最优根治闭环·2026-08-12）：命中时额外调用 extract_format_contract() 实时从
  SSOT SKILL.md 抽取「回复/输出格式」契约拼接进注入上下文，使 AI 每次拉活源、无陈旧缓存可渲染。
- 写 /tmp/route_state.json 决策留痕（观测层，供对账）；`--selfcheck` 模式打印挂载注册状态+调用实证。
- 失败默认放行（exit 0），绝不阻断对话（守卫编写规范原则1/2）。

挂载实证（2026-08-24 童灵核查·绑实录）：
  · settings.json hooks.UserPromptSubmit 已注册本脚本（command: python3 .../route_inject_prompt.py UserPromptSubmit）。
  · traces/ 有 2026-08-24 当天多次调用记录；/tmp/route_state.json 有实跑决策留痕。
  · 结论：钩子已挂载且在跑，"是否注入属待验证项"旧注释有误导性，已删除。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
# Win console UTF-8 guard (auto by clock-loop 1.7.2 · 2026-10-12 并源嫁接)
import datetime

ROUTER_DIR = os.path.expanduser("[记忆共享中心]/脚本中心/Skill路由引擎/scripts")  # 2026-10-12 单点化：真源自身
sys.path.insert(0, ROUTER_DIR)
from router import route  # 单一真源
from format_contract import extract_format_contract  # SSOT 格式契约抽取（注入/校验共用）


# ── 输出协议单一真源（2026-09-04 根治·Qoder CN 裸文本被产品判 "winner=none" 整轮丢弃）──
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

_PAYLOAD = {}
def main():
    # --selfcheck 模式：打印挂载注册状态 + 最近调用实证（让"机制在跑"变成可观测事实）
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        return
    # --prompt 模式：argv 传参（hook stdin input 传递不可靠·2026-08-13 实证，与 feeder 同构）
    if len(sys.argv) > 2 and sys.argv[1] == "--prompt":
        prompt = sys.argv[2]
        _inject(prompt)
        return
    raw = ""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')  # 2026-10-12 并源：裸字节不炸（devtools 硬化块嫁接）
    except Exception:
        raw = ""
    # 离线诊断兼容：把原始 payload 追加写入 /tmp/wb_hook_probe.log（非致命，便于回归排查）
    # —— 折自已废弃的 route_verify_prompt.py，保留其不可约能力，单一真源、降表面积
    try:
        _evt = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        _pp = json.loads(raw) if raw else {}
        globals()["_PAYLOAD"] = _pp  # 供 hook_protocol 判端指纹
        _rec = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "argv_event": _evt,
            "prompt": _pp.get("prompt"),
            "session_id": _pp.get("session_id"),
            "permission_mode": _pp.get("permission_mode"),
            "hook_event_name": _pp.get("hook_event_name"),
        }
        with open("/tmp/wb_hook_probe.log", "a") as _f:
            _f.write(json.dumps(_rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    try:
        prompt = json.loads(raw).get("prompt", "")
    except Exception:
        prompt = ""
    _inject(prompt)


def _selfcheck():
    """挂载自检：打印 hooks 注册状态 + 最近调用实证（可观测，非注释猜测）"""
    import glob
    print("=== route_inject_prompt.py 挂载自检 ===")
    # 1. 注册状态
    registered = False
    try:
        d = json.load(open(os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "settings.json")))
        for evt, entries in d.get("hooks", {}).items():
            for e in entries:
                for h in e.get("hooks", []):
                    if "route_inject_prompt" in h.get("command", ""):
                        registered = True
                        print(f"  [注册] hooks.{evt} -> {h['command']}")
    except Exception as e:
        print(f"  [注册] 读取 settings.json 失败: {e}")
    if not registered:
        print("  [注册] ⚠️ 未在 hooks 中找到本脚本注册")
    # 2. 调用实证
    traces = sorted(glob.glob(os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "traces") + "/*/trace_*.json"),
                    key=os.path.getmtime, reverse=True)[:3]
    print(f"  [调用实证] traces/ 最近 {len(traces)} 条记录存在" if traces else "  [调用实证] ⚠️ 无 traces 调用记录")
    for t in traces:
        print(f"    - {os.path.basename(t)} ({datetime.datetime.fromtimestamp(os.path.getmtime(t)).isoformat(timespec='seconds')})")
    # 3. route_state 决策留痕
    try:
        with open("/tmp/route_state.json") as f:
            lines = f.readlines()
        print(f"  [决策留痕] /tmp/route_state.json 共 {len(lines)} 条记录")
    except Exception:
        print("  [决策留痕] ⚠️ 无 route_state.json（脚本从未成功写入）")
    print("=== 自检结束 ===")
    sys.exit(0)


def _inject(prompt):
    """注入主体（stdin 与 --prompt 共用）：置信门控唯一命中 → stdout 注入上下文"""
    if not prompt:
        return
    try:
        matched = route(prompt)
    except Exception:
        return

    decision = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "prompt": prompt,
        "matched": matched,
    }
    try:
        with open("/tmp/route_state.json", "a") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # 置信门控注入
    if len(matched) == 1:
        skill = matched[0]
        explicit = ("<command-name>" in prompt) or prompt.lstrip().startswith("/")
        if explicit:
            ctx = (
                "【路由引擎·候选提示（非指令）】本轮是显式命令轮，硬匹配候选 `%s` "
                "**仅作提示**——显式命令优先，不按本条改道（本条非指令）。" % skill
            )
            _emit(ctx, decision)   # v3.0.3：定档让位于显式命令，格式契约随之停发（独立复核补漏：原写法仍在此分支拼"以此为准"=半指令）
            return
        else:
            ctx = (
                "【路由引擎硬匹配】此消息命中技能 `%s`，请调用该 Skill 执行"
                "（不要绕过、不要手动 Edit 日志文件）。" % skill
            )
        # SSOT 格式契约实时注入（最优根治闭环）：拉活源、不依赖历史缓存
        contract = ""
        try:
            contract = extract_format_contract(skill)
        except Exception:
            contract = ""
        if contract:
            ctx += (
                "\n\n【SSOT 格式契约·实时拉取】以下为 `%s` 技能 SKILL.md 中“回复/输出格式”"
                "相关段落的实时抽取（每次拉活源、不依赖历史缓存），渲染该 Skill 回复时"
                "以此为准：\n%s" % (skill, contract)
            )
        _emit(ctx, decision)
    elif len(matched) > 1:
        # v3.0.0 修复：多命中不再静默丢弃——取首个降级注入 + 标⚠️歧义告警
        skill = matched[0]
        # v3.0.1：引擎自己都判不了档时⛔不下祈使指令——原写法「⚠️多命中歧义…请调用该 Skill
        # 执行」把裁定负担整包推给模型（每轮需自行仲裁，且指令与用户显式命令抢方向盘）。
        # 改为显式非指令：候选列全，裁定归实际意图/显式命令。
        ctx = (
            "【路由引擎·候选提示（非指令）】此消息命中多个技能：%s。引擎无法机械定档，"
            "**不指定调用哪一个**——以你的显式命令与实际意图为准自行裁定；若都不适用，忽略本条即可"
            "（本条非指令，⛔不要因它绕开显式命令；日志仍不手动 Edit）。"
            % "/".join(matched)
        )
        # v3.0.2：既然不定档，就⛔不同时下发 matched[0] 的「回复格式契约」并写"以此为准"——
        # 那等于把裁定负担只下推一半（口头说不指定，手上仍按首选注入格式=半指令·复核实测发现）。
        contract = ""
        if contract:
            ctx += (
                "\n\n【SSOT 格式契约·实时拉取】以下为 `%s` 技能 SKILL.md 中“回复/输出格式”"
                "相关段落的实时抽取（每次拉活源、不依赖历史缓存），渲染该 Skill 回复时"
                "以此为准：\n%s" % (skill, contract)
            )
        # 歧义告警写入决策留痕（供 route_audit 追）
        decision["ambiguity_warn"] = matched
        _emit(ctx, decision)
    sys.exit(0)


def _hp_emit(ctx, decision):
    """输出协议委托 hook_protocol 单一真源（⛔本脚本不再自选形态）。

    实测依据（2026-09-04）：Qoder CN 端裸文本 stdout 被产品判
    `winner=none (no parsed output)` 整轮丢弃 → 须 JSON envelope；
    ZCode 须 JSON（2026-08-27 实测）；WorkBuddy 吃裸文本 → 判据集中在真源。
    """
    if _hp is not None:
        mode = _hp.emit(ctx, payload=_PAYLOAD, argv=sys.argv[1:],
                        event="UserPromptSubmit", script=os.path.basename(__file__))
        decision["emit"] = "%s-via-hook_protocol" % mode
        return mode
    decision["emit"] = "text-fallback-no-module"  # 真源缺失=降级，留痕不静默
    sys.stdout.write(ctx)
    return "text"


def _emit(ctx: str, decision: dict) -> None:
    """输出适配：形态由 hook_protocol 判定（json / text），本脚本只负责组装文本。"""
    _hp_emit(ctx, decision)
    try:
        with open("/tmp/route_state.json", "a") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
