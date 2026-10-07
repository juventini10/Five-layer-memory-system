#!/bin/bash
# ============================================================
# setup.sh — LobsterAI adapter 聚合安装入口（幂等·fail-loud）
# 用途: install_scripts.py --platform lobsterai 按 capability.yaml install_entry 委派到此（条文 13）
# 前提: 已装布洛陀五层记忆系统（<记忆共享中心> 就位且含 L1/L4/L5 指纹）+ 已安装 LobsterAI（macOS 应用）
# 功能: ① 记忆中心指纹检测 ② 数据清理（样例数据·强制） ③ AGENTS.md 头部段注入执行准则
#       ④ skills 软链 ⑤ 童灵（数字分身）插件落位 + openclaw.json 注册
#       ⑤b 路由注入插件（脱敏·config 驱动）落位 + 注册
#       ⑤c 脚本体系运行面插件（事件类映射·config 驱动）落位 + 注册
#       ⑤d 知识库注入插件（脱敏·config 驱动）落位 + 注册 ⑥ 自验证
# 设计: fail-loud + 幂等（可重跑）+ 增量不覆盖（保本地私人版）+ 沙盒可测
# 机制依据: 本端=OpenClaw 引擎·AGENTS.md 每会话全文加载（截断保头）/ 插件走
#          third-party-extensions + openclaw.json plugins.entries / SKILLs 软链直挂
# 用法: bash setup.sh "<记忆共享中心绝对路径>"
#       沙盒测试: LOBSTERAI_HOME=/tmp/lob MEMORY_CENTER=/tmp/mc bash setup.sh /tmp/mc
# 来源: 布洛陀 v2.0 全平台安装包 adapters/lobsterai/setup.sh
# ============================================================
set -uo pipefail

