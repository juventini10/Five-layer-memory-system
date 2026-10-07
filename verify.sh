#!/bin/bash
# ============================================================
# verify.sh — 布洛陀安装包 接入自检 v1.0（只读·不改任何文件）
# 用法: bash verify.sh [--platform <端ID>]   (默认记忆中心 ~/记忆共享中心)
#       MEMORY_CENTER=/path bash verify.sh   (自定义记忆中心)
#       --platform qodercn → 落点检查按该端 capability.yaml 的 config_root（v2.0.1·多端）
# 检查项: 0)数据污染 1)系统文件 2)规则三层 3)记忆Skill 4)安装包干净度 5)版本锚点
#         3.6)派发心跳(advisory 显形·不计分·注册≠派发)
#         3.7)分身链路(抽卡→落卡→碰撞 dry-run·包能力检查·隔离沙箱)
#         3.8)养成链在位(答题页/造芯件/部署声明/INSTALL指引/蒸馏清单 五要素)
# 退出码 0=全过 非0=有问题
# 设计: 与加强包 verify.sh 同构的只读自检；污染检测调用包内 data_contamination_check.py
#       （与 INSTALL.md Step 0.5 同口径）；干净度=发布卫生验证（无作者私人称呼/无作者用户名/无运行时状态文件）
#       3.7 复用包内 twin_chain_check.py（⛔不触碰用户真实卡库·不要求已装 Phase B）
# ============================================================
set -uo pipefail
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; C='\033[0;36m'; N='\033[0m'
PASS=0; FAIL=0
ok(){ echo -e "${G}  [PASS] $1${N}"; PASS=$((PASS+1)); }
no(){ echo -e "${R}  [FAIL] $1${N}"; FAIL=$((FAIL+1)); }

