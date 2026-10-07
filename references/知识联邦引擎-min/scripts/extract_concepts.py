#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
extract_concepts.py — 三库联邦·概念抽取管道（D-F5/F6/F7实现）
设计依据: 08-三库联邦设计.md
架构: prepare(脚本收集) → AI抽概念(唯一AI环节·会话内完成) → commit(脚本校验+入库+留痕)
铁律: 机械活全在脚本 / AI只碰语义 / 有痕跳过≠静默跳过 / 时间=系统时钟
用法:
  python3 extract_concepts.py prepare   # 收集未处理源文本→bundle文件，AI读它抽概念
  python3 extract_concepts.py commit <concepts.json>  # 校验AI产出→写概念卡+log+索引
  python3 extract_concepts.py status    # 查看进度状态
"""
import sys, os, json, re, glob
from datetime import datetime, timedelta, date
from source_hash import source_content_hash  # 真相单一住所(守卫编写规范原则1)·v2026-07-28哈希谓词

# ==== 路径配置（端用户版·单一真源 _paths·自推导记忆共享中心） ====
from _paths import (MC, FED, INSTALLED, CONCEPTS_DIR, AILIB_DIR, INDEX_FILE,
                    SYSLOG_DIR, diary_dir, ensure_dirs)
LOG_FILE = os.path.join(FED, "log.md") if FED else None
BUNDLE_FILE = os.path.join(FED, "pending_bundle.md") if FED else None
STATE_FILE = os.path.join(FED, ".batch_state.json") if FED else None
CANDIDATES_FILE = os.path.join(FED, "collision_candidates.json") if FED else None  # 消费健康度数据源

def _require_installed():
    """prepare/commit 仅安装态可跑（需 [记忆共享中心]/脚本中心 布局）"""
    if not INSTALLED:
        print("❌ 未安装态：请先完成安装（本脚本需位于 [记忆共享中心]/脚本中心/知识联邦引擎/scripts/ 内运行）")
        sys.exit(1)

VALID_OWNERS = {"AI", "我", "共创"}

def now_str():  # 时间永远来自系统时钟（D-F8要点）
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def today():
    return date.today()

def load_state():
    if STATE_FILE and os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_batch_date": None}

def save_state(state):
    if not STATE_FILE:
        return
    # v2026-08-12 根治（时序边角·晚写感悟漏抽）：批次时间戳=晚写源重扫判定基准
    state["last_batch_ts"] = datetime.now().timestamp()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def append_log(entry_type, detail):
    """log.md追加条目（单一日志·封口块门禁的检查目标）·未安装态静默跳过"""
    if not LOG_FILE:
        return
    with open(LOG_FILE, "a") as f:
        f.write(f"\n## [{today().isoformat()}] {entry_type} | {detail} | 记录时间:{now_str()}\n")

def dates_to_process(state):
    """补齐式（catch-up）：从上次批次日期+1到今天"""
    last = state.get("last_batch_date")
    start = date.fromisoformat(last) + timedelta(days=1) if last else today()
    if start > today():
        return []
    out, d = [], start
    while d <= today():
        out.append(d); d += timedelta(days=1)
    return out

def extract_diary_insight(d):
    """定位日记'今日感悟'段（实测结构: ## 6️⃣ 💡 今日感悟）"""
    path = os.path.join(diary_dir(), d.strftime("%Y-%m"), f"{d.isoformat()}.md")
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    m = re.search(r"##[^\n]*今日感悟[^\n]*\n(.*?)(?=\n## |\Z)", text, re.S)
    if not m:
        return None
    content = m.group(1)
    # 模板过滤: 去掉HTML注释/分隔线/空白后不足10字=未填写，视为无源
    stripped = re.sub(r"<!--.*?-->|---|[\s%]", "", content, flags=re.S)
    return content.strip() if len(stripped) >= 10 else None

