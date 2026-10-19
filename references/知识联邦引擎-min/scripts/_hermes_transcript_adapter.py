#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermes 会话 transcript 适配器（接入层·不改动审计脚本本体）。

布洛陀知识库审计脚本(audit_search_kb.py / feedback_detect.py)契约：
从 stdin 读 {"transcript_path": "..."} → 读该 jsonl（每行
{"role","message":{"content":[{"type":"text","text":c}]}}）→ 审计。

Hermes 的 on_session_end 只给 session_id，transcript 存在 state.db 的
messages 表（content 为纯文本），无文件路径。本适配器在插件侧（接入层）
完成 db→jsonl 转换，把路径喂给既有脚本——符合"接入=调用，不=改写脚本"
的跨工具中立纪律。

用法：
    python3 _hermes_transcript_adapter.py <session_id> [audit|feedback|format|l3guard]
      audit   → 导出 transcript 后调 audit_search_kb.py（stdin 传路径）
      feedback→ 导出 transcript 后调 feedback_detect.py（stdin 传路径）
      format  → v1.1 调 reply_format_guard.py（SOUL 容器校验·rc2=格式缺失）
      l3guard → v1.1 调 l3_conclusion_guard.py（需 guard v1.3+·三明智签名缺块检测）
"""
import os
import sys
import json
import sqlite3
import tempfile
import subprocess

HOME = os.path.expanduser("~")
STATE_DB = os.path.join(HOME, ".hermes", "state.db")
# ENGINE 定位（2026-10-13·童灵·根治硬编码旧位）：
# audit_search_kb.py / feedback_detect.py / transcript_reader.py 随
# references/scripts 全量投递到脚本中心（= rp("script_center") / rp("devtools")），
# ⛔ 不再硬编码 开发工具/知识联邦引擎（旧位·10-12 迁顶层后仅残留苟活）。
# 候选链（实位优先）：script_center → devtools → 旧位兜底（作者机残留）。
# 装包侧 path_overlay 会改写这些常量到用户机实况。
def _resolve_engine():
    """定位 audit/feedback/transcript_reader 所在目录（候选链·实位优先）。"""
    _cands = []
    _sc = os.environ.get("BULUOTUO_SCRIPT_CENTER")
    _dt = os.environ.get("BULUOTUO_DEVTOOLS")
    if _sc:
        _cands.append(_sc)
    if _dt:
        _cands.append(_dt)
    _cands.append(os.path.join(HOME, "个人AI档案", "脚本中心"))
    _cands.append(os.path.join(HOME, "个人AI档案", "开发工具", "知识联邦引擎", "scripts"))
    for _c in _cands:
        if _c and os.path.isfile(os.path.join(_c, "audit_search_kb.py")):
            return _c
    return _cands[-1]  # 全不中回落旧位（fail-open·下游 isfile 兜底）


ENGINE = _resolve_engine()
AUDIT_SCRIPT = os.path.join(ENGINE, "audit_search_kb.py")
FEEDBACK_SCRIPT = os.path.join(ENGINE, "feedback_detect.py")
FORMAT_SCRIPT = os.path.expanduser(
    os.path.expanduser("[记忆共享中心]/开发工具/Skill路由引擎/scripts/reply_format_guard.py")
)
L3_GUARD_SCRIPT = os.path.expanduser(
    os.path.expanduser("[记忆共享中心]/开发工具/l3_conclusion_guard_tests/l3_conclusion_guard.py")
)
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"[记忆共享中心]/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def export_transcript(session_id: str) -> str | None:
    """从 state.db 按 session_id 导出 transcript 为临时 jsonl，返回路径。"""
    if not os.path.isfile(STATE_DB):
        return None
    try:
        con = sqlite3.connect(STATE_DB)
        cur = con.execute(
            "SELECT role, content, tool_calls, tool_name FROM messages "
            "WHERE session_id=? ORDER BY id ASC",
            (session_id,),
        )
        rows = cur.fetchall()
        con.close()
    except Exception as exc:
        sys.stderr.write(f"db 读取失败: {exc!r}\n")
        return None
    if not rows:
        return None
    fd, path = tempfile.mkstemp(suffix=".jsonl", prefix="hermes_tx_")
    # 修复①（2026-10-13·童灵·30D 基线缺口根治）：把临时文件放到 .hermes/ 下
    # 让 _host_of() 能从路径识别端名——旧方案用 /tmp/hermes_tx_ 路径不含任何
    # 端名信号 ⇒ host=? 永远填不上 ⇒ predicted/actual 双账不可对账。
    # 修复②（同轮）：把 tool_calls 字段转成端A独立行式 {type:"function_call",
    # name, arguments} ——旧方案只导 content 字段，_real_run 看不到 tool_call
    # 结构 ⇒ real_run=unknown 永远。transcript_reader.extract_tool_calls 收口
    # 端差异：端A=独立行式·端B=content[].tool_use 元素式；Hermes db 存的是
    # tool_calls JSON 字符串 + tool_name，转成端A独立行式即可被识别。
    hermes_dir = os.path.join(HOME, ".hermes", "transcript_exports")
    os.makedirs(hermes_dir, exist_ok=True)
    fd, path = tempfile.mkstemp(suffix=".jsonl", prefix="hermes_tx_", dir=hermes_dir)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for role, content, tool_calls, tool_name in rows:
            if content is None:
                content = ""
            # 主行：role + content（嵌套式·transcript_reader.locate 兼容）
            line_data = {
                "role": role,
                "message": {"content": [{"type": "text", "text": str(content)}]},
            }
            fh.write(json.dumps(line_data, ensure_ascii=False) + "\n")
            # 附行：tool_call 独立行式（端A·transcript_reader.extract_tool_calls 兼容）
            if tool_calls:
                # tool_calls 是 JSON 字符串，解析成数组逐个写成独立 function_call 行
                try:
                    tc_list = json.loads(tool_calls)
                    if isinstance(tc_list, list):
                        for tc in tc_list:
                            if isinstance(tc, dict):
                                fn = tc.get("function") or tc
                                fc_line = {
                                    "type": "function_call",
                                    "name": fn.get("name") or tool_name or "unknown",
                                    "arguments": json.dumps(fn.get("arguments", {}), ensure_ascii=False)
                                        if isinstance(fn.get("arguments"), (dict, list))
                                        else str(fn.get("arguments", "")),
                                }
                                fh.write(json.dumps(fc_line, ensure_ascii=False) + "\n")
                    elif isinstance(tc_list, dict):
                        # 单条 tool_call 形态
                        fn = tc_list.get("function") or tc_list
                        fc_line = {
                            "type": "function_call",
                            "name": fn.get("name") or tool_name or "unknown",
                            "arguments": json.dumps(fn.get("arguments", {}), ensure_ascii=False)
                                if isinstance(fn.get("arguments"), (dict, list))
                                else str(fn.get("arguments", "")),
                        }
                        fh.write(json.dumps(fc_line, ensure_ascii=False) + "\n")
                except (json.JSONDecodeError, TypeError, AttributeError):
                    # tool_calls 非 JSON 字符串：按裸 tool_name 兜底写独立行
                    if tool_name:
                        fc_line = {"type": "function_call", "name": tool_name, "arguments": "{}"}
                        fh.write(json.dumps(fc_line, ensure_ascii=False) + "\n")
            elif tool_name:
                # 无 tool_calls 但有 tool_name：写一条最简 function_call 行
                fc_line = {"type": "function_call", "name": tool_name, "arguments": "{}"}
                fh.write(json.dumps(fc_line, ensure_ascii=False) + "\n")
    return path


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write("用法: _hermes_transcript_adapter.py <session_id> [audit|feedback]\n")
        return 2
    session_id = sys.argv[1]
    mode = sys.argv[2]
    tx_path = export_transcript(session_id)
    if not tx_path:
        sys.stderr.write(f"无 transcript（session {session_id} 无消息或 db 不可读）\n")
        return 0  # 失败放行
    try:
        if mode == "audit":
            script = AUDIT_SCRIPT
        elif mode == "feedback":
            script = FEEDBACK_SCRIPT
        elif mode == "format":
            script = FORMAT_SCRIPT  # v1.1: SOUL 回复格式守卫（Hermes 接入·2026-08-24）
        elif mode == "l3guard":
            script = L3_GUARD_SCRIPT  # v1.1: 三明智结论块守卫（需 guard v1.3+ parse 兼容）
        else:
            sys.stderr.write(f"未知模式: {mode}\n")
            return 2
        if not os.path.isfile(script):
            sys.stderr.write(f"审计脚本不存在: {script}\n")
            return 0
        proc = subprocess.run(
            ["python3", script],
            input=json.dumps({"transcript_path": tx_path}),
            capture_output=True,
            text=True,
            timeout=120,
        )
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        return proc.returncode
    except Exception as exc:
        sys.stderr.write(f"调用失败: {exc!r}\n")
        return 0
    finally:
        try:
            os.unlink(tx_path)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
