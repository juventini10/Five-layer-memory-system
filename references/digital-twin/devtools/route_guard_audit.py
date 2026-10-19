#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
route_guard_audit.py v0.2 — 护栏防线3：敏感操作审计（Stop 钩子·留痕不拦截）

v0.2（2026-10-15·跨端交接单第④项根治·WB 端实测本端复现）：`read_transcript_rich()` 对
  WB 扁平 `{"type":"function_call"}` 行（locate 取不到 role）补 role="assistant"——
  此前工具调用被 extract 出来又被 role 门整族丢弃 ⇒ 对他端假绿；回归位入 `self_test()`
  三构型＋反向断言（纯文本不误报）。⛔未动共享层 `_ROLE_TYPES`（改它＝改所有消费方语义）。

依据：护栏路由POC设计.md v0.1 §三 + 敏感操作清单v0
功能：每次主代理结束响应时（Stop 钩子），解析 transcript，检测本轮对话中的
      敏感操作证据（删除类/核心写/外发类）→ 追加 guard_events.jsonl（confirmed 待人工对账）。

检测规则（映射敏感操作清单 v0）：
  R1 删除类：rm -rf / rm -r / 批量 rm / trash 清空 / find -delete
  R2 核心写：写/覆盖 铁律|摘要|详解|CORE.md|SHADOW.md（配合防线1：直接写会失败，
             此规则捕获"已 unlock 后违规写"）
  R3 外发类：邮件/公开渠道/外链提交 且 内容涉~/个人AI档案

设计原则（对齐 route_audit.py 范式）：
  - 解析异常/无 transcript → exit 0（失败放行，绝不破坏对话）
  - 保守判定：宁漏勿误（误记=审计噪音）
  - 跨工具中立：公共脚本，各工具 settings.json hooks 仅做接入

用法：
  echo '{"transcript_path": "..."}' | python3 route_guard_audit.py   # Stop 钩子模式
  python3 route_guard_audit.py --stats                                # 统计
  python3 route_guard_audit.py --self-test                            # 自测
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import sys
import os
import re
import json
# 跨端解析·单一真源（2026-09-23 童灵根治·2026-10-14 R1' 融合回灌根层——原只在路由家族副本里）
# 路径取 脚本中心 真源而非 开发工具 转发链（阶段5 废转发链后本行仍成立）
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
import transcript_reader as _tr
try:
    import fcntl  # Unix-only（Windows 无此模块）——缺失时降级为"无文件锁"，仍可运行（2026-09-15 出包容错）
except ImportError:  # pragma: no cover
    fcntl = None
from datetime import datetime


def _lock_ex(f):
    """加排他锁（Unix）；Windows 无 fcntl → 静默降级为无锁（append-mode 单进程写足够）"""
    if fcntl is None:
        return
    try:
        fcntl.flock(f, fcntl.LOCK_EX)
    except OSError:
        pass


def _lock_un(f):
    """解锁（Unix）；Windows 无 fcntl → 静默降级"""
    if fcntl is None:
        return
    try:
        fcntl.flock(f, fcntl.LOCK_UN)
    except OSError:
        pass

GUARD_DIR = os.path.expanduser("[记忆共享中心]/脚本中心/.guard")
EVENT_LOG = os.environ.get("GUARD_EVENT_LOG", os.path.join(GUARD_DIR, "guard_events.jsonl"))

# 检测规则：{规则名: 正则}（大小写不敏感）——真相所有权：规则唯一住所=route_guard_config.json rules
# （语义源=敏感操作清单v0.md §一损失分级；⛔不在此内联——清单更新脚本自动感知）
# 设计：只检测"实际动作"（工具调用字段），不检测文本讨论/引用——护栏管"发生了什么"不是"讨论了什么"
# 字段约定：提取时已带工具名 {"tool": name, "input": {...}}；命令类工具用 command/cmd 字段，写文件类用 path 字段
RULES = {}

def load_rules():
    """从 route_guard_config.json 加载规则；失败=留痕+空规则（Hook 纪律：失败放行，但降级必须留痕）"""
    cfg = os.path.expanduser("[记忆共享中心]/脚本中心/route_guard_config.json")
    try:
        with open(cfg, encoding="utf-8") as f:
            data = json.load(f)
        rules = {k: re.compile(v, re.I) for k, v in data.get("rules", {}).items()}
        if not rules:
            raise ValueError("rules 为空")
        return rules
    except Exception as e:
        _alert_config_missing(cfg, e)
        return {}

def _alert_config_missing(cfg, err):
    """配置缺失/损坏：写入 alert 事件留痕（降级留痕原则），不静默"""
    try:
        import datetime as _dt
        os.makedirs(os.path.dirname(EVENT_LOG), exist_ok=True)
        with open(EVENT_LOG, "a", encoding="utf-8") as f:
            _lock_ex(f)
            f.write(json.dumps({
                "ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "guard_config_missing",
                "rule": "-",
                "file": cfg,
                "evidence": str(err)[:100],
                "confirmed": None,
                "src": "config-load",
            }, ensure_ascii=False) + "\n")
            _lock_un(f)
    except Exception:
        pass
    sys.stderr.write(f"⚠️ 护栏规则配置加载失败（{cfg}），本次不检测: {err}\n")


