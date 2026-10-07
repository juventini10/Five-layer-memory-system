#!/usr/bin/env bash
# doenglingz_guard.sh —— Stop 钩子·童灵守护三查（数字分身常驻守卫）
# 设计定位：童灵"守护"职能（02-治理与灰度设计规范§五）在 WorkBuddy 运行时刻的机械落点。
#   依据：宪法愿景「分身让规则在每次执行中被真正执行」+ 02规范守护三查(合规/价值/漂移)。
# 执行对象：Stop 钩子传入的最终回复文本（stdin JSON 的 .text 或 argv --text）。
# 契约：--check(JSON,含 alarm) / --report(markdown明细) / --selfcheck(挂载自检)。
# 机械边界（02规范§五.3 守护自限）：只扫成文硬红线(红区六类+铁律版关键词)，
#   价值/漂移类软信号不静默裁决→仅提示"建议你质证"，alarm 不置 true（防误拦·自主≠黑箱）。
# 台账：写 ${WORKBUDDY_CONFIG_DIR:-$HOME/.workbuddy}/doenglingz_guard_state.json（端中立·官方 env 优先）（可观测"童灵在跑"·落持久目录根治 /tmp 重启易失误报🔴）。
# 挂载：registry_guards.sh 自动发现 GUARD_DIR 下 *guard.sh → 零配置接入（第一性原理根治·文件系统单一真相源）。
# TSL 观察层 + W1 上岗兑现检测（2026-09-08 回流共脚本 doenglingz_guard.py · WB 端落地）：
#   把 AutoClaw 首创的 tsl_hits 8特征观察 + Qoder CN 的 check_w1_honor 对账，焊进 WB Stop 链，
#   让"声称上岗却没走TSL"在 WB 端可机械留痕（观察模式不裁决·对齐守护自限）。
#
# GUARD_CONTRACT: doenglingz_guard
# GUARD_VERSION: 1.2-wb-sh
# ── 面④版本对齐位声明（2026-10-06 三明治落地·registry_guards.sh 面④⑤）──
# 本件=registry 兜底形态（*.sh 自动发现·非 settings.json 显式链），与共脚本
#   doenglingz_guard.py 是**同判据的两形态**（06 §二·1「零配置优先·参考 registry」）。
# 契约名 doenglingz_guard = 与共脚本同判据；版本号独立编号，因能力集不同：
#   本件独有 = tsl_hits 8特征 + persona_tier/persona_guard 三查（.py 无此能力）。
#   本件已于 2026-10-06 追平 v1.2 会话级分账（sid 归一/触发按 sid 过滤/水位线按会话分文件
#   + --sid 显式会话号参数），⛔共脚本 .py 零改动（端中立）。隔离压测旧版vs新版同场景对照：
#   旧版串账假红(not_honored)+写全局单槽 / 新版放行+按会话分文件。
#   版本号 = 1.2-wb-sh：分账能力已对齐 v1.2，后缀标形态（兜底件非正挂点件）。
# ── 二次追平（2026-10-06 下午·皮叔令「杜绝发现的这些问题」·06 §2.2.9-补 (A) WB 端收口）──
#   W1 兑现判据从「只认'童灵上岗'四字」升级为共脚本 v1.121 全件按序：
#   _identity_anchors() 同源读规格书 §1.1 上岗身份声明（与 injector/共脚本同源·读失败回退旧变体
#   保守放行）+ _d3_ritual_full_ordered()（D3 自报回合须身份声明→TSL 树按序齐全·D1/D2 返 None
#   不误伤）。判据逐字照 py 件移植，⛔共脚本零改动。契约版本仍对齐基线 1.2（面④比对不触红）。
#   隔离压测 11/11（验证卡 8 用例分层 A 口径 + 触发在场 B 组合 3 例）/tmp/dlz_ritual_test.py。
set -uo pipefail
# B修源·声明驱动口径v2(2026-10-06·条文47·B修源46支·env三档默认删除+机器名清零)：
# 根唯一来源=runtime_paths 声明(相对脚本目录解析·解析器已 realpath 下沉=软链/实体入口均可达)；
# ⛔消费侧默认兜底已删，无声明 hard fail+指引句自带即教育。
MC="$(python3 "$(dirname "$0")/../../脚本中心/runtime_paths.py" get archive_root 2>/dev/null)" \
  || { echo "❌ doenglingz_guard: 读不到 runtime_paths 声明·作者机先跑 脚本中心/runtime_paths.py build / 端用户机跑安装器(条文47)" >&2; exit 1; }

