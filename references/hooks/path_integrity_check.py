#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""path_integrity_check.py — 装机产物路径完整性检查器 v2（2026-10-10 十一轮·双拼病门禁）

用法：
    python3 path_integrity_check.py --root <记忆共享中心或包根> [--pkg-template] [--quiet]

检查项（命中任一 = exit 1）：
  1) 双拼形态（运行时调用形）：expanduser( 或引号内紧跟的 波浪号+双斜杠绝对路径
     / 波浪号+盘符冒号 形态——病形本体（expanduser 静默失效·Fail-Silent）。
     prose 注释/文档描述病形不算（行级判据 + 显式豁免标记，防自伤假阳性）。
  2) 占位符残留：装机面仍含未替换的占位符 token（安装器漏替换）
  3) 畸形前缀：波浪号斜杠紧贴占位符（包模板层病灶·--pkg-template 主判此项）

⛔ 判据构造纪律（本文件源码会被安装器 _fill / mirror relocate/deident 改写）：
  - 占位符 token 用 chr() 动态构造 ⇒ _fill 替换不到本判据（防"检查器自己被治成假绿"）
  - 先例同构：pkg_cleanliness_check.py TILDE_PAT
"""
import argparse
import os
import re
import sys

PLACEHOLDER = chr(0x5B) + "记忆共享中心" + chr(0x5D)      # 左方括号 + 词 + 右方括号
TILDE_PREFIXED = chr(0x7E) + chr(0x2F) + PLACEHOLDER      # 波浪号斜杠 + 占位符
Q = "[" + chr(39) + chr(34) + "]+"               # 单双引号字符类（chr 构造避转义）
BAD_CALL = re.compile(
    "expanduser\\(" + Q + "\\s*" + chr(0x7E) + "(/[A-Za-z]:[/\\\\]|//)"
    "|" + Q + chr(0x7E) + "[A-Za-z]:[/\\\\]"
)
EXEMPT = "PATH-INTEGRITY-EXEMPT"                          # 行级显式豁免标记
TEXT_EXT = {".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".txt", ".html"}
SKIP_DIRS = {".git", "__pycache__", ".package-lock", "记忆琥珀", "logs", "_archive",
             ".snapshots", ".guard", ".patrol"}


def scan(root, only_dirs=None, ph_files=None):
    hits = {"double": [], "placeholder": [], "tilde_prefixed": []}
    for dp, dn, fn in os.walk(root):
        _rel = os.path.relpath(dp, root)
        parts = set(dp.replace("\\", "/").split("/"))
        if parts & SKIP_DIRS:
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            continue
        if only_dirs and not any(_rel == d or _rel.startswith(d + os.sep) for d in only_dirs):
            # 声明域=「只扫这些 root 子目录」（2026-10-12 域修正·条文19 实现=声明）：
            # root 直挂文件=白名单外跳过 fn，但 ⛔不可剪 dn（首版把 root 剪死=维护假绿，负例T17当场抓获）
            if _rel == ".":
                fn[:] = []
            else:
                dn[:] = []
                continue
        for f in fn:
            if os.path.splitext(f)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            rel = os.path.relpath(p, root)
            _exe = os.path.splitext(f)[1].lower() in {".py", ".sh", ".ps1"}
            for ln in t.splitlines():
                if EXEMPT in ln:
                    continue
                if BAD_CALL.search(ln) and _exe:  # double=运行时调用形⇒⛔不判 .md/.json 等 prose（2026-10-12 域修正·历史台账引用不可改亦不该判）
                    hits["double"].append(rel)
                    break
            if (ph_files is None or rel in ph_files) and PLACEHOLDER in t:
                hits["placeholder"].append(rel)
            if TILDE_PREFIXED in t and (ph_files is None or rel in ph_files):
                # 2026-10-12 域修正·条文19 实现=声明：tilde 类与占位符类同受 --placeholder-files
                # 管辖（R4 扫描域收窄声明=双参数成对；原实现漏这一腿⇒作者机 MC 病案登记 prose 全爆红，
                # 装机态白名单件照判不损失）；行级 PATH-INTEGRITY-EXEMPT 同步生效
                for _ln in t.splitlines():
                    if TILDE_PREFIXED in _ln and EXEMPT not in _ln:
                        hits["tilde_prefixed"].append(rel)
                        break
    return hits


def main():
    ap = argparse.ArgumentParser(description="装机产物路径完整性（双拼病门禁·只读）")
    ap.add_argument("--root", required=True, help="记忆共享中心或包根")
    ap.add_argument("--quiet", action="store_true", help="只输出总判定")
    ap.add_argument("--pkg-template", action="store_true",
                    help="包模板层模式：只判畸形前缀（占位符未替换=出厂原态、prose 病形示例不算）")
    ap.add_argument("--only-dirs", default=None,
                    help="只扫这些 root 子目录（逗号分隔·空=全树）——装机产物面白名单")
    ap.add_argument("--placeholder-files", default=None,
                    help="占位符残留只查这些文件（相对 root 或绝对路径·逗号分隔；空=全树）——直拷类设计含占位符不误报")
    args = ap.parse_args()
    root = os.path.expanduser(args.root)
    if not os.path.isdir(root):
        print("[FAIL] 根目录不存在: %s" % root, file=sys.stderr)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    hits = scan(root,
                only_dirs=[d for d in args.only_dirs.split(",") if d] if args.only_dirs else None,
                ph_files=set(args.placeholder_files.split(",")) if args.placeholder_files else None)
    if args.pkg_template:
        hits["placeholder"] = []
        hits["double"] = []
    total = sum(len(v) for v in hits.values())
    if total and not args.quiet:
        for k, label in (("double", "双拼形态产物(运行时调用形)"),
                         ("placeholder", "占位符残留(未替换)"),
                         ("tilde_prefixed", "畸形前缀(波浪号紧贴占位符)")):
            if hits[k]:
                print("  [FAIL] %s: %d 件" % (label, len(hits[k])))
                for r in hits[k][:8]:
                    print("         - %s" % r)
                if len(hits[k]) > 8:
                    print("         ... 另有 %d 件" % (len(hits[k]) - 8))
    if total == 0:
        print("  [PASS] 路径完整性: 无双拼/无占位符残留/无畸形前缀")
        return 0
    print("  [FAIL] 路径完整性: 共 %d 件命中" % total)
    return 1


if __name__ == "__main__":
    sys.exit(main())
