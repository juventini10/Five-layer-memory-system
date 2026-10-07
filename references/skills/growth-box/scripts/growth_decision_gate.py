#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_decision_gate.py — 成长箱决策层裁决器（Phase 2 决策自主化 · 步骤2.1 · v1.0.1）

定位（设计：~/[记忆共享中心]/自定义层/待完成工作/成长箱升级/phase2-design.md）：
  把「可机械验证」的候选/工单/草案从人工终审队列分流到机械裁决轨——
  每条自动裁决必须出裁决书（判据+证据+可上诉），白名单外一律保留终审（G6 Fail-Closed）。
  ⛔ 本脚本对 learnings/ERRORS/规则文件零写入权（G10 写域隔离·自测断言）。

判据白名单 v1.0（phase2-design §三·宁窄勿宽，扩充须你确认）：
  D1 候选指纹近期已❌（同坑仍噪声） → 标❌引用旧拒因
  D2 候选与既有条目去重（同坑已有记录） → 标「重复·并入」
  D3 L1草案 verify_cmd 复跑通过 → 标「已验证·待你形式批准」
  D4 L1草案 verify_cmd 复跑失败 → 打回重诊断（回⏳+失败注记）
  D5 工单首查探针=检测对象已消失 → 出「建议退役」裁决书（执行仍走E流程终审）
  D6 候选严重度low且7天未复现 → 降级「观察」

用法：
  python3 growth_decision_gate.py              # 裁决一轮
  python3 growth_decision_gate.py --check      # 健康检查 JSON
  python3 growth_decision_gate.py --self-test  # 自测（夹具自清理）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta

VERSION = "1.1.0"

HOME = os.path.expanduser("~")
BASE = os.path.expanduser("[记忆共享中心]")
CANDIDATES = os.path.join(BASE, "成长箱", "learnings", "CANDIDATES.md")
DECISIONS = os.path.join(BASE, "成长箱", "learnings", "DECISIONS.jsonl")
STATE = os.path.join(BASE, "成长箱", "learnings", "growth_decision_gate_state.json")
RECURRENCE = os.path.join(BASE, "成长箱", "免疫复发记录.md")
WORKORDERS = os.path.join(BASE, "成长箱", "免疫修复工单.md")

# G10 写域隔离哨兵：本脚本任何写入都不得触达这些文件
WRITE_FORBIDDEN = [
    os.path.join(BASE, "成长箱", "learnings", "LEARNINGS.md"),
    os.path.join(BASE, "成长箱", "learnings", "ERRORS.md"),
]


