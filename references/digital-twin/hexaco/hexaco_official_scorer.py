#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hexaco_official_scorer.py — 官方 HEXACO-100 自动计分器（确定性·AI 不参与数值计算）

## 为什么存在（C34·2026-10-15 布洛陀 E2E 修包线）
官方卷 D2 计分此前=「把答案粘贴给 AI，AI 读 PDF 心算」——自建卷的实测证明 AI 手抄
96 个数首轮就错 2 题（C27），官方卷 100 题×反向换算同病。本脚本把官方计分机械化：
**键表不在脚本里**——从随包 `ScoringKeys_100.pdf` 构建期派生 `hexaco_official_keytable-100.json`
（含 PDF sha256 溯源头），脚本运行时解析该表；每次计分先核 `PDF 实况 sha == 记录 sha`，
PDF 被动过 ⇒ 拒算显形（⛔拿旧键表算新量表）。同 C27 律：源只有一份，⛔硬抄=漂移起点。

## 用法
  python3 hexaco_official_scorer.py --build-keytable          # 从 PDF 派生/重建键表（需 pdftotext）
  python3 hexaco_official_scorer.py <官方答卷.json>           # 人话报告（六维+25 facet 含间质面）
  python3 hexaco_official_scorer.py <官方答卷.json> --json     # 机器可读 JSON
  python3 hexaco_official_scorer.py --verify-keytable          # 重抽 PDF 与键表逐格对账（键表过期显形）
  python3 hexaco_official_scorer.py --selftest                 # 出厂判据（合成夹具·不碰答卷）
  可选 --pdf <路径> / --keytable <路径> 覆盖默认（默认=本脚本同目录）

## 设计口径（四条硬规则）
  1. **PDF 是唯一真源**：键表 json = PDF 的机器投影＋sha 溯源头；运行时双验（json 头 sha ↔ PDF 实况 sha）。
  2. **脚本内 ⛔ 不硬抄任何题号/键值**：条目归属、R 标记全部来自键表解析。
  3. **维度分=该域 4 个 facet 分的均值**（官方口径；本量表各面等题数⇒与全 16 题均分等价，注明取舍）。
     Altruism 为间质面（97-100），独立输出，⛔并入 A 维。
  4. **译名对账**：PDF 官方键名与本包生成器 DOMAIN_FACETS 若有一字之差（实测：Forgiveness/Forgivingness），
     映射登记在键表 json `aliases`（人工核一次·数据面），脚本不内置；构建时 fail-loud 校验全覆盖。
     直线作答检测不在本脚本（判据真源=自建卷 hexaco_selfbuild_scorer.py，⛔两处各写一份阈值=新漂移源）。

## 退出码契约（供装机链/AI 判读）
  0 = 计分完成
  2 = fail-closed：键表缺失/PDF sha 不符/答卷缺题越界/生成器名对账破裂（拒算即显形，⛔不带病出分）

version: v1.0（2026-10-15·布洛陀 E2E 修包线 C34）
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）


HERE = os.path.dirname(os.path.abspath(__file__))
PDF_NAME = "ScoringKeys_100.pdf"
KT_NAME = "hexaco_official_keytable-100.json"
GEN_NAME = os.path.join("..", "k2-slice-generator", "hexaco_slice_generator.py")
SCHEMA = "blt-hexaco100-keys-v1"
DOMAIN_ORDER = ["Honesty-Humility", "Emotionality", "Extraversion",
                "Agreeableness", "Conscientiousness", "Openness to Experience"]


def die(msg, remedy, code=2):
    print("❌ " + msg)
    print("   怎么办：" + remedy)
    sys.exit(code)


def _sha8(b):
    return hashlib.sha256(b).hexdigest()


