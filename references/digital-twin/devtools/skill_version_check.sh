#!/bin/bash
# skill-version-check.sh — Skill 版本一致性机械校验 v1.1
# 变更记录: v1.1(2026-10-20·Qoder CN·版本对账批)——frontmatter 提取由 head -15 固定窗
#   改为开/闭 --- 精确解析。根因=实测 awaken-memory-system version 落在第16行被漏读，
#   巡检假报🟡「无版本声明」（窗口截断≠字段不存在）。v1.0(2026-09 better-harness 发现#5)
# 来源: better-harness 发现#5「治理铁律靠口头重复维持」→ 落成机械校验
# 铁律依据: 皮叔的治理规则——每个 skill 内涉及版本信息必须全部一致，不允许版本不一致的信息存在
# 用法:
#   bash skill-version-check.sh              # 扫描默认目录，输出违规清单
#   bash skill-version-check.sh /path/to/dir # 扫描指定 skill 根目录
# 只读脚本，不修改任何文件。

set -u
SKILL_ROOT="${1:-$HOME/.qoder/skills}"
PASS=0; FAIL=0; WARN=0
echo "=== Skill 版本一致性校验 v1.1 ==="
echo "扫描根: $SKILL_ROOT"
echo ""

for dir in "$SKILL_ROOT"/*/; do
  name=$(basename "$dir")
  f="$dir/SKILL.md"
  [ -f "$f" ] || { echo "⚪ $name: 无 SKILL.md, 跳过"; continue; }

  # 1) frontmatter version 字段（v1.1: 首行 --- 到次 --- 精确解析，⛔不用固定行窗——防深位字段漏读）
  fm_ver=$(awk 'NR==1 && $0 ~ /^---[[:space:]]*$/ {infm=1; next} infm && $0 ~ /^---[[:space:]]*$/ {exit} infm && $0 ~ /^version:/ {gsub(/^[version:[:space:]"]+/,""); gsub(/["[:space:]]+$/,""); print; exit}' "$f")

  # 2) 正文自版本声明行（"> **版本**：vX.Y.Z" / "版本：vX.Y.Z" 开头的行）
  body_vers=$(grep -oE '^>? ?\*{0,2}版本\*{0,2}[：:][[:space:]]*v?[0-9]+\.[0-9]+(\.[0-9]+)?' "$f" \
    | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | sort -u)

  # 3) 汇总本 skill 的全部"自版本"取值
  all_vers=$(printf '%s\n%s\n' "$fm_ver" "$body_vers" | grep -E '^[0-9]' | sort -u)
  n_distinct=$(echo "$all_vers" | grep -c . || true)

  if [ -z "$all_vers" ]; then
    echo "🟡 $name: 未找到任何版本声明（frontmatter 无 version 且正文无版本行）"
    WARN=$((WARN+1))
  elif [ "$n_distinct" -eq 1 ]; then
    echo "✅ $name: v$(echo "$all_vers" | head -1) 一致"
    PASS=$((PASS+1))
  else
    echo "🔴 $name: 版本不一致 → [$(echo "$all_vers" | tr '\n' ' ' | sed 's/ $//')]"
    # 输出各版本出现的行号，便于定位
    for v in $all_vers; do
      lines=$(grep -nE "版本\*{0,2}[：:].*v?${v}|^version:.*${v}" "$f" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
      echo "     v$v @ 行 $lines"
    done
    FAIL=$((FAIL+1))
  fi
done

echo ""
echo "=== 结果: ✅$PASS 一致 | 🔴$FAIL 不一致 | 🟡$WARN 无版本声明 ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
