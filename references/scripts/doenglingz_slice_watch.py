#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doenglingz_slice_watch.py — 童灵切片新鲜度守望（W2 质变版·事件驱动）

设计定位（05-K2 §6.2 完整双层 + 愿景①全自动化「机制自动运转，不依赖人记得」）：
  规格书 SSOT 一变 → 自动重跑 k2_slice_generator → 自动重部署各端恒驻核文件。
  装载层由 launchd WatchPaths 事件触发（本端 A'C'D' 已验证模式），非轮询。

与各端 W2 的关系：
  - AutoClaw W2 = sha256 心跳比对（检测漂移，报而不治）；
  - WB = 注入式读 live slices（切片→注入天然新鲜，但规格书→切片无守卫）；
  - 本脚本 = 补上「规格书→切片→各端恒驻文件」全链自动同步，检测+自愈一体（对齐 PAT-023 改后同步守卫·检测+自愈混合先例）。

注册端（恒驻文件自动部署，格式：frontmatter 保留 + 定位块保留 + core/L6 正文刷新）：
  - Qoder CN: ~/.qoder-cn/rules/doenglingz-core.md
  - 其他端注册前须先实测该端恒驻文件格式，勿盲挂。

纪律：只读规格书；只写 slices 产物目录与注册端恒驻文件（写前 .bak 一份）；
     异常 exit 0（绝不制造 launchd 噪音）；无变化 stdout 为空 + 不写日志（静默）；有动作才留痕。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]")
# 数字分身中心：可用 DIGITALTWIN_HOME 覆盖（对齐 due_check/drift 提醒器先例·同一体系同一变量名·
# 便于脱敏入包后整体搬家；本文件全部产物/日志路径均从此派生，不留第二套硬编码根）
TWIN_HOME = os.environ.get("DIGITALTWIN_HOME") or os.path.join(BASE, "数字分身")
STATE_BUS = os.path.join(TWIN_HOME, "state_bus.json")
SPEC = os.path.join(TWIN_HOME, "童灵·人格规格书.md")
SLICES_DIR = os.path.join(TWIN_HOME, "K2切片蒸馏/slices")

# 生成器取件两态自适应（发现18修复·2026-10-18）：作者侧布局 K2切片蒸馏/（软链视图·A3/A4 留链）先命中；
# 装机态生成器真身在 k2-slice-generator/，K2切片蒸馏/ 只有 slices 数据 ⇒ 旧单路径悬空（rc=2 静默不干活）。
# 候选序固定：isfile 不中才下一候选；两候选全不中返回空串——调用方必须出声（⛔静默 return·PAT-023 病形零容忍）。
def _resolve_twin_gen(fname):
    for d in ("K2切片蒸馏", "k2-slice-generator"):
        p = os.path.join(TWIN_HOME, d, fname)
        if os.path.isfile(p):
            return p
    return ""

GENERATOR = _resolve_twin_gen("k2_slice_generator.py")
MANIFEST = os.path.join(SLICES_DIR, "manifest.json")
# PERSONA-BASE（人格基座·HEXACO）再生链 —— 2026-09-13 段四
PERSONA_VEC = os.path.join(TWIN_HOME, "童灵·人格向量.json")
PERSONA_GEN = _resolve_twin_gen("hexaco_slice_generator.py")
PERSONA_CLEAN = os.path.join(SLICES_DIR, "人格基座切片-童灵-端上纯净.md")
LOG = os.path.join(TWIN_HOME, "scripts/doenglingz_slice_watch.log")

