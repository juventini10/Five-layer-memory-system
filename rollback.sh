#!/bin/bash
# rollback.sh — 布洛陀 1.10 · 系统文件回滚脚本
#
# 用途：从记忆琥珀备份中恢复系统核心文件（SOUL/IDENTITY/USER/MEMORY）
# 使用场景：更新后发现不兼容或数据异常，一键回滚到升级前的状态
#
# 用法：
#   ./rollback.sh                          # 列出可用备份
#   ./rollback.sh --preview                # 预览最近一次备份的文件差异
#   ./rollback.sh --restore                # 恢复最近一次备份
#   ./rollback.sh --restore=2026-06-27_12  # 恢复指定时间戳的备份
#
# ⚠️ 隐私安全：
#   [记忆共享中心] — 用户实际路径，不随包分发，由用户运行前设置
#   export MEMORY_CENTER=/path/to/your/memory  # 设置后运行
# ============================================================

set -euo pipefail

# ── 配置 ──────────────────────────────────────────────
MEMORY_CENTER="${MEMORY_CENTER:-}"
BACKUP_DIR="$MEMORY_CENTER/记忆琥珀"
CORE_FILES=("SOUL.md" "IDENTITY.md" "USER.md" "MEMORY.md")

# ── 帮助 ──────────────────────────────────────────────
usage() {
    echo "📋 布洛陀 1.10 · 系统文件回滚工具"
    echo ""
    echo "用法:"
    echo "  ./rollback.sh                          # 列出可用备份"
    echo "  ./rollback.sh --preview                # 预览最近一次备份"
    echo "  ./rollback.sh --restore                # 恢复最近一次备份"
    echo "  ./rollback.sh --restore=YYYY-MM-DD_HH  # 恢复指定时间戳备份"
    echo ""
    echo "环境变量:"
    echo "  export MEMORY_CENTER=/path/to/your/memory"
    echo "  或运行前手动设置路径"
    echo ""
    exit 0
}

[ $# -eq 0 ] && { usage; exit 0; }

# ── 路径检查 ──────────────────────────────────────────
check_path() {
    if [ -z "$MEMORY_CENTER" ]; then
        echo "❌ 未设置 MEMORY_CENTER"
        echo "   运行前设置：export MEMORY_CENTER=/path/to/your/memory"
        echo "   或：MEMORY_CENTER=/path ./rollback.sh --restore"
        exit 1
    fi
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "❌ 备份目录不存在：$BACKUP_DIR"
        echo "   你还没有运行过升级备份，或者记忆共享中心路径不对"
        exit 1
    fi
}

# ── 列出备份 ──────────────────────────────────────────
list_backups() {
    check_path
    echo "📦 可用备份："
    echo ""
    local count=0
    for dir in "$BACKUP_DIR"/升级备份_*; do
        if [ -d "$dir" ]; then
            local ts="${dir##*升级备份_}"
            local files=0
            for f in "${CORE_FILES[@]}"; do
                [ -f "$dir/$f.bak" ] && files=$((files+1))
            done
            echo "  🕐 $ts  →  $files/4 个系统文件已备份"
            count=$((count+1))
        fi
    done
    [ $count -eq 0 ] && echo "  (无备份记录)"
}

# ── 预览差异 ──────────────────────────────────────────
preview_diff() {
    check_path
    local ts="${1:-}"
    local restore_dir=""

    if [ -n "$ts" ]; then
        restore_dir="$BACKUP_DIR/升级备份_$ts"
    else
        restore_dir=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "升级备份_*" | sort -r | head -1)
    fi

    if [ ! -d "$restore_dir" ]; then
        echo "❌ 备份不存在：$restore_dir"
        list_backups
        exit 1
    fi

    local resolved_ts="${restore_dir##*升级备份_}"
    echo "🔍 预览备份：$resolved_ts"
    echo ""
    for file in "${CORE_FILES[@]}"; do
        local bak="$restore_dir/$file.bak"
        local current="$HOME/.workbuddy/$file"
        if [ -f "$bak" ] && [ -f "$current" ]; then
            echo "─── $file ───"
            diff --brief "$bak" "$current" 2>/dev/null || true
            echo ""
        elif [ -f "$bak" ] && [ ! -f "$current" ]; then
            echo "⚠️  $file：备份存在但当前文件不存在（可能已删除）"
            echo ""
        else
            echo "⚠️  $file：备份不存在"
            echo ""
        fi
    done
}

# ── 执行恢复 ──────────────────────────────────────────
do_restore() {
    check_path
    local ts="${1:-}"
    local restore_dir=""

    if [ -n "$ts" ]; then
        restore_dir="$BACKUP_DIR/升级备份_$ts"
    else
        restore_dir=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "升级备份_*" | sort -r | head -1)
    fi

    if [ ! -d "$restore_dir" ]; then
        echo "❌ 备份不存在：$restore_dir"
        list_backups
        exit 1
    fi

    local resolved_ts="${restore_dir##*升级备份_}"
    echo "🔄 正在回滚到备份：$resolved_ts"
    echo ""

    local ok=0 fail=0
    for file in "${CORE_FILES[@]}"; do
        local bak="$restore_dir/$file.bak"
        local target="$HOME/.workbuddy/$file"
        if [ -f "$bak" ]; then
            # 先备份当前文件（以防回滚后不满意）
            local current_bak="$BACKUP_DIR/回滚前_${ts}_${file}"
            [ -f "$target" ] && cp "$target" "$current_bak" || true
            # 恢复备份
            cp "$bak" "$target"
            echo "  ✅ $file → 已恢复（当前版本已备份到 回滚前_${ts}_${file}）"
            ok=$((ok+1))
        else
            echo "  ⚠️  $file → 备份文件不存在，跳过"
            fail=$((fail+1))
        fi
    done

    echo ""
    echo "─────────────────────────────"
    echo "✅ 回滚完成：$ok/4 个文件已恢复，$fail 个跳过"
    if [ $fail -gt 0 ]; then
        echo "⚠️ 部分文件未恢复，可能不完整"
    else
        echo "🎉 你的系统文件已回滚到升级前的状态"
    fi
    echo ""
    echo "💡 运行后建议：说'我美吗'重新唤醒记忆系统"
}

# ── 入口 ──────────────────────────────────────────────
case "${1:-}" in
    --preview)
        preview_diff "${2:-}"
        ;;
    --restore=*)
        ts="${1#*=}"
        do_restore "$ts"
        ;;
    --restore)
        do_restore "${2:-}"
        ;;
    --list|--help|-h)
        list_backups
        ;;
    *)
        usage
        ;;
esac
