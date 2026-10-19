#!/usr/bin/env python3
# version: v0.1
"""wbai_title_namer.py — WorkBuddy AI（国际版）专属适配器：新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy-ai/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题
    日期 = 北京时区实际创建日期（取 sessions.created_at）
    类型 ∈ {功能,设计,修复,优化,发布,探索,文档,研究}（关键词启发式，默认=探索）
    主题 = 首条 prompt 简洁概括
    只动 custom_title（预留的用户自定义标题位）——title 列留给宿主自动起名，不动。
    已有 custom_title（手动命名过）→ 永不覆盖。

原语来源（2026-09-10 抽公共·跨工具中立）:
    classify / extract_theme / make_title / bj_date_from_ms 在
    [记忆共享中心]/脚本中心/内容创作/session_title_utils.py（各端适配器 import，⛔DO NOT 复制实现）。
    本文件只保留 WorkBuddy AI 国际版专属的「定位会话 + 落库」两件事——对齐
    §二·七 2026-09-10 皮叔令「端适配器只写定位会话+落库」与 dsh_title_namer.py 先例。

与国内版适配器（session_title_namer.py）的唯一差异:
    数据根 ~/.workbuddy/ → ~/.workbuddy-ai/（其余逻辑同构·同库结构 sessions.custom_title）

数据链路:
    WorkBuddy AI UserPromptSubmit 钩子 stdin JSON {session_id, prompt, ...}
    → 首次观察到该 session_id（状态文件判断）→ 写 sessions.custom_title
    → 状态文件 ~/.workbuddy-ai/cache/title-namer/<session_id>.json 防重入

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 runtime.log）
    - UPDATE 带 `AND custom_title IS NULL` 守卫——不覆盖手动命名
    - sqlite busy_timeout=5000 并发安全
    - 无 session_id / 会话不在库中 → 跳过不猜（fail-open to no-rename）
    - ⛔绝不写 ~/.workbuddy/（国内版数据根）——端隔离红线

用法:
    echo '{"session_id":"<id>","prompt":"..."}' | python3 wbai_title_namer.py UserPromptSubmit  # 钩子模式
    python3 wbai_title_namer.py --dry-run --prompt "修复搜索超时问题"                              # 只看标题不写库
    python3 wbai_title_namer.py --set <session_id> --title "260911 | 功能 | 主题"                  # 手动/历史改名
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import json
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

from session_title_utils import make_title

DB_PATH = Path.home() / ".workbuddy-ai" / "workbuddy.db"
STATE_DIR = Path.home() / ".workbuddy-ai" / "cache" / "title-namer"
RUNTIME_LOG = STATE_DIR / "runtime.log"


def log(msg: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(RUNTIME_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def get_session(session_id: str):
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    try:
        con.execute("PRAGMA busy_timeout=5000")
        row = con.execute(
            "SELECT custom_title, created_at FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
    finally:
        con.close()
    return row


def set_custom_title(session_id: str, title: str, force: bool = False) -> bool:
    """force=False（钩子首轮自动命名）=带 NULL 守卫·永不覆盖手动命名；
    force=True（--set 手动/历史改名通道）=允许覆盖。"""
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    try:
        con.execute("PRAGMA busy_timeout=5000")
        sql = ("UPDATE sessions SET custom_title=? WHERE id=?" if force
               else "UPDATE sessions SET custom_title=? WHERE id=? AND custom_title IS NULL")
        cur = con.execute(sql, (title, session_id))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def hook_mode() -> None:
    try:
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        payload = {}
    session_id = str(payload.get("session_id", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    if not session_id or not prompt:
        log(f"skip: no session_id/prompt (sid={session_id!r})")
        return

    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        return  # 已处理过，防重入

    try:
        row = get_session(session_id)
        if row is None:
            log(f"skip: session not in db sid={session_id}")
            state_file.write_text(json.dumps({"status": "not_in_db"}, ensure_ascii=False))
            return
        custom_title, created_ms = row
        if custom_title:
            log(f"skip: custom_title already set sid={session_id}")
            state_file.write_text(json.dumps({"status": "already_named"}, ensure_ascii=False))
            return
        title = make_title(prompt, int(created_ms or 0) or int(datetime.now().timestamp() * 1000))
        if set_custom_title(session_id, title):
            state_file.write_text(
                json.dumps({"status": "named", "title": title}, ensure_ascii=False)
            )
            log(f"named sid={session_id} title={title!r}")
        else:
            state_file.write_text(json.dumps({"status": "lost_race"}, ensure_ascii=False))
            log(f"skip: lost race (custom_title set concurrently) sid={session_id}")
    except Exception as e:  # 钩子永不阻塞主流程
        log(f"error sid={session_id}: {type(e).__name__}: {e}")
    sys.exit(0)


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--dry-run":
        prompt, created_ms = "", int(datetime.now().timestamp() * 1000)
        i = 1
        while i < len(args):
            if args[i] == "--prompt":
                prompt = args[i + 1]
                i += 2
            elif args[i] == "--created-at-ms":
                created_ms = int(args[i + 1])
                i += 2
            else:
                i += 1
        print(make_title(prompt, created_ms))
        return
    if args and args[0] == "--set":
        sid, title = args[1], ""
        i = 2
        while i < len(args):
            if args[i] == "--title":
                title = args[i + 1]
                i += 2
            else:
                i += 1
        ok = set_custom_title(sid, title, force=True)
        print(f"{'OK' if ok else 'SKIP(会话不存在)'}: {sid} -> {title!r}")
        log(f"manual-set sid={sid} ok={ok} title={title!r}")
        return
    hook_mode()


if __name__ == "__main__":
    main()
