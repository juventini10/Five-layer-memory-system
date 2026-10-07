#!/bin/bash
# dsh_frame_guard_loop.sh <持续秒数> — 帧契约快守卫「自续短链」（由 session-patrol 每轮重生）
#
# 家族：引擎（引） ｜ 部署形态：调度
# version: v0.1
# 职责：按寿命契约（chain_end.ts）重生 dsh_frame_guard.sh 快链，把检测窗口压到 60s 内
#
# 为什么不用独立 launchd job（2026-09-10 实证）
# ────────────────────────────────────────────
# DSH 会话内无法向 launchd 注册新 job：`launchctl bootstrap gui/$UID <plist>` 返回
# "Bootstrap failed: 5: Input/output error"，且**用已知已加载的巡逻 plist 换 label 做对照
# 同样失败** → 是执行上下文被挡，不是 plist 内容问题。故改为"借已注册的巡逻 job 自续"：
#   patrol 由 launchd 拉起 ⇒ 它 fork 的后代不被 DSH 进程树连带杀死
#   （对比教训：AI 在会话内 nohup 的离线修复脚本会随 dsh web 一起被杀·见 dsh_offline_repair.sh 头注）。
# 每轮寿命 = 巡逻区间 - 余量，天然收敛，⛔不会堆叠残留；巡逻停跑则快链最长 15 分钟内自灭。
#
# 用法（巡检脚本内部调用·也可手动）：
#   nohup bash dsh_frame_guard_loop.sh 880 &
set -uo pipefail

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

GUARD="[记忆共享中心]/脚本中心/dsh_frame_guard.sh"
STATE_DIR="$HOME/.dsh/cache/frame-guard"
LOG="$STATE_DIR/guard-loop.log"
DURATION="${1:-880}"

mkdir -p "$STATE_DIR" || exit 0

# 单实例判定 = 「上一条快链的计划寿命到了没」（chain_end.ts）—— 2026-09-10 三次实测修正：
#   · 锁文件方案有致命反例：快链被 SIGKILL 时不触发 EXIT trap → 留死锁 → 新快链看到"锁在"
#     直接退出，陈旧阈值 20min ⇒ 最长 20 分钟守卫空窗（机制自己变成故障源）。
#   · 心跳新鲜度方案有边界坑：快链 840s、巡逻 900s ⇒ 巡逻到场时心跳仅 60s 前 ⇒ 被误判"活跃"
#     ⇒ 跳过重生，空窗直接放大到一个巡逻周期（15 分钟）。
#   二者都不如"寿命契约"确定：启动时写下 END 时间戳，巡逻只在 now > END+30 时才重生。
#   ⇒ 无空窗、无堆叠、无死锁，判断只依赖一个数字。
CHAIN_END_FILE="$STATE_DIR/chain_end.ts"
if [ -f "$CHAIN_END_FILE" ]; then
    PREV_END=$(cat "$CHAIN_END_FILE" 2>/dev/null || echo 0)
    case "$PREV_END" in ''|*[!0-9]*) PREV_END=0 ;; esac
    if [ "$(date +%s)" -le $((PREV_END + 30)) ]; then
        exit 0          # 上一条快链仍在计划寿命内 → 不重生（防堆叠）
    fi
fi

[ -f "$GUARD" ] || exit 0

END=$(( $(date +%s) + DURATION ))
echo "$END" > "$CHAIN_END_FILE"
echo "$(date '+%F %T') 快链启动（${DURATION}s·60s/轮·END=${END}）" >> "$LOG"

while [ "$(date +%s)" -lt "$END" ]; do
    bash "$GUARD"          # 单轮自带并发锁 + 静默幂等 + 真实计数状态行
    sleep 60
done

echo "$(date '+%F %T') 快链到期退出（下一轮巡逻重生）" >> "$LOG"
exit 0
