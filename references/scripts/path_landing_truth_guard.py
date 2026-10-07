#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/path_landing_truth_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""path_landing_truth_guard.py — 落点真值守卫（记忆根不变量·独立验证器）

## 它治什么（2026-10-04 脱敏逆向污染实证案）

发布侧净化管线（relocate/deident：`[记忆共享中心]/脚本中心` → `[记忆共享中心]/脚本中心`，
占位符再填 `~`）被**反向套用到生产正本**，造出两类非法形态：

| 形态 | 生产侧写法 | 实际解析 | 病灶 |
|:--|:--|:--|:--|
| A 丢记忆根前缀 | `expanduser("~/脚本中心/logs/runtime")` | `/Users/x/脚本中心/…` | 家根幽灵目录 |
| B 占位符填进 join | `join(expanduser("~"), expanduser("~"), "开发工具", …)` | `/Users/x/开发工具/…` | 同上（grep 抓不到） |

两者都被 `os.makedirs(..., exist_ok=True)` **静默建目录**，于是台账分批落到家根，
取证链断裂（本案：W3 判定记录 09:13 后分散在三处）。

## 为什么是"独立验证器"

⛔ 不 import 被测件（避免跟随被测代码的错误逻辑自证清白，也避免触发副作用），
而是 **AST 静态求值**：把 `expanduser/join/字符串字面量` 算成**绝对路径真值**，
再对照不变量「必须位于记忆中心根之下」。因此 B 类（跨函数嵌套、grep 形态漏网）也能抓到。

## 三条判据

① 落点真值不变量：路径常量/字面量解析后 ⛔ 不得等于 `$HOME` 直系子项（须在 archive_root 下）
② 家根幽灵哨兵：`$HOME/<记忆中心子目录名>` 若是**真实目录**（非软链）⇒ 幽灵，报文件数+最新 mtime
③ 静态残留：活体树中出现 `~/脚本中心/`、`~/开发工具/` 等丢前缀字面量 ⇒ 显形

Fail-Loud：有红即单行显形（Stop 钩子不阻断，守 Hook 三纪律）；留痕 JSONL。

用法：
  python3 path_landing_truth_guard.py            # 人读报告
  python3 path_landing_truth_guard.py --json     # 机读
  python3 path_landing_truth_guard.py --report   # Stop 钩子用：仅单行
  python3 path_landing_truth_guard.py --self-test
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import json
import os
import re
import sys
import time

# ①-④ v1.9.0 增量注记见 scan_tree/_eval_path_expr/scan_raw_tilde/scan_rules_links 各段
__version__ = "1.9.0"  # v1.9.0(2026-10-07 QoderCN 野根根治轮)：①判据①新增常量间接解析(MC=expanduser("~")+join(MC,档案子项)盲区·实证13件借此脱检致刷新链静默崩4小时)②裸~判定补多行 expanduser( 换行参数识别(假阳6处 platform_adaptation_check)③丢前缀文本线豁免#注释行(历史注记非fs落点)④rules面端实体化白名单(2026-10-07你定端哲学·Qoder CN core-soul/core-user)
# 历史 v1.8.0(2026-10-05·P3/B3挂账)(2026-10-05·P3/B3挂账)：判据④扩面——认 Path.home() / "~/…" 拼接形与 home() 候选元组混入裸~（原只追模块级裸~常量赋值）
# rules 面（判据⑤·v1.7）：断链类命中常属**他端** rules 资产（本端⛔不改他端文件），
# 默认进 advisory_detail 显形不判红；--rules-strict 才计入 hits（由人确认后翻硬）。
RULES_STRICT = False

HOME = os.path.expanduser("~")
# B修源·声明驱动口径v2(2026-10-05·条文47·37支)：档案根=本件realpath上溯两层(真身在脚本中心·层数按本件深度实算非沿用36支)
ARCHIVE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# 活体树 = 被检对象；发布树（发布库/包内）不属本守卫职责
LIVE_TREES = [os.path.join(ARCHIVE, "开发工具"), os.path.join(ARCHIVE, "脚本中心")]
LEDGER = os.path.join(ARCHIVE, "开发工具", "logs", "runtime", "path_landing_truth.jsonl")
CACHE = os.path.join(ARCHIVE, "开发工具", "logs", "runtime", "path_landing_truth.cache.json")  # 指纹缓存：域内无变更即复用上次判定
FINGERPRINT = True

SKIP_DIR = {"__pycache__", ".venv", ".venv-st", "node_modules", ".git", "cache"}
# 本守卫自身的字面量就是判据形态（检测器必须写着要检测的模式）
SELF_EXEMPT = ("path_landing_truth_guard.py",)


SETTINGS_CANDIDATES = [
    os.path.join(HOME, ".qoder-cn", "settings.json"),
    os.path.join(HOME, ".workbuddy", "settings.json"),
    os.path.join(HOME, ".qoder", "settings.json"),
    os.path.join(HOME, ".zcode", "cli", "config.json"),
    os.path.join(HOME, ".hermes", "settings.json"),
]


