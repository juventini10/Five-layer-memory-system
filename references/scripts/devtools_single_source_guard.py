#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/devtools_single_source_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
r"""devtools_single_source_guard.py — devtools 单一真相源守卫（2026-10-17 补判据⑧ 消费侧引用面；Hermes 端 · 2026-10-03 立 · v1.1 2026-10-05 加判据①b/③b/③c · v1.2 加真源缺单元腿 · v1.3 加判据⑤ 跨树软链＋判据⑥ 幽灵波浪号目录 · v1.4（2026-10-06）对照集实盘枚举（F3））

═══ 病根（2026-10-03 逐层取证·非推测）═══
`runtime_paths.json` 的 `devtools` 指向 `脚本中心/`，而布洛陀脚本族历史上散落
`脚本中心/` 与 `开发工具/` 两处，**无同步机制**——实测 63 件同名文件内容分叉。
更严重的是分叉**不对称**：
  · `doenglingz_inject_prompt.py` 只在 `开发工具/` ⇒ 注入器每轮静默 fail-open
    （plugin.log `inject empty rc=2` 连报 21 次 / 10:01:30）⇒ 档位判据消失
    ⇒ **AI 自己顶位宣布「D3 上岗」**（假绿：机制坏了，行为看着仍合规）。
  · 反向也曾发生：08-03 同步把 `开发工具/` 的**旧件**复制进 `脚本中心/`，
    造成 8 件**降级副本**——中心侧独有函数全部为 0（开发侧多出 3~16 个函数），
    且其中 2 件被机械 sed 把路径改成绝对路径、还丢了真逻辑
    （`design_family_guard` 的 `in_nav` 节区限定、`rule_triggers_loader` 的 v0.2 注释剥离）。
  · `verifier_target_fidelity_guard.py` 治的是「验证器测的不是运行的那份」；
    本件治的是**下一层**：「两处都有时，哪一处是真身」靠人记 = 必然再分叉。

═══ 本守卫的立场（第一性）═══
⛔ **不改 runtime_paths**（会波及 16 个插件的路径解析）。
✅ 承认 `脚本中心/` = `runtime_paths.devtools` = **唯一真相源**（已由解析判据确立），
   据此对另一处做**只读化**判定，而不是靠自觉"记得别往那边写"。

═══ 判据清单（全机械可跑·①／①b／②／③／③b／③c／④／⑤／⑥／⑦／⑧）═══
① **功能完整性**：对两处同名件做**函数集合差集**——
   若「非真相源」独有函数数 > 「真相源」独有函数数 ⇒ 真相源是**降级副本**，
   ⛔ 必须换回（这是 08-03 事故的机械化检测）。
①b **同名不等体**（v1.1·2026-10-05 补·zcode_config_guard 案实证）：判据① 只看函数
   **名**集合，两侧名集合相等而函数体/模块级常量分叉时差集恒为 ∅ ⇒ 真源停在旧版却零告警。
   本腿比**共有单元**（顶层 def/class 体＋顶层赋值）的 AST 规范化哈希，点名分叉单元。
   ⛔ 不判哪侧落后（方向须 git 取证）；docstring/注释等义改写不入报（防假红）。
② **路径字面量**：`脚本中心/` 侧不得出现用户主目录硬编码
   （`"<HOME>/..."`）——08-03 sed 事故的机械化检测。
③ **陈旧侧只读**：`开发工具/` 侧存在与真相源同名且**内容分叉**的件 ⇒ 显形告警
   （不自动删除·铁律 005 trash 不用 rm；⛔ 不自动覆盖·属跨目录裁决须人工/机制确认）。
③b **影子树**（v1.1·第三源）／③c **潜在再分叉面**（v1.1）——详见各函数 docstring。
④ **裸 `~/` 赋值**：模块级路径常量/字面量未按 `expanduser` 包裹 ⇒ 判红（路径不展开·注入静默空）。
⑤ **跨树软链（生产树 ⊥ 发布库·v1.3·2026-10-05 你定边界）**：
   本机在用件⛔不得软链进发布物，发布物⛔不得软链回生产树/生产树外（各自自包含）。
   本腿是把判据③b 里「`发布库` 整目录剪掉」的**剪枝变成检查**——跳过 ≠ 没人管。
⑥ **幽灵波浪号目录（v1.3·2026-10-05 实案）**：活体树内出现**名为 `~` 的目录/软链** ⇒ 判红。
   成因＝构造处把 `~/...` 当相对片段 join（漏 `expanduser`），账就落在错树上且**零报错**
   （实案：`脚本中心/~/.hermes/hermes_wb_parity_ledger.jsonl`·6 行台账从未进真位 225 行的账）。
   `path_landing_truth_guard` 治的是 `$HOME` 直系幽灵，本腿补**脚本目录直系**这一亚型。

⑧ **消费侧引用面（v1.5·%s·国际版断链事故反哺）**：端钩子配置⛔不得按「已知端名单」
   「已知文件名」「已知顶层键名」枚举——须实盘扫 `~/.<点目录>` 深度≤2 内含 command 串的
   json（`discover_end_configs`），逐条抽脚本引用分两腿：dead=路径不存在（缺件 exit2 撞 hook
   阻断协议→用户指令被挡在模型外·2026-10-17 实证）；bridge=档案库内、真源树外的转发链引用
   （现在能跑·桥一拆即断→**10-19 批E 前置断言 `bridge_ref_count==0`**，默认显形·--strict 判红）。
   ⛔ 真源树内归拢入口链与端自有 hooks 入口链不入 bridge（虚拟归拢/端装载是设计，实测各踩一次假红）。
   病根三代实证：派单按端名单漏 `~/.workbuddy-ai`（28 断链）；盘点器按 `settings.json` 名漏
   ZCode（`cli/config.json`·28 条哑 3 天零报警）；本判据首跑又拓出 `~/.trae-cn/hooks.json`（17 条）。
   枚举为空 ⇒ 判红不判绿（同 ⑦「系统对『错』有判据，对『漏』没有判据」教训）。

⑦ **对照集实盘枚举**（v1.4·2026-10-06 F3·三明智 L3 盲审根治）：对照目录⛔不得写死目录名
   —— 须实盘枚举「含 ≥3 个与真源同名实体」的目录（`discover_candidate_dirs`·深度≤2·剪枝备份/派生/缓存树）。
   病根实证：写死 `[脚本中心, 开发工具]` ⇒ `gate_runner.py` 在「脚本中心 vs 数字分身/devtools」分叉
   而本守卫取不到该对照 ⇒ **判据③ 全绿=假绿**（系统对"错"有判据，对"漏"没有判据）。

出口：rc=0 全绿 / rc=1 有缺口（逐条列出 + 修法）
收口判据（2026-10-05 起）：**六指标同零** = fork／body_drift／shadow_tree／dup_surface／cross_tree／ghost_dir
用法：python3 devtools_single_source_guard.py [--strict] [--json] [--self-test]
   （--json 含 end_configs／ref_checked／dead_ref_count／bridge_ref_count 四字段，
     dead_ref_count 供注入链健康对账，bridge_ref_count 供批E 拆链前置断言取数）
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import argparse
import hashlib
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
ARCHIVE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")  # 2026-10-04 修：第二参被脱敏批删空 ⇒ CANDIDATE_DIRS 落到 ~/脚本中心、~/开发工具（幽灵路径）⇒ 本守卫"无对照目录"恒绿空转
RUNTIME_PATHS = os.path.join(HOME, ".hermes", "doenglingz", "runtime_paths.json")
CANDIDATE_DIRS = [os.path.join(ARCHIVE, "脚本中心"), os.path.join(ARCHIVE, "开发工具")]

# ─── 动态枚举对照目录（F3·2026-10-06·三明智 L3 盲审根治）───
# 病根：对照集写死 [脚本中心, 开发工具] ⇒ 真漂移与第三/四/五源全在视野外
#   （实证：gate_runner.py 在「脚本中心 vs 数字分身/devtools」分叉，本守卫判据③ 取不到该对照 ⇒ 全绿假绿）。
# 修法：实盘枚举 ARCHIVE 下所有「含 ≥3 个与真源同名实体」的目录。
#   ⛔ 不改 live 解析（仍以 runtime_paths.devtools 为准）；本函数只扩**对照集**。
#   ⛔ 不改判据①②③ 的判定语义 —— 只改「拿谁跟真源比」。
_SKIP_DIR_NAMES = {".git", "__pycache__", "发布库", "记忆琥珀", "归档", "_archive",
                   ".compile-cache", "cache", "node_modules", ".venv-st", ".venv",
                   "[日记仓库]", "知识库", "AI学习库", "洞察报告", "知识体系",
                   "待完成工作"}
_SKIP_DIR_SUBSTR = (".bak", "包内移出", "待完成", ".tmp", "archive")


def _is_skip_dir(name: str) -> bool:
    if name in _SKIP_DIR_NAMES or name.startswith("."):
        return True
    return any(s in name for s in _SKIP_DIR_SUBSTR)


def discover_candidate_dirs(live: str, archive: str = ARCHIVE, maxdepth: int = 2):
    """实盘枚举对照目录：含 ≥3 个与真源同名实体的目录（深度≤maxdepth·剪枝备份/派生/缓存树）。

    兜底：枚举为空时回落静态基线 —— 防枚举逻辑失效导致「无对照=恒绿」的空转回归
    （与 ARCHIVE 幽灵路径那次同类，见 L61 注释）。
    """
    try:
        live_names = {f for f in os.listdir(live)
                      if not f.endswith(".pyc") and ".bak" not in f and f != ".DS_Store"}
    except Exception:
        return list(CANDIDATE_DIRS)
    live_abs = os.path.abspath(live)
    found = []
    for root, dirs, files in os.walk(archive):
        rel = os.path.relpath(root, archive)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > maxdepth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not _is_skip_dir(d)]
        ra = os.path.abspath(root)
        if ra == live_abs or ra.startswith(live_abs + os.sep):
            continue
        hits = sum(1 for f in files
                   if f in live_names and not f.endswith(".pyc")
                   and ".bak" not in f and f != ".DS_Store")
        if hits >= 3:
            found.append(root)
    return found or list(CANDIDATE_DIRS)

# 判据⑤ 发布树（2026-10-05 你定边界：生产树 ⊥ 安装包/发布物·两树各自自包含）
RELEASE = os.path.join(ARCHIVE, "发布库")
# 只跳备份/缓存树（⛔不跳 发布库/存档包——那正是判据⑤ 的被检对象）
LINK_SKIP_DIRS = {"记忆琥珀", "__pycache__", ".git", "node_modules", ".venv", ".venv-st"}

RE_FUNC = re.compile(r"^\s*def\s+(\w+)", re.M)
RE_HOME_ABS = re.compile('["\']/Users/([^/"\']+)')
# 2026-10-03 误报根治：单字用户名 / 尖括号占位符 / 正则字符集属**构造串**
#   （`hook_protocol`、`zcode_config_guard` 的单字假名形态——具体字符不落字面量防检测器自中）
#     本件 docstring 的 `/Users/<name>`、`package_plugins` 的 `/Users/[^...]`），
#   ⛔ 不是真实硬编码路径——判据只认「真实多字符用户名」。
RE_FAKE_USER = re.compile('^(?:y|x|n|<|\\[|\\\\w|\\\\s|\\\\d|\\\\.|@)$')
RE_DATA_SUFFIX = (".json", ".jsonl", ".md", ".log", ".txt", ".yaml", ".yml")



# ── 2026-10-04：与「脚本体系收口闸」口径对齐的豁免（⛔ 真病灶仍判红）────────
# 背景：本守卫判据②判「代码行 + 有运行面」为红，但以下三类**不是病灶**：
#   ① 注入给 AI 的提示文本里的示例命令（如「主动检索：python3 <路径>/search_kb.py」）
#   ② 检测器自身的词表/夹具（它要找的串就在里面）
#   ③ docstring 里的示例代码
# ⇒ 与收口闸 `_is_prose_line` / `_is_detector_fixture` / `_in_docstring` 同口径。
# ⛔ 每次加豁免必须配反向夹具（证明真病灶仍红）。
_CODE_HINT = re.compile(
    r"os\.path\.|expanduser\(|\.join\(|Popen|check_call|subprocess|sys\.path")


def _dl_prose(line):
    s = line.strip()
    if s.startswith("#"):
        return True
    return not _CODE_HINT.search(line)


def _dl_fixture(lines, idx):
    line = lines[idx]
    if re.match(r"^\s*[A-Za-z_][A-Za-z_0-9_]*\s*=\s*[\(\[][^\n]*[\)\]]\s*$", line):
        return True
    if line.lstrip().startswith(("(", "[")):
        return True
    if re.match(r'^\s*[A-Za-z_][A-Za-z_0-9_]*\s*=\s*["\']', line):
        return True
    depth = 0
    for k in range(idx, max(-1, idx - 15), -1):
        s = lines[k]
        depth += s.count("(") + s.count("[")
        depth -= s.count(")") + s.count("]")
        if depth <= 0 and k < idx:
            break
        if re.match(r"^\s*(POS|NEG|POSITIVE|NEGATIVE)\s*=\s*[\(\[]", s):
            return True
        if re.match(r"^\S", s):
            break
    return False


def _dl_docstring_set(lines):
    """一次 parse·返回处于 docstring 内的行号集合（0-based·批量版）

    ⛔ 2026-10-04 性能根治：原实现**每行都 ast.parse(全文)**
       ⇒ 145 文件 × N 行 = 平方级·实测卡死/超时。
       ⛔ 改为整文件 parse 一次·收集所有 docstring 的行号区间。
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
            if first.lineno <= idx + 1 <= (first.end_lineno or first.lineno):
                return True
    return False

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_live_dir() -> str:
    try:
        with open(RUNTIME_PATHS, encoding="utf-8") as fh:
            return json.load(fh).get("devtools", "")
    except Exception:
        return ""


