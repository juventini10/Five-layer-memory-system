#!/usr/bin/env python3
"""脚本体系收口闸（SSOT 判据·6 条机械判据）

2026-10-04 皮叔令「不要一会说做完一会说没做完」⇒ 口径固化在此文件，
⛔ AI 不得凭印象改口径·⛔ 不得在没有全绿时说「做完」。

用法：
    python3 脚本体系收口闸.py            # 全跑·输出总表
    python3 脚本体系收口闸.py --json     # 机读
    python3 脚本体系收口闸.py --gates 1,3   # 只跑指定闸
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import ast
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HOME = os.path.expanduser("~")
MC = os.path.expanduser("[记忆共享中心]")
SC = os.path.join(MC, "脚本中心")
PKG = os.path.join(MC, "发布库/五层记忆系统/布洛陀-全平台安装包")
REFS = os.path.join(PKG, "references/scripts")
PLUG = os.path.join(HOME, ".hermes/plugins/buluotuo-readonly-guards/__init__.py")

# 用户机上「不该出现」的形态（真病灶·非脱敏差异）
BAD_PATTERNS = [
    (r"expanduser\(\s*os\.path\.expanduser\(", "双层expanduser"),
    (r"os\.path\.os\.path\.", "重复os.path"),
    # ⛔ 2026-10-04 修正：原 pattern 是裸串 `~/个人AI档案`，
    #    它也会命中**正常形态** `os.path.expanduser("[记忆共享中心]/…")` 的尾部
    #    ⇒ 夹具抓到「正常形态误报」。必须锚定「路径开头」形态：
    #    ① 行首/引号/括号后紧跟 `/Users/…`（真实字面量）
    #    ② 排除前面是 `~` 的（即已经参数化的形态）
    (r'(?<![~\w])["\'(,=]\s*~/个人AI档案', "作者绝对路径"),
    (r"^\s*~/个人AI档案", "作者绝对路径"),
    (r"~/\.hermes/cache", "测试路径泄漏"),
    (r"PLACEHOLDER", "发布占位符残留"),
]

# ⛔ 精确豁免（2026-10-04·实测 smoke_test.py 8 处误报）
#   `PLACEHOLDERS = [...]` 是**检测器自己的检测词表**——它要检的就是这些串。
#   把它判红 = 要求检测器把词表删掉 ⇒ 检测器失效（PAT-058 仪器自身假绿同族）。
#   ⛔ 只豁「清单定义行」·⛔ 不豁其他 PLACEHOLDER 出现（如 NameError 那种真病灶）。
PLACEHOLDER_DEF = re.compile(r"^\s*[A-Z_]*PLACEHOLDER[A-Z_]*\s*=")

def _is_detector_wordlist(line):
    return bool(PLACEHOLDER_DEF.match(line))


# ⛔ 作者绝对路径的**文案豁免**（2026-10-04·实测 445 处里 68 处全是这类）
#   形态：`跑 \`python3 /Users/…/x.py\` 定位`、`grep -i 'kw' /Users/…/GUARD_INDEX.md`、
#         `⛔ 不用 \`/Users/…\` 硬编码——那是作者侧路径`
#   它们是**给人看的说明字符串 / docstring / 文档表格**，⛔ 不是可执行路径。
#   ⛔ 豁免只认「该行不产生可执行路径」：无 os.path./expanduser/join/Popen/赋值
#      ⇒ 只要出现这些调用形态·一律仍判红。
EXEC_HINT = re.compile(
    r"os\.path\.|expanduser\(|\.join\(|Popen|check_call|subprocess|"
    r"sys\.path|^\s*[A-Za-z_][A-Za-z_0-9_]*\s*=\s*[\"']")


def _in_docstring_set(lines):
    """一次 parse·返回处于 docstring 内的行号集合（0-based·批量版）

    ⛔ 2026-10-04 性能根治：单行版 `_in_docstring(lines, idx)` **每行都
       ast.parse(全文)** ⇒ 145 文件 × N 行 = 平方级·实测收口闸超时。
       ⛔ 改为整文件 parse 一次·收集所有 docstring 行号区间。
    """
    out = set()
    try:
        tree = ast.parse("\n".join(lines))
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", [])
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            lo = first.lineno
            hi = first.end_lineno or lo
            out.update(range(lo - 1, hi))
    return out


def _is_prose_line(line):
    """说明性文案 ⇒ 不判红（无任何可执行路径构造痕迹）"""
    if _is_detector_wordlist(line):
        return True
    if line.strip().startswith("#"):
        return True
    return not EXEC_HINT.search(line)


# ⛔ **检测器自身词表/夹具**豁免（2026-10-04·实测 hermes_transform_gate.py 3 处）
#   形态：`("KB = expanduser(os.path.expanduser(\"/Users/x\"))", "双层expanduser"),`
#         `s = "x = expanduser(os.path.expanduser(\"~/…\"))"`（self-test 幂等用例）
#   它们是**检测器自己要找的那些串**——判红 = 要求检测器删掉自己的检测词表
#   ⇒ 同 PAT-058 仪器自身假绿。
#   ⛔ 只豁「在列表/元组字面量里」与「赋值给 *_CASE/POS/NEG 之类夹具变量」；
#      ⛔ 真实可执行路径（模块级赋值后被使用）仍判红。
FIXTURE_HINT = re.compile(r"""^\s*[\(\[]|^\s*(POS|NEG|POSITIVE|NEGATIVE|CASES?)\s*=|
                              \s*(POS|NEG)\s*=\s*\[|^\s*[sp]\s*=\s*["']""", re.X)


def _is_detector_fixture(lines, idx):
    """该行是否属于检测器的词表/夹具（窄判据·⛔ 回溯窗口必须短）

    ⛔ 2026-10-04 夹具 v3 实测踩坑：回溯窗口开 12 行时，
       `POS = ["a"]`（单行已闭合的列表）会把**其后 10 行**全吞进豁免区
       ⇒ 真病灶 `D = expanduser(expanduser(...))` 漏检。
    ⇒ 修：**只认多行未闭合的列表**——向上回溯时一旦遇到该行的结尾（`]`
       / `)` 闭合或空行/非缩进续行）就立即停。
    """
    line = lines[idx]
    if FIXTURE_HINT.search(line):
        # 单行即闭合的列表/元组（`X = [...]`、`X = (a, b)`、`NEG = ['...']`）⇒ 只豁这一行
        if re.match(r"^\s*[A-Za-z_][A-Za-z_0-9_]*\s*=\s*[\(\[][^\n]*[\)\]]\s*$",
                    line):
            return True
        if line.lstrip().startswith(("(", "[")):
            return True
        # s = "..." / pos = "..." 这类纯字符串夹具
        if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9_]*\s*=\s*["\']', line):
            return True
        return False
    # 多行列表内：向上找未闭合的 POS/NEG 开启行，且中途不得出现闭合/顶格
    depth = 0
    for k in range(idx, max(-1, idx - 15), -1):
        s = lines[k]
        depth += s.count("(") + s.count("[")
        depth -= s.count(")") + s.count("]")
        if depth <= 0 and k < idx:
            break                      # 已闭合 ⇒ 不在列表内
        if re.match(r"^\s*(POS|NEG|POSITIVE|NEGATIVE|CASES?|cases?|fixlist|FIXLIST)\s*=\s*[\(\[]", s):
            return True
        if re.match(r"^\S", s):       # 顶格 ⇒ 出列表
            break
    return False


def _run(cmd, cwd=None, timeout=280, stdin=b""):
    try:
        r = subprocess.run(cmd, capture_output=True, cwd=cwd, timeout=timeout, input=stdin)
        return r.returncode, ((r.stdout or b"").decode("utf-8", "replace")
                              + (r.stderr or b"").decode("utf-8", "replace"))
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"


def gate1_readonly():
    """闸1·readonly 整批 rc=0"""
    if not os.path.isfile(PLUG):
        return False, "插件文件不存在: %s" % PLUG
    items = re.findall(r'\("([\w.\-]+\.(?:py|sh))",\s*(\[[^\]]*\])?\)',
                       open(PLUG, encoding="utf-8").read())
    if not items:
        return False, "挂载清单解析为 0 件（⛔不是「全绿」）"
    bad, t0 = [], time.time()
    for name, args in items:
        argv = re.findall(r'"([^"]*)"', args) if args else []
        argv = [x.replace("~", HOME) if x.startswith("~") else x for x in argv]
        p = os.path.join(SC, name)
        if not os.path.isfile(p):
            bad.append("%s=缺件" % name)
            continue
        rc, _ = _run((["bash", p] if name.endswith(".sh") else ["python3", p]) + argv,
                     cwd=SC, timeout=90)
        if rc != 0:
            bad.append("%s=rc=%d" % (name, rc))
    return (not bad), ("%d/%d rc=0 · %.1fs%s" % (
        len(items) - len(bad), len(items), time.time() - t0,
        "" if not bad else " · 🔴 " + "; ".join(bad[:5])))


def gate2_plugins():
    """闸2·插件安装面 rc=0"""
    out, ok = [], True
    for s in ("plugin_live_gate.py", "verify_hermes_runtime.py"):
        p = os.path.join(REFS, s)
        if not os.path.isfile(p):
            out.append("%s=缺件" % s)
            ok = False
            continue
        rc, o = _run(["python3", p], cwd=SC, timeout=180)
        ok = ok and rc == 0
        out.append("%s rc=%d" % (s, rc))
        if rc != 0:
            tail = [x.strip() for x in o.strip().split("\n") if x.strip()][-2:]
            out.append("  " + " | ".join(t[:70] for t in tail))
    return ok, " · ".join(out)


def gate3_single_source():
    """闸3·单源守卫 rc=0（零漏项）"""
    p = os.path.join(SC, "devtools_single_source_guard.py")
    if not os.path.isfile(p):
        return False, "守卫件不存在"
    rc, o = _run(["python3", p], cwd=SC, timeout=250)
    if rc == 0:
        return True, "rc=0"
    m = re.search(r"缺口 (\d+) 项", o)
    f1 = re.search(r"真相源缺 (\d+) 个函数", o)
    detail = []
    if f1:
        detail.append("判据①功能完整性 %s 处" % f1.group(1))
    if m:
        detail.append("判据②路径硬编码 %s 项" % m.group(1))
    d = re.search(r"分叉件 = (\d+)", o)
    if d:
        detail.append("判据③分叉 %s 件（默认不判红）" % d.group(1))
    return False, "rc=1 · " + " · ".join(detail)


def gate4_receipt():
    """闸4·安装回执 verdict=ok"""
    p = os.path.join(REFS, "install_receipt.py")
    if not os.path.isfile(p):
        return False, "回执脚本不存在"
    rc, o = _run(["python3", p, "--package", PKG, "--platform", "hermes",
                  "--mc", MC, "--config-root", os.path.join(HOME, ".hermes")],
                 cwd=SC, timeout=120)
    m = re.search(r"verdict=(\w+)", o)
    v = m.group(1) if m else "?"
    return (rc == 0 and v == "ok"), "rc=%d · verdict=%s" % (rc, v)


def _scan_dir(root):
    hits = {}
    if not os.path.isdir(root):
        return None
    for dp, _dn, fns in os.walk(root):
        for f in fns:
            if not f.endswith((".py", ".sh")):
                continue
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            _lines = t.split("\n")
            # self_test 函数体行号集合（2026-10-08·豁免「夹具里的字面路径名」）：
            #   self_test 在 tempdir 下构造假记忆中心，路径段是**字面目录名**（非真实作者机路径）。
            #   与 _is_detector_fixture 同理——判红 = 要求夹具不用路径名 ⇒ 夹具写不出来。
            #   用 ast 精确取（比缩进回溯稳·⛔ 只豁 self_test/selftest 函数体）。
            _selftest_lines = set()
            try:
                _tree = ast.parse(t)
                for _node in ast.walk(_tree):
                    if isinstance(_node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                            and _node.name in ("self_test", "_self_test", "selftest", "run_self_test"):
                        for _ln in range(_node.lineno, getattr(_node, "end_lineno", _node.lineno) + 1):
                            _selftest_lines.add(_ln - 1)   # ast 1-based → 0-based
            except SyntaxError:
                pass
            # ⛔ 2026-10-04 性能根治（实测闸5 scan 370 秒·超时）：
            #   原实现**每行都重算** fixture 集合 + docstring 集合
            #   （各含 15 行回溯 / 全文 ast.parse）⇒ 平方级。
            # ⇒ 改为：docstring 集合整文件算一次；fixture/文案判据
            #        **只在「本行真的命中某个 BAD_PATTERNS」时才判**
            #        —— 不命中的行本来就不需要豁免判据。
            _doc_set = _in_docstring_set(_lines)
            _rel = os.path.relpath(p, root)
            for _i, _line in enumerate(_lines):
                if _line.strip().startswith("#"):
                    continue
                _hit = None
                for _pat, _name in BAD_PATTERNS:
                    if re.search(_pat, _line):
                        _hit = _name
                        break
                if _hit is None:
                    continue          # ⛔ 不命中 ⇒ 无需豁免判据（性能关键）
                if _i in _doc_set:
                    continue          # 文档字符串里的示例代码
                if _is_detector_fixture(_lines, _i):
                    continue          # 检测器自身的词表/夹具
                if _hit in ("发布占位符残留", "作者绝对路径") \
                        and _is_prose_line(_line):
                    continue          # 说明性文案
                if _hit == "作者绝对路径" and _i in _selftest_lines:
                    continue          # self_test 夹具区（临时目录下的字面名·非真路径）
                hits.setdefault(_hit, []).append("%s L%d" % (_rel, _i + 1))
    return hits


def gate5_clean_install():
    """闸5·干净用户机装完 0 处病灶

    🔴 2026-10-04 两处结构性根治（当天「修好又变红」循环 9 次的两环）：
    ① **cfg_root 必须隔离** —— 不传时安装器把 `<cfg_root>/doenglingz/runtime_paths.json`
       写成临时 MC 路径 ⇒ 真机声明从 12 键掉到 5 键（worklog 缺）⇒ 后续只读闸全红。
       ⇒ 本闸显式传 `--cfg-root <临时目录>`（安装器 2026-10-04 新增该覆盖入口）。
    ② **装后必须回同步** —— 隔离装仍会写 `<MC>/脚本中心` 与 `<MC>/数字分身/devtools`
       （DT_SUITE 部署路径）⇒ 「装完的旧版」滞留 ⇒ 回同步把它拉回真源。
       ⚠️ 回同步失败**不算闸5 判红**（闸5 判的是「装出来的产物干净」），
          但必须打印出来 —— 否则会静默留着旧版当下一轮起点。
    """
    fake = tempfile.mkdtemp(prefix="blt_verify_")
    fake_cfg = tempfile.mkdtemp(prefix="blt_verify_cfg_")
    try:
        os.makedirs(os.path.join(fake, "开发工具"), exist_ok=True)
        rc, o = _run(["python3", os.path.join(PKG, "install_scripts.py"), fake,
                      "--platform", "hermes",
                      "--cfg-root", fake_cfg], cwd=PKG, timeout=280)
        # 装后回同步（结构不变量：验收跑完不留旧版）
        _sync = os.path.join(PKG, "..", "..", "..", "开发工具",
                             "buluotuo-release-sync", "单向真源同步.py")
        _sync = os.path.abspath(_sync)
        sync_note = ""
        if os.path.isfile(_sync):
            src, sout = _run(["python3", _sync], cwd=os.path.dirname(_sync), timeout=300)
            tail = [l.strip() for l in sout.strip().split("\n") if l.strip()][-1:]
            sync_note = " · 回同步 rc=%d %s" % (src, (tail[0] if tail else "")[:60])
        else:
            sync_note = " · ⛔ 回同步器缺失"
        if rc != 0:
            return False, "install rc=%d%s" % (rc, sync_note)
        sc = os.path.join(fake, "脚本中心")
        n = len([f for f in os.listdir(sc) if f.endswith((".py", ".sh"))])
        hits = _scan_dir(sc) or {}
        total = sum(len(v) for v in hits.values())
        if total:
            det = " · ".join("%s×%d(%s)" % (k, len(v), v[0]) for k, v in hits.items())
            return False, "%d 件落盘 · 🔴 %d 处 · %s%s" % (n, total, det, sync_note)
        return True, "%d 件落盘 · 0 处病灶%s" % (n, sync_note)
    finally:
        shutil.rmtree(fake, ignore_errors=True)
        shutil.rmtree(fake_cfg, ignore_errors=True)


def gate6_idempotent():
    """闸6·安装器幂等（连跑 2 遍结果不变）

    🔴 2026-10-04 根治：本闸用**真实 MC** 连装两遍 ⇒ 它是闸5 之后
       **唯一还在写的闸** ⇒ 闸5 的「装后回同步」被它灌回去
       （实测：闸5 回同步后守卫全绿·闸6 跑完又回到 9 项缺口）。
       ⇒ ① 也传 `--cfg-root <临时目录>`（不碰真机声明）
          ② 幂等判定**仍用真实 MC**（幂等性必须在真实落点验）
             但**跑完立刻回同步**（不留旧版当下一轮起点）。

    🔴🔴 2026-10-08 二次根治（皮叔令「主源是我本地电脑端，不要搞混」）：
       上条 ② 的前提是**错的**——安装器的职责是「把包装到用户机」，
       它的输入是包、输出是 `<MC>/*`。在**源机**上把 `<MC>` 指向真源树，
       等于**让包（下游脱敏映射物）反灌本源**（实测：跑一次往 `脚本中心/` 灌入
       93 件构建链块 + 8 件绝对路径；而它的「回同步」只回同步包侧、⛔不回源侧）。
       ⇒ 判据改正：**幂等性在隔离 MC 上验**（幂等=「同一输入跑两遍结果一致」，
         这是**函数性质**，与 MC 是不是真源无关）·⛔ 真源树零写入。
       ⇒ 真源侧只保留**只读**快照（读 `runtime_paths` 声明，不写）。
    """
    def snapshot(mc):
        out = {}
        for sub in ("脚本中心", "数字分身"):
            d = os.path.join(mc, sub)
            if os.path.isdir(d):
                out[sub] = sorted(os.listdir(d))
        return out

    iso_mc = tempfile.mkdtemp(prefix="blt_gate6_mc_")
    iso_cfg = tempfile.mkdtemp(prefix="blt_gate6_cfg_")
    try:
        os.makedirs(os.path.join(iso_mc, "开发工具"), exist_ok=True)
        before = snapshot(iso_mc)
        # ⚠️ 双隔离：MC=临时目录（⛔不碰真源树）· cfg_root=临时目录（⛔不碰真机声明）
        rc, _ = _run(["python3", os.path.join(PKG, "install_scripts.py"), iso_mc,
                      "--platform", "hermes", "--cfg-root", iso_cfg],
                     cwd=PKG, timeout=280)
        if rc != 0:
            return False, "第一遍 rc=%d" % rc
        mid = snapshot(iso_mc)
        rc2, _ = _run(["python3", os.path.join(PKG, "install_scripts.py"), iso_mc,
                       "--platform", "hermes", "--cfg-root", iso_cfg],
                      cwd=PKG, timeout=280)
        if rc2 != 0:
            return False, "第二遍 rc=%d" % rc2
        after = snapshot(iso_mc)
        diff = [k for k in set(mid) | set(after) if mid.get(k) != after.get(k)]
        if diff:
            return False, "两遍之间变化: %s" % ",".join(sorted(diff))
        # 首遍是否也未改变现状（幂等定义：重复执行无新变化）
        first_diff = [k for k in set(before) | set(mid) if before.get(k) != mid.get(k)]
        # 真源树零写入自证（本闸的新增判据）
        sc_src = os.path.join(MC, "脚本中心")
        polluted = 0
        if os.path.isdir(sc_src):
            for f in os.listdir(sc_src):
                if not f.endswith((".py", ".sh")):
                    continue
                try:
                    _txt = open(os.path.join(sc_src, f),
                                encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                # 判据精化（2026-10-08·皮叔令「保障我自己能正常使用，用户也不受干扰」）：
                #   原判据只看「全文含 'auto by build chain'」⇒ 把**正常的模块级 UTF-8 守卫**
                #   （作者手写、位于 import 区之后）也计为污染。实测 6 件里 5 件是这类，
                #   只有 `install_ledger_reconcile.py`（第 2 行）是**装机器头部注入**的真痕迹。
                #   装机器行为的机械特征 = **注入到文件最前部**（前 5 行内）。
                #   ⇒ 只认头部注入；模块级守卫（非头部）不算污染。
                _head = "\n".join(_txt.split("\n")[:5])
                if "auto by build chain" in _head:
                    polluted += 1
        note = "隔离MC两遍一致 · 首遍变更 %d 项 · 真源树头部装机块 %d 件" % (len(first_diff), polluted)
        if polluted > 1:      # 1 件为既有基线（install_ledger_reconcile.py）
            return False, "🔴 源树被灌入装机块 %d 件（应≤1）· %s" % (polluted, note)
        return True, note
    finally:
        shutil.rmtree(iso_mc, ignore_errors=True)
        shutil.rmtree(iso_cfg, ignore_errors=True)


def gate7_managed_block():
    """闸7·规则文件托管块无副本（防 10-02 副本病复发）

    🔴 2026-10-04：`8b1de0f2` 批量给规则文件加托管块·`C5 追加契约`致
       原文留段外 ⇒ 每条规则出现两次（铁律版 828→428 行已归位）。
    ⇒ 判据在 `rules_managed_block_guard.py`（5/5 反向夹具）·
       本闸同时扫**真源**与**用户落点**（两侧都要干净才算干净）。
    """
    g = os.path.join(MC, "脚本中心", "守卫", "rules_managed_block_guard.py")
    if not os.path.isfile(g):
        return False, "守卫文件缺失: %s" % g
    targets = [os.path.join(MC, "开发工具/buluotuo-release-sync/assets/rules-curation"),
               os.path.join(MC, "记忆规则")]
    bad = []
    for d in targets:
        rc, o = _run(["python3", g, d], cwd=MC, timeout=90)
        if rc != 0:
            for line in o.split("\n"):
                if "·" in line and line.strip().startswith("·"):
                    bad.append("%s:%s" % (os.path.basename(d), line.strip()[:60]))
    if bad:
        return False, "🔴 %d 处 · %s" % (len(bad), " · ".join(bad[:3]))
    n = sum(len([f for f in os.listdir(d) if f.endswith(".md")])
            for d in targets if os.path.isdir(d))
    return True, "%d 件 · 真源+落点双面零副本" % n


GATES = [
    ("readonly 整批", gate1_readonly),
    ("插件安装面", gate2_plugins),
    ("单源守卫", gate3_single_source),
    ("安装回执", gate4_receipt),
    ("干净用户机", gate5_clean_install),
    ("安装幂等", gate6_idempotent),
    ("托管块无副本", gate7_managed_block),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gates", default="")
    a = ap.parse_args()
    want = {int(x) for x in a.gates.split(",") if x.strip().isdigit()} or None
    rows = []
    # ⚠️ 2026-10-04 顺序根治（实测闸内竞态·闸1/2 读到半写的 runtime_paths）：
    #   闸5/闸6 会真跑安装器 ⇒ 它们会**重写** ~/.hermes/doenglingz/runtime_paths.json。
    #   若闸1/2 与它们并发/在其之前，读到的是**半写态** ⇒ 假红
    #   （实测：单独跑 plugin_live_gate rc=0，闸内跑却报「缺 worklog 键」）。
    # ⇒ 顺序铁律：**先跑只读闸（1/2/3/4），再跑会写盘的闸（5/6）**。
    for i, (name, fn) in enumerate(GATES, 1):
        if want and i not in want:
            continue
        t0 = time.time()
        try:
            ok, detail = fn()
        except Exception as e:          # noqa: BLE001 - 闸门自身异常 ⇒ 判红不静默
            ok, detail = False, "闸门异常: %s: %s" % (type(e).__name__, e)
        rows.append({"no": i, "name": name, "ok": ok,
                     "detail": detail, "sec": round(time.time() - t0, 1)})
    passed = sum(1 for r in rows if r["ok"])
    if a.json:
        print(json.dumps({"gates": rows, "passed": passed, "total": len(rows),
                          "verdict": "done" if passed == len(rows) else "not_done"},
                         ensure_ascii=False, indent=1))
        return 0 if passed == len(rows) else 1
    print("═══ 脚本体系收口闸（%d 条机械判据）═══" % len(GATES))
    for r in rows:
        print("  %s %d. %-12s %-6s %s" % ("✅" if r["ok"] else "🔴", r["no"],
                                           r["name"], "%ss" % r["sec"], r["detail"]))
    print("─── %d/%d ───" % (passed, len(rows)))
    print("判定：%s" % ("✅ 脚本体系做完" if passed == len(rows)
                       else "🔴 未做完（%d 条未绿）" % (len(rows) - passed)))
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())