def read_transcript_rich(path):
    """读 JSONL transcript → [(role, text)]，text=助手文本+工具调用 input 序列化"""
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
            # 工具调用提取走跨端统一层（2026-09-23 童灵根治·R1' 融合回灌）：
            # 端A 独立行式 function_call（WB）/ 端B content 元素式 tool_use（QCN）
            # ⛔ 本函数不在此内联重写解析分支——内联版只认 tool_use，令 WB 形态的工具调用
            #    整族不进审计域（= 护栏防线3 对他端假绿），2026-10-14 diff 实证根层曾因此退化。
            role, _ = _tr.locate(d)
            parts = [json.dumps({"tool": t["tool"], "input": t["input"]}, ensure_ascii=False)
                     for t in _tr.extract_tool_calls(d)]
            # 🔴 2026-10-15 交接单第④项根治（WB 端实测·本端独立复现确认）：
            #   WB 扁平行 `{"type":"function_call",...}` 在 locate() 里取不到 role（"function_call"
            #   不在 _ROLE_TYPES），返回 ""；而 audit() 只收 role=="assistant" ⇒ 工具调用被提取出来
            #   却在下一步整族丢弃＝假绿钩子（护栏防线3 对他端失明）。
            #   修法落在本函数而非 _ROLE_TYPES：工具调用本身即"助手侧实际动作"，与端形态无关；
            #   ⛔只给"有工具调用且无 role"的行补位——纯文本行（含用户消息/文档里写 rm -rf 的说明）
            #   不受影响，反向断言 D 仍须为 0 检出。
            if parts and not role:
                role = "assistant"
            msgs.append((role, " ".join(parts)))
    return msgs


def append_log(entry):
    os.makedirs(os.path.dirname(EVENT_LOG), exist_ok=True)
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        _lock_ex(f)
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        _lock_un(f)

# 规则加载（置于 append_log 之后：_alert_config_missing 依赖 EVENT_LOG 写入）
RULES.update(load_rules())


def audit(transcript_path, src="stop-audit"):
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    msgs = read_transcript_rich(transcript_path)
    if not msgs:
        return 0
    # 只审计助手侧文本（助手回复+工具调用）——用户消息里的"帮我删个文件"是需求不是操作
    assistant_text = " ".join(t for role, t in msgs if role == "assistant")
    if not assistant_text:
        return 0
    hits = 0
    for rule, pattern in RULES.items():
        m = pattern.search(assistant_text)
        if m:
            entry = {
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "guard_hit",
                "rule": rule,
                "file": "",
                "evidence": assistant_text[max(0, m.start() - 20):m.end() + 20][:100],
                "confirmed": None,  # 待人工对账：true=真实敏感操作 / false=误报
                "src": src,
            }
            append_log(entry)
            hits += 1
    return 0


def audit_openclaw(path):
    """AutoClaw chat-history 格式（JSON 数组，元素含 blocks[text/tool]）→ 同一 RULES 检测"""
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return 0
    if not isinstance(data, list):
        return 0
    assistant_text = []
    for e in data:
        if e.get("role") != "assistant":
            continue
        for b in e.get("blocks", []):
            t = b.get("type")
            if t == "tool":
                tc = b.get("toolCall", {})
                assistant_text.append(json.dumps({"tool": tc.get("name"), "input": tc.get("input", {})}, ensure_ascii=False))
    text = " ".join(assistant_text)
    if not text:
        return 0
    hits = 0
    for rule, pattern in RULES.items():
        m = pattern.search(text)
        if m:
            append_log({
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "guard_hit",
                "rule": rule,
                "file": os.path.basename(path),
                "evidence": text[max(0, m.start() - 20):m.end() + 20][:100],
                "confirmed": None,
                "src": "openclaw-scan",
            })
            hits += 1
    return hits


def scan_openclaw_dir(d):
    """扫描目录下 24h 内修改的 chat-history 文件"""
    import time
    cutoff = time.time() - 86400
    total = 0
    for fn in sorted(os.listdir(d)):
        fp = os.path.join(d, fn)
        if not fn.endswith(".json") or not os.path.isfile(fp):
            continue
        if os.path.getmtime(fp) < cutoff:
            continue
        h = audit_openclaw(fp)
        if h:
            print(f"{fn}: {h} 条命中")
            total += h
    print(f"扫描完成：24h 内会话 {total} 条敏感事件")
    return 0  # exit 0（命中数仅打印，不作文本退出码）


