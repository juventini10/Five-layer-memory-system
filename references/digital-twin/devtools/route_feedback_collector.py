#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_feedback_collector.py — 行为信号采集器（与 embedding 无关）
语义路由质变方案 §任务 B 步骤 4。

职责：记录 miss 后用户行为（retry 重试 / abandon 放弃 / rephrase 换说法 / hit 命中）
→ feedback_events.jsonl，为 Phase 3b 自进化（MAB reward 启发式）提供 30 天信号轨。

设计铁律：
  - append-only 输出 + 心跳文件（07-15 教训：防静默失效）。
  - 只采集行为信号，不参与语义匹配（匹配在 radar / search_kb 侧）。

用法：
  python3 route_feedback_collector.py --task "帮我写篇稿" --behavior abandon
  python3 route_feedback_collector.py --task "..." --behavior retry --skill scriyore
  python3 route_feedback_collector.py --task "..." --behavior rephrase
  python3 route_feedback_collector.py --selfcheck

输出：.guard/feedback_events.jsonl（append-only）+ .guard/collector_last_run.ts（心跳）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, json, argparse, datetime

HOME = os.path.expanduser("~")
GUARD_DIR = os.path.join(HOME, os.path.expanduser("[记忆共享中心]/脚本中心"), ".guard")
FEEDBACK_OUT = os.path.join(GUARD_DIR, "feedback_events.jsonl")
HEARTBEAT = os.path.join(GUARD_DIR, "collector_last_run.ts")
VALID = {"retry", "abandon", "rephrase", "hit"}


def emit(task, behavior, skill=None, note=None):
    rec = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "task": task,
        "behavior": behavior,
        "skill": skill,
        "note": note,
    }
    os.makedirs(GUARD_DIR, exist_ok=True)
    with open(FEEDBACK_OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # 心跳：正常记录路径也要写（2026-08-29 修·PAT-033 第4例）
    # 原实现只在 --selfcheck 分支写心跳，正常路径不留痕 → 台账在更新、
    # 心跳却停在 2026-08-12（17 天）→ 三层健康度的"存活"判据失效。
    with open(HEARTBEAT, "w") as f:
        f.write(datetime.datetime.now().isoformat(timespec="seconds"))
    return rec


def selfcheck():
    os.makedirs(GUARD_DIR, exist_ok=True)
    with open(HEARTBEAT, "w") as f:
        f.write(datetime.datetime.now().isoformat(timespec="seconds"))
    print(f"[selfcheck] feedback_out 可写={'OK' if os.access(GUARD_DIR, os.W_OK) else 'NO'} "
          f"valid_behaviors={sorted(VALID)} heartbeat=written")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task")
    ap.add_argument("--behavior", choices=sorted(VALID))
    ap.add_argument("--skill")
    ap.add_argument("--note")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        return selfcheck()
    if not a.task or not a.behavior:
        print("需 --task + --behavior（或 --selfcheck）")
        return 1
    rec = emit(a.task, a.behavior, a.skill, a.note)
    print(f"[feedback] 记录: {rec['task'][:30]}… → {a.behavior}"
          + (f" ({a.skill})" if a.skill else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
