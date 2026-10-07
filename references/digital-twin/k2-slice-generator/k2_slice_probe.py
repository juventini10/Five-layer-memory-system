#!/usr/bin/env python3
"""K2 切片试切探针（v0.1·2026-08-24）——D3 定稿的数据前提。

职责：从童灵规格书按六层切段，实测各层体积，计算恒驻最小核候选与
域切片候选的体积，输出对比数据——用数据定双层结构边界，不用直觉。

幂等可重跑：只读规格书，无副作用。对齐引擎验收四问。

用法:
  python3 k2_slice_probe.py [规格书路径] [--soul 基准文件]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys

SPEC_DEFAULT = os.path.expanduser("[记忆共享中心]/数字分身/童灵·人格规格书.md")
SOUL_DEFAULT = os.path.expanduser("~/.workbuddy/SOUL.md")


def layer_sections(text):
    """按 '## L{n} · 标题' 切出六层段。返回 [(层号, 标题, 文本)]"""
    # 匹配 "## L1 · 身份骨架" 到下一个 "## " 二级标题前的六层
    pattern = re.compile(r"^## (L[1-6]) · (.+)$", re.M)
    matches = list(pattern.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        # 终止于下一个 "## " 二级标题（含 🔁/📍，不含 ### 子标题）
        end_m = re.search(r"^## (?![1-6]\.)", text[start:], re.M)
        end = start + end_m.start() if end_m else len(text)
        sections.append((m.group(1), m.group(2), text[start:end]))
    return sections


def est_tokens(text):
    """中文约 1 字≈1 token 粗估（中文 tokenizer 常见 ~0.6-1.2 字/token，取保守上界）。"""
    # 中文汉字 + 全角标点按 1 计，ASCII 按 4 字符 1 token 计
    cn = len(re.findall(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", text))
    ascii_chars = len(re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", "", text))
    return cn + max(1, ascii_chars // 4)


def main():
    spec_path = SPEC_DEFAULT
    soul_path = SOUL_DEFAULT
    if len(sys.argv) > 1:
        spec_path = sys.argv[1]
    if "--soul" in sys.argv:
        soul_path = sys.argv[sys.argv.index("--soul") + 1]

    with open(spec_path, encoding="utf-8") as f:
        spec = f.read()
    with open(soul_path, encoding="utf-8") as f:
        soul = f.read()

    # 恒驻核候选 = 运行时注入声明段 + L1 全量
    # 注入声明段: "## ⚡ 运行时注入声明" 到 "## 🔧 机制登记"（机制登记=导航指针·按需Read规格书·2026-09-11 与生成器对齐瘦身）
    decl_m = re.search(r"^## ⚡ 运行时注入声明.*?(?=^## 🔧 机制登记|^## 📍 续蒸游标)", spec, re.M | re.S)
    decl_text = decl_m.group(0) if decl_m else ""

    sections = layer_sections(spec)
    layer_map = {num: (title, txt) for num, title, txt in sections}

    # 恒驻核候选: 注入声明 + L1
    core_text = decl_text + "\n" + layer_map.get("L1", ("", ""))[1]

    # 域切片候选: L2 认知 / L3 行为 / L4 表达 / L5 边界 / L6 反向
    domain_slices = {}
    for num in ["L2", "L3", "L4", "L5", "L6"]:
        if num in layer_map:
            domain_slices[num] = layer_map[num][1]

    # ---- 输出 ----
    def fmt(name, txt):
        return (name, len(txt.encode("utf-8")), est_tokens(txt))

    rows = []
    rows.append(fmt("SOUL.md（恒驻核对比基准）", soul))
    rows.append(fmt("规格书全量", spec))
    rows.append(("", 0, 0))  # spacer
    rows.append(fmt("【恒驻核候选】注入声明+L1", core_text))
    for num in ["L2", "L3", "L4", "L5", "L6"]:
        if num in domain_slices:
            rows.append(fmt(f"  └ 域切片 {num} {layer_map[num][0]}", domain_slices[num]))

    print(f"{'段':<40} {'字节':>8} {'~token':>8}")
    print("-" * 60)
    for name, b, t in rows:
        if b == 0:
            print()
            continue
        print(f"{name:<40} {b:>8} {t:>8}")

    core_bytes = len(core_text.encode("utf-8"))
    soul_bytes = len(soul.encode("utf-8"))
    ratio = core_bytes / soul_bytes if soul_bytes else 0
    print("-" * 60)
    print(f"恒驻核 / SOUL 比值: {ratio:.2f}x (目标 ≤1.5x -> {'✅ 达标' if ratio <= 1.5 else '❌ 超标'})")
    print(f"全量 / SOUL 比值: {len(spec.encode('utf-8')) / soul_bytes:.2f}x")

    # 剩余空间: 若核心≤1.5x，还能装多少域切片
    budget = soul_bytes * 1.5
    room = budget - core_bytes
    print(f"预算(1.5×SOUL)={budget}B, 恒驻核={core_bytes}B, 剩余可装={room}B")
    l3_bytes = len(domain_slices.get("L3", "").encode("utf-8"))
    if room > 0:
        print(f"  剩余空间可容纳 L3 行为规则({l3_bytes}B)? -> {'✅ 可' if l3_bytes <= room else '❌ 不可'}")

    # 逐断言 trigger 分布统计（语义簇边界验证）
    trig_count = len(re.findall(r"triggers:", spec))
    print(f"\n断言 trigger 字段总数: {trig_count}（语义簇边界可用性）")


if __name__ == "__main__":
    main()
