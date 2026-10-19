#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CatPaw 端 Skill 生态健康度守卫 v0.1
功能: 检测 CatPaw skills 目录下 Skill 的健康度
检测项(4项):
  1. 软链接有效性(断裂检测)
  2. SKILL.md 存在性 + frontmatter 完整性
  3. 重复检测(同名 Skill 冲突)
  4. 必备缺失检测(核心 Skill 是否全在)
退出码: 0=全健康 1=有异常 2=参数错误
作者: CatPaw (按布洛陀脚本体系·跨工具中立方式 B 接入)
设计源: 记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/INDEX.md §进度速览·豆包办公/ TeleAgent 端接入先例
用法: python3 catpaw_skill_health_guard.py [--json]
部署: 记忆中心 开发工具/ (跨工具中立脚本·patrol 降级调用)
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import os
import sys
import json
import re

CATPAW_SKILLS_DIR = os.path.join(os.path.expanduser("~"), ".meituan-catpaw", "997967003", "skills")

# CatPaw 端必备 Skill(与发布口径·router.py 触发词表对齐·16个核心 Skill)
REQUIRED_SKILLS = [
    "awaken-memory-system",
    "chrold",
    "clock-loop",
    "daily-buddy",
    "good-good-study",
    "growth-box",
    "meta-aletheia",
    "scriyore",
    "shall-we-talk",
    "skill-forge",
    "sucair",
    "system-logger",
    "triwich",
    "excavator",
    "热点捕手",
    "素然启镜",
]


def parse_frontmatter(skill_md_path: str) -> dict:
    """解析 SKILL.md frontmatter，返回 name/description/version 等"""
    fm = {}
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read(3000)
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                fm_raw = content[3:end]
                for line in fm_raw.strip().splitlines():
                    m = re.match(r'^([\w-]+)\s*:\s*(.+)', line)
                    if m:
                        key = m.group(1).strip()
                        val = m.group(2).strip()
                        if val.startswith(">"):
                            val = val[1:].strip()
                        fm[key] = val
    except Exception:
        pass
    return fm


def check_skill(skill_path: str) -> dict:
    """检查单个 Skill 的健康度(4 项检测的基础)"""
    name = os.path.basename(skill_path)
    result = {
        "name": name,
        "path": skill_path,
        "is_symlink": os.path.islink(skill_path),
        "link_target": "",
        "link_valid": True,
        "skill_md_exists": False,
        "frontmatter_complete": False,
        "status": "healthy",
        "issues": []
    }

    # 检测1: 软链接有效性(断裂检测)
    if result["is_symlink"]:
        target = os.readlink(skill_path)
        result["link_target"] = target
        if not os.path.exists(skill_path):
            result["link_valid"] = False
            result["status"] = "broken"
            result["issues"].append(f"软链接断链: {target}")
            return result

    # 检测2: SKILL.md 存在性 + frontmatter 完整性
    skill_md = os.path.join(skill_path, "SKILL.md")
    if os.path.isfile(skill_md):
        result["skill_md_exists"] = True
        fm = parse_frontmatter(skill_md)
        if "name" in fm and "description" in fm:
            result["frontmatter_complete"] = True
    else:
        result["issues"].append("SKILL.md不存在")

    if not result["frontmatter_complete"]:
        result["status"] = "warning"
        result["issues"].append("frontmatter不完整(name/description缺失)")

    return result


def main():
    if not os.path.isdir(CATPAW_SKILLS_DIR):
        print(f"错误: CatPaw skills 目录不存在: {CATPAW_SKILLS_DIR}", file=sys.stderr)
        sys.exit(2)

    skills = []
    for item in sorted(os.listdir(CATPAW_SKILLS_DIR)):
        item_path = os.path.join(CATPAW_SKILLS_DIR, item)
        if os.path.isdir(item_path) or os.path.islink(item_path):
            skills.append(check_skill(item_path))

    # 检测3: 重复检测(同名 Skill 冲突)
    name_counts = {}
    for s in skills:
        name_counts[s["name"]] = name_counts.get(s["name"], 0) + 1
    duplicates = {n: c for n, c in name_counts.items() if c > 1}
    for s in skills:
        if s["name"] in duplicates:
            s["status"] = "warning"
            s["issues"].append(f"重复: 同名Skill共{duplicates[s['name']]}个")

    # 检测4: 必备缺失检测(16 个核心 Skill 是否全在)
    existing_names = {s["name"] for s in skills}
    missing_required = [s for s in REQUIRED_SKILLS if s not in existing_names]

    # 统计
    total = len(skills)
    healthy = sum(1 for s in skills if s["status"] == "healthy")
    warning = sum(1 for s in skills if s["status"] == "warning")
    broken = sum(1 for s in skills if s["status"] == "broken")

    has_json = "--json" in sys.argv

    if has_json:
        output = {
            "skills_dir": CATPAW_SKILLS_DIR,
            "total": total,
            "healthy": healthy,
            "warning": warning,
            "broken": broken,
            "duplicates": list(duplicates.keys()),
            "missing_required": missing_required,
            "required_list": REQUIRED_SKILLS,
            "skills": skills
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"=== CatPaw端Skill生态健康度检测 v0.1 ===")
        print(f"Skill目录: {CATPAW_SKILLS_DIR}")
        print(f"总计: {total} | 健康: {healthy} | 警告: {warning} | 断链: {broken}")
        print()

        # 检测4: 必备缺失
        print(f"[必备缺失] 核心{len(REQUIRED_SKILLS)}个 Skill 在位: {len(REQUIRED_SKILLS) - len(missing_required)}/{len(REQUIRED_SKILLS)}")
        if missing_required:
            print(f"  ❌ 缺失: {', '.join(missing_required)}")
        else:
            print(f"  ✅ 全部在位")
        print()

        # 检测3: 重复
        if duplicates:
            print(f"[重复检测] 发现{len(duplicates)}个同名冲突:")
            for n, c in duplicates.items():
                print(f"  ⚠️ {n}: {c}个")
        else:
            print(f"[重复检测] ✅ 无同名冲突")
        print()

        # 逐 Skill 详情
        for s in skills:
            icon = "✅" if s["status"] == "healthy" else ("⚠️" if s["status"] == "warning" else "❌")
            link_info = f"→{s['link_target']}" if s["is_symlink"] else "(目录)"
            print(f"{icon} {s['name']} {link_info}")
            for issue in s["issues"]:
                print(f"   - {issue}")
        print()

        # 汇总
        has_critical = broken > 0 or len(missing_required) > 0
        if has_critical:
            print(f"❌ 关键问题: 断链{broken}个 + 必备缺失{len(missing_required)}个")
        if warning > 0:
            print(f"⚠️ 警告: {warning}个Skill有问题(frontmatter不完整/重复)")
        if not has_critical and warning == 0:
            print(f"✅ 全部{total}个Skill健康")

    has_critical = broken > 0 or len(missing_required) > 0
    sys.exit(1 if (has_critical or warning > 0) else 0)


if __name__ == "__main__":
    main()
