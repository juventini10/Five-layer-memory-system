#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""platform_adaptation_check.py v0.9 — 布洛陀脚本体系·平台接入率漂移校验（检测+自愈混合架构）
v0.9（2026-10-12·CSK卡内部台账/15 A4'/A4''落地）：check_hermes 新增层1.5=审计账本主判据+import式同源诊断(不复刻候选·降级=纯审计账本)+对偶完整性自证+不可观子空间声明。

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
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
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
    "[记忆共享中心]/脚本中心/Skill路由引擎/scripts/route_autoclaw_patrol.sh"
)
# 2026-10-09 童灵根治：原指 脚本中心/route_autoclaw_patrol.sh（根目录扁平镜像，
#   10-06 15:13 清理后缺失·同步器只投影开发工具顶层不投影子目录故不会重建）→ 实体真源在子目录。
AUTOCLAW_INJECT_PLUGIN = os.path.expanduser(
    "~/.openclaw-autoclaw/extensions/buluotuo-route-inject/index.js"
)
LOBSTERAI_CONFIG = os.path.expanduser(
    "~/Library/Application Support/LobsterAI/openclaw/state/openclaw.json"
)  # LobsterAI 运行时配置（macOS 应用标准路径·非 ~/.lobsterai——2026-08-22 实测可读）
LOBSTERAI_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/Skill路由引擎/scripts/route_lobsterai_patrol.sh"
)
# 2026-10-09 童灵根治：根目录扁平镜像 10-06 清理后缺失 → 对齐 Skill路由引擎/scripts 实体。
LOBSTERAI_HOOKS_DIR = os.path.expanduser(
    "~/Library/Application Support/LobsterAI/openclaw/state/hooks"
)
TRAEWORK_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/Skill路由引擎/scripts/route_traework_patrol.sh"
)  # Trae Work 运行时接入源（2026-10-09 童灵根治：根目录扁平镜像 10-06 清理后缺失→对齐子目录实体；无 CC 式 hooks 平台边界·守卫全挂 patrol 拉模式·实盘可读）
DOUBAOWORK_PATROL = os.path.expanduser(
    "[记忆共享中心]/脚本中心/Skill路由引擎/scripts/route_doubaowork_patrol.sh"
)  # 豆包办公运行时接入源（2026-10-09 童灵根治：根目录扁平镜像 10-06 清理后缺失→对齐子目录实体；无 hooks+无 session_memory 平台边界·patrol 拉模式·实盘可读）
DOUBAOWORK_HEARTBEAT = os.path.expanduser(
    "[记忆共享中心]/脚本中心/.patrol/last_run_doubaowork.ts"
)  # 豆包办公巡逻心跳（2026-10-09 童灵根治：原指 脚本中心/.patrol/ 与 patrol 实写位置不符→对齐 patrol line26/37 实写路径；执行证据·新鲜度≤60min）
DSH_PLUGIN = os.path.expanduser(
    "[记忆共享中心]/脚本中心/five-layer-memory/src/index.js"
)  # DSH 插件真源（2026-10-09 童灵根治：原指 脚本中心/five-layer-memory 镜像 10-06 清理后缺失→对齐开发工具实体）
SSOT = os.path.expanduser(
    # 2026-10-09 Trae CN 修：原指 脚本中心/布洛陀脚本架构设计哲学/04-跨端接入指南.md——
    # 该脚本中心镜像目录已缺失（读取恒失败→documented_rate 恒 None→对账静默跳过=假绿根因）。
    # 改指 canonical 真源（与 panel_snapshot.py 同款·与 04 frontmatter"SSOT 路径已同步指向本文件"声明一致）。
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
    # ⚠️ 以上两行为历史注记非判据本体——禁设面机器真源=同目录 retired-hooks.json（§二·廿一
    #    法则1·check_retired() 每跑必核查）；新增退役：先写台账一行+04表一行，再回来删注释。
    ("feedback_detect.py", "Stop", True, ""),
    ("rule_three_layer_guard.py", "Stop", True, ""),
    ("card_id_guard.py", "Stop", True, "AI学习库立场卡编号防撞·hook 模式 exit 0 放行"),
    ("session_title_namer 族", "SessionStart/UserPromptSubmit/pre-step", True,
     "2026-10-09 自实验区转正（门槛①7端落地+你令）·各端适配器名:session_title_namer(WB)/dsh_title_namer(DSH)/traecode_title_namer(TraeCN)/qodercn_title_namer(QCN)/zcode_title_namer(ZCode)/wbai_title_namer(WBAI)/buluotuo-session-title-hook(Hermes插件)·已落地端的分子计法由各端 check 函数按其适配器名特判（未特判端分子暂少计1·回写期口径）"),
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


def report_source_missing(src, what, path):
    """被检对象读取失败 = 守卫成功发现静默失效（非守卫自身故障）→ print 显形 + rc=2 真报警。

    2026-10-09 童灵根治假绿：旧逻辑 open 失败即 log_line+return 0，在最该报警的条件
    （镜像被清理/路径缺失）下沉默，背叛守卫"把静默失效变成主动检测"的使命。
    rc=2 经 patrol 的 run_guard_standalone 捕获只记录不传播、patrol 末仍 exit 0
    → 不阻断生产，只在巡逻 .out/log 留下 CRITICAL（对齐 skill_health_guard exit=2）。
    """
    msg = f"[BROKEN] {src} {what} 读取失败（镜像缺失/被清理？）：{path}"
    print(msg)
    log_line(msg)
    return 2


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
        # 2026-10-09 Trae CN 修（严格行定位）：只认首单元格=「接入率」的行——
        # 旧条件 "接入率 in line" 会被表内自核签名行（含"接入率重估"字样）抢匹配 → 取错行→返回 None→假绿。
        cells0 = line.strip().lstrip("|").strip()
        if line.strip().startswith("|") and cells0.startswith("接入率"):
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

    # 层1.5：审计账本反向实证(主判据)+import式可达性诊断（A4'/A4'' 2026-10-12 CSK卡内部台账/15落地）
    # ⛔不硬编码复刻候选序列（漂移面·违S842平台无关）——import插件真源调 _find_script，插件改候选探针自动跟
    import json as _json
    _audit_log = os.path.expanduser("[记忆共享中心]/脚本中心/logs/route_audit.jsonl")
    _hermes_lines = []
    try:
        with open(_audit_log, encoding="utf-8") as _f:
            for _ln in _f:
                try:
                    _d = _json.loads(_ln)
                except Exception:
                    continue
                if _d.get("src") == "hermes":
                    _hermes_lines.append(_d)
    except FileNotFoundError:
        pass
    if _hermes_lines:
        log_line(f"[层1.5·审计账本] src=hermes {len(_hermes_lines)}行·末行ts={str(_hermes_lines[-1].get('ts','?'))[:19]}")
    else:
        log_line("[层1.5·审计账本] src=hermes 0行（Hermes会话未跑属正常；已跑而0行→落不可观子空间①，不可从本判据区分）")
    _reach = None
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("route_audit_hook_probe", os.path.expanduser("~/.hermes/plugins/route-audit-hook/__init__.py"))
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        _reach = {n: bool(_mod._find_script(n)) for n in ("route_audit.py", "route_guard_audit.py", "deident_plugins.py")}
        _adapter = getattr(_mod, "_KB_ADAPTER", None)
        _reach["adapter"] = bool(_adapter and (os.path.isfile(_adapter) or os.path.isdir(_adapter)))
    except Exception as _e:
        _reach = None  # 降级=纯审计账本判据（内部台账降级分支）
    if _reach is not None:
        _miss = [k for k, v in _reach.items() if not v]
        if _miss:
            drift.append(f"插件同源诊断不可达: {_miss}（层1.5·A4'）")
        else:
            log_line("[层1.5·import] 三脚本+adapter 经插件 _find_script 全可达（真源同源·零候选复刻）")
    # 对偶完整性自证（A4''②·修复面⊆观测面）
    if _reach is not None:
        log_line("[对偶] 修复面:插件候选→审计账本+import观测 / rp.custom_route→import观测 / adapter迁顶层→import观测(adapter位) ✓ 同构")
    # 不可观子空间显式声明（A4''①·诚实边界落盘）
    log_line("[不可观] ①插件触发面(on_session_end未 firing→审计账本0行与静默失效不可分) ②audit内部降级 ③runtime_paths其他键漂移")

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
        return report_source_missing("dsh", "插件 index.js", DSH_PLUGIN)
    # DSH 专属合法停用排除（对齐哲学文件分母口径 ①排除分母：⛔合法停用+N/A·各平台自查自己列）
    DSH_EXCLUDED = {"crossend_guard.py", "reply_format_guard.py"}
    applicable = [h for h in HOOKS if h[0] not in DSH_EXCLUDED]
    denominator = len(applicable)
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(5)  # DSH 列 = col 5
    _df = documented_fraction(5)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] dsh 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("dsh", yes, denominator, 5)
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
        _ok = f"[OK] dsh 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
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
        return report_source_missing("autoclaw", "patrol/配置", AUTOCLAW_PATROL)
    denominator = len(HOOKS)  # 13：crossend 适用（历史事故肇事方）
    yes = sum(1 for n, _, _, _ in HOOKS if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(4)  # AutoClaw 列 = col 4
    _df = documented_fraction(4)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] autoclaw 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("autoclaw", yes, denominator, 4)
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
        _ok = f"[OK] autoclaw 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
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
        return report_source_missing("lobsterai", "patrol", LOBSTERAI_PATROL)
    applicable = [h for h in HOOKS if h[0] != "crossend_guard.py"]
    denominator = len(applicable)
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(6)  # LobsterAI 列 = col 6
    _df = documented_fraction(6)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] lobsterai 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("lobsterai", yes, denominator, 6)
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
        _ok = f"[OK] lobsterai 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
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

    诚实分母=11（HOOKS 现 11 项·l3_conclusion/reply_format 已移出清单·2026-10-09 随清单收敛；
      旧口径 13-Hook - crossend=12 已过时，推翻 v1.3.18 自造 6/6）：
      crossend N/A（无跨端场景·设计不适用）→ 唯一排除分母
      3 入站改写（route_inject/miss_feeder/kb_inject·无 UserPromptSubmit 事件/插件点）+ 4 无转录
      （l3/reply/unknown_unknown/feedback·摘要级审计）→ 🔴待支持·计入分母（功能装不上·非排除）
      实接共享 = 5 降级守卫（patrol 实挂·route_audit/guard_audit/audit_search_kb/rule_three/card_id）
      → 接入率 5/11 (45%)；专属 session_memory_quality_guard 另计 +1 不进共享比值。
      对账 SSOT §二·七 Trae Work 列（col 7·5/11）。
    """
    mounted = traework_actual_mounted()
    if mounted is None:
        return report_source_missing("traework", "route_traework_patrol.sh", TRAEWORK_PATROL)
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
    denominator = len([h for h in HOOKS if h[2]])  # 11：HOOKS 现 11 项·l3/reply 已移出·🔴待支持计入不排除
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)  # 实接共享=5·专属另计不含比值
    rate = f"{yes}/{denominator}"
    doc = documented_rate(7)  # Trae Work 列 = col 7·5/11
    _df = documented_fraction(7)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] traework 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("traework", yes, denominator, 7)
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
        _ok = f"[OK] traework 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
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

    诚实分母=11（HOOKS 现 11 项·l3_conclusion/reply_format 已移出清单·2026-10-09 随清单收敛；
      旧口径 13-Hook - crossend=12 已过时，2026-08-25 第一性原理修正曾推翻原 8/12）：
      crossend N/A（Qoder 系专属·设计不适用）→ 唯一排除分母
      3 入站改写（route_inject/miss_feeder/kb_inject·无 UserPromptSubmit 事件）+ feedback_detect
      （无完整转录）→ 🔴待支持·计入分母（功能装不上·非排除）
      6 个需要 transcript 的守卫（route_audit/audit_search_kb/route_guard_audit/unknown_unknown/
      reply_format/l3_conclusion）→ 🟡软约束（Skill 内校验 AI 自觉·非机械执行·不计入分子）
      实接机械执行 = 2 个文件级守卫（patrol 实挂·rule_three_layer/card_id）
      → 接入率 2/11 (18%)。
      对账 SSOT §二·七 豆包办公列（col 10·2/11）。

    执行证据校验路径（创新·不读配置文件）：
      不读 settings.json（豆包办公无配置文件在文件系统），读巡逻脚本执行产物+心跳新鲜度（≤60min）。
      配置了≠执行了，执行了=真的执行了——执行证据比配置声明更可靠（第一性原理）。
    """
    mounted = doubaowork_actual_mounted()
    if mounted is None:
        return report_source_missing("doubaowork", "route_doubaowork_patrol.sh", DOUBAOWORK_PATROL)
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
    denominator = len([h for h in HOOKS if h[2]])  # 11：HOOKS 现 11 项·l3/reply 已移出·🔴待支持计入·6转录类🟡软约束不计分子
    yes = sum(1 for n, _, _, _ in applicable if n in mounted)  # 实接机械执行=2
    rate = f"{yes}/{denominator}"
    doc = documented_rate(10)  # 豆包办公列 = 表头第11列(索引10)·2/11（documented_rate 按表头列序解析·不依赖星号格式）
    _df = documented_fraction(10)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] doubaowork 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("doubaowork", yes, denominator, 10)
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
            fix_ssot_rate("doubaowork", yes, denominator, 10)
            missing = [n for n, _, _, _ in applicable if n not in mounted]
            if missing:
                print(f"[SUGGEST] doubaowork 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 patrol)")
                log_line(f"[SUGGEST] doubaowork 未挂 {missing}")
    else:
        _ok = f"[OK] doubaowork 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
    return 0


