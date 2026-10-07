#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""platform_compat.py — 布洛陀安装包跨平台兼容性检查（Phase X-PKG 第5检查项）
================================================================
检测：.sh/.ps1 双平台配对、编码(UTF-8无BOM)、换行符(\r\n残留)、
      shebang 正确、路径分隔符（反斜杠残留）、
      单平台路径假设（检查⑩·1.6）、发布者工具泄漏（检查⑪·1.6）、
      共享中心目录名硬编码（检查⑫·1.6）。
退出码：0=通过  1=有缺陷  2=参数错误
"""
import ast
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


DEFAULT_PKG = Path.home() / "记忆共享中心/发布库/五层记忆系统/布洛陀-安装包"

# 需要双平台配对的脚本（.sh 必须有对应 .ps1）
PAIRED_SCRIPTS = [
    ("rollback.sh", "rollback.ps1"),
    ("references/skills/restore-my-skills.sh", "references/skills/restore-my-skills.ps1"),
    ("references/记忆琥珀/scripts/amber_backup.sh", "references/记忆琥珀/scripts/amber-backup.ps1"),
    ("references/记忆琥珀/scripts/amber_pin.sh", "references/记忆琥珀/scripts/amber-pin.ps1"),
]


def check_paired_scripts(pkg: Path) -> list:
    """检查双平台脚本配对。"""
    issues = []
    for sh, ps1 in PAIRED_SCRIPTS:
        sh_exists = (pkg / sh).exists()
        ps1_exists = (pkg / ps1).exists()
        if sh_exists and not ps1_exists:
            issues.append(f"缺 Win 版: {sh} 有但 {ps1} 缺失")
        elif ps1_exists and not sh_exists:
            issues.append(f"缺 Mac 版: {ps1} 有但 {sh} 缺失")
        elif not sh_exists and not ps1_exists:
            issues.append(f"双平台均缺: {sh} / {ps1}")
    return issues


def check_encoding_and_lineendings(pkg: Path) -> list:
    """检测编码问题：BOM、.sh 文件的 \\r\\n 换行。"""
    issues = []
    for f in pkg.rglob("*"):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or ".git" in f.parts:
            continue
        if f.name.endswith(".bak") or f.name == ".DS_Store":
            continue

        suffix = f.suffix.lower()
        if suffix not in (".sh", ".ps1", ".py", ".md"):
            continue

        try:
            raw = f.read_bytes()
        except (PermissionError, OSError):
            continue

        rel = str(f.relative_to(pkg))

        # BOM 检测（.sh/.py 不应有 BOM；.ps1 带 BOM 是 PowerShell 推荐做法，跳过）
        if raw.startswith(b"\xef\xbb\xbf") and suffix != ".ps1":
            issues.append(f"UTF-8 BOM 残留: {rel}")

        # .sh 文件不应有 \r\n（Mac/Linux 上会报错）
        if suffix == ".sh" and b"\r\n" in raw:
            issues.append(f".sh 文件含 CRLF 换行(Mac不兼容): {rel}")

    return issues


def check_shebang(pkg: Path) -> list:
    """检查脚本 shebang 行。"""
    issues = []
    for f in pkg.rglob("*"):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or ".git" in f.parts:
            continue
        if f.name.endswith(".bak"):
            continue

        suffix = f.suffix.lower()
        if suffix not in (".sh", ".py"):
            continue

        try:
            first_line = f.read_text(encoding="utf-8").split("\n", 1)[0]
        except (UnicodeDecodeError, PermissionError):
            continue

        rel = str(f.relative_to(pkg))

        if suffix == ".sh":
            if not first_line.startswith("#!"):
                issues.append(f".sh 缺 shebang: {rel}")
            elif "bash" not in first_line and "sh" not in first_line:
                issues.append(f".sh shebang 异常({first_line[:30]}): {rel}")

        elif suffix == ".py":
            # Python 脚本建议有 shebang 但非强制（只在可执行时需要）
            pass  # 不强制

    return issues


def check_backslash_paths(pkg: Path) -> list:
    """检测 .md/.py 文件中的反斜杠路径（Windows 路径格式残留）。"""
    issues = []
    refs = pkg / "references"
    if not refs.exists():
        return issues

    # 只检测 .md 和 .py（最可能混入路径的）
    for f in refs.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".md", ".py"):
            continue
        if "__pycache__" in f.parts or f.name.endswith(".bak"):
            continue

        try:
            content = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        # 匹配 C:\Users\ 或 D:\xxx\ 等 Windows 绝对路径（排除教学示例和检测逻辑注释）
        for line_no, line in enumerate(content.splitlines(), 1):
            if re.search(r'[A-Z]:\\(?:Users|个人AI)', line):
                # 教学示例/文档表格/代码注释 = 合法引用，不报
                if any(kw in line for kw in ("违规", "⛔", "DO NOT", "示例", "只抓", "example")):
                    continue
                if line.strip().startswith("#"):
                    continue
                issues.append(f"Windows绝对路径残留: {f.relative_to(pkg)}:{line_no}")
                break

    return issues


def check_unix_path_assumption(pkg: Path) -> list:
    """检查⑩（1.6）：.md 运行时指令中硬编码 /tmp/ 具体路径且无平台声明。
    背景：awaken v7.16→v7.20 硬编码 Unix 心跳路径，Windows 无 /tmp → 全员永远误报（实际复发史）。
    豁免（任一命中即合法）：
      a) 命中行自身含平台标记（Windows/macOS/Mac/Linux/Unix/平台/⛔/示例/example）
      b) 命中行所属章节的任一级标题含平台标记（如 §10.2 macOS 故障排查）
      c) 文件内存在跨平台声明行（同行含 Windows 与 %TEMP%/$env:TEMP/平台分支/等价替换之一）
    """
    issues = []
    line_markers = ("Windows", "macOS", "Mac", "Linux", "Unix", "平台", "⛔", "示例", "example")
    heading_markers = ("Windows", "macOS", "Mac", "Linux", "Unix", "平台")
    decl_re = re.compile(r"Windows.*(%TEMP%|\$env:TEMP|\u5e73台分支|\u7b49价替换)")
    tmp_re = re.compile(r"/tmp/[A-Za-z0-9_\-{]")  # 具体路径才算，/tmp/* 泛指不算

    for f in pkg.rglob("*.md"):
        rel = str(f.relative_to(pkg))
        if "CHANGELOG" in f.name or "__pycache__" in f.parts:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue

        has_decl = any(decl_re.search(l) for l in lines)
        heading_stack = {}  # level -> text
        for i, line in enumerate(lines):
            m = re.match(r"^(#{1,6})\s+(.*)", line)
            if m:
                lvl = len(m.group(1))
                heading_stack[lvl] = m.group(2)
                for deeper in list(heading_stack):
                    if deeper > lvl:
                        del heading_stack[deeper]
                continue
            if not tmp_re.search(line):
                continue
            # 跳过表格行与反例/禁止/固化叙述行（非用户端执行指令；检查器注释明定"运行时指令"）
            if line.strip().startswith("|"):
                continue
            if any(k in line for k in ("违规", "⛔DO NOT", "禁止", "固化", "变更说明")):
                continue
            if any(k in line for k in line_markers):
                continue
            if any(any(k in h for k in heading_markers) for h in heading_stack.values()):
                continue
            if has_decl:
                continue
            issues.append(f"单平台路径假设(/tmp/无平台声明): {rel}:{i+1}")
    return issues


# 发布者专属工具（安装包不携带，用户端引用必须带降级声明）
_PUBLISHER_TOOLS = [
    "buluotuo-release-sync",
    "changelog-guard",
    "changelog_guard",
    "\u77e5\u8bc6\u8054\u90a6\u5f15\u64ce",  # 知识联邦引擎
    "knowledge_lint",
    "guard-heartbeat-mirror-sync",
]
# 合法降级标记（命中行同行或其后20行内出现即视为已声明降级）
_DEGRADE_MARKERS = ["N/A", "未安装", "发布者工具", "个人工具",
                    "熔断", "降级", "脚本缺失", "不携带", "不阻塞", "不可用"]
# 仅查运行时指令行（动作动词），纯叙述/表格行不查
_INSTR_TOKENS = ("\u2705DO", "python3", "bash ", "Read ", "\u8fd0\u884c", "\u6267\u884c", "Get-Content", "cat ")


def check_publisher_tool_leak(pkg: Path) -> list:
    """检查⑪（1.6）：用户端运行时指令引用发布者专属工具且无降级声明。
    背景：mirror-sync 守护判定无降级 → 安装包用户 100% 永远误报（第二次复发，首次为 changelog-guard）。
    范式：system-logger「N/A（个人工具·未安装）合法终态」。
    范围：references/skills/** + INSTALL.md + references/steps/**（用户端运行时文档）。
    豁免：命中行同行或其后20行内含降级标记（熔断器/降级块紧跟指令块之后，向后看而非向前）；表格行（`|`起始）为契约叙述非指令，不查。

    【已知局限·未来】本检查靠黑名单 _PUBLISHER_TOOLS 枚举工具名，默认放行=清单外的新工具漏报（新工具泄漏需有人手动补进清单才能被抓）。
    治本方向=路径特征法：判据换成“用户端运行指令出现 `/开发工具/` 子路径 + 无降级声明 → FAIL”——发布包不铺开发工具目录，锁物理事实而非工具名，不依赖枚举完全性。
    触发改造：第三次同类复发时，或下次重构 platform_compat 时一并上（需同步重校豁免：clock-loop 自身文档有大量合法 `/开发工具/` 引用，不豁免会自伤）。来源：2026-07-31 mirror-sync 误报复盘时的第一性原理讨论。
    """
    issues = []
    for f in pkg.rglob("*.md"):
        rel = str(f.relative_to(pkg))
        if "CHANGELOG" in f.name or "__pycache__" in f.parts:
            continue
        if not (rel.startswith("references/skills/") or rel == "INSTALL.md" or rel.startswith("references/steps/")):
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue
        for i, line in enumerate(lines):
            if line.lstrip().startswith("|"):
                continue  # 表格行=契约叙述非运行指令
            if not any(t in line for t in _PUBLISHER_TOOLS):
                continue
            if not any(tok in line for tok in _INSTR_TOKENS):
                continue  # 非运行指令行（叙述/表格/来源注）不查
            window = "\n".join(lines[i:min(len(lines), i + 21)])
            if any(m in window for m in _DEGRADE_MARKERS):
                continue
            tool = next(t for t in _PUBLISHER_TOOLS if t in line)
            # 跳过"X=工具"等式列举（设计规范叙述中的已有机制对应关系，非用户端执行指令）
            if "=" in line and tool in line.split("=", 1)[1]:
                continue
            issues.append(f"发布者工具无降级声明[{tool}]: {rel}:{i+1}")
    return issues


def check_author_path_undeclared(pkg: Path) -> list:
    """检查⑪-治本（v1.7·2026-09-15）：用户运行时文档引用作者侧路径 `开发工具/` 且无降级声明。

    落地「检查⑪ docstring·已知局限·治本方向=路径特征法」——判据锁**物理事实**
    （发布包不铺 `开发工具/` 目录），不依赖 `_PUBLISHER_TOOLS` 黑名单枚举，故清单外新工具
    泄漏亦被抓；覆盖**叙述行**（不止运行指令行），补 检查⑪ 只查运行指令行的漏网。
    范围：references/skills/** + INSTALL.md + references/steps/** 的 .md（用户端运行时文档·
          同 检查⑪ 边界）+ references/templates/用户基本规则-*.md（用户当指令读的规则模板）。
    豁免：CHANGELOG / 台账(decision-room 等) / 表格行(`|`起始·契约叙述非指令) /
          命中行或其后 20 行内含降级标记（复用 检查⑪ 的 _DEGRADE_MARKERS + 作者侧专用标记）。
    来源：2026-09-15 皮叔令「彻底根治·没有尾巴」——growth-box SKILL.md 引用 antibody_guard.sh
          （未随包分发的 Stop 守卫）实锤，同族 3 处已补降级声明。
    """
    markers = _DEGRADE_MARKERS + ["未随包分发", "未随本安装包分发", "作者侧", "发布者侧", "私有引擎"]
    issues = []
    for f in pkg.rglob("*.md"):
        rel = str(f.relative_to(pkg))
        if "CHANGELOG" in f.name or "__pycache__" in f.parts:
            continue
        in_scope = (rel.startswith("references/skills/") or rel == "INSTALL.md"
                    or rel.startswith("references/steps/")
                    or (rel.startswith("references/templates/") and f.name.startswith("用户基本规则-")))
        if not in_scope:
            continue
        if "decision-room" in f.name or "\u53f0\u8d26" in f.name:
            continue  # 机制台账=记录非指令
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue
        for i, line in enumerate(lines):
            if line.lstrip().startswith("|"):
                continue  # 表格行=契约叙述非指令
            if "\u5f00\u53d1\u5de5\u5177/" not in line:
                continue
            window = "\n".join(lines[i:min(len(lines), i + 21)])
            if any(m in window for m in markers):
                continue
            issues.append(f"作者侧路径引用未声明降级(\u5f00\u53d1\u5de5\u5177/): {rel}:{i+1}")
    return issues


# ── P1 反哺检查（2026-08-11）──
# Unix-only 模块：仅 POSIX 系统存在，Windows 上 import 即 ImportError 崩脚本
UNIX_ONLY_MODULES = ("fcntl", "grp", "resource", "termios", "tty", "pwd", "posix")


def _is_in_try_block(tree: ast.AST, target: ast.AST) -> bool:
    """判断 target 节点是否位于某个 try 语句块内（try/except/else/finally 全部子体）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for sub in ast.walk(node):
                if sub is target:
                    return True
    return False


def check_unix_only_imports(pkg: Path) -> list:
    """P1（2026-08-11 反哺）：跨平台 .py 顶层 import Unix-only 模块且无守卫→Windows 崩溃。
    背景：Qoder系加强包 route_unknown_unknown.py 旧版顶层 `import fcntl`（仅 Unix），
          Windows 全新安装 [2/8] 中止。权威源已改为 try/except 守卫（见主包同文件）；
          本检查抓"仍无守卫"的副本/新包。
    判定：模块级 Import/ImportFrom 命中 UNIX_ONLY_MODULES，且文件内无 try 守卫包裹该导入、
         也无 sys.platform/os.name 条件导入信号→FAIL。
    """
    issues = []
    for f in pkg.rglob("*.py"):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or ".git" in f.parts or f.name.endswith(".bak"):
            continue
        try:
            src = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError:
            continue
        has_platform_signal = ("sys.platform" in src) or ("os.name" in src) or ("import platform" in src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module.split(".")[0]] if node.module else []
            else:
                continue
            hit = [m for m in mods if m in UNIX_ONLY_MODULES]
            if not hit:
                continue
            if _is_in_try_block(tree, node) or has_platform_signal:
                continue  # 有守卫，安全
            issues.append(f"Unix-only导入无守卫[{','.join(hit)}]: {f.relative_to(pkg)}:{node.lineno}")
    return issues


# 安装器脚本（跨平台部署器双端）
_INSTALLER_SCRIPTS = ("setup.sh", "setup.ps1")
# 资产名提取的合法扩展名（避免抓版本号/纯路径串等非资产）
_ASSET_EXT = (".py", ".sh", ".ps1", ".md", ".json", ".yml", ".yaml", ".txt", ".command", ".bin")


def _extract_asset_names(path: Path) -> set:
    """从安装脚本中提取被引用（cp/copy/操作）的文件名集合（取 basename）。"""
    names = set()
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except (PermissionError, OSError):
        return names
    for line in lines:
        for m in re.finditer(r'["\']([^"\']+\.[A-Za-z0-9]+)["\']', line):
            base = m.group(1).split("/")[-1]
            if base.lower().endswith(_ASSET_EXT):
                names.add(base)
    return names


def check_installer_asset_parity(pkg: Path) -> list:
    """P1（2026-08-11 反哺）：安装器双端(setup.sh/ps1)引用资产名必须对称。
    背景：Qoder系加强包 setup.sh 与 setup.ps1 引用了不同文件名→Windows 端缺资产。
    判定：pkg 下若同时存在 setup.sh 与 setup.ps1，解析两端各自引用的文件名集合做对称 diff，
         任一端引用了另一端不存在的文件名→FAIL。两端均缺失→跳过（非安装器型包，不适用）。
    """
    sh = pkg / "setup.sh"
    ps1 = pkg / "setup.ps1"
    if not sh.exists() and not ps1.exists():
        return []  # 非安装器型包，跳过
    if sh.exists() and not ps1.exists():
        return ["缺 Win 安装器: setup.sh 有但 setup.ps1 缺失"]
    if ps1.exists() and not sh.exists():
        return ["缺 Mac 安装器: setup.ps1 有但 setup.sh 缺失"]
    sh_files = _extract_asset_names(sh)
    ps1_files = _extract_asset_names(ps1)
    issues = []
    for name in sorted(sh_files - ps1_files):
        issues.append(f"Mac安装器引用但Win端缺失资产: {name}")
    for name in sorted(ps1_files - sh_files):
        issues.append(f"Win安装器引用但Mac端缺失资产: {name}")
    return issues


# ── P1 反哺检查（2026-08-11·Windows 钩子失效反馈）──
# Windows 安装包用裸 `python` + 正斜杠路径 → 裸 python 被「应用执行别名」劫持→微软商店/失败；
# 正斜杠 C:/... 经 Git Bash(MSYS) 调度被路径转换误改 → 钩子静默失效（【🕳️】段永不路由）。
# 治本：Windows 段一律用 WorkBuddy 自带 python.exe 绝对路径(glob versions/*/python.exe) + MSYS_NO_PATHCONV=1 前缀。
_BUNDLED_PY_MARKER = "binaries/python"