def mount_domains():
    """判据域=实盘挂载的脚本所在目录（v1.1.0 挂载驱动·⛔不写死两目录）。
    根因：route_miss_feeder.py 实际挂在 自定义层/待完成工作/路由家族/scripts/，
    域写死 开发工具+脚本中心 时该件在家根建幽灵却检不出=守卫自身「判据未随对象演化」。"""
    dirs = set(LIVE_TREES)
    for sp in SETTINGS_CANDIDATES:
        try:
            d = json.load(open(sp, encoding="utf-8"))
        except Exception:
            continue
        hooks = d.get("hooks") or d.get("hooks", {}).get("events") or {}
        for groups in (hooks.values() if isinstance(hooks, dict) else []):
            if not isinstance(groups, list):
                continue
            for grp in groups:
                for h in (grp.get("hooks", []) if isinstance(grp, dict) else []):
                    cmd = h.get("command", "") if isinstance(h, dict) else ""
                    for m in re.finditer(r"([/~][^\s\"'`]*?\.py)", cmd):
                        p = os.path.expanduser(m.group(1))
                        if os.path.isfile(p):
                            dirs.add(os.path.dirname(os.path.realpath(p)))
    return sorted(dirs)

def archive_child_names():
    """记忆中心子目录名——幽灵哨兵词源：以 archive_root 实际子项为唯一真源（⛔不手抄清单）。"""
    try:
        return {n for n in os.listdir(ARCHIVE)
                if os.path.isdir(os.path.join(ARCHIVE, n)) and not n.startswith(".")}
    except OSError:
        return set()


def lost_prefix_re():
    return re.compile(r'~/(%s)/' % "|".join(sorted(archive_child_names())))


# ── AST 求值：把路径表达式算成绝对路径真值 ────────────────────────────────
def _eval_path_expr(node, consts=None):
    """返回 (绝对路径, 构造说明)；认不出返回 None（⛔不猜变量段）。
    v1.9.0：consts=模块级常量表时认 Name 查表（仅收可完整求值的简单赋值·宁漏不误）。"""
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        # `X = os.environ.get(..) or os.path.expanduser("~")` 族：静态判据取回退侧（默认落点即实盘落点）
        return _eval_path_expr(node.values[-1], consts)
    if isinstance(node, ast.Name):
        if consts and node.id in consts:
            return consts[node.id], "const<-%s>" % node.id
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        s = node.value
        if s.startswith("~") or os.path.isabs(s):
            return os.path.normpath(os.path.expanduser(s)), "literal"
        return None
    if isinstance(node, ast.Call):
        fn = node.func
        name = getattr(fn, "attr", None) or (getattr(fn, "id", None)
                                             if isinstance(fn, ast.Name) else None)
        if name == "expanduser" and len(node.args) == 1:
            inner = _eval_path_expr(node.args[0], consts)
            if inner:
                return os.path.normpath(os.path.expanduser(inner[0])), "expanduser<-%s" % inner[1]
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                return os.path.normpath(os.path.expanduser(node.args[0].value)), "expanduser"
            return None
        if name == "join":
            parts = []
            for a in node.args:
                v = _eval_path_expr(a, consts)
                if v is not None:
                    parts.append(v[0])
                elif isinstance(a, ast.Constant) and isinstance(a.value, str):
                    parts.append(a.value)
                else:
                    return None
            if len(parts) >= 2:
                return os.path.normpath(os.path.join(*parts)), "join"
            return None
    return None


def _module_consts(tree):
    """v1.9.0 判据①扩：模块级简单赋值常量表（NAME -> 绝对路径），定点迭代两轮收链。
    仅收「单 Name 目标 = 可完整求值表达式」；函数内局部同名变量不查（AST walk 在模块级赋值建表后
    对任意深度表达式复用该表，存在遮蔽假阳风险——但判据下游 _is_home_child 双闸(家根∩档案子项名)
    极难被遮蔽命中，宁漏不误原则下接受）。"""
    consts = {}
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            tg = n.targets if isinstance(n, ast.Assign) else [n.target]
            names = [x.id for x in tg if isinstance(x, ast.Name)]
            for _ in range(2):
                ev = _eval_path_expr(n.value, consts)
                if ev:
                    for nm in names:
                        consts[nm] = ev[0]
    return consts


def _is_home_child(p):
    """幽灵落点判据：解析结果的第一段（$HOME 下）与记忆中心子目录**同名** ⇒ 违规。

    为什么不只查"直系子项"：`~/脚本中心/logs/runtime` 是嵌套层，只查直系必漏
    （自测 T3 首跑即因此假阴性——判据未随对象演化=假绿，同 铁律-002 假红先例反号）。
    词源取 archive_root 实况子项，⛔ 不手抄目录名清单（换机/改名自动跟随）。
    """
    if not p:
        return False
    if p == ARCHIVE or p.startswith(ARCHIVE + os.sep):
        return False
    if not (p == HOME or p.startswith(HOME + os.sep)):
        return False
    rel = os.path.relpath(p, HOME)
    if rel.startswith(".."):
        return False
    first = rel.split(os.sep)[0]
    return first in archive_child_names()


def _candidate_exprs(node):
    if isinstance(node, ast.Assign):
        t = node.value
        if isinstance(t, (ast.Tuple, ast.List)):
            return list(t.elts)
        return [t]
    if isinstance(node, ast.keyword) and isinstance(node.value, ast.expr):
        return [node.value]
    if isinstance(node, (ast.Call, ast.Subscript)):
        return [node]
    return []


