#!/bin/bash
# amber_pin.sh v2.0 — 手动标记"重要·永久"备份（人工指定，永不被 cleanup 删）
# 设计：重要=价值判断，只能人指定，脚本不自动判定。
#   v2.0（2026-07-26）：永久件统一落入「永久收藏」子文件夹——文案词=文件夹名，
#   用户在 个人AI档案→记忆琥珀→永久收藏 一眼找到全部永不清理的文件。
#   pin  = 把某文件当前最新的普通备份，复制一份为 _major_ 版放进 永久收藏/
#   复制而非重命名：普通备份仍走 7天/同日清理，永久版独立保存
# 用法：
#   amber_pin.sh <关键词>        收藏：匹配琥珀库中含关键词的最新普通备份
#   amber_pin.sh --list          列出「永久收藏」内容
#   amber_pin.sh --unpin <名字>  取消收藏（删除永久收藏里的该 _major_ 副本）
set -euo pipefail
AMBER_DIR="[记忆共享中心]/记忆琥珀"
PERM_DIR="$AMBER_DIR/永久收藏"
mkdir -p "$PERM_DIR"

usage() { grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0; }
[ $# -eq 0 ] && usage

case "$1" in
  --list)
    echo "=== 永久收藏（个人AI档案 → 记忆琥珀 → 永久收藏）==="
    pinned=$(find "$PERM_DIR" -maxdepth 1 -name "*_major_*.bak" 2>/dev/null | sort)
    legacy=$(find "$AMBER_DIR" -maxdepth 1 -name "*_major_*.bak" 2>/dev/null | sort)
    if [ -z "$pinned" ] && [ -z "$legacy" ]; then
      echo "（还没有主动收藏过。用 amber_pin.sh <关键词> 收藏）"
    else
      [ -n "$pinned" ] && echo "$pinned" | sed "s|$PERM_DIR/|📌 |"
      [ -n "$legacy" ] && echo "$legacy" | sed "s|$AMBER_DIR/|📌(旧位置) |"
    fi
    other=$(find "$PERM_DIR" -maxdepth 1 -type f ! -name "*_major_*.bak" ! -name "归档清单*" ! -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
    [ "$other" -gt 0 ] && echo "（另有 ${other} 份历史归档文件也在此文件夹）"
    ;;
  --unpin)
    [ $# -lt 2 ] && { echo "❌ 用法: amber_pin.sh --unpin <收藏件名字>"; exit 1; }
    target=$(find "$PERM_DIR" "$AMBER_DIR" -maxdepth 1 -name "*$2*_major_*.bak" 2>/dev/null | head -1)
    [ -z "$target" ] && { echo "❌ 永久收藏里没找到匹配 '$2' 的收藏件"; exit 1; }
    rm -f "$target"; echo "✅ 已取消收藏: $(basename "$target")"
    echo "   注：原普通备份不受影响，仍按正常规则清理"
    ;;
  *)
    kw="$1"
    latest=$(find "$AMBER_DIR" -maxdepth 1 -name "*${kw}*.bak" -not -name "*_major_*" 2>/dev/null | sort | tail -1)
    if [ -z "$latest" ]; then
      echo "❌ 琥珀库里没找到含 '$kw' 的普通备份"
      echo "   提示：先确认该文件在白名单里、且已被备份过（改动一次会自动备份）"
      exit 1
    fi
    bn=$(basename "$latest")
    # 命名保留 _major_ 子串双保险：即使文件被移出子文件夹，cleanup 的排除模式仍护住它
    major_name="${bn%.bak}_major_keep.bak"
    major_path="$PERM_DIR/$major_name"
    if [ -f "$major_path" ]; then
      echo "🟡 这一版已经收藏过了，无需重复: $major_name"; exit 0
    fi
    cp "$latest" "$major_path"
    echo "✅ 已放入「永久收藏」，永远不会被自动清理"
    echo "   源: $bn"
    echo "   位置: 个人AI档案 → 记忆琥珀 → 永久收藏 → $major_name"
    ;;
esac