# —— 取待检文本 + 载荷键：优先 argv --text，其次 stdin JSON（宽容多键·对齐 ZCode 范本）——
# TEXT_KEYS：Stop 载荷文本候选键（宽容读取·命中第一个非空字符串即止）。
#   responseText/last_assistant_message = 运行时 Stop 载荷实测键。
TEXT_KEYS=("text" "prompt" "content" "responseText" "response" "message" "last_assistant_message" "last_message" "responsePreview" "output" "assistant_message")

extract_payload() {
  # 读 stdin（Stop 钩子传入的 JSON payload），返回 JSON {"text":..., "keys":...}
  python3 -c '
import sys, json
raw = sys.stdin.read() or "{}"
try:
    d = json.loads(raw)
except Exception:
    d = {}
if not isinstance(d, dict):
    d = {"__value__": str(d)}
KEYS = ["text","prompt","content","responseText","response","message","last_assistant_message","last_message","responsePreview","output","assistant_message"]
t = ""
for k in KEYS:
    v = d.get(k)
    if isinstance(v, str) and v.strip():
        t = v
        break
keys = ",".join(sorted(d.keys()))
sys.stdout.write(json.dumps({"text": t, "keys": keys, "session_id": str(d.get("session_id") or "")}, ensure_ascii=False))
' 2>/dev/null
}

# selfcheck 模式不读 stdin（避免 python 无输入阻塞）；--text 直接取 argv
TEXT=""
STDIN_KEYS=""
SESSION_ID=""
# --sid 显式会话号（2026-10-06 落地·对齐共脚本 .py v1.2 的 --sid）
# 病根：--text 形态原把 SESSION_ID 硬设 "(argv)" 字符串（非真 sid）⇒ 会话级分账
#   在该形态下永远匹配不到触发 ⇒ 全放行（判据形同空转）。加此参数后调用方
#   （hermes 等无 stdin 载荷的 --text 调用方）可显式传真 sid，分账才真正生效。
ARGV_SID=""
_prev=""
for _a in "$@"; do
  if [ "$_prev" = "--sid" ]; then ARGV_SID="$_a"; fi
  _prev="$_a"
done
if [ "${1:-}" = "--text" ] && [ -n "${2:-}" ]; then
  TEXT="$2"
  STDIN_KEYS="(argv --text)"
  SESSION_ID="${ARGV_SID:-(argv)}"
elif [ "${1:-}" != "--selfcheck" ]; then
  PAYLOAD=$(extract_payload)
  TEXT=$(printf '%s' "$PAYLOAD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('text',''))" 2>/dev/null)
  STDIN_KEYS=$(printf '%s' "$PAYLOAD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('keys',''))" 2>/dev/null)
  # 会话级判据数据基础（段0·皮叔拍板 A 会话级）：从 Stop 载荷提取 session_id，写入台账供消费端按会话聚合
  SESSION_ID=$(printf '%s' "$PAYLOAD" | python3 -c "import sys,json;print(json.load(sys.stdin).get('session_id','') or '')" 2>/dev/null)
fi

