#!/usr/bin/env python3
# drift_check_remind.py v1.4 — 童灵漂移告警器（四判据：体检到期 + 飞轮断链 + 童灵验收抽查断链 + 谓词契约族漂移 + 弹窗触达）
# v1.4: 2026-10-09 (Qoder CN·你「按三明智建议继续下一步」批·S1087分诊落地)——新增判定④「谓词契约族漂移」：
#   跨作者字符串契约（文档填法值↔消费者脚本==判等）文档侧锚丢失而消费侧仍判等→告警。
#   分诊判据（S1087）：只巡 跨作者×非自写自读 的族——107候选点筛出3族(1强2弱)，其余豁免（自写自读/运行时输入判词）。
#   纯函数 _contract_drift_lines(contracts, read_text, today) 可注入夹具；--test-contracts 三态验收。
#   数据真源=锚点常量表（本文件内）+ 工作痕迹/predicate_contracts_2026-10-09.json（全集盘点底稿·下限口径）。
# 创建: 2026-09-20 (WorkBuddy·皮叔拍板例行化)
# v1.1: 2026-10-08 (Qoder CN·校准飞轮第二圈补燃料 T4)——新增判定②，把 02§三
#   「飞轮断链兜底」原文承诺（你长期不抽检>14天→自动漂移自告警+升级全人工待回归，
#   禁止静默停转）从 gray_stats.log 的"只进报告没人读"迁入会话代理真读的消费通道。
# v1.2: 2026-10-08 (Qoder CN·T8)——notify_bro() 弹窗触达（有告警才弹·复用 awaken patrol
#   §3.2 无事不打扰）；--test-notify 验收开关。本文件由会话实录重建（原 v1.2 实体被
#   软链自愈还原吞没·2026-10-08 14:2x 发现，恢复依据=当日 13:1x 全文 Read 实录+自有补丁）。
# v1.3: 2026-10-08 (豆包办公·K007融入飞轮 T11-4)——新增判定③「童灵验收抽查断链」：
#   距你最近一次抽查童灵验收判定（合并台账"确认人=你"行）>14天→告警。数据真源=
#   AI学习库/合并台账.md（去重/融合机制#8）；合并台账不存在=判定③未激活·静默跳过
#   （等待去重/融合机制落地后自动激活），不误告警。
#
# 判定①（人格漂移体检·v1.0 原职责保留）: 距上次体检 ≥30 天 → 写到期提醒。
# 判定②（飞轮断链·v1.1 新增）: 距"你最近一次复核"（认可/推翻）> 14 天 → 写自告警。
#   数据真源 = steps/step3-first-review-log.md 复核列内认可日期 + steps/step3-overturned.md
#   登记日期，口径复用 gray_release_stats.parse_review（⛔不内联第二套判据）。
# 判定③（童灵验收抽查断链·v1.3 新增）: 距"你最近一次抽查童灵验收判定">14天→告警。
#   数据真源 = AI学习库/合并台账.md 的"确认人=你"行（去重/融合机制#8合并台账第6字段）。
#   合并台账不存在或无你确认记录=判定③未激活·静默跳过（等待机制落地）。
#   ⛔ 本脚本不做体检/抽检本身——触发归脚本、语义执行归会话代理（分工红线同 v1.0）。
#
# 判定数据源①（单一真源）: scripts/drift_check_state.json 的 last_check 字段
#   - 体检完成后由执行代理更新（约定见 数字分身/README.md 接续入口）
#   - state 缺失 = 视为超期，提醒中注明"未初始化"
#
# 输出: scripts/drift_check_remind.log
#   - 任一判定触发: 非空提醒行（会话代理读到非空即执行对应动作）+ 弹窗（v1.2·macOS）
#   - 双判据均未触发: 空文件（静默·不弹窗）
# 退出码: 恒 0（提醒器不阻塞系统，到期与否看日志）

# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

def _base_dir() -> Path:
    env = os.environ.get("DIGITALTWIN_HOME")  # 自定义数字分身中心（安装包用户可配置）
    return Path(env).expanduser() if env else Path('[记忆共享中心]') / "数字分身"


