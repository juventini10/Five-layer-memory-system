#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-sync-guard v1.4.0 —— 技能与系统说明(README)同步守卫（守备链版）
# v1.4.0 (2026-10-01 童灵愿景轮): 新增 lint_constitution 子命令——将《00-宪法愿景.md》五原则
#   （宪法/愿景/唯一性/中立/命名）落地为可机检规则；全部路径复用模块级 SKILL_ROOT/CORE_FILES
#   （已随副本参数化）→ 零新增路径字面量 → 4 副本本段代码逐字节一致。
# v1.3.3 (2026-09-14 童灵根治轮): 核心文件路径自检——CORE_FILES 内 3 条路径已随目录重组漂移失效
#   （三大思维白皮书.md 实为 01_思维方法论/、五层记忆系统.md 实为 00_系统总览/、00-soul.md 实为 共享核心/core-soul.md），
#   extract_core_version 对缺失路径返回 None → 调用处静默 continue → 该行**从未被检查**却报「0 漂移」的假绿灯
#   （与残差#110「机检绿灯只在其文件视野内为真」同族）。修：路径对齐真源 + 新增 collect_missing_core_paths()
#   自检并入 audit 报告与 verify/sync 硬拦集合——路径失效=红灯，不再静默。
# v1.3.2 (2026-09-10 童灵根治轮): §四注册表真相源路径「过捕获」根治——旧 findall 字符类吞掉反引号/全角斜杠/中点，
#   在中文散文里把路径尾巴一并吃进（9 处幻影失效）；改 _REG_PATH_RE 显式排除 + registry_path_candidates() 去尾缀
#   /glob→前缀目录，并补 registry_path_selftest() 7 例夹具（含 3 负例）接入 `self-test` 子命令。自测 7/7 全绿，
#   audit 恢复「✅ 守卫注册表：真相源路径全部有效」。（同病根同轮另一处见 guard_doc_consistency 段内配对四律）
# v1.3.1 (2026-08-09 你拍板): README 新增 §4.3 个人专用技能节（6 个皮叔个人用），§4.1 删 chrold/scriyore 与 manifest 对齐；
#   §4.3 纳入软提示排除（第2列目录名匹配）。实测：§4.1↔manifest 0 漂移，软提示仅剩 impeccable。
# v1.3.0 (2026-08-09 皮叔定案+第一性原理深化): 同步真相源=mirror-manifest.json；§4.1↔manifest 双向硬一致性
#   （漏登记/多登记报漂移·报告不改写·处置需人工）；技能配置未分类→软提示（§4.1∪§4.2∪manifest 外）。
#   负例四用例（2026-08-09）：多登记 chrold/scriyore 实测 / 未分类 impeccable 提示不报 / 漏登记构造 manifest / 损坏降级。
零第三方依赖（仅 python 标准库：os/re/sys/shutil/datetime）。

子命令:
  audit   只读扫描，输出【漂移报告】（不改动任何文件）
  sync    全量同步：pre快照 → apply回写 → verify校验
  verify  仅校验当前高频硬同步区是否 0 漂移（供 git hook / CI 调用）
  lint_norm  规范词汇治理：扫描对外 spec/skill 是否携带 RFC 2119 等价映射（详见指令编写规范 §1.1.1）
  lint_format  文件格式规范：扫描 03_开发规范 + references 的 frontmatter 是否通过 §3.5 结构合规（详见文件格式规范 v2.0.0）

设计原则（见 自定义层/待完成工作/Skill开发/技能同步脚本_S级方案.md）:
  - 单一事实源(SSOT): 版本号权威在 SKILL.md frontmatter / 核心文件字段
  - 机制兜底: pre 步骤把 README 改前版本快照到记忆琥珀
  - 全量扫描: 读所有 skill + 核心文件，不依赖人记得"哪改了"
  - 幂等: 连跑两次结果一致（changed==0 时不 bump 自身版本、不写文件）
  - 一次性整完: 一次覆盖 README 所有相关章节

