#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
regen_ailib_index.py — AI学习库 INDEX.md 编译产物生成器（D-F11 精神·S017 自锁落地）
职责: 从 AI学习库 卡片 frontmatter 全量重建 INDEX.md（frontmatter+说明块保留，表格体重建）。
      早期卡缺字段从旧 INDEX 历史行补（key 归一: #S005 == 立场卡#S005）。
      ⛔只读卡片+只写 INDEX.md；卡片 frontmatter 零改动（派生数据重建·永不手写）。
用法: python3 regen_ailib_index.py
"""
import sys, os, re, glob, subprocess
from datetime import datetime

from _paths import AILIB_DIR, INSTALLED

INDEX_FILE = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None
LINT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lint_collision_card.py")

# 2026-09-30 终检根治（数字分身完整版 G2·分身链路「落卡」步）：
#   新装端用户无 INDEX.md ⇒ 原逻辑走 `old=""` → 结构定位失败 rc=1 ＝**首张落卡必失败**
#   （沙箱实证：`⚠️ 无卡片可索引` / `❌ 无法定位旧 INDEX 结构`）。作者机有历史 INDEX
#   故从未暴露 ⇒ 典型「作者态 vs 端用户态口径分离」缺口。
#   改法：**缺件自愈**——无 INDEX.md 时以本骨架为基底，后续走同一条重建管道（幂等）。
#   骨架结构必须满足下方正则 `^(---\n.*?\n---\n)(.*?)(\n\| 卡号)`（frontmatter + 说明块 + 表头）。
_DEFAULT_INDEX_SKELETON = """---
title: AI学习库索引
type: index
note: 编译产物·由 regen_ailib_index.py 全量重建
---

> 本文件为**编译产物**（AI学习库卡片 frontmatter 的机械聚合），⛔DO NOT 手工编辑；
> 增删改卡后重跑 `regen_ailib_index.py` 即重建。

| 卡号 | 主题 | 类型 | 领域 | reading_status | 日期 | 来源 |
|------|------|------|------|:---:|------|------|
"""

def parse_fm(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm

def norm_cid(c):
    """归一卡号：#S005 / 立场卡#S005 → 立场卡#S005（表格 key 统一）"""
    return c if c.startswith(("立场卡", "技能卡")) else ("立场卡" + c if c.startswith("#S") else "技能卡" + c)