# ─────────────────────────────────────────────────────────────────────────
# 键表：构建（pdftotext 投影）与装载（含 PDF 实况对账）
# ─────────────────────────────────────────────────────────────────────────
def extract_keys(pdf_text):
    """从 pdftotext -layout 文本解析 {facet: [(q, R?), ...]} + 域归属 + 间质面。fail-closed。"""
    dom, scales, inter = None, {}, {}
    for line in pdf_text.splitlines():
        dm = re.match(r"^\s*(" + "|".join(map(re.escape, DOMAIN_ORDER)) + r")\s*$", line)
        if dm:
            dom = dm.group(1)
            continue
        im = re.match(r"^\s*\(interstitial facet scale\)\s*(\S+)\s+(.+?)\s*$", line)
        if im:
            inter[im.group(1)] = _items(im.group(2))
            continue
        sm = re.match(r"^\s{2,}([A-Za-z][A-Za-z \-]*[a-z])\s{2,}([\dR,\s]+)$", line)
        if sm and dom:
            name = sm.group(1).strip()
            if name in scales:
                die("键表解析到重名 facet「%s」" % name, "PDF 版式可能变了——重跑 pdftotext 人工比对，⛔手改键表。")
            scales[name] = {"domain": dom, "items": _items(sm.group(2))}
    if len(scales) != 24 or len(inter) != 1:
        die("从 PDF 解析到 %d 个 facet 面（应 24）/ 间质面 %d（应 1）。" % (len(scales), len(inter)),
            "PDF 版式或内容变了（本解析器认 6 域头×4 面＋1 间质行）——先跑 pdftotext -layout 人工看差异，再决定修解析器还是重制量表。")
    return scales, inter


def _items(s):
    out = []
    for tok in re.findall(r"(\d+)(R?)", s):
        out.append({"q": int(tok[0]), "r": tok[1] == "R"})
    if not out:
        raise ValueError("空题号列表: %r" % s)
    return out


def generator_facet_names():
    """解析下游生成器 DOMAIN_FACETS 名集（对账用·F13 同构；找不到返回 None）。"""
    gp = os.path.normpath(os.path.join(HERE, GEN_NAME))
    if not os.path.isfile(gp):
        return None
    gt = open(gp, encoding="utf-8").read()
    gm = re.search(r"DOMAIN_FACETS = \{(.*?)\n\}", gt, re.S)
    if not gm:
        return None
    pairs = re.findall(r'"([A-Za-z \-()]+)":\s*\[([^\]]*)\]', gm.group(1))
    return {k: set(x.strip().strip('"') for x in v.split(",") if x.strip()) for k, v in pairs}


def build_keytable(pdf_path, out_path):
    if not os.path.isfile(pdf_path):
        die("找不到官方键表 PDF：%s" % pdf_path, "随包件 ScoringKeys_100.pdf 应在本脚本同目录。")
    try:
        r = subprocess.run(["pdftotext", "-layout", pdf_path, "-"],
                           capture_output=True, timeout=60)
        r.check_returncode()
    except Exception as e:
        die("pdftotext 抽取失败：%r" % e,
            "构建键表需 poppler（Mac: brew install poppler；Win: 装 poppler 或用 WSL）。端用户机可跳过——随包键表已构建好。")
    text = r.stdout.decode("utf-8", "replace")
    scales, inter = extract_keys(text)
    allq = [it["q"] for f in scales.values() for it in f["items"]]
    allq += [it["q"] for v in inter.values() for it in v]
    if sorted(allq) != list(range(1, 101)):
        die("键表题号覆盖异常（%d 个·应 1-100 无缝无重）" % len(allq),
            "PDF 抽出来的键表不完整，⛔禁止带病出键表——人工比对 pdftotext 输出。")
    # 与下游生成器名集对账：差额须恰好可被 aliases 弥合，且只许人工核过的映射进 aliases
    aliases = {}
    gn = generator_facet_names()
    if gn is not None:
        gen_all = set().union(*gn.values())
        pdf_all = set(scales) | set(inter)
        only_pdf, only_gen = pdf_all - gen_all, gen_all - pdf_all
        if len(only_pdf) == len(only_gen):
            ps, gs = sorted(only_pdf), sorted(only_gen)
            if len(ps) > 0:
                print("⚠️ PDF 名与生成器名有 %d 对差异，按序登记 aliases（务必人工核对语义同源）：" % len(ps))
                for a, b in zip(ps, gs):
                    aliases[a] = b
                    print("   %s → %s" % (a, b))
        elif only_pdf:
            die("PDF facet 名与生成器名集差集不对称（PDF 独有 %s·生成器独有 %s）"
                % (sorted(only_pdf), sorted(only_gen)),
                "两边量表结构可能不是一致的东西，人工核对后再构建，⛔硬凑映射。")
    kt = {"$schema": SCHEMA,
          "source": os.path.basename(pdf_path),
          "pdf_sha256": _sha8(open(pdf_path, "rb").read()),
          "extracted_via": "pdftotext -layout（构建期一次性·运行时只核 sha 不重抽）",
          "extracted_at": __import__("datetime").date.today().isoformat(),
          "note": "本 json 是 PDF 的机器投影（hexaco_official_scorer.py --build-keytable 生成）。手改=自毁溯源，改量表请改 PDF 后重建。",
          "aliases": aliases,
          "domain_order": DOMAIN_ORDER,
          "scales": scales,
          "interstitial": inter}
    io_write(out_path, json.dumps(kt, ensure_ascii=False, indent=1, sort_keys=False))
    print("✅ 键表已构建：%s（24 facet＋间质 1·100 题全覆盖·pdf_sha256=%s…）"
          % (out_path, kt["pdf_sha256"][:8]))
    return kt


