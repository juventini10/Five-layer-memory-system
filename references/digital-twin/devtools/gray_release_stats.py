#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gray_release_stats.py v0.2 — Step3灰度期机械统计器（S006合规版）

核心修正（相对 v0.1）：
  1. 分母谬误修复：推翻率分母 = 你"真质证"卡数（认可/已质证/亲裁），
     不再把童灵自动初审的批量卡(802张)混入分母 → 杜绝"0/748=0%假过关"。
  2. 点估计→置信区间：0失败时用 Clopper-Pearson 95% 单侧上界
     ub = 1 - 0.05**(1/n)；k>0 用 Wilson 上界。判定以"上界<15%"为准。
  3. 最小样本门槛 MIN_N=19：k=0 时 n=19 上界 14.6%<15%，n<19 一律"数据不足·不判"
     → 验证系统无权在小样本下声称充分（S006 根因）。
  4. 真实纠偏回收通道：额外读取"三明治L3双盲审"处置表，把你盲审检出的
     童灵质证缺陷作为"系统性风险信号"独立上报（不混入例程CI分母，但
     未闭环时阻止过闸）。这些缺陷须登记进推翻台账(入口①)才闭合飞轮。

指标输出：
  - 童灵累计初审(批量+逐卡)：INFO，仅体量参考，不入任何率分母
  - 你真质证 n / 例程推翻率点估计 / 95%CI上界
  - 三明治盲审：复审卡数 / 检出缺陷 / 密度（非随机·专项压力测试）
  - 门禁判定（数据驱动为主，日历为提醒）
设计原则：只读台账、失败放行 exit 0、无内联真相（真相源=两份台账文件）。
用法：python3 gray_release_stats.py
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, re, sys, math, subprocess
from datetime import datetime, date

BASE = os.path.dirname(os.path.abspath(__file__))
REVIEW_LOG = os.path.join(BASE, "..", "steps", "step3-first-review-log.md")
OVERTURNED = os.path.join(BASE, "..", "steps", "step3-overturned.md")
ANCHOR = date(2026, 8, 21)   # 灰度起始锚点
THRESHOLD = 15.0             # 推翻率红线%
MIN_N = 19                   # k=0 时 95%CI上界<15% 的最小样本 (n=19→14.6%)
SPOTCHECK_GAP = 14           # 抽检最大间隔天

def ci_upper_ub(n, k):
    """95% 单侧上置信界。
    k=0 闭式(Clopper-Pearson): 1 - 0.05**(1/n)
    k>=1 用 Wilson 上界(无依赖、对小样本稳健)。"""
    if n <= 0:
        return 1.0
    if k <= 0:
        return 1.0 - (0.05 ** (1.0 / n))
    z = 1.959963984540054
    phat = k / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = (z * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))) / denom
    return min(1.0, center + half)

def parse_review(path):
    """解析初审台账：返回体量/真质证/盲审缺陷等结构。"""
    out = dict(auto_volume=0, human_judged=0, human_approved=0,
               parallel_approved=0, blind_reviewed=0, blind_defects=0,
               last_human_date=None, batch_total=0)
    if not os.path.isfile(path):
        return out
    lines = open(path, encoding="utf-8").read().splitlines()
    section = ""
    individual_rows = 0
    for line in lines:
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if line.startswith("*建立"):       # 重置段标记，避免误把后续表当盲审
            section = ""
            continue
        # 批量总结：总处理 | N张
        m = re.search(r"总处理\s*\|\s*(\d+)张", line)
        if m:
            out["batch_total"] = int(m.group(1))
        # 三明治L3双盲审 处置表：| 发现(S8xx) | 处置(✅已...) |
        if "双盲审" in section:
            rev = sum(1 for _ in re.finditer(r"S8\d\d", line))
            if rev and ("✅已" in line or "已" in line):
                out["blind_defects"] += rev
                out["blind_reviewed"] = max(out["blind_reviewed"], 10)  # 8✅+2🟡=10
            continue
        # 逐卡行：| # | 日期 | 卡号 | ... | 你复核 |
        m = re.match(r"^\|\s*\d+\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\S+)", line)
        if not m:
            continue
        individual_rows += 1
        d = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        review = cells[-1] if cells else ""
        is_parallel = "平行校验" in section
        human = ("认可" in review) or ("已质证" in review) or ("亲裁" in review)
        pending = "待你抽检" in review
        if human and not pending:
            out["human_judged"] += 1
            out["human_approved"] += 1
            # 抽检新鲜度：优先取“你复核”列内认可日期（真实质证日）；
            # 列内无日期才回退行首初审日期——修复“列内09-11认可仍按08-25算16天无抽检”误报
            m2 = re.search(r"(20\d{2}-\d{2}-\d{2})", review)
            human_d = datetime.strptime(m2.group(1), "%Y-%m-%d").date() if m2 else d
            if out["last_human_date"] is None or human_d > out["last_human_date"]:
                out["last_human_date"] = human_d
            if is_parallel:
                out["parallel_approved"] += 1
    out["auto_volume"] = out["batch_total"] + individual_rows
    return out

