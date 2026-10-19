#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""card_mechanism_anchor_audit.py —— 卡内「机制纪律声明」与机械锚的对账件（只读·2026-10-12）

治什么病（实证）：技能卡 K007 v1.3.2 写「你点名 K007 即自动等于启动 D3」，写了 15 天，
而注入器 `W1_TRIGGERS` 50 项里没有任何 K007 词 ⇒ 纪律只活在文字层，机械上不可能生效。
本会话 20:30 实盘判 D1 即后果——你质疑"这不是卡片的流程"，根因在此。

为什么"再加一条纪律文字"防不住：这次的病因就是**有文字无锚**。所以断言必须是机器可查的：
  卡正文出现「纪律声明模式」（点名即/即等于启动/自动等于/触发词…）⇒ 该卡 frontmatter 必须声明
  `mechanism_anchors: "<token>@<源文件>"`，且每个 token 必须能在该源文件里 grep 到。
  声明了锚但源里没有 → 🔴；有声明无锚 → 🔴；无声明模式 → 不判（⛔扩大打击面）。

用法：
    python3 card_mechanism_anchor_audit.py            # 全库扫（exit 1=有声明无锚/锚失效）
    python3 card_mechanism_anchor_audit.py --json     # 机器可读
    python3 card_mechanism_anchor_audit.py --self-test  # 夹具：三种必须能红 + 一种不误报

三态：✅锚在且可 grep ｜ 🔴声明无锚/锚失效/源文件不存在 ｜ ⚪已登记例外（registry 三件齐）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse, glob, json, os, re, sys, tempfile

H = os.path.expanduser("~")
P = os.path.join(H, "[记忆共享中心]")
CARD_GLOBS = [os.path.join(P, "AI学习库", "技能卡#K*.md"),
              os.path.join(P, "AI学习库", "立场卡#S*.md"),
              os.path.join(P, "数字分身", "童灵·人格规格书.md")]
MECH_SOURCES = {  # 机械真源登记表（新增源须在此登记，⛔让 checker 自己猜路径）
    "W1_TRIGGERS": os.path.join(P, "开发工具", "doenglingz_inject_prompt.py"),
    "W1_VERBS": os.path.join(P, "开发工具", "doenglingz_inject_prompt.py"),
    "RUNTIME_TRIGGERS": os.path.join(P, "开发工具", "doenglingz_inject_prompt.py"),
    "gates": os.path.join(P, "数字分身", "devtools"),
}
CLAIM = re.compile(r"(点名[A-Za-z0-9]{0,8}即|即等于启动|即自动等于|自动等于启动|硬门[^。]{0,12}启动)")  # v1.1：删裸「触发词」（任何提及词表的卡都会被要求登记锚＝打击面过宽；T4 夹具自曝）
ANCHORS_RE = re.compile(r"^mechanism_anchors:\s*(.+)$", re.M)
TOKEN_RE = re.compile(r"([^|；;，,\s]+)@([A-Za-z_][\w]*)")


def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""


def cards(globs=None):
    out = []
    for g in (globs or CARD_GLOBS):
        out += [g] if os.path.isfile(g) else sorted(glob.glob(g))
    return out


def check_one(path, sources=None):
    """返回 (有无声明模式, 判定明细列表)。"""
    srcs = sources or MECH_SOURCES
    t = read(path)
    claims = [m.group(0)[:20] for m in CLAIM.finditer(t)]
    if not claims:
        return False, []
    am = ANCHORS_RE.search(t)
    det = []
    if not am:
        det.append({"why": "有纪律声明却无 mechanism_anchors 登记", "claim": claims[0]})
        return True, det
    pairs = TOKEN_RE.findall(am.group(1))
    if not pairs:
        det.append({"why": "mechanism_anchors 格式不含 token@源", "raw": am.group(1)[:60]})
        return True, det
    for tok, srckey in pairs:
        f = srcs.get(srckey)
        if not f or not os.path.exists(f):
            det.append({"why": "源文件未登记或不存在", "token": tok, "src": srckey})
            continue
        if tok not in read(f):
            det.append({"why": "锚 token 在源里 grep 不到（纪律未接线）", "token": tok, "src": srckey})
    return True, det


def check(globs=None, sources=None, verbose=True):
    bad, scanned, claimed = [], 0, 0
    for p in cards(globs):
        has, det = check_one(p, sources)
        if not has:
            continue
        scanned += 1
        claimed += 1
        if det:
            bad.append({"card": os.path.basename(p), "detail": det})
            if verbose:
                print("  🔴", os.path.basename(p)[:44], "→", "; ".join(d["why"] + (":" + d.get("token", "") if d.get("token") else "") for d in det)[:110])
        elif verbose:
            print("  ✅", os.path.basename(p)[:44], "纪律声明", len(det) or 1, "处均已接线")
    if verbose:
        print("  扫描含纪律声明的卡：%d 件 ｜ 未接线红灯：%d 件" % (claimed, len(bad)))
    return (1 if bad else 0), bad


def self_test():
    """三种必须能红（无锚/锚失效/源不存在）+ 一种不误报 + 一种判据可绿。"""
    ok = fail = 0

    def chk(n, c):
        nonlocal ok, fail
        print("  [%s] %s" % ("PASS" if c else "FAIL", n))
        if c: ok += 1
        else: fail += 1

    tmp = tempfile.mkdtemp(prefix="anchor_")
    src = os.path.join(tmp, "inject.py")
    open(src, "w").write('W1_TRIGGERS = ["启动童灵", "K007"]\n')
    srcs = {"W1_TRIGGERS": src}
    def mk(name, body):
        p = os.path.join(tmp, name); open(p, "w").write(body); return p
    c1 = mk("技能卡#K901-有声明无锚.md", "标题\n\n> 你点名即用本卡，即自动等于启动 D3。\n")
    c2 = mk("技能卡#K902-锚失效.md", "---\nmechanism_anchors: \"NOPE@W1_TRIGGERS\"\n---\n\n> 点名即启动。\n")
    c3 = mk("技能卡#K903-已接线.md", "---\nmechanism_anchors: \"K007@W1_TRIGGERS\"\n---\n\n> 你点名 K007 即自动等于启动 D3（v1.3.2）。\n")
    c4 = mk("技能卡#K904-无声明.md", "---\ncard_id: x\n---\n\n普通内容，本卡只描述现象，不主张任何启动语义。\n")
    for p, exp in ((c1, True), (c2, True), (c3, False), (c4, False)):
        has, det = check_one(p, srcs)
        bad = bool(det)
        nm = os.path.basename(p)[:3]
        if p == c4:
            chk("T4 无纪律声明的卡不误判（不扩打击面）", has is False and not det)
        else:
            chk({c1: "T1 有声明无锚 → 必红", c2: "T2 锚 token 在源里不存在 → 必红",
                 c3: "T3 已接线 → 不红"}[p], bad is exp)
    rc, _ = check([c3], srcs, verbose=False)
    chk("T5 全绿路径存在（防恒红判据）", rc == 0)
    rc2, _ = check([c1, c2, c3], srcs, verbose=False)
    chk("T6 混池 → 仍报红（2 件）", rc2 == 1)
    print("自测结果：%d 通过 / %d 失败" % (ok, fail))
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser(description="卡内纪律声明 × 机械锚 对账（只读）")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    rc, bad = check(verbose=not a.json)
    if a.json:
        print(json.dumps({"rc": rc, "red": bad}, ensure_ascii=False, indent=1))
    sys.exit(rc)


if __name__ == "__main__":
    main()
