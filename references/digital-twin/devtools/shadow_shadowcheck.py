#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""shadow_shadowcheck.py v1.0 — SHADOW 真源自检（元数据新鲜度 + 锁 + 可读性）

为什么有这个（2026-10-02·铁律-002 数据截止日纪律）：
  今天审计出的三类病，只有前两类有守卫：
    · 分叉 → shadow_ssot_guard 管
    · 断回流 → shadow_reflux_guard 管
    · ⛔ 但「元数据腐化」没人管——frontmatter 的 version/date/complies_with
      与实盘脱钩（今天实证：内容已升到 v4.5，date 还写着 2026-07-19；
      complies_with 还写 v1.0.2，现行规范早已 v2.6.0）。
      这类病的特点是【不影响任何脚本跑】，所以永远不会有人发现——
      直到某天按着过期元数据去判断「这份文件多久没更新」。

判据（三条，全机械）：
  ① 真源存在 + 是实体文件 + 可读
  ② 只读锁在位（444/444 或更严）——丢了锁意味着有人手工直写过
  ③ 元数据新鲜度：frontmatter 的 date 距文件 mtime 不得超过 N 天
     （默认 30；内容改过但 date 没跟上 = 版本真相守卫会拦，这里是第二道）

⛔ 边界：本件【只读不改】。发现 date 过期不自动改——改元数据是人的动作，
  自动改会把「我改过」和「机器改过」混成一笔账，正是铁律-002 说的记不得清。

用法：
  python3 shadow_shadowcheck.py
  python3 shadow_shadowcheck.py --max-stale 14
  python3 shadow_shadowcheck.py --json
退出：0=健康；1=有异常
"""
import argparse
import json
import os
import re
import stat
import sys
from datetime import date, datetime

SSOT = os.path.expanduser("[记忆共享中心]/潜意识层/SHADOW.md")


def read_frontmatter(path):
    """取 frontmatter 键值对（简易解析，不引第三方）。"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return {}, []
    if not lines or lines[0].strip() != "---":
        return {}, []
    fm = {}
    end = 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
        m = re.match(r"^([a-zA-Z_]+):\s*(.+)$", lines[i].strip())
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, lines[end + 1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-stale", type=int, default=30, help="date 距 mtime 超过多少天算过期")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    problems = []

    # ① 存在 + 实体 + 可读
    if not os.path.exists(SSOT):
        problems.append({"kind": "缺失", "detail": SSOT, "fix": "查回收站/备份——这不是健康问题，是数据丢了"})
        return emit(problems, a.json)
    if os.path.islink(SSOT):
        problems.append({"kind": "真源成软链", "detail": SSOT, "fix": "SSOT 必须是实体文件"})

    try:
        st = os.stat(SSOT)
        mode = stat.S_IMODE(st.st_mode)
        with open(SSOT, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        problems.append({"kind": "不可读", "detail": str(e), "fix": "查权限（444 下需解锁才能写）"})
        return emit(problems, a.json)

    # ② 只读锁在位
    if mode & 0o222:
        problems.append({
            "kind": "只读锁丢失",
            "detail": "当前权限 {:o}（含写位）".format(mode),
            "fix": "chmod 444 恢复——锁没了意味着有人绕过写入口手工直写过",
        })

    # ③ 元数据新鲜度
    fm, _ = read_frontmatter(SSOT)
    mtime_day = datetime.fromtimestamp(st.st_mtime).date()
    fm_date_raw = fm.get("date", "")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", fm_date_raw)
    if not m:
        problems.append({"kind": "frontmatter date 缺失或格式非 YYYY-MM-DD",
                         "detail": repr(fm_date_raw), "fix": "补 date 字段（格式 v2.6.0 要求）"})
    else:
        fm_day = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        stale = (mtime_day - fm_day).days
        if stale > a.max_stale:
            problems.append({
                "kind": "元数据过期",
                "detail": "frontmatter date={} 但文件 mtime={}（差 {} 天 > 阈值 {}）".format(
                    fm_day, mtime_day, stale, a.max_stale),
                "fix": "内容改过就同步升 version + date（铁律-002 数据截止日纪律·⛔勿写「冻结」）",
            })

    info = {
        "path": SSOT,
        "mode": "{:o}".format(mode),
        "version": fm.get("version", "?"),
        "date": fm_date_raw or "?",
        "complies_with": fm.get("complies_with", "?"),
        "mtime": str(mtime_day),
        "size": len(content.encode("utf-8")),
        "lines": content.count("\n") + 1,
    }
    return emit(problems, a.json, info)


def emit(problems, as_json, info=None):
    if as_json:
        print(json.dumps({"info": info or {}, "problems": problems}, ensure_ascii=False, indent=2))
    else:
        print("[shadow_shadowcheck] 真源：{}".format(SSOT))
        if info:
            print("  版本={} date={} 规范={} | 权限={} mtime={} {}字节 {}行".format(
                info["version"], info["date"], info["complies_with"], info["mode"],
                info["mtime"], info["size"], info["lines"]))
        if problems:
            print("  🔴 {} 项异常：".format(len(problems)))
            for i, p in enumerate(problems, 1):
                print("    {}. [{}] {}".format(i, p["kind"], p["detail"]))
                print("       修法：{}".format(p["fix"]))
        else:
            print("  ✅ 真源健康（存在·实体·可读·444锁在位·元数据新鲜）")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())