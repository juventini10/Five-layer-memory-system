#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plugin_path_scan.py —— 16 个插件的作者路径硬编码·AST 级分类

沿用 §3.3 的教训：⛔ 不一条正则打天下。先分类再动手。

分类：
  CONST     模块级路径常量         → 改定义即可（rp("devtools")）
  INLINE    调用内联实参            → 改实参即可
  JOIN      os.path.join(多段)      → 改整段
  PATTERN   re.compile 参数          → ⛔ 禁动
  FIXTURE   自测体                  → ⛔ 禁动
  LIST      列表/字典里的路径        → 逐条看
  PROMPT    提示词模板里的路径        → 看给谁看
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import ast
import io
import os
import re
import tokenize

PLUG = os.path.expanduser("~/.hermes/plugins")

KEYMAP = [
    (os.path.expanduser("[记忆共享中心]/脚本中心"), "kb_engine"),
    (os.path.expanduser("[记忆共享中心]/脚本中心/路由家族"), "custom_route"),
    (os.path.expanduser("[记忆共享中心]/脚本中心"), "devtools"),
    (os.path.expanduser("[记忆共享中心]/脚本中心"), "devtools"),
    (os.path.expanduser("[记忆共享中心]/工作日志"), "worklog"),
    ("个人AI档案/数字分身", "twin"),
    ("个人AI档案/知识库", "knowledge"),
    (os.path.expanduser("[记忆共享中心]/技能配置"), "skills"),
    (os.path.expanduser("[记忆共享中心]/记忆蓝图"), "blueprint"),
    (os.path.expanduser("~"), "archive_root"),
]
ORDER = sorted(KEYMAP, key=lambda x: len(x[0]), reverse=True)
PAT = re.compile("|".join(re.escape(k[0]) for k in ORDER))


def key_for(lit):
    for pref, key in KEYMAP:
        if pref in lit:
            return key, lit.split(pref, 1)[1].lstrip("/")
    return None, None


def classify(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    lines = src.split("\n")
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return None, "语法错 %s" % e

    comment = set()
    with open(path, "rb") as f:
        for t in tokenize.tokenize(f.readline):
            if t.type == tokenize.COMMENT:
                comment.add(t.start[0])

    pattern, fixture, const, inline, joinline, inlist = set(), set(), set(), set(), set(), set()
    for n in ast.walk(tree):
        # re.compile 参数
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                n.func.attr == "compile":
            for a in list(n.args) + [k.value for k in n.keywords]:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    pattern.add(a.lineno)
        # 自测体
        nm = getattr(n, "name", "")
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                any(k in nm.lower() for k in ("selftest", "self_test", "test_", "_t")):
            for s in ast.walk(n):
                if isinstance(s, ast.Constant) and isinstance(s.value, str):
                    fixture.add(s.lineno)
        # 模块级赋值
        if isinstance(n, (ast.Assign, ast.AnnAssign)):
            for t in getattr(n, "targets", []) + ([n.target] if isinstance(n, ast.AnnAssign) else []):
                if isinstance(t, ast.Name) and isinstance(n, ast.Assign):
                    v = n.value
                    if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) \
                            and v.func.attr == "expanduser":
                        const.add(n.lineno)
                    elif isinstance(v, ast.BinOp):
                        const.add(n.lineno)
    # os.path.join(多段) 所在行
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                n.func.attr == "join":
            lo = getattr(n, "end_lineno", n.lineno)
            for i in range(n.lineno, lo + 1):
                joinline.add(i)
    # expanduser 内联
    for i, ln in enumerate(lines, 1):
        if 'expanduser("~' in ln or "expanduser('~" in ln:
            inline.add(i)
    # 列表/字典字面量内
    for n in ast.walk(tree):
        if isinstance(n, (ast.List, ast.Dict, ast.Tuple, ast.Set)):
            for s in ast.walk(n):
                if isinstance(s, ast.Constant) and isinstance(s.value, str) \
                        and os.path.expanduser("~") in s.value:
                    inlist.add(s.lineno)

    out = []
    for i, ln in enumerate(lines, 1):
        if os.path.expanduser("~") not in ln:
            continue
        raw = ln.strip()
        if i in comment:
            c = "COMMENT"
        elif i in pattern:
            c = "PATTERN"
        elif i in fixture:
            c = "FIXTURE"
        elif i in const:
            c = "CONST"
        elif i in inline:
            c = "INLINE"
        elif i in joinline:
            c = "JOIN"
        elif i in inlist:
            c = "LIST"
        elif raw.startswith(('"', "'")) and raw.endswith(('"', "'")):
            c = "PROMPT"
        else:
            c = "OTHER"
        k, tail = key_for(ln)
        rep = ""
        if k and c in ("CONST", "INLINE", "JOIN"):
            rep = 'rp("%s")' % k if not tail else \
                  'rp("%s", "%s")' % (k, tail.replace("/", ", \""))
        out.append((i, c, raw[:70], rep))
    return out, None


TAGS = {"CONST": "✅", "INLINE": "✅", "JOIN": "✅",
        "PATTERN": "⛔", "FIXTURE": "⛔", "COMMENT": "·",
        "LIST": "⚠️", "PROMPT": "⚠️", "OTHER": "⚠️"}

print("=== 16 插件 · 作者路径硬编码 AST 分类 ===\n")
TOT = {}
plugins = sorted(d for d in os.listdir(PLUG)
                 if os.path.isfile(os.path.join(PLUG, d, "plugin.yaml")))
print("插件数：%d\n" % len(plugins))
for d in plugins:
    p = os.path.join(PLUG, d, "__init__.py")
    if not os.path.isfile(p):
        continue
    res, err = classify(p)
    if err:
        print("── %-32s ❌ %s" % (d, err)); continue
    if not res:
        continue
    cnt = {}
    for _i, c, _r, _x in res:
        cnt[c] = cnt.get(c, 0) + 1
        TOT[c] = TOT.get(c, 0) + 1
    print("── %-32s %d 处  %s" % (d, len(res),
          " ".join("%s%s×%d" % (TAGS[k], k, v) for k, v in sorted(cnt.items()))))
    for i, c, raw, rep in res:
        if c in ("CONST", "INLINE", "JOIN"):
            print("     L%-5d %-8s %s" % (i, c, raw))
            print("            → %s" % rep)

print("\n" + "=" * 70)
print("分类合计：")
for c, n in sorted(TOT.items(), key=lambda x: -x[1]):
    print("   %-8s %3d %s" % (c, n, TAGS[c]))
auto = TOT.get("CONST", 0) + TOT.get("INLINE", 0) + TOT.get("JOIN", 0)
print("\n可机械改 %d / %d" % (auto, sum(TOT.values())))