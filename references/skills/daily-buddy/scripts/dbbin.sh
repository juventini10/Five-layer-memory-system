#!/usr/bin/env bash
# dbbin.sh — daily-buddy 脚本统一调用器（Hermes 沙箱环境根治·第一性原理）
#
# 作用：AI 调用 daily-buddy 脚本时只需 `bash dbbin.sh <script.py> [args...]`
#       本包装器强制：
#         1. HOME=<权威HOME>   （破除沙箱 HOME 劫持 /tmp/hb_sb/home）
#         2. 用真实 python3（破除沙箱 python3 假 no-op）
#         3. 真实 HOME 下跑，脚本内部 Path.home() 等自然落到正确路径
#
# 路径动态化（2026-09-11 收口·发布视角）：默认值保留本机真值（沙箱防线不变），
# 发布/其他机器用环境变量覆盖：DB_HOME=<用户主目录> DB_PYTHON=<真实python3>。
# dbenv.py 同律读取（DB_HOME > 默认），两处单一口径。
#
# PYTHONHOME/PYTHONPATH 污染自愈（2026-09-11 收口·硬路牌 shell 层处理）：
# Trae Work 等宿主 shell 注入 PYTHONHOME（自带 Python）/PYTHONPATH，会在解释器
# 初始化阶段报 "No module named 'encodings'"（init_fs_encoding·污染发生在 Python
# 启动前，代码内清理无效）。统一调用器 = 唯一安全入口 → 本文件显式 -u 清理，
# AI 无需记得加前缀（愿景①机制代意志·不依赖人记得）。
#
# 用法：
#   bash ~/[记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh create_skeleton.py --date 2026-08-20
#   bash ~/[记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh finalize_diary.py --date 2026-08-20
#   bash ~/[记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh update_diary_achievement.py --date 2026-08-20
#
# 配套：每个日常-buddy .py 内部 import dbenv（路径/内部子进程自愈），双保险。
set -euo pipefail

REAL_HOME="${DB_HOME:-~}"
REAL_PY="${DB_PYTHON:-/usr/local/bin/python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -lt 1 ]]; then
  echo "用法: bash dbbin.sh <script.py> [args...]" >&2
  exit 1
fi

SCRIPT="$1"; shift
# 支持相对脚本名（相对 scripts 目录）
if [[ ! "$SCRIPT" == /* ]]; then
  SCRIPT="$SCRIPT_DIR/$SCRIPT"
fi

if [[ ! -f "$SCRIPT" ]]; then
  echo "❌ 脚本不存在: $SCRIPT" >&2
  exit 1
fi

exec env -u PYTHONHOME -u PYTHONPATH HOME="$REAL_HOME" DB_HOME="$REAL_HOME" DB_PYTHON="$REAL_PY" "$REAL_PY" "$SCRIPT" "$@"
