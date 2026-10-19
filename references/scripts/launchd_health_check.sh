#!/usr/bin/env bash
#
# launchd_health_check.sh — 定时任务健康度巡检（L2持续巡检·方案落地验证闭环）
# Version: 1.0.0 (2026-09-02)
#
# 职责（单一）：扫描所有 com.buluotuo.* launchd 任务的运行状态，发现死形态/异常→报警。
# 设计原则（守卫编写规范 §八 + 脚本哲学 §二·五）：
#   - 只读巡检：不修改任何launchd配置
#   - 失败放行：异常 exit 1（供上游门禁判定），正常 exit 0
#   - 有痕输出：异常任务逐条列出原因
#   - 静默全绿：全部正常时仅输出摘要
#
# 检查项（3项机械判定）：
#   1. runs > 0 —— 从来没跑过=死形态（plist存在但从未触发）
#   2. last exit code = 0 —— 跑了但报错=异常
#   3. 日志新鲜度（如配置了StandardOutPath）—— 应该定期更新的日志超过预期间隔没更新=可能死了
#
# 用法：
#   launchd_health_check.sh            # 完整报告
#   launchd_health_check.sh --summary  # 仅摘要
#   launchd_health_check.sh --strict   # 有异常则exit 1（供门禁用）
#
set -eo pipefail

LABEL_PREFIX="com.buluotuo."
STRICT=0
SUMMARY_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    --summary) SUMMARY_ONLY=1 ;;
  esac
done

echo "🛡️  launchd 任务健康度巡检 v1.1.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 获取所有 com.buluotuo.* 任务
tasks=$(launchctl list 2>/dev/null | grep "$LABEL_PREFIX" | awk '{print $3}' || true)

if [[ -z "$tasks" ]]; then
  echo "⚠️  未找到任何 ${LABEL_PREFIX}* 任务"
  exit 0
fi

task_count=$(echo "$tasks" | wc -l | tr -d ' ')
healthy=0
dead=0
error=0
stale=0
dead_list=()
error_list=()
stale_list=()

while IFS= read -r label; do
  [[ -z "$label" ]] && continue

  # 获取任务详情
  detail=$(launchctl print "gui/$(id -u)/$label" 2>/dev/null || true)

  # 1. runs 数
  runs=$(echo "$detail" | grep -E "^\s*runs = " | head -1 | sed 's/.*runs = //' | tr -d ' ')
  [[ -z "$runs" ]] && runs="0"

  # 2. last exit code
  exit_code=$(echo "$detail" | grep -E "^\s*last exit code = " | head -1 | sed 's/.*last exit code = //' | tr -d ' ')
  [[ -z "$exit_code" || "$exit_code" == "(never"* ]] && exit_code="never"

  # 3. 日志路径和新鲜度
  stdout_path=$(echo "$detail" | grep -E "^\s*stdout path = " | head -1 | sed 's/.*stdout path = //' | tr -d ' ')
  stale_flag=""
  # 检查是否是常驻服务（KeepAlive=true）——常驻服务不判断日志陈旧（常驻服务日志不频繁写入是正常行为）
  is_keepalive=0
  plist="$HOME/Library/LaunchAgents/${label}.plist"
  if [[ -f "$plist" ]]; then
    keepalive=$(/usr/libexec/PlistBuddy -c "Print :KeepAlive" "$plist" 2>/dev/null || echo "false")
    [[ "$keepalive" == "true" ]] && is_keepalive=1
  fi
  if [[ $is_keepalive -eq 1 ]]; then
    stale_flag=""  # 常驻服务跳过日志陈旧判断（v1.1.0优化·2026-09-03·童灵愿景裁决：常驻服务state=running即健康，日志陈旧是正常行为）
  elif [[ -n "$stdout_path" && -f "$stdout_path" ]]; then
    # 获取plist中的StartInterval（秒）
    interval=86400  # 默认每天
    if [[ -f "$plist" ]]; then
      interval=$(/usr/libexec/PlistBuddy -c "Print :StartInterval" "$plist" 2>/dev/null || echo 86400)
    fi
    # 日志最后修改时间距现在的秒数
    if [[ $(uname) == "Darwin" ]]; then
      file_mtime=$(stat -f "%m" "$stdout_path" 2>/dev/null || echo 0)
    else
      file_mtime=$(stat -c "%Y" "$stdout_path" 2>/dev/null || echo 0)
    fi
    now=$(date +%s)
    age=$((now - file_mtime))
    # 超过2个interval没更新=可能死了（容忍1个interval的延迟）
    threshold=$((interval * 2))
    if [[ $age -gt $threshold && $runs -gt 0 ]]; then
      # v1.1.0优化·2026-09-03：如果StandardOutPath为空或0字节（脚本内部自己重定向了输出），
      # 检查同目录下是否有最近24小时内修改的last_run*.ts文件，有则说明任务在正常运行，不标记为日志陈旧
      if [[ ! -s "$stdout_path" ]]; then
        last_run_file=$(find "$(dirname "$stdout_path")" -name "last_run*.ts" -mtime -1 2>/dev/null | head -1)
        if [[ -n "$last_run_file" ]]; then
          stale_flag=""  # 有最近的last_run文件，任务在正常运行（脚本内部重定向了输出，launchd的stdout为空是正常的）
        else
          # 没有last_run文件，才标记为日志陈旧
          if [[ $age -ge 86400 ]]; then
            age_display="$((age/86400))天"
          elif [[ $age -ge 3600 ]]; then
            age_display="$((age/3600))小时"
          else
            age_display="${age}秒"
          fi
          if [[ $interval -ge 86400 ]]; then
            int_display="每$((interval/86400))天"
          elif [[ $interval -ge 3600 ]]; then
            int_display="每$((interval/3600))小时"
          else
            int_display="每${interval}秒"
          fi
          stale_flag="⚠️日志陈旧(${age_display}前更新,预期${int_display},stdout为空且无last_run)"
        fi
      else
        # stdout非空，正常的日志陈旧判断
        if [[ $age -ge 86400 ]]; then
          age_display="$((age/86400))天"
        elif [[ $age -ge 3600 ]]; then
          age_display="$((age/3600))小时"
        else
          age_display="${age}秒"
        fi
        if [[ $interval -ge 86400 ]]; then
          int_display="每$((interval/86400))天"
        elif [[ $interval -ge 3600 ]]; then
          int_display="每$((interval/3600))小时"
        else
          int_display="每${interval}秒"
        fi
        stale_flag="⚠️日志陈旧(${age_display}前更新,预期${int_display})"
      fi
    fi
  fi

  # 判定
  if [[ "$runs" == "0" ]]; then
    dead=$((dead + 1))
    dead_list+=("$label | runs=0 (死形态·从未触发)")
    [[ $SUMMARY_ONLY -eq 0 ]] && echo "  🔴 $label: 死形态 (runs=0·从未触发)"
  elif [[ "$exit_code" != "0" && "$exit_code" != "never" ]]; then
    error=$((error + 1))
    error_list+=("$label | exit_code=$exit_code")
    [[ $SUMMARY_ONLY -eq 0 ]] && echo "  🟠 $label: 异常 (last exit=$exit_code)"
  elif [[ -n "$stale_flag" ]]; then
    stale=$((stale + 1))
    stale_list+=("$label | $stale_flag")
    [[ $SUMMARY_ONLY -eq 0 ]] && echo "  🟡 $label: $stale_flag"
  else
    healthy=$((healthy + 1))
    [[ $SUMMARY_ONLY -eq 0 ]] && echo "  ✅ $label: 健康 (runs=$runs, exit=0)"
  fi
