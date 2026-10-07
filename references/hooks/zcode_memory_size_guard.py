#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# zcode_memory_size_guard.py — MEMORY.md 尺寸守卫（T0 方案 B2·吸收 WorkBuddy memory-size-guard·PreToolUse 事前拦）
# version: v1.0（2026-10-04·ZCode 童灵 D3·G0 裁决「接」）
#
# Disease：auto-memory 的 MEMORY.md=每会话常驻注入的索引——它只增不减时，
#   每次会话的注入成本与索引噪音单调上涨；WB 端有 ≤3800 机械拦（Stop 事后），本端此前无。
#
# Verdict（mechanical·PreToolUse·matcher=Write|Edit·只管 MEMORY.md）：
#   主判据=行数（索引膨胀的直接语义）·辅判=字节（防超长单行）。
#   **拦截判定域（方案 v1.3 修正③·L3 审查定稿）**：仅拦「使文件增大且已超限」的写入；
#   缩减类编辑一律放行——否则超限后的修复写入会被自己的闸拦死（死锁·B 审查发现）。
#
# 阈值：行数默认 40（现值 30+25% 余量·ZCODE_MEM_LINES_MAX 可覆盖）·字节 12000（辅判）。
# 台账：~/.zcode/state/memory_size_guard.jsonl（拦截与放行超限事件·append-only）。
# 回流链（§二·十九）：①本件②PreToolUse 事件驱动③消费=WB 蒸馏/归档流程由人触发·本件只拦不改（C-091：台账消费=拦截动作本身+月度复盘）。
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

GUARD = "zcode_memory_size_guard.py"
MEM_DIR_DEFAULT = Path.home() / ".zcode" / "cli" / "memories"


def _mem_dir():
    """动态读 env——模块级冻结会废掉自测夹具（T2 先例·本件首版即犯第三次·当场被抓）。"""
    return Path(os.environ.get("ZCODE_MEM_DIR", str(MEM_DIR_DEFAULT)))
LINES_MAX = int(os.environ.get("ZCODE_MEM_LINES_MAX", "40"))
BYTES_MAX = int(os.environ.get("ZCODE_MEM_BYTES_MAX", "12000"))
LEDGER_DEFAULT = Path.home() / ".zcode" / "state" / "memory_size_guard.jsonl"


def _is_target(fp: str):
    p = Path(fp).expanduser()
    try:
        p.relative_to(_mem_dir())
    except ValueError:
        return False
    return p.name == "MEMORY.md"


def _count_lines_bytes(text: str):
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0), len(text.encode("utf-8"))


def _ledger(row):
    try:
        lg = Path(os.environ.get("ZCODE_MEM_GUARD_LEDGER", str(LEDGER_DEFAULT)))
        lg.parent.mkdir(parents=True, exist_ok=True)
        with open(lg, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError:
        pass


def check():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0  # fail-open（观测面垃圾输入不阻断正常工作）
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    if not _is_target(str(fp)):
        return 0
    tool = payload.get("toolName") or payload.get("tool_name") or ""
    cur_text = ""
    if Path(fp).is_file():
        try:
            cur_text = Path(fp).read_text(encoding="utf-8")
        except OSError:
            pass
    cur_lines, cur_bytes = _count_lines_bytes(cur_text)
    if tool == "Write":
        new_text = ti.get("content") or ""
    else:  # Edit：old→new 差量估算新体量
        old_s = ti.get("old_string") or ""
        new_s = ti.get("new_string") or ""
        new_text = cur_text.replace(old_s, new_s, 1) if (old_s or new_s) else cur_text
    new_lines, new_bytes = _count_lines_bytes(new_text)
    over = new_lines > LINES_MAX or new_bytes > BYTES_MAX
    growing = new_lines >= cur_lines and new_bytes >= cur_bytes
    row = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "file": str(fp),
           "cur": f"{cur_lines}L/{cur_bytes}B", "new": f"{new_lines}L/{new_bytes}B",
           "verdict": "block" if (over and growing) else "pass"}
    _ledger(row)
    if over and growing:
        print(json.dumps({
            "alarm": True,
            "reason": f"MEMORY.md 写入后 {new_lines} 行/{new_bytes}B 超限（阈值 {LINES_MAX} 行/{BYTES_MAX}B）且为增量写入——"
                      f"索引只增不减=每会话注入成本与噪音单调上涨（吸收 WB memory-size-guard·B2）",
            "fix": "先瘦身再写：老条目按 [[name]] 归档到 memory/ 下单件文件（MEMORY.md 只留一行指针），"
                   "或蒸馏合并同族条目——缩减类写入本闸放行（防死锁设计）"
        }, ensure_ascii=False))
        return 2
    return 0


def self_test():
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        mem = td / "memories" / "projects" / "p1" / "memory"
        mem.mkdir(parents=True)
        memfile = mem / "MEMORY.md"
        # 夹具=贴近阈值边缘的实盘同形结构（§二·十九 判据7：夹具须实盘衍生——索引行「- [名](件.md) — 钩」）
        base = "\n".join(f"- [条目{i}](item-{i}.md) — 钩子描述若干字" for i in range(int(os.environ.get("ZCODE_MEM_LINES_MAX", "40")) - 2))
        memfile.write_text(base + "\n", encoding="utf-8")
        os.environ["ZCODE_MEM_DIR"] = str(td / "memories")
        os.environ["ZCODE_MEM_GUARD_LEDGER"] = str(td / "ledger.jsonl")
        import io as _io
        old = sys.stdin
        def run(payload):
            sys.stdin = _io.StringIO(json.dumps(payload, ensure_ascii=False))
            try:
                return check()
            finally:
                sys.stdin = old
        # T1 未超限写入→放行
        assert run({"toolName": "Write", "tool_input": {"file_path": str(memfile), "content": base + "\n- [新增](n.md) — 一条\n"}}) == 0, "T1"
        ok += 1; print("✅ T1 未超限放行")
        # T2 超限增大→拦（exit 2）
        big = base + "\n".join(f"\n- [填充{i}](f{i}.md) — 迫超阈值" for i in range(6))
        rc = run({"toolName": "Write", "tool_input": {"file_path": str(memfile), "content": big}})
        assert rc == 2, "T2"
        ok += 1; print("✅ T2 超限增量拦截")
        # T3 超限缩减→放行（防死锁关键负例）
        slim = "\n".join(f"- [瘦{i}](s{i}.md) — 钩" for i in range(5))
        assert run({"toolName": "Write", "tool_input": {"file_path": str(memfile), "content": slim}}) == 0, "T3"
        ok += 1; print("✅ T3 超限缩减放行（防死锁）")
        # T4 非目标文件→放行
        assert run({"toolName": "Write", "tool_input": {"file_path": str(td / "other.md"), "content": "x" * 20000}}) == 0, "T4"
        ok += 1; print("✅ T4 非目标文件放行")
        # T5 垃圾 stdin→不崩
        sys.stdin = _io.StringIO("garbage-not-json")
        try:
            assert check() == 0, "T5"
        finally:
            sys.stdin = old
        ok += 1; print("✅ T5 垃圾输入不崩")
    for k in ("ZCODE_MEM_DIR", "ZCODE_MEM_GUARD_LEDGER"):
        os.environ.pop(k, None)
    print(f"自测结果: {ok}/5 通过")
    return 0 if ok == 5 else 1


def main():
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(check())


if __name__ == "__main__":
    main()
