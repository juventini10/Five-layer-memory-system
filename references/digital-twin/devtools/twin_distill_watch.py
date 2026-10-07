#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
twin_distill_watch.py v0.2 — 童灵·增量蒸馏指纹监视器

职责（单一）：扫描源资产指纹 vs 上次快照，输出变化清单。只读不写源文件。
设计原则（守卫编写规范 §八 + 脚本哲学 §二·五）：
  - 只读巡检：不修改任何源文件
  - 失败放行：异常 exit 0（cron 场景绝不制造噪音）
  - 静默无变更：无变化时 stdout 为空（watchdog 模式零投递）
  - 有痕跳过：--init 显式初始化基线
监视源（v0.2 8类蒸馏源+1类抗更新）：
  diary/greatest/stance/core/soul/shadow/rules/systemlog(第五入口·[童灵思考]标记)
用法：
  python3 twin_distill_watch.py --init      # 初始化/重置指纹基线
  python3 twin_distill_watch.py             # 常规巡检（有变化才输出）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, sys, json, hashlib
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]")
STATE = os.path.join(BASE, "数字分身/scripts/fingerprint_state.json")

WATCH = [
    # (label, path_or_dir, recursive)
    ("diary",    os.path.expanduser("~/[日记仓库]/1-每日计划/01-日记"), True),
    ("greatest", os.path.join(BASE, "最伟大的我"), True),
    ("stance",   os.path.join(BASE, "AI学习库"), True),
    ("core",     os.path.join(BASE, "核心层/CORE.md"), False),
    ("soul",     os.path.join(BASE, "核心层/SOUL.md"), False),
    ("shadow",   os.path.join(BASE, "潜意识层/SHADOW.md"), False),
    ("rules",    os.path.join(BASE, "记忆规则"), True),
    # 第五学习入口（2026-08-25 童灵代行讨论定案·设计哲学01规范§4.1）：
    # AI端自我反思——系统日志中带 [童灵思考] 标记的条目。
    # 消费端（蒸馏执行时）须 grep '[童灵思考]' 过滤，无标记的普通任务记录不进入人格蒸馏。
    # 方向：童灵→童灵（自我认知深化），不伪装成你的立场（防二阶折射）。
    ("systemlog", os.path.join(BASE, "工作日志/系统日志"), True),
    # dsh 插件活体（2026-08-25 抗更新监视）：被升级/重装覆盖时在此现形
    # → 处置：python3 [记忆共享中心]/脚本中心/dsh_plugin_deploy.py --deploy
    ("dsh-plugin", os.path.expanduser("~/.dsh/profiles/web/node_modules/five-layer-memory/src/index.js"), False),
]

def fingerprint(path):
    try:
        st = os.stat(path)
        with open(path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()[:16]
        return f"{h}:{st.st_mtime_ns}:{st.st_size}"
    except Exception:
        return None

def scan():
    snap = {}
    for label, p, rec in WATCH:
        if os.path.isfile(p):
            fp = fingerprint(p)
            if fp:
                snap[label + "/" + os.path.basename(p)] = fp
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if not d.startswith(".") and "bak" not in d.lower()]
                for fn in files:
                    if fn.endswith(".md"):
                        full = os.path.join(root, fn)
                        fp = fingerprint(full)
                        if fp:
                            snap[label + "/" + os.path.relpath(full, p)] = fp
    return snap

def main():
    init = "--init" in sys.argv
    cur = scan()
    if init or not os.path.isfile(STATE):
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds"), "snap": cur}, f, ensure_ascii=False)
        if init:
            print(f"[init] 基线已写入 {len(cur)} 个文件指纹")
        return 0
    prev = json.load(open(STATE, encoding="utf-8")).get("snap", {})
    added   = sorted(set(cur) - set(prev))
    removed = sorted(set(prev) - set(cur))
    changed = sorted(k for k in set(cur) & set(prev) if cur[k] != prev[k])
    if not (added or removed or changed):
        return 0  # 静默无变更
    # B埋点(2026-08-23·你令): trigger_source=hook_auto（生产调用方=launchd；失败放行）
    try:
        import subprocess as _sp
        _logger = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                               "开发工具", "guard_invocation_logger.py")
        if os.path.exists(_logger):
            _sp.run(["python3", _logger, "--guard", "twin_distill_watch", "--source", "hook_auto",
                     "--detail", f"+{len(added)}~{len(changed)}-{len(removed)}"],
                    timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    print(f"[twin-distill] 源资产变化 @ {datetime.now().isoformat(timespec='seconds')}")
    for k in added:
        print(f"  + 新增 {k}")
    for k in changed:
        print(f"  ~ 变更 {k}")
    for k in removed:
        print(f"  - 移除 {k}")
    print(f"合计: +{len(added)} ~{len(changed)} -{len(removed)}")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # 失败放行
