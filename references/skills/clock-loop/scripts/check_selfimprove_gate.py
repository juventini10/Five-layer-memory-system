#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自进步门禁触发器（确定性 · 文件计数锚定）

来源：clock-loop v2.5.3 阶段4 收尾门禁
用途：确定性统计 test_results/ 下评估报告数量，输出 L3沉淀是否必须运行。
v3.0.0新增：双盲审计到期检测（每10份评估报告触发一次双盲+人类锚审计）。
v3.0.4修复：L3触发从"整除5"改为"增量≥5"——自上次L3以来新积累5份报告即触发，
  解决多源写入导致计数器非线性跳变时漏触发的问题（实测22份报告，15/20两个5的倍数均被跳过）。
不做AI语义判定——纯路径计数 + 日期解析，可grep可复现。

设计依据：L3沉淀原靠"AI数文件 + post-delivery SHOULD"触发，实测10份报告零产物
（AI漏跑/数错）。本脚本将"是否触发L3"变为确定性决策：门禁以 `l3_required`
字段为准，不靠AI自觉或算术。与对话冲突管道同哲学（修复#4：脚本确定性加载，
不靠"AI记得去看"）。

双盲审计触发依据：反方向的钟设计哲学§九#8——自指不可消除，用常态外部审计
压缩自指偏差存续时间。触发机制在脚本里不在prose里（机制代替意志力）。

输出格式（JSON）：
{
  "report_count": N,
  "l3_required": true|false,   # v3.0.4: 自上次L3以来新积累 >=5 份报告 → true
  "last_l3_date": "YYYY-MM-DD" | null,
  "last_l3_n": int | null,     # v3.0.4: 上次L3时的报告数
  "days_since_l3": int | null,
  "double_blind_due": true|false,  # v3.0.0: N>=10 且双盲报告数不足时触发
  "double_blind_count": int,       # 已完成的双盲审计报告数
  "double_blind_overdue_n": int,   # v3.11.1: 双盲欠账次数(应审-已审)——≥2时门禁③冻结clock-loop自身版本升级
  "next_double_blind_at": int      # 下次双盲到期时的报告数阈值
}

失败处理：
- test_results 目录不存在 → 返回 {"report_count":0,"l3_required":false,...,"double_blind_due":false}
- 解析异常 → 打印错误到stderr，返回安全默认（l3_required=false, double_blind_due=false），不崩溃
- 日期解析失败 → last_l3_date=null, days_since_l3=null

用法：
  python3 check_selfimprove_gate.py [--test-results PATH] [--evolution PATH]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import sys
from datetime import datetime, date
from pathlib import Path

DEFAULT_TEST_RESULTS = "[记忆共享中心]/评估知识库/test_results"
DEFAULT_EVOLUTION = "[记忆共享中心]/评估知识库/evolution"


def resolve_path(p: str) -> Path:
    return Path(p).expanduser()


def _count_valid_reports(test_results: Path, pattern: str) -> int:
    """v3.50.0（#41 空文件绕过硬门禁根治）：文件名命中且 非空+≥3非空行 才计数。

    旧逻辑=纯文件名计数——造一个空的"xx双盲xx.md"即可清零欠账、解冻自升级
    （存在性≠有效性·#41）。威胁模型=非恶意偷懒（GS-1 L204）·不防对抗性伪造。
    """
    if not test_results.exists():
        return 0
    n = 0
    for f in test_results.rglob(pattern):
        try:
            if f.stat().st_size == 0:
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                lines = [ln for ln in fh.read().splitlines() if ln.strip()]
            if len(lines) >= 3:
                n += 1
        except OSError:
            continue
    return n


# 自评估报道命名清单（v修复·G/H 路径计数缺口根治）：
# 扩展: E/F 命名碎片化一并根治——原仅 *评估报告*.md 致 E/F 非"评估报告"命名
# (Loop评估/修复闭环报告/子Agent审查报告/重评估/修复报告) 与 G/H 均不进 5/10 cadence
# 计数（通用规范:148 实证 + self_check_uncounted 实测 E/F 碎片化 15 份）。
# 语义锚 = 「loop 自评估报道(可交付)」；凡落 test_results/ 且命名命中以下任一即计。
# 明确排除(非交付物·不进 cadence): *双盲*.md(由 count_double_blind_reports 单独计数)
# / *sim*.md(仿真) / *changeplan*.md(变更计划)。
# 新增路径命名须同步加入此清单(或经 funnel 登记)，否则 self_check_uncounted 会告警。
KNOWN_SELF_ASSESSMENT_PATTERNS = [
    "*评估报告*.md",
    "*Loop评估*.md",
    "*修复闭环报告*.md",
    "*子Agent审查报告*.md",
    "*重评估*.md",
    "*修复报告*.md",
    "*检查报告*.md",
    "*发布包检查报告*.md",
    "*loop报告*.md",
    "*体检报告*.md",
]


