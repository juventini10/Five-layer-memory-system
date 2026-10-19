#!/usr/bin/env python3
"""growth-box/scripts/drain-backlog.py — 反哺管道排空脚本

用法：
  python3 drain-backlog.py --check          # 只数数量，输出 ALARM/NORMAL
  python3 drain-backlog.py --report         # 逐条输出排空报告

功能：
  --check: 扫描 规范反哺日志.md 总追踪表，统计 🔴待整合 数量。
           输出 JSON: {backlog:N, alarm:true/false, since_last_drain:days}
           由 growth-box SKILL.md 启动时调用，决定是否触发排空。

  --report: 扫描全部 🔴待整合 条目，逐条提取 {日期/标题/落点/内容摘要}。
            输出 Markdown 表格，供 AI 呈现给用户逐条 y/n。

设计原则：
  SKILL.md 不重复写阈值和逻辑——所有逻辑在脚本里。
  SKILL.md 只写一句：✅DO 启动时调 drain-backlog.py --check，按结果执行。
  依据：指令§6.1 单一来源（阈值/判定规则只存在一处）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import re
import json
import sys
from pathlib import Path
from datetime import date, datetime

FEEDBACK_LOG = Path.home() / "[记忆共享中心]/成长箱/experience/规范反哺日志.md"
ALARM_THRESHOLD = 15


def count_backlog(text: str) -> int:
    """统计总追踪表中 🔴待整合 条目数"""
    in_table = False
    count = 0
    for line in text.split('\n'):
        if line.startswith('## 总追踪表'):
            in_table = True
            continue
        if in_table and line.startswith('## '):
            break
        # 审查P2-1：兼容'🔴待整合'（SKILL.md规范·无空格）与'🔴 待整合'（存量13条带空格）两种写入
        if in_table and ('🔴待整合' in line or '🔴 待整合' in line):
            count += 1
    return count


def days_since_last_drain(text: str) -> int | None:
    """从总追踪表找最后一次 ✅已整合 的日期，返回距今天数"""
    in_table = False
    last_ok = None
    for line in text.split('\n'):
        if line.startswith('## 总追踪表'):
            in_table = True
            continue
        if in_table and line.startswith('## '):
            break
        if in_table and '✅ 已整合' in line:
            # 优先认完整 YYYY-MM-DD；仅 MM-DD 时用当前年份，解出未来日期则回退一年（跨年安全，P2-4修复）
            full = re.findall(r'(\d{4}-\d{2}-\d{2})', line)
            if full:
                try:
                    d = datetime.strptime(full[0], "%Y-%m-%d").date()
                    if last_ok is None or d > last_ok:
                        last_ok = d
                except ValueError:
                    pass
                continue
            dates = re.findall(r'(\d{2}-\d{2})', line)
            if dates:
                try:
                    d = datetime.strptime(f"{date.today().year}-{dates[0]}", "%Y-%m-%d").date()
                    if d > date.today():
                        d = d.replace(year=d.year - 1)
                    if last_ok is None or d > last_ok:
                        last_ok = d
                except ValueError:
                    pass
    if last_ok is None:
        return None
    return (date.today() - last_ok).days


def parse_detailed_entries(text: str) -> list[dict]:
    """从详细反哺条目段提取 🔴待整合 条目的元数据"""
    entries = []
    # 定位到 "## 详细反哺条目" 之后
    detail_start = text.find("## 详细反哺条目")
    if detail_start == -1:
        return entries
    detail_text = text[detail_start:]

    # 按 ### 块头分块（2026-09-22 修：原按 `### 年份-` 分块会漏掉 `### 反哺N：` 类块头 →
    #   整批并成一个巨块，块内后段条目的 🔴 被归到"块首那条"的标题上＝**标题错配**。
    #   实证：09-21 批次 4 条真 🔴 被 --report 报成 07-29「定义类决策」与 09-11「批判验证」
    #   两个与 🔴 无关的旧标题，致 E9.1 备料对准了错对象。按 `### ` 全量分块即根治。）
    blocks = re.split(r'\n(?=### )', detail_text)
    for block in blocks:
        # 审查ND-1修复：--report 路径同样兼容双格式（首轮只改了 --check 路径致 --report 回退 2→1）
        # 2026-09-22 修（真根因·口径分裂之源）：原按「块内含 🔴待整合 字样」判 — 会把
        #   `🔍 验证触发场景` 里的**散文提及**（"季度 Skill 维护扫描 🔴 待整合时"）当成状态行，
        #   致 3 个**已整合**条目被虚计（实证：--check 1 vs --report 4）。
        #   改为**只认「🚦 状态」字段行**：`状态` 后随分隔符即 🔴 待整合。
        if not re.search(r'状态\s*\**\s*[：:|]\s*\**\s*🔴\s*待整合', block):
            continue
        entry = {}
        # 兼容三种格式（审查ND-1补·复核实盘100处加粗形态）：**🔖 反哺标题**：value / - 🔖 **反哺标题**：value / | 🔖 反哺标题 | value |
        m = re.search(r'(?:^\|\s*|^\s*[-*]\s*)?🔖\s*\*{0,2}\s*反哺标题\s*\*{0,2}\s*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['title'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*|^\s*[-*]\s*)?📅\s*\*{0,2}\s*日期\s*\*{0,2}\s*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['date'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*|^\s*[-*]\s*)?📚\s*\*{0,2}\s*建议落点\s*\*{0,2}\s*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['target'] = m.group(1).strip().rstrip('|').strip()
        m = re.search(r'(?:^\|\s*|^\s*[-*]\s*)?📝\s*\*{0,2}\s*反哺内容\s*\*{0,2}\s*[：:|]?\s*(.+)', block, re.MULTILINE)
        if m:
            entry['summary'] = m.group(1).strip().rstrip('|').strip()[:120]
        m = re.search(r'(?:^\|\s*|^\s*[-*]\s*)?⚡\s*\*{0,2}\s*重要度\s*\*{0,2}\s*[：:|]?\s*(高|低)', block, re.MULTILINE)
        if m:
            entry['priority'] = m.group(1)

        if entry.get('title'):
            entries.append(entry)
    return entries


def _append_scan_trail(backlog, alarm, days):
    """E0 扫描动作凭证（append-only）。2026-10-10 Qoder CN·供 tsl_verify v0.11.8 L7-2 读账。

    为什么由脚本写：backlog 数**本脚本自己算**——若让 AI 报"我扫了，没候选"，那还是自证；
    脚本落账后该回合的"无对象"有独立凭证（承 v0.11.7 L7-3「动作即凭证」同一范式）。
    fail-open：写失败绝不影响 --check 的原有 stdout/exit 语义（守卫不阻断纪律）。
    """
    try:
        import datetime as _dt
        import json as _json
        import os as _os
        from pathlib import Path as _P
        p = _P(_os.environ.get("DOENGLINGZ_E0_TRAIL") or
               str(_P(__file__).resolve().parent.parent / "logs" / "e0_scan_trail.jsonl"))
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": _dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
               "backlog": int(backlog), "alarm": bool(alarm),
               "since_last_drain": days,
               "src": _os.environ.get("DOENGLINGZ_SRC", "unknown"),
               "by": "drain-backlog.cmd_check"}
        with p.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def cmd_check():
    """--check: 输出 JSON 状态。
    v0.4（2026-09-22）：口径归一——原 n=count_backlog(总追踪表行数)，与 --report(详细条目块数)
      **同账两口径**（实证 1 vs 4）。改以**详细条目为唯一真源**（源=详细条目，总追踪表=派生索引），
      并把两口径差作为 `tracker_detail_gap` 显形（⛔不静默——两本账不齐本身就是要报的账）。"""
    if not FEEDBACK_LOG.exists():
        print(json.dumps({"backlog": 0, "alarm": False, "since_last_drain": None, "error": "feedback log not found"}))
        sys.exit(0)
    text = FEEDBACK_LOG.read_text(encoding='utf-8')
    tracker = count_backlog(text)                       # 总追踪表口径（派生索引）
    n = len(parse_detailed_entries(text))               # 详细条目口径（唯一真源）
    days = days_since_last_drain(text)
    alarm = n >= ALARM_THRESHOLD or (days is not None and days >= 30)
    result = {"backlog": n, "tracker_rows": tracker, "tracker_detail_gap": tracker - n,
              "alarm": alarm, "since_last_drain": days}
    # 只在**成功扫描**路径落凭证：上面 `error: feedback log not found` 分支不落（错误态不得换 GO）。
    _append_scan_trail(n, alarm, days)
    print(json.dumps(result))
    sys.exit(0 if not alarm else 1)


def cmd_report():
    """--report: 输出排空报告 Markdown 表格"""
    if not FEEDBACK_LOG.exists():
        print("规范反哺日志不存在")
        sys.exit(1)
    text = FEEDBACK_LOG.read_text(encoding='utf-8')
    entries = parse_detailed_entries(text)
    if not entries:
        print("✅ 无 🔴待整合 条目")
        return

    print(f"## ⚠️ 反哺管道积压：{len(entries)} 条 🔴待整合\n")
    print("| # | 日期 | 重要度 | 标题 | 建议落点 | 内容摘要 |")
    print("|:-:|:----:|:------:|------|---------|---------|")
    for i, e in enumerate(entries, 1):
        title = e.get('title', '?')[:50]
        d = e.get('date', '?')
        p = e.get('priority', '?')
        target = e.get('target', '?')[:45]
        summary = e.get('summary', '?')[:80]
        print(f"| {i} | {d} | {p} | {title} | {target} | {summary} |")


DOC_ROOTS = [
    Path.home() / "[记忆共享中心]/记忆蓝图",
    Path.home() / "[记忆共享中心]/记忆规则",
    Path.home() / "[记忆共享中心]/技能配置",      # 2026-09-22 补：反哺落点常是 Skill（如 clock-loop）
]
APPLY_THRESHOLD = 0.5          # 回标门槛：落点覆盖率 ≥ 此值才判「疑似已整合」（低阈值不放行·防误回标）
_STOP_CHARS = set("的了呢吗和与或及等在对不为以于从这那有是了地得着把被")


def _resolve_target(target: str):
    """从自由文本落点解析真实文件路径。
    ①先认**显式文件名 token**（如 `references/pkg-checkup.md`）——落点常直接点名文件；
    ②退化为按 或/、/，/ /§ 切候选取首个中文/字母串 rglob。"""
    t = target or ""
    for fn in re.findall(r'[A-Za-z0-9_\-]+\.(?:md|py|sh|json|yaml|yml)', t):
        for root in DOC_ROOTS:
            if root.exists():
                for p in root.rglob(fn):
                    return p
    for c in re.split(r'[或、,，/]|§', t):
        m = re.search(r'[\u4e00-\u9fffA-Za-z0-9_\-]+', c)
        if not m:
            continue
        stem = m.group(0)
        if len(stem) < 4:
            continue
        for root in DOC_ROOTS:
            if not root.exists():
                continue
            for p in root.rglob(f"*{stem}*.md"):
                return p
    return None


def _key_terms(text: str) -> set:
    """提关键片段：中文**二元组**（中文无空格·整句会成单 token → bigram 提召回）+ 字母数字 ≥3 字。
    剔除「两字全为停用字」的 bigram（如「的了」）。"""
    out = set()
    for run in re.findall(r'[\u4e00-\u9fff]{2,}', text or ""):
        out |= {run[i:i + 2] for i in range(len(run) - 1)}
    out |= set(re.findall(r'[A-Za-z0-9_\-]{3,}', text or ""))
    return {t for t in out if not (len(t) == 2 and all(c in _STOP_CHARS for c in t))}


def _coverage(terms: set, doc_text: str) -> float:
    if not terms:
        return 0.0
    return sum(1 for t in terms if t in doc_text) / len(terms)


def trace_integrated(entries: list) -> list:
    """已整合追溯：逐条拿「落点文件全文」核对该反哺是否已被覆盖（2026-09-22 新增）。
    ⛔核心判据＝语义覆盖（条款文字是否已在落点出现），⛔不是看台账状态字段——
    依据：2026-09-22 实证——反哺②台账挂 🔴，其条文早已写进 01-知识库 §四 v1.7。"""
    out = []
    for e in entries:
        target, title, summary = e.get('target', ''), e.get('title', ''), e.get('summary', '')
        path = _resolve_target(target)
        if not path or not path.exists():
            out.append({**e, 'resolved': None, 'coverage': None, 'verdict': '❓未解析落点'})
            continue
        doc = path.read_text(encoding='utf-8', errors='replace')
        terms = _key_terms(title) | _key_terms(summary)
        cov = _coverage(terms, doc)
        # 强信号（2026-09-22 补）：落点带**来源标注**——本反哺日期 + "反哺"字样同时出现
        #   ＝已按 E9.2 整合的确定性证据（落点常改措辞，词面 bigram 覆盖会漏；实证：
        #   pkg-checkup.md 含 `[来源: 成长箱反哺 | 日期: 2026-08-11 | 反哺标题: …]`，
        #   而标题 bigram 覆盖只 0.2 被误判"确未整合"）。命中即视作已整合。
        d = (e.get('date') or '')[:10]
        src_hit = bool(re.search(r'\d{4}-\d{2}-\d{2}', d) and d in doc and '反哺' in doc)
        out.append({**e, 'resolved': str(path),
                    'coverage': 1.0 if src_hit else round(cov, 2),
                    'src_annot': src_hit,
                    'verdict': '✅疑似已整合' if (src_hit or cov >= APPLY_THRESHOLD) else '🔴确未整合'})
    return out


def cmd_trace(apply: bool = False):
    """--trace：输出「已整合追溯」报告；--apply：把判定为已整合的条目回标 ✅（总追踪表+详细条目）。"""
    if not FEEDBACK_LOG.exists():
        print("规范反哺日志不存在")
        sys.exit(1)
    text = FEEDBACK_LOG.read_text(encoding='utf-8')
    entries = parse_detailed_entries(text)
    if not entries:
        print("✅ 无 🔴待整合 条目")
        return
    res = trace_integrated(entries)
    print(f"## 🔎 已整合追溯（{len(res)} 条 🔴 待核对·阈值 {APPLY_THRESHOLD}）\n")
    print("| # | 标题 | 落点解析 | 覆盖率 | 判定 |")
    print("|:-:|------|---------|:------:|------|")
    for i, r in enumerate(res, 1):
        print(f"| {i} | {r.get('title','?')[:38]} | {(r.get('resolved') or '—').split('/')[-1]} "
              f"| {r.get('coverage') if r.get('coverage') is not None else '—'} | {r['verdict']} |")
    to_apply = [r for r in res if r['verdict'] == '✅疑似已整合' and r.get('title')]
    if apply and to_apply:
        # 回标＝**块内作用域**替换：详细条目的 🔴 在「🚦 状态」独立行（与标题不同行），
        #   故不能只按"同行含标题"替换（2026-09-22 实证：首版按同行替换→报"已回标 2 条"实 0 变更＝假绿）。
        #   策略：标题出现的行开启作用域，直到下一个 ### 块头（非目标）关闭；作用域内 🔴 行全回标。
        keys = [r['title'][:10] for r in to_apply]
        out, active, n_repl = [], None, 0
        for ln in text.split('\n'):
            if ln.startswith('### '):
                active = next((k for k in keys if k in ln), None)   # 新块头：命中目标才开作用域
            if ln.lstrip().startswith('|'):
                # 表格行＝**自包含**：只有本行含目标标题才回标（⛔不借块作用域——
                #   2026-09-22 实测：借作用域会让相邻的"非目标行"（如发版门禁条）被连带回标＝假绿）
                if any(k in ln for k in keys) and ('🔴待整合' in ln or '🔴 待整合' in ln):
                    ln = ln.replace('🔴待整合', '✅已整合').replace('🔴 待整合', '✅已整合')
                    n_repl += 1
            elif active and ('🔴待整合' in ln or '🔴 待整合' in ln):
                ln = ln.replace('🔴待整合', '✅已整合').replace('🔴 待整合', '✅已整合')
                n_repl += 1
            out.append(ln)
        new = '\n'.join(out)
        FEEDBACK_LOG.write_text(new, encoding='utf-8')
        # 独立复验（⛔不假绿）：重解析详细条目，🔴 块数必须真降，否则如实报 FAIL
        left = len(parse_detailed_entries(new))
        ok = left < len(entries)
        print(f"\n{'✅' if ok else '🔴'} 回标{'' if ok else '失败'}：改动 {n_repl} 行 · "
              f"🔴条数 {len(entries)}→{left}（{'真降' if ok else '未降＝假绿·请人工核'}）"
              f"→ {'已回标 '+str(len(to_apply))+' 条' if ok else '未生效'}")
    elif to_apply:
        print(f"\n💡 {len(to_apply)} 条疑似已整合——加 `--apply` 回标（默认只报不改·防误回标）")


def main():
    parser = argparse.ArgumentParser(description='反哺管道排空脚本')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='统计 🔴待整合 数量，输出 JSON')
    group.add_argument('--report', action='store_true', help='逐条输出排空报告')
    group.add_argument('--trace', action='store_true', help='已整合追溯：核对落点是否已覆盖')
    parser.add_argument('--apply', action='store_true', help='配合 --trace：把判定已整合的条目回标 ✅')
    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.report:
        cmd_report()
    elif args.trace:
        cmd_trace(apply=args.apply)


if __name__ == '__main__':
    main()
