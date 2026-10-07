#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_index_pointer.py v1.1.0 — 加漂移检测（C-100 闭环）+ 自测

## 为什么要升（童灵 D3 评估「三层是否最优」的结论·立场卡 #S903 判据）
三层方案（manifest 真源 → audit 审计器 → 生成式指针卡）**方向正确**——
符合 #S903「单一写入口 + 派生·⛔不独立手写同一改动的描述」。
但评估出**两个真缺陷**：

### 缺陷① GUARD_INDEX 无漂移检测（C-100 改动闭环律）
manifest 变了（registrar 入册/退役）而指针卡没重生成 ⇒ **卡静默过期**：
AI 照过期卡找守卫 ⇒ 找不到新入册的、或照着已退役的找。
**C-100 要求：改了就 bump，不一致要能机械判出来。**
⇒ v1.1.0 加 `--check`：重生成到内存·与盘上逐字节比对·不一致 ⇒ **exit 1**（Fail-Closed）。

### 缺陷② 守卫规范零处提及 GUARD_INDEX（C-100 同步面）
新建生成物却没在判据真源登记 ⇒ **没人知道它存在** ⇒ C-100 未满足
⇒ 本轮补登记（同批 `reg_*.py`）+ 本脚本 §导航 自带指针 + 纪律第1条点名。

## C4/C7 自证（本脚本对自己）
· ⛔ C4 恒真：`--check` 若永不变红则无用 ⇒ `--selftest` 证明「改 manifest ⇒ 必红」
· ⛔ C7 恒假：逐字节比对若总误报则不可用 ⇒ `--selftest` 证明「无改动时必绿」

## 本卡为何是生成物而非人写的清单
立场卡 #S903：同一改动的描述在 N 处独立书写 = N-1 份漂移源。
链条：registrar（单一写入口）→ manifest（机器真源）→ 本卡（**纯派生**）⇒ N=1。
⭐ 落点论证（实测·⛔推翻「塞进 MEMORY」这个默认想法）：
AI 每轮**只读** `SOUL.md`(5767字) + `memories/MEMORY.md`——全项目唯二常驻文件，
登记表放哪都不会被自动读到；且 MEMORY 实测 **2184/2200 字符·仅剩 16 字符**，
塞 200+ 条（≈11500 字符）超上限 3 倍 ⇒ 不可行。
⇒ 正解=放脚本目录根部（`ls` 第一眼可见）+ 首行声明是入口 + ⛔常驻层只挂一条指针。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

__version__ = "v1.1.0"
DEV = os.path.expanduser("[记忆共享中心]/脚本中心")
SC = os.path.expanduser("[记忆共享中心]/脚本中心")
MANIFEST = os.path.join(DEV, "scripts_manifest.json")
OUT = os.path.join(DEV, "GUARD_INDEX.md")
TEMP_PAT = re.compile(r"^(_cards_|_gen_round|_gen_subbatch|_step\d|_gen_20|__init__|_batch)")
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


def load(manifest_path=MANIFEST):
    d = json.load(open(manifest_path, encoding="utf-8"))
    raw = d.get("scripts", [])
    if isinstance(raw, dict):
        items = [dict(v, name=k) if isinstance(v, dict) else {"name": k} for k, v in raw.items()]
    else:
        items = [x for x in raw if isinstance(x, dict)]
    return d, items


