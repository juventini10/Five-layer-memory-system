#!/usr/bin/env python3
"""
sync_readme_scripts_index.py — 数字分身 README scripts 索引自动生成器

功能：
  1. 扫描 scripts/ 目录下所有文件
  2. 对 .py/.sh 提取头部说明（docstring/注释首行）
  3. 生成 Markdown 表格，替换 README 中 <!-- SCRIPTS-INDEX:START --> 和 <!-- SCRIPTS-INDEX:END --> 之间的内容
  4. 幂等：重复运行结果一致

设计原则：
  - 消除双本账（C-085）：scripts 索引从实际目录派生，不手工维护
  - 相对路径：脚本位于 scripts/ 内，README 在上级，用 ../README.md
  - 失败告警：异常时 exit 非0，launchd WatchPaths 触发失败可被 L2 巡检发现

用法：
  python3 sync_readme_scripts_index.py          # 同步索引
  python3 sync_readme_scripts_index.py --check  # 只检查是否需要更新（exit 0=已最新, 1=需更新）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime

# ── 路径配置（相对路径，不硬编码绝对路径）──
# ⛔不用 resolve()：本件真源在脚本中心、部署面经软链调用（数字分身/scripts/→本件）。
#   resolve 会把 SCRIPT_DIR 漂到真源目录→README_PATH 落到脚本中心/README.md（无标记块）→
#   "markers not found"（2026-10-06 实证）且 scan_scripts 扫错对象（真源≠部署面）。
#   不 resolve 时 __file__ 即调用路径：软链调用=部署面 scripts/（plist/WatchPaths 语义）✅；
#   直接跑真源属误用（见头部用法说明）。
SCRIPT_DIR = Path(__file__).parent
README_PATH = SCRIPT_DIR.parent / "README.md"
START_MARKER = "<!-- SCRIPTS-INDEX:START -->"
END_MARKER = "<!-- SCRIPTS-INDEX:END -->"

# ── 文件类型分类 ──
SCRIPT_EXTENSIONS = {".py", ".sh", ".pl", ".rb"}
DATA_EXTENSIONS = {".json", ".log", ".txt", ".csv", ".yaml", ".yml", ".toml", ".md"}


def extract_py_docstring(filepath: Path) -> str:
    """提取 Python 文件的 docstring 首行"""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
        # 先用 ast 取模块级 docstring：旧正则 `"""[^"]*?"""` 遇到正文含双引号会静默跳过模块 docstring、
        # 抓到下一个函数 docstring 当描述（2026-09-27 实测：state_bus_sync v2.1.0 因正文含引号被写成 file_hash 的说明）
        try:
            import ast
            mod = ast.parse(content)
            doc = ast.get_docstring(mod) or ""
        except Exception:
            doc = ""
        if not doc.strip():
            # 匹配模块级 docstring（三引号）
            m = re.search(r'^[ \t]*"""([^"]*?)"""', content, re.DOTALL | re.MULTILINE)
            if not m:
                m = re.search(r"^[ \t]*'''([^']*?)'''", content, re.DOTALL | re.MULTILINE)
            doc = m.group(1) if m else ""
        if doc.strip():
            # 取第一行非空
            for line in doc.strip().split("\n"):
                line = line.strip()
                if line:
                    return line[:80]
    except Exception:
        pass
    return ""


def extract_sh_comment(filepath: Path) -> str:
    """提取 shell 脚本头部注释的首行有意义内容"""
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").split("\n")
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            # 跳过 shebang 和空行
            if line.startswith("#!") or not line:
                continue
            # 跳过纯注释标记行（如 # ====）
            if re.match(r"^#+\s*[=\-*]+$", line):
                continue
            if line.startswith("#"):
                text = line.lstrip("#").strip()
                if text and len(text) > 3:
                    return text[:80]
    except Exception:
        pass
    return ""


def get_file_description(filepath: Path) -> tuple[str, str]:
    """返回 (类型, 说明)"""
    ext = filepath.suffix.lower()
    name = filepath.name

    if ext in SCRIPT_EXTENSIONS:
        if ext == ".py":
            desc = extract_py_docstring(filepath)
            ftype = "Python"
        else:
            desc = extract_sh_comment(filepath)
            ftype = "Shell"
        if not desc:
            desc = "（无说明）"
        return ftype, desc

    if ext in DATA_EXTENSIONS:
        if ext == ".json":
            return "数据", "JSON 数据/配置文件"
        if ext == ".log":
            return "日志", "运行日志"
        if ext in {".yaml", ".yml"}:
            return "配置", "YAML 配置文件"
        return "数据", f"{ext[1:].upper()} 文件"

    return "其他", f"{ext or '无扩展名'} 文件"


def scan_scripts() -> list[dict]:
    """扫描 scripts 目录，返回文件信息列表"""
    files = []
    for f in sorted(SCRIPT_DIR.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            ftype, desc = get_file_description(f)
            size = f.stat().st_size
            files.append({
                "name": f.name,
                "type": ftype,
                "desc": desc,
                "size": size,
            })
    return files


def generate_table(files: list[dict]) -> str:
    """生成 Markdown 表格"""
    lines = []
    lines.append("| 脚本 | 类型 | 说明 |")
    lines.append("|------|------|------|")
    for f in files:
        # 转义管道符
        name = f["name"].replace("|", "\\|")
        desc = f["desc"].replace("|", "\\|")
        lines.append(f"| `{name}` | {f['type']} | {desc} |")
    return "\n".join(lines)


def sync_readme(check_only: bool = False) -> int:
    """同步 README 中的 scripts 索引"""
    if not README_PATH.exists():
        print(f"ERROR: README not found: {README_PATH}", file=sys.stderr)
        return 2

    content = README_PATH.read_text(encoding="utf-8")

    if START_MARKER not in content or END_MARKER not in content:
        print(f"ERROR: markers not found in README", file=sys.stderr)
        return 2

    files = scan_scripts()
    table = generate_table(files)

    # 构建新的索引区块（包含标题和说明）
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_block = (
        f"{START_MARKER}\n"
        f"### scripts 索引（自动生成·勿手工编辑此区域）\n\n"
        f"> 由 `scripts/sync_readme_scripts_index.py` 自动生成，WatchPaths 事件驱动同步。手工编辑会被覆盖。\n"
        f"> 共 {len(files)} 个文件 · 最后同步 {timestamp}\n\n"
        f"{table}\n"
        f"{END_MARKER}"
    )

    # 用正则替换标记之间的内容（包括标记本身）
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    # 检查是否需要更新：表格（实质内容）已一致即视为最新，仅时间戳差异不重写
    # （根治自动同步反复制造 git 脏区：跨分钟运行会因时间戳不同而整块重写）
    current_match = pattern.search(content)
    if current_match and table in current_match.group(0):
        print(f"✅ README scripts 索引已是最新（{len(files)} 个文件）")
        return 0

    if check_only:
        print(f"⚠️  README scripts 索引需要更新（当前 {len(files)} 个文件）")
        return 1

    # 执行替换
    new_content = pattern.sub(new_block, content)
    README_PATH.write_text(new_content, encoding="utf-8")
    print(f"✅ README scripts 索引已同步（{len(files)} 个文件）→ {README_PATH}")
    return 0


if __name__ == "__main__":
    check_only = "--check" in sys.argv
    sys.exit(sync_readme(check_only=check_only))
