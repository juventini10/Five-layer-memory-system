#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策卡回访挂载回归（triwich_seal v1.2.0 · 2026-09-13 G2回访机制M2固化）
场景：封口登记→前置筛查→回访销账全链路 + 3 负例（重复销账/非法偏差枚举/缺四件套·Fail-Closed须拦截）
环境：TRIWICH_DECISION_ROOM/TRIWICH_HIST_DIR/TRIWICH_SEAL_LOG/TRIWICH_FOLLOWUP_LEDGER 全隔离·不污染实盘台账与封口链
用法：env -u PYTHONHOME -u PYTHONPATH python3 tests/test_triwich_decision_room.py
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import shutil
import sys
import tempfile

_SKILL = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(_SKILL, "scripts"))
os.environ["PYTHONPATH"] = os.path.join(_SKILL, "scripts")

import triwich_seal as TS  # noqa: E402
_TS_ORIG = (TS.DECISION_ROOM_PATH, getattr(TS, 'HIST_DIR', None), TS.JSONL_ENABLED)  # v4.4.9b·import 时捕获真默认（早于一切测试动作）

SIGNED = "## L2 回访回归 结果\n依据：x\n[🧠 三明智 L2 完成 ✅]"


def prepare(t, room_body="## 三、条目区（脚本追加·勿手排·按 FU-{seq} 递增）\n"):
    hist = os.path.join(t.base, "hist")
    os.makedirs(hist, exist_ok=True)
    fname = "agent%3Amain%3Acase.json"
    msgs = [{"role": "user", "content": "t"}, {"role": "assistant", "content": SIGNED}]
    with open(os.path.join(hist, fname), "w", encoding="utf-8") as f:
        json.dump(msgs, f, ensure_ascii=False)
    room = os.path.join(t.base, "decision-room.md")
    with open(room, "w", encoding="utf-8") as f:
        f.write(room_body)
    TS.HIST_DIR, TS.LOG_PATH, TS.DECISION_ROOM_PATH = hist, os.path.join(t.base, "seal.log"), room
    # v1.5.0 新增留痕全局：⛔不一起隔离就会把夹具卡写进实盘锚点（2026-09-18 实测泄漏 2 行·由锚自身抓出）
    TS.FOLLOWUP_LEDGER = os.path.join(t.base, "followup_ledger.log")
    return room


def run_cli(argv):
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = TS.main.__wrapped__(argv) if hasattr(TS.main, "__wrapped__") else None
    return code, buf.getvalue()


def cli(argv):
    """直接走 main 的分发逻辑（用 sys.argv 注入再还原）。"""
    old = sys.argv
    sys.argv = ["triwich_seal.py"] + argv
    try:
        return TS.main()
    finally:
        sys.argv = old


class T:
    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="decision_room_test_")
        TS.JSONL_ENABLED = False  # 测试隔离：禁用真实 WB/ZCode JSONL 探测，走 fixture 路径

    def clean(self):
        # v4.4.9·R1-P2-07：恢复模块原默认（旧硬编码真机路径=夹具会回落到读真机会话存储——
        # 按文档设 TRIWICH_HIST_DIR 跑测试时 6 例变红的根因，红虽是审查者 env 触发，泄漏属实）
        TS.DECISION_ROOM_PATH, TS.HIST_DIR, TS.JSONL_ENABLED = _TS_ORIG  # v4.4.9b·恢复 import 时真默认（⛔硬编码真机路径=按文档设 env 跑测试时的泄漏向量·R1-P2-07）
        shutil.rmtree(self.base, ignore_errors=True)