# —— 红区六类硬关键词（02规范§二·不可逆+影响身份）——
# 仅作"提示性扫描"：机械命中代表"此回复可能涉及红区动作"，须你/AI 复核，不直接拦。
RED_ZONE_PAT='(删除记忆|清空调|rm -rf|跨根迁移|对外发布|发布视频|发布文章|发布安装包|变更SOUL|改铁律|信用授权|新授权|收回授权|记忆架构根变更)'

# —— 铁律/记忆规则硬触线（005删除防护/001先看清等·可机械判定）——
# 反模式：回复里出现"rm -rf"针对个人目录、"直接删了"无 trash 语境等。
HARD_VIOLATION_PAT='(rm -rf ~|rm -rf /Users|rm -rf \$HOME|直接 rm |直接删除.*(Desktop|Downloads|Documents))'

# —— TSL 会话执行特征观察层 + W1 上岗兑现检测（2026-09-08 回流共脚本·WB 端落地）——
# tsl_hits：从回复文本机械观察 L3-L7 各层是否真执行（8特征·观察模式不裁决）。
# w1_status：最近一次未消费的 WB 端 W1 触发 → 回复须含"童灵上岗"自证词，否则记 not_honored。
# 失败默认放行（Hook 三纪律）。
TSL_W1_JSON=$(printf '%s' "$TEXT" | DG_MC="$MC" DG_SESSION_ID="$SESSION_ID" python3 -c '
import sys, json, os, re
from datetime import datetime
text = sys.stdin.read()
TSL_MARKER_PATTERNS = {
    "ts_l3_ritual": r"童灵上岗",
    "ts_l3_slice_report": r"命中域切片",
    "ts_l4_loaded": r"(切片：?L[2-5]|L[2-5]_[^，。\s]{2,12}\.md)",
    "ts_l5_selfcheck": r"(守护三查|8要素|试金石)",
    "ts_l6_sync": r"(state_bus|watcher|in sync|全绿)",
    "ts_l7_growth": r"(成长箱|LRN-)",
    "ts_l7_syslog": r"系统日志[^\n]{0,20}已写入",
    "ts_l7_reflection": r"(\[童灵思考\]|--reflection)",
}
TSL_MARKER_RE = {k: re.compile(v) for k, v in TSL_MARKER_PATTERNS.items()}
# ── 树行自指污染修复（2026-10-06·L5 MISS 根治配套·v1.2.1-wb）──
# 病灶（实锤）：relay 的机械树行本身含特征词——「├─ L5 守护三查 🔴…」「├─ L7-1 错误→成长箱…」——
# 原文匹配 = 树给自己作证。实证：上会话 122 条回复 0 条🧪痕行、ts_l5_selfcheck 5 次命中全部
# 来自树行而非 AI 亲写。危害双面：观察层假命中（把没做记成做了）；且 tsl_verify v0.11.5 把
# L5 对账口径切到本台账 ts_l5_selfcheck 后，不修此条=永久假绿（全绿幻觉红线）。
# 修法：机械树行（├─/└─/🧾/🧮/🔏/📌/📄/【TSL 开头）一律剥除后再匹配——8特征观察对象=AI
# 亲写的非树行文本；🧪 8要素 法定痕行不在剥除面（🧪 开头不命中剥除正则）。
_OBS_TREE_LINE = re.compile(r"^(├─|└─|🧾|🧮|🔏|📌|📄|【TSL)")
obs_text = "\n".join(l for l in (text or "").splitlines() if not _OBS_TREE_LINE.match(l.strip()))
tsl_hits = sorted(k for k, r in TSL_MARKER_RE.items() if r.search(obs_text))
# 段1（2026-09-09·皮叔授权开工）：反思通道 ts_l7_reflection 的信号源不在回复文本——
# 其产出物 = 当日系统日志里的 [童灵思考] 条目（append_log_entry.py --reflection 写入）。
# 补机械判据：日志含 [童灵思考] → 记命中。⛔不依赖 AI 在回复里写标记
# （实证：1 次命中来自"在回复里谈论 --reflection 这个词"=假命中·声明≠执行·PAT-020 同族）。
if "ts_l7_reflection" not in tsl_hits:
    try:
        _lp = os.path.join(os.environ["DG_MC"], "工作日志/系统日志/系统日志_%s.md" % datetime.now().strftime("%Y-%m-%d"))
        if os.path.exists(_lp):
            with open(_lp, encoding="utf-8") as _lf:
                if "[童灵思考]" in _lf.read(1000000):
                    tsl_hits.append("ts_l7_reflection")
                    tsl_hits = sorted(tsl_hits)
    except Exception:
        pass
INJECT_STATE = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "doenglingz_inject_state.json")
W1_WATERMARK = os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "doenglingz_w1_watermark_workbuddy")
THIS_SRC = "workbuddy"
W1_PROOF = "童灵上岗"
# ── W1 兑现判据 v1.121 全件按序（2026-10-06 二次追平·逐字照共脚本 py 件移植·⛔共脚本零改动）──
_DLZ_SSOT_SPEC = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身", "童灵·人格规格书.md")
def _identity_anchors():
    try:
        for ln in open(_DLZ_SSOT_SPEC, encoding="utf-8"):
            if "上岗身份声明全文" in ln and "：" in ln:
                s = ln.split("：", 1)[1].strip()
                core = s.split("——")[-1].split("，")[0].strip()
                return tuple(x for x in (s, core) if len(x) >= 4) or ("别指望我永不犯错",)
    except Exception:
        pass
    return ("别指望我永不犯错", "我是你的数字分身", "我是你的数字分身")
