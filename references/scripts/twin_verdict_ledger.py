#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/twin_verdict_ledger.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# version: v0.1
"""twin_verdict_ledger.py —— 运行期裁决台账（Stop 钩子·童灵代行裁决的观测端）

设计定位：L3 深度模式结论的 P0 地基——让"分身作出裁决"这件事**首次可观测**。
  背景（2026-08-29 L3 实证）：运行期代行裁决留痕为**零条**；既有 step2.x 判据是
  **盲判评测样本**非运行流水（step3 台账自证"不计推翻率分母"），不可充作分母。

🔴 核心设计：防静默失效（F4 病根·2026-08-24 立 H4 五天零条）
  双路径检测，把"没记=没发生"翻转为"没记=一条待补记录"：
  - 主路径（structured）：回复含 `<!--TWIN_VERDICT {...}-->` → 解析入库
  - 兜底路径（pending_structure）：正则扫裁决性语句 → 落一条待补结构化记录
  → 漏写标记不再静默丢失，而是变成一条可见的待补项。

🔴 三层分离（G1-Q1 结论：推翻率是混合统计量，一个数字同时驱动三层 = Deming tampering）
  每条裁决必须标 layer，禁止用一个混合数同时驱动：
  - L1_single    ：这次做对了吗 → 触发单次纠错（不该调权）
  - L2_rule      ：判断规则对吗 → 触发改规则
  - L3_authority ：该不该有这个权 → 触发调权（扩/收）

🔴 信号源：verbalized confidence 不可用（外部证据 AUROC 仅 62.7% +
  Reasoning Contamination Effect 正中童灵"先推理再裁决"结构）→ 改用
  sampling-consistency（同题多采样一致性，AUROC 54.8%→92.7%）。
  本脚本存 samples[] 并自动算 consistency；consistency=null 时标"未测"，
  ⛔ 不得用 confidence_verbalized 单独充当置信度信号。

契约：--check(JSON,含 alarm) / --report(markdown) / --add(json) / --selfcheck
台账：[记忆共享中心]/数字分身/steps/twin-verdict-ledger.jsonl（单行 JSON·O_APPEND 原子）
心跳：/tmp/twin_verdict_ledger.heartbeat（证明"挂了且在跑"·S014 升级条款）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
import re
import hashlib
from datetime import datetime

LEDGER = os.path.expanduser("[记忆共享中心]/数字分身/steps/twin-verdict-ledger.jsonl")
HEARTBEAT = "/tmp/twin_verdict_ledger.heartbeat"
HOST = os.environ.get("CARD_GUARD_HOST") or os.environ.get("TWIN_HOST") or "workbuddy"

# ── 主路径：结构化裁决标记 ──
VERDICT_TAG = re.compile(r"<!--\s*TWIN_VERDICT\s*(\{.*?\})\s*-->", re.S)

# ── 兜底路径：裁决性语句（防漏标静默丢失·命中即落 pending_structure）──
VERBAL_PATTERNS = [
    # ── 强信号：显式裁决措辞（命中即落 pending_structure）──
    r"分身裁决[：: ]",
    r"童灵裁决[：: ]",
    r"童灵(?:批|不批|准|不准|否决|驳回)[：: ]",
    r"\*\*裁决\*\*[：: ]",
    r"我(?:批准|否决|驳回)[：: ]",
    # ── 中信号：判断性陈述（须带裁决动词，防普通对话误报）──
    r"(?:我|分身|童灵)(?:的)?(?:判断|结论|决定|主张|裁决)(?:是|为)[：: ]",
    r"(?:建议|决定|裁定)(?:采纳|通过|不通过|否决)[：: ]",
    r"我的最优(?:解|方案)(?:是|为)[：: ]",
]

LAYERS = ("L1_single", "L2_rule", "L3_authority")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def beat_heartbeat():
    """心跳：证明本守卫真的在跑（S014 升级：挂了≠在跑，须有心跳证据）"""
    try:
        with open(HEARTBEAT, "w", encoding="utf-8") as f:
            json.dump({"ts": now_iso(), "host": HOST, "script": "twin_verdict_ledger.py"}, f)
    except OSError:
        pass


def get_text_from_stdin():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        if not raw.strip():
            return ""
        try:
            d = json.loads(raw)
            for k in ("text", "prompt", "content", "message"):
                v = d.get(k)
                if isinstance(v, str) and v.strip():
                    return v
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            return item["text"]
            return json.dumps(d, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return raw
    except Exception:
        return ""


def calc_consistency(samples):
    """sampling-consistency：多次采样的一致率。

    samples: [1,1,0] 形式——每次采样是否得出与首次相同的结论。
    返回 0.0~1.0；空/非法返回 None（标"未测"，⛔不默认为 1.0）。
    """
    if not isinstance(samples, list) or not samples:
        return None
    clean = [int(s) for s in samples if isinstance(s, (int, float, bool))]
    if not clean:
        return None
    return round(sum(1 for s in clean if s) / len(clean), 3)


def make_id(claim, ts):
    h = hashlib.sha1(f"{ts}{claim}".encode("utf-8")).hexdigest()[:6]
    return f"WV-{ts.replace('-', '').replace(':', '')[:15]}-{h}"


def append_ledger(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def normalize(rec, status, snippet=""):
    ts = rec.get("ts") or now_iso()
    claim = (rec.get("claim") or snippet or "")[:200]
    samples = rec.get("samples")
    return {
        "ts": ts,
        "host": rec.get("host") or HOST,
        "verdict_id": rec.get("verdict_id") or make_id(claim, ts),
        "claim": claim,
        "layer": rec.get("layer") if rec.get("layer") in LAYERS else "L1_single",
        "confidence_verbalized": rec.get("confidence_verbalized"),
        "samples": samples,
        "consistency": calc_consistency(samples),
        "basis": rec.get("basis") or [],
        "status": status,
        "evidence_snippet": snippet[:160],
    }


def _try_json(raw):
    """解析结构化标记——Stop 钩子传入的文本常被 JSON 编码，引号被转义。

    三级降级：原样 → 反转义引号 → unicode_escape 全解。
    （2026-08-29 实测：主路径标记因 \\" 转义而落到兜底路径，结构化率 0%）
    """
    for candidate in (raw,
                      raw.replace('\\"', '"').replace("\\'", "'"),
                      raw.replace('\\\\', '\\').replace('\\"', '"')):
        try:
            d = json.loads(candidate)
            if isinstance(d, dict):
                return d
        except (json.JSONDecodeError, TypeError):
            continue
    try:
        d = json.loads(raw.encode().decode("unicode_escape"))
        if isinstance(d, dict):
            return d
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        pass
    return None


def scan(text):
    """返回 (structured_recs, pending_recs)

    去重：同一轮内重叠的字符区间只留第一条（2026-08-29 实测：
    一段话被 3 条正则各抓一次，台账灌水）。
    """
    structured, pending = [], []
    if not text:
        return structured, pending

    taken = []  # 已占用的字符区间，防重复捕获

    def overlapped(a, b):
        return any(not (b <= s or a >= e) for s, e in taken)

    for m in VERDICT_TAG.finditer(text):
        taken.append((m.start(), m.end()))
        rec = _try_json(m.group(1))
        if rec is None:
            pending.append(normalize({}, "pending_structure", m.group(1)[:160]))
            continue
        structured.append(normalize(rec, "structured", str(rec.get("claim", ""))[:160]))

    for pat in VERBAL_PATTERNS:
        for m in re.finditer(pat, text):
            if overlapped(m.start(), m.end()):
                continue
            taken.append((m.start(), m.end()))
            # 只取锚点后的一句话（到句号/换行/分号为止），不抓整段
            tail = text[m.end():m.end() + 160]
            stop = min([i for i in (tail.find("。"), tail.find("\n"), tail.find("；"))
                        if i >= 0] or [len(tail)])
            snip = (m.group(0) + tail[:stop + 1]).strip().replace("\n", " ")
            pending.append(normalize({}, "pending_structure", snip))
    return structured, pending


def read_ledger():
    if not os.path.exists(LEDGER):
        return []
    rows = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def mode_check(text):
    beat_heartbeat()
    structured, pending = scan(text)
    for rec in structured:
        append_ledger(rec)
    if pending:
        # 同一轮内的多项疑似裁决**聚合为一条**：不静默丢失（F4 病根），也不灌水
        agg = pending[0]
        if len(pending) > 1:
            agg["claim"] = (f"[聚合] 本轮 {len(pending)} 处疑似裁决未结构化"
                            f"｜首条：{pending[0]['claim'][:70]}")
            agg["pending_count"] = len(pending)
        append_ledger(agg)
    alarm = bool(pending)
    print(json.dumps({
        "alarm": alarm,
        "structured": len(structured),
        "pending_structure": len(pending),
        "ledger_appended": 1 if pending else 0,
        "ledger": LEDGER,
        "note": "pending_structure≠错误，是'疑似裁决未结构化'待补项——防静默丢失",
    }, ensure_ascii=False))
    return 0


def mode_report(_text=None):
    rows = read_ledger()
    structured = [r for r in rows if r.get("status") == "structured"]
    pending = [r for r in rows if r.get("status") == "pending_structure"]
    unmeasured = [r for r in structured if r.get("consistency") is None]

    print("## 📒 童灵运行期裁决台账")
    print()
    print(f"- 结构化裁决：**{len(structured)}** 条")
    print(f"- 待补结构化：**{len(pending)}** 条（疑似裁决未打标记）")
    print(f"- 未测一致性：**{len(unmeasured)}** 条（⛔ 不得用 verbalized 单独当信号）")
    print(f"- 台账： `{LEDGER}`")
    print()

    if not rows:
        print("> ⚠️ 台账为空——无法区分「零裁决」与「零测量」（冷启动死锁）。")
        print("> 若分身已在代行裁决，说明**观测端未生效**，先查 hook 挂载与心跳。")
        return

    if pending:
        print("### 🟡 待补结构化（疑似裁决·须补标记或确认非裁决）")
        print("| 时间 | 摘要 |")
        print("|---|---|")
        for r in pending[-8:]:
            print(f"| {r['ts']} | {r['claim'][:70]} |")
        print()

    by_layer = {}
    for r in structured:
        by_layer.setdefault(r["layer"], []).append(r)
    print("### 三层分布（⛔ 不得合并成一个推翻率）")
    print("| 层 | 含义 | 条数 | 已测一致性 |")
    print("|---|---|---:|---:|")
    for layer, desc in (("L1_single", "这次做对了吗→单次纠错"),
                        ("L2_rule", "判断规则对吗→改规则"),
                        ("L3_authority", "该不该有这个权→调权")):
        rs = by_layer.get(layer, [])
        measured = sum(1 for r in rs if r.get("consistency") is not None)
        print(f"| {layer} | {desc} | {len(rs)} | {measured} |")
    print()

    if structured:
        print("### 最近裁决（按 consistency 升序=最不确定者在前）")
        print("| 时间 | 层 | 一致性 | 裁决摘要 |")
        print("|---|---|---:|---|")
        ordered = sorted(structured, key=lambda r: (r.get("consistency") is None,
                                                    r.get("consistency") or 0))
        for r in ordered[-10:]:
            c = r.get("consistency")
            c = "未测" if c is None else str(c)
            print(f"| {r['ts']} | {r['layer']} | {c} | {r['claim'][:60]} |")


def mode_add(payload):
    """外部写入结构化裁决（供分身/主agent 在裁决时调用）"""
    beat_heartbeat()
    try:
        rec = json.loads(payload)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"JSON 解析失败: {e}"}, ensure_ascii=False))
        return 2
    if not rec.get("claim"):
        print(json.dumps({"ok": False, "error": "缺 claim 字段"},
                         ensure_ascii=False))
        return 2
    append_ledger(normalize(rec, "structured", rec.get("claim", "")))
    print(json.dumps({"ok": True, "consistency": calc_consistency(rec.get("samples")),
                      "ledger": LEDGER}, ensure_ascii=False))
    return 0


def mode_selfcheck():
    ok = True
    d = os.path.dirname(LEDGER)
    print(f"台账目录: {d} {'✅' if os.path.isdir(d) else '❌ 不存在'}")
    ok &= os.path.isdir(d)
    print(f"心跳文件: {HEARTBEAT} {'✅' if os.path.exists(HEARTBEAT) else '⚠️ 未生成（尚未运行）'}")
    rows = read_ledger()
    print(f"台账条数: {len(rows)}")
    print("用法: twin_verdict_ledger.py [--check|--report|--add <json>|--selfcheck]")
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if "--selfcheck" in args:
        sys.exit(mode_selfcheck())
    if "--report" in args:
        mode_report()
        return
    if "--add" in args:
        i = args.index("--add")
        payload = args[i + 1] if i + 1 < len(args) else sys.stdin.buffer.read().decode('utf-8', errors='replace')
        sys.exit(mode_add(payload))
    text = get_text_from_stdin() if "--check" in args or not args else ""
    sys.exit(mode_check(text))


if __name__ == "__main__":
    main()