def test_jsonl_wb_reader(t):
    """WorkBuddy jsonl reader（v1.3.0）：行 {"role":"assistant","content":[{type,text}]} → 拼取 text。"""
    root = os.path.join(t.base, "projects", "Users-x")
    os.makedirs(root, exist_ok=True)
    jl = os.path.join(root, "abc.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "content": [{"type": "input_text", "text": "q"}]}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"role": "assistant", "content": [
            {"type": "output_text", "text": "## L2 WB 结果\n依据：x\n"},
            {"type": "output_text", "text": "[🧠 三明智 L2 完成 ✅]"}]}, ensure_ascii=False) + "\n")
    old_src, old_en = TS.JSONL_SOURCES, TS.JSONL_ENABLED
    TS.JSONL_SOURCES, TS.JSONL_ENABLED = [("WB-test", t.base, "projects/*/*.jsonl", "wb")], True
    try:
        sess, text = TS.load_latest_text()
        assert sess == "abc.jsonl", f"session key 错: {sess}"
        assert "[🧠 三明智 L2 完成 ✅]" in text and "## L2 WB 结果" in text, f"text 拼接错: {text[:80]}"
        assert TS.compute_seal(sess, text), "签名未提取到"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED = old_src, old_en
    return "WB jsonl reader 解析+签名提取 ✅"


def test_jsonl_zcode_reader(t):
    """ZCode rollout reader（v1.3.0）：行 {"type":"model_io","response":{"text"},"sessionId"} →
    tool-calls 轮（text 空）跳过，只取真文本轮。"""
    root = os.path.join(t.base, "rollout")
    os.makedirs(root, exist_ok=True)
    jl = os.path.join(root, "model-io-sess_t1.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "model_io", "sessionId": "sess_t1",
                            "response": {"text": "", "finishReason": "tool-calls"}}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "model_io", "sessionId": "sess_t1",
                            "response": {"text": "## L3 深度模式 结果\n[🧠 三明智 L3 完成 ✅]"}}, ensure_ascii=False) + "\n")
    old_src, old_en = TS.JSONL_SOURCES, TS.JSONL_ENABLED
    TS.JSONL_SOURCES, TS.JSONL_ENABLED = [("ZCode-test", t.base, "rollout/model-io-sess_*.jsonl", "zcode")], True
    try:
        sess, text = TS.load_latest_text()
        assert sess == "sess_t1", f"session key 应取行内 sessionId: {sess}"
        assert "[🧠 三明智 L3 完成 ✅]" in text, f"text 错: {text[:80]}"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED = old_src, old_en
    return "ZCode rollout reader 解析+sessionId 取键 ✅"


def test_全链路(t):
    room = prepare(t)
    assert cli(["record", "--followup", "回归任务", "--predict", "P成立", "--falsify", "若P不成立则错", "--window", "下次", "--depth", "L2"]) == 0
    body = open(room, encoding="utf-8").read()
    assert "## FU-1 · 状态:待回访" in body and "- 任务：回归任务" in body
    assert cli(["followup"]) == 0
    assert cli(["resolve", "1", "--actual", "P成立", "--bias", "B2",
                "--cause", "证据环", "--fix", "前置查替代", "--mechanism", "mechanism"]) == 0
    body = open(room, encoding="utf-8").read()
    assert "状态:已回访" in body and "发起方式:mechanism" in body and "- 偏差类型：B2" in body
    assert "- 实际：P成立" in body
    return "全链路 登记→筛查→销账 ✅"


def test_负例_重复销账(t):
    prepare(t)
    cli(["record", "--followup", "任务A", "--predict", "P", "--falsify", "F1", "--window", "W"])
    assert cli(["resolve", "1", "--actual", "a", "--bias", "B1", "--cause", "c", "--fix", "f"]) == 0
    assert cli(["resolve", "1", "--actual", "a", "--bias", "B1", "--cause", "c", "--fix", "f"]) == 1
    return "负例1 重复销账拦截 ✅"


def test_负例_非法枚举(t):
    prepare(t)
    cli(["record", "--followup", "任务A", "--predict", "P", "--falsify", "F1", "--window", "W"])
    assert cli(["resolve", "1", "--actual", "a", "--bias", "B99", "--cause", "c", "--fix", "f"]) == 1
    return "负例2 非法偏差枚举拦截 ✅"


def test_负例_缺四件套(t):
    prepare(t)
    cli(["record", "--followup", "任务A", "--predict", "P", "--falsify", "F1", "--window", "W"])
    assert cli(["resolve", "1", "--actual", "a", "--bias", "B1", "--cause", "c"]) == 1
    return "负例3 缺回访四件套拦截 ✅"


