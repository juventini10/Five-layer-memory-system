#!/bin/bash
# route_traework_patrol.sh v0.8 — Trae Work 统一接入层（拉模式·摘要级降级审计·装机版）
# [包内装机版·与记忆中心运行时版 v0.6 同源]
#
# ⚠️ 本文件是「端用户态」派生版（vs 作者态运行时版），四处差异：
#   ① 全量占位符化：路径一律 [记忆共享中心]/脚本中心/…（安装时 setup.sh fill_ph 替换真实路径）
#      —— 作者态写 ~/[记忆共享中心]/开发工具/…，装机态脚本落在 脚本中心/（install_scripts.py ①）
#   ② 缺件守卫静默降级：每次调用前 [ -f ] 判存，缺则记 SKIP 不阻塞；
#      另设「域外」模式(X)：件在盘但本机无守对象（知识库域/AI学习库域）⇒ 不跑、不计可达
#      （⛔非故障、⛔不报成告警、⛔不谎报成可达）
#   ③ 末尾自报「实跑接入率」：机械计数 可达/12（⛔不虚报·对齐「数据真实性=伦理底线」）
#   ④ 不含作者侧自校验腿（platform_adaptation_check --src dsh/traework）——该件读作者侧
#      SSOT 文档，端用户机器不存在 ⇒ 本版不引用（⛔不留死链）
#
# 第一性原理接入形态（2026-08-19）：Trae Work 无 CC 式 hooks（平台边界），
#   会话数据只有 session_memory jsonl（记忆摘要·无完整转录）→ 守卫只能降级审计。
#   运行载体 = 系统 launchd（跨工具中立铁律·⛔不挂工具内置调度）。
# 触发源：
#   - 系统 launchd 每 30 分钟（拉·主通道）→ 心跳监督 + 摘要级降级审计
#   - Trae Work Automations（兜底监督·可选）→ 心跳检查/断链告警
#
# 守卫名册（唯一数据源·静态可达统计与实跑调用同源·⛔不写第二份）：
#   ── 计入接入率分母 5 件（SSOT §二·七「降级接入」组）──
#   ✅ route_audit（--src traework·从 intent 判疑似漏触发）
#   ✅ guard_audit（route_guard_audit.py --src traework·从 actions 判敏感操作）
#   ✅ rule_three_layer_guard（只读三文件·版本号+铁律集合一致性）
#   ⛔ audit_search_kb（从 actions 判知识调用）  ← 知识库域·端用户无知识库⇒守卫无对象
#   ⛔ card_id_guard（立场卡编号防撞·CARD_GUARD_HOST=traework）← AI学习库域·端用户无立场卡库⇒无对象
#      ⚠️ 口径说明（2026-10-01 实测订正）：这两件的 .py **确实在包内、也落盘脚本中心**（可调用），
#         但**本机无其守的对象**。故按 2026-09-17「按域剔」决策口径：分母仍计 5（SSOT 不变），
#         但**不计入「可达」**（可达＝本机有对象可守）。作者态 SSOT 标 ✅ 系作者机有库口径；
#         端用户态实跑 = 3/12（⛔非假绿：3 件有对象且可达，2 件域外无对象，已显式自报不计）。
#   ── 不计分母（专属 / 附加检查）──
#   ＋ session_memory_quality_guard（Trae Work 专属·摘要结构完整性 + learned 字段监控）
#   ＋ trae_isolation_guard（Trae 系共享文件端中性巡检·2026-09-30）
#   ── 装不上（计入分母·本 patrol 不实跑）──
#   🔴 route_inject / miss_feeder / kb_inject（无 UserPromptSubmit 事件/插件点）
#   🔴 unknown_unknown / feedback_detect（无完整转录·摘要级审计不可达）
#   ── 设计不适用（排除分母）──
#   ❌ crossend（无多工作区跨端场景）
#   接入率 = 可达件数/12（分母 12 = 5 降级接入 + 4 无转录 + 3 入站·crossend 排除）
#
# 增量语义：audit_state_traework.json 记录 {sessions: {path: count}}
# 原则：守卫独立调用互不影响；异常静默退出（失败放行）
# 创建：2026-08-19 ｜ 更新：2026-10-01（v0.8：加「域外」模式 X·audit_search_kb 路径订正为装机态
#   扁平(原指向作者态 知识联邦引擎/scripts/ ⇒ 装机态必缺件)·可达口径订正为「有对象可守」）
set -u