def _d3_ritual_full_ordered(text):
    if not text:
        return None
    is_d3 = ("D3 上岗" in text) or ("童灵·D3" in text) or ("童灵上岗" in text and "上岗模式" in text)
    if not is_d3:
        return None
    _ida = _identity_anchors()
    has_id = any(a in text for a in _ida)
    has_tsl = ("🔏" in text) or ("TSL-stamp" in text) or ("├─ L0" in text)
    if not (has_id and has_tsl):
        return False
    _pos = [text.find(a) for a in _ida if a in text]
    idx_id = max(_pos) if _pos else -1
    idx_tsl = min([i for i in (text.find("🔏"), text.find("TSL-stamp"), text.find("├─ L0")) if i >= 0] or [10**9])
    return idx_id <= idx_tsl
# 会话号自 env 取（宿主 SESSION_ID 变量传不进来·内嵌 python 块是独立解释器）
SESSION_ID = os.environ.get("DG_SESSION_ID", "")
w1_status = None
try:
    if os.path.exists(INJECT_STATE):
        # ── W1 会话级分账 v1.2 对齐（2026-10-06 落地·键20261006_125446）──
        # 病根：本件停在 v1.0 全局单槽——A 会话触发被 B 会话 Stop 消费 ⇒ B 从未被注入却被打红
        #   （与共脚本 doenglingz_guard.py v1.2 的差距：缺 sid 归一 / 缺 sid 过滤 / 水位线不分文件）。
        # ⛔ 端中立：逻辑照共脚本 v1.2 权威实现移植，⛔不改共脚本迁就本件。
        # 归一权威＝共脚本 `_norm_sid`（触发侧带 '.session.execution' 后缀·Stop 侧不带·不归一则同会话判异会话）。
        def _norm_sid(sid):
            return str(sid or "").replace(".session.execution", "")
        _sid = _norm_sid(SESSION_ID)
        if not _sid:
            raise ValueError("no session id")   # 拿不到会话标识=不可判·保守放行（不追缴）
        last_w1 = ""
        with open(INJECT_STATE, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("w1") is True and d.get("src") == THIS_SRC:
                    t_sid = _norm_sid(d.get("session_id", ""))
                    # 他会话触发不归本会话消费（v1.2 主修）；无 sid 触发=不可归账·保守不冤枉
                    if not t_sid or t_sid != _sid:
                        continue
                    if str(d.get("ts", "")) > last_w1:
                        last_w1 = str(d.get("ts", ""))
        if last_w1:
            # 水位线按会话分文件（同会话防重复检·跨会话互不消耗）
            import re as _re
            wm = W1_WATERMARK + "_" + _re.sub(r"[^A-Za-z0-9._-]", "_", _sid)
            seen = ""
            if os.path.exists(wm):
                with open(wm, encoding="utf-8") as f:
                    seen = f.read().strip()
            if last_w1 != seen:
                with open(wm, "w", encoding="utf-8") as f:
                    f.write(last_w1)
                _base = W1_PROOF in (text or "")
                if not _base:
                    w1_status = False
                else:
                    _ritual = _d3_ritual_full_ordered(text or "")
                    w1_status = _base if _ritual is None else _ritual
except Exception:
    w1_status = None
print(json.dumps({"tsl_hits": tsl_hits, "w1_status": w1_status}, ensure_ascii=False))
' 2>/dev/null)
TSL_HITS=$(printf '%s' "$TSL_W1_JSON" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin).get('tsl_hits',[])))" 2>/dev/null)
W1_STATUS=$(printf '%s' "$TSL_W1_JSON" | python3 -c "import sys,json;v=json.load(sys.stdin).get('w1_status');print('not_honored' if v is False else ('honored' if v is True else ''))" 2>/dev/null)

