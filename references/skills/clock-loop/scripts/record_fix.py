#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复登记器 record_fix.py（v1.0.0 · clock-loop v3.14.0 P2·修复闭环三分权）

来源：02-better-harness深读对标§一#7+8+9（finding-bound-fix三分权·皮叔拍板现在动工2026-07-28）
解决：双盲审计弱点③"修复后finding状态自写自验"——修复者、状态writer、复核者三权分立。

三条铁规（物理位强制，非条文）：
1. 修复者只能建档（--record）：status 恒为 pending_review，代码里没有让record写verdict的入口
2. 状态只经本writer落盘：--expected-revision 乐观锁，revision不符拒写（防并发/防基于过期状态写入）
3. 复核判决（--review）只准三态 verified|partial|blocked，已有判决的fix拒绝二次判决（不可变审计）

两本账原则（SKILL.md条款配套）：本台账只记"修复状态"；Skill评分是另一本账——
修复verified也不改上一份报告的分数，评分变化必须等下一次完整评估（"同窗口修好不涨分"）。

v1.1.0 变更（2026-09-05 · C07 #55 pending_review 超期自动化 · 声明-执行gap根治）：
  病（实测实锤）：steps/counter_pending_review.md（v3.49.0 A20建）声明"N=今日-最旧pending条目
    created日期·实取日期计算"，但全库零脚本消费——pending_review_overdue_days 靠AI手填，
    与 #55"积压26天无报警"同病（载体建了不接线=第二张纸锁）。
  解：本脚本加 --overdue 模式——读 fix_ledger.json 实算最旧 pending_review 条目积压天数，
    自动更新载体文件（pending_review_overdue_days: N）+ 阈值报警（≥7 ⚠提示 / ≥14 exit3 阻断）。
    exit 码：0=正常 | 1=参数错 | 2=乐观锁拒写 | 3=规则拒绝 | 4=超期阻断（≥14天）
    ⛔数据源唯一=fix_ledger.json（not 对话/报告正文）·载体只是计算结果的落盘点（防双本账）。

用法：
  record:  python3 record_fix.py --record --finding-id <id> --finding-src <报告文件名> \
             --fix-desc <一句话> --actual-output <实测摘要> --expected-revision <N>
  review:  python3 record_fix.py --review --fix-id <FIX-N> --verdict verified|partial|blocked \
             --note <复核依据> --expected-revision <N>
  show:    python3 record_fix.py --show
  overdue: python3 record_fix.py --overdue            # 计算并落盘积压天数·阈值报警（C07 #55）
退出码：0=成功 | 1=参数错 | 2=乐观锁拒写 | 3=规则拒绝 | 4=超期阻断
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, sys, json, argparse, re
from datetime import datetime, date

LEDGER = os.path.expanduser("[记忆共享中心]/评估知识库/test_results/fix_ledger.json")
VALID_VERDICTS = ("verified", "partial", "blocked")
# v1.1.0（C07 #55）：载体文件与 record_fix 同根 steps/ 目录（与 counter_conditional_promises.md 并列）
COUNTER_PENDING_REVIEW = os.path.expanduser(
    "[记忆共享中心]/技能配置/clock-loop/steps/counter_pending_review.md")
# 闹钟阈值（与 counter_pending_review.md 头部声明同源·v1.1.0 C07 #55）
WARN_DAYS = 7
BLOCK_DAYS = 14


def _now():
    # v3.50.1（#45跨平台）：subprocess调date在Windows语义不同且多进程开销→datetime本地取
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load():
    # v3.38.2 P3-3修：JSON损坏/缺revision键时优雅降级（备份坏文件+走默认），不裸抛traceback
    if not os.path.exists(LEDGER):
        return {"revision": 0, "fixes": []}
    try:
        with open(LEDGER, encoding="utf-8") as f:
            d = json.load(f)
        if not isinstance(d, dict) or "revision" not in d:
            raise ValueError("ledger缺少revision键或结构非法")
        return d
    except Exception:
        try:
            os.replace(LEDGER, LEDGER + ".corrupt." + _now().replace(" ", "_"))
        except Exception:
            pass
        return {"revision": 0, "fixes": []}


