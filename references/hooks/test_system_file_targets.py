#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_system_file_targets.py —— 项 3/4 承重验收：系统文件落点解析

核心命题：**落点必须来自端声明，不是硬编码 `[配置根]/`**。
写错 ⇒ 文件在盘上但端根本不读，而 verify 只查"文件在不在" ⇒ 恒真假绿。

用例：
  T1 扁平端（未声明）⇒ 五件全落配置根（向后兼容·行为不变）
  T2 Hermes 声明 ⇒ USER/MEMORY 落 memories/·IDENTITY 为 None
  T3 段 id 从声明读·未声明时派生稳定 id
  T4 两路 YAML 解析一致（PyYAML / 内置 mini-YAML）
  T5 造错：把 Hermes 声明删掉 ⇒ T2 必须 FAIL（证明判据可区分）
  T6 造错：全角/CJK 不影响解析
  T7 端中立性：⛔ 函数本身不含任何端名字符串（防"为 Hermes 特判"）
  T8 三形态解析（~/ 绝对 / :: 字段级 / platform:// 平台托管）——C29 承重
  T9 九端键名=条文32 协议逐字一致（键名三源归一的账）+裸名键负例
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import os
import re
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(os.path.dirname(_HERE))
_spec = importlib.util.spec_from_file_location("ins", os.path.join(_PKG, "install_scripts.py"))
ins = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ins)

PASS, FAIL = [], []


