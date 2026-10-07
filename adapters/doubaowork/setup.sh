#!/usr/bin/env bash
# doubaowork-adapter-setup.sh — 豆包办公端部署
#
# ## 本端为什么特殊（别照搬别的端）
#
# 豆包办公**没有规则目录、没有 alwaysApply 机制、没有 hook 事件**。
# 规则唯一常驻通道是「设置 → 工作任务偏好指令」这个**文本框**——平台每次工作任务自动注入框里的文字。
# ⇒ 本端部署做五件事：
#   ① 五系统文件模板落盘到 ~/.doubaowork-config/（T0 指令强制 AI 每次新会话首条 Read）
#   ② 从模板生成待粘贴文本 doubaowork-paste.md（用户复制粘贴，不手抄——手抄必漏字）
#   ③ 2 个端专属 Skill 到点必装（直部署S1豆包user_skills·⛔不进MC共享目录·其他端不可见）
#   ④ TSL机械校验脚本部署到MC/脚本中心/（童灵D3上岗时AI调用·构造权归脚本不归AI）
#   ⑤ 自检：五系统文件在位·paste 非空·关键段齐全·⛔ 不含私人内容·Skill 可达·TSL脚本可达
#
# ⚠️ **诚实标注**：本脚本⛔ 不能替用户点那个保存按钮。
#    装完仍需用户手动粘贴+保存。INSTALL 状态表据此标注为
#    「✅进包（需手动粘贴 1 步）」，⛔ 不写"✅完整"——那是虚假承诺。
#
# ## 用法
#   bash setup.sh [记忆共享中心绝对路径]
#   演练零写入: DRY=1 bash setup.sh  或  bash setup.sh --dry-run
#
# ## 设计: fail-loud + 幂等 + 增量不覆盖 + DRY 零写入
set -uo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
AD="$PKG/adapters/doubaowork"
OUT="${DOENGLINGZ_CONFIG_DIR:-$HOME/.doubaowork-config}"
DST="$OUT/doubaowork-paste.md"
DRY="${DRY:-0}"
FAIL=0

# ── 参数解析：--dry-run（参数通道）+ 记忆中心路径（$1 或 $2，跳过 --dry-run）──
_MC_ARG=""
for a in "$@"; do
  if [ "$a" = "--dry-run" ]; then DRY=1; else _MC_ARG="$a"; fi
done
if [ "$DRY" = "1" ]; then
  echo -e "${CYAN}[dry-run] 演练模式：展示将做什么，⛔ 一个字节都不写。真装请去掉 --dry-run/DRY 重跑。${NC}"
fi

# ── 记忆中心定位：参数 › MEMORY_CENTER/BULUOTUO_MEMORY_CENTER › 探测（⛔ 不写死任何作者目录名）──
_buluotuo_mc() {
  if [[ -n "${BULUOTUO_MEMORY_CENTER:-}" ]]; then printf '%s' "$BULUOTUO_MEMORY_CENTER"; return; fi
  local d
  for d in "$HOME"/*/.hermes/doenglingz "$HOME"/*/.workbuddy/doenglingz "$HOME"/.workbuddy/doenglingz; do
    if [[ -f "$d/runtime_paths.json" ]]; then
      python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('archive_root',''))" "$d" 2>/dev/null
      return
    fi
  done
  for d in "$HOME"/*/; do
    [[ -d "${d}开发工具" || -d "${d}脚本中心" || -d "${d}记忆规则" || -d "${d}核心层" ]] || continue
    printf '%s' "${d%/}"; return
  done
  printf '%s' ""
}
MC="${_MC_ARG:-${MEMORY_CENTER:-$(_buluotuo_mc)}}"

# ── 豆包 user_skills 目录定位（多 profile 检测·默认 Default）──
_doubao_user_skills() {
  local base="$HOME/Library/Application Support/DoubaoWork"
  if [ -d "$base/Default/.doubaowork/agent_mode/workspace/.user_skills" ]; then
    printf '%s' "$base/Default/.doubaowork/agent_mode/workspace/.user_skills"; return
  fi
  for p in "$base"/*/; do
    if [ -d "${p}.doubaowork/agent_mode/workspace/.user_skills" ]; then
      printf '%s' "${p}.doubaowork/agent_mode/workspace/.user_skills"; return
    fi
  done
  printf '%s' "$base/Default/.doubaowork/agent_mode/workspace/.user_skills"
}
US="$(_doubao_user_skills)"