def scan_tree():
    hits = []
    rx = lost_prefix_re()
    for tree in mount_domains():
        if not os.path.isdir(tree):
            continue
        for root, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR]
            for fn in files:
                if not fn.endswith(".py") or fn in SELF_EXEMPT:
                    continue
                fp = os.path.join(root, fn)
                try:
                    src = open(fp, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                lines = src.split("\n")
                try:
                    parsed = ast.parse(src)
                except SyntaxError:
                    hits.append({"file": fp, "line": 0, "form": "syntax-error(无法求值)",
                                 "path_value": "", "snippet": ""})
                    continue
                consts = _module_consts(parsed)
                for node in ast.walk(parsed):
                    for e in _candidate_exprs(node):
                        got = _eval_path_expr(e, consts)
                        # 判据①扩 A 型（2026-10-04·Hermes 指控本件不认空参退化，指控成立）：
                        #   真特征 = 只有一个实参的 os.path.join(...)（join 单参恒等返回该参，本身无意义，
                        #   此族皆由「第二参被脱敏删空」造成）；⛔ 不得用「求值==HOME」当判据（那会把
                        #   `HOME = os.path.expanduser("~")` 这类合法写法全误报——首版实测假红 483 处即此错）
                        if isinstance(e, ast.Call) and getattr(e.func, "attr", "") == "join" and len(e.args) == 1:
                            # 根因修正：_eval_path_expr 对单参 join 直接返回 None（要求≥2段），
                            # 故必须先判形态、再对**内层实参**求值，否则本分支永不触发（实测首两版即如此）
                            g1 = _eval_path_expr(e.args[0], consts)
                            if g1 and g1[0] == HOME:
                                ln = getattr(e, "lineno", 0) or getattr(node, "lineno", 0)
                                hits.append({"file": fp, "line": ln,
                                             "form": "落点退化为家目录(join 仅一参·疑参数被删空)",
                                             "path_value": g1[0],
                                             "snippet": (lines[ln - 1].strip() if ln else "")[:120]})
                                continue
                        if got and _is_home_child(got[0]):
                            ln = getattr(e, "lineno", 0) or getattr(node, "lineno", 0)
                            hits.append({"file": fp, "line": ln,
                                         "form": "落点解析到家根(%s)" % got[1],
                                         "path_value": got[0],
                                         "snippet": (lines[ln - 1].strip() if ln else "")[:120]})
                _doclines = set()  # v1.6.1：docstring/示例块豁免（AST 路线本就正确，文本线补齐·N2错位防假阳 QCN清尾轮实证）
                try:
                    for _n in ast.walk(ast.parse(src)):
                        if isinstance(_n, ast.Expr) and isinstance(_n.value, ast.Constant) and isinstance(_n.value.value, str):
                            _doclines.update(range(_n.value.lineno, (_n.value.end_lineno or _n.value.lineno) + 1))
                except SyntaxError:
                    pass
                for i, l in enumerate(lines, 1):
                    m = rx.search(l)
                    if m and i not in _doclines and not l.lstrip().startswith("#"):  # v1.9.0 历史注释非fs落点
                        hits.append({"file": fp, "line": i, "form": "丢记忆根前缀字面量",
                                     "path_value": m.group(0), "snippet": l.strip()[:120]})
    uniq, seen = [], set()
    for h in hits:
        k = (h["file"], h["line"], h["form"])
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    return uniq


FS_OPS = {"open", "exists", "isfile", "isdir", "makedirs", "join", "Path",
          "listdir", "stat", "getmtime", "read_text", "write_text"}


def _is_home_call(node):
    """v1.8.0 判据④扩面辅助：认 `X.home()` 零参调用形态（Path.home()）。"""
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "home" and not node.args)


