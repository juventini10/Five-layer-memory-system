#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
systemlog_gate_check.py — 结构健康门禁五条封装（守卫类·按需部署）
设计依据: system-logger SKILL.md「结构健康门禁」节（v3.9.2→v3.9.4 四条·v3.10.0 封装合一·v3.10.17 补第五查）
职责: 写前五查合一——①一级标题唯一 ②今日概览唯一 ③体积<800KB ④normalize_tool.py exit 0
      ⑤本 Skill 正文完整（SKILL.md ≥200 行）。
      判定逻辑从 AI 手跑多条命令移入脚本 → AI 只读 exit code（机械断言·假执行伪装不了）。
用法:
  python3 systemlog_gate_check.py [日志文件路径]   # 五查合一，全过 exit 0
  python3 systemlog_gate_check.py                  # 无参=今日日志（自动定位）
退出码语义:
  0 = 五查全过
  1 = 通用错误（文件不存在等）
  2 = 一级标题异常（h1 ≠ 1：不存在/重复 = 整体重贴结构病）
  3 = 今日概览异常（概览 ≠ 1）
  4 = 体积超限（≥800KB = 膨胀）
  5 = normalize_tool.py 未过（工具名违规/重复组 = 层级错位/组头重复）
  6 = SKILL.md 正文塌陷（< 200 行或不存在 = 执行规范整体丢失·静默事故的机械可见化）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, subprocess
from datetime import date

HOME = os.path.expanduser("~")
SYSLOG_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "工作日志", "系统日志")
SIZE_LIMIT = 800 * 1024  # 800KB
# 第五查阈值取"最低合法正文量"而非当前值——瘦身是常态，绑当前值=每次瘦身都要改数字
SKILL_MIN_LINES = 200

def resolve_log_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    d = date.today().isoformat()
    return os.path.join(SYSLOG_DIR, f"系统日志_{d}.md")

def count_matches(path, pattern):
    r = subprocess.run(["grep", "-c", pattern, path], capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0

def main():
    path = resolve_log_path()
    if not os.path.exists(path):
        print(f"❌ 日志文件不存在: {path}")
        return 1

    # ① 一级标题唯一（整体重贴结构病）
    h1 = count_matches(path, "^# 系统日志")
    if h1 != 1:
        print(f"❌ 一级标题检查未过：'# 系统日志' 出现 {h1} 次（须==1·整体重贴结构病）→ 治理：备份记忆琥珀→按一级标题整块去重→回验")
        return 2

    # ② 今日概览唯一
    ov = count_matches(path, "^## 今日概览")
    if ov != 1:
        print(f"❌ 今日概览检查未过：'## 今日概览' 出现 {ov} 次（须==1）→ 治理：按条目工具字段重组→回验")
        return 3

    # ③ 体积上限（膨胀）
    size = os.path.getsize(path)
    if size >= SIZE_LIMIT:
        print(f"❌ 体积检查未过：{size} 字节（须 <800KB·膨胀）→ 治理：备份记忆琥珀→按一级标题整块去重→回验")
        return 4

    # ④ normalize_tool.py（工具名 allowlist + 重复组检测·复用既有脚本）
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "normalize_tool.py")
    r = subprocess.run([sys.executable, script, path], capture_output=True, text=True)
    print(r.stdout, end="")
    if r.returncode != 0:
        print("❌ 工具名/重复组检查未过（normalize_tool.py exit ≠ 0）→ 治理：按 SKILL.md「工具名规范」节归一 + 组头唯一性规则合并")
        return 5

    # ⑤ 本 Skill 正文完整性（v3.10.17·2026-08-27 00:03 提交把 632 行正文清空且过了全部既有守卫）
    #    经 realpath 定位——各端 SKILL.md/脚本均为软链到唯一源，须穿透软链才能找到同源的 SKILL.md
    skill_md = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir, "SKILL.md")
    if not os.path.exists(skill_md):
        print(f"❌ 正文完整性检查未过：SKILL.md 不存在（{skill_md}）→ 治理：从 git 最后完整版复原")
        return 6
    with open(skill_md, encoding="utf-8") as f:
        skill_lines = sum(1 for _ in f)
    if skill_lines < SKILL_MIN_LINES:
        print(f"❌ 正文完整性检查未过：SKILL.md 仅 {skill_lines} 行（须 ≥{SKILL_MIN_LINES}）="
              f"执行正文（写入流程/工具名规范/概览派生/追加姿势）已塌陷 → "
              f"治理：git log 定位最后完整版 → 复原正文 → 重新套用本次真实增量（⛔只补被删的行、不覆盖式重写）→ 回验")
        return 6

    print(f"✅ 门禁五查全过：h1=1 / 概览=1 / {size}B<800KB / normalize exit 0 / SKILL.md {skill_lines}行 — {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
