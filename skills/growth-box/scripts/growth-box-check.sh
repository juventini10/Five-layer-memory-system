#!/usr/bin/env bash
#
# growth-box-check.sh — 成长箱晋升提醒（只读巡检，只报告不写入）
# Version: 1.1 (2026-07-16) — 修复晋升判断逻辑（文件总条目数→单条Count≥3且active）
#
# 检查逻辑：
#   1. 扫描 learnings/ 下各错误文件，按单条错误统计 Count/累计次数
#   2. 晋升阈值 = 3次（与 growth-box SKILL.md 一致）
#   3. 单条 Count ≥ 3 且 Status: active/pending → 报告"待晋升"
#   4. 同时检查各 agent 通知箱未读条目数
#
# 用法：
#   growth-box-check.sh            # 完整报告
#   growth-box-check.sh --summary  # 仅摘要
#   growth-box-check.sh --pending  # 仅待晋升列表
#
set -eo pipefail

LEARNINGS_DIR="$HOME/个人AI档案/成长箱/learnings"
NOTIFICATIONS_DIR="$HOME/个人AI档案/成长箱/notifications"
THRESHOLD=3
export THRESHOLD

# ── 1. 错误晋升检查 ──────────────────────────────────────────────
echo "🌱 成长箱晋升巡检"
echo

pending=()
for f in "$LEARNINGS_DIR"/*.md; do
  name=$(basename "$f")
  # skip INDEX and general docs
  [[ "$name" =~ ^(INDEX|ERRORS|LEARNINGS|FEATURE_REQUESTS|book)_?\.md$ ]] && continue

  file_total=$(grep -c "^## \[" "$f" 2>/dev/null || echo 0)

  # 用 perl 按条目遍历，提取 Count/累计次数 + Status
  perl -ne '
    BEGIN { $title=""; $count=""; $status=""; $first=1 }
    if (/^## \[/) {
      # 输出上一条（如果满足条件）
      if (!$first && $count ne "" && $count >= $ENV{THRESHOLD} && $status eq "active") {
        print "$prev_title\n";
      }
      $title=$_; chomp $title;
      $count=""; $status="";
      $first=0;
      $prev_title=$title;
    }
    if (/\*\*Count\*\*:/ || /\*\*累计次数\*\*:/) {
      if (m{([0-9]+)/[0-9]+}) { $count=$1 }
      if (/Count:[^0-9]*([0-9]+)/ && ($count eq "" || $1 > $count)) { $count=$1 }
    }
    if (/\*\*Status\*\*:/) {
      $status = /active|pending/ ? "active" : "done";
    }
    END {
      if ($count ne "" && $count >= $ENV{THRESHOLD} && $status eq "active") {
        print "$prev_title\n";
      }
    }
  ' "$f" > /tmp/gb_candidates.txt

  cand_count=$(wc -l < /tmp/gb_candidates.txt | tr -d ' ')
  if [[ "$cand_count" -gt 0 ]]; then
    echo "  🔴 $name: $cand_count 条达到晋升阈值 (≥$THRESHOLD)"
    while IFS= read -r line; do
      [[ -n "$line" ]] && echo "      - $line"
    done < /tmp/gb_candidates.txt
    pending+=("$name")
  else
    echo "  ✅ $name: $file_total 条 (无≥${THRESHOLD}次的晋升候选)"
  fi
done

# ── 2. 通知箱检查 ────────────────────────────────────────────────
echo
echo "📬 通知箱检查"
has_unread=0
for nf in "$NOTIFICATIONS_DIR"/*_pending.md; do
  agent=$(basename "$nf" _pending.md)
  # 未读条目：有日期的非占位行
  unread=$(awk '/^\| [0-9]{4}-/ && !/\| - \|/ {n++} END{print n+0}' "$nf" 2>/dev/null || echo 0)
  if [[ "$unread" -gt 0 ]]; then
    echo "  🔴 $agent: $unread 条未读"
    has_unread=1
  else
    echo "  ✅ $agent: 0 未读"
  fi
done

# ── 3. 蒸馏建议 ──────────────────────────────────────────────────
echo
echo "🧪 蒸馏建议"
total_pending=${#pending[@]}
if [[ $total_pending -gt 0 ]]; then
  echo "  有 $total_pending 个错误文件含待晋升条目，建议启动 growth-box 蒸馏流程"
  echo "  文件: ${pending[*]}"
else
  echo "  所有错误记录均未达到晋升阈值 ✅"
fi

if [[ $has_unread -eq 0 ]]; then
  echo "  所有 agent 通知箱均为空 ✅"
fi

echo
echo "📊 巡检完成 · 脚本只读模式"
