#!/usr/bin/env python3
"""check-cured-snapshot.py — 固化版本对账脚本

检测 triwich / meta-aletheia 的固化副本（clock-loop/references/）是否与源 Skill 版本一致。
不一致 = 固化过期 = clock-loop 正在用过期的尺子评估。

用法：
  python3 check-cured-snapshot.py
  → exit 0 = 全部一致
  → exit 1 = 有固化过期（输出差异清单到 stdout）

设计原则：脚本机械读版本号比对——零手工，零 prose 判断。
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import sys
import yaml
from pathlib import Path

SKILL_BASE = Path(__file__).parent.parent  # clock-loop/
REFS = SKILL_BASE / "references"

CHECKS = [
    {
        "name": "triwich",
        "source_skill": Path.home() / "个人AI档案/技能配置/triwich/SKILL.md",
        "cured_file": REFS / "triwich-integration.md",
    },
    {
        "name": "meta-aletheia",
        "source_skill": Path.home() / "个人AI档案/技能配置/meta-aletheia/SKILL.md",
        "cured_file": REFS / "philosophical-evaluation.md",
    },
]


def read_version(path: Path) -> str | None:
    """从 YAML frontmatter 读 version 字段"""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    # 提取 YAML frontmatter (--- 之间的内容)
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
        return str(fm.get("version", ""))
    except Exception:
        return None


def main():
    errors = []
    for check in CHECKS:
        src_ver = read_version(check["source_skill"])
        cured_ver = read_version(check["cured_file"])

        if src_ver is None:
            errors.append(f"❌ {check['name']}: 无法读取源 Skill 版本（{check['source_skill']}）")
            continue
        if cured_ver is None:
            errors.append(f"❌ {check['name']}: 无法读取固化版本（{check['cured_file']}）")
            continue

        if src_ver != cured_ver:
            errors.append(
                f"⚠️ {check['name']}: 固化过期 —— 源 v{src_ver} ≠ 固化 v{cured_ver}"
            )
        else:
            print(f"✅ {check['name']}: v{src_ver} == v{cured_ver}")

    if errors:
        print("\n".join(errors))
        print(f"\n🔴 固化版本对账失败：{len(errors)} 项不一致")
        print("→ 需手动重新固化到 clock-loop/references/ 并升 version，否则 clock-loop 用过期的尺子评估")
        sys.exit(1)

    print("\n✅ 固化版本全绿")
    sys.exit(0)


if __name__ == "__main__":
    main()
