#!/usr/bin/env python3
# version: v0.6
"""session_title_namer.py — WorkBuddy 专属适配器：UserPromptSubmit 钩子新会话首轮自动命名对话标题。

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题
    日期 = 北京时区实际创建日期（取 sessions.created_at）
    类型 ∈ {功能,设计,修复,优化,发布,探索,文档,研究}（关键词启发式，默认=探索）
    主题 = 首条 prompt 简洁概括
    已有手动命名（custom_title 非本钩子格式）→ 永不覆盖。

v0.5（2026-09-29·你死命令「新任务对话后标题即按设定格式呈现，不重启」）:
    实锤：WB 新版 UI 标题读 sessions.title 列（宿主 AI 起名接管），
    custom_title 写了不上屏。修复=钩子接管 title 列+每轮守卫改回。

v0.6（2026-09-29·真机实锤补充）：宿主 AI 起名发生在钩子首轮写入之后
    几秒（实证 7b5abc5f：22:30:12 钩子写→宿主覆盖'关于小美的对话'），
    且宿主一个会话只起名一次、之后不再动 title（实证 61a2175a/990e342b
    守卫改回后长期稳住）。结论：UserPromptSubmit 同步写入必输（宿主后写赢）。
    修复=**后台夺回守卫**：钩子写完 title 后 spawn 脱离进程，每 3s 轮询
    title，被宿主覆盖→改回；连续 3 次检查（9s）稳定为钩子格式→胜利退出。
    窗口 2 分钟（覆盖宿主起名最慢情形）。期间你手动改名（custom_title
    非钩子格式）→ 立即停火。

原语来源（2026-09-10 抽公共）:
    classify / extract_theme / make_title / bj_date_from_ms 已抽至
    `<脚本中心>/session_title_utils.py`（跨工具中立·各端适配器共用·由 runtime_paths 的 script_center 键解析）。

数据链路:
    UserPromptSubmit 钩子 stdin JSON {session_id, prompt, ...}
    → 写 sessions.title + custom_title（NULL 守卫）→ 状态文件存首轮标题
    → spawn --guard-reclaim 后台进程（2 分钟窗口轮询夺回）

安全设计:
    - 任何异常 exit 0 静默降级——钩子绝不允许阻塞主流程（失败留痕 runtime.log）
    - 后台进程 start_new_session=True 脱离钩子父进程（钩子退出不牵连）
    - reclaim 窗口内二次触发不重复 spawn（状态文件 reclaim_until 时间戳）
    - custom_title UPDATE 带 `AND custom_title IS NULL` 守卫——不覆盖已有
    - title UPDATE 无守卫（显示位·本钩子职责即守卫它）但以格式签名自证
    - sqlite busy_timeout=5000 + WAL 并发安全

用法:
    echo '{"session_id":"<id>","prompt":"..."}' | python3 session_title_namer.py UserPromptSubmit   # 钩子模式
    python3 session_title_namer.py --dry-run --prompt "修复搜索超时问题" [--created-at-ms 1788952825816]  # 只看生成的标题不写库
    python3 session_title_namer.py --name-only --prompt "修复搜索超时问题" [--created-at-ms ...]   # 纯输出标题
    python3 session_title_namer.py --set <session_id> --title "260909 | 功能 | 对话标题命名"        # 手动/历史改名（同步写双列）
    python3 session_title_namer.py --guard-reclaim --session <id>   # 后台夺回（钩子自动 spawn·一般不手动跑）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import re
import subprocess
import sys
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from session_title_utils import make_title

DB_PATH = Path.home() / ".workbuddy" / "workbuddy.db"
STATE_DIR = Path.home() / ".workbuddy" / "cache" / "title-namer"
RUNTIME_LOG = STATE_DIR / "runtime.log"

# v0.5：本钩子产物的格式签名——title/custom_title 命中=钩子写的（守卫），
# 不命中=宿主/手动命名。宿主覆盖 title 后签名消失→守卫改回。
HOOK_TITLE_RE = re.compile(r"^\d{6} \| ")

# v0.6 后台夺回参数
RECLAIM_INTERVAL_S = 3      # 轮询间隔
RECLAIM_MAX_TICKS = 40      # 40×3s = 2 分钟窗口
RECLAIM_STABLE_TICKS = 3    # 连续 3 次稳定=胜利退出（9s）

# v0.2 修（2026-09-21，端实证）：模块级建目录——原实现中状态文件写入依赖
# log() 的 mkdir 副作用，但 named 分支 write_text 先于 log 执行 → STATE_DIR
# 不存在的新机器首跑必抛 FileNotFoundError → 防重入状态晚一轮才生效。
# 教训：初始化不可依赖他函数副作用（写入与建目录同层负责）。
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


def _connect():
    """统一连接入口（v0.3 修·260921 用户反馈排查）：docstring 原声称
    "busy_timeout=5000 + WAL 并发安全"但代码从未设 WAL——你本机库恰好
    由宿主建成 WAL 才即时可见；非 WAL 库跨进程写完宿主长连接可能读旧
    快照=用户端「每任务都需重启才见标题」的头号嫌疑。显式设 WAL（幂等：
    已 WAL 则 no-op；宿主忙导致设失败则静默降级，不阻塞钩子）。"""
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    try:
        con.execute("PRAGMA busy_timeout=5000")
        try:
            con.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass  # 设不了 WAL 不影响写入本身（守卫列仍在），可见性回退宿主行为
    except Exception:
        pass
    return con


def _to_ms(v) -> int:
    """created_at 跨版本归一化（v0.4 修·对抗审查发现）：本机 created_at=int 毫秒，
    但其他版本 WB 可能存秒级整数（→标题日期变 1970）或 ISO 字符串（→int() 抛
    异常→标题静默不写）。统一转 epoch ms；解析失败→0（上层回退当前时间）。"""
    try:
        if v is None:
            return 0
        if isinstance(v, (int, float)):
            n = float(v)
        else:
            s = str(v).strip()
            if not s:
                return 0
            try:
                n = float(s)
            except ValueError:
                from datetime import datetime as _dt
                n = _dt.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000
        return int(n if n > 1e11 else n * 1000)  # 秒级(<1e11)→毫秒
    except Exception:
        return 0


def get_session(session_id: str):
    con = _connect()
    try:
        row = con.execute(
            "SELECT custom_title, created_at, title FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
    finally:
        con.close()
    return row


def set_custom_title(session_id: str, title: str, force: bool = False) -> bool:
    """写 custom_title。force=False（钩子自动命名）=带 `custom_title IS NULL` 守卫，
    永不覆盖已有；force=True（--set 手动/历史改名通道）=允许覆盖。"""
    con = _connect()
    try:
        sql = ("UPDATE sessions SET custom_title=? WHERE id=?" if force
               else "UPDATE sessions SET custom_title=? WHERE id=? AND custom_title IS NULL")
        cur = con.execute(sql, (title, session_id))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def set_title(session_id: str, title: str) -> bool:
    """v0.5：写 title 列（UI 消费位·无条件）。这是显示位不是存档位，
    宿主 AI 起名覆盖后由下一轮钩子守卫改回——显示权争夺的最终裁判=格式签名。"""
    con = _connect()
    try:
        cur = con.execute("UPDATE sessions SET title=? WHERE id=?", (title, session_id))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def _read_state(session_id: str) -> dict:
    try:
        return json.loads((STATE_DIR / f"{session_id}.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(session_id: str, data: dict) -> None:
    try:
        (STATE_DIR / f"{session_id}.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass  # 状态文件写失败不影响本轮命名，下一轮重试


def spawn_reclaim(session_id: str) -> None:
    """v0.6：spawn 脱离父进程的后台夺回守卫。窗口内已有守卫（reclaim_until
    未过期）则跳过——防止同会话多实例重复轮询。"""
    state = _read_state(session_id)
    now = time.time()
    if state.get("reclaim_until", 0) > now:
        log(f"reclaim skip: already guarding sid={session_id}")
        return
    _write_state(session_id, {
        **state,
        "reclaim_until": now + RECLAIM_MAX_TICKS * RECLAIM_INTERVAL_S + 10,
    })
    try:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()),
             "--guard-reclaim", "--session", session_id],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )
        log(f"reclaim spawned sid={session_id}")
    except Exception as e:
        log(f"reclaim spawn failed sid={session_id}: {type(e).__name__}: {e}")


def guard_reclaim(session_id: str) -> None:
    """v0.6 后台夺回守卫（独立进程运行·不在钩子关键路径上）：
    每 3s 查 title——被宿主覆盖→用状态文件里的首轮标题改回；
    连续 3 次稳定为钩子格式→胜利退出；你手动命名→立即停火。
    任何写失败继续轮询（静默降级），窗口结束自然退出。"""
    state = _read_state(session_id)
    title_wanted = state.get("title")
    if not title_wanted:
        log(f"reclaim abort: no stored title sid={session_id}")
        return
    stable = 0
    for _ in range(RECLAIM_MAX_TICKS):
        time.sleep(RECLAIM_INTERVAL_S)
        try:
            row = get_session(session_id)
            if row is None:
                return  # 会话没了（删除/异常）→ 退出
            custom_title, _, db_title = row
            if db_title and HOOK_TITLE_RE.match(db_title):
                stable += 1
                if stable >= RECLAIM_STABLE_TICKS:
                    log(f"reclaim stable sid={session_id} title={db_title!r}")
                    return
                continue
            stable = 0
            # 你手动命名（custom_title 非钩子格式且非空）→ 停火
            if custom_title and not HOOK_TITLE_RE.match(custom_title):
                log(f"reclaim stop: manual naming detected sid={session_id}")
                return
            if set_title(session_id, title_wanted):
                log(f"reclaimed sid={session_id} title={title_wanted!r}")
        except Exception as e:
            log(f"reclaim error sid={session_id}: {type(e).__name__}: {e}")
    log(f"reclaim window closed sid={session_id}")


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

    try:
        row = get_session(session_id)
        if row is None:
            # v0.5：不在库中不再写 not_in_db 状态文件——旧版写了状态文件导致
            # 宿主延迟入库时永久放弃（首轮 not_in_db → 防重入短路全部后续轮）。
            log(f"skip: session not in db sid={session_id}")
            return
        custom_title, created_ms, db_title = row

        # 手动命名判定（v0.5）：custom_title 存在且非本钩子格式 → 你手动命名，
        # title 一起放手。
        if custom_title and not HOOK_TITLE_RE.match(custom_title):
            log(f"skip: manual custom_title sid={session_id}")
            return

        # 守卫判定：title 已是本钩子格式 → 合规，只补漏（custom_title 空则补写留档）
        state = _read_state(session_id)
        if db_title and HOOK_TITLE_RE.match(db_title):
            if not custom_title and state.get("title"):
                set_custom_title(session_id, state["title"])
            if not state.get("title"):
                _write_state(session_id, {"status": "named", "title": db_title})
            return  # 已合规，静默退出

        # 需要写：优先用状态文件里存的首轮标题（生成一次·格式稳定不漂），
        # 无存档才用本条 prompt 生成（fallback：宿主延迟入库等场景）
        title = state.get("title") or make_title(
            prompt, _to_ms(created_ms) or int(datetime.now().timestamp() * 1000)
        )
        set_custom_title(session_id, title)  # NULL 守卫·覆盖已有=no-op
        ok = set_title(session_id, title)
        _write_state(session_id, {"status": "named", "title": title})
        if ok:
            log(f"guarded sid={session_id} title={title!r} (state={'reused' if state.get('title') else 'fresh'})")
            # v0.6：宿主 AI 起名在本写入之后几秒到达（真机实证）——同步写入
            # 必被覆盖，spawn 后台守卫在宿主起名完成后夺回。
            spawn_reclaim(session_id)
        else:
            log(f"skip: title update no-op sid={session_id}")
    except Exception as e:  # 钩子永不阻塞主流程
        log(f"error sid={session_id}: {type(e).__name__}: {e}")
    sys.exit(0)


def main() -> None:
    # v0.4 修（对抗审查）：Windows 管道默认 GBK——print 中文标题会
    # UnicodeEncodeError。强制 UTF-8 输出（旧 Python 无此方法则忽略）。
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = sys.argv[1:]
    if args and args[0] == "--guard-reclaim":
        # v0.6 后台夺回守卫（钩子自动 spawn·独立进程）
        sid = ""
        i = 1
        while i < len(args):
            if args[i] == "--session":
                sid = args[i + 1]
                i += 2
            else:
                i += 1
        if sid:
            guard_reclaim(sid)
        return
    if args and args[0] == "--dry-run":
        prompt, created_ms = "", int(datetime.now().timestamp() * 1000)
        i = 1
        while i < len(args):
            if args[i] == "--prompt":
                prompt = args[i + 1]
                i += 2
            elif args[i] == "--created-at-ms":
                created_ms = _to_ms(args[i + 1])
                i += 2
            else:
                i += 1
        print(make_title(prompt, created_ms))
        return
    if args and args[0] == "--name-only":
        # 纯输出模式（2026-09-10 新增·供其他端适配器调用·不写 WB 库）：
        #   --prompt <首条消息> [--created-at-ms <epoch ms>] → stdout 打印 "YYMMDD | 类型 | 主题"
        prompt, created_ms = "", int(datetime.now().timestamp() * 1000)
        i = 1
        while i < len(args):
            if args[i] == "--prompt":
                prompt = args[i + 1]
                i += 2
            elif args[i] == "--created-at-ms":
                created_ms = _to_ms(args[i + 1])
                i += 2
            else:
                i += 1
        print(make_title(prompt, created_ms))
        return
    if args and args[0] == "--set":
        # 手动/历史改名通道：--set <session_id> --title "..."（force 覆盖 custom_title）
        # v0.5：同步写 title 列——UI 读 title，只写 custom_title 不上屏。
        sid, title = args[1], ""
        i = 2
        while i < len(args):
            if args[i] == "--title":
                title = args[i + 1]
                i += 2
            else:
                i += 1
        ok = set_custom_title(sid, title, force=True)
        ok_title = set_title(sid, title)
        print(f"{'OK' if ok else 'SKIP(会话不存在)'}: {sid} -> {title!r} (title_col={'OK' if ok_title else 'FAIL'})")
        log(f"manual-set sid={sid} ok={ok} title_col={ok_title} title={title!r}")
        return
    hook_mode()


if __name__ == "__main__":
    main()
