#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_triwich_closeout.py — closeout 四合一编排器常驻回归（F10 S1 配套·2026-10-21）
覆盖夹具三轮手工实证的固化：T1 全链四落点 / T2 无签名预检拒 / T3 FU被拒显形盘点。
⛔全部落点 env 隔离（TRIWICH_SEAL_LOG/DECISION_ROOM/FOLLOWUP_LEDGER/KEY_ROOT+假logdir+临时采样），真链零污染。
R0②（2026-10-21）：键根隔离补齐——此前缺省键根=cwd/steps，run.sh 从真实工作区启动时自动踩真盘最新键，
T1/T3 随 cwd 红绿漂移（卡轮28 以为竞态，实为真盘状态泄漏）。
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, subprocess, tempfile, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.join(HERE, "..", "scripts", "triwich_closeout.py")
PY = sys.executable
FAIL = 0

def run(tmp, block, extra, dr=True):
    env = dict(os.environ)
    env.update({"TRIWICH_SEAL_LOG": os.path.join(tmp, "s.log"),
                "TRIWICH_DECISION_ROOM": os.path.join(tmp, "dr.md"),
                "TRIWICH_FOLLOWUP_LEDGER": os.path.join(tmp, "fl.log"),
                "TRIWICH_KEY_ROOT": tmp})
    if dr:
        open(env["TRIWICH_DECISION_ROOM"], "w", encoding="utf-8").write("# 台账（夹具）\n\n## 三、条目区\n")
    return subprocess.run([PY, CO, "--tool", "qodercn", "--block-file", block,
                           "--sampling-file", os.path.join(tmp, "sp.md"), "--logdir", tmp] + extra,
                          capture_output=True, text=True, env=env)

def main():
    global FAIL
    tmp = tempfile.mkdtemp(prefix="closeout_test_")
    try:
        # R0② 夹具键：落 tmp 键根（legacy ts < RECEIPT_SINCE ⇒ 回执闸 SKIP-legacy 确定性，不依赖真实工作区状态）
        os.makedirs(os.path.join(tmp, "steps"), exist_ok=True)
        open(os.path.join(tmp, "steps", "step0-determination-20260101_000000.md"), "w", encoding="utf-8").write(
            "**路线声明**：三明智 L1 路径:第一性原理\n**深度声明**：夹具\n**验证保障**：夹具\n")
        good = os.path.join(tmp, "b.txt")
        open(good, "w", encoding="utf-8").write("## L1 x 结果\n[🧠 三明智 L1 (x) ✅ | t | 2026-10-21]\n")
        sa = ["--seal-args", '--followup 卡 --predict p --falsify f --deadline 2099-01-01 --default noop --window 1天 --depth L1']
        r = run(tmp, good, sa + ["--sampling", "a|b|c|d|e", "--log-summary", "T1守恒标记"])
        lgf = os.path.join(tmp, "系统日志_%s.md" % datetime.date.today().strftime("%Y-%m-%d"))
        ok = (r.returncode == 0 and "CLOSEOUT:OK" in r.stdout
              and os.path.isfile(os.path.join(tmp, "dr.md"))
              and "FU-1" in open(os.path.join(tmp, "dr.md"), encoding="utf-8").read()
              and os.path.isfile(lgf) and "T1守恒标记" in open(lgf, encoding="utf-8").read())
        print(("PASS" if ok else "FAIL") + " T1 全链四落点(假盘隔离)"); FAIL += (not ok)
        nb = os.path.join(tmp, "nb.txt"); open(nb, "w").write("无签名块\n")
        r2 = run(tmp, nb, ["--log-summary", "x"], dr=False)
        ok2 = r2.returncode != 0 and "签名预检" in (r2.stderr + r2.stdout)
        print(("PASS" if ok2 else "FAIL") + " T2 无签名→预检拒（负例）"); FAIL += (not ok2)
        os.remove(os.path.join(tmp, "dr.md"))  # T1 留档清场：本例要测"dr 缺失→FU拒显形"，前例残留=用例污染
        r3 = run(tmp, good, sa + ["--sampling", "none", "--no-sampling-reason", "T3", "--log-summary", "y"], dr=False)
        ok3 = r3.returncode != 0 and "FU登记" in r3.stderr and "已完成面" in r3.stderr
        print(("PASS" if ok3 else "FAIL") + " T3 FU被拒→显形+已完成面盘点（负例）"); FAIL += (not ok3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("结果: %d/3 通过 %s" % (3 - FAIL, "✅" if FAIL == 0 else "❌"))  # 套件判绿口径=run.sh v1.5.6 正则（首跑挂在此=措辞面非功能面·已对齐全族成功措辞）
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
