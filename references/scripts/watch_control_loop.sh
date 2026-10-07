#!/bin/bash
# TRUTH_OF: 脚本中心/watch_control_loop.sh   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# watch_control_loop.sh — 控制论闭环看门狗（单一观察器·归 WorkBuddy 管）
# 愿景：全自动化·不依赖人记得。自动判定闭环是否真在跑，死了就告警。
# 判活逻辑：读 self_optimization_audit.jsonl 末条 ts；若距 now > 35min 且无当日 evolution_deviation 产出 → 写告警进系统日志。
set -u
# B修源·声明驱动口径v2(2026-10-05·条文47·第3支模板回读版·LRN-015纪律)：根唯一来源=声明；rc 判定非变量判定。
MC="$(python3 "$(dirname "$0")/runtime_paths.py" get archive_root 2>/dev/null)" \
  || { echo "❌ watch_control_loop: 读不到 runtime_paths 声明·作者机先跑 脚本中心/runtime_paths.py build / 端用户机跑安装器(条文47)" >&2; exit 1; }
SYSLOG="$MC/开发工具/logs/runtime"
AUDIT="$SYSLOG/self_optimization_audit.jsonl"
DEV="$MC/开发工具"
NOW_TS=$(date +%s)
ALIVE=1

# 判据1：审计日志末条不超过35分钟
if [ -f "$AUDIT" ]; then
  LAST=$(tail -1 "$AUDIT" 2>/dev/null | grep -o '"ts": "[0-9T:+-]*"' | head -1 | sed 's/.*"\(.*\)".*/\1/')
  if [ -n "$LAST" ]; then
    LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${LAST%??}" +%s 2>/dev/null || echo 0)
    if [ $((NOW_TS - LAST_TS)) -le 2100 ]; then ALIVE=0; fi
  fi
fi

# 判据2：当日 evolution_deviation 产出存在（闭环当轮实跑的标志）
TODAY=$(date +%Y-%m-%d)
if [ -f "$SYSLOG/evolution_deviation_$TODAY.json" ]; then ALIVE=0; fi

if [ "$ALIVE" -eq 0 ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') WATCH_OK 闭环存活"
  exit 0
fi

# 死了→写告警进系统日志（走 append_log_entry 若有，否则直写）
WARN="$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG告警] 控制论闭环超35分钟无活动·疑似停滞·请检查 cron(~/buluotuo_bin/run_control_loop.sh) 与 launchd 残留"
echo "$WARN" >> "$SYSLOG/control_loop_watchdog.log"
echo "$WARN"
exit 2
