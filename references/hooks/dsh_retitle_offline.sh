#!/bin/bash
# dsh_retitle_offline.sh — 停服 → 离线补标题 → 起服（一键·延迟执行·自我验证）
#
# 为什么必须"停服"才能补标题（2026-09-10 实证）
# --------------------------------------------
# DSH 把**已加载会话**的状态持有在内存里（会话目录下有 session.lock 标记）。
# 外部脚本改会话文件时：
#   · 未被加载的会话（无 lock）→ 改动立即生效 ✅
#   · 已加载的会话（有 lock）  → 宿主写盘时用**内存视图**覆盖 → 改动被吃掉 ❌
# 实证：10 个 lock 会话标题全部无效，未 lock 的 36 个全部生效。
# → 因此必须在**宿主停止**时批处理（此时无内存竞争），再启动宿主让它重新从磁盘加载。
#
# 为什么用"延迟 + 独立进程"
# ------------------------
# AI 自身跑在 DSH web 进程内 → 直接 kill 会连带杀掉自己、回复发不出去。
# 本脚本以 nohup 独立进程运行，延迟期内 AI 回复正常发出，随后自行完成全流程。
#
# 流程：等延迟 → 停 dsh web → 等端口释放 → 离线补标题 → 帧契约兜底 → 起 dsh web → 验证
#
# 用法：nohup bash dsh_retitle_offline.sh [延迟秒数] > /dev/null 2>&1 &
set -uo pipefail

DELAY="${1:-25}"
LOG="$HOME/.dsh/dsh-retitle.log"
WEBLOG="$HOME/.dsh/dsh-web.log"
PORT=3080
TOOLS="[记忆共享中心]/脚本中心"
TITLE="$TOOLS/dsh_session_title_batch.py"
REFRAME="$TOOLS/dsh_session_reframe.py"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export HOME="$HOME"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }

log "=== 离线补标题流程启动（延迟 ${DELAY}s）==="
sleep "$DELAY"

# ---------- 1. 停服 ----------
OLD_PID=$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1)
if [ -n "${OLD_PID:-}" ]; then
    kill "$OLD_PID" 2>/dev/null
    log "已停 dsh web（PID=$OLD_PID）"
else
    log "端口 $PORT 无监听者（无需停）"
fi
for i in $(seq 1 20); do
    sleep 1
    lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1 || { log "端口已释放（${i}s）"; break; }
done
if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    log "❌ 端口 $PORT 未释放——中止（⛔不在宿主运行时改文件）"
    exit 1
fi

# ---------- 2. 离线补标题（忽略 lock/mtime·此时无内存竞争） ----------
if [ -f "$TITLE" ]; then
    TOUT=$(python3 "$TITLE" --apply --force --ignore-lock 2>&1)
    log "标题批处理：$(printf '%s' "$TOUT" | grep -E '统计' | tail -1)"
    printf '%s\n' "$TOUT" | grep -E '✅' | tail -8 >> "$LOG"
else
    log "⚠️ 未找到 $TITLE —— 跳过补标题"
fi

# ---------- 3. 帧契约兜底（⛔任何写路径出问题都不许落盘成坏文件） ----------
if [ -f "$REFRAME" ]; then
    ROUT=$(python3 "$REFRAME" --fix --all 2>&1)
    log "帧契约体检：$(printf '%s' "$ROUT" | grep -E '统计|合规' | tail -1)"
    printf '%s' "$ROUT" | grep -qE '⚠️ 失败' && log "⚠️ 帧契约修复存在失败，见 dsh-retitle.log 上方"
fi

# ---------- 4. 起服 ----------
if ! command -v dsh >/dev/null 2>&1; then
    log "❌ dsh 不在 PATH（$PATH）——需人工恢复"
    exit 1
fi
cd "$HOME" || exit 1
log "启动: dsh web"
nohup dsh web >> "$WEBLOG" 2>&1 &

OK=0
for i in $(seq 1 40); do
    sleep 1
    NPID=$(lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1)
    if [ -n "${NPID:-}" ]; then
        log "✅ 重启成功：新 PID=$NPID（耗时 ${i}s）"
        OK=1
        break
    fi
done

if [ "$OK" -ne 1 ]; then
    log "❌ 重启失败：dsh web 未能在 40s 内监听 $PORT"
    tail -15 "$WEBLOG" 2>/dev/null >> "$LOG"
    exit 1
fi

log "=== 离线补标题流程完成·刷新页面即可看到统一标题 ==="
