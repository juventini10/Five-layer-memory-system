#!/usr/bin/env python3
# version: v0.2
# 家族：变换（改） ｜ 部署形态：按需（经巡逻/快守卫调度）
"""dsh_session_reframe.py — 修复 DSH 会话文件的 zstd 帧契约（重压缩·内容零改动）。

背景（2026-09-10 三次事故·"侧栏只剩当前会话"）
--------------------------------------------
DSH 加载器 dsh-session-persistence-jsonl 的 assertZstdHeaderFrame 要求：
    **第一个 zstd 帧必须恰好只含 header 那一行**
    （plaintext.length !== 0 && plaintext.indexOf(10) === plaintext.length - 1）
早期 dsh_session_title_batch.py 用 `zstd -q -o` 把整个文件压成**单帧** → 首帧含全部事件
    → 抛 "corrupt Zstandard session log: first frame is not exactly one header line"
    → 整个 session/list 失败 → 侧栏只剩当前会话（误以为"对话全没了"）。

本工具：把这类文件按 DSH 契约**逐行成帧**重新压缩。⛔只重压缩，不改任何事件内容。

安全
----
① 备份 `<file>.bak-<ts>-prereframe`（只增不删）
② 原子替换（同目录临时文件 → os.replace）
③ 修前判据：首帧合规则跳过（幂等·最小侵入）
④ 修后双重回验：a) 解压内容与原文件逐字节一致 b) 首帧合规——任一不过则放弃写盘
⑤ 不等活跃期：BAD 即刻修（DSH 宿主只追加帧、从不整文件重写 ⇒ BAD 必是外部写手产物·
   ⛔不存在"宿主正在写所以等等"的情形；旧 300s 跳过会造成假全清+15 分钟空白窗口）

用法
----
  python3 dsh_session_reframe.py --scan            # 只扫描报告（默认 ~/.dsh/sessions）
  python3 dsh_session_reframe.py --fix --all       # 修复全部不合规文件
  python3 dsh_session_reframe.py --fix --all --dry-run
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsh_session_repair import compress, decompress, frame_states  # noqa: E402  帧契约唯一实现

ROOT_DEFAULT = os.path.expanduser("~/.dsh/sessions")
# 2026-09-10 四次事故根治后已废弃（BAD 即刻修·不再按 mtime 跳过）；保留常量仅为兼容
# 历史调用方的 import，⛔新代码不要使用（见 reframe_one 注释与模块头 ⑤）。
ACTIVE_WINDOW_S = 0


def session_files(root: str) -> list[str]:
    return sorted(
        p for p in glob.glob(os.path.join(root, "*", "*", "session*.jsonl.zstd"))
        if ".bak-" not in p
    )


def reframe_one(path: str, dry_run: bool = False, force: bool = False, state: str | None = None) -> str:
    """返回 one of: skip-ok | fixed | failed:<原因>。

    state：调用方批量体检得到的首帧结论（frame_states）——批量预检使 49 文件体检从
    7.5s 降到 0.2s，这是"快守卫 1 分钟一轮"能成立的前提；缺省则单文件自检。
    """
    if state is None:
        state = frame_states([path]).get(path, "ERR:体检未返回结果")
    if state == "OK" and not force:
        return "skip-ok"
    if state.startswith("ERR"):
        return f"failed:首帧判据执行失败({state})"
    # 🔴 2026-09-10 四次事故根治 —— BAD 即刻修，不再受 300s 活跃窗口限制。
    # 依据 = DSH 宿主写路径源码（dsh-session-persistence-jsonl/lib/index.js）：
    #   · appendLines → open(path,"a") + writeFile(单帧追加) + fsync；
    #   · materialize → 写 tmp 后 rename。
    # 宿主从不整文件重写 → 首帧永远是 header 帧 → **宿主持有的文件不可能呈 BAD**。
    # 故 BAD ⇒ 必是外部写手违规产物（实证：title_batch 的 `zstd -q -o`、/tmp/seqfix.py）
    # ⇒ 无竞争风险；等待 15 分钟只延长"侧栏空白"窗口，且旧 300s 跳过会让巡逻
    #   在 last_status 里报"无坏会话"= 假全清（本次事故即如此漏过）。
    # 注：force 仍只用于"连合规文件也重写"的场景；本函数不因活跃期跳过 BAD。
    if dry_run:
        return "would-fix"

    raw = decompress(path)                      # 解压全部事件（内容基准）
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{path}.bak-{ts}-prereframe"
    subprocess.run(["cp", path, backup], check=True)
    tmp = f"{path}.tmp-{ts}"
    compress(raw, tmp)                          # 逐行成帧（与 DSH 自身写法一致）

    # 回验 a：内容逐字节一致（⛔重压缩不得改动内容）
    if decompress(tmp) != raw:
        os.remove(tmp)
        return "failed:回验内容不一致→放弃写盘"
    # 回验 b：帧契约合规
    state2 = frame_states([tmp]).get(tmp, "ERR:体检未返回结果")
    if state2 != "OK":
        os.remove(tmp)
        return f"failed:回验帧契约仍不合规({state2})→放弃写盘"
    os.replace(tmp, path)
    return "fixed"


def main() -> None:
    ap = argparse.ArgumentParser(description="DSH 会话 zstd 帧契约修复（重压缩·内容零改动）")
    ap.add_argument("--root", default=ROOT_DEFAULT)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="忽略幂等/活跃保护")
    a = ap.parse_args()

    targets = session_files(a.root)
    if not targets:
        print(f"未找到会话文件：{a.root}")
        sys.exit(1)

    # 批量预检（单 node 进程·49 文件 ≈0.2s，替代逐文件起进程的 ≈7.5s）
    states = frame_states(targets)

    if a.scan or a.dry_run:
        bad = 0
        for p in targets:
            state = states.get(p, "ERR:体检未返回结果")
            if state != "OK":
                bad += 1
                print(f"❌ {state:>10}  {os.path.basename(os.path.dirname(p))}")
        print(f"\n共 {len(targets)} 个文件 | ✅合规 {len(targets)-bad} | ❌违规 {bad}")
        sys.exit(0 if bad == 0 else 1)

    if not (a.fix and a.all):
        ap.print_help()
        sys.exit(1)

    stats: dict[str, int] = {}
    failures: list[str] = []
    for p in targets:
        try:
            r = reframe_one(p, dry_run=False, force=a.force, state=states.get(p))
        except Exception as e:  # 单点失败不中断整批（会话可能正被宿主写入）
            r = f"failed:{type(e).__name__}:{str(e)[:60]}"
        stats[r] = stats.get(r, 0) + 1
        if r.startswith("failed") or r == "fixed":
            print(f"{'🔧' if r == 'fixed' else '⚠️'} {os.path.basename(os.path.dirname(p))} → {r}")
        if r.startswith("failed"):
            failures.append(f"{os.path.basename(os.path.dirname(p))}:{r}")

    print("\n统计：" + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if failures:
        print(f"⚠️ 失败 {len(failures)} 个（原文件与备份均在·未动）")
        for f in failures[:8]:
            print("   ", f)
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
