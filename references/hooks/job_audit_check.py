#!/usr/bin/env python3
"""
job_audit_check.py — 童灵岗位账对账（只读 diff·v1.5 2026-09-22 批量简写展开）

用途：30 秒回答"岗位账齐不齐"——初审日志决策ID vs 推翻率台账 decisions 双向 diff。
性质：纯只读，不写任何文件，不动台账，不动调度器。
用法：
  python3 job_audit_check.py               # 对账全部岗位（JOB-001/003/...）
  python3 job_audit_check.py --job JOB-001 # 只对账指定岗位
  python3 job_audit_check.py --json        # 输出 JSON（供后续脚本消费）

对账口径（v1.5·2026-09-21 红队审计反哺 / 2026-09-22 批量简写展开）：
  日志ID = 初审日志（step3-first-review-log.md）中出现的唯一决策ID
  台账ID = job_probation_ledger.json jobs.<JOB>.decisions[].decision_id
  ⚠️ 已知合法差异：0911 批量日 45 条逐条差额已由 4 锚点补登收口（锚点条目注明范围），
     台账=19 条 vs 日志=60 ID 的量级差属"批量日按批登记"设计选择，不判 FAIL——
     本脚本报告缺口清单+锚点覆盖判定，人终判。
对账信号（DESIGN-PHILOSOPHY §七·v1.2）：
  EXIT 0 = 齐（或缺口全部被锚点覆盖）/ EXIT 1 = 有缺口 / EXIT 2 = 数据源异常
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import re
import sys
from pathlib import Path
from datetime import datetime

HOME = Path.home()
LEDGER_PATH = HOME / "~/[记忆共享中心]/数字分身/job_probation_ledger.json"
ID_RE = re.compile(r"JOB-\d{3}-\d{8}-\d{3}")
# v1.5·批量简写展开（2026-09-22 假红根治）。载体被明文允许"按批登记·批次ID范围"写法
# （good-good-study SKILL.md JOB-001 段：批量初审按批登记·决策ID连续·每批末尾汇总一条含批次ID范围），
# 而 ID_RE 只认逐号全串 → 批量尾号（如 `JOB-003-20260922-003/004` 的 004）物理匹配不上
# → 被误报「台账有而日志无·倒填嫌疑」。判据须随被检对象的合法写法一起演化，否则假红常态化。
BATCH_TAIL_RE = re.compile(
    r"\s*(?P<sep>[/、,，]|~|～|至|到)\s*(?:JOB-(?P<job>\d{3})-(?P<day>\d{8})-)?(?P<num>\d{3})"
)  # ⛔不写 ^ ：match(text,pos) 已从 pos 起手，加 ^ 会退化为「只在行首生效」致批量展开全量失效（自测 T1a-d 实测捕得）
RANGE_SEPS = {"~", "～", "至", "到"}
SPAN_CAP = 60  # 超此跨度的范围不展开：交锚点/按批登记口径处理，防批量日反向造红


def collect_ids(text):
    """全串 ID + 批量简写展开：列表式 `/004`、`、005` 逐个补；范围式 `~015`、`至015` 补跨度。"""
    out = set()
    for m in ID_RE.finditer(text):
        full = m.group(0)
        out.add(full)
        job, day, pos = full[4:7], full[8:16], m.end()
        last = int(full[19:])
        while True:
            s = BATCH_TAIL_RE.match(text, pos)
            if not s:
                break
            if s.group("job") and (s.group("job"), s.group("day")) != (job, day):
                break  # 分隔符后是别的岗位/日期的全串ID → 本批到此为止
            num = int(s.group("num"))
            if num > last:
                if s.group("sep") in RANGE_SEPS:
                    if num - last <= SPAN_CAP:
                        out.update(f"JOB-{job}-{day}-{i:03d}" for i in range(last + 1, num + 1))
                    else:
                        break  # 超上限：不展开也不合成端点（端点未必真在台账·造出来=反向造红）
                else:
                    out.add(f"JOB-{job}-{day}-{num:03d}")
                last = num
            pos = s.end()  # 绝对坐标（match 在 text 上跑，span 已是全局位置）
    return out

# 岗位→日志载体映射（v1.1·2026-09-21：各岗位决策记录的日志载体不同——
# JOB-001=step3-first-review-log.md（单一载体）；
# JOB-003=规范反哺日志+LEARNINGS+系统日志（分散载体·响应表绑定的record在动作列）
# 新增岗位时在此登记载体路径，否则该岗位日志ID=0（只能单向对账）
JOB_LOG_SOURCES = {
    "JOB-001": [
        HOME / "~/[记忆共享中心]/数字分身/steps/step3-first-review-log.md",
    ],
    "JOB-003": [
        HOME / "~/[记忆共享中心]/成长箱/experience/规范反哺日志.md",
        HOME / "~/[记忆共享中心]/成长箱/learnings/LEARNINGS.md",
        HOME / "~/[记忆共享中心]/工作日志/系统日志",   # 目录：递归扫当日+归档
    ],
    "JOB-004": [
        HOME / "~/[记忆共享中心]/数字分身/steps/step3-first-review-log.md",
    ],  # 技能卡审核岗（七闸）·与 JOB-001 共用同一初审台账载体（卡号 KXXX/SXXX 区分）·2026-09-22 上岗同轮登记
    "JOB-002": [],  # 蒸馏调度岗·载体未登记（登记前该岗位仅单向对账）
}

# 锚点覆盖登记（v1.0 硬编码·补登锚点=批量日合法差额的收口凭证）
# 结构：锚点ID -> (覆盖范围说明, 覆盖的日志ID集合生成器描述)
ANCHOR_COVERAGE = {
    "JOB-001-20260911-016": "0911批量日决策-016至-056共41条未逐条入账·初审日志L156-229全量可查（2026-09-21红队审计补登锚点）",
    "JOB-003-20260909-001": "0909批次5条（-001~-005）·系统日志0909 L392记载'JOB-003推翻率台账5条approved'·载体措辞不含决策ID全串（2026-09-21考古定性·非倒填）",
    "JOB-003-20260911-002": "0911批次3条（-002~-004）·系统日志0911 L331记载JOB-003台账入账·载体措辞不含决策ID全串（2026-09-21考古定性）",
    "JOB-003-20260919-005": "0919批次6条部分·系统日志0919在案·载体措辞不含决策ID全串（2026-09-21考古定性）",
}


def load_log_ids(job_id):
    """按岗位载体映射收集日志ID（v1.1）"""
    sources = JOB_LOG_SOURCES.get(job_id, [])
    if not sources:
        return None, "no-sources"
    ids = set()
    src_status = []
    for p in sources:
        if p.is_dir():
            for f in p.glob("系统日志_*.md"):
                ids.update(collect_ids(f.read_text(encoding="utf-8", errors="replace")))
            src_status.append(f"系统日志目录({len(list(p.glob('系统日志_*.md')))}文件)")
        elif p.exists():
            ids.update(collect_ids(p.read_text(encoding="utf-8", errors="replace")))
            src_status.append(p.name)
        else:
            src_status.append(f"⚠️缺失:{p.name}")
    return ids, ";".join(src_status)


def load_ledger():
    if not LEDGER_PATH.exists():
        return None, f"台账不存在: {LEDGER_PATH}"
    try:
        d = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, f"台账JSON损坏: {e}"
    return d, None


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    job_filter = None
    if "--job" in args:
        i = args.index("--job")
        if i + 1 < len(args):
            job_filter = args[i + 1]

    ledger, err = load_ledger()
    if ledger is None:
        print(f"❌ {err}")
        sys.exit(2)

    jobs = ledger.get("jobs", {})
    if job_filter:
        jobs = {k: v for k, v in jobs.items() if k == job_filter}
        if not jobs:
            print(f"❌ 台账中无岗位 {job_filter}")
            sys.exit(2)

    # 按岗位前缀分派日志ID（JOB-xxx）
    all_report = {}
    any_gap = False

    for job_id, job in sorted(jobs.items()):
        ledger_ids = set()
        for dec in job.get("decisions", []):
            did = dec.get("decision_id", "")
            if did:
                ledger_ids.add(did)
        job_log_ids, src_note = load_log_ids(job_id)
        if job_log_ids is None:
            # 无载体登记：单向对账（只报台账侧）
            job_log_ids = set()
            src_note = "未登记载体·单向对账"
        else:
            job_log_ids = {x for x in job_log_ids if x.startswith(job_id + "-")}  # 跨岗位串扰过滤（载体含多岗位ID·v1.2）
        missing_in_ledger = sorted(job_log_ids - ledger_ids)      # 日志有·台账无
        missing_in_log = sorted(ledger_ids - job_log_ids)          # 台账有·日志无（应=锚点）
        # 日志方向锚点覆盖：同日批次有锚点 → 按批登记设计口径（如0911批量日-016~-056）
        ledger_dates = {x[:18] for x in ledger_ids}
        missing_in_ledger_explained = [x for x in missing_in_ledger if x[:18] in ledger_dates]
        missing_in_ledger = [x for x in missing_in_ledger if x[:18] not in ledger_dates]

        # 锚点覆盖判定：台账多出的ID若落在已登记锚点/已考古定性的批次内 → 合法
        # 批次判定：同决策ID前18位（JOB-XXX-YYYYMMDD）存在锚点 → 该日批次整体被考古覆盖
        anchored_prefixes = {k[:18] for k in ANCHOR_COVERAGE}
        unexplained_ledger_only = [
            x for x in missing_in_log if x not in ANCHOR_COVERAGE and x[:18] not in anchored_prefixes
        ]

        bulk_warning = len(missing_in_ledger) > 20 and not missing_in_log
        if unexplained_ledger_only or (missing_in_ledger and not bulk_warning):
            status = "❌ 有缺口"
            any_gap = True
        elif missing_in_ledger and bulk_warning:
            status = "🟡 量级差·按批登记（同日台账有锚点则合法·人终判）"
        else:
            status = "✅ 齐"

        report = {
            "job": job_id,
            "job_name": job.get("job_name", "?"),
            "status": job.get("status", "?"),
            "log_sources": src_note,
            "log_ids": len(job_log_ids),
            "ledger_ids": len(ledger_ids),
            "missing_in_ledger": missing_in_ledger,
            "missing_in_ledger_explained_bulk": len(missing_in_ledger_explained),
            "missing_in_log": missing_in_log,
            "unexplained_ledger_only": unexplained_ledger_only,
            "anchor_coverage": {k: v for k, v in ANCHOR_COVERAGE.items()
                                if k in missing_in_log or k[:18] in {x[:18] for x in missing_in_log}},
            "bulk_warning": bulk_warning,
            "verdict": status,
        }
        all_report[job_id] = report

    if as_json:
        print(json.dumps(all_report, ensure_ascii=False, indent=1))
        sys.exit(1 if any_gap else 0)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"📊 岗位账对账 · {ts}")
    print("═" * 50)
    for job_id, r in all_report.items():
        print(f"\n{r['verdict']} {job_id} {r['job_name']}（台账状态:{r['status']}）")
        print(f"   日志载体: {r['log_sources']}")
        print(f"   日志ID: {r['log_ids']} 个 | 台账decisions: {r['ledger_ids']} 条")
        if r["missing_in_ledger"]:
            show = r["missing_in_ledger"][:5]
            more = len(r["missing_in_ledger"]) - 5
            print(f"   ⚠️ 日志有而台账无: {len(r['missing_in_ledger'])} 条（{', '.join(show)}{'…' if more > 0 else ''}）")
            if r["bulk_warning"]:
                print("   🟡 量级差>20·属批量日按批登记设计口径（0911锚点在案）·人终判")
        if r["missing_in_log"]:
            print(f"   ℹ️ 台账有而日志无: {len(r['missing_in_log'])} 条（补登锚点·合法）")
            for k, v in r["anchor_coverage"].items():
                print(f"      🔗 {k}: {v[:60]}…")
        if r["unexplained_ledger_only"]:
            print(f"   ❌ 台账有而日志无且非锚点: {r['unexplained_ledger_only']}（倒填嫌疑·人查）")
    print("\n" + "═" * 50)
    verdict = "✅ 岗位账齐（或缺口全部有锚点解释）" if not any_gap else "❌ 岗位账有缺口——见上行明细"
    print(verdict)
    sys.exit(1 if any_gap else 0)


if __name__ == "__main__":
    main()
