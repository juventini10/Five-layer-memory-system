#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/doenglingz_level_declare_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
# version: v1.12（2026-10-27 GitHub issues #6/#8 外部反馈根治·tiger5325·2026-10-26 报）：
#   ①#8 版本单源——自测横幅手写 v1.9 与文件头版本注释（v1.11）两本账，用户无法机械对账。
#     修=__version__ 常量为唯一真源，横幅/输出一律引用，⛔手写数字（版本号只住一处）。
#   ②#6 判据空转根治——包内旧版 LEVEL_SRC 硬编作者机绝对路径，端用户机上不存在
#     ⇒ _output_level() 恒 None ⇒ 两处 TSL 对账判据（降级对账+D3静默分支）静默全灭
#     （用户以为守卫在保护，实际什么都没判=假绿同族·报障者实测 F01 全树/包内均无该件）。
#     修=env DOENGLINGZ_LEVEL_SRC 可覆盖（装机端指向自己那份清单）+ 源缺失显形：
#     台账记 level_src_missing + 本回合真需要判（童灵在场且提TSL/声明D3）时显式报警，
#     ⛔静默空转不复发。
# version: v1.10 → v1.11（2026-10-16 Qoder CN·假红结构定案根治：_expected_tier 按"最大ts组内max"
#   实现注释本意，堵"同会话历史 D3 被无下界窗口永久继承"；负例三例自测见系统日志 10-16）
# version: v1.8 → v1.9（2026-10-09 Qoder CN·皮叔令「按符合愿景的最优解去根治处理」·位置性假红根治：
#   声明类判据（档位/档位对账/域判定）加 transcript 本回合回退读面·仅在读面判不出时启用·树位置等判据零变更；
#   ⛔不取 tool_use 字（防假红换假绿）·切片以末条有正文 user 行为界（防上回合声明顶替本回合）；
#   台账新增 round_used 可见性；自测 +T17/T18/T19 +MUT3（置哑 _round_text→T17 必红·可证伪））
# version: v1.7 → v1.8（2026-10-07 Qoder CN·你令按三明治推荐开工·P3②错位对账落地：
#   D3 回合 AI 宣告域⊄W3机器词面域 且 无补载痕(显形行/transcript读slices动作) → alarm+台账；
#   痕在=已恢复仅台账不报警；W3无当会话行=不判⛔不假红。判据源可证伪：MUT2 置哑 _machine_layers → T13 必哑。
#   病根实证=同日 ZCode 回合「切片判定:全域」vs AI「任务域判定:L3」不同源（真源=06 v1.135 + injector v1.18 契约①补载义务））
# version: v1.6 → v1.7（2026-10-05 FU-116 判假线修复：_norm_sid sid 归一——三代格式并存致对账腿假阴性·隔离压测 T4 复现）
# version: v1.4 → v1.5（2026-09-30 加树位置判据 + 非D3树越界判据）
"""
doenglingz_level_declare_guard.py —— Stop 钩子·童灵档位声明对账（D 轴反向校验层）

病根·v1.6（2026-09-30 你质证「我有没启动童灵 D3，为什么还有 TSL？」）：
  v1.5 只修了"树放哪里"（首段→末段），**没重申"该不该有树"** → 反制造歧义（读起来像每轮都该有树）；
  AI 在 D1 回合**自行跑 tsl_verify 并 relay 树**（钩子门控正确未注入·AI 越界产树）=你看到的怪象。
  口径（08 §七·钩子 `tsl_echo_hook.py` L32 同源）：**TSL 树仅 D3 上岗回合出现**。
  v1.6 补判据：**非 D3 回合（exp_tier ∈ {D1,D2}）出现树块 → 台账 + alarm**。
  判据沉淀：**先问「该不该有」（触发条件），再问「放哪里」（位置）**——只修后者会制造新歧义。

病根·v1.5（2026-09-30 你质证「TSL 有时在顶部有时在底部…一开始就显示，很多工作都没做，有什么审计效果？」
  且明言「以后不想再讨论这个 TSL 的问题·耗费无数时间」→ 要求机制级根治）：
  08 §七 旧文要求「首段输出本清单」＝把**后验对账产物（Stop 钩子回合末扫账本的树）**
  塞进**前瞻位置（首段）** → 时序错位：首段只能呈现上一回合的树 → 零审计效力 + 位置漂移观感。
  规范已修（08 §七 执行时机 + 06 §1.6 呈现时机注记）：**前瞻（声明/计划）归首段，后验（树）归末段**。
  v1.5 补**反向校验**（执规-008 判据：不读文档也会被拦才算机制化）：树块出现在回复前半段
  → 台账留痕 + alarm。位置判据机械可验 → 不再靠人记得、不再需要你重复质证。

病根·v1.0（2026-09-19 你三度质证「为什么格式又不对」）：
  06-跨端适配规范 §1.6（单一真源）+ 08-会话级L7验证清单 §七 已定「D 档位声明义务」，
  但**只有正面规则**——缺反向校验（执规-008 判据：不读文档也会被拦才算机制化）。

病根·v1.1（2026-09-20 你再问「昨天不是修了吗？怎么还是这样」）：
  v1.0 **100% 空转**——文本键表只有 text/prompt/content/response/…，而 WorkBuddy Stop 的
  真实 stdin 文本键是 **last_assistant_message**（实证来源：doenglingz_guard_state.json 的
  stdin_keys 字段）→ _get_text 恒返空 → 在写台账**之前**就 return → 连"我处理过"都不留痕
  → 守卫隐身，发病时无法与"守卫正常无事"区分（比报警失效更糟）。
  且 v1.0 的"4 例实测通过"是用人工构造的 {"text": …} 喂的**假绿**——没走真实 Stop 键名。
  v1.1 修：①KEYS 置 last_assistant_message 于首位 ②空文本也写台账（no_text + stdin_keys）
  ——把"读不到"从隐身变成显形。

本守卫做什么（只做机器能做的）：
  读本回合最终回复文本（Stop stdin JSON）→ 若回复属「童灵在场」（含"童灵"字样）
  但**首段无档位声明**（`童灵·D1/D2/D3` 任一）→ 台账留痕 + alarm。
  声明义务真源：06 §1.6 + 08 §七（v1.3.2）。

契约（守卫规范）：--check(JSON·含 alarm) / --report(明细) ；exit 0 恒定不阻断；失败放行。
台账：~/.workbuddy/doenglingz_level_declare_state.json（append-only·单行 JSON）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import sys
import os
import json
import re
from datetime import datetime

# v1.12（issue#8 版本单源·真源声明）：本守卫当前版本的唯一真源——横幅/输出一律引用本常量，
# ⛔手写数字（版本号只住一处；文件头 version 注释行=沿革账，当前值以本常量为准）。
__version__ = "1.12"

# v1.9：transcript_reader 装载（同 doenglingz_guard._fallback_transcript_text 惯例·端中立件）
_TR_LIB = None
def _load_tr():
    global _TR_LIB
    if _TR_LIB is not None:
        return _TR_LIB
    for _p in (os.path.dirname(os.path.realpath(__file__)),
               os.path.dirname(os.path.abspath(__file__)),
               os.path.expanduser("[记忆共享中心]/脚本中心"),
               os.path.expanduser("[记忆共享中心]/脚本中心")):
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
    try:
        import transcript_reader as _tr
        _TR_LIB = _tr
    except Exception:
        _TR_LIB = False
    return _TR_LIB

STATE = os.path.join(os.environ.get("DOENGLINGZ_CONFIG_DIR") or os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
                     "doenglingz_level_declare_state.json")
DECL = re.compile(r"童灵·D[123]")
HEAD = 300          # 声明须落在回复首段（前 300 字符内）
MENTION = "童灵"
# TSL 档位对账（v1.2·2026-09-20）——08 §七 默认档位=展开版(树状·跨端固定视觉)；
# 切档**唯一入口**=08 的 `OUTPUT_LEVEL` 字段（单行摘要版仅供 token 敏感场景）。
# 反模式：AI 在对话里"为了清爽"自行降级为单行摘要版，绕过唯一入口
# （皮叔 2026-09-20 质证「你这个签名怎么是这样显示了？前面的对话不是好好的么」）。
# v1.12（issue#6 判据空转根治）：包内旧版把本路径硬编为作者机绝对形状（构建链替换产物），
#   端用户机上不存在 → _output_level() 恒 None → 两处 TSL 对账判据静默全灭。
#   修=①env DOENGLINGZ_LEVEL_SRC 可覆盖（装机端指向自己那份 08 清单副本）；
#     ②源缺失显形：台账 level_src_missing + 本回合真需要判时显式报警（见 check 末段），⛔静默空转。
LEVEL_SRC = os.environ.get("DOENGLINGZ_LEVEL_SRC") or os.path.expanduser("[记忆共享中心]/脚本中心/08-会话级L7验证清单.md")
TSL_MENTION = re.compile(r"TSL")
# ── 档位对账（v1.3·2026-09-26 你质证「到底是 D1 还是 D2？真解决还是假的解决」）──
# v1.0-v1.2 只判"有没有声明"，不判"声明得对不对"：回复写『童灵·D2』而注入器算出 D1 时
# 本守卫全程绿灯——这正是你连问三轮的病灶（判据只覆盖了一半）。
# 期望值真源=注入器台账 `d_tier` 字段（injector v1.8 起由脚本算出的唯一档位）。
INJECT_STATE_NAME = "doenglingz_inject_state.json"
TIER_DECL = re.compile(r"童灵·D([123])")
# ── 域判定错位对账（v1.8·2026-10-07·triwich L2 seal c81b799072b0c360）──
# 三源：机器词面=W3台账layers / AI宣告=首段「任务域判定：LN」/ 补载痕=显形「已补载：LN」或transcript读slices/LN。
DECL_LAYER = re.compile(r"任务域判定[：:]\s*(L[2-5])")
RELOADED = re.compile(r"已补载[：:]\s*(L[2-5])")
W3_LEDGER = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime/w3_inject_ledger.jsonl")

TSL_TREE = re.compile(r"[├└]─")
# ── 树位置判据（v1.5·2026-09-30）──
# 树＝后验对账产物（Stop 钩子回合末扫账本）→ 必须居末段；
# 出现在回复前半段＝把上一回合的账摆到前瞻位置（零审计效力 + 位置漂移）。
TREE_BLOCK = re.compile(r"🧾\s*TSL\s*机械核验")
TREE_POS_MIN = 0.5          # 树块起始偏移须 ≥ 全长的 50% 才算"居末段"
TREE_POS_MIN_LEN = 200      # 短回复不判（防噪声）


def _output_level():
    """读 08 §七 的 OUTPUT_LEVEL 当前值（切档唯一入口）。读不到→None（不判·失败放行）。"""
    try:
        with open(LEVEL_SRC, encoding="utf-8") as f:
            m = re.search(r"`OUTPUT_LEVEL`.*?\*\*`([^`]+)`\*\*", f.read())
        return m.group(1).strip() if m else None
    except Exception:
        return None


# 文本键表（v1.2）：与同域已成熟运行的 `changelog-guard/doenglingz_guard.sh` 的 TEXT_KEYS
# **逐键对齐**——v1.0 自拟 6 键、漏 last_assistant_message 致全程空转；v1.1 只补 1 键仍不全。
# 教训：**同域已有能跑的件，新建件必须先对齐它的接口再写**（⛔勿照自己假设另造一套键表）。
KEYS = ("last_assistant_message", "responseText", "text", "prompt", "content",
        "response", "message", "last_message", "responsePreview",
        "output", "assistant_message")


def _get_text(obj):
    if not isinstance(obj, dict):
        return ""
    for k in KEYS:
        v = obj.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _round_text(obj):
    """v1.9（2026-10-09 Qoder CN·皮叔令「按符合愿景的最优解根治」）：本回合全部 assistant 正文（时间序）。

    病根＝**位置性假红**：Stop payload 的 last_assistant_message 只含**最后一段**回复。档位块若落在
    工具调用之前的分段（「先交代→再取证→再交付」这一正常工作形态），payload 文本看不见它 →
    declared=false＋alarm=true。本端台账 2026-10-09 18:56 实证（head 以【意图分类】开头而实际首行有档位块）。
    判据未随对象演化：本守卫该判的对象是「**这一回合**有没有交代」，不是「最后一条消息有没有」。

    三条读面纪律（⛔不得放宽）：
    ① 只取 role==assistant 的正文——flatten_content 对 tool_use/thinking 取不到 text 天然剥离，
       从工具参数里捞「童灵·D3」＝把假红换成假绿，比原病更糟；
    ② 切片以「最后一条有正文的 user 行」为界——⛔不取整份 transcript，否则上一回合的声明会顶替本回合的漏交代（假绿）；
    ③ transcript 不可得/reader 缺件 → 返空串＝维持 v1.8 原判定（宁可不判不猜·保守不冤枉）。
    """
    tp = obj.get("transcript_path") if isinstance(obj, dict) else None
    tr = _load_tr()
    if not tp or not os.path.isfile(tp) or not tr:
        return ""
    try:
        msgs = tr.iter_messages(tp)
    except Exception:
        return ""
    cut = 0
    for i, (role, text) in enumerate(msgs):
        if role == "user" and text.strip():
            cut = i + 1
    return "\n".join(t for role, t in msgs[cut:] if role == "assistant" and t.strip())


def _norm_sid(s):
    """sid 归一（FU-116·2026-10-05 判假线实证）：ZCode payload sid 三代格式并存
    （sess_* / task-*.session.execution / 裸 UUID）且 UPS 与 Stop 同会话不同形
    → 精确匹配恒失配（expected_tier=None 假阴性漏告警·隔离压测 T4 复现）。
    剥宿主前缀与尾巴留核心 id 段比对；归一后为空仍不判（宁可不判不猜·原语义）。"""
    s = str(s or "").strip()
    for pre in ("sess_", "task-"):
        if s.startswith(pre):
            s = s[len(pre):]
    return s.split(".", 1)[0].strip().lower()


def _tsnorm(v):
    """时间串归一为 "YYYY-MM-DD HH:MM:SS" 可字典序比较；解不了给空串＝不参与窗口。"""
    s = str(v or "").strip()
    if not s:
        return ""
    s = s.replace("T", " ").replace("Z", "").split(".")[0].split("+")[0]
    return s[:19] if len(s) >= 19 else ""


def _round_ts(obj):
    """被审回合最后一条 assistant 正文的时刻（=本回合回复时刻），作对账窗口上界。
    取不到→空串＝调用方退回旧行为（保守不放松·⛔不因此新造假红）。"""
    tp = obj.get("transcript_path") if isinstance(obj, dict) else None
    tr = _load_tr()
    if not tp or not tr or not hasattr(tr, "iter_messages_with_ts"):
        return ""
    try:
        rows = tr.iter_messages_with_ts(tp)
    except Exception:
        return ""
    cut = 0
    for i, (role, text, _ts) in enumerate(rows):
        if role == "user" and text.strip():
            cut = i + 1
    for role, text, ts in reversed(rows[cut:]):
        if role == "assistant" and text.strip():
            return _tsnorm(ts)
    return ""


def _expected_tier(session_id, inject_path=None, as_of=""):
    """取本回合注入算出的档位。

    v1.10（2026-10-10·PAT-087·Qoder CN）：as_of 给定时按**窗口**取（ts<=as_of 的最后一组行里
    的最大档），⛔再用"全会话最后一行"代表本回合——原因是事件腿让一个回合可有多行，
    且下一回合的 UPS 行会在 Stop 评估前落盘，旧取法把"下一回合的 D1"当"本回合的期望档"，
    使真红（惯性高报）与假红（合法升档）同形。as_of 空＝退回 v1.9 行为（保守·不新增假红）。
    无 d_tier 字段（v1.8 前的老台账行）→ None＝不判·⛔不假红。"""
    # PAT-081 根治（2026-10-06·皮叔令「每端做自己端的·不要互通造成假象」）：
    #   旧只认 WORKBUDDY_CONFIG_DIR→默认 ~/.workbuddy，与 injector 写 inject_state 的
    #   三段解析(DOENGLINGZ>WORKBUDDY>默认)不同根 ⇒ 非 WB 端 inject 写本端根、declare_guard
    #   却读 WB 根的陈旧他端行 ⇒ 每轮拿错账比出「档位不符」假象（读写不同根=串流假象）。
    #   对齐三段：各端 declare_guard 读本端 inject_state·每端做自己端的。
    path = inject_path or os.path.join(
        os.environ.get("DOENGLINGZ_CONFIG_DIR")
        or os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
        INJECT_STATE_NAME)
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return None
    want = _norm_sid(session_id)
    if not want:
        return None          # 无会话号＝对不上归属，宁可不判也不猜（防跨会话错配）
    cand = [r for r in rows if r.get("d_tier") and _norm_sid(r.get("session_id")) == want]
    if not cand:
        return None
    _as = _tsnorm(as_of)
    if _as:
        win = [r for r in cand if (_tsnorm(r.get("ts")) or "9999") <= _as]
        if win:
            _ord = {"D1": 1, "D2": 2, "D3": 3}
            # v1.11 归真（2026-10-16·Qoder CN·会话task-acf6c假红实锤）：docstring 说
            # "最后一组行里的最大档"，实现却拿整个无下界窗口的 max ⇒ 同会话历史上出现过
            # D3 后，其后每一轮都被永久继承成期望 D3（昨日 13 行 D3 咬中今日 D2 轮）。
            # 组=最大 ts 的那一组行：max 只横向往（事件腿同轮多行取最高档），⛔纵向跨时间继承。
            _mx = max(_tsnorm(r.get("ts")) or "9999" for r in win)
            grp = [r for r in win if (_tsnorm(r.get("ts")) or "9999") == _mx]
            return max((r.get("d_tier") for r in grp), key=lambda t: _ord.get(t, 0))
    return cand[-1].get("d_tier")


def _machine_layers(session_id, ledger_path=None):
    """本会话最近一次 W3 台账行 → 机器词面域集合（如 {"L3"}）。无行→None=不判·⛔不假红。"""
    path = ledger_path or W3_LEDGER
    try:
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:
        return None
    want = _norm_sid(session_id)
    if not want:
        return None
    cand = [r for r in rows if _norm_sid(r.get("session_id")) == want]
    if not cand:
        return None
    return {str(x).split("_")[0] for x in (cand[-1].get("layers") or [])}


def _reloaded(obj, txt, codes):
    """补载痕 = 显形行（全文任意位）∪ transcript 中 slices/LN 读取动作。返回有证据的码集合。"""
    got = set(RELOADED.findall(txt))
    tp = obj.get("transcript_path") if isinstance(obj, dict) else None
    if tp and os.path.exists(tp):
        try:
            with open(tp, encoding="utf-8", errors="ignore") as f:
                blob = f.read()
            for c in codes:
                if ("slices/" + c) in blob:
                    got.add(c)
        except Exception:
            pass
    return got


def _ledger(rec):
    try:
        with open(STATE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def check():
    try:
        obj = json.load(sys.stdin)
    except Exception as e:
        # v1.1：解析失败也留痕——同"空文本"病灶（该分支原也在写台账之前 return）。
        # 失败放行语义不变（守卫规范）。
        _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "parse_error": str(e)[:120]})
        return 0
    txt = _get_text(obj)
    if not txt.strip():
        # v1.1：空文本也留痕——防"读不到 → 静默隐身"（v1.0 此分支 return 早于写台账，
        # 空转零痕迹，发病时无法与"守卫正常无事"区分）。失败放行语义不变（守卫规范）。
        _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 "no_text": True,
                 "stdin_keys": ",".join(sorted(obj.keys())) if isinstance(obj, dict) else ""})
        return 0
    declared = bool(DECL.search(txt[:HEAD]))
    # v1.9 分段回退腿（位置性假红根治）：**仅在 payload 读面判不出声明时**才启用 transcript 读面，
    #   已绿回合路径零变更＝不牵连出新红；树位置/TSL/非D3越界三判据继续读 payload txt（⛔不扩大改动面）。
    dcl_src, round_used = txt, False
    if not declared:
        _rnd = _round_text(obj)
        if _rnd.strip() and DECL.search(_rnd[:HEAD]):
            dcl_src, declared, round_used = _rnd, True, True
    # v1.3 档位"对不对"（声明集合 vs 注入器算出的唯一档位）
    _sid = str((obj if isinstance(obj, dict) else {}).get("session_id", "") or "")
    got_tiers = sorted({"D" + m for m in TIER_DECL.findall(dcl_src[:HEAD])})
    exp_tier = _expected_tier(_sid, as_of=_round_ts(obj))
    # 只在「童灵在场」的回合判定（防非童灵回合噪声）
    tongling_turn = MENTION in txt
    alarm = bool(tongling_turn and not declared)

    tier_alarm = ""
    if exp_tier and got_tiers:
        if len(got_tiers) > 1:
            tier_alarm = "同回合声明了 %d 个档位 %s（§1.6 互斥律·应唯一＝%s）" % (
                len(got_tiers), "/".join(got_tiers), exp_tier)
        elif got_tiers[0] != exp_tier:
            tier_alarm = "声明＝%s 与注入器档位＝%s 不符（档位定义权在脚本·真源=inject 台账 d_tier）" % (
                got_tiers[0], exp_tier)

    # ── TSL 档位对账（v1.2）：默认档位必须与 08 的 OUTPUT_LEVEL 一致 ──
    level = _output_level()
    # v1.12（issue#6）：源缺失=判据空转，必须显形（⛔静默全灭=假绿同族·报障者实测案）
    level_src_missing = bool(level is None and not os.path.isfile(LEVEL_SRC))
    fmt_tree = bool(TSL_TREE.search(txt))
    tsl_mentioned = bool(TSL_MENTION.search(txt))
    fmt = "tree" if fmt_tree else ("flat" if tsl_mentioned else "")
    # v1.4 档位门控（2026-09-26 实测假警报）：08 §1.6/TSL 设计口径是「**TSL 仅 D3 上岗档需要**，
    #   D1/D2 非上岗」，但本判据原先不看档位——D1 回合只要正文里出现"TSL"字样（含提到守卫文件名
    #   `tsl_closeout_guard.py`）且没贴整棵树，就被喊"降级为单行摘要版"。修：
    #   已知本回合非 D3（exp_tier∈{D1,D2}）→ 不判降级；exp_tier=None（老台账/无会话号）→ 维持原判不放松。
    tier_says_no_tsl = exp_tier in ("D1", "D2")
    tsl_alarm = bool(tongling_turn and level == "展开版" and tsl_mentioned
                     and not fmt_tree and not tier_says_no_tsl)
    # 静默假启动分支(2026-10-06 你质证「D3假启动无TSL联动」)：原判据以 tsl_mentioned 为前置，
    # D3标签在场+零提TSL+无树=静默型漏网(T7测"提到无树"、T4/T5测"不提到不报"，中间形态无人管)。
    # 严格门控：只认显式 D3 上岗标签（⛔不用 tongling_turn 的宽语义，防 T4/T5 类无D3声明回合误伤）。
    if (("童灵·D3" in txt or "D3 上岗模式" in txt) and level == "展开版"
            and not fmt_tree and not tier_says_no_tsl):
        tsl_alarm = True

    # ── 树位置对账（v1.5·2026-09-30）：后验产物（树）须居末段 ──
    # 判据机械可验：树块起始偏移 / 全文长度 < 50% → 位置违规（＝把上一回合的账摆到前瞻位）。
    tree_pos, tree_pos_alarm = None, ""
    _mt = TREE_BLOCK.search(txt)
    if _mt and tongling_turn and len(txt) >= TREE_POS_MIN_LEN:
        tree_pos = round(_mt.start() / len(txt), 3)
        if tree_pos < TREE_POS_MIN:
            tree_pos_alarm = "TSL 树出现在回复前 %.0f%%（位置违规·后验产物须居末段）" % (tree_pos * 100)

    # ── 非 D3 回合出现树（v1.6·2026-09-30 你质证「我没启动 D3 为什么还有 TSL」）──
    # 树义务仅 D3（08 §七·钩子 tsl_echo_hook L32 门控同源）→ D1/D2 出现树块 = AI 越界自行产树。
    # 判据顺序纪律：**先问「该不该有」（本判据）·再问「放哪里」（上判据）**。
    nond3_tree_alarm = ""
    if exp_tier in ("D1", "D2") and _mt:
        nond3_tree_alarm = ("非 D3 回合（%s）出现 TSL 树——树义务仅 D3；"
                            "AI 不得自行产树/relay（该不该有 未过）" % exp_tier)

    # ── 域判定错位对账（v1.8）：仅 D3 回合判；宣告⊄机器 且无痕=报警，有痕=已恢复不报警 ──
    machine = _machine_layers(_sid) if exp_tier == "D3" else None
    declared_l = set(DECL_LAYER.findall(dcl_src[:HEAD]))
    drift_recovered, drift_alarm = set(), ""
    if exp_tier == "D3" and machine is not None and declared_l:
        drift_missing = declared_l - machine
        if drift_missing:
            drift_recovered = _reloaded(obj, txt, drift_missing) & drift_missing
            drift_missing -= drift_recovered
            if drift_missing:
                drift_alarm = ("宣告域 %s 不在机器词面判定 %s 中且无补载痕——契约①补载义务：宣告域须真Read该域切片+显形「已补载：LN」" % (
                    "/".join(sorted(drift_missing)), "/".join(sorted(machine)) or "未命中"))

    _ledger({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             "tongling_turn": tongling_turn, "declared": declared, "alarm": alarm,
             "tsl_level": level, "tsl_format": fmt, "tsl_alarm": tsl_alarm,
             "level_src_missing": level_src_missing,
             "tree_pos": tree_pos, "tree_pos_alarm": bool(tree_pos_alarm),
             "nond3_tree_alarm": bool(nond3_tree_alarm),
             "session_id": _sid, "declared_tiers": got_tiers, "expected_tier": exp_tier,
             "tier_alarm": tier_alarm,
             "declared_layers": sorted(declared_l),
             "machine_layers": (sorted(machine) if machine is not None else None),
             "drift_recovered": sorted(drift_recovered), "drift_alarm": bool(drift_alarm),
             "head": txt[:80], "round_used": round_used,
             # v1.9.1 自证字段：本端载荷是否携带 transcript_path（不带=回退腿死代码·⛔不靠猜）
             "tp_present": bool(isinstance(obj, dict) and
                               str(obj.get("transcript_path") or "").strip())})

    if alarm:
        print(json.dumps({"alarm": True,
                          "reason": "童灵在场回合缺档位声明（首段未出现 童灵·D1/D2/D3）"
                                    "·真源=06-跨端适配规范 §1.6 + 08-会话级L7验证清单 §七"},
                         ensure_ascii=False))
    if tier_alarm:
        print(json.dumps({"alarm": True,
                          "reason": "D 轴档位声明对账失败：" + tier_alarm
                                    + "·真源=06-跨端适配规范 §1.6"}, ensure_ascii=False))
    if tsl_alarm:
        print(json.dumps({"alarm": True,
                          "reason": "TSL 被降级为单行摘要版，但 08 §七 OUTPUT_LEVEL=展开版（默认档位）"
                                    "——切档唯一入口是 08 的 OUTPUT_LEVEL 字段，⛔不得在对话内自行降级"},
                         ensure_ascii=False))
    if tree_pos_alarm:
        print(json.dumps({"alarm": True,
                          "reason": "TSL 树位置违规：" + tree_pos_alarm
                                    + "·真源=08 §七 执行时机 + 06 §1.6 呈现时机注记"
                                      "（前瞻归首段·后验归末段）"},
                         ensure_ascii=False))
    if nond3_tree_alarm:
        print(json.dumps({"alarm": True,
                          "reason": "TSL 树越界：" + nond3_tree_alarm
                                    + "·真源=08 §七（每次启动童灵后必须输出＝仅 D3）+ "
                                      "tsl_echo_hook.py L32 档位门控（非 D3 不注入）"},
                         ensure_ascii=False))
    if drift_alarm:
        print(json.dumps({"alarm": True,
                          "reason": "域判定错位未恢复：" + drift_alarm
                                    + "·真源=06 §1.6 v1.135 + injector v1.18 契约①"}, ensure_ascii=False))
    # v1.12（issue#6）：判据源缺失显形——只在「本回合真需要判」时报警（童灵在场且提 TSL/声明 D3），
    # ⛔不每轮刷屏，也⛔再静默（源缺失时 TSL 两判据整体不可判，用户有权知道）
    if level_src_missing and tongling_turn and (tsl_mentioned or "童灵·D3" in txt or "D3 上岗模式" in txt):
        print(json.dumps({"alarm": True,
                          "reason": "OUTPUT_LEVEL 判据源缺失（%s 不存在）⇒ TSL 档位对账本轮不可判"
                                    "（判据空转=假绿同族·issue#6）。修法：设 env DOENGLINGZ_LEVEL_SRC "
                                    "指向 08-会话级L7验证清单.md 副本" % LEVEL_SRC}, ensure_ascii=False))
    return 0


def report():
    """--report：打印台账明细（供岗位3周报/对账）。"""
    if not os.path.exists(STATE):
        print("（台账为空）")
        return 0
    rows = []
    for ln in open(STATE, encoding="utf-8"):
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    tot = len(rows)
    al = sum(1 for r in rows if r.get("alarm"))
    print(f"档位声明对账：回合 {tot} · 缺声明 {al} · 合规率 {(tot-al)/tot*100:.1f}%" if tot else "（无数据）")
    for r in rows[-10:]:
        flag = "⛔" if r.get("alarm") else "✅"
        print(f"  {flag} {r['ts']} 童灵回合={r.get('tongling_turn')} 声明={r.get('declared')} | {r.get('head','')[:50]}")
    return 0


def _self_test():
    """v1.3 档位对账自测（夹具走临时目录隔离·⛔不污染真台账）。

    判据必须可证伪（守卫编写规范 §3.9）：MUT 段把 _expected_tier 短路成 None，
    T2/T3 必须一起变哑——若仍报警＝判据另有来源；若全绿＝恒真探针，作废。
    """
    import contextlib
    import io as _io
    import tempfile

    global STATE, W3_LEDGER
    tmp = tempfile.mkdtemp(prefix="ldg_v13_")
    STATE = os.path.join(tmp, "declare_state.json")          # 本守卫台账隔离
    # v1.12（issue#6）：LEVEL_SRC 夹具化——真源路径在端用户机（乃至本机作者态占位形状）必缺，
    # 不夹具化则既有 T6/T7/T11-T15 的期望（level=展开版）与 T22 的「缺失显形」互相打架。
    # 夹具内容=OUTPUT_LEVEL 展开版（与既有用例口径一致）；测试结束还原真源路径。
    globals()["_LEVEL_SRC_REAL"] = LEVEL_SRC
    _lvl_fixture = os.path.join(tmp, "08_fixture.md")
    with open(_lvl_fixture, "w", encoding="utf-8") as _f:
        _f.write("### 七 档位与呈现\n`OUTPUT_LEVEL` 当前值：**`展开版`**\n")
    globals()["LEVEL_SRC"] = _lvl_fixture
    inj = os.path.join(tmp, "inject_state.json")             # 注入器台账夹具
    with open(inj, "w", encoding="utf-8") as f:
        for r in [{"ts": "1", "session_id": "S1", "d_tier": "D1"},
                  {"ts": "2", "session_id": "S2", "d_tier": "D2"},
                  {"ts": "3", "session_id": "S3"},            # 老台账行：无 d_tier
            {"ts": "4", "session_id": "S4", "d_tier": "D3"},
            {"ts": "5", "session_id": "S6", "d_tier": "D3"}]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    W3_LEDGER = os.path.join(tmp, "w3_fixture.jsonl")       # v1.8 错位对账夹具
    with open(W3_LEDGER, "w", encoding="utf-8") as f:
        for r in [{"ts": "1", "session_id": "S4", "layers": []},          # 机器未命中（原「全域」态）
                  {"ts": "2", "session_id": "S6", "layers": ["L3_行为规则"]}]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    orig = _expected_tier

    # v1.9 夹具：本回合 transcript（分段形态＝档位块在前一段、最终消息只剩正文）
    def mk_transcript(name, segs):
        """segs=[(role, text 或 content列表)] → 写 jsonl，返回路径。"""
        path = os.path.join(tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            for role, cont in segs:
                f.write(json.dumps({"message": {"role": role, "content": cont}},
                                   ensure_ascii=False) + "\n")
        return path

    def run(msg, sid, stub=None, tp=None):
        _pl = {"last_assistant_message": msg, "session_id": sid}
        if tp:
            _pl["transcript_path"] = tp
        payload = json.dumps(_pl, ensure_ascii=False)
        globals()["_expected_tier"] = stub or (lambda s2, inject_path=None, as_of="": orig(s2, inject_path=inj, as_of=as_of))
        buf = _io.StringIO()
        old = sys.stdin
        sys.stdin = _io.StringIO(payload)
        try:
            with contextlib.redirect_stdout(buf):
                check()
        finally:
            sys.stdin = old
            globals()["_expected_tier"] = orig
        out = buf.getvalue()
        # v1.4：探测"本回合有无任何 alarm 输出"（档位类或 TSL 类皆算），⛔不按关键词挑——
        #   原写法只认"档位/D 轴"字样，TSL 降级报警会被自己的自测漏计（=仪器看不见其中一类报警）。
        return '"alarm": true' in out

    CASES = [
        ("T1 台账D1·回复D1 → 静默", "【童灵·D1 常驻模式（非全量，仅人格基底）】正文", "S1", False),
        ("T2 台账D1·回复D2 → 必报", "【童灵·D2 域模式（命中域切片：L2 · 非上岗）】正文", "S1", True),
        ("T3 同回合两档 → 必报", "童灵·D1 常驻模式 / 童灵·D2 域模式 正文", "S2", True),
        ("T4 老台账无 d_tier → 不误报", "【童灵·D2 域模式】正文", "S3", False),
        ("T5 无会话号 → 不判", "【童灵·D2 域模式】正文", "", False),
        # TSL 降级判据的档位门控（v1.4）：夹具里把 08 OUTPUT_LEVEL 视为展开版（真实值），
        # D1 回合正文提到 TSL 而无树 → 不该报；D3 回合同样输入 → 该报。
        ("T6 D1回合提到TSL无树 → 不误报", "【童灵·D1 常驻模式】本轮跑了 tsl_closeout_guard 自测，未涉及 TSL 呈现", "S1", False),
        ("T7 D3回合提到TSL无树 → 该报", "【童灵·D3 上岗模式】本轮 TSL 核验我只给了一行摘要", "S4", True),
        ("T11 D3静默无树(零提TSL) → 必报·静默分支", "【童灵·D3 上岗模式】童灵上岗——身份声明。" + "正文" * 130, "S4", True),
        ("T12 D1标签静默无树 → 不误报(严格门控)", "【童灵·D1 常驻模式（非全量，仅人格基底）】童灵人格基座在岗。" + "正文" * 130, "S1", False),
        # v1.5 树位置判据（前瞻/后验分离）：后验的树必须居末段。
        ("T8 树在首段 → 必报", "【童灵·D1 常驻模式（非全量，仅人格基底）】\n🧾 TSL 机械核验 v0.11.2\n├─ L0 ✅做到\n" + "正文" * 130, "S1", True),
        ("T9 D3树居末段 → 不报", "【童灵·D3 上岗模式】\n" + "正文" * 130 + "\n🧾 TSL 机械核验 v0.11.2\n├─ L0 ✅做到", "S4", False),
        ("T10 非D3回合带树 → 必报", "【童灵·D1 常驻模式（非全量，仅人格基底）】\n" + "正文" * 130 + "\n🧾 TSL 机械核验 v0.11.2\n├─ L0 ✅做到", "S1", True),
        # v1.8 错位对账（机器台账S4=未命中 / S6=命中L3；树居末段防串扰）
        ("T13 D3宣告L3·机器未命中·无补载 → 必报", "【童灵·D3 上岗模式】任务域判定：L3行为规则域。" + "正文" * 130 + "\n🧾 TSL 机械核验 v0.11.5\n├─ L0 ✅做到", "S4", True),
        ("T14 D3宣告L3·显形已补载 → 不报(已恢复)", "【童灵·D3 上岗模式】任务域判定：L3行为规则域。已补载：L3。" + "正文" * 130 + "\n🧾 TSL 机械核验 v0.11.5\n├─ L0 ✅做到", "S4", False),
        ("T15 D3宣告L3·机器同判L3 → 不报(同源)", "【童灵·D3 上岗模式】任务域判定：L3行为规则域。" + "正文" * 130 + "\n🧾 TSL 机械核验 v0.11.5\n├─ L0 ✅做到", "S6", False),
        ("T16 D1回合宣告域 → 不参与错位判(仅D3)", "【童灵·D1 常驻模式（非全量，仅人格基底）】任务域判定：L3行为规则域。" + "正文" * 130, "S1", False),
    ]
    bad = 0
    print("=== doenglingz_level_declare_guard v%s 档位对账自测（含树位置+非D3越界+域错位+判据源显形判据）===" % __version__)
    for name, msg, sid, want in CASES:
        got = run(msg, sid)
        ok = (got == want)
        bad += 0 if ok else 1
        print("  %s %-32s 期望报警=%-5s 实得=%s" % ("\u2705" if ok else "\u274c", name, want, got))
    # ── v1.9 位置性假红用例（分段形态·transcript 读面）──
    tp_seg = mk_transcript("tp_seg.jsonl", [
        ("user", "帮我看下这个方案"),
        ("assistant", "【童灵·D1 常驻模式（非全量，仅人格基底）】\n我在。先取证再答。"),
        ("assistant", [{"type": "tool_use", "name": "Bash",
                        "input": {"command": "grep 童灵·D3 x"}}]),
        ("assistant", "【意图分类】评估类。\n结论如上。童灵在岗。"),
    ])
    tp_none = mk_transcript("tp_none.jsonl", [
        ("user", "帮我看下"),
        ("assistant", "【意图分类】评估类。正文里提到童灵。"),
    ])
    tp_tool = mk_transcript("tp_tool.jsonl", [
        ("user", "帮我看下"),
        ("assistant", [{"type": "tool_use", "name": "Bash",
                        "input": {"command": "echo 童灵·D1 常驻模式"}}]),
        ("assistant", "【意图分类】评估类。正文里提到童灵。"),
    ])
    tp_stale = mk_transcript("tp_stale.jsonl", [
        ("assistant", "【童灵·D1 常驻模式（非全量，仅人格基底）】上一回合的声明"),
        ("user", "新指令"),
        ("assistant", "【意图分类】评估类。正文里提到童灵，本回合没交代档位。"),
    ])
    EXTRA = [
        ("T17 档位块在分段前·payload看不见 → 不报(根治)", "【意图分类】评估类。\n结论如上。童灵在岗。", "S1", tp_seg, False),
        ("T18 两处都无档位 → 仍必报(防恒真)", "【意图分类】评估类。童灵在岗。", "S1", tp_none, True),
        ("T19 档位只在tool_use里 → 必报(防假绿)", "【意图分类】评估类。童灵在岗。", "S1", tp_tool, True),
        ("T20 上回合声明不顶本回合 → 必报(切片界)", "【意图分类】评估类。童灵在岗。", "S1", tp_stale, True),
        ("T21 payload自身有档位 → 回退腿不启用(不过界)", "【童灵·D1 常驻模式（非全量，仅人格基底）】正文", "S1", tp_none, False),
    ]
    mute = lambda s2, inject_path=None, as_of="": None
    m2, m3 = run("【童灵·D2 域模式】正文", "S1", mute), run("童灵·D1 / 童灵·D2 正文", "S2", mute)
    mut_ok = (not m2) and (not m3)
    print("  %s MUT 判据源置哑 → T2/T3 必同时变哑（实得 T2=%s T3=%s）" % ("\u2705" if mut_ok else "\u274c", m2, m3))
    print("合计 %d/%d 过＋变异%s（分母由 len(CASES) 实算·不含 v1.9 新用例）" % (len(CASES) - bad, len(CASES),
                                                          "被抓" if mut_ok else "未抓·探针作废"))
    # §3.9 承接标记（guard_selftest_check classify_mut 消费）：探针一直在跑，⛔未按标记留痕＝聚合器看不见
    #   ⇒ 该 🔴"新守卫缺变异自检"按设计正确（无标记＝无证据），本次补的是本件欠的承接，不是纠错。
    print("  %s MUT:%s 判据源置哑 → T2/T3 同时变哑（探针在岗且可证伪）"
          % ("✅" if mut_ok else "❌", "OK" if mut_ok else "FAIL"))
    # §3.9 承接标记（guard_selftest_check v0.3 classify_mut 消费）：探针真跑了≠留痕了——
    #   本件此前只把变异结果写进"合计"行的人话里，未按标记留痕 ⇒ 聚合器报"新守卫缺变异自检"。
    #   ⚠️ 定性如实：该红是**按设计正确**的（契约 09-18 立、探针存在不抵契约、无标记＝无"变异跑过"的痕迹），
    #   本次补的是**本件欠的承接**，不是纠错。2026-10-01·Qoder CN 承接。
    print("  %s MUT:%s 判据源置哑 → T2/T3 同时变哑（探针在岗且可证伪）"
          % ("✅" if mut_ok else "❌", "OK" if mut_ok else "FAIL"))
    # MUT2（v1.8）：置哑 _machine_layers → T13 必哑（证明错位判据确实吃 W3 台账这个源）
    # ── v1.9 新用例实跑（分母计入·⛔不另起小计糊弄）──
    for name, msg, sid, tp, want in EXTRA:
        got = run(msg, sid, tp=tp)
        ok = (got == want)
        bad += 0 if ok else 1
        print("  %s %-46s 期望报警=%-5s 实得=%s" % ("\u2705" if ok else "\u274c", name, want, got))
    # MUT3：置哑 _round_text → T17 必须变红（证明 T17 真吃回退腿，非恒绿）
    orig_rt = _round_text
    globals()["_round_text"] = lambda o: ""
    m17 = run("【意图分类】评估类。\n结论如上。童灵在岗。", "S1", tp=tp_seg)
    globals()["_round_text"] = orig_rt
    mut3_ok = bool(m17)
    print("  %s MUT3:回退腿置哑 → T17 必红（实得 T17=%s）" % ("\u2705" if mut3_ok else "\u274c", m17))
    print("  %s MUT3:%s 回退腿置哑 → T17 转红（探针在岗且可证伪）" % ("MUT:OK" if mut3_ok else "MUT:FAIL", "OK" if mut3_ok else "FAIL"))
    total = len(CASES) + len(EXTRA)
    orig_ml = _machine_layers
    globals()["_machine_layers"] = lambda sid, ledger_path=None: None
    m13 = run("【童灵·D3 上岗模式】任务域判定：L3行为规则域。" + "正文" * 130
              + "\n🧾 TSL 机械核验 v0.11.5\n├─ L0 ✅做到", "S4")
    globals()["_machine_layers"] = orig_ml
    mut2_ok = not m13
    print("  %s MUT2:W3台账源置哑 → T13 必哑（实得 T13=%s）" % ("✅" if mut2_ok else "❌", m13))

    # ── T22（v1.12·issue#6 判据源缺失显形·双向）：源缺失时「真需要判」的回合必报且含「判据源缺失」；
    #    源在场时不报该因——⚠️off 态用「存在但无 OUTPUT_LEVEL 字段」的夹具件，保证任何机器
    #   （含端用户机·真源路径必缺）上双向都可判定，⛔不依赖作者机文件在不在场。
    def run_raw(msg, sid):
        payload = json.dumps({"last_assistant_message": msg, "session_id": sid}, ensure_ascii=False)
        globals()["_expected_tier"] = lambda s2, inject_path=None, as_of="": orig(s2, inject_path=inj, as_of=as_of)
        buf = _io.StringIO()
        old = sys.stdin
        sys.stdin = _io.StringIO(payload)
        try:
            with contextlib.redirect_stdout(buf):
                check()
        finally:
            sys.stdin = old
            globals()["_expected_tier"] = orig
        return buf.getvalue()

    _lvl_real = LEVEL_SRC
    _msg22 = "【童灵·D3 上岗模式】" + "正文" * 130
    globals()["LEVEL_SRC"] = os.path.join(tmp, "不存在的08清单.md")
    _out22_on = run_raw(_msg22, "S4")
    _lvl_fix = os.path.join(tmp, "fake08_exists_but_no_output_level.md")
    with open(_lvl_fix, "w", encoding="utf-8") as _f22:
        _f22.write("08 清单夹具（存在但无 OUTPUT_LEVEL 字段）\n")
    globals()["LEVEL_SRC"] = _lvl_fix
    _out22_off = run_raw(_msg22, "S4")
    globals()["LEVEL_SRC"] = _lvl_real
    t22 = ("判据源缺失" in _out22_on) and ("判据源缺失" not in _out22_off)
    print("  %s T22 判据源缺失显形（#6·缺失必报/源在场不报该因·双向）" % ("\u2705" if t22 else "\u274c"))
    bad += 0 if t22 else 1
    total = total + 1
    globals()["LEVEL_SRC"] = globals().pop("_LEVEL_SRC_REAL", _lvl_real)
    print("合计 %d/%d 过（含 v1.9 新用例 %d 条·分母实算）" % (total - bad, total, len(EXTRA)))
    return 0 if (bad == 0 and mut_ok and mut2_ok and mut3_ok) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    try:
        if "--report" in sys.argv:
            report()
        else:
            check()
    except Exception:
        pass
    sys.exit(0)                       # 恒定放行·⛔不阻断（--self-test 走真实 rc）
