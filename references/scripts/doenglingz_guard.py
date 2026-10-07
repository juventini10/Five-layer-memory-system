#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/doenglingz_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
"""doenglingz_guard.py —— Stop 钩子·童灵守护三查（数字分身常驻守卫·Qoder CN 端）
设计定位：童灵"守护"职能（02-治理与灰度设计规范§五）在 Qoder CN 运行时刻的机械落点。
  依据：宪法愿景「分身让规则在每次执行中被真正执行」+ 02规范守护三查(合规/价值/漂移)。
执行对象：Stop 钩子传入的最终回复文本（stdin JSON 的 .text/.prompt/.content）。
契约：--check(JSON,含 alarm) / --report(markdown明细) / --selfcheck(挂载自检)。
机械边界（02规范§五.3 守护自限）：只扫成文硬红线(红区六类+铁律版关键词)，
  价值/漂移类软信号不静默裁决→仅提示"建议你质证"，alarm 不置 true（防误拦·自主≠黑箱）。
台账：写 <配置根>/doenglingz_guard_state_<--src>.json（配置根三段解析·2026-10-01 端隔离根治·默认 ~/.workbuddy·持久目录·根治 /tmp 清理误判）。
跨端适配：06-跨端适配规范§二（内核不分端·装载分态·本端适配器）。
v1.1（2026-10-01·Hermes 端 T0 实测根治·Hermes 🪶）：端隔离修复——STATE_FILE/INJECT_STATE/W1_WATERMARK
  三处去写死 ~/.workbuddy/，改随三段配置根（DOENGLINGZ_CONFIG_DIR > WORKBUDDY_CONFIG_DIR > 默认）；
  水位线文件名按 --src 派生（原写死 qodercn ⇒ 各端共用一条·串端）。⛔判定逻辑零变更，仅落点参数化。
v1.2（2026-10-06·Qoder CN 童灵·W1兑现对账链根治·任务卡 2026-10-06-W1）：
  ① 会话级分账：check_w1_honor 只吃**同 session_id** 的触发，水位线按会话分文件——
     根治全局单槽水位线跨会话消费（实证 20 红抽样 14 条=非D3回合被其它会话/窗口的触发
     追缴自证=假阳；task-* 子会话触发与主会话 Stop 互吃）。src 过滤（v1.1）不够——
     同端多窗口并发时单槽仍互吃。
  ② transcript 兜底：Stop 载荷拿不到消息文本时读 transcript_path 末条 assistant 正文
     （SubagentStop 案已开过这条路·transcript_reader 单一真源，import 失败静默降级=保守放行）。
  ③ --self-test 夹具：串会话必被过滤/会话级 honored/跨端触发必被过滤/空载荷 transcript 兜底 负例。
  ④ v1.2.1（2026-10-06·ZCode 端 SSOT 归一轮补）：自测夹具 T 补 🔏 全件形态——同日 _d3_ritual_full_ordered 升级后原夹具（无 TSL 标记）C2/C5 必红（7/7 不可达）；判定逻辑零变更·仅测试件对齐。
── 存量定谳（pre-fix 红=存量，消费侧 cutoff 不计新增报警·先例=qodercn_config_guard v0.14）──
cutoff=2026-10-06T08:52（本修落盘时刻·各端以本端挂载适配完成时刻为各自 cutoff）
逐端红存量与真假机械分类（取数脚本 qoder-cn-work/steps/w1_stock_adjud/sample3_20261006）：
  qodercn   红120 绿21     | 定谳假阳22（会话从未被W1注入）·无sid不可归账5·有触发待深核93
                             （20红人工抽样：14 非D3回合被转嫁=假阳 / 2 时序·判定面 / 4 不可核）
  workbuddy 红139 绿77     | 假阳7·无sid 5·待深核127
  zcode     红78(布尔) 绿368 | 抽3条 stop 侧全无 session_id=不可归账（分叉脚本未采会话·SSOT归一挂派单卡）
  lobsterai 红67 绿0        | 同上全无 sid；且其注入台账 w1 触发带 sid 数=0（注入器未传 session 载荷）
  hermes    红37 绿26      | 同上全无 sid（--text 模式不传会话）→ v1.2 后自动转 None 放行，
                             补 --sid 即恢复信号（见派单卡 2026-10-06-W1对账链-G3派单卡.md）
结论：红≠dishonor 已量化——跨会话转嫁在 qodercn 有硬假阳实锤，他端红面主体为"不可归账"
（结构同病：stop 侧无会话标识），v1.2 使其⛔不再被冤枉、也不再假装可判。周报口径按 cutoff 分存量/新增。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import json
import re
import os
from datetime import datetime

# ── 台账路径（Qoder CN 端专属·与 WB 端 /tmp/doenglingz_guard_state.json 区分）──
# 2026-09-01 迁持久目录：原 /tmp 会被系统清理（实测 09:02 /tmp 清空致台账消失→对账误判守卫未跑）
# 对齐岗位3判据 v1.7「事件驱动守卫台账落点迁 ~/.workbuddy/（持久·根治重启清空）」
# 端标识（2026-09-11 端中立参数化）：--src <name> 覆盖·默认 qodercn 保持向后兼容
_SRC = "qodercn"
_a = sys.argv[1:]
if "--src" in _a and _a.index("--src") + 1 < len(_a):
    _SRC = _a[_a.index("--src") + 1].strip() or "qodercn"
# 三段配置根（2026-10-01 端隔离根治·对齐 doenglingz_inject_prompt.py L83 形态）：
#   DOENGLINGZ_CONFIG_DIR（install_scripts --platform 写进钩子命令·端专属落点）
#   > WORKBUDDY_CONFIG_DIR（向后兼容缝·lobsterai 已在用）
#   > ~/.workbuddy（旧默认行为·WB/Qoder CN 端不变）
# 病灶：原式只认 WORKBUDDY_CONFIG_DIR，⛔不认 DOENGLINGZ_CONFIG_DIR ⇒ 非 WB 端调本脚本
#       会把守护台账写进 ~/.workbuddy/（Hermes 端 2026-10-01 实测踩中·已还原留证）。
_DLZ_CFG = (os.environ.get("DOENGLINGZ_CONFIG_DIR")
            or os.environ.get("WORKBUDDY_CONFIG_DIR")
            or os.path.expanduser("~/.workbuddy"))
STATE_FILE = os.path.join(_DLZ_CFG, f"doenglingz_guard_state_{_SRC}.json")

# ── 红区六类硬关键词（02规范§二·不可逆+影响身份）──
# 仅作"提示性扫描"：机械命中代表"此回复可能涉及红区动作"，须你/AI 复核，不直接拦。
RED_ZONE_PATTERNS = [
    r"删除记忆", r"清空调", r"rm\s+-rf",
    r"跨根迁移", r"对外发布", r"发布视频", r"发布文章", r"发布安装包",
    r"变更\s*SOUL", r"改铁律", r"信用授权", r"新授权", r"收回授权",
    r"记忆架构根变更",
]

# ── 铁律/记忆规则硬触线（不可逆删除类·可机械判定）──
HARD_VIOLATION_PATTERNS = [
    r"rm\s+-rf\s+~", r"rm\s+-rf\s+/Users", r"rm\s+-rf\s+\$HOME",
    r"直接\s+rm\s", r"直接删除.*(Desktop|Downloads|Documents)",
]

# ── 认知深化信号关键词（v0.2 新增·2026-08-26·童灵第五入口沉淀机制）──
# 检测到这些关键词时，提醒 AI 使用 system-logger --reflection 添加 [童灵思考] 标记
REFLECTION_SIGNAL_PATTERNS = [
    r"今天.*收获", r"今天.*学到", r"今天.*发现",
    r"我.*发现", r"我.*意识到", r"我.*认识到",
    r"认知深化", r"经验沉淀", r"童灵.*沉淀",
    r"分母统一", r"口径统一", r"标准统一",
    r"自动化优先", r"SSOT", r"唯一真源",
]

RED_ZONE_RE = re.compile("|".join(RED_ZONE_PATTERNS))
HARD_VIOLATION_RE = re.compile("|".join(HARD_VIOLATION_PATTERNS))
REFLECTION_SIGNAL_RE = re.compile("|".join(REFLECTION_SIGNAL_PATTERNS))

# ── TSL 会话执行特征观察层（2026-09-08·回流自 AutoClaw 端 v1.3.0 全系首创·对齐哲学 v1.57 双层评级+08 清单）──
# 8 特征 · 观察模式不裁决（守护自限·供蒸馏与对账消费）——从回复文本机械观察各层是否真执行，
# 让「未列 TSL 清单就声称上岗」留可审计空档（🟡 从「待人工确认」向「可机械观察」逼近一步）。
# 回流动机：AutoClaw 端首创后锁在插件本体；回流共脚本=SSOT 单一真源，一处改对 WB/Qoder CN/ZCode/DSH/AutoClaw 全端生效。
#   观察模式：只记 tsl_hits 台账字段，⛔不阻断不裁决（对齐守护自限·02规范§五.3）。
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


# 实测本端 Stop 载荷键（2026-09-04 取证 ~/.qoder-cn/logs/crossend_guard.jsonl
# payload_keys=['cwd','extra','hook_event_name','last_assistant_message','request_set_id',
#               'session_id','transcript_path']）——原实现只读 text/prompt/content，
# 三个键本端从来不存在 ⇒ 守护 305 次调用 305 次 text_len=0，扫空文本＝形式在跑功能空转
# （同构病灶 ZCode v1.19 / WB 2026-08-29 均已根治，本端漏修）。
TEXT_KEYS = [
    "last_assistant_message", "text", "prompt", "content", "responseText",
    "responsePreview", "message", "finalMessage", "assistant_message", "output",
    "stopReason", "result",
]


def get_text_from_stdin():
    """宽容提取 Stop 载荷文本 + 留痕真实键集（多端共用一个脚本时的自证手段）。"""
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace') or "{}"
        d = json.loads(raw)
    except Exception:
        d = {}
    if not isinstance(d, dict):
        d = {}
    t = ""
    for k in TEXT_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            t = v
            break
    _STDIN_KEYS[0] = ",".join(sorted(d.keys()))
    _SESSION_ID[0] = str(d.get("session_id", "") or "")
    _TRANSCRIPT_PATH[0] = str(d.get("transcript_path", "") or "")
    return t if isinstance(t, str) else json.dumps(t, ensure_ascii=False)


_STDIN_KEYS = [""]
_SESSION_ID = [""]
_TRANSCRIPT_PATH = [""]


def _norm_sid(sid):
    """会话 id 归一（v1.2）：触发侧带 '.session.execution' 后缀、Stop 侧不带，
    不归一则同会话判不同会话。"""
    return str(sid or "").replace(".session.execution", "")


def _fallback_transcript_text():
    """v1.2 缺口②兜底：载荷无消息文本时读 transcript 末条 assistant 正文。
    transcript_reader 不可用（端侧未部署）→ 返空串=维持原放行（保守不冤枉）。"""
    tp = _TRANSCRIPT_PATH[0]
    if not tp or not os.path.isfile(tp):
        return ""
    for _p in (os.path.dirname(os.path.abspath(__file__)),
               os.path.expanduser("[记忆共享中心]/脚本中心"),
               os.path.expanduser("[记忆共享中心]/脚本中心")):
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
    try:
        import transcript_reader as _tr
        return _tr.last_assistant_text(tp) or ""
    except Exception:
        return ""


# ── W1 上岗兑现检测（2026-09-04 移植·契约第③条在本端从"空头承诺"变机械可检）──
# 台账与水位线（2026-10-01 端隔离根治·⛔判据未动·仅落点参数化）：
# 病灶：两处均写死 ~/.workbuddy/ ⇒ 非 WB 端 W1 兑现对账恒返回 None（读不到本端注入台账）
#      = **L7① 在所有非 WB 端事实哑火**；且水位线文件名写死 qodercn ⇒ 各端共用一条水位线（串端）。
# 修法：随 _DLZ_CFG 走；水位线文件名按 --src 派生（qodercn 端默认配置根下文件名不变·向后兼容）。
# ⚠️ 旧 ~/.workbuddy/doenglingz_w1_watermark_qodercn 刻意保留不删（他端在用·⛔不破坏他端数据）。
INJECT_STATE = os.path.join(_DLZ_CFG, "doenglingz_inject_state.json")
W1_WATERMARK = os.path.join(_DLZ_CFG, f"doenglingz_w1_watermark_{_SRC}")
W1_PROOF = "童灵上岗"
THIS_SRC = _SRC   # 端标识跟随 --src（2026-09-11 端中立参数化）


_DLZ_SSOT_SPEC = os.path.join(os.path.expanduser("~"), "~/个人AI档案", "数字分身", "童灵·人格规格书.md")


def _identity_anchors():
    """从规格书 §1.1 读「上岗身份声明全文」真源→(整句, 核心子句) 供检测侧同源。
    PAT-082 根治：旧 has_id/idx_id 硬编码三变体，与 injector 读真源不同源 ⇒ 真源一改即全端 D3 假红。
    读不到真源 → 回退旧三变体（⛔不因读失败制造新假红·保守放行同族）。"""
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
    """D3上岗回合须「全件+按序」：身份声明 → (域判定) → TSL树，且顺序成立。
    仅当回复自报 D3 档位时启用（D1/D2 无 TSL 义务→返回 None 不约束）；
    非 D3 或不可判→None（放行）。这是把"后壳"从"只认童灵上岗四字"升级为"兜住06 §2.2.6三层件全件按序"（2026-10-06 你令彻底根治）。"""
    if not text:
        return None
    is_d3 = ("D3 上岗" in text) or ("童灵·D3" in text) or ("童灵上岗" in text and "上岗模式" in text)
    if not is_d3:
        return None  # 非D3回合：TSL义务不成立，不约束（守互斥律·防假红）
    _ida = _identity_anchors()
    has_id = any(a in text for a in _ida)
    has_tsl = ("🔏" in text) or ("TSL-stamp" in text) or ("├─ L0" in text)
    if not (has_id and has_tsl):
        return False  # 全件缺→未兑现（正是要兜的病）
    # 按序：身份声明须在 TSL 树之前（首段上岗·末段审计）
    _pos = [text.find(a) for a in _ida if a in text]
    idx_id = max(_pos) if _pos else -1
    idx_tsl = min([i for i in (text.find("🔏"), text.find("TSL-stamp"), text.find("├─ L0")) if i >= 0] or [10**9])
    return idx_id <= idx_tsl


def check_w1_honor(text):
    """本端·**本会话**最近一次未消费的 W1 触发 → 回复须含自证词（v1.2 会话级分账）。

    返回 True=兑现 / False=缺位（登记 w1_not_honored）/ None=无触发或不可判定（放行）。
    分账三层（逐层收窄假阳）：
      层1 src==THIS_SRC（v1.1 半修·防跨端）；
      层2 会话级（v1.2 根治·防同端多窗口互吃——原全局单槽水位线：A 会话的 D3 触发
         被 B 会话 Stop 消费 → B 的非 D3 回合被打红；实证 20 红抽样 14 假阳）；
      层3 水位线按会话分文件（同会话防重复检，跨会话互不消耗）。
    保守放行面（宁漏报不冤枉）：Stop 无 session_id / 触发行无 session_id /
    transcript_reader 不可取——均返 None。2026-09-04 前无 src 的历史行不计入（原口径保留）。
    """
    try:
        if not os.path.exists(INJECT_STATE):
            return None
        sid = _norm_sid(_SESSION_ID[0])
        if not sid:
            return None  # 拿不到本端会话标识=不可判（保守放行·不追缴）
        last_w1 = ""
        with open(INJECT_STATE, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("w1") is not True or d.get("src") != THIS_SRC:
                    continue
                t_sid = _norm_sid(d.get("session_id", ""))
                if t_sid and t_sid != sid:
                    continue  # 他会话触发不归本会话消费（v1.2 主修）
                if not t_sid:
                    continue  # 触发无会话标识=不可归账（保守不冤枉）
                if str(d.get("ts", "")) > last_w1:
                    last_w1 = str(d.get("ts", ""))
        if not last_w1:
            return None
        wm = W1_WATERMARK + "_" + re.sub(r"[^A-Za-z0-9._-]", "_", sid)
        seen = ""
        if os.path.exists(wm):
            with open(wm, encoding="utf-8") as f:
                seen = f.read().strip()
        if last_w1 == seen:
            return None  # 该触发已检过（会话级水位线防重复检）
        with open(wm, "w", encoding="utf-8") as f:
            f.write(last_w1)
        _base = W1_PROOF in (text or "")
        if not _base:
            return False
        _ritual = _d3_ritual_full_ordered(text or "")
        return _base if _ritual is None else _ritual
    except Exception:
        return None  # 失败放行（Hook 三纪律）


def scan(text):
    """扫描文本，返回 (red_hits, hard_hits, reflection_signals, alarm, tsl_hits)"""
    red_hits = sorted(set(RED_ZONE_RE.findall(text)))
    hard_hits = sorted(set(HARD_VIOLATION_RE.findall(text)))
    reflection_signals = sorted(set(REFLECTION_SIGNAL_RE.findall(text)))
    alarm = len(hard_hits) > 0
    # TSL 会话执行特征观察（v2026-09-08·回流 AutoClaw 首创·观察模式不裁决）
    tsl_hits = sorted(k for k, r in TSL_MARKER_RE.items() if r.search(text or ""))
    return red_hits, hard_hits, reflection_signals, alarm, tsl_hits


def write_state(text_len, red_hits, hard_hits, reflection_signals, alarm,
               w1_status=None, tsl_hits=None):
    """台账：单行 JSON 追加（tail -n 1 = 最后一条记录）·含载荷自证。"""
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    record = {
        "ts": ts,
        "text_len": text_len,
        "red_zone_hits": ",".join(red_hits),
        "hard_violation_hits": ",".join(hard_hits),
        "reflection_signals": ",".join(reflection_signals),
        "alarm": alarm,
        "stdin_keys": _STDIN_KEYS[0],
        "session_id": _SESSION_ID[0],
    }
    if tsl_hits:
        record["tsl_hits"] = ",".join(tsl_hits)
    if w1_status is not None:
        record["w1_not_honored"] = w1_status
    try:
        with open(STATE_FILE, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def mode_selfcheck():
    """挂载自检：不读 stdin，直接查挂载态"""
    # 1. 是否在 settings.json Stop 链中
    settings_path = os.path.expanduser("~/.qoder-cn/settings.json")
    in_settings = "❌ 否"
    try:
        with open(settings_path) as f:
            content = f.read()
        if "doenglingz_guard" in content:
            in_settings = "✅ 是"
    except Exception:
        in_settings = "⚠️ 无法读取 settings.json"

    # 2. 脚本是否可执行
    script_path = os.path.abspath(__file__)
    exec_ok = "是" if os.access(script_path, os.X_OK) else "否(chmod +x缺失)"

    # 3. 最近一次调用台账
    last_record = "（无调用台账·尚未被 Stop 链实际调用）"
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                lines = f.readlines()
            if lines:
                last_record = lines[-1].strip()
        except Exception:
            pass

    print("## 🔍 童灵守卫挂载自检 (doenglingz_guard.py · Qoder CN)")
    print()
    print("| 检查项 | 结果 |")
    print("|---|---|")
    print(f"| 在 settings.json Stop 链中 | {in_settings} |")
    print(f"| 脚本可执行 | {exec_ok} |")
    print(f"| 最近一次实际调用台账 | {last_record} |")
    print()
    # 4. 空转自检（2026-09-04 补·治"形式在跑功能空转"）
    zero = nonzero = 0
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                for line in f:
                    try:
                        if int(json.loads(line).get("text_len", 0)) > 0:
                            nonzero += 1
                        else:
                            zero += 1
                    except Exception:
                        pass
        except Exception:
            pass
    print(f"| 台账空转比（text_len=0 / >0） | {zero} / {nonzero} |")
    print()
    print("> 四项均正常=童灵守护已在 Qoder CN 运行时刻生效；"
          "空转比全 0 命中或 stdin_keys 不含 last_assistant_message=机制静默失效（须修）。")


def mode_check(text):
    """检查模式：输出 JSON 结果"""
    red_hits, hard_hits, reflection_signals, alarm, tsl_hits = scan(text)
    honor = check_w1_honor(text)
    nh = (honor is False)
    write_state(len(text), red_hits, hard_hits, reflection_signals, alarm,
                w1_status=("not_honored" if nh else ("honored" if honor is True else None)),
                tsl_hits=tsl_hits)
    result = {
        "text_len": len(text),
        "red_zone_hits": ",".join(red_hits),
        "hard_violation_hits": ",".join(hard_hits),
        "reflection_signals": ",".join(reflection_signals),
        "alarm": alarm,
        "w1_not_honored": nh,
        "tsl_hits": ",".join(tsl_hits),
    }
    print(json.dumps(result, ensure_ascii=False))


def mode_report(text):
    """报告模式：输出 markdown 明细"""
    red_hits, hard_hits, reflection_signals, alarm, tsl_hits = scan(text)
    honor = check_w1_honor(text)
    nh = (honor is False)
    write_state(len(text), red_hits, hard_hits, reflection_signals, alarm,
                w1_status=("not_honored" if nh else ("honored" if honor is True else None)),
                tsl_hits=tsl_hits)

    if not alarm and not red_hits and not reflection_signals and not nh:
        print("✅ 童灵守护三查：未检出硬红线触线，红区提示性扫描无命中，无认知深化信号")
        print("🟢 TSL 会话执行特征观察：命中 %d/8（%s）" % (len(tsl_hits), ", ".join(tsl_hits) if tsl_hits else "无"))
        return

    print("## ⚠️ 童灵守护三查扫描结果")
    print()
    if hard_hits:
        print("### 🔴 硬触线（已报警·须复核）")
        print("| 命中模式 | 说明 |")
        print("|---|---|")
        for h in hard_hits:
            print(f"| {h} | 可能涉及不可逆删除·须确认走 trash 而非 rm |")
        print()
    if red_hits:
        print("### 🟡 红区提示（建议你质证·非静默裁决）")
        print("| 可能涉及红区 | 依据(02规范§二) |")
        print("|---|---|")
        for r in red_hits:
            print(f"| {r} | 红区六类之一·须你亲裁·分身不代批 |")
        print()
    if reflection_signals:
        print("### 🔵 认知深化信号（建议使用 system-logger --reflection）")
        print("| 命中关键词 | 建议操作 |")
        print("|---|---|")
        print(f"| {', '.join(reflection_signals)} | 检测到认知深化信号·建议使用 `system-logger --reflection` 添加 `[童灵思考]` 标记 |")
        print()
    if nh:
        print("### 🔴 W1 上岗契约未兑现（w1_not_honored）")
        print("你本回合显式调用童灵，钩子已注入上岗契约，但回复不含『%s』自证——"
              "分身身份被静默吞掉，已登记台账供岗位3周报。" % W1_PROOF)
    if tsl_hits:
        print("### 🟢 TSL 会话执行特征观察（v1.3.0 回流·观察模式不裁决）")
        print("| 命中特征 | 说明 |")
        print("|---|---|")
        for f in tsl_hits:
            print("| %s | 回复文本含该层执行产出物特征 |" % f)
        print()
    print("> 机械部分脚本已填；价值/漂移类软信号不在此静默裁决（02规范§五.3 守护自限），须你/AI 复核。")


def _selftest():
    """v1.2 自测夹具：会话级分账 + transcript 兜底 的正/负样本（任务卡步骤2 扩负例）。
    跑法：python3 doenglingz_guard.py --self-test；全绿=0，有红=1。临时目录隔离，⛔不碰真台账。"""
    import subprocess, tempfile, shutil
    script = os.path.abspath(__file__)
    td = tempfile.mkdtemp(prefix="dlz_w1_selftest_")
    env = dict(os.environ, DOENGLINGZ_CONFIG_DIR=td)
    INJ = os.path.join(td, "doenglingz_inject_state.json")
    ST = os.path.join(td, "doenglingz_guard_state_qodercn.json")
    cases, ok = [], 0

    def reset(rows):
        with open(INJ, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        for fn in os.listdir(td):
            if fn.startswith("doenglingz_w1_watermark_qodercn_"):
                os.remove(os.path.join(td, fn))
        open(ST, "w").close()

    def run(payload):
        r = subprocess.run([sys.executable, script, "--check", "--src", "qodercn"],
                           input=json.dumps(payload, ensure_ascii=False),
                           capture_output=True, text=True, env=env, timeout=30)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return {"_rc": r.returncode, "_err": (r.stderr or "")[-200:]}

    def trig(ts, src, sid, w1=True):
        return {"ts": ts, "w1": w1, "src": src, "session_id": sid}

    T = "【童灵·D3 上岗模式】" + (_identity_anchors()[0] or "童灵上岗——我是你的数字分身") + " 🔏"  # v1.2.1 夹具对齐（2026-10-06·ZCode 端 SSOT 归一轮）：同日 ritual 升级后 D3 全件须含 TSL 标记，原夹具无🔏致 C2/C5 必红；判定零变更·仅测试件

    def ledger_field():
        try:
            d = json.loads(open(ST).read().strip().splitlines()[-1])
            return d.get("w1_not_honored")
        except Exception:
            return "<?>（无台账行）"
    # C1 他会话触发不被本会话 Stop 消费（串账样本注入必被过滤）
    reset([trig("2026-10-06T09:00:00", "qodercn", "sess-OTHER")])
    run({"session_id": "sess-MINE", "last_assistant_message": "普通回复无自证"})
    cases.append(("C1 他会话触发→本会话不可判(台账字段=None)", ledger_field() is None))
    # C2 同会话触发+含自证 → honored
    reset([trig("2026-10-06T09:00:00", "qodercn", "sess-MINE")])
    run({"session_id": "sess-MINE", "last_assistant_message": T + "，本回合任务域判定"})
    cases.append(("C2 同会话+自证→honored", ledger_field() == "honored"))
    # C3 同会话触发+无自证 → not_honored（真红保得住，不滥放）
    reset([trig("2026-10-06T09:00:00", "qodercn", "sess-MINE")])
    run({"session_id": "sess-MINE", "last_assistant_message": "没有自证行的回复"})
    cases.append(("C3 同会话+无自证→not_honored", ledger_field() == "not_honored"))
    # C4 跨端触发不被吃（src 过滤回归）
    reset([trig("2026-10-06T09:00:00", "workbuddy", "sess-MINE")])
    run({"session_id": "sess-MINE", "last_assistant_message": "无自证"})
    cases.append(("C4 他端src触发→过滤(字段=None)", ledger_field() is None))
    # C5 空载荷 + transcript_path 兜底 → honored（.session.execution 后缀归一）
    txp = os.path.join(td, "tx.jsonl")
    with open(txp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "assistant",
                            "message": {"content": [{"type": "text", "text": T + "（兜底取回）"}]}},
                           ensure_ascii=False) + "\n")
    reset([trig("2026-10-06T09:00:00", "qodercn", "sess-MINE.session.execution")])
    run({"session_id": "sess-MINE", "transcript_path": txp})
    cases.append(("C5 空载荷→transcript兜底+后缀归一→honored", ledger_field() == "honored"))
    # C6 同会话二次 Stop（水位线已消费）→ 不重复判
    reset([trig("2026-10-06T09:00:00", "qodercn", "sess-MINE")])
    run({"session_id": "sess-MINE", "last_assistant_message": T})
    run({"session_id": "sess-MINE", "last_assistant_message": "同会话第二条"})
    cases.append(("C6 已消费触发→二次Stop不重复判", ledger_field() is None))
    # E2E 无参数运行不崩（Hook 三纪律：失败放行）
    r = subprocess.run([sys.executable, script], input="{}",
                       capture_output=True, text=True, env=env, timeout=30)
    cases.append(("E2E 裸跑（真挂载形态·空payload）rc=0 无traceback", r.returncode == 0 and "Traceback" not in (r.stderr or "")))

    for name, passed in cases:
        ok += 1 if passed else 0
        print("  %s %s" % ("✅" if passed else "❌", name))
    print("自测 %d/%d %s" % (ok, len(cases), "全绿" if ok == len(cases) else "有红"))
    shutil.rmtree(td, ignore_errors=True)
    return 0 if ok == len(cases) else 1


def main():
    args = sys.argv[1:]

    if "--self-test" in args:
        sys.exit(_selftest())

    if "--selfcheck" in args:
        mode_selfcheck()
        return

    # --sid 显式会话标识（v1.2·为 --text 型调用方补会话，如 Hermes 插件无 stdin 载荷）
    if "--sid" in args and args.index("--sid") + 1 < len(args):
        _SESSION_ID[0] = args[args.index("--sid") + 1]

    # 取文本：优先 --text argv，其次 stdin，再次 transcript 兜底（v1.2 缺口②）
    text = ""
    if "--text" in args:
        idx = args.index("--text")
        if idx + 1 < len(args):
            text = args[idx + 1]
    else:
        text = get_text_from_stdin()
        if not (text or "").strip():
            text = _fallback_transcript_text()

    if "--report" in args:
        mode_report(text)
    elif "--check" in args or not args:
        mode_check(text)
    else:
        print("用法: doenglingz_guard.py [--check|--report|--selfcheck|--text <text> [--sid <会话id>] [--src <端名>]]", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