def parse_history(text):
    hist = {}
    for line in text.split("\n"):
        if not line.startswith("| #") and not line.startswith("| 立场卡") and not line.startswith("| 技能卡"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        cid = norm_cid(cells[0])
        if len(cells) == 6:
            hist[cid] = {"src": cells[2], "evid": cells[3], "date": cells[5]}
        elif len(cells) == 7:
            hist[cid] = {"src": cells[6], "evid": "", "date": cells[5]}
    return hist

def main():
    # 管道闸（gate A·2026-08-07 立·根除静默失败）：重建 INDEX 前强制 lint --strict
    # 任何含碰撞来源的卡不合规（HARD/SOFT 任一）→ 非零退出拒建，S054 类事故结构上不可能
    if not INSTALLED:
        print("❌ 未安装态：请先完成安装（需 [记忆共享中心]/脚本中心 布局）")
        return 1
    if not os.path.exists(LINT_PATH):
        print("ℹ️ lint_collision_card.py 不在（可选件）——跳过 lint 闸直接重建")
    lint = subprocess.run([sys.executable, LINT_PATH, "--strict"], capture_output=True, text=True) if os.path.exists(LINT_PATH) else None
    if lint is not None and lint.stdout:
        print(lint.stdout, end="")
    if lint is not None and lint.returncode != 0:
        raise SystemExit(f"❌ 碰撞卡 lint 未过（exit={lint.returncode}）——拒绝重建 INDEX。先按上面 lint 报错修卡，再重跑 regen。")
    old = open(INDEX_FILE, encoding="utf-8").read() if INDEX_FILE and os.path.exists(INDEX_FILE) else ""
    # 2026-09-30 缺件自愈（见 _DEFAULT_INDEX_SKELETON 注释）：新装无 INDEX.md 时以骨架为基底，
    # ⛔不因缺件而 rc=1（那会让端用户「首张落卡」永久失败）。
    if not old:
        old = _DEFAULT_INDEX_SKELETON
    hist = parse_history(old)
    cards = []
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "*.md"))):
        if os.path.basename(p) == "INDEX.md":
            continue
        fm = parse_fm(open(p, encoding="utf-8").read())
        cid = fm.get("card_id", "")
        if not cid:
            continue
        # 机械断言（S017自锁·2026-08-06）：文件名 MUST 以 card_id 开头——命名漂移零容忍
        fname = os.path.basename(p).replace(".md", "")
        if not fname.startswith(cid):
            raise SystemExit(f"❌ 命名漂移: 文件名 '{fname}' 不以 card_id '{cid}' 开头——"
                             f"按 card-schema 重命名为 '{cid}-{{主题}}.md'")
        topic = fm.get("topic", "?")
        typ = fm.get("type", "?")
        dom = fm.get("领域分诊", "?")
        status = fm.get("reading_status", "L1")
        date = fm.get("date", "")
        src = (fm.get("碰撞来源") or fm.get("触发残差") or fm.get("触发来源") or "").strip()
        h = hist.get(cid, {})
        if not date: date = h.get("date", "")
        if not src: src = h.get("src", "")
        cards.append(f"| {cid} | {topic} | {typ} | {dom} | {status} | {date} | {src} |")
    if not cards:
        print("⚠️ 无卡片可索引"); return 1
    cards.sort(key=lambda r: r.split("|")[1].strip())
    header = "| 卡号 | 主题 | 类型 | 领域 | reading_status | 日期 | 来源 |"
    sep = "|------|------|------|------|:---:|------|------|"
    body = "\n".join(cards)

    # 提取旧文件 frontmatter（--- 到 ---）与首个表格前的说明块
    m = re.match(r"^(---\n.*?\n---\n)(.*?)(\n\| 卡号)", old, re.S)
    if not m:
        print("❌ 无法定位旧 INDEX 结构"); return 1
    frontmatter, pre_notes = m.group(1), m.group(2)
    # 提取表格后说明块（留存机制等）：从第一个 `---` 分隔（表格后）到文件尾
    # post 说明块：留存机制段，到下一个表格行或文件尾截断（防抓进旧表格）
    post_match = re.search(r"\n---\n(> \*\*留存机制[\s\S]*?)(?=\n\| #|\n\| 立场卡|\n\| 技能卡|\n\| 卡号|$)", old)
    post_notes = post_match.group(1).rstrip() if post_match else ""

    # 严格幂等：frontmatter/pre_notes/post_notes 全部 strip 归一，空白不参与状态
    new = (frontmatter.rstrip() + "\n\n" + pre_notes.strip() + "\n\n" +
           header + "\n" + sep + "\n" + body)
    if post_notes:
        new += "\n\n---\n" + post_notes.strip()
    new = new.rstrip() + "\n"
    if INDEX_FILE:
        open(INDEX_FILE, "w", encoding="utf-8").write(new)
    else:
        print("❌ 未安装态·无法写 INDEX"); return 1
    print(f"✅ INDEX.md 重建完成: {len(cards)} 张卡 | {datetime.now().strftime('%H:%M')}")

    # 向量化挂接（第二刀·2026-08-07）：INDEX 重建后顺带增量检查知识向量库（零新增流水线）
    # build_kb_vectors.py 无变化时秒级返回（md5 复用不加载模型），有新卡才编码；失败不影响 INDEX 结果
    vec_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_kb_vectors.py")
    try:
        if os.path.exists(vec_script):
            subprocess.run([sys.executable, vec_script], check=False)
    except Exception as e:
        print(f"⚠️ 向量库增量检查失败（不影响 INDEX 结果）: {e}")

    # reading_status 派生挂接（质证回写管道根治·2026-08-17）：
    # derive_reading_status.py 从卡内质证事件记录机械派生 L2，写 INDEX status 列
    # （与 INDEX 编译同构；无事件零变更，失败不影响 INDEX 结构结果）
    derive_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "derive_reading_status.py")
    try:
        subprocess.run([sys.executable, derive_script], check=False)
    except Exception as e:
        print(f"⚠️ reading_status 派生失败（不影响 INDEX 结构结果）: {e}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
