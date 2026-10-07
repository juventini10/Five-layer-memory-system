#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triwich_closeout_guard.py —— 三明智收尾三登记机械兜底（Stop 钩子）
Version: 1.3.0 (2026-09-18·S1/S3 判定从"时间差代理"改为"登记身份匹配"·第一性根治)

主矛盾（皮叔 2026-09-15 质询"三明治相关的技术应该可以自动化吧？不应该每次都让我来问"）：
  三明智收尾有**三个登记动作**——① seal 封口 ② 决策卡 FU 登记（record --followup）③ 阶段A采样台账补一行。
  但 Stop 链里**一条兜底都没有**：① 靠 SKILL.md 里"AI 要记得跑"；② ③ 的要求住在台账文档
  的收尾协议里、**SKILL.md 流程根本看不到它** → 必漏（2026-09-15 实证：#22 由你点名才补上；
  2026-09-17 实证：seal 12ad95e1287a88a4 封口后漏 FU 登记·并行端 06:32 手工补登 FU-22 才补上）。
  = 典型"靠人记得"结构，违反愿景①全自动化。

本守卫做什么（只做机器能做的，⛔不越界代写）：
  ① **漏补采样台账**——seal.log 链尾身份（台账行末列 `seal <指纹>`）是否已落在台账 → 显形报警 + 给出补法。
  ② **疑似未封口**——工作区本轮键文件 `steps/step0-determination-{ts}.md` 在窗口内新建，但 seal.log
     窗口内无新链尾 → 显形报警 + 给出封口命令。
  ③ **漏决策卡 FU 登记**（v1.1.0 新增）——seal 链尾 `(ts, session)` 是否已在 decision-room 出现对应登记
     → 显形报警 + 给出补法。
  ④ 附**哲学三回流提醒**（改了脚本/Skill 时该更新的三处）——提示层，不判定。

判定范式（v1.3.0·2026-09-18 第一性根治）：**直接证据优先于代理信号**。
  原 ①③ 用“时间差 + mtime 代理”：mtime 只答“文件被动过”，不答“有没有这一条”——
  无关编辑重置它（假阴性），补了别人的行也满足它（假阳性）。现改**身份匹配**：
  链尾 `ts|session|seal` 为身份，台账行/决策卡登记行各自携带可验证凭据。
  证据分三级：strong（身份命中）→ 出定论；weak（无身份凭据可验）→ 仅出 hint 不出 finding；
  不可判（如台账自称链长超前于实链长）→ 交人工，⛔不降级成“漏补”定论。

⛔ 本守卫**不代写台账内容**——样本内容（任务/卡点/深度匹配）需 AI 判读，编造=踩采样红线
   "⛔不编造样本·没跑真实任务就不填"。机器只负责"追"，不负责"编"。
⛔ 不阻断（exit 0）：Hook 纪律（与守卫规范 §3.3 抗体"只记录不拦截"同族）；⛔DO NOT 让提示变拦截。

接口契约（registry_guards 族 / Stop 直挂通用）：--check 输出含 "alarm": true|false 的 JSON；--report 人类可读。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import subprocess
import sys
import time

VERSION = "1.3.2"  # 1.3.2（2026-10-05）：MC_CANDIDATES_HOME 语义修正（HOME 本身→HOME 下子目录名），根治负向注入假命中（f84d9401 匿名化对象写错·tests [2] 拦截）。历史：1.3.1（2026-09-19）SESSION_RX 截断修复——旧式 `[^\s·]+` 在多字工具名处截成 "Qoder"，S3 恒假红（WorkBuddy 单词名免疫故从未暴露）
HOME = os.path.expanduser("~")


# ── 记忆共享中心根探测（v1.2.0·2026-09-18·换机/对外可用性根治） ──
# 原实现把 HOME 下个人绝对路径写死（~/个人AI档案/...）→ 换机器/换用户名/对外分发包时
# 全部失效，S1/S2/S3 静默放行——**比误报更危险：守卫看起来在岗实际零判定**。
# 探测优先级：①包内自我定位 ②env 覆盖 ③HOME 候选。皆失败→显式 skipped，⛔不静默。
MC_CANDIDATES_ENV = ("TRIWICH_MC", "MEMORY_CENTER")
MC_CANDIDATES_HOME = ("[记忆共享中心]", "[日记仓库]")  # 1.3.2根治(2026-10-05)：原 (os.path.expanduser("~"),…) 把 HOME 本身当 MC 候选——join(HOME,HOME)=HOME 必假命中，孤立环境负向测试当场逮住（f84d9401 匿名化时对象写错：MC 根是 HOME 的子目录不是 HOME）


