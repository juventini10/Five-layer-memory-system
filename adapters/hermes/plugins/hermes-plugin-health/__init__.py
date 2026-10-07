"""Hermes 端专属配置/健康守卫 · 承载插件（on_session_end）。

## 为什么 Hermes 端需要这个（元守卫·第一性原理）

布洛陀三大家族的守卫都守「业务真相」，但 Hermes 端多了一个**其他端没有的失效面**：
插件层。每个布洛陀插件是一整段 Python，`config.yaml plugins.enabled` 只证明
「注册了」，⛔不证明「在跑」「没崩」「跑的是预期那件」。

2026-10-01 实锤的教科书案例（守卫规范 §3.5 崩点静默 · §3.9c）：

    route-audit-hook/__init__.py 末尾残留一段 `_mode`/`_label` 未定义的 try 块
    （2026-09-12 撤 l3_conclusion 调用位时只删了 for 头、留下整个循环体）。

    运行时链：每轮 on_session_end → NameError(_mode) → except 分支自身又引用
    `_mode` → 第二个 NameError → 被内层 `except Exception: pass` 吞掉。

    ⇒ 守卫**从未执行、零留痕、无告警**。而它逃过了全部既有闸门：
      · py_compile 通过（语法合法，未定义名是运行期错误）
      · 平台 hooks 自检通过（注册态正常）
      · platform_adaptation_check --src hermes 通过（只读 config.yaml 不读代码）

    本插件承载的守卫就是补这个面：**AST 静态扫未定义名**（不执行代码即可抓）。

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：报告制，恒 exit 0
- 失败放行：任何异常 → exit 0，⛔绝不阻断会话
- 保守判定：只查机械可判项（配置/声明/注册/静态名），⛔不做语义评价
- 端隔离：台账落 ~/.hermes/（插件自己写），⛔不写他端目录
- 零复制：只 subprocess 调 `开发工具/hermes_plugin_health_guard.py`（公共脚本），
  ⛔不内联任何判据（真相所有权：判据在脚本本体，插件只做"接入不拥有"）

## 边界（诚实声明·防夸大）

守卫报 ✅ 只证明「配置/声明/注册/静态名四层自洽」，⛔不证明「内核真的派发了这个
hook」——Hermes 无逐事件派发回执通道（无 hook_protocol 等价物），运行态仍是
advisory 层。此边界与守卫规范 §3.4 宿主收讫律同源：不把「注册态」当「运行态」。
"""

from __future__ import annotations

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
GUARD = rp("devtools", "hermes_plugin_health_guard.py")

_LOG_DIR = os.path.join(_HOME, ".hermes")
_TIMEOUT = 30


def _log(msg: str) -> None:
    """插件自留痕（端中立目录）。⛔不写系统日志（那是 Skill 通道的事，插件不越权）。"""
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        from datetime import datetime
        with open(os.path.join(_LOG_DIR, "hermes_plugin_health_hook.log"), "a",
                  encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _on_session_end(session_id: str = "", **_: Any) -> None:
    """跑端专属健康守卫。失败放行、恒不阻断。"""
    if not os.path.isfile(GUARD):
        _log("guard missing")
        return
    try:
        proc = subprocess.run(
            [sys.executable, GUARD, "--check", "--json"],
            capture_output=True, text=True, timeout=_TIMEOUT,
        )
        red = warn = 0
        # JSON 计数由守卫机械产出，插件只取数回显（⛔不自解析判定）
        out = proc.stdout or ""
        if '"red"' in out and '"warn"' in out:
            for line in out.splitlines():
                s = line.strip().strip(",")
                if s.startswith('"red"'):
                    red = int(s.split(":")[-1])
                elif s.startswith('"warn"'):
                    warn = int(s.split(":")[-1])
        # 只有 RED 才留痕（WARN 常态·每轮写盘=噪声，按 §3.5 告警疲劳纪律过滤）
        if red:
            _log(f"RED={red} WARN={warn} session={session_id}")
    except Exception as exc:
        _log(f"fail {exc!r}")


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
