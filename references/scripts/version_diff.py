#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""version_diff.py —— 包版本驱动差量自查（B形态·2026-10-13 皮叔令「那就动手」施工）

> 临时验证版（落脚本中心·不受发布门卫管辖）。逻辑验证通过后，按发布流程进包
> （references/scripts/·届时经 mirror-sync Skill 正门·⛔不 touch 撒谎留痕）。

## 治什么（承 K007 结论·B形态=最符合愿景①③的最优解）

「新通用件入包 → 老端装过也查不出缺」——事件腿(tsl_echo_hook/skill_onduty_promote)
在包内 devtools 但零对账 capability 键，老端装了旧包升级后 verify 查不出缺新件。

## B形态=包版本驱动 diff（不动 11 端 capability·不改 component-versions.json）

两版本基线都现成（K007 读码已证实）：
  · 旧版本(端侧快照)：<MC>/.install/versions.json（装机时 install_scripts 落的 cv 快照）
  · 新版本(包当前)：  <包>/references/component-versions.json

⇒ diff = 纯读两个同构 JSON 做结构对比·⛔ 零改文件·⛔ 不动 11 端 capability。

## 判据纪律

1. 值只由两 JSON 实测对比产出·⛔ 不接受"我觉得落后了"当依据
2. 版本一致 ⇒ 报"已最新"·⛔ 不造"可能缺"的噪音
3. 报差只到「结构键级」·不精确到单文件名（cv 记数量非清单·精确到名需改包·不在 B 最小范围）
4. diff 是提示非阻断：rc=0 恒真退出（提示层·⛔ 不因落后就判 verify failed）
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# V9 守卫（2026-10-13 Win 真机 CI run 38362089334 逮出：本件 print emoji 在
#   cp1252 控制台必崩·承 fill_syntax_scan.py 先例形态·reconfigure 不可用则降级不阻断）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def diff_versions(user_snap: dict, pkg_cv: dict) -> dict:
    """两同构 JSON → 结构差。值只由实测对比产出。"""
    out = {
        "user_package_version": user_snap.get("package_version"),
        "pkg_package_version": pkg_cv.get("package_version"),
        "up_to_date": user_snap.get("package_version") == pkg_cv.get("package_version"),
        "component_deltas": [],
        "skill_deltas": [],
        "platform_support_added": [],
        "platform_status_changed": [],
    }
    uc = (user_snap.get("components") or {})
    pc = (pkg_cv.get("components") or {})
    udf = ((uc.get("digital_twin") or {}).get("files") or {})
    pdf = ((pc.get("digital_twin") or {}).get("files") or {})
    for k in sorted(set(udf) | set(pdf)):
        uv, pv = udf.get(k), pdf.get(k)
        if uv != pv:
            out["component_deltas"].append({
                "component": "digital_twin.files.%s" % k,
                "user": uv, "pkg": pv,
                "delta": (pv - uv) if isinstance(uv, int) and isinstance(pv, int) else "?",
            })
    uss = (uc.get("script_system") or {}).get("files")
    pss = (pc.get("script_system") or {}).get("files")
    if uss != pss:
        out["component_deltas"].append({
            "component": "script_system.files", "user": uss, "pkg": pss,
            "delta": (pss - uss) if isinstance(uss, int) and isinstance(pss, int) else "?",
        })
    usk = (uc.get("skills") or {})
    psk = (pc.get("skills") or {})
    for k in sorted(set(usk) | set(psk)):
        if usk.get(k) != psk.get(k):
            out["skill_deltas"].append({"skill": k, "user": usk.get(k), "pkg": psk.get(k)})
    ups = (user_snap.get("platform_support") or {})
    pps = (pkg_cv.get("platform_support") or {})
    for k in sorted(set(pps) - set(ups)):
        out["platform_support_added"].append(k)
    upn = (user_snap.get("platform_support_notes") or {}).get("ends") or {}
    ppn = (pkg_cv.get("platform_support_notes") or {}).get("ends") or {}
    for k in sorted(set(upn) & set(ppn)):
        us, ps = (upn[k] or {}).get("status"), (ppn[k] or {}).get("status")
        if us != ps:
            out["platform_status_changed"].append({"platform": k, "user": us, "pkg": ps})
    return out