def detect_mc():
    """返回记忆共享中心根路径，失败返回 None。

    优先级（显式意图 > 自动探测）：
    ①env：TRIWICH_MC / MEMORY_CENTER——**最高优先**（沙盒测试/多机部署/换机迁移的唯一可靠开关；
      若被自动探测抢先，则沙盒改不动真实目录=测试性缺陷，2026-09-18 实测纠正）。
    ②自我定位：从本文件向上找第一个「含 技能配置/ 子目录」的祖先——
      随包安装到 <MC>/技能配置/triwich/scripts/ 与本机 <MC>/开发工具/ 两种位置均正确命中。
    ③HOME 候选：向后兼容既有安装。
    每级均做 realpath（macOS /tmp→/private/tmp 符号链接下保持路径可比对）。
    """
    for name in MC_CANDIDATES_ENV:
        v = os.environ.get(name)
        if v and os.path.isdir(v):
            return os.path.realpath(v)
    d = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    for _ in range(4):
        parent = os.path.dirname(d)
        if not parent or parent == d:
            break
        d = parent
        if os.path.isdir(os.path.join(d, "技能配置")):
            return d
    for name in MC_CANDIDATES_HOME:
        p = os.path.join(HOME, name)
        if os.path.isdir(p):
            return os.path.realpath(p)
    return None


MC = detect_mc()
TRIWICH_DIR = os.path.join(MC, "技能配置/triwich") if MC else None
SKILL_DIRS = [os.path.join(HOME, ".workbuddy/skills/triwich")]
if TRIWICH_DIR:
    SKILL_DIRS.append(TRIWICH_DIR)
SAMPLE_LEDGER = os.path.join(MC, "自定义层/待完成工作/阶段A采样清单-三明智4.0.md") if MC else None
DECISION_ROOM = os.path.join(TRIWICH_DIR, "references/decision-room.md") if TRIWICH_DIR else None
PHILO_DIR = os.path.join(MC, "记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学") if MC else None

WINDOW_SEC = 6 * 3600      # 判定窗口：6 小时内有三明智活动才算"本轮"
LAG_TOLERANCE = 120        # 旧口径回退容忍（仅用于"无身份凭据可验"的降级场景）
SEAL_RX = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\|")
FU_REG_RX = re.compile(r"登记：\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)")
# 会话身份 = "{工具名}:{hash}"，而**工具名普遍含空格**（Qoder CN / Qoder Desktop /
# DeepSeek Harness / WorkBuddy 唯一例外）。旧判据 `会话:([^\s·]+)` 在第一个空格处截断
# ⇒ 多字端一律只拿到 "Qoder" ⇒ 与链上完整身份永不相等 ⇒ S3 **假红**（登记明明在位仍报
# "决策卡无本轮登记"）。WorkBuddy 单词名恰好免疫，故该缺陷只在非 WB 端显形（2026-09-19
# Qoder CN 实跑命中：FU-40 已在位仍被报 S3）。修法＝截到 " · " 或行尾。
SESSION_RX = re.compile(r"会话:(.+?)(?:\s+·|$)")

# ── 登记身份匹配（v1.3.0·2026-09-18·第一性根治） ──
# 原实现用"时间差 + mtime"代理回答"本轮登记补了吗"——但封口与登记的对应关系本来就在文件里：
#   · seal.log 每条 = ts|session|seal|prev|hash   → 本轮身份 = (ts, session, seal)
#   · 台账行   = `seal 5a7a9cc3e3802904（链长36）`   → 强凭据：直接含 seal 指纹
#   · 决策卡行 = `登记：{ts} · … · 会话:{session}`       → 强凭据：ts+session 与链逐字对应
# mtime 只回答"文件被动过"，不回答"有没有这一条"：无关编辑重置它（假阴性），补了别的行也满足它（假阳性）。
# 故证据分三档：strong（指纹/身份命中）→ 判定；weak（mtime 新于 seal 但无身份命中）→ 降级不报只出 hint；
# none（mtime 落后）→ 报 finding 并附【证据强度：弱】。
SEAL_HEX_RX = re.compile(r"\b[0-9a-f]{16}\b")
DECLARED_RX = re.compile(r"(链长|seal_count|记录数)\D{0,4}(\d+)")


