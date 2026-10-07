#!/bin/bash
# ============================================================
# ZCode 加强包 — 接入脚本 v0.1.1 (macOS / Linux)
# 前提:已装布洛陀五层记忆系统(记忆中心已就位·本脚本自动探测) + 已安装 ZCode CLI
# 功能:检测记忆中心 → AGENTS.md注入文件 → skills软链(10) → Stop钩子注册 → 分身钩子(可选) → 体检 → 自验证
# 用法: bash setup.sh   (沙盒测试: ZCODE_HOME=/tmp/xxx MEMORY_CENTER=/tmp/yyy bash setup.sh)
# 设计:fail-loud + 幂等(可重跑) + 自验证 + 增量不覆盖
# 机制依据:2026-08-30 ZCode 端实测(~/.zcode/AGENTS.md 唯一常驻注入/skills 软链放置即发现/
#          ~/.zcode/cli/config.json hooks 7事件·config-file hooks 须 enabled:true)
# ============================================================
set -uo pipefail

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
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
MEMORY_CENTER="${MEMORY_CENTER:-}"
if [ -z "$MEMORY_CENTER" ]; then
  for _c in "$HOME/共享中心" "$HOME/记忆中心" "$HOME/记忆库" "$HOME/记忆" "$MC"; do
    if [ -f "$_c/核心层/CORE.md" ]; then MEMORY_CENTER="$_c"; break; fi
  done
  MEMORY_CENTER="${MEMORY_CENTER:-$HOME/${MC}}"
fi
FAIL=0
TOOL_NAME="ZCode"; TOOL_EMOJI="🧩"
ZCODE_HOME="${ZCODE_HOME:-$HOME/.zcode}"
SKILLS_DIR="$ZCODE_HOME/skills"; HOOKS_DIR="$ZCODE_HOME/hooks"; CONFIG="$ZCODE_HOME/cli/config.json"
# 记忆 Skill 清单(10个=布洛陀 v2.0 全平台包发布口径·2026-09-30 by ZCode 增 good-good-study 对齐包内 references/skills)
# 发布版读书助手 Skill 为 sucair;旧版安装包为 reading-assistant——源缺失时自动回退(见 step4)
SKILLS=(awaken-memory-system clock-loop daily-buddy good-good-study growth-box meta-aletheia shall-we-talk sucair system-logger triwich)
FP_SKILLS=(awaken-memory-system clock-loop daily-buddy growth-box meta-aletheia shall-we-talk sucair system-logger triwich)

# safe_link <link> <src>: 增量安全——⛔绝不覆盖用户实体文件;软链才修正指向;失效软链(目标消失)重建
safe_link() {
  local link="$1" src="$2" nm; nm="$(basename "$link")"
  if [ -L "$link" ]; then
    if [ -e "$link" ]; then
      if [ "$(readlink "$link")" = "$src" ]; then echo -e "${GREEN}  [=] $nm(已正确)${NC}"
      else ln -sfn "$src" "$link"; echo -e "${GREEN}  [OK] $nm(更新指向)${NC}"; fi
    else
      if [ -d "$src" ]; then
        ln -sfn "$src" "$link"; echo -e "${GREEN}  [OK] $nm(修复失效软链·原目标已消失)${NC}"
      else
        echo -e "${YELLOW}  [skip] $nm(失效软链且源缺失·发布口径与本机版本差异过渡态)${NC}"
      fi
    fi
  elif [ -e "$link" ]; then
    echo -e "${YELLOW}  [keep] $nm 已是实体目录,未覆盖(尊重用户已有)${NC}"
  else
    ln -s "$src" "$link"; echo -e "${GREEN}  [OK] $nm${NC}"
  fi
}

echo -e "${CYAN}=== ZCode 加强包 接入 v0.1.1 ===${NC}"
echo -e "${YELLOW}    前提:需已装布洛陀五层记忆系统(记忆中心自动探测)+已安装 ZCode。未装则安全中止,不破坏任何东西。${NC}"
echo -e "${CYAN}    目标工具: $TOOL_NAME $TOOL_EMOJI | ZCode 根: $ZCODE_HOME${NC}"

