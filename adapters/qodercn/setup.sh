#!/usr/bin/env bash
# setup.sh — Qoder CN 端部署（rules 核心件=模板实体落盘 + 记忆数据软链 + 系统模板落盘 + skills 软链 + 自验证）
# v2.0（2026-10-07·Qoder CN·你令端哲学落地）：rules 四核心件从"软链包内件"升级为"模板渲染实体"——
#   装机态=本端自有实体可独立演化；旧装机软链自动升级；已存在实体⛔不覆盖（本机真身优先）。
#
# ## 分工（2026-10-03 委派链统一·条文13扩展）
#   本脚本 = 端专属件：rules/ alwaysApply 文件软链 + AGENTS.md/MEMORY.md 落盘 + skills 软链 + 自验证
#   settings.json 4事件钩子（Stop/UserPromptSubmit/PreToolUse/SessionStart + extra_hooks）
#           = 安装器标准分支注册（hooks_event=true）——本脚本 ⛔ 不碰 settings.json（防双写）
#   旧形态：本端 rules 落盘无机械路径（靠端 AI 自觉读 README）＝「✅完整」实装零端件（假绿）
#
# ## 用法
#   bash setup.sh [记忆共享中心绝对路径]
#   沙盒测试: QODERCN_HOME=/tmp/qc MEMORY_CENTER=/tmp/mc bash setup.sh /tmp/mc
#   演练零写入: DRY=1 bash setup.sh  或  bash setup.sh --dry-run（双通道·安装器委派契约）
#
# ## 设计: fail-loud + 幂等 + 增量不覆盖 + DRY 零写入
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QODERCN_HOME="${QODERCN_HOME:-$HOME/.qoder-cn}"
DRY="${DRY:-0}"
FAIL=0

# ── 参数解析：--dry-run（参数通道）+ 记忆中心路径（$1 或 $2，跳过 --dry-run）──
_MC_ARG=""
RELINK="${RELINK:-0}"
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --relink-skills) RELINK=1 ;;   # P11：Skill 落位（④）后复链巡检——建链时序倒置的补救腿
    *) _MC_ARG="$a" ;;
  esac
done
if [ "$DRY" = "1" ]; then
  echo -e "${CYAN}[dry-run] 演练模式：展示将做什么，⛔ 一个字节都不写。真装请去掉 --dry-run/DRY 重跑。${NC}"
fi

