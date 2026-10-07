#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""w1_vocab_dryrun.py v1.1 — W1 词表 dry-run ＋ 双向夹具（WP2·铁律-020 ＋ S875 预注册判据）

v1.1（2026-09-18·Qoder CN 端·皮叔令「认可方案去做吧」）：**接入观测采集层真实语料**——
  本脚本成为 `路由家族/logs/prompts.jsonl` 的**首个真实消费者**（FU-34 的判假方式就此有外部锚）。
  为什么是它而不是新写一个分析器：本脚本原语料=对账报告 §8.6 的 19 条手抄样本，
  自家文档自陈「真实 prompt 强度高样本小」——语料腿的缺口正好由采集层补，⛔不造第二个消费者。
  姿势：⛔只取 tier=primary（machine/paraphrase 非你原话，进来即污染上岗率分母）；
  空语料/缺文件 → 显式报 0 行告警（「0 行」在观测层是一等告警信号），⛔不报成"0% 上岗"的绿。
  新增 `--corpus [路径]` 与 `--self-test`（六例双向·含空语料与缺件负例）。

═════════ 预注册验收判据（先于改动写下·改动后必须全过·⛔结果不由 AI 事后追加）═════════
正例 5 条 → 必须判「上岗」
负例 5 条 → 必须判「静默」
26 条真样本（对账报告 §8.6）→ A 类上岗率↑ 且 B 类静默率不降
基线（改动前）与复跑（改动后）两次输出必须都贴进任务书 §五 痕迹表。

语料来源：`路由家族/对账报告_2026-08-22.md` §8.6 实证（A 类 6 / B 类 3 / C 类 1）
         ＋ 报告给出的 8/29 你要的阴性例。⛔不编造样本。
纪律：只读＋只打印，⛔不写任何文件、不改任何配置（纯 dry-run）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import importlib.util
import os
import sys

# ── 被测脚本路径解析（2026-10-03·你「第一性原理根治」·治「验证器测的不是运行的那份」）──
# 病根实证：原式硬编码 `[记忆共享中心]/脚本中心/`，而 `runtime_paths.json` 的 `devtools`
#   指向 `脚本中心/`——两份 sha256 不同 ⇒ 回归器报「全绿」与运行态零关联。
#   同日实测：加病句断言后，旧件判 D3 / 真跑件判 D2，**两次都报全绿**。
# 判据（verifier_target_fidelity_guard.py）：路径必须解析自 runtime_paths。
# 降级：runtime_paths 不可读时用脚本中心/开发工具 双候选探测 + 显形，⛔不静默取旧件。
def _resolve_devtools(name):
    """按 runtime_paths.devtools 解析脚本名；解析不到则逐候选探测并显形告警。"""
    import json as _json
    rp = os.path.expanduser("~/.hermes/doenglingz/runtime_paths.json")
    base = None
    if os.path.isfile(rp):
        try:
            with open(rp, encoding="utf-8") as fh:
                base = _json.load(fh).get("devtools")
        except Exception:
            base = None
    cands = []
    if base:
        cands.append(os.path.join(base, name))
    cands += [
        os.path.expanduser("[记忆共享中心]/脚本中心/" + name),
        os.path.expanduser("[记忆共享中心]/脚本中心/" + name),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    sys.stderr.write("[WARN] %s 解析不到·候选=%s\n" % (name, cands))
    return cands[0]


ENGINE = _resolve_devtools("doenglingz_inject_prompt.py")


# 真实语料源（观测采集层产物·v1.1 接入：本脚本即 prompts.jsonl 的首个真实消费者）
CORPUS = os.path.expanduser("[记忆共享中心]/脚本中心/logs/prompts.jsonl")

spec = importlib.util.spec_from_file_location("dg", ENGINE)
dg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dg)

SEP = dg._ADDRESS_SEP

