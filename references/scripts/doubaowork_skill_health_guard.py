#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
doubaowork_skill_health_guard.py v0.1 — 豆包办公 Skill 生态健康守卫（专属·质变级）

第一性原理（2026-08-25）：豆包办公端 53 个 Skill 软链接是所有能力的载体，
  软链接断裂=Skill 静默消失=需要时找不到=无报错。这是最危险的失效模式。
  本守卫将静默失效变为主动检测，每次巡逻输出健康报告。

对齐先例：Qoder CN qodercn_inject_chain_guard（注入链健康四检测）·
  Trae Work session_memory_quality_guard（摘要质量监控）·
  共同模式=检测平台特有核心机制健康度。

检测项（5 项）：
  1. 软链接断裂（源目录不存在）
  2. SKILL.md 缺失（软链接目录下无 SKILL.md）
  3. 重复链接（同一源被多个软链接指向）
  4. 必备 Skill 缺失（核心能力 Skill 不在列表中）
  5. 版本漂移（软链接指向的 SKILL.md version 字段异常）

退出码：
  0 = 全部健康
  1 = 有非必备问题（断裂/重复/版本漂移）
  2 = 有必备 Skill 缺失（核心能力失效）

使用：
  python3 doubaowork_skill_health_guard.py           # 文本报告
  python3 doubaowork_skill_health_guard.py --json     # JSON 报告
  python3 doubaowork_skill_health_guard.py --fix      # 尝试修复（重新创建断裂软链接·需源存在）