# 注册端恒驻文件（自动部署对象）·v1.6.1（2026-10-02·Zwork 端纳端 by Zwork·皮叔令「L5/L6/L7 做到最好+待裁决按愿景最优解」）
#   格式 A（frontmatter+定位块+正文）: Qoder CN / Trae Work doenglingz-core.md → deploy_home()
#   格式 B（HTML 注释标记对）: ZCode AGENTS.md / AutoClaw USER.md / 豆包办公 USER.md / TeleAgent USER.md → deploy_marked()
#     同构约定：core 开始标记 → [core 结束标记(ZCode/豆包/TeleAgent 有·AutoClaw 无)] → L6 开始/结束标记。
HOMES = [
    os.path.expanduser("~/.qoder-cn/rules/doenglingz-core.md"),
    os.path.expanduser("~/.trae-cn/user_rules/doenglingz-core.md"),  # Trae Work 恒驻核（格式A·deploy_home）·2026-09-01 正名纳入自动同步
]
MARKED_HOMES = [
    os.path.expanduser("~/.zcode/AGENTS.md"),
    os.path.expanduser("~/.openclaw-autoclaw/workspace/USER.md"),
    # 2026-09-02 纳端：先实测该端恒驻文件格式、补标记对（写前留 .bak-20260902-nafmat）再注册。
    #   豆包：童灵节在「数字分身·童灵」段（画像层另有一份 L6·无标记对·不受部署影响）
    #   TeleAgent：真身文件在 ~/.local/share/TeleAgent/memory/USER.md（instructions 四文件之一，
    #              不是 06 旧登记的 ~/.config/TeleAgent/USER.md——那里根本没有该文件）
    os.path.expanduser("[记忆共享中心]/豆包办公系统文件/USER.md"),
    os.path.expanduser("~/.local/share/TeleAgent/memory/USER.md"),
    # 2026-09-11 纳端（WorkBuddy AI 国际版·第18端）：童灵节在 USER.md（复刻自国内版·core/L6 标记对在位）
    os.path.expanduser("~/.workbuddy-ai/USER.md"),
    # 2026-09-12 纳端（WorkBuddy 国内版·本源端补挂）：童灵节在 USER.md，K2 标记对 2026-09-12 补齐
    #   （国际版标记对"复刻自国内版"但国内版本体此前无标记对、不在注册表——跨端提请自查后闭环）
    os.path.expanduser("~/.workbuddy/USER.md"),
    # 2026-09-09 纳端（LobsterAI 端·皮叔令「核实完就动手」）：童灵节在 workspace-main/USER.md，
    # 标记对已实测写入（core 开始/结束 + L6 开始/结束）。恒驻核随 Project Context 每轮注入。
    # 2026-10-11 任务1 补漏（WB端01:10收口三写对冲丢失件·本轮实跑仍报USER.md标记结构异常为证）：
    #   LobsterAI 官方定位分家（2026-10-06）后恒驻核实体在 SOUL.md（标记对已焊入·WB端施工），
    #   USER.md 只剩导航节无标记对——注册改指 SOUL.md（判据随对象演化），USER.md 由该端自维不入机器管辖。
    os.path.expanduser("~/Library/Application Support/LobsterAI/openclaw/state/workspace-main/SOUL.md"),
    # 2026-10-02 纳端（Zwork 🧠·第 19 端·by Zwork）：恒驻核=[记忆共享中心]/AutoClaw/AGENTS.md 童灵节
    # 标记对 2026-10-02 补齐（core 开始/结束 + L6 开始/结束·格式 B 同构 ZCode AGENTS.md）。
    # 端分立：与 ~/.openclaw-autoclaw（AutoClaw 第 14 端）互不共用——本行属 Zwork 端自登。
    os.path.expanduser("[记忆共享中心]/AutoClaw/AGENTS.md"),
]


