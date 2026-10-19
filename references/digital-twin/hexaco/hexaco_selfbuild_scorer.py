#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hexaco_selfbuild_scorer.py — 自建 HEXACO-100 自动计分器（确定性·AI 不参与数值计算）

## 为什么存在（C27·2026-10-15 E2E 修包线）
题库 §八 第 4 条自陈待办：「过闸后：写入 `hexaco_selfbuild_scorer.py`（自动计分）→ 随包」。
本轮之前全库 find 无此文件，D2 计分由 **AI 手算 96 个数**。实测后果（E2E 实录）：
AI 首轮手抄就抄错 2 题（Q34/35 写成 2，真值 3），改逐字解析才修正——96 个数走概率路径必漂。
本脚本把「反向计分 + 维度均分 + 效度闸 + 直线作答检测」全部机械化，同份输入必得同份输出。

## 用法
  python3 hexaco_selfbuild_scorer.py <答题页导出的.json>            # 人话报告
  python3 hexaco_selfbuild_scorer.py <答题页导出的.json> --json     # 机器可读 JSON
  python3 hexaco_selfbuild_scorer.py --selftest                     # 内置夹具自测（出厂判据）
  可选 --bank <题库.md> 覆盖题库路径（默认=本脚本同目录的 自建100题-分身版-题库-v1.md）

## 设计口径（三条硬规则）
  1. **题库是唯一真源**：题号→维度、正/反、效度标准、题号→facet 归属全部从
     §〇/§〇·2/§一-§七 表格**解析**得到，脚本内 ⛔ 不硬抄任何题号表（硬抄=第二个源=漂移起点，正是 C27 病根）。
  2. **页面导出自带 reverse_items/dims 只做对账，不做判据**：与题库逐格比对，不一致显形
     并标明「以题库为准」（页面是便利副本，题库是量表规格）。
  3. **facet 级读数（C25·2026-10-15 解锁）**：归属从题库 §〇·2 归属表**解析**（同规则 1，
     脚本内不内置表）；面分＝该面 4 题反向调整后的均分（与维度分同尺 1-5）。页面导出
     `facet_groups` 只做对账不做判据。Altruism 为间质面、自建卷不测，不产出。

## 退出码契约（供装机链/AI 判读，⛔不靠读文案猜）
  0 = 计分完成·效度通过·无直线告警
  1 = 有有效读数但命中直线作答告警（建议重答该段）
  2 = 作答作废（硬效度闸 V1/V3/V4 未过·V2 为标注制不在此列 P30）或 输入/题库不可用（fail-closed）