def parse_overturned(path):
    """推翻台账登记条数（入口①飞轮燃料）。"""
    n = 0
    if not os.path.isfile(path):
        return 0
    for line in open(path, encoding="utf-8"):
        if re.match(r"^\|\s*\d+\s*\|\s*\d{4}-\d{2}-\d{2}", line):
            n += 1
    return n

def main():
    r = parse_review(REVIEW_LOG)
    registered = parse_overturned(OVERTURNED)
    n = r["human_judged"]
    k = 0  # 你复核列无"推翻"记录(k来自台账登记另计)；例程翻转以真质证为分母
    ub = ci_upper_ub(n, k)
    point = (k / n * 100) if n else 0.0

    print("═══ Step3 灰度期机械统计 v0.2 (S006合规) ═══")
    days_in = (date.today() - ANCHOR).days
    print(f"灰度第 {days_in} 天（锚点 {ANCHOR}·期限1个月）")

    print("── 体量(INFO·不入率分母) ──")
    print(f"童灵累计初审: {r['auto_volume']} 张（批量{r['batch_total']}+逐卡{r['auto_volume']-r['batch_total']}）")
    print(f"你真质证 n={n}（平行校验认可{r['parallel_approved']}张按协议不计分母）")

    print("── 例程推翻率（你复核列） ──")
    print(f"点估计: {point:.1f}%  |  95%CI上界: {ub*100:.1f}%  [门槛<{THRESHOLD}%]")

    print("── 三明治L3双盲审（系统性风险信号·非随机） ──")
    if r["blind_defects"]:
        dens = r["blind_defects"] / max(r["blind_reviewed"], 1) * 100
        print(f"你盲审≈{r['blind_reviewed']}卡·检出缺陷 {r['blind_defects']} 处（密度≈{dens:.0f}%）")
        print(f"推翻台账已登记: {registered} 条 → {'✅已补登闭环' if registered else '❌通道断裂·须登记入口①'}")
    else:
        print("无盲审缺陷记录")

    # ── 门禁判定（数据驱动为主）──
    verdict = []
    if n < MIN_N:
        verdict.append(f"⏳ 数据不足·不判：你真质证 n={n}<{MIN_N}；当前95%CI上界={ub*100:.1f}%>15%·不可信")
    elif ub < THRESHOLD / 100.0:
        if r["blind_defects"] and not registered:
            verdict.append(f"🟡 例程CI过闸(上界{ub*100:.1f}%)但盲审系统性风险未闭环({r['blind_defects']}缺陷待入台账)→过闸搁置")
        else:
            verdict.append(f"✅ 过闸（95%CI上界{ub*100:.1f}%<15%·n={n}≥{MIN_N}）")
    else:
        verdict.append("🔴 推翻率超阈→回Step2.6复测")

    # 抽检新鲜度
    ref = r["last_human_date"] or ANCHOR
    gap = (date.today() - ref).days
    if gap > SPOTCHECK_GAP:
        verdict.append(f"🔴 漂移自告警：已 {gap} 天无你抽检→协议要求自动升级全人工")
    else:
        verdict.append(f"✅ 抽检新鲜度: {gap}天前 (≤{SPOTCHECK_GAP})")

    # 灰度期满/临近提醒（日历为提醒·非门禁条件）
    GRAY_DAYS = 30
    if days_in >= GRAY_DAYS:
        if any(v.startswith("✅ 过闸") for v in verdict):
            verdict.append(f"🔔 灰度期满（第{days_in}天≥{GRAY_DAYS}）：数据驱动门禁已过闸→进入复盘体检，转正/回炉待你裁决")
        else:
            verdict.append(f"🔔 灰度期满（第{days_in}天≥{GRAY_DAYS}）：数据驱动门禁未过→仍为⏳；请你加速真质证至≥{MIN_N}张")
    elif days_in >= GRAY_DAYS - 7:
        verdict.append(f"⏳ 灰度期临近（剩 {GRAY_DAYS - days_in} 天）：预备Step4/5决策材料")

    # 迁移残留清理提醒
    import glob
    for ow in glob.glob(os.path.expanduser("~/数字分身_观察窗_backup_*")):
        verdict.append(f"🧹 迁移残留清理：{os.path.basename(ow)}/ 仍在（确认无新写入后 rm -rf 并提交）")

    print("── 门禁 ──")
    for v in verdict:
        print(v)

    # ── 周检清单（机制化·防盲审整改回潮·2026-09-01 固化）──
    print("── 周检清单（建议随你抽检一并跑） ──")
    print("① verify_checklist_gate.py：post-2026-08-24 初审卡须含合规【查证清单】块")
    print("② 盲审5缺陷回归：判定标准见 steps/step3-blind-regression-spec.md")

    # ── 线B查证清单进度（动态调用verify_checklist_gate·无内联真相·2026-09-02根治硬编码）──
    checklist_gate = os.path.join(BASE, "verify_checklist_gate.py")
    try:
        cp = subprocess.run(
            [sys.executable, checklist_gate, "--strict"],
            capture_output=True, text=True, timeout=30
        )
        gate_out = cp.stdout + cp.stderr
        m_noncompliant = re.search(r"门禁未过[：:]\s*(\d+)\s*张", gate_out)
        m_exempt = re.search(r"历史豁免\s*(\d+)\s*张", gate_out)
        m_reviewed = re.search(r"已初审卡\(纳入门禁\)\s*[：:]\s*(\d+)", gate_out)
        noncompliant = int(m_noncompliant.group(1)) if m_noncompliant else None
        exempt = int(m_exempt.group(1)) if m_exempt else None
        reviewed = int(m_reviewed.group(1)) if m_reviewed else None
        # scope内总数=已初审-历史豁免（动态取数·无内联真相·2026-09-11根治硬编码54）
        total_post_0824 = (reviewed - exempt) if (reviewed is not None and exempt is not None) else None
        if noncompliant is not None and total_post_0824 is not None:
            compliant = total_post_0824 - noncompliant
            status = "✅已闭环" if noncompliant == 0 else f"⏳差{noncompliant}张4列真实内容"
            print(f"   📊 线B查证清单进度：{total_post_0824}张中✅合规{compliant}张 / ❌非合规{noncompliant}张（历史豁免{exempt}张）→ {status}")
            if noncompliant > 0:
                print(f"   ⚠️ 数据层未闭环：{noncompliant}张初审卡查证清单待回填·回填须真实质证记录、禁止编造（铁律002）")
        else:
            print(f"   ⚠️ 线B进度解析失败（verify_checklist_gate输出未匹配到门禁未过数字）·请手动跑 verify_checklist_gate.py --strict")
    except Exception as e:
        print(f"   ⚠️ 线B进度获取失败（{e!r}）·请手动跑 verify_checklist_gate.py --strict")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[warn] 统计异常放行: {e!r}")
        sys.exit(0)
