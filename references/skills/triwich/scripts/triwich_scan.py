#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: skip=triwich Skill 包内预算工具件（非脚本中心独立守卫族）·挂载与守卫S4接入随任务卡2026-10-20议题⑥条款落 SKILL.md 时统一登记
"""triwich_scan.py — 三明智 L3 盘点类检索的物理预算闸门（v1.0 · 2026-10-20）

设计哲学（Poka-Yoke 功能法·非 contact 警示法）：
  预算不是条款，是物理。不经过本工具的裸 grep 全域转储，靠"台账留痕 vs 结论数字"
  对账显形（绕过留痕=绕过成本>遵守成本，与 Step0 键铸造同构）。
  实证起因：案1 轮 20261020_211758——Agent A 裸扫描落盘 raw 约250MB，
  38 分钟未进思维本体；Agent B 有 120s 保险丝，Agent A 零条款（全包 grep 坐实）。

硬预算（物理内置；闸门拦走门者，绕闸裸 grep 靠 S4 台账对账留痕显形——⛔不宣称杜绝，纯AI环境诚实边界见 Skill架构规范 §1.1）：
  ①超时→杀进程 rc=124        ②输出→行数上限截断并显式报告
  ③扫描面→默认排除名单       ④同轮重扫→指纹命中即拒，须 --force 带理由
  ⑤失败与零命中严格区分（grep rc=1 = 查成功无命中，exit 0；工具缺失/路径不存在 = exit 非0）

TRUTH_OF: 本脚本的预算常量为唯一真源；SKILL.md 条款只引用本入口，不复制参数值（防双本账）。
挂账项: 守卫 S4 对账（键文件无 scan 台账却出盘点结论=签名造假）待条款落 SKILL.md 后接入
        triwich_closeout_guard；见任务卡 2026-10-20-三明智分析端补强 §议题⑥。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass


import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

# ── 预算常量（唯一真源·调参从实跑台账数据出发，不拍脑袋）──
DEFAULT_TIMEOUT = 30        # 秒·单次检索动作上限（案1教训：无上限=38分钟）
DEFAULT_MAX_LINES = 2000    # 输出行上限（超出截断，⛔全文转储不落盘）
MAX_CAPTURE_BYTES = 64 * 1024 * 1024  # 临时输出文件硬顶（防内存/磁盘爆炸）

# 默认排除（目录名 glob 匹配）——要扫这些域须 --include-excluded 并带理由，理由进台账
DEFAULT_EXCLUDES = [
    "__pycache__", ".git", "node_modules", ".venv", "venv", ".obsidian",
    "*记忆琥珀*", "*琥珀*", "*归档*", "*存档*", "*backup*", "*bak*",
    "*Trash*", "*回收站*",
]


def build_command(mode, pattern, roots, excludes, context):
    """优先 rg（更快更准的 glob 排除），无 rg 回退 grep。返回 argv。"""
    if shutil.which("rg"):
        cmd = ["rg", "--no-heading"]
        if mode == "list":
            cmd.append("-l")
        else:
            cmd += ["-n", "-C", str(context)]
        for g in excludes:
            cmd += ["-g", f"!**/{g}/**", "-g", f"!{g}"]
        cmd += ["--", pattern]
        cmd += [os.path.expanduser(r) for r in roots]
        return cmd
    # grep 回退（--exclude-dir 仅支持目录 basename 级 glob，粒度略粗，如实声明）
    cmd = ["grep", "-rnE" if mode == "ctx" else "-rlE"]
    for e in excludes:
        if "*" in e or "/" in e:
            core = e.strip("*").split("/")[-1]
            cmd += ["--exclude-dir", core or e]
        else:
            cmd += ["--exclude-dir", e]
    cmd += ["--", pattern]
    cmd += [os.path.expanduser(r) for r in roots]
    return cmd


def fingerprint(mode, pattern, roots, excludes):
    raw = "|".join([mode, pattern, ",".join(sorted(roots)), ",".join(sorted(excludes))])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def check_rescan(ledger_path, ts, fp):
    """同轮同指纹已查过 → True（须 --force 才放行）。台账不存在/无本轮记录 → False。"""
    if not os.path.isfile(ledger_path):
        return False
    try:
        with open(ledger_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if f"ts={ts}" in line and f"fp={fp}" in line:
                    return True
    except OSError:
        pass
    return False


def append_ledger(ledger_path, row):
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(row + "\n")


def main():
    ap = argparse.ArgumentParser(description="三明智盘点检索·物理预算闸门")
    ap.add_argument("--mode", choices=["list", "ctx"], default="list",
                    help="list=只列命中文件（默认·分级令第一段）；ctx=命中行+上下文（第二段）")
    ap.add_argument("--pattern", required=True, help="检索模式（rg/grep -E 语法）")
    ap.add_argument("--root", action="append", required=True, dest="roots",
                    help="扫描根，可多次传入（多域显式列举，⛔整个家目录一把梭）")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    ap.add_argument("--context", type=int, default=1, help="ctx 模式上下文行数")
    ap.add_argument("--include-excluded", action="store_true",
                    help="不跳默认排除名单（须带 --reason 说明为何要扫归档/琥珀等域）")
    ap.add_argument("--reason", default="-", help="越权/重扫理由（进台账·开 --force 必带）")
    ap.add_argument("--force", action="store_true", help="允许同轮重扫同域（必须带 --reason）")
    ap.add_argument("--ts", default=datetime.now().strftime("%Y%m%d_%H"),
                    help="本轮键（三明智运行传 {ts}·重扫检测按轮隔离）")
    ap.add_argument("--ledger", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "scan_ledger.log"),
                    help="预算台账（留痕唯一载体·换机不冒充跨机证据，同 seal.log 策略）")
    args = ap.parse_args()

    excludes = [] if args.include_excluded else DEFAULT_EXCLUDES
    if args.force and args.reason == "-":
        print("❌ --force 必须带 --reason（为何第一遍结果不可复用）。Fail-Loud，拒绝。")
        return 14
    fp = fingerprint(args.mode, args.pattern, args.roots, excludes)
    if not args.force and check_rescan(args.ledger, args.ts, fp):
        print(f"🔴 同轮重扫拦截 fp={fp} ts={args.ts}：该域+该模式本轮已扫过。\n"
              f"   复用台账里第一遍的结果；确需重扫 → --force --reason '理由'。")
        return 13
    for r in args.roots:
        if not os.path.exists(os.path.expanduser(r)):
            print(f"❌ 扫描根不存在: {r}（工具失败≠零命中，不静默）")
            return 2
    cmd = build_command(args.mode, args.pattern, args.roots, excludes, args.context)
    if cmd is None:
        print("❌ rg 与 grep 均不可用——检索工具缺失，中止而非降级成无预算扫描")
        return 3

    t0 = time.time()
    timed_out = False
    with tempfile.NamedTemporaryFile("w+", suffix=".triwich_scan", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with open(tmp_path, "w", encoding="utf-8", errors="replace") as out:
            proc = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE,
                                  timeout=args.timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        rc = 124
    finally:
        size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        oversize = size > MAX_CAPTURE_BYTES
        if oversize:
            os.unlink(tmp_path)  # 超硬顶：原始转储直接丢弃不落盘不回显（防案1式250MB污染）
    elapsed = time.time() - t0

    lines, trunc = [], 0
    if os.path.isfile(tmp_path):
        with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i < args.max_lines:
                    lines.append(line)
                else:
                    trunc += 1
        os.unlink(tmp_path)

    # 区分：rc=1 且零输出 = 查成功无命中（rg/grep 约定）；其余非零 = 检索异常
    if rc == 1 and not lines and not timed_out:
        rc, status = 0, "no_hit(查成功·非失败)"
        lines.append("ℹ️ 零命中（查询成功，确无匹配）——零命中≠不存在≠查询失败，三态不混\n")
    else:
        status = "ok" if rc == 0 else ("timeout_killed" if timed_out else f"rc={rc}")
    if trunc:
        lines.append(f"⚠️ 已截断 {trunc} 行（max-lines={args.max_lines}）——命中量=规模信号，"
                     f"收窄 pattern/root 再钻第二段，⛔把截断当全量下结论\n")
    if timed_out:
        lines.append(f"🔴 预算耗尽：{args.timeout}s 未扫完已杀。要么收窄扫描面，"
                     f"要么显式声明理由重跑——⛔静默等待=今晚案1重演\n")
    sys.stdout.write("".join(lines))

    # F6（v1.1）：成功态默认落副本文件（免疫终端吞 stdout）；路径进台账行
    out_path = "-"
    if status == "ok" or status.startswith("no_hit"):
        try:
            out_dir = os.path.join(os.path.expanduser("~"), ".cache", "triwich_scan", "out")  # ⛔不进 Skill 包（防 file_clutter）
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "%s_%s.txt" % (args.ts, fp))
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("".join(lines))
        except Exception:
            out_path = "-"
    append_ledger(args.ledger,
                  f"scan|ts={args.ts}|t={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                  f"|mode={args.mode}|fp={fp}|pattern={args.pattern}|roots={len(args.roots)}"
                  f"|status={status}|elapsed={elapsed:.1f}s|lines={len(lines)}"
                  f"|truncated={trunc}|excludes={'off' if args.include_excluded else 'on'}"
                  f"|reason={args.reason}|out={out_path}")
    if oversize:
        print(f"🔴 原始命中体量超硬顶 {size}B——转储已丢弃不回显（物理防案1式污染）。"
              f"该域命中密度异常，须收窄 pattern/root 重查；结论只可按抽样声明，⛔按全量断言")
    return 0 if not timed_out else 124


if __name__ == "__main__":
    sys.exit(main())
