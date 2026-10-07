#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
hermes_read_evidence_guard.py — Hermes 会话级「读文件证据」检测守卫

根因（2026-08-22）：
    SOUL.md 写了"先读后动"但频繁违反——AI 凭 MEMORY.md 摘要或印象做
    判断，未真正 read_file 原文。成长箱 1985 条纠正中高频出现"凭记忆"。

检测逻辑（会话结束后）：
    ① 解析 transcript，找 AI 输出中所有"引用文件内容"的断言（含
       "根据X"/"读了X"/"X中说"/"见X"/文件名+具体行号/内容描述）。
    ② 对应查找该 session 中是否有 read_file 工具调用命中同一文件。
    ③ 有断言但无 read_file → 漂移（凭印象/凭摘要判断）。
    ④ 仅检测"涉及文件内容"的断言（面板数据/守卫结果/SSOT 状态等），
       纯逻辑推论/通用知识不断处（宁漏勿误）。

用法：
    python3 hermes_read_evidence_guard.py <transcript.jsonl>
    python3 hermes_read_evidence_guard.py --dir <session_dir>  # 自动找最新 transcript / request_dump_*.json

退出码：
    0 = 无漂移（所有文件断言均有 read_file 证据）
    1 = 漂移（至少 1 条断言无证据）
    2 = 用法/文件错误

设计原则（符合愿景）：
    - 全自动化：on_session_end 调用，零人工
    - 越用越好用：漂移记录反馈给 AI 改进
    - 更懂你：减少"凭印象"错误，判断更准
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import re
import sys
from pathlib import Path

HOME = os.path.expanduser("~")
MC = os.path.join(HOME, os.path.expanduser("~"))

# 文件引用模式：AI 输出中"引用了文件内容"的断言标志
FILE_REF_PATTERNS = [
    # "根据X"/"读了X"/"见X"/"X 中说"
    re.compile(r"(?:根据|读了|见|参考|依据|来自|引用|查了|看了)\s*"
               r"[「『\"']?\s*([A-Za-z0-9_./\-]+\.(?:md|py|sh|json|yaml|js|html))"
               r"[」』\"']?"),
    # "X 第Y行" / "X 中的Y" / "X 写：..." 
    re.compile(r"([A-Za-z0-9_./\-]+\.(?:md|py|sh|json|yaml))\s*"
               r"(?:第\s*\d+\s*行|中(?:的)?|写\s*[:：]|说\s*[:：])"),
    # "见 §X.Y" + 文件名上下文
    re.compile(r"(?:见|参见)\s*[§§]?\s*\d+\.\d+.*?"
               r"([A-Za-z0-9_./\-]+\.(?:md|py|sh|json|yaml))"),
]

# 纯逻辑/通用知识标志（不断为漂移）
GENERAL_KNOWLEDGE = re.compile(
    r"(?:第一性原理|实事求是|三问|四方向|SOUL|铁律|成长箱|"
    r"WorkBuddy|Qoder|布洛陀|素然启镜|热点捕手)"
)

