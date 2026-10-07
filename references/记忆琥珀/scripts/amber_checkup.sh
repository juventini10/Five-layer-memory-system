#!/bin/bash
# [G2-2 fail-loud 守卫 v2·检测串运行时拼装——字面量拆两段拼接，任何占位符替换正则均不可命中本行]
_self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
_PH='[记忆共享'_'中心]'
if grep -Fq "\"$_PH" "$_self" 2>/dev/null; then
  echo "❌ $(basename "$0"): 检测到未替换的记忆中心占位符——请按 step6.5b 完成占位符替换后再运行（拒绝字面运行·防静默假目录）" >&2
  exit 1
fi


# amber_checkup.sh — 琥珀每日体检（写状态文件，供唤醒Skill读盘保底提醒）
# 设计（§4.10 常态审计须脚本触发）：每天由 launchd 定时跑一次（com.memoryamber.checkup.plist）
#   体检两项独立指标（各自告警，不需同时满足）：
#     ① 永久收藏超 30 天无主动收藏（_major_ 件）→ 提醒
#     ② 琥珀顶层又出现手动散件（本该进永久收藏）→ 提醒
#   输出 = engine/amber-status.txt（守护写盘、Skill读盘——复用心跳检测先例）
#   ⚠️ 只提醒不代判：收藏与否永远由人决定
set -u
AMBER_DIR="$HOME/记忆共享中心/记忆琥珀"
PERM_DIR="$AMBER_DIR/永久收藏"
STATUS="$AMBER_DIR/engine/amber-status.txt"

# 指标①：距最近一次主动收藏的天数
newest_pin=$(find "$PERM_DIR" -maxdepth 1 -name "*_major_*.bak" -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
if [ -z "$newest_pin" ]; then
  last_pin_days="NEVER"
else
  last_pin_days=$(( ( $(date +%s) - $(stat -f %m "$newest_pin") ) / 86400 ))
fi

# 指标②：顶层手动散件数（非 .bak 滚动件、非 .DS_Store；2026-07-26起顶层应为零散件）
stray=$(find "$AMBER_DIR" -maxdepth 1 -type f ! -name "*.bak" ! -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')

# 告警判定
alert=""
if [ "$last_pin_days" = "NEVER" ] || { [ "$last_pin_days" != "NEVER" ] && [ "$last_pin_days" -ge 30 ]; }; then
  alert="⚠️ 永久收藏已 ${last_pin_days} 天没有新收藏——最近有定稿、改好的重要文件想永久留住吗？对AI说：帮我永久保存某某文件。"
fi
if [ "$stray" -gt 0 ]; then
  alert="${alert}${alert:+ ｜ }⚠️ 琥珀顶层出现 ${stray} 个手动散件，建议归进「永久收藏」。"
fi
[ -z "$alert" ] && alert="✅ 琥珀双轨正常。"

{
  echo "UPDATED=$(date '+%Y-%m-%d %H:%M:%S')"
  echo "LAST_PIN_DAYS=${last_pin_days}"
  echo "STRAY_TOPLEVEL=${stray}"
  echo "PERM_TOTAL=$(find "$PERM_DIR" -maxdepth 1 -type f ! -name '归档清单*' ! -name '.DS_Store' 2>/dev/null | wc -l | tr -d ' ')"
  echo "MESSAGE=${alert}"
} > "$STATUS"