BASE = _base_dir()
SCRIPTS = BASE / "scripts"
STEPS = BASE / "steps"
STATE_FILE = SCRIPTS / "drift_check_state.json"
REMIND_LOG = SCRIPTS / "drift_check_remind.log"
REVIEW_LOG = STEPS / "step3-first-review-log.md"
OVERTURNED_LOG = STEPS / "step3-overturned.md"
INTERVAL_DAYS = 30        # 判定①：体检到期阈值（天）
REVIEW_GAP_DAYS = 14      # 判定②：飞轮断链阈值（天·02§三原文）
ACCEPTANCE_GAP_DAYS = 14  # 判定③：童灵验收抽查断链阈值（天·对齐判定②）
MERGE_LEDGER = Path.home() / "[记忆共享中心]" / "知识库" / "AI学习库" / "合并台账.md"  # 判定③数据真源（去重/融合机制#8）

sys.path.insert(0, str(SCRIPTS))


def read_last_check() -> tuple[str | None, str | None]:
    """返回 (last_check_iso, note)。state 缺失/损坏返回 (None, 原因)。"""
    if not STATE_FILE.exists():
        return None, "state 未初始化"
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        last = data.get("last_check")
        date.fromisoformat(last)  # 校验格式
        return last, data.get("note")
    except Exception as e:  # noqa: BLE001
        return None, f"state 损坏: {e}"


def last_review_date() -> tuple[date | None, str]:
    """你最近一次复核日期（认可∪推翻 取 max）。返回 (日期|None, 说明)。
    口径复用 gray_release_stats.parse_review——本函数不重复实现复核列判据。"""
    dates: list[date] = []
    notes: list[str] = []
    try:
        import gray_release_stats as grs
    except Exception as e:  # noqa: BLE001
        return None, f"口径模块缺失（{e!r}）·无法判定断链——请检查 scripts/gray_release_stats.py"
    try:
        r = grs.parse_review(str(REVIEW_LOG))
        if r.get("last_human_date"):
            dates.append(r["last_human_date"])
    except Exception as e:  # noqa: BLE001
        notes.append(f"初审台账解析异常: {e!r}")
    if OVERTURNED_LOG.exists():
        for line in OVERTURNED_LOG.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^[|]\s*\d+\s*[|]\s*(\d{4}-\d{2}-\d{2})", line)
            if m:
                try:
                    dates.append(datetime.strptime(m.group(1), "%Y-%m-%d").date())
                except ValueError:
                    pass
    else:
        notes.append("推翻台账缺失")
    if not dates:
        ref = getattr(grs, "ANCHOR", None)
        if ref:
            return ref, f"自灰度锚点 {ref.isoformat()} 起无任何复核记录"
        return None, "无任何复核记录且锚点不可得"
    return max(dates), ""


def last_acceptance_review_date() -> tuple[date | None, str]:
    """判定③（v1.3）：你最近一次抽查童灵验收判定日期。
    数据真源=AI学习库/合并台账.md的"确认人=你"行（去重/融合机制#8合并台账第6字段）。
    合并台账不存在=判定③未激活（等待去重/融合机制落地），返回(None, "未激活·不告警")。
    合并台账存在但无你确认记录=返回(None, "无你确认记录·不告警")。
    ⛔ 不内联第二套判据——合并台账格式定义见去重/融合机制任务书#8（9字段Markdown表格）。"""
    if not MERGE_LEDGER.exists():
        return None, "合并台账不存在·判定③未激活（等待去重/融合机制落地）"
    dates: list[date] = []
    for line in MERGE_LEDGER.read_text(encoding="utf-8").splitlines():
        # Markdown表格行：| M001 | 2026-10-15 | S1001 | S1002 | 原因 | 你 | v1.2→v1.3 | 路径 | 备注 |
        # split("|")后索引：0='' 1=合并ID 2=日期 3=主卡 4=次卡 5=原因 6=确认人 7=主卡版本 8=次卡归档 9=备注 10=''
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 7 and cells[6] == "你":
            try:
                dates.append(datetime.strptime(cells[2], "%Y-%m-%d").date())
            except ValueError:
                pass
    if not dates:
        return None, "合并台账存在但无你确认记录"
    return max(dates), ""


