#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""questionnaire_sync_check.py — 33 题「题库 ↔ 答题页」构建期逐字对账（C06）

## 为什么存在（2026-10-15 E2E 修包线 C06）
包内 33 题有**两个源**：`references/questionnaire.md`（官方题库·step4 第1关的比对基准）与
`references/自建33题-答题页-v1.html` 的 `const Q`（用户实际看到的页面）。两者各自演化，
实测 5 题分叉（Q5 丢半句、Q18 题库带作者侧 `🔴`、Q23/24 丢作答指引、Q29 类型标注形态差）。
后果不是排版问题：step4 第1关拿「答卷题干 vs 题库」逐题核对，并在原判据里写「主形态下若不一致
=非页面产物的手改卷，按可疑卷处理」——**用户老老实实答页面，页面本身就和题库不一致，于是诚实用户
被判可疑卷**（E2E 实录：真页面答卷被判可疑）。判据的归因方向是反的：漂移在包内，账却记到用户头上。

## 本脚本做的事：把「两源必须逐字相等」变成发版前机械闸（不靠人记得）
等式（判据口径·Rule A）：
  1. **题干**：题库 stem 去掉**类型标注**（（单选）/（多选）/（可多选））后，须与页面 stem 逐字相等。
     ——类型标注由页面的 single/multi/open 字段承载，属**形态差**不是**语义差**，剥掉比；
  2. **类型**：题库标注 ↔ 页面字段须互相印证（（可多选）⇒ multi=True；选项行仅 `________` ⇒ open=True）；
  3. **选项**：逐字母逐字相等（含「其他：________」占位）；
  4. **作答指引不是类型标注**：如「（用一两句话描述）」「（只能说一件事，越具体越好）」——
     它们改变用户该写什么，⛔不在剥离名单里，丢了就是红（这正是 Q23/Q24 的病）；
  5. **作者侧残留**：题库题干含 emoji（🔴⚠️✅❌）或卡号（#Sxxx）即红——那是作者工作标记，不该进用户视野。

## 用法
  python3 questionnaire_sync_check.py                 # 全量对账，stdout 逐条列差
  python3 questionnaire_sync_check.py --quiet          # 只给总结行（供 verify.sh 内嵌）
  python3 questionnaire_sync_check.py --negative-test  # 变异自检：4 类漂移必须全被抓到

## 退出码
  0 = 两源相等（33/33）
  1 = 存在分叉（逐条打印：题号＋两个源的原文＋差异位置）
  2 = 解析失败/基数不对（fail-closed，⛔不返回"看起来没问题"）