PKG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# ── v2.0.1 多端配置根（2026-09-30 L3审计根治：验收门禁不覆盖非WB端）────────
# --platform <端ID> → 读 adapters/<端ID>/capability.yaml 的 config_root（如 qodercn→~/.qoder-cn）
# 不传 → ~/.workbuddy（向后兼容·与旧行为逐字一致）
PLATFORM=""
_a=("$@"); _i=0
while [ $_i -lt ${#_a[@]} ]; do
  [ "${_a[$_i]}" = "--platform" ] && PLATFORM="${_a[$((_i+1))]}"
  _i=$((_i+1))
done
if [ -n "$PLATFORM" ]; then
  _cap="$PKG_ROOT/adapters/$PLATFORM/capability.yaml"
  if [ ! -f "$_cap" ]; then echo "❌ --platform ${PLATFORM}：$_cap 不存在（占位端未接入）"; exit 2; fi
  CONFIG_ROOT="$(grep -m1 '^config_root:' "$_cap" | sed -e 's/^config_root:[[:space:]]*//' -e 's/[[:space:]]*#.*$//' | tr -d '"')"
  # ⚠️ 2026-10-03 修：旧用 `awk '{print $2}'` 取 config_root ⇒ 含空格的路径（如
  #    ~/Library/Application Support/…）被截成 "~/Library/Application" ⇒ §1.5 等落点检查全假红。
  #    ⛔ 别再对含空格路径用 awk 单字段取值。
elif [ -n "${MEMORY_CENTER:-}" ] && [ -f "$MEMORY_CENTER/.install/versions.json" ] && grep -q '"platform_installed"' "$MEMORY_CENTER/.install/versions.json"; then
  PLATFORM="$(grep -m1 '"platform_installed"' "$MEMORY_CENTER/.install/versions.json" | sed -E 's/.*: *"([^"]*)".*/\1/')"
  _cap="$PKG_ROOT/adapters/$PLATFORM/capability.yaml"
  echo "ℹ️ 未显式 --platform——按装机归属登记判定端=${PLATFORM}（install_scripts.py 写入·G2-2 根治）"
  [ -f "$_cap" ] && CONFIG_ROOT="$(grep -m1 '^config_root:' "$_cap" | sed -e 's/^config_root:[[:space:]]*//' -e 's/[[:space:]]*#.*$//' | tr -d '"')" || { echo "❌ 登记端 ${PLATFORM} 无 capability.yaml"; exit 2; }
else
  echo "⚠️ 未显式 --platform 且无装机归属登记——回落 ~/.workbuddy（向后兼容·若本机非 WB 端此检查会假红/假绿，请带 --platform）"
  CONFIG_ROOT="~/.workbuddy"
  PLATFORM="${PLATFORM:-workbuddy}"   # 2026-10-07 clock-loop真机反哺：端适配门禁需端身份，与CONFIG_ROOT同口径回退（否则 --src 空→门禁必红）
fi
[ -z "$CONFIG_ROOT" ] && CONFIG_ROOT="~/.workbuddy"
CFG_DIR="${CONFIG_ROOT/#\~/$HOME}"
# 记忆中心探测：支持多候选目录名（不同用户共享目录命名不同·避免写死单一默认值误报"未装"）
# 优先 MEMORY_CENTER 环境变量；否则按候选列表探测首个存在的目录；最后回退默认名。
if [ -n "${MEMORY_CENTER:-}" ]; then
  MC="$MEMORY_CENTER"
else
  MC=""
  # 2026-09-20 回灌群友 Windows 实测：Windows 端记忆树可在 E: 等异盘、以 Junction 挂在
  # ~/个人AI档案（C: 入口），该名是其实际可达入口。
  # 🔴 2026-10-03 根治「注释声称已做·代码没做」（声明-执行脱钩·与 awaken v8.3.0 同源病）：
  #     原注释写「候选补 $HOME/个人AI档案」，但 for 列表里根本没有这一项 ⇒ 该端永远
  #     探测失败 ⇒ CORE.md/铁律版/摘要版 三项恒假红，而实际目录一直都在。
  # ✅ 双层探测（防误层·不再靠枚举名字，靠「什么才算记忆中心」的结构特征判定）：
  #     ① 具名候选（含 个人AI档案·兑现注释承诺）
  #     ② 结构特征兜底：同时具备 核心层/CORE.md 与 记忆规则/ 两个标志物者认定为记忆中心
  #        ——要求「同时具备」而非任一，防撞名误命中（防错层）。
  for cand in "$HOME/个人AI档案" "$HOME/记忆共享中心" "$HOME/[记忆共享中心]" "$HOME/共享中心" "$HOME/记忆中心" "$HOME/布洛陀记忆中心"; do
    if [ -d "$cand" ]; then MC="$cand"; break; fi
  done
  # 具名候选全未命中 → 结构特征兜底扫描 $HOME 一层子目录
  if [ -z "$MC" ]; then
    for cand in "$HOME"/*/ ; do
      [ -d "${cand}核心层" ] && [ -d "${cand}记忆规则" ] && [ -s "${cand}核心层/CORE.md" ] && { MC="${cand%/}"; break; }
    done
  fi
  if [ -z "$MC" ]; then MC="$HOME/记忆共享中心"; fi
  [ -d "$MC" ] || echo "⚠️ 记忆中心未探测到（候选全未命中·结构特征兜底亦未命中）·下游检查将报缺失——装好后可用 MEMORY_CENTER=<路径> 显式指定"
fi

# Windows Git Bash 路径归一（2026-09-20 回灌群友实测）：/c/... 形态传给原生 Windows
# Python 可能被解析成 d:\c\... —— 有 cygpath 时统一转 C:/ 盘符形态（bash 自身两种形态通吃）。
if command -v cygpath >/dev/null 2>&1; then
  PKG_ROOT="$(cygpath -m "$PKG_ROOT")"
  case "$MC" in /*) MC="$(cygpath -m "$MC")" ;; esac
fi
echo -e "${C}=== 布洛陀安装包 接入自检 | 记忆中心: $MC | 端: ${PLATFORM:-workbuddy} 配置根: $CONFIG_ROOT ===${N}"

# ── python 解析（N5·2026-09-17 收口）────────────────────────────────
# 与 verify.ps1 的 Find-Python 同语义：优先 WorkBuddy 自带解释器 → PATH 上的 python3 → python。
# 原实现裸调 python3，macOS 端若只有 python（无 python3）→ §0/§4 静默失败（-f 判断过但执行失败）。
PY=""
# 试跑校验（2026-09-20 回灌群友 Windows 实测）：Git Bash 下 python3 可能命中
# MS Store stub（command -v 可见·实际执行 exit 49）——仅探测不试跑会把坏解释器当可用。
py_ok(){ "$1" -c "pass" >/dev/null 2>&1; }
for cand in "$HOME/.workbuddy/binaries/python/versions/"*/bin/python3 "$HOME/.workbuddy/binaries/python/versions/"*/bin/python; do
  if [ -x "$cand" ] && py_ok "$cand"; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
  for cand in python3 python; do
    p="$(command -v "$cand" 2>/dev/null)" && py_ok "$p" && { PY="$p"; break; }
  done
fi
if [ -z "$PY" ]; then echo -e "${Y}  [i] 未找到可用 python（跳过污染检测/干净度检查）${N}"; else echo -e "${C}  [i] python: $PY${N}"; fi
# 🔴 2026-10-03 治本（防误层·不造污染，而非事后擦）：本自检自身 import 包内脚本时
#    Python 会写 __pycache__ → verify 每跑一次就自己造一次污染、然后自己报污染（自噬循环）。
#    ⛔ 此前只能靠人工事后清（防错层·每次擦屁股）。现从产生源封死：
#    PYTHONDONTWRITEBYTECODE=1 环境级生效，覆盖本脚本全部 py_run 调用 + 直接调用点。
export PYTHONDONTWRITEBYTECODE=1
py_run(){ [ -n "$PY" ] || return 127; "$PY" "$@"; }

# 0) 数据污染检测（全路径强制·与 Step 0.5 同口径·dry-run 只读）
#    域外降级判据（2026-09-30 终检·**结构性**·⛔无作者侧字面量）：
#      本项判据=「端用户记忆中心不应含随包样例数据」。若 MC 恰为**安装包源码树之祖先**
#      （包住在 MC 之下）＝源码机自检；而指纹池（references/integrity-fingerprints.json）
#      正是从该卡库生成 ⇒ 全量命中属**判据域外**（非缺陷）→ 降级为 advisory。
#      端用户机（包解压位与记忆中心分离）行为**完全不变**。
if [ "${PKG_ROOT#"$MC"/}" != "$PKG_ROOT" ]; then MC_OWNS_PKG=1; else MC_OWNS_PKG=0; fi
if [ -n "$PY" ] && [ -f "$PKG_ROOT/data_contamination_check.py" ] && [ -f "$PKG_ROOT/references/integrity-fingerprints.json" ]; then
  if py_run "$PKG_ROOT/data_contamination_check.py" --memory-root "$MC" \
       --fingerprints "$PKG_ROOT/references/integrity-fingerprints.json" \
       --template-root "$PKG_ROOT/references" >/dev/null 2>&1; then
    ok "数据污染检测: 无污染"
  elif [ "$MC_OWNS_PKG" = 1 ]; then
    echo -e "${C}  [i] 数据污染检测: 判据域外·降级（记忆中心即安装包源码树之根 ⇒ 指纹池与本地卡库同源·全量命中属预期）；本项仅对端用户新装记忆中心有意义${N}"
  else no "数据污染检测: 命中污染（需 --apply 清理或人工核对）"; fi
elif [ -z "$PY" ]; then no "未找到可用 python（跳过污染检测）"
else no "污染检测依赖缺失(data_contamination_check.py / references/integrity-fingerprints.json)"; fi

# 1) 系统文件（发布包模板齐全 + 记忆中心核心层存在）
for e in "references/templates/SOUL.md|人格模板" "references/templates/IDENTITY.md|身份模板" "references/templates/USER.md|用户画像模板"; do
  rel="${e%%|*}"; lb="${e#*|}"
  if [ -s "$PKG_ROOT/$rel" ]; then ok "发布模板 $lb: $rel"; else no "发布模板 $lb: $rel (缺失)"; fi
done
if [ -s "$MC/核心层/CORE.md" ]; then ok "记忆中心 核心层: CORE.md"; else no "记忆中心 核心层: CORE.md (缺失/为空)"; fi

# 1.5) 平台系统文件（落点 SSOT = adapters/<端>/capability.yaml 的 system_file_paths）
#
# ⚠️ 2026-10-02 修：旧版硬编码「SOUL/IDENTITY/USER 一律在 $CFG_DIR 根」——
#    那只对**扁平配置根**的端成立。Hermes 是**混合结构**：USER.md 在 memories/ 子目录，
#    IDENTITY.md 无独立载体（设计如此，并入 SOUL.md）。
#    ⇒ 旧版对 hermes 恒假红（USER.md/IDENTITY.md 报缺失），而 capability.yaml 早已写对。
#    这是「声明面改了·门禁面没跟」的同型病：⛔ 别再在本脚本里硬编码任何端落点。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/adapters/$PLATFORM/capability.yaml" ]; then
  SYSFILE_OUT="$("$PY" - "$PKG_ROOT" "$CFG_DIR" "$PLATFORM" <<'PYEOF'
import os, sys
pkg, cfg, plat = sys.argv[1], sys.argv[2], sys.argv[3]
# 2026-10-03 降级链：WB 自带解释器无 PyYAML（实锤·本段曾恒 SKIP）→ 无 yaml 用内置 mini 解析
# （只提取 system_file_paths 扁平块·与 install_scripts._mini_yaml 同族思路·零依赖）
import re as _re
def _mini_sysfiles(text):
    out, in_blk, base = {}, False, None
    for ln in text.split("\n"):
        if _re.match(r"^system_file_paths:\s*(#.*)?$", ln):
            in_blk, base = True, None; continue
        if not in_blk:
            continue
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        ind = len(ln) - len(ln.lstrip())
        if base is None:
            base = ind
        if ind < base:
            break
        body = ln.split("#", 1)[0].strip()
        if not body:
            continue
        if ":" not in body:
            break
        k, v = body.split(":", 1)
        k = k.strip().strip(chr(34)).strip(chr(39))
        v = v.strip().strip(chr(34)).strip(chr(39))
        out[k] = None if v in ("", "null", "~") else v
    return out
cap_path = os.path.join(pkg, "adapters", plat, "capability.yaml")
try:
    cap_text = open(cap_path, encoding="utf-8").read()
except Exception as e:
    print("SKIP	capability.yaml 读取失败：%s" % e); raise SystemExit(0)
try:
    import yaml
    cap = yaml.safe_load(cap_text) or {}
except Exception:
    cap = {"system_file_paths": _mini_sysfiles(cap_text)}
# 2026-10-03 端级严格评估（用户令·口径=WorkBuddy布洛陀设计哲学/02-三层分离与系统文件映射规范 §六）：
# 五系统文件 = SOUL.md/IDENTITY.md/USER.md/MEMORY.md/自定义指令（customPrompt 等价物）·⛔SHADOW 不算（L5 投影进 USER.md 的段）。
# 判据（用户定）：不管什么形式，五件逐件有本端适配载体+内容百分百适配即可——缺键=判红（缺口如实显形·⛔不SKIP不豁免）。
SYSFILES = ["SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md", "自定义指令"]
paths = cap.get("system_file_paths") or {}
if not paths:
    print("FAIL\tsystem_file_paths\tcapability.yaml 未声明五系统文件落点映射（端自适配义务缺失·2026-10-03 起判红，逐端取证后补表）")
    raise SystemExit(0)
missing_keys = [k for k in SYSFILES if k not in paths]
for k in missing_keys:
    print("NOKEY\t%s\t五系统文件之一未声明适配载体（端适配缺口·补齐或显式声明后转绿）" % k)
for name, rel in sorted(paths.items()):
    if rel is None:
        print("MERGED\t%s\t无独立载体·并入端主载体（端设计如此·⛔ 不判缺失）" % name)
    elif "::" in str(rel):
        fpath, jpath = str(rel).split("::", 1)
        full = os.path.join(cfg, fpath)
        ok = os.path.isfile(full)
        if ok:
            try:
                import json as _json
                node = _json.load(open(full, encoding="utf-8"))
                for part in jpath.split("."):
                    node = node[part]
                ok = bool(str(node).strip())
            except Exception:
                ok = False
        print(("OK" if ok else "MISS") + "	%s	%s（字段级核）" % (name, rel))
    else:
        print(("OK" if os.path.isfile(os.path.join(cfg, rel)) and os.path.getsize(os.path.join(cfg, rel)) else "MISS")
              + "\t%s\t%s" % (name, rel))
PYEOF
)"
  while IFS="$(printf '\t')" read -r st nm rel; do
    [ -z "$st" ] && continue
    case "$st" in
      OK)     ok  "平台系统文件: $nm → $CONFIG_ROOT/$rel" ;;
      MERGED) ok  "平台系统文件: $nm → $rel" ;;
      MISS)   no  "平台系统文件: $nm → $CONFIG_ROOT/$rel (缺失)" ;;
         BADF)   no  "平台系统文件: $nm — $rel (字段路径取不到·声明有误)" ;;
         EMPTY)  echo -e "${C}  [i] 平台系统文件: $nm → $rel (载体在位·内容待用户填·非缺陷)${N}" ;;
      FAIL)   no  "平台系统文件: $nm" ;;
      NOKEY)  no  "平台系统文件: $nm — $rel" ;;
      SKIP)   echo -e "${C}  [i] 平台系统文件落点校核: $rel${N}" ;;
    esac
  done <<< "$SYSFILE_OUT"
