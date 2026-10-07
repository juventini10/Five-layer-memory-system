#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""privacy_check.py — 布洛陀发布包隐私残留检测（Phase X-PKG 第4检查项）
================================================================
职责：扫描安装包全文本文件，检测 deident/STRIP 可能遗漏的隐私残留。
      若目标路径不存在（安装包用户环境）→ 退出码0（graceful skip）。

被谁调用：clock-loop "loop 安装包" 路径 Phase X-PKG 机检。
命令行：python3 privacy_check.py [<包根目录>]
        默认包根：按脚本自身位置推导（verify.sh 锚定·2026-09-20 C3 自推导化）

退出码：0=通过（含graceful skip）  1=检测到隐私残留

设计约束（对齐 §五原则6隐私红线 + deident_rules.py 规则集）：
- 关键词集覆盖：身份/称呼/路径/行为偏好/STRIP未清/source泄露
- 仅扫文本类文件（复用 deident ALLOWED_EXT 白名单）
- 白名单排除：__pycache__/.git/.DS_Store/.bak
- 结果输出 human-readable + 退出码机械判定

⚠️ v1.1 认知诚实边界（自指盲区·2026-09-04 实测后补）：
  本脚本第 _should_scan 跳过扫描自身（防检测规则字符串被当泄露的假阳性）——
  这造成一个**结构性盲区**：检测器自身的隐私残留永远检不出来。
  根治不靠"不跳过自身"（那会永久假阳），而靠**作者隐私词不入本文件**：
  已用 STRIP 标记隔离 + deident 规则8 打包时自动清空（见 PRIVACY_CHECKS 上方说明）。
  ⛔DO NOT 在本文件任何位置（含注释/测试/docstring）直写作者隐私特征词。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────────────
# 自推导（2026-09-20 C3 根治）：原作者主目录硬编码——装机侧经 deident 替换后=字面占位符
#   死路径（引用落点检查⑪实锤）。按脚本位置推导包根
#   （scripts→clock-loop→skills→references→包根），verify.sh 存在锚定；作者侧直跑请传位置参数。
_pkg = Path(__file__).resolve()
_cand = _pkg.parents[4] if len(_pkg.parents) > 4 else _pkg.parent
DEFAULT_PKG = _cand if (_cand / "verify.sh").exists() else _cand

# 作者真实用户名（动态获取，不写死）
AUTHOR_USERNAME = Path.home().name

# 隐私关键词分组：每组 (组名, 关键词列表, 严重度)
# ── v1.1（2026-09-04）作者隐私区段隔离 ───────────────────────────────
# 病（你定为隐私红线·实测实锤）：本检测器把作者本人的隐私特征词硬编码在自身体内，
#   被打进 2 个对外发布包；而两道防线均对它失明——①deident 规则6 只清
#   HTML 注释形式的标记区段（本文件的关键词无标记→不脱敏）②本脚本
#   第 _should_scan 显式跳过扫描自身（防假阳性）→ 实跑永远报"✅ 0 残留"。
# 解（复用现有 STRIP 机制·不新造概念）：给作者隐私词加 **Python 注释形式**的 STRIP
#   起止标记（井号注释·标记名 author_privacy_keywords），deident 新增规则8 打包时自动清空本区段。
#   🔴⛔本说明段不得写出标记的字面拼法（井号+STRIP_START+冒号）——原因是 deident 规则8
#   会把"解释标记的注释行"误当真标记起点 → 从注释处一直清到真结束标记 → 大段代码被吞、
#   语法崩坏（2026-09-04 实测踩坑：unexpected indent）。这是"检测规则体内含被检测模式"
#   的自指陷阱，与本脚本跳过扫自身属同一类盲区。
#   为什么不用 HTML 注释标记：它在 .py 里是语法错误；为什么不用哈希化：
#   sha1 不可逆而检测逻辑是 `kw in line` 子串匹配，只有哈希无法做子串检测（技术上不可行）。
# 清空后本检测器在安装包里仍有效：动态用户名/绝对路径/死路径三组保留（对使用者通用），
#   使用者按注释提示填入自己的隐私特征词即可。
PRIVACY_CHECKS = [
    ("身份-用户名", [AUTHOR_USERNAME], "🔴"),
    ("身份-绝对路径", [f"/Users/{AUTHOR_USERNAME}/", f"/home/{AUTHOR_USERNAME}/"], "🔴"),
    # STRIP_START:author_privacy_keywords
    # （此处初始为空——安装后由使用者填入自己的隐私特征词；⛔作者隐私词绝不进包）
    # STRIP_END:author_privacy_keywords
    ("死路径", [".openclaw/workspace/MEMORY.md", "QClaw记忆/MEMORY.md"], "🟡"),
]