echo -e "${YELLOW}[1/8] 检测布洛陀记忆中心(指纹级·非仅目录存在)...${NC}"
if [ ! -d "$MEMORY_CENTER" ]; then
  echo -e "${RED}[X] 记忆中心目录不存在: $MEMORY_CENTER${NC}"
  echo -e "    请先完成布洛陀五层记忆系统安装,再跑本脚本。"; exit 1
fi
FP_FAIL=0
fp_file() { # <相对路径> <层说明> [关键词]
  local f="$MEMORY_CENTER/$1" kw="${3:-}"
  if [ ! -s "$f" ]; then echo -e "${RED}  [缺] $2: $1 (不存在或为空)${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  if [ -n "$kw" ] && ! grep -q "$kw" "$f"; then echo -e "${RED}  [疑] $2: $1 存在但无\"$kw\"关键词(疑似非布洛陀文件)${NC}"; FP_FAIL=$((FP_FAIL+1)); return; fi
  echo -e "${GREEN}  [OK] $2: $1${NC}"
}
fp_file "核心层/CORE.md"             "L1核心层"
fp_file "情境层/动态状态快照.md"     "L4情境层"
fp_file "潜意识层/SHADOW.md"         "L5潜意识层"
fp_file "记忆规则/用户基本规则-铁律版.md" "行为规则" "铁律"
FP_SK=0
for s in "${FP_SKILLS[@]}"; do
  [ -f "$MEMORY_CENTER/技能配置/$s/SKILL.md" ] && FP_SK=$((FP_SK+1))
done
if [ "$FP_SK" -ge 8 ]; then echo -e "${GREEN}  [OK] 记忆Skill: $FP_SK/9${NC}"
else echo -e "${RED}  [缺] 记忆Skill仅 $FP_SK/9 (期望>=8)${NC}"; FP_FAIL=$((FP_FAIL+1)); fi
if [ "$FP_FAIL" -gt 0 ]; then
  echo -e "${RED}[X] $MEMORY_CENTER 存在,但不是完整的布洛陀五层记忆系统($FP_FAIL 项指纹缺失,见上)${NC}"
  echo -e "    可能只是通用目录。请先完成布洛陀初始化,再跑本脚本。"; exit 1
fi
BLZ_VER=$( (cat "$MEMORY_CENTER/.install/version" 2>/dev/null || grep -m1 "基线版本" "$MEMORY_CENTER/README.md" 2>/dev/null | grep -oE "v[0-9]+\.[0-9]+\.[0-9]+") | head -1 | tr -d '[:space:]' || true)
echo -e "${GREEN}[OK] 布洛陀指纹验证通过 | 记忆中心: $MEMORY_CENTER${BLZ_VER:+ | 布洛陀版本: $BLZ_VER}${NC}"
# ZCode 环境检测(~/.zcode 存在=CLI 已安装并运行过)
if [ ! -d "$ZCODE_HOME" ]; then
  echo -e "${RED}[X] 未探测到 ZCode 根目录: $ZCODE_HOME${NC}"
  echo -e "    请先安装 ZCode 并至少运行一次,再跑本脚本。"; exit 1
fi

echo -e "${YELLOW}[2/8] 数据清理(🔴不可跳过·强制门禁):清除开发阶段遗留样例数据(SHA256精确比对·绝不碰你的记录)...${NC}"
if [ ! -f "$PKG_DIR/privacy/release_contamination_check.py" ] || [ ! -f "$PKG_DIR/privacy/integrity-fingerprints.json" ]; then
  echo -e "${RED}[X] 数据清理工具/指纹缺失——为确保样例数据清理到位,此步不可跳过,已中止。请用完整加强包重试。${NC}"; exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}[X] 未找到 python3,数据清理无法执行(不可跳过)——已中止。请先安装 Python3 再重试。${NC}"; exit 1
fi
python3 "$PKG_DIR/privacy/release_contamination_check.py" --memory-root "$MEMORY_CENTER" \
  --fingerprints "$PKG_DIR/privacy/integrity-fingerprints.json" \
  --template-root "$PKG_DIR/privacy/decontam-templates" --apply 2>&1 | sed 's/^/  /'
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
  echo -e "${RED}[X] 数据清理执行失败——为防样例数据残留,此步不可跳过,已中止安装。${NC}"; exit 1