else
  echo -e "${C}  [i] 平台系统文件落点校核: 跳过（缺 python 或 adapters/$PLATFORM/capability.yaml）${N}"
fi

echo "DEBUG_SEC16 PY=[${PY:-空}] PLAT=[${PLATFORM:-空}]" >&2
# 1.6) 端功能面映射校核（条文33·hooks_surface/twin_surface·2026-10-03）
#      delivered 逐件三查：①端注册面（config.json/settings.json）有引用 ②磁盘落盘可达 ③包内有源
#      gap 域=欠账 advisory 显形（不判 FAIL——修复前如实可见）；声明缺失=FAIL（fail-closed·同 §1.5）
if [ -n "$PY" ] && [ -f "$PKG_ROOT/adapters/$PLATFORM/capability.yaml" ]; then
  HOOKS_OUT="$("$PY" - "$PKG_ROOT" "$PLATFORM" "$MC" <<'PYEOF'
import os, sys, re, json
pkg, plat = sys.argv[1], sys.argv[2]
mc = sys.argv[3] if len(sys.argv) > 3 else ""
cap_text = open(os.path.join(pkg, "adapters", plat, "capability.yaml"), encoding="utf-8").read()
# hooks_surface 段提取 —— 双形态契约（2026-10-03 扩面·此前只认 script 形态）：
#   形态 A「script 直挂」：`- {script: xxx.py, event: E, src: D}`  → zcode 等注册面在单文件里的端
#   形态 B「plugin 声明」：`- {plugin: 名字, events: [E1,E2]}`      → Hermes（插件目录 + provides_hooks）
#   原因：两种端**载体形态不同**（zcode=单一 config.json / Hermes=~/.hermes/plugins/*/plugin.yaml）。
#         ⛔ 用形态 A 的列表冒充形态 B = 拿一个端的格式冒充另一个端 = 声明造假；
#            且注册面读不到时全判 ADV ⇒ 声明变装饰 ⇒ 假绿。故必须按真实形态分别提取+核验。
def section(name):
    out, on = [], False
    for raw in cap_text.split("\n"):
        s = raw.strip()
        if re.match(r"^%s:\s*(#.*)?$" % name, s):
            on = True; continue
        if on:
            if s and not s.startswith("-") and re.match(r"^[a-z_]+:", s):
                break
            m = re.search(r"script:\s*([A-Za-z0-9_.\-]+\.py)", s)
            if m: out.append(("script", m.group(1))); continue
            m = re.search(r"plugin:\s*([A-Za-z0-9_.\-]+)", s)
            if m: out.append(("plugin", m.group(1)))
    return out
