#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill_version_check.py — 布洛陀安装包 Skill 版本检测
============================================================
职责：比对安装包内 Skill 版本与用户已安装版本，输出结构化差异报告。
      支持全量检测和单 Skill 检测两种模式。

用法：
  python3 skill_version_check.py                       # 检测全部 Skill
  python3 skill_version_check.py --skill daily-buddy   # 只检测指定 Skill
  python3 skill_version_check.py --pkg-root <路径>     # 指定安装包根目录
  python3 skill_version_check.py --user-root <路径>    # 指定用户技能配置目录

退出码：0=全部最新  1=有可更新项  2=参数/路径错误

设计约束：
- 只读操作，不修改任何文件
- 用户技能配置不存在 → 全部标记"未安装"
- CHANGELOG 摘要只取首条变更标题行（一眼看到更新了什么）
- 版本比较使用语义化版本排序（支持 x.y.z 和 x.y 格式）
"""
import argparse
import os
import re
import sys
from pathlib import Path

# Windows 控制台 UTF-8 守卫：cp1252 代码页下 print emoji/中文 会 UnicodeEncodeError
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass



def _extract_version(skill_md: Path) -> str:
    """从 SKILL.md 提取 version 字段值。"""
    if not skill_md.exists():
        return ""
    try:
        for line in skill_md.read_text(encoding="utf-8").splitlines()[:50]:
            m = re.match(r'^version:\s*["\']?([^"\']+)["\']?\s*$', line)
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    return ""


def _parse_version(v: str) -> tuple:
    """将版本字符串解析为可比较的元组。支持 x.y.z / x.y / x 格式。"""
    parts = re.split(r'[.\-]', v)
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(p)
    return tuple(result)


def _compare_versions(installed: str, package: str) -> str:
    """比较两个版本，返回状态标签。"""
    if not installed:
        return "未安装"
    if not package:
        return "包无版本"
    if installed == package:
        return "已最新"
    try:
        v_inst = _parse_version(installed)
        v_pkg = _parse_version(package)
        if v_inst < v_pkg:
            return "可更新"
        elif v_inst > v_pkg:
            return "本地领先"
        else:
            return "已最新"
    except (TypeError, ValueError):
        # 无法比较时按字符串判断
        return "已最新" if installed == package else "版本不同"


def _get_changelog_summary(skill_dir: Path) -> str:
    """读取 Skill 的 CHANGELOG.md 首条变更标题行。"""
    changelog = skill_dir / "references" / "CHANGELOG.md"
    if not changelog.exists():
        # 尝试备选路径
        changelog = skill_dir / "CHANGELOG.md"
    if not changelog.exists():
        return "-"
    try:
        lines = changelog.read_text(encoding="utf-8").splitlines()
        for line in lines:
            # 匹配 ## vX.X.X 或 ### vX.X.X 或 - **vX.X.X** 格式
            if re.match(r'^#{1,3}\s+v?\d', line) or re.match(r'^-\s+\*\*v?\d', line):
                # 截取核心内容（去掉 ## 前缀，限80字）
                summary = re.sub(r'^#{1,3}\s+', '', line).strip()
                summary = re.sub(r'^-\s+\*\*', '', summary).strip()
                return summary[:80] if len(summary) > 80 else summary
    except Exception:
        pass
    return "-"


def scan_skills(pkg_root: Path, user_root: Path, target_skill: str = None) -> list:
    """扫描并比对 Skill 版本。返回 [(name, installed_ver, pkg_ver, status, changelog), ...]"""
    pkg_skills_dir = pkg_root / "references" / "skills"
    if not pkg_skills_dir.exists():
        return []

    results = []
    for skill_dir in sorted(pkg_skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        name = skill_dir.name
        if target_skill and name != target_skill:
            continue

        pkg_skill_md = skill_dir / "SKILL.md"
        user_skill_md = user_root / name / "SKILL.md"

        pkg_ver = _extract_version(pkg_skill_md)
        installed_ver = _extract_version(user_skill_md)

        if not pkg_ver:
            continue  # 包里这个 Skill 没有版本声明，跳过

        status = _compare_versions(installed_ver, pkg_ver)
        changelog = _get_changelog_summary(skill_dir) if status == "可更新" else "-"

        results.append((name, installed_ver or "-", pkg_ver, status, changelog))

    return results


def main():
    parser = argparse.ArgumentParser(description="布洛陀安装包 Skill 版本检测")
    parser.add_argument("--skill", type=str, default=None, help="只检测指定 Skill")
    parser.add_argument("--pkg-root", type=str, default=None, help="安装包根目录")
    parser.add_argument("--user-root", type=str, default=None, help="用户技能配置目录")
    args = parser.parse_args()

    # 确定安装包根目录（默认：脚本所在目录的上两级）
    if args.pkg_root:
        pkg_root = Path(args.pkg_root).expanduser().resolve()
    else:
        # 脚本在 references/scripts/ 下，包根 = ../../
        pkg_root = Path(__file__).resolve().parent.parent.parent

    # 确定用户技能配置目录
    if args.user_root:
        user_root = Path(args.user_root).expanduser().resolve()
    else:
        # G2-2 走查缺陷修：字面 "~/记忆共享中心" 默认值=用户中心名任意时全报"未安装"假红。
        # 根治=与 verify.sh §MC 同型候选探测；全落空则 fail-loud 要求显式 --user-root（⛔不静默兜底）。
        _cands = []
        _mc_env = os.environ.get("MEMORY_CENTER")
        if _mc_env:
            _cands.append(Path(_mc_env))
        else:
            for _c in (Path.home() / "记忆共享中心", "[记忆共享中心]",
                       Path.home() / "共享中心", Path.home() / "记忆中心", Path.home() / "布洛陀记忆中心"):
                _cands.append(_c)
        user_root = next((c / "技能配置" for c in _cands if (c / "技能配置").is_dir()), None)
        if user_root is None:
            print("错误：未找到记忆中心/技能配置——请传 --user-root <路径> 或设 MEMORY_CENTER 环境变量（防默认值假红）")
            sys.exit(2)

    # 校验路径
    if not pkg_root.exists():
        print(f"错误：安装包路径不存在：{pkg_root}")
        sys.exit(2)

    pkg_skills = pkg_root / "references" / "skills"
    if not pkg_skills.exists():
        print(f"错误：安装包 references/skills/ 不存在：{pkg_skills}")
        sys.exit(2)

    # 用户目录不存在 → 全部"未安装"（全新用户正常情况）
    if not user_root.exists():
        print(f"提示：用户技能配置目录不存在：{user_root}")
        print("      可能是全新安装，所有 Skill 将标记为「未安装」\n")

    # 执行检测
    results = scan_skills(pkg_root, user_root, args.skill)

    if not results:
        if args.skill:
            print(f"未找到 Skill：{args.skill}")
            sys.exit(2)
        print("未检测到任何有版本声明的 Skill")
        sys.exit(0)

    # 输出报告
    print("=== Skill 版本检测 ===\n")

    # 表头
    header = f"{'Skill':<22} {'已安装':<10} {'包版本':<10} {'状态':<8} {'最新变更'}"
    print(header)
    print("-" * len(header.encode('gbk', errors='replace')))

    # 数据行
    counts = {"已最新": 0, "可更新": 0, "未安装": 0, "本地领先": 0}
    for name, inst_ver, pkg_ver, status, changelog in results:
        counts[status] = counts.get(status, 0) + 1
        # 状态标记
        mark = {"已最新": "✅", "可更新": "⬆️ ", "未安装": "❌", "本地领先": "🔵"}.get(status, "  ")
        print(f"  {mark} {name:<20} {inst_ver:<10} {pkg_ver:<10} {status:<8} {changelog}")

    # 汇总
    total = len(results)
    print(f"\n汇总：{total}个Skill中", end="")
    parts = []
    if counts.get("可更新", 0):
        parts.append(f"{counts['可更新']}个可更新")
    if counts.get("已最新", 0):
        parts.append(f"{counts['已最新']}个已最新")
    if counts.get("未安装", 0):
        parts.append(f"{counts['未安装']}个未安装")
    if counts.get("本地领先", 0):
        parts.append(f"{counts['本地领先']}个本地领先")
    print("、".join(parts))

    # 操作引导（有可更新或未安装时输出）
    updatable = [name for name, _, _, status, _ in results if status == "可更新"]
    not_installed = [name for name, _, _, status, _ in results if status == "未安装"]

    if updatable or not_installed:
        print()
        print("─" * 50)
        print("📋 操作指引：")
        print()
        if updatable:
            if len(updatable) >= 3:
                print('  升级全部 → 对 AI 说："升级全部 Skill"')
            print("  逐个升级 → 对 AI 说：")
            for name in updatable:
                print(f'    "升级 {name}"')
        if not_installed:
            print("  安装缺失 → 对 AI 说：")
            for name in not_installed:
                print(f'    "安装 {name}"')
        print()
        print("  💡 以上指令需在安装包对话中使用（把安装包文件夹丢给 AI 后说）")

    # 退出码
    if counts.get("可更新", 0) or counts.get("未安装", 0):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
