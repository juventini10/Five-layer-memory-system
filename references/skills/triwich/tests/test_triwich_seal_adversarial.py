#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triwich_seal 对抗测试（v1.1.1 根治后固化·跨工具通用·2026-09-05）
实测基础：确定性构造链 + TRIWICH_HIST_DIR/TRIWICH_SEAL_LOG 环境变量，直接调模块内 verify。
场景：基线 record+verify / 改内容 / 改日志 / 删链尾 —— 三对抗均须拦截(FAIL)，基线须通过(OK)。

用法：env -u PYTHONHOME -u PYTHONPATH python3 test_triwich_seal_adversarial.py
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import hashlib
import json
import os
import shutil
import sys
import tempfile

_SKILL = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SEAL_DIR = os.path.join(_SKILL, "scripts")
sys.path.insert(0, SEAL_DIR)
os.environ["PYTHONPATH"] = SEAL_DIR  # 确保模块 import

import triwich_seal as TS  # noqa: E402

HIST_FN = "agent%3Amain%3Acurrent.json"
SIGNED_CONTENT = (
    "用户：请用三明智评估这个方案。\n"
    "## L2 评估 结果\n"
    "主要矛盾：xxx\n"
    "第一性原理：yyy\n"
    "[🧠 三明智 L2 完成 ✅ 深度达标]"
)


def write_history(hist_dir, fname, content=SIGNED_CONTENT):
    os.makedirs(hist_dir, exist_ok=True)
    msgs = [{"role": "user", "content": "请用三明智评估这个方案。"},
            {"role": "assistant", "content": content}]
    with open(os.path.join(hist_dir, fname), "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False)


def make_chain(hist_dir, log, current_name="current.json"):
    """确定性构造 sA→current 两跳链，当前会话=链尾（真实场景：最新会话刚 seal 完）。"""
    entries = []
    prev = "GENESIS"
    for i, name in enumerate(("sA.json", current_name)):
        fname = f"agent%3Amain%3A{name}"
        write_history(hist_dir, fname, SIGNED_CONTENT)
        seal = TS.compute_seal(fname, SIGNED_CONTENT)
        assert seal, "签名未提取到"
        now = f"2026-09-05 09:0{i}:00"
        h = TS.self_hash(now, fname, seal, prev)
        entries.append(f"{now}|{fname}|{seal}|{prev}|{h}")
        prev = h
    with open(log, "w", encoding="utf-8") as f:
        f.write("\n".join(entries) + "\n")
    TS.HIST_DIR = hist_dir
    TS.LOG_PATH = log


def run_verify(t, expected_ok):
    sess, msgs = TS.load_latest_history()
    assert sess, "无会话历史"
    code, msg = TS.verify()
    if expected_ok:
        assert code == 0 and "OK" not in str(msg).startswith(
            "SEAL"), f"应通过: code={code} msg={msg}"
        assert code == 0, f"基线应通过: code={code} {msg}"
    else:
        assert code == 1, f"对抗应拦截: code={code} {msg}"
    return code, msg


class T:
    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="seal_test_")
        self.hist = os.path.join(self.base, "chat-history")
        self.log = os.path.join(self.base, "seal.log")

    def clean(self):
        TS.LOG_PATH = os.path.expanduser("[记忆共享中心]/技能配置/triwich/scripts/seal.log")
        shutil.rmtree(self.base, ignore_errors=True)


def test_对抗1_改内容(t):
    make_chain(t.hist, t.log)  # sA→current 两跳，当前会话=current
    mutated = SIGNED_CONTENT.replace("yyy", "xXX")
    write_history(t.hist, "agent%3Amain%3Acurrent.json", mutated)  # 改当前会话结论块内容
    code, msg = TS.verify()
    assert code == 1, f"改内容未拦截: code={code} {msg}"
    assert "不一致" in msg, msg
    return "对抗1 改内容 FAIL ✅"


def test_对抗2_改日志(t):
    make_chain(t.hist, t.log)  # 2 跳
    log = open(t.log, encoding="utf-8").read().strip().split("|")
    log[2] = "DEADBEEF"
    with open(t.log, "w", encoding="utf-8") as f:
        f.write("|".join(log) + "\n")
    code, msg = TS.verify()
    assert code == 1 and "self_hash" in msg, f"改日志未拦截: code={code} {msg}"
    return "对抗2 改日志 FAIL ✅"


def test_对抗3_删链尾(t):
    make_chain(t.hist, t.log)  # sA→current 两跳，当前会话在链尾
    lines = open(t.log, encoding="utf-8").readlines()
    assert len(lines) >= 2
    with open(t.log, "w", encoding="utf-8") as f:
        f.writelines(lines[:-1])  # 删掉链尾=当前会话那一跳
    code, msg = TS.verify()
    assert code == 1 and "链尾" in msg, f"删链尾未拦截: code={code} {msg}"
    return "对抗3 删链尾 FAIL ✅"


def test_基线_ok(t):
    make_chain(t.hist, t.log)  # sA→current，当前会话=链尾且内容未改
    code, msg = TS.verify()
    assert code == 0, f"基线应通过: code={code} {msg}"
    return "基线 record+verify ✅"


def main():
    # load_latest_history 依赖 TS.HIST_DIR，我们对 TS 做 monkeypatch 指向临时目录
    tests = [test_基线_ok, test_对抗1_改内容, test_对抗2_改日志, test_对抗3_删链尾]
    fail = 0
    for fn in tests:
        t = T()
        try:
            TS.HIST_DIR = t.hist
            TS.LOG_PATH = t.log
            TS.JSONL_ENABLED = False  # v1.3.0 测试隔离：禁真实 WB/ZCode JSONL 探测（防命中实盘会话）
            print(f"[PASS] {fn(t)}")
        except AssertionError as e:
            fail += 1
            print(f"[FAIL] {fn.__name__}: {e}")
        finally:
            TS.JSONL_ENABLED = True
            t.clean()
    print(f"\n结果: {len(tests) - fail}/{len(tests)} 通过" + (" ✅" if fail == 0 else f" · {fail} 失败 ❌"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())