# ── 记忆中心定位：参数 › MEMORY_CENTER › 探测（⛔ 不写死任何作者目录名）──
_buluotuo_mc() {
  if [[ -n "${BULUOTUO_MEMORY_CENTER:-}" ]]; then printf '%s' "$BULUOTUO_MEMORY_CENTER"; return; fi
  local d
  for d in "$HOME"/*/.hermes/doenglingz "$HOME"/*/.workbuddy/doenglingz "$HOME"/.workbuddy/doenglingz; do
    if [[ -f "$d/runtime_paths.json" ]]; then
      python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('archive_root',''))" "$d/runtime_paths.json" 2>/dev/null
      return
    fi
  done
  for d in "$HOME"/*/; do
    [[ -d "${d}开发工具" || -d "${d}脚本中心" || -d "${d}记忆规则" ]] || continue
    printf '%s' "${d%/}"; return
  done
  printf '%s' ""
}
MC="${_MC_ARG:-${MEMORY_CENTER:-$(_buluotuo_mc)}}"

# ── safe_link <link> <src>：增量安全——⛔绝不覆盖用户实体文件；软链才修正指向；失效软链（源在）重建 ──
safe_link() {
  local link="$1" src="$2" nm; nm="$(basename "$link")"
  if [ -L "$link" ]; then
    if [ -e "$link" ]; then
      if [ "$(readlink "$link")" = "$src" ]; then echo -e "  ${GREEN}[=] ${nm}（已正确）${NC}"
      else ln -sfn "$src" "$link"; echo -e "  ${GREEN}[OK] ${nm}（更新指向）${NC}"; fi
    else
      if [ -e "$src" ]; then
        ln -sfn "$src" "$link"; echo -e "  ${GREEN}[OK] ${nm}（修复失效软链）${NC}"
      else
        echo -e "  ${YELLOW}[skip] ${nm}（失效软链且源缺失·发布口径与本机版本差异过渡态）${NC}"
      fi
    fi
  elif [ -e "$link" ]; then
    echo -e "  ${YELLOW}[keep] $nm 已是实体文件，未覆盖（尊重用户已有·本机真身优先）${NC}"
  elif [ -e "$src" ]; then
    ln -s "$src" "$link"; echo -e "  ${GREEN}[OK] $nm${NC}"
  else
    echo -e "  ${YELLOW}[skip] ${nm}（源缺失）${NC}"
  fi
}

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" = "1" ]; then say "  [dry] $*"; else "$@"; fi; }

echo -e "${CYAN}=== Qoder CN 端部署（rules 软链 + 系统模板 + skills） ===${NC}"
say "    配置根: $QODERCN_HOME$( [ "$DRY" = "1" ] && echo '  (dry-run·零写入)' )"

# ── [1/5] 记忆中心指纹检测（C12 修·2026-10-15 鸡生蛋根治）────────────────────
# 原逻辑：CORE.md 不在就 exit 1。但安装器在**部署公共资产之前**就委派本脚本
#   （install_scripts.py L2341 起·条文13扩展；L2424「委派成功 ≠ 全装完——继续走公共资产部署」），
#   全新用户此刻：L1 的 CORE.md 要到 step5 才合成、规则层 ①b 也排在委派之后、记忆 Skill 要到 step6
#   才部署 ⇒ 每次全新装机必见「❌ 端接入未完成·退出码 1」，而端专属件（rules 实体/AGENTS/MEMORY
#   全取包内模板）本来能正常落盘——假红把用户推到"真机复核"，实证见修包清单 D1。
# 修法＝⛔不放宽阈值，改**绑过程证据**分三态（S021 声明/验证二分：拿不可复制的装机进度事实判定）：
#   ① $MC 不是目录，或既无 `.install/` 又无 `核心层/CORE.md` ⇒ 这不是布洛陀记忆中心
#      （原守卫意图完整保留：防装到通用空目录/传错路径）→ exit 1
#   ② 是布洛陀记忆中心、但产出该资产的 step 检查点尚未写 ⇒ 装机中途态 → 打 ⏳ 不判红、继续落端件
#   ③ step 检查点已写而产物缺失 ⇒ 真缺失 → 判红 exit 1（原语义一字未动）
# ⛔ 不用退出码 3：安装器会把 3 播报成「仅『extensions/patrol』注册待手动收尾」
#   （L2386 `mech = cap.get("hooks_mechanism", "extensions/patrol")` 取静态默认值），
#   本端钩子走 settings.json、无 patrol——那等于把一个假红换成一句假话。
# 完整性终审仍由 step7 `verify.sh` 硬拦（§1 系统文件／§2 规则三层／§3 记忆Skill 逐项判红），
#   所以中途态放行不会让坏装机溜过去，只是不再在链路中间用未成熟状态谎报失败。
FP_FAIL=0
# C30（2026-10-15）：态①拆出「装机链内空壳态」——空目录/未创建目录在安装链语境里
#   =「还没长出来」（step1/step3 稍后建目录树、step5 才合成 CORE.md），不是「装错地方」。
#   链标志 BLT_INSTALL_CHAIN 只由安装器委派时注入（=装机过程事实·S021 声明/验证二分），
#   判据三分：链内且（不存在∨空目录）⇒ ⏳ 继续；链内但目录非空且无指纹⇒ 仍硬拒（保护不缩水）；
#   无标志（人直跑）⇒ 原态①语义一字不动。
BLT_EMPTY_MC=0
if [ "${BLT_INSTALL_CHAIN:-}" = "1" ] && { [ ! -d "$MC" ] || [ -z "$(ls -A "$MC" 2>/dev/null)" ]; }; then
  BLT_EMPTY_MC=1
  echo -e "${YELLOW}[⏳] 记忆中心尚未成型: ${MC:-<未创建>}（装机链内·step1/3/5 稍后创建目录树与核心文件·本行≠失败）${NC}"
elif [ ! -d "$MC" ] || { [ ! -d "$MC/.install" ] && [ ! -f "$MC/核心层/CORE.md" ]; }; then
  echo -e "${RED}[X] 记忆中心不存在或非布洛陀指纹: ${MC:-<未找到>}${NC}"
  if [ "${BLT_INSTALL_CHAIN:-}" = "1" ]; then
    echo -e "    目录非空却没有布洛陀指纹（记忆琥珀/engine ∧ 记忆规则）——可能指到了他端资产或无关目录。"
    echo -e "    请确认记忆中心路径；确要新建请传空目录或不存在的路径。"
  else
    echo -e "    请先完成布洛陀五层记忆系统安装，再跑本脚本（或显式传记忆中心绝对路径）。"
  fi
  exit 1
fi
MID_L1=$BLT_EMPTY_MC
if [ ! -s "$MC/核心层/CORE.md" ] && [ ! -f "$MC/.install/step5-done.md" ]; then MID_L1=1; fi
fp_file() { # <相对路径> <层说明> [关键词]
  local f="$MC/$1" kw="${3:-}"
  if [ "$MID_L1" = 1 ]; then
    echo -e "${YELLOW}  [⏳] $2: $1（step5 尚未完成·装机中途态，装完跑 step7 verify.sh 终验）${NC}"; return
  fi
  if [ ! -s "$f" ]; then echo -e "${RED}  [缺] $2: $1${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  if [ -n "$kw" ] && ! grep -q "$kw" "$f"; then echo -e "${RED}  [疑] $2: $1（无\"$kw\"关键词）${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  echo -e "${GREEN}  [OK] $2${NC}"
}
fp_file "核心层/CORE.md" "L1核心层"
fp_file "记忆规则/用户基本规则-铁律版.md" "行为规则" "铁律"
FP_SK=0
for s in awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich; do
  [ -f "$MC/技能配置/$s/SKILL.md" ] && FP_SK=$((FP_SK+1))
done
MID_SK=0
if [ "$FP_SK" -lt 8 ] && [ ! -f "$MC/.install/step6-done.md" ]; then MID_SK=1; fi
if [ "$FP_SK" -ge 8 ]; then echo -e "${GREEN}  [OK] 记忆Skill: $FP_SK/10${NC}"
elif [ "$MID_SK" = 1 ]; then echo -e "${YELLOW}  [⏳] 记忆Skill: $FP_SK/10（step6 尚未完成·装机中途态，装完跑 step7 verify.sh 终验）${NC}"
else echo -e "${RED}  [缺] 记忆Skill仅 $FP_SK/10（step6-done 已写仍缺=真缺失·期望>=8）${NC}"; FP_FAIL=$((FP_FAIL+1)); fi
if [ "$FP_FAIL" -gt 0 ]; then
  echo -e "${RED}[X] $MC 不是完整的布洛陀五层记忆系统（$FP_FAIL 项指纹缺失）${NC}"; exit 1
fi
if [ "$MID_L1" = 1 ] || [ "$MID_SK" = 1 ]; then
  echo -e "${YELLOW}[1/5] 记忆中心指纹：中途态放行（L1=$([ "$MID_L1" = 1 ] && echo "⏳" || echo "✅")／Skill=$([ "$MID_SK" = 1 ] && echo "⏳" || echo "✅")）——端专属件继续落盘；⛔ 本行≠已装完，完整性由 step7 verify.sh 终审${NC}"
else
  echo -e "${GREEN}[1/5] 记忆中心指纹通过: $MC${NC}"
fi

# ── [2/5] rules/ 常驻注入：核心四件=模板渲染**实体落盘**（端哲学 2026-10-07 你令：系统文件本端实体，⛔软链借用）──
#   记忆数据三件(快照/问卷/题目库)仍软链=数据共享单一真源(v0.9 既定)，两种形态分治
echo -e "${YELLOW}[2/5] rules/ 落位（核心四件模板实体 + 记忆数据软链）...${NC}"
run mkdir -p "$QODERCN_HOME/rules"
_R_FAIL=0
render_entity() { # <src> <dst>：占位渲染→tmp+mv 原子写；已存在实体不覆盖；本装机旧软链升级为实体；用户自建链不动
  local src="$1" dst="$2" nm tgt
  nm="$(basename "$dst")"
  if [ -L "$dst" ]; then
    tgt="$(readlink "$dst")"
    case "$tgt" in
      "$AD_DIR/rules/$nm"|*adapters/qodercn/rules/"$nm") rm -f "$dst" ;;  # 旧装机态(本包留下的链)→升级实体
      *) echo -e "  ${YELLOW}[keep] $nm 为用户自建软链($tgt)，不动${NC}"; return ;;
    esac
  elif [ -e "$dst" ]; then
    echo -e "  ${YELLOW}[keep] $nm 已是实体文件，未覆盖（本机真身优先）${NC}"; return
  fi
  sed -e "s|\[记忆共享中心\]|$MC|g" -e "s|{记忆共享中心}|$MC|g" "$src" > "$dst.tmp" && mv "$dst.tmp" "$dst"
  # 待填显形闸（2026-10-07 D3 轮·锚 S561/S802）：人设占位 {称呼}{Q24} 等全链无填装腿——
  #   装后如实报数，⛔静默把原始占位符当正常交付；不判红（模板含占位=设计态·答配合成腿另立项）
  local pend
  pend="$(grep -oE '\{[^{}]+\}' "$dst" 2>/dev/null | grep -cv "记忆共享中心" || true)"
  if [ "$pend" -gt 0 ]; then
    echo -e "  ${YELLOW}[待填] ${nm} 含 ${pend} 个答题占位符（{称呼}等·答配合成腿未接·当前为原始形态）${NC}"
  fi
  echo -e "  ${GREEN}[OK] ${nm} 渲染落位（实体）${NC}"
}
for r in core-identity.md core-soul.md core-user.md execution-guidelines.md; do
  src="$AD_DIR/rules/$r"
  if [ ! -f "$src" ]; then echo -e "${RED}  [X] 包内模板件缺失: $r${NC}"; _R_FAIL=$((_R_FAIL+1)); continue; fi
  if [ "$DRY" = "1" ]; then say "  [dry] 模板渲染 $r → $QODERCN_HOME/rules/${r}（实体落盘）"; else render_entity "$src" "$QODERCN_HOME/rules/$r"; fi
done
# 记忆中心侧共享注入面（AGENTS.md 导航描述的 alwaysApply 面补齐·源在才链）
if [ "$DRY" = "1" ]; then
  say "  [dry] 软链 动态状态快照.md / 问卷答案汇总.md / 题目库.md ← 记忆中心对应层"
else
  [ -f "$MC/情境层/动态状态快照.md" ] && safe_link "$QODERCN_HOME/rules/动态状态快照.md" "$MC/情境层/动态状态快照.md"
  [ -f "$MC/记忆规则/问卷答案汇总.md" ] && safe_link "$QODERCN_HOME/rules/问卷答案汇总.md" "$MC/记忆规则/问卷答案汇总.md"
  [ -f "$MC/记忆规则/题目库.md" ] && safe_link "$QODERCN_HOME/rules/题目库.md" "$MC/记忆规则/题目库.md"
fi
if [ "$_R_FAIL" -gt 0 ]; then echo -e "${RED}[X] rules 承载件缺 $_R_FAIL 件——⛔ 拒绝装残${NC}"; exit 2; fi
echo -e "${GREEN}[2/5] rules 落位完成（核心四件实体 + 记忆数据软链共享面）${NC}"

# ── [3/5] AGENTS.md / MEMORY.md 系统模板落盘（已存在不覆盖·占位符替换）──
echo -e "${YELLOW}[3/5] AGENTS.md（导航仪）/ MEMORY.md（经验积累器）落盘...${NC}"
for t in AGENTS.md MEMORY.md; do
  src="$AD_DIR/templates/$t"
  dst="$QODERCN_HOME/$t"
  if [ ! -f "$src" ]; then echo -e "${RED}  [X] 包内模板缺失: $t${NC}"; FAIL=$((FAIL+1)); continue; fi
  if [ "$DRY" = "1" ]; then
    if [ -e "$dst" ]; then say "  [dry] $t 已存在·将跳过（不覆盖）"; else say "  [dry] 落盘 ${t}（占位符替换后）"; fi
    continue
  fi
  if [ -e "$dst" ]; then
    echo -e "  ${YELLOW}[keep] $t 已存在，未覆盖（如需更新请手动比对 templates/${t}）${NC}"
  else
    mkdir -p "$QODERCN_HOME"
    # 占位符双形态：[记忆共享中心]（=install_scripts.PLACEHOLDER 单一真源·46行）+ {记忆共享中心}（zcode 系模板形态·防漂移）
    sed -e "s|\[记忆共享中心\]|$MC|g" -e "s|{记忆共享中心}|$MC|g" "$src" > "$dst.tmp" && mv "$dst.tmp" "$dst"
    echo -e "  ${GREEN}[OK] 装 $t${NC}"
  fi
done
echo -e "${GREEN}[3/5] 系统模板就位${NC}"

# ── [4/5] skills/ 软链（10 个=布洛陀 v2.0 全平台包发布口径）──
echo -e "${YELLOW}[4/5] 记忆系统 Skills 软链...${NC}"
run mkdir -p "$QODERCN_HOME/skills"
SK=0
if [ "$DRY" = "1" ]; then
  say "  [dry] 软链 10 个记忆 Skill → $QODERCN_HOME/skills/（计数以真跑为准）"
else
  for s in awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich; do
    src="$MC/技能配置/$s"
    [ -f "$src/SKILL.md" ] && { safe_link "$QODERCN_HOME/skills/$s" "$src"; SK=$((SK+1)); }
  done
fi
echo -e "${GREEN}[4/5] skills 软链: $SK/10${NC}"
if [ "$RELINK" = "1" ] && [ "$DRY" != "1" ] && [ "$SK" -lt 10 ]; then
  echo -e "${RED}[4/5·relink] Skill 落位后复链仍 $SK/10 不足——⛔ rc=0 收场（P11 时序倒置判红）${NC}"
  exit 1
fi
if [ "$RELINK" != "1" ] && [ "$DRY" != "1" ] && [ "$SK" -lt 10 ]; then
  echo -e "${YELLOW}  [i] 软链 $SK/10：若记忆中心处于装机中途态，先跑 install_scripts.py --deploy-skills（④落位），再以 --relink-skills 复链巡检（P11 补救腿）${NC}"
fi

# ── [5/5] 自验证（装完必验·恒真判据免疫）──
echo -e "${YELLOW}[5/5] 自验证...${NC}"
V_FAIL=0
if [ "$DRY" = "1" ]; then
  say "  [dry] 将验证: rules/ 4 承载件可达 · AGENTS.md/MEMORY.md 在位 · skills 软链计数"
else
  for r in core-identity.md core-soul.md core-user.md execution-guidelines.md; do
    if [ -L "$QODERCN_HOME/rules/$r" ] || [ ! -f "$QODERCN_HOME/rules/$r" ]; then
      echo -e "${RED}  [X] rules/$r 非实体文件（缺失或软链残留）${NC}"; V_FAIL=$((V_FAIL+1))
    fi
  done
  [ -e "$QODERCN_HOME/AGENTS.md" ] || { echo -e "${RED}  [X] AGENTS.md 缺失${NC}"; V_FAIL=$((V_FAIL+1)); }
  [ -e "$QODERCN_HOME/MEMORY.md" ] || { echo -e "${RED}  [X] MEMORY.md 缺失（memory_root·经验积累器）${NC}"; V_FAIL=$((V_FAIL+1)); }
  NK=0; for s in awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich; do
    [ -e "$QODERCN_HOME/skills/$s" ] && NK=$((NK+1))
  done
  echo -e "  skills 软链: $NK/10"
  if [ "$V_FAIL" -eq 0 ]; then
    if [ "$MID_L1" = 1 ] || [ "$MID_SK" = 1 ]; then
      # C12：中途态不喊「自验证通过」——端载体确实落好了，但记忆资产还没长齐，
      # 喊绿就是谎报；⛔ 也不喊「失败」，因为这不是失败，是还没到那一步。
      echo -e "${YELLOW}=== [⏳] Qoder CN 端载体已落盘（rules 实体／AGENTS.md／MEMORY.md／skills 软链），记忆中心仍处装机中途态 ===${NC}"
      echo -e "  待办：装完 step5/step6 后跑 step7 的 verify.sh 做完整性终审（本脚本不替它判装完）。"
      echo -e "  生效验证：新开 Qoder CN 会话问「你是谁」→ 应自报 Qoder CN 🔮 并带署名规范。"
    else
      echo -e "${GREEN}=== [OK] Qoder CN 端部署完成·自验证通过 ===${NC}"
      echo -e "  生效验证：新开 Qoder CN 会话问「你是谁」→ 应自报 Qoder CN 🔮 并带署名规范。"
      echo -e "  注：settings.json 4 事件钩子由安装器标准分支注册（本脚本不重复注册）。"
    fi
  else
    echo -e "${RED}=== [X] 自验证 $V_FAIL 项未过——⛔ 不可视为安装成功 ===${NC}"; exit 1
  fi
fi
exit 0
