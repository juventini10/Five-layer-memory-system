#!/bin/bash
# ============================================================
# verify.sh — 布洛陀安装包 接入自检 v1.0（只读·不改任何文件）
# 用法: bash verify.sh [--platform <端ID>]   (默认记忆中心 ~/记忆共享中心)
# 语义声明（2026-10-20·反馈#3 误读根治）：本脚本=**装后自检**——需要已安装的记忆中心；
#   在未安装的 clone/解包目录上跑，装机态项（路径完整性/占位符残留/软链）必报失败，属预期，
#   ⛔ 不等于"包缺件"。只看包面请用：python3 references/scripts/smoke_test.py . 与 platform_compat.py .
#       MEMORY_CENTER=/path bash verify.sh   (自定义记忆中心)
#       --platform qodercn → 落点检查按该端 capability.yaml 的 config_root（v2.0.1·多端）
# 检查项: 0)数据污染 1)系统文件 2)规则三层 3)记忆Skill 4)安装包干净度 5)版本锚点
#         3.1c)33 题两源对账(题库↔答题页逐字相等·C06)
#         3.1d)自陈待办在位对账(承诺面「写入 X.py→随包」必须有实物·C32 通用闸)
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
PASS=0; FAIL=0; PEND=0
ok(){ echo -e "${G}  [PASS] $1${N}"; PASS=$((PASS+1)); }
no(){ echo -e "${R}  [FAIL] $1${N}"; FAIL=$((FAIL+1)); }
# 三态分账（2026-10-22 R9·条文70·与 verify.ps1 同口径镜像·条文68）
pend(){ echo -e "${C}  [PEND] $1${N}"; PEND=$((PEND+1)); }

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
STEP5_DONE=0; [ -f "$MC/.install/step5-done.md" ] && STEP5_DONE=1
miss(){ if [ "$STEP5_DONE" = 0 ]; then pend "$1（AI引导段未跑·答题后重跑即消）"; else no "$1"; fi; }
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
if [ -s "$MC/核心层/CORE.md" ]; then ok "记忆中心 核心层: CORE.md"; else miss "记忆中心 核心层: CORE.md (缺失/为空)"; fi

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
# ── zwork 形态 D（平台托管型·2026-10-08·第四种落点判据）：────────────────
#   五件等价物=端自有实体（条文48 端自持有律原生成立）+平台 Memory 两面——
#   判据=实体文件在场+内容锚点 grep（⛔按 config_root 相对路径拼检=平台托管型必假红：
#   platform:// 伪协议与 ~/ 绝对路径都不是 config_root 下的相对路径——判据面与落点面不相交）。
#   声明值两形态：绝对路径（~ 展开判 isfile+锚点 grep）/ platform://（判 MERGED=平台面信任源）。
if plat == "zwork":
    _ANCHORS = {
        "SOUL.md": ("~/个人AI档案/AutoClaw/SOUL.md", "把沉淀当资产"),
        "IDENTITY.md": ("~/个人AI档案/AutoClaw/AGENTS.md", "端身份与边界"),
        "USER.md": (None, "平台 Memory 用户卡（Run 级注入·机制级·平台内不可文件检=信任源）"),
        "MEMORY.md": (None, "平台 Memory 记忆层（Run 级注入·机制级·平台内不可文件检=信任源）"),
        "自定义指令": ("~/个人AI档案/AutoClaw/AGENTS.md", "buluotuo:execution-guidelines-v1"),
    }
    for name, (fp, anchor) in _ANCHORS.items():
        if fp is None:
            print("MERGED\t%s\t%s" % (name, anchor)); continue
        full = os.path.expanduser(fp)
        ok = False
        if os.path.isfile(full) and os.path.getsize(full):
            try:
                ok = anchor in open(full, encoding="utf-8").read()
            except Exception:
                ok = False
        if ok:
            print("OK\t%s\t%s（端实体+锚点核）" % (name, fp))
        elif os.path.isfile(full) and os.path.getsize(full):
            print("OK\t%s\t装机档：实体在位·真身锚点留作者对账档" % name)
        else:
            print("MISS\t%s\t%s（端实体+锚点核）" % (name, fp))
    raise SystemExit(0)
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
      MISS)   if [ "$nm" = "自定义指令" ]; then no "平台系统文件: $nm → $CONFIG_ROOT/$rel (缺失·F20 预期态注：设置框字段由用户手动粘贴·安装输出有指引·粘后重跑即消·⛔非装失败)"; else miss "平台系统文件: $nm → $CONFIG_ROOT/$rel (缺失)"; fi ;;
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
# 2026-10-08 端形态扩容：zwork 平台托管型 delivered=诚实空集+gaps=平台边界说明（非 {script}/{plugin} 形态）——
# 原判据「提取不到条目=未声明」把「声明了但条目为说明文本」的端误判 FAIL（条文34③同族：验收器能力未跟上端形态）。
# 修法=先判「段在场性」再判「条目核验」：段在场+delivered 空且 gaps 有字=标量声明形态（PASS·标量=端诚实能力声明）。
hooksec_present = bool(re.search(r"^hooks_surface:\s*(#.*)?$", cap_text, re.M))
if not delivered and not gaps and not hooksec_present:
    print("FAIL\thooks_surface\t未声明端功能面映射（条文33·fail-closed）")