version: v1.1（2026-10-15·C25 解锁 facet 输出；v1.0=C27 首发）
"""
import argparse
import json
import os
import re
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）


DIM_LETTERS = ("H", "E", "X", "A", "C", "O")
RUN_MIN = 10          # 同维/跨维连续同分 ≥10 题 → 直线告警（C11 机械判据·清单 C6 原文）
SHARE_MAX = 0.40      # 全卷单一分值占比 >40% → 直线告警
DUR_MIN = 120         # 导出 duration_sec <120s → 疑似未逐题读（C26 真计时阈值；存量卷无该字段=跳过不判）
BANK_NAME = "自建100题-分身版-题库-v1.md"


def die(msg, remedy, code=2):
    """人话报错 + 怎么办（⛔不抛裸 traceback——同 hexaco_slice_generator.validate_vec 口径）"""
    print("❌ " + msg)
    print("   怎么办：" + remedy)
    sys.exit(code)


# ─────────────────────────────────────────────────────────────────────────
# 题库解析（唯一真源）
# ─────────────────────────────────────────────────────────────────────────
def load_blueprint(bank_path):
    """从题库 md 解析出 {dims, direction, validity, warnings}；结构不符即 fail-closed。"""
    if not os.path.isfile(bank_path):
        die("找不到题库：%s" % bank_path,
            "题库须与本脚本同目录（包内 references/digital-twin/hexaco/）。"
            "确实放在别处请加 --bank <题库绝对路径>；⛔不接受跳过题库直接用页面内置表计分。")
    text = open(bank_path, encoding="utf-8").read()
    warnings = []

    # §〇 量表结构表：| **H 诚实-谦逊** | 真诚/公平/戒贪/谦逊 | 1-16 | 各半 |
    dims = []
    for cells in _rows(text):
        head = cells[0].replace("*", "").strip()
        m = re.match(r"^([HEXACO])\s+(\S+)$", head)
        if not m or len(cells) < 3:
            continue
        rng = cells[2].strip()
        rm = re.match(r"^(\d+)-(\d+)$", rng)
        if not rm:
            continue
        dims.append({"letter": m.group(1), "cn": m.group(2),
                     "facets": [f.strip() for f in cells[1].split("/") if f.strip()],
                     "lo": int(rm.group(1)), "hi": int(rm.group(2))})
    if len(dims) != 6:
        die("题库 §〇 结构表解析到 %d 个维度（应为 6）。" % len(dims),
            "检查题库 §〇 表格是否被改动（列序须为 维 / facet×4 / 题号 / 正反）。")
    if tuple(d["letter"] for d in dims) != DIM_LETTERS:
        die("题库 §〇 维度字母顺序是 %s（应为 %s）。" % (
            "".join(d["letter"] for d in dims), "".join(DIM_LETTERS)),
            "维度顺序决定题号段归属，请勿改动 §〇 表行序。")
    # 题号段必须连续无缝覆盖 1..96
    expect = 1
    for d in dims:
        if d["lo"] != expect or d["hi"] - d["lo"] + 1 != 16:
            die("题库 §〇 题号段不连续：%s 维是 %d-%d（期望从 %d 起、16 题）。"
                % (d["letter"], d["lo"], d["hi"], expect),
                "每维必须 16 题且首尾相接覆盖 1-96，请核对 §〇 表『题号』列。")
        expect = d["hi"] + 1
    if expect != 97:
        die("题库 §〇 题号覆盖到 %d（应到 96）。" % (expect - 1), "请核对 §〇 表『题号』列。")

    # §〇·2 题号→facet 归属表（C25 唯一真源）：| H Honesty-Humility | 真诚 | Sincerity | 1,2,3,4 |
    facet_rows = []
    for cells in _rows(text):
        if len(cells) != 4:
            continue
        fm = re.match(r"^([HEXACO])\s+([A-Za-z][A-Za-z \-]*)$", cells[0])
        qm = re.match(r"^\d+(,\d+)*$", cells[3].replace(" ", ""))
        if not fm or not qm:
            continue
        facet_rows.append({"letter": fm.group(1), "domain_en": fm.group(2).strip(),
                           "cn": cells[1], "en": cells[2],
                           "questions": [int(x) for x in cells[3].split(",")]})
    if len(facet_rows) != 24:
        die("题库 §〇·2 题号→facet 归属表解析到 %d 行（应为 24＝6 维×4 面）。" % len(facet_rows),
            "该表是 facet 级读数与 D4 人格向量的唯一归属真源；行形如「| H Honesty-Humility | 真诚 | Sincerity | 1,2,3,4 |」，缺行/串行都判红。")
    facets = {}
    for d in dims:
        rows_d = [r for r in facet_rows if r["letter"] == d["letter"]]
        if [r["cn"] for r in rows_d] != d["facets"]:
            die("%s 维归属表的 facet 名序与 §〇 结构表不一致：%s ≠ %s"
                % (d["letter"], "/".join(r["cn"] for r in rows_d), "/".join(d["facets"])),
                "两张表同在本文件内、必须逐字一致（题库内自对账）——改一处就要同步另一处。")
        seen = []
        for r in rows_d:
            for q in r["questions"]:
                if q in seen:
                    die("归属表题号 %d 重复归属两个 facet。" % q, "每题只能属于一个 facet，请核对 §〇·2。")
                seen.append(q)
        if sorted(seen) != list(range(d["lo"], d["hi"] + 1)):
            die("%s 维归属表题号覆盖不全（%d 题，期望 %d-%d 无缝 16 题）。"
                % (d["letter"], len(seen), d["lo"], d["hi"]),
                "每维 16 题须恰好分给 4 个 facet，请核对 §〇·2 题号列。")
        des = set(r["domain_en"] for r in rows_d)
        if len(des) != 1:
            die("%s 维归属表的维度英文名出现 %d 种：%s" % (d["letter"], len(des), sorted(des)),
                "同一维的 4 行第一列应相同，请核对 §〇·2。")
        facets[d["letter"]] = rows_d

    # §一-§六 逐题表：| 1 | 题目 | 正 |
    direction = {}
    for cells in _rows(text):
        if len(cells) < 3:
            continue
        if not re.match(r"^\d{1,2}$", cells[0]):
            continue
        n = int(cells[0])
        flag = cells[-1].strip()
        if not re.match(r"^\d+$", cells[0]) or not (1 <= n <= 96):
            continue
        if flag not in ("正", "反"):
            die("题库第 %d 题的『向』列是「%s」（只能是 正 或 反）。" % (n, flag),
                "『向』列是反向计分的唯一判据，请改回 正/反。")
        if n in direction:
            die("题库第 %d 题出现多次（正向 %s，反向 %s）。" % (n, direction[n], flag),
                "题号必须唯一，请检查是否误增了重复行。")
        direction[n] = flag
    missing = [n for n in range(1, 97) if n not in direction]
    if missing:
        die("题库缺 %d 题的正/反标注（缺：%s）。" % (len(missing), _short(missing)),
            "逐题表『向』列缺一格就没法机械计分，请补齐 §一-§六 表格。")

    # 各半对账（§〇 承诺每维正反各半）
    for d in dims:
        rev = sum(1 for n in range(d["lo"], d["hi"] + 1) if direction[n] == "反")
        if rev != 8:
            warnings.append("题库 §〇 声明「各半」，但 %s 维正向 %d／反向 %d（反=%d）"
                            % (d["letter"], 16 - rev, rev, rev))

    # §七 效度题：| V1 | 这道题请填 **3**。 | 答=3 |
    validity = {}
    for cells in _rows(text):
        if len(cells) < 2 or not re.match(r"^V\d$", cells[0]):
            continue
        m = re.search(r"答\s*([=≥≤≠])\s*(\d)", cells[-1])
        if not m:
            die("效度题 %s 的『通过标准』列解析不出「答=<符号><数字>」（原文：%s）。"
                % (cells[0], cells[-1]), "通过标准须写成 答=3 / 答≥4 / 答≠5 这类可机械判定的式子。")
        validity[cells[0]] = (m.group(1), int(m.group(2)))
    if len(validity) != 4:
        die("题库 §七 解析到 %d 道效度题（应为 V1-V4 共 4 道）。" % len(validity),
            "效度闸是作答质量的唯一机械防线，请核对 §七 表格完整性。")

    return {"dims": dims, "direction": direction, "validity": validity,
            "facets": facets, "warnings": warnings, "path": bank_path}


def _rows(text):
    """把 md 表格行拆成 cell 列表（跳过表头分隔行与 | # | 名列）。"""
    out = []
    for line in text.split("\n"):
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or all(re.match(r"^:?-{2,}:?$", c or "-") for c in cells):
            continue
        out.append(cells)
    return out


