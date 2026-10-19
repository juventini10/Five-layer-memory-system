#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
immunity_l1_draft.py — L1 修复草案生成器（免疫自愈推进 P0 · 真源单一化版）
Version: 2.1.0 (2026-09-18)

定位：对「声明/文档类长坑」（W4/W5/W6/W8/W11）自动诊断 + 生成**可复验**的修复草案。
      人只批"要不要改"，不再自己想怎么改。

v1.2.0 → v2.0.0 为什么不兼容（2026-09-18 实查根因）：
  v1.x 在 WORK_ORDERS 里**自带 detect 副本**，且副本填的是"改好的新命令"——于是
  `--verify` 判的是自己的副本，不是抗体真源（规范反哺日志/LEARNINGS）。实测后果：
    · PROGRESS 记「Phase 0 完成·5/5 抗体免疫」，而真源 W6 仍是恒真 `|| echo "missing"`
      （命中 36 / 免疫史 0）、W8 真源仍无 CHANGELOG 排除、W11 真源仍命中；
    · 工单表 5 条至今全 ⬜，全盘 find 无一份草案文件落盘；
    · 草案里 `old_detect` 取内置副本 → 审批人看到的"改前"是一个不存在的状态。
  ⇒ **自证闭环**：脚本自带尺子 ⇒ 自动生产假绿。这不是精度问题，是权限问题。
  v2.0.0 的结构性修法：**脚本无权定义判据**——detect 一律经 antibody_gate.py --list
  从真源解析；解析不到 = Fail-Closed（不出草案、退出码非 0），⛔不得回退到任何内置副本。

三态修法来源（把"要不要人决定"变成脚本可自证的机械字段）：
  derived   派生型：草案文本 = f(权威源)，无决定内容 → 唯一可毕业到"自动写回"的类
  skeleton  骨架型：结构可算、内容需人补（如 CHANGELOG 条目的变更说明）→ 永不自动
  no_source 无源型：改什么本身是判断（选哪个脚本 / 谁的亲证）→ 永不自动·永久留人
  毕业判据见 --graduation（与 成长箱升级 phase2-design README §3.3 判据#2 同一条，不另建）。

设计边界（L1 红线·机械可验）：
  ⛔ 不直接改生产文件——写域锁死在 成长箱/修复草案/（越界=抛异常·自测 T5）
  ⛔ 不批量跳过——每条工单独立 Loop（评估→草案→复验）per S938
  ⛔ 不宣告"已修复"——免疫判定只由真源 detect 复跑得出，草案本身不算修复

  被接受的风险面（显式记录，回应 shell 执行告警）：抗体的定义**就是**单行 shell 命令，
  复验必须在 bash 里跑它——与巡检端 growth_box_check.sh 阶段② 同一行为，不新增信任面。
  命令源=仓库内抗体真源（规范反哺日志/LEARNINGS·落盘前已过 antibody_gate 六项门禁），
  ⛔不接受任何外部/用户输入拼接进命令；本工具唯一的写域是草案目录（T5 锁死）。

用法：
  immunity_l1_draft.py                    # 逐条诊断（真源）+ 草案落盘 + 台账登记
  immunity_l1_draft.py --w6               # 仅一条（S938 推荐口径）
  immunity_l1_draft.py --verify [--w6]    # 复验：复跑真源 detect，报 命中/免疫
  immunity_l1_draft.py --control          # 正控：证每条真源 detect 能响(坑在)能停(坑修)
  immunity_l1_draft.py --due              # 工单 §六 到期/逾期显形（launchd 每日 08:50 自动跑）
  immunity_l1_draft.py --verdict W5 原样批 # 记审批处置（append-only）
  immunity_l1_draft.py --graduation       # 按台账算：哪一类够格升自动写回
  immunity_l1_draft.py --json             # 结构化输出
  immunity_l1_draft.py --self-test        # 夹具（含防自证闭环核心负例）

退出码：0 = 所选工单真源全免疫；1 = 有草案待批 / 真源未定位（Fail-Closed）；2 = 用法错误
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

VERSION = "2.1.0"
HOME = os.path.expanduser("~")

GATE_PY = os.environ.get(
    "GB_ANTIBODY_GATE",
    os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置/growth-box/scripts/antibody_gate.py"),
)
DRAFT_DIR = os.environ.get(
    "GB_DRAFT_DIR", os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/修复草案")
)
LEDGER = os.path.join(DRAFT_DIR, "审批台账.md")
CHECK_SH = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置/growth-box/scripts/growth_box_check.sh")
SKILL_VER_GUARD = os.path.join(HOME, "[记忆共享中心]/脚本中心/changelog-guard/skill_version_guard.sh")

# 三态修法来源：authority=权威源（可派生）；note=为什么不是纯派生
SOURCE_CLASS = {
    "W4": ("skeleton", "版本号/日期可从 SKILL.md+git 实算，但「变更说明」文字须人写"),
    "W5": ("derived", "权威源=~/.workbuddy/settings.json（挂载实盘）·看板状态词=f(实盘)"),
    "W6": ("derived", "权威源=append_log_entry.py 验证块模板·缺行=补固定模板行"),
    "W8": ("no_source", "「补哪个脚本的调用」是设计判断，机械不可推"),
    "W11": ("no_source", "「你是否亲口确认过」是事实归属+价值层，⛔不得由脚本生成证据"),
}

# 真源锚点：工单 → (抗体所在文件 basename, 标题别名子串列表)。⛔此处不放 detect 命令（见文件头根因）
#   别名而非单串：抗体会被别的修正轮改标题（2026-09-18 实测 W5/W8/W11 标题追加「v1.1修正：…」
#   ⇒ 单串锚当场失效）。改名是允许的，但**判定位必须唯一**：命中 0 或 >1 一律 Fail-Closed。
SOURCE_ANCHORS = {
    "W4": ("规范反哺日志.md", ("Skill 升版未记 CHANGELOG", "skill_lead")),
    "W5": ("规范反哺日志.md", ("settings.json 已实挂", "但已实挂", "待拍板")),
    "W6": ("规范反哺日志.md", ("验证块是否包含变更日志检测行", "变更日志检测", "guard_line")),
    "W8": ("规范反哺日志.md", ("有终检清单声明但无对应脚本调用", "终检清单声明")),
    "W11": ("LEARNINGS.md", ("标注但正文无你亲确认事件证据", "你已质证", "亲确认证据")),
}

TITLES = {
    "W4": "Skill 升版未记 CHANGELOG",
    "W5": '看板写"待拍板"但 settings.json 已实挂',
    "W6": "系统日志验证块须含变更日志检测行",
    "W8": "references 有终检清单声明但无脚本调用",
    "W11": '"你已质证"标注无亲确认证据',
}

CLS_LABEL = {"derived": "派生型", "skeleton": "骨架型", "no_source": "无源型"}


# ── 真源解析（单源：antibody_gate.py --list）────────────────────

def parse_gate_tsv(text):
    """把 gate --list 的 \\x1f 分隔行解析成 [{src,lineno,cmd,title,codes}]。纯函数·可测。"""
    rows = []
    for line in text.split("\n"):
        if not line.strip():
            continue
        p = line.split("\x1f")
        if len(p) < 5:
            continue
        rows.append({
            "src": p[0], "lineno": p[1], "cmd": p[2],
            "title": p[3], "codes": p[4],
        })
    return rows


def resolve_anchors(rows):
    """按别名锚把工单映射到真源抗体。定位必须唯一：0 命中=missing，>1 命中=ambiguous，
    两者一律 Fail-Closed（⛔不得回退内置 detect 副本、⛔不得凭猜挑一条）。"""
    resolved, missing, ambiguous = {}, [], {}
    for wid, (src, aliases) in SOURCE_ANCHORS.items():
        cand = []
        for sub in aliases:
            cand = [r for r in rows if r["src"] == src and sub in r["title"]]
            if cand:
                break
        if len(cand) == 1:
            resolved[wid] = cand[0]
        elif len(cand) == 0:
            missing.append(wid)
        else:
            ambiguous[wid] = cand
    return resolved, missing, ambiguous


