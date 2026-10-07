#!/bin/bash
# ============================================================
# verify.sh — ZCode 布洛陀包 接入自检 v0.2.0 (只读·可随时重跑)
# 用法: bash verify.sh   (沙盒: ZCODE_HOME=/tmp/xxx MEMORY_CENTER=/tmp/yyy bash verify.sh)
# 检查 7 组: 布洛陀指纹 / AGENTS.md注入 / skills软链 / Stop钩子(三态+注册面) / 隐私残留 / 分身钩子(advisory) / 路由落点
# v0.2.0 (2026-10-06):
#   [4/6] 三态判据: 用户机态(HOOK_DST可执行) / T0迁移态(正本在Skill路由引擎) / 墓碑兜底态 —— 修 v0.1.1 两假红
#   注册面判据: command 含 route_unknown_unknown.py 即 registered(不再强绑旧落盘位)
#   [5b/6] 注册面 7 件对齐 config.json SSOT(doenglingz_guard 共脚本 v1.2 · twin 台账 2 件 10-03 纳管)
# 退出码 0 = 全过
# ============================================================
set -uo pipefail

_buluotuo_mc() {
  if [[ -n "${BULUOTUO_MEMORY_CENTER:-}" ]]; then printf '%s' "$BULUOTUO_MEMORY_CENTER"; return; fi
  local d
  for d in "$HOME"/.hermes/doenglingz "$HOME"/.workbuddy/doenglingz; do
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
MC="$(_buluotuo_mc)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_CENTER="${MEMORY_CENTER:-}"
if [ -z "$MEMORY_CENTER" ]; then
  for _c in "$HOME/个人AI档案" "$HOME/共享中心" "$HOME/记忆中心" "$MC"; do
    if [ -f "$_c/核心层/CORE.md" ]; then MEMORY_CENTER="$_c"; break; fi
  done
  MEMORY_CENTER="${MEMORY_CENTER:-$HOME/${MC}}"
fi
ZCODE_HOME="${ZCODE_HOME:-$HOME/.zcode}"
AGENTS="$ZCODE_HOME/AGENTS.md"; CONFIG="$ZCODE_HOME/cli/config.json"
HOOK_DST="$ZCODE_HOME/hooks/route_unknown_unknown.py"
SKILLS=(awaken-memory-system clock-loop daily-buddy growth-box meta-aletheia shall-we-talk sucair system-logger triwich)
PASS=0; FAIL=0
ok()   { echo -e "${GREEN}  [PASS] $1${NC}"; PASS=$((PASS+1)); }
bad()  { echo -e "${RED}  [FAIL] $1${NC}"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}  [WARN] $1${NC}"; }

echo -e "${CYAN}=== ZCode 布洛陀包 接入自检 v0.2.0(只读) ===${NC}"

echo -e "${CYAN}[1/6] 布洛陀指纹${NC}"
FP=0
for f in "核心层/CORE.md" "情境层/动态状态快照.md" "潜意识层/SHADOW.md" "记忆规则/用户基本规则-铁律版.md"; do
  [ -s "$MEMORY_CENTER/$f" ] && FP=$((FP+1))
done
FPS=0
for s in "${SKILLS[@]}"; do [ -f "$MEMORY_CENTER/技能配置/$s/SKILL.md" ] && FPS=$((FPS+1)); done
if [ "$FP" -eq 4 ] && [ "$FPS" -ge 8 ]; then ok "记忆中心指纹完整(核心文件4/4 + 记忆Skill $FPS/9)"
else bad "记忆中心指纹不完整(核心 $FP/4 + Skill $FPS/9)——先完成布洛陀安装"; fi

echo -e "${CYAN}[2/6] AGENTS.md 注入文件${NC}"
if [ -f "$AGENTS" ]; then
  ok "$AGENTS 存在"
  grep -q "你的 ZCode" "$AGENTS" && ok "署名含「你的 ZCode」" || bad "AGENTS.md 无 ZCode 署名——请比对 templates/AGENTS.md"
  grep -q "你的 ZCode 🧩" "$AGENTS" || warn "署名 emoji 缺失(应为「—— 你的 ZCode 🧩」)"
else
  bad "AGENTS.md 不存在——请跑 setup.sh 或手动装 templates/AGENTS.md"
fi

echo -e "${CYAN}[3/6] 记忆 Skill 软链(~/.zcode/skills/)${NC}"
SK=0; MISS=""
for s in "${SKILLS[@]}"; do
  link="$ZCODE_HOME/skills/$s"
  if [ -L "$link" ] && [ -e "$link" ]; then SK=$((SK+1))
  elif [ -d "$link" ] && [ -f "$link/SKILL.md" ]; then SK=$((SK+1))
  else MISS="$MISS $s"; fi
done
if [ "$SK" -ge 8 ]; then ok "记忆Skill在册: $SK/9"
else bad "记忆Skill仅 $SK/9 (期望>=8)·缺失:$MISS"; fi

echo -e "${CYAN}[4/6] 未知未知路由 Stop 钩子(三态)${NC}"
HOOK_MAIN_CAND="$MEMORY_CENTER/开发工具/Skill路由引擎/scripts/route_unknown_unknown.py"
if [ -x "$HOOK_DST" ]; then
  ok "钩子脚本就位可执行: $HOOK_DST"
  if grep -q "\[记忆共享中心\]" "$HOOK_DST"; then bad "钩子脚本含未替换占位符——残留将写不进悬置区"
  else ok "路径占位符已替换"; fi
elif [ -x "$HOOK_MAIN_CAND" ]; then
  ok "正本在册(Skill路由引擎·2026-10-04 T0迁移态); 旧位墓碑兜底=$HOOK_DST"
elif [ -f "$HOOK_DST" ]; then
  warn "旧位仅墓碑桩(exit 0 兜底)且正本不在 $MEMORY_CENTER/开发工具——建议核对迁移态"
else
  bad "钩子脚本缺失: ${HOOK_DST}——请跑 setup.sh"
fi
if [ -f "$CONFIG" ]; then
  V=$(python3 - "$CONFIG" <<'PYEOF' 2>&1
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    print("JSONERR", e); raise SystemExit
h = d.get("hooks", {})
print("ENABLED", "yes" if h.get("enabled") else "no")
stop = h.get("events", {}).get("Stop", [])
hit = any("route_unknown_unknown.py" in x.get("command", "")
          for g in stop if isinstance(g, dict)
          for x in g.get("hooks", []) if isinstance(x, dict))
print("REGISTERED", "yes" if hit else "no")
PYEOF
)
  echo "$V" | grep -q "ENABLED yes" && ok "hooks.enabled=true(钩子运行器已启用)" || bad "hooks.enabled 未开启——config-file hooks 默认禁用,ZCode 钩子全不跑"
  echo "$V" | grep -q "REGISTERED yes" && ok "Stop 钩子已注册(route_unknown_unknown.py)" || bad "Stop 钩子未注册——请跑 setup.sh 或手动追加"
  echo "$V" | grep -q "JSONERR" && bad "config.json 解析失败: $V"
else
  bad "config.json 不存在: ${CONFIG}——请跑 setup.sh"
fi

echo -e "${CYAN}[5/6] 隐私残留(随包脱敏门禁·扫包内文件)${NC}"
if [ -f "$PKG_DIR/privacy/desensitize-guard.sh" ]; then
  if bash "$PKG_DIR/privacy/desensitize-guard.sh" "$PKG_DIR" >/dev/null 2>&1; then
    ok "包内无个人态字面量残留(路径/用户名/邮箱)"
  else
    bash "$PKG_DIR/privacy/desensitize-guard.sh" "$PKG_DIR" 2>&1 | head -5
    bad "包内检测到个人态残留——请用官方完整包重装(勿使用来路不明的副本)"
  fi
else
  warn "脱敏门禁脚本缺失,跳过本项"
fi

echo -e "${CYAN}[5b/6] digital-twin hooks (advisory, optional)${NC}"
DT_DEV="$MEMORY_CENTER/数字分身/devtools"
V2=$(python3 - "$CONFIG" "$DT_DEV" <<'PY2' 2>/dev/null
import json, re, sys, os
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
dev = sys.argv[2]
names = []
for ev, arr in cfg.get("hooks", {}).get("events", {}).items():
    for g in arr:
        for h in g.get("hooks", []):
            for nm in re.findall(r'/([A-Za-z0-9_]+\.py)', h.get("command", "")):
                if ('oenglingz' in nm or 'position3' in nm or nm.startswith('twin_') or nm.startswith('tsl_closeout')) and nm not in names:
                    names.append(nm)
names.append('tsl_verify.py')
miss = [nm for nm in names if not os.path.isfile(os.path.join(dev, nm))]
print('NREG', len(names) - 1)
print('NMISS', len(miss))
print('NFILES', len(names))
PY2
)
NREG=$(echo "$V2" | sed -n 's/^NREG //p')
NMISS=$(echo "$V2" | sed -n 's/^NMISS //p')
NFILES=$(echo "$V2" | sed -n 's/^NFILES //p')
if [ "${NMISS:-1}" -eq 0 ] && [ -n "$NREG" ]; then
  ok "twin hook files ${NFILES}/件 deployed (数字分身/devtools)"
  if [ "$NREG" -eq 7 ]; then ok "twin hooks registered 7/7 (UPS 2 + Stop 5)"
  else warn "twin hooks registered ${NREG}/7 (optional -- run setup.sh)"; fi
else
  warn "twin files not deployed -- say 「装数字分身」 for full install (optional)"
fi

echo -e "${CYAN}[6/6] 路由落点${NC}"
if [ -f "$MEMORY_CENTER/未知未知/悬置区.md" ]; then ok "悬置区落点存在"
else warn "悬置区.md 不存在——AI 触发未知未知时自动创建"; fi
if [ -f "$MEMORY_CENTER/未知未知/.route_heartbeat.json" ]; then ok "路由心跳文件存在(事件驱动)"
else warn "路由心跳未创建——首次触发【🕳️ 我的未知未知】后自动生成"; fi

echo ""
echo -e "${CYAN}=== 结果: PASS=$PASS FAIL=$FAIL ===${NC}"
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}✅ 接入正常。验证效果:新开 ZCode 会话回复应带【意图分类】开头、署名「—— 你的 ZCode 🧩」;说「我美吗」测记忆唤醒。${NC}"
  exit 0
else
  echo -e "${RED}❌ $FAIL 项未过——按上方 [FAIL] 项修复后重跑。${NC}"
  exit 1
fi
