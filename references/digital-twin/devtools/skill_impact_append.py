#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill_impact_append.py v1.0.0 — 技能变更审计唯一合法写入口（append-only 协议）

来源：WikiSkill 借鉴 B3（2026-09-10 你拍板落地）。联动哲学 §7.1 数据资产契约簿
新增「技能变更审计」资产行（立法位）——论文 skill-impact.md 的核心洞察：
技能变更若无程序化审计轨迹 → 提案重复 + SKILL.md 声明↔实现静默漂移
（联动哲学 KL#3 版本漂移 / KL#4 声明-实现滞后 的下游根因之一）。

第一性原理（对齐 changelog_append.py）：要保护的是【历史不可篡改】，
不是【文件不可触碰】。

与中央账（变更日志.md · 铁律-018）的分工（⛔不重复建设）：
  变更日志.md      → 全系统文件版本跃迁史（任何文件·版本号级·无被拒维度）
  技能变更审计.md  → 技能变更的决策审计（谁/何时/改什么/理由/结果/被拒记录）
                     ——「被拒记录」是账本不覆盖的独有维度（防重复提案）

用法：
  python3 skill_impact_append.py --tool "WorkBuddy" --skill "growth-box" \
      --action 修改 --reason "…" --result "…"
  被拒提案：--action 提案被拒 --rejected（该记录即防重复提案的查询依据）
退出码：0 成功 | 2 输入校验拒绝（未触碰文件） | 3 IO/回锁失败（大声报错+人工恢复指引）
设计约束：纯 stdlib 零依赖（铁律-014 写入工具安全·append-only；坏不得堵死最后的人工通道）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import datetime
import os
import stat
import sys

DEFAULT_TARGET = os.path.expanduser("~/技能变更审计.md")
LOCK_MODE = 0o444
UNLOCK_MODE = 0o644
ACTIONS = ("新增", "修改", "退役", "提案被拒")

HEADER = """# 技能变更审计

> **性质**：技能变更的决策审计台账（append-only·唯一写入口=`开发工具/skill_impact_append.py`）。
> **立法依据**：皮叔Skill联动设计哲学 §7.1 数据资产契约簿「技能变更审计」资产行（2026-09-10 B3 落地）。
> **与中央账分工**：`变更日志.md`（铁律-018）= 全系统文件版本跃迁史；本台账 = 技能变更的**决策**审计（含「被拒记录」，防重复提案）。
> ⛔ DO NOT 手工编辑本文件——一切追加走脚本（校验→按需解锁→O_APPEND→回锁 444）。

| 日期 | 执行端 | 技能 | 动作 | 理由 | 结果 |
|---|---|---|---|---|---|
"""


def fail(code, msg):
    print("[skill_impact_append]{}".format(msg), file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description="技能变更审计唯一合法写入口（append-only 协议）")
    ap.add_argument("--tool", required=True, help="执行端工具名（规范名·如 WorkBuddy）")
    ap.add_argument("--skill", required=True, help="被变更的技能名")
    ap.add_argument("--action", required=True, help="动作：{}".format("/".join(ACTIONS)))
    ap.add_argument("--reason", required=True, help="变更理由（为什么改）")
    ap.add_argument("--result", default="—", help="变更结果（做了什么/验证结论）")
    ap.add_argument("--target", default=DEFAULT_TARGET, help="台账路径（默认技能变更审计.md·可用于隔离压测）")
    a = ap.parse_args()

    # ① 输入校验（不合格 exit 2·此时台账一个字节都没动）
    today = datetime.date.today().isoformat()
    tool = a.tool.strip()
    skill = a.skill.strip()
    action = a.action.strip()
    reason = " ".join(str(a.reason).split())
    result = " ".join(str(a.result).split()) or "—"
    if not tool or not skill or not action or not reason:
        fail(2, "[拒写] --tool/--skill/--action/--reason 均不能为空")
    if action not in ACTIONS:
        fail(2, "[拒写] --action 非法值「{}」——合法值：{}".format(action, "/".join(ACTIONS)))
    row = "| {} | {} | {} | {} | {} | {} |".format(today, tool, skill, action, reason, result)
    if not row.startswith("| {} | ".format(today)) or not row.endswith(" |"):
        fail(2, "[拒写] 行格式异常：{}".format(row))

    # ② 受控追加（不存在→先建表头；按需解锁 → O_APPEND → finally 回锁）
    target = a.target
    try:
        if not os.path.exists(target):
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(HEADER)
            os.chmod(target, UNLOCK_MODE)   # 新建文件按需解锁语义（首次追加后回锁）
            print("[skill_impact_append]新建台账（含表头）: {}".format(target))
        cur = stat.S_IMODE(os.stat(target).st_mode)
        if cur & 0o222 == 0:            # 只读态才解锁（已是可写则不动）
            os.chmod(target, UNLOCK_MODE)
        needs_nl = False
        try:
            with open(target, "rb") as fb:
                fb.seek(-1, os.SEEK_END)
                needs_nl = fb.read(1) != b"\n"
        except OSError:
            pass                        # 空文件
        with open(target, "a", encoding="utf-8") as f:
            f.write(("\n" if needs_nl else "") + row + "\n")
    except Exception as e:
        fail(3, "[错误] 追加失败: {}\n手动恢复指引: chmod 644 '{}' 后人工补行:\n{}".format(e, target, row))

    # ③ 回锁断言（裸奔 = 最严重的失败模式·必须大声喊出来）
    try:
        if stat.S_IMODE(os.stat(target).st_mode) != LOCK_MODE:
            os.chmod(target, LOCK_MODE)
    except Exception as e:
        fail(3, "[严重] 回锁失败: {} —— 台账正在裸奔！立即执行: chmod 444 '{}'".format(e, target))
    end_mode = stat.S_IMODE(os.stat(target).st_mode)
    print("APPENDED {} bytes -> {}".format(len(row.encode("utf-8")), target))
    print("TIME {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("ROW {}".format(row))
    if end_mode != LOCK_MODE:
        fail(3, "[严重] 结束模式 {:o} != 444 —— 台账未回锁！".format(end_mode))
    print("LOCK 444 ok")


if __name__ == "__main__":
    main()
