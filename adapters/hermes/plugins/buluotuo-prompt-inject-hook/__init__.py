"""布洛陀公共逐轮注入守卫 · Hermes 端适配（pre_llm_call 通道）。

## 存在理由（纠正一个跨端误判·本文件的第一性原理）

脚本哲学 SSOT 的 Hermes 列曾把 11 个守卫全标 🔴 待支持，理由写「无
UserPromptSubmit 事件·平台边界」。**这个前提是错的**，2026-10-01 源码实测：

    hermes_cli/plugins.py:109  VALID_HOOKS ⊇ {pre_llm_call, post_llm_call,
                                            pre_tool_call, on_session_start, on_session_end}
    agent/turn_context.py:754-777  _collect_pre_llm_call_context()
        → 插件返回值 {"context": ...} 注入**本轮用户消息**（每轮）= 等价 UserPromptSubmit
    agent/turn_finalizer.py:454-463 post_llm_call 带 assistant_response（每轮输出后）
        = 等价 Stop

且 `doenglingz-twin` 插件已用 pre_llm_call 实跑（plugin.log「inject ok len=4124」）。

⇒ Hermes **不是**平台边界，而是**能力最强却最未被 SSOT 认知**的端：本插件把
公共注入脚本按 Hermes 特性接到真实钩子上。

## 为什么是「公共」而不是各端一份

守卫编写规范 §二·十四 接入不拥有：插件层只做适配（喂参数·取 stdout·注入），
⛔不内联任何判据。四个公共脚本各 100% 原样复用：

    route_inject_prompt.py    —— Skill 路由提示（该用哪个 Skill·强指令）
    kb_inject_prompt.py       —— 知识库确定性激活（该用哪些知识·补位）
    route_miss_feeder.py      —— 路由漏接语义召回（0 命中兜底）
    rule_fragment_inject.py   —— 规则片段按需注入

## Hermes 端专属设计（⛔ 非照搬他端）

1. **顺序契约**（对齐 SSOT 记载的分工）：先 Skill 路由 → 命中则不再注入知识；
   未命中才跑知识库 → 仍未命中跑 feeder。三段短路，避免每轮叠加噪声。
2. **短路降级**：任一段空输出 = 视同未命中，进入下一段（⛔ 不阻断对话）。
3. **⛔ 显式命令轮不注入**：载荷含 `/command-name` 时（用户明打了 Skill 调用），
   不下发路由提示——⛔ 不与作者抢方向盘（route_inject_prompt.py 自身的
   显式命令轮降级律在此做端侧兜底，不依赖脚本版本是否已带该律）。
4. **hermes 专属空转防护**：连续 N 轮全段空输出 ⇒ 写一次 WARN（防"永远注入不出"
   变成新的静默失效面·本端教训=route-audit-hook 的 `_mode` 崩点）。
5. **⛔ 零复制零他端**：⛔ 不读写 `.trae-cn` / `.workbuddy` / `.qoder-cn` 等他端目录；
   台账落 `~/.hermes/buluotuo_inject_hook.log`（端隔离）。

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只注入不裁决：注入文本是**候选提示**，⛔ 不指定"必须调用哪个"（多命中时脚本自身
  已降级为非指令候选，本插件不改写其语义）
- 失败放行：任何异常 → 返回 None，⛔ 绝不阻断对话
- 预算护栏：每段独立超时（默认 25s）+ 单段输出截断（默认 4000 字符）
  ⇒ 防注入炸掉上下文窗（Hermes 特性：注入进的是**每轮用户消息**，成本高于
  他端一次性 system prompt 注入，故护栏更紧）
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
# ── DEIDENT ────────────────────────────────────────────────
# 私人称谓已脱敏：「作者」= 系统建造经过·「用户」= 终端使用者。
# 本文件由 deident_plugins.py 生成，⛔ 请勿手改（会被下次构建覆盖）。
# ── /DEIDENT ───────────────────────────────────────────────

# ── BULUOTUO-PATH-PARAM ───────────────────────────────────────
# 布洛陀发布包·路径参数化：作者态落点（"~/<记忆中心>/…"）改为读
# runtime_paths 声明的**语义键**——键表达职责，落点由安装器填，
# 所以用户的记忆中心叫什么都行。⛔ 公共件不得含端名/作者路径。
try:
    import os as _os
    import sys as _sys
    # ⛔ 解析器落点**多路径探测**——单路径会在"装到别处"时 rp=None ⇒ 全插件 TypeError。
    #    实测：只认 `<plugins>/scripts/` 时，装在 ~/.hermes/plugins/ 下 16/16 全炸。
    for _c in (
        _os.environ.get("BULUOTUO_SCRIPTS_DIR"),
        _os.path.join(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__))), "scripts"),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__)))), "doenglingz"),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))), "doenglingz"),
    ):
        if _c and _os.path.isfile(_os.path.join(_c, "runtime_paths.py")):
            _sys.path.insert(0, _c)
            break
    from runtime_paths import rp

    def _cand(key, *parts):
        """**候选**路径：该目录不存在是正常态（回退列表里的备选）。

        ⛔ 不用 `rp(key, optional=True)`——那返回 None，
        下游 `os.path.exists(None)` 会抛 TypeError。
        ⇒ 缺键时返回**哨兵路径**（永不存在）⇒ exists() 恒 False·不崩。
        """
        try:
            return rp(key, *parts)
        except Exception:
            import os as _o2
            return _o2.path.join(_o2.path.sep, "nonexistent",
                                 "__BULUOTUO_ABSENT__:%s" % key)
except Exception:            # ⛔ 不静默：解析器不可达时留痕交守卫报
    rp = None

    def _cand(key, *parts):
        return None
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────


__version__ = "v1.0.0"

_HOME = os.path.expanduser("~")
_DEVTOOLS = rp("devtools")
_SCRIPT_CENTER = rp("script_center")
_ROUTER = os.path.join(_DEVTOOLS, "Skill路由引擎", "scripts")

_TIMEOUT = 25
_MAX_CHARS = 4000
_LOG = os.path.join(_HOME, ".hermes", "buluotuo_inject_hook.log")
_STATS = os.path.join(_HOME, ".hermes", "buluotuo_inject_stats.json")

# 空转告警阈值：连续 N 轮三段全空即写一次 WARN（正常命中时不该连续全空）
_EMPTY_STREAK_WARN = 20


def _log(msg: str) -> None:
    """端隔离留痕。⛔ 不写系统日志（那是 Skill 通道·插件不越权）。"""
    try:
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        from datetime import datetime
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _candidates(name: str) -> List[str]:
    """脚本可能在多根（历史漂移实证：route_inject_prompt 在 Skill路由引擎/scripts，
    kb_inject_prompt 在 脚本中心/）⇒ 列候选而非假定单一路径。"""
    roots = [_ROUTER, _SCRIPT_CENTER, _DEVTOOLS,
             os.path.join(_DEVTOOLS, "路由家族", "scripts"),
             # 数字分身域脚本（position3_notify 等·真身在「包内移出」目录）
             _cand("twin", "包内移出-20260929", "scripts"),
             # 知识联邦引擎脚本（record_card_trigger 在此·⚠️ 实测第一版漏了这个根
             #   ⇒ _candidates 返回空 ⇒ 该守卫「静默永不触发」·第四类契约错位同族：
            #   根没列全 = 脚本不可达 = 装了个摆设）
             _cand("kb_engine", "scripts")]
    out = []
    for r in roots:
        p = os.path.join(r, name)
        if os.path.isfile(p):
            out.append(p)
    return out


def _run(name: str, prompt: str, src: str = "hermes") -> str:
    """跑一个公共注入脚本，取 stdout 作注入文本。空/异常 → 空串（视同未命中）。"""
    for path in _candidates(name):
        try:
            proc = subprocess.run(
                [sys.executable, path, "--prompt", prompt, "--src", src],
                capture_output=True, text=True, timeout=_TIMEOUT,
                cwd=os.path.dirname(path),
            )
            text = (proc.stdout or "").strip()
            if text:
                return text[:_MAX_CHARS]
        except Exception as exc:
            _log(f"{name} fail {exc!r}")
    return ""


def _run_script(name: str) -> str:
    """跑**零输入**脚本（不读 stdin·读共享台账自身）。

    ⚠️ 契约差异第五类（2026-10-01 欠账清零轮实测）：`position3_notify.py`
    刻意**不读 stdin**（作者纪律·避免钩子阻塞对话）⇒ 既非 `--prompt` argv 型
    也非 stdin 型·而是「跑起来自己读台账」型⇒ 需第三条通道。
    ⇒ 适配层至此三通道：**`_run`（argv --prompt）/ `_run_stdin`（stdin JSON）/
    `_run_session`（stdin session_id）/ `_run_script`（零输入）**。
    """
    for path in _candidates(name):
        try:
            proc = subprocess.run(
                [sys.executable, path],
                capture_output=True, text=True, timeout=_TIMEOUT,
                cwd=os.path.dirname(path),
            )
            text = (proc.stdout or "").strip()
            if text:
                return text[:_MAX_CHARS]
        except Exception as exc:
            _log(f"{name} fail {exc!r}")
    return ""


def _run_stdin(name: str, payload: dict) -> str:
    """跑吃 stdin JSON 的注入脚本（secret_key_guard 契约·⛔ 非 argv）。

    ⚠️ 这已是本插件第三处契约差异（route_inject/kb_inject/rule_fragment 走 argv
    `--prompt`·ttl_expiry 与 secret_key 走 stdin）⇒ 适配层按脚本各自契约分通道，
    ⛔ 不假设"注入脚本都长一样"（那是照搬的典型翻车点）。
    """
    import json as _json
    for path in _candidates(name):
        try:
            proc = subprocess.run(
                [sys.executable, path],
                input=_json.dumps(payload, ensure_ascii=False),
                capture_output=True, text=True, timeout=_TIMEOUT,
                cwd=os.path.dirname(path),
            )
            text = (proc.stdout or "").strip()
            if text:
                return text[:_MAX_CHARS]
        except Exception as exc:
            _log(f"{name} fail {exc!r}")
    return ""


def _run_session(name: str, session_id: str) -> str:
    """跑吃 session_id 的注入脚本（ttl_expiry_guard 契约·⛔ 非 prompt）。

    ⚠️ 契约差异（实测 2026-10-01）：`ttl_expiry_guard.py` 从 stdin 取
    `{"session_id": ...}`·⛔ 不吃 `--prompt`；而本插件其余四段走的都是
    `--prompt` argv。⇒ 这里按 stdin 契约单独一条通道。
    """
    if not session_id:
        return ""
    import json as _json
    for path in _candidates(name):
        try:
            proc = subprocess.run(
                [sys.executable, path],
                input=_json.dumps({"session_id": session_id,
                                   "prompt": "", "payload": {}}),
                capture_output=True, text=True, timeout=_TIMEOUT,
                cwd=os.path.dirname(path),
            )
            text = (proc.stdout or "").strip()
            if text:
                return text[:_MAX_CHARS]
        except Exception as exc:
            _log(f"{name} fail {exc!r}")
    return ""


def _bump_stats(hits: List[str], empty: bool) -> None:
    """统计：三段命中分布 + 连续空转轮数（空转防护的数据源）。"""
    try:
        import json
        os.makedirs(os.path.dirname(_STATS), exist_ok=True)
        try:
            with open(_STATS, encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            d = {"turns": 0, "hits": {}, "empty_streak": 0, "warned_at_streak": 0}
        d["turns"] = d.get("turns", 0) + 1
        for h in hits:
            d["hits"][h] = d.get("hits", {}).get(h, 0) + 1
        d["empty_streak"] = 0 if not empty else d.get("empty_streak", 0) + 1
        # 空转告警：每跨过一个新阈值只告警一次（防告警疲劳·§3.5）
        s = d.get("empty_streak", 0)
        if s and s % _EMPTY_STREAK_WARN == 0 and d.get("warned_at_streak") != s:
            _log(f"WARN empty_streak={s} 连续 {s} 轮三段全空·注入通道疑似静默失效")
            d["warned_at_streak"] = s
        with open(_STATS, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _pre_llm_call(user_message: Any = "", is_first_turn: bool = False,
                  session_id: str = "", **_: Any) -> Optional[Dict[str, str]]:
    """等价 UserPromptSubmit：返回 {"context": ...} 注入本轮用户消息。

    ⛔ 任何异常 → None（无注入），绝不阻断对话。
    """
    prompt = user_message if isinstance(user_message, str) else ""
    if not prompt.strip():
        return None
    # ⛔ 显式命令轮不抢方向盘（端侧兜底·不依赖脚本版本）
    if prompt.lstrip().startswith("/") or "<command-name>" in prompt:
        return None

    hits: List[str] = []
    blocks: List[str] = []
    # ① Skill 路由（强指令·唯一命中才给）
    t = _run("route_inject_prompt.py", prompt)
    if t:
        blocks.append(t)
        hits.append("route_inject")
    # ② 知识库（补位·仅在 Skill 未命中时跑·对齐脚本哲学分工）
    if not hits:
        t = _run("kb_inject_prompt.py", prompt)
        if t:
            blocks.append(t)
            hits.append("kb_inject")
    # ③ 语义召回兜底（前两段皆空才跑）
    if not hits:
        t = _run("route_miss_feeder.py", prompt)
        if t:
            blocks.append(t)
            hits.append("miss_feeder")
    # ④ 规则片段注入（2026-10-01 接入）——**无条件段**，不参与短路。
    #    分工依据（脚本家族实例 L253）：本项是「加载时机」预注入硬墙（把易漏读的
    #    规则/纪律段提前钉进本轮上下文），⛔ 不是「召回什么」的语义检索⇒ 与①②③
    #    短路链不同质，放进短路链会让它被前段命中吃掉而永不触发。
    t = _run("rule_fragment_inject.py", prompt)
    if t:
        blocks.append(t)
        hits.append("rule_fragment")
    # ⑤ 密钥泄露提醒 + TTL 过期提醒（2026-10-01 接入·作者广授权批次）
    #    ⛔ 二者皆**无条件段**：它们是「本轮内容里有风险」的安全提醒，
    #    ⛔ 不是「召回什么知识」——放进短路链会被前段命中吃掉而永不触发。
    #    secret_key_guard 尤其关键：它是**隐私红线④**（密钥绝不外传）的机械保障，
    #    此前 Hermes 端零覆盖。脚本自身只报类型与处置建议、⛔ 不回显密钥内容。
    # ⚠️ 契约差异（实测第三次踩同族坑·2026-10-01）：`secret_key_guard.py`
    #   **只吃 stdin**（`json.load(sys.stdin)` → `payload["prompt"]`），
    #   ⛔ 不认 `--prompt` argv——传 argv 时它**静默 exit 0 无输出**
    #   ⇒ 用通用 `_run()` 会得到"永远不触发"的空转守卫。
    #   ⇒ 走 `_run_stdin()` 通道。（与 ttl_expiry 同一族契约·下条）
    t = _run_stdin("secret_key_guard.py", {"prompt": prompt, "session_id": session_id})
    if t:
        blocks.append(t)
        hits.append("secret_key")
    # ttl_expiry_guard 吃 session_id（非 prompt）·单独跑
    t = _run_session("ttl_expiry_guard.py", session_id)
    if t:
        blocks.append(t)
        hits.append("ttl_expiry")
    # ⑥ 岗位3 对账异常对话触达（2026-10-01 欠账清零轮）
    #    `position3_notify.py` — 读 steps/position3-audit-log.jsonl 末条·
    #    red>0 → 注入一行触达（超 7 天未处置升级措辞）·red=0/无台账/异常 → 静默。
    #    ⛔ **不读 stdin**（脚本作者纪律·避免钩子阻塞对话）⇒ **零注入负载**·
    #       它读的是**共享台账**（多端同一真相源）·端适配只需给执行环境。
    #    价值对齐愿景①：告警必须长到作者每天必然经过的通道——Hermes 对话就是那条通道。
    t = _run_script("position3_notify.py")
    if t:
        blocks.append(t)
        hits.append("position3")

    _bump_stats(hits, empty=not hits)
    if not blocks:
        return None
    return {"context": "\n\n".join(blocks)}


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)