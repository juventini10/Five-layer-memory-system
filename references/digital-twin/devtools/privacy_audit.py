#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""privacy_audit.py —— 「给用户的东西」分层隐私审计

## 为什么要另立一道（而不是只靠 pkg_cleanliness_check）

`pkg_cleanliness_check.py` 查的是**发布卫生**（私人称呼 / 用户名 / .bak / 临时残留）——
只有 2 类隐私签名，而且是**全包统一口径**。

但「**给用户的东西**」的要求更严（皮叔 2026-10-02 立规：
*给用户的必须也是脱敏的通用版，不要有我个人的隐私*）：

| 交付类 | 落到哪 | 隐私底线 |
|:---|:---|:---|
| **A 待粘贴文本** | 用户的**系统提示框**·逐字生效 | **最严**——任何作者痕迹都是错的 |
| **B 落进用户系统的规则** | 用户的 SOUL/MEMORY/规则目录 | 严 |
| **C 会进用户上下文的插件** | 每轮对话注入 | 中（注释/文档可提"作者"） |
| **D 安装文档** | 用户读的说明书 | 松（可诚实说明"由作者脱敏"） |

⚠️ **A 类最容易被忽略**：它的内容**逐字进系统提示**，
一句「2026-09-15 你质询…」就是作者工作记录进了别人的系统。

## 八类签名（⛔ 本文件自身必须脱敏免疫）

| # | 类 | 说明 |
|:--|:---|:---|
| 1 | 私人称谓 | 口语称呼 |
| 2 | 本机用户名 | 账户名 |
| 3 | 作者档案目录名 | 作者记忆中心目录 |
| 4 | 本机绝对路径 | `/Users/…` `/home/…` |
| 5 | **作者工作记录** | 日期化决策记录（`YYYY-MM-DD` + 作者动作） |
| 6 | **作者签名式回复格式** | 意图分类容器 / 产出签名 / 端徽标署名 |
| 7 | **作者专属判据** | 愿景三问等个人判据 |
| 8 | 私人内容标记 | 私人记忆/台账/人格作答痕迹 |
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import os
import re
import sys

PKG = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# ⛔ 签名一律「拼接 / 转义」构造——本文件自己也要过闸（照 pkg_cleanliness_check 先例）
_S = lambda *a: "".join(a)
SIG = {
    "1-私人称谓": _S("\u54e5"),
    "2-本机用户名": _S("juv", "entini10"),
    "3-作者档案目录": _S("个人", "AI档案"),
    "4-本机绝对路径": None,          # 用正则，见 ABS_RE
    "5-作者工作记录": None,          # 用正则，见 WORK_RE
    "6-作者签名式格式": _S("意图分类", "容器"),
    "7-作者专属判据": _S("强化闭环吗", "减少人工吗"),
    "8-私人内容标记": _S("卡池通读档案", "本地Obsidian_Vault"),
}
# ⚠️ **占位符不算隐私**：`/Users/xxx`、`/Users/<用户名>`、`/Users/{用户名}` 是**示例**，
#    出现在"⛔ 不要这样写"的规范条文里、或脱敏脚本的**检测模式**里。
#    把它们当命中 ⇒ 判据恒红 ⇒ 永远红的判据等于没有判据（台账 §1.2 恒真的反面）。
_ABS = r"/(?:Users|home)/[^/\s\"'）)`+]+|C:\\\\Users\\\\[^\\\s\"'）)`+]*"
PLACEHOLDER = re.compile(r"^(?:x{2,}|<[^>]*>|\{[^}]*\}|\$\{[^}]*\}|%s|用户名|USER|xxx+|\.\.\.)$", re.I)
ABS_RE = re.compile("(?:%s)" % _ABS)
ABS_HITS = None      # 由 filter_abs 填充
# 日期 + 作者动作 ⇒ 工作记录
WORK_RE = re.compile(r"20\d{2}-\d{2}-\d{2}[^\n]{0,24}"
                     + re.escape(SIG["1-私人称谓"]))
# 端徽标署名（作者端标识）
SIGN_RE = re.compile(re.escape(_S("你的 Hermes")) + r"|" + re.escape(_S("Hermes 🪶")))

