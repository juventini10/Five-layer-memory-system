#!/bin/bash
# awaken_patrol.sh — 薄壳：转发 awaken_patrol.py（8.4.0 执行体已迁平台中立 py·单一真源⛔逻辑驻留本壳）
# 保留仅为兼容既有载体（作者机旧 plist ProgramArguments 指本文件）；
# 新载体（com.buluotuo.awaken-patrol.plist.template / Task Scheduler awaken-patrol-install-task.ps1）直指 py。
# 规格真源：references/patrol.md §3
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec env -u PYTHONHOME -u PYTHONPATH python3 "$SCRIPT_DIR/awaken_patrol.py" "$@"
