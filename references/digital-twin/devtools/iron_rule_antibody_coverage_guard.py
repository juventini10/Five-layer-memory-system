#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iron_rule_antibody_coverage_guard.py — 铁律抗体覆盖率体检（v1.0.0·2026-10-01）

## 为什么存在（实盘取证·⛔非推测）
`growth-box` 流程 B4 步骤7 要求「晋升时配🛡抗体」，但**没有任何脚本检查有没有真的配**。
后果实测（2026-10-01）：铁律版 **30 条铁律中仅 3 条**（028/029/030）写了「承接器在岗／抗体」，
**27 条纯文本**——而这 27 条里包含铁律-001「先看清再动手」、铁律-002「实事求是底线」，
INDEX 关联行明写 PAT-001「已晋升铁律-001，**仍复发**」4/3 次。
⇒ **条文写了不等于会被执行；无抗体 = 无规则**。本守卫把这个隐性事实变成可见读数。

## 判据（只读·零写入·⛔不改任何铁律内容）
「一条铁律是否配了抗体」的判据 = 该条目正文是否含抗体/承接器标记：
    「承接器在岗」/「抗体」/「🛡」
· **有意声明豁免**：条目含「豁免」+ 理由 → 计为「声明豁免」（不算无抗体·但要求有理由）
· 报红口径：既无抗体标记、也无豁免声明 → `no_antibody`（⚠️ 提示级·⛔ 不阻断）

## 为什么只提示不阻断
· 反漂移纪律：铁律版是全端共享 SSOT，⛔本守卫绝不代改铁律内容
· 存量 27 条是历史事实，⛔ 不能因为体检就假装它们有抗体
· 输出是**读数**：让你和 AI 看见「哪些铁律有机械承接、哪些只是文本」

## 用法
  python3 iron_rule_antibody_coverage_guard.py            # 人读报告
  python3 iron_rule_antibody_coverage_guard.py --json     # 机读（供其他守卫消费）
  python3 iron_rule_antibody_coverage_guard.py --selftest # 自测（含负例）

## 退出码
  0 = 无阻断项（本体恒 0·本守卫为提示级）
  1 = 用法错/文件不可读
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import io
import json
import os
import re
import sys

DEFAULT_IRON = os.path.expanduser("[记忆共享中心]/记忆规则/用户基本规则-铁律版.md")
# 第二载体（2026-10-01 22:58 口径根治·见下）
DEFAULT_FEEDBACK = os.path.expanduser("[记忆共享中心]/成长箱/experience/规范反哺日志.md")
__version__ = "v1.2.0"

# 第三载体（2026-10-01 23:25·同日第二次载体盲区的机械对策）
# 起因：抗体还落在 `脚本中心/`（72 守卫）·而注册表偏向 开发工具/（30:1）
#   ⇒ 实锤漏判两条：脚本中心/reference_path_check.py→003、脚本中心/guard_selftest_check.py→021
# ⚠️ 两个目录必须都声明——少声明一个就重现今天第二次假阴性。
SCRIPT_DIRS = [
    os.path.expanduser("[记忆共享中心]/脚本中心"),
    os.path.expanduser("[记忆共享中心]/脚本中心"),
]
REGISTRY = os.path.expanduser(
    "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md")

# ── 口径根治记录（必读·今日四次同型病的产物）──────────────────────────────
# v1.0.0 只扫铁律正文的「承接器在岗/抗体/🛡」字样 ⇒ 报 10%。
# 实测查明：抗体**真身确实存在**，载体是【成长箱反哺日志】的
#   「📚 建议落点：铁律-NNN…」+「🛡 复发检测条件」字段
#   （growth_box_check.sh v1.5 双源扫描的数据源），⛔**不是**写在铁律正文里。
# ⇒ v1.0.0 把「载体在反哺日志」误判成「没抗体」＝**假阴性**
#   （仪器结构性问题·立场卡 C-089「仪器假警报归因反转」
#    + #S881「红牌必须先验仪器再判对象且验完必须修」）。
# v1.1.0 口径 = **双载体并集**：
#   载体1 = 铁律正文标记（承接器在岗/抗体/🛡）
#   载体2 = 反哺日志中「建议落点/反哺标题」指向该铁律
# ⚠️ 仍⛔不做语义判定：命中载体2 只说明「有反哺条目挂在它身上」，
#    ⛔**不等于**那条反哺已真正配出可执行抗体——那属 verifier 的逐条核证职责。