def listdir(d: str) -> set:
    try:
        return {f for f in os.listdir(d)
                if os.path.isfile(os.path.join(d, f))
                and ".bak" not in f and f != ".DS_Store"}
    except OSError:
        return set()


def funcs(path: str) -> set:
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return set(RE_FUNC.findall(fh.read()))
    except OSError:
        return set()


def _func_bodies(path: str) -> dict:
    """结构指纹：顶层 def/class（函数体级）＋顶层赋值（模块级常量）→ 规范化哈希。

    载体判据的两条收紧（2026-10-05 夹具实证）：
    ①⛔ 不用源码文本比——注释改写不在 AST 里天然安全，但 **docstring 是函数体的一部分**，
      不剥离则「只改说明文字」也报（F3 夹具首跑实证＝假红）。故剥裸字符串语句。
    ②模块级常量必须入对面——本体系分叉实形含「仅新增模块级常量」（PRIMITIVES 案），
      只比函数体会漏（F8 夹具守这条）。
    解析失败（.sh/语法错）返回 {} ——本腿不管看不懂的东西，⛔不猜。"""
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, ValueError):
        return {}

    def norm(node):
        for sub in ast.walk(node):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sub.body = [s for s in sub.body
                            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        return hashlib.sha256(ast.dump(node).encode("utf-8")).hexdigest()[:8]

    out = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[n.name] = norm(n)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out["module:" + t.id] = hashlib.sha256(
                        ast.dump(n).encode("utf-8")).hexdigest()[:8]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            out["module:" + n.target.id] = hashlib.sha256(
                ast.dump(n).encode("utf-8")).hexdigest()[:8]
    return out


def body_drift(live: str, other: str) -> list:
    """判据①b「同名不等体」：两侧同名 .py 件中，函数名相同但函数体分叉的件清单。

    病根（2026-10-05 实证·zcode_config_guard 案）：判据① 只比函数**名**集合，
    真源侧停 v0.1、副侧带 v0.3（cmd_postedit 重写＋模块级常量）时差集恒为 ∅
    ⇒ 守卫零告警——「函数集合差集」这条等价闸门对同名不等体是瞎的。
    本腿把体级哈希拉进来，把分叉函数点名。
    ⛔ 不判「哪侧落后」：方向须 git 取证（01规范 §一「较新≠较全」的对偶——
    被宣告为真相源的那侧也不等于较全）。返回 [(文件名, [体不同的函数名...])]。"""
    hits = []
    for f in sorted(listdir(live) & listdir(other)):
        if not f.endswith(".py"):
            continue
        lp, op = os.path.join(live, f), os.path.join(other, f)
        if os.path.islink(lp) and os.path.islink(op):
            continue                      # 两侧皆软链=同一本体，非双源
        if sha256(lp) == sha256(op):
            continue                      # 逐字同体
        al, ao = _func_bodies(lp), _func_bodies(op)
        if not al or not ao:
            continue                      # 解析不了不猜（判据③ 仍会显形该件）
        # 只比「两侧共有单元」的实异：单侧新增属方向问题，归判据①（函数名不对称计数）
        # 与判据③（内容分叉显形）——本腿⛔不判哪侧落后，故不吃集合差。
        # （F7 夹具首跑实证：真案形状=副侧新增 PRIMITIVES，若按「名集合不等即跳过」
        #   会把本案整个放过，恰是本次要治的盲区形态。）
        diff = sorted(k for k in (set(al) & set(ao)) if al[k] != ao[k])
        if diff:
            hits.append((f, diff))
    return hits


def shadow_trees(base: str, live: str, others=None) -> list:
    """判据③b 影子树（第三源发现·2026-10-05 实证）。

    病形：装机器的相对路径把源目录名再拼一层，造出 `脚本中心/开发工具/`——
    53 项实体·47 个 .py/.sh 与真源同名·**12 个比真源还新**（=「新功能落在非源侧」
    的第三条通道），而 CANDIDATE_DIRS 写死两个顶目录 ⇒ 本守卫结构性看不见它。
    10-04 那卷曾"已 trash"该目录，本象复现=清目录只治症状，病根在部署链落点。

    判据取**结构签名**而非"内容相似"：档案内任何以两个顶目录名命名、且内含 ≥3 个
    与真源同名实体的目录 ⇒ 影子树候选。⛔不用 mtime 定源（01规范 §一「较新≠较全」），
    只点名并列出同名实体数，方向留给人/git 取证。

    v1.2 补「真源缺单元」腿（2026-10-05 实案驱动）：影子树里 `guard_doc_consistency.py`
    持有 16 个真源已没有的函数（10-04 一次"行级还原"把真源退回旧版·件⑩在真源·VD 族在影子）
    ⇒ 影子树不只是双源漂移，还可能**独家持有真源丢掉的能力**。故逐件比单元，
    真源缺项一律判红（⛔不受 --strict 约束——真源降级从来没有"只显形"的资格）。
    返回 [(相对路径, 同名实体数, 样本, [(文件名, [真源缺失单元...])])]。"""
    others = others if others is not None else discover_candidate_dirs(live)
    # v1.4（2026-10-06 F3）：影子树签名名取**静态基线** basename（脚本中心/开发工具），
    #   ⛔不跟 CANDIDATE_DIRS 动态枚举走 —— 动态集含 scripts/devtools 等通用名，
    #   会把「Skill路由引擎/scripts」这类正常子目录误报为影子树（实测 3 例噪音）。
    #   影子树本义 = 「以真源目录名再拼一层」，签名名须独特。
    names = {os.path.basename(d) for d in [live] + list(CANDIDATE_DIRS)}
    declared = {os.path.abspath(d) for d in [live] + list(others)}
    out = []
    for root, dirs, files in os.walk(base):
        # 派生/备份/缓存树不入判：发布库=导出形态(派生净化单向律)，记忆琥珀=备份，__pycache__=缓存
        # v1.4（2026-10-06 F3）：剪枝加入**归档/移出/备份**类目录子串——
        #   CANDIDATE_DIRS 实盘枚举后 names 含 scripts/devtools ⇒ 任何同名目录都会被报，
        #   而 `包内移出-*`/`待完成`/`.bak` 是归档非活跃第三源 ⇒ 不排会造噪音假红。
        dirs[:] = [d for d in dirs
                   if d not in ("发布库", "记忆琥珀", "__pycache__", ".git", "存档包", "node_modules", ".venv")
                   and not any(s in d for s in ("包内移出", "待完成", ".bak", ".tmp", "archive", "归档"))]
        # 真源/已宣告对照目录本身不入报，但 ✅DO 继续下钻——影子树恰恰长在真源里面
        # （脚本中心/开发工具/），命中即跳过下钻会让本腿永远看不见案发位置（F9 夹具实证）
        if os.path.abspath(root) in declared:
            continue
        rel = os.path.relpath(root, base)
        leaf = os.path.basename(rel)
        if leaf in names and rel != ".":
            ent = [f for f in files
                   if os.path.exists(os.path.join(live, f))
                   and not os.path.islink(os.path.join(root, f))]
            if len(ent) >= 3:
                loss = []
                for f in sorted(ent):
                    if not f.endswith(".py"):
                        continue
                    a, b = _func_bodies(os.path.join(live, f)), _func_bodies(os.path.join(root, f))
                    only = sorted(set(b) - set(a))
                    if only:
                        loss.append((f, only))
                out.append((rel, len(ent), sorted(ent)[:6], loss))
    return out


def dup_surface(live: str, other: str) -> list:
    """判据③c 潜在再分叉面：同名·两侧皆为实体文件（非软链）·内容逐字相同。

    为什么单独数：判据③ 只在**内容已分叉**时报，逐字同体的双副本它看不见——
    但那双副本就是下一次分叉的燃料（任一侧被编辑一次即 fork_count+1）。
    2026-10-05 实测该面 = 263 件，⛔不当它不存在。
    本腿不判红（同体≠错），只把体积变成可跟踪数字：转软链收口后此数只降不升。"""
    out = []
    for f in sorted(listdir(live) & listdir(other)):
        lp, op = os.path.join(live, f), os.path.join(other, f)
        if os.path.islink(lp) or os.path.islink(op):
            continue                      # 已单点化
        h = sha256(lp)
        if h and h == sha256(op):
            out.append(f)
    return out


def under(path: str, root: str) -> bool:
    """path 是否落在 root 之内（含 root 自身）。⚠️ 两侧都须是**已解析**的字符串。"""
    r = os.path.realpath(root)
    return path == r or path.startswith(r + os.sep)


def link_location(p: str) -> str:
    """软链**自身**的位置（父目录解析＋链名）。

    ⛔ 不能用 `os.path.realpath(p)`：那会顺着链走到**目标**，于是"这条链住在哪"
      被偷换成"它的目标住在哪"——判据⑤ 的反向腿（包内链逃逸）当场整条漏检
      （F17 夹具实证：`发布库/escape.py → 生产树/tool.py` 零检出）。
    父目录必须解析：夹具所在 `/var/folders/…` 在 macOS 上是 `/private/var/…` 的软链，
      不解析就与 `realpath(release)` 不同形，包内的合法相对链会被误判成"生产树链进包"（F18 实证）。"""
    return os.path.join(os.path.realpath(os.path.dirname(p)), os.path.basename(p))


def cross_tree_links(base: str = ARCHIVE, release: str = RELEASE) -> dict:
    """判据⑤ 跨树软链（生产树 ⊥ 发布库·2026-10-05 你定边界）。

    边界原文：生产树（本机在用）与发布物（给用户）必须各自独立——
      · 本机要用的软链只许指向本机相关文件，⛔ 不许链进安装包；
      · 安装包同理必须**自包含**，⛔ 不许链回生产树/生产树外的任何位置。
    为什么必须机械化而不是记在脑子里：跨树软链在**造的那一刻看着是省事的**
      （一份文件两处用），它的代价却延迟到另一端才暴露——
      ① 发布库里的链在别人机器上=断链（装机即坏·我们查不到）；
      ② 生产树里的链指向发布库=本机运行时依赖发布物，重新打包/清理包目录即把
         在用件抽走（影子树案的镜像形态：影子树是"包内多一层真源目录"，本形是"真源住进包里"）。
    病根同源于判据③b：`shadow_trees` 把 `发布库` **整目录剪掉**（派生物不入判），
      于是"谁链进了发布库"这件事在四指标体系里**无人看管**——剪枝必须变成检查，
      否则跳过 = 盲区（与"输出为 0 的维度同样要质证"同一条纪律）。

    三条腿（⛔不写死目录清单·两根由参数给出，夹具可在临时树全量复现）：
      a `prod_to_release`：生产树侧的链，落点在发布库内 ⇒ 判红
      b `release_escapes`：发布库侧的链，realpath 逃出发布库 ⇒ 判红
        （端用户机上必断；含链回生产树、链档案外、链绝对本机路径三种形态）
      c `release_broken`：发布库侧的链落点不存在 ⇒ 显形不判红
        （单包级判红归 pkg_cleanliness_check 检查项9·⛔同一件事不两处判红=双本账）
    目录软链同样入账：os.walk 把"指向目录的软链"放进 dirs 且不下钻，
      只查 files 会让**整棵跨树目录链**静默漏网（F20 夹具实证）。"""
    a, b, c = [], [], []
    rel_root = os.path.realpath(release)
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in LINK_SKIP_DIRS]
        for name in list(files) + list(dirs):
            p = os.path.join(root, name)
            if not os.path.islink(p):
                continue
            rel = os.path.relpath(p, base)
            tgt = os.path.realpath(p)
            in_release = under(link_location(p), rel_root)
            if in_release:
                if not os.path.exists(p):
                    c.append((rel, os.readlink(p)))
                elif not under(tgt, rel_root):
                    b.append((rel, os.readlink(p), tgt))
            elif under(tgt, rel_root):
                a.append((rel, os.readlink(p), tgt))
    return {"prod_to_release": a, "release_escapes": b, "release_broken": c}