elif not delivered and not gaps and hooksec_present:
    print("ADV\thooks_surface\t平台托管型诚实空集（delivered=[]+gaps=边界说明·零钩子件交付面）")
else:
    # 端注册面按 plat 分发（此前硬编码 zcode config.json ⇒ 他端恒读不到 ⇒ 恒判 ADV）
    #   zcode 形态 A → ~/.zcode/cli/config.json
    #   Hermes 形态 B → ~/.hermes/plugins/*/plugin.yaml 的 provides_hooks
    #   Trae Work 形态 C → ~/Library/LaunchAgents/com.buluotuo.traework.patrol.plist
    #                      + <MC>/开发工具/Skill路由引擎/scripts/route_traework_patrol.sh 的 ROSTER
    #                      （2026-10-03 补·本端无 config.json 注册面＝第三形态：无钩子事件面·launchd 拉模式）
    reg, reg_kind = "", "script"
    if plat == "zwork":
        # zwork 形态 E（平台托管型·2026-10-08）：无 config.json/settings.json/plist/openclaw.json——
        # 注册面证据=端实体锚点串集合（K2 标记对+对账器+规格书指针）。零钩子件=诚实空集交付面。
        _parts = []
        for _fp, _anchor in (("~/个人AI档案/数字分身/童灵·人格规格书.md", "Doenglingz"),
                             ("~/个人AI档案/AutoClaw/AGENTS.md", "buluotuo:execution-guidelines-v1"),
                             ("~/个人AI档案/AutoClaw/AGENTS.md", "K2 core_slice 开始"),
                             ("~/个人AI档案/数字分身/K2切片蒸馏/slices/core_slice.md", "运行时注入声明")):
            _full = os.path.expanduser(_fp)
            if os.path.isfile(_full):
                try:
                    if _anchor in open(_full, encoding="utf-8", errors="ignore").read():
                        _parts.append("%s:%s" % (_fp, _anchor))
                except Exception: pass
        reg = "\n".join(_parts)
    elif plat == "hermes":
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

# 1.7) 接入率漂移附加检查（platform_adaptation_check.py --src·2026-10-10 口径订正）
#
# 🔴 2026-10-10 死链根治（9/9 端恒 rc=2·git 考古 --gate 从未在 pac 里存在过）：
#    旧版本节传 `--gate --pkg-root`，而 pac 的 argparse 只有
#    `--src/--fix/--absorb/--absorb-selftest` ⇒ 拿到的 rc=2 是 **argparse 参数拒绝**
#    （非业务判红）⇒ 本节**恒判红**却宣称"端适配未达 100%"，误导排查方向。
#    且真正的三面判据**就在本文件自身**（§1.5 系统文件 / §1.6 钩子面 / twin_surface
#    ·L648/650 的 PASS/FAIL 汇总），⛔ 不需要也不应该再委派给外部脚本。
#    同时 install_scripts.py 的 gate_check() 已改为**委派本文件**（判据真源）；
#    若本节再反向调 install_scripts --gate ⇒ **递归互调**（verify→gate→verify）。
# ⇒ 本节降级为「接入率漂移」附加检查，语义如实标注：
#    · 三面判据 = 本文件 §1.5/§1.6/twin_surface + 末尾汇总（权威·不发版外判）
#    · pac = 文档 vs 实盘的接入率漂移（⚠️ 漂移不拦放行·只提示）
if [ -n "$PY" ] && [ -f "$PKG_ROOT/platform_adaptation_check.py" ]; then
  # ⚠️ rc 必须先落变量再判——⛔ 不可在 if [ $? ] 之后又用 $? 取值（第一个 echo 会把它
  #   重置为 0·且 set -u 下可能触发 unbound variable·2026-10-10 实测 line 430 崩过）
  PAC_OUT="$("$PY" "$PKG_ROOT/platform_adaptation_check.py" --src "$PLATFORM" 2>&1)"
  PAC_RC=$?
  if [ "$PAC_RC" -eq 0 ]; then
    ok "接入率漂移: 无漂移（platform_adaptation_check.py --src ${PLATFORM}）"
  else
    echo -e "${C}  [i] 接入率漂移: 有漂移（platform_adaptation_check.py rc=${PAC_RC} ）——"
    echo -e "      不影响本文件三面判据；发布前请核对（明细如下）${N}"
    while IFS= read -r _pac_line; do
      [ -n "$_pac_line" ] && echo -e "${Y}      $_pac_line${N}" >&2
    done <<< "$PAC_OUT"
  fi
  # ⚠️ 源机自指噪声清理（2026-10-10·第二类自指·同 __pycache__ 同族）：
  #   包内那份 pac 的 LOG 是占位符形态 `[记忆共享中心]/脚本中心/logs/…`
  #   （deident 规则4 所致·装机时才替换成用户记忆中心）。在**源机**上跑它 ⇒
  #   占位符不被替换 ⇒ 真在包内造出 .log ⇒ 下方 §4 干净度检查把它当污染报 FAIL
  #   ⇒ 「门禁自己污染自己」。用户机上该路径本就指向记忆中心·不涉及真实资产。
  #   ⚠️ 必须清在 §4 之前（§4 是判它的那个检查器）。
  [ -d "$PKG_ROOT/[记忆共享中心]" ] && rm -rf "$PKG_ROOT/[记忆共享中心]"
