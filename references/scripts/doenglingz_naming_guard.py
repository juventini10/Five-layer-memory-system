#!/usr/bin/env python3
r"""命名红线机械校验器——把规格书「全系统机械校验为证」从声明变成可跑的闸。

五条判据，每条反推自 2026-09-02 实锤病灶，不发明规则：

  C1 反身性完整性：「禁止生成或引用 X（拼音）」里的 X 必须是被禁目标名 tongling。
     09-01 批量正名把这句的 X 一并换成 doenglingz → 禁令自我否定；
     更糟的是 `grep -ri tongling 残留=0` 因此把已污染文件判成"清洁"——判据缺一半的假绿。
  C2 清单主键可寻址：常驻清单条目（`- \`file.md\`` 形态）主键位的文件名必须在盘上存在。
     抓"改名后索引未跟"（AGENTS.md 曾写 tongling-core.md 而盘上只有 doenglingz-core.md）。
     ⛔只判主键位：历史实录行与描述性提及（"原名 tongling-core.md"）合法含旧名，
       纳入即误报——判据必须绑定被检对象的结构位置，不是关键字。
  C3 产物逐字性：slices/ 产物必须逐字等于生成器对当前规格书的输出。
     manifest.src_hash 只证明"规格书没变"，不证明"产物==规格书"——本次两件事同时成立。
  C4 声明-实盘对账：文档里写出的规格书 hash（戳记／守护期望值／话术基准）必须等于 manifest.src_hash。
     规格书一改，手填戳记当天集体腐烂：实测同日 10 处过期，其中守护 Skill 的期望值一烂
     就天天假红——声明无人对账时，它比没有声明更危险。
  C5 端点注入区逐字性：各注册端注入区必须逐字等于 core+L6 产物。
     戳记自称"与 slices 逐字一致"，判据就必须能证伪它；只比 hash 戳记等于把 fidelity 交给手填。

用法:
  python3 doenglingz_naming_guard.py              # 扫现状
  python3 doenglingz_naming_guard.py --selfcheck  # 夹具自证：证明它真会报警
退出码: 0 = 全绿；1 = 有红；2 = 校验器自身失效（⛔不得当通过读）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import glob
import importlib.util
import json
import os
import re
import sys
import tempfile

BASE = os.path.expanduser("[记忆共享中心]")
TWIN = os.path.join(BASE, "数字分身")
SLICES = os.path.join(TWIN, "K2切片蒸馏/slices")
GENERATOR = os.path.join(TWIN, "K2切片蒸馏/k2_slice_generator.py")
WATCHER = os.path.join(TWIN, "scripts/doenglingz_slice_watch.py")

# 归档/日志/trace/运行态记忆/备份 = 历史实录，回改等于伪造取证，不纳入校验。
EXCLUDE = re.compile(
    r"(正名留档|/logs/|/traces/|rollout|系统日志|/memory/|\.bak$|__pycache__|/发布包/|/开发库/)"
)

BANNED_NAME = "tongling"  # 被禁目标名，必须原样保留在禁令里
# 清单条目主键位：行首 "- `名字`"，只取第一个 code span
ENTRY = re.compile(r"^- `([^`/]+)`", re.M)

# C1 的三种真实句式（2026-09-02 实测枚举，不是发明）：
#   a) 规格书/各端 core：禁止生成或引用 tongling（拼音）
#   b) 哲学 06 §〇：   不得……引用拼音 `tongling`
#   c) 哲学 06 §〇：   grep -ri tongling   ← 检测命令本身也会被打反
PINYIN_AFTER = re.compile(r"([A-Za-z]+)\s*（拼音）")
PINYIN_BEFORE = re.compile(r"拼音\s*[`'\" ]*([A-Za-z]+)")
GREP_PROBE = re.compile(r"grep\s+-[A-Za-z]+\s+([A-Za-z]+)\b")
# 判据绑定规范段：含"命名红线"的块，或"命名红线"小节下的块；历史段一律排除——
# 历史行（变更记录/勘误）合法引用被禁名描述"当初错成什么"，纳入即误报，且回改=伪造取证。
REDLINE_MARK = re.compile(r"命名红线")
HIST_SECTION = re.compile(r"(变更记录|勘误|事故|历史|版本轨迹)")
# 体裁判据：变更日志类文档整篇是历史实录（合法引用病句原文描述"当初错成什么"），
# 小节标题未必带"变更记录"字样 → 只绑标题会误报（2026-09-02 反扫 6 红全落在 CHANGELOG）。
HIST_FILE = re.compile(r"(CHANGELOG|变更记录|勘误|留档|事故)")

# 真源与跨端总则：红线段的规范正文住在这里。校验器若只查分发件不查真源＝优先级倒置
# （真源被打反时 C3 会把"产物≠派生"的锅甩给产物，维护者照坏真源重跑＝扩散）。
NORM_SOURCES = [
    os.path.join(TWIN, "童灵·人格规格书.md"),
    os.path.join(BASE, "记忆蓝图/04_系统文件设计/数字分身设计哲学/06-跨端适配规范.md"),
    os.path.join(BASE, "记忆蓝图/04_系统文件设计/数字分身设计哲学/03-进度看板.md"),
    os.path.join(TWIN, "K2切片蒸馏/各端切换分发话术.md"),
    os.path.join(BASE, "技能配置/布洛陀-童灵守护/SKILL.md"),
]
MANIFEST = os.path.join(SLICES, "manifest.json")

# C4 声明对账：凡正文以"切片来源 hash / 规格书 hash / src_hash / 应为 X"形式写出 12 位十六进制的，
#    该值必须等于 manifest.src_hash。戳记是手填的→规格书一变即腐烂成假声明，
#    且守护 Skill 里的期望值一烂就天天假红（2026-09-02 实测三处不一致）。
#    绑定＝"声明关键词出现在同一行、且在 token 之前"，不认全文任意 12 位 hex（防 git 短号误报）。
HASH12 = re.compile(r"(?<![0-9a-f])[0-9a-f]{12}(?![0-9a-f])")
STAMP_KEY = re.compile(r"(切片来源|规格书|src_hash|应为)")

# 紧邻日期豁免：现状登记表常内嵌"2026-08-27 重跑生成器对齐规格书 70c9…"式行内实录——
#   那是当时真相，按「历史行不回改」铁律不得为凑绿而改写（否则判据反过来逼人伪造取证）。
#   只在 hash 前 30 字内出现日期时豁免；无日期的现状声明（"切片来源 hash：`xxx`"）照判。
NEAR_DATE = re.compile(r"(?<![\d-])(?:20\d{2}-\d{2}-\d{2}|\d{2}-\d{2})(?![\d-])")

# C2 的查找根：注册端恒驻目录 + 分身脚本目录 + 开发工具
SEARCH_ROOTS = [
    os.path.join(TWIN, "scripts"),
    os.path.join(BASE, "开发工具"),
    os.path.expanduser("~/.qoder-cn/rules"),
    os.path.expanduser("~/.trae-cn/user_rules"),
    SLICES,
]


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def existing_names():
    real = set()
    for root in SEARCH_ROOTS:
        real.update(os.path.basename(f) for f in glob.glob(os.path.join(root, "*")))
    return real


_WATCHER_MOD = None


def watcher():
    """watcher 清单单一来源（缓存）：C1/C2 覆盖面 + C5 校验对象 + 标记常量都从这里取，
    避免"校验器自己维护一份端清单"＝双实现漂移。"""
    global _WATCHER_MOD
    if _WATCHER_MOD is None:
        _WATCHER_MOD = _load_module(WATCHER, "dz_watch")
        if not getattr(_WATCHER_MOD, "HOMES", None):
            raise RuntimeError("watcher HOMES 为空——分发清单失效，校验范围不可信")
    return _WATCHER_MOD


def targets():
    """校验对象 = 分发目标（从 watcher 导入·零复制=零双实现漂移）+ 本端索引 + 规范源 + 切片产物。"""
    try:
        w = watcher()
        paths = list(getattr(w, "HOMES", [])) + list(getattr(w, "MARKED_HOMES", []))
    except Exception as e:
        raise RuntimeError("watcher 清单不可读（C1/C2/C5 覆盖面会失准）: %s" % e)
    paths.append(os.path.expanduser("~/.qoder-cn/AGENTS.md"))
    paths.extend(NORM_SOURCES)
    paths.extend(glob.glob(os.path.join(SLICES, "*.md")))
    return [p for p in paths if os.path.exists(p) and not EXCLUDE.search(p)]


def _scan_sections(path):
    """按 markdown 小节标题切正文 → [(小节名, [(行号, 原文)])]。
    frontmatter 整块跳过（元数据·summary 行常引用旧值做变更说明）；
    变更日志类文档整篇是历史实录 → 返回空。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if HIST_FILE.search(os.path.basename(path)):
        return []
    offset = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                offset = j + 1
                lines = [""] * offset + lines[offset:]
                break
    blocks, section, block = [], "", []

    def flush():
        if block:
            blocks.append((section, list(block)))
        del block[:]

    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s:
            flush()
        elif s.startswith("#"):
            flush()
            section = s.lstrip("#").strip()
        else:
            block.append((i, raw))
    flush()
    return blocks