say() { printf '%s\n' "$*"; }
run() { if [ "$DRY" -eq 1 ]; then say "  [dry] $*"; else "$@"; fi; }

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
        echo -e "  ${YELLOW}[skip] ${nm}（失效软链且源缺失）${NC}"
      fi
    fi
  elif [ -e "$link" ]; then
    echo -e "  ${YELLOW}[keep] $nm 已是实体文件，未覆盖（尊重用户已有·本机真身优先）${NC}"
  elif [ -e "$src" ]; then
    ln -s "$src" "$link"; echo -e "  ${GREEN}[OK] ${nm}${NC}"
  else
    echo -e "  ${YELLOW}[skip] ${nm}（源缺失）${NC}"
  fi
}

echo -e "${CYAN}=== 豆包办公端部署（五系统文件 + paste + 端专属Skill） ===${NC}"
say "    配置根: $OUT$( [ "$DRY" = "1" ] && echo '  (dry-run·零写入)' )"
say "    记忆中心: ${MC:-<未找到>}"
say "    user_skills: $US"

# ── [1/6] 记忆中心指纹检测（fail-loud·防装到通用空目录）──────────────────────
if [ ! -d "$MC" ] || [ ! -f "$MC/核心层/CORE.md" ]; then
  echo -e "${RED}[X] 记忆中心不存在或非布洛陀指纹: ${MC:-<未找到>}${NC}"
  echo -e "    请先完成布洛陀五层记忆系统安装，再跑本脚本（或显式传记忆中心绝对路径）。"; exit 1
fi
FP_FAIL=0
fp_file() {
  local f="$MC/$1" kw="${3:-}"
  if [ ! -s "$f" ]; then echo -e "${RED}  [缺] $2: $1${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  if [ -n "$kw" ] && ! grep -q "$kw" "$f"; then echo -e "${RED}  [疑] $2: $1（无\"$kw\"关键词）${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  echo -e "${GREEN}  [OK] $2${NC}"
}
fp_file "核心层/CORE.md" "L1核心层"
fp_file "记忆规则/用户基本规则-铁律版.md" "行为规则" "铁律"
if [ "$FP_FAIL" -gt 0 ]; then
  echo -e "${RED}[X] $MC 不是完整的布洛陀五层记忆系统（$FP_FAIL 项指纹缺失）${NC}"; exit 1
fi
echo -e "${GREEN}[1/6] 记忆中心指纹通过: $MC${NC}"

# ── [2/6] 五系统文件模板落盘（已存在不覆盖·占位符替换）──────────────────────
echo -e "${YELLOW}[2/6] 五系统文件模板落盘（SOUL/IDENTITY/USER/MEMORY/customPrompt）...${NC}"
run mkdir -p "$OUT"
SYS_FAIL=0
for t in SOUL.md IDENTITY.md USER.md MEMORY.md customPrompt.md; do
  src="$AD/templates/$t"
  dst="$OUT/$t"
  if [ ! -f "$src" ]; then
    echo -e "${RED}  [X] 包内模板缺失: $t${NC}"; SYS_FAIL=$((SYS_FAIL+1)); continue
  fi
  if [ "$DRY" = "1" ]; then
    if [ -e "$dst" ]; then say "  [dry] ${t} 已存在·将跳过（不覆盖用户真身）"; else say "  [dry] 落盘 ${t}（占位符替换后）"; fi
    continue
  fi
  if [ -e "$dst" ]; then
    echo -e "  ${YELLOW}[keep] ${t} 已存在，未覆盖（如需更新请手动比对 templates/${t}）${NC}"
  else
    # 占位符双形态：[记忆共享中心]（install_scripts.PLACEHOLDER 单一真源）+ {记忆共享中心}（zcode 系模板形态）
    sed -e "s|\[记忆共享中心\]|$MC|g" -e "s|{记忆共享中心}|$MC|g" "$src" > "$dst.tmp" && mv "$dst.tmp" "$dst"
    echo -e "  ${GREEN}[OK] 装 $t${NC}"
  fi