MC="[记忆共享中心]"
PATROL_DIR="$MC/脚本中心/.patrol"
SCRIPTS="$MC/脚本中心"
MEM_DIR="$HOME/.trae-cn/memory/projects"   # Trae Work 会话数据（工具目录·⛔非记忆中心）
STATE="$PATROL_DIR/audit_state_traework.json"
LOCK_DIR="$PATROL_DIR/audit_once_traework.lock"
LOG="$PATROL_DIR/patrol_traework.log"
TMP=$(mktemp /tmp/patrol_traework_XXXX.jsonl)
DENOM=12                                   # SSOT §二·七 分母（该端应接守卫数）
WIRED=0; SKIPPED=0
trap 'rm -f "$TMP"; rmdir "$LOCK_DIR" 2>/dev/null' EXIT
mkdir -p "$PATROL_DIR"

# ── 守卫名册（唯一数据源）：名|脚本中心相对路径|模式(T=转录依赖/S=独立/X=域外不跑)|参数 ──
#    路径一律「装机态」形态（脚本中心扁平·⛔非作者态 开发工具/ 子目录形态）
ROSTER=(
  "route_audit|route_audit.py|T|--src traework"
  "guard_audit|route_guard_audit.py|T|--src traework"
  "audit_search_kb|audit_search_kb.py|X|"
  "rule_three_layer_guard|rule_three_layer_guard.py|S|"
  "card_id_guard|card_id_guard.py|X|hook"
  "session_memory_quality_guard|session_memory_quality_guard.py|S|"
  "trae_isolation_guard|trae_isolation_guard.py|S|--check"
)
IN_DENOM=" route_audit guard_audit audit_search_kb rule_three_layer_guard card_id_guard "

# 并发锁（mkdir 原子）：launchd 与手动同时触发只跑一个
mkdir "$LOCK_DIR" 2>/dev/null || exit 0

# 心跳（监督：对账 E 账检查连续性，>60min=断链告警）
date +%Y-%m-%dT%H:%M:%S > "$PATROL_DIR/last_run_traework.ts"

# ── 接入率静态可达统计（可达 = 本机「有对象可守」的名册件）──
#    域外件(mode=X)分母仍计(SSOT 5 件)但⛔不计可达、⛔不计缺件（不谎报成可达/缺件）
AVAIL=0; MISSING=""; EXCLUDED=""
for _row in "${ROSTER[@]}"; do
  IFS='|' read -r _n _rel _m _a <<< "$_row"
  case "$IN_DENOM" in
    *" $_n "*)
      if [ "$_m" = "X" ]; then
        EXCLUDED="$EXCLUDED $_n"
      elif [ -f "$SCRIPTS/$_rel" ]; then AVAIL=$((AVAIL+1)); else MISSING="$MISSING $_n"; fi
      ;;
  esac
done

# 状态加载（多会话独立计数：{sessions: {path: count}}）
load_state() {
  python3 -c "
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding='utf-8'))
    print(json.dumps(d.get('sessions',{})))
except Exception:
    print('{}')" "$STATE" 2>/dev/null || echo '{}'
}
STATE_JSON=$(load_state)

# 守卫调用：转录依赖（循环内·需 PAYLOAD）
run_guard() {
  local name="$1"; shift
  local path="$1"; shift
  if [ ! -f "$path" ]; then
    echo "[$(date +%H:%M:%S)] $name SKIP（缺件·降级不阻塞·端用户无此件）: $path" >> "$LOG"
    SKIPPED=$((SKIPPED+1)); return 0
  fi
  echo "$PAYLOAD" | env -u PYTHONHOME -u PYTHONPATH python3 "$path" "$@" >> "$PATROL_DIR/$name.out" 2>&1
  local rc=$?
  WIRED=$((WIRED+1))
  if [ $rc -eq 2 ]; then
    # ⚠️ 变量后接中文标点必须 ${var}——bash 3.2 会把全角括号吃进标识符 → set -u unbound
    #    （恰在"真告警(rc=2)"时崩、告警日志丢失＝最坏假阴性·2026-08-29 根治）
    echo "[$(date +%H:%M:%S)] $name exit=${rc}（格式/结论不合规→告警）" >> "$LOG"
    rc=0
  else
    echo "[$(date +%H:%M:%S)] $name exit=$rc" >> "$LOG"
  fi
  return $rc
}

# 守卫调用：独立（循环外·只读文件/扫文件名·无需转录）
run_guard_standalone() {
  local name="$1"; shift
  local path="$1"; shift
  if [ ! -f "$path" ]; then
    echo "[$(date +%H:%M:%S)] $name SKIP（缺件·降级不阻塞·端用户无此件）: $path" >> "$LOG"
    SKIPPED=$((SKIPPED+1)); return 0
  fi
  env -u PYTHONHOME -u PYTHONPATH python3 "$path" "$@" >> "$PATROL_DIR/$name.out" 2>&1
  local rc=$?
  WIRED=$((WIRED+1))
  echo "[$(date +%H:%M:%S)] $name exit=$rc" >> "$LOG"
}

