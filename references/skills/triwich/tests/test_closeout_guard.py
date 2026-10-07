#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_closeout_guard.py —— 三明智收尾守卫回归（负例驱动）
Version: 2.0.0 (2026-09-18·身份匹配判定 + 假阳性/假阴性双向回归)

S3 用例补充 (2026-09-18·评估 C-05 修复)：原夹具只重定向 SKILL_DIRS/SAMPLE_LEDGER，
未隔离 DECISION_ROOM → S3 读到真实档案库文件 → 正例[3] 假失败（实测 2026-09-18）。

v2.0.0 (2026-09-18·第一性根治配套)：S1/S3 判定从"时间差+mtime 代理"改为
"登记身份匹配"（台账 seal 指纹 / 决策卡 ts+session）。故夹具**必须提供真凭据**，
否则"好状态"会被正确判为"缺证据"。新增双向回归：
  · 假阴性：台账含 seal 指纹但 mtime 很旧 → 不得报 S1
  · 假阳性：台账 mtime 很新但不含 seal 指纹 → 必须报 S1
这两条是旧判定过不去的（旧判定=纯 mtime），是本次根治的验收锚点。

立场卡依据：S167/S172（判据机制须过负例测试）· C-067（门禁须真机双关）。
单进程纯 python 夹具，避免逐例开子进程打爆沙箱文件打开预算。
用法：python3 技能配置/triwich/tests/test_closeout_guard.py
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(os.path.expanduser("~"), "[记忆共享中心]/脚本中心/triwich_closeout_guard.py")

spec = importlib.util.spec_from_file_location("triwich_closeout_guard", GUARD)
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

PASS, FAIL = [], []
SEAL_HEX = "0123456789abcdef"
SESS = "WorkBuddy:test"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  🔴 ") + name + ((" :: " + str(detail)) if (detail and not cond) else ""))


def make_env(seal_age, ledger_age, key_age=None, fu_age=None,
             ledger_has_seal=None, fu_synced=None, declared_len=None):
    """ledger_has_seal: True→台账含本轮 seal 指纹 / False→不含 / None→台账只有标题
    fu_synced: True→决策卡含 (ts,session) 精确对应 / False→含但不匹配 / "legacy"→老式无会话字段 / "absent"→无登记行
    declared_len: 台账自称"链长 N"（用于超前检测）
    """
    tmp = tempfile.mkdtemp(prefix="twcg_")
    now = time.time()
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - seal_age))

    log = os.path.join(tmp, "scripts", "seal.log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("%s|%s|%s|cafe|beef\n" % (ts, SESS, SEAL_HEX))

    ledger = os.path.join(tmp, "阶段A采样清单-三明智4.0.md")
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write("## 三、采样台账\n")
        if ledger_has_seal is True:
            fh.write("| 46 | 本轮任务 | L2 | 卡点 | 匹配 | 需要 | 没回访 | seal %s（链长%d） |\n"
                     % (SEAL_HEX, declared_len or 1))
        elif declared_len:
            fh.write("| 46 | 本轮任务 | L2 | 卡点 | 匹配 | 需要 | 没回访 | seal xxx（链长%d） |\n" % declared_len)
    os.utime(ledger, (now - ledger_age, now - ledger_age))

    cwd = os.path.join(tmp, "ws")
    steps = os.path.join(cwd, "steps")
    os.makedirs(steps)
    if key_age is not None:
        kf = os.path.join(steps, "step0-determination-20260915_120000.md")
        with open(kf, "w", encoding="utf-8") as fh:
            fh.write("x")
        os.utime(kf, (now - key_age, now - key_age))

    room = os.path.join(tmp, "decision-room.md")
    if fu_synced is not None and fu_synced != "absent":
        old = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now - (fu_age or 0)))
        with open(room, "w", encoding="utf-8") as fh:
            if fu_synced is True:
                fh.write("## FU-99\n- 登记：%s · 发起方式:机制封口自动登记 · 会话:%s\n" % (ts, SESS))
            elif fu_synced == "legacy":
                # 老式行：无会话字段 → 身份不可判
                fh.write("## FU-99\n- 登记：%s · 发起方式:机制封口自动登记\n" % old)
            else:
                # 有会话字段但时间戳对不上（登记的是别人的一轮）
                fh.write("## FU-99\n- 登记：%s · 发起方式:机制封口自动登记 · 会话:%s\n" % (old, SESS))

    # 重定向模块常量到夹具环境（DECISION_ROOM 必重定向——否则 S3 读真实档案库→假失败）
    G.SKILL_DIRS = [tmp]
    G.SAMPLE_LEDGER = ledger
    G.DECISION_ROOM = room
    return tmp, cwd


