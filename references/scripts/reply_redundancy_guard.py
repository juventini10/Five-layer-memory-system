#!/usr/bin/env python3
# version: v1.0.0
"""回复冗余守卫 —— 拦「每轮套同一套模板」的自我复述。

## 为什么存在（2026-10-02 by Hermes·你两次报障）

你原话：「为什么你的回复老是重复地回复给我呢？这个视觉上看真的很累啊」
       「现在不止你这个对话，其他对话也是这样，来来回回重复出现很多信息，
         也浪费TOKEN，知道吗？我自己看的也不清不糊的」

**实测根因（⛔ 不是 hook 注入）**：
- 排查 16 个插件的 `pre_llm_call` / `system_prompt_section` / `post_llm_call`
  ⇒ 每轮注入的 context 极少（3 处命中全在注释里）·**不是元凶**
- 真因 = **AI 自己的输出模式固定**：每轮都写
  「结论表 + 判据/根因/实证的复盘 + 决策词收尾」
  ⇒ 同类词在同一会话反复出现（实测某会话 `⛔` 45 次 / `判据` 58 次）
  ⇒ 你看到的是**同一套模板反复套**·token 也白烧

**判据**：
1. `template_terms`：模板词（⛔/判据/根因/实证/教训/遗留/端到端/MUT:OK…）
   在同一会话内的密度超阈值 ⇒ RED
2. `duplicate_paragraph`：同一会话内**完全重复的长段落**
   （≥80 字且出现 ≥2 次）⇒ RED（最硬的指纹）

⛔ 纪律：**只检测不阻断**（报告制·恒 exit 0）——风格守卫不该卡死对话。
✅ 数据源：`~/.hermes/state.db` 的 `messages` 表（role='assistant'）·端隔离。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter

VERSION = "v1.0.0"
DB = os.path.expanduser("~/.hermes/state.db")

TEMPLATE_TERMS = (
    "⛔", "判据", "根因", "实证", "教训", "遗留", "端到端", "MUT:OK",
    "一条我该说的", "值得记", "沉淀", "护栏", "闭环", "反思",
)
TERM_PER_MSG_LIMIT = 2.5
PARA_MIN = 80
PARA_REPEAT = 2


def _messages(sid: str, limit: int = 30) -> list:
    con = sqlite3.connect(DB, timeout=15)
    # ⚠️ 2026-10-02 变异测试抓出：门槛原为 `length(content) > 80`，
    #    但 SQLite 的 `length()` 对中文按**字符**计 ⇒ 80~200 字的正常回复被全滤掉
    #    （实测造 4 条重复事实的消息·查询返回 0 条）⇒ 守卫形同虚设。
    #    ⇒ 降到 40（够滤掉"好的""收到"这类寒暄，又不漏正常回复）。
    rows = con.execute(
        "SELECT content FROM messages WHERE session_id=? AND role='assistant' "
        "AND content IS NOT NULL AND length(content) > 40 "
        "ORDER BY id DESC LIMIT ?", (sid, limit)).fetchall()
    con.close()
    return [r[0] for r in reversed(rows)]


def check(sid: str, limit: int = 30) -> dict:
    msgs = _messages(sid, limit)
    findings = []
    if len(msgs) < 4:
        return {"version": VERSION, "session": sid, "messages": len(msgs),
                "findings": findings, "red": 0, "warn": 0}

    text = " ".join(" ".join(m.split()) for m in msgs)
    c = Counter()
    for t in TEMPLATE_TERMS:
        n = text.count(t)
        if n:
            c[t] = n
    per_msg = {t: n / len(msgs) for t, n in c.items()}
    hot = {t: round(v, 1) for t, v in per_msg.items() if v > TERM_PER_MSG_LIMIT}
    if hot:
        findings.append({
            "level": "RED", "kind": "template_terms",
            "detail": f"{len(msgs)} 条回复模板词密度超阈值（>{TERM_PER_MSG_LIMIT}/条）："
                      f"{hot} ⇒ 同一套话术在反复套"})

    paras = Counter()
    for m in msgs:
        for p in re.split(r"\n\s*\n", m):
            p = " ".join(p.split())
            if len(p) >= PARA_MIN:
                paras[p] += 1
    dup = {p[:60]: n for p, n in paras.items() if n >= PARA_REPEAT}
    if dup:
        findings.append({
            "level": "RED", "kind": "duplicate_paragraph",
            "detail": f"{len(dup)} 段长文本（≥{PARA_MIN}字）重复出现 ≥{PARA_REPEAT} 次："
                      f"{list(dup)[:3]}"})

    # ③ 事实性片段重列（2026-10-02 你「来来回回重复」实测最硬的一类）
    #    判据：时间戳 / 版本号 / 数字 ID 这类**具体事实**在同一会话多条回复里
    #    出现 ≥2 次 ⇒ 说明我在每轮重开证据表·同一证据隔轮完整重列。
    #    ⚠️ 这是本守卫最有价值的一条——它测的不是"话术重复"（那是风格），
    #    而是"信息重复"（那是 token 浪费 + 你的眼睛看不清）。
    # ⚠️ 2026-10-02 变异测试后收窄：原式含 `\b\d{3,5}\b` 会把 `2026`（年份）
    #    `444`（锁号）`100`（百分比）这类**碎片**算成"事实"⇒ 误报。
    #    ⇒ 只保留**高特异性**模式：完整时间戳 / 带字母前缀的版本号 / 长 ID(≥6 位)。
    fact_pat = re.compile(
        r"\b\d{2}:\d{2}:\d{2}\b"          # 完整时间戳 HH:MM:SS
        r"|\bv\d+\.\d+(?:\.\d+)?\b"     # 版本号 v1.3.97
        r"|\b20\d{2}-\d{2}-\d{2}\b"     # 日期 2026-10-02
        r"|\b[0-9a-f]{12,}\b"              # 长 hash/id
    )
    facts = Counter()
    for m in msgs:
        for f in set(fact_pat.findall(m)):
            facts[f] += 1
    fact_rep = {k: v for k, v in facts.items() if v >= 2}
    if fact_rep:
        top = sorted(fact_rep.items(), key=lambda kv: -kv[1])[:6]
        findings.append({
            "level": "RED", "kind": "fact_restated",
            "detail": f"{len(fact_rep)} 个具体事实（时间戳/版本号/ID）在多条回复里重列 ≥2 次："
                      f"{top} ⇒ 每轮重开证据表·同一结论隔轮完整重列"})

    return {"version": VERSION, "session": sid, "messages": len(msgs),
            "terms": {t: round(v, 1) for t, v in per_msg.items()},
            "facts_restated": fact_rep,
            "findings": findings,
            "red": sum(1 for f in findings if f["level"] == "RED"),
            "warn": 0}


def _self_test() -> int:
    ok = 0
    con = sqlite3.connect(DB, timeout=15)
    sids = [r[0] for r in con.execute(
        "SELECT id FROM sessions ORDER BY started_at DESC LIMIT 6")]
    con.close()
    red = sum(1 for s in sids if check(s, 30)["red"])
    print(f"  抽样 {len(sids)} 个会话 · 判红 {red} 个")
    ok += 1
    r = check("nonexistent_sid_xxx", 30)
    assert r["red"] == 0, "空会话不应判红"
    print("  空会话不判红 OK")
    ok += 1
    print(f"SELF-TEST: {'OK' if ok == 2 else 'FAIL'}")
    return 0 if ok == 2 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="回复冗余守卫（只检测不阻断）")
    ap.add_argument("--session-id", "-s")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if a.session_id:
        print(json.dumps(check(a.session_id, a.limit), ensure_ascii=False, indent=2))
        return 0
    con = sqlite3.connect(DB, timeout=20)
    sids = [x[0] for x in con.execute(
        "SELECT id FROM sessions ORDER BY started_at DESC LIMIT 12")]
    con.close()
    print(f"回复冗余巡检 · {VERSION} · 最近 {len(sids)} 个会话\n")
    tot = 0
    for s in sids:
        r = check(s, a.limit)
        tot += r["red"]
        flag = f"RED {r['red']}" if r["red"] else "OK"
        print(f"  {flag:7} {s[:26]:28} {r['messages']:>3} 条")
        for f in r["findings"]:
            print(f"          └ {f['detail'][:140]}")
    print(f"\n→ 判红会话 {tot}/{len(sids)}（⛔ 报告制·不阻断对话）")
    return 0


if __name__ == "__main__":
    sys.exit(main())