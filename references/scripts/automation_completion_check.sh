#!/usr/bin/env bash
#
# automation_completion_check.sh — 自动化方案完成验收门禁（L3脚本门禁）
# Version: 1.0.0 (2026-09-02)
#
# 职责（单一）：验证自动化方案（launchd/cron/钩子类）的4项验收是否全部通过。
# 设计原则（铁律-021"终检靠脚本不靠自觉" + S014"自觉是安慰剂，机械是药"）：
#   - 脚本门禁：4项全过才exit 0，任何一项不过=方案未完成
#   - 不依赖自觉：AI/人不能跳过验证直接宣称完成
#   - 明确缺口：失败时指出具体缺哪一项、怎么补
#
# 4项验收（对应方案落地验证闭环）：
#   1. 配置文件已创建 —— plist/cron配置文件存在且格式合法
#   2. 首次运行已验证 —— launchctl runs>0 且 last exit code=0
#   3. 持续运行机制已确认 —— StartInterval/cron表达式存在且>0
#   4. 健康度监控已纳入 —— 任务label以com.buluotuo.开头（在launchd_health_check扫描范围内）
#
# 用法：
#   automation_completion_check.sh <label> [plist_path]
#
# 示例：
#   automation_completion_check.sh com.buluotuo.my-task
#   automation_completion_check.sh com.buluotuo.my-task ~/Library/LaunchAgents/com.buluotuo.my-task.plist
#
set -eo pipefail

if [[ $# -lt 1 ]]; then
  echo "❌ 用法: automation_completion_check.sh <label> [plist_path]"
  exit 1
fi

LABEL="$1"
PLIST="${2:-$HOME/Library/LaunchAgents/${LABEL}.plist}"

echo "🔒 自动化方案完成验收门禁 v1.0.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  任务: $LABEL"
echo "  plist: $PLIST"
echo ""

PASS=0
FAIL=0
FAILED_ITEMS=()

# ── 验收1：配置文件已创建 ─────────────────────────────────
echo "  [1/4] 配置文件已创建..."
if [[ -f "$PLIST" ]]; then
  # 验证plist格式合法
  if /usr/libexec/PlistBuddy -c "Print :Label" "$PLIST" >/dev/null 2>&1; then
    plist_label=$(/usr/libexec/PlistBuddy -c "Print :Label" "$PLIST" 2>/dev/null)
    if [[ "$plist_label" == "$LABEL" ]]; then
      echo "        ✅ 通过（plist存在且Label匹配）"
      PASS=$((PASS + 1))
    else
      echo "        ❌ 失败（plist的Label=$plist_label 与预期不匹配）"
      FAIL=$((FAIL + 1))
      FAILED_ITEMS+=("验收1: plist的Label不匹配（预期，实际）")
    fi
  else
    echo "        ❌ 失败（plist格式不合法）"
    FAIL=$((FAIL + 1))
    FAILED_ITEMS+=("验收1: plist格式不合法")
  fi
else
  echo "        ❌ 失败（plist不存在: ）"
  FAIL=$((FAIL + 1))
  FAILED_ITEMS+=("验收1: plist不存在（）")
fi

# ── 验收2：首次运行已验证 ─────────────────────────────────
echo "  [2/4] 首次运行已验证..."
detail=$(launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null || true)
if [[ -z "$detail" ]]; then
  echo "        ❌ 失败（任务未注册到launchd）"
  FAIL=$((FAIL + 1))
  FAILED_ITEMS+=("验收2: 任务未注册到launchd（执行 launchctl load ）")
else
  runs=$(echo "$detail" | grep -E "^\s*runs = " | head -1 | sed 's/.*runs = //' | tr -d ' ')
  exit_code=$(echo "$detail" | grep -E "^\s*last exit code = " | head -1 | sed 's/.*last exit code = //' | tr -d ' ')
  [[ -z "$runs" ]] && runs="0"
  [[ -z "$exit_code" ]] && exit_code="never"

  if [[ "$runs" == "0" ]]; then
    echo "        ❌ 失败（runs=0，从未运行过）"
    FAIL=$((FAIL + 1))
    FAILED_ITEMS+=("验收2: runs=0（从未运行，执行 launchctl kickstart -k gui/$(id -u)/）")
  elif [[ "$exit_code" != "0" ]]; then
    echo "        ❌ 失败（runs=$runs 但 exit code=）"
    FAIL=$((FAIL + 1))
    FAILED_ITEMS+=("验收2: 首次运行异常（exit code=）")
  else
    echo "        ✅ 通过（runs=$runs, exit code=0）"
    PASS=$((PASS + 1))
  fi
fi

# ── 验收3：持续运行机制已确认 ─────────────────────────────
echo "  [3/4] 持续运行机制已确认..."
if [[ -f "$PLIST" ]]; then
  interval=$(/usr/libexec/PlistBuddy -c "Print :StartInterval" "$PLIST" 2>/dev/null || echo "")
  calendar=$(/usr/libexec/PlistBuddy -c "Print :StartCalendarInterval" "$PLIST" 2>/dev/null || echo "")

  if [[ -n "$interval" && "$interval" -gt 0 ]]; then
    echo "        ✅ 通过（StartInterval=${interval}秒=$((interval/3600))小时）"
    PASS=$((PASS + 1))
  elif [[ -n "$calendar" ]]; then
    echo "        ✅ 通过（StartCalendarInterval已配置）"
    PASS=$((PASS + 1))
  else
    echo "        ❌ 失败（无StartInterval且无StartCalendarInterval）"
    FAIL=$((FAIL + 1))
    FAILED_ITEMS+=("验收3: 无持续运行机制（需配置StartInterval或StartCalendarInterval）")
  fi
else
  echo "        ⏭️  跳过（plist不存在，已在验收1判定）"
fi

# ── 验收4：健康度监控已纳入 ───────────────────────────────
echo "  [4/4] 健康度监控已纳入..."
if [[ "$LABEL" == com.buluotuo.* ]]; then
  echo "        ✅ 通过（label以com.buluotuo.开头，在launchd_health_check.sh扫描范围内）"
  PASS=$((PASS + 1))
else
  echo "        ❌ 失败（label不以com.buluotuo.开头，不在健康度巡检范围内）"
  FAIL=$((FAIL + 1))
  FAILED_ITEMS+=("验收4: label不以com.buluotuo.开头（重命名为com.buluotuo.xxx以纳入巡检）")
fi

# ── 最终判定 ──────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 验收结果：$PASS/4 通过"

if [[ $FAIL -eq 0 ]]; then
  echo "✅ 全部通过！方案已完成落地验证闭环。"
  echo "   可以宣称'自动化方案已完成'。"
  exit 0
else
  echo "❌ 未通过（项缺失）。方案未完成，不能宣称完成。"
  echo ""
  echo "📋 缺失项及修复方法："
  for item in "${FAILED_ITEMS[@]}"; do
    echo "   - $item"
  done
  echo ""
  echo "💡 快速修复：使用 create_launchd_task.sh 封装脚本会自动完成验收1-3，"
  echo "   验收4只需确保label以com.buluotuo.开头。"
  exit 1
fi
