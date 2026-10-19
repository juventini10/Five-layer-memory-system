#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/test_runtime_paths.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""test_runtime_paths.py —— R1–R12 承重验收

承重思路：**造一个只填 `archive_root` 的空包**，再验声明机制会不会
静默把它变成"看起来装好了"。这是本机制唯一真正要防的失败。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util as il
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # .../references/scripts
PKG = os.path.dirname(os.path.dirname(HERE))               # .../布洛陀-全平台安装包
sys.path.insert(0, HERE)
sys.path.insert(0, PKG)

# ── 载入被测模块 ─────────────────────────────────────────────
spec = il.spec_from_file_location("runtime_paths",
                                  os.path.join(HERE, "runtime_paths.py"))
rp_mod = il.module_from_spec(spec)
spec.loader.exec_module(rp_mod)
# B16根治(2026-10-05·台账B16)：本件设计运行面=包内 references/scripts/（PKG上溯两层即包根）；
# 作者态 HERE=脚本中心，上溯两层非包根 ⇒ import 断链。回落=由声明推包根（条文47·⛔不引入档案根字面）。
if not os.path.isfile(os.path.join(PKG, "install_scripts.py")):
    PKG = os.path.join(rp_mod.rp("archive_root"), "发布库/五层记忆系统/布洛陀-全平台安装包")
    sys.path.insert(0, PKG)
import install_scripts as INS

TMP = tempfile.mkdtemp(prefix="rt_paths_")
FIX = os.path.join(TMP, "MyVault")          # 用户的记忆中心·故意不叫档案根名（防投影字面泄漏·B修源v2）

# ── 造夹具：只建一部分目录（模拟"全新用户/半装"）────────────────
# ⚠️ 夹具目录名必须与 install_scripts.RUNTIME_PATH_DIRS **同源**。
#    2026-10-02 键落点改了（devtools 开发工具→脚本中心）⇒ 旧夹具造 `开发工具/`
#    目录已不存在 ⇒ 键被存在性过滤跳过 ⇒ R2b/R3 假红。
#    ⛔ 教训：夹具写死目录名 = 与落点表漂移的第二本账。
os.makedirs(os.path.join(FIX, "脚本中心"))
os.makedirs(os.path.join(FIX, "工作日志"))
os.makedirs(os.path.join(FIX, "数字分身", "K2切片蒸馏"))
# ⛔ 故意不建：记忆蓝图 / 技能配置 / 知识库  ⇒ 它们**不该**进声明

os.environ["BULUOTUO_RUNTIME_PATHS"] = os.path.join(TMP, "cfg", "runtime_paths.json")
rp_mod.reset_cache()

PASS, FAIL = [], []


def ck(name, cond, why=""):
    (PASS if cond else FAIL).append(name)
    print("  %s %-46s %s" % ("✅" if cond else "❌", name, why))


print("=== runtime_paths 承重验收 ===\n")

# R1 端中立：⛔ **可执行**代码里不得含端名/作者路径。
# ⚠️ 判据说明（前两版判据都不可信，此版用 AST 不用正则）：
#   v1 按行首 `#` 剥注释 → docstring 不是注释，漏放行内说明里的端名（误报）
#   v2 剥 docstring → 同上问题反过来，且易吞真代码
#   **v3（本版）= ast 解析：查「非 docstring 的字符串常量」+「所有标识符」**
#      ⇒ 文档随便写端名（那是给人看的），代码里出现就是污染。
import ast

_src = open(os.path.join(HERE, "runtime_paths.py"), encoding="utf-8").read()
_tree = ast.parse(_src)
# 收集所有 docstring 节点（模块/类/函数）→ 从检查集里排除
_doc_nodes = set()
for _n in ast.walk(_tree):
    if isinstance(_n, (ast.Module, ast.ClassDef, ast.FunctionDef,
                        ast.AsyncFunctionDef)):
        _d = ast.get_docstring(_n, clean=False)
        if _d is not None:
            _body = getattr(_n, "body", [])
            if _body and isinstance(_body[0], ast.Expr) and \
                    isinstance(_body[0].value, ast.Constant):
                _doc_nodes.add(id(_body[0].value))
_code_text = []
for _n in ast.walk(_tree):
    if isinstance(_n, ast.Constant) and isinstance(_n.value, str) \
            and id(_n) not in _doc_nodes:
        _code_text.append(_n.value)
    elif isinstance(_n, ast.Name):
        _code_text.append(_n.id)
    elif isinstance(_n, ast.Attribute):
        _code_text.append(_n.attr)
    elif isinstance(_n, (ast.FunctionDef, ast.ClassDef)):
        _code_text.append(_n.name)
_hay = "\n".join(_code_text).lower()
import os as _os, re as _re, getpass as _gp
_author_tag = _re.sub(r"\d+$", "", _os.environ.get("USER") or _gp.getuser()).lower()
banned = [w for w in ("hermes", "workbuddy", "trae-cn", "qoder", "zcode",
                      "/users/", "个人ai档案", "记忆蓝图",
                      "知识联邦引擎") + ((_author_tag,) if len(_author_tag) >= 6 else ())
          if w in _hay]
