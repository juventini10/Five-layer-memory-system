#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# 件端覆盖矩阵生成器（试点v0 · 仅ZCode列实扫）
import json, re, os
from datetime import datetime

NOW = datetime.now()
SCAN_TIME = NOW.strftime("%Y-%m-%d %H:%M")
DATA = json.load(open("/tmp/coverage_audit_data.json"))
rows = DATA["rows"]
mounted = DATA["zcode_mounted"]

# ---------- 终判映射（每件: (态, 证据)） ----------
V = {}

def setv(name, state, ev):
    V[name] = (state, ev)

# 1. 实挂 28 -> ✅
for name, evs in mounted.items():
    uniq = ",".join(sorted(set(evs)))
    setv(name, "✅", "~/.zcode/cli/config.json hooks.events [%s] 实挂(行级扫描)" % uniq)

# 2. ⛔ 裁定 3
setv("l3_conclusion_guard.py", "⛔", "09-05你令永久关闭·ZCode端级排除分母(SRC_EXCLUDED)·04指南L174裁定记录")
setv("reply_format_guard.py", "⛔", "本体08-26完全删除·退回SOUL软约束·04指南L174裁定")
setv("guard_registry_check.py", "⛔", "真相源形态不符(settings.json vs config.json)·同职能zcode_config_guard覆盖·04指南L174判定")

# 3. import 闭包 🟡 (AST级·被ZCode实挂件import)
IMPORT_EV = {
    "hook_protocol.py": "被ZCode实挂8件import(注入输出协议唯一真源·注册表L671)",
    "router.py": "被route_inject/route_miss_feeder/route_audit import(路由判据真源)",
    "transcript_reader.py": "被ZCode实挂7件import(transcript解析单一真源)",
    "rule_triggers_loader.py": "被rule_fragment_inject/rule_three_layer_guard import",
    "session_title_utils.py": "被zcode_title_namer.py import(公共原语)",
    "format_contract.py": "被route_inject_prompt.py import(格式契约抽取)",
    "guard_doc_consistency.py": "被ZCode Stop实挂件manifest_registrar.py import(扫描口径复用)",
}
for k, v in IMPORT_EV.items():
    setv(k, "🟡", v)

# 4. git 仓库级 🟡 (全端提交生效·端无关承载面)
GIT_EV = {
    "shell_cjk_guard.py": "注册表L664: 挂载点=~/.git/hooks/pre-commit·全端提交生效",
    "md_table_shape_guard.py": "注册表L665: .git/hooks/pre-commit·J1🔴阻断全端生效",
    "verify_skill_version_hook.sh": "注册表L633: git hook pre-commit部署·全端提交生效",
    "git_commit_safe.sh": "注册表L641: ~/bin/git wrapper·所有端git commit自动经门禁",
}
for k, v in GIT_EV.items():
    setv(k, "🟡", v)