def _t(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  ❌ ") + name + (("  · " + detail) if detail and not cond else ""))
    return cond


def t1_flat_default():
    print("T1 扁平端（未声明）⇒ 全落配置根")
    root = os.path.expanduser("~/.workbuddy")
    tg = ins.system_file_targets(root, {})
    _t("四件都有落点", all(v is not None for v in tg.values()), repr(tg))
    for f, p in tg.items():
        _t("%s 落配置根" % f, p == os.path.join(root, f), p)
    # cap=None 也必须能跑（调用方可能没读 yaml）
    tg2 = ins.system_file_targets(root, None)
    _t("cap=None 同行为", tg2 == tg)


def t2_hermes_declared():
    print("T2 Hermes 声明 ⇒ memories/ + IDENTITY=None")
    cap = ins.load_capability(os.path.join(_PKG, "adapters/hermes/capability.yaml"))
    _t("声明存在", bool(cap.get("system_file_paths")), repr(cap.get("system_file_paths")))
    root = os.path.expanduser("~/.hermes")
    tg = ins.system_file_targets(root, cap)
    _t("SOUL.md → 配置根", tg["SOUL.md"] == os.path.join(root, "SOUL.md"), tg["SOUL.md"])
    _t("USER.md → memories/", tg["USER.md"] == os.path.join(root, "memories/USER.md"), tg["USER.md"])
    _t("MEMORY.md → memories/", tg["MEMORY.md"] == os.path.join(root, "memories/MEMORY.md"), tg["MEMORY.md"])
    _t("IDENTITY.md → None（无载体·⛔不许落配置根）", tg["IDENTITY.md"] is None, repr(tg["IDENTITY.md"]))


def t3_segments():
    print("T3 段 id 解析")
    cap = ins.load_capability(os.path.join(_PKG, "adapters/hermes/capability.yaml"))
    sg = ins.system_file_segments(cap)
    _t("SOUL 段 id 来自声明", sg["SOUL.md"] == "soul.persona", sg["SOUL.md"])
    _t("USER 段 id 来自声明", sg["USER.md"] == "user.profile", sg["USER.md"])
    # 未声明 ⇒ 派生稳定 id（两次调用必须一致·⛔ 不许带随机/时间）
    a = ins.system_file_segments({})
    b = ins.system_file_segments(None)
    _t("未声明时派生且稳定", a == b and a["SOUL.md"] == "sys.soul", repr(a))
    # C29·键名归一后第五件派生 slug 必须保持旧值（段 id 一经断章不可漂移）
    _t("第五件派生 slug 不漂移", a.get("自定义指令") == "sys.customprompt", repr(a.get("自定义指令")))
    for v in a.values():
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", v):
            _t("段 id 合规", False, v)
            return
    _t("段 id 合规（引擎白名单）", True)


def t4_two_yaml_paths():
    print("T4 两路 YAML 解析一致")
    p = os.path.join(_PKG, "adapters/hermes/capability.yaml")
    try:
        import yaml
        a = yaml.safe_load(open(p, encoding="utf-8"))
        route = "PyYAML"
    except ModuleNotFoundError:
        a = None
        route = "仅内置"
    b = ins._mini_yaml(open(p, encoding="utf-8").read())
    _t("内置 mini-YAML 能读到声明",
       (b.get("system_file_paths") or {}).get("USER.md") == "memories/USER.md",
       repr(b.get("system_file_paths")))
    if a is not None:
        _t("两路 system_file_paths 一致",
           a.get("system_file_paths") == b.get("system_file_paths"))
        _t("两路 config_root 一致", a.get("config_root") == b.get("config_root"))


def t5_falsification():
    print("T5 造错：删掉 Hermes 声明 ⇒ T2 判据必须 FAIL（防恒真）")
    p = os.path.join(_PKG, "adapters/hermes/capability.yaml")
    orig = open(p, encoding="utf-8").read()
    # 造错：模拟"没写声明"的端
    stripped = re.sub(r"system_file_paths:.*?(?=\n# 段 id 映射)",
                      "system_file_paths: {}\n", orig, flags=re.S)
    _t("造错确实改了文件内容（否则本用例恒真）", stripped != orig)
    tmp = tempfile.mkdtemp()
    q = os.path.join(tmp, "capability.yaml")
    try:
        open(q, "w", encoding="utf-8").write(stripped)
        cap = ins.load_capability(q)
        tg = ins.system_file_targets("/root/.hermes", cap)
        _t("无声明 ⇒ 落回配置根（USER 变成 ~/.hermes/USER.md）",
           tg["USER.md"] == "/root/.hermes/USER.md", tg["USER.md"])
        _t("这正是旧缺陷的形态（落错·但 verify 查不出来）", True)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def t6_cjk_safe():
    print("T6 路径含 CJK 不影响解析")
    root = os.path.expanduser("~/测试 记忆中心/.hermes")
    cap = ins.load_capability(os.path.join(_PKG, "adapters/hermes/capability.yaml"))
    tg = ins.system_file_targets(root, cap)
    _t("USER 落点在 CJK 路径下正确", tg["USER.md"] == os.path.join(root, "memories/USER.md"), tg["USER.md"])


def t7_endpoint_neutral():
    print("T7 端中立性（⛔ 函数内不含任何端名硬编码）")
    src = ""
    for fn in ("system_file_targets", "system_file_segments"):
        src += "\n".join(l for l in inspect_lines(fn))
    banned = ["hermes", "workbuddy", "qoder", "zcode", "trae", "lobster", "autoclaw", "doubao"]
    hit = [b for b in banned if b in src.lower()]
    _t("无任何端名硬编码（防为 Hermes 特判）", not hit, repr(hit))


def inspect_lines(fn_name):
    import inspect
    return inspect.getsource(getattr(ins, fn_name)).split("\n")


SSOT5 = ("SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md", "自定义指令")


def _key_check(paths):
    """键集对协议判据（T9 与负例共用同一把尺·⛔两套逻辑）。"""
    if not isinstance(paths, dict):
        return ["缺段"]
    return [("+%s" % k) for k in paths if k not in SSOT5] + \
           [("-%s" % k) for k in SSOT5 if k not in paths]


def t8_three_forms():
    print("T8 三形态解析（C29·~/ :: platform://）")
    cap = {"system_file_paths": {
        "SOUL.md": "~/custom-home/SOUL.md",
        "IDENTITY.md": "sub/IDENTITY.md",
        "USER.md": "platform://memory/user-cards",
        "MEMORY.md": None,
        "自定义指令": "app/app-config.json::personalization.customPrompt",
    }}
    tg = ins.system_file_targets("/root/.cfg", cap)
    _t("~/ ⇒ expanduser 绝对（⛔不拼配置根）",
       tg["SOUL.md"] == os.path.expanduser("~/custom-home/SOUL.md"), repr(tg["SOUL.md"]))
    _t("相对值 ⇒ 拼 config_root（向后兼容）",
       tg["IDENTITY.md"] == "/root/.cfg/sub/IDENTITY.md", repr(tg["IDENTITY.md"]))
    _t("platform:// ⇒ 平台托管目标（无文件可写）",
       tg["USER.md"] == {"platform": "platform://memory/user-cards"}, repr(tg["USER.md"]))
    _t("None ⇒ None（无载体）", tg["MEMORY.md"] is None, repr(tg["MEMORY.md"]))
    ft = tg["自定义指令"]
    _t(":: ⇒ 结构化字段目标（宿主文件+字段路径·⛔按 md 整写会毁配置）",
       isinstance(ft, dict) and ft.get("file") == "/root/.cfg/app/app-config.json"
       and ft.get("field") == "personalization.customPrompt", repr(ft))
    # 负例（防恒真）：宿主文件路径被拼上 ::（旧缺陷形态）必须不再出现
    _t("旧缺陷形态不复现（值里不再含 :: 字面）",
       "::" not in str(ft), repr(ft))


def t9_key_protocol():
    print("T9 九端键名=条文32 协议")
    adir = os.path.join(_PKG, "adapters")
    bad = []
    n_cov = 0
    for pid in sorted(os.listdir(adir)):
        p = os.path.join(adir, pid, "capability.yaml")
        if not os.path.isfile(p):
            continue
        n_cov += 1
        cap = ins.load_capability(p)
        v = _key_check(cap.get("system_file_paths"))
        if v:
            bad.append((pid, v))
    _t("adapters 全端键集=条文32 五键（含显式 null 缺件声明·NOKEY=0）", not bad, repr(bad))
    _t("覆盖端数 ≥9", n_cov >= 9, "n=%d" % n_cov)
    # 负例（防恒真）：裸名键必须被同一把尺判出
    neg = _key_check({"SOUL": "SOUL.md", "IDENTITY.md": None, "USER.md": None,
                      "MEMORY.md": None, "自定义指令": None})
    _t("负例：裸名键「SOUL」被协议判出", "+SOUL" in neg and "-SOUL.md" in neg, repr(neg))


def main():
    print("=== 项 3/4 承重验收 · 系统文件落点解析 ===\n")
    for fn in (t1_flat_default, t2_hermes_declared, t3_segments,
               t4_two_yaml_paths, t5_falsification, t6_cjk_safe, t7_endpoint_neutral,
               t8_three_forms, t9_key_protocol):
        fn()
        print("")
    print("=" * 52)
    print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("❌ 失败项：" + " · ".join(FAIL))
        return 1
    print("✅ 全部通过（落点来自端声明·扁平端行为不变）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())