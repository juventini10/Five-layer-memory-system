#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""self_optimization_engine.py v0.2 — 自寻优引擎（真实闭环·跨工具中立）

控制论闭环定位：偏差信号 → 观测 → 方向性决策 → 配置覆盖层 → 观测比较 → 保留/回滚。

v0.2 根治（2026-08-24·据三明智L2评估·皮叔令"去完成工作·为愿景服务"）：
  - 废弃 random ε-greedy：决策改为观测驱动（读 route_evolution_suggest 的 uncovered_hits 真实信号）
  - 废弃直改 .py：改为写配置覆盖层（self_opt_overlay.json），route_semantic_radar 读它生效
  - 实装回滚：审计日志记录观测值与前后值，下一轮比较恶化>5%即回滚
  - 审计日志 = 闭环活着的唯一真相源（哲学状态判定权移交此文件）

设计原则（第一性原理 + 三层沙箱）：
  - Layer 1（自由层）：数值阈值 → 方向性试探 + 自动回滚（可逆·数据驱动·失败放行）
  - 单源禁令：沙箱 yaml 是"能改什么"唯一权威（本引擎只读不改）
  - 填值权归脚本：改参机械执行，AI 不编造
  - 跨工具中立：公共设施住 [记忆共享中心]/脚本中心/，各端 hook/调度器只调用不拥有
"""

import os
import sys
import json
import glob
from datetime import datetime

MC = os.path.expanduser("[记忆共享中心]")
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
DEV = os.path.join(MC, "开发工具")
RADAR_DIR = os.path.join(MC, "自定义层/待完成工作/路由家族")
GUARD_DIR = os.path.join(RADAR_DIR, ".guard")
SANDBOX = os.path.join(DEV, "self_optimization_sandbox.yaml")
AUDIT_LOG = os.path.join(SYSLOG, "self_optimization_audit.jsonl")
OVERLAY = os.path.join(GUARD_DIR, "self_opt_overlay.json")

# 行为旋钮：唯一有"真实信号→行为"链路的 Layer1 参数（其余为评估目标值，调它们=改目标冒充改进，禁用）
THRESHOLD_KEY = "route_semantic_radar.THRESHOLD"
THRESHOLD_DEFAULT = 0.03
THRESHOLD_RANGE = [0.01, 0.10]
THRESHOLD_STEP = 0.005
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_signal():
    """观测真实信号：route_evolution_suggest 的 uncovered_hits（覆盖不足=路由缺口）。"""
    files = sorted(glob.glob(os.path.join(SYSLOG, "route_evolution_suggest_*.json")))
    if not files:
        return None
    d = _read_json(files[-1])
    if not d:
        return None
    stats = d.get("stats", {})
    return {
        "date": d.get("date"),
        "uncovered_hits": stats.get("uncovered_hits", 0),
        "uncovered_skills": stats.get("uncovered_skills", 0),
        "total_radar_hits": stats.get("total_radar_hits_30d", 0),
    }


def get_current_threshold():
    """当前值：优先覆盖层，否则源码默认值。"""
    d = _read_json(OVERLAY)
    if d and THRESHOLD_KEY in d:
        try:
            return float(d[THRESHOLD_KEY])
        except Exception:
            pass
    return THRESHOLD_DEFAULT


def decide_direction(current, signal):
    """方向性决策（非随机）：uncovered_hits>0 → 降低阈值（更宽松→更多 Skill 进雷达路由→缩覆盖缺口）。

    下限熔断：当前值已 ≤ 下限 lo（或距下限不足一步）→ 不再降，避免一路退化到地板后停摆；
    上限守卫：绝不超出 [lo, hi]，保证语义安全。
    """
    if signal is None:
        return current, "无信号·不动"
    gap = signal.get("uncovered_hits", 0)
    lo, hi = THRESHOLD_RANGE
    if current > hi:  # 越界守卫：异常值钳回上限，避免雷达失效
        return round(hi, 6), f"当前{current}越上限→钳回{hi}"
    if current <= lo or (current - THRESHOLD_STEP) <= lo:
        return current, f"已贴近/达下限{lo}·不再降（缩缺口依赖 Layer2 采纳·不退化到地板）"
    if gap > 0:
        new = round(current - THRESHOLD_STEP, 6)
        reason = (f"观测 uncovered_hits={gap}>0（覆盖缺口）→ 降阈值至{new}"
                  f"（更宽松→更多 Skill 进雷达路由→缩缺口）")
        return new, reason
    return current, "无覆盖缺口·不动"


def write_overlay(new_val):
    """写配置覆盖层（不改 live .py）。返回旧值。"""
    old = get_current_threshold()
    os.makedirs(GUARD_DIR, exist_ok=True)
    d = _read_json(OVERLAY) or {}
    d[THRESHOLD_KEY] = new_val
    with open(OVERLAY, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return old


def log_audit(param, old, new, signal, reason, rolled_back=False):
    """写审计日志（追加 JSONL）——闭环活着的唯一真相源。"""
    os.makedirs(SYSLOG, exist_ok=True)
    rec = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "param": param,
        "old": old,
        "new": new,
        "reason": reason,
        "observation": signal,
        "rolled_back": rolled_back,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def last_applied_entry():
    """最近一次（未回滚的）应用记录。"""
    try:
        if not os.path.isfile(AUDIT_LOG):
            return None
        rows = []
        with open(AUDIT_LOG, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
        applied = [r for r in rows if not r.get("rolled_back")]
        return applied[-1] if applied else None
    except Exception:
        return None


def maybe_rollback(current_signal):
    """比较节点：当前覆盖缺口比上次应用时恶化>5% → 回滚到旧值（闭环的可逆性）。"""
    prev = last_applied_entry()
    if not prev or not current_signal:
        return None
    prev_gap = (prev.get("observation") or {}).get("uncovered_hits", 0)
    cur_gap = current_signal.get("uncovered_hits", 0)
    if prev_gap <= 0:
        return None
    if cur_gap > prev_gap * 1.05:  # 恶化>5%
        old = prev.get("old")
        if old is None:
            return None
        write_overlay(old)
        log_audit(THRESHOLD_KEY, get_current_threshold(), old, current_signal,
                  f"恶化回滚：上次应用后 uncovered_hits {prev_gap}→{cur_gap}(>{prev_gap*1.05:.0f})→恢复{old}",
                  rolled_back=True)
        return old
    return None


def main():
    signal = load_signal()
    # 比较节点优先：先看是否需回滚（闭环的可逆性保证）
    maybe_rollback(signal)
    current = get_current_threshold()  # 回滚可能已改变当前值，重读

    new_val, reason = decide_direction(current, signal)
    if abs(new_val - current) < 1e-9:
        print(f"[self_opt] 本轮不动：{reason}（current={current}·signal={signal}）")
    else:
        old = write_overlay(new_val)
        rec = log_audit(THRESHOLD_KEY, old, new_val, signal, reason)
        print(f"[self_opt] 方向性调参：{old}→{new_val}")
        print(f"[self_opt] 理由：{reason}")
        print(f"[self_opt] 审计已留痕：{AUDIT_LOG}")
        print(f"[self_opt] 覆盖层生效：{OVERLAY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