delivered, gaps = section("delivered"), section("gaps")
if not delivered and not gaps:
    print("FAIL\thooks_surface\t未声明端功能面映射（条文33·fail-closed）")
else:
    # 端注册面按 plat 分发（此前硬编码 zcode config.json ⇒ 他端恒读不到 ⇒ 恒判 ADV）
    #   zcode 形态 A → ~/.zcode/cli/config.json
    #   Hermes 形态 B → ~/.hermes/plugins/*/plugin.yaml 的 provides_hooks
    #   Trae Work 形态 C → ~/Library/LaunchAgents/com.buluotuo.traework.patrol.plist
    #                      + <MC>/开发工具/Skill路由引擎/scripts/route_traework_patrol.sh 的 ROSTER
    #                      （2026-10-03 补·本端无 config.json 注册面＝第三形态：无钩子事件面·launchd 拉模式）
    reg, reg_kind = "", "script"
    if plat == "hermes":
        reg_kind = "plugin"
        plug_dir = os.path.expanduser("~/.hermes/plugins")
        if os.path.isdir(plug_dir):
            names, evs = set(), set()
            for pn in sorted(os.listdir(plug_dir)):
                pf = os.path.join(plug_dir, pn, "plugin.yaml")
                if not os.path.isfile(pf):
                    continue
                names.add(pn)
                try:
                    import re as _re
                    for ln in open(pf, encoding="utf-8"):
                        if _re.search(r"provides_hooks", ln):
                            evs.add(pn)
                except Exception:
                    pass
            reg = json.dumps({"plugins": sorted(names), "with_hooks": sorted(evs)}, ensure_ascii=False)
    elif plat == "traework":
        _parts = []
        _plist = os.path.expanduser("~/Library/LaunchAgents/com.buluotuo.traework.patrol.plist")
        if os.path.isfile(_plist):
            try: _parts.append(open(_plist, encoding="utf-8", errors="ignore").read())
            except Exception: pass
        if mc:
            for _rel in (os.path.join("开发工具", "Skill路由引擎", "scripts", "route_traework_patrol.sh"),
                         os.path.join("脚本中心", "route_traework_patrol.sh")):
                _p = os.path.join(mc, _rel)
                if os.path.isfile(_p):
                    try: _parts.append(open(_p, encoding="utf-8", errors="ignore").read())
                    except Exception: pass
                    break
        reg = "\n".join(_parts)
    elif plat == "lobsterai":
        # 本端注册面=宿主插件表（openclaw.json）+ 插件源码 ROSTER（无 config.json 注册面・第四形态）
        _parts = []
        _oj = os.path.expanduser("~/Library/Application Support/LobsterAI/openclaw/state/openclaw.json")
        if os.path.isfile(_oj):
            try: _parts.append(open(_oj, encoding="utf-8", errors="ignore").read())
            except Exception: pass
        _pdir = os.path.expanduser("~/Library/Application Support/LobsterAI/third-party-extensions")
        if os.path.isdir(_pdir):
            for _pn in sorted(os.listdir(_pdir)):
                if not _pn.startswith("lobsterai-"):
                    continue
                _p = os.path.join(_pdir, _pn, "index.js")
                if os.path.isfile(_p):
                    try: _parts.append(open(_p, encoding="utf-8", errors="ignore").read())
                    except Exception: pass
                _lib = os.path.join(_pdir, _pn, "lib")
                if os.path.isdir(_lib):
                    _parts.append(" ".join(os.listdir(_lib)))
        reg = "\n".join(_parts)
    else:
        cfg_json = os.path.expanduser("~/.zcode/cli/config.json")
        if os.path.isfile(cfg_json):
            try: reg = json.dumps(json.load(open(cfg_json, encoding="utf-8")), ensure_ascii=False)
            except Exception: reg = ""
    pkg_src_dirs = ["adapters/%s/hooks" % plat, "references/scripts", "references/digital-twin/devtools", "references/hooks"]
    pkg_plugin_dir = "adapters/%s/plugins" % plat
    for kind, nm in delivered:
        if kind == "plugin":
            if not reg:
                in_reg = "ADV"
            elif ('"%s"' % nm) in reg or ("/%s/" % nm) in reg:
                in_reg = "OK"
            else:
                in_reg = "MISS"
            src_ok = os.path.isdir(os.path.join(pkg, pkg_plugin_dir, nm))
            st = "OK" if (in_reg == "OK" and src_ok) else ("MISS" if in_reg == "MISS" else "ADV")
            print(st + "\t" + nm + "\t" + ("插件已装✓包内有源✓" if st == "OK" else ("插件未安装" if in_reg == "MISS" else "插件注册面不可读·advisory")))
        else:
            in_reg = ("OK" if nm in reg else "MISS") if reg else "ADV"
            src_ok = any(os.path.isfile(os.path.join(pkg, d, nm)) for d in pkg_src_dirs)
            st = "OK" if (in_reg == "OK" and src_ok) else ("MISS" if in_reg == "MISS" else "ADV")
            print(st + "\t" + nm + "\t" + ("注册✓包源✓" if st == "OK" else ("注册面未引用" if in_reg == "MISS" else "注册面不可读·advisory")))
    for kind, nm in gaps:
        print("ADV\t%s\tgap欠账（实盘在挂/包未交付·见capability）" % nm)