else
  echo -e "${C}  [i] 接入率漂移检查: 跳过（缺 python 或 platform_adaptation_check.py）${N}"
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
_skill_present() { # $1=包内Skill目录 $2=待查根目录 → rc 0=在场 1=缺席 2=仪器未跑
  # 判据下沉 verify_pair_checks.skill_present（三口径单源·2026-10-21 条文68孪生同构律：
  # 旧 bash 手搓版与 ps1 侧同判据两处演化=「sh有ps1没有」漂移族病根，本壳只调用不再持有逻辑）
  [ -z "$PY" ] && return 2
  [ -f "$PKG_ROOT/references/scripts/verify_pair_checks.py" ] || return 2
  "$PY" "$PKG_ROOT/references/scripts/verify_pair_checks.py" skill-present "$1" "$2"
  local rc=$?
  case "$rc" in 0|1) return $rc ;; *) return 2 ;; esac
}

# 3) 记忆 Skill（2026-09-21 改「名单同源」：从包内 references/skills/ 动态枚举，⛔不再硬编码
#    9 个名字——硬编码导致新增 Skill 长期不在验证覆盖内=装了没装都不报）
#    2026-10-03 落点判定升级双口径（见 §3.0）：目录名或 frontmatter name 任一匹配即计）
SKILLS_TOTAL=0; FSK=0; SKI=0
for d in "$PKG_ROOT"/references/skills/*/; do
  [ -d "$d" ] || continue
  [ -f "$d/SKILL.md" ] || continue
  SKILLS_TOTAL=$((SKILLS_TOTAL+1))
  _skill_present "$d" "$MC/技能配置"; _rc=$?
  case "$_rc" in
    0) FSK=$((FSK+1)) ;;
    1) : ;;
    *) SKI=$((SKI+1)) ;;
  esac
done
if [ "$SKI" -gt 0 ]; then no "记忆Skill落点判定: 仪器未跑 ${SKI} 件（python 或 verify_pair_checks.py 不可用·⛔失明期间不得代报"缺失"——仪器故障与判据红分态·承§4.7 10-18教训）";
elif [ "$SKILLS_TOTAL" -gt 0 ] && [ "$FSK" -eq "$SKILLS_TOTAL" ]; then ok "记忆Skill: $FSK/${SKILLS_TOTAL}（名单源=包内 references/skills/·三口径=verify_pair_checks 双端单源）";
elif [ "$SKILLS_TOTAL" -eq 0 ]; then no "记忆Skill: 包内 references/skills/ 无可枚举 Skill（包结构异常）";
else no "记忆Skill仅 $FSK/$SKILLS_TOTAL(缺失：比对包内 references/skills/ 与 $MC/技能配置/)"; fi

# 3.1) systemlog 写时守护双轨在位（2026-10-11 Win对等任务卡·mac .sh + Win .ps1 配对，⛔Win用户被指launchctl）
_SLD="$PKG_ROOT/references/skills/system-logger/scripts"
_sl_miss=""
for _f in systemlog_watch.sh install_watch.sh systemlog-watch.ps1 systemlog-install-task.ps1; do
  [ -f "$_SLD/$_f" ] || _sl_miss="$_sl_miss $_f"
done
if [ -z "$_sl_miss" ]; then ok "systemlog看守双轨: 包内 4/4 在位（mac .sh ×2 + Win .ps1 ×2）";
else no "systemlog看守缺包内件:$_sl_miss"; fi
if [ ! -f "$MC/技能配置/system-logger/SKILL.md" ]; then echo -e "${C}  [i] system-logger 未装此记忆中心——跳过 Win 件落盘检查${N}";
elif [ -f "$MC/技能配置/system-logger/scripts/systemlog-watch.ps1" ] && [ -f "$MC/技能配置/system-logger/scripts/systemlog-install-task.ps1" ]; then ok "systemlog看守 Win 件装机落盘 2/2（deploy_skills 逐目录复制实证）";
else no "systemlog看守 Win 件装机未落盘（<MC>/技能配置/system-logger/scripts/ 缺 .ps1）"; fi

# 3.1b) 装后语法面全量扫描（2026-10-11 _fill转义地雷根治卡 R2 verify腿·存量面）
#       装机产物面全量 .py compile + .json loads——转义雷/语法破损从"用户首触即死"左移为"verify 当轮显形"
#       与 install_scripts.fill_syntax_guard 双保险：guard 管装机当轮增量，本腿管跨版本存量
if [ -n "$PY" ] && [ -f "$PKG_ROOT/fill_syntax_scan.py" ]; then
  if "$PY" "$PKG_ROOT/fill_syntax_scan.py" "$MC" --quiet >/dev/null 2>&1; then ok "装后语法面: 装机面 .py/.json 编译级全绿"; else no "装后语法面有雷（$PY $PKG_ROOT/fill_syntax_scan.py $MC 看逐行明细）"; fi
elif [ ! -f "$PKG_ROOT/fill_syntax_scan.py" ]; then no "fill_syntax_scan.py 缺件（根治卡 R2 腿未入包）";
else echo -e "${C}  [i] 装后语法扫描: 跳过（无 python）${N}"; fi

# 3.1c) 33 题两源对账（C06·2026-10-15 修包 E2E）：题库 questionnaire.md ↔ 答题页 const Q 逐字相等
#       病根：包内两个源各自演化（实测 10 处分叉：Q5/Q23/Q24 页面丢内容、Q25-Q33 带 markdown 残留
#       `**`、Q18 题库带作者侧 🔴），而 step4 第1关拿「答卷 vs 题库」核对并把差异判成"用户手改卷"——
#       漂移在包内，账却记到用户头上（诚实答卷被判可疑）。本腿把"两源相等"左移成发版前机械闸。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/questionnaire_sync_check.py" ]; then
  if "$PY" "$PKG_ROOT/questionnaire_sync_check.py" --quiet >/dev/null 2>&1; then
    ok "33 题两源对账: 题库↔答题页 33/33 逐字相等"
  else
    no "33 题两源分叉（跑 $PY $PKG_ROOT/questionnaire_sync_check.py 看逐题明细·修完前 step4 第1关不可信）"
  fi
elif [ ! -f "$PKG_ROOT/questionnaire_sync_check.py" ]; then no "questionnaire_sync_check.py 缺件（C06 对账腿未入包）";
else echo -e "${C}  [i] 33 题两源对账: 跳过（无 python）${N}"; fi

# 3.1d) 自陈待办在位对账（C32·2026-10-15 用户认可的通用闸·C27/C16/C06 同族病的复发兜底）
#       判据：包内「承诺面」md 若写「待办/过闸后：写入 X.py → 随包」，X 必须在包内存在。
#       病根＝这类语句是承诺却无机械判据，可从 09-13 挂到 10-15 而门禁全程不红（C27 实证）。
#       扫描面二分：CHANGELOG／golden_samples／fixtures＝记录面（过去时·故意不回改）跳过并计数显形。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/todo_landing_check.py" ]; then
  if "$PY" "$PKG_ROOT/todo_landing_check.py" --quiet >/dev/null 2>&1; then
    ok "自陈待办对账: 承诺面待办全部有实物（或已带 reason 登记）"
  else
    no "自陈待办无实物（跑 $PY $PKG_ROOT/todo_landing_check.py 看逐条·这类待办挂空=文档与实盘脱钩）"
  fi
elif [ ! -f "$PKG_ROOT/todo_landing_check.py" ]; then no "todo_landing_check.py 缺件（C32 通用闸未入包）";
else echo -e "${C}  [i] 自陈待办对账: 跳过（无 python）${N}"; fi

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
  # F7 根治（2026-10-17·沙箱实测）：旧逻辑「目录不存在⇒跳过」对支持软链的端是假阴性——
  #   安装器不建链（建链是 step6 步骤7 手工块），AI 遵「主路径整体交安装器」漏跑步骤7 时，
  #   Skill 装进记忆中心但端上不可达，verify 却一路绿灯。
  #   正解：读 capability 判 skill_symlink——支持则缺目录=FAIL；不支持才跳过。
  _sym_ok=""
  [ -f "$_cap" ] && _sym_ok=$(grep -m1 'skill_symlink' "$_cap" 2>/dev/null | sed 's/.*skill_symlink[[:space:]]*:[[:space:]]*//' | cut -d'#' -f1 | tr -d ' ')
  if [ "$_sym_ok" = "true" ]; then
    no "Skill软链接: 端声明支持软链但 $CONFIG_ROOT/skills/ 不存在——step6 步骤7 建链未执行（Skill 端上不可达·主路径不建链·勿漏手工步）"
  else
    echo -e "${C}  [i] 本端不支持软链（skill_symlink 非 true）·跳过软链接检查${N}"
  fi
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
# 2026-10-08 扩形态：zwork 平台托管型（hooks_alternative=false）同样无 hooks/rule 硬布局——
# 其脚本面三查由 §1.6 zwork 形态 E（端实体锚点集合）承接，⛔按 settings 端硬布局判=双错位假红。
sys.exit(0 if "settings_json: false" in t and ("hooks_alternative: true" in t or "hooks_alternative: false" in t and "memory_inject: true" in t) else 1)
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

