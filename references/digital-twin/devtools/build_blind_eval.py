#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_blind_eval.py — Step 2 影子模式评测·盲题构造器
====================================================
职责：从 AI学习库 SSOT 抽样 40 张立场卡 → 构造盲题（遮盖你的最终裁决）
     → 落盘 step2-blind-items.md（该文件不含任何结论段，供分身盲判用）

防泄漏设计（见 step2-eval-protocol.md §二）：
- 盲题只含：card_id / date / 领域分诊 / 碰撞来源编号 / 主要矛盾段 / 权威A 行
- 遮盖：topic/标题 / 立场段 / 推理B / 反例C / steelman / 让步 / 红线 / 旧认知 / 自测题
- 硬排除：S812 S813（已被会话完整读过）
- 种子固定 20260821，可复现

用法：python3 build_blind_eval.py
产出：steps/step2-blind-items.md + stdout 抽样摘要
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import random
import re
from pathlib import Path

SEED = 20260821
KB_DIR = Path.home() / "[日记仓库]" / "2-知识库" / "09-AI学习库"  # 2026-10-13 C''波次2迁移后路径同步·顺带根治Path.home()重复bug
MAP_FILE = Path('[记忆共享中心]') / "数字分身" / "立场卡通读档案" / "立场卡全量地图.md"
OUT_FILE = Path('[记忆共享中心]') / "数字分身" / "steps" / "step2-blind-items.md"

# 规格书 v0.1 已引用的立场卡（in-spec 池）
SPEC_CITED = [1, 3, 4, 5, 6, 7, 74, 84, 114, 127, 132, 179, 180, 650, 771, 810, 811, 812, 813, 814]
# 已被会话完整读过 → 硬排除
READ_EXCLUDE = {812, 813}
READ_EXCLUDE_KEYS = {"S812", "S813"}
IN_SPEC_POOL = [s for s in SPEC_CITED if s not in READ_EXCLUDE]

N_IN_SPEC = 10
N_OUT_SPEC = 30


def load_topic_map() -> dict:
    """从全量地图解析 card_id → 主题组"""
    m = {}
    if not MAP_FILE.exists():
        return m
    for line in MAP_FILE.read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) >= 3 and re.fullmatch(r"S\d+", parts[0]):
            sid = int(parts[0][1:])
            if sid not in m:  # 地图有重复行（已知数据瑕疵），取首条
                m[sid] = parts[2]
    return m


def parse_card(path: Path) -> dict:
    """解析单张立场卡：frontmatter + 主要矛盾段 + 权威A 行"""
    text = path.read_text(encoding="utf-8")
    meta = {}
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')

    body = text[fm.end():] if fm else text

    # 主要矛盾段：兼容 **主要矛盾** / ## 主要矛盾 / ## **主要矛盾** 三种写法
    scene = ""
    m = re.search(
        r"(?:^|\n)\s*(?:#{1,6}\s*)?\*{0,2}主要矛盾\*{0,2}[^\n：:]*[:：]?\s*(.*?)"
        r"(?=\n\s*#{1,6}[\s*]|\n\s*\*\*|\n-{3,}|\Z)",
        body, re.S,
    )
    if m:
        scene = m.group(1).strip()
        scene = re.sub(r"\n-{3,}\s*$", "", scene).strip()  # 去掉段尾 --- 分隔线

    # 权威A 行（依现场原话/文献基准，不含结论）
    authority = ""
    ma = re.search(r"^[-•]?\s*\*{0,2}权威A[^：:]*[:：](.*)$", body, re.M)
    if ma:
        authority = ma.group(1).strip()

    return {"meta": meta, "scene": scene, "authority": authority}