# twin_surface 声明存在性
print("TWIN\t" + ("declared" if "twin_surface:" in cap_text else "absent"))
PYEOF
)"
  echo "$HOOKS_OUT" | while IFS="$(printf '\t')" read -r st nm msg; do
    [ -z "$st" ] && continue
    case "$st" in
      OK)   ok  "功能面: ${nm}（${msg}）" ;;
      MISS) no  "功能面: $nm — $msg" ;;
      ADV)  echo -e "${C}  [i] 功能面: $nm — $msg${N}" ;;
      FAIL) no  "功能面: $msg" ;;
      TWIN) if [ "$nm" = "declared" ]; then ok "分身功能面: twin_surface 已声明"; else no "分身功能面: twin_surface 未声明（条文33·fail-closed）"; fi ;;
    esac
  done <<< "$HOOKS_OUT"
fi

# 1.7) 发版前置门禁（端适配 100% 判据·platform_adaptation_check.py --gate·2026-10-03）
#
# 用户令：把「自身 100% 才许映射」从单端点状修补升级为**全端通用发版门禁**——
# 任一端未达 100% → 拒绝打包该端。机制代意志（愿景①·不依赖人记得）：
# 下次换端改造时，半成品映射在打包门禁就被拦下，⛔不再等装机后由用户发现。
# 判据三面与 §1.5/§1.6 **同源**（⛔不另立判据防脱钩）：面A 五系统文件声明+包内载体 /
# 面B 钩子面 delivered 包内有源 / 面C 数字分身面；--gate 任一缺口 → exit 1。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/platform_adaptation_check.py" ]; then
  PAC_OUT="$("$PY" "$PKG_ROOT/platform_adaptation_check.py" --src "$PLATFORM" --gate --pkg-root "$PKG_ROOT" 2>&1)"
  if [ $? -eq 0 ]; then
    ok "发版门禁: 端适配 100%（--gate 放行·platform_adaptation_check.py）"
  else
    no "发版门禁: 端适配未达 100% → 拒绝打包/发版该端（缺口明细如下·补齐 capability 声明后转绿）"
    while IFS= read -r _pac_line; do
      [ -n "$_pac_line" ] && echo -e "${Y}      $_pac_line${N}" >&2
    done <<< "$PAC_OUT"
  fi
else
  echo -e "${C}  [i] 发版前置门禁: 跳过（缺 python 或 platform_adaptation_check.py）${N}"
fi

# 2) 规则三层（铁律/摘要为硬性）
for e in "记忆规则/用户基本规则-铁律版.md|铁律版|rules.tielu" \
         "记忆规则/用户基本规则-摘要版.md|摘要版|rules.summary" \
         "记忆规则/用户基本规则-详解存档版.md|详解存档版|rules.detail"; do
  rel="${e%%|*}"; rest="${e#*|}"; lb="${rest%%|*}"; sid="${rest#*|}"
  if [ -s "$MC/$rel" ]; then ok "规则三层 $lb: $rel"; else no "规则三层 $lb: $rel (缺失)"; fi
  # 2b) 唯一性校核（2026-10-03 补·「三个文件各只有一份」升为机械判据）
  #     病根：模板形态=裸正文+BEGIN/END段·写入侧曾把"frontmatter 之后全部"当段正文
  #     ⇒ 装出来一份文件里套两份标记（实测摘要版 174 行/BEGIN×2·铁律版 811 行/BEGIN×2）。
  #     判据：同一 sid 的 BEGIN 标记**有且仅有一处**——2 处即重复安装，0 处即段丢失。
  if [ -f "$MC/$rel" ]; then
    _nb=$(grep -c "BULUOTUO:BEGIN $sid" "$MC/$rel" 2>/dev/null || echo 0)
    if [ "$_nb" = "1" ]; then
      ok "规则唯一性 $lb: 段 $sid 恰好 1 处（无重复安装）"
    elif [ "$_nb" = "0" ]; then
      no "规则唯一性 $lb: 段 $sid **0 处**（断章标记丢失·增量合并会判'文件里没有本段'⇒追加第二个半截段）"
    else
      no "规则唯一性 $lb: 段 $sid **$_nb 处**（重复安装/套嵌·⛔ 唯一来源被破坏）"
    fi
  fi