# ── 判定④：谓词契约族漂移（v1.4·S1087分诊落地）──
_KF = Path('[记忆共享中心]') / "开发工具" / "知识联邦引擎" / "scripts"
PATROL_CONTRACTS = [
    {"name": "合并台账·确认人（强·跨作者）",
     "doc": Path.home() / "[记忆共享中心]" / "知识库" / "AI学习库" / "合并台账.md",
     "doc_needle": "裸名 `童灵` 或 `你`",
     "reader": Path('[记忆共享中心]') / "脚本中心" / "build_spotpack.py",
     "reader_needle": '!= "童灵"'},
    {"name": "反馈话术·这条没用（弱·同域异代）",
     "doc": _KF / "kb_inject_prompt.py",
     "doc_needle": "这条没用",
     "reader": _KF / "feedback_detect.py",
     "reader_needle": '"这条没用"'},
    {"name": "快照·日期列名（弱·异端写入观察）",
     "doc": Path('[记忆共享中心]') / "情境层" / "动态状态快照.md",
     "doc_needle": "| 日期 |",
     "reader": Path('[记忆共享中心]') / "技能配置" / "awaken-memory-system" / "scripts" / "awaken_health_dashboard.py",
     "reader_needle": 'cells[0] == "日期"'},
]

def _contract_drift_lines(contracts, read_text, today):
    """纯函数：文档侧锚丢失 且 消费侧仍判等 → 告警行。
    任一文件读不到=该族未激活→静默（同判定③「等待机制落地」模式·不误报）。
    消费侧needle消失=契约已自愿解除→静默。"""
    out = []
    for c in contracts:
        try:
            doc = read_text(c["doc"]); rdr = read_text(c["reader"])
        except OSError:
            continue
        if c["reader_needle"] in rdr and c["doc_needle"] not in doc:
            out.append(
                f"🔴 契约族漂移（{c['name']}）（{today.isoformat()}）：消费侧仍按旧值判等而文档侧锚已消失——"
                "改文档措辞前须 grep 消费者（S1087纪律①）；动作=恢复文档锚或双侧同步解除契约。"
                f"（doc={Path(c['doc']).name}·needle=「{c['doc_needle'][:20]}」）"
            )
    return out

def contract_drift_lines(today) -> list[str]:
    return _contract_drift_lines(PATROL_CONTRACTS, lambda p: Path(p).read_text(encoding="utf-8"), today)

def _selftest_contracts() -> int:
    """三态夹具：命中告警 / 一致静默 / doc未激活静默。"""
    from datetime import date as _d
    today = _d(2026, 10, 9)
    C = [{"name": "T", "doc": "D", "doc_needle": "锚A", "reader": "R", "reader_needle": '== "x"'}]
    reads = {
        "hit":  {"D": "正文里这个格子是空的", "R": 'v == "x"'},  # 夹具教训(2026-10-09):原文案「正文没有锚A」本身含锚A=假阴性夹具
        "ok":   {"D": "含 锚A 字样", "R": 'v == "x"'},
        "dead": {"D": "随便", "R": 'v.startswith("x")'},   # 消费侧解除
    }
    def mk(tag):
        return lambda p: reads[tag][p]
    r1 = _contract_drift_lines(C, mk("hit"), today)
    r2 = _contract_drift_lines(C, mk("ok"), today)
    r3 = _contract_drift_lines(C, mk("dead"), today)
    ok = bool(r1) and not r2 and not r3
    print("[drift-check selftest-contracts] 命中/静默/解除:", "3/3 通过" if ok else f"FAIL ({len(r1)},{len(r2)},{len(r3)})")
    return 0 if ok else 1

def notify_bro(lines) -> None:
    """T8 触达（2026-10-08·任务卡）：有告警才弹窗——复用 awaken patrol §3.2「无事不打扰」模式。
    macOS 宿主依赖：非 darwin 静默跳过；弹窗失败不阻塞（日志仍是主通道·降级如实打印）。"""
    if sys.platform != "darwin":
        return
    try:
        import subprocess
        msg = lines[0][:180].replace('"', "'").replace("\\", "")
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "童灵·飞轮告警"'],
                       timeout=15, check=False)
    except Exception as e:  # noqa: BLE001
        print(f"[drift-check-remind] 弹窗失败（不阻塞·日志为主通道）: {e!r}")


