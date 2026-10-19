#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
concept_projection.py — 概念卡下游收窄派生段生成器（生产脚本·非 lint 管道）
数据来源: [记忆共享中心]/知识库/AI学习库/INDEX.md 的「碰撞来源」列（已有数据·零新建）
产出: 向概念卡([记忆共享中心]/知识库/概念卡/C-XXX*.md)正文末尾
      注入标记包裹的「下游收窄」派生段。仅物化已有数据，永不手工维护。
设计依据: 概念卡演化-L3最优方案.md §四（projection 层·Event Sourcing 映射）
硬边界: 只做指针聚合（照抄 INDEX 文本），绝不做语义合成（不自动改写 definition）
用法:
  python3 concept_projection.py --dry-run     # 只打印计划，不改文件
  python3 concept_projection.py               # 全量重写所有概念卡的派生段
  python3 concept_projection.py --purge       # 删除全部派生段（回滚到逐字节原状）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, glob
from datetime import datetime

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, AILIB_DIR, CONCEPTS_DIR
INDEX = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None
CONCEPT_DIR = CONCEPTS_DIR
PROJ_RE = re.compile(r"<!-- PROJECTION:AUTO-GENERATED.*?<!-- /PROJECTION -->", re.S)
TOP_N = 5  # 防概念卡退化为目录页（§4.4 上限）


def parse_index():
    """抽 INDEX.md 中带碰撞来源列的立场卡行 → [(cid, topic, concept_a, concept_b)]"""
    rows = []
    for line in open(INDEX, encoding="utf-8"):
        if not (line.startswith("| 立场卡") or line.startswith("| 技能卡")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        src = cells[-1]  # 碰撞来源列（末列）
        m = re.search(r"\[(C-[0-9]+)\s*[×x]\s*(C-[0-9]+)\]", src)
        if m:
            rows.append((cells[0], cells[1], m.group(1), m.group(2)))
            continue
        # 含 "C-X × C-Y" 形态却缺方括号 → 不合规，fail-fast（堵静默丢数据）
        # S054-S063 事故类：缺方括号会让派生段静默缺失且零报错
        if re.search(r"C-[0-9]+\s*[×x]\s*C-[0-9]+", src):
            raise SystemExit(
                f"❌ 碰撞来源格式不合规（缺方括号）：{src.strip()!r} @ {cells[0]}\n"
                f"   正确格式：\"[C-XXX × C-YYY]\"（必须带方括号）"
            )
        # 其余（空/非碰撞占位文本）→ 非碰撞卡，静默跳过
    return rows


def build_inverted(rows):
    """concept_id → [(立场卡cid, topic), ...] 倒排"""
    inv = {}
    for cid, topic, a, b in rows:
        for c in (a, b):
            inv.setdefault(c, []).append((cid, topic))
    return inv


def concept_file(cid):
    fs = glob.glob(os.path.join(CONCEPT_DIR, f"{cid}-*.md"))
    return fs[0] if fs else None


def render_block(insights, date):
    lines = [
        "<!-- PROJECTION:AUTO-GENERATED — 勿手改，由 concept_projection.py 全量重写 -->",
        f"## 下游收窄（自动派生 · {date}）",
        "",
        f"本概念已被 {len(insights)} 张洞见卡收窄：",
        "",
    ]
    for cid, topic in insights[:TOP_N]:
        lines.append(f"- **{cid}** · {topic}")
    if len(insights) > TOP_N:
        lines.append(f"- （另有 {len(insights) - TOP_N} 条，见 INDEX.md）")
    lines += [
        "",
        "> ⚠️ 上方 definition 是源的摘要，未包含以上约束。使用前请一并阅读。",
        "<!-- /PROJECTION -->",
    ]
    return "\n".join(lines)


def main():
    if not INSTALLED or not INDEX:
        print("未安装态（记忆共享中心自推导失败）——跳过投影")
        return
    dry = "--dry-run" in sys.argv
    purge = "--purge" in sys.argv
    date = datetime.now().strftime("%Y-%m-%d")
    rows = parse_index()
    inv = build_inverted(rows)
    print(f"解析到 {len(rows)} 条碰撞来源，涉及 {len(inv)} 张概念卡")
    for cid, insights in sorted(inv.items()):
        fp = concept_file(cid)
        if not fp:
            print(f"  [跳过] {cid} 概念卡文件未找到")
            continue
        txt = open(fp, encoding="utf-8").read()
        stripped = PROJ_RE.sub("", txt).rstrip() + "\n"
        if purge:
            if dry:
                print(f"[dry-purge] {cid}: 将删除派生段")
            else:
                open(fp, "w", encoding="utf-8").write(stripped)
                print(f"[purge] {cid}")
            continue
        block = render_block(insights, date)
        if dry:
            print(f"[dry] {cid} ({os.path.basename(fp)}): +{len(insights)} 条下游")
            for bl in block.split("\n"):
                print("    " + bl)
        else:
            open(fp, "w", encoding="utf-8").write(stripped + "\n" + block + "\n")
            print(f"[write] {cid}: 注入 {len(insights)} 条下游")


if __name__ == "__main__":
    main()
