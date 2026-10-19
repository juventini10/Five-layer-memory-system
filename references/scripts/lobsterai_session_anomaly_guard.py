#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
lobsterai_session_anomaly_guard.py — LobsterAI 专属守卫（会话层异常检测）

根因（2026-08-22 第一性原理定案）：
    LobsterAI 接入形态独有 3 个共享守卫管不到的静默失败窗口：
      ① before_prompt_build 注入（route_inject/kb_inject 插件）——OpenClaw 升级后插件加载失败
         / allow 被改 → 注入静默消失，无人知晓（08-12 假阴性疲劳同源病：机制失效无感知=最危险）
      ② patrol 增量状态机（audit_state_lobsterai.json {sessions:{path:count}}）——状态文件损坏/
         孤儿指针 → 全量重审或漏审
      ③ miss-feeder 清洗正则——system instructions 块格式随引擎升级变化 → 触发词污染路由判定
         （2026-08-13 AutoClaw 同源实证）
    对齐先例：DSH 端 dsh_session_anomaly_guard.py（专属守卫·transcript 转换+pre-step 注入验证）。

检查不变量（两级联判·防"无路由场景"误报）：
    ① 配置层（加载层快检）：openclaw.json plugins.allow 含 lobsterai-route-inject/kb-inject
       + 插件目录存在 —— 缺失=高置信失效
    ② 生效层（产物痕迹）：24h 内新会话 JSONL 中注入标记计数（标记常量运行时从
       route_inject_prompt.py【SSOT 格式契约】/ kb_inject_prompt.py【知识库激活】源码 grep 提取，
       ⛔ 不内联——改标记自动跟随，防守卫静默失效）
       —— 配置层坏 + 产物 0 = 告警（真失效）；配置层好 + 产物 0 = 提示（可能只是无路由场景）
    ③ 状态机健康：audit_state_lobsterai.json 可解析 + sessions 键路径存在（无孤儿指针）
    ④ 清洗污染：miss_candidates.txt 尾部样本无 [LobsterAI system instructions] 残留

退出码：0=正常/静默/无样本/任何异常（失败放行·Hook 纪律）；1=检出异常（stdout 告警）
部署：route_lobsterai_patrol.sh 循环外 run_guard_standalone 调用（不依赖 transcript 增量）
告警显形：异常 → 写 .patrol/lobsterai_anomaly_alert.txt + exit 1（patrol 日志留痕）
创建：2026-08-22
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
SESSIONS_DIR = HOME / "Library/Application Support/LobsterAI/openclaw/state/agents/main/sessions"
OPENCLAW_JSON = HOME / "Library/Application Support/LobsterAI/openclaw/state/openclaw.json"
EXT_DIR = HOME / "Library/Application Support/LobsterAI/third-party-extensions"
PATROL_DIR = HOME / "[记忆共享中心]/脚本中心/.patrol"
STATE_FILE = PATROL_DIR / "audit_state_lobsterai.json"
ALERT_FILE = PATROL_DIR / "lobsterai_anomaly_alert.txt"
ROUTE_INJECT_PY = HOME / "[记忆共享中心]/脚本中心/route_inject_prompt.py"
KB_INJECT_PY = HOME / "[记忆共享中心]/脚本中心/kb_inject_prompt.py"
MISS_CANDIDATES = HOME / "[记忆共享中心]/脚本中心/.guard/miss_candidates.txt"

PLUGINS = ["lobsterai-route-inject", "lobsterai-kb-inject"]
WINDOW_HOURS = 24
SYS_INSTR_MARK = "[LobsterAI system instructions]"


def read_inject_markers():
    """从注入脚本源码 grep 提取标记常量（真相源=脚本源码·⛔ 不内联）。"""
    markers = {}
    for key, path in (("route", ROUTE_INJECT_PY), ("kb", KB_INJECT_PY)):
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = re.search(r"【(SSOT 格式契约[^】]*|知识库激活[^】]*)", src)
        if m:
            markers[key] = m.group(0)
    return markers


def check_config_layer():
    """① 配置层：plugins.allow + 插件目录存在性。返回 (ok, problems)。"""
    problems = []
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text(encoding="utf-8"))
        allow = set(cfg.get("plugins", {}).get("allow", []))
        for name in PLUGINS:
            if name not in allow:
                problems.append(f"plugins.allow 缺失 {name}")
            if not (EXT_DIR / name).is_dir():
                problems.append(f"插件目录缺失 {EXT_DIR / name}")
    except Exception as e:
        problems.append(f"openclaw.json 读取失败: {e}")
    return (len(problems) == 0, problems)


