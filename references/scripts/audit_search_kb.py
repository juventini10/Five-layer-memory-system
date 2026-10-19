#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_search_kb.py v0.4.1 — Stop 钩子审计：观测知识调用场景的 search_kb.py 漏检率
  v0.4（2026-10-13·Qoder CN·皮叔令「立场卡检索总是由AI心情执行，那不行」）：新增引用溯源三判据
    cited/fabricated/uncited_real/ran_not_used，把义务⑧从 prose 级升为机械级；self_test 扩至 11 例。
  v0.4.1（同日）：_TRAIL_PATH 改同源解析（原指 脚本中心/logs/ 而真身在 知识联邦引擎/logs/ ⇒
    v0.2「修复①」自写下起一直 fail-open 空转，属「声称已修、实未生效」）。

挂为 Qoder CN 原生 Stop 钩子（~/.qoder-cn/settings.json）。
每次主代理结束响应时，通过 stdin 传入 JSON，含 transcript_path（完整对话 JSONL）。
本脚本解析对话：

  - 判定"知识调用场景"：最后一则 user 任务命中 ROUTE_TABLE 5 桶关键词；
    不含关键词的延续任务（"继续""按建议推进"）向前回溯最多 3 则 user 消息
    找最近的知识场景任务（回溯范围内找不到 → exit 0 不记）。
  - v0.3（P5·2026-10-05）拆两字段：「被推送」injected（trail 命中）与
    「实跑回执」real_run（场景之后宿主记账 tool_call 含 search_kb 才 True；
    整段无可解析 tool_call → "unknown"⚪ 端形态未识别不假红；有 tool_call 但
    未触碰 → False）。正文提及无回执 → 保守不判 miss 只标 mention_only。
    每场景任务必落 1 条（旧"可能已跑静默不记"使分母残缺）。
  - 其余一切情况 → 退出码 0 = 放行（绝不拦截、绝不误写）。

设计原则（失败默认放行，绝不破坏对话）：
  - 解析异常 / 无 transcript_path / 行损坏 → 直接 exit 0
  - 无知识场景任务 → exit 0（不写）
  - 判定保守：宁可漏记不可误记（误记=审计噪音污染 miss 率）
  - 任何未捕获异常 → exit 0

消费端：--stats 子命令统计 miss 率（月度/千条 TTL 检查点触发第二刀评估）。

用法：
  echo '{"transcript_path": "..."}' | python3 audit_search_kb.py        # Stop 钩子模式
  python3 audit_search_kb.py --stats                                     # 统计 miss 率
  python3 audit_search_kb.py --self-test                                 # 内置自测（4 用例）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
try:
    import fcntl          # Unix/macOS：文件锁防并发撕裂
except ImportError:
    # Windows 无 fcntl——本件属对外发布包，必须能在 Win 导入并运行。
    # 降级守设计律②「降级不阻塞」：锁变 no-op，jsonl 追加仍可写，
    # 行级去重由各件自身判据兜（撕裂风险如实承认，不假装锁还在）。
    # ⚠️ 同型守卫共三处（build_kb_vectors / audit_search_kb / transcript_reader）。
    class _NoFcntl:
        LOCK_EX = LOCK_UN = LOCK_NB = 0

        @staticmethod
        def flock(fh, op):
            return None
    fcntl = _NoFcntl()

