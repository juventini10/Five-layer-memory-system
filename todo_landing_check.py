#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""todo_landing_check.py — 包内「自陈待办 → 必须有实物」通用闸（C32·2026-10-15 立卡）

## 为什么存在（不是洁癖，是复发条件）
包里 md 会写「过闸后：写入 `X.py`（自动计分）→ 随包」这类**自陈待办**。这类语句有两个性质：
  ①它是给未来读者（AI/人）的**承诺**——读者会据此认为"有这个件"；
  ②它没有任何机械判据核该件是否存在 ⇒ 承诺可以长期挂着，甚至可以"声称已完成"而盘上无物。
实证两例：`自建100题-分身版-题库-v1.md` §八 第4条从 09-13 挂到 10-15（C27）；
`step3/step5` 类"已生成"叙述与盘上实况不符（C16）。两道卡都是**人肉发现**的，门禁全程不红。
本闸把这一族变成机械判据：凡 md 自陈"要写入某文件"，该文件必须在包内**在位**，否则发版前显形。

## 判据（机械可定·⛔不做语义理解）
  收集：同一行内 `待办语汇` 与 `文件名(.py/.sh/.json/.js/.html)` 共现
        待办语汇 = 待办|TODO|过闸后|待写入|应写入|需写入|要写入|计划|下一步|未来|尚未|未落地|待建…
  在位：该文件 basename 在包内任意路径存在（一次 walk 建索引）⇒ 在位。
        ⚠️ 与卡面原设计「四路解析（md 所在目录∪包根∪references∪references/scripts）」相比取了**更宽**口径：
        整包即发货面，"随包"的语义＝在包里，不锁死目录；锁死目录会把"换了个位置放"误判成"没做"（假红），
        而假红逼出来的动作是**改文案绕闸**——比漏报更坏。窄口径留待 C20/D9 的落点清单去管（那是另一判据）。
  豁免：`todo-landing-whitelist.json` 逐条登记（登记处唯一），每条须带
        ①被登记语句的内容指纹（sha8·语句被改写⇒登记自动失效，防"改文案骗过闸"）
        ②target（该待办指向的件）③reason（为什么合法：运行时产物/作者侧件/他端承接件…）
        ⛔ 不把正则改窄来凑绿——收窄判据=把真坑埋回盲区（先例：personal-path-whitelist 合账史）

## 扫描面=承诺面，⛔不含记录面（v1.1·2026-10-15 实测数据后所定·有判据不是图省事）
`--report` 全量干跑实测：真「无实物」共 4 类名（settings.json／step0_gate.py／
job_probation_ledger.json／reply_format_guard.py），**全部落在 CHANGELOG.md 与 golden_samples 副本里，
且逐条读原文后确认没有一条是对包内件的前景承诺**：
  - `reply_format_guard.py`：system-logger CHANGELOG:129「⛔ 方案B不采纳·永久禁止……此处留痕以防再次误复活」
    ——它**本就该永久不在包里**；若把这条塞进豁免清单，等于给一份「故意不回改」的账本挂 fp 指纹，
    日后任何人在这行补一个字→登记失效→假红，而唯一"修法"是改写这条留痕本身＝伪造取证。
  - `step0_gate.py`：triwich CHANGELOG:845，指作者机 `~/WorkBuddy/数据记录/smoke-20260809/` 的冒烟实证（过去时）。
  - `job_probation_ledger.json`：good-good-study CHANGELOG:122「同轮数字分身侧……两条 actor 修正」（过去时·作者侧账）。
  - `settings.json`：triwich CHANGELOG:969 叙述 WorkBuddy 平台自己的钩子注册文件（他端运行态件）。
结论：**记录面（账本／冻结样本／单测夹具）装的是"已经发生什么"，承诺面装的是"将要有什么"**。
本闸只对后者执法——因为病（"声称完成而盘上无物"）的成立条件是"读者据以形成期待"，
而 CHANGELOG 的文体（过去时＋不回改）恰恰不产生这种期待。跳过项**逐条计数并打印**（⛔静默吞）。
判据形态：路径角色常量表（`RECORD_SURFACES`），按文件名/目录名机械匹配，⛔不按日期、⛔不按"看起来像历史"。
先例同族：clock-loop CHANGELOG:355 自己写着「登记入 known-limitations」——前景待办的合法家是待办面，
账本里那句只是它的记账副本；跳过副本而扫正本＝去重，不是漏检。

