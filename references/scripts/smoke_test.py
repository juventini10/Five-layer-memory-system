#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_test.py — 布洛陀安装包结构完整性检查（Phase X-PKG 第4检查项）
================================================================
检测：必含文件/目录存在性、Steps完整、9 Skill 结构、Templates 关键文件、
      占位符残留、空文件、version.md 格式合法、组件账实对账（P1-P6·2026-10-08）。
退出码：0=通过  1=有缺陷  2=参数错误
"""
import os
import re
import sys
from pathlib import Path

# Windows 控制台 UTF-8 守卫：cp1252 代码页下 print emoji/中文 会 UnicodeEncodeError
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


DEFAULT_PKG = Path.home() / "记忆共享中心/发布库/五层记忆系统/布洛陀-全平台安装包"

# ── 必含文件/目录清单 ──
REQUIRED_TOP = [
    "INSTALL.md", "version.md", "CHANGELOG.md", "README.md",
    "rollback.sh", "rollback.ps1", "conffiles",
    "references/steps", "references/skills", "references/templates",
    "references/成就系统", "references/最伟大的我",
    "references/未知未知", "references/记忆琥珀",
]

REQUIRED_STEPS = [
    "step1-identity-check.md", "step2-basic-identity.md",
    "step3-path-setup.md", "step4-questionnaire.md",
    "step5-file-synthesis.md", "step6-skill-install.md",
    "step6-hook-install.md", "step6.5-amber-install.md",
    "step7-verification.md",
]

REQUIRED_SKILLS = [
    "awaken-memory-system", "clock-loop", "daily-buddy",
    "growth-box", "meta-aletheia", "sucair",
    "shall-we-talk", "system-logger", "triwich",
]

REQUIRED_TEMPLATES = [
    "IDENTITY.md", "MEMORY.md", "SHADOW.md", "SOUL.md", "USER.md",
    "情境层-动态状态快照.md", "用户基本规则-摘要版.md", "用户基本规则-铁律版.md",
]

# 占位符（在 path_utils.py 和 step3 中合法，其他地方残留=安装时替换失败风险提示）
PLACEHOLDERS = [os.path.expanduser("~"), "[日记仓库]", "[日记子目录]"]
PLACEHOLDER_ALLOWED_FILES = {"path_utils.py", "step3-path-setup.md", "step6-skill-install.md", "step7-verification.md"}

# ── 版本轴（2026-10-01 同源根治）────────────────────────────────────────
# 真源 = 包根 version.md；其余全是「宣称位」，必须读得到同一个号。
# 口径：号由功能增量决定（《版本命名规范》§2），发布状态不由号决定——状态只住
#       CHANGELOG 顶段头 `[未发布]`，发版那一刻 relabel 为 `[X.Y.Z]`（§4.1）。
# ⛔ 不收 integrity-fingerprints.json 的 version 字段作判据：它是生成器
#   （release_contamination_check.py）自述的工具版本标签，非用户宣称位，
#   纳入比对＝把工具内部字段当产品账（域错置·同 2026-09-17 童灵域隔离教训同源）。
_VERSION_PURE_RX = re.compile(r"\d+\.\d+(?:\.\d+)?")
_UNRELEASED_MARKS = {"未发布", "unreleased"}

# 宣称位（存在性检查·正判据）：path → (正则模板, 该位置为什么必须带号)
# {v} 由真源版本串填充；短形式（major.minor）同时容忍，见 _carrier_rx()。
VERSION_CARRIERS = [
    ("INSTALL.md", r"^# .{0,12}布洛陀\s*{v}", "安装入口标题（用户/AI 第一眼看到的号）"),
    ("INSTALL.md", r"布洛陀\s*{v} 安装检测", "Step1 检测输出模板（每次安装都会在对话里出现）"),
    ("rollback.sh", r"布洛陀\s*{v}", "回滚脚本头与运行横幅（用户执行回滚时看到）"),
    ("rollback.ps1", r"布洛陀\s*{v}", "回滚脚本 Windows 版头"),
    ("references/steps/step7-verification.md", r"布洛陀\s*{v}", "装机验证报告的『记忆系统名称』行"),
    ("references/component-versions.json", r'"package_version":\s*"{v}"', "组件版本单一真源文件"),
]


def _read(p: Path) -> str:
    """读文本（utf-8 容错·.ps1 BOM 不干扰正则）。"""
    try:
        return p.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError):
        return p.read_text(encoding="utf-8", errors="replace")


def _read_version(pkg: Path):
    """取 version.md 真源原始串（含后缀也照原样返回，交格式检查判红）。"""
    vf = pkg / "version.md"
    if not vf.exists():
        return None
    m = re.search(r'^version:\s*["\']?([^"\'\s#]+)["\']?\s*$',
                  _read(vf), re.MULTILINE)
    return m.group(1) if m else None


def _carrier_rx(v: str) -> str:
    """把 {v} 填成"完整号 或 其 major.minor 短形式"。

    容忍短形式的理由：README/标题类文案按 §1 可写 `布洛陀 2.0`（X.Y 即功能级号），
    强求逐位相等会把合法写法判成红（假红）；而 `2.1` 对真源 `2.0.0` 仍判不匹配，
    漂移抓得住——短形式取真源前两段，不取"任意前缀"。
    """
    esc = re.escape(v)
    parts = v.split(".")
    short = "%s.%s" % (parts[0], parts[1]) if len(parts) > 2 else ""
    alt = esc if not short or short == v else "%s|%s" % (esc, re.escape(short))
    return alt



def check_required_files(pkg: Path) -> list:
    """检查必含文件/目录。"""
    issues = []
    for item in REQUIRED_TOP:
        if not (pkg / item).exists():
            issues.append(f"缺失顶层: {item}")
    for step in REQUIRED_STEPS:
        if not (pkg / "references/steps" / step).exists():
            issues.append(f"缺失步骤: steps/{step}")
    for skill in REQUIRED_SKILLS:
        skill_dir = pkg / "references/skills" / skill
        if not skill_dir.exists():
            issues.append(f"缺失Skill目录: skills/{skill}/")
        elif not (skill_dir / "SKILL.md").exists():
            issues.append(f"Skill缺SKILL.md: skills/{skill}/SKILL.md")
    for tmpl in REQUIRED_TEMPLATES:
        if not (pkg / "references/templates" / tmpl).exists():
            issues.append(f"缺失模板: templates/{tmpl}")
    return issues


def check_empty_files(pkg: Path) -> list:
    """检测0字节文件（排除 __pycache__/.git/.DS_Store）。"""
    issues = []
    for f in pkg.rglob("*"):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or ".git" in f.parts or f.name == ".DS_Store":
            continue
        if f.name.endswith(".bak"):
            continue
        if f.stat().st_size == 0:
            issues.append(f"空文件(0字节): {f.relative_to(pkg)}")
    return issues


def check_version_format(pkg: Path) -> list:
    """version.md 版本串必须为纯数字 X.Y 或 X.Y.Z（《版本命名规范》§1）。

    2026-10-01 改判据（你裁定"不存在发布前/发布后两个版本状态"）：
    原实现只查"有没有 x.y"，`2.0.0-dev` 照样通过 ⇒ 状态后缀混进真源无人拦，
    一处后缀实测连带 5 处宣称位红＋归档名污染。现改为显式拒绝任何后缀形态。
    发布状态的正确住处＝CHANGELOG 顶段头 `[未发布]`（§4.1），不在版本串里。
    """
    issues = []
    vf = pkg / "version.md"
    if not vf.exists():
        return ["version.md 不存在"]
    text = _read(vf)
    m = re.search(r'^version:\s*["\']?([^"\'\s#]+)["\']?\s*$', text, re.MULTILINE)
    if not m:
        return ["version.md 缺少合法 version: 字段（需 x.y 或 x.y.z）"]
    raw = m.group(1)
    if not _VERSION_PURE_RX.fullmatch(raw):
        issues.append(
            "version.md 版本串非纯数字：%s ——《版本命名规范》§1 禁一切后缀（-dev/-rc/-beta/+…）。"
            "发布状态只住 CHANGELOG 顶段头（§4.1：未发布→发版时 relabel），"
            "写进版本串＝同一版本出现两种宣称串（INSTALL/rollback 抄的是不带后缀的号）"
            % raw)
    return issues




def _same_ver(a: str, b: str) -> bool:
    """同一个号的两种合法写法：完整号 X.Y.Z 与其 major.minor 短形式 X.Y。"""
    if a == b:
        return True
    return b.count(".") == 1 and a.startswith(b + ".")


def _old_ver_hits(suffix, text, prev):
    """旧号命中行（注记豁免版·2026-10-08 B 类修正·负例实证）。

    实证反例：归档段 [2.0.0] 建立后全包 17 处命中全部为开发注记/
    工具自述版本/测试夹具/事故引用（v2.0.0 修订注、__version__、
    "version": "2.0.0"、V2.0.0-dev.zip 案例、夹具字符串），零处包
    版本宣称位。本腿语义=抓「非注记语境」旧号残留。
    """
    lines = text.splitlines()
    note_lines = set()
    if suffix == ".py":
        try:
            import io as _io
            import tokenize
            for tok in tokenize.generate_tokens(_io.StringIO(text).readline):
                if tok.type in (tokenize.COMMENT, tokenize.STRING):
                    note_lines.update(range(tok.start[0], tok.end[0] + 1))
        except Exception:
            pass
    hits = []
    for i, ln in enumerate(lines, 1):
        if prev not in ln:
            continue
        st = ln.strip()
        if st.startswith(("#", "//", "<!--")):
            continue
        if "-dev" in ln:  # 事故档名引用形态（V2.0.0-dev.zip）·历史案例
            continue
        # 列粒度豁免（2026-10-18 Loop轮·你批「能根治就处理」·根治 Agent B⑤行粒度挂账）：
        #   逐处定位 prev，仅豁免"§紧邻其前"的那一处；同句其余命中照常记红。
        if not [pp for pp in (mm0.start() for mm0 in re.finditer(re.escape(prev), ln))
                if not re.search(r"§\s*$", ln[:pp])]:
            continue
        if re.match(r'^\s*"(version|__version__)"\s*:', ln):  # 工具自述版本字段
            continue
        if i in note_lines:
            continue
        hits.append(i)
    return hits


def check_version_consistency(pkg: Path) -> list:
    """版本号同源检查：真源=version.md，核 ①CHANGELOG 顶段头 ②各宣称位 ③旧号残留。

    2026-10-01 同源根治（你裁定"不存在发布前一个号、发布后另一个号"）：
      旧版此处查的是"状态后缀有没有同步抄到 INSTALL 首行"——等于默认允许版本串带状态，
      于是"定版去后缀"与"INSTALL 也加后缀"两条路都算修好，互斥红只能靠人临场解释。
      现判据：版本串必须纯数字（形态红由 check_version_format 出），本函数只做**同源比对**：
      每个宣称位都必须读得到真源那个号；发布状态只许出现在 CHANGELOG 顶段头 `[未发布]`。
    """
    issues = []
    raw = _read_version(pkg)
    if raw is None:
        return ["version.md 不存在或取不到 version: 字段——真源缺失时本项无从比对，"
                "须先补真源（⛔不以其余载体的号当结论）"]
    if not _VERSION_PURE_RX.fullmatch(raw):
        # 真源形态非法 ⇒ 宣称位比对无意义，显式声明跳过（静默返回空＝假绿·判据缺一半）
        return ["version.md 真源版本串非纯数字（%s），宣称位比对已跳过——先修形态再谈同源" % raw]
    v = raw

    # ① CHANGELOG 顶段头：状态词合法（§4.1），已定号则必须等于真源
    cl = pkg / "CHANGELOG.md"
    if cl.exists():
        m = re.search(r"^##\s*\[([^\]]+)\]", _read(cl), re.MULTILINE)
        if not m:
            issues.append("CHANGELOG.md 无可识别顶段头 `## [未发布]` 或 `## [X.Y.Z]`——"
                          "升级检测与三标记比对都从这里取号，缺段头＝这两项检查失明")
        else:
            top = m.group(1).strip()
            if top.lower() in _UNRELEASED_MARKS:
                pass  # 未发布态：状态住段头，号以 version.md 为准
            elif not _VERSION_PURE_RX.fullmatch(top):
                issues.append("CHANGELOG 顶段头既不是状态词、也不是纯版本号：[%s]（"
                              "发布状态写进段头以外的位置＝两处版本串各说各话的老病）" % top)
            elif not _same_ver(v, top):
                issues.append("版本真源与 CHANGELOG 顶段头漂移：version.md=%s 而顶段头=[%s]"
                              % (v, top))

    # ② 宣称位存在性比对（正判据：读不到真源的号＝红）
    alt = _carrier_rx(v)
    present = 0
    for rel, tpl, why in VERSION_CARRIERS:
        f = pkg / rel
        if not f.exists():
            issues.append("宣称位载体不存在：%s（应含 %s 的%s）——该处号无从核对，"
                          "不是通过而是不测" % (rel, v, why))
            continue
        present += 1
        # ⚠️ 替换值必须包非捕获组：alt 内含 `|`（完整号|短形式），裸插会把整个
        #    模板切成两条备选式（`布洛陀\s*2\.0\.0|2\.0 安装检测`）——实测后果＝
        #    前半段无锚点裸匹配，模板行缺失也不报红（K4 假绿·2026-10-01 自测逮出）。
        if not re.search(tpl.replace("{v}", "(?:%s)" % alt), _read(f)):
            issues.append("宣称位≠真源：%s 读不到 %s（该处=%s）" % (rel, v, why))
    if present == 0:
        issues.append("宣称位清单零覆盖（%d 个载体一个都不存在）＝本项假绿，须核对包结构"
                      % len(VERSION_CARRIERS))

    # 搜全包除 CHANGELOG 外的旧版本残留
    # 取上一个版本：搜 CHANGELOG 里第一个 ≠ 真源的 [x.y.z] 条目（本包「版本传承」节
    # 只写表格不建 `## [1.x]` 段头，正是为了让这条腿继续只认"已发版的历史段"）
    changelog = pkg / "CHANGELOG.md"
    old_vers = []
    if changelog.exists():
        for line in _read(changelog).splitlines():
            vm = re.match(r'^## \[(\d+\.\d+(?:\.\d+)?)\]', line)
            if vm and not _same_ver(vm.group(1), v):
                old_vers.append(vm.group(1))
                if len(old_vers) >= 1:
                    break  # 只取最近一个旧版本

    if not old_vers:
        return issues  # 🔴 2026-10-01 修正：原 `return []` 会把此行之前已攒的 issues 整个丢弃
                       #   ——「没有旧版本可比较」只该跳过残留搜索，不该宣布全项通过。
                       #   实锤：当时"发布态互斥"判据在此被吞，smoke 对真包报 0 缺陷，
                       #   合成包（有 CHANGELOG 旧版本）却正常开火。族＝门禁三态之
                       #   "假绿·结论被提前丢弃"（现由同源的宣称位腿承担同等火力）。

    prev_ver = old_vers[0]
    # 搜全包文件中是否残留旧版本号
    text_ext = {".md", ".py", ".sh", ".ps1", ".json"}
    for fp in pkg.rglob("*"):
        if not fp.is_file() or fp.suffix.lower() not in text_ext:
            continue
        if "__pycache__" in fp.parts or fp.name.endswith(".bak"):
            continue
        if fp.name == "CHANGELOG.md":
            continue  # CHANGELOG 里保留旧版本历史是正确的
        # 2026-09-17 童灵根治·域隔离：包版本号只应出现在「包自身元信息域」
        # （包根 + references/steps/ + references/scripts/）。以下目录属独立版本域或历史域，
        # 与包版本无关联 —— 子串搜索跨域必假阳性（实证：1.5.2 同时是 shall-we-talk 的版本号，
        # 被判成"包版本残留"×6；与 铁律-020「改匹配先 dry-run」同源）
        _rel = str(fp.relative_to(pkg)).replace("\\", "/")
        if _rel.startswith(("references/skills/", "references/templates/",
                            "references/成就系统/", "references/最伟大的我/",
                            "references/未知未知/", "references/记忆琥珀/",
                            "references/digital-twin/")):
            continue  # Skill/模板/成就/台账/数字分身 各有独立版本序列；历史区保留旧版本是事实
            # 2026-09-21 补 digital-twin：实证假阳性×1（该域 1.7.1 系「立项书v1.7.1」文档名，非包版本残留）
        # 包自检工具自身：注释里必然引用旧版本号做说明（非内容残留）——同 pkg_cleanliness_check 豁免律
        # 2026-09-21 补 sync_guard.py：同族包自检工具（实证假阳性×2——注释标"2026-09-20 v1.7.1"
        #   + T2 测试夹具标注，均为说明性引用非内容残留，与本条既有豁免律同源）
        if fp.name in {"smoke_test.py", "pkg_cleanliness_check.py", "platform_compat.py",
                       "sync_guard.py"}:
            continue
        try:
            content = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        _hit = _old_ver_hits(fp.suffix.lower(), content, prev_ver)
        if _hit:
            issues.append("旧版本号 %s 残留: %s（行 %s）"
                          % (prev_ver, fp.relative_to(pkg),
                             ",".join(str(x) for x in _hit[:5])))

    return issues

def check_placeholder_residual(pkg: Path) -> list:
    """检测占位符残留（合法文件除外）。"""
    issues = []
    refs = pkg / "references"
    if not refs.exists():
        return issues
    text_ext = {".md", ".py", ".sh", ".ps1", ".json", ".yaml", ".yml", ".txt"}
    for f in refs.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in text_ext:
            continue
        if f.name in PLACEHOLDER_ALLOWED_FILES:
            continue
        if "__pycache__" in f.parts or f.name.endswith(".bak"):
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for ph in PLACEHOLDERS:
            if ph in content:
                # step/install 文档中出现占位符是正常的（模板说明）
                rel = str(f.relative_to(pkg))
                if "step" in rel or "INSTALL" in rel:
                    continue
                issues.append(f"占位符残留 '{ph}': {f.relative_to(pkg)}")
                break
    return issues


# ── 组件账实对账 · P1-P6（2026-10-08 新增·皮叔令「提炼进 loop 安装包规则」）──
# 病根：全包「账实一致」零判据——component-versions 版本登记失准 5/10、
#   devtools 登记 13 实盘 258、CHANGELOG 缺 [2.0.0] 段、铁律版 desc/正文矛盾、
#   端数四口径并存、单数路径引用复发面——全部逃过既有腿（既有四查只测
#   存在性/同源性，不测「账=实」）。本组把账实一致机械化成 6 条判据：
#   P1 组件版本对账 / P2 件数对账 / P3 规则四件自洽 / P4 CHANGELOG 结构 /
#   P5 端名册一致 / P6 单数路径防复发。
# 承重纪律与版本轴自测同款：正例必绿、负例必红、变异必翻转（--self-test）。

_PATH_EXT = {".md", ".py", ".sh", ".ps1", ".json", ".yaml", ".yml", ".txt"}


def _skip_scan(p):
    """扫描跳过口径：缓存/备份/点前缀噪音（计数与路径扫描共用）。"""
    return ("__pycache__" in p.parts or ".git" in p.parts
            or p.name == ".DS_Store" or p.name.endswith(".bak"))


def _norm_ver(s):
    """版本串归一：去 v 前缀与空白（对账唯一口径）。"""
    return s.strip().lstrip("vV")


def _count_files(d):
    """件数口径（与 component-versions 登记对账共用）：递归计数·跳缓存/备份。"""
    if not d.exists():
        return -1
    n = 0
    for f in d.rglob("*"):
        if f.is_file() and not _skip_scan(f):
            n += 1
    return n


def _load_cv(pkg):
    """读 component-versions.json（None=不存在；dict 含 _parse_error=坏）。"""
    import json as _json
    f = pkg / "references/component-versions.json"
    if not f.exists():
        return None
    try:
        return _json.loads(_read(f))
    except ValueError as e:
        return {"_parse_error": str(e)}


def check_component_ledger(pkg: Path) -> list:
    """P1+P2 组件账实对账：component-versions.json 登记 ↔ 实盘（双向）。"""
    issues = []
    cv = _load_cv(pkg)
    if cv is None:
        return ["component-versions.json 不存在（账实对账整体失明）"]
    if "_parse_error" in cv:
        return ["component-versions.json 解析失败：%s" % cv["_parse_error"]]
    comp = cv.get("components") or {}

    # P1-a skills：双向（登记→实盘 + 实盘→登记）
    reg = comp.get("skills") or {}
    disk = {}
    sk_dir = pkg / "references/skills"
    if sk_dir.is_dir():
        for sd in sorted(sk_dir.iterdir()):
            sm = sd / "SKILL.md"
            if sm.is_file():
                m = re.search(r"^version:\s*[\"']?([^\"'\s#]+)", _read(sm), re.M)
                disk[sd.name] = m.group(1) if m else "?"
    for name in sorted(reg):
        if name not in disk:
            issues.append("[账实] 登记但实盘无：skill %s" % name)
        elif _norm_ver(reg[name]) != _norm_ver(disk[name]):
            issues.append("[账实] Skill 版本失准：%s 登记=%s 实盘=%s"
                          % (name, reg[name], disk[name]))
    for name in sorted(disk):
        if name not in reg:
            issues.append("[账实] 实盘有但登记缺：skill %s（须双向全登记）" % name)

    # P1-b system_rules：登记 ↔ 铁律版正文版本行
    sr = comp.get("system_rules")
    tl = pkg / "references/templates/用户基本规则-铁律版.md"
    if sr and tl.exists():
        m = re.search(r"^>\s*版本：v?(\S+)", _read(tl), re.M)
        if not m:
            issues.append("[账实] 铁律版读不到「> 版本：vX」行，system_rules 无从对账")
        elif _norm_ver(sr) != _norm_ver(m.group(1)):
            issues.append("[账实] system_rules 失准：登记=%s 铁律版正文=v%s"
                          % (sr, m.group(1)))

    # P2-a digital_twin 件数
    dt = comp.get("digital_twin") or {}
    for k in sorted((dt.get("files") or {})):
        rn = dt["files"][k]
        actual = _count_files(pkg / "references/digital-twin" / k)
        if actual < 0:
            issues.append("[账实] digital_twin.%s 已登记=%s 但实盘目录不存在" % (k, rn))
        elif int(rn) != actual:
            issues.append("[账实] digital_twin.%s 件数失准：登记=%s 实盘=%s" % (k, rn, actual))

    # P2-b script_system：口径=脚本中心三源并集（install_scripts.deploy_script_center）
    ss = comp.get("script_system") or {}
    if ss.get("files") is not None:
        union = set()
        for d in ("references/scripts", "references/hooks",
                  "references/digital-twin/devtools"):
            dd = pkg / d
            if dd.is_dir():
                for f in dd.iterdir():
                    if f.is_file() and not _skip_scan(f):
                        union.add(f.name)
        if int(ss["files"]) != len(union):
            issues.append("[账实] script_system.files 失准：登记=%s 实盘并集=%s"
                          % (ss["files"], len(union)))

    # P2-c 安装入口展示模板数字（INSTALL Step -0.6 模板须与 component-versions 同步）
    inst = pkg / "INSTALL.md"
    if inst.exists():
        it = _read(inst)
        m = re.search(r"系统 v(\S+) · Skill (\d+) 个 · 脚本 (\d+) 文件", it)
        if m:
            sr_ = comp.get("system_rules")
            n_sk = len(comp.get("skills") or {})
            n_sc = (comp.get("script_system") or {}).get("files")
            if sr_ and _norm_ver(m.group(1)) != _norm_ver(sr_):
                issues.append("[账实] INSTALL 模板系统号=%s ≠ 登记=%s"
                              % (m.group(1), sr_))
            if n_sk and int(m.group(2)) != n_sk:
                issues.append("[账实] INSTALL 模板 Skill 数=%s ≠ 登记=%d"
                              % (m.group(2), n_sk))
            if n_sc and int(m.group(3)) != int(n_sc):
                issues.append("[账实] INSTALL 模板脚本数=%s ≠ 登记=%s"
                              % (m.group(3), n_sc))
        m2 = re.search(r"▸ triwich：缺失 → v(\S+)", it)
        tri = (comp.get("skills") or {}).get("triwich")
        if m2 and tri and _norm_ver("v" + m2.group(1)) != _norm_ver(tri):
            issues.append("[账实] INSTALL 模板 triwich 示例=%s ≠ 登记=%s"
                          % (m2.group(1), tri))
    return issues


def check_rules_consistency(pkg: Path) -> list:
    """P3 规则四件自洽：desc/正文/摘要/详解同版本 + 031 段位 + 索引表齐全。"""
    issues = []
    tpl = pkg / "references/templates"
    vers = {}
    for label, fn in (("铁律版", "用户基本规则-铁律版.md"),
                      ("摘要版", "用户基本规则-摘要版.md"),
                      ("详解版", "用户基本规则-详解存档版.md")):
        f = tpl / fn
        if not f.exists():
            issues.append("[规则自洽] %s 缺失" % fn)
            continue
        m = re.search(r"^>\s*版本：v?(\S+)", _read(f), re.M)
        vers[label] = m.group(1) if m else None
        if not m:
            issues.append("[规则自洽] %s 读不到「> 版本：vX」行" % fn)
    vals = set(v for v in vers.values() if v)
    if len(vals) > 1:
        issues.append("[规则自洽] 三层版本号不同号：%s（铁律版头部声明三层须同升）"
                      % " / ".join("%s=v%s" % (k, v) for k, v in sorted(vers.items())))
    tl = tpl / "用户基本规则-铁律版.md"
    if tl.exists():
        txt = _read(tl)
        md = re.search(r"^description:\s*\"[^\"]*?（v(\d+\.\d+)", txt, re.M)
        if md and vers.get("铁律版") and _norm_ver(md.group(1)) != _norm_ver(vers["铁律版"]):
            issues.append("[规则自洽] 铁律版 description=v%s ≠ 正文=v%s"
                          % (md.group(1), vers["铁律版"]))
        if "### 铁律-031" in txt:
            above = txt[:txt.find("### 铁律-031")]
            h2 = ""
            for line in reversed(above.splitlines()):
                if line.startswith("## "):
                    h2 = line
                    break
            if h2 and "执行铁律" not in h2:
                issues.append("[规则自洽] 铁律-031 段位异常：挂「%s」下（应在「AI执行铁律」段）"
                              % h2.strip("# ⚡").strip()[:40])
            if "| 031 |" not in txt:
                issues.append("[规则自洽] 铁律-031 未入加载时机索引表")
        n_idx = len(re.findall(r"^\|\s*\d{3}\s*\|", txt, re.M))
        n_rules = len(re.findall(r"^### 铁律-\d{3}", txt, re.M))
        if n_idx and n_rules and n_idx != n_rules:
            issues.append("[规则自洽] 索引表行(%d)≠条数(%d)（索引漏行或多余）"
                          % (n_idx, n_rules))
        for line in txt.splitlines():
            if line.startswith("## "):
                phr = re.findall(r"（([^（）]{4,40})）", line)
                if any(phr.count(x) >= 2 for x in set(phr)):
                    issues.append("[规则自洽] 段头重复文案：%s" % line.strip()[:64])
    return issues


def check_changelog_structure(pkg: Path) -> list:
    """P4 CHANGELOG 结构：段头格式合法 + 无裸段 + 顶段==真源 + 有历史段头。"""
    issues = []
    f = pkg / "CHANGELOG.md"
    if not f.exists():
        return ["[CHANGELOG] CHANGELOG.md 不存在"]
    ver_sections = []
    for i, line in enumerate(_read(f).splitlines(), 1):
        if not line.startswith("## "):
            continue
        title = line[3:].strip()
        if title.startswith("["):
            m = re.match(r"^\[([^\]]+)\]", title)
            tag = m.group(1) if m else ""
            if re.fullmatch(r"\d+\.\d+(\.\d+)?", tag):
                ver_sections.append(tag)
            elif tag.lower() not in _UNRELEASED_MARKS:
                issues.append("[CHANGELOG] 段头格式异常 L%d：%s" % (i, line.strip()[:64]))
        elif "版本传承" in title:
            continue
        else:
            issues.append("[CHANGELOG] 裸段头（无版本号）：L%d %s" % (i, line.strip()[:64]))
    v = _read_version(pkg)
    if ver_sections and v and not _same_ver(v, ver_sections[0]):
        issues.append("[CHANGELOG] 顶段头=[%s] ≠ version.md=%s" % (ver_sections[0], v))
    if v and len(ver_sections) < 2:
        issues.append("[CHANGELOG] 仅 1 个版本段头（历史段缺失）——旧号残留腿将失去比较基准"
                      "（互锁失明），非首版本须有归档段")
    return issues


def check_platform_roster(pkg: Path) -> list:
    """P5 端名册四源一致：README/INSTALL 数字 == platform_support true 计数。"""
    issues = []
    cv = _load_cv(pkg)
    if cv is None or "_parse_error" in cv:
        return ["[端名册] component-versions.json 不可用，对账失明"]
    ps = cv.get("platform_support") or {}
    n_true = sum(1 for x in ps.values() if x is True)
    readme, install = pkg / "README.md", pkg / "INSTALL.md"
    if readme.exists():
        m = re.search(r"适配 \*\*(\d+) 端\*\*", _read(readme))
        if not m:
            issues.append("[端名册] README 读不到「适配 **N 端**」口径行")
        elif int(m.group(1)) != n_true:
            issues.append("[端名册] README=适配 %s 端 ≠ platform_support true 数=%d"
                          % (m.group(1), n_true))
    if install.exists():
        it = _read(install)
        for rx, label in ((r"（(\d+) 端一包", "INSTALL 标题"),
                          (r"合并 (\d+) 端适配层", "INSTALL 段头文案"),
                          (r"把 (\d+) 端合进一个包", "INSTALL 导航文案"),
                          (r"列上表 (\d+) 端选单", "INSTALL 平台判定")):
            for got in re.findall(rx, it):
                if int(got) != n_true:
                    issues.append("[端名册] %s=「%s 端」≠ true 数=%d" % (label, got, n_true))
        for got in re.findall(r"其余 (\d+) 端", it):
            if int(got) != max(n_true - 1, 0):
                issues.append("[端名册] INSTALL「其余 %s 端」≠ true 数-1=%d" % (got, n_true - 1))
        # 未适配标注：notes 标「未适配」的端须在 INSTALL 有对应标注
        # （防「清单 true 但用户无感」·2026-10-08 实证）
        ends = (cv.get("platform_support_notes") or {}).get("ends") or {}
        n_unfit = sum(1 for v in ends.values() if "未适配" in str(v.get("status", "")))
        if n_unfit > 0:
            _cnt = it.count("未适配完毕")
            if _cnt < n_unfit:
                issues.append("[端名册] 「未适配完毕」标注不足：notes 有 %d 端标未适配，INSTALL 仅 %d 处"
                              % (n_unfit, _cnt))
    return issues


def check_reference_paths(pkg: Path) -> list:
    """P6 单数 reference 斜杠路径形态 0 残留（防 2026-09 单复数混用复发）。

    frontmatter `type: reference` 字段值是 Diataxis 术语非路径，天然不命中
    （无斜杠）。本函数自身源码也不含该字面量（运行期拼接），自扫不误伤。
    """
    issues = []
    rx = re.compile(r"(?<![A-Za-z])reference" + "/")
    _diataxis_rx = re.compile(r"(?<![A-Za-z])reference"
                              + r"/(?:explanation|how-to|tutorial)")
    for f in pkg.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in _PATH_EXT:
            continue
        if _skip_scan(f):
            continue
        try:
            txt = _read(f)
        except Exception:
            continue
        n = len(rx.findall(txt)) - len(_diataxis_rx.findall(txt))
        if n > 0:
            issues.append("[路径] 单数 reference" + "/ 残留 ×%d：%s"
                          % (n, f.relative_to(pkg)))
    return issues


def check_legacy_upgrade_fixture(pkg: Path) -> list:
    """P8 历史形态升级夹具全跑（2026-10-09 条文54·2.1.0四缺陷行为面教训）。

    P1-P7 测账与结构；P8 测「安装器对历史文件形态的升级行为」。
    无 install_scripts.py 的包形态（加强包等）⇒ N/A 空返回（⛔不假红）；
    有安装器但缺夹具 ⇒ 红（缺件不静默）；夹具 rc!=0 ⇒ 红带输出截断。
    """
    import subprocess
    if not (pkg / "install_scripts.py").exists():
        return []
    fx = pkg / "references/scripts/test_legacy_upgrade.py"
    if not fx.is_file():
        return ["[行为夹具] 夹具缺件：references/scripts/test_legacy_upgrade.py 不在（条文54违例·⛔不静默）"]
    try:
        r = subprocess.run([sys.executable, str(fx), "--pkg-root", str(pkg)],
                           capture_output=True, text=True, timeout=180)
    except Exception as e:
        return ["[行为夹具] 夹具运行异常：%s" % e]
    if r.returncode != 0:
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-3:]
        return ["[行为夹具] 夹具未过 rc=%d：%s" % (r.returncode, " / ".join(tail))]
    return []


def check_amber_cover_guard(pkg: Path) -> list:
    """P7 琥珀覆盖保护在位：step6.5 含覆盖保护指令 + amber-watch.ps1 含版本常量。

    病根（2026-10-08）：升级/重装无条件 Copy-Item 会盖掉用户机修复版
    （实证：目录级旧版覆盖修复版 → 「每15s触发备份+日志膨胀」重现）。
    """
    issues = []
    st = pkg / "references/steps/step6.5-amber-install.md"
    if st.exists() and "覆盖保护" not in _read(st):
        issues.append("[琥珀] step6.5 缺覆盖保护指令（amber-watch.ps1 覆盖前须版本比对）")
    w = pkg / "references/记忆琥珀/scripts/amber-watch.ps1"
    if w.exists():
        wt = _read(w)
        if "AmberWatchVersion" not in wt:
            issues.append("[琥珀] amber-watch.ps1 缺 AmberWatchVersion 版本常量（覆盖保护比对锚）")
        if "amber-whitelist" not in wt:
            issues.append("[琥珀] amber-watch.ps1 缺 whitelist 文件级监听逻辑"
                          "（amber-whitelist 读取·目录全树递归=误触发病根）")
    return issues


def main():
    pkg = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PKG
    if not pkg.exists():
        print(f"ℹ️  包路径不存在，跳过结构检查：{pkg}")
        sys.exit(0)

    print(f"🔍 结构完整性检查 · {pkg.name}")
    print()

    all_issues = []
    checks = [
        ("必含文件/目录", check_required_files(pkg)),
        ("空文件检测", check_empty_files(pkg)),
        ("version.md格式", check_version_format(pkg)),
        ("版本号全链路一致", check_version_consistency(pkg)),
        ("组件账实对账", check_component_ledger(pkg)),
        ("规则文件自洽", check_rules_consistency(pkg)),
        ("CHANGELOG结构", check_changelog_structure(pkg)),
        ("端名册一致", check_platform_roster(pkg)),
        ("单数路径防复发", check_reference_paths(pkg)),
        ("琥珀覆盖保护", check_amber_cover_guard(pkg)),
        ("历史形态夹具P8", check_legacy_upgrade_fixture(pkg)),
    ]

    for name, issues in checks:
        if issues:
            print(f"  ❌ {name}: {len(issues)}项")
            for iss in issues[:10]:
                print(f"     {iss}")
            if len(issues) > 10:
                print(f"     ...及另外{len(issues)-10}项")
            all_issues.extend(issues)
        else:
            print(f"  ✅ {name}: 通过")

    print()
    if all_issues:
        print(f"❌ 结构检查未通过：{len(all_issues)} 项缺陷")
        sys.exit(1)
    else:
        print("✅ 结构完整性检查通过：0 缺陷")
        sys.exit(0)


# ── 版本轴自测（2026-10-01 新增·门禁三态自证）───────────────────────────
# 纪律：正例必绿（防判据恒红→红警疲劳）、负例必红（防恒绿假通过）、
#       变异必翻转（防"写了判据但不承重"的装饰性代码）。
# ⛔ 变异体与源逐字相同＝自测恒真，显式拒绝出结论。
_VER_FIX_KW = dict(ver="2.0.0", cl_head="未发布", claim=None, tmpl=True,
                   cv=None, carriers=True)


def _mk_ver_fixture(root, **kw):
    """造只含版本相关件的最小假包。"""
    opt = dict(_VER_FIX_KW)
    opt.update({k: v for k, v in kw.items() if v is not None or k in ("cv", "tmpl", "carriers")})
    ver = opt["ver"]
    claim = opt["claim"] or ver
    p = Path(root)
    (p / "references" / "steps").mkdir(parents=True, exist_ok=True)
    (p / "version.md").write_text('version: "%s"\n' % ver, encoding="utf-8")
    (p / "CHANGELOG.md").write_text("# 变更记录\n\n## [%s] — 2026-10-01\n\n### 新增\n- x\n"
                                    % opt["cl_head"], encoding="utf-8")
    if not opt["carriers"]:
        return p
    inst = "# 🏮 布洛陀 %s — 多平台安装入口\n" % claim
    if opt["tmpl"]:
        inst += "\n```\n🏮 布洛陀 %s 安装检测\n```\n" % claim
    (p / "INSTALL.md").write_text(inst, encoding="utf-8")
    (p / "rollback.sh").write_text("# rollback.sh — 布洛陀 %s · 回滚\n" % claim, encoding="utf-8")
    (p / "rollback.ps1").write_text("# rollback.ps1 — 布洛陀 %s · 回滚\n" % claim, encoding="utf-8")
    (p / "references" / "steps" / "step7-verification.md").write_text(
        "> 记忆系统名称：五层记忆系统 布洛陀 %s\n" % claim, encoding="utf-8")
    cv = ver if opt["cv"] is None else opt["cv"]
    (p / "references" / "component-versions.json").write_text(
        '{"package_version": "%s"}\n' % cv, encoding="utf-8")
    return p


def _ver_issues(pkg_path, load=None):
    """跑版本两条腿（格式+同源），返回 issue 文本列表。"""
    fmt_fn = (load or globals())["check_version_format"]
    con_fn = (load or globals())["check_version_consistency"]
    return fmt_fn(Path(pkg_path)) + con_fn(Path(pkg_path))


def _version_selftest() -> int:
    import tempfile
    here = Path(__file__).resolve()
    src = here.read_text(encoding="utf-8")

    def _load(mut_from=None, mut_to=None):
        code = src
        if mut_from is not None:
            n = src.count(mut_from)
            if n != 1:
                raise AssertionError("变异锚点命中 %d 次（应为 1）：%r" % (n, mut_from[:44]))
            code = src.replace(mut_from, mut_to)
            if code == src:
                raise AssertionError("变异体与源逐字相同＝自测恒真，拒绝出结论")
        ns = {"__name__": "smoke_selftest_ns", "__file__": str(here)}
        exec(compile(code, "<smoke-selftest>", "exec"), ns)
        return ns

    cases = [
        ("K1 正例：未发布态＋全宣称位同源", {}, []),
        ("K2 负例：真源带状态后缀 -dev", {"ver": "2.0.0-dev"}, ["非纯数字", "已跳过"]),
        ("K3 负例：单一宣称位撒谎", {"cv": "1.7.2"}, ["宣称位≠真源"]),
        ("K4 负例：Step1 检测模板行没带号", {"tmpl": False}, ["宣称位≠真源"]),
        ("K5 负例：顶段头已定号且≠真源", {"cl_head": "1.7.2"}, ["漂移"]),
        ("K6 正例：短形式（布洛陀 2.0）合法", {"claim": "2.0"}, []),
        ("K7 负例：宣称位载体全缺＝零覆盖", {"carriers": False}, ["零覆盖"]),
    ]
    fails = 0
    print("── 版本轴自测（宣称位＝真源）──")
    with tempfile.TemporaryDirectory() as td:
        for name, kw, expects in cases:
            sub = os.path.join(td, "case")
            if os.path.isdir(sub):
                import shutil as _sh
                _sh.rmtree(sub)
            root = _mk_ver_fixture(sub, **kw)
            got = _ver_issues(root)
            blob = " | ".join(got)
            ok = all(e in blob for e in expects) and (bool(got) == bool(expects))
            print(("  ✅ " if ok else "  ❌ ") + "%s → %s"
                  % (name, ("开火 %d 条" % len(got) if got else "无红")))
            if not ok:
                for g in got:
                    print("       ↳ %s" % g[:110])
                fails += 1
        # 变异三向（锚点必须拆成相邻字面量，否则本函数自身＝第二处命中·计数失真）
        # mode=vanish：短路后该判据消失在别处报出（证明它在承重）
        # mode=flip_red：短路后正例必须翻红（证明豁免/放行分支是承重的，不是装饰）
        muts = [
            ("M1 宣称位比对腿短路", '        if not re.search(tpl.replace("{v}", "(?:%s)" % alt), _read(' 'f)):',
             "        if False:", {"cv": "1.7.2"}, "vanish", "宣称位≠真源"),
            ("M2 零覆盖基数腿短路", "    if present == " "0:", "    if False:",
             {"carriers": False}, "vanish", "零覆盖"),
            ("M3 未发布态豁免短路", "            if top.lower() in _UNRELEASED_" "MARKS:",
             "            if False:", {}, "flip_red", "未发布"),
        ]
        print("── 变异测试（证明判据分支承重）──")
        for mname, a, b, kw, mode, key in muts:
            try:
                ns = _load(a, b)
            except AssertionError as exc:
                print("  ❌ %s — 变异锚点失效：%s" % (mname, exc))
                fails += 1
                continue
            sub = os.path.join(td, "mut")
            if os.path.isdir(sub):
                import shutil as _sh
                _sh.rmtree(sub)
            root = _mk_ver_fixture(sub, **kw)
            got = _ver_issues(root, ns)
            blob = " | ".join(got)
            if mode == "vanish":
                ok = key not in blob
                detail = "短路后「%s」应消失，实得 %s" % (key, (blob[:70] + "…") if blob else "无红")
            else:  # flip_red：正例（本应无红）短路后必须出现红
                ok = bool(got)
                detail = "短路后正例（%s）应翻红，实得 %s" % (key, (blob[:70] + "…") if blob else "无红")
            print(("  ✅ " if ok else "  ❌ ") + "%s — %s" % (mname, detail))
            if not ok:
                fails += 1
    print("\n🟢 版本轴自测全绿（用例 7＋变异 3）" if fails == 0
          else "\n🔴 版本轴自测 %d 项失败——判据有假红/假绿，勿据此发货" % fails)
    return 0 if fails == 0 else 1


# ── 账实对账自测（P1-P6 承重验证·正例必绿/负例必红/变异必翻转·2026-10-08）──
def _mk_ledger_fixture(root):
    """最小账实自洽假包（正例基线：P1-P6 全绿）。"""
    import json as _json
    p = Path(root)

    def _w(rel, txt):
        f = p / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(txt, encoding="utf-8")

    _w("version.md", 'version: "2.1.0"\n')
    _w("references/skills/alpha-skill/SKILL.md", '---\nversion: "1.0.0"\n---\n')
    _w("references/skills/beta-skill/SKILL.md", '---\nversion: "v2.0.0"\n---\n')
    _w("references/digital-twin/guards/g1.sh", "#!/bin/sh\n")
    _w("references/scripts/one.py", "x = 1\n")
    _w("references/hooks/two.py", "y = 2\n")
    _w("references/digital-twin/devtools/three.py", "z = 3\n")
    _w("references/component-versions.json", _json.dumps({
        "package_version": "2.1.0",
        "components": {
            "skills": {"alpha-skill": "1.0.0", "beta-skill": "v2.0.0"},
            "system_rules": "v8.29",
            "digital_twin": {"files": {"guards": 1}},
            "script_system": {"files": 3},
        },
        "platform_support": {"aa": True, "bb": True, "cc": False},
    }, ensure_ascii=False))
    _w("references/templates/用户基本规则-铁律版.md",
       '---\ndescription: "x（v8.29·fixture）"\n---\n\n# 铁律\n\n'
       "> 版本：v8.29 | 创建：x | 更新：x |\n>\n"
       "## 加载时机索引表\n\n"
       "| 001 | a | t | k |\n| 002 | b | t | k |\n\n"
       "## AI执行铁律（31条·009已合并入008·不可违反）\n\n"
       "### 铁律-001：a\n\n- x\n\n### 铁律-002：b\n\n- y\n\n"
       "## 执行规范（精选3条·其余下沉详解存档版）\n\n### 执规-002：c\n\n- z\n")
    _w("references/templates/用户基本规则-摘要版.md", "# x\n\n> 版本：v8.29 | 创建：x |\n")
    _w("references/templates/用户基本规则-详解存档版.md", "# x\n\n> 版本：v8.29 | 创建：x |\n")
    _w("CHANGELOG.md", "# 变更记录\n\n## [2.1.0] — 2026-10-07\n\n- x\n\n"
                       "## [2.0.0] — 2026-10-01\n\n- y\n")
    _w("README.md", "# 布洛陀\n\n> v2.1：一个包适配 **2 端**\n")
    _w("INSTALL.md", "# 布洛陀 2.1.0 — 多平台安装入口（2 端一包）\n\n"
                    "本包合并 2 端适配层。\n把 2 端合进一个包。\n"
                    "列上表 2 端选单。\n其余 1 端。\n"
                    "├─ 包内最新：系统 v8.29 · Skill 2 个 · 脚本 3 文件\n")
    _w("references/steps/step6.5-amber-install.md",
       "# 假 step6.5\n\n覆盖保护（fixture）\n")
    _w("references/记忆琥珀/scripts/amber-watch.ps1",
       '$AmberWatchVersion = "7.18.0-pkg"\n# reads amber-whitelist.txt\n')
    return p


def _mut_skill_ver(root):
    f = root / "references/skills/beta-skill/SKILL.md"
    f.write_text(f.read_text(encoding="utf-8").replace('v2.0.0', 'v9.9.9'),
                 encoding="utf-8")


def _mut_dt_count(root):
    f = root / "references/component-versions.json"
    f.write_text(f.read_text(encoding="utf-8").replace('"guards": 1', '"guards": 5'),
                 encoding="utf-8")


def _mut_desc(root):
    f = root / "references/templates/用户基本规则-铁律版.md"
    f.write_text(f.read_text(encoding="utf-8").replace('（v8.29·fixture）', '（v8.27·fixture）'),
                 encoding="utf-8")


def _mut_naked_section(root):
    f = root / "CHANGELOG.md"
    f.write_text(f.read_text(encoding="utf-8") + "\n## 裸段测试\n\n- x\n",
                 encoding="utf-8")


def _mut_roster(root):
    f = root / "README.md"
    f.write_text(f.read_text(encoding="utf-8").replace('**2 端**', '**5 端**'),
                 encoding="utf-8")


def _mut_single_ref(root):
    f = root / "references/steps/bad.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("see reference" + "/x.md\n", encoding="utf-8")


def _mut_inst_sysnum(root):
    f = root / "INSTALL.md"
    f.write_text(f.read_text(encoding="utf-8").replace("系统 v8.29", "系统 v8.20"),
                 encoding="utf-8")


def _mut_amber_tag(root):
    f = root / "references/记忆琥珀/scripts/amber-watch.ps1"
    f.write_text(f.read_text(encoding="utf-8")
                 .replace('$AmberWatchVersion = "7.18.0-pkg"', ""),
                 encoding="utf-8")


def _ledger_all(pkg_root):
    pkg_root = Path(pkg_root)
    return (check_component_ledger(pkg_root) + check_rules_consistency(pkg_root)
            + check_changelog_structure(pkg_root) + check_platform_roster(pkg_root)
            + check_reference_paths(pkg_root) + check_amber_cover_guard(pkg_root))


def _ledger_selftest() -> int:
    import tempfile
    import shutil as _sh
    here = Path(__file__).resolve()
    src = here.read_text(encoding="utf-8")

    def _load(mut_from=None, mut_to=None):
        code = src
        if mut_from is not None:
            n = src.count(mut_from)
            if n != 1:
                raise AssertionError("变异锚点命中 %d 次（应为 1）：%r" % (n, mut_from[:44]))
            code = src.replace(mut_from, mut_to)
            if code == src:
                raise AssertionError("变异体与源逐字相同＝自测恒真，拒绝出结论")
        ns = {"__name__": "smoke_ledger_selftest_ns", "__file__": str(here)}
        exec(compile(code, "<smoke-ledger-selftest>", "exec"), ns)
        return ns

    cases = [
        ("L0 正例：账实自洽假包全绿", None, None),
        ("L1 负例：Skill 版本失准", _mut_skill_ver, "Skill 版本失准"),
        ("L2 负例：件数失准", _mut_dt_count, "digital_twin.guards 件数失准"),
        ("L3 负例：desc/正文矛盾", _mut_desc, "description=v8.27"),
        ("L4 负例：CHANGELOG 裸段", _mut_naked_section, "裸段头"),
        ("L5 负例：端名册失配", _mut_roster, "README=适配 5 端"),
        ("L6 负例：单数路径残留", _mut_single_ref, "单数 reference"),
        ("L7 负例：INSTALL 模板数字漂移", _mut_inst_sysnum, "INSTALL 模板系统号"),
        ("L8 负例：琥珀版本常量缺失", _mut_amber_tag, "[琥珀] amber-watch.ps1 缺"),
    ]
    fails = 0
    print("── 账实对账自测（P1-P6）──")
    with tempfile.TemporaryDirectory() as td:
        for name, mut, expect in cases:
            sub = os.path.join(td, "case")
            if os.path.isdir(sub):
                _sh.rmtree(sub)
            root = _mk_ledger_fixture(sub)
            if mut:
                mut(root)
            got = _ledger_all(root)
            blob = " | ".join(got)
            if expect is None:
                ok = not got
                detail = "无红" if ok else blob[:120]
            else:
                ok = expect in blob
                detail = ("命中「%s」" % expect) if ok else ("未命中，实得：%s"
                                                          % (blob[:120] or "无红"))
            print(("  ✅ " if ok else "  ❌ ") + "%s → %s" % (name, detail))
            if not ok:
                fails += 1
        muts = [
            ("M1 版本比较腿短路（应证 L1 消失）",
             "elif _norm_ver(reg[name]) != _norm_ver(disk[" "name]):", "elif False:",
             _mut_skill_ver, "Skill 版本失准"),
            ("M2 裸段腿短路（应证 L4 消失）",
             'issues.append("[CHANGELOG] 裸段头（无版本号）：L%d %s" % (i, line.strip()[' ':64]))',
             'issues.append("_suppressed")',
             _mut_naked_section, "裸段头"),
        ]
        print("── 变异测试（证明判据承重）──")
        for mname, a, b, mut, key in muts:
            try:
                ns = _load(a, b)
            except AssertionError as exc:
                print("  ❌ %s — 变异锚点失效：%s" % (mname, exc))
                fails += 1
                continue
            sub = os.path.join(td, "mut")
            if os.path.isdir(sub):
                _sh.rmtree(sub)
            root = _mk_ledger_fixture(sub)
            mut(root)
            got = _ledger_all(root)
            blob = " | ".join(got)
            got_m = (ns["check_component_ledger"](Path(root))
                     + ns["check_rules_consistency"](Path(root))
                     + ns["check_changelog_structure"](Path(root))
                     + ns["check_platform_roster"](Path(root))
                     + ns["check_reference_paths"](Path(root)))
            blob_m = " | ".join(got_m)
            ok = (key not in blob_m) and (key in blob)
            print(("  ✅ " if ok else "  ❌ ") + "%s — 短路后「%s」%s"
                  % (mname, key, "消失（承重✓）" if ok else "仍在（不承重）"))
            if not ok:
                fails += 1
    print("\n🟢 账实对账自测全绿（用例 9＋变异 2）" if fails == 0
          else "\n🔴 账实对账自测 %d 项失败——判据有假红/假绿，勿据此发货" % fails)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _rc1 = _version_selftest()
        _rc2 = _ledger_selftest()
        sys.exit(max(_rc1, _rc2))
    main()