def read_syslog(d):
    path = os.path.join(SYSLOG_DIR, f"系统日志_{d.isoformat()}.md")
    if not os.path.exists(path):
        return None
    return open(path, encoding="utf-8").read().strip()

def cmd_prepare():
    state = load_state()
    dates = dates_to_process(state)
    if not dates:
        # v2026-08-12 根治（时序边角·8/12晚写感悟漏抽）：日期已处理≠该日源已抽完
        # 日记感悟可在批次后任意时刻晚写（如8/11补录时8/12感悟尚未写）——mtime晚于上次批次→重扫今日
        last_ts = state.get("last_batch_ts")
        if last_ts:
            recheck = []
            p = os.path.join(diary_dir(), today().strftime("%Y-%m"), f"{today().isoformat()}.md")
            if os.path.exists(p) and os.path.getmtime(p) > last_ts and extract_diary_insight(today()):
                recheck.append(today())
                append_log("ingest", f"晚写源重扫: 今日日记感悟 mtime {datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M')} 晚于批次 {datetime.fromtimestamp(last_ts).strftime('%H:%M')}")
                print(f"RECHECK: 今日日记感悟晚写，重扫 {today().isoformat()}")
            if not recheck:
                append_log("ingest", "skipped: 今日批次已处理")
                print("SKIP: 今日已处理过"); return
            dates = recheck
        else:
            append_log("ingest", "skipped: 今日批次已处理")
            print("SKIP: 今日已处理过"); return
    sections, missing = [], []
    for d in dates:
        diary = extract_diary_insight(d)
        syslog = read_syslog(d)
        if diary:
            sections.append(f"### 来源: 日记感悟 {d.isoformat()}\n{diary}")
        if syslog:
            sections.append(f"### 来源: 系统日志 {d.isoformat()}\n{syslog[:3000]}")
        if not diary and not syslog:
            missing.append(d.isoformat())
    if not sections:  # 有痕跳过≠静默跳过（D-F6）
        append_log("ingest", f"skipped: no sources ({','.join(missing)})")
        # 时序保护: 今天可能还没写感悟(如清晨跑)——进度只推到昨天，今天保持待处理
        yesterday = (today() - timedelta(days=1)).isoformat()
        state["last_batch_date"] = yesterday; save_state(state)
        print("SKIP-LOGGED: 无进料源已留痕(今天保持待处理,晚间复盘可重扫)"); return
    header = ("# 待抽取源文本（AI读此文件按card-schema抽概念·输出严格JSON数组）\n"
              "# 每个概念: {\"concept_name\":\"\",\"definition\":\"一句话\",\"source_cards\":[\"来源\"],"
              "\"source_owner\":\"AI|我|共创\",\"domain\":\"\"}\n"
              "# 分流规则: 日记感悟的概念owner=我 / 系统日志的概念owner=AI或共创\n"
              "# ⚠️source_cards格式allowlist（v2026-08-06·S018防漂移·hash解析器要求/分隔）:\n"
              "#   - 日记来源 MUST写: 日记感悟 YYYY-MM-DD\n"
              "#   - 日志来源 MUST写: 系统日志 YYYY-MM-DD/小节名（/后为日志中###标题，须逐字一致）\n"
              "#   ⛔DO NOT 空格分隔标题 / 括号注释 / 自造格式——否则source_hash无法解析退mtime\n"
              "# v2026-08-15 根治·源段漏抽（8/14系统日志漏抽·8/12晚写根治未覆盖第二失败模式）:\n"
              "#   每个源段必须被至少一张卡引用（source_cards前缀匹配），否则commit拒绝(exit 4)。\n"
              "#   若某源段确无概念可抽，AI须在concepts_out.json显式声明 skipped_sources 才能过。\n"
              f"# 覆盖日期: {dates[0].isoformat()} ~ {dates[-1].isoformat()}\n"
              f"# SOURCES: {'|'.join(s.splitlines()[0][len('### 来源: '):] for s in sections)}\n\n")
    with open(BUNDLE_FILE, "w") as f:
        f.write(header + "\n\n".join(sections))
    print(f"PREPARED: {BUNDLE_FILE}\n覆盖{len(dates)}天, {len(sections)}个源段。AI请读bundle抽概念后调commit。")

