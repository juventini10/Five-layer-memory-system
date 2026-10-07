#!/usr/bin/env bash
# tests/test_retire_anchor.sh — 离源台账去重锚回归（工单 D19②·growth_box_check.sh v2.1）
#
# 治什么病：退役台账用「抗体标题」做去重锚。标题可匿名（E9.2 链上 9 条全署「未命名抗体」），
# 第二条不同命令会被第一条的匿名标题判「已登记」而丢弃 → 台账丢条 = 不可点名 = 死数据。
# 锚改为「抗体命令 sha1 前 12」后，本夹具把两种形态都钉住：
#   T1 同命令双跑 → 只留一行（不自我膨胀）
#   T2 同标题不同命令 → 各留一行（本次根治的病症）
#   T3 变异自证 → 把锚退化成标题匹配，T2 的病症必须复现（证明绿来自锚变更，不是放宽）
#   T4 存量无锚行 → 仍按标题回退（历史条目不重复追加）
#
# ⛔ 本夹具不重写被测实现：retire_already / ab_anchor 由 awk 从 growth_box_check.sh 原位抽出。
# ⛔ 台账走 mktemp，绝不碰 真源 免疫退役记录.md。

set -uo pipefail
SRC="${GB_CHECK_SRC:-[记忆共享中心]/技能配置/growth-box/scripts/growth_box_check.sh}"
[[ -f "$SRC" ]] || { echo "❌ 被测脚本不存在: $SRC"; exit 1; }

RETIRE_LOG="$(mktemp -t gb-retire)"
trap 'rm -f "$RETIRE_LOG"' EXIT

eval "$(awk '/^retire_already\(\)\{/{f=1} f{print} /^ab_anchor\(\)\{/{exit}' "$SRC")"
declare -F retire_already ab_anchor >/dev/null || { echo "❌ 函数抽取失败（被测脚本结构变了，夹具需同步）"; exit 1; }

append(){ echo "  - 2026-09-19 | 🟡退役候选 | 形 | $2 | \`$1\` | 来源: T | 锚:$(ab_anchor "$1")" >> "$RETIRE_LOG"; }
anchor_lines(){ grep -cF "| 锚:$(ab_anchor "$1")" "$RETIRE_LOG" 2>/dev/null || true; }

fails=0; total=0
C1='test ! -f "/abs/x.md"'
C2='grep -q "QCN-20260919" "[记忆共享中心]/成长箱/learnings/qoder_cn_errors.md"'
C3='python3 "[记忆共享中心]/脚本中心/some_other_guard.py" --check'

# T1 同一命令连续两轮巡检 → 台账不得重复
for _ in 1 2; do retire_already "$C1" "未命名抗体" || append "$C1" "未命名抗体"; done
n=$(anchor_lines "$C1"); total=$((total+1))
if [[ "$n" == "1" ]]; then echo "✅ T1 同命令双跑不重复（行数=1）"
else echo "❌ T1 期望 1 行，实得 ${n}（去重失效=台账自我膨胀）"; fails=$((fails+1)); fi

# T2 标题相同（都署「未命名抗体」）、命令不同 → 必须各留一行
for c in "$C2" "$C3"; do retire_already "$c" "未命名抗体" || append "$c" "未命名抗体"; done
a2=$(anchor_lines "$C2"); a3=$(anchor_lines "$C3"); total=$((total+1))
if [[ "$a2" == "1" && "$a3" == "1" ]]; then echo "✅ T2 匿名同标题·不同命令 → 两行俱在（$a2/${a3}）"
else echo "❌ T2 期望 1/1，实得 $a2/${a3}（匿名抗体被误并=台账丢条，D19②的病复发）"; fails=$((fails+1)); fi

# T3 变异自证：把锚退化成标题匹配（在**全量台账**上按标题判重，=v2.1 前的行为）
#    → 必须复现误并：C3 会被判「已登记」而丢弃。否则 T2 的反例不成立、该判据没有专属证据。
grep -qF "| 未命名抗体 | " "$RETIRE_LOG"
mut_would_drop=$?; total=$((total+1))
if [[ "$mut_would_drop" == "0" ]]; then echo "✅ T3 变异体（标题锚）复现误并：C3 在旧逻辑下被判已登记 → 判据活着"
else echo "❌ T3 变异体未复现误并 → T2 的反例不成立"; fails=$((fails+1)); fi

# T4 存量无锚行（v2.1 之前登记）→ 按标题回退命中，不重复追加历史条目
echo "  - 2026-09-06 | 🚫强制退役 | 恒真 | 旧标题抗体 | \`x\` | 来源: 老 | " >> "$RETIRE_LOG"
total=$((total+1))
if retire_already "完全不相关的命令" "旧标题抗体"; then echo "✅ T4 存量无锚行按标题回退命中"
else echo "❌ T4 回退失效（历史条目会重复追加）"; fails=$((fails+1)); fi

# T5 带锚行不得参与标题回退（T2 的加固：匿名标题不能吞掉新命令）
total=$((total+1))
if retire_already "全新形态命令 zzz" "未命名抗体"; then
  echo "❌ T5 带锚的匿名行仍被当成回退依据 → 换锚等于没换"; fails=$((fails+1))
else echo "✅ T5 带锚行不参与标题回退（匿名标题不再吞新命令）"; fi

echo "RETIRE-ANCHOR: $((total-fails))/$total 通过"
[[ $fails -eq 0 ]] && { echo "MUT:OK 判据可证伪=T3 复现旧病"; exit 0; } || { echo "MUT:FAIL"; exit 1; }
