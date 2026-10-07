#!/usr/bin/env python3
# version: v0.1
"""growth_box_pending_audit.py —— 成长箱 pending 状态漂移体检（G3 派生一致性的成长箱分支）

🔴 立脚本原因（2026-08-29 童灵代行·流程B 晋升检查实证）：
  成长箱模式目录表同一行里——「累计次数」由 stats.py 重算（派生数据），
  「状态」列由**手工维护**，两者之间**没有任何一致性校验**。
  实证：PAT-031 状态标 pending(4/3)，但源文件独立记录引用 = 0 → 幽灵计数。
  → 拿漂移的数字做**不可逆的晋升**（写规则文件），错晋升比不晋升危害大得多。

🔴 真值口径（唯一来源·⛔不自己 grep）：
  累计次数 = stats.py 输出（口径：learnings/ 下 `*_errors.md`/`LEARNINGS.md`/
  `ERRORS.md`/`skill_errors.md` 中，含该 PAT 的 `## ` 独立记录块数，记录内去重）。
  ⛔DO NOT 用"文件数"替代——2026-08-29 实测：grep 文件数得 2、stats 记录数得 3，
  口径不同会导致误判（本脚本第一版即踩此坑）。

判据（三态）：
  🔴 幽灵   = 状态 pending(N/3) 且 N≥3，但真实引用 = 0 → 晋升判据虚标，阻断晋升
  🟡 倒挂   = 真实引用 > 状态 N → 有实例未回写状态列（PAT-023 病：改后同步遗漏）
  ⚪ 零引用已晋升 = 状态已晋升但真实引用 0 → **不计问题**（2026-08-29 实证：
     INDEX 的 PAT 是从 QD/LRN 记录**提炼**的模式，源记录用 QD 编号、不回写 PAT 号，
     故扫不到 ≠ 无效。实测 9 条此类条目，逐条核对 archived_* 与活跃文件均为 0，
     但 INDEX 详情段「关联错误」字段非空（如 PAT-038 关联 QD-006 等）→ 判据误报）

契约：--check(JSON,含 alarm) / --report(markdown) / --selfcheck
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
import subprocess
from datetime import datetime

LEARNINGS = os.path.expanduser("[记忆共享中心]/成长箱/learnings")
INDEX = os.path.join(LEARNINGS, "INDEX.md")
STATS = os.path.expanduser("[记忆共享中心]/技能配置/growth-box/scripts/stats.py")
HEARTBEAT = "/tmp/growth_box_pending_audit.heartbeat"
ROW = re.compile(r"^\s*\|\s*(PAT-\d+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")


def beat():
    try:
        with open(HEARTBEAT, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds")}, f)
    except OSError:
        pass


def recompute():
    """真值：调 stats.py 重算（派生数据单一来源）"""
    if not os.path.exists(STATS):
        return {}, "stats.py 不存在"
    try:
        r = subprocess.run(
            [sys.executable, STATS, "--learnings-dir", LEARNINGS, "--index", INDEX],
            capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError) as e:
        return {}, f"stats.py 执行失败: {e}"
    out = {}
    for line in r.stdout.splitlines():
        m = ROW.match(line)
        if m:
            cnt = m.group(3).strip()
            out[m.group(1)] = {
                "count": int(cnt.replace("+", "")) if cnt.replace("+", "").isdigit() else 0,
                "count_raw": cnt,
                "latest": m.group(4).strip(),
            }
    return out, None


def read_index():
    rows = []
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            m = ROW.match(line)
            if m:
                pid, name, cnt, latest, status = m.groups()
                rows.append({"id": pid, "name": name.strip(), "count_col": cnt.strip(),
                             "latest": latest.strip(), "status": status.strip()})
    return rows


_INDEX_TEXT = ""


def detail_fields(pid):
    """提取 PAT-XXX 详情段的关键字段（用于查重与完整性校验）"""
    i = _INDEX_TEXT.find("### " + pid + "：")
    if i < 0:
        i = _INDEX_TEXT.find("### " + pid + ":")
    if i < 0:
        return None
    seg = _INDEX_TEXT[i:i + 1600]
    f = {}
    for m in re.finditer(r"\|\s*\*\*(.+?)\*\*\s*\|\s*([^|]*?)\s*\|", seg):
        f[m.group(1)] = m.group(2).strip()
    return f


def atomicity_check(index_rows):
    """原子性校验（2026-08-29 第一性原理：本质是入库环节无校验）

    三类非原子条目——任何基于"计数"的机械判据在这三类上都会系统性失效：
      🔴 重复登记 = 详情段(触发特征,根因,解法)三元组完全相同 → 同一模式两次入库
      🟡 无详情段 = 目录表有一行、但无定义段 → 不可判定也不可复用
      🟡 无关联错误 = 详情段存在但「关联错误」字段空/占位符 → 无实战来源
    """
    sig_map, no_detail, no_ref = {}, [], []
    for r in index_rows:
        f = detail_fields(r["id"])
        if not f:
            no_detail.append(r)
            continue
        sig = (f.get("触发特征", ""), f.get("根因", ""), f.get("解法", ""))
        if all(sig):
            sig_map.setdefault(sig, []).append(r["id"])
        rel = f.get("关联错误", "").strip()
        if not rel or rel in ("-", "—", "无"):
            no_ref.append(r)
    dup = [{"ids": ids, "sig": sig[0][:46]}
           for sig, ids in sig_map.items() if len(ids) > 1]
    return dup, no_detail, no_ref


def audit():
    global _INDEX_TEXT
    _INDEX_TEXT = open(INDEX, encoding="utf-8").read()
    truth, err = recompute()
    if err:
        return None, err
    rows = read_index()
    ghosts, inverted, empty_promoted, ok = [], [], [], []
    for r in rows:
        t = truth.get(r["id"], {})
        real = t.get("count", 0)
        m = re.search(r"pending\((\d+)/(\d+)\)", r["status"])
        if m:
            n = int(m.group(1))
            if n >= 3 and real == 0:
                ghosts.append({**r, "real": real, "claimed_n": n,
                               "why": f"状态标 {n}/3 但源文件独立记录引用 = 0"})
            elif real > n:
                inverted.append({**r, "real": real, "claimed_n": n,
                                 "why": f"实际引用 {real} 条 > 状态标 {n}/3"})
            else:
                ok.append(r)
        elif "已晋升" in r["status"] and real == 0:
            empty_promoted.append({**r, "real": real,
                                   "why": "状态已晋升但源文件零引用（历史晋升后清理？）"})
        else:
            ok.append(r)
    dup, no_detail, no_ref = atomicity_check(rows)
    return {"total": len(rows), "ghosts": ghosts, "inverted": inverted,
            "empty_promoted": empty_promoted, "ok": len(ok), "truth_rows": len(truth),
            "duplicates": dup, "no_detail": no_detail, "no_ref": no_ref}, None


def mode_check():
    beat()
    res, err = audit()
    if err:
        print(json.dumps({"alarm": True, "error": err}, ensure_ascii=False))
        return 1
    print(json.dumps({
        "alarm": bool(res["ghosts"]),
        "total": res["total"],
        "ghosts": [{"id": g["id"], "name": g["name"], "claimed": f"{g['claimed_n']}/3",
                    "real": g["real"]} for g in res["ghosts"]],
        "inverted": [{"id": g["id"], "claimed": f"{g['claimed_n']}/3", "real": g["real"]}
                     for g in res["inverted"]],
        "empty_promoted": [g["id"] for g in res["empty_promoted"]],
        "healthy": res["ok"],
        "note": "真值口径=stats.py 独立记录计数（⛔非文件数）",
    }, ensure_ascii=False, indent=2))
    return 0


def mode_report():
    beat()
    res, err = audit()
    if err:
        print(f"❌ {err}")
        return
    print("## 🧬 成长箱 pending 状态漂移体检")
    print()
    print(f"扫描 {res['total']} 条模式 ｜ 真值来源：stats.py 独立记录计数（⛔非文件数）")
    print()
    g, inv, ep = res["ghosts"], res["inverted"], res["empty_promoted"]
    print("| 判据 | 数量 | 含义 |")
    print("|---|---:|---|")
    print(f"| 🔴 幽灵条目 | {len(g)} | 状态标 N≥3 但源文件零引用 → **晋升判据虚标·阻断晋升** |")
    print(f"| 🟡 倒挂条目 | {len(inv)} | 实际引用 > 状态 N → 实例未回写（PAT-023 病） |")
    print(f"| ⚪ 零引用已晋升 | {len(ep)} | 提炼型模式（源记录用 QD 号不回写 PAT）→ **非问题** |")
    print(f"| ✅ 正常 | {res['ok']} | |")
    print()

    if g:
        print("### 🔴 幽灵条目（阻断晋升）")
        print("| 编号 | 模式 | 状态标 | 真实引用 | 判读 |")
        print("|---|---|---:|---:|---|")
        for x in g:
            print(f"| {x['id']} | {x['name'][:32]} | {x['claimed_n']}/3 | **0** | {x['why']} |")
        print()
    if inv:
        print("### 🟡 倒挂条目（实例未回写状态列）")
        print("| 编号 | 模式 | 状态标 | 真实引用 |")
        print("|---|---|---:|---:|")
        for x in inv:
            print(f"| {x['id']} | {x['name'][:32]} | {x['claimed_n']}/3 | {x['real']} |")
        print()
    if ep:
        print("### ⚪ 零引用已晋升（非问题·提炼型模式）")
        for x in ep:
            print(f"- {x['id']} {x['name'][:36]} — 源记录用 QD 编号不回写 PAT 号，非虚标")
        print()
    if not (g or inv or ep):
        print("> ✅ 状态列与源文件引用完全一致，无漂移。")


def mode_selfcheck():
    print(f"INDEX: {INDEX} {'✅' if os.path.exists(INDEX) else '❌'}")
    print(f"stats.py: {STATS} {'✅' if os.path.exists(STATS) else '❌'}")
    print("用法: growth_box_pending_audit.py [--check|--report|--selfcheck]")
    return 0


def main():
    a = sys.argv[1:]
    if "--selfcheck" in a:
        sys.exit(mode_selfcheck())
    if "--report" in a:
        mode_report()
        return
    sys.exit(mode_check())


if __name__ == "__main__":
    main()
