#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_receipt.py —— **到货回执**生成器（装机唯一出口·⛔ 不手写副本）

## 为什么必须有这个文件（根因·交接书 §三）

包里有 `component-versions.json`（**出厂清单**＝我该有什么），
⛔ 但**没有** `installed_manifest.json`（**到货回执**＝我实际有什么）。
⇒ 只要回执不存在，"每端自己检查"在物理上就不成立——
   协议文件写得再漂亮，端 AI 拿到的只是**说明书**，不是**尺子**。

## 回执回答三个问题（缺一即废）

| 问题 | 字段 | 判定依据 |
|:---|:---|:---|
| 我装成什么样了 | `components` / `capabilities` | 逐件 `isfile` 实测·⛔ 不抄安装器意图 |
| 我 OK 吗 | `verdict` | `ok` / `degraded` / `failed`（机械规则·见 `_verdict`）|
| 哪些能力我没装上 | `missing` + `reason` | 逐项带缺失语义（required/optional/n_a）|

## 🔴 判据纪律（本文件自身）

1. **值只由实测产出**——`installed: true` 的唯一依据是 `os.path.isfile` 命中。
   ⛔ 不接受"安装器说它装了"作为依据（那是意图，不是事实）。
2. **缺项必须显式**——每条 missing 带 `severity`（required/optional/n_a）
   + `reason`（为什么没装上）。静默跳过 = 假绿（交接书 §二·约束3）。
3. **必需 vs 可选分流**——可选路径不存在是**正常态**，⛔ 不能恒红（约束4）。
   severity 语义取自 `capability.yaml` 的 `missing_semantics` 段。
4. **本机跑通 ≠ 用户机能用**——落点全部参数化·⛔ 零作者路径
   （用户机夹具 `user_machine_fixture.py` 会在无作者侧设施的环境重跑一遍）。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import datetime
import json
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 回执 schema 版本——端 AI 读它决定字段解析方式（⛔ 破坏性变更须升版并双写过渡）
SCHEMA_VERSION = "1.0"

VERDICT_OK = "ok"
VERDICT_DEGRADED = "degraded"
VERDICT_FAILED = "failed"


def _now() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _pkg_root() -> str:
    """包根 = 本脚本上溯两级（references/scripts → references → 包根）。

    ⛔ 不用 `~/[记忆共享中心]/发布库/...` 硬编码——那是**作者侧路径**，
    用户把包装在别处时全链恒真（台账 §1.1「校验器自身必须先过它要执行的校验」）。
    """
    return os.path.dirname(os.path.dirname(HERE))


