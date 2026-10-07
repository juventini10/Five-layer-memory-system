#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
format_contract.py — SSOT 格式契约抽取（路由注入与停止守卫共用的单一真源）

职责：从某技能的 SSOT SKILL.md 抽取“回复/输出格式”相关段落，供
- route_inject_prompt.py：在 Skill 触发时把活源格式契约注入 prompt（消除陈旧缓存/历史渲染）
- reply_format_guard.py：⛔已退役（2026-08-13 停用·实体已删·D25）——原用于停止时按同一活源做软校验；现由 SOUL 回复容器承载

抽取策略（数据驱动，非手编例外）：
- 遍历所有 Markdown 标题行，取「标题文本命中 FORMAT_INCLUDE 且未命中 FORMAT_EXCLUDE」
  的整段（直到下一个标题行或文件尾）。
- 各 Skill 的“回复格式”段标题命名不统一（输出格式 / 返回格式 / 签名规则 / 结论块 / 呈现 / …），
  故用关键词集覆盖；新增 Skill 只要其格式段标题含任一关键词即自动纳入，无需改本模块。
- 失败一律返回 ""（优雅降级，绝不抛错阻断主流程）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re

# SSOT 基址：技能配置目录（与各 Skill 的 SKILL.md 唯一真源对齐）
BASE = os.path.expanduser("[记忆共享中心]/技能配置")

# 命中即纳入抽取的标题关键词（覆盖各 Skill 不同命名习惯）
FORMAT_INCLUDE = [
    "回复格式", "输出格式", "返回格式", "输出规范", "回复规范",
    "呈现", "签名规则", "签名格式", "签名锁", "结论块", "结论反馈",
    "格式规范", "格式要求", "输出要求", "模板锁", "共用模板", "结果",
]
# 命中即排除的标题关键词（历史/变体/非回复格式类）
FORMAT_EXCLUDE = [
    "旧格式", "旧版", "变体声明", "命名规范", "自检清单", "历史", "判断标准",
]
# 注入长度上限，避免撑爆 prompt
MAX_CONTRACT_CHARS = 2500


def _heading_level(line):
    m = re.match(r'^(#{1,6})\s+', line)
    return len(m.group(1)) if m else 0


def _iter_sections(lines):
    """yield (标题文本, 段起始行号, 段结束行号) —— 段含标题行及其所有嵌套子段，
    止于下一个「层级 ≤ 当前层级」的标题或文件尾（保证 ## 段吞掉其 ### 子段，不丢正文）。"""
    heads = [(i, _heading_level(lines[i]))
             for i, ln in enumerate(lines) if re.match(r'^#{1,6}\s+', ln)]
    for k, (hi, lvl) in enumerate(heads):
        htext = lines[hi].lstrip('#').strip()
        end = len(lines)
        for j in range(k + 1, len(heads)):
            if heads[j][1] <= lvl:
                end = heads[j][0]
                break
        yield htext, hi, end


def extract_format_contract(skill):
    """抽取某技能的 SSOT 格式契约文本；无文件/无命中返回 ''。"""
    path = os.path.join(BASE, skill, "SKILL.md")
    if not os.path.isfile(path):
        return ""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception:
        return ""
    lines = txt.split("\n")
    out = []
    for htext, s, e in _iter_sections(lines):
        if any(ex in htext for ex in FORMAT_EXCLUDE):
            continue
        if not any(inc in htext for inc in FORMAT_INCLUDE):
            continue
        out.append("\n".join(lines[s:e]).strip())
    joined = "\n\n".join(out)
    if not joined.strip():
        return ""
    if len(joined) > MAX_CONTRACT_CHARS:
        joined = joined[:MAX_CONTRACT_CHARS] + "\n…（已截断，完整契约见 SSOT SKILL.md）"
    return joined


if __name__ == "__main__":
    import sys
    skill = sys.argv[1] if len(sys.argv) > 1 else "triwich"
    print(extract_format_contract(skill))
