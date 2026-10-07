#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""platform_adaptation_check.py — 端适配 100% 发版前置门禁（全端通用·2026-10-03）

把「自身 100% 才许映射」从单端点状修补升级为全端通用发版门禁：
**任一端未达 100% 适配 → 拒绝打包该端（--gate）**。机制代意志（愿景①·不依赖人记得）——
下次换端改造时，半成品映射在打包门禁就被拦下，⛔不再等装机后由用户发现。

判据三面（口径与 verify.sh §1.5/§1.6 **同源**·⛔不另立判据，防「声明面改了·门禁面没跟」同型病）：
  面A 五系统文件 — capability.yaml `system_file_paths` 归一化 5 键全声明（语义等价匹配：
                   SOUL.md≈SOUL / IDENTITY.md≈IDENTITY / USER.md≈USER / MEMORY.md≈MEMORY /
                   自定义指令≈customPrompt·2026-10-03 用户口径「自定义指令（customPrompt 等价物）」）
                  + 包内载体在位（adapters/<端>/rules|templates 含 .md——声明了映射却无载体=半成品）
  面B 钩子面     — `hooks_surface` 段声明 + delivered 每件**包内有源**（script 四候选目录 /
                   plugin 目录·「脚本已映射」的包内证据）；gaps=欠账 advisory 显形不判 FAIL
  面C 数字分身面 — `twin_surface` 段声明 + injection/guards 键（可选组件但「可选≠缺声明」·条文16 降级不阻塞）

用法：
  platform_adaptation_check.py --src <端> [--gate] [--json] [--pkg-root <包根>]

  无 --gate = 报告模式（exit 0·适配度与缺口全显）
  --gate    = 门禁模式：任一缺口 → exit 1（拒绝打包该端）
  --json    = 机器可读输出（供 verify.sh / install_scripts.py 挂接解析）

