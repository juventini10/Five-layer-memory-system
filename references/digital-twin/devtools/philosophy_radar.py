#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# REG: family=哲学读侧雷达 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""
philosophy_radar.py v0.1 — 哲学读侧完整性专项 · P0 变更雷达（launchd 每日一次）

设计定位（哲学读侧完整性专项-S级方案 §三 P0.1）：
- 治「AI 读哲学敷衍漏读」——把你的抽查变成开卷考试：凡近 72h 变动的哲学文件，机器先看见。
- 扫描域默认口径：记忆蓝图全域（00_系统总览 ~ 05 全部 .md），
  排除 发布库/（随包快照非活源）与 .bak（备份噪声非活源）——此口径经皮叔 2026-10-02 授权走默认。
- 输出：logs/philosophy_radar.jsonl，一行一条 {file/domain/version/born/mtime}，按 mtime 降序。
  ⛔ 每日快照式覆盖写（滚动 72h 窗口），非 append 累积——到达腿读的是"当前近 72h 在动什么"，
  累积会把陈旧项混进注入＝制造噪声（Hermes「接了制造噪声」判例 → 阈值闸精神）。
- "新建"判据用 git 出生（首次 Add 提交时间），⛔凭 mtime 猜新建（方案 §三 P0.1 明令）。

家族形态（复用先例）：launchd 承载照 com.buluotuo.* 家族（如 com.buluotuo.semantic-radar）。
失败默认放行（Hook/守卫三纪律）：任何异常 exit 0，绝不因雷达坏而堵链路。

用法：
  python3 philosophy_radar.py                 # 默认 72h 窗口扫描并覆盖写 jsonl
  python3 philosophy_radar.py --window-hours 168 --print   # 自验：放宽窗口 + 人读打印
  PHILO_RADAR_WINDOW_H=168 python3 philosophy_radar.py      # 环境变量亦可
"""
import sys
import os
import re
import json
import argparse
import subprocess
from datetime import datetime

HOME = os.path.expanduser("~")
BLUEPRINT = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆蓝图")
REPO_ROOT = os.path.expanduser("~")            # 记忆蓝图属此 git 仓（实测 rev-parse）
DEFAULT_OUT = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "logs", "philosophy_radar.jsonl")
DEFAULT_WINDOW_H = 72

# 排除项（活源判据）：备份噪声 + 随包快照——路径子串命中即跳过
EXCLUDE_SUBSTR = ("发布库",)
EXCLUDE_NAME_MARKS = (".bak", "~")
# 域 = 记忆蓝图下 0X_ 前缀首层目录（00_系统总览 ~ 05）
DOMAIN_RE = re.compile(r"^0[0-9]_")


def _window_hours(cli_val):
    if cli_val is not None:
        return cli_val
    env = os.environ.get("PHILO_RADAR_WINDOW_H", "").strip()
    if env:
        try:
            return float(env)
        except ValueError:
            pass
    return DEFAULT_WINDOW_H


def version_head(path):
    """从文件头提取版本：优先 frontmatter version:，其次行首 # version:，最后首个 v\\d 号；取不到标 '?'。"""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            head = "".join(f.readlines()[:60])
    except Exception:
        return "?"
    m = re.search(r"^version:\s*[\"']?([vV][\w.\-]+)", head, re.M)      # frontmatter
    if m:
        return m.group(1)
    m = re.search(r"^#\s*version:\s*([vV][\w.\-]+)", head, re.M)         # 行首版本注
    if m:
        return m.group(1)
    m = re.search(r"[vV]\d+(?:\.\d+)*", head)                            # 兜底首个版本号
    return m.group(0) if m else "?"