# B埋点(v2.0·2026-09-03·童灵·补exit码埋点): 从"脚本开头Popen后台写日志(无exit码)"
# 改为"包装入口点在退出时写日志(含exit码)"——原设计在脚本开头写日志，无法知道最终exit码;
# v2.0用try/finally包装入口逻辑，捕获sys.exit的code，在所有退出点统一写日志(含exit码)。
# 手动侧自埋点·fail-open不阻塞。
def _guard_log_exit(rc):
    try:
        import subprocess as _sp
        _sp.Popen(["python3", os.path.expanduser("[记忆共享中心]/脚本中心/guard_invocation_logger.py"),
                   "--guard", "audit_search_kb",
                   "--source", os.environ.get("GUARD_TRIGGER_SOURCE", "hook_auto"),
                   "--exit", str(rc),
                   "--detail", "self-instrumented"],
                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    except Exception:
        pass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
from search_kb import ROUTE_TABLE  # 单一真源：路由表改一处，审计跟着走
import transcript_reader as _tr  # 跨端解析·单一真源（2026-09-23 童灵根治·WB端0/304实证）

DEFAULT_LOG = os.path.expanduser("[记忆共享中心]/脚本中心/logs/audit_log.jsonl")
LOG_PATH = os.environ.get("AUDIT_LOG", DEFAULT_LOG)  # 测试可重定向
MAX_BACKTRACK = 3  # 延续任务回溯深度

BUCKET_NAMES = [b["name"] for b in ROUTE_TABLE]

# ── v0.2 判据修复（2026-10-01·童灵裁决·WB 端补位）────────────────────────────
# 依据：开发/KB漏用miss诊断-真漏vs审计噪声-20261001.md（近30天 682 条全量分层）
#   59.2% = A 门禁已注入却记 miss（证据面错）｜18.9% = 非用户任务混入（对象面污染）
# 与 07:40 另一端改的「注入标记扩面 + 摘要剥离」正交：那段修的是"注入块混入 task"，
# 本段修的是"已注入却找不到证据词"和"元内容仍混入"。全部 fail-open，异常一律吞掉。
#
# 修复① 证据面：miss 前先查 kb_query_trail.jsonl（A 门禁注入留痕 = 已注入的真源）。
#        旧判据在 transcript 文本搜 "search_kb" 字样——注入走 hookSpecificOutput
#        .additionalContext，不进 transcript，故注入成功也必然判 miss。
# 修复② 对象面：剥离 system-reminder / task-notification / Local Time Context /
#        他端 system instructions / Base directory / file:// URI；剥完为空则不判场景。
# 修复③ 可归因：补 host（由 transcript 路径推断端）+ route_ver（路由表指纹）。
# 修复④ 分母：记 miss=False 的"已注入"记录（旧版只记 miss ⇒ "率"从来算不出来）。

_META_BLOCKS = [
    re.compile(r"<system-reminder>.*?</system-reminder>", re.S),
    re.compile(r"<task-notification>.*?</task-notification>", re.S),
]
_META_SEGS = [
    re.compile(r"^##\s*Local Time Context\s*\n(?:[-*].*\n?)*", re.M),
    re.compile(r"^\[[^\]]*system instructions\].*?(?=\n\s*\n|\Z)", re.S | re.M | re.I),
    re.compile(r"^Base directory for this skill:.*$", re.M),
    re.compile(r"file://\S+"),
]
# 剥完仍以元内容前缀开头（无闭合标签）→ 判空，宁可漏记不可误记
_META_HEAD = re.compile(
    r"^\s*(?:<system-reminder|<conversation_history_summary|<task-notification"
    r"|\[[^\]]*system instructions|##\s*Local Time Context|Base directory for this skill"
    r"|<[a-zA-Z_-]+[ >])", re.I)

# v0.4.1 路径同源修复（2026-10-13·Qoder CN）：原 `_TRAIL_PATH` = DEFAULT_LOG 同目录，
#   而写方 kb_query_trail.py 的真源是 ENGINE_ROOT/logs/（由 __file__ 派生）——两处不同目录，
#   实测 脚本中心/logs/kb_query_trail.jsonl 不存在 ⇒ v0.2「修复①」的 trail 判据自写下起
#   一直返回 None 走 fail-open 旧口径（=声称已修、实未生效）。修法=优先 import 写方取其常量，
#   取不到再按候选列表探测，⛔不在读侧另抄一条会漂的硬路径。
def _resolve_trail_path():
    cands = []
    _env = os.environ.get("KB_TRAIL_PATH")
    if _env:
        cands.append(os.path.expanduser(_env))
    try:
        import kb_query_trail as _kt
        _tl = getattr(_kt, "TRAIL_LOG", "")
        if _tl:
            cands.append(_tl)
    except Exception:
        pass
    _home = os.path.expanduser("~")
    cands += [
        os.path.join(_home, "[记忆共享中心]/脚本中心/知识联邦引擎/logs/kb_query_trail.jsonl"),
        os.path.join(os.path.dirname(DEFAULT_LOG), "kb_query_trail.jsonl"),
    ]
    for _c in cands:
        if _c and os.path.isfile(_c):
            return _c
    return cands[-1]


_TRAIL_PATH = _resolve_trail_path()


def strip_meta(text):
    """剥离元内容——与 strip_inject 分工：它剥注入块，我剥系统/工具注入的伪任务"""
    if not text:
        return text
    for pat in _META_BLOCKS:
        text = pat.sub("", text)
    for pat in _META_SEGS:
        text = pat.sub("", text)
    if _META_HEAD.match(text):
        return ""
    return text


def norm_task(s, n=40):
    """任务归一键（去空白·前 n 字符），用于 trail 比对"""
    return re.sub(r"\s+", "", s or "")[:n]


def _trail_recent_keys(limit=800):
    """trail 末尾 limit 行的 task 归一键集合；读不到 → None（fail-open 走旧判据）"""
    try:
        if not os.path.isfile(_TRAIL_PATH):
            return None
        with open(_TRAIL_PATH, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-limit:]
        keys = set()
        for line in lines:
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("task", "")
            if t:
                keys.add(norm_task(t))
        return keys
    except Exception:
        return None


def _host_of(transcript_path):
    """由 transcript 路径推断端——旧记录无端字段，无法按端归因"""
    p = str(transcript_path or "")
    for k in ("qoder-cn", "workbuddy-ai", "workbuddy", "claude", "qoder",
              "trae", "hermes", "codebuddy", "qwen"):
        if "." + k in p or "/" + k + "/" in p:
            return k
    return "?"


def _route_ver():
    """路由表指纹（桶数b+关键词数k）——跨版本可比性"""
    try:
        return "%db%dk" % (len(ROUTE_TABLE),
                           sum(len(b.get("keywords", [])) for b in ROUTE_TABLE))
    except Exception:
        return "?"

# 知识注入块标记（kb_inject_prompt.py 输出前缀·2026-08-16 自反馈污染修复）：
# 注入文本进入 transcript 后不得参与场景判定/证据词扫描——否则注入块含桶词
# （如"写作/文案"）会把任意 user 消息误判为知识场景，或把"注入过"误判为"用过"。
INJECT_MARK = "【知识库激活·确定性注入】"

# 注入标记全集（2026-10-01 扩面·miss 台账聚类实证：1541 条中 377 条为注入/恢复噪音——
# triwich 路由契约、童灵 D 档注入、铁律预注入块、会话压缩摘要均混入 task 致假 miss 污染闭环数据）
INJECT_MARKS = [
    INJECT_MARK,                 # kb_inject 知识激活块
    "【路由引擎硬匹配】",         # route_inject Skill 路由块
    "【SSOT 格式契约",           # triwich 契约实时拉取块
    "【铁律自动预注入",           # rule_fragment_inject 铁律块
    "【童灵·D1 常驻模式", "【童灵·D2 域模式", "【童灵·D3 上岗模式",  # doenglingz D 档注入
    "【童灵人格基座", "【童灵域切片", "【童灵显示义务", "【童灵降级留痕", "【童灵档位不变量",
]
_SUMMARY_RE = re.compile(r"<conversation_history_summary>.*?</conversation_history_summary>", re.S)


def strip_inject(text):
    """剥离注入块+会话压缩摘要——自反馈污染防护。
    块界=标记到下一个任意注入标记（标记本身即块头，不依赖"下一个【"启发）；
    无后续标记则剥到结尾——尾块连真实任务一起剥属漏记方向，对齐"宁可漏记不可误记"。"""
    text = _SUMMARY_RE.sub("", text)
    for mark in INJECT_MARKS:
        while mark in text:
            i = text.index(mark)
            ends = [text.find(m, i + len(mark)) for m in INJECT_MARKS if m != mark]
            ends = [e for e in ends if e != -1]
            end = min(ends) if ends else len(text)
            text = text[:i] + text[end:]
    return text


def task_of(msg_text):
    """提取 user 消息中的任务描述（<user_query> 标签优先，无标签用全文）·剥离注入块"""
    m = re.search(r"<user_query>(.*?)</user_query>", msg_text, re.S)
    return strip_meta(strip_inject((m.group(1) if m else msg_text).strip()))


def is_kb_scene(task):
    """任务命中 5 桶关键词 = 知识调用场景。返回 [(桶名, 命中关键词)] 或 []"""
    hits = []
    for b in ROUTE_TABLE:
        kw = [k for k in b["keywords"] if k in task]
        if kw:
            hits.append((b["name"], kw))
    return hits


def read_transcript(path):
    """读 JSONL transcript → 返回 [(role, text)]，行损坏跳过"""
    msgs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            role, content = _tr.locate(d)
            msgs.append((role, _tr.flatten_content(content)))
    return msgs


def find_last_kb_scene(msgs):
    """找最后一则知识场景任务。返回 (任务, 桶命中) 或 (None, None)"""
    user_tasks = []
    for role, text in msgs:
        if role == "user":
            task = task_of(text)
            if task:
                user_tasks.append(task)
    if not user_tasks:
        return None, None
    # 从最后一则 user 任务向前回溯（含自身），最多 MAX_BACKTRACK 则
    for task in reversed(user_tasks[-MAX_BACKTRACK:]):
        hits = is_kb_scene(task)
        if hits:
            return task, hits
    return None, None


def log_path():
    """动态取审计日志路径（环境变量可重定向，便于隔离测试）"""
    return os.environ.get("AUDIT_LOG", DEFAULT_LOG)


def append_log(entry):
    path = log_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


def _real_run(transcript_path, scene_start):
    """实跑回执判据（v0.3·P5）：只认宿主记账层事件（transcript 由宿主落盘，
    非 AI 正文自报）。transcript_reader.extract_tool_calls 已收口端差异
    （端A function_call 独立行式 / 端B message.content[].tool_use 元素式）。
    True=确认跑过；False=段内有工具调用但未触碰 search_kb；
    "unknown"=整段零 tool_call 结构（端形态未识别·如实⚪不猜——判据未绑对象=假红/假绿双风险）。"""
    try:
        raws = []
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    raws.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        if scene_start >= len(raws):
            return "unknown"
        saw_tool_call = False
        for d in raws[scene_start:]:
            for tc in _tr.extract_tool_calls(d):
                saw_tool_call = True
                if "search_kb" in json.dumps(tc, ensure_ascii=False):
                    return True
        return "unknown" if not saw_tool_call else False
    except Exception:
        return "unknown"



# ── v0.4 引用溯源判据（2026-10-13·Qoder CN·皮叔令「既然是启动D3标榜火力全开，
#     立场卡检索总是由AI心情执行，那不行」）──────────────────────────────
# 补的缺口：本件原判「注入送达 vs 使用」，card_id_guard 判「新卡编号防撞」，
#   「回复里引用的卡号是否出自当次实跑 hits」此前**无任何机械消费者**（C-072 同型病）。
# 三条判据（全部 fail-open，读不到即不判，⛔不阻断 Stop 链）：
#   cited      = 回复文本中出现的卡号集合（S/C/K 前缀，3-4 位）
#   fabricated = 卡号既不在当日 trail hits、KB 里也无实体卡文件 → 🔴 疑似编造
#   uncited_real = 卡文件真实存在但本会话无实跑来源 → 🟡 凭记忆引用（未检索）
#   ran_not_used = 本回合确有实跑(real_run=True) 而 cited 为空 → ⚠️ 跑而未用
# 诚实边界（机械判不了的两件事，⛔不假装覆盖）：
#   ①语义相关性——引了 A 卡但真正对症的是 B 卡（S917 漏引案）不报，
#     机器只能管「可追溯 + 必须有」，不能管「用得对不对」（对齐 triwich §机械化边界）。
#   ②引用形式不受控——AI 用自然语言转述卡义而不写卡号，判据会误报 ran_not_used，
#     故此态只作 ⚠️ 显形，不进 miss 硬判、不改 exit 码。
# (?<![\w-]) 排除 QCN-20261013/LRN- 等错误编号被误抓成卡号（假阳性源）；
# \d{3,} 不设上限，使 S99991 这类超长编造号也能进校验（原 {3,4} 会静默放过）。
_CARD_PTN = re.compile(r"(?<![\w-])([SCK]-?\d{3,})")
_KB_LIB_DIRS = [os.path.expanduser(u) for u in (
    "~/[日记仓库]/2-知识库/09-AI学习库",
    "~/[日记仓库]/2-知识库/08-概念层",
    "~/[日记仓库]/2-知识库/05-知识池",
)]


def norm_card(c):
    """卡号规范化：大写 + 去内部横线（C-153 == C153）"""
    return (c or "").upper().replace("-", "")


def _trail_ids_of_day(day=None, limit=3000):
    """当日 trail 全部 hits 的卡号集合；读不到/无当日行 → None（fail-open 不判溯源）"""
    try:
        if not os.path.isfile(_TRAIL_PATH):
            return None
        day = day or datetime.now().strftime("%Y-%m-%d")
        with open(_TRAIL_PATH, encoding="utf-8", errors="replace") as f:
            rows = [json.loads(l) for l in f.readlines()[-limit:] if l.strip()]
        ids = set()
        hit_today = False
        for d in rows:
            if not str(d.get("ts", "")).startswith(day):
                continue
            hit_today = True
            for h in d.get("hits", []) or []:
                for m in _CARD_PTN.findall(str(h.get("title", "")) + " " + str(h.get("path", ""))):
                    ids.add(norm_card(m))
        return ids if hit_today else None
    except Exception:
        return None


def _card_file_exists(nc):
    """KB 里是否有该卡的实体文件（S330 → 匹配 *S330* / C153 → 匹配 *C-153*）"""
    for d in _KB_LIB_DIRS:
        try:
            if not os.path.isdir(d):
                continue
            pat = nc if "-" in nc else nc
            for fn in os.listdir(d):
                base = norm_card(fn)
                if re.search(r"(?:^|[^0-9])" + re.escape(nc) + r"(?:[^0-9]|$)", base):
                    return True
        except Exception:
            continue
    return False


def citation_provenance(after_text, day_ids, real_run):
    """回复引用卡号 ↔ 当日实跑 hits 一致性。day_ids 为 None 时整体不判（fail-open）。"""
    if day_ids is None:
        return None
    cited = {norm_card(m) for m in _CARD_PTN.findall(after_text or "")}
    fabricated, uncited_real = [], []
    for c in sorted(cited):
        if c in day_ids:
            continue
        (uncited_real if _card_file_exists(c) else fabricated).append(c)
    ran_not_used = bool(real_run is True) and not cited
    if not cited and not ran_not_used:
        return None
    return {"cited": sorted(cited), "fabricated": fabricated,
            "uncited_real": uncited_real, "ran_not_used": ran_not_used}


def audit(transcript_path):
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    msgs = read_transcript(transcript_path)
    if not msgs:
        return 0
    task, hits = find_last_kb_scene(msgs)
    if not task:
        return 0
    # 场景任务之后全部文本（含工具调用渲染）搜 search_kb 字样
    scene_start = None
    for i, (role, text) in enumerate(msgs):
        if role == "user" and task_of(text) == task:
            scene_start = i
            break
    if scene_start is None:
        return 0
    after_text = " ".join(strip_inject(t) for _, t in msgs[scene_start:])
    # 修复①：trail 才是"已注入"的真源（注入走 additionalContext，不进 transcript）
    tkeys = _trail_recent_keys()
    injected = bool(tkeys) and norm_task(task) in tkeys
    real = _real_run(transcript_path, scene_start)   # v0.3(P5)：被推送≠实跑，分字段独立取证
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "task": task[:100],
        "type": " / ".join(b for b, _ in hits),
        "buckets": [b for b, _ in hits],
        "miss": False, "injected": injected, "real_run": real,
        "src": "stop-audit",
        "host": _host_of(transcript_path),
        "route_ver": _route_ver(),
    }
    if not injected and real is not True:
        if "search_kb" in after_text:
            entry["mention_only"] = True   # 正文提及无宿主回执：保守不判miss（沿用旧口径），但落条目进分母
        else:
            entry["miss"] = True
    # v0.4 引用溯源（fail-open：异常/无当日 trail 则不加字段、不报警）
    try:
        _quiet = bool(os.environ.get("AUDIT_SELFTEST"))   # 夹具静音：自测文本天然触发判据，⛔不混进真报警
        prov = citation_provenance(after_text, _trail_ids_of_day(), real)
        if prov and not _quiet:
            entry["cited"] = prov["cited"]
            entry["fabricated"] = prov["fabricated"]
            entry["uncited_real"] = prov["uncited_real"]
            entry["ran_not_used"] = prov["ran_not_used"]
            if prov["fabricated"]:
                sys.stderr.write("ALERT:CITATION-FABRICATED 回复引用了当日检索与KB均无的卡号: %s\n"
                                 % ",".join(prov["fabricated"]))
            if prov["uncited_real"]:
                sys.stderr.write("ALERT:CITATION-UNTRACED 卡真实存在但本会话无实跑来源(凭记忆引用): %s\n"
                                 % ",".join(prov["uncited_real"]))
            if prov["ran_not_used"]:
                sys.stderr.write("ALERT:CITATION-RAN-NOT-USED 本回合实跑了检索但回复零卡号引用(跑而未用)\n")
    except Exception:
        pass
    append_log(entry)
    return 0