# 文本文件扩展名白名单（复用 deident_rules.py）
ALLOWED_EXT = {
    ".md", ".markdown", ".txt", ".py", ".sh", ".bash", ".zsh",
    ".ps1", ".bat", ".cmd", ".yaml", ".yml", ".json", ".jsonc",
    ".toml", ".cfg", ".ini", ".conf", ".sample", ".csv", ".mdc",
}

# 排除路径片段
EXCLUDE_PARTS = {"__pycache__", ".git", ".DS_Store"}


def _should_scan(filepath: Path) -> bool:
    """判断文件是否应该扫描。"""
    if any(part in filepath.parts for part in EXCLUDE_PARTS):
        return False
    if filepath.suffix.lower() not in ALLOWED_EXT:
        return False
    if filepath.name.endswith(".bak"):
        return False
    # 跳过扫描自身（防止检测规则字符串被当作泄露的假阳性）
    if filepath.name == "privacy_check.py":
        return False
    return True


def scan(pkg_root: Path) -> list:
    """扫描包目录，返回 [(文件, 行号, 组名, 匹配片段, 严重度), ...]"""
    findings = []
    # v3.52.1（#47两层盲区根治）：有references时旧版只扫references/——包根顶层的
    # INSTALL.md/version.md/CHANGELOG.md/SKILL.md等不入扫描。改为扫包根全树（references/
    # 自然包含·排除目录由EXCLUDE_PARTS管）。
    roots = [pkg_root] if (pkg_root / "references").exists() else []
    if not roots:
        roots = [pkg_root]  # 无references的包：行为与旧版一致（扫包根）

    seen = set()
    for root in roots:
        for filepath in sorted(root.rglob("*")):
            if str(filepath) in seen:
                continue
            seen.add(str(filepath))
            if not filepath.is_file() or not _should_scan(filepath):
                continue
            try:
                lines = filepath.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, PermissionError):
                continue

            for line_no, line in enumerate(lines, 1):
                for group_name, keywords, severity in PRIVACY_CHECKS:
                    for kw in keywords:
                        if kw in line:
                            # 允许注释中提及"替代原作者 openclaw/QClaw 死路径"作为历史说明
                            if "替代原作者" in line and kw in ("QClaw记忆/MEMORY.md", ".openclaw/workspace/MEMORY.md"):
                                continue
                            # 允许模板占位符形态——《书名》是字面占位非真实内容，真书名仍报
                            # 来源：2026-07-30 pkg实弹假阳性（note-template.md命名规范行被误报，源包两侧同文本零隐私）
                            # v1.1：⛔不再按具体文件名硬匹配——原写法在豁免逻辑里重复了作者个人文件名
                            #   字面量，而该文件名已列入上方 STRIP 隐私区段→脱敏后此处会残留→自相矛盾。
                            #   改按占位符特征（《书名》）豁免，不含任何作者个人文件名字面量。
                            if "《书名》" in line:
                                continue
                            snippet = line.strip()[:80]
                            findings.append((
                                str(filepath.relative_to(pkg_root)),
                                line_no, group_name, snippet, severity
                            ))
    return findings


def main():
    pkg_root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PKG

    if not pkg_root.exists():
        print(f"ℹ️  包路径不存在，跳过隐私检测：{pkg_root}")
        print("   （安装包用户环境·graceful skip）")
        sys.exit(0)

    print(f"🔍 隐私残留检测 · {pkg_root.name}")
    print(f"   扫描范围：{pkg_root}/（包根全树·#47盲区根治）")
    print()

    findings = scan(pkg_root)

    if not findings:
        print("✅ 隐私检测通过：0 残留")
        sys.exit(0)

    # 有残留 → 输出报告
    print(f"❌ 检测到 {len(findings)} 处隐私残留：\n")
    for filepath, line_no, group, snippet, severity in findings:
        print(f"  {severity} [{group}] {filepath}:{line_no}")
        print(f"     {snippet}")
        print()

    # 按组汇总
    from collections import Counter
    group_counts = Counter(f[2] for f in findings)
    print("── 汇总 ──")
    for g, c in group_counts.most_common():
        print(f"  {g}: {c} 处")

    sys.exit(1)


if __name__ == "__main__":
    main()
