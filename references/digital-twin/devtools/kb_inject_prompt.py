#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
kb_inject_prompt.py — UserPromptSubmit 钩子：知识库确定性激活（知识库宪法落地·黑鲸第10端首装）。

设计定位（知识库设计哲学 01-通用规范 原则2/3 + 宪法"不依赖 AI 记得"）：
- 按需检索（原则2）：先过轻量意图门（ROUTE_TABLE 5 桶关键词预筛，零检索开销），命中才全量检索。
- 确定性触发（原则3）：机制在 pre-step 固定跑本脚本（由宿主钩子 spawn），不依赖 AI 记得调 search_kb。
- 单一真源：import search_kb（ROUTE_TABLE + search() 共用，路由表改一处，注入/审计跟着走）。
- 输出契约：stdout 注入文本（Top-3 锚点层 title+path+summary+理由）；空=未命中/失败 → 钩子链继续。
- 失败默认放行（exit 0），绝不阻断对话（守卫编写规范原则1/2）。
- 与 route_inject_prompt 的分工：Skill 唯一命中=强指令优先（该用什么 Skill）；本脚本=知识补位
  （该用什么知识）——宿主先跑 Skill 注入，未命中才跑本脚本，两者不打架。

双路架构 v2（2026-08-26·治 30s 冷载超时）：
  ① 快通道 _serve_search：UDS socket 问常驻引擎 kb_serve.py（模型/索引驻留，毫秒级返回，
     system python 直连不 execv）。意图门也交给引擎（路由表单一真源仍在 search_kb，
     含外部路由表覆盖一并生效）。
  ② 回退通道：快通道任何异常 → 本脚本自我 re-exec 进 .venv-st（2026-09-10 修复：
     旧架构靠 search_kb 顶层 execv 自动换身，v0.3.6 改 CLI 子进程委托后该路径失效）
     → 进程内 import search_kb 走完整语义检索。kb_serve 不存在时仍零单点。

用法：
  python3 kb_inject_prompt.py --prompt "写视频文案（介绍每日伙伴）"   # argv 模式·测试用
  echo '{"prompt":"..."}' | python3 kb_inject_prompt.py UserPromptSubmit   # 钩子 stdin 模式