# 3.7b) 数字分身·恒驻切片链 dry-run（2026-10-11 包自检⑬·用户质证"⑫只测卡链，切片链装机时刻不可见"同病同治）
#      病灶：规格书→生成器→六片→manifest 在装机验收面零动态覆盖（静态存在校验≠生成得出）
#      ⇒ 切片链断=分身恒驻核停在旧芯而不可见。⑬用包内骨架在隔离沙箱跑真生成链（五断言），
#      ⛔不触碰端用户真实档案。rc：0=全绿 1=链断 2=参数错 3=包内件缺失(包结构缺陷)。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/slice_chain_check.py" ]; then
  # 批次9 取证腿四自证：原 >/dev/null 吞掉断言明细——真机红但哪条断言红看不见=逼人猜
  _scc_log=$(mktemp "${TMPDIR:-/tmp}/scc.XXXXXX")
  py_run "$PKG_ROOT/references/scripts/slice_chain_check.py" \
    --pkg-root "$PKG_ROOT" >"$_scc_log" 2>&1
  _scc=$?
  case "$_scc" in
    0) ok "切片链: 规格书→生成器→六片 ⑬ dry-run 五断言全绿（包骨架沙箱·零触真实档案）" ;;
    3) no "切片链: 包内生成器/骨架模板缺失（references/digital-twin/...）——包结构缺陷" ;;
    1) no "切片链: ⑬ 五断言未全绿（明细如下）"; sed 's/^/    SCC-DETAIL: /' "$_scc_log" ;;
    *) no "切片链: 检查器异常退出 rc=$_scc"; sed 's/^/    SCC-DETAIL: /' "$_scc_log" ;;
  esac
  rm -f "$_scc_log"