def render(manifest_path=MANIFEST):
    """从 manifest 机械渲染指针卡全文（⛔纯派生·⛔不读盘上 GUARD_INDEX）

    ⚠️ 每次调用都重新读 manifest ⇒ `--check` 才能判出「manifest 变了·卡没重生成」。
    """
    d, items = load(manifest_path)
    by_fam = {}
    for it in items:
        fam = it.get("family") or "待分类"
        by_fam.setdefault(fam, []).append(it)

    # 按目录聚合（"这个守卫在哪"比"它叫什么"更常被问）
    by_dir = {}
    for it in items:
        p = str(it.get("path") or "")
        d0 = "/".join(p.split("/")[:2]) if "/" in p else p
        by_dir.setdefault(d0, []).append(it)

    L = []
    A = L.append
    A("# 🛡 守卫清单指针卡（GUARD_INDEX）")
    A("")
    A("> 🤖 **AI 读到这里就够了**——本卡由 `guard_index_pointer.py` 从 "
      "`scripts_manifest.json` **机械生成**，⛔不要手工编辑（手改必漂）。")
    A(">")
    A("> ⛔ 你**不需要通读本卡**。按任务用下面三条命令之一取你真正要的东西。")
    A("")
    A("## 🚀 三条命令（按意图选一条，别通读）")
    A("")
    A("| 我要做的事 | 命令 |")
    A("|:--|:--|")
    A("| **找某个功能的守卫** | `grep -i '<关键词>' [记忆共享中心]/脚本中心/GUARD_INDEX.md` |")
    A("| **登记/对账有没有漏** | `python3 [记忆共享中心]/脚本中心/guard_registry_audit.py` |")
    A("| **直接看机器真源** | `python3 -c \"import json,os;print(len(json.load(open(os.path.expanduser"
      "('[记忆共享中心]/脚本中心/scripts_manifest.json')))['scripts']))\"` |")
    A("")
    A("## 🧭 导航")
    A("")
    A("- **判据真源（写守卫前必读）**：`记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md`"
      " §四 注册表 · §3.9 变异测试 · §3.3 抗体生命周期")
    A("- **登记执行器**：`manifest_registrar.py --add <绝对路径> --apply`"
      "（⛔ 不手抄 JSON；新脚本默认 dry-run，须显式 `--apply`）")
    A("- **审计器**：`guard_registry_audit.py`（三问：未入册 / dangling / 新建未登记）")
    A("- **抗体覆盖率尺**：`iron_rule_antibody_coverage_guard.py`"
      "（三载体口径·`--scan-audit` 输出载体差集）")
    A("")
    A("## 📊 当前读数")
    A("")
    A("| 项 | 值 |")
    A("|:--|:--|")
    A("| 在册脚本总数 | **%d** |" % len(items))
    A("| manifest generated | %s |" % d.get("generated", "?"))
    A("| 分类数 | %d |" % len(by_fam))
    A("| 目录数 | %d |" % len(by_dir))
    A("")
    A("**⚠️ 口径说明**：`family` 为「待分类」= registrar 的 fail-closed 默认"
      "（新条目属性待补，⛔不是故障）。全量字段以 manifest 为准，本卡只做导航。")
    A("")
    A("## 📁 按目录（\"这个守卫在哪\"——最常问）")
    A("")
    A("| 目录 | 脚本数 | 名单 |")
    A("|:--|--:|:--|")
    for d0 in sorted(by_dir, key=lambda x: -len(by_dir[x])):
        names = sorted(x.get("name", "?") for x in by_dir[d0])
        shown = ", ".join("`%s`" % n for n in names[:8])
        more = " …+%d" % (len(names) - 8) if len(names) > 8 else ""
        A("| `%s` | %d | %s%s |" % (d0, len(names), shown, more))
    A("")
    A("## 🏷 按分类")
    A("")
    A("| family | 数 |")
    A("|:--|--:|")
    for fam in sorted(by_fam, key=lambda f: -len(by_fam[f])):
        A("| %s | %d |" % (fam, len(by_fam[fam])))
    A("")

    # ── 功能导航：AI 找东西要的是「哪个守卫管这件事」·不是「有 N 个文件」──
    # ⚠️ 这层是**关键词→文件名**的映射·⛔ 不是判定（判定在 verifier·见纪律第4条）
    A("## 🧲 功能导航（找守卫按关键词·不是按文件名）")
    A("")
    A("> ⛔ 本表是**寻址捷径**（关键词→文件），⛔ 不是「这个脚本真守什么」的判定。"
      "判定属 `iron_rule_antibody_verifier.py`（须回读源码）。")
    A("")
    KW = [
        ("铁律 / 抗体 / 覆盖率",
         ["iron_rule", "antibody", "coverage"]),
        ("登记 / manifest / 孤儿",
         ["manifest", "registrar", "orphan"]),
        ("版本 / TTL / 时效",
         ["version", "ttl", "expiry", "fresh"]),
        ("引用 / 路径 / 可达性",
         ["reference", "path", "selfcontained", "reachab"]),
        ("自测 / 变异 / 退化",
         ["selftest", "mutation", "degener"]),
        ("跨端 / 串端 / 隔离",
         ["crossend", "isolation", "cross_type"]),
        ("知识库 / 立场卡 / 召回",
         ["kb_", "search_kb", "audit_search", "recall", "lint"]),
        ("系统日志 / changelog",
         ["changelog", "systemlog", "commit"]),
        ("成长箱 / 反哺",
         ["growth", "antibody_guard", "feedback"]),
        ("跨端接入 / 端健康",
         ["hermes_", "twin_", "plugin_health"]),
    ]
    names_all = sorted(x.get("name", "") for x in items)
    for label, kws in KW:
        hits = [n for n in names_all if any(k in n.lower() for k in kws)]
        if not hits:
            A("| **%s** | — |" % label)
            continue
        A("| **%s** | %s |" % (label, ", ".join("`%s`" % h for h in hits[:6])
                              + (" …+%d" % (len(hits) - 6) if len(hits) > 6 else "")))
    A("")
    A("## ⚠️ 纪律（⛔四条）")
    A("")
    A("1. ⛔ **不手抄路径进本卡**——本卡是生成物，手改必漂；改 manifest 或跑 `--add`。")
    A("2. ⛔ **不把清单塞进 MEMORY/SOUL**——实测 MEMORY 只剩 %d 字符预算，"
      "塞 200+ 条必超上限；常驻层只放**一条指针**指向本卡。" % 16)
    A("3. ⛔ **不把「未入册」直接当「漏登」**——审计器会分档："
      "一次性产物 / 成熟期豁免 / 第三方·别端·引擎子脚本 都不是漏登。")
    A("4. ⛔ **不把本卡的「功能导航」当判定**——它只是关键词寻址；"
      "「这个脚本真守什么」须回读源码，判定权在 `iron_rule_antibody_verifier.py`。")
    A("")
    A("---")
    A("")
    # ⚠️ 2026-10-01 23:47 真机抓出：⛔ 卡尾**不可嵌生成时间戳**。
    #   原写 `于 <now> 机械生成` ⇒ 每次 render() 时间都变 ⇒ `--check` 逐字节比对
    #   **永远判为漂移** = C7 恒假（假红）。自测没抓到：夹具两次生成在同一秒内·时间戳相同。
    #   ⇒ 改为**版本指纹**（只随脚本版本变·⛔不随时间变）：
    #     脚本升版 ⇒ 指纹变 ⇒ check 红（这才是真漂移·C-100 要求）
    #     时间流逝 ⇒ 指纹不变 ⇒ check 绿（⛔ 不错报）
    A("<!-- 本文件由 guard_index_pointer.py %s 机械生成 · 勿手改 -->" % __version__)
    A("")
    return "\n".join(L)


