"""布洛陀写侧守卫集群 · Hermes 端适配（pre_tool_call 通道）。

## 存在理由（作者 2026-10-01 提醒·「其他端做了有用的脚本和 hook，我们自己也要适配」）

对账实锤：WorkBuddy 端实挂 **46 个 hook**，Hermes 端当时仅 10 个插件 ⇒ 缺口 31 项。
其中 **PreToolUse 族 5 个**（grep_sandbox / edit_heading / change_reflux / skill_write_gate /
skill_spec_read）是**写侧真拦截**——它们拦住的是"错误的写"发生在写之前，成本最低。

**Hermes 端特性（⛔ 不是照搬，是更强）**：

    plugins.py:2055  invoke_lifecycle_hook("pre_tool_call", tool_name=..., args={...})
    plugins_dispatch.py:49  pre_tool_call ∈ _HOOK_TIMEOUT_FAIL_CLOSED_HOOKS
    plugins.py:2049  precedence: block > approve > none（任一 veto 胜）

⇒ Hermes 的 `pre_tool_call` 是 **fail-closed** 通道：钩子抛异常/超时 = **拦下**，
而 WorkBuddy 的 PreToolUse 默认 fail-open。**同一批守卫装在 Hermes 上更硬**。
载荷形态也不同：WB 走 stdin JSON，Hermes 走 kwargs（`tool_name` + `args` dict）。

## 接入纪律（守卫规范 §二·十四 接入不拥有）

**⛔ 零判据内联**：五个守卫的判据全在各自脚本本体，本插件只做
「读 args → 调脚本 → 读 stdout → 转 block 指令」的适配。

## 为什么不 spawn 子进程跑 shell 版脚本

WB 版脚本走 stdin 收 JSON。Hermes 端 args 已在 kwargs 里 ⇒ 直接喂 stdin 即可
（`json.dumps({...})`），⛔ 不必改脚本本体。

## 纪律（守卫编写规范 §八 Hook 三纪律）

- **本通道允许真拦截**（fail-closed 是 Hermes 内核语义，不是插件越权）：
  仅当脚本明确判定违规才 block；⛔ 脚本缺失/超时/异常 → **一律放行**
  （守卫失灵不该锁死用户的活干——拦截只在有确凿判据时）
- 保守判定：⛔ 不猜·判据全在脚本
- 端隔离：⛔ 只读本端 args·不写他端
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
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


__version__ = "v1.1.0"

_HOME = os.path.expanduser("~")
_DEVTOOLS = rp("devtools")
_LOG = os.path.join(_HOME, ".hermes", "pretool_guards_hook.log")

# 五守卫（对齐 WorkBuddy PreToolUse 族·⛔ 判据全在脚本本体）
_GUARDS = [
    ("grep_sandbox_guard.py", []),          # 沙箱 grep 不支持 \w \+ ⇒ 先教怎么写
    ("edit_heading_guard.py", ["--hook"]),  # Edit 吞标题（3 起真实事故）
    ("change_reflux_guard.py", []),         # 改触发件必回流清单
    ("skill_write_gate_guard.py", []),      # 写 Skill 前置闸门
    ("skill_spec_read_guard.py", []),       # 改 Skill 前必读规范（作者 2026-09-19 立规）
]

_TIMEOUT = 20
# 写侧工具（其余工具不跑守卫·省时·这也是 Hermes 端能挂 5 个不拖慢的原因）
_WRITE_TOOLS = {"write_file", "patch", "edit", "str_replace", "create_file",
                "write", "edit_file", "multiedit"}
# 🆕 v1.1.0 读侧工具（2026-10-02）：仅用于**只读型守卫**——见 _READ_GUARDS。
#   ⛔ 不把读工具丢进 _WRITE_TOOLS（那会让 5 个写侧守卫对每次 Read 都跑一遍=白烧）。
_READ_TOOLS = {"read_file", "view_file", "open_file", "grep", "search_files",
               "rg", "ripgrep", "glob", "find_files", "list_files"}
# 只读型守卫白名单（守卫写作时会出现「读侧记状态·写侧校验」双分支的才可进）
# ⚠️ 准入判据：该守卫的读侧分支**只写自己的 marker/缓存**，⛔ 不可能因读内容而拦截用户。
#   skill_spec_read_guard 读规范 → 写 `spec_read.active` marker（纯记状态·零拦截）✅ 合规。
#   其余四守卫（grep_sandbox/edit_heading/change_reflux/skill_write_gate）均为
#   纯写侧判据·读侧无分支 ⇒ ⛔ 不进本白名单（不为「对称」而对称）。
_READ_GUARDS = {
    "skill_spec_read_guard.py": [],
}

# ⚠️ 三处契约错位（实测踩出·2026-10-01·这正是"照搬"的坑）：
#   ① 工具名：守卫脚本按 **WorkBuddy/Claude 的 CamelCase 名**判
#      （`if tool in ("Edit","Write","MultiEdit","NotebookEdit")`），
#      而 Hermes 端真名是小写下划线（`write_file`/`patch`）⇒ 不映射则守卫**永远不触发**
#      （我第一版直接传 `write_file` → 正例放行 → 查出来是这个）。
#   ② 字段名：脚本读 `toolName` / `input`（WB 形态），⛔ 不认 `tool_name`/`args`。
#   ③ 输出通道：违规信息 **打 stderr + exit 2**（⛔ stdout 为空）——
#      只读 stdout ⇒ 有违规也看不见。
#   ⇒ 适配层三处全转。判据零改动（脚本本体一个字不动）。
_WB_TOOL_MAP = {
    "write_file": "Write", "create_file": "Write", "write": "Write",
    "edit_file": "Edit", "edit": "Edit", "multiedit": "MultiEdit",
    "patch": "Edit", "str_replace": "Edit", "notebook_edit": "NotebookEdit",
    # 🆕 v1.1.0 读侧映射（2026-10-02 修「读规范永不记 marker」缺陷）：
    #   守卫 skill_spec_read_guard.py 内有**两个分支**——读规范命中 → 记 marker（L74）；
    #   改 SKILL.md 无 marker → 拦（L78）。⛔ 此前读工具名不在 map 内 ⇒ 传下去的是
    #   小写 `read_file`，守卫 L74 判 `tool in ("Read","Grep","Glob")` 永远不中
    #   ⇒ **只剩拦截分支·正向分支在 Hermes 端结构性失效**（守卫规范 §3.4·扩D
    #   观察域律：信号源不在扫描域内）。现象=4h TTL 一到改任何 SKILL.md 必被误锁，
    #   即使本会话真读了规范。⛔ 判据脚本零改动——只补适配层映射（守「零判据内联」）。
    "read_file": "Read", "view_file": "Read", "open_file": "Read",
    "grep": "Grep", "search_files": "Grep", "rg": "Grep", "ripgrep": "Grep",
    "glob": "Glob", "find_files": "Glob", "list_files": "Glob",
}
# Hermes args 参数名 → WB input 参数名（守卫按 WB 名取路径）
_ARG_ALIASES = {
    "path": "file_path", "file": "file_path", "filename": "file_path",
    "filePath": "file_path", "content": "content", "new_string": "content",
    "old_string": "content", "new_str": "content",
}


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _target_text(args: Dict[str, Any]) -> str:
    """从 args 里取出守卫要看的目标（文件路径 + 待写内容）。

    Hermes 各写工具参数名不一（write_file=path/file_path/content；patch=path/old_string…）
    ⇒ 取所有字符串值拼起来喂守卫，⛔ 不猜单一参数名（守卫自己按内容判）。
    """
    out = []
    for v in args.values():
        if isinstance(v, str):
            out.append(v)
    return "\n".join(out)


def _run_guard(script: str, extra: List[str], tool_name: str,
               args: Dict[str, Any]) -> Optional[str]:
    """跑一个守卫，返回其违规输出（None=放行）。⛔ 任何异常 → None（放行）。"""
    path = os.path.join(_DEVTOOLS, script)
    if not os.path.isfile(path):
        return None                      # 脚本不存在 → 静默放行（不误锁）
    wb_tool = _WB_TOOL_MAP.get(tool_name, tool_name)
    wb_input = {}
    for k, v in args.items():
        wb_input[_ARG_ALIASES.get(k, k)] = v
    payload = json.dumps({"toolName": wb_tool, "input": wb_input,
                          # 同时给 WB 双形态键（不同脚本读法不同·⛔ 冗余无害）
                          "tool_name": wb_tool, "tool_input": wb_input},
                         ensure_ascii=False)
    try:
        proc = subprocess.run(
            [sys.executable, path] + extra,
            input=payload, capture_output=True, text=True,
            timeout=_TIMEOUT, cwd=_DEVTOOLS,
        )
        # ⛔ stderr 也要读：违规信息打 stderr（实测 skill_spec_read_guard 是 exit 2 + stderr）
        msg = (proc.stderr or "").strip() or (proc.stdout or "").strip()
        if proc.returncode == 0:
            return None                  # exit 0 = 守卫判通过
        return msg or f"守卫 {script} 拒绝（exit {proc.returncode}·无输出）"
    except Exception:
        return None                      # ⛔ 异常/超时一律放行


def _pre_tool_call(tool_name: str = "", args: Optional[Dict[str, Any]] = None,
                   session_id: str = "", **_: Any) -> Optional[Dict[str, str]]:
    """写侧真拦截 + 读侧只记状态（v1.1.0）。⛔ 返回 None = 放行；返回 block 指令 = 拦下。"""
    args = dict(args or {})
    is_write = tool_name in _WRITE_TOOLS
    is_read = tool_name in _READ_TOOLS
    if not (is_write or is_read):
        return None                      # ⛔ 非写非读工具不跑（省时）
    text = _target_text(args)
    if not text.strip():
        return None
    # 读侧：只跑只读型守卫（记 marker 类·零拦截能力）；⛔ 不跑写侧守卫（纯烧钱）
    guards = _GUARDS if is_write else _READ_GUARDS.items()
    for script, extra in guards:
        out = _run_guard(script, extra, tool_name, args)
        if not out:
            continue
        # ⛔ 读侧即使守卫有输出也**不 block**（读侧无拦截权·失败放行=守卫规范 §三 Hook 三纪律）
        #    ——skill_spec_read_guard 的读侧只会 return（记 marker），走不到这里；
        #    此分支是防御性：万一将来有人把有拦截能力的守卫误加进 _READ_GUARDS。
        if not is_write:
            _log(f"READ-SIDE-SKIP {script} tool={tool_name}（读侧不具拦截权·放行）")
            continue
        _log(f"BLOCK by {script} tool={tool_name}")
        return {"action": "block",
                "message": f"[{script}] {out[:600]}"}
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _pre_tool_call)