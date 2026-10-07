#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""evolution_deviation.py v0.8 — 自主进化活系统·误差量化信号层（引擎类·stats）
v0.8（2026-10-07 Qoder CN 童灵·野根根治轮）：②join 率读侧重写——复用写侧同一提取器 antibody_gate.extract_antibodies（双载体池80·原只扫反哺39=N0扫描域半缺），主键=抗体标题+命令深归一回退；修 split 位置错位与管道截断（81%→8% 静默塌陷根因）。免疫命中数与闭环流同径（带日期行），治 1043/1040/1039 三名字。

控制论闭环定位：参考模型(愿景四方向) → 观测(实际态) → 误差(理想−实际) → 调整。
本脚本只做"误差量化"环：把"实际态 vs 愿景四方向理想态"算成可计算的偏差分，
产出 evolution_deviation_<日期>.json，供 growth-box 蒸馏/月报消费（填值权归脚本·AI只回显）。

v0.7（2026-08-23·你条件授权）：compute_auto_rate 切 v2 口径=hook_auto 事件占比（AUTO_RATE_CUTOFF 排除误标期·legacy route_audit 口径降 compute_auto_rate_legacy 对照列一周期）。
v0.5（2026-08-22·你愿景裁定·结构性少定义定案落地）：
  - ③自主进化改「本季度新增被采纳」口径：净采纳率=本季度新增有效抗体/本季度总提案（防累计存量无牵引·贴进化本义）
  - 四方向输出新增 state 状态行{定案/过渡/N-A}（过渡/N-A不得冒充定案·机械校验）：
      ①全自动化=定案(returncode==0审计成功占比·证自动可靠闭合)
      ③自主进化=定案(本季度新增净采纳率)
      ④越懂你=过渡(认知发现数·通往预测准确率的必要数据积累)
      ②越用越好用=过渡(免疫命中/有效抗体·待双池)
  - 数据源=系统真实状态快照（settings实际/真实免疫命中/实际已落盘变更）·禁止AI自声明事件日志作指标源（Agent B前置3）

v0.4（2026-08-22·你定案·第一性原理·时间框架统一自然日历 + 口径精化）：
  - ④越懂你 compute_cogdiscover_growth 由"滑动30天 mtime 窗口"改为"按自然月归当月"
    （文件名 YYYY-MM-DD- 前缀；mtime=改动时间≠发生时间·历史改会虚高·实测 7月39/8月10 → 7月28/8月9）
  - 输出 current_month/count/days_left_in_month/by_month；兼容旧字段 actual_new_30d（值=当月数）
  - 定案口径仍=预测准确率(S815)，此过渡口径 evidence=🟡部分
  - ①全自动化 compute_auto_rate 口径精化：旧=近N天日志文件数/总文件数（只能证"日志存在"·1.0虚荣近似·你点名砍）
    → 新=returncode==0 自动审计成功占比（能证"自动闭合可靠运行"·愿景①真义）；note 同步更新
  - ②越用越好用 立过渡基线：免疫命中/反哺🛡抗体（同池·成长箱·不硬凑）·evidence 🟡；定案=漏触发修复率待两池统一
  - ③自主进化 立挑战线（2026-08-22 再定·净采纳率≥60%）：compute_evolution_events 返回 dict{total_events,adopted,adoption_rate}；
    adopted=有效抗体条目(^-🛡·内化免疫规则=真被采纳进系统)；adoption_rate=被采纳/事件；
    challenge=adoption_rate·target=0.60·当前 14/23=61%🟢；被采纳数(累计存量)不用作季度目标(无牵引)

v0.2（2026-08-21·愿景仪表盘定案落地·皮叔拍板第一性原理）：
  - 核心健康指标 = 调节回路活跃度（测"恒温器工作状态"非"当前温度"——系统之美卡3/工程控制论卡5李雅普诺夫）
  - 四方向 health 全算 + 证据档位（🟢实测/🟡部分/🔴无证据——C-016 无证据不评分·防自评满分作弊 C-040）
v0.3（2026-08-22·愿景仪表盘 v3 峰终体验）：
  - 新增 closed_loop 闭环流字段（检测DRIFT/修正WorkBuddy行/免疫命中/抗体🛡+近7日逐日趋势）
  - overall_health 已废弃（2026-08-22·你裁定"分数全去掉"·虚荣指标·面板改显示证据档位+原生数据）
  - 越懂你 = 预测准确率口径（立场卡 S815 测效用非记录量·当前以认知发现数过渡·待精化）
  - closed_loop 闭环流数据（v0.3·2026-08-21 峰终体验定案）：
      detected   = 本周 DRIFT 检出数（platform_adaptation_check.log）
      fixed      = 本周变更日志 WorkBuddy 行数（修正完成近似）
      immune     = 本周免疫复发记录.md 命中行数（免疫拦截）
      antibodies = 有效抗体条目 = 规范反哺日志.md 行首 `- 🛡 **复发检测条件**` 数（与②越用越好用 fanbu_antibodies 同口径·单一事实源）
      trend_7d   = 近7日逐日三环流量（结构性基线·从原始日志重算·不靠快照积累）

四方向指标（对照愿景 SSOT 00-宪法愿景.md）：
  ① 全自动化率   = 本周期自动审计事件 / 总会话事件（来源：route_audit_*.log 计数）
  ② 越用越好用   = 路由命中趋势（来源：route_audit 命中行；趋势=近期/早期比）
  ③ 自主自动进化 = 本周期反哺+抗体事件数（来源：规范反哺日志🛡条件数 + 免疫复发记录命中数）
  ④ 越用越懂使用者 = 预测准确率（来源：路由命中率·过渡口径）

设计原则（跨工具中立·守 Hook 三纪律·失败放行）：
  - 任一数据源读不到 → 该指标记 null + 证据档位=🔴无证据（N/A 由脚本产出，AI 不编造降级值）
  - 任何未捕获异常 → 写错误日志 + 产空 JSON + exit 0（绝不卡主流程）
  - 仅写 evolution_deviation_*.json 到系统日志目录，不拦截、不改其他文件

