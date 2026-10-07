#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feedback_detect.py — Stop 钩子：召回质量反馈信号自动检测器（检索自进化 P0 落地·2026-08-16）

背景：log_kb_feedback.py（P0 通道）只能手动调——"你说这条没用/漏了X"时靠 AI 记得跑，
     违反知识库宪法"不依赖 AI 记得"。本脚本把它变成机制级自动触发：
     各端 Stop 钩子挂本脚本 → 每轮结束自动扫描最近交互 → 检测反馈信号 → 自动调 log_kb_feedback 记录。

用法（Stop 钩子模式·与 audit_search_kb 同协议）：
  echo '{"transcript_path": "..."}' | python3 feedback_detect.py
  python3 feedback_detect.py --transcript <path>     # 直接传路径
  python3 feedback_detect.py --self-test              # 内置自测

检测信号（当前版本·保守判定）：
  - 用户消息含"这条没用"/"没用"/"不对/不对呀"（对检索结果的否定）→ 类型=这条没用
  - 用户消息含"漏了X"/"漏了"/"少了X"（检索缺了什么）→ 类型=漏了X
  - 用户消息含"采纳"/"用这个"/"就用这个"（采纳某结果）→ 类型=采纳
  - ⛔ 保守判定：宁可漏记不可误记（误记=污染 MAB 训练数据）

设计原则（Hook 三纪律·守卫编写规范 §八）：
  - 只记录不拦截（exit 0 恒放行）
  - 失败默认放行（解析异常/无输入 → exit 0）
  - 保守判定（检测信号用硬信号词，不用泛词）

跨工具中立（脚本架构通用规范 §二·五）：公共脚本住开发工具/知识联邦引擎/scripts/，
  任何端（DSH/WorkBuddy/Qoder/AutoClaw）Stop 钩子接入即生效；⛔ 不绑定任何单端。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
import transcript_reader as _tr  # 跨端解析·单一真源（2026-09-23 童灵根治）

FEEDBACK_TYPES = {"这条没用", "漏了X", "采纳"}

# 反馈信号硬词（保守·宁可漏记不可误记）
SIGNAL_PATTERNS = [
    # (类型, 用户消息正则, 说明)
    ("这条没用", r"(这条|这个|这些|刚才).{0,6}(没用|不行|不对|不相关|跑偏)", "检索结果被否定"),
    ("这条没用", r"这条(卡|结果|内容).{0,4}(不要|删掉|去掉)", "检索结果被要求移除"),
    ("漏了X", r"(漏了|少了|缺了|还缺).{0,12}", "检索缺内容（用户指出漏了什么）"),
    ("采纳", r"(就|用|选)(这个|这条|这张|这卡)", "结果被采纳"),
]


def read_transcript(path):
    """读 CC 格式 JSONL transcript → [(role, text)]（与 route_audit 同构）"""
    msgs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            role, content = _tr.locate(d)
            msgs.append((role, _tr.flatten_content(content)))
    return msgs


