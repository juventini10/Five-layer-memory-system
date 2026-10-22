#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto_write_audit.py — JOB-003 自动写入标记审计（v1.0·2026-10-22）

用途（愿景红线：自主≠黑箱，可观测/可抽检/可收回）：
  1) 清点：扫描记忆蓝图/成长箱 中所有 `auto_written_by=JOB-003` 标记块
  2) 校验：每块须带 决策ID + 回退指针 + 来源/TTL，且决策ID在反哺日志可查
  3) 回退指令：--revert-dryrun 打印各块删除指引（⛔不自动删，删除动作归人）
用法：python3 scripts/auto_write_audit.py [--json] [--revert-dryrun]
退出码：0=全部合规；1=存在缺件或账上查无。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import io, os, re, sys, json, argparse

HOME = os.path.expanduser("~")
ROOTS = [os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "02_设计理念"), os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆蓝图", "03_开发规范")]  # 只扫实际写入目标域（登记定义行/历史日志非写入块·排除）
LOG = os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱", "experience", "规范反哺日志.md")
MARK = "auto_written_by=JOB-003"

def blocks():
    out = []
    for root in ROOTS:
        for dp, _, fs in os.walk(root):
            if "/归档" in dp or "Trash" in dp:
                continue
            for fn in fs:
                if not fn.endswith(".md"):
                    continue
                if ("JOB-003-第二阶段" in fn) or fn.startswith("09-童灵"):
                    continue  # 登记/定义件非写入块
                p = os.path.join(dp, fn)
                try:
                    lines = io.open(p, encoding="utf-8").read().split("\n")
                except Exception:
                    continue
                for i, ln in enumerate(lines):
                    if MARK in ln:
                        ctx = "\n".join(lines[max(0, i-15): i+25])
                        ids = re.findall(r"JOB-003-\d{8}-\d{3}", ctx)
                        has_rb = ("回退" in ctx)
                        has_src = ("[来源:" in ctx or "来源标注" in ctx)
                        has_ttl = ("TTL" in ctx)
                        title = ""
                        for k in range(i, max(0, i-25), -1):
                            if lines[k].startswith("### ") or lines[k].startswith("## "):
                                title = lines[k].strip(); break
                        out.append({"file": os.path.relpath(p, HOME), "line": i+1, "title": title,
                                    "decision": ids[0] if ids else "", "rollback": has_rb,
                                    "source": has_src, "ttl": has_ttl})
    # 去重：同一文件同一决策ID同一标题只算一块（标记可能出现在块头与变更记录两处）
    seen, uniq = set(), []
    for b in out:
        k = (b["file"], b["decision"], b["title"])
        if k in seen:
            continue
        seen.add(k); uniq.append(b)
    return uniq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--revert-dryrun", action="store_true")
    a = ap.parse_args()
    log = io.open(LOG, encoding="utf-8").read() if os.path.isfile(LOG) else ""
    bs = blocks()
    bad = []
    for b in bs:
        if not b["decision"] or b["decision"] not in log:
            bad.append((b, "决策ID缺失或账上查无"))
        if not b["rollback"]:
            bad.append((b, "缺回退指针"))
        if not b["source"]:
            bad.append((b, "缺来源标注"))
        if not b["ttl"]:
            bad.append((b, "缺TTL"))
    if a.json:
        print(json.dumps({"blocks": bs, "bad": [(x[0]["file"], x[0]["line"], x[1]) for x in bad]}, ensure_ascii=False, indent=1))
    else:
        print("自动写入标记清点：%d 块" % len(bs))
        for b in bs:
            print("  - %s:%d ｜ %s ｜ 决策ID=%s ｜ 回退=%s ｜ 来源=%s ｜ TTL=%s" % (
                b["file"], b["line"], b["title"] or "-", b["decision"] or "-",
                "有" if b["rollback"] else "缺", "有" if b["source"] else "缺", "有" if b["ttl"] else "缺"))
        if a.revert_dryrun:
            print("回退指令（dry-run·不执行）：")
            for b in bs:
                print("  删 %s 中「%s」块（决策ID %s）→ 同步反哺日志状态" % (b["file"], b["title"] or "-", b["decision"]))
    if bad:
        print("AUDIT:FAIL %d 处：" % len(bad), file=sys.stderr)
        for b, why in bad:
            print("   %s:%d %s" % (b["file"], b["line"], why), file=sys.stderr)
        return 1
    print("AUDIT:OK 全部标记合规（决策ID可查/回退/来源/TTL 齐）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
