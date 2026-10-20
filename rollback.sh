#!/bin/bash
# rollback.sh — 布洛陀 2.2.8 · 系统文件回滚工具（多端 · 增量宪法配套）
#
# 用途：把「用户已有文件」恢复到安装/升级**之前**的状态。
# 与断章增量引擎（宪法 §2.0 C1-C7）配套：⛔ 断章只保证"装的时候不覆盖"，
#    本脚本保证"万一判错了能一句话退回去"。
#
# 用法：
#   ./rollback.sh                          # 列出可用备份
#   ./rollback.sh --preview                # 预览最近一次备份的差异（⛔ 不写盘）
#   ./rollback.sh --restore                # 恢复最近一次备份
#   ./rollback.sh --restore=20261002_0720  # 恢复指定时间戳
#   ./rollback.sh --platform hermes        # 显式指定端（否则自动探测）
#
# 环境变量：
#   export MEMORY_CENTER=/path/to/your/memory   # 记忆共享中心
#
# ⚠️ 隐私安全：[记忆共享中心] 由用户运行时设置，不随包分发。
# ============================================================

set -uo pipefail   # ⚠️ 不用 -e：循环里单项失败要继续并如实计数，不能整体崩

# ── 配置 ─────────────────────────────────────────────────────────
MEMORY_CENTER="${MEMORY_CENTER:-}"
PKG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM=""

# 用户文件清单：系统文件（配置根）+ 规则三层（记忆规则/）
# ⚠️ 2026-10-02 扩到规则三层：原来只回滚 4 个系统文件，
#    而断章增量保护的是 7 处落点（含规则三层）⇒ 回滚范围必须对齐，
#    否则"能保护但不能退"= 只做了一半。
SYS_FILES=(SOUL.md IDENTITY.md USER.md MEMORY.md)
RULE_FILES=(用户基本规则-铁律版.md 用户基本规则-摘要版.md 用户基本规则-详解存档版.md)

# ── 工具 ─────────────────────────────────────────────────────────
usage() {
    cat <<'EOF'
📋 布洛陀 · 系统文件回滚工具

用法:
  ./rollback.sh                          列出可用备份
  ./rollback.sh --preview                预览最近一次差异（不写盘）
  ./rollback.sh --restore                恢复最近一次备份
  ./rollback.sh --restore=YYYYMMDD_HHMM  恢复指定时间戳
  ./rollback.sh --platform <端ID>        显式指定端（默认自动探测）

环境变量:
  export MEMORY_CENTER=/path/to/your/memory

覆盖范围:
  · 系统文件 SOUL / IDENTITY / USER / MEMORY（落在端配置根）
  · 规则三层 铁律版 / 摘要版 / 详解存档版（落在 <记忆中心>/记忆规则/）
EOF
}

die() { echo "❌ $*"; exit 1; }

