#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_scan_domain_ssot.py — 守卫扫描域单一真源 + 域覆盖门禁

================================================================================
【为什么有这个件】2026-10-03·本会话「检测器自身失效」同族病第 1-4 例的根治
================================================================================

实证四例（全部同一根因：守卫各自手写扫描域，没有单一真源，漏了没人知道）：

  ① `guard_selftest_check.SCAN_ROOTS` 漏 `数字分身/{scripts,guards}`
     ⇒ 差集误报「幽灵」· 差集 79→80（补域后能看见更多真缺夹具的件）
  ② `devtools_single_source_guard` 判据④ 只扫 `live`（脚本中心）**1 个目录**
     ⇒ `数字分身/scripts` 的裸 `~/`（launchd state-bus-sync LastExitStatus=1）抓不到
  ③ 判据④ 正则只吃 `NAME = "~/…"`，**真实病灶 `os.path.join(HOME, "~/…")` 不在检测范围**
     ⇒ 长期假绿（绿 = 没人会去看 stdout）
  ④ `post_change_guard.py` L704 裸 `~/` 字符串 ⇒ 每轮在 cwd 造 `~/` 目录树（47KB）

**根因不是某一处写错，是「扫描域」这个概念散落在 8 个守卫里各写一份。**
⇒ 逐个补是打地鼠（本会话已补 2 处，仍有 6 处未知）。
⇒ 正解：**扫描域收敛到本件一个真源 + 任何守卫新增/改动扫描域必须经本件**，
         并提供 `DOMAINS` 供守卫 import（消除「各写一份」）。

--------------------------------------------------------------------------------
【本件做什么 / 不做什么】
--------------------------------------------------------------------------------
  ✅ 做：① 维护「哪些目录是守卫该管的载体」的唯一清单（DOMAINS）
          ② 对每个声明了扫描域的守卫，核它的域是否 ⊆ DOMAINS 且覆盖该管的载体
          ③ 反向夹具自测：故意漏一个域 → 本件必须判红
  ⛔ 不做：不改任何守卫的判据逻辑（本件只管「域」，不管「判得准不准」）
          不替守卫决定它该管哪些目录（那需要逐件判断，机械做不到 ⇒ 如实显形）

--------------------------------------------------------------------------------
【为什么不能复用 user_machine_fixture.RUNTIME_PATH_DIRS】
--------------------------------------------------------------------------------
  那是**安装落点**（端用户机上该有哪些目录），本件是**守卫扫描域**（本机扫描哪些）。
  ⛔ 两者混用 = 端用户机概念污染本机元层 ⇒ user_machine_fixture 已显式禁止建
  「开发工具」，理由同一。故独立成件。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import json
import os
import re
import shutil
import sys
from datetime import date

HOME = os.path.expanduser("~")
ARCHIVE = os.path.expanduser("[记忆共享中心]")
SELF = os.path.realpath(__file__)
DEVTOOLS = os.path.join(ARCHIVE, "开发工具")

# ==============================================================================
# 单一真源：守卫该管的载体目录（相对 ARCHIVE）
# ==============================================================================
# 增补纪律（⛔ 别再随手加）：
#   一个目录进这里 = 「守卫的扫描域必须覆盖它」。
#   加之前先答：① 这个目录里真的放守卫/脚本件吗？② 它是「作者侧」还是「端用户侧」？
#   端用户侧目录（脚本中心以外的落点）**不进** —— 那是 user_machine_fixture 的账。
DOMAINS = [
    "脚本中心",                              # 插件取件面（rp("devtools") 指这里）
    "开发工具",                              # 工作区/发布真源
    "数字分身/scripts",                      # ⛔ 2026-10-03 补：state-bus 等生产件住这
    "数字分身/guards",                       # ⛔ 2026-10-03 补：registry_guards 等
    "技能配置",                              # 路由家族之外的可执行件
    "自定义层/待完成工作/路由家族/scripts",    # 路由家族
    # ⛔ 2026-10-03 本件正例实跑抓到的真盲区（判据③）：
    "成就系统/scripts",                      # check_concept_achievement / check_achievements
    "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/templates",  # _template_guard
    "发布库/五层记忆系统/存档包/脱敏门禁",     # ⛔ 2026-10-03 修正：真实位置在此
                                          #   （原写 知识库/五层记忆系统/脱敏门禁·不存在
                                          #    ⇒ 判据① 抓到「又一份漂移的账」·本件自证有效）
]

