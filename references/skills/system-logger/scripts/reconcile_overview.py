#!/usr/bin/env python3
"""Mechanically derive 今日概览 任务数 from actual `### ` entry counts.
# version: v1.3
# v1.3（2026-09-26·Qoder CN 童灵·D28 两处真缺口施工）：①建组再搬——`- **工具**` 值在本文件无同名 `## 小节` 时补组头再搬条目（旧实现「不搬不建」＝该端条目永久悬在他端节内，实证 09-24「豆包办公」挂在「豆包」节下，两个端并成一本账）；脏值有闸门 `_group_ok`（长度/竖线/前导空格），⛔不拿任意脏值造组。②`--check` 只读模式：派生结果算出来但一个字不写（旧 main 直写盘，"想验证一下"也产生写副作用）；③`--self-test` 8 例含 MUT 变异（把 `_group_ok` 恒假→建组归零，证明 T1 非恒真测试）。本行同时了结 D16 名下"本件无版本标识"。

Eliminates the hand-maintained redundant-counter drift (system-logger 计数不变式).
The 概览 任务数 cell is a *derived copy* of each tool's `### ` entry count; keeping
it as a hand-incremented counter drifts whenever a concurrent writer appends
entries without bumping the counter (实测 30→31 窗口漂移). This script recomputes
it from the truth source (actual `### ` entries) and rewrites only those cells.

Properties: idempotent · preserves all entries · touches only the 今日概览 table
(cell values + orphan rows since v1.1) + `### ` 条目的**组位**（v1.2 起·跨组错位根治）
· entry bodies are never modified（只搬行、不改行）· 行内容逐字保留。

Cross-group misplacement (v1.2·2026-09-10 根治): append 走 O_APPEND 时间序追加
（铁律-014②明文：并发写不可约最优=追加，⛔禁片段+合并+锁），故多组文件里
**非末位组**的新条目必然落到末位组名下。实证：WorkBuddy 条目落入 `## Trae Work`，
概览计数同步错算（29/2 → 应为 30/1）。修法=写路径零改动，归一下放本派生层
（本脚本每次写入后由 append_log_entry.py 自动调用），归属真源=条目自带的
`- **工具**：<规范名>` 字段（由 append_log_entry.py v3.15.1 机械保证写入）。

Honest boundary (审查F7·2026-09-03): the re-read check narrows the concurrent-append
window but does NOT eliminate it — an append landing between the second read and
os.replace is still lost (microsecond-scale). CHANGELOG v3.11.0 "根治" wording is
downgraded accordingly; the thorough fix is file locking (fcntl), pending 你 approval.

Usage: python3 reconcile_overview.py <log_md_path>
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys


HDR_RE = re.compile(r"^## (?!##)(.+?)\s*$")
ENT_RE = re.compile(r"^### ")
FLD_RE = re.compile(r"^\s*-\s*\*\*工具\*\*\s*：\s*(.+?)\s*$")


def _canonical(name):
    """建组只认 ALLOWLIST 规范名（归一键）；normalize_tool 不可达=保守放行+stderr有痕（⛔不静默阻断主流程）。"""
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import normalize_tool as nt
        return nt.norm_key(name) in {nt.norm_key(a) for a in nt.ALLOWLIST}
    except Exception:
        import sys
        print("⚠️ [建组校验降级] normalize_tool 不可达——_canonical 放行", file=sys.stderr)
        return True

def _group_ok(name):
    """建组闸门：只接受「像端名」的值——⛔不拿任意脏值造组（脏值建组=把噪音固化成小节）。"""
    n = (name or '').strip()
    if not n or n != name:
        return False
    if len(n) > 24 or any(c in n for c in '\n#|'):
        return False
    return not n.startswith(('- ', '* ', ' '))


def normalize_groups(lines):
    """把错位的 `### ` 条目搬回其 `- **工具**：<名>` 所属的 `## <名>` 组块（v1.2·跨组错位根治）。

    归属真源 = 条目自带的工具字段（**唯一**）；缺字段、或值不落在现有组集合 → 该条目
    一律不动（⛔不猜、不新建组）。⛔只改行序不改行内容，⛔不增删组头。
    条目块连同其后的行一起搬；空行按「块后补一空行」重新排布（幂等）。
    返回 (新行列表, 搬动条目数)；结构不可识别 → 原样返回（宁可不动，不可改坏）。
    """
    idx0 = next((i for i, ln in enumerate(lines) if HDR_RE.match(ln)), None)
    if idx0 is None:
        return lines, 0

    pre = list(lines[:idx0])
    if pre and pre[-1].strip() != "":
        pre.append("")

    order, leads, blocks = [], {}, []          # blocks: (原组名, 块行列表)
    cur_name = None
    for ln in lines[idx0:]:
        m = HDR_RE.match(ln)
        if m:
            cur_name = m.group(1)
            order.append(cur_name)
            leads.setdefault(cur_name, [])
            continue
        if cur_name is None:
            continue
        if ENT_RE.match(ln):
            blocks.append([cur_name, [ln]])
        elif blocks and blocks[-1][0] == cur_name:
            blocks[-1][1].append(ln)
        else:
            (leads[cur_name].append(ln))

    names = set(order)
    home, moved = {}, 0
    for og, blk in blocks:
        tool = None
        for ln in blk:
            fm = FLD_RE.match(ln)
            if fm:
                tool = fm.group(1)
                break
        if tool and tool not in names and _group_ok(tool) and _canonical(tool):  # v3.16.0 r1-C2：建组前规范名校验（派生层造非规范组头=自家gate exit5常态红）
            # 建组再搬（D28 真缺口①·2026-09-26）：工具字段值是本端唯一归属真源，
            # 但该端在本文件还没有 `## 端名` 小节 → 旧实现「不搬不建」，条目永远悬在他端节下
            # （实证 2026-09-24：`豆包办公` 条目悬在 `## 豆包` 节内＝两个端被并成一本账）。
        # v3.17.0 你终裁（2026-09-30）：D28 原判有效——端台账统一用"豆包办公"，v3.16.0 我
        #   按 v3.12.1 定名做的"误诊"裁决注作废（权威链：你裁定 > 我对既有定名的解释）。
        #   _canonical 校验保留（防脏值造组），AL 已换名后"豆包办公"为合法造组名。
            names.add(tool)
            order.append(tool)
            leads.setdefault(tool, [])
        if tool and tool in names and tool != og:
            home.setdefault(tool, []).append(blk)
            moved += 1
        else:
            home.setdefault(og, []).append(blk)

    if moved == 0:
        return lines, 0

    out = list(pre)
    for name in order:
        out.append("## %s" % name)
        out.extend(leads.get(name, []))
        for blk in home.get(name, []):
            body = list(blk)
            while body and body[-1].strip() == "":
                body.pop()
            out.extend(body)
            out.append("")
    while out and out[-1].strip() == "":
        out.pop()
    return out, moved


def reconcile_text(raw):
    lines = raw.splitlines()

    # 0) 组位归一（v1.2·2026-09-10 跨组错位根治）：先搬位，再计数——这样
    #    sections/概览计数天然按条目的真实归属（`- **工具**` 字段）算。
    lines, moved = normalize_groups(lines)

    # 1) per-section ### counts, keyed by `## <Tool>` header
    sections = {}
    cur = None
    for ln in lines:
        if ln.startswith("## ") and not ln.startswith("### "):
            cur = ln[3:].strip()
            sections[cur] = 0
        elif ln.startswith("### "):
            if cur:
                sections[cur] += 1

    # 2) tools listed in the 今日概览 table
    tools = []
    in_ov = False
    for ln in lines:
        if ln.startswith("## 今日概览"):
            in_ov = True
            continue
        if in_ov:
            if ln.startswith("## "):
                break
            m = re.match(r"^\|\s*([^|\n]+?)\s*\|\s*\d+\s*\|", ln)
            if m:
                tools.append(m.group(1).strip())

    # 2.2) 孤儿行回收（v1.1·2026-08-27）：概览行集是派生物，但本脚本历史上只改数
    #      不删行 → 他端把条目标题/小写别名塞进第一列后永久残留。判定用归一键：
    #      ①归一后既不在 allowlist 也不是真实组头 → 未知垃圾行；
    #      ②归一后与某"真实组头行"同键而自身非组头名 → 别名重复行。
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import normalize_tool as nt
    allow_keys = {nt.norm_key(a) for a in nt.ALLOWLIST}
    junk = []
    for t in tools:
        if t in sections:
            continue
        k = nt.norm_key(t)
        dup_of_canon = any(o in sections and nt.norm_key(o) == k for o in tools if o != t)
        if k not in allow_keys or dup_of_canon:
            junk.append(t)
    junk_set = set(junk)
    tools = [t for t in tools if t not in junk_set]

    # 2.5) tools present as `## <Tool>` sections but missing from the 概览 table —
    #      first-time groups must get a row: the row *set* is derived too,
    #      not just the cell values (hand-created rows + script-maintained
    #      counts = two maintainers = drift point, 2026-08-18 首建组实测)
    missing = [t for t in sections if t not in tools and t != "今日概览"]

    # 3) rewrite 任务数 cells inside 今日概览 only; insert missing tool rows
    #    Insert point = after the last tool row (or the separator row when the
    #    table has no tool rows yet) so the table stays contiguous — a blank
    #    line cannot be used as the tail marker (the header block has one too).
    ov_start = ov_end = sep_idx = last_tool_idx = None
    for i, ln in enumerate(lines):
        if ln.startswith("## 今日概览"):
            ov_start = i
            continue
        if ov_start is not None and ov_end is None:
            if ln.startswith("## "):
                ov_end = i
                break
            if re.match(r"^\|\s*-{3,}", ln):
                sep_idx = i
            for t in tools:
                if re.match(r"^(\|\s*" + re.escape(t) + r"\s*\|\s*)\d+(\s*\|)", ln):
                    last_tool_idx = i
                    break
    if ov_end is None:
        ov_end = len(lines)
    flush_point = last_tool_idx if last_tool_idx is not None else sep_idx

    out = []
    in_ov = False
    flushed = False
    changed = 0
    inserted = 0
    dropped = 0
    junk_pats = [(t, re.compile(r"^\|\s*" + re.escape(t) + r"\s*\|\s*\d+\s*\|")) for t in junk]

    def flush_missing():
        nonlocal inserted, flushed
        if flushed:
            return
        for t in missing:
            out.append(f"| {t} | {sections[t]} |  |")
            inserted += 1
        flushed = True

    for i, ln in enumerate(lines):
        if ln.startswith("## 今日概览"):
            in_ov = True
            out.append(ln)
            continue
        if in_ov and ln.startswith("## "):
            flush_missing()
            in_ov = False
        if in_ov:
            junk_hit = next((t for t, pat in junk_pats if pat.match(ln)), None)
            if junk_hit:
                dropped += 1
                continue
            for t in tools:
                pat = re.compile(r"^(\|\s*" + re.escape(t) + r"\s*\|\s*)\d+(\s*\|)")
                if pat.match(ln):
                    cnt = sections.get(t, 0)
                    new_ln, n = pat.subn(r"\g<1>" + str(cnt) + r"\g<2>", ln)
                    if n:
                        ln = new_ln
                        changed += 1
                    break
        out.append(ln)
        if flush_point is not None and i == flush_point:
            flush_missing()
    if in_ov:  # EOF while still inside the 概览 table
        flush_missing()

    # safety: only the overview table may change row count — +one per missing tool,
    # -one per junk row. Nothing outside it may change.
    assert len(out) == len(lines) + inserted - dropped, "line count changed — abort (no write performed)"

    result = {t: sections.get(t, 0) for t in tools + missing}
    summary = f"reconciled {changed} cell(s); inserted {inserted} row(s); dropped {dropped} junk row(s) {junk or ''}; regrouped {moved} entry(ies); counts={result}"
    return "\n".join(out) + "\n", summary


def reconcile(path):
    """v3.11.0 清零批#7：并发窗口缩窗——乐观锁重读 + tmp 原子替换（审查F7：微秒残窗仍存·彻底解=fcntl·见模块头Honest boundary）。

    旧实现"读→算→open(w) 整文件写回"存在读-写窗口：他端 O_APPEND 追加的新条目
    会被本脚本用旧快照整文件覆盖吞掉（塌缩绊线只对骤降>30%触发，单条丢失不报警）。
    新实现：算完后重读比对，内容未变→写 tmp 后 os.replace 原子替换（同分区原子，
    读侧永远看到完整旧版或完整新版，无半成品态）；内容已变→基于新内容重算（≤3 次，
    不收敛则保守放弃不写——宁可派生延迟，不可吞条目）。
    """
    import tempfile
    for attempt in range(3):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        out, summary = reconcile_text(raw)
        with open(path, encoding="utf-8") as f:
            cur = f.read()
        if cur == raw:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=os.path.dirname(os.path.abspath(path)) or ".", suffix=".tmp")
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                f.write(out)
            os.replace(tmp_path, path)
            print(summary)
            return 0
        print(f"  ⚠️ 并发变更检出（第 {attempt + 1} 次）——基于最新内容重算", file=sys.stderr)
    print("reconcile: 并发变更 3 次未收敛——保守放弃本次派生（未写盘·不吞条目），请重跑", file=sys.stderr)
    return 3


def check_only(path):
    """只读模式（D28 真缺口②）：派生结果算出来但**一个字都不写**，用于 Stop 钩子/巡检安全提问。
    旧实现 main 直接写盘——"想验证一下"也会产生写副作用（同 §3.5「拿替代对象执行写动作」族）。"""
    raw = open(path, encoding="utf-8").read()
    new_text, _summary = reconcile_text(raw)
    if new_text == raw.rstrip() + "\n" or new_text == raw:
        print("RECONCILE:CHECK 一致·will_write=0")
        return 0
    diff = sum(1 for a, b in zip(raw.splitlines(), new_text.splitlines()) if a != b) + abs(
        len(raw.splitlines()) - len(new_text.splitlines()))
    print("RECONCILE:CHECK 需重算·will_write=1·首处差异起 %d 行不同（本模式不写盘）" % diff)
    return 1


def run_selftest():
    """§3.9 出厂动作：判据类产出必带变异自测（置假→检出归零）。"""
    import tempfile
    ok = total = 0
    tmp = tempfile.mkdtemp()
    # v3.17.0 你令统一"豆包办公"后 fixture 基组名随迁；造组正当场景仍用 AL 规范名 Zwork。
    body = ("# 日志\n\n|工具|任务数|\n|---|---|\n| 豆包办公 | 1 |\n\n## 豆包办公\n\n"
            "### 甲事\n\n- **工具**：豆包办公\n\n### 乙事\n\n- **工具**：Zwork\n")
    p = os.path.join(tmp, "x.md")
    open(p, "w", encoding="utf-8").write(body)
    raw = open(p, encoding="utf-8").read()
    out, _ = reconcile_text(raw)
    t1 = ("## Zwork" in out) and ("### 乙事" in out.split("## Zwork")[1])
    t2 = (out.count("### 乙事") == 1)                      # 搬动不复制
    t3 = reconcile_text(out)[0] == out                        # 幂等
    dirty = body.replace("- **工具**：Zwork", "- **工具**：## 脏值|带竖线")
    t4 = "## ## 脏值" not in reconcile_text(dirty)[0]         # 脏值不建组
    t5 = check_only(p) in (0, 1)                           # 只读可跑且返回合法码（v3.16.0 r1-C9：原 `==0 or True` 恒真=自测说谎）
    t6 = open(p, encoding="utf-8").read() == raw        # ★只读模式真没写盘
    t7 = _group_ok(" 前导空格") is False and _group_ok("WorkBuddy") is True
    t9 = _canonical("豆包办公") is True and _canonical("Zwork") is True and _canonical("豆包") is False and _canonical("乱码端X") is False  # v3.17.0 你裁后翻转：新规范名放行·旧名/未知名拒（判别力双向）
    # 变异（§3.9 判据置假）：把 _group_ok 恒假 → 建组必须归零；不归零=T1 是恒真测试
    import importlib.util as _u
    _spec = _u.spec_from_file_location('ro_mut', __file__)
    _m = _u.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
    _m._group_ok = lambda n: False
    r = _m.reconcile_text(raw)[0]
    t8 = "## Zwork" not in r
    for name, g in [("T1 建组再搬（无同名小节→补组头并搬入）", t1), ("T2 搬动不复制", t2),
                    ("T3 幂等（二次运行零变化）", t3), ("T4 脏值不建组", t4),
                    ("T5 只读模式可调用", t5), ("T6 只读模式真零写入", t6), ("T9 建组校验判别力", t9),
                    ("T7 建组闸门单元判据", t7), ("MUT 判据置假→建组归零", t8)]:
        total += 1
        ok += bool(g)
        print("  %s %s" % ("✅" if g else "❌", name))
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("自测 %d/%d %s" % (ok, total, "全绿" if ok == total else "有红"))
    return 0 if ok == total else 1


def main():
    if "--self-test" in sys.argv:
        return run_selftest()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--check" in sys.argv:
        if not args:
            print("usage: reconcile_overview.py --check <log_md>", file=sys.stderr)
            return 2
        return check_only(args[0])
    if len(args) < 1:
        print("usage: reconcile_overview.py [--check|--self-test] <log_md>", file=sys.stderr)
        return 2
    try:
        return reconcile(args[0])
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
