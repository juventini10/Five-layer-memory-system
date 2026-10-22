#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_page_receipt.py — 翻页回执对账+页表指纹 变异测试双向验证（V3 出闸判据·2026-10-21）
纪律：缺回执必报警（变异向）+ 合法操作不误报（守恒向），判据上线老规矩。
P1 缺回执→guard FAIL（报警）
P2 合法回执→guard OK（不误报）
P3 指纹伪造/改版漂移→guard FAIL
P4 接线前存量键→SKIP-legacy（历史不判红——防永久红基线纪律）
P5 L3 轮缺十锁页回执→FAIL；双行齐→OK
P6 closeout 接线：缺回执键→seal 前判红（seal.log 零写入）；合法键→过闸
P7 manifest 三方一致：build→check 绿；篡改页体→check 红；还原→绿（临时树隔离，真盘不动）
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, subprocess, tempfile, shutil, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.abspath(os.path.join(HERE, ".."))
GUARD = os.path.join(SKILL, "scripts", "page_receipt_guard.py")
MM = os.path.join(SKILL, "scripts", "make_manifest.py")
CO = os.path.join(SKILL, "scripts", "triwich_closeout.py")
PY = sys.executable
FAIL = 0

sys.path.insert(0, os.path.join(SKILL, "scripts"))
import page_receipt_guard as prg  # 取 RECEIPT_SINCE 等常量（判据同源，⛔测试侧复制常数）

MF = json.load(open(os.path.join(SKILL, "pages", "manifest.json"), encoding="utf-8"))
TAB = {e["path"]: e["fingerprint"] for e in MF["pages"]}
NEW_TS = "20991231_235900"   # 恒 > RECEIPT_SINCE（未来桩）
NEW_TS2 = "20991231_235901"  # 第二枚未来桩（P6 双键隔离——首版同 ts 同名互覆=用例自污染，T1 残留教训同族）
OLD_TS = "20200101_000000"   # 恒 < RECEIPT_SINCE（存量桩）

def keyfile(tmp, ts, route="三明智 L1 路径:测试", receipts=None):
    p = os.path.join(tmp, "step0-determination-%s.md" % ts)
    lines = ["- **本轮键**:`%s`" % ts, "- **路线声明**:`%s`" % route]
    for pg, fp in (receipts or {}).items():
        lines.append("- **装载回执**: 已读 %s @%s" % (pg, fp))
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return p