同步矩阵落点:
  [高频硬同步·自动patch·决定0漂移判据]
    1. §4.1 核心技能版本列   <- 技能配置/*/SKILL.md 的 version:
    2. §二  核心文件版本列   <- CORE/白皮书/铁律/详解/摘要/SHADOW/五层/00-soul/SOUL 的版本字段
    3. §6.2 记忆琥珀计数     <- ls 记忆琥珀/技能升级备份/ | wc -l
    4. README 自身版本       <- 头部「本README版本」(有改动才升补丁号)
  [低频软同步·只读审计+提示·不自动改写]
    5. §一 本地偏移条数      <- 变更日志.md 真实条目(约数，人工确认)
    6. §二 变更日志.md 条数   <- 同上
    7. §4.1 一句话功能/联动   <- 需语义判断，人工
    8. §4.2 辅助技能版本      <- 市场skill，best-effort
    9. §4.3 联动关系图        <- 人工
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
import sys
import shutil
import json
import datetime

HOME = os.path.expanduser("~")
SKILL_ROOT = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置")
README = os.path.join(os.path.expanduser("[记忆共享中心]"), "README.md")
AMBER = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆琥珀", "技能升级备份")
SYNC_BACKUP = os.path.join(AMBER, "sync-backups")
CHANGELOG = os.path.join(os.path.expanduser("[记忆共享中心]"), "变更日志.md")
# v1.3.0 新增：同步真相源 = mirror-manifest.json（安装包清单），README §4.1 是派生投影
# 守备链（皮叔 2026-08-08 定案 + 2026-08-09 第一性原理深化）：
#   硬一致性：§4.1 ↔ manifest 双向报漂移（README 是 manifest 的投影，必须一致）
#   软提示：技能配置未分类 Skill → 提示登记/标个人专用（不进漂移报告）
MANIFEST = os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "buluotuo-release-sync", "mirror-manifest.json")

# 核心文件清单: (README §二 锚点关键字 -> 文件路径)
# 锚点关键字用于唯一定位 README 表格行；路径用于提取权威版本
CORE_FILES = [
    ("核心层/CORE.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "核心层", "CORE.md")),
    ("三大思维白皮书.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "01_思维方法论", "三大思维白皮书.md")),
    ("用户基本规则-铁律版.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则", "用户基本规则-铁律版.md")),
    ("用户基本规则-详解存档版.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则", "用户基本规则-详解存档版.md")),
    ("用户基本规则-摘要版.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则", "用户基本规则-摘要版.md")),
    ("SHADOW.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "潜意识层", "SHADOW.md")),
    ("五层记忆系统.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "00_系统总览", "五层记忆系统.md")),
    ("记忆规则/共享核心/core-soul.md", os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆规则", "共享核心", "core-soul.md")),
    ("workbuddy/SOUL.md", os.path.join(HOME, ".workbuddy", "SOUL.md")),
]

VER_RE = re.compile(r"v?(\d+\.\d+(?:\.\d+)?)")


def collect_missing_core_paths():
    """核心文件路径有效性自检（v1.3.3 新增 · 2026-09-14 童灵根治轮）。

    为什么必须有：extract_core_version 对不存在的路径返回 None，调用处
    `if not actual: continue` 静默跳过——**路径失效的那一行根本不被检查**，
    而 audit 照样打印「0 漂移」= 有洞的绿灯（与残差#110「机检绿灯只在其
    文件视野内为真」同族）。有痕不静默：失效路径必须显形并进硬拦集合。
    """
    return [(anchor, os.path.relpath(path, HOME))
            for anchor, path in CORE_FILES if not os.path.isfile(path)]


# ---------- 权威事实源提取 ----------

def extract_skill_version(skill_dir):
    """从 SKILL.md frontmatter 提取 version:（仅搜 --- 块内首个）。"""
    p = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(p):
        return None
    try:
        lines = open(p, encoding="utf-8").read().split("\n")
    except Exception:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            break
        m = re.match(r'version:\s*["\']?([0-9][\w.]*)\s*["\']?', lines[i])
        if m:
            return m.group(1)
    return None


def extract_core_version(path):
    """从核心文件提取版本号（优先头部"版本/version"词后，容忍 **： 等符号）。"""
    if not os.path.isfile(path):
        return None
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return None
    head = "\n".join(text.split("\n")[:200])
    m = re.search(r"(?:版本|version).{0,10}?v?(\d+\.\d+(?:\.\d+)?)", head, re.I)
    if m:
        return m.group(1)
    m = re.search(r"v(\d+\.\d+(?:\.\d+)?)", head)
    return m.group(1) if m else None


def collect_actual():
    skills = {}
    if os.path.isdir(SKILL_ROOT):
        for d in sorted(os.listdir(SKILL_ROOT)):
            sd = os.path.join(SKILL_ROOT, d)
            if os.path.isdir(sd):
                v = extract_skill_version(sd)
                if v:
                    skills[d] = v
    cores = {}
    for anchor, path in CORE_FILES:
        v = extract_core_version(path)
        if v:
            cores[anchor] = v
    return skills, cores


def extract_references_versions(skill_dir):
    """扫描 references/ 下带 source_skill/source 字段的固化引用文件。
    返回 [(ref_file_name, source_name, source_path, ref_version), ...]"""
    refs_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(refs_dir):
        return []
    results = []
    for f in sorted(os.listdir(refs_dir)):
        if not f.endswith(".md"):
            continue
        p = os.path.join(refs_dir, f)
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        head = "\n".join(text.split("\n")[:15])
        # 跳过非固化引用文件（无 source_skill/source 字段）
        if "source_skill:" not in head and "source:" not in head:
            continue
        # 提取 version
        m_ver = re.search(r'^version:\s*["\']?([0-9][\w.]*)["\']?', text, re.M)
        if not m_ver:
            continue
        ref_ver = m_ver.group(1)
        # 提取 source_skill 或 source
        m_src = re.search(r'^source_skill:\s*(.+)$', text, re.M)
        source_name = m_src.group(1).strip() if m_src else None
        if not source_name:
            m_src2 = re.search(r'^source:\s*(.+)$', text, re.M)
            source_name = m_src2.group(1).strip() if m_src2 else None
        if not source_name:
            continue
        # source_path 字段：固化文件自声明的源路径（最权威解析依据）
        m_sp = re.search(r'^source_path:\s*(.+)$', text, re.M)
        source_path = m_sp.group(1).strip() if m_sp else None
        results.append((f, source_name, ref_ver, source_path))
    return results


def collect_references_drift():
    """扫描所有 Skill 的 references/ 固化引用版本 vs 源头版本。
    返回 [(skill_name, ref_file, source_name, ref_ver, source_ver), ...]"""
    drifts = []
    if not os.path.isdir(SKILL_ROOT):
        return drifts
    for d in sorted(os.listdir(SKILL_ROOT)):
        sd = os.path.join(SKILL_ROOT, d)
        if not os.path.isdir(sd):
            continue
        refs = extract_references_versions(sd)
        if not refs:
            continue
        for ref_file, source_name, ref_ver, source_path in refs:
            # URL外部源（如OWASP官网）无本地文件可比对，属合法固化，跳过校验
            if any(str(x).startswith(("http://", "https://")) for x in (source_name, source_path) if x):
                continue
            source_ver = None
            # ① 优先：固化文件自声明的 source_path 直读（覆盖规范/任意路径源，不依赖硬编码fallback）
            if source_path:
                sp = os.path.expanduser(source_path.strip("`\'\""))
                if os.path.isfile(sp):
                    source_ver = extract_core_version(sp)
            # ② 兜底：技能配置/ 下同名 Skill
            if not source_ver:
                source_dir = os.path.join(SKILL_ROOT, source_name)
                source_ver = extract_skill_version(source_dir)
            # ③ 兜底：记忆蓝图/03_开发规范/ 下同名规范（含子文件夹形态）
            if not source_ver:
                spec_root = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "03_开发规范")
                for cand in (os.path.join(spec_root, f"{source_name}.md"),
                             os.path.join(spec_root, source_name, f"{source_name}.md")):
                    if os.path.isfile(cand):
                        source_ver = extract_core_version(cand)
                        break
            if not source_ver:
                # 有痕跳过≠静默跳过：源不可解析必须显形，否则漂移检查=假绿灯
                drifts.append((d, ref_file, source_name, ref_ver, "⚠️源不可解析"))
            elif _norm_ver(ref_ver) != _norm_ver(source_ver):
                drifts.append((d, ref_file, source_name, ref_ver, source_ver))
    return drifts


def _norm_ver(v):
    """版本归一化：去v/V前缀再比对，防 v4.5 vs 4.5 误报"""
    return str(v).strip().lstrip("vV")


# ── 守卫注册表扫描（守卫编写规范§五·2026-07-26） ────────────────
GUARD_REGISTRY = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "04_系统文件设计", "布洛陀脚本架构设计哲学", "守卫编写规范.md")


# 真相源格路径提取（2026-09-10 童灵根治轮·9 条假阳根治）
# 旧式 `~/[^\s+()（）]+` 的字符类**未排除分隔符**——markdown 反引号、全角斜杠、中点、顿号
# 被一并吞进路径（`~/bin/git`` 尾随反引号、`~/.git`／`~/.qoder-cn/.git`·说明 整段变路径），
# 9 条候选**恒不存在** = 9 条假阳。病根与 guard_doc_consistency §二 配对同源：
# **匹配器过捕获 → 假阳 → 告警疲劳 → 真错误混在噪音里漏网**（2026-09-10 手抄错的
# twin_changelog_guard 真相源正是被这堆噪音掩盖而漏网·见 守卫编写规范 §3.0·8 元教训）。
_REG_PATH_RE = re.compile(r"(?:~/|\[记忆共享中心\]/)[^\s`+()（）／·，。、；;：:]+")
# 2026-09-20 v1.7.1：占位符形态 [记忆共享中心]/xxx 与 ~/xxx 同权提取，候选归一 ~/（存在性判定时
#   expanduser 展开）——发布侧参数化后注册表行不再被静默漏检（只认 ~/ = 占位符行恒不检查=假绿）
_REG_PATH_TAIL = "。，,.、；;：:`"


def registry_path_candidates(truth_src):
    """从注册表「真相源」格提取候选路径 —— 返回 [(判定用路径, 原文), ...]。

    · 裸路径，引用符/分隔符尾已剥离；
    · glob 形态（如 `logs/runs/*/*.log`）取通配符**之前**的目录部分做存在性判定；
    · 纯 `~` 丢弃（不是路径）。
    """
    out = []
    for raw in _REG_PATH_RE.findall(truth_src):
        p = raw.rstrip(_REG_PATH_TAIL)
        if "*" in p:
            p = p.split("*")[0].rstrip("/")
        if not p or p == "~":
            continue
        if p.startswith(os.path.expanduser("~/")):
            p = "~/" + p[len(os.path.expanduser("~/")):]
        out.append((p, raw))
    return out


def collect_guard_registry_issues():
    """扫描守卫注册表：真相源列的 ~/ 路径必须真实存在。
    返回 [(守卫名, 问题), ...]；注册表缺失/不可解析也入列（有痕跳过≠静默跳过）。"""
    issues = []
    if not os.path.isfile(GUARD_REGISTRY):
        return [("注册表", "守卫编写规范.md 不存在: " + GUARD_REGISTRY)]
    txt = open(GUARD_REGISTRY, encoding="utf-8").read()
    m = re.search(r"<!-- STRIP_START:守卫注册表[^>]*-->(.*?)<!-- STRIP_END:守卫注册表[^>]*-->", txt, re.S)
    if not m:
        return [("注册表", "注册表标记区不可解析（STRIP标记缺失）")]
    rows = [l for l in m.group(1).splitlines() if l.strip().startswith("|") and "---" not in l]
    if len(rows) <= 1:
        return []  # 仅表头=空表（发布包侧属正常，不报）
    for row in rows[1:]:
        cols = [c.strip() for c in row.split("|")]
        if len(cols) < 6:
            continue
        guard_name, truth_src = cols[1], cols[4]
        for path_str, _raw in registry_path_candidates(truth_src):
            if not os.path.exists(os.path.expanduser(path_str)):
                issues.append((guard_name, f"真相源路径失效: {path_str}"))
    return issues


def registry_path_selftest():
    """注册表路径提取夹具（守卫编写规范 §3.0·5 自测纪律·2026-09-10 童灵根治轮）。"""
    cases = [
        ("T1 反引号包裹（单路径·git_commit_safe 档）", "`~/bin/git`", ["~/bin/git"]),
        ("T2 全角斜杠并列两条且中点尾随说明（git_commit_safe 档）",
         "`[记忆共享中心]/.git`／`~/.qoder-cn/.git`·家目录非单仓库故逐文件向上找",
         ["~/.git", "~/.qoder-cn/.git"]),  # 占位符输入→候选归一 ~/ 输出（2026-09-20 v1.7.1）
        ("T3 中点尾随说明（doenglingz_slice_watch 档）",
         "`~/.qoder-cn/rules/doenglingz-core.md`·他端入驻即加行",
         ["~/.qoder-cn/rules/doenglingz-core.md"]),
        ("T4 glob 取通配符前缀目录（qodercn logs 档）",
         "`~/.qoder-cn/logs/runs/*/*.log`", ["~/.qoder-cn/logs/runs"]),
        ("T5 句读尾随剥离", os.path.expanduser("~/foo.md。"), [os.path.expanduser("~/foo.md")]),
        ("T6 一格多路径（+ 分隔·负例不变形）", "~/a/b.py + ~/c/d.sh", ["~/a/b.py", "~/c/d.sh"]),
        ("T7 纯波浪号丢弃", "`~`", []),
    ]
    ok = 0
    for title, src, want in cases:
        got = [p for p, _ in registry_path_candidates(src)]
        good = (got == want)
        ok += bool(good)
        print("  %s %s" % ("✅" if good else "❌", title))
        if not good:
            print("       期望 %s" % want)
            print("       实得 %s" % got)
    print("自测 %d/%d %s" % (ok, len(cases), "全绿" if ok == len(cases) else "有红"))
    return 0 if ok == len(cases) else 1


# ── 规范词汇治理 lint（RFC 2119 等价映射·2026-07-27 新增） ────────────────
NORM_VOCAB_PATTERNS = [
    "normative_vocab:",
    "RFC2119",
    "指令编写规范 §1.1",
    "✅DO=RFC2119",
]


def _has_norm_mapping(text):
    """判断文本是否携带 RFC 2119 等价映射声明（字段或正文指针均可）。"""
    return any(p in text for p in NORM_VOCAB_PATTERNS)


def collect_norm_vocab_issues():
    """扫描对外分发的 spec 与 skill，缺 RFC 2119 等价映射即入列。
    返回 [(文件类型, 路径), ...]（有痕列出≠静默跳过）。"""
    issues = []
    # 1) 开发规范（随安装包分发的规范文件）
    spec_dir = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "03_开发规范")
    if os.path.isdir(spec_dir):
        for f in sorted(os.listdir(spec_dir)):
            if not f.endswith(".md"):
                continue
            p = os.path.join(spec_dir, f)
            try:
                txt = open(p, encoding="utf-8").read()
            except Exception:
                continue
            if not _has_norm_mapping(txt):
                issues.append(("规范", f))
    # 2) 技能配置（SKILL.md + references/）
    if os.path.isdir(SKILL_ROOT):
        for d in sorted(os.listdir(SKILL_ROOT)):
            sd = os.path.join(SKILL_ROOT, d)
            if not os.path.isdir(sd):
                continue
            skill_md = os.path.join(sd, "SKILL.md")
            if os.path.isfile(skill_md):
                if not _has_norm_mapping(open(skill_md, encoding="utf-8").read()):
                    issues.append(("skill", f"{d}/SKILL.md"))
            refs = os.path.join(sd, "references")
            if os.path.isdir(refs):
                for rf in sorted(os.listdir(refs)):
                    if not rf.endswith(".md"):
                        continue
                    if not _has_norm_mapping(open(os.path.join(refs, rf), encoding="utf-8").read()):
                        issues.append(("skill-ref", f"{d}/references/{rf}"))
    return issues


def lint_norm(verbose=True):
    """规范词汇治理 lint：报告缺 RFC 2119 等价映射的对外文件。"""
    issues = collect_norm_vocab_issues()
    if verbose:
        print("=" * 52)
        print("  规范词汇治理 · RFC 2119 等价映射 lint")
        print(f"  时间: {datetime.datetime.now():%Y-%m-%d %H:%M}")
        print("=" * 52)
        if not issues:
            print("  ✅ 所有对外 spec/skill 均已携带映射声明")
        else:
            print(f"  ⚠️ {len(issues)} 个文件缺 RFC 2119 等价映射（补 normative_vocab 字段或 §1.1 指针）：")
            for typ, path in issues:
                print(f"    [{typ}] {path}")
        print("=" * 52)
    return issues


# ── 文件格式规范 lint（frontmatter 结构合规·2026-07-27 新增） ─────────────
# 校验《文件格式规范》v2.0.0 §3.5 符合性自检清单的机检项（1-12、14）。
# 范围（依 §一 适用范围）：
#   - 03_开发规范/*.md（含子目录）：规范文件，必须有 frontmatter，缺则报；
#   - 技能配置/*/references/*.md：参考文档，有 frontmatter 才检（无则跳过）；
#   - SKILL.md 按 §一 不适用本规范，排除。
# 零第三方依赖：YAML 用极简解析（目标字段均为单行），不 import yaml。

FILEFMT_LATEST = "v2.0.0"  # 与《文件格式规范》自身 version 对齐；升级时同步改此处
VALID_TYPES = {"reference", "explanation", "how-to", "tutorial", "plan", "reading-card", "note"}
VALID_STATUS = {"active", "draft", "deprecated"}
VER_RE_FMT = re.compile(r"^v\d+\.\d+(?:\.\d+)?(?:-[\w]+)?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# §3.5#4 禁止的同义字段名（全库字段名须一致）
FIELD_ALIASES = ["created_date", "created_at", "date_created", "modified", "updated", "d1"]


def _parse_frontmatter(text):
    """返回 (frontmatter_dict, lines, end_line)。无 frontmatter 时 dict=None。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, lines, 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, lines, 0
    fm = {}
    for ln in lines[1:end]:
        if ":" in ln:
            k, _, v = ln.partition(":")
            k = k.strip()
            if k:
                fm[k] = v.strip().strip('"').strip("'")
    return fm, lines, end


def _walk_spec_dir():
    """递归收集 03_开发规范 下所有 .md（含子目录）。"""
    out = []
    spec_dir = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "03_开发规范")
    if not os.path.isdir(spec_dir):
        return out
    for root, _dirs, files in os.walk(spec_dir):
        for f in sorted(files):
            if f.endswith(".md"):
                out.append(("规范", os.path.join(root, f)))
    return out


def collect_format_issues():
    """扫描规范文件，返回 [(类型, 路径, [问题...]), ...]。

    范围：仅 03_开发规范/*.md（递归，含子目录）——这是《文件格式规范》的核心适用对象。
    SKILL.md 及 references/ 按 §一 不适用本规范、且已由 lint_norm 管外部化映射，故排除，
    避免对 skill 参考文档的半成品 frontmatter 过度报错（范围外噪音）。
    """
    issues = []
    targets = _walk_spec_dir()  # 03_开发规范/*.md（递归）

    for typ, p in targets:
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        fm, lines, end = _parse_frontmatter(text)
        file_issues = []

        if fm is None:
            # 规范区文件必须有 frontmatter；references 区无则跳过（opt-in）
            if typ == "规范":
                issues.append((typ, p, ["缺 YAML frontmatter（规范文件必须携带，§三 段1）"]))
            continue

        # #1 三短横线首行
        if lines[0].strip() != "---":
            file_issues.append("§3.5#1 三短横线 `---` 不在文件绝对第一行")
        # #3 YAML 块唯一
        stray = sum(1 for ln in lines[1:end] if ln.strip() == "---")
        if stray > 0:
            file_issues.append(f"§3.5#3 存在 {stray} 个额外 `---` 块（YAML 应唯一）")
        # #2 闭合---后空一行
        if end + 1 < len(lines) and lines[end + 1].strip() != "":
            file_issues.append("§3.5#2 闭合 `---` 后未空一行即写正文")
        # #4 字段名一致（禁止同义别名）
        for alias in FIELD_ALIASES:
            if alias in fm:
                file_issues.append(f"§3.5#4 使用了禁止的同义字段名 `{alias}`")
        # #5 title
        if not fm.get("title"):
            file_issues.append("§3.5#5 `title` 必填")
        # #6 type
        t = fm.get("type", "")
        if not t:
            file_issues.append("§3.5#6 `type` 必填")
        elif t not in VALID_TYPES:
            file_issues.append(f"§3.5#6 `type` 值非法: {t!r}（须 {sorted(VALID_TYPES)}）")
        # #7 status
        s = fm.get("status", "")
        if not s:
            file_issues.append("§3.5#7 `status` 必填")
        elif s not in VALID_STATUS:
            file_issues.append(f"§3.5#7 `status` 值非法: {s!r}（须 {sorted(VALID_STATUS)}）")
        # #8 version
        v = fm.get("version", "")
        if not v:
            file_issues.append("§3.5#8 `version` 必填")
        elif not VER_RE_FMT.match(v):
            file_issues.append(f"§3.5#8 `version` 格式非法: {v!r}（须 vM.N.P[-tag]）")
        # #9 date
        dt = fm.get("date", "")
        if not dt:
            file_issues.append("§3.5#9 `date` 必填")
        elif not DATE_RE.match(dt):
            file_issues.append(f"§3.5#9 `date` 格式非法: {dt!r}（须 YYYY-MM-DD）")
        # #10 summary
        sm = fm.get("summary", "")
        if not sm:
            file_issues.append("§3.5#10 `summary` 必填")
        elif len(sm) > 40:
            file_issues.append(f"§3.5#10 `summary` 超 40 字（{len(sm)}字）")
        # #11 source（⛔DO NOT）
        if not fm.get("source"):
            file_issues.append("§3.5#11 `source` 必填（⛔DO NOT）")
        # #12 complies_with（☑SHOULD）
        cw = fm.get("complies_with", "")
        if not cw:
            file_issues.append("§3.5#12 `complies_with` 建议包含（☑SHOULD）")
        elif "文件格式规范" in cw and FILEFMT_LATEST not in cw:
            file_issues.append(f"§3.5#12 `complies_with` 指向旧版: {cw}（当前 {FILEFMT_LATEST}）")
        # #14 normative_vocab（对外分发须携带）
        if "normative_vocab" not in fm:
            file_issues.append("§3.5#14 对外分发文件缺 `normative_vocab`（RFC2119 映射，✅DO）")

        if file_issues:
            issues.append((typ, p, file_issues))
    return issues


def lint_format(verbose=True):
    """文件格式规范 lint：报告 §3.5 结构合规问题。"""
    issues = collect_format_issues()
    if verbose:
        print("=" * 52)
        print("  文件格式规范 · frontmatter 结构合规 lint")
        print(f"  时间: {datetime.datetime.now():%Y-%m-%d %H:%M}")
        print("=" * 52)
        if not issues:
            print("  ✅ 所有规范/参考文件均通过 §3.5 结构合规")
        else:
            total = sum(len(iss) for _, _, iss in issues)
            print(f"  ⚠️ {len(issues)} 个文件 / 共 {total} 项不合规：")
            for typ, p, iss in issues:
                rel = os.path.relpath(p, HOME)
                print(f"    [{typ}] {rel}")
                for it in iss:
                    print(f"        - {it}")
        print("=" * 52)
    return issues


def get_readme_skill_keys(lines, section="### 4.1"):
    """从 README 指定节表格提取技能目录名（第2数据段）。v1.3.0 参数化（§4.1 核心/§4.2 辅助）。"""
    keys = []
    in_sec = False
    for line in lines:
        s = line.strip()
        if s.startswith(section):
            in_sec = True
            continue
        if in_sec and s.startswith("### "):
            break
        if in_sec and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 2 and re.match(r"^[a-z][a-z0-9\-]*$", parts[2]):
                keys.append(parts[2])
    return keys


def get_readme_42_names(lines):
    """从 README §4.2/§4.3 表格提取技能名（第1数据段·去括号版本后缀）——辅助/个人专用识别。"""
    names = set()
    in_sec = False
    for line in lines:
        s = line.strip()
        if s.startswith("### 4.2") or s.startswith("### 4.3"):
            in_sec = True
            continue
        if in_sec and s.startswith("### "):
            break
        if in_sec and "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 1 and parts[1]:
                name = re.sub(r"\s*\(.*$", "", parts[1]).strip()
                if name and name != "技能名":
                    names.add(name)
            if len(parts) > 2 and re.match(r"^[a-z][a-z0-9\-]*$", parts[2]):
                names.add(parts[2])  # §4.3 第2列=目录名（中文名第1列匹配不到目录 key）
    return names


def load_manifest_skills():
    """读 mirror-manifest.json（安装包清单·同步真相源）→ 进包 Skill 目录名集合。
    失败 → 返回 None（调用方降级：硬一致性跳过并报⚠️，不挂死）。"""
    try:
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
        items = m.get("entries", []) if isinstance(m, dict) else m
        skills = set()
        for it in items:
            if not isinstance(it, dict):
                continue
            src = it.get("src_dir") or ""  # 只认目录条目（src 单文件如 restore-my-skills 不算 Skill）
            if "技能配置" in src:
                # src_dir 形如 [记忆共享中心]/技能配置/daily-buddy/
                tail = src.rstrip("/").split("/")[-1]
                if tail:
                    skills.add(tail)
        return skills
    except Exception:
        return None


def count_amber():
    if not os.path.isdir(AMBER):
        return 0
    return len([
        f for f in os.listdir(AMBER)
        if os.path.isfile(os.path.join(AMBER, f)) and not f.startswith(".")
    ])


# ── 宪法五原则机检（2026-10-01 · 愿景最优解落地） ────────────────
# 将《00-宪法愿景.md》五原则（宪法/愿景/唯一性/中立/命名）落地为可机检规则。
# 防"纸面覆盖/假绿"纪律（见记忆"判据沉默三查/验证同源=假绿"）：
#   · 每条断言仅针对"可机械验证"条件；抽象原则不实机检，仅作文档声明。
#   · proxy 类检查（愿景/宪法）在报告中标注"代理判据"，不与"已根治"混淆。
#   · 全部路径复用模块级 SKILL_ROOT / CORE_FILES（已随副本参数化）→ 本段零新增路径字面量
#     → 4 副本代码逐字节一致，同步只需原样落盘无需改路径。

def _skill_dirs():
    """技能配置/ 下所有技能目录名。"""
    if not os.path.isdir(SKILL_ROOT):
        return []
    return [d for d in sorted(os.listdir(SKILL_ROOT))
            if os.path.isdir(os.path.join(SKILL_ROOT, d))]


def _read_skill_field(skill_dir, field):
    """从 SKILL.md frontmatter 取字段值（None=无/非 frontmatter/字段在 body）。"""
    p = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(p):
        return None
    try:
        lines = open(p, encoding="utf-8").read().split("\n")
    except Exception:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return None
        m = re.match(rf"{field}:\s*(.+)", lines[i])
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def _skill_field_empty(skill_dir, field):
    """字段存在但值为空 → True（自相矛盾·必错）；字段缺失/无 frontmatter → False。"""
    p = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(p):
        return False
    try:
        lines = open(p, encoding="utf-8").read().split("\n")
    except Exception:
        return False
    if not lines or lines[0].strip() != "---":
        return False
    pat = re.compile(rf"{field}:\s*$")
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return False
        if pat.match(lines[i]):
            return True
    return False


VISION_MARKERS = ["全自动化", "越用越好用", "自主自动进化", "越用越了解使用者"]
CONSTITUTION_MARKERS = ["以任何规则覆盖本愿景", "愿景四方向为准", "最高判据"]


def collect_constitution_issues():
    """扫描技能与核心文件，返回 [(原则, 对象, 问题), ...]（有痕列出≠静默跳过）。"""
    issues = []

    # ── 命名（窄判据：只抓自相矛盾——name: 存在但为空；中文目录名合法不强检·2026-10-01 误报收窄）──
    for d in _skill_dirs():
        if _skill_field_empty(os.path.join(SKILL_ROOT, d), "name"):
            issues.append(("命名", d, "SKILL.md name: 字段存在但为空（自相矛盾）"))

    # ── 唯一性（SSOT 单源）──
    name_map = {}
    for d in _skill_dirs():
        nm = _read_skill_field(os.path.join(SKILL_ROOT, d), "name")
        if nm:
            name_map.setdefault(nm, []).append(d)
    for nm, ds in name_map.items():
        if len(ds) > 1:
            issues.append(("唯一性", nm, "技能 name 重复: " + ", ".join(ds)))

    # 固化引用 SSOT 指针——裁定（2026-10-01 误报收窄·留痕）：本生态约定「声明 source_skill:/source:
    # 才算固化件」（extract_references_versions 同口径），未声明者=第一方文档（自带 version 的
    # CHANGELOG/设计细则等），强检即 7 项全误报。SSOT 指针正规判据=既有 `refs` 子命令（对已声明
    # 固化件查版本漂移+源不可解析显形），此处不重复不倒置。

    # ── 愿景（代理判据：SOUL.md 须锚定四方向）──
    for anchor, path in CORE_FILES:
        if "SOUL" not in anchor:
            continue
        if not os.path.isfile(path):
            continue
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        missing = [m for m in VISION_MARKERS if m not in txt]
        if missing:
            issues.append(("愿景", anchor, "未锚定愿景四方向(代理): " + ", ".join(missing)))

    # ── 宪法（代理判据：SOUL.md 须声明愿景最高条款）──
    for anchor, path in CORE_FILES:
        if "SOUL" not in anchor:
            continue
        if not os.path.isfile(path):
            continue
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        if not any(m in txt for m in CONSTITUTION_MARKERS):
            issues.append(("宪法", anchor, "未声明愿景最高条款(代理): 以任何规则覆盖本愿景"))

    # ── 中立（窄安全判据：对外引用不得含安装包禁用个人标识）──
    for d in _skill_dirs():
        refs = os.path.join(SKILL_ROOT, d, "references")
        if not os.path.isdir(refs):
            continue
        for rf in sorted(os.listdir(refs)):
            if not rf.endswith(".md"):
                continue
            try:
                txt = open(os.path.join(refs, rf), encoding="utf-8").read()
            except Exception:
                continue
            if "童灵在岗" in txt:
                issues.append(("中立", d + "/references/" + rf, "含安装包禁用个人标识「童灵在岗」(脱敏违规)"))

    return issues


def lint_constitution(verbose=True):
    """宪法五原则机器强制 lint：命名/唯一性/愿景/宪法/中立。"""
    issues = collect_constitution_issues()
    if verbose:
        print("=" * 52)
        print("  宪法五原则 · 机器强制 lint")
        print("  时间: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        print("=" * 52)
        if not issues:
            print("  ✅ 所有技能/核心文件通过宪法五原则机检")
        else:
            print("  ⚠️ " + str(len(issues)) + " 项待修：")
            for principle, obj, msg in issues:
                print("    [" + principle + "] " + obj + ": " + msg)
        print("=" * 52)
    return issues


# ---------- README 读写 ----------

def read_readme():
    text = open(README, encoding="utf-8").read()
    return text, text.split("\n")


def write_readme(text, lines):
    out = "\n".join(lines)
    if text.endswith("\n"):
        out += "\n"
    open(README, "w", encoding="utf-8").write(out)


# ---------- README 字段读取 ----------

def get_readme_skill_version(lines, key):
    """§4.1: key=目录名精确匹配数据段，版本在下一数据段。"""
    for line in lines:
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        for k, p in enumerate(parts):
            if p == key and k + 1 < len(parts):
                m = VER_RE.search(parts[k + 1])
                return m.group(1) if m else None
    return None


def get_readme_core_version(lines, anchor):
    """§二: anchor 关键字定位行，版本在第4数据段(parts[4])。"""
    for line in lines:
        if "|" not in line or anchor not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > 4:
            m = VER_RE.search(parts[4])
            return m.group(1) if m else None
    return None


def get_readme_amber_count(lines):
    for line in lines:
        m = re.search(r"当前 \*\*(\d+) 个存档\*\*", line)
        if m:
            return int(m.group(1))
    return None


def get_readme_self_version(lines):
    for line in lines:
        m = re.search(r"\*\*本README版本\*\*：v([\d.]+)", line)
        if m:
            return m.group(1)
    return None


# ---------- README 字段改写 ----------

def patch_table_field(lines, anchor, field_idx, new_ver):
    """定位含 anchor 的表格行，把第 field_idx 个数据段内的版本号替换为 new_ver。
    field_idx: §4.1 版本列=3, §二 版本列=4 (parts[0]为前导空)。"""
    for i, line in enumerate(lines):
        if "|" not in line or anchor not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if field_idx < len(parts):
            old = parts[field_idx]
            new_field = VER_RE.sub("v" + new_ver, old)
            if new_field != old:
                parts[field_idx] = new_field
                lines[i] = "| " + " | ".join(parts[1:-1]) + " |"
                return True
            return False
    return False


def patch_amber_count(lines, cnt):
    for i, line in enumerate(lines):
        m = re.search(r"当前 \*\*(\d+) 个存档\*\*", line)
        if m:
            lines[i] = line.replace(f"**{m.group(1)} 个存档**", f"**{cnt} 个存档**")
            return True
    return False


def patch_readme_self_version(lines, new_ver):
    for i, line in enumerate(lines):
        m = re.search(r"\*\*本README版本\*\*：v([\d.]+)", line)
        if m:
            lines[i] = line.replace(f"v{m.group(1)}", f"v{new_ver}")
            return True
    return False


def bump_patch(ver):
    parts = ver.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def pre_backup_readme():
    os.makedirs(SYNC_BACKUP, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    dst = os.path.join(SYNC_BACKUP, f"README_pre-sync_{ts}.bak")
    shutil.copy2(README, dst)
    print(f"[pre] 备份 README → sync-backups/{os.path.basename(dst)}")


# ---------- 低频软同步审计（提示不改写） ----------

def soft_check(lines, soft_skills=None):
    msgs = []
    if soft_skills:
        msgs.append(
            f"技能配置/ 下 {len(soft_skills)} 个 skill 未分类"
            f"（不在 §4.1 核心/§4.2 辅助/§4.3 个人专用/mirror-manifest 进包清单——建议登记对应节）：{', '.join(soft_skills)}"
        )
    msgs.append(
        "§一/§二 变更日志条数为约数（220+/221+），实际以变更日志.md 为准，"
        "脚本不自动改写约数"
    )
    return msgs


# ---------- 主流程 ----------

def audit(verbose=True):
    skills, cores = collect_actual()
    _, lines = read_readme()
    drifts = []
    manifest_drifts = []  # v1.3.0：§4.1 ↔ manifest 双向硬一致性（报告不改写·处置需人工）
    soft_skills = []
    keys = get_readme_skill_keys(lines)
    for key in keys:
        actual = skills.get(key)
        if not actual:
            continue
        rv = get_readme_skill_version(lines, key)
        if rv is None:
            drifts.append(("skill", key, "(缺失行)", actual))
        elif rv != actual:
            drifts.append(("skill", key, rv, actual))
    # v1.3.0 守备链：§4.1（README 投影）↔ manifest（真相）双向比对
    listed = set(keys)
    manifest_skills = load_manifest_skills()
    if manifest_skills is None:
        manifest_drifts.append(("⚠️", "manifest", "读取失败", "硬一致性跳过（降级：不报不拦）"))
    else:
        for k in sorted(manifest_skills - listed):
            manifest_drifts.append(("漏登记", k, "manifest 有", "README §4.1 无"))
        for k in sorted(listed - manifest_skills):
            manifest_drifts.append(("多登记", k, "README §4.1 有", "manifest 无（个人用/待进包）"))
    # 软提示：技能配置未分类（不在 §4.1 ∪ §4.2 ∪ §4.3 个人专用 ∪ manifest）= 待登记
    sec42 = get_readme_42_names(lines)
    for d in skills:
        if d not in listed and d not in sec42 and not (manifest_skills and d in manifest_skills):
            soft_skills.append(d)
    for anchor, _ in CORE_FILES:
        actual = cores.get(anchor)
        if not actual:
            continue
        rv = get_readme_core_version(lines, anchor)
        if rv is None:
            drifts.append(("core", anchor, "(缺失)", actual))
        elif rv != actual:
            drifts.append(("core", anchor, rv, actual))
    cnt = count_amber()
    rc = get_readme_amber_count(lines)
    if rc is not None and rc != cnt:
        drifts.append(("amber", "记忆琥珀", str(rc), str(cnt)))

    # 固化引用版本核对（v1.1新增）
    ref_drifts = collect_references_drift()
    # 守卫注册表扫描（守卫编写规范§五·2026-07-26新增）
    guard_issues = collect_guard_registry_issues()
    # 核心文件路径自检（v1.3.3·防「路径失效→静默跳过→假绿灯」）
    missing_paths = collect_missing_core_paths()

    if verbose:
        print("=" * 52)
        print("  技能与系统说明同步 · 漂移审计报告")
        print(f"  时间: {datetime.datetime.now():%Y-%m-%d %H:%M}")
        print("=" * 52)
        if not drifts:
            print("  ✅ 高频硬同步区：0 漂移")
        else:
            print("  ⚠️ 高频硬同步区漂移：")
            for typ, key, old, new in drifts:
                print(f"    [{typ}] {key}: README={old} → 实际={new}")
        print("-" * 52)
        if not missing_paths:
            print(f"  ✅ 核心文件路径：{len(CORE_FILES)}/{len(CORE_FILES)} 有效（视野完整·0 静默跳过）")
        else:
            print(f"  ⚠️ 核心文件路径失效 {len(missing_paths)}/{len(CORE_FILES)}——下列行**未被任何检查覆盖**（假绿灯源）：")
            for a, p in missing_paths:
                print(f"    [path] {a}: {p}（文件不存在）")
        print("-" * 52)
        if not ref_drifts:
            print("  ✅ 固化引用版本：0 漂移")
        else:
            print("  ⚠️ 固化引用版本漂移：")
            for skill_name, ref_file, source_name, ref_ver, source_ver in ref_drifts:
                print(f"    [{skill_name}] {ref_file}: 固化v{ref_ver} vs {source_name} v{source_ver}")
        print("-" * 52)
        if not guard_issues:
            print("  ✅ 守卫注册表：真相源路径全部有效")
        else:
            print("  ⚠️ 守卫注册表问题：")
            for g, msg in guard_issues:
                print(f"    [{g}] {msg}")
        print("-" * 52)
        if not manifest_drifts:
            print("  ✅ §4.1↔manifest（README 投影↔同步真相）：0 漂移")
        else:
            print("  ⚠️ §4.1↔manifest 一致性（报告不改写·处置需人工）：")
            for typ, key, o, n in manifest_drifts:
                print(f"    [{typ}] {key}: {o} → {n}")
        print("-" * 52)
        print("  低频软同步提示（不自动改写，请人工确认）：")
        for s in soft_check(lines, soft_skills):
            print("    " + s)
        print("=" * 52)
    return (drifts
            + [("ref", f"{d}/{r}", rv, sv) for d, r, _, rv, sv in ref_drifts]
            + [("path", a, "路径失效(该行未被检查)", p) for a, p in missing_paths])


def sync():
    skills, cores = collect_actual()
    text, lines = read_readme()
    changed = 0
    for key, actual in skills.items():
        rv = get_readme_skill_version(lines, key)
        if rv != actual and patch_table_field(lines, key, 3, actual):
            changed += 1
    for anchor, _ in CORE_FILES:
        actual = cores.get(anchor)
        if actual and get_readme_core_version(lines, anchor) != actual:
            if patch_table_field(lines, anchor, 4, actual):
                changed += 1
    cnt = count_amber()
    if get_readme_amber_count(lines) != cnt and patch_amber_count(lines, cnt):
        changed += 1

    if changed > 0:
        self_v = get_readme_self_version(lines)
        nv = bump_patch(self_v) if self_v else "1.1.2"
        patch_readme_self_version(lines, nv)
        changed += 1
        pre_backup_readme()
        write_readme(text, lines)
        print(f"[sync] 改写 {changed} 处（含 README 自身版本 {self_v}→{nv}）")
    else:
        print("[sync] 已对齐，无需改动（幂等）")

    d = audit(verbose=False)
    hard = [x for x in d if x[0] in ("skill", "core", "amber", "path")]
    if hard:
        print(f"⚠️ sync 后仍有 {len(hard)} 处高频漂移/守卫视野缺口：")
        for t, k, o, n in hard:
            print(f"    [{t}] {k}: {o}→{n}")
        return 1
    print("✅ sync 完成，高频硬同步区 0 漂移")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd in ("self-test", "--self-test"):
        print("=== sync_guard.py 注册表路径提取夹具 ===")
        sys.exit(registry_path_selftest())
    if cmd == "audit":
        audit(verbose=True)
        sys.exit(0)
    elif cmd == "sync":
        rc = sync()
        sys.exit(rc)
    elif cmd == "verify":
        d = audit(verbose=False)
        hard = [x for x in d if x[0] in ("skill", "core", "amber", "ref", "path")]
        if hard:
            print(f"⚠️ {len(hard)} 处漂移（含固化引用）")
            for t, k, o, n in hard:
                print(f"  [{t}] {k}: {o}→{n}")
            sys.exit(1)
        print("✅ 0 漂移")
        sys.exit(0)
    elif cmd == "refs":
        # v1.1新增：专门扫描固化引用版本漂移
        ref_drifts = collect_references_drift()
        if not ref_drifts:
            print("✅ 固化引用版本：0 漂移")
            sys.exit(0)
        print(f"⚠️ {len(ref_drifts)} 处固化引用版本漂移：")
        for skill_name, ref_file, source_name, ref_ver, source_ver in ref_drifts:
            print(f"  [{skill_name}] {ref_file}: 固化v{ref_ver} vs {source_name} v{source_ver}")
        sys.exit(1)
    elif cmd == "lint_norm":
        issues = lint_norm(verbose=True)
        sys.exit(1 if issues else 0)
    elif cmd == "lint_format":
        issues = lint_format(verbose=True)
        sys.exit(1 if issues else 0)
    elif cmd == "lint_constitution":
        issues = lint_constitution(verbose=True)
        sys.exit(1 if issues else 0)
    else:
        print("用法: sync_guard.py [audit|sync|verify|refs|lint_norm|lint_format]")
        sys.exit(2)


if __name__ == "__main__":
    main()