# 5. 系统级调度 🟡 (launchd/cron/fswatch·作者机系统级·服务含ZCode的全端)
SCHED_EV = {
    "amber-checkup.sh": "注册表L581: launchd每日(记忆琥珀健康·服务全端)",
    "doenglingz_slice_watch.py": "launchd WatchPaths+MARKED_HOMES[0]=~/.zcode/AGENTS.md(W2机械腿ZCode纳端·脚本实证)",
    "eval_health_guard.sh": "注册表L673: launchd周巡(检索质量)",
    "gray_release_stats.py": "注册表L654: launchd每日(灰度统计)",
    "twin_distill_watch.py": "注册表L655: launchd每6h(蒸馏源指纹)",
    "growth_chain.sh": "注册表L688: launchd单驱动七棒(growth-chain)",
    "growth_cross_link.py": "growth_chain链内棒·launchd每日",
    "growth_decision_gate.py": "growth_chain链内棒·launchd每日",
    "write_race_watch.py": "growth_chain链末棒·launchd每日",
    "script_family_check.py": "注册表L672/L592: launchd每周一09:00(六层体检)",
    "route_fswatch_poll.sh": "manifest调度形态·fswatch快照diff(路由观测)",
    "route_source_scan.py": "manifest引擎/调度·多端会话源观测(ZCode rollout目录在扫域)",
    "systemlog_watch.sh": "注册表L617: launchd常驻com.buluotuo.systemlog.watch",
    "watch_control_loop.sh": "manifest引擎/调度形态(系统级调度承载推定⚠️未逐脚本验证运行态)",
    "mirror_fswatch_wrapper.sh": "manifest变换/调度形态(系统级fswatch)",
    "doenglingz_tsl_report.py": "manifest引擎/调度(分身TSL报告调度)",
    "philosophy_radar.py": "注册表L661: launchd每日06:30(哲学变更雷达)",
    "growth_box_check.sh": "注册表L603: 活版本=技能配置/growth-box/scripts(v1.7)+growth_chain家族",
    "normalize_tool.py": "被ZCode实挂件doenglingz_inject_prompt调用+launchd systemlog链工具表真源",
    "triwich_seal.py": "注册表L628: 每轮三明智收尾AI执行(SKILL.md正文条款v4.3.0转正)·ZCode triwich Skill在册承载",
}
for k, v in SCHED_EV.items():
    setv(k, "🟡", v)

# 6. 端专属/专属承载面 ➖ (既有裁定=注册表行端声明)
DEDIC_EV = {
    "autoclaw_gateway_guard.py": "注册表L650: AutoClaw网关专属(元守卫)",
    "buluotuo-stop-hook": "注册表L653: Hermes专属插件(承载route_unknown_unknown)",
    "catpaw_skill_health_guard.py": "注册表L670: CatPaw专属",
    "doenglingz-guard": "注册表L656: AutoClaw agent_end插件",
    "doenglingz_guard_dsh.py": "注册表L658: DSH端适配器(B方案)·ZCode有同族doenglingz_guard_zcode✅",
    "dsh_session_anomaly_guard.py": "注册表L647: DSH专属",
    "dsh_session_repair.py": "DSH会话修复(变换)·DSH数据面",
    "dsh_session_row_restore.py": "DSH会话行恢复·DSH数据面",
    "dsh_title_namer.py": "manifest变换/Hook·DSH端命名器",
    "dsh_frame_guard_loop.sh": "manifest引擎/调度·DSH frame guard",
    "dsh_plugin_deploy.py": "manifest引擎·DSH插件部署",
    "mirror_dsh_docs.py": "manifest变换·DSH文档镜像",
    "hermes_plugin_health_guard.py": "注册表L652: Hermes插件层专属(元守卫)",
    "hermes_read_evidence_guard.py": "注册表L651: Hermes会话层专属",
    "hermes_tsl_closeout_adapter.py": "注册表L576: Hermes端TSL适配层(端差异补丁)",
    "lobsterai_session_anomaly_guard.py": "注册表L648: LobsterAI专属",
    "qodercn_config_guard.py": "注册表L619: Qoder CN专属·⛔不进12-Hook共享分母(行文明示)",
    "qodercn_inject_chain_guard.py": "注册表L659: Qoder CN注入链专属",
    "session_memory_quality_guard.py": "注册表L649: Trae Work专属(04指南L149各端N/A裁定同构)",
    "teleagent_skill_health_guard.py": "注册表L669: TeleAgent专属",
    "trae_isolation_guard.py": "注册表L610: Trae系双端共享面守卫·被检对象=~/.trae-cn",
    "traecode_isolation_guard.py": "注册表L611: 已退役(09-30前提证伪·trae_isolation_guard接替)",
    "traecode_title_namer.py": "注册表L612: TraeCode端命名器",
    "wbai_title_namer.py": "manifest变换/会话命名·WorkBuddy AI国际版",
    "workbuddy_config_guard.py": "注册表L683: WB端settings.json挂载活性对账",
    "workbuddy_inject_chain_guard.py": "注册表L682: WB端UPS注入链健康",
    "workbuddy_skill_health_guard.py": "注册表L681: WB端Skill双面健康",
    "session_title_namer.py": "manifest变换/Hook·WB端命名器(ZCode用zcode_title_namer✅同族分立)",
    "route_autoclaw_patrol.sh": "AutoClaw patrol承载(manifest引擎/调度·端专属patrol)",
    "route_doubaowork_patrol.sh": "豆包办公patrol承载",
    "route_lobsterai_patrol.sh": "LobsterAI patrol承载",
    "route_traework_patrol.sh": "Trae Work patrol承载",
    "route_audit_openclaw.sh": "manifest引擎·OpenClaw(AutoClaw)变体",
    "registry_guards.sh": "注册表L638: WorkBuddy专属附加守卫(Stop链入口·行文明示)",
    "antibody_guard.sh": "注册表L604: 由registry_guards.sh自动发现挂Stop(WB聚合面)",
    "kb_index_guard.sh": "注册表L595: Stop钩子内跑+registry_guards聚合(WB面)+clock-loop按需",
    "panel_snapshot.py": "注册表L643: Stop Hook(WorkBuddy专属)+Hermes插件(行文明示)",
    "stamp_precheck_guard.py": "注册表L620/L666: 挂载=Qoder CN PreToolUse·行文明示⛔不宣称跨端覆盖",
    "gate_runner.py": "数字分身会话域流程件(零问题门禁运行器·规格书机制登记·非端钩子面·manifest form=Hook系流程语义缺口)",
}
for k, v in DEDIC_EV.items():
    setv(k, "➖", v)

