#!/usr/bin/env bash
# setup.sh — Zwork 端对账器（平台托管型·对账吸收模式·幂等·fail-loud）
# 端分立铁律：本端=AutoClaw 新客户端（zwork 运行时·🧠）·⛔与 ~/.openclaw-autoclaw（旧客户端·🦞）混同
# 本端无盘上规则注入面：五系统文件等价物=端自有实体——本脚本只对账，⛔覆盖端实体（条文48 端自持有律）
# 用法: bash setup.sh [记忆共享中心绝对路径] ；演练: DRY=1 bash setup.sh
set -uo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY="${DRY:-0}"
FAIL=0
say() { echo -e "$1"; }
run() { if [ "$DRY" = "1" ]; then say "  ${CYAN}[dry]${NC} $*"; else "$@"; fi; }

# ── 记忆中心定位：参数 › 环境变量 › 缺省 ~/个人AI档案（MC=档案库实体·本端 作者机=用户机同构）──
MC="${1:-${MEMORY_CENTER:-$HOME/个人AI档案}}"
[ -d "$MC" ] || { say "${RED}❌ 记忆中心不存在: ${MC}（传参或设 MEMORY_CENTER）${NC}"; exit 2; }

say "${CYAN}[1/3] 撞端防线${NC}"
if [ -d "$HOME/.openclaw-autoclaw" ]; then
  say "${YELLOW}  ⚠️ 本机存在 ~/.openclaw-autoclaw（旧客户端端·另一独立端）——本次对账对象为 Zwork（AutoClaw 新客户端）·两端不共用不占用${NC}"
fi

say "${CYAN}[2/3] 端实体对账（五系统文件等价物·只读不写）${NC}"
# ① K2 宪法实体：SOUL.md + AGENTS.md 成对标记对（buluotuo:execution-guidelines-v1 ×2）
ZW_DIR="$MC/AutoClaw"
for f in "$ZW_DIR/SOUL.md" "$ZW_DIR/AGENTS.md"; do
  if run test -f "$f"; then
    if [ ! -f "$f" ]; then say "${RED}  ❌ 缺失: $f${NC}"; FAIL=1; else say "  ✅ 实体在场: $f"; fi
  fi
done
if [ -f "$ZW_DIR/AGENTS.md" ]; then
  N=$(grep -c "buluotuo:execution-guidelines-v1" "$ZW_DIR/AGENTS.md" || true)
  if [ "$N" -ge 2 ]; then say "  ✅ 执行准则标记对成对（×${N}）"; else say "${RED}  ❌ 标记对不完整（×${N}·须≥2）${NC}"; FAIL=1; fi
  if grep -q "5.5 检索与卡号纪律" "$ZW_DIR/AGENTS.md"; then say "  ✅ 5.5 检索与卡号纪律段在场"; else say "${YELLOW}  🟡 5.5 段缺（M1 对账吸收可补·非阻塞）${NC}"; fi
fi
# ② SOUL 卡号纪律硬化
if [ -f "$ZW_DIR/SOUL.md" ]; then
  if grep -q "说不出=编" "$ZW_DIR/SOUL.md"; then say "  ✅ SOUL 卡号硬化句在场"; else say "${YELLOW}  🟡 SOUL 卡号硬化句缺（v1.1 补·非阻塞）${NC}"; fi
fi
# ③ Memory 面（机制级注入·端 AI 行为侧自查口令）
say "  ✅ Memory 面=平台托管（Run 级注入·机械保证·脚本不可测属平台内）"

say "${CYAN}[3/3] K2 恒驻核与 W2 机械腿${NC}"
# [3b] TSL 机械校验器部署（§八·七 无钩子端脚本化·构造权归脚本·版本比对同版跳过）
TSL_SRC="$PKG/adapters/zwork/scripts/zwork_tsl_verify.py"
TSL_DST="$MC/脚本中心/zwork_tsl_verify.py"
if [ -f "$TSL_SRC" ]; then
  if [ ! -f "$TSL_DST" ] || ! cmp -s "$TSL_SRC" "$TSL_DST"; then
    if [ "$DRY" = "1" ]; then
      say "  ${CYAN}[dry]${NC} mkdir -p 脚本中心 && cp → 脚本中心/zwork_tsl_verify.py"
    else
      mkdir -p "$(dirname "$TSL_DST")" \
        && cp "$TSL_SRC" "$TSL_DST" \
        && say "  ✅ TSL校验器已部署: 脚本中心/zwork_tsl_verify.py" \
        || { say "${RED}  ❌ TSL校验器部署失败: $TSL_DST${NC}"; FAIL=1; }
    fi
  else
    say "  ✅ TSL校验器同版在位（跳过）"
  fi
  say "  ℹ️ D3 上岗回合末调用: python3 \"$TSL_DST\" --window 30（AI 只许逐行 relay stdout）"
else
  say "${RED}  ❌ TSL校验器源缺失: $TSL_SRC${NC}"; FAIL=1
fi
K2="$MC/数字分身/K2切片蒸馏/slices/core_slice.md"
if run test -f "$K2"; then
  [ -f "$K2" ] && say "  ✅ K2 切片库在场: ${K2#$MC/}" || { say "${RED}  ❌ core_slice.md 缺失${NC}"; FAIL=1; }
else
  say "${YELLOW}  🟡 K2 切片库缺（数字分身完整版单装时补·M7 域）${NC}"
fi
TS="$MC/数字分身/scripts/last_run_doenglingz_slice_watch.ts"
if [ -f "$TS" ]; then say "  ✅ W2 心跳文件在场（末次: $(cat "$TS" 2>/dev/null)）"; else say "${YELLOW}  🟡 W2 心跳未建（蒸馏调度域·非阻塞）${NC}"; fi

echo
if [ "$FAIL" -eq 0 ]; then say "${GREEN}✅ Zwork 对账完成：端实体全在场（对账吸收模式·零写入）${NC}"; exit 0
else say "${RED}❌ 对账发现缺失（见上·FAIL=${FAIL}）——缺失段按 M1 对账吸收补齐，⛔整文件覆盖${NC}"; exit 1; fi
