#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v0.1
"""dsh_session_title_batch.py — DSH 历史会话标题批量统一命名（对齐 WB session_title_batch_rename.py）

机制（真相源=DSH 源码 `dsh-session-title/lib/index.js`）
------------------------------------------------------
· 标题载体 = 会话事件流中的 `session/title` 事件（投影规则：取**最后一条**）
· `source.kind` 合法值 = fallback | provider | plugin | **user**
  → 本工具用 `kind:"user"`（源码注释原文："user rename superseded automatic title generation"）
  → 即 DSH 官方「用户手动改名」语义 = 权威、且会压制自动生成
· ⛔ 本工具**不碰** DSH 自带 LLM 标题的生成逻辑，只追加一条 user 源 title（幂等·已有则不覆盖）

用法
----
  python3 dsh_session_title_batch.py --scan              # 列出全部会话 + 将生成的标题（dry）
  python3 dsh_session_title_batch.py --apply [--session <uuid>]  # 落盘（单个或全部）
  python3 dsh_session_title_batch.py --apply --force     # 覆盖已有 user 源标题（重刷）
  python3 dsh_session_title_batch.py --verify <file>     # 校验单会话事件流形状

安全
----
① 备份 `<file>.bak-<ts>-prerename` ② 原子替换 ③ 改后自校验（可解压+事件形状合规）
④ 只追加 1 条 title 事件，⛔不动既有事件 ⑤ 宿主正写该文件时跳过（不硬改）
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from session_title_utils import make_title  # noqa: E402
from dsh_session_repair import compress as _shared_compress, assert_frame_contract  # noqa: E402

ROOT_DEFAULT = os.path.expanduser("~/.dsh/sessions")
MESSAGE_ROLE_BY_TYPE = {
    "system/message": "system",
    "user/message": "user",
    "assistant/message": "assistant",
    "tool/result": "user",
}


def session_files(root):
    """全部会话文件（含同目录多格式）。"""
    return sorted(
        p for p in glob.glob(os.path.join(root, "*", "*", "session*.jsonl.zstd"))
        if ".bak-" not in p
    )


def target_files(root):
    """按会话目录分组，每目录只取 **mtime 最新** 的会话文件。

    ⚠️ 2026-09-10：同一会话目录常见两个文件并存——`session.jsonl.zstd`（迁移前）与
    `session.v3.jsonl.zstd`（当前活跃）。DSH 实际读最新写入者 → 只改它，⛔不两个都改
    （改非活跃副本无意义且徒增风险）。
    """
    best = {}
    for p in session_files(root):
        d = os.path.dirname(p)
        m = os.path.getmtime(p)
        if d not in best or m > best[d][1]:
            best[d] = (p, m)
    return sorted(v[0] for v in best.values())


def decompress(path):
    r = subprocess.run(["zstd", "-d", "-c", path], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"zstd 解压失败: {r.stderr.decode(errors='replace')[:120]}")
    return r.stdout


# ⚠️ 2026-09-10 三次事故根治 —— 帧契约（⛔本文件不得再自写压缩实现）
# DSH 加载器 dsh-session-persistence-jsonl 的 assertZstdHeaderFrame 要求：
#   **第一个 zstd 帧必须恰好只含 header 那一行**（plaintext.indexOf(10) === plaintext.length-1）
# 本文件早期用 `zstd -q -o` 整文件压成单帧 → 首帧含全部事件
#   → 抛 "first frame is not exactly one header line" → 整个 session/list 失败
#   → 侧栏只剩当前会话（2026-09-10 18:37 起由 session-patrol 每 15min 触发全量复发）
# 教训：压缩实现只允许存在一份（dsh_session_repair.compress = 逐行成帧），
#       两处各写一份 = 一处修了另一处漏 = 复发（本文件即复发源）。故改为 import 共用。
compress = _shared_compress


def load_events(path):
    return [json.loads(l) for l in decompress(path).splitlines() if l.strip()]


def serialize(events):
    return ("\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n").encode()


def first_user_prompt(events):
    """首条真实用户消息（⛔排除 plugin/agent-instructions 等注入）。"""
    for e in events:
        if e.get("type") != "user/message":
            continue
        d = e.get("data") or {}
        src = d.get("source") or {}
        if src.get("kind") != "user":
            continue
        txt = "".join(
            c.get("text", "") for c in (d.get("content") or []) if isinstance(c, dict)
        ).strip()
        if txt:
            return txt, e.get("seq"), e.get("time")
    return None, None, None


def has_user_title(events):
    """当前**生效**的标题是否为 user 源（⛔不是"历史上有没有过"）。

    ⚠️ 2026-09-10 三次事故修正：DSH 标题投影 = `events.findLast(session/title)` ——
    **只认最后一条**（dsh-session-title/lib/index.js·foldSessionTitle）。
    原实现遍历取"第一个 user title"就返回 → 若其后又被追加了自动标题事件
    （宿主用内存视图覆盖外部改动时会发生），则投影实际显示的是**自动标题**，
    而本函数仍报"已有 user 标题"→ 跳过 → 标题永远修不回来（虚绿）。
    实证：612cb454 / d54d0a56 两个会话即为此形态。
    """
    last = None
    for e in events:
        if e.get("type") == "session/title":
            last = e
    if last is None:
        return None
    d = last.get("data") or {}
    if (d.get("source") or {}).get("kind") != "user":
        return None
    return d.get("title")


def plan_for(path):
    events = load_events(path)
    uuid = os.path.basename(os.path.dirname(path))
    prompt, pseq, ptime = first_user_prompt(events)
    existing = has_user_title(events)
    title = None
    if prompt:
        title = make_title(prompt, int(ptime or time.time() * 1000))
    return {
        "path": path,
        "uuid": uuid,
        "events": len(events),
        "prompt": (prompt or "")[:40],
        "first_seq": pseq,
        "first_time": ptime,
        "existing_user_title": existing,
        "title": title,
    }


CACHE_DIR = os.path.expanduser("~/.dsh/storages/session_projcache/sessions")


def sync_cache(uuid, title):
    """同步投影缓存 title.val —— 侧栏显示读这里（事件流是权威源·缓存是派生快照）。

    ⚠️ 2026-09-10 实证：只写事件流时侧栏**不变**（缓存未重算）→ 必须双写：
      事件流（持久·DSH 重算时的真源）+ 投影缓存（立即显示）。
    ⛔ 只改 rows.title.val，不动 ver/seq 与其它行（避免与宿主投影逻辑冲突）。
    """
    cands = glob.glob(os.path.join(CACHE_DIR, f"*{uuid}*.json"))
    if not cands:
        return "no-cache"
    p = cands[0]
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return "cache-unreadable"
    rows = (d.get("record") or {}).get("rows")
    if not isinstance(rows, dict):
        return "no-rows"
    t = rows.get("title")
    if not isinstance(t, dict):
        return "no-title"
    if t.get("val") == title:
        return "cache-same"
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    subprocess.run(["cp", p, f"{p}.bak-{ts}-prerename"], check=False)
    t["val"] = title
    tmp = f"{p}.tmp-{ts}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, p)
    return "cache-synced"


def cmd_scan(root):
    rows = []
    for p in target_files(root):
        try:
            rows.append(plan_for(p))
        except Exception as e:
            print(f"  [skip] {p}: {e}")
    print(f"共 {len(rows)} 个会话：\n")
    n_new = n_has = n_skip = 0
    for r in rows:
        if not r["title"]:
            n_skip += 1
            state = "⚠️ 无可用首条消息"
        elif r["existing_user_title"]:
            n_has += 1
            state = f"已有 user 标题：{r['existing_user_title']}"
        else:
            n_new += 1
            state = "待命名"
        print(f"  [{state}] {r['uuid'][:20]:22} {r['title'] or '-'}")
    print(f"\n待命名 {n_new} · 已有 user 标题 {n_has} · 不可命名 {n_skip}")
    return 0


def host_running(port: int = 3080) -> bool:
    """DSH web 是否在监听（= 宿主活着）。用于阻止"宿主运行时改活跃会话事件流"。

    ⚠️ 2026-09-10 五次事故（"历史加载失败：has seq gap"）根因：
      宿主用**内存里的 seq 计数器**追加事件；外部脚本用 `max(seq)+1` 追加 title。
      两者各算各的 → 同一 seq 被写两次 → DSH 报 `expected X, got X-1` → 会话加载失败。
      ⛔ 因此在宿主运行时，**活跃会话的事件流绝不可由外部写入**——不是"写了无效"，
         而是"写了就制造损坏"（实证 b1810d3b 修完即被 DSH 追上再撞号）。
    """
    try:
        r = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
                           capture_output=True)
        return bool(r.stdout.strip())
    except Exception:
        return False


def apply_one(path, force=False, dry=False, guard_secs=300, ignore_lock=False):
    # 离线模式（--ignore-lock·2026-09-10 新增）：**宿主已停**时使用。
    #   语义前提：DSH web 已停止 → 无内存状态 → 不存在"改了被覆盖"的问题
    #   → lock 残留与 mtime 新都不能作为活跃判据，须一并忽略。
    #   ⛔ 仅限停服后调用；宿主运行中使用 = 白改（会被内存视图覆盖）。
    # 活跃保护（2026-09-10）：宿主可能正在写该会话文件 → os.replace 会与写入竞争。
    #   guard_secs 内有写入 = 视为活跃，跳过（下次巡逻/手动再处理），⛔不硬改。
    # ⚠️ 2026-09-10 二次加固 —— **session.lock 才是权威活跃判据**：
    #   宿主把已加载会话的状态持有在**内存**里，外部改文件会被它的内存视图覆盖
    #   → 改了也**不生效**（实证：10 个 lock 会话标题全无效，未 lock 的 36 个全生效）。
    #   lock 存在 = 宿主占用中 → 跳过（force 也不例外：硬改等于白改+引入竞争）。
    if not ignore_lock:
        if os.path.exists(os.path.join(os.path.dirname(path), "session.lock")):
            return "skip-locked", None
        if guard_secs and (time.time() - os.path.getmtime(path)) < guard_secs:
            return "skip-active", None
    elif host_running():
        # 🔴 硬门禁（2026-09-10 五次事故·物理拦截）：--ignore-lock 只允许在**宿主已停**时用。
        #   宿主在跑 → 活跃会话的写入会与 DSH 的内存 seq 计数器撞号 → 会话损坏（非仅无效）。
        #   ⛔ 不接受任何"就这一次"的绕过——损坏是静默的，加载时才暴露。
        return "skip-host-running", None
    events = load_events(path)
    uuid = os.path.basename(os.path.dirname(path))
    existing = has_user_title(events)
    if existing and not force:
        # ⚠️ 2026-09-10 四次事故补：**"事件流已就绪" ≠ "界面已生效"**。
        #   投影缓存 projcache 是侧栏的直接数据源，宿主回写会把它覆盖回旧标题
        #   （实证 a68dccc1/dab686c7：事件流最后一条已是 user title，缓存却仍是 provider 标题）。
        #   原实现在此直接 return → 缓存永远修不回来 = 文件对了界面还错（虚绿）。
        #   → 跳过前先同步缓存（幂等：已一致则 no-op）。
        sync_cache(uuid, existing)
        return "skip-has-title", existing
    prompt, pseq, ptime = first_user_prompt(events)
    if not prompt:
        return "skip-no-prompt", None
    title = make_title(prompt, int(ptime or time.time() * 1000))
    if existing == title and not force:
        return "skip-same", title
    if dry:
        return "would-apply", title
    last_seq = max((e.get("seq") or 0) for e in events)
    events.append({
        "type": "session/title",
        "seq": last_seq + 1,
        "time": int(time.time() * 1000),
        "data": {"title": title, "messageSeqs": [], "source": {"kind": "user"}},
    })
    data = serialize(events)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak-{ts}-prerename"
    subprocess.run(["cp", path, backup], check=True)
    tmp = f"{path}.tmp-{ts}"
    compress(data, tmp)
    # 自校验：可解压 + 最后一条是 user title + **帧契约合规**
    # ⚠️ 帧契约门禁（2026-09-10 三次事故后加）：原回验只查内容不查帧结构，
    #   而帧结构一旦不合规 = DSH 整个 session/list 加载失败 = 侧栏全空。
    #   内容对 ≠ 能加载 —— 两者都要验，且都在落盘前（物理拦截）。
    chk = load_events(tmp)
    ok = chk[-1].get("type") == "session/title" and \
        ((chk[-1].get("data") or {}).get("source") or {}).get("kind") == "user"
    if not ok:
        os.remove(tmp)
        return "fail-verify", None
    try:
        assert_frame_contract(tmp)
    except RuntimeError as e:
        os.remove(tmp)
        return f"fail-frame({e})", None
    os.replace(tmp, path)
    sync_cache(uuid, title)
    return "applied", title


def cmd_apply(root, session=None, force=False, dry=False, ignore_lock=False):
    targets = target_files(root)
    if session:
        targets = [p for p in targets if session in p]
        if not targets:
            print(f"未找到会话 {session}")
            return 1
    stats = {}
    for p in targets:
        try:
            r, t = apply_one(p, force=force, dry=dry, ignore_lock=ignore_lock)
        except Exception as e:
            r, t = f"error:{type(e).__name__}", str(e)[:60]
        stats[r] = stats.get(r, 0) + 1
        if r in ("applied", "would-apply"):
            print(f"  ✅ {os.path.basename(os.path.dirname(p))[:20]:22} → {t}")
        elif r.startswith("error"):
            print(f"  ❌ {os.path.basename(os.path.dirname(p))[:20]:22} {t}")
    print("\n统计：", ", ".join(f"{k}={v}" for k, v in stats.items()))
    return 0


def resolve_target(arg):
    """把 --verify 的参数解析为**该会话目录下 mtime 最新**的会话文件（与批量改写口径一致）。

    ⚠️ 2026-09-10 教训：同目录并存 v3 与旧格式文件，直接 glob 第一个会验到**未被改写的那个**
    → 虚警"标题没生效"。验证必须针对被改写的同一文件。
    """
    if os.path.isfile(arg):
        return arg
    cands = [p for p in session_files(ROOT_DEFAULT) if arg in p]
    if not cands and os.path.isdir(arg):
        cands = [p for p in session_files(ROOT_DEFAULT) if os.path.dirname(p) == arg.rstrip("/")]
    if not cands:
        return arg
    return max(cands, key=os.path.getmtime)


def cmd_title_for(uuid: str) -> int:
    """**只产出**该会话应有的标题文本（⛔不写任何文件）——供 DSH 插件调官方 rename。

    为什么需要这个模式（2026-09-10 第一性原理裁定）：
      WB 的 hook 能自动改标题，是因为它跑在宿主进程内、走官方改名接口；
      DSH 的等价通道 = 插件里的 `ctx.sessionTitle.rename(session, title)`。
      ⛔ 插件绝不能自己改文件（那是"进程外改文件"= 与宿主内存态抢写 = 今日全部事故根源）。
      → 本脚本在此退化为**纯标题计算器**：只输出文本，写入交给宿主的 rename 接口。

    stdout: 一行标题（已有合规 user 标题则原样返回·幂等）
    返回码: 0=有可用标题 / 1=无标题可生成
    """
    cands = [p for p in target_files(ROOT_DEFAULT) if uuid in p]
    if not cands:
        return 1
    events = load_events(cands[0])
    existing = has_user_title(events)
    if existing:
        print(existing)
        return 0
    prompt, pseq, ptime = first_user_prompt(events)
    if not prompt:
        return 1
    print(make_title(prompt, int(ptime or time.time() * 1000)))
    return 0


def cmd_verify(path):
    path = resolve_target(path)
    evs = load_events(path)
    bad = []
    for e in evs:
        t = e.get("type")
        if t not in MESSAGE_ROLE_BY_TYPE:
            continue
        d = e.get("data") or {}
        msg = d if t == "user/message" else (d.get("message") or {})
        if isinstance(msg, dict) and msg.get("role") != MESSAGE_ROLE_BY_TYPE[t]:
            bad.append(e.get("seq"))
    if bad:
        print(f"❌ 不合规 {len(bad)} 处: {bad[:8]}")
        return 1
    last_title = None
    for e in evs:
        if e.get("type") == "session/title":
            last_title = e.get("data")
    print(f"✅ 合规（{len(evs)} 事件）· 最终标题投影: {json.dumps(last_title, ensure_ascii=False)[:140]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="DSH 历史会话标题批量统一命名")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--session")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify")
    ap.add_argument("--ignore-lock", action="store_true",
                    help="离线模式：宿主已停时使用（忽略 session.lock 与 mtime 活跃保护）")
    ap.add_argument("--title-for", metavar="UUID",
                    help="只产出该会话应有的标题文本（不写文件）——供 DSH 插件调官方 rename")
    a = ap.parse_args()
    if a.title_for:
        sys.exit(cmd_title_for(a.title_for))
    if a.verify:
        sys.exit(cmd_verify(a.verify))
    if a.scan:
        sys.exit(cmd_scan(a.root))
    if a.apply:
        sys.exit(cmd_apply(a.root, a.session, a.force, a.dry_run, a.ignore_lock))
    ap.print_help()


if __name__ == "__main__":
    main()