# 7. c 挂账 15 (试点口径判❓·尽职复核后挂账)
C_ITEMS = [
    ("changelog_guard.sh", "Stop报告制·判据端中立(读变更日志.md)·ZCode零承载·挂载机制=WB registry_guards自动发现需另建ZCode侧挂载"),
    ("changelog_guard.py", "变更日志写入前排除校验·同族上一件·ZCode零承载零裁定"),
    ("systemlog_stophook_check.py", "Stop收口校验(改动无日志→提醒)·WB+QCN已挂·判据端中立·ZCode零承载"),
    ("change_closedloop_guard.py", "Stop·改动闭环律机械门禁·WB已挂·判据端中立·ZCode零承载"),
    ("design_family_guard.py", "Stop·设计哲学家族一致性·WB已挂·判据端中立·ZCode零承载"),
    ("post_change_guard.py", "Stop·AI改文件后同步遗漏检测·WB+QCN已挂·ZCode零承载"),
    ("reply_tail_guard.py", "Stop advisory·回复留尾巴检测(注册表L695)·WB承载·ZCode零承载"),
    ("skill_spec_read_guard.py", "PreToolUse硬拦·改SKILL.md前必读规范(注册表L696)·ZCode有PreToolUse同位件skill_write_gate_guard可并挂"),
    ("grep_sandbox_guard.py", "PreToolUse物理阻断·沙箱grep转义防护(LRN-20260920-009)·ZCode沙箱grep盲区为本轮试点实证痛点·优先级最高"),
    ("twin_changelog_guard.py", "Stop·分身域变更日志完整性(注册表L680)·ZCode为分身入驻端·零承载"),
    ("registry_precheck_guard.py", "PreToolUse·治理域新建脚本须带REG头(注册表L667)·QCN挂载·ZCode有PreToolUse未挂"),
    ("philosophy_radar_inject.py", "UPS到达腿·读哲学雷达会话首轮注入(注册表L662)·QCN挂载·ZCode会话无哲学雷达注入"),
    ("triwich_closeout_guard.py", "Stop·三明智收尾三登记(注册表L605)·行文'现仅WorkBuddy端'系事实陈述非裁定·ZCode零承载"),
    ("change_reflux_guard.py", "PreToolUse advisory·必回流清单指路(注册表L692)·行文明示QCN尚未挂载·ZCode亦未挂·跨端共享件"),
    ("symlink_guard.sh", "注册表L629·脚本ENDS硬编码6端(.box-agent/.qclaw/.qoder/.qoderwork/.trae/.workbuddy)不含~/.zcode/skills·ZCode skill_symlink=true生态存在巡检盲区(实盘证据)"),
]
for name, why in C_ITEMS:
    setv(name, "c挂账", why)