def _short(nums):
    return ", ".join(str(n) for n in nums[:12]) + (" …" if len(nums) > 12 else "")


# ─────────────────────────────────────────────────────────────────────────
# 页面导出对账（页面=便利副本·题库=判据）
# ─────────────────────────────────────────────────────────────────────────
def cross_check(payload, bp):
    notes = []
    page_rev = payload.get("reverse_items")
    if isinstance(page_rev, list):
        page_set = set(int(x) for x in page_rev)
        bank_rev = set(n for n, f in bp["direction"].items() if f == "反")
        only_bank = sorted(bank_rev - page_set)
        only_page = sorted(page_set - bank_rev)
        if only_bank or only_page:
            notes.append("页面 reverse_items 与题库不一致：题库独有=%s 页面独有=%s → 以题库为准"
                         % (_short(only_bank) or "无", _short(only_page) or "无"))
    page_dims = payload.get("dims")
    if isinstance(page_dims, dict):
        for d in bp["dims"]:
            rng = page_dims.get(d["letter"])
            if isinstance(rng, list) and [int(rng[0]), int(rng[1])] != [d["lo"], d["hi"]]:
                notes.append("页面 dims.%s=%s 与题库 %d-%d 不一致 → 以题库为准"
                             % (d["letter"], rng, d["lo"], d["hi"]))
    page_fg = payload.get("facet_groups")
    bank_fg = {d["letter"]: {r["cn"]: sorted(r["questions"])
                             for r in bp["facets"][d["letter"]]} for d in bp["dims"]}
    if isinstance(page_fg, dict):
        norm = {k: {kk: sorted(vv) for kk, vv in v.items()}
                for k, v in page_fg.items() if k in bank_fg}
        if norm != bank_fg:
            diff = [k for k in bank_fg if norm.get(k) != bank_fg[k]]
            notes.append("页面 facet_groups 与题库 §〇·2 归属不一致（维：%s）→ 以题库为真源"
                         % ("/".join(diff) if diff else "结构差异"))
    else:
        notes.append("页面导出无 facet_groups（页面版本早于 C25 机制）→ facet 归属按题库 §〇·2 真源计算")
    return notes


# ─────────────────────────────────────────────────────────────────────────
# 计分 + 效度 + 直线检测
# ─────────────────────────────────────────────────────────────────────────
_ALLOW_LEGACY = False  # main() 按 --allow-legacy 置真（P28 逃生口·显式留痕）
EXPECTED_FORM = "BLT-SELF-BUILD-v1"  # P28（皮叔2026-10-18裁决·包面答题页物理单源）：答卷来源指纹


