"""布洛陀 Skill 生态健康守卫 · Hermes 端承载（on_session_end）。

判据全在公共脚本 `开发工具/hermes_skill_health_guard.py`（⛔ 零内联·接入不拥有）。
本插件只做「跑 + 把 RED 留痕」，⛔ 恒 exit 0（报告制·Hook 三纪律）。
台账端隔离落 ~/.hermes/（⛔ 不写他端）。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
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


__version__ = "v1.0.0"

_HOME = os.path.expanduser("~")
_GUARD = rp("devtools", "hermes_skill_health_guard.py")
_LOG = os.path.join(_HOME, ".hermes", "skill_health_hook.log")
_TIMEOUT = 30


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _on_session_end(session_id: str = "", **_: Any) -> None:
    """跑 Skill 健康守卫。⛔ 失败放行·恒不阻断。"""
    if not os.path.isfile(_GUARD):
        return
    try:
        proc = subprocess.run(
            [sys.executable, _GUARD, "--json"],
            capture_output=True, text=True, timeout=_TIMEOUT,
        )
        rep = json.loads(proc.stdout or "{}")
        # 只记 RED（WARN 常态·每轮写盘=噪声·守卫规范 §3.5 告警疲劳纪律）
        red = int(rep.get("red", 0) or 0)
        if red:
            kinds = [f.get("kind") for f in rep.get("findings", [])
                     if f.get("level") == "RED"]
            _log(f"RED={red} kinds={kinds} total={rep.get('total')}")
    except Exception as exc:
        _log(f"fail {exc!r}")


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
