#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""platform_adaptation_check.py v0.7.1 — 布洛陀脚本体系·平台接入率漂移校验（检测+自愈混合架构）
v0.7.1（2026-08-26·回滚 SSOT 动态解析·恢复硬编码清单）：
  - 回滚 v0.8 的 SSOT 表格动态解析（复杂表格格式导致解析错误）
  - 恢复 v0.7.1 的硬编码 HOOKS 清单（简洁可靠）
  - reply_format_guard.py 已从清单移除（2026-08-26 皮叔令"完全删除"）
  - 各平台实际接入情况由 check_* 函数直接读取配置文件/运行时文件检测
v0.7.1（2026-08-22）：check_dsh 分母口径对齐哲学文件——DSH_EXCLUDED 增 reply_format_guard.py
（皮叔 2026-08-13 决策·⛔合法停用排除分母·pre-step 预防式已覆盖·见 SSOT v1.3.14）·分母 12→11·
根治校验器口径≠文档产生的"分子巧合相等误报无漂移"（对齐 v1.3.14 DSH 11/11）。

挂为各平台 Hook（Stop/on_session_end）：每次会话结束校验实际挂载的 Hook 清单
vs §二·七 文档记录的接入率，报告 drift（文档≠事实）。

v0.6（2026-08-21）：新增 --fix 模式（C''方案·事件驱动drift修复）：
  - 低风险操作（自动执行）：实测接入率与SSOT文档不一致时，自动同步文档接入率行
  - 高风险操作（仅报告）：settings.json 缺失 Hook 时生成补挂建议，不自动修改配置
  - Hook 纪律：无论哪种情况，exit 0 放行，确保流程不中断

支持平台：
  --src workbuddy      读 ~/.workbuddy/settings.json（12-Hook 清单·SSOT §二·七 真相源）
  --src hermes         读 ~/.hermes/config.yaml plugins.enabled（跨工具中立·Hermes 以插件形态接入）
  --src qoder-desktop  读 ~/.qoder/settings.json hooks（Qoder Desktop·SessionStart/UserPromptSubmit/Stop）
  --src qoder-cn       读 ~/.qoder-cn/settings.json hooks（Qoder CN·crossend 适用）
  --src dsh            读 DSH 插件 src/index.js 实盘（STOP_GUARDS 数组 Stop 类 + pre-step 3 通道·
                       2026-08-22 v0.7 幽灵挂载根治：文档声称挂载↔插件实盘机械对账·DSH 走插件不走 settings.json）
  --src zcode          读 ~/.zcode/cli/config.json hooks.events 实盘（ZCode·2026-08-22 第13端接入·
                       配置文件形态 hooks.events.<Event> 与 CC 形态 hooks.<Event> 并存适配）
  --src autoclaw       读 ~/.openclaw-autoclaw/openclaw.json + route_autoclaw_patrol.sh 实盘
                       （AutoClaw·2026-08-22 第7端机械校验：patrol 守卫清单(11)+配置核心项+
                       注入插件实盘·分母 13 含 crossend——2026-07-28 AutoClaw workspace 指回 ~ 事故肇事方）

设计原则（失败默认放行，绝不破坏对话·守 Hook 三纪律）：
  - 解析异常 / 配置读不到 / 正则未命中 → 直接 exit 0
  - 无漂移 → 静默（仅写日志），不打断节奏
  - 有漂移 → stdout 告警一行 + 写日志（仍 exit 0，不拦截）
  - 任何未捕获异常 → exit 0

