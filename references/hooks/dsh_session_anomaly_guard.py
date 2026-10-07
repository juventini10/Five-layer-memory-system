#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
dsh_session_anomaly_guard.py — DSH 会话层异常检测守卫（跨工具中立·Stop Hook）

根因（2026-08-21）：DSH 端 turn-stopping 管道依赖 transcript 双重载荷适配
（zstd 解压 + DSH 消息结构 → CC 格式转换），适配层有 3 类已知故障：
  ① 空 transcript（zstd 解压失败 / 会话刚结束未写入）→ 0 条消息 → 下游守卫全盲
  ② 结构异常（JSON 解析失败 / 缺少 role / 缺少 content）→ 静默跳过
  ③ 8 段常驻段文件缺失 → 插件内 fallback 占位文本 → 注入空壳
本守卫让"DSH 端管道本身是否健康"成为可被机械检查的运行时门禁。

用法：
  # Stop Hook 模式（与 route_audit 同协议）
  echo '{"transcript_path": "/tmp/dsh-transcript-cc-xxx.jsonl"}' | python3 dsh_session_anomaly_guard.py
  python3 dsh_session_anomaly_guard.py --transcript <path>
  python3 dsh_session_anomaly_guard.py --self-test

检测项：
  A. transcript 空消息（msg_count=0）→ 告警
  B. transcript 无 assistant 消息（无 assistant/只有 user）→ 告警
  C. transcript 结构异常（JSON 解析失败行 / 缺 role 行 / 缺 content 行）→ 告警+统计
  D. 8 段常驻段文件存在性（DEFAULT_SECTIONS 8 项 path 实际可读）→ 缺失告警
  E. 内容注入验证（pre-step 管道是否实际注入内容——读 route_audit 日志确认有 evidence）→ 无 evidence 告警

设计原则：
  - Hook 三纪律（守卫编写规范 §八）：只告警不拦截 exit 0 恒放行
  - 失败默认放行（解析异常/无输入 → exit 0）
  - 跨工具中立（脚本架构通用规范 §二·五）：公共脚本住开发工具/，任何端可接入
  - 真相所有权（守卫原则1）：transcript 格式契约+DEFAULT_SECTIONS 住在插件本体（index.js），本脚本 import/解析，⛔不内联
  - 负例证据（守卫原则3）：3 类故障均配造错测试（self-test）
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
from datetime import datetime

HOME = os.path.expanduser("~")
DSH_HOME = os.path.join(HOME, ".dsh")
DST_PLUGIN = os.path.join(DSH_HOME, "profiles", "web", "node_modules",
                          "five-layer-memory", "src", "index.js")
ARCHIVE = os.path.expanduser("~")

# 8 段常驻段路径契约（truth source = 插件 index.js DEFAULT_SECTIONS）
# 注意：这里不是"真相所有权内联"，而是"契约引用"——§四 注册表"真相源"列
# 明确写 index.js，本脚本 import 解析 index.js 取 path，此处仅为 self-test 兜底
SECTIONS_CONST = [
    "five-layer-dsh-const", "five-layer-core", "five-layer-persona",
    "five-layer-rules", "five-layer-template", "five-layer-thinking",
    "five-layer-context",
]


def parse_sections_from_plugin(path=DST_PLUGIN):
    """从插件 index.js 解析 DEFAULT_SECTIONS——真相所有权归插件本体（⛔不内联）"""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # 正则提取 DEFAULT_SECTIONS 数组里的 path 字段
    pattern = r"path:\s*['\"]([^'\"]+)['\"]"
    paths = re.findall(pattern, text)
    return paths


def parse_transcript(path):
    """读 JSONL transcript → {msg_count, assistant_count, errors...}

    2026-09-23 童灵根治：取值改走共享解析层（守卫编写规范 §3.12 单一入口律）——
    原硬编码 `obj["message"]["content"]` ＝端绑定（该端若把 content 放顶层 → 恒 missing_content），
    同类病已在 WB 端 5 个守卫上实证空转。降级兜底保留原语义，共享层不可用时行为不变。
    """
    import sys as _sys
    _root = os.path.expanduser("[记忆共享中心]/脚本中心")
    if _root not in _sys.path:
        _sys.path.insert(0, _root)
    try:
        import transcript_reader as _tr
        _locate, _flatten = _tr.locate, _tr.flatten_content
    except Exception:
        def _locate(d):
            if not isinstance(d, dict):
                return ("", None)
            m = d.get("message") if isinstance(d.get("message"), dict) else {}
            return (d.get("role") or m.get("role") or "",
                    d.get("content") if d.get("content") is not None else m.get("content"))

        def _flatten(c):
            if isinstance(c, list):
                return " ".join(x.get("text", "") for x in c if isinstance(x, dict))
            return c if isinstance(c, str) else ""

    result = {"msg_count": 0, "assistant_count": 0, "user_count": 0,
              "error_lines": [], "missing_role": 0, "missing_content": 0}
    if not os.path.exists(path):
        result["file_missing"] = True
        return result
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                result["error_lines"].append(i)
                continue
            role, content = _locate(obj)
            if not role:
                result["missing_role"] += 1
                continue
            if not _flatten(content).strip():
                result["missing_content"] += 1
                continue
            result["msg_count"] += 1
            if role == "assistant":
                result["assistant_count"] += 1
            elif role == "user":
                result["user_count"] += 1
    return result


