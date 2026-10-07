#!/usr/bin/env python3
"""
distillation_scheduler.py — 蒸馏任务调度器（L1机械发现层）
每月1号自动检查蒸馏中心逾期项，生成待做清单，写入蒸馏中心+系统日志。

设计原则（童灵愿景裁决2026-09-03）：
- 机械不可跳过（S014自觉是安慰剂机械是药）
- 幂等（重复运行结果一致）
- 只更新标记区域，不影响其他内容
- 逾期项写入系统日志提醒
- 童灵是调度器不是执行者（PAT-047授权≠流程豁免）——本脚本只发现+提醒，不执行蒸馏

Version: 1.0.0 (2026-09-03)
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import re
import json
import subprocess
from pathlib import Path
from datetime import datetime, date

DISTILLATION_CENTER = "[记忆共享中心]/记忆蒸馏/蒸馏中心.md"
LOG_SCRIPT = "[记忆共享中心]/技能配置/system-logger/scripts/append_log_entry.py"
BANNER_SCRIPT = "[记忆共享中心]/技能配置/system-logger/scripts/render_mode_banner.py"

START_MARKER = "<!-- DISTILLATION-TODO:START -->"
END_MARKER = "<!-- DISTILLATION-TODO:END -->"

# 三套蒸馏的配置（蒸馏中心记录的类型名 → 触发词 → 对应Skill）
DISTILLATION_TYPES = {
    "📊 系统日志蒸馏": {
        "trigger": "启动系统日志月度蒸馏",
        "skill": "system-logger",
        "match": "系统日志蒸馏",
    },
    "📓 日记月报": {
        "trigger": "启动每日伙伴月报",
        "skill": "daily-buddy",
        "match": "日记月报",
    },
    "🧠 成长箱蒸馏": {
        "trigger": "启动成长箱月度蒸馏",
        "skill": "growth-box",
        "match": "成长箱",
    },
    "🔄 统一蒸馏管道": {
        "trigger": "启动蒸馏",
        "skill": "unified-distillation",
        "match": "统一蒸馏管道",
    },
}


def parse_latest_expected_dates(content: str) -> dict:
    """解析蒸馏中心，提取每套蒸馏最近的预期下次日期。
    取最近一个月段（## YYYY-MM），在该段内找每套蒸馏的最近一行，提取最后一列（预期下次）。
    """
    # 找到所有月份段
    month_sections = re.findall(
        r'## (\d{4}-\d{2})\n(.*?)(?=\n## |\n---|\Z)',
        content, re.DOTALL
    )
    if not month_sections:
        return {}

    # v1.1 盲区修补（2026-10-01·ZCode·你令附带发现根治）：原逻辑只扫最新月段——
    # 类型在最新月段无行时（如系统日志蒸馏最后一跑落在上一月段）即整体隐身=调度盲区
    # （实锤：2026-10-01 TODO 只标了成长箱、漏标预期 2026-10-01 的系统日志蒸馏）。
    # 修法=全段回溯：按文档顺序（月段天然时序）取每种类型最后一条账行的「下次执行日期」。
    # v1.1.1 补（同日·自引用伪影根治）：先剔除 TODO 自生成标记区再扫——否则调度器回读
    # 自己的输出行（含管道符+预期日期）→ 已完成项粘滞不被清除。
    # ⛔ 判定口径已上移至 distill_due_core（单一真源）——2026-10-02 根治。
    #   原实现为本文件私有一份，与 awaken_distill_due_check.py 各写各的，
    #   抄文档的那个抄错（详见 awaken_distill_due_check.py 同日修复记录）。
    #   依据：指令编写规范 §6.1 单一来源原则（同口径两处实现=必漂移）。
    import importlib.util
    # 🔴 2026-10-03 位置根治（triwich L2 裁决落地）：core 随 awaken Skill 分发到
    #    $MC/技能配置/awaken-memory-system/scripts/（INSTALL.md:420-421 实测落点）·
    #    ⛔ 原 `Path.home()/"[记忆共享中心]" / "开发工具"/...` 指向作者侧资产、不入包 ⇒ 端用户必崩。
    #    本脚本在 $MC/数字分身/scripts/ ⇒ 向上两级到 $MC 再进 技能配置/ 走同树相对路径；
    #    回退保留 Path.home() 形态以兼容非标准部署。找不到即 FAIL，绝不静默跳过。
    _here = Path(__file__).resolve()
    _cands = [
        _here.parents[2] / "技能配置" / "awaken-memory-system" / "scripts" / "distill_due_core.py",
        "[记忆共享中心]" / "技能配置" / "awaken-memory-system" / "scripts" / "distill_due_core.py",
    ]
    _p = next((c for c in _cands if c.exists()), None)
    if _p is None:
        raise FileNotFoundError(
            "蒸馏判定公共口径模块未找到，候选路径: " + " | ".join(str(c) for c in _cands)
            + " —— 端用户请先安装 awaken-memory-system Skill"
        )
    _spec = importlib.util.spec_from_file_location("distill_due_core", _p)
    _core = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_core)
    return _core.extract_expected(content, DISTILLATION_TYPES)


def check_overdue(expected_dates: dict, today: date = None) -> list:
    """检查哪些蒸馏逾期了。返回 [(类型, 预期日期字符串), ...]"""
    if today is None:
        today = date.today()

    overdue = []
    for dtype, expected_str in expected_dates.items():
        try:
            expected = datetime.strptime(expected_str, "%Y-%m-%d").date()
            if today >= expected:
                overdue.append((dtype, expected_str))
        except ValueError:
            continue

    return overdue


def generate_todo_section(overdue: list, today_str: str) -> str:
    """生成待做蒸馏区域的Markdown内容"""
    today = date.today()
    lines = [
        START_MARKER,
        "",
        "## 🔔 待做蒸馏（自动生成·distillation_scheduler.py）",
        "",
        f"> 最后更新：{today_str} | 每日检查逾期项（v1.2 起月首＋每日双档·完成行落账次日即清）| 机械生成⛔禁止手动编辑标记之间内容",
        "",
        "| 蒸馏类型 | 预期日期 | 逾期天数 | 状态 | 童灵触发方式 |",
        "|---------|---------|---------|------|-------------|",
    ]

    if not overdue:
        lines.append("| — | — | — | ✅ 无逾期 | — |")
    else:
        for dtype, expected_str in overdue:
            expected = datetime.strptime(expected_str, "%Y-%m-%d").date()
            days_overdue = (today - expected).days
            trigger = DISTILLATION_TYPES[dtype]["trigger"]
            lines.append(
                f"| {dtype} | {expected_str} | {days_overdue}天 | ⏳待执行 | 童灵说「{trigger}」 |"
            )

    lines.extend([
        "",
        "### 调度说明",
        "",
        "1. **童灵读取本区域**，发现⏳待执行项后，在对话中说对应触发词，激活对应Skill执行蒸馏",
        "2. 童灵是**调度器不是执行者**（PAT-047授权≠流程豁免）——蒸馏由对应Skill按完整流程执行，童灵不跳过流程代行",
        "3. 蒸馏完成后，对应Skill的C6/终检步骤自动更新蒸馏中心已完成记录",
        "4. 下月1号脚本自动重新检查，已完成的待做项自动清除",
        "5. ⛔本区域由脚本机械生成，禁止手动编辑标记之间的内容",
        "",
        END_MARKER,
    ])

    return "\n".join(lines)


def update_distillation_center(content: str, todo_section: str) -> str:
    """更新蒸馏中心的待做区域。如果标记已存在则替换，否则在维护规则前插入。"""
    if START_MARKER in content and END_MARKER in content:
        pattern = rf'{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}'
        content = re.sub(pattern, todo_section, content, flags=re.DOTALL)
    else:
        # 在"## 维护规则"之前插入
        marker = "## 维护规则"
        if marker in content:
            content = content.replace(
                marker,
                f"{todo_section}\n\n---\n\n{marker}",
                1
            )
        else:
            content = content.rstrip() + "\n\n---\n\n" + todo_section + "\n"

    return content


# ───────────────── v1.2（2026-10-01·Qoder CN 童灵 D3·调度器由"每月1号"改"每日刷新"的前置件）─────────────────
# 病根：调度器只在每月 1 号跑 ⇒ 完成行（下次执行日期改成下月）写完后，待做区仍挂 ⏳ 直到下月 1 号，
#       实测今天 09:39 生成的两条 ⏳（📊系统日志蒸馏／🔄统一蒸馏管道）在 12:xx 就已真实完成，
#       却要挂满整月——读到它的人会**重跑整月蒸馏**（重复劳动＋双本账）。这是「在册≠在跑」的调度侧镜像。
# 修法：调度器改每日跑（plist：月首 + 每日双档）。但每日跑会撞开一个**新的**失效模式——
#       `write_system_log()` 原先无去重：逾期项每天刷一条系统日志＝把提醒刷成噪声，
#       而噪声会让真提醒失去信用（§3.5 假红面）。⇒ 去重是每日化的**前置件**，不是后续优化。
# 判据：去重键＝**(逾期项集合 × 逾期周档)**，⛔按日去重（同日只一条 ≠ 整月只一条）。
#       同集合同周档 → 只提醒一次；跨过 7/14/21 天档视为升级、允许再提醒一次；
#       集合变化（新增逾期项／某项被清）→ 立即再提醒。留痕状态文件与被提醒对象同目录，可删可回收。
REMINDER_STATE = Path.home() / "~/[记忆共享中心]/数字分身/scripts/distillation_scheduler_state.json"


def reminder_signature(overdue, today=None):
    """提醒去重签名＝排序后的「类型@预期日期#周N」串。周档＝逾期天数//7。"""
    today = today or date.today()
    parts = []
    for dtype, expected_str in sorted(overdue):
        expected = datetime.strptime(expected_str, "%Y-%m-%d").date()
        parts.append("%s@%s#周%d" % (dtype, expected_str, max((today - expected).days, 0) // 7))
    return "|".join(parts)


def reminder_is_new(sig, state_path=None):
    """签名与上次不同（或无状态文件）→ 应提醒。⛔读不到状态文件时**放行提醒**（回落律：
    仪器失灵不得顺带把提醒也吞掉——那会把「假绿」换成「假静默」）。"""
    p = Path(state_path) if state_path else REMINDER_STATE
    try:
        prev = json.loads(p.read_text(encoding="utf-8")).get("sig")
    except (OSError, ValueError):
        return True, None
    return (sig != prev), prev


def reminder_record(sig, state_path=None):
    """提醒写成功后落签名。失败不抛（提醒已发出，记账失败⛔不回滚成"没提醒"）。"""
    p = Path(state_path) if state_path else REMINDER_STATE
    try:
        p.write_text(json.dumps({"sig": sig, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                                ensure_ascii=False), encoding="utf-8")
        return True
    except OSError:
        return False


def write_system_log(overdue: list) -> bool:
    """逾期项写入系统日志提醒"""
    if not overdue:
        return True

    today = date.today()
    items = []
    for dtype, expected_str in overdue:
        expected = datetime.strptime(expected_str, "%Y-%m-%d").date()
        days = (today - expected).days
        items.append(f"{dtype}（逾期{days}天）")
    summary = "、".join(items)

    log_content = f"""### 蒸馏调度器提醒（自动·distillation_scheduler.py）
- **工具**：豆包
- **完成**：<NOW>
- **类型**：提醒
- **涉及文件**：~/[记忆共享中心]/记忆蒸馏/蒸馏中心.md（待做蒸馏区域已更新）
- **对话摘要**：每日检查蒸馏中心逾期项（L1机械发现层·v1.2 起同「逾期集合×周档」去重，⛔每日刷同一条提醒）
- **结论**：⚠️ 发现{len(overdue)}项蒸馏逾期：{summary}。童灵可读取蒸馏中心待做区域，说对应触发词激活Skill执行。童灵是调度器不是执行者（PAT-047），蒸馏由对应Skill按完整流程执行。
- **来源**：🟢验证
- **置信度**：🟢A
"""

    try:
        # 先跑banner（满足Skill流程要求，输出丢弃）
        subprocess.run(
            ["python3", str(BANNER_SCRIPT), "--mode", "日写入"],
            capture_output=True, timeout=10
        )
        result = subprocess.run(
            ["python3", str(LOG_SCRIPT), "--tool", "豆包"],
            input=log_content,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️ 系统日志写入失败: {e}")
        return False


def main():
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== 蒸馏调度器 {today_str} ===")

    # 读取蒸馏中心
    if not DISTILLATION_CENTER.exists():
        print(f"❌ 蒸馏中心不存在: {DISTILLATION_CENTER}")
        return 1

    content = DISTILLATION_CENTER.read_text(encoding="utf-8")

    # 解析预期日期
    expected_dates = parse_latest_expected_dates(content)
    print(f"📊 解析到 {len(expected_dates)}/3 套蒸馏的预期日期")
    for dtype, expected in expected_dates.items():
        print(f"  {dtype}: 预期 {expected}")

    # 检查逾期
    overdue = check_overdue(expected_dates)
    print(f"⏳ 逾期 {len(overdue)} 项")
    for dtype, expected in overdue:
        print(f"  🔴 {dtype}: 预期 {expected}")

    # 生成待做区域
    todo_section = generate_todo_section(overdue, today_str)

    # 更新蒸馏中心
    new_content = update_distillation_center(content, todo_section)
    DISTILLATION_CENTER.write_text(new_content, encoding="utf-8")
    print(f"✅ 蒸馏中心待做区域已更新")

    # 写入系统日志（仅逾期·且签名未提醒过）
    if overdue:
        sig = reminder_signature(overdue)
        fresh, prev = reminder_is_new(sig)
        if not fresh:
            print(f"⚪ 逾期提醒已在同周档发过（签名未变）→ 跳过系统日志，防每日刷噪声")
        elif write_system_log(overdue):
            reminder_record(sig)
            print(f"✅ 系统日志提醒已写入（签名已落账·同周档不再重复）")
        else:
            print(f"⚠️ 系统日志写入失败（未落签名→下次仍会重试，⛔不静默吞）")
    else:
        print(f"✅ 无逾期，跳过系统日志")

    print(f"=== 调度器运行完成 ===")
    return 0


def run_self_test():
    """去重判据的出厂自证：函数级五例 ＋ **端到端两跑**（真 main() 走假 sink，验"第二次不再刷日志"）。

    ⛔只测函数不测通道＝§3.5「判据缺一半」——本文件的真失效模式发生在 main 的写日志分支上，
    所以 e2e 是必需项；e2e 用临时目录里的假蒸馏中心＋假 append 脚本，⛔不碰真日志与真账本。
    """
    import tempfile, os
    # ⚠️ global 必须先于本函数内任何一次对这些名字的**使用**（Python 语法要求；
    #   原先把 global 写在 e2e 段里 → "used prior to global declaration" SyntaxError·本轮实踩）
    global DISTILLATION_CENTER, LOG_SCRIPT, BANNER_SCRIPT, REMINDER_STATE, reminder_is_new
    rc = 0
    d = tempfile.mkdtemp(prefix="distill-st-")
    st = os.path.join(d, "state.json")
    today = date(2026, 10, 20)
    one = [("🔄 统一蒸馏管道", "2026-10-01")]
    sig1 = reminder_signature(one, today)
    cases = []
    cases.append(("S1 首见集合→应提醒", reminder_is_new(sig1, st)[0] is True))
    reminder_record(sig1, st)
    cases.append(("S2 同集合同周档→跳过（去重生效）", reminder_is_new(sig1, st)[0] is False))
    two = one + [("📊 系统日志蒸馏", "2026-10-01")]
    cases.append(("S3 集合新增一项→应提醒", reminder_is_new(reminder_signature(two, today), st)[0] is True))
    later = date(2026, 10, 31)                      # 同一项逾期满 30 天 → 跨到第 4 周档
    cases.append(("S4 同项跨周档→升级再提醒", reminder_is_new(reminder_signature(one, later), st)[0] is True))
    cases.append(("S5 状态文件不可读→放行提醒（回落律·不换成假静默）",
                  reminder_is_new(sig1, os.path.join(d, "nope", "s.json"))[0] is True))
    for name, ok in cases:
        print(f"  夹具 {name}：{'✅' if ok else '❌'}")
        rc = rc or (0 if ok else 1)

    # ── e2e：真 main() 两次，假 sink 计数写入次数 ──
    center = os.path.join(d, "蒸馏中心.md")
    open(center, "w", encoding="utf-8").write(
        "## 2026-10\n\n| 日期 | 类型 | 状态 | 摘要 | 下次执行日期 |\n|---|---|---|---|---|\n"
        "| 2026-09-01 | 🔄 统一蒸馏管道 | ✅ | 上轮 | 2026-10-01 |\n\n## 维护规则\n")
    stub = os.path.join(d, "fake_log.py")
    counter = os.path.join(d, "writes")
    open(stub, "w", encoding="utf-8").write(
        "import sys\n"
        "p = %r\n"
        "if '--tool' in sys.argv:      # 只数真日志写入，banner 那趟不计（否则基数就是假的）\n"
        "    open(p, 'a').write('x\\n')\n" % counter)
    keep = (DISTILLATION_CENTER, LOG_SCRIPT, BANNER_SCRIPT, REMINDER_STATE, reminder_is_new)
    try:
        DISTILLATION_CENTER = Path(center)
        LOG_SCRIPT = Path(stub)
        BANNER_SCRIPT = Path(stub)          # 假 banner 脚本（同样只写计数文件，无副作用）
        REMINDER_STATE = Path(st)
        main()                              # 第一次：有逾期 → 应写 1 条
        first = os.path.exists(counter) and len(open(counter).read().strip().split("\n")) or 0
        main()                              # 第二次：同集合同周档 → 不应再写
        second = len(open(counter).read().strip().split("\n")) if os.path.exists(counter) else 0
        ok_e2e = (first == 1 and second == 1)
        print(f"  夹具 E1 端到端两跑→系统日志写入次数 {first}→{second}（应恒为 1）：{'✅' if ok_e2e else '❌'}")
        rc = rc or (0 if ok_e2e else 1)
        # ── 变异：把去重判据短路成"永远是新签名"→ E1 同输入必翻红（证明判据在跑）──
        real = reminder_is_new
        try:
            reminder_is_new = lambda sig, state_path=None: (True, None)
            open(counter, "w").close()
            main(); main()
            n = len(open(counter).read().strip().split("\n")) if os.path.exists(counter) else 0
        finally:
            reminder_is_new = real
        ok_mut = (n == 2)
        print(f"  变异体 去重短路→两跑写入 {n} 条（应为 2·若仍为 1 说明 e2e 从未触达判据）：{'✅' if ok_mut else '❌'}")
        rc = rc or (0 if ok_mut else 1)
    finally:
        (DISTILLATION_CENTER, LOG_SCRIPT, BANNER_SCRIPT, REMINDER_STATE, reminder_is_new) = keep
    print("MUT:" + ("OK" if rc == 0 else "FAIL") + f" 蒸馏调度器去重自证（{len(cases)} 夹具＋E1＋变异 1）")
    return rc


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        exit(run_self_test())
    exit(main())
