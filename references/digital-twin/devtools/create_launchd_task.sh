#!/usr/bin/env bash
#
# create_launchd_task.sh — launchd任务创建封装（L1机械封装·创建即验证）
# Version: 1.0.0 (2026-09-02)
#
# 职责（单一）：创建launchd plist + 自动load + kickstart首次运行 + 验证exit=0+日志非空。
# 设计原则（S014"自觉是安慰剂，机械是药" + 铁律-021"终检靠脚本不靠自觉"）：
#   - 创建≠运行：创建后必须自动kickstart验证，不通过则创建失败
#   - 机械强制：不依赖AI/人"记得去验证"，脚本封装了验证步骤
#   - 失败回滚：验证不通过时提示问题，不静默成功
#   - 幂等：已存在的任务先unload再重建（避免旧配置残留）
#
# 用法：
#   create_launchd_task.sh <label> <script_path> <interval_seconds> [log_path]
#
# 示例：
#   create_launchd_task.sh com.buluotuo.my-task /path/to/script.py 86400 /path/to/log.log
#
# 参数：
#   label            — launchd任务标签（如 com.buluotuo.my-task）
#   script_path      — 要执行的脚本绝对路径
#   interval_seconds — 运行间隔（秒），如 86400=每天, 21600=每6小时
#   log_path         — （可选）日志文件路径，默认 [记忆共享中心]/数字分身/scripts/<label>.log
#
set -eo pipefail

# ── 参数校验 ──────────────────────────────────────────────
if [[ $# -lt 3 ]]; then
  echo "❌ 用法: create_launchd_task.sh <label> <script_path> <interval_seconds> [log_path]"
  echo "   示例: create_launchd_task.sh com.buluotuo.demo /path/script.py 86400"
  exit 1
fi

LABEL="$1"
SCRIPT_PATH="$2"
INTERVAL="$3"
LOG_PATH="${4:-[记忆共享中心]/数字分身/scripts/${LABEL}.log}"
ERR_LOG="${LOG_PATH%.log}_err.log"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"

# 校验脚本存在且可执行
if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "❌ 脚本不存在: $SCRIPT_PATH"
  exit 1
fi

# 校验interval是正整数
if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -lt 1 ]]; then
  echo "❌ interval必须是正整数（秒）: $INTERVAL"
  exit 1
fi

# 确定python3路径（优先用env python3，兼容不同环境）
PYTHON_PATH=$(which python3 || echo "/usr/local/bin/python3")

echo "🔧 创建 launchd 任务: $LABEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  脚本: $SCRIPT_PATH"
echo "  间隔: ${INTERVAL}秒 ($((INTERVAL/3600))小时)"
echo "  日志: $LOG_PATH"
echo "  plist: $PLIST"
echo ""

# ── 步骤1：如果已存在，先unload（幂等） ──────────────────
if [[ -f "$PLIST" ]]; then
  echo "  🔄 发现已存在的plist，先unload..."
  launchctl unload "$PLIST" 2>/dev/null || true
  echo "  ✅ 已unload旧任务"
fi

# ── 步骤2：创建plist ─────────────────────────────────────
echo "  📝 创建plist..."
mkdir -p "$(dirname "$LOG_PATH")"
touch "$LOG_PATH" "$ERR_LOG"

cat > "$PLIST" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>${SCRIPT_PATH}</string>
    </array>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>StandardOutPath</key>
    <string>${LOG_PATH}</string>
    <key>StandardErrorPath</key>
    <string>${ERR_LOG}</string>
</dict>
</plist>
PLIST_EOF

echo "  ✅ plist已创建"

# ── 步骤3：load ───────────────────────────────────────────
echo "  📥 load任务..."
launchctl load "$PLIST" 2>&1
echo "  ✅ 已load"

# ── 步骤4：kickstart首次运行 ──────────────────────────────
echo "  🚀 kickstart首次运行..."
launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>&1
echo "  ✅ 已kickstart"

# ── 步骤5：等待并验证 ─────────────────────────────────────
echo "  ⏳ 等待运行完成（最多15秒）..."
MAX_WAIT=15
waited=0
while [[ $waited -lt $MAX_WAIT ]]; do
  sleep 1
  waited=$((waited + 1))
  # 检查任务是否还在运行
  state=$(launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -E "^\s*state = " | head -1 | sed 's/.*state = //' | tr -d ' ')
  if [[ "$state" != "running" ]]; then
    break
  fi
done

# 获取运行结果
detail=$(launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null || true)
runs=$(echo "$detail" | grep -E "^\s*runs = " | head -1 | sed 's/.*runs = //' | tr -d ' ')
exit_code=$(echo "$detail" | grep -E "^\s*last exit code = " | head -1 | sed 's/.*last exit code = //' | tr -d ' ')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 验证结果："
echo "   runs: $runs"
echo "   last exit code: $exit_code"

# 检查日志非空
log_size=$(stat -f%z "$LOG_PATH" 2>/dev/null || echo 0)
echo "   stdout日志大小: ${log_size}字节"

# ── 步骤6：判定 ───────────────────────────────────────────
if [[ "$runs" == "0" ]]; then
  echo ""
  echo "❌ 创建失败：任务从未运行（runs=0）"
  echo "   可能原因：plist格式错误 / 脚本路径错误 / 权限问题"
  echo "   排查命令：launchctl print gui/$(id -u)/$LABEL"
  exit 1
elif [[ "$exit_code" != "0" ]]; then
  echo ""
  echo "❌ 创建失败：首次运行异常（exit code=${exit_code}）"
  echo "   错误日志：$ERR_LOG"
  echo "   最后10行错误："
  tail -10 "$ERR_LOG" 2>/dev/null || true
  exit 1
elif [[ "$log_size" -eq 0 ]]; then
  echo ""
  echo "⚠️  警告：任务运行成功但stdout日志为空（exit=0但无输出）"
  echo "   如果脚本设计为静默运行（无变更时无输出），这是正常的。"
  echo "   否则请检查脚本是否有print输出。"
  echo ""
  echo "✅ 创建成功（exit=0，runs=${runs}）"
else
  echo ""
  echo "✅ 创建成功！"
  echo "   任务已验证运行（runs=$runs, exit=0, 日志非空）"
  echo "   StartInterval=${INTERVAL}秒，将自动定期运行。"
fi

echo ""
echo "📌 后续巡检：launchd_health_check.sh 会自动检查此任务的健康度。"
exit 0