fi
echo -e "${GREEN}  [OK] 数据清理完成:已清理开发阶段遗留的样例数据(不是你的内容),你的记录完整保留,原文件已备份可还原${NC}"

echo -e "${YELLOW}[3/8] 检查 AGENTS.md 注入文件(~/.zcode/AGENTS.md·唯一常驻注入·实体不覆盖)...${NC}"
AGENTS="$ZCODE_HOME/AGENTS.md"
if [ -e "$AGENTS" ]; then
  echo -e "${YELLOW}  [keep] AGENTS.md 已存在,未覆盖(如需更新请手动比对 templates/AGENTS.md)${NC}"
else
  if [ -f "$PKG_DIR/templates/AGENTS.md" ]; then
    cp "$PKG_DIR/templates/AGENTS.md" "$AGENTS"
    sed -i.bak "s#{记忆共享中心}#$MEMORY_CENTER#g" "$AGENTS" && rm -f "$AGENTS.bak"
    echo -e "${GREEN}  [OK] 装 AGENTS.md (骨架·{称呼}待填)${NC}"; NEW_AGENTS=yes
  else
    echo -e "${RED}  [X] AGENTS.md 缺失且包内无模板——请用完整加强包重试${NC}"; FAIL=$((FAIL+1))
  fi
fi

echo -e "${YELLOW}[4/8] 软链记忆系统 Skills(10个=v2.0 全平台包发布口径·平台内置Skill不碰)...${NC}"
mkdir -p "$SKILLS_DIR"
SK=0
for s in "${SKILLS[@]}"; do
  src="$MEMORY_CENTER/技能配置/$s"
  if [ ! -f "$src/SKILL.md" ]; then
    # 旧版安装包兼容:发布名 sucair 缺失时回退 reading-assistant(同一读书助手Skill的曾用名)
    if [ "$s" = "sucair" ] && [ -f "$MEMORY_CENTER/技能配置/reading-assistant/SKILL.md" ]; then
      src="$MEMORY_CENTER/技能配置/reading-assistant"; echo -e "${CYAN}  [i] sucair 源缺失→回退旧发布名 reading-assistant${NC}"
    else
      echo -e "${YELLOW}  [skip] $s (源缺失·指纹门禁已保证>=8装全,个别缺失为发布口径与本机版本差异)${NC}"; continue
    fi
  fi
  safe_link "$SKILLS_DIR/$s" "$src"; [ -e "$SKILLS_DIR/$s" ] && SK=$((SK+1))
done
echo -e "${GREEN}  [OK] 记忆Skill软链: $SK/${#SKILLS[@]}${NC}"

echo -e "${YELLOW}[5/8] 安装未知未知路由 Stop 钩子(~/.zcode/hooks/ + config.json 幂等注册)...${NC}"
mkdir -p "$HOOKS_DIR" "$ZCODE_HOME/cli"
HOOK_SRC="$PKG_DIR/hooks/route_unknown_unknown.py"
HOOK_DST="$HOOKS_DIR/route_unknown_unknown.py"
if [ ! -f "$HOOK_SRC" ]; then
  echo -e "${RED}  [X] 包内钩子脚本缺失——请用完整加强包重试${NC}"; FAIL=$((FAIL+1))
else
  # 拷贝:实体文件不覆盖已是本钩子的旧拷贝;占位符每次替换为当前记忆中心路径
  if [ -f "$HOOK_DST" ] && ! [ -L "$HOOK_DST" ] && grep -q "route_unknown_unknown" "$HOOK_DST"; then
    echo -e "${YELLOW}  [keep] 钩子脚本已存在,仅刷新路径占位符${NC}"
  else
    cp "$HOOK_SRC" "$HOOK_DST"; echo -e "${GREEN}  [OK] 钩子脚本已安装${NC}"
  fi
  perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g" "$HOOK_DST" 2>/dev/null || sed -i.bak "s|\[记忆共享中心\]|$MEMORY_CENTER|g" "$HOOK_DST" && rm -f "$HOOK_DST.bak"
  chmod +x "$HOOK_DST"
  if grep -q "\[记忆共享中心\]" "$HOOK_DST"; then
    echo -e "${RED}  [X] 占位符替换失败——钩子将写不进你的悬置区${NC}"; FAIL=$((FAIL+1))
  else
    echo -e "${GREEN}  [OK] 路径占位符已替换为 $MEMORY_CENTER${NC}"
  fi
  # 注册到 config.json:幂等按脚本名匹配·保留全部现有钩子·enabled 缺失才补 true(不覆盖用户显式关闭)
  python3 - "$CONFIG" "$HOOKS_DIR" <<'PYEOF'