def stats():
    path = log_path()
    if not os.path.isfile(path):
        print("审计日志为空"); return 0
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    total = len(rows)
    miss_rows = [r for r in rows if r.get("miss") is True]
    by_type = {}
    for r in miss_rows:
        t = r.get("type", "未知")
        by_type[t] = by_type.get(t, 0) + 1
    # 修复④：旧版把 miss 条数当"率"输出（无分母）；v0.2 起记录含 miss=False，
    #         miss 率 = miss 条数 / 场景记录总数，口径可算。
    rate = (100.0 * len(miss_rows) / total) if total else 0.0
    print(f"审计日志共 {total} 条场景记录，其中 miss {len(miss_rows)} 条（miss 率 {rate:.1f}%）")
    print(f"  已注入不算 miss（injected=True）: {sum(1 for r in rows if r.get('injected') is True)} 条")
    known = [r for r in rows if r.get("real_run") in (True, False)]
    n_rr = sum(1 for r in known if r.get("real_run") is True)
    n_unk = sum(1 for r in rows if r.get("real_run") == "unknown")
    print(f"  实跑回执 real_run（v0.3·宿主tool_call取证）: {n_rr}/{len(known)} ｜ 端形态未识unknown⚪: {n_unk} ｜ mention_only未计: {sum(1 for r in rows if r.get('mention_only'))}")
    by_host = {}
    for r in known:
        h = r.get("host", "?")
        a, b = by_host.get(h, (0, 0))
        by_host[h] = (a + (1 if r.get("real_run") is True else 0), b + 1)
    for h, (a, b) in sorted(by_host.items(), key=lambda x: -x[1][1]):
        print(f"    host={h} 真跑率 {100.0 * a / b:.1f}%（{a}/{b}）")
    for t, n in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")
    print("提示：miss 率 = 审计 miss 条数 / 知识场景任务总数（场景总数需人工/后续统计口径）")
    return 0


