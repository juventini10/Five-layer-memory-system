#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/tsl_echo_hook.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
# version: v1.1 → v1.2
"""
tsl_echo_hook.py — TSL 树回显钩子（UserPromptSubmit·v1.1）
LRN-20260929-01 根治·闭环末环：
  Stop 钩子 tsl_tree_hook 机械产树至 ~/.workbuddy/tsl_last_tree.md
  → 本钩子（UserPromptSubmit）读树·未消费则 additionalContext 注入 → AI 被迫逐行 relay
  → 写 .consumed 标记（同 stamp 只注入一次）
产出（Stop）与呈现（UserPromptSubmit）均不经 AI 意志。

## v1.2 病根（2026-10-07·你「上岗回复老不按模板」根治·WB 端）

引擎源码实证（`app.asar.unpacked/cli/dist/codebuddy-lite-wb.mjs`）：
- `aggregateSettledResults`：`hookSpecificOutput = {...旧, ...新}` → **同 key 覆盖**
- `aggregateSettledResults`：`stdout = 旧 + "\n" + 新` → **拼接共存**
- UPS 消费：有 additionalContext → 覆盖赋值；否则走 stdout 拼接

⇒ **json envelope = 竞争（last wins）；裸文本 = 共存**。
WB 端 UPS 实挂 11 条钩子，多条同发 envelope ⇒ 排前面的注入块**结构性必被覆盖**（童灵块排第 4）。

旧形态另有一层污染：空闲时 `_emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）` 产出 `{}` → 引擎按 stdout 拼接时
**把字面量 `{}` 塞进模型上下文**（每轮一枚·非空上下文噪声）。

v1.2 修法：①输出形态委托 `hook_protocol` 单一真源（WB=text 裸文本）；
②空闲时**零输出**（⛔ 不再吐 `{}`），符合 `emit()` 空 ctx 只留痕不输出的既有语义。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, re, sys, json

# 输出协议单一真源（2026-10-07·与注入钩子家族同源·WB 端必须 text）
_p = os.path.dirname(os.path.abspath(__file__))
if _p not in sys.path:
    sys.path.insert(0, _p)
try:
    import hook_protocol as _hp
except Exception:
    _hp = None


def _emit(ctx):
    """输出协议委托 hook_protocol 单一真源；空闲（空 ctx）零输出。"""
    if not ctx:
        return
    if _hp is not None:
        try:
            _hp.emit(ctx, payload={"hook_event_name": "UserPromptSubmit"},
                     argv=sys.argv[1:], event="UserPromptSubmit",
                     script="tsl_echo_hook.py")
            return
        except Exception:
            pass
    sys.stdout.write(ctx)


# v1.1（2026-09-30 by ZCode·与 tsl_tree_hook v1.2 同轮配对）：跨端适配三改——
#   ① TREE env 化（TSL_TREE_OUT·与 tree_hook 同名 env·ZCode 独立树槽·默认不变=WB 零回归）
#   ② 门控 session_d_tier：stdin UPS payload 的 session_id 过滤台账本会话最新行
#      （根除「全局最新行」跨端/跨会话串台·无 session_id 退全局=向后兼容）
#   ③ 树头 session 比对：树头带 session 且 ≠ 本会话 → 不回显（旧格式树头无 session=跳过比对·兼容）
TREE = os.environ.get("TSL_TREE_OUT") or os.path.join(os.path.expanduser("~"), ".workbuddy", "tsl_last_tree.md")
DONE = TREE + ".consumed"
STATE = os.environ.get("TSL_INJECT_STATE") or os.path.join(os.path.expanduser("~"), ".workbuddy", "doenglingz_inject_state.json")  # env=测试隔离缝（同 tsl_tree_hook v1.2）

def _stdin_session_id():
    try:
        d = json.loads(sys.stdin.read() or "{}")
        return d.get("session_id", "") if isinstance(d, dict) else ""
    except Exception:
        return ""

def session_d_tier(sid):
    """本会话最新档位——TSL 呈现义务仅 D3（08 §七·06 v1.89 档位门控）。
    sid 为空 → 退全局最新行（旧宿主兼容）；本会话无注入行 → 判非 D3（⛔不退全局·那正是串台源）。"""
    try:
        with open(STATE, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        for line in reversed(lines):
            d = json.loads(line)
            if sid and d.get("session_id") and d.get("session_id") != sid:
                continue
            if d.get("d_tier"):
                return d.get("d_tier")
        if sid:
            return ""
        for line in reversed(lines):
            d = json.loads(line)
            if d.get("d_tier"):
                return d.get("d_tier")
    except Exception:
        pass
    return ""

def main():
    sid = _stdin_session_id()
    if session_d_tier(sid) != "D3":
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）  # ⛔档位门控：仅 D3 回合注入 TSL 树
        return
    if not os.path.exists(TREE):
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）
        return
    try:
        tree = open(TREE, encoding="utf-8").read()
    except Exception:
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）
        return
    m = re.search(r"stamp=(\w+)", tree)
    stamp = m.group(1) if m else ""
    if not stamp:
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）
        return
    consumed = ""
    if os.path.exists(DONE):
        try:
            consumed = open(DONE, encoding="utf-8").read().strip()
        except Exception:
            consumed = ""
    ms = re.search(r"session=([\w\-]+)", tree)
    tree_sid = ms.group(1) if ms else ""
    if tree_sid and tree_sid != "legacy" and sid and tree_sid != sid:
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）  # v1.1：树是别的会话产的（跨端/跨会话）→ 本会话不回显
        return
    if stamp == consumed:
        _emit("")   # v1.2：空闲零输出（⛔ 不再吐 `{}` 污染上下文）  # 已回显过·不重复灌
        return
    with open(DONE, "w", encoding="utf-8") as f:
        f.write(stamp)
    ctx = ("【TSL 上回合核验树·Stop 钩子机械产出·⛔必须在回复中逐行 relay 后方可视为已呈报·AI 无省略权】\n"
           + tree)
    _emit(ctx)

if __name__ == "__main__":
    main()
