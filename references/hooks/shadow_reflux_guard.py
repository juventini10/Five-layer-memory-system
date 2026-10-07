#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shadow_reflux_guard.py v1.0 — 月度蒸馏回流校验（治 SHADOW 断回流）

背景：
  2026-10-02 审计发现，月度蒸馏的"月报本体"做得好好的（8月月报 9/1 执行、
  9月月报 10/1 执行且 finalize 16/16 通过），但 SHADOW.md 的「月度蒸馏统计」表
  停在 2026-07 行——8/9/10 三个月全部漏回流。
  根因：蒸馏闭环只验"月报生成了"，没验"结论回流到 SSOT"，闭环是半截的。

机制：
  对每个已过去的月份，核两件事：
    ① 该月月报/自画像是否存在（蒸馏做了没）
    ② SHADOW「月度蒸馏统计」表是否有该月行（回流了没）
  ①有②无 = 断回流 → exit 1 并列出待补月份。

用法：
  python3 shadow_reflux_guard.py           # 全量核查
  python3 shadow_reflux_guard.py --month 2026-09   # 指定月
  python3 shadow_reflux_guard.py --fix-hint         # 打印补写建议
出口：0=全部回流；1=存在断回流月份；2=SHADOW 表结构不可解析
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
from datetime import date

MC = os.path.expanduser("~")
SSOT = os.path.join(MC, "~/[记忆共享中心]/潜意识层/SHADOW.md")

# 月报/自画像可能的落点（多端命名不一，全量找）
DISTILL_DIRS = [
    os.path.join(MC, "~/[记忆共享中心]/工作日志/系统日志月度蒸馏"),
    os.path.join(MC, "~/[记忆共享中心]/最伟大的我/自画像"),
    os.path.join(MC, "~/[记忆共享中心]/记忆蒸馏"),
]


def ssot_months():
    """从 SHADOW 抽「月度蒸馏统计」表里已有的月份行。"""
    if not os.path.exists(SSOT):
        print("[shadow_reflux_guard] 🔴 SHADOW 不存在: {}".format(SSOT))
        sys.exit(2)
    with open(SSOT, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # 定位「月度蒸馏统计」到下一个 ## 为止
    m = re.search(r"##\s*📊\s*月度蒸馏统计(.*?)(?=\n##\s|\Z)", content, re.S)
    if not m:
        print("[shadow_reflux_guard] 🔴 找不到「月度蒸馏统计」段——表结构变了，需人工确认")
        sys.exit(2)
    block = m.group(1)
    return set(re.findall(r"\|\s*(20\d{2}-\d{2})\s*\|", block)), block


def distill_evidence(month):
    """该月有没有蒸馏产物（月报或自画像）。"""
    hits = []
    y, mm = month.split("-")
    for d in DISTILL_DIRS:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if month in f and f.endswith(".md"):
                hits.append(os.path.join(d, f))
    return hits


def should_check(month):
    """只查已过去的完整月份（当月不算）。"""
    y, m = int(month[:4]), int(month[5:7])
    today = date.today()
    return (y, m) < (today.year, today.month)


def main():
    args = sys.argv[1:]
    months_in_ssot, block = ssot_months()

    if "--month" in args:
        targets = [args[args.index("--month") + 1]]
    else:
        # 从第一篇有产物的月份扫到上个月
        found_any = False
        earliest = None
        for d in DISTILL_DIRS:
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                # ⛔ 教训（2026-10-02 审计实证）：初版用 re.match 匹配文件名【开头】，
                # 而真实命名是 `系统日志月度蒸馏_2026-03.md` / `自画像_2026-05.md`——
                # 月份在文件名【中间】，re.match 一律不命中 ⇒ 守卫推导出 earliest=2026-08，
                # 只检查 8/9 两个月，3 月与 5 月的断回流整段落在视野外却报 exit 0 全绿。
                # 判据改为子串搜（与同文件 distill_evidence 的 `if month in f` 同口径）。
                m2 = re.search(r"(20\d{2}-\d{2})", f)
                if m2:
                    found_any = True
                    earliest = min(earliest or m2.group(1), m2.group(1))
        if not earliest:
            print("[shadow_reflux_guard] ⚠️ 未找到任何蒸馏产物目录，无法核查")
            return 0
        ey, em = int(earliest[:4]), int(earliest[5:7])
        today = date.today()
        targets = []
        y, m = ey, em
        while (y, m) < (today.year, today.month):
            targets.append("{}-{:02d}".format(y, m))
            m += 1
            if m > 12:
                y, m = y + 1, 1

    broken = []
    skipped = []
    print("=" * 66)
    print("[shadow_reflux_guard] 月度蒸馏 → SHADOW 回流核查")
    print("=" * 66)
    print("  SHOT 已有月份行：{}".format(", ".join(sorted(months_in_ssot)) or "(无)"))
    print()

    for month in targets:
        if not should_check(month):
            skipped.append(month)
            continue
        ev = distill_evidence(month)
        has_row = month in months_in_ssot
        if has_row:
            print("  ✅ {}  已回流（证据 {} 个）".format(month, len(ev)))
        elif ev:
            print("  🔴 {}  断回流！蒸馏产物 {} 个，但 SHADOW 表无该月行".format(month, len(ev)))
            for e in ev[:3]:
                print("       证据：{}".format(os.path.basename(e)))
            broken.append((month, ev))
        else:
            print("  🟡 {}  无蒸馏产物，暂不要求回流".format(month))

    print()
    if skipped:
        print("  (跳过未结束月份：{})".format(", ".join(skipped)))
    if not broken:
        print("  ✅ 全部已结束月份均已回流")
        return 0

    print("  🔴 共 {} 个月断回流：{}".format(len(broken), ", ".join(m[0] for m in broken)))
    print("""
根因复盘（2026-10-02 实证）：
  蒸馏闭环只验"月报生成了"，没验"结论回流到 SSOT"——闭环是半截的。
  月报里的睡眠硬数据（如 9月均值 5.33h / 23天<6h）已经在别处成型，
  但 SHADOW 的偏差统计看不到，AI 读 SHADOW 做判断时就在用过期认知。

修复：按上方证据把数据补进 SHADOW「月度蒸馏统计」表 +「月度睡眠体检」段。
""")
    return 1


if __name__ == "__main__":
    sys.exit(main())