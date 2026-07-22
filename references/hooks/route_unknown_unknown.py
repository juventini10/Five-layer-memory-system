#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
未知未知路由钩子（非 LLM 层 · 兜底自动路由）

挂为 WorkBuddy 原生 Stop 钩子（~/.workbuddy/settings.json）。
每次主代理结束响应时，WorkBuddy 通过 stdin 传入 JSON，含 transcript_path
（完整对话 JSONL）。本脚本解析最后一则 assistant 消息：

  - 若含 `【🕳️ 我的未知未知】` 段 → 提取盲区描述，按悬置区.md §1.6 schema
    自动 append 一条 T5 / AI盲区 / 来源对话 的残差条目（兜底路由）。
  - 其余一切情况 → 退出码 0 = 放行（绝不拦截、绝不误写）。

设计原则（失败默认放行，绝不破坏对话）：
  - 解析异常 / 无 transcript_path / 行损坏 → 直接 exit 0
  - 无 🕳️ 段 → exit 0（不写）
  - 去重：同一盲区文本已落盘（AI 当轮手动 Write 或本钩已写）→ 跳过，不重复
  - 任何未捕获异常 → exit 0

来源：悬置区.md §1.6 schema + SOUL.md v3.10 【🕳️】段（T5 路由）

注：本脚本随布洛陀安装包装载。默认路径含 `[记忆共享中心]` 占位符，
    由安装步骤（step6-hook-install）在执行机替换为用户真实记忆中心路径。
    也可用环境变量 UU_TARGET / UU_STATE / UU_HEARTBEAT 重定向（便于隔离测试）。
"""
import sys
import os
import re
import json
import hashlib
from datetime import datetime

DEFAULT_TARGET = "[记忆共享中心]/未知未知/悬置区.md"
TARGET = os.environ.get("UU_TARGET", DEFAULT_TARGET)  # 测试可重定向
DEFAULT_STATE = "[记忆共享中心]/未知未知/.route_state.json"
STATE_PATH = os.environ.get("UU_STATE", DEFAULT_STATE)  # 测试可重定向
DEFAULT_HEARTBEAT = "[记忆共享中心]/未知未知/.route_heartbeat.json"
HEARTBEAT_PATH = os.environ.get("UU_HEARTBEAT", DEFAULT_HEARTBEAT)  # 调度心跳·测试可重定向

MARKER_RE = re.compile(r'【🕳️\s*我的未知未知】\s*\n?([\s\S]*?)(?=\n【|\n\[|$)')
RESIDUE_RE = re.compile(r'###\s*残差#(\d+)')


def normalize(text: str) -> str:
    """归一化：去首尾空白 + 合并内部所有空白为单空格。
    用于去重比较，使「手动 Write 文本」与「钩子从 transcript 提取文本」
    即使换行/全半角空格有微差也能判为同一条，杜绝重复污染。"""
    return re.sub(r'\s+', ' ', text.strip())


def extract_text(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(content)


def parse_transcript(path):
    msgs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            role = obj.get("role")
            content = obj.get("content")
            if content is None and isinstance(obj.get("message"), dict):
                m = obj["message"]
                if role is None:
                    role = m.get("role")
                content = m.get("content")
            if role is None and obj.get("type") in ("user", "assistant"):
                role = obj["type"]
                content = obj.get("content")
            if role is None:
                continue
            text = extract_text(content)
            if text:
                msgs.append((role, text))
    return msgs


def next_index(target_text: str) -> int:
    nums = [int(m.group(1)) for m in RESIDUE_RE.finditer(target_text)]
    return (max(nums) + 1) if nums else 0


def already_routed(text: str, target_text: str) -> bool:
    n = normalize(text)
    # 1) 文本已落盘（覆盖 AI 当轮手动 Write 的情况，归一化比较抗微差）
    if n and n in normalize(target_text):
        return True
    # 2) 本钩状态表（覆盖同轮多次 Stop）
    h = hashlib.sha256(n.encode("utf-8")).hexdigest()[:16]
    try:
        if os.path.isfile(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            if h in state:
                return True
    except Exception:
        pass
    return False


def mark_routed(text: str):
    h = hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]
    state = {}
    try:
        if os.path.isfile(STATE_PATH):
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
    except Exception:
        state = {}
    state[h] = datetime.now().isoformat(timespec="seconds")
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def build_entry(index: int, date: str, description: str) -> str:
    return (
        f"### 残差#{index:03d} · {date}\n"
        f"- 触发: T5\n"
        f"- 归属: AI盲区\n"
        f"- 来源: 对话\n"
        f"- 记录者: AI\n"
        f"- 状态: 悬置(未闭合)\n"
        f"- 毛坯描述: {description.strip()}\n"
        f"- 显形: (待月报回看)"
    )


def insert_entry(target_text: str, entry: str) -> str:
    sep = "\n---\n\n---\n\n## 三、被动诱捕状态"
    if sep in target_text:
        return target_text.replace(sep, "\n\n" + entry + sep, 1)
    # 兜底：直接追加到文件末尾
    return target_text.rstrip() + "\n\n" + entry + "\n"


def mark_heartbeat():
    """钩子每次被 Stop 调度即写时间戳——与是否写入残差解耦的「调度证明」信号。
    放在 main 最前调用，确保只要被调度就记录，不被后续去重/无🕳️/异常吞掉。
    职责分离：heartbeat=是否被调度；state=已落盘 hash（去重用）；悬置区=实际残差条目。"""
    try:
        data = {"last_run": "", "count": 0}
        if os.path.isfile(HEARTBEAT_PATH):
            try:
                with open(HEARTBEAT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["count"] = int(data.get("count", 0)) + 1
        data["last_run"] = datetime.now().isoformat(timespec="seconds")
        with open(HEARTBEAT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main() -> int:
    mark_heartbeat()  # 调度即记心跳（与任何结果解耦）
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except Exception:
        return 0

    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0

    try:
        msgs = parse_transcript(transcript_path)
    except Exception:
        return 0

    if not msgs:
        return 0

    last_assistant = None
    for role, text in reversed(msgs):
        if role == "assistant":
            last_assistant = text
            break
    if not last_assistant:
        return 0

    m = MARKER_RE.search(last_assistant)
    if not m:
        return 0  # 无 🕳️ 段

    blind = m.group(1).strip()
    if not blind:
        return 0

    # 去重检查
    try:
        with open(TARGET, "r", encoding="utf-8") as f:
            target_text = f.read()
    except Exception:
        return 0

    if already_routed(blind, target_text):
        return 0

    idx = next_index(target_text)
    date = datetime.now().strftime("%Y-%m-%d")
    entry = build_entry(idx, date, blind)
    new_text = insert_entry(target_text, entry)

    try:
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(new_text)
    except Exception:
        return 0

    mark_routed(blind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
