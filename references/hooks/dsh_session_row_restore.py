#!/usr/bin/env python3
# version: v0.3
# 家族：变换（改） ｜ 部署形态：按需
"""dsh_session_row_restore.py — 复原被别人删掉的行，重建会话文件的 seq 连续性。

背景（2026-09-10 侧栏「历史加载失败」根因）
------------------------------------------
同侪工具 `dsh_session_fix_seq.py` 的标题搬迁逻辑是「**删掉原位的 user 标题行 → 在文件末尾重新追加一条**」。
对 **v0 遗留格式**（`session.jsonl.zstd`）而言这是致命操作：v0→v1 迁移器
（dsh-session-format-v0-to-v1/lib/index.js scanRows）要求 **每行 seq === 递增事件计数**
（`released Session row N has seq gap (expected X, got Y)`），删掉中间一行即在事件流里留洞 →
整个会话加载失败 → 侧栏该会话「历史记录不在」。
实证（session-1f496e8c）：当前文件 = 15:11 备份 **减去** 第 7 行 `session/title seq=6`
**加上** 末尾两条 title(26501/26502) —— 仅此 2 处差异。

本工具：以「上一次已知可加载」的备份为基准，把**缺失的行按原位插回**（内容取备份原样），
保留当前文件里更新的行与末尾追加行。⛔不虚构任何事件（只搬运已存在过的行）。

安全
----
① 备份 `<file>.bak-<ts>-prerowrestore`（只增不删）
② 修前判据：当前文件与备份无「缺失行」→ skip（幂等·最小侵入）
③ 修后回验：前 len(备份) 行的 (type, seq) 必须与备份逐位一致 + 末尾追加行 seq 严格递增
④ 写盘走 dsh_session_repair.compress（帧契约自检内建）

用法
----
  python3 dsh_session_row_restore.py --scan                 # 只扫描报告（默认 ~/.dsh/sessions）
  python3 dsh_session_row_restore.py --fix --all            # 修复全部命中会话
  python3 dsh_session_row_restore.py --fix --session <uuid> # 单个
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import glob
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsh_session_repair import compress, decompress, frame_states, v0_contiguity, chain_restore_ok  # noqa: E402

ROOT_DEFAULT = os.path.expanduser("~/.dsh/sessions")


def session_files(root: str) -> list:
    out = []
    for p in glob.glob(os.path.join(root, "*", "*", "session*.jsonl.zstd")):
        if ".bak-" in p or ".tmp-" in p:
            continue
        out.append(p)
    return sorted(out)


def v0_only(paths: list) -> list:
    """只取 v0 遗留格式（`session.jsonl.zstd`）。

    为什么限定：v0→v1 迁移器（dsh-session-format-v0-to-v1 scanRows）**强制**每行 seq === 递增事件计数，
    删行即致命（"released Session row N has seq gap"）；而 v2/v3 是当前格式、由宿主正常读取，
    **容忍**中间缺号（实证：本轮 v3 会话被同一工具删过 title 行仍可加载）。⇒
    ⛔不对可加载的 v2/v3 文件做无谓改动（少动=少风险）；v2/v3 若报错再用本工具单独处理。
    """
    return [p for p in paths if os.path.basename(p) == "session.jsonl.zstd"]


def load_rows(path: str) -> list:
    return [json.loads(l) for l in decompress(path).decode("utf-8").splitlines() if l.strip()]


def plan(path: str) -> dict:
    """返回 {status, missing, rows(复原后行表), backup} —— status: skip-no-backup/skip-ok/would-fix"""
    base = path.rsplit(".jsonl.zstd", 1)[0] + ".jsonl.zstd"
    baks = sorted(glob.glob(base + ".bak-*"), key=os.path.getmtime)
    if not baks:
        return {"status": "skip-no-backup"}
    cur = load_rows(path)
    cur_seqs = Counter(e.get("seq") for e in cur)
    # 从新到旧找第一个「包含当前缺失行」的备份作为复原源
    for bak in reversed(baks):
        old = load_rows(bak)
        old_seqs = Counter(e.get("seq") for e in old)
        missing = old_seqs - cur_seqs
        if not missing:
            continue
        # 复原：按备份顺序走，取当前文件里的同 seq 行（内容更新），缺失行取备份原样；
        #       备份里没有的行（末尾新追加）按原序接在后面。
        pool = {}
        for e in cur:
            pool.setdefault(e.get("seq"), []).append(e)
        used = Counter()
        restored, taken = [], set()
        for e in old:
            s = e.get("seq")
            lst = pool.get(s) or []
            if used[s] < len(lst):
                restored.append(lst[used[s]]); used[s] += 1; taken.add(id(lst[used[s] - 1]))
            else:
                restored.append(e); used[s] += 1
        tail = [e for e in cur if id(e) not in taken]
        restored += tail
        return {"status": "would-fix", "missing": sorted(k for k in missing),
                "rows": restored, "backup": bak, "prev_n": len(old), "cur_n": len(cur),
                "tail_n": len(tail)}
    return {"status": "skip-ok"}


def verify(rows: list, old: list, prev_n: int) -> str | None:
    """写盘前双验：①与备份逐位一致（内容基准）②v0 加载硬契约（共享判据·与宿主对齐）"""
    ok, detail = v0_contiguity(rows[1:])
    if not ok:
        return f"v0 加载硬契约不过（{detail}）"
    for i in range(prev_n):
        a, b = rows[i], old[i]
        if (a.get("type"), a.get("seq")) != (b.get("type"), b.get("seq")):
            return f"第 {i} 行与备份不一致（{a.get('type')}/{a.get('seq')} vs {b.get('type')}/{b.get('seq')}）"
    tail = [e.get("seq") for e in rows[prev_n:]]
    if tail != sorted(tail):
        return f"末尾追加行 seq 非递增：{tail[:6]}"
    return None


def chain_ok(path: str):
    """把（可能带帧的）会话文件解压到临时 jsonl 后跑宿主全链核验。"""
    import tempfile
    with tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False) as fh:
        fh.write(decompress(path))
        tmp = fh.name
    try:
        return chain_restore_ok(tmp)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def plan_content(path: str):
    """内容复原：以「能过宿主全链核验」的基准备份为准，前段取基准原文、末段保留当前追加行。

    为什么需要它（2026-09-10 第二层损坏）：除"删行留洞"外还有一类损坏——**行被改了字段**。
    实证：角色补全工具给 v0 的 user/message 加了 role，v0 迁移器便按"当前格式"校验 → 要求 id
    → 而插件注入的消息本就没有 id → `refuses this format v0 Session: ... lacks required member "id"`
    → 整个会话历史加载失败。逐行复原到基准即可（基准是当时能加载的状态）。
    """
    base = path.rsplit(".jsonl.zstd", 1)[0] + ".jsonl.zstd"
    for bak in sorted(glob.glob(base + ".bak-*"), key=os.path.getmtime):   # 从旧到新找第一个可用基准
        try:
            if not chain_ok(bak):
                continue
            old, cur = load_rows(bak), load_rows(path)
        except Exception:
            continue
        rows = old + cur[len(old):]
        return {"status": "would-fix", "rows": rows, "backup": bak,
                "prev_n": len(old), "cur_n": len(cur), "tail_n": len(cur) - len(old)}
    return {"status": "skip-no-baseline"}


def fix_one(path: str, dry: bool = False) -> str:
    # ① 权威判据优先：已能过宿主全链核验 ⇒ 无事可做（幂等·最小侵入）
    #    ⚠️ chain_ok 返回 (ok, detail) 元组——直接 `if chain_ok(...)` 会因"非空元组恒真"而永远跳过
    #    （2026-09-10 写测试当场逮住：判据是元组时不能当布尔用）
    try:
        ok_chain, _d = chain_ok(path)
        if ok_chain:
            return "skip-ok"
    except Exception:
        pass
    # ② 先试"插回被删行"，不行再"逐行内容复原"
    p = plan(path)
    if p["status"] != "would-fix":
        p = plan_content(path)
    if p["status"] != "would-fix":
        return p["status"]
    old = load_rows(p["backup"])
    err = verify(p["rows"], old, p["prev_n"])
    if err:
        return f"failed:回验不过（{err}）→放弃写盘"
    if dry:
        mode = "插回被删行" if p.get("missing") else "逐行内容复原"
        return f"would-fix[{mode}](缺 {len(p.get('missing', []))} 行·尾 {p['tail_n']})"

    data = ("\n".join(json.dumps(e, ensure_ascii=False) for e in p["rows"]) + "\n").encode("utf-8")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak-{ts}-prerowrestore"
    subprocess.run(["cp", path, backup], check=True)
    tmp = f"{path}.tmp-{ts}"
    compress(data, tmp)                       # 内含帧契约自检
    ok, state = frame_states([tmp]).get(tmp, "ERR"), None
    if ok != "OK":
        os.remove(tmp)
        return f"failed:帧契约（{ok}）→放弃写盘"
    if [json.loads(l) for l in decompress(tmp).decode("utf-8").splitlines() if l.strip()] != p["rows"]:
        os.remove(tmp)
        return "failed:回验内容不一致→放弃写盘"
    # ★ 权威判据终检：宿主自身全链恢复器必须无错——这是"历史能否显示"的唯一判据
    ok2, detail = chain_ok(tmp)
    if not ok2:
        os.remove(tmp)
        return f"failed:宿主全链核验不过（{detail}）→放弃写盘（原文件未动）"
    os.replace(tmp, path)
    mode = "插回被删行" if p.get("missing") else "逐行内容复原"
    return f"fixed[{mode}]({p['cur_n']}→{len(p['rows'])} 行)"


def cmd_watch(root: str) -> int:
    """按变更才体检（verify-on-change）：稳态零成本，变更即校验+必要时自愈。

    为什么这么设计（愿景①机制代意志 × 成本可控）：全量 v0 体检约 2 分钟，塞进 15 分钟巡逻
    是 18% 占空比；而 v0 文件绝大多数时间不变 ⇒ 用 (mtime,size) 指纹做缓存，
    只在文件**变动过**时才真正解压校验。于是可以挂进 60s 快链而几乎不花时间。
    """
    cache_path = os.path.expanduser("~/.dsh/cache/frame-guard/v0_verified.json")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        cache = json.load(open(cache_path, encoding="utf-8"))
    except Exception:
        cache = {}
    checked = fixed = skipped = broken = 0
    for p in v0_only(session_files(root)):
        try:
            st = os.stat(p)
            fp = f"{int(st.st_mtime)}:{st.st_size}"
        except OSError:
            continue
        if cache.get(p) == fp:
            skipped += 1
            continue
        checked += 1
        try:
            # ★ 权威判据（宿主自身全链恢复器）——⛔不用自建复刻当健康判据
            ok, _detail = chain_ok(p)
        except Exception:
            ok = False
        if not ok:
            broken += 1
            r = fix_one(p)
            if r.startswith("fixed"):
                fixed += 1
                ok = True
                print(f"  🔧 {os.path.basename(os.path.dirname(p))} :: {r}")
            else:
                print(f"  ⚠️ {os.path.basename(os.path.dirname(p))} :: 自愈未成（{r}）——原文件与备份均在")
        if ok:
            try:
                st = os.stat(p)
                cache[p] = f"{int(st.st_mtime)}:{st.st_size}"
            except OSError:
                pass
    with open(cache_path, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=0)
    print(f"v0 变更体检：新增/变更 {checked} · 命中缓存跳过 {skipped}"
          + (f" · ❌ 发现断链 {broken} · 🔧 已自愈 {fixed}" if broken else " · ✅ 全部合规"))
    return 0 if not broken or fixed == broken else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="DSH 会话缺失行复原（重建 v0 seq 连续性）")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--session", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--watch", action="store_true", help="按变更体检（指纹缓存·稳态零成本）")
    ap.add_argument("--include-v23", action="store_true", help="同时处理 v2/v3 文件（默认只修 v0）")
    a = ap.parse_args()

    if a.watch:
        sys.exit(cmd_watch(a.root))

    targets = session_files(a.root)
    if not a.include_v23:
        targets = v0_only(targets)
    if a.session:
        targets = [p for p in targets if a.session in p]
    if not targets:
        print(f"未找到会话文件：{a.root}")
        sys.exit(1)

    stats, bad = {}, []
    for p in targets:
        name = os.path.basename(os.path.dirname(p))
        try:
            if a.scan or a.dry_run:
                r = fix_one(p, dry=True)
                if r.startswith("would-fix"):
                    bad.append(f"{name} :: {r}")
            else:
                r = fix_one(p)
                if r.startswith("fixed"):
                    bad.append(f"{name} :: {r}")
        except Exception as e:
            r = f"failed:{type(e).__name__}:{str(e)[:60]}"
            bad.append(f"{name} :: {r}")
        stats[r.split("(")[0]] = stats.get(r.split("(")[0], 0) + 1

    for line in bad:
        print("  🔧", line)
    print("\n统计：" + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if a.scan or a.dry_run:
        print(f"共 {len(targets)} 个文件 | 需复原 {len(bad)} 个")
    sys.exit(0 if not [b for b in bad if "failed" in b] else 1)


if __name__ == "__main__":
    main()
