#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""环节维护台账.py v1.0 — 环节维护成本信息源（git log 派生·免人工·免自评）

你的挑战（愿景仪表盘 §10.5）：独立台账谁做？跨天跨月怎么统计？
答案：不建人工台账（自评不可信·C-040），用 git log 事件流——
每次 commit 改某环节 = 一条维护事件（时间戳/文件自动留痕）。
维护成本 = 每环节 git 提交数/周（自动·跨天跨月天然支持 --since）。

环节清单（§10.5 参考口径·≈30 环节归 8 类）：
  守卫治理 / 路由 / 知识注入 / 面板 / 数字分身 / 日志 / 知识库 / 其他

输出：[记忆共享中心]/脚本中心/logs/runtime/环节维护台账_<日期>.json（供 panel_snapshot 消费）
v1.1 2026-09-02：从系统日志目录迁出，根治运行时日志污染系统日志目录。

设计原则（守卫三纪律）：git 读不到 → 产空 JSON + 记错误日志 + exit 0（不卡主流程）。
"""

import os
import sys
import json
import subprocess
from datetime import datetime

MC = os.path.expanduser("[记忆共享中心]")
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
WINDOW_DAYS = 7

# 环节 → 路径关键词（按序优先匹配：一个文件只归一个环节）
SEGMENT_RULES = [
    ("守卫治理", ["guard", "守卫", "platform_adaptation", "consistency",
                 "self_improvement", "self_optimization"]),
    ("路由", ["路由", "route_"]),
    ("知识注入", ["知识联邦", "知识注入", "kb_", "知识库设计哲学"]),
    ("面板", ["panel", "可视化呈现"]),
    ("技能配置", ["技能配置"]),
    ("数字分身", ["数字分身"]),
    ("日志", ["工作日志", "系统日志", "变更日志"]),
    ("记忆蓝图", ["记忆蓝图"]),
    ("知识库", ["知识库", "知识体系", "AI学习库"]),
]


def classify(path):
    for seg, kws in SEGMENT_RULES:
        for kw in kws:
            if kw in path:
                return seg
    return "其他"


def collect(window_days=WINDOW_DAYS):
    r = subprocess.run(
        ["git", "-C", MC, "-c", "core.quotepath=false", "log",
         "--since={} days".format(window_days),
         "--name-only", "--pretty=format:@@%ad", "--date=short"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError("git log 失败: {}".format(r.stderr.strip()[:200]))

    seg_stats = {seg: {"commits": 0, "files": 0,
                       "first": None, "last": None}
                 for seg, _ in SEGMENT_RULES}
    seg_stats["其他"] = {"commits": 0, "files": 0, "first": None, "last": None}
    total_commits = 0
    cur_date = None
    cur_segs = set()
    for line in r.stdout.splitlines():
        if line.startswith("@@"):
            # 落账上一个 commit
            if cur_date is not None:
                total_commits += 1
                for s in cur_segs:
                    st = seg_stats[s]
                    st["commits"] += 1
                    if st["first"] is None or cur_date < st["first"]:
                        st["first"] = cur_date
                    if st["last"] is None or cur_date > st["last"]:
                        st["last"] = cur_date
            cur_date = line[2:]
            cur_segs = set()
        elif line.strip() and cur_date is not None:
            s = classify(line.strip())
            cur_segs.add(s)
            seg_stats[s]["files"] += 1
    if cur_date is not None:
        total_commits += 1
        for s in cur_segs:
            st = seg_stats[s]
            st["commits"] += 1
            if st["first"] is None or cur_date < st["first"]:
                st["first"] = cur_date
            if st["last"] is None or cur_date > st["last"]:
                st["last"] = cur_date
    return total_commits, seg_stats


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    out = {
        "date": today,
        "source": "环节维护台账.py v1.0",
        "window_days": WINDOW_DAYS,
        "metric": "维护成本=每环节 git 提交数/周（git log 事件流·免人工免自评·§10.5）",
    }
    try:
        total, seg_stats = collect()
        out["total_commits"] = total
        segs = []
        for name, _ in SEGMENT_RULES + [("其他", None)]:
            st = seg_stats[name]
            segs.append({
                "segment": name,
                "commits_7d": st["commits"],
                "files_touched": st["files"],
                "first_commit": st["first"],
                "last_commit": st["last"],
            })
        segs.sort(key=lambda x: -x["commits_7d"])
        out["segments"] = segs
    except Exception as exc:
        out["total_commits"] = None
        out["segments"] = []
        out["error"] = repr(exc)
        try:
            with open(os.path.join(SYSLOG, "环节维护台账_errors.log"), "a", encoding="utf-8") as f:
                f.write("{} {}\n".format(datetime.now().isoformat(), exc))
        except Exception:
            pass

    try:
        os.makedirs(SYSLOG, exist_ok=True)
        out_path = os.path.join(SYSLOG, "环节维护台账_{}.json".format(today))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("[环节维护台账] 已产出 {} (总提交 {})".format(out_path, out.get("total_commits")))
    except Exception as exc:
        print("[环节维护台账] 写出失败: {}".format(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