alarm=false
red_hits=""
hard_hits=""

if [ -n "$TEXT" ]; then
  red_hits=$(printf '%s' "$TEXT" | grep -oE "$RED_ZONE_PAT" | sort -u | tr '\n' ',' | sed 's/,$//')
  hard_hits=$(printf '%s' "$TEXT" | grep -oE "$HARD_VIOLATION_PAT" | sort -u | tr '\n' ',' | sed 's/,$//')
  # 硬触线(不可逆删除类)→ 真报警（机械可判·须拦）
  [ -n "$hard_hits" ] && alarm=true
fi

# —— W4 人格对账（段三·2026-09-13·并入现有三查·⛔不另起第二条 Stop 链）——
# 判据边界（S006 防假绿·方案 §三 诚实边界）：只扫**机械可判**的三项——
#   ①企业腔禁例（硬判据·与切片「企业腔禁例」段对齐）
#   ②W4 注入态（读采样台账·按 session_id 匹配末条）
#   ③守护档粗兑现（词面近似·观察层·不裁决）
#   ⛔"腔调是否自然"是语义判断，机械判不了——不造假判据，显式留人工抽检。
PERSONA_JSON=$(printf '%s' "$TEXT" | DG_SESSION_ID="$SESSION_ID" python3 -c '
import sys, json, os, re
text = sys.stdin.read() or ""
sid = os.environ.get("DG_SESSION_ID", "")
CORP_PATS = [r"很高兴为您服务", r"非常棒[，,][^。]{0,12}探讨", r"希望对您有帮助",
             r"祝您生活愉快", r"有什么可以帮到您", r"感谢您的耐心等待"]
corp = sorted({m.group(0)[:10] for p in CORP_PATS for m in re.finditer(p, text)})
tier, hits = "", []
try:
    with open(os.path.join(os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"), "doenglingz_w4_samples.jsonl"), encoding="utf-8") as f:
        rows = []
        for ln in f:
            try:
                d = json.loads(ln)
            except Exception:
                continue
            # 兼容早期采样（无 session_id 字段）：一并纳入候选——否则加字段前的
            # 记录全被滤掉 ⇒ 对账静默失效（2026-09-13 实测首跑即踩·tier 空）。
            if not sid or not d.get("session_id") or d.get("session_id") == sid:
                rows.append(d)
    if rows:
        tier = rows[-1].get("tier", "")
        hits = rows[-1].get("guard_hits", []) or []
except Exception:
    pass
pb = ""
if hits:
    PB_ACT = [r"拦", r"替代方案", r"不建议", r"先盘", r"约束", r"不确定", r"⚠️"]
    pb = "delivered" if any(re.search(x, text) for x in PB_ACT) else "missing"
print(json.dumps({"corp": corp, "tier": tier, "guard": hits, "pb": pb}, ensure_ascii=False))
' 2>/dev/null)
PERSONA_CORP=$(printf '%s' "$PERSONA_JSON" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin).get('corp',[])))" 2>/dev/null)
PERSONA_TIER=$(printf '%s' "$PERSONA_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('tier',''))" 2>/dev/null)
PERSONA_GUARD=$(printf '%s' "$PERSONA_JSON" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin).get('guard',[])))" 2>/dev/null)
PERSONA_PB=$(printf '%s' "$PERSONA_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin).get('pb',''))" 2>/dev/null)