def read_answers(payload, bp):
    # P28②：答卷↔题库绑定（声明即验证）——错页答卷喂本计分器=读数整体错位且原链路无拦截。
    # form 缺失/不符 ⇒ fail-closed rc=2；旧卷有意补判须显式 --allow-legacy（留痕）。
    _form = payload.get("form")
    if _form != EXPECTED_FORM and not _ALLOW_LEGACY:
        die("答卷来源指纹缺失或不符（form=%r，期望 %r）。" % (_form, EXPECTED_FORM),
            "P28：本链路只认 自建100题-答题页-v1（页内导出带 form 字段）。官方壳页/旧版页的答卷题号序不同，"
            "静默计分=整体失真。请改用自建页重答；确属历史卷需人工判读时加 --allow-legacy 重跑（结果会标注来源未验证）。")
    elif _form != EXPECTED_FORM:
        print("⚠️ --allow-legacy：来源指纹未验证（历史卷人工判读场景·P28 留痕）")
    raw = payload.get("answers")
    if not isinstance(raw, dict):
        die("导出的 JSON 里没有 answers 对象（或不是 {} 形态）。",
            "请用答题页「生成结果」后的文本框内容/下载的 .json 文件，⛔不要用截断的片段。")
    ans = {}
    for k, v in raw.items():
        try:
            val = int(v)
        except (TypeError, ValueError):
            die("第 %s 题的值「%s」不是 1-5 的整数。" % (k, v),
                "五点量表只能填 1/2/3/4/5，请回到答题页重答这一题。")
        if not 1 <= val <= 5:
            die("第 %s 题的值 %d 超出 1-5。" % (k, val),
                "五点量表范围是 1=极不同意 … 5=非常同意，请改正后重跑。")
        ans[str(k)] = val
    miss = [n for n in range(1, 97) if str(n) not in ans]
    if miss:
        die("缺 %d 题未答（%s）。" % (len(miss), _short(miss)),
            "维度分=16 题均分，缺一题就不是这个量表的分。请答完再导出（页面按钮在 100/100 才可点）。")
    vmiss = [v for v in sorted(bp["validity"]) if v not in ans]
    if vmiss:
        die("缺效度题答案：%s。" % ", ".join(vmiss),
            "V1-V4 是作答质量闸，缺任一道本次读数不可信。请答完再导出。")
    return ans


def score_dims(ans, bp):
    out = []
    for d in bp["dims"]:
        items = []
        for n in range(d["lo"], d["hi"] + 1):
            v = ans[str(n)]
            items.append(6 - v if bp["direction"][n] == "反" else v)
        total = sum(items)
        out.append({"dim": d["letter"], "name": d["cn"], "n": len(items),
                    "sum": total,
                    "score": round(total / float(len(items)), 2),
                    "raw_items": items,
                    "zero_signal": len(set(items)) == 1})
    return out


def score_facets(ans, bp):
    """facet 分＝该面题数反向调整后的均分（同尺 1-5）。归属来自题库 §〇·2（唯一真源）。"""
    out, meta = {}, {}
    for d in bp["dims"]:
        rows = bp["facets"][d["letter"]]
        dom = rows[0]["domain_en"]
        scores, info = {}, []
        for r in rows:
            items = [6 - ans[str(n)] if bp["direction"][n] == "反" else ans[str(n)]
                     for n in r["questions"]]
            scores[r["en"]] = round(sum(items) / float(len(items)), 2)
            info.append({"facet": r["en"], "facet_cn": r["cn"],
                         "questions": r["questions"], "n": len(items),
                         "score": scores[r["en"]], "zero_signal": len(set(items)) == 1})
        out[dom] = scores
        meta[d["letter"]] = {"domain_en": dom, "facets": info}
    return out, meta


SOFT_VALIDITY = {"V2"}  # P30（2026-10-19）：V2 降级标注制——防不住印象管理者、误伤语义诚实者；作废职分归 V1/V3/V4


def validity_check(ans, bp):
    rows = []
    for vid in sorted(bp["validity"]):
        op, want = bp["validity"][vid]
        got = ans[vid]
        ok = {"=": got == want, "≠": got != want,
              "≥": got >= want, "≤": got <= want}[op]
        soft = vid in SOFT_VALIDITY
        row = {"id": vid, "rule": "答%s%d" % (op, want), "got": got, "pass": ok}
        if soft:
            row["soft"] = True
            if not ok:
                row["note"] = "⚠️ 自评偏完美（P30 标注制·不作废）：H 维读数参考时留意"
        rows.append(row)
    return rows, all(r["pass"] for r in rows if not r.get("soft"))