## 文件名抽取三处实测缺陷（v1.1 修·⛔不是把判据改窄）
  缺陷①（扩展名序）：`js` 排在 `json` 前 ⇒ `settings.json` 被切成 `settings.js`，假红 6 条。
    修法＝按点号定位、扩展名**长名优先**＋要求扩展名后不再是字母数字。
  缺陷②（中文黏连）：首字符类含 `一-龥` ⇒「由distillation_scheduler.py」整串被当文件名，假红 5 条。
    修法＝保留中文文件名能力（包里确有 `童灵·人格向量.json`／`自建100题-分身版-题库-v1.md` 这类真件名），
    抽取后按「中文→ASCII 边界」生成候选（整串＋尾段），**任一候选在位即算在位并打 ↳尾段解析 标记**；
    两候选都不在位 ⇒ 仍报红（用尾段名点名）。⇒ 该消歧只改**名字解析**，不改**判定强度**：
    缺件不会因为前面黏了中文而被说成有件（自检 T5 专测这一条）。
  缺陷③（`+` 黏连）：字符类含 `+` ⇒「v2.5.0断言台账管道+load_claim_index.py」整串成名，假红 1 条
    ——而 `load_claim_index.py` 实测**在包内存在**（references/skills/clock-loop/scripts/）。
    修法＝字符类去掉 `+`；先去取证：实测包内 **0 个**文件名含 `+`（含 `·` 的有 2 个，故 `·` 保留）。

## 扩展名集合＝{py, sh, json, js, html}，⛔不含 `.md`（v1.1 探针实测后所定·不收窄也不虚扩）
把 `md` 加进 EXTS 实测：承诺面语句 22→90 条、红 0→**31 条**，逐条读原文后 31 条**全是叙述或引用**
（`step6.5-done.md`＝装机产物名、`CORE.md`＝L1 层文件、`归档-详解版退役段-v8.14.md`＝历史归档、
`YYYY-MM-月总结.md`＝未来日期模板占位、`_errors.md`／`ERRORS.md`＝成长箱数据文件……）。
⇒ 病（"自陈待办零实物"）的实物侧＝可执行/配置件（py/sh/json/js/html），C27 真句形正落在 `.py` 侧；
`.md` 在包内同时充当"文档/产物/模板占位"三种语义，纳入即淹进 31 条假红，执法价值归零。

## 用法
  python3 todo_landing_check.py --report            # 干跑：只列命中与在位实况（⛔不改判，先看清命中范围·铁律-020）
  python3 todo_landing_check.py                     # 执法：未登记且不在位 ⇒ 红（exit 1）
  python3 todo_landing_check.py --quiet                # 一行结论＋红清单（verify.sh §3.1d 接线用）
  python3 todo_landing_check.py --selftest              # 变异自检 12 条：假待办必红／建空壳必绿／空壳回落／登记生命周期／两处变异自证
  可选 --pkg-root <路径>（默认=本脚本所在目录）

## 退出码
  0 = 全部待办有实物（或已带理由登记）
  1 = 存在无实物且未登记的待办，或存在被改写的豁免登记
  2 = 用法/路径/豁免清单解析错误（fail-closed，⛔不返回"看起来没问题"）