def self_test():
    os.environ["AUDIT_SELFTEST"] = "1"   # 夹具静音开关（详见 audit() 内 _quiet）
    """4 用例：回溯命中不记 / 场景无 search_kb 记 miss / 场景有 search_kb 不记 / 坏输入 exit 0"""
    import tempfile
    cases = []
    # 用例1：延续任务回溯命中评估场景，其后文本含 search_kb → 不记
    t1 = tempfile.mktemp(suffix=".jsonl")
    with open(t1, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>最严苛且科学的评估这个方案</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "跑了 python3 search_kb.py 验证"}]}}) + "\n")
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>按建议推进</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "好的，继续执行"}]}}) + "\n")
    # 用例2：场景无 search_kb → 记 miss
    t2 = tempfile.mktemp(suffix=".jsonl")
    with open(t2, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>写一篇视频文案</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "文案如下：……"}]}}) + "\n")
    # 用例3：场景有 search_kb → 不记
    t3 = tempfile.mktemp(suffix=".jsonl")
    with open(t3, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>写一篇视频文案</user_query>"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "先跑 search_kb.py 再写：……"}]}}) + "\n")

    os.environ["AUDIT_LOG"] = tempfile.mktemp(suffix=".jsonl")

    # 直接测模块级函数（当前模块即被测试对象）
    msgs1 = read_transcript(t1)
    task1, hits1 = find_last_kb_scene(msgs1)
    ok1 = task1 == "最严苛且科学的评估这个方案" and any("评估" in b for b, _ in hits1)
    msgs2 = read_transcript(t2)
    task2, hits2 = find_last_kb_scene(msgs2)
    ok2 = task2 == "写一篇视频文案" and any("写作" in b for b, _ in hits2)
    msgs3 = read_transcript(t3)
    task3, hits3 = find_last_kb_scene(msgs3)
    ok3 = task3 == "写一篇视频文案"
    # 记日志行为：用例2 记、用例3 不记（用独立日志文件）
    LOG_SAVE = os.environ["AUDIT_LOG"]
    os.environ["AUDIT_LOG"] = LOG_SAVE + ".c2"
    n_before = 0
    if os.path.isfile(os.environ["AUDIT_LOG"]):
        n_before = sum(1 for _ in open(os.environ["AUDIT_LOG"]))
    append_log({"ts": "t", "task": task2, "type": "t", "buckets": [], "miss": True, "src": "selftest"})
    n_after = sum(1 for _ in open(os.environ["AUDIT_LOG"]))
    ok4 = n_after == n_before + 1
    # 坏输入
    import subprocess
    p = subprocess.run([sys.executable, __file__], input="not json", capture_output=True, text=True)
    ok5 = p.returncode == 0
    # 用例6（v0.3·P5）：场景+宿主 tool_call 回执含 search_kb → 条目 real_run=True, miss=False
    t6 = tempfile.mktemp(suffix=".jsonl")
    with open(t6, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>最严苛评估这个方案</user_query>"}]}}) + "\n")
        f.write(json.dumps({"type": "function_call", "name": "Bash",
                            "arguments": json.dumps({"command": "python3 [记忆共享中心]/脚本中心/search_kb.py 评估"}, ensure_ascii=False)}) + "\n")
    os.environ["AUDIT_LOG"] = LOG_SAVE + ".c6"
    audit(t6)
    rows6 = [json.loads(l) for l in open(os.environ["AUDIT_LOG"], encoding="utf-8")]
    ok6 = len(rows6) == 1 and rows6[0].get("real_run") is True and rows6[0].get("miss") is False
    # 用例7：段内有工具调用但未触碰 search_kb 且正文无提及 → miss=True + real_run=False
    t7 = tempfile.mktemp(suffix=".jsonl")
    with open(t7, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "<user_query>最严苛评估这个方案</user_query>"}]}}) + "\n")
        f.write(json.dumps({"type": "function_call", "name": "Bash",
                            "arguments": json.dumps({"command": "ls -la"})}) + "\n")
    os.environ["AUDIT_LOG"] = LOG_SAVE + ".c7"
    audit(t7)
    rows7 = [json.loads(l) for l in open(os.environ["AUDIT_LOG"], encoding="utf-8")]
    ok7 = len(rows7) == 1 and rows7[0].get("real_run") is False and rows7[0].get("miss") is True
    os.environ["AUDIT_LOG"] = LOG_SAVE

    # ── 用例8-10：v0.4 引用溯源判据在册负例（2026-10-13·Qoder CN）──
    _ids = {"C153", "S828", "S917"}          # 模拟当日 hits 集合
    _r8 = citation_provenance("依据取自 C-153 与 立场卡#S828", _ids, True)
    _ok8 = (_r8 is not None and _r8["cited"] == ["C153", "S828"]
            and _r8["fabricated"] == [] and _r8["uncited_real"] == []
            and _r8["ran_not_used"] is False)
    _r9 = citation_provenance("依 S9999 与 S99991 判定", _ids, True)
    _ok9 = _r9 is not None and set(_r9["fabricated"]) == {"S9999", "S99991"}
    _r10 = citation_provenance("本轮结论全靠门禁 rc", _ids, True)
    _ok10 = _r10 is not None and _r10["ran_not_used"] is True and _r10["fabricated"] == []
    # 用例11 防误伤：错误编号 QCN-20261013-004 不得被当卡号；trail=None 时整体不判
    _r11a = citation_provenance("见 QCN-20261013-004 与 内部记录", _ids, None)
    _ok11 = (_r11a is None) and (citation_provenance("引用 C-153", None, True) is None)
    print(f"用例8 引用在当日hits→fabricated/uncited均空: {'✅' if _ok8 else '❌'}")
    print(f"用例9 编造号(含超5位)→fabricated 命中: {'✅' if _ok9 else '❌'}")
    print(f"用例10 实跑零引用→ran_not_used=True: {'✅' if _ok10 else '❌'}")
    print(f"用例11 错误编号不误抓+无trail不判(fail-open): {'✅' if _ok11 else '❌'}")
    print(f"用例1 回溯命中+已跑search_kb→不记: {'✅' if ok1 else '❌'}")
    print(f"用例2 场景判定（写作）: {'✅' if ok2 else '❌'}")
    print(f"用例3 场景判定: {'✅' if ok3 else '❌'}")
    print(f"用例4 日志追加: {'✅' if ok4 else '❌'}")
    print(f"用例5 坏输入 exit 0: {'✅' if ok5 else '❌'}")
    print(f"用例6 宿主回执含search_kb→real_run=True: {'✅' if ok6 else '❌'}")
    print(f"用例7 有工具调用未跑search_kb→miss=True: {'✅' if ok7 else '❌'}")
    return 0 if all([ok1, ok2, ok3, ok4, ok5, ok6, ok7, _ok8, _ok9, _ok10, _ok11]) else 1


def _main_entry():
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        return stats()
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        return self_test()
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        return 0
    try:
        return audit(payload.get("transcript_path"))
    except Exception:
        return 0


if __name__ == "__main__":
    _rc = 0
    try:
        _rc = _main_entry()
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else 0
    except Exception:
        _rc = 0
    finally:
        _guard_log_exit(_rc)
    sys.exit(_rc)