def straightline(ans, bp):
    """C11 机械判据：①连续 ≥10 题同分（题号序，可跨维）②单一分值占比>40% ③维度零信号。"""
    seq = [(n, ans[str(n)]) for n in range(1, 97)]
    runs, i = [], 0
    while i < len(seq):
        j = i
        while j + 1 < len(seq) and seq[j + 1][1] == seq[i][1]:
            j += 1
        if j - i + 1 >= RUN_MIN:
            runs.append({"value": seq[i][1], "start": seq[i][0], "end": seq[j][0],
                         "count": j - i + 1})
        i = j + 1
    counts = {}
    for _, v in seq:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.items(), key=lambda kv: (kv[1], -kv[0]))
    share = {"value": top[0], "count": top[1], "ratio": round(top[1] / 96.0, 4)}
    return runs, share, share["count"] / 96.0 > SHARE_MAX


# ─────────────────────────────────────────────────────────────────────────
# 输出
# ─────────────────────────────────────────────────────────────────────────
FACETS_NOTE = ("facet 归属真源=题库 §〇·2 表（本脚本不内置）；面分＝4 题均分（同尺 1-5）。"
               "Altruism 为间质面，自建卷不测、不产出（D4 该面保留模板默认或经官方卷校准·C34）。")


def render_human(res):
    L = []
    L.append("自建 HEXACO-100 · 自动计分（%s）" % os.path.basename(res["bank"]))
    L.append("")
    L.append("六维分（1-5·16 题均分·反向题已 6−原始分）")
    L.append("| 维 | 名称 | 分 | 原始和 | 零信号 |")
    L.append("|---|---|---|---|---|")
    for d in res["dims"]:
        L.append("| %s | %s | %.2f | %d | %s |"
                 % (d["dim"], d["name"], d["score"], d["sum"], "🔴 是" if d["zero_signal"] else "否"))
    L.append("")
    L.append("效度闸（题库 §七·硬闸不过即作废重测；V2=标注制不作废·P30）")
    for r in res["validity"]:
        _mark = "✅" if r["pass"] else ("⚠️ 标注" if r.get("soft") else "❌")
        L.append("  %s %s → 答 %d %s%s" % (r["id"], r["rule"], r["got"], _mark,
                                           ("  " + r["note"]) if r.get("note") else ""))
    L.append("  效度总体：%s" % ("通过 ✅" if res["validity_pass"] else "不通过 ❌（作答作废·须重测）"))
    L.append("")
    if res["runs"] or res["share_flag"] or res["zero_dims"] or res.get("duration_flag"):
        L.append("作答质量告警（C11/C26·机械检出，⛔不靠效度题自陈）")
        for r in res["runs"]:
            L.append("  · 连续同分：第 %d-%d 题全答 %d（%d 题连片）→ 建议重答该段"
                     % (r["start"], r["end"], r["value"], r["count"]))
        if res["share_flag"]:
            L.append("  · 单一分值占比超阈：答 %d 的有 %d 题（%.1f%% > 40%%）→ 全卷疑似没逐题读"
                     % (res["share"]["value"], res["share"]["count"], res["share"]["ratio"] * 100))
        for dim in res["zero_dims"]:
            L.append("  · %s 维零信号（16 题同一读数）→ 该维本次无信息，⛔不拿中性值冒充读数" % dim)
        if res.get("duration_flag"):
            L.append("  · 本次用时 %s 秒 < %d 秒 → 96 题物理上读不完，疑似未逐题作答，建议重测" % (res.get("duration_sec"), DUR_MIN))
    else:
        L.append("作答质量：未命中直线/过快告警（无 ≥10 题连片同分·无单一分值占比>40%·六维皆有信号·用时合规或无字段）")
    if res["notes"]:
        L.append("")
        L.append("题库↔页面对账")
        for n in res["notes"]:
            L.append("  ⚠️ " + n)
    if res["bank_warnings"]:
        L.append("")
        L.append("题库结构对账")
        for w in res["bank_warnings"]:
            L.append("  ⚠️ " + w)
    L.append("")
    L.append("facet 级读数（24 面·归属=题库 §〇·2·面分=该面题数均分·同尺 1-5）")
    L.append("| 维 | facet | 题库名 | 题号 | 分 | 零信号 |")
    L.append("|---|---|---|---|---|---|")
    for d in res["dims"]:
        for f in res["facet_meta"][d["dim"]]["facets"]:
            L.append("| %s | %s | %s | %s | %.2f | %s |"
                     % (d["dim"], f["facet"], f["facet_cn"],
                        ",".join(str(x) for x in f["questions"]),
                        f["score"], "🔴 是" if f["zero_signal"] else "否"))
    L.append("  %s" % FACETS_NOTE)
    L.append("")
    L.append("判定：%s（退出码 %d）" % (res["verdict"], res["exit_code"]))
    return "\n".join(L)


