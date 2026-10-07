#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_invocation_logger.py v1.0 -- B埋点批次共享留痕器 (2026-08-23, 皮叔令)

目的: 让「自动化率」可机械测量——每次守卫调用留一行 {ts, guard, source}，
source ∈ {hook_auto, manual}。检测不靠自觉: hook 侧由调用方(pre-commit/watch)
显式写 hook_auto; 其余一切来源默认 manual(无钩子上下文=手动, 语义准确)。

写入: 开发工具/logs/runtime/guard_invocations_YYYY-MM.jsonl (append-only 单行写,
铁律-014 合规; 月分文件防单文件无限膨胀)。
v1.1 2026-09-02: 从系统日志目录迁出，根治运行时日志污染系统日志目录。

Usage:
  python3 guard_invocation_logger.py --guard NAME --source hook_auto|manual
        [--exit N] [--detail "..."]
Exit: 0 written | 2 usage | 3 io failure (fail-open: 调用方应忽略本工具失败,
埋点永不阻塞守卫主流程)。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse, datetime, io, json, os, sys

OUT_DIR = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "logs", "runtime")  # v1.1 2026-09-02 根治：从系统日志目录迁出
VALID = {"hook_auto", "manual"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guard", required=True)
    ap.add_argument("--source", required=True, choices=sorted(VALID))
    ap.add_argument("--exit", dest="rc", default=None)
    ap.add_argument("--detail", default="")
    a = ap.parse_args()
    rec = {"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "guard": a.guard, "trigger_source": a.source}
    if a.rc is not None and a.rc != "":
        rec["exit"] = int(a.rc)
    if a.detail:
        rec["detail"] = a.detail[:200]
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
        month = rec["ts"][:7]
        path = os.path.join(OUT_DIR, "guard_invocations_%s.jsonl" % month)
        with io.open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(path)
        sys.exit(0)
    except Exception as e:
        print("logger-fail(open): %s" % e, file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