# 8. b 裁定 1
setv("guard_heartbeat_check.py", "➖(b裁定)", "同职能已由zcode_config_guard活性腿覆盖(其注册表行文:钩子活性=route_audit src:zcode实证+STALE_DAYS过期告警)·心跳真源HB_DIR在WB hooks域·引04指南L174 guard_registry_check同型裁定先例")

# 9. 兜底: 其余 -> ➖ 按需/变换/引擎形态
FALLBACK = "按需/变换/引擎形态·无端挂载语义·01规范部署四形态(本质三分x部署四形态正交v1.3.69)+scripts_manifest form字段"

unc = []
for r in rows:
    name = r["name"]
    if name == "------" or set(name) <= {"-", ":", " "}:
        continue  # 表头分隔行非件（扫描器残留·试点修正）
    if name not in V:
        V[name] = ("➖", FALLBACK + ("·manifest在册" if any("manifest" in s for s in r["sources"]) else "·注册表时序表述"))
        unc.append(name)

# 行全量外实挂件（试点发现·不入矩阵行·单列披露）
ROW_NAMES = {r["name"] for r in rows}
OUTSIDE_MOUNTED = {
    "doenglingz_inject_prompt.py": "manifest family=守卫(非路由/引擎/变换scope)·注册表L671仅行文提及·Hook清单14件外",
    "position3_notify.py": "manifest零记录(不在册!)·真身=数字分身/scripts/·ZCode UPS实挂",
    "session_tail_inject.py": "manifest family=守卫/会话注入(scope外)",
    "tsl_echo_hook.py": "manifest family=待分类(scope外)",
    "tsl_tree_hook.py": "manifest family=待分类(scope外)",
}
V = {k: v for k, v in V.items() if k in ROW_NAMES}

# ---------- 统计 ----------
from collections import Counter
dist = Counter(v[0] for v in V.values())
print("终判分布:", dict(dist))
print("总数:", sum(dist.values()))
assert sum(dist.values()) == 191, "终判覆盖不全: %d vs 191" % sum(dist.values())

# ---------- 19端 ----------
ENDS = [
    ("qoder-desktop", "Qoder Desktop", "04指南L133对比表列"),
    ("qodercn", "Qoder CN", "04指南L133+06JSON"),
    ("workbuddy", "WorkBuddy", "04指南L133+06JSON"),
    ("workbuddyai", "WorkBuddy AI(国际版·18)", "04指南L133+06JSON"),
    ("autoclaw", "AutoClaw(14)", "04指南L133+06JSON"),
    ("zwork", "Zwork(19)", "04指南L133+06JSON"),
    ("dsh", "DeepSeek Harness(10)", "04指南L133+06JSON"),
    ("lobsterai", "LobsterAI(11)", "04指南L133+06JSON"),
    ("traework", "Trae Work", "04指南L133+06JSON"),
    ("traecode", "TraeCode", "06JSON"),
    ("hermes", "Hermes(12)", "04指南L133+06JSON"),
    ("zcode", "ZCode(13)", "04指南L133+06JSON"),
    ("doubaowork", "豆包办公(15)", "04指南L133+06JSON"),
    ("teleagent", "TeleAgent(16)", "04指南L133+06JSON"),
    ("catpaw", "CatPaw(17)", "04指南L133+06JSON"),
    ("qwen", "Qwen", "adapters/子目录(无capability.yaml)"),
    ("qclaw", "Qclaw", "06JSON(pending)"),
    ("qoderwork", "QoderWork", "06JSON(pending)"),
    ("wukong", "悟空", "06JSON(ignored·2026-08-24你令不落地)"),
]