def _has_bundled_py(seg: str) -> bool:
    """分隔符不敏感地判断"这段是否已用自带 python.exe 绝对路径"。

    根因修复（2026-10-01·假红根治）：文档里的路径按 Windows 原生写法是
    `.workbuddy\\binaries\\python\\versions\\*\\python.exe`（反斜杠），而原判据用
    正斜杠字面量 `in body` 匹配 ⇒ 匹配不上，于是**"声明自带绝对路径的那一行本身"**
    被判成"Windows 块裸 python 调用"——门禁把合规写法报成违规，长期 1 项红。
    归一只发生在比较前（`\\`→`/`），⛔不放宽语义：仍要求 binaries/python 确实在场。
    族：PAT-059（字面锚点不容书写变体→机器静默失配）。
    """
    return _BUNDLED_PY_MARKER in seg.replace("\\", "/")
_WIN_SIGNALS = ("MSYS_NO_PATHCONV", "$env:", "Get-ChildItem", "Get-Date",
                "Test-Path", "Copy-Item", "New-Item")


def check_windows_bare_python(pkg: Path) -> list:
    """P1（2026-08-11 Windows 钩子失效反馈反哺）：安装步骤文档的 Windows 段若用裸
    `python`/`python3` 作解释器（无自带 python 绝对路径）即 FAIL。
    背景：主包 step6-hook-install.md 原 Windows 段写 `python C:/.../route_unknown_unknown.py`，
          Windows 上裸 python 被应用执行别名劫持→钩子永不触发；同模式亦见于 INSTALL.md
          data_contamination_check.py 调用。治本=改用自带 python.exe 绝对路径 + MSYS_NO_PATHCONV=1。
    判定：扫描 INSTALL.md + references/steps/*.md 的代码块；
          仅查 Windows 块(powershell 围栏 / 含 _WIN_SIGNALS 信号)；
          块内出现裸 `python`/`python3` 解释器调用且整块不含 _BUNDLED_PY_MARKER → FAIL。
    macOS/Linux 的 ```bash 块不查(裸 python3 在该环境可用、非本次缺陷)。
    """
    issues = []
    doc_files = []
    steps_dir = pkg / "references" / "steps"
    if steps_dir.is_dir():
        doc_files.extend(sorted(steps_dir.glob("*.md")))
    install_md = pkg / "INSTALL.md"
    if install_md.is_file():
        doc_files.append(install_md)

    fence_re = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    for path in doc_files:
        try:
            raw = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        # 去除 blockquote 前缀(> )，使引用块内的围栏也能被解析
        text = re.sub(r"(?m)^>\s?", "", raw)
        rel = str(path.relative_to(pkg))
        for m in fence_re.finditer(text):
            lang = m.group(1).lower()
            body = m.group(2)
            is_win = (lang == "powershell") or any(sig in body for sig in _WIN_SIGNALS)
            if not is_win:
                continue
            if _has_bundled_py(body):
                continue  # 已用自带 python 绝对路径，安全
            for ln in body.splitlines():
                s = ln.strip()
                if s.startswith("#"):
                    continue
                if re.search(r"(?i)\bpython3?\b(?=\s|$)", s) and not _has_bundled_py(s):
                    issues.append(f"Windows块裸python调用(应改自带python.exe绝对路径): {rel}")
                    break
    return issues