跨工具中立（脚本哲学 §二·五）：本脚本是公共设施，各工具 hook 只调用不拥有；
Hermes 端由 route-audit-hook（on_session_end）调用，WorkBuddy 由 Stop 钩子调用，
Qoder Desktop 由各工具自治调用（自治核对·单一写入权归你）。
"""
import sys
import os
import re
import json
import argparse

# B埋点(v2.0·2026-09-03·童灵·补exit码埋点): 从"脚本开头Popen后台写日志(无exit码)"
# 改为"包装入口点在退出时写日志(含exit码)"——原设计在脚本开头写日志，无法知道最终exit码;
# v2.0用try/finally包装main()，捕获sys.exit的code，在所有退出点统一写日志(含exit码)。
# 手动侧自埋点·fail-open不阻塞。
def _guard_log_exit(rc):
    try:
        import subprocess as _sp
        _sp.Popen(["python3", os.path.expanduser("[记忆共享中心]/脚本中心/guard_invocation_logger.py"),
                   "--guard", "platform_adaptation_check",
                   "--source", os.environ.get("GUARD_TRIGGER_SOURCE", "hook_auto"),
                   "--exit", str(rc),
                   "--detail", "self-instrumented"],
                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    except Exception:
        pass
from datetime import datetime
# yaml 延迟导入（hermes 专用·2026-08-22 v0.7 修）：顶层导入在无 yaml 环境直接
# ModuleNotFoundError exit 1——违反"失败默认放行"设计原则（本机 python3 实测崩）

SETTINGS = os.path.expanduser("~/.workbuddy/settings.json")
WBAI_SETTINGS = os.path.expanduser("~/.workbuddy-ai/settings.json")
QODER_SETTINGS = os.path.expanduser("~/.qoder/settings.json")
QODERCN_SETTINGS = os.path.expanduser("~/.qoder-cn/settings.json")
HERMES_CONFIG = os.path.expanduser("~/.hermes/config.yaml")
ZCODE_CONFIG = os.path.expanduser("~/.zcode/cli/config.json")
AUTOCLAW_CONFIG = os.path.expanduser("~/.openclaw-autoclaw/openclaw.json")
AUTOCLAW_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/route_autoclaw_patrol.sh"
)
AUTOCLAW_INJECT_PLUGIN = os.path.expanduser(
    "~/.openclaw-autoclaw/extensions/buluotuo-route-inject/index.js"
)
LOBSTERAI_CONFIG = os.path.expanduser(
    "~/Library/Application Support/LobsterAI/openclaw/state/openclaw.json"
)  # LobsterAI 运行时配置（macOS 应用标准路径·非 ~/.lobsterai——2026-08-22 实测可读）
LOBSTERAI_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/route_lobsterai_patrol.sh"
)
LOBSTERAI_HOOKS_DIR = os.path.expanduser(
    "~/Library/Application Support/LobsterAI/openclaw/state/hooks"
)
TRAEWORK_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/route_traework_patrol.sh"
)  # Trae Work 运行时接入源（无 CC 式 hooks 平台边界·守卫全挂 patrol 拉模式·实盘可读）
DOUBAOWORK_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/route_doubaowork_patrol.sh"
)  # 豆包办公运行时接入源（无 hooks+无 session_memory 平台边界·仅 2 个文件级守卫可机械执行·patrol 拉模式·实盘可读）
DOUBAOWORK_HEARTBEAT = os.path.expanduser(
    "[记忆共享中心]/脚本中心/.patrol/last_run_doubaowork.ts"
)  # 豆包办公巡逻心跳（执行证据校验路径·不读配置文件·读心跳新鲜度≤60min）
DSH_PLUGIN = os.path.expanduser(
    "[记忆共享中心]/脚本中心/five-layer-memory/src/index.js"
)
SSOT = os.path.expanduser(
    "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/04-跨端接入指南.md"
)
LOG = os.path.expanduser(
    "[记忆共享中心]/脚本中心/logs/platform_adaptation_check.log"
)

# 11-Hook 清单（SSOT §二·七 真相源·分母统一为 11·含 crossend_guard·2026-08-26 你拍板 12
#   → 2026-09-12 起 11：l3_conclusion_guard 全端永久关闭移出清单，仿 reply_format_guard 全局移除先例）
# crossend_guard 定位：跨工具中立守卫（多工具共居家目录均需·非 Qoder 专属）
# 分母口径规则：所有平台统一分母 = 11（含 crossend）·🔴待支持计入分母·N/A排除分母
HOOKS = [
    ("crossend_guard.py", "SessionStart", True, "跨工具中立·多工具共居家目录均需·2026-08-26 你拍板统一分母"),
    ("route_inject_prompt.py", "UserPromptSubmit", True, ""),
    ("route_miss_feeder.py", "UserPromptSubmit", True, ""),
    ("kb_inject_prompt.py", "UserPromptSubmit", True, ""),
    ("route_unknown_unknown.py", "Stop", True, ""),
    ("audit_search_kb.py", "Stop", True, ""),
    ("route_audit.py", "Stop", True, ""),
    ("route_guard_audit.py", "Stop", True, ""),
    # reply_format_guard.py 已 ⛔合法停用（2026-08-26 皮叔令"完全删除"·替代方案=core-soul.md 常驻注入）
    # l3_conclusion_guard.py 已 ⛔永久关闭（2026-09-05 你令·2026-09-12 全端下线：Stop 正则误判污染回复=伪确定性类别错误，
    #   判据见 守卫编写规范 §3.4·扩「呈现格式禁拦律」）→ 移出分母，对齐 reply_format_guard 全局移除先例
    ("feedback_detect.py", "Stop", True, ""),
    ("rule_three_layer_guard.py", "Stop", True, ""),
    ("card_id_guard.py", "Stop", True, "AI学习库立场卡编号防撞·hook 模式 exit 0 放行"),
]

# 平台级合法停用（⛔排除分母·端特例版·对齐 reply_format 全局移除先例）：
# zcode：l3_conclusion_guard 2026-09-05 你令永久关闭（Stop 正则误判污染回复·伪确定性=反模式6/7
#   ——zcode_config_guard.py BASELINE 注释同源）——非"未接入"，是拍板停用→不计 zcode 分母
SRC_EXCLUDED = {
    # zcode 的 l3 端级排除已上收为全局（l3 于 2026-09-12 移出 HOOKS）→ 死配置清除
}


def log_line(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except Exception:
        pass


def load_settings():
    try:
        with open(SETTINGS) as f:
            return json.load(f)
    except Exception:
        return None


def classify_entries(settings):
    """按「产品会不会执行」把挂载条目分成三类，不再混为一谈。

    返回 (strict, unverified, dead)，均为 [(event, command), ...]：
      strict     —— 包裹形态且条目 type=="command"：唯一被证明会执行的形态。
      unverified —— 有 hooks 包裹但条目缺 type（或 type 非 command）：该形态在各端是否执行未实测。
      dead       —— 扁平形态（事件数组条目直接带 command·无 hooks 包裹）：
                    Qoder CN 实测「不报错·不执行·无痕迹」（9 条死形态复活前后回执对比）。
    2026-08-30 根治：旧实现只查命令子串，把 dead 计入"已挂载"→面板全绿而产品半数没跑。
    """
    strict, unverified, dead = [], [], []
    hooks_root = settings.get("hooks", {})
    # ZCode 配置文件形态：hooks.events.<Event>（分组在 events 下）；CC 形态直挂 hooks.<Event>。
    # 兼容取两者并集——无 events 键的平台（workbuddy/qoder）行为不变。
    for evt in ("SessionStart", "UserPromptSubmit", "Stop"):
        evt_entries = list(hooks_root.get(evt, [])) + list(
            hooks_root.get("events", {}).get(evt, [])
        )
        for h in evt_entries:
            if "hooks" in h:
                for x in h["hooks"]:
                    cmd = x.get("command", "")
                    if x.get("type") == "command":
                        strict.append((evt, cmd))
                    else:
                        unverified.append((evt, cmd))
            elif "command" in h:
                dead.append((evt, h["command"]))
    return strict, unverified, dead


def match_hooks(cmds):
    return {name for name, _, _, _ in HOOKS if any(name in c for _, c in cmds)}


def actual_mounted(settings):
    """返回 (mounted, dead_names, unverified_names)。

    mounted = strict ∪ unverified（计入分子——unverified 无"它是死的"证据，⛔不假红）。
    dead_names / unverified_names 只保留"该脚本仅由这一非标准形态支撑"的项——
    即真正的静默风险点，供调用方单独报警，⛔不静默计入也不静默丢弃。
    """
    strict, unverified, dead = classify_entries(settings)
    counted = match_hooks(strict) | match_hooks(unverified)
    dead_only = match_hooks(dead) - counted
    unverified_only = match_hooks(unverified) - match_hooks(strict)
    return counted, dead_only, unverified_only


def documented_rate(col=3):
    """从 SSOT §二·七 接入率行提取指定平台列（col=1 起·与表头列序一致）。

    col 1=Qoder Desktop, 2=Qoder CN, 3=WorkBuddy, 4=AutoClaw, 5=DSH,
    6=LobsterAI, 7=Trae Work, 8=Hermes（9=ZCode）—— 与表头列序一致。
    2026-08-22 修（你点名"登记三件套做完仍报漂移"根因）：旧实现只匹配 **N/M** 星号包裹值，
    但 SSOT 接入率行仅少数列带星号（AutoClaw/DSH/Trae Work 加粗）→ 列错位/越界。
    改按表头「Hook 脚本」行解析平台名各列索引，再取接入率行对应单元格——与 panel_snapshot 同款
    单元格分割（以表格列序为真相源·不依赖星号格式·永不漂移）。
    """
    try:
        txt = open(SSOT, encoding="utf-8").read()
    except Exception:
        return None
    lines = txt.splitlines()
    # ① 表头行（含 "Hook 脚本"）→ 平台名列序（col 从 1 起=第 1 个平台列）
    header = None
    for i, line in enumerate(lines):
        if "Hook 脚本" in line and line.strip().startswith("|"):
            header = i
            break
    if header is None:
        return None
    # ② 接入率行（表头之后的含 "接入率" 的表格行）
    rate_cells = None
    for line in lines[header + 1:]:
        if "接入率" in line and line.strip().startswith("|"):
            rate_cells = [c.strip() for c in line.strip().strip("|").split("|")]
            break
    if rate_cells is None:
        return None
    # ③ 对齐：表头首列="Hook 脚本"，接入率行首列="接入率"——平台数据从索引1起，两端一致
    # rate_cells[col] = 目标平台列（第 col 个平台索引即 col，因索引0是行名）
    if col < len(rate_cells):
        raw = rate_cells[col]
        m = re.search(r"(\d+)/\d+", raw)
        return m.group(1) if m else None
    return None


def hermes_expected_from_ssot():
    """解析 §二·七 接入状态表 Hermes 列，返回 {hook脚本名: 状态}。

    真相源=§二·七（脚本只解析不内联）。Hermes 列是每行末列（管道分隔最后一格）。
    状态取该行 Hermes 列首字符：✅=已挂 / ❌=未挂 / ⚠️=部分。
    注意：表里括号为全角（（Stop）），正则须匹配全角。
    """
    try:
        txt = open(SSOT, encoding="utf-8").read()
    except Exception:
        return None
    hook_names = [h[0] for h in HOOKS]
    result = {}
    for line in txt.splitlines():
        m = re.match(r"\|\s*([\w]+\.py)\s*（", line)  # 全角括号（
        if not m or m.group(1) not in hook_names:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3:
            continue
        # markdown 表格行尾是 `|`，split("|") 末元素为空串；
        # 倒数第二格才是最后一列数据（Hermes 列）。
        hermes_cell = cells[-2] if cells[-1] == "" else cells[-1]
        result[m.group(1)] = hermes_cell
    if not result:
        log_line("[platform_adaptation_check:hermes] §二·七 Hermes 列解析为空→疑似SSOT结构变更·需人工核对(非静默放行)")
    return result if result else None


def hermes_actual_plugins():
    """读 ~/.hermes/config.yaml 的 plugins.enabled（机械提取事实挂载）。"""
    try:
        import yaml  # 延迟导入：仅 hermes 链路需要，无 yaml 环境不影响其他端
        with open(HERMES_CONFIG) as f:
            cfg = yaml.safe_load(f)
        enabled = cfg.get("plugins", {}).get("enabled", []) or []
        return set(enabled)
    except Exception:
        return None


def check_hermes():
    """Hermes 端 drift 校验（跨工具中立·守 Hook 三纪律）。

    校验逻辑分两层（避免脆弱的 hook→plugin 1:1 映射，守真相所有权）：
      1. 核心标志自检：§二·七 明确记 Hermes 核心接入=route-audit-hook（on_session_end
         承载 route_audit/route_guard_audit/route_unknown_unknown 三能力）。检查该插件
         是否在 config.yaml plugins.enabled——这是机械可验证的事实。
      2. 定性对账：把 §二·七 Hermes 列所有 ✅ 的 Hook 清单输出到日志，
         供 growth-box/月报消费（填值权归脚本，AI 只回显）。
    不内联"哪些 hook 由哪个插件承载"——那是会变的实现细节，真相源在 §二·七。
    """
    actual = hermes_actual_plugins()
    if actual is None:
        log_line("[platform_adaptation_check:hermes] config.yaml 读取失败→exit0放行")
        return 0

    # 层1：核心标志自检
    core = "route-audit-hook"
    drift = []
    if core not in actual:
        drift.append(f"核心接入插件{core}未在 plugins.enabled（Hermes 审计链路断）")

    # 层2：定性对账（§二·七 ✅ 清单→日志，供下游消费）
    expected = hermes_expected_from_ssot()
    documented_ok = []
    if expected:
        for hook, cell in expected.items():
            if cell.startswith("✅"):
                documented_ok.append(hook)
    log_line(
        f"[对账] Hermes 实测挂载={sorted(actual)} | §二·七文档✅Hook={documented_ok}"
    )

    if drift:
        msg = f"[DRIFT] Hermes: {' | '.join(drift)}"
        print(msg)
        log_line(msg)
    else:
        log_line(f"[OK] Hermes 核心接入完好 {sorted(actual)}（✅Hook={len(documented_ok)}项·详见对账）")
    return 0


def dsh_actual_mounted():
    """读 DSH 插件 index.js 实盘：STOP_GUARDS 数组（Stop 类）+ pre-step 4 通道。

    真相源=插件源码本身（DSH 走插件不走 settings.json·§3.0 件②机械化）。
    STOP_GUARDS 行级解析（遇独立 ] 行终止——args 内联 ] 会提前截断·panel_snapshot v0.6 同款先例）。
    pre-step 通道按调用模式机械判定（变量名出现在 spawn/spawnGetStdout 调用）。
    ⚠️ 2026-09-10 增 dsh_title_namer（第 4 通道·对话标题统一命名·皮叔拍板跨工具同步）——
       该通道不在 13-Hook 清单内，不进接入率分母（新机制首期登记·口径变更待你拍板）；
       此处登记仅让实盘机械可读（幽灵挂载根治精神：文档↔实盘双向可验）。
    返回 set(13-Hook 清单口径挂载名 + pre-step 观测通道) 或 None（读不到）。
    """
    try:
        with open(DSH_PLUGIN, encoding="utf-8") as f:
            src = f.read()
    except Exception:
        return None
    mounted = set()
    seg_lines = []
    for line in src.split("STOP_GUARDS", 1)[1].splitlines():
        if line.strip().startswith("]") and "script:" not in line:
            break
        seg_lines.append(line)
    seg = "\n".join(seg_lines)
    for name, _, _, _ in HOOKS:
        if name in seg:
            mounted.add(name)
    pre_step_calls = {
        "route_miss_feeder.py": ("spawn('python3', [missFeeder", 'spawn("python3", [missFeeder'),
        "route_inject_prompt.py": ("spawnGetStdout(injectPrompt",),
        "kb_inject_prompt.py": ("spawnGetStdout(kbInject",),
        # 2026-09-10 新增·第 4 通道（对话标题统一命名·跨平台共享机制·首批 WB/DSH 接入）
        "dsh_title_namer.py": ("spawn('python3', [titleNamer", 'spawn("python3", [titleNamer'),
    }
    for hook, patterns in pre_step_calls.items():
        if any(p in src for p in patterns):
            mounted.add(hook)
    return mounted


def check_dsh(fix=False):
    """DSH 端 drift 校验（v0.7·幽灵挂载根治：文档声称↔插件实盘机械对账）。

    分母=11（13-Hook 清单 - crossend N/A - reply_format ⛔合法停用）。
    依据 SSOT §二·七 分母口径注记 ①排除分母：crossend（N/A·DSH 无 Qoder 式跨端场景）
    + reply_format_guard（皮叔 2026-08-13 决策·pre-step 预防式 SOUL 契约注入已覆盖其职责·
    事后反馈注入打乱回复节奏·2026-08-16 从 STOP_GUARDS 移除·⛔合法停用排除分母·见 v1.3.14）。
    dsh_session_anomaly_guard 系 DSH 专属附加守卫，不在 13-Hook 分母内（+1 口径归进度看板管）。
    """
    mounted = dsh_actual_mounted()
    if mounted is None:
        log_line("[platform_adaptation_check:dsh] 插件 index.js 读取失败→exit0放行")
        return 0
    # DSH 专属合法停用排除（对齐哲学文件分母口径 ①排除分母：⛔合法停用+N/A·各平台自查自己列）
    DSH_EXCLUDED = {"crossend_guard.py", "reply_format_guard.py"}
    applicable = [h for h in HOOKS if h[0] not in DSH_EXCLUDED]
    denominator = len(applicable)
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(5)  # DSH 列 = col 5
    detail = " | ".join(
        f"{n}:{'✅' if n in mounted else '❌'}" for n, _, _, _ in applicable
    )
    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] dsh 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 DSH 列与插件实盘脱节（幽灵挂载检查·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("dsh", yes, denominator, 5)
            missing = [n for n, _, _, _ in applicable if n not in mounted]
            if missing:
                print(f"[SUGGEST] dsh 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 STOP_GUARDS)")
                log_line(f"[SUGGEST] dsh 未挂 {missing}")
    else:
        log_line(f"[OK] dsh 接入率 {rate} 无漂移（{detail}）")
    return 0


def autoclaw_actual_mounted():
    """读 AutoClaw 实盘：route_autoclaw_patrol.sh（patrol 守卫清单·唯一接入点）
    + openclaw.json（hooks/plugins enabled）+ buluotuo-route-inject 插件（kb_inject v0.3）。

    真相源=运行时文件本身（对齐 dsh_actual_mounted 读源码先例·幽灵挂载根治）。
    patrol 脚本 grep run_guard 行机械判定（⛔不内联清单——脚本增删守卫此处自动跟随）。
    返回 set(13-Hook 清单口径挂载名) 或 None（读不到）。
    """
    mounted = set()
    try:
        patrol_src = open(AUTOCLAW_PATROL, encoding="utf-8").read()
    except Exception:
        return None
    # patrol 守卫（run_guard <name> 调用行→映射 13-Hook 清单名）
    patrol_map = {
        "route_audit": "route_audit.py",
        "l3_conclusion": "l3_conclusion_guard.py",
        "reply_format": "reply_format_guard.py",
        "guard_audit": "route_guard_audit.py",
        "unknown_unknown": "route_unknown_unknown.py",
        "audit_search_kb": "audit_search_kb.py",
        "feedback_detect": "feedback_detect.py",
        "rule_three_layer": "rule_three_layer_guard.py",
        "card_id": "card_id_guard.py",
        "crossend": "crossend_guard.py",
    }
    for alias, hook in patrol_map.items():
        if re.search(rf"\brun_guard\s+{alias}\b", patrol_src):
            mounted.add(hook)
    # 配置核心项（openclaw.json hooks/plugins enabled）
    try:
        cfg = json.loads(open(AUTOCLAW_CONFIG, encoding="utf-8").read())
    except Exception:
        cfg = None
    if cfg is not None:
        try:
            if (
                cfg.get("plugins", {})
                .get("entries", {})
                .get("buluotuo-route-inject", {})
                .get("enabled")
            ):
                mounted.add("route_inject_prompt.py")
        except Exception:
            pass
        try:
            if (
                cfg.get("hooks", {})
                .get("internal", {})
                .get("entries", {})
                .get("buluotuo-miss-feeder", {})
                .get("enabled")
            ):
                mounted.add("route_miss_feeder.py")
        except Exception:
            pass
    # kb_inject：插件 v0.3 内 KB_INJECT 转发（同一 before_prompt_build 管道）
    try:
        plugin_src = open(AUTOCLAW_INJECT_PLUGIN, encoding="utf-8").read()
        if "kb_inject_prompt.py" in plugin_src:
            mounted.add("kb_inject_prompt.py")
    except Exception:
        pass
    return mounted


def check_autoclaw(fix=False):
    """AutoClaw 端 drift 校验（2026-08-22 第 7 端机械校验·幽灵挂载根治）。

    分母=13（crossend 适用——2026-07-28 AutoClaw openclaw.json 将 workspace 指回家目录根
    事故肇事方·patrol 降级承载无 SessionStart 事件）。专属守卫 autoclaw_gateway_guard 系
    AutoClaw 附加守卫，不在 13-Hook 分母内（+1 口径归进度看板管）。
    """
    mounted = autoclaw_actual_mounted()
    if mounted is None:
        log_line("[platform_adaptation_check:autoclaw] patrol/配置读取失败→exit0放行")
        return 0
    denominator = len(HOOKS)  # 13：crossend 适用（历史事故肇事方）
    yes = sum(1 for n, _, _, _ in HOOKS if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(4)  # AutoClaw 列 = col 4
    detail = " | ".join(
        f"{n}:{'✅' if n in mounted else '❌'}" for n, _, _, _ in HOOKS
    )
    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] autoclaw 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 AutoClaw 列与实盘脱节（幽灵挂载检查·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("autoclaw", yes, denominator, 4)
            missing = [n for n, _, _, _ in HOOKS if n not in mounted]
            if missing:
                print(f"[SUGGEST] autoclaw 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 patrol/插件)")
                log_line(f"[SUGGEST] autoclaw 未挂 {missing}")
    else:
        log_line(f"[OK] autoclaw 接入率 {rate} 无漂移（{detail}）")
    return 0


def lobsterai_actual_mounted():
    """读 LobsterAI 实盘：route_lobsterai_patrol.sh（patrol 守卫清单·唯一接入点）
    + openclaw.json plugins.allow（route-inject/kb-inject 专属插件）+ state/hooks 目录（实时 hook）。

    真相源=运行时文件本身（对齐 dsh/autoclaw 读源码先例·幽灵挂载根治）。
    LobsterAI 走 macOS 应用标准配置路径（~/Library/Application Support/LobsterAI/），
    非 ~/.lobsterai——2026-08-22 实测完全可读，推翻了"运行时不可见"旧判定（SSOT 因此改口）。
    patrol 脚本 grep run_guard/run_guard_standalone 行机械判定（⛔不内联清单）。
    返回 set(13-Hook 清单口径挂载名) 或 None（读不到 patrol）。
    """
    # ① patrol 守卫清单（循环内 run_guard + 循环外 run_guard_standalone——LobsterAI 两种都有）
    try:
        patrol_src = open(LOBSTERAI_PATROL, encoding="utf-8").read()
    except Exception:
        return None
    mounted = set()
    patrol_map = {
        "route_audit": "route_audit.py",
        "l3_conclusion": "l3_conclusion_guard.py",
        "reply_format": "reply_format_guard.py",
        "guard_audit": "route_guard_audit.py",
        "unknown_unknown": "route_unknown_unknown.py",
        "audit_search_kb": "audit_search_kb.py",
        "feedback_detect": "feedback_detect.py",
        "rule_three_layer": "rule_three_layer_guard.py",
        "card_id": "card_id_guard.py",
    }
    for alias, hook in patrol_map.items():
        # 循环内是 run_guard，循环外是 run_guard_standalone——两者都算实挂；
        # 守卫名后常带 _guard 后缀（如 rule_three_layer_guard）→ 别名后可选 (?:_guard)?
        # （若只用 \b 在 "_" 处不构成词边界 → run_guard_standalone 行永不命中·2026-08-22 实测抓漏）
        if re.search(rf"\brun_guard(?:_standalone)?\s+{alias}(?:_guard)?\b", patrol_src):
            mounted.add(hook)
    # ② openclaw.json plugins.allow（专属注入插件是否放行）
    try:
        cfg = json.loads(open(LOBSTERAI_CONFIG, encoding="utf-8").read())
    except Exception:
        cfg = None
    if cfg is not None:
        allowed = cfg.get("plugins", {}).get("allow", []) or []
        if "lobsterai-route-inject" in allowed:
            mounted.add("route_inject_prompt.py")
        if "lobsterai-kb-inject" in allowed:
            mounted.add("kb_inject_prompt.py")
    # ③ state/hooks 目录（实时 hook：miss-feeder 是唯一对应 13-Hook 清单一条的）
    try:
        if os.path.isdir(os.path.join(LOBSTERAI_HOOKS_DIR, "lobsterai-miss-feeder")):
            mounted.add("route_miss_feeder.py")
    except Exception:
        pass
    return mounted


def check_lobsterai(fix=False):
    """LobsterAI 端 drift 校验（2026-08-22 第 8 端机械校验·幽灵挂载根治）。

    分母=12（13-Hook 清单 - crossend N/A——LobsterAI 无 SessionStart 事件·同 WorkBuddy/zcode/dsh）。
    lobsterai_session_anomaly_guard 系 LobsterAI 专属附加守卫，不在 13-Hook 分母内（+1 口径归看板管）。
    """
    mounted = lobsterai_actual_mounted()
    if mounted is None:
        log_line("[platform_adaptation_check:lobsterai] patrol 读取失败→exit0放行")
        return 0
    applicable = [h for h in HOOKS if h[0] != "crossend_guard.py"]
    denominator = len(applicable)
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(6)  # LobsterAI 列 = col 6
    detail = " | ".join(
        f"{n}:{'✅' if n in mounted else '❌'}" for n, _, _, _ in applicable
    )
    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] lobsterai 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 LobsterAI 列与实盘脱节（幽灵挂载检查·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("lobsterai", yes, denominator, 6)
            missing = [n for n, _, _, _ in applicable if n not in mounted]
            if missing:
                print(f"[SUGGEST] lobsterai 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 patrol/插件)")
                log_line(f"[SUGGEST] lobsterai 未挂 {missing}")
    else:
        log_line(f"[OK] lobsterai 接入率 {rate} 无漂移（{detail}）")
    return 0


def traework_actual_mounted():
    """读 Trae Work 实盘：route_traework_patrol.sh（patrol 守卫清单·唯一接入点）。

    Trae Work 无 CC 式 hooks（无 SessionStart/UserPromptSubmit 事件·平台边界），
    守卫全部以 patrol 拉模式挂载（系统 crontab 30min 承载）→ 真相源=patrol 脚本本身
    （对齐 dsh/autoclaw/lobsterai 读源码先例·2026-08-22 第 9 端机械校验·根治"自签例外"）。
    patrol 脚本 grep run_guard/run_guard_standalone 行机械判定（⛔不内联清单）。
    返回 set(13-Hook 清单口径挂载名·不含专属) 或 None（读不到 patrol）。
    """
    try:
        patrol_src = open(TRAEWORK_PATROL, encoding="utf-8").read()
    except Exception:
        return None
    mounted = set()
    patrol_map = {
        "route_audit": "route_audit.py",
        "guard_audit": "route_guard_audit.py",
        "audit_search_kb": "audit_search_kb.py",
        "rule_three_layer": "rule_three_layer_guard.py",
        "card_id": "card_id_guard.py",
    }
    for alias, hook in patrol_map.items():
        # 循环内 run_guard 转录类 + 循环外 run_guard_standalone 降级类都算实挂
        if re.search(rf"\brun_guard(?:_standalone)?\s+{alias}(?:_guard)?\b", patrol_src):
            mounted.add(hook)
    return mounted


def check_traework(fix=False):
    """Trae Work 端 drift 校验（2026-08-22 第 9 端机械校验·根治"自签例外"）。

    诚实分母=12（13-Hook - crossend N/A 唯一排除·2026-08-22 分母纠偏，推翻 v1.3.18 自造 6/6）：
      crossend N/A（无跨端场景·设计不适用）→ 唯一排除分母
      3 入站改写（route_inject/miss_feeder/kb_inject·无 UserPromptSubmit 事件/插件点）+ 4 无转录
      （l3/reply/unknown_unknown/feedback·摘要级审计）→ 🔴待支持·计入分母（功能装不上·非排除）
      实接共享 = 5 降级守卫（patrol 实挂·route_audit/guard_audit/audit_search_kb/rule_three/card_id）
      → 接入率 5/12 (42%)；专属 session_memory_quality_guard 另计 +1 不进共享比值。
      对账 SSOT §二·七 Trae Work 列（col 7·5/12）。
    """
    mounted = traework_actual_mounted()
    if mounted is None:
        log_line("[platform_adaptation_check:traework] route_traework_patrol.sh 读取失败→exit0放行")
        return 0
    try:
        patrol_src = open(TRAEWORK_PATROL, encoding="utf-8").read()
    except Exception:
        patrol_src = ""
    # 专属守卫 session_memory_quality_guard（Trae Work 专属·计入该接分母）
    has_exclusive = re.search(
        r"\brun_guard(?:_standalone)?\s+session_memory_quality_guard\b", patrol_src
    )
    applicable = [h for h in HOOKS if h[0] in
                  {"route_audit.py", "route_guard_audit.py", "audit_search_kb.py",
                   "rule_three_layer_guard.py", "card_id_guard.py"}]
    denominator = len([h for h in HOOKS if h[2]])  # 12：13-Hook - crossend(N/A)·3入站+4无转录🔴计入不排除
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)  # 实接共享=5·专属另计不含比值
    rate = f"{yes}/{denominator}"
    doc = documented_rate(7)  # Trae Work 列 = col 7·5/12
    detail = " | ".join(
        f"{n}:{'✅' if n in mounted else '❌'}" for n, _, _, _ in applicable
    )
    detail += " | 🔴待支持(计入分母):route_inject/miss_feeder/kb_inject/l3/reply/unknown_unknown/feedback"
    detail += f" | 专属 session_memory_quality_guard.py:{'✅' if has_exclusive else '❌'}(另计)"
    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] traework 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 Trae Work 列与实盘脱节（幽灵挂载检查·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("traework", yes, denominator, 7)
            missing = [n for n, _, _, _ in applicable if n not in mounted]
            if not has_exclusive:
                missing.append("session_memory_quality_guard.py(专属)")
            if missing:
                print(f"[SUGGEST] traework 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 patrol)")
                log_line(f"[SUGGEST] traework 未挂 {missing}")
    else:
        log_line(f"[OK] traework 接入率 {rate} 无漂移（{detail}）")
    return 0


def doubaowork_actual_mounted():
    """读豆包办公实盘：route_doubaowork_patrol.sh（patrol 守卫清单·唯一接入点）。

    豆包办公无 CC 式 hooks（无 SessionStart/UserPromptSubmit/Stop 事件·平台边界），
    无 session_memory jsonl（会话数据在平台内部·不在文件系统）→
    需要 transcript 的 6 个守卫无法机械执行，仅 2 个文件级守卫可 patrol 拉模式挂载。
    真相源=patrol 脚本本身（对齐 traework 读源码先例·2026-08-25 第10端机械校验·执行证据校验路径）。
    patrol 脚本 grep run_guard_standalone 行机械判定（⛔不内联清单）。
    返回 set(13-Hook 清单口径挂载名) 或 None（读不到 patrol）。
    """
    try:
        patrol_src = open(DOUBAOWORK_PATROL, encoding="utf-8").read()
    except Exception:
        return None
    mounted = set()
    patrol_map = {
        "rule_three_layer": "rule_three_layer_guard.py",
        "card_id": "card_id_guard.py",
    }
    for alias, hook in patrol_map.items():
        if re.search(rf"\brun_guard_standalone\s+{alias}(?:_guard)?\b", patrol_src):
            mounted.add(hook)
    return mounted


def check_doubaowork(fix=False):
    """豆包办公端 drift 校验（2026-08-25 第10端机械校验·执行证据校验路径·第一性原理修正）。

    诚实分母=12（13-Hook - crossend N/A 唯一排除·2026-08-25 第一性原理修正，推翻原 8/12）：
      crossend N/A（Qoder 系专属·设计不适用）→ 唯一排除分母
      3 入站改写（route_inject/miss_feeder/kb_inject·无 UserPromptSubmit 事件）+ feedback_detect
      （无完整转录）→ 🔴待支持·计入分母（功能装不上·非排除）
      6 个需要 transcript 的守卫（route_audit/audit_search_kb/route_guard_audit/unknown_unknown/
      reply_format/l3_conclusion）→ 🟡软约束（Skill 内校验 AI 自觉·非机械执行·不计入分子）
      实接机械执行 = 2 个文件级守卫（patrol 实挂·rule_three_layer/card_id）
      → 接入率 2/12 (17%)。
      对账 SSOT §二·七 豆包办公列（col 10·2/12）。

    执行证据校验路径（创新·不读配置文件）：
      不读 settings.json（豆包办公无配置文件在文件系统），读巡逻脚本执行产物+心跳新鲜度（≤60min）。
      配置了≠执行了，执行了=真的执行了——执行证据比配置声明更可靠（第一性原理）。
    """
    mounted = doubaowork_actual_mounted()
    if mounted is None:
        log_line("[platform_adaptation_check:doubaowork] route_doubaowork_patrol.sh 读取失败→exit0放行")
        return 0
    # 心跳新鲜度检查（执行证据·≤60min=巡逻在运行）
    heartbeat_fresh = False
    try:
        with open(DOUBAOWORK_HEARTBEAT, encoding="utf-8") as f:
            ts_str = f.read().strip()
        ts = datetime.fromisoformat(ts_str)
        age = (datetime.now() - ts).total_seconds()
        heartbeat_fresh = age <= 3600  # ≤60min
    except Exception:
        heartbeat_fresh = False
    applicable = [h for h in HOOKS if h[0] in
                  {"rule_three_layer_guard.py", "card_id_guard.py"}]
    denominator = len([h for h in HOOKS if h[2]])  # 12：13-Hook - crossend(N/A)·3入站+feedback🔴计入不排除·6转录类🟡软约束不计分子
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)  # 实接机械执行=2
    rate = f"{yes}/{denominator}"
    doc = documented_rate(10)  # 豆包办公列 = 表头第11列(索引10)·2/12（documented_rate 按表头列序解析·不依赖星号格式）
    detail = " | ".join(
        f"{n}:{'✅' if n in mounted else '❌'}" for n, _, _, _ in applicable
    )
    detail += " | 🟡软约束(AI自觉·不计分子):route_audit/audit_search_kb/route_guard_audit/unknown_unknown/reply_format/l3_conclusion"
    detail += " | 🔴待支持(计入分母):route_inject/miss_feeder/kb_inject/feedback_detect"
    detail += f" | 心跳:{'✅新鲜≤60min' if heartbeat_fresh else '❌过期/缺失(巡逻未运行)'}"
    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] doubaowork 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 豆包办公列与实盘脱节（执行证据校验·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("doubaowork", yes, denominator, 6)
            missing = [n for n, _, _, _ in applicable if n not in mounted]
            if missing:
                print(f"[SUGGEST] doubaowork 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 patrol)")
                log_line(f"[SUGGEST] doubaowork 未挂 {missing}")
    else:
        log_line(f"[OK] doubaowork 接入率 {rate} 无漂移（{detail}）")
    return 0


def fix_ssot_rate(args_src, yes, denominator, col):
    """--fix 模式：自动同步 SSOT §二·七 接入率行（低风险·可逆·机械替换）。

    同时更新分子和分母（如 13/13 → 12/12），确保分母随 Hook 清单变化。
    高风险场景（settings.json 缺 Hook）仅报告建议，不自动改配置。
    
    列定位方式：与 documented_rate 一致，按表格单元格分割（| 分隔），
    第 col 个平台列 = 目标列（col 从 1 起，索引 0 是行名）。
    """
    try:
        txt = open(SSOT, encoding="utf-8").read()
    except Exception:
        log_line(f"[platform_adaptation_check:fix] SSOT 读取失败→跳过自动修复")
        return False

    lines = txt.splitlines()
    fixed = False
    for i, line in enumerate(lines):
        if "接入率" not in line or not line.strip().startswith("|"):
            continue
        # 按表格单元格分割（与 documented_rate 一致）
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col < len(cells):
            raw = cells[col]
            # 匹配 N/M 模式（不依赖 ** 包裹）
            m = re.search(r"(\d+)/(\d+)", raw)
            if m:
                old_num = m.group(1)
                old_den = m.group(2)
                # 同时更新分子和分母
                if old_num != str(yes) or old_den != str(denominator):
                    new_rate = f"{yes}/{denominator}"
                    # 替换原单元格中的 N/M
                    new_cell = raw[:m.start()] + new_rate + raw[m.end():]
                    cells[col] = new_cell
                    # 重新组装行
                    new_line = "| " + " | ".join(cells) + " |"
                    lines[i] = new_line
                    fixed = True
                    log_line(f"[FIX] {args_src} SSOT 接入率自动同步：{old_num}/{old_den}→{new_rate}")
        break

    if fixed:
        try:
            with open(SSOT, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print(f"[FIXED] {args_src} SSOT §二·七 接入率已自动同步为 {yes}/{denominator}")
            return True
        except Exception:
            log_line(f"[platform_adaptation_check:fix] SSOT 写入失败→跳过")
    return False



def absorb_scan(src_key):
    """FU-79腿（2026-10-02·Qoder CN·皮叔拍板）：本端缺项 × 别端已落地 × 本端形态线索。
    只读显形，⛔不参与分子/判据/exit 码——四动作协议动作 2·3 的机械承接件（v1.3.94 声明的『腿』）。
    数据源=同一张 SSOT 对比表（同源律：与 documented_rate 同表同列序）。"""
    try:
        txt = open(SSOT, encoding="utf-8").read()
    except Exception:
        print("[ABSORB] SSOT 不可读→如实报告读取失败（不谎称零缺口）")
        return 0
    lines = txt.splitlines()
    header_i = None
    for i, l in enumerate(lines):
        if "Hook 脚本" in l and "Qoder Desktop" in l and l.strip().startswith("|"):
            header_i = i
            break
    if header_i is None:
        print("[ABSORB] 表头缺失（形状损坏·非零缺口）")
        return 0
    cols = [c.strip().strip("*").strip() for c in lines[header_i].strip().strip("|").split("|")]
    disp = {"qoder-cn": "Qoder CN", "qoder-desktop": "Qoder Desktop", "hermes": "Hermes",
            "workbuddy": "WorkBuddy", "zcode": "ZCode", "dsh": "DSH", "autoclaw": "AutoClaw",
            "lobsterai": "LobsterAI", "traework": "Trae Work", "doubaowork": "豆包办公",
            "teleagent": "TeleAgent", "catpaw": "CatPaw", "workbuddyai": "WorkBuddy AI",
            "zwork": "Zwork"}.get(src_key, src_key)
    tgt_col = None
    for j, c in enumerate(cols):
        if j > 0 and disp.lower() in c.lower():
            tgt_col = j
            break
    if tgt_col is None:
        print(f"[ABSORB] 列「{disp}」不在表头（表形状变更·判据未随对象演化防线）")
        return 0
    gaps = []
    for l in lines[header_i + 1:]:
        if not l.strip().startswith("|"):
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) <= tgt_col or "接入率" in cells[0]:
            continue
        row = cells[0]
        hook = next((h for h in HOOKS if h[0] in row), None)
        if hook is None:
            continue
        mine = cells[tgt_col]
        if mine.startswith("✅") or "**✅" in mine[:6] or "⛔" in mine or "N/A" in mine or "排除分母" in mine:
            continue
        done_by = [cols[j] for j in range(1, len(cells)) if j != tgt_col and (cells[j].startswith("✅") or cells[j].startswith("**✅"))]
        hints = mine[:60]
        gaps.append((hook[0], hook[1], "、".join(done_by)[:80] or "（无端落地）", hints))
    print(f"[ABSORB] {disp} 缺项 × 别端已落地 × 本端形态线索（只读·不计分子·{len(gaps)} 项）")
    for g in gaps:
        print(f"  - {g[0]}（{g[1]}）｜已落地：{g[2]}｜本端格实录：{g[3]}")
    if not gaps:
        print("  （0 项——若表损坏请以 --src 模式交叉佐证）")
    return 0


def _absorb_selftest():
    """出厂夹具（§3.0·5）：正例抓缺口/不误伤/归属正确 + 变异承重自证（T4）。"""
    import tempfile, io, contextlib
    ok = fail = 0
    fixture = """| Hook 脚本 | Qoder Desktop | Alpha | Beta | Gamma |
