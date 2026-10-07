#!/usr/bin/env bash
# reuse_check.sh —— 落手写新守卫/脚本前·必跑的「同类件先查」闸
#
# 病根（2026-10-03·Hermes 端当日第四笔同族错 HE-20261003-009）：
#   依据哲学 04 §二·七·〇 记载（「本端不查注入链」）起手写 hermes_inject_chain_guard.py，
#   落盘前被 stale_write 门卫拦下才发现 **该文件 2026-10-02 已存在（245 行·RED0/WARN0）**。
#   ⇒ 15 分钟白写 + 方案里挂了一条**假缺口**。
#
# 根因不是「忘了查」，是**查这一步没有物理位置**——
# 哲学把它写成「动作 3」（一条建议），我可以在任何时刻跳过它而不会有任何反馈。
#
# ⇒ 本脚本把「查」做成**可执行的前置**：新起文件名 → 跑它 → 有同类就停。
#
# 用法：
#   ./reuse_check.sh hermes_inject_chain_guard.py
#   ./reuse_check.sh --all                      # 扫全端已登记守卫清单对照
set -uo pipefail

DEV="${BULUOTUO_DEVTOOLS:-[记忆共享中心]/脚本中心}"
RED=0

if [ "${1:-}" = "--all" ]; then
    echo "=== 开发工具/ 下含 guard/check/audit 的件 ==="
    ls -1 "$DEV" 2>/dev/null | grep -E 'guard|check|audit' || echo "(无)"
    exit 0
fi

TARGET="${1:-}"
[ -z "$TARGET" ] && { echo "用法: $0 <新文件名> | $0 --all" >&2; exit 2; }

echo "=== 落手前同类件核查：$TARGET ==="

# ① 本端脚本中心/开发工具 下是否已有同名或同类件
echo "--- ① 同名件 ---"
SAME=$(find ""/脚本中心" ""/脚本中心" \
       -maxdepth 2 -name "$TARGET" 2>/dev/null)
if [ -n "$SAME" ]; then
    echo "  🔴 已存在同名件："
    printf '%s\n' "$SAME" | sed 's/^/     /'
    RED=1
else
    echo "  ✅ 无同名件"
fi

# ② 词干类���件（如 xxx_guard → 找 *_guard.py 全族）
STEM="${TARGET%.py}"
STEM="${STEM##*/}"
STEM="${STEM%_guard}"; STEM="${STEM%_check}"; STEM="${STEM%_audit}"
echo "--- ② 同族件（词干=${STEM}）---"
KIN=$(find ""/脚本中心" -maxdepth 2 \
      \( -name "*${STEM}*guard*" -o -name "*${STEM}*check*" -o -name "*${STEM}*audit*" \) \
      2>/dev/null | head -10)
if [ -n "$KIN" ]; then
    echo "  🟡 存在同族件（**逐个读后再决定扩它还是另起**）："
    printf '%s\n' "$KIN" | sed 's/^/     /'
    echo "     ⛔ 哲学 04 §二·七·〇 动作3：能对齐先例就不自建（复制=双本账漂移）"
else
    echo "  ✅ 无同族件"
fi

# ③ 端专属插件目录下的既有守卫插件
echo "--- ③ 本端守卫插件（plugins/*guard*）---"
PLUG=$(ls -1 "$HOME/.hermes/plugins" 2>/dev/null | grep -E 'guard|readonly' || true)
if [ -n "$PLUG" ]; then
    echo "  ℹ️  既有守卫插件（职责可能已覆盖）："
    printf '     %s\n' $PLUG
else
    echo "  ✅ 无"
fi

echo "--- ④ 本端实跑既有守卫（看是否已绿）---"
for g in hermes_inject_chain_guard hermes_plugin_health_guard; do
    [ -f "$DEV/$g.py" ] || continue
    if python3 "$DEV/$g.py" >/dev/null 2>&1; then
        echo "  ✅ $g.py 可跑（rc=0）"
    else
        echo "  🟡 $g.py 非零退出（其自报判据见直接运行）"
    fi
done

echo
if [ "$RED" = "1" ]; then
    echo "🔴 已有同名件 → ⛔ 停止新写。先读它、试它，然后决定：扩它 / 改它 / 确属不同职责才另起。"
    exit 1
fi
echo "✅ 无同名冲突（同族件需人工判读·不是自动放行）。"
exit 0