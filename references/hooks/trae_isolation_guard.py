#!/usr/bin/env python3
# REG: family=守卫 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""trae_isolation_guard.py v1.0 — Trae 系双端「共享文件端中性」巡检守卫（端中性·双端通用）

为什么是「内容层端中性」而不是「分目录隔离」（2026-09-30 机制纠正）：
  Trae Work（TRAE SOLO CN）与 TraeCode（Trae CN）的 product.json 中 dataFolderName 同为 `.trae-cn`
  ⇒ 全局规则目录 / hooks.json 物理共用，**目录级隔离根本不存在**。
  隔离只能在**内容层**做：共享文件一律端中性，端身份由运行期自证（ICUBE_APP_ROOT）+ IDENTITY.md 判定表决定。
  本守卫即内容层的机械兜底——扫共享面，抓「单端写死」。

替代关系：本守卫替代 2026-09-19 Qoder CN 提交的 traecode_isolation_guard.py。
  其前提（SELF_DIR=~/.trae-cn 视作 TraeCode 独占 / PEER_DIR=~/.trae 视作「他端目录」）已被证伪，
  实跑把共享工作区文件误标为「他端目录混入本端口径」，且把「讲这个坑」的叙述当成自指断言。

被检面（SHARED_TARGETS）：
  1. ~/.trae-cn/user_rules/*.md   —— 全局共享规则（Trae 系双端每回合注入）
  2. ~/.trae/rules/*.md           —— 工作区级共享规则（工作区＝家目录时双端同读）
  3. ~/.trae-cn/hooks.json        —— 共享钩子配置
  ⛔ 不计入：~/CLAUDE.md（importClaudeMd 仅 Trae Work 开启 ⇒ 非共享面）；
             端专属目录（Trae记忆/ · Trae Work记忆/ · 端设计哲学包）；备份 / 归档 / 隐藏文件。

判据：
  R1 🔴 单端自称——共享文件出现**自指断言**（Name: / 本端= / 本宿主= / 生效范围 / 装载头 / 署名行）。
        · 豁免 IDENTITY.md（双端判定表·设计使然，两端署名列必须并存）
        · **引号包裹＝提及，不算断言**——防把"描述这个坑"的叙述误判成"踩这个坑"
  R2 🔴 共脚本端参数写死——hooks.json 出现 `--src traework|traecode`（应 `auto` 运行期自识别）
  R3 🟡 共享 hooks.json 中的端专属脚本——因 Trae Work 钩子被产品门禁关闭（iCubeApp.hooks=null），
       hooks.json 实际只有 TraeCode 执行 ⇒ 属「TraeCode 执行面」非缺陷，仅提示。

时序协议：只读巡检，无共写方；命中仅 stdout + 退出码，⛔不落盘不修改（对被检对象零副作用）。
负例证据：--selftest 走**内存夹具**（旧口径应抓红 / 引号提及不应误伤），⛔不建临时文件、不碰真机文件。

用法: python3 trae_isolation_guard.py [--check] [--selftest] [--quiet]
退出码: 0 = 全绿 / 1 = 有 🔴 命中 / 2 = 参数错误
"""
try:
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
USER_RULES_DIR = os.path.join(HOME, ".trae-cn", "user_rules")
WORKSPACE_RULES_DIR = os.path.join(HOME, ".trae", "rules")
SHARED_HOOKS_JSON = os.path.join(HOME, ".trae-cn", "hooks.json")

# 双端判定表：两端署名列必须并存，属设计使然 ⇒ 豁免 R1
EXEMPT_FILES = {"IDENTITY.md"}

# 引号族：命中被引号包裹 ⇒ 判为「提及」而非「断言」
QUOTE_CHARS = set('"\'「」“”‘’《》`')

# R1 单端自称（每条 = 一个自指断言模式；捕获组 1 须为端名）
SELF_ASSERT_PATTERNS = [
    (r"^\s*\*\*Name:\*\*\s*(Trae\s*(?:Work|Code))\b", "身份自称头 Name:"),
    (r"本端\s*(?:即|是|为|＝|=|:|：)\s*(Trae\s*(?:Work|Code))", "本端自称"),
    (r"本宿主\s*(?:即|是|为|＝|=|:|：)\s*(Trae\s*(?:Work|Code))", "本宿主自称"),
    (r"生效范围[：:][^\n]{0,40}?(Trae\s*(?:Work|Code))\s*(?:端|新任务|桌面端|IDE)", "生效范围声明"),
    (r"(Trae\s*(?:Work|Code))\s*端装载", "装载头自称"),
    (r"^\s*——\s*你的\s*(Trae\s*(?:Work|Code))", "署名行"),
]

# R2 共脚本端参数写死
SRC_HARDCODE_PATTERNS = [
    (r"--src\s+(traework|traecode)\b", "端参数写死（应 --src auto）"),
]

# R3 端专属脚本（共享 hooks.json 内）
END_SCRIPT_PATTERN = re.compile(r"\b(traework|traecode|wbai|qodercn|zcode|dsh)_[a-z0-9_]+\.py\b")


def _is_quoted(line, start, end):
    """命中片段是否被引号包裹 ⇒ 提及（非断言）。"""
    before = line[start - 1] if start > 0 else ""
    after = line[end] if end < len(line) else ""
    return before in QUOTE_CHARS or after in QUOTE_CHARS


def scan_text(text, filename):
    """扫一段文本，返回 [(行号, 端名, 判据说明, 行文本), ...]。零副作用。"""
    hits = []
    if os.path.basename(filename) in EXEMPT_FILES:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for pat, label in SELF_ASSERT_PATTERNS:
            for m in re.finditer(pat, line):
                if _is_quoted(line, m.start(), m.end()):
                    continue  # 引号包裹＝提及
                hits.append((lineno, m.group(1), "R1 单端自称·%s" % label, line.strip()[:90]))
        for pat, label in SRC_HARDCODE_PATTERNS:
            for m in re.finditer(pat, line):
                if _is_quoted(line, m.start(), m.end()):
                    continue
                hits.append((lineno, m.group(1), "R2 %s" % label, line.strip()[:90]))
    return hits


def scan_shared_md():
    """扫共享 .md 面，返回 (red_hits, scanned_files)。"""
    red, files = [], []
    for d in (USER_RULES_DIR, WORKSPACE_RULES_DIR):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.startswith(".") or not fn.endswith(".md"):
                continue
            p = os.path.join(d, fn)
            if not os.path.isfile(p) or os.path.islink(p):
                continue  # 软链＝指向中心本体，本体另计；此处不重复扫
            files.append(p)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            for lineno, endname, label, excerpt in scan_text(text, fn):
                red.append((p, lineno, endname, label, excerpt))
    return red, files


def scan_shared_hooks():
    """扫共享 hooks.json，返回 (red_hits, yellow_notes, exists)。"""
    red, yellow = [], []
    if not os.path.isfile(SHARED_HOOKS_JSON):
        return red, yellow, False
    try:
        with open(SHARED_HOOKS_JSON, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return red, yellow, False
    for lineno, line in enumerate(text.splitlines(), 1):
        for pat, label in SRC_HARDCODE_PATTERNS:
            for m in re.finditer(pat, line):
                if _is_quoted(line, m.start(), m.end()):
                    continue
                red.append((SHARED_HOOKS_JSON, lineno, m.group(1), "R2 %s" % label, line.strip()[:90]))
        for m in END_SCRIPT_PATTERN.finditer(line):
            yellow.append((SHARED_HOOKS_JSON, lineno, m.group(1),
                           "R3 共享 hooks.json 内端专属脚本（Trae Work 钩子被门禁关闭⇒实际只有该端执行）",
                           line.strip()[:90]))
    return red, yellow, True


def run_check(quiet=False):
    red, files = scan_shared_md()
    h_red, h_yellow, hooks_exists = scan_shared_hooks()
    red += h_red

    for p, lineno, endname, label, excerpt in red:
        if quiet:
            print("🔴 %s:%d [%s]" % (os.path.relpath(p, HOME), lineno, endname))
        else:
            print("🔴 [共享文件单端写死] %s:%d → %s\n     %s" % (os.path.relpath(p, HOME), lineno, label, excerpt))
    for p, lineno, endname, label, excerpt in h_yellow:
        if quiet:
            print("🟡 %s:%d [%s]" % (os.path.relpath(p, HOME), lineno, endname))
        else:
            print("🟡 %s:%d → %s\n     %s" % (os.path.relpath(p, HOME), lineno, label, excerpt))

    if not quiet:
        print("\n被检面：共享 .md %d 件（%s）＋ hooks.json %s" % (
            len(files), " · ".join(os.path.relpath(f, HOME) for f in files) or "—",
            "在位" if hooks_exists else "缺失"))
    if red:
        if not quiet:
            print("\n⛔ 巡检不通过：共享面单端写死 %d 处（须改为端中性，端专属内容指针化到 IDENTITY.md 判定表）。" % len(red))
        return 1
    if not quiet:
        print("\n✅ 巡检通过：共享面无单端写死（提示 %d 条）。" % len(h_yellow))
    return 0


def selftest():
    """内存夹具双向自测：旧口径应抓红 / 引号提及不应误伤。⛔零文件副作用。"""
    cases = [
        ("旧口径·Name 自称", '**Name:** TraeCode\n', 1),
        ("旧口径·生效范围", "生效范围：Trae Work 新任务\n", 1),
        ("旧口径·装载头", "本文件为 Trae Work 端装载头\n", 1),
        ("旧口径·署名行", "—— 你的 Trae Work 🤖\n", 1),
        ("旧口径·本端自称", "本端＝TraeCode\n", 1),
        ("旧口径·本宿主", "本宿主是 Trae Work\n", 1),
        ("正例·引号提及不应误伤", '`doenglingz-core.md` 头写"TraeCode 端装载"（这是要防的坑）\n', 0),
        ("正例·判定表映射不应误伤", "含 `TRAE SOLO` → **Trae Work**；含 `Trae CN` → **TraeCode**\n", 0),
        ("正例·端中性表述不应误伤", "本端身份由 IDENTITY.md 判定表 + 运行期自证决定\n", 0),
        ("正例·数据点不应误伤", "| Trae Work 数据目录 | `.trae-cn` | product.json 实证 |\n", 0),
    ]
    bad = 0
    for name, text, want in cases:
        got = len(scan_text(text, "fixture.md"))
        ok = got == want
        bad += 0 if ok else 1
        print("%s %s（期望 %d 命中·实得 %d）" % ("✅" if ok else "❌", name, want, got))
    # 豁免验证
    ex = len(scan_text("**Name:** TraeCode\n", "IDENTITY.md"))
    ok = ex == 0
    bad += 0 if ok else 1
    print("%s 豁免·IDENTITY.md 判定表不误伤（期望 0 命中·实得 %d）" % ("✅" if ok else "❌", ex))
    print("\n%s 自测 %d/%d 通过（内存夹具·零文件副作用）" % (
        "✅" if bad == 0 else "❌", len(cases) + 1 - bad, len(cases) + 1))
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="Trae 系双端共享文件端中性巡检（端中性·双端通用）")
    ap.add_argument("--check", action="store_true", help="执行巡检（默认行为）")
    ap.add_argument("--selftest", action="store_true", help="内存夹具双向自测")
    ap.add_argument("--quiet", action="store_true", help="仅输出命中摘要")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run_check(quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())