def check_hardcoded_center_name(pkg: Path) -> list:
    """检查⑫（1.6）：安装脚本硬编码单一"记忆共享中心"目录名为默认值，且无候选探测/环境变量兜底。
    背景：DSH 加强包 v0.1.1 默认值写死 `MEMORY_CENTER="${MEMORY_CENTER:-$HOME/记忆共享中心}"`——
        其他用户共享目录叫"共享中心"/"记忆中心"等 → 不设环境变量直接跑 = 误报"未装布洛陀"。
        Loop 首轮未发现的死角：隐私检查只管"绝对路径泄漏"，没管"默认值写死单一目录名"（适配性死角）。
    判定（确定性 grep·零 LLM 裁决）：
      命中模式 = 赋值语句把 HOME/USERPROFILE + 单一固定目录名拼成默认值（`${VAR:-$HOME/xxx}` / Join-Path）。
      豁免（任一命中即合法）：
        a) 候选目录名列表（循环/数组遍历多个候选名，如 `for cand` / `foreach ($cand` / "候选"）
        b) 自动探测逻辑（find/Test-Path 遍历/glob）
      注：`${VAR:-$HOME/xxx}` 形式的"环境变量优先+默认值写死单一目录"即问题模式本身（环境变量只是手动兜底，
          不是自动适配不同目录名），⛔不作为豁免。
    范围：包内所有 .sh/.ps1 安装/接入脚本（setup*.sh / setup*.ps1 / 顶层 *.sh / *.ps1）。
    豁免：脚本内包含"候选/探测/自动查找/目录名可自定义"任一说明性标记，视为已声明通用化意图（降级为提示不阻断）。
    """
    issues = []
    # 命中模板：`VAR="${VAR:-$HOME/xxx}"` (sh) / `$VAR = ... Join-Path $env:USERPROFILE "xxx"` (ps1)
    sh_re = re.compile(r'^[A-Z_]+="\$\{[A-Z_]+:-\$HOME/[^"}]*\}"$')
    ps1_re = re.compile(r'Join-Path\s+\$env:USERPROFILE\s+"[^"]+"')
    center_hint = ("记忆共享中心", "共享中心", "记忆中心", "布洛陀", "记忆共享")
    generic_hint = ("候选", "探测", "自动查找", "目录名可自定义", "for cand", "foreach ($cand")
    for f in list(pkg.rglob("*.sh")) + list(pkg.rglob("*.ps1")):
        rel = str(f.relative_to(pkg))
        if "__pycache__" in f.parts or ".git" in f.parts:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue
        has_candidate_loop = False
        hit_line = None
        for i, line in enumerate(lines):
            if any(t in line for t in ("for cand", "foreach ($cand", "候选")):
                has_candidate_loop = True
            if hit_line is None:
                if sh_re.match(line.strip()) and any(h in line for h in center_hint):
                    hit_line = (i + 1, line.strip())
                elif ps1_re.search(line) and any(h in line for h in center_hint):
                    hit_line = (i + 1, line.strip())
        if hit_line is None:
            continue
        if has_candidate_loop:
            continue
        if any(g in "\n".join(lines) for g in generic_hint):
            issues.append(f"⚠️ 共享中心目录名疑似硬编码默认值(有通用化说明·请人工确认): {rel}:{hit_line[0]}")
            continue
        issues.append(f"共享中心目录名硬编码为单一默认值[{hit_line[1]}]: {rel}:{hit_line[0]}")
    return issues