def io_write(path, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)


def load_keytable(kt_path, pdf_path):
    """装载键表 + PDF 实况对账（每次计分都过·不靠人记得）。"""
    if not os.path.isfile(kt_path):
        die("键表不存在：%s" % kt_path,
            "跑 python3 hexaco_official_scorer.py --build-keytable 从 PDF 重建（需 pdftotext）。⛔手抄键表。")
    kt = json.load(open(kt_path, encoding="utf-8"))
    if kt.get("$schema") != SCHEMA:
        die("键表 schema=%r 与本脚本期望 %r 不符。" % (kt.get("$schema"), SCHEMA),
            "键表与本脚本版本不匹配——用同目录本脚本 --build-keytable 重建。")
    if os.path.isfile(pdf_path):
        live = _sha8(open(pdf_path, "rb").read())
        if live[:16] != kt["pdf_sha256"][:16]:
            die("PDF 与键表已分叉：实况 sha=%s… ≠ 键表记录 sha=%s…" % (live[:8], kt["pdf_sha256"][:8]),
                "量表源（PDF）被改过而键表没重建——这是「判据与对象不同源」的实锤，拒算。"
                "确认改动合法后跑 --build-keytable 重建（并把 PDF+json 一起走发版同步）。")
        kt["_pdf_checked"] = True
    else:
        kt["_pdf_checked"] = False  # 装机态只带 json 不带 PDF 的降级：如实标注，⛔冒充核过
    return kt


# ─────────────────────────────────────────────────────────────────────────
# 计分
# ─────────────────────────────────────────────────────────────────────────
def read_answers(payload, kt):
    raw = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        die("答卷 JSON 没有 answers 对象。", "用官方答题页「下载答案」的整份 .json（form=HEXACO-PI-R-100）。")
    want = [it["q"] for f in kt["scales"].values() for it in f["items"]]
    for v in kt["interstitial"].values():
        want += [it["q"] for it in v]
    ans = {}
    for k, val in raw.items():
        if not re.match(r"^\d+$", str(k)):
            continue
        try:
            v = int(val)
        except (TypeError, ValueError):
            die("第 %s 题的值「%s」不是 1-5 整数。" % (k, val), "官方五点量表 1=强烈不同意 … 5=强烈同意。")
        if not 1 <= v <= 5:
            die("第 %s 题值 %d 越界 1-5。" % (k, v), "回答卷改正后重导。")
        ans[int(k)] = v
    miss = sorted(set(want) - set(ans))
    if miss:
        die("官方卷缺 %d 题（%s%s）。" % (len(miss), miss[:12], " …" if len(miss) > 12 else ""),
            "缺题就没有该面的读数，⛔算残缺分。补答后重导。")
    return ans


def score(ans, kt):
    facets = {}
    zero = []
    for dom in kt["domain_order"]:
        facets[dom] = {}
    for fname, f in kt["scales"].items():
        items = [6 - ans[it["q"]] if it["r"] else ans[it["q"]] for it in f["items"]]
        val = round(sum(items) / float(len(items)), 2)
        facets[f["domain"]][fname] = val
        if len(set(items)) == 1:
            zero.append("%s·%s" % (f["domain"], fname))
    for fname, v in kt["interstitial"].items():
        items = [6 - ans[it["q"]] if it["r"] else ans[it["q"]] for it in v]
        facets.setdefault("Altruism(interstitial)", {})[fname] = round(sum(items) / float(len(items)), 2)
    dims = {}
    for dom in kt["domain_order"]:
        fs = list(facets[dom].values())
        dims[dom] = round(sum(fs) / float(len(fs)), 2)   # 官方口径=facet 均值的均值（等题数⇒与 16 题均分等价）
    return facets, dims, zero


