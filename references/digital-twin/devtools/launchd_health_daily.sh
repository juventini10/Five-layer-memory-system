#!/usr/bin/env bash
#
# launchd_health_daily.sh — launchd健康巡检常态化wrapper（P0-3）
# Version: 1.0.0 (2026-09-03)
#
# 职责（单一）：定期运行健康巡检，自动kickstart死形态任务，写系统日志。
# 设计原则（守卫编写规范 + 脚本哲学）：
#   - 单一职责：health_check负责"检测"（人读友好），本wrapper负责"报告+自愈"
#   - 自愈有界：只kickstart一次，验证exit=0才算修复，不无限重试
#   - 日志分层：异常时写详细8字段条目，正常时写简洁摘要
#   - 失败放行：本脚本自身失败不阻断其他任务（exit 0除非严重错误）
#
# 自动kickstart逻辑（童灵愿景裁决2026-09-03）：
#   runs=0 → kickstart一次 → 等待5秒 → 检查exit code
#   exit=0 → 标记已修复并记录
#   exit!=0 → 报警（runs数增加≠任务成功，必须验证exit=0）
#
# 用法：
#   launchd_health_daily.sh   # 完整运行（巡检+自愈+日志）
#
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HEALTH_CHECK="$SCRIPT_DIR/launchd_health_check.sh"
LOG_SCRIPT="[记忆共享中心]/技能配置/system-logger/scripts/append_log_entry.py"
BANNER_SCRIPT="[记忆共享中心]/技能配置/system-logger/scripts/render_mode_banner.py"

# ── 1. 运行健康巡检 ──────────────────────────────────────────────
output=$("$HEALTH_CHECK" --summary 2>&1) || true

# ── 1b. plist 脚本漂移重指提案（B段·plist_repoint.py·2026-10-20 人工批·只提案不写入·失败放行）──
REPOINT="${SCRIPT_DIR}/plist_repoint.py"
if [ -x "$REPOINT" ]; then
  repoint_out=$(/usr/bin/python3 "$REPOINT" 2>&1) || true
  if echo "$repoint_out" | grep -q "提案 "; then
    output="${output}
[plist重指提案] $(echo "$repoint_out" | grep -c '提案 ') 件待批准（运行 plist_repoint.py --apply 或人工处置）"
    echo "$repoint_out" >> "${SCRIPT_DIR}/repoint_proposals.log"
  fi
fi

# 解析摘要数字（macOS BSD grep不支持-P，用sed）
healthy=$(echo "$output" | sed -n 's/.*健康: \([0-9]*\).*/\1/p' | head -1)
dead=$(echo "$output" | sed -n 's/.*死形态: \([0-9]*\).*/\1/p' | head -1)
error=$(echo "$output" | sed -n 's/.*异常: \([0-9]*\).*/\1/p' | head -1)
stale=$(echo "$output" | sed -n 's/.*日志陈旧: \([0-9]*\).*/\1/p' | head -1)
total=$(echo "$output" | sed -n 's/.*共 \([0-9]*\).*/\1/p' | head -1)
# 空值兜底
[[ -z "$healthy" ]] && healthy="?"
[[ -z "$dead" ]] && dead="?"
[[ -z "$error" ]] && error="?"
[[ -z "$stale" ]] && stale="?"
[[ -z "$total" ]] && total="?"

# ── 2. 自动kickstart死形态任务（自愈有界）──────────────────────
kickstart_results=""
if [[ "$dead" =~ ^[0-9]+$ ]] && [[ "$dead" -gt 0 ]]; then
  dead_labels=$(echo "$output" | grep "🔴.*死形态" | sed 's/.*🔴 //' | sed 's/:.*//' || true)
  for label in $dead_labels; do
    [[ -z "$label" ]] && continue
    if launchctl kickstart -k "gui/$(id -u)/$label" >/dev/null 2>&1; then
      sleep 5
      new_exit=$(launchctl print "gui/$(id -u)/$label" 2>/dev/null | grep "last exit code" | head -1 | sed 's/.*= //' | tr -d ' ' || echo "?")
      if [[ "$new_exit" == "0" ]]; then
        kickstart_results+="✅$label kickstart修复(exit=0); "
      else
        kickstart_results+="🔴$label kickstart后exit=$new_exit(需人工排查); "
      fi
    else
      kickstart_results+="🔴$label kickstart失败; "
    fi
  done
fi

# ── 3. 写系统日志（异常详写/正常略写）──────────────────────────
# 先跑banner（输出丢弃，满足Skill流程要求）
python3 "$BANNER_SCRIPT" --mode 日写入 >/dev/null 2>&1 || true

if [[ "$dead" == "0" && "$error" == "0" ]]; then
  # 正常：简洁摘要
  python3 "$LOG_SCRIPT" --tool 豆包 >/dev/null 2>&1 << EOF
### launchd健康巡检（常态化·12h）
- **工具**：豆包
- **完成**：<NOW>
- **类型**：巡检
- **涉及文件**：launchd任务共${total}个
- **对话摘要**：P0-3 launchd健康巡检常态化自动运行（每12小时）
- **结论**：✅全部健康——健康${healthy}/死形态${dead}/异常${error}/日志陈旧${stale}
- **来源**：🟢验证
- **置信度**：🟢A
EOF
  log_status="✅正常已记"
else
  # 异常：详细条目
  python3 "$LOG_SCRIPT" --tool 豆包 >/dev/null 2>&1 << EOF
### launchd健康巡检（常态化·发现异常+自动自愈）
- **工具**：豆包
- **完成**：<NOW>
- **类型**：巡检+自愈
- **涉及文件**：launchd任务共${total}个
- **对话摘要**：P0-3 launchd健康巡检常态化自动运行，发现死形态/异常任务并自动kickstart
- **结论**：⚠️发现异常——健康${healthy}/🔴死形态${dead}/🟠异常${error}/🟡日志陈旧${stale}。自动kickstart结果：${kickstart_results:-无死形态任务}。修复建议：kickstart后仍exit!=0的任务需人工排查plist配置/脚本bug；日志陈旧任务检查调度间隔是否合理。
- **来源**：🟢验证
- **置信度**：🟢A
EOF
  log_status="⚠️异常已记+自愈"
fi

# ── 4. 输出巡检结果（供launchd日志）────────────────────────────
echo "=== launchd健康巡检常态化 $(date '+%Y-%m-%d %H:%M') ==="
echo "任务: ${total} | 健康: ${healthy} | 死形态: ${dead} | 异常: ${error} | 日志陈旧: ${stale}"
echo "自愈: ${kickstart_results:-无}"
echo "日志: ${log_status}"
echo "$output" | tail -5