def test_续号(t):
    room = prepare(t, room_body="条目区\n\n## FU-4 · 状态:待回访\n- 任务：旧\n")
    cli(["record", "--followup", "新任务", "--predict", "P", "--falsify", "F2", "--window", "W"])
    assert "## FU-5 · 状态:待回访" in open(room, encoding="utf-8").read()
    return "续号（4→5·缺号不回填） ✅"


def test_jsonl_tool_routing(t):
    """--tool 定向路由（v1.3.0）：双端源并存时只探测指定端——多端并行防错位封口。"""
    wb_root = os.path.join(t.base, "projects", "Users-x")
    zc_root = os.path.join(t.base, "rollout")
    os.makedirs(wb_root, exist_ok=True)
    os.makedirs(zc_root, exist_ok=True)
    with open(os.path.join(wb_root, "wb1.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "assistant", "content": [{"type": "output_text", "text": "WB端回复 [🧠 三明智 L1 完成 ✅]"}]}, ensure_ascii=False) + "\n")
    with open(os.path.join(zc_root, "model-io-sess_z1.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "model_io", "sessionId": "sess_z1",
                            "response": {"text": "ZCode端回复 [🧠 三明智 L1 完成 ✅]"}}, ensure_ascii=False) + "\n")
    old_src, old_en = TS.JSONL_SOURCES, TS.JSONL_ENABLED
    TS.JSONL_SOURCES = [("WorkBuddy", t.base, "projects/*/*.jsonl", "wb"),
                        ("ZCode", t.base, "rollout/model-io-sess_*.jsonl", "zcode")]
    TS.JSONL_ENABLED = True
    try:
        sess, _ = TS.load_latest_text("zcode")
        assert sess == "sess_z1", f"--tool zcode 应命中 ZCode 源: {sess}"
        sess, _ = TS.load_latest_text("workbuddy")
        assert sess == "wb1.jsonl", f"--tool workbuddy 应命中 WB 源: {sess}"
        sess, _ = TS.load_latest_text("ZCODE")  # 大小写宽容
        assert sess == "sess_z1", "工具名应大小写宽容"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED = old_src, old_en
    return "--tool 定向路由+大小写宽容 ✅"


def test_jsonl_签名段定位(t):
    """v1.3.1 语义修复：多段拆流下按"最近一条含签名"定位——最新段无签名（后续开场白）不遮蔽更早的签名段。"""
    root = os.path.join(t.base, "rollout")
    os.makedirs(root, exist_ok=True)
    jl = os.path.join(root, "model-io-sess_t2.jsonl")
    rows = [
        {"type": "model_io", "sessionId": "sess_t2", "response": {"text": "开场白无签名"}},
        {"type": "model_io", "sessionId": "sess_t2", "response": {"text": "## L2 补封 结果\n[🧠 三明智 L2 完成 ✅]"}},
        {"type": "model_io", "sessionId": "sess_t2", "response": {"text": "下一轮开场白也无签名"}},
    ]
    with open(jl, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    old_src, old_en = TS.JSONL_SOURCES, TS.JSONL_ENABLED
    TS.JSONL_SOURCES, TS.JSONL_ENABLED = [("ZCode-test", t.base, "rollout/model-io-sess_*.jsonl", "zcode")], True
    try:
        sess, text = TS.load_latest_text()  # 不传 tool——源名 ZCode-test 与字面 zcode 不等价·本用例只验签名段定位
        assert "[🧠 三明智 L2 完成 ✅]" in text, f"应定位到签名段: {text[:60]}"
        assert "开场白无签名" not in text, "不应被后续无签名段遮蔽"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED = old_src, old_en
    return "签名段定位（后续无签名段不遮蔽） ✅"


def test_封口幂等(t):
    """v1.3.2：同会话同指纹重复 record → 不重复入链（链长不变）+ sealed=False（--followup 不重复登记）。"""
    prepare(t)
    assert cli(["record", "--followup", "任务A", "--predict", "P", "--falsify", "F1", "--window", "W"]) == 0
    log_lines = open(TS.LOG_PATH, encoding="utf-8").readlines()
    assert cli(["record", "--followup", "任务A", "--predict", "P", "--falsify", "F1", "--window", "W"]) == 0
    log_lines2 = open(TS.LOG_PATH, encoding="utf-8").readlines()
    assert len(log_lines) == len(log_lines2), f"重复封口应去重: {len(log_lines)} → {len(log_lines2)}"
    room = open(TS.DECISION_ROOM_PATH, encoding="utf-8").read()
    assert room.count("## FU-") == 1, "重复 record 不应重复登记 FU"
    return "封口幂等（同指纹去重·FU 不重复） ✅"


def test_jsonl_wbai_reader(t):
    """v1.3.3：WB-AI 行结构 type:"message"（非顶层 role）→ 独立 wbai kind 解析。"""
    root = os.path.join(t.base, "wbaiproj", "Users-x-wbai")
    os.makedirs(root, exist_ok=True)
    jl = os.path.join(root, "uuid1.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"type": "message", "role": "user", "content": [{"type": "input_text", "text": "q"}]}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"type": "message", "role": "assistant", "sessionId": "wbsess_1",
                            "content": [{"type": "output_text", "text": "## L2 WB-AI 结果\n[🧠 三明智 L2 完成 ✅]"}]}, ensure_ascii=False) + "\n")
    old_src, old_en = TS.JSONL_SOURCES, TS.JSONL_ENABLED
    TS.JSONL_SOURCES, TS.JSONL_ENABLED = [("WorkBuddy AI", t.base, "wbaiproj/*/*.jsonl", "wbai")], True
    try:
        sess, text = TS.load_latest_text("workbuddy ai")
        assert sess == "wbsess_1", f"应取行内 sessionId: {sess}"
        assert "[🧠 三明智 L2 完成 ✅]" in text, f"text 错: {text[:80]}"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED = old_src, old_en
    return "WB-AI wbai reader 解析 ✅"


