#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reference_path_check.py — 发包自检 ⑪「脚本内引用落点存在性」（2026-09-20 C3·群友问题6 根治）

为什么存在
----------
群友实锤（§70）：growth_signal_collector.py 内引用 `开发工具/...` 子路径——镜像替换了
`~/个人AI档案` 根但**子路径段没跟布局转换** → 用户机器上引用断头 → 感知层 3/4 空转。
原门禁只查"有没有占位符"，不查"占位符后面的路通不通"——**账面干净≠运行可达**（S885）。

判据（三腿·过任一即可达）
--------------------------
腿① 包内模板实体：references/templates/<rel>、references/<rel>、references/templates/<basename>
腿② 安装时生成：references/steps/*.md 文本提及该 basename（安装器会造）
腿③ 运行时生长白名单：脚本中心/成长箱/数字分身/成就系统/记忆琥珀/工作日志/.install/
    日记/[日记仓库]/技能配置 等用户机器上随使用生长的目录——安装器只建骨架，
    内容运行期产生，包内无实体属预期。

用法
----
    python3 reference_path_check.py --pkg-root <包根>
    python3 reference_path_check.py --pkg-root <包根> --list     # 只列抽到的引用（调试白名单用）
退出码：0=全部可达  1=存在断头引用  2=参数错误
"""
import argparse
import os
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SCAN_EXT = {".py", ".sh", ".ps1", ".bash", ".zsh"}
# 引用形态：占位根/X（方括号或 MEMORY_CENTER 变量两种写法）后跟到引号/空白/右括号/行尾的路径段
# 2026-09-30：字符类补 `|` —— sed 分隔符（`s|\[记忆共享中心\]|$MC|g; s|\[数字分身中心\]|$MC/数字分身|g`）
#   会被原式抽成 `数字分身|g` 假路径 ⇒ 假阳性（实测 adapters/lobsterai/setup.sh）。
#   `|` 在路径语境中从不是合法字符 ⇒ 收进排除集零误伤。
REF_RE = re.compile(
    r"""(?:\[记忆共享中心\]|\$\{MEMORY_CENTER\}|\$MEMORY_CENTER|\$MC)/([^\s"'`)\];,|]+)"""
)

# 腿③ 运行时生长白名单（首段目录）——安装器建骨架/内容随使用生长，包内无实体属预期
INSTALL_TIME_DOCS = {"变更日志.md", "技能变更审计.md"}   # 安装时生成/作者生态降级·装机后存在
RUNTIME_ROOTS = {
    "脚本中心", "成长箱", "数字分身", "成就系统", "记忆琥珀", "工作日志",
    "记忆规则", "自定义层", "技能配置", "AI学习库", " [日记仓库]",
    "[日记仓库]", "日志", "logs", ".install", "记忆蓝图", "核心层",
    "认知层", "行为层", "情境层", "潜意识层", "最伟大的我", "未知未知", "蒸馏源档案",
    "记忆蒸馏", "评估知识库", "归档", "QClaw记忆",
    # 2026-09-30 件4 配套：`知识库/` 层级 —— 端用户卡库/概念库落
    #   `~/个人AI档案/知识库/{AI学习库,概念卡}/`（真源=数字分身完整版-安装流程设计
    #   §B2·Phase B 引擎 ensure_dirs() 运行期建）。⛔ 原白名单只列 `AI学习库`
    #   而**无 `知识库`** ⇒ 解析出的首段=`知识库` 落空 → 正确路径反被判**断头**
    #   （实证 4 处：auto_pass_audit / count_card_topic / immunity_l1_draft×2）。
    #   同族教训：「路径层级变了，判据面必须同步变」——否则新对的被当错、旧错的被放过。
    "知识库",
}


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def collect_refs(pkg_root: Path):
    """扫包内代码类文件，抽 (rel_file, 引用相对路径) 集合。"""
    refs = set()
    for dp, dn, fn in os.walk(pkg_root):
        parts = Path(dp).parts
        if ".git" in parts or "__pycache__" in parts:
            continue
        for f in fn:
            p = Path(dp) / f
            if p.suffix.lower() not in SCAN_EXT:
                continue
            if f == "reference_path_check.py":
                continue                              # 自身 docstring 示例豁免（pkg_cleanliness 同款手法）
            if "/tests/" in str(p).replace(os.sep, "/"):
                continue                              # 测试 fixture 字符串（抗体正则样本·不执行·非真引用）
            text = _read(p)
            for m in REF_RE.finditer(text):
                rel = m.group(1).strip().rstrip("/")
                # 动态/示例形态跳过：变量插值/glob/花括号/中文标点说明尾——静态无法判定或非真引用
                if any(ch in rel for ch in "${}*{}：（）：，。·"):
                    continue
                if rel == "foo.md":
                    continue                          # sync_guard T5 句读测试样本名（fixture 字符串）
                if rel == "x.md":
                    continue                          # 2026-09-30：antibody_gate 自测夹具样本名（grep -L 判据用例·同 foo.md 族）
                if rel.startswith(".."):
                    # 2026-09-30：`~/个人AI档案/../X` 越出中心 ⇒ 非「中心内资源引用」，
                    #   本检查器的管辖域不覆盖（实测 adapters/lobsterai/setup.sh 的
                    #   `$MC/../开发工具/platform_adaptation_check.py` 兜底探测）。
                    continue
                if rel:
                    try:
                        where = str(p.relative_to(pkg_root))
                    except ValueError:
                        where = str(p)
                    refs.add((where, rel))
    return refs


def reachable(pkg_root: Path, rel: str, steps_txt: str) -> bool:
    """三腿可达判定。rel 形如 脚本中心/rule_fragment_inject.py 或 记忆规则/铁律版.md"""
    if rel in INSTALL_TIME_DOCS:
        return True                                   # 腿③b 安装时生成的根级文档
    first = rel.split("/")[0]
    if first in RUNTIME_ROOTS:
        return True                                   # 腿③
    base = os.path.basename(rel)
    for cand in (
        pkg_root / "references" / rel,
        pkg_root / "references" / "templates" / rel,
        pkg_root / "references" / "templates" / base,
        pkg_root / "references" / base,
    ):
        if cand.exists():
            return True                               # 腿①
    if base in steps_txt or rel in steps_txt:
        return True                                   # 腿②
    return False


def main():
    ap = argparse.ArgumentParser(description="脚本内引用落点存在性检查（C3·只读）")
    ap.add_argument("--pkg-root", required=True)
    ap.add_argument("--list", action="store_true", help="只列抽到的引用，不判定（调试白名单）")
    a = ap.parse_args()
    root = Path(os.path.expanduser(a.pkg_root))
    if not root.is_dir():
        print(f"[FAIL] 包根不存在: {root}", file=sys.stderr)
        return 2

    refs = collect_refs(root)
    if a.list:
        for where, rel in sorted(refs):
            print(f"  {where}  →  ~/个人AI档案/{rel}")
        print(f"\n共 {len(refs)} 处引用")
        return 0

    steps_txt = ""
    sdir = root / "references" / "steps"
    if sdir.is_dir():
        for f in sdir.glob("*.md"):
            steps_txt += _read(f)

    dead = []
    for where, rel in sorted(refs):
        if not reachable(root, rel, steps_txt):
            dead.append((where, rel))

    if dead:
        print(f"  [FAIL] 脚本内引用落点断头: {len(dead)} 处（占位符后的路径三腿均不可达）")
        for where, rel in dead[:12]:
            print(f"         - {where} → ~/个人AI档案/{rel}")
        if len(dead) > 12:
            print(f"         ... 另有 {len(dead) - 12} 处")
        return 1
    print(f"  [PASS] 脚本内引用落点: {len(refs)} 处引用全部可达（模板实体/步骤生成/运行时生长三腿）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