# 交付分层：A/B/C/D —— A 最严
CLASSES = [
    ("A-待粘贴文本", ["adapters/doubaowork/rules",
                      "adapters/lobsterai/templates",
                      "adapters/qodercn/templates",
                      "adapters/zcode/privacy"]),
    ("B-落进用户系统的规则", ["references/templates"]),
    ("C-会进用户上下文的插件", ["adapters/hermes/plugins",
                                "adapters/lobsterai/plugin"]),
    ("D-安装文档", ["adapters", "references/steps", "INSTALL.md", "README.md"]),
    # E：指纹池去私有（2026-10-03·根治）——池只许由**中立样例源**生成，
    #    ⛔ 不得带作者档案派生指纹（一处泄私有入包·见 12 号 §5.9）。
    ("E-指纹池（去私有）", ["references/integrity-fingerprints.json"]),
]
# 各层**允许**的签名（A 类一条都不许；D 类可提"作者"字样但不许提称谓/路径/工作记录）
ALLOW = {
    "A-待粘贴文本": set(),
    "B-落进用户系统的规则": {"1-私人称谓"},
    "C-会进用户上下文的插件": {"1-私人称谓"},
    "D-安装文档": {"1-私人称谓", "6-作者签名式格式", "7-作者专属判据"},
    "E-指纹池（去私有）": set(),
}
SKIP_DIR = {"__pycache__", ".git"}
# ⛔ 检测器/脱敏器本体豁免：它们**必须**写着要检测的模式，否则没法工作
EXEMPT = ("desensitize-guard", "deident", "privacy_audit.py", "pkg_cleanliness_check.py",
          "integrity-fingerprints.json")


def code_surface(path):
    """.py 用 AST（⛔ docstring 也要看——它会被人读），非 py 用全文本。"""
    raw = open(path, encoding="utf-8", errors="replace").read()
    if not path.endswith(".py"):
        return raw, "text"
    try:
        ast.parse(raw)
    except SyntaxError:
        return raw, "text(broken)"
    return raw, "text"          # ⛔ 刻意用全文本：注释/docstring 同样是给人读的


# ⚠️ 「作者档案目录」只在**路径上下文**才算命中。
#    散文里的「AI 打开个人AI档案第一眼读这个」= **泛指用户的记忆中心**（不是落点），
#    规范里的「`~/个人AI档案/` 是用户自起目录名（不安全），需用 `~/个人AI档案`」
#    = **教学举例**（它恰恰在讲该用什么）——改了会毁掉规范的教学意义。
#    ⇒ 判据：前面是 ~/ $HOME {HOME} os.path.join(… 后面跟 / 才是落点。
_PATH_CTX = re.compile(
    r"(?:~/|\$HOME/|\{HOME\}/|\$\{HOME\}/|Join-Path[^\n]{0,40}|os\.path\.join\([^\n]{0,40})"
    + re.escape(SIG["3-作者档案目录"])
    + r"/")

# ⛔ 教学/否定/分享行豁免（与 relocate_rules._ARCHIVE_REF_MARKERS 同源判据，2026-10-03 #27）：
#   行内出现「解药串 `~/个人AI档案`」或教学/元讨论标记词 ⇒ 该行在“讲该用什么”=教学举例，
#   不是落点（改了毁教学意义）。实测：发布包 B 类 指令编写规范 6 处均为该形态（伪安全教学）。
_REF_CTX_MARKERS = (
    os.path.expanduser("~"), "伪安全", "应改", "不安全", "违规",
    "反哺", "硬编码", "路径泛化", "静默失效", "通用化",
    "检测", "判据", "门禁", "grep", "重叠",
    "绑定", "分享", "不硬编码", "非个人", "变量化", "不碰",
)