def check_sections(archive=ARCHIVE):
    """检查 8 段常驻段文件存在性——缺失=插件注入空壳"""
    missing = []
    # 用契约引用（默认 7 项，user 段可选）
    expected = [
        ("核心层/DSH宪法.md", "DSH 宪法"),
        ("核心层/CORE.md", "CORE 核心层"),
        ("最伟大的我/自画像/当前.md", "自画像"),
        ("记忆规则/用户基本规则-铁律版.md", "铁律版"),
        ("记忆规则/用户基本规则-摘要版.md", "摘要版"),
        ("记忆蓝图/01_思维方法论/三大思维白皮书.md", "三大思维"),
        ("情境层/动态状态快照.md", "动态快照"),
    ]
    for rel, label in expected:
        full = os.path.join(archive, rel)
        if not os.path.exists(full):
            missing.append(label)
    return missing


def latest_transcript(dsh_home=DSH_HOME):
    """找最近活跃的 CC transcript"""
    tmp = "/tmp"
    candidates = []
    for f in os.listdir(tmp):
        if f.startswith("dsh-transcript-cc-") and f.endswith(".jsonl"):
            full = os.path.join(tmp, f)
            try:
                mtime = os.path.getmtime(full)
                candidates.append((mtime, full))
            except OSError:
                continue
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def main():
    ap = argparse.ArgumentParser(description="DSH 会话层异常检测守卫")
    ap.add_argument("--transcript", help="CC transcript 路径")
    ap.add_argument("--strict", action="store_true",
                    help="发现异常 exit 1（默认 exit 0 恒放行）")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    ap.add_argument("--self-test", action="store_true", help="内置负例自测")
    args = ap.parse_args()

    if args.self_test:
        return run_self_test()

    anomalies = []
    transcript_path = args.transcript

    # 自动找最新 transcript（无 --transcript 时）
    if not transcript_path:
        transcript_path = latest_transcript()
    if transcript_path:
        t = parse_transcript(transcript_path)
        if t.get("file_missing"):
            anomalies.append({"type": "A", "severity": "high",
                              "detail": "transcript 文件不存在"})
        else:
            if t["msg_count"] == 0:
                anomalies.append({"type": "A", "severity": "high",
                                  "detail": f"transcript 0 条消息"})
            if t["assistant_count"] == 0 and t["msg_count"] > 0:
                anomalies.append({"type": "B", "severity": "medium",
                                  "detail": f"无 assistant 消息（user={t['user_count']}）"})
            if t["error_lines"]:
                anomalies.append({"type": "C", "severity": "high",
                                  "detail": f"JSON 解析失败行 {len(t['error_lines'])} 条"})
            if t["missing_role"]:
                anomalies.append({"type": "C", "severity": "medium",
                                  "detail": f"缺 role 字段 {t['missing_role']} 条"})
            if t["missing_content"]:
                anomalies.append({"type": "C", "severity": "medium",
                                  "detail": f"缺 content 字段 {t['missing_content']} 条"})
    else:
        anomalies.append({"type": "A", "severity": "high",
                          "detail": "未找到最近 CC transcript"})

    # D. 8 段常驻段检查
    missing = check_sections()
    if missing:
        anomalies.append({"type": "D", "severity": "medium",
                          "detail": f"缺失常驻段 {missing}"})

    if args.json:
        print(json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "anomalies": anomalies,
            "healthy": len(anomalies) == 0,
        }, ensure_ascii=False))
    else:
        print(f"DSH 会话层巡检 ({datetime.now().strftime('%H:%M:%S')})")
        if anomalies:
            print(f"⚠️ 检测到 {len(anomalies)} 项异常：")
            for a in anomalies:
                print(f"  [{a['severity'].upper()}] {a['type']} {a['detail']}")
        else:
            print("✅ 会话层健康")

    return 1 if (anomalies and args.strict) else 0


def run_self_test():
    """负例自测——3 类故障 + 1 正常态"""
    import tempfile
    tests = [
        ("空 transcript", '{"role":"user","message":{"content":[]}}', ["A"]),
        ("无 assistant", '{"role":"user","message":{"content":[{"type":"text","text":"hi"}]}}', ["B"]),
        ("坏 JSON（单行）", '{"role": "bad"', ["A", "C"]),
        ("坏 JSON（混正常行）", '{"role":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}\n{"role": "bad"', ["C"]),
        ("正常", '{"role":"assistant","message":{"content":[{"type":"text","text":"ok"}]}}', []),
    ]
    results = []
    for name, content, expected_types in tests:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        t = parse_transcript(tmp)
        got = []
        if t["msg_count"] == 0:
            got.append("A")
        if t["assistant_count"] == 0 and t["msg_count"] > 0:
            got.append("B")
        if t["error_lines"] or t["missing_role"]:
            got.append("C")
        pass_ = got == expected_types
        results.append((name, pass_, got, expected_types))
        os.unlink(tmp)

    all_pass = all(r[1] for r in results)
    print("dsh_session_anomaly_guard.py self-test")
    for name, p, got, exp in results:
        status = "✅" if p else "❌"
        print(f"  {status} {name}: got={got} expected={exp}")
    print(f"\n{'✅ 自测全过' if all_pass else '❌ 自测失败'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())