|------|------|------|------|
| crossend_guard.py（SessionStart） | ✅ 已挂 | ✅ 已挂 | 🔴 待支持（无事件） | ⛔ N/A 排除分母 |
| kb_inject_prompt.py（UserPromptSubmit） | ✅ | ✅ | ⏳ 待适配 | ✅ |
| card_id_guard.py（Stop） | ✅ | ✅ | ✅ | ✅ |
| 接入率（分母=11） | 11/11 | 2/11 | 1/10 |
"""
    global SSOT
    keep = SSOT
    try:
        fd, p = tempfile.mkstemp(suffix=".md"); os.close(fd)
        SSOT = p; open(p, "w").write(fixture)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            absorb_scan("beta")
        out = buf.getvalue()
        tests = [
            ("T1 抓缺口（crossend 🔴 + kb_inject ⏳ 显形）", "crossend_guard.py" in out and "kb_inject_prompt.py" in out),
            ("T2 不误伤（✅行不报）", "card_id_guard" not in out),
            ("T3 别端落地归属（Alpha 列）", "Alpha" in out),
        ]
        for name, cond in tests:
            print(("✅ " if cond else "❌ ") + name); ok += cond; fail += (not cond)
        os.remove(p)
        fd, p2 = tempfile.mkstemp(suffix=".md"); os.close(fd)
        SSOT = p2; open(p2, "w").write(fixture.replace("✅ 已挂 | 🔴 待支持（无事件） | ⛔", "✅ 已挂 | ✅ 已挂 | ⛔"))
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            absorb_scan("beta")
        mut_ok = ("crossend_guard.py" not in buf2.getvalue()) and ("kb_inject_prompt.py" in buf2.getvalue())
        print(("✅ " if mut_ok else "❌ ") + "T4 变异承重（置假可红）")
        ok += mut_ok; fail += (not mut_ok)
        os.remove(p2)
    finally:
        SSOT = keep
    print(f"_absorb_selftest: {ok} passed / {fail} failed")
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="workbuddy",
                    choices=["workbuddy", "hermes", "qoder-desktop", "qoder-cn", "dsh", "zcode", "autoclaw", "lobsterai", "traework", "doubaowork", "workbuddyai"],
                    help="平台源：workbuddy=读 ~/.workbuddy/settings.json；hermes=读 config.yaml plugins.enabled；qoder-desktop=读 ~/.qoder/settings.json；qoder-cn=读 ~/.qoder-cn/settings.json；dsh=读插件 index.js 实盘（STOP_GUARDS+pre-step）；zcode=读 ~/.zcode/cli/config.json hooks.events 实盘；autoclaw=读 openclaw.json+patrol 实盘（2026-08-22 第7端）；lobsterai=读 openclaw.json plugins.allow+patrol+state/hooks 实盘（2026-08-22 第8端）；traework=读 route_traework_patrol.sh 实盘（2026-08-22 第9端·Trae Work 无 hooks 平台边界·守卫全挂 patrol 拉模式）；doubaowork=读 route_doubaowork_patrol.sh 实盘+心跳（2026-08-25 第10端·豆包办公无 hooks+无 session_memory·仅2文件级守卫可机械执行·执行证据校验路径不读配置文件）；workbuddyai=读 ~/.workbuddy-ai/settings.json（2026-09-11 第18端·WorkBuddy AI 国际版·与国内版同 schema 同代码双发行版）")
    ap.add_argument("--fix", action="store_true",
                    help="自动修复模式：实测接入率与SSOT文档不一致时自动同步文档（低风险）；settings.json 缺 Hook 仅报告建议（高风险）")
    ap.add_argument("--absorb", metavar="SRC", help="FU-79腿：本端缺项×别端已落地 只读显形（不计分子·不改文件）")
    ap.add_argument("--absorb-selftest", action="store_true", help="absorb_scan 出厂夹具+变异承重自证")
    args = ap.parse_args()

    if args.absorb_selftest:
        return _absorb_selftest()
    if args.absorb:
        return absorb_scan(args.absorb)
    if args.src == "hermes":
        return check_hermes()
    if args.src == "dsh":
        return check_dsh(fix=args.fix)
    if args.src == "autoclaw":
        return check_autoclaw(fix=args.fix)
    if args.src == "lobsterai":
        return check_lobsterai(fix=args.fix)
    if args.src == "traework":
        return check_traework(fix=args.fix)
    if args.src == "doubaowork":
        return check_doubaowork(fix=args.fix)

    # 平台参数：配置文件 / SSOT 列 / 分母是否含 crossend（Qoder Desktop/CN 专属适用）
    if args.src == "qoder-desktop":
        cfg_path, col, denom_all = QODER_SETTINGS, 1, True
    elif args.src == "qoder-cn":
        cfg_path, col, denom_all = QODERCN_SETTINGS, 2, True
    elif args.src == "zcode":
        # ZCode（第13端·2026-08-22）：crossend N/A（Qoder 系专属）→ 分母=适用项；
        # ZCode 列=表末第 9 列（documented_rate 按接入率行第 col 个 **N/M 解析）
        cfg_path, col, denom_all = ZCODE_CONFIG, 9, False
    elif args.src == "workbuddyai":
        # WorkBuddy AI 国际版（第 18 端·2026-09-11）：读 ~/.workbuddy-ai/settings.json
        # 列=表末第 13 列；crossend 无 SessionStart 事件 → 计入分母（与国内版同口径）
        cfg_path, col, denom_all = WBAI_SETTINGS, 13, False
    else:
        cfg_path, col, denom_all = SETTINGS, 3, False

    try:
        with open(cfg_path) as f:
            settings = json.load(f)
    except Exception:
        log_line(f"[platform_adaptation_check:{args.src}] 配置读取失败→exit0放行")
        return 0

    mounted, dead_only, unverified_only = actual_mounted(settings)
    # 2026-08-26 你拍板：所有平台统一分母 = 12（含 crossend_guard）
    # crossend_guard 定位：跨工具中立守卫（多工具共居家目录均需）
    # 🔴待支持（因平台功能不支持）计入分母·N/A排除分母
    # 2026-09-12：端级合法停用排除分母（SRC_EXCLUDED·如 zcode 的 l3_conclusion）
    hooks_eff = [h for h in HOOKS if h[0] not in SRC_EXCLUDED.get(args.src, set())]
    denominator = len(hooks_eff)
    yes = sum(1 for n, _, _, _ in hooks_eff if n in mounted)
    applicable_filter = list(range(len(hooks_eff)))
    rate = f"{yes}/{denominator}"

    # 形态告警独立于接入率：接入率对得上不代表挂载会执行。
    # 2026-08-30 根治——旧实现"命令子串命中=已挂载"把扁平死形态算进分子，
    # 造成面板全绿而产品实跑半数没跑（本端 9 条·详见 qodercn_config_guard.py 辖区）。
    if dead_only:
        shape_msg = (
            f"[SHAPE] {args.src} {len(dead_only)} 个 Hook 为扁平死形态"
            f"（事件数组条目缺 hooks:[{{type:\"command\",…}}] 包裹）→ ⛔不计入分子：{sorted(dead_only)} "
            f"—— 产品不报错、不执行、无痕迹；修法=补包裹形态"
        )
        print(shape_msg)
        log_line(shape_msg)
    if unverified_only:
        uv_msg = (
            f"[SHAPE?] {args.src} {len(unverified_only)} 个 Hook 包裹形态缺 type=\"command\""
            f"→ {sorted(unverified_only)} —— 该形态在本端是否被执行未实测，"
            f"暂计入分子（⛔不据本端外推判死），须以本端产品回执证活"
        )
        print(uv_msg)
        log_line(uv_msg)

    doc = documented_rate(col)
    detail = " | ".join(
        f"{hooks_eff[i][0]}:{'✅' if hooks_eff[i][0] in mounted else '❌'}" for i in applicable_filter
    )

    if doc is not None and doc != str(yes):
        msg = (
            f"[DRIFT] {args.src} 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"{cfg_path} 与 SSOT §二·七 脱节，需同步文档（{detail}）"
        )
        print(msg)
        log_line(msg)
        # --fix 模式：低风险自动同步 SSOT 文档
        if args.fix:
            fix_ssot_rate(args.src, yes, denominator, col)
            # 高风险：settings.json 缺 Hook → 仅报告建议，不自动改配置
            missing = [hooks_eff[i][0] for i in applicable_filter if hooks_eff[i][0] not in mounted]
            if missing:
                print(f"[SUGGEST] {args.src} 缺失 Hook：{', '.join(missing)} —— 建议手动补挂（不自动修改配置）")
                log_line(f"[SUGGEST] {args.src} 缺失 {len(missing)} 个 Hook：{missing}")
    else:
        log_line(f"[OK] {args.src} 接入率 {rate} 无漂移（{detail}）")

    return 0


if __name__ == "__main__":
    _rc = 0
    try:
        _rc = main()
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else 0
        # 步2(2026-10-07 v? 报警噪声根治卡·你令彻底做完):检红rc归0——平台契约下 exit≠0专留真崩,
        #   检红可见性=输出红行+台账(_guard_log_exit/.out/patrol log);⛔不减一行红输出。
        if _rc == 1:
            _rc = 0

    except Exception:
        _rc = 0
    finally:
        _guard_log_exit(_rc)
    sys.exit(_rc)

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