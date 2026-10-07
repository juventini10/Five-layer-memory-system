#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""guard_registry_audit.py v1.0.0 — 守卫登记三问审计（2026-10-01·皮叔令「没登记的就去登记」）

## 你的原话
「那没有登记的就去登记啊——在那个哲学脚本、哲学文件里面，要把这些脚本的相关路径给标出来啊，
  你评估一下，标在哪里是最显眼、最能够让AI能读到。」

## 取证结论（⛔推翻了我最初的方案设想·必读）
1. **AI 每轮只读 `~/.hermes/SOUL.md`(5767字) + `memories/MEMORY.md`(2184字)**——
   全项目唯二常驻文件。登记表放哪都**不会被自动读到**。
2. `memories/MEMORY.md` 实测 **2184/2200 字符，只剩 16 字符**——
   ⛔塞不进任何脚本路径（383条≈11500字符，超上限3倍）。
3. 现存三处候选落点的可达性：
   - `开发工具/README.md`（29行）— AI **ls 目录时可见**，但需主动 ls
   - `守卫编写规范 §四注册表`（L555-695·869 行大文件深埋）— AI 除非专程读否则看不到
   - `scripts_manifest.json`（3291行）— **机器读**，AI 默认不读

⇒ **结论：明细不可能也不该进 MEMORY；正解是「MEMORY 一条指针 + 机器自动触发」。**

## 本脚本的职责（登记三问·每问都可机械判）
不是"再维护一份表"（那会变成第四台双本账），而是**回答三个治理问题**：
  Q1 有多少脚本没进 manifest？（含递归·⛔只扫顶层是 2026-10-01 当日实测过的错）
  Q2 有多少 manifest 条目指向已消失的文件？（dangling）
  Q3 新建脚本有没有进 manifest？（mtime 近 N 分钟内 ⇒ 未入册＝活跃期·按 registrar 契约豁免）

