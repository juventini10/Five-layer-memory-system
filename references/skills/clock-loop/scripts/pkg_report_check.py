#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# pkg_report_check.py — G 路径(发布包检查)报告封口校验 v1.0.0
# 定位: E/F 路径有 finalize_report.py 17道检查(写此注释时为6道·v3.50.1同步=#48引用滞后); G 路径报告此前零机械校验(v3.38.0 补)
# 校验: ①报告存在+frontmatter ②专项分析段 ③子Agent审查结果段 ④候选处置台账段 ⑤发布判定三态行 ⑥版本一致
# 用法: python3 pkg_report_check.py <报告绝对路径> [--pkg-version <包版本>]
# 退出: 0=全过(可交付) 1=校验失败(拒绝交付)
# ============================================================
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, re, sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("专项分析", "G 路径报告必含专项分析段(表单四栏+专项项→结果映射·v3.37.0)"),
    (("子Agent 独立审查", "子 Agent 审查结果"), "G 路径报告必含子Agent审查段(独立审查强制·v3.38.0)"),
    ("候选处置台账", "G 路径报告必含候选处置台账段(或'本轮无候选'·v3.22.0 同构)"),
    ("发布判定", "G 路径报告必含发布判定三态行(✅可发布/⚠️有条件发布/❌不可发布·v3.35.2)"),
]

TRI_STATE_PATTERNS = [
    re.compile(r"✅\s*可(对外)?发布"),
    re.compile(r"⚠️\s*有条件发布"),
    re.compile(r"❌\s*不可发布"),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python3 pkg_report_check.py <报告路径> [--pkg-version <包版本>]")
        return 2
    report = Path(sys.argv[1])
    pkg_ver = None
    if "--pkg-version" in sys.argv:
        pkg_ver = sys.argv[sys.argv.index("--pkg-version") + 1]

    fails = []
    # ① 报告存在 + frontmatter
    if not report.exists():
        print(f"[FAIL] 报告不存在: {report}")
        return 1
    text = report.read_text(encoding="utf-8")
    if not text.startswith("---"):
        fails.append("frontmatter 缺失(应以 --- 开头)")
    else:
        fm = text.split("---", 2)[1] if text.count("---") >= 2 else ""
        if not re.search(r"^version:\s*.+$", fm, re.M):
            fails.append("frontmatter 缺 version 字段")
        if not re.search(r"^summary:\s*.+$", fm, re.M):
            fails.append("frontmatter 缺 summary 字段")

    # ②③④ 必含段(多候选任一命中即可)
    for name, why in REQUIRED_SECTIONS:
        names = name if isinstance(name, tuple) else (name,)
        if not any(n in text for n in names):
            fails.append(f"缺「{'/'.join(names)}」段——{why}")

    # ⑤ 发布判定三态行
    tri = [p for p in TRI_STATE_PATTERNS if p.search(text)]
    if not tri:
        fails.append("缺发布判定三态行(✅可发布/⚠️有条件发布/❌不可发布)")

    # ⑥ 版本一致(报告 version == 包版本)
    if pkg_ver:
        m = re.search(r"^version:\s*[\"']?([^\"'\n]+)", text, re.M)
        if not m or m.group(1).strip() != pkg_ver:
            fails.append(f"版本不一致: 报告={m.group(1).strip() if m else '?'} 包={pkg_ver}")

    if fails:
        print(f"[FAIL] {len(fails)} 项校验未过:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"[PASS] G 路径报告封口校验全过: {report.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
