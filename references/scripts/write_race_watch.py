#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
write_race_watch.py — 恢复式写入竞态侦测器（v1.0.0·2026-09-18·工单 §六 D5 根治）

治什么病（不是猜测，是本轮实测撞到的）：
  多端共写同一仓库（家目录 个人AI档案 被 10+ 端读写），出现过一种形态：
  **文件内容变了，mtime 反而变旧**（P-L1b 实录）——这是"某端把整文件按旧快照
  恢复式重写"的指纹，等于把别人的新改动静默吞掉（丢更新）。
  此前只有事后 git 对账能看见，⛔没有任何机制在"下一次"当场逮住它。

第一性原理：判据不能靠被检对象自述（同抗体域 C1-C7 的教训）。
  → 本侦测器自己不做判定的"真值"，只留**双向指纹台账**（mtime + 内容 sha256），
    git 才是仲裁者：异常态一律附 `git log -1 -- <file>` 的 HEAD 指纹供对账。

三类异常（各对应一种真实成因·⛔不合并成一句"有问题"）：
  R1 内容变 + mtime 变旧        → 恢复式写入（丢更新嫌疑·最高危）
  R2 内容变 + mtime 未变        → 同刻双写/时钟回拨（mtime 失去判别力）
  R3 内容未变 + mtime 变新很多  → 触碰式重写（touch 噪音·低危只显形）
  R4 内容未变 + 索引位从有到无  → 丢档（他端 reset / rm --cached·v1.1.0 新增）

用法：
  python3 write_race_watch.py scan            # 扫受监控清单→比对→写台账/显形
  python3 write_race_watch.py check           # 读台账报最近异常（供日报/通知消费）
  python3 write_race_watch.py --self-test     # 造 R1/R2/R3/正常 四态夹具自测