# —— 台账（可观测）：单行 JSON 追加，保证 tail -n 1 = 最后一条记录 ——
# selfcheck 不写台账（避免污染"真实调用"记录·与 ZCode 版同构）。
if [ "${1:-}" != "--selfcheck" ]; then
  TS=$(date "+%Y-%m-%dT%H:%M:%S")
  EXTRA=""
  [ -n "$TSL_HITS" ] && EXTRA="$EXTRA,\"tsl_hits\":\"$TSL_HITS\""
  [ -n "$W1_STATUS" ] && EXTRA="$EXTRA,\"w1_not_honored\":\"$W1_STATUS\""
  [ -n "$PERSONA_TIER" ] && EXTRA="$EXTRA,\"persona_tier\":\"$PERSONA_TIER\""
  [ -n "$PERSONA_GUARD" ] && EXTRA="$EXTRA,\"persona_guard\":\"$PERSONA_GUARD\""
  [ -n "$PERSONA_PB" ] && EXTRA="$EXTRA,\"persona_pb\":\"$PERSONA_PB\""
  [ -n "$PERSONA_CORP" ] && EXTRA="$EXTRA,\"corp_tone_hits\":\"$PERSONA_CORP\""
  printf '{"ts":"%s","session_id":"%s","text_len":%d,"red_zone_hits":"%s","hard_violation_hits":"%s","stdin_keys":"%s","alarm":%s%s}\n' \
    "$TS" "$SESSION_ID" "${#TEXT}" "$red_hits" "$hard_hits" "$STDIN_KEYS" "$alarm" "$EXTRA" \
    >> "${WORKBUDDY_CONFIG_DIR:-$HOME/.workbuddy}/doenglingz_guard_state.json" 2>/dev/null || true
fi

if [ "${1:-}" = "--text" ]; then
  mode="--check"
else
  mode="${1:---check}"
