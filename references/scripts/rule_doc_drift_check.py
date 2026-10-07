#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
rule_doc_drift_check.py — 铁律版索引表描述 vs 实盘常驻文件 一致性检查

设计定位（2026-09-15 童灵执行·三明智L2结论落地）：
- 三明智L2评估发现：铁律版索引表写"008已通过MEMORY+SOUL双启动"，
  但实盘MEMORY.md里只有一句指路，008骨架实际只在SOUL.md。
- 本脚本机械检查：索引表声称常驻的铁律，在目标文件里是否真的存在。
- 只报告不自动修复——发现漂移输出⚠️，人决定怎么改。

检查项：
1. resident铁律（索引表标"已通过...强启动"）→ 目标文件里能否搜到该铁律的关键词
2. MEMORY.md里的铁律骨架段（001/002/005）→ 和索引表声称的resident状态是否一致
3. 索引表编号连续性（001-022，009占位）

退出码：0=全部一致，1=有漂移
"""
import os
import re
import sys

HOME = os.path.expanduser("~")
TIELU_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆规则", "用户基本规则-铁律版.md")
MEMORY_FILE = os.path.join(HOME, ".workbuddy", "MEMORY.md")
SOUL_FILE = os.path.join(HOME, ".workbuddy", "SOUL.md")


def read_file(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parse_index_table(tielu_text):
    """从铁律版提取加载时机索引表，返回 [(编号, 名称, 加载时机描述, resident判断)]"""
    rows = []
    in_table = False
    for line in tielu_text.splitlines():
        if "加载时机索引表" in line and "##" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("## ") and "加载时机" not in line:
                break
            m = re.match(r"\|\s*(\d{3})\s*\|([^|]+)\|([^|]+)\|", line)
            if m:
                num = m.group(1).strip()
                name = m.group(2).strip()
                timing = m.group(3).strip()
                is_resident = "强启动" in timing or "无需额外 Read" in timing or "已通过" in timing
                rows.append((num, name, timing, is_resident))
    return rows


def check():
    tielu = read_file(TIELU_FILE)
    memory = read_file(MEMORY_FILE) or ""
    soul = read_file(SOUL_FILE) or ""

    if not tielu:
        print("❌ 铁律版文件不存在:", TIELU_FILE)
        return 1

    issues = []
    rows = parse_index_table(tielu)
    print(f"📋 索引表解析到 {len(rows)} 条铁律")
    print()

    # 检查1: resident铁律是否真的在目标文件里
    print("=== 检查1: resident铁律实盘验证 ===")
    for num, name, timing, is_resident in rows:
        if not is_resident:
            continue
        # 提取名称关键词（取前4个字做搜索）
        keyword = name[:4].replace("（", "").replace("(", "")
        in_memory = keyword in memory or name in memory
        in_soul = keyword in soul or name in soul

        # 索引表说"通过MEMORY.md硬路牌 + SOUL.md强启动"
        claims_memory = "MEMORY" in timing
        claims_soul = "SOUL" in timing

        print(f"  {num} {name[:20]:<22} | 索引表声称: MEMORY={claims_memory} SOUL={claims_soul} | 实盘: MEMORY={'✅' if in_memory else '❌'} SOUL={'✅' if in_soul else '❌'}")

        if claims_memory and not in_memory:
            issues.append(f"⚠️ {num} {name}: 索引表声称在MEMORY.md常驻，但实盘搜不到关键词'{keyword}'")
        if claims_soul and not in_soul:
            issues.append(f"⚠️ {num} {name}: 索引表声称在SOUL.md常驻，但实盘搜不到关键词'{keyword}'")
    print()

    # 检查2: MEMORY.md铁律骨架段实际内容
    print("=== 检查2: MEMORY.md铁律骨架段实盘 ===")
    skeleton_section = re.search(r"铁律骨架.*?\n(.*?)(?=\n##|\Z)", memory, re.DOTALL)
    if skeleton_section:
        skeleton_text = skeleton_section.group(1)
        print(f"  MEMORY.md铁律骨架段内容:")
        for line in skeleton_text.strip().splitlines():
            if line.strip():
                print(f"    {line.strip()}")
        # 提取编号
        skeleton_ids = re.findall(r"(\d{3})\s", skeleton_text)
        print(f"  实盘常驻编号: {skeleton_ids}")
    else:
        issues.append("⚠️ MEMORY.md未找到'铁律骨架'段")
    print()

    # 检查3: 索引表编号连续性
    print("=== 检查3: 索引表编号连续性 ===")
    nums = [int(r[0]) for r in rows]
    expected = list(range(1, 23))
    missing = [n for n in expected if n not in nums]
    extra = [n for n in nums if n not in expected]
    if missing:
        issues.append(f"⚠️ 索引表缺少编号: {missing}")
    if extra:
        issues.append(f"⚠️ 索引表多出编号: {extra}")
    if not missing and not extra:
        print(f"  ✅ 001-022完整（009占位正常）")
    print()

    # 报告
    print("=" * 50)
    if issues:
        print(f"🔍 发现 {len(issues)} 处漂移:")
        for i in issues:
            print(f"  {i}")
        return 1
    else:
        print("✅ 全部一致，无漂移")
        return 0


if __name__ == "__main__":
    sys.exit(check())