done
if [ "$SYS_FAIL" -gt 0 ]; then
  echo -e "${RED}[X] 五系统文件模板缺 $SYS_FAIL 件——⛔ 拒绝装残（T0 指令会 Read 不存在的文件）${NC}"; exit 2
fi
echo -e "${GREEN}[2/6] 五系统文件就位（$OUT/）${NC}"

# ── [3/6] paste.md 从模板生成（占位符替换·每次重新生成确保最新）──────────────
echo -e "${YELLOW}[3/6] 待粘贴文本从模板生成...${NC}"
PASTE_TPL="$AD/templates/paste.md"
if [ ! -f "$PASTE_TPL" ]; then
  echo -e "${RED}[X] 包内 paste 模板缺失: $PASTE_TPL${NC}"; exit 2
fi
if [ "$DRY" = "1" ]; then
  say "  [dry] 将写出 ${DST}（从 templates/paste.md·占位符替换）+ ${DST}.readme"
  bytes=0
else
  run mkdir -p "$OUT"
  sed -e "s|\[记忆共享中心\]|$MC|g" -e "s|{记忆共享中心}|$MC|g" "$PASTE_TPL" > "${DST}.tmp" && mv "${DST}.tmp" "$DST"
  # 说明文件：给人看的，⛔ 不用粘
  cat > "${DST}.readme" <<EOF
# 豆包办公端 · 粘贴说明（**这个文件不用粘**）

待粘贴的内容在同目录的：$(basename "$DST")

## 怎么做

