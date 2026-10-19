#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/qodercn_title_namer.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# version: v0.2
"""qodercn_title_namer.py — Qoder CN 专属适配器：UserPromptSubmit 钩子新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题（原语来自 session_title_utils.py·跨工具中立·与 WB/DSH/ZCode 同源）

落库目标（Qoder CN 无会话库·标题走 transcript JSONL 记录·落点实测 2026-09-20）:
    ~/.qoder-cn/projects/<cwd_slug>/<session_id>.jsonl 追加一行
    {"type":"custom-title","sessionId":...,"customTitle":...,"timestamp":"<ISO Z>"}
    （现存 3 会话 67 条产品写入记录·active-leaf 反复引用=UI 显示源；存量记录 64/67 无
     timestamp 字段，本适配器统一带 ISO 时间戳——产品对两种格式均有写入先例）

数据链路:
    Qoder CN UserPromptSubmit 钩子 stdin JSON {session_id, prompt, cwd, ...}
    → 定位 transcript（cwd → slug → projects/<slug>/<session_id>.jsonl）
    → 守卫通过 → 追加标题记录 → 状态文件防重入

守卫（zcode 语义对齐·落点形态不同）:
    - transcript 已存在任何 custom-title 记录 → 跳过并写状态文件
      （本端 custom-title 无 title_source 字段，"已有即尊重"=你手动命名/产品已命名都不碰）
    - transcript 不存在（首轮 UPS 竞态）→ 不写状态文件，下轮 prompt 重试

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 runtime.log）
    - stdout 零输出（本端产品把 UPS stdout 按 JSON 解析，本钩子纯副作用型不注入上下文）
    - 追加时 fcntl.flock 排它锁（产品与钩子并发 append 活 jsonl 的原子性兜底）

用法:
    echo '{"session_id":"<uuid>","prompt":"...","cwd":"/path"}' | python3 qodercn_title_namer.py UserPromptSubmit --hook-protocol=json
    python3 qodercn_title_namer.py --dry-run --prompt "修复搜索超时问题" [--created-at-ms ...]
    python3 qodercn_title_namer.py --force --session-id <uuid> --cwd <path> --prompt "..."   # 测试用·绕过已有标题守卫
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import json
import re
import sys
try:
    import fcntl          # Unix/macOS：标题写入串行化
except ImportError:
    # Windows 无 fcntl——本件随发布包装进 Windows 端（Loop判据[跨平台适配]P1红实证:
    # 顶层裸 import 在 Win 直接 ImportError=标题钩子全灭）。降级守设计律②
    # 「降级不阻塞」：锁变 no-op，文件读写仍可跑（并发撕裂风险如实承认，不假装锁还在）。
    # 同型先例=audit_search_kb.py / build_kb_vectors / transcript_reader 三处。
    class _NoFcntl:
        LOCK_EX = LOCK_UN = LOCK_NB = 0

        @staticmethod
        def flock(fh, op):
            return None
    fcntl = _NoFcntl()
from datetime import datetime, timezone
from pathlib import Path

from session_title_utils import make_title

CN_HOME = Path.home() / ".qoder-cn"
PROJECTS_DIR = CN_HOME / "projects"
STATE_DIR = CN_HOME / "cache" / "title-namer"
RUNTIME_LOG = STATE_DIR / "runtime.log"

# v0.2 修（2026-09-21，WB 端同款根治）：模块级建目录——状态文件写入不能依赖
# log() 顺带建目录的副作用，否则目录不存在的新机器首跑（named 分支先写后 log）
# 状态文件落盘失败、防重入晚一轮才生效。
try:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # 建不了目录时各写入点自带 try/except 兜底，钩子永不阻塞主流程


def log(msg: str) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(RUNTIME_LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def clean_prompt(prompt: str) -> str:
    """去前导序号（"1、xxx"/"2. xxx"）——utils.extract_theme 在首个顿号截断，
    带序号 prompt 的主题会退化成纯序号（实测 2026-09-20："1、你有挂任务标题…"
    → 主题="1"）。utils 是 SSOT 原语（接入=调用不=改写·改动影响 WB/ZCode），
    故清洗放本端调用侧。⚠️ 本端与 WB/ZCode 对带序号 prompt 的主题可能不一致。"""
    return re.sub(r"^\s*\d+\s*[、.．,)）]\s*", "", prompt)


def cwd_to_slug(cwd: str) -> str:
    """workspace cwd → projects 目录 slug。实测：~/qoder-cn-work
    → -Users-用户名-qoder-cn-work（即 path.replace('/', '-')）。"""
    return str(cwd).replace("/", "-")


def find_transcript(session_id: str, cwd: str):
    """双形态定位（2026-09-22·跨版本数据形态归一·WB v1.3.69 教训②本端落地）：
    老版产品落 <slug>/<sid>.jsonl；新版 task 会话落 <slug>/transcript/<sid>.jsonl。
    实锤病：只认老形态导致 09-21 起 82 轮 skip: transcript not found yet（注册态≠派发态）。"""
    root = PROJECTS_DIR / cwd_to_slug(cwd)
    for cand in (root / f"{session_id}.jsonl", root / "transcript" / f"{session_id}.jsonl"):
        if cand.is_file():
            return cand
    return None


def transcript_created_ms(p: Path) -> int:
    """首行 runtime-config 的 epoch ms → 会话创建时间（标题日期取它）。读不到回退 0。"""
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                ts = d.get("timestamp")
                if isinstance(ts, (int, float)):
                    return int(ts)
    except Exception:
        pass
    return 0


def existing_title(p: Path) -> str:
    """transcript 中最后一条 custom-title 的标题（无则空串）。逐行流式扫描防大文件。"""
    found = ""
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if '"type":"custom-title"' in line:
                    try:
                        d = json.loads(line)
                        if d.get("type") == "custom-title":
                            found = str(d.get("customTitle", "")).strip()
                    except Exception:
                        continue
    except Exception:
        pass
    return found


def append_title(p: Path, session_id: str, title: str) -> None:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    record = {
        "type": "custom-title",
        "sessionId": session_id,
        "customTitle": title,
        "timestamp": ts,
    }
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(line)
            f.flush()
            import os
            os.fsync(f.fileno())
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def hook_mode() -> None:
    try:
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        payload = {}
    session_id = str(payload.get("session_id", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    cwd = str(payload.get("cwd", "")).strip()
    if not session_id or not prompt or not cwd:
        log(f"skip: missing sid/prompt/cwd (sid={session_id!r} cwd={cwd!r})")
        return
    if "subagent" in session_id:
        return
    prompt = clean_prompt(prompt)

    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        return

    try:
        transcript = find_transcript(session_id, cwd)
        if transcript is None:
            log(f"skip: transcript not found yet sid={session_id} cwd={cwd}")
            return
        prev = existing_title(transcript)
        if prev:
            state_file.write_text(json.dumps({"status": "existing_title", "title": prev}, ensure_ascii=False))
            log(f"skip: existing custom title {prev!r} sid={session_id}")
            return
        created_ms = transcript_created_ms(transcript) or int(datetime.now().timestamp() * 1000)
        title = make_title(prompt, created_ms)
        append_title(transcript, session_id, title)
        state_file.write_text(json.dumps({"status": "named", "title": title}, ensure_ascii=False))
        log(f"named sid={session_id} title={title!r}")
    except Exception as e:
        log(f"error sid={session_id}: {type(e).__name__}: {e}")
    sys.exit(0)


def _parse_kv(args, i, key):
    return args[i + 1], i + 2


def manual_mode(args) -> None:
    """--dry-run 只算不写 / --force 绕过已有标题守卫强写（测试用）"""
    prompt, session_id, cwd = "", "", ""
    created_ms = int(datetime.now().timestamp() * 1000)
    force = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--prompt":
            prompt, i = _parse_kv(args, i, a)
        elif a == "--created-at-ms":
            created_ms, i = _parse_kv(args, i, a)
            created_ms = int(created_ms)
        elif a == "--session-id":
            session_id, i = _parse_kv(args, i, a)
        elif a == "--cwd":
            cwd, i = _parse_kv(args, i, a)
        elif a == "--force":
            force = True
            i += 1
        else:
            i += 1
    if not prompt:
        print("ERROR: --prompt required", file=sys.stderr)
        sys.exit(2)
    title = make_title(clean_prompt(prompt), created_ms)
    if not force:
        print(title)
        return
    if not session_id or not cwd:
        print("ERROR: --force requires --session-id and --cwd", file=sys.stderr)
        sys.exit(2)
    transcript = find_transcript(session_id, cwd)
    if transcript is None:
        print(f"ERROR: transcript not found: {PROJECTS_DIR / cwd_to_slug(cwd) / (session_id + '.jsonl')}", file=sys.stderr)
        sys.exit(2)
    append_title(transcript, session_id, title)
    log(f"forced sid={session_id} title={title!r}")
    print(title)


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("--dry-run", "--force"):
        manual_mode(args)
        return
    hook_mode()


if __name__ == "__main__":
    main()