def main() -> int:
    if "--test-contracts" in sys.argv:  # v1.4 判定④三态自测
        return _selftest_contracts()
    if "--test-notify" in sys.argv:  # T8 验收：强制试弹（非真告警）
        notify_bro(["🔧 测试弹窗：T8触达验收（收到即验证通过·非真告警）"])
        print("[drift-check-remind] --test-notify 已调用弹窗")
        return 0
    today = date.today()
    lines: list[str] = []

    # ── 判定①：人格漂移体检到期（≥30天）──
    last, note = read_last_check()
    if last is None:
        lines.append(
            f"⚠️ 漂移体检提醒（{today.isoformat()}）: {note}。"
            "请执行首次/修复初始化: 按 steps/step2-eval-protocol.md 跑盲评，"
            "完成后写 scripts/drift_check_state.json {last_check: YYYY-MM-DD, note: ...}"
        )
    else:
        days_check = (today - date.fromisoformat(last)).days
        if days_check >= INTERVAL_DAYS:
            lines.append(
                f"🔔 漂移体检到期（{today.isoformat()}）: 上次体检 {last}，已 {days_check} 天（阈值 {INTERVAL_DAYS}）。"
                "执行: 复用 steps/step2.8-blind-items.md 同套盲题 → 童灵盲判落盘 → 独立隔离上下文判分"
                "（先例 steps/step2.9-drift-{judgments,report}.md）→ 更新 drift_check_state.json"
            )

    # ── 判定②：飞轮断链（距你最近复核>14天·02§三）──
    rev_d, rev_note = last_review_date()
    if rev_d is not None:
        gap = (today - rev_d).days
        if gap > REVIEW_GAP_DAYS:
            extra = f"（{rev_note}）" if rev_note else ""
            lines.append(
                f"🔴 飞轮断链自告警（{today.isoformat()}）: 距你最近一次复核 {rev_d.isoformat()} 已 {gap} 天"
                f"（阈值 {REVIEW_GAP_DAYS}）{extra}。依 02§三 断链兜底：升级全人工待回归，禁止静默停转——"
                "动作=生成/递送抽检包（scripts/build_spotpack.py·或读 pending 抽检包），你复核后本告警自清。"
            )
    else:
        lines.append(
            f"🔴 飞轮断链判定失效告警（{today.isoformat()}）: {rev_note}。"
            "无法判定≠正常——按断链处置：人工对账 gray_release_stats 口径与台账路径。"
        )

    # ── 判定③：童灵验收抽查断链（距你最近一次抽查童灵验收>14天·v1.3新增）──
    acc_d, acc_note = last_acceptance_review_date()
    if acc_d is not None:
        acc_gap = (today - acc_d).days
        if acc_gap > ACCEPTANCE_GAP_DAYS:
            lines.append(
                f"🔴 童灵验收抽查断链（{today.isoformat()}）: 距你最近一次抽查童灵验收判定 {acc_d.isoformat()} 已 {acc_gap} 天"
                f"（阈值 {ACCEPTANCE_GAP_DAYS}）。童灵连续做验收判定但你长期未抽查→可能积累误判→"
                "动作=从合并台账抽取近期童灵判定记录交你抽查（对齐去重/融合机制§八严重问题标准）。"
            )
    # acc_d is None时静默跳过（合并台账不存在或无你确认记录=判定③未激活·不告警·不误报）

    # ── 判定④：谓词契约族漂移（v1.4·S1087分诊3族·无状态逐次实读）──
    lines.extend(contract_drift_lines(today))

    if lines:
        REMIND_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[drift-check-remind] {len(lines)} 条告警已写入: {REMIND_LOG.name}")
        notify_bro(lines)  # T8：写了日志同时弹一次（有事才到这行）
    else:
        REMIND_LOG.write_text("", encoding="utf-8")  # 静默
        days_check = (today - date.fromisoformat(last)).days if last else -1
        gap = (today - rev_d).days if rev_d else -1
        acc_gap = (today - acc_d).days if acc_d else -1
        acc_status = f"·验收抽查 gap {acc_gap} 天≤{ACCEPTANCE_GAP_DAYS}" if acc_d else "·验收抽查未激活（合并台账无数据）"
        print(f"[drift-check-remind] 四判据均未触发（体检 {days_check} 天前·复核 gap {gap} 天≤{REVIEW_GAP_DAYS}{acc_status}），日志已清空")

    return 0


if __name__ == "__main__":
    sys.exit(main())
