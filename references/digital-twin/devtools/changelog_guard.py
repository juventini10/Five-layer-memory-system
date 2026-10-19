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

def _probe_mc_root():
    """记忆中心根探测：按结构指纹在家目录下扫一层目录，⛔不认目录名。

    判据源=platform_compat 检查⑫「共享中心目录名硬编码」＋条文47「运行期根决定权唯一源」：
    不同用户的记忆中心根目录叫法各不相同（本端 / 端用户机 / 记忆中心 等），写死任一个
    ＝其他用户直接错根。结构指纹取「记忆规则/用户基本规则-铁律版.md」——布洛陀实装机的
    必要产物，缺它就不是布洛陀环境，探测自然返回 None 走家目录兜底。
    （⛔本文不引门禁扫描词字面量·条文18⑥「门禁词自伤」）
    """
    _home = os.path.expanduser("~")
    _mark = os.path.join("记忆规则", "用户基本规则-铁律版.md")
    try:
        for _e in os.scandir(_home):
            if _e.is_dir() and os.path.isfile(os.path.join(_e.path, _mark)):
                return _e.path
    except OSError:
        pass
    return None


def _changelog_path():
    """变更日志落点 = <记忆中心根>/变更日志.md（B4 根治·2026-10-10 刚叔 V2.1.0 提请单）。

    病根：原 `expanduser("~/变更日志.md")` 把"记忆中心根"当"家目录"——作者机 mac 解析到
    ~/变更日志.md（不存在）、端用户 Windows 解析到 C:/Users/<user>/变更日志.md（也不存在），
    两端都指空文件；真身在 <记忆中心根>/变更日志.md（本端实测 1.3MB 在盘·每日在写）。
    根解析序：env 声明（BULUOTUO_MC/MEMORY_CENTER）→ 结构指纹探测（家目录扫一层）→ HOME。
    ⛔不写死单一目录名（条文47 运行期根唯一源 + platform_compat 检查⑫ 同源）。
    """
    for _k in ("BULUOTUO_MC", "MEMORY_CENTER", "DOENGLINGZ_MC"):
        _v = os.environ.get(_k)
        if _v:
            _p = os.path.expanduser(_v)
            if os.path.isdir(_p):
                return os.path.join(_p, "变更日志.md")
    _ar = _probe_mc_root()
    if _ar:
        return os.path.join(_ar, "变更日志.md")
    return os.path.join(os.path.expanduser("~"), "变更日志.md")


CHANGELOG_PATH = _changelog_path()

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
