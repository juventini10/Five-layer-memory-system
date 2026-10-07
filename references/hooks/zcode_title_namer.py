#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v0.4
"""zcode_title_namer.py — ZCode 专属适配器：UserPromptSubmit 钩子新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题（原语来自 session_title_utils.py·跨工具中立·与 WB/DSH 同源）

落库目标（ZCode 有真会话库·对齐 WB 直写形态而非 DSH 索引文件）:
    ~/.zcode/cli/db/db.sqlite session 表 title 列 + title_source='custom' + time_title_updated。
    ⚠️ v0.2 根治（2026-09-12）：必须写 'custom' 而非 'generated'——ZCode 客户端自带标题自动
    生成（title_source='generated' 同名同源），钩子先写 generated 后客户端 ~4min 后生成即覆盖
    （双会话实锤：sess_fb5ed250 钩子 05:57:44 写→客户端 06:01:26 覆盖）；客户端对 'custom'
    永不覆盖（实证：sess_72d307ad 'Loop4' custom 一周未被客户端动过）→ 写 custom=终态不可逆覆盖。
    代价：'custom=手动命名' 语义被自动命名共用——你手动改名仍写 custom，不冲突。
    ⚠️ v0.4 根治（2026-09-27）：UI 库须同时写 tasks.title 列与 meta_json.$.title 嵌套键——
    客户端渲染读 meta_json 嵌套键而非 title 列（实证：钩子写列成功后新会话 UI 仍显原始
    prompt 截断，meta_json 未同步；老会话靠客户端 completed 时回写才变格式化=存在窗口期）。
    只写列 = 格式化标题对你不可见。

数据链路:
    ZCode UserPromptSubmit 钩子 stdin JSON {session_id, prompt, ...}
    → 首次观察到该 session_id（状态文件判断）→ 写 session.title
    → 状态文件 ~/.zcode/cache/title-namer/<session_id>.json 防重入

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 runtime.log）
    - 会话不在库中 → 跳过且**不写状态文件**（下轮 prompt 重试——ZCode 首轮 UPS 可能早于
      session 行落库，与 WB 的 not_in_db 永久跳过不同，这里失败可重试）
    - 子代理会话（sess_subagent_*）跳过——标题命名只管主会话
    - sqlite busy_timeout=5000 + WAL 并发安全
    - UPDATE 带 AND title_source != 'custom' 守卫——不覆盖手动命名

用法:
    echo '{"session_id":"<id>","prompt":"..."}' | python3 zcode_title_namer.py UserPromptSubmit   # 钩子模式
    python3 zcode_title_namer.py --dry-run --prompt "修复搜索超时问题" [--created-at-ms ...]      # 只看标题不写库
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

from session_title_utils import make_title

DB_PATH = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"
UI_DB_PATH = Path.home() / ".zcode" / "v2" / "tasks-index.sqlite"  # v0.3 双写：桌面端会话列表标题源
STATE_DIR = Path.home() / ".zcode" / "cache" / "title-namer"
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
            "SELECT title_source, time_created FROM session WHERE id=?", (session_id,)
        ).fetchone()
    finally:
        con.close()
    return row


def set_title(session_id: str, title: str, created_ms: int) -> bool:
    """写 title。v0.2：title_source 写 'custom'——客户端对 custom 永不覆盖（竞争写者根治）；
    v0.3：双写 UI 索引库 ~/.zcode/v2/tasks-index.sqlite tasks.title——桌面端会话列表读 UI 库
    而非 cli 逻辑库（只写 cli 库=界面永不显示，存量 14 条实锤）；title_overridden=0 才写
    （=1 系你手动命名·不碰）。带 title_source != 'custom' SQL 守卫——不覆盖你的手动命名。
    v0.4：UI 库同步写 meta_json.$.title——客户端渲染源是嵌套键不是列（v0.4 docstring 实证）。"""
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    try:
        con.execute("PRAGMA busy_timeout=5000")
        cur = con.execute(
            "UPDATE session SET title=?, title_source='custom', time_title_updated=? "
            "WHERE id=? AND title_source != 'custom'",
            (title, created_ms, session_id),
        )
        con.commit()
    finally:
        con.close()
    try:  # UI 索引库双写·失败静默（v0.4 前靠客户端回同步兜底，有窗口期——已根治）
        ui = sqlite3.connect(UI_DB_PATH, timeout=5)
        try:
            ui.execute("PRAGMA busy_timeout=5000")
            ui.execute(
                "UPDATE tasks SET title=?, meta_json=json_set(meta_json,'$.title',?) "
                "WHERE task_id=? AND title_overridden=0 AND deleted=0",
                (title, title, session_id),
            )
            ui.commit()
        finally:
            ui.close()
    except Exception:
        pass
    return cur.rowcount == 1


def hook_mode() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        payload = {}
    session_id = str(payload.get("session_id", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    if not session_id or not prompt:
        log(f"skip: no session_id/prompt (sid={session_id!r})")
        return
    if "subagent" in session_id:
        return  # 子代理会话不命名

    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        return  # 已处理过，防重入

    try:
        row = get_session(session_id)
        if row is None:
            # 会话行尚未落库（首轮 UPS 竞态）→ 不写状态文件，下轮 prompt 重试
            log(f"skip: session not in db yet sid={session_id}")
            return
        title_source, created_ms = row
        if title_source == "custom":
            log(f"skip: custom title (manual) sid={session_id}")
            state_file.write_text(json.dumps({"status": "manual_named"}, ensure_ascii=False))
            return
        ts = int(created_ms or 0) or int(datetime.now().timestamp() * 1000)
        title = make_title(prompt, ts)
        if set_title(session_id, title, ts):
            state_file.write_text(
                json.dumps({"status": "named", "title": title}, ensure_ascii=False)
            )
            log(f"named sid={session_id} title={title!r}")
        else:
            # 并发窗口：title 刚被你手动改名（custom）→ 尊重现状
            state_file.write_text(json.dumps({"status": "lost_race"}, ensure_ascii=False))
            log(f"skip: lost race (title set concurrently) sid={session_id}")
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
    hook_mode()


if __name__ == "__main__":
    main()
