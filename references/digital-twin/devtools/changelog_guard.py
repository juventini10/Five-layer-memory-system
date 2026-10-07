#!/usr/bin/env python3
"""
变更日志写入前机械校验 v1.1
检查待写入条目是否属于 excluded_types（规则2的机械实现）

v1.1修正：
  - 匹配逻辑从"核心词完整子串"改为"关键词组分匹配"
  - 每个excluded_type拆成多个关键词，任一匹配即判定属于该类型
  - 增加同义词扩展（如"安装包"≈"发布包"≈"布洛陀包"）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re

CHANGELOG_PATH = os.path.expanduser("~/变更日志.md")

# excluded_types 的关键词组定义
# 每个类型含多个关键词，任一匹配即判定属于该类型
EXCLUDED_KEYWORDS = {
    "安装包自身改动": [
        "安装包", "发布包", "布洛陀", "包侧", "脱敏", "version.md",
        "INSTALL.md", "conffiles", "mirror-sync", "mirror-manifest",
        "deident_rules", "包版本", "install-audit", "sync-check",
        "smoke-test",
    ],
    "开发工具/构建脚本": [
        "manifest", "rules-strip", "fswatch", "launchd", "LaunchAgents",
        "mirror-", "release-sync", "开发工具", "构建脚本", "build",
        "rules-curation", "whitelist", "amber-backup", "amber-watch",
        "sync-systemlog", "consistency_check", "growth_box_check",
        "changelog_guard",
    ],
    "私人日记正文内容": [
        "每日日记", "灵感闪现", "睡眠质量", "心情", "感悟", "伙伴建议",
        "今日工作", "明日目标", "晨间规划", "晚间复盘",
    ],
    "测试产出物批量修复": [
        "评估报告", "progress文件", "test_results", "审查报告",
        "skill_tests", "批量补YAML", "批量修复",
    ],
}


def check_entry(entry_text):
    """
    检查条目说明文本是否属于excluded_types
    返回 (allowed: bool, matched_types: list of (type, keyword))
    """
    entry_lower = entry_text.lower()
    matched = []
    
    for excluded_type, keywords in EXCLUDED_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in entry_lower:
                matched.append((excluded_type, kw))
                break  # 每个类型只需一个关键词匹配
    
    return len(matched) == 0, matched


def main():
    if len(sys.argv) < 2:
        print("用法: python3 changelog_guard.py \"本次记录的说明文本\"")
        sys.exit(2)
    
    entry_text = " ".join(sys.argv[1:])
    
    allowed, matched = check_entry(entry_text)
    
    if allowed:
        print(f"✅ 校验通过——允许写入变更日志")
        print(f"   说明: {entry_text[:100]}")
        sys.exit(0)
    else:
        print(f"❌ 校验失败——本条目属于 excluded_types，禁止写入变更日志")
        print(f"   说明: {entry_text[:100]}")
        print(f"   匹配的排除类型:")
        for t, kw in matched:
            print(f"     • {t} (关键词: \"{kw}\")")
        print(f"   依据: 变更日志规则2（🚫 不记）+ frontmatter excluded_types 字段")
        print(f"   如果确实属于LIVE系统演进，请手动确认后写入（覆盖机械校验）")
        sys.exit(1)


if __name__ == "__main__":
    main()