1. 豆包办公 → 左下角点头像 → 设置 → 工作模式任务设置 → 工作任务偏好指令
2. **全选打开 \`$(basename "$DST")\` 的全部内容**（只粘这个文件，⛔ 别粘本说明）
3. 粘贴 → 保存

## ⚠️ 关于字数上限

豆包官方已公布该文本框上限为 10000 字符。
本文件生成的待粘贴文本约 \$(wc -m < "$DST" | tr -d ' ') 字，剩余空间充足，可放心追加个人偏好。
如果以后内容增加接近上限，安装器会自动警告。

## 怎么确认真的生效了

随便问一句：**「你的准则第一条是什么？」**

- 答得出「退一步再动 / 先说假设」⇒ 生效了
- 答不出 ⇒ 没粘上或没保存 ⇒ 回设置里再看一眼那个框

## 为什么这一步必须你手动做

豆包办公**没有规则目录、没有 alwaysApply 机制**（其它端把文件放进目录就自动生效）。
规则唯一常驻通道就是「设置」里那个文本框，平台每次任务自动注入框里的文字。
⇒ 脚本能把文本准备好，**但点那个保存按钮只能你来**。

## 五系统文件已就位

安装器已把五系统文件部署到 \`$OUT/\`：
- SOUL.md（品格+愿景+格式模板）
- IDENTITY.md（身份+署名）
- USER.md（用户画像+童灵core_slice/L6）
- MEMORY.md（导航仪+触发开关+路径索引）
- customPrompt.md（执行准则#10-13+铁律恒驻）

paste.md 首条 T0 指令会强制 AI 每次新会话首条 Read 这五件。
EOF
  bytes=$(wc -c < "$DST" | tr -d ' ')
fi
say "[3/6] 待粘贴文本 ${bytes} 字节（+ 同名 .readme 说明）"

# ── [4/7] Skill 到点必装（端专属2个直部署S1 + 通用10个MC真源→S1软链）──
# 设计：端专属Skill=豆包端独有资产（compatibility: doubao-work），⛔DO NOT放MC/技能配置/共享目录
#       ——其他端会扫描/软链MC/技能配置/，端专属Skill被误加载=混乱（2026-10-06 隔离令根治）
#       端专属2个直接部署到S1（豆包user_skills），通用10个仍走MC/技能配置/真源→S1软链
echo -e "${YELLOW}[4/7] Skill 到点必装（端专属2个直部署S1 + 通用10个MC真源→S1软链）...${NC}"
SK_OK=0
MC_SKILLS="${MC}/技能配置"
for s in "布洛陀-豆包办公规则" "doenglingz-slice-nav-doubao"; do
  src="${AD}/skills/${s}"
  s1_dst="${US}/${s}"
  if [ ! -d "$src" ]; then
    echo -e "${RED}  [X] 包内端专属 Skill 缺失: ${s}${NC}"; FAIL=$((FAIL+1)); continue
  fi
  # 4a. 端专属Skill直接部署到S1（豆包user_skills·不经过MC共享目录·已存在不覆盖）
  if [ "$DRY" = "1" ]; then
    say "  [dry] 部署端专属 ${s} → ${s1_dst}"
  else
    run mkdir -p "$US"
    if [ -e "$s1_dst" ]; then
      echo -e "  ${YELLOW}[keep] ${s}（S1已存在·未覆盖·尊重用户真身）${NC}"
    else
      run cp -r "$src" "$s1_dst"
      if [ -d "$s1_dst" ]; then
        # 占位符三形态：[记忆共享中心] + {记忆共享中心} + <记忆共享中心>（端专属Skill用尖括号形态）
        find "$s1_dst" -name "*.md" -type f | while read -r f; do
          sed -e "s|\[记忆共享中心\]|${MC}|g" -e "s|{记忆共享中心}|${MC}|g" -e "s|<记忆共享中心>|${MC}|g" "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
        done
        echo -e "  ${GREEN}[OK] ${s}（端专属·直部署S1·占位符已替换）${NC}"
      fi
    fi
  fi
  SK_OK=$((SK_OK+1))
done
echo -e "${GREEN}[4/7] 端专属 Skill: ${SK_OK}/2（直部署S1·不进MC共享目录·其他端不可见）${NC}"

# ── 4c/4d. 通用 Skill 部署（10个·从 references/skills/ → MC/技能配置/ → user_skills 软链）──
# 通用Skill=全端共用资产（awaken-memory-system/clock-loop/daily-buddy/good-good-study/
#   growth-box/meta-aletheia/shall-we-talk/sucair/system-logger/triwich）
# 豆包端 skill_symlink=false（不走 restore-my-skills.sh 的静态软链），由本 setup.sh 自包含部署
GEN_SKILLS=(awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich)
GEN_OK=0
for s in "${GEN_SKILLS[@]}"; do
  src="${PKG}/references/skills/${s}"
  mc_dst="${MC_SKILLS}/${s}"
  if [ ! -d "$src" ]; then
    echo -e "${RED}  [X] 包内通用 Skill 缺失: ${s}${NC}"; FAIL=$((FAIL+1)); continue
  fi
  # 4c. 部署到MC/技能配置/（统一真源·已存在不覆盖·占位符三形态替换）
  if [ "$DRY" = "1" ]; then
    say "  [dry] 部署通用 ${s} → ${mc_dst}"
  else
    run mkdir -p "$MC_SKILLS"
    if [ -d "$mc_dst" ]; then
      echo -e "  ${YELLOW}[keep] ${s}（MC/技能配置/已存在·未覆盖）${NC}"
    else
      run cp -r "$src" "$mc_dst"
      if [ -d "$mc_dst" ]; then
        find "$mc_dst" -name "*.md" -type f | while read -r f; do
          sed -e "s|\[记忆共享中心\]|${MC}|g" -e "s|{记忆共享中心}|${MC}|g" -e "s|<记忆共享中心>|${MC}|g" "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
        done
        echo -e "  ${GREEN}[OK] ${s}（通用Skill已部署到MC/技能配置/·占位符已替换）${NC}"
      fi
    fi
  fi
  # 4d. 从MC/技能配置/软链到豆包 user_skills（真源→运行时）
  if [ "$DRY" = "1" ]; then
    say "  [dry] 软链通用 ${s} → ${US}/${s}"
  else
    run mkdir -p "$US"
    safe_link "${US}/${s}" "$mc_dst"
  fi
  GEN_OK=$((GEN_OK+1))
done
echo -e "${GREEN}[4/7] 通用 Skill: ${GEN_OK}/10（真源=MC/技能配置/·运行时=user_skills软链）${NC}"

# ── [5/7] TSL机械校验脚本部署（构造权归脚本不归AI·童灵D3上岗时AI调用relay）──
# 设计哲学：数字分身设计哲学/08-会话级L7验证清单.md §十——根治＝把构造权从AI手里拿走交给脚本
# 豆包端无Stop钩子→AI主动调用脚本（非自绘），脚本机械检查L0-L7可验证部分，AI只许relay stdout
echo -e "${YELLOW}[5/7] TSL机械校验脚本部署（doubaowork_tsl_verify.py → MC/脚本中心/）...${NC}"
TSL_SRC="${AD}/scripts/doubaowork_tsl_verify.py"
TSL_DST="${MC}/脚本中心/doubaowork_tsl_verify.py"
if [ ! -f "$TSL_SRC" ]; then
  echo -e "${RED}  [X] 包内TSL脚本缺失: ${TSL_SRC}${NC}"; FAIL=$((FAIL+1))
else
  if [ "$DRY" = "1" ]; then
    say "  [dry] 部署 TSL脚本 → ${TSL_DST}"
  else
    run mkdir -p "${MC}/脚本中心"
    if [ -f "$TSL_DST" ]; then
      # 已存在：比较版本，版本不同则更新（脚本是基础设施，非用户真身，可覆盖更新）
      src_ver=$(grep -m1 '__version__' "$TSL_SRC" | sed "s/.*= *['\"]//;s/['\"].*//")
      dst_ver=$(grep -m1 '__version__' "$TSL_DST" | sed "s/.*= *['\"]//;s/['\"].*//")
      if [ "$src_ver" != "$dst_ver" ]; then
        run cp "$TSL_SRC" "$TSL_DST"
        echo -e "  ${GREEN}[OK] TSL脚本已更新（${dst_ver}→${src_ver}）${NC}"
      else
        echo -e "  ${GREEN}[=] TSL脚本已为最新（${src_ver}）${NC}"
      fi
    else
      run cp "$TSL_SRC" "$TSL_DST"
      run chmod +x "$TSL_DST"
      echo -e "  ${GREEN}[OK] TSL脚本已部署到MC/脚本中心/（v$(grep -m1 '__version__' "$TSL_SRC" | sed "s/.*= *['\"]//;s/['\"].*//")）${NC}"
    fi
  fi
fi

# ── [6/7] 自检：五系统文件在位 + paste 非空/关键段/无私人内容 + Skill 可达 + TSL脚本可达 ────
echo -e "${YELLOW}[6/7] 自检...${NC}"
if [ "$DRY" = "1" ]; then say "  [dry] 跳过自检"; else
  V_FAIL=0
  # 五系统文件在位
  for t in SOUL.md IDENTITY.md USER.md MEMORY.md customPrompt.md; do
    if [ ! -s "$OUT/$t" ]; then
      echo -e "${RED}  [X] 五系统文件缺失或为空: $t${NC}"; V_FAIL=$((V_FAIL+1))
    fi
  done
  # paste 非空+关键段
  if [ ! -s "$DST" ]; then echo -e "${RED}  [X] paste 产出为空${NC}"; V_FAIL=$((V_FAIL+1)); fi
  miss=""
  for k in "执行准则" "实事求是" "反绕过" "先看清" "T0" "SOUL" "童灵"; do
    grep -q "$k" "$DST" || miss="$miss $k"
  done
  if [ -n "$miss" ]; then
    echo -e "${RED}  [X] paste 关键段缺失：${miss}——⛔ 粘过去也是残的${NC}"; V_FAIL=$((V_FAIL+1))
  fi
  # ⛔ 私人内容闸：与包内同一判据（pkg_cleanliness_check）保持一致
  if grep -qE "$(printf '\xe5\x93\xa5')" "$DST"; then
    echo -e "${RED}  [X] paste 含私人称谓——⛔ 不可发给用户${NC}"; V_FAIL=$((V_FAIL+1))
  fi
  # 五系统文件也查私人称谓（模板脱敏校验）
  for t in SOUL.md IDENTITY.md USER.md MEMORY.md customPrompt.md; do
    if grep -qE "$(printf '\xe5\x93\xa5')" "$OUT/$t" 2>/dev/null; then
      echo -e "${RED}  [X] $t 含私人称谓——模板脱敏失败${NC}"; V_FAIL=$((V_FAIL+1))
    fi
  done
  # Skill 可达（端专属2个+通用10个=12个）
  for s in "布洛陀-豆包办公规则" "doenglingz-slice-nav-doubao" awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich; do
    if [ ! -e "$US/$s" ]; then
      echo -e "${RED}  [X] Skill 不可达: $s${NC}"; V_FAIL=$((V_FAIL+1))
    fi
  done
  # TSL脚本可达
  if [ ! -f "${MC}/脚本中心/doubaowork_tsl_verify.py" ]; then
    echo -e "${RED}  [X] TSL脚本不可达: ${MC}/脚本中心/doubaowork_tsl_verify.py${NC}"; V_FAIL=$((V_FAIL+1))
  fi
  if [ "$V_FAIL" -gt 0 ]; then
    echo -e "${RED}[X] 自检 $V_FAIL 项未过——⛔ 不可视为安装成功${NC}"; exit 1
  fi
  echo -e "${GREEN}[6/7] 自检 ✅（五系统文件在位·paste 关键段齐全·无私人内容·Skill 可达·TSL脚本可达）${NC}"
fi

# ── [7/7] 如实交付 ────────────────────────────────────────────────────────
echo -e "${GREEN}[7/7] ✅ 就绪${NC}"
if [ "$DRY" = "1" ]; then
  say ""
  say "[dry-run] 真实运行时：把 $DST 全部内容粘进「设置 → 工作模式任务设置 → 工作任务偏好指令」并保存。"
  exit 0
fi
# 统计字符数（中文按字计，非字节）+ 占比
chars=$(wc -m < "$DST" | tr -d ' ')
LIMIT=10000
pct=$(( chars * 100 / LIMIT ))
remain=$(( LIMIT - chars ))
say ""
say "⚠️ **还有 1 步必须你手动做**（本端机制使然，脚本代劳不了）："
say "   豆包办公 → 设置 → 工作模式任务设置 → 工作任务偏好指令"
say "   把 $DST 全文（共 ${chars} 字 / 上限 ${LIMIT} 字 · 已用 ${pct}% · 剩 ${remain} 字）粘进去 → 保存"
say ""
if [ "$pct" -ge 90 ]; then
  say "   🔴 警告：已用 ${pct}%，接近上限！如需追加个人偏好，请先精简 paste.md 里用不上的段落。"
elif [ "$pct" -ge 70 ]; then
  say "   🟡 提醒：已用 ${pct}%，剩余 ${remain} 字，追加个人偏好时注意不要超限。"
else
  say "   ✅ 字数充足（已用 ${pct}%），可放心在末尾追加自己的个性化偏好。"
fi
say ""
say "   五系统文件已部署到 $OUT/（T0 指令强制每次新会话首条 Read）"
say "   12 个 Skill（2端专属+10通用）已软链到 $US/"
say ""
say "   粘完请自检：随便问一句「你的准则第一条是什么」，答不上来 = 没生效。"
exit 0
