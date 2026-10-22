#!/usr/bin/env python3
# version: v0.3
# v0.3（2026-10-22·皮叔问「90天谁记得」）：扫描域扩到 记忆蓝图/**（正文内 TTL，含 2026-10-22 转正条文）+ 到期前 7 天预警 + --check 人工/CI 校验口；原 v0.2：输出协议委托 hook_protocol
"""ttl_expiry_guard.py — UserPromptSubmit 钩子：规则文件 TTL 过期/临期自动提醒（每会话首prompt一次）。
扫描 记忆规则/*.md（头部）+ 记忆蓝图/**/*.md（正文「过期：YYYY-MM-DD」）→ 已过期或 7 天内到期则注入提醒；否则静默。
--check：人工/CI 校验口（列出全部 TTL，有已过期 exit 1）。
防重入：cache/ttl-expiry/<sid>.json。异常 exit 0。"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import json, os, re, sys
from datetime import datetime
from pathlib import Path

RULES_DIR = Path(os.path.expanduser("[记忆共享中心]/记忆规则"))
BLUEPRINT_DIR = Path(os.path.expanduser("[记忆共享中心]/记忆蓝图"))
SOON_DAYS = int(os.environ.get("TTL_SOON_DAYS", "7"))
STATE_DIR = Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or (Path.home() / ".workbuddy")) / "cache/ttl-expiry"


def _scan_file(p, whole=False):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    if not whole:
        text = text[:800]
    out, today = [], datetime.now().date()
    for ln, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"过期[:：]\s*(\d{4}-\d{2}-\d{2})", line):
            try:
                d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            out.append((p.name, m.group(1), (d - today).days, ln, str(p)))
    return out


def collect_ttls():
    """返回 (overdue, soon, all)：均按剩余天数升序。"""
    items = []
    if RULES_DIR.is_dir():
        for p in sorted(RULES_DIR.glob("*.md")):
            items += _scan_file(p, whole=False)
    if BLUEPRINT_DIR.is_dir():
        for dp, dns, fns in os.walk(BLUEPRINT_DIR):
            dns[:] = [d for d in dns if d not in ("归档", "_archive", "__pycache__") and ("备份" not in d) and ("bak" not in d.lower())]
            if "/归档" in dp or "Trash" in dp:
                continue
            for fn in fns:
                if not fn.endswith(".md"):
                    continue
                items += _scan_file(Path(dp) / fn, whole=True)
    seen, uniq = set(), []
    for it in items:
        k = (it[4], it[3], it[1])
        if k in seen:
            continue
        seen.add(k); uniq.append(it)
    uniq.sort(key=lambda x: x[2])
    overdue = [x for x in uniq if x[2] < 0]
    soon = [x for x in uniq if 0 <= x[2] <= SOON_DAYS]
    return overdue, soon, uniq


def main():
    if "--check" in sys.argv:
        ov, soon, all_ = collect_ttls()
        print("TTL 扫描：共 %d 条（已过期 %d · %d 天内到期 %d）" % (len(all_), len(ov), SOON_DAYS, len(soon)))
        for name, date, left, ln, path in all_:
            tag = "已过期" if left < 0 else ("临期" if left <= SOON_DAYS else "有效")
            print("  [%s] %s ｜ 过期 %s ｜ 剩 %d 天 ｜ %s:%d" % (tag, name, date, left, path.replace(os.path.expanduser("~"), "~"), ln))
        return 1 if ov else 0
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
        sid = str(payload.get("session_id", "")).strip()
    except Exception:
        sys.exit(0)
    if not sid:
        sys.exit(0)
    state = STATE_DIR / f"{sid}.json"
    if state.exists():
        sys.exit(0)  # 本会话已查过
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        ov, soon, _all = collect_ttls()
        state.write_text(json.dumps({"checked": True, "overdue": len(ov), "soon": len(soon)}, ensure_ascii=False))
        if ov or soon:
            parts = []
            if ov:
                parts.append("已过期：" + "；".join(f"{name}({-left}天)" for name, _, left, _, _ in ov[:4]))
            if soon:
                parts.append("临期(≤%d天)：" % SOON_DAYS + "；".join(f"{name}余{left}天" for name, _, left, _, _ in soon[:4]))
            msg = "【⏰ TTL 提醒】" + " ｜ ".join(parts) + "——引用其内容前先声明状态或更新（铁律-010）"
            # 输出协议委托 hook_protocol 单一真源（2026-09-18 Qoder CN 挂载轮·对齐 secret_key_guard）：
            #   本端裸 stdout 判 winner=none 整轮丢弃；text 端由真源维持裸文本，零回归。
            try:
                import hook_protocol as _hp
                _hp.emit(msg, payload=payload, argv=sys.argv[1:],
                         event="UserPromptSubmit", script="ttl_expiry_guard.py")
            except Exception:
                sys.stdout.write(msg)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
