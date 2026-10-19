#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""transcript_reader.py — 跨端 transcript 读取·单一真源（2026-09-23 童灵根治）

【病根】"读 JSONL transcript 提 assistant 正文"这件事被 N 个守卫脚本各自实现一遍，
        每份都硬编码**单一端**的字段结构 → 换端即全局失明，且 fail-open 无任何告警。
        实证（2026-09-23）：WB 端 5 个已挂 Stop 守卫解析真实会话 0/304 条成功——
        知识库审计/反馈检测/路由审计/路由守卫审计/TSL 收尾全部静默空转，无人知晓。

【根治】解析逻辑收敛到此一处，端格式差异在本层吸收：
        各脚本只调 iter_messages / assistant_texts / last_assistant_text，
        ⛔不再自行取值 d["message"]["content"] 之类的硬编码路径。

【已覆盖端格式】
  A 顶层式（WorkBuddy）: {type:"message", role:"assistant", content:[{type:"output_text",text}]}
  B 嵌套式（Qoder CN） : {type:"assistant", message:{role:"assistant", content:[{type:"text",text}]}}
  C 裸 content 变体    : {role:"assistant", content:"..."} / {role:.., content:[{text}]}
  （新端接入：若结构不属以上，在本模块补一支并同步 --self-test 夹具，⛔勿在调用方打补丁）

【纪律】fail-open：任何异常返回空、不抛——守卫不得因解析失败阻断对话。

用法：
  from transcript_reader import iter_messages, assistant_texts, last_assistant_text
  python3 transcript_reader.py --self-test    # 多端夹具 + 变异测试
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
try:
    import fcntl          # Unix/macOS：读端加锁防读到半截写入
except ImportError:
    # Windows 无 fcntl——本件属对外发布包（各端 Stop 钩子都 import 它），
    # 必须能在 Win 导入并运行。降级守设计律②「降级不阻塞」：锁变 no-op，
    # 读到半截行的风险由本件既有的「解析失败即跳过该条」容错兜（不崩≠不脏，如实声明）。
    # ⚠️ 同型守卫共三处（build_kb_vectors / audit_search_kb / transcript_reader）。
    class _NoFcntl:
        LOCK_EX = LOCK_UN = LOCK_NB = 0

        @staticmethod
        def flock(fh, op):
            return None
    fcntl = _NoFcntl()
import json
import os
import sys
from datetime import datetime

# 端格式开关：仅用于 --self-test 的变异测试（模拟旧版"只认嵌套"行为，验证夹具具检出力）。
_ONLY_NESTED = False

_ROLE_TYPES = ("assistant", "user", "system")

# ── 输入层探针（2026-09-23 童灵根治 · fail-open + fail-loud 双轨）──────────────
# 病根：守卫 fail-open（拿不到输入就静默 exit 0）保证了对话安全，代价是**失效无声**。
#       WB 端 5 个守卫空转 0/304，而六层体检全绿——因为没有任何一处记录「我没拿到输入」。
# 正解：⛔不改成 fail-closed（会阻断对话），而是**行为继续 fail-open，事实留痕**。
#       本模块是所有读 transcript 守卫的必经之路 → 此处埋点，一处实现、全族可观测。
DEFAULT_EVENT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "logs", "runtime", "transcript_parse_events.jsonl")  # 自推导·两环境同构（作者侧=开发工具/logs·用户侧=脚本中心/logs·2026-09-30 by ZCode）
EVENT_LOG = os.environ.get("TRANSCRIPT_EVENT_LOG", DEFAULT_EVENT_LOG)


def _log_event(kind, path, detail=""):
    """记录一次输入层异常（不阻断·不抛）。kind ∈ transcript_path_missing /
    transcript_missing / assistant_text_empty；caller 取 argv[0]（=调用方守卫）。"""
    try:
        caller = os.path.basename(sys.argv[0] or "") or "unknown"
        os.makedirs(os.path.dirname(EVENT_LOG), exist_ok=True)
        with open(EVENT_LOG, "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps({
                "ts": datetime.now().isoformat(timespec="seconds"),
                "kind": kind, "caller": caller, "path": str(path), "detail": detail,
            }, ensure_ascii=False) + "\n")
            fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        pass  # 探针自身永不阻断（守卫三纪律）


