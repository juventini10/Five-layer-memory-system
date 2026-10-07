#!/usr/bin/env python3
# systemlog_stophook_check.py v0.1 —— Stop 链·系统日志收口纪律校验守卫
# 设计: 机械(检测)脚本自动;修正动作(写日志)留人/AI。非阻断(exit 0)·纯提醒。
# 依据: app-config.json §3 闭环④「实质性任务记系统日志」+ 愿景①(检测不靠人记得)+ S014「机械是药」。
# 触发: settings.json Stop 链挂载(与 registry_guards.sh 同族·末位校验)。
#
# 判据(避免噪声·精准显形):
#   ① 今日系统日志文件存在且含 >=1 条任务记录(完成：) → 纪律已守 → ✅ 静默过。
#   ② 今日无日志 → 查「今日是否有实质工作」证据:
#        - git: ~/个人AI档案今日有 commit, 或
#        - git: ~/个人AI档案工作树有未提交改动
#      → 有证据 = 做了工作却漏记 → ⚠️ 提醒(不阻断)。
#   ③ 今日无日志且无工作证据 → 纯聊天日 → ✅ 静默过(零噪声)。
# 全过/告警均 exit 0(末位校验守卫·不阻断会话收尾)。

# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import subprocess
from datetime import datetime, date

HOME = os.path.expanduser("~")
REPO = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
LOG_DIR = os.path.join(REPO, "工作日志", "系统日志")
TODAY = date.today().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"系统日志_{TODAY}.md")


def run(cmd):
    try:
        return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=30)
    except Exception:
        return None


def log_has_entry():
    if not os.path.isfile(LOG_FILE):
        return False
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False
    # 任务记录行: 「完成：」(append_log_entry 写入) 或 「### 」任务块标题
    return bool(re.search(r"完成[:：]|^###\s", content, re.MULTILINE))


def work_evidence_today():
    # ① 今日 commit
    r = run(["git", "log", "--since", f"{TODAY} 00:00", "--oneline", "-1"])
    if r and r.returncode == 0 and r.stdout.strip():
        return True
    # ② 未提交改动(排除日志/记忆琥珀等噪声)
    r = run(["git", "status", "--porcelain"])
    if r and r.returncode == 0 and r.stdout.strip():
        return True
    return False


def main():
    if log_has_entry():
        print(f"✅ 系统日志收口校验通过（今日 {TODAY} 已有记录·纪律已守）")
        return 0
    # 今日无日志
    if work_evidence_today():
        print(f"⚠️ [系统日志收口·缺口] 今日（{TODAY}）~/个人AI档案有实质改动/提交，但系统日志_无记录。")
        print("   按 app-config §3 闭环④：实质性任务须记系统日志——请补记（system-logger Skill）。")
        print("   本守卫仅提醒不阻断。")
        return 0
    # 纯聊天日
    print(f"✅ 系统日志收口校验跳过（今日 {TODAY} 无实质工作证据·纯交互）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
