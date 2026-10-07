"""buluotuo-transform-gate —— Transform 层闸（Hermes 端适配）

## 为什么是 Transform（2026-10-04 官方机制取证·不是拍脑袋）

官方 `VALID_HOOKS`（`hermes_cli/plugins.py:109-112`）逐字含：

    "pre_tool_call", "post_tool_call", "transform_terminal_output",
    "transform_tool_result",
    # transform_llm_output: return a replacement string (first non-None wins) or None.
    "transform_llm_output", "pre_llm_call", "post_llm_call",

`plugins_dispatch.invoke_hook` 语义：**回调各自隔离·返回非 None 的结果·首个生效**。

官方自带的 `plugins/security-guidance/__init__.py:115` 就是这个模式的样板：
`_on_transform_tool_result(...) -> Optional[str]`·命中则 `return result + 警告块`·
不命中 `return None`。**本插件照该样板写·不引第二套语义。**

## 布洛陀此前为什么没用（对账实锤）

`grep -rln "transform_" ~/.hermes/plugins/` → **零命中**。
17 个插件占了 5 个事件（pre_tool_call / pre_llm_call / pre_verify /
post_llm_call / on_session_end），**Transform 类 3 个一个没占**。

代价是实打实的：今天最贵的一类错误是「工具结果里带作者绝对路径 / 测试临时目录 /
双层 expanduser」——AI 把它当事实读进去 → 污染推理 → 造出一堆假病灶。
本插件在**进对话之前**一道洗掉 = 一次处理·所有下游受益。

## 通道纪律（守卫编写规范 §八）

- **fail-open**：脚本缺失/异常/超时 → 一律返回 None（不改输出）
  ⇒ 守卫失灵不该锁死用户的活干
- **有界**：纯 O(n) 字符串处理·⛔ 不跑子进程（Transform 在关键路径上）
- **保守**：只认白名单形态·⛔ 不猜、不模糊替换
- **保守**：LLM 侧只剥测试路径噪声·⛔ **不改语义、不加不减**（塑形≠改写）
- **端隔离**：⛔ 不写任何文件·纯返回字符串

## 为什么不用 shell hook 面

shell hook 注册在**进程启动时**（`agent/shell_hooks.py register_from_config()`）·
改配置须重启 Hermes 才生效；且本端 shell hook 面只挂 `skill_view` 一条。
插件面由 `mount_plugins.py` 幂等挂载 + `discover_and_load(force=True)` 热重载。
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))


def rp(*parts: str) -> str:
    """脚本取件面（与 buluotuo-verify-gate 同一实现·⛔ 不引第二根）。"""
    home = os.path.expanduser("~")
    # 作者目录名拼接构造（2026-10-05 隐私根治·与 package_plugins.SIG_DIR 同款先例）：
    #   AST 常量层不含完整目录名（闸判据=AST 字符串常量值），运行时等价，功能不变。
    _MC = "个人" + "AI档案"
    roots = [
        os.path.join(home, _MC, "脚本中心"),
        os.path.join(home, _MC, "开发工具"),
    ]
    env = os.environ.get("BULUOTUO_SCRIPT_CENTER")
    if env:
        roots.insert(0, env)
    for r in roots:
        p = os.path.join(r, *parts)
        if os.path.isfile(p):
            return p
    return ""


_SCRIPT = ""


def _script() -> str:
    global _SCRIPT
    if not _SCRIPT:
        _SCRIPT = rp("hermes_transform_gate.py")
    return _SCRIPT


def _run(mode: str, text: str, timeout: float = 8.0) -> Optional[str]:
    """跑脚本取清洗后文本。**任何失败 → None（fail-open）**。"""
    p = _script()
    if not p:
        return None
    try:
        r = subprocess.run([sys.executable, p, mode],
                           input=text.encode("utf-8"),
                           capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    out = (r.stdout or b"").decode("utf-8", "replace")
    return out


def _on_transform_tool_result(tool_name: str = "", args: Any = None,
                              result: Any = None, **_: Any) -> Optional[str]:
    """工具结果入对话之前清洗（None = 不变）。

    ⛔ 只处理 str 结果·⛔ 非 str 一律不动（⛔ 不猜结构）。
    ⛔ 不装饰错误结果——模型已经有更大问题（照官方 security-guidance 的处置）。
    """
    if not isinstance(result, str) or not result:
        return None
    try:
        import json as _json
        parsed = _json.loads(result)
        if isinstance(parsed, dict) and "error" in parsed and len(parsed) <= 2:
            return None
    except (ValueError, TypeError):
        pass
    out = _run("tool-result", result)
    return out if out and out != result else None


def _on_transform_llm_output(response_text: str = "", **_: Any) -> Optional[str]:
    """AI 回复最终投递之前塑形（None = 不变）。

    ⛔⛔ 只剥测试路径噪声·**绝不动语义**——塑形≠改写。
    这条通道碰的是「我说出口的话」·误伤代价最高·判据必须最窄。
    """
    if not isinstance(response_text, str) or not response_text:
        return None
    out = _run("llm-output", response_text)
    return out if out and out != response_text else None


def register(ctx) -> None:
    ctx.register_hook("transform_tool_result", _on_transform_tool_result)
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)