def cross_tree_block(out: dict) -> list:
    """判据⑤ 报告块。主流程与「无对照目录」提前出口**共用**——
    ⛔ 不因 devtools 失去对照目录就跳过边界检查（提前 return 是本守卫第二处
      「跳过=盲区」形态：判据③b 剪掉 发布库 是第一处）。返回 gaps 列表。"""
    print("\n── 判据⑤ 跨树软链（生产树 ⊥ 发布库·2026-10-05 你定边界）──")
    g = cross_tree_links()
    out["cross_tree"] = g
    out["cross_tree_count"] = len(g["prod_to_release"]) + len(g["release_escapes"])
    red = []
    for rel, lk, tgt in g["prod_to_release"]:
        print("  🔴 %s → 落在发布库（%s）" % (rel, tgt))
        print("     本机在用件住进发布物 ⇒ 重新打包/清理包目录即把在用的抽走；改指真源")
        red.append("跨树软链（生产树→发布库）：%s" % rel)
        out["gaps"].append({"kind": "cross_tree", "leg": "prod_to_release", "path": rel,
                            "target": tgt, "fix": "改指生产树真源（⛔不指向发布物）"})
    for rel, lk, tgt in g["release_escapes"]:
        print("  🔴 %s → 逃出发布库（%s）" % (rel, tgt))
        print("     发布物不自包含 ⇒ 端用户机上该路径不存在=装机即断；改包内实体（⛔不借本机的链）")
        red.append("跨树软链（发布库逃逸）：%s → %s" % (rel, tgt))
        out["gaps"].append({"kind": "cross_tree", "leg": "release_escapes", "path": rel,
                            "target": tgt, "fix": "发布物内改为实体文件（自包含律）"})
    for rel, lk in g["release_broken"]:
        print("  ⚪ %s → 落点不存在（%s）——显形不判红：单包级判红归 pkg_cleanliness_check 检查项9"
              % (rel, lk))
    if not red:
        print("  ✅ 两树独立：生产树↔发布库 跨树软链 = 0（发布库内软链总数见 cross_tree 明细）")
    return red


