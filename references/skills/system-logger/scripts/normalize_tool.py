#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalize_tool.py — 工具名 allowlist 机械断言（S017 门槛自锁·C-030 落地）
设计依据: system-logger SKILL.md「🔒 工具名规范」节 allowlist（唯一权威源·v3.6.7）
职责: 校验系统日志文件中所有 `## [工具名]` 章节标题 ∈ allowlist 规范名。
      v0.2（2026-08-08）：新增重复组检测——同一工具名出现 >1 次 = 结构病（多端追加重复组头实证·QCN 治理）。
      v0.3（2026-08-09）：M4审查候选修复——变体映射补齐5个SKILL.md已文档化变体（千问办公/Wukong AI/growth-box/成长箱Skill/Trae Solo）+ `key in ALLOWLIST` 拉丁侧恒假判定改归一比对+死代码清除。
      ⛔本脚本只校验不改写（语义活归 AI·机械断言只做闸门）——与 kb_concept_lint 零直写同理。
用法:
  python3 normalize_tool.py [日志文件路径]   # 校验指定文件，全过 exit 0，违规 exit 1
  python3 normalize_tool.py                  # 无参=校验今日日志（自动定位）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re
from datetime import date
from collections import Counter

HOME = os.path.expanduser("~")
# MC 由脚本落点向上推导（scripts→system-logger→技能配置→MC）：⛔"HOME+目录名"字面量形态
# ——Win 装机态 _fill 会把反斜杠路径填进 .py 源码字符串，\a/\b 等被 Python 转义语义吃掉
#（真机实证 2026-10-11：OSError WinError 123 'D:\x07'·任务卡 Win对等 T19 逮出）
_MC = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, os.pardir))
SYSLOG_DIR = os.path.join(_MC, "工作日志", "系统日志")

# allowlist 规范名（⚠️ 本文件=工具表的唯一物理住所·机器真源。systemlog_normalize_fix.py 经 import
# 消费本表；SKILL.md「工具名规范」表格仅为文档投影。新增端只改这里+SKILL.md投影，⛔DO NOT 在其他脚本内联副本）
ALLOWLIST = {
    "WorkBuddy", "Qoder Desktop", "Qclaw", "Trae", "Trae Work", "QoderWork",
    "Qoder CN", "Qwen Work", "AutoClaw", "LobsterAI", "ZCode", "悟空", "成长箱", "Hermes",
    "DeepSeek Harness", "TeleAgent",
    "系统守护",  # v3.11.0 清零批#6：watch 自愈条目归因载体（18 规范名）
    "豆包办公",  # 2026-09-30 你裁定统一用"豆包办公"（推翻 v3.12.1 定名的"豆包"·规范名换字面·旧名"豆包"降为变体·D28 建组裁决由你确认有效）
    "童灵思考",  # v1.2 2026-09-05：童灵反思→童灵思考更名（你裁定·反思带认错偏置·思考=最大集合覆盖收获/发现/确认/复盘全光谱·独立模块⛔不依托任何工具/端·W1 契约⑦ --reflection 通道前缀·非端段）
    "WorkBuddy AI",  # v3.15.0 2026-09-11：WorkBuddy AI 国际版端规范名（第18端·与国内版同代码双发行版·数据根 ~/.workbuddy-ai/）
    "CatPaw",  # v3.14.1 2026-09-06：CatPaw 端（第17端·布洛陀能力基座端·美团 CatPaw 桌面端·L7 ✅·无 Hook 走 Skill 软约束·k2_core_path=USER.md）
    "Zwork",  # v3.16.0 2026-09-24：Zwork 端（AutoClaw 新客户端·zwork 运行时·你定名·软约束端·平台 Memory 为唯一机制级跨会话记忆·端徽标🧠·宪法=记忆蓝图/02_设计理念/02-平台端适配类/Zwork布洛陀设计哲学/）
    "Trae CN",  # 2026-10-09 你令：合并单端定名 Trae CN（原 TraeCode/历史组"Trae"保留·新条目用本名）
}

# 归一判定：小写+去空格+去emoji/符号 → 匹配即视为合规变体（脚本校验允许变体存在但提示）
def norm_key(name: str) -> str:
    return re.sub(r"[\W_]", "", name).lower()