写域：仅 成长箱/竞态台账.jsonl + 成长箱/learnings/write_race_watch_state.json
"""
import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
from datetime import datetime

VERSION = "1.1.0"
HOME = os.path.expanduser("~")
BASE = os.path.expanduser("[记忆共享中心]")
LEDGER = os.path.join(BASE, "成长箱", "竞态台账.jsonl")
STATE = os.path.join(BASE, "成长箱", "learnings", "write_race_watch_state.json")
# 受监控清单：本轮实测出竞态痕迹 + 多端共写热点（⛔不写死全库扫描，成本与噪音都不可控）
WATCH = [
    "成长箱/免疫修复工单.md",
    "成长箱/learnings/CANDIDATES.md",
    "成长箱/learnings/ERRORS.md",
    "成长箱/experience/规范反哺日志.md",
    "成长箱/跨域日报.md",
    "变更日志.md",
    "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md",
    "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/02-脚本家族实例/守卫家族实例.md",
    "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md",
]
BIG_SKIP = 2_000_000  # >2MB 不入库指纹（成本闸·报告里显式标跳过数）


def _sha(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()[:16]


def _git_head(rel):
    """git 仲裁位：HEAD 中该文件最后提交号（读不到返回 '-'，⛔不猜）。"""
    try:
        r = subprocess.run(["git", "-C", BASE, "log", "-1", "--format=%h", "--", rel],
                           capture_output=True, text=True, timeout=20)
        return (r.stdout or "").strip() or "-"
    except (OSError, subprocess.TimeoutExpired):
        return "-"


def classify(prev, cur):
    """四态判据（纯机械·返回 None=正常）。prev/cur = {"sha","mtime"}。"""
    if prev is None or cur is None or cur.get("sha") is None:
        return None
    same = prev["sha"] == cur["sha"]
    dt = cur["mtime"] - prev["mtime"]
    if not same and dt < 0:
        return "R1"          # 内容变、mtime 反旧 = 恢复式写入
    if not same and abs(dt) < 1:
        return "R2"          # 内容变、mtime 不动 = mtime 失去判别力
    if same and dt > 3600:
        return "R3"          # 内容没变、时间跳新 = touch 噪音
    return None


def load_prev():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f).get("files", {})
    except (OSError, ValueError):
        return {}


def tracked(rel, repo=None):
    """git 索引位探针：文件在索引里=1，不在=0，取不到=空（⛔不猜）。"""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", repo or BASE, "ls-files", "--", rel],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return "1" if (r.stdout or "").strip() else ("0" if r.returncode == 0 else "")


def classify_index(prev_tracked, cur_tracked):
    """R4 判据：曾被 git 索引跟踪 → 现不在索引 = 丢档（他端 reset/rm --cached 或 add 未落）。

    为什么内容层三态不够（2026-09-18 实测）：`write_race_watch.py` 与 `growth_chain.sh`
    本端 `git add` 后复扫回到 `??`（索引被并发改动冲掉），内容一字未变 ⇒ R1/R2/R3 全哑，
    只有 §3.0 件① 孤儿检查抓得到，但那是「每日一次」的粗网，不是当场显形。
    """
    if prev_tracked == "1" and cur_tracked == "0":
        return "R4"
    return None

def scan(now=None):
    prev = load_prev()
    cur, events, skipped = {}, [], 0
    for rel in WATCH:
        p = os.path.join(BASE, rel)
        if not os.path.isfile(p):
            continue
        if os.path.getsize(p) > BIG_SKIP:
            skipped += 1
            continue
        sha = _sha(p)
        mtime = os.path.getmtime(p)
        tr = tracked(rel)
        cur[rel] = {"sha": sha, "mtime": mtime, "tracked": tr}
        kind = classify(prev.get(rel), {"sha": sha, "mtime": mtime})
        if kind is None:
            kind = classify_index((prev.get(rel) or {}).get("tracked"), tr)
            if kind:
                cur[rel]["note"] = "索引丢档（内容未变·件①被冲）"
        if kind:
            ev = {"ts": (now or datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                  "kind": kind, "file": rel, "sha_prev": prev.get(rel, {}).get("sha"),
                  "sha_cur": sha, "git_head": _git_head(rel)}
            if cur[rel].get("note"):
                ev["note"] = cur[rel]["note"]
            events.append(ev)
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump({"version": VERSION, "last_run": datetime.now().isoformat(timespec="seconds"),
                   "files": cur}, f, ensure_ascii=False, indent=1)
    if events:
        with open(LEDGER, "a", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    hi = [e for e in events if e["kind"] in ("R1", "R2", "R4")]
    print("write_race_watch: 监控 %d 项·跳过 %d·异常 %d（高危 %d）" % (len(cur), skipped, len(events), len(hi)))
    for e in events:
        print("  %s %s git=%s %s（%s→%s）" % ("🔴" if e["kind"] != "R3" else "⚪",
              e["kind"], e["git_head"], e["file"], e["sha_prev"], e["sha_cur"]))
    return 1 if hi else 0


def check():
    if not os.path.isfile(LEDGER):
        print("write_race_watch: 台账未建立（尚无异常记录）")
        return 0
    rows = []
    with open(LEDGER, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    hi = [r for r in rows if r.get("kind") in ("R1", "R2", "R4")]
    print("write_race_watch 台账：共 %d 条·高危(R1/R2) %d 条·最近 %s"
          % (len(rows), len(hi), rows[-1]["ts"] if rows else "-"))
    for r in hi[-5:]:
        print("  🔴 %s %s git=%s" % (r["ts"], r["kind"], r["file"]))
    return 1 if hi else 0


def self_test():
    """四态夹具：正常/R1/R2/R3 必须各归各位（含"⛔恒真"负例——同 sha 同 mtime 不得报）。"""
    global BASE, WATCH, LEDGER, STATE
    bad = []
    base = {"sha": "a" * 16, "mtime": 1000.0}
    if classify(base, {"sha": "a" * 16, "mtime": 1000.0}) is not None:
        bad.append("正常态误报（恒真嫌疑）")
    if classify(base, {"sha": "b" * 16, "mtime": 900.0}) != "R1":
        bad.append("R1 未识别（内容变+mtime 旧）")
    if classify(base, {"sha": "b" * 16, "mtime": 1000.0}) != "R2":
        bad.append("R2 未识别（内容变+mtime 不动）")
    if classify(base, {"sha": "a" * 16, "mtime": 5000.0}) != "R3":
        bad.append("R3 未识别（touch 噪音）")
    if classify(base, {"sha": "a" * 16, "mtime": base["mtime"] + 60}) is not None:
        bad.append("R3 阈值边界误报（同内容+60 秒内 touch 不该报）")
    if classify(None, base) is not None:
        bad.append("首轮无基线却报异常（首跑风暴嫌疑）")
    if classify(base, {"sha": None, "mtime": 1.0}) is not None:
        bad.append("读不到内容却报异常（缺数据当证据）")
    # R4 端到端：真临时 git 仓库，add 后 reset 掉索引 → 必须报 R4
    repo = tempfile.mkdtemp(prefix="wrw_repo_")
    r4tmp = tempfile.mkdtemp(prefix="wrw_r4_")
    try:
        import subprocess
        subprocess.run(["git", "init", "-q", repo], capture_output=True, timeout=30)
        rel = "f.md"
        pathlib.Path(os.path.join(repo, rel)).write_text("内容A\n", encoding="utf-8")
        subprocess.run(["git", "-C", repo, "add", rel], capture_output=True, timeout=30)
        gb, gs, gl = BASE, STATE, LEDGER
        BASE, STATE, LEDGER = repo, os.path.join(r4tmp, "r4_state.json"), os.path.join(r4tmp, "r4_ledger.jsonl")
        WATCH2 = list(WATCH)
        globals()["WATCH"] = [rel]
        devnull = open(os.devnull, "w"); old_stdout = sys.stdout; sys.stdout = devnull
        try:
            scan()  # 建基线（tracked=1）
            subprocess.run(["git", "-C", repo, "rm", "--cached", "-q", "-f", rel], capture_output=True, timeout=30)
            scan()  # 内容未变、索引丢档 → R4
        finally:
            sys.stdout = old_stdout; devnull.close()
            BASE, STATE, LEDGER = gb, gs, gl
            globals()["WATCH"] = WATCH2
        rows4 = [json.loads(l) for l in open(os.path.join(r4tmp, "r4_ledger.jsonl"), encoding="utf-8")] \
            if os.path.isfile(os.path.join(r4tmp, "r4_ledger.jsonl")) else []
        if not any(r.get("kind") == "R4" for r in rows4):
            bad.append("T5 R4 未端到端捕获索引丢档（内容未变那类竞态测不到）")
    except Exception as exc:
        bad.append("T5 R4 端到端跑不起来：%s（⛔不当通过）" % exc)
    finally:
        import shutil as _sh
        _sh.rmtree(r4tmp, ignore_errors=True)
        _sh.rmtree(repo, ignore_errors=True)
    # 写域断言：scan/check 不得触碰受监控文件本体
    before = {os.path.join(BASE, r): os.path.getmtime(os.path.join(BASE, r))
              for r in WATCH if os.path.isfile(os.path.join(BASE, r))}
    real = (LEDGER, STATE)
    tmp = tempfile.mkdtemp(prefix="wrw_selftest_")
    LEDGER = os.path.join(tmp, "ledger.jsonl")
    STATE = os.path.join(tmp, "state.json")
    try:
        out = sys.stdout
        devnull = open(os.devnull, "w")
        sys.stdout = devnull
        try:
            scan()
            scan()
        finally:
            sys.stdout = out
            devnull.close()
    finally:
        LEDGER, STATE = real
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    for p, mt in before.items():
        if os.path.getmtime(p) != mt:
            bad.append("越权写入受监控文件：%s" % os.path.basename(p))
    if bad:
        print("SELF-TEST FAIL：")
        for x in bad:
            print("  ✗ " + x)
        return 1
    print("SELF-TEST PASS（T1 四态各归位+R3 阈值边界·T2 无基线不报·T3 缺数据不报·T5 R4 索引丢档端到端·T4 写域零越权·连跑两遍幂等）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="恢复式写入竞态侦测器 v%s" % VERSION)
    ap.add_argument("mode", nargs="?", default="scan", choices=["scan", "check"])
    ap.add_argument("--self-test", action="store_true", dest="selftest")
    args = ap.parse_args()
    if args.selftest:
        return self_test()
    if args.mode == "check":
        return check()
    return scan()


if __name__ == "__main__":
    sys.exit(main())
