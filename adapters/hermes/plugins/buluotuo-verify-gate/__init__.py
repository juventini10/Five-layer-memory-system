"""buluotuo-verify-gate —— 改码后验证闸（Hermes 端适配 · pre_verify 通道）

## 为什么是 pre_verify（官方机制取证·不是拍脑袋）

官方 `VALID_HOOKS`（`hermes_cli/plugins.py:119`）含 `pre_verify`，语义逐字：

    pre_verify: once per turn when the agent edited code and is about to verify/finish.
    Return `{"action": "continue", "message"}` (or Claude-Code Stop
    `{"decision": "block", "reason"}`) to keep going; anything else finishes.
    Bounded by `agent.max_verify_nudges`.

触发点在 `agent/turn_stop_gates.py:52 _pre_verify_nudge()`，三道门全过才问插件：

    if _edited and has_hook("pre_verify") and attempt < max_verify_nudges():

`agent/turn_stop_gates.py:5` 的模块 docstring 直书这是**停止门**（stop gate）——
即「agent 想收工的那一刻」。这是全事件面**唯一一个专门为「别急着说完」设计的官方通道**。

**对账实锤（2026-10-03）**：`grep -rln pre_verify ~/.hermes/plugins/` → **零命中**。
⇒ 本端 16 个插件**没有一个占这个位**，而这个位恰好治本端当天最贵的错：
「改完就宣布完成，没实跑就说完成」（HE-007/008/010 族）。

## 本插件做什么（⛔ 零判据内联）

判据全在 `hermes_verify_gate.py`（脚本本体）。本插件只做三件适配：

1. 从 `rp("devtools")` 取脚本（与 `buluotuo-pretool-guards` 同一取件面·⛔ 不引第二根）
2. 把官方 kwargs（`coding`/`attempt`/`changed_paths`/`final_response`/`session_id`/`platform`）
   序列化成脚本的 stdin JSON 契约
3. 读退出码 → 转 `{"action":"continue","message":...}` 或 `None`

## 通道纪律（守卫编写规范 §八 Hook 三纪律）

- **fail-open**：脚本缺失/超时/异常 → **一律放行**（守卫失灵不该锁死用户的活干）
- **有界**：官方 `max_verify_nudges` 已封顶；本插件**不自行节流**（⛔ 不造第二套上限）
- **保守**：只信脚本 exit 码，⛔ 不自己判断「这次算不算完成」
- **端隔离**：只读 `~/.hermes/` 与 `rp("devtools")`，⛔ 不写他端

## 为什么不用 shell hook 面

`~/.hermes/config.yaml` 的 shell hook 注册发生在**进程启动时**
（`agent/shell_hooks.py register_from_config()` → `manager._hooks`，幂等集 `_registered`），
改配置须重启 Hermes 才生效；且本端 shell hook 面只挂 `skill_view` 一条，
若为 verify_gate 单开一条 ⇒ **两个通道做同一件事 = 双层顶账**（守卫规范 §二·十四「接入不拥有」的反面）。

插件面则由 `mount_plugins.py` 幂等挂载 + `discover_and_load(force=True)` 热重载，
**不必重启**。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional

__BULUOTUO_ABSENT__ = "buluotuo-verify-gate"

_VERSION = "v1.0.0"
_TIMEOUT = 20                       # 与 pretool-guards 同档（官方 pre_tool_call fail-closed 语义不同）
_SCRIPT = "hermes_verify_gate.py"
_LOG = os.path.expanduser("~/.hermes/verify_gate_hook.log")
# ⛔ 官方事件名（desktop 端真名）：pre_verify ∈ VALID_HOOKS（plugins.py:119）
#    勿写成 PreVerify/PreVerifyUse —— 不在表内 ⇒ 注册静默失败


# ── BULUOTUO-PATH-PARAM ───────────────────────────────────────
# 取件面：与 bulutuo-pretool-guards **同一根**（⛔ 不引第二个取件面）。
# ⚠️ 多路径探测是实测踩出的硬要求：解析器落点随安装形态变
#    （`~/.hermes/scripts/` vs `~/.hermes/doenglingz/`），
#    单路径写在另一种装法下 ⇒ rp 不可调用 ⇒ 插件整个炸（plugin_live_gate G2 拦）。
# ⚠️ **模块级导出 `rp`**：plugin_live_gate.py 的 G2 关用
#    `callable(getattr(module,'rp',None))` 实导校验 ⇒ 只在函数里 import 会被判「不可调用」。
try:
    for _c in (
        os.environ.get("BULUOTUO_SCRIPTS_DIR"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "doenglingz"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))), "doenglingz"),
    ):
        if _c and os.path.isfile(os.path.join(_c, "runtime_paths.py")):
            if _c not in sys.path:
                sys.path.insert(0, _c)
            break
    from runtime_paths import rp          # ⛔ 模块级·G2 实导校验要它可调用
except Exception:                          # ⛔ 解析器不可用 ⇒ 下面一律 fail-open
    rp = None                              # type: ignore[assignment]


def _devtools() -> Optional[str]:
    """插件唯一取件面（⛔ 解析器缺席 ⇒ None ⇒ 调用方 fail-open 放行）。"""
    if rp is None:
        _log("ABSENT rp 不可调用（解析器未载入）⇒ 放行（fail-open）")
        return None
    try:
        return rp("devtools")
    except Exception as e:
        _log("ABSENT rp('devtools') 异常 %r ⇒ 放行（fail-open）" % e)
        return None


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def _pre_verify(session_id: str = "", platform: str = "", model: str = "",
                coding: bool = False, attempt: int = 0,
                final_response: str = "", changed_paths: Optional[List[str]] = None,
                **_: Any) -> Optional[Dict[str, str]]:
    """pre_verify 回调：脚本判定「这次交付没实证」⇒ 让 agent 继续干，别收工。

    ⛔ 返回 None = 放行（本回合照常结束）。
    ✅ 返回 `{"action": "continue", "message": ...}` = 让这一轮继续。
    """
    paths = list(changed_paths or [])
    # 官方三道门已保证 _edited 非空；此处再挡一层是防御（⛔ 不信上游的空 changed_paths）
    if not paths:
        return None
    root = _devtools()
    if not root:
        _log("ABSENT 无 rp('devtools') ⇒ 放行（fail-open）")
        return None
    script = os.path.join(root, _SCRIPT)
    if not os.path.isfile(script):
        _log("ABSENT %s 不存在 ⇒ 放行（fail-open·脚本未部署）" % _SCRIPT)
        return None
    payload = {
        "toolName": "Verify", "input": {},          # 脚本若沿用写侧守卫的 tool 分派
        "session_id": session_id, "platform": platform, "model": model,
        "coding": bool(coding), "attempt": int(attempt or 0),
        "final_response": final_response or "",
        "changed_paths": paths,
    }
    try:
        proc = subprocess.run(
            ["python3", script], input=json.dumps(payload, ensure_ascii=False),
            capture_output=True, text=True, timeout=_TIMEOUT, cwd=root,
        )
    except subprocess.TimeoutExpired:
        _log("TIMEOUT >%ds ⇒ 放行（fail-open）" % _TIMEOUT)
        return None
    except Exception as e:                          # ⛔ 脚本自身异常不该锁死用户
        _log("EXC %r ⇒ 放行（fail-open）" % e)
        return None
    out = (proc.stdout or "").strip() or (proc.stderr or "").strip()
    if proc.returncode == 0:
        return None
    _log("NUDGE attempt=%s changed=%d by %s" % (attempt, len(paths), _SCRIPT))
    return {"action": "continue",
            "message": "[%s] %s" % (_SCRIPT, out[:800] if out else "验证闸判定未过（脚本 exit %d）" % proc.returncode)}


def register(ctx) -> None:
    ctx.register_hook("pre_verify", _pre_verify)