# ── 候选新词表（WP2·只增复合窄词·铁律-020 禁裸高频词）──
NEW_TRIGGERS = list(dg.W1_TRIGGERS) + [
    "童灵怎么看", "童灵有何", "童灵有什么", "童灵继续", "童灵接着", "童灵你继续",
]
NEW_SELF = list(dg.W1_SELF_WORDS) + [
    "收获", "发现", "思考", "想法", "复盘", "有何", "怎么看",
]

# ── B 类防误召闸（元讨论·复合窄词·先于正例判定）──
# 依据 §8.6 B 类实证三条＋同型词，全部为"与童灵共现才成立"的复合词。
#
# ⚠️⚠️ 定位声明 + 误用警示（2026-09-23 童灵补·皮叔质证轮）：
#   本脚本是**候选判据比对器**（历史用途：2026-09-13 词表扩容前，比"引擎旧逻辑" vs "候选新逻辑"），
#   ⛔**不是引擎回归网**——它下面的 `w1_new()` 与 `META_GUARDS` 是**脚本内副本**，
#   与 `doenglingz_inject_prompt.py` 的**当前实现不同步**（实证：本文件的 META_GUARDS 仅 7 项，
#   而引擎已含 D 轴设计词；2026-09-23 有人据本脚本"19/19"当作引擎回归证据＝**假绿**）。
#   ✅ 引擎回归请**直接 import 引擎本体**调 `dg.w1_fired()` 跑样本（同批 19 例实测：5/5·5/5·6/6·3/3 全过）。
META_GUARDS = ["每次问", "都会出现", "封装成", "是不是最好", "不都可以", "聊了几句", "童灵的特性"]


def w1_new(prompt):
    """候选新判据（含 C 类机器块过滤 + B 类元讨论闸 + 句中直呼）。"""
    t = (prompt or "").strip()
    if not t:
        return False
    # ① C 类·机器块过滤（<internal-error> 之类回显，不该进台账）
    if t.startswith("<") and ">" in t[:24]:
        return False
    # ② B 类·元讨论闸：提及≠调用（先于正例判定）
    if "童灵" in t and any(g in t for g in META_GUARDS):
        return False
    # ③ 句中直呼："童灵"后紧跟分隔符（位置不限·治"那童灵，…"）
    idx = t.find("童灵")
    if idx >= 0:
        tail = t[idx + 2:]
        if (not tail) or tail[0] in SEP:
            return True
    # ④ 原判据 + 新词
    if any(x in t for x in NEW_TRIGGERS):
        return True
    return "童灵" in t and any(v in t for v in dg.W1_VERBS + NEW_SELF)


# ── 夹具（正例应上岗 / 负例应静默）──
POS = [
    "童灵怎么看？",
    "童灵继续推进",
    "那童灵，你有什么收获吗？",
    "童灵有何发现？",
    "那就动手，童灵，你要看着",
]
NEG = [
    "我和童灵儿聊了几句",
    "现在童灵是每次问都会出现吗？",
    "讨论：现在基于童灵的特性，是不是封装成 Skill 是最好的选择？",
    "童灵不都可以帮我做吗？",
    "<internal-error> 回显",
]
# ── 26 条真样本中的可复现子集（§8.6 实证列出者）──
REAL_A = ["童灵怎么看？", "童灵有何收获？", "童灵继续推进", "童灵你继续做",
          "那童灵，你有什么收获吗？", "那就动手，童灵，你要看着"]
REAL_B = ["现在童灵是每次问都会出现吗？",
          "讨论：现在基于童灵的特性，是不是封装成 Skill 是最好的选择？",
          "童灵不都可以帮我做吗？"]


def run(label, items, want):
    ok = bad = 0
    rows = []
    for s in items:
        old, new = dg.w1_fired(s), w1_new(s)
        good_new = (new == want)
        ok += good_new
        bad += (not good_new)
        rows.append("  %s 旧=%-5s 新=%-5s %s | %s"
                    % ("✅" if good_new else "❌", old, new,
                       "(旧错新对)" if (not (old == want) and good_new) else
                       ("(旧对新错·回归!)" if ((old == want) and not good_new) else ""),
                       s[:44]))
    print("\n【%s】%d/%d 过" % (label, ok, ok + bad))
    for r in rows:
        print(r)
    return ok, bad