def next_concept_id():
    ids = [int(m.group(1)) for p in glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md"))
           if (m := re.search(r"C-(\d+)", os.path.basename(p)))]
    return max(ids, default=0) + 1

def existing_concepts():
    """concept_name → filepath"""
    out = {}
    for p in glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md")):
        t = open(p, encoding="utf-8").read()
        if m := re.search(r'concept_name:\s*"?([^"\n]+)"?', t):
            out[m.group(1).strip()] = p
    return out

def existing_source_hashes():
    """source_hash值 → 出现该hash的卡路径列表（commit幂等查重·v2026-08-10根治双跑重复卡）

    每张概念卡frontmatter存 source_hash（来源内容指纹）。同一来源两次commit若AI命名漂移，
    按 concept_name 精确匹配会失效（C-044≡C-047 即此坑）。改用 hash 查重可免疫命名变化，
    使 commit 幂等——同一来源无论跑几次都只落一张卡。"""
    out = {}
    for p in glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md")):
        t = open(p, encoding="utf-8").read()
        for m in re.finditer(r'-\s*"[^"]+":\s*([0-9a-fA-F]+)', t):
            out.setdefault(m.group(1), []).append(p)
    return out

def validate(c):
    """D-F6③校验：字段全/definition一句话/owner合法"""
    errs = []
    for k in ("concept_name", "definition", "source_cards", "source_owner", "domain"):
        if not c.get(k): errs.append(f"缺字段{k}")
    if c.get("definition") and ("\n" in c["definition"] or len(c["definition"]) > 120):
        errs.append("definition须为一句话(≤120字无换行)")
    if c.get("source_owner") not in VALID_OWNERS:
        errs.append(f"owner非法:{c.get('source_owner')}")
    return errs

def check_bundle_coverage(concepts, json_path, meta=None):
    """v2026-08-15 根治·源段漏抽（8/14系统日志漏抽实锤）：
    bundle 源段清单（# SOURCES: 行）vs AI 提交概念引用（source_cards）+ 显式跳过（skipped_sources）。
    返回未覆盖源段列表（空=全覆盖）。
    v2026-08-17：meta 参数=dict 格式的 skipped_sources 载体（顶层 {"concepts":[...],"skipped_sources":[...]}）。
    v2026-09-20 根治（系统日志概念提取断档事故）：
    系统日志源段为必选，禁止skipped！
    系统日志记录的是系统建设实战方法论，是宝贵的可复利资产，必须每天至少提取1个概念。
    即使在skipped_sources中声明系统日志，也不视为覆盖——必须真正提取概念。
    """
    if not os.path.exists(BUNDLE_FILE):
        return []  # 无 bundle（如手动构造 JSON 补抽场景）→ 不强制
    text = open(BUNDLE_FILE, encoding="utf-8").read()
    m = re.search(r"^# SOURCES:\s*(.+)$", text, re.M)
    if not m:
        return []  # 旧版 bundle 无 SOURCES 行 → 不强制（向前兼容）
    sources = [s.strip() for s in m.group(1).split("|") if s.strip()]
    # 收集所有被引用的源（前缀匹配：日记感悟 YYYY-MM-DD / 系统日志 YYYY-MM-DD/小节）
    covered = set()
    for c in concepts:
        for src in c.get("source_cards", []):
            for s in sources:
                if src.startswith(s.split("/")[0]) or src.startswith(s):
                    covered.add(s)
    # 显式跳过（AI 判定无概念可抽）——meta 为 dict 顶层时的 skipped_sources
    # v2026-09-20 根治：系统日志源段即使在skipped中也不视为覆盖！
    skipped = (meta or {}).get("skipped_sources", []) if isinstance(meta, dict) else []
    for s in skipped:
        for src in sources:
            if src.startswith(s.split("/")[0]) or src == s:
                if "系统日志" not in src:  # 日记感悟可以skipped，系统日志不行
                    covered.add(src)
    missing = [s for s in sources if s not in covered]
    return missing


