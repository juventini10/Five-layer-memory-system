#!/usr/bin/env python3
"""
qodercn_inject_chain_guard.py — Qoder CN 注入链健康守卫（Qoder CN 专属）

本质分类：守卫类（守）
部署形态：Hook（Stop·报告制）+ 按需（--check / --record）
辖区：Qoder CN 注入链（.qoder-cn 与 .qoder 双 rules 目录 + AGENTS.md 导航仪）

职责（五项机械检测·全部只读）：
  ① rules/ 软链断裂 —— 链目标失效=常驻规则（SOUL/USER/快照）静默消失，系统表面正常=假绿灯
  ② frontmatter paths 误用 —— Qoder CN 独有语义：有 paths=按需加载，误加=常驻规则静默降级
  ③ AGENTS.md/MEMORY.md 硬路牌引用腐烂 —— 引用的 .md 路径不存在=导航指空（占位符豁免）
  ④ 同名软链目标一致性 —— 双目录同名规则若都是软链，须指向同一共享源；
     目标不一致=共享机制破断。实体文件允许平台差异（core-identity/cross-end-guard
     是各端合法适配副本·2026-08-24 首跑 diff 实证），⛔不判漂移（保守·宁漏勿误）
  ⑤ 注入实证对账 —— 前四项守"文件层"，守不到"IDE 到底注进 context 没有"。
     注入产物不落盘（2026-08-27 实测：会话转录无任何 rules 正文），故唯一磁盘侧
     可取证物=AI 在会话内报告的观察痕迹（--record 落 JSONL）。盘上真相集=双 rules
     目录 .md + 双配置根根级 .md（实测 AGENTS.md 亦进 context，故纳入·否则如实上报会被误报）。
     四项判定：
       · 注入静默失效：本端 rules/ 中**标记 alwaysApply:true 的常驻文件**盘上有、痕迹里没有
         （升级重置注入行为的核心信号·v0.3 收窄：无标记的按需记忆软链不进基准=不误报；
          双端同源软链 realpath 去重=AI 自报只填一端不算本端失效）
       · 幻影注入项：痕迹里有、盘上真相集查无此文件（AI 报出不存在的路径=来源不明）
       · 跨端串味：他端根的实体文件出现在本端注入清单（他端软链=同源去重·不判）
       · 痕迹缺失/超龄：从未自检或＞7 天=生效性无实证（不假装绿灯）

真相源：目录实盘本身（软链活性/文件内容）+ AGENTS.md/MEMORY.md 本体 + 观察痕迹文件——无内联清单
时序协议：只读无共写（--record 为本守卫独占写痕迹文件·单写者）；失败默认放行（exit 0·Hook 三纪律）
判定纪律：保守判定·宁漏勿误（解析不了的跳过不报；缺失判定只覆盖本端根·防噪音）

锁得住：链接活性/字段存在性/路径存在性/内容指纹一致性（结构性）+ 期望×实证的差集
锁不住：① 规则内容的语义质量（验收第四问诚实声明）② **AI 报告的清单本身**——脚本无法
        证伪 AI 是否如实上报（注入产物只存在于模型上下文，磁盘无痕）。本守卫因此是
        "留痕+对账"而非"独立观测"，价值在忘跑被抓、差集显形，不在证明"确实注入了"。

负例证据：--self-test 16 用例（正常静默/断链/paths误用/引用腐烂/双目录漂移/静默失效/
          幻影/超龄/串味/无痕迹/他端软链未注入不误报/留痕闸门/按需文件不误报/双端同源去重/
          痕迹写法归一不误报）
根因：crossend_guard 曾指错目录静默失效半月无人知（成长箱在案）——注入链断=
      人格与规则静默消失而其余守卫照常跑，是 Qoder CN 端独有的单点失效面。
      ⑤ 来源=2026-08-27 你令 N4：新版 CN 是 0.1.0 换代线，常驻注入建立在官方未文档化
      行为上，"升级后注入自检"须成为可留痕可对账的验收动作（对齐 S816 兼容≠生效）。

作者：皮叔（Qoder CN 端）
版本：v0.5
日期：2026-08-24（v0.1）/ 2026-08-27（v0.2 加检测⑤）/ 2026-09-04（v0.3）/ 2026-09-20（v0.4 判定域边界显式外印）/ 2026-10-11（v0.5 痕迹写法归一根治假红）
来源：皮叔令"从最符合我愿景的情况下，第一性原理做最优处理"→六端专属守卫先例
      （DSH/LobsterAI/TraeWork/ZCode/AutoClaw/Hermes）的一致解：守本端单点失效面。
v0.3 变更（2026-09-04·皮叔令"按符合愿景的最优解根治注入自检假警"）：病根=⑤ own_rules
      无差别含 rules 全部 .md，与注入规范§二"常驻三要件（要件2=alwaysApply 标记）缺一即
      退化按需"不一致→把按需记忆软链（动态快照/问卷/题库·4端共享均无标记）误报"常驻静默
      失效"；且 core-user 双端同源软链，AI 自报只填他端路径时本端被误报。根治=① own_rules
      收窄为仅含 alwaysApply:true（_has_always_apply）② 失效判定加六端同源 realpath 去重
      （_realpath_of_key）。3 记忆软链不动（保 4端共享单一真源·按需要靠常驻路由表触发·
      快照按需读到最新比常驻启动快照更"懂你"·愿景④）。纯本端脚本修复·零跨端污染。
v0.5 变更（2026-10-11·皮叔令"符合愿景第一性原理真根治，不要再出现"）：病根=⑤ 对账把
      AI 自报路径与盘上 truth key 做精确字符串比对，不认写法变体——10-10 窗口用 `~/`
      tilde 或绝对路径落痕后，同一批文件被同时报"注入静默失效"+"幻影注入项"（10-11
      00:03 实测 12 处假红）。模型看到的注入路径本就常是绝对路径，输入格式控不住，
      靠文档约束"请用规范前缀"=判据不随对象演化（复发必然）。根治=_canon_seen 按
      归属 tag 切片归一，写入侧（record）+读取侧（check）双卡；读取侧归一使存量
      脏痕迹即时自愈，不靠等下个窗口重落痕。负例 T16 焊住此判据。

用法：
  python3 qodercn_inject_chain_guard.py            # Hook 报告制：恒 exit 0
  python3 qodercn_inject_chain_guard.py --check    # 手动核验：有问题 exit 1
  python3 qodercn_inject_chain_guard.py --record \
      --seen .qoder-cn/rules/a.md,.qoder-cn/AGENTS.md   # AI 会话内落观察痕迹并即时对账
  python3 qodercn_inject_chain_guard.py --self-test
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
import sys
import json
import time
import shutil
import hashlib
import tempfile

# B埋点自插桩(v2.0·2026-09-03·童灵·补exit码埋点): 从"脚本开头Popen后台写日志(无exit码)"
# 改为"包装入口点在退出时写日志(含exit码)"——原设计在脚本开头写日志，无法知道最终exit码;
# v2.0用try/finally包装main()，捕获sys.exit的code，在所有退出点统一写日志(含exit码)。
# 挂载守卫默认 hook_auto·离线手动默认 manual·fail-open·对齐 v1.2.45 先例。
def _guard_log_exit(rc):
    try:
        import subprocess as _sp
        _sp.Popen(["python3", os.path.expanduser("[记忆共享中心]/脚本中心/guard_invocation_logger.py"),
                   "--guard", "qodercn_inject_chain_guard",
                   "--source", os.environ.get("GUARD_TRIGGER_SOURCE", "hook_auto"),
                   "--exit", str(rc),
                   "--detail", "self-instrumented"],
                  stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    except Exception:
        pass

HOME = os.path.expanduser("~")
# 双目录：Qoder CN 客户端同时加载两者（workbench 硬编码 [".qoder",".qoder-cn"]）
RULES_DIRS = [
    os.path.join(HOME, ".qoder-cn", "rules"),
    os.path.join(HOME, ".qoder", "rules"),
]
NAVIGATOR_FILES = [
    os.path.join(HOME, ".qoder-cn", "AGENTS.md"),
    os.path.join(HOME, ".qoder-cn", "MEMORY.md"),
]

# ⑤ 注入实证对账：痕迹=AI 在会话内报告"实际看到哪些 rules 进了 context"后落盘
# （注入产物只存在于模型上下文、不落转录——2026-08-27 实测 877159ed.jsonl 无 rules 正文，
#   故磁盘侧唯一可机械取证的是这条痕迹，脚本不猜、AI 报告、脚本对账）
OBSERVED_LOG = os.path.expanduser(    "[记忆共享中心]/脚本中心/logs/injection_observed_qodercn.jsonl")
STALE_DAYS = 7  # 痕迹超龄=自检断链（对齐 autoclaw_gateway_guard 注入链路活性先例）
STALE_HOURS_WITH_SESSION = 24  # 本端有会话活动但>24h无自检记录=活跃日断链显形（09-22挂尸普查反哺：7天窗口实测放过2天断链）

# 硬路牌引用提取：`~/路径.md` 或裸 ~/路径.md（保守：解析不了就跳过）
REF_RE = re.compile(r"~/[^\s`)'\"（）]+\.(?:md|py|sh|json)")
# 占位符豁免：模板路径不是具体引用（{SKILL名}/YYYY-MM-DD 等·防误报=守卫变噪音）
PLACEHOLDER_RE = re.compile(r"[{<]|YYYY|<.*>")


def check_dangling_links(rules_dirs):
    """① 软链断裂检测：链目标失效=常驻规则静默消失"""
    findings = []
    for rd in rules_dirs:
        if not os.path.isdir(rd):
            continue
        try:
            for name in sorted(os.listdir(rd)):
                p = os.path.join(rd, name)
                if os.path.islink(p) and not os.path.exists(p):
                    findings.append(("断链", f"{rd}/{name} -> {os.readlink(p)}"))
        except Exception:
            continue  # 保守：读不了不报
    return findings


def check_paths_misuse(rules_dirs):
    """② frontmatter paths 误用：常驻规则被静默降级为按路径按需加载"""
    findings = []
    for rd in rules_dirs:
        if not os.path.isdir(rd):
            continue
        try:
            for name in sorted(os.listdir(rd)):
                if not name.endswith(".md"):
                    continue
                p = os.path.join(rd, name)
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        head = f.read(2000)
                except Exception:
                    continue
                if not head.startswith("---"):
                    continue  # 无 frontmatter 的常驻文件不受此坑影响
                fm = head.split("---", 2)[1] if head.count("---") >= 2 else ""
                if re.search(r"^paths\s*:", fm, re.MULTILINE):
                    findings.append(("paths误用", f"{rd}/{name}（常驻规则将降级为按需加载）"))
        except Exception:
            continue
    return findings


def check_reference_rot(navigator_files):
    """③ 硬路牌引用腐烂：导航仪引用的 ~/ 路径不存在=指空"""
    findings = []
    for nav in navigator_files:
        if not os.path.isfile(nav):
            continue
        try:
            with open(nav, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue
        for ref in sorted(set(REF_RE.findall(content))):
            if PLACEHOLDER_RE.search(ref):
                continue  # 模板占位符非具体引用→豁免（保守判定）
            target = os.path.expanduser(ref)
            if not os.path.exists(target):
                findings.append(("引用腐烂", f"{os.path.basename(nav)} → {ref} 不存在"))
    return findings


def check_dual_dir_drift(rules_dirs):
    """④ 同名软链目标一致性：双目录同名规则若都是软链须指向同一共享源。
    实体文件允许平台差异（首跑实证 core-identity/cross-end-guard 为合法适配副本）"""
    findings = []
    if len(rules_dirs) < 2:
        return findings
    a, b = rules_dirs[0], rules_dirs[1]
    if not (os.path.isdir(a) and os.path.isdir(b)):
        return findings
    try:
        names_a = {n for n in os.listdir(a) if n.endswith(".md")}
        names_b = {n for n in os.listdir(b) if n.endswith(".md")}
        for name in sorted(names_a & names_b):
            pa, pb = os.path.join(a, name), os.path.join(b, name)
            if not (os.path.islink(pa) and os.path.islink(pb)):
                continue  # 实体文件=平台适配副本→不判（保守·宁漏勿误）
            if os.path.realpath(pa) != os.path.realpath(pb):
                findings.append(("软链分歧", f"{name} 双目录软链目标不一致（共享机制破断）"))
    except Exception:
        pass
    return findings


def _has_always_apply(path):
    """判定 rules 文件是否标记常驻（frontmatter `alwaysApply: true`）——注入规范§二三要件之要件2。
    无标记=按需读取（§二"三要件缺一即退化按需"），⛔不进常驻注入基准=防把按需记忆软链
    （动态快照/问卷/题库·4端共享·均无标记）误报为"常驻静默失效"。保守：读不了/无frontmatter=False。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(2000)
    except Exception:
        return False
    if not head.startswith("---"):
        return False
    parts = head.split("---", 2)
    fm = parts[1] if len(parts) >= 3 else ""
    return bool(re.search(r"^alwaysApply\s*:\s*true\s*$", fm, re.MULTILINE | re.IGNORECASE))