def sha12(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def log_line(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


# 各端正文里的规格书 hash 戳记（两种历史句式）。
# ⚠ 戳记原为手填：规格书一变即腐烂成假声明——2026-09-02 实测 Trae 端停在上一版、
#    AutoClaw 端停在更早一版，而两处戳记都自称"逐字一致"。改为由本脚本代写。
STAMP_TOKENS = [
    re.compile(r"(切片来源 hash\*\*：\s*`)[0-9a-f]{12}(`)"),
    re.compile(r"(规格书 hash `)[0-9a-f]{12}(`)"),
    re.compile(r"(src_hash=`)[0-9a-f]{12}(`)"),   # TeleAgent/豆包 句式·2026-09-02 纳端时补
]


def sync_stamps(text, src_hash):
    for pat in STAMP_TOKENS:
        text = pat.sub(lambda m: m.group(1) + src_hash + m.group(2), text)
    return text


def first_drop_home(path, core, l6, src_hash):
    """首落壳（2026-10-13 恒驻核根治·任务卡-恒驻核首落壳-20261010）：
    独立文件式 HOMES 端缺失 → 组装式首落（非空壳：frontmatter 最小形+core+L6+stamps）。
    受益=qodercn/trae 两端装机运行时；MARKED 族缺失属 setup 域，⛔不越权建整文件只显形。"""
    # 定位注释行确保 deploy_home 的 prefix 提取走 idx>0 正常路径（若无此行，core 首行=body 首行会落 split fallback 造成头部重复）；兼作首落来源标识
    body = "---\nalwaysApply: true\n---\n<!-- K2 首落壳 · slice_watch first_drop_home 组装 · 非手工空壳 -->\n" + core.strip() + "\n\n" + l6.strip() + "\n"
    new = sync_stamps(body, src_hash)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    log_line("W2 首落壳 | 已组装创建 %s（含身份骨架+L6·非空壳）" % path)
    return True


def deploy_home(path, core, l6, src_hash):
    """保留 frontmatter+定位块，刷新 core_slice+L6 正文。内容一致则不动（幂等）。"""
    cur = open(path, encoding="utf-8").read()
    parts = cur.split("---\n", 2)  # ['', frontmatter, body...]
    if len(parts) < 3:
        log_line("⚠️ %s frontmatter 结构异常，跳过部署" % path)
        return False
    front, body = parts[1], parts[2]
    first_line = core.split("\n", 1)[0]
    idx = body.find(first_line)
    prefix = body[:idx] if idx > 0 else body.split("## ⚡")[0]
    new = sync_stamps("---\n" + front + "---\n" + prefix + core.strip() + "\n\n" + l6.strip() + "\n",
                      src_hash)
    if new == cur:
        return False
    with open(path + ".bak", "w", encoding="utf-8") as f:
        f.write(cur)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    log_line("✅ 恒驻核已刷新: %s (bak=同名.bak)" % path)
    return True


CORE_START = "<!-- K2 core_slice 开始"
CORE_END = "<!-- K2 core_slice 结束 -->"
L6_START = "<!-- L6 反向约束 开始"
L6_END = "<!-- L6 反向约束 结束 -->"


def deploy_marked(path, core, l6, src_hash):
    """标记对部署（ZCode AGENTS.md / AutoClaw USER.md 同构）：
    「core 开始标记行后 → L6 开始标记行前」段替换为新 core（原段含 core 结束标记则保留）；
    「L6 开始标记行后 → L6 结束标记行前」段替换为新 L6。内容一致则不动（幂等）。"""
    cur = open(path, encoding="utf-8").read()
    i1, i2, i3 = cur.find(CORE_START), cur.find(L6_START), cur.find(L6_END)
    if not (0 <= i1 < i2 < i3):
        log_line("⚠️ %s 标记结构异常，跳过部署" % path)
        return False
    core_line_end = cur.find("\n", i1) + 1
    l6_line_end = cur.find("\n", i2) + 1
    has_core_end = CORE_END in cur[core_line_end:i2]
    new_core_block = core.strip() + "\n\n" + (CORE_END + "\n\n" if has_core_end else "")
    new_l6_block = l6.strip() + "\n\n"
    new = sync_stamps(cur[:core_line_end] + new_core_block + cur[i2:l6_line_end]
                      + new_l6_block + cur[i3:], src_hash)
    if new == cur:
        return False
    with open(path + ".bak", "w", encoding="utf-8") as f:
        f.write(cur)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    log_line("✅ 标记对恒驻核已刷新: %s (bak=同名.bak)" % path)
    return True


# ---------- K2 芯区指纹 · 分发者=判据唯一合法写者（2026-09-27 判据换向根治） ----------
# 病根：state_bus_sync 原把"上一轮观测值"当期望、又在本轮把观测值写回同一字段
#      ⇒ 检查者改写判据 ⇒ 端侧真漂移只红一次即自愈（假绿）；
#      且比对粒度是整文件，而机器只拥有标记块 ⇒ 端改块外合法内容必触发假红。
# 根治：①期望值由本脚本（分发者）在部署后按"机器拥有的那段"现算并登记；
#      ②检查器只读该字段，永不写；③覆盖判定取自本脚本的注册表，不抄文档。

def _core_anchor():
    """机器拥有区的起点锚 = core_slice 首行（格式A 无标记对时用它切割，块外不参与比对）。"""
    try:
        with open(os.path.join(SLICES_DIR, "core_slice.md"), encoding="utf-8") as f:
            return f.readline().rstrip("\n")
    except Exception:
        return ""


def k2_region_text(path):
    """端文件中机器拥有的区段：有 K2 标记对→取 core+L6 区段（格式B）；
    无标记对→取 core 首行至文件尾（格式A·frontmatter/定位块属端侧，不参与比对）。
    两者都定位不到 → 返回空串（不 fallback 成全文，避免把端侧自维内容误 bless 成基线）。"""
    try:
        with open(path, encoding="utf-8") as f:
            cur = f.read()
    except Exception:
        return ""
    i1, i2, i3 = cur.find(CORE_START), cur.find(L6_START), cur.find(L6_END)
    if 0 <= i1 < i2 < i3:
        return cur[cur.find("\n", i1) + 1:i3 + len(L6_END)]
    anchor = _core_anchor()
    idx = cur.find(anchor) if anchor else -1
    return cur[idx:] if idx >= 0 else ""


def k2_region_hash(path):
    txt = k2_region_text(path)
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:12] if txt else ""


def dispatch_covered(path):
    """该恒驻文件是否落在 W2 自动分发覆盖内（判据源=本脚本注册表，非文档手抄）。"""
    target = os.path.normpath(os.path.expanduser(path))
    return any(os.path.normpath(h) == target for h in HOMES + MARKED_HOMES)


def record_baselines(spec_hash):
    """分发后立基线：把各端"机器拥有区段"的期望指纹登记进 state_bus。
    一端多 id 共用同一物理文件（Trae Work/TraeCode 共享 user_rules）⇒ 按路径反查全部 id，不漏账。"""
    try:
        with open(STATE_BUS, encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        log_line("⚠️ 基线登记跳过：state_bus 不可读 %s" % str(e)[:100])
        return 0
    index = {}
    for eid, v in (sb.get("ends") or {}).items():
        p = v.get("k2_core_path")
        # 多文件恒驻核（2026-10-06 LobsterAI 分家态·str/list 双形态）：此前 list 直入
        # expanduser 抛 TypeError 被顶层异常放行吞掉→该日起基线登记静默中断（2026-10-11 根治）
        for pp in (p if isinstance(p, list) else [p]):
            if pp:
                index.setdefault(os.path.normpath(os.path.expanduser(pp)), []).append(eid)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    touched = unregistered = 0
    for h in HOMES + MARKED_HOMES:
        if not os.path.exists(h):
            continue
        ids = index.get(os.path.normpath(h))
        if not ids:
            log_line("⚠️ 基线无处登记：%s 未被任何端登记（分发覆盖≠端清单·双本账前兆）" % h)
            unregistered += 1
            continue
        rh = k2_region_hash(h)
        if not rh:
            log_line("⚠️ 基线计算失败（区段为空）：%s" % h)
            continue
        for eid in ids:
            e = sb["ends"].setdefault(eid, {})
            e["expected_hash"] = rh
            e["expected_src"] = spec_hash
            e["dispatch_at"] = now
            touched += 1
    try:
        with open(STATE_BUS, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_line("⚠️ 基线写入失败 %s" % str(e)[:100])
        return 0
    if touched:
        log_line("基线已登记 %d 端 | src=%s%s"
                 % (touched, spec_hash,
                    " | ⚠️%d 个恒驻文件未登记" % unregistered if unregistered else ""))
    return touched


NAMING_GUARD = os.path.join(TWIN_HOME, "scripts/doenglingz_naming_guard.py")


def naming_gate(stage):
    """分发前闸：**只有"分发源本身被污染"才阻断**——C1 命名红线／C2 可寻址性／C3 切片派生一致性。

    ⚠️ 判据必须与闸的职责同源（2026-09-02 实跑踩坑后修正）：C4（文档声明过期）与 C5（下游端文件落后）
       不是分发源污染信号，把它们计入阻断集会造成死锁——C5 检出的正是本轮部署要修的漂移，
       于是"永不部署、永不恢复"。此类红改为 ⚠️ 观察行：仍留痕、不静默，但不拦自愈。

    ⚠️ 仪器故障不等于违规：校验器自身失效（rc=2 / 不可调用）时放行并记 ⚠️——
       否则校验器一坏就让全端切片停止更新，制造比污染更难发现的静默失效。
    """
    try:
        r = subprocess.run([sys.executable, NAMING_GUARD, "--json"],
                           capture_output=True, text=True, timeout=30)
    except Exception as e:
        log_line("⚠️ 命名校验器不可调用（放行不阻断）: %s" % str(e)[:150])
        return True
    if r.returncode == 2:
        log_line("⚠️ 命名校验器自身失效 rc=2（放行不阻断）: %s" % r.stdout[:150])
        return True
    if r.returncode != 0:
        try:
            reds = json.loads(r.stdout).get("red", [])
        except Exception:
            reds = ["C1 校验器输出不可解析（按最严处置）: " + r.stdout[:200]]
        blocking = [x for x in reds if re.match(r"^C[123]\b", x)]
        observe = [x for x in reds if not re.match(r"^C[123]\b", x)]
        if observe:
            log_line("⚠️ %s 有 %d 项非污染源红（不阻断·部署即自愈）：%s"
                     % (stage, len(observe), " | ".join(observe)[:400]))
        if blocking:
            log_line("🔴 命名红线闸阻断 %s（%d 红）：%s"
                     % (stage, len(blocking), " | ".join(blocking)[:400]))
            return False
    return True


def heartbeat():
    # 心跳戳记：每次运行写入（无论有无变更），供 launchd_health_check.sh 的 last_run 豁免机制判定活性。
    try:
        with open(os.path.join(os.path.dirname(LOG), "last_run_doenglingz_slice_watch.ts"), "w", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S\n"))
    except Exception:
        pass


def persona_freshness():
    """PERSONA-BASE 切片新鲜度（段四·2026-09-13）：向量更新 → 自动重跑 hexaco 生成器。

    判据用 **mtime 比对**（向量文件新于切片产物 ⇒ 需再生），⛔不用 persona_manifest.src_hash
    —— 该字段原用 Python 内建 hash()，有 per-process 随机化，三次运行三个值，不可作判据
    （2026-09-13 实测；生成器本体已改 sha256，但历史 manifest 存档值仍是旧算法的，故不取）。
    副作用边界（如实声明）：hexaco_slice_generator 会**直部署 ZCode 的 AGENTS.md**（其设计如此），
    多端并行会话期间可能与他端改动交错 ⇒ 仅在向量确实更新时触发，不做例行轮询再生。
    """
    try:
        if not (os.path.exists(PERSONA_VEC) and os.path.exists(PERSONA_CLEAN)):
            return
        if os.path.getmtime(PERSONA_VEC) <= os.path.getmtime(PERSONA_CLEAN):
            return
        if not PERSONA_GEN:
            log_line("🔴 PERSONA_GEN 悬空 | 两候选均不存在: %s/{K2切片蒸馏,k2-slice-generator}/hexaco_slice_generator.py —— PERSONA-BASE 无法再生，需人工处置" % TWIN_HOME)
            return
        log_line("W2-PERSONA 触发 | 向量新于切片 → 重跑 hexaco_slice_generator")
        r = subprocess.run([sys.executable, PERSONA_GEN], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log_line("❌ hexaco 生成器失败 rc=%s stderr=%s" % (r.returncode, r.stderr[:200]))
            return
        log_line("✅ PERSONA-BASE 切片已再生（向量更新触发）")
    except Exception as e:
        log_line("⚠️ persona freshness 异常放行: %s" % str(e)[:150])


def main():
    heartbeat()
    persona_freshness()
    if not os.path.exists(SPEC):
        return
    spec_hash = sha12(SPEC)
    try:
        man_hash = json.load(open(MANIFEST, encoding="utf-8")).get("src_hash", "")
    except Exception:
        man_hash = ""

    if spec_hash == man_hash:
        # 切片与规格书同步——仍检查注册端恒驻文件是否落后（生成器跑过但部署断链的场景）
        core_p = os.path.join(SLICES_DIR, "core_slice.md")
        l6_p = os.path.join(SLICES_DIR, "L6_反向约束.md")
        if not (os.path.exists(core_p) and os.path.exists(l6_p)):
            return
        core, l6 = open(core_p, encoding="utf-8").read(), open(l6_p, encoding="utf-8").read()
        if not naming_gate("部署自愈"):
            return
        changed = False
        for h in HOMES:
            if os.path.exists(h):
                if deploy_home(h, core, l6, spec_hash):
                    changed = True
            elif first_drop_home(h, core, l6, spec_hash):
                changed = True
        for h in MARKED_HOMES:
            if os.path.exists(h):
                if deploy_marked(h, core, l6, spec_hash):
                    changed = True
            else:
                log_line("W2 首落缺口显形 | %s 不存在（标记区族属 setup 领地·不代建·装机步骤应创建）" % h)
        if changed:
            log_line("W2 部署自愈 | spec=%s (切片已新)" % spec_hash)
        record_baselines(spec_hash)
        return

    if not GENERATOR:
        log_line("🔴 GENERATOR 悬空 | 两候选均不存在: %s/{K2切片蒸馏,k2-slice-generator}/k2_slice_generator.py —— 切片不会更新，需人工处置" % TWIN_HOME)
        return
    log_line("W2 触发 | spec %s → 重跑生成器" % spec_hash)
    r = subprocess.run(
        [sys.executable, GENERATOR], capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0:
        log_line("❌ 生成器失败 rc=%s stderr=%s" % (r.returncode, r.stderr[:300]))
        return
    core_p = os.path.join(SLICES_DIR, "core_slice.md")
    l6_p = os.path.join(SLICES_DIR, "L6_反向约束.md")
    core, l6 = open(core_p, encoding="utf-8").read(), open(l6_p, encoding="utf-8").read()
    if not naming_gate("全链刷新"):
        return
    for h in HOMES:
        if os.path.exists(h):
            deploy_home(h, core, l6, spec_hash)
        else:
            first_drop_home(h, core, l6, spec_hash)
    for h in MARKED_HOMES:
        if os.path.exists(h):
            deploy_marked(h, core, l6, spec_hash)
        else:
            log_line("W2 首落缺口显形 | %s 不存在（标记区族属 setup 领地·不代建）" % h)
    log_line("W2 全链刷新完成 | spec=%s" % spec_hash)
    record_baselines(spec_hash)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_line("⚠️ 异常放行: %s" % str(e)[:200])
    sys.exit(0)
