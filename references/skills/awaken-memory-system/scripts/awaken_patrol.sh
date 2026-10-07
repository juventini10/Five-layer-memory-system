#!/bin/bash
# awaken_patrol.sh — 记忆健康自动巡检（awaken-memory-system 8.0 阶段③·主动泵）
# 规格锚点：references/patrol.md §3 · 升级方案 awaken-memory-system-8.0升级.md 阶段③
#          · T0 调查（S708 容忍度函数 / PLOS 轻量周期优于频密打扰 / Fogg B=MAP 补 P）
# 载体：launchd StartInterval（每6小时·试跑校准·plist: com.buluotuo.awaken-patrol）
# 职责：①快照滞后检查（复用 update_snapshot_from_diary.py·exit 语义见 patrol.md §1）
#       ②蒸馏待办三级阈值检测（复用 patrol.md §2 逻辑·awaken_distill_due_check.py）
#       ③触达：有逾期（🟡/🔴）或快照缺口才 osascript 弹窗·无事不打扰（只提醒不写入）
# 纪律：⛔不写他者文件（不替任何 Skill 写文件；自有快照经 update_snapshot_from_diary.py 属职责内·v8.1.2审查A14消歧）·失败显形（假绿防线）·可观测（巡检日志）
#       ·可收回（plist 卸载即停）·自主≠黑箱（可观测/可抽检）

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AWAKEN_HOME="[记忆共享中心]/技能配置/awaken-memory-system"
LOG_DIR="$HOME/buluotuo_bin/log"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/awaken_patrol.log"
NOW="$(date '+%Y-%m-%d %H:%M:%S')"
DUE_CENTER="${DISTILL_CENTER_PATH:-}"

log() { printf '%s %s\n' "$NOW" "$*" >> "$LOG_FILE"; }

ALERTS=""
SNAP_STATE="skip"

# ── ① 快照滞后检查（复用现成脚本·⛔不复制逻辑·SSOT 在 patrol.md §1）──
SNAP_SCRIPT="$AWAKEN_HOME/scripts/update_snapshot_from_diary.py"
if [ ! -f "$SNAP_SCRIPT" ]; then
  SNAP_STATE="missing"
  log "[快照] 脚本缺失: $SNAP_SCRIPT"
  ALERTS="${ALERTS}【快照缺口】update_snapshot_from_diary.py 缺失\n"
else
  env -u PYTHONHOME -u PYTHONPATH python3 "$SNAP_SCRIPT" >> "$LOG_FILE" 2>&1
  rc=$?
  case "$rc" in
    0) SNAP_STATE="updated"; log "[快照] 已更新（exit 0）" ;;
    2) SNAP_STATE="uptodate"; log "[快照] 无需更新（exit 2）" ;;
    *) SNAP_STATE="fail"; log "[快照] 更新失败（exit ${rc}）→ 数据可能滞后"
       ALERTS="${ALERTS}【快照缺口】快照更新失败(exit $rc)，数据可能滞后\n" ;;
  esac
fi

# ── ② 蒸馏待办三级阈值检测（patrol.md §2 逻辑·脚本化）──
DUE_OUT="$(env -u PYTHONHOME -u PYTHONPATH python3 "$SCRIPT_DIR/awaken_distill_due_check.py" ${DUE_CENTER:+"$DUE_CENTER"} 2>>"$LOG_FILE")"
if [ $? -ne 0 ]; then
  log "[蒸馏] 检测失败（脚本非零退出）"
  ALERTS="${ALERTS}【巡检异常】蒸馏待办检测失败\n"
else
  if [ "$DUE_OUT" = "NONE" ]; then
    log "[蒸馏] 无待办（静默）"
  else
    # 触达阈值：仅 🟡/🔴 弹窗；🔵 即将到期仅入日志（无事不打扰·防打扰校准）
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      case "$line" in
        *"🔴"*) ALERTS="${ALERTS}${line#DUE|}\n"; log "[蒸馏] $line" ;;
        *"🟡"*) ALERTS="${ALERTS}${line#DUE|}\n"; log "[蒸馏] $line" ;;
        *) log "[蒸馏] $line" ;;
      esac
    done <<< "$DUE_OUT"
  fi
fi

# ── ③ 触达层：有逾期/缺口才弹·无事不打扰（Fogg 补 P·只提醒不写入）──
# B-1（设计哲学 §9.5·2026-09-17）：弹窗文案追加"输入『小美』看详情"——巡检=机制层（补 P 提示入口），小美=对话层（详情面板）·巡检→对话联动闭环
# D-3（设计哲学 §9.5·2026-09-17）：弹窗顶部加仪表盘单行摘要（awaken_health_dashboard.py --summary·与完整仪表盘同源·三处可见入口①·脚本缺失/失败降级=弹窗不含摘要不阻塞）
if [ -n "$ALERTS" ]; then
  DASH_SCRIPT="$SCRIPT_DIR/awaken_health_dashboard.py"
  dash_sum=""
  if [ -f "$DASH_SCRIPT" ]; then
    dash_sum="$(env -u PYTHONHOME -u PYTHONPATH python3 "$DASH_SCRIPT" --summary 2>>"$LOG_FILE")"
  fi
  msg="$(printf '%b' "$ALERTS" | sed 's/\\n$//')"
  if [ -n "$dash_sum" ]; then
    msg="${dash_sum}

${msg}

输入『小美』看详情"
  else
    msg="${msg}

输入『小美』看详情"
  fi
  osascript -e "display notification \"$msg\" with title \"布洛陀·记忆巡检\"" >> "$LOG_FILE" 2>&1
  log "[触达] 已弹通知（$(printf '%b' "$ALERTS" | tr '\n' ' ')）·含小美入口"
else
  log "[触达] 无事不打扰（静默）"
fi

log "[完成] 巡检结束（快照=${SNAP_STATE}）"
exit 0