# ---------- 生成矩阵 md ----------
L = []
L.append("# 件端覆盖矩阵（试点v0：仅ZCode列实扫）")
L.append("")
L.append("> 数据截止日: 2026-10-02 · 扫描时刻: %s · 生成端: ZCode(第13端·童灵试点执行)" % SCAN_TIME)
L.append("> 施工单: 自定义层/待完成工作/2026-10-02-件端覆盖审计施工单-v2.md (v2.1)")
L.append("> 试点口径: 他端18列一律⚪未扫(试点符号·未扫≠存疑·归因律) — ⛔未跑他端真身扫描,不产他端判定")
L.append("> 行全量=三源并集: ①守卫编写规范§四注册表(机器提取L563-698·剔除表头分隔行) ②04-跨端接入指南Hook清单14件 ③scripts_manifest路由/引擎/变换在册件")
L.append("> ZCode列五态: ✅实接(真身config.json hooks.events扫出) / 🟡等效(写明承载件) / ⛔平台边界(裁定引文) / ❓未接无理由(已§四清零=0) / ➖设计不适用(引裁定/形态出处) · c挂账15件见§四处置表")
L.append("")
L.append("## 〇、行全量计数")
L.append("")
L.append("| 源 | 行数 | 去重后 | 备注 |")
L.append("|---|---|---|---|")
L.append("| ①守卫编写规范§四注册表 | 133表格行 | 131独立名 | 含3退役(traecode_isolation/l3_conclusion/reply_format)·2对重复行(stamp_precheck L620/L666·script_family_check L592/L672)·1粘连行补提(platform_adaptation_check L620行内) |")
L.append("| ②04指南Hook清单 | 14行 | 14件 | 含2退役行(#9 reply_format·#10 l3_conclusion) |")
L.append("| ③scripts_manifest(路由/引擎/变换) | 72件 | 71独立 | route_unknown_unknown.py双条目(引擎/路由引擎Hook+引擎/路由家族按需)=manifest内双本账 |")
L.append("| **三源并集** | — | **191件** | 本矩阵行全量(已剔除表头分隔行1) |")
L.append("")
L.append("## 〇.2、19端列清单（权威清单考证）")
L.append("")
L.append("> ⚠️卡手发现: 19端权威单一清单在任何单一文档不存在 — 本列名=三源机械拼合: 04指南L133对比表14列 ∪ 06-跨端适配规范§2.2.0端清单JSON(17条) ∪ adapters/子目录(补qwen)。拼合后恰=19端。")
L.append("")
L.append("| # | 端id | 端名 | 出处 | 本试点状态 |")
L.append("|---|---|---|---|---|")
for i, (eid, ename, src) in enumerate(ENDS, 1):
    st = "实扫(本端)" if eid == "zcode" else "⚪未扫(试点)"
    L.append("| %d | %s | %s | %s | %s |" % (i, eid, ename, src, st))
L.append("")
L.append("## 一、主矩阵（行=件全量191·列=19端·ZCode列实判·他端⚪）")
L.append("")
L.append("ZCode列符号后括号=判据编号，明细见§二判据明细表。")
L.append("")
hdr = "| 件名 | 行来源 | " + " | ".join(e[0] for e in ENDS) + " |"
L.append(hdr)
L.append("|" + "---|" * (2 + len(ENDS)))
srcmap = {}
for r in rows:
    key = r["name"]
    srcmap.setdefault(key, set())
    for s in r["sources"]:
        srcmap[key].add(s[0])  # ①②③
for name in sorted(V.keys()):
    srcs = "".join(sorted(srcmap.get(name, {"?"})))
    zc = V[name][0]
    zsym = zc[0] if zc[0] in "✅🟡⛔➖" else ("❓→" + zc if zc == "c挂账" else zc)
    if zc == "✅": zsym = "✅"
    elif zc == "🟡": zsym = "🟡"
    elif zc == "⛔": zsym = "⛔"
    elif zc == "➖": zsym = "➖"
    elif zc == "➖(b裁定)": zsym = "➖b"
    elif zc == "c挂账": zsym = "❓→c"
    cells = ["⚪"] * len(ENDS)
    cells[11] = zsym  # zcode index
    L.append("| %s | %s | %s |" % (name, srcs, " | ".join(cells)))
