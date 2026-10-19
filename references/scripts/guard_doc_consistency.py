#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.2
"""
guard_doc_consistency.py — 守卫「文档声称」vs「守卫全宇宙实挂」一致性巡检

根因修复（2026-08-20）：
    手工维护的文档名单 ≠ settings.json 实际挂载（同源漂移，
    与 kb-index-guard 沉默死同一根因）。本脚本让 settings.json 成为
    唯一真相源（SSOT），文档对挂载状态的声称必须对其负责——
    文档说「X 已挂 @Stop」但 settings.json 没有 → 即漂移，必须修文档/机制，
    不得 whack-a-mole 改名单。

检查方向：
    ① 正向（硬·exit 1）：文档 §二 成员表声称某脚本 Stop/UserPromptSubmit 实挂，
       但聚合 9 宿主真相源后该脚本在任一宿主均未实挂 → 文档虚报。
       （2026-08-24 根治：原仅以 WorkBuddy settings.json 为真相源→跨宿主守卫误报 phantom）
    ② 反向（可选 --reverse）：注册表(守卫编写规范 §四)成员且 settings.json 实际挂载，
       但 §二 未登记其挂载状态 → 文档遗漏（提示补登，不计入硬漂移）。
    ③ 三件套（硬·exit 1·2026-08-22 §3.0 立）：注册表登记的脚本必须在"守卫全宇宙"已落地——
       落点=多仓库 git 跟踪(~/个人AI档案+记忆琥珀) ∪ 跨系统宿主目录(~/.workbuddy/hooks、
       ~/.openclaw-autoclaw/hooks、记忆琥珀/engine、DSH/Skill路由引擎) ∪ git pre-commit Hook。
       仓库内脚本根存在但未跟踪（孤儿·§3.0 ①未入库）→ 硬漂移；
       全宇宙守卫目录均找不到（真缺失）→ 硬漂移。
       （2026-08-24 根治：原仅扫 3 仓库根→仓库外宿主原生守卫误报 ghost）

用法：
    python3 guard_doc_consistency.py
    python3 guard_doc_consistency.py --reverse
    python3 guard_doc_consistency.py --script-center   # 开发工具/ ↔ scripts_manifest 对账
    python3 guard_doc_consistency.py --settings ~/.workbuddy/settings.json \
        --docs 守卫家族实例.md 守卫编写规范.md --json

退出码：0=一致  1=发现硬漂移  2=用法/文件错误
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

# —— 默认路径（与当前部署一致）——
# 2026-10-06 根治：原 DEFAULT_DOCS 硬编码 ~/记忆蓝图 为家根错基（家根无此目录）⇒ 每轮 FileNotFoundError 崩·Stop 链 exit1 实证。
HOME = os.path.expanduser("~")
_CFG_ROOT = os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.join(HOME, ".workbuddy")
DEFAULT_SETTINGS = os.path.join(_CFG_ROOT, "settings.json")

def _archive_root():
    """MC 声明驱动（条文47同族·对齐 doenglingz_guard.sh 先例）：优先 runtime_paths.get archive_root；
    失败回退 <HOME>/个人AI档案（作者态）。⛔回退串不带数字伪装有效数据。"""
    try:
        _rp = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            os.pardir, "脚本中心", "runtime_paths.py"))
        _r = subprocess.run(["python3", _rp, "get", "archive_root"],
                            capture_output=True, text=True, timeout=15)
        _p = _r.stdout.strip()
        if _r.returncode == 0 and _p and os.path.isdir(_p):
            return _p
    except Exception:
        pass
    return os.path.expanduser("[记忆共享中心]")

DEFAULT_DOCS = [
    os.path.join(_archive_root(), "记忆蓝图", "04_系统文件设计",
                 "布洛陀脚本架构设计哲学", "02-脚本家族实例", "守卫家族实例.md"),
    os.path.join(_archive_root(), "记忆蓝图", "04_系统文件设计",
                 "布洛陀脚本架构设计哲学", "守卫编写规范.md"),
]

SCRIPT_RE = re.compile(r"([A-Za-z0-9_\-]+\.(?:py|sh))")

# —— §二 挂载声称配对常量（2026-09-10 童灵根治·假阳根因）——
# 事件词表（认领匹配顺序即此顺序）
HOOK_EVENTS = ("UserPromptSubmit", "SessionStart", "PreToolUse",
               "PermissionRequest", "PostToolUse", "Stop")
# 否定护栏：部署格写「不依赖 Hook 事件」= 主动声明非 Hook 挂载，Hook 兜底不得触发。
# 实证：CatPaw 行「**patrol 降级**（launchd/cron 调度·不依赖 Hook 事件）」旧版经兜底
# 误升为 Stop 挂载 → 2 条假阳。
_HOOK_NEG_RE = re.compile(r"(?:不|无|非|未)[^|。；\n]{0,8}?[Hh]ook|[Hh]ook[^|。；\n]{0,4}?(?:不|无|非|未)")
# 段切分符：`+` `|` `；` `;` 换行——文档在同一格内并列多脚本/多部署形态时的天然边界。
_SEG_SPLIT_RE = re.compile(r"[+|；;\n]")


# —— 跨宿主真实挂载聚合（2026-08-24 根治：原仅读 WorkBuddy settings.json→跨宿主守卫误报 phantom）——
# 真相源=各宿主运行时配置本身（与 platform_adaptation_check 同源·连看复用口径，不自造第二套）。
HOST_CONFIGS = {
    "workbuddy": os.path.join(HOME, ".workbuddy", "settings.json"),
    "workbuddyai": os.path.join(HOME, ".workbuddy-ai", "settings.json"),
    "qoder-desktop": os.path.join(HOME, ".qoder", "settings.json"),
    "qoder-cn": os.path.join(HOME, ".qoder-cn", "settings.json"),
    "zcode": os.path.join(HOME, ".zcode", "cli", "config.json"),
    "autoclaw": os.path.join(HOME, ".openclaw-autoclaw", "openclaw.json"),
    "lobsterai": os.path.join(HOME, "Library", "Application Support", "LobsterAI", "openclaw", "state", "openclaw.json"),
    "dsh": os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "five-layer-memory", "src", "index.js"),
    "hermes": os.path.join(HOME, ".hermes", "config.yaml"),
    "traework": os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "Skill路由引擎", "scripts", "route_traework_patrol.sh"),
}


def _scripts_in_text(text):
    """从任意宿主配置原文粗提所有 .py/.sh 完整基名（含扩展名·与 load_actual/scan_guard_universe 口径一致）。"""
    return set(m.group(1) for m in SCRIPT_RE.finditer(text))


def load_all_host_mounted():
    """返回在所有宿主运行时配置中真实出现过的守卫脚本基名集合（跨宿主真相源聚合）。
    用于消除 phantom 误报：某守卫在 DSH/QoderCN 等宿主实挂、但不在 WorkBuddy settings.json
    时，原逻辑误判为'声称未挂'；聚合后只要'某宿主实挂'即非 phantom。"""
    mounted = set()
    for _host, path in HOST_CONFIGS.items():
        try:
            mounted |= _scripts_in_text(open(path, encoding="utf-8").read())
        except Exception:
            continue
    return mounted


# ——————————————————————————————————————————————
# 守卫全宇宙（真相源全集·与 platform_adaptation_check 同源口径·不自造第二套）
#   ① 多仓库 git 跟踪（~/个人AI档案 + 记忆琥珀，各自版本化）
#   ② 仓库内脚本根（孤儿判定·在仓库内但未 git add → 提示补 track）
#   ③ 跨系统宿主运行时目录（WorkBuddy/AutoClaw 宿主原生 hook + DSH/Skill路由引擎）
#      —— 这些目录的守卫由各自系统版本化，不在 ~/个人AI档案 仓库内，但属"已落地"合法位置
#   ④ git pre-commit Hook（commit_sweep_guard 类·DSH 皮叔令根治扫库扯皮·不在 JSON 配置）
# ——————————————————————————————————————————————
KNOWN_REPOS = [
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆琥珀"),
]
REPO_SCRIPT_ROOTS = [
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "自定义层"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置"),
]
EXTERNAL_GUARD_DIRS = [
    os.path.join(_CFG_ROOT, "hooks"),
    os.path.join(HOME, ".openclaw-autoclaw", "hooks"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆琥珀", "engine"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "five-layer-memory"),
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "Skill路由引擎", "scripts"),
]
PRECOMMIT_REPOS = KNOWN_REPOS + [
    os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "five-layer-memory"),
]


def load_git_precommit_mounted():
    """git pre-commit Hook 实挂的守卫基名集合（commit_sweep_guard 类·DSH 皮叔令根治扫库扯皮）。

    这类守卫挂在仓库 .git/hooks/pre-commit（或 core.hooksPath 重定向目标），
    根本不出现在任何 JSON 配置——原逻辑只认 settings.json → 永远误判 phantom。
    2026-08-24 根治：纳入 git pre-commit 真相源。"""
    mounted = set()
    for repo in PRECOMMIT_REPOS:
        hook = os.path.join(repo, ".git", "hooks", "pre-commit")
        try:
            mounted |= _scripts_in_text(open(hook, encoding="utf-8").read())
        except Exception:
            pass
        # core.hooksPath 重定向（pre-commit 可能不在默认 .git/hooks/）
        try:
            hp = subprocess.run(["git", "-C", repo, "config", "--get", "core.hooksPath"],
                                capture_output=True, text=True).stdout.strip()
            if hp:
                mounted |= _scripts_in_text(open(os.path.expanduser(hp), encoding="utf-8").read())
        except Exception:
            pass
    return mounted


def load_registry_guards_mounted():
    """registry_guards.sh 目录自动发现通道（2026-08-24 补·doenglingz_guard 假阳性根治）。

    registry_guards.sh 挂 WorkBuddy Stop（settings.json 可见），运行时扫描 GUARD_DIR 下
    全部 *guard.sh（排除 *.bak*）自动发现并逐个执行——这类守卫**不出现在任何 JSON 配置
    文本中**（仅目录存在），原聚合逻辑误判"文档虚报"。修复：读 registry_guards.sh 源码
    解析 GUARD_DIR（单一事实源·不硬编码路径），扫描该目录同构收录。"""
    mounted = set()
    reg = os.path.join(_CFG_ROOT, "hooks", "registry_guards.sh")
    guard_dir = None
    try:
        for line in open(reg, encoding="utf-8"):
            m = re.search(r'GUARD_DIR="([^"]+)"', line)
            if m:
                guard_dir = os.path.expanduser(m.group(1))
                if guard_dir.startswith("$HOME"):
                    guard_dir = os.path.join(os.environ.get("HOME", ""), guard_dir[len("$HOME"):].lstrip("/"))
                break
    except Exception:
        return mounted
    if guard_dir and os.path.isdir(guard_dir):
        for name in os.listdir(guard_dir):
            if name.endswith("guard.sh") and ".bak" not in name:
                mounted.add(name)
    return mounted


# ——————————————————————————————————————————————
# ① 解析 settings.json 实际挂载（SSOT）
# ——————————————————————————————————————————————
def load_actual(settings_path):
    """返回 {basename: set(events)} 实际挂载。
    兼容两种宿主 schema（2026-08-27 根治 zcode 哑通道·--settings TypeError bool 实证）：
      - WorkBuddy 型 {"hooks": {Stop: [组,...]}}
      - ZCode 型     {"hooks": {"enabled": bool, "events": {Stop: [组,...]}}}"""
    with open(settings_path, encoding="utf-8") as f:
        cfg = json.load(f)
    actual = {}
    hooks = cfg.get("hooks", {})
    events_map = hooks.get("events", {}) if isinstance(hooks, dict) and isinstance(hooks.get("events"), dict) else hooks
    if not isinstance(events_map, dict):
        return actual
    for event, entries in events_map.items():
        if not isinstance(entries, list):   # enabled 等标量键跳过（bool 不可迭代即由此而来）
            continue
        for grp in entries:
            # 兼容两种结构：{"hooks":[{"command":...}]} 与 直接 {"type":"command","command":...}
            items = grp.get("hooks", [grp]) if isinstance(grp, dict) else []
            for it in items:
                m = SCRIPT_RE.search(it.get("command", ""))
                if m:
                    actual.setdefault(m.group(1), set()).add(event)
    return actual


# ——————————————————————————————————————————————
# ② 解析 守卫家族实例.md §二 成员表的挂载声称
# ——————————————————————————————————————————————
def extract_section(text, start_pat, end_pat):
    m = re.search(start_pat + r".*?(?=" + end_pat + r")", text, re.S)
    return m.group(0) if m else ""


def _seg_events(seg):
    """段内**显式**事件词（词边界匹配，防 PostToolUse 吞掉 Failure 后缀）。"""
    return [e for e in HOOK_EVENTS if re.search(r"\b" + e + r"\b", seg)]


def _seg_hook_fallback(seg):
    """旧口径兜底：段内写 Hook、无显式事件词、且无否定护栏 → 按 Stop 认领（AutoClaw 先例）。

    ⛔ 只允许用于「部署格 + 该段内无脚本名」的整组认领场景。两类幽灵声称实证：
      · 2026-08-27 hermes_read_evidence_guard：成员列 `route-audit-hook` 复合词；
      · 2026-09-10 qodercn_config_guard：部署列内嵌他端路径 `hooks/crossend_guard.py`。
    两者都是「段内提到 Hook 字样」≠「本行脚本挂在该 Hook 上」，故兜底收紧到唯一安全场景。
    """
    if _seg_events(seg):
        return []
    if re.search(r"[Hh]ook", seg) and not _HOOK_NEG_RE.search(seg):
        return ["Stop"]
    return []


def load_family_claims(doc_path, actual_mounts):
    """从 §二 成员表提取 (script_basename, event) 挂载声称。

    2026-09-10 童灵根治（存量孤儿治理轮·假阳根因三类，均在真实数据上实测复现）：
      ① 否定词盲区：部署格写「不依赖 Hook 事件」→ 旧版按 `re.search("[Hh]ook")` 兜底
         认领成 Stop 挂载（CatPaw 行 → catpaw_skill_health_guard.py / route_catpaw_patrol.sh 两条假阳）。
      ② 一格多脚本外溢：成员格并列 N 个脚本时，格内任一处事件词被认领给全部 N 个
         （系统日志行：Stop 实属 systemlog_stophook_check.py，却外溢给
         systemlog_normalize_fix.py / normalize_tool.py 两条假阳）。
      ③ 跨脚本串味：部署格内嵌他脚本时，其事件被认领给成员列脚本
         （position3 行「position3_notify.py 挂 UserPromptSubmit」→ 旧版算给 position3_audit.py 假阳）。

    改法：按段（`+` `|` `；` `;` 换行）拆格配对——
      · 成员格：事件只归「同段内出现的脚本」，不再外溢到整格；
      · 部署格：段内有脚本名 → 事件归该脚本（治③）；段内无脚本名 → 按整组认领
        （保住 registry_guards / doenglingz_guard 类**真实**整组声称，不误伤）。
    ⛔ 不改成员列脚本抽取口径（SCRIPT_RE + stem 兜底）——配对粒度是本次唯一变量。
    """
    claims = []
    text = open(doc_path, encoding="utf-8").read()
    sec = extract_section(text, r"## 二、", r"\n## 三、")
    if not sec:
        return claims
    stems = {os.path.splitext(b)[0]: b for b in actual_mounts}
    seen = set()

    def _claim(script, event):
        if (script, event) not in seen:
            seen.add((script, event))
            claims.append((script, event))

    def _scripts_whole(chunk):
        """成员列整体抽取（口径同旧版：SCRIPT_RE 命中即止，否则按 stem 兜底）。"""
        found = SCRIPT_RE.findall(chunk)
        if not found:
            for tok in re.findall(r"[A-Za-z][A-Za-z0-9_\-]+", chunk):
                tok = tok.strip("*")
                if tok in stems:
                    found.append(stems[tok])
        return found

    def _scripts_seg(chunk):
        """段内抽取：只认带扩展名的脚本名（⛔不做 stem 兜底，避免段内散词误升为脚本）。"""
        return SCRIPT_RE.findall(chunk)

    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        # 删除线行=已退役≠挂载声称（reply_format_guard 残余虚报根治·2026-08-27）：
        # ~~…~~ 整行退役标注曾让解析器仍按"Stop Hook"字样算作声称→虚报假阳性，跳过。
        if cells[0].startswith("~~") or cells[1].startswith("~~"):
            continue
        member_col, deploy_col = cells[1], cells[2]
        # DSH 平台行豁免（真相所有权）：DSH 挂载真相源=插件 STOP_GUARDS 数组，
        # 不走 WorkBuddy settings.json——不豁免则永远假阳性（2026-08-22 实证）
        if "DSH" in cells[0]:
            continue
        row_scripts = _scripts_whole(member_col)
        # ① 成员格：段内显式配对（治②——事件不外溢到同格其他脚本）
        #    ⛔ 成员格不做 Hook 兜底：`route-audit-hook` 类复合词会制造幽灵声称（2026-08-27 实证）
        for seg in _SEG_SPLIT_RE.split(member_col):
            evs = _seg_events(seg)
            if not evs:
                continue
            for s in _scripts_seg(seg):
                for e in evs:
                    _claim(s, e)
        # ② 部署格：段内有脚本名 → 只认显式事件并归该脚本（治③跨脚本串味）；
        #    段内无脚本名 → 显式事件或 Hook 兜底，按整组认领（保真实整组声称不误伤）
        for seg in _SEG_SPLIT_RE.split(deploy_col):
            seg_scripts = _scripts_seg(seg)
            if seg_scripts:
                evs, targets = _seg_events(seg), seg_scripts
            else:
                evs, targets = (_seg_events(seg) or _seg_hook_fallback(seg)), row_scripts
            if not evs:
                continue
            for s in targets:
                for e in evs:
                    _claim(s, e)
    return claims


# ——————————————————————————————————————————————
# ③ 解析 守卫编写规范.md §四 注册表（已知守卫全集）
# ——————————————————————————————————————————————
def load_registry(doc_path):
    """返回注册表脚本 stem 集合（用于反向检查）。"""
    names = set()
    if not os.path.exists(doc_path):
        return names
    text = open(doc_path, encoding="utf-8").read()
    sec = extract_section(text, r"## 四", r"\n## 五")
    if not sec:
        return names
    for line in sec.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        # §四 有两种行形：脚本在前（| script.py | 辖区 | …）与辖区在前
        # （| 引擎·免疫自愈 | immunity_l1_draft.py v2.0.0 | 挂载 | 功能…）。
        # 旧版只读 cells[0] ⇒ 辖区在前行里的脚本**全部漏出监管集**（2026-09-18 实测：
        # immunity_l1_draft / antibody_gate / mirror-* / generate_release 等 96→? 在册项），
        # 件⑥回流门禁据此建 = 对自己该守的东西报绿（判据缺一半·假绿）。
        # 只扫前两列：第 3/4 列是功能与真相源说明，里面提到的他脚本不该被当"在册守卫"
        # （否则 ③号孤儿/幽灵 检查会拿散文里的名字报警=假红）。
        row_txt = re.sub(r"~~[^~]*~~", "", line)  # 退役删除线=不在册（先例 load_family_claims T8）
        cells_r = [c.strip() for c in row_txt.strip().strip("|").split("|")]
        for col in cells_r[:2]:
            for m in SCRIPT_RE.finditer(col):
                names.add(os.path.splitext(m.group(1))[0])
    return names


# ——————————————————————————————————————————————
# ③ 三件套校验（§3.0 登记三件套·件①入库）：注册表 ↔ 守卫全宇宙已落地
# ——————————————————————————————————————————————
def scan_guard_universe():
    """返回 (tracked, disk)：
    tracked = 多仓库 git 跟踪基名并集（~/个人AI档案 + 记忆琥珀）
    disk   = 仓库内脚本根 + 跨系统宿主运行时目录 磁盘文件并集
    2026-08-24 根治：原仅 git ls-files(~/个人AI档案) + 扫 3 仓库根 →
    仓库外宿主原生守卫(registry_guards/crossend_guard)与记忆琥珀引擎(amber-checkup)误报 ghost。
    """
    tracked = set()
    for repo in KNOWN_REPOS:
        if not os.path.isdir(repo):
            continue
        try:
            # core.quotepath=false：中文路径不转义（否则 basename 匹配全失效）
            r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=false",
                                "ls-files"], capture_output=True, text=True)
            tracked |= {os.path.basename(line) for line in r.stdout.splitlines() if line}
        except Exception:
            continue
    disk = set()
    for root in REPO_SCRIPT_ROOTS + EXTERNAL_GUARD_DIRS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in ("node_modules", "__pycache__", ".git")]
            disk.update(filenames)
    return tracked, disk


def check_registry_resolved(registry_stems):
    """返回 (orphans, ghosts)：
    resolved = 多仓库任一 git 跟踪 或 任一已知守卫目录磁盘存在 → 合法（已落地）
    orphans  = 落在仓库内脚本根但 ~/个人AI档案 仓库未跟踪（提示 git add·硬漂移）
    ghosts   = 全宇宙守卫目录均找不到（真缺失·硬漂移）
    2026-08-24 根治：外部宿主目录(WorkBuddy/AutoClaw hooks)与记忆琥珀引擎视为已落地合法位置，
    不再误报 ghost；孤儿判定仅限仓库内脚本根，避免外部系统目录被错判。
    """
    tracked, disk = scan_guard_universe()
    orphans, ghosts = [], []
    for stem in sorted(registry_stems):
        cands = (stem + ".py", stem + ".sh", stem + ".ps1")
        if any(c in tracked for c in cands):
            continue  # 多仓库任一已跟踪 ✓
        if any(c in disk for c in cands):
            # 仓库内脚本根且未跟踪 → 孤儿；外部宿主目录已落地 → 合法跳过
            if any(os.path.exists(os.path.join(r, c)) for r in REPO_SCRIPT_ROOTS for c in cands):
                orphans.append(stem)
        else:
            ghosts.append(stem)
    return orphans, ghosts


# ——————————————————————————————————————————————
# ⑥ 件④哲学回流（2026-09-18 新增）：§四注册表在册 → 家族实例 §二 须提及
# 立起来的原因：守卫编写规范 §3.0 件④ 原文自承「暂无独立机械闸门，靠执行端纪律」——
#   2026-09-15 同型漏项两次（triwich_closeout / skill_selfcontained），2026-09-18 又两次
#   （secret_key_guard / ttl_expiry_guard：§四在册、脚本已入库、钩子实挂，家族实例零命中）。
#   同一条纪律第四次靠人追问才补上 ⇒ 该从自律升物理门禁（记忆判例「自律门禁改物理门禁」）。
# 分级（防假红风暴·G4 预存态透明）：
#   BACKFLOW_STOCK 里的 = 存量债务 → ⚪ 只显形不硬红；不在其中的新缺 = 🔴 计入 drift。
# ——————————————————————————————————————————————
BACKFLOW_STOCK = set([
    # 2026-09-18 首跑实测存量（件④历史欠账·只显形不硬红；⛔新项不得加入本名单，加了就等于把新欠账洗成存量。清账方式=在家族实例 §二 补该脚本的辖区行后从这里删除）
    "check_selfimprove_gate",
    "doenglingz_guard_dsh",
    "doenglingz_slice_watch",
    "evolution_deviation",
    "generate_release",
    "git_commit_safe",
    "hook_protocol",
    "kb_concept_lint",
    "kb_topology_scan",
    "route_evolution_suggest",
    "script_family_check",
    "self_optimization_engine",
    "symlink_guard",
    "teleagent_skill_health_guard",
    "traecode_isolation_guard",
    "traecode_title_namer",
    "triwich_seal",
    "verify_all_skills",
    "verify_resources",
    "verify_skill_version",
    "verify_skill_version_hook",
])


def check_philosophy_backflow(registry_stems, family_text, stock=None):
    """返回 (missing, new_debts, stock_debts)：
    missing     = §四在册但家族实例全文无该脚本名词干
    new_debts   = missing - stock   → 硬红（计入 drift）
    stock_debts = missing & stock   → ⚪ 存量显形
    判据取干名（不含扩展名）·全文匹配——宁漏勿误：只抓"完全没提过"的，不抓措辞差异。
    """
    stock = BACKFLOW_STOCK if stock is None else set(stock)
    # 归一比较：家族实例习惯用连字符名（audit-staleness），注册表用下划线（audit_staleness）——
    #   不归一即造 27 条假红（2026-09-18 实测），新门禁上线即噪音=守卫被无视=失效（§八-3 宁漏勿误）
    text = (family_text or "").lower().replace("-", "_")
    missing, new_debts, stock_debts = [], [], []
    for stem in sorted(registry_stems):
        if not stem or stem.lower().replace("-", "_") in text:
            continue
        missing.append(stem)
        (stock_debts if stem in stock else new_debts).append(stem)
    return missing, new_debts, stock_debts

# ——————————————————————————————————————————————
# ④ 查悬空（2026-08-22 反哺·成长箱 PAT-033 族落地）：文档"必做/待落地"项 ↔ 实现痕迹
#   宁漏勿误：仅判定文本可机械提取的 明确绝对路径/脚本名 存在性；
#   语义性（如"已渲染/已接 hook"）不强判——宁可漏掉也不误报（守卫变噪音=被无视=失效）。
# ——————————————————————————————————————————————
PENDING_MARK = re.compile(r"必做|待落地|待决|🔴\s*待|未实现|未落地|待补|接手必做|真实空缺")
ABSOLUTE_PATH = re.compile(r"(?:/Users/[A-Za-z0-9_\-]+|~\b)[A-Za-z0-9_/\.\-\u4e00-\u9fff]+\.(?:json|py|sh|md|js)")


def scan_pending_todo(todo_dir, repo_root, tracked, disk):
    """返回 [{src_line, kind, name, reason}] 悬空项：文档声称"必做/必补"但无落地痕迹。
    空目录/不可读 → []（宁漏勿误·前置条件缺失不放警）。"""
    dangling = []
    if not os.path.isdir(todo_dir):
        return dangling
    for root, dirnames, filenames in os.walk(todo_dir):
        dirnames.sort()
        for fn in sorted(filenames):
            if not (fn.endswith(".md") or fn.endswith(".json")):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, todo_dir)
            try:
                text = open(p, encoding="utf-8").read()
            except Exception:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if not PENDING_MARK.search(line):
                    continue
                src = f"{rel}:{lineno}"
                for m in ABSOLUTE_PATH.finditer(line):
                    cand = m.group(0).replace("~", os.path.expanduser("~"))
                    if not os.path.exists(cand):
                        dangling.append({"src_line": src, "kind": "file", "name": cand,
                                         "reason": "待办声称必做但目标文件不存在"})
                for m in SCRIPT_RE.finditer(line):
                    stem = os.path.splitext(m.group(1))[0]
                    cands = (stem + ".py", stem + ".sh")
                    if any(c in tracked for c in cands) or any(c in disk for c in cands):
                        continue
                    dangling.append({"src_line": src, "kind": "script", "name": m.group(1),
                                     "reason": "必做项声明的脚本 未入库 且 磁盘不存在"})
    return dangling


# ——————————————————————————————————————————————
# ④b 跨端交接单收件人对账（2026-09-18 Qoder CN·"无人消费的记录是死数据"第 2 实例）
#   病灶：交接单只有纸面流程（status / 处置列），全库实测 0 个解析者（grep "待接单" 仅命中
#   单据自身）⇒ "等别人来接单"完全依赖人记得，违反愿景①。本项即那个缺失的消费者。
#   判据只测可机械提取的两件事：frontmatter date 龄期 + 处置格「⬜ 待接单」行数；
#   语义性回填（对方写了什么处置）不强判——宁可漏也不误报（守卫变噪音=被无视=失效）。
# ——————————————————————————————————————————————
HANDOFF_PREFIX = "跨端交接单"
HANDOFF_UNCLAIMED = "⬜ 待接单"
HANDOFF_AGE_DAYS = 7


def check_handoff_pending(todo_dir, today=None):
    """返回超龄仍未被接单的跨端交接单 [{file, age_days, unclaimed, reason}]。
    缺目录 / 缺 date / 无待接行 → []（宁漏勿误·与 scan_pending_todo 同口径）。"""
    out = []
    if not os.path.isdir(todo_dir):
        return out
    today = today or datetime.date.today()
    for root, dirnames, filenames in os.walk(todo_dir):
        dirnames.sort()
        for fn in sorted(filenames):
            if not (fn.startswith(HANDOFF_PREFIX) and fn.endswith(".md")):
                continue
            p = os.path.join(root, fn)
            try:
                text = open(p, encoding="utf-8").read()
            except Exception:
                continue
            m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
            if not m:
                continue
            try:
                d0 = datetime.date.fromisoformat(m.group(1))
            except ValueError:
                continue
            n = sum(1 for line in text.splitlines() if HANDOFF_UNCLAIMED in line)
            if n == 0:
                continue
            age = (today - d0).days
            if age < HANDOFF_AGE_DAYS:
                continue
            out.append({"file": os.path.relpath(p, todo_dir), "age_days": age, "unclaimed": n,
                        "reason": f"交接单立单 {age} 天仍有 {n} 行「{HANDOFF_UNCLAIMED}」未被接单/回填"})
    return out


# ——————————————————————————————————————————————
# ⑤ 开发工具/ ↔ scripts_manifest 对账（半边D消费者·机械自校正·2026-08-27 加）
# ——————————————————————————————————————————————
SCRIPT_CENTER_MANIFEST = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "scripts_manifest.json")
# 基础设施/构建产物目录（永不含业务脚本·剪枝用）
INFRA_EXCLUDE = {"__pycache__", "node_modules", ".git", "dist", "logs", "_drafts"}
# 全域遍历排除清单（判据⑦⑧ 共用·同源律：两个遍历共用同一份排除清单·⛔不给两判据造两个真相面）
#   记忆琥珀=备份（历史快照同号是它的职责）·归档/存档包=历史留存·真源消副本前备份=迁移留痕
_EXCL_DIRS = {"记忆琥珀", "归档", "存档包", "真源消副本前备份", "__pycache__", ".venv", "node_modules"}
# 已知第三方/子项目目录（合法不入册·与 EXTERNAL_GUARD_DIRS 同源硬编码风格）
KNOWN_SUBPROJECT_EXCLUDE = {
    "DailyHotApi", "Kami", "JsBarcode", "deepseek-harness",
    "five-layer-memory.bak_260815_1154", "video-shotcraft-absorb", "知识联邦引擎",
    "buluotuo-release-sync", "backfill-undo", "guizang-ppt-skill",
    "ian-xiaohei-illustrations", "记忆系统自动化", "未知未知研究",
    "skill-compliance-check", "skill-rehab-tests", "skill-symlink-guard",
    "skill-sync-guard", "skill-version-check", "安装包测试脚本",
    "changelog-guard", "dsh-kb-sync", "Skill路由引擎", "hooks-test",
    "l3_conclusion_guard_tests", "five-layer-memory",
}
BAK_SUFFIX = (".bak", ".bak-20260826-2112", ".bak-202608241050", ".bak-20260826-2206")


def load_manifest_scripts(manifest_path):
    """返回 (reg_rel, excluded_norm)：
    reg_rel       = scripts 数组条目的 path，归一为相对 开发工具/ 的段（如 foo/bar.py）
    excluded_norm = excluded_dir_level 的 path，归一为相对 开发工具/ 的段（如 DailyHotApi）
    用于 ⑤ 开发工具/ ↔ scripts_manifest 对账。"""
    reg_rel, excluded = set(), set()
    if not os.path.exists(manifest_path):
        return reg_rel, excluded
    d = json.load(open(manifest_path, encoding="utf-8"))
    for e in d.get("scripts", []):
        if not (isinstance(e, dict) and "path" in e):
            continue
        # 本检查仅覆盖 开发工具/ 范围（与 manifest.script_center 字段一致）；
        # 自定义层/等其他范围的条目不属本检查域·跳过（避免域外路径拼到开发工具/下误报悬空）
        p = e["path"]
        parts = p.split("/")
        if parts[:2] == [os.path.expanduser("~"), "开发工具"]:
            reg_rel.add("/".join(parts[2:]))
    for e in d.get("excluded_dir_level", []):
        if isinstance(e, dict) and "path" in e:
            excluded.add(e["path"])
    # 归一：剥 "开发工具/" 前缀
    excluded_norm = set()
    for e in excluded:
        parts = e.split("/")
        if parts[:2] == ["开发工具"]:
            excluded_norm.add("/".join(parts[2:]) if len(parts) > 2 else parts[-1])
        else:
            excluded_norm.add(e)
    return reg_rel, excluded_norm


def check_script_center(manifest_path):
    """⑤ 开发工具/ ↔ scripts_manifest 对账（半边D消费者·机械自校正）。

    返回 (orphans, dangling)：
      dangling = manifest 条目声称的脚本在磁盘不存在 → 真漂移（硬·计入 drift）
      orphans  = 开发工具/ 内真实 .py/.sh（在册范围·排除第三方/子项目/备份）但未入册
                 → 仅提示（不计入硬漂移·避免误伤合法不入册目录）

    设计哲学：scripts_manifest 的 scripts 数组 = 唯一真相条目（per-script 各平台自维护）。
    本检查让'文件系统'反向校验它——漂移即报，彻底消除'手填第二副本静默漂移'
    （原 stats 块已删·同病根·01-通用规范 line34）。"""
    reg_rel, excluded_norm = load_manifest_scripts(manifest_path)
    center = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具")
    disk = set()
    for root, dirs, files in os.walk(center):
        rel = os.path.relpath(root, center)
        top = rel.split(os.sep)[0]
        # 剪枝：排除 manifest 声明目录 + 已知第三方/子项目 + 基础设施目录
        keep = []
        for d in dirs:
            full_rel = os.path.join(rel, d) if rel != "." else d
            if full_rel in excluded_norm or d in KNOWN_SUBPROJECT_EXCLUDE or d in INFRA_EXCLUDE:
                continue
            keep.append(d)
        dirs[:] = keep
        if rel != "." and (top in KNOWN_SUBPROJECT_EXCLUDE or top in INFRA_EXCLUDE or top in excluded_norm):
            continue
        for fn in files:
            if not (fn.endswith(".py") or fn.endswith(".sh")):
                continue
            if fn.endswith(BAK_SUFFIX):
                continue
            disk.add(os.path.join(rel, fn) if rel != "." else fn)
    # dangling：在册但磁盘无（硬漂移）
    dangling = sorted(p for p in reg_rel if not os.path.exists(os.path.join(center, p)))
    # orphans：磁盘有但未在册（仅提示）
    orphans = sorted(d for d in disk if d not in reg_rel)
    return orphans, dangling


# ——————————————————————————————————————————————
# 主流程
# ——————————————————————————————————————————————
# 自测夹具（守卫编写规范 §3.0·5 自测纪律：新匹配路径必须有负例证据）
# ——————————————————————————————————————————————
def run_selftest():
    """§二 挂载声称配对夹具（2026-09-10 童灵根治轮）。

    覆盖 3 类假阳根因 + 3 类回归护栏，共 8 例：
      假阳档：T2 否定词 / T3 一格多脚本外溢 / T4 跨脚本串味
      幽灵档：T6 成员列 route-audit-hook 复合词 / T7 部署列内嵌他端路径
      护栏档：T1 正例不误伤 / T5 整组声称保全 / T8 退役删除线跳过
    """
    import tempfile
    head = "## 二、家族成员（按辖区分组）\n\n| 辖区 | 成员 | 部署 | 说明 |\n|---|---|---|---|\n"
    tail = "\n\n## 三、落地全案\n"
    mounts = {"a_guard.py", "b_tool.py", "c_guard.py", "d_guard.py",
              "position3_notify.py", "crossend_guard.py"}
    cases = [
        ("T1 单脚本 + 部署格 Stop Hook（正例·防误伤）",
         "| 域 | **a_guard.py**（v1） | **Stop Hook**（常驻） | - |",
         {("a_guard.py", "Stop")}),
        ("T2 否定护栏「不依赖 Hook 事件」（CatPaw 假阳档）",
         "| CatPaw | **a_guard.py**（v0.1）+ **b_tool.py**（v0.1） | **patrol 降级**（launchd 调度·不依赖 Hook 事件） | - |",
         set()),
        ("T3 成员格多脚本外溢（系统日志假阳档）",
         "| 系统日志 | **a_guard.py**（引擎）+ **b_tool.py**（allowlist）+ **c_guard.py**（Stop 链末位收口） | launchd 常驻 | - |",
         {("c_guard.py", "Stop")}),
        ("T4 跨脚本串味（position3 假阳档）",
         "| 岗位3 | **a_guard.py**（launchd 每日） | **调度**（launchd）+ 触达（position3_notify.py 挂 UserPromptSubmit 第5条） | - |",
         {("position3_notify.py", "UserPromptSubmit")}),
        ("T5 整组声称保全（防误伤·registry_guards 真档形态）",
         "| 登记一致性 | **a_guard.py + b_tool.py** | **Stop Hook** | - |",
         {("a_guard.py", "Stop"), ("b_tool.py", "Stop")}),
        ("T6 成员列 route-audit-hook 不误升（2026-08-27 幽灵档）",
         "| Hermes | **c_guard.py**（route-audit-hook 实挂） | **on_session_end**（插件钩子） | - |",
         set()),
        ("T7 部署列内嵌他端路径不误升（2026-09-10 幽灵档）",
         "| Qoder | **a_guard.py**（v1.1） | 首跑即抓他端产物 `hooks/crossend_guard.py` v2.0 | - |",
         set()),
        ("T8 退役删除线行跳过（reply_format_guard 档）",
         "| ~~格式契约~~ | ~~**d_guard.py**~~ **⛔ DEPRECATED** | ~~**Stop Hook**~~ | - |",
         set()),
    ]
    ok = 0
    for title, row, expect in cases:
        fd, path = tempfile.mkstemp(suffix=".md")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(head + row + tail)
            got = set(load_family_claims(path, mounts))
        finally:
            os.unlink(path)
        good = got == expect
        ok += bool(good)
        print("  %s %s" % ("✅" if good else "❌", title))
        if not good:
            print("       期望 %s" % sorted(expect))
            print("       实得 %s" % sorted(got))
    # ⑥ 件④回流纯函数三例：新缺硬红 / 存量不误伤 / 已回流零告警
    bf = [("B1 新缺→硬红", check_philosophy_backflow({"new_guard"}, "")[1] == ["new_guard"]),
          ("B2 存量→⚪不硬红", check_philosophy_backflow({"old_guard"}, "", stock={"old_guard"})[1] == []),
          ("B3 已提及→零告警", check_philosophy_backflow({"ok_guard"}, "| x | **ok_guard.py** | Stop |")[0] == []),
          ("B4 命名变体不误伤（连字符↔下划线）", check_philosophy_backflow({"audit_staleness"}, "| x | audit-staleness / amber-checkup |")[0] == [])]
    for t, g in bf:
        ok += bool(g)
        print("  %s %s" % ("✅" if g else "❌", t))
    # ④b 交接单收件人五例：正例能红 + 四条不误伤（守卫变噪音=被无视=失效）
    TODAY = datetime.date(2026, 9, 18)
    def _mkdoc(name, body):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(body)
        return d
    hp_dirs = {
        "stale": _mkdoc("跨端交接单-A.md", "---\ndate: 2026-09-10\n---\n| T1 | ⬜ 待接单 |\n| T2 | ⬜ 待接单 |\n"),
        "fresh": _mkdoc("跨端交接单-B.md", "---\ndate: 2026-09-18\n---\n| T1 | ⬜ 待接单 |\n"),
        "done": _mkdoc("跨端交接单-C.md", "---\ndate: 2026-09-01\n---\n| T1 | ✅ 已回填 |\n"),
        "nodate": _mkdoc("跨端交接单-D.md", "---\ntitle: 无日期\n---\n| T1 | ⬜ 待接单 |\n"),
        "other": _mkdoc("普通待办.md", "---\ndate: 2026-09-01\n---\n| T1 | ⬜ 待接单 |\n"),
    }
    _stale = check_handoff_pending(hp_dirs["stale"], TODAY)
    hp = [
        ("H1 超龄 8 天 + 2 行待接 → 报（正例·能红）",
         len(_stale) == 1 and _stale[0]["age_days"] == 8 and _stale[0]["unclaimed"] == 2),
        ("H2 当天立单 → 不报（防新单即红）", check_handoff_pending(hp_dirs["fresh"], TODAY) == []),
        ("H3 超龄但处置列已回填 → 不报（接单即消）", check_handoff_pending(hp_dirs["done"], TODAY) == []),
        ("H4 超龄但缺 date 字段 → 不报（宁漏勿误）", check_handoff_pending(hp_dirs["nodate"], TODAY) == []),
        ("H5 非交接单命名的 ⬜ 待接单 → 不误伤", check_handoff_pending(hp_dirs["other"], TODAY) == []),
    ]
    for t, g in hp:
        ok += bool(g)
        print("  %s %s" % ("✅" if g else "❌", t))
    import shutil
    for _d in hp_dirs.values():
        shutil.rmtree(_d, ignore_errors=True)
    # —— ⑦ 撞号判据夹具（2026-10-07 v1.1 扩面·字母后缀段号；v1.2 扩面·CHANGELOG 版本号）——
    import tempfile as _tf, shutil as _sh
    with _tf.TemporaryDirectory() as _td:
        _mb = os.path.join(_td, "记忆蓝图"); os.makedirs(_mb)
        # C 形态夹具（版本号撞号）——与 A/B 同文件共存，验三形态互不干扰
        open(os.path.join(_mb, "dup_seed_clog.md"), "w", encoding="utf-8").write(
            "- **v1.3.126（2026-10-11·Hermes·甲）**：条目甲\n"
            "- **v1.3.126（2026-10-11·Hermes·乙）**：条目乙（同裸号·真撞号·必红）\n"
            "- **v1.3.125-H（2026-10-10·Hermes·丙）**：带后缀\n"
            "- **v1.3.126-H（2026-10-11·Hermes·丁）**：带后缀（与裸号并存·L53 正解·必绿）\n"
            "- **v1.3.127-H（2026-10-11·Hermes·戊）**：同后缀重复（真撞号·必红·供 C4）\n"
            "- **v1.3.127-H（2026-10-11·Hermes·己）**：同后缀重复（真撞号·必红·供 C4）\n"
            "- **v1.3.128-Q（2026-10-11·Hermes·庚）**：另一端的独立后缀·只此一次（必绿·供 C3）\n"
            "- **v1.14.9·C6熔断器修复（P1）**：同版本多子条目甲（必绿·供 C7）\n"
            "- **v1.14.9·YAML触发词修正（命名修正）**：同版本多子条目乙（必绿·供 C7）\n"
            "- **v0.1.3 做法（收敛后的正解）**：空格+子标题甲（必绿·供 C8）\n"
            "- **v0.1.3 新增第三道（疑问词裸奔）**：空格+子标题乙（必绿·供 C8）\n"
            "- **v2.0.1（2026-10-11·Qoder CN·条目壬）**：完整条目甲（真撞号·必红·供 C9）\n"
            "- **v2.0.1（2026-10-11·WorkBuddy·条目癸）**：完整条目乙（真撞号·必红·供 C9）\n"
            "本文提及 v1.3.999 但不构成条目（非 bullet·必绿）\n")
        open(os.path.join(_mb, "dup_seed.md"), "w", encoding="utf-8").write(
            "#### 3.4·扩F 甲律（正例锚）\n正文\n#### §3.4·扩F 乙律（同号病灶）\n"
            "## 条文 7 丙\n## 条文 7 丁\n## 条文 28\n## 条文 28·附 合法派生\n"
            "#### 3.5·扩F 戊（父节不同·合法）\n#### 3.4·扩 己（无字母后缀·不判）\n")
        _hits = {os.path.basename(fp): d for fp, d in check_article_duplication(_td)}
        _d = _hits.get("dup_seed.md", {})
        _c = _hits.get("dup_seed_clog.md", {})
        ad = [
            ("A1 同文件两个 3.4·扩F → 报红（本次真病灶形态）",
             "3.4·扩F" in _d and _d.get("3.4·扩F") == 2),
            ("A2 同文件两个 条文 7 → 仍报红（A形态回归护栏）",
             "条文 7" in _d),
            ("A3 3.5·扩F 与 3.4·扩F 并存 → 各自独立不互撞（防假红）",
             "3.5·扩F" not in _d),
            ("A4 条文28 + 条文28·附 派生号 → 不判撞（防假红·既有annex规则对⑦B同步生效域）",
             "条文 28" not in _d),
            # ── C 形态（2026-10-11 v1.2 扩面·Hermes 撞号案）──
            ("C1 同裸号 v1.3.126 出现两次 → 报红（本次真病灶形态）",
             _c.get("版本 v1.3.126") == 2),
            ("C2 裸号 v1.3.126 与带后缀 v1.3.126-H 并存 → 不判撞（L53「后加者让号加后缀」正解·防假红）",
             "版本 v1.3.126-H" not in _c),
            ("C3 不同端后缀 v1.3.128-Q 只出现一次 → 不判撞（后缀≠免撞金牌·但单独出现本就不该撞）",
             "版本 v1.3.128-Q" not in _c),
            ("C4 同后缀 v1.3.127-H 出现两次 → 仍报红（后缀不是免撞金牌）",
             _c.get("版本 v1.3.127-H") == 2),
            ("C5 非 bullet 行里的版本号字面量 → 不判撞（只认条目行·防假红）",
             not any(str(k).startswith("版本 v1.3.999") for k in _c)),
            ("C6 A/B/C 三形态同目录并存 → 互不干扰（A 形态结论不因 C 加入而变）",
             _d.get("3.4·扩F") == 2 and _d.get("条文 7") == 2),
            # ── v1.3 扩面（同版本多子条目豁免·2026-10-11 全域扫描实证 4 处假红后补）──
            ("C7 `v1.14.9·C6熔断器` 与 `v1.14.9·YAML修正` → 不判撞（同版本多子条目·正常记账·防假红）",
             "版本 v1.14.9" not in _c),
            ("C8 `v0.1.3 做法` 与 `v0.1.3 新增第三道` → 不判撞（空格+子标题·同族形态）",
             "版本 v0.1.3" not in _c),
            ("C9 两条各自完整的 `v2.0.1（端·条目）` → 仍报红（⛔ 豁免不收纵到放过真撞号）",
             _c.get("版本 v2.0.1") == 2),
        ]
        _sh.rmtree(_mb, ignore_errors=True)
    # —— ⑧ 官方源引用符号在位性夹具（2026-10-11 v1.2.253·Hermes 行号漂移案）——
    #   双向：真符号在位→绿｜假符号（编的名）→红｜他端口径词/否定语境→豁免不红
    with _tf.TemporaryDirectory() as _td8:
        _repo = os.path.join(_td8, "repo"); os.makedirs(_repo)
        _off = os.path.join(_td8, "hermes-agent", "hermes_cli"); os.makedirs(_off)
        _ag = os.path.join(_td8, "hermes-agent", "agent"); os.makedirs(_ag)
        open(os.path.join(_off, "plugins.py"), "w", encoding="utf-8").write(
            "VALID_HOOKS = {'pre_llm_call'}\n\ndef invoke_hook(hook_name):\n    return []\n")
        open(os.path.join(_ag, "turn_context.py"), "w", encoding="utf-8").write(
            "from agent.title_generator import start_title_upgrade\n")
        open(os.path.join(_repo, "ref_seed.md"), "w", encoding="utf-8").write(
            "见 `hermes_cli/plugins.py` 的 `invoke_hook()` 派发钩子（真符号·必绿）\n"
            "`VALID_HOOKS` 是内核合法集（真符号·必绿）\n"
            "调 `turn_context.py` 的 `start_title_upgrade`（真符号·必绿）\n"
            "`hermes_cli/plugins.py` 的 `totally_fake_symbol_xyz` 不在源里（假符号·紧邻官方 .py·必红·判据有牙）\n"
            "他端 `UserPromptSubmit`/`Stop` 事件对照（他端口径词·豁免不红）\n"
            "共用件要 `transcript_path`·而 Hermes 没有该字段（否定语境·豁免不红）\n")
        _save_dir, _save_core = _OFFICIAL_SRC_DIR, dict(_OFFICIAL_CORE)
        try:
            globals()["_OFFICIAL_SRC_DIR"] = os.path.join(_td8, "hermes-agent")
            globals()["_OFFICIAL_CORE"] = {"plugins.py": "hermes_cli/plugins.py", "turn_context.py": "agent/turn_context.py"}
            _od = check_official_ref_integrity(_repo)
        finally:
            globals()["_OFFICIAL_SRC_DIR"], globals()["_OFFICIAL_CORE"] = _save_dir, _save_core
        _bad = {(b, sy) for _fp, b, sy, _ln in _od}
        dd = [
            ("D1 真符号 `invoke_hook` 在位 → 不报（防假绿·判据有效性）", ("plugins.py", "invoke_hook") not in _bad),
            ("D2 假符号 `totally_fake_symbol_xyz` 编造 → 报红（真病灶形态·判据有牙）", ("plugins.py", "totally_fake_symbol_xyz") in _bad),
            ("D3 他端口径词 `UserPromptSubmit`/`Stop` → 豁免不报（跨端对照词非官方符号·防假红）", ("plugins.py", "UserPromptSubmit") not in _bad and ("plugins.py", "Stop") not in _bad),
            ("D4 否定语境 `transcript_path`（没有该字段） → 豁免不报（论证缺失·符号查无是论点·防假红）", ("turn_context.py", "transcript_path") not in _bad),
        ]
        for t, g in dd:
            ok += bool(g)
            print("  %s %s" % ("✅" if g else "❌", t))
    for t, g in ad:
        ok += bool(g)
        print("  %s %s" % ("✅" if g else "❌", t))
    total = len(cases) + len(bf) + len(hp) + len(ad) + len(dd)
    print("自测 %d/%d %s" % (ok, total, "全绿" if ok == total else "有红"))
    return 0 if ok == total else 1


# ——————————————————————————————————————————————


def check_article_duplication(repo_root):
    """⑦ 标识号唯一性（2026-10-07 条文45撞号案·多端并发立法防再同号）。

    判据（三形态·同一文件内标题多现即撞号）：
    A. `^## 条文 (N)` 数字条文号（2026-10-07 初版·条文45撞号案）。
    B. 子节号字母后缀 `^#+ §?X.Y·扩Z`（v1.1 扩面·2026-10-07 守卫编写规范
       「§3.4·扩F」两节并发立法案——原判据只认 A 形态，字母后缀段号在盲区）。
       父节号不同（3.4·扩F vs 3.5·扩F）=合法·不判撞。
    C. 🔴 CHANGELOG bullet 版本号 `^- **vX.Y.Z(-端后缀)?（` （v1.2 扩面·2026-10-11
       Hermes 撞号案）——病形同 A/B（多端共写同一本账·无原子发号），但载体是
       **变更记录 bullet 而非标题** ⇒ A/B 两形态的正则全不匹配 ⇒ **恒静默全绿**。
       实盘实证（扩判据前）：记忆蓝图下 **5 处存量撞号**全部漏判
       （脚本哲学 01 的 v1.3.130/127/115/109 四处 + 安装包哲学 CHANGELOG 的 v1.3.115 一处），
       而判据⑦当时正打印「✅ 无条文撞号」——**判据盲区 = 静默全绿**，比没判据更危险。
       ⚠️ 合法豁免：版本号**带端后缀**（`v1.3.126-H` vs `v1.3.126`）是 CHANGELOG L53
       「后加者让号·加区分后缀」纪律的**正解形态** ⇒ 视为不同号·不判撞。
       ⛔ 但**同后缀重复**（`v1.3.126-H` 出现两次）仍是撞号·照判。
    范围=repo_root 全域 .md（v1.3 扩面·2026-10-11；原为 `记忆蓝图/` 单目录 ⇒ 同族账本
       散在他处恒静默全绿·实测 218 条/35 文件中仅 117 条/11 文件在记忆蓝图内）。
       **逐文件独立判**（⛔ 不是「全域同号」）⇒ 跨副本/投影同号天然不红（不同文件）。
       排除：隐藏目录/`记忆琥珀`（备份）/`归档`+`存档包`（历史留存）/缓存类。
    """
    import glob, collections
    head = re.compile(r"^## 条文 (\d+)(.*)$")
    annex = re.compile(r"^\s*[·・\-—]?\s*附")   # 附条（条文28附 / 条文33附）=合法派生号·不算撞号
    subhead = re.compile(r"^#{2,6}\s*§?\s*(\d+(?:\.\d+)*)\s*·?\s*扩([A-Z])(?![A-Za-z])")
    # C 形态：bullet 版本号（捕获版本串·含可选端后缀）
    clogver = re.compile(r"^- \*\*(v\d+\.\d+\.\d+(?:-[A-Za-z]+)?)")
    # ⚠️ 同版本多子条目豁免（v1.3 扩面实证·2026-10-11）：
    #   判据⑦ C 形态首跑逮到 4 处**假红**——`- **v1.14.9·C6熔断器…**` 与
    #   `- **v1.14.9·YAML触发词…**` 同一版本号下记**多条改动**（一个版本含多项变更
    #   是正常记账·不是撞号）。撞号病的定义是「**两个独立条目**声称同一版本号」，
    #   而这里是「**同一版本号的多个子段**」。
    #   ✅DO 判据：版本号后紧跟 `·` 或全角间隔号 + 子标题 ⇒ 视为**同条多段**·不计入撞号。
    #      （`- **v0.1.3 做法（收敛后的正解）**` 这类版本号后接空格+子标题的也属同类）
    #   ⛔ DO NOT 放宽成「同号一律不判」——那会把**真撞号**（两条各自完整的版本条目
    #      用同一号）也放过 = 判据自毁。区分点：**有无子标题后缀**。
    _subtail = re.compile(r"^(v\d+\.\d+\.\d+(?:-[A-Za-z]+)?)\s*(?:[·・]|\s)")
    # ── 扫描域（v1.3 扩面·2026-10-11 全域）────────────────────────────────
    # 原 glob 前缀 `记忆蓝图/` ⇒ 同族账本散在他处时**恒静默全绿**（判据盲区同族病）。
    # 实测分布（扩域前）：记忆蓝图 117 条/11 文件、技能配置 48/8、发布库 42/10、
    #   自定义层 4/3、脚本中心 3/1、开发工具 3/1、工作日志 1/1 —— 共 218 条 / 35 文件。
    # ⇒ 扩到 repo_root 全域，**逐文件独立判**（判据语义=「同文件内标识号重复」，
    #   ⛔ 不是「全域同号」）⇒ 跨副本/投影同号天然不红（不同文件·已实证 18 份 CHANGELOG
    #   跨副本共同版本号 = 0·唯一共同 1 个的 v4.16 双份也在不同文件）⇒ 扩域不引入假红。
    # ⚠️ 排除项：`.git`/隐藏目录（版本库与工具缓存）/`记忆琥珀`（**备份**·历史快照同号是它的职责）/
    #   `归档`+`存档包`（历史留存·同 A/B 两形态的一贯豁免域）/`__pycache__`/`.venv`（缓存）。
    #   ⚠️ A/B 两形态（条文号/扩字母段号）随之扩域——三者同属「设计规范族标识格式」，
    #     分离扫描域 = 给同一判据造两个真相面（⛔ 双本账）。
    #   `_EXCL_DIRS` 已提为全局常量（L585·与判据⑧ 共用·同源律）。
    hits = []
    for dp, dns, fns in os.walk(repo_root):
        dns[:] = [d for d in dns if d not in _EXCL_DIRS and not d.startswith(".")]
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            fp = os.path.join(dp, fn)
            try:
                lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            nums = []
            for ln in lines:
                mm = head.match(ln)
                if mm and not annex.match(mm.group(2)):
                    nums.append("条文 " + mm.group(1))
                    continue
                ms = subhead.match(ln)
                if ms:
                    nums.append("%s·扩%s" % (ms.group(1), ms.group(2)))
                    continue
                # C 形态：CHANGELOG bullet 版本号（⚠️ 带端后缀与裸号视为不同号·见 docstring）
                mv = clogver.match(ln)
                if mv:
                    # 同版本多子条目豁免：`v1.14.9·C6熔断器` / `v1.14.9·YAML修正`
                    # = 一个版本号下记多条改动（正常记账）⇒ 不计入撞号分母。
                    # ⚠️ 判据只看「版本号后是否紧跟子标题分隔符」·⛔ 不放开到「同号一律不判」
                    #    （那会放过真撞号：两条各自完整的版本条目用同一号）。
                    if not _subtail.match(ln.lstrip("- *").strip()):
                        nums.append("版本 " + mv.group(1))
            if not nums:
                continue
            dups = {k: v for k, v in collections.Counter(nums).items() if v > 1}
            if dups:
                hits.append((os.path.relpath(fp, repo_root), dups))
    return hits


# —— ⑧ 官方源引用完整性（2026-10-11·Hermes 端「生搬硬套/行号漂移」案·宪法铁律#6 的机械承接器）——
# 病根：宪法 T0 铁律#6 只要求「改机制前先回源」，没规定**引用形态**。手抄行号（`xxx.py:行号`）
# 零机械校验 ⇒ 官方 hermes-agent 一升级即全漂（实测 21 处引用漂 4 处·invoke_hook 漂 191 行）。
# 判据形态：文档里凡**官方核心文件**引用，查其引用的**符号名**是否在官方全局符号集内；
#   非官方文件（我们包内的 runtime_paths/path_utils/技能自带的 scan/shared 等）⇒ 静默跳过。
# ⛔ 本判据不判「行号对不对」——行号随版本必漂、判它必假红风暴；判的是「**符号名是否在位**」（跨版本稳定）。
# ⚠️ 官方源=**白名单**（basename 唯一≠官方源·首版 204 处假红根因就是误收包内同名文件）。
#    一行可引多文件 ⇒ 符号查**全局官方符号集**（union of all 白名单文件的符号）·⛔ 不按命名文件单查。
# 官方核心白名单（Hermes 端·宪法铁律#6 常引的那几个）：
_OFFICIAL_SRC_DIR = os.path.join(os.path.expanduser("~"), ".hermes", "hermes-agent")
_OFFICIAL_CORE = {
    "plugins.py": "hermes_cli/plugins.py",
    "plugins_dispatch.py": "hermes_cli/plugins_dispatch.py",
    "turn_context.py": "agent/turn_context.py",
    "turn_finalizer.py": "agent/turn_finalizer.py",
    "title_generator.py": "agent/title_generator.py",
    "config_defaults.py": "hermes_cli/config_defaults.py",
    "memory_tool_store.py": "tools/memory_tool_store.py",
}
# 他端口径词豁免集：这些是**被对照的他端事件名/字段名**（UserPromptSubmit/Stop/PreToolUse…）
#   ⛔ 不是 Hermes 官方符号——文档拿它们做跨端对照表时必然反引号包裹·判据不该验它们在官方源在不在
#   （病名=判据把「叙述对象」当「官方符号」·他端事件名在 Hermes 源里查无是**应该的**）
_HETEROGENOUS_TERMS = {
    "UserPromptSubmit", "Stop", "PreToolUse", "SessionStart", "PostToolUse",
    "provides_hooks", "SessionEnd", "SubagentStop",
}
# 引用形态：`官方源文件.py`（反引号可选）·后可选 `:行号` 或 `:行号-行号`
_OFFICIAL_REF_RE = re.compile(r'`?([A-Za-z_][\w\-]*\.py)`?(?:[：:](\d+)(?:-(\d+))?)?')
# 符号名提取：**只认反引号包裹的标识符**（`符号名`）——这是文档里标「这是官方符号」的约定形态
#   ⛔ 不认紧跟()/= 的散落词——首版 2320 + 次版 116 处假红全来自把 Stop/position/title/from
#   等文档叙述词当符号验（病名=判据⑤「提取正则太宽」·收窄到反引号唯一形态才干净）
_SYMBOL_TOKEN_RE = re.compile(r'`([A-Za-z_][A-Za-z0-9_]{3,})`')
_STOPWORDS = {'py', 'md', 'the', 'and', 'for', 'doc', 'note', 'from', 'import', 'True', 'False', 'None', 'json'}
# 否定语境豁免：文档写「输入要 transcript_path·而 Hermes **没有**该字段」= 在**论证缺失**
#   ⇒ transcript_path 不在源里是**论点本身**（事实正确）·⛔ 判据不把否定式引用当符号漂移
#   （病名=判据不分「肯定引用」vs「否定引用」·否定语境里符号查无是应该的）
_NEGATION_CONTEXT_RE = re.compile(r'没有|不传|缺少|无该字段|查无|不存在|无此字段|不持有|未持有|而非|而不是')


def check_official_ref_integrity(repo_root):
    """⑧ 官方源引用符号在位性。返回 [(docpath, filename, symbol, lineno)] · 符号不在位=漂移。

    白名单制：只验 6 个官方核心文件（_OFFICIAL_CORE）·非官方同名文件不验（basename 唯一≠官方源）。
    符号查全局官方符号集（union）·⛔ 不按命名文件单查（一行可引多文件）。
    """
    # 建全局官方符号集（union of 白名单文件的所有 def/常量/集合元素）
    official_symbols = set()
    for base, rel in _OFFICIAL_CORE.items():
        fp = os.path.join(_OFFICIAL_SRC_DIR, rel)
        if not os.path.exists(fp):
            continue
        try:
            text = open(fp, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for m in re.finditer(r'^\s*def ([A-Za-z_]\w*)\(', text, re.M):
            official_symbols.add(m.group(1))
        for m in re.finditer(r'^([A-Z_][A-Z0-9_]*)\s*[:=]', text, re.M):
            official_symbols.add(m.group(1))
        # kwargs 参数名（hook 派发形态 `assistant_response=...` / 函数签名内的关键字参数）
        for m in re.finditer(r'\b([a-z_]\w*)\s*=\s*\w', text):
            official_symbols.add(m.group(1))
        for m in re.finditer(r'"([A-Za-z_]\w{3,})"', text):
            official_symbols.add(m.group(1))
    drift = []
    for dp, dns, fns in os.walk(repo_root):
        dns[:] = [d for d in dns if d not in _EXCL_DIRS and not d.startswith(".")]
        for fn in fns:
            if not fn.endswith('.md'):
                continue
            fp = os.path.join(dp, fn)
            try:
                doc_lines = open(fp, encoding='utf-8', errors='replace').read().split('\n')
            except Exception:
                continue
            for i, line in enumerate(doc_lines):
                # 逐 .py 引用处理：只验**紧邻该 .py** 的反引号符号（同片段）
                #   ⛔ 一行可引多文件——把整行所有反引号符号算给同行的 .py = 符号归属错（假红）
                #   例：`turn_context.py:245` 的 `start_title_upgrade` 紧邻算它的；
                #       同行 `title_source` 是 hermes_state_titles.py 的·不归 turn_context。
                for m in _OFFICIAL_REF_RE.finditer(line):
                    base = m.group(1)
                    if base not in _OFFICIAL_CORE:
                        continue  # 非官方核心文件 ⇒ 短路跳过·⛔不硬拉
                    # 紧邻窗口：.py 引用位置前后各 60 字符（覆盖 `xxx.py:行号` 的 `符号名` 形态）
                    lo = max(0, m.start() - 60)
                    hi = min(len(line), m.end() + 60)
                    window = line[lo:hi]
                    # 提取窗口内反引号符号（去停用词 + 去他端口径词）
                    toks = set()
                    for gm in _SYMBOL_TOKEN_RE.finditer(window):
                        grp = gm.group(1)
                        if grp and grp not in _STOPWORDS and grp not in _HETEROGENOUS_TERMS:
                            toks.add(grp)
                    for tok in toks:
                        # 符号在位判：查全局官方符号集（union）·⛔ 不按命名文件单查
                        if tok in official_symbols:
                            continue
                        # 否定语境豁免：窗口内若含否定词（没有/不传/查无…）= 文档在论证「该符号缺失」
                        #   ⇒ 查无是论点本身·不判漂移
                        if _NEGATION_CONTEXT_RE.search(window):
                            continue
                        drift.append((os.path.relpath(fp, repo_root), base, tok, i + 1))
    return drift


def main():
    ap = argparse.ArgumentParser(description="守卫 文档声称 vs 守卫全宇宙实挂 一致性巡检")
    ap.add_argument("--settings", default=DEFAULT_SETTINGS)
    ap.add_argument("--docs", nargs="*", default=DEFAULT_DOCS)
    ap.add_argument("--reverse", action="store_true", help="额外做反向完整性检查")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--backflow-seed", action="store_true",
                    help="打印当前缺失名单（一次性标定 BACKFLOW_STOCK 用）")
    ap.add_argument("--script-center", action="store_true",
                    help="额外做 开发工具/ ↔ scripts_manifest.json 对账（半边D消费者·机械自校正）")
    ap.add_argument("--self-test", action="store_true", dest="self_test",
                    help="跑配对/回流/交接单夹具（例数由运行输出，⛔不写死在文案）")
    args = ap.parse_args()

    if args.self_test:
        print("=== guard_doc_consistency.py 自测夹具（§二 配对） ===")
        return run_selftest()

    if args.backflow_seed:
        reg = load_registry(next((d for d in args.docs if os.path.basename(d) == "守卫编写规范.md"), None))
        fam = next((d for d in args.docs if os.path.basename(d) == "守卫家族实例.md"), None)
        txt = open(fam, encoding="utf-8", errors="replace").read() if fam and os.path.exists(fam) else ""
        miss, _n, _st = check_philosophy_backflow(reg, txt)
        print("BACKFLOW 缺失 %d / 注册表在册 %d" % (len(miss), len(reg)))
        for m_ in miss:
            print("  " + m_)
        return 0

    if not os.path.exists(args.settings):
        print(f"[ERR] settings 不存在: {args.settings}", file=sys.stderr)
        return 2

    actual = load_actual(args.settings)
    # 聚合「全宇宙」实挂真相源：9 宿主配置 + git pre-commit Hook + registry_guards 目录发现
    # （2026-08-24 根治：原仅 WorkBuddy settings.json → 跨宿主/pre-commit 守卫误报 phantom）
    # （2026-08-24 补：registry_guards 自动发现通道——doenglingz_guard 类目录守卫不出现在 JSON 配置）
    mounted_all = load_all_host_mounted() | load_git_precommit_mounted() | load_registry_guards_mounted()
    family_doc = next((d for d in args.docs if os.path.basename(d) == "守卫家族实例.md"), None)
    spec_doc = next((d for d in args.docs if os.path.basename(d) == "守卫编写规范.md"), None)

    claims = load_family_claims(family_doc, mounted_all) if family_doc else []
    registry = load_registry(spec_doc) if spec_doc else set()

    # —— 正向：文档声称挂载但全宇宙均未实挂 → 虚报（硬漂移）——
    phantom = []
    for script, event in claims:
        if script not in mounted_all:
            phantom.append((script, event))

    # —— 反向：注册表成员且实挂但 §二 未声称 → 遗漏（可选）——
    missing_doc = []
    if args.reverse:
        claimed_scripts = {s for s, _ in claims}
        for script in actual:
            stem = os.path.splitext(script)[0]
            if stem in registry and script not in claimed_scripts:
                missing_doc.append(script)

    # —— 三件套（§3.0 ①入库）：注册表脚本必须"守卫全宇宙已落地" ——
    repo_root = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
    orphans, ghosts = check_registry_resolved(registry)

    # —— ④ 查悬空（§3.3 反哺落地）：待完成/交接文档"必做"项 ↔ 落地痕迹 ——
    tracked, disk = scan_guard_universe()
    todo_dir = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "自定义层", "待完成工作")
    dangling = scan_pending_todo(todo_dir, repo_root, tracked, disk)

    # —— ④b 跨端交接单收件人（立单必有机械消费者·2026-09-18）——
    handoff = check_handoff_pending(todo_dir)

    # —— ⑤ 开发工具/ ↔ scripts_manifest 对账（半边D消费者·机械自校正）——
    sc_orphans, sc_dangling = ([], []) if not args.script_center else check_script_center(SCRIPT_CENTER_MANIFEST)

    # —— ⑥ 件④哲学回流（§四在册 ↔ 家族实例提及·新缺=硬红·存量=⚪显形）——
    fam_text = ""
    if family_doc and os.path.exists(family_doc):
        fam_text = open(family_doc, encoding="utf-8", errors="replace").read()
    bf_missing, bf_new, bf_stock = check_philosophy_backflow(registry, fam_text)

    drift = bool(phantom) or bool(orphans) or bool(dangling) or bool(sc_dangling)
    drift = drift or bool(bf_new) or bool(handoff)

    # —— ⑦ 条文号唯一性（2026-10-07·条文45撞号案·并发立法防再同号）——
    art_dups = check_article_duplication(repo_root)
    drift = drift or bool(art_dups)

    # —— ⑧ 官方源引用符号在位性（2026-10-11·宪法铁律#6 机械承接器·行号漂移案）——
    off_drift = check_official_ref_integrity(repo_root)
    drift = drift or bool(off_drift)

    if args.json:
        print(json.dumps({
            "actual_mounts": {k: sorted(v) for k, v in sorted(actual.items())},
            "doc_claims": [list(c) for c in claims],
            "phantom_claims": [list(p) for p in phantom],
            "missing_doc_registered_mounted": sorted(missing_doc),
            "orphan_scripts_untracked": orphans,
            "ghost_scripts_not_found": ghosts,
            "dangling_pending": dangling,
            "handoff_pending": handoff,
            "script_center_orphans": sc_orphans,
            "script_center_dangling": sc_dangling,
            "backflow_missing": bf_missing,
            "backflow_new_debts": bf_new,
            "backflow_stock_debts": bf_stock,
            "article_number_collisions": [[f, d] for f, d in art_dups],
            "official_ref_symbol_drift": off_drift,
            "drift": drift,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"实挂守卫（SSOT · settings.json）: {len(actual)} 个")
        for k in sorted(actual):
            print(f"  ✅ {k}  ←  {', '.join(sorted(actual[k]))}")
        print()
        if phantom:
            print(f"❌ 文档虚报挂载（声称已挂但实际未挂）: {len(phantom)} 个")
            for s, e in phantom:
                print(f"   - {s} @ {e}  （§二 声称，settings.json 无）")
        else:
            print("✅ 无文档虚报（§二 声称的挂载均已在 settings.json 落地）")
        if args.reverse:
            print()
            if missing_doc:
                print(f"⚠️ 实挂但 §二 未登记挂载状态（文档遗漏）: {len(missing_doc)} 个")
                for s in sorted(missing_doc):
                    print(f"   - {s}")
            else:
                print("✅ 无文档遗漏（实挂守卫均已在 §二 登记）")
        print()
        if bf_new:
            print(f"❌ 件④哲学回流缺口（§四在册但家族实例全文未提及·新账·§3.0 件④）: {len(bf_new)} 个")
            for s_ in bf_new:
                print(f"   - {s_}  （补 02-脚本家族实例/守卫家族实例.md §二 对应辖区行后消除）")
        elif bf_missing:
            print(f"⚪ 件④哲学回流：新缺 0 · 存量 {len(bf_missing)}（名单见 BACKFLOW_STOCK·只显形不硬红）")
        else:
            print("✅ 件④哲学回流：§四在册脚本在家族实例均有提及")
        print()
        if orphans:
            print(f"❌ 孤儿脚本（仓库内脚本根存在·但 ~/个人AI档案 仓库未跟踪·§3.0 ①未入库）: {len(orphans)} 个")
            for s in orphans:
                print(f"   - {s}.py/.sh/.ps1  （git add + commit 后消除）")
        else:
            print("✅ 注册表脚本全部已落地（仓库跟踪 + 跨宿主目录 + 记忆琥珀·§3.0 ①过）")
        if ghosts:
            print(f"⚠️ 全宇宙守卫目录均未找到（真缺失·硬漂移·仅提示）: {len(ghosts)} 个")
            for s in ghosts:
                print(f"   - {s}")
        print()
        if dangling:
            print(f"❌ 悬空承诺（待完成/交接文档「必做」项无落地痕迹·§3.3 查悬空）: {len(dangling)} 项")
            for d in dangling[:30]:
                print(f"   - {d['src_line']}  [{d['kind']}] {d['name']}  （{d['reason']}）")
            if len(dangling) > 30:
                print(f"   … 其余 {len(dangling)-30} 项")
        else:
            print("✅ 无悬空承诺（待完成/交接文档「必做」项均有落地痕迹）")
        print()
        if handoff:
            print(f"❌ 跨端交接单超龄未接单（≥{HANDOFF_AGE_DAYS} 天仍有「{HANDOFF_UNCLAIMED}」行·立单必有收件人）: {len(handoff)} 份")
            for h in handoff[:10]:
                print(f"   - {h['file']}  {h['reason']}  （接单方回填处置列＋更新 status 后消除；确不支持则改判 ⛔ 并写明理由）")
        else:
            print("✅ 无超龄未接单的跨端交接单")
        if args.script_center:
            print()
            if sc_dangling:
                print(f"❌ scripts_manifest 悬空条目（声称存在·但磁盘无·硬漂移）: {len(sc_dangling)} 个")
                for p in sc_dangling[:30]:
                    print(f"   - {p}")
            else:
                print("✅ scripts_manifest 无悬空条目（全部声称脚本均存在于磁盘）")
            if sc_orphans:
                print(f"⚠️ 开发工具/ 在册范围未入册脚本（提示·非硬漂移）: {len(sc_orphans)} 个")
                for p in sc_orphans[:30]:
                    print(f"   - {p}")
                if len(sc_orphans) > 30:
                    print(f"   … 其余 {len(sc_orphans)-30} 个")
            else:
                print("✅ 开发工具/ 在册范围无未入册脚本（库存与 manifest 一致）")
        print()
        if art_dups:
            print(f"❌ 标识号撞号（同文件「## 条文 N」/「§X.Y·扩Z」/「^- **vX.Y.Z」多现·⑦·并发同号病）: {len(art_dups)} 个文件")
            for fp, d in art_dups:
                print(f"   - {fp}  {d}")
                # C 形态（CHANGELOG 版本号）单独给处置口径——⛔ 不套用条文让号那套
                _ver_dups = {k: v for k, v in d.items() if str(k).startswith("版本 ")}
                if _ver_dups:
                    print(f"     ↳ CHANGELOG 版本号撞号处置：按该文件多端共写纪律「后加者让号·加区分后缀」")
                    print(f"        （如 v1.3.126 → v1.3.126-H；H=端名首字母）。带后缀与裸号=不同号·同后缀重复仍算撞。")
                else:
                    print(f"     ↳ 条文/段号撞号处置：按让号先例归位（外部机械落点引用密度低者让号·历史文字冻结）")
        else:
            print("✅ 无标识号撞号（记忆蓝图/ 全部 .md 的条文号/扩字母段号/CHANGELOG 版本号均唯一）")
        print()
        if off_drift:
            print(f"❌ 官方源引用符号漂移（文档引用的符号名不在 live 官方源·宪法铁律#6·行号随版本必漂·符号名跨版本稳定）: {len(off_drift)} 处")
            for fp, base, sym, ln in off_drift[:40]:
                print(f"   - {fp}:{ln} → {base} 的 `{sym}` 不在源里（改符号名为 live 实际名·或该功能已下线则删引用）")
            if len(off_drift) > 40:
                print(f"   … 其余 {len(off_drift)-40} 处")
        else:
            print("✅ 官方源引用符号全部在位（文档引用的 Hermes 官方符号名与 live 源一致）")
        print()
        print("结论:", "发现硬漂移，需修正文档或机制" if drift else "一致，无漂移 ✅")

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
