#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_evolve_feed.py v0.1 — 路由自进化·执行漏判信号腿（与 route_evolution_suggest 雷达覆盖腿互补）
定位：消费 route_audit.jsonl 的 potential_miss（硬路由触发但 Skill 未执行的执行纪律缺口），
     是 route_evolution_suggest.py 雷达覆盖缺口（补触发词）之外的另一信号轴，不重复。
源：记忆蓝图 知识库设计哲学/02-实例/路由设计哲学 v1.0 自进化（miss→学→不再miss）
    01-知识库设计通用规范 v1.3 原则7（反馈闭环+评测集同步）

职责（最小不可约）：
  读 route_audit.jsonl 的 potential_miss（已清洗）→ 按 skill 聚类 →
  产 route_evolve_backlog.jsonl（学习 backlog：计数+触发词+样本任务+建议）。
  ⚠️ 仅产出"建议"，不直接改路由（AI 无权自改路由，对齐原则8 信任分层）。
  ⚠️ v0.1 仅数据准备，不声称"已自进化"（闭环未闭合）。

用法：
  python3 route_evolve_feed.py            # 生成 backlog
  python3 route_evolve_feed.py --stats    # 仅打印统计
  python3 route_evolve_feed.py --out X.jsonl
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
import argparse
from collections import defaultdict

# 与 route_audit.py 同默认日志路径（单一真源）
DEFAULT_LOG = os.path.expanduser(
    os.environ.get("ROUTE_AUDIT_LOG",
    os.path.expanduser("[记忆共享中心]/脚本中心/logs/route_audit.jsonl")))
DEFAULT_OUT = os.path.expanduser("[记忆共享中心]/脚本中心/.snapshots/route_evolve_backlog.jsonl")


def read_rows(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def build_backlog(rows):
    """按 skill 聚合并生成学习 backlog（幂等：同输入同输出）"""
    agg = defaultdict(lambda: {"miss_count": 0, "triggers": set(),
                               "samples": [], "tasks_seen": set()})
    for r in rows:
        if r.get("potential_miss") is not True:
            continue
        skills = r.get("skills", []) or []
        trig = r.get("triggers", {}) or {}
        task = (r.get("task") or "")[:120]
        tkey = task[:40]
        for s in skills:
            a = agg[s]
            a["miss_count"] += 1
            for w in (trig.get(s, []) if isinstance(trig, dict) else []):
                if w:
                    a["triggers"].add(w)
            if tkey and tkey not in a["tasks_seen"]:
                a["tasks_seen"].add(tkey)
                if len(a["samples"]) < 5:
                    a["samples"].append(task)
    # 转成有序列表
    out = []
    for s in sorted(agg, key=lambda k: -agg[k]["miss_count"]):
        a = agg[s]
        out.append({
            "skill": s,
            "miss_count": a["miss_count"],
            "triggers": sorted(a["triggers"]),
            "sample_tasks": a["samples"],
            "suggested_action": (
                f"复盘：触发词 {sorted(a['triggers'])[:3]} 出现时确保 {s} 被调用；"
                "人工确认后走路由/证据词更新（AI 不直接改）"),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=DEFAULT_LOG)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    rows = read_rows(os.path.expanduser(args.log))
    backlog = build_backlog(rows)

    if args.stats:
        print(f"审计日志: {args.log}")
        print(f"potential_miss 总条数: {sum(1 for r in rows if r.get('potential_miss') is True)}")
        print(f"聚类 skill 数: {len(backlog)}")
        for b in backlog:
            print(f"  {b['skill']}: {b['miss_count']} 次 | 触发词 {b['triggers'][:3]}")
        return 0

    os.makedirs(os.path.dirname(os.path.expanduser(args.out)), exist_ok=True)
    with open(os.path.expanduser(args.out), "w", encoding="utf-8") as f:
        for b in backlog:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    print(f"backlog 已生成: {args.out}（{len(backlog)} 个 skill 聚类）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