def normative_lines(path):
    """C1 作用域：块内含"命名红线"标记，或处于该标记小节下的块；历史小节整段排除。"""
    res = []
    for section, block in _scan_sections(path):
        if section and HIST_SECTION.search(section):
            continue
        if REDLINE_MARK.search(section) or any(REDLINE_MARK.search(t) for _, t in block):
            res.extend(block)
    return res


def live_lines(path):
    """C4 作用域：全部规范正文行（历史小节／frontmatter／历史体裁已排除）。"""
    res = []
    for section, block in _scan_sections(path):
        if section and HIST_SECTION.search(section):
            continue
        res.extend(block)
    return res


def check_reflexivity(paths):
    """C1：规范段里"被禁目标名"的位置必须填 tongling（三句式全覆盖，历史段不判）。"""
    reds = []
    for p in paths:
        try:
            scope = normative_lines(p)
        except Exception as e:
            reds.append("C1/FAIL %s 读取失败 %s" % (p, e))
            continue
        for lineno, text in scope:
            for pat, tag in ((PINYIN_AFTER, "拼音后置"),
                             (PINYIN_BEFORE, "拼音前置"),
                             (GREP_PROBE, "检测命令")):
                for m in pat.finditer(text):
                    got = m.group(1)
                    if got.lower() != BANNED_NAME:
                        reds.append("C1 %s:%d %s被打反——被禁名位置填了 '%s'，应为 '%s'（禁令自我否定）"
                                    % (p, lineno, tag, got, BANNED_NAME))
    return reds


