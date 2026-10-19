#!/bin/bash
# kb_philo_consistency.sh — 知识库/设计哲学「声明-证据」对账器 v1.1
# 设计定位：让哲学文档的"声称"被实盘产物定期质证——漂移显形，不修文不拦截（填值权归登记方）
# 三态输出：GREEN=齐 / YELLOW=文档滞后 N 天 / RED=矛盾（实盘活而文档零登记）
# 真相源两侧：
#   证据侧 = 各端 .patrol 心跳(.ts) + 台账行数(jsonl) + 产物 mtime（客观·不会说谎）
#   声明侧 = 哲学文件夹各 INDEX/看板 frontmatter version + 变更记录最新条目日期（解析 markdown）
# 原则：只读+追加台账+失败放行 exit 0；⛔不改任何被对账文件（守卫编写规范 Hook 纪律）
# v1.1（2026-09-23·AutoClaw 童灵 D3 根治轮）：check_version_sync 排序根治——原 sort -n 把主版本带 v 前缀的
#   「v2」当非数字读作 0，主版本跨越时（v1.x→v2.x）v2.24 被 v1.99 压住＝对账器自身假 RED（分身看板实案）。
#   修：剥 v 前缀后按三段数值排序取最大，比对时 frontmatter 同步剥 v（兼容守卫规范「1.2.171」无 v 风格）。
# 挂载：route_autoclaw_patrol.sh 循环外降级段（30min 承载·跨工具中立）
# 创建：2026-08-27 by AutoClaw ｜ 皮叔令"基于我的愿景第一性原理最优解"
set -u

PHILO_DIR="[记忆共享中心]/脚本中心"
KB_PHILO="$PHILO_DIR/知识库设计哲学"
TWIN_PHILO="$PHILO_DIR/数字分身设计哲学"
SCRIPT_PHILO="$PHILO_DIR/布洛陀脚本架构设计哲学"
PATROL_DIR="[记忆共享中心]/脚本中心/.patrol"
LEDGER="$PATROL_DIR/kb_philo_consistency.jsonl"

now_ts=$(date +%s)
findings=()

# —— 对账项1：知识库哲学各文件的变更记录新鲜度 vs 实盘活动 ——
# 实盘证据：.patrol 目录今天有写入（审计在跑）而知识库看板变更记录仍停在更早日期 → YELLOW
check_freshness() {
  local doc="$1" label="$2"
  [ -f "$doc" ] || { findings+=("RED|$label|文件不存在"); return; }
  # 变更记录最新条目日期（仅取 YYYY-MM-DD 的日期部分）
  local last_entry
  last_entry=$(grep -oE '2026-[0-9]{2}-[0-9]{2}' "$doc" 2>/dev/null | tail -1)
  if [ -z "$last_entry" ]; then
    findings+=("YELLOW|$label|变更记录无法解析（无 YYYY-MM-DD 条目）")
    return
  fi
  local entry_sec
  entry_sec=$(date -j -f "%Y-%m-%d" "$last_entry" +%s 2>/dev/null || echo 0)
  if [ "$entry_sec" -eq 0 ]; then
    findings+=("YELLOW|$label|日期解析失败：$last_entry")
    return
  fi
  local doc_mtime_days=$(( (now_ts - $(stat -f %m "$doc") ) / 86400 ))
  local entry_days=$(( (now_ts - entry_sec) / 86400 ))
  local drift=$(( entry_days > doc_mtime_days ? doc_mtime_days : entry_days ))
  if [ "$drift" -ge 3 ]; then
    findings+=("YELLOW|$label|变更记录滞后 ${drift} 天（最后条目 2026-${last_entry}）——若期间有实盘工作即漏登")
  else
    findings+=("GREEN|$label|新鲜度 OK（≤${drift}天）")
  fi
}

