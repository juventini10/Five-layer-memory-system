#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_key_link.py — 键-链强互锁变异测试双向（seal v1.6.0·2026-10-21 你令 gogogo）
纪律同 V3：报警向（顶包/篡改/撕裂必红）+ 守恒向（合法/老链不误报）·全落点 env 隔离真链零污染。
K1 带键封口→7字段行入链·verify绿·linkcheck OK（合法守恒）
K2 无键封口→5字段老式行·verify 绿（老链祖父化·不误报）
K3 同键二次封不同结论→record 拒绝（顶包报警）
K4 封口后改键文件→linkcheck FAIL（篡改报警）
K5 链中6字段撕裂行→verify FAIL 定位（半提交报警）
K6 closeout 全链带键→done 含「键链回读(linkcheck OK)」且链尾7字段（接线守恒）
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, subprocess, tempfile, shutil, json

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.abspath(os.path.join(HERE, ".."))
SEAL = os.path.join(SKILL, "scripts", "triwich_seal.py")
CO = os.path.join(SKILL, "scripts", "triwich_closeout.py")
PY = sys.executable
FAIL = 0

MF = json.load(open(os.path.join(SKILL, "pages", "manifest.json"), encoding="utf-8"))
P05FP = [e["fingerprint"] for e in MF["pages"] if "p05" in e["path"]][0]

def mkkey(tmp, ts="20990101_000001"):
    p = os.path.join(tmp, "steps", "step0-determination-%s.md" % ts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(
        "- **本轮键**:`%s`\n- **装载回执**:已读 pages/p05-assumption-gates.md @%s\n内容A\n" % (ts, P05FP))
    return p

def mkblock(tmp, name, body="内容甲"):
    p = os.path.join(tmp, name + ".txt")
    open(p, "w", encoding="utf-8").write(
        "## L1 x 结果\n%s\n[🧠 三明智 L1 (x) ✅ | %s | 2026-10-21]\n" % (body, name))
    return p

def run(tmp, args):
    env = dict(os.environ)
    env.update({"TRIWICH_SEAL_LOG": os.path.join(tmp, "s.log"),
                "TRIWICH_DECISION_ROOM": os.path.join(tmp, "dr.md"),
                "TRIWICH_FOLLOWUP_LEDGER": os.path.join(tmp, "fl.log"),
                "TRIWICH_HIST_DIR": os.path.join(tmp, "nohist")})
    r = subprocess.run([PY, SEAL] + args, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr

def check(name, cond):
    global FAIL
    print(("PASS" if cond else "FAIL") + " " + name)
    FAIL += (not cond)

def main():
    tmp = tempfile.mkdtemp(prefix="keylink_")
    try:
        kf = mkkey(tmp)
        b1 = mkblock(tmp, "b1")
        rc, out = run(tmp, ["record", "--tool", "qodercn", "--text-file", b1, "--key-file", kf])
        line = open(os.path.join(tmp, "s.log")).read().strip().splitlines()[-1]
        check("K1a 带键封口入链(7字段)", rc == 0 and len(line.split("|")) == 7)
        rc, out = run(tmp, ["verify", "--tool", "qodercn", "--text-file", b1])
        check("K1b verify 绿(新式分式)", rc == 0 and "SEAL:OK" in out)
        rc, out = run(tmp, ["linkcheck", "--key-file", kf])
        check("K1c linkcheck OK", rc == 0 and "LINKCHECK:OK" in out)
        # K2 无键老式
        b2 = mkblock(tmp, "b2", "内容乙")
        rc, out = run(tmp, ["record", "--tool", "qodercn", "--text-file", b2])
        rc2, out2 = run(tmp, ["verify", "--tool", "qodercn", "--text-file", b2])
        check("K2 无键5字段老式行·verify绿(祖父化不误报)",
              rc == 0 and len(out.split("链长")[0]) > 0 and rc2 == 0)
        # K3 同键二次封不同结论
        b3 = mkblock(tmp, "b3", "内容丙顶包")
        rc, out = run(tmp, ["record", "--tool", "qodercn", "--text-file", b3, "--key-file", kf])
        check("K3 同键异封→拒绝(顶包报警)", rc != 0 and "键-链互锁拒绝" in out)
        # K4 封口后改键文件
        open(kf, "a", encoding="utf-8").write("封口后偷加一行\n")
        rc, out = run(tmp, ["linkcheck", "--key-file", kf])
        check("K4 封口后改键→linkcheck FAIL(篡改报警)", rc != 0 and "封口后被改" in out)
        # K5 撕裂6字段行
        prev_h = line.split("|")[4]
        with open(os.path.join(tmp, "s.log"), "a", encoding="utf-8") as f:
            f.write("2099-01-02 00:00:00|x:deadbeef1234|sealX|%s|hY6f|20990102_000000\n" % prev_h)
        rc, out = run(tmp, ["verify", "--tool", "qodercn", "--text-file", b2])
        check("K5 6字段撕裂行→verify FAIL 定位", rc != 0 and "链撕裂" in out)
        # K6 closeout 全链接线
        os.remove(os.path.join(tmp, "s.log"))
        open(os.path.join(tmp, "dr.md"), "w", encoding="utf-8").write("# 台账（夹具）\n\n## 三、条目区\n")
        kf2 = mkkey(tmp, "20990103_000000")
        env = dict(os.environ)
        env.update({"TRIWICH_SEAL_LOG": os.path.join(tmp, "s.log"),
                    "TRIWICH_DECISION_ROOM": os.path.join(tmp, "dr.md"),
                    "TRIWICH_FOLLOWUP_LEDGER": os.path.join(tmp, "fl.log")})
        r = subprocess.run([PY, CO, "--tool", "qodercn", "--block-file", b1,
                            "--key-file", kf2, "--sampling", "none", "--no-sampling-reason", "K6",
                            "--log-summary", "K6守恒标记", "--logdir", tmp],
                           capture_output=True, text=True, env=env)
        tail = open(os.path.join(tmp, "s.log")).read().strip().splitlines()[-1]
        check("K6 closeout 带键+回读自证入链",
              r.returncode == 0 and "键链回读(linkcheck OK)" in r.stdout and len(tail.split("|")) == 7)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("结果: %d/8 通过 %s" % (8 - FAIL, "✅" if FAIL == 0 else "❌"))
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