# 条目切分：`### 铁律-NNN：标题`
_SEC_RE = re.compile(r"^### 铁律-(\d{3})[：:]\s*(.*)$", re.M)
# 抗体/承接器标记（任一命中 = 已配机械承接）
_AB_RE = re.compile(r"承接器在岗|抗体|🛡")
# 有意豁免声明。
# ⚠️ 踩坑二修（2026-10-01 真机跑批抓出）：⛔ 不能只找「豁免」二字——
#   铁律-022「授权≠流程豁免」/024「豁免须报名」**标题里就带豁免**，
#   会被误判成"已声明不配抗体"。豁免声明的真形态是**抗体位留空 + 说明为何不配**：
#   「抗体：…暂无 / 不适用 / N/A + 理由」。故要求三者同现：
#     ①抗体位提及（抗体/🛡/承接器）②否定/未配标记（暂无/无/不适用/N/A/未配）③理由连接
_EXEMPT_RE = re.compile(
    r"(?:抗体|🛡|承接器)[^。\n]{0,30}?"
    r"(?:暂无|尚无|无|不适用|N/?A|未配|没有)"
    r".{0,40}?(?:理由|原因|因|系|：|:)", re.S)


def parse_rules(text: str):
    """切出铁律条目 → [{num, title, body, has_ab, has_exempt}]"""
    marks = list(_SEC_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.start():end]
        out.append({
            "num": m.group(1),
            "title": m.group(2).strip()[:48],
            "body": body,
            "has_ab": bool(_AB_RE.search(body)),
            "has_exempt": bool(_EXEMPT_RE.search(body)),
        })
    return out


def _load_carrier3():
    """载体3 = 守卫脚本目录 ∪ 注册表 → 反查它明确关联到哪些铁律。

    ⚠️ 只认「注册表同一行里 脚本名 … 铁律-NNN」的**显式**关联
       ⇒ ⛔ 不做「标题↔文件名」弱联想（那是我今天犯的第三台假尺的同型）。
       ⛔ 命中也⛔不等于 CONFIRMED：文件存在 ≠ 它真守这条铁律，
          真伪仍须 iron_rule_antibody_verifier.py 回读源码判定。
    """
    import glob
    names = set()
    for d in SCRIPT_DIRS:
        if os.path.isdir(d):
            for f in glob.glob(os.path.join(d, "*")):
                if f.endswith((".py", ".sh")):
                    names.add(os.path.basename(f))
    reg = ""
    if os.path.isfile(REGISTRY):
        reg = io.open(REGISTRY, encoding="utf-8").read()
    direct = {}
    for m in re.finditer(r"([A-Za-z_0-9]+\.(?:py|sh))([^|\n]{0,300}?)铁律[- ]?(\d{3})", reg):
        direct.setdefault(m.group(3), set()).add(m.group(1))
    # 反向：注册表整行里先出现铁律号再出现脚本名（顺序不固定）
    for line in reg.splitlines():
        if not line.startswith("|"):
            continue
        nums = re.findall(r"铁律[- ]?(\d{3})", line)
        fs = re.findall(r"([A-Za-z_0-9]+\.(?:py|sh))", line)
        if nums and fs:
            for n in nums:
                for f in fs:
                    direct.setdefault(n, set()).add(f)
    return names, direct