def test_定向未命中不误配(t):
    """v1.3.3：--tool 指定端无数据 → (None,None) 不落无差别兜底（防他端会话误配·实锤于 WB-AI 首测）。"""
    root = os.path.join(t.base, "wbaiproj", "Users-x-wbai")
    os.makedirs(root, exist_ok=True)  # 目录在但无 jsonl = 该端无签名数据
    other = os.path.join(t.base, "autoclaw-hist")
    os.makedirs(other, exist_ok=True)
    with open(os.path.join(other, "agent%3Acloud-x%3A09e.json"), "w", encoding="utf-8") as f:
        json.dump([{"role": "assistant", "content": "[🧠 三明智 L1 完成 ✅]"}], f, ensure_ascii=False)
    old_src, old_en, old_hist = TS.JSONL_SOURCES, TS.JSONL_ENABLED, TS.HIST_DIR
    TS.JSONL_SOURCES = [("WorkBuddy AI", t.base, "wbaiproj/*/*.jsonl", "wbai")]
    TS.JSONL_ENABLED, TS.HIST_DIR = True, other
    try:
        sess, _ = TS.load_latest_text("workbuddy ai")
        assert sess is None, f"定向未命中应返回 None 不误配: {sess}"
    finally:
        TS.JSONL_SOURCES, TS.JSONL_ENABLED, TS.HIST_DIR = old_src, old_en, old_hist
    return "定向未命中不落兜底（防他端误配） ✅"


def test_text_file_封口与登记(t):
    """v1.4.0 方案C：--text-file 路径——不依赖读会话存储，直接封口+登记（全端通用主路径）。"""
    room = prepare(t)
    blk = os.path.join(t.base, "block.txt")
    with open(blk, "w", encoding="utf-8") as f:
        f.write("## L2 结果\n[🧠 三明智 L2 完成 ✅]")
    TS.HIST_DIR = os.path.join(t.base, "no_such_hist")  # 故意指向不存在目录：证明不依赖会话探测
    assert cli(["record", "--tool", "WorkBuddy", "--text-file", blk,
                "--followup", "全端覆盖测试", "--predict", "P", "--falsify", "F3", "--window", "W", "--depth", "L2"]) == 0
    log = open(TS.LOG_PATH, encoding="utf-8").read()
    assert "WorkBuddy:" in log, f"session 键应为 端名:sha1: {log}"
    assert "## FU-1 · 状态:待回访" in open(room, encoding="utf-8").read()
    return "--text-file 封口+登记（不依赖会话探测） ✅"