version: v1.1（2026-10-15·C32 收口轮：扫描面二分＋文件名抽取三处实测缺陷修＋12 条自检含 2 处变异自证；v1.0=同日初版）
"""
import argparse
import hashlib
import json
import os
import re
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）

import tempfile

TODO_VOCAB = ("待办", "TODO", "过闸后", "待写入", "待补写", "应写入", "需写入", "要写入",
              "计划", "下一步", "未来", "尚未", "未落地", "待建", "后续补", "应随包", "待补",
              "应补", "应增", "应加", "还没", "尚未随包")
EXTS = ("json", "html", "py", "sh", "js")            # 长名优先（缺陷①）
NAME_CH = re.compile(r"[0-9A-Za-z_./\-一-鿿·]")   # ⛔不含 `+`：实测包内 0 个文件名带加号，
#   而 prose「…管道+load_claim_index.py」里的 `+` 会把中文前缀黏进文件名⇒假红（v1.1 第二处实测缺陷）
CJK = re.compile(r"[一-鿿]")
SCAN_EXT = (".md",)
SKIP_DIR = ("__pycache__", ".git", "记忆琥珀")
# 记录面＝账本／冻结样本／单测夹具（判据理由见 docstring「扫描面=承诺面」段）
RECORD_SURFACES = ("CHANGELOG.md", "/golden_samples/", "/scripts/fixtures/", "/记忆琥珀/")
WHITELIST = "todo-landing-whitelist.json"


def sha8(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:8]


def is_record_surface(rel):
    """rel=包内相对路径（posix 形态）。记录面⇒不参与执法，但计入"已跳过"读数。"""
    return any(m in "/" + rel for m in RECORD_SURFACES)


def extract_names(line):
    """抽出一行里的文件名串（含中文真件名）。按点号定位，扩展名后须非字母数字。"""
    out = []
    for m in re.finditer(r"\.(" + "|".join(EXTS) + r")(?![0-9A-Za-z_])", line):
        head = line[:m.start()]
        k = len(head)
        while k > 0 and NAME_CH.match(head[k - 1]):
            k -= 1
        stem = head[k:]
        seg = stem.split("/")[-1]
        if not seg.strip(".") or set(seg) <= {"."}:   # "`.ps1/.sh/.md`" 里的裸 .sh＝无名
            continue
        out.append(stem + m.group(0))
    return out


def name_candidates(run):
    """整串优先；再给「中文→ASCII 边界」尾段候选（缺陷②·只改名不改判）。"""
    cands = [run]
    parts = re.split(r"(?<=[一-鿿])(?=[0-9A-Za-z_])", run)
    if len(parts) > 1:
        cands.append(parts[-1])
    seen, res = set(), []
    for c in cands:
        b = os.path.basename(c)
        if b and b not in seen:
            seen.add(b)
            res.append((c, b))
    return res


def index_package(pkg_root):
    """一次遍历：返回 (md 文件清单, basename→路径集合)。"""
    mds, bases = [], {}
    for root, dirs, files in os.walk(pkg_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR and not d.endswith(".bak")]
        for f in files:
            p = os.path.join(root, f)
            bases.setdefault(f, []).append(p)
            if f.endswith(SCAN_EXT):
                mds.append(p)
    return mds, bases


def scan(mds, pkg_root):
    """收集承诺面的自陈待办：返回 (hits, 跳过语句数, 跳过文件数)。"""
    hits, skip_lines, skip_files = [], 0, 0
    for p in mds:
        rel = os.path.relpath(p, pkg_root).replace(os.sep, "/")
        if is_record_surface(rel):
            skip_files += 1
            try:
                skip_lines += sum(1 for l in open(p, encoding="utf-8", errors="replace")
                                  if any(v in l for v in TODO_VOCAB))
            except OSError:
                pass
            continue
        try:
            lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if not any(v in line for v in TODO_VOCAB):
                continue
            for run in extract_names(line):
                cands = name_candidates(run)
                if WHITELIST in run:
                    continue
                hit = {"where": "%s:%d" % (rel, n),
                       "stmt": line.strip()[:200],
                       "fp": sha8(line.strip()),
                       "run": run}
                hit["resolved"] = [b for _, b in cands]
                hits.append(hit)
    return hits, skip_lines, skip_files


def resolve(h, bases):
    """任一候选名在位 ⇒ (True, 该名, 是否走了尾段消歧)。"""
    for i, (_raw, b) in enumerate(name_candidates(h["run"])):
        if b in bases:
            return True, b, i > 0
    return False, name_candidates(h["run"])[-1][1], False


def load_whitelist(pkg_root):
    path = os.path.join(pkg_root, WHITELIST)
    if not os.path.isfile(path):
        return {}, path
    try:
        data = json.load(open(path, encoding="utf-8"))
    except ValueError as e:
        die("豁免清单解析失败：%s（%s）" % (e, path),
            "该清单是唯一登记处；损坏时本判据失明＝红，⛔ 不按「读不到就算过」处理。")
    idx = {}
    for it in data.get("items", []):
        if not it.get("reason"):
            die("豁免条目缺 reason：%r（%s）" % (it, path),
                "每条登记必须写清为什么合法（运行时产物／作者侧件／他端承接件）——无理由的豁免＝无人能审的空子。")
        idx[(it.get("where"), it.get("fp"))] = it
    return idx, path


def die(msg, remedy, code=2):
    print("❌ " + msg)
    print("   怎么办：" + remedy)
    sys.exit(code)


def evaluate(hits, bases, wl):
    """分类：在位／已合法登记／登记但语句已被改写（失效）／未登记且不在位（红）"""
    ok, reg, stale, bad = [], [], [], []
    for h in hits:
        exists, target, via_tail = resolve(h, bases)
        h["target"] = target
        h["via_tail"] = via_tail
        if exists:
            ok.append(h)
            continue
        if (h["where"], h["fp"]) in wl:
            reg.append(h)
            continue
        if any(k[0] == h["where"] for k in wl):
            stale.append(h)          # 登记过这句话，但话被改了 ⇒ 登记自动失效，需重登
        else:
            bad.append(h)
    return ok, reg, stale, bad


def _build_case(d):
    """真跑真写的夹具（QCN-20261015-003：⛔自测恒真／⛔转写不照形状）。"""
    os.makedirs(os.path.join(d, "references"), exist_ok=True)
    os.makedirs(os.path.join(d, "references", "skills", "x", "golden_samples", "GS-1"), exist_ok=True)
    open(os.path.join(d, "verify.sh"), "w", encoding="utf-8").write("#!/bin/sh\n")
    open(os.path.join(d, "present_tool.py"), "w", encoding="utf-8").write("# 真件\n")
    open(os.path.join(d, "童灵·人格向量.json"), "w", encoding="utf-8").write("{}\n")
    open(os.path.join(d, "INSTALL.md"), "w", encoding="utf-8").write(
        "# 安装\n\n过闸后：写入 `brand_new_tool.py`（自动计分）→ 随包\n"
        "计划：`present_tool.py` 已在位即可用\n")
    # 真 C27 句形（题库 §八 第4条原文形状·照抄形状不转写）
    open(os.path.join(d, "自建100题-分身版-题库-v1.md"), "w", encoding="utf-8").write(
        "## 八、待办\n\n4. 过闸后：写入 `hexaco_selfbuild_scorer.py`（自动计分）→ 随包\n")
    # 中文黏连两例（⛔不加反引号，反引号会让首字符不黏连、测不到缺陷②）：
    #   尾段在位（须算在位）／尾段也不在位（须仍报红）
    open(os.path.join(d, "notes.md"), "w", encoding="utf-8").write(
        "请先运行安装包present_tool.py，后续补 由ghost_missing.py 的调用\n")
    # 记录面：同一句假待办写进 CHANGELOG 与 golden_samples 副本（须被跳过且计数显形）
    open(os.path.join(d, "references", "CHANGELOG.md"), "w", encoding="utf-8").write(
        "- **v9** (2026-08-01)：待办：写入 `brand_new_tool.py`（当年叙述）\n")
    open(os.path.join(d, "references", "skills", "x", "golden_samples", "GS-1", "T.md"),
         "w", encoding="utf-8").write("待办：写入 `gs_only_in_sample.py`\n")


def _try_load(pkg_root):
    """调 load_whitelist 并把 die() 的 exit code 收回来自测（⛔让 die 的打印漏进自检输出——C27 轮 F9 教训）。"""
    import contextlib
    import io
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            load_whitelist(pkg_root)
    except SystemExit as e:
        return int(e.code if e.code is not None else 2), buf.getvalue()
    return 0, buf.getvalue()


def selftest(pkg_root):
    """出厂负例＋变异（#S138／gate-false-green 三态：判据缺一半的闸不算闸）。"""
    d = tempfile.mkdtemp(prefix="todoland-")
    _build_case(d)
    results = []

    def run():
        mds, bases = index_package(d)
        hits, sk_lines, sk_files = scan(mds, d)
        wl, _ = load_whitelist(d)
        return evaluate(hits, bases, wl), sk_lines, sk_files, hits, mds, wl

    (ok, reg, stale, bad), sk_lines, sk_files, hits, mds, wl = run()
    results.append(("T1 假待办（brand_new_tool.py 不在位）⇒ 必须报红",
                    any(b["target"] == "brand_new_tool.py" for b in bad)))
    results.append(("T2 包内真件（present_tool.py）⇒ 不误报（夹具内真建该件）",
                    any(h["target"] == "present_tool.py" for h in ok) and
                    not any(h["target"] == "present_tool.py" for h in bad)))
    results.append(("T3 真 C27 句形（题库 §八 写入 scorer）⇒ 必须报红",
                    any(b["target"] == "hexaco_selfbuild_scorer.py" for b in bad)))
    # T4 建空壳 ⇒ 转绿（同一判据、无豁免）
    open(os.path.join(d, "hexaco_selfbuild_scorer.py"), "w", encoding="utf-8").write("# 空壳\n")
    (ok2, _, _, bad2), _s2, _f2, _h2, _m2, _w2 = run()
    results.append(("T4 建空壳后 ⇒ 必须转绿（同一判据、无豁免）",
                    not any(b["target"] == "hexaco_selfbuild_scorer.py" for b in bad2)))
    # T5 中文黏连：尾段在位⇒算在位；尾段也不在位⇒仍报红
    results.append(("T5 中文黏连「由ghost_missing.py」⇒ 仍报红（消歧只改名不改判）",
                    any(b["target"] == "ghost_missing.py" for b in bad)))
    results.append(("T6 中文黏连「安装包present_tool.py」⇒ 尾段解析为在位（不误报）",
                    any(h["target"] == "present_tool.py" and h["via_tail"] for h in ok)))
    # T7 记录面：golden_samples 副本里的假待办必须被跳过（同句在承诺面则红——见 T1）
    results.append(("T7 记录面（CHANGELOG／golden_samples）⇒ 跳过且读数显形（件数与行数都>0）",
                    sk_files >= 2 and sk_lines >= 2 and
                    not any(b["target"] == "gs_only_in_sample.py" for b in bad)))
    # T7b 变异：把记录面判据短路成"什么都不跳" ⇒ golden_samples 那条假待办必须显形
    orig_rec = globals()["is_record_surface"]
    globals()["is_record_surface"] = lambda rel: False
    (_okx, _rx, _sx, badx), _sxy, _fxy, _hx, _mx, _wx = run()
    globals()["is_record_surface"] = orig_rec
    results.append(("T7b 变异（记录面短路）⇒ gs_only_in_sample.py 必转红（证跳过确由该判据产生）",
                    any(b["target"] == "gs_only_in_sample.py" for b in badx)))
    # T8 中文真件名仍可被引用（缺陷②修法的能力保底）
    open(os.path.join(d, "INSTALL.md"), "a", encoding="utf-8").write(
        "\n待办：应随包写入 `童灵·人格向量.json`（用户机生成）\n")
    (ok3, _, _, bad3), _s3, _f3, _h3, _m3, _w3 = run()
    results.append(("T8 中文名件（童灵·人格向量.json）⇒ 能识别（不静默丢能力）",
                    any(h["target"] == "童灵·人格向量.json" for h in ok3)))
    # T9 变异：短路名字抽取 ⇒ 一切红必消失（证明各断言真在被算而非恒真）
    orig = globals()["extract_names"]
    globals()["extract_names"] = lambda line: []
    (_ok4, _r4, _s4, bad4), _s5, _f5, _h5, _m5, _w5 = run()
    globals()["extract_names"] = orig
    results.append(("T9 变异（名字抽取短路）⇒ 红集必为空（否则断言恒真）",
                    bad4 == [] and len(bad) > 0))
    # T10 豁免生命周期：带 reason 登记 ⇒ 红转豁免；同句改写 ⇒ 登记自动失效并显形（⛔静默放行）
    inst = os.path.join(d, "INSTALL.md")
    txt = open(inst, encoding="utf-8").read()
    target_line = [l for l in txt.split("\n") if "brand_new_tool.py" in l][0]
    where = next(b["where"] for b in bad if b["target"] == "brand_new_tool.py")
    json.dump({"items": [{"where": where, "fp": sha8(target_line.strip()),
                          "target": "brand_new_tool.py", "reason": "运行时产物（用户机生成）"}]},
              open(os.path.join(d, WHITELIST), "w", encoding="utf-8"), ensure_ascii=False)
    (_ok5, reg5, _st5, bad5), _s6, _f6, _h6, _m6, _w6 = run()
    results.append(("T10 登记后 ⇒ 该条从红转豁免（且仍在报告里可见）",
                    any(r["target"] == "brand_new_tool.py" for r in reg5) and
                    not any(b["target"] == "brand_new_tool.py" for b in bad5)))
    open(inst, "w", encoding="utf-8").write(txt.replace(
        "过闸后：写入 `brand_new_tool.py`（自动计分）→ 随包",
        "过闸后：写入 `brand_new_tool.py`（说法换了）→ 随包"))
    (_ok6, _r6, stale6, bad6), _s7, _f7, _h7, _m7, _w7 = run()
    results.append(("T11 改写语句后 ⇒ 登记自动失效并显形（⛔静默放行）",
                    any(s["target"] == "brand_new_tool.py" for s in stale6) or
                    any(b["target"] == "brand_new_tool.py" for b in bad6)))
    # T12 无理由登记 ⇒ fail-closed（exit 2·不按"读不到就算过"）
    json.dump({"items": [{"where": "INSTALL.md:3", "fp": "deadbeef",
                          "target": "brand_new_tool.py"}]},
              open(os.path.join(d, WHITELIST), "w", encoding="utf-8"), ensure_ascii=False)
    rc2, _out2 = _try_load(d)
    results.append(("T12 豁免条目缺 reason ⇒ 硬失败 rc=2（登记处不许留空子·⛔读不到就算过）", rc2 == 2))
    allok = True
    for name, cond in results:
        print("  %s %s" % ("✅" if cond else "❌", name))
        allok = allok and cond
    print("  自检 %d/%d" % (sum(1 for _, c in results if c), len(results)))
    return 0 if allok else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="包内自陈待办的在位对账（C32）")
    ap.add_argument("--pkg-root", default=here)
    ap.add_argument("--report", action="store_true",
                    help="干跑：只列命中，不改判（铁律-020 要求先看命中范围）")
    ap.add_argument("--selftest", action="store_true", help="变异自检（10 条）")
    ap.add_argument("--quiet", action="store_true",
                    help="只出一行结论（verify.sh §3.1d 接线用·逐条明细省略）")
    a = ap.parse_args()
    pkg = os.path.abspath(os.path.expanduser(a.pkg_root))
    if not os.path.isdir(pkg):
        die("包根不存在：%s" % pkg, "确认路径（默认=本脚本所在目录）。")
    if a.selftest:
        sys.exit(selftest(pkg))
    mds, bases = index_package(pkg)
    hits, sk_lines, sk_files = scan(mds, pkg)
    wl, wl_path = load_whitelist(pkg)
    ok, reg, stale, bad = evaluate(hits, bases, wl)
    if a.report:
        print("干跑（--report·不改判）：md %d 件（执法面 %d／记录面跳过 %d 件·其内待办语汇行 %d 行）"
              % (len(mds), len(mds) - sk_files, sk_files, sk_lines))
        print("                    自陈待办语句 %d 条" % len(hits))
        for h in ok:
            tail = "  ↳尾段解析:%s" % h["run"] if h.get("via_tail") else ""
            print("  ✅ 在位  %-32s ← %s%s" % (h["target"], h["where"], tail))
        for h in reg:
            print("  📋 登记  %-32s ← %s" % (h["target"], h["where"]))
        for h in stale:
            print("  🔁 失效  %-32s ← %s（语句已改写，登记需重做）" % (h["target"], h["where"]))
        for h in bad:
            print("  ❌ 无实物 %-30s ← %s" % (h["target"], h["where"]))
            print("        语句：%s" % h["stmt"])
        print("小结：在位 %d ／已登记 %d ／登记失效 %d ／无实物 %d ／记录面跳过 %d 件"
              % (len(ok), len(reg), len(stale), len(bad), sk_files))
        sys.exit(0)
    print("自陈待办在位对账：承诺面语句 %d 条·在位 %d·合法登记 %d·记录面跳过 %d 件（判据见本文件 docstring）"
          % (len(hits), len(ok), len(reg), sk_files))
    if not stale and not bad:
        print("✅ 全部待办有实物（或已带理由登记）")
        sys.exit(0)
    for h in bad:
        if a.quiet:
            print("  ❌ 待办无实物：%s ← %s" % (h["target"], h["where"]))
        else:
            print("  ❌ 待办无实物：%s ← %s\n        语句：%s" % (h["target"], h["where"], h["stmt"]))
    for h in stale:
        print("  🔁 豁免登记失效（语句被改写）：%s ← %s" % (h["target"], h["where"]))
    print("   怎么办：①真要做就把该件建出来；②本就不该在包里（运行时产物/作者侧件）→"
          "写进 %s 带 reason 登记；⛔ 不要把正则改窄来凑绿。" % os.path.basename(wl_path))
    sys.exit(1)


if __name__ == "__main__":
    main()
