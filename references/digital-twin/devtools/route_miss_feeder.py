#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_miss_feeder.py — miss 候选投喂器（UserPromptSubmit 钩子，实时）
语义路由质变方案 §任务 B 步骤 6（miss 候选投喂源·第一性原理最小管道）。

职责：每个用户提交 → 取任务文本 → 调 router.route() 判 zero-hit →
     零命中（miss）即 append 到 .guard/miss_candidates.txt（与雷达/采集器同构 append-only + 心跳）。

设计铁律（复用真源 + 跨工具中立）：
  - 单一真源：import router.route()（触发词从 SKILL.md desc 自动提取，与 route_inject_prompt.py 同一真源）。
  - 只接入不判定：本脚本仅"转发输入 + 零命中判定"，不承载路由决策（§〇 跨工具中立硬约束）。
  - append-only + 心跳：防静默失效（07-15 教训）。
  - 失败默认放行（exit 0）：绝不阻断对话（守卫编写规范原则1/2）。

输入：stdin JSON（UserPromptSubmit 钩子契约，含 "prompt" 字段）。
输出：.guard/miss_candidates.txt（append-only）+ .guard/feeder_last_run.ts（心跳）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, json, datetime

HOME = os.path.expanduser("~")
ROUTER_DIR = os.path.expanduser("[记忆共享中心]/脚本中心")
ROUTE_DIR = os.path.expanduser("[记忆共享中心]/脚本中心")
GUARD_DIR = os.path.join(ROUTE_DIR, ".guard")
CAND = os.path.join(GUARD_DIR, "miss_candidates.txt")
HEARTBEAT = os.path.join(GUARD_DIR, "feeder_last_run.ts")


def touch_heartbeat():
    os.makedirs(GUARD_DIR, exist_ok=True)
    with open(HEARTBEAT, "w") as f:
        f.write(datetime.datetime.now().isoformat(timespec="seconds"))


def append_candidate(task):
    """append-only + 去重：同文件内已有相同行则跳过（避免重复投喂）。"""
    os.makedirs(GUARD_DIR, exist_ok=True)
    existing = set()
    if os.path.exists(CAND):
        with open(CAND, encoding="utf-8") as f:
            existing = {l.strip() for l in f if l.strip()}
    if task in existing:
        return False
    with open(CAND, "a", encoding="utf-8") as f:
        f.write(task + "\n")
    return True


def feed(prompt):
    """投喂入口：心跳 + 零命中判定 + append（stdin 与 --prompt 共用同一实现）"""
    touch_heartbeat()  # 心跳：证明钩子确实触发（无论命中与否，防静默失效）
    if not prompt:
        return
    # 单一真源：router.route()（空列表 = zero-hit = miss）
    try:
        sys.path.insert(0, ROUTER_DIR)
        from router import route
        matched = route(prompt)
    except Exception:
        return  # 失败默认放行，绝不阻断对话
    if matched:
        return  # 有命中 → 非 miss，不投喂
    # 零命中 → miss 候选
    added = append_candidate(prompt)
    if added:
        print(f"[feeder] miss 候选已投喂: {prompt[:40]}…")


def main():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        prompt = json.loads(raw).get("prompt", "")
    except Exception:
        return
    feed(prompt)


if __name__ == "__main__":
    # --prompt 模式：argv 传参（hook stdin input 传递不可靠·2026-08-13 实证：心跳更新但投喂缺失）
    if len(sys.argv) > 2 and sys.argv[1] == "--prompt":
        feed(sys.argv[2])
    else:
        main()
    sys.exit(0)