def flatten_content(content):
    """content 任意形态 → 纯文本。列表元素只取 text 字段（thinking/tool_use 天然无 text）。"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text") or content.get("content") or "")
    if isinstance(content, (list, tuple)):
        parts = []
        for x in content:
            if isinstance(x, dict):
                t = x.get("text")
                if isinstance(t, str) and t:
                    parts.append(t)
            elif isinstance(x, str):
                parts.append(x)
        return " ".join(parts)
    return ""


def locate(d):
    """从一行 transcript 记录定位 (role, content) ——【端差异唯一收口点】。

    各守卫脚本请一律用本函数取值：
        role, content = transcript_reader.locate(d)
    ⛔ 勿再自写 d["message"]["content"] / d["content"] 之类的硬编码路径——
       那是"每换一个端就失明一次"的病根（2026-09-23 WB 端 5 守卫实证）。
    """
    if not isinstance(d, dict):
        return ("", None)
    m = d.get("message")
    if _ONLY_NESTED:                                  # 变异测试用：模拟旧版只认嵌套
        return ((m.get("role") or "") if isinstance(m, dict) else "",
                m.get("content") if isinstance(m, dict) else None)
    role = d.get("role")
    if not role and isinstance(m, dict):
        role = m.get("role")
    if not role:
        t = d.get("type")
        if t in _ROLE_TYPES:                          # 排除 WB 的 type="message" 等非角色类型
            role = t
    content = d.get("content")                        # 顶层式（WorkBuddy）
    if content is None and isinstance(m, dict):
        content = m.get("content")                    # 嵌套式（Qoder CN）
    if content is None:
        content = d.get("text")                       # 裸文本变体
    return (role or "", content)


def tool_calls(path):
    """全文件工具调用 → [{"tool": name, "input": dict}]（端中立）。"""
    out = []
    if not path or not os.path.isfile(path):
        return out
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("{"):
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                out.extend(extract_tool_calls(d))
    except Exception:
        return out
    return out


def extract_tool_calls(d):
    """从一条记录提取工具调用（端中立）——工具调用的「端差异收口点」。

    端 A 独立行式（WorkBuddy）: {type:"function_call", name:"Skill", arguments:"{...}"}
    端 B 元素式（Qoder CN）  : message.content[].{type:"tool_use", name:..., input:{...}}
    """
    out = []
    if not isinstance(d, dict):
        return out
    if d.get("type") == "function_call":
        name = d.get("name")
        if name:
            args = d.get("arguments")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {"raw": args}
            out.append({"tool": str(name),
                        "input": args if isinstance(args, dict) else {"raw": args}})
    _, content = locate(d)
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name"):
                inp = c.get("input")
                out.append({"tool": str(c["name"]),
                            "input": inp if isinstance(inp, dict) else {"raw": inp}})
    return out


def iter_messages_with_ts(path):
    """JSONL → [(role, text, ts_str)]；ts 取条目自带时间字段，取不到给空串。

    2026-10-10 新增（PAT-087 根治·Qoder CN 童灵）：`iter_messages` 只给 (role, text)，
    使任何"按回合时刻对账"的判据无锚点可用——declare 对账腿因此只能拿
    「台账最后一行」当「本回合」，跨回合交叠时真红与假红同形。
    ⛔不改 iter_messages 行为（它被多端共用·改返回形状＝牵连既有读面）。
    """
    out = []
    if not path or not os.path.isfile(path):
        return out
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                role, content = locate(d)
                ts = ""
                for k in ("timestamp", "ts", "created_at", "time"):
                    v = d.get(k)
                    if isinstance(v, str) and v.strip():
                        ts = v.strip()
                        break
                out.append((role, flatten_content(content), ts))
    except Exception:
        return []
    return out


def iter_messages(path):
    """JSONL → [(role, text)]。行损坏/空行跳过；不抛异常。

    输入层探针（2026-09-23 童灵根治）：路径缺失 / 文件不存在 / 解析出 0 条
    assistant 正文 → 各留一条事件，使「空转」由静默变为可观测。
    """
    out = []
    if not path:
        _log_event("transcript_path_missing", "")
        return out
    if not os.path.isfile(path):
        _log_event("transcript_missing", path)
        return out
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if not isinstance(d, dict):
                    continue
                role, content = locate(d)
                out.append((role, flatten_content(content)))
    except Exception:
        return out
    if not any(r == "assistant" and t.strip() for r, t in out):
        _log_event("assistant_text_empty", path, "parsed_lines=%d" % len(out))
    return out


def assistant_texts(path):
    """只取 assistant 行的正文（非空）。"""
    try:
        return [t for r, t in iter_messages(path) if r == "assistant" and t.strip()]
    except Exception:
        return []


def last_assistant_text(path):
    """最后一条 assistant 正文；无则空串。"""
    ts = assistant_texts(path)
    return ts[-1] if ts else ""


# ──────────────────────────── 自测 ────────────────────────────
def _fixtures(d):
    """多端夹具：A(WB 顶层) / B(QCN 嵌套) / C(裸 content) / 反例。"""
    import tempfile

    def w(name, rows):
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return p

    wb = w("wb.jsonl", [
        {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "U1"}]},
        {"type": "message", "role": "assistant", "content": [
            {"providerData": {}, "type": "output_text", "text": "A1 提到 #S922"},
            {"type": "thinking", "thinking": "内部想到 S888"}]},
        {"type": "function_call", "name": "Skill", "callId": "c1",
         "arguments": "{\"skill\": \"miora\"}"},
        {"type": "function_call_result", "name": "Skill", "callId": "c1",
         "output": {"type": "text", "text": "FC 不该算"}},
        {"type": "reasoning", "content": [{"type": "text", "text": "R 不该算"}]},
        {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "A2 收尾"}]},
    ])
    qcn = w("qcn.jsonl", [
        {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "U2"}]}},
        {"type": "assistant", "message": {"role": "assistant",
                                          "content": [{"type": "text", "text": "B1 提到 #S815"}]}},
        {"type": "progress", "data": {"note": "S999 不该算"}},
    ])
    bare = w("bare.jsonl", [{"role": "assistant", "content": "C1 裸文本"}])
    # ⚠️ 损坏行必须**绕过 json.dumps** 手写——首版用 dumps 序列化"断行{"，
    #    结果写出来是合法 JSON，夹具测不到「损坏行跳过」分支（自测当场抓出）。
    broken = os.path.join(d, "broken.jsonl")
    with open(broken, "w", encoding="utf-8") as f:
        f.write(json.dumps({"role": "assistant", "content": "D1 好行"}, ensure_ascii=False) + "\n")
        f.write('{"role": "assistant", "content": "断行{\n')
    return wb, qcn, bare, broken


def self_test():
    import tempfile
    d = tempfile.mkdtemp()
    # 探针隔离：自测不得污染真实事件账本
    os.environ["TRANSCRIPT_EVENT_LOG"] = os.path.join(d, "events.jsonl")
    globals()["EVENT_LOG"] = os.environ["TRANSCRIPT_EVENT_LOG"]
    wb, qcn, bare, broken = _fixtures(d)
    try:
        a_wb = assistant_texts(wb)
        assert len(a_wb) == 2, "WB 顶层式应取到 2 条 assistant 正文，实得 %d" % len(a_wb)
        assert "#S922" in a_wb[0] and "A2" in a_wb[1]
        assert all("#S888" not in t for t in a_wb), "thinking 不得计入"
        assert all("不该算" not in t for t in a_wb), "function_call/reasoning 不得计入"

        a_q = assistant_texts(qcn)
        assert len(a_q) == 1 and "#S815" in a_q[0], "QCN 嵌套式应取到 1 条"
        assert all("S999" not in t for t in a_q), "progress 行不得计入"

        assert last_assistant_text(bare) == "C1 裸文本", "裸 content 变体应可读"
        assert len(assistant_texts(broken)) == 1, "损坏行应跳过、好行保留"
        assert assistant_texts("/nonexistent/x.jsonl") == [], "不存在路径应返回空不抛"
        assert iter_messages(wb)[0][0] == "user", "role 提取应为 user"

        # 工具调用（跨端统一表达）
        tc_wb = tool_calls(wb)
        assert len(tc_wb) == 1 and tc_wb[0]["tool"] == "Skill", "WB 独立行式 function_call 应被提取"
        assert tc_wb[0]["input"].get("skill") == "miora", "arguments 字符串应解析为 dict"
        assert tool_calls(qcn) == [], "QCN 夹具无 tool_use 元素，应为空"

        # 输入层探针：缺失路径必须留痕（把「静默空转」变可观测）
        assert assistant_texts("/nonexistent/x.jsonl") == []
        ev = open(EVENT_LOG, encoding="utf-8").read()
        assert "transcript_missing" in ev, "输入层探针应记录 transcript_missing"
        # 文件在但一条 assistant 行都没有 → 必须记 assistant_text_empty（本次病根的可观测出口）
        only_user = os.path.join(d, "only_user.jsonl")
        with open(only_user, "w", encoding="utf-8") as f:
            f.write(json.dumps({"role": "user", "content": "只有用户"}, ensure_ascii=False) + "\n")
        assert assistant_texts(only_user) == []
        assert "assistant_text_empty" in open(EVENT_LOG, encoding="utf-8").read(), \
            "无 assistant 行 → 应记空转事件"

        # ── 变异测试：证明夹具能抓出「端格式回归」（守卫编写规范 §3.9）──
        global _ONLY_NESTED
        _ONLY_NESTED = True
        try:
            assert assistant_texts(wb) == [], "变异后 WB 夹具应变空（旧版行为）"
            assert len(assistant_texts(qcn)) == 1, "变异后 QCN 仍应可读"
        finally:
            _ONLY_NESTED = False
        print("[PASS] transcript_reader self-test：多端夹具 8 项 + 变异测试 OK")
        # §3.9 承接标记（guard_selftest_check classify_mut 消费）：能走到本行＝上面变异断言已全过
        #   （变异段任一 assert 失败会先抛 AssertionError 走 [FAIL] 分支，标记不落＝Fail-Closed）
        print("  MUT:OK 端格式回归探针在岗（_ONLY_NESTED 置真 → WB 夹具必变空·QCN 仍可讀）")
        return 0
    except AssertionError as e:
        print("[FAIL] %s" % e)
        return 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    print(__doc__)
