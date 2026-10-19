#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.2
"""
rule_fragment_inject.py — UserPromptSubmit 钩子：规则「加载时机」命中即硬注入对应铁律段

设计定位（Solution A·2026-09-01）：
- 把三层渐进加载中「按需 Read 细则」那一下，从【纪律驱动+告警网】(rule_three_layer_guard ④⑤
  warn-only) 升级为【pre-response 硬墙】：用户输入命中某铁律「加载时机」→ 在 AI 回答前自动把
  该铁律段注入上下文，AI 不再需要"记得去 Read"。
- 对齐愿景四方向①「全自动化·不靠人记得」：机制代意志，杜绝文档与实盘脱钩。
- 仅注入【命中片段】(不注全文件、不注 resident 的 008/009)，保持渐进式披露的"只给相关"语义。

机制要点：
- 触发规格单一真源：记忆规则/rule_triggers.yaml（由 铁律版 加载时机索引表 派生）。
- 匹配：对每个非 resident 触发，re.search 任一 match 正则于 prompt → 命中。
- 注入内容：铁律版中对应 `### 铁律-0NN` 小节正文（动作化 DO/NOT + 口诀），非全文件。
- 端感知输出（复用 route_inject_prompt._emit 协议）：ZCode 端输出 hookSpecificOutput JSON，
  WB/其他端输出纯文本（挂载实证 2026-08-24 同形态）。
- 失败默认放行（exit 0），绝不阻断对话（守卫编写规范原则1/2）。
- 覆盖守卫：--coverage 模式校验 yaml 覆盖 19 条且与铁律版索引表对齐（供 rule_three_layer_guard ⑥
  与回归复用）；本钩子运行时不阻断，仅 --coverage 显式报告。

挂载：settings.json hooks.UserPromptSubmit 新增本脚本。与 rule_inject_prompt(技能路由) 并列，
两挂点各管一域（Skill vs 规则），不互相改。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import sys
import os
import re
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rule_triggers_loader import load_triggers, extract_tielu_section, extract_tielu_index_ids

HOME = os.path.expanduser("~")
RULES_DIR = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆规则")
TIELU_FILE = os.path.join(RULES_DIR, "用户基本规则-铁律版.md")
TRIGGERS_YAML = os.path.join(RULES_DIR, "rule_triggers.yaml")
STATE_PATH = "/tmp/rule_fragment_state.json"
MAX_INJECT = 3  # 单消息最多注入条数，超过取前 N 并标歧义，防上下文爆

# ---- 冲突/边缘场景 → 详解版 预注入（Q2②·2026-09-01）----
# 与 rule_three_layer_guard ⑤（Stop 事后 warn-only 查"末条回复处冲突须带详解锚点"）同族，
# 但本段把该域升级为 pre-response 硬墙：用户输入命中冲突/边缘信号即预注入"须 Read 详解存档版"
# 指令，把"该读详解版没读"从告警转为已注入（检测→预防，对齐 Solution A 质变）。
# 不入 rule_triggers.yaml 的 triggers 列表（那是 19 条铁律·受 ⑥覆盖守卫约束）；此处是独立
# 信号类·独立真源=rule_conflict_signals.yaml（2026-09-16 迁入治理·B闸）。语义与 ⑤ 互补：⑤查助手末条（事后·实测工作 2026-09-16），本段查用户输入（事前）。
CONFLICT_PATTERNS_DEFAULT = [
    "规则冲突|冲突.*规则|这两条规则|规则.*矛盾|规则打架|规则.*抵触",
    "改.*规则|修改.*这条规则|这条规则.*改|调整.*规则|规则.*能不能改|规则.*如何改",
    "边缘情况|边缘场景|边界情况|边界场景|特殊情况|异常情形",
    "为什么.*规则|规则.*为什么|规则.*依据|规则.*这样定|规则.* rationale",
    "成长箱.*晋升|晋升.*复查|晋升复查|晋升.*评估",
]

def _load_conflict_patterns():
    """优先 rule_conflict_signals.yaml（治理真源·B闸），缺失/失败 fallback 内置默认组（v0.2）。"""
    try:
        from rule_triggers_loader import load_conflict_signals
        sigs = load_conflict_signals()
        pats = []
        for sig in sigs or []:
            pats.extend(sig.get("match", []) or [])
        if pats:
            return pats, "yaml(%d组)" % len(sigs)
    except Exception:
        pass
    return CONFLICT_PATTERNS_DEFAULT, "builtin-fallback"


CONFLICT_PATTERNS, _CONFLICT_PATTERNS_SRC = _load_conflict_patterns()
CONFLICT_INJECT_TEXT = (
    "【铁律自动预注入·冲突/边缘场景】检测到规则冲突/边缘场景信号 → 按铁律版规定，"
    "处理前必须 Read 用户基本规则-详解存档版 对应铁律章节"
    "（仅看铁律版摘要不足以覆盖冲突/边缘细节，避免凭记忆踩坑）。"
)


# ── 输出协议单一真源（2026-09-04 根治·同 route_inject/kb_inject 口径）──
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

_PAYLOAD = {}

def _hp_mode(ctx, decision):
    """协议委托 hook_protocol 单一真源（2026-09-04 根治·消除第 5 份复制实现）。"""
    if _hp is not None:
        mode = _hp.emit(ctx, payload=_PAYLOAD, argv=sys.argv[1:],
                        event="UserPromptSubmit", script=os.path.basename(__file__))
        decision["emit"] = "%s-via-hook_protocol" % mode
        return mode
    decision["emit"] = "text-fallback-no-module"
    sys.stdout.write(ctx)
    return "text"


def _emit(ctx: str, decision: dict) -> None:
    """输出：形态由 hook_protocol 判定（json/text），本脚本只组装文本。"""
    _hp_mode(ctx, decision)
    try:
        with open(STATE_PATH, "a") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _match_triggers(prompt, triggers):
    """返回命中(非resident)的触发列表。"""
    hit = []
    for t in triggers:
        if t.get("resident"):
            continue
        pats = t.get("match") or []
        for p in pats:
            try:
                if re.search(p, prompt):
                    hit.append(t)
                    break
            except re.error:
                continue
    return hit


def _match_conflict(prompt):
    """冲突/边缘场景信号（用户输入侧·Q2② pre-response 硬墙）。命中即须注入详解版指令。"""
    for p in CONFLICT_PATTERNS:
        try:
            if re.search(p, prompt):
                return True
        except re.error:
            continue
    return False


def _build_ctx(hit):
    parts = []
    shown = hit[:MAX_INJECT]
    for t in shown:
        anchor = t.get("source_anchor", "")
        try:
            sec = extract_tielu_section(_read_tielu(), anchor)
        except Exception:
            sec = None
        body = sec if sec else f"（⚠️ 未能从铁律版提取 {anchor} 小节）"
        # 提取段已含 "### 铁律-0NN：名称" 标题，不再预加，避免重复
        parts.append(body)
    header = ("【铁律自动预注入·触发命中】以下铁律因当前输入命中其「加载时机」被自动注入"
              "（替代原\"AI自觉Read\"步骤，成为硬墙，无需再手动 Read）：\n")
    ctx = header + "\n".join(parts)
    if len(hit) > MAX_INJECT:
        ctx += (f"\n\n⚠️ 本消息命中 {len(hit)} 条，仅注入前 {MAX_INJECT} 条；"
                f"其余按铁律版索引表自行 Read 细则。")
    return ctx


_tielu_cache = None


def _read_tielu():
    global _tielu_cache
    if _tielu_cache is None:
        with open(TIELU_FILE, encoding="utf-8") as f:
            _tielu_cache = f.read()
    return _tielu_cache


def _inject(prompt):
    if not prompt:
        return
    try:
        triggers = load_triggers()
    except Exception:
        return
    hit = _match_triggers(prompt, triggers)
    conflict_hit = _match_conflict(prompt)
    decision = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "prompt": prompt,
        "hit_ids": [t.get("id") for t in hit],
        "inject_count": min(len(hit), MAX_INJECT),
        "conflict": conflict_hit,
    }
    if not hit and not conflict_hit:
        decision["action"] = "no-match-skip"
        _emit("", decision) if False else _record(decision)
        return
    ctx = _build_ctx(hit)
    if conflict_hit:
        ctx += "\n\n" + CONFLICT_INJECT_TEXT
    decision["action"] = "inject"
    _emit(ctx, decision)


def _record(decision):
    try:
        with open(STATE_PATH, "a") as f:
            f.write(json.dumps(decision, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _coverage():
    """覆盖守卫：yaml 19 条 == 铁律版索引表 19 条 + anchor 存在 + resident/match 一致。"""
    out = {"ok": True, "issues": []}
    try:
        triggers = load_triggers()
    except Exception as e:
        return {"ok": False, "issues": [f"解析 rule_triggers.yaml 失败: {e}"]}
    yaml_ids = sorted(t.get("id") for t in triggers)
    try:
        tielu_text = _read_tielu()
    except Exception as e:
        return {"ok": False, "issues": [f"读取铁律版失败: {e}"]}
    idx_ids = extract_tielu_index_ids(tielu_text)
    if yaml_ids != idx_ids:
        out["ok"] = False
        out["issues"].append(f"id 集合漂移: yaml={yaml_ids} 铁律版索引={idx_ids}")
    for t in triggers:
        i = t.get("id")
        if not t.get("resident"):
            if not (t.get("match")):
                out["ok"] = False
                out["issues"].append(f"非 resident 触发 {i} 缺 match 正则")
            anc = t.get("source_anchor")
            if anc and anc not in tielu_text:
                out["ok"] = False
                out["issues"].append(f"触发 {i} 的 anchor 不在铁律版: {anc}")
        else:
            if t.get("match"):
                out["ok"] = False
                out["issues"].append(f"resident 触发 {i} 不应有 match: {t.get('match')}")
    return out


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        r = _coverage()
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)  # 步2(2026-10-07):注入失败=检红语义→rc归0(失败详情已在上方输出/台账;exit≠0专留真崩·报警噪声根治卡)
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        return
    # --prompt 模式：argv 传参（hook stdin 不可靠，与 route_inject_prompt 同构）
    if len(sys.argv) > 2 and sys.argv[1] == "--prompt":
        _inject(sys.argv[2])
        return
    raw = ""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
    except Exception:
        raw = ""
    try:
        _parsed = json.loads(raw) if raw else {}
        if isinstance(_parsed, dict):
            globals()["_PAYLOAD"] = _parsed
        prompt = _parsed.get("prompt", "") if isinstance(_parsed, dict) else ""
    except Exception:
        prompt = ""
    _inject(prompt)


def _selfcheck():
    print("=== rule_fragment_inject.py 自检 ===")
    import glob
    reg = False
    try:
        d = json.load(open(os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "settings.json")))
        for evt, entries in d.get("hooks", {}).items():
            for e in entries:
                for h in e.get("hooks", []):
                    if "rule_fragment_inject" in h.get("command", ""):
                        reg = True
                        print(f"  [注册] hooks.{evt} -> {h['command']}")
    except Exception as e:
        print(f"  [注册] 读 settings.json 失败: {e}")
    if not reg:
        print("  [注册] ⚠️ 未在 hooks 中找到本脚本")
    cov = _coverage()
    print(f"  [覆盖守卫] {'✅' if cov['ok'] else '⚠️'} {cov['issues'] or '19条对齐'}")
    traces = sorted(glob.glob("/tmp/rule_fragment_state.json"), key=os.path.getmtime, reverse=True)[:1]
    print(f"  [决策留痕] {'有' if traces else '无'} /tmp/rule_fragment_state.json")
    print("=== 自检结束 ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
