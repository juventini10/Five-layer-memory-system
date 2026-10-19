#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""route_evolution_suggest.py v0.1 — 语义路由自进化·建议生成器（引擎类·stats）

控制论闭环定位：radar观测 → feedback留痕 → eval量化 → 建议生成 → 再观测。
本脚本做"建议生成"环：消费 semantic_radar.jsonl 命中数据 + 硬路由 Skill 清单，
产出"哪些 Skill 应补触发词"的排序建议 JSON（填值权归脚本·AI只回显）。

设计原则（跨工具中立·守 Hook 三纪律·失败放行）：
  - 仅读 .guard/semantic_radar.jsonl + route_audit.py EVIDENCE_WORDS，不改路由
  - 产出 route_evolution_suggest_<日期>.json 到系统日志目录
  - 任一数据源读不到 → 记 null（N/A 由脚本产出），不崩、不编造
  - 不自动改 router.py——建议交你确认后由 growth-box 蒸馏/手动改

跨工具中立（脚本哲学 §二·五）：本脚本是公共设施，住 [记忆共享中心]/脚本中心/，
各工具 hook 只调用不拥有。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import os
import sys
import json
import glob
from datetime import datetime
from collections import Counter

MC = os.path.expanduser("[记忆共享中心]")
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
GUARD = os.path.join(MC, "自定义层/待完成工作/路由家族/.guard")
RADAR = os.path.join(GUARD, "semantic_radar.jsonl")
ROUTE_AUDIT = os.path.join(MC, "开发工具/Skill路由引擎/scripts/route_audit.py")
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"[记忆共享中心]/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def load_hard_route_skills():
    """从 route_audit.py EVIDENCE_WORDS 机械提取硬路由覆盖 Skill（不内联真相）。"""
    try:
        txt = open(ROUTE_AUDIT, encoding="utf-8").read()
        import re
        m = re.search(r"EVIDENCE_WORDS\s*=\s*\{(.+?)\}", txt, re.S)
        if not m:
            return None
        words = eval("{" + m.group(1) + "}")
        return set(words.keys())
    except Exception:
        return None


def load_radar_hits(window_days=30):
    """读 semantic_radar.jsonl 近 N 天的命中（按 ts 字段判定）。"""
    try:
        if not os.path.isfile(RADAR):
            return None
        cutoff = datetime.now().timestamp() - window_days * 86400
        hits = []
        with open(RADAR, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    ts = datetime.fromisoformat(r["ts"]).timestamp()
                    if ts >= cutoff:
                        hits.append(r)
                except Exception:
                    continue
        return hits
    except Exception:
        return None


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    out = {
        "date": today,
        "source": "route_evolution_suggest.py v0.1",
        "window_days": 30,
        "reference_model": "硬路由 Skill 清单 (route_audit.py EVIDENCE_WORDS)",
        "suggestions": [],
        "stats": {},
    }

    hard_skills = load_hard_route_skills()
    hits = load_radar_hits()

    if hard_skills is None or hits is None:
        out["error"] = "数据源读取失败（route_audit.py 或 semantic_radar.jsonl 不可达）"
        # 仍写 JSON（留痕），exit 0 失败放行
    else:
        # 统计雷达命中但硬路由未覆盖的 Skill
        uncovered = Counter()
        for h in hits:
            skill = h.get("skill", "")
            if skill and skill not in hard_skills:
                uncovered[skill] += 1

        # 按命中次数降序 → 建议补触发词
        for skill, count in uncovered.most_common():
            out["suggestions"].append({
                "skill": skill,
                "radar_hits_30d": count,
                "action": "建议补触发词（待你确认）",
                "evidence": f"雷达近30天命中{count}条，但不在硬路由EVIDENCE_WORDS",
            })

        out["stats"] = {
            "total_radar_hits_30d": len(hits),
            "hard_route_skills": len(hard_skills),
            "uncovered_skills": len(uncovered),
            "uncovered_hits": sum(uncovered.values()),
        }

    # 写 JSON（失败放行）
    try:
        os.makedirs(SYSLOG, exist_ok=True)
        out_path = os.path.join(SYSLOG, f"route_evolution_suggest_{today}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[route_evolution_suggest] 已产出 {out_path}")
    except Exception as exc:
        try:
            with open(os.path.join(SYSLOG, "route_evolution_suggest_errors.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {exc!r}\n")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