def compute(payload, bp):
    ans = read_answers(payload, bp)
    dims = score_dims(ans, bp)
    vrows, vpass = validity_check(ans, bp)
    runs, share, share_flag = straightline(ans, bp)
    facets, facet_meta = score_facets(ans, bp)
    zero_dims = [d["dim"] for d in dims if d["zero_signal"]]
    notes = cross_check(payload, bp)
    dur = payload.get("duration_sec")  # C26：页面真计时（存量卷缺字段=None 不判·向后兼容）
    dur_flag = isinstance(dur, (int, float)) and 0 < dur < DUR_MIN
    if not vpass:
        verdict, code = "作答作废：效度题未通过，请重测后再进 D3", 2
    elif runs or share_flag or zero_dims or dur_flag:
        verdict, code = "读数有效但命中直线/过快作答告警：按上方建议重答该段，确认后再进 D3", 1
    else:
        verdict, code = "计分完成：效度通过、无直线告警，可进 D3 偏移与基调协商", 0
    out = [{"dim": d["dim"], "name": d["name"], "score": d["score"], "sum": d["sum"],
            "n": d["n"], "zero_signal": d["zero_signal"]} for d in dims]
    return {"instrument": "selfbuild-hexaco-100-v1",
            "bank": bp["path"],
            "bank_sha8": _sha8(open(bp["path"], encoding="utf-8").read()),
            "answered_at": payload.get("answered_at"),
            "dims": out,
            "facets": facets,
            "facet_meta": facet_meta,
            "facets_note": FACETS_NOTE,
            "validity": vrows, "validity_pass": vpass,
            "runs": runs, "share": share, "share_flag": share_flag,
            "duration_sec": dur, "duration_flag": dur_flag,
            "zero_dims": zero_dims, "notes": notes, "bank_warnings": bp["warnings"],
            "verdict": verdict, "exit_code": code,
            "answers_sorted": {k: ans[k] for k in sorted(ans, key=lambda s: (s.startswith("V"), s))}}


def _sha8(s):
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def _strip_volatile(res):
    """确定性输出：不重复内嵌原始答案（答案已在输入文件里），只留判读面。"""
    d = dict(res)
    d.pop("answers_sorted", None)
    return d