def check_script_center_reachability(pkg: Path) -> list:
    """检查⑪-白名单（v1.8·2026-09-21）：承诺的「脚本中心」路径必须在包内真实存在。

    病根（立场卡 S879「结构性瓶颈须换路径·补优化是给不可优化对象白做工」）：
      检查⑪（黑名单枚举工具名）与 检查⑪-治本（找 `开发工具/` 字样）**共用同一个被
      relocate 改写过的观测面**——relocate 一级映射把作者侧「开发工具/」下的脚本族根参数化为
      `[记忆共享中心]/脚本中心/X`，`开发工具/` 字样随之消失 → 治本那条**结构性失明**；
      黑名单那条靠枚举，清单外新工具必漏。两条各自都对，合起来留缝。

    治本＝**判据换面**：不问「文本里出现了什么工具名」，只问「这条路径端用户机器上存不存在」。
      真源＝包内 `references/scripts/` + `references/hooks/`——install_scripts.py 定义
      「脚本中心 ← references/scripts 全量 + references/hooks」，故白名单即**包内物理构成**，
      不依赖任何外部枚举，新增脚本族自动被覆盖（黑名单「清单外新工具漏报」的已知局限由此消解）。

    ✅DO 覆盖**所有行含表格行**——命令表（逐行给命令）是用户真会照跑的最高危形态；
       不沿用 检查⑪/⑪-治本 的「表格行跳过」边界（那两处为叙述豁免设计，此处语义相反）。
    豁免：命中行或其后 20 行内含降级标记（复用 检查⑪ 的 _DEGRADE_MARKERS + 作者侧专用标记）。

    实证（2026-09-21 首跑）：同一次扫描，黑名单判据报 1 处，本判据报 13 组不可达引用
      （同一设施散在 5 文件）——「枚举完备性假设」即此前漏报之源。
    """
    markers = _DEGRADE_MARKERS + ["未随包分发", "未随本安装包分发", "作者侧", "发布者侧", "私有引擎"]
    script_center = pkg / "references" / "scripts"
    hooks_dir = pkg / "references" / "hooks"
    rx = re.compile(r"脚本中心/([A-Za-z0-9_\-\u4e00-\u9fff][A-Za-z0-9_\-./\u4e00-\u9fff]*)")
    issues = []
    for f in pkg.rglob("*.md"):
        rel = str(f.relative_to(pkg))
        if "CHANGELOG" in f.name or "__pycache__" in f.parts:
            continue
        in_scope = (rel.startswith("references/skills/") or rel == "INSTALL.md"
                    or rel.startswith("references/steps/")
                    or (rel.startswith("references/templates/") and f.name.startswith("用户基本规则-")))
        if not in_scope:
            continue
        if "decision-room" in f.name or "台账" in f.name:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, PermissionError):
            continue
        for i, line in enumerate(lines):
            for hit in rx.finditer(line):
                x = hit.group(1).rstrip(".").strip()
                if not x:
                    continue
                # 装后布局别名（2026-10-01 补·假红根治）：install_scripts.py:231-240 会把
                #   `references/知识联邦引擎-min/` → 装成 `脚本中心/知识联邦引擎/`（子目录改名映射）。
                #   原判据 premise 只知「脚本中心 ← references/scripts 全量 + hooks」，不知道这条映射，
                #   于是把装后**确实存在**的路径判成"端用户不可达"——长期 4 项红 = 警报疲劳，
                #   真断点（如 fcntl/裸 python）反而混在里面没人看。
                #   加映射而非放宽：仍要求包内有对应源文件，只是承认改名这一条真实装配事实。
                _alias_hit = False
                for _pre, _alt in (("知识联邦引擎/", "知识联邦引擎-min/"),):
                    if x.startswith(_pre):
                        _p = pkg / "references" / _alt / x[len(_pre):]
                        if _p.exists():
                            _alias_hit = True
                        break
                if (script_center / x).exists() or (hooks_dir / x).exists() or _alias_hit:
                    continue  # 白名单命中 = 端用户可达
                window = "\n".join(lines[i:min(len(lines), i + 21)])
                if any(mk in window for mk in markers):
                    continue
                issues.append("承诺路径端用户不可达(脚本中心/%s 不在包内): %s:%d" % (x, rel, i + 1))
    return issues


