#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doenglingz_skill_onduty_tier_promote.py v2.0.1 — Skill 启动事件 → 本回合 D3 升档（源侧转正·端中立）

源侧沿革：v2.0.0=2026-10-10 Qoder CN 端层首装实证；v2.0.1=2026-10-12 皮叔令「要脱敏入包」
  → 真源归位 开发工具（端实体改软链·单一真源），LOG/SKILL_ROOTS/src 三处单端硬编码全部
  config 根派生（承 06 L1166 写读同根纪律）；各端挂载指引=12-端适配协议「端侧机械面装载指引」节。

治什么（06 §补充节「启动侧」的第二条入口）：
  「触发即上岗」原只有**词面腿**——用户消息命中 Skill 触发词 → W1 钩子在 UserPromptSubmit
  注入 D3 契约（inject_prompt W1_TRIGGERS 2026-10-04 收 growth-box 显式调用词）。
  但当使用者没写触发词、而 AI 依 `铁律-023 Channel C` 等**主动调用 Skill 工具**时，
  消息词面不命中 ⇒ 注入层维持 D1 ⇒ 该回合按 06 §1.6 互斥律「不得产树」，
  而 growth-box 自身条款又说「启动即上岗、收尾须 relay TSL」⇒ 两指令对冲，
  AI 只能服从机制禁令（D1 ⛔产树）并把冲突显形。2026-10-10 11:5x 本端实证。

机制化（把工单 P2 从口头挂账变成件）：
  真源=**Skill 自声明** `requires_twin_on_duty: true`（frontmatter·全端同源·非硬编码名单）
  本脚本=**事件腿**：PreToolUse(matcher=Skill) 捕获启动动作 →
    ①向注入器同一 state 文件（`<端config>/doenglingz_inject_state.json`）追加一行
      d_tier=D3（同 schema·同文件·档位判定单文件真源不另起一本账；写者是新增事件腿，
      词面腿逻辑零改动）⇒ Stop 侧 `doenglingz_level_declare_guard._expected_tier()`
      取本会话最近一行 ⇒ 本回合的 TSL 树合法，且「静默分支」（D3 在场+零 TSL）开始生效
    ②非阻断提示（exit 0）：告知本回合已升 D3、收口前须实跑 tsl_verify --full 并 relay

纪律（守 Hook 三条·见 06 取证 §2.2 Qoder CN 行）：
  ⛔不阻断（永远 exit 0）；⛔不造噪音（异常静默放行）；⛔不猜会话号
  （取不到 sid ⇒ 不写行——对齐 guard「无会话号＝不判也不猜」纪律）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import io
import json
import os
import re
import sys

ONDUTY_KEY = "requires_twin_on_duty"
TIER = "D3"


def _cfg_root():
    return (os.environ.get("DOENGLINGZ_CONFIG_DIR")
            or os.environ.get("WORKBUDDY_CONFIG_DIR")
            or os.path.expanduser("~/.workbuddy"))


def _skill_roots():
    """端中立扫描根：①本端 config/skills（settings 挂载端实体层）②技能配置唯一真源（软链家）。
    SKILL_ROOTS_EXTRA（冒号分隔）供特殊布局端显式追加；⛔不写死单端名。"""
    extra = [os.path.expanduser(x) for x in os.environ.get("SKILL_ROOTS_EXTRA", "").split(":") if x]
    return extra + [os.path.join(_cfg_root(), "skills"),
                    os.path.expanduser("[记忆共享中心]/技能配置")]


def _payload_obj():
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _get(obj, *keys):
    for k in keys:
        v = obj.get(k)
        if v:
            return v
    return ""