"""
import argparse
import os
import re
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）

import tempfile

TYPE_TAGS = ("（单选）", "（多选）", "（可多选）")
AUTHOR_MARK = re.compile(r"[🔴⚠️✅❌]|#S\d{3}")
OPEN_PLACEHOLDER = "________"


def die(msg, remedy, code=2):
    print("❌ " + msg)
    print("   怎么办：" + remedy)
    sys.exit(code)


# ─────────────────────────────────────────────────────────────────────────
def parse_bank(path):
    """题库 md → {id: {stem, tag, opts:[(k,text)], raw}}"""
    if not os.path.isfile(path):
        die("找不到题库：%s" % path, "本脚本须与发布包同根运行（默认按包内相对路径寻址）。")
    text = open(path, encoding="utf-8").read()
    items = {}
    for m in re.finditer(r"^\*\*Q(\d+)\.\s*(.+?)\*\*[ \t]*$", text, re.M):
        num, stem = int(m.group(1)), m.group(2).strip()
        if num in items:
            die("题库第 %d 题出现两次" % num, "题库一题一条，请核对 questionnaire.md。")
        # 该题下方的选项行（- A xxx / - ________）
        tail = text[m.end():]
        opts = []
        for line in tail.split("\n"):
            s = line.strip()
            if not s:
                continue
            if s.startswith("**Q") or s.startswith("## ") or s.startswith("---"):
                break
            if not s.startswith("- "):
                continue
            body = s[2:].strip()
            km = re.match(r"^([A-Z])\s+(.+)$", body, re.S)
            if km:
                opts.append((km.group(1), km.group(2).strip()))
            else:
                opts.append(("", body))
        tag = ""
        for t in TYPE_TAGS:
            if t in stem:
                tag = t
                break
        items[num] = {"stem": stem, "tag": tag, "opts": opts}
    if len(items) != 33:
        die("题库解析到 %d 题（应为 33）。" % len(items),
            "题库条目格式为 `**Q<数字>. 题干**` + 下方 `- A …` 选项行；格式被改动会让本对账失明（⛔不是「没问题」）。")
    return items


def parse_page(path):
    """答题页 const Q（JSON 数组）→ {id: {stem, opts, single, multi, open}}"""
    if not os.path.isfile(path):
        die("找不到答题页：%s" % path, "页面文件名以 INSTALL.md 养成链 D1 行为准。")
    text = open(path, encoding="utf-8").read()
    line = None
    for l in text.split("\n"):
        if l.strip().startswith("const Q="):
            line = l.strip()
            break
    if line is None:
        die("答题页里找不到 `const Q=` 数据行。",
            "页面改版请把题目数组留在同一行首（本脚本按 `const Q=[…]` 取数·⛔不靠肉眼比对）。")
    import json
    js = line[line.index("["):].rstrip().rstrip(";")
    try:
        arr = json.loads(js)
    except ValueError as e:
        die("答题页 const Q 不是合法 JSON：%s" % e, "该数组由 JSON 字面量维护，请检查引号/逗号。")
    items = {}
    for d in arr:
        num = int(d["id"])
        if num in items:
            die("页面第 %d 题出现两次" % num, "题号必须唯一。")
        opts = [(o["k"], o["v"]) for o in d.get("opts", [])]
        if not opts and isinstance(d.get("single"), list):
            opts = [(k, v) for k, v in d["single"]]
        items[num] = {"stem": d["q"].strip(), "opts": opts,
                      "single": bool(d.get("single")), "multi": bool(d.get("multi")),
                      "open": bool(d.get("open"))}
    if len(items) != 33:
        die("页面解析到 %d 题（应为 33）。" % len(items),
            "页面必须与题库同基数，缺题=用户答不完还能过闸。")
    return items


def norm_stem(stem, tag):
    s = stem
    if tag:
        s = s.replace(tag, "")
    return s.replace(" ", "").strip()


def compare(bank, page):
    diffs = []
    ids = sorted(set(bank) | set(page))
    for i in ids:
        if i not in bank:
            diffs.append("Q%d 只在页面存在、题库缺失（第1关必判你手改卷·以题库为准则无基准）" % i)
            continue
        if i not in page:
            diffs.append("Q%d 只在题库存在、页面缺失（用户答不到这题）" % i)
            continue
        b, p = bank[i], page[i]
        # ① 题干（剥类型标注后逐字）
        nb, np_ = norm_stem(b["stem"], b["tag"]), norm_stem(p["stem"], "")
        if nb != np_:
            pos = next((k for k in range(min(len(nb), len(np_))) if nb[k] != np_[k]),
                       min(len(nb), len(np_)))
            diffs.append("Q%d 题干不等：题库=%r 页面=%r（首个差异在第 %d 字·%s）"
                         % (i, b["stem"], p["stem"], pos + 1,
                            "页面缺内容" if len(nb) > len(np_) else "两源各写各的"))
        # ② 作者侧残留标记（题库侧）
        if AUTHOR_MARK.search(b["stem"]):
            diffs.append("Q%d 题库题干带作者侧标记 %s（⛔不该进用户视野·页面也接不住）"
                         % (i, " ".join(AUTHOR_MARK.findall(b["stem"]))))
        # ③ 类型互证
        bank_open = (len(b["opts"]) == 1 and b["opts"][0][1] == OPEN_PLACEHOLDER)
        if bank_open and not p["open"]:
            diffs.append("Q%d 题库是开放题（选项仅 %s）但页面不是 open 字段" % (i, OPEN_PLACEHOLDER))
        if p["open"] and not bank_open:
            diffs.append("Q%d 页面是开放题但题库选项不止 %s" % (i, OPEN_PLACEHOLDER))
        if b["tag"] == "（可多选）" and not p["multi"]:
            diffs.append("Q%d 题库标（可多选）但页面 multi=False（用户只能单选=答不了）" % i)
        if b["tag"] in ("（单选）", "（多选）") and p["multi"]:
            diffs.append("Q%d 题库标 %s 但页面 multi=True" % (i, b["tag"]))
        # ④ 选项逐字
        if not bank_open and not p["open"]:
            if len(b["opts"]) != len(p["opts"]):
                diffs.append("Q%d 选项数不等：题库 %d 个 / 页面 %d 个"
                             % (i, len(b["opts"]), len(p["opts"])))
            else:
                for (bk, bt), (pk, pt) in zip(b["opts"], p["opts"]):
                    if bk != pk or bt != pt:
                        diffs.append("Q%d 选项不等：题库 %s %r / 页面 %s %r" % (i, bk, bt, pk, pt))
    return diffs


def norm_answer(stem):
    """答卷侧归一：剥类型标注 + 剥作者侧标记（C06 存量兼容关键一步）。
    装前存量 `问卷答案汇总.md` 是按**当时的**题库抄的，题干里带着 `🔴` 这类作者标记；
    本轮把它们从题库删了 ⇒ 若第1关仍按全文比，老用户的真答卷会被新判据打成"不符→补答"。
    ⛔ 这是我自己改动引入的回归，必须在同一轮补上归一（不是放宽判据：内容一字未放）。
    """
    s = stem
    for t in TYPE_TAGS:
        s = s.replace(t, "")
    return AUTHOR_MARK.sub("", s).replace(" ", "").strip()


def parse_answer(path):
    """答卷侧解析：支持两种真形态——4d 写的 md（`**Q<n>. 题干**`）与页面导出 JSON（answers[].question）"""
    if not os.path.isfile(path):
        die("答卷文件不存在：%s" % path, "第1关要的是 4d 写入的 `问卷答案汇总.md` 或页面导出的 JSON。")
    txt = open(path, encoding="utf-8").read()
    got = {}
    if path.endswith(".json") or txt.lstrip().startswith("{"):
        import json
        try:
            data = json.loads(txt)
        except ValueError as e:
            die("答卷 JSON 解析失败：%s" % e, "用页面「复制结果/下载」的整份内容，⛔别截断。")
        for it in data.get("answers", []):
            got[int(it["id"])] = str(it.get("question", "")).strip()
    else:
        for a, b in re.findall(r"^\*\*Q(\d+)\.\s*(.+?)\*\*[ \t]*$", txt, re.M):
            got[int(a)] = b.strip()
    if not got:
        die("答卷里没解析出任何题（两种形态都不匹配）。",
            "md 形态须为 `**Q<n>. 题干**`；JSON 形态须含 answers[].question。")
    return got


def compare_answer(bank, ans):
    diffs = []
    for i in sorted(bank):
        if i not in ans:
            diffs.append("Q%d 答卷缺题（用户答不到/被漏抄）" % i)
            continue
        if norm_answer(bank[i]["stem"]) != norm_answer(ans[i]):
            diffs.append("Q%d 题干与题库不等：题库=%r 答卷=%r" % (i, bank[i]["stem"], ans[i]))
    for i in sorted(set(ans) - set(bank)):
        diffs.append("Q%d 答卷里有、题库里没有（版本漂移）" % i)
    return diffs


def negative_test(bank_path, page_path):
    """变异自检（#S138：对账类检测出厂前须过冒充负例，防假完善）

    ⚠️ 变异必须**只打一侧**：两侧字符串相同处同时改＝两源仍相等＝变异恒不发作伪测试
    （本轮第一版就犯了这个错：M1/M2 的替身在题库与页面各有一份，双侧替换后分叉被抵消，
      2/4 的"低分"其实暴露的是夹具缺陷而非检测缺陷）。
    且必须断言"变异真的落到了文件上"，否则"没抓到"与"没改成功"两种成因会被混为一谈。
    """
    bank_txt = open(bank_path, encoding="utf-8").read()
    page_txt = open(page_path, encoding="utf-8").read()
    cases = [
        ("M1 页面某题干改一字（对页面侧变异）", "page", "你属于哪种", "你属于哪"),
        ("M2 题库某选项文本改一字（对题库侧变异）", "bank", "路径重构", "路径重购"),
        ("M3 页面把（可多选）题的 multi 改 False", "page", '"multi": true, "open": false',
         '"multi": false, "open": false'),
        ("M4 页面删掉一整题（基数被抓）", "page", '{"id": 7, ', None),
        ("M5 题库题干被加作者侧标记 🔴", "bank", '**Q1. 回想一个', '**Q1. 🔴 回想一个'),
    ]
    caught = 0
    for name, side, old, new in cases:
        d = tempfile.mkdtemp(prefix="qsync-neg-")
        b2, p2 = os.path.join(d, "bank.md"), os.path.join(d, "page.html")
        tgt = b2 if side == "bank" else p2
        src_txt = bank_txt if side == "bank" else page_txt
        open(b2, "w", encoding="utf-8").write(bank_txt)
        open(p2, "w", encoding="utf-8").write(page_txt)
        if old not in src_txt:
            print("  ❌ %s ← 变异锚点在该侧文件里不存在＝夹具失效（⛔不算抓到也不算没抓到）" % name)
            continue
        mutated = src_txt.replace(old, new, 1) if new is not None else src_txt.replace(old, "", 1)
        if mutated == src_txt:
            print("  ❌ %s ← 变异未生效＝夹具失效" % name)
            continue
        open(tgt, "w", encoding="utf-8").write(mutated)
        try:
            diffs = compare(parse_bank(b2), parse_page(p2))
            hit = bool(diffs)
            why = diffs[0][:70] if hit else "无分叉＝对账失明"
        except SystemExit:
            hit, why = True, "解析即失败（基数/格式被抓）"
        print("  %s %s ｜%s" % ("✅" if hit else "❌", name, why))
        caught += 1 if hit else 0
    # M6/M7 答卷侧（--answer 模式的标定：拿题库自己当答卷必须绿，改一字必须红）
    b = parse_bank(bank_path)
    mk = os.path.join(tempfile.mkdtemp(prefix="qsync-ans-"), "answers.md")
    open(mk, "w", encoding="utf-8").write(
        "\n".join("**Q%d. %s**" % (i, b[i]["stem"]) for i in sorted(b)) + "\n")
    d6 = compare_answer(b, parse_answer(mk))
    print("  %s M6 题库自身充当答卷 ⇒ 必须全绿（标定，防模式一上线就恒红）｜%s"
          % ("✅" if not d6 else "❌", (d6 or ["0 处不符"]) [0][:60]))
    caught += 1 if not d6 else 0
    t = open(mk, encoding="utf-8").read().replace("你心里知道应该做", "你心里知道应该做做", 1)
    open(mk, "w", encoding="utf-8").write(t)
    d7 = compare_answer(b, parse_answer(mk))
    print("  %s M7 答卷某题干多一个字 ⇒ 必须报红｜%s"
          % ("✅" if d7 else "❌", (d7 or ["没抓到＝答卷模式失明"])[0][:60]))
    caught += 1 if d7 else 0
    total = len(cases) + 2
    print("  变异自检 %d/%d 被抓" % (caught, total))
    return 0 if caught == total else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="33 题题库↔答题页构建期逐字对账")
    ap.add_argument("--bank", default=os.path.join(here, "references", "questionnaire.md"))
    ap.add_argument("--page", default=os.path.join(here, "references", "自建33题-答题页-v1.html"))
    ap.add_argument("--quiet", action="store_true", help="只输出总结行（供 verify 内嵌）")
    ap.add_argument("--negative-test", action="store_true", help="变异自检：各类漂移必须全被抓")
    ap.add_argument("--answer", default=None,
                    help="第1关用法：对 4d 写入的 问卷答案汇总.md / 页面导出 JSON 逐题核对题库（step4 用它替代肉眼比）")
    a = ap.parse_args()
    bank = parse_bank(a.bank)
    if a.answer:
        ans = parse_answer(a.answer)
        diffs = compare_answer(bank, ans)
        if not diffs:
            print("✅ 第1关（答卷↔题库）%d/%d 逐题相等（已按 Rule A 剥类型标注与作者侧标记归一·内容零放宽）" % (len(bank), len(bank)))
            sys.exit(0)
        print("❌ 第1关（答卷↔题库）不符 %d 处：" % len(diffs))
        for d in diffs:
            print("   · " + d)
        print("   归因口径（C06）：先跑不带 --answer 的两源对账。两源分叉=包内问题（⛔不指向用户）；"
              "两源绿而答卷不符=答卷侧问题，按题号向用户指出、以题库为准。")
        sys.exit(1)
    bank, page = parse_bank(a.bank), parse_page(a.page)
    if a.negative_test:
        sys.exit(negative_test(a.bank, a.page))
    diffs = compare(bank, page)
    if not diffs:
        print("✅ 两源逐字相等：题库↔答题页 33/33（题干剥类型标注后等、类型互证、选项逐字等、无作者侧残留）")
        sys.exit(0)
    if a.quiet:
        print("❌ 题库↔答题页分叉 %d 处（明细去 --quiet 重跑）" % len(diffs))
        sys.exit(1)
    print("❌ 题库↔答题页分叉 %d 处（step4 第1关会把这记成「用户手改卷」·⛔那是错误归因）：" % len(diffs))
    for d in diffs:
        print("   · " + d)
    print("   怎么办：以题库为准修页面（题干/选项/类型三处对齐），"
          "作者侧标记从题库删；改完重跑本脚本，33/33 才算过。")
    sys.exit(1)


if __name__ == "__main__":
    main()