done

# 3.0) Skill 落点双口径判定（2026-10-03 根治中文别名目录误报）：
#       目录名直配 或 frontmatter name 直配 或 扫描目标目录 SKILL.md frontmatter 匹配——
#       多端包内 Skill 用英文标识符目录名，端用户本地可能以中文别名目录名部署（如
#       「布洛陀-童灵切片导航-豆包办公」= doenglingz-slice-nav-doubao），按 basename
#       直配会把「已装」误报「缺失」。三口径任一命中即计已部署。
_skill_present() { # $1=包内Skill目录 $2=待查根目录
  local s name d f fm
  s=$(basename "$1")
  [ -e "$2/$s" ] && return 0                                  # 口径①目录名直配
  name=$(grep -m1 '^name:' "$1/SKILL.md" 2>/dev/null | sed -E 's/^name:[[:space:]]*["'"'"']?([^"'"'"'[:space:]]*).*/\1/')
  [ -n "$name" ] && [ -e "$2/$name" ] && return 0             # 口径②frontmatter name 直配
  for d in "$2"/*/; do                                        # 口径③扫描目标目录 frontmatter
    [ -d "$d" ] || continue
    [ -f "$d/SKILL.md" ] || continue
    fm=$(grep -m1 '^name:' "$d/SKILL.md" 2>/dev/null | sed -E 's/^name:[[:space:]]*["'"'"']?([^"'"'"'[:space:]]*).*/\1/')
    [ -n "$fm" ] && [ "$fm" = "$name" ] && return 0
  done
  return 1
}

# 3) 记忆 Skill（2026-09-21 改「名单同源」：从包内 references/skills/ 动态枚举，⛔不再硬编码
#    9 个名字——硬编码导致新增 Skill 长期不在验证覆盖内=装了没装都不报）
#    2026-10-03 落点判定升级双口径（见 §3.0）：目录名或 frontmatter name 任一匹配即计）
SKILLS_TOTAL=0; FSK=0
for d in "$PKG_ROOT"/references/skills/*/; do
  [ -d "$d" ] || continue
  [ -f "$d/SKILL.md" ] || continue
  SKILLS_TOTAL=$((SKILLS_TOTAL+1))
  _skill_present "$d" "$MC/技能配置" && FSK=$((FSK+1))
done
if [ "$SKILLS_TOTAL" -gt 0 ] && [ "$FSK" -eq "$SKILLS_TOTAL" ]; then ok "记忆Skill: $FSK/${SKILLS_TOTAL}（名单源=包内 references/skills/）";
elif [ "$SKILLS_TOTAL" -eq 0 ]; then no "记忆Skill: 包内 references/skills/ 无可枚举 Skill（包结构异常）";
else no "记忆Skill仅 $FSK/$SKILLS_TOTAL(缺失：比对包内 references/skills/ 与 $MC/技能配置/)"; fi

# 3.2) Skill 软链接（step7 检查清单 #12·N6）
#      2026-09-17 新增：原双端均不验，契约与验证器脱节。
#      2026-09-21：名单同步改为动态枚举（同 §3）。
#      2026-10-03：落点判定升级双口径（同 §3.0·中文别名目录不误报 WARN）。
SLINK_DIR="$CFG_DIR/skills"
if [ -d "$SLINK_DIR" ]; then
  SLK=0
  for d in "$PKG_ROOT"/references/skills/*/; do
    [ -f "$d/SKILL.md" ] || continue
    _skill_present "$d" "$SLINK_DIR" && SLK=$((SLK+1))
  done
  if [ "$SKILLS_TOTAL" -gt 0 ] && [ "$SLK" -eq "$SKILLS_TOTAL" ]; then ok "Skill软链接: $SLK/$SKILLS_TOTAL 有效（$CONFIG_ROOT/skills/）";
  else echo -e "${Y}  [WARN] Skill软链接 $SLK/${SKILLS_TOTAL}（需开发者模式/管理员；step6 降级护栏已声明）${N}"; fi
else
  echo -e "${C}  [i] $CONFIG_ROOT/skills/ 不存在·跳过软链接检查${N}"
fi

# 3.5) 脚本体系部署（可选·装了才查；未装「脚本中心/」则跳过不计分）
if [ -f "$MC/脚本中心/rule_fragment_inject.py" ]; then
  ok "脚本中心: rule_fragment_inject.py 已部署"
  # 2026-10-03 端形态感知（条文19·判据与变换一致）：hooks/rule/ 硬布局只属 settings.json 端（WB/qodercn）；
  # zcode 类端（settings_json=false+hooks_alternative）的 ROSTER 变换=[5c/8]（脚本中心+config.json 注册），
  # 其「注册↔落盘↔包源」三查由 §1.6 hooks_surface 承接——本段对 zcode 形态跳过硬布局检查⛔双判据打架。
  _settings_json_true="1"
  if [ -n "$PY" ] && [ -f "$PKG_ROOT/adapters/$PLATFORM/capability.yaml" ]; then
    "$PY" - "$PKG_ROOT/adapters/$PLATFORM/capability.yaml" <<'PYEOF' 2>/dev/null && _settings_json_true="0"