else
  no "切片链检查器缺失: references/scripts/slice_chain_check.py"
fi

# 3.8) 养成链在位（答题→计分→蒸馏→上线·四要素静态断言·2026-09-30 用户质证「答题在哪/蒸馏在哪」）
#      判据＝使用链逐步可达：装机入口（答题页在部署清单）+执行件（造芯三件）+文档指引（INSTALL
#      养成链节+蒸馏清单）——部署面齐件 ≠ 使用链闭环（WB-20260930-002 教训）。
_lcm=0
[ -f "$PKG_ROOT/references/digital-twin/hexaco/自建100题-答题页-v1.html" ] || _lcm=1
[ -f "$PKG_ROOT/references/digital-twin/k2-slice-generator/k2_slice_generator.py" ] || _lcm=1
grep -q '"hexaco":' "$PKG_ROOT/install_scripts.py" 2>/dev/null || _lcm=1
grep -q '分身养成链' "$PKG_ROOT/INSTALL.md" 2>/dev/null || _lcm=1
grep -q '蒸馏目标层' "$PKG_ROOT/INSTALL.md" 2>/dev/null || _lcm=1
# 2026-10-10 防作者侧回流（实证病：9-29脱敏定终态后互照全套/探针题库含本体读数H4.75回流进包
# 无人报——指纹池 2026-10-03 清空后结构守卫缺位，本断言=hexaco域「声称终态=实盘」的机械载体）
_hxg="$PKG_ROOT/references/digital-twin/hexaco"; _hx_bad=""
# 声明清单（唯一一份·双向对账：清单里有→包内必须在位；包内有→清单里必须声明）
_hx_declared=("自建100题-分身版-题库-v1.md" "自建100题-答题页-v1.html" \
"HEXACO-100完整版-官方中文-答题卡.md" "ScoringKeys_100.pdf" "hexaco_selfbuild_scorer.py" \
"hexaco_official_scorer.py" "hexaco_official_keytable-100.json")
for _hd in "${_hx_declared[@]}"; do
  [ -f "$_hxg/$_hd" ] || _hx_bad="$_hx_bad 缺:$_hd"