# —— 对账项2：frontmatter version vs 变更记录最大版本号（版本头悬停检测·你今日抓的第三类） ——
check_version_sync() {
  local doc="$1" label="$2"
  local fm_v log_v
  fm_v=$(awk '/^version:/{print $2; exit}' "$doc" 2>/dev/null)
  # 前导空白容错（2026-08-28 实修）：条目写入时曾带 1 个前导空格（" - v1.39"），列首正则读不到 → 误报版本头悬停。
  # 只放宽缩进，不放宽条目形态（仍须 "- v数字" 起头）→ 真漏记/真悬停照样 RED。
  # v1.1: 剥 v 前缀再数值排序（主版本跨越 bug 根治·见头注）
  log_v=$(grep -oE '^[[:space:]]*- v?[0-9]+(\.[0-9]+)*' "$doc" 2>/dev/null | sed 's/^[[:space:]]*- //; s/^v//' | sort -t. -k1,1n -k2,2n -k3,3n | tail -1)
  fm_v_norm=$(printf '%s' "$fm_v" | sed 's/^v//')
  [ -z "$fm_v_norm" ] || [ -z "$log_v" ] && return
  if [ "$fm_v_norm" != "$log_v" ]; then
    # 2026-08-29 根治: 原 "${log_v}（"同款全角吞名 → RED(有漂移)路径亦崩;与下方 GREEN 路径合计=
    # check_version_sync 两条分支全崩,该函数自建起从未跑通(实测 line 63 崩)。
    findings+=("RED|$label|frontmatter version=${fm_v} ≠ 变更记录最新=${log_v}（版本头悬停）")
  else
    # 2026-08-29 根治: 原写 "${fm_v}）"——中文全角括号(EF BC 89)紧贴变量名,bash 3.2 把多字节
    # 字节当标识符字符 → 变量名被吃成 fm_v\xef... → set -u unbound → 全绿路径崩死(挂30min循环=沉默死)。
    # 修: ${fm_v} 花括号显式界定变量名边界。凡变量后紧跟中文标点,必须用 ${var}。
    findings+=("GREEN|$label|version 同步（${fm_v}）")
  fi
}

# —— 对账项3：patrol 实盘活跃 vs 知识库看板「待决项」声称矛盾（如#3曾标待办而实盘跑了半月） ——
# 启发式：待决项含"待办/待实施/待机"字样，但对应台账已大量记录 → RED 质证
check_pending_vs_ledger() {
  local board="$KB_PHILO/03-进度看板.md"
  [ -f "$board" ] || return
  local audit_total=0
  if [ -f "$PATROL_DIR/audit_state.json" ]; then
    audit_total=$(python3 -c "
import json
try:
    d=json.load(open('$PATROL_DIR/audit_state.json'))
    print(sum(int(v) for v in d.get('sessions',{}).values()))
except Exception:
    print(0)" 2>/dev/null || echo 0)
  fi
  if [ "$audit_total" -gt 100 ] && grep -qE "^\| 3 \| .*审计兜底.*\|( 第三刀待办|\s*第三刀待办)" "$board" 2>/dev/null; then
    findings+=("RED|知识库看板#3|审计兜底累计 ${audit_total} 条但状态仍标'第三刀待办'（声明-证据矛盾）")
  fi
}

# —— 执行 ——
mkdir -p "$PATROL_DIR" 2>/dev/null
check_freshness "$KB_PHILO/INDEX.md"        "知识库INDEX"
check_freshness "$KB_PHILO/03-进度看板.md"  "知识库看板"
check_freshness "$SCRIPT_PHILO/INDEX.md"    "脚本哲学INDEX"
check_freshness "$TWIN_PHILO/03-进度看板.md" "分身看板"
check_version_sync "$KB_PHILO/INDEX.md"          "知识库INDEX"
check_version_sync "$KB_PHILO/03-进度看板.md"    "知识库看板"
check_version_sync "$SCRIPT_PHILO/INDEX.md"      "脚本哲学INDEX"
check_version_sync "$SCRIPT_PHILO/守卫编写规范.md" "守卫规范"
check_version_sync "$TWIN_PHILO/03-进度看板.md"   "分身看板"
check_version_sync "$TWIN_PHILO/06-跨端适配规范.md" "分身06规范"
check_pending_vs_ledger

# 输出+台账
ts=$(date +%Y-%m-%dT%H:%M:%S)
red=0; yellow=0; green=0
# 2026-08-29 健康态崩溃根治(同 changelog_guard v1.12.1): 全部对账项无产出时 findings 为空数组,
# 裸 "${findings[@]}" 在 set -u/bash 3.2 下触发 unbound → 对账在"全绿"时崩死(本脚本挂 30min 定时循环=静默失效)。
for f in ${findings[@]+"${findings[@]}"}; do
  state="${f%%|*}"
  case "$state" in
    RED) red=$((red+1)); echo "🔴 $f" ;;
    YELLOW) yellow=$((yellow+1)); echo "🟡 $f" ;;
    GREEN) green=$((green+1)); echo "✅ $f" ;;
  esac
done
echo "――― 对账汇总 $ts : GREEN=$green YELLOW=$yellow RED=$red ―――"
printf '{"ts":"%s","green":%d,"yellow":%d,"red":%d,"findings":"%s"}\n' \
  "$ts" "$green" "$yellow" "$red" "$(IFS=';'; echo "${findings[*]}" | tr '|' '/')" >> "$LEDGER" 2>/dev/null

# 退出码：0=无RED（失败放行纪律·不拦 patrol 链）；1=有RED（仅供上游日志观察，不阻断）
[ "$red" -eq 0 ] && exit 0 || exit 1

