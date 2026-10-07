#!/usr/bin/env python3
# memlog.py —— 记忆日志并发安全追加网关（第一性原理最优·append-only）
#
# 根因：多写者对同一可变文件做 read-modify-write 无协调 → last-writer-wins。
# 第一性原理最优：消除 read-modify-write，改为纯追加。
#   - O_APPEND：内核在每次 write 前把偏移移到文件末尾，单 write（≤PIPE_BUF 4096B）原子落盘，
#     两写者的条目永不互相覆盖/穿插 → 竞争在 OS 层被消解，无需片段/合并/锁协议。
#   - flock：仅当单条目 >4KB 需多次 write 时，锁住整段写入防止与其他写者穿插（小条目无感）。
#   - 直接写 canonical，无片段目录、无合并步、无标记、无需迁移（旧的 adopt/seed/merge 正是 bug 来源，已弃）。
#
# 用法：memlog append <YYYY-MM-DD> "<content>"
# 约定（根治生效前提）：所有记忆追加走 `memlog append`；罕见的中途修订仍用 Edit，但须在单写者时刻（回合末）进行。
# version: v0.1
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os
try:
    import fcntl
except ImportError:
    fcntl = None  # Windows 无 fcntl → 跳过文件锁（小条目 O_APPEND 仍原子）

MEMDIR = os.environ.get("MEMLOG_DIR", os.path.expanduser("~/WorkBuddy/开发/.workbuddy/memory"))

def append(date, content):
    c = os.path.join(MEMDIR, date + ".md")
    # 'a' 模式 = O_APPEND：内核保证每次 write 原子追加到末尾，无 read-modify-write 竞争
    with open(c, "a", encoding="utf-8") as f:
        if fcntl:
            fcntl.flock(f, fcntl.LOCK_EX)   # 大条目跨多次 write 时防穿插（小条目本就原子）
        try:
            f.write(content + "\n")
        finally:
            if fcntl:
                fcntl.flock(f, fcntl.LOCK_UN)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: memlog append <date> <content>"); sys.exit(2)
    if sys.argv[1] == "append":
        append(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    else:
        print("unknown cmd:", sys.argv[1]); sys.exit(2)
