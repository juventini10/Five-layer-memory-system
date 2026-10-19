#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_box_schema_check.py — 成长箱归档 Schema 机械断言（守卫类·按需部署）

v2.0.0（2026-10-11 · growth-box v4.5.0 显示层改造 步4②）
  新增【反哺日志模式】：读 `规范反哺日志.md` 条目里的 `🧪 门禁痕` 结构化字段并逐段机械校验。
  立项理由（尺A/尺B 双尺，见 SKILL.md「呈现层三块式骨架」节）：E3.5/C3.5 四锁表此前
  **零脚本消费者**（实测引用数 0，而手抄落盘 173/140/199 次）——零消费者的手画格式每轮必漂。
  本模式把该格式的消费数从 0 抬到 ≥1：格式有人保证，漂了会红。
  ⛔不新建独立守卫文件（卡A 收口纪律「不为本改造新建阻断守卫」）——扩既有闸门，一闸门两语料。

职责:
  A. 错误归档模式（v1.x 原有）：校验 learnings 错误条目必填字段齐全 + 枚举合法 + 联动合法。
  B. 反哺日志模式（v2.0.0 新增）：按 `### ` 切条目，对【生效日及之后】的条目硬校验 🧪 门禁痕
     六段语法；【生效日之前】的条目按存量祖父化跳过（只计数不判红，同 v1.1 P2-13 裁决口径）。

用法:
  python3 growth_box_schema_check.py <归档或反哺日志文件路径>
  python3 growth_box_schema_check.py <反哺日志路径> --feedback   # 强制走反哺模式（文件名不符时显式指定）
  python3 growth_box_schema_check.py --self-test      # 夹具自测（正/负/变异三段）
  exit 语义：0=过 · 2=缺字段/缺痕 · 3=取值/联动非法 · 4=表↔详情🔴配对失配（v2.2.0·逐条点名）

退出码（两模式共用）:
  0 = 通过  |  1 = 文件不存在/不可读/无语料
  2 = 必填字段缺失（缺门禁痕=缺字段）  |  3 = 取值非法/段数不符/联动非法

🧪 门禁痕 固定语法（一行·六段·段间用全角｜）:
  门禁=E3.5｜锚[成立:{≥1项;…};失效:{≥1项;…}]｜8要素[1✅2✅…8❌]｜自爆[未触发|复检补N项|复检仍全✅→❌]｜结论[✅可反哺|🟡需修正|❌不可反哺]｜签名[✅|❌]
联动判据（机械可表达的门禁语义）:
  J1 门禁 ∈ {E3.5, C3.5}
  J2 锚两列均非空（只填一列=没有边界=过度泛化，对齐锁1 原句）
  J3 8要素恰好 8 格，序号 1..8 连续，取值 ∈ {✅,❌}（定值法：少一行=阻断）
  J4 全✅ 时 自爆 ≠ 未触发（8项全绿却未触发自爆=评估不完整=误归纳风险，对齐锁2 自爆机制）
  J5 结论三态枚举合法
  J6 结论↔签名联动：✅可反哺→签名✅；❌不可反哺→签名❌；🟡需修正=退回中不得落盘
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, io

REQUIRED_BOLD_FIELDS = ["Logged", "Priority", "Status", "Area", "来源 AI", "认知象限"]
REQUIRED_SECTIONS = ["Summary", "Details", "Root Cause", "Rule", "Why", "How to apply"]
ENUMS = {
    "Priority": ("high", "medium", "low", "critical"),
    "Status": ("pending", "resolved", "promoted"),
    "Area": ("流程", "验证", "身份认知", "技术实现", "其他"),
    "认知象限": ("已知未知", "已知已知"),
}

# ── 反哺日志模式常量（判据本体，⛔不在函数里硬写魔数）──
FEEDBACK_BASENAME = "规范反哺日志.md"
TRACE_FIELD = "🧪 门禁痕"
TRACE_CUTOFF = "2026-10-12"          # v4.5.0 生效日：此日前条目=存量祖父化
LOCK2_SLOTS = 8                       # 定值法：锁2 固定 8 格
GATE_ENUM = ("E3.5", "C3.5")
CONCLUSION_ENUM = ("✅可反哺", "🟡需修正", "❌不可反哺")
DATE_RE = re.compile(r"^- 📅 日期[：:]\s*(\d{4}-\d{2}-\d{2})", re.M)


EXPECT_RECORDS = 0      # 由 main() 依 --expect-records 覆写；0=只显形不判红（v2.3.0b）
STRICT_FROM = "2026-10-13"        # v2.3.0 逐条断言生效日：此日后 Logged 的记录逐条查；此前存量祖父化但计数显形


def _has_field(text, name):
    """v2.3.0 方言兼容：`**K**:`／`- **K**:`／`- K:` 三种写法均视为该字段在位。
    根因：learnings 归档有两种载体方言（通用 LEARNINGS.md 用行首粗体，`*_errors.md` 用 `- K: v` 内联），
    旧实现只认前者 ⇒ 后者整族 41 条从未被断言却共享 rc=0（QCN-20261013-005 实测：单条喂报缺 11-12 项、整档 rc=0）。"""
    return bool(re.search(r"^(?:- )?(?:\*\*)?" + re.escape(name) + r"(?:\*\*)?\s*[：:]", text, re.M))


