#!/bin/bash
# 成就达成通知脚本
# 用法：./achievement_notify.sh "成就名称" "描述" "音效（可选）"
# 示例：./achievement_notify.sh "番茄新星" "累计番茄突破100🍅！" "Glass"

TITLE="${1:-🏆 成就达成}"
MESSAGE="${2:-恭喜达成新成就！}"
SOUND="${3:-Glass}"

osascript -e "display notification \"$MESSAGE\" with title \"🏆 成就达成：$TITLE\" subtitle \"$(date '+%Y-%m-%d') 里程碑\" sound name \"$SOUND\""

echo "✅ 通知已发送：$TITLE"