def load_corpus(path=CORPUS, limit=None):
    """读观测层真实语料：⛔只取 tier=primary（machine/paraphrase 是机器块或转述，不是你的原话）。
    返回 (rows, stats)。文件缺失/空 → rows=[] 并由调用方显形，⛔不静默当"0% 上岗"。"""
    import json
    rows, stats = [], {"total": 0, "primary": 0, "skipped_tier": 0, "bad_line": 0, "missing_prompt": 0}
    if not os.path.exists(path):
        return rows, stats
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            stats["total"] += 1
            try:
                d = json.loads(ln)
            except Exception:
                stats["bad_line"] += 1
                continue
            if d.get("tier") != "primary":
                stats["skipped_tier"] += 1
                continue
            p = (d.get("raw_prompt") or "").strip()
            if not p:
                stats["missing_prompt"] += 1
                continue
            stats["primary"] += 1
            rows.append(p)
            if limit and len(rows) >= limit:
                break
    return rows, stats


def corpus_report(rows, stats, path=CORPUS):
    """在真实语料上跑旧/新两套判据，报分布与差异——⛔不报"好坏"（那是 W1 契约的判定域），只报可观测。"""
    print("\n【真实语料·tier=primary】%s" % path)
    if not rows:
        print("  ⚠️ 0 行可用语料（读 %d 行·primary %d）——"
              "「0 行」在观测层是一等告警信号：可能采集器失明而非真的没人说话；先核采集器配置（语料源路径·权限·更新时间）再下结论"
              % (stats.get("total", 0), stats.get("primary", 0)))
        return {"rows": 0}
    hits = [p for p in rows if "童灵" in p]
    old_on = [p for p in rows if dg.w1_fired(p)]
    new_on = [p for p in rows if w1_new(p)]
    gained = [p for p in new_on if not dg.w1_fired(p)]
    lost = [p for p in old_on if not w1_new(p)]
    print("  语料 %d 条（含「童灵」%d 条）｜旧判据上岗 %d（%.2f%%）→ 新判据上岗 %d（%.2f%%）"
          % (len(rows), len(hits), len(old_on), 100.0 * len(old_on) / len(rows),
             len(new_on), 100.0 * len(new_on) / len(rows)))
    print("  新判据净增 %d 条 / 净减 %d 条（净减>0＝可能误杀，须逐条看，⛔不默认「应是噪声」）" % (len(gained), len(lost)))
    for tag, bucket in (("增", gained), ("减", lost)):
        for p in bucket[:5]:
            print("    [%s] %s" % (tag, p[:70].replace("\n", " ")))
        if len(bucket) > 5:
            print("    [%s] …其余 %d 条" % (tag, len(bucket) - 5))
    print("  语料构成：总读 %d 行｜primary %d｜非 primary 跳过 %d｜坏行 %d｜缺正文 %d"
          % (stats["total"], stats["primary"], stats["skipped_tier"], stats["bad_line"], stats["missing_prompt"]))
    return {"rows": len(rows), "old_on": len(old_on), "new_on": len(new_on),
            "gained": len(gained), "lost": len(lost)}