# ─────────────────────────────────────────────────────────────────────────
# 自测（出厂判据·AI 不心算任何数）
# ─────────────────────────────────────────────────────────────────────────
def selftest(bp):
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("  %s %s%s" % ("✅" if cond else "❌", name, "" if cond else " ← " + detail))
        if not cond:
            ok = False

    def fake(vals):
        a = {str(i): vals(i) for i in range(1, 97)}
        a.update({"V1": 3, "V2": 4, "V3": 4, "V4": 2})
        return {"answers": a, "answered_at": "T", "form": "BLT-SELF-BUILD-v1"}

    # F1 全答 5：每维正反各半 → 反向题变 1 → 均分必为 3.00（这一条同时验算反向表）
    r1 = compute(fake(lambda n: 5), bp)
    check("F1 全答5 ⇒ 六维均=3.00（反向计分+各半不变量）",
          all(d["score"] == 3.0 for d in r1["dims"]), str(r1["dims"]))
    # F2 全答 1 ⇒ 同样 3.00（镜像）
    r2 = compute(fake(lambda n: 1), bp)
    check("F2 全答1 ⇒ 六维均=3.00", all(d["score"] == 3.0 for d in r2["dims"]), str(r2["dims"]))
    # F3 正向题全5、反向题全1 ⇒ 每题计分后皆 5 ⇒ 维度分 5.00
    r3 = compute(fake(lambda n: 5 if bp["direction"][n] == "正" else 1), bp)
    check("F3 正=5/反=1 ⇒ 六维均=5.00", all(d["score"] == 5.0 for d in r3["dims"]), str(r3["dims"]))
    # F4 反向：正=1/反=5 ⇒ 皆 1 ⇒ 1.00
    r4 = compute(fake(lambda n: 1 if bp["direction"][n] == "正" else 5), bp)
    check("F4 正=1/反=5 ⇒ 六维均=1.00", all(d["score"] == 1.0 for d in r4["dims"]), str(r4["dims"]))
    # F5 确定性：同一输入跑两次，JSON 字节级一致
    p = fake(lambda n: (n % 5) + 1)
    j1 = json.dumps(_strip_volatile(compute(p, bp)), ensure_ascii=False, sort_keys=True)
    j2 = json.dumps(_strip_volatile(compute(json.loads(json.dumps(p)), bp)),
                    ensure_ascii=False, sort_keys=True)
    check("F5 同份输入跑两次输出完全一致（C27 验收本体）", j1 == j2)
    # F6 直线检测：E2E 实录病灶（第 2-35 题连片答 3·Q1=2；36 题后真值清单未记，取中性卷）
    def e2e(n):
        if n == 1:
            return 2
        if 2 <= n <= 35:
            return 3
        return (4, 5, 2, 1)[n % 4]   # 3-值不出现的周期4中性卷：⛔不用奇偶式（与反向题偶数号同相
                                     #   → 反向计分后整维同值=假零信号），也⛔不用含 3 的周期（会连片外溢）
    r6 = compute(fake(e2e), bp)
    hit = [x for x in r6["runs"] if x["start"] == 2 and x["end"] == 35]
    check("F6 连片 2-35 全答3 ⇒ 检出该段（≥10 题同分）", bool(hit), str(r6["runs"]))
    check("F6b 零信号维度恰为 ['E']（不多报也不漏报）", r6["zero_dims"] == ["E"], str(r6["zero_dims"]))
    check("F6c 全卷单一分值占比未超 40% ⇒ 不误报全卷",
          r6["share"]["count"] / 96.0 <= SHARE_MAX, str(r6["share"]))
    check("F6d 告警走退出码 1（不是 0·不是静默）", r6["exit_code"] == 1, str(r6["exit_code"]))
    # F7 效度不过 ⇒ 作废（rc=2）
    bad = fake(lambda n: 3)
    bad["answers"]["V1"] = 5
    r7 = compute(bad, bp)
    check("F7 V1 未按指令 ⇒ 作答作废·rc=2", r7["exit_code"] == 2 and not r7["validity_pass"])
    # F7b P30（2026-10-19）：V2=5 不再作废——降级为 H 读数标注（误伤诚实人防线）
    v2p = fake(lambda n: 3)
    v2p["answers"]["V2"] = 5
    r_v2 = compute(v2p, bp)
    check("P30 V2=5 不作废（validity_pass 仍真·硬闸V1/V3/V4在岗）", r_v2["validity_pass"] and r_v2["exit_code"] != 2,
          "pass=%s code=%s" % (r_v2["validity_pass"], r_v2["exit_code"]))
    check("P30 V2=5 输出挂自评偏完美标注", any("自评偏完美" in str(r) for r in r_v2["validity"]), str(r_v2["validity"]))
    # F7c P28：无来源指纹 ⇒ fail-closed rc=2
    nf = fake(lambda n: 3)
    nf.pop("form", None)
    import contextlib as _cl, io as _io
    _buf = _io.StringIO()
    try:
        with _cl.redirect_stdout(_buf):
            compute(nf, bp)
        check("P28 缺 form ⇒ 硬失败", False, "未报错")
    except SystemExit as e:
        check("P28 缺 form ⇒ rc=2 拒收（错页防线）", e.code == 2)
    # F8 页面 reverse_items 被改动 ⇒ 对账显形（题库为准）
    tam = fake(lambda n: (n % 5) + 1)
    tam["reverse_items"] = [i for i in range(2, 97, 2)]
    r8 = compute(tam, bp)
    check("F8 页面反向表与题库不一致 ⇒ 对账显形（题库漏标 11 号）",
          any("reverse_items" in n for n in r8["notes"]), str(r8["notes"]))
    # F9 缺题 ⇒ fail-closed（不静默算残缺分）
    miss = fake(lambda n: 3)
    del miss["answers"]["42"]
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            compute(miss, bp)
        check("F9 缺 1 题 ⇒ 硬失败", False, "未报错")
    except SystemExit as e:
        check("F9 缺 1 题 ⇒ 硬失败（exit 2·报错文案已捕获不外泄）", e.code == 2)
    # F10 facet 产出（C25 解锁后）：24 面全出数·全答 5 时面分必 3.00
    nf = sum(len(v) for v in r1["facets"].values())
    check("F10 facet=24 面全出数（6 域×4 面·归属来自题库 §〇·2）",
          nf == 24 and len(r1["facets"]) == 6, "n=%d domains=%d" % (nf, len(r1["facets"])))
    check("F10b 全答5 ⇒ 24 facet 均=3.00（面分与反向表联动）",
          all(s == 3.0 for dom in r1["facets"].values() for s in dom.values()),
          str(r1["facets"]))
    # F11 变异测试（防自测恒真）：把 X 维第 34 题的「反」改成「正」，全答5 时 X 必不再等 3.00
    bp_m = {"dims": bp["dims"], "validity": bp["validity"], "warnings": bp["warnings"],
            "facets": bp["facets"], "path": bp["path"], "direction": dict(bp["direction"])}
    assert bp_m["direction"][34] == "反", "题库第 34 题应为反向题，夹具前提失效"
    bp_m["direction"][34] = "正"
    r11 = compute(fake(lambda n: 5), bp_m)
    xm = [d for d in r11["dims"] if d["dim"] == "X"][0]
    check("F11 变异（34 题正反改错）⇒ 全答5 的 X 维偏离 3.00（=判据真在被算）",
          abs(xm["score"] - 3.0) > 0.01, "X=%.2f" % xm["score"])
    # F12 facet 级变异：34 题只属「胜任自尊」一面 ⇒ 只有该面偏离，同维余三面不动
    xfac = r11["facets"].get("Extraversion", {})
    check("F12 变异题 34 只拖偏其归属面（Social Self-Esteem≠3.00·同维余三面=3.00）",
          abs(xfac.get("Social Self-Esteem", 3.0) - 3.0) > 0.01
          and len(xfac) == 4
          and all(abs(v - 3.0) < 0.001 for k, v in xfac.items() if k != "Social Self-Esteem"),
          str(xfac))
    # F13 facet 英文名 ↔ 下游生成器 DOMAIN_FACETS 键逐名对账（两套词表曾互不认账·C25 根治面）
    gen_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(bp["path"])),
                                             "..", "k2-slice-generator",
                                             "hexaco_slice_generator.py"))
    if os.path.isfile(gen_path):
        gt = io.open(gen_path, encoding="utf-8").read()
        gm = re.search(r"DOMAIN_FACETS = \{(.*?)\n\}", gt, re.S)
        pairs = re.findall(r'"([A-Za-z \-()]+)":\s*\[([^\]]*)\]', gm.group(1)) if gm else []
        want = {k: set(x.strip().strip('"') for x in v.split(",") if x.strip())
                for k, v in pairs if not k.startswith("Altruism")}
        got = {rows[0]["domain_en"]: set(r["en"] for r in rows)
               for rows in bp["facets"].values()}
        diff = {k: sorted(want[k] ^ got.get(k, set())) for k in want if want[k] != got.get(k)}
        check("F13 归属表英文名与生成器 DOMAIN_FACETS 逐域全等（24 名·Altruism 除外）",
              not diff and len(want) == 6, "diff=%s" % diff)
    else:
        print("  ℹ️ F13 跳过：生成器不在旁路（期望 %s）——包内/装机态均为同层兄弟目录，正常态应命中" % gen_path)
    # F14 时长阈值（C26）：正常卷+duration_sec=10 ⇒ 告警 rc=1；存量卷无字段 ⇒ 不受影响 rc=0
    def _cyc(n):
        return (n % 4) + 1
    r14a = compute(fake(_cyc), bp)
    check("F14a 存量卷无 duration 字段=不判（正常卷 rc=0）",
          r14a["exit_code"] == 0, str(r14a["exit_code"]))
    p_fast = fake(_cyc)
    p_fast["duration_sec"] = 10
    r14b = compute(p_fast, bp)
    check("F14b duration_sec=10 ⇒ rc=1 且报告含用时告警",
          r14b["exit_code"] == 1 and "秒 < 120 秒" in render_human(r14b),
          str(r14b["exit_code"]))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="自建 HEXACO-100 自动计分器（确定性）")
    ap.add_argument("answers_json", nargs="?", help="答题页「生成结果」导出的 .json 或粘贴文本文件")
    ap.add_argument("--allow-legacy", action="store_true", dest="allow_legacy",
                    help="P28 逃生口：跳过来源指纹校验（历史卷人工判读用·输出会标注）")
    ap.add_argument("--bank", default=None, help="题库 md 路径（默认=脚本同目录 %s）" % BANK_NAME)
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON（去原始答案）")
    ap.add_argument("--selftest", action="store_true", help="跑内置夹具（出厂判据）")
    a = ap.parse_args()
    global _ALLOW_LEGACY
    _ALLOW_LEGACY = bool(getattr(a, "allow_legacy", False))
    bank = a.bank or os.path.join(os.path.dirname(os.path.abspath(__file__)), BANK_NAME)
    bp = load_blueprint(bank)
    if a.selftest:
        print("selftest（题库=%s）" % bank)
        sys.exit(selftest(bp))
    if not a.answers_json:
        die("没给答卷文件。",
            "用法：python3 hexaco_selfbuild_scorer.py <答题页导出的.json>；"
            "想看判据是否完好先跑 --selftest。")
    path = a.answers_json
    if not os.path.isfile(path):
        die("答卷文件不存在：%s" % path, "确认路径；答题页下载的文件名形如 hexaco-selfbuild-answers-YYYY-MM-DD.json")
    try:
        payload = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        die("答卷 JSON 解析失败：%s" % e,
            "多半是复制时截断或带了多余文字——请用「下载 .json 文件」按钮的整份文件。")
    if not isinstance(payload, dict):
        die("答卷内容不是 JSON 对象。", "请传答题页导出的完整 payload。")
    res = compute(payload, bp)
    if a.json:
        print(json.dumps(_strip_volatile(res), ensure_ascii=False, indent=1, sort_keys=True))
    else:
        print(render_human(res))
    sys.exit(res["exit_code"])


if __name__ == "__main__":
    main()