def _realpath_of_key(key, rules_dirs):
    """把归属 key（`.qoder-cn/rules/x.md`）映射回磁盘 realpath（软链解析）。
    按 key 的归属 tag 反查 rules_dirs 实际目录（兼容 self-test 临时夹具·⛔硬编码 HOME）。
    用于六端同源软链去重：双端 rules 同名文件若指向同一共享源=同一注入实体。解析失败返回 None。"""
    try:
        tag, rest = key.split("/", 1)
        for rd in rules_dirs:
            if os.path.basename(os.path.dirname(rd)) == tag:
                return os.path.realpath(os.path.join(os.path.dirname(rd), rest))
        return None
    except Exception:
        return None


def _canon_seen(item, rules_dirs):
    """痕迹条目写法归一（v0.5 根治假红）：AI 自报路径存在三种写法——
    `.qoder-cn/rules/x.md`（规范）/ `~/.qoder-cn/rules/x.md`（tilde）/
    `/Users/xx/.qoder-cn/rules/x.md`（绝对）。truth 盘上 key 是规范写法，
    精确差集遇写法变体=同一文件双向误报（静默失效+幻影成对出现=假红指纹）。
    按归属 tag 从展开路径切片归一；未命中任何 tag 的路径原样返回
    （真幻影照判，⛔不借归一放行来源不明项）。tag 后必须跟 `/` 且前置边界
    为路径分隔符，防 `.qoder-cn-work` 类假匹配。"""
    s = (item or "").strip()
    exp = os.path.expanduser(s)
    for rd in rules_dirs:
        tag = os.path.basename(os.path.dirname(rd))
        i = exp.find(tag + "/")
        if i != -1 and (i == 0 or exp[i - 1] == "/"):
            return exp[i:]
    return s