def selftest():
    """C4/C7 自证：①无改动必绿(防C7恒假) ②改manifest必红(防C4恒真) ③可恢复 ④幂等"""
    tmpd = tempfile.mkdtemp(prefix="gip_")
    mf = os.path.join(tmpd, "m.json")
    out = os.path.join(tmpd, "GUARD_INDEX.md")
    base = {"scripts": [{"name": "a_guard.py",
                          "path": os.path.expanduser("[记忆共享中心]/脚本中心/a_guard.py"),
                          "family": "守卫"}],
            "generated": "2026-10-01"}
    ok = True

    def chk(manifest, outfile):
        fresh = render(manifest)
        if not os.path.isfile(outfile):
            return 1, "缺卡"
        cur = io.open(outfile, encoding="utf-8").read()
        same = (fresh == cur)
        return (0 if same else 1), ("一致" if same else "不一致")

    io.open(mf, "w", encoding="utf-8").write(json.dumps(base, ensure_ascii=False))
    io.open(out, "w", encoding="utf-8").write(render(mf))
    rc1, w1 = chk(mf, out)
    print("%s ①无改动时 check=0（防 C7 恒假误报）  rc=%d %s"
          % ("PASS" if rc1 == 0 else "FAIL", rc1, w1))
    ok = ok and rc1 == 0

    base2 = json.loads(json.dumps(base))
    base2["scripts"].append({"name": "b_guard.py",
                              "path": os.path.expanduser("[记忆共享中心]/脚本中心/b_guard.py"),
                              "family": "守卫"})
    io.open(mf, "w", encoding="utf-8").write(json.dumps(base2, ensure_ascii=False))
    rc2, w2 = chk(mf, out)
    print("%s ②manifest变更后 check=1（防 C4 恒真）  rc=%d %s"
          % ("PASS" if rc2 == 1 else "FAIL", rc2, w2))
    ok = ok and rc2 == 1

    io.open(out, "w", encoding="utf-8").write(render(mf))
    rc3, w3 = chk(mf, out)
    print("%s ③重生成后 check=0（可恢复）  rc=%d %s"
          % ("PASS" if rc3 == 0 else "FAIL", rc3, w3))
    ok = ok and rc3 == 0

    a, b = render(mf), render(mf)
    print("%s ④幂等（连续两次逐字节一致）" % ("PASS" if a == b else "FAIL"))
    ok = ok and (a == b)

    # ⑤ 卡尾禁嵌时间戳（2026-10-01 23:47 真机抓到的 C7 恒假）
    #   病：原卡尾写 `于 <now> 机械生成` ⇒ 每次 render 时间都变 ⇒ check 永远红。
    #   ⛔ 本用例不 sleep（慢）·改为直接断言卡尾**不含日期时间形态**。
    txt = render(mf)
    tail = [ln for ln in txt.splitlines() if "guard_index_pointer.py" in ln and "机械生成" in ln]
    has_ts = bool(tail) and bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{2}:\d{2}", tail[-1]))
    print("%s ⑤卡尾无时间戳（防 C7 恒假·时间流逝不得判红）  %s"
          % ("PASS" if not has_ts else "FAIL",
             (tail[-1][-40:] if tail else "<无尾行>")))
    ok = ok and not has_ts

    shutil.rmtree(tmpd, ignore_errors=True)
    print("selftest: %s" % ("5/5 全绿" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="守卫清单指针卡生成器（生成物·勿手改）")
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="漂移检测：卡与 manifest 不一致 ⇒ exit 1（C-100 闭环·Fail-Closed）")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    txt = render(a.manifest)
    if a.check:
        if not os.path.isfile(a.out):
            print("❌ 指针卡不存在：%s（跑一次生成）" % a.out, file=sys.stderr)
            return 1
        cur = io.open(a.out, encoding="utf-8").read()
        if cur == txt:
            print("✅ 指针卡与 manifest 一致（无漂移）")
            return 0
        print("❌ 指针卡已漂移：manifest 变了但卡未重生成", file=sys.stderr)
        print("   修：python3 %s" % __file__, file=sys.stderr)
        return 1
    with io.open(a.out, "w", encoding="utf-8") as f:
        f.write(txt)
    print("✅ 已生成 %s（%d 行·%d 字符）" % (a.out, txt.count("\n") + 1, len(txt)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())