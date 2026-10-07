"""布洛陀 Stop 守卫 · Hermes 端适配（post_llm_call 通道）。

## 存在理由（补一个被 SSOT 虚报的缺口）

脚本哲学 SSOT 的 Hermes 列在 `route_unknown_unknown.py（Stop）` 记「✅ 2026-08-20
实装·on_session_end 插件 route-audit-hook 调用·真机验证日志落盘」。

**2026-10-01 全机 grep 实测：该断言不成立**——

    grep -rl route_unknown_unknown ~/.hermes/ <记忆中心>/开发工具/
        <记忆中心>/脚本中心/ <记忆中心>/记忆蓝图/
    → 零接入点（排除归档/发布库/记忆琥珀后为空）

脚本真身在 `脚本中心/route_unknown_unknown.py`，但 Hermes 端从未有代码调它。
SSOT 那条 ✅ 属**文档虚报**（守卫规范 §3.5 假绿 + platform_adaptation_check
「文档≠事实」反查要抓的那一类）。

## 为什么用 post_llm_call 而不是 on_session_end（Hermes 端特性·非照搬）

| 候选通道 | Hermes 实况 | 取舍 |
|:--|:--|:--|
| `on_session_end` | 真实派发（turn_finalizer.py）但**会话级**（一天一次） | ⚠️ 晚于 Stop 语义：WorkBuddy 的 Stop 是**每轮**主代理结束时 |
| `post_llm_call` | 真实派发（turn_finalizer.py:454-463）带 `assistant_response` | ✅ **每轮** LLM 输出后 = Stop 的等价语义，取用 |

⇒ 本守卫按**每轮**触发，与他端 Stop 口径对齐。这是「按自身系统特性实现」的
具体落点，而非把 WorkBuddy 的 hooks.json 抄过来。

## 契约适配（接入层收口·⛔ 不动脚本本体）

    route_unknown_unknown.py 契约：从 stdin 读 {"transcript_path": "..."}
    Hermes 实况：无 transcript 文件，消息在 state.db
    ⇒ 借 `_hermes_transcript_adapter.export_transcript(session_id)` 走同一条
      已实测打通的 db→jsonl 路径（route_audit.py 复用同法·2026-10-01 实证）

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：⛔ 返回 None，绝不改写模型输出，绝不阻断
- 失败放行：任何异常 → 静默 return
- 保守判定：判据全在公共脚本本体，插件零内联
- ⛔ 端隔离：台账落 `~/.hermes/`，⛔不写他端目录
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Optional
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
_SCRIPT_CENTER = rp("script_center")
# ⚠️ 原为 os.path.join(_HOME, "<记忆中心>", …) 的多行形态——⛔ 批量正则漏了
#    「尾随逗号 + 续行」这种形态（台账 §3.1 的同类）。手改，不调正则。
_ADAPTER = rp("kb_engine", "scripts", "_hermes_transcript_adapter.py")
_LOG = os.path.join(_HOME, ".hermes", "buluotuo_stop_hook.log")

_TIMEOUT = 30
_SRC = "hermes"


def _log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        from datetime import datetime
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _guard_path() -> Optional[str]:
    p = os.path.join(_SCRIPT_CENTER, "route_unknown_unknown.py")
    return p if os.path.isfile(p) else None


def _post_llm_call(assistant_response: Any = "", session_id: str = "", **_: Any) -> None:
    """等价 Stop：每轮 LLM 输出后跑未知未知检测。⛔ 只记录不拦截·恒返回 None。"""
    text = assistant_response if isinstance(assistant_response, str) else ""
    if not text.strip():
        return
    guard = _guard_path()
    if guard is None or not os.path.isfile(_ADAPTER):
        return
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("_hermes_tx_adapter", _ADAPTER)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tx = mod.export_transcript(session_id) if session_id else None
        if not tx:
            return                      # 无 transcript ⇒ 不跑（不假红）
        proc = subprocess.run(
            [sys.executable, guard, "--src", _SRC],
            input=json.dumps({"transcript_path": tx}),
            capture_output=True, text=True, timeout=_TIMEOUT,
            cwd=os.path.dirname(guard),
        )
        # 有实质产出才留痕（降噪：守卫常态静默·守卫规范 §3.5 告警疲劳纪律）
        if proc.stdout and proc.stdout.strip():
            _log(f"rc={proc.returncode} out={proc.stdout.strip()[:200]}")
    except Exception as exc:
        _log(f"fail {exc!r}")


def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _post_llm_call)