def detect(msgs):
    """检测最近一轮交互的反馈信号。返回 (task, 类型, 补充词) 或 None。
    取最后一个 user 消息为任务，在其后的 assistant 回复中找信号（回复否定=这条没用）。"""
    if not msgs:
        return None
    # 找最后一则 user 消息（排除系统提醒）
    last_user_idx = None
    for i in range(len(msgs) - 1, -1, -1):
        role, text = msgs[i]
        if role == "user" and text.strip() and not text.startswith("<system-reminder"):
            last_user_idx = i
            break
    if last_user_idx is None:
        return None
    user_text = msgs[last_user_idx][1]
    # 信号检测：优先看用户消息本身（含"漏了X"类），再看其后的 assistant 回复前 500 字（含"这条没用"类）
    after_text = " ".join(t for role, t in msgs[last_user_idx + 1:] if role == "assistant")[:500]
    for ftype, pat, desc in SIGNAL_PATTERNS:
        if re.search(pat, user_text):
            # 漏了X 类需语境确认（防日常误报如"漏了打卡"）：本消息或前一条 user 消息含检索/知识语境
            if ftype == "漏了X":
                prev_task = ""
                for j in range(last_user_idx - 1, -1, -1):
                    if msgs[j][0] == "user" and msgs[j][1].strip() and not msgs[j][1].startswith("<system-reminder"):
                        prev_task = msgs[j][1]
                        break
                ctx = user_text + " " + prev_task
                if not re.search(r"(卡|书|知识|内容|方法|文案|角度|视角|检索|搜索|参考|资料|素材|信息|提示|借势|主角|写作|读书)", ctx):
                    continue
            # task = 最近的非反馈任务（回溯：反馈消息往前找真正的任务）
            task = prev_task if ftype == "漏了X" and prev_task else user_text
            return task[:100], ftype, desc
    # "这条没用"通常出现在下一轮用户消息（看到注入结果后否定）——若本 user 消息是否定反馈，捕获
    if re.search(r"(这条|这个|这些).{0,6}(没用|不行|不对)", user_text):
        return user_text[:100], "这条没用", "检索结果被否定（用户消息内）"
    return None


def record(task, ftype, desc):
    """调 log_kb_feedback.py 记录（复用 P0 通道·单一真源）"""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_kb_feedback.py")
    if not os.path.isfile(script):
        print(f"⚠️ log_kb_feedback.py 不存在: {script}", file=sys.stderr)
        return
    import subprocess
    subprocess.run([sys.executable, script, task, "自动检测", ftype], capture_output=True, timeout=15)


def self_test():
    import tempfile
    # 用例1：用户说"这条没用" → 检测命中 这条没用
    t1 = tempfile.mktemp(suffix=".jsonl")
    with open(t1, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "写碎碎念文案"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "这是三张卡..."}]}}) + "\n")
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "这条没用，换别的"}]}}) + "\n")
    r1 = detect(read_transcript(t1))
    ok1 = r1 and r1[1] == "这条没用"
    # 用例2：用户说"漏了借势" → 检测命中 漏了X
    t2 = tempfile.mktemp(suffix=".jsonl")
    with open(t2, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "写碎碎念文案"}]}}) + "\n")
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "漏了借势和主角"}]}}) + "\n")
    r2 = detect(read_transcript(t2))
    ok2 = r2 and r2[1] == "漏了X"
    # 用例3：普通对话（无反馈信号）→ 不检测
    t3 = tempfile.mktemp(suffix=".jsonl")
    with open(t3, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "user", "message": {"content": [{"type": "text", "text": "今天天气不错"}]}}) + "\n")
        f.write(json.dumps({"role": "assistant", "message": {"content": [{"type": "text", "text": "是的，天气很好"}]}}) + "\n")
    r3 = detect(read_transcript(t3))
    ok3 = r3 is None
    print(f"用例1 这条没用检测: {'✅' if ok1 else '❌'} {r1}")
    print(f"用例2 漏了X检测: {'✅' if ok2 else '❌'} {r2}")
    print(f"用例3 普通对话不误报: {'✅' if ok3 else '❌'} {r3}")
    return 0 if all([ok1, ok2, ok3]) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        tp = payload.get("transcript_path")
    except (json.JSONDecodeError, ValueError):
        tp = None
    if not tp and len(sys.argv) > 2 and sys.argv[1] == "--transcript":
        tp = sys.argv[2]
    if not tp or not os.path.isfile(tp):
        sys.exit(0)  # 失败放行
    try:
        msgs = read_transcript(tp)
        hit = detect(msgs)
        if hit:
            task, ftype, desc = hit
            record(task, ftype, desc)
            print(f"📝 反馈信号已自动记录: task={task[:30]}... type={ftype} ({desc})")
        sys.exit(0)
    except Exception:
        sys.exit(0)  # 任何异常放行