def format_report(d: dict) -> str:
    if d["up_to_date"]:
        return "✅ 版本已最新（%s）·无差量" % d["pkg_package_version"]
    lines = ["⬆️ 包版本驱动 diff（B形态自查）",
             "   端侧快照版本：%s → 包当前版本：%s（落后·建议升级）" % (
                 d["user_package_version"], d["pkg_package_version"])]
    if d["component_deltas"]:
        lines.append("   组件数量差：")
        for c in d["component_deltas"]:
            lines.append("     · %s：%s → %s（%+s）" % (
                c["component"], c["user"], c["pkg"], c["delta"]))
    if d["skill_deltas"]:
        lines.append("   Skill 版本差（%d 个）：" % len(d["skill_deltas"]))
        for s in d["skill_deltas"]:
            lines.append("     · %s：%s → %s" % (s["skill"], s["user"], s["pkg"]))
    if d["platform_support_added"]:
        lines.append("   新增支持端：%s" % ", ".join(d["platform_support_added"]))
    if d["platform_status_changed"]:
        lines.append("   端状态变化：")
        for p in d["platform_status_changed"]:
            lines.append("     · %s：%s → %s" % (p["platform"], p["user"], p["pkg"]))
    lines.append("   ⚠️ 落后≠装失败（提示层）·补装/升级动作须由端执行（B 解决'报缺'不解决'自动补装'）")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="包版本驱动 diff 自查（B形态）")
    ap.add_argument("--mc", required=True, help="记忆中心绝对路径（读 .install/versions.json）")
    ap.add_argument("--package", default=None,
                    help="包根（component-versions.json 所在·默认自溯=本脚本上溯三级到包根）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非人读报告")
    a = ap.parse_args()
    pkg = a.package
    if not pkg:
        # 自溯：本脚本若在包内 references/scripts/version_diff.py → 上溯三级=包根
        pkg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # 自溯校验：溯到的根下必须有 references/component-versions.json·否则自溯失败
        if not os.path.isfile(os.path.join(pkg, "references", "component-versions.json")):
            # 不在包内（如在脚本中心独立跑）⇒ 自溯不成立·报清晰错⛔不拿None糊弄
            print("❌ --package 未指定且自溯失败（本脚本不在包内 references/scripts/）")
            print("   自溯到的路径不含 component-versions.json：%s" % pkg)
            print("   显式指定：--package <布洛陀-全平台安装包绝对路径>")
            return 2
    user_snap = _read_json(os.path.join(a.mc, ".install", "versions.json"))
    pkg_cv = _read_json(os.path.join(pkg, "references", "component-versions.json"))
    if not pkg_cv:
        print("❌ 包 component-versions.json 读不到：%s" % pkg)
        return 2
    if not user_snap:
        print("⚠️ 用户侧 .install/versions.json 不存在（可能从未装机·或路径非标准）")
        print("   路径：%s" % os.path.join(a.mc, ".install", "versions.json"))
        print("   ⚠️ 无快照无法 diff·不编造版本·报'未装机/无快照'")
        return 3
    d = diff_versions(user_snap, pkg_cv)
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(format_report(d))
    return 0  # 提示层·恒 rc=0（落后≠失败）


def run_diff(mc: str, package: str = None) -> str:
    """可 import 入口：给定 mc(和可选包根) → 返回人读 diff 报告字符串。

    ⛔ 不依赖 subprocess（供 install_scripts.py verify 直接 import 调用·
    避免安装器未 import subprocess 的依赖坑·2026-10-13 实测）。
    mc 不存在快照 ⇒ 返回提示串（不抛·不编造）。
    """
    pkg = package
    if not pkg:
        pkg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.isfile(os.path.join(pkg, "references", "component-versions.json")):
            return "❌ 自溯失败·version_diff 不在包内·请显式传 package"
    user_snap = _read_json(os.path.join(mc, ".install", "versions.json"))
    pkg_cv = _read_json(os.path.join(pkg, "references", "component-versions.json"))
    if not pkg_cv:
        return "❌ 包 component-versions.json 读不到：%s" % pkg
    if not user_snap:
        return ("⚠️ 用户侧 .install/versions.json 不存在（未装机或无快照）·不 diff·不编造版本\n"
                "   路径：%s" % os.path.join(mc, ".install", "versions.json"))
    return format_report(diff_versions(user_snap, pkg_cv))


if __name__ == "__main__":
    raise SystemExit(main())
