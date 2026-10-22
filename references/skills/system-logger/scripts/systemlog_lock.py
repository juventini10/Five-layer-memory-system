# -*- coding: utf-8 -*-
# REG: skip 共享并发锁工具库（非守卫/非引擎判据·无挂载·被 append/reconcile import）
# TRUTH_OF: 脚本中心/system-logger/scripts/systemlog_lock.py
"""systemlog_lock — 系统日志并发写锁（根治 reconcile os.replace 吞并发 append）。

根因：append 用 O_APPEND(安全原子)，但 reconcile_overview 读全文→算→os.replace
换 inode；若他端 append 落在"reconcile 读"与"replace"之间，append 写进即将被换掉的
旧 inode = 条目消失（现乐观重试≤3 只缩窗不消除·脚本自曝"彻底解=fcntl"）。

修法：同一把独占锁(锁文件 <logdir>/.systemlog.lock)让 append 的写 与 reconcile 的
read→replace 互斥。调用方纪律：append 只在它那一笔写内持锁，释放后再 spawn reconcile
（否则父持锁+子抢同锁=死锁）。flock 对同 fd 可重入、跨进程互斥。
平台：POSIX→fcntl.flock；Windows→msvcrt.locking；都不支持→best-effort no-op（诚实降级，
      ⛔不崩，但该平台仍存竞态，须显式声明）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os, sys, contextlib

@contextlib.contextmanager
def log_lock(logfile, timeout_s=10.0):
    """对 logfile 所在目录的 .systemlog.lock 持独占锁；持不到超时则 best-effort 放行。"""
    lockpath = os.path.join(os.path.dirname(os.path.abspath(logfile)), ".systemlog.lock")
    fd = None
    try:
        fd = os.open(lockpath, os.O_CREAT | os.O_RDWR, 0o644)
    except OSError:
        fd = None
    if fd is None:
        yield
        return
    try:
        if os.name == "posix":
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        elif sys.platform == "win32":
            import msvcrt, time
            msvcrt.setlkinfo = None
            t0 = time.time()
            while True:
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() - t0 > timeout_s:
                        break  # best-effort 放行（Win 罕见并发·仍可能竞态，显式超时不 hang）
                    time.sleep(0.05)
        yield
    finally:
        try:
            if os.name == "posix":
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
            elif sys.platform == "win32":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        try:
            os.close(fd)
        except OSError:
            pass
