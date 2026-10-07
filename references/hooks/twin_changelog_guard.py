#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/twin_changelog_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# version: v0.1
"""twin_changelog_guard.py —— 童灵规格书↔CHANGELOG 同步守卫

🔴 立脚本原因（2026-08-29 你提出"更新信息应集中到更新文件"）：
  版本记录与机制说明外置到 `数字分身/CHANGELOG.md` 后，引入**新风险**：
  改了规格书却没更新 CHANGELOG = 另一处文档与实盘脱钩（同源漂移病）。

判据（两条，任一命中即提示）：
  1. 规格书 mtime **晚于** CHANGELOG mtime（超过容忍窗口）→ 改了正文没记变更
  2. 规格书内容 hash 与上次记录不同 → 正文实质变化，须在 CHANGELOG 留痕

契约：--check(JSON,含 alarm) / --report / --selfcheck / --baseline（写入基线）
⛔ 提示级（alarm 恒 false）——同 vision_gate：提醒别漏，不拦交付。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
import hashlib
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]/数字分身")
SPEC = os.path.join(BASE, "童灵·人格规格书.md")
CHG = os.path.join(BASE, "CHANGELOG.md")
STATE = "/tmp/twin_changelog_state.json"
TOLERATE_SEC = 300  # 5 分钟内视为同批修改，不算漂移


def beat(mark=True):
    pass


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def mtime(p):
    return os.path.getmtime(p) if os.path.exists(p) else 0.0


def last_change_date():
    """CHANGELOG 里最近一次 ## YYYY-MM-DD 标题"""
    if not os.path.exists(CHG):
        return None
    txt = open(CHG, encoding="utf-8").read()
    ds = re.findall(r"^## (\d{4}-\d{2}-\d{2})", txt, re.M)
    return max(ds) if ds else None


def check():
    if not os.path.exists(SPEC):
        return {"error": "规格书不存在"}
    if not os.path.exists(CHG):
        return {"drift": True, "reason": "CHANGELOG.md 不存在（外置后未建立）"}
    d = mtime(SPEC) - mtime(CHG)
    h = sha(SPEC)
    prev = None
    if os.path.exists(STATE):
        try:
            prev = json.load(open(STATE, encoding="utf-8")).get("sha")
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "spec_mtime": round(mtime(SPEC), 1),
        "changelog_mtime": round(mtime(CHG), 1),
        "spec_newer_by_sec": round(d, 1),
        "time_drift": d > TOLERATE_SEC,
        "sha": h,
        "sha_changed": bool(prev and prev != h),
        "last_change_date": last_change_date(),
        "drift": (d > TOLERATE_SEC) or bool(prev and prev != h),
    }


def mode_check():
    r = check()
    r["alarm"] = False  # 提示级
    if r.get("drift"):
        r["reminder"] = ("⚠️ 规格书已变更但 CHANGELOG 未同步——补一条 `## YYYY-MM-DD` 变更记录"
                         "（外置后新引入的漂移风险，靠本守卫兜底）")
    else:
        r["reminder"] = None
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def mode_baseline():
    json.dump({"sha": sha(SPEC), "ts": datetime.now().isoformat(timespec="seconds")},
              open(STATE, "w", encoding="utf-8"))
    print(json.dumps({"ok": True, "baseline": sha(SPEC)}, ensure_ascii=False))
    return 0


def main():
    a = sys.argv[1:]
    if "--selfcheck" in a:
        print(f"规格书: {SPEC} {'✅' if os.path.exists(SPEC) else '❌'}")
        print(f"CHANGELOG: {CHG} {'✅' if os.path.exists(CHG) else '❌'}")
        print("用法: twin_changelog_guard.py [--check|--report|--selfcheck|--baseline]")
        return 0
    if "--baseline" in a:
        sys.exit(mode_baseline())
    sys.exit(mode_check())


if __name__ == "__main__":
    main()