退出码：0=100% 适配（或报告模式）；1=门禁拒绝（缺口明细）；2=前置错误。
"""

import argparse
import json
import os
import re
import sys

# ── 五系统文件 语义等价组（2026-10-03·用户口径·⛔不逐字硬匹配——doubaowork 键名无 .md 后缀）──
SYSFILE_GROUPS = [
    ("SOUL",     {"SOUL.md", "SOUL"}),
    ("IDENTITY", {"IDENTITY.md", "IDENTITY"}),
    ("USER",     {"USER.md", "USER"}),
    ("MEMORY",   {"MEMORY.md", "MEMORY"}),
    ("CUSTOM",   {"自定义指令", "customPrompt"}),
]


def _read_cap(pkg_root, src):
    """读 capability.yaml 原文；不存在/不可读 → 抛 IOError。"""
    p = os.path.join(pkg_root, "adapters", src, "capability.yaml")
    if not os.path.isfile(p):
        raise IOError("占位端未接入：adapters/%s/capability.yaml 不存在" % src)
    with open(p, encoding="utf-8") as f:
        return f.read()


def _section(cap_text, name):
    """提取顶层段文本（'name:' 起到下一个顶层键止·键行本身入段）。零依赖 mini 解析。
    键匹配 `^name:`（容忍行内标量值如 `hooks_surface: none # 注释`——标量形态=端诚实能力声明）。
    ⚠️ 键行必须入段：标量形态一行即完成声明，⛔排除键行会把 `hooks_surface: none` 判成空段假红。"""
    out, on = [], False
    for ln in cap_text.split("\n"):
        s = ln.rstrip()
        if re.match(r"^%s:" % name, s):
            out.append(s)
            on = True
            continue
        if on:
            if s and not s.startswith((" ", "\t", "-", "#")) and re.match(r"^[A-Za-z_]+:", s):
                break
            out.append(s)
    return "\n".join(out)


def _sysfile_keys(cap_text):
    """system_file_paths 扁平块键集（键去引号·去尾注释·与 verify.sh §1.5 _mini_sysfiles 同族）。"""
    keys, in_blk, base = set(), False, None
    for ln in cap_text.split("\n"):
        if re.match(r"^system_file_paths:\s*(#.*)?$", ln.strip()):
            in_blk, base = True, None
            continue
        if not in_blk:
            continue
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        ind = len(ln) - len(ln.lstrip())
        if base is None:
            base = ind
        if ind < base:
            break
        body = ln.split("#", 1)[0].strip()
        if not body or ":" not in body:
            break
        k = body.split(":", 1)[0].strip().strip('"').strip("'")
        keys.add(k)
    return keys


def _hook_entries(cap_text):
    """hooks_surface 的 delivered/gaps 条目（script/plugin 双形态·与 verify.sh §1.6 section() 同族）。
    子段行带缩进（`  delivered:`）→ 行级 strip 后按 delivered/gaps 状态机归类。"""
    sec = _section(cap_text, "hooks_surface")
    out_d, out_g, cur = [], [], None
    for ln in sec.split("\n"):
        s = ln.strip()
        if re.match(r"^delivered:\s*(#.*)?$", s):
            cur = "d"
            continue
        if re.match(r"^gaps:\s*(#.*)?$", s):
            cur = "g"
            continue
        if cur is None:
            continue
        m = re.search(r"script:\s*([A-Za-z0-9_.\-]+\.py)", ln)
        if m:
            (out_d if cur == "d" else out_g).append(("script", m.group(1)))
            continue
        m = re.search(r"plugin:\s*([A-Za-z0-9_.\-]+)", ln)
        if m:
            (out_d if cur == "d" else out_g).append(("plugin", m.group(1)))
    return sec, out_d, out_g


def _has_carrier(pkg_root, src, cap=None):
    """包内五系统文件载体·**两种合法形态**（2026-10-03 补第二形态）。

    形态 1「端专属模板」：`adapters/<端>/rules|templates` 含 ≥1 个 .md（合并式承载合法）。
        适用=端要对五件**改结构或并入别处**的端（zcode 并 AGENTS.md / traework 拆四件 /
        doubaowork 走粘贴文本）。

    形态 2「公共模板 + 端名注入」：capability 显式 `system_file_tpl_mode: shared`。
        适用=**扁平配置根端**（WorkBuddy 等）：五件原样用公共 `references/templates/`，
        合成时按 capability 的 `display_name`/`emoji` 注入端名与署名
        （落点见 step5「端名注入（G2-2 走查缺陷修·ID-5）」）。
        这是一等设计形态，⛔ **不是"没做适配"** ⇒ 不得因缺端专属模板而判半成品。

    ⚠️ 为什么必须显式声明而不是"自动认共享"：自动认 ⇒ 加个目录就能绕过载体检查，
    判据形同虚设；显式声明 ⇒ 端必须写明"我走共享模板路线"，是一次表态。
    """
    for d in ("rules", "templates"):
        p = os.path.join(pkg_root, "adapters", src, d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if fn.endswith(".md"):
                return True
    if (cap or {}).get("system_file_tpl_mode") == "shared":
        tpl = os.path.join(pkg_root, "references", "templates")
        if os.path.isdir(tpl) and any(
                fn.endswith(".md") for fn in os.listdir(tpl)):
            return True
    return False


# ── 面B 包内有源候选目录（与 verify.sh §1.6 pkg_src_dirs 同族）────────────────────
def _has_pkg_src(pkg_root, src, kind, name):
    if kind == "plugin":
        return os.path.isdir(os.path.join(pkg_root, "adapters", src, "plugins", name))
    for d in ("references/scripts", "references/hooks",
              "references/digital-twin/devtools", os.path.join("adapters", src, "hooks")):
        if os.path.isfile(os.path.join(pkg_root, d, name)):
            return True
    return False


def check_adaptation(pkg_root, src):
    """三面判据 → (passed, faces, missing, notes)。"""
    faces, missing, notes = {}, [], []
    cap_text = _read_cap(pkg_root, src)
    # 轻量解析 capability 顶层键值（_has_carrier 需要 system_file_tpl_mode·⛔ 不引 yaml 依赖）
    _cap = {}
    for _ln in cap_text.split("\n"):
        _m = re.match(r"^([a-z_]+):\s*([^#\n]+?)\s*$", _ln)
        if _m:
            _cap[_m.group(1)] = _m.group(2).strip().strip("\"'")

    # ── 面A：五系统文件 声明 + 包内载体 ──
    keys = _sysfile_keys(cap_text)
    miss_groups = [g for g, alts in SYSFILE_GROUPS if not (keys & alts)]
    declared = len(SYSFILE_GROUPS) - len(miss_groups)
    carrier = _has_carrier(pkg_root, src, _cap)
    a_ok = (declared == len(SYSFILE_GROUPS)) and carrier
    if miss_groups:
        missing.append("面A 缺声明键: %s" % ", ".join(miss_groups))
    if not carrier:
        missing.append("面A 包内载体缺失: adapters/%s/rules|templates 无 .md（声明了映射却无内容=半成品）" % src)
    faces["A_五系统文件"] = {
        "ok": a_ok, "declared": declared, "total": len(SYSFILE_GROUPS),
        "carrier": carrier, "missing": miss_groups,
    }

    # ── 面B：hooks_surface 段（列表=delivered 包内有源 / 标量=端诚实能力声明·皆 PASS）──
    sec, delivered, gaps = _hook_entries(cap_text)
    b_ok = False
    if not sec.strip():
        missing.append("面B hooks_surface 未声明（条文33·fail-closed）")
        faces["B_钩子面"] = {"ok": False, "declared": False, "delivered": [], "gaps": gaps, "missing_src": []}
    else:
        no_src = [(k, n) for k, n in delivered if not _has_pkg_src(pkg_root, src, k, n)]
        b_ok = not no_src
        if no_src:
            missing.append("面B delivered 包内无源: %s" % ", ".join(n for _, n in no_src))
        if gaps:
            notes.append("面B gaps 欠账 %d 件（advisory·修复前如实可见）" % len(gaps))
        if not delivered and not gaps:
            notes.append("面B 标量声明（无列表条目·端专属机制承接·如 none/ui_paste）")
        faces["B_钩子面"] = {
            "ok": b_ok, "declared": True, "delivered": [n for _, n in delivered],
            "gaps": [n for _, n in gaps], "missing_src": [n for _, n in no_src],
        }

    # ── 面C：twin_surface 段（列表=injection/guards 键 / 标量=端诚实能力声明·皆 PASS）──
    tsec = _section(cap_text, "twin_surface")
    c_ok = False
    if not tsec.strip():
        missing.append("面C twin_surface 未声明（数字分身=可选组件但「可选≠缺声明」·条文16）")
        faces["C_数字分身面"] = {"ok": False, "declared": False, "keys": []}
    else:
        tkeys = [k for k in ("injection", "guards", "reach", "gaps") if re.search(r"^\s*%s:" % k, tsec, re.M)]
        c_ok = True
        if tkeys and not (set(tkeys) & {"injection", "guards"}):
            notes.append("面C 列表形态缺 injection/guards 键（advisory）")
        if not tkeys:
            notes.append("面C 标量声明（如 ui_paste·端专属通道承接）")
        faces["C_数字分身面"] = {"ok": c_ok, "declared": True, "keys": tkeys}

    passed = a_ok and b_ok and c_ok
    return passed, faces, missing, notes


def main():
    ap = argparse.ArgumentParser(description="端适配 100% 发版前置门禁")
    ap.add_argument("--src", required=True, help="端 ID（adapters/<端>/）")
    ap.add_argument("--gate", action="store_true", help="门禁模式：未达 100%% → exit 1（拒绝打包该端）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--pkg-root", default=os.path.dirname(os.path.abspath(__file__)),
                    help="安装包根（默认=本脚本所在目录）")
    a = ap.parse_args()

    pkg_root = os.path.abspath(a.pkg_root)
    if not os.path.isdir(os.path.join(pkg_root, "adapters", a.src)):
        print(json.dumps({"src": a.src, "gate": a.gate, "passed": False,
                          "reason": "占位端未接入：adapters/%s 不存在" % a.src}, ensure_ascii=False)
              if a.json else "❌ 端 %s 未接入适配器（adapters/%s 不存在）→ 禁止打包" % (a.src, a.src))
        return 1 if a.gate else 0

    try:
        passed, faces, missing, notes = check_adaptation(pkg_root, a.src)
    except IOError as e:
        print(json.dumps({"src": a.src, "gate": a.gate, "passed": False, "reason": str(e)},
                         ensure_ascii=False) if a.json else "❌ %s → 禁止打包" % e)
        return 1 if a.gate else 0

    if a.json:
        print(json.dumps({"src": a.src, "gate": a.gate, "passed": passed,
                          "faces": faces, "missing": missing, "notes": notes}, ensure_ascii=False))
    else:
        a_ = faces["A_五系统文件"]; b_ = faces["B_钩子面"]; c_ = faces["C_数字分身面"]
        print("[端] %s" % a.src)
        print("  面A 五系统文件: %s 声明 %d/%d · 载体%s%s" % (
            "✅" if a_["ok"] else "❌", a_["declared"], a_["total"],
            "在位" if a_["carrier"] else "缺失", " · 缺: %s" % ", ".join(a_["missing"]) if a_["missing"] else ""))
        if b_["declared"]:
            print("  面B 钩子面: %s delivered %d 件包内有源%s" % (
                "✅" if b_["ok"] else "❌", len(b_["delivered"]),
                " · 缺源: %s" % ", ".join(b_["missing_src"]) if b_["missing_src"] else ""))
            if b_["gaps"]:
                print("       gaps 欠账 %d 件（advisory）" % len(b_["gaps"]))
        else:
            print("  面B 钩子面: ❌ 未声明（条文33·fail-closed）")
        if c_["declared"]:
            print("  面C 数字分身面: %s twin_surface 已声明（键: %s）" % (
                "✅" if c_["ok"] else "❌", "/".join(c_["keys"])))
        else:
            print("  面C 数字分身面: ❌ 未声明（可选≠缺声明·条文16）")
        for n in notes:
            print("  [i] %s" % n)
        if passed:
            print("=> 适配度 100%%%s" % (" · --gate 放行" if a.gate else ""))
        else:
            print("=> 适配度未达 100%% → %s" % ("**拒绝打包该端**" if a.gate else "缺口清单见上"))
            for m in missing:
                print("   ⛔ %s" % m)

    return 0 if (not a.gate or passed) else 1


if __name__ == "__main__":
    sys.exit(main())