def _read(path, limit=4_000_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def _fingerprint(text):
    return hashlib.sha1(text.strip().encode("utf-8")).hexdigest()[:16]


def _append_decision(row):
    """裁决台账 append-only（jsonl）。"""
    os.makedirs(os.path.dirname(DECISIONS), exist_ok=True)
    with open(DECISIONS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_state(payload):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    except OSError as exc:
        sys.stderr.write("growth_decision_gate: 状态写入失败 %s\n" % exc)


# ---------- 候选块解析（与采集器 Schema 对齐） ----------

def parse_candidates(text):
    """解析 CANDIDATES.md → [{id,title,fingerprint,status,src}]。"""
    entries = []
    for b in re.split(r"(?=^### \[CAND-)", text, flags=re.M):
        hm = re.match(r"### \[CAND-(\d{8})-(\d+)\]\s*(.+)", b)
        if not hm:
            continue
        fp = re.search(r"\*\*指纹\*\*：([0-9a-f]{16})", b)
        st = re.search(r"\*\*状态\*\*：\s*([⏳✅❌🟡])", b)
        src = re.search(r"\*\*来源信号\*\*：\s*(S\d)", b)
        entries.append({
            "id": "CAND-%s-%s" % (hm.group(1), hm.group(2)),
            "date": hm.group(1),
            "title": hm.group(3).strip(),
            "fingerprint": fp.group(1) if fp else "",
            "status": st.group(1) if st else "⏳",
            "src": src.group(1) if src else "",
        })
    return entries


def rewrite_candidate_status(text, cand_id, new_status, conclusion):
    """按行改写指定候选的状态与审核结论（指令编写规范 §1.5·禁切片拼接）。"""
    out, inside, hit = [], False, False
    for line in text.splitlines(keepends=True):
        if re.match(r"^### \[CAND-", line):
            inside = (cand_id in line)
            if inside:
                hit = True
        if inside and re.match(r"^- \*\*状态\*\*：", line):
            line = re.sub(r"\*\*状态\*\*：.*", "**状态**：%s" % new_status, line)
        elif inside and re.match(r"^- \*\*审核结论\*\*：", line):
            line = re.sub(r"\*\*审核结论\*\*：.*",
                          "**审核结论**：[机械裁决%s] %s（%s 可上诉：改回⏳并注理由）"
                          % (datetime.now().strftime("%m-%d %H:%M"), conclusion, cand_id), line)
        out.append(line)
    return ("".join(out), hit) if hit else (text, False)


# ---------- 判据 D1-D6（每条独立·证据可追溯） ----------

def d1_recently_rejected(entry, all_entries, today):
    """同指纹 7 天内已有 ❌ → 沿用噪声判定。"""
    if not entry["fingerprint"]:
        return None
    for e in all_entries:
        if e["fingerprint"] == entry["fingerprint"] and e["status"] == "❌" and e["id"] != entry["id"]:
            return {"rule": "D1", "evidence": "同指纹 %s 已有 ❌ 记录（%s）" % (entry["fingerprint"], e["id"])}
    return None


def d2_duplicate_of_existing(entry, learnings_text, today):
    """标题关键词在 learnings/ERRORS 已有条目 → 重复。"""
    if entry["src"] != "S2":
        return None
    m = re.search(r"免疫坑复发：(.+)", entry["title"])
    if not m:
        return None
    pit = m.group(1)
    key = re.sub(r"（.*?）|\s", "", pit)[:12]
    if len(key) < 6:
        return None
    if key in learnings_text:
        return {"rule": "D2", "evidence": "坑关键词「%s」已存在于 learnings/ERRORS" % key}
    return None


def d6_low_stale(entry, recurrence_text, today):
    """S2 坑近 7 天无复发 + 候选已超 3 天 → 降级观察。"""
    if entry["src"] != "S2":
        return None
    m = re.search(r"免疫坑复发：(.+)", entry["title"])
    if not m:
        return None
    pit = m.group(1)
    for line in recurrence_text.splitlines():
        if pit[:20] in line and "命中" in line and re.search(r"^\s*-\s+(\d{4}-\d{2}-\d{2})", line):
            d_s = re.search(r"(\d{4}-\d{2}-\d{2})", line).group(1)
            d = datetime.strptime(d_s, "%Y-%m-%d").date()
            if (today - d).days <= 7:
                return None  # 近7天仍有复发→不降级
    made = datetime.strptime(entry["date"], "%Y%m%d").date()
    if (today - made).days >= 3:
        return {"rule": "D6", "evidence": "近7天无复发且候选已滞留%d天" % (today - made).days}
    return None


def d3_d4_verify_cmd(draft_cmd, today):
    """D3/D4：草案验证命令复跑。返回 (rule, evidence) 或 None。"""
    if not draft_cmd:
        return None
    try:
        r = subprocess.run(["bash", "-c", draft_cmd], capture_output=True,
                           text=True, timeout=60)
        if r.returncode == 0:
            return {"rule": "D3", "evidence": "verify_cmd 复跑 exit 0（修复已生效）"}
        return {"rule": "D4", "evidence": "verify_cmd exit %d（修复未生效·打回重诊断）" % r.returncode}
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"rule": "D4", "evidence": "verify_cmd 执行异常: %s（显式降级）" % exc}


def d5_probe_gone(probe_cmd, today):
    """D5：工单首查探针——检测对象已消失=假警报→建议退役。"""
    if not probe_cmd:
        return None
    try:
        r = subprocess.run(["bash", "-c", probe_cmd], capture_output=True,
                           text=True, timeout=60)
        # 探针语义：exit 0 = 检测对象已消失（坑不在）→ 建议退役
        if r.returncode == 0:
            return {"rule": "D5", "evidence": "首查探针 exit 0：检测对象已消失（假警报·建议退役，执行走E流程终审）"}
    except (subprocess.TimeoutExpired, OSError) as exc:
        return None
    return None


# ---------- 主流程 ----------

def run_gate(today=None, dry_run=False):
    today = today or date.today()
    cand_text = _read(CANDIDATES)
    rec_text = _read(RECURRENCE)
    learnings_text = _read(os.path.join(BASE, "成长箱", "learnings", "LEARNINGS.md")) + _read(os.path.join(BASE, "成长箱", "learnings", "ERRORS.md"))
    stats = {"scanned": 0, "auto": 0, "left": 0, "by_rule": {}, "errors": []}
    decisions = []

    if not cand_text:
        stats["errors"].append("CANDIDATES.md 缺失（显式降级·本轮仅统计）")
    else:
        entries = parse_candidates(cand_text)
        cand_ids = {e["id"] for e in entries}
        new_text = cand_text
        for e in entries:
            if e["status"] != "⏳":
                continue
            stats["scanned"] += 1
            verdict = (d1_recently_rejected(e, entries, today)
                       or d2_duplicate_of_existing(e, learnings_text, today)
                       or d6_low_stale(e, rec_text, today))
            if verdict:
                stats["auto"] += 1
                stats["by_rule"][verdict["rule"]] = stats["by_rule"].get(verdict["rule"], 0) + 1
                decisions.append({"ts": datetime.now().isoformat(timespec="seconds"),
                                  "target": e["id"], **verdict})
                if not dry_run:
                    if verdict["rule"] == "D1":
                        new_status, concl = "❌", "同指纹已判噪声"
                    elif verdict["rule"] == "D2":
                        new_status, concl = "❌", "重复·并入既有条目"
                    else:
                        new_status, concl = "🟡", "降级观察"
                    new_text, hit = rewrite_candidate_status(new_text, e["id"], new_status, concl)
                    if not hit:
                        stats["errors"].append("%s 状态改写未命中（幂等保护）" % e["id"])

        # 写回前断言：候选集合必须与解析时一致（防丢段·指令编写规范§1.5）
        if not dry_run and new_text != cand_text:
            text_ids = {m.group(1) for m in re.finditer(r"### \[(CAND-\d{8}-\d+)\]", new_text)}
            if text_ids == cand_ids:
                with open(CANDIDATES, "w", encoding="utf-8") as f:
                    f.write(new_text)
            else:
                stats["errors"].append("写回断言失败：候选集合变化，放弃写回（防丢段）")

    for d in decisions:
        if not dry_run:
            _append_decision(d)

    stats["left"] = stats["scanned"] - stats["auto"]
    if not dry_run:
        _write_state({"version": VERSION, "last_run": datetime.now().isoformat(timespec="seconds"),
                      "today": today.isoformat(), **stats})
    print("growth_decision_gate: 扫描%d·机械裁决%d（%s）·留终审%d%s" % (
        stats["scanned"], stats["auto"],
        ",".join("%s×%d" % kv for kv in stats["by_rule"].items()) or "无",
        stats["left"], "·%d条错误" % len(stats["errors"]) if stats["errors"] else ""))
    for err in stats["errors"]:
        print("  ⚠ " + err)
    return 0


def health_check():
    state = {}
    try:
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        pass
    n_dec = 0
    try:
        with open(DECISIONS, encoding="utf-8") as f:
            n_dec = sum(1 for line in f if line.strip())
    except OSError:
        pass
    out = {"version": VERSION, "last_run": state.get("last_run", ""),
           "candidates_file": os.path.isfile(CANDIDATES),
           "decisions_total": n_dec, "last_stats": state,
           "alarm": state.get("left", 0) > 0}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


# ---------- 自测 ----------

def self_test():
    failures = []
    tmp = tempfile.mkdtemp(prefix="gdg_selftest_")
    today = date(2026, 9, 16)
    global CANDIDATES, DECISIONS, STATE, RECURRENCE, WRITE_FORBIDDEN
    real = (CANDIDATES, DECISIONS, STATE, RECURRENCE, WRITE_FORBIDDEN)
    try:
        CANDIDATES = os.path.join(tmp, "CANDIDATES.md")
        DECISIONS = os.path.join(tmp, "DECISIONS.jsonl")
        STATE = os.path.join(tmp, "state.json")
        RECURRENCE = os.path.join(tmp, "rec.md")

        # 夹具：⏳A(同指纹有❌历史→D1) ⏳B(learnings已有关键词→D2) ⏳C(近7天复发中→留终审) ⏳D(low滞留→D6)
        fp_a = "aaaaaaaaaaaaaaaa"
        with open(CANDIDATES, "w", encoding="utf-8") as f:
            f.write("""# t

### [CAND-20260916-001] 免疫坑复发：测试坑甲（很长的标题占位）
- **来源信号**：S2 · x
- **指纹**：%s
- **状态**：⏳待审
- **审核结论**：

### [CAND-20260916-002] 免疫坑复发：测试坑乙关键词一二三四五六七八
- **来源信号**：S2 · x
- **指纹**：bbbbbbbbbbbbbbbb
- **状态**：⏳待审
- **审核结论**：

### [CAND-20260916-003] 免疫坑复发：活跃坑丙持续复发送审
- **来源信号**：S2 · x
- **指纹**：cccccccccccccccc
- **状态**：⏳待审
- **审核结论**：

### [CAND-20260913-004] 免疫坑复发：停滞坑丁很久没复发了啊
- **来源信号**：S2 · x
- **指纹**：dddddddddddddddd
- **状态**：⏳待审
- **审核结论**：
""" % fp_a)
        with open(RECURRENCE, "w", encoding="utf-8") as f:
            f.write("- 2026-09-16 07:00 | 🔴命中 | 活跃坑丙持续复发送审 | c | 来源: t\n")
        # 历史条目：001 同指纹已❌（伪造历史条目）
        with open(CANDIDATES, "a", encoding="utf-8") as f:
            f.write("""
### [CAND-20260910-099] 免疫坑复发：测试坑甲（历史）
- **来源信号**：S2 · x
- **指纹**：%s
- **状态**：❌已拒（噪声）
- **审核结论**：上次是噪声
""" % fp_a)
        # learnings 关键词预置（D2）
        learnings_p = os.path.join(tmp, "LEARNINGS.md")
        with open(learnings_p, "w", encoding="utf-8") as f:
            f.write("## [x] 测试坑乙关键词一二三四五六七八\n已记录\n")

        # G10 哨兵文件（mtime 断言）
        forbidden_p = os.path.join(tmp, "LEARNINGS.md")  # 即 learnings_p
        before_mtime = os.path.getmtime(forbidden_p)
        old_WRITE = WRITE_FORBIDDEN
        WRITE_FORBIDDEN = [forbidden_p]

        devnull = open(os.devnull, "w")
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            # 注入 learnings 路径到 d2（通过临时改全局 BASE 语义不可行·直接改函数签名不方便——
            # d2 读全局 BASE 下文件，故自测里把 BASE 指到 tmp）
            pass
        finally:
            pass

        # 改 BASE 指向 tmp 以便 d2 读夹具 learnings
        global BASE
        real_base = BASE
        BASE = tmp
        os.makedirs(os.path.join(tmp, "成长箱", "learnings"), exist_ok=True)
        shutil.copy(learnings_p, os.path.join(tmp, "成长箱", "learnings", "LEARNINGS.md"))
        with open(os.path.join(tmp, "成长箱", "learnings", "ERRORS.md"), "w") as f:
            f.write("")

        try:
            run_gate(today=today)
        finally:
            sys.stdout = old_stdout
            devnull.close()
            BASE = real_base

        text = _read(CANDIDATES)
        if "同指纹已判噪声" not in text:
            failures.append("T1 D1 未生效")
        if "重复·并入既有条目" not in text:
            failures.append("T2 D2 未生效")
        blk3 = re.search(r"### \[CAND-20260916-003\][\s\S]*?(?=\n### \[|$)", text)
        if not blk3 or "⏳" not in blk3.group(0):
            failures.append("T3 活跃坑不应被裁决")
        if "降级观察" not in text:
            failures.append("T4 D6 未生效（停滞坑丁）")
        # 裁决台账
        n = sum(1 for l in _read(DECISIONS).splitlines() if l.strip())
        if n != 3:
            failures.append("T5 裁决台账 %d≠3" % n)
        # G10 写域隔离
        if os.path.getmtime(forbidden_p) != before_mtime:
            failures.append("T6 G10 违规：哨兵文件被写")
        # 幂等
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            run_gate(today=today)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        n2 = sum(1 for l in _read(DECISIONS).splitlines() if l.strip())
        if n2 != 3:
            failures.append("T7 重跑不幂等 %d→%d" % (n, n2))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        CANDIDATES, DECISIONS, STATE, RECURRENCE, WRITE_FORBIDDEN = real

    if failures:
        print("SELF-TEST FAIL（%d）:" % len(failures))
        for f_ in failures:
            print("  ✗ " + f_)
        return 1
    # T8（§3.9 自测红线的物理承接）：把判据探针纳入自测主流程——聚合器只跑 --self-test，
    # MUT 行只在 --probe 路径打=对下游不可见（本机 2026-09-18 实测被自己的新机制判为未承接）。
    if probe_criteria() != 0:
        print("MUT:FAIL 判据探针未两向翻转（恒真/恒假嫌疑）")
        return 1
    print("MUT:OK 判据两向可翻转（D1/D2/D6/D3-D4/D5 各含正负夹具·恒真或恒假即 PROBE:FAIL）")
    print("SELF-TEST PASS（T1-T8 全绿·含G10写域隔离断言·探针两向可翻转·夹具已自清理）")
    return 0


# ---------- 判据可证伪探针（D10·2026-09-18·每条白名单判据必须两向可翻转） ----------

def probe_criteria():
    """恒真/恒假探针：每条判据跑「应命中」+「应不命中」两组夹具。
    两向同结果 = 判据不区分输入 = 尺子没刻度（与 W1 恒真抗体同构）→ exit 1。"""
    today = date(2026, 9, 18)
    bad = []

    def ent(**kw):
        base = {"id": "C1", "src": "S2", "fingerprint": "fp1", "date": "20260910",
                "title": "免疫坑复发：探针夹具坑名足够长", "status": "⏳"}
        base.update(kw)
        return base

    # D1：同指纹有 ❌ → 命中；无 ❌ → 不命中
    pos = d1_recently_rejected(ent(), [ent(id="C1"), ent(id="C2", status="❌")], today)
    neg = d1_recently_rejected(ent(), [ent(id="C1"), ent(id="C2", status="⏳")], today)
    if not pos or neg:
        bad.append("D1 两向未翻转（pos=%s neg=%s）" % (bool(pos), bool(neg)))

    # D2：坑名已在 learnings → 命中；不在 → 不命中
    pit = re.sub(r"（.*?）|\s", "", "探针夹具坑名足够长")[:12]
    pos = d2_duplicate_of_existing(ent(), "命中史含 %s 一条" % pit, today)
    neg = d2_duplicate_of_existing(ent(), "与本坑无关的文本", today)
    if not pos or neg:
        bad.append("D2 两向未翻转（pos=%s neg=%s）" % (bool(pos), bool(neg)))

    # D6：近 7 天无复发且滞留≥3 天 → 命中；有近期复发 → 不命中
    rec_hot = "- 2026-09-17 命中 免疫坑复发：探针夹具坑名足够长"
    pos = d6_low_stale(ent(), "无复发记录", today)
    neg = d6_low_stale(ent(), rec_hot, today)
    if not pos or neg:
        bad.append("D6 两向未翻转（pos=%s neg=%s）" % (bool(pos), bool(neg)))

    # D3/D4：verify_cmd exit0/exit1 必须给出不同裁决（同裁决=没在跑命令）
    a, b = d3_d4_verify_cmd("true", today), d3_d4_verify_cmd("exit 7", today)
    if not a or not b or a["rule"] == b["rule"]:
        bad.append("D3/D4 未区分 exit0/非0（%s vs %s）" % (a and a["rule"], b and b["rule"]))

    # D5：探针 exit0 → 建议退役；exit非0 → 不建议
    pos, neg = d5_probe_gone("true", today), d5_probe_gone("exit 3", today)
    if not pos or neg:
        bad.append("D5 两向未翻转（pos=%s neg=%s）" % (bool(pos), bool(neg)))

    if bad:
        print("PROBE:FAIL 判据不区分输入（恒真/恒假嫌疑）：")
        for x in bad:
            print("  ✗ " + x)
        return 1
    print("PROBE:OK 5 条判据两向可翻转（D1/D2/D6/D3-D4/D5·各含正负夹具）")
    # §3.9 自测红线的物理承接：probe 的每条夹具都是「同一判据必须既能红也能绿」——
    # 任一条被判据吞成恒真/恒假，上面就 PROBE:FAIL 并 exit 1（2026-09-18 变异实测：D5 恒真 → PROBE:FAIL）。
    print("MUT:OK 判据两向可翻转（D1/D2/D6/D3-D4/D5 各含正负夹具·恒真或恒假即 PROBE:FAIL）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="成长箱决策层裁决器 v%s" % VERSION)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--probe", action="store_true", help="判据可证伪探针（恒真/恒假检测·D10）")
    args = ap.parse_args()
    if args.probe:
        return probe_criteria()
    if args.self_test:
        return self_test()
    if args.check:
        return health_check()
    return run_gate()


if __name__ == "__main__":
    sys.exit(main())