def stats():
    if not os.path.isfile(EVENT_LOG):
        print("护栏事件日志为空"); return 0
    rows = []
    with open(EVENT_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    guard = [r for r in rows if r.get("action") == "guard_hit"]
    by_rule = {}
    for r in guard:
        by_rule[r.get("rule")] = by_rule.get(r.get("rule"), 0) + 1
    print(f"护栏事件共 {len(rows)} 条（guard_hit {len(guard)} 条）")
    for r, n in sorted(by_rule.items(), key=lambda x: -x[1]):
        print(f"  {r}: {n}")
    unconfirmed = [r for r in guard if r.get("confirmed") is None]
    if unconfirmed:
        print(f"待人工对账 {len(unconfirmed)} 条（confirmed 置 true/false）")
    return 0


def self_test():
    import tempfile
    global EVENT_LOG
    EVENT_LOG = tempfile.mktemp(suffix=".jsonl")
    cases = [
        # (名称, 工具调用 input JSON, 期望命中规则) —— 文本讨论不再检测（护栏管实际动作）
        ("删除类", '{"command": "rm -rf /tmp/old_dir"}', "R1_delete"),
        ("核心写", '{"path": "[记忆共享中心]/记忆规则/用户基本规则-铁律版.md", "content": "..."}', "R2_core_write"),
        ("外发类", '{"command": "send_mail --content ~/个人AI档案摘要"}', "R3_external"),
        ("文本引用不误报", '{"text": "文档里写了 rm -rf 示例"}', None),
        ("无敏感", '{"command": "ls -la"}', None),
    ]
    ok = True
    for name, text, expect in cases:
        hit = None
        for rule, pattern in RULES.items():
            if pattern.search(text):
                hit = rule
                break
        if (hit == expect) or (expect is None and hit is None):
            print(f"用例 {name}: ✅")
        else:
            print(f"用例 {name}: ❌ (期望 {expect}, 实际 {hit})")
            ok = False
    # 整链：audit 写日志（三构型对照·2026-10-15 交接单第④项根治永久回归位）
    # 病根：WB 端扁平行 {"type":"function_call",...} 在 locate() 取不到 role，旧 audit() 只收
    #       role=="assistant" ⇒ 工具调用整族被丢＝假绿钩子（WB 实测·本端独立复现 2026-10-15）。
    #       回归位必须含"另两端形态真能检出"，⛔只测本端嵌套形态＝测了个不会坏的。
    chain_cases = [
        ("整链 QCN嵌套tool_use",
         [{"role": "user", "message": {"content": [{"type": "text", "text": "清理一下"}]}},
          {"role": "assistant", "message": {"content": [
              {"type": "tool_use", "name": "exec", "input": {"command": "rm -rf /tmp/x"}}]}}], 1),
        ("整链 WB扁平function_call须检出",
         [{"type": "function_call", "name": "Bash",
           "arguments": json.dumps({"command": "rm -rf /tmp/wb_flat"})}], 1),
        ("整链 WB扁平核心写须检出",
         [{"type": "function_call", "name": "Write",
           "arguments": json.dumps({"path": os.path.expanduser(
               "[记忆共享中心]/记忆规则/用户基本规则-铁律版.md"), "content": "x"})}], 1),
        ("整链 WB扁平纯文本不误报（反向断言）",
         [{"type": "message", "role": "assistant",
           "content": "文档里写了 rm -rf 示例，仅说明用途"}], 0),
    ]
    for name, records, want in chain_cases:
        EVENT_LOG = tempfile.mktemp(suffix=".jsonl")
        t = tempfile.mktemp(suffix=".jsonl")
        with open(t, "w", encoding="utf-8") as f:
            for d in records:
                f.write(json.dumps(d, ensure_ascii=False) + "\n")
        audit(t)
        n = sum(1 for _ in open(EVENT_LOG, encoding="utf-8") if _.strip()) if os.path.exists(EVENT_LOG) else 0
        if n == want:
            print(f"{name}: ✅ ({n} 条)")
        else:
            # 2026-10-14 R1' 融合留的诊断位：账本 0 条常因"规则配置缺失→不检测"，⛔掩盖成真红
            hint = "（0 条常因 route_guard_config.json 缺失→整条不检测·属 fail-open 非脚本崩）" if n == 0 else ""
            print(f"{name}: ❌ (期望 {want}·实际 {n}{hint})"); ok = False
    # 坏输入
    import subprocess
    p = subprocess.run([sys.executable, __file__], input="not json", capture_output=True, text=True)
    if p.returncode == 0:
        print("坏输入 exit 0: ✅")
    else:
        print("坏输入 exit 0: ❌"); ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        sys.exit(stats())
    if len(sys.argv) > 1 and sys.argv[1] == "--scan-openclaw-dir":
        sys.exit(scan_openclaw_dir(sys.argv[2]))
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    # --src：分源标注（多端接入同一账本·2026-08-13 与 route_audit --src 同构）
    src = "stop-audit"
    if len(sys.argv) > 2 and sys.argv[1] == "--src":
        src = sys.argv[2]
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    try:
        sys.exit(audit(payload.get("transcript_path"), src))
    except Exception:
        sys.exit(0)
