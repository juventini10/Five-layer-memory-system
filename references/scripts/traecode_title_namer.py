#!/usr/bin/env python3
# version: v0.1
"""traecode_title_namer.py — TraeCode 专属适配器：新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题（原语来自 session_title_utils.py·跨工具中立·与 WB/DSH 同源）

落库目标（2026-09-16 定案·对齐 DSH 先例——TraeCode 会话库 database.db 非标准 sqlite 不可写）:
    [记忆共享中心]/Trae记忆/session-titles.jsonl —— append 一行 {"session_id","title","created_at","at"}。
    只写新会话首轮（防重入 state 文件 [记忆共享中心]/Trae记忆/cache/title-namer/<session_id>.json）。
    ⚠️ 纯索引文件，⛔DO NOT 改 TraeCode 会话存储本体（宿主私有格式）。

数据链路:
    TraeCode UserPromptSubmit 钩子（~/.trae-cn/hooks.json）:
        stdin JSON {session_id, prompt, ...}（官网 stdin 通用字段 + 事件字段）
    → 首轮（state 文件不存在）→ 生成标题 → append 到 session-titles.jsonl + 写 state

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 stderr）
    - 已有 state 文件 → 跳过（防重入·对齐 WB/DSH）
    - 无 session_id / 无 prompt → 跳过不猜（fail-open to no-rename）

用法:
    echo '{"session_id":"<id>","prompt":"..."}' | python3 traecode_title_namer.py   # 钩子模式（读 stdin）
    python3 traecode_title_namer.py --prompt "修复搜索超时问题"                      # 钩子模式（参数）
    python3 traecode_title_namer.py --dry-run --prompt "修复搜索超时问题"           # 只看生成的标题不写
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from session_title_utils import make_title

TRAE_DIR = Path('[记忆共享中心]') / "Trae记忆"
TITLES_FILE = TRAE_DIR / "session-titles.jsonl"
STATE_DIR = TRAE_DIR / "cache" / "title-namer"


def already_named(session_id: str) -> bool:
    return (STATE_DIR / f"{session_id}.json").exists()


def mark_named(session_id: str, title: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{session_id}.json").write_text(
            json.dumps({"status": "named", "title": title, "at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def append_title(session_id: str, title: str, created_ms: int) -> None:
    """append 落库（O_APPEND 原子性·并发安全·对齐铁律-014 ②）。"""
    try:
        TITLES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TITLES_FILE, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"session_id": session_id, "title": title, "created_at_ms": created_ms, "at": datetime.now().isoformat(timespec="seconds")},
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception as e:
        sys.stderr.write(f"traecode_title_namer: append 失败 {type(e).__name__}: {e}\n")


def hook_mode(session_id: str, prompt: str, created_ms: int | None) -> None:
    if not session_id or not prompt.strip():
        return
    if already_named(session_id):
        return  # 防重入
    ts = created_ms if created_ms is not None else int(datetime.now().timestamp() * 1000)
    title = make_title(prompt, ts)
    append_title(session_id, title, ts)
    mark_named(session_id, title)


def parse_stdin() -> dict:
    """读 hooks stdin JSON（失败返回空 dict·fail-open）。"""
    try:
        data = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        if not data.strip():
            return {}
        return json.loads(data)
    except Exception:
        return {}


def main() -> None:
    args = sys.argv[1:]
    prompt_arg, created_ms, dry_run = "", None, False
    i = 0
    while i < len(args):
        if args[i] == "--prompt":
            prompt_arg = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif args[i] == "--created-at-ms":
            created_ms = int(args[i + 1])
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    # 优先读 stdin（hooks 模式）；--prompt 参数为手动/预研模式
    payload = parse_stdin()
    session_id = payload.get("session_id") or payload.get("id") or ""
    prompt = payload.get("prompt") or payload.get("user_message") or prompt_arg

    if dry_run:
        ts = created_ms if created_ms is not None else int(datetime.now().timestamp() * 1000)
        print(make_title(prompt, ts))
        return
    hook_mode(session_id, prompt, created_ms)
    sys.exit(0)


if __name__ == "__main__":
    main()