def _seal_log():
    for d in SKILL_DIRS:
        p = os.path.join(d, "scripts/seal.log")
        if os.path.isfile(p):
            return p
    return None


def _seal_identity(log_path):
    """返回本轮身份 dict：{t, ts, session, seal, prev, raw, chain_len} 或 None。

    v1.3.0 重构：S1/S3 判定改靠**身份匹配**而非时间差，故需完整字段而非只有 epoch。
    """
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
            lines = [l for l in fh.read().split("\n") if l.strip()]
    except (IOError, OSError):
        return None
    if not lines:
        return None
    last = lines[-1]
    m = SEAL_RX.match(last)
    if not m:
        return None
    try:
        t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
    except (ValueError, OverflowError):
        return None
    parts = last.split("|")
    if len(parts) < 3:
        return None
    return {"t": t, "ts": parts[0], "session": parts[1], "seal": parts[2],
            "raw": last, "chain_len": len(lines)}


def _last_seal(log_path):
    """兼容保留：返回 (epoch, raw_line)。"""
    ident = _seal_identity(log_path)
    return (ident["t"], ident["raw"]) if ident else (None, None)


def _ledger_probe(seal_hex, chain_len):
    """核验台账是否含本轮 seal 指纹。返回 dict {verdict, reason}。

    verdict ∈ hit（含本节指纹·强凭据）/ miss（指纹体系中但无本节）/ unknown（不可判）。
    unknown 的两种来由：①台账自称"链长 N" > 实链长 —— 台账**超前于链**（自称的记录不存在），
    属自相矛盾，交人工而非归为"漏补台账"；②文件不可读/不存在。
    """
    if not SAMPLE_LEDGER or not os.path.isfile(SAMPLE_LEDGER):
        return {"verdict": "unknown", "reason": "台账文件不存在或未配置"}
    try:
        body = open(SAMPLE_LEDGER, "r", encoding="utf-8", errors="replace").read()
    except (IOError, OSError):
        return {"verdict": "unknown", "reason": "台账不可读"}
    declared = [int(n) for _, n in DECLARED_RX.findall(body)]
    if declared and max(declared) > chain_len:
        return {"verdict": "unknown",
                "reason": "台账自称链长 %d > 实链长 %d（台账超前于链·自相矛盾）"
                          % (max(declared), chain_len)}
    if seal_hex in body:
        return {"verdict": "hit", "reason": "含本轮 seal 指纹"}
    return {"verdict": "miss", "reason": "无本轮 seal 指纹"}


def _fu_registered(ts, session):
    """decision-room 是否含与 (ts, session) 精确对应的登记（强凭据）。返回 bool|None。

    决策卡行原形：`- 登记：2026-09-17 17:20:28 · 发起方式:机制封口自动登记 · 会话:WorkBuddy:72756ac71b41`
    ⛔ 未带会话字段的老式行 → 不能给结论（身份不完备），只回 False 不参与强判定。
    """
    if not DECISION_ROOM or not os.path.isfile(DECISION_ROOM):
        return None
    try:
        fh = open(DECISION_ROOM, "r", encoding="utf-8", errors="replace")
    except (IOError, OSError):
        return None
    saw_identity_line = False
    with fh:
        for line in fh:
            m = FU_REG_RX.search(line)
            if not m:
                continue
            t_txt = m.group(1)
            m2 = SESSION_RX.search(line)
            if not m2:
                continue
            saw_identity_line = True
            got = m2.group(1).strip()
            # 秒位缺失时，与链上 ts 的前 16 位对齐后必相等
            if t_txt[:16] == ts[:16] and got == session:
                return True
    # 文件里一条带会话的登记都没有 → 身份方案不适用（老式文件）→ 不可判，交回退
    return False if saw_identity_line else None


