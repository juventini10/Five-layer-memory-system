#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# TRUTH_OF: 脚本中心/position3_notify.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""position3_notify.py — 岗位3 对账异常的对话主动触达钩子（UserPromptSubmit）。

设计定位（2026-08-29 你质证"不要依赖我的记性"·愿景①根治）：
  岗位3 对账报告若只躺文件里，"每周瞄一眼"仍是记性依赖——告警必须长到你每天
  必然经过的通道：对话注入。你开口即看到一行提醒，异常处置后自动消失。

行为：
  读 steps/position3-audit-log.jsonl 末条——red>0 → 注入一行触达（含报告路径）；
  超 7 天未处置升级措辞；red=0 / 无台账 / 任何异常 → 静默放行（零噪音）。
节流：无状态每次注入一行（一行成本·异常清零即消失——处置激励内建）。
纪律：失败默认放行 exit 0 · 只读不改 · 端感知输出（ZCode=additionalContext JSON·其他端=纯文本）。
"""
import json
import os
import sys
from datetime import datetime

_DT_STEPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "steps")  # 自推导·两环境同构（scripts/与devtools/的上级都是数字分身/·2026-09-30 by ZCode）
AUDIT_LOG = os.path.join(_DT_STEPS, "position3-audit-log.jsonl")
REPORT = os.path.join(_DT_STEPS, "position3-reconciliation-report.md")


# ── 输出协议单一真源（2026-09-04 根治·Qoder CN 裸文本被产品判 "winner=none" 丢弃）──
for _p in (os.path.expanduser("[记忆共享中心]/脚本中心"), os.path.expanduser("[记忆共享中心]/脚本中心")):  # 双路径·hook_protocol 作者侧/用户侧（2026-09-30 by ZCode）
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
try:
    import hook_protocol as _hp
except Exception:
    _hp = None


def _emit(ctx):
    """输出协议委托 hook_protocol 单一真源（2026-09-04 根治）。

    ⛔ 本脚本不读 stdin（避免钩子阻塞对话·原有纪律），故判端依赖**挂载命令显式声明**
    `--hook-protocol=json`（Qoder CN 配置里声明）；未声明 → 默认 text
    （WorkBuddy 实测吃 text·零回归）。
    """
    if _hp is not None:
        _hp.emit(ctx, payload={}, argv=sys.argv[1:],
                 event="UserPromptSubmit", script=os.path.basename(__file__))
        return
    sys.stdout.write(ctx)


def main():
    try:
        if not os.path.exists(AUDIT_LOG):
            return
        last = None
        with open(AUDIT_LOG, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
        if not last:
            return
        r = json.loads(last)
        red = int(r.get("red", 0))
        if red <= 0:
            return
        ts = str(r.get("ts", ""))[:10]
        age_days = None
        try:
            age_days = (datetime.now() - datetime.strptime(ts, "%Y-%m-%d")).days
        except ValueError:
            pass
        urgency = "⚠️已超7天未处置" if (age_days is not None and age_days > 7) else "待处置"
        _emit("📋 岗位3对账（%s 第%s轮）：🔴%d 处声明-实盘脱钩%s → 报告 %s（处置后下轮对账自动消除提醒）"
              % (ts, r.get("round", "?"), red, urgency,
                 REPORT.replace(os.path.expanduser("~"), "~")))
    except Exception:
        pass  # 失败放行·绝不阻塞对话


if __name__ == "__main__":
    main()
    sys.exit(0)
