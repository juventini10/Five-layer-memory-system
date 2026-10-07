"""布洛陀守卫家族 · Hermes 会话结束守卫调度钩子。

原生接入方式：Hermes 插件钩子 `on_session_end`。
一次会话结束后，按需运行「适合会话级巡检、失败放行」的守卫脚本，
把健康状态写回系统日志。

设计原则（来自守卫编写规范）：
- 失败放行：任何守卫异常 exit 0，绝不拦截主流程。
- 真相只 import：守卫自己内联路径/真相源，本插件不替它做判定。
- 保守判定：本插件只负责"在正确时机调用守卫"，不做语义改写。

哪些守卫放在这里（会话结束巡检形态，无参可跑）：
- amber-checkup.sh        （记忆系统辖区·双轨健康巡检，rc=0 实测可跑）

哪些守卫「不」放这里（形态不匹配，硬跑会 rc≠0 噪音）：
- changelog_guard.py      → 写入前闸门，需参数，非会话巡检
- normalize_tool.py       → 管道下游消费，依赖特定日志路径，非会话巡检
- amber-checkup.ps1       → PowerShell 脚本，macOS 无 pwsh 时跳过
# l3_conclusion：2026-09-12 作者令全端永久关闭 → 调用位已撤，⛔勿重挂
                          → 依赖 Claude Code/CodeBuddy 特定事件，Hermes 无对应，
                            改用 Skill 承载近似校验（见 buluotuo-scripts）
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any, List
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


_SEARCH_ROOTS = [
    _cand("devtools"),
    _cand("skills"),
    _cand("knowledge", "五层记忆系统"),
    rp("memory_amber", "engine"),
]

# 仅收录「会话结束巡检形态、无参可跑、失败放行」的守卫。
_GUARDS = [
    "amber-checkup.sh",
]


def _find_script(name: str) -> str | None:
    for root in _SEARCH_ROOTS:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            if name in files:
                return os.path.join(dirpath, name)
    return None


def _run_guard(path: str, log_fh) -> None:
    try:
        proc = subprocess.run(
            ["bash", path],
            cwd=os.path.dirname(path),
            capture_output=True,
            text=True,
            timeout=90,
        )
        log_fh.write(
            f"\n## {os.path.basename(path)} (rc={proc.returncode})\n"
            f"{proc.stdout[-400:]}\n{proc.stderr[-200:]}\n"
        )
    except Exception as exc:
        log_fh.write(f"\n## {os.path.basename(path)} ERROR: {exc!r}\n")


def _on_session_end(session_id: str = "", **_: Any) -> None:
    if not session_id:
        return
    found = [(g, _find_script(g)) for g in _GUARDS]
    found = [(g, p) for g, p in found if p]
    if not found:
        return
    log_dir = rp("worklog")
    os.makedirs(log_dir, exist_ok=True)
    out_path = os.path.join(log_dir, f"guards_{session_id}.log")
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(f"# 守卫调度 @ session {session_id}\n")
            fh.write(f"guards_run: {', '.join(g for g, _ in found)}\n")
            for _name, path in found:
                _run_guard(path, fh)
    except Exception:
        pass


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