def self_test():
    """双向夹具：正例证明真在数，负例证明不静默放行（§3.0·5 自测纪律·⛔只测"能否跑"）。"""
    import json
    import tempfile
    tmp = tempfile.mkdtemp(prefix="w1_corpus_")
    good = os.path.join(tmp, "ok.jsonl")
    with open(good, "w", encoding="utf-8") as f:
        f.write(json.dumps({"tier": "primary", "raw_prompt": "童灵怎么看？"}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"tier": "primary", "raw_prompt": "今天写文案"}, ensure_ascii=False) + "\n")
        f.write(json.dumps({"tier": "machine", "raw_prompt": "童灵 机器回显"}, ensure_ascii=False) + "\n")
        f.write("{坏 JSON\n")
        f.write(json.dumps({"tier": "primary", "raw_prompt": ""}, ensure_ascii=False) + "\n")
    empty = os.path.join(tmp, "empty.jsonl")
    open(empty, "w").close()
    cases = []
    try:
        rows, stats = load_corpus(good)
        cases.append(("C1 只收 primary 真语料（2 条·非 4 条）", len(rows) == 2 and stats["primary"] == 2))
        cases.append(("C2 非 primary 被跳过（machine 不进分母）", stats["skipped_tier"] == 1))
        cases.append(("C3 坏行/缺正文各计一次（不静默吞）", stats["bad_line"] == 1 and stats["missing_prompt"] == 1))
        rep = corpus_report(rows, stats, good)
        cases.append(("C4 上岗统计真在数（旧=1·新=1·净增 0）",
                      rep["rows"] == 2 and rep["old_on"] == 1 and rep["new_on"] == 1 and rep["gained"] == 0))
        r2, s2 = load_corpus(empty)
        rep2 = corpus_report(r2, s2, empty)
        cases.append(("C5 空语料 → 显形 0 行告警（⛔不装「0% 上岗」的绿）", rep2 == {"rows": 0} and s2["total"] == 0))
        r3, s3 = load_corpus(os.path.join(tmp, "不存在.jsonl"))
        cases.append(("C6 文件缺失 → 空返回不抛异常（宿主缺件降级）", r3 == [] and s3["total"] == 0))
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    ok = 0
    print("=== w1_vocab_dryrun.py 自测夹具（真实语料消费腿）===")
    for name, good_case in cases:
        ok += bool(good_case)
        print("  %s %s" % ("✅" if good_case else "❌", name))
    print("自测 %d/%d %s" % (ok, len(cases), "全绿" if ok == len(cases) else "有红"))
    return 0 if ok == len(cases) else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    argv = sys.argv[1:]
    if "--corpus" in argv:
        i = argv.index("--corpus")
        path = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else CORPUS
        rows, stats = load_corpus(path)
        print("W1 词表真实语料校准（消费腿：观测采集层 prompts.jsonl）")
        rep = corpus_report(rows, stats, path)
        return 0 if rep.get("rows", 0) else 1
    print("W1 词表 dry-run（WP2）· 预注册判据：正例 5 全上岗 / 负例 5 全静默")
    print("词表规模：旧 TRIGGERS %d → 新 %d ｜ 旧 SELF %d → 新 %d ｜ 元讨论闸 %d 词"
          % (len(dg.W1_TRIGGERS), len(NEW_TRIGGERS),
             len(dg.W1_SELF_WORDS), len(NEW_SELF), len(META_GUARDS)))
    p_ok, _ = run("正例·应上岗", POS, True)
    n_ok, _ = run("负例·应静默", NEG, False)
    a_ok, _ = run("A 类真样本·应上岗", REAL_A, True)
    b_ok, _ = run("B 类真样本·应静默", REAL_B, False)
    total = p_ok + n_ok + a_ok + b_ok
    print("\n" + "═" * 62)
    total_n = len(POS) + len(NEG) + len(REAL_A) + len(REAL_B)
    print("合计 %d/%d 过（正例 %d/%d · 负例 %d/%d · A %d/%d · B %d/%d）"
          % (total, total_n, p_ok, len(POS), n_ok, len(NEG),
             a_ok, len(REAL_A), b_ok, len(REAL_B)))
    print("判定：全过 = 可落地；否则 ⛔不得落地（铁律-020）")
    print("注：分母由 len() 实算——初版硬编码 20 与实数 19 不符（任务书 P1「分母错」同型·当场修正）")


if __name__ == "__main__":
    main()