def render_human(res):
    L = ["官方 HEXACO-100 · 自动计分（键表=%s·PDF 核过=%s）"
         % (os.path.basename(res["keytable"]), "是" if res["pdf_checked"] else "⚠️否(装机态无PDF可核)"), ""]
    L.append("六维分（1-5·该域 4 面均分·反向题已 6−原始分）")
    for dom in res["dims"]:
        L.append("  %-26s %.2f" % (dom, res["dims"][dom]))
    L.append("")
    L.append("25 面读数（24 facet＋间质 Altruism·键名=PDF 官方名经 aliases 对齐生成器）")
    for dom in res["facets"]:
        for f in res["facets"][dom]:
            L.append("  %-26s %-26s %.2f" % (dom, f, res["facets"][dom][f]))
    if res["zero_facets"]:
        L.append("")
        L.append("⚠️ 零信号面（4 题同一读数·该面无信息）：" + " · ".join(res["zero_facets"]))
    L.append("")
    L.append("直线作答检测/效度闸：官方卷不含（判据真源在自建卷 hexaco_selfbuild_scorer.py，⛔两处各写阈值=漂移源）。")
    L.append("判定：%s（退出码 %d）" % (res["verdict"], res["exit_code"]))
    return "\n".join(L)


def compute(payload, kt, kt_path):
    ans = read_answers(payload, kt)
    facets_raw, dims_raw, zero = score(ans, kt)
    al = kt.get("aliases") or {}
    strip = lambda d: {al.get(k, k): v for k, v in d.items()}
    facets = {}
    for dom, v in facets_raw.items():
        facets[dom] = strip(v)
    out = {"instrument": "official-hexaco-100-v1",
           "keytable": kt_path, "pdf_checked": kt.get("_pdf_checked", False),
           "pdf_sha8": kt["pdf_sha256"][:8],
           "answered_at": payload.get("date") or payload.get("answered_at"),
           "dims": dims_raw, "facets": facets, "zero_facets": zero,
           "verdict": "计分完成：六维＋25 面读数可进 D4（间质面单列·⛔并 A 维）",
           "exit_code": 0}
    return out


# ─────────────────────────────────────────────────────────────────────────
# 对账与自测
# ─────────────────────────────────────────────────────────────────────────
def verify_keytable(pdf_path, kt_path):
    kt = json.load(open(kt_path, encoding="utf-8"))
    try:
        r = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, timeout=60)
        r.check_returncode()
    except Exception as e:
        die("pdftotext 不可用（%r），无法对账。" % e, "装 poppler 后重跑；或至少做 sha 核：实况见 --selftest s7。")
    scales, inter = extract_keys(r.stdout.decode("utf-8", "replace"))
    same = (json.dumps(scales, sort_keys=True) == json.dumps(kt["scales"], sort_keys=True)
            and json.dumps(inter, sort_keys=True) == json.dumps(kt["interstitial"], sort_keys=True))
    if not same:
        die("PDF 现文与键表逐格不一致：键表过期或 PDF 被改。", "人工确认后 --build-keytable 重建（PDF+json 同步发版）。")
    live = _sha8(open(pdf_path, "rb").read())
    if live[:16] != kt["pdf_sha256"][:16]:
        die("内容一致但字节级 sha 变了（%s… vs %s…）——可能是注释/元数据级改动。" % (live[:8], kt["pdf_sha256"][:8]),
            "重建键表吸收新 sha，并留 CHANGELOG 记录。")
    print("✅ 键表↔PDF 逐格对账全等（24 facet＋间质·100 题·%s…）" % live[:8])
    return 0