def _last_fu_register():
    """返回 decision-room 最新 FU 登记时间的 epoch（解析所有 `登记：` 行取最大）。

    与 _last_seal 同构：S3 判定用——seal 比最新 FU 登记晚 → 封口了但决策卡没登记。
    """
    if not os.path.isfile(DECISION_ROOM):
        return None
    latest = None
    try:
        with open(DECISION_ROOM, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = FU_REG_RX.search(line)
                if not m:
                    continue
                try:
                    t = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                except (ValueError, OverflowError):
                    continue
                if latest is None or t > latest:
                    latest = t
    except (IOError, OSError):
        return None
    return latest


def _steps_candidates(cwd):
    """steps/ 里近窗口内新建的判定文件（用于判"跑了三明智但没封口"）。

    v1.0.1（2026-09-16）扫描域修复：原实现只扫 cwd/steps——但三明智键文件的
    规范铸造位是 技能配置/triwich/steps/（技能中心固定路径），非会话工作区；
    在 cwd≠技能配置夹的会话里 S2 检查必然放行（2026-09-16 16:09 轮实测漏拦）。
    现固定扫 [技能配置/triwich/steps, cwd/steps（若存在）] 两处，去重按 (name, mtime)。
    """
    out = []
    now = time.time()
    seen = set()
    steps_dirs = []
    if TRIWICH_DIR:
        steps_dirs.append(os.path.join(TRIWICH_DIR, "steps"))
    if cwd:
        steps_dirs.append(os.path.join(cwd, "steps"))
    for steps in steps_dirs:
        if not steps or not os.path.isdir(steps):
            continue
        try:
            for name in os.listdir(steps):
                if not name.startswith("step0-determination-") or name.endswith(".bak"):
                    continue
                full = os.path.join(steps, name)
                try:
                    mt = os.stat(full).st_mtime
                except OSError:
                    continue
                if now - mt <= WINDOW_SEC and (name, mt) not in seen:
                    seen.add((name, mt))
                    out.append((name, mt))
        except OSError:
            pass
    return sorted(out, key=lambda x: -x[1])


def _recent_script_change():
    """近 1 小时内是否改过脚本/Skill（决定要不要附带哲学三回流提醒）。"""
    now = time.time()
    roots = [os.path.join(MC, "开发工具")] if MC else []
    for base in ("技能配置",):
        p = os.path.join(MC, base) if MC else None
        if p and os.path.isdir(p):
            try:
                for d in os.listdir(p):
                    sp = os.path.join(p, d, "SKILL.md")
                    if os.path.isfile(sp) and now - os.stat(sp).st_mtime <= 3600:
                        return True
            except OSError:
                pass
    for root in roots:
        if not os.path.isdir(root):
            continue
        n = 0
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if not d.startswith((".", "__"))]
                for fn in filenames:
                    if not fn.endswith((".py", ".sh")):
                        continue
                    n += 1
                    if n > 400:            # 有界扫描·防大目录拖慢 Stop 链
                        return False
                    try:
                        if now - os.stat(os.path.join(dirpath, fn)).st_mtime <= 3600:
                            return True
                    except OSError:
                        continue
        except OSError:
            continue
    return False