def guard(p):
    r = subprocess.run([PY, GUARD, "--key-file", p], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr

def check(name, cond):
    global FAIL
    print(("PASS" if cond else "FAIL") + " " + name)
    FAIL += (not cond)

def main():
    tmp = tempfile.mkdtemp(prefix="pgrecv_")
    try:
        okp05 = TAB["pages/p05-assumption-gates.md"]
        # P1 缺回执必报警
        p = keyfile(tmp, NEW_TS)
        rc, out = guard(p)
        check("P1 缺回执→RECEIPT:FAIL（报警）", rc == 1 and "RECEIPT:FAIL" in out and "缺回执" in out)
        # P2 合法回执不误报
        p = keyfile(tmp, NEW_TS, receipts={"pages/p05-assumption-gates.md": okp05})
        rc, out = guard(p)
        check("P2 合法回执→RECEIPT:OK（不误报）", rc == 0 and "RECEIPT:OK" in out)
        # P3 指纹不符（伪造/漂移）
        p = keyfile(tmp, NEW_TS, receipts={"pages/p05-assumption-gates.md": "deadbeef"})
        rc, out = guard(p)
        check("P3 指纹不符→RECEIPT:FAIL", rc == 1 and "指纹不符" in out)
        # P4 存量轮不判红
        p = keyfile(tmp, OLD_TS)
        rc, out = guard(p)
        check("P4 接线前存量键→SKIP-legacy（历史不误报）", rc == 0 and "SKIP-legacy" in out)
        # P5 L3 追加十锁页
        p = keyfile(tmp, NEW_TS, route="三明智 L3 路径:深度模式(双Agent)",
                   receipts={"pages/p05-assumption-gates.md": okp05})
        rc, out = guard(p)
        check("P5a L3 缺十锁页回执→FAIL", rc == 1 and "p-mechanism" in out)
        p = keyfile(tmp, NEW_TS, route="三明智 L3 路径:深度模式(双Agent)",
                   receipts={"pages/p05-assumption-gates.md": okp05,
                             "pages/p-mechanism.md": TAB["pages/p-mechanism.md"]})
        rc, out = guard(p)
        check("P5b L3 双回执齐→OK", rc == 0 and "RECEIPT:OK" in out)
        # P6 closeout 接线（env 隔离真链零污染）
        env = dict(os.environ)
        env.update({"TRIWICH_SEAL_LOG": os.path.join(tmp, "s.log"),
                    "TRIWICH_DECISION_ROOM": os.path.join(tmp, "dr.md"),
                    "TRIWICH_FOLLOWUP_LEDGER": os.path.join(tmp, "fl.log")})
        open(env["TRIWICH_DECISION_ROOM"], "w", encoding="utf-8").write("# 台账（夹具）\n\n## 三、条目区\n")
        blk = os.path.join(tmp, "b.txt")
        open(blk, "w", encoding="utf-8").write("## L1 x 结果\n[🧠 三明智 L1 (x) ✅ | t | 2026-10-21]\n")
        kbad = keyfile(tmp, NEW_TS)               # 缺回执
        kogd = keyfile(tmp, NEW_TS2, receipts={"pages/p05-assumption-gates.md": okp05})
        base = [PY, CO, "--tool", "qodercn", "--block-file", blk,
                "--sampling", "none", "--no-sampling-reason", "P6", "--log-summary", "P6", "--logdir", tmp]
        r = subprocess.run(base + ["--key-file", kbad], capture_output=True, text=True, env=env)
        sealed = os.path.isfile(env["TRIWICH_SEAL_LOG"]) and open(env["TRIWICH_SEAL_LOG"]).read().strip() != ""
        check("P6a closeout 缺回执→seal 前判红且 seal.log 零写入",
              r.returncode != 0 and "回执对账" in r.stderr and not sealed)
        r2 = subprocess.run(base + ["--key-file", kogd], capture_output=True, text=True, env=env)
        check("P6b closeout 合法回执→过闸进链",
              r2.returncode == 0 and "回执对账(OK" in r2.stdout)
        # P7 manifest 三方一致（临时树隔离）
        troot = os.path.join(tmp, "skillroot")
        shutil.copytree(os.path.join(SKILL, "pages"), os.path.join(troot, "pages"))
        rb = subprocess.run([PY, MM, "build", "--root", troot], capture_output=True, text=True)
        rc_check_ok = subprocess.run([PY, MM, "check", "--root", troot], capture_output=True, text=True)
        check("P7a 克隆树 build+check 自洽绿", rb.returncode == 0 and rc_check_ok.returncode == 0)
        victim = os.path.join(troot, "pages", "p0-step0.md")
        with open(victim, "a", encoding="utf-8") as f:
            f.write("\n变异注入：篡改页体一行\n")
        rc2 = subprocess.run([PY, MM, "check", "--root", troot], capture_output=True, text=True)
        check("P7b 篡改页体→check 红（表内≠重算显形）", rc2.returncode == 1 and "MANIFEST:FAIL" in rc2.stderr)
        os.remove(victim); shutil.copy2(os.path.join(SKILL, "pages", "p0-step0.md"), victim)
        rc3 = subprocess.run([PY, MM, "check", "--root", troot], capture_output=True, text=True)
        check("P7c 还原→check 复绿（变异可逆自证）", rc3.returncode == 0)
        # P7d 真盘现状必须已建表一致（收尾门禁的本体）
        rc4 = subprocess.run([PY, MM, "check"], capture_output=True, text=True)
        check("P7d 真盘 manifest 三方一致", rc4.returncode == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("结果: %d/12 通过 %s" % (12 - FAIL, "✅" if FAIL == 0 else "❌"))
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