def save(d):
    d["revision"] += 1  # 每次成功写入自增——调用方下次必须带新revision
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, LEDGER)  # 原子写
    return d["revision"]


def overdue_rc(days):
    """--overdue 退出码唯一实现（v4.12.4·R4-F-B：main零覆盖的rc5/4/0语义提为可测纯函数）。
    None→5 fail-closed / ≥BLOCK→4 / 其余0。gate/finalize 消费口径以此为准。"""
    if days is None:
        return 5
    return 4 if days >= BLOCK_DAYS else 0


def check_pending_review_overdue(ledger=None, counter_path=None, today=None):
    """计算最旧 pending_review 条目积压天数并落盘载体（C07 #55·v1.1.0）。

    ⛔数据源唯一=fix_ledger.json（not 对话/报告正文）·载体只是计算结果落盘点。
    判定：N = 今日 - 最旧 pending_review 条目 created 日期（同分钟粒度取日·跨天即算）。
    闹钟：N ≥ 14 → 阻断（exit4·先复核再交付）；N ≥ 7 → ⚠提示（交付声明须含欠账行）；
          N < 7 或无 pending → 0 静默。
    载体：不存在→创建（幂等·full-flow 第258行"文件不存在→视为 N=0 并创建"）；
          存在但无 key 行→重建头文件（fail-visible·⛔不静默吞）。
    Returns (days, oldest_id, pending_count, msg)"""
    ledger_path = ledger or LEDGER
    counter_path = counter_path or COUNTER_PENDING_REVIEW
    today = today or date.today()
    import glob as _glob
    if _glob.glob(str(ledger_path) + '.corrupt.*') or _glob.glob(LEDGER + '.corrupt.*'):
        # v4.12.3·R3攻2：损坏隔离侧车在位="损坏未复核"态，超期不可确知（fail-closed），⛔不得报0健康
        _write_counter(counter_path, None)  # v4.12.4·R4-F-C：不可确知态同样落盘-1（载体与机器行两口径对齐）
        return (None, None, None, '⛔ fix_ledger 存在 .corrupt.* 隔离侧车——损坏待人工核查回灌，超期状态不可确知（v4.12.3）')
    if not os.path.exists(ledger_path):
        days, oldest_id, n = 0, None, 0
    else:
        try:
            with open(ledger_path, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            _write_counter(counter_path, None)  # v4.12.4·R4-F-C：fail-closed 也须落载体（-1哨兵），否则案发现场只有stdout见过、载体仍报旧值
            return (None, None, None,
                    "⛔ fix_ledger.json 读取失败（损坏）——fail-closed：无法确认积压天数，须人工核查")
        pend = [f for f in d.get("fixes", []) if isinstance(f, dict)
                and f.get("status") == "pending_review"]
        n = len(pend)
        if not pend:
            days, oldest_id = 0, None
        else:
            oldest = min(pend, key=lambda f: str(f.get("created", "")))
            oldest_id = oldest.get("id", "?")
            try:
                _c = datetime.strptime(str(oldest.get("created", "")), "%Y-%m-%d %H:%M").date()
            except ValueError:
                _write_counter(counter_path, None)  # 同上（v4.12.4·R4-F-C）
                return (None, None, None,
                        f"⛔ {oldest_id} created 日期格式异常（{oldest.get('created')}）——fail-closed·须人工核查")
            days = (today - _c).days
    # 落盘载体（结果唯一落盘点·防双本账）
    _write_counter(counter_path, days)
    if days is None:
        return (None, None, None, "⚠️ 超期检查 fail-closed：无法确认积压天数（详见上）")
    if days >= BLOCK_DAYS:
        return (days, oldest_id, n,
                f"🔴 pending_review 欠账 {days} 天 ≥ {BLOCK_DAYS}（{oldest_id} 等 {n} 条）——"
                f"阻断'✅交付完成'声明：先复核再交付（C07 #55 闹钟阈值）")
    if days >= WARN_DAYS:
        return (days, oldest_id, n,
                f"⚠️ pending_review 欠账 {days} 天 ≥ {WARN_DAYS}（{oldest_id} 等 {n} 条）——"
                f"交付声明须含欠账行（收尾门禁汇报）")
    if n == 0:
        return (0, None, 0, "pending_review 无积压（0 条）")
    return (days, oldest_id, n,
            f"pending_review {n} 条·最旧 {oldest_id} 积压 {days} 天（<{WARN_DAYS}·未到闹钟阈值）")


def _write_counter(counter_path, days):
    """载体落盘——与 counter_pending_review.md 头部声明格式对齐（原子写·NFC 路径安全）。
    ⛔只更新计数行值·⛔不重写台账段（防误删人工记录）。"""
    header = ("# 持久化计数器：pending_review 超期闹钟（v3.49.0 A20·#55）\n\n"
              "# 形态范式：triwich steps/agent_b_streak.md（单行 key: N + 启动/收尾时检查初始化 + 到阈值注入指令）\n"
              "# ⛔铁律（full-flow 第258行原则）：计数器只放对话上下文=跨会话归零=机制不存在——必须落盘此文件。\n\n")
    if os.path.exists(counter_path):
        try:
            with open(counter_path, encoding="utf-8") as f:
                txt = f.read()
        except OSError:
            txt = ""
        if re.search(r'^pending_review_overdue_days\s*:\s*-?\d+', txt, re.M):  # v4.12.4·R4-F-C：负哨兵可识别，不再重复追加
            txt = re.sub(r'^(pending_review_overdue_days\s*:\s*)-?\d+', r'\g<1>%d' % (days if days is not None else -1),
                         txt, count=1, flags=re.M)
        else:
            txt = txt.rstrip() + f"\npending_review_overdue_days: {days if days is not None else -1}\n"  # -1=fail-closed哨兵（0=确知无积压·两态物理分离·v4.12.3）
    else:
        txt = header + f"pending_review_overdue_days: {days if days is not None else -1}\n"  # 同上哨兵语义
    os.makedirs(os.path.dirname(counter_path), exist_ok=True)
    tmp = counter_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(txt)
    os.replace(tmp, counter_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--overdue", action="store_true")
    ap.add_argument("--finding-id")
    ap.add_argument("--finding-src")
    ap.add_argument("--fix-desc")
    ap.add_argument("--actual-output")
    ap.add_argument("--fix-id")
    ap.add_argument("--verdict")
    ap.add_argument("--note")
    ap.add_argument("--expected-revision", type=int)
    a = ap.parse_args()

    # v4.12.3·R3攻2根治：--overdue 必须先于 load()——load() 遇损坏会把台账 .corrupt 隔离，
    # 之后超期计算就"看不见案发现场"而报0健康（检查器吃掉自己的证据=第四形态新变体）
    if a.overdue:
        days, oldest_id, n, msg = check_pending_review_overdue()
        print(msg)
        print(f"PENDING_REVIEW_DAYS: {days if days is not None else -1}")  # 机器行·gate/finalize单口径（攻3双算法根治）
        return overdue_rc(days)  # v4.12.4·R4-F-B：语义收进可测纯函数

    d = load()

    if a.show:
        print(json.dumps(d, ensure_ascii=False, indent=2)); return 0

    # 乐观锁：record与review都必须带当前revision
    if a.expected_revision is None or a.expected_revision != d["revision"]:
        print(f"⛔ 乐观锁拒写：expected_revision={a.expected_revision} ≠ 当前revision={d['revision']}（先--show取最新）")
        return 2

    if a.record:
        if not all([a.finding_id, a.finding_src, a.fix_desc, a.actual_output]):
            print("❌ record需要 --finding-id --finding-src --fix-desc --actual-output"); return 1
        if a.verdict:
            print("⛔ 规则拒绝：record模式不接受verdict——修复者建档不判决（三分权铁规1）"); return 3
        # v3.55.2（B04校验·#53数据污染防新增）：finding_id 不得为 FIX- 形态——那是本系统
        # 分配的修复ID（自指/引用他人fix条目=FIX-018/019~022实锤污染形态）；来源ID应来自
        # 审查队列/评估报告的原始编号体系
        if a.finding_id.startswith("FIX-"):
            print(f"⛔ 规则拒绝：finding_id 不得为 FIX- 形态（{a.finding_id}）——finding_id 引用来源问题原始ID，FIX-N 由本系统分配（#53校验·自指/污染防新增）"); return 3
        # v3.51.1（#44 ID碰撞根治）：fid 取"现存最大编号+1"并扫描 .corrupt 备份继承水位——
        # 旧逻辑=列表长度+1，corrupt重置清空后新建会与历史FIX-001重名（审计链断裂）
        _nums = [int(f2["id"].split("-")[-1]) for f2 in d.get("fixes", [])
                 if isinstance(f2, dict) and str(f2.get("id", "")).startswith("FIX-")
                 and f2["id"].split("-")[-1].isdigit()]
        _glob = os.path.join(os.path.dirname(LEDGER), os.path.basename(LEDGER) + ".corrupt.*")
        import glob as _glob_mod
        for _bak in _glob_mod.glob(_glob):
            try:
                _bd = json.load(open(_bak, encoding="utf-8"))
                for f2 in _bd.get("fixes", []):
                    if isinstance(f2, dict) and str(f2.get("id", "")).startswith("FIX-"):
                        _tail = f2["id"].split("-")[-1]
                        if _tail.isdigit():
                            _nums.append(int(_tail))
            except Exception:
                continue  # 备份损坏不阻塞建档（水位尽力继承）
        fid = f"FIX-{(max(_nums) if _nums else 0) + 1:03d}"
        d["fixes"].append({
            "id": fid, "finding_id": a.finding_id, "finding_src": a.finding_src,
            "fix_desc": a.fix_desc, "actual_output": a.actual_output,
            "status": "pending_review",  # 恒定——无入口可改
            "review": None, "created": _now(), "reviewed": None,
        })
        rev = save(d)
        print(f"✅ 已建档 {fid} | status=pending_review | 新revision={rev}")
        return 0

    if a.review:
        if not all([a.fix_id, a.verdict, a.note]):
            print("❌ review需要 --fix-id --verdict --note"); return 1
        if a.verdict not in VALID_VERDICTS:
            print(f"⛔ 规则拒绝：verdict只准 {VALID_VERDICTS}（输出限窄·三分权铁规3）"); return 3
        hit = [f for f in d["fixes"] if f["id"] == a.fix_id]
        if not hit:
            print(f"❌ 无此fix: {a.fix_id}"); return 1
        fx = hit[0]
        if fx["status"] != "pending_review":
            print(f"⛔ 规则拒绝：{a.fix_id} 已有判决({fx['status']})——不可变审计，变更走新fix条目"); return 3
        # v3.55.2（B04校验·#53自写自验防新增）：复核时间与建档同分钟→拒绝（复核独立性）
        _c = str(fx.get("created", ""))
        _r = _now()
        if _c[:16] == _r[:16]:
            print(f"⛔ 规则拒绝：复核与建档同一分钟（{_c[:16]}）——自写自验（#53实证形态·须独立时点复核）"); return 3
        fx["status"] = a.verdict
        fx["review"] = a.note
        fx["reviewed"] = _r
        rev = save(d)
        print(f"✅ 已判决 {a.fix_id} → {a.verdict} | 新revision={rev}")
        return 0

    ap.print_help(); return 1


if __name__ == "__main__":
    sys.exit(main())