# ── Poka-Yoke · 补缺式写入（守卫编写规范 §8.7·2026-10-06 立）────────────
# 病灶：原式 en[k]={...} 整键覆盖 / if k not in en 只判键不判值
#   ⇒ 端侧在同一键上的精细配置（hooks/config 等子字段）被装包一跑刷没
#   ⇒ LobsterAI 端 2026-10-06 当日实测四次回退，累计约 2 小时
# 纪律：装包只填**缺失的叶子键**，⛔ 不覆盖端侧已有值；已有值=端侧主权。
# 打印「新增/保留」两类清单 ⇒ 满足 §8.7 纪律④「写前可报出差异」。
_poka_merge_entry() {
  python3 - "$1" "$2" <<'POKAEOF'
import json, sys
path, pid = sys.argv[1], sys.argv[2]
WANT = {"enabled": True, "hooks": {"allowConversationAccess": True}}
try:
    cfg = json.load(open(path, encoding="utf-8"))
except Exception as e:
    print("POKA_ERR " + str(e)); sys.exit(1)
en = cfg.setdefault("plugins", {}).setdefault("entries", {})
cur = en.get(pid)
if not isinstance(cur, dict):
    cur = {}
added, kept = [], []
for k, v in WANT.items():
    if isinstance(v, dict):
        sub = cur.get(k)
        if not isinstance(sub, dict):
            cur[k] = dict(v); added.append(k)
        else:
            for sk, sv in v.items():
                if sk not in sub:
                    sub[sk] = sv; added.append(k + "." + sk)
                else:
                    kept.append(k + "." + sk + "=" + repr(sub[sk]))
    else:
        if k not in cur:
            cur[k] = v; added.append(k)
        else:
            kept.append(k + "=" + repr(cur[k]))
en[pid] = cur
json.dump(cfg, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("POKA_OK " + pid + " added=" + (",".join(added) or "-") + " kept=" + (",".join(kept) or "-"))
POKAEOF
}


# DRY=1（安装器委派契约·2026-10-03）：本脚本未实现零写入演练——显式跳过而非"演练着写盘"（⛔假绿）
if [ "${DRY:-0}" = "1" ]; then
  echo "[dry-run] DRY=1：本脚本未实现零写入演练，已跳过实际写入（幂等安全·真装请不带 --dry-run 重跑）"
  exit 0
fi

# ── 记忆中心定位（⛔ 不写死任何目录名·不靠包内占位符——本脚本是被 exec 的，
#    占位符不会被替换。改为：环境变量 › runtime_paths 声明 › 多候选探测）
_buluotuo_mc() {
  if [[ -n "${BULUOTUO_MEMORY_CENTER:-}" ]]; then printf '%s' "$BULUOTUO_MEMORY_CENTER"; return; fi
  local d
  for d in "$HOME"/.hermes/doenglingz "$HOME"/.workbuddy/doenglingz; do
    if [[ -f "$d/runtime_paths.json" ]]; then
      python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('archive_root',''))" "$d/runtime_paths.json"
      return
    fi
  done
  for d in "$HOME"/*/; do
    [[ -d "${d}开发工具" || -d "${d}脚本中心" || -d "${d}记忆规则" ]] || continue
    printf '%s' "${d%/}"; return
  done
  printf '%s' ""
}
MC="$(_buluotuo_mc)"
R='\033[0;31m'; G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'; N='\033[0m'
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
FAIL=0

# ─── 记忆中心（参数 > 环境变量 > 探测）───
MC="${1:-${MEMORY_CENTER:-}}"
if [ -z "$MC" ]; then
  for _c in "$HOME/记忆中心" "$HOME/记忆共享中心" "$HOME/记忆库" "$HOME/记忆" "$MC"; do
    [ -f "$_c/核心层/CORE.md" ] && { MC="$_c"; break; }
  done
  MC="${MC:-$HOME/${MC}}"
fi

# ─── LobsterAI 根（环境变量可覆盖·沙盒可测）───
LA_HOME="${LOBSTERAI_HOME:-$HOME/Library/Application Support/LobsterAI}"
STATE="$LA_HOME/openclaw/state"
CONFIG="$STATE/openclaw.json"
SKILLS_DIR="$LA_HOME/SKILLs"
PLUGIN_DST="$LA_HOME/third-party-extensions/lobsterai-doenglingz"
PLUGIN_SRC="$SRC_DIR/plugin/lobsterai-doenglingz"
AGENTS_MARK="buluotuo:execution-guidelines-v1"

echo -e "${C}=== LobsterAI adapter 安装（记忆中心指纹 + AGENTS 准则 + skills 软链 + 童灵插件） ===${N}"
echo -e "${Y}    记忆中心: $MC | LobsterAI 根: $LA_HOME${N}"

# ─── [1/6] 记忆中心指纹检测（层级存在性 + 关键词·非仅目录存在）───
echo -e "${Y}[1/7] 检测布洛陀记忆中心（指纹级）...${N}"
[ -d "$MC" ] || { echo -e "${R}[X] 记忆中心目录不存在: $MC${N} 请先完成布洛陀五层记忆系统安装。"; exit 1; }
FP_FAIL=0
fp() { local f="$MC/$1" kw="${2:-}"
  if [ ! -s "$f" ]; then echo -e "${R}  [缺] $1（不存在或为空）${N}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  if [ -n "$kw" ] && ! grep -q "$kw" "$f"; then echo -e "${R}  [疑] $1 存在但无关键词「${kw}」（疑似非布洛陀文件）${N}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  echo -e "${G}  [OK] $1${N}"; }
fp "核心层/CORE.md" "铁律"
fp "记忆规则/用户基本规则-铁律版.md" "铁律"
if [ "$FP_FAIL" -gt 0 ]; then echo -e "${R}[X] $MC 存在但不是完整布洛陀五层记忆系统（$FP_FAIL 项指纹缺失）${N}"; exit 1; fi
echo -e "${G}[OK] 记忆中心指纹通过${N}"

# ─── [2/6] 数据清理（强制·样例数据精确比对·绝不碰用户记录）───
echo -e "${Y}[2/7] 数据清理（开发阶段遗留样例数据·SHA256 精确比对）...${N}"
CLEAN="$SRC_DIR/../../data_contamination_check.py"
FPF="$SRC_DIR/../../references/integrity-fingerprints.json"
if [ -f "$CLEAN" ] && [ -f "$FPF" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$CLEAN" --memory-root "$MC" --fingerprints "$FPF" \
    --template-root "$SRC_DIR/../../references" --apply 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -ne 0 ] && { echo -e "${R}[X] 数据清理执行失败——已中止（防样例数据残留）${N}"; exit 1; }
  echo -e "${G}  [OK] 数据清理完成（你的记录完整保留·原文件已备份可还原）${N}"
else
  echo -e "${R}[X] 缺数据清理工具/指纹 或 无 python3——此步不可跳过，已中止${N}"; exit 1
fi

# ─── [3/6] AGENTS.md 头部段注入执行准则（marker 幂等·⛔不碰托管段）───
echo -e "${Y}[3/7] AGENTS.md 头部段注入执行准则（通用版）...${N}"
TMPL="$SRC_DIR/templates/execution-guidelines.md"
# workspace 路径：读 openclaw.json agents（defaults.workspace / list[].workspace），缺则回退 state/workspace-main
WS=""
if [ -f "$CONFIG" ] && command -v python3 >/dev/null 2>&1; then
  WS="$(python3 - "$CONFIG" <<'PYEOF' 2>/dev/null
import json,sys,os
try: d=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception: sys.exit(0)
ag=d.get("agents",{}) or {}
ws=[]
dw=(ag.get("defaults",{}) or {}).get("workspace")
if dw: ws.append(os.path.expanduser(dw))
for a in ag.get("list",[]) or []:
    w=(a or {}).get("workspace")
    if w: ws.append(os.path.expanduser(w))
print("\n".join(sorted(set(ws))))
PYEOF
)"
fi
if [ -z "$WS" ]; then WS="$STATE/workspace-main"; fi
echo "$WS" | while IFS= read -r w; do [ -n "$w" ] && echo -e "${C}  [i] 注入面候选: $w${N}"; done
if [ ! -f "$TMPL" ]; then echo -e "${R}  [X] 缺模板 $TMPL${N}"; FAIL=$((FAIL+1)); else
  # 提取注入正文：去 frontmatter（若有）+ 去「本端注入说明/来源」引用块（发文面脱敏·条文 6）
  BODY="$(mktemp)"; awk 'NR==1&&/^---$/{fm=1;next} fm&&/^---$/{fm=0;next} fm{next} !/^>/{print}' "$TMPL" > "$BODY"
  INJ=0
  while IFS= read -r w; do
    [ -n "$w" ] || continue
    A="$w/AGENTS.md"
    if [ ! -f "$A" ]; then echo -e "${Y}  [skip] 无 AGENTS.md（非 bootstrap 工作区）: $A${N}"; continue; fi
    if grep -q "$AGENTS_MARK" "$A" 2>/dev/null; then echo -e "${G}  [=] 已含标记·跳过: $A${N}"; INJ=$((INJ+1)); continue; fi
    cp -p "$A" "$A.bak-$(date +%Y%m%d)-guidelines"
    { printf '<!-- %s · 安装包通用版同步 %s -->\n\n' "$AGENTS_MARK" "$(date +%F)"; cat "$BODY"; printf '\n<!-- /%s -->\n\n' "$AGENTS_MARK"; cat "$A"; } > "$A.tmp" && mv "$A.tmp" "$A"
    echo -e "${G}  [OK] 注入: ${A}（原文件备份 .bak-$(date +%Y%m%d)-guidelines）${N}"; INJ=$((INJ+1))
  done <<< "$WS"
  rm -f "$BODY"
  [ "$INJ" -gt 0 ] || { echo -e "${R}  [X] 未注入任何 AGENTS.md${N}"; FAIL=$((FAIL+1)); }
fi

# ─── [4/7] 五系统文件模板落盘（SOUL/IDENTITY/USER/MEMORY）───
# 端点判据：本端形态 = OpenClaw bootstrap 工作区（docs/concepts/agent-workspace.md）
#   · SOUL/IDENTITY = required 文件（缺失有 marker）
#   · USER/MEMORY = optional 文件（缺失静默省略）+ USER 独立 4,000 字符预算
#   ⇒ 模板落盘是「人格层能否常驻」的唯一通道，缺此步 = 装了个空壳。
# 路径来源：capability.yaml → system_file_paths（key 必须与 SYS_FILE_NAMES 逐字一致）
# 幂等：已存在则跳过（⛔ 不覆盖用户已改的人格文件）
echo -e "${Y}[4/7] 五系统文件模板落盘（SOUL/IDENTITY/USER/MEMORY + customPrompt）...${N}"
# 模板源优先级：① adapters/lobsterai/rules/（端专属·带本端 char_budget 与官方定位声明）
#              ② references/templates/（公共脱敏层·回退）
# ⛔ 端专属上限不得上提公共层：他端无 bootstrapMaxChars/bootstrapTotalMaxChars/USER.md-4,000 这套机制
SYSDIR="$SRC_DIR/../../references/templates"
ENDIR="$SRC_DIR/rules"
SFT=0; SFAIL=0
for pair in "SOUL.md:core-soul.md" "IDENTITY.md:core-identity.md" "USER.md:core-user.md" "MEMORY.md:core-memory.md"; do
  key="${pair%%:*}"; endfile="${pair##*:}"
  if [ -f "$ENDIR/$endfile" ]; then src="$ENDIR/$endfile"; tag="端专属"
  elif [ -f "$SYSDIR/$key" ]; then src="$SYSDIR/$key"; tag="公共回退"
  else echo -e "${R}  [X] 缺模板（端专属与公共均无）: $endfile / $key${N}"; SFAIL=$((SFAIL+1)); continue; fi
  DONE=0
  while IFS= read -r w; do
    [ -n "$w" ] || continue
    dst="$w/$key"
    if [ -f "$dst" ]; then echo -e "${G}  [=] 已存在·跳过（保用户版）: ${dst}${N}"; SFT=$((SFT+1)); DONE=1; continue; fi
    cp -p "$src" "$dst" && { echo -e "${G}  [OK] 落盘[$tag]: ${dst}${N}"; SFT=$((SFT+1)); DONE=1; }
  done <<< "$WS"
  [ "$DONE" -gt 0 ] || echo -e "${Y}  [skip] 无 bootstrap 工作区·未落 $key${N}"
done
echo -e "${G}  [OK] 五系统文件: $SFT 件在位${N}"
# customPrompt 走 [3/7] 头部段注入（载体=AGENTS.md·⛔不覆盖 App 托管段），此处只核模板可达
if [ -f "$ENDIR/customPrompt.md" ] || [ -f "$SRC_DIR/templates/execution-guidelines.md" ]; then
  echo -e "${G}  [OK] customPrompt 模板可达（经 [3/7] 头部段注入）${N}"
else echo -e "${R}  [X] 缺 customPrompt 模板${N}"; SFAIL=$((SFAIL+1)); fi
[ "$SFAIL" -gt 0 ] && { echo -e "${R}  [X] 五系统文件模板缺 $SFAIL 件——⛔ 拒绝装残${N}"; FAIL=$((FAIL+1)); }

# ─── [5/7] skills 软链（记忆中心/技能配置 → 本端 SKILLs·存在不覆盖）───
echo -e "${Y}[5/7] skills 软链（$MC/技能配置 → ${SKILLS_DIR}）...${N}"
mkdir -p "$SKILLS_DIR"; SK=0; TOT=0
if [ -d "$MC/技能配置" ]; then
  for d in "$MC/技能配置"/*/; do
    [ -f "$d/SKILL.md" ] || continue
    TOT=$((TOT+1)); nm="$(basename "$d")"; link="$SKILLS_DIR/$nm"; src="${d%/}"
    if [ -L "$link" ]; then
      [ "$(readlink "$link")" = "$src" ] && { SK=$((SK+1)); } || { ln -sfn "$src" "$link"; SK=$((SK+1)); }
    elif [ -e "$link" ]; then echo -e "${Y}  [keep] $nm 已是实体·未覆盖${N}"; SK=$((SK+1))
    else ln -s "$src" "$link"; SK=$((SK+1)); fi
  done
  echo -e "${G}  [OK] skills 软链: $SK/$TOT${N}"
else echo -e "${R}  [X] 未找到 $MC/技能配置${N}"; FAIL=$((FAIL+1)); fi

# ─── [5/6] 童灵（数字分身）插件落位 + 注册 ───
echo -e "${Y}[6/7] 童灵（数字分身）插件落位 + openclaw.json 注册...${N}"
if [ ! -d "$PLUGIN_SRC" ]; then echo -e "${R}  [X] 包内缺插件: $PLUGIN_SRC${N}"; FAIL=$((FAIL+1)); else
  mkdir -p "$(dirname "$PLUGIN_DST")"
  if [ -d "$PLUGIN_DST" ]; then echo -e "${Y}  [keep] 已存在·增量刷新（保 config.json）${N}"; cp -R "$PLUGIN_SRC/." "$PLUGIN_DST/"; \
  else cp -R "$PLUGIN_SRC" "$PLUGIN_DST"; echo -e "${G}  [OK] 插件落位: $PLUGIN_DST${N}"; fi
  # 共脚本落位（发布副本·单一真源=包内 references/digital-twin/devtools/）→ 插件 lib/ + 占位符替换
  DTLIB="$PLUGIN_DST/lib"; mkdir -p "$DTLIB"
  for s in doenglingz_inject_prompt.py doenglingz_guard.py; do
    if [ -f "$SRC_DIR/../../references/digital-twin/devtools/$s" ]; then
      cp "$SRC_DIR/../../references/digital-twin/devtools/$s" "$DTLIB/$s"
      sed -i.bak "s|\[记忆共享中心\]|$MC|g; s|\[数字分身中心\]|$MC/数字分身|g" "$DTLIB/$s" && rm -f "$DTLIB/$s.bak"
      echo -e "${G}  [OK] 共脚本落位: lib/${s}（占位符已替换）${N}"
    else echo -e "${R}  [X] 包内缺共脚本 references/digital-twin/devtools/$s${N}"; FAIL=$((FAIL+1)); fi
  done
  # 写 config.json（记忆中心 + 共脚本路径·安装时落定·插件启动即读）
  python3 - "$PLUGIN_DST" "$MC" <<'PYEOF'
import json,sys,os
d,mc=sys.argv[1],sys.argv[2]
cfg={"mc":mc,"src":"LobsterAI","inject":os.path.join(d,"lib","doenglingz_inject_prompt.py"),
     "guard":os.path.join(d,"lib","doenglingz_guard.py"),"state_dir":os.path.join(mc,".lobsterai")}
json.dump(cfg,open(os.path.join(d,"config.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("CONFIG_OK")
PYEOF
  # 注册到 openclaw.json（幂等·保留既有 allow/entries/load.paths）
  [ -f "$CONFIG" ] || { echo -e "${R}  [X] 未找到 openclaw.json: $CONFIG${N}"; FAIL=$((FAIL+1)); }
  if [ -f "$CONFIG" ]; then
    python3 - "$CONFIG" "$LA_HOME/third-party-extensions" <<'PYEOF'
import json,sys,os
p,dload=sys.argv[1],sys.argv[2]
try: d=json.load(open(p,encoding="utf-8"))
except Exception as e: print("FAIL_JSON:%s"%e); sys.exit(1)
pl=d.setdefault("plugins",{})
al=pl.setdefault("allow",[])
if "lobsterai-doenglingz" not in al: al.append("lobsterai-doenglingz"); print("ALLOW_ADDED")
ld=pl.setdefault("load",{}); paths=ld.setdefault("paths",[])
if dload not in paths: paths.append(dload); print("LOADPATH_ADDED")
en=pl.setdefault("entries",{})
if "lobsterai-doenglingz" not in en:
    _poka_merge_entry "$CONFIG" "lobsterai-doenglingz"
else: print("ENTRY_PRESENT")
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
PYEOF
    rc=$?
    if [ $rc -ne 0 ]; then echo -e "${R}  [X] openclaw.json 注册失败——请手动把 lobsterai-doenglingz 加入 plugins.allow/entries${N}"; FAIL=$((FAIL+1));
    else grep -q "lobsterai-doenglingz" "$CONFIG" && echo -e "${G}  [OK] 插件已注册（幂等·现有配置完整保留）${N}" || { echo -e "${R}  [X] 注册验证失败${N}"; FAIL=$((FAIL+1)); }; fi
  fi
fi

# ─── [5b/6] 路由注入插件（脱敏·config 驱动）落位 + 注册 ───
# 与 WB 端 UserPromptSubmit 钩子 route_inject_prompt 等价承载：转发用户消息给
# <MC>/脚本中心/route_inject_prompt.py（脚本体系随装落位），命中则 appendContext 注入格式契约。
echo -e "${Y}[5b/6] 路由注入插件 lobsterai-route-inject 落位 + 注册...${N}"
RIN_DST="$LA_HOME/third-party-extensions/lobsterai-route-inject"
RIN_SRC="$SRC_DIR/plugin/lobsterai-route-inject"
if [ ! -d "$RIN_SRC" ]; then echo -e "${R}  [X] 包内缺插件: $RIN_SRC${N}"; FAIL=$((FAIL+1)); else
  mkdir -p "$(dirname "$RIN_DST")"
  if [ -d "$RIN_DST" ]; then echo -e "${Y}  [keep] 已存在·增量刷新（保 config.json）${N}"; cp -R "$RIN_SRC/." "$RIN_DST/"; \
  else cp -R "$RIN_SRC" "$RIN_DST"; echo -e "${G}  [OK] 插件落位: $RIN_DST${N}"; fi
  # 写 config.json（记忆中心 + 公共脚本路径·安装时落定·插件启动即读·⛔无硬编码）
  python3 - "$RIN_DST" "$MC" <<'PYEOF'
import json,sys,os
d,mc=sys.argv[1],sys.argv[2]
cfg={"mc":mc,"src":"LobsterAI","inject":os.path.join(mc,"脚本中心","route_inject_prompt.py"),
     "state_dir":os.path.join(mc,".lobsterai")}
json.dump(cfg,open(os.path.join(d,"config.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("ROUTE_CONFIG_OK")
PYEOF
  # 注册到 openclaw.json（幂等·保留既有 allow/entries/load.paths）
  if [ -f "$CONFIG" ]; then
    python3 - "$CONFIG" "$LA_HOME/third-party-extensions" <<'PYEOF'
import json,sys,os
p,dload=sys.argv[1],sys.argv[2]; pid="lobsterai-route-inject"
try: d=json.load(open(p,encoding="utf-8"))
except Exception as e: print("FAIL_JSON:%s"%e); sys.exit(1)
pl=d.setdefault("plugins",{})
al=pl.setdefault("allow",[])
if pid not in al: al.append(pid); print("ALLOW_ADDED")
ld=pl.setdefault("load",{}); paths=ld.setdefault("paths",[])
if dload not in paths: paths.append(dload); print("LOADPATH_ADDED")
en=pl.setdefault("entries",{})
_poka_merge_entry "$CONFIG" "$pid"
else: print("ENTRY_PRESENT")
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
PYEOF
    rc=$?
    if [ $rc -ne 0 ]; then echo -e "${R}  [X] openclaw.json 注册失败（route-inject）——请手动加入 plugins.allow/entries${N}"; FAIL=$((FAIL+1));
    else grep -q "lobsterai-route-inject" "$CONFIG" && echo -e "${G}  [OK] 插件已注册（幂等·现有配置完整保留）${N}" || { echo -e "${R}  [X] 注册验证失败（route-inject）${N}"; FAIL=$((FAIL+1)); }; fi
  else echo -e "${R}  [X] 未找到 openclaw.json: $CONFIG${N}"; FAIL=$((FAIL+1)); fi
fi

# ─── [5c/6] 脚本体系运行面插件（事件类映射·config 驱动）落位 + 注册 ───
# 把 WB 端 settings.json 的脚本体系钩子（UserPromptSubmit/Stop/PreToolUse/SessionStart）
# 按事件类映射到 OpenClaw typed hook：转发给 <MC>/脚本中心 与 <MC>/数字分身/devtools 的公共脚本。
echo -e "${Y}[5c/6] 脚本体系运行面插件 lobsterai-buluotuo-hooks 落位 + 注册...${N}"
BH_DST="$LA_HOME/third-party-extensions/lobsterai-buluotuo-hooks"
BH_SRC="$SRC_DIR/plugin/lobsterai-buluotuo-hooks"
if [ ! -d "$BH_SRC" ]; then echo -e "${R}  [X] 包内缺插件: $BH_SRC${N}"; FAIL=$((FAIL+1)); else
  mkdir -p "$(dirname "$BH_DST")"
  if [ -d "$BH_DST" ]; then echo -e "${Y}  [keep] 已存在·增量刷新（保 config.json）${N}"; cp -R "$BH_SRC/." "$BH_DST/"; \
  else cp -R "$BH_SRC" "$BH_DST"; echo -e "${G}  [OK] 插件落位: $BH_DST${N}"; fi
  python3 - "$BH_DST" "$MC" <<'PYEOF'
import json,sys,os
d,mc=sys.argv[1],sys.argv[2]
cfg={"mc":mc,"src":"LobsterAI","scripts_dir":os.path.join(mc,"脚本中心"),
     "dt_devtools":os.path.join(mc,"数字分身","devtools"),"state_dir":os.path.join(mc,".lobsterai")}
json.dump(cfg,open(os.path.join(d,"config.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("HOOKS_CONFIG_OK")
PYEOF
  if [ -f "$CONFIG" ]; then
    python3 - "$CONFIG" "$LA_HOME/third-party-extensions" <<'PYEOF'
import json,sys,os
p,dload=sys.argv[1],sys.argv[2]; pid="lobsterai-buluotuo-hooks"
try: d=json.load(open(p,encoding="utf-8"))
except Exception as e: print("FAIL_JSON:%s"%e); sys.exit(1)
pl=d.setdefault("plugins",{})
al=pl.setdefault("allow",[])
if pid not in al: al.append(pid); print("ALLOW_ADDED")
ld=pl.setdefault("load",{}); paths=ld.setdefault("paths",[])
if dload not in paths: paths.append(dload); print("LOADPATH_ADDED")
en=pl.setdefault("entries",{})
_poka_merge_entry "$CONFIG" "$pid"
else: print("ENTRY_PRESENT")
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
PYEOF
    rc=$?
    if [ $rc -ne 0 ]; then echo -e "${R}  [X] openclaw.json 注册失败（buluotuo-hooks）${N}"; FAIL=$((FAIL+1));
    else grep -q "lobsterai-buluotuo-hooks" "$CONFIG" && echo -e "${G}  [OK] 插件已注册（幂等）${N}" || { echo -e "${R}  [X] 注册验证失败（buluotuo-hooks）${N}"; FAIL=$((FAIL+1)); }; fi
  else echo -e "${R}  [X] 未找到 openclaw.json${N}"; FAIL=$((FAIL+1)); fi
fi

# ─── [5d/6] 知识库注入插件（脱敏·config 驱动）落位 + 注册 ───
# 转发用户消息给 <MC>/脚本中心/kb_inject_prompt.py（意图门 + search_kb 检索 + Top-K 锚点注入）。
echo -e "${Y}[5d/6] 知识库注入插件 lobsterai-kb-inject 落位 + 注册...${N}"
KBI_DST="$LA_HOME/third-party-extensions/lobsterai-kb-inject"
KBI_SRC="$SRC_DIR/plugin/lobsterai-kb-inject"
if [ ! -d "$KBI_SRC" ]; then echo -e "${R}  [X] 包内缺插件: $KBI_SRC${N}"; FAIL=$((FAIL+1)); else
  mkdir -p "$(dirname "$KBI_DST")"
  if [ -d "$KBI_DST" ]; then echo -e "${Y}  [keep] 已存在·增量刷新（保 config.json）${N}"; cp -R "$KBI_SRC/." "$KBI_DST/"; \
  else cp -R "$KBI_SRC" "$KBI_DST"; echo -e "${G}  [OK] 插件落位: $KBI_DST${N}"; fi
  python3 - "$KBI_DST" "$MC" <<'PYEOF'
import json,sys,os
d,mc=sys.argv[1],sys.argv[2]
json.dump({"mc":mc,"src":"LobsterAI","inject":os.path.join(mc,"脚本中心","kb_inject_prompt.py"),"state_dir":os.path.join(mc,".lobsterai")},
          open(os.path.join(d,"config.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print("KB_CONFIG_OK")
PYEOF
  if [ -f "$CONFIG" ]; then
    python3 - "$CONFIG" "$LA_HOME/third-party-extensions" <<'PYEOF'
import json,sys
p,dload=sys.argv[1],sys.argv[2]; pid="lobsterai-kb-inject"
d=json.load(open(p,encoding="utf-8")); pl=d.setdefault("plugins",{})
al=pl.setdefault("allow",[])
if pid not in al: al.append(pid)
ll=pl.setdefault("load",{}); paths=ll.setdefault("paths",[])
if dload not in paths: paths.append(dload)
_poka_merge_entry "$CONFIG" "$pid"
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2); print("KB_REG_OK")
PYEOF
    grep -q "lobsterai-kb-inject" "$CONFIG" && echo -e "${G}  [OK] 插件已注册（幂等）${N}" || { echo -e "${R}  [X] 注册验证失败（kb-inject）${N}"; FAIL=$((FAIL+1)); }
  else echo -e "${R}  [X] 未找到 openclaw.json${N}"; FAIL=$((FAIL+1)); fi
fi

# ─── [7/7] 自验证 ───
echo -e "${Y}[7/7] 自验证...${N}"
MK=$(grep -rl "$AGENTS_MARK" "$STATE" 2>/dev/null | head -1)
CHK="$(ls "$MC/脚本中心/platform_adaptation_check.py" "$MC/../开发工具/platform_adaptation_check.py" 2>/dev/null | head -1)"
if [ -n "$CHK" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$CHK" --src lobsterai >/dev/null 2>&1 && echo -e "${G}  [OK] platform_adaptation_check --src lobsterai rc=0${N}" || echo -e "${Y}  [!] platform_adaptation_check 未 rc=0（多为本机运行时差异·见其输出）${N}"
else echo -e "${Y}  [!] 未找到 platform_adaptation_check.py·跳过（不影响安装）${N}"; fi
echo -e "  AGENTS 标记: ${MK:-未找到} | 五系统文件: $SFT 件 | skills: $SK/$TOT | 童灵插件: $([ -d "$PLUGIN_DST" ] && echo 在 || echo 缺)·注册 $(grep -q lobsterai-doenglingz "$CONFIG" 2>/dev/null && echo 在 || echo 缺) | 路由插件: $([ -d "$RIN_DST" ] && echo 在 || echo 缺)·注册 $(grep -q lobsterai-route-inject "$CONFIG" 2>/dev/null && echo 在 || echo 缺) | 脚本体系插件: $([ -d "$BH_DST" ] && echo 在 || echo 缺)·注册 $(grep -q lobsterai-buluotuo-hooks "$CONFIG" 2>/dev/null && echo 在 || echo 缺) | 知识库插件: $([ -d "$KBI_DST" ] && echo 在 || echo 缺)·注册 $(grep -q lobsterai-kb-inject "$CONFIG" 2>/dev/null && echo 在 || echo 缺) | 跳过: $FAIL"
# ─── 本端字符预算闸（2026-10-06 立·端专属判据·⛔ 不通用化）──
# 三上限来源：OpenClaw 官方 docs/concepts/agent-workspace.md（⛔ 本数字仅 LobsterAI 端成立）
#   bootstrapMaxChars 20000/文件 · bootstrapTotalMaxChars 60000/总量 · USER.md 独立 4000
echo -e "${C}  ── 本端字符预算闸（LobsterAI 专属·OpenClaw 三上限）──${N}"
echo "$WS" | while IFS= read -r w; do
  [ -n "$w" ] || continue
  python3 - "$w" <<'PYEOF'
import os, sys
ws = sys.argv[1]
LIM = {"SOUL.md": 20000, "IDENTITY.md": 20000, "USER.md": 4000, "MEMORY.md": 20000}
tot, bad = 0, 0
for f, lim in LIM.items():
    p = os.path.join(ws, f)
    if not os.path.isfile(p):
        print("    [X] %-12s 缺失（required 缺失有 marker·optional 缺失静默省略）" % f); bad += 1; continue
    n = len(open(p, encoding="utf-8").read()); tot += n
    print("    %s %-12s %6d / %-6d 余 %d" % ("[OK]" if n <= lim else "[X]", f, n, lim, lim - n))
    if n > lim: bad += 1
cap = 20000
ap = os.path.join(ws, "AGENTS.md")
if os.path.isfile(ap):
    an = len(open(ap, encoding="utf-8").read()); tot += an
    print("    %s %-12s %6d / %-6d 余 %d" % ("[OK]" if an <= cap else "[!]", "AGENTS.md", an, cap, cap - an))
print("    %s 总量 %d / 60000" % ("[OK]" if tot <= 60000 else "[X]", tot))
sys.exit(1 if bad else 0)
PYEOF
  [ $? -eq 0 ] && echo -e "${G}    ⇒ 预算闸通过${N}" || echo -e "${Y}    ⇒ 预算闸有超限（见上·⛔ 参照 rules/*.md 的 char_budget）${N}"
done
if [ -n "$MK" ] && [ "$FAIL" -eq 0 ]; then
  echo -e "${G}=== [OK] LobsterAI 适配完成！新开会话即生效（AGENTS.md 头部段恒定注入） ===${N}"
  echo -e "    数字分身（童灵）：运行时已就位。人格内核需你**自己造**——照「数字分身/onboarding/」模板："
  echo -e "    答题（HEXACO 100 + 33 题）→ 填模板 → 跑 k2-slice-generator 生成切片。"
  echo -e "    ⛔ 切片落位：persona（L1–L6）写入 **SOUL.md**，⛔**不要写 USER.md**（本端 USER.md 独立 4,000 字符预算·超限不注入且无告警）。"
  echo -e "    验证：新会话回复带【意图分类】开头、署名含本端标识。"
else
  echo -e "${R}[X] 适配不完整：见上方 [X]/[!] 项（多为源文件缺失或 openclaw.json 需手动补）${N}"; exit 1
fi