ck("R1 端中立·可执行代码无端名/作者路径", not banned, "命中：%s" % banned)

# R2 目录不存在 ⇒ 该键不写入声明（⛔ 不指空目录）
data = INS.build_runtime_paths(FIX)
ck("R2 不存在的目录不进声明", "blueprint" not in data and "skills" not in data)
ck("R2b 存在的目录进声明", "devtools" in data and "worklog" in data)
ck("R2c 嵌套路径正确", data.get("k2_slices", "").endswith(
    os.path.join("数字分身", "K2切片蒸馏")), data.get("k2_slices", ""))

# R3 记忆中心改名 ⇒ 键值跟着变（这就是解耦的意义）
ck("R3 记忆中心改名不影响键名", "devtools" in data and FIX in data["devtools"])

# R4 写 + 读闭环
written = rp_mod.write(data)
ck("R4 写读闭环", os.path.isfile(written) and rp_mod.rp("devtools") == data["devtools"])

# R5 缺键抛错（⛔ 不是 None、不是静默回落）
try:
    rp_mod.rp("blueprint")
    ck("R5 缺键抛 PathKeyMissing", False, "竟然没抛 ⇒ 静默回落风险")
except rp_mod.PathKeyMissing as e:
    ck("R5 缺键抛 PathKeyMissing", "blueprint" in str(e))
except Exception as e:
    ck("R5 缺键抛 PathKeyMissing", False, "抛了 %s" % type(e).__name__)

# R6 optional=True ⇒ None（⛔ 但由调用方显式处理）
ck("R6 optional 返 None", rp_mod.rp("blueprint", optional=True) is None)

# R7 声明文件不存在 ⇒ DeclNotFound（⛔ 不返回空 dict）
os.environ["BULUOTUO_RUNTIME_PATHS"] = os.path.join(TMP, "nope.json")
rp_mod.reset_cache()
try:
    rp_mod.rp("devtools")
    ck("R7 无声明文件抛 DeclNotFound", False, "竟然没抛")
except rp_mod.DeclNotFound:
    ck("R7 无声明文件抛 DeclNotFound", True)
except Exception as e:
    ck("R7 无声明文件抛 DeclNotFound", False, "抛了 %s" % type(e).__name__)

# R8 env 覆盖（BULUOTUO_PATH_*）—— 多实例/测试缝
os.environ["BULUOTUO_RUNTIME_PATHS"] = os.path.join(TMP, "cfg", "runtime_paths.json")
os.environ["BULUOTUO_PATH_DEVTOOLS"] = "/tmp/alt_devtools"
rp_mod.reset_cache()
ck("R8 env 覆盖生效", rp_mod.rp("devtools") == "/tmp/alt_devtools")
del os.environ["BULUOTUO_PATH_DEVTOOLS"]
rp_mod.reset_cache()

# R9 写前备份（铁律005）+ 原子写
rp_mod.write(data)
before = os.path.isfile(written + ".bak")
rp_mod.write(dict(data, worklog="/tmp/x"))
ck("R9 写前备份", before)
ck("R9b 无残留 .tmp", not os.path.isfile(written + ".tmp"))

# R10 相对路径被拒（⛔ 相对路径让 cwd 变成隐式依赖）
try:
    rp_mod.write({"devtools": "relative/path"})
    ck("R10 相对路径被拒", False, "竟然写进去了")
except ValueError:
    ck("R10 相对路径被拒", True)

# R11 🔴 造错——**空包**：只有 archive_root，其余目录全不存在
EMPTY = os.path.join(TMP, "EmptyVault")
os.makedirs(EMPTY)
e_data = INS.build_runtime_paths(EMPTY)
ck("R11a 空包只出 archive_root", set(e_data.keys()) == {"archive_root"},
   "实际：%s" % sorted(e_data.keys()))
os.environ["BULUOTUO_RUNTIME_PATHS"] = os.path.join(TMP, "empty.json")
rp_mod.write(e_data)
try:
    rp_mod.rp("devtools")
    ck("R11b 空包上取 devtools 报错（不静默）", False, "静默了 ⇒ 假绿")
except rp_mod.PathKeyMissing:
    ck("R11b 空包上取 devtools 报错（不静默）", True)

# R12 capability 声明 ↔ 目录约定 一致（⛔ 声明了但没实现 = 契约漂移）
cap_path = os.path.join(PKG, "adapters", "hermes", "capability.yaml")
cap_text = open(cap_path, encoding="utf-8").read()
declared = set()
for line in cap_text.split("\n"):
    if "- {key:" in line:
        declared.add(line.split("- {key:")[1].split(",")[0].strip())
impl = set(INS.RUNTIME_PATH_DIRS) | {"archive_root"}
ck("R12a capability 键 ⊆ 实现键", declared <= impl,
   "声明有实现无：%s" % sorted(declared - impl))
ck("R12b 实现键 ⊆ capability 声明", impl <= declared,
   "实现有声明无：%s" % sorted(impl - declared))

shutil.rmtree(TMP, ignore_errors=True)
print("\n%d/%d 通过" % (len(PASS), len(PASS) + len(FAIL)))
if FAIL:
    print("❌ 失败：%s" % FAIL)
sys.exit(1 if FAIL else 0)