def check_addressability(paths):
    """C2：常驻清单主键位的文件名必须可寻址。"""
    real = existing_names()
    reds = []
    for p in paths:
        text = open(p, encoding="utf-8").read()
        for m in ENTRY.finditer(text):
            name = m.group(1)
            if name in real:
                continue
            reds.append("C2 %s:%d 清单主键指向不存在的文件 %s（改名后索引未跟？）"
                        % (p, text[: m.start()].count("\n") + 1, name))
    return reds


def check_derivation_core(pairs, slices_dir):
    """C3 核心：pairs=[(产物文件名, 期望文本)]，逐个与 slices_dir 下盘上内容逐字比对。"""
    reds = []
    for fname, expect in pairs:
        expect = expect.strip() if expect else ""
        path = os.path.join(slices_dir, fname)
        if not expect:
            reds.append("C3/FAIL %s 生成器输出为空（抽取正则失效·换代信号）" % fname)
            continue
        if not os.path.exists(path):
            reds.append("C3 %s 产物缺失" % path)
            continue
        disk = open(path, encoding="utf-8").read().strip()
        if disk != expect:
            dl, el = disk.split("\n"), expect.split("\n")
            n = sum(1 for a, b in zip(dl, el) if a != b) + abs(len(dl) - len(el))
            reds.append("C3 %s 产物≠规格书派生（%d 行差异·src_hash 一致也判红）" % (path, n))
    return reds