def check_inject_evidence(markers):
    """② 生效层：24h 内新会话注入标记计数。返回 (has_evidence, total_sessions, found)。"""
    if not markers:
        return False, 0, 0
    cutoff = datetime.now() - timedelta(hours=WINDOW_HOURS)
    total = 0
    found = 0
    pats = [re.compile(re.escape(m)) for m in markers.values()]
    try:
        for f in SESSIONS_DIR.glob("*.jsonl"):
            try:
                if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                    continue
            except Exception:
                continue
            total += 1
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if any(p.search(text) for p in pats):
                found += 1
    except Exception:
        return False, total, found
    return (found > 0), total, found


def check_state_health():
    """③ 状态机健康：可解析 + 无孤儿指针。返回 (ok, problems)。"""
    problems = []
    if not STATE_FILE.exists():
        return True, problems  # 无状态文件=初始态，非异常
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        sessions = data.get("sessions", {})
        for path in sessions:
            if not Path(path).exists():
                problems.append(f"孤儿指针（会话已不存在）: {path}")
    except Exception as e:
        problems.append(f"状态文件损坏: {e}")
    return (len(problems) == 0, problems)


def check_clean_pollution():
    """④ 清洗污染：miss_candidates 尾部样本无 system instructions 残留。"""
    if not MISS_CANDIDATES.exists():
        return True, []
    try:
        lines = MISS_CANDIDATES.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = "\n".join(lines[-20:])
        if SYS_INSTR_MARK in tail or "[Current user request]" in tail:
            return False, ["miss_candidates 尾部样本含系统注入残留（清洗正则可能失效）"]
    except Exception:
        pass
    return True, []


def main():
    ap = argparse.ArgumentParser(description="LobsterAI 会话层异常检测（专属守卫）")
    ap.add_argument("--sessions-dir", type=str, default=None, help="会话目录覆盖（测试用）")
    ap.add_argument("--state", type=str, default=None, help="状态文件覆盖（测试用）")
    ap.add_argument("--miss-candidates", type=str, default=None, help="候选文件覆盖（测试用）")
    args = ap.parse_args()

    global SESSIONS_DIR, STATE_FILE, MISS_CANDIDATES
    if args.sessions_dir:
        SESSIONS_DIR = Path(args.sessions_dir)
    if args.state:
        STATE_FILE = Path(args.state)
    if args.miss_candidates:
        MISS_CANDIDATES = Path(args.miss_candidates)

    issues = []

    # ① 配置层
    cfg_ok, cfg_problems = check_config_layer()
    if not cfg_ok:
        issues.append("配置层异常: " + "; ".join(cfg_problems))

    # ② 生效层（两级联判）
    markers = read_inject_markers()
    has_evidence, total_sessions, found = check_inject_evidence(markers)
    if not cfg_ok and total_sessions > 0 and not has_evidence:
        issues.append(
            f"注入失效（高置信）: 配置层异常且 {total_sessions} 个新会话注入痕迹全 0"
        )
    elif cfg_ok and total_sessions > 0 and not has_evidence:
        issues.append(
            f"注入无痕迹（提示级·可能无路由场景或插件静默失效）: {total_sessions} 个新会话注入痕迹全 0"
        )

    # ③ 状态机健康
    state_ok, state_problems = check_state_health()
    if not state_ok:
        issues.append("状态机异常: " + "; ".join(state_problems))

    # ④ 清洗污染
    clean_ok, clean_problems = check_clean_pollution()
    if not clean_ok:
        issues.append("清洗污染: " + "; ".join(clean_problems))

    if issues:
        msg = "\n".join(f"  - {i}" for i in issues)
        print(f"lobsterai_session_anomaly_guard: 检出 {len(issues)} 项异常\n{msg}")
        try:
            ALERT_FILE.write_text(
                f"[{datetime.now().isoformat(timespec='seconds')}]\n{msg}\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # 失败放行（Hook 纪律：任何异常→exit 0，⛔ 不因守卫自身故障拦截/误报）
        sys.exit(0)
