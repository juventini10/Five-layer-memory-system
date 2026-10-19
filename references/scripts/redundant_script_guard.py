#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redundant_script_guard.py — 脚本唯一真相源路径纪律·机械兜底
（v1.3.40 脚本架构设计通用规范 §一 推论应用实例延伸）

检测：开发工具/ 下是否存在与 技能配置/*/scripts/ 同名的「系统机制族」脚本（野副本）。
野副本根因 = AI 只查单目录就断言缺失 → 在 开发工具/ 另建正本已存在于 技能配置/*/scripts/ 的脚本。
本守卫排除通用模块名(stoplist)以降低误报（各 Skill 自带内部模块 utils.py/render.py 等不算野副本）。
命中即 RED(exit1)，供 patrol/hook 接入；干净即 GREEN(exit0)。

用法：python3 redundant_script_guard.py
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys

ROOT = os.path.expanduser("[记忆共享中心]")
DEV = os.path.join(ROOT, "开发工具")
SKILL = os.path.join(ROOT, "技能配置")

# 通用模块名 stoplist：各 Skill 自带内部模块，非系统机制脚本副本，不视为野副本
GENERIC = {
    "__init__.py", "build.py", "build_metadata.py", "checks.py", "content.py",
    "draft-release-notes.py", "highlight.py", "lint.py", "mac_draft.py", "mcp_server.py",
    "mermaid_normalize.py", "optional_deps.py", "preview.py", "render.py", "shared.py",
    "site_facts.py", "slides-en.py", "slides.py", "smoke_test.py", "stats.py",
    "test_build.py", "tokens.py", "utils.py", "verify.py", "visual.py", "windows_draft.py",
}

_LIB_MARKERS = ("site-packages", "/lib/python", "node_modules", "dist-packages")


def find_skill_script(name):
    """返回 技能配置/*/scripts/<name> 的全路径列表（仅 scripts/ 子目录·即正统机制脚本家）。"""
    hits = []
    for root, _, files in os.walk(SKILL):
        if os.path.basename(root) == "scripts" and name in files:
            hits.append(os.path.join(root, name))
    return [h for h in hits if not any(m in h for m in _LIB_MARKERS)]


def main():
    if not os.path.isdir(DEV):
        print("[redundant_script_guard] 开发工具/ 不存在，跳过")
        return 0

    rogue = []
    for f in sorted(os.listdir(DEV)):
        if not f.endswith(".py") or f in GENERIC:
            continue
        hits = find_skill_script(f)
        if hits:
            rogue.append((f, hits))

    if rogue:
        print("🔴 RED: 检测到 开发工具/ 与 技能配置/*/scripts/ 同名系统机制脚本（野副本）：")
        for f, hits in rogue:
            for h in hits:
                print(f"   {f}  ⟷  {h}")
        print(f"[redundant_script_guard] 命中 {len(rogue)} 处 · 须 trash 清除后复查（铁律-005·非 rm）")
        return 1

    print("🟢 GREEN: 开发工具/ 无与 技能配置/*/scripts/ 同名的系统机制脚本野副本")
    return 0


if __name__ == "__main__":
    sys.exit(main())
