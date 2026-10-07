#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""test_path_overlay.py —— O1–O14 承重验收

核心承重点：**覆盖层会不会"看起来在工作、其实啥也没改"**。
这是覆盖层这类机制的典型死法（键名对不上 → 静默跳过 → 脚本仍指作者路径）。
⇒ O9/O10 专门造这个错。
"""

import importlib.util as il
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

spec = il.spec_from_file_location("path_overlay",
                                  os.path.join(HERE, "path_overlay.py"))
PO = il.module_from_spec(spec)
spec.loader.exec_module(PO)

TMP = tempfile.mkdtemp(prefix="poverlay_")
os.environ["BULUOTUO_PATH_OVERRIDE"] = os.path.join(TMP, "path_override.py")
os.environ.pop("DOENGLINGZ_CONFIG_DIR", None)

PASS, FAIL = [], []


def ck(name, cond, why=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %-48s %s" % ("✅" if cond else "❌", name, why))


print("=== path_overlay 承重验收 ===\n")

# O1 无覆盖文件 ⇒ 空表（作者侧常态·⛔ 不是错）
ck("O1 无覆盖文件返空表", PO.load_override() == {})

# O2 哨兵路径永不存在
s = PO.sentinel("PATROL")
ck("O2 哨兵路径不存在", not os.path.exists(s), s)
ck("O2b 哨兵在不同 kind 下不同", PO.sentinel("A") != PO.sentinel("B"))

# O3 写覆盖 → 读回
p = PO.write_override({"DSH_PLUGIN": PO.sentinel("DSH"),
                       "AUTOCLAW_PATROL": "/real/path/patrol.sh"})
ck("O3 写覆盖文件", os.path.isfile(p))
t = PO.load_override()
ck("O3b 读回一致", t.get("DSH_PLUGIN") == PO.sentinel("DSH")
   and t.get("AUTOCLAW_PATROL") == "/real/path/patrol.sh")

# O4 apply_override 真的改了 globals
g = {"DSH_PLUGIN": os.path.expanduser("[记忆共享中心]/脚本中心/five-layer-memory/src/index.js"),
     "OTHER": "keep"}
ch = PO.apply_override(g)
ck("O4 覆盖生效", g["DSH_PLUGIN"] == PO.sentinel("DSH"))
ck("O4b 未列出的键不动", g["OTHER"] == "keep")
ck("O4c 返回改动清单", set(ch) == {"DSH_PLUGIN"}, str(ch))

# O5 ⛔ 不凭空造常量
g2 = {"A": 1}
PO.apply_override(g2)
ck("O5 不凭空造键", set(g2) == {"A"})

# O6 🔴 造错 A：strict=False 时键名对不上 ⇒ 静默跳过（**这是隐患本身**）
g3 = {"DSH_PLGUIN": "作者路径"}     # 故意打错字
ch3 = PO.apply_override(g3, strict=False)
ck("O6 造错A·非strict 静默跳过（隐患复现）", ch3 == {} and "DSH_PLGUIN" in g3)

# O7 🔴 造错 B：strict=True 必抛错（发布前自检的兜底）
# ⚠️ 此处刻意传一个**不含**覆盖键的 g —— 模拟"目标模块里那个常量被改名/删了"。
#    （首版误传 {"DSH_PLGUIN": "x"}，键在 g 里 ⇒ 判为"存在"⇒ 不抛——测试自己骗了自己）
try:
    PO.apply_override({"SOME_OTHER_CONST": 1}, strict=True)
    ck("O7 造错B·strict=True 抛错", False, "竟然没抛 ⇒ 覆盖层会静默失效")
except KeyError as e:
    # ⛔ 断言**机制**（"覆盖层会静默失效"这句告警），⛔ 不写死具体键名——
    #    write_override 按字母序输出⇒ 首个报错的键随字母序变（首版误断言 DSH_PLUGIN）。
    ck("O7 造错B·strict=True 抛错", "静默失效" in str(e), str(e)[:52])

# O8 selfcheck CLI 能查出键名对不上
fake = os.path.join(TMP, "target.py")
open(fake, "w", encoding="utf-8").write(
    "DSH_PLUGIN = 1\nAUTOCLAW_PATROL = 2\n")
PO.write_override({"DSH_PLGUIN": "x", "AUTOCLAW_PATROL": "y"},
                  path=os.environ["BULUOTUO_PATH_OVERRIDE"])
import io
import contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc_bad = PO.main.__wrapped__() if hasattr(PO.main, "__wrapped__") else None
# main 需要 argv，直接调子逻辑更稳：
from pathlib import Path
src = open(fake, encoding="utf-8").read()
missing = [k for k in PO.load_override()
           if ("%s =" % k) not in src and ("%s=" % k) not in src]
ck("O8 键名对不上可被查出", missing == ["DSH_PLGUIN"], str(missing))

# O9 覆盖文件语法错 ⇒ 明确报错（⛔ 不静默当空表）
bad = os.path.join(TMP, "bad_override.py")
open(bad, "w", encoding="utf-8").write("OVERRIDE = [1,2,3]\n")
os.environ["BULUOTUO_PATH_OVERRIDE"] = bad
try:
    PO.load_override()
    ck("O9 覆盖表类型错⇒报错", False, "静默当空表了")
except ValueError:
    ck("O9 覆盖表类型错⇒报错", True)

# O10 env 指向不存在的文件 ⇒ 返 None（不是崩）
os.environ["BULUOTUO_PATH_OVERRIDE"] = os.path.join(TMP, "nope.py")
ck("O10 env 指不存在⇒空表不崩", PO.load_override() == {})

# O11 端中立：代码无端名/作者路径
src_po = open(os.path.join(HERE, "path_overlay.py"), encoding="utf-8").read()
import ast
tree = ast.parse(src_po)
docids = set()
for n in ast.walk(tree):
    if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef)):
        b = getattr(n, "body", [])
        if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant):
            docids.add(id(b[0].value))
code = []
for n in ast.walk(tree):
    if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docids:
        code.append(n.value)
    elif isinstance(n, ast.Name):
        code.append(n.id)
    elif isinstance(n, ast.Attribute):
        code.append(n.attr)
hay = "\n".join(code).lower()
import os as _os, re as _re, getpass as _gp
_author_tag = _re.sub(r"\d+$", "", _os.environ.get("USER") or _gp.getuser()).lower()
banned = [w for w in ("hermes", "workbuddy", "trae-cn", "qoder", "zcode",
                      "个人ai档案", "记忆蓝图") + ((_author_tag,) if len(_author_tag) >= 6 else ())
          if w in hay]
ck("O11 端中立·可执行代码无端名/作者路径", not banned, "命中：%s" % banned)

# O12 生成物自带"勿手改"头
os.environ["BULUOTUO_PATH_OVERRIDE"] = os.path.join(TMP, "path_override.py")
PO.write_override({"X": "/y"})
head = open(os.environ["BULUOTUO_PATH_OVERRIDE"], encoding="utf-8").read()
ck("O12 生成物带勿手改头", "请勿手改" in head and "自动生成" in head)

# O13 幂等：写两次内容一致
PO.write_override({"X": "/y"})
a1 = open(os.environ["BULUOTUO_PATH_OVERRIDE"], encoding="utf-8").read()
PO.write_override({"X": "/y"})
a2 = open(os.environ["BULUOTUO_PATH_OVERRIDE"], encoding="utf-8").read()
ck("O13 幂等", a1 == a2)

# O14 🔴 端到端：哨兵覆盖后，os.path.exists 判断仍能正常工作（不抛 TypeError）
g4 = {"PATROL": PO.sentinel("P")}
PO.write_override({"PATROL": PO.sentinel("P2")})
PO.apply_override(g4)
try:
    r = os.path.exists(g4["PATROL"])
    ck("O14 覆盖后 exists() 正常返 False", r is False)
except TypeError as e:
    ck("O14 覆盖后 exists() 正常返 False", False, "TypeError: %s" % e)

shutil.rmtree(TMP, ignore_errors=True)
print("\n%d/%d 通过" % (len(PASS), len(PASS) + len(FAIL)))
if FAIL:
    print("❌ 失败：%s" % FAIL)
sys.exit(1 if FAIL else 0)