跨工具中立（脚本哲学 §二·五）：本脚本是公共设施，住 [记忆共享中心]/脚本中心/，
各工具 hook（Hermes on_session_end / WorkBuddy Stop）只调用不拥有。
"""

import os
import sys
import json
import glob
import re
import io
from datetime import datetime, timedelta

MC = os.path.expanduser("[记忆共享中心]")
BASE = MC  # 2026-10-07 根治：v0.4 岗位3并入因 BASE 未定义 NameError 被吞，detected 假零五周
SYSLOG = os.path.join(MC, "开发工具/logs/runtime")
SSOT_VISION = os.path.join(
    MC, "记忆蓝图/00_系统总览/五层记忆系统设计哲学/00-宪法愿景.md"
)
FANBU_LOG = os.path.join(MC, "成长箱/experience/规范反哺日志.md")
RECUR_LOG = os.path.join(MC, "成长箱/免疫复发记录.md")
COGDISCOVER = os.path.join(MC, "最伟大的我/认知发现")
GUARD_DIR = os.path.join(MC, "开发工具/changelog-guard")
DEV_TOOLS = os.path.join(MC, "开发工具")
PLATFORM_LOG = os.path.join(MC, "开发工具/logs/platform_adaptation_check.log")
CHANGELOG = os.path.join(MC, "变更日志.md")

# 理想态阈值（可配置常量·非内联真相；愿景文件是方向真相源，此处只放量化目标）
TARGET = {
    "auto_rate": 0.95,        # ①全自动化率目标 ≥95%
    "evolution_events": 3,    # ③自主进化事件/周期 目标 ≥3（反哺+抗体）
    "cogdiscover_growth": 1,  # ④认知发现新增/周期 目标 ≥1（过渡口径）
    "regulator_active": 1,    # ★调节回路活跃度目标 ≥1（本周有检测+修正即健康）
    "better_baseline": 0.8,   # ②漏触发修复基线 目标 ≥80%（免疫命中/有效抗体）
}


def _compute_immune_join_rate():
    """②免疫池↔抗体池 join 率（v0.6 重写 2026-10-07 野根根治轮·教训已入 01-通用规范§二·三十）。

    旧实现病：读侧自抽文本（split("|")[3] 位置错位+命令含管道被切），与写侧
    （growth_box_check.sh 经 antibody_gate.extract_antibodies 生成的抗体池）两把
    尺子不同源；路径/措辞演化后静默塌陷 81%→8%，且只扫反哺单载体（N0 扫描域
    半缺——抗体真身跨双载体：反哺日志+learnings 晋升条目）。
    根治=读侧复用写侧同一提取器（S922：副本必须指向真源⛔不手抄副本），
    join 主键=抗体标题 label（命中行第3段即写侧当池原名照抄），副键=命令深归一。
    返回 dict{rate,rows,pool,uncovered_forms}；源缺/失败返回 None（fail-open⛔不编造）。
    """
    try:
        sys.path.insert(0, os.path.join(MC, "技能配置/growth-box/scripts"))
        import antibody_gate as _ag
        pool = []
        for _p in _ag.default_sources():
            pool.extend(_ag.extract_antibodies(_p))
        if not pool:
            return None
        def norm(s):
            return re.sub(r"（.*?）|\s", "", s or "").lower()
        labels = {norm(lb) for _l, _c, lb in pool if lb}
        cmds = {norm(c) for _l, c, _lb in pool if c and len(c) > 15}
        rows = []
        with open(RECUR_LOG, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "命中" not in line or "|" not in line:
                    continue
                parts = line.split("|")
                head = parts[0].lstrip(" -").strip()
                if not re.match(r"20\d\d-\d\d-\d\d", head):
                    continue
                lb = parts[2].strip() if len(parts) > 2 else ""
                rem = "|".join(parts[3:]) if len(parts) > 3 else ""
                rows.append((lb, rem, head[:10]))
        if not rows:
            return None
        matched, uncovered = 0, {}
        form_rows = {}   # 形态 -> [行数, 末次命中日]（10-07 终审轮·活跃口径：退役后停跳的死账不再压分母）
        for lb, rem, dte in rows:
            n = norm(lb)
            ok = bool(n) and (n in labels or any(n in a or a in n for a in labels if a))
            if not ok:
                c = norm(rem)
                ok = bool(c) and any(c in x or x in c for x in cmds)
            if ok:
                matched += 1
            else:
                uncovered[n or "?"] = uncovered.get(n or "?", 0) + 1
            fr = form_rows.setdefault(n or "?", [0, ""])
            fr[0] += 1
            if dte > fr[1]:
                fr[1] = dte
        cutoff14 = (datetime.now() - __import__("datetime").timedelta(days=14)).strftime("%Y-%m-%d")
        act_rows = sum(v[0] for v in form_rows.values() if v[1] >= cutoff14)
        act_match = sum(1 for lb, rem, dte in rows
                        if form_rows.get(norm(lb) or "?", [0, ""])[1] >= cutoff14
                        and (norm(lb) in labels or any(norm(lb) in x or x in norm(lb) for x in labels if x)))
        rate_active = (round(act_match / act_rows, 3) if act_rows else None)
        return {"rate": round(matched / len(rows), 3), "rows": len(rows),
                "pool": len(pool), "uncovered_forms": len(uncovered),
                "rate_active": rate_active, "rows_active": act_rows}
    except Exception:
        return None


# ④越懂你 预测准率晋级阈值：需「预测 vs 实际」成对样本 ≥此数 → 判据显示"就绪"（你裁定·仅当前网页）
PRED_SAMPLE_THRESHOLD = 30


def _count_prediction_pairs():
    """④越懂你 预测准确率数据源探测：route_audit 日志里是否存在「预测 vs 实际」成对标签。

    当前 route_audit 只有 script/returncode（守卫运行记录·无预测语义），故应返回 None(数据源未建立)。
    若未来日志加入预测/命中对比字段，此函数统计其对数——晋级判据由是否探测到样本决定。
    """
    try:
        logs = glob.glob(os.path.join(SYSLOG, "route_audit_*.log"))
        if not logs:
            return None
        pairs = 0
        import re as _re
        for lp in logs[-50:]:
            try:
                with open(lp, encoding="utf-8") as f:
                    txt = f.read()
                if _re.search(r"predicted:|actual:|命中:|预测:", txt):
                    pairs += 1
            except Exception:
                continue
        # curl 当前无预测标签：仅当确实探测到成对标签才返回 >0，否则 None=没建立
        return pairs if pairs > 0 else None
    except Exception:
        return None


def _safe_count(path_glob=None, path=None, grep_pattern=None):
    """安全计数：glob文件数 / 单文件行数 / grep命中数。失败返回 None（N/A）。"""
    try:
        if path_glob:
            return len(glob.glob(path_glob))
        if path and grep_pattern:
            import subprocess
            r = subprocess.run(
                ["grep", "-c", grep_pattern, path],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                return int(r.stdout.strip() or 0)
            return 0
    except Exception:
        return None
    return None


# 口径切换点=B埋点误标修复上线时刻（此前 audit_search_kb/platform_adaptation_check 的
# hook 调用被硬编码记为 manual·16+8 条假 manual·不可作分母。历史行不回改·统计侧排除）
AUTO_RATE_CUTOFF = "2026-08-23T18:15:00+08:00"

def compute_auto_rate(window_days=30):
    """① 全自动化率（v2 口径切换 2026-08-23·你条件授权执行）：近30天 guard_invocations jsonl 中
    trigger_source==hook_auto 事件占比——愿景①真义=「机制自动运转，不依赖人记得」，触发来源占比
    直接测这个；旧 returncode 口径测的是「自动跑时闭合可靠」（可靠性≠自动化程度），降为对照列。
    诚实边界：覆盖面=pre-commit链/fswatch/launchd/三高频守卫自埋点（env GUARD_TRIGGER_SOURCE 检测·
    挂载守卫默认 hook_auto·离线守卫默认 manual），其余守卫的手动调用不可见→分母偏小=读数偏乐观；
    切换点 AUTO_RATE_CUTOFF 前的历史行含误标，机械排除不回改（append-only 纪律）。

    第一性原理（2026-08-22 定·2026-09-03 童灵口径修正）：
    v0.4旧口径=近N天日志文件数/总文件数——只证明"审计日志文件存在"，1.0是虚荣近似（你已点名要砍）。
    v0.5过渡口径=route_audit returncode==0 审计成功占比——测的是"自动跑时闭合可靠"（可靠性≠自动化程度），已降为对照列 compute_auto_rate_legacy。
    v2定口径（2026-08-23切换）=hook_auto 触发占比——愿景①真义=「机制自动运转，不依赖人记得」，触发来源占比直接测它。
    ⚠️ 诚实边界（2026-09-03童灵裁决）：当前为🟡过程代理，非定案——覆盖面仅4/11平台，其余守卫手动调用不可见→分母偏小=读数偏乐观；
    定案需满足：①覆盖面≥8/11 ②手动调用埋点可见 ③稳定3个周期。自动闭环率（hook_auto且exit==0）需先补exit码埋点（当前99.7%记录无exit字段），作为下一阶段目标。
    """
    try:
        import json as _json
        files = sorted(glob.glob(os.path.join(SYSLOG, "guard_invocations_*.jsonl")))
        if not files:
            return None
        cutoff = AUTO_RATE_CUTOFF
        total = hook = 0
        for fp in files:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = _json.loads(line)
                    except Exception:
                        continue
                    if str(r.get("ts", "")) < cutoff:
                        continue  # 切换点前数据含 hook 调用误标 manual·不作分母（append-only 不回改历史）
                    total += 1
                    if r.get("trigger_source") == "hook_auto":
                        hook += 1
        if total == 0:
            return None
        return round(hook / total, 3)
    except Exception:
        return None


def compute_auto_rate_legacy():
    """①对照列（一周期后撤·2026-08-23 v2）：route_audit returncode==0 审计成功占比（v0.4 旧口径）。
    保留原因：新口径（hook_auto 占比）上线初期防盲区断崖——两读数并跑一个周期，背离过大即报警查因。"""
    try:
        import re
        logs = glob.glob(os.path.join(SYSLOG, "route_audit_*.log"))
        if not logs:
            return None
        returncode_ok = 0
        for lp in logs:
            try:
                with open(lp, encoding="utf-8") as f:
                    txt = f.read()
                m = re.search(r"returncode:\s*(-?\d+)", txt)
                if m and int(m.group(1)) == 0:
                    returncode_ok += 1
            except Exception:
                pass
        return round(returncode_ok / len(logs), 3)
    except Exception:
        return None


def compute_auto_closure_rate():
    """①第二指标（2026-09-03童灵·补exit码埋点后新增）：自动闭环率 = hook_auto且exit==0事件数 ÷ hook_auto总事件数。
    与自动触发占比（第一指标）正交：触发占比测"多少事是自动做的"，闭环率测"自动做的事有多少成功闭环"。
    诚实边界：仅统计有exit字段的记录（2026-09-03前99.7%记录无exit字段），有exit字段的hook_auto记录<10条时返回None（数据积累中）。
    定案条件：exit码埋点全覆盖+稳定3个周期。
    """
    try:
        import json as _json
        files = sorted(glob.glob(os.path.join(SYSLOG, "guard_invocations_*.jsonl")))
        if not files:
            return None
        cutoff = AUTO_RATE_CUTOFF
        hook_total = 0  # 有exit字段的hook_auto记录数
        hook_closed = 0  # hook_auto且exit==0的记录数
        for fp in files:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = _json.loads(line)
                    except Exception:
                        continue
                    if str(r.get("ts", "")) < cutoff:
                        continue
                    if r.get("trigger_source") != "hook_auto":
                        continue
                    if "exit" not in r:
                        continue  # 仅统计有exit字段的记录
                    hook_total += 1
                    if r.get("exit") == 0:
                        hook_closed += 1
        if hook_total < 10:
            return None  # 数据积累中，样本不足不输出
        return round(hook_closed / hook_total, 3)
    except Exception:
        return None


def compute_guard_coverage():
    """①覆盖面（2026-09-03童灵·实事求是根治）：机械计算有guard_invocations埋点的守卫数量。
    原设计硬编码"4/11"是估算不准确——实盘核实有埋点的真实守卫是5个（排除测试用test_guard），
    总守卫数量远不止11个（开发工具目录13个guard脚本+launchd 7个定时守卫）。
    最优处理：不硬编码总守卫数（定义模糊·易过时），只机械计算"有埋点的守卫数量"作为覆盖面分子，
    定案条件改为"有埋点守卫数≥8"（原"8/11"的分子部分，分母因定义模糊废除）。
    返回：{"instrumented": N, "instrumented_list": [...], "note": "..."}
    """
    try:
        import json as _json
        files = sorted(glob.glob(os.path.join(SYSLOG, "guard_invocations_*.jsonl")))
        if not files:
            return {"instrumented": 0, "instrumented_list": [], "note": "无guard_invocations数据"}
        cutoff = AUTO_RATE_CUTOFF
        guards = set()
        for fp in files:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = _json.loads(line)
                    except Exception:
                        continue
                    if str(r.get("ts", "")) < cutoff:
                        continue
                    g = r.get("guard", "")
                    if g and g != "test_guard":  # 排除测试用守卫
                        guards.add(g)
        return {
            "instrumented": len(guards),
            "instrumented_list": sorted(guards),
            "note": "机械统计guard_invocations中出现过的不同守卫数（排除test_guard）·总守卫数因定义模糊不硬编码·定案条件=有埋点守卫数≥8",
        }
    except Exception:
        return {"instrumented": 0, "instrumented_list": [], "note": "计算异常"}


def compute_evolution_events():
    """③ 自主自动进化（本季度新增口径 v0.5·你愿景裁定 2026-08-22）：
    - 事件总数 = 本季度反哺块数（提过多少条进化提案）
    - 被采纳数 = 本季度新增有效抗体块数（^-🛡复发检测条件·内化成免疫规则的机制——真被采纳进系统）
    - 采纳率 = 本季度新增被采纳 / 本季度总提案（防累计存量无牵引·测"本季度真内化几个新机制"）

    第一性原理（2026-08-22·你定案·愿景③「自主自动进化」真义=机制被采纳进系统）：
    v0.5 改「累计存量」口径（adopted=全部抗体累计 14/23=61%·永远达标无牵引）→「本季度新增」：
    累计抗体是历史遗产，拿它当季目标永远"已达标"；本季度新增=这季度真内化了几个新机制，
    有牵引·贴进化本义。反哺块按 📅 日期机械归本季（自然季·非滚动窗口），带 🛡 才算被采纳。
    """
    import re
    try:
        if not os.path.isfile(FANBU_LOG):
            return None
        src = open(FANBU_LOG, encoding="utf-8").read()
        now = datetime.now()
        # 自然季边界（机械推导·不写死·跨年自动进位）
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        q_start = datetime(now.year, q_start_month, 1)
        if q_start_month == 10:
            q_end = datetime(now.year + 1, 1, 1)
        else:
            q_end = datetime(now.year, q_start_month + 3, 1)

        blocks = re.split(r"\n(?=### 反哺：)", src)
        total = 0        # 本季度提案数
        adopted = 0      # 本季度新增被采纳（带🛡复发检测条件=内化成免疫规则=真被采纳）
        for b in blocks:
            if not b.lstrip().startswith("### 反哺："):
                continue
            d = re.search(r"📅 \*\*日期\*\*：(\d{4}-\d{2}-\d{2})", b)
            if not d:
                continue
            dt = datetime.strptime(d.group(1), "%Y-%m-%d")
            if not (q_start <= dt < q_end):
                continue
            total += 1
            if "🛡 **复发检测条件**" in b:
                adopted += 1
    except Exception:
        return None

    return {
        "total_events": total,
        "adopted": adopted,
        "adoption_rate": round(adopted / total, 3) if total else None,
        "quarter": f"{now.year}-Q{(now.month - 1) // 3 + 1}",
    }


def read_twin_eval():
    """v0.6 新增：读数字分身 Step2 盲评报告，返回④定案仪器当前读数。
    数据源=数字分身/steps/step2-report.md(+step2.6-report.md 状态行)。
    解析失败/缺文件一律返回 None，消费方回落旧口径——宁可少一个读数，不要假读数。
    ⚠️ 该仪器自设纪律(step2.6-report L46)：三轮判卷同一会话·你抽审前 100% 不作数——
    此处只搬运读数与状态，⛔不替你签收，state 保持过渡。"""
    twin_dir = os.path.join(MC, "数字分身", "steps")
    rep = os.path.join(twin_dir, "step2-report.md")
    rep26 = os.path.join(twin_dir, "step2.6-report.md")
    if not os.path.exists(rep):
        return None
    try:
        txt = io.open(rep, encoding="utf-8").read()
        m = re.search(u"\u603b\u4e00\u81f4\u7387.*?\\*\\*([\\d.]+)%\\*\\*(\uff08[\\d./]+\uff09)", txt)
        mf = re.search(u"\u4e8b\u5b9e\u5c42\u4e00\u81f4\u7387.*?\\*\\*([\\d.]+)%\\*\\*", txt)
        ms = re.search(u"\u98ce\u683c\u5c42\u4e00\u81f4\u7387.*?\\*\\*([\\d.]+)%\\*\\*", txt)
        if not m:
            return None
        out = {
            "total_agreement_pct": float(m.group(1)),
            "fraction": m.group(2),
            "fact_layer_pct": (float(mf.group(1)) if mf else None),
            "style_layer_pct": (float(ms.group(1)) if ms else None),
            "rounds": 3,
            "gate": None,
            "verdict_rule": None,
            "source": u"\u6570\u5b57\u5206\u8eab/steps/step2-report.md",
        }
        if os.path.exists(rep26):
            t26 = io.open(rep26, encoding="utf-8").read()
            if u"\u95f8\u95e8\u901a\u8fc7" in t26:
                out["gate"] = u"\u6280\u672f\u95f8\u95e8\u8fc7(step2.6)"
            if u"\u4e0d\u4f5c\u6570" in t26:
                out["verdict_rule"] = u"\u672a\u62bd\u5ba1\u524d100%\u4e0d\u4f5c\u6570"
        rep28 = os.path.join(twin_dir, "step2.8-report.md")
        vpath = os.path.join(twin_dir, "step2.7-verdict.md")
        if os.path.exists(rep28):
            t28 = io.open(rep28, encoding="utf-8").read()
            mf28 = re.search(r"\*\*事实层一致率\*\* \| \*\*([\d.]+)%\*\*", t28)
            ms28 = re.search(r"\*\*风格层一致率\*\* \| \*\*([\d.]+)%\*\*", t28)
            me28 = re.search(r"升级纪律遵守率 \| \*\*([\d/]+)\*\*", t28)
            if mf28:
                out["fact_layer_pct"] = float(mf28.group(1))
                out["style_layer_pct"] = (float(ms28.group(1)) if ms28 else None)
                out["escalation_discipline"] = (me28.group(1) if me28 else None)
                out["rounds"] = u"重测v1.1.0(step2.8)"
                out["source"] = u"数字分身/steps/step2.8-report.md"
        if os.path.exists(vpath):
            out["verdict"] = u"你抽审认可(五条2026-08-21+争议裁定2026-08-23)"
        return out
    except Exception:
        return None

def compute_cogdiscover_growth(window_days=30):
    """④ 越用越懂使用者（过渡口径）：按自然月统计当月发生的认知发现条数。

    v0.4 改造（第一性原理·你定案 2026-08-22）：
    - 时间框架与自然季度框定一致（季度=自然月拼装），废弃滑动30天窗口。
    - "发生"按文件名日期前缀 YYYY-MM-DD- 归当月（非 mtime：mtime=改动时间≠发生时间）。
    - 返回 dict：{current_month, count, days_left_in_month, by_month}，
      兼容旧消费方 actual_new_30d 字段保留（值=当月数）。
    - 定案口径仍为预测准确率（S815 测效用），此过渡口径 evidence=🟡部分。
    """
    try:
        import re
        from collections import defaultdict
        if not os.path.isdir(COGDISCOVER):
            return None
        now = datetime.now()
        ym_key = (now.year, now.month)
        # 本月剩余天数（自然月边界·机械算）
        # 2026-09-27 童灵根治：replace 会保留当前时分秒——"剩 N 天"按 18:32→次日同刻算了整天，归零到自然月边界 00:00
        if now.month == 12:
            nxt = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            nxt = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        days_left = (nxt - now).days
        by_month = defaultdict(int)
        cur_count = 0
        for fp in glob.glob(os.path.join(COGDISCOVER, "*.md")):
            base = os.path.basename(fp)
            m = re.match(r"^(\d{4})-(\d{2})-", base)
            if not m:
                continue
            y, mo = int(m.group(1)), int(m.group(2))
            by_month[(y, mo)] += 1
            if (y, mo) == ym_key:
                cur_count += 1
        return {
            "current_month": f"{now.year}-{now.month:02d}",
            "count": cur_count,
            "days_left_in_month": days_left,
            "by_month": {f"{k[0]}-{k[1]:02d}": v for k, v in sorted(by_month.items())},
        }
    except Exception:
        return None


def compute_closed_loop(window_days=7):
    """闭环流数据（v0.3·峰终体验定案·检测→修正→免疫→接近目标）。

    全部从原始留痕逐日重算（结构性基线·数学之美卡6：设计结构让数据自动回答），
    不依赖快照积累——三环数据源各有日期戳，趋势=近7日逐日计数。
    任一数据源读不到 → 该环节记 None（N/A 由脚本产出·AI 不编造）。
    """
    import re
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() - timedelta(days=window_days - 1)).strftime("%Y-%m-%d")
    det_by_day, fix_by_day, imm_by_day = {}, {}, {}

    # 检测：platform_adaptation_check.log [DRIFT] 行（时间戳前缀）
    detected = None
    try:
        with open(PLATFORM_LOG, encoding="utf-8") as f:
            for line in f:
                if "[DRIFT]" in line and re.match(r"\d{4}-\d{2}-\d{2}", line):
                    d = line[:10]
                    if cutoff <= d <= today:
                        det_by_day[d] = det_by_day.get(d, 0) + 1
        detected = sum(det_by_day.values())
    except Exception:
        detected = None

    # 检测④（v0.4·2026-08-29）：岗位3「声明-实盘对账官」检出（steps/position3-audit-log.jsonl）
    # red=脱钩 yellow=悬置——对账检出并入 detected 总数（S847 独立审查：读 jsonl 机械计数·非手填）
    try:
        _p3log = os.path.join(BASE, "数字分身/steps/position3-audit-log.jsonl")
        if os.path.exists(_p3log):
            _p3_det = 0
            with open(_p3log, encoding="utf-8") as f:
                for _line in f:
                    try:
                        _r = json.loads(_line)
                        if cutoff <= str(_r.get("ts", ""))[:10] <= today:
                            _p3_det += int(_r.get("red", 0)) + int(_r.get("yellow", 0))
                    except Exception:
                        pass
            detected = _p3_det if detected is None else detected + _p3_det
    except Exception:
        pass  # 岗位3源缺失不阻塞既有闭环读数

    # 修正：变更日志本周 WorkBuddy 行（与 regulator 口径同源）
    fixed = None
    try:
        with open(CHANGELOG, encoding="utf-8") as f:
            for line in f:
                if line.startswith("| 20") and "WorkBuddy" in line:
                    parts = line.split("|")
                    if len(parts) > 1:
                        d = parts[1].strip()
                        if cutoff <= d <= today:
                            fix_by_day[d] = fix_by_day.get(d, 0) + 1
        fixed = sum(fix_by_day.values())
    except Exception:
        fixed = None

    # 免疫：免疫复发记录.md「命中」行（行首日期戳）
    immune = None
    try:
        _hit_dates = []
        with open(RECUR_LOG, encoding="utf-8") as f:
            for line in f:
                if "命中" not in line:
                    continue
                m = re.search(r"(\d{4}-\d{2}-\d{2})", line[:30])
                if not m:
                    continue
                _hit_dates.append(m.group(1))
                if cutoff <= m.group(1) <= today:
                    imm_by_day[m.group(1)] = imm_by_day.get(m.group(1), 0) + 1
        immune = sum(imm_by_day.values())
        # 累计命中与末次命中日期（不受本周窗口限制）——供面板呈现免疫环节真实静默时长
        # v0.4 增：immune=本周窗口(可能为0)，immune_total=累计，immune_last_date=末次命中日
        immune_total = len(_hit_dates)
        immune_last_date = max(_hit_dates) if _hit_dates else None
    except Exception:
        immune = None
        immune_total = None
        immune_last_date = None

    # 抗体：有效抗体条目（行首 `- 🛡 **复发检测条件**`·与②越用越好用 fanbu_antibodies 同口径）
    # 口径统一：抗体数=系统内化了几条防复发规则（行首精确·裸🛡/正文引用不算）——单一事实源 allowlist
    antibodies = _safe_count(grep_pattern=r"^\- 🛡 \*\*复发检测条件\*\*", path=FANBU_LOG)

    # 近7日逐日趋势（含今天·缺数日=0：结构性基线从今天自动积累）
    trend = []
    for i in range(window_days - 1, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        trend.append({
            "date": d[-5:],
            "detected": det_by_day.get(d, 0),
            "fixed": fix_by_day.get(d, 0),
            "immune": imm_by_day.get(d, 0),
        })

    return {
        "detected": detected,
        "fixed": fixed,
        "immune": immune,
        "immune_total": immune_total,
        "immune_last_date": immune_last_date,
        "antibodies": antibodies,
        "trend_7d": trend,
        "pending": (detected - fixed if detected is not None and fixed is not None and detected > fixed else 0),
        "sources": {
            "detected": "开发工具/logs/platform_adaptation_check.log [DRIFT] + 数字分身/steps/position3-audit-log.jsonl（岗位3对账·v0.4 并入）",
            "fixed": "变更日志.md WorkBuddy 行（本周）",
            "immune": "成长箱/免疫复发记录.md「命中」（本周）",
            "immune_last_date": "成长箱/免疫复发记录.md「命中」最大日期（累计口径·不受本周窗口限制）",
            "antibodies": "成长箱/experience/规范反哺日志.md 行首 `- 🛡 复发检测条件`（有效抗体条目·累计）",
        },
    }


def compute_regulator_activity(window_days=7):
    """★ 调节回路活跃度（v0.2 核心健康指标·测恒温器工作状态非当前温度）。
    口径（第一性原理·系统之美卡3恒温器/工程控制论卡5李雅普诺夫）：
      detected = 本周检测到的 drift/告警数（guard 相关日志中的 DRIFT/告警行）
      fixed    = 本周修正完成数（变更日志本周 WorkBuddy 行数近似）
    活跃度 = detected + fixed（>0 即调节回路在工作=系统在自主进化）
    返回 (本周值, 上周值)——上周对比让"26"有参照系（皮叔 2026-08-21 定）
    """
    def _count_detected(window_days):
        cnt = 0
        week_start = (datetime.now() - timedelta(days=window_days)).strftime("%Y-%m-%d")
        guard_logs = glob.glob(os.path.join(SYSLOG, "*.log"))
        for lp in guard_logs:
            if "platform_adaptation_check" in lp or "guard" in lp:
                try:
                    import subprocess
                    r = subprocess.run(["grep", "DRIFT", lp], capture_output=True, text=True)
                    if r.returncode == 0:
                        for line in r.stdout.splitlines():
                            if week_start <= line[:10]:
                                cnt += 1
                except Exception:
                    pass
        return cnt

    def _count_fixed(window_start, window_end):
        """变更日志中 [window_start, window_end] 区间 WorkBuddy 行数"""
        cnt = 0
        try:
            cl = os.path.join(MC, "变更日志.md")
            with open(cl, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("| 20") and "WorkBuddy" in line:
                        parts = line.split("|")
                        if len(parts) > 1:
                            d = parts[1].strip()
                            if window_start <= d <= window_end:
                                cnt += 1
        except Exception:
            pass
        return cnt

    today = datetime.now().strftime("%Y-%m-%d")
    # 本周: [今天-7, 今天]
    this_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week = _count_detected(7) + _count_fixed(this_start, today)
    # 上周: [今天-14, 今天-7]
    last_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    last_end = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    last_week = _count_detected(14) - _count_detected(7) + _count_fixed(last_start, last_end)
    return this_week, last_week


def evidence_level(actual, target):
    """证据档位（C-016 无证据不评分·防自评满分作弊 C-040）：
    🟢实测=有数据且达标 / 🟡部分=有数据未达标 / 🔴无证据=数据缺失"""
    if actual is None:
        return "🔴", None
    ratio = actual / target if target else 0
    health = round(min(ratio, 1.0), 3)
    if ratio >= 1.0:
        return "🟢", health
    return "🟡", health


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    out = {
        "date": today,
        "source": "evolution_deviation.py v0.8",
        "reference_model": "愿景四方向 (00-宪法愿景.md) + 调节回路活跃度 + 闭环流",
        "directions": {},
    }

    # ★ 闭环流（v0.3·峰终体验峰值数据源：检测→修正→免疫→抗体）
    out["closed_loop"] = compute_closed_loop()

    # ★ 调节回路活跃度（核心健康指标）
    reg_pair = compute_regulator_activity()
    reg = reg_pair[0] if reg_pair else None
    reg_last = reg_pair[1] if reg_pair else None
    reg_ev, reg_health = evidence_level(reg, TARGET["regulator_active"])
    out["directions"]["regulator_activity"] = {
        "actual": reg,
        "last_week": reg_last,
        "delta": (reg - reg_last if reg is not None and reg_last is not None else None),
        "target": TARGET["regulator_active"],
        "deviation": (reg - TARGET["regulator_active"] if reg is not None else None),
        "evidence": reg_ev,
        "note": "调节回路活跃度=检测drift数+修正完成数(恒温器工作状态·系统之美卡3/工程控制论卡5)·含上周对比",
    }

    # ① 全自动化率（v2口径：hook_auto触发占比·2026-08-23切换·2026-09-03童灵裁决为🟡过程代理非定案）
    ar = compute_auto_rate()
    ar_leg = compute_auto_rate_legacy()
    ar_closure = compute_auto_closure_rate()  # 第二指标：自动闭环率（hook_auto且exit==0占比·2026-09-03童灵新增）
    ar_cov = compute_guard_coverage()  # 覆盖面（2026-09-03童灵实事求是根治：机械计算有埋点的守卫数，废除硬编码4/11）
    ar_use = ar if ar is not None else ar_leg  # 新口径无数据时回退旧口径（冷启动保护）
    ar_ev, ar_health = evidence_level(ar_use, TARGET["auto_rate"])
    # 分母构成（透明度提升·2026-09-03童灵裁决）：统计切换点后总事件数、hook_auto数、manual数
    ar_breakdown = None
    try:
        import json as _json
        _files = sorted(glob.glob(os.path.join(SYSLOG, "guard_invocations_*.jsonl")))
        if _files:
            _total = _hook = _manual = 0
            for _fp in _files:
                with open(_fp, encoding="utf-8") as _f:
                    for _line in _f:
                        _line = _line.strip()
                        if not _line: continue
                        try:
                            _r = _json.loads(_line)
                        except: continue
                        if str(_r.get("ts", "")) < AUTO_RATE_CUTOFF: continue
                        _total += 1
                        if _r.get("trigger_source") == "hook_auto": _hook += 1
                        elif _r.get("trigger_source") == "manual": _manual += 1
            if _total > 0:
                ar_breakdown = {"total": _total, "hook_auto": _hook, "manual": _manual,
                                 "other": _total - _hook - _manual,
                                 "hook_auto_pct": round(_hook / _total * 100, 1),
                                 "manual_pct": round(_manual / _total * 100, 1)}
    except Exception:
        pass
    out["directions"]["auto_rate"] = {
        "actual": ar_use,
        "auto_closure_rate": ar_closure,  # 第二指标：自动闭环率（hook_auto且exit==0占比·2026-09-03童灵新增·数据积累中可能为None）
        "coverage": ar_cov,  # 覆盖面（2026-09-03童灵实事求是根治：机械计算有埋点的守卫数，废除硬编码4/11）
        "legacy_route_audit_rate": ar_leg,  # 对照列·并跑一周期后撤（防新口径盲区断崖）
        "target": TARGET["auto_rate"],
        "deviation": (round(ar_use - TARGET["auto_rate"], 3) if ar_use is not None else None),
        "evidence": ar_ev,
        "state": "过程代理",  # 2026-09-03童灵裁决：覆盖面仅4/11+手动调用不可见→读数偏乐观，非定案；定案需覆盖面≥8/11+手动埋点可见+稳定3周期
        "breakdown": ar_breakdown,  # 2026-09-03童灵透明度提升：分母构成（total/hook_auto/manual/other）
        "note": ("全自动化率(v2口径·hook_auto事件占比·自2026-08-23T18:15切换点起算·切换点前含误标已排除)"
                 "·对照列=route_audit returncode旧口径(一周期)"
                 "·覆盖面=有guard_invocations埋点的守卫数（机械计算·见coverage字段·2026-09-03童灵实事求是根治：废除硬编码4/11）"
                 "·其余守卫手动调用不可见→分母偏小=读数偏乐观"
                 "·🟡过程代理非定案（2026-09-03童灵裁决）：定案需有埋点守卫数≥8+手动埋点可见+稳定3周期"),
    }

    # ③ 自主自动进化（本季度新增被采纳口径 v0.5·你愿景裁定）
    ev_info = compute_evolution_events()
    ev = ev_info["total_events"] if isinstance(ev_info, dict) else ev_info
    ev_ev, ev_health = evidence_level(ev, TARGET["evolution_events"])
    out["directions"]["autonomous_evolution"] = {
        "actual": ev,
        "target": TARGET["evolution_events"],
        "deviation": (ev - TARGET["evolution_events"] if ev is not None else None),
        "evidence": ev_ev,
        "adopted": (ev_info.get("adopted") if isinstance(ev_info, dict) else None),
        "adoption_rate": (ev_info.get("adoption_rate") if isinstance(ev_info, dict) else None),
        "quarter": (ev_info.get("quarter") if isinstance(ev_info, dict) else None),
        # 挑战线定案（2026-08-22·你愿景裁定·改本季度新增）：净采纳率≥60%——愿景③真义=机制被采纳进系统，
        # 是"质量"不是"数量"。v0.5 改"本季度新增被采纳/本季度总提案"：累计存量(全部抗体14)永远达标无牵引，
        # 本季度新增=这季度真内化了几个新机制，测"提的进化有多少真内化"，防"提一堆不落地"。
        "challenge": (ev_info.get("adoption_rate") if isinstance(ev_info, dict) else None),
        "challenge_target": 0.60,
        "challenge_unit": "rate",
        "state": "定案",  # 定案口径=本季度新增净采纳率
        "note": "季度={quarter}·本季提案数={total}·本季新增被采纳={adopted}(有效抗体内化=真进化)·净采纳率={rate} · 挑战线=净采纳率≥60%(本季度新增口径·防累计存量无牵引·测'这季度真内化几个新机制'·愿景③) ".format(
            quarter=ev_info.get("quarter"), total=ev_info.get("total_events"),
            adopted=ev_info.get("adopted"), rate=ev_info.get("adoption_rate")) if isinstance(ev_info, dict) else "",
    }

    # ④ 越用越懂使用者（过渡口径：认知发现数·按自然月）
    cg = compute_cogdiscover_growth()
    cg_count = cg["count"] if isinstance(cg, dict) else cg
    cg_days_left = cg.get("days_left_in_month") if isinstance(cg, dict) else None
    cg_by_month = cg.get("by_month") if isinstance(cg, dict) else None
    # 过渡口径 evidence 强制🟡：定案=预测准确率(S815)待路由数据积累，不随数量达标升🟢
    pred_pairs = _count_prediction_pairs()
    twin = read_twin_eval()
    # v0.7：④定案判定机械化——step2.7-verdict.md 在盘=你异质检验完成(五条08-21+争议08-23) → state=定案
    _verdict_on = bool(twin and isinstance(twin, dict) and twin.get("verdict"))
    cg_ev = "🟢" if _verdict_on else "🟡"  # 过渡期强制🟡；定案后交还面板机械判定
    # ④晋级判据（你裁定"样本数达标显就绪·仅当前网页"）：预测准确率需「预测 vs 实际」成对样本
    #   route_audit 当前只有 script/returncode 守卫运行记录、无预测标签 → 数据源未建立→诚实明说·不空承诺
    if pred_pairs is None:
        if twin and _verdict_on:
            knows_note = ("定案(2026-08-23你抽审认可)=数字分身盲评·{} · 事实层{}/风格层{}/升级纪律{} · §5.2-A双列换算方向10/10+校准FAIL×1(guard检出S048) · 口径=规格书内记忆保真·out-spec泛化未测 · 远期精化=预测准确率(预测标签未建)".format(
                twin.get("rounds"), twin.get("fact_layer_pct"), twin.get("style_layer_pct"),
                twin.get("escalation_discipline")))
        elif twin:
            knows_note = ("过渡=认知发现数{:.0f}条 · 定案仪器已建成=数字分身Step2盲评(3轮·总一致率{:.2f}% {}) · ⚠️{}(待你step2.7抽审) · 抽审通过后④转定案".format(
                cg_count if cg_count is not None else 0,
                twin["total_agreement_pct"], twin.get("fraction", ""),
                twin.get("verdict_rule") or ""))
        else:
            knows_note = ("过渡=认知发现数{:.0f}条·定案=预测准确率需「预测vs实际」成对样本·当前 route_audit 无预测标签(数据源未建立)·非等数据积累而是需先建预测标签".format(
                cg_count if cg_count is not None else 0))
    else:
        knows_note = ("过渡=认知发现数{:.0f}条·定案=预测准确率·预测样本{}条·待≥{}(样本达标显就绪)".format(
            cg_count if cg_count is not None else 0, pred_pairs, PRED_SAMPLE_THRESHOLD))
    out["directions"]["knows_user_better"] = {
        "actual": cg_count,
        "count": cg_count,  # 当月数（自然月归当月·文件名日期）
        "actual_new_30d": cg_count,  # 兼容旧消费方（值=当月数）
        "current_month": (cg.get("current_month") if isinstance(cg, dict) else None),
        "days_left_in_month": cg_days_left,
        "by_month": cg_by_month,
        "target": TARGET["cogdiscover_growth"],
        "deviation": (cg_count - TARGET["cogdiscover_growth"] if cg_count is not None else None),
        "evidence": cg_ev,
        "prediction_pairs": pred_pairs,
        "twin_eval": twin,
        "state": ("定案" if _verdict_on else "过渡"),  # v0.7：verdict文件在盘=异质检验完成→定案；否则维持过渡不冒充
        "note": knows_note,
    }

    # ② 越用越好用：晋级判定（v0.5·你裁定"定案=join率≥90%·仅当前网页"）
    #   定案=漏触发修复率：命中过的坑是否被抗体覆盖（两池可join=免疫闭环成立）
    #   机械判据：免疫记录命中命令 与 反哺抗体命令 的可join率 ≥ 90% → state=定案
    fanbu_ant = _safe_count(grep_pattern=r"^\- 🛡 \*\*复发检测条件\*\*", path=FANBU_LOG)
    # join v0.6：免疫命中数与 join 同源同径（带日期行·与闭环流 immune_total 口径一致·治三名字）
    jn = _compute_immune_join_rate()
    immune_hit = jn["rows"] if jn else _safe_count(grep_pattern="命中", path=RECUR_LOG)
    baseline = None
    if fanbu_ant is not None and immune_hit is not None and fanbu_ant:
        baseline = round(immune_hit / fanbu_ant, 3)
    route_count = _safe_count(path_glob=os.path.join(SYSLOG, "route_audit_*.log"))
    # join 率 = 免疫命中中有多少已被抗体（双载体池）覆盖→免疫闭环真实覆盖度
    join_rate = jn["rate"] if jn else None
    JOIN_THRESHOLD = 0.90  # 你裁定（2026-08-22）
    _ra = jn.get("rate_active") if jn else None
    join_gate = _ra if _ra is not None else join_rate  # 门槛判定切活跃口径（活跃行=0 时 _ra=None→回落全史并在 note 注明）
    if join_gate is not None and join_gate >= JOIN_THRESHOLD:
        better_state = "定案"
        better_ev = "🟢" if baseline is not None and baseline >= TARGET["better_baseline"] else "🟡"
        better_note = ("定案=漏触发修复率(活跃口径·近14天命中行)：join={:.0%}≥90%·免疫闭环成立·全史对照{:.0%}(死账系已退役形态历史命中)·过渡基线免疫/抗体={:.1f}倍".format(
            join_gate if join_gate is not None else 0, join_rate or 0,
            baseline if baseline is not None else 0))
    else:
        better_state = "过渡"
        better_ev = "🟡"
        joins_need = ("近14天活跃口径join={}·全史{:.0%}(死账{}行为已退役形态历史命中·不计覆盖缺口)·{}个形态未覆盖(双载体池{}条)".format(
            ("{:.0%}".format(_ra) if _ra is not None else "无活跃命中行"), join_rate,
            (jn["rows"] - jn.get("rows_active", 0)) if jn else 0, jn["uncovered_forms"], jn["pool"]) if join_rate is not None else "join率待算(数据源未读)")
        # 2026-09-27 童灵根治：note 带实跑三元组（命中/抗体/倍数）——原文案只有 join 率，OKR 卡看不出过渡读数实值
        better_note = "过渡读数=免疫 {}/抗体 {} = {:.1f} 倍(每抗体摊命中·低好方向) · 两池{} · 定案=漏触发修复率(需join≥90%)".format(
            immune_hit, fanbu_ant, baseline if baseline is not None else 0, joins_need)
    out["directions"]["gets_better"] = {
        "immune_hits": immune_hit,
        "fanbu_antibodies": fanbu_ant,
        "antibody_pool_dual": (jn["pool"] if jn else None),
        "join_uncovered_forms": (jn["uncovered_forms"] if jn else None),
        "join_rate_active": (jn.get("rate_active") if jn else None),
        "join_rows_active": (jn.get("rows_active") if jn else None),
        "transition_baseline": baseline,
        "join_rate": join_rate,
        "route_audit_total": route_count,
        "evidence": better_ev,
        "state": better_state,
        "note": better_note,
    }

    # ★ 整体健康度已废弃（2026-08-22·你裁定"分数全去掉"）：health/overall_health 是虚荣指标
    #   ——"自主进化"不是 0-1 达标分数，是"回路状态+趋势"。面板改显示证据档位+原生数据，
    #   不显示 health 分数。整体证据覆盖保留（evidence_coverage 非分数，描述有多少方向有证据）。
    coverage = 0
    scored_dirs = 0
    total_dirs = 0
    for d in out["directions"].values():
        total_dirs += 1
        if d.get("evidence") and d.get("evidence") != "🔴":
            scored_dirs += 1
    coverage = (scored_dirs / total_dirs) if total_dirs > 0 else 0
    out["evidence_coverage"] = "{}/{}".format(scored_dirs, total_dirs)
    out["overall_evidence"] = (
        "🟢" if coverage >= 0.8 else "🟡" if coverage >= 0.4 else "🔴"
    )
    out["note"] = (
        "健康度/整体分数已废弃(你裁定·虚荣指标)·面板改显示证据档位+原生数据·"
        "证据档位: 🟢实测/🟡部分/🔴无证据(C-016·防自评满分作弊C-040)"
    )

    # 写 JSON（失败放行）
    try:
        os.makedirs(SYSLOG, exist_ok=True)
        out_path = os.path.join(SYSLOG, f"evolution_deviation_{today}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"[evolution_deviation] 已产出 {out_path}")
    except Exception as exc:
        try:
            with open(os.path.join(SYSLOG, "evolution_deviation_errors.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {exc!r}\n")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

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