def scan_one(path, cls):
    raw, kind = code_surface(path)
    hits = []
    for name, sig in SIG.items():
        if sig is None:
            continue
        if name in ALLOW.get(cls, set()):
            continue
        if name == "3-作者档案目录":
            # ⛔ 只认**路径上下文**（见 _PATH_CTX 注释）；教学/否定/分享行不认（见 _REF_CTX_MARKERS）
            for line in raw.split("\n"):
                if any(mk in line for mk in _REF_CTX_MARKERS):
                    continue
                for m in _PATH_CTX.finditer(line):
                    hits.append((name, 1, m.group(0)[:44]))
            continue
        if sig in raw:
            n = raw.count(sig)
            hits.append((name, n, ""))
    if "4-本机绝对路径" not in ALLOW.get(cls, set()):
        for m in ABS_RE.finditer(raw):
            seg = m.group(0)
            # 取「用户名段」：POSIX 取最后一段；Windows 取 `Users\` 之后那段
            if "\\" in seg:
                user = seg.split("\\")[-1]
            else:
                user = seg.rstrip("/").split("/")[-1]
            if not user or PLACEHOLDER.match(user):
                continue                          # 占位符 ⇒ 跳过
            hits.append(("4-本机绝对路径", 1, m.group(0)[:36]))
    if "5-作者工作记录" not in ALLOW.get(cls, set()):
        for m in WORK_RE.finditer(raw):
            hits.append(("5-作者工作记录", 1, m.group(0)[:40]))
    if "6-作者签名式格式" not in ALLOW.get(cls, set()):
        for m in SIGN_RE.finditer(raw):
            hits.append(("6-作者签名式格式", 1, m.group(0)))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg-root", default=PKG)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    report, nfiles = [], 0
    for cls, rels in CLASSES:
        files = []
        for rel in rels:
            p = os.path.join(a.pkg_root, rel)
            if os.path.isfile(p):
                files.append(p)
            elif os.path.isdir(p):
                for r, dn, fs in os.walk(p):
                    dn[:] = [d for d in dn if d not in SKIP_DIR]
                    files += [os.path.join(r, f) for f in fs
                              if ".bak" not in f and not f.endswith(".pyc")]
        nfiles += len(files)
        for f in files:
            if any(x in f for x in EXEMPT):
                continue                       # 检测器本体豁免
            h = scan_one(f, cls)
            if h:
                report.append((cls, os.path.relpath(f, a.pkg_root), h))
    # ── E 腿：指纹池去私有（2026-10-03·根治）──────────────────────
    #   判据：非空指纹池必须声明 sample_seed（中立样例源）——否则判红；
    #   带 seed_root_hash 且非空 ⇒ 作者档案派生指纹 ⇒ 判红。
    import json as _json
    _pool = os.path.join(a.pkg_root, "references/integrity-fingerprints.json")
    if os.path.isfile(_pool):
        try:
            _d = _json.load(open(_pool, encoding="utf-8"))
        except Exception:
            _d = {}
        _fps = _d.get("fingerprints") or []
        _hits = []
        if _fps and not _d.get("sample_seed"):
            _hits.append(("9-指纹池非中立源", len(_fps), "非空且未声明中立样例源 sample_seed"))
        if _fps and _d.get("seed_root_hash"):
            _hits.append(("9-指纹池非中立源", 1, "含 seed_root_hash（作者档案派生）"))
        if _hits:
            report.append(("E-指纹池（去私有）", "references/integrity-fingerprints.json", _hits))
    if a.json:
        import json
        print(json.dumps([{"class": c, "file": f,
                           "hits": [{"sig": s, "n": n, "sample": x} for s, n, x in h]}
                          for c, f, h in report], ensure_ascii=False, indent=2))
    else:
        by = {}
        for c, f, h in report:
            by.setdefault(c, []).append((f, h))
        print("=== 给用户的东西 · 分层隐私审计 ===\n扫描 %d 文件\n" % nfiles)
        for c, _rels in CLASSES:
            items = by.get(c, [])
            bad = {}
            for f, h in items:
                for s, n, x in h:
                    bad.setdefault(s, []).append((f, x))
            if not items:
                print("%-24s ✅ 无命中" % c)
                continue
            print("%-24s ❌ %d 文件" % (c, len(items)))
            for s in sorted(bad):
                lst = bad[s]
                print("    · %s × %d" % (s, len(lst)))
                for f, x in lst[:3]:
                    print("        %s%s" % (f[:66], ("  ← " + x) if x else ""))
                if len(lst) > 3:
                    print("        …另 %d 处" % (len(lst) - 3))
        print("\n%s" % ("✅ 全部干净" if not report
                        else "❌ %d 文件命中——⛔ 不可发包" % len(report)))
    return 1 if report else 0


if __name__ == "__main__":
    raise SystemExit(main())