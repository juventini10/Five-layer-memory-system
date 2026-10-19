"""布洛陀 TSL 三件套 · Hermes 端承载（作者 2026-10-02 授权接入）。

## TSL 是什么（先说清功能·作者问「它有什么功能」）

**TSL = 会话级 L0-L7 执行验证清单**——回答「这回合我到底做没做、凭什么说做了」。

三件套的分工（**产出与呈现都不经 AI 意志**·这是它设计的核心）：

| 件 | 通道 | 做什么 | 为什么需要它 |
|:--|:--|:--|:--|
| `tsl_tree_hook.py` | **post_llm_call**（每轮·等价 Stop） | 读 stamps.log 尾行取窗口 → 跑 `tsl_verify.py --since <锚> --full` → **树写文件** | 把 TSL 从「AI 手动跑」变成「机制机械产」——AI 只剩 relay 义务 |
| `tsl_echo_hook.py` | **pre_llm_call**（每轮·等价 UPS） | 读树·未消费则**注入** `additionalContext` → AI 被迫逐行 relay → 写 `.consumed`（同 stamp 只注入一次） | **闭环末环**：产出（Stop）与呈现（UPS）都不经 AI 意志 ⇒ AI 无法「不跑就说跑了」 |
| `tsl_closeout_guard.py` | post_llm_call | 校验「说了要 TSL 树 ⇒ 是否真跑了 tsl_verify」 | 反向校验层：手绘状态行/自填 ✅ 会被留痕 |

## ⛔ 门控（为什么本端装上不会每轮产树）

`tsl_tree_hook` v1.2 内置**档位门控** `session_d_tier(sid)`：**TSL 树义务仅 D3**
（童灵 08 §七·与注入侧同源）。非 D3 回合 ⛔ **不产文件**——
这是 2026-09-30 作者质证「我没启动 D3 怎么还有 TSL」的机制级根治：
把「AI 不该 relay」从**判据**（事后报警·靠自觉）升级为**物理不可达**（文件不存在）。

⚠️ 门控数据源要求：注入台账的 `session_id` 必须真落。
**本端此前 session_id 恒空**（插件走 argv `--prompt` ⇒ 注入器 `_PAYLOAD={}`）
⇒ 门控退化为「全局最新行」= 跨会话串台。
⇒ 本轮已改 `doenglingz-twin` 插件走 **stdin 载荷**（带 session_id）·端适配层解决·
⛔ 未改公共注入器本体（守卫规范 §二·十四 接入不拥有）。

## 端隔离（⛔ 不写他端）

`TSL_TREE_OUT` / `TSL_INJECT_STATE` 两个 env（**ZCode 端 v1.2 已开的先例**）：
- 树槽 → `~/.hermes/doenglingz/tsl_last_tree.md`（⛔ 不写 `~/.workbuddy/tsl_last_tree.md`）
- 台账 → `~/.hermes/doenglingz/doenglingz_inject_state.json`（与注入器同根）
- `.consumed` 标记随树同目录（脚本按 `TREE + ".consumed"` 推导）

## 纪律（守卫编写规范 §八）

- 只记录不拦截：⛔ 恒返回 None·不改写模型输出·不阻断
- 失败放行：任何异常 → 静默 return（树是审计产物·缺树不该锁死对话）
- 端隔离：⛔ 全部落 `~/.hermes/doenglingz/`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional
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


__version__ = "v1.0.0"

_HOME = os.path.expanduser("~")
_DEVTOOLS = rp("devtools")
_ROOT = os.path.join(_HOME, ".hermes", "doenglingz")
_TREE = os.path.join(_ROOT, "tsl_last_tree.md")
_STATE = os.path.join(_ROOT, "doenglingz_inject_state.json")
_LOG = os.path.join(_HOME, ".hermes", "tsl_hook.log")

_TREE_HOOK = os.path.join(_DEVTOOLS, "tsl_tree_hook.py")
_ECHO_HOOK = os.path.join(_DEVTOOLS, "tsl_echo_hook.py")

_TIMEOUT = 60


def _env() -> Dict[str, str]:
    env = dict(os.environ)
    env["TSL_TREE_OUT"] = _TREE
    env["TSL_INJECT_STATE"] = _STATE
    # ── 2026-10-02 断线一根治（本端唯一缺失的 env·对齐 doenglingz-twin L83-86 同款形态）──
    # 病根：tsl_verify.py L22 读 WORKBUDDY_CONFIG_DIR（回落 ~/.workbuddy）判 L3「上岗仪式」，
    #   本插件这条链未设该变量 ⇒ L3 判据读的是 WorkBuddy 端台账，本端 50 次档位声明一条不取，
    #   L3 层长期替别端打分（实测 2026-10-02：~/.workbuddy 今日 14 行，Hermes 格式 session_id 命中 0）。
    # 修法：端适配层设本端配置根（与 doenglingz-twin._ENV 同款），⛔ 共脚本本体零改动（端中立判据）。
    # 两个 env 键都设的原因：doenglingz_inject_prompt.py 读 DOENGLINGZ_CONFIG_DIR 优先、
    #   doenglingz_guard.py / tsl_verify.py 只认 WORKBUDDY_CONFIG_DIR（插件注释 L74-77 实测记录）。
    env["DOENGLINGZ_CONFIG_DIR"] = _ROOT
    env["WORKBUDDY_CONFIG_DIR"] = _ROOT
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _pre_llm_call(user_message: Any = "", session_id: str = "",
                  **_: Any) -> Optional[Dict[str, str]]:
    """等价 UserPromptSubmit：读树·未消费则注入。"""
    if not os.path.isfile(_TREE) or not os.path.isfile(_ECHO_HOOK):
        return None                      # 无树（正确状态·非 D3 或未产）⇒ 不注入
    try:
        proc = subprocess.run(
            [sys.executable, _ECHO_HOOK],
            input=json.dumps({"session_id": str(session_id or ""),
                              "prompt": user_message if isinstance(user_message, str) else ""},
                             ensure_ascii=False),
            capture_output=True, text=True, timeout=_TIMEOUT, env=_env(),
        )
        out = (proc.stdout or "").strip()
        if not out:
            return None                  # 已消费过 / 门控非 D3 ⇒ 静默
        return {"context": out}
    except Exception as exc:
        _log(f"echo fail {exc!r}")
        return None


def _post_llm_call(session_id: str = "", **_: Any) -> None:
    """等价 Stop：机械产树。⛔ 恒 None·失败放行。"""
    if not os.path.isfile(_TREE_HOOK):
        return
    try:
        proc = subprocess.run(
            [sys.executable, _TREE_HOOK],
            input=json.dumps({"session_id": str(session_id or ""),
                              "prompt": "", "response": ""}, ensure_ascii=False),
            capture_output=True, text=True, timeout=_TIMEOUT, env=_env(),
        )
        born = os.path.isfile(_TREE)       # 树文件是否真产（gate 判据·不靠 stdout 猜）
        _log(f"tree rc={proc.returncode} born={born} "
             f"{(proc.stdout or proc.stderr or '')[:140]}")
    except Exception as exc:
        _log(f"tree fail {exc!r}")


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)