#!/bin/bash
# growth_chain.sh — 成长箱自动化链单驱动（D11 根治·2026-09-18·v1.0.0）
#
# 为什么合并成一份驱动（不是五份 plist）：
#   五份 plist 各自 RunAtLoad=True → 登录批次同刻齐发，"08:00 采集 → 08:15 裁决 →
#   08:30 预测 → 08:45 日报 → 08:50 到期"的**棒序依赖**被打乱（2026-09-18 实测：
#   日报棒 11:22:25 早于采集棒 11:24:07，于是今天的行装的是昨天的数据）。
#   五份调度 = 五个各自为政的时钟；一份驱动 = 一个有序调用。环节数 5→1，不是新增自动化。
#
# 纪律：每棒独立跑、失败不拖垮后棒（记录 rc）；⛔不在本脚本里做任何判定（判据住各棒内）；
#       全程只写各棒既有产物 + 链日志（写域零扩张）。
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="[记忆共享中心]/成长箱"
LOG="$BASE/修复草案/链运行.log"
PYTHON="${PYTHON:-/usr/bin/python3}"

STEPS=(
  "采集|$SCRIPT_DIR/growth_signal_collector.py|"
  "裁决探针|$SCRIPT_DIR/growth_decision_gate.py|--probe"
  "裁决|$SCRIPT_DIR/growth_decision_gate.py|"
  "预测|$SCRIPT_DIR/growth_pattern_predictor.py|"
  "跨域日报|$SCRIPT_DIR/growth_cross_link.py|"
  "到期提醒|$SCRIPT_DIR/immunity_l1_draft.py|--due --notify"
  "竞态侦测|[记忆共享中心]/脚本中心/write_race_watch.py|scan"
)

run_chain() {
  mkdir -p "$(dirname "$LOG")"
  local line rc_any=0 rc
  for s in "${STEPS[@]}"; do
    IFS='|' read -r name script args <<< "$s"
    if [ ! -f "$script" ]; then
      printf '%s | %s | MISSING %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$name" "$script" >> "$LOG"
      rc_any=1
      continue
    fi
    # shellcheck disable=SC2086
    "$PYTHON" "$script" $args >/dev/null 2>&1
    rc=$?
    [ "$rc" -ne 0 ] && rc_any="$rc"
    printf '%s | %s | rc=%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$name" "$rc" >> "$LOG"
  done
  echo "growth_chain: ${#STEPS[@]} 步按序完成（日志 ${LOG}·最差 rc=${rc_any}）"
  return "$rc_any"
}

self_test() {
  # 断言：①每棒脚本存在 ②顺序为 采集→探针→裁决→预测→日报→到期→竞态 ③到期棒带 --notify ④末棒为侦测器
  local fail=0 i=0 name script args
  for s in "${STEPS[@]}"; do
    IFS='|' read -r name script args <<< "$s"
    [ -f "$script" ] || { echo "  ✗ T1 缺脚本：$name → $script"; fail=1; }
    i=$((i+1))
  done
  order=$(printf '%s\n' "${STEPS[@]}" | cut -d'|' -f1 | tr '\n' ',')
  want="采集,裁决探针,裁决,预测,跨域日报,到期提醒,竞态侦测,"
  [ "$order" = "$want" ] || { echo "  ✗ T2 棒序漂移：$order ≠ $want"; fail=1; }
  grep -q -- "--due --notify" <(printf '%s\n' "${STEPS[@]}") \
    || { echo "  ✗ T3 到期棒未带 --notify（D12 消费端断线）"; fail=1; }
  [ "$fail" -eq 0 ] && echo "SELF-TEST PASS（T1 七棒齐·T2 序对·T3 通知在·共 ${#STEPS[@]} 棒）"
  return "$fail"
}

case "${1:-run}" in
  --self-test|selftest) self_test ;;
  *) run_chain ;;
esac