def check_derivation():
    """C3 入口：从当前规格书 + 生成器算出期望文本，再比对盘上产物。"""
    try:
        g = _load_module(GENERATOR, "dz_gen")
    except Exception as e:
        return ["C3/FAIL 生成器不可加载: %s" % e]
    spec_path = os.path.join(TWIN, "童灵·人格规格书.md")
    if not os.path.exists(spec_path):
        return ["C3/FAIL 规格书不存在: %s" % spec_path]
    spec = open(spec_path, encoding="utf-8").read()
    pairs = [("core_slice.md", g.extract_core(spec)),
             ("L6_反向约束.md", g.extract_layer(spec, "L6"))]
    return check_derivation_core(pairs, SLICES)


def check_stamps(paths, manifest_hash):
    """C4：文档里声明的规格书 hash 必须等于 manifest.src_hash。
    戳记手填＝必腐烂；守护 Skill 的期望值腐烂＝天天假红。声明与实盘脱钩即红。
    例外：hash 前 30 字内带日期＝行内实录（当时真相），按历史行不回改铁律不判。"""
    reds = []
    for p in paths:
        try:
            scope = live_lines(p)
        except Exception as e:
            reds.append("C4/FAIL %s 读取失败 %s" % (p, e))
            continue
        for lineno, text in scope:
            for m in HASH12.finditer(text):
                if not STAMP_KEY.search(text[:m.start()]):
                    continue  # 无声明语境的 12 位 hex（git 短号等）不判
                if NEAR_DATE.search(text[max(0, m.start() - 30):m.start()]):
                    continue  # 带日期的行内实录不判
                if m.group(0) != manifest_hash:
                    reds.append("C4 %s:%d 声明-实盘脱钩：文中 hash=%s ≠ manifest=%s"
                                "（分发断链／手改戳记／守护期望值过期）"
                                % (p, lineno, m.group(0), manifest_hash))
    return reds


def _strip_comment_lines(seg):
    """剔除 HTML 注释标记行 + 空行后返回内容行。
    ⚠ 空行一并剔除：标记对脚手架（core 结束标记／L6 开始标记）本身占空行，保留会比较布局而非内容
      （2026-09-02 实测 ZCode 端 16 行"差异"全为空行位移、内容行逐字相同）。
      判据仍对每个内容行逐字严格——"逐字一致"判的是文字，不是段落间距。"""
    return "\n".join(l for l in seg.split("\n")
                     if l.strip() and not l.strip().startswith("<!--")).strip()


