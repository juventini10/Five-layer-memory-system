#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.2.0-lobsterai
"""
delivery_boundary_sending_guard.py — LobsterAI 端专属：外发边界守卫（message_sending 面）

为什么本端要另立一面（端独占质变·2026-10-06）：
  · delivery_boundary_guard.py（Stop 面）跑在 agent_end——**回复那时已经发出去��**，只能留账。
  · OpenClaw 独占面 `message_sending` 在**发送那一刻**拿到 `content` 正文本体
    ⇒ 可改写/可取消（Modify / gate），是 WB settings.json 端**不存在**的面。
  · 同一套判据（取舍词在、声明词缺），换到发送面前 = 从「事后留痕」升级为「当场拦下」。

输入契约（探针实证 · docs/plugins/hooks.md · message_sending）：
  stdin JSON: { "to":..., "content": <正文本体>, "replyToId":..., "threadId":..., "metadata":... }
  无 transcript_path（⛔不解析文件——content 已是本体，比回读 transcript 更省更准）。

输出契约（对齐脚本体系惯例）：
  exit 0 = 放行（默认·防误报优先）
  stdout 非空 = 违规提示（宿主可据此 decide；本脚本自身不改内容）
  台账：append-only 单行 JSON（并发安全·铁律014②）

安全：解析失败/无内容 → 静默 exit 0（⛔绝不因守卫失败阻断对话）
判据：沿用 delivery_boundary_guard 的取舍词/声明词口径（同一病源·同一把尺·⛔不各造一套）
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json, os, sys, time
from datetime import datetime

# 判据唯一住所 = delivery_boundary_common（⛔本件⛔内联词表·抽公共原语 v0.2.0）
from delivery_boundary_common import judge as _judge  # 真相仅一份


def main():
    try:
        raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
    except Exception:
        sys.exit(0)
    try:
        text = extract_text(payload.get("content"))
        if not text:
            sys.exit(0)
        violated, reason = _judge(text)
        if not violated:
            sys.exit(0)
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "epoch": int(time.time()),
            "hook": "message_sending",
            "to": str(payload.get("to", ""))[:120],
            "threadId": str(payload.get("threadId", ""))[:64],
            "reason": reason,
            "text_head": text[:200],
        }
        # append-only（铁律014②·并发零污染）
        try:
            os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
            with open(LEDGER, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        print("⚠️ 交付边界缺失（外发面）：%s——⛔本次拦下，请补上交代声明后再发。" % reason)
        sys.exit(0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