def selftest(kt_path, pdf_path):
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("  %s %s%s" % ("✅" if cond else "❌", name, "" if cond else " ← " + detail))
        if not cond:
            ok = False

    kt = json.load(open(kt_path, encoding="utf-8"))
    # s0 正向 sha 对账（有 PDF 就跑真核——防 selftest 只测无 PDF 分支）
    if os.path.isfile(pdf_path):
        kt["_pdf_checked"] = load_keytable(kt_path, pdf_path)["_pdf_checked"]
        check("s0 键表头 sha ↔ PDF 实况 sha 正向一致", kt.get("_pdf_checked") is True,
              "未核成功但 PDF 在位")
    else:
        print("  ℹ️ s0 跳过：PDF 不在位（端用户装机态可只带键表）——正向核未执行，如实显形⚪")
    allq = [it["q"] for f in kt["scales"].values() for it in f["items"]]
    for v in kt["interstitial"].values():
        allq += [it["q"] for it in v]
    check("s1 键表 1-100 无缝无重（24+1 面）", sorted(allq) == list(range(1, 101))
          and len(kt["scales"]) == 24 and len(kt["interstitial"]) == 1, "n=%d" % len(allq))

    def fake(fn):
        allitems = [it for f2 in kt["scales"].values() for it in f2["items"]]
        allitems += [it for v in kt["interstitial"].values() for it in v]
        return {"form": "HEXACO-PI-R-100", "answers": {str(it["q"]): fn(it) for it in allitems}}

    import copy
    kt2 = copy.deepcopy(kt)
    # 真不变量（非恒真）：维度分聚合路径对账——facet 均分的均值 == 题级均分（等题数域）
    def _items_of(dom):
        return [it for f, f2 in kt["scales"].items() if f2["domain"] == dom for it in f2["items"]]
    r2 = compute(fake(lambda it: (it["q"] % 5) + 1), kt2, kt_path)
    agg_bad = []
    for dom in kt["domain_order"]:
        vals = []
        for it in _items_of(dom):
            raw = (it["q"] % 5) + 1
            vals.append(6 - raw if it["r"] else raw)
        item_mean = round(sum(vals) / len(vals), 2)
        if abs(item_mean - r2["dims"][dom]) > 0.011:
            agg_bad.append((dom, item_mean, r2["dims"][dom]))
    check("s2a 维度分聚合路径对账（题级均分≈facet均分均值·独立重算）", not agg_bad, str(agg_bad))
    r2b = compute(fake(lambda it: 3), kt2, kt_path)
    check("s2b 全答3 ⇒ 六维+25 面均=3.00（中点不变量·反向不改变 3）",
          all(v == 3.0 for v in r2b["dims"].values())
          and all(v == 3.0 for dom in r2b["facets"].values() for v in dom.values())
          and sum(len(d) for d in r2b["facets"].values()) == 25, str(r2b["dims"]))
    r3 = compute(fake(lambda it: 1 if it["r"] else 5), kt2, kt_path)
    check("s3 正=5/R=1 ⇒ 全 5.00（反向换算被真算）", all(v == 5.0 for dom in r3["facets"].values() for v in dom.values()), str(r3["dims"]))
    r4 = compute(fake(lambda it: 5 if it["r"] else 1), kt2, kt_path)
    check("s4 正=1/R=5 ⇒ 全 1.00（镜像）", all(v == 1.0 for dom in r4["facets"].values() for v in dom.values()), str(r4["dims"]))
    p5 = fake(lambda it: (it["q"] % 5) + 1)
    j1 = json.dumps(_strip_volatile(compute(json.loads(json.dumps(p5)), kt2, kt_path)), ensure_ascii=False, sort_keys=True)
    j2 = json.dumps(_strip_volatile(compute(json.loads(json.dumps(p5)), kt2, kt_path)), ensure_ascii=False, sort_keys=True)
    check("s5 同份输入双跑字节级一致（卡面验收①）", j1 == j2)
    p6 = json.loads(json.dumps(p5))
    p6["answers"].pop("7")
    try:
        buf = __import__("io").StringIO()
        _old = sys.stdout
        sys.stdout = buf
        try:
            compute(p6, kt2, kt_path)
        finally:
            sys.stdout = _old
        check("s6 缺 1 题 ⇒ 硬失败", False, "未报错")
    except SystemExit as e:
        check("s6 缺 1 题 ⇒ 硬失败（exit 2）", e.code == 2)
    # s7 变异：把某面一题的 r 翻转 ⇒ 全答5 时该面必偏离 3.00（5 非中点，R 翻转把 5↔1 才有效应；3 中点无效应——实测纠正）
    kt3 = copy.deepcopy(kt)
    fk = list(kt3["scales"])[0]
    kt3["scales"][fk]["items"][0]["r"] = not kt3["scales"][fk]["items"][0]["r"]
    r7 = compute(fake(lambda it: 5), kt3, kt_path)
    check("s7 变异单题 R 位 ⇒ 对应面偏离 3.00（键真在被算）",
          abs(r7["facets"][kt3["scales"][fk]["domain"]][fk] - 3.0) > 0.01, str(r7["facets"]))
    # s8 名集对账：aliases 套用后 = 生成器 25 名（含间质域）
    gn = generator_facet_names()
    if gn is None:
        print("  ℹ️ s8 跳过：生成器不在旁路（包内/装机态应命中·期望 %s）" % os.path.normpath(os.path.join(HERE, GEN_NAME)))
    else:
        mine = {d: set(v) for d, v in gn.items() if "Altruism" not in d}
        gen_al = set().union(*[v for k, v in gn.items() if "Altruism" in k]) if any("Altruism" in k for k in gn) else set()
        my_al = {f for d, v in r2b["facets"].items() if "Altruism" in d for f in v}
        pdf_mapped = {d: {(kt.get("aliases") or {}).get(k, k) for k in kt["scales"] if kt["scales"][k]["domain"] == d} for d in kt["domain_order"]}
        diffs = {d: sorted(pdf_mapped[d] ^ mine.get(d, set())) for d in kt["domain_order"] if pdf_mapped.get(d, set()) != mine.get(d)}
        check("s8 PDF 名经 aliases 套用=生成器 24 名逐域全等", not diffs, str(diffs))
        check("s8b 间质面对齐（Altruism）", gen_al == my_al == {"Altruism"}, "gen=%s mine=%s" % (gen_al, my_al))
    # s9 PDF sha 对账：改 PDF 副本 ⇒ load_keytable 必拒（负例·防把保护改成放行）
    import shutil
    import tempfile
    if os.path.isfile(pdf_path):
        tmpd = tempfile.mkdtemp()
        try:
            pc = os.path.join(tmpd, os.path.basename(pdf_path))
            shutil.copyfile(pdf_path, pc)
            with open(pc, "ab") as f:
                f.write(b"%")
            buf = __import__("io").StringIO()
            _old = sys.stdout
            sys.stdout = buf
            try:
                load_keytable(kt_path, pc)
                code = 0
            except SystemExit as e:
                code = e.code
            finally:
                sys.stdout = _old
            check("s9 PDF 被改 1 字节 ⇒ 拒算（sha 对账在岗·卡面验收③）", code == 2, "code=%s" % code)
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
    else:
        check("s9 跳过：PDF 不在同目录（端用户装机态仅键表可运行·如实显形）", True)
    return 0 if ok else 1


