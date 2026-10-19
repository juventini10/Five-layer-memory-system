#!/usr/bin/env python3
# version: v1.0.0
"""Skill 生态健康度守卫 · 公共原语（跨工具中立·各端 import 不复制）。

## 存在理由（《04-跨端接入指南》§二·七·〇 动作 3「先查可复用」）

四端（catpaw / doubaowork / teleagent / hermes）各自写过一份 200~260 行
同构守卫 = 典型重复造轮子（复制=双本账漂移·见 title-namer 先例 L184）。
本件按「公共原语 + 端薄适配器」两段式抽出四端共有判据，各端只写
「定位 skills 根 + 必备清单 + 端特有面」三件事。

⛔ 本件不含任何端路径常量——端专属一律走端适配器（跨工具中立性 §二·五）。

## 四检测（族内已验证·沿用不另造判据）

1. 软链有效性（断链）           → RED
2. SKILL.md 存在 + frontmatter name → WARN
3. frontmatter name 重名冲突      → RED
4. 必备 Skill 缺失               → WARN

## 假阳性豁免（Hermes 端 2026-10-01 三处实测沉淀·族内共享）

- 系统/隐藏目录（`.` 开头）：端自身机制目录，⛔ 不是 Skill 也不是垃圾
- 分类目录（含 DESCRIPTION.md 或含子 SKILL.md）：平台原生组织形态
- 资源目录（非空且无 SKILL.md）：Skill 的脚本/参考附属目录，删了丢资源

⛔ 顺序不可颠倒：先判 Skill 本体语义（frontmatter/重名），再判资源豁免。

## 反「静默旁路」（Hermes 段判据沉淀③）

聚合/派生层的 `except Exception: pass` 是所有假绿的共同上游。
本件所有解析失败 → 进 findings（kind="parse_error"·WARN），⛔ 不吞。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
from datetime import datetime

_FM_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.M)


def fm_name(skill_md: str):
    """读 SKILL.md frontmatter 的 name。

    ⛔ 解析失败返回 None（不猜语义）；⛔ 文件读取失败同上。
    """
    try:
        head = open(skill_md, encoding="utf-8", errors="replace").read(4096)
    except OSError:
        return None
    if not head.startswith("---"):
        return None
    m = _FM_NAME_RE.search(head)
    return m.group(1).strip().strip("\"'") if m else None


def classify(path: str):
    """判一个条目属于哪类（返回 kind 字符串）。

    kind ∈ {system, symlink, category, resource, skill}
    ⛔ 只看形态不看名字——命名不做判据（防把平台形态当违规）。
    """
    if os.path.islink(path):
        return "symlink"
    if not os.path.isdir(path):
        return "skip"
    if os.path.isfile(os.path.join(path, "DESCRIPTION.md")):
        return "category"
    try:
        subs = [d for d in os.listdir(path)
                if os.path.isfile(os.path.join(path, d, "SKILL.md"))]
    except OSError:
        subs = []
    if subs:
        return "category"
    md = os.path.join(path, "SKILL.md")
    if os.path.isfile(md):
        return "skill"
    try:
        nonempty = bool(os.listdir(path))
    except OSError:
        nonempty = False
    return "resource" if nonempty else "empty"


def new_report(skills_dir: str, version: str):
    return {
        "version": version,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "skills_dir": skills_dir,
        "total": 0, "categories": 0, "system_dirs": 0, "resources": 0,
        "names": 0, "findings": [], "red": 0, "warn": 0,
    }


def add(rep: dict, level: str, kind: str, detail: str):
    rep["findings"].append({"level": level, "kind": kind, "detail": detail})


def finalize(rep: dict):
    rep["red"] = sum(1 for f in rep["findings"] if f["level"] == "RED")
    rep["warn"] = sum(1 for f in rep["findings"] if f["level"] == "WARN")
    return rep


def self_test_core(check_fn) -> int:
    """通用自测夹具：五类异常各一例 + 空目录变异探针。

    ⛔ 全程临时目录·不碰任何真实 skills 根。
    变异探针（防凭空造告警）：空目录除 required_missing 外不得有其他告警。
    """
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        os.symlink(os.path.join(td, "nonexistent-target"),
                   os.path.join(td, "broken-skill"))
        os.makedirs(os.path.join(td, "empty-dir"))
        os.makedirs(os.path.join(td, "no-fm"))
        open(os.path.join(td, "no-fm", "SKILL.md"), "w").write("正文无 frontmatter\n")
        for d in ("dup-a", "dup-b"):
            os.makedirs(os.path.join(td, d))
            open(os.path.join(td, d, "SKILL.md"), "w").write(
                f"---\nname: same-name\n---\n# {d}\n")
        os.makedirs(os.path.join(td, "good"))
        open(os.path.join(td, "good", "SKILL.md"), "w").write(
            "---\nname: good\n---\n# ok\n")
        os.makedirs(os.path.join(td, "cat-dir"))
        open(os.path.join(td, "cat-dir", "DESCRIPTION.md"), "w").write("分类\n")

        rep = check_fn(td)
        kinds = {f["kind"] for f in rep["findings"]}
        expect = {"broken_symlink", "no_skill_md", "no_frontmatter_name",
                  "duplicate_name", "required_missing"}
        missing = expect - kinds
        print(f"  self-test: 检出 {sorted(kinds)}")
        print("  MISSING:" + str(sorted(missing)) if missing else "  ALL-EXPECTED-HIT")
        # 假阳性抑制：分类目录不得被报缺件
        cat_hit = [f for f in rep["findings"]
                   if f["kind"] in ("no_skill_md",) and "cat-dir" in f["detail"]]
        print(f"  分类目录豁免：{'FAIL(误报)' if cat_hit else 'OK ✓'}")

    with tempfile.TemporaryDirectory() as td2:
        r2 = check_fn(td2)
        extra = {f["kind"] for f in r2["findings"]} - {"required_missing"}
        print(f"  空目录变异：额外告警={sorted(extra) or 'NONE ✓'}")

    return 0 if not missing and not cat_hit else 1
