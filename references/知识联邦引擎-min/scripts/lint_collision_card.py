#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_collision_card.py — 立场卡（碰撞产出）schema 合规校验（生成即检 gate）
设计依据: 第一性原理 gate 方案 B（good-good-study · 2026-08-07）
双层判定:
  HARD（必拦截·会导致派生层损坏）:
    1. 碰撞来源含 "C-X × C-Y" 形态却缺方括号 → 派生段静默缺失（S054 事故类）
    2. card_id 缺 `#` 前缀 → regen/index 断言失败
    3. 文件名不以 card_id 开头 → 命名漂移
  SOFT（批次模式升 HARD·全库模式仅报告·属历史债）:
    4. 必需字段齐全（card_id/topic/type/碰撞来源/date）
    5. 正文 7 段齐全（当前 schema）
模式:
  - 传文件参数 = 批次模式：SOFT 升 HARD，严格卡本次生成
  - 不传参数   = 全库审计：仅 HARD 拦截，SOFT 打印为 ⚠️ 历史债，不阻塞
退出码: 0=无 HARD 违规；1=存在 HARD 违规
用法:
  python3 lint_collision_card.py 立场卡#S054*.md 立场卡#S055*.md   # 批次模式（gate）
  python3 lint_collision_card.py                                    # 全库审计
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, glob

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, AILIB_DIR
LIB = AILIB_DIR
COLLISION_RE = re.compile(r"\[(C-[0-9]+)\s*[×x]\s*(C-[0-9]+)\]")      # 当前schema: C-XXX 方括号
CROSS_TYPE_RE = re.compile(r"\[(BP-[^\]]+?)\s*[×x]\s*(S[0-9]+)\]")   # 跨类型碰撞: 蓝图索引卡×立场卡（v1.1新增·2026-09-08）
MULTI_SOURCE_RE = re.compile(r"\[[^\]]+?\s*[×x]\s*[^\]]+?(\s*[×x]\s*[^\]]+?)+\]")  # 多源综合卡: ≥3个来源（v1.1新增·2026-09-08）
MALFORMED_RE = re.compile(r"C-[0-9]+\s*[×x]\s*C-[0-9]+")            # 含 C- 形态（可能缺方括号）
BRACKETED_ANY_RE = re.compile(r"\[.+?\s*[×x]\s*.+?\]")             # 任意方括号对（含 legacy 名）
REQUIRED_SECTIONS = [
    "**主要矛盾", "**立场", "**依据链**", "**顶住红线",
    "**推翻",  # 兼容两种头：**推翻了我哪个旧认知** / **推翻的旧认知**（变体误报2026-08-07）
    "**碰撞后我会做的三件事", "**自测题",
]
REQUIRED_FIELDS = ["card_id", "topic", "type", "碰撞来源", "date"]


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip("\n")
    body = text[end + 4:]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def lint_file(path, batch_mode):
    text = open(path, encoding="utf-8").read()
    fm, body = parse_frontmatter(text)
    hard, soft = [], []
    cid = fm.get("card_id", "")
    src = fm.get("碰撞来源", "")
    src_val = src.strip().strip('"').strip("'")

    # HARD 1: 含 C- 形态却缺方括号 → 派生层静默缺失（事故类）
    if src_val and MALFORMED_RE.search(src_val) and not COLLISION_RE.match(src_val):
        hard.append(f"碰撞来源格式不合规（含 C-X×C-Y 却缺方括号）：{src!r}")
    # HARD 2/3: card_id 前缀 + 文件名一致
    if cid and not re.match(r"^(立场卡|技能卡)#", cid):
        hard.append(f"card_id 缺 `#` 前缀：{cid!r}")
    stem = os.path.basename(path)[:-3]
    if cid and not stem.startswith(cid):
        hard.append(f"文件名不以 card_id 开头：文件={stem!r} / card_id={cid!r}")

    # SOFT: 字段 + 正文段（legacy 债·批次模式升 HARD）
    for f in REQUIRED_FIELDS:
        if f not in fm or not fm[f].strip():
            soft.append(f"缺必需字段 `{f}`")
    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            soft.append(f"正文缺段：{sec}")
    # legacy 名格式提示（不报错）——仅当碰撞来源含C-XXX编号但格式不标准时触发；
    # 不含C-XXX的非概念卡碰撞（Skill×立场卡/会话×立场卡/蓝图×立场卡/多源综合）为合法格式，不警告
    has_c_id = re.search(r"C-[0-9]+", src_val)
    if src_val and BRACKETED_ANY_RE.match(src_val) and not COLLISION_RE.match(src_val) and has_c_id:
        soft.append(f"legacy 名格式碰撞来源（非 C-XXX 编号，派生层不投影）：{src!r}")

    if batch_mode:
        return hard + soft, []   # 批次模式：全部升 HARD
    return hard, soft            # 全库模式：分层


def main():
    strict = "--strict" in sys.argv
    files = [a for a in sys.argv[1:] if a != "--strict"]
    batch_mode = bool(files) or strict  # --strict: 全库也升 HARD（管道闸用）
    if not files:
        if LIB is None:
            print("未安装态（_paths 自推导失败）——全库审计跳过；批次模式请显式传卡路径")
            raise SystemExit(0)
        files = glob.glob(os.path.join(LIB, "*.md"))
    targets = []
    for fp in files:
        if not os.path.isfile(fp):
            continue
        text = open(fp, encoding="utf-8").read()
        fm, _ = parse_frontmatter(text)
        if "碰撞来源" in fm:
            targets.append(fp)
    if not targets:
        print("无含碰撞来源的卡，跳过")
        return
    all_hard, all_soft = [], []
    all_warn = []  # 相关卡软警告（v1.1.0 任务书#10：新卡空=警告不阻断·童灵验收兜底）
    explicit_batch = bool(files) and not strict  # 仅"显式传文件=本次新卡"才检查；全库/strict存量不查（存量选填·v1.2.0起强制）
    for fp in targets:
        h, s = lint_file(fp, batch_mode)
        if h:
            all_hard.append((os.path.basename(fp), h))
        if s:
            all_soft.append((os.path.basename(fp), s))
        if explicit_batch:
            fm2, _ = parse_frontmatter(open(fp, encoding="utf-8").read())
            if fm2.get("card_id", "").startswith("立场卡") and not fm2.get("相关卡", "").strip():
                all_warn.append(os.path.basename(fp))

    mode = "strict(全库)" if strict else ("批次(严格)" if batch_mode else "全库(审计)")
    if all_warn:
        print(f"💡 [相关卡软警告·不阻断] {len(all_warn)} 张新卡未填「相关卡」字段（去重/融合第一道防线缺线索·童灵验收兜底）：")
        for name in all_warn:
            print(f"  [{name}]")
    if all_soft:
        print(f"⚠️ [{mode}] {len(all_soft)} 张 SOFT 历史债（不阻塞）：")
        for name, errs in all_soft:
            print(f"  [{name}]")
            for e in errs:
                print(f"    - {e}")
    if all_hard:
        print(f"\n❌ [{mode}] {len(all_hard)} 张 HARD 不合规：")
        for name, errs in all_hard:
            print(f"  [{name}]")
            for e in errs:
                print(f"    - {e}")
        raise SystemExit(1)
    print(f"✅ [{mode}] {len(targets)} 张碰撞卡无 HARD 违规")


if __name__ == "__main__":
    main()