# 变体→规范名的映射（从 SKILL.md 变体列提取，供报告参考）
VARIANTS = {
    "系统守护v": "系统守护", "sysguard": "系统守护", "watch": "系统守护", "systemlogwatch": "系统守护", "写时守护": "系统守护",
    "workbuddy": "WorkBuddy", "wb": "WorkBuddy",
    "workbuddyai": "WorkBuddy AI", "wbai": "WorkBuddy AI",
    "qoderdesktop": "Qoder Desktop", "qoder": "Qoder Desktop",
    "qclaw": "Qclaw", "trae": "Trae", "traesolo": "Trae", "traecn": "Trae CN",  # traecn=2026-10-09 合并单端定名
    "traework": "Trae Work", "traeworksolo": "Trae Work",
    "qoderwork": "QoderWork", "qodercn": "Qoder CN",
    "qwenwork": "Qwen Work", "千问办公": "Qwen Work",
    "autoclaw": "AutoClaw",
    "lobsterai": "LobsterAI",
    "deepseekharness": "DeepSeek Harness", "dsh": "DeepSeek Harness", "黑鲸": "DeepSeek Harness",
    "zcode": "ZCode", "wukong": "悟空", "wukongai": "悟空",
    "growthbox": "成长箱", "成长箱skill": "成长箱",
    "hermes": "Hermes", "hermesagent": "Hermes", "🪶": "Hermes", "羽毛笔": "Hermes",
    "teleagent": "TeleAgent", "tele": "TeleAgent", "星辰超级智能体": "TeleAgent", "星辰": "TeleAgent",
    "doubao": "豆包办公", "豆包": "豆包办公", "豆包work": "豆包办公", "doubaowork": "豆包办公", "字节豆包": "豆包办公",  # 2026-09-30 你令：统一豆包办公，"豆包"反转为变体
    "catpaw": "CatPaw", "catpawdesk": "CatPaw", "布洛陀能力基座": "CatPaw",
    "zwork": "Zwork", "zw": "Zwork", "autoclaw新客户端": "Zwork",
    "童灵": "童灵思考", "doenglingz": "童灵思考", "tl": "童灵思考", "童灵反思模块": "童灵思考", "童灵反思": "童灵思考",  # v1.2：反思→思考更名·旧字样容错归新名
}

def resolve_log_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    d = date.today().isoformat()
    return os.path.join(SYSLOG_DIR, f"系统日志_{d}.md")

def main():
    path = resolve_log_path()
    if not os.path.exists(path):
        print(f"❌ 日志文件不存在: {path}")
        return 1
    text = open(path, encoding="utf-8").read()
    # 提取所有 `## [工具名]` 章节标题（任务记录章节）
    # 兼容两种格式：`## WorkBuddy`（实测·8/5日志）与 `## [WorkBuddy]`（SKILL.md文档）
    tools = re.findall(r"^##\s+\[?([^\]\n]+?)\]?\s*$", text, re.M)
    tools = [t.strip() for t in tools if t.strip() and "概览" not in t and "任务记录" not in t and t.strip() != "📋"]
    if not tools:
        print(f"✅ 无任务章节（今日无日志或纯概览）: {path}")
        return 0
    # 重复组检测（v0.2·2026-08-08·多端追加重复组头结构病）——同工具组头必须唯一
    counts = Counter(tools)
    dups = {t: c for t, c in counts.items() if c > 1}
    if dups:
        for t, c in dups.items():
            print(f"  ⛔ [{t}] 重复组（出现 {c} 次）——同工具组头必须唯一，按 SKILL.md「组头唯一性规则」合并")
        print("❌ 重复组检测未通过——组头唯一性被破坏")
        return 1
    violations = []
    ok = 0
    for t in tools:
        if t in ALLOWLIST:
            ok += 1
            continue
        key = norm_key(t)
        matched = next((a for a in ALLOWLIST if norm_key(a) == key), None)
        if matched:
            # 大小写/格式变体：仍算违规（SKILL.md 要求落盘规范名），但给出建议
            # v0.3·M4：原 `key in ALLOWLIST` 对拉丁规范名恒假（混合大小写集合 vs 小写key）→改归一比对；死代码表达式 `t if False else key` 一并清除
            violations.append((t, f"格式变体→应为 {matched}"))
        elif key in VARIANTS:
            violations.append((t, f"变体→应为 {VARIANTS[key]}"))
        else:
            violations.append((t, "未知工具名（未入 allowlist）"))
    print(f"工具章节总数: {ok + len(violations)} | 合规: {ok} | 违规: {len(violations)}")
    if violations:
        for t, hint in violations:
            print(f"  ⛔ [{t}] {hint}")
        print("❌ 工具名 allowlist 校验未通过——按 SKILL.md「工具名规范」节归一后重跑")
        return 1
    print(f"✅ 工具名 allowlist 校验通过（全部 ∈ {len(ALLOWLIST)} 规范名）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
