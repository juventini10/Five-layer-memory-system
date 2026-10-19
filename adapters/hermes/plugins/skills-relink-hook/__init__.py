"""技能软链接自愈钩子 · Hermes 会话结束自动修复。

原生接入方式：Hermes 插件钩子 `on_session_end`。
一次会话结束后，运行 skills_relink.py 自愈器，修复 ~/.hermes/skills/ 下
因 /tmp 清理、系统重启等导致断裂的技能软链接（如 clock-loop），
保证斜杠菜单里的技能永不因断链消失。

设计原则（对齐 guard-scheduler-hook 范式）：
- 失败放行：自愈器异常 exit 0，绝不拦截主流程。
- 幂等：重复跑结果一致，不会制造第二份真身、不会误删资产。
- 无参可跑：skills_relink.py 默认形态即自愈，rc=0（无 error 时）。
"""

from __future__ import annotations

import os
import subprocess
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
except Exception as _rp_exc:   # ⛔ 解析器不可用 = 安装不完整·必须显形（2026-10-09 根治）
    # 此前 rp=None 会让下游模块级 rp(...) 报 'NoneType' object is not callable
    # ——完全不指向根因（session-title hook 失效排查的教训）。改为明确抛错。
    raise RuntimeError(
        "布洛陀运行路径解析器（runtime_paths）不可用：%s: %s\n"
        "  ⇒ 运行路径声明（runtime_paths.json）缺失/损坏，或解析器不在探测路径。\n"
        "     修复：运行安装器重新生成，或确认 doenglingz/runtime_paths.{py,json} 就位。\n"
        "  ⛔ 不回落 rp=None——否则下游只报 NoneType（不指向根因·排查成本极高）。"
        % (type(_rp_exc).__name__, _rp_exc)
    ) from _rp_exc
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────


# 自愈器绝对路径（不依赖 walk，避免 _SEARCH_ROOTS 漂移）
_RELINK = rp("devtools", "skills_relink.py")


def _on_session_end(session_id: str = "", **_: Any) -> None:
    if not session_id:
        return
    if not os.path.isfile(_RELINK):
        return
    log_dir = rp("worklog")
    os.makedirs(log_dir, exist_ok=True)
    out_path = os.path.join(log_dir, f"skills_relink_{session_id}.log")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(f"# 技能软链接自愈 @ session {session_id}\n")
            try:
                proc = subprocess.run(
                    ["python3", _RELINK],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                fh.write(
                    f"rc={proc.returncode}\n"
                    f"{proc.stdout[-600:]}\n{proc.stderr[-200:]}\n"
                )
            except Exception as exc:
                fh.write(f"ERROR: {exc!r}\n")
    except Exception:
        pass


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