def _has_section(text, name):
    """小节同样兼容：独立节头 `### Summary`／内联 `- Summary:`／`- **Summary**:`。"""
    return bool(re.search(r"^(?:- )?(?:\*\*)?" + re.escape(name) + r"(?:\*\*)?\s*[：:]|^###\s+" + re.escape(name) + r"\s*$", text, re.M))


def _get_field(text, name):
    m = re.search(r"^(?:- )?(?:\*\*)?" + re.escape(name) + r"(?:\*\*)?\s*[：:]\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def _field(block, name):
    """取条目块内 `- <name>：value` 行的 value（全角/半角冒号均可）。"""
    m = re.search(rf"^- {re.escape(name)}[：:]\s*(.+)$", block, re.M)
    return m.group(1).strip() if m else None


def parse_trace(val):
    """🧪 门禁痕 一行 → 六段 dict；语法不符返回 (None, 原因)。"""
    segs = [s.strip() for s in val.split("｜")]
    need = ["门禁=", "锚[", "8要素[", "自爆[", "结论[", "签名["]
    got = {}
    for s in segs:
        for k in need:
            if s.startswith(k):
                got[k] = s[len(k):]
                break
    miss = [k for k in need if k not in got]
    if miss:
        return None, f"缺段 {','.join(miss)}（六段齐全才可解析）"
    gate = got["门禁="].strip()
    anchor = got["锚["].rstrip("]")
    locks = got["8要素["].rstrip("]")
    boom = got["自爆["].rstrip("]")
    concl = got["结论["].rstrip("]")
    sign = got["签名["].rstrip("]")
    return {"gate": gate, "anchor": anchor, "locks": locks,
            "boom": boom, "concl": concl, "sign": sign}, None


def validate_trace(v, label):
    """六段痕 → 违规原因列表（消费者共用：反哺日志模式 v2.0 ＋ 蒸馏报告模式 v2.1）。
    判据本体不变：段齐/门禁枚举/锚两列非空/8格定值连续/全绿必触自爆/结论枚举/结论↔签名联动。"""
    parsed, err = parse_trace(v)
    if err:
        return ["%s：%s" % (label, err)]
    p = parsed
    bad = []
    if p["gate"] not in GATE_ENUM:
        bad.append("%s：门禁=%s（应 ∈ %s）" % (label, p["gate"], "/".join(GATE_ENUM)))
    parts = [x.strip() for x in re.split(r"[;；]", p["anchor"])]
    col = {}
    for x in parts:
        for nm in ("成立", "失效"):
            if x.startswith(nm + ":") or x.startswith(nm + "："):
                col[nm] = re.split(r"[:：]", x, 1)[1]
    if "成立" not in col or "失效" not in col:
        bad.append("%s：锚缺 成立:/失效: 子段（语法=锚[成立:…;失效:…]）" % label)
    else:
        for nm in ("成立", "失效"):
            if not any(y.strip() for y in re.split(r"[,，;；]", col[nm])):
                bad.append("%s：锚 %s 列为空（只填一列=没有边界）" % (label, nm))
    slots = re.findall(r"(\d)([✅❌])", p["locks"])
    if len(slots) != LOCK2_SLOTS:
        bad.append("%s：8要素解析到 %d 格（定值法应恰 %d 格）" % (label, len(slots), LOCK2_SLOTS))
    else:
        seq = [int(s[0]) for s in slots]
        if seq != list(range(1, LOCK2_SLOTS + 1)):
            bad.append("%s：8要素序号不连续 %s" % (label, seq))
            all_green = False
        else:
            all_green = all(s[1] == "✅" for s in slots)
        if all_green and p["boom"].startswith("未触发"):
            bad.append("%s：8格全✅ 但 自爆=未触发（全绿=评估不完整，须先触发自爆）" % label)
    if p["concl"] not in CONCLUSION_ENUM:
        bad.append("%s：结论=%s（应 ∈ %s）" % (label, p["concl"], "/".join(CONCLUSION_ENUM)))
    elif p["concl"] == "🟡需修正":
        bad.append("%s：结论=🟡需修正 已落盘（🟡=退回修正中，不得作为终态条目入库）" % label)
    elif p["concl"] == "✅可反哺" and p["sign"] != "✅":
        bad.append("%s：结论✅可反哺 但 签名=%s（联动断裂）" % (label, p["sign"]))
    elif p["concl"] == "❌不可反哺" and p["sign"] != "❌":
        bad.append("%s：结论❌不可反哺 但 签名=%s（❌终态不该存在）" % (label, p["sign"]))
    return bad


def check_distill_report(text, path):
    """蒸馏报告模式（v2.1 新增·C3.5 痕的脚本消费者）：只认显式 --distill，⛔ 不按文件名猜。"""
    m = re.search(r"^#{2,4}[^\n]*步骤④：决策表[^\n]*\n.*?(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        print("❌ 未找到「步骤④：决策表」段（该文件不是蒸馏报告？显式 --distill 已指定）: %s" % path)
        return 1
    rows = [l for l in m.group(0).splitlines() if l.strip().startswith("|")]
    header = next((r for r in rows if TRACE_FIELD in r), None)
    if not header:
        print("❌ 蒸馏报告决策表缺「%s」列 → C3.5 痕无处落盘（exit 2）: %s" % (TRACE_FIELD, path))
        return 2
    idx = [i for i, c in enumerate(header.split("|")) if TRACE_FIELD in c][0]
    rows = rows[rows.index(header) + 1:]      # 表头及之前不算数据行（否则表头自身被判缺痕）
    data = []
    for r in rows:
        body = r.replace("|", "").replace(" ", "")
        if body and set(body) <= set("-:"):
            continue                      # 分隔行
        if r.split("|")[1].strip() == "[编号]":
            continue                      # 模板占位行（v2.2.2 判据精确化：只认首格＝真模板行；原"整行含 [编号]"会把正文出现该字样的真实缺痕行判成模板态＝假绿后门）
        data.append(r)
    if not data:
        print("✅ 蒸馏报告决策表为模板态（无真实决策行）·跳过不判红 — %s" % path)
        return 0
    missing, illegal = [], []
    for i, r in enumerate(data, 1):
        cells = [c.strip() for c in r.split("|")]
        lab = "行%d(%s)" % (i, cells[1] if len(cells) > 1 else "?")
        v = cells[idx] if idx < len(cells) else ""
        if "门禁=" not in v:
            missing.append("%s：缺六段痕（C3.5 结果未落表）" % lab)
            continue
        illegal += validate_trace(v, lab)
    if missing:
        print("❌ 蒸馏报告缺 %s %d 行: %s" % (TRACE_FIELD, len(missing), " | ".join(missing[:5])))
        print("   → 回到 flow-C.md 步骤 C4 补齐痕列（脚本闸门·exit 2）")
        return 2
    if illegal:
        print("❌ 蒸馏报告门禁痕取值/联动非法 %d 项: %s" % (len(illegal), " | ".join(illegal[:5])))
        print("   → 按 flow-C.md C3.5 三子步骤修正后重写（脚本闸门·exit 3）")
        return 3
    print("✅ 蒸馏报告 C3.5 门禁痕 校验通过：真实决策行 %d 行·六段齐全＋联动合法 — %s" % (len(data), path))
    return 0


PAIR_MIN = 12  # 配对阈值：标题规范化后存在 ≥PAIR_MIN 字符公共子串即成对（对长中文/编号标题稳定）


def _norm(s):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s)


def _lcs_hit(a, b, k):
    if len(a) > len(b):
        a, b = b, a
    return any(a[i:i + k] in b for i in range(len(a) - k + 1))

ID_RX = re.compile(r"[A-Z]{1,4}-?20\d{6}-\d{2,4}")   # QCN-20261011-018 / R-20261012-01 族 ID 精确键（v2.2.1 补定义·上批漏落）


def pair_audit(text):
    """表↔详情双向配对审计（v2.2.1）。扫描面=全文件（总追踪表节＋各批次/待整合队列子表——
    2026-10-12 实证「待整合队列」节也散着 🔴 行，只扫总追踪表=第三面账漏网）。
    方向1（表→详情）：每条 🔴 表行必有标题同源的 🔴 详情——没有＝「表在🔴但详情已销/未建」。
    方向2（详情→表）：每条 🔴 详情必在文件内有对应表行（任何状态）——没有＝「详情从未在表上登记」。
    配对键＝「行内 ID 交集（硬证据）∪ 标题规范化 ≥PAIR_MIN 公共子串（兜无 ID 存量）」。
    🔴 判定=状态字段**开头**（v2.2.0 用 contains🔴 把『✅已整合(…🔴注记)』误判🔴——判据开头化收紧）。
    强度上限（如实）：标题模糊通道对『同案不同题且无 ID』会失配——失配只显式点名⛔不自动改表；
    ✅/📌 存量不回溯。返回失配列表；文件无任何表格行 → None（跳过声明）。"""
    all_rows = [l for l in text.splitlines() if l.startswith("| ") and ("🔴待整合" in l or "🔴 待整合" in l)]
    any_rows = [l for l in text.splitlines() if l.startswith("| ") and len(l) > 8]
    if not any_rows:
        return None
    dreds = []
    for b in re.split(r"(?=^### )", text, flags=re.M):
        if b.startswith("### ") and re.search(r"^- 🚦 状态[：:]\s*🔴", b, re.M):
            dreds.append(b.splitlines()[0].lstrip("# ").strip())
    def _hit(a, c):
        ai, ci = set(ID_RX.findall(a)), set(ID_RX.findall(c))
        return bool(ai & ci) or _lcs_hit(_norm(a), _norm(c), PAIR_MIN)
    bad = []
    for r in all_rows:
        if not any(_hit(r, d) for d in dreds):
            bad.append("表行🔴 无对应🔴详情（详情未建或状态已改而表/队列漏更）: " + r.strip().strip("|").split("|")[1].strip()[:42] if len(r.split("|")) > 2 else "表行🔴 无对应🔴详情: " + r[:44])
    for d in dreds:
        if not any(_hit(l, d) for l in any_rows):
            bad.append("详情🔴 从未在表上登记（任何状态均无配对行）: " + d[:44])
    return bad


def check_feedback_entries(text, path):
    """反哺日志模式主校验。返回 exit code。"""
    blocks = [b for b in re.split(r"(?=^### )", text, flags=re.M) if b.startswith("### ")]
    if not blocks:
        print(f"❌ 未解析到任何反哺条目（`### ` 标题 0 个）: {path}")
        return 1
    missing, illegal = [], []
    n_new = n_stock = 0
    for b in blocks:
        title = b.splitlines()[0].lstrip("#").strip()[:48]
        m_date = DATE_RE.search(b)
        if m_date is None:
            # v2.2.2 补堵"缺日期即免检"后门：无 📅 日期行却含门禁痕字段＝新条目形态，按缺痕同级拦（exit 2）
            if TRACE_FIELD in b:
                n_new += 1
                missing.append(f"{title}…（无 📅 日期行·却含 {TRACE_FIELD}）")
                continue
            n_stock += 1
            continue
        d = m_date.group(1)
        if d < TRACE_CUTOFF:
            n_stock += 1
            continue
        n_new += 1
        v = _field(b, TRACE_FIELD)
        if not v:
            missing.append(f"{title}…（{d}）缺 {TRACE_FIELD} 行")
            continue
        illegal += validate_trace(v, title + "…")
    if missing:
        print(f"❌ 反哺条目缺 {TRACE_FIELD} {len(missing)} 条: " + " | ".join(missing[:5]))
        print("   → 按 SKILL.md 步骤 E4 Schema 补齐（脚本闸门·exit 2）")
        return 2
    if illegal:
        print(f"❌ 门禁痕取值/联动非法 {len(illegal)} 条: " + " | ".join(illegal[:5]))
        print("   → 按 SKILL.md 步骤 E3.5 四锁修正后重写（脚本闸门·exit 3）")
        return 3
    print(f"✅ 反哺日志 Schema 校验通过：新条目 {n_new} 条（门禁痕六段齐全+联动合法）· 存量 {n_stock} 条（<{TRACE_CUTOFF} 祖父化跳过）— {path}")
    bad = pair_audit(text)
    if bad is None:
        print("🧪 表↔详情配对：无总追踪表节，跳过（夹具/局部语料形态）")
    elif bad:
        print(f"❌ 表↔详情配对失配 {len(bad)} 项（exit 4·双向断言 v2.2.1）：")
        for x in bad[:8]:
            print("   · " + x)
        print("   → 逐条按名字对账：改详情必同步表行，或表行🔴须建详情；确属误配（近义标题）人工复核后保持（脚本闸门·exit 4）")
        return 4
    else:
        print("🧪 表↔详情双向配对：🔴 集合双向全对 ✓")
    return 0


def check_learnings(path, text):
    """v1.x 原有：错误归档模式（整文件语义，局限性声明见模块 docstring）。"""
    basename = os.path.basename(path)
    is_tool_specific = basename.endswith("_errors.md") and basename not in ("ERRORS.md", "LEARNINGS.md")
    required_bold = [f for f in REQUIRED_BOLD_FIELDS if not (f == "来源 AI" and is_tool_specific)]

    # ── v2.3.0 作用域自证：先数记录，再谈通过（治"解析 0 条却打全绿"）──
    recs = [b for b in re.split(r"(?=^##+\s+\[)", text, flags=re.M) if re.match(r"^##+\s+\[", b)]
    if not recs:
        # v2.3.0b：零记录**默认不判红**——learnings 目录混有说明型/复核表型 .md（实测 12 个），
        #   判红等于用"假红风暴"换"仪器沉默"，比原病更坏（真红会淹没在其中）。改为强制显形 ⚠️ 行；
        #   要硬约束的调用方自带 --expect-records N（归档写入端用 1），把选择权留给消费者。
        print("⚠️ 作用域=0 条：未解析到 `## [ID]`／`### [ID]` 记录——若本文件是归档文件则其方言已脱离断言域须复核；"
              "若是说明/复核型文档属正常。需判红请加 `--expect-records 1` — %s" % os.path.basename(path))
        if EXPECT_RECORDS > 0:
            print("   → --expect-records %d 未达（exit 1）" % EXPECT_RECORDS)
            return 1
        return 0
    strict = [b for b in recs if (_get_field(b, "Logged") or "0000-00-00")[:10] >= STRICT_FROM]
    legacy = len(recs) - len(strict)
    print("🧪 作用域自证：解析 %d 条记录·逐条实检 %d 条（Logged≥%s）·存量祖父化 %d 条 — %s"
          % (len(recs), len(strict), STRICT_FROM, legacy, os.path.basename(path)))

    # 整文件存在性层（v1.x 原语义·v2.3.1b 加 grandfather 闸门）：仅当本文件含新条目（Logged≥STRICT_FROM）时才生效，
    #   纯存量档案不再被追改（旧行为：一个 2026-04 的说明型 .md 也报"缺 12 字段"＝27 个文件常红，红到无人看＝等于没有）。
    missing = []
    if strict:
        missing = [f for f in required_bold if not _has_field(text, f)]
        missing += [x for x in REQUIRED_SECTIONS if not _has_section(text, x)]
    if missing:
        print(f"❌ 必填字段缺失 {len(missing)} 个: {', '.join(missing)}")
        print("   → 回到步骤A2按 references/错误记录模板.md 补齐后再写（脚本闸门·exit 2）")
        return 2

    is_legacy_active = re.search(r"^\*\*Status\*\*\s*:\s*active\b", text, re.M)
    illegal = []
    for field, allowed in ENUMS.items():
        if field == "Status" and is_legacy_active:
            continue
        m = re.search(rf"^\*\*{re.escape(field)}\*\*\s*:\s*(.+)$", text, re.M)
        if not m:
            continue
        val = m.group(1).strip()
        if not any(val.startswith(a) or a in val for a in allowed):
            illegal.append(f"{field}={val}（应 ∈ {'/'.join(allowed)}）")
    if illegal and strict:
        # v2.3.3b：整文件枚举粗筛只在含新条目时生效——纯存量档案不追改（FEATURE_REQUESTS.md 2026-03 自有 Area 词表实证）
        print(f"❌ 枚举取值非法 {len(illegal)} 个: " + " | ".join(illegal))
        print("   → 按 SKILL.md 步骤A2 枚举修正（脚本闸门·exit 3）")
        return 3

    blocks = [b for b in re.split(r"(?=^##+\s+\[)", text, flags=re.M) if re.match(r"^##+\s+\[", b)]
    # ── v2.3.0 逐条断言（新条目字段/小节/枚举/联动·治"整文件存在性掩盖新条目缺字段"）──
    perrec_bad = []
    for b in strict:
        rid = b.splitlines()[0].strip()[:46]
        mf = [f for f in required_bold if not _has_field(b, f)]
        ms = [x for x in REQUIRED_SECTIONS if not _has_section(b, x)]
        if mf or ms:
            perrec_bad.append("%s 缺字段%s%s" % (rid, ("：" + "/".join(mf)) if mf else "",
                                                 ("·缺小节" + "/".join(ms)) if ms else ""))
            continue
        st = _get_field(b, "Status").split()[0].strip("（(:") if _get_field(b, "Status") else ""
        st = re.sub(r"\(.*$", "", st).strip()
        if st and st != "active" and st not in ("pending", "resolved", "promoted"):
            perrec_bad.append("%s Status 非法=%s" % (rid, st))
        for fld in ("Priority", "Area", "认知象限"):
            val = _get_field(b, fld)
            if val and not any(val.startswith(a) or a in val for a in ENUMS[fld]):
                perrec_bad.append("%s %s 枚举非法=%s" % (rid, fld, val[:22]))
        if st in ("promoted", "resolved") and "已知已知" not in _get_field(b, "认知象限"):
            if _get_field(b, "Logged")[:10] >= "2026-07-01":
                perrec_bad.append("%s 联动非法=%s 却非已知已知" % (rid, st))
    if perrec_bad:
        print("❌ 逐条断言未过 %d 条（新条目·v2.3.0）:" % len(perrec_bad))
        for x in perrec_bad[:8]:
            print("   · " + x)
        print("   → 补齐本次新条目字段/小节后再写（exit 2）；存量条目按祖父化不在此列")
        return 2

    linkage_bad = []
    for b in blocks:
        if not b.startswith("## ["):
            continue
        m_status = re.search(r"^\*\*Status\*\*\s*:\s*(\S+)", b, re.M)
        if not m_status or m_status.group(1) in ("active",):
            continue
        if m_status.group(1) not in ("promoted", "resolved"):
            continue
        m_log = re.search(r"^\*\*Logged\*\*\s*:\s*(\d{4}-\d{2}-\d{2})", b, re.M)
        if m_log and m_log.group(1) < "2026-07-01":
            continue
        m_quad = re.search(r"^\*\*认知象限\*\*\s*:\s*(.+)$", b, re.M)
        quad = m_quad.group(1).strip() if m_quad else ""
        if "已知已知" not in quad:
            title = b.splitlines()[0].strip()[:60]
            linkage_bad.append(f"{title}… Status={m_status.group(1)} 但认知象限={quad or '（缺失）'}（应=已知已知）")
    if linkage_bad:
        print(f"❌ Status↔认知象限联动非法 {len(linkage_bad)} 条: " + " | ".join(linkage_bad))
        print("   → 按 Poka-Yoke 3.1 修正认知象限（脚本闸门·exit 3）")
        return 3

    print(f"✅ 归档 Schema 校验通过：字段 {len(required_bold)}+{len(REQUIRED_SECTIONS)} 齐全 + 枚举合法 + 联动合法 — {path}")
    return 0


# ── 自测夹具（正/负/变异三段·判据改坏必红）──
_FIX_OK_E = ("### 2026-10-13 10:00 · 正例甲\n\n"
             "- 📅 日期：2026-10-13\n"
             f"- {TRACE_FIELD}：门禁=E3.5｜锚[成立:发版链缺真机项;失效:纯文档改动]｜"
             "8要素[1✅2✅3✅4✅5✅6✅7✅8✅]｜自爆[复检补2项后仍全✅→❌]｜结论[❌不可反哺]｜签名[❌]\n")
_FIX_OK_C = ("### 2026-10-13 11:00 · 正例乙\n\n"
             "- 📅 日期：2026-10-13\n"
             f"- {TRACE_FIELD}：门禁=C3.5｜锚[成立:蒸馏决策表;失效:单条新错]｜"
             "8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]\n")
_FIX_STOCK = ("### 2026-10-11 19:52 · 存量例（无门禁痕·祖父化）\n\n"
              "- 📅 日期：2026-10-11\n")
_N = lambda bad: ("### 2026-10-13 12:00 · 负例\n\n- 📅 日期：2026-10-13\n"
                  f"- {TRACE_FIELD}：{bad}\n")


def _self_test():
    cases = [
        ("P1 正例·E3.5 全绿但已触发自爆→❌", _FIX_OK_E, 0),
        ("P2 正例·C3.5 有❌且未触发自爆→✅", _FIX_OK_C, 0),
        ("N1 缺门禁痕行", "### 2026-10-13 · 缺痕\n\n- 📅 日期：2026-10-13\n- 🔖 反哺标题：x\n", 2),
        ("N2 8要素只有7格", _N("门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2✅3✅4✅5✅6✅7✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]"), 3),
        ("N3 锚 失效列空", _N("门禁=E3.5｜锚[成立:a;失效:]｜8要素[1✅2✅3✅4✅5✅6✅7❌8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]"), 3),
        ("N4 全✅却自爆=未触发", _N("门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2✅3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]"), 3),
        ("N5 结论✅ 签名❌", _N("门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[❌]"), 3),
        ("N6 结论🟡落盘", _N("门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[🟡需修正]｜签名[✅]"), 3),
        ("N7 门禁枚举非法", _N("门禁=X9.9｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]"), 3),
        ("N8 缺 自爆 段", _N("门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜结论[✅可反哺]｜签名[✅]"), 3),
        ("P3 存量条目无痕=跳过不判红", _FIX_STOCK, 0),
        ("P4 混合语料（存量+合规）", _FIX_STOCK + _FIX_OK_C, 0),
        ("P5 配对·表行🔴⇔详情🔴同源→0",
         "## 总追踪表\n| 日期 | 反哺标题 | 来源 | 落点 | 状态 |\n|:-:|---|---|---|---|\n"
         "| 10-13 | 配对审计正例条目甲乙丙丁戊己庚 | x | y | 🔴待整合 |\n\n"
         + ("### 2026-10-13 12:00 · 配对审计正例条目甲乙丙丁戊己庚\n\n- 📅 日期：2026-10-13\n"
            "- 🚦 状态：🔴待整合\n"
            f"- {TRACE_FIELD}：门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]\n"), 0),
        ("N9 表行🔴 无详情🔴（改详情漏表之镜像）→4",
         "## 总追踪表\n| 日期 | 反哺标题 | 来源 | 落点 | 状态 |\n|:-:|---|---|---|---|\n"
         "| 10-13 | 滞后失配条目壬癸甲乙丙丁戊 | x | y | 🔴待整合 |\n\n" + _FIX_OK_C, 4),
        ("N10 详情🔴 无表行（表漏登）→4",
         "## 总追踪表\n| 日期 | 反哺标题 | 来源 | 落点 | 状态 |\n|:-:|---|---|---|---|\n"
         "| 10-13 | 无关已结条目子丑寅卯 | x | y | ✅已整合 |\n\n"
         + ("### 2026-10-13 13:00 · 孤儿详情条目卯辰巳午未申酉\n\n- 📅 日期：2026-10-13\n- 🚦 状态：🔴待整合\n"
            f"- {TRACE_FIELD}：门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]\n"), 4),
        ("P6 无表节（局部语料）→跳过不判红", _FIX_OK_C, 0),
    ]
    ok = True
    print(f"===== growth_box_schema_check.py（v{__version__} · 反哺日志模式）--self-test =====")
    for name, body, want in cases:
        got = check_feedback_entries(body, "<fixture>")
        mark = "✅" if got == want else f"❌（want={want} got={got}）"
        if got != want:
            ok = False
        print(f"  {mark} {name}")
    # 变异检验：把定值法常数改坏，正例必红——证明判据不是恒真
    global LOCK2_SLOTS
    _keep = LOCK2_SLOTS
    LOCK2_SLOTS = 7
    mutated = check_feedback_entries(_FIX_OK_E, "<mutation>")
    LOCK2_SLOTS = _keep
    print(f"  {'✅' if mutated != 0 else '❌'} MUT 变异·定值法 8→7 后正例必红（rc={mutated}）")
    if mutated == 0:
        ok = False
    # MUT2 配对判据变异（v2.2.0）：阈值 12→30 后 P5 配对正例必红（证明配对 matcher 有牙·非恒绿）
    global PAIR_MIN
    _kp = PAIR_MIN
    PAIR_MIN = 30
    p5_body = "## 总追踪表\n| 日期 | 反哺标题 | 来源 | 落点 | 状态 |\n|:-:|---|---|---|---|\n| 10-13 | 配对审计正例条目甲乙丙丁戊己庚 | x | y | 🔴待整合 |\n\n" + ("### 2026-10-13 12:00 · 配对审计正例条目甲乙丙丁戊己庚\n\n- 📅 日期：2026-10-13\n- 🚦 状态：🔴待整合\n" + f"- {TRACE_FIELD}：门禁=E3.5｜锚[成立:a;失效:b]｜8要素[1✅2❌3✅4✅5✅6✅7✅8✅]｜自爆[未触发]｜结论[✅可反哺]｜签名[✅]\n")
    mut2 = check_feedback_entries(p5_body, "<mutation-pair>")
    PAIR_MIN = _kp
    print(f"  {'✅' if mut2 == 4 else '❌'} MUT2 变异·PAIR_MIN 12→30 后配对正例必红 rc=4（实得 {mut2}）")
    if mut2 != 4:
        ok = False
    # ── v2.3.0 learnings 模式夹具（方言兼容·逐条断言·零记录显形）＋MUT3 变异检验 ──
    import tempfile as _tf
    _lfix = [("L1 专属方言合规→0", "lg_errors.md", """### [QCN-T-001] 专属方言合规

- Logged: 2026-10-13 12:00
- Priority: medium
- Status: pending(1/3)
- Area: 验证
- 认知象限: 已知未知（收集中）
- Summary: 摘要
- Details:
  - 事实：甲
- Root Cause: 乙
- Rule: 丙
- Why: 丁
- How to apply: 戊
""", 0),
             ("L2 专属方言缺 Rule/Summary→2", "lm_errors.md", """### [QCN-T-001] 专属方言合规

- Logged: 2026-10-13 12:00
- Priority: medium
- Status: pending(1/3)
- Area: 验证
- 认知象限: 已知未知（收集中）
- Details:
  - 事实：甲
- Root Cause: 乙
- Why: 丁
- How to apply: 戊
""", 2),
             ("L3 说明型零记录→仅显形 0", "ln.md", """# 说明型文档

- Logged: 2026-10-13 12:00
""", 0),
             ("L4 存量缺小节→祖父化 0", "ll_errors.md", """### [QCN-T-001] 专属方言合规

- Logged: 2026-09-01 09:00
- Priority: medium
- Status: pending(1/3)
- Area: 验证
- 认知象限: 已知未知（收集中）
- Summary: 摘要
- Details:
  - 事实：甲
- Root Cause: 乙
- Why: 丁
- How to apply: 戊
""", 0),
             ("L5 通用粗体方言合规→0", "lb.md", """## [ERR-T-1] 通用粗体方言合规

**Logged**: 2026-10-13 12:00
**Priority**: low
**Status**: pending
**Area**: 其他
**来源 AI**: Qoder CN
**认知象限**: 已知未知（收集中）
### Summary
a
### Details
b
### Root Cause
c
### Rule
d
### Why
e
### How to apply
f
""", 0)]
    _d = _tf.mkdtemp(prefix="gb_self_L_")
    for _nm, _fn, _body, _want in _lfix:
        _p = os.path.join(_d, _fn)
        with open(_p, "w", encoding="utf-8") as _f:
            _f.write(_body)
        _buf = io.StringIO()
        _keep_out = sys.stdout
        try:
            sys.stdout = _buf
            _got = check_learnings(_p, _body)
        finally:
            sys.stdout = _keep_out
        _scope = [l for l in _buf.getvalue().splitlines() if ("作用域" in l or "逐条断言" in l)]
        _mk = "✅" if _got == _want else "❌(want=%s got=%s)" % (_want, _got)
        if _got != _want:
            ok = False
        print("  %s %-24s %s" % (_mk, _nm, (_scope[0][:60] if _scope else "")))
    # L6 零记录＋--expect-records 语义（同一路径必须判红，证明自证行不只是装饰）
    _p6 = os.path.join(_d, "lexp_errors.md")
    open(_p6, "w", encoding="utf-8").write(_lfix[2][2])
    global EXPECT_RECORDS
    _k6 = EXPECT_RECORDS
    EXPECT_RECORDS = 1
    _b6 = io.StringIO(); _o6 = sys.stdout
    try:
        sys.stdout = _b6
        _g6 = check_learnings(_p6, _lfix[2][2])
    finally:
        sys.stdout = _o6
    EXPECT_RECORDS = _k6
    print("  %s L7 零记录＋expect=1 → 必红(%s)" % ("✅" if _g6 == 1 else "❌", _g6))
    if _g6 != 1:
        ok = False
    # MUT3 变异：把生效日提前 → 存量缺字段条目必红（证明逐条断言有牙·非恒绿）
    _kS = STRICT_FROM
    globals()["STRICT_FROM"] = "2026-01-01"
    _b3 = io.StringIO(); _o3 = sys.stdout
    try:
        sys.stdout = _b3
        _g3 = check_learnings(os.path.join(_d, "ll_errors.md"), _lfix[3][2])
    finally:
        sys.stdout = _o3
    globals()["STRICT_FROM"] = _kS
    print("  %s MUT3 变异·STRICT_FROM 提前后存量缺小节条目必红(%s)" % ("✅" if _g3 != 0 else "❌", _g3))
    if _g3 == 0:
        ok = False
    print("✅✅ --self-test 全过" if ok else "❌ --self-test 有项不过")
    return 0 if ok else 1


__version__ = "2.3.4"   # v2.3.4（2026-10-13）：纠正 v2.3.3 误改——祖父化闸门落在 check_learnings（v2.3.3 的 replace 命中了 check_distill_report 的同名行，给那里塞进未定义变量 strict，因 `illegal and strict` 短路而未即时爆雷·已复原）；并移除 v2.3.2 遗留的 `if not strict: pass` 空分支\n               # v2.3.3（2026-10-13）：整文件枚举粗筛也加 grandfather 闸门（FEATURE_REQUESTS.md 三条 2026-03 存量记录自有 Area 词表被误判 exit 3）\n               # v2.3.2（2026-10-13）：①零记录文件显形后直接返回（不再跑存在性层制造纯假红）②整文件存在性层加 grandfather 闸门——只在含新条目时生效（实测旧行为使 learnings 目录 27/34 文件常红·红到失效）\n               # v2.3.1（2026-10-13·v2.3.0b）：零记录由 exit 1 降为强制显形 ⚠️＋可选 --expect-records 硬约束（实测 learnings 目录含 12 个说明/复核型 .md，判红=假红风暴淹没真警报）；self-test 补 L1-L7 五夹具＋MUT3 变异检验\n               # v2.3.0（2026-10-13·反哺 R-20261013-03 落地）：learnings 模式加①方言兼容（三种字段/小节写法）②记录切分含 `### [`（工具专属条目此前整族不进断言域）③新条目逐条断言（Logged≥2026-10-13，存量祖父化但计数显形）④作用域自证行＋解析 0 条判 exit 1（⛔零记录打全绿）
               # v2.2.2（2026-10-12·Loop 成长箱 R3 双路审查 P-12/P-14 承接）：①--distill 模板占位行只认首格 [编号]（原整行子串＝真行可转白）②反哺模式堵"缺 📅 日期行即整条零校验"后门（含门禁痕而无日期＝按缺痕拦）
               # v2.2.1（同日）：dreds 判据=状态开头🔴（contains 会误杀✅带注记）·表侧扫描面=全文件🔴行（待整合队列节实证漏网面）·配对键=ID交集∪标题子串双通道   # v2.2.0（2026-10-12·皮叔令「做；」）：+pair_audit 表↔详情双向配对断言（exit 4）——治"改详情漏改表/表🔴无详情"双形态（2026-10-12 三行滞后全绿溜过实证）；只对🔴集合断言·✅📌不回溯；失配显式点名不自动改表（强度上限如实）


def main():
    if "--self-test" in sys.argv:
        return _self_test()
    if "--distill" in sys.argv:
        pa = [a for a in sys.argv[1:] if not a.startswith("-")]
        if not pa or not os.path.exists(pa[0]):
            print("用法: python3 growth_box_schema_check.py <蒸馏报告.md> --distill")
            return 1
        return check_distill_report(open(pa[0], encoding="utf-8").read(), pa[0])
    global EXPECT_RECORDS
    if "--expect-records" in sys.argv:
        _i = sys.argv.index("--expect-records")
        try:
            EXPECT_RECORDS = int(sys.argv[_i + 1])
        except (IndexError, ValueError):
            print("用法: --expect-records <整数>"); return 1
    force = "--feedback" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-") and a != str(EXPECT_RECORDS)]
    if not args:
        print("用法: python3 growth_box_schema_check.py <路径> [--feedback|--distill] | --self-test")
        return 1
    path = args[0]
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        return 1
    text = open(path, encoding="utf-8").read()
    # 分流只按文件名（⛔不用全文子串启发——同族坑：卡A 步1 曾因「全文含标题」误判命中压掉别人的真候选）
    if os.path.basename(path) == FEEDBACK_BASENAME or force:
        return check_feedback_entries(text, path)
    return check_learnings(path, text)


if __name__ == "__main__":
    sys.exit(main())