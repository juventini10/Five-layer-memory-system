#!/usr/bin/env python3
# version: v0.1
"""dsh_title_namer.py — DeepSeek Harness 专属适配器：新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题（原语来自 session_title_utils.py·跨工具中立·与 WB 同源）

落库目标（你拍板 2026-09-10·DSH 无 workbuddy.db sessions.custom_title）:
    ~/.dsh/session-titles.jsonl —— append 一行 {"uuid","title","created_at","at"}。
    只写新会话首轮（防重入 state 文件 ~/.dsh/cache/title-namer/<uuid>.json）。
    ⚠️ 纯索引文件，⛔DO NOT 改 DSH 会话存储本体（session.jsonl.zstd 是宿主私有格式）。

数据链路:
    DSH 插件 pre-step 管道（agent/pre-step ≈ UserPromptSubmit）:
        python3 dsh_title_namer.py --prompt <首条消息> [--created-at-ms <epoch ms>]
    → 定位最新会话目录 uuid（与插件 findLatestSessionJsonl 同构：扫 $DSH_HOME/sessions 按 mtime）
    → 首轮（state 文件不存在）→ 生成标题 → append 到 session-titles.jsonl + 写 state

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 stderr）
    - 已有 state 文件 → 跳过（防重入·对齐 WB）
    - 找不到会话目录 / 无 session.jsonl.zstd → 跳过不猜（fail-open to no-rename）

用法:
    python3 dsh_title_namer.py --prompt "修复搜索超时问题"                     # 钩子模式（pre-step 调用）
    python3 dsh_title_namer.py --dry-run --prompt "修复搜索超时问题"          # 只看生成的标题不写
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

DSH_HOME = Path(os.environ.get("DSH_HOME", Path.home() / ".dsh"))
SESSIONS_ROOT = DSH_HOME / "sessions"
TITLES_FILE = DSH_HOME / "session-titles.jsonl"
STATE_DIR = DSH_HOME / "cache" / "title-namer"


def find_latest_session_uuid() -> str | None:
    """与插件 findLatestSessionJsonl 同构：扫 sessions 按 mtime 取最新会话文件的目录 uuid。

    ⚠️ 2026-08-14 真机教训（插件注释同源）：不能用环境变量拿会话 id——agent 请求级变量
    宿主进程不可见；改扫目录按 mtime（刚结束回合的会话必然最新写入）。

    ⚠️ 2026-09-10 两处真机根治（第一版因假设错误永不产出，实测"未找到会话目录，跳过"）：
      ① **目录层级**：真实结构是 `sessions/<workspace>/<session-<uuid>>/<file>`
         （workspace 形如 `--Users-用户名--`）——只迭代一层会漏掉全部会话；
         ⛔隔离测试的目录结构必须与真实一致（本 bug 正因首版隔离测试用了一层结构而未抓到）。
      ② **文件形态**：`session.jsonl.zstd`（迁移前）与 `session.v3.jsonl.zstd`（迁移后·当前活跃）
         并存——只认前者同样找不到。
    """
    best = None
    best_mtime = -1.0
    if not SESSIONS_ROOT.is_dir():
        return None
    # 两层 glob：workspace 目录 / session 目录 / 会话文件（.bak-* 备份不以 .zstd 结尾·天然排除）
    for z in SESSIONS_ROOT.glob("*/*/session*.jsonl.zstd"):
        if not z.is_file():
            continue
        m = z.stat().st_mtime
        if m > best_mtime:
            best_mtime = m
            best = z.parent.name  # session-<uuid>
    if not best:
        return None
    # 目录名形如 session-<uuid> → 取 uuid 段；取不到就用目录名
    return best.removeprefix("session-") if best.startswith("session-") else best


def already_named(uuid: str) -> bool:
    return (STATE_DIR / f"{uuid}.json").exists()


def mark_named(uuid: str, title: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{uuid}.json").write_text(
            json.dumps({"status": "named", "title": title, "at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def append_title(uuid: str, title: str, created_ms: int) -> None:
    """append 落库（O_APPEND 原子性·并发安全·对齐铁律-014 ②）。"""
    try:
        TITLES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TITLES_FILE, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"uuid": uuid, "title": title, "created_at_ms": created_ms, "at": datetime.now().isoformat(timespec="seconds")},
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception as e:
        sys.stderr.write(f"dsh_title_namer: append 失败 {type(e).__name__}: {e}\n")


def hook_mode(prompt: str, created_ms: int | None) -> None:
    if not prompt.strip():
        return
    uuid = find_latest_session_uuid()
    if not uuid:
        sys.stderr.write("dsh_title_namer: 未找到会话目录，跳过\n")
        return
    if already_named(uuid):
        return  # 防重入
    ts = created_ms if created_ms is not None else int(datetime.now().timestamp() * 1000)
    title = make_title(prompt, ts)
    append_title(uuid, title, ts)
    mark_named(uuid, title)


def main() -> None:
    args = sys.argv[1:]
    prompt, created_ms, dry_run = "", None, False
    i = 0
    while i < len(args):
        if args[i] == "--prompt":
            prompt = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif args[i] == "--created-at-ms":
            created_ms = int(args[i + 1])
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1
    if dry_run:
        # dry-run：只打印标题，不写任何文件（参数先全解析，再输出）
        ts = created_ms if created_ms is not None else int(datetime.now().timestamp() * 1000)
        print(make_title(prompt, ts))
        return
    hook_mode(prompt, created_ms)
    sys.exit(0)


if __name__ == "__main__":
    main()