def count_reports(test_results: Path) -> int:
    """统计 test_results/ 下所有 loop 自评估报道（E/F/G/H 全路径），排除 progress 等非报道文件。

    v修复: 扩展覆盖 G/H 命名（原仅靠 *评估报告*.md 致 G/H 静默漏计）。
    """
    return sum(_count_valid_reports(test_results, p) for p in KNOWN_SELF_ASSESSMENT_PATTERNS)


def self_check_uncounted(test_results: Path) -> "list[str]":
    """v修复: 自显形自检——扫描带路径标记的未计数自评估报道并告警。

    根因=计数锚是脆弱文件名 glob，新路径命名会静默绕过（打地鼠）。
    本函数让绕过「响」而非「静默漏」：凡 frontmatter 含路径标记
    (task_type: E/F/G/H.xxx / type: reference / type: report) 且未命中
    KNOWN_SELF_ASSESSMENT_PATTERNS 且非 progress_ 的 .md，列出供人工补登记。
    仅告警不阻断——cadence 仍由 KNOWN 清单兜底。
    """
    if not test_results.exists():
        return []
    warns = []
    counted = set()
    for p in KNOWN_SELF_ASSESSMENT_PATTERNS:
        for f in test_results.rglob(p):
            counted.add(f.resolve())
    for f in test_results.rglob("*.md"):
        try:
            rp = f.resolve()
            if rp in counted:
                continue
            if f.name.startswith("progress_"):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if not text.startswith("---"):
                continue
            fm = text.split("---", 2)[1] if text.count("---") >= 2 else ""
            has_marker = (
                re.search(r"^task_type:\s*(E|F|G|H)\.", fm, re.M) is not None
                or re.search(r"^type:\s*reference\s*$", fm, re.M) is not None
                or re.search(r"^type:\s*report\s*$", fm, re.M) is not None
            )
            if has_marker:
                warns.append(str(f.relative_to(test_results)))
        except OSError:
            continue
    return warns


def _parse_count_single(latest) -> "int | None":
    """单文件解析 l3_report_count（v4.17.0 歧义修复拆出·兼容旧「触发…report_count=N」推断）。"""
    latest = None
    try:
        with open(latest, 'r', encoding='utf-8') as fh:
            for line in fh:
                m = re.search(r"l3_report_count:\s*(\d+)", line)
                if m:
                    return int(m.group(1))
    except Exception:
        pass
    # 向后兼容：旧沉淀文件无 l3_report_count 字段，尝试从「触发：...N份」推断
    try:
        with open(latest, 'r', encoding='utf-8') as fh:
            for line in fh:
                m = re.search(r"触发.*?report_count[：:=]\s*(\d+)|累计.*?(\d+)\s*份|报告数\s*[:：=]?\s*(\d+)", line)
                if m:
                    for g in m.groups():
                        if g:
                            return int(g)
    except Exception:
        pass
    return None