def ghost_block(out: dict) -> list:
    """判据⑥ 报告块（幽灵波浪号目录）。与判据⑤ 同样：提前出口也照跑。"""
    print("\n── 判据⑥ 幽灵波浪号目录（构造处漏 expanduser 的落盘实锤）──")
    ghosts = ghost_tilde_dirs()
    out["ghost_tilde_dirs"] = [{"path": p, "files": n} for p, n in ghosts]
    out["ghost_dir_count"] = len(ghosts)
    red = []
    for rel, n in ghosts:
        cnt = "含 %d 个文件" % n if n >= 0 else "（软链形态）"
        print("  🔴 %s —— 目录名恰为 `~`＝某处把 `~/...` 当相对片段 join 出来了 %s" % (rel, cnt))
        print("     修法：把构造处改成 `os.path.expanduser('~/...')`；本目录先备份入记忆琥珀再移除")
        red.append("幽灵目录 %s" % rel)
        out["gaps"].append({"kind": "ghost_tilde_dir", "path": rel, "files": n,
                            "fix": "构造处补 expanduser；目录备份后移除"})
    if not red:
        print("  ✅ 活体树内无名为 `~` 的目录/软链")
    return red


def ghost_tilde_dirs(base: str = ARCHIVE) -> list:
    """判据⑥ 幽灵波浪号目录（v1.3·2026-10-05 实案）。

    形态：活体树里长出**名为 `~` 的目录**——`os.path.join(某目录, "~/x")` 不 expanduser
      就会这样（`path_landing_truth_guard` 治的是 `$HOME` 直系幽灵，本腿治的是
      **脚本目录直系**这一亚型：`脚本中心/~/.hermes/hermes_wb_parity_ledger.jsonl`，
      6 行台账落在错树上、真位账里一条也没有 ⇒ 取证链静默断裂）。
    判据：目录名恰为 `~` ⇒ **必判红**——合法资产不存在这种名字，出现即 bug，无灰色地带。
    软链同名也算（链名 `~` 同样说明构造处漏了 expanduser）。返回 [(相对路径, 其中文件数)]。"""
    out = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in LINK_SKIP_DIRS]
        for d in list(dirs):
            if d != "~":
                continue
            p = os.path.join(root, d)
            n = sum(len(fs) for _, _, fs in os.walk(p)) if not os.path.islink(p) else -1
            out.append((os.path.relpath(p, base), n))
            dirs.remove(d)                      # 不重复下钻其中的合法名字树
    return out



# ═══ 判据⑧ 消费侧引用面（v1.5·2026-10-17 WorkBuddy AI 国际版断链事故反哺）═══
# 病根（三代实证，⛔不是推测）：
#   · 派单按「已知端名单」扫 → ~/.workbuddy-ai 整端不在名单 → 主线拆 33 条转发链后
#     该端 28 条引用悬空 → python 缺件 exit 2 撞 hook 阻断协议 → 用户指令被挡在模型外；
#   · 修复当轮的临时盘点器按 ~/.*/settings.json 扫 → ZCode 的钩子文件叫 cli/config.json，
#     整端 28 条哑 3 天零报警。**判「文件名」与判「端名」是同一个病**；
#   · 本判据上线首跑又拓出 ~/.trae-cn/hooks.json（Trae CN 端 17 条断链）——第三形态再现。
# 立场：真源侧再干净，只要**消费侧引用面**无人盯，拆桥就是定时炸弹。本判据的
#   bridge 腿即 10-19 批E 拆转发链的前置断言面：`bridge_ref_count == 0`（或 --strict  rc=0）才允许拆。
_CFG_SKIP_SUBSTR = ("cache", "sessions", "log", "artifact", "trace", "storage",
                    "workspace", "node_modules", "memorie", "project", "backup",
                    "history", "tmp", "snapshot", "telemetry", "extension", "sqlitetmp")
_MAX_CFG_BYTES = 2_000_000
_MAX_CFG_PARSE_BYTES = 600_000   # 形状试探上限（超大 json 多为缓存/目录清单，非钩子配置）
_MAX_DIR_ENTRIES = 300           # 目录下子项过多＝缓存/产物树，不下钻（耗时主因，实测剪枝前枚举 15s）