"""
import os
import sys
import json
import re
import argparse
from collections import defaultdict
from datetime import datetime

# === 配置 ===
SKILL_LINKS_DIR = os.path.expanduser(
    "~/Library/Application Support/DoubaoWork/Default/.doubaowork/agent_mode/workspace/.user_skills"
)
# 必备 Skill 清单（核心能力·缺失=系统级失效）
# 注意：只包含 .user_skills 下的软链接，系统内置 Skill（.skills 目录下如 doubao-cron-scheduler）不计入
REQUIRED_SKILLS = [
    "system-logger",           # 系统日志（实质性任务后必须写入）
    "布洛陀-豆包办公规则",      # 端专属规则（五系统文件加载+核心3守卫）
]
# 可选但重要的 Skill（缺失=功能降级但不系统级失效）
IMPORTANT_SKILLS = [
    "lark-doc", "lark-sheets", "lark-slides-pro", "lark-calendar",
    "lark-im", "lark-task", "lark-base", "lark-drive",
    "doubao-app-builder", "doubao-creative-video", "doubao-creative-design",
]


def scan_skill_links(links_dir):
    """扫描所有软链接，返回 {link_name: {target, exists, has_skill_md, version}}"""
    results = {}
    if not os.path.isdir(links_dir):
        return results, f"软链接目录不存在: {links_dir}"
    for name in sorted(os.listdir(links_dir)):
        link_path = os.path.join(links_dir, name)
        if not os.path.islink(link_path):
            continue  # 非软链接跳过（如真实目录）
        target = os.readlink(link_path)
        # 解析相对路径
        if not os.path.isabs(target):
            target = os.path.normpath(os.path.join(os.path.dirname(link_path), target))
        exists = os.path.isdir(target)
        has_skill_md = False
        version = None
        if exists:
            skill_md = os.path.join(target, "SKILL.md")
            has_skill_md = os.path.isfile(skill_md)
            if has_skill_md:
                try:
                    with open(skill_md, encoding="utf-8") as f:
                        content = f.read(2000)  # 只读前2000字符（frontmatter）
                    m = re.search(r'^version:\s*["\']?([^"\'\n]+)', content, re.MULTILINE)
                    if m:
                        version = m.group(1).strip()
                except Exception:
                    pass
        results[name] = {
            "target": target,
            "exists": exists,
            "has_skill_md": has_skill_md,
            "version": version,
        }
    return results, None


def detect_duplicates(results):
    """检测重复链接（同一目标被多个软链接指向）"""
    target_to_links = defaultdict(list)
    for name, info in results.items():
        if info["exists"]:
            target_to_links[info["target"]].append(name)
    duplicates = {t: names for t, names in target_to_links.items() if len(names) > 1}
    return duplicates


def check_required(results):
    """检测必备 Skill 是否存在且健康"""
    missing = []
    unhealthy = []
    for req in REQUIRED_SKILLS:
        if req not in results:
            missing.append(req)
        elif not results[req]["exists"]:
            unhealthy.append((req, "软链接断裂"))
        elif not results[req]["has_skill_md"]:
            unhealthy.append((req, "SKILL.md 缺失"))
    return missing, unhealthy


def check_version_drift(results):
    """检测版本漂移（仅对必备 Skill 检测 version 字段·其他 Skill 无 version 属正常·不计入问题）"""
    drift = []
    for req in REQUIRED_SKILLS:
        if req in results and results[req]["exists"] and results[req]["has_skill_md"]:
            if not results[req]["version"]:
                drift.append((req, "version 字段缺失"))
            elif not re.match(r'^v?\d+\.\d+', results[req]["version"]):
                drift.append((req, f"version 格式异常: {results[req]['version']}"))
    return drift


def generate_report(results, duplicates, missing_required, unhealthy_required, version_drift, fmt="text"):
    """生成健康报告"""
    total = len(results)
    broken = [n for n, i in results.items() if not i["exists"]]
    no_skill_md = [n for n, i in results.items() if i["exists"] and not i["has_skill_md"]]
    healthy_count = total - len(broken) - len(no_skill_md)

    report = {
        "timestamp": datetime.now().isoformat(),
        "guard": "doubaowork_skill_health_guard",
        "version": "v0.1",
        "summary": {
            "total": total,
            "healthy": healthy_count,
            "broken": len(broken),
            "no_skill_md": len(no_skill_md),
            "duplicates": len(duplicates),
            "missing_required": len(missing_required),
            "unhealthy_required": len(unhealthy_required),
            "version_drift": len(version_drift),
        },
        "details": {
            "broken": broken,
            "no_skill_md": no_skill_md,
            "duplicates": duplicates,
            "missing_required": missing_required,
            "unhealthy_required": unhealthy_required,
            "version_drift": version_drift,
        },
    }

    # 判定退出码
    if missing_required or unhealthy_required:
        report["exit_code"] = 2
        report["status"] = "CRITICAL"
    elif broken or duplicates or version_drift:
        report["exit_code"] = 1
        report["status"] = "WARNING"
    else:
        report["exit_code"] = 0
        report["status"] = "HEALTHY"

    if fmt == "json":
        return json.dumps(report, ensure_ascii=False, indent=2), report["exit_code"]

    # 文本报告
    lines = []
    lines.append("=" * 60)
    lines.append(f"豆包办公 Skill 生态健康守卫 v0.1")
    lines.append(f"时间: {report['timestamp']}")
    lines.append(f"状态: {report['status']} (exit={report['exit_code']})")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"总 Skill 数: {total}")
    lines.append(f"  ✅ 健康: {healthy_count}")
    lines.append(f"  ❌ 断裂: {len(broken)}")
    lines.append(f"  ⚠️  无 SKILL.md: {len(no_skill_md)}")
    lines.append(f"  🔁 重复链接: {len(duplicates)}")
    lines.append(f"  🔴 必备缺失: {len(missing_required)}")
    lines.append(f"  🟡 必备不健康: {len(unhealthy_required)}")
    lines.append(f"  📌 版本漂移: {len(version_drift)}")
    lines.append("")

    if broken:
        lines.append("❌ 断裂的软链接:")
        for n in broken:
            lines.append(f"  - {n} → {results[n]['target']} (不存在)")
        lines.append("")

    if no_skill_md:
        lines.append("⚠️  无 SKILL.md:")
        for n in no_skill_md:
            lines.append(f"  - {n}")
        lines.append("")

    if duplicates:
        lines.append("🔁 重复链接:")
        for target, names in duplicates.items():
            lines.append(f"  - {target}")
            for n in names:
                lines.append(f"    ↳ {n}")
        lines.append("")

    if missing_required:
        lines.append("🔴 必备 Skill 缺失:")
        for n in missing_required:
            lines.append(f"  - {n}")
        lines.append("")

    if unhealthy_required:
        lines.append("🟡 必备 Skill 不健康:")
        for n, reason in unhealthy_required:
            lines.append(f"  - {n}: {reason}")
        lines.append("")

    if version_drift:
        lines.append("📌 版本漂移:")
        for n, reason in version_drift:
            lines.append(f"  - {n}: {reason}")
        lines.append("")

    if report["status"] == "HEALTHY":
        lines.append("✅ 全部健康，无问题。")

    return "\n".join(lines), report["exit_code"]


def main():
    parser = argparse.ArgumentParser(description="豆包办公 Skill 生态健康守卫")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--fix", action="store_true", help="尝试修复（重新创建断裂软链接）")
    args = parser.parse_args()

    results, err = scan_skill_links(SKILL_LINKS_DIR)
    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    duplicates = detect_duplicates(results)
    missing_required, unhealthy_required = check_required(results)
    version_drift = check_version_drift(results)

    fmt = "json" if args.json else "text"
    report, exit_code = generate_report(
        results, duplicates, missing_required, unhealthy_required, version_drift, fmt
    )
    print(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