# 元层守卫自身的扫描域变量名（元层守卫若声明，必须 ⊆ DOMAINS）
DOMAIN_VARS = (
    "SCAN_ROOTS", "CANDIDATE_DIRS", "SCAN_DIRS", "TARGET_DIRS",
)

# ⛔ 刻意排除：这些守卫的「域」不是「守卫载体」，是它自己业务的数据面
#   （write_race_watch 扫 成长箱/*.md = 工单数据；twin_distill_watch 扫 日记目录）
DOMAIN_EXEMPT = {
    "write_race_watch.py",                  # 域=成长箱工单数据面·非守卫载体
    "twin_distill_watch.py",                # 域=日记/立场卡数据面·非守卫载体
    "shadow_ssot_guard.py",                 # 域=单一 SSOT 文件所在目录
    "doenglingz_naming_guard.py",           # 域=各端配置目录（非本档案根）
    "verifier_target_fidelity_guard.py",    # 域含 .hermes（插件运行面·非档案内载体）
    "guard_doc_consistency.py",             # 域=文档 SSOT 所在目录·判的是文档不是件
}

SCAN_GUARD_DIRS = ["脚本中心", "开发工具", "数字分身/scripts", "数字分身/guards"]


def declared_domains(path):
    """抽出守卫声明的扫描域（相对 ARCHIVE 的相对路径列表）。⛔ 不猜。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
    except OSError:
        return None
    found = []
    for var in DOMAIN_VARS:
        m = re.search(r'%s\s*=\s*\[(.*?)\n\s*\]' % re.escape(var), src, re.S)
        if not m:
            continue
        for seg in m.group(1).split("\n"):
            mm = re.search(r'"([^"]+)"', seg)
            if mm:
                found.append((var, mm.group(1)))
    return found


def normalize(d):
    """归一：ARCHIVE 绝对 → 相对；os.path.join(X, "a", "b") 的多段拼接由调用方给全。"""
    d = d.replace(ARCHIVE, "").lstrip("/")
    if d.startswith("个人AI档案/"):
        d = d[len("个人AI档案/"):]
    return d.rstrip("/")


def rel_to_archive(p):
    try:
        return os.path.relpath(os.path.realpath(p), ARCHIVE)
    except ValueError:
        return p


def audit():
    problems = []
    info = []

    # ── 判据①：真源里的目录必须真实存在（防空挂）───────────────────────────────
    for d in DOMAINS:
        p = os.path.join(ARCHIVE, d)
        if not os.path.isdir(p):
            problems.append("真源目录不存在：%s（DOMAINS 里有、盘上没有 ⇒ 又一份漂移的账）" % d)

    # ── 判据②：每个声明扫描域的守卫，域必须 ⊆ DOMAINS ─────────────────────────
    for root_rel in SCAN_GUARD_DIRS:
        root = os.path.join(ARCHIVE, root_rel)
        if not os.path.isdir(root):
            continue
        for f in sorted(os.listdir(root)):
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            if os.path.realpath(p) == SELF:
                continue
            decl = declared_domains(p)
            if not decl:
                continue
            rel = rel_to_archive(p)
            # ⛔ 豁免：域 ≠ 守卫载体 的守卫（业务数据面·见 DOMAIN_EXEMPT）
            #   ⚠️ 2026-10-03 实测实证：判据② 曾把这两件误报为「散落域」——
            #     `verifier_target_fidelity_guard` 的域含 `.hermes`（插件运行面）
            #     `shadow_ssot_guard` 的域是 `~/个人AI档案`（单一 SSOT 所在目录）
            #   ⇒ 豁免表原先只定义了**从未被用上**=装饰品，现接上。
            #     若将来某守卫名不再在表内而它真的是守卫载体，判据③ 仍会兜住。
            base_name = os.path.basename(p)
            if base_name in DOMAIN_EXEMPT or rel.split("/")[-1] in DOMAIN_EXEMPT:
                info.append((rel, len(decl), "（豁免·域为业务数据面）"))
                continue
            info.append((rel, len(decl), ""))
            for var, d in decl:
                nd = normalize(d)
                # 多段拼接（"数字分身","scripts"）→ 只有首段可比
                if nd and nd.split("/")[0] not in {x.split("/")[0] for x in DOMAINS}:
                    problems.append(
                        "%s 的 %s 声明了域「%s」，不在 DOMAINS 真源内"
                        " ⇒ 扫描域散落第 N 处（本会话同族病）" % (rel, var, nd))

    # ── 判据③：载有**真守卫件**的目录是否都在 DOMAINS 里 ────────────────────
    #   ⚠️ 判据口径两次收紧（2026-10-03·本件自建过程实证）：
    #     v1「≥3 个可执行件就算载守卫」⇒ **判据过宽**：正例实跑抓到 6 个"盲区"，
    #        逐个定性后 **5 个不是守卫载体**（可视化呈现/scripts=面板工具·
    #        Trae记忆=记忆脚本·知识联邦引擎/scripts=引擎·QClaw记忆=migrate/distill）
    #        ⇒ 真含守卫件的只有 2 处（成就系统/scripts 2 个·templates 1 个）。
    #     v2「文件名含 guard/check/audit/verify/watch 才是守卫」⇒ **语义判据**。
    #   ⇒ 只认**语义守卫件**；工具/引擎目录不算盲区（它们另有归属）。
    # ⚠️ `发布库` **不在排除表**：它下面的 `存档包/脱敏门禁/desensitize-guard.sh`
    #   是真守卫件（判据① 已证实）——2026-10-03 一度把 发布库 整目录排除，
    #   那会让真守卫从判据③ 眼前消失（与「域收窄导致假绿」同型）。
    GUARD_TOKENS = ("guard", "check", "audit", "verify", "watch")
    dom_heads = {x.split("/")[0] for x in DOMAINS}
    for dp, dn, fn in os.walk(ARCHIVE):
        dn[:] = [x for x in dn
                 if x not in ("__pycache__", ".git", "site-packages", ".venv",
                              "记忆琥珀", "记忆蒸馏", "node_modules",
                              # ⛔ 归档不是活载体（2026-10-03 正例实跑抓到
                              #   `归档/脚本归档/…-deprecated` 里的已废弃守卫）
                              "归档")
                 and not x.startswith(".")]
        guards = [f for f in fn
                  if f.endswith((".py", ".sh")) and any(t in f for t in GUARD_TOKENS)]
        if not guards:
            continue
        rel = rel_to_archive(dp)
        if rel in DOMAINS or rel.split("/")[0] in dom_heads:
            continue
        # 已被真源某条覆盖（含多段路径）？
        if any(rel == d or rel.startswith(d + "/") or d.startswith(rel + "/")
               for d in DOMAINS):
            continue
        problems.append(
            "目录「%s」载有 %d 个守卫件（%s）但不在 DOMAINS 真源内 ⇒ 元层看不见它"
            "（要么加进真源·要么它不该有守卫件·现在两者都没说）"
            % (rel, len(guards), "、".join(guards[:3])))

    # ── 判据④：**守卫域声明的覆盖率**（2026-10-04·皮叔问「8个只扫5个·另3个为什么没做」触发）
    #   ⛔ **事实纠正**：我 2026-10-03 说的「8 个守卫只扫了 5 个」是**误导性表述**——
    #     当时只查了「声明了 DOMAIN_VARS 的」那一小撮，得 5。
    #     全盘实况：**156 件守卫**（文件名含 guard/check/audit/verify/watch），
    #     其中只有 5 件声明了扫描域 ⇒ 「另 3 个」的问法本身建立在一个错误分母上。
    #   ⇒ 本判据给出的不是「漏了几个」，而是**分母本身**：
    #     多少守卫有显式域声明 / 多少没有。没有声明的守卫，它的覆盖范围**无从核对**
    #     （它可能只读一个文件，也可能 walk 整个档案根）——这是真实的不可见面。
    #   ⇒ 处置：显形为主（⚠️），不判红。判红 = 逼所有守卫加声明 = 过度施工。
    #     但**分母要可见**——「156 个守卫里 5 个有声明」这个事实必须能被说出来。
    all_guards = 0
    with_decl = 0
    for root_rel in SCAN_GUARD_DIRS:
        root = os.path.join(ARCHIVE, root_rel)
        if not os.path.isdir(root):
            continue
        for f in sorted(os.listdir(root)):
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            if os.path.realpath(p) == SELF:
                continue
            if not any(tok in f for tok in ("guard", "check", "audit", "verify", "watch")):
                continue
            all_guards += 1
            if declared_domains(p):
                with_decl += 1
    info.append(("__COVERAGE__", all_guards, "守卫总数"))
    info.append(("__COVERAGE__", with_decl, "有显式域声明"))
    if with_decl < all_guards:
        info.append(("__COVERAGE_WARN__",
                     all_guards - with_decl,
                     "守卫无显式域声明 ⇒ 覆盖范围无从核对（不可见面·非漏检）"))

    return problems, info



def self_test():
    """反向夹具：故意让判据③ 失败 ⇒ 必须判红。⛔ 正例绿证明不了域对。"""
    if "--self-test" not in sys.argv:
        return None
    # ⚠️ 夹具建在**档案根下**（2026-10-03 二次夹具实证）：
    #   第一版建在 `开发工具/` 下 ⇒ 被 `rel.split("/")[0] in dom_heads` 命中而跳过
    #   ⇒ 正例绿、盲区照样漏——**夹具必须放在与真实盲区同构的位置**。
    #   真实盲区形态（正例实跑抓到 6 个）：`可视化呈现/scripts` / `成就系统/scripts` 这类
    #   「顶层目录不在真源 + 它自己还有 scripts 子目录」。
    tmp = os.path.join(ARCHIVE, "_probe_盲区夹具", "scripts")
    os.makedirs(tmp, exist_ok=True)
    try:
        for i in range(3):
            with open(os.path.join(tmp, "probe_guard_%d.py" % i), "w") as fh:
                fh.write("# probe\n")
        probs, _ = audit()
        hit = any("_probe_盲区夹具" in p for p in probs)
        print("[self-test] 反向夹具（%s 含 3 件·不在真源）→ 判据③ %s"
              % (tmp, "✅ 抓到" if hit else "❌ 没抓到"))
        if not hit:
            print("[self-test] ⛔ FAIL：盲区守卫形同虚设")
            return 1
        print("[self-test] ✅ PASS")
        return 0
    finally:
        # ⚛ 清到档案根的父目录（只 rmtree(tmp) 会留 `_probe_盲区夹具/` 空壳·
        #   下次 self-test 会撞上自己上次留的壳 ⇒ 夹具失真）
        shutil.rmtree(os.path.dirname(tmp), ignore_errors=True)


def main():
    if "--self-test" in sys.argv:
        return self_test() or 0

    problems, info = audit()
    print("── 判据① 真源目录存在性 ──")
    ok = [d for d in DOMAINS if os.path.isdir(os.path.join(ARCHIVE, d))]
    bad = [d for d in DOMAINS if d not in ok]
    print("  %d/%d 目录在盘" % (len(ok), len(DOMAINS)))
    for d in bad:
        print("  ❌ 不存在: %s" % d)
    if not bad:
        print("  ✅ 全部存在")

    print("\n── 判据② 守卫扫描域 ⊆ 真源 ──")
    # ⛔ 过滤哨兵行（`__COVERAGE__` / `__COVERAGE_WARN__` 是判据④ 的数据·不是守卫）
    decl_rows = [r for r in info if not str(r[0]).startswith("__")]
    print("  有域声明的守卫: %d 件" % len(decl_rows))
    for row in decl_rows:
        rel, n = row[0], row[1]
        note = row[2] if len(row) > 2 else ""
        print("    %-44s %d 个域 %s" % (rel[:42], n, note))
    p2 = [p for p in problems if "不在 DOMAINS 真源内" in p and "载有" not in p]
    print("  %s" % ("✅ 无散落域" if not p2 else "❌ %d 处散落" % len(p2)))
    for p in p2:
        print("    ❌ %s" % p)

    print("\n── 判据③ 载有守卫的目录全覆盖 ──")
    p3 = [p for p in problems if "载有" in p]
    print("  %s" % ("✅ 无盲区" if not p3 else "❌ %d 个盲区" % len(p3)))
    for p in p3:
        print("    ❌ %s" % p)

    print("\n── 判据④ 守卫域声明覆盖率 ──")
    tot = dec = miss = 0
    for row in info:
        if row[0] == "__COVERAGE__":
            if row[2] == "守卫总数":
                tot = row[1]
            else:
                dec = row[1]
        elif row[0] == "__COVERAGE_WARN__":
            miss = row[1]
    print("  %d/%d 守卫有显式域声明（%.1f%%）" % (dec, tot, (dec / tot * 100) if tot else 0))
    if miss:
        print("  ⚠️ %d 件守卫无域声明 ⇒ 覆盖范围**无从核对**" % miss)
        print("     （不是「漏检」——是没说清它扫哪；处置=显形·不判红）")

    if problems:
        print("\n结论：%d 项待处理" % len(problems))
        return 1
    print("\n结论：✅ 扫描域收敛完毕（真源 %d 目录·无散落·无盲区）" % len(DOMAINS))
    return 0


if __name__ == "__main__":
    sys.exit(main())