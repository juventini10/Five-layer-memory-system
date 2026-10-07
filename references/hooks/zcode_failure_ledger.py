#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# zcode_failure_ledger.py — PostToolUseFailure 失败留痕引擎（T0 方案 C2·愿景③「报错→数据」落点）
# version: v1.0（2026-10-04·ZCode 童灵 D3·皮叔令「不追求速度只追求质量」）
#
# Disease：工具失败（报错/超时/拒绝）过去只活在当轮对话里——「报错→忽略」；
#   愿景③要求系统从自身运行数据学习·失败是最贵的运行数据·却零留痕。
#
# Verdict（mechanical·PostToolUseFailure·纯记录 exit 0 永不阻断）：
#   stdin JSON → 防御性提取（tool/错误详情）→ append-only JSONL 台账。
#
# ⚠️ 字段取证边界（诚实标注·不硬猜）：官方文档未细写本事件载荷 schema——
#   v1.0 按 Tool 事件族已知双形状（toolName/tool_name·ZCode/CC）宽松解析，
#   错误详情字段尽力提取（error/error_message/message/stderr/tool_input 命中即取），
#   全取不到 → 记 "unknown_failure"（留痕优先于精确·运行态真实样本落台账后再校准精化）。
#
# 回流链三段（01 规范 §二·十九·方案 v1.6 定稿）：
#   ①怎么写=本件 append-only 台账 ②何时写=PostToolUseFailure 事件驱动（无人值守也跑）
#   ③谁看=月度蒸馏 D2.5 工作模式信号管道（system-logger 联动·C-091「无人消费的记录是死数据」）
#   挂载=~/.zcode/cli/config.json → hooks.events.PostToolUseFailure（本事件端内首次使用）
try:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import os
import time
from pathlib import Path

GUARD = "zcode_failure_ledger.py"
LEDGER_DEFAULT = Path.home() / ".zcode" / "state" / "failure_ledger.jsonl"
ERROR_KEYS = ("error", "error_message", "errorMessage", "message", "stderr", "reason", "detail")


def _ledger():
    return Path(os.environ.get("ZCODE_FAILURE_LEDGER", str(LEDGER_DEFAULT)))


def _extract(payload):
    """防御性提取：双形状兼容·字段尽力·永不抛。返回 (tool, err)。"""
    if not isinstance(payload, dict):
        return "unknown_tool", "unknown_failure"
    tool = (payload.get("toolName") or payload.get("tool_name")
            or payload.get("tool") or "unknown_tool")
    err = ""
    for k in ERROR_KEYS:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            err = v.strip()
            break
    if not err:
        ti = payload.get("tool_input") or payload.get("toolInput") or {}
        if isinstance(ti, dict):
            for k in ERROR_KEYS:
                v = ti.get(k)
                if isinstance(v, str) and v.strip():
                    err = v.strip()
                    break
    if not err:
        # 嵌套 error 对象兜底（{error:{message}} 形状）
        e = payload.get("error")
        if isinstance(e, dict):
            for k in ("message", "error", "detail"):
                v = e.get(k)
                if isinstance(v, str) and v.strip():
                    err = v.strip()
                    break
    return str(tool), (err[:200] if err else "unknown_failure")


def record():
    raw = ""
    try:
        raw = sys.stdin.read() or ""
    except Exception:
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {"parse_note": raw[:120]}
    tool, err = _extract(payload)
    row = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tool": tool,
        "error": err,
        "session": os.environ.get("CLAUDE_SESSION_ID", "")[:36],
    }
    try:
        lg = _ledger()
        lg.parent.mkdir(parents=True, exist_ok=True)
        with open(lg, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass  # 台账失败静默（观测件·⛔不阻断主流程）
    return 0  # 纯记录·恒放行


def self_test():
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        lg = Path(td) / "failure_ledger.jsonl"
        os.environ["ZCODE_FAILURE_LEDGER"] = str(lg)
        import io as _io
        old = sys.stdin
        cases = [
            ('{"toolName":"Bash","error":"command not found: foo"}', "Bash", "command not found"),
            ('{"tool_name":"Edit","tool_input":{"error":"patch failed"}}', "Edit", "patch failed"),
            ('not-json-at-all', "unknown_tool", "unknown_failure"),
            ('', "unknown_tool", "unknown_failure"),
        ]
        for i, (sin, et, ee) in enumerate(cases, 1):
            sys.stdin = _io.StringIO(sin)
            try:
                assert record() == 0, f"T{i}"
            finally:
                sys.stdin = old
            rows = [json.loads(l) for l in lg.read_text(encoding="utf-8").splitlines()]
            assert rows[-1]["tool"] == et and ee in rows[-1]["error"], f"T{i}b"
            ok += 1
            print(f"✅ T{i} {['正常JSON','嵌套形状','垃圾stdin','空输入'][i-1]}→台账落行")
        assert len(rows) == 4, "T5"
        ok += 1
        print("✅ T5 append-only 四行不覆盖")
    os.environ.pop("ZCODE_FAILURE_LEDGER", None)
    print(f"自测结果: {ok}/5 通过")
    return 0 if ok == 5 else 1


def main():
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(record())


if __name__ == "__main__":
    main()
