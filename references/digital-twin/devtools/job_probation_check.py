#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
童灵岗位试用期转正检查脚本
- 自动扫描试用期岗位，统计推翻率
- 试用期结束时自动输出转正评估报告
- 支持记录决策响应（--record）
- 符合愿景①全自动化（不需要人工统计推翻率）

用法：
  python3 job_probation_check.py --check          # 只检查试用期到期岗位，输出摘要
  python3 job_probation_check.py --report         # 输出所有试用期到期岗位的转正评估报告
  python3 job_probation_check.py --report --job JOB-003  # 输出指定岗位的转正评估报告
  python3 job_probation_check.py --record --job JOB-003 --decision-id JOB-003-20260908-001 --content "E9.2最终评估：反哺X写入规范Y" --response approved  # 记录一次决策响应
  python3 job_probation_check.py --stats          # 输出所有岗位的统计摘要

v1.9（2026-09-28·童灵收口）：stats/report 实时计算后把 stats 快照写回 JSON（读后写回·幂等·变了才写）——消 record 动作之外的台账数据修正（如 actor 修正）留下的过期缓存旁路假信号（JOB-004 实证：旁路直读 rejection_rate=100%·官方读数路径 calc_stats 实时重算本无恙）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import sys
import argparse
from datetime import datetime, timedelta

LEDGER_PATH = os.path.expanduser("~/[记忆共享中心]/数字分身/job_probation_ledger.json")
REJECTION_THRESHOLD = 15.0  # 推翻率阈值<15%可转正