def check_fidelity(core, l6, homes, marked_homes):
    """C5：注册端注入区必须逐字等于 core+L6 产物。戳记自称"逐字一致"，判据就得能证伪它。"""
    expect = _strip_comment_lines(core.strip() + "\n\n" + l6.strip())
    first_line = core.split("\n", 1)[0]
    core_start = watcher().CORE_START
    l6_end = watcher().L6_END
    reds = []
    for p in homes:
        if not os.path.exists(p):
            reds.append("C5 %s 恒驻核缺失（注册端无落点文件·分发未覆盖或路径漂移）" % p)
            continue
        body = open(p, encoding="utf-8").read().split("---\n", 2)
        body = body[2] if len(body) >= 3 else open(p, encoding="utf-8").read()
        idx = body.find(first_line)
        if idx < 0:
            reds.append("C5 %s 注入区不可定位（找不到切片首行·格式 A 约定被破坏）" % p)
            continue
        got = _strip_comment_lines(body[idx:])
        if got != expect:
            reds.append("C5 %s 注入区≠切片产物（%s 行差异·规格书→端点断链）"
                        % (p, _diffcount(got, expect)))
    for p in marked_homes:
        if not os.path.exists(p):
            reds.append("C5 %s 标记对恒驻文件缺失" % p)
            continue
        text = open(p, encoding="utf-8").read()
        i1, i3 = text.find(core_start), text.find(l6_end)
        if not (0 <= i1 < i3):
            reds.append("C5 %s 标记结构不可解析（格式 B 约定被破坏·无从校验逐字性）" % p)
            continue
        got = _strip_comment_lines(text[text.find("\n", i1) + 1:i3])
        if got != expect:
            reds.append("C5 %s 注入区≠切片产物（%s 行差异·规格书→端点断链）"
                        % (p, _diffcount(got, expect)))
    return reds


def _diffcount(a, b):
    al, bl = a.split("\n"), b.split("\n")
    return sum(1 for x, y in zip(al, bl) if x != y) + abs(len(al) - len(bl))


def run_all():
    paths = targets()
    try:
        manifest_hash = json.load(open(MANIFEST, encoding="utf-8")).get("src_hash", "")
    except Exception as e:
        raise RuntimeError("manifest 不可读（C4 无从对账·判据缺真值）: %s" % e)
    if not manifest_hash:
        raise RuntimeError("manifest.src_hash 为空——C4 判据失去真值基准")
    core_p, l6_p = os.path.join(SLICES, "core_slice.md"), os.path.join(SLICES, "L6_反向约束.md")
    if not (os.path.exists(core_p) and os.path.exists(l6_p)):
        raise RuntimeError("切片产物缺失——C5 判据失去比对基准")
    core = open(core_p, encoding="utf-8").read()
    l6 = open(l6_p, encoding="utf-8").read()
    w = watcher()
    return paths, (check_reflexivity(paths) + check_addressability(paths) + check_derivation()
                   + check_stamps(paths, manifest_hash)
                   + check_fidelity(core, l6, w.HOMES, w.MARKED_HOMES))


