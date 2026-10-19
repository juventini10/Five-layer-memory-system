#!/bin/bash
# dsh_restart.sh — DSH 服务重启（脱离进程树执行·自我验证·失败留痕）
#
# 背景（2026-09-10）：DSH 由豆包办公沙箱 node 启动（PID 23139·自 15:42），普通终端关不掉它；
#   你授权代劳重启。因 AI 自身跑在该进程内，直接用 kill 会连带杀掉自己 → 本脚本设计为
#   **nohup 独立进程 + 延迟执行**：延迟期内 AI 回复正常发出，随后脚本独立完成 kill+重启+验证。
#
# 用法：nohup bash dsh_restart.sh [延迟秒数] > /dev/null 2>&1 &
set -uo pipefail

DELAY="${1:-25}"
LOG="$HOME/.dsh/dsh-restart.log"
WEBLOG="$HOME/.dsh/dsh-web.log"
PORT=3080

# 显式环境（nohup 继承的沙箱环境可能缺 PATH）
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export HOME="$HOME"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== 重启流程启动（延迟 ${DELAY}s）==="
sleep "$DELAY"

OLD_PID=$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1)
log "旧进程 PID=${OLD_PID:-无}"

if [ -n "${OLD_PID:-}" ]; then
    kill "$OLD_PID" 2>/dev/null
    log "已发 kill 信号 → $OLD_PID"
else
    log "端口无监听者（无需 kill）"
fi

# 等端口释放（最多 15s）
for i in $(seq 1 15); do
    sleep 1
    if ! lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
        log "端口 $PORT 已释放（${i}s）"
        break
    fi
done

# 启动新实例
if ! command -v dsh >/dev/null 2>&1; then
    log "❌ dsh 不在 PATH（${PATH}）——需人工恢复"
    exit 1
fi

cd "$HOME" || exit 1
log "启动: dsh web（输出追加至 dsh-web.log）"
nohup dsh web >> "$WEBLOG" 2>&1 &
NEW_SHELL_PID=$!
log "dsh web 已拉起（shell pid=${NEW_SHELL_PID}）·等待监听…"

# 验证（最多 40s）
OK=0
for i in $(seq 1 40); do
    sleep 1
    NPID=$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1)
    if [ -n "${NPID:-}" ]; then
        log "✅ 重启成功：新 PID=${NPID}（耗时 ${i}s）·URL 见 $WEBLOG 末行"
        OK=1
        break
    fi
done

if [ "$OK" -ne 1 ]; then
    log "❌ 重启失败：dsh web 未能在 40s 内监听 $PORT"
    log "--- dsh-web.log 末 15 行 ---"
    tail -15 "$WEBLOG" 2>/dev/null >> "$LOG"
    exit 1
fi

log "=== 重启流程完成 ==="