# 会话中常见"文件名 + 具体描述"（文件名+行号/内容片段引用）
SPECIFIC_REF = re.compile(
    r"([A-Za-z0-9_./\-]+\.(?:md|py|sh|json|yaml|js|html))"
    r"\s*(?:第\s*\d+|行\s*\d+|[:：]\s*[^【】\s]|中写|中说|的版本|的接入率)"
)
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def parse_transcript(input_path):
    """解析 transcript，支持两种格式：
    1. transcript.jsonl：每行一个消息对象（Hermes 旧格式）
    2. request_dump_*.json：Hermes 实际格式，request.body.messages 数组
    """
    msgs = []
    # 判断格式
    if input_path.endswith('.json'):
        # request_dump_*.json 格式
        with open(input_path, encoding="utf-8") as f:
            obj = json.load(f)
        raw_msgs = obj.get("request", {}).get("body", {}).get("messages", [])
        for m in raw_msgs:
            role = m.get("role", "")
            content = m.get("content", "") or ""
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                )
            tool_calls = m.get("tool_calls", [])
            msgs.append((role, content, tool_calls))
    else:
        # transcript.jsonl 格式（旧）——2026-09-23 童灵根治：收敛到共享解析层
        # （守卫编写规范 §3.12 单一入口律）。
        # ⚠️ 上方 `request_dump_*.json` 分支**刻意保留自写**：那是 Hermes 端专属结构
        #    （request.body.messages 数组），属"端专属补偿"，共享层不覆盖也不同步
        #    （跨端口诀：无钩子端的补偿方案，有钩子端不要抄）。
        import sys as _sys
        _root = os.path.expanduser("[记忆共享中心]/脚本中心")
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        try:
            import transcript_reader as _tr
            _locate, _flatten = _tr.locate, _tr.flatten_content
        except Exception:
            def _locate(d):
                return (d.get("role", ""), d.get("content"))

            def _flatten(c):
                return c if isinstance(c, str) else ""

        with open(input_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                role, content = _locate(obj)
                tool_calls = obj.get("tool_calls", [])
                msgs.append((role, _flatten(content), tool_calls))
    return msgs


def extract_read_files(msgs):
    """从 tool_calls 中提取所有 read_file 调用的文件路径（归一化为文件名）"""
    read_files = set()
    for role, content, tool_calls in msgs:
        for tc in tool_calls:
            func = tc.get("function", {})
            if func.get("name") == "read_file":
                args = func.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        continue
                path = args.get("path", "")
                if path:
                    # 归一化：只取 basename（大小写不敏感匹配）
                    read_files.add(os.path.basename(path).lower())
                    # 同时保留归一化后的 stem
                    stem = os.path.splitext(os.path.basename(path))[0].lower()
                    read_files.add(stem)
    return read_files


def detect_drift(msgs, read_files):
    """检测漂移：AI 声称读了文件但实际没调 read_file"""
    drift = []
    for role, content, tool_calls in msgs:
        if role != "assistant":
            continue
        # 提取该条输出中所有文件引用
        claimed_files = set()
        for pat in FILE_REF_PATTERNS:
            for m in pat.finditer(content):
                claimed_files.add(m.group(1).lower())
        for m in SPECIFIC_REF.finditer(content):
            claimed_files.add(m.group(1).lower())
        
        # 过滤通用知识引用（不断为漂移）
        claimed_files = {
            f for f in claimed_files
            if not GENERAL_KNOWLEDGE.search(f)
        }
        
        # 检查每个声称是否有 read_file 证据
        for cf in claimed_files:
            basename = os.path.basename(cf).lower()
            stem = os.path.splitext(basename)[0]
            if basename not in read_files and stem not in read_files:
                # 无 read_file 证据 → 漂移
                # 提取断言上下文（前后 30 字）
                idx = content.lower().find(cf[:10])
                ctx = content[max(0, idx-30):idx+60] if idx >= 0 else content[:80]
                drift.append({
                    "file": cf,
                    "context": ctx.strip(),
                    "reason": f"引用了 {cf} 的内容，但本 session 无 read_file({cf}) 调用"
                })
    return drift


def main():
    ap = argparse.ArgumentParser(description="Hermes 会话读文件证据检测")
    ap.add_argument("transcript", nargs="?", help="transcript.jsonl 路径")
    ap.add_argument("--dir", help="session 目录（自动找最新 transcript / request_dump_*.json）")
    ap.add_argument("--session-id", help="session ID，用于精确定位 request_dump 文件名（优先级高于 --dir 自动选最新）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    transcript_path = args.transcript
    if args.dir:
        # 自动找最新 transcript（支持两种格式）
        tdir = Path(args.dir)
        # 优先找 transcript.jsonl，其次找 request_dump_*.json
        candidates = sorted(tdir.glob("**/transcript.jsonl"), reverse=True)
        if not candidates:
            candidates = sorted(tdir.glob("**/request_dump_*.json"), reverse=True)
        if not candidates:
            # 也支持直接在 sessions 目录下找
            candidates = sorted(Path(args.dir).glob("request_dump_*.json"), reverse=True)
        if not candidates:
            print(f"[ERR] 未找到 transcript 或 request_dump in {args.dir}", file=sys.stderr)
            return 2
        # 有 session-id 时，优先匹配文件名含该 id 的 dump
        if args.session_id:
            matched = [c for c in candidates if args.session_id in c.name]
            if matched:
                transcript_path = str(matched[0])
            else:
                # 宁缺勿假（愿景·诚实判据）：session-id 未命中即显错，
                # 不静默降级到"全目录最新"——否则会拿别的会话的 read_file 证据
                # 误判本次会话，产生错误归属的检测数据，且无法被自身发现。
                print(
                    f"[ERR] 未找到 session_id={args.session_id} 对应的 request_dump "
                    f"（宁缺勿假：不拿其他会话顶包误判）",
                    file=sys.stderr,
                )
                return 2
        else:
            transcript_path = str(candidates[0])

    if not transcript_path or not os.path.exists(transcript_path):
        print(f"[ERR] 文件不存在: {transcript_path}", file=sys.stderr)
        return 2

    msgs = parse_transcript(transcript_path)
    if not msgs:
        print("[ERR] 空 transcript", file=sys.stderr)
        return 2

    read_files = extract_read_files(msgs)
    drift = detect_drift(msgs, read_files)

    if args.json:
        print(json.dumps({
            "read_files": sorted(read_files),
            "drift_count": len(drift),
            "drift": drift[:10],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"本 session 实际 read_file: {len(read_files)} 个文件")
        for f in sorted(read_files):
            print(f"  ✅ {f}")
        print()
        if drift:
            print(f"⚠️ 漂移（引用但无 read_file 证据）: {len(drift)} 处")
            for d in drift[:10]:
                print(f"   - {d['reason']}")
                print(f"     上下文: {d['context'][:60]}")
        else:
            print("✅ 无漂移（所有文件引用均有 read_file 证据）")

    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
