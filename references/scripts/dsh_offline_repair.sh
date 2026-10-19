#!/bin/bash
# dsh_offline_repair.sh — 停服窗口内修复会话（seq 撞号 + 标题 + 帧契约）
#
# 家族：引擎（引） ｜ 部署形态：调度
# version: v0.2
# 职责：停服窗口内按序修复会话文件（seq 撞号→v0 内容契约复原→标题→帧契约）并重启 dsh web
#
# 为什么必须由 launchd 运行（⛔不要直接 bash 执行）
# -------------------------------------------------
# 2026-09-10 实测：AI 在会话内直接 nohup 启动本类脚本时，脚本在 kill 掉 dsh web 后
# **自己也随之被杀**（dsh-retitle.log 只留下一行启动记录）→ 修复从未执行。
# 用 `launchctl submit` 运行可让任务成为 launchd 的子进程，完全脱离 DSH 进程树。
#
# 正确用法（在**终端**跑，不要在 DSH 会话里跑）：
#   launchctl submit -l com.buluotuo.dsh.offline-repair \
#     -o /tmp/dsh-repair.out -e /tmp/dsh-repair.err \
#     -- /bin/bash "[记忆共享中心]/脚本中心/dsh_offline_repair.sh" 15
#
# 流程：等延迟 → 停 dsh web → 确认窗口 → 修 seq → 补标题+同步缓存 → 帧契约 → 起 dsh web → 验证
set -uo pipefail

DELAY="${1:-15}"
PORT=3080
LOG="$HOME/.dsh/dsh-repair.log"
WEBLOG="$HOME/.dsh/dsh-web.log"
TOOLS="[记忆共享中心]/脚本中心"

export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export HOME="$HOME"

log() { echo "$(date '+%F %T') $*" >> "$LOG"; }
listening() { lsof -nP -iTCP:$PORT -sTCP:LISTEN -t 2>/dev/null | head -1; }

log "=== 离线修复流程启动（延迟 ${DELAY}s·由 launchd 运行）==="
sleep "$DELAY"

# ---------- 1. 停服（并确保窗口真的打开：最多重试 5 次，防沙箱立刻拉起） ----------
for i in $(seq 1 5); do
    PID=$(listening)
    if [ -n "${PID:-}" ]; then
        kill "$PID" 2>/dev/null
        log "第${i}次停 dsh web（PID=${PID}）"
        sleep 1
    fi
    if [ -z "$(listening)" ]; then
        log "✅ 端口已释放（第${i}轮）"
        break
    fi
done

if [ -n "$(listening)" ]; then
    log "❌ 端口 $PORT 始终被占用（沙箱自动拉起？）——中止，⛔不在宿主运行时改文件"
    exit 1
fi

# ---------- 2. 修 seq 撞号（⛔须先于标题步骤：标题步骤依赖事件流已合法） ----------
if [ -f "$TOOLS/dsh_session_fix_seq.py" ]; then
    SOUT=$(python3 "$TOOLS/dsh_session_fix_seq.py" --fix --all 2>&1)
    log "seq修复：$(printf '%s' "$SOUT" | grep -E '统计' | tail -1)"
    printf '%s\n' "$SOUT" | grep -E '🔧|⚠️' | tail -10 >> "$LOG"
fi

# ---------- 3. 补标题 + 同步投影缓存（此时无宿主内存态竞争） ----------
if [ -f "$TOOLS/dsh_session_title_batch.py" ]; then
    TOUT=$(python3 "$TOOLS/dsh_session_title_batch.py" --apply --force --ignore-lock 2>&1)
    log "标题批处理：$(printf '%s' "$TOUT" | grep -E '统计' | tail -1)"
fi

# ---------- 3.5 v0 内容契约复原（★禁源之后的自愈兜底） ----------
# 为什么必须有：本流第 2 步的 fix_seq 曾一次改坏 10 个 v0 会话（删中间 title 行 → seq 断链 →
#   整会话历史加载失败）。现已在该工具加 v0 跳过守卫，本步是"万一还有别的路径造成断链"的兜底：
#   以历史备份为基准把缺失行按原位插回，⛔不虚构事件。
if [ -f "$TOOLS/dsh_session_row_restore.py" ]; then
    ROUT2=$(python3 "$TOOLS/dsh_session_row_restore.py" --fix --all 2>&1)
    log "v0 复原：$(printf '%s' "$ROUT2" | grep -E '统计' | tail -1)"
    printf '%s\n' "$ROUT2" | grep -E '🔧|⚠️' | tail -10 >> "$LOG"
fi

# ---------- 4. 帧契约兜底 ----------
if [ -f "$TOOLS/dsh_session_reframe.py" ]; then
    ROUT=$(python3 "$TOOLS/dsh_session_reframe.py" --fix --all 2>&1)
    log "帧契约：$(printf '%s' "$ROUT" | grep -E '统计' | tail -1)"
fi

# ---------- 5. 起服 ----------
if ! command -v dsh >/dev/null 2>&1; then
    log "❌ dsh 不在 PATH——需人工恢复"
    exit 1
fi
cd "$HOME" || exit 1
nohup dsh web >> "$WEBLOG" 2>&1 &
log "已发起 dsh web 启动"

OK=0
for i in $(seq 1 40); do
    sleep 1
    NPID=$(listening)
    if [ -n "${NPID:-}" ]; then
        log "✅ 修复完成并重启成功：新 PID=${NPID}（耗时 ${i}s）"
        OK=1
        break
    fi
done
[ "$OK" -ne 1 ] && log "❌ 重启失败：40s 内未监听 ${PORT}（见 ${WEBLOG}）"
log "=== 离线修复流程结束 ==="