def _strip_volatile(res):
    d = dict(res)
    d.pop("answered_at", None)   # 时间戳来自输入，不算判据面
    return d


def main():
    ap = argparse.ArgumentParser(description="官方 HEXACO-100 自动计分器（确定性）")
    ap.add_argument("answers_json", nargs="?", help="官方答题页导出的 .json")
    ap.add_argument("--pdf", default=os.path.join(HERE, PDF_NAME))
    ap.add_argument("--keytable", default=os.path.join(HERE, KT_NAME))
    ap.add_argument("--build-keytable", action="store_true", help="从 PDF 构建/重建键表（需 pdftotext）")
    ap.add_argument("--verify-keytable", action="store_true", help="重抽 PDF 与键表逐格对账")
    ap.add_argument("--json", action="store_true", help="机器可读 JSON")
    ap.add_argument("--selftest", action="store_true", help="出厂判据（合成夹具）")
    a = ap.parse_args()
    if a.build_keytable:
        build_keytable(a.pdf, a.keytable)
        return 0
    if a.verify_keytable:
        return verify_keytable(a.pdf, a.keytable)
    if a.selftest:
        if not os.path.isfile(a.keytable):
            die("selftest 前键表必须先存在（判据不许造数据）。", "跑 --build-keytable。")
        print("selftest（键表=%s）" % a.keytable)
        return selftest(a.keytable, a.pdf)
    if not a.answers_json:
        die("没给答卷文件。", "用法：python3 hexaco_official_scorer.py <官方答卷.json>；判据完好先跑 --selftest。")
    if not os.path.isfile(a.answers_json):
        die("答卷文件不存在：%s" % a.answers_json, "用答题页下载按钮的整份文件。")
    try:
        payload = json.load(open(a.answers_json, encoding="utf-8"))
    except ValueError as e:
        die("答卷 JSON 解析失败：%s" % e, "多半复制时截断——用下载的整份 .json。")
    if payload.get("form") not in (None, "HEXACO-PI-R-100"):
        die("答卷 form=%r 不是官方 100 卷（form 应为 HEXACO-PI-R-100）。" % payload.get("form"),
            "自建卷走 hexaco_selfbuild_scorer.py——两把尺子各量各的卷，⛔混用。")
    kt = load_keytable(a.keytable, a.pdf)
    res = compute(payload, kt, a.keytable)
    if a.json:
        print(json.dumps(_strip_volatile(res), ensure_ascii=False, indent=1, sort_keys=True))
    else:
        print(render_human(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
