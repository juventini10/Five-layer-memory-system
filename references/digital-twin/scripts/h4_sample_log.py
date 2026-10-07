#!/usr/bin/env python3
"""h4_sample_log.py —— H4 冲突样本采集网关（O_APPEND 原子追加）

目的：攒"冲突标注态 → 你裁决"配对样本，供未来算 H4 冲突裁决误判率混淆矩阵。
触发：规格书增量刷新路径中，任何"冲突项标'待你质证'"发生时，AI 组装一条 JSON 经 stdin 传入。

用法: echo '<json>' | python3 h4_sample_log.py
字段: source(触发源) / claim(冲突断言摘要) / action(标注态) / verdict(你裁决) / note(备注·可选)
时间: 脚本内部捕获（AI 接触不到时间值，物理防漂移·同 memlog/append_log_entry 精神）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, json, datetime, os

LOG = os.path.expanduser("[记忆共享中心]/数字分身/steps/h4-conflict-samples.jsonl")
REQUIRED = {"source", "claim", "action", "verdict"}


def main():
    raw = sys.stdin.buffer.read().decode('utf-8', errors='replace').strip()
    if not raw:
        print("usage: echo '<json>' | python3 h4_sample_log.py", file=sys.stderr)
        sys.exit(2)
    try:
        rec = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}", file=sys.stderr)
        sys.exit(2)
    missing = REQUIRED - set(rec)
    if missing:
        print(f"缺字段: {missing}", file=sys.stderr)
        sys.exit(2)
    rec["ts"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rec.setdefault("note", "")
    line = json.dumps(rec, ensure_ascii=False)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print("APPENDED", LOG)
    print("REC", line)


if __name__ == "__main__":
    main()