def git_birth_ts(relpath):
    """git 出生时间戳（首次 Add 提交的 commit 时间·秒）。返回 (born_ts|None, untracked:bool)。
    空输出 = 该文件不在 git 历史（未跟踪/未提交）→ 视为新建。"""
    try:
        out = subprocess.run(
            ["git", "-C", REPO_ROOT, "log", "--diff-filter=A", "--reverse",
             "--format=%ct", "--", relpath],
            capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return None, True
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        if not lines:
            return None, True          # git 有仓但该路径从无 Add 记录 → 未入库
        return int(lines[0]), False    # --reverse 首条即最早 Add
    except Exception:
        return None, True


def iter_md(window_s, now_s):
    """遍历记忆蓝图全域 .md，yield (abspath, rel_to_home, domain, mtime_s)。窗口外不产出。"""
    if not os.path.isdir(BLUEPRINT):
        return
    for dirpath, dirnames, filenames in os.walk(BLUEPRINT):
        # 就地裁剪排除目录（发布库/隐藏目录），减少下钻
        dirnames[:] = [d for d in dirnames
                       if not any(x in d for x in EXCLUDE_SUBSTR) and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            if any(m in fn for m in EXCLUDE_NAME_MARKS):
                continue
            full = os.path.join(dirpath, fn)
            if any(x in full for x in EXCLUDE_SUBSTR):
                continue
            try:
                mtime_s = os.path.getmtime(full)
            except Exception:
                continue
            if now_s - mtime_s > window_s:
                continue
            rel_home = os.path.relpath(full, HOME)
            # 域 = 记忆蓝图相对路径首段（0X_）
            sub = os.path.relpath(full, BLUEPRINT)
            domain = sub.split(os.sep, 1)[0] if DOMAIN_RE.match(sub.split(os.sep, 1)[0]) else "根"
            yield full, rel_home, domain, mtime_s


def scan(window_h, out_path):
    now_s = datetime.now().timestamp()
    window_s = window_h * 3600.0
    records = []
    for full, rel_home, domain, mtime_s in iter_md(window_s, now_s):
        rel_repo = os.path.relpath(full, REPO_ROOT)
        born_ts, untracked = git_birth_ts(rel_repo)
        if untracked:
            is_new, born = True, None
        elif born_ts is not None and (now_s - born_ts) <= window_s:
            is_new, born = True, datetime.fromtimestamp(born_ts).strftime("%Y-%m-%d")
        else:
            is_new, born = False, (datetime.fromtimestamp(born_ts).strftime("%Y-%m-%d")
                                   if born_ts else None)
        records.append({
            "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "file": rel_home,
            "domain": domain,
            "version": version_head(full),
            "born": born,                       # git 出生日（未入库=None）
            "new": is_new,                       # 近窗口内出生 = 新建
            "mtime": datetime.fromtimestamp(mtime_s).strftime("%Y-%m-%dT%H:%M:%S"),
            "mtime_s": round(mtime_s, 1),
        })
    records.sort(key=lambda r: r["mtime_s"], reverse=True)     # 最新在前

    tmp = out_path + ".tmp"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, out_path)                   # 原子覆盖（读到的一直是完整快照）
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-hours", type=float, default=None,
                    help="变动窗口（默认 72，可用环境变量 PHILO_RADAR_WINDOW_H 覆盖）")
    ap.add_argument("--out", default=DEFAULT_OUT, help="输出 jsonl 路径")
    ap.add_argument("--print", dest="do_print", action="store_true", help="扫描后人读打印结果")
    args = ap.parse_args()
    try:
        wh = _window_hours(args.window_hours)
        recs = scan(wh, args.out)
        if args.do_print:
            print("哲学变更雷达（窗口 %gh）→ %s：命中 %d 项" % (wh, args.out, len(recs)))
            for r in recs:
                flag = "新建" if r["new"] else "改"
                print("  [%s] %s ｜域 %s ｜版本 %s ｜动于 %s"
                      % (flag, r["file"], r["domain"], r["version"], r["mtime"]))
    except Exception as e:
        sys.stderr.write("philosophy_radar 异常（默认放行·不阻断）：%s\n" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