# ── 端与配置根探测 ───────────────────────────────────────────────
# ⚠️ 原实现把 ~/.workbuddy 写死在三处 ⇒ 非 WB 端回滚会打到错的地方。
#    正解：读 adapters/<端>/capability.yaml 的 config_root（安装时的同一真源）。
detect_platform() {
    [ -n "$PLATFORM" ] && return 0
    local hits=()
    for cap in "$PKG_ROOT"/adapters/*/capability.yaml; do
        [ -f "$cap" ] || continue
        local cr
        cr=$(grep -m1 '^config_root:' "$cap" | awk '{print $2}' | tr -d '"')
        [ -z "$cr" ] && continue
        cr="${cr/#\~/$HOME}"
        [ -d "$cr" ] && hits+=("$(basename "$(dirname "$cap")"):$cr")
    done
    if [ ${#hits[@]} -eq 0 ]; then
        die "未探测到任何端配置根·请用 --platform <端ID> 显式指定"
    elif [ ${#hits[@]} -gt 1 ]; then
        echo "⚠️ 本机共存多端："
        for h in "${hits[@]}"; do echo "     $h"; done
        die "请用 --platform <端ID> 显式指定端"
    fi
    PLATFORM="${hits[0]%%:*}"
    CONFIG_ROOT="${hits[0]#*:}"
    return 0     # ⚠️ 显式 return：末条 `[ -n ] && return 0` 为假时函数返回非 0
}                #            （实测在 set -e 环境下会误退出·此处用 set -uo 更安全）

CONFIG_ROOT=""
resolve_config_root() {
    detect_platform
    if [ -n "$PLATFORM" ]; then
        local cap="$PKG_ROOT/adapters/$PLATFORM/capability.yaml"
        if [ -f "$cap" ]; then
            CONFIG_ROOT=$(grep -m1 '^config_root:' "$cap" | awk '{print $2}' | tr -d '"')
            CONFIG_ROOT="${CONFIG_ROOT/#\~/$HOME}"
        fi
    fi
    [ -z "$CONFIG_ROOT" ] && CONFIG_ROOT="$HOME/.workbuddy"
}

# Hermes 端：SOUL 在配置根，USER/MEMORY 在 memories/ 子目录
# ⚠️ 源码实证：doctor_state.py:234-238 / profiles.py:197
target_path() {
    local name="$1"
    case "$PLATFORM:$name" in
        hermes:USER.md|hermes:MEMORY.md) echo "$CONFIG_ROOT/memories/$name" ;;
        *) echo "$CONFIG_ROOT/$name" ;;
    esac
}

# ── 备份发现（认两种格式）─────────────────────────────────────────
# ① <记忆中心>/记忆琥珀/升级备份_<ts>/<file>.bak        （旧版 step5g）
# ② <记忆中心>/记忆琥珀/安装前备份/<file>.bak-<ts>       （断章引擎 C6）
BACKUP_KINDS=("升级备份_*" "安装前备份")

list_backups() {
    check_env
    # ⚠️ 必须先定端：`detect_platform` 内部会把端名写进另一个变量，
    #    但 `--list` 不带 --platform 时 PLATFORM 仍可能未定义 ⇒ set -u 直接炸。
    #    实测报 "PLATFORM 后跟一串乱码: unbound variable"——根因是**本段上方注释里**
    #    写了裸的 美元符号 + 变量名 + 问号，bash 解析注释时会一路吞字符。
    #    ⇒ 教训：⛔ bash 注释里不要出现 裸美元符号紧跟变量名再跟非空白字符 的写法。
    : "${PLATFORM:=未指定}"
    echo "📦 可用备份（记忆中心：$MEMORY_CENTER · 端：${PLATFORM}）"
    echo "   配置根：$CONFIG_ROOT"
    echo ""
    local n=0
    local total=$(( ${#SYS_FILES[@]} + ${#RULE_FILES[@]} ))
    for kind in "${BACKUP_KINDS[@]}"; do
        for d in "$BACKUP_DIR"/$kind; do
            [ -d "$d" ] || continue
            local cnt=0 ts label
            for f in "${SYS_FILES[@]}" "${RULE_FILES[@]}"; do
                ls "$d/$f.bak" >/dev/null 2>&1 && cnt=$((cnt+1))
                ls "$d/$f.bak-"* >/dev/null 2>&1 && cnt=$((cnt+1))
            done
            ts="$(basename "$d")"
            label="$ts"
            echo "  🕐 $label  →  $cnt/$total 个文件已备份   [$kind]"
            n=$((n+1))
        done
    done
    [ "$n" -eq 0 ] && echo "  (无备份记录·你可能还没跑过带备份的安装)"
    return 0
}

# 找某个文件在备份集里的实体路径（兼容 .bak 与 .bak-<ts> 两种）
find_bak() {
    local dir="$1" name="$2"
    if [ -f "$dir/$name.bak" ]; then echo "$dir/$name.bak"; return 0; fi
    local hit
    hit=$(ls -t "$dir/$name.bak-"* 2>/dev/null | head -1)
    if [ -n "$hit" ] && [ -f "$hit" ]; then echo "$hit"; return 0; fi
    return 1
}

resolve_backup_dir() {
    local ts="${1:-}"
    if [ -n "$ts" ]; then
        for kind in "${BACKUP_KINDS[@]}"; do
            local d="$BACKUP_DIR/${kind/\%/$ts}"
            [ -d "$d" ] && { echo "$d"; return 0; }
        done
        return 1
    fi
    # 取 mtime 最新的那个备份目录
    local newest="" newest_t=0
    for kind in "${BACKUP_KINDS[@]}"; do
        for d in "$BACKUP_DIR"/$kind; do
            [ -d "$d" ] || continue
            local t
            t=$(stat -f %m "$d" 2>/dev/null || stat -c %Y "$d" 2>/dev/null || echo 0)
            if [ "$t" -gt "$newest_t" ]; then newest_t="$t"; newest="$d"; fi
        done
    done
    [ -n "$newest" ] && { echo "$newest"; return 0; }
    return 1
}

# ── 预览 ─────────────────────────────────────────────────────────
do_preview() {
    check_env
    local dir; dir=$(resolve_backup_dir "${1:-}") || { die "未找到备份"; list_backups; return 1; }
    echo "🔍 预览备份：$(basename "$dir")"
    echo "   端：$PLATFORM · 配置根：$CONFIG_ROOT"
    echo ""
    for f in "${SYS_FILES[@]}"; do
        local bak cur
        bak=$(find_bak "$dir" "$f") || { echo "─── $f ─── 无备份"; continue; }
        cur=$(target_path "$f")
        echo "─── $f ───"
        echo "   位置：$cur"
        if [ -f "$cur" ]; then
            if diff -q "$bak" "$cur" >/dev/null 2>&1; then
                echo "   ✓ 与备份一致（无需回滚）"
            else
                echo "   ⟲ 与当前不同：$(diff "$bak" "$cur" 2>/dev/null | grep -c '^[<>]') 行差异"
            fi
        else
            echo "   ⚠️ 当前文件不存在"
        fi
    done
    for f in "${RULE_FILES[@]}"; do
        local bak cur="$MEMORY_CENTER/记忆规则/$f"
        bak=$(find_bak "$dir" "$f") || { echo "─── 记忆规则/$f ─── 无备份"; continue; }
        echo "─── 记忆规则/$f ───"
        echo "   位置：$cur"
        if [ -f "$cur" ]; then
            if diff -q "$bak" "$cur" >/dev/null 2>&1; then
                echo "   ✓ 与备份一致（无需回滚）"
            else
                echo "   ⟲ 与当前不同：$(diff "$bak" "$cur" 2>/dev/null | grep -c '^[<>]') 行差异"
            fi
        else
            echo "   ⚠️ 当前文件不存在"
        fi
    done
    echo ""
    echo "💡 确认无误后执行：./rollback.sh --restore"
}

# ── 恢复 ─────────────────────────────────────────────────────────
do_restore() {
    check_env
    local dir; dir=$(resolve_backup_dir "${1:-}") || { die "未找到备份"; list_backups; return 1; }
    echo "🔄 正在回滚到备份：$(basename "$dir")"
    echo "   端：$PLATFORM · 配置根：$CONFIG_ROOT"
    echo ""

    local safety="$BACKUP_DIR/回滚前_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$safety"

    local ok=0 skip=0 fail=0
    restore_one() {
        local bak="$1" target="$2" label="$3"
        [ -f "$bak" ] || { echo "  ⚠️  $label → 无备份，跳过"; skip=$((skip+1)); return; }
        mkdir -p "$(dirname "$target")"
        # ⚠️ 回滚本身也要能退：先备份当前版本
        if [ -f "$target" ]; then
            cp "$target" "$safety/$(basename "$target")" 2>/dev/null || true
        fi
        if cp "$bak" "$target" 2>/dev/null; then
            echo "  ✅ $label → 已恢复"
            ok=$((ok+1))
        else
            echo "  ❌ $label → 恢复失败：$target"
            fail=$((fail+1))
        fi
    }

    # ⚠️⛔ **必须横跨所有备份目录找**（早期只取"最新一个目录"）——
    #    实测踩中：旧版升级备份里有 SOUL，断章引擎的安装前备份里有规则三层，
    #    两者时间戳不同 ⇒ 只取最新 ⇒ 另一批文件"无备份"被跳过 ⇒
    #    **回滚只回了一半**（保护与退出不对齐= 只做了一半）。
    #    正解：每个文件独立地在所有备份目录里找，取**最新的一份**。
    find_bak_all() {
        local name="$1" best="" best_t=0
        for kind in "${BACKUP_KINDS[@]}"; do
            for d in "$BACKUP_DIR"/$kind; do
                [ -d "$d" ] || continue
                local cand
                cand=$(find_bak "$d" "$name" || true)
                [ -z "$cand" ] && continue
                local t
                t=$(stat -f %m "$cand" 2>/dev/null || stat -c %Y "$cand" 2>/dev/null || echo 0)
                if [ "$t" -gt "$best_t" ]; then best_t="$t"; best="$cand"; fi
            done
        done
        [ -n "$best" ] && echo "$best"
    }

    for f in "${SYS_FILES[@]}"; do
        restore_one "$(find_bak_all "$f")" "$(target_path "$f")" "$f"
    done
    for f in "${RULE_FILES[@]}"; do
        restore_one "$(find_bak_all "$f")" "$MEMORY_CENTER/记忆规则/$f" "记忆规则/$f"
    done

    echo ""
    echo "─────────────────────────────"
    echo "✅ 回滚完成：恢复 $ok · 跳过 $skip · 失败 $fail"
    echo "   回滚前版本另存：$safety"
    if [ "$fail" -gt 0 ]; then
        echo "⚠️ 有文件恢复失败，请检查上面标 ❌ 的行"
        return 1
    fi
    if [ "$skip" -gt 0 ]; then
        echo "ℹ️ 跳过的是备份集中没有的文件（不是错误）"
    fi
}

check_env() {
    if [ -z "$MEMORY_CENTER" ]; then
        die "未设置 MEMORY_CENTER
   运行前设置：export MEMORY_CENTER=/path/to/your/memory
   或：MEMORY_CENTER=/path ./rollback.sh --restore"
    fi
    [ -d "$MEMORY_CENTER" ] || die "记忆共享中心不存在：$MEMORY_CENTER"
    BACKUP_DIR="$MEMORY_CENTER/记忆琥珀"
    [ -d "$BACKUP_DIR" ] || die "备份目录不存在：$BACKUP_DIR
   你可能还没跑过带备份的安装"
    resolve_config_root
}

# ── 参数解析 ─────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --platform) PLATFORM="${2:-}"; shift 2 ;;
        --platform=*) PLATFORM="${1#*=}"; shift ;;
        --preview)   do_preview "${2:-}"; exit $? ;;
        --restore)   do_restore "${2:-}"; exit $? ;;
        --restore=*) do_restore "${1#*=}"; exit $? ;;
        --list|-h|--help) list_backups; exit 0 ;;
        -*) die "未知参数：${1}（--help 看用法）" ;;
        *) die "未知参数：${1}（--help 看用法）" ;;
    esac
done
usage