import sys
t = open(sys.argv[1], encoding="utf-8").read()
sys.exit(0 if "settings_json: false" in t and "hooks_alternative: true" in t else 1)
PYEOF
  fi
  if [ "$_settings_json_true" = "1" ]; then
    [ -f "$CFG_DIR/hooks/rule/rule_fragment_inject.py" ] && ok "运行钩子: $CONFIG_ROOT/hooks/rule/rule_fragment_inject.py" || no "运行钩子: $CONFIG_ROOT/hooks/rule/rule_fragment_inject.py (缺失)"
    [ -f "$CFG_DIR/hooks/rule/rule_triggers.yaml" ] && ok "触发规格: $CONFIG_ROOT/hooks/rule/rule_triggers.yaml" || no "触发规格: $CONFIG_ROOT/hooks/rule/rule_triggers.yaml (缺失)"
  else
    echo -e "${C}  [i] 运行钩子布局: 本端=脚本中心形态（hooks/rule/ 硬布局不适用·三查见 §1.6 功能面）${N}"
  fi
  # 2026-09-21 根治：核查口径改为「与安装共用同一数据源」——直接调 install_scripts.py --verify
  # （读其 ROSTER 数组），不再在 verifier 里另抄一份钩子清单——另抄一份正是「登记了却没装文件」的复发土壤。
  if [ -n "$PY" ] && [ -f "$PKG_ROOT/install_scripts.py" ]; then
    if py_run "$PKG_ROOT/install_scripts.py" --verify "$MC" ${PLATFORM:+--platform "$PLATFORM"} >/dev/null 2>&1; then  # v2.0.1 透传端（核查与安装同源同端）
      ok "钩子总表: 全部落盘并已注册（数据源=install_scripts.py ROSTER）"
    else
      no "钩子总表: 有钩子未落盘/未注册，或规则数据缺失（跑 python3 install_scripts.py --verify \"<记忆中心>\" 看明细）"
    fi
  else no "install_scripts.py 缺失（无法核对钩子总表）"; fi

  # 3.6) 派发心跳（advisory 显形·注册 ≠ 派发·2026-09-21 端用户连坐案例）
  #      病灶：第三方插件 hooks.json 格式非法 → 宿主整事件连坐停摆 → 钩子静默失效，
  #      注册态检查（§3.5）零症状。心跳证据=钩子被真派发时自动留痕
  #      （hook_protocol.py import 即留痕；路径单一真源=其 HB_DIR）。
  #      ⛔ 有意不计 FAIL：新鲜度无法区分「停摆」与「用户休假」，假阳性比没有检查更糟；
  #      状态明细跑 python3 references/scripts/guard_heartbeat_check.py --report。
  if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/guard_heartbeat_check.py" ]; then
    MEMORY_CENTER="$MC" py_run "$PKG_ROOT/references/scripts/guard_heartbeat_check.py" --brief 2>/dev/null \
      && true
  fi
else
  echo -e "${C}  [i] 脚本体系未安装(脚本中心/缺失)·跳过硬墙部署检查${N}"
fi

# 3.7) 数字分身·卡链路三步（抽卡→落卡→碰撞·2026-09-30 终检·件4 收官）
#      病灶：数字分身完整版 Phase B 交付「抽卡→落卡→碰撞」链路，原六项自检**零覆盖**
#      ⇒ 装了但链路断=不可见（同族「装了没装都不报」，设计真源=数字分身完整版-安装流程设计
#      §二·终检行「三步 dry-run 全绿 = exit 0」）。本项为**包能力检查**：在隔离沙箱内复制
#      **包内**引擎跑真链路 ⇒ ⛔不要求端用户已装 Phase B、⛔不触碰其真实卡库；
#      判据由 twin_chain_check.py 自证（三步逐步 exit 0 + INDEX.md 真写出）。
#      rc：0=全绿 3=包内引擎缺失(包结构缺陷) 1=链路断 2=参数错。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/twin_chain_check.py" ]; then
  py_run "$PKG_ROOT/references/scripts/twin_chain_check.py" \
    --pkg-root "$PKG_ROOT" --memory-center "$MC" --quiet >/dev/null 2>&1
  _tcc=$?
  case "$_tcc" in
    0) ok "分身链路: 抽卡→落卡→碰撞 三步 dry-run 全绿（隔离沙箱·零触真实卡库）" ;;
    3) no "分身链路: 包内引擎缺失（references/知识联邦引擎-min/scripts）——包结构缺陷" ;;
    1) no "分身链路: 三步 dry-run 未全绿（跑 python3 references/scripts/twin_chain_check.py --pkg-root \"$PKG_ROOT\" 看明细）" ;;
    *) no "分身链路: 检查器异常退出 rc=$_tcc" ;;
  esac
elif [ -z "$PY" ]; then no "未找到可用 python（跳过分身链路检查）"
else no "分身链路检查器缺失: references/scripts/twin_chain_check.py"; fi