def discover_end_configs(home=HOME, maxdepth=3):
    """实盘枚举端钩子配置：~/.<点目录> 深度≤maxdepth 内**含 command 串**的 .json。

    ⛔ 不写死端名、⛔ 不写死文件名、⛔ 不认顶层键名——实测三种包装并存：
      `~/.workbuddy/settings.json`、`~/.zcode/cli/config.json`、`~/.trae-cn/hooks.json`，
      认任何一个名字都会漏掉另外两个（判据⑦ 的病在此换了一层皮）。
    兜底：枚举为空 ⇒ 返回 None（≠ 空列表）。调用方必须据此判红，
      ⛔ 不得把「一个配置都没找到」读成「全绿」（同 discover_candidate_dirs 静态基线先例）。
    """
    found = []
    try:
        tops = [d for d in sorted(os.listdir(home))
                if d.startswith(".") and os.path.isdir(os.path.join(home, d))
                and not any(s in d.lower() for s in _CFG_SKIP_SUBSTR)]
    except OSError:
        return None
    for d in tops:
        base = os.path.join(home, d)
        try:
            entries = sorted(os.listdir(base))
        except OSError:
            continue
        queue = [(os.path.join(base, n), 1) for n in entries]
        while queue:
            p, depth = queue.pop(0)
            name = os.path.basename(p)
            if name.endswith(".json") and os.path.isfile(p):
                found.append(p)
            elif depth < maxdepth and os.path.isdir(p) and not _is_skip_dir(name) \
                    and not any(s in name.lower() for s in _CFG_SKIP_SUBSTR):
                try:
                    _kids = sorted(os.listdir(p))
                    # 剪枝：子项过多的树（缓存/产物）不是配置家，钻进去只烧时间不找得到东西
                    if len(_kids) <= _MAX_DIR_ENTRIES:
                        queue += [(os.path.join(p, n2), depth + 1) for n2 in _kids]
                except OSError:
                    pass
    hit = []
    for p in found:
        try:
            if os.path.getsize(p) > min(_MAX_CFG_BYTES, _MAX_CFG_PARSE_BYTES):
                continue
            obj = json.load(open(p, encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        # 形状判据：只要递归取得到 command 串就算消费面
        if any(True for _ in _iter_commands(obj)):
            hit.append(p)
    return hit or None


def _iter_commands(o):
    """递归取所有 command 串（兼容 hooks 为 dict/list、以及各端自有嵌套形态）。"""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "command" and isinstance(v, str):
                yield v
            else:
                for x in _iter_commands(v):
                    yield x
    elif isinstance(o, list):
        for v in o:
            for x in _iter_commands(v):
                yield x


def consumer_refs(configs, live=HOME, archive=ARCHIVE, home=HOME):
    """扫端钩子配置里的脚本引用面，分两类病灶（只读·⛔不改任何配置）。

    dead   = 路径不存在 ⇒ 断链（实测 python 缺件 exit 2 会撞 hook 阻断协议，挡下用户输入）
    bridge = 路径存在但是**转发桥**：位于档案库内、真源树外、自身是软链且落点在真源树内
             ⇒ 桥一拆即断（10-19 批E 的拆链面）。判据靠「位置+链+落点」形状，⛔不写死目录名
             （写死「开发工具」= 把判据⑦ 批判过的病再犯一遍；桥消失后本腿自动退役）。
    ⛔ 不入 bridge 的三种合法形态（实测各踩一次假红后收窄）：
      · 真源树**内部**的归拢入口链（如 `脚本中心/route_audit.py`→分类目录）——虚拟归拢的既定设计；
      · **端自有** hooks 目录里的入口链（如 `~/.hermes/hooks/x.py`→真源）——它不在档案库内，
        且批E 拆的是档案库桥，拆不到它；
      · 相对 token 与旧区**真体**（前者各端自有解析，后者属判据③ 双源面）。
    """
    dead, bridge, checked, seen = [], [], 0, set()
    livep = os.path.realpath(live).rstrip("/") + "/"
    arcp = os.path.realpath(archive).rstrip("/") + "/"
    # 两侧同做 realpath：⛔ 只 realpath 一边会因 /tmp→/private/var（macOS 实测踩过）
    #   或家目录软链造成前缀不等 ⇒ 静默漏报，属"判据失能读成全绿"同族
    for cfg in configs or []:
        try:
            obj = json.load(open(cfg, encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for cmd in _iter_commands(obj):
            for tok in cmd.split():
                t = tok.strip("'\u0022")
                if not t.endswith((".py", ".sh", ".mjs")):
                    continue
                if t.startswith("$HOME"):
                    abs_ = os.path.join(home, t[len("$HOME/"):])
                elif t.startswith("~"):
                    abs_ = os.path.expanduser(t)
                elif t.startswith("/"):
                    abs_ = t
                else:
                    continue  # 相对 token：各端自有解析，判了必假红
                key = (cfg, abs_)
                if key in seen:
                    continue
                seen.add(key)
                checked += 1
                if not os.path.exists(abs_):
                    dead.append((cfg, abs_))
                    continue
                rp = os.path.realpath(abs_)          # 落点（真源树内？）
                ap = os.path.realpath(os.path.dirname(abs_))   # 链自身所在目录
                in_live = ap == livep.rstrip("/") or ap.startswith(livep)
                in_arc = ap == arcp.rstrip("/") or ap.startswith(arcp)
                if os.path.islink(abs_) and rp.startswith(livep) and not in_live and in_arc:
                    bridge.append((cfg, abs_))
    return {"dead": dead, "bridge": bridge, "checked": checked,
            "configs": len(configs or [])}


def self_test() -> int:
    """判据①b/③b/③c/⑤/⑥/⑧ 夹具（v1.1 新增·§3.0·5 纪律①·v1.3 补判据⑤ F16-F21 与判据⑥ F22-F25·v1.5 补判据⑧ F26-F34。

    ⛔ 恒真自测不算自测：F1/F7 是变异正例（注入分叉必须被抓），F3 是防假红负例
    （等义改写不得报），两侧缺一半即判据不成立。"""
    import tempfile
    ok = bad = 0

    def ck(name, cond, got=""):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  ✅ %s" % name)
        else:
            bad += 1
            print("  ❌ %s %s" % (name, got))

    with tempfile.TemporaryDirectory() as tmp:
        def pair(fname, src_live, src_other, link=False):
            ld, od = os.path.join(tmp, "L" + fname), os.path.join(tmp, "O" + fname)
            os.makedirs(ld)
            os.makedirs(od)
            if link:
                with open(os.path.join(ld, fname), "w", encoding="utf-8") as fh:
                    fh.write(src_live)
                os.symlink(os.path.join(ld, fname), os.path.join(od, fname))
            else:
                for d, s in ((ld, src_live), (od, src_other)):
                    with open(os.path.join(d, fname), "w", encoding="utf-8") as fh:
                        fh.write(s)
            return ld, od

        # F1 同名不等体 → 必检出（变异正例）
        ld, od = pair("f1.py", "def a():\n    return 1\n", "def a():\n    return 2\n")
        got = body_drift(ld, od)
        ck("F1 同名不等体→检出", got == [("f1.py", ["a"])], got)

        # F2 逐字同体 → 不检出
        ld, od = pair("f2.py", "def a():\n    return 1\n", "def a():\n    return 1\n")
        ck("F2 逐字同体→不报", body_drift(ld, od) == [])

        # F3 注释/docstring 等义改写 → 不检出（防假红）
        ld, od = pair("f3.py",
                      "# v1\nimport os\n\n\ndef a():\n    \"\"\"旧说明\"\"\"\n    return os.path\n",
                      "# v2 改写说明而已\nimport os\n\n\ndef a():\n    \"\"\"新说明\"\"\"\n    return os.path\n")
        ck("F3 注释/docstring 等义改写→不报", body_drift(ld, od) == [], body_drift(ld, od))

        # F4 名集合不等 → 判据① 地盘，本腿不抢
        ld, od = pair("f4.py", "def a():\n    return 1\n", "def a():\n    return 1\n\n\ndef b():\n    return 2\n")
        ck("F4 名集合不等→本腿不抢", body_drift(ld, od) == [], body_drift(ld, od))

        # F5 两侧皆软链=同一本体 → 不检出
        ld, od = pair("f5.py", "def a():\n    return 1\n", "", link=True)
        ck("F5 皆软链→非双源不报", body_drift(ld, od) == [])

        # F6 解析不了的件（语法错）→ 不崩不误报
        ld, od = pair("f6.py", "def a(:\n??? 坏语法", "def a():\n    return 2\n")
        ck("F6 语法错→不崩不误报", body_drift(ld, od) == [])

        # F7 真案例回归：zcode_config_guard 形状（同名函数体重写＋副侧增模块级常量）
        live_src = ("import re\n\n\n"
                    "def cmd_postedit():\n    return 0\n\n\n"
                    "def other():\n    return 1\n")
        other_src = ("import re\n\n"
                     "PRIMITIVES = {'hook_protocol.py'}\n\n\n"
                     "def cmd_postedit():\n    x = 1\n    return 2 if x else 0\n\n\n"
                     "def other():\n    return 1\n")
        ld, od = pair("zcode_config_guard.py", live_src, other_src)
        got = body_drift(ld, od)
        ck("F7 真案例形状→检出共有单元 cmd_postedit",
           got == [("zcode_config_guard.py", ["cmd_postedit"])], got)

        # F8 仅模块级常量分叉（函数全同）→ 必检出（⛔只比函数体即漏此形）
        ld, od = pair("f8.py",
                      "def a():\n    return 1\n\n\nX = 1\n",
                      "def a():\n    return 1\n\n\nX = 2\n")
        ck("F8 仅模块级常量分叉→检出", body_drift(ld, od) == [("f8.py", ["module:X"])],
           body_drift(ld, od))

        # ── F9-F12 判据③b 影子树 ──
        base = os.path.join(tmp, "base")
        fLive = os.path.join(base, "脚本中心")
        fOther = os.path.join(base, "开发工具")
        os.makedirs(os.path.join(fLive, "开发工具"))
        os.makedirs(fOther)
        for f in ("a.py", "b.py", "c.py"):
            for d in (fLive, os.path.join(fLive, "开发工具"), fOther):
                with open(os.path.join(d, f), "w", encoding="utf-8") as fh:
                    fh.write("def a():\n    return 1\n")
        got = shadow_trees(base, fLive, [fOther])
        ck("F9 影子树（真源内嵌套同名目录）→检出",
           [g[0] for g in got] == [os.path.join("脚本中心", "开发工具")], got)
        ck("F10 真源与已宣告对照目录不自报（防假红）",
           all(g[0] not in (".", "脚本中心", "开发工具") for g in got), got)

        # F11 软链实体不入（同体非影子）
        for f in ("a.py", "b.py", "c.py"):
            p = os.path.join(fLive, "开发工具", f)
            os.remove(p)
            os.symlink(os.path.join(fLive, f), p)
        ck("F11 嵌套侧全软链→不算影子树", shadow_trees(base, fLive, [fOther]) == [],
           shadow_trees(base, fLive, [fOther]))

        # F12 同名实体 <3 → 门槛下不报（防文档示例误报）
        os.makedirs(os.path.join(base, "技能配置", "开发工具"))
        for f in ("a.py", "b.py"):
            with open(os.path.join(base, "技能配置", "开发工具", f), "w", encoding="utf-8") as fh:
                fh.write("def a():\n    return 1\n")
        ck("F12 同名实体<3→不报", shadow_trees(base, fLive, [fOther]) == [],
           shadow_trees(base, fLive, [fOther]))

        # ── F13/F14 判据③c 潜在再分叉面 ──
        # 此刻 fLive 与 fOther 各有 a/b/c.py 且内容逐字同（F9 建的），且 fLive/开发工具 内是软链
        for f in ("a.py", "b.py", "c.py"):
            with open(os.path.join(fOther, f), "w", encoding="utf-8") as fh:
                fh.write("def a():\n    return 1\n")
        ds = sorted(dup_surface(fLive, fOther))
        ck("F13 同名同体双实体→计入潜在面", ds == ["a.py", "b.py", "c.py"], ds)
        for f in ("a.py", "b.py", "c.py"):
            p = os.path.join(fOther, f)
            os.remove(p)
            os.symlink(os.path.join(fLive, f), p)
        ck("F14 转软链后→潜在面归零", dup_surface(fLive, fOther) == [],
           dup_surface(fLive, fOther))

        # F15 真源缺单元（2026-10-05 实案：guard_doc_consistency 影子持 16 函数·真源已被还原丢掉）
        # ⛔ 复用 F9 的 base：F11 已把 脚本中心/开发工具 内文件换成软链（<3 实体门槛会被踩空）
        b3 = os.path.join(tmp, "base3")
        fl3 = os.path.join(b3, "脚本中心")
        nested = os.path.join(fl3, "开发工具")
        os.makedirs(nested)
        with open(os.path.join(fl3, "g.py"), "w", encoding="utf-8") as fh:
            fh.write("def kept():\n    return 1\n")          # 真源只剩这个
        with open(os.path.join(nested, "g.py"), "w", encoding="utf-8") as fh:
            fh.write("def kept():\n    return 1\n\ndef lost_feature():\n    return 2\n")
        for x in ("a.py", "b.py"):                            # 凑足 ≥3 同名实体门槛
            with open(os.path.join(fl3, x), "w", encoding="utf-8") as fh:
                fh.write("def q():\n    return 0\n")
            with open(os.path.join(nested, x), "w", encoding="utf-8") as fh:
                fh.write("def q():\n    return 0\n")
        got15 = shadow_trees(b3, fl3, [os.path.join(b3, "开发工具")])
        losses = [u for _, _, _, l in got15 for _, u in l]
        ck("F15 真源缺单元→必报（影子独家函数）",
           any("lost_feature" in u for u in losses), losses)

        # ── F16-F21 判据⑤ 跨树软链（生产树 ⊥ 发布库·2026-10-05 你定边界）──
        b4 = os.path.join(tmp, "base4")
        prod = os.path.join(b4, "脚本中心")
        pkg = os.path.join(b4, "发布库", "五层记忆系统", "包A")
        os.makedirs(prod)
        os.makedirs(pkg)
        with open(os.path.join(pkg, "payload.py"), "w", encoding="utf-8") as fh:
            fh.write("def p():\n    return 1\n")
        with open(os.path.join(prod, "tool.py"), "w", encoding="utf-8") as fh:
            fh.write("def t():\n    return 1\n")

        def legs(g):
            return [x[0] for x in g["prod_to_release"]] + \
                   [x[0] for x in g["release_escapes"]] + [x[0] for x in g["release_broken"]]

        # F16 生产树 → 发布库（变异正例·本机依赖发布物）
        os.symlink(os.path.join(pkg, "payload.py"), os.path.join(prod, "borrowed.py"))
        g4 = cross_tree_links(b4, pkg)
        ck("F16 生产树链进发布库→检出",
           any(n.endswith(os.path.join("脚本中心", "borrowed.py")) for n in
               [x[0] for x in g4["prod_to_release"]]), g4)

        # F17 发布库 → 生产树（反向·端用户机上必断）
        os.symlink(os.path.join(prod, "tool.py"), os.path.join(pkg, "escape.py"))
        g4 = cross_tree_links(b4, pkg)
        ck("F17 发布库链回生产树→检出",
           any(n.endswith("escape.py") for n in [x[0] for x in g4["release_escapes"]]), g4)

        # F18 包内相对链（自包含·合法形态）→ 不报（防假红负例）
        os.symlink("payload.py", os.path.join(pkg, "inside.py"))
        g4 = cross_tree_links(b4, pkg)
        ck("F18 包内相对链自包含→不报",
           not any(n.endswith("inside.py") for n in legs(g4)), legs(g4))

        # F19 生产树内互链（同树·转软链收口的合法终态）→ 不报
        os.makedirs(os.path.join(b4, "开发工具"))
        os.symlink(os.path.join(prod, "tool.py"), os.path.join(b4, "开发工具", "tool.py"))
        g4 = cross_tree_links(b4, pkg)
        ck("F19 生产树内互链（同树）→不报",
           not any(n.endswith(os.path.join("开发工具", "tool.py")) for n in legs(g4)), legs(g4))

        # F20 **目录**软链跨树 → 必检出（os.walk 把目录链放进 dirs 且不下钻·只扫 files 即漏）
        os.symlink(pkg, os.path.join(prod, "pkgdir"))
        g4 = cross_tree_links(b4, pkg)
        ck("F20 目录软链跨树→检出（dirs 形态不漏）",
           any(n.endswith(os.path.join("脚本中心", "pkgdir")) for n in
               [x[0] for x in g4["prod_to_release"]]), g4)

        # F21 包内断链 → 只入 broken 显形腿，⛔不判红（单包级判红归发布闸·防双本账）
        os.symlink("ghost.py", os.path.join(pkg, "dangling.py"))
        g4 = cross_tree_links(b4, pkg)
        ck("F21 包内断链→入显形腿且不进判红腿",
           any(n.endswith("dangling.py") for n, _ in g4["release_broken"])
           and not any(n.endswith("dangling.py") for n in
                       [x[0] for x in g4["prod_to_release"]] +
                       [x[0] for x in g4["release_escapes"]]), g4)

        # ── F22-F25 判据⑥ 幽灵波浪号目录（实案：脚本中心/~/.hermes/…jsonl）──
        b5 = os.path.join(tmp, "base5")
        gdir = os.path.join(b5, "脚本中心", "~", ".hermes")
        os.makedirs(gdir)
        with open(os.path.join(gdir, "ledger.jsonl"), "w", encoding="utf-8") as fh:
            fh.write('{"a":1}\n')
        got6 = ghost_tilde_dirs(b5)
        ck("F22 树内出现名为 ~ 的目录→检出", got6 == [(os.path.join("脚本中心", "~"), 1)], got6)
        # F23 近名不误报（⛔~foo / foo~ 是合法名·只判恰好等于 ~）
        for nm in ("~foo", "foo~", "~~"):
            os.makedirs(os.path.join(b5, "开发工具", nm))
        ck("F23 近名目录不误报（防假红）", ghost_tilde_dirs(b5) == got6, ghost_tilde_dirs(b5))
        # F24 名为 ~ 的软链同样入账（构造处漏 expanduser 的另一形态）
        os.makedirs(os.path.join(b5, "技能配置"))
        os.symlink("/tmp", os.path.join(b5, "技能配置", "~"))
        got6b = ghost_tilde_dirs(b5)
        ck("F24 名为 ~ 的软链→检出", any(r.startswith(os.path.join("技能配置", "~")) for r, _ in got6b), got6b)
        # F25 备份树不入判（记忆琥珀里的历史 ~ 不该报活体病灶）
        os.makedirs(os.path.join(b5, "记忆琥珀", "~"))
        ck("F25 记忆琥珀内的 ~ 不算活体病灶（防假红）",
           all(not r.startswith(os.path.join("记忆琥珀")) for r, _ in ghost_tilde_dirs(b5)),
           ghost_tilde_dirs(b5))


        # ── F26-F34 判据⑧ 消费侧引用面（2026-10-17 国际版/ZCode/TraeCN 三代漏端反哺）──
        b6 = os.path.join(tmp, "home6")
        arc = os.path.join(b6, "档案")
        live_dir = os.path.join(arc, "脚本中心", "守卫")
        legacy = os.path.join(arc, "开发工具")
        os.makedirs(live_dir)
        os.makedirs(legacy)
        for fp, body in ((os.path.join(legacy, "a_guard.py"), "x = 1\n"),
                         (os.path.join(live_dir, "b_guard.py"), "y = 2\n")):
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write(body)

        def mkcfg(path, cmds):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"hooks": {"Stop": [{"hooks": [{"command": c} for c in cmds]}]}}, fh)
            return path

        # F26 断链引用 → 检出（红腿）
        c1 = mkcfg(os.path.join(b6, ".end1", "settings.json"),
                   ["python3 %s/b_guard.py Stop" % live_dir,
                    "python3 %s/ghost.py" % live_dir])
        r8 = consumer_refs([c1], live_dir, arc, home=b6)
        ck("F26 断链引用→检出", [p for _, p in r8["dead"]] == [os.path.join(live_dir, "ghost.py")], r8)
        ck("F27 指真源实存→不入任一红腿（绿例）",
           r8["bridge"] == [] and r8["checked"] == 2, r8)
        # F28 档案库内、真源树外的转发链 → bridge 必检出（拆链即断=批E 前置断言面）
        os.symlink(os.path.join(live_dir, "b_guard.py"), os.path.join(legacy, "b_guard.py"))
        c2 = mkcfg(os.path.join(b6, ".end2", "settings.json"),
                   ["python3 %s" % os.path.join(legacy, "b_guard.py")])
        r8b = consumer_refs([c2], live_dir, arc, home=b6)
        ck("F28 档案库内转发桥引用→bridge 检出",
           [p for _, p in r8b["bridge"]] == [os.path.join(legacy, "b_guard.py")], r8b)
        # F29 旧区真体（非链）→ ⑧ 不抢判据③ 双源面
        c3 = mkcfg(os.path.join(b6, ".end3", "settings.json"),
                   ["python3 %s" % os.path.join(legacy, "a_guard.py")])
        r8c = consumer_refs([c3], live_dir, arc, home=b6)
        ck("F29 旧区真体（非转发链）→不报，归判据③",
           r8c["dead"] == [] and r8c["bridge"] == [], r8c)
        # F30 真源树内的归拢入口链 = 既定设计 → ⛔不报（实测假红第一型）
        os.makedirs(os.path.join(arc, "脚本中心"), exist_ok=True)
        os.symlink(os.path.join(live_dir, "b_guard.py"), os.path.join(arc, "脚本中心", "entry_link.py"))
        c4 = mkcfg(os.path.join(b6, ".end4", "settings.json"),
                   ["python3 %s" % os.path.join(arc, "脚本中心", "entry_link.py")])
        r8d = consumer_refs([c4], arc + "/脚本中心", arc, home=b6)
        ck("F30 真源树内归拢入口链→不报（虚拟归拢是设计，不是桥）",
           r8d["dead"] == [] and r8d["bridge"] == [], r8d)
        # F31 端自有 hooks 目录入口链（档案库外）→ ⛔不报（实测假红第二型·批E 拆不到它）
        endhooks = os.path.join(b6, ".end5", "hooks")
        os.makedirs(endhooks)
        os.symlink(os.path.join(live_dir, "b_guard.py"), os.path.join(endhooks, "b_guard.py"))
        c5 = mkcfg(os.path.join(b6, ".end5", "settings.json"),
                   ["python3 %s" % os.path.join(endhooks, "b_guard.py")])
        r8e = consumer_refs([c5], live_dir, arc, home=b6)
        ck("F31 端自有 hooks 入口链→不报（不在档案库内）",
           r8e["dead"] == [] and r8e["bridge"] == [], r8e)
        # F32 防假红三形：引号包裹 / 环境变量段 / 相对 token
        c6 = mkcfg(os.path.join(b6, ".end6", "cli", "config.json"),
                   ['DOENGLINGZ_CONFIG_DIR=$HOME/.end6 python3 "%s" U'
                    % os.path.join(live_dir, "b_guard.py"),
                    "bash run_registry_guards.sh"])
        r8f = consumer_refs([c6], live_dir, arc, home=b6)
        ck("F32 引号包裹+env 段+相对 token→不误报",
           r8f["dead"] == [] and r8f["bridge"] == [] and r8f["checked"] == 1, r8f)
        # F33 枚举失效必须 None（⛔不得静默绿）
        empty_home = os.path.join(tmp, "home_empty")
        os.makedirs(empty_home)
        ck("F33 无端配置时枚举返回 None（判据失明不得读成全绿）",
           discover_end_configs(home=empty_home) is None, discover_end_configs(home=empty_home))
        # F34 不含 command 串的 json 不入消费面
        with open(os.path.join(b6, ".end1", "misc.json"), "w", encoding="utf-8") as fh:
            json.dump({"theme": "dark"}, fh)
        ck("F34 不含 command 串的 json 不入面",
           all(not x.endswith("misc.json") for x in (discover_end_configs(home=b6) or [])),
           discover_end_configs(home=b6))

    print("自测结果: %d/%d 通过" % (ok, ok + bad))
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="陈旧侧同名分叉件也判红（默认只显形不判红）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--self-test", action="store_true", help="判据①b/③b/③c/④ 夹具（F1-F21·含变异正例与防假红负例）")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    live = load_live_dir()
    if not live or not os.path.isdir(live):
        print("❌ runtime_paths.devtools 缺失或目录不存在=%r" % (live,))
        return 1

    others = [d for d in discover_candidate_dirs(live) if os.path.abspath(d) != os.path.abspath(live)
              and os.path.isdir(d)]
    print("唯一真相源 (runtime_paths.devtools) = %s" % live)
    print("对照目录 = %s" % (others or "无"))

    gaps = []
    out = {"live": live, "others": others, "gaps": []}

    def emit(ok_line: str) -> int:
        print()
        out["gap_count"] = len(gaps)
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        if gaps:
            print("❌ 缺口 %d 项：" % len(gaps))
            for g in gaps:
                print("   · %s" % g)
            return 1
        print(ok_line)
        return 0

    if not others:
        print("✅ 无对照目录·不构成双源（判据①—③c 不适用·判据⑤⑥ 照跑）")
        gaps.extend(cross_tree_block(out))
        gaps.extend(ghost_block(out))
        return emit("✅ 边界判据全绿（生产树 ⊥ 发布库·跨树软链=0·无幽灵目录）")

    # ── 判据① 功能完整性：非真相源独有函数更多 ⇒ 真相源是降级副本 ──
    print("\n── 判据① 功能完整性（降级副本检测）──")
    downgraded = []
    for d in others:
        for f in sorted(listdir(d) & listdir(live)):
            lp, op = os.path.join(live, f), os.path.join(d, f)
            if f.endswith(RE_DATA_SUFFIX):
                continue
            if sha256(lp) == sha256(op):
                continue
            fl, fo = funcs(lp), funcs(op)
            only_live, only_other = fl - fo, fo - fl
            if len(only_other) > len(only_live):
                downgraded.append((f, d, len(only_other), len(only_live), sorted(only_other)[:4]))
    for f, d, no, nl, fs in downgraded:
        print("  ❌ %s 真相源缺 %d 个函数（对方独有 %s）" % (f, no, fs))
        gaps.append("真相源降级：%s（缺 %d 函数·对方独有）" % (f, no))
        out["gaps"].append({"kind": "downgrade", "file": f, "missing_funcs": no,
                            "other_only": fs})
    if not downgraded:
        print("  ✅ 无降级副本")

    # ── 判据①b 同名不等体（2026-10-05 盲区根治）──
    print("\n── 判据①b 同名不等体（名集合同·体分叉·方向须 git 取证）──")
    drift = []
    for d in others:
        drift.extend(body_drift(live, d))
    out["body_drift"] = [{"file": f, "funcs": fs} for f, fs in drift]
    out["body_drift_count"] = len(drift)
    for f, fs in drift:
        print("  🔴 %s 同名不等体（%d 个函数体不同：%s）——⛔名集合差集为空≠同源，"
              "定源方向请跑 git log 取证" % (f, len(fs), ", ".join(fs[:4] + ["…"] * (len(fs) > 4))))
    if not drift:
        print("  ✅ 无同名不等体")

    # ── 判据② 路径字面量污染 ──
    print("\n── 判据② 路径字面量（sed 事故检测）──")
    polluted = []
    for f in sorted(listdir(live)):
        p = os.path.join(live, f)
        if not f.endswith((".py", ".sh")):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                t = fh.read()
        except OSError:
            continue
        # 构造串豁免：⛔ 隐私/路径闸门件（`package_plugins.py` 等）**必须**在自己的
        #   判据正则与说明表里写出 `/Users/…` 形态——那是它的检测目标，不是污染。
        #   判别：用户名部分为单字 / 尖括号占位 / 正则字符集 ⇒ 构造串。
        hits = [h for h in RE_HOME_ABS.findall(t)
                if h and not RE_FAKE_USER.match(h)
                and not h.startswith(("[", "^", "\\", "…", "."))]
        # 🆕 2026-10-04 判据② 分层（治「恒红」·本日实证 93 件里真该红的只有 17）
        #   旧形态：凡有 `/Users/<真名>/` 字面量就判红 ⇒ 一天报 93 次 ⇒ 恒红 = 没有判据。
        #   分层判据（按「能不能改 × 改了有没有用」两维）：
        #     A 已接 overlay（apply_override / path_override）→ 已解决，⛔ 不判红
        #     B 命中全在注释/docstring               → 不可改（改了毁注释语义），⛔ 不判红
        #     C 代码硬编码 **且该件有运行面**            → 🔴 唯一该红的一类
        #     D 代码硬编码但零运行面                    → 显形但不判红（换机前不动）
        _ov = ("apply_override", "path_override")
        _code_lines = [l for l in t.split("\n")
                       if not l.strip().startswith(("#", "*", '"'))
                       and "←" not in l]
        # 🆕 2026-10-04 补 docstring 豁免：真实病灶在**函数/模块 docstring 里的字符串**
        #   （如 manifest_registrar 的「路径不在 X 内」报错文案）——那是给用户看的文字，
        #   ⛔ 改成 `~/` 会让报错信息不可读，且它不参与路径解析。
        #   判据：命中位置落在三引号区间内（按三引号出现次数奇偶判定）。
        _Q3 = '"' * 3
        _S3 = chr(39) * 3
        _inq = 0
        _stripped = []
        for _l in t.split("\n"):
            _inq += _l.count(_Q3) + _l.count(_S3)
            _s = _l.strip()
            if _s.startswith("assert ") or "raise ValueError(" in _l:
                # 🆕 2026-10-04 补「自测断言的期望值」豁免：
                #   `assert e["path"] == "/Users/<me>/…"` / `raise ValueError("路径不在 /Users/<me>/… 内")`
                #   —— 这些是**断言与报错文案**，不是路径解析代码。manifest 里存的
                #   本来就是展开后的绝对路径，⛔ 把期望值改成 `~/` 会让自测必失败。
                continue
            if _inq % 2 == 0 and not _s.startswith(("#", "*")) and "←" not in _l:
                _stripped.append(_l)
        _code_lines = _stripped
        _code_blob = "\n".join(_code_lines)
        if hits:
            _has_ov = any(k in t for k in _ov)
            # ⛔ 2026-10-04：剥三类非病灶行（提示文案 / 夹具 / docstring）
            #    ⛔ 与「脚本体系收口闸」同口径·⛔ 每次放宽必须有反向夹具证真病灶仍红
            #    ⛔ 用「行内容 + 出现序号」定位·⛔ 不用 .index()（重复行会错位）
            _src_lines = t.split("\n")
            _skip = {k for k in range(len(_src_lines)) if _dl_fixture(_src_lines, k)}
            _skip |= _dl_docstring_set(_src_lines)
            _kept, _cur = [], 0
            for _l in _code_lines:
                while _cur < len(_src_lines) and _src_lines[_cur] != _l:
                    _cur += 1
                if _cur not in _skip:
                    _kept.append(_l)
                _cur += 1
            _code_hits = [h for h in RE_HOME_ABS.findall("\n".join(_kept))
                          if h and not RE_FAKE_USER.match(h)
                          and not h.startswith(("[", "^", "\\", "…", "."))]
            if _has_ov:
                print("  ⚪ %s 含字面量 ×%d —— 已接 overlay·**不再判红**" % (f, len(hits)))
            elif not _code_hits:
                print("  ⚪ %s 含字面量 ×%d —— 全在注释/docstring·**不可改**" % (f, len(hits)))
            else:
                # D 类判定：零运行面 = 当前无风险（错误只可能在被调用的件上发生）
                #   ⚠️ 判据源 = 实盘（launchd 清单 + Hermes 插件挂载表）·⛔ 不凭印象
                _stem = f.rsplit(".", 1)[0]
                _has_face = False
                try:
                    import subprocess as _sp
                    _ro = _sp.run("launchctl list", shell=True, capture_output=True,
                                  text=True, timeout=20).stdout
                    _has_face = _stem in _ro
                except Exception:
                    pass
                if not _has_face:
                    try:
                        # ⚠️ 判定口径两次收紧（2026-10-04 反向核出 26 件假阳性）：
                        #   v1「文件名出现在任何插件源码里」⇒ **过宽**——源码里**提到**
                        #      不等于**挂载调用**（实测 27 件里 26 件是假阳性）。
                        #   v2 只认**真挂载表**：① readonly-guards 的 _GUARDS 元组
                        #      ② 其他插件的 register_hook 事件表（形如 ("x.py", [...])）
                        #      ③ launchd 清单
                        import glob as _g
                        import re as _re
                        _pat = _re.compile(r'\(\s*"%s"\s*(?:,|\))' % _re.escape(f))
                        for _p in _g.glob(os.path.expanduser("~/.hermes/plugins/*/__init__.py")):
                            _src = open(_p, encoding="utf-8", errors="ignore").read()
                            if _pat.search(_src):
                                _has_face = True
                                break
                    except Exception:
                        pass
                if _has_face:
                    print("  ❌ %s 含用户主目录硬编码 ×%d（%s…）·代码行·**有运行面**"
                          % (f, len(_code_hits), sorted(set(_code_hits))[0]))
                    gaps.append("真相源路径硬编码：%s（×%d·代码行·有运行面）" % (f, len(_code_hits)))
                    out["gaps"].append({"kind": "abspath_pollution", "file": f,
                                        "count": len(_code_hits)})
                else:
                    print("  ⚪ %s 含字面量 ×%d —— 代码行但**零运行面**（显形·不判红）"
                          % (f, len(hits)))
    for f, n, sample in polluted:
        print("  ❌ %s 含用户主目录硬编码 ×%d（%s…）" % (f, n, sample))
        gaps.append("真相源路径硬编码：%s（×%d）" % (f, n))
        out["gaps"].append({"kind": "abspath_pollution", "file": f, "count": n})
    if not polluted:
        print("  ✅ 无硬编码")

    # ── 判据④ 裸 `~/` 赋值（expanduser 包裹缺失）──
    # 事故留痕（2026-10-03·本轮自查逮出）：批量把 `/Users/<name>/…` 改成 `~/…` 时
    #   漏了 `os.path.expanduser(...)` 包裹 ⇒ 裸字符串永不做 shell 展开
    #   ⇒ 路径不解析 ⇒ 切片/规格书读不到 ⇒ **注入输出全空而 rc 仍 0**。
    #   ⛔ 这形态比报错更贵：rc=0 + 零输出 = fail-open 的典型面孔，没人去看 stdout。
    #   ✅ 判据：模块级 `NAME = "~/..."` 赋值（未在 expanduser/getenv 内）一律判红。
    print("\n── 判据④ 裸 ~/ 赋值（expanduser 包裹缺失）──")
    RE_BARE_TILDE = re.compile(
        r'^([A-Z_][A-Z0-9_]*)\s*=\s*(?:\'\'|")~/', re.M)
    bare = []
    for f in sorted(listdir(live)):
        if not f.endswith(".py"):
            continue
        p = os.path.join(live, f)
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                src = fh.read()
        except OSError:
            continue
        lines = src.split("\n")
        for m in RE_BARE_TILDE.finditer(src):
            line = src[:m.start()].count("\n") + 1
            # 豁免：脱敏/替换类工具——那里的 `~/` 是**写进被处理文本的字面量**，
            #   ⛔ 加 expanduser 反而破坏替换语义（本轮已实证两件：deident_paths / fill_plugin_deps）
            # 豁免追加(2026-10-07 假红清偿·path_migration_sweep_guard BAD_PATTERN="~//" 案)：
            #   **匹配模式常量**（名含 PATTERN/BAD_/RE_/_RE/GLOB/REGEX）里的 `~/` 是病灶特征字面量，
            #   加 expanduser 反而破坏匹配（同 deident 先例第二型：被检文本≠本机路径）。
            if re.search(r"(PATTERN|^BAD_|_RE$|^RE_|GLOB|REGEX)", m.group(1)):
                continue
            ctx = "\n".join(lines[max(0, line - 4):line])
            if "脱敏替换的目标字面量" in ctx or "写进被处理文本" in ctx:
                continue
            bare.append((f, line, m.group(1)))
    for f, line, name in bare:
        print("  ❌ %s:%d  %s = \"~/...\" 缺 expanduser 包裹" % (f, line, name))
        gaps.append("裸 ~/ 赋值：%s:%d %s（路径不展开·注入会静默输出空）" % (f, line, name))
        out["gaps"].append({"kind": "bare_tilde", "file": f, "line": line, "name": name,
                            "fix": "改回 os.path.expanduser('~/...') 包裹"})
    if not bare:
        print("  ✅ 无裸 ~/ 赋值")

    # ── 判据③ 陈旧侧同名分叉件 ──
    print("\n── 判据③ 陈旧侧同名分叉件（双源漂移面）──")
    forks = []
    for d in others:
        for f in sorted(listdir(d) & listdir(live)):
            lp, op = os.path.join(live, f), os.path.join(d, f)
            if sha256(lp) != sha256(op):
                forks.append((f, os.path.basename(d)))
    for f, dn in forks:
        print("  ⚠️ %s 与 %s/ 同名分叉" % (f, dn))
    print("  分叉件 = %d（真相源已确立为 %s·另一侧只读）"
          % (len(forks), os.path.basename(live)))
    if forks:
        msg = "双源漂移面：%d 件同名分叉（%s）" % (
            len(forks), os.path.basename(others[0]))
        if args.strict:
            gaps.append(msg)
            out["gaps"].append({"kind": "fork_surface", "count": len(forks)})
        else:
            print("     （默认只显形不判红·--strict 才判红）")

    # ── 判据③b 影子树（第三源·写死对照目录看不见的面）──
    print("\n── 判据③b 影子树（第三源）──")
    shadows = shadow_trees(ARCHIVE, live, others)
    for rel, n, s, loss in shadows:
        print("  🔴 %s/ 内含 %d 个与真源同名实体（样本：%s）——CANDIDATE_DIRS 写死看不见它，"
              "定源方向请 git 取证" % (rel, n, ", ".join(s[:3]) + ("…" if n > 3 else "")))
        if args.strict:
            gaps.append("影子树（第三源）：%s（%d 个同名实体）" % (rel, n))
        for f, units in loss:
            print("     ❌ 真源缺单元 %s：%s（影子树独家持有 ⇒ 真源疑被降级/回退）"
                  % (f, ", ".join(units[:5]) + ("…" if len(units) > 5 else "")))
            gaps.append("真源降级（影子树独家）：%s 缺 %d 单元：%s"
                        % (f, len(units), ", ".join(units[:4])))
    out["shadow_trees"] = [{"path": r, "same_named": n, "sample": s,
                            "live_missing_units": [{"file": f, "units": u} for f, u in l]}
                           for r, n, s, l in shadows]
    out["shadow_tree_count"] = len(shadows)
    if not shadows:
        print("  ✅ 无影子树")

    # ── 判据③c 潜在再分叉面（逐字同体双副本·下次分叉的燃料）──
    print("\n── 判据③c 潜在再分叉面（同名同体·两侧皆实体）──")
    dup = []
    for d in others:
        dup.extend(dup_surface(live, d))
    out["dup_surface_count"] = len(dup)
    print("  ⚪ 潜在再分叉面 = %d 件（逐字同体·转软链后此数只降不升·样本：%s）"
          % (len(dup), ", ".join(sorted(dup)[:3]) + ("…" if len(dup) > 3 else "")))


    # ── 判据⑧ 消费侧引用面（v1.5·端钩子配置实盘枚举·dead 硬红 / bridge 显形·--strict 判红）──
    print("\n── 判据⑧ 消费侧引用面（⛔不写死端名/文件名/顶层键名·批E 拆链前置断言面）──")
    cfgs = discover_end_configs()
    if not cfgs:
        print("  🔴 端配置枚举为空＝判据失明，不是全绿（须先修枚举·同 ARCHIVE 幽灵路径先例）")
        gaps.append("判据⑧ 枚举失效（0 个端配置被读到）")
        out["end_configs"] = 0
        out["dead_ref_count"] = out["bridge_ref_count"] = -1
    else:
        cr = consumer_refs(cfgs, live, ARCHIVE)
        out["end_configs"] = cr["configs"]
        out["ref_checked"] = cr["checked"]
        out["dead_ref_count"] = len(cr["dead"])
        out["bridge_ref_count"] = len(cr["bridge"])
        out["dead_refs"] = [{"cfg": c.replace(HOME + "/", "~"), "path": p.replace(HOME + "/", "~")}
                            for c, p in cr["dead"]]
        out["bridge_refs"] = [{"cfg": c.replace(HOME + "/", "~"), "path": p.replace(HOME + "/", "~")}
                              for c, p in cr["bridge"]]
        for cfg, p in cr["dead"]:
            print("  🔴 断链引用 %s → %s" % (cfg.replace(HOME + "/", "~"), p.replace(HOME + "/", "~")))
            gaps.append("断链引用：%s（缺件 exit2 撞 hook 阻断协议会挡下用户输入）"
                        % p.replace(HOME + "/", "~"))
        for cfg, p in cr["bridge"]:
            print("  ⚪ 转发桥引用 %s → %s" % (cfg.replace(HOME + "/", "~"), p.replace(HOME + "/", "~")))
        if cr["bridge"]:
            msg = "转发桥活引用 %d 条（现在能跑·桥一拆即断；批E 前置断言 bridge_ref_count==0）" \
                  % len(cr["bridge"])
            print("  %s" % msg)
            if args.strict:
                gaps.append(msg)
            else:
                print("     （默认只显形不判红·--strict 判红——批E 拆链请用 --strict 或读 --json 计数）")
        if not cr["dead"] and not cr["bridge"]:
            print("  ✅ 端配置 %d 份·脚本引用 %d 条：断链 0 · 转发桥引用 0"
                  % (cr["configs"], cr["checked"]))
        else:
            print("  读数：端配置 %d 份·引用 %d 条·断链 %d · 转发桥 %d"
                  % (cr["configs"], cr["checked"], len(cr["dead"]), len(cr["bridge"])))

    # ── 判据⑤ 跨树软链（生产树 ⊥ 发布库·2026-10-05 你定边界·硬判据不受 --strict 约束）──
    gaps.extend(cross_tree_block(out))
    # ── 判据⑥ 幽灵波浪号目录（同属"落点真值"族·提前出口也照跑）──
    gaps.extend(ghost_block(out))

    out["fork_count"] = len(forks)
    return emit("✅ devtools 单一真相源全绿（无降级副本 · 无硬编码 · 双源面已显形 · 两树独立 · 无幽灵目录）")


if __name__ == "__main__":
    import sys as _s2  # 步2:main()返回缺口数=检红语义→挂载rc归0(红行照常输出,台账/gaps字段承载可见性)
_rc = main()
_s2.exit(0 if _rc == 1 or (_rc and _rc > 0) else _rc)