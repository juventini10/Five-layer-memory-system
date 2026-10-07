#!/bin/bash
# dsh_frame_guard.sh — DSH 会话文件 zstd 帧契约**快守卫**（launchd 承载·每 60s）
#
# 家族：守卫（守） ｜ 部署形态：调度
# version: v0.2
# 职责：机械体检 + 即刻修复 ~/.dsh/sessions 会话文件的**两道契约**——帧契约（zstd 首帧=单行 header）
#       + v0 内容契约（seq 严格连续·v0 遗留格式的加载硬约束），使 session/list 与各会话历史恒可加载
#
# 为什么单独一条 60s 快链（2026-09-10 四次事故根治）
# ─────────────────────────────────────────────────────────
# 症状：任一会话文件的"首帧 ≠ 单行 header"违反 DSH 加载器契约（assertZstdHeaderFrame）
#       → **整个 session/list 失败** → 侧栏只剩当前会话（看起来"对话全没了"）。
# 旧防线的两个缺口（本次事故原样漏过）：
#   ① 位置：帧体检排在 15 分钟一轮的 session-patrol **末尾**，前面还有 31s 的 role 修复
#      与 LLM 标题批处理 → 检测窗口最长十几分钟；
#   ② 判据：旧版对 300s 内写过的文件直接跳过，却在 last_status 写"无坏会话"= 假全清。
# 本守卫：只做帧契约（批量 0.2s·单 node 进程）+ 违规**即刻**重压缩修复 → 检测窗口 ≤60s。
# 职责分离：role 修复 / 标题批处理仍留给 15 分钟的 session-patrol（贵活慢链）。
#
# 安全：修复全权委托 dsh_session_reframe.py（备份+内容逐字节回验+合约回验+原子替换），
#       本脚本只负责"何时跑"，⛔不自己写会话文件。
set -uo pipefail

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REFRAME="[记忆共享中心]/脚本中心/dsh_session_reframe.py"
STATE_DIR="$HOME/.dsh/cache/frame-guard"
LOCK="$STATE_DIR/guard.lock"
LOG="$STATE_DIR/guard.log"

mkdir -p "$STATE_DIR" || exit 0

# 并发锁（目录创建原子性；陈旧锁 >120s 视为残留自动清理·⚠️被 kill -9 时不触发 EXIT trap）
#   ⚠️ 为何 120s：单轮体检 0.2s、含修复 ≤10s ⇒ 超过 120s 的锁必是死锁（旧值 600s 会让
#   一次 SIGKILL 换来最长 10 分钟守卫空窗——机制自己变成故障源）。
if ! mkdir "$LOCK" 2>/dev/null; then
    if [ -d "$LOCK" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || echo 0) ))
        [ "$age" -gt 120 ] && rmdir "$LOCK" 2>/dev/null
    fi
    exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

[ -f "$REFRAME" ] || exit 0

OUT=$(python3 "$REFRAME" --fix --all 2>&1)
RC=$?
STAT=$(printf '%s' "$OUT" | grep -oE '统计：.*' | tail -1)

# 心跳（执行证据=校验路径·不依赖读配置文件）
date +%s > "$STATE_DIR/last_run.ts"

if printf '%s' "$OUT" | grep -qE '🔧'; then
    {
        echo "=== $(date '+%F %T') ⚠️ 帧契约违规·已自愈（侧栏不会空白）==="
        printf '%s\n' "$OUT" | grep -E '🔧|统计' | tail -12
    } >> "$LOG"
    echo "$(date '+%F %T') rc=$RC 已自愈 | ${STAT:-无统计行}" > "$STATE_DIR/last_status.txt"
elif printf '%s' "$OUT" | grep -qE '⚠️ 失败'; then
    {
        echo "=== $(date '+%F %T') ⚠️ 自愈失败（需人工介入）==="
        printf '%s\n' "$OUT" | grep -E '⚠️|统计|   ' | tail -10
    } >> "$LOG"
    echo "$(date '+%F %T') rc=$RC ⚠️ 自愈失败 | ${STAT:-无统计行}" > "$STATE_DIR/last_status.txt"
else
    # 真实计数（⛔不写"静默/无坏会话"这类无法分辨"没扫"与"扫了没事"的假全清）
    echo "$(date '+%F %T') rc=$RC 合规 | ${STAT:-无统计行}" > "$STATE_DIR/last_status.txt"
fi

# ---------- 第二道契约：v0 内容契约（seq 严格连续）按变更体检 ----------
# 60s 快链承担它，靠「(mtime,size) 指纹缓存」把稳态成本压到 ~0（只在文件变动后真解压校验）；
# 发现断链即调用 dsh_session_row_restore 自愈（备份基准·不虚构·写盘前双验）。
V0REST="[记忆共享中心]/脚本中心/dsh_session_row_restore.py"
if [ -f "$V0REST" ]; then
    VOUT=$(python3 "$V0REST" --watch 2>&1)
    if printf '%s' "$VOUT" | grep -q '🔧'; then
        {
            echo "=== $(date '+%F %T') ⚠️ v0 内容契约违规·已自愈 ==="
            printf '%s\n' "$VOUT" | grep -E '🔧|v0 变更体检'
        } >> "$LOG"
        echo "$(date '+%F %T') v0 契约：已自愈 | $(printf '%s' "$VOUT" | grep -oE 'v0 变更体检：.*' | tail -1)" >> "$STATE_DIR/last_status.txt"
    elif printf '%s' "$VOUT" | grep -q '⚠️'; then
        echo "$(date '+%F %T') ⚠️ v0 契约自愈失败：$(printf '%s' "$VOUT" | grep -oE '⚠️.*' | head -1)" >> "$STATE_DIR/last_status.txt"
        printf '%s\n' "$VOUT" | grep -E '⚠️|v0 变更体检' >> "$LOG"
    fi
fi

exit 0
