#!/usr/bin/env python3
# version: v0.2（2026-10-13 同名分叉合并：端运行体功能面 × 源去硬编码意图，双修源侧 Path 用法断裂）
"""session_tail_inject.py — UserPromptSubmit 钩子：新会话首 prompt 自动注入"上次收工+待办欠账"。

愿景依据（SSOT=[记忆共享中心]/README.md §演进愿景）：
    ①全自动化——"上次干到哪/有什么欠账"不再依赖人记得。
数据源（2026-09-09 实盘核验·只用真实存在的数据）：
    ① 上次收工状态：昨日+今日系统日志最后一条条目（标题/工具/时间）
    ② 机械待办计数：成长箱反哺积压（drain-backlog）+ 错误候选待确认数
注入通道：stdout 文本块（与 kb_inject_prompt 同形态）；无数据则静默零注入。
防重入：状态文件 $WORKBUDDY_CONFIG_DIR/cache/tail-inject/<session_id>.json（端中立·官方 env 优先·兜底 ~/.workbuddy；仿 title-namer）。
安全：任何异常 exit 0 静默降级，钩子绝不阻塞主流程。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

MC_ROOT = os.path.expanduser("[记忆共享中心]")  # relocate 锚定行（包态被占位符替换后 Path() 仍可解析）
LOG_DIR = Path(MC_ROOT) / "工作日志" / "系统日志"  # 2026-10-17 G案根治：旧形被占位化后成 str/str 静默崩
_CFG_ROOT = Path(os.environ.get("WORKBUDDY_CONFIG_DIR") or (Path.home() / ".workbuddy"))
STATE_DIR = _CFG_ROOT / "cache" / "tail-inject"
GROWTH_DIR = Path(MC_ROOT) / "成长箱"
MAX_INJECT_LINES = 8


def read_stdin_session_id() -> str:
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip().startswith("{") else {}
        return str(payload.get("session_id", "")).strip()
    except Exception:
        return ""


def last_log_entry(days_back: int = 2):
    """读最近 days_back 天系统日志，返回最后一条条目的 (日期, 标题, 工具, 完成时间) 或 None。"""
    for offset in range(days_back):
        day = datetime.now() - timedelta(days=offset)
        path = LOG_DIR / f"系统日志_{day.strftime('%Y-%m-%d')}.md"
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        entries = re.findall(r"^### (.+)$", text, re.M)
        if not entries:
            continue
        title = entries[-1].strip()
        # 最后一条条目块内找 工具/完成 行（向后取块）
        tail = text[text.rfind(f"### {title}"):]
        # 兼容两种格式：标准 8 字段「- **工具**：X / - **完成**：HH:MM」与
        # 异构端「**完成：YYYY-MM-DD HH:MM**」（无工具字段·2026-09-09 实盘发现）
        # 2026-09-11 修：原式 \S{1,12} 只吃非空白 → 含空格规范名被截断
        #   （WorkBuddy AI→WorkBuddy / Trae Work→Trae / Qoder CN→Qoder）→ 改取整行到行尾
        tool_m = re.search(r"\*\*工具\*\*：\s*([^\n]+?)\s*$", tail, re.M)
        done_m = (re.search(r"\*\*完成\*\*：\s*(\d{1,2}:\d{2})", tail)
                  or re.search(r"\*\*完成：\s*\S+\s+(\d{1,2}:\d{2})", tail)
                  or re.search(r"(\d{1,2}:\d{2})", tail))
        day_tag = "今天" if offset == 0 else "昨天"
        who = (tool_m.group(1).strip()[:24] if tool_m else "端未标")
        when = done_m.group(1) if done_m else "?"
        return f"上次收工（{day_tag} {when}·{who}）：{title[:40]}"
    return None


def pending_counts():
    """机械待办计数：反哺积压 + 错误候选待确认。脚本取值，AI/人都不手填。"""
    lines = []
    try:
        r = subprocess.run(
            ["python3", str(Path.home() / "[记忆共享中心]/技能配置/growth-box/scripts/drain-backlog.py"), "--check"],  # 源版字面 "~/..." 不经 shell 展开=FileNotFoundError 静默，已修
            capture_output=True, text=True, timeout=30,
        )
        m = re.search(r'"backlog": (\d+)', r.stdout)
        if m and int(m.group(1)) > 0:
            lines.append(f"成长箱反哺积压 {m.group(1)} 条（≥10 触发批量整合）")
    except Exception:
        pass
    try:
        f = GROWTH_DIR / "错误候选待确认.md"
        if f.exists():
            n = sum(1 for l in f.read_text(encoding="utf-8", errors="replace").splitlines() if "⏳待确认" in l)
            if n > 0:
                lines.append(f"错误候选待确认 {n} 条（晨间规划/成长箱呈报）")
    except Exception:
        pass
    return lines


def build_injection() -> str:
    parts = []
    entry = last_log_entry()
    if entry:
        parts.append(f"- {entry}")
    parts.extend(f"- {l}" for l in pending_counts())
    if not parts:
        return ""
    body = "\n".join(parts[:MAX_INJECT_LINES])
    return f"【🔔 尾巴续接·上轮工作脉络与欠账（系统自动注入·皮叔可无视）】\n{body}"


def main() -> None:
    session_id = read_stdin_session_id()
    if not session_id:
        sys.exit(0)
    state_file = STATE_DIR / f"{session_id}.json"
    if state_file.exists():
        sys.exit(0)  # 已注入过，防重入
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        out = build_injection()
        state_file.write_text(json.dumps({"status": "injected", "has_content": bool(out)}, ensure_ascii=False))
        if out:
            print(out)
    except Exception:
        pass  # 钩子永不阻塞
    sys.exit(0)


if __name__ == "__main__":
    main()