def _frontmatter_flag(skill_name):
    """读 Skill 自声明：frontmatter 内 `requires_twin_on_duty: true`。缺文件/缺字段=False。"""
    if not skill_name:
        return False
    for root in _skill_roots():
        p = os.path.join(root, skill_name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        try:
            with io.open(p, encoding="utf-8") as f:
                head = f.read(4000)
        except Exception:
            continue
        fm = re.match(r"^---\s*\n(.*?)\n---", head, re.S)
        if not fm:
            return False
        return bool(re.search(r"^%s:\s*true\s*$" % ONDUTY_KEY, fm.group(1), re.M))
    return False


def _state_path(sid):
    """注入器同源三段解析（DOENGLINGZ > WORKBUDDY > ~/.workbuddy）——⛔不另起根。"""
    return os.path.join(_cfg_root(), "doenglingz_inject_state.json")


def _append_row(sid, skill_name):
    from datetime import datetime
    row = {
        "session_id": sid,
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "d_tier": TIER,
        "mode": "skill_event",
        "src": os.environ.get("DOENGLINGZ_SRC") or "unknown",
        "w1": "skill_start:%s" % skill_name,
        "inject_len": 0,
        "inject_sha": "",
        "w3_layers": [],
        "slices_injected": 0,
        "slices_failed": 0,
    }
    p = _state_path(sid)
    try:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        return False
    return True


def _log(msg):
    # v2.0.1 端中立：日志路径 call-time 从 config 根派生（承 06 L1166 写读同根纪律·⛔写死单端）
    try:
        p = os.path.join(_cfg_root(), "logs", "skill_onduty_promote.log")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with io.open(p, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def main():
    if "--self-test" in sys.argv:
        return _self_test()
    obj = _payload_obj()
    if not isinstance(obj, dict):
        return 0
    return _run(obj)


def _self_test():
    """四例夹具（2026-10-10 焊入·承 01规范 §二·三十「新增判据入口须同轮入回归网」）
    用临时 config 根跑，⛔不碰真实台账；正例必升、三负例必不升。"""
    import tempfile
    d = tempfile.mkdtemp(prefix="onduty_selftest_")
    state = os.path.join(d, "doenglingz_inject_state.json")
    env_dir = os.environ.get("DOENGLINGZ_CONFIG_DIR")
    os.environ["DOENGLINGZ_CONFIG_DIR"] = d
    def fire(payload):
        return _run(payload)
    def nrows():
        if not os.path.exists(state):
            return 0
        return sum(1 for l in io.open(state, encoding="utf-8") if "selftest-sid" in l)
    ok = []
    n0 = nrows()
    fire({"sessionId": "selftest-sid", "toolName": "Skill", "input": {"skill": "growth-box"}})
    ok.append(("正例升档(声明件)", nrows() == n0 + 1))
    last = [l for l in io.open(state, encoding="utf-8") if "selftest-sid" in l][-1]
    ok.append(("行含D3与skill_start", '"d_tier": "D3"' in last and "skill_start:growth-box" in last))
    n1 = nrows()
    fire({"sessionId": "selftest-sid", "toolName": "Skill", "input": {"skill": "accessibility-review"}})
    ok.append(("负例·未声明Skill不升", nrows() == n1))
    fire({"sessionId": "selftest-sid", "toolName": "Bash", "input": {"command": "ls"}})
    ok.append(("负例·非Skill工具不升", nrows() == n1))
    fire({"toolName": "Skill", "input": {"skill": "growth-box"}})
    ok.append(("负例·无会话号不猜", nrows() == n1))
    if env_dir:
        os.environ["DOENGLINGZ_CONFIG_DIR"] = env_dir
    else:
        os.environ.pop("DOENGLINGZ_CONFIG_DIR", None)
    bad = [k for k, v in ok if not v]
    for k, v in ok:
        print("  %s %s" % ("✅" if v else "❌", k))
    print("self-test: %d/%d" % (len(ok) - len(bad), len(ok)))
    return 1 if bad else 0


def _run(obj):
    """主逻辑（与 stdin 解耦，供自测直调）。"""
    tool = _get(obj, "toolName", "tool_name")
    if tool != "Skill":
        return 0
    inp = obj.get("input") or obj.get("tool_input") or {}
    if not isinstance(inp, dict):
        return 0
    skill = inp.get("skill") or ""
    sid = _get(obj, "sessionId", "session_id")
    declared = _frontmatter_flag(skill)
    _log("%s | skill=%s | declared=%s | sid=%s" % (
        __import__("datetime").datetime.now().strftime("%F %T"), skill, declared,
        (sid[:18] if sid else "NONE")))
    if not declared or not sid:
        return 0
    if not _append_row(sid, skill):
        return 0
    tip = ("【Skill 上岗事件腿】本回合 Skill=%s 自声明 %s ⇒ 已升档 D3（写入注入器同一 state·"
           "Stop 侧 _expected_tier 取本会话最近行）。义务：首段档位改/认 D3，收口前 MUST 实跑 "
           "`tsl_verify.py --since <本回合起点> --full` 逐行 relay 至末段审计区（⛔手绘/⛔跨回合补）。"
           ) % (skill, ONDUTY_KEY)
    try:
        sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
        import hook_protocol as _hp
        _hp.emit(tip, payload=obj, argv=sys.argv[1:], event="PreToolUse", script="skill_onduty_tier_promote.py")
    except Exception:
        print(tip)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)      # 仪器故障不等于违规：静默放行不制造 launchd/hook 噪音
