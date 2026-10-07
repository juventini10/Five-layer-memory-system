"""布洛陀发布包链路守卫 · Hermes pre_tool_call 窄匹配拦截钩子。

原生接入方式：Hermes 插件钩子 `pre_tool_call`。
当 LLM 即将写入「发布包相关路径」时，先跑发布包链路守卫：
- content-gate.py   （内容门禁：遗留样例数据/真实感数据外泄拦截，rc=1 拒绝）
- sync_guard.py     （一致性：manifest 为基准，漂移 rc=1）

设计原则（来自守卫编写规范 + 第一性原理）：
- 窄匹配：仅当 write_file/patch 的目标路径落在发布包目录才拦截，
  普通写文件（记忆日志/对话产出）完全不触发 —— 避免误伤、避免每次写都扫包。
- 失败放行：守卫脚本异常/缺失时放行（绝不因守卫故障卡死主流程）。
- 真相只 import：守卫自己内联特征库/Manifest 路径，本插件不替它判定。

注意：pre_tool_call 回调可拿到 tool_name 与 args（disk-cleanup 官方插件实证
签名具名默认参数）。本插件在回调里读 args["path"] / args["old_string"] 所在文件，
命中发布包目录才执行守卫。
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Optional
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
        """**候选**路径：目录不存在是正常态（回退列表的备选）。
        ⛔ 不用 optional=True（返 None 会让 os.path.exists(None) 抛 TypeError）
        ⇒ 缺键返**哨兵路径**：exists() 恒 False·不崩。"""
        try:
            return rp(key, *parts)
        except Exception:
            import os as _o2
            return _o2.path.join(_o2.path.sep, "nonexistent",
                                 "__BULUOTUO_ABSENT__:%s" % key)
except Exception:
    rp = None

    def _cand(key, *parts):
        return None
except Exception:            # ⛔ 不静默：解析器不可达时留痕交守卫报
    rp = None
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────


# 发布包相关目录（窄匹配命中才拦截）。用 expanduser 兼容 ~。
_PACKAGE_DIRS = [
    _cand("knowledge", "五层记忆系统", "布洛陀-安装包"),
    _cand("devtools", "buluotuo-release-sync"),
    _cand("skills"),
]

_CONTENT_GATE = rp("devtools", "buluotuo-release-sync", "content-gate.py")
_SYNC_GUARD = rp("devtools", "skill-sync-guard", "sync_guard.py")


def _target_path(args: Optional[dict]) -> Optional[str]:
    if not isinstance(args, dict):
        return None
    # write_file: args["path"]；patch: args["path"]
    p = args.get("path")
    return p if isinstance(p, str) and p else None


def _in_package_dir(path: str) -> bool:
    ap = os.path.abspath(path)
    return any(ap.startswith(os.path.abspath(d)) for d in _PACKAGE_DIRS if d)


def _resolve_pkg_dir(path: str) -> Optional[str]:
    """解析 content-gate 的 --package 目录。

    content-gate 要求 --package 是已存在的目录（is_dir 校验，否则 exit 2）。
    首次写全新文件时 os.path.dirname(path) 可能尚不存在 —— 向上回溯到
    _PACKAGE_DIRS 内最深的已存在目录；都找不到则回退首个包根（避免误拦）。
    """
    ap = os.path.abspath(path)
    cur = os.path.dirname(ap)
    # 向上回溯，直到落在某个 _PACKAGE_DIRS 内且目录存在
    for d in _PACKAGE_DIRS:
        ad = os.path.abspath(d)
        if ap.startswith(ad) or cur.startswith(ad):
            # 从 cur 向上找第一个存在的目录
            probe = cur
            while probe and not os.path.isdir(probe):
                parent = os.path.dirname(probe)
                if parent == probe:
                    break
                probe = parent
            if os.path.isdir(probe):
                return probe
    # 兜底：首个包根（必存在）
    for d in _PACKAGE_DIRS:
        if os.path.isdir(d):
            return d
    return None


def _run_guard(script: str, label: str, package_dir: Optional[str] = None, file_path: Optional[str] = None, content: Optional[str] = None) -> Optional[dict]:
    """跑守卫，返回 None=放行，返回 dict(action=block,...)=拒绝（Hermes pre_tool_call 契约）。

    Hermes pre_tool_call 的阻断契约（实证自官方 security-guidance 插件）：
    回调返回 {"action": "block", "message": ...} 字典即拒绝工具调用；
    返回 None 视为放行。

    file_path: content-gate --file 单文件模式（扫磁盘现有文件）。
    content:   content-gate --content 待写内容模式（扫 write_file 的 content 参数，
              能拦新建文件将要写的内容，是 pre_tool_call 拦新文件的正确姿势）。
    """
    cmd = ["python3", script]
    if content is not None:
        cmd += ["--content", content]
        if file_path:
            cmd += ["--file", file_path]
    elif file_path:
        cmd += ["--file", file_path]
    elif package_dir:
        cmd += ["--package", package_dir]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            reason = proc.stdout.strip()[-300:] or proc.stderr.strip()[-300:]
            return {
                "action": "block",
                "message": f"{label} 拦截发布包写入：{reason}\n（如需绕过，先清理遗留样例数据/同步漂移后重试）",
            }
    except Exception:
        # 守卫异常 → 放行（失败放行原则）
        return None
    return None


def _on_pre_tool_call(
    tool_name: str = "",
    args: Optional[dict] = None,
    **_: Any,
) -> Optional[dict]:
    """pre_tool_call 回调：窄匹配发布包写入，跑内容门禁 + 一致性守卫。

    返回 dict(action=block) = 拒绝；返回 None = 放行。
    """
    if tool_name not in ("write_file", "patch"):
        return None
    path = _target_path(args)
    if not path or not _in_package_dir(path):
        return None
    # 内容门禁（发布包外泄拦截）——硬门禁，命中即阻断
    if os.path.isfile(_CONTENT_GATE):
        # 优先扫"待写内容"（write_file 的 content 参数）——能拦新建文件将要写的内容；
        # 无 content（如 patch 模式）时回退扫磁盘现有文件（--file）。
        content = (args or {}).get("content") if isinstance(args, dict) else None
        if content:
            block = _run_guard(_CONTENT_GATE, "content-gate",
                               file_path=path, content=content)
        else:
            block = _run_guard(_CONTENT_GATE, "content-gate", file_path=path)
        if block:
            _log_block(block["message"])
            return block  # 真阻断：返回 block 字典，框架拒绝本次工具调用
    # 一致性守卫（manifest 漂移）——sync_guard 设计为审计非硬门禁，仅跑不阻断
    if os.path.isfile(_SYNC_GUARD):
        _run_guard(_SYNC_GUARD, "sync_guard")
    return None


def _log_block(reason: str) -> None:
    try:
        log_dir = rp("worklog")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "release_guard_blocks.log"), "a", encoding="utf-8") as fh:
            from datetime import datetime
            fh.write(f"[{datetime.now().isoformat()}] {reason}\n")
    except Exception:
        pass


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