def scan_raw_tilde():
    """判据④：模块级常量值是裸 `~/...` 字符串（未经 expanduser），且该常量被文件系统操作引用。
    `open("~/x")` 不展开 ~ ⇒ FileNotFoundError ⇒ 注入/检测静默失败。
    实证：注入器 SLICES_DIR 被脱敏从绝对路径改成裸 ~/ 后，L2~L5 域切片注入静默降级约 7 小时，
    判据①②③当时全部无感（不落家根，只是读不到）。
    v1.8.0 扩面（台账B3）：原只认「模块级常量=裸~/字符串且被fs操作引用」；漏两种真形态——
    A) `Path.home() / "~/…"` 拼接（解析成 家根/~/… 幽灵）；B) 候选元组混型：Path 与裸~字符串同列，
    经 `/` 运算对 str 抛 TypeError 或静默永不匹配（实证 skill_version_check.py L164）。"""
    out = []
    for tree in mount_domains():
        if not os.path.isdir(tree):
            continue
        for root, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR]
            for fn in files:
                if not fn.endswith(".py") or fn in SELF_EXEMPT:
                    continue
                fp = os.path.join(root, fn)
                try:
                    src = open(fp, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                lines = src.split("\n")
                try:
                    t = ast.parse(src)
                except SyntaxError:
                    continue
                # v1.8.0 判据④扩面·两形态：A) Path.home() / "~…" 拼接 B) home() 元组混入裸~
                for sub in ast.walk(t):
                    if isinstance(sub, ast.BinOp) and isinstance(sub.op, ast.Div):
                        for lhs, rhs in ((sub.left, sub.right), (sub.right, sub.left)):
                            if (_is_home_call(lhs) and isinstance(rhs, ast.Constant)
                                    and isinstance(rhs.value, str) and rhs.value.startswith("~")):
                                out.append({"file": fp, "line": sub.lineno,
                                            "form": "Path.home()拼接裸~(落家根幽灵目录~/)",
                                            "path_value": rhs.value,
                                            "snippet": (lines[sub.lineno - 1].strip() if sub.lineno <= len(lines) else "")[:120]})
                                break
                    elif isinstance(sub, (ast.Tuple, ast.List)):
                        if any(any(_is_home_call(x) for x in ast.walk(e)) for e in sub.elts):
                            for e in sub.elts:
                                if (isinstance(e, ast.Constant) and isinstance(e.value, str)
                                        and e.value.startswith("~")):
                                    out.append({"file": fp, "line": e.lineno,
                                                "form": "Path.home()候选元组混入裸~字符串",
                                                "path_value": e.value,
                                                "snippet": (lines[e.lineno - 1].strip() if e.lineno <= len(lines) else "")[:120]})
                raw = {}
                for n in t.body:
                    if not isinstance(n, (ast.Assign, ast.AnnAssign)) or n.value is None:
                        continue
                    tgs = n.targets if isinstance(n, ast.Assign) else [n.target]
                    names = [x.id for x in tgs if isinstance(x, ast.Name)]
                    for sub in ast.walk(n.value):
                        if (isinstance(sub, ast.Constant) and isinstance(sub.value, str)
                                and sub.value.startswith("~/")):
                            lo = sub.lineno - 1
                            hi = (sub.end_lineno or sub.lineno) - 1
                            if any("expanduser" in lines[k] for k in range(max(lo - 1, 0), hi + 1) if k < len(lines)):  # v1.9.0 多行调用首行
                                continue
                            for nm in names:
                                raw.setdefault(nm, (sub.value, sub.lineno))
                if not raw:
                    continue
                used = set()
                for n in ast.walk(t):
                    if not isinstance(n, ast.Call):
                        continue
                    nm = getattr(n.func, "attr", None) or (n.func.id if isinstance(n.func, ast.Name) else None)
                    if nm in FS_OPS:
                        for sub in ast.walk(n):
                            if isinstance(sub, ast.Name) and sub.id in raw:
                                used.add(sub.id)
                for name in sorted(used):
                    val, ln = raw[name]
                    out.append({"file": fp, "line": ln, "form": "裸~常量进文件系统操作(静默失败)",
                                "path_value": val,
                                "snippet": (lines[ln - 1].strip() if ln <= len(lines) else "")[:120]})
    return out


def scan_skill_links():
    """判据⑤（2026-10-04 你定底线）：Skill 源唯一=~/[记忆共享中心]/技能配置；
    各端 skills 目录 ⛔ 不得软链到 发布库（包内=给用户的投影）。
    实证：6 端 × 10 Skill 共 60 条链进包内 ⇒ 改源不抵端，作者端跑的是投影。"""
    out = []
    pkg = os.path.join(ARCHIVE, "发布库")
    home = HOME
    import glob as _glob
    roots = set()
    for pat in (".*/skills", ".config/*/skills", "Library/Application Support/*/skills"):
        roots.update(p for p in _glob.glob(os.path.join(home, pat)) if os.path.isdir(p))
    for r in sorted(roots):
        try:
            names = sorted(os.listdir(r))
        except OSError:
            continue
        for nm in names:
            p = os.path.join(r, nm)
            if not os.path.islink(p):
                continue
            try:
                t = os.path.realpath(p)
            except OSError:
                continue
            if t.startswith(os.path.realpath(pkg) + os.sep):   # 两端都 realpath（macOS /var→/private/var 会让裸前缀假阴性）
                out.append({"file": p, "line": 0, "form": "端Skill链进包内投影(违源唯一)",
                            "path_value": t, "snippet": "%s -> %s" % (p.replace(home + os.sep, "~/"), t.replace(home + os.sep, "~/"))})
    return out


TEN = ["awaken-memory-system", "clock-loop", "daily-buddy", "good-good-study", "growth-box",
       "meta-aletheia", "shall-we-talk", "sucair", "system-logger", "triwich"]


def scan_rules_links(base_home=None, base_archive=None):
    """判据⑤·rules 面（2026-10-05 补·本卷挂账「skills 面已治·rules 面漏网」的根治腿）。

    各端 rules 常驻注入目录（~/.*/rules/*.md|.mdc）的软链必须落进档案真源。抓四种错：
      ① 断链（链在·目标不在）② 链出档案（指向端内私产=改源不抵端）
      ③ 同名跨端指向不同真源（十端共读同一文件=必同一真源）
      ④ 实体副本与「他端所链真源」同名（吃不到源更新·双源漂移）
    真源名集**由链的落点自推**（⛔不写死档案目录清单——写死=下一处新域必漏，
    与本卷判据③b 影子树同病根）。
    ⛔ 不判端专属实体（core-identity／cross-end-guard／doenglingz-core 按 AGENTS.md
       是端专属合法实体·不同名于档案真源即不入报）。
    返回 (hits, strict_only)：strict_only=断链类，属他端资产，默认显形不判红。"""
    home = base_home or HOME
    arc = os.path.realpath(base_archive or ARCHIVE)
    import glob as _glob
    roots = [p for p in _glob.glob(os.path.join(home, ".*/rules")) if os.path.isdir(p)]
    links, ents = {}, []
    for r in roots:
        for nm in sorted(os.listdir(r)):
            if not nm.endswith((".md", ".mdc")):
                continue
            p = os.path.join(r, nm)
            if os.path.islink(p):
                links[p] = nm
            else:
                ents.append((p, nm))
    hits, strict = [], []
    targets = {}
    for p, nm in links.items():
        rp = os.path.realpath(p)
        rec = {"file": p, "line": 0, "path_value": rp,
               "snippet": "%s -> %s" % (p.replace(home + os.sep, "~/"), rp.replace(home + os.sep, "~/"))}
        if not os.path.exists(rp):
            rec["form"] = "rules链断目标缺失(他端资产·默认显形)"
            strict.append(rec)
        elif not rp.startswith(arc + os.sep):
            rec["form"] = "rules链出档案真源(违源唯一)"
            hits.append(rec)
        else:
            targets.setdefault(nm, set()).add(rp)
    for nm, s in sorted(targets.items()):          # ③ 同名多真源
        if len(s) > 1:
            hits.append({"file": "rules/" + nm, "line": 0, "form": "rules同名跨端指向不同真源",
                         "path_value": " | ".join(sorted(s)), "snippet": nm + " ×" + str(len(s))})
    canon = set(targets)                            # ④ 实体副本撞真源名
    # v1.9.0 端实体化白名单（2026-10-07 你定端哲学：本端系统文件本端实体化·不做软链·
    #   源更新吸收改由本端主动回流记账。Qoder CN 两件套合法实体，不判副本病）
    MATERIALIZED_OK = {".qoder-cn/rules/core-soul.md", ".qoder-cn/rules/core-user.md"}
    for p, nm in ents:
        if p.replace(home + os.sep, "~/") in MATERIALIZED_OK or p[len(home) + 1:] in MATERIALIZED_OK:
            continue
        if nm in canon:
            hits.append({"file": p, "line": 0, "form": "rules实体副本与档案真源同名(吃不到源更新)",
                         "path_value": nm, "snippet": p.replace(home + os.sep, "~/")})
    return hits, strict


def scan_ten_link_shape():
    """判据⑤扩面（2026-10-04 皮叔令「只管我这 10 个，软链一定做好」）：
    这 10 个自有 Skill 在任何端的形态必须是指向 技能配置 的软链。
    抓三种错：实体副本（吃不到源更新）／断链／指向非源（含链进发布库）。
    ⛔ 不抓"某端少装了几个"——数量是端的选择，不是形态错。"""
    out = []
    src_root = os.path.join(ARCHIVE, "技能配置")
    import glob as _glob
    roots = set()
    for pat in (".*/skills", ".config/*/skills", "Library/Application Support/*/skills"):
        roots.update(d for d in _glob.glob(os.path.join(HOME, pat)) if os.path.isdir(d))
    for r in sorted(roots):
        for nm in TEN:
            p = os.path.join(r, nm)
            src = os.path.join(src_root, nm)
            if not os.path.lexists(p) or not os.path.isdir(src):
                continue
            if os.path.islink(p):
                tgt = os.path.realpath(p)
                if not os.path.exists(p):
                    kind = "端Skill断链(真源已改名或删除)"
                elif tgt != os.path.realpath(src):
                    kind = "端Skill未指向真源"
                else:
                    continue
                out.append({"file": p, "line": 0, "form": kind, "path_value": os.readlink(p),
                            "snippet": "%s -> %s" % (p.replace(HOME + os.sep, "~/"), os.readlink(p))})
            else:
                out.append({"file": p, "line": 0, "form": "端Skill是实体副本(吃不到源更新)",
                            "path_value": p, "snippet": "非软链·实体目录：" + p.replace(HOME + os.sep, "~/")})
    return out


def scan_ghost_dirs():
    out = []
    for name in sorted(archive_child_names()):
        p = os.path.join(HOME, name)
        if os.path.islink(p) or not os.path.isdir(p):
            continue
        n, newest = 0, 0.0
        for sub, _, fs in os.walk(p):
            n += len(fs)
            for f in fs:
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(sub, f)))
                except OSError:
                    pass
        out.append({"name": name, "path": p, "files": n,
                    "newest": time.strftime("%Y-%m-%d %H:%M", time.localtime(newest)) if newest else "-"})
    return out