def load_ledger():
    """加载台账文件"""
    if not os.path.exists(LEDGER_PATH):
        print(f"❌ 台账文件不存在：{LEDGER_PATH}")
        sys.exit(1)
    with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_ledger(ledger):
    """保存台账文件"""
    ledger['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(LEDGER_PATH, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, ensure_ascii=False, indent=2)


def calc_stats(job):
    """计算岗位统计数据"""
    decisions = job.get('decisions', [])
    total = len(decisions)
    approved = sum(1 for d in decisions if d.get('response') == 'approved')
    rejected = sum(1 for d in decisions if d.get('response') == 'rejected')
    modified = sum(1 for d in decisions if d.get('response') == 'modified')
    questioned = sum(1 for d in decisions if d.get('response') == 'questioned')
    
    # 推翻率 = (拒绝 + 修改 + 质疑) / 总数 * 100
    # v1.7（2026-09-23 口径根治·皮叔令「按符合愿景第一性原理最优处理」）：区分**谁做出的响应**——
    #   actor=ge（你推翻）计入推翻率；actor=self（审核岗**自查修正**，如闸3异体审挡回后自己改）不计入。
    # 病根：同一个 `modified` 值承载两种语义（你改 / 童灵自查改），混算致 JOB-004 首条即显
    #   「推翻率 100%」的假信号——而推翻率的用途是**衡量童灵判断被你推翻的频率**（质量信号），
    #   自己改自己不是质量信号。缺失 actor 字段的历史记录视为 ge（向后兼容·⛔不改写历史）。
    self_corrected = sum(1 for d in decisions
                         if d.get('response') in ('rejected', 'modified', 'questioned')
                         and d.get('actor') == 'self')
    non_approved = rejected + modified + questioned - self_corrected
    rejection_rate = (non_approved / total * 100) if total > 0 else 0.0

    return {
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'modified': modified,
        'questioned': questioned,
        'self_corrected': self_corrected,
        'rejection_rate': round(rejection_rate, 1)
    }


def refresh_stats_snapshot(job):
    """v1.9·stats快照读后写回（幂等）：实时算完与 JSON 内缓存比对，变了才更新。
    根因修：record 路径写回快照，但 record 之外的台账数据修正（如 actor 修正）会让
    快照过期——旁路直读 JSON 者复见假信号（JOB-004 实证 rejection_rate=100%）。
    官方读数路径（calc_stats 实时重算）本无恙；本函数让 stats/report 命令顺手自愈。"""
    fresh = calc_stats(job)
    if job.get('stats') != fresh:
        job['stats'] = fresh
        return True
    return False


def is_probation_expired(job):
    """检查试用期是否已满"""
    probation_end = job.get('probation_end', '')
    if not probation_end:
        return False
    try:
        end_date = datetime.strptime(probation_end, '%Y-%m-%d')
        return datetime.now() >= end_date
    except ValueError:
        return False


def get_conversion_recommendation(stats):
    """根据统计数据给出转正建议"""
    if stats['total'] == 0:
        return "⏳ 试用期内无决策记录，无法评估（建议延长试用期或人工评估）"
    if stats['rejection_rate'] < REJECTION_THRESHOLD:
        return f"✅ 建议转正（推翻率{stats['rejection_rate']}%<{REJECTION_THRESHOLD}%阈值）"
    else:
        return f"⚠️ 建议延长试用期或降级（推翻率{stats['rejection_rate']}%≥{REJECTION_THRESHOLD}%阈值）"


def print_report(job, job_id):
    """输出转正评估报告"""
    stats = calc_stats(job)
    recommendation = get_conversion_recommendation(stats)
    expired = is_probation_expired(job)
    
    print("=" * 60)
    print("📋 童灵岗位试用期转正评估报告")
    print("=" * 60)
    print(f"├─ 岗位编号：{job_id}")
    print(f"├─ 岗位名称：{job.get('job_name', '未知')}")
    print(f"├─ 所属系统：{job.get('system', '未知')}")
    print(f"├─ 授权等级：{job.get('authorization_level', '未知')}")
    print(f"├─ 试用期：{job.get('probation_start', '未知')} 至 {job.get('probation_end', '未知')}")
    print(f"├─ 试用期状态：{'🟡 试用期内' if not expired else '🔔 试用期已满（可转正评估）'}")
    print(f"├─ 决策总数：{stats['total']}次")
    print(f"├─ ✅通过：{stats['approved']}次")
    print(f"├─ ❌拒绝：{stats['rejected']}次")
    print(f"├─ 🔄修改：{stats['modified']}次")
    print(f"├─ ❓质疑：{stats['questioned']}次")
    print(f"├─ 推翻率：{stats['rejection_rate']}%（阈值<{REJECTION_THRESHOLD}%）")
    print(f"├─ 转正建议：{recommendation}")
    
    # 推翻明细
    rejected_decisions = [d for d in job.get('decisions', []) if d.get('response') in ['rejected', 'modified', 'questioned']]
    if rejected_decisions:
        print(f"├─ 推翻明细（{len(rejected_decisions)}次）：")
        for i, d in enumerate(rejected_decisions[:10], 1):  # 最多显示10条
            print(f"│  {i}. [{d.get('decision_id', '未知')}] {d.get('date', '未知')}")
            print(f"│     内容：{d.get('content', '未知')[:50]}...")
            print(f"│     响应：{d.get('response', '未知')}")
            if d.get('reason'):
                print(f"│     原因：{d.get('reason', '')[:50]}")
        if len(rejected_decisions) > 10:
            print(f"│  ... 还有{len(rejected_decisions)-10}条，详见台账文件")
    
    print(f"└─ 你决定：✅转正 / 🔄延长1个月 / ⬇️降级授权 / 🔴收回岗位")
    print("=" * 60)
    print()



BLOCKED_CARDS_PATH = os.path.expanduser("~/[记忆共享中心]/数字分身/steps/step3-blocked-cards.md")


def blocked_write(decision_id, text, path=None):
    """v1.8·被挡清单第三账（闸5）：rejected 决策的挡回条目由 record 原子落盘。
    根治=把"记得写被挡清单"从 AI 自觉改成动作产物（同 v1.6 双写同理·JOB-001 断链45条病灶）。
    幂等：同 decision_id 已在文件内则不重复追加。返回 True/False/None(文件不可用)。"""
    p = path or BLOCKED_CARDS_PATH
    try:
        if not os.path.isfile(p):
            return None
        with open(p, 'r', encoding='utf-8') as f:
            cur = f.read()
        if decision_id in cur:
            return True  # 幂等：已挡过不重复
        entry = f"\n<!-- {decision_id} ·record自动写入 -->\n{text.strip()}\n"
        with open(p, 'a', encoding='utf-8') as f:
            f.write(entry)
        return True
    except Exception:
        return False


def mirror_to_log(job_id, decision_id, content, response):
    """record 的单动作双写（v1.6·2026-09-22 双本账根治）。

    一次初审 = 台账一行 + 载体日志一行，把"两账齐"从约定（靠执行者记得）改成动作产物。
    落点判据：仅当该岗位在 job_audit_check.JOB_LOG_SOURCES 里登记了**恰好一个**实体文件才写；
    多载体岗位（如 JOB-003 三载体）不猜该落哪个 → 返回 None 保持现状，
    由对账的反向检测（日志有·台账无）兜底。
    幂等：decision_id 已在载体内则不重复追加（重跑安全）。
    ⛔不静默：写盘异常返回 False 让上层显形——静默失败正是被根治的那类病。
    恒真防御：本函数只补"日志侧"，对账仍双向查；手改 json 不入日志、日志有 ID 而台账无，
    两类仍会被抓，检测力未被双写消解。
    """
    try:
        from job_audit_check import JOB_LOG_SOURCES
    except Exception as e:
        print(f"   ⚠️ 对账模块不可导入（{e}）·跳过双写")
        return None
    sources = JOB_LOG_SOURCES.get(job_id) or []
    if len(sources) != 1 or not sources[0].is_file():
        return None
    path = sources[0]
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if decision_id in text:
            return True
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        head = "## record 自动落账（双写·含全串决策ID）"
        safe = " ".join(content[:80].split()).replace("|", "/")
        line = f"- {stamp} | {decision_id} | {response} | {safe} |"
        if head in text:
            new = text.rstrip("\n") + "\n" + line + "\n"
        else:
            new = text.rstrip("\n") + "\n\n" + head + "\n\n" + line + "\n"
        path.write_text(new, encoding="utf-8")
        return True
    except Exception as e:
        print(f"   🔴 双写落盘失败：{e}")
        return False


def record_decision(job_id, decision_id, content, response, reason='', actor='ge', blocked_text=''):
    """记录一次决策响应。

    v1.8（2026-09-23·皮叔问「拒绝数据能自动么」·Qoder CN）：rejected 决策新增第三账——
    `--blocked-text` 传入即原子写 step3-blocked-cards.md（闸5被挡可追溯，幂等按 decision_id）；
    rejected 缺文本=🔴显形"闸5欠账"不静默。根治"记得写被挡清单"靠自觉的旧病（同 v1.6 双写逻辑）。

    v1.7（2026-09-23 口径根治）：新增 `actor` —— 记录**谁做出的这个响应**
    （ge=你 / self=童灵审核中自查修正）。动机：`modified` 一个值承载两种语义
    （你改了童灵的判断 vs 童灵自己改自己），混算使"推翻率"这一**质量信号**失真
    （JOB-004 首条实证：闸3 自查修正被算成「推翻率 100%」）。缺省 ge＝向后兼容。
    """
    ledger = load_ledger()
    
    if job_id not in ledger.get('jobs', {}):
        print(f"❌ 岗位不存在：{job_id}")
        sys.exit(1)
    
    job = ledger['jobs'][job_id]
    
    # 检查决策ID是否已存在
    for d in job.get('decisions', []):
        if d.get('decision_id') == decision_id:
            print(f"⚠️ 决策ID已存在：{decision_id}，将更新响应")
            d['response'] = response
            d['actor'] = actor
            if reason:
                d['reason'] = reason
            save_ledger(ledger)
            mirror_to_log(job_id, decision_id, content, response)
            print(f"✅ 已更新决策响应：{decision_id} → {response}")
            return
    
    # 新增决策记录
    decision = {
        'decision_id': decision_id,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'content': content,
        'response': response,
        'reason': reason,
        'actor': actor
    }
    job.setdefault('decisions', []).append(decision)
    
    # 更新统计
    job['stats'] = calc_stats(job)
    
    save_ledger(ledger)
    mirror_ok = mirror_to_log(job_id, decision_id, content, response)
    print(f"✅ 已记录决策响应：{decision_id} → {response}")
    print(f"   岗位：{job_id} {job.get('job_name', '')}")
    print(f"   当前推翻率：{job['stats']['rejection_rate']}%")
    if mirror_ok is True:
        print("   🔗 双写完成：台账 + 载体日志（一次动作两账齐）")
    elif mirror_ok is False:
        print("   🔴 双写失败：台账已写·日志未落——对账将报缺日志，需重跑本命令")
    else:
        print("   ℹ️ 双写跳过（多载体/无载体岗位不猜落点·由对账反向检测兜底）")

    # v1.8 第三账：rejected → 被挡清单原子落盘（闸5·⛔靠执行者记得）
    if response == 'rejected':
        bt = blocked_text or ''
        if bt:
            bw = blocked_write(decision_id, bt)
            if bw is True:
                print("   🚫 第三账完成：被挡清单已落（闸5·幂等）")
            elif bw is False:
                print("   🔴 被挡清单写入失败——手工补录并修权限，对账不查此账故必须显形")
            else:
                print("   ⚠️ 被挡清单文件不存在·跳过（首张被挡卡由人工建文件后自动接管）")
        else:
            print("   🔴 rejected 但未传 --blocked-text = 闸5欠账（被挡无记录=单方面挡），请重跑补 --blocked-text")


def cmd_check(args):
    """检查试用期到期岗位"""
    ledger = load_ledger()
    expired_jobs = []
    probation_jobs = []
    
    for job_id, job in ledger.get('jobs', {}).items():
        if job.get('status') == 'probation':
            stats = calc_stats(job)
            if is_probation_expired(job):
                expired_jobs.append((job_id, job, stats))
            else:
                probation_jobs.append((job_id, job, stats))
    
    print("📊 童灵岗位试用期检查")
    print("=" * 50)
    
    if expired_jobs:
        print(f"🔔 试用期已满（{len(expired_jobs)}个岗位，可转正评估）：")
        for job_id, job, stats in expired_jobs:
            print(f"  - {job_id} {job.get('job_name', '')}：推翻率{stats['rejection_rate']}%（{stats['total']}次决策）")
        print()
        print("💡 运行 --report 输出转正评估报告")
    else:
        print("✅ 无试用期已满的岗位")
    
    if probation_jobs:
        print(f"🟡 试用期内（{len(probation_jobs)}个岗位）：")
        for job_id, job, stats in probation_jobs:
            days_left = (datetime.strptime(job.get('probation_end', '2099-12-31'), '%Y-%m-%d') - datetime.now()).days
            print(f"  - {job_id} {job.get('job_name', '')}：推翻率{stats['rejection_rate']}%，剩余{days_left}天")
    
    print("=" * 50)
    
    # exit code: 有试用期到期岗位返回1（信号语义，供launchd判断是否需要输出报告）
    if expired_jobs:
        sys.exit(1)
    else:
        sys.exit(0)


def cmd_report(args):
    """输出转正评估报告"""
    ledger = load_ledger()
    
    if args.job:
        if args.job not in ledger.get('jobs', {}):
            print(f"❌ 岗位不存在：{args.job}")
            sys.exit(1)
        job = ledger['jobs'][args.job]
        if refresh_stats_snapshot(job):
            save_ledger(ledger)
            print("🔄 stats快照读后写回：1个岗位已刷新（消过期缓存旁路假信号）")
        print_report(job, args.job)
    else:
        # 输出所有试用期到期岗位的报告
        expired_count = 0
        refreshed = []
        for job_id, job in ledger.get('jobs', {}).items():
            if job.get('status') == 'probation' and is_probation_expired(job):
                if refresh_stats_snapshot(job):
                    refreshed.append(job_id)
                print_report(job, job_id)
                expired_count += 1
        if refreshed:
            save_ledger(ledger)
            print(f"🔄 stats快照读后写回：{len(refreshed)}个岗位已刷新（{', '.join(refreshed)}）·消过期缓存旁路假信号")
        if expired_count == 0:
            print("✅ 无试用期已满的岗位，无需转正评估")
            print("💡 运行 --check 查看所有试用期岗位状态")


def cmd_stats(args):
    """输出所有岗位的统计摘要"""
    ledger = load_ledger()

    print("📊 童灵岗位统计摘要")
    print("=" * 60)
    print(f"{'岗位ID':<10} {'岗位名称':<15} {'状态':<8} {'决策数':<6} {'推翻率':<8} {'试用期结束'}")
    print("-" * 60)

    refreshed = []
    for job_id, job in ledger.get('jobs', {}).items():
        stats = calc_stats(job)
        if refresh_stats_snapshot(job):
            refreshed.append(job_id)
        status = job.get('status', '未知')
        status_icon = {'probation': '🟡试用', 'active': '🟢在岗', 'retired': '🔴收回', 'pending': '⏳待上岗'}.get(status, status)
        print(f"{job_id:<10} {job.get('job_name', '')[:12]:<15} {status_icon:<8} {stats['total']:<6} {stats['rejection_rate']}%{'':<3} {job.get('probation_end', 'N/A')}")

    print("=" * 60)
    if refreshed:
        save_ledger(ledger)
        print(f"🔄 stats快照读后写回：{len(refreshed)}个岗位已刷新（{', '.join(refreshed)}）·消过期缓存旁路假信号")


def main():
    parser = argparse.ArgumentParser(description='童灵岗位试用期转正检查脚本')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # --check
    subparsers.add_parser('check', help='检查试用期到期岗位')
    
    # --report
    report_parser = subparsers.add_parser('report', help='输出转正评估报告')
    report_parser.add_argument('--job', help='指定岗位ID（如JOB-003）')
    
    # --record
    record_parser = subparsers.add_parser('record', help='记录一次决策响应')
    record_parser.add_argument('--job', required=True, help='岗位ID（如JOB-003）')
    record_parser.add_argument('--decision-id', required=True, help='决策唯一ID（如JOB-003-20260908-001）')
    record_parser.add_argument('--content', required=True, help='决策内容')
    record_parser.add_argument('--response', required=True, choices=['approved', 'rejected', 'modified', 'questioned'], help='你的响应')
    record_parser.add_argument('--reason', default='', help='原因（可选）')
    record_parser.add_argument('--actor', default='ge', choices=['ge', 'self'],
                               help='响应主体：ge=你（计入推翻率）/ self=童灵自查修正（不计入·v1.7 口径根治）')
    record_parser.add_argument('--blocked-text', default='', help='rejected 时的被挡条正文（闸5第三账·缺则显形提醒）')

    
    # --stats
    subparsers.add_parser('stats', help='输出所有岗位的统计摘要')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        cmd_check(args)
    elif args.command == 'report':
        cmd_report(args)
    elif args.command == 'record':
        record_decision(args.job, args.decision_id, args.content, args.response, args.reason,
                        getattr(args, 'actor', 'ge'), getattr(args, 'blocked_text', ''))
    elif args.command == 'stats':
        cmd_stats(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