def selfcheck():
    """夹具自证：每条判据各一个坏样本 + 一个好样本，证明会报警也知放行。"""
    results = []
    bad_redline = "> 📌 **命名红线**：任何端一律使用 doenglingz 前缀；禁止生成或引用 doenglingz（拼音）任一变体。\n"
    good_redline = bad_redline.replace("引用 doenglingz（拼音）", "引用 tongling（拼音）")
    with tempfile.TemporaryDirectory() as d:
        f_bad = os.path.join(d, "bad.md")
        f_good = os.path.join(d, "good.md")
        open(f_bad, "w", encoding="utf-8").write(bad_redline)
        open(f_good, "w", encoding="utf-8").write(good_redline)
        results.append(("C1 会报警", len(check_reflexivity([f_bad])) == 1))
        results.append(("C1 不误报", len(check_reflexivity([f_good])) == 0))

        # 新增句式 + 段绑定：前置式/grep 式各判各的（同文件混排会让计数互相污染）
        f_pinyin = os.path.join(d, "forms_pinyin.md")
        open(f_pinyin, "w", encoding="utf-8").write(
            "## 〇、命名红线（全端刚性）\n\n- 任何端不得引用拼音 `doenglingz`（及变体）\n")
        results.append(("C1 拼音前置式会报警", len(check_reflexivity([f_pinyin])) == 1))
        f_grep = os.path.join(d, "forms_grep.md")
        open(f_grep, "w", encoding="utf-8").write(
            "## 〇、命名红线（全端刚性）\n\n- 机械校验：`grep -ri doenglingz` 命中活文件即触碰\n")
        results.append(("C1 grep 检测命令会报警", len(check_reflexivity([f_grep])) == 1))
        f_hist_doc = os.path.join(d, "histdoc.md")
        open(f_hist_doc, "w", encoding="utf-8").write(
            "## 〇、命名红线\n\n- 禁止生成或引用 tongling（拼音）任一变体\n\n"
            "## 变更记录\n\n- v1.34：命名红线段曾被误毁为\"引用拼音 doenglingz\"，已改回\n")
        results.append(("C1 历史段不误报", len(check_reflexivity([f_hist_doc])) == 0))
        f_fm = os.path.join(d, "frontmatter.md")
        open(f_fm, "w", encoding="utf-8").write(
            "---\nsummary: 命名红线段矫正（`grep -ri doenglingz`→`grep -ri tongling`）\n---\n\n"
            "## 〇、命名红线\n\n- 禁止生成或引用 tongling（拼音）任一变体\n")
        results.append(("C1 frontmatter 不误报", len(check_reflexivity([f_fm])) == 0))
        # 体裁判据：同名内容，CHANGELOG.md 不判、规范文档判（证明短路来自体裁而非判据失效）
        corrupt_norm = "## 〇、命名红线\n\n- 禁止生成或引用 doenglingz（拼音）任一变体\n"
        for nm in ("CHANGELOG.md", "06-跨端适配规范.md"):
            fp = os.path.join(d, nm)
            open(fp, "w", encoding="utf-8").write(corrupt_norm)
            n = len(check_reflexivity([fp]))
            if nm.startswith("CHANGELOG"):
                results.append(("C1 历史体裁不判", n == 0))
            else:
                results.append(("C1 同内容入规范文档仍判", n == 1))
        results.append(("C1 真源规范行可切出", len(normative_lines(NORM_SOURCES[0])) > 0))

        f_entry = os.path.join(d, "entry.md")
        open(f_entry, "w", encoding="utf-8").write("- `tongling_ghost.py` — 不存在的条目\n")
        results.append(("C2 会报警", len(check_addressability([f_entry])) == 1))
        f_hist = os.path.join(d, "hist.md")
        open(f_hist, "w", encoding="utf-8").write(
            "| 2026-08-30 | 首次入库 rules/tongling-core.md | 取证 |\n"
            "- `doenglingz-core.md` — 正文提到 原名 tongling-core.md 已更名\n")
        results.append(("C2 历史行不误报", len(check_addressability([f_hist])) == 0))

    # C3 夹具：临时目录里造"产物≠派生"与"产物==派生"两份，验证双向判定
    with tempfile.TemporaryDirectory() as d:
        expect = "行一\n行二\n行三"
        drift = os.path.join(d, "core_slice.md")
        open(drift, "w", encoding="utf-8").write("行一\n被 sed 改过的一行\n行三")
        results.append(("C3 会报警（产物漂移）",
                        len(check_derivation_core([("core_slice.md", expect)], d)) == 1))
        open(drift, "w", encoding="utf-8").write(expect)
        results.append(("C3 不误报（产物一致）",
                        len(check_derivation_core([("core_slice.md", expect)], d)) == 0))
        results.append(("C3 生成器空输出判 FAIL",
                        any("FAIL" in r for r in check_derivation_core([("core_slice.md", "")], d))))

    # C4 夹具：声明的 hash 必须与 manifest 相等；无声明语境／历史实录不判
    with tempfile.TemporaryDirectory() as d:
        f_hash = os.path.join(d, "norm_hash.md")
        open(f_hash, "w", encoding="utf-8").write(
            "## 2.2 各端适配器清单\n\n- 恒驻核 切片来源 hash `aaaa1111bbbb`（与 slices 逐字一致）\n")
        results.append(("C4 声明相等不误报", len(check_stamps([f_hash], "aaaa1111bbbb")) == 0))
        results.append(("C4 声明过期会报警", len(check_stamps([f_hash], "ffff9999eeee")) == 1))
        f_ctx = os.path.join(d, "commit_ref.md")
        open(f_ctx, "w", encoding="utf-8").write("## 现状\n\n- 关联提交 aaaaa1111111 已合入\n")
        results.append(("C4 无声明语境的 12hex 不判", len(check_stamps([f_ctx], "ffff9999eeee")) == 0))
        f_hush = os.path.join(d, "CHANGELOG.md")
        open(f_hush, "w", encoding="utf-8").write("- v1.35（2026-09-01）：当时真源 hash = `1c6f316b8f75`\n")
        results.append(("C4 历史戳记不判", len(check_stamps([f_hush], "ffff9999eeee")) == 0))
        f_dated = os.path.join(d, "registry.md")
        open(f_dated, "w", encoding="utf-8").write(
            "## 2.2 各端适配器清单\n\n"
            "- Trae：2026-08-27 重跑生成器对齐规格书 70c917662765（当时实录）\n"
            "- Qoder CN：规格书 hash `70c917662765`（现状声明）\n")
        results.append(("C4 带日期的行内实录不判",
                        len(check_stamps([f_dated], "ffff9999eeee")) == 1))

    # C5 夹具：格式 A／格式 B 各造一份真端文件，再手改一行验证会报警
    with tempfile.TemporaryDirectory() as d:
        core = "# 童灵 · K2 恒驻注入\n\n内容行A\n内容行B\n"
        l6 = "## L6 · 反向约束层\n\n内容行C\n"
        home_a = os.path.join(d, "coreA.md")
        open(home_a, "w", encoding="utf-8").write(
            "---\nalwaysApply: true\n---\n\n> 定位块（保留）\n\n" + core + "\n" + l6)
        results.append(("C5 格式A逐字一致不误报",
                        len(check_fidelity(core, l6, [home_a], [])) == 0))
        hand = os.path.join(d, "coreA_hand.md")
        open(hand, "w", encoding="utf-8").write(
            open(home_a, encoding="utf-8").read().replace("内容行B", "内容行B（端内手改）"))
        results.append(("C5 端内手改会报警", len(check_fidelity(core, l6, [hand], [])) == 1))
        w = watcher()
        marked = os.path.join(d, "marked.md")
        open(marked, "w", encoding="utf-8").write(
            "前文\n%s（生成器产物·逐字嵌入·禁手抄） -->\n\n%s\n\n%s\n\n%s（生成器产物） -->\n\n%s\n\n%s\n后文\n"
            % (w.CORE_START, core.strip(), w.CORE_END, w.L6_START, l6.strip(), w.L6_END))
        results.append(("C5 格式B标记对不误报", len(check_fidelity(core, l6, [], [marked])) == 0))
        results.append(("C5 注册端缺文件会报警",
                        len(check_fidelity(core, l6, [os.path.join(d, "ghost.md")], [])) == 1))

    ok = 0
    for label, passed in results:
        print("  %s %s" % ("✅" if passed else "🔴", label))
        ok += 1 if passed else 0
    print("selfcheck %d/%d" % (ok, len(results)))
    return 0 if ok == len(results) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selfcheck", action="store_true")
    args = ap.parse_args()

    if args.selfcheck:
        return selfcheck()

    try:
        paths, reds = run_all()
    except Exception as e:
        print(json.dumps({"status": "validator_error", "detail": str(e)}, ensure_ascii=False))
        return 2

    if args.json:
        print(json.dumps({"status": "green" if not reds else "red",
                          "scanned": len(paths), "red": reds}, ensure_ascii=False, indent=2))
    else:
        for p in paths:
            print("  · %s" % p)
        for r in reds:
            print("🔴 %s" % r)
        print("命名红线校验 | 活文件 %d 份 | %s"
              % (len(paths), "全绿 ✅" if not reds else "%d 红 🔴" % len(reds)))
    return 0 if not reds else 1


if __name__ == "__main__":
    sys.exit(main())