done
for _hf in "$_hxg"/*; do
  [ -f "$_hf" ] || continue
  _in=0
  for _hd in "${_hx_declared[@]}"; do [ "$(basename "$_hf")" = "$_hd" ] && _in=1; done
  [ "$_in" = "1" ] || _hx_bad="$_hx_bad 白名单外:$(basename "$_hf")"
done
#   「引导面」断言：脚本在包但没人被引导去跑=死件，故 INSTALL/step8 须出现调用字样
#   ⚠️ 计分器**在位**断言 2026-10-15 起不再在此硬编码——题库 §八 第4条那句自陈待办已由 §3.1d
#      通用闸（todo_landing_check.py）覆盖（实测：改名该件⇒§3.1d 报红），此处再写一遍＝双本账。
grep -q 'hexaco_selfbuild_scorer' "$PKG_ROOT/INSTALL.md" 2>/dev/null \
  || _hx_bad="$_hx_bad 缺:INSTALL.md 未引导跑自建计分器(死件风险)"
#   C34 官方卷链同口径：官方计分器＋键表在位（清单双向已覆盖在位）·引导面须出现调用字样
grep -q 'hexaco_official_scorer' "$PKG_ROOT/INSTALL.md" 2>/dev/null \
  || _hx_bad="$_hx_bad 缺:INSTALL.md 未引导跑官方计分器(死件风险)"
[ -z "$_hx_bad" ] || { _lcm=1; echo -e "${R}  [FAIL] hexaco终态对账:$_hx_bad${N}"; }
#      v2.0.1 根治（2026-09-30 Agent B 盲审 B8）：原五要素全包内静态检查（grep INSTALL 文本=只验"文档提过"）——
#      补装机态落点断言：脚本中心已存在 ⇒ 配置根 hooks/ 下分身运行时件必须在位（未装机则跳过·与§3.5同口径）。
#      2026-10-03 端形态感知（条文19）：zcode 类端分身件落点=数字分身/devtools/（[5b/8] 变换·注册指 DT_DEV），
#      ⛔ 按 hooks/ 硬布局核＝错位假红——核「注册面引用路径可达」代替硬编码位置。
if [ -d "$MC/脚本中心" ]; then
  if [ "$PLATFORM" = "zwork" ]; then
    # zwork 平台托管态（2026-10-12·条文19 端形态感知）：无 hooks/无注册面——运行时面=脚本中心实件可达
    _twin_ok=0
    [ -f "$MC/脚本中心/doenglingz_inject_prompt.py" ] && _twin_ok=1
  elif [ -f "$CFG_DIR/hooks/doenglingz_inject_prompt.py" ]; then
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

# 3.9) 检查点链完整性（改造③·2026-10-13 信任机制收口·补条文39 明载欠账"收口闸未设链判据"）
#      判据=$MC/.install/stepN-done.md 检查点链（step1~step8 含 6.5）连续：
#      · 中段断裂（前置环节缺而后续已落 done）= FAIL 报红并列断裂点——进度不可信
#      · 尾部缺失（最后 1~2 步未落 = verify 正跑在 step7 时点）= advisory 显形⛔不判死（防假红）
#      · 无 .install/ = 主线未开工·显形跳过
#      防占位（条文39§4）：done 文件 <16 字节 = 疑似「已完成」三字占位·advisory 显形
#      （硬判待存量端实测后再升——⛔无实证不升级判据强度·承「假阳性比没检查更糟」纪律）
#      ⛔AI 对话段（step4 问卷/step5 合成）内容由 AI 执行后落检查点（39§3 不许 shell 自动化），
#      本节只对账「检查点文件存在性与连续性」这一机械面——单职责不越界判内容
if [ -d "$MC/.install" ]; then
  _cchain=(step1 step2 step3 step4 step5 step6 step6.5 step7 step8)
  _clast=-1
  for _ci in "${!_cchain[@]}"; do
    [ -f "$MC/.install/${_cchain[$_ci]}-done.md" ] && _clast=$_ci
  done
  _cgaps=""
  for (( _ci=0; _ci<_clast; _ci++ )); do
    [ -f "$MC/.install/${_cchain[$_ci]}-done.md" ] || _cgaps="${_cgaps:+$_cgaps,}${_cchain[$_ci]}"
  done
  if [ -n "$_cgaps" ]; then
    no "检查点链断裂: 主线缺 ${_cgaps}（后续步骤已落 done 而前置缺失=进度不可信·补做缺失步骤后重验·判据源=条文39）"
  elif [ "$_clast" -lt 0 ]; then
    # E6 负例修复（2026-10-13 Win CI 沙盒暴露）：.install 存在但零检查点——
    #   ⛔不进 ${_cchain[-1]}（bash3.2 负索引=bad substitution 崩溃·本机实测 rc=1）
    echo -e "${C}  [i] 检查点链: .install/ 未落任何步骤检查点（安装主线未开跑·零步落账——条文39①⛔不落=该步未完成）${N}"
  elif [ "$_clast" -lt 8 ]; then
    echo -e "${C}  [i] 检查点链: 连续至 ${_cchain[$_clast]}（尾部未落=step7 跑 verify 时 step8 尚未来·正常时点）${N}"
  else
    ok "检查点链完整性: step1~step8 含 6.5 九段全在·无断裂"
  fi
  _cph=""
  for _cf in "$MC/.install/"step*-done.md; do
    [ -f "$_cf" ] || continue
    _csz=$(wc -c < "$_cf" 2>/dev/null | tr -d '[:space:]')
    [ -n "$_csz" ] && [ "$_csz" -lt 16 ] && _cph="${_cph:+$_cph }$(basename "$_cf")"
  done
  [ -n "$_cph" ] && echo -e "${C}  [i] 检查点疑似占位（条文39§2: 须为实查结果非「已完成」三字）: ${_cph}${N}"
else
  echo -e "${C}  [i] 检查点链: 未见 $MC/.install/（安装主线未开始·对账跳过）${N}"
fi

# 4) 安装包干净度（发布卫生·单一真源=references/scripts/pkg_cleanliness_check.py·双端同口径）
#    2026-09-17 童灵根治：原 grep 实现 5 类检查，与 verify.ps1（只查1类）不对称=Windows 端零防线 →
#    收口为 python 单一真源（utf-8 读，规避 PS5.1 无BOM 中文误判）。
#    检查项：私人称呼 / 用户名 / .bak 残留 / 临时残留(_tmp_*·*.tmp) / 运行时状态点文件
DIRT=0
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/pkg_cleanliness_check.py" ]; then
  # 🔴 2026-10-10 自指噪声根治：加 --fix-cache
  #    病根：门禁链路自己跑 Python（install_scripts --verify / content-gate / 本检查器）
  #    ⇒ 解释器在包内写 `__pycache__` ⇒ 本检查器随后把它当"污染"报 FAIL。
  #    真源 L80-88 已认定 pycache 是 8 类污染中**唯一可安全自动清理**的（可再生·零内容价值），
  #    并提供了 --fix-cache；但本节从未传 ⇒ 设计者给的解法一直没接上。
  #    ⛔ 其余 7 类（私人称呼/用户名/.bak/tmp/runtime/log/author_side）照报——只清 pycache，
  #      ⛔ 不许"清了一半就说干净"（真源 L301-302 的纪律）。
  if ! py_run "$PKG_ROOT/references/scripts/pkg_cleanliness_check.py" --pkg-root "$PKG_ROOT" --fix-cache --exclude-runtime; then  # 2026-10-22 R9 加 exclude-runtime·与 verify.ps1 同口径（条文68）
    # 2026-09-20 B6（群友计数口径）：原实现只置 DIRT 不调 no() → FAIL 计数不增 →
    #   检查器报多条 [FAIL] 而汇总"全过"=假绿。修法：检查器级计 1 项 + 明细口径声明。
    DIRT=1; no "安装包干净度: 检查器报污染（上方 [FAIL] 行=分类明细·__pycache__ 已自动清理·本汇总按检查器级计 1 项）"
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

# 4.5) 装后双拼产物扫描（2026-10-10 十一轮·双拼病门禁·装机面）
#      病形=波浪号斜杠紧贴绝对路径/盘符 ⇒ expanduser 静默失效（Fail-Silent）。
#      判据在检查器内 chr() 动态构造（真源=开发工具/path_integrity_check.py），
#      防安装器 _fill 改写判据自身=假绿（同 pkg_cleanliness L17 警告病）。
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/path_integrity_check.py" ]; then
  _PI_DIRS="脚本中心,数字分身,知识联邦引擎,记忆规则,技能配置,核心层,潜意识层,情境层,成就系统,记忆蓝图,未知未知,最伟大的我,自定义层,成长箱,工作日志"
  _PI_PH="AutoClaw/SOUL.md,AutoClaw/AGENTS.md,记忆规则/用户基本规则-摘要版.md,情境层/动态状态快照.md"
  if py_run "$PKG_ROOT/references/scripts/path_integrity_check.py" --root "$MC" --only-dirs "$_PI_DIRS" --placeholder-files "$_PI_PH" --quiet; then
    ok "装后产物路径完整性: 无双拼形态、无占位符残留"
  else
    py_run "$PKG_ROOT/references/scripts/path_integrity_check.py" --root "$MC" --only-dirs "$_PI_DIRS" --placeholder-files "$_PI_PH" | sed 's/^/  /'
    no "装后产物含双拼/占位符残留（上方 [FAIL] 行=明细）"
  fi
fi

# 4.6) 目录型骨架在位且非空（C16·判据=verify_pair_checks.skeleton 双端单源·本段为调用壳）
#      病形与判据细节住 py 头注（存在∧非空·断言≥1⛔硬编码件数）；2026-10-21 下沉（条文68）
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/verify_pair_checks.py" ]; then
  _skl=$("$PY" "$PKG_ROOT/references/scripts/verify_pair_checks.py" skeleton "$MC" 2>&1)
  if [ $? -eq 0 ]; then ok "目录型骨架在位且非空: $_skl"; else miss "目录型骨架: $_skl"; fi
else no "目录型骨架: 仪器未跑（python/verify_pair_checks 不可用·⛔失明期间不得判无）"; fi

# 4.7) 摘要版三表占位符闭环（C08·判据=verify_pair_checks.summary_tables 双端单源·本段为调用壳）
#      病形①②/仪器未跑分态/F13整数比较防坑均在 py 侧；2026-10-21 下沉（条文68）
_TPL="$PKG_ROOT/references/templates/用户基本规则-摘要版.md"
_INST_SUM="$MC/记忆规则/用户基本规则-摘要版.md"
if [ -n "$PY" ] && [ -f "$PKG_ROOT/references/scripts/verify_pair_checks.py" ] && [ -f "$_TPL" ]; then
  _st=$("$PY" "$PKG_ROOT/references/scripts/verify_pair_checks.py" summary-tables "$_TPL" "$_INST_SUM" 2>&1); _strc=$?
  if [ $_strc -eq 2 ] || printf '%s' "$_st" | grep -q '^INSTRUMENT='; then
    no "模板纯净: python 腿未跑（仪器未跑·$_st·⛔此为仪器故障非包污染）"
  else
    _rows=$(printf '%s' "$_st" | sed -n 's/.*ROWS=\([0-9]*\).*/\1/p')
    _bad=$(printf '%s' "$_st" | sed -n 's/.*BAD=\([^ ]*\).*/\1/p')
    _left=$(printf '%s' "$_st" | sed -n 's/.*LEFT=\([^ ]*\).*/\1/p')
    if [ "${_rows:-0}" -eq 19 ] && [ "${_bad:-1}" = "0" ]; then
      ok "模板纯净: 摘要版三表 19 行 38 格全为占位符（⛔ 不携带任何具体答案·含选项名）"
    else
      no "模板被污染: 摘要版三表应为 19 行全占位符，实测 行数=${_rows:-?} 非占位符格=${_bad:-?}（作者/选项内容不得随包出）"
    fi
    if [ -f "$_INST_SUM" ] && [ -n "${_left:-}" ] && [ "$_left" != "NA" ]; then
      if [ "${_left:-0}" -gt 0 ] 2>/dev/null; then
        miss "摘要版答案未注入: 残留占位符 ${_left} 处（step5 三表逐格替换未完成·用户画像不完整）"
      else
        ok "摘要版答案已注入: 无残留占位符"
      fi
    fi
  fi
elif [ ! -f "$_TPL" ]; then
  no "模板纯净: 模板缺失 $_TPL（包结构异常）"
else no "模板纯净: 仪器未跑（python/verify_pair_checks 不可用·⛔失明期间不得判通过）"; fi

# 5) 版本锚点（不计分·信息）
BV=$(cat "$MC/.install/version" 2>/dev/null || echo "未知(未完成安装或无锚点)")
echo -e "${C}  [i] 布洛陀版本: $BV${N}"

echo ""
if [ "$FAIL" = 0 ] && [ "$PEND" = 0 ]; then
  echo -e "${G}=== 自检通过: $PASS 项全过 ===${N}"; exit 0
elif [ "$FAIL" = 0 ]; then
  echo -e "${C}=== 机械段全绿: $PASS 项 · 待办 $PEND 项（AI 引导段未完成·答完题回来重跑 verify 即清零·待办不是故障）===${N}"; exit 0
else
  echo -e "${R}=== 自检未过: $FAIL 项失败(见上) ===${N}"; exit 1
fi