def main():
    only_author = "--only-author-path" in sys.argv
    _pos = [a for a in sys.argv[1:] if not a.startswith("--")]
    pkg = Path(_pos[0]).resolve() if _pos else DEFAULT_PKG
    if not pkg.exists():
        print(f"ℹ️  包路径不存在，跳过跨平台检查：{pkg}")
        sys.exit(0)

    print(f"🔍 跨平台兼容性检查 · {pkg.name}")
    print()

    all_issues = []
    checks = [
        ("双平台脚本配对", check_paired_scripts(pkg)),
        ("编码/换行符", check_encoding_and_lineendings(pkg)),
        ("Shebang检测", check_shebang(pkg)),
        ("Windows路径残留", check_backslash_paths(pkg)),
        ("单平台路径假设(检查⑩)", check_unix_path_assumption(pkg)),
        ("发布者工具泄漏(检查⑪·advisory·枚举不完备)", check_publisher_tool_leak(pkg), True),
        ("作者侧路径引用未声明(检查⑪-治本)", check_author_path_undeclared(pkg)),
        ("Unix-only导入守卫(P1)", check_unix_only_imports(pkg)),
        ("安装器双端资产对称(P1)", check_installer_asset_parity(pkg)),
        ("Windows裸python调用(P1)", check_windows_bare_python(pkg)),
        ("共享中心目录名硬编码(检查⑫)", check_hardcoded_center_name(pkg)),
        ("承诺路径可达性(检查⑪-白名单)", check_script_center_reachability(pkg)),
    ]

    if only_author:
        checks = [c for c in checks if "作者侧路径" in c[0]]

    for entry in checks:
        name, issues = entry[0], entry[1]
        advisory = len(entry) > 2 and entry[2]
        if issues:
            print(f"  {'⚠️' if advisory else '❌'} {name}: {len(issues)}项" + ("（advisory·不阻断·仅显形）" if advisory else ""))
            for iss in issues[:10]:
                print(f"     {iss}")
            if len(issues) > 10:
                print(f"     ...及另外{len(issues)-10}项")
            if not advisory:
                all_issues.extend(issues)
        else:
            print(f"  ✅ {name}: 通过")

    print()
    if all_issues:
        print(f"❌ 跨平台检查未通过：{len(all_issues)} 项缺陷")
        sys.exit(1)
    else:
        print("✅ 跨平台兼容性检查通过：0 缺陷")
        sys.exit(0)


if __name__ == "__main__":
    main()
