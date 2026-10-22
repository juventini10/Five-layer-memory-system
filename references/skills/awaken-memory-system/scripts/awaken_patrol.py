#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: skip Skill运行执行体（awaken-memory-system 管辖·patrol.md §3 规格件），非守卫/registry 资产，版本纪律走本 Skill CHANGELOG
"""awaken_patrol.py — 记忆健康自动巡检执行体（平台中立·mac/Win 共享同一份）

规格锚点：references/patrol.md §3 · 8.4.0 Win 对等件根治（任务卡 2026-10-21-唤醒巡检Win对等件根治）
先例判据：slice-watch「执行体同一份平台中性 python·单一真源⛔ps1/sh 逻辑副本」——
  awaken_patrol.sh 已降为薄壳转发本文件，两载体（launchd / Task Scheduler）都只调本 py。
职责（与 .sh 原逻辑逐段对应·四段留痕格式不变·dashboard 解析零改动兼容）：
  ①快照滞后检查 → update_snapshot_from_diary.py（exit 0/2/其他 语义原样保留·patrol.md §1）
  ②蒸馏待办三级检测 → awaken_distill_due_check.py（patrol.md §2）
  ③触达：mac=osascript 弹窗；Win/其他=pending 告警文件+日志留痕，会话内由唤醒轻量转述（§4）
  ④[完成] 收尾行
纪律：⛔不写他者文件（自有日志/pending 属职责内）·失败显形（假绿防线）·可观测·可收回（卸载体即停）
调用：载体负责环境清洗（launchd 模板 / install-task.ps1 均剥 PYTHONHOME/PYTHONPATH）；
     本脚本对自身 subprocess 同样清洗（双保险·与 .sh env -u 同口径）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import datetime
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_DIR = Path.home() / "buluotuo_bin" / "log"
LOG_FILE = LOG_DIR / "awaken_patrol.log"
PENDING_FILE = LOG_DIR / "awaken_patrol_alerts.pending"


def _clean_env():
    env = os.environ.copy()
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    return env


def _run(script, args=()):
    """跑同目录脚本 → CompletedProcess(stdout 捕获)；自身 env 清洗，stdout 不污染日志。"""
    return subprocess.run([sys.executable, str(SCRIPT_DIR / script), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=_clean_env())


class Patrol:
    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        # 一轮一个时间戳（与 .sh 的 NOW 语义一致：四段留痕同轮同刻·dashboard 按日期窗口聚合）
        self.stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.alerts = []      # 触达层告警原文（不含 DUE| 技术前缀）
        self.snap_state = "skip"

    def log(self, text):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{self.stamp} {text}\n")

    # ── ① 快照滞后检查（复用现成脚本·⛔不复制逻辑·SSOT 在 patrol.md §1）──
    def check_snapshot(self):
        snap = SCRIPT_DIR / "update_snapshot_from_diary.py"
        if not snap.is_file():
            self.snap_state = "missing"
            self.log(f"[快照] 脚本缺失: {snap}")
            self.alerts.append("【快照缺口】update_snapshot_from_diary.py 缺失")
            return
        try:
            r = _run("update_snapshot_from_diary.py")
        except OSError as exc:
            self.snap_state = "fail"
            self.log(f"[快照] 更新失败（无法启动: {exc}）→ 数据可能滞后")
            self.alerts.append("【快照缺口】快照更新脚本无法启动，数据可能滞后")
            return
        rc = r.returncode
        if rc == 0:
            self.snap_state = "updated"
            self.log("[快照] 已更新（exit 0）")
        elif rc == 2:
            self.snap_state = "uptodate"
            self.log("[快照] 无需更新（exit 2）")
        else:
            self.snap_state = "fail"
            self.log(f"[快照] 更新失败（exit {rc}）→ 数据可能滞后")
            self.alerts.append(f"【快照缺口】快照更新失败(exit {rc})，数据可能滞后")
        # .sh 里快照脚本输出直接 >>LOG_FILE；py 版捕获后原样转写（stdout 空则跳过）
        if r.stdout.strip():
            for line in r.stdout.splitlines():
                self.log(f"[快照·输出] {line}")

    # ── ② 蒸馏待办三级阈值检测（patrol.md §2 逻辑脚本化）──
    def check_distill(self):
        args = ()
        center = os.environ.get("DISTILL_CENTER_PATH", "").strip()
        if center:
            args = (center,)
        try:
            r = _run("awaken_distill_due_check.py", args)
        except OSError:
            self.log("[蒸馏] 检测失败（脚本无法启动）")
            self.alerts.append("【巡检异常】蒸馏待办检测失败")
            return
        if r.returncode != 0:
            self.log("[蒸馏] 检测失败（脚本非零退出）")
            self.alerts.append("【巡检异常】蒸馏待办检测失败")
            return
        out = r.stdout.strip()
        if out == "NONE":
            self.log("[蒸馏] 无待办（静默）")
            return
        for line in out.splitlines():
            if not line.strip():
                continue
            self.log(f"[蒸馏] {line}")
            # 触达阈值：仅 🟡/🔴 弹窗；🔵 即将到期仅入日志（无事不打扰·防打扰校准）
            if "🔴" in line or "🟡" in line:
                msg = line[4:] if line.startswith("DUE|") else line
                self.alerts.append(msg)

    # ── ③ 触达层：有逾期/缺口才出声·无事不打扰（Fogg 补 P·只提醒不写入）──
    # mac=osascript 弹窗（B-1 原设计）；Win/其他=pending 文件留痕，由唤醒轻量会话内转述
    # （S4U 非交互会话弹不出 toast 是 2026-10-21 任务卡设计决策 a·形态 b 待你拍板可升级）
    # D-3：弹窗/留痕顶部带仪表盘单行摘要（脚本缺失/失败降级=不含摘要不阻塞）
    def touch(self):
        if not self.alerts:
            self.log("[触达] 无事不打扰（静默）")
            return
        joined = " ".join(self.alerts)
        dash = ""
        dash_script = SCRIPT_DIR / "awaken_health_dashboard.py"
        if dash_script.is_file():
            try:
                r = _run("awaken_health_dashboard.py", ("--summary",))
                if r.returncode == 0 and r.stdout.strip():
                    dash = r.stdout.strip()
            except OSError:
                pass
        body = "\n\n".join(x for x in (dash, "\n".join(self.alerts)) if x)
        msg = f"{body}\n\n输入『小美』看详情"
        if sys.platform == "darwin":
            esc = msg.replace("\\", "\\\\").replace('"', '\\"')
            script = f'display notification "{esc}" with title "布洛陀·记忆巡检"'
            try:
                r = subprocess.run(["osascript", "-e", script],
                                   capture_output=True, text=True, env=_clean_env())
                if r.returncode == 0:
                    self.log(f"[触达] 已弹通知（{joined}）·含小美入口")
                else:
                    self.log(f"[触达] 弹窗失败（{joined}）·osascript exit {r.returncode}")
            except OSError as exc:
                self.log(f"[触达] 弹窗失败（{joined}）·osascript 不可启动: {exc}")
        else:
            try:
                PENDING_FILE.write_text(msg + "\n", encoding="utf-8")
                self.log(f"[触达] 告警已记录（{joined}）·pending·待会话内转述")
            except OSError as exc:
                # 失败显形：连留痕都写不进=巡检异常级告警，进日志显眼
                self.log(f"[触达] 告警落盘失败（{joined}）·pending 写入异常: {exc}")

    def finish(self):
        self.log(f"[完成] 巡检结束（快照={self.snap_state}）")


def main():
    p = Patrol()
    p.check_snapshot()
    p.check_distill()
    p.touch()
    p.finish()
    return 0


if __name__ == "__main__":
    sys.exit(main())