def test_text_file_空文本拒绝(t):
    """v1.4.0 Fail-Closed：--text-file 内容为空 → 拒绝封口（exit 1）。"""
    prepare(t)
    blk = os.path.join(t.base, "empty.txt")
    open(blk, "w", encoding="utf-8").write("   \n")
    assert cli(["record", "--tool", "WorkBuddy", "--text-file", blk]) == 1
    return "--text-file 空文本拒绝（Fail-Closed） ✅"


def test_fail_loud_无文本无会话(t):
    """v1.4.0 Fail-Loud：无 --text-file 且读不到会话历史 → exit 1，不再静默跳过。"""
    prepare(t)
    TS.HIST_DIR = os.path.join(t.base, "no_such_hist")
    TS.JSONL_ENABLED = False
    assert cli(["record", "--tool", "SomeEnd"]) == 1
    return "Fail-Loud 无文本无会话拦截 ✅"


def test_verify_text_file_对账(t):
    """v1.4.0：verify 与 record 同口径——--text-file 封的口能被 verify --text-file 对账上；
    篡改文本 → session 变 → 对账 FAIL（防伪不因新路径失效）。"""
    prepare(t)
    blk = os.path.join(t.base, "block.txt")
    with open(blk, "w", encoding="utf-8") as f:
        f.write("## L2 结果\n[🧠 三明智 L2 完成 ✅]")
    TS.HIST_DIR = os.path.join(t.base, "no_such_hist")
    assert cli(["record", "--tool", "WorkBuddy", "--text-file", blk]) == 0
    assert cli(["verify", "--tool", "WorkBuddy", "--text-file", blk]) == 0
    blk2 = os.path.join(t.base, "tampered.txt")
    with open(blk2, "w", encoding="utf-8") as f:
        f.write("## L2 结果\n[🧠 三明智 L2 完成 ✅]\n改过的内容")
    assert cli(["verify", "--tool", "WorkBuddy", "--text-file", blk2]) == 1
    return "verify --text-file 对账+篡改拦截 ✅"