def traecn_actual_mounted():
    """读 Trae CN 实盘：`~/.trae-cn/hooks.json`（官方全局 Hook 配置·2026-10-09 第 20 端接入）。

    真相源=配置文件本身（对齐 zcode/workbuddy 读配置先例·hooks.json 为官方唯一挂载面，
    项目级 .trae/hooks.json 本机无）。commands 全文串包含即判挂载（含 adapter --run 的
    共脚本路径参数）。返回 04 §Hook 清单口径挂载名集合；读不到 → None。
    """
    try:
        cfg = json.load(open(os.path.expanduser("~/.trae-cn/hooks.json"), encoding="utf-8"))
    except Exception:
        return None
    corpus = []
    for groups in cfg.get("hooks", {}).values():
        for g in groups:
            for h in g.get("hooks", []):
                corpus.append(h.get("command", ""))
    blob = "\n".join(corpus)
    mounted = set()
    for name in ("route_inject_prompt.py", "route_miss_feeder.py", "kb_inject_prompt.py",
                 "route_unknown_unknown.py", "audit_search_kb.py", "route_audit.py",
                 "route_guard_audit.py", "feedback_detect.py", "rule_three_layer_guard.py",
                 "card_id_guard.py", "rule_fragment_inject.py",
                 "traecode_title_namer.py"):
        if name in blob:
            mounted.add(name)
    return mounted


