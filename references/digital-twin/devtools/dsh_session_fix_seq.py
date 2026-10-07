#!/usr/bin/env python3
# version: v0.2
"""dsh_session_fix_seq.py — 修复"外部插入 title 事件导致 seq 撞号"的会话损坏。

背景（2026-09-10 五次事故·"历史加载失败：has seq gap"）
------------------------------------------------------
DSH 要求 v3 事件流的 seq 严格连续（每条 +1）。当外部脚本在**宿主运行时**向会话
事件流追加 `session/title` 事件时：
  · 外部脚本用 `max(seq)+1` 算新号
  · 宿主用**内存里的 seq 计数器**继续写
  → 两个写者各算各的 → 同一 seq 被写两次（撞号）
  → DSH 加载时报 `invalid committed event at line N: ... has seq gap (expected X, got X-1)`
  → 该会话"历史加载失败"

实证三例（2026-09-10）：
  a68dccc1 line1523 title(user) seq=1521 / line1524 agent/inbox/spliced seq=1521
  dab686c7 line336  title(user) seq=334  / line337  tool/result        seq=334
  b1810d3b line463  title(user) seq=461  / line464  agent/inbox/spliced seq=461

修复策略（保持事件语义·⛔不重新编号既有事件）
------------------------------------------
① 找到"不在末尾的 user title"事件（= 插在中间的那条，就是撞号的肇事者）
② 把它**从原位移除** —— 移除后既有事件序列自动恢复连续（因为撞号的两条只留一条）
③ 在**文件末尾**重新追加一条同内容 user title（seq = 末尾+1）—— append 语义正确·投影仍生效
④ 双重校验：a) seq 恢复连续 b) 帧契约合规 —— 任一不过则放弃写盘

⛔ 本工具不重排既有事件的 seq（`messageSeqs` 等字段会引用 seq，重排=破坏引用）。

用法
----
  python3 dsh_session_fix_seq.py --scan          # 扫描损坏会话
  python3 dsh_session_fix_seq.py --fix --all     # 修复全部
  python3 dsh_session_fix_seq.py --fix --all --dry-run
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsh_session_repair import compress, decompress, assert_frame_contract  # noqa: E402

ROOT_DEFAULT = os.path.expanduser("~/.dsh/sessions")


def session_files(root: str) -> list[str]:
    """只处理 v3 文件（v2 的 seq 跳跃是格式特征，不是损坏）。"""
    out = []
    for p in glob.glob(os.path.join(root, "*", "*", "session*.jsonl.zstd")):
        if ".bak-" in p or ".tmp-" in p:
            continue
        out.append(p)
    return sorted(out)


def is_user_title(e: dict) -> bool:
    if e.get("type") != "session/title":
        return False
    return ((e.get("data") or {}).get("source") or {}).get("kind") == "user"


def find_gaps(events: list) -> list:
    """返回**真损坏**的 seq 断点 [(行号, 前值, 当前值, 类型)]。

    判据（2026-09-10 收紧·对齐 DSH 实际报错）：
      · ✅ 真损坏 = `seq <= 前一个 seq`（**重复或倒退**）——DSH 报 `expected X, got X-1`
      · ❌ 不算损坏 = `seq > 前一个+1`（**前进跳跃**）——未提交的 seq 本就被跳过，
        且 assistant/chunk 分段不占 seq 序列（v2 文件大量跳跃即属此列）
    收紧前把 13 个文件误报为损坏（含大量正常跳跃），实际只有 3 个真撞号。
    """
    gaps, prev = [], None
    for i, e in enumerate(events, 1):
        s = e.get("seq")
        if s is None:
            continue
        if prev is not None and s <= prev and e.get("type") != "assistant/chunk":
            gaps.append((i, prev, s, e.get("type")))
        prev = s
    return gaps


def diagnose(path: str) -> dict:
    events = [json.loads(l) for l in decompress(path).decode("utf-8").splitlines() if l.strip()]
    last_non_title = -1
    for i, e in enumerate(events):
        if e.get("type") != "session/title":
            last_non_title = i
    movable = [(i, e) for i, e in enumerate(events) if is_user_title(e) and i <= last_non_title]
    return {"events": events, "n": len(events), "movable": movable, "gaps": find_gaps(events)}


def fix_one(path: str, dry: bool = False) -> tuple[str, str | None]:
    # 🔴 2026-09-10 六次事故根治（禁源）：v0 遗留格式**一律跳过**。
    #   本工具的标题搬迁姿势是「删原位 user 标题行 → 末尾重新追加」，对 v3 安全（容忍缺号），
    #   对 v0 却是数据破坏：v0→v1 迁移器要求 seq 严格连续，删中间行即整会话加载失败
    #   （实证：--fix --all 一次改坏 10 个 v0 会话·报 "released Session row 6 has seq gap"）。
    #   ⛔DO NOT 在此工具内"顺便兼容" v0——v0 的正确姿势是原位更新，属另一支路，需要时新开工具。
    if os.path.basename(path) == "session.jsonl.zstd":
        return "skip-v0-guard", None
    d = diagnose(path)
    if not d["movable"]:
        return ("skip-ok" if not d["gaps"] else "skip-no-title"), None
    events = d["events"]
    remove = {i for i, _ in d["movable"]}
    kept = [e for i, e in enumerate(events) if i not in remove]
    src = d["movable"][-1][1]
    title = (src.get("data") or {}).get("title")
    max_seq = max((e.get("seq") or 0) for e in kept)
    kept.append({
        "type": "session/title",
        "seq": max_seq + 1,
        "time": int(time.time() * 1000),
        "data": {"title": title, "messageSeqs": [], "source": {"kind": "user"}},
    })
    # 校验 a：seq 恢复连续
    still = find_gaps(kept)
    if still:
        return f"fail-still-gap({still[0][1]}→{still[0][2]}@{still[0][3]})", title
    if dry:
        return "would-fix", title

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak-{ts}-preseqfix"
    subprocess.run(["cp", path, backup], check=True)
    tmp = f"{path}.tmp-{ts}"
    data = ("\n".join(json.dumps(e, ensure_ascii=False) for e in kept) + "\n").encode("utf-8")
    compress(data, tmp)
    # 校验 b：帧契约
    try:
        assert_frame_contract(tmp)
    except RuntimeError as e:
        os.remove(tmp)
        return f"fail-frame({e})", title
    # 校验 c：回验内容可解析且无断点
    chk = [json.loads(l) for l in decompress(tmp).decode("utf-8").splitlines() if l.strip()]
    if find_gaps(chk):
        os.remove(tmp)
        return "fail-verify-gap", title
    os.replace(tmp, path)
    return "fixed", title


def main() -> None:
    ap = argparse.ArgumentParser(description="DSH 会话 seq 撞号修复")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    files = session_files(a.root)
    if a.scan or a.dry_run:
        bad = 0
        for p in files:
            try:
                d = diagnose(p)
            except Exception as e:
                print(f"  [skip] {os.path.basename(os.path.dirname(p))}: {type(e).__name__}")
                continue
            if d["gaps"]:
                bad += 1
                g = d["gaps"][0]
                print(f"❌ {os.path.basename(os.path.dirname(p))[:40]:42} 断点{len(d['gaps'])} 首处 line{g[0]} {g[1]}→{g[2]} ({g[3]}) 可修={bool(d['movable'])}")
        print(f"\n共 {len(files)} 文件 | ❌有断点 {bad}")
        return

    if not (a.fix and a.all):
        ap.print_help()
        return

    stats, fails = {}, []
    for p in files:
        try:
            r, t = fix_one(p, dry=False)
        except Exception as e:
            r, t = f"error:{type(e).__name__}", None
        stats[r] = stats.get(r, 0) + 1
        if r in ("fixed", "would-fix"):
            print(f"🔧 {os.path.basename(os.path.dirname(p))[:40]:42} → {str(t)[:36]}")
        elif r.startswith(("fail", "error")):
            fails.append(f"{os.path.basename(os.path.dirname(p))}:{r}")
            print(f"⚠️ {os.path.basename(os.path.dirname(p))[:40]:42} {r}")
    print("\n统计：" + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if fails:
        print(f"⚠️ 失败 {len(fails)}：原文件与备份均在·未动")
        for f in fails[:6]:
            print("   ", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
