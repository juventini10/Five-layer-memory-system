#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v0.1
"""session_title_batch_rename.py — 历史会话标题批量统一为「YYMMDD | 类型 | 主题」。

规则（你立 2026-09-09）：复用 session_title_namer 的日期/分类/主题函数；
范围 = custom_title IS NULL 的普通会话（is_background_automation 非真）——
已有 custom_title（你/宿主手动命名过）的不动，除非 --force。
写前 DB 文件级备份由调用方保证；单事务 + 每行 custom_title IS NULL 守卫。

用法:
    python3 session_title_batch_rename.py --dry-run   # 只打印映射不写库
    python3 session_title_batch_rename.py --apply     # 落库并写台账
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from session_title_namer import DB_PATH, classify, extract_theme, bj_date_from_ms

LEDGER = Path.home() / "WorkBuddy/开发/output/对话标题批量改名台账-20260909.md"

TARGET_SQL = """
SELECT id, title, created_at FROM sessions
WHERE deleted_at IS NULL
  AND custom_title IS NULL
  AND title IS NOT NULL AND title != ''
  AND (is_background_automation IS NULL OR is_background_automation = 0)
ORDER BY created_at DESC
"""

# force 模式：全部未符合新格式的会话（含手动命名+自动化）；
# 标题源=COALESCE(custom_title, title)——手动命名优先作主题与分类依据。
# 已符合 YYMMDD | 格式的跳过（幂等，不重复改）。
FORCE_TARGET_SQL = """
SELECT id, COALESCE(NULLIF(custom_title,''), title) AS src, created_at FROM sessions
WHERE deleted_at IS NULL
  AND COALESCE(NULLIF(custom_title,''), title) IS NOT NULL
  AND COALESCE(NULLIF(custom_title,''), title) != ''
  AND COALESCE(NULLIF(custom_title,''), '') NOT GLOB '[0-9][0-9][0-9][0-9][0-9][0-9] | *'
ORDER BY created_at DESC
"""


def fetch_targets(force: bool = False):
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        return con.execute(FORCE_TARGET_SQL if force else TARGET_SQL).fetchall()
    finally:
        con.close()


def plan_rows(rows):
    plan = []
    for sid, title, created_ms in rows:
        date = bj_date_from_ms(int(created_ms))
        theme = extract_theme(title)
        new_title = f"{date} | {classify(title)} | {theme}"
        plan.append((sid, title.strip(), new_title))
    return plan


def apply(plan, force: bool = False):
    con = sqlite3.connect(str(DB_PATH), timeout=10)
    done = []
    try:
        con.execute("PRAGMA busy_timeout=10000")
        for sid, old, new in plan:
            if force:
                # force：覆盖非格式旧名；已符合格式的不动（幂等双保险）
                guard = "AND COALESCE(NULLIF(custom_title,''), '') NOT GLOB '[0-9][0-9][0-9][0-9][0-9][0-9] | *'"
            else:
                guard = "AND custom_title IS NULL"
            cur = con.execute(
                f"UPDATE sessions SET custom_title=? WHERE id=? {guard}",
                (new, sid),
            )
            if cur.rowcount == 1:
                done.append((sid, old, new))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return done


def write_ledger(done, force: bool = False):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tag = "第二轮·force全量统一" if force else "第一轮"
    lines = [
        "",
        f"## {tag} · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"> 共 {len(done)} 条" + ("（覆盖手动命名+含自动化会话·皮叔授权全量统一）" if force else ""),
        "",
        "| 会话ID | 原标题 | 新标题 |",
        "|---|---|---|",
    ]
    for sid, old, new in done:
        lines.append(f"| {sid[:8]} | {old} | {new} |")
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return LEDGER


def main():
    argv = sys.argv[1:]
    force = "--force" in argv
    mode = next((a for a in argv if a.startswith("--") and a != "--force"), "--dry-run")
    plan = plan_rows(fetch_targets(force))
    if mode == "--dry-run":
        print(f"待改 {len(plan)} 条{'（force·覆盖手动命名）' if force else ''}，映射预览（前15）：")
        for _, old, new in plan[:15]:
            print(f"  {old}  ⇒  {new}")
        return
    if mode == "--apply":
        done = apply(plan, force)
        path = write_ledger(done, force)
        print(f"已改名 {len(done)} 条（守卫拦下 {len(plan)-len(done)} 条）｜台账：{path}")
        for _, old, new in done[:10]:
            print(f"  {old}  ⇒  {new}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
