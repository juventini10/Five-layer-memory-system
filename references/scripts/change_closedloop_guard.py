#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
change_closedloop_guard.py — 改动闭环律机械门禁（Stop 链·warn-only）
设计依据: app-config.json §3 闭环四查（SSOT 同步 + 系统日志收口）+ 愿景①(检测不靠人记得)。
职责: 会话结束前机械核验「今日 git 提交过的产物/哲学/SSOT 文件，是否在今日系统日志登记」。
      未登记 → ⚠️ 提醒（exit 0 不阻断）。已登记/无产物改动 → ✅ 静默过。
判据:
  ① 取今日 git 提交涉及的文件（git log --since today --name-only），过滤到闭环律相关路径
    （技能配置/记忆蓝图/守卫编写规范/app-config.json/变更日志/system-logger）。
  ② 今日系统日志（系统日志_<today>.md）存在且含任一改动文件 basename → 已收口 → 静默过。
  ③ 存在闭环律相关改动但日志未提及 → ⚠️ 提醒具体文件（不阻断）。
全过/告警均 exit 0（末位校验族·不阻断会话收尾）。
失败放行原则: 任何异常 → 静默过（不阻塞守护）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import subprocess
from datetime import date

HOME = os.path.expanduser("~")
REPO = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
LOG_DIR = os.path.join(REPO, "工作日志", "系统日志")
TODAY = date.today().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"系统日志_{TODAY}.md")

# 闭环律相关路径模式（改了这些 = 须登记进哲学/SSOT/系统日志）
# 锚定规范目录（非任意子串），避免命中 install-package 镜像副本里的同名子路径
CLOSEDLOOP_PATTERNS = [
    "技能配置/",            # 规范技能配置（含 system-logger）
    "记忆蓝图/",            # 顶层记忆蓝图（规范哲学文件）
    "变更日志.md",          # 顶层中央账本
    "app-config.json",      # WB 运行时配置
]
# 派生/镜像目录：install-package & DSH 副本由 mirror-sync 自动生成，非手写产物，排除以免噪声
EXCLUDE_DIRS = ["知识库/", "发布库/"]

# 噪声过滤：同步工具产生的临时/备份文件不应触发闭环律告警（失败放行·降噪）
# 含 .tmp. 任意位置（如 SKILL.md.tmp.1049.1787838738798）也判 junk，避免残留临时文件误报
JUNK_RE = re.compile(r"(/\.git/|\.tmp\.|\.tmp$|\.bak$|\.swp$|\.orig$|~$)", re.IGNORECASE)


def is_junk(path):
    if "/.git/" in path:
        return True
    return bool(JUNK_RE.search(os.path.basename(path)))


def run(cmd):
    try:
        return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=30)
    except Exception:
        return None


def changed_product_files():
    files = set()
    # core.quotepath=false：中文路径默认被 git 加双引号包裹（"\346...CHANGELOG.md"），
    # 导致 basename 带尾引号与日志文本不匹配→全量误报；此处输出原始路径根治
    r = run(["git", "-c", "core.quotepath=false", "log", "--since", f"{TODAY} 00:00", "--name-only", "--pretty=format:"])
    if r and r.returncode == 0:
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(ex in line for ex in EXCLUDE_DIRS):
                continue  # 派生镜像目录，非手写产物
            if not is_junk(line):
                files.add(line)
    out = []
    for f in files:
        for p in CLOSEDLOOP_PATTERNS:
            if p in f:
                out.append(f)
                break
    return out


def main():
    try:
        prod = changed_product_files()
        if not prod:
            return 0  # 今日无产物/哲学改动 → 不触发闭环律
        log_text = ""
        if os.path.isfile(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8") as fh:
                    log_text = fh.read()
            except Exception:
                log_text = ""
        unclosed = [f for f in prod if os.path.basename(f) not in log_text]
        if not unclosed:
            print(f"✅ 改动闭环律门禁通过（今日 {TODAY} 改动了 {len(prod)} 个产物/哲学文件，均已在系统日志登记）")
            return 0
        print(f"⚠️ [改动闭环律·未收口] 今日（{TODAY}）以下产物/哲学文件已改动但未在系统日志登记：")
        for f in unclosed:
            print(f"   - {f}")
        print("   按 app-config §3 闭环：改动涉及产物/哲学/SSOT 须同步更新并记入系统日志（system-logger Skill）。")
        print("   本门禁仅提醒不阻断。")
        return 0
    except Exception:
        return 0  # 失败放行


if __name__ == "__main__":
    sys.exit(main())
