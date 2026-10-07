"""布洛陀路由家族 · Hermes 会话结束标记钩子。

职责（轻量、不破坏系统提示）：
- 在 on_session_end 时，确认路由家族脚本目录可达，并写一条
  系统日志标记"路由上下文已激活"，供后续 audit 钩子对照。

说明：Hermes 用户插件的 on_session_start 在通用分发链路里无调用点
（仅 observability 内部消费），而 on_session_end 在 turn_finalizer.py
真实 invoke。故本插件挂在 on_session_end 才能真触发。
真实的"路由注入/意图分类路由"由 Skill（buluotuo-scripts）承载：
技能被加载时其 SKILL.md 指令即生效，LLM 在本轮对话中遵循路由行为。
"""

from __future__ import annotations

import os
from typing import Any
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


_CANDIDATE_DIRS = [
    _cand("custom_route", "scripts"),
    _cand("custom_route", "scripts"),
    _cand("custom_route", "scripts"),
]


def _on_session_end(session_id: str = "", **_: Any) -> None:
    if not session_id:
        return
    reachable = [d for d in _CANDIDATE_DIRS if d and os.path.isdir(d)]
    try:
        log_dir = rp("worklog")
        os.makedirs(log_dir, exist_ok=True)
        with open(
            os.path.join(log_dir, f"route_ctx_{session_id}.log"),
            "w",
            encoding="utf-8",
        ) as fh:
            fh.write(f"# 路由上下文激活 @ session {session_id}\n")
            fh.write(
                "script_dirs_reachable: "
                + (",".join(reachable) if reachable else "NONE")
                + "\n"
            )
            fh.write("note: 路由注入由 Skill buluotuo-scripts 承载\n")
    except Exception:
        pass


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