def cmd_commit(json_path):
    with open(json_path) as f:
        raw = json.load(f)
    # v2026-08-17: 顶层兼容两种格式——list（纯概念数组）或 dict {"concepts":[...],"skipped_sources":[...]}
    if isinstance(raw, dict):
        concepts = raw.get("concepts", [])
        meta = raw
    else:
        concepts = raw
        meta = None
    # v2026-08-15 根治·源段漏抽（8/14系统日志漏抽·8/12晚写根治未覆盖第二失败模式）：
    # bundle 源段覆盖率机械校验——每个源段必须被至少一张卡引用（source_cards前缀匹配），
    # 否则拒绝（exit 4）。AI 判定某源段确无概念可抽时，须在 JSON 显式声明 skipped_sources。
    missing_srcs = check_bundle_coverage(concepts, json_path, meta)
    if missing_srcs:
        print("❌ 源段漏抽门禁：以下源段未被任何概念卡引用，commit 拒绝：", file=sys.stderr)
        for s in missing_srcs:
            print(f"   - {s}", file=sys.stderr)
        # v2026-09-20：系统日志单独提示
        syslog_missing = [s for s in missing_srcs if "系统日志" in s]
        if syslog_missing:
            print("   ⛔ 注意：系统日志源段为必选！禁止在skipped_sources中跳过系统日志！", file=sys.stderr)
            print("   系统日志记录的是系统建设实战方法论，是宝贵的可复利资产，必须每天至少提取1个概念。", file=sys.stderr)
        print("   处理：为漏抽源段补抽概念；或确认无概念可抽后，在 concepts_out.json 加 "
              "skipped_sources 显式声明跳过（日记感悟可skipped，系统日志不行）。", file=sys.stderr)
        sys.exit(4)
    existing = existing_concepts()
    existing_hashes = existing_source_hashes()  # v2026-08-10: 幂等查重基底
    written, merged, rejected, deduped = [], [], [], []
    for c in concepts:
        errs = validate(c)
        if errs:
            rejected.append({"concept": c, "errors": errs}); continue
        name = c["concept_name"].strip()
        if name in existing:  # D-F7去重：追加来源不新建
            path = existing[name]
            text = open(path, encoding="utf-8").read()
            for src in c["source_cards"]:
                if src not in text:
                    text = re.sub(r"(source_cards:\n(?:  - [^\n]+\n)*)", rf"\g<1>  - {src}\n", text, count=1)
            open(path, "w").write(text); merged.append(name)
        else:
            # v2026-08-10 根治·双跑重复卡（C-044≡C-047 同source_hash）：source_hash幂等查重
            # 同一来源已落卡(其hash已存在) → 视为重复跳过新建，使commit可重跑不产生冗余卡
            hashes = []
            for s in c["source_cards"]:
                h, _why = source_content_hash(s)
                if h: hashes.append(h)
            if hashes and any(h in existing_hashes for h in hashes):
                deduped.append(name); continue
            cid = f"C-{next_concept_id():03d}"
            # v2026-07-28: 源内容hash(哈希谓词·01§五决策位落地)——不可算时省略字段,lint退mtime有痕兼容
            hashes = []
            for s in c["source_cards"]:
                h, _why = source_content_hash(s)
                if h: hashes.append(f'  - "{s}": {h}\n')
            hash_block = ("source_hash:\n" + "".join(hashes)) if hashes else ""
            card = (f"---\nconcept_id: {cid}\nconcept_name: \"{name}\"\ntype: concept\n"
                    f"definition: \"{c['definition']}（粗粒度摘要·精确语义见source_cards）\"\n"
                    f"source_cards:\n" + "".join(f"  - {s}\n" for s in c["source_cards"]) +
                    hash_block +
                    f"source_owner: {c['source_owner']}\ndomain: \"{c['domain']}\"\n"
                    f"derived_date: {today().isoformat()}\nstatus: active\n---\n")
            open(os.path.join(CONCEPTS_DIR, f"{cid}-{name}.md"), "w").write(card)
            written.append(f"{cid}:{name}")
    if rejected:  # 降级记录不静默丢弃（D-F6③）
        with open(os.path.join(FED, "rejected_pending.json"), "a") as f:
            f.write(json.dumps({"date": today().isoformat(), "items": rejected}, ensure_ascii=False) + "\n")
    append_log("ingest", f"新增{len(written)}概念 合并{len(merged)} 拒收{len(rejected)} 去重{len(deduped)}")
    state = load_state(); state["last_batch_date"] = today().isoformat(); save_state(state)
    if os.path.exists(BUNDLE_FILE): os.remove(BUNDLE_FILE)
    regen_index()
    print(f"COMMITTED: 新增{len(written)} 合并{len(merged)} 拒收{len(rejected)} 去重{len(deduped)}(留待clock-loop呈报)")
    # D-F8每晚管道: 抽取尾部串接碰撞扫描（best-effort·熔断不阻塞入库）
    if written or merged:
        try:
            import subprocess
            r = subprocess.run([sys.executable, os.path.join(FED, "scripts", "collision_scan.py"), "scan"],
                               timeout=600, check=False, capture_output=True, text=True)
            if r.returncode != 0:
                err = (r.stderr or r.stdout or "").strip().splitlines()[-1][:200]
                append_log("scan-fail", f"exit{r.returncode} {err}")
                print(f"⚠️ 碰撞扫描失败(exit {r.returncode})——已留痕 log.md scan-fail，可手动重跑")
        except Exception as e:
            append_log("scan-fail", f"exception {str(e)[:200]}")
            print(f"⚠️ 碰撞扫描异常({e})——已留痕 log.md scan-fail，可手动: python3 scripts/collision_scan.py scan")
    # D-F10轻档: lint挂if块外无条件执行——零新增之夜也必须留跳过痕(01冻结版·哲学审B修正①)
    try:
        import subprocess
        # v2026-08-08: knowledge_lint.py 已改名 kb_concept_lint.py（他窗18脚本批量改名·git mv）——调用方同步新名，防静默断裂
        _lint = os.path.join(FED, "scripts", "kb_concept_lint.py")
        if os.path.exists(_lint):
            subprocess.run([sys.executable, _lint, "--light"], timeout=300, check=False)
    except Exception as e:
        print(f"⚠️ 知识Lint未跑({e})——可手动: python3 scripts/kb_concept_lint.py --light")