def test_help自指契约(t):
    """v4.4.12·R4-TW-01 自指断言：--help 给出的调用形态必须真实可跑——
    旧版 help 写 `resolve FU-序号` 而实现只认裸数字（FU-FU-N 必失败+锚假阴性+诱导改标manual）。
    本考题把"文档教你=实现认的"钉成契约（同类"help/文档/实现三口径"防复发）。"""
    import subprocess
    r = subprocess.run([TS.sys.executable, "-B", TS.__file__, "--help"],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"首参 --help 必须 rc=0（收紧后契约），got rc={r.returncode}"
    assert "裸数字或 FU-N 均可" in r.stdout, "help 必须给出与实现一致的双形态 resolve 口径"
    assert "FU-序号" not in r.stdout, "help 内不得再出现实现不认的 FU-序号 形态"
    # FU-N 双形态兼容（文档/台账展示形不炸）
    prepare(t)
    rc = cli(["record", "--followup", "自指卡", "--predict", "P", "--falsify", "F",
              "--deadline", "2099-01-01", "--default", "no-op：维持", "--window", "1周"])
    assert rc == 0
    r2 = subprocess.run([TS.sys.executable, "-B", TS.__file__, "resolve", "FU-1",
                         "--actual", "A", "--bias", "B1", "--cause", "C", "--fix", "D"],
                        capture_output=True, text=True, timeout=30,
                        env={**TS.os.environ, "TRIWICH_DECISION_ROOM": TS.DECISION_ROOM_PATH,
                             "TRIWICH_SEAL_LOG": TS.LOG_PATH})
    assert "FU-FU" not in (r2.stdout + r2.stderr), f"双前缀消息/行为复发: {r2.stdout[:80]}"
    assert "已销账" in r2.stdout, f"FU-1 带前缀形态必须可销账: {r2.stdout[:80]}"
    # v4.4.13·R5-N4 加固：双形态"文档即测试"闭合——help 宣称的裸数字形态也必须真执行
    # （R5 变异体实证：只验 FU-N 一例时"裸数字被改坏"可单例绕过本契约）
    with open(TS.DECISION_ROOM_PATH, "a", encoding="utf-8") as fh:
        fh.write("\n## FU-2 · 状态:待回访\n- 任务：自指二卡\n- 判假方式：f\n")
    r3 = subprocess.run([TS.sys.executable, "-B", TS.__file__, "resolve", "2",
                         "--actual", "A", "--bias", "B1", "--cause", "C", "--fix", "D"],
                        capture_output=True, text=True, timeout=30,
                        env={**TS.os.environ, "TRIWICH_DECISION_ROOM": TS.DECISION_ROOM_PATH,
                             "TRIWICH_SEAL_LOG": TS.LOG_PATH})
    assert "已销账" in r3.stdout, f"裸数字形态必须同样可跑(双形态闭合): {r3.stdout[:80]}"
    return "help 自指契约（双形态真执行·双前缀清零） ✅"


def test_缺值族必拒(t):
    """v4.4.13·R5-N1/N5 回归断言（R5 实锤五例 B3/B4/B5/G1/G2 转必拒）：
    已知 flag 缺值/空值≠未提供——静默换源(v1.4.2 幻影链尾同伤害级)/回访静默蒸发/单横线被吞 三洞封死。"""
    import io as _io
    from contextlib import redirect_stdout as _rs

    def _c(argv):
        old = sys.argv
        sys.argv = ["triwich_seal.py"] + argv
        b = _io.StringIO()
        try:
            with _rs(b):
                rc = TS.main()
        finally:
            sys.argv = old
        return rc, b.getvalue()

    prepare(t)
    rc, out = _c(["record", "--tool", "T", "--text-file"])
    assert rc == 1 and "值为空" in out, f"record 缺值必须拒(旧版静默换源封他会话): rc={rc} {out[:80]}"
    rc, out = _c(["record", "--tool", "W", "--text-file", ""])
    assert rc == 1 and "值为空" in out, f"空串值必须拒(shell 变量空经典事故面): {out[:80]}"
    rc, out = _c(["verify", "--tool", "X", "--text-file"])
    assert rc == 1 and "值为空" in out, f"verify 缺值必须拒(旧版对账他人链态): {out[:80]}"
    rc, out = _c(["record", "--tool", "W", "--followup", ""])
    assert rc == 1 and "FOLLOWUP:FAIL" in out, f"--followup 空值不得静默蒸发回访义务: rc={rc} {out[:100]}"
    rc, out = _c(["record", "--tool", "X", "-h", "--text-file", "x"])
    assert rc == 1 and "未知参数" in out, f"单横线 -h 必须确定性拒绝(旧被静默吞后照常写链): {out[:80]}"
    rc, out = _c(["record", "-tool", "W", "--text-file", "x"])
    assert rc == 1 and "未知参数" in out and "·tool" in out, f"单横线已知别名 -tool 必须拒(v4.4.14·R6①旁路封死): rc={rc} {out[:80]}"
    return "缺值族六必拒（N1/N5/R6① 收口断言） ✅"


def main():
    tests = [test_help自指契约, test_缺值族必拒, test_全链路, test_负例_重复销账, test_负例_非法枚举, test_负例_缺四件套, test_续号,
             test_jsonl_wb_reader, test_jsonl_zcode_reader, test_jsonl_tool_routing, test_jsonl_签名段定位,
             test_封口幂等, test_jsonl_wbai_reader, test_定向未命中不误配,
             test_text_file_封口与登记, test_text_file_空文本拒绝, test_fail_loud_无文本无会话,
             test_verify_text_file_对账]
    fail = 0
    for fn in tests:
        t = T()
        try:
            print(f"[PASS] {fn(t)}")
        except AssertionError as e:
            fail += 1
            print(f"[FAIL] {fn.__name__}: {e}")
        finally:
            t.clean()
    print(f"\n结果: {len(tests) - fail}/{len(tests)} 通过" + (" ✅" if fail == 0 else f" · {fail} 失败 ❌"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