done <<< "$tasks"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 巡检摘要：共 $task_count 个任务"
echo "   ✅ 健康: $healthy | 🔴 死形态: $dead | 🟠 异常: $error | 🟡 日志陈旧: $stale"

# ── 附加检查：README scripts 索引一致性（P0-2兜底层·C-085双本账漂移防护）──
echo ""
echo "🔍 附加检查：README scripts 索引一致性"
sync_script="[记忆共享中心]/数字分身/scripts/sync_readme_scripts_index.py"
if [[ -f "$sync_script" ]]; then
  if /usr/bin/python3 "$sync_script" --check >/dev/null 2>&1; then
    echo "   ✅ README scripts 索引与实际目录一致（双本账零漂移）"
  else
    check_exit=$?
    if [[ $check_exit -eq 1 ]]; then
      echo "   ⚠️  README scripts 索引过时（WatchPaths可能未触发或失败）→ 自动同步中..."
      /usr/bin/python3 "$sync_script" >/dev/null 2>&1 && echo "   ✅ 已自动同步" || echo "   🔴 自动同步失败，请手动运行: python3 $sync_script"
    else
      echo "   🔴 索引检查失败（exit=${check_exit}，可能标记缺失或脚本错误）"
    fi
  fi
else
  echo "   ⚠️  同步脚本不存在: ${sync_script}（跳过检查）"
fi

# ── 附加检查：多端状态同步（P1-3·童灵多端状态总线·全量内容hash比对）──
echo ""
echo "🔍 附加检查：多端状态同步"
state_bus_script="[记忆共享中心]/数字分身/scripts/state_bus_sync.py"
if [[ -f "$state_bus_script" ]]; then
  if /usr/bin/python3 "$state_bus_script" --summary >/dev/null 2>&1; then
    echo "   ✅ 多端状态全部同步（8端已接入·SSOT驱动·端清单=06-跨端适配规范.md §2.2.0）"
  else
    sb_exit=$?
    if [[ $sb_exit -eq 1 ]]; then
      echo "   ⚠️  有端状态不同步 → 运行 'python3 $state_bus_script' 查看详情"
    else
      echo "   🔴 状态同步检查失败（exit=${sb_exit}，可能state_bus.json缺失或格式错误）"
    fi
  fi
else
  echo "   ⚠️  状态同步脚本不存在: ${state_bus_script}（跳过检查）"
fi

if [[ $dead -gt 0 || $error -gt 0 ]]; then
  echo ""
  echo "🚨 异常任务清单："
  for item in "${dead_list[@]}"; do echo "   🔴 $item"; done
  for item in "${error_list[@]}"; do echo "   🟠 $item"; done
  for item in "${stale_list[@]}"; do echo "   🟡 $item"; done
  echo ""
  echo "💡 修复建议：死形态任务执行 'launchctl kickstart -k gui/$(id -u)/<label>' 手动触发一次，验证 exit=0 后 StartInterval 将自动计时。"
  if [[ $STRICT -eq 1 ]]; then
    exit 1
  fi
else
  echo "   ✅ 全部健康"
fi

exit 0
