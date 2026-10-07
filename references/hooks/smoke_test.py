#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""smoke_test.py — 布洛陀安装包结构完整性检查（Phase X-PKG 第4检查项）
================================================================
检测：必含文件/目录存在性、Steps完整、9 Skill 结构、Templates 关键文件、
      占位符残留、空文件、version.md 格式合法。
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
        if prev_ver in content:
            issues.append(f"旧版本号 {prev_ver} 残留: {fp.relative_to(pkg)}")

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


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_version_selftest())
    main()