# 遍历 24h 内所有 session_memory jsonl（⛔不只看最新——多会话覆盖）
while IFS= read -r LATEST; do
  [ -f "$LATEST" ] || continue
  [ "$(find "$LATEST" -mmin +1440 2>/dev/null)" ] && continue  # 超 24h 跳过

  # 消息总数（记录数）+ 已审计数（新会话→0）
  TOTAL=$(wc -l < "$LATEST" 2>/dev/null | tr -d ' ') || continue
  [ "$TOTAL" -gt 0 ] || continue
  COUNT=$(python3 -c "
import json,sys
try:
    d=json.loads(sys.argv[1])
    print(int(d.get(sys.argv[2],0)))
except Exception:
    print(0)" "$STATE_JSON" "$LATEST" 2>/dev/null || echo 0)
  [ "$TOTAL" -le "$COUNT" ] && continue  # 无增量

  # 增量转换：后 (TOTAL-COUNT) 条记录 → 伪 transcript JSONL（intent→user / actions+outcome→assistant）
  python3 - "$LATEST" "$TMP" "$COUNT" << 'PYEOF' || continue
import json, sys
src, dst, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
out = []
n = 0
try:
    with open(src, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if n < start:
                n += 1
                continue
            n += 1
            intent = (e.get('intent') or '').strip()
            outcome = (e.get('outcome') or '').strip()
            actions = e.get('actions') or []
            act_txt = '；'.join(actions) if isinstance(actions, list) else str(actions)
            if intent:
                out.append({'role': 'user', 'message': {'content': [{'type': 'text', 'text': intent}]}})
            if act_txt.strip():
                out.append({'role': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'actions: ' + act_txt}]}})
            if outcome:
                out.append({'role': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'outcome: ' + outcome}]}})
    if not out:
        sys.exit(0)
    with open(dst, 'w', encoding='utf-8') as f:
        for m in out:
            f.write(json.dumps(m, ensure_ascii=False) + '\n')
except Exception:
    sys.exit(0)
PYEOF
  [ -s "$TMP" ] || continue

  PAYLOAD=$(printf '{"transcript_path": "%s"}' "$TMP")

  # 转录依赖组（名册 mode=T·逐件判存降级）
  for _row in "${ROSTER[@]}"; do
    IFS='|' read -r _n _rel _m _a <<< "$_row"
    [ "$_m" = "T" ] || continue
    run_guard "$_n" "$SCRIPTS/$_rel" $_a
  done

  # 更新该会话审计指针（其余会话状态保留）——循环外统一落盘
  STATE_JSON=$(python3 -c "
import json,sys
d=json.loads(sys.argv[1]); d[sys.argv[2]]=int(sys.argv[3]); print(json.dumps(d))
" "$STATE_JSON" "$LATEST" "$TOTAL" 2>/dev/null || echo "$STATE_JSON")
done < <(find "$MEM_DIR" -name "session_memory_*.jsonl" -mmin -1440 2>/dev/null | head -20)

# 独立组（名册 mode=S·每次 patrol 都跑·逐件判存降级）
for _row in "${ROSTER[@]}"; do
  IFS='|' read -r _n _rel _m _a <<< "$_row"
  [ "$_m" = "S" ] || continue
  case "$_n" in
    # card_id_guard 需宿主标识（立场卡防撞分源）
    card_id_guard) CARD_GUARD_HOST=traework run_guard_standalone "$_n" "$SCRIPTS/$_rel" $_a ;;
    *)             run_guard_standalone "$_n" "$SCRIPTS/$_rel" $_a ;;
  esac
done

# 状态落盘（{sessions: {...}}）
[ -n "$STATE_JSON" ] && printf '{"sessions": %s}' "$STATE_JSON" > "$STATE" 2>/dev/null

# ── 接入率自报（机械计数·⛔不虚报）──
#   两个口径⛔不混：①「可达」= 静态判存（名册件落盘且非域外·本机有对象可守）
#   ②「实跑」= 本轮真被调用的件数（转录依赖件无增量时不计入——⛔不把判存当实跑）
#   作者态 5/12 系作者机有库；端用户态 3/12（2 件域外无对象）
{
  echo "[$(date +%Y-%m-%dT%H:%M:%S)] 可达接入率 = ${AVAIL}/${DENOM}（SSOT 分母·静态判存·本机有对象可达口径）"
  echo "    本轮实跑守卫 ${WIRED} 件（真被调用·与可达数⛔非同义）· 调用时缺件跳过 ${SKIPPED} 件"
  [ -n "$MISSING" ] && echo "    缺件（应装未落盘·⚠️需排查）:${MISSING}"
  [ -n "$EXCLUDED" ] && echo "    域外不计可达（本机无守对象·设计不装·⛔非故障）:${EXCLUDED}"
} >> "$LOG"
printf '%s/%s\n' "$AVAIL" "$DENOM" > "$PATROL_DIR/接入率_traework.txt"

exit 0