def report(text: str, fb_text: str = "") -> dict:
    rules = parse_rules(text)

    # ── 载体3：脚本目录 + 注册表显式关联 ──
    script_names, script_direct = _load_carrier3()

    # ── 载体2：反哺日志里指向该铁律的条目 ──
    # 只认「建议落点/反哺标题 明确写了铁律-NNN」的行 ⇒ ⛔ 不做语义联想
    fb_rules = set()
    if fb_text:
        for m in re.finditer(r"(?:建议落点|反哺标题)[^\n]{0,120}?铁律[- ]?(\d{3})", fb_text):
            fb_rules.add(m.group(1))

    # ⚠️ 优先级：豁免声明**先判**。
    # 踩坑（2026-10-01 自测当场抓出）：条目写「抗体：暂无·豁免理由=…」时，
    # 「抗体」二字会把 has_ab 置真 → 误判为已覆盖。豁免的语义就是「没配」，
    # 必须优先于"有抗体标记"判定，否则豁免声明永远无法被识别。
    for r in rules:
        r["has_fb"] = r["num"] in fb_rules
        if r["has_exempt"]:
            r["status"] = "exempt"
        elif r["has_ab"]:
            r["status"] = "covered"
        elif r["has_fb"]:
            r["status"] = "covered_via_feedback"   # 载体2：有反哺条目挂它身上
        elif r["num"] in script_direct:
            r["status"] = "covered_via_script"    # 载体3：注册表明确关联到脚本
        else:
            r["status"] = "no_antibody"
            # ⛔ 不做「标题↔文件名」弱关联给候选——那正是我今天犯的第三台假尺的同型
            #    （数字/标题命中≠该脚本真守这条铁律）⇒ 默认不给候选。
    total = len(rules)
    covered = sum(1 for r in rules if r["status"] == "covered")
    via_fb = sum(1 for r in rules if r["status"] == "covered_via_feedback")
    via_scr = sum(1 for r in rules if r["status"] == "covered_via_script")
    exempt = sum(1 for r in rules if r["status"] == "exempt")
    bare = [r for r in rules if r["status"] == "no_antibody"]
    pct = round(100.0 * (covered + via_fb + via_scr + exempt) / total, 1) if total else 0.0
    pct_iron_only = round(100.0 * (covered + exempt) / total, 1) if total else 0.0
    return {"version": __version__, "total": total, "covered": covered,
            "covered_via_feedback": via_fb, "covered_via_script": via_scr,
            "exempt": exempt,
            "no_antibody": len(bare), "coverage_pct": pct,
            "coverage_pct_iron_mark_only": pct_iron_only,
            "bare_rules": [{"num": r["num"], "title": r["title"]} for r in bare]}