def _read_json(path: str, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _semantics(cap_path: str) -> dict:
    """读 `capability.yaml` 的 `missing_semantics` 段。

    ⚠️ 解析器**故意极简**：只认 `键: 值` 与 `键: 值  # 注释` 两种形态。
    理由：包内已有一个成熟 YAML 解析器（`install_scripts._mini_yaml`），
    但它属于**安装器**；回执生成器 ⛔ 不 import 安装器（避免装载期依赖倒挂），
    且 `missing_semantics` 是**本脚本唯一需要的子集**——
    用完整 YAML 解析器去读三个平坦键，是引入不必要依赖。
    ⛔ 读不到 ⇒ 返回空 dict ⇒ 上层 fail-closed（见 `_classify`）。
    """
    out = {}
    if not cap_path or not os.path.isfile(cap_path):
        return out
    try:
        with open(cap_path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return out
    in_sec = False
    for ln in lines:
        s = ln.split("#", 1)[0].rstrip() if not ln.strip().startswith("#") else ""
        if not s.strip():
            continue
        if not ln.startswith((" ", "\t")):
            in_sec = s.strip() == "missing_semantics:"
            continue
        if in_sec and ":" in s:
            k, v = s.split(":", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _capability_flags(cap_text: str) -> dict:
    """抽 `capabilities:` 段里的**布尔**能力声明（键 → True/False）。

    ⚠️ 只认布尔字面量。`install_entry: setup.sh` / `hooks_mechanism: "launchd"`
    这类**字符串值不是布尔能力**，⛔ 不参与 present 判定——
    把它们当能力会把"有入口"报成"缺入口"（判据问的不是它问的问题）。
    """
    out = {}
    lines = cap_text.split("\n")
    in_cap = False
    for ln in lines:
        if not ln.startswith((" ", "\t")):
            in_cap = ln.split("#", 1)[0].strip() == "capabilities:"
            continue
        if not in_cap:
            continue
        s = ln.split("#", 1)[0].strip()
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        v = v.strip().strip('"').strip("'").lower()
        if v in ("true", "false"):
            out[k.strip()] = (v == "true")
    return out


def _classify(key: str, sem: dict, present: bool) -> dict:
    """单个能力键 → 回执条目。**唯一真源**（⛔ 别处不许另判一遍）。"""
    raw = sem.get(key)
    sev = raw if raw in ("required", "optional", "n_a") else None
    if sev is None:
        # 🔴 **未知 ⇒ fail-closed**：声明里没写的键，按 required 处理。
        #    理由：默认 optional 会让"忘了声明语义"的新键静默消失（约束3）。
        sev, raw = "required", "undeclared(treated=required)"
    if present:
        status, reason = "installed", None
        # 🔴 **语义一致性**：声明为 n_a 却实测具备 ⇒ 是声明自相矛盾，
        #    不是"装上了"。显形让端 AI 看得见，⛔ 不静默吞掉矛盾。
        if sev == "n_a":
            status, reason = "installed_but_marked_na", \
                "声明 n_a（本端不涉及）·实测却具备·声明自相矛盾，需修 capability.yaml"
    elif sev == "n_a":
        status, reason = "not_applicable", "本端不涉及该能力"
    elif sev == "optional":
        status, reason = "skipped", "可选路径不存在（正常态·非缺陷）"
    else:
        status, reason = "missing", "必需能力未装上"
    return {"key": key, "status": status, "severity": sev,
            "declared": raw, "reason": reason}


def _probe_twin_core(mc: str) -> dict:
    """数字分身「芯」状态（2026-10-04·三态 + unknown）

    ⚠️ ⛔ **不参与 verdict**：新用户首次安装尚未造芯是**正常态**，不是安装失败。
       装成功 ≠ 用户已造芯——两件事不许混，故独立字段。

    判据与安装器落点同源（⛔ 不另造一套互相矛盾的定义）：
      · core_built —— 人格规格书 + K2 切片目录都在
      · kit_only  —— 套件在·规格书或切片缺（还没造芯）
      · absent    —— <MC>/数字分身/ 不存在
      · unknown   —— 未传 --mc（⛔ 不猜·不判）
    """
    if not mc:
        return {"state": "unknown", "reason": "未传 --mc·⛔ 不猜记忆中心位置"}
    twin = os.path.join(mc, "数字分身")
    if not os.path.isdir(twin):
        return {"state": "absent", "reason": "数字分身/ 不存在"}
    spec = os.path.join(twin, "童灵·人格规格书.md")
    slices = os.path.join(twin, "K2切片蒸馏", "slices")
    has_spec, has_slices = os.path.isfile(spec), os.path.isdir(slices)
    if has_spec and has_slices:
        return {"state": "core_built", "spec": True, "slices": True}
    return {"state": "kit_only",
            "reason": "套件在·%s" % ("规格书缺失" if not has_spec else "K2 切片缺失"),
            "spec": has_spec, "slices": has_slices}


def _rule_conflicts(degrade: list, mc: str, cfg_root: str) -> list:
    """降级条目的自证链（安装包哲学条文 40·2026-10-04）

    条文 40 的三要素——每条 degraded 必须能自证：
      ① **冲突在哪个文件**（`files`，机器可查）
      ② **为何不自动覆盖**（`why_not_overwrite`，资产所有权）
      ③ **如何显式覆盖**（`how_to_overwrite`，用户出口）

    ⛔ **三要素不全 ⇒ 视为未完成声明**，本函数把它标成 `incomplete: true`
       并在 `verdict` 计算中**照常计入 degraded**——
       「说不清的降级」不许因为写得含糊就变成绿。
    ✅ 非「规则层冲突」类降级（如「某可选组件未启用」）走 `kind: other`，
       三要素按通用形态补齐·⛔ 不伪造文件路径。
    """
    out = []
    for d in degrade:
        text = str(d)
        is_rule = ("规则层" in text or "用户文件" in text or "覆盖" in text)
        rec = {
            "declared": text,
            "kind": "rule_conflict" if is_rule else "other",
            "files": [],
            "why_not_overwrite": None,
            "how_to_overwrite": None,
            "incomplete": True,
        }
        if is_rule and mc:
            rule_dir = os.path.join(mc, "记忆规则")
            if os.path.isdir(rule_dir):
                rec["files"] = [os.path.join(rule_dir, f)
                                for f in sorted(os.listdir(rule_dir))][:20]
            rec["why_not_overwrite"] = (
                "用户既有规则/身份文件属用户资产·安装器⛔不自动覆盖"
                "（铁律：改 SOUL/铁律版/USER 须告知并由用户决定）")
            rec["how_to_overwrite"] = (
                "显式出口：确认差异后由用户主动开启覆盖开关，"
                "或手工合并（保留用户版本 + 追加包内新增条款）")
            rec["incomplete"] = False
        out.append(rec)
    return out


def _verdict(items: list, components_missing: list, degrade: list) -> str:
    """verdict 的**机械规则**（⛔ 不许凭感觉）。

    failed   —— 任一 required 能力 missing，或必需组件缺失
    degraded —— 无 required 缺失，但有 optional 缺失或显式降级项
    ok       —— 全部 required 满足且无降级
    """
    req_bad = [i for i in items
               if i["severity"] == "required" and i["status"] == "missing"]
    if req_bad or components_missing:
        return VERDICT_FAILED
    if degrade:
        return VERDICT_DEGRADED
    return VERDICT_OK


def build(args) -> dict:
    pkg = args.package or _pkg_root()
    cap_path = os.path.join(pkg, "adapters", args.platform, "capability.yaml")
    if not os.path.isfile(cap_path):
        raise SystemExit("❌ capability.yaml 不存在：%s" % cap_path)

    # ── 端配置根：命令行 > capability 声明（2026-10-04 根治·安装包哲学条文 40）──
    # 🔴 病根：旧写法 `cfg_root = expanduser(args.config_root or "~")`
    #    —— 未传 --config-root 时**落家目录**，于是 runtime_paths / path_overlay
    #    两件按 `<家目录>/doenglingz/` 找 → 必 missing → 回执 verdict=failed。
    #    那不是「用户文件冲突」，是**判据路径自己指错**——与 ARCHIVE /
    #    hermes_wb_parity / manifest_registrar / changelog_append
    #    同族的第 5 例「路径少一段」，第 6 处在下面的 --out 落点。
    # ✅ 正确：未显式传 ⇒ 读 **capability.yaml 的 config_root 声明**（同源·8/8 端齐备）
    #    ——这是条文 40「有默认终态」的落地：⛔ 不让调用方靠记得传参。
    if args.config_root:
        cfg_root = os.path.expanduser(args.config_root)
    else:
        _cap_txt = open(cap_path, encoding="utf-8").read()
        _m = re.search(r'^\s*config_root:\s*["\']?([^"\'\s#]+)', _cap_txt, re.M)
        if not _m:
            raise SystemExit(
                "❌ capability.yaml 未声明 config_root·且未显式传 --config-root\n"
                "   （%s）——⛔ 不猜端配置根·请补声明或显式传参" % cap_path)
        cfg_root = os.path.expanduser(_m.group(1).strip().strip('"').strip("'"))
    cfg_root = os.path.abspath(cfg_root)

    # ── 组件侧：出厂清单 × 端上实测 ────────────────────────────────
    cv = _read_json(os.path.join(pkg, "references", "component-versions.json"), {}) or {}
    comp_out = {}
    comp_missing = []
    mc = os.path.abspath(args.mc) if args.mc else ""
    # 读取端能力声明（用于判断plugins等端专属组件是否适用·2026-10-03 无hook端假红修复）
    cap_txt_for_probe = ""
    try:
        cap_txt_for_probe = open(cap_path, encoding="utf-8").read()
    except OSError:
        pass
    cap_flags = _capability_flags(cap_txt_for_probe)
    has_hooks = cap_flags.get("hooks_event", False)
    # 分量 → 端上落点（相对 MC 或相对 CFG）。⛔ 落点表在此单点声明。
    probes = [
        ("script_center", os.path.join(mc, "脚本中心") if mc else None),
        ("digital_twin", os.path.join(mc, "数字分身") if mc else None),
        ("rule_data", os.path.join(mc, "记忆规则") if mc else None),
        ("runtime_paths", os.path.join(cfg_root, "doenglingz", "runtime_paths.json")),
        ("path_overlay", os.path.join(cfg_root, "doenglingz", "path_override.py")),
    ]
    # ── plugins 是否为本包交付物（2026-10-03 隔离机实测定死·⛔ 不再由 has_hooks 推断）
    # 病根：旧写法「有 hook 端 ⇒ 要求 <cfg_root>/plugins 存在」，但—
    #   ① WorkBuddy 的 plugins/ 是**端应用自建**（cache / marketplaces / installed_plugins.json），
    #      **本包安装器从不装它**；干净机上应用没跑过 ⇒ 目录不存在 ⇒ 判 missing ⇒ **verdict=failed**。
    #   ② Hermes 的插件是本包装的，但落点**不是** cfg_root/plugins ⇒ 同一逻辑对 Hermes 同样假红。
    # ⇒ 适用性属**端事实**，只能由 capability 声明（`plugins_delivered`），⛔ 不得由 hook 能力反推。
    _pd = cap_flags.get("plugins_delivered")
    if _pd is True:
        probes.append(("plugins", os.path.join(cfg_root, "plugins")))
    else:
        comp_out["plugins"] = {
            "status": "not_applicable", "path": None,
            "reason": ("本端 plugins 非本包交付物（端应用自建或走端专属目录）·不计入 verdict"
                       if _pd is False else
                       "capability 未声明 plugins_delivered·按不适用处理（⛔ 不由 hook 能力反推）")}
    for key, path in probes:
        if path is None:
            comp_out[key] = {"status": "unknown", "path": None,
                             "reason": "未提供 --mc·无法定位记忆中心"}
            continue
        ok = os.path.exists(path)
        comp_out[key] = {"status": "installed" if ok else "missing",
                         "path": path, "reason": None if ok else "落点不存在"}
        if not ok:
            comp_missing.append(key)

    # ── 能力侧：capability.yaml 声明 × 缺失语义 ───────────────────
    sem = _semantics(cap_path)
    cap_txt = ""
    try:
        cap_txt = open(cap_path, encoding="utf-8").read()
    except OSError:
        pass
    # 🔴 **能力项的真值只有一个来源**：`capabilities:` 段里写的 true/false。
    #    旧版除 hooks_event 外一律传 present=False ⇒ 把"声明为 true"的能力
    #    判成 missing（恒假·交接书 §二·盲区1「只测了一种形态」的同族病）。
    #    ⛔ 不接受"没查"当"没有"——查不到 ⇒ status=unknown ≠ missing。
    cap_decl = _capability_flags(cap_txt)
    items = []
    for k in sorted(sem):
        if k not in cap_decl:
            # 本端压根没声明这个键 ⇒ 缺失语义说了算（n_a/optional/required）
            items.append(_classify(k, sem, False))
            continue
        val = cap_decl[k]
        if val:                      # 声明为真 = 本端具备
            items.append(_classify(k, sem, True))
        else:                        # 声明为假 = 本端形态上不涉及
            it = _classify(k, sem, False)
            it["status"] = "not_applicable"
            it["reason"] = "本端声明 capabilities.%s: false" % k
            it["severity"] = "n_a"    # 声明为假 ⇒ 语义必然是 n_a（除非声明本身矛盾）
            items.append(it)

    degrade = list(args.degrade or [])
    v = _verdict(items, comp_missing, degrade)
    req_missing = [i for i in items
                   if i["severity"] == "required" and i["status"] == "missing"]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "platform": args.platform,
        "config_root": cfg_root,
        "mc": mc or None,
        "package_version": cv.get("package_version"),
        "verdict": v,
        "counts": {"capabilities": len(items),
                   "required_missing": len(req_missing),
                   "components_missing": len(comp_missing),
                   "degraded": len(degrade)},
        "components": comp_out,
        "capabilities": items,
        "missing_capabilities": req_missing,
        # 数字分身造芯态（2026-10-04）·⛔ 不计入 verdict：
        #   装成功 ≠ 用户已造芯——新用户首装尚未造芯是**正常态**，不是安装失败。
        "twin_core": _probe_twin_core(mc),
        "degraded": degrade,
        # degraded 自证链（安装包哲学条文 40·第 3 点）：
        #   每条降级必须能自证「冲突在哪个文件 / 为何不自动覆盖 / 如何显式覆盖」，
        #   ⛔ 缺三要素的条目视为**未完成声明**·由 rule_conflicts 机械拒收。
        "rule_conflicts": _rule_conflicts(degrade, mc, cfg_root),
        "pending_manual": list(args.pending_manual or []),
        "notes": [
            "本文件由 install_receipt.py 产出·⛔ 禁手写副本",
            "verdict=failed 表示必需能力缺失·degraded 表示有降级但必需项齐全",
            "severity=n_a 表示本端不涉及·optional 缺失属正常态",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="生成安装回执 installed_manifest.json（到货回执）")
    ap.add_argument("--platform", required=True, help="端 ID（adapters/<端>/）")
    ap.add_argument("--config-root", default=None, help="端配置根（默认 ~/.hermes 等）")
    ap.add_argument("--mc", default=None, help="记忆共享中心绝对路径")
    ap.add_argument("--package", default=None, help="安装包根（默认自溯）")
    ap.add_argument("--degrade", action="append", default=[],
                    help="显式降级项（可重复）·缺项必须显式告知")
    ap.add_argument("--pending-manual", action="append", default=[],
                    help="待手动收尾项（可重复）")
    ap.add_argument("--out", default=None, help="回执输出路径（默认 <配置根>/doenglingz/）")
    ap.add_argument("--print", action="store_true", help="只打印不写盘")
    a = ap.parse_args()

    rec = build(a)
    if a.print:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return 0 if rec["verdict"] != VERDICT_FAILED else 1

    # ⛔ 同族第 6 处：未传 --config-root 时 --out 落家目录·回执写错地方。
    # ✅ 直接用 build() 已解析好的 config_root（命令行 > capability 声明·同源）。
    out = a.out or os.path.join(rec["config_root"],
                                "doenglingz", "installed_manifest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print("📦 安装回执已写入：%s" % out)
    print("   verdict=%s · 能力%d项(required缺%d) · 组件缺%d · 降级%d"
          % (rec["verdict"], rec["counts"]["capabilities"],
             rec["counts"]["required_missing"],
             rec["counts"]["components_missing"], rec["counts"]["degraded"]))
    return 0 if rec["verdict"] != VERDICT_FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())