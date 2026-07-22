#!/bin/bash
# 成就检测快捷脚本
# 用法：
#   ./check_achievements.sh          # 检测今日
#   ./check_achievements.sh --all    # 全量扫描
#   ./check_achievements.sh --status # 查看进度

# 相对自身定位脚本目录，重同步到安装包后仍可移植
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/achievement_tracker.py" "$@"