import json, sys, os
p = sys.argv[1]
# ── 并发写闸（2026-09-30 by ZCode·多端 setup 并发实证治理）：读-改-写全程持独占锁·close 释放 ──
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None
data = {}
if os.path.isfile(p):
    try:
        with open(p, "r", encoding="utf-8") as f: data = json.load(f)
    except Exception as e:
        print(f"FAIL_JSON:{e}"); sys.exit(1)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
enabled_missing = "enabled" not in hooks
if enabled_missing: hooks["enabled"] = True
stop = hooks.setdefault("events", {}).setdefault("Stop", [])
import sys as _sa
_hook_dir = _sa.argv[2] if len(_sa.argv) > 2 else os.path.expanduser("~/.zcode/hooks")
already = any(
    "route_unknown_unknown.py" in h.get("command", "") and (".zcode/hooks" in h.get("command", "") or _hook_dir in h.get("command", ""))
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
foreign = any(
    "route_unknown_unknown.py" in h.get("command", "") and not (".zcode/hooks" in h.get("command", "") or _hook_dir in h.get("command", ""))
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
if already:
    print("SKIPPED:registered")
else:
    if foreign:
        print("INFO:检测到其他实现的同名路由钩子,并存注册(本钩子内置盲区文本去重·不会重复写入)")
    hook_cmd = _sa.executable + " " + os.path.join(_hook_dir, "route_unknown_unknown.py")
    stop.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    print("APPENDED")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
if enabled_missing: print("ENABLED_SET")
try:
    if _lk is not None:
        _lk.close()  # close 即释放锁（POSIX fcntl/Windows 句柄锁随句柄关闭释放）
except Exception:
    pass
PYEOF
  REG=$?
  if [ $REG -ne 0 ]; then
    echo -e "${RED}  [X] config.json 解析/写入失败——请手动把本钩子追加到 $CONFIG 的 hooks.events.Stop${NC}"; FAIL=$((FAIL+1))
  else
    echo -e "${GREEN}  [OK] Stop 钩子已注册(幂等·现有钩子完整保留)${NC}"
    grep -q "route_unknown_unknown.py" "$CONFIG" && echo -e "${GREEN}  [OK] 注册验证通过${NC}" || { echo -e "${RED}  [X] 注册验证失败${NC}"; FAIL=$((FAIL+1)); }
  fi
fi

echo -e "${YELLOW}[5b/8] 数字分身钩子(可选组件·件在才挂·缺件不阻塞·条文16降级不阻塞)...${NC}"
DT_DEV="$MEMORY_CENTER/数字分身/devtools"
DT_SRC="$PKG_DIR/../../references/digital-twin/devtools"
DT_HOOKS_UPS=(doenglingz_inject_prompt.py position3_notify.py)  # tsl_echo_hook 已卸（v1.3.102 双树设计消除·⛔勿复挂）
DT_HOOKS_STOP=(doenglingz_guard.py doenglingz_level_declare_guard.py tsl_closeout_guard.py twin_verdict_ledger.py twin_changelog_guard.py)  # 2026-10-06 SSOT归一：guard_zcode分叉退役→共脚本doenglingz_guard.py（--check --src zcode与env双键见下方plan注册）·tsl_tree_hook 同卸
DT_MISSING=0
for h in "${DT_HOOKS_UPS[@]}" "${DT_HOOKS_STOP[@]}" tsl_verify.py; do
  if [ ! -f "$DT_DEV/$h" ]; then
    if [ -f "$DT_SRC/$h" ]; then
      mkdir -p "$DT_DEV"
      cp "$DT_SRC/$h" "$DT_DEV/$h"
      perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g" "$DT_DEV/$h" 2>/dev/null || sed -i.bak "s|\[记忆共享中心\]|$MEMORY_CENTER|g" "$DT_DEV/$h" && rm -f "$DT_DEV/$h.bak"
      chmod +x "$DT_DEV/$h"
      echo -e "${GREEN}  [OK] $h 已从包内部署到 数字分身/devtools/${NC}"
    else
      echo -e "${YELLOW}  [skip] $h (包内与部署面皆缺·分身为可选组件不影响核心)${NC}"; DT_MISSING=$((DT_MISSING+1))
    fi
  else
    echo -e "${GREEN}  [=] $h (部署面已在)${NC}"
  fi
done
if [ "$DT_MISSING" -eq 0 ]; then
  python3 - "$CONFIG" "$DT_DEV" <<'DTPYEOF'
import json, sys, os
p, dt_dev = sys.argv[1], sys.argv[2]
# ── 并发写闸（2026-09-30 by ZCode·多端 setup 并发实证治理）：读-改-写全程持独占锁·close 释放 ──
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None

data = {}
if os.path.isfile(p):
    with open(p, encoding="utf-8") as f: data = json.load(f)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
hooks.setdefault("enabled", True)
events = hooks.setdefault("events", {})
plan = {
    "UserPromptSubmit": ["doenglingz_inject_prompt.py", "position3_notify.py"],
    "Stop": ["doenglingz_guard.py --check --src zcode", "doenglingz_level_declare_guard.py", "tsl_closeout_guard.py", "twin_verdict_ledger.py", "twin_changelog_guard.py"],
}
for evt, names in plan.items():
    lst = events.setdefault(evt, [])
    for nm in names:
        already = any(nm in h.get("command", "") for grp in lst if isinstance(grp, dict) for h in grp.get("hooks", []) if isinstance(h, dict))
        if already:
            print(f"SKIPPED:{evt}:{nm}")
        else:
            # 2026-10-06 SSOT归一·端根显式（06 §2.2.9-补 (C)(D)）：doenglingz_ 族注册命令带 env 双键端根（防静默写 WB 根）
            _env = "DOENGLINGZ_CONFIG_DIR=$HOME/.zcode WORKBUDDY_CONFIG_DIR=$HOME/.zcode " if nm.split(" ")[0].startswith("doenglingz_") else ""
            lst.append({"hooks": [{"type": "command", "command": f"{_env}python3 {os.path.join(dt_dev, nm)}"}]})
            print(f"APPENDED:{evt}:{nm}")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
try:
    if _lk is not None:
        _lk.close()  # close 即释放锁（POSIX fcntl/Windows 句柄锁随句柄关闭释放）
except Exception:
    pass
DTPYEOF
  REG=$?
  if [ $REG -ne 0 ]; then
    echo -e "${YELLOW}  [!] config.json 写入失败——分身钩子未注册(可选组件·手动补见 INSTALL §数字分身完整版单装)${NC}"
  else
    DT_REG=0
    for h in "${DT_HOOKS_UPS[@]}" "${DT_HOOKS_STOP[@]}"; do
      grep -q "$h" "$CONFIG" && DT_REG=$((DT_REG+1))
    done
    echo -e "${GREEN}  [OK] 分身钩子注册: $DT_REG/7 (幂等·现有钩子完整保留)${NC}"
    echo -e "${CYAN}  [i] 分身激活≠装文件:完成养成链(答题→计分→造芯)后分身才活,见 INSTALL §数字分身完整版单装${NC}"
  fi
else
  echo -e "${CYAN}  [i] 分身件缺 $DT_MISSING 项——未注册钩子(避免悬空引用)。完整安装:给 AI 说「装数字分身」${NC}"
fi

echo -e "${YELLOW}[5c/8] 布洛陀通用层钩子注册(22条·脚本中心路径·幂等按名·缺件skip)...${NC}"
SC="$MEMORY_CENTER/脚本中心"
GEN_SRC="$PKG_DIR/../../references/scripts"
python3 - "$CONFIG" "$SC" "$GEN_SRC" <<'GENPYEOF'
import json, sys, os
p, sc, gen_src = sys.argv[1], sys.argv[2], sys.argv[3]
# ── 并发写闸（与 5b 同款）──
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None
data = {}
if os.path.isfile(p):
    with open(p, encoding="utf-8") as f: data = json.load(f)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
hooks.setdefault("enabled", True)
events = hooks.setdefault("events", {})
# 布洛陀通用层钩子注册表（形态=2026-09-30 作者侧 ZCode 实盘·端中立件路径→脚本中心）
PLAN = {
    "SessionStart": [("crossend_guard.py", "", "")],
    "PreToolUse": [("edit_heading_guard.py", "--hook", ""), ("skill_write_gate_guard.py", "", "")],
    "PostToolUse": [("zcode_config_guard.py", "postedit", "")],
    "UserPromptSubmit": [
        ("route_inject_prompt.py", "UserPromptSubmit", ""),
        ("route_miss_feeder.py", "", ""),
        ("kb_inject_prompt.py", "UserPromptSubmit", ""),
        ("rule_fragment_inject.py", "UserPromptSubmit", ""),
        ("session_tail_inject.py", "UserPromptSubmit", "WORKBUDDY_CONFIG_DIR=$HOME/.zcode"),
        ("zcode_title_namer.py", "UserPromptSubmit", ""),
        ("secret_key_guard.py", "UserPromptSubmit", ""),
        ("ttl_expiry_guard.py", "UserPromptSubmit", "WORKBUDDY_CONFIG_DIR=$HOME/.zcode"),
    ],
    "Stop": [
        ("audit_search_kb.py", "", ""),
        ("route_audit.py", "--src zcode", ""),
        ("route_guard_audit.py", "", ""),
        ("card_id_guard.py", "hook", "CARD_GUARD_HOST=zcode"),
        ("feedback_detect.py", "", ""),
        ("rule_three_layer_guard.py", "--deliver", ""),
        ("zcode_config_guard.py", "hook", ""),
        ("delivery_boundary_guard.py", "Stop", ""),
        ("manifest_registrar.py", "--apply --quiet", ""),
        ("triwich_closeout_guard.py", "", ""),
        ("systemlog_stophook_check.py", "", ""),
    ],
}
for evt, items in PLAN.items():
    lst = events.setdefault(evt, [])
    for item in items:
        nm, args, env = item
        # 存在性检查查包内源（脚本中心由 install_scripts 公共部署在委派后落位·
        # 钩子配置下次会话才加载→时序天然兼容·条文17 腿A：注册指向部署面+包内源验证）
        _src = os.path.join(gen_src, nm)
        if not os.path.isfile(_src):  # hooks 域件源在 references/hooks（公共部署同落脚本中心）
            _src = os.path.join(os.path.dirname(gen_src), "hooks", nm)
        if not os.path.isfile(_src):
            print(f"SKIP_MISSING:{evt}:{nm}")
            continue
        already = any(nm in h.get("command", "") for grp in lst if isinstance(grp, dict) for h in grp.get("hooks", []) if isinstance(h, dict))
        if already:
            print(f"SKIPPED:{evt}:{nm}")
            continue
        envp = env + " " if env else ""
        cmd = f"{envp}python3 {os.path.join(sc, nm)}{(' ' + args) if args else ''}"
        lst.append({"hooks": [{"type": "command", "command": cmd}]})
        print(f"APPENDED:{evt}:{nm}")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
if _lk is not None:
    try: _lk.close()
    except Exception: pass
GENPYEOF
GEN_REG=$(grep -c "APPENDED\|SKIPPED" "$CONFIG" 2>/dev/null || echo 0)
echo -e "${GREEN}  [OK] 通用层钩子注册完成(幂等·缺件显形 SKIP_MISSING)${NC}"

echo -e "${YELLOW}[6/8] 检测未知未知路由落点(悬置区+心跳)...${NC}"
HB="$MEMORY_CENTER/未知未知/.route_heartbeat.json"
if [ -f "$HB" ]; then
  echo -e "${GREEN}  [OK] 路由心跳在跑(事件驱动·闲置属正常)${NC}"
else
  echo -e "${YELLOW}  [!] 未找到路由心跳 ${HB}——首次触发一次【🕳️ 我的未知未知】即自动创建${NC}"
fi
if [ -f "$MEMORY_CENTER/未知未知/悬置区.md" ]; then
  echo -e "${GREEN}  [OK] 悬置区落点存在(未知未知/悬置区.md)${NC}"
else
  echo -e "${YELLOW}  [!] 悬置区.md 不存在——AI 触发未知未知时自动创建,或手动建空文件${NC}"
fi

echo -e "${YELLOW}[7/8] 体检:新功能/版本(缺则指路,不代装)...${NC}"
if [ ! -d "$MEMORY_CENTER/成就系统" ]; then
  echo -e "${YELLOW}  [!] 未装成就系统 → 用布洛陀安装包安装(丢安装包给 AI 说\"装成就系统\")${NC}"
else echo -e "${GREEN}  [OK] 成就系统已装${NC}"; fi
if [ ! -d "$MEMORY_CENTER/记忆琥珀" ]; then
  echo -e "${YELLOW}  [!] 未装记忆琥珀 → 布洛陀安装包 step6.5-amber-install 安装${NC}"
else
  echo -e "${GREEN}  [OK] 记忆琥珀已装${NC}"
  if [ -d "$MEMORY_CENTER/记忆琥珀/永久收藏" ]; then echo -e "${GREEN}  [OK] 记忆琥珀为双轨新版${NC}"
  else echo -e "${YELLOW}  [!] 记忆琥珀是旧版(无「永久收藏」双轨) → 用布洛陀安装包升级${NC}"; fi
fi
echo -e "${CYAN}  [i] ZCode 定时任务:如需记忆琥珀定时备份,可在对话中让 AI 用定时任务工具配置${NC}"
echo -e "${CYAN}  [i] 如需最新 Skill:去网盘下最新布洛陀安装包(含最新 skill,可单独装)${NC}"

echo -e "${YELLOW}[8/8] 自验证...${NC}"
AG_OK=no; [ -f "$AGENTS" ] && AG_OK=yes
SIGN_OK=no; grep -q "你的 ZCode" "$AGENTS" 2>/dev/null && SIGN_OK=yes
HK_FILE=no; [ -x "$HOOK_DST" ] && HK_FILE=yes
HK_REG=no; grep -q "route_unknown_unknown.py" "$CONFIG" 2>/dev/null && HK_REG=yes
EN_OK=no; python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('yes' if d.get('hooks',{}).get('enabled') else 'no')" "$CONFIG" 2>/dev/null | grep -q yes && EN_OK=yes
DT_OK=no
if [ "$DT_MISSING" -eq 0 ]; then
  DT_N=0
  for h in "${DT_HOOKS_UPS[@]}" "${DT_HOOKS_STOP[@]}"; do grep -q "$h" "$CONFIG" 2>/dev/null && DT_N=$((DT_N+1)); done
  [ "$DT_N" -eq 7 ] && DT_OK=yes
else
  DT_OK=n/a
fi
echo -e "  AGENTS.md: $AG_OK | 署名ZCode: $SIGN_OK | skills软链: $SK/${#SKILLS[@]} | 钩子脚本: $HK_FILE | 钩子注册: $HK_REG | hooks启用: $EN_OK | 分身钩子: $DT_OK(7) | 跳过: $FAIL"
if [ "$AG_OK" = yes ] && [ "$SIGN_OK" = yes ] && [ "$SK" -ge 8 ] && [ "$HK_FILE" = yes ] && [ "$HK_REG" = yes ] && [ "$EN_OK" = yes ] && [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}=== [OK] ZCode 接入完成!新开 ZCode 会话即生效 ===${NC}"
  echo -e "    验证:新会话回复应带【意图分类】开头、署名\"—— 你的 ZCode 🧩\";说\"我美吗\"测记忆唤醒;说\"小美\"测轻量模式。"
  echo -e "    待办:{称呼}占位符替换(若新装了 AGENTS.md 骨架)——对话中告诉 AI 你的称呼即可。"
else
  echo -e "${RED}[X] 接入不完整: AGENTS=$AG_OK 署名=$SIGN_OK skills=$SK(期望>=8) 钩子=$HK_FILE/$HK_REG enabled=$EN_OK 跳过=$FAIL${NC}"
  echo -e "    请检查上方 [skip]/[X]/[!] 项(多为源文件缺失=布洛陀未装全,或 config.json 需手动补)。"; exit 1
fi
