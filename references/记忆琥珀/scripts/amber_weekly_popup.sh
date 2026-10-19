#!/bin/bash
# [G2-2 fail-loud 守卫 v2·检测串运行时拼装——字面量拆两段拼接，任何占位符替换正则均不可命中本行]
_self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
_PH='[记忆共享'_'中心]'
if grep -Fq "\"$_PH" "$_self" 2>/dev/null; then
  echo "❌ $(basename "$0"): 检测到未替换的记忆中心占位符——请按 step6.5b 完成占位符替换后再运行（拒绝字面运行·防静默假目录）" >&2
  exit 1
fi


# amber_weekly_popup.sh — 琥珀周报弹窗（加强渠道，保底仍是唤醒Skill读盘）
# 设计：每周日 19:30 由 launchd 定时触发（com.memoryamber.weeklypopup.plist）
#   出口 = display dialog 中央模态框（与成就系统 achievement_tracker.py L287 同款）
#   文案规范：大白话——零AI基础、零电脑基础的人也能看懂要做什么（大白话文案规范）
#     禁用词：pin / 滚动区 / 永久区 / major —— 对人只说"临时备份 / 永久收藏"
#     行动指引必须带位置：说了怎么存，就要说存在哪（大白话文案规范）
#   ⚠️ 只提醒不代判：收藏与否永远由人决定
set -u
# 记忆中心定位（C03·2026-10-14 E2E 实跑根治·与 amber_checkup.sh 同型同判据）：
# 本行原写死 `$HOME/记忆共享中心/记忆琥珀`——是「字面目录名」而非占位符 `[记忆共享中心]`，
# step6.5b 的 sed 命中不了它；用户中心改名同样落空 → 周报永远读不到 永久收藏 数据。
# 口径：环境变量 > 真源自定位 > 具名候选 > 结构兜底 > 全落空 fail-loud（⛔不静默兜底假路径）
_is_center() { [ -d "$1/记忆琥珀/engine" ] && [ -d "$1/记忆规则" ]; }   # 同时具备才认定，防撞名误命中
_MC=""
for _c in "${AMBER_MC:-}" "${MEMORY_CENTER:-}" \
          "$(cd "$(dirname "$0")/../.." 2>/dev/null && pwd)" \
          "$HOME/记忆共享中心" "$HOME/共享中心" "$HOME/记忆中心" "$HOME/布洛陀记忆中心"; do
  # ⛔ 具名候选只放「端用户可能起的通用名」，不放作者侧目录名（作者目录名进包=占位化链路孤儿，
  #   manifest_coverage_check 判红；且下面 $HOME/*/ 结构兜底本就按**结构特征**认中心，与目录叫什么无关）
  [ -n "$_c" ] && _is_center "$_c" && { _MC="$_c"; break; }
done
if [ -z "$_MC" ]; then
  for _d in "$HOME"/*/; do                        # 结构兜底：扫 $HOME 一层子目录
    _d="${_d%/}"; [ -d "$_d" ] && _is_center "$_d" && { _MC="$_d"; break; }
  done
fi
if [ -z "$_MC" ]; then
  echo "❌ $(basename "$0")：未探测到记忆中心（须同时含 记忆琥珀/engine 与 记忆规则）——请设 AMBER_MC=<绝对路径> 或 MEMORY_CENTER=<绝对路径> 后重跑；⛔不静默兜底假路径（防弹窗文案与数据错位）" >&2
  exit 2
fi
AMBER_DIR="$_MC/记忆琥珀"
PERM_DIR="$AMBER_DIR/永久收藏"

# 临时备份：本周（7天内）新增数
bak_week=$(find "$AMBER_DIR" -maxdepth 1 -name "*.bak" -mtime -7 2>/dev/null | wc -l | tr -d ' ')

# 永久收藏：总件数 + 最近一次主动收藏距今天数
perm_total=$(find "$PERM_DIR" -maxdepth 1 -type f ! -name "归档清单*" ! -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
newest_pin=$(find "$PERM_DIR" -maxdepth 1 -name "*_major_*.bak" -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1)
if [ -z "$newest_pin" ]; then
  perm_msg="「永久收藏」里有 ${perm_total} 份文件，但你还没主动收藏过新东西。"
else
  age_days=$(( ( $(date +%s) - $(stat -f %m "$newest_pin") ) / 86400 ))
  perm_msg="「永久收藏」里有 ${perm_total} 份文件，最近一次收藏是 ${age_days} 天前。"
fi

# 补偿守卫（关机错过补弹·静默幂等）：只在「最近一个周日19:30已过 且 该周期还没弹过」时才弹
# 正常周日19:30触发=该弹；开机RunAtLoad触发=本周期弹过就静默退出，没弹过就补弹一次
LOG="$AMBER_DIR/engine/logs/weekly-popup.log"
now_epoch=$(date +%s)
dow=$(date +%w)
target=$(date -v-"${dow}"d -v19H -v30M -v0S +%s)
[ "$target" -gt "$now_epoch" ] && target=$((target - 604800))
last_pop=0
if [ -f "$LOG" ]; then
  last_ts=$(tail -1 "$LOG" | sed -E 's/^\[([0-9-]+ [0-9:]+)\].*/\1/')
  [ -n "$last_ts" ] && last_pop=$(date -j -f "%Y-%m-%d %H:%M:%S" "$last_ts" +%s 2>/dev/null || echo 0)
fi
[ "$last_pop" -ge "$target" ] && exit 0

# 提示音
afplay /System/Library/Sounds/Glass.aiff >/dev/null 2>&1 &

# 中央模态框（大白话文案 + 存放位置指引）
osascript -e "tell app \"System Events\" to display dialog \"这一周，我自动帮你临时备份了 ${bak_week} 次。\n（临时备份只保留 7 天，之后会自动清掉）\n\n${perm_msg}\n\n如果这周有写完、改好的重要文件，想永远留住——\n就对 AI 说：帮我永久保存某某文件。\n\n收藏好的文件都在这里：\n记忆共享中心 → 记忆琥珀 → 永久收藏\" with title \"🟠 每周备份小管家 · $(date '+%m月%d日')\" buttons {\"知道了\"} default button \"知道了\" with icon note giving up after 60" >/dev/null 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 周报弹窗已发送：临时备份+${bak_week} / ${perm_msg}" >> "$AMBER_DIR/engine/logs/weekly-popup.log"