def regen_index():
    """D-F11: 总索引=编译产物·每次自动重生成·永不手写"""
    files = glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md"))
    domains = {}
    for p in files:
        t = open(p, encoding="utf-8").read()
        m = re.search(r'domain:\s*"?([^"\n]+)"?', t)
        dom = m.group(1) if m else "未分类"
        domains[dom] = domains.get(dom, 0) + 1
    state = load_state()
    # v2026-08-05: 概念库消费健康度（S9防复发·防只进不出）——统计 pending 候选 + 本周新卡
    pending_n = 0
    if os.path.exists(CANDIDATES_FILE):
        try:
            pending_n = sum(1 for c in json.load(open(CANDIDATES_FILE)).get("candidates", [])
                            if c.get("status") == "pending")
        except Exception:
            pending_n = -1  # 解析失败=不可用
    week_ingest = 0
    if os.path.exists(LOG_FILE):
        try:
            week_ingest = len(re.findall(r'## \[\d{4}-\d{2}-\d{2}\] ingest \| 新增(\d+)概念',
                                         open(LOG_FILE, encoding="utf-8").read()))
        except Exception:
            week_ingest = -1
    lines = [ "---", "title: 知识总索引", "type: auto-generated-index",
              f"generated: {now_str()}", "warning: 本文件由脚本自动生成，手工修改会被覆盖", "---", "",
              "# 🗺️ 知识总索引（编译产物·勿手写）", "",
              "## 三库入口",
              f"- AI学习库: {os.path.join(AILIB_DIR, 'INDEX.md')}",
              f"- 概念卡库: {CONCEPTS_DIR}", "",
              "## 概念层统计", f"- 概念总数: {len(files)}",
              f"- 最近批次: {state.get('last_batch_date')}", "- domain分布:" ]
    lines += [f"  - {k}: {v}" for k, v in sorted(domains.items(), key=lambda x: -x[1])]
    # v2026-08-06: 概念→洞见卡倒排（正查断：打开概念卡看不到被哪些洞见卡收窄）
    # 数据源=AI学习库洞见卡"碰撞来源"字段；兼容 ID格式[C-XXX×C-YYY] 与 概念名格式[名称×名称]
    concept_name_to_id = {}
    for p in files:
        t = open(p, encoding="utf-8").read()
        cid = re.search(r'concept_id:\s*(\S+)', t)
        cname = re.search(r'concept_name:\s*"?([^"\n]+)"?', t)
        if cid and cname:
            concept_name_to_id[cname.group(1).strip()] = cid.group(1)
    reverse_map = {}  # concept_id -> [洞见卡名]
    if os.path.exists(AILIB_DIR):
        for sp in sorted(glob.glob(os.path.join(AILIB_DIR, "*.md"))):
            st = open(sp, encoding="utf-8").read()
            m = re.search(r'碰撞来源:\s*"\[([^"\]]+)\]"', st)
            if not m:
                continue
            scard = os.path.basename(sp).replace(".md", "")
            pair_text = m.group(1)
            for token in re.split(r'\s*×\s*', pair_text):
                token = token.strip()
                if not token:
                    continue
                cid_key = token if token.startswith("C-") else concept_name_to_id.get(token)
                if cid_key:
                    reverse_map.setdefault(cid_key, []).append(scard)
    lines += ["", "## 概念→洞见卡（自动生成·正查断·v2026-08-06）"]
    if reverse_map:
        for cid in sorted(reverse_map):
            lines.append(f"- {cid}: " + ", ".join(sorted(set(reverse_map[cid]))))
    else:
        lines.append("- （暂无倒排数据）")
    lines += ["", "## 概念库消费健康度（自动生成·防只进不出）",
              f"- 累计ingest批次: {week_ingest if week_ingest >= 0 else '不可用'}",
              f"- 当前pending碰撞候选: {pending_n if pending_n >= 0 else '不可用'}",
              "- 判定: " + ("⚠️ pending>50 → 概念库只进不出，建议周报/月报消费一次（学/碰/蒸）"
                           if pending_n > 50 else "🟢 pending≤50 → 消费健康")]
    open(INDEX_FILE, "w").write("\n".join(lines) + "\n")

def cmd_status():
    if not INSTALLED:
        print("状态：未安装（包内暂存态）——完成安装后此命令显示概念库进度")
        return
    state = load_state()
    n = len(glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md")))
    print(f"概念数:{n} | 上次批次:{state.get('last_batch_date')} | 待处理天数:{len(dates_to_process(state))}")

if __name__ == "__main__":
    from _engine_env import ensure_engine_python; ensure_engine_python()  # 有venv用venv·无则系统python
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd in ("prepare", "commit"):
        _require_installed()
    ensure_dirs()  # 端用户版·首次自动建库（幂等·仅安装态）
    if cmd == "prepare": cmd_prepare()
    elif cmd == "commit": cmd_commit(sys.argv[2])
    elif cmd == "status": cmd_status()
    else: print(__doc__)
