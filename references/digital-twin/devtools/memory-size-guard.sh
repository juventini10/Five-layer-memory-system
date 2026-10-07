#!/usr/bin/env bash
# memory-size-guard.sh v1.0 —— MEMORY.md 字符数守卫（changelog-guard 族·2026-08-28 皮叔定·升机械层）
# 协议: registry_guards.sh 跑 `bash $0 --check`(grep "alarm": true) + `bash $0 --report`
# 红线: MEMORY.md > 3800 字符 → alarm（平台注入硬上限 4000 chars/session, 留 200 缓冲）
# 依据: 皮叔"品格<脚本<机制兜底"实证立场 + 2026-08-28 实测(灌4705→原Stop守卫零报警→确认纯自觉软守卫)
# 零第三方依赖(bash+wc+awk)。接入: 置于 GUARD_DIR(changelog-guard/) + chmod +x → 每次 Stop 自动发现巡检。
# 注意: macOS bash 3.2 UTF-8 坑——中文/全角字符紧跟变量后必须用 ${var}, 否则多字节字符被误判进变量名(同 registry_guards.sh line9 警告).
set -uo pipefail
MEMORY="${WORKBUDDY_CONFIG_DIR:-$HOME/.workbuddy}/MEMORY.md"
LIMIT=3800
HARD=4000

size_of() {
  wc -m < "${MEMORY}" | awk '{print $1}'
}

mode="${1:---check}"

# 文件不存在 = 记忆系统故障, 必须报警(不静默)
if [ ! -f "${MEMORY}" ]; then
  if [ "${mode}" = "--report" ]; then
    echo "## MEMORY.md 文件丢失（预期路径 ${MEMORY}）"
    echo "> 文件不存在 = 记忆系统故障，须立即排查恢复。"
  else
    printf '{"file": "%s", "chars": -1, "limit": %d, "hard": %d, "alarm": true}\n' "${MEMORY}" "${LIMIT}" "${HARD}"
  fi
  exit 1
fi

case "${mode}" in
  --check)
    s=$(size_of)
    if [ "${s}" -gt "${LIMIT}" ]; then
      printf '{"file": "%s", "chars": %d, "limit": %d, "hard": %d, "alarm": true}\n' "${MEMORY}" "${s}" "${LIMIT}" "${HARD}"
      exit 1
    else
      printf '{"file": "%s", "chars": %d, "limit": %d, "hard": %d, "alarm": false}\n' "${MEMORY}" "${s}" "${LIMIT}" "${HARD}"
      exit 0
    fi
    ;;
  --report)
    s=$(size_of)
    if [ "${s}" -gt "${LIMIT}" ]; then
      echo "## MEMORY.md 字符数超限（当前 ${s} > 红线 ${LIMIT}，平台硬截断 ${HARD}）"
      echo ""
      echo "| 项 | 值 |"
      echo "|---|---|"
      echo "| 当前字符 | ${s} |"
      echo "| 软红线(报警) | ${LIMIT} |"
      echo "| 平台硬上限(截断) | ${HARD} |"
      echo "| 超出红线 | $((s - LIMIT)) |"
      echo ""
      echo "> 处置：须指针化——完整细则移归档 ~/[记忆共享中心]/记忆规则/MEMORY-完整细则归档.md 再写，⛔DO NOT 直接塞。"
      echo "> 机械报警已触发；修正动作(腾挪内容/指针化)须 AI 执行。"
    else
      echo "MEMORY.md ${s} 字符 ≤ 红线 ${LIMIT}（缓冲 $((HARD - s)) 至硬上限 ${HARD}），守卫通过"
    fi
    ;;
  *) echo "用法: memory-size-guard.sh [--check|--report]"; exit 2 ;;
esac