def main():
    rng = random.Random(SEED)
    topic_map = load_topic_map()

    # 1. 加载全部立场卡
    #    历史缺陷（2026-08-21 发现并于当日修复）：曾有两张卡共用 id S810，
    #    检索效用卡已改号 S815（SSOT 已归正）。以下撞号处理保留为防御层，防复发。
    cards = {}
    for p in sorted(KB_DIR.glob("立场卡#S*.md")):
        m = re.search(r"#S(\d+)", p.name)
        if not m:
            continue
        sid = int(m.group(1))
        key = f"S{sid:03d}"
        if key in cards:  # 撞号：协作硬规则卡优先占主 id，另一张加 -B
            if "协作硬规则" in p.name:
                cards[key + "-B"] = cards[key]
                cards[key] = p
            else:
                cards[key + "-B"] = p
        else:
            cards[key] = p
    print(f"[盘点] AI学习库立场卡总数: {len(cards)}（含 S810-B 撞号拆分）")

    # 2. in-spec 抽样
    pool_in = [f"S{s:03d}" for s in IN_SPEC_POOL if f"S{s:03d}" in cards]
    sample_in = sorted(rng.sample(pool_in, N_IN_SPEC))
    print(f"[in-spec] 池={len(pool_in)} 抽={N_IN_SPEC}: {sample_in}")

    # 3. out-of-spec 分层抽样（按主题组比例，每组至少1张）
    exclude = {f"S{s:03d}" for s in SPEC_CITED} | READ_EXCLUDE_KEYS
    out_pool = {}
    for key, p in cards.items():
        if key in exclude:
            continue
        sid_num = int(re.search(r"\d+", key).group())
        grp = topic_map.get(sid_num, "其他/跨域")
        out_pool.setdefault(grp, []).append(key)

    total = sum(len(v) for v in out_pool.values())
    print(f"[out-of-spec] 池总量={total} 主题组={len(out_pool)}")

    # 比例分配 + 保底1张 + 凑满 N_OUT_SPEC
    alloc = {}
    for grp, ids in out_pool.items():
        alloc[grp] = max(1, round(N_OUT_SPEC * len(ids) / total))
    diff = N_OUT_SPEC - sum(alloc.values())
    order = sorted(out_pool, key=lambda g: len(out_pool[g]), reverse=True)
    i = 0
    while diff != 0 and order:
        g = order[i % len(order)]
        if diff > 0:
            alloc[g] += 1
            diff -= 1
        elif alloc[g] > 1:
            alloc[g] -= 1
            diff += 1
        i += 1
    # 修正超出组容量的情况
    for g in alloc:
        alloc[g] = min(alloc[g], len(out_pool[g]))

    sample_out = []
    for grp, n in alloc.items():
        sample_out += [(key, grp) for key in rng.sample(out_pool[grp], n)]
    sample_out.sort(key=lambda x: x[0])
    print(f"[out-of-spec] 实际抽={len(sample_out)} 分配={ {g: alloc[g] for g in order} }")

    # 4. 构造盲题文件
    lines = [
        "# Step 2 盲题集（40条）",
        "",
        "> ⚠️ 本文件只含场景+证据，不含你的裁决。盲判完成前禁止对照原卡。",
        "> 若【场景】末尾仍残留结论句（碰撞卡通病），盲判前先人工剥离并在原位标注 [已剥离]。",
        "> 种子=20260821 · 构造=build_blind_eval.py · 2026-08-21",
        "",
        "---",
        "",
        "# 第一部分 · 规格书内（in-spec · 记忆/保真测试）",
        "",
    ]

    def emit(key: str, tag: str, grp: str = ""):
        d = parse_card(cards[key])
        meta = d["meta"]
        lines.append(f"## {tag} · {key}")
        lines.append("")
        lines.append(f"- 日期: {meta.get('date', '?')}")
        lines.append(f"- 领域分诊: {meta.get('领域分诊', '?')}")
        if meta.get("碰撞来源"):
            lines.append(f"- 碰撞来源: {meta.get('碰撞来源')}")
        if grp:
            lines.append(f"- 主题组(分层用,非内容): {grp}")
        lines.append("")
        lines.append("**【场景】**")
        lines.append("")
        lines.append(d["scene"] if d["scene"] else "（原卡无主要矛盾段）")
        lines.append("")
        lines.append("**【现场证据】**")
        lines.append("")
        if d["authority"]:
            lines.append(d["authority"])
        else:
            lines.append("（无权威A现场证据，仅场景可凭）")
        lines.append("")
        lines.append("---")
        lines.append("")

    for key in sample_in:
        emit(key, "IN")
    lines.append("# 第二部分 · 规格书外（out-of-spec · 泛化测试）")
    lines.append("")
    for key, grp in sample_out:
        emit(key, "OUT", grp)

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[落盘] {OUT_FILE} ({OUT_FILE.stat().st_size} bytes)")
    print(f"[校验] in={len(sample_in)} out={len(sample_out)} 合计={len(sample_in)+len(sample_out)}")


if __name__ == "__main__":
    main()