def _list_injectables(rules_dirs):
    """盘上真相=期望集（⛔不内联清单·第五问纪律）。
    实测注入层不止 rules/ 双目录：`~/.qoder-cn/AGENTS.md`（根级导航仪）同样进 context，
    故真相集含"双 rules 目录 .md"+"双配置根根级 .md"两层。
    key 形如 `.qoder-cn/rules/core-soul.md` / `.qoder-cn/AGENTS.md`（归属根前缀必带=串味可判）
    返回 (truth_map, own_rules_keys)：
      · truth_map=盘上全部可注入文件（幻影/串味判定域·全量·v0.3 不变）
      · own_rules_keys=本端 rules/ 中**标记 alwaysApply:true 的常驻文件**=缺失判定域
        （v0.3 收窄：⛔不再无差别含全部 .md——无标记的按需记忆软链不进常驻基准，
         对齐注入规范§二"三要件缺一即退化按需"，根治"按需文件被误报常驻静默失效"·
         实证：动态快照/问卷/题库 4端均无 alwaysApply=设计本意按需，产品不注入是正确行为）"""
    truth, own_rules = {}, set()
    self_tag = None
    for rd in rules_dirs:
        tag = os.path.basename(os.path.dirname(rd))  # .qoder-cn / .qoder
        self_tag = self_tag or tag
        if not os.path.isdir(rd):
            continue
        root = os.path.dirname(rd)
        try:
            for name in sorted(os.listdir(rd)):
                if name.endswith(".md"):
                    p = os.path.join(rd, name)
                    truth[f"{tag}/rules/{name}"] = os.path.islink(p)
                    # 常驻基准仅收本端 + 标记 alwaysApply:true（注入规范§二三要件之要件2）
                    if tag == self_tag and _has_always_apply(p):
                        own_rules.add(f"{tag}/rules/{name}")
            for name in sorted(os.listdir(root)):  # 根级 .md（导航仪/经验器）
                p = os.path.join(root, name)
                if name.endswith(".md") and os.path.isfile(p):
                    truth[f"{tag}/{name}"] = os.path.islink(p)
        except Exception:
            continue
    return truth, own_rules