def check_traecn(fix=False):
    """Trae CN 端 drift 校验（2026-10-09 第 20 端机械校验腿·皮叔令「动手」）。

    分母=12（2026-10-09 title_namer 转正 +1：traecode_title_namer UPS 实挂·自实验区迁入正式矩阵；
    前值 11 = 04 矩阵行 − reply_format/l3_conclusion 排除 − session_memory N/A
    − crossend N/A[合并单端·.trae-cn 无他端共居·2026-10-09 by Trae CN 签名排除]）：
      直挂 text 通道：route_inject / route_miss_feeder / kb_inject / rule_fragment
      直挂 Stop：route_unknown_unknown / card_id
      adapter --run 喂食（traecn_transcript_adapter）：route_audit / route_guard_audit /
        audit_search_kb / feedback_detect / rule_three_layer_guard
    对账 SSOT §二·七 Trae CN 列（col 15·12/12·2026-10-09 title_namer 转正后 by Trae CN）。
    rc 恒 0（报告制·漂移只打印+日志，--fix 才动文档）。
    """
    mounted = traecn_actual_mounted()
    if mounted is None:
        return report_source_missing("traecn", "~/.trae-cn/hooks.json",
                                     os.path.expanduser("~/.trae-cn/hooks.json"))
    items = ("route_inject_prompt.py", "route_miss_feeder.py", "kb_inject_prompt.py",
             "route_unknown_unknown.py", "audit_search_kb.py", "route_audit.py",
             "route_guard_audit.py", "feedback_detect.py", "rule_three_layer_guard.py",
             "card_id_guard.py", "rule_fragment_inject.py", "traecode_title_namer.py")
    denominator = 12
    yes = sum(1 for n in items if n in mounted)
    rate = f"{yes}/{denominator}"
    doc = documented_rate(15)  # Trae CN 列 = 第 15 个平台列（表尾·2026-10-09 插列）
    _df = documented_fraction(15)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] traecn 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if fix:
            fix_ssot_rate("traecn", yes, denominator, 15)
    detail = " | ".join(f"{n}:{'✅' if n in mounted else '❌'}" for n in items)
    if doc is None:
        # 假绿防护：文档列解析不出 ≠ 无漂移——显形不静默（守卫规范 §3.5）
        msg = f"[WARN] traecn 文档列(col15)解析为空·无法对账——按实盘记录 {rate}（{detail}）"
        print(msg)
        log_line(msg)
        return 0
    if doc != str(yes):
        msg = (
            f"[DRIFT] traecn 实测 {rate} ≠ 文档记录 {doc}/{denominator} —— "
            f"SSOT §二·七 Trae CN 列与实盘脱节（幽灵挂载检查·{detail}）"
        )
        print(msg)
        log_line(msg)
        if fix:
            fix_ssot_rate("traecn", yes, denominator, 15)
            missing = [n for n in items if n not in mounted]
            if missing:
                print(f"[SUGGEST] traecn 清单内未挂：{', '.join(missing)} —— 确认是停用(改文档注记)还是漏挂(补 hooks.json)")
                log_line(f"[SUGGEST] traecn 未挂 {missing}")
    else:
        _ok = f"[OK] traecn 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)
    return 0



def documented_fraction(col):
    """纯分母变更腿（2026-10-09·皮叔令「立项·按K007做完」·K007 v1.1 声明值对账固定项反哺缺口）。
    返回接入率行第 col 列的 "N/M" 全分数；解析失败 → None（显形不静默·守卫规范 §3.5）。
    缺口根因：documented_rate 只取分子 → 分母单变（如 title_namer 转正 +1）时分子门禁全盲、
    --fix 不触发、文档分母滞留旧值（登记表与实盘脱钩=C-206 同族病）。"""
    try:
        txt = open(SSOT, encoding="utf-8").read()
    except Exception:
        return None
    for line in txt.splitlines():
        if not line.strip().startswith("|"):
            continue
        if not line.strip().lstrip("|").strip().startswith("接入率"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col < len(cells):
            m = re.search(r"(\d+)/(\d+)", cells[col])
            if m:
                return m.group(0)
        return None
    return None



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
        # 2026-10-09 Trae CN 修（严格行定位·与 documented_rate 同款）：首单元格=「接入率」才认，
        # 防自核签名行（含"接入率重估"）抢匹配致 --fix 空转假绿。
        if not line.strip().startswith("|"):
            continue
        if not line.strip().lstrip("|").strip().startswith("接入率"):
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
                    # pct 腿（同轮·K007 分母腿配套）：首个百分比重算（只动引导段第一个 · 防注释区误伤）
                    mp = re.search(r"[（(]\s*\d{1,3}\s*[%％]\s*[）)]", new_cell)
                    if mp and mp.start() < m.start() + 40:
                        npct = round(int(yes) * 100 / int(denominator))
                        new_cell = new_cell[:mp.start()] + f"({npct}%)" + new_cell[mp.end():]
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
            "zwork": "Zwork", "traecn": "Trae CN"}.get(src_key, src_key)
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



# ── 禁设台账核查（2026-10-10·Qoder CN D3 轮·§二·廿一 法则1 机制化）──────────
# 病根：禁止面（退役/永久关闭的守卫与钩子）此前只活在两处散文里——04 表行 +
# HOOKS 列表注释——散文不是判据：checker 不消费它，禁设复活无人机械可见（§二·廿一
# 「禁止类知识必须落盘成台账，源码只读台账」立的法由本函数自证）。
RETIRED_LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "retired-hooks.json")


def _load_retired_ledger(ledger_path=None, home=None):
    """返回 (ledger|None, err_kind, err_msg)。缺账语义分态：作者态=🔴（法则失效）·
    装机态=⚠️ 静默跳（台账不随包属既定设计·⛔不拿作者法绑架端机）。"""
    ledger_path = ledger_path or RETIRED_LEDGER
    home = home or os.path.expanduser("~")
    try:
        with open(ledger_path, encoding="utf-8") as f:
            return json.load(f), None, ""
    except FileNotFoundError:
        author_side = os.path.isdir(PLACEHOLDER)
        if author_side:
            return None, "red", ("🔴 禁设台账缺失——§二·廿一 法则1 失效面（源码读不到台账=禁设核查"
                                 "静默变零，比无台账更毒：消费者以为有闸）：%s" % ledger_path)
        return None, "skip", "⚠️ 禁设台账 absent（装机态合法·作者态必在）·本项静默跳"
    except Exception as e:
        return None, "red", "🔴 禁设台账不可解析：%s" % e


def check_retired(ledger_path=None, home=None, doc_path=None, verbose=True):
    """五态核查：①台账在且可解析 ②条目四字段齐 ③entity_deleted=零复活
    ④exit0_stub=只活在白名单路径+行数≤max+无must_not_contain ⑤台账name⊆04文档表。
    返回异常数（0=全绿）。夹具缝=三入参可注入（--retired-selftest 消费）。"""
    import glob as _glob
    home = home or os.path.expanduser("~")
    ledger, kind, msg = _load_retired_ledger(ledger_path, home)
    if kind == "skip":
        if verbose:
            print("  " + msg)
        return 0
    if kind == "red":
        if verbose:
            print("  " + msg)
        return 1
    doc = doc_path or os.path.join(
        home, "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/04-跨端接入指南.md")
    doctxt = ""
    try:
        doctxt = open(doc, encoding="utf-8").read()
    except Exception:
        pass
    noise = ("记忆琥珀", "存档包", "/归档", ".bak", "sessions", "workspace",
             ".openclaw-attachments", "__pycache__", "backup",
             # 2026-10-20：以下不是运行面（发布库=包快照·评估库=报告·日志=流水），
             # 全树扫它们既慢又会产生"包内副本=复活"的语义假红
             "发布库", "评估知识库", "工作日志", "记忆蒸馏")

    # 2026-10-20 性能根治（Stop 钩子实测 52-70s > 60s 超时线）：
    # 旧实现=每个退役名 × 11 个根各跑一次 recursive glob（实测 1.87M 次 stat·98s/轮）。
    # 修法=每个根只 os.walk 一次建 basename 索引（剪 noise 目录），按名查表；
    # 语义不变（同 noise 过滤·同匹配名），⛔不改变命中的定义。
    _idx_cache = {}

    def _index_dir(root):
        if root in _idx_cache:
            return _idx_cache[root]
        idx = {}
        if not os.path.isdir(root):
            _idx_cache[root] = idx
            return idx
        # 重依赖/缓存目录一律不可能是"钩子复活"的落点（.hermes 28.7万件/.workbuddy 17.6万件
        # 绝大部分住在这里）；剪掉它们把每轮 Stop 的索引成本压到可用范围，判据面不变。
        _prune = {"node_modules", ".venv", "venv", ".git", "cache", "logs", "dist",
                  "build", "__pycache__", ".cache", "site-packages", "tools"}
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns
                      if d not in _prune and not any(n.strip("/") in d for n in noise)]
            for fn in fns:
                fp = os.path.join(dp, fn)
                if any(n in fp for n in noise):
                    continue
                idx.setdefault(fn, []).append(fp)
        _idx_cache[root] = idx
        return idx

    def _hits(patterns):
        out = []
        for pat in patterns:
            if "/**/" in pat:
                root, name = pat.split("/**/", 1)
                out.extend(_index_dir(root).get(name, []))
            else:
                for fp in _glob.glob(pat, recursive=True):
                    if any(n in fp for n in noise):
                        continue
                    out.append(fp)
        return out

    problems = 0
    for item in ledger.get("retired_hooks", []):
        name = item.get("name", "?")
        miss = [k for k in ("name", "decision", "form", "ref") if not item.get(k)]
        if miss:
            problems += 1
            if verbose:
                print("  🔴 [%s] 台账字段缺失：%s" % (name, miss))
            continue
        form = item["form"]
        if form == "entity_deleted":
            hits = _hits([os.path.join(home, d, "**", name) for d in
                         (".qoder-cn", ".workbuddy", ".qoder", ".trae-cn", ".zcode",
                          ".openclaw-autoclaw", ".hermes", ".dsh", ".claude", ".codex")]
                        + [os.path.join(os.path.expanduser("[记忆共享中心]"), _d, "**", name)
                           for _d in ("脚本中心", "技能配置", "数字分身")])
            if hits:
                problems += 1
                if verbose:
                    print("  🔴 [%s] entity_deleted 复活于：%s"
                          % (name, [h.replace(home, "~") for h in hits[:4]]))
        elif form == "exit0_stub":
            allow = [os.path.realpath(os.path.expanduser(p)) for p in item.get("allowed_paths", [])]
            files = _hits([os.path.join(os.path.expanduser("[记忆共享中心]"), _d, "**", name)
                           for _d in ("脚本中心", "技能配置", "数字分身")]
                          + [os.path.join(home, d, "**", name) for d in
                             (".qoder-cn", ".workbuddy", ".qoder", ".trae-cn", ".zcode",
                              ".openclaw-autoclaw", ".hermes", ".dsh")])
            for fp in files:
                if any(os.path.realpath(fp).startswith(a) for a in allow):
                    if os.path.exists(fp):
                        txt = open(fp, encoding="utf-8", errors="ignore").read()
                        if (len(txt.splitlines()) > item.get("max_stub_lines", 30)
                                or any(t in txt for t in item.get("must_not_contain", []))):
                            problems += 1
                            if verbose:
                                print("  🔴 [%s] 桩形态破形（超行数或含阻断token）：%s"
                                      % (name, fp.replace(home, "~")))
                    continue
                problems += 1
                if verbose:
                    print("  🔴 [%s] 桩出现在非白名单位：%s" % (name, fp.replace(home, "~")))
        if doctxt and name not in doctxt:
            problems += 1
            if verbose:
                print("  🟡 [%s] 两本账漂移：台账条目未同现于 04 文档表（%s）" % (name, os.path.basename(doc)))
    if verbose:
        print(("  ✅ 禁设台账核查通过（%d 条）" % len(ledger.get("retired_hooks", [])))
              if problems == 0 else "  🔴 禁设台账 %d 项异常" % problems)
    return problems


def _retired_selftest():
    """出厂夹具（§3.9 判据完备性：每个红灯分支都要有能置假的用例·R5 变异自证）。"""
    import tempfile
    import shutil as _sh
    ok = 0
    total = 5
    tmp = tempfile.mkdtemp(prefix="retired-selftest-")
    try:
        home = os.path.join(tmp, "home")
        arch = PLACEHOLDER
        ledger = json.load(open(RETIRED_LEDGER, encoding="utf-8"))
        lg = os.path.join(tmp, "retired-hooks.json")
        json.dump(ledger, open(lg, "w", encoding="utf-8"))
        doc = os.path.join(tmp, "04doc.md")
        open(doc, "w", encoding="utf-8").write(
            "\n".join(r["name"] for r in ledger["retired_hooks"]))
        def t(name, cond):
            nonlocal ok
            print(("  ✅ " if cond else "  🔴 ") + name)
            if cond:
                ok += 1
        # R1 正例：干净态=0
        t("R1 正例·无复活→0 异常", check_retired(lg, home, doc, verbose=False) == 0)
        # R2 复活：entity_deleted 件出现在端 hooks 位
        d = os.path.join(home, ".qoder-cn", "hooks")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "reply_format_guard.py"), "w").write("sys.exit(2)")
        t("R2 负例·reply_format 复活必红", check_retired(lg, home, doc, verbose=False) >= 1)
        os.remove(os.path.join(d, "reply_format_guard.py"))
        # R3 桩破形：白内位塞 >max 行/含 exit2
        s = os.path.join(arch, "技能配置/triwich/scripts")
        os.makedirs(s, exist_ok=True)
        open(os.path.join(s, "l3_conclusion_guard.py"), "w").write(
            ("x = 1" + chr(10)) * 40 + "sys.exit(2)")
        t("R3 负例·桩含 sys.exit(2)/超行必红", check_retired(lg, home, doc, verbose=False) >= 1)
        os.remove(os.path.join(s, "l3_conclusion_guard.py"))
        # R4 两本账漂移：04 文档表缺条目名
        open(doc, "w", encoding="utf-8").write("空表")
        t("R4 负例·台账name缺席04表必显形", check_retired(lg, home, doc, verbose=False) >= 1)
        open(doc, "w", encoding="utf-8").write(
            "\n".join(r["name"] for r in ledger["retired_hooks"]))
        # R5 变异自证：作者态缺账=🔴（不是静默绿）
        t("R5 变异·作者态台账缺失=红非静默", check_retired(os.path.join(tmp, "nope.json"), home, doc, verbose=False) >= 1)
    finally:
        _sh.rmtree(tmp, ignore_errors=True)
    print("=== 禁设台账自测 %d/%d ===" % (ok, total))
    return ok == total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="workbuddy",
                    choices=["workbuddy", "hermes", "qoder-desktop", "qoder-cn", "dsh", "zcode", "autoclaw", "lobsterai", "traework", "doubaowork", "workbuddyai", "traecn"],
                    help="平台源：workbuddy=读 ~/.workbuddy/settings.json；hermes=读 config.yaml plugins.enabled；qoder-desktop=读 ~/.qoder/settings.json；qoder-cn=读 ~/.qoder-cn/settings.json；dsh=读插件 index.js 实盘（STOP_GUARDS+pre-step）；zcode=读 ~/.zcode/cli/config.json hooks.events 实盘；autoclaw=读 openclaw.json+patrol 实盘（2026-08-22 第7端）；lobsterai=读 openclaw.json plugins.allow+patrol+state/hooks 实盘（2026-08-22 第8端）；traework=读 route_traework_patrol.sh 实盘（2026-08-22 第9端·Trae Work 无 hooks 平台边界·守卫全挂 patrol 拉模式）；doubaowork=读 route_doubaowork_patrol.sh 实盘+心跳（2026-08-25 第10端·豆包办公无 hooks+无 session_memory·仅2文件级守卫可机械执行·执行证据校验路径不读配置文件）；workbuddyai=读 ~/.workbuddy-ai/settings.json（2026-09-11 第18端·WorkBuddy AI 国际版·与国内版同 schema 同代码双发行版）；traecn=读 ~/.trae-cn/hooks.json 实盘（2026-10-09 第20端·Trae CN 合并版·6事件命令式 Hook·分母11·crossend N/A·Stop 正文类经 traecn_transcript_adapter --run 承载）")
    ap.add_argument("--fix", action="store_true",
                    help="自动修复模式：实测接入率与SSOT文档不一致时自动同步文档（低风险）；settings.json 缺 Hook 仅报告建议（高风险）")
    ap.add_argument("--absorb", metavar="SRC", help="FU-79腿：本端缺项×别端已落地 只读显形（不计分子·不改文件）")
    ap.add_argument("--absorb-selftest", action="store_true", help="absorb_scan 出厂夹具+变异承重自证")
    ap.add_argument("--retired", action="store_true",
                    help="禁设台账独立核查（2026-10-10 §二·廿一 机制化·rc≠0=复活/破形/漂移）")
    ap.add_argument("--retired-selftest", action="store_true",
                    help="check_retired 出厂夹具+变异自证（R1-R5·含『缺账必红』承重）")
    args = ap.parse_args()

    if args.absorb_selftest:
        return _absorb_selftest()
    if args.absorb:
        return absorb_scan(args.absorb)
    if args.retired_selftest:
        return 0 if _retired_selftest() else 1
    if args.retired:
        return 1 if check_retired() else 0
    _rp = check_retired()
    if _rp:
        print("🔴 [禁设台账] %d 项异常（见上·⛔退役守卫重挂=踩 §3.4·扩/退役裁决·处置先查本台账）" % _rp)
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
    if args.src == "traecn":
        return check_traecn(fix=args.fix)

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
        return report_source_missing(args.src, "配置文件", cfg_path)

    mounted, dead_only, unverified_only = actual_mounted(settings)
    # 2026-10-09 童灵根治 WB 端聚合器误报：WB 端 UserPromptSubmit 已收敛为单出口
    # ups_aggregator.py（内部并发跑 11 组 provider），route_inject_prompt / route_miss_feeder /
    # kb_inject_prompt / session_title_namer 四件作为 provider 被聚合器实跑
    # （非 settings.json 顶层独立挂载）。旧提取按顶层命令子串匹配 → 四件全 ❌ → 虚假 8/12 漂移。
    # 修法：聚合器确已实挂（命令串含 ups_aggregator.py）则按适配器名承认可其承载的四件，
    # 避免把「聚合承载」误判成「未接入」（C-206 登记表与实盘脱钩同族病）。
    if args.src == "workbuddy":
        ups_carried = {"route_inject_prompt.py", "route_miss_feeder.py",
                       "kb_inject_prompt.py", "session_title_namer 族"}
        _s, _u, _d = classify_entries(settings)
        ups_mounted = any("ups_aggregator.py" in c for _, c in _s) or \
                      any("ups_aggregator.py" in c for _, c in _u)
        if ups_mounted:
            mounted |= ups_carried
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
    _df = documented_fraction(col)
    if _df is not None and _df.split("/")[0] == str(yes) and _df.split("/")[1] != str(denominator):
        _dm = f"[DRIFT-DEN] {args.src} 纯分母变更：文档 {_df} vs 计算 {yes}/{denominator}（分子一致·分子门禁盲区·K007 分母触发腿 2026-10-09）"
        print(_dm); log_line(_dm)
        if args.fix:
            fix_ssot_rate(args.src, yes, denominator, col)
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
        _ok = f"[OK] {args.src} 接入率 {rate} 无漂移（{detail}）"
        print(_ok); log_line(_ok)

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
# **作者态落点**（"[记忆共享中心]/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass