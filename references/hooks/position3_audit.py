#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""position3_audit.py — 岗位3「声明-实盘对账官」对账引擎（童灵扩展岗位·2026-08-29 你批准）。

设计定位（04-发展路线图三闸申报获批 · steps/position3-declaration-audit-proposal.md）：
  童灵"守护"职能的周期性执行位——对账各端"文档声明"与"运行时台账实锤"，
  把"说做了"与"真做了"的落差在 48h 内机械显形，不依赖你质疑（愿景①不依赖人记得）。

对账判据（改判据须升版本并在报告标注·S870 纪律）：
  ① 悬置声明：设计哲学文件中"待下轮实锤"类未兑现承诺，行内日期起算超 48h → 🔴；
  ② 台账健康度：童灵守卫/注入台账 存在性·新鲜度(≤7天)·载荷真实性(运行时键数≥10)；
  ③ 切片新鲜度：各端恒驻文件内嵌 core_slice 与 slices/ 当前产物逐字比对；
  ④ 暂存区水位（v1.2 入）：git staged 超阈→观察模式，连续两轮→机械归位；
  ⑤ 定时作业健康度（v1.3 入）：launchd 作业 脚本存在性·加载态·退出码诚实性·产物时效
     （vs 宣称频率）——缘起=com.knowledge.backup 静默死 23 天，判据①-④对这一类结构性失明。
     v1.4 补：常驻作业(KeepAlive)判活改由 `launchctl print state` 实锤；WatchPaths 指向
     不存在文件→🔴（事件永不触发）；stdout 弱证据仅在真有周期时计时效（其余显式报盲区）。

纪律（02规范§五.3 守护自限 + 守卫三纪律）：
  只读+只写报告/台账——不修改任何被对账文件、不代改登记状态（异常清单呈你）；
  失败默认放行（异常 exit 0 绝不制造 launchd 噪音）；台账 O_APPEND 可观测。
产出：
  报告 steps/position3-reconciliation-report.md（滚动覆盖·写前 .bak·处置记录节回显历史归档）
  台账 steps/position3-audit-log.jsonl（单行 JSON·rec.dispositions=处置记录累积快照·供 evolution_deviation.py 闭环流并入）
用法：
  python3 position3_audit.py            # 对账一轮
  python3 position3_audit.py --selfcheck  # 挂载自检（三要素）
  python3 position3_audit.py --negtest    # 判据⑤逐分支负例实测（S064·临时目录伪造）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

BASE = os.path.expanduser("[记忆共享中心]")
PHIL = os.path.join(BASE, "记忆蓝图/04_系统文件设计/数字分身设计哲学")
STEPS = os.path.join(BASE, "数字分身/steps")
SLICES = os.path.join(BASE, "数字分身/K2切片蒸馏/slices")

AUDIT_FILES = [
    os.path.join(PHIL, "03-进度看板.md"),
    os.path.join(PHIL, "06-跨端适配规范.md"),
]
REPORT = os.path.join(STEPS, "position3-reconciliation-report.md")
AUDIT_LOG = os.path.join(STEPS, "position3-audit-log.jsonl")

# 悬置声明模式（未兑现承诺的自认表述）+ 阴性排除（已兑现/勘误表述）
PENDING_PATTERNS = [
    r"待下轮[^，。;）|]*实锤",
    r"待下次[^，。;）|]*实锤",
    r"待[^，。;）|]{0,6}消息投递实锤",
    r"待[^，。;）|]{0,8}用户提交实锤",
    r"真实触发台账待[^，。;）|]{2,20}",
]
RESOLVED_MARKERS = ["兑现", "已修正", "已兑现", "修正为误判"]  # 行内含此=已闭环·不计悬置
STALE_DAYS = 2          # 悬置超阈（提案 48h）
LEDGER_FRESH_DAYS = 7   # 台账新鲜度阈值

# 各端童灵台账（守卫+注入）
LEDGERS = {
    "WB守卫": os.path.expanduser("~/.workbuddy/doenglingz_guard_state.json"),  # 持久化根治 /tmp 重启易失误报🔴（守卫经 registry_guards.sh 已挂载）
    "ZCode守卫": os.path.expanduser("~/.zcode/doenglingz_guard_state_zcode.json"),  # 2026-10-06 SSOT归一迁端根（env双键显式·守卫=共脚本 doenglingz_guard.py --check --src zcode）；原 ~/.workbuddy 侧存量446行(pre-fix历史)+3行分叉尾档留原处不删
    "QoderCN守卫": os.path.expanduser("~/.workbuddy/doenglingz_guard_state_qodercn.json"),  # 持久化·v1.6迁移~/.workbuddy/时漏改·2026-09-02处置：真ledger落点在此(/tmp重启易失致假红)
    "注入(WB/QCN)": os.path.expanduser("~/.workbuddy/doenglingz_inject_state.json"),  # 实盘由 UserPromptSubmit 钩子 doenglingz_inject_prompt.py 实时写入~/.workbuddy/；/tmp/ 是 zcode 守卫死路径(未跑)→误报🔴已校正
    "注入(ZCode)": os.path.expanduser("~/.zcode/doenglingz_inject_state.json"),  # 2026-10-06 端根显式（env双键）后本端注入账落 ~/.zcode；首条=下一会话首提示落，此前缺失→走 LEDGER_GUARDS 挂载锚降🟡待命
    "DSH守卫": os.path.expanduser("~/.dsh/doenglingz_guard_state.json"),  # 2026-09-27 补册：DSH 端 Stop 台账此前不在任何巡检视野内（本引擎每日对账的"声称覆盖≠真覆盖"同构病·实测末条停在 09-10）
}

# 各端守卫"挂载态"锚点：台账缺失时回退查"守卫是否已在对应端 hooks 配置挂载"。
# 已挂载但端休眠/未触发→降级🟡(休眠待命)而非🔴(脱钩)；完全未挂载→仍🔴。
LEDGER_GUARDS = {
    "WB守卫": (os.path.expanduser("~/.workbuddy/settings.json"), "doenglingz_guard.sh"),
    "ZCode守卫": (os.path.expanduser("~/.zcode/cli/config.json"), "doenglingz_guard.py"),  # 2026-10-06 SSOT归一：锚点改共脚本活态命令（分叉名退役）
    "注入(ZCode)": (os.path.expanduser("~/.zcode/cli/config.json"), "doenglingz_inject_prompt.py"),  # 2026-10-06 补册：端根注入台账缺失时的挂载兜底
    "DSH守卫": (os.path.expanduser("~/.dsh/profiles/web/node_modules/five-layer-memory/src/index.js"),
                "doenglingz_guard_dsh.py"),  # DSH 无 settings.json，挂载锚=插件 STOP_GUARDS 声明处（实测 2 处命中）
}

# 各端恒驻文件内嵌切片 vs 当前产物（v1 只核 ZCode/AutoClaw 标记对形态·QoderCN frontmatter 形态轻核存在性）
EMBED_CHECKS = {
    "ZCode/AGENTS.md": os.path.expanduser("~/.zcode/AGENTS.md"),
    "AutoClaw/USER.md": os.path.expanduser("~/.openclaw-autoclaw/workspace/USER.md"),
}
# v1.9（2026-09-23·皮叔令"没做的根治"·本端盲区消除）：全文件形态端（无标记对，生成器整文件装配）
# 病灶：注释声称"QoderCN frontmatter 形态轻核存在性"但 dict 里根本没有本端条目=声称与实施脱钩
# （正是本引擎每日对账的病）。本端 content 已实测 39 锚点/0 缺失后入册，首响无假红。
EMBED_FULLFILE_CHECKS = {
    "QoderCN/rules/doenglingz-core.md": (
        os.path.expanduser("~/.qoder-cn/rules/doenglingz-core.md"),
        ("core_slice.md", "L6_反向约束.md")),
}
CORE_START = "<!-- K2 core_slice 开始"
L6_START = "<!-- L6 反向约束 开始"


def _sha_or_none(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except Exception:
        return None


def _load_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except Exception:
        return []


CHANGELOG_HEADER = "## 变更记录"  # 其后=历史快照区（append-only·当时态不按当前悬置计）


def _current_zone(lines):
    """返回当前态区行数上界（变更记录历史区之前的行数）。"""
    for i, line in enumerate(lines, 1):
        if line.strip().startswith(CHANGELOG_HEADER):
            return i - 1
    return len(lines)


def check_pending_claims():
    """判据①(v1.1)：悬置声明检测——只扫当前态区（排除变更记录历史快照）。
    返回 [(file, lineno, text, days_or_None, level, resolved_in_changelog)]"""
    out = []
    now = datetime.now()
    for path in AUDIT_FILES:
        fname = os.path.basename(path)
        lines = _load_lines(path)
        cur_end = _current_zone(lines)
        changelog_text = "".join(lines[cur_end:])  # 历史区全文·用于兑现词回扫
        for i, line in enumerate(lines, 1):
            if i > cur_end:
                break  # v1.1 修正①：历史快照区不按当前悬置计（首轮误报实证：L112/L120/L130 均为变更记录条目）
            for pat in PENDING_PATTERNS:
                m = re.search(pat, line)
                if not m:
                    continue
                if any(k in line for k in RESOLVED_MARKERS):
                    continue  # 行内自证已闭环
                # 悬置起点：行内/就近上方 20 行内的最近日期
                days = None
                dm = re.search(r"(20\d{2}-\d{2}-\d{2})", line)
                if not dm:
                    for j in range(i - 2, max(0, i - 22), -1):
                        dm = re.search(r"(20\d{2}-\d{2}-\d{2})", lines[j - 1])
                        if dm:
                            break
                if dm:
                    try:
                        days = (now - datetime.strptime(dm.group(1), "%Y-%m-%d")).days
                    except ValueError:
                        days = None
                level = "🔴" if (days is not None and days > STALE_DAYS) else "🟡"
                # v1.1：兑现词回扫——历史区若已记录兑现，则属"登记未回改"（仍是悬置·建议动作不同）
                resolved = any(k in changelog_text for k in ["兑现", "已修正"]) and                     m.group(0)[:8] in changelog_text
                out.append((fname, i, m.group(0), days, level, resolved))
                break
    return out


def check_ledgers():
    """判据②：台账健康度。返回 [(name, verdict, detail)]"""
    out = []
    now = datetime.now()
    for name, path in LEDGERS.items():
        if not os.path.exists(path):
            # v1.6 挂载态兜底：已挂载但端休眠/未触发≠脱钩→🟡；真未挂载才🔴
            m = LEDGER_GUARDS.get(name)
            mounted = False
            if m:
                cfg, base = m
                try:
                    if os.path.exists(cfg) and base in open(cfg, encoding="utf-8", errors="ignore").read():
                        mounted = True
                except Exception:
                    mounted = False
                # 间接挂载（registry 自动发现类）：守卫文件存在于已知守卫目录即视为已挂载
                if not mounted:
                    for d in (os.path.expanduser("[记忆共享中心]/脚本中心"),):
                        if os.path.exists(os.path.join(d, base)):
                            mounted = True
                            break
            if mounted:
                out.append((name, "🟡", "守卫已挂载 hooks 但端休眠/未触发·无运行时台账（非脱钩·待命）"))
            else:
                out.append((name, "🔴", "台账文件不存在（守卫从未触发或 台账被清·selfcheck 兜底项）"))
            continue
        recs = []
        for line in _load_lines(path):
            try:
                recs.append(json.loads(line))
            except Exception:
                pass
        if not recs:
            out.append((name, "🔴", "台账存在但零可解析记录"))
            continue
        last = recs[-1]
        try:
            # 时间键容两型：WB/ZCode 系用 ts，DSH 适配器用 last_run（只认 ts 会把在跑的端读成"不可解析"＝仪器失明）
            ts = datetime.strptime(str(last.get("ts") or last.get("last_run") or "")[:19], "%Y-%m-%dT%H:%M:%S")
            age_days = (now - ts).days
        except Exception:
            age_days = None
        issues = []
        ts_disp = str(last.get("ts") or last.get("last_run") or "?")[:16]
        if age_days is None:
            issues.append("末条时间戳不可解析")
        elif age_days > LEDGER_FRESH_DAYS:
            issues.append("末条距今 %d 天(>%d)" % (age_days, LEDGER_FRESH_DAYS))
        if "stdin_keys" in last:
            n_keys = len([k for k in str(last.get("stdin_keys", "")).split(",") if k.strip()])
            if n_keys < 10 and "注入" not in name:
                issues.append("末条载荷键数 %d<10 疑似测试载荷" % n_keys)
            detail = "末条 %s·键数%d·%s" % (ts_disp, n_keys,
                                            "；".join(issues) if issues else "健康")
        else:
            # v1.1 修正②：schema 无 stdin_keys（如 QoderCN 旧版同构）→ 只判新鲜度·不套载荷口径（首轮误报实证）
            detail = "末条 %s·schema无stdin_keys字段·%s" % (ts_disp,
                                                             "；".join(issues) if issues else "健康")
        out.append((name, "🟡" if issues else "✅", detail))
    return out


def check_embeds():
    """判据③：恒驻文件内嵌切片新鲜度。返回 [(name, verdict, detail)]"""
    out = []
    core_cur = _sha_or_none(os.path.join(SLICES, "core_slice.md"))
    if core_cur is None:
        return [("slices/core_slice.md", "🔴", "当前切片产物不可读")]
    for name, path in EMBED_CHECKS.items():
        if not os.path.exists(path):
            out.append((name, "🔴", "恒驻文件不存在"))
            continue
        cur = open(path, encoding="utf-8").read()
        i1, i2 = cur.find(CORE_START), cur.find(L6_START)
        if not (0 <= i1 < i2):
            out.append((name, "🔴", "无 core_slice 标记对（岗位3 v1 不覆盖此形态·须人工核）"))
            continue
        emb = cur[cur.find("\n", i1) + 1:i2].strip()
        emb = emb[:emb.rfind("<!-- K2 core_slice 结束 -->")].strip() if "<!-- K2 core_slice 结束 -->" in emb else emb
        emb_sha = hashlib.sha256(emb.encode()).hexdigest()[:12]
        # 与当前产物逐字比对（内容级）
        core_full = open(os.path.join(SLICES, "core_slice.md"), encoding="utf-8").read().strip()
        ok = emb == core_full
        out.append((name, "✅" if ok else "🔴",
                    "内嵌 vs slices/ 逐字%s（emb %s / cur %s）" % ("一致" if ok else "不一致·漂移", emb_sha, core_cur)))
    # ── 全文件形态端（v1.9）：锚点行（- / ## / ###）对 slices 100% 覆盖检查 ──
    for name, (path, _slices) in EMBED_FULLFILE_CHECKS.items():
        if not os.path.exists(path):
            out.append((name, "🔴", "恒驻文件不存在")); continue
        body = open(path, encoding="utf-8").read()
        anchors, miss, broken = 0, [], False
        for sf in _slices:
            sp = os.path.join(SLICES, sf)
            if not os.path.exists(sp):
                out.append((name, "🔴", "切片产物缺失 " + sf)); broken = True; break
            for l in open(sp, encoding="utf-8"):
                t = l.strip()
                if t.startswith(("- ", "## ", "### ")):
                    anchors += 1
                    if t not in body:
                        miss.append(t[:60])
        if broken:
            continue
        okf = anchors >= 20 and not miss
        out.append((name, "✅" if okf else "🔴",
                    "全文覆盖核 锚点%d·缺%d%s" % (anchors, len(miss),
                        "" if okf else ("（锚点<20=产物空壳嫌疑）" if anchors < 20 else "·例:"+miss[0]))))
    return out


STAGING_STATE = os.path.join(STEPS, "position3-staging-state.json")
STAGING_THRESHOLD = 500  # 水位阈（你批准 v1.2·触发观察）
STAGING_ROUNDS = 2       # 连续两轮超阈（周轮×2≈14天·对齐体系断链容忍先例）才自动归位
# 论证锚（triwich L1 修正）：堆积时长即无人认领的机械证明——staged 承载工作意图不可机械判定，
# 故不自动清单轮超阈；连续两轮（14天）无人消费=意图已消失，机械归位零意图损失。


def check_staging_water():
    """判据④：暂存区水位（观察模式先行：首轮超阈只显形记录·次轮仍超阈→自动归位+🔴）。
    返回 (level, detail, action)"""
    try:
        import subprocess
        r = subprocess.run(["git", "-C", BASE, "diff", "--cached", "--name-only"],
                           capture_output=True, text=True, timeout=30)
        count = len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception as e:
        return "🟡", "水位读数失败（%s）·失败放行" % str(e)[:60], "none"
    if count <= STAGING_THRESHOLD:
        # 归零即清状态
        if os.path.exists(STAGING_STATE):
            os.unlink(STAGING_STATE)
        return "✅", "staged %d ≤ %d" % (count, STAGING_THRESHOLD), "none"
    state = {}
    try:
        state = json.load(open(STAGING_STATE, encoding="utf-8"))
    except Exception:
        pass
    if not state.get("since"):
        state = {"since": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "rounds": 1}
        with open(STAGING_STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        return "🟡", "staged %d > %d·首次超阈→观察模式（记录 since，验读数）" % (count, STAGING_THRESHOLD), "observe"
    state["rounds"] = state.get("rounds", 1) + 1
    with open(STAGING_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    if state["rounds"] >= STAGING_ROUNDS:
        r2 = subprocess.run(["git", "-C", BASE, "restore", "--staged", "."],
                            capture_output=True, text=True, timeout=120)
        if r2.returncode == 0:
            os.unlink(STAGING_STATE)
            return "🔴", "staged %d 连续 %d 轮超阈→**已自动归位工作区**（非破坏·内容零损失·各端重新 add 即回）" % (count, state["rounds"]), "healed"
        return "🔴", "staged %d 超阈且自动归位失败（%s）·须人工" % (count, r2.stderr[:80]), "heal-failed"
    return "🟡", "staged %d 连续 %d 轮超阈（观察中·%s 起）" % (count, state["rounds"], state["since"][:10]), "observe"


# ============ 判据⑤：定时作业健康度（launchd 声明-实盘对账·v1.3 新增·v1.4 补判活） ============
CRITERIA_VERSION = "v1.11"  # 报告头部与分节标题共用（⛔不两处各写一次=防双本账）
# 缘起（2026-08-30 实证）：com.knowledge.backup 因 plist 脚本名手误 exit=127 静默死 23 天；
# 同日又查出 3 个 plist 指向已不存在的脚本且根本没加载。判据①-④ 全测不到这一类——
# "作业声称每日跑"与"台账实锤没跑"的落差必须机械显形（愿景①不依赖人记得）。
# 归属判据：认被调脚本路径不认 label 前缀（label 可被任何工具起任何名，路径才是资产归属实锤）。
LAUNCH_DIR = os.path.expanduser("~/Library/LaunchAgents")
OWN_ROOTS = (
    os.path.expanduser("[记忆共享中心]/"),
    os.path.expanduser("~/.qoder-cn/"),
    os.path.expanduser("~/重要备份/"),
)
JOB_GRACE = 2.5  # 产物最大容忍年龄 = 宣称周期 × 该系数
# 产物声明表（⚠️双本账风险：plist 不声明业务产物，此处只登记"脚本正文已取证"的落点。
# 未登记作业一律显式报 🟡 盲区，⛔不得当作"检查通过"——仪器盲区不豁免执行。）
#   kind: per-run=每轮必写(时效可判) / alarm-only=仅异常落笔(时效不可判·只判存在性)
JOB_ARTIFACTS = {
    "com.用户名.offsite-bundle-backup": ("[记忆共享中心]/脚本中心/offsite_bundle_backup.log", "per-run"),
    "com.knowledge.backup": ("[记忆共享中心]/脚本中心/knowledge-backup.log", "per-run"),  # 2026-10-06 订正：原指向 脚本中心/ 为迁移后旧址（盘上真实产物在 记忆系统自动化/）
    "com.buluotuo.position3-audit": ("[记忆共享中心]/数字分身/steps/position3-audit-log.jsonl", "per-run"),
    "com.用户名.check-skill-links": ("[记忆共享中心]/脚本中心/skill-symlink-guard/audit.log", "alarm-only"),  # 2026-10-06 订正：原键"com.用户名."占位符未替换→查表恒miss=「未登记产物声明」🟡根因；原路径"脚本中心/audit.log"不存在，真实产物在 开发工具/skill-symlink-guard/audit.log（symlink_guard.sh L28 唯一写入点）
}


def _launchctl_job(label):
    """(loaded, exit_code)。loaded=True/False/None(探测不可用·盲区)。
    用逐 label `launchctl print gui/$UID/<label>`（v1.5 起·替代 legacy `launchctl list`：
    后者在重启后/非交互 shell 返回空→误报『未加载』🔴）。与 _job_alive 同源可靠。
    'Could not find service' = 明确未加载（硬红）；超时/异常 = 盲区（None）。"""
    domain = "gui/%d/%s" % (os.getuid(), label)
    for _ in range(2):  # 偶发瞬时失败→重试一次
        try:
            r = subprocess.run(["launchctl", "print", domain],
                               capture_output=True, text=True, timeout=10)
        except Exception:
            return (None, None)
        if r.returncode != 0 or "Could not find service" in r.stderr:
            return (False, None)
        loaded = "path =" in r.stdout
        exit_code = None
        for line in r.stdout.splitlines():
            t = line.strip()
            if t.startswith("last exit code = "):
                exit_code = t[len("last exit code = "):].strip()
                break
        return (loaded, exit_code)
    return (None, None)


_CRASH_RE = None  # 延迟编译


def _rc_semantics(d, rc):
    """把 launchd 的 last exit code 分成三类，根治「检查器有发现」被误判成「作业崩了」。

    缘起（2026-09-26 第107轮实证）：4 处🔴里只有 1 处是真崩（panel_snapshot TypeError），
    另 3 处是检查器正常工作——`script_family_check.py --strict` 的 help 自己写着
    「任一红→exit 1」，`blueprint-index-watcher` stdout 末行「发现 2 个问题」，
    `changelog-audit` stdout `alarm: true`。判据原样把 rc≠0 一律记 hard，
    后果不是"多报 3 个红"，而是**真崩被假红淹没**（信噪比 1:3，狼来了）。

    分类判据（机械可判，⛔不依赖被检脚本自报语义）：
      crash   —— stderr 有异常特征（Traceback/Error/信号/找不到文件等）**且时效不旧于 stdout**（v1.10 时效闸）
      finding —— stderr 空且 stdout 有内容（检查器出了报告）→ 🟡 待处置，非故障
      unknown —— 两者皆无/读不到 → 保守留 🔴（宁可假红不可漏真崩）
    """
    import re as _re
    global _CRASH_RE
    if _CRASH_RE is None:
        _CRASH_RE = _re.compile(
            r"Traceback|Error:|error:|Exception|Segmentation|Abort|Killed|"
            r"command not found|No such file|Permission denied|not executable",
            _re.I)
    err = (d.get("StandardErrorPath") or "").strip()
    out = (d.get("StandardOutPath") or "").strip()

    def _tail(path, n=2):
        try:
            with open(path, "rb") as f:
                f.seek(max(0, f.seek(0, 2) - 8192))
                data = f.read().decode("utf-8", "replace").strip().splitlines()
            return data[-n:]
        except Exception:
            return []

    et = _tail(err) if err else []
    if et and _CRASH_RE.search("\n".join(et)):
        # v1.10 时效闸（2026-10-10 第148轮实证）：state-bus-sync 崩案已于前夜修复且复跑
        # stdout 新鲜、stderr 静默，但 err.log 里的旧 Traceback 残被无条件当现行证据→
        # 修好的作业永远真崩。判据：崩溃签名只在 stderr mtime ≥ stdout mtime（同轮或更晚）
        # 时算现行；旧于 stdout ⇒ 上一轮遗账·降级走 finding/unknown。
        # 保守性不变：取不到 stdout/比较异常时照旧 crash（宁可假红不漏真崩）。
        stale = False
        try:
            if out and os.path.exists(out):
                stale = os.path.getmtime(err) < os.path.getmtime(out) - 1.0
        except OSError:
            stale = False
        if not stale:
            return ("crash", et[-1][:110])
        et = []
    ot = _tail(out) if out else []
    if not et and ot:
        return ("finding", ot[-1][:110])
    if not et and not ot:
        return ("unknown", "")
    return ("unknown", (et or ot)[-1][:110])


def _launchctl_map():
    """label → 上次退出码（字符串）。逐 label 实查；取不到返回 {}（调用方须显形为盲区而非假通过）。
    v1.5：枚举 LAUNCH_DIR 下 plist，逐 label 调 _launchctl_job——修复 restart/非交互 shell 下
    `launchctl list` 返回空导致全部 own job 误报『未加载』🔴 的假红（2026-08-31 实证：手动补跑爆 27 假红）。"""
    m = {}
    try:
        files = glob.glob(os.path.join(LAUNCH_DIR, "*.plist"))
    except Exception:
        return {}
    for path in files:
        label = os.path.basename(path)[:-6]
        loaded, exit_code = _launchctl_job(label)
        if loaded is True:
            m[label] = exit_code if exit_code not in (None, "(never exited)") else "0"
    return m


def _plist_scripts(d):
    """提取被调脚本绝对路径：兼容 args 直给、`bash -c "...py..."` 包装（相对名按 WorkingDirectory 解析）、ScriptFile。"""
    wd = d.get("WorkingDirectory") or ""
    out = []

    def add(tok):
        tok = os.path.expanduser(str(tok).strip().strip('"').strip("'"))
        if not tok.startswith("/"):
            if not wd:
                return
            tok = os.path.normpath(os.path.join(wd, tok))
        if tok not in out:
            out.append(tok)

    for a in d.get("ProgramArguments") or []:
        a = str(a)
        if a.endswith((".sh", ".py")):
            add(a)
            continue
        for m in re.finditer(r"(?:^|[\s&;|(])([^\s&;|()]*\.(?:sh|py))", a):
            add(m.group(1))
    if d.get("ScriptFile"):
        add(d["ScriptFile"])
    return out


def _cadence(d):
    """(周期秒 or None, 标签, 时效是否适用)。"""
    iv = d.get("StartInterval")
    if iv:
        return float(iv), "每%d秒" % iv, True
    cal = d.get("StartCalendarInterval")
    if cal:
        items = cal if isinstance(cal, list) else [cal]
        if any("Weekday" in x for x in items):
            return 7 * 86400.0, "每周轮", True
        return 86400.0, "每日轮", True
    if d.get("WatchPaths"):
        return None, "WatchPaths事件驱动", False
    if d.get("KeepAlive"):
        return None, "常驻", False
    if d.get("RunAtLoad"):
        return None, "仅加载时", False
    return None, "无调度", False


def _job_alive(label):
    """launchd 自证：返回 (True/False/None, pid)。None=探测不可用（须显形为盲区）。
    连查两次——实测批量连发 `launchctl print` 时会偶发返回 not running（同 label 单查即 running）。"""
    domain = "gui/%d/%s" % (os.getuid(), label)
    got = False
    for _ in range(2):
        try:
            r = subprocess.run(["launchctl", "print", domain],
                               capture_output=True, text=True, timeout=10)
        except Exception:
            return (None, "")
        state = pid = ""
        for line in r.stdout.splitlines():
            t = line.strip()
            if t.startswith("state = ") and not state:
                state = t[8:].strip()
            elif t.startswith("pid = ") and not pid:
                pid = t[6:].strip()
        if state == "running":
            return (True, pid)
        got = got or bool(state)
    return ((False, "") if got else (None, ""))


def _watchpaths_missing(d):
    """WatchPaths 指向不存在的路径 → 事件永不触发（静默死亡新形态·plist 自证，无探测噪声）。"""
    wp = d.get("WatchPaths") or []
    wp = [wp] if isinstance(wp, str) else list(wp)
    return [w for w in wp if not os.path.exists(os.path.expanduser(str(w)))]


def check_scheduled_jobs(launch_dir=None, own_roots=None, ctl=None, now=None, probe=None):
    """判据⑤：本系统 launchd 作业 存在性·加载态·退出码诚实性·产物时效。
    返回 (own_rows, foreign_rows, skipped_count)；row=(label, level, detail)。
    只读——⛔不修改任何 plist、不代启停作业（处置归你/原登记端）。"""
    launch_dir = launch_dir or LAUNCH_DIR
    own_roots = own_roots or OWN_ROOTS
    now = now or datetime.now()
    if ctl is None:
        ctl = _launchctl_map()
    probe = probe or _job_alive
    own, foreign, skipped = [], [], 0
    for path in sorted(glob.glob(os.path.join(launch_dir, "*.plist"))):
        label = os.path.basename(path)[:-6]
        try:
            d = plistlib.load(open(path, "rb"))
        except Exception as e:
            own.append((label, "🔴", "plist 不可解析（%s）" % str(e)[:40]))
            continue
        if d.get("Disabled"):
            skipped += 1
            continue
        scripts = _plist_scripts(d)
        cad, clabel, time_ok = _cadence(d)
        is_own = any(s.startswith(root) for s in scripts for root in own_roots)
        if not is_own:
            # 他端/第三方：按跨端自限纪律不处置，只在"确证坏了"时显形
            if scripts and all(not os.path.exists(s) for s in scripts):
                foreign.append((label, "🟡", "脚本缺失·未加载（%s）·他端资产·仅显形不处置"
                                % os.path.basename(scripts[0])))
            else:
                skipped += 1
            continue
        hard, soft = [], []
        blind = stale_weak = no_sched = pending_finding = False
        if clabel == "无调度":
            no_sched = True
            soft.append("无调度声明且无 WatchPaths/KeepAlive/RunAtLoad→永不自动触发（盲区）")
        if not scripts:
            soft.append("无可解析的被调脚本（形态超出判据⑤ v1 覆盖）")
        missing = [s for s in scripts if not os.path.exists(s)]
        if missing:
            hard.append("脚本缺失❌ %s" % " ".join(os.path.basename(m) for m in missing))
        wmiss = _watchpaths_missing(d)
        if wmiss:
            wp_all = d.get("WatchPaths")
            wp_n = 1 if isinstance(wp_all, str) else len(wp_all or [])
            txt = "WatchPaths 指向不存在文件 %s" % " ".join(os.path.basename(str(w).rstrip("/")) for w in wmiss)
            if len(wmiss) == wp_n:
                hard.append(txt + "（全缺❌事件永不触发）")
            else:
                soft.append(txt + "（部分缺·仍可被其余路径触发）")
        if ctl is None:
            blind = True
            soft.append("launchctl 不可读→加载态/退出码未检（仪器盲区）")
        elif label not in ctl:
            hard.append("未加载（plist 在盘但 launchctl 域无此作业·宣称%s）" % clabel)
        elif ctl[label] != "0":
            kind, detail = _rc_semantics(d, ctl[label])
            if kind == "finding":
                # 不是故障，但检查器报的是真欠账——标 🟡 待处置，⛔不得标 ✅（那等于藏账）
                pending_finding = True
                soft.append("exit=%s 为检查器报告有发现（stderr 无异常·stdout 有产物），"
                            "非作业故障 → 末行：%s" % (ctl[label], detail))
            elif kind == "crash":
                hard.append("上次退出码=%s·真崩（stderr：%s）" % (ctl[label], detail))
            else:
                hard.append("上次退出码=%s（非0·退出码语义不可判，保守记红）" % ctl[label])
        art = JOB_ARTIFACTS.get(label)
        if art:
            ap = (art[0] if os.path.isabs(art[0])
              else os.path.expanduser("~/" + art[0].lstrip("~/")))  # 2026-10-06 根治：lstrip("~/") 对绝对路径会把 /Users/... 剥成 Users/... 再拼 HOME=幽灵路径（两层红实证·job声明绝对/相对两形态并存）
            if not os.path.exists(ap):
                hard.append("声明产物不存在❌ %s" % os.path.basename(ap))
            elif art[1] == "per-run" and time_ok and cad:
                age = (now - datetime.fromtimestamp(os.path.getmtime(ap))).total_seconds()
                lim = cad * JOB_GRACE
                if age > lim:
                    hard.append("产物超龄 %.1f天 > 阈 %.1f天（宣称%s·实盘未出活）"
                                % (age / 86400.0, lim / 86400.0, clabel))
                else:
                    soft.append("产物新鲜 %.1f天" % (age / 86400.0))
            else:
                soft.append("%s·时效不适用" % ("仅异常落笔" if art[1] == "alarm-only" else clabel))
        else:
            # 未登记产物：优先用 launchd 自证判活（常驻作业），再回退 plist 自身声明的 stdout 作弱证据
            # （两者均派生自被检对象，⛔不另立手工名单=防双本账）
            judged = False
            if clabel == "常驻":
                running, pid = probe(label)
                if running is True:
                    soft.append("launchd 实锤 running（常驻·pid=%s）" % pid)
                    judged = True
                elif running is False:
                    blind = True
                    soft.append("KeepAlive 声明常驻但 launchd 双探均非 running（盲区·非通过）")
                    judged = True
            if not judged:
                sop = os.path.expanduser(d.get("StandardOutPath") or "")
                if sop and os.path.exists(sop) and os.path.getsize(sop) > 0:
                    age = (now - datetime.fromtimestamp(os.path.getmtime(sop))).total_seconds()
                    if not (time_ok and cad):
                        blind = True
                        soft.append("plist stdout 存在但%s→时效不可判（盲区·非通过）" % clabel)
                    elif age > cad * JOB_GRACE:
                        stale_weak = True  # 弱证据不升 🔴：stdout 写入频率 ≠ 作业触发频率
                        soft.append("plist stdout 超龄 %.1f天（弱证据·宣称%s）" % (age / 86400.0, clabel))
                    else:
                        soft.append("plist stdout 新鲜 %.1f天（弱证据）" % (age / 86400.0))
                else:
                    blind = True
                    soft.append("未登记产物声明且 plist 无可用 stdout→时效不可判（盲区·非通过）")
        lv = "🔴" if hard else ("🟡" if (blind or stale_weak or no_sched or pending_finding) else "✅")
        det = "｜".join(hard + soft) if (hard or soft) else "%s·加载正常·exit 0" % clabel
        own.append((label, lv, det))
    own.sort(key=lambda r: (r[1] != "🔴", r[1] != "🟡", r[0]))
    return own, foreign, skipped


# ============ 处置记录持久化（v1.8 新增·根治人工处置被滚动覆盖丢失） ============
# 缘起（2026-09-01 第20轮实证）：第19轮人工处置记录（09:45·com.用户名.consistency-guard 双因修复
# + QoderCN守卫台账落点迁移）被引擎滚动覆盖无持久化，仅 .bak 存留——处置记录落点=报告本身=每次被覆盖。
# 根治（愿景①全自动化/②越用越好用/③自主进化）：写新报告前引擎自旧报告机械提取处置记录 →
# 合并去重入 audit-log rec.dispositions（累积快照·自包含）→ 新报告「处置记录」节回显 →
HEARTBEAT_STALE_DAYS = 30
JOB_LEDGER = os.path.expanduser("[记忆共享中心]/数字分身/job_probation_ledger.json")


def check_job_heartbeat(ledger_path=None, now=None):
    """判据⑥：岗位心跳（在册岗位按判决台账聚合·>30天零判决=🟡休眠·只显形不撤岗）。
    2026-10-20 A段（你批上岗改善方案）·负例夹具见 --negtest 11-14。"""
    now = now or datetime.now()
    path = ledger_path or JOB_LEDGER
    if not os.path.exists(path):
        return [("job_probation_ledger", "🟡", "台账缺失（fail-loud·心跳判据不可判·%s）" % path)]
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [("job_probation_ledger", "🟡", "台账损坏不可解析（⛔静默吞=死数据·%s）" % str(e)[:60])]
    rows = []
    for job, v in sorted((d.get("jobs") or {}).items()):
        if not isinstance(v, dict):
            continue
        if v.get("status") == "retired":
            continue
        ds = v.get("decisions") or []
        dates = []
        for x in ds:
            dd = (x or {}).get("date", "")[:10]
            try:
                dates.append(datetime.strptime(dd, "%Y-%m-%d"))
            except Exception:
                continue
        if not dates:
            st = v.get("start_date") or v.get("probation_start")
            if st:
                try:
                    dates.append(datetime.strptime(st[:10], "%Y-%m-%d"))
                except Exception:
                    pass
        if not dates:
            rows.append((job, "🟡", "零判决且无上岗日期字段（盲区·不可判休眠也⛔不假绿）"))
            continue
        days = (now - max(dates)).days
        n = len(ds)
        if days > HEARTBEAT_STALE_DAYS:
            rows.append((job, "🟡", "岗位休眠：距末判决 %d 天>%d（在册·判决累计 %d 条·撤留归你）" % (days, HEARTBEAT_STALE_DAYS, n)))
        else:
            rows.append((job, "✅", "心跳正常：末判决距 %d 天（累计 %d 条·status=%s）" % (days, n, v.get("status", "?"))))
    return rows


# 处置台账随 audit-log 供 evolution_deviation.py 闭环流消费（处置了什么→下轮还红不红=闭环验证数据）。
# 机械锚点：报告内 `> YYYY-MM-DD HH:MM 处置记录：<内容>`（blockquote 行·第19轮既有格式）。
DISPOSITION_PATTERN = re.compile(
    r"^>\s*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)\s*处置记录[:：]\s*(.+)$")


def _extract_dispositions(text):
    """从报告文本机械提取处置记录。返回 [(ts, txt)]·保序（空文本→[]）。"""
    out = []
    for line in (text or "").splitlines():
        m = DISPOSITION_PATTERN.match(line.strip())
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def _audit_log_last_dispositions():
    """audit-log 末条 rec.dispositions（累积快照·无则 []）。"""
    last = None
    for line in _load_lines(AUDIT_LOG):
        line = line.strip()
        if not line:
            continue
        try:
            last = json.loads(line)
        except Exception:
            pass
    if not last:
        return []
    disp = last.get("dispositions") or []
    return [[str(a), str(b)] for a, b in disp] if isinstance(disp, list) else []


def _merge_dispositions(prev, carried):
    """合并去重保序：prev(台账累积) + carried(旧报告新提取·按 (ts,txt) 去重)。"""
    seen = set(tuple(x) for x in prev)
    merged = [list(x) for x in prev]
    for ts, txt in carried:
        if (ts, txt) not in seen:
            seen.add((ts, txt))
            merged.append([ts, txt])
    return merged


def build_report(round_no, pend, ledg, emb, water, jobs, dispositions=None, hb=None):
    j_own, j_foreign, j_skipped = jobs
    dispositions = dispositions or []
    red = sum(1 for x in pend if x[4] == "🔴") + sum(1 for x in ledg + emb if x[1] == "🔴") \
        + sum(1 for x in j_own if x[1] == "🔴")
    yellow = (len(pend) - sum(1 for x in pend if x[4] == "🔴")) + \
             sum(1 for x in ledg + emb if x[1] == "🟡") + \
             sum(1 for x in j_own if x[1] == "🟡") + len(j_foreign) + \
             sum(1 for x in (hb or []) if x[1] == "🟡")
    now = datetime.now()
    L = []
    L.append("# 岗位3 · 声明-实盘对账报告（第 %d 轮 · %s）\n" % (round_no, now.strftime("%Y-%m-%d %H:%M")))
    L.append("> 本轮结论：🔴 %d 处脱钩 · 🟡 %d 处悬置 · 其余声明与台账相符%s\n" % (red, yellow,
             ("（已归档处置 %d 条）" % len(dispositions)) if dispositions else ""))
    L.append("> 判据版本 %s（台账实锤才算✅·悬置阈 %d 天·台账新鲜阈 %d 天·运行时载荷键数≥10·仅当前态区计悬置·schema无stdin_keys不套载荷口径）——v1→v1.1 演进依据=第1轮两处误报实证（变更记录历史区/异端schema）；v1.2→v1.3 演进依据=同日实证 com.knowledge.backup plist 脚本名手误 exit=127 静默死 23 天，判据①-④对『作业没在跑』这一类结构性失明；v1.3→v1.4 演进依据=建 v1.3 过程中自查出的假绿（拿 plist stdout mtime 给常驻作业判时效，而 stdout 新旧与『进程是否在跑』无因果），改由 launchd 自证 state/pid，并补 WatchPaths 指向不存在文件→🔴（事件永不触发）。v1.4→v1.5 演进依据=2026-08-31 实证：重启后/非交互 shell 下 `launchctl list` 返回空→全部 own job 误报『未加载』🔴（手动补跑爆 27 假红）；改由逐 label `launchctl print gui/$UID/<label>` 实查（与 _job_alive 同源可靠），并新增「看门狗看自己」自身节律缺口门禁（>9天未跑→🔴），根治看门狗漏跑无感。v1.5→v1.6 演进依据=同次根治：调度原语从 `StartCalendarInterval`（周一09:00·错过点不补跑·脆弱）改为 `StartInterval 86400`+`RunAtLoad`（每日·加载即跑·睡眠/重启自愈），自身节律门禁阈值随 9→2 天；从愿景①「不依赖人记得」判定此为看门狗最优可靠形态，原「每周」仅为拍脑袋节奏。v1.6→v1.7 演进依据=2026-08-31 第9轮27🔴复盘：判据②原以 /tmp 台账存在+新鲜判守卫健康，但 /tmp 重启易失且事件驱动守卫(端休眠无会话即不写账)→WB/ZCode 误报🔴；根治=事件驱动守卫台账落点迁 ~/.workbuddy/(持久·根治重启清空)+判据②增补「挂载态兜底」(已挂 hooks 但端休眠/未触发→🟡待命而非🔴·真未挂载才🔴)，对齐愿景「可观测·全自动化」。v1.7→v1.8 演进依据=2026-09-01 第20轮实证：第19轮人工处置记录(09:45·consistency-guard 双因修复+QoderCN台账落点迁移)被引擎滚动覆盖丢失仅.bak存留；根治=写报告前引擎自旧报告机械提取处置记录→合并去重入 audit-log rec.dispositions(累积快照)→报告「处置记录」节回显(历史可追溯)，处置台账随 audit-log 供 evolution_deviation.py 闭环流消费——对齐愿景①不依赖人记得/②越用越好用/③自主进化。v1.8→v1.9 演进依据=2026-09-26 第107轮实证：4 处🔴里只有 1 处是真崩（panel_snapshot.compute_okr TypeError），另 3 处是检查器正常工作——`script_family_check.py --strict` 的 help 自陈「任一红→exit 1」、blueprint watcher stdout 末行「发现 2 个问题」、changelog-audit stdout `alarm:true`，其 stderr 全空。原判据对 last exit code 非 0 一律 hard.append（裸比较分支），把「有发现」与「崩了」混为同一红，代价不是多报 3 红，而是**真崩被假红淹没（信噪比 1:3）→ 狼来了 → 红被习惯性跳过**。根治=新增 `_rc_semantics()` 三分类（crash/finding/unknown，机械判据：stderr 异常特征 vs stdout 有产物），finding 记 🟡 待处置（⛔不记 ✅——那等于把欠账藏进绿里），unknown 保守留 🔴（宁可假红不漏真崩）；判据⑤负例夹具 17/17 复跑通过。对齐愿景③「从自身运行数据学习改进」——本轮同时暴露并修掉上游真崩根因（SSOT 那行被加粗成「接入率（**分母」→ 字面锚点失配 → 回退手敲裸 int → 解包崩），教训抽象：**凡靠字面锚点解析文档的机器，匹配前必须先剥 markdown 装饰，且降级兜底值不得携带具体数字（伪装成有效数据的降级=二次故障源）**。v1.9→v1.10 演进依据=2026-10-10 第148轮实证：state-bus-sync 崩案已于10-09修复并复跑（rc=1 系业务发现·stderr 静默），但 err.log 里的旧 TypeError 残骸被 _rc_semantics 无条件当现行证据→修好的作业永远真崩（同源律的取数时点残面：判据演化了，证据时效没跟上）。根治=崩溃签名加时效闸（stderr mtime 早于 stdout ⇒ 上一轮遗账·降级 finding/unknown；无 stdout 可比时照旧 crash·保守性不丢）；负例夹具 +3 例（18旧trace不得crash/19新trace仍crash/20无签名仍finding）。对齐愿景③。v1.10→v1.11 演进依据=2026-10-20 上岗改善方案A段落地（你批）：岗位「在册但休眠」无机械检——一手机证：09表 10-13 扫描记「JOB-005 0条」，至 10-20 台账实查已 24 条（二手引用会腐烂，必须一手机检）；JOB-004 末判决 10-02 渐近沉默。新增判据⑥「岗位心跳」：在册岗位按 job_probation_ledger 聚合，>30 天零判决→🟡休眠（只显形不撤岗——撤岗属价值层归你·愿景红线）；台账缺失/损坏→🟡 fail-loud；retired/无判决字段如实🟡不假绿。对齐愿景①不依赖人记得/④越用越懂你（哪些岗真在干活）。⚠️另记：本判据首跑即推翻一处本家族二手声明（见处置记录）。 （判据预注册下如实升版）· 抽检入口：detail 内路径可直接打开验证\n"
             % (CRITERIA_VERSION, STALE_DAYS, LEDGER_FRESH_DAYS))
    L.append("\n## 处置记录（v1.8·引擎机械归档·历史可追溯）\n")
    if dispositions:
        for ts, txt in dispositions:
            L.append("- `%s` %s" % (ts, txt))
    else:
        L.append("无。")
    L.append("\n## 悬置声明（判据①·设计哲学文件中未兑现承诺）\n")
    if pend:
        L.append("| 文件 | 行 | 声明片段 | 已悬置 | 级别 | 备注 |")
        L.append("|---|---|---|---|---|---|")
        for f, ln, txt, days, lv, resolved in pend:
            note = "历史区已见兑现记录→属登记未回改（建议回改登记行）" if resolved else "未见解 record→真悬置（催办）"
            L.append("| %s | L%d | %s | %s | %s | %s |" % (f, ln, txt, ("%d天" % days) if days is not None else "日期未知", lv, note))
    else:
        L.append("无。")
    L.append("\n## 台账健康度（判据②·童灵各端守卫/注入台账）\n")
    L.append("| 台账 | 判定 | detail |")
    L.append("|---|---|---|")
    for n, v, d in ledg:
        L.append("| %s | %s | %s |" % (n, v, d))
    L.append("\n## 暂存区水位（判据④·v1.2 你批准三修正）\n")
    L.append("| 判定 | detail | 自动动作 |")
    L.append("|---|---|---|")
    L.append("| %s | %s | %s |" % (water[0], water[1], {"observe": "观察模式（首轮只记录）", "healed": "已自动归位", "heal-failed": "失败须人工", "none": "无"}.get(water[2], "无")))
    L.append("\n## 切片新鲜度（判据③·恒驻文件内嵌 vs slices/ 产物）\n")
    L.append("| 恒驻文件 | 判定 | detail |")
    L.append("|---|---|---|")
    for n, v, d in emb:
        L.append("| %s | %s | %s |" % (n, v, d))
    L.append("\n## 定时作业健康度（判据⑤·%s·launchd 声明 vs 实盘）\n" % CRITERIA_VERSION)
    L.append("| 作业 | 判定 | detail |")
    L.append("|---|---|---|")
    if j_own:
        for n, v, d in j_own:
            L.append("| %s | %s | %s |" % (n, v, d))
    else:
        L.append("| （本系统作业零命中） | 🔴 | 判据⑤自身失明：扫描根 %s 或 OWN_ROOTS 失效·不可视作通过 |" % LAUNCH_DIR)
    if j_foreign:
        L.append("\n**他端/第三方确证异常（跨端自限·仅显形不处置）**\n")
        L.append("| 作业 | 判定 | detail |")
        L.append("|---|---|---|")
        for n, v, d in j_foreign:
            L.append("| %s | %s | %s |" % (n, v, d))
    L.append("\n## 岗位心跳（判据⑥·%s·按判决台账聚合·只显形不撤岗）\n" % CRITERIA_VERSION)
    L.append("| 岗位 | 判定 | detail |")
    L.append("|---|---|---|")
    for n, v2, d2 in (hb or []):
        L.append("| %s | %s | %s |" % (n, v2, d2))
    L.append("\n> 归属判据=被调脚本路径落在 %s 之一；其余 %d 项作业属他端/系统组件，不纳入本判据（如实声明边界·不假装全覆盖）。\n"
             % ("、".join("~/" + os.path.basename(r.rstrip("/")) for r in OWN_ROOTS), j_skipped))
    L.append("\n---\n\n*岗位3「声明-实盘对账官」试运行产出·只检测不修改·异常处置归你/原登记端（02规范§五.3）*\n")
    return "\n".join(L), red, yellow


def check_self_cadence(now=None):
    """看门狗看自己：本对账官末次实跑距今天数。每日轮（v1.6 起·StartInterval 86400），>2天=漏跑。
    返回 (level, detail) 或 None（无台账）。v1.5 新增·v1.6 随调度改为每日而阈值 9→2 天——根治
    『看门狗自己漏跑却无感』的结构性盲区，使任意一次后续实跑都能机械显形此前的调度缺口（愿景①不依赖人记得）。"""
    now = now or datetime.now()
    last = None
    for line in _load_lines(AUDIT_LOG):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            last = rec.get("ts")
        except Exception:
            pass
    if not last:
        return ("🟡", "对账官自身无运行台账（盲区·首跑前）")
    try:
        lt = datetime.strptime(last, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return ("🟡", "对账官自身台账时间戳不可解析（盲区）")
    age = (now - lt).total_seconds() / 86400.0
    if age > 2:
        return ("🔴", "对账官自身超时未跑（距末次 %.1f 天>2天）·须排查 launchd 调度（RunAtLoad+StartInterval 应加载即跑/每日）" % age)
    return ("✅", "对账官自身运行节律正常（距末次 %.1f 天）" % age)


def run_round():
    pend = check_pending_claims()
    ledg = check_ledgers()
    emb = check_embeds()
    water = check_staging_water()
    jobs = check_scheduled_jobs()
    hb = check_job_heartbeat()
    # 看门狗看自己：把自身节律缺口并入门禁（v1.5）
    sc = check_self_cadence()
    if sc:
        jobs[0].append(("com.buluotuo.position3-audit·自身节律", sc[0], sc[1]))
    # 轮次号=台账行数+1
    round_no = sum(1 for line in _load_lines(AUDIT_LOG) if line.strip()) + 1
    # v1.8 处置记录持久化：写新报告前，先从旧报告机械提取人工处置 → 合并去重入累积快照
    # （愿景①不依赖人记得·②新报告回显可追溯·③随 audit-log 供 evolution_deviation.py 闭环流消费）
    old_text = ""
    if os.path.exists(REPORT):
        try:
            old_text = open(REPORT, encoding="utf-8").read()
        except Exception:
            old_text = ""
    dispositions = _merge_dispositions(_audit_log_last_dispositions(), _extract_dispositions(old_text))
    report, red, yellow = build_report(round_no, pend, ledg, emb, water, jobs, dispositions, hb=hb)
    if os.path.exists(REPORT):
        shutil.copy2(REPORT, REPORT + ".bak")
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    rec = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "round": round_no,
        "pending_claims": len(pend),
        "red": red,
        "yellow": yellow,
        "dispositions": dispositions,
        "ledgers": {n: v for n, v, _ in ledg},
        "embeds": {n: v for n, v, _ in emb},
        "staging": {"level": water[0], "action": water[2]},
        "jobs": {
            "red": sum(1 for x in jobs[0] if x[1] == "🔴"),
            "yellow": sum(1 for x in jobs[0] if x[1] == "🟡"),
            "state": {n: v for n, v, _ in jobs[0]},
            "foreign_alerts": len(jobs[1]),
            "not_in_scope": jobs[2],
        },
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("岗位3 对账第 %d 轮完成：🔴%d 🟡%d → %s" % (round_no, red, yellow, REPORT))
    return red


def mode_negtest_jobs():
    """判据⑤负例实测（S064：守卫必须被证明会报警）。临时目录伪造，不碰真配置。"""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="p3negtest-")
    own = os.path.join(tmp, "own")
    os.makedirs(own)
    roots = (own + os.sep,)
    results = []

    def case(name, cond):
        results.append((name, bool(cond)))
        print("  %s %s" % ("✅" if cond else "🔴", name))

    def mk(label, args=None, no_sched=False, **extra):
        d = {"Label": label, "ProgramArguments": args or ["/bin/bash", os.path.join(own, "s.sh")]}
        if not no_sched:
            d["StartInterval"] = 86400  # 模拟"宣称每日跑"的作业
        d.update(extra)
        plistlib.dump(d, open(os.path.join(tmp, label + ".plist"), "wb"))
        return d

    script = os.path.join(own, "s.sh")
    open(script, "w").write("#!/bin/bash\ntrue\n")
    # 复用已登记作业名以命中 JOB_ARTIFACTS（其产物=knowledge-backup.log，盘上真实新鲜）
    lab = "com.knowledge.backup"
    mk(lab)
    ok_rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0"})
    case("1 正常作业→✅（非假红）", ok_rows and ok_rows[0][1] == "✅")

    os.unlink(script)
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0"})
    case("2 负例·脚本缺失→🔴", rows[0][1] == "🔴" and "脚本缺失" in rows[0][2])
    open(script, "w").write("#!/bin/bash\ntrue\n")

    rows, _, _ = check_scheduled_jobs(tmp, roots, {})
    case("3 负例·plist在盘但未加载→🔴", rows[0][1] == "🔴" and "未加载" in rows[0][2])

    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "127"})
    case("4 负例·退出码非0→🔴（127 这一族就是本次事故形态）", rows[0][1] == "🔴" and "退出码" in rows[0][2])

    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0"}, now=datetime.now() + timedelta(days=30))
    case("5 负例·产物超龄→🔴（宣称每日但30天没出活）", rows[0][1] == "🔴" and "产物超龄" in rows[0][2])

    mk("com.unregistered.job")
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.unregistered.job": "0"})
    un = [r for r in rows if r[0] == "com.unregistered.job"][0]
    case("6 负例·无产物声明→🟡显式盲区（⛔不假绿）", un[1] == "🟡" and "未登记" in un[2])

    mk("com.qclaw.foreign", args=["/bin/bash", os.path.join(tmp, "gone", "x.sh")])
    rows, foreign, _ = check_scheduled_jobs(tmp, roots, {lab: "0"})
    case("7 他端边界·脚本缺失只进 foreign 不处置", foreign and foreign[0][0] == "com.qclaw.foreign"
         and "不处置" in foreign[0][2] and not any(r[0] == "com.qclaw.foreign" for r in rows))

    # bash -c 包装 + 相对脚本名（semantic-radar 实装形态）
    rel = os.path.join(own, "sub")
    os.makedirs(rel, exist_ok=True)
    open(os.path.join(rel, "r.py"), "w").write("")
    mk("com.buluotuo.wrapper", args=["/bin/bash", "-c", "cd %s && /usr/bin/python3 r.py --scan" % rel],
       StartInterval=600, WorkingDirectory=rel)
    scripts = _plist_scripts({"ProgramArguments": ["/bin/bash", "-c",
                                                   "cd %s && /usr/bin/python3 r.py --scan" % rel],
                              "WorkingDirectory": rel})
    case("8 形态解析·bash -c 内相对名可按 WorkingDirectory 还原", scripts == [os.path.join(rel, "r.py")])
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.buluotuo.wrapper": "0"})
    w = [r for r in rows if r[0] == "com.buluotuo.wrapper"][0]
    case("9 无产物登记的包装作业→🟡 而非漏检", w[1] == "🟡" and "未登记" in w[2])

    rows, _, _ = check_scheduled_jobs(tmp, (os.path.join(tmp, "nope") + os.sep,), {lab: "0"})
    case("10 负例·归属零命中→own 空（报告层显式为判据失明）", rows == [])

    # ── 判据⑥岗位心跳负例（v1.11）──
    import json as _json
    hj = os.path.join(tmp, "hb_ledger.json")
    old = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")
    fresh = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    _json.dump({"jobs": {
        "JOB-T1": {"status": "active", "decisions": [{"date": old}]},
        "JOB-T2": {"status": "probation", "decisions": [{"date": fresh}, {"date": fresh}]},
        "JOB-T3": {"status": "retired", "decisions": [{"date": old}]},
        "JOB-T4": {"status": "active", "decisions": []}}}, open(hj, "w"))
    hb = check_job_heartbeat(hj)
    hm = {r[0]: r for r in hb}
    case("11 心跳·40天零判决→🟡休眠", hm["JOB-T1"][1] == "🟡" and "休眠" in hm["JOB-T1"][2])
    case("12 心跳·5天有判决→✅", hm["JOB-T2"][1] == "✅" and "累计 2" in hm["JOB-T2"][2])
    case("13 心跳·retired不进判（退役岗不误报）", "JOB-T3" not in hm)
    case("14 心跳·零判决无日期→🟡盲区不假绿", hm["JOB-T4"][1] == "🟡" and "盲区" in hm["JOB-T4"][2])
    hb2 = check_job_heartbeat(os.path.join(tmp, "ghost.json"))
    case("15 心跳·台账缺失→🟡fail-loud", hb2[0][1] == "🟡" and "缺失" in hb2[0][2])

    mk("com.nosched.job", no_sched=True)
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.nosched.job": "0"})
    ns = [r for r in rows if r[0] == "com.nosched.job"][0]
    case("11 负例·无任何调度声明→🟡永不自动触发（不静默放过）", ns[1] == "🟡" and "永不自动触发" in ns[2])

    # 常驻作业判活：launchd 自证，⛔不靠 stdout mtime（mtime 与"是否在跑"无关）
    def probe_running(label):
        return (True, "4242")

    def probe_dead(label):
        return (False, "")

    def probe_none(label):
        return (None, "")

    mk("com.resident.job", no_sched=True, KeepAlive=True, RunAtLoad=True)
    ctl_res = {lab: "0", "com.resident.job": "0"}
    rows, _, _ = check_scheduled_jobs(tmp, roots, ctl_res, probe=probe_running)
    rs = [r for r in rows if r[0] == "com.resident.job"][0]
    case("12 常驻·launchd running→✅（非假红）", rs[1] == "✅" and "实锤 running" in rs[2])

    rows, _, _ = check_scheduled_jobs(tmp, roots, ctl_res, probe=probe_dead)
    rs = [r for r in rows if r[0] == "com.resident.job"][0]
    case("13 负例·KeepAlive 声明常驻但非 running→🟡（⛔不假绿）", rs[1] == "🟡" and "非 running" in rs[2])

    rows, _, _ = check_scheduled_jobs(tmp, roots, ctl_res, probe=probe_none)
    rs = [r for r in rows if r[0] == "com.resident.job"][0]
    case("14 负例·探测不可用→🟡显式盲区（仪器盲区不豁免）", rs[1] == "🟡" and "未登记" in rs[2])

    mk("com.wp.allmiss", no_sched=True, WatchPaths=[os.path.join(tmp, "gone", "a.md")])
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.wp.allmiss": "0"}, probe=probe_none)
    wp = [r for r in rows if r[0] == "com.wp.allmiss"][0]
    case("15 负例·WatchPaths 全缺→🔴事件永不触发", wp[1] == "🔴" and "全缺" in wp[2])

    mk("com.wp.partmiss", no_sched=True,
       WatchPaths=[os.path.join(tmp, "gone", "a.md"), script])
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.wp.partmiss": "0"}, probe=probe_none)
    wp = [r for r in rows if r[0] == "com.wp.partmiss"][0]
    case("16 WatchPaths 部分缺→🟡不升🔴（其余路径仍可触发）", wp[1] == "🟡" and "部分缺" in wp[2])

    wout = os.path.join(tmp, "wp-stdout.log")
    open(wout, "w").write("x\n")
    mk("com.wp.stdout", no_sched=True, WatchPaths=[script], StandardOutPath=wout)
    rows, _, _ = check_scheduled_jobs(tmp, roots, {lab: "0", "com.wp.stdout": "0"}, probe=probe_none)
    wo = [r for r in rows if r[0] == "com.wp.stdout"][0]
    case("17 负例·事件驱动作业有 stdout 不得判✅（旧版假绿实锤已修）", wo[1] == "🟡" and "时效不可判" in wo[2])

    # v1.10 时效闸三例（直打 _rc_semantics·防「判据演化了夹具还测旧形状」）
    se = os.path.join(tmp, "rc.err")
    so = os.path.join(tmp, "rc.out")
    open(se, "w").write("Traceback (most recent call last):\nTypeError: old crash\n")
    open(so, "w").write("正常产物\n")
    fresh = os.stat(so).st_mtime
    os.utime(se, (fresh - 60, fresh - 60))
    k, _ = _rc_semantics({"StandardErrorPath": se, "StandardOutPath": so}, "1")
    case("18 v1.10·崩溃签名旧于stdout(上一轮遗账)→finding 不判crash", k == "finding")
    os.utime(se, (fresh + 2, fresh + 2))
    k, _ = _rc_semantics({"StandardErrorPath": se, "StandardOutPath": so}, "1")
    case("19 v1.10·崩溃签名新于stdout(现行崩)→crash 保守性不丢", k == "crash")
    open(se, "w").write("")
    k, _ = _rc_semantics({"StandardErrorPath": se, "StandardOutPath": so}, "1")
    case("20 回归·stderr空+stdout有产物→finding", k == "finding")

    shutil.rmtree(tmp, ignore_errors=True)
    bad = [n for n, o in results if not o]
    print("=== 判据⑤负例实测 %d/%d 通过 ===" % (len(results) - len(bad), len(results)))
    if bad:
        print("未报警分支：" + "；".join(bad))
    sys.exit(1 if bad else 0)


def mode_selfcheck():
    print("=== position3_audit.py 挂载自检（岗位3·三要素） ===")
    ok = True
    # ① 数据源可读
    src_ok = all(os.path.exists(p) for p in AUDIT_FILES) and os.path.isdir(SLICES)
    print("  [数据源] %s（哲学文件 %d/2 + slices/）" % ("✅" if src_ok else "🔴", sum(1 for p in AUDIT_FILES if os.path.exists(p))))
    ok &= src_ok
    # ② 报告可写
    try:
        os.makedirs(STEPS, exist_ok=True)
        t = REPORT + ".selfcheck-tmp"
        with open(t, "w") as f:
            f.write("ok")
        os.unlink(t)
        print("  [报告可写] ✅ %s" % REPORT)
    except Exception as e:
        print("  [报告可写] 🔴 %s" % e)
        ok = False
    # ③ 台账可写
    try:
        t = AUDIT_LOG + ".selfcheck-tmp"
        with open(t, "a") as f:
            f.write("")
        os.unlink(t) if os.path.exists(t) else None
        rounds = sum(1 for line in _load_lines(AUDIT_LOG) if line.strip())
        print("  [台账可写] ✅ %s（已累计 %d 轮）" % (AUDIT_LOG, rounds))
    except Exception as e:
        print("  [台账可写] 🔴 %s" % e)
        ok = False
    print("=== 自检%s ===" % ("通过" if ok else "未过"))
    sys.exit(0 if ok else 1)


def main():
    if "--selfcheck" in sys.argv[1:]:
        mode_selfcheck()
        return
    if "--negtest" in sys.argv[1:]:
        mode_negtest_jobs()
        return
    run_round()
    sys.exit(0)


if __name__ == "__main__":
    # 失败放行只适用于"对账轮次"（生产作业·绝不制造 launchd 噪音）。
    # 自检/负例模式必须严格：门禁自身崩了却 exit 0 = 假成功（2026-08-30 实测到该形态后修正）。
    _strict = {"--selfcheck", "--negtest"} & set(sys.argv[1:])
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("⚠️ position3_audit 异常: %s" % str(e)[:200])
        if _strict:
            print("🔴 自检模式异常退出·不放行")
            sys.exit(1)
    sys.exit(0)