## ⛔ 纪律
· 只读·不改任何文件·不自动登记（登记由 manifest_registrar.py 执行器负责·⛔不抢它的活）
· ⛔ 不自动把「未入册」判成「漏登」——须先分类（一次性卡片生成器 ≠ 守卫）
· 分类口径照抄 registrar 的设计意图：`_cards_*/_gen_round*/__init__` = 一次性产物
"""

import glob
import json
import os
import re
import sys
import time

__version__ = "v1.0.0"
DEV = os.path.expanduser("[记忆共享中心]/脚本中心")
SC = os.path.expanduser("[记忆共享中心]/脚本中心")
MANIFEST = os.path.join(DEV, "scripts_manifest.json")
REGISTRY = os.path.expanduser(
    "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md")
SETTLE_MINUTES = 10   # 与 manifest_registrar 的成熟期闸门同口径

# 一次性产物（registrar 契约③/④的同源分类·⛔这些不算漏登）
TEMP_PAT = re.compile(r"^(_cards_|_gen_round|_gen_subbatch|_step\d|_gen_20|__init__|_batch)")
# 守卫/检测族（这些漏登才是真问题）
GUARD_PAT = re.compile(r"(guard|check|verify|validate|scan|audit|lint|test)", re.I)


def collect():
    disk = {}
    for base in (DEV, SC):
        for f in glob.glob(os.path.join(base, "**", "*"), recursive=True):
            if os.path.isfile(f) and f.endswith((".py", ".sh")):
                disk.setdefault(os.path.basename(f), []).append(f)
    return disk


def manifest_names():
    """⚠️ scripts_manifest.json 的 `scripts` 是 **list[dict]**·⛔不是 dict。
    第一版把它当 dict 迭代⇒ 读数「在册 204/dangling 61」全错（2026-10-01 当日实测抓出）。
    正确读法：每条取 `name`/`path`；既有条目可能同名多路径（subfamily 复用）⇒ 用 multiset 语义。
    """
    if not os.path.isfile(MANIFEST):
        return {}, None
    d = json.load(open(MANIFEST, encoding="utf-8"))
    raw = d.get("scripts", [])
    out = {}
    if isinstance(raw, dict):            # 容错：万一结构变了要显形⛔不是静默兼容
        for k, v in raw.items():
            p = (v.get("path") if isinstance(v, dict) else k) or k
            out.setdefault(os.path.basename(str(p)), v)
        return out, d.get("generated")
    for it in raw:
        if not isinstance(it, dict) or "name" not in it:
            continue
        out.setdefault(os.path.basename(str(it.get("path") or it["name"])), it)
    return out, d.get("generated")


def main():
    print("🗂 守卫登记三问审计 %s" % __version__)
    print("起因：皮叔令「没登记的就去登记」+「标在哪最显眼·AI 能读到」")
    print("=" * 78)
    disk = collect()
    man, gen = manifest_names()
    print("\n【Q1/Q2 基数】")
    print("  磁盘脚本（递归 两目录去重）: %d" % len(disk))
    print("  manifest 在册              : %d  （generated=%s）" % (len(man), gen))
    un = sorted(set(disk) - set(man))
    dang = sorted(set(man) - set(disk))
    print("  Q1 未入册: %d    Q2 dangling（登记了·磁盘无）: %d" % (len(un), len(dang)))

    # ── 分类（⛔ 不把"未入册"直接判成"漏登"·⛔ 也不把"守卫族"直接判成"我的守卫"）──
    # ⚠️ 2026-10-01 实测踩坑修正：第一版只按 GUARD_PAT 分档 ⇒ 41 条"待登记守卫"里
    #   绝大多数**根本不是本体的守卫**——`test_*.py`/`checks.py`(Kami 第三方 SDK)、
    #   `deepseek-harness/scripts/*`(别端资产)、`知识联邦引擎/scripts/*`(引擎子脚本)。
    #   ⛔ 把"文件名像守卫"当"本体漏登的守卫"＝又一次载体/作用域双重错位。
    # ⇒ 收紧为：路径必须落在**本体治理范围**内（顶层 + 脚本中心 + 少数已登记过的子目录）
    #   才算"本体的守卫"；第三方/别端/引擎子脚本一律不判漏登。
    OWNED_PREFIX = (
        DEV + "/", SC + "/",
    )
    OWNED_SUBPAT = re.compile(
        r"/(changelog-guard|数字分身|成长箱|技能配置)/.*/(check|verify|guard|scan)_")

    def owned(path):
        if path.startswith(OWNED_PREFIX):
            # 顶层与脚本中心/ 一律 owned；子目录只在已知本体域内才 owned
            if path in (os.path.join(DEV, os.path.basename(path)),
                        os.path.join(SC, os.path.basename(path))):
                return True
            if re.match(r"^%s/[^/]+$" % re.escape(DEV), path) or \
               re.match(r"^%s/[^/]+$" % re.escape(SC), path):
                return True
            return bool(OWNED_SUBPAT.search(path))
        return False

    now = time.time()
    tmp, grd, fresh, oth, notmine = [], [], [], [], []
    for n in un:
        paths = disk[n]
        newest = max(os.path.getmtime(p) for p in paths)
        mine = [p for p in paths if owned(p)]
        if TEMP_PAT.match(n):
            tmp.append(n)
        elif not mine:
            notmine.append(n)       # ⛔ 第三方/别端/引擎子脚本·不是本体漏登
        elif (now - newest) < SETTLE_MINUTES * 60:
            fresh.append(n)          # 成熟期闸门内·按 registrar 契约豁免
        elif GUARD_PAT.search(n):
            grd.append(n)
        else:
            oth.append(n)

    print("\n【Q1 分类·照抄 registrar 契约口径】")
    print("  · 一次性产物（_cards_*/_gen_round*/__init__）: %d  ⛔不算漏登" % len(tmp))
    print("  · 成熟期内（mtime < %dmin·registrar 契约④豁免）: %d  ⛔不算漏登"
          % (SETTLE_MINUTES, len(fresh)))
    if fresh:
        print("      " + ", ".join(fresh[:5]))
    print("  · 第三方/别端/引擎子脚本 ⛔不是本体守卫: %d  （Kami SDK/deepseek-harness/知识联邦引擎 等）"
          % len(notmine))
    print("  · 守卫/检测族 ← 真·待登记: %d" % len(grd))
    for n in grd:
        print("      · %s  ← %s" % (n, os.path.relpath(disk[n][0], os.path.expanduser("~/"))))
    print("  · 其他（需人工判定是否该入册）: %d" % len(oth))

    print("\n【Q2 dangling】")
    if dang:
        for n in dang:
            print("  · %s" % n)
        print("  ⚠️ dangling 非零 ⇒ manifest 有硬漂移，须 manifest_registrar --apply 退役回路处理")
    else:
        print("  （无·差集为空）")

    # ── Q3 ──
    print("\n【Q3 新建脚本登记状态】成熟期闸门 = %d 分钟" % SETTLE_MINUTES)
    newfiles = []
    for n, paths in disk.items():
        newest = max(os.path.getmtime(p) for p in paths)
        if (now - newest) < SETTLE_MINUTES * 60:
            newfiles.append((n, n in man))
    if not newfiles:
        print("  （近 %d 分钟无新建脚本）" % SETTLE_MINUTES)
    for n, ok in newfiles:
        print("  %s %s  ← 成熟期内·豁免登记" % ("✅已入册" if ok else "⏳成熟期内", n))

    print("\n【落点评估·AI 可达性实测】")
    for label, path, note in [
        ("memories/MEMORY.md（唯一常驻·2184/2200字）",
         os.path.expanduser("~/.hermes/memories/MEMORY.md"), "⛔只剩 16 字符·塞不进路径"),
        ("SOUL.md（唯一常驻·5767 字）",
         os.path.expanduser("~/.hermes/SOUL.md"), "⛔人格规则·不放清单"),
        ("开发工具/README.md（29 行）",
         os.path.join(DEV, "README.md"), "🟡 AI ls 目录时可见·需主动 ls"),
        ("守卫编写规范 §四注册表（L555-695）",
         REGISTRY, "🟡 判据真源·但深埋 869 行大文件"),
        ("scripts_manifest.json（3291 行）",
         MANIFEST, "⚪ 机器真源·AI 默认不读"),
    ]:
        ok = "✅在" if os.path.isfile(path) else "⛔无"
        size = os.path.getsize(path) if os.path.isfile(path) else 0
        print("  %-46s %s %6d B  %s" % (label, ok, size, note))

    print("\n【本脚本⛔不做的事】")
    print("  · ⛔不自动登记——登记执行器是 manifest_registrar.py（--apply），⛔不抢它的活")
    print("  · ⛔不维护第四份清单——那是制造新的双本账")
    print("  · ⛔不改 MEMORY/SOUL——那是常驻人格层，须单独决定")
    return 0


if __name__ == "__main__":
    sys.exit(main())