fi
if [ "$mode" = "--selfcheck" ]; then
  # 挂载自检：不读 stdin（避免 python 无输入阻塞），直接查挂载态
  GUARD_DIR="${GUARD_DIR:-$MC/开发工具/changelog-guard}"
  here=$(basename "$0")
  if ls "$GUARD_DIR"/*guard.sh 2>/dev/null | grep -q "$here"; then
    discovered="✅ 是"
  else
    discovered="❌ 否·未进GUARD_DIR"
  fi
  if [ -x "$0" ]; then exec_ok="是"; else exec_ok="否(chmod +x缺失)"; fi
  last="（无调用台账·尚未被Stop链实际调用）"
  if [ -f "${WORKBUDDY_CONFIG_DIR:-$HOME/.workbuddy}/doenglingz_guard_state.json" ]; then
    last=$(tail -n 1 "${WORKBUDDY_CONFIG_DIR:-$HOME/.workbuddy}/doenglingz_guard_state.json" 2>/dev/null)
  fi
  echo "## 🔍 童灵守卫挂载自检 (doenglingz_guard.sh · WorkBuddy)"
  echo ""
  echo "| 检查项 | 结果 |"
  echo "|---|---|"
  echo "| 被 registry 自动发现 | ${discovered} |"
  echo "| 可执行位 | ${exec_ok} |"
  echo "| TSL 观察层 + W1 对账 | ✅ 已焊入（tsl_hits 8特征 + w1_not_honored 全件按序 v1.121） |"
  echo "| 最近一次实际调用台账 | ${last} |"
  echo ""
  echo "> 各项正常=童灵守护已在WB运行时刻生效（含TSL机械自证层）；任一异常=机制静默失效（须修）。"
  exit 0
elif [ "$mode" = "--check" ]; then
  printf '{"text_len": %d, "red_zone_hits": "%s", "hard_violation_hits": "%s", "alarm": %s, "tsl_hits": "%s", "w1_not_honored": "%s", "persona_tier": "%s", "persona_guard": "%s", "persona_pb": "%s", "corp_tone_hits": "%s"}\n' \
    "${#TEXT}" "$red_hits" "$hard_hits" "$alarm" "$TSL_HITS" "$W1_STATUS" "$PERSONA_TIER" "$PERSONA_GUARD" "$PERSONA_PB" "$PERSONA_CORP"
elif [ "$mode" = "--report" ]; then
  if [ "$alarm" = false ] && [ -z "$red_hits" ] && [ -z "$TSL_HITS" ] && [ -z "$W1_STATUS" ] && [ -z "$PERSONA_TIER" ]; then
    echo "✅ 童灵守护三查 + TSL 观察：未检出硬红线触线，红区/特征无命中"
    exit 0
  fi
  echo "## ⚠️ 童灵守护三查 + TSL 会话观察"
  echo ""
  if [ -n "$hard_hits" ]; then
    echo "### 🔴 硬触线（已报警·须复核）"
    echo "| 命中模式 | 说明 |"
    echo "|---|---|"
    echo "| ${hard_hits} | 可能涉及不可逆删除·须确认走 trash 而非 rm |"
    echo ""
  fi
  if [ -n "$red_hits" ]; then
    echo "### 🟡 红区提示（建议你质证·非静默裁决）"
    echo "| 可能涉及红区 | 依据(02规范§二) |"
    echo "|---|---|"
    echo "| ${red_hits} | 红区六类之一·须你亲裁·分身不代批 |"
    echo ""
  fi
  if [ -n "$TSL_HITS" ]; then
    echo "### 🟢 TSL 会话执行特征观察（2026-09-08 回流·观察模式不裁决）"
    echo "| 命中特征 | 含义 |"
    echo "|---|---|"
    echo "| ${TSL_HITS} | L3-L7 各层机械命中·对账蒸馏消费 |"
    echo ""
  fi
  if [ -n "$PERSONA_TIER" ]; then
    echo "### 🟢 W4 人格对账（注入—兑现·观察模式·2026-09-13）"
    echo "| 项 | 值 |"
    echo "|---|---|"
    echo "| 注入档位 | ${PERSONA_TIER} |"
    echo "| 守护命中 | ${PERSONA_GUARD:-—} |"
    echo "| 守护兑现粗判 | ${PERSONA_PB:-—} |"
    echo "| 企业腔禁例 | ${PERSONA_CORP:-无} |"
    echo ""
  fi
  if [ -n "$W1_STATUS" ]; then
    if [ "$W1_STATUS" = "not_honored" ]; then
      echo "### 🔴 W1 上岗契约未兑现（w1_not_honored）"
      echo "> 本回合 W1 触发但回复未含'童灵上岗'自证词→登记 not_honored·供岗位3周报"
    else
      echo "### 🟢 W1 上岗契约已兑现（honored）"
    fi
    echo ""
  fi
  echo "> 机械部分脚本已填；价值/漂移类软信号不在此静默裁决（02规范§五.3 守护自限），须你/AI 复核。"
else
  echo "用法: doenglingz_guard.sh [--check|--report|--text <text>]"
  exit 2
fi
