#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
TeleAgent 端 Skill 生态健康度守卫 v0.3
功能: 检测 TeleAgent skills 目录下 Skill 软链接的健康度
检测项(4项·对齐设计哲学 03-守卫与护栏规范 §6.4):
  1. 软链接有效性(断裂检测)
  2. SKILL.md 存在性 + frontmatter 完整性
  3. 重复检测(同名 Skill 冲突)
  4. 必备缺失检测(9 个发布口径 Skill 是否全在)
退出码: 0=全健康 1=有异常 2=参数错误
作者: 皮叔
用法: python3 teleagent_skill_health_guard.py --mc <记忆中心路径> [--json]
部署: 记忆中心 开发工具/teleagent-enhancer/guards/ (由加强包 setup 写入)
设计源: 记忆蓝图/02_设计理念/星辰超级智能体布洛陀设计哲学/03-守卫与护栏规范.md §6.4

v0.3 变更: 移除 v0.2 第5项版本漂移检测——TeleAgent 端 Skill 普遍无 version 字段(平台常态),
  软链场景本地与基线为同一文件版本永远一致, 且使用者本地版本普遍高于发布口径属正常升级状态。
  版本号缺失不再报 warning(对齐守卫原则'守卫不阻塞业务')。
"""
import os
import sys
import argparse
import json
import re
from pathlib import Path

# 发布口径必备 Skill 清单(与 setup.sh FP_SKILLS 一致·布洛陀-安装包 references/skills)
REQUIRED_SKILLS = [
    "awaken-memory-system",
    "clock-loop",
    "daily-buddy",
    "growth-box",
    "meta-aletheia",
    "shall-we-talk",
    "system-logger",
    "triwich",
    "sucair",
]


def find_teleagent_skills_dir(mc: str) -> str:
    """查找 TeleAgent skills 目录（macOS/Windows 通用）"""
    candidates = []
    home = os.path.expanduser("~")

    # macOS / Linux / Windows 同构路径
    main_path = os.path.join(home, ".config", "TeleAgent", "skills")
    candidates.append(main_path)

    # 记忆中心下的技能配置目录（备份兜底）
    mc_skills = os.path.join(mc, "技能配置")
    candidates.append(mc_skills)

    for c in candidates:
        if os.path.isdir(c):
            return c
    return ""


def parse_frontmatter(skill_md_path: str) -> dict:
    """解析 SKILL.md frontmatter，返回 name/description/version 等"""
    fm = {}
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read(3000)  # 只读前3000字符
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                fm_raw = content[3:end]
                # 逐行解析 key: value（支持多行 > 值取第一行）
                for line in fm_raw.strip().splitlines():
                    m = re.match(r'^(\w[\w-]*)\s*:\s*(.+)', line)
                    if m:
                        key = m.group(1).strip()
                        val = m.group(2).strip()
                        # 去掉 YAML 多行指示符 >
                        if val.startswith(">"):
                            val = val[1:].strip()
                        fm[key] = val
    except Exception:
        pass
    return fm


def extract_version(fm: dict) -> str:
    """从 frontmatter 提取版本号"""
    # 常见字段名: version / v
    for key in ("version", "v"):
        if key in fm:
            return fm[key]
    return ""


def check_skill(skill_path: str, mc_skills_dir: str) -> dict:
    """检查单个 Skill 的健康度（4 项检测）"""
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

    # ── 检测1: 软链接有效性(断裂检测) ──
    if result["is_symlink"]:
        target = os.readlink(skill_path)
        result["link_target"] = target
        if not os.path.exists(skill_path):
            result["link_valid"] = False
            result["status"] = "broken"
            result["issues"].append(f"软链接断链: {target}")
            return result

    # ── 检测2: SKILL.md 存在性 + frontmatter 完整性 ──
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
    parser = argparse.ArgumentParser(description="TeleAgent端Skill生态健康度守卫")
    parser.add_argument("--mc", required=True, help="记忆共享中心路径")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    mc = os.path.expanduser(args.mc)
    if not os.path.isdir(mc):
        print(f"错误: 记忆中心不存在: {mc}", file=sys.stderr)
        sys.exit(2)

    skills_dir = find_teleagent_skills_dir(mc)
    if not skills_dir:
        print("错误: 未找到TeleAgent skills目录", file=sys.stderr)
        sys.exit(2)

    mc_skills_dir = os.path.join(mc, "技能配置")

    # 扫描所有 Skill
    skills = []
    for item in sorted(os.listdir(skills_dir)):
        item_path = os.path.join(skills_dir, item)
        if os.path.isdir(item_path) or os.path.islink(item_path):
            skills.append(check_skill(item_path, mc_skills_dir))

    # ── 检测3: 重复检测(同名 Skill 冲突) ──
    name_counts = {}
    for s in skills:
        name_counts[s["name"]] = name_counts.get(s["name"], 0) + 1
    duplicates = {n: c for n, c in name_counts.items() if c > 1}
    for s in skills:
        if s["name"] in duplicates:
            s["status"] = "warning"
            s["issues"].append(f"重复: 同名Skill共{duplicates[s['name']]}个")

    # ── 检测4: 必备缺失检测(9 个发布口径 Skill 是否全在) ──
    existing_names = {s["name"] for s in skills}
    missing_required = [s for s in REQUIRED_SKILLS if s not in existing_names]

    # 统计
    total = len(skills)
    healthy = sum(1 for s in skills if s["status"] == "healthy")
    warning = sum(1 for s in skills if s["status"] == "warning")
    broken = sum(1 for s in skills if s["status"] == "broken")

    if args.json:
        output = {
            "skills_dir": skills_dir,
            "mc_skills_dir": mc_skills_dir,
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
        print(f"=== TeleAgent端Skill生态健康度检测 v0.3 ===")
        print(f"Skill目录: {skills_dir}")
        print(f"基线目录: {mc_skills_dir}")
        print(f"总计: {total} | 健康: {healthy} | 警告: {warning} | 断链: {broken}")
        print()

        # 检测4: 必备缺失
        print(f"[必备缺失] 发布口径{len(REQUIRED_SKILLS)}个 Skill 在位: {len(REQUIRED_SKILLS) - len(missing_required)}/{len(REQUIRED_SKILLS)}")
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

    # 退出码: 断链或必备缺失=1(异常), 否则按 warning 判定
    has_critical = broken > 0 or len(missing_required) > 0
    sys.exit(1 if (has_critical or warning > 0) else 0)


if __name__ == "__main__":
    main()