def load_real_antibodies():
    """调 gate 取真源抗体清单。gate 不可用 = 全条 Fail-Closed。"""
    if not os.path.isfile(GATE_PY):
        return None, "antibody_gate.py 不存在：%s" % GATE_PY
    try:
        p = subprocess.run([sys.executable, GATE_PY, "--list"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except Exception as e:
        return None, "gate 调用异常：%s" % e
    if p.returncode != 0:
        return None, "gate --list 退出码 %s" % p.returncode
    return parse_gate_tsv(p.stdout.decode("utf-8", "replace")), ""


# ── 执行与探针 ───────────────────────────────────────────────────

def run_cmd(cmd, timeout=30, home=None):
    env = dict(os.environ)
    env["HOME"] = home or HOME
    try:
        p = subprocess.run(cmd, shell=True, executable="/bin/bash",
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, env=env)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


IMMUN_LOG = os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/免疫抗体历史.md")
HITS_LOG = os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/免疫复发记录.md")


def _cmd_seen_count(path, cmd):
    """留痕台账里出现该 detect 命令的行数（纯读·零子进程）。查不到=0。"""
    if not os.path.isfile(path) or not cmd.strip():
        return 0
    try:
        data = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return 0
    return sum(1 for line in data.split("\n") if cmd.strip() in line)


def classify_probe(as_is, empty, ever_hit, immun_logged):
    """探针四态（v2.0.0 自纠：二态会把"真干净"误报成"不可证伪"=假红=报警疲劳）。

    ever_hit / immun_logged = 行为级留痕，作**正控**用（抗体历史上响过 ⇒ 天线是好的）。
    """
    if as_is == 0 and empty != 0:
        return "falsifiable_hit", "✅ 可证伪·当前命中（对象在=响，对象消=不响）"
    if as_is == 0 and empty == 0:
        return "always_true", "🔴 恒真嫌疑：对象消失后仍命中（假警报源·⛔永不转免疫）"
    if as_is != 0 and empty == 0:
        return "reverse_anomaly", "🟡 反向异常：空环境反而命中（detect 路径依赖有缺陷）"
    # 两态同为非 0：不命中。分不清"坑真没了"还是"天线恒盲"→ 用留痕当正控
    if ever_hit:
        return "immune_verified", "✅ 已免疫（有历史命中记录=%d 次=天线有效，当前不响）" % ever_hit
    if immun_logged:
        return "immune_logged", "✅ 转免疫已登记（免疫留痕 %d 条·⚠️但无命中史=尚缺正控）" % immun_logged
    return "no_evidence", "⚪ 不可判（当前不命中，但既无命中史也无免疫留痕=缺正控·⛔不得算已验收）"


def probe_falsifiable(cmd):
    """同一条 detect 跑两态（真实 HOME / 空 HOME），再叠行为级留痕正控。

    只**显形**不裁决修复（§八-3 保守判定）；返回 (as_is, isolated, kind, label)。
    """
    empty = tempfile.mkdtemp(prefix="gb-probe-")
    try:
        a, _, _ = run_cmd(cmd)
        b, _, _ = run_cmd(cmd, home=empty)
    finally:
        try:
            os.rmdir(empty)
        except OSError:
            pass
    kind, label = classify_probe(a, b, _cmd_seen_count(HITS_LOG, cmd),
                                 _cmd_seen_count(IMMUN_LOG, cmd))
    return a, b, kind, label


def fingerprint(wid, cmd):
    return hashlib.sha256(("%s|%s" % (wid, cmd.strip())).encode("utf-8")).hexdigest()[:12]


# ── 各工单诊断（只读取证·不改任何生产文件）────────────────────

def diagnose_w4():
    """交叉核对 skill_version_guard 的 --check 与 --report 两口径是否一致。"""
    c1, out1, _ = run_cmd('bash "%s" --check' % SKILL_VER_GUARD)
    c2, out2, _ = run_cmd('bash "%s" --report' % SKILL_VER_GUARD)
    lead = 0
    m = re.search(r'"skill_lead"\s*:\s*(\d+)', out1)
    if m:
        lead = int(m.group(1))
    leads = []
    for line in out2.split("\n"):
        if "SKILL领先" in line:
            parts = [x.strip() for x in line.split("|") if x.strip()]
            if len(parts) >= 4:
                leads.append({"skill": parts[0], "skill_version": parts[1],
                              "changelog_version": parts[2], "issue": parts[3]})
    contradict = (lead >= 1 and not leads) or (lead == 0 and leads)
    return {"check_stdout": out1.strip(), "report_stdout": out2.strip().split("\n")[0][:120],
            "skill_lead": lead, "report_leads": leads, "instrument_contradiction": contradict}


def diagnose_w5():
    settings = os.path.join(HOME, ".workbuddy/settings.json")
    kb_dir = os.path.join(HOME, "[记忆共享中心]/脚本中心/知识库设计哲学")
    has_inject = os.path.isfile(settings) and "kb_inject_prompt" in open(settings, encoding="utf-8", errors="replace").read()
    hits = []
    if os.path.isdir(kb_dir):
        for root, _, files in os.walk(kb_dir):
            for fn in sorted(files):
                if not fn.endswith(".md"):
                    continue
                fp = os.path.join(root, fn)
                try:
                    with open(fp, encoding="utf-8", errors="replace") as fh:
                        for i, line in enumerate(fh, 1):
                            if "待拍板" in line:
                                hist = any(k in line for k in ("已更正", "早期", "为看板漂", "收录"))
                                hits.append({"file": fp, "line": i,
                                             "content": line.strip()[:140], "historical": hist})
                except OSError:
                    continue
    return {"authority": settings, "authority_has_kb_inject": has_inject, "hits": hits,
            "true_pos": [h for h in hits if not h["historical"]],
            "false_pos": [h for h in hits if h["historical"]]}


def diagnose_w6():
    today = os.path.join(os.path.expanduser("[记忆共享中心]"), "工作日志/系统日志/系统日志_%s.md"
                         % datetime.now().strftime("%Y-%m-%d"))
    exists = os.path.isfile(today)
    has_line = exists and ("变更日志检测" in open(today, encoding="utf-8", errors="replace").read())
    return {"today_log": today, "log_exists": exists, "has_changelog_line": has_line}


def diagnose_w8():
    _, out, _ = run_cmd('grep -l "终检清单\\|终检锁\\|必须全部.*才能输出" '
                        '%s/[记忆共享中心]/技能配置/*/references/*.md 2>/dev/null' % HOME)
    files = [x.strip() for x in out.split("\n") if x.strip()]
    res = []
    for fp in files:
        _, o2, _ = run_cmd('grep -L "bash.*finalize\\|python3.*verify\\|exit code" "%s" 2>/dev/null' % fp)
        res.append({"file": fp, "basename": os.path.basename(fp),
                    "is_changelog": "CHANGELOG" in os.path.basename(fp).upper(),
                    "no_script_call": bool(o2.strip())})
    return {"candidates": res,
            "suspect": [r for r in res if r["no_script_call"] and not r["is_changelog"]],
            "false_pos": [r for r in res if r["is_changelog"]]}


def diagnose_w11():
    _, out, _ = run_cmd('grep -rl "你已质证\\|你已确认\\|你已拍板" '
                        '%s/[记忆共享中心]/知识库/AI学习库/ %s/[记忆共享中心]/记忆蓝图/ 2>/dev/null | grep -v "\\.bak"' % (HOME, HOME))
    files = [x.strip() for x in out.split("\n") if x.strip() and os.path.isfile(x.strip())]
    no_ev = []
    for fp in files:
        content = open(fp, encoding="utf-8", errors="replace").read()
        claims = [w for w in ("你已质证", "你已确认", "你已拍板") if w in content]
        ev = [w for w in ("你说", "你确认", "你拍板", "你纠正", "皮叔令") if w in content]
        if claims and not ev:
            lines = [{"line": i, "content": ln.strip()[:120]}
                     for i, ln in enumerate(content.split("\n"), 1) if any(c in ln for c in claims)][:3]
            no_ev.append({"file": fp, "basename": os.path.basename(fp),
                          "claims": claims, "claim_lines": lines})
    return {"scanned": len(files), "files_without_evidence": no_ev}


# ── 草案正文 ─────────────────────────────────────────────────────

def _fence(s, lang="bash"):
    return "```%s\n%s\n```" % (lang, s)


def build_draft(wid, real, diag, probe):
    """产出草案 dict：诊断 / 建议改法（提案文本·⛔不生效）/ 复验命令 / 可复验性声明。"""
    cls, why = SOURCE_CLASS[wid]
    src = real["src"]
    lineno = real["lineno"]
    cmd = real["cmd"]
    d = {"class": cls, "class_reason": why, "antibody_src": src, "antibody_line": lineno,
         "real_detect": cmd, "probe_kind": probe[2], "probe_label": probe[3],
         "falsifiable": probe[2] in ("falsifiable_hit", "immune_verified", "immune_logged"),
         "probe": {"as_is": probe[0], "empty_home": probe[1]}}

    if wid == "W4":
        if diag["instrument_contradiction"]:
            d["verdict"] = ("⛔ **仪器自相矛盾·本轮不可生成可信草案**：`--check` 报 skill_lead=%d，"
                            "`--report` 却列不出任何「SKILL领先」实例（`%s`）。"
                            "在两套口径互相矛盾的尺子上补 CHANGELOG=把噪音自动化。"
                            % (diag["skill_lead"], diag["report_stdout"][:60]))
            d["proposal"] = ("先查 `skill_version_guard.sh` 的 --check / --report 口径分裂根因"
                             "（同脚本两条路径对同一集合给出不同计数）。属 L2 功能坑，非文档坑。")
            d["reverify"] = "复跑 `bash %s --check` 与 `--report`，两者对「领先」的计数一致" % SKILL_VER_GUARD
            d["class"] = "no_source"
            d["class_reason"] = "仪器两口径互斥，修法方向本身待定"
        else:
            items = ["- 目标：`[记忆共享中心]/技能配置/%s/references/CHANGELOG.md`（PREPEND 新条目）"
                     % x["skill"] for x in diag["report_leads"]]
            d["verdict"] = "真坑：%d 个 Skill 版本领先于自身 CHANGELOG" % len(diag["report_leads"])
            d["proposal"] = _fence("\n".join(items) if items else "（无实例）", "markdown")
            d["reverify"] = "复跑 `bash %s --check` → skill_lead=0" % SKILL_VER_GUARD

    elif wid == "W5":
        tp, fp = diag["true_pos"], diag["false_pos"]
        d["verdict"] = ("权威源实盘：settings.json %s `kb_inject_prompt`；"
                        "文档残留「待拍板」真阳性 %d 处 / 历史叙述误命中 %d 处。"
                        % ("**含**" if diag["authority_has_kb_inject"] else "**不含**", len(tp), len(fp)))
        lines = ["| 文件 | 行 | 现状 | 建议 |", "|:---|:--:|:---|:---|"]
        for h in tp[:8]:
            lines.append("| `%s` | L%d | %s | 按权威源改状态词（已实挂·%s 实证） |"
                         % (os.path.relpath(h["file"], HOME), h["line"], h["content"][:48],
                            datetime.now().strftime("%Y-%m-%d")))
        d["proposal"] = "\n".join(lines) + "\n\n" + _fence(
            "# 权威源（真源·只读）\ngrep -o 'kb_inject_prompt[^\"]*' %s | head -1" % diag["authority"],
            "bash")
        d["reverify"] = "复跑真源抗体（同一命令）→ exit≠0 即转免疫；或在反哺日志更新 detect 后跑 --verify"
        if fp:
            d["note"] = ("抗体过宽：`grep -rl 待拍板 <整个设计哲学目录>` 会把 CHANGELOG/「已更正」历史句"
                         "也算真坑（本例 %d 处）。缩窄范围属**改判据**，见下方判据段。" % len(fp))

    elif wid == "W6":
        d["verdict"] = ("今日日志 %s；验证块「变更日志检测」行 %s。"
                        % ("存在" if diag["log_exists"] else "**不存在**",
                           "在" if diag["has_changelog_line"] else "**缺**"))
        d["proposal"] = ("坑本体（派生型）：向今日系统日志验证块补固定模板行"
                         "（内容=f(append_log_entry.py 模板)·无决定内容）。\n"
                         "⚠️ 但见「可复验性」段——若 detect 不可证伪，补完也永远不转免疫。")
        d["reverify"] = "复跑真源 detect：期望 exit≠0（免疫）。⛔恒真态下此判据永不满足"

    elif wid == "W8":
        d["verdict"] = ("命中候选 %d 个，其中 CHANGELOG 类误判 %d 个、疑似真坑 %d 个。"
                        % (len(diag["candidates"]), len(diag["false_pos"]), len(diag["suspect"])))
        d["proposal"] = "\n".join(
            ["- `%s`（无脚本调用声明）" % r["basename"] for r in diag["suspect"][:8]] or ["（无真阳性）"]) + \
            "\n\n**需人定**：每个 references 终检声明应对应哪个校验脚本（机械不可推）。"
        d["reverify"] = "复跑真源 detect → exit≠0"

    elif wid == "W11":
        n = diag["files_without_evidence"]
        d["verdict"] = ("扫描 %d 个含「你已…」标注的文件，其中 %d 个文件内无亲证事件词。"
                        % (diag["scanned"], len(n)))
        d["proposal"] = "\n".join(["- `%s`：%s" % (x["basename"], " / ".join(x["claims"])) for x in n[:8]]) \
            + ("\n\n⛔ **本条永不自动**：唯一『自动化修法』是替你造一段你的原话当证据，"
               "那会把签名虚标做成机制。可选处置只有两条，且都属价值层：\n"
               "① 你确认属实 → 由你补亲证事件行；② 属 AI 代标 → 把标注降级为「AI 推断·未亲证」。")
        d["reverify"] = "复跑真源 detect → exit≠0（或按判据段缩窄证据词表后复跑）"

    # 判据段（改 detect = L1c·只出提案·⛔不随草案自动生效）
    if probe[2] in ("always_true", "reverse_anomaly"):
        d["gate_fix"] = (
            "抗体**不可证伪**：真实 HOME 与空 HOME 两态退出码相同（%s=%s / %s=%s），"
            "即判定与检测对象无关 = 恒真或恒假形态。\n"
            "**必须先修判据**（改反哺日志真源·走 E 流程），否则本工单永远无法「转免疫」：\n"
            "- 现真源 detect：%s\n"
            "- 建议方向：用反断表达「对象在且坑在 → exit 0」，⛔不得以 `|| echo ...` 收尾"
            "（echo 恒 exit 0）。\n"
            "- 写入前必过：`python3 %s --check-cmd '<新命令>'`（C1-C6 门禁）。"
            % (probe[0], d["probe"]["as_is"], "空HOME", d["probe"]["empty_home"],
               _fence(cmd), GATE_PY))
    return d


WORK_ORDER_DOC = os.path.join(os.path.expanduser("[记忆共享中心]"), "成长箱/免疫修复工单.md")
DUE_SECTION = "## 六、待办分级与到期"


def parse_due_table(text):
    """解析工单 §六 表 → [(id, 项, 优先级, 到期, 归属, 状态)]。列序固定，非表行跳过。"""
    rows = []
    started = False
    for line in text.split("\n"):
        if line.startswith(DUE_SECTION):
            started = True
            continue
        if not started:
            continue
        if line.startswith("## ") and DUE_SECTION not in line:
            break
        if not line.startswith("| D"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6:
            rows.append(tuple(cells[:6]))
    return rows


def _notify(title, body):
    """macOS 系统通知（D12 消费端：不依赖 AI 会话在场、不依赖人记得去翻 log）。
    osascript 不可用/失败 → 只显形一行，⛔不影响退出码（通知是加法，不是主路）。"""
    script = 'display notification "%s" with title "%s"' % (body.replace('"', "'"), title.replace('"', "'"))
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            print("  ⚪ 系统通知未送达（osascript rc=%d）·留痕仍在 log" % r.returncode)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("  ⚪ 系统通知不可用（%s）·留痕仍在 log" % exc)


def run_due(today=None, notify=False):
    """到期/逾期显形（P2·防通道空转）。返回 0=无逾期 / 1=有逾期。"""
    if not os.path.isfile(WORK_ORDER_DOC):
        print("⛔ 工单表不存在：%s" % WORK_ORDER_DOC)
        return 1
    rows = parse_due_table(open(WORK_ORDER_DOC, encoding="utf-8", errors="replace").read())
    today = today or datetime.now().strftime("%Y-%m-%d")
    open_rows = [r for r in rows if not r[5].startswith("✅")]
    print("免疫工单到期检查（今天 %s · 挂账 %d 条·另有已闭环 %d 条）"
          % (today, len(open_rows), len(rows) - len(open_rows)))
    overdue = 0
    urgent = []
    for rid, item, pri, due, owner, state in rows:
        if state.startswith("✅"):
            continue
        days = (_iso(due) - _iso(today)).days if _iso(due) and _iso(today) else None
        if days is None:
            mark, txt = "⚪", "到期日不可解析（⛔不猜）"
        elif days < 0:
            mark, txt = "🔴", "已逾期 %d 天" % -days
            overdue += 1
            urgent.append("%s(逾期%d天)" % (rid, -days))
        elif days <= 3:
            mark, txt = "🟠", "%d 天内到期" % days
            urgent.append("%s(%d天内)" % (rid, days))
        else:
            mark, txt = "🟢", "余 %d 天" % days
        print("  %s %s[%s] 到期%s · 归属:%s — %s（%s）" % (mark, rid, pri, due, owner, txt, item[:46]))
    print("  ── 逾期 %d 条" % overdue)
    if notify and urgent:
        _notify("免疫挂账到期", "逾期/3天内到期共 %d 条：%s" % (len(urgent), "、".join(urgent[:4])))
    return 1 if overdue else 0


def _iso(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None

# ── 落盘（写域锁死）─────────────────────────────────────────────

def _assert_in_draft_dir(path):
    ap = os.path.abspath(path)
    base = os.path.abspath(DRAFT_DIR)
    if os.path.commonpath([ap, base]) != base:
        raise RuntimeError("写域越界（G10 同族）：%s 不在 %s 内" % (ap, base))
    return ap


def ledger_rows():
    if not os.path.isfile(LEDGER):
        return []
    out = []
    for line in open(LEDGER, encoding="utf-8", errors="replace"):
        if line.startswith("| 20") or line.startswith("| 20"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 6:
                out.append(cells)
    return out


def ledger_append(wid, cls, fp, path, verdict="⬜待批"):
    _assert_in_draft_dir(LEDGER)
    os.makedirs(DRAFT_DIR, exist_ok=True)
    if not os.path.isfile(LEDGER):
        with open(LEDGER, "w", encoding="utf-8") as f:
            f.write("# L1 草案审批台账（append-only·免疫自愈 L1 毕业数据源）\n\n"
                    "> 生成器：immunity_l1_draft.py v%s。⛔本文件只记处置，不改生产文件。\n"
                    "> 列：日期 | 工单 | 修法来源 | 指纹 | 草案/动作 | 处置\n"
                    "> 毕业判据（`--graduation`）：同类 `derived` 连续 ≥5 次「原样批」且 0 次「否」→ 该判据类够格升自动写回；"
                    "`skeleton`/`no_source` 永不升级（愿景红线：价值层永不裁决）。\n\n"
                    "| 日期 | 工单 | 修法来源 | 指纹 | 草案/动作 | 处置 |\n|:---|:--:|:--:|:---|:---|:--:|\n")
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write("| %s | %s | %s | %s | %s | %s |\n"
                % (datetime.now().strftime("%Y-%m-%d %H:%M"), wid, cls, fp, path, verdict))


def render_md(wid, title, diag, d):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = ["# %s 修复草案（%s）" % (wid, now), "",
         "> 生成器：immunity_l1_draft.py v%s ｜ 立场卡 S938：本条独立走完整 Loop，⛔不批量跳过" % VERSION,
         "> ⛔ 本文件是**草案**——不是已完成的修复。生产文件一个字节都没被本工具改动（写域锁死在 成长箱/修复草案/）。",
         "",
         "## 一、抗体真源定位（单源·脚本不自带判据）",
         "",
         "| 项 | 值 |", "|:---|:---|",
         "| 工单 | %s %s |" % (wid, title),
         "| 真源文件/行 | `%s` L%s |" % (d["antibody_src"], d["antibody_line"]),
         "| 真源 detect | %s |" % ("`%s`" % d["real_detect"].replace("|", "\\|")),
         "| 本工单判定 | %s |" % ("🔴 命中（坑在）" if d["probe"]["as_is"] == 0 else "✅ 免疫（坑不在）"),
         "",
         "## 二、修法来源三态（决定该不该要人批）",
         "",
         "| 字段 | 值 |", "|:---|:---|",
         "| 分类 | **%s**（`%s`） |" % (CLS_LABEL[d["class"]], d["class"]),
         "| 依据 | %s |" % d["class_reason"],
         "| 可否自动写回 | %s |" % ("🟢 够格候选（仍需毕业计数）" if d["class"] == "derived" else "⛔ 永不（含决定内容）"),
         "| 抗体判定力 | %s |" % d.get("probe_label", "—"),
         "| 探针两态码 | 真 HOME=%s / 空 HOME=%s |" % (d["probe"]["as_is"], d["probe"]["empty_home"]),
         "",
         "## 三、诊断结论",
         "",
         d.get("verdict", "—"), "",
         ]
    if d.get("note"):
        L += ["## 三·补、抗体口径", "", d["note"], ""]
    L += ["## 四、建议改法（草案·待人批，⛔不自动生效）", "", d.get("proposal", "—"), ""]
    if d.get("gate_fix"):
        L += ["## 四·补、判据修正（L1c·改判据本体）", "", d["gate_fix"], ""]
    L += ["## 五、复验（改完必须复跑·不接受『看起来对了』）", "",
          "- 判定标准：%s" % d.get("reverify", "—"),
          "- 分批复跑（沙箱文件配额限制）：",
          _fence("GB_ANTIBODY_LIMIT=10 GB_ANTIBODY_ONLY=1 bash %s --summary" % CHECK_SH),
          "- 单条复验（本工单真源）：",
          _fence("python3 %s --verify --%s" % (os.path.abspath(__file__), wid.lower())),
          "",
          "## 六、处置",
          "",
          "批 → 由人/AI 按第四节执行修复 → 复跑第五节 → 抗体转免疫 → 工单表 ⬜→✅ + 登记退役台账。",
          "处置记入台账：`python3 %s --verdict %s <原样批|改后批|否>`" % (os.path.abspath(__file__), wid),
          ""]
    return "\n".join(L)


# ── 主流程 ───────────────────────────────────────────────────────

def diagnose_one(wid, real):
    return {"W4": diagnose_w4, "W5": diagnose_w5, "W6": diagnose_w6,
            "W8": diagnose_w8, "W11": diagnose_w11}[wid]()


def run(wids=None, as_json=False, quiet=False):
    rows, err = load_real_antibodies()
    if rows is None:
        print("⛔ 真源不可读（Fail-Closed·⛔不回退内置副本）：%s" % err)
        return 1
    resolved, missing, ambiguous = resolve_anchors(rows)
    results = []
    for wid in (wids or sorted(TITLES.keys())):
        if wid in missing:
            results.append({"id": wid, "status": "⛔真源未定位（锚点漂移或抗体被删）", "fail_closed": True})
            print("  %s ⛔ 真源未定位 → 不出草案（宁缺不编）" % wid)
            continue
        if wid in ambiguous:
            cand = "；".join("L%s:%s" % (r["lineno"], r["title"][:34]) for r in ambiguous[wid])
            results.append({"id": wid, "status": "⛔真源定位歧义（%d 候选）" % len(ambiguous[wid]),
                            "fail_closed": True})
            print("  %s ⛔ 定位歧义 → 不出草案（⛔不猜）：%s" % (wid, cand))
            continue
        real = resolved[wid]
        probe = probe_falsifiable(real["cmd"])
        entry = {"id": wid, "title": TITLES[wid], "antibody": real,
                 "as_is": probe[0], "empty_home": probe[1],
                 "probe_kind": probe[2], "probe_label": probe[3]}
        if probe[0] != 0:
            closed = probe[2] in ("falsifiable_hit", "immune_verified", "immune_logged")
            entry["closed"] = closed
            entry["status"] = ("✅ 真源不命中·判定力成立" if closed else "⚪ 真源不命中·缺正控")
            results.append(entry)
            print("  %s %s — %s" % (wid, entry["status"], probe[3]))
            continue
        diag = diagnose_one(wid, real)
        draft = build_draft(wid, real, diag, probe)
        entry.update({"status": "🔴 真源命中·草案已生成", "draft": draft, "diag": diag})
        os.makedirs(DRAFT_DIR, exist_ok=True)
        fname = "%s_%s.md" % (datetime.now().strftime("%Y-%m-%d"), wid)
        path = _assert_in_draft_dir(os.path.join(DRAFT_DIR, fname))
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_md(wid, TITLES[wid], diag, draft))
        fp = fingerprint(wid, real["cmd"])
        entry["fingerprint"] = fp
        entry["draft_path"] = path
        # 幂等：同指纹的「生成行」已有则不重复追加（G9 判据幂等）
        if not any(r[3] == fp and r[5] == "⬜待批" for r in ledger_rows()):
            ledger_append(wid, draft["class"], fp, os.path.relpath(path, HOME))
        results.append(entry)
        print("  %s 🔴 命中 → 草案 %s [%s·可证伪=%s]"
              % (wid, os.path.relpath(path, HOME), CLS_LABEL[draft["class"]],
                 "是" if draft["falsifiable"] else "否"))
    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    bad = [r for r in results if r.get("fail_closed") or r.get("closed") is False
           or r.get("status", "").startswith("🔴")]
    return 1 if bad else 0


def run_verify(wids=None):
    rows, err = load_real_antibodies()
    if rows is None:
        print("⛔ 真源不可读：%s" % err)
        return 1
    resolved, missing, ambiguous = resolve_anchors(rows)
    all_immune = True
    print("L1 复验·**只跑真源 detect**（v2.0.0：脚本无权自带判据）")
    for wid in (wids or sorted(TITLES.keys())):
        if wid in missing or wid in ambiguous:
            why = "未定位" if wid in missing else "定位歧义(%d候选)" % len(ambiguous[wid])
            print("  %s ⛔ 真源%s → 复验不成立" % (wid, why))
            all_immune = False
            continue
        real = resolved[wid]
        a, b, kind, label = probe_falsifiable(real["cmd"])
        print("  %s %s — %s [%s L%s]" % (wid, label, TITLES[wid], real["src"], real["lineno"]))
        if a == 0 or kind == "no_evidence":
            all_immune = False
    return 0 if all_immune else 1


def run_verdict(wid, verdict):
    rows, err = load_real_antibodies()
    if rows is None or wid not in dict(SOURCE_ANCHORS):
        print("⛔ 无法记处置：%s" % (err or "未知工单 %s" % wid))
        return 1
    real = resolve_anchors(rows)[0].get(wid)
    if not real:
        print("⛔ %s 真源未定位，处置无处可锚" % wid)
        return 1
    ledger_append(wid, SOURCE_CLASS[wid][0], fingerprint(wid, real["cmd"]),
                  "（处置登记）", verdict)
    print("✅ %s 处置=%s（台账：%s）" % (wid, verdict, LEDGER))
    return 0


def run_graduation():
    rows = ledger_rows()
    print("L1 毕业判定（数据源=审批台账·append-only·⛔不凭印象）")
    print("判据：derived 类连续 ≥5 次「原样批」且 0 次「否」→ 够格申请升自动写回（改白名单仍须你确认）")
    if not rows:
        print("  （台账为空——还没有一次真实审批，毕业计数无从谈起）")
        return 1
    by = {}
    for r in rows:
        by.setdefault(r[1], []).append(r)
    print("\n| 工单 | 类 | 原样批 | 改后批 | 否 | 最新连续原样批 | 结论 |")
    print("|:--:|:--:|:--:|:--:|:--:|:--:|:---|")
    for wid in sorted(by):
        seq = by[wid]
        cls = seq[-1][2]
        ok = sum(1 for r in seq if r[5] == "原样批")
        edited = sum(1 for r in seq if r[5] == "改后批")
        no = sum(1 for r in seq if r[5] == "否")
        streak = 0
        for r in reversed(seq):
            if r[5] == "原样批":
                streak += 1
            elif r[5] in ("否", "改后批"):
                break
        if cls != "derived":
            concl = "⛔ 永不升级（%s含决定内容）" % CLS_LABEL[cls]
        elif streak >= 5 and no == 0:
            concl = "🟢 够格升自动写回（待你改白名单）"
        else:
            concl = "🟡 数据不足（%d/5）" % streak
        print("| %s | %s | %d | %d | %d | %d | %s |" % (wid, CLS_LABEL[cls], ok, edited, no, streak, concl))
    return 0


# ── 正控夹具（P-L1a 根治 · 2026-09-18）──────────────────────────
# 为什么必须有：一条抗体"当前不命中"有两种可能——坑真被修好了，或这根天线根本不响。
#   只看退出码分不清（=判据缺一半·缺正控）。故在**临时 HOME**里各造一个"坑在"与"坑已修"
#   的世界，跑同一条真源 detect：坑在必须 exit 0、坑已修必须 exit≠0，两态都对才算检波器活着。
# 边界：⛔全程不写生产文件（只写 tempfile.mkdtemp 下的假树，跑完 rmtree 自清理）；
#   正控证的是 **detect 的逻辑灵敏度**，不证"坑此刻在不在"（后者由 --verify 答）。

_TODAY = datetime.now().strftime("%Y-%m-%d")
_KB_DIR = "[记忆共享中心]/脚本中心/知识库设计哲学"


def _mk(root, rel, content):
    p = os.path.join(root, rel)
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)
    return p


def _both(*pairs):
    return lambda r: [_mk(r, rel, c) for rel, c in pairs]


FAKE_GUARD_LEAD = """#!/bin/sh
echo '{"skills_with_version": 9, "skill_lead": 1, "alarm": true}'
"""
FAKE_GUARD_CLEAN = """#!/bin/sh
echo '{"skills_with_version": 9, "skill_lead": 0, "alarm": false}'
"""
UPS_PIT = (".workbuddy/settings.json",
           '{"hooks":{"UserPromptSubmit":[{"command":"kb_inject_prompt.py"}]}}\n')
UPS_INDEX_PIT = (_KB_DIR + "/INDEX.md", "| 激活 | ⏳ 待决 | 门禁时机 A/B 待拍板 |\n")
UPS_INDEX_CLEAN = (_KB_DIR + "/INDEX.md", "| 激活 | ✅ 已落地（settings.json 实证） | A+B 双挂对称 |\n")
LOG_TODAY = ("[记忆共享中心]/工作日志/系统日志/系统日志_%s.md" % _TODAY, "## 条目\n")
TERMINAL_PIT = ("[记忆共享中心]/技能配置/fake-skill/references/终检.md",
                "## 终检清单\n- 必须全部通过才能输出\n")
TERMINAL_CLEAN = ("[记忆共享中心]/技能配置/fake-skill/references/终检.md",
                  "## 终检清单\n- 收工前跑 `python3 verify_checklist_gate.py` 退出码 0 才能输出\n")
CLAIM_PIT = ("[记忆共享中心]/知识库/AI学习库/立场卡#fake.md", "本卡结论：你已质证\n")
CLAIM_CLEAN = ("[记忆共享中心]/知识库/AI学习库/立场卡#fake.md",
               "本卡结论：你已质证\n- 置信度: 🟢 · 自述\n- 碰撞来源: 你原话\n")

POSITIVE = {
    "W4": (lambda r: _mk(r, "[记忆共享中心]/脚本中心/changelog-guard/skill_version_guard.sh", FAKE_GUARD_LEAD),
           lambda r: _mk(r, "[记忆共享中心]/脚本中心/changelog-guard/skill_version_guard.sh", FAKE_GUARD_CLEAN)),
    "W5": (_both(UPS_PIT, UPS_INDEX_PIT), _both(UPS_PIT, UPS_INDEX_CLEAN)),
    "W6": (lambda r: _mk(r, LOG_TODAY[0], LOG_TODAY[1]),
           lambda r: (_mk(r, LOG_TODAY[0], LOG_TODAY[1]),
                      _mk(r, ".cache/systemlogger/guard_line.txt", "fresh-today"))),
    "W8": (lambda r: _mk(r, *TERMINAL_PIT), lambda r: _mk(r, *TERMINAL_CLEAN)),
    "W11": (lambda r: _mk(r, *CLAIM_PIT), lambda r: _mk(r, *CLAIM_CLEAN)),
}


def run_positive_controls(wids=None, quiet=False):
    """返回 (结果表, 退出码)。结果行=(wid, ok, 坑在码, 坑修码, 真源位置)。"""
    import shutil
    rows, err = load_real_antibodies()
    if rows is None:
        print("⛔ 真源不可读：%s" % err)
        return [], 1
    resolved, missing, ambiguous = resolve_anchors(rows)
    out = []
    for wid in (wids or sorted(POSITIVE)):
        if wid not in resolved:
            out.append((wid, None, None, None, "真源未定位/歧义(%d候选)" % len(ambiguous.get(wid, []))))
            continue
        cmd = resolved[wid]["cmd"]
        base = tempfile.mkdtemp(prefix="gb-ctl-")
        try:
            pit = os.path.join(base, "pit")
            cln = os.path.join(base, "cln")
            os.makedirs(pit)
            os.makedirs(cln)
            POSITIVE[wid][0](pit)
            POSITIVE[wid][1](cln)
            hp, _, _ = run_cmd(cmd, home=pit)
            hc, _, _ = run_cmd(cmd, home=cln)
        finally:
            shutil.rmtree(base, ignore_errors=True)
        out.append((wid, hp == 0 and hc != 0, hp, hc,
                    "%s L%s" % (resolved[wid]["src"], resolved[wid]["lineno"])))
    if not quiet:
        for wid, ok, hp, hc, loc in out:
            if ok is None:
                print("  %s ⚪ 跳过 — %s" % (wid, loc))
            else:
                print("  %s %s 坑在=%s 坑修=%s — %s"
                      % (wid, "✅ 检波器活着" if ok else "🔴 检波器有缺陷", hp, hc, loc))
    return out, (1 if any(x[1] is not True for x in out) else 0)


# ── 自测夹具（§3.0·5 上线必带·测线上本体非副本）────────────────

def selftest():
    fails = []
    n_ck = [0]

    def ck(name, cond, detail=""):
        n_ck[0] += 1
        if not cond:
            fails.append("%s %s" % (name, detail))
            print("❌ %s %s" % (name, detail))
        else:
            print("✅ %s" % name)

    # T1 解析器：真源 TSV → 锚点命中（且取的是 gate 给的命令，不是任何内置值）
    tsv = "\x1f".join(["规范反哺日志.md", "2857", "! grep -q 'X' '/abs/log.md'",
                       "当日系统日志条目写入后，验证块是否包含变更日志检测行", "", "", ""])
    rows = parse_gate_tsv(tsv)
    res, miss, amb = resolve_anchors(rows)
    ck("T1 解析器+锚点命中", "W6" in res and res["W6"]["cmd"] == "! grep -q 'X' '/abs/log.md'", str(rows))
    # T1b 别名锚抗改名：标题被追加「v1.1修正：…」后仍须唯一定位（2026-09-18 实测失效场景）
    tsv_b = "\x1f".join(["规范反哺日志.md", "2857", "! grep -q 'Y' '/abs/log.md'",
                         "当日系统日志条目写入后，验证块是否包含变更日志检测行（v1.1修正：检测对象改 guard_line 缓存）",
                         "", "", ""])
    resb, missb, ambb = resolve_anchors(parse_gate_tsv(tsv_b))
    ck("T1b 别名锚抗改名", "W6" in resb and not ambb.get("W6"), str(missb))
    # T2 Fail-Closed：锚点在真源查无 → 必须进 missing，⛔不得回退副本
    res2, miss2, amb2 = resolve_anchors([])
    ck("T2 真源缺失=Fail-Closed", not res2 and len(miss2) == 5, str(miss2))
    # T3 恒真探针抓得住（真源 W6 历史形态：|| echo 收尾）
    a, b, kind3, _l3 = probe_falsifiable('bash -c \'test -f "$HOME/不存在/1970-01-01.md" '
                                         '&& grep -q "x" "$HOME/不存在/1970-01-01.md" && echo v || echo m\'')
    ck("T3 恒真抗体被抓", kind3 == "always_true", "as_is=%s empty=%s kind=%s" % (a, b, kind3))
    # T4 可证伪抗体不误伤：对象=线上本体（真 HOME 命中 / 空 HOME 对象消失），零写盘副作用
    self_path = os.path.abspath(__file__)
    t4cmd = 'grep -q "def selftest" "$HOME/%s"' % os.path.relpath(self_path, HOME)
    a4, b4, kind4, _l4 = probe_falsifiable(t4cmd)
    ck("T4 可证伪不误伤", kind4 == "falsifiable_hit" and a4 == 0 and b4 != 0,
       "as_is=%s empty=%s kind=%s" % (a4, b4, kind4))
    # T8 四态判定纯函数（v2.0.0 自纠：两态同码=1 曾被误报成"不可证伪"=假红）
    ck("T8 四态判定齐备", [classify_probe(*x)[0] for x in [
        (0, 1, 0, 0), (0, 0, 9, 9), (1, 0, 0, 0), (1, 1, 5, 0), (1, 1, 0, 2), (1, 1, 0, 0)]]
       == ["falsifiable_hit", "always_true", "reverse_anomaly",
           "immune_verified", "immune_logged", "no_evidence"])
    # T5 写域锁死：越界路径必须抛
    try:
        _assert_in_draft_dir(os.path.join(os.path.expanduser("[记忆共享中心]"), "变更日志.md"))
        ck("T5 写域锁死", False, "越界未抛异常")
    except RuntimeError:
        ck("T5 写域锁死", True)
    # T6 三态分类齐备 + 派生型以外的类不参与毕业
    ck("T6 三态分类齐备", all(w in SOURCE_CLASS for w in TITLES)
       and all(SOURCE_CLASS[w][0] in ("derived", "skeleton", "no_source") for w in TITLES))
    # T7 台账幂等 + 毕业判据（临时目录隔离·自清理）
    global DRAFT_DIR, LEDGER
    _saved = (DRAFT_DIR, LEDGER)
    tmpd = tempfile.mkdtemp(prefix="gb-l1test-")
    DRAFT_DIR, LEDGER = tmpd, os.path.join(tmpd, "审批台账.md")
    try:
        ledger_append("W5", "derived", "fp1", "x.md")
        ledger_append("W5", "derived", "fp1", "x.md")
        ck("T7a 台账可追加且行格式可解析", len(ledger_rows()) == 2, str(len(ledger_rows())))
        for _ in range(5):
            ledger_append("W5", "derived", "fp2", "（处置登记）", "原样批")
        ledger_append("W11", "no_source", "fp3", "（处置登记）", "原样批")
        rows2 = ledger_rows()
        by = {}
        for r in rows2:
            by.setdefault(r[1], []).append(r)
        w5 = by["W5"]
        streak = 0
        for r in reversed(w5):
            if r[5] == "原样批":
                streak += 1
            else:
                break
        ck("T7b derived 5连批→够格", streak >= 5, "streak=%s" % streak)
        ck("T7c no_source 永不升级", by["W11"][-1][2] == "no_source")
    finally:
        DRAFT_DIR, LEDGER = _saved
        import shutil
        shutil.rmtree(tmpd, ignore_errors=True)
    # T9 正控夹具：五条真源 detect 必须"坑在能响、坑修能停"（P-L1a 根治·防恒盲天线）
    _ctl, ctl_rc = run_positive_controls(quiet=True)
    ck("T9 五工单正控全通过", ctl_rc == 0 and len(_ctl) == 5,
       str([(w, k, a, b) for w, k, a, b, _l in _ctl]))
    total = n_ck[0]
    if fails:
        print("🔴 immunity_l1_draft 自测失败 %d/%d" % (len(fails), total))
        return 1
    print("✅ immunity_l1_draft 自测通过：%d/%d（含防自证闭环 T1/T2 + 恒真探针 T3/T4 + 写域锁 T5 + 毕业判据 T7）"
          % (total, total))
    return 0


# ── CLI ─────────────────────────────────────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="L1 修复草案生成器 v%s（真源单一化）" % VERSION)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true", help="复跑真源 detect 复验")
    ap.add_argument("--graduation", action="store_true", help="按台账算毕业状态")
    ap.add_argument("--verdict", nargs=2, metavar=("WID", "处置"),
                    help="记审批处置：原样批|改后批|否")
    ap.add_argument("--notify", action="store_true",
                    help="配合 --due：逾期/3天内到期时发 macOS 系统通知（D12 消费端）")
    ap.add_argument("--due", action="store_true",
                    help="工单 §六 到期/逾期显形（P2·launchd 每日调用）")
    ap.add_argument("--control", action="store_true",
                    help="跑正控夹具：证明每条真源 detect 能响也能停")
    ap.add_argument("--self-test", action="store_true", dest="selftest")
    for wid in sorted(TITLES):
        ap.add_argument("--%s" % wid.lower(), action="store_true", dest=wid.lower(),
                        default=False, help="仅处理该工单")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.due:
        return run_due(notify=a.notify)
    if a.control:
        _o, rc = run_positive_controls()
        return rc
    if a.verdict:
        return run_verdict(a.verdict[0].upper(), a.verdict[1])
    sel = [w for w in sorted(TITLES) if getattr(a, w.lower(), False)] or None
    if a.verify:
        return run_verify(sel)
    return run(sel, as_json=a.json)


if __name__ == "__main__":
    sys.exit(main())