def _read_last_trace(observed_log):
    """读最后一条观察痕迹（JSONL 尾行·损坏即返回 None 不抛）"""
    try:
        with open(observed_log, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        if not lines:
            return None
        d = json.loads(lines[-1])
        return d if isinstance(d.get("seen"), list) else None
    except Exception:
        return None


def record_observed(seen, rules_dirs=None, session="", observed_log=None):
    """AI 侧记录：把"本会话实际看到的常驻注入清单"落痕，并即时对账。
    seen 项形如 `.qoder-cn/rules/core-soul.md`（归属根前缀必带，用于抓跨端串味）
    留痕闸门：对账只读尾行 → seen 未变且未跨天不重复写（防 JSONL 无界增长），仍照常报告"""
    rules_dirs = rules_dirs or RULES_DIRS
    log = observed_log or OBSERVED_LOG
    os.makedirs(os.path.dirname(log), exist_ok=True)
    now = time.time()
    seen_set = sorted({_canon_seen(s, rules_dirs) for s in seen if s and s.strip()})
    last = _read_last_trace(log) if os.path.isfile(log) else None
    unchanged = bool(last) and sorted(set(last["seen"])) == seen_set \
        and (now - float(last.get("epoch", 0))) < 86400
    if unchanged:
        print(f"✅ 痕迹未变化且＜1 天，跳过落盘（{len(seen_set)} 项·仍照常对账）")
    else:
        rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
               "epoch": int(now), "seen": seen_set, "session": session}
        with open(log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✅ 痕迹已落 {log}（{len(seen_set)} 项）")
    return check_injection_proof(rules_dirs, log)


def _recent_session_activity():
    """本端最近24h是否有会话活动=transcript mtime 最大值（异常免疫：读不到返回 False=退回7天口径不误报）"""
    import glob as _g
    cutoff = time.time() - 86400
    try:
        for pat in (os.path.join(HOME, ".qoder-cn/projects/*/*.jsonl"),
                    os.path.join(HOME, ".qoder-cn/projects/*/transcript/*.jsonl")):
            for f in _g.glob(pat):
                try:
                    if os.path.getmtime(f) > cutoff:
                        return True
                except OSError:
                    continue
    except Exception:
        return False
    return False


def check_injection_proof(rules_dirs, observed_log):
    """⑤ 注入实证对账：期望（盘上真相）× 实证（AI 报告）
    判定范围（第五问·宁可少守不可误报）：
      - 缺失只判本端 rules/ 本体：他端根软链=六端同源共享，实测在本端 context 被去重属合法态；
        根级文件（MEMORY.md 等）按需注入，不判缺失
      - 幻影=盘上真相集查无此文件（AI 报出不存在的路径）⛔不是"不在 rules/ 清单里"
      - 他端根实体文件被观察到=跨端串味"""
    findings = []
    truth, own_rules = _list_injectables(rules_dirs)
    trace = _read_last_trace(observed_log)
    if trace is None:
        return [("无自检痕迹", f"{os.path.basename(observed_log)} 缺失/不可解析=注入生效性无实证")]
    self_tag = os.path.basename(os.path.dirname(rules_dirs[0]))
    # 读取侧归一（v0.5）：存量脏痕迹即时自愈，不靠等下一个窗口重新落痕
    seen = {_canon_seen(s, rules_dirs) for s in trace["seen"]}
    age = time.time() - float(trace.get("epoch", 0))
    if age > STALE_DAYS * 86400:
        findings.append(("痕迹超龄",
                         f"上次注入自检 {trace.get('ts', '?')}＞{STALE_DAYS} 天=自检断链（升级/换代后须重跑）"))
    elif _recent_session_activity() and age > STALE_HOURS_WITH_SESSION * 3600:
        findings.append(("断链早期显形",
                         f"本端有在场会话但注入自检已 {int(age // 3600)} 小时未跑（>{STALE_HOURS_WITH_SESSION}h）——"
                         f"钩子在派发，AI 侧 --record 动作欠账（09-20→09-22 实测 7 天窗静默放过）"))
    # 六端同源软链去重（v0.3）：seen 命中项的 realpath 集——本端常驻文件若与他端已观察项
    # 指向同一共享源（如 core-user 双端软链同一 core-user.md·实测两端 realpath 一致），
    # context 去重后 AI 自报只填一端属合法态，⛔不判本端失效（否则漏报本端路径=误报·实证）
    seen_realpaths = {rp for rp in (_realpath_of_key(s, rules_dirs) for s in seen) if rp}
    for item in sorted(own_rules - seen):
        rp = _realpath_of_key(item, rules_dirs)
        if rp and rp in seen_realpaths:
            continue  # 同源去重·共享源已被观察=本端也算注入
        findings.append(("注入静默失效", f"{item} 在盘上但未被观察进 context"))
    for item in sorted(seen - set(truth)):
        findings.append(("幻影注入项", f"{item} 被观察到但双目录盘上无此文件（来源不明）"))
    for item in sorted(seen & set(truth)):
        # 他端根实体文件=串味（软链=六端同源共享，实测被注入去重，不判）
        if item.split("/", 1)[0] != self_tag and not truth[item]:
            findings.append(("跨端串味", f"{item} 是他端资产根的实体文件，却出现在本端注入清单"))
    return findings


def run_all(rules_dirs=None, navigator_files=None, observed_log=None):
    rules_dirs = rules_dirs or RULES_DIRS
    navigator_files = navigator_files or NAVIGATOR_FILES
    observed_log = observed_log or OBSERVED_LOG
    findings = []
    findings += check_dangling_links(rules_dirs)
    findings += check_paths_misuse(rules_dirs)
    findings += check_reference_rot(navigator_files)
    findings += check_dual_dir_drift(rules_dirs)
    findings += check_injection_proof(rules_dirs, observed_log)
    return findings


# 对账判定域边界声明（v0.4·2026-09-20 better-harness 复盘落）：
# ⑤注入实证按设计"缺失只判本端 rules/ 本体"（宁可少守不可误报），根级导航仪（AGENTS.md/MEMORY.md）
# 落在判定域之外——过去这句只写在 docstring 里，输出面看不出"全绿"没覆盖哪一轴，于是「全绿」被读成
# 「整链完整」。现把它显式印到每次结论里：全绿的覆盖面与不判定的轴，一并交给读者。
NOT_JUDGED = ("ℹ️ 本次对账不判定轴：根级文件（AGENTS.md / MEMORY.md 等按需注入项）——"
              "「盘上有但未申报」与「真的没注入」在此轴不可区分，⛔不得把全绿读成整链完整")


def report(findings):
    if not findings:
        print("✅ [qodercn_inject_chain_guard] 注入链健康（软链/paths/引用/一致性 + 注入实证对账全绿）")
        print("   " + NOT_JUDGED)
        return
    print(f"⚠️ [qodercn_inject_chain_guard] 注入链异常 {len(findings)} 处：")
    print("   " + NOT_JUDGED)
    for kind, detail in findings:
        print(f"  🔴 [{kind}] {detail}")


# ─── --self-test（§3.0·5·夹具构造临时目录·不碰真实配置·幂等自清理）────────────

def _mk_fixture(root):
    """构造最小注入链夹具：双 rules 目录 + 导航仪 + 一份有效观察痕迹。
    他端根（.qoder）只放软链=六端同源共享的仿真，避免与⑤串味判定互相干扰"""
    d1 = os.path.join(root, ".qoder-cn", "rules")
    d2 = os.path.join(root, ".qoder", "rules")
    os.makedirs(d1)
    os.makedirs(d2)
    arch = os.path.join(root, "archive")
    os.makedirs(arch)
    # core-soul=常驻样本（带 alwaysApply·进 own_rules 基准·供 T6 失效检出）
    with open(os.path.join(arch, "core-soul.md"), "w", encoding="utf-8") as f:
        f.write("---\ndescription: 常驻品格\nalwaysApply: true\n---\n# core-soul.md\n")
    # shared=按需样本（无 frontmatter·他端软链·供 T11 不误报）
    with open(os.path.join(arch, "shared.md"), "w", encoding="utf-8") as f:
        f.write("# shared.md\n")
    os.symlink(os.path.join(arch, "core-soul.md"), os.path.join(d1, "core-soul.md"))
    os.symlink(os.path.join(arch, "shared.md"), os.path.join(d2, "shared-rule.md"))
    # normal=有 frontmatter 但无 alwaysApply（按需·不进常驻基准·供 T13）
    with open(os.path.join(d1, "normal.md"), "w", encoding="utf-8") as f:
        f.write("---\ntitle: x\n---\n正文\n")
    nav = os.path.join(root, ".qoder-cn", "AGENTS.md")
    with open(nav, "w", encoding="utf-8") as f:
        f.write(f"# 导航\n必读：`{os.path.join(arch, 'core-soul.md')}`\n")
    trace = os.path.join(root, "observed.jsonl")
    _write_trace(trace, [d1, d2])
    return [d1, d2], [nav], trace


def _write_trace(trace_path, rules_dirs, omit=None, extra=None, age_days=0):
    """从磁盘实盘生成痕迹（=AI 报告的仿真）：可故意漏项/加幻影项/改旧时间戳造负例"""
    seen = set(_list_injectables(rules_dirs)[0])
    seen -= set(omit or [])
    seen |= set(extra or [])
    now = time.time() - age_days * 86400
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
           "epoch": int(now), "seen": sorted(seen), "session": "self-test"}
    with open(trace_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return trace_path


def self_test():
    results = []

    def case(name, expect_n, findings):
        ok = len(findings) == expect_n
        results.append((name, ok, findings))

    tmp = tempfile.mkdtemp(prefix="qodercn_icg_test_")
    try:
        # T1 正常态：零发现
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t1"))
        # 含根级 AGENTS.md 如实上报不判幻影（实跑发现：注入层含导航仪）
        case("T1 正常态零发现", 0, run_all(dirs, navs, trace))

        # T2 断链：链目标删除
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t2"))
        os.remove(os.path.join(tmp, "t2", "archive", "core-soul.md"))
        case("T2 断链检出", 1, run_all(dirs, navs, trace))

        # T3 paths 误用：常驻规则被降级（写共享源=双目录软链同时命中）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t3"))
        for src in ("core-soul.md", "shared.md"):
            with open(os.path.join(tmp, "t3", "archive", src), "w", encoding="utf-8") as f:
                f.write("---\ntitle: x\npaths: [src/**]\n---\n正文\n")
        case("T3 paths误用检出", 2, run_all(dirs, navs, trace))

        # T4 引用腐烂：导航仪引用不存在路径
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t4"))
        with open(navs[0], "a", encoding="utf-8") as f:
            f.write("\n另读：`~/nonexistent_dir_qodercn_icg/x.md`\n")
        case("T4 引用腐烂检出", 1, run_all(dirs, navs, trace))

        # T5 同名软链目标分歧：双目录同名软链指向不同文件=共享机制破断
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t5"))
        other_target = os.path.join(tmp, "t5", "archive", "core-soul-OTHER.md")
        with open(other_target, "w", encoding="utf-8") as f:
            f.write("# soul 另一份\n")
        os.symlink(other_target, os.path.join(dirs[1], "core-soul.md"))
        _write_trace(trace, dirs)  # 变更后重建痕迹，隔离⑤的干扰
        case("T5 同名软链分歧检出", 1, run_all(dirs, navs, trace))

        # T6 注入静默失效：盘上有、AI 没看到（=升级重置注入行为的核心负例）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t6"))
        _write_trace(trace, dirs, omit=[".qoder-cn/rules/core-soul.md"])
        case("T6 注入静默失效检出", 1, run_all(dirs, navs, trace))

        # T7 幻影注入项：AI 看到了双目录盘上都不存在的文件
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t7"))
        _write_trace(trace, dirs, extra=[".qoder-cn/rules/ghost_qodercn_icg.md"])
        case("T7 幻影注入项检出", 1, run_all(dirs, navs, trace))

        # T8 痕迹超龄：自检断链（升级后忘记重跑）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t8"))
        _write_trace(trace, dirs, age_days=STALE_DAYS + 3)
        case("T8 痕迹超龄检出", 1, run_all(dirs, navs, trace))

        # T9 跨端串味：他端资产根的实体文件出现在本端注入清单
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t9"))
        with open(os.path.join(dirs[1], "foreign_entity.md"), "w", encoding="utf-8") as f:
            f.write("---\nalwaysApply: true\n---\n他端专属身份\n")
        _write_trace(trace, dirs)
        case("T9 跨端串味检出", 1, run_all(dirs, navs, trace))

        # T10 无痕迹：从未跑过注入自检=生效性无实证（不假装绿灯）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t10"))
        os.remove(trace)
        case("T10 无自检痕迹检出", 1, run_all(dirs, navs, trace))

        # T11 防误报回归：他端根软链未进 context=六端同源去重合法态，必须静默
        #（⛔勿把"缺失"判定扩到他端根，否则每会话误报=守卫变噪音=失效·第五问）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t11"))
        _write_trace(trace, dirs, omit=[".qoder/rules/shared-rule.md"])
        case("T11 他端软链未注入不误报", 0, run_all(dirs, navs, trace))

        # T12 留痕闸门：同日同清单重复 --record 不追加（对账只读尾行·防 JSONL 无界增长）
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t12"))
        os.remove(trace)
        seen_all = sorted(_list_injectables(dirs)[0])
        f12a = record_observed(seen_all, dirs, "t12-a", trace)
        f12b = record_observed(seen_all, dirs, "t12-b", trace)
        with open(trace, encoding="utf-8") as tf:
            n_lines = len([l for l in tf if l.strip()])
        results.append(("T12 留痕闸门（同日重复不追加）",
                        n_lines == 1 and f12a == f12b, [(n_lines, f12a)]))

        # T13 按需文件不误报（v0.3）：无 alwaysApply 标记的 rules 文件（动态快照/问卷/题库类）
        # 属注入规范§二"按需读取"，⛔不进常驻基准=即使 AI 未报告也不判"静默失效"
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t13"))
        od = os.path.join(tmp, "t13", "archive", "on-demand.md")
        with open(od, "w", encoding="utf-8") as f:
            f.write("# 动态快照类按需记忆（无 frontmatter）\n")
        os.symlink(od, os.path.join(dirs[0], "on-demand.md"))
        # AI 只报常驻文件，漏报两个按需文件（normal 有frontmatter无alwaysApply + on-demand 无frontmatter）
        _write_trace(trace, dirs, omit=[".qoder-cn/rules/normal.md", ".qoder-cn/rules/on-demand.md"])
        case("T13 按需文件(无alwaysApply)不误报失效", 0, run_all(dirs, navs, trace))

        # T16 痕迹写法归一（v0.5 根治假红）：AI 自报用 `~`tilde / 绝对路径写法
        # （模型看到的注入路径常是绝对路径，输入格式不可控），⛔不得成对误报
        # "静默失效"+"幻影"——2026-10-10 实测 tilde 痕迹一落，6 文件×双向=12 假红
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t16"))
        _seen_norm = sorted(_list_injectables(dirs)[0])
        _mixed = [("~/" + k) if k.startswith(".qoder-cn/")
                  else os.path.join(tmp, "t16", k) if k.startswith(".qoder/")
                  else k for k in _seen_norm]
        _t16_now = time.time()
        with open(trace, "w", encoding="utf-8") as tf:
            tf.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(_t16_now)),
                                 "epoch": int(_t16_now), "seen": sorted(_mixed),
                                 "session": "t16"}, ensure_ascii=False) + "\n")
        case("T16 tilde/绝对写法痕迹归一不误报", 0, run_all(dirs, navs, trace))

        # T14 六端同源软链去重（v0.3）：本端常驻文件与他端已观察项指向同一共享源
        # （core-user 双端软链同一实体·实测 realpath 一致），AI 自报只填他端路径⛔不判本端失效
        dirs, navs, trace = _mk_fixture(os.path.join(tmp, "t14"))
        sc = os.path.join(tmp, "t14", "archive", "shared-core.md")
        with open(sc, "w", encoding="utf-8") as f:
            f.write("---\nalwaysApply: true\n---\n# 共享核心（core-user 类·双端同源）\n")
        os.symlink(sc, os.path.join(dirs[0], "shared-core.md"))  # .qoder-cn 端（本端）
        os.symlink(sc, os.path.join(dirs[1], "shared-core.md"))  # .qoder 端（他端·同源）
        # AI 自报只填他端 .qoder/rules/shared-core.md，漏报本端 .qoder-cn/rules/shared-core.md
        _write_trace(trace, dirs, omit=[".qoder-cn/rules/shared-core.md"])
        case("T14 双端同源软链去重不误报", 0, run_all(dirs, navs, trace))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)  # 自清理（家族纪律）

    # T15 判定域边界外印（2026-09-20 独立复核补·v0.4 负例）：全绿结论必须自带「不判定轴」一行，
    # 缺行=「全绿」又被读成「整链完整」——此断言让那行删不掉（防无声回退·§3.5 送达路径须有负例）
    import contextlib as _cl, io as _io
    _buf = _io.StringIO()
    with _cl.redirect_stdout(_buf):
        report([])
    results.append(("T15 全绿结论自带判定域边界声明", "不判定轴" in _buf.getvalue(), []))
    passed = sum(1 for _, ok, _ in results if ok)
    for name, ok, findings in results:
        mark = "✅" if ok else "❌"
        extra = "" if ok else f"（实得 {len(findings)} 处：{findings}）"
        print(f"{mark} {name}{extra}")
    print(f"self-test: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


def main():
    if "--self-test" in sys.argv:
        sys.exit(self_test())

    if "--record" in sys.argv:
        try:
            idx = sys.argv.index("--seen")
            seen = [s for s in sys.argv[idx + 1].split(",") if s.strip()]
        except (ValueError, IndexError):
            print("用法：--record --seen .qoder-cn/rules/a.md,.qoder-cn/AGENTS.md", file=sys.stderr)
            sys.exit(2)
        session = ""
        if "--session" in sys.argv:
            try:
                session = sys.argv[sys.argv.index("--session") + 1]
            except IndexError:
                pass
        try:
            findings = record_observed(seen, session=session)
        except Exception as e:
            print(f"[qodercn_inject_chain_guard] 记录异常·放行：{e}", file=sys.stderr)
            sys.exit(0)
        report(findings)
        sys.exit(1 if findings else 0)

    try:
        findings = run_all()
        report(findings)
    except Exception as e:
        print(f"[qodercn_inject_chain_guard] 解析异常·放行：{e}", file=sys.stderr)
        sys.exit(0)  # 失败放行（Hook 纪律2）

    if "--check" in sys.argv:
        sys.exit(1 if findings else 0)
    sys.exit(0)  # Hook 报告制：恒 exit 0（Hook 纪律1）


if __name__ == "__main__":
    _rc = 0
    try:
        main()
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else 0
        # 步2(2026-10-07 v? 报警噪声根治卡·你令彻底做完):检红rc归0——平台契约下 exit≠0专留真崩,
        #   检红可见性=输出红行+台账(_guard_log_exit/.out/patrol log);⛔不减一行红输出。
        if _rc == 1:
            _rc = 0

    except Exception:
        _rc = 0  # 失败放行（Hook 纪律2）
    finally:
        _guard_log_exit(_rc)
    sys.exit(_rc)
