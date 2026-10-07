#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""design_family_guard.py v0.1 — 设计哲学家族文档一致性巡检（只读·只记录不拦截）

背景（2026-08-21 第一性原理·同步义务必配机械校验）：
  记忆蓝图/04_系统文件设计/ 下各设计哲学目录的 INDEX/进度看板 是人工维护点，
  会漂（实证：知识库看板 frontmatter v1.13 vs 变更记录 1.14；脚本哲学看板曾 v1.2 vs v1.11）。
  本守卫把两类「同文件内一致性」机械化——跨文件版本比对语义不可靠（不同文档版本独立），不做。

检查项：
  ① 看板自洽：目录有 03-进度看板.md → frontmatter version == 变更记录（行首 `- vX.Y（`）最大条目
  ② INDEX 引用存在：目录有 INDEX.md → 导航表反引号内相对路径（.md 文件或目录）必须存在

设计原则（Hook 三纪律）：
  - 只读；失败默认放行 exit 0；--strict 时漂移 exit 1（人工调用用）
  - 输出到 stdout + 追加日志
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]/脚本中心")
LOG = os.path.expanduser("[记忆共享中心]/脚本中心/logs/design_family_guard.log")


def log_line(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except Exception:
        pass


def frontmatter_version(path):
    """取 frontmatter version: vX.Y(.Z) → (X, Y, Z)。无版本返回 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(2000)
    except Exception:
        return None
    m = re.search(r"^version:\s*v([0-9]+)\.([0-9]+)(?:\.([0-9]+))?", head, re.M)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def parse_board(board_path):
    """返回 (frontmatter_version_tuple, max_change_entry_tuple)。"""
    fm = frontmatter_version(board_path)
    try:
        with open(board_path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return fm, None
    entries = []
    for m in re.finditer(r"^- v([0-9]+)\.([0-9]+)(?:\.([0-9]+))?（", text, re.M):
        entries.append((int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)))
    return fm, (max(entries) if entries else None)


def parse_index_refs(index_path):
    """导航表反引号内「当前目录文档家族」引用——数字前缀 + 行级外部基准排除。

    收：`0X-*.md` / `0X-*/` 且所在行不含外部基准词。
    行级判定（2026-08-21 实测）：`待完成工作/Skill开发/学习引擎/08-...`、`09-...` 这类
    行内混外部路径+简写（同一路径省前缀），机器无法靠引用本身区分简写/孤悬——
    但整行含外部基准词即说明该行是外部导航区，整行跳过。只守"当前目录家族"行。
    """
    external_markers = ("待完成工作/", "~/", "记忆蓝图/", "自定义层/",
                        "开发工具/", "记忆系统架构/", "00_", "02_", "03_", "04_")
    refs = []
    try:
        with open(index_path, encoding="utf-8") as f:
            for line in f:
                if any(mk in line for mk in external_markers):
                    continue  # 外部导航行，整行跳过
                for m in re.finditer(r"`([^`]+)`", line):
                    raw = m.group(1).strip()
                    path_part = re.split(r"[ §]", raw)[0]
                    if not path_part:
                        continue
                    if not (path_part.endswith(".md") or path_part.endswith("/")):
                        continue
                    if not re.match(r"^\d+-", path_part):
                        continue
                    refs.append(path_part)
    except Exception:
        pass
    return refs


def main():
    strict = "--strict" in sys.argv
    issues = []
    if not os.path.isdir(BASE):
        log_line(f"[design_family_guard] BASE 不存在 {BASE} → exit0 放行")
        print(f"设计哲学家族文档一致性巡检：BASE 不存在 {BASE}")
        return 0

    print("设计哲学家族文档一致性巡检（INDEX 引用 / 看板自洽）：")
    for d in sorted(os.listdir(BASE)):
        dpath = os.path.join(BASE, d)
        if not os.path.isdir(dpath) or d.startswith("."):
            continue
        # ① 看板自洽
        board = os.path.join(dpath, "03-进度看板.md")
        if os.path.exists(board):
            fm, mx = parse_board(board)
            if fm is None:
                issues.append((d, "看板", "frontmatter 无 version 字段"))
            elif mx is None:
                issues.append((d, "看板", "变更记录无版本条目可比对"))
            elif fm != mx:
                fmt = f"v{fm[0]}.{fm[1]}" + (f".{fm[2]}" if fm[2] else "")
                mxt = f"v{mx[0]}.{mx[1]}" + (f".{mx[2]}" if mx[2] else "")
                issues.append((d, "看板", f"frontmatter {fmt} ≠ 变更记录最大 {mxt}"))
        # ② INDEX 当前目录引用存在（单基准·只查当前目录自洽引用）
        index = os.path.join(dpath, "INDEX.md")
        if os.path.exists(index):
            for ref in parse_index_refs(index):
                if ref.endswith("/"):
                    hit = os.path.isdir(os.path.join(dpath, ref.rstrip("/")))
                else:
                    hit = os.path.exists(os.path.join(dpath, ref))
                if not hit:
                    issues.append((d, "INDEX", f"当前目录引用缺失: {ref}"))

    if not issues:
        print("✅ 无漂移：各目录 INDEX 引用存在 + 看板 frontmatter/变更记录自洽")
        log_line("[design_family_guard] OK 无漂移")
        return 0

    for d, kind, detail in issues:
        print(f"⚠️ [{d}] {kind}: {detail}")
        log_line(f"[design_family_guard:DRIFT] {d} {kind} {detail}")
    print(f"结论: {len(issues)} 处漂移（只读告警·不拦截）")
    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