L.append("")
L.append("## 二、ZCode列判据明细表（每格证据指针）")
L.append("")
L.append("| 件名 | 态 | 证据指针 |")
L.append("|---|---|---|")
for name in sorted(V.keys()):
    st, ev = V[name]
    L.append("| %s | %s | %s |" % (name, st, ev))
L.append("")
L.append("## 三、五态分布（ZCode列·处置后）")
L.append("")
L.append("| 态 | 数 |")
L.append("|---|---|")
L.append("| ✅实接 | %d |" % dist.get("✅", 0))
L.append("| 🟡等效 | %d |" % dist.get("🟡", 0))
L.append("| ⛔平台边界 | %d |" % dist.get("⛔", 0))
L.append("| ➖设计不适用(含b裁定1件) | %d |" % (dist.get("➖", 0) + dist.get("➖(b裁定)", 0)))
L.append("| ❓未接无理由 | 0 (处置前16件:15c挂账+1b裁定·见§四) |")
L.append("| 合计 | 191 |")
L.append("")
L.append("## 三.5、试点发现：行全量外实挂件（5件·ZCode实挂但三源皆无）")
L.append("")
L.append("> ZCode实挂28件中5件不在行全量三源(注册表/Hook清单/manifest路由引擎变换scope)任何一源=行全量定义不完备的实证。分身注入链4件+W1附属1件悬空于三源体系之外。")
L.append("")
L.append("| 件 | ZCode实挂证据 | 三源缺位原因 |")
L.append("|---|---|---|")
for k, why in OUTSIDE_MOUNTED.items():
    evs = ",".join(sorted(set(mounted.get(k, []))))
    L.append("| %s | config.json hooks.events [%s] | %s |" % (k, evs, why))
L.append("")
L.append("## 四、§四消化处置表（试点口径❓16件·清零）")
L.append("")
L.append("> 试点适配口径(施工单§三.3试点适配): 件在行全量+ZCode列零承载(config.json events/capability.yaml委派面/patrol与软约束/SSOT裁定四查皆无)→❓; 判❓前已做尽职复核(os.walk第二通道扫~/.zcode全树+变更日志考古), artifacts会话缓存命中不构成承载证据。")
L.append("")
L.append("| # | 件 | 处置 | 理由(证据指针) |")
L.append("|---|---|---|---|")
for i, (name, why) in enumerate(C_ITEMS, 1):
    L.append("| %d | %s | c挂账 | %s |" % (i, name, why))
L.append("| 16 | guard_heartbeat_check.py | b裁定→➖ | 同职能已由zcode_config_guard活性腿覆盖(route_audit src:zcode实证+STALE_DAYS告警·注册表L618)·心跳真源HB_DIR在WB hooks域·引04指南L174 guard_registry_check同型裁定先例 |")
L.append("")
L.append("> a接=0件·理由: ①ZCode钩子配置不热加载(04指南L174诚实边界'改好≠生效'), 本会话无法验证运行态, 不满足零自引入缺陷的可机械验证要求 ②每接一件须BASELINE三处同轮(config+zcode_config_guard基准+04指南ZCode列), 牵动共享件超出试点单端低风险边界 ③新增件均属共享分母外扩权, 取舍归你。15件挂账工单见试点结论文档。")
L.append("")
L.append("---")
L.append("*试点v0生成 · 后续端append-only: 改前重读末行(§〇.3并发共写纪律)*")

OUT = os.path.expanduser("[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/03-体检记录/件端覆盖矩阵.md")
open(OUT, "w").write("\n".join(L) + "\n")
print("矩阵已写:", OUT, "(", os.path.getsize(OUT), "bytes )")
print("uncategorized 兜底➖数:", len(unc))
