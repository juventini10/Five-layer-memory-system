#!/bin/bash
# TRUTH_OF: 脚本中心/run_control_loop.sh   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# run_control_loop.sh — 控制论闭环统一入口（跨工具中立·各端调度器只调用不拥有）
# 愿景：全自动化·自主进化。各端（WorkBuddy/Qoder CN/AutoClaw/DSH/Hermes…）统一经此入口跑闭环，不 fork。
# 顺序：误差量化 → 路由进化建议 → 自寻优（观测→方向决策→配置覆盖层→比较→回滚）
set -u
# B修源·声明驱动口径v2(2026-10-05·条文47·L2键20261005_194734下沉轮)：
# 根唯一来源=runtime_paths 声明(同目录解析器取，解析器已 realpath 下沉=软链/实体入口均可达)；
# ⛔消费侧默认兜底已删，无声明 hard fail+指引即教育。
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
SELF="$(python3 -c "import os,sys;print(os.path.realpath(sys.argv[1]))" "$SELF")"  # realpath 下沉（2026-10-16 拆链批：注释已承诺·实现补上）
MC="$(python3 "$(dirname "$SELF")/../runtime_paths.py" get archive_root 2>/dev/null)" \
  || { echo "❌ run_control_loop: 读不到 runtime_paths 声明·作者机先跑 脚本中心/runtime_paths.py build / 端用户机跑安装器(条文47)" >&2; exit 1; }
DEV="$MC/脚本中心"
LOG="$MC/脚本中心/logs/runtime/control_loop.log"
PY=/usr/bin/python3
echo "=== control-loop $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
"$PY" "$DEV/evolution_deviation.py" >> "$LOG" 2>&1
"$PY" "$DEV/route_evolution_suggest.py" >> "$LOG" 2>&1
"$PY" "$DEV/self_optimization_engine.py" >> "$LOG" 2>&1
echo "=== done ===" >> "$LOG"