def run(seal_age, ledger_age, key_age=None, fu_age=None,
        ledger_has_seal=None, fu_synced=None, declared_len=None):
    tmp, cwd = make_env(seal_age, ledger_age, key_age, fu_age,
                        ledger_has_seal, fu_synced, declared_len)
    try:
        return G.check(cwd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("🧪 三明智收尾守卫回归 v%s" % G.VERSION)

    print("\n[1] 负例：封口后未补台账（台账无本轮 seal 指纹 → 应报 S1）")
    r = run(seal_age=300, ledger_age=7200, ledger_has_seal=False)
    codes = [f["code"] for f in r["findings"]]
    check("S1 命中", "S1" in codes, r)
    check("alarm=True", r["alarm"] is True, r)

    print("\n[2] 负例：键文件晚于末次封口（应报 S2·疑似未封口）")
    r = run(seal_age=1800, ledger_age=60, key_age=120, ledger_has_seal=True)
    codes = [f["code"] for f in r["findings"]]
    check("S2 命中", "S2" in codes, r)

    print("\n[3] 正例：封口在前、台账在后且含本轮 seal 指纹（不得误报）")
    r = run(seal_age=600, ledger_age=30, ledger_has_seal=True, fu_synced=True)
    check("无 finding", not r["findings"], r)
    check("alarm=False", r["alarm"] is False, r)

    print("\n[3b] S3 负例：封口后决策卡无本轮 (ts,session) 对应登记（应报 S3）")
    r = run(seal_age=1800, ledger_age=30, fu_age=7200, ledger_has_seal=True, fu_synced=False)
    codes = [f["code"] for f in r["findings"]]
    check("S3 命中", "S3" in codes, r)

    print("\n[3c] S3 静默：decision-room 完全无 FU 登记（不得误报）")
    r = run(seal_age=1800, ledger_age=30, ledger_has_seal=True, fu_synced="absent")
    codes = [f["code"] for f in r["findings"]]
    check("无 S3", "S3" not in codes, r)

    print("\n[3d] 多字工具名回归（Qoder CN 实跑命中）：登记行会话含空格时 S3 不得假红")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        room = os.path.join(td, "decision-room.md")
        ts_now = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(room, "w", encoding="utf-8") as fh:
            fh.write("## FU-40\n- 登记：%s · 发起方式:机制封口自动登记 · 会话:Qoder CN:9a59c1d5f478\n" % ts_now)
        keep = G.DECISION_ROOM
        try:
            G.DECISION_ROOM = room
            check("正例·完整身份命中→已登记（旧判据在此必 False=S3 假红）",
                  G._fu_registered(ts_now, "Qoder CN:9a59c1d5f478") is True)
            check("负例·同前缀不同 hash 不得算命中（防放宽把别人的轮次认成本轮）",
                  G._fu_registered(ts_now, "Qoder CN:deadbeef0000") is False)
        finally:
            G.DECISION_ROOM = keep

    print("\n[★4] 假阴性回归：台账含本轮 seal 指纹但 mtime 很旧（旧判定必报 S1→现不得报）")
    r = run(seal_age=300, ledger_age=7200, ledger_has_seal=True)
    codes = [f["code"] for f in r["findings"]]
    check("无 S1（强凭据优先于 mtime）", "S1" not in codes, r)

    print("\n[★5] 假阳性回归：台账 mtime 很新但不含本轮 seal 指纹（旧判定静默→现必报 S1）")
    r = run(seal_age=1800, ledger_age=10, ledger_has_seal=False)
    codes = [f["code"] for f in r["findings"]]
    check("S1 命中（mtime 新≠登记了本轮）", "S1" in codes, r)

    print("\n[★6] 弱证据降级：老式登记行（无会话字段）身份不可判 → 不出 S3 定论")
    r = run(seal_age=1800, ledger_age=30, fu_age=7200, ledger_has_seal=True, fu_synced="legacy")
    codes = [f["code"] for f in r["findings"]]
    check("无 S3 定论", "S3" not in codes, r)
    check("有弱证据提示", any("弱" in h for h in r.get("hints", [])), r)

    print("\n[★7] 台账超前检测：自称链长 99 > 实链长 1 → 不可判，不出 S1 定论")
    r = run(seal_age=300, ledger_age=7200, ledger_has_seal=False, declared_len=99)
    codes = [f["code"] for f in r["findings"]]
    check("无 S1 定论（自觉超前→交人工）", "S1" not in codes, r)

    print("\n[8] 边界：窗口外无三明智活动（静默跳过）")
    r = run(seal_age=G.WINDOW_SEC + 600, ledger_age=30, ledger_has_seal=True)
    check("skipped 非空", bool(r.get("skipped")), r)
    check("无 finding", not r["findings"], r)

    print("\n[9] 边界：seal.log 缺失（静默降级·不阻断）")
    tmp = tempfile.mkdtemp(prefix="twcg_")
    try:
        G.SKILL_DIRS = [tmp]
        G.SAMPLE_LEDGER = os.path.join(tmp, "ledger.md")
        G.DECISION_ROOM = os.path.join(tmp, "room.md")
        res = G.check(tmp)
        check("skipped 非空", bool(res.get("skipped")), res)
        check("alarm=False", res["alarm"] is False, res)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 46)
    print("结果: %d 通过 / %d 失败" % (len(PASS), len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("   🔴 " + f)
        return 1
    print("✅ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
