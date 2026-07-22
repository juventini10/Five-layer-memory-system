#!/bin/bash
# amber-fswatch-wrapper.sh — 记忆琥珀监听（macOS · 加固版，Intel + Apple Silicon 通用）
# ─────────────────────────────────────────────────────────────
# 修复真机问题：
#   ① fswatch 路径硬编码 /usr/local/bin/fswatch → Apple Silicon 在 /opt/homebrew/bin 失效
#      对策：command -v 优先，再依次探 /opt/homebrew/bin(M) 与 /usr/local/bin(Intel)
#   ② fswatch 是外部依赖，没装就静默不备份
#      对策：探测不到 fswatch → 自动退回「轮询模式」（与 Windows amber-watch.ps1 同哲学，零依赖）
#   ③ 记忆中心路径写死
#      对策：AMBER_MC 环境变量优先，默认 $HOME/[记忆共享中心]
# ─────────────────────────────────────────────────────────────
# 测试用环境变量：
#   AMBER_MC         记忆中心根
#   AMBER_INTERVAL   轮询间隔秒（默认 15，仅轮询模式用）
#   AMBER_ONCE=1     只跑一轮就退出（轮询模式，功能测试用）
#   AMBER_MAXSEC     最长运行秒数（0=永久）
#   AMBER_NO_FSWATCH=1  强制走轮询（测试回退路径用）

set -u

HOMEDIR="${HOME}"
MC="${AMBER_MC:-$HOMEDIR/[记忆共享中心]}"
ENGINE="$MC/记忆琥珀/engine"
BACKUP_SCRIPT="$ENGINE/amber-backup.sh"
LOG_DIR="$ENGINE/logs"
WATCH_LOG="$LOG_DIR/amber-watch.log"
HEARTBEAT="$LOG_DIR/amber-watch.heartbeat"
LOCK_FILE="/tmp/amber-fswatch-debounce.lock"
DEBOUNCE_SEC=3
INTERVAL="${AMBER_INTERVAL:-15}"

mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >>"$WATCH_LOG"; }

# ── 监听目录（与白名单覆盖目录一致） ──
PATHS=(
  "$HOMEDIR/.workbuddy"
  "$MC/核心层"
  "$MC/QClaw记忆"
  "$MC/潜意识层"
  "$MC/情境层"
  "$MC/记忆规则"
  "$MC/成就系统/scripts"
  "$MC/技能配置/daily-buddy"
  "$MC/技能配置/shall-we-talk"
  "$MC/技能配置/triwich"
  "$MC/技能配置/clock-loop"
  "$MC/技能配置/growth-box"
  "$MC/技能配置/awaken-memory-system"
  "$MC/技能配置/reading-assistant"
  "$MC/技能配置/system-logger"
  "$MC/技能配置/meta-aletheia"
)

# 只保留真实存在的目录
EXIST_PATHS=()
for p in "${PATHS[@]}"; do
  [ -d "$p" ] && EXIST_PATHS+=("$p")
done

run_backup() {
  if [ ! -f "$BACKUP_SCRIPT" ]; then
    log "错误：备份脚本不存在 $BACKUP_SCRIPT"
    return
  fi
  nohup bash "$BACKUP_SCRIPT" >>"$LOG_DIR/amber-fswatch.out.log" 2>&1 &
}

# ── fswatch 路径探测（Intel + Apple Silicon 通用） ──
detect_fswatch() {
  if [ -n "${AMBER_NO_FSWATCH:-}" ]; then echo ""; return; fi
  local c
  c="$(command -v fswatch 2>/dev/null)"; [ -n "$c" ] && { echo "$c"; return; }
  for cand in /opt/homebrew/bin/fswatch /usr/local/bin/fswatch; do
    [ -x "$cand" ] && { echo "$cand"; return; }
  done
  echo ""
}
FSWATCH="$(detect_fswatch)"

# 心跳（30 秒一次，供只读判活）
( while true; do date '+%Y-%m-%d %H:%M:%S' >"$HEARTBEAT"; sleep 30; done ) &
HEARTBEAT_PID=$!
trap 'kill $HEARTBEAT_PID 2>/dev/null' EXIT

START_TS=$(date +%s)
maxsec_reached() {
  [ "${AMBER_MAXSEC:-0}" -gt 0 ] || return 1
  [ $(( $(date +%s) - START_TS )) -ge "${AMBER_MAXSEC:-0}" ]
}

if [ ${#EXIST_PATHS[@]} -eq 0 ]; then
  log "错误：没有可监听的目录（MC=${MC}）"
  exit 1
fi

# ═══ 模式 A：fswatch 事件监听（有 fswatch 时） ═══
if [ -n "$FSWATCH" ]; then
  log "=== 记忆琥珀监听启动（fswatch 模式，${FSWATCH}，${#EXIST_PATHS[@]} 个目录）==="
  rm -f "$LOCK_FILE"
  "$FSWATCH" -0 -l 2 -r "${EXIST_PATHS[@]}" | while IFS= read -r -d '' _event; do
    [ -f "$LOCK_FILE" ] && continue
    touch "$LOCK_FILE"
    ( sleep "$DEBOUNCE_SEC"; rm -f "$LOCK_FILE" ) &
    run_backup
  done
  exit 0
fi

# ═══ 模式 B：轮询回退（无 fswatch，与 Windows 同哲学，零依赖） ═══
log "=== 记忆琥珀监听启动（轮询回退模式 interval=${INTERVAL}s，未检测到 fswatch，${#EXIST_PATHS[@]} 个目录）==="
snapshot() {
  # 输出所有文件的 路径:mtime:size，供比对
  find "${EXIST_PATHS[@]}" -type f 2>/dev/null -exec stat -f '%N:%m:%z' {} + 2>/dev/null | sort
}
PREV=""
FIRST=1
while true; do
  CUR="$(snapshot)"
  if [ "$FIRST" -eq 1 ]; then
    FIRST=0                      # 首轮建基线，不触发
  elif [ "$CUR" != "$PREV" ]; then
    log "检测到变化，触发备份"
    run_backup
  fi
  PREV="$CUR"
  date '+%Y-%m-%d %H:%M:%S' >"$HEARTBEAT"
  [ -n "${AMBER_ONCE:-}" ] && { log "AMBER_ONCE 已设置，跑完一轮退出"; break; }
  maxsec_reached && { log "达到 AMBER_MAXSEC，退出"; break; }
  sleep "$INTERVAL"
done
