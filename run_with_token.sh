#!/bin/bash
# ============================================================
# run_with_token.sh —— 带令牌的命令执行包装器
# ============================================================
# 起源：system-logger Skill v3.13.0 的🔖流程完成令牌机制
# 2026-09-03 童灵评估后扩大化为通用脚本验证机制
# 设计哲学：《布洛陀脚本架构设计通用规范》§二·十
#
# 本质：用物理锚定的证据（🔖令牌）代替AI的自觉声明
# 四要素：物理锚定 + 必须relay + 无法伪造 + 可追溯
#
# 用法：
#   bash run_with_token.sh <动作名> <命令...>
#   bash run_with_token.sh "数据生成" python3 evolution_deviation.py
#   bash run_with_token.sh "面板渲染" python3 panel_snapshot.py
#
# 输出：
#   命令的原始输出
#   命令执行完成后输出 🔖 令牌：{8位十六进制}
#   （令牌同时写入执行日志 token_log_YYYY-MM.jsonl）
#
# 边界声明：
#   令牌验证"做了没做"，不验证"做得好不好"——与质量验证正交分工。
# ============================================================

set -euo pipefail

# 检查参数
if [ $# -lt 2 ]; then
    echo "用法：bash run_with_token.sh <动作名> <命令...>"
    echo "示例：bash run_with_token.sh \"数据生成\" python3 evolution_deviation.py"
    exit 1
fi

ACTION_NAME="$1"
shift

# 令牌生成器路径
TOKEN_GENERATOR="[记忆共享中心]/脚本中心/token_generator.py"

# 执行命令（捕获exit code，但不立即退出）
set +e
"$@"
EXIT_CODE=$?
set -e

# 命令执行完成后生成令牌（物理锚定·只有真正执行了才生成）
if [ -f "$TOKEN_GENERATOR" ]; then
    DETAIL="命令: $* | exit_code: $EXIT_CODE"
    TOKEN_OUTPUT=$(python3 "$TOKEN_GENERATOR" --action "$ACTION_NAME" --detail "$DETAIL" 2>/dev/null || true)
    # 提取令牌行
    TOKEN_LINE=$(echo "$TOKEN_OUTPUT" | grep "^🔖 令牌：" || true)
    if [ -n "$TOKEN_LINE" ]; then
        echo ""
        echo "$TOKEN_LINE"
        echo "（AI必须在回复中relay此令牌作为'已执行'的证据）"
    fi
else
    echo ""
    echo "⚠️ 令牌生成器未找到：$TOKEN_GENERATOR"
fi

# 传递原始命令的exit code
exit $EXIT_CODE
