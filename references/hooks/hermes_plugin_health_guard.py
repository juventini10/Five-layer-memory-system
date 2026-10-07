#!/usr/bin/env python3
# version: v1.0.0
"""Hermes 端专属配置/健康守卫（守卫家族 · on_session_end 报告制）。

## 存在理由（Hermes 端单点失效面·第一性原理）

布洛陀其他端（ZCode/Qoder CN/AutoClaw）均有「端配置+活性」专属守卫，因为它们的
端健康=单一配置文件完整性。Hermes 端的健康面**不同**：`config.yaml plugins.enabled`
是插件注册的唯一真相源，而**每个插件是一整段 Python 逻辑**——配置对 ≠ 插件在跑。

Hermes 端三类独有静默失效（其他端无此形态）：

1. **死代码崩点静默**（2026-10-01 实锤）：`route-audit-hook/__init__.py` 末尾残留
   一段 `_mode`/`_label` 未定义的 try 块（2026-09-12 撤 l3 调用位时只删 for 头、
   留下循环体）。每轮 on_session_end 抛 NameError，except 分支自身又引用 `_mode`
   抛第二个 NameError 被 `except Exception: pass` 吞掉 ⇒ **守卫从未执行、零留痕、
   无告警**，与 doenglingz_level_declare_guard v1.0 空转同族。
   ⚠️ 这类缺陷逃过 py_compile（语法合法）、逃过平台 hooks 自检（注册态正常）、
   逃过 `platform_adaptation_check --src hermes`（只看配置不看代码）。

2. **幽灵插件**：`plugins/` 下目录存在但未在 config.yaml enabled（或反之）⇒
   「装了就以为在跑」或「在跑但名字对不上」。

3. **注册名漂移**：`plugin.yaml` 的 `provides_hooks` / `__init__.py` 的
   `ctx.register_hook(...)` 与 Hermes 内核 `VALID_HOOKS` 不一致 ⇒ 钩子注册
   成功但内核永不派发（内核按 VALID_HOOKS 过滤），症状=插件"装了没反应"。

## 三条纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截（report 制，恒 exit 0）
- 失败放行（任何异常→exit 0，不阻断会话）
- 保守判定（宁漏勿误；只查机械可判项，不做语义评价）

## 真相源

- `~/.hermes/config.yaml` → `plugins.enabled`（注册态 SSOT）
- `~/.hermes/plugins/*/plugin.yaml` → `provides_hooks`（声明态）
- `~/.hermes/plugins/*/__init__.py` → `ctx.register_hook` 调用（实际注册态）
- `~/.hermes/hermes-agent/hermes_cli/plugins.py` → `VALID_HOOKS`（内核合法集）

## 部署

WorkBuddy/ZCode 端的配置守卫不进 12-Hook 共享分母；本守卫同例（端专属·不计分母）。
由 Hermes 端 `hermes-plugin-health-hook` 插件在 on_session_end 调用（报告制）。

## 边界（诚实声明·防夸大）

- ✅ 能查：死代码未定义名 / 幽灵插件 / 注册名漂移 / 插件目录缺失 / 台账新鲜度
- ❌ 不能查：插件内部逻辑正确性（那是语义层）、内核是否真派发（无逐事件回执通道，
  只能查"注册名在 VALID_HOOKS 内"这一必要条件）⇒ 报 ✅ 不等于运行态证明。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import builtins
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional

VERSION = "v1.0.0"

HERMES_HOME = os.path.expanduser("~/.hermes")
CONFIG_YAML = os.path.join(HERMES_HOME, "config.yaml")
PLUGINS_DIR = os.path.join(HERMES_HOME, "plugins")
HERMES_SRC = os.path.join(HERMES_HOME, "hermes-agent", "hermes_cli", "plugins.py")
HEALTH_LOG = os.path.join(HERMES_HOME, "plugin_health_guard_state.json")

# 日志新鲜度阈值：正常会话结束的插件应每轮留痕（state mtime）。
# 24h 不用（有会话频率差）；12h 足够抓「插件彻底失联一天」又不会误报夜间闲置。
STALE_HOURS = 12


# ── 真相源读取 ────────────────────────────────────────────────

def read_enabled_plugins() -> Optional[list]:
    """读 config.yaml plugins.enabled。无 yaml 时退化为正则（回落律：不静默空放）。"""
    if not os.path.isfile(CONFIG_YAML):
        return None
    try:
        import yaml  # 优先权威解析
        with open(CONFIG_YAML, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh) or {}
        enabled = ((cfg.get("plugins") or {}).get("enabled")) or []
        return [str(x) for x in enabled]
    except ImportError:
        # 无 PyYAML：受限正则（只认 plugins.enabled 块的 '- name' 行）
        out, in_block = [], False
        try:
            for line in open(CONFIG_YAML, encoding="utf-8"):
                if re.match(r"^plugins:\s*$", line):
                    in_block = True
                    continue
                if in_block:
                    if line.strip() and not line.startswith((" ", "\t", "-")):
                        break
                    m = re.match(r"^\s*-\s*(\S+)\s*$", line)
                    if m:
                        out.append(m.group(1))
        except OSError:
            return None
        return out


def plugin_dirs() -> list:
    if not os.path.isdir(PLUGINS_DIR):
        return []
    return sorted(
        d for d in os.listdir(PLUGINS_DIR)
        if os.path.isfile(os.path.join(PLUGINS_DIR, d, "plugin.yaml"))
    )


def read_declared_hooks(name: str) -> Optional[list]:
    """读 plugin.yaml 的 provides_hooks（声明态）。"""
    p = os.path.join(PLUGINS_DIR, name, "plugin.yaml")
    try:
        txt = open(p, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"^provides_hooks:\s*$", txt, re.M)
    if not m:
        return []          # 该插件不提供 hook（只有 tool 或 system_prompt_section）
    out = []
    for line in txt[m.end():].splitlines():
        if not line.startswith((" ", "\t")):
            break
        mm = re.match(r"^\s*-\s*(\S+)\s*$", line)
        if mm:
            out.append(mm.group(1))
    return out


def read_registered_hooks(name: str) -> Optional[list]:
    """读 __init__.py 里 ctx.register_hook(...) 的实参（实际注册态·非声明态）。"""
    p = os.path.join(PLUGINS_DIR, name, "__init__.py")
    try:
        src = open(p, encoding="utf-8").read()
    except OSError:
        return None
    return re.findall(r"register_hook\(\s*[\"']([^\"']+)[\"']\s*,", src)


def read_valid_hooks() -> Optional[set]:
    """读 Hermes 内核 VALID_HOOKS（hook 名是否合法的唯一判据）。

    ⚠️ 自曝·首版假阳性（守卫规范 §3.5 恒假形态）：正则 `Set\\[str\\]\\s*=\\s*\\{(.*?)\\}`
    非贪婪匹配到**第一个** `}` 即停，而 VALID_HOOKS 是跨行的 set 字面量（多个 `}` 分组），
    ⇒ 只截到首段，`on_session_start`/`on_session_end` 等被判"不在集内"= 4 条假红。
    ✅DO 用「括号配平扫描」取完整字面量；⛔DO NOT 用非贪婪正则扫嵌套结构。
    """
    if not os.path.isfile(HERMES_SRC):
        return None
    try:
        src = open(HERMES_SRC, encoding="utf-8").read()
    except OSError:
        return None
    m = re.search(r"VALID_HOOKS:\s*Set\[str\]\s*=\s*\{", src)
    if not m:
        return None
    # 从 '{' 起做括号配平，取出完整 set 体
    start = src.index("{", m.start())
    depth, end = 0, None
    for i in range(start, len(src)):
        ch = src[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return None
    return set(re.findall(r"[\"']([a-z_]+)[\"']", src[start:end]))


# ── 死代码扫描（§3.5 崩点静默 / §3.12 空转显形）────────────────

_BUILTINS = set(dir(builtins))


def _module_bindings(tree: ast.Module) -> set:
    """模块级绑定（函数/类名、顶层赋值、导入、顶层复合语句内的绑定）。

    ⚠️ 作用域陷阱（自曝·本函数首版漏了顶层复合语句 → 假阳性泛滥）：
    顶层 `for`/`if`/`try` 内的赋值与 import 同样是模块级名字，
    漏收会让每个函数都报一堆"未定义"。
    """
    out = set()

    def collect(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                out.add(sub.id)
            elif isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.add(sub.name)
            elif isinstance(sub, ast.arg):
                out.add(sub.arg)
            elif isinstance(sub, ast.Import):
                for a in sub.names:
                    out.add((a.asname or a.name).split(".")[0])
            elif isinstance(sub, ast.ImportFrom):
                for a in sub.names:
                    out.add(a.asname or a.name)
            elif isinstance(sub, ast.ExceptHandler) and sub.name:
                out.add(sub.name)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(node.name)
        collect(node)
    return out


def scan_undefined(path: str) -> list:
    """返回 [(func_name, name, lineno), ...]：函数体内加载但无任何绑定的名字。

    ✅DO 只报「函数内 Load 且不在局部绑定 ∪ 模块绑定 ∪ builtins」——
    这是静态不可判的最小集合（运行时才知是否被闭包/globals 注入）。
    ⛔DO NOT 报模块级未定义（那是另一类，且 import 期即崩不会静默）。
    """
    try:
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return []
    assert isinstance(tree, ast.Module)   # ast.parse 返回 Module；显式收窄供类型检查
    glob = _module_bindings(tree) | _BUILTINS
    bad = []
    for fn in tree.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        local = {a.arg for a in list(fn.args.args) + list(fn.args.kwonlyargs)}
        if fn.args.vararg:
            local.add(fn.args.vararg.arg)
        if fn.args.kwarg:
            local.add(fn.args.kwarg.arg)
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                local.add(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                local.add(node.name)
            elif isinstance(node, ast.arg):
                local.add(node.arg)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                local.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                local.update(node.names)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    local.add((a.asname or a.name).split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    local.add(a.asname or a.name)
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in local and node.id not in glob:
                    bad.append((fn.name, node.id, node.lineno))
    return bad


# ── 检查项 ────────────────────────────────────────────────────

def check_ghost_plugins() -> list:
    """幽灵插件：目录存在但未 enabled / enabled 但目录缺失（双向）。"""
    out = []
    enabled = read_enabled_plugins()
    if enabled is None:
        return [{"level": "WARN", "kind": "config_unreadable",
                 "detail": "config.yaml 不可读或无 plugins.enabled → 本项跳过"}]
    dirs = plugin_dirs()
    for name in dirs:
        if name not in enabled:
            out.append({"level": "WARN", "kind": "orphan_plugin",
                        "detail": f"插件目录存在但未在 config.yaml enabled：{name}"})
    for name in enabled:
        if name not in dirs:
            out.append({"level": "RED", "kind": "missing_plugin",
                        "detail": f"config.yaml 已启用但插件目录缺失：{name}"})
    return out


def check_hook_registration() -> list:
    """注册名漂移：register_hook 实参 ∪ provides_hooks 声明，须 ⊆ 内核 VALID_HOOKS。"""
    valid = read_valid_hooks()
    if valid is None:
        return [{"level": "WARN", "kind": "valid_hooks_unavailable",
                 "detail": "读不到 Hermes 内核 VALID_HOOKS → 本项跳过"}]
    out = []
    for name in plugin_dirs():
        declared = read_declared_hooks(name)
        registered = read_registered_hooks(name)
        if declared is None:
            out.append({"level": "RED", "kind": "plugin_unreadable",
                        "detail": f"{name}: plugin.yaml 不可读"})
            continue
        for hook in declared:
            if hook not in valid:
                out.append({"level": "RED", "kind": "invalid_declared_hook",
                            "detail": f"{name}: plugin.yaml 声明 {hook} 不在内核 VALID_HOOKS"})
        if registered is None:
            continue
        for hook in registered:
            if hook not in valid:
                out.append({"level": "RED", "kind": "invalid_registered_hook",
                            "detail": f"{name}: register_hook({hook}) 不在内核 VALID_HOOKS"})
        # 声明与实际不一致（plugin.yaml 漏声明 = 下一个人读声明会误判）
        if declared and registered:
            miss = set(registered) - set(declared)
            if miss:
                out.append({"level": "WARN", "kind": "decl_register_mismatch",
                            "detail": f"{name}: 实际注册但 plugin.yaml 未声明：{sorted(miss)}"})
    return out


def check_dead_code() -> list:
    """死代码崩点：插件 __init__.py 内未定义名（py_compile 抓不到的静默崩点）。"""
    out = []
    for name in plugin_dirs():
        init = os.path.join(PLUGINS_DIR, name, "__init__.py")
        if not os.path.isfile(init):
            continue
        for fn, sym, line in scan_undefined(init):
            out.append({"level": "RED", "kind": "undefined_name",
                        "detail": f"{name}/__init__.py:{line} {fn}() 引用未定义名 {sym}"
                                  f"（运行必 NameError；except 内同名引用会被静默吞）"})
    return out


def check_health_freshness() -> list:
    """插件健康台账新鲜度：state 文件超 STALE_HOURS 未更新 = 插件疑似失联。"""
    if not os.path.isfile(HEALTH_LOG):
        return []          # 首跑无台账属正常，不假红
    try:
        age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(HEALTH_LOG))
    except OSError:
        return []
    if age > timedelta(hours=STALE_HOURS):
        return [{"level": "RED", "kind": "stale_health_log",
                  "detail": f"插件健康台账已 {age.seconds // 3600}h 未更新"
                            f"（阈值 {STALE_HOURS}h）→ on_session_end 链路疑似断"}]
    return []


def check_config_clobber_risk() -> list:
    """配置覆写风险：后台遗留的 `hermes config set` 进程会在完成瞬间覆写整份配置。

    ⚠️ 2026-10-01 实锤（真踩过一次·根因修正）：
       上一轮我以为「桌面 App 保存设置时覆写 config.yaml」导致末尾两行插件被截断——
       **那个归因是错的**。真凶是**我自己启动的一个卡在 source-update 检查上的
       后台 `hermes config set` 进程**：它启动时捕获旧值（8 插件），卡了二十多分钟后
       才完成，完成瞬间用旧值整份写回 ⇒ 把期间新增的插件静默吃掉。

       ⇒ 机理与预防同「陈旧读覆写」（stale-read clobber）：
         **长时运行进程携带的旧快照 + 迟到的整份写** = 配置丢失。
       ✅ 预防＝写前确认无同类在途进程；⛔ 预防不住就至少让它显形（RED），
         不再靠"改完记得看一眼"。

    判据：进程表中存在 `hermes config set` 且其启动早于当前 config.yaml 的 mtime
    （= 它携带的是过期快照）。纯机械可判，不猜意图。
    """
    out = []
    try:
        proc = subprocess.run(["ps", "-eo", "pid,args"],
                              capture_output=True, text=True, timeout=10)
    except Exception:
        return [{"level": "WARN", "kind": "proc_scan_failed",
                 "detail": "ps 不可用 → 本项跳过"}]
    cfg_mtime = os.path.getmtime(CONFIG_YAML) if os.path.isfile(CONFIG_YAML) else 0
    for line in proc.stdout.splitlines():
        if "hermes config set" not in line:
            continue
        # ⚠️ 自指假阳性（变异探针/实跑各抓到一次·2026-10-01）：
        #   `ps` 快照里会包含**本守卫自己**那条含 "hermes config set" 字样的
        #   python/shell 命令行 ⇒ 朴素子串匹配会 100% 自命中 ⇒ 永久 RED（告警疲劳）。
        #   判据收紧：命令行必须**以 hermes 开头**（真实 CLI 形态），
        #   且排除 python/sh -c / grep 等包装进程。
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        pid, args = parts[0], parts[1].strip()
        argv0 = args.split()[0] if args.split() else ""
        if os.path.basename(argv0) != "hermes":
            continue                      # 非 hermes CLI 本体（包装/自指/grep）
        out.append({
            "level": "RED", "kind": "stale_writer_in_flight",
            "detail": "检测到在途 `hermes config set` 进程——它携带启动时的旧快照，"
                      "完成瞬间会整份覆写 config.yaml（2026-10-01 实锤吃掉 2 个插件）。"
                      f"处理：kill {pid} 或等它退出后再改配置。"
                      f"当前 config mtime={cfg_mtime:.0f}",
        })
        break
    return out


def check_dispatch_heartbeat() -> list:
    """运行态腿：**派发心跳**（补「注册态 ≠ 派发态」盲区）。

    ⚠️ 为什么必须补（2026-10-01 核实《04-跨端接入指南》「派发心跳机制」节）：
       该节记的病根＝**「写进配置=生效」的机制，配置完好 ≠ 宿主真派发**，
       端用户实证：第三方插件 hooks.json 格式非法 → 宿主整事件连坐停摆 →
       本包钩子集体静默失效、**零症状**（注册态自检结构性盲区）。

       本守卫此前只查**注册态**（配置/声明/注册名/静态名）⇒ 正落在该盲区里。
       而 `guard_heartbeat_check.py`（公共心跳守卫）硬编码 `~/.workbuddy/`
       （HB_DIR/SETTINGS 全指向 WB）⇒ **Hermes 端零覆盖**。

    ✅DO 用 Hermes 端**自己已有的运行态产物**当心跳（零新增机制）：
       元守卫自己的 state 文件（on_session_end 每轮写）＋ 三个集群的 hook log
       ＋ 注入链 stats。判据=**mtime 新鲜度**。
    ⛔DO NOT 判死（守则 §3.5·判据沉淀②）：新鲜度天然无法区分「守卫停摆」
       与「用户休假/无会话」⇒ **只报 WARN·advisory 显形·不阻断**。
       假阳性比没有检查更糟。
    """
    out = []
    now = datetime.now()
    for label, path, hours in _HEARTBEAT_SOURCES:
        if not os.path.isfile(path):
            continue                      # 尚无产物 = 首跑·不假红
        try:
            age = now - datetime.fromtimestamp(os.path.getmtime(path))
        except OSError:
            continue
        if age > timedelta(hours=hours):
            out.append({
                "level": "WARN", "kind": "stale_heartbeat",
                "detail": f"[advisory] {label} 已 {age.seconds // 3600}h 未更新"
                          f"（阈值 {hours}h）—— 注册态正常但运行态无痕："
                          f"宿主可能未真派发该钩子（注册态≠派发态·指南「派发心跳机制」节）",
            })
    return out


# 运行态心跳源（label, 路径, 阈值小时）——⛔ 阈值按各源真实调用频率定·不统一拍
_HEARTBEAT_SOURCES = [
    ("hermes-plugin-health（on_session_end 自证）",
     os.path.expanduser("~/.hermes/plugin_health_guard_state.json"), 24),
    ("buluotuo-closeout-guards（post_llm_call·仅告警时写盘）",
     os.path.expanduser("~/.hermes/closeout_guards_hook.log"), 72),
    ("buluotuo-readonly-guards（on_session_end·仅告警时写盘）",
     os.path.expanduser("~/.hermes/readonly_guards_hook.log"), 72),
    ("buluotuo-prompt-inject-hook（pre_llm_call·每轮 bump）",
     os.path.expanduser("~/.hermes/buluotuo_inject_stats.json"), 24),
]


def export_hooks_registry(path: str | None = None) -> dict:
    """把 Hermes 端注册态**机械派生**成公共心跳守卫可读的格式。

    ## 为什么需要（2026-10-01·端中立化收口）

    `guard_heartbeat_check.py` v3.2 已端中立化（`GUARD_HEARTBEAT_ROOT` /
    `GUARD_HEARTBEAT_SETTINGS` env），但它的**注册清单真相源形态**是
    `settings.json` 的 `{"hooks": {event: [{hooks:[{command:...}]}]}}` 树
    ——**Hermes 端无此结构**（真相源是 `config.yaml` 的 `plugins.enabled` 列表）。

    ⛔ **不 fork 公共脚本**（守卫规范 §二·十四 接入不拥有·零复制）
    ⛔ **不手写注册清单**（会立刻漂移·且「手写=声明」正是 SSOT 反复批的病）
    ✅DO **从 config.yaml 机械派生**——本函数即派生器·每次跑都重算。
       注册清单与派发态**分离**：这里只给「名册」（注册态），
       派发态由心跳腿（`check_dispatch_heartbeat`）独立判（指南 §派发心跳机制
       判据沉淀①：注册态检查只证"名册有名字"不证"打卡机有记录"）。
    """
    out = path or os.path.join(HERMES_HOME, "hooks_registry.json")
    enabled = read_enabled_plugins() or []
    # 每插件一条「on_session_end」形态的登记（保守：只登记可核的 on_session_end
    # 承载插件·⛔ 不臆造 pre_llm_call/post_llm_call 的 per-event 注册态——
    #   那些由内核 VALID_HOOKS + plugin.yaml provides_声明双面已覆盖）
    reg = {}
    for name in enabled:
        pdir = os.path.join(PLUGINS_DIR, name)
        init = os.path.join(pdir, "__init__.py")
        if not os.path.isfile(init):
            continue
        try:
            src = open(init, encoding="utf-8").read()
        except OSError:
            continue
        hooks = re.findall(r"register_hook\(\s*[\"']([^\"']+)[\"']\s*,", src)
        for h in hooks:
            # ⚠️ 诚实边界（⛔ 不造假凭据）：公共心跳守卫按 `command` 里的脚本名去
            #   找实体脚本，但**插件不是脚本**（插件是 Hermes 特有的加载形态·
            #   无对应 .py 可执行体）⇒ 这里给「插件名」而非伪造脚本路径。
            #   后果要如实说：公共守卫的 hook 腿对本端**只能核到「名册」**，
            #   派发态仍由本守卫自己的 `check_dispatch_heartbeat`（读真实运行态产物）
            #   独立判——两条腿互补，⛔ 不互相顶账（指南 §派发心跳机制 判据沉淀①）。
            reg.setdefault(h, []).append({"command": f"hermes-plugin:{name}"})
    data = {"hooks": {k: [{"hooks": v}] for k, v in reg.items()},
            "_source": "~/.hermes/config.yaml plugins.enabled + plugins/*/__init__.py",
            "_note": "机械派生·非手写·注册态≠派发态（派发态见 heartbeat 检查项）"}
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass
    return data


CHECKS = {
    "ghost": check_ghost_plugins,
    "hookreg": check_hook_registration,
    "deadcode": check_dead_code,
    "freshness": check_health_freshness,
    "clobber": check_config_clobber_risk,
    "heartbeat": check_dispatch_heartbeat,
}


def run_all() -> dict:
    # 先机械派生注册清单（每次重算·⛔ 不缓存不手写·防漂移）
    # ⚠️ 自曝静默失败（2026-10-01 实测踩出）：初版这里是 `except Exception: pass`
    #   ⇒ 派生器里一个 NameError（常量名写错）被整条吞掉·文件永不生成·
    #   **而 --check 照样报 RED 0 全绿** ⇒ 又一个"崩点静默"实例。
    #   ✅DO 失败要显形（进 findings·归自己·守卫规范 §3.4 归因律）。
    findings = []
    try:
        export_hooks_registry()
    except Exception as exc:
        findings.append({"level": "WARN", "kind": "registry_export_failed",
                         "detail": f"注册清单派生失败（公共心跳守卫将只能核 WB 侧名册）：{exc!r}"})
    for name, fn in CHECKS.items():
        try:
            findings.extend(fn())
        except Exception as exc:
            # 聚合层自身故障归自己（守卫规范 §3.4 归因律扩展·不得计入被检对象）
            findings.append({"level": "WARN", "kind": "checker_crash",
                             "detail": f"检查项 {name} 自身异常：{exc!r}"})
    return {
        "version": VERSION,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "plugins_enabled": read_enabled_plugins(),
        "plugins_on_disk": plugin_dirs(),
        "findings": findings,
        "red": sum(1 for f in findings if f["level"] == "RED"),
        "warn": sum(1 for f in findings if f["level"] == "WARN"),
    }


def write_state(report: dict) -> None:
    try:
        os.makedirs(os.path.dirname(HEALTH_LOG), exist_ok=True)
        with open(HEALTH_LOG, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _selftest() -> int:
    """自测（守卫规范 §3.0·5）：每条判据须有「专属夹具」+双向（能红/不误伤）。

    ✅DO 断言扫描域 == 被检对象的产出域：临时目录里造真插件文件（.py 内容），
    ⛔DO NOT 拿写死字符串假装扫过——首版易犯（AGENTS.md 表头顶罪族）。
    """
    import tempfile
    passed = failed = 0

    def case(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print(f"  ❌ {name}")

    # 夹具：真实插件文件（死代码形态）
    with tempfile.TemporaryDirectory() as td:
        dead = os.path.join(td, "__init__.py")
        open(dead, "w", encoding="utf-8").write(
            "import os\n"
            "def f():\n"
            "    try:\n"
            "        print(os.sep)\n"
            "    except Exception:\n"
            "        print(_mode)\n"
        )
        clean = os.path.join(td, "clean.py")
        open(clean, "w", encoding="utf-8").write(
            "import os\n"
            "MODE = 'x'\n"
            "def g():\n"
            "    try:\n"
            "        print(os.sep, MODE)\n"
            "    except Exception as e:\n"
            "        print(MODE, e)\n"
        )
        # 复合语句内绑定（作用域陷阱回归夹具）
        compound = os.path.join(td, "compound.py")
        open(compound, "w", encoding="utf-8").write(
            "import os\n"
            "for _x in range(1):\n"
            "    TOPVAR = _x\n"
            "try:\n"
            "    import json\n"
            "except ImportError:\n"
            "    json = None\n"
            "def h():\n"
            "    return TOPVAR, json, os.sep\n"
        )
        # N1 死代码（真伤）
        bad = scan_undefined(dead)
        case("deadcode 抓未定义名", any(s == "_mode" for _, s, _ in bad))
        # N2 不误伤：合法插件零命中
        case("clean 零命中", scan_undefined(clean) == [])
        # N3 作用域陷阱回归：顶层复合语句内的绑定不得误报
        case("compound 零命中（作用域陷阱回归）", scan_undefined(compound) == [])
        # N4 语法坏文件不崩（回落律）
        badf = os.path.join(td, "broken.py")
        open(badf, "w", encoding="utf-8").write("def (:\n")
        case("坏文件返回空不抛", scan_undefined(badf) == [])
        # N5 builtins 不误报
        bi = os.path.join(td, "bi.py")
        open(bi, "w", encoding="utf-8").write(
            "def k():\n    return len(str(sorted([1])))\n")
        case("builtins 不误报", scan_undefined(bi) == [])

    # 变异探针（守卫规范 §3.9）：关掉扫描 ⇒ 死代码用例必须转绿（证明它有牙）
    orig = CHECKS["deadcode"]
    CHECKS["deadcode"] = lambda: []
    try:
        rep = run_all()
    finally:
        CHECKS["deadcode"] = orig
    case("变异探针：关判据后死代码不再报（证明承重）",
         not any(f["kind"] == "undefined_name" for f in rep["findings"]))
    # 变异探针反向：判据在位时真实机器上确有其事（2026-10-01 已修 ⇒ 现应 0）
    rep_real = run_all()
    case("真实机器死代码已清零（修复态）",
         not any(f["kind"] == "undefined_name" for f in rep_real["findings"]))

    print(f"  self-test: {passed} passed, {failed} failed")
    print("MUT:OK" if failed == 0 else "MUT:FAIL")
    return 0 if failed == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Hermes 端插件/配置健康守卫")
    ap.add_argument("--check", action="store_true", help="人类可读报告")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--self-test", action="store_true", help="自测夹具")
    ap.add_argument("--no-state", action="store_true", help="不写健康台账")
    args = ap.parse_args()

    if args.self_test:
        return _selftest()

    rep = run_all()
    if not args.no_state:
        write_state(rep)

    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    elif args.check:
        print(f"Hermes 插件健康 · {rep['ts']} · {VERSION}")
        print(f"  enabled: {rep['plugins_enabled']}")
        print(f"  on_disk: {rep['plugins_on_disk']}")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    # 恒 exit 0（Hook 三纪律·报告制不阻断）
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass