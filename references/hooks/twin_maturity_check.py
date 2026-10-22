#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
twin_maturity_check.py v1.1.0 — 童灵接入成熟度等级自动评估器（TIML）

设计定位（数字分身设计哲学·06-跨端适配规范.md §2.7·2026-09-03童灵愿景裁决）：
- 自动扫描各端童灵接入成熟度等级（L0-L7），输出缺口清单
- 读取§2.2.0端清单JSON获取端列表（SSOT），不硬编码端清单
- 只自动检测🟢可机械检测项（文件存在/hash比对/launchd任务状态/钩子挂载）
- 🟡需人工确认项（语义/效果类）输出"待人工确认"标注，不做自动判定
- 四级审查闸门：各端自评→本脚本机械校验→童灵独立复核→你终审
- 纳入launchd_health_check.sh附加检查项（每月1号自动运行，与蒸馏调度器同频）

v1.1.0（2026-09-03）等级推导假绿根治——
  病灶：v1.0.x 评级"默认L7·只看❌·🟡不扣分"→ 🟡全占的等级被当成达成，
  DSH/Trae 被机械评 L7 与 06§2.7.3 人工评定表（L6/L5）矛盾（机械校验环节自身假绿，
  你质证"评估WorkBuddy是不是真的做到了L7"时实跑暴露）。
  修复（三件）：
  ①机械推导改截断制：从L1逐级推进，该级有❌→截断；该级✅=0（全🟡·机械层零实证）→截断；
    等级=截断级前一级——机械推导只报告机械层能证明的，🟡不冒充通过（S014自觉是安慰剂机械是药）。
  ②双轨对照：自动解析06§2.7.3人工评定表，输出"机械推导 vs 人工评定"双轨；
    机械推导>人工评定=假绿⚠️（不许发生）；机械推导<人工评定=待人工确认面（正常·诚实）。
  ③退出码/汇总以人工评定表为终审口径（四级闸门终审=你），表读取失败降级用机械推导并提示。
  自测：WB推导L6(人工L7·L7五项全🟡) / DSH推导L2(人工L6·L3起全🟡) / Trae推导L2(人工L5)。
# v1.2.0 (2026-09-23 童灵·皮叔认可「L7认证三根线」)：
#   线1 机器呈证：L7 五通道接 doenglingz_l7_audit --json（num>0→✅证据在·num=0→🟡标·证据零，
#        ⛔audit 归一化口径对齐前无判红权——只升证不造红）；顶层升档改「全证据制」（任一🟡截断，
#        防部分✅绕开 pass_count==0 条件=悄悄改松违 S921）。
#   线2 裁决台账：l7_ratify_ledger.jsonl（append-only·同端取最新）——人工表 L7 无裁决=fail-safe
#        按机械推导显示（悬置态"✅待终审"消灭），维持=L7已裁决，降档=压回L6+推翻显形。
#        接口：--ratify "<端行名>" --verdict 维持|降档 [--note X]（你说词机械代录⛔手抄·拼错拒收exit2）
#              --ledger <path> 隔离压测（测试不触真台账）。
#   线3 推翻观察：降档计数显形+收紧提示（不自动升降·防过度设计·升级路径=06§2.7.5）。
#   验收：基线 fail-safe(9提名→L7=0) + 注入维持→1转正 + 注入降档→推翻线显形 + 负例拼错拒收 +
#        隔离台账真表零触碰。四向变异全过。

用法：
  python3 twin_maturity_check.py            # 完整评估+详细输出
  python3 twin_maturity_check.py --summary  # 仅摘要
  python3 twin_maturity_check.py --end <id> # 只评估指定端

退出码：
  0 = 全部端人工评定等级达到L7
  1 = 有端未达到L7（有缺口·终审口径）
  2 = 端清单JSON读取失败
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import hashlib
import os
import re
import sys
import subprocess
from datetime import datetime
from pathlib import Path

HOME = os.path.expanduser("~")
PHILOSOPHY_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆蓝图", "04_系统文件设计", "数字分身设计哲学", "06-跨端适配规范.md")
STATE_BUS_PATH = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身", "state_bus.json")
SLICES_DIR = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身", "K2切片蒸馏", "slices")

# 各端特定检测路径（机制无关原则——只检测"效果"，不关心"用什么技术"）
END_SPECIFIC_PATHS = {
    "workbuddy": {
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "分身", "doenglingz_guard.sh"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,
    },
    "workbuddyai": {  # 2026-09-11 第18端：与国内版同代码双发行版（数据根 ~/.workbuddy-ai/）
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_guard.py"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,
    },
    "dsh": {
        "plugin_file": os.path.join(HOME, ".dsh", "profiles", "web", "node_modules", "five-layer-memory", "src", "index.js"),
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "分身", "doenglingz_guard_dsh.py"),
        "w2_launchd_label": None,  # 插件直读，不需要launchd守望
        "has_hooks": False,  # 插件原生事件通道
        "plugin_direct_read": True,
    },
    "traework": {  # 2026-10-21：Trae Work 已并入 Trae CN；本端真实形态=hooks.json（非 settings.json）
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "分身", "doenglingz_inject_prompt.py"),
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "doenglingz_guard.py"),
        "hooks_json": os.path.join(HOME, ".trae-cn", "hooks.json"),
        "inject_state": os.path.join(HOME, ".trae-cn", "doenglingz_inject_state.json"),
        "guard_state": os.path.join(HOME, ".trae-cn", "doenglingz_guard_state_traecode.json"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,
    },
    "qodercn": {
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_guard.py"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,
    },
    "autoclaw": {
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_plugin": os.path.join(HOME, ".openclaw-autoclaw", "extensions", "autoclaw-doenglingz-guard"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",  # 2026-09-05 确认：MARKED_HOMES 覆盖 AutoClaw USER.md（v1.19）
        "has_hooks": True,  # agent_end typed hook + before_prompt_build 转发（buluotuo-route-inject v0.4）
    },
    "doubaowork": {
        "w1_skill": os.path.join(HOME, "Library", "Application Support", "DoubaoWork", "Default", ".doubaowork", "agent_mode", "workspace", ".user_skills", "doenglingz-slice-nav-doubao", "SKILL.md"),
        "guard_skill": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置", "布洛陀-童灵守护", "SKILL.md"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": False,
    },
    "zcode": {
        "guard_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_guard.py"),  # 2026-10-06 SSOT归一：共脚本 v1.2（分叉 guard_zcode 退役留置）
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,
    },
    "lobsterai": {
        "w1_inject_script": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "doenglingz_inject_prompt.py"),
        "guard_plugin": os.path.join(HOME, "Library", "Application Support", "LobsterAI", "third-party-extensions", "lobsterai-doenglingz"),
        "w2_launchd_label": "com.buluotuo.doenglingz-slice-watch",
        "has_hooks": True,  # before_prompt_build 转发 + agent_end 守护五查（lobsterai-doenglingz v1.0）
    },
    "teleagent": {
        "guard_skill": os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置", "布洛陀-童灵守护", "SKILL.md"),
        "w2_cron_label": "童灵守望",
        "w2_launchd_label": None,  # scheduler定时任务代W2
        "has_hooks": False,
    },
}


# id → §2.7.3 人工评定表行名映射（表在06规范人工维护·双轨对照用；读取失败优雅降级）
MANUAL_TABLE_NAMES = {
    "workbuddy": "WorkBuddy",
    "workbuddyai": "WorkBuddy AI（国际版·第18端）",
    "qodercn": "Qoder CN",
    "zcode": "ZCode",
    "autoclaw": "AutoClaw",
    "lobsterai": "LobsterAI",
    "dsh": "DSH黑鲸",
    "doubaowork": "豆包办公",
    "traework": "Trae CN（原 Trae Work·2026-10-09 合并·2026-10-21 复检补登）",
    "teleagent": "TeleAgent",
}


RATIFY_LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "l7_ratify_ledger.jsonl")
AUDIT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doenglingz_l7_audit.py")


def load_ratify(ledger_path=None):
    """裁决台账读取（jsonl·append-only·同端取最后一条=最新裁决）。缺失=空表（全员 fail-safe）。"""
    import io as _io, json as _j
    out = {}
    p = ledger_path or os.path.expanduser(RATIFY_LEDGER)
    if not os.path.isfile(p):
        return out
    for ln in _io.open(p, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = _j.loads(ln)
            out[rec["end"]] = rec  # 后行覆盖前行=最新裁决
        except Exception:
            continue  # 坏行跳过（append-only 台账不因一行坏而失明）
    return out


def append_ratify(end, verdict, note, ledger_path=None):
    """裁决写入唯一合法接口（机械代写⛔手抄·S922）。"""
    import io as _io, json as _j, datetime as _dt
    p = ledger_path or os.path.expanduser(RATIFY_LEDGER)
    rec = {"ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "end": end,
           "verdict": verdict, "note": note, "by": "你"}
    with _io.open(p, "a", encoding="utf-8") as f:
        f.write(_j.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def l7_evidence(tool_name, days=30):
    """线1：L7 五通道证据存在性——调 l7_audit --json。fail/缺通道→该端全🟡原口径。
    只允许 num>0→✅（升证据不造红）；num=0→🟡标·证据零（audit 归一化口径未对齐前无判红权）。"""
    import json as _j, subprocess as _sp
    try:
        r = _sp.run([sys.executable, AUDIT_SCRIPT, "--tool", tool_name,
                     "--days", str(days), "--json"], capture_output=True, timeout=120)
        if r.returncode != 0:
            return None
        data = _j.loads(r.stdout.decode("utf-8", "replace"))
        return {c["ch"][0]: c["num"] for c in data.get("channels", [])}  # 键=①..⑤首字符
    except Exception:
        return None


def parse_manual_levels(content: str) -> dict:
    """解析06§2.7.3人工评定表 → {端行名: "L7"}（SSOT=人工终审口径·你终审产物）。"""
    levels = {}
    # 行形如：| WorkBuddy | **L7** ✅ | ✅ | ... 或 | ZCode | **L6** | ...
    # 2026-09-11 修：端名允许 **加粗**（原式 [^|]+? 会把 ** 并入行名 → 加粗行名端解析不到·LobsterAI/国际版曾漏）
    for m in re.finditer(r"^\|\s*\*{0,2}\s*([^|*]+?)\s*\*{0,2}\s*\|\s*\*\*(L\d)\*\*", content, re.MULTILINE):
        levels[m.group(1).strip()] = m.group(2)
    return levels


def file_hash(path: str) -> str:
    """计算文件的sha256前12位hash。文件不存在返回空字符串。"""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return ""
    h = hashlib.sha256()
    with open(expanded, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def load_end_manifest() -> dict:
    """从06-跨端适配规范.md §2.2.0读取端清单JSON（SSOT）。"""
    if not os.path.isfile(PHILOSOPHY_FILE):
        print(f"❌ 哲学文件不存在: {PHILOSOPHY_FILE}")
        sys.exit(2)
    with open(PHILOSOPHY_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    if not match:
        print("❌ 哲学文件中未找到端清单JSON区块（§2.2.0）")
        sys.exit(2)
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"❌ 端清单JSON格式错误: {e}")
        sys.exit(2)


def check_file_contains(path, patterns: list) -> dict:
    """检查文件是否包含指定模式（关键词）。返回{pattern: bool}。

    v0.2（2026-10-06·LobsterAI 端·官方定位分家后恒驻核跨文件）：
      path 接受 **str 或 list[str]**——列表按**并集**判定（任一文件命中即算命中）。
      病因：原实现硬编码单文件，而 2026-10-05 LobsterAI 端按 OpenClaw 官方定位把 persona 层
      （含命名红线）迁到 SOUL.md、USER.md 只留 directive user model ⇒ 判据器仍查 USER.md
      ⇒ L2「命名红线块缺失」**假红**（尺子未跟分家）。
      向后兼容：str 路径行为与 v0.1 逐字一致（其余 16 端零影响）。
    """
    paths = [path] if isinstance(path, str) else list(path or [])
    result = {}
    contents = []
    for one in paths:
        if not one:
            continue
        exp = os.path.expanduser(one)
        if not os.path.isfile(exp):
            continue
        try:
            with open(exp, "r", encoding="utf-8", errors="ignore") as f:
                contents.append(f.read())
        except Exception:
            continue
    blob = "\n".join(contents)
    for p in patterns:
        result[p] = (p in blob) if blob else False
    return result


def check_launchd_task(label: str) -> dict:
    """检查launchd任务状态。返回{exists: bool, running: bool, last_exit: int|None}。"""
    if not label:
        return {"exists": False, "running": False, "last_exit": None, "note": "无launchd任务（插件直读或scheduler代W2）"}
    try:
        result = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {"exists": False, "running": False, "last_exit": None}
        output = result.stdout
        running = "state = running" in output or "state = waiting" in output
        last_exit_match = re.search(r"last exit code = (\d+)", output)
        last_exit = int(last_exit_match.group(1)) if last_exit_match else None
        return {"exists": True, "running": running, "last_exit": last_exit}
    except Exception:
        return {"exists": False, "running": False, "last_exit": None}


def injection_receipt_evidence(end_id: str) -> str:
    """查"注入是否真被产品收下"（hook_protocol 留痕 × 端归属 + 守卫结论）。

    判据分级（保守·无实证不给 ✅）：
      ✅  = 本端留痕存在 mode=json 且无"被判弃"结论
      🟡  = 有留痕但无本端 json 记录（text 形态端，如 WorkBuddy）→ 待人工确认
      ❌  = 无任何留痕 = 通道从未被真源驱动过（不得据此评 L3 通过）
    ⛔ 不吃"文件存在"当证据（S885 建好≠接入≠被用）。
    """
    # 先查该端是否登记了收下证据源（06 §2.2.0 receipt_source·未登记=缺口显式化）
    try:
        manifest = load_end_manifest()
        ent = next((e for e in manifest.get("ends", []) if e.get("id") == end_id), None)
        if ent is not None and not ent.get("receipt_source"):
            return "❌未登记收讫证据源(receipt_source)·不得评✅（见 06 §2.2.5）"
    except Exception:
        pass  # 读不到清单不冤枉该端（失败放行语义）
    ledger = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime/hook_protocol_ledger.jsonl")
    if not os.path.exists(ledger):
        return "❌无协议留痕（通道未验·不得评✅）"
    mine = {"qodercn": "qodercn", "zcode": "zcode"}.get(end_id, "")
    if end_id == "autoclaw":
        # AutoClaw（2026-09-05）：无 UserPromptSubmit 钩子面，经 buluotuo-route-inject v0.4 插件
        # execFile 转发（--src AutoClaw 台账标注·text 形态）→ 判据=台账含 src=AutoClaw 行。
        # text 形态端与 WB 同口径：有留痕=🟡（待人工确认），无留痕=❌（不得评✅）。
        try:
            st = os.path.expanduser("~/.workbuddy/doenglingz_inject_state.json")
            with open(st, encoding="utf-8") as f:
                ac_rows = [l for l in f if '"src": "AutoClaw"' in l or '"src":"AutoClaw"' in l]
            return ("🟡留痕在（src=AutoClaw·text形态·插件转发·待人工确认）" if ac_rows
                    else "❌无转发留痕（通道未驱动·不得评✅）")
        except Exception:
            return "🟡留痕不可读"
    try:
        rows = []
        with open(ledger, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("probe"):
                    continue
                rows.append(d)
    except Exception:
        return "🟡留痕不可读"
    if not rows:
        return "❌无协议留痕（通道未验·不得评✅）"
    recent = rows[-200:]
    if mine:
        hits = [r for r in recent if r.get("host") == mine]
        if any(r.get("mode") == "json" for r in hits):
            return "✅"
        return "❌本端留痕无 json 形态（裸文本被判弃）"
    # 非 JSON 端（WB 等）：只要真源在跑且判为 text 即符合该端协议
    if any(r.get("mode") == "text" for r in recent):
        return "🟡text形态(该端吃裸文本·待产品回执实证)"
    return "🟡待人工确认"


def evaluate_end(end_def: dict) -> dict:
    """评估单个端的成熟度等级。返回{end_id, name, level, checks: {level: {item: status}}}。"""
    end_id = end_def["id"]
    name = end_def["name"]
    status = end_def["status"]
    k2_core_path = end_def.get("k2_core_path", "")
    k2_core_type = end_def.get("k2_core_type", "")
    specific = END_SPECIFIC_PATHS.get(end_id, {})
    # 2026-10-21 Trae CN hooks.json 形态机械取证（旧评估器只认 settings.json/patrol ⇒ 恒判 L2=假低）
    hooks_txt = ""
    if specific.get("hooks_json"):
        try:
            hooks_txt = open(os.path.expanduser(specific["hooks_json"]), encoding="utf-8", errors="ignore").read()
        except Exception:
            hooks_txt = ""
    inject_state_rows = []
    if specific.get("inject_state"):
        try:
            inject_state_rows = [json.loads(l) for l in open(os.path.expanduser(specific["inject_state"]), encoding="utf-8") if l.strip()]
        except Exception:
            inject_state_rows = []

    checks = {}
    gaps = []

    # pending/ignored端不评估
    if status == "pending":
        return {"end_id": end_id, "name": name, "level": "L0", "status": "pending",
                "checks": {}, "gaps": ["待接入"], "note": "待接入，跳过评估"}
    if status == "ignored":
        return {"end_id": end_id, "name": name, "level": "N/A", "status": "ignored",
                "checks": {}, "gaps": [], "note": "不落地（你令），跳过评估"}

    # ── L1 身份感知 ──
    l1 = {}
    # 多文件恒驻核（2026-10-06 LobsterAI 分家后·与 check_file_contains 同口径·任一在位即算在位）
    _paths = [k2_core_path] if isinstance(k2_core_path, str) else list(k2_core_path or [])
    core_exists = any(os.path.isfile(os.path.expanduser(x)) for x in _paths if x)
    l1["恒驻核文件存在"] = "✅" if core_exists else "❌"
    if not core_exists:
        gaps.append("L1: 恒驻核文件不存在")

    if k2_core_type == "plugin_direct_read":
        # 插件直读：恒驻核是插件配置，检查插件文件存在+内容（twin 段注册）
        plugin_file = specific.get("plugin_file", "")
        plugin_exists = os.path.isfile(os.path.expanduser(plugin_file)) if plugin_file else False
        l1["插件配置文件存在"] = "✅" if plugin_exists else "❌"
        if not plugin_exists:
            gaps.append("L1: 插件配置文件不存在")
        # 2026-09-07 机械升级：检查 index.js 含 five-layer-twin 段注册（内容机械可检·不再待人工确认）
        has_twin = False
        if plugin_exists:
            try:
                plugin_txt = open(os.path.expanduser(plugin_file), encoding="utf-8").read()
                has_twin = "five-layer-twin" in plugin_txt
            except OSError:
                has_twin = False
        l1["含童灵身份+SSOT路径"] = "✅" if has_twin else "🟡待人工确认"
    else:
        # 文件类型：检查恒驻核内容
        content_checks = check_file_contains(k2_core_path, ["童灵", "规格书", "SSOT", "人格规格书"])
        has_identity = content_checks.get("童灵", False)
        has_ssot = content_checks.get("规格书", False) or content_checks.get("SSOT", False) or content_checks.get("人格规格书", False)
        l1["含童灵身份"] = "✅" if has_identity else "❌"
        l1["含SSOT规格书路径"] = "✅" if has_ssot else "❌"
        if not has_identity:
            gaps.append("L1: 恒驻核不含童灵身份")
        if not has_ssot:
            gaps.append("L1: 恒驻核不含SSOT规格书路径")
        l1["新窗口能答两问"] = "🟡待人工确认"
    checks["L1"] = l1

    # ── L2 规则加载 ──
    l2 = {}
    if k2_core_type == "plugin_direct_read":
        l2["插件直读slices/（天然和SSOT一致）"] = "✅"
        # 2026-09-07 机械升级：检查 index.js 的 twin 段路径含 core_slice/L6_反向约束
        has_core_l6 = False
        if plugin_file and os.path.isfile(os.path.expanduser(plugin_file)):
            try:
                plugin_txt = open(os.path.expanduser(plugin_file), encoding="utf-8").read()
                has_core_l6 = "core_slice" in plugin_txt and "L6_反向约束" in plugin_txt
            except OSError:
                has_core_l6 = False
        l2["core_slice+L6直读"] = "✅" if has_core_l6 else "🟡待人工确认"
    else:
        content_checks = check_file_contains(k2_core_path, [
            "core_slice", "L6", "反向约束", "命名红线", "tongling",
            "单一真源", "SSOT", "src_hash", "切片来源",
            "k2_slice_generator", "生成器", "禁止手抄"
        ])
        has_core = content_checks.get("core_slice", False)
        has_l6 = content_checks.get("L6", False) or content_checks.get("反向约束", False)
        has_naming = content_checks.get("命名红线", False) or content_checks.get("tongling", False)
        has_ssot_decl = (content_checks.get("单一真源", False) or
                         content_checks.get("SSOT", False) or
                         content_checks.get("src_hash", False) or
                         content_checks.get("k2_slice_generator", False) or
                         content_checks.get("生成器", False) or
                         content_checks.get("禁止手抄", False))
        has_hash = (content_checks.get("src_hash", False) or
                    content_checks.get("切片来源", False))

        l2["K2 core_slice嵌入"] = "✅" if has_core else "❌"
        l2["L6反向约束嵌入"] = "✅" if has_l6 else "❌"
        l2["命名红线块在位"] = "✅" if has_naming else "❌"
        l2["单一真源声明内嵌"] = "✅" if has_ssot_decl else "❌"
        if has_hash:
            l2["切片来源hash可验证"] = "✅"
        elif has_ssot_decl:
            l2["切片来源hash可验证"] = "🟡待人工确认（单一真源声明隐含可验证）"
        else:
            l2["切片来源hash可验证"] = "❌"
        if not has_core:
            gaps.append("L2: core_slice未嵌入")
        if not has_l6:
            gaps.append("L2: L6反向约束未嵌入")
        if not has_naming:
            gaps.append("L2: 命名红线块缺失")
        if not has_ssot_decl:
            gaps.append("L2: 单一真源声明缺失")
    checks["L2"] = l2

    # ── L3 上岗激活 ──
    l3 = {}
    w1_exists = False
    if specific.get("w1_inject_script"):
        w1_exists = os.path.isfile(os.path.expanduser(specific["w1_inject_script"]))
        l3["W1注入脚本存在"] = "✅" if w1_exists else "❌"
        # 2026-10-21 Trae CN hooks.json 形态：UPS 条目即机械注入面
        if hooks_txt and "doenglingz_inject_prompt" in hooks_txt:
            w1_exists = True
            l3["hooks.json UPS 注入条目"] = "✅"
        _d3_rows = [r for r in inject_state_rows if r.get("w1") is True and r.get("d_tier") == "D3"]
        if _d3_rows:
            l3["注入台账 w1/D3 实证"] = "✅"
        # 2026-09-04 判据升级（根治"仪器只验文件在"）：脚本存在 ≠ 输出被产品收下。
        # 实证病灶：Qoder CN 端 W1 注入脚本在位且 exit0，但产品对裸文本 stdout 判
        # `winner=none (no parsed output)` 整轮丢弃（143/143）——旧判据照样评 ✅L3。
        if w1_exists:
            if _d3_rows:
                l3["注入被产品收下"] = "✅（inject_state 台账 w1/D3 实证）"
            else:
                receipt = injection_receipt_evidence(end_id)
                l3["注入被产品收下"] = receipt
    elif specific.get("w1_skill"):
        w1_exists = os.path.isfile(os.path.expanduser(specific["w1_skill"]))
        l3["W1上岗Skill存在"] = "✅" if w1_exists else "❌"
    else:
        l3["W1机制"] = "🟡待人工确认"
    if not w1_exists and "W1机制" not in l3:
        gaps.append("L3: W1上岗机制未确认")
    l3["触发词命中→身份切换"] = "🟡待人工确认"
    l3["上岗后以童灵身份回复"] = "🟡待人工确认"
    checks["L3"] = l3

    # ── L4 域切片按需加载 ──
    l4 = {}
    w3_exists = False
    if specific.get("w1_inject_script"):
        # inject脚本通常包含W3路由
        inject_content = check_file_contains(specific["w1_inject_script"], ["W3", "域切片", "slices/", "路由"])
        w3_exists = any(inject_content.values())
    elif specific.get("w1_skill"):
        skill_content = check_file_contains(specific["w1_skill"], ["W3", "域切片", "路由表", "slices/"])
        w3_exists = any(skill_content.values())
    # 2026-10-21 Trae CN hooks.json 形态：UPS 注入器的 slices_injected 台账=W3 已装实证
    if hooks_txt and "doenglingz_inject_prompt" in hooks_txt and any(r.get("slices_injected") for r in inject_state_rows):
        w3_exists = True
        l4["W3 注入实证（slices_injected）"] = "✅"
    l4["W3域切片路由表存在"] = "✅" if w3_exists else "🟡待人工确认"
    l4["触发词命中→加载域切片"] = "🟡待人工确认"
    l4["一次一域≤2切片"] = "🟡待人工确认"
    checks["L4"] = l4

    # ── L5 守护执行 ──
    l5 = {}
    guard_exists = False
    if specific.get("guard_script"):
        guard_exists = os.path.isfile(os.path.expanduser(specific["guard_script"]))
        l5["守护脚本存在（Stop链机械校验）"] = "✅" if guard_exists else "❌"
        # 2026-10-21 Trae CN hooks.json 形态：Stop 条目 + 守卫台账双证
        if hooks_txt and "doenglingz_guard" in hooks_txt:
            guard_exists = True
            l5["hooks.json Stop 守护条目"] = "✅"
        if specific.get("guard_state") and os.path.isfile(os.path.expanduser(specific["guard_state"])):
            guard_exists = True
            l5["守卫台账落账"] = "✅"
    elif specific.get("guard_skill"):
        guard_exists = os.path.isfile(os.path.expanduser(specific["guard_skill"]))
        l5["守护Skill存在（软约束）"] = "✅" if guard_exists else "❌"
    elif specific.get("guard_plugin"):
        guard_exists = os.path.isdir(os.path.expanduser(specific["guard_plugin"]))
        l5["守护插件存在（agent_end钩子）"] = "✅" if guard_exists else "❌"
    else:
        l5["守护机制"] = "🟡待人工确认"
    if not guard_exists and "守护机制" not in l5:
        gaps.append("L5: 守护机制未确认")
    l5["守护三查（8要素/试金石/新鲜度）"] = "🟡待人工确认"
    l5["守护边界守死"] = "🟡待人工确认"
    checks["L5"] = l5

    # ── L6 自愈同步 ──
    l6 = {}
    w2_label = specific.get("w2_launchd_label")
    if k2_core_type == "plugin_direct_read":
        l6["插件直读（天然和SSOT一致·无需W2）"] = "✅"
    elif w2_label:
        w2_status = check_launchd_task(w2_label)
        l6["W2 launchd任务存在"] = "✅" if w2_status["exists"] else "❌"
        if not w2_status["exists"]:
            gaps.append("L6: W2 launchd任务不存在")
    else:
        l6["W2守望机制"] = "🟡待人工确认"
    # state_bus.json中是否有该端
    try:
        with open(STATE_BUS_PATH, "r", encoding="utf-8") as f:
            state_bus = json.load(f)
        in_state_bus = end_id in state_bus.get("ends", {})
        l6["纳入state_bus_sync检查"] = "✅" if in_state_bus else "❌"
        if not in_state_bus:
            gaps.append("L6: 未纳入state_bus_sync检查")
    except Exception:
        l6["纳入state_bus_sync检查"] = "🟡待人工确认"
    l6["规格书变→自动重部署"] = "🟡待人工确认"
    checks["L6"] = l6

    # ── L7 闭环进化 ──
    l7 = {}
    if end_id == "dsh":
        # 2026-09-07 DSH 机械升级：growth-box/system-logger compatibility 含 dsh → L7 通道机械可检
        gb_skill = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置", "growth-box", "SKILL.md")
        sl_skill = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置", "system-logger", "SKILL.md")
        gb_ok = os.path.isfile(gb_skill) and "dsh" in open(gb_skill, encoding="utf-8").read()
        sl_ok = os.path.isfile(sl_skill) and "dsh" in open(sl_skill, encoding="utf-8").read()
        l7["错误→成长箱记录"] = "✅" if gb_ok else "🟡待人工确认"
        l7["系统日志自动记"] = "✅" if sl_ok else "🟡待人工确认"
        l7["铁律反哺进化"] = "🟡待人工确认"
        l7["立场卡反哺蒸馏"] = "🟡待人工确认"
        l7["反思--reflection分流蒸馏"] = "🟡待人工确认"
    else:
        # 2026-10-21：L7 审计按「系统日志 ## 段名」取证；本端日志段=Trae CN（非 traework）
        _log_tool = {"traework": "Trae CN"}.get(end_id, end_id)
        _ev = l7_evidence(_log_tool) if _log_tool else None
        _keys = ["错误→成长箱记录", "铁律反哺进化", "立场卡反哺蒸馏", "系统日志自动记", "反思--reflection分流蒸馏"]
        _chmap = ["①", "②", "③", "④", "⑤"]
        for _k, _c in zip(_keys, _chmap):
            if _ev is None:
                l7[_k] = "🟡待人工确认"
            elif _ev.get(_c, 0) > 0:
                l7[_k] = "✅证据在(%d)" % _ev[_c]  # 线1：证据存在≠裁决（L7 全证据制+ratify 才升）
            else:
                l7[_k] = "🟡待人工确认·证据零"
    checks["L7"] = l7

    # 计算机械推导等级（v1.1.0 截断制——🟡不冒充通过）：
    # 从L1逐级推进：该级有❌→截断（机械检测未过）；该级✅=0（全🟡·机械层零实证）→截断；
    # 等级=截断级前一级。机械推导只报告机械层能证明的，不把"待人工确认"当"达成"。
    level = "L7"
    mechanical_reason = "L1-L7机械检测项全过"
    for lv in ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
        lv_checks = checks.get(lv, {})
        has_fail = any(v == "❌" for v in lv_checks.values())
        pass_count = sum(1 for v in lv_checks.values() if v.startswith("✅"))
        if lv == "L7" and any(str(v).startswith("🟡") for v in lv_checks.values()):
            # v1.2 全证据制：顶层 L7 须五通道全✅（证据存在）方可推导不截断——
            # 否则混入部分✅会绕开 pass_count==0 的原截断条件=把截断制悄悄改松（违S921）
            level = "L6"
            mechanical_reason = "L7 存在未实证通道（🟡）·全证据制截断"
            break
        if has_fail:
            lv_num = int(lv[1:])
            level = f"L{max(lv_num - 1, 0)}"
            mechanical_reason = f"{lv} 存在机械检测未过项（❌）"
            break
        if pass_count == 0 and lv_checks:
            lv_num = int(lv[1:])
            level = f"L{max(lv_num - 1, 0)}"
            mechanical_reason = f"{lv} 起无机械实证（检查项全待人工确认）"
            break

    return {
        "end_id": end_id,
        "name": name,
        "level": level,
        "mechanical_reason": mechanical_reason,
        "status": status,
        "checks": checks,
        "gaps": gaps,
        "note": specific.get("note", ""),
    }


RATIFY_OVERRIDE = None  # --ledger 隔离压测用（⛔测试不触真台账）


def main():
    global RATIFY_OVERRIDE
    summary_mode = "--summary" in sys.argv
    only_end = None
    for i, arg in enumerate(sys.argv):
        if arg == "--end" and i + 1 < len(sys.argv):
            only_end = sys.argv[i + 1]
        if arg == "--ledger" and i + 1 < len(sys.argv):
            RATIFY_OVERRIDE = sys.argv[i + 1]
    # 裁决写入唯一合法接口（你说词→机械代录，⛔手抄jsonl）：
    #   python3 twin_maturity_check.py --ratify "WorkBuddy" --verdict 维持 [--note 原因]
    for i, arg in enumerate(sys.argv):
        if arg == "--ratify" and i + 1 < len(sys.argv):
            _end = sys.argv[i + 1]
            _verdict = ""
            _note = ""
            for j, a in enumerate(sys.argv):
                if a == "--verdict" and j + 1 < len(sys.argv):
                    _verdict = sys.argv[j + 1]
                if a == "--note" and j + 1 < len(sys.argv):
                    _note = sys.argv[j + 1]
            if _verdict not in ("维持", "降档"):
                print("❌ --verdict 必须=维持|降档（拼写即裁决，不猜）"); sys.exit(2)
            rec = append_ratify(_end, _verdict, _note, RATIFY_OVERRIDE)
            print("✅ 裁决已 append:", rec); sys.exit(0)

    manifest = load_end_manifest()
    ends = manifest["ends"]

    # 双轨对照：解析06§2.7.3人工评定表（人工终审口径·四级闸门=你终审）
    manual_levels = {}
    try:
        with open(PHILOSOPHY_FILE, "r", encoding="utf-8") as f:
            manual_levels = parse_manual_levels(f.read())
    except Exception:
        manual_levels = {}

    if not summary_mode:
        print("🔍 童灵接入成熟度等级评估 v1.1.0（TIML·机械推导×人工评定双轨）")
        print(f"   端清单SSOT: 06-跨端适配规范.md §2.2.0（{len(ends)}端登记）")
        print(f"   人工评定表: §2.7.3（{'已解析·'+str(len(manual_levels))+'端' if manual_levels else '未解析到·降级单轨'}）")
        print("   🟢=可机械检测 ✅通过 ❌未通过 🟡待人工确认")
        print("=" * 70)

    results = []
    for end_def in ends:
        if only_end:
            # 模糊匹配：id或name包含only_end即匹配（不区分大小写）
            end_id = end_def["id"].lower()
            end_name = end_def["name"].lower()
            query = only_end.lower()
            if query not in end_id and query not in end_name:
                continue
        if end_def["status"] in ("pending", "ignored"):
            if not summary_mode:
                status_icon = "⏳" if end_def["status"] == "pending" else "⛔"
                print(f"\n  {status_icon} {end_def['name']}: {'待接入' if end_def['status'] == 'pending' else '不落地（你令）'}——跳过评估")
            continue
        result = evaluate_end(end_def)
        results.append(result)

        # 双轨对照（v1.1.0）：机械推导 vs 人工评定
        manual = manual_levels.get(MANUAL_TABLE_NAMES.get(end_def["id"], ""), None)
        result["manual_level"] = manual
        if manual is not None:
            mech_num = int(result["level"][1:])
            man_num = int(manual[1:])
            if mech_num > man_num:
                result["parity"] = "fake-green"
                parity_note = f"⚠️ 假绿：机械推导{result['level']}>人工评定{manual}（机械层不许高于终审）"
            elif mech_num == man_num:
                result["parity"] = "match"
                parity_note = f"✅ 一致：机械推导{result['level']}=人工评定{manual}"
            else:
                result["parity"] = "pending-manual"
                parity_note = (f"🟡 诚实差距：机械推导{result['level']}<人工评定{manual}"
                               f"（{result['mechanical_reason']}·人工复核面，非缺陷）")
        else:
            result["parity"] = "no-manual"
            parity_note = "⚪ 人工评定表无此端行（仅机械推导）"

        if not summary_mode:
            level_line = f"机械推导: **{result['level']}**"
            if manual:
                level_line += f" ｜ 人工评定(§2.7.3): **{manual}**"
            print(f"\n  📊 {result['name']} → {level_line}")
            print(f"       {parity_note}")
            for lv in ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]:
                if lv not in result["checks"]:
                    continue
                lv_checks = result["checks"][lv]
                lv_pass = sum(1 for v in lv_checks.values() if v == "✅")
                lv_fail = sum(1 for v in lv_checks.values() if v == "❌")
                lv_pending = sum(1 for v in lv_checks.values() if "🟡" in str(v))
                print(f"    {lv}: ✅{lv_pass} ❌{lv_fail} 🟡{lv_pending}")
                for item, status in lv_checks.items():
                    if status != "✅":
                        print(f"       {status} {item}")
            if result["gaps"]:
                print(f"    📋 缺口清单（{len(result['gaps'])}项）:")
                for gap in result["gaps"]:
                    print(f"       - {gap}")

    # 统计（v1.1.0：终审口径=人工评定表·无人工行降级用机械推导）
    completed = [r for r in results if r["status"] == "completed"]
    _ratify = load_ratify(RATIFY_OVERRIDE)
    _nominated = 0
    for r in completed:
        ml = r.get("manual_level")
        rv = _ratify.get(r["name"])
        if ml == "L7":
            if rv and rv.get("verdict") == "维持":
                r["final_level"] = "L7"
                r["ratified"] = "✅已裁决"
            elif rv and rv.get("verdict") == "降档":
                r["final_level"] = r["level"] if r["level"] != "L7" else "L6"
                r["ratified"] = "⬇已降档"
            else:
                # 线2 fail-safe：人工提名无裁决=按机械推导显示，L7 不计数（悬置态消灭）
                r["final_level"] = r["level"]
                r["ratified"] = "📋L7提名·待裁(按%s计)" % r["level"]
                _nominated += 1
        else:
            r["final_level"] = ml if ml else r["level"]
    l7_count = sum(1 for r in completed if r["final_level"] == "L7")
    below_l7 = len(completed) - l7_count
    _demotes = [k for k, v in _ratify.items() if v.get("verdict") == "降档"]
    fake_green = [r for r in completed if r.get("parity") == "fake-green"]

    if not summary_mode:
        print()
        print("=" * 70)
        print(f"📊 评估汇总（v1.2裁决口径=人工维持+fail-safe）: {len(completed)}端已接入, L7={l7_count}端(已裁决), 未达L7={below_l7}端, 其中L7提名待裁={_nominated}端")
        if _demotes:
            print(f"   ⚠ 推翻台账: 降档端 {len(_demotes)} 个（{_demotes}）——该端再提名须附增量证据（收紧观察·线3）")
        level_counts = {}
        for r in completed:
            level_counts[r["final_level"]] = level_counts.get(r["final_level"], 0) + 1
        for lv in sorted(level_counts.keys(), reverse=True):
            print(f"   {lv}: {level_counts[lv]}端")
        mech_counts = {}
        for r in completed:
            mech_counts[r["level"]] = mech_counts.get(r["level"], 0) + 1
        print(f"   机械推导参考: " + " / ".join(f"{lv}={n}端" for lv, n in sorted(mech_counts.items(), reverse=True)))
        if fake_green:
            print(f"   🚨 假绿警报: {len(fake_green)}端机械推导高于人工评定 —— {[r['name'] for r in fake_green]}")
    else:
        fg = f", FAKE_GREEN={len(fake_green)}" if fake_green else ""
        print(f"twin_maturity: L7={l7_count}/{len(completed)} ends (manual-governed), {below_l7} below L7{fg}")

    # 退出码：假绿优先报警（机械不许高于终审），其次未达L7
    sys.exit(2 if fake_green else (0 if below_l7 == 0 else 1))


if __name__ == "__main__":
    main()
