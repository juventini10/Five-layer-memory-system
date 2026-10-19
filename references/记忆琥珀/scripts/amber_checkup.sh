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
# 记忆中心定位（C03·2026-10-14 E2E 实跑根治）：本行原写死 `$HOME/记忆共享中心/记忆琥珀`。
# 那是「字面目录名」而不是占位符 `[记忆共享中心]`——step6.5b 的 sed 正则物理上命中不了它；
# 用户的记忆中心改名（如 AI记忆库/共享中心）时同样落空。后果：体检每次 exit 1、
# amber-status.txt 写不出、唤醒Skill读盘的保底提醒永久静默（守护面谎报）。
# 口径与同族先例一致（skill_version_check.py L157 / verify.sh §MC）：
#   环境变量 > 真源自定位 > 具名候选 > 结构兜底 > 全落空 fail-loud（⛔不静默兜底假路径）
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
  echo "❌ $(basename "$0")：未探测到记忆中心（须同时含 记忆琥珀/engine 与 记忆规则）——请设 AMBER_MC=<绝对路径> 或 MEMORY_CENTER=<绝对路径> 后重跑；⛔不静默兜底假路径（防状态写进错目录、提醒谎报正常）" >&2
  exit 2
fi
AMBER_DIR="$_MC/记忆琥珀"
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
# F15 根治（2026-10-17）：装机自带 README.md（step3 3b 整目录复制）旧被判「手动散件」
#   ⇒ 每台新机天天误报。排除装机自带件。
stray=$(find "$AMBER_DIR" -maxdepth 1 -type f ! -name "*.bak" ! -name ".DS_Store" ! -name "README.md" 2>/dev/null | wc -l | tr -d ' ')

# 告警判定
alert=""
if [ "$last_pin_days" = "NEVER" ]; then
  # P15 根治（2026-10-19）：哨兵值 NEVER 不进用户话术——内部标记直出=脏文案跨端扩散
  alert="⚠️ 永久收藏还没有过第一条——最近有定稿、改好的重要文件想永久留住吗？对AI说：帮我永久保存某某文件。"
elif [ "$last_pin_days" -ge 30 ]; then
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