def _parse_l3_count_from_file(evolution_dir: Path, l3_date: str) -> "int | None":
    """同日期全候选取 max（v4.17.0 歧义修复）。"""
    cands = []
    for f in evolution_dir.rglob("L3_沉淀_*.md"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if m and m.group(1) == l3_date:
            cands.append(f)
    vals = [v for v in (_parse_count_single(f) for f in cands) if v is not None]
    return max(vals) if vals else None


def last_l3_info(evolution: Path) -> "tuple[str|None, int|None]":
    """返回 (最新L3日期, 当时报告数)。"""
    if not evolution.exists():
        return None, None
    dates = []
    for f in evolution.rglob("L3_沉淀_*.md"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.name)
        if m:
            dates.append(m.group(1))
    if not dates:
        return None, None
    latest_date = max(dates)
    latest_n = _parse_l3_count_from_file(evolution, latest_date)
    return latest_date, latest_n


def count_double_blind_reports(test_results: Path) -> int:
    """统计 test_results/ 下双盲审计报告数量（*双盲*.md）。

    v3.0.0新增：每10份评估报告应触发1次双盲审计。
    双盲报告数不足 → double_blind_due=true。
    v3.50.0：改走 _count_valid_reports（非空+≥3非空行·#41空文件绕过根治）。
    """
    return _count_valid_reports(test_results, "*双盲*.md")


# 双盲审计触发阈值：每10份评估报告触发1次
DOUBLE_BLIND_THRESHOLD = 10

# L3沉淀阈值：自上次L3以来新积累5份报告即触发
L3_INCREMENT_THRESHOLD = 5


def main():
    ap = argparse.ArgumentParser(description="自进步门禁触发器（确定性计数）")
    ap.add_argument("--test-results", default=DEFAULT_TEST_RESULTS, help="评估报告根目录")
    ap.add_argument("--evolution", default=DEFAULT_EVOLUTION, help="L3沉淀目录")
    args = ap.parse_args()

    try:
        test_results_path = resolve_path(args.test_results)
        evolution_path = resolve_path(args.evolution)
        n = count_reports(test_results_path)
        uncounted = self_check_uncounted(test_results_path)
        l3_date, last_l3_n = last_l3_info(evolution_path)
        days = None
        if l3_date:
            try:
                days = (date.today() - datetime.strptime(l3_date, "%Y-%m-%d").date()).days
            except ValueError:
                days = None
        
        # v3.0.4: 增量触发——自上次L3以来新积累 >=5 份报告即触发
        # v3.38.2 P2-3修：last_l3_n 解析失败(null)时，若 last_l3_date==今天 → 视为今日已跑，不重复触发；
        # 否则落入首触发分支（保守：宁多跑不静默漏）
        if n >= L3_INCREMENT_THRESHOLD and last_l3_n is not None:
            l3_required = (n - last_l3_n) >= L3_INCREMENT_THRESHOLD
        elif n >= L3_INCREMENT_THRESHOLD and last_l3_n is None:
            if l3_date == date.today().strftime("%Y-%m-%d"):
                # 今日已生成 L3 沉淀但字段解析失败 → 不重复触发（去重防退化）
                l3_required = False
            else:
                # 有报告但没有 L3 沉淀记录 → 首次触发
                l3_required = True
        else:
            l3_required = False
        
        # v3.0.0: 双盲审计到期检测——每10份报告应有1次双盲审计
        db_count = count_double_blind_reports(test_results_path)
        expected_db = n // DOUBLE_BLIND_THRESHOLD  # 应有的双盲审计次数
        db_overdue_n = max(0, expected_db - db_count)  # v3.11.1: 双盲欠账次数——≥2时门禁③冻结clock-loop自身版本升级(N1修复)
        double_blind_due = (n >= DOUBLE_BLIND_THRESHOLD and db_count < expected_db)
        next_db_at = ((n // DOUBLE_BLIND_THRESHOLD) + 1) * DOUBLE_BLIND_THRESHOLD if n > 0 else DOUBLE_BLIND_THRESHOLD
        
        # v4.12.2·R2-N-01/N-02：pending_review 超期接线（#55载体建了零消费的收口）——
        # 复用 record_fix --overdue 单一实现（subprocess 防第二套路径口径），stdout 天数即取
        _pr_days, _pr_err = 0, None
        try:
            import subprocess as _sp
            _rf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record_fix.py')
            _r = _sp.run([sys.executable, '-B', _rf, '--overdue'], capture_output=True, text=True, timeout=30)
            _m = re.search(r'PENDING_REVIEW_DAYS:\s*(-?\d+)', _r.stdout)  # v4.12.3·攻3根治：与record_fix同一机器行口径（旧"天"字样正则把fail-closed读成0健康）
            _pv = int(_m.group(1)) if _m else -1
            _pr_days = _pv if _pv >= 0 else 0
            if _pv < 0 or _r.returncode == 5:
                _pr_err = 'record_fix fail-closed(-1/rc5)——pending不可确知（非0天健康）'
            elif _r.returncode not in (0, 4):
                _pr_err = f"rc={_r.returncode}"
            else:
                _pr_err = None
        except Exception as _e:
            _pr_err = str(_e)  # fail-visible：不静默给0
        out = {
            "report_count": n,
            "pending_review_overdue_days": _pr_days,
            "pending_review_reader_wired": True,  # v4.12.2 消费位实证标志
            **({"pending_review_err": _pr_err} if _pr_err else {}),
            "l3_required": l3_required,
            "last_l3_date": l3_date,
            "last_l3_n": last_l3_n,
            "days_since_l3": days,
            "double_blind_due": double_blind_due,
            "double_blind_count": db_count,
            "double_blind_overdue_n": db_overdue_n,
            "next_double_blind_at": next_db_at,
            "uncounted_self_assessment_warn": uncounted,
        }
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001
        # v3.50.1（#40 fail-open根治）：异常时旧版输出 overdue_n=0 的全绿JSON=门禁被异常静默放行。
        # 改为显式 gate_error 标记 + exit 1——消费方（finalize check_overdue_freeze）遇此必须拒绝放行。
        print(f"ERROR: {e}", file=sys.stderr)
        print(json.dumps(
            {"gate_error": str(e),
             "report_count": 0, "l3_required": False, "last_l3_date": None, "last_l3_n": None,
             "days_since_l3": None,
             "double_blind_due": False, "double_blind_count": 0, "double_blind_overdue_n": 0,
             "next_double_blind_at": DOUBLE_BLIND_THRESHOLD},
            ensure_ascii=False,
        ))
        sys.exit(1)


if __name__ == "__main__":
    main()