# 3.8) 养成链在位（答题→计分→蒸馏→上线·四要素静态断言·2026-09-30 用户质证「答题在哪/蒸馏在哪」）
#      判据＝使用链逐步可达：装机入口（答题页在部署清单）+执行件（造芯三件）+文档指引（INSTALL
#      养成链节+蒸馏清单）——部署面齐件 ≠ 使用链闭环（WB-20260930-002 教训）。
_lcm=0
[ -f "$PKG_ROOT/references/digital-twin/hexaco/自建100题-答题页-v1.html" ] || _lcm=1
[ -f "$PKG_ROOT/references/digital-twin/k2-slice-generator/k2_slice_generator.py" ] || _lcm=1
grep -q '"hexaco":' "$PKG_ROOT/install_scripts.py" 2>/dev/null || _lcm=1
grep -q '分身养成链' "$PKG_ROOT/INSTALL.md" 2>/dev/null || _lcm=1
grep -q '蒸馏目标层' "$PKG_ROOT/INSTALL.md" 2>/dev/null || _lcm=1
#      v2.0.1 根治（2026-09-30 Agent B 盲审 B8）：原五要素全包内静态检查（grep INSTALL 文本=只验"文档提过"）——
#      补装机态落点断言：脚本中心已存在 ⇒ 配置根 hooks/ 下分身运行时件必须在位（未装机则跳过·与§3.5同口径）。
#      2026-10-03 端形态感知（条文19）：zcode 类端分身件落点=数字分身/devtools/（[5b/8] 变换·注册指 DT_DEV），
#      ⛔ 按 hooks/ 硬布局核＝错位假红——核「注册面引用路径可达」代替硬编码位置。
if [ -d "$MC/脚本中心" ]; then
  if [ -f "$CFG_DIR/hooks/doenglingz_inject_prompt.py" ]; then
    :   # settings.json 端形态落点在位
  elif [ -f "$HOME/.zcode/doenglingz_doenglingz_placeholder" ]; then
    :   # 占位（不可达·防御分支）
  else
    # 端形态通用核：注册面（config.json 或 settings.json）引用 inject_prompt 且命令中路径文件存在 ⇒ 在位
    _twin_ok=0
    for _reg in "$CFG_DIR/cli/config.json" "$CFG_DIR/settings.json" "$HOME/.zcode/cli/config.json"; do
      [ -f "$_reg" ] || continue
      _cmd=$("$PY" -c "
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding='utf-8'))
    print(json.dumps(d.get('hooks',{}).get('events',{}),ensure_ascii=False))
except Exception: print('')" "$_reg" 2>/dev/null)
      if [ -n "$_cmd" ] && echo "$_cmd" | grep -q "doenglingz_inject_prompt"; then
        _p=$(echo "$_cmd" | "$PY" -c "
import json,sys,re
ev=json.loads(sys.stdin.read() or '{}')
for g in ev.get('UserPromptSubmit',[]):
    for h in g.get('hooks',[]) if isinstance(g,dict) else []:
        c=h.get('command','') if isinstance(h,dict) else ''
        if 'doenglingz_inject_prompt' in c:
            print(re.findall(r'[^ ]*doenglingz_inject_prompt\\.py',c)[0]); break" 2>/dev/null)
        [ -n "$_p" ] && [ -f "$_p" ] && _twin_ok=1 && break
      fi
    done
    [ "$_twin_ok" = 1 ] || { _lcm=1; echo -e "${R}  [FAIL] 分身运行时落点: 注册面引用的 doenglingz_inject_prompt.py 不可达（已装脚本中心·分身钩子未挂/悬空）${N}"; }
  fi
fi
if [ "$_lcm" = 0 ]; then ok "养成链在位: 答题页+造芯件+部署声明+INSTALL指引+蒸馏清单 五要素齐+装机态落点"
else no "养成链缺件: 答题页/造芯件/部署声明/INSTALL指引/蒸馏清单 有缺失（看上方 [FAIL] 明细）"; fi

# 4) 安装包干净度（发布卫生·单一真源=references/scripts/pkg_cleanliness_check.py·双端同口径）
#    2026-09-17 童灵根治：原 grep 实现 5 类检查，与 verify.ps1（只查1类）不对称=Windows 端零防线 →
#    收口为 python 单一真源（utf-8 读，规避 PS5.1 无BOM 中文误判）。
#    检查项：私人称呼 / 用户名 / .bak 残留 / 临时残留(_tmp_*·*.tmp) / 运行时状态点文件
DIRT=0
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/pkg_cleanliness_check.py" ]; then
  if ! py_run "$PKG_ROOT/references/scripts/pkg_cleanliness_check.py" --pkg-root "$PKG_ROOT"; then
    # 2026-09-20 B6（群友计数口径）：原实现只置 DIRT 不调 no() → FAIL 计数不增 →
    #   检查器报多条 [FAIL] 而汇总"全过"=假绿。修法：检查器级计 1 项 + 明细口径声明。
    DIRT=1; no "安装包干净度: 检查器报污染（上方 [FAIL] 行=分类明细·本汇总按检查器级计 1 项）"
  fi
elif [ -z "$PY" ]; then no "未找到可用 python（跳过干净度检查）"; DIRT=1
else no "卫生检查器缺失: references/scripts/pkg_cleanliness_check.py"; DIRT=1; fi
# 作者侧路径引用未声明（用户端文档引用 `开发工具/` 且无降级声明·检查⑪-治本·2026-09-15 皮叔令彻底根治）
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/platform_compat.py" ]; then
  if ! py_run "$PKG_ROOT/references/scripts/platform_compat.py" --only-author-path "$PKG_ROOT" >/dev/null 2>&1; then
    no "安装包含未声明的作者侧路径引用（用户端文档引用 开发工具/ 路径但无 N/A/未随包分发 声明）"; DIRT=1
  fi
fi
[ "$DIRT" = 0 ] && ok "安装包干净度: 8 类卫生项全过 + 无未声明作者侧路径"

# 5) 版本锚点（不计分·信息）
BV=$(cat "$MC/.install/version" 2>/dev/null || echo "未知(未完成安装或无锚点)")
echo -e "${C}  [i] 布洛陀版本: $BV${N}"

echo ""
if [ "$FAIL" = 0 ]; then
  echo -e "${G}=== 自检通过: $PASS 项全过 ===${N}"; exit 0
else
  echo -e "${R}=== 自检未过: $FAIL 项失败(见上) ===${N}"; exit 1
fi
