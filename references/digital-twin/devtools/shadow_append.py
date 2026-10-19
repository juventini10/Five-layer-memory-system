#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/shadow_append.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""shadow_append.py v1.0.0 — SHADOW.md 合法写入口（解锁→段内插入→回锁·append-only 语义保护）

根因（与 changelog_append v1.0.0 同源）：SHADOW.md 曾被 0444 无主锁锁定，且全系统
没有任何脚本负责解锁写入它——AI 手工 Write/Edit 必 permission denied，导致潜意识层
写入管线自 2026-09-03 后断裂。本脚本补上"解锁→插入→回锁"机制，与 changelog_append
同构，使 SHADOW 写入成机制、不靠 AI 记得 chmod（机制代意志·对应 shadow-protocol 机械睡眠闸）。

第一性原理：要保护的是【历史不可篡改】，不是【文件不可触碰】。
三层防线分工：git 管改历史 / shadow_append 管写入语义（常态 444·校验→解锁→插入→回锁）。

用法：
  python3 shadow_append.py --date 2026-09-11 --icon 🔴 --title "..." --quadrant 未知已知 \
      --type 作息违背 --fact "..." --attribution "..." --selfcheck "✅" \
      --related "..." --count "..." [--cross "..."] [--positive "..."] [--note "..."] \
      [--source WorkBuddy] [--dry-run]
退出码：0 成功 | 2 输入校验拒绝（未触碰文件） | 3 IO/回锁失败（大声报错+手动恢复指引）
设计约束：纯 stdlib 零依赖（铁律-014 写入工具安全；坏不得堵死最后的人工通道）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import datetime
import os
import stat
import sys

DEFAULT_TARGET = os.path.expanduser("[记忆共享中心]/潜意识层/SHADOW.md")
ANCHOR_PREFIX = "## 📋 日报联动"
LOCK_MODE = 0o444
UNLOCK_MODE = 0o644


def fail(code, msg):
    print("[shadow_append]{}".format(msg), file=sys.stderr)
    sys.exit(code)


def build_block_lines(a):
    lines = []
    lines.append("### {} {} {} [{}]".format(a.date, a.icon, a.title.strip(), a.source))
    lines.append("- **认知象限**：{}".format(a.quadrant))
    lines.append("- **偏差类型**：{}".format(a.type))
    lines.append("- **事实**：{}".format(a.fact.strip()))
    lines.append("- **归因**：{}".format(a.attribution.strip()))
    lines.append("- **自查确认**：{}".format(a.selfcheck.strip()))
    if a.cross and a.cross.strip():
        lines.append("- **交叉验证**：{}".format(a.cross.strip()))
    lines.append("- **关联模式**：{}".format(a.related.strip()))
    lines.append("- **连续计数**：{}".format(a.count.strip()))
    if a.positive and a.positive.strip():
        lines.append("- **积极信号**：{}".format(a.positive.strip()))
    if a.note and a.note.strip():
        lines.append("- **注意**：{}".format(a.note.strip()))
    return lines


def main():
    ap = argparse.ArgumentParser(description="SHADOW.md 合法写入口（解锁→段内插入→回锁）")
    ap.add_argument("--date", required=True, help="条目日期 YYYY-MM-DD（机械闸触发夜）")
    ap.add_argument("--icon", default="🔴", help="图标 🔴/⚠️/✅")
    ap.add_argument("--title", required=True, help="偏差简述")
    ap.add_argument("--quadrant", default="未知已知", help="认知象限（默认未知已知）")
    ap.add_argument("--type", required=True, help="偏差类型枚举")
    ap.add_argument("--fact", required=True, help="事实（客观数据）")
    ap.add_argument("--attribution", required=True, help="归因")
    ap.add_argument("--selfcheck", default="—", help="自查确认")
    ap.add_argument("--cross", default="", help="交叉验证（可选）")
    ap.add_argument("--related", default="—", help="关联模式")
    ap.add_argument("--count", default="—", help="连续计数")
    ap.add_argument("--positive", default="", help="积极信号（可选）")
    ap.add_argument("--note", default="", help="注意（可选）")
    ap.add_argument("--source", default="WorkBuddy", help="来源端")
    ap.add_argument("--target", default=DEFAULT_TARGET, help="SHADOW.md 路径")
    ap.add_argument("--dry-run", action="store_true", help="只校验+打印，不写盘")
    a = ap.parse_args()

    # ① 输入校验（不合格 exit 2·此时文件一个字节都没动）
    if not (a.date and a.title.strip() and a.type.strip()
            and a.fact.strip() and a.attribution.strip()):
        fail(2, "[拒写] date/title/type/fact/attribution 均不能为空")
    block_lines = build_block_lines(a)
    block_text = "\n".join(block_lines) + "\n"
    if a.dry_run:
        print("[dry-run] 拟插入块:\n" + block_text)
        print("DRYRUN ok (未写盘)")
        return

    target = a.target
    if not os.path.exists(target):
        fail(3, "[拒写] 目标不存在: {}".format(target))

    # ② 读取 + 定位锚点段首行
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        fail(3, "[错误] 读取失败: {}".format(e))
    src_lines = content.split("\n")
    insert_idx = None
    for i, ln in enumerate(src_lines):
        if ln.startswith(ANCHOR_PREFIX):
            insert_idx = i + 1  # 锚点段首行之后插入（保持倒序·最新在上）
            break
    if insert_idx is None:
        fail(3, "[拒写] 未找到锚点段 '{}'——文件结构异常".format(ANCHOR_PREFIX))

    new_lines = src_lines[:insert_idx] + block_lines + src_lines[insert_idx:]
    new_content = "\n".join(new_lines)
    if new_content == content:
        fail(2, "[拒写] 插入后内容无变化（锚点定位异常）")

    # 备份（铁律-005④·改前先备份·用 cp 不 mv）
    backup = target + ".bak." + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    try:
        with open(backup, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        fail(3, "[错误] 备份失败: {}（原文件未动）".format(e))

    # ③ 解锁→写→回锁（try/finally 兜底·回锁失败=最严重模式·必须大声喊）
    try:
        cur = stat.S_IMODE(os.stat(target).st_mode)
        if cur & 0o222 == 0:            # 只读态才解锁（已是可写则不动）
            os.chmod(target, UNLOCK_MODE)
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)
        finally:
            try:
                os.chmod(target, LOCK_MODE)
            except Exception as e:
                fail(3, "[严重] 回锁失败: {} —— 文件正在裸奔！立即执行 chmod 444 '{}'".format(e, target))
    except Exception as e:
        fail(3, "[错误] 写入失败: {}\n手动恢复: 从备份 {} 还原".format(e, backup))

    # ④ 校验回锁 + 内容落地（防整体写回事故·读回验锚点与首行）
    end_mode = stat.S_IMODE(os.stat(target).st_mode)
    if end_mode != LOCK_MODE:
        fail(3, "[严重] 结束模式 {:o} != 444 —— 未回锁！".format(end_mode))
    with open(target, "r", encoding="utf-8") as f:
        final = f.read()
    first_line = block_lines[0]
    if first_line not in final or ANCHOR_PREFIX not in final:
        fail(3, "[严重] 内容校验失败——插入可能丢失。从备份 {} 还原".format(backup))
    print("INSERTED 1 entry -> {}".format(target))
    print("TIME {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("HEAD {}".format(first_line))
    print("LOCK 444 ok")
    print("BACKUP {}".format(backup))


if __name__ == "__main__":
    main()

