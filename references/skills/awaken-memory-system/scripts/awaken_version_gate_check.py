#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
awaken_version_gate_check.py — 版本门禁 + 规则.mdc 一致性机械断言（守卫类·按需部署）
设计依据: awaken-memory-system SKILL.md 步骤 1c（版本门禁）+ 1f（规则.mdc 版本一致性）
职责: ①权威源 SKILL.md 版本 vs 各平台缓存副本版本（不一致=执行旧逻辑风险）
      ②.workbuddy/rules/*.mdc 版本 vs 铁律版权威源（过期=旧规则注入打架）
      判定逻辑从 AI 手跑"Read→对比"移入脚本 → AI 只读 exit code（机械断言）。
      ⛔本脚本只校验不改写（修复动作归 AI：备份→覆盖→从步骤1重来）——零直写原则。
用法:
  python3 awaken_version_gate_check.py   # 双查合一，全过 exit 0
退出码语义:
  0 = 全部一致（版本门禁过 + 规则.mdc 无过期）
  1 = 通用错误（权威源不存在等）
  2 = 缓存版本不一致（权威源 vs 任一平台缓存 SKILL.md——需备份→覆盖→从步骤1重来）
  3 = 规则.mdc 过期（存在但头部版本 ≠ 铁律版权威源——告警输出"规则文件过期"）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re

HOME = os.path.expanduser("~")
AUTHORITY = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "awaken-memory-system", "SKILL.md")
CACHE_PATHS = [
    os.path.join(HOME, ".qoder", "skills", "awaken-memory-system", "SKILL.md"),
    os.path.join(HOME, ".qoder-cn", "skills", "awaken-memory-system", "SKILL.md"),
    os.path.join(HOME, ".workbuddy", "skills", "awaken-memory-system", "SKILL.md"),
    os.path.join(HOME, ".trae-cn", "skills", "awaken-memory-system", "SKILL.md"),
    os.path.join(HOME, ".zcode", "skills", "awaken-memory-system", "SKILL.md"),
]
RULES_DIR = os.path.join(HOME, ".workbuddy", "rules")
# 规则.mdc 的版本对比对象（铁律版权威源·按 SKILL.md 1f 原文）
RULES_AUTHORITY = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则", "用户基本规则-铁律版.md")
# 需检查的规则.mdc 清单（1f 原文：用户基本规则.mdc 等 alwaysApply 文件·实测 .workbuddy/rules 实际命名；
# 快照类 .mdc 为日期格式无版本号，不纳入）
RULE_FILES = ["用户基本规则-铁律版.mdc", "用户基本规则-摘要版.mdc"]

# 版本号提取：优先 frontmatter `version: "X.Y"`，回退正文 `> 版本：vX.Y`（实测铁律版格式）
VERSION_PATTERNS = [r'^version:\s*"?([\d.]+)"?', r'版本：v?([\d.]+)']

def extract_version(path):
    """提取版本号：逐个模式尝试（frontmatter version: → 正文 版本：vX.Y）"""
    try:
        with open(path, encoding="utf-8") as f:
            head = f.read(4000)
    except OSError:
        return None
    for pat in VERSION_PATTERNS:
        m = re.search(pat, head, re.MULTILINE)
        if m:
            return m.group(1)
    return None

def main():
    if not os.path.exists(AUTHORITY):
        print(f"❌ 权威源不存在: {AUTHORITY}")
        return 1
    auth_v = extract_version(AUTHORITY)
    if not auth_v:
        print(f"❌ 权威源版本号提取失败: {AUTHORITY}")
        return 1
    print(f"权威源 SKILL.md 版本: v{auth_v}")

    # ① 版本门禁（1c）：权威源 vs 各平台缓存
    # ⚠️可比对性（D①）：1e 软链接自愈使各平台缓存普遍是指向权威源的软链——同 inode 的路径
    # 读的是同一份文件，比对自身必然"一致"，无独立鉴别力。故先 realpath 去重：
    # 与权威源同源者记为「软链同源」（不充当验证样本），仅对真实独立副本做版本比对，
    # 并如实报告独立来源数——独立副本为 0 时本项降级为「权威源可达性」检查，不谎称跨平台一致。
    auth_real = os.path.realpath(AUTHORITY)
    mismatch = []
    linked = []       # realpath == 权威源 → 同一文件，天然一致
    independent = {}  # realpath → 展示名，真实独立副本（多别名去重，只比对一次）
    missing = 0
    for p in CACHE_PATHS:
        # 平台名取第 3 级父目录（~/.qoder/skills/<skill>/SKILL.md → .qoder）——
        # 取第 2 级只会得到恒为 "skills" 的无区分度标签，无法定位是哪个平台
        label = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))
        if not os.path.exists(p):
            missing += 1
            continue  # 缓存无文件 = 🟡 提示需同步，不阻塞（1c 表）
        rp = os.path.realpath(p)
        if rp == auth_real:
            linked.append(label)
            continue
        independent.setdefault(rp, label)
    for rp, label in independent.items():
        cv = extract_version(rp)
        if cv is None:
            # 2026-09-20 回灌群友实测（.qoder 缓存 vNone 事故）：提不出版本 ≠ 版本不一致，
            # 分开说清——门禁仍拦（坏缓存同样该覆盖），但不再输出莫名其妙的 vNone。
            mismatch.append(f"{label}: 版本无法解析（缓存文件为空或非 SKILL 格式→按过期处理）")
        elif cv != auth_v:
            mismatch.append(f"{label}: v{cv}（权威源 v{auth_v}）")
    if mismatch:
        print(f"❌ 缓存版本异常 {len(mismatch)} 个: " + " | ".join(mismatch))
        print("   → 备份旧版到记忆琥珀 → 读权威源覆盖缓存 → 从步骤1重新执行（脚本闸门·exit 2）")
        return 2
    print(f"✅ 版本门禁通过：权威源 v{auth_v} 可达；独立副本 {len(independent)} 个比对一致，"
          f"软链同源 {len(linked)} 个，缺失 {missing} 个跳过（共配置 {len(CACHE_PATHS)} 个路径）")
    if not independent:
        print(f"   ℹ️ 本机无独立缓存副本 → 本项等价于「权威源可达性」检查，不构成跨平台一致性验证"
              f"（软链同源: {', '.join(linked) if linked else '无'}）")

    # ② 规则.mdc 一致性（1f）：头部版本 vs 铁律版权威源
    if not os.path.isdir(RULES_DIR):
        print("🟢 规则.mdc 跳过（.workbuddy/rules 不存在，可能已迁移）")
        return 0
    auth_rule_v = extract_version(RULES_AUTHORITY) if os.path.exists(RULES_AUTHORITY) else None
    stale = []
    for name in RULE_FILES:
        p = os.path.join(RULES_DIR, name)
        if not os.path.exists(p):
            continue  # 文件不存在 = 🟢 跳过（1f 表：可能已迁移）
        rv = extract_version(p)
        if rv != auth_rule_v:
            stale.append(f"{name}: v{rv}（权威源 v{auth_rule_v}）")
    if stale:
        for s in stale:
            print(f"  ⛔ {s}")
        print(f"❌ 规则.mdc 过期 {len(stale)} 个 → 在报告输出中标注\"规则文件过期\"（脚本闸门·exit 3）")
        return 3
    print(f"✅ 规则.mdc 一致性通过：{len(RULE_FILES)} 个候选全部同步（权威源 v{auth_rule_v}）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
