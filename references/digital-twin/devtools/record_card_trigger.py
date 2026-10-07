#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
record_card_trigger.py — Stop 钩子：立场卡"触发事件"自动登记（2026-09-22 童灵落地）

v0.2（2026-09-22 童灵 D3 根治）：适配产品 Stop 真实 transcript=`session.execution.jsonl`（顶层 type、role 在 message）——v0.1 误按 conversation-history 顶层 role 判 assistant，真实格式下恒不命中=静默空转假绿（自检拿错格式样例掩盖）。现 read 兼容双格式 + fixture 用真实格式 + 补 thinking/progress 负例。

职责：每轮对话结束(Stop)时，扫 transcript 的 assistant 正文里提及的立场卡号(S0XX)，
     按 (卡号,日期,session) 幂等追加到 触发台账.md。
判据边界（锚 知识库设计哲学 原则15 / S1056 / S815）：
     本脚本记的是"AI 回应中提及了这张卡"= 可观测触发事件，⛔不判"采纳"——
     "卡是否真改变了判断"是因果不可观测项(黑盒无 prompt_logprobs)，不得由本脚本冒充。
     采纳判定仍走"人工从触发台账挑依据型→引用台账"。
自反馈污染防护（复用 audit_search_kb.strip_inject 精神）：
     注入块的 Top-3 卡号不得计入触发（否则"注入过"被虚报成"用了"）→ 先 strip_inject 再扫。
设计纪律（Hook 三纪律）：只记录不拦截(exit0) / 失败默认放行(全 try) / 保守判定(仅 assistant 正文+strip 注入)。
跨工具中立：公共脚本住 开发工具/知识联邦引擎/scripts/，各端 Stop 钩子接入即生效。

用法：
  echo '{"transcript_path":"..."}' | python3 record_card_trigger.py
  python3 record_card_trigger.py --self-test