"""
import sys
import os
import json
import time
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
SOCK_PATH = os.path.join(BASE, "kb.sock")

# ── 硬截止看门狗（2026-10-06 根治·修 UserPromptSubmit 60s 超时卡死整轮对话）──
# 病灶：快通道 socket 超时 50s + 回退冷跑（载入句子向量模型/2701 文档索引）可再耗数十秒，
#       两端相加逼近宿主 60s 硬上限 ⇒ 钩子超时 ⇒ 你这一轮提示整条被拦在门外（本会话实证）。
# 判据：注入是「补位」不是「必经」——超预算宁可放行，绝不可阻塞对话
#       （守卫编写规范原则1/2：失败默认放行）。故加一次性 ITIMER_REAL 闹钟，
#        到点抛 _Deadline → 顶层捕获 → 留痕 → exit 0 放行。
# 默认值 8s：> 热态实测（本会话 5.8s）·<< 60s 上限·冷启首跑让位给后台预热。
# 可调：env KB_HOOK_DEADLINE（秒，0=不设限·仅调试用）。
try:
    HOOK_DEADLINE = float(os.environ.get("KB_HOOK_DEADLINE", "8"))
except Exception:
    HOOK_DEADLINE = 8.0
_T0 = time.time()


class _Deadline(Exception):
    pass


def _elapsed_ms():
    return int((time.time() - _T0) * 1000)


def _arm_deadline():
    """装一次性闹钟（须在 venv re-exec 之后调用——execve 会重置 interval timer）。
    失败静默（平台不支持 → 退化为无保护，⛔不阻断）。"""
    if HOOK_DEADLINE <= 0:
        return
    def _h(_sig, _frm):
        raise _Deadline()
    try:
        signal.signal(signal.SIGALRM, _h)
        signal.setitimer(signal.ITIMER_REAL, HOOK_DEADLINE)
    except Exception:
        pass


def _disarm_deadline():
    try:
        signal.setitimer(signal.ITIMER_REAL, 0)
    except Exception:
        pass


def _tick(stage=""):
    """阶段边界显式复检（补一次性闹钟的窟窿）：闹钟是 one-shot，
    若在 socket recv 里被打断，后续阶段将裸奔——故每进下一阶段先验预算。"""
    if HOOK_DEADLINE > 0 and (time.time() - _T0) > HOOK_DEADLINE:
        raise _Deadline(stage)

# ── 2026-09-10 修复：回退通道自我 re-exec 进 .venv-st（保证回退=完整语义检索而非纯 BM25）──
# 背景：旧架构依赖 search_kb 模块顶层 execv 自动换身；v0.3.6 改子进程委托+__main__守卫后，
# import 场景不再换身 → 回退会退化为纯 BM25。此处由钩子自身换身（单发进程·execv 合法）。
_VENV_PY = os.path.expanduser("[记忆共享中心]/脚本中心/知识联邦引擎/.venv-st/bin/python")
if (os.environ.get("KB_HOOK_VENV") != "1"
        and os.path.exists(_VENV_PY)
        and os.path.realpath(sys.executable) != os.path.realpath(_VENV_PY)):
    import importlib.util as _ilu
    if _ilu.find_spec("sentence_transformers") is None:
        os.environ["KB_HOOK_VENV"] = "1"
        os.execv(_VENV_PY, [_VENV_PY, os.path.abspath(__file__)] + sys.argv[1:])

INJECT_TOPN = 3        # 注入锚点条数（渐进式加载锚点层·原则4：不给全文，按需 --drill 下钻）
CHAR_BUDGET = 1200     # 注入字符预算（超预算截断低分条目·防上下文溢出·对齐 search_kb 预算思想）

INJECT_MARK = "【知识库激活·确定性注入】"

# ── C1 观测接入（2026-09-07·OpenViking 借鉴唯一过闸项）：查询命中路径留痕 ──
# 延迟 import（仅 stdlib 依赖·快通道零 execv 开销）；记录失败静默不阻断注入。
try:
    from kb_query_trail import append_trail as _append_trail
except Exception:
    _append_trail = None
_TRAIL_SOURCE = "serve"

# ── #1 可观测性（2026-09-03·落地）：钩子回退事件写计数日志（与 search_kb 同文件）──
# 2026-09-10 根治：原写 BASE(=scripts/)/logs/，与 search_kb._log_degrade() 的引擎根
# logs/ 分叉成两本账（只看一份=判断残缺）→ 统一上溯一级到引擎根。
_DEGRADE_LOG = os.path.join(os.path.dirname(BASE), "logs", "kb_degrade.jsonl")

# ── 输出协议单一真源（2026-09-04 根治·Qoder CN 裸文本被产品判 "winner=none" 整轮丢弃）──
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

_PAYLOAD = {}
def _log_degrade(event, detail=""):
    """钩子回退（daemon 不可达→进进程检索）事件追加到 logs/kb_degrade.jsonl。
    失败静默吞掉。不放 search_kb 顶层 import（保快通道零 execv 开销）。"""
    try:
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_DEGRADE_LOG, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"ts": ts, "event": event, "detail": detail},
                                 ensure_ascii=False) + "\n")
    except Exception:
        pass


def is_kb_scene(task):
    """轻量意图门（与 audit_search_kb 同口径·单一真源 ROUTE_TABLE·惰性加载）。
    命中任意桶任一关键词 = 知识场景 → 才检索；未命中 → 空输出（零检索开销）。"""
    from search_kb import ROUTE_TABLE
    hits = []
    for b in ROUTE_TABLE:
        kw = [k for k in b["keywords"] if k in task]
        if kw:
            hits.append((b["name"], kw))
    return hits


def _serve_search(task):
    """快通道：问常驻引擎 kb_serve.py（含意图门+检索）。成功返回 (scores元组列表, 桶名列表)；
    未命中知识场景返回 ([], [])；引擎不可达/任何异常返回 None → 回退本地冷跑。"""
    try:
        import socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # 服务端单次检索实测 7~21s（2701 文档全库 + bge 向量 RRF），5s 超时必触发回退冷跑→偶发破 60s 钩子上限。
        # 拉到 50s：> P100 实测响应且 < WorkBuddy 60s 钩子硬上限，快通道稳定命中不再回退。
        s.settimeout(50.0)
        s.connect(SOCK_PATH)
        s.sendall((json.dumps({"task": task, "k": INJECT_TOPN}) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        s.close()
        resp = json.loads(buf.decode("utf-8"))
        if not (isinstance(resp, dict) and resp.get("ok")):
            return None
        scores = [(h["score"], h["path"],
                   {"src": h.get("src", ""), "title": h.get("title", ""),
                    "summary": h.get("summary", "")}, h.get("matched", []))
                  for h in resp.get("hits", [])]
        return scores, resp.get("buckets", [])
    except Exception:
        return None


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--prompt":
        task = sys.argv[2]
        _inject(task)
        return
    # 无 --prompt：读 stdin（v1.4.1 协议统一：优先解析 JSON payload 取 prompt 字段；解析失败回退全文）
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    global _PAYLOAD
    task = raw
    if raw:
        try:
            _pp = json.loads(raw)
            if isinstance(_pp, dict):
                _PAYLOAD = _pp
            if isinstance(_pp, dict) and _pp.get("prompt"):
                task = _pp["prompt"]
        except Exception:
            pass
    _inject(task)


def _inject(task):
    if not task or not task.strip():
        return
    task = task.strip()
    # ── 硬截止：整段注入（快通道 + 回退冷跑）一笔账，到点即放行 ──
    _arm_deadline()
    try:
        # ① 快通道：常驻引擎一并做意图门+检索（毫秒级）；not None 即采纳
        served = _serve_search(task)
        _tick("after_serve")   # 闹钟若已在 recv 内触发，这里补刀，⛔不让回退冷跑裸奔
        if served is not None:
            scores, bucket_names = served
            if not scores:
                return  # 引擎判非知识场景（或零召回）→ 放行
            if _append_trail:
                _append_trail(task, scores, bucket_names, source="serve")
            _emit(scores, bucket_names)
            return
        # ② 回退：本地冷跑（本进程已在 .venv-st 内·import search_kb 即完整语义检索）
        #    意图门先行：未命中知识场景 → 空输出（预筛成本≈0，避免全量检索延迟）
        hits = is_kb_scene(task)
        if not hits:
            return
        _log_degrade("hook_fallback_inprocess")  # daemon 不可达→进进程检索（向量/BM25 由 search_kb 决定）
        _tick("before_cold_import")  # 冷跑前最后一道闸：模型载入不可中断，只能提前挡
        try:
            from search_kb import search
            scores, buckets = search(task, k=INJECT_TOPN)
        except Exception:
            return  # 检索失败默认放行
        if not scores:
            return
        # hits 元组 = (桶名字符串, 关键词列表)，首位即桶名
        if _append_trail:
            _append_trail(task, scores, [b for b, _ in hits], source="fallback")
        _emit(scores, [b for b, _ in hits])
    except _Deadline:
        # 到点未出结果 → 留痕 + 放行（⛔不阻塞对话）。冷启首跑属预期，
        # 常驻引擎在后台继续预热，下一轮提示即走热态快通道。
        _log_degrade("hook_deadline_exceeded",
                     "budget=%ss elapsed=%sms" % (HOOK_DEADLINE, _elapsed_ms()))
    except Exception:
        pass
    finally:
        _disarm_deadline()


def _hp_emit(ctx):
    """输出协议委托 hook_protocol 单一真源（2026-09-04 根治·同 route_inject 口径）。"""
    if _hp is not None:
        return _hp.emit(ctx, payload=_PAYLOAD, argv=sys.argv[1:],
                        event="UserPromptSubmit", script=os.path.basename(__file__))
    try:  # 真源缺失 → 降级裸文本并留痕（⛔不静默）
        with open(_DEGRADE_LOG, "a", encoding="utf-8") as f:
            f.write('{"reason":"hook_protocol import failed","script":"kb_inject_prompt.py"}\n')
    except Exception:
        pass
    sys.stdout.write(ctx)
    return "text"


def _emit(scores, bucket_names):
    """格式化注入文本：锚点层（title+path+summary+理由）·字符预算截断·端感知输出"""
    used = 0
    lines = []
    lines.append("%s任务命中知识场景（%s），自动召回 Top-%d 锚点（渐进式加载·可 --drill 下钻全文）："
                 % (INJECT_MARK, "/".join(bucket_names), min(len(scores), INJECT_TOPN)))
    for i, (s, p, d, matched) in enumerate(scores, 1):
        rel = os.path.relpath(p, os.path.expanduser("~"))
        sc = f"{s:.4f}" if s < 1 else f"{s:.1f}"
        entry = ("[%d] %s | %s\n    路径: %s\n    命中: %s | %s"
                 % (i, d.get("src", ""), d.get("title", ""), rel,
                    ", ".join(matched[:6]), d.get("summary", "")[:60]))
        if used + len(entry) > CHAR_BUDGET:
            break
        used += len(entry)
        lines.append(entry)
    # ── 主动检索提示行（2026-10-01·你裁决落地·修"能搜不搜"行为留白）：把工具从藏着变递到手边──
    # 路径统一用 D3 契约⑧权威路径（全机惯例·脚本中心适配副本亦写此路径不写自身）。
    lines.append("📌 主动检索（锚点不够/需更多证据时必跑）：python3 [记忆共享中心]/脚本中心/search_kb.py \"关键词\"")
    lines.append("📌 下钻全卡正文：python3 [记忆共享中心]/脚本中心/search_kb.py --drill <上列路径>")
    lines.append("⛔ 这条没用 → 回写路由表/关键词（反馈闭环）")
    ctx = "\n".join(lines)
    _hp_emit(ctx)


if __name__ == "__main__":
    main()