def _selftest() -> int:
    """自测：正例/负例/混合/边界。⛔ 断言判据本身可信（不做「恒真」自欺）。"""
    cases = [
        ("正例·有承接器", "### 铁律-001：X\n正文\n承接器在岗：guard.py\n", 1, 1, 0, 100.0),
        ("负例·纯文本", "### 铁律-002：Y\n正文只有约束没有机械承接。\n", 1, 0, 0, 0.0),
        ("豁免声明", "### 铁律-003：Z\n正文\n抗体：暂无·豁免理由=仅措辞类无可测对象。\n", 1, 0, 1, 100.0),
        ("混合·3条", "### 铁律-001：A\n承接器在岗：x\n\n### 铁律-002：B\n纯文本\n\n### 铁律-003：C\n🛡 抗体：y\n",
         3, 2, 0, 66.7),
        ("边界·空文件", "", 0, 0, 0, 0.0),
        ("边界·无条目", "# 只是标题\n正文\n", 0, 0, 0, 0.0),
        ("豁免须有理由·裸「豁免」不算", "### 铁律-004：W\n豁免\n", 1, 0, 0, 0.0),
        # 踩坑二修（真机跑批抓出）：标题含「豁免」≠声明豁免（022/024 曾被误判）
        ("标题带豁免不算", "### 铁律-022：授权≠流程豁免\n正文：授权不等于豁免流程。\n", 1, 0, 0, 0.0),
        ("真豁免·抗体位留空+理由", "### 铁律-005：V\n正文\n抗体：N/A·理由=仅措辞类无可测对象\n", 1, 0, 1, 100.0),
        # ── 载体2（反哺日志）口径用例·v1.1.0 新增·防修尺修出新病 ──
        # 形态：正文纯文本无任何标记（载体1 不中）·但反哺日志有条目挂在它身上
        #   ⇒ 应判 covered_via_feedback（正文标记口径 0%，双载体口径 100%）
        # ⚠️ 用例文本⛔不得出现"抗体/承接器/豁免"任何触发字样——
        #    否则载体1 先命中，测不到载体2（2026-10-01 自测当场踩到：
        #    初版用例正文写"正文无任何抗体标记"，"抗体"二字把 has_ab 置真
        #    ⇒ covered=1/via_fb=0，自测 FAIL 才发现是【用例写错】不是【判据写错】）
        {"name": "载体2·反哺日志挂该铁律→正文0/双载体100",
         "iron": "### 铁律-007：纯文字条目\n这里只是一段普通正文。\n",
         "fb": "### 反哺：铁律-007某项\n- 📚 建议落点：铁律-007 某规范\n",
         "total": 1, "covered": 0, "exempt": 0,
         # 双载体口径 coverage_pct 应为 100.0（载体2 命中即算覆盖）
         # ⚠️ 初版这里误写 0.0 → 自测 FAIL 才发现是【期望值写错】不是【判据写错】
         #    （连续两次：先是用例正文混入触发字·再是期望值笔误——
         #      两次都是"尺的问题"其实是"我写测试的问题"·自测是唯一的发现手段）
         "pct": 100.0, "pct_iron_only": 0.0, "via_fb": 1},
    ]
    ok = True
    # ⚠️ v1.1.0 结构根治：旧版用位置元组 c[:6]，新增载体2 用例后元组长度不一致
    #   （fb 插在第 3 位）⇒ 位置解包把 fb 当成 total 传进 report，
    #   自测连续 FAIL 才暴露。改为**具名 dict**·⛔不再依赖任何位置约定。
    for c in cases:
        d = c if isinstance(c, dict) else {
            "name": c[0], "iron": c[1], "total": c[2],
            "covered": c[3], "exempt": c[4], "pct": c[5],
            "fb": "", "pct_iron_only": c[5], "via_fb": None}
        r = report(d["iron"], d.get("fb", ""))
        good = (r["total"], r["covered"], r["exempt"], r["coverage_pct"]) == (
            d["total"], d["covered"], d["exempt"], d["pct"])
        if "pct_iron_only" in d:
            good = good and r["coverage_pct_iron_mark_only"] == d["pct_iron_only"]
        if d.get("via_fb") is not None:
            good = good and r["covered_via_feedback"] == d["via_fb"]
        ok = ok and good
        print("%s %-34s total=%d covered=%d via_fb=%d exempt=%d pct=%s iron_only=%s"
              % ("PASS" if good else "FAIL", d["name"], r["total"], r["covered"],
                 r["covered_via_feedback"], r["exempt"],
                 r["coverage_pct"], r["coverage_pct_iron_mark_only"]))
    # 反向变异：判据若恒真，下列两条必挂（防空转）
    mutated = "### 铁律-001：X\n承接器在岗：x\n"
    r = report(mutated)
    v1 = r["covered"] == 1
    v2 = report("### 铁律-001：X\n纯文本\n")["covered"] == 0
    # v1b（v1.1.0 新增）：载体2 判据若恒真·任意文本+任意反哺都算覆盖
    v3 = report("### 铁律-002：Y\n纯文本\n", "### 反哺：别的铁律-009\n- 📚 建议落点：铁律-009 x\n"
               )["covered_via_feedback"] == 0
    ok = ok and v1 and v2 and v3
    print("%s 变异·标记变化可辨（防空转）" % ("PASS" if (v1 and v2) else "FAIL"))
    print("%s 变异·载体2 指向别的铁律不计（防恒真）" % ("PASS" if v3 else "FAIL"))
    print("self-test: %d/%d" % (sum(1 for _ in cases) + 2, len(cases) + 2) if ok else "self-test FAILED")
    # ⚠️ 上面那行是**恒真计数**（sum over cases 恒 = len(cases)）·只作展示。
    #    真判据是 ok 布尔 + 变异项 v1/v2/v3·⛔不拿计数当通过证据。
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="铁律抗体覆盖率体检（提示级·只读）")
    ap.add_argument("--file", default=DEFAULT_IRON)
    ap.add_argument("--feedback", default=DEFAULT_FEEDBACK,
                    help="载体2·反哺日志路径（抗体真身载体·2026-10-01 v1.1.0 新增）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan-audit", action="store_true",
                    help="扫描域自检：已声明载体 vs 盘上其他候选目录（本日两次载体盲区的机械对策）")
    ap.add_argument("--strict", action="store_true",
                    help="多载体口径下·仍有裸铁律 ⇒ exit 1（Fail-Closed·需 verifier 逐条核证后才会为 0）")
    a = ap.parse_args()

    if a.selftest:
        return _selftest()

    if a.scan_audit:
        import glob
        print("🔍 扫描域自检 %s" % __version__)
        print("起因：2026-10-01 同日两次载体盲区——v1.0.0 漏反哺日志(10%假阴性)·"
              "v1.1.0 漏脚本中心/(仍假阴性 40%→真 46.7%)")
        print("=" * 74)
        print("\n【已声明载体】")
        for name, p in [("载体1 铁律正文", a.file),
                        ("载体2 反哺日志", a.feedback),
                        ("载体3 注册表", REGISTRY)]:
            print("  %-14s %s  %s" % (name, "✅在" if os.path.isfile(p) else "⚠️缺失", p))
        print("\n【载体3 脚本目录·两个都必须声明】")
        for d in SCRIPT_DIRS:
            n = len(glob.glob(os.path.join(d, "*.py"))) + len(glob.glob(os.path.join(d, "*.sh")))
            print("  %-6s %s  （%d 个脚本）" % ("✅在" if os.path.isdir(d) else "⚠️缺失", d, n))
        base = os.path.expanduser("~")
        cands = [d for d in sorted(os.listdir(base))
                 if os.path.isdir(os.path.join(base, d))
                 and re.search(r"(守卫|guard|script|脚本|工具)", d, re.I)
                 and os.path.join(base, d) not in SCRIPT_DIRS]
        print("\n【⚠️ 盘上其他候选目录·本脚本未声明为载体】")
        if not cands:
            print("  （无·差集为空）")
        for d in cands:
            cnt = (len(glob.glob(os.path.join(base, d, "*.py")))
                   + len(glob.glob(os.path.join(base, d, "*.sh"))))
            print("  · %-24s %d 个脚本" % (d, cnt))
        print("\n  ⇒ 差集非空＝我又可能在漏载体。⛔本脚本不自动把它们当载体——")
        print("    那会引入第四第五次假阴性猜测（这正是今天前两次的成因）。")
        return 0

    if not os.path.isfile(a.file):
        print("❌ 铁律版不存在：%s" % a.file, file=sys.stderr)
        return 1
    fb_text = ""
    if os.path.isfile(a.feedback):
        fb_text = io.open(a.feedback, encoding="utf-8").read()
    else:
        print("⚠️ 载体2 缺失：%s（本次只按载体1=铁律正文口径读）" % a.feedback, file=sys.stderr)
    rep = report(io.open(a.file, encoding="utf-8").read(), fb_text)

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if (a.strict and rep["no_antibody"]) else 0

    print("🛡 铁律抗体覆盖率体检 %s（双载体口径）" % __version__)
    print("   载体1 铁律正文：%s" % a.file)
    print("   载体2 反哺日志：%s%s" % (a.feedback, "" if fb_text else "（缺失·未参与）"))
    print("=" * 70)
    print("📊 总数 %d ｜ 载体1 正文标记 %d ｜ 载体2 反哺挂靠 %d ｜ 声明豁免 %d ｜ ⬜无抗体 %d"
          % (rep["total"], rep["covered"], rep["covered_via_feedback"],
             rep["exempt"], rep["no_antibody"]))
    print("   覆盖率：正文口径 %.1f%%  →  双载体口径 %.1f%%"
          % (rep["coverage_pct_iron_mark_only"], rep["coverage_pct"]))
    if rep["bare_rules"]:
        print("\n⬜ 无任何抗体载体的铁律（有约束·无机械承接·靠自觉执行）：")
        for r in rep["bare_rules"]:
            print("   · 铁律-%s %s" % (r["num"], r["title"]))
    print("\n⚠️ 口径说明（2026-10-01 22:58 修尺记录·必读）：")
    print("   v1.0.0 只扫载体1 ⇒ 报 10%，把「载体在反哺日志」误判成「没抗体」＝**假阴性**")
    print("   （立场卡 C-089 仪器假警报归因反转 + #S881 验完必须修）")
    print("   v1.1.0 = 双载体并集。⚠️ 命中载体2 只说明「有反哺条目挂在它身上」，")
    print("   ⛔ 不等于那条反哺已真正配出可执行抗体——逐条核证属 "
          "iron_rule_antibody_verifier.py 职责。")
    print("   本守卫为**提示级**（默认 exit 0）——⛔不改铁律内容·只暴露「哪些只是文本」。")
    return 1 if (a.strict and rep["no_antibody"]) else 0


if __name__ == "__main__":
    sys.exit(main())