def fingerprint():
    """域内 .py 最大 mtime + 幽灵目录集合 的廉价指纹（纯 stat，不 AST 求值）。
    写盘必改 mtime ⇒ 任何源码变更都会翻转指纹；无变更 ⇒ 复用缓存判定，
    把每轮 Stop 的 31s AST 全扫降到 stat 级（成本随愿景②收敛）。"""
    mx = 0.0
    for tree in mount_domains():
        for root, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d not in SKIP_DIR]
            for fn in files:
                if fn.endswith(".py"):
                    try:
                        mx = max(mx, os.stat(os.path.join(root, fn)).st_mtime)
                    except OSError:
                        pass
    import hashlib
    # 版本入指纹（2026-10-05 实测：v1.6→v1.7 加了 rules 面，旧缓存无新键 ⇒ 消费侧 KeyError，
    #  而指纹只看 mtime+幽灵名集，判据改版它认不出来）
    key = "v%s|%.6f|%s" % (__version__, mx, ",".join(sorted(g["name"] for g in scan_ghost_dirs())))
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def verdict_cached():
    """有指纹缓存则复用，避免每轮全量 AST 扫描（缓存仅存判定摘要，不改判据强度）。"""
    fp = fingerprint()
    try:
        c = json.load(open(CACHE, encoding="utf-8"))
        if c.get("fp") == fp and isinstance(c.get("verdict"), dict):
            v = dict(c["verdict"])
            v["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
            v["cached"] = True
            return v
    except (OSError, ValueError):
        pass
    v = verdict()
    v["cached"] = False
    try:
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        slim = {k: v[k] for k in v if k not in ("cached", "ts")}   # 排除法（白名单=新键必漏·同族病）
        json.dump({"fp": fp, "verdict": slim}, open(CACHE, "w", encoding="utf-8"))
    except OSError:
        pass
    return v


def verdict():
    rules_hits, rules_soft = scan_rules_links()
    hits = (scan_tree() + scan_raw_tilde() + scan_skill_links() + scan_ten_link_shape()
            + rules_hits + (rules_soft if RULES_STRICT else []))
    ghosts = scan_ghost_dirs()
    return {"version": __version__, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "archive_root": ARCHIVE, "residue_hits": len(hits), "ghost_dirs": len(ghosts),
            "rules_surface": {"hits": len(rules_hits), "advisory_breaks": len(rules_soft),
                              "strict": bool(RULES_STRICT)},
            "detail": hits, "ghost_detail": ghosts,
            "advisory_detail": [] if RULES_STRICT else rules_soft,
            "rc": 1 if (hits or ghosts) else 0}


def self_test():
    """双向验证：正例必绿 + 三类负例必红 + 变异体（短路不变量后 T3 应消失=判据真在做事）。"""
    import shutil
    import tempfile
    base = tempfile.mkdtemp(prefix="pltg-")
    global HOME, ARCHIVE, LIVE_TREES
    backup = (HOME, ARCHIVE, LIVE_TREES)
    fake_home = os.path.join(base, "home")
    fake_arc = os.path.join(fake_home, "~/个人AI档案")
    center = os.path.join(fake_arc, "脚本中心")
    os.makedirs(os.path.join(center, "logs", "runtime"), exist_ok=True)
    # ⚠️ 必须连环境变量 HOME 一起重定向：os.path.expanduser("~") 走的是进程 HOME，
    #    只改模块变量会让夹具自己骗自己（T3 首跑假阴性即此因·自测验的是真求值链）
    _old_env_home = os.environ.get("HOME")
    os.environ["HOME"] = fake_home
    HOME, ARCHIVE, LIVE_TREES = fake_home, fake_arc, [center]
    ok = 0
    FIXT = os.path.expanduser("~/脚本中心/_absent_x")
    results = []
    try:
        def write(rel, text):
            p = os.path.join(center, rel)
            os.makedirs(os.path.dirname(p) or center, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)

        write("good/a.py", 'LEDGER = os.path.expanduser("~/脚本中心/logs/runtime/x.jsonl")\n')
        n1 = len([h for h in scan_tree() if h["file"].endswith("good/a.py")])
        results.append(("T1 正例·合法落点零命中", n1 == 0, "命中%d" % n1))

        write("bad_a.py", 'LEDGER = os.path.expanduser("~/脚本中心/logs/runtime/x.jsonl")\n')
        n2 = len([h for h in scan_tree() if h["file"].endswith("bad_a.py")])
        results.append(("T2 负例·丢前缀字面量必红", n2 >= 1, "命中%d" % n2))

        write("bad_b.py", 'OUT_DIR = os.path.join(os.path.expanduser("~"), '
                          'os.path.expanduser("~"), "脚本中心", "logs", "runtime")\n')
        n3 = len([h for h in scan_tree() if h["file"].endswith("bad_b.py")
                  and h["form"].startswith("落点解析到家根")])
        results.append(("T3 负例·双expanduser到家根必红", n3 >= 1, "命中%d" % n3))

        os.makedirs(os.path.join(fake_home, "脚本中心", "logs"), exist_ok=True)
        with open(os.path.join(fake_home, "脚本中心", "logs", "x.log"), "w") as f:
            f.write("1")
        g = scan_ghost_dirs()
        results.append(("T4 负例·家根幽灵目录必红", any(d["name"] == "脚本中心" for d in g),
                        "检出%d" % len(g)))

        _orig = globals()["_is_home_child"]
        globals()["_is_home_child"] = lambda p: False
        n5 = len([h for h in scan_tree() if h["file"].endswith("bad_b.py")
                  and h["form"].startswith("落点解析到家根")])
        globals()["_is_home_child"] = _orig
        results.append(("T5 变异体·短路不变量后T3判据应消失", n5 == 0, "短路后命中%d" % n5))

        # T6 负例：裸 ~/ 常量进 open ⇒ 判据④必红
        write("bad_raw.py", "SLICES = \"" + FIXT + "\"\ndef load():\n    return open(SLICES).read()\n")
        r6 = [h for h in scan_raw_tilde() if h["file"].endswith("bad_raw.py")]
        results.append(("T6 负例·裸~常量进fs操作必红", len(r6) >= 1, "命中" + str(len(r6))))
        # T7 正例：同串经 expanduser ⇒ 不误报
        write("good_raw.py", "SLICES = os.path.expanduser(\"" + FIXT + "\")\ndef load():\n    return open(SLICES).read()\n")
        r7 = [h for h in scan_raw_tilde() if h["file"].endswith("good_raw.py")]
        results.append(("T7 正例·expanduser包裹不误报", len(r7) == 0, "命中" + str(len(r7))))
        # T8 变异：短路判据④后 T6 必须消失（证明判据真在做事，非恒红）
        _o = globals()["scan_raw_tilde"]
        globals()["scan_raw_tilde"] = lambda: []
        r8 = [h for h in scan_raw_tilde() if h["file"].endswith("bad_raw.py")]
        globals()["scan_raw_tilde"] = _o
        results.append(("T8 变异体·短路判据④后T6应消失", len(r8) == 0, "短路后命中" + str(len(r8))))
        # T17-T20 判据④ v1.8 扩面双向自测：注入必红 + 撤除必绿（交接卡§三·1 验收前置）
        write("bad_concat.py", "from pathlib import Path\nP = Path.home() / \"~/~/[记忆共享中心]/工作日志/x.md\"\ndef load():\n    return P.read_text()\n")
        r17 = [h for h in scan_raw_tilde() if h["file"].endswith("bad_concat.py")]
        results.append(("T17 负例·Path.home()拼接裸~必红", len(r17) >= 1, "命中" + str(len(r17))))
        write("good_concat.py", "from pathlib import Path\nP = Path.home() / \"~/[记忆共享中心]/工作日志/x.md\"\ndef load():\n    return P.read_text()\n")
        r18 = [h for h in scan_raw_tilde() if h["file"].endswith("good_concat.py")]
        results.append(("T18 正例·home()合法拼接不误伤", len(r18) == 0, "命中" + str(len(r18))))
        write("bad_tuple.py", "from pathlib import Path\nCANDS = (Path.home() / \"记忆共享中心\", \"~/个人AI档案\")\ndef pick():\n    return [c for c in CANDS if c.is_dir()]\n")
        r19 = [h for h in scan_raw_tilde() if h["file"].endswith("bad_tuple.py")]
        results.append(("T19 负例·home()候选元组混入裸~必红", len(r19) >= 1, "命中" + str(len(r19))))
        for _f in ("bad_concat.py", "bad_tuple.py"):
            os.remove(os.path.join(center, _f))
        r20 = [h for h in scan_raw_tilde() if h["file"].endswith(("bad_concat.py", "bad_tuple.py"))]
        results.append(("T20 双向·撤除注入文件后命中必消失", len(r20) == 0, "残余" + str(len(r20))))
        # T9 负例：端 Skill 软链进 发布库 ⇒ 判据⑤必红（夹具自造一条假链）
        pkgf = os.path.join(fake_arc, "发布库", "五层记忆系统", "包", "references", "skills", "fakeskill")
        os.makedirs(pkgf, exist_ok=True)
        destroot = os.path.join(fake_home, ".fakeend", "skills")   # 须落在 ~/.*/skills 模式内
        os.makedirs(destroot, exist_ok=True)
        os.symlink(pkgf, os.path.join(destroot, "fakeskill"))
        _md2 = globals()["mount_domains"]
        globals()["mount_domains"] = lambda: [os.path.dirname(destroot)]
        r9 = scan_skill_links()
        globals()["mount_domains"] = _md2
        results.append(("T9 负例·端Skill链进包内必红", any("fakeskill" in h["file"] for h in r9), "命中" + str(len(r9))))
        # T10 负例：10 个自有 Skill 中某端出现实体副本 ⇒ 判据⑤扩面必红
        t10 = os.path.join(fake_home, ".fakeend2", "skills", "triwich")
        os.makedirs(t10, exist_ok=True)
        open(os.path.join(t10, "SKILL.md"), "w").write("# fake")
        _sr = os.path.join(fake_arc, "技能配置", "triwich")
        os.makedirs(_sr, exist_ok=True)
        open(os.path.join(_sr, "SKILL.md"), "w").write("# src")
        r10 = [h for h in scan_ten_link_shape() if h["file"] == t10]
        results.append(("T10 负例·自有Skill实体副本必红", len(r10) >= 1, "命中" + str(len(r10))))
        # T11 出厂自检·A 型空参退化必红（求值器自证；2026-10-04 Hermes 指控本件判据①不认 A 型，实测成立）
        a11 = os.path.join(center, "probe_typeA.py")   # 探针须在 LIVE_TREES 内，否则 scan_tree 走不到（首版放 base ⇒ 假阴性）
        open(a11, "w", encoding="utf-8").write("REPO = os.path.join(os.path.expanduser(\"~\"), )\nopen(REPO + \"/x.log\", \"a\")\n")
        n11 = len([h for h in scan_tree() if h["file"] == a11])  # 走真判据链路，不手工调函数
        results.append(("T11 出厂自检·A型空参退化必红", n11 >= 1, "命中" + str(n11)))

        # T12-T16 判据⑤ rules 面（v1.7 新增·每种错形各一条负例 + 一条防误伤正例）
        def rules_fixture():
            rh = os.path.join(base, "rh%d" % len(results))
            ra = os.path.join(rh, "~/个人AI档案")
            os.makedirs(os.path.join(ra, "记忆规则"), exist_ok=True)
            open(os.path.join(ra, "记忆规则", "shared.md"), "w", encoding="utf-8").write("# src")
            os.makedirs(os.path.join(rh, ".endA", "rules"), exist_ok=True)
            os.makedirs(os.path.join(rh, ".endB", "rules"), exist_ok=True)
            return rh, ra

        rh, ra = rules_fixture()          # T12 链出档案
        open(os.path.join(rh, "outside.md"), "w").write("# 私产")
        os.symlink(os.path.join(rh, "outside.md"), os.path.join(rh, ".endA", "rules", "o.md"))
        r12 = scan_rules_links(rh, ra)
        results.append(("T12 负例·rules链出档案必红",
                        any(h["form"].startswith("rules链出档案") for h in r12[0]), str(len(r12[0]))))

        rh, ra = rules_fixture()          # T13 同名跨端指向不同真源（两份都必须在档案内）
        open(os.path.join(ra, "记忆规则", "shared_alt.md"), "w", encoding="utf-8").write("# 另一份真源")
        os.symlink(os.path.join(ra, "记忆规则", "shared.md"), os.path.join(rh, ".endA", "rules", "x.md"))
        os.symlink(os.path.join(ra, "记忆规则", "shared_alt.md"), os.path.join(rh, ".endB", "rules", "x.md"))
        r13 = scan_rules_links(rh, ra)
        results.append(("T13 负例·同名跨端不同真源必红",
                        any(h["form"].startswith("rules同名跨端") for h in r13[0]), str(len(r13[0]))))

        rh, ra = rules_fixture()          # T14 实体副本撞真源名
        os.symlink(os.path.join(ra, "记忆规则", "shared.md"), os.path.join(rh, ".endA", "rules", "shared.md"))
        os.makedirs(os.path.join(rh, ".endB", "rules"), exist_ok=True)
        open(os.path.join(rh, ".endB", "rules", "shared.md"), "w").write("# 副本")
        r14 = scan_rules_links(rh, ra)
        results.append(("T14 负例·rules实体副本撞真源名必红",
                        any(h["form"].startswith("rules实体副本") for h in r14[0]), str(len(r14[0]))))

        rh, ra = rules_fixture()          # T15 断链=advisory（不判红）
        os.symlink(os.path.join(ra, "记忆规则", "gone.md"), os.path.join(rh, ".endA", "rules", "gone.md"))
        h15, s15 = scan_rules_links(rh, ra)
        results.append(("T15 负例·rules断链进advisory且不入hits（他端资产不代定红）",
                        len(s15) == 1 and len(h15) == 0, "hits%d/adv%d" % (len(h15), len(s15))))

        rh, ra = rules_fixture()          # T16 正例·全软链同真源 ⇒ 零命中（防误伤）
        for e in (".endA", ".endB"):
            os.symlink(os.path.join(ra, "记忆规则", "shared.md"),
                       os.path.join(rh, e, "rules", "shared.md"))
        h16, s16 = scan_rules_links(rh, ra)
        results.append(("T16 正例·合规 rules 面不误伤", h16 == [] and s16 == [],
                        "hits%d/adv%d" % (len(h16), len(s16))))
        for name, passed, info in results:
            print("%s %s (%s)" % ("✅" if passed else "❌", name, info))
            ok += 1 if passed else 0
    finally:
        HOME, ARCHIVE, LIVE_TREES = backup
        if _old_env_home is not None:
            os.environ["HOME"] = _old_env_home
        else:
            os.environ.pop("HOME", None)
        shutil.rmtree(base, ignore_errors=True)
    total = len(results)      # 分母取自实收夹具（原写死 total=11·加例即假红·2026-10-05 实测）
    print("自测 %d/%d" % (ok, total))
    return 0 if ok == total else 1


def _log(v):
    """留痕：任何模式（含 --report）都必须落一行——上一版 --report 提前 return 导致
    正凭证缺失，验收讫时只能靠宿主日志反推（2026-10-04 实测误判一次）。"""
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": v["ts"], "residue": v["residue_hits"],
                                "ghost": v["ghost_dirs"], "rc": v["rc"],
                                "cached": v.get("cached", False)}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main(argv):
    global RULES_STRICT
    RULES_STRICT = "--rules-strict" in argv
    if "--self-test" in argv:
        return self_test()
    v = verdict_cached()
    if "--json" in argv:
        print(json.dumps(v, ensure_ascii=False))
    elif "--report" in argv:
        _log(v)
        if v.get("advisory_detail"):
            print("⚪[rules面·显形不判红] %d 条断链（⛔不代他端定红·翻硬请 --rules-strict）：%s"
                  % (len(v.get("advisory_detail", [])),
                     ", ".join(h["file"].replace(HOME + os.sep, "~/") for h in v.get("advisory_detail", [])[:3])))
        if v["rc"] == 0:
            return 0
        line = "⚠️[落点真值守卫 v%s] 丢前缀残留%d处 / 家根幽灵目录%d个" % (
            v["version"], v["residue_hits"], v["ghost_dirs"])
        if v["ghost_detail"]:
            line += "｜幽灵 %s" % " ".join(g["name"] for g in v["ghost_detail"])
        if v["detail"]:
            t = v["detail"][0]
            line += "｜首条 %s:%s" % (os.path.basename(t["file"]), t["line"])
        print(line)
        return 0
    else:
        print("记忆根=%s  残留=%d  幽灵目录=%d" % (ARCHIVE, v["residue_hits"], v["ghost_dirs"]))
        for g in v["ghost_detail"]:
            print("  [幽灵] %s  文件%s个 最新=%s" % (g["path"], g["files"], g["newest"]))
        for h in v["detail"][:40]:
            print("  %-70s L%-5s %s" % (h["file"].replace(ARCHIVE + os.sep, ""),
                                        h["line"], h["form"]))
        if v["residue_hits"] > 40:
            print("  …余%d处（--json 取全量）" % (v["residue_hits"] - 40))
    _log(v)
    return v["rc"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