def check(cwd):
    """返回 dict：alarm / findings / hints"""
    findings = []
    if not MC:
        return {"alarm": False, "version": VERSION, "mc": None,
                "skipped": "记忆共享中心根探测失败（试过：包内自我定位/env TRIWICH_MC|MEMORY_CENTER/HOME 候选）——⛔不静默放行，请设 TRIWICH_MC 指向共享中心",
                "findings": [], "hints": []}
    log = _seal_log()
    if not log:
        return {"alarm": False, "version": VERSION, "mc": MC,
                "skipped": "seal.log 缺失", "findings": [], "hints": []}

    ident = _seal_identity(log)
    if not ident:
        return {"alarm": False, "version": VERSION, "mc": MC,
                "skipped": "seal.log 无可解析链尾", "findings": [], "hints": []}
    t_seal = ident["t"]
    now = time.time()
    if (now - t_seal) > WINDOW_SEC:
        return {"alarm": False, "version": VERSION, "mc": MC,
                "skipped": "窗口内无三明智封口", "findings": [], "hints": []}

    seal_when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_seal))

    # ① 漏补采样台账：先用**seal 指纹身份**判定；指纹不可判时才回退时间差
    led = {"verdict": "unknown", "reason": "未配置台账"}
    weak_s1 = None
    if SAMPLE_LEDGER and os.path.isfile(SAMPLE_LEDGER):
        led = _ledger_probe(ident["seal"], ident["chain_len"])
        mtime = os.stat(SAMPLE_LEDGER).st_mtime
        lag = t_seal - mtime
        if led["verdict"] == "miss":
            findings.append({
                "code": "S1",
                "msg": "三明智已封口但采样台账无本轮记录",
                "detail": "封口=%s · seal 指纹 %s 未出现在台账（强凭据判定）"
                          % (seal_when, ident["seal"]),
                "fix": "在 %s 的 §三 台账补一行（任务简述/深度/卡点环节/深度匹配/需回访/已回访/补充）"
                       "，末列写 `seal %s（链长%d）`——⛔不编造，没跑真实任务就不填"
                       % (os.path.basename(SAMPLE_LEDGER), ident["seal"], ident["chain_len"]),
            })
        elif led["verdict"] == "unknown" and lag > LAG_TOLERANCE:
            weak_s1 = ("封口=%s · 台账最后改动=%s（落后 %.0f 分钟）· %s"
                       % (seal_when, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)),
                          lag / 60.0, led["reason"]))

    # ② 疑似未封口：工作区本轮键文件存在但 seal.log 窗口内无对应新链尾
    for name, mt in _steps_candidates(cwd)[:1]:
        # 键文件比末次封口晚 120s 以上 = 最后一次三明智活动未被封口
        if mt > t_seal + 120:
            findings.append({
                "code": "S2",
                "msg": "三明智判定文件已生成但疑似未封口",
                "detail": "本轮键文件=%s（%s）· seal.log 末条=%s"
                          % (name, time.strftime("%H:%M:%S", time.localtime(mt)), seal_when),
                "fix": 'python3 <triwich>/scripts/triwich_seal.py record --tool <端名> '
                       "--text-file /tmp/triwich_block_<ts>.txt --followup \"…\" --predict \"…\" --window \"…\" --depth L<N>",
            })
        break

    # ③ 漏决策卡 FU 登记：先用**身份匹配**（链上 ts+session 是否已出现在决策卡）；
    #    身份不可判时才回退时间差（附证据强度）。
    strong_fu = _fu_registered(ident["ts"], ident["session"])
    t_fu = _last_fu_register()
    weak_s3 = None
    if strong_fu is False:
        findings.append({
            "code": "S3",
            "msg": "三明智已封口但决策卡无本轮登记",
            "detail": "封口=%s · 会话=%s · 链上此轮身份在 decision-room 中未找到对应登记（强凭据判定）"
                      % (seal_when, ident["session"]),
            "fix": "在 decision-room.md 条目区补登 FU-{seq}（任务/深度/预测/回访窗口/登记——"
                   "登记行须含 `登记：%s · 发起方式:… · 会话:%s`，参照 FU-19/FU-22 手工补登先例·"
                   "⛔不编造·本轮未走完三明智流程则不补），"
                   "或确认本轮 seal 为误操作（对齐 FU-10 作废先例·状态标作废不占计数）"
                   % (seal_when, ident["session"]),
        })
    elif strong_fu is None and t_fu is not None and t_seal - t_fu > LAG_TOLERANCE:
        # 身份不可判（老式无会话字段）→ 降级为提示，不进 findings（⛔不用弱证据报定论）
        weak_s3 = ("decision-room 最新 FU 登记=%s（落后 %.0f 分钟）· 登记行不含会话字段身份不可判"
                   % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_fu)),
                      (t_seal - t_fu) / 60.0))

    hints = []
    if weak_s1:
        hints.append("⚠️ S1 证据强度弱·待确认：%s —— 若已补登请为台账行加 `seal <指纹>（链长N）` 以保身份可验" % weak_s1)
    if weak_s3:
        hints.append("⚠️ S3 证据强度弱·待确认：%s —— 若已补登请为登记行补会话字段以保身份可验" % weak_s3)
    if _recent_script_change():
        hints.append("本轮改过脚本/Skill → 哲学回流三查：①对应编写规范 ②03-进度看板变更记录 ③02-脚本家族实例")

    return {
        "alarm": bool(findings),
        "version": VERSION,
        "mc": MC,
        "seal": seal_when,
        "findings": findings,
        "hints": hints,
    }


def report(res):
    if res.get("skipped"):
        return  # 窗口内无三明智活动 → 静默（安静时静默·异常时必须响）
    if not res.get("findings"):
        extra = ("　｜　" + "；".join(res.get("hints", []))) if res.get("hints") else ""
        print("✅ 三明智收尾三登记：无漏项（封口 %s）%s" % (res.get("seal", ""), extra))
        return
    print("⚠️ 三明智收尾三登记告警（%d 项）" % len(res["findings"]))
    for f in res["findings"]:
        print("   [%s] %s" % (f["code"], f["msg"]))
        print("        %s" % f["detail"])
        print("        补法：%s" % f["fix"])
    for h in res.get("hints", []):
        print("   💡 %s" % h)


def main():
    argv = sys.argv[1:]
    res = check(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--report" in argv:
        report(res)
    else:
        print(json.dumps(res, ensure_ascii=False))
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