"""
import sys, os, re, json
# 🆕 2026-10-03 跨平台根治：fcntl 是 Unix-only，Windows 无此模块 ⇒ 原
#   `import ..., fcntl` 在 Windows 上 **ImportError 直接崩**（platform_compat
#   「Unix-only导入无守卫」P1 项实锤）。按包内既有范式改可降级导入：
#   Unix 走 fcntl.flock；Windows 走 msvcrt.locking；两者皆无 ⇒ 不加锁。
#   ⛔ 无锁不报错（守卫 fail-open 纪律·本脚本是「只记录不拦截」的观测件，
#   锁缺失不影响判据正确性，只留台账并发写的极小风险）。
try:
    import fcntl as _fcntl
except ImportError:              # Windows
    _fcntl = None
    try:
        import msvcrt as _msvcrt
    except ImportError:          # 两无（理论极端）
        _msvcrt = None
else:
    _msvcrt = None
from collections import Counter
from datetime import datetime
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
import transcript_reader as _tr  # 跨端解析·单一真源（2026-09-23 童灵根治）

LEDGER = os.environ.get("TRIGGER_LEDGER",
    os.path.expanduser("[记忆共享中心]/知识库/AI学习库/触发台账.md"))
CARD_RE = re.compile(r"(?:立场卡#|#)?(S\d{3,4})")
INJECT_MARK = "【知识库激活·确定性注入】"

# 端识别（2026-09-23 童灵·跨端累计诉求）：按 transcript 路径片段判端——
# 端专属路径是唯一可靠来源（session 名格式会漂）。台账因此看得见"哪端贡献"。
HOST_FRAGMENTS = [
    ("workbuddy", "/.workbuddy/"),
    ("qoder-cn", "/.qoder-cn/"),
    ("qoder-desktop", "/.qoder/"),
    ("zcode", "/.zcode/"),
    ("autoclaw", "/.openclaw-autoclaw/"),
    ("lobsterai", "/LobsterAI/"),
    ("dsh", "/five-layer-memory/"),
    ("hermes", "/.hermes/"),
]
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


def detect_host(transcript_path):
    p = str(transcript_path or "")
    for host, frag in HOST_FRAGMENTS:
        if frag in p:
            return host
    return "unknown"


def strip_inject(text):
    """剥离知识注入块（含标记的整段到下一个【标记/结尾）——自反馈污染防护"""
    if INJECT_MARK not in text:
        return text
    parts = text.split(INJECT_MARK)
    out = [parts[0]]
    for p in parts[1:]:
        cut = p.find("【")
        out.append(p if cut == -1 else p[cut:])
    return "".join(out)


def read_assistant_text(path):
    """读 transcript → 拼接全部 assistant 正文（行损坏跳过）。

    2026-09-23 童灵根治：原实现把 content 路径写死 `d["message"]["content"]`，
    而 WorkBuddy 端 transcript 为**顶层** role/content → WB 端解析 0 条、
    fail-open 静默空转（实测 3 个真实会话均 0 段）。端差异已收口到
    `transcript_reader.locate()`，本函数退化为一行调用。
    """
    return "\n".join(_tr.assistant_texts(path))


def load_keys():
    """读台账已有 (卡号,日期,session) 键集，用于幂等"""
    keys = set()
    if not os.path.exists(LEDGER):
        return keys
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and "#S" in line:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 3 and cells[0].startswith("#S"):
                    keys.add((cells[0], cells[1], cells[2]))
    return keys


def run(transcript_path, session_hint=""):
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    body = strip_inject(read_assistant_text(transcript_path))
    if not body:
        return 0
    date = datetime.now().strftime("%Y-%m-%d")
    session = session_hint or os.path.splitext(os.path.basename(transcript_path))[0][:16]
    cnt = Counter("#" + c for c in CARD_RE.findall(body))
    if not cnt:
        return 0
    keys = load_keys()
    new = [(card, n) for card, n in cnt.items() if (card, date, session) not in keys]
    if not new:
        return 0
    host = detect_host(transcript_path)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        if _fcntl is not None:
            _fcntl.flock(f, _fcntl.LOCK_EX)
        elif _msvcrt is not None:                 # Windows 等价锁
            try:
                _msvcrt.locking(f.fileno(), _msvcrt.LK_LOCK, 1)
            except OSError:
                pass                              # ⛔ 锁失败不阻断（fail-open）
        for card, n in new:
            f.write("| {} | {} | {} | {} | 输出提及 | {} |\n".format(
                card, date, session, n, host))
        f.flush()
        if _fcntl is not None:
            _fcntl.flock(f, _fcntl.LOCK_UN)
        elif _msvcrt is not None:
            try:
                _msvcrt.locking(f.fileno(), _msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
    return 0


def self_test():
    import tempfile
    d = tempfile.mkdtemp()
    tp = os.path.join(d, "sess_selftest.jsonl")
    with open(tp, "w", encoding="utf-8") as f:
        # 真实 session.execution.jsonl 格式：role 在 message、type 在顶层
        f.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "这也印证了 S922 的正向应用和 #S815 的边界。"}]}}) + "\n")
        # thinking 元素（无 text）不算对外输出 → S888 不得计入
        f.write(json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "内部想到 S888"}]}}) + "\n")
        # progress 行非 assistant → 跳过
        f.write(json.dumps({"type": "progress", "data": {"note": "S999"}}) + "\n")
        # user 注入块含 S777 → strip_inject 后不得计入
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": "【知识库激活·确定性注入】命中 立场卡#S777 \n实际正文"}]}}) + "\n")
    globals()["LEDGER"] = os.path.join(d, "t.md")
    run(tp, "selftest")
    run(tp, "selftest")  # 第二次应幂等·不重复追加
    txt = open(LEDGER, encoding="utf-8").read()
    assert "#S922" in txt and "#S815" in txt, "应记录正文提及的卡"
    assert "#S777" not in txt, "注入块卡号不得计入触发(strip_inject)"
    assert "#S888" not in txt, "thinking 内部思考不得计入对外提及"
    assert "#S999" not in txt, "progress/非assistant 行不得计入"
    assert txt.count("#S922") == 1, "重跑须幂等不重复"
    # 端识别 + 端列（2026-09-23 跨端累计诉求）
    assert detect_host("/x/.workbuddy/projects/a.jsonl") == "workbuddy"
    assert detect_host("/x/.qoder-cn/sess.jsonl") == "qoder-cn"
    assert detect_host("/tmp/none.jsonl") == "unknown"
    assert txt.count("输出提及") == 2, "两张卡应各写一行"
    assert "| unknown |" in txt, "端列应落盘（tempfile 路径非端专属）"
    # ── §3.9 变异自检（守卫编写规范·出厂第一个跑的是变异测试）──────────────────────
    #   可置假对象=strip_inject（自反馈污染防护的唯一执行位）。置哑后注入块里的 #S777
    #   必然混进台账 ⇒ 说明上面那条「注入块卡号不得计入」断言真的有检出力，不是恒真。
    #   ⚠️ 承接标记 MUT:OK 由本结果派生（2026-10-01 补·此前本件长期 🔴「新守卫缺变异自检」：
    #   断言写得齐、变异没跑过 ⇒ 聚合器看不见"变异跑过"的痕迹，该红按设计正确）。
    #   ⚠️ 探针对象选址（2026-10-01 实测后改判·原方案被自己的变异测试否掉）：
    #     第一版置哑的是 strip_inject，结果 S777 并没有混入 ⇒ 说明"注入块卡号不入账"这条断言
    #     实际由 **role 过滤**（read_assistant_text）承重，strip_inject 在该形态下不承重＝探针没牙。
    #     另立实测（不在本件内改判据）：strip_inject 对"标记后无下一个【"的单块形态**不剥离**
    #     （cut==-1 分支保留整段）⇒ 其有效性依赖注入块的排列顺序，已立案观察，⛔不顺手改匹配
    #     （铁律-020：改匹配须先 dry-run 量化命中面，跨端顺序样本未测齐）。
    #     现置哑对象＝本件自己的文本读取位 `read_assistant_text`（本件符号·⛔不动跨端原语
    #     transcript_reader.assistant_texts），让它把非 assistant 行也读进来。
    _real_rat = globals()["read_assistant_text"]
    def _blind(path):
        out = []
        for line in open(path, encoding="utf-8"):
            try:
                out.append(json.dumps(json.loads(line), ensure_ascii=False))
            except Exception:
                continue
        return "\n".join(out)
    globals()["read_assistant_text"] = _blind
    globals()["LEDGER"] = os.path.join(d, "t_mut.md")
    try:
        run(tp, "selftest-mut")
        _mtxt = open(LEDGER, encoding="utf-8").read()
    finally:
        globals()["read_assistant_text"] = _real_rat
        globals()["LEDGER"] = os.path.join(d, "t.md")
    _caught = "#S777" in _mtxt or "#S888" in _mtxt or "#S999" in _mtxt
    print("  %s MUT:%s 文本读取位置哑 → 注入/thinking/progress 卡号混入（混入=%s/%s/%s）"
          % ("✅" if _caught else "❌", "OK" if _caught else "FAIL",
             "#S777" in _mtxt, "#S888" in _mtxt, "#S999" in _mtxt))
    print("[PASS] self-test OK\n" + txt)
    return 0 if _caught else 1


def doctor():
    """端覆盖度自检（2026-09-23 童灵根治·防「挂着却空转」复发）。

    ① 各端运行时配置是否挂了本钩子 ② 台账里各端贡献行数
    ③ 已挂但零贡献 → 显形提示（advisory·不阻断）
    动机：本机制的第一次失效（WB 端解析 0/304）**没有任何告警**——fail-open 是
    对话安全的正确设计，但必须补一个"显形"出口，否则同类失效永远靠人偶然发现。
    """
    try:
        from guard_doc_consistency import HOST_CONFIGS   # 跨端宿主 SSOT·不造第二套
    except Exception:
        HOST_CONFIGS = {
            "workbuddy": os.path.expanduser("~/.workbuddy/settings.json"),
            "qoder-cn": os.path.expanduser("~/.qoder-cn/settings.json"),
        }
    print("== 立场卡触发台账 · 端覆盖度自检 ==")
    mounted, absent, missing_file = [], [], []
    for host, path in sorted(HOST_CONFIGS.items()):
        try:
            txt = open(path, encoding="utf-8").read()
        except Exception:
            missing_file.append(host)      # 本机未装该端 → 非缺陷，如实分类
            continue
        (mounted if "record_card_trigger" in txt else absent).append(host)
    print("  已挂本钩子:", ", ".join(mounted) or "(无)")
    print("  已装未挂:", ", ".join(absent) or "(无)")
    print("  本机无此端:", ", ".join(missing_file) or "(无)")

    dist = Counter()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and "#S" in line:
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    dist[cells[5] if len(cells) > 5 else "未标注端(QCN旧行)"] += 1
    # 旧行（本列引入前的历史行）无端列 → 按 session 命名推断（task-* 为 Qoder CN 会话名）
    legacy = dist.pop("未标注端(QCN旧行)", 0)
    if legacy:
        dist["qoder-cn(旧行推断)"] = legacy
    print("  台账端分布:", dict(dist) or "(空)")

    silent = [h for h in mounted if not any(k.startswith(h) for k in dist)]
    if silent:
        print("  ⚠️ 已挂但台账零贡献:", ", ".join(silent),
              "→ 长期为零须查 Stop payload 是否含 transcript_path（防静默空转）")
    else:
        print("  ✅ 已挂各端均有台账贡献")
    return 0


if __name__ == "__main__":
    try:
        if "--self-test" in sys.argv:
            sys.exit(self_test())
        if "--doctor" in sys.argv:
            sys.exit(doctor())
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            payload = {}
        tp = payload.get("transcript_path") or payload.get("transcriptPath") or ""
        sid = str(payload.get("session_id") or "")
        sys.exit(run(tp, sid[:16]))
    except Exception as e:
        sys.stderr.write("record_card_trigger fail-open: %s\n" % e)
        sys.exit(0)
