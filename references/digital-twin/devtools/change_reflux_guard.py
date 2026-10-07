#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v1.0.0
"""change_reflux_guard.py — 改前回流指路守卫（PreToolUse Hook·advisory 不阻断）

职责：检测到即将 Edit/Write 一个"触发件"（Skill / 脚本 / 安装包 / 哲学 / 铁律 …）时，
      输出该触发件对应的"必回流清单"（读自 变更回流映射表.md），把"你人肉提醒"换成"机制提示"。

第一性原理（2026-09-19·你质询"为什么老要我记得同步"根治）：
  病根 = "改X→回流Y"的映射只住在你脑子里 → 只有你记得 → 你当人肉指路针。
  治法 = 映射外化为文件（立场卡#S1007"真相源不能依赖记忆"）+ 改前机制提示。

设计纪律（守卫家族·Hook 三条）：
  - 只提示不拦截：任何情况 exit 0（⛔不阻断你的操作）
  - 失败放行：解析失败 / 映射表缺失 / 任何异常 → 静默 exit 0
  - 保守判定：命中才提示，宁漏勿误（避免告警疲劳）

用法（PreToolUse Hook）：
  echo '{"tool_name":"Edit","tool_input":{"file_path":".../SKILL.md"}}' | python3 change_reflux_guard.py

职责边界（2026-09-19 收敛·对齐 ZCode 端）：
  本守卫 = 「回流指路」advisory——只提示"改了 X 还要同步 Y/Z"，⛔不阻断。
  同族 skill_write_gate_guard.py = 「写入门禁」——exit2 硬拦"未启动 Skill 就写管辖目录"。
  两者互补不同职：一个防"漏同步"，一个防"绕流程"；⛔不合并、不互替（01-通用规范 §补充节）。
"""
import json
import os
import re
import sys

MAP_FILE = os.path.expanduser("[记忆共享中心]/脚本中心/变更回流映射表.md")

# 触发件 → 回流清单（与映射表 §二 同源；命中任一 pattern 即提示）
RULES = [
    (r"/技能配置/[^/]+/(SKILL\.md|scripts/|references/)",
     "改 Skill", "Skill架构规范 + 指令编写规范 + 该Skill references/CHANGELOG.md"),
    (r"/skills/[^/]+/(SKILL\.md|scripts/|references/)",
     "改 Skill", "Skill架构规范 + 指令编写规范 + 该Skill references/CHANGELOG.md"),
    (r"/(开发工具|changelog-guard)/[^/]+\.(py|sh)$",
     "改布洛陀脚本", "布洛陀脚本架构设计哲学 + 对应家族设计哲学"),
    (r"/发布库/.*布洛陀-安装包/",
     "改安装包", "安装包设计哲学(01通用规范+03进度看板) + 发布包编写规范"),
    (r"/(hook|hooks)/|core_slice|k2_slice|doenglingz_inject",
     "改注入链", "注入机制设计哲学"),
    (r"知识联邦引擎|search_kb",
     "改知识库/检索", "知识库设计哲学 + 检索设计哲学"),
    (r"/(SOUL|IDENTITY)\.md$|童灵·人格规格书|/数字分身/",
     "改品格/分身", "品格设计哲学 + 数字分身设计哲学(含11-发布判据)"),
    (r"用户基本规则-(铁律版|摘要版|详解存档版)",
     "改铁律/规则三层", "铁律治理与落地规范 + 三层版本号一起升"),
    (r"/(SHADOW|00_动态状态快照)\.md$",
     "改记忆层", "MEMORY设计哲学"),
    (r"/记忆蓝图/04_系统文件设计/",
     "改设计哲学", "本域自身 + 变更回流映射表自身（新增域要登记）"),
]
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        return  # 失败放行

    tool = str(payload.get("tool_name", ""))
    if tool not in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return

    ti = payload.get("tool_input") or {}
    fp = str(ti.get("file_path", "") or "").replace("\\", "/")
    if not fp:
        return

    hits = []
    for pat, label, targets in RULES:
        try:
            if re.search(pat, fp):
                hits.append((label, targets))
        except Exception:
            continue
    if not hits:
        return

    # 输出回流提示（advisory）
    lines = [f"🔁 [改前回流指路] 检测到「{hits[0][0]}」变更 → 除本次目标外，请核对是否需同步："]
    for _, t in hits:
        lines.append(f"   • {t}")
    lines.append("   • 通例: 变更日志.md(changelog_append.py) + 系统日志")
    if os.path.exists(MAP_FILE):
        lines.append("   （全表: 记忆蓝图/04_系统文件设计/变更回流映射表.md）")
    print("\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)   # 恒定放行·⛔不阻断
