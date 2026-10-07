#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""rules_managed_block_guard.py —— 托管块重复守卫（2026-10-04·`8b1de0f2` 副本病根治）

## 病根（git 溯源·实测）

`commit 8b1de0f2`（2026-10-02 21:30）给 `rules-curation/` 的规则文件**追加**了
`<!-- BULUOTUO:BEGIN/END rules.tielu -->` 托管块，而 `buluotuo_merge` 的
**C5 契约**是「文件已存在且无段 ⇒ **追加**·⛔ 不重写整file」
⇒ 原正文原封不动留在**段外**，托管块内又是完整一份 ⇒ **每条规则出现两次**
（铁律版 405→809 行·摘要版 87→172 行）。
后果：改一份漏一份 ⇒ 铁律内容漂移（当日实测 26 行段级差异）。

## 判据（三条·⛔ 不放宽）

1. **段外不得含托管块内已有的正文行** —— 覆盖率 > 30% 即判红
   （⛔ 30% 而非 90%：段外允许少量真用户内容，但不允许「整份副本」）
2. **BEGIN / END 标记各恰 1 处** —— 出现 2 处即结构损坏
3. **托管块可读且非空** —— 机器维护面失效即判红

## 反向夹具（`--self-test`）

必须证明**「真病灶会红」**而不是「文件里有托管块就红」：
- 副本形态（段外=完整副本）⇒ 🔴 必红
- 归位形态（段外仅空行）⇒ ✅ 必绿
- 单份无托管块形态 ⇒ ✅ 必绿（不是所有规则文件都有托管块）
- BEGIN/END 各 2 处 ⇒ 🔴 必红
- 段外保留少量真用户内容（覆盖率 < 30%）⇒ ✅ 必绿

## 用法

    python3 rules_managed_block_guard.py [--self-test] [目录...]
退出码：0 = 全绿；1 = 有红项（逐条打印）
"""
import os
import re
import sys

MARK = "BULUOTUO:BEGIN"
END = "BULUOTUO:END"
DUP_THRESHOLD = 0.30          # 段外被段内覆盖超过 30% ⇒ 判红
DEFAULT_DIRS = (
    os.path.expanduser("[记忆共享中心]/脚本中心/assets/rules-curation"),
)


def _norm(lines):
    return [l.rstrip() for l in lines if l.strip()]


def _split_fm(lines):
    if lines and lines[0].strip() == "---":
        j = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
        if j is not None:
            return lines[: j + 1], lines[j + 1 :]
    return [], lines


def check(path):
    """返回 (ok, [问题…])"""
    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    nb, ne = raw.count(MARK), raw.count(END)
    problems = []
    if nb == 0 and ne == 0:
        return True, []                      # 单份形态·无托管块 ⇒ 不适用·不算红
    # 判据 2：标记成对且各恰 1 处
    if nb != 1 or ne != 1:
        problems.append("标记不成对或重复：BEGIN=%d END=%d（各须恰为 1）" % (nb, ne))
        return False, problems
    bi = next(i for i, l in enumerate(lines) if MARK in l)
    ei = next(i for i, l in enumerate(lines) if END in l)
    if bi >= ei:
        problems.append("END 出现在 BEGIN 之前·结构损坏")
        return False, problems
    _, outside = _split_fm(lines[:bi])
    inside = lines[bi + 1 : ei]
    # 判据 3：托管块可读非空
    if not _norm(inside):
        problems.append("托管块段内为空·机器维护面失效")
    # 判据 1：段外重复率
    in_set = set(_norm(inside))
    out_n = _norm(outside)
    if out_n:
        covered = sum(1 for l in out_n if l in in_set)
        ratio = covered / len(out_n)
        if ratio > DUP_THRESHOLD:
            problems.append(
                "段外是托管块内容的副本：%d/%d 行重复（%.0f%% > %.0f%%）"
                "⇒ 每条规则出现两次·改一份漏一份"
                % (covered, len(out_n), ratio * 100, DUP_THRESHOLD * 100))
    return (not problems), problems


def _fixture(name, body, expect_red):
    """造临时文件跑判据"""
    import tempfile
    d = tempfile.mkdtemp(prefix="rmbg_")
    p = os.path.join(d, "x.md")
    open(p, "w", encoding="utf-8").write(body)
    ok, probs = check(p)
    got_red = not ok
    good = got_red == expect_red
    print("  %-34s 期望 %-4s 实得 %-4s %s"
          % (name, "红" if expect_red else "绿", "红" if got_red else "绿",
             "✅" if good else "🔴"))
    if not good and probs:
        print("       %s" % probs[0][:80])
    import shutil
    shutil.rmtree(d, ignore_errors=True)
    return good


def self_test():
    print("═══ rules_managed_block_guard · self-test ═══")
    BODY = "## A\n\n内容甲\n\n## B\n\n内容乙\n"
    BLOCK = "<!-- BULUOTUO:BEGIN rules.tielu -->\n\n%s\n<!-- BULUOTUO:END rules.tielu -->\n" % BODY
    cases = [
        # 真病灶：段外 = 完整副本
        ("副本形态（段外=完整副本）", "---\nd: x\n---\n\n" + BODY + "\n" + BLOCK, True),
        # 已归位：段外仅空行
        ("归位形态（段外仅空行）", "---\nd: x\n---\n\n\n\n" + BLOCK, False),
        # 单份·无托管块
        ("单份形态（无托管块）", "---\nd: x\n---\n\n" + BODY, False),
        # 标记重复
        ("BEGIN/END 各 2 处", BLOCK + "\n" + BLOCK, True),
        # 段外少量真用户内容（覆盖率 < 30%）
        ("段外少量真用户内容", "---\nd: x\n---\n\n## 我的私注\n\n一句\n\n" + BLOCK, False),
    ]
    ok = all(_fixture(n, b, e) for n, b, e in cases)
    print("\n%s" % ("PASS · 判据能对真病灶红·不放宽" if ok else "FAIL"))
    return ok


def main():
    if "--self-test" in sys.argv:
        return 0 if self_test() else 1
    dirs = [a for a in sys.argv[1:] if not a.startswith("-")] or list(DEFAULT_DIRS)
    bad = 0
    checked = 0
    for d in dirs:
        if not os.path.isdir(d):
            print("🔴 目录不存在：%s" % d)
            bad += 1
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".md") or ".bak" in f:
                continue
            p = os.path.join(d, f)
            ok, probs = check(p)
            checked += 1
            if ok:
                print("  ✅ %-32s" % f)
            else:
                bad += 1
                print("  🔴 %-32s" % f)
                for pr in probs:
                    print("       · %s" % pr[:96])
    print("\n═══ %d 件 · %d 红 ═══" % (checked, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())