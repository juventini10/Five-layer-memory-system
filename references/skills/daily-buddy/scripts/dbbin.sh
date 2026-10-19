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
# PYTHON 跨平台根治（2026-10-13）：原兜底写死 /usr/local/bin/python3 仅 Intel Mac
# 命中（Apple Silicon Homebrew 在 /opt/homebrew·Windows Git Bash 无 Unix 路径），
# 改为运行期解析链——command -v 命中优先·兜底列表覆盖 Linux/ARM/Homebrew 常见位·
# 最终 py launcher（Windows 官方入口）。与 dbenv.py 解析链对齐（沙箱防线不变）。
#
# PYTHONHOME/PYTHONPATH 污染自愈（2026-09-11 收口·硬路牌 shell 层处理）：
# Trae Work 等宿主 shell 注入 PYTHONHOME（自带 Python）/PYTHONPATH，会在解释器
# 初始化阶段报 "No module named 'encodings'"（init_fs_encoding·污染发生在 Python
# 启动前，代码内清理无效）。统一调用器 = 唯一安全入口 → 本文件显式 -u 清理，
# AI 无需记得加前缀（愿景①机制代意志·不依赖人记得）。
#
# 用法：
#   bash [记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh create_skeleton.py --date 2026-08-20
#   bash [记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh finalize_diary.py --date 2026-08-20
#   bash [记忆共享中心]/技能配置/daily-buddy/scripts/dbbin.sh update_diary_achievement.py --date 2026-08-20
#
# 配套：每个日常-buddy .py 内部 import dbenv（路径/内部子进程自愈），双保险。
set -euo pipefail

REAL_HOME="${DB_HOME:-~}"
# 运行期 python 解析（跨平台·2026-10-13 根治）：显式 > PATH 命中 > 平台常见位 > py
REAL_PY="${DB_PYTHON:-}"
if [ -z "$REAL_PY" ]; then
  REAL_PY="$(command -v python3 2>/dev/null || true)"
  [ -z "$REAL_PY" ] && REAL_PY="$(command -v python 2>/dev/null || true)"
  if [ -z "$REAL_PY" ]; then
    for _cand in /usr/local/bin/python3 /usr/bin/python3 /opt/homebrew/bin/python3; do
      [ -x "$_cand" ] && REAL_PY="$_cand" && break
    done
  fi
  [ -z "$REAL_PY" ] && REAL_PY="$(command -v py 2>/dev/null || true)"  # Windows Python launcher 官方入口
  if [ -z "$REAL_PY" ]; then
    echo "❌ 找不到 python 解释器（PATH/常见位/py 均未命中）——请装 Python 3 或设 DB_PYTHON" >&2
    exit 1
  fi
fi
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
