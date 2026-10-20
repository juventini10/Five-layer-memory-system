#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_scripts.py — 布洛陀「脚本体系」安装器（包根·单一数据源）

用法：
    python3 install_scripts.py "<记忆共享中心绝对路径>"
    python3 install_scripts.py --dry-run "<记忆共享中心绝对路径>"

做三件事（幂等·可重复跑·重跑即修复）：
    ① 生成脚本中心    <记忆共享中心>/脚本中心/     ← references/scripts 全量 + references/hooks
    ①a 数字分身套件   <记忆共享中心>/数字分身/     ← references/digital-twin（scripts/devtools/gates/k2造芯/hexaco答题件）
    ①b 规则层数据     <记忆共享中心>/记忆规则/     ← rule_*.yaml + 三层规则文件
    ② 部署钩子副本    ~/.workbuddy/hooks/…          ← 按下方 ROSTER 表（主件 + 同目录依赖）
    ③ 注册 settings.json hooks                      ← 同一个 ROSTER 表驱动

🌐 多端语义（--platform <端ID>）：
    ①②③ 是「有 hook 事件端」的完整链；①/①a/①b 是**与端无关的公共资产**，任何端都装。
    无 hook 事件的端（hooks_event=false）只跳过 ②③，①/①a/①b 照常——
    端特有部分（规则落盘 / launchd patrol 等）由 adapters/<端>/<install_entry> 承载。

🔑 设计约束（根治「名册有、文件没搬」缺口）：
    ROSTER 是**唯一数据源**——②搬运与③注册读同一个数组，物理上不可能出现
    「已注册但没有文件」或「有文件但没注册」。新增/删除钩子只改这一处。

判据依据：布洛陀安装包设计通用规范 条文1「出包判据 = 端用户侧设施可达性」——
    凡注册进 settings.json 的钩子，其执行文件必须先落在端用户可达路径。

作者：布洛陀体系 | 版本：1.0.0 | 日期：2026-09-21
"""

import argparse
import glob
import json
import re
import os
import shutil
import stat
import pathlib
import datetime
import hashlib
import sys
# Windows 控制台默认 cp1252/cp936，强制 stdout/stderr UTF-8（同包 data_contamination_check.py 先例）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PKG = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = "[记忆共享中心]"
# 2026-10-10 十一轮：畸形前缀归一化（双拼病防御）——旧模板/已发布包可能残留
# 波浪号斜杠紧贴占位符的形态（deident tilde 化 + relocate 裸形态规则残留前缀），
# 纯 replace 后变 `~//Users/...`（Mac）/ `~/C:/Users/...`（Win）⇒ expanduser 静默失效。
# 替换前统一剥前缀，重装旧包也治愈存量。
TILDE_PREFIXED = "~/" + PLACEHOLDER
# 路径变量（--platform 覆盖·默认 WorkBuddy 兼容）
HOOKS_ROOT = os.path.join(os.path.expanduser("~"), ".workbuddy", "hooks")
_LANDED_INDEX = None  # P12 根治：deploy_hooks 全量落地件索引 [(rel, srcdir)]·写侧保护与指纹建档共用
# v2.0.1 多端：注册期已知端与配置根（默认 workbuddy=旧行为；--platform 分支覆盖）
_PLATFORM_ID = "workbuddy"
_CFG_ROOT_ABS = os.path.join(os.path.expanduser("~"), ".workbuddy")
SETTINGS = os.path.join(os.path.expanduser("~"), ".workbuddy", "settings.json")

# ─────────────────────────────────────────────────────────────────────────
# 钩子总表（唯一数据源）：(事件, 落位子目录, 包内目录, 主件, [同目录依赖…])
#   落位子目录 "." = ~/.workbuddy/hooks/ 根；其余 = 该子目录
#   改这张表 = 同时改「搬运」与「注册」两件事
# ─────────────────────────────────────────────────────────────────────────
ROSTER = [
    # —— 布洛陀核心 ——
    ("UserPromptSubmit", "route", "references/scripts", "route_inject_prompt.py",
     ["router.py", "format_contract.py", "hook_protocol.py"]),
    ("UserPromptSubmit", "rule", "references/scripts", "rule_fragment_inject.py",
     ["rule_triggers_loader.py", "rule_triggers.yaml", "hook_protocol.py"]),
    ("UserPromptSubmit", ".", "references/scripts", "secret_key_guard.py",
     ["hook_protocol.py"]),
    ("UserPromptSubmit", ".", "references/scripts", "ttl_expiry_guard.py",
     ["hook_protocol.py"]),
    ("UserPromptSubmit", ".", "references/scripts", "session_tail_inject.py", []),
    ("Stop", ".", "references/hooks", "route_unknown_unknown.py", []),
    ("Stop", "rule", "references/scripts", "rule_three_layer_guard.py",
     ["rule_triggers_loader.py", "rule_triggers.yaml", "hook_protocol.py"]),
    ("Stop", ".", "references/scripts", "systemlog_stophook_check.py", []),
    ("Stop", ".", "references/scripts", "reply_tail_guard.py", []),
    ("Stop", ".", "references/scripts", "post_change_guard.py", []),
    ("Stop", ".", "references/scripts", "delivery_boundary_guard.py", []),
    ("PreToolUse", ".", "references/scripts", "edit_heading_guard.py", []),
    ("PreToolUse", ".", "references/scripts", "skill_write_gate_guard.py", []),
    ("PreToolUse", ".", "references/scripts", "skill_spec_read_guard.py", []),
    ("PreToolUse", ".", "references/scripts", "grep_sandbox_guard.py", []),
    ("SessionStart", ".", "references/scripts", "crossend_guard.py", []),
    # —— 2026-10-03 补进 18 件（端中立·实测无作者侧依赖·此前"在包里但从不注册"=死件）——
    # 事件归属**取自本机 settings.json 实挂**（⛔ 不凭印象分配事件）。
    # ⚠️ 维护提醒：新增/停用只改这一处表，deploy_hooks / register_hooks / --verify 三处同源。
    ("UserPromptSubmit", ".", "references/scripts", "kb_inject_prompt.py",
     ["runtime_paths.py"]),
    ("UserPromptSubmit", ".", "references/scripts", "route_miss_feeder.py", []),
    ("PreToolUse", ".", "references/scripts", "change_reflux_guard.py", []),
    ("Stop", ".", "references/scripts", "audit_search_kb.py", []),
    ("Stop", ".", "references/scripts", "card_id_guard.py", []),
    ("Stop", ".", "references/scripts", "change_closedloop_guard.py", []),
    ("Stop", ".", "references/scripts", "design_family_guard.py", []),
    ("Stop", ".", "references/scripts", "feedback_detect.py", []),
    ("Stop", ".", "references/scripts", "guard_heartbeat_check.py", []),
    ("Stop", ".", "references/scripts", "record_card_trigger.py", ["transcript_reader.py"]),
    # —— 对话标题自动命名（2026-10-03 补·脱敏后纳入·依赖 session_title_utils.py 同在脚本中心）——
    ("UserPromptSubmit", ".", "references/scripts", "session_title_namer.py",
     ["session_title_utils.py"]),
    ("Stop", ".", "references/scripts", "route_audit.py", ["router.py"]),
    ("Stop", ".", "references/scripts", "route_guard_audit.py", []),
    ("Stop", ".", "references/scripts", "triwich_closeout_guard.py", []),
    ("Stop", ".", "references/scripts", "vision_gate.py", []),
    ("Stop", ".", "references/scripts", "workbuddy_config_guard.py", []),
    ("Stop", ".", "references/scripts", "workbuddy_inject_chain_guard.py", []),
    ("Stop", ".", "references/scripts", "workbuddy_skill_health_guard.py", ["skill_health_common.py"]),

    # —— 守卫族自动体检入口（2026-10-03 补·落 <MC>/数字分身/guards/）——
    # ⚠️ 跑的是「脚本中心 + guards/ 目录」下全部 *guard.sh（文件系统即真相源·新增守卫零配置接入）
    # deps=部署但不注册（Windows 承载孪生件·2026-10-11 批次6）：注册哪条由 _hook_command 按平台选
    ("Stop", ".", "references/scripts", "run_registry_guards.sh", ["run_registry_guards.ps1"]),

    # —— 数字分身（随分身启用；未部署分身者钩子会安全空转）——
    ("UserPromptSubmit", ".", "references/digital-twin/devtools", "doenglingz_inject_prompt.py", []),
    ("Stop", ".", "references/digital-twin/devtools", "twin_verdict_ledger.py", []),
    ("Stop", ".", "references/digital-twin/devtools", "twin_changelog_guard.py", []),
]

TEXT_EXT = (".py", ".sh", ".yaml", ".yml", ".json", ".md",
            ".ps1", ".plist", ".template", "",
            ".jsonl", ".txt", ".cmd", ".swift")  # 2026-10-20 反馈：Skill 拷贝链实际含这四类文本，
                                                 # 旧白名单外=占位符原文出包（当前 0 处·防未来静默）
            # 2026-10-11 批次6：A2/E3 根治——原白名单漏这几类，
                                               # 其中占位符永不本地化（Win 侧必错根·真机 T16 报 12 件）

# ─── R1 转义地雷根治（2026-10-11 _fill转义地雷根治卡）───────────────────
# 病根：Win 的 mc 含反斜杠，裸 replace 填进"会二次解析反斜杠"的格式面就吃字面——
#   .py 串内 \a→BEL（真机 WinError 123 实证）、C:\Users 的 \U→SyntaxError 编译即死；
#   .json 串内 \U→loads 崩、\b\f\n\r\t→静默变控制符；.yaml 双引号 scalar 同毒。
# 修法：仅对转义敏感面填入前把 mc 换正斜杠（Win32 API/Python/JSON/YAML/shell 全域接受），
#   .ps1/.plist/.md/.sh/conffiles 等展示与字面语义面保留反斜杠原样（不改变显示）。
# 本体先例：L925/955/959/969 hooks 命令串早已用 .replace("\\", "/") 同型解法。
SLASH_FILL_EXT = (".py", ".json", ".yaml", ".yml", ".template")
_FILL_REPORT = []  # R2 门禁原料：本轮被填写盘的 (path, ext)

def _mc_for(ext, mc):
    """按目标扩展名选 mc 变体：转义敏感面→正斜杠；其余→原样。"""
    return mc.replace("\\", "/") if ext in SLASH_FILL_EXT else mc

# ─────────────────────────────────────────────────────────────────────────
# 数字分身套件（2026-09-30 补部署契约·根治「入包了不活」）
#   判据＝端用户侧设施可达性：凡被端用户可见物（Skill 正文/安装文档/守卫豁免表）
#   以运行/指令形态引用的件，必须在装机态可达。落点由包内既有引用自证：
#     · checklist_backfill.py:29  → [记忆共享中心]/数字分身/scripts/verify_checklist_gate.py
#     · launchd_health_check.sh   → [记忆共享中心]/数字分身/scripts/{state_bus_sync,sync_readme_scripts_index}.py
#     · skill_spec_read_guard.py:39 / skill_write_gate_guard.py:42 → 豁免路径 /数字分身/scripts/
#   未列入本表的 digital-twin/scripts 件＝作者侧运营工具（造评测集/发布灰度/多端巡检/
#   launchd 自检），已由 mirror-manifest 的 digitaltwin-scripts@v2（intersection_only）
#   排除出包——它们对端用户零用户。
# ─────────────────────────────────────────────────────────────────────────
DT_SUITE = {
    # Skill 运行依赖（good-good-study / growth-box / daily-buddy / triwich 引用）
    "scripts": ("count_card_topic.py", "auto_pass_audit.py", "batch_auto_pass.py",
                "job_probation_check.py", "job_audit_check.py",
                "error_candidate_miner.py", "verify_checklist_gate.py",
                "state_bus_sync.py",          # growth-box SKILL.md:540 硬指令「晋升后必须 --update」
                "doenglingz_drift_check_remind.py",
                "com.doenglingz.drift-check-remind.plist.template",
                # 2026-10-19 Q3路线C装机周期守护两件（声明见 digital-twin/guardians.json·Q6门禁②对账）
                "com.doenglingz.slice-watch.plist.template",
                "slice-watch-install-task.ps1",
                # K2 造芯链路引用（立场卡 triggers 机械核验 / H4 冲突样本采集）
                "blank_claim_guard.py", "h4_sample_log.py"),
    # 童灵治理套件（守护/闸门运行器/TSL 报告器）
    #   · doenglingz_guard.py ＝ gates/G2.json 的 delegate（红线触碰检查实现）
    #     且被 adapters/lobsterai/setup.sh 复制进插件 lib/
    #   · shadow_append.py ＝ daily-buddy 的 SHADOW.md 合法写入口（Skill 明载必走）
    "devtools": ("doenglingz_guard.sh", "doenglingz_guard.py", "gate_runner.py",
                 "doenglingz_tsl_report.py", "shadow_append.py",
                 # 2026-09-30 纳管 by ZCode（发布者令「评估ZCode能否经安装包完整安装·数字分身面」）：
                 # ZCode 形态分身钩子件（guard_zcode=ZCode 专属守护 / position3=岗位3触达 /
                 # level_declare+tsl_closeout=06 §1.6 挂载边界反查两件·全端义务）。
                 # 端中立部署：非 ZCode 端装了不挂载=零副作用；ZCode setup.sh 注册时引用本部署面。
                 "doenglingz_guard_zcode.py", "position3_notify.py",
                 "doenglingz_level_declare_guard.py", "tsl_closeout_guard.py",
                 "tsl_verify.py", "tsl_echo_hook.py", "tsl_tree_hook.py",
                 # 2026-09-30 补·LobsterAI 运行面需要（WB ROSTER 已注册 Stop 两件·非 WB 端
                 # 此前不在 DT_SUITE → 数字分身 devtools 不部署 → 端用户钩子指针悬空）：
                 "twin_verdict_ledger.py", "twin_changelog_guard.py"),
    # 守卫族（2026-10-03 补·承 registry_guards.sh 的"文件系统即真相源"机制）
    #   registry_guards.sh ＝ Stop 钩子入口·自动发现并跑同目录全部 *guard.sh
    #   kb_index_guard.sh ＝ 知识池↔INDEX 一致性（修复前"曾存在数周零使用"）
    # ⛔ 端中立：两件内 ⛔ 无作者侧路径（GUARD_DIR/DOC_CHECK 均走环境变量+同目录缺省）
    #   skill_version_guard.sh ＝ Skill 版本 ↔ 其 CHANGELOG 顶版对账（⛔ 不带 changelog_guard：
    #     它检查记忆规则三层的 CHANGELOG，而该文件不在包内 ⇒ 端用户机无对象可守）
    "guards": ("registry_guards.sh", "kb_index_guard.sh", "skill_version_guard.sh"),
    # 闸门声明（G1-G4 + health_probes）＝ Phase A2 骨架明载项
    "gates": None,          # None = 整目录
    # K2 造芯管线（2026-09-30 补·闭合 Phase A3「造芯管线可跑」承诺）
    #   判据＝INSTALL.md §数字分身完整版单装 Phase A3 明载「33 题答案在位 → 造芯管线可跑
    #   （你自己蒸馏规格书→切片）」，且 adapters/traework/setup.sh 缺 slices 时的提示路径
    #   直指本目录 → 不装＝端用户死引用（条文 17 腿A/腿D）。
    #   ⛔ 只装自足造芯三件：k2_slice_generator（规格书→切片·stdlib only）/
    #   hexaco_slice_generator（人格向量→基座切片）/ k2_slice_probe（试切体积探针）。
    #   同目录其余件＝作者侧实验产物（d4_behavior 评测集 2.8MB / D1 调研清单生成器
    #   读作者侧 日记仓库+AI学习库）→ ⛔不入包（条文 1 端用户侧前提）。
    "k2-slice-generator": ("k2_slice_generator.py", "hexaco_slice_generator.py",
                           "k2_slice_probe.py"),
    # 人格测评答题件（2026-09-30 补·养成链第一步入职入口·判定标准「用户更好体验」）
    #   判据＝养成链第一步「答题」必须有装机态入口：AI 安装完成后直接 open 答题页，
    #   用户零找路。⛔只装测评白名单件（题库+自建答题页+官方答题卡+官方计分键PDF）——
    #   2026-10-10 收敛：hexaco/ 包内终态=这五件本体（作者侧回流的互照套件×3/探针题库
    #   （含本体读数H4.75·脱敏红线回归）/60简版/runner 六件已移出至
    #   数字分身/HEXACO测评/包内移出-20261010/；verify §3.8 hexaco终态穷举断言在岗防再回流。）
    #   2026-10-15 C27 增量：`hexaco_selfbuild_scorer.py`（自建 100 题自动计分器）入部署面——
    #   题库 §八 第4条自陈待办「写入 scorer → 随包」此前从未落地，D2 计分实际由 AI 手算 96 个数
    #   （E2E 实测首轮手抄错 2 题）。⛔只装不引导=死件，同轮把 INSTALL/step8/入门指南的 D2 口径
    #   从「粘贴给 AI 算」改为「跑本脚本」，并在 verify §3.8 加在位断言（缺件即红·防再次漂移）。
    #   2026-10-15 C34 增量：官方卷计分链入部署面——`hexaco_official_scorer.py`＋键表投影
    #   `hexaco_official_keytable-100.json`（PDF 机器投影·头含 sha 溯源）＋`HEXACO-100-HTML答题页.html`
    #   （此前官方页在包不部署：答题卡/PDF 已部署而答题入口缺失=官方链断点，本卡补全）。
    #   ⛔只装不引导=死件：同轮改答题卡口径＋INSTALL D2 官方命令行＋verify §3.8 清单/引导断言。
    "hexaco": ("自建100题-分身版-题库-v1.md", "自建100题-答题页-v1.html",
               "HEXACO-100完整版-官方中文-答题卡.md",
               "ScoringKeys_100.pdf", "hexaco_selfbuild_scorer.py",
               "hexaco_official_scorer.py", "hexaco_official_keytable-100.json"),  # P28作者裁决2026-10-18：官方壳页移出包面（答题页物理单源=自建版；官方参照物保留）
    # 装机日引导三件（2026-09-30 补·全端统一造芯流程）：
    #   人格向量空模板 / 规格书骨架模板 / 通用入门指南。装机日 AI 从本目录复制模板到
    #   「数字分身/」根、改名、陪用户填，再跑 k2-slice-generator 造切片。
    #   全端共享同一份 → 任意端造芯流程一致；端差异只在 adapters/<端>/ 接入。
    "onboarding": ("童灵·人格向量-空模板.json", "童灵·人格规格书-骨架模板.md",
                   "入门指南-通用版.md"),
}


def deploy_digital_twin(mc, dry=False):
    """部署数字分身运营套件 → <MC>/数字分身/{scripts,devtools,gates}/（幂等）。

    ⚠️ **只覆盖运营套件，不碰用户数据**（2026-10-03 明确·跨端共享铁律）：
      DT_SUITE 只含 scripts/devtools/gates/k2-slice-generator/hexaco/onboarding
      ——这些是**工具/模板/运营件**，重复安装覆盖是安全的。
      用户数据（童灵·人格规格书.md / K2切片蒸馏/slices/ 下的已生成切片）
      **不在 DT_SUITE 中**，本函数永不触碰——重复安装不会覆盖用户已填的
      人格规格书和已生成的切片。
    """
    base = os.path.join(PKG, "references", "digital-twin")
    dst_root = os.path.join(mc, "数字分身")
    n = 0
    for sub, files in DT_SUITE.items():
        src_dir = os.path.join(base, sub)
        if not os.path.isdir(src_dir):
            continue
        names = sorted(os.listdir(src_dir)) if files is None else list(files)
        for name in names:
            src = os.path.join(src_dir, name)
            if not os.path.isfile(src):
                continue
            if not dry:
                os.makedirs(os.path.join(dst_root, sub), exist_ok=True)
            _copy(src, os.path.join(dst_root, sub, name), dry)
            n += 1
    if not dry:                      # 占位符替换（与脚本中心同惯例）
        for root, _dn, fs in os.walk(dst_root):
            for name in fs:
                if name.endswith(TEXT_EXT):
                    _fill(os.path.join(root, name), mc)
    return n


# ─────────────────────────────────────────────────────────────────────────
# 装机态运行落点自举（2026-10-13 根治·封包前置·包宪法命题二「防误 > 防错」）
#   判据＝凡被 Skill 以运行形态引用、且首跑即 sys.exit(1)/exit(2) 的落点文件，
#   装机态必须物理可达（条文 17 腿A：不装＝端用户死引用）。
#   实跑定位的硬隐患集（源=references/digital-twin/scripts 逐脚本读 exit 绑定）：
#     · job_probation_check.py load_ledger  缺台账            → exit(1)
#     · job_probation_check.py record       缺岗位定义          → exit(1)
#     · batch_auto_pass.py                  缺 step3 初审台账   → exit(1)
#     · job_audit_check.py                  缺台账              → exit(2)
#   （概念碰撞成就.md 属成就系统，随 references/成就系统 整目录复制路由投递，本函数不重复；
#    step3-blocked-cards.md 由 job_probation_check 的「首张发生时创建 + 不存在跳过」优雅处理，
#    step3-handover-protocol.md 无脚本硬 exit → 均不入自举，守「精准不过界」）。
#   ⛔ 不补造历史数据：只写「空骨架」（零决策/零记录），与「不补造」纪律正交。
#   幂等律（硬边界①可观测 + 存量机保护）：目标已存在＝用户数据，⛔绝不覆盖，仅报 skipped。
# ─────────────────────────────────────────────────────────────────────────
def _ledger_skeleton(mc):
    """岗位台账空骨架：三在岗岗位以 probation 起步、零决策。
    JOB-002 蒸馏调度岗不设推翻率台账（编号非断档·见 ledger_scope_note）。"""
    today = datetime.date.today()
    end = today + datetime.timedelta(days=30)          # 试用期 1 个月
    iso = lambda d: d.strftime("%Y-%m-%d")

    def job(name, system, level):
        return {"job_name": name, "system": system,
                "probation_start": iso(today), "probation_end": iso(end),
                "status": "probation", "authorization_level": level,
                "decisions": [],
                "stats": {"total": 0, "approved": 0, "rejected": 0,
                          "modified": 0, "questioned": 0, "self_corrected": 0,
                          "rejection_rate": 0.0}}

    return {
        "version": "1.0", "last_updated": iso(today),
        "description": ("童灵岗位试用期推翻率台账——自动记录童灵每次决策后你的响应，"
                        "试用期结束时自动统计推翻率，输出转正评估报告。"
                        "符合愿景①全自动化（不需要人工统计）。"),
        "ledger_path": os.path.join(mc, "数字分身", "job_probation_ledger.json"),
        "check_script": os.path.join(mc, "数字分身", "scripts", "job_probation_check.py"),
        "response_types": {"approved": "✅你确认通过", "rejected": "❌你拒绝",
                           "modified": "🔄你要求修改",
                           "questioned": "❓你质疑评估角度/方式方法"},
        "conversion_criteria": {
            "time": "试用期满1个月（从上岗日期起算）",
            "quality": "试用期内推翻率<15%",
            "confirmation": "你确认转正（你可凭实战背景直接拍板转正，不受15%阈值限制）",
            "post_conversion": ("🟡试用期→🟢在岗，授权等级可按演进路径申请升级"
                               "（L1→L2→L3→L4，每级升级需重新试用期验证），"
                               "推翻率持续监控但不需每月复测"),
            "failure_handling": ("推翻率≥15%或你主动决定不转正：①延长试用期1个月"
                                "（回炉复测）②降级授权等级（如L3→L2）③收回岗位"
                                "（🔴已收回，岗位编号保留不删除）。具体处理方式由你决定")},
        "ledger_scope_note": ("JOB-002蒸馏调度岗不设推翻率台账（其运转检验=蒸馏中心按账核），"
                              "编号非断档"),
        "jobs": {
            "JOB-001": job("立场卡价值预筛岗",
                           "good-good-study (知识库立场卡)", "L1预筛（价值过滤）"),
            "JOB-003": job("成长箱审核岗", "growth-box", "L1审核"),
            "JOB-004": job("技能卡审核岗（七闸）",
                           "good-good-study (AI学习库技能卡)", "L1七闸审核"),
        },
    }


def _first_review_skeleton():
    """step3 初审台账 0 态骨架：表头就绪、零数据行（batch_auto_pass 正则扫到 0 行
    返回空 dict、job_audit_check 日志ID数=台账 0 决策=齐，均不崩）。"""
    return (
        "# Step 3 · 分身初审台账（童灵上岗记录）\n\n"
        "> **路由**：good-good-study SKILL.md ④入库（A线动作）+ AI学习库 INDEX.md\n"
        "> **硬格式**：层级归属 / 置信度 / 裁决+边界 / 依据 / 升级声明 / 可回溯理由\n"
        "> **决策ID规则**：JOB-{编号}-{YYYYMMDD}-{NNN}（岗位-日期-当日序号）\n"
        "> **下游**：你推翻 → 台账 response 更新；月度汇总 → 规格书迭代\n\n"
        "## 📋 初审记录\n\n"
        "| 序号 | 日期 | 卡ID | 层级归属 | 置信度 | 裁决+边界 | 依据 | 升级声明 | 你复核 |\n"
        "|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        "<!-- 首张初审卡由岗1预筛时按 record 动作追加于本表；装机初始为空 -->\n"
    )


def bootstrap_runtime_state(mc, dry=False):
    """缺才建、有则绝不覆盖（存量机用户数据保护）。返回逐项落点清单供打印。"""
    dt_root = os.path.join(mc, "数字分身")
    targets = (
        (os.path.join(dt_root, "job_probation_ledger.json"),
         lambda: json.dumps(_ledger_skeleton(mc), ensure_ascii=False, indent=2) + "\n"),
        (os.path.join(dt_root, "steps", "step3-first-review-log.md"),
         _first_review_skeleton),
    )
    report = []
    for path, gen in targets:
        rel = os.path.relpath(path, mc)
        if os.path.exists(path):
            report.append("skipped·存量保留 %s" % rel)
            continue
        if not dry:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(gen())
        report.append("created %s" % rel)
    return report



def _detect_existing_twin(mc):
    """检测用户是否已在其他端造过芯（跨端共享·不重复造芯）。

    判据（双条件同时满足才算"已有分身"）：
      ① <MC>/数字分身/童灵·人格规格书.md 存在（用户已填实的人格规格书）
      ② <MC>/数字分身/K2切片蒸馏/slices/ 下有切片文件（生成器已跑过）

    只检测不操作——返回 True/False，调用方决定打印什么。
    ⛔ 本函数不删除/覆盖任何用户数据。
    """
    spec = os.path.join(mc, "数字分身", "童灵·人格规格书.md")
    slices_dir = os.path.join(mc, "数字分身", "K2切片蒸馏", "slices")
    if not os.path.isfile(spec):
        return False
    if not os.path.isdir(slices_dir):
        return False
    entries = os.listdir(slices_dir)
    if not entries:
        return False
    return any(os.path.isfile(os.path.join(slices_dir, f)) for f in entries)


def pre_install_health_check(mc, platform_id, cap=None, cfg_root=None, dry=False):
    """安装前端体检报告（2026-10-03·条文20/21）：检测端之后、部署之前，
    扫描记忆共享中心下已有资产，输出已有/缺失清单 + 端能力 + 建议操作。

    三种场景：
      - 新用户：全部缺失 → 走完整安装
      - 老用户：有什么缺什么 → 建议增量装
      - 跨端用户：公共资产已在位（其他端装过）→ 只装端适配

    只扫描不操作——返回 dict 含资产状态，调用方决定是否继续。
    """
    tag = "[dry-run] " if dry else ""
    print()
    print("━━━━━━━━ 🩺 安装前端体检报告 ━━━━━━━━")

    # ── 1. 扫描公共资产（记忆中心级·跨端共享）──
    assets = {}
    # 脚本中心
    sc = os.path.join(mc, "脚本中心")
    assets["脚本中心"] = os.path.isdir(sc) and any(
        os.path.isfile(os.path.join(sc, f)) for f in os.listdir(sc)
    ) if os.path.isdir(sc) else False
    # 知识联邦引擎
    kb = os.path.join(mc, "知识联邦引擎")
    assets["知识联邦引擎"] = os.path.isdir(kb)
    # 数字分身（运营套件在位）
    dt = os.path.join(mc, "数字分身")
    dt_scripts = os.path.join(dt, "scripts")
    assets["数字分身套件"] = os.path.isdir(dt_scripts)
    # 数字分身（用户已造芯）
    assets["数字分身·已造芯"] = _detect_existing_twin(mc)
    # 记忆规则
    rd_dir = os.path.join(mc, "记忆规则")
    assets["记忆规则"] = os.path.isdir(rd_dir) and any(
        name in os.listdir(rd_dir) for name in RULE_FILES
    ) if os.path.isdir(rd_dir) else False
    # Skill（技能配置）
    skills_dir = os.path.join(mc, "技能配置")
    skill_count = 0
    if os.path.isdir(skills_dir):
        skill_count = sum(
            1 for d in os.listdir(skills_dir)
            if os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
        )
    assets["Skill"] = skill_count > 0
    assets["_skill_count"] = skill_count
    # 五系统文件在位（2026-10-15 C29 根治·两分支合一到声明解析）：
    # 旧 zwork 特判锚表键名「自定义指令.md」与名单失配（静默少计=本卡键名漂移的又一处实例）；
    # 旧扁平分支把名单键当文件名（WB 字段型恒判缺失、声明了 memories/ 子目录的端也判缺失）——
    # 判据面与落点面不相交。现=system_file_targets() 按端声明解析三形态（~/、::、platform://），
    # 端自有实体经声明值表达 ⇒ platform_id=="zwork" 特判退役（端中立+1）。
    # 行为差如实注：zwork 在位计数 4→5（第五件 AGENTS.md 实体在位·旧因键名失配漏计）；
    # 其余端计数只增不减（字段型/子目录型从恒缺失变为按声明判）。
    _cap = cap or {}
    if not _cap.get("system_file_paths") and platform_id:
        _cp = os.path.join(PKG, "adapters", platform_id, "capability.yaml")
        if os.path.isfile(_cp):
            _cap = load_capability(_cp)
    targets = system_file_targets(cfg_root or mc, _cap)
    sys_present = []
    for name, v in targets.items():
        if isinstance(v, dict):
            ok = True if "platform" in v else os.path.isfile(v.get("file", ""))
            # platform://=端自有托管面（verify 同口径判信任源）；字段级=宿主文件在位即计
        else:
            ok = bool(v) and os.path.isfile(v) and os.path.getsize(v) > 0
        if ok:
            sys_present.append(name)
    assets["五系统文件"] = len(sys_present)
    assets["_sys_files"] = sys_present

    # ── 2. 判定用户身份 ──
    public_assets = ["脚本中心", "数字分身套件", "记忆规则", "Skill"]
    public_present = sum(1 for k in public_assets if assets.get(k))
    # F10 根治（2026-10-17）：资产存在 ≠ 老用户——全新用户走完 step5 后，五系统文件/
    # 规则/Skill 已由步骤文档预生成，旧判据（public_present>=2 ⇒ 老用户）把**在装的新用户**
    # 误报"老用户"+建议"增量升级"，与 INSTALL Step -0.6 播报 B「机器上没有旧版本」矛盾。
    # 正源=安装完成标记（.install/version·step7 7c 写；或 step7-done.md）——
    # 无标记=首次安装进行中（现有资产是步骤5 产物·非旧版遗留）。
    _ever_installed = (os.path.isfile(os.path.join(mc, ".install", "version"))
                       or os.path.isfile(os.path.join(mc, ".install", "step7-done.md"))
                       # 2026-10-20 反馈#2：versions.json 是安装末尾写入的组件快照，
                       # 其存在=装过（老用户）；旧判据漏它 → 老用户被误判"首次安装进行中"。
                       or os.path.isfile(os.path.join(mc, ".install", "versions.json")))
    if not _ever_installed:
        user_type = "新用户（首次安装进行中·现有资产为步骤5 预生成·非旧版遗留）"
        suggestion = "完整安装（继续走完 step6-7·⛔ 不按老用户跳过问卷等前置）"
    elif public_present == 0 and assets["五系统文件"] == 0:
        user_type = "新用户"
        suggestion = "完整安装（全部资产从零部署）"
    elif assets["数字分身·已造芯"] and public_present >= 3:
        user_type = "跨端老用户（已在其他端造过芯）"
        suggestion = "增量升级（公共资产已在位·只补缺的和端适配·跳过造芯）"
    elif public_present >= 2:
        user_type = "老用户"
        suggestion = "增量升级（只补缺的，不覆盖已有的）"
    else:
        user_type = "半安装态（安装中断过）"
        suggestion = "从中断处继续（补装缺失资产）"

    # ── 3. 输出报告 ──
    print("检测到端：%s" % (cap.get("display_name", platform_id) if cap else platform_id))
    print("用户身份：%s" % user_type)
    print()
    print("【已有资产】")
    for k in ["五系统文件", "脚本中心", "知识联邦引擎", "数字分身套件",
              "数字分身·已造芯", "记忆规则", "Skill"]:
        v = assets.get(k)
        if k == "五系统文件":
            print("  %s：%s（%d/4在位：%s）" % (
                "✅" if v >= 4 else ("⚠️" if v > 0 else "❌"),
                k, v, ", ".join(assets["_sys_files"]) or "无"))
        elif k == "Skill":
            print("  %s：%s（%d个）" % ("✅" if v else "❌", k, assets["_skill_count"]))
        elif k == "数字分身·已造芯":
            print("  %s：%s" % ("✅" if v else "❌", k))
        else:
            print("  %s：%s" % ("✅" if v else "❌", k))

    # 缺失清单
    missing = [k for k in public_assets if not assets.get(k)]
    if assets["五系统文件"] < 4:
        missing.append("五系统文件（缺%d个）" % (4 - assets["五系统文件"]))
    if missing:
        print()
        print("【缺失/待升级】")
        for m in missing:
            print("  ⚠️  %s" % m)

    # ── 4. 端能力分析 ──
    if cap:
        caps = cap.get("capabilities", {})
        print()
        print("【端能力】")
        cap_labels = {
            "hooks_event": ("Hook事件", "有" if caps.get("hooks_event") else "无"),
            "rules_inject": ("规则目录直落", "支持" if caps.get("rules_inject") else "不支持（UI粘贴）"),
            "skill_symlink": ("Skill软链", "支持" if caps.get("skill_symlink") else "不支持（手动安装）"),
            "settings_json": ("settings.json", "有" if caps.get("settings_json") else "无"),
            "custom_directive": ("自定义指令", "支持" if caps.get("custom_directive") else "不支持"),
        }
        for key, (label, val) in cap_labels.items():
            if key in caps:
                print("  · %s：%s" % (label, val))

    print()
    print("【建议操作】%s" % suggestion)
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if not dry:
        print("（体检完成·继续安装·如需中止请按 Ctrl+C）")
    print()
    return {"user_type": user_type, "assets": assets, "suggestion": suggestion}


def _status(path):
    """统计用：返回 'ok' 表示普通文件存在。"""
    return os.path.isfile(path)


def _fill_text(txt, mc, ext=None, paths=None):
    """占位符替换（**纯函数版**·⛔ 不写盘）。

    拆出来的原因：断章增量要求「先在内存里替换好，再整块写进段里」，
    否则会出现「包模板已填、用户文件已填」两份不同占位符 ⇒ 冲突判定误报。
    ext=目标文件扩展名（R1·2026-10-11）：转义敏感面自动斜杠化 mc；不传=原样（.md 文档面）。
    paths=F4 根治（2026-10-17）：{MEMORY_CENTER/DIARY_REPO/KNOWLEDGE_BASE/DIARY_SUBDIR}
      —— 旧版只换 [记忆共享中心]，[日记仓库]/[知识库]/[日记子目录] 安装器零管辖
      ⇒ 走完主路径+step6 文档 glob（漏 .py）后技能 .py 仍残留 16 处字面量，
      日记采集/成就追踪脚本路径全错（10-14「12 件残留」的变形复发）。括号+花括号双形态都换。
    """
    t = (txt or "").replace(TILDE_PREFIXED, PLACEHOLDER)
    t = t.replace(PLACEHOLDER, _mc_for(ext or "", mc))
    t = t.replace("{" + PLACEHOLDER[1:-1] + "}", _mc_for(ext or "", mc))
    if paths:
        for _key, _ph in (("DIARY_REPO", "日记仓库"), ("KNOWLEDGE_BASE", "知识库"),
                          ("DIARY_SUBDIR", "日记子目录")):
            _v = (paths or {}).get(_key)
            if _v:
                # 2026-10-20：.py/.json 转义敏感面统一正斜杠（否则 Windows 路径的 \_ 等
                # 会落进普通字符串 → SyntaxWarning / 编译雷；fill_syntax_scan 真机实锤）
                _v = _mc_for(ext or "", _v)
                # 先处理带家目录前缀的形态（~/[日记仓库] 直接填成绝对值，否则变 ~/C:/… 双前缀）
                t = (t.replace("~/[" + _ph + "]", _v)
                      .replace("~/{ " + _ph + " }", _v)
                      .replace("~/{" + _ph + "}", _v)
                      .replace("[" + _ph + "]", _v)
                      .replace("{" + _ph + "}", _v))
        # 2026-10-20：花括号新占位符（vault 探测态）——旧实现只有 [日记仓库]/[知识库]，
        # 新增 {{DIARY_ROOT}}/{{KB_ROOT}} 无填充器 ⇒ 装机后原样残留（审查实锤）。
        for _ph, _key in (("{{DIARY_ROOT}}", "DIARY_ROOT"), ("{{KB_ROOT}}", "KB_ROOT")):
            _v = (paths or {}).get(_key)
            if _v:
                _v = _mc_for(ext or "", _v)
                t = t.replace(_ph, _v)
    return t


def _read_install_paths(mc):
    """F4（2026-10-17）：从 <mc>/.install/step3-done.md 读路径变量，喂 _fill_text。

    缺 DIARY_SUBDIR（step3-done 模板无此键·日记子目录在 step6 才定）时回落
    包内通行约定 1-每日计划/01-日记（step6-skill-install 步骤1 示例值）。
    """
    out = {"DIARY_SUBDIR": "1-每日计划/01-日记"}
    p = os.path.join(mc, ".install", "step3-done.md")
    if os.path.isfile(p):
        try:
            for line in open(p, encoding="utf-8"):
                m = re.match(r"^(MEMORY_CENTER|DIARY_REPO|KNOWLEDGE_BASE|DIARY_SUBDIR)=(.+)$",
                             line.strip())
                if m:
                    out[m.group(1)] = m.group(2).strip()
        except OSError:
            pass
    # 占位态视为缺省
    for _k in ("DIARY_REPO", "KNOWLEDGE_BASE"):
        _v = (out.get(_k) or "").strip()
        if _v.startswith("[") or _v.startswith("{{"):
            out.pop(_k, None)
    try:
        _dr = detect_diary_root(mc)                      # …/1-每日计划/01-日记
        out["DIARY_ROOT"] = _dr
        out.setdefault("DIARY_REPO", os.path.dirname(os.path.dirname(_dr)))
        out["KB_ROOT"] = detect_kb_root(mc)
        out.setdefault("KNOWLEDGE_BASE", out["KB_ROOT"])
    except Exception:
        pass
    return out


def _fill(path, mc, dry=False):
    """占位符替换：<记忆共享中心> → 实际绝对路径（仅文本类文件·R1 按扩展名转义适配）。"""
    if not path.endswith(TEXT_EXT):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
    except (OSError, UnicodeDecodeError):
        return 0
    if PLACEHOLDER not in txt:
        return 0
    txt = txt.replace(TILDE_PREFIXED, PLACEHOLDER)  # 十一轮：畸形前缀归一化
    n = txt.count(PLACEHOLDER)
    if not dry:
        ext = os.path.splitext(path)[1]
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt.replace(PLACEHOLDER, _mc_for(ext, mc)))
        if ext in (".py", ".json"):
            _FILL_REPORT.append(path)  # R2 门禁原料（仅语法可判面登记）
    return n


def fill_syntax_guard():
    """R2 填后语法门禁（2026-10-11 根治卡）：本轮被填 .py 必过 compile、.json 必过 loads。

    病名：语法雷靠真机运行时才炸=用户侧首触即死；本门禁把检出左移到装机当轮。
    ⛔不吞不静默——失败件由调用方并入 bad 列表（rc=1 阻断+进回执原料）。
    返回 bad 字符串列表（空=全绿）。
    """
    import json as _json
    bad = []
    for p in _FILL_REPORT:
        try:
            # utf-8-sig：BOM 开头 .py 在 import 层合法，直读 utf-8 会假报（2026-10-11 全机扫首跑逮到）
            src = open(p, encoding="utf-8-sig").read()
            if p.endswith(".py"):
                compile(src, p, "exec")
            else:
                _json.loads(src)
        except Exception as e:
            bad.append("填后语法雷:%s(%s)" % (p, str(e)[:100]))
    return bad


def _copy(src, dst, dry=False):
    if dry:
        return not os.path.exists(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    try:
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass
    return True


def _md5(p):
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()
    except Exception:
        return "-"


def _sha8(path):
    """P12 内容指纹（2026-10-19）：sha256 前8位，读不了返回 '-'。"""
    try:
        return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:8]
    except Exception:
        return "-"  # 注意：⛔在此吞 NameError 类编程错——改动本函数后必跑沙箱装实测（P12 自测逮过本病）


def _hook_fingerprints_path():
    return os.path.join(os.path.dirname(SETTINGS), "hook_fingerprints.json")


def write_hook_fingerprints(deployed, dry=False):
    """P12 升级第三层判定基线：逐钩子记录 {sub: {pkg_sha8, installed_sha8, srcdir}}。
    旧基线只有事件→basename 清单（存在性两层），差异不可见——本件补内容指纹参照系。"""
    if dry:
        return False
    fp = _hook_fingerprints_path()
    data = {}
    if os.path.isfile(fp):
        try:
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    index = globals().get("_LANDED_INDEX")
    if index:
        # P12 根治：全量落地件（主件+依赖）逐件建档，写侧保护与三态呈报同一参照系
        for rel, srcdir in index:
            landing = os.path.join(HOOKS_ROOT, rel)
            src = os.path.join(PKG, srcdir, os.path.basename(rel))
            data[rel] = {"pkg_sha8": _sha8(src), "installed_sha8": _sha8(landing),
                         "srcdir": srcdir}
    else:
        for ev, subpath, srcdir, _m in deployed:
            bname = os.path.basename(subpath)
            landing = os.path.join(HOOKS_ROOT, subpath)
            src = os.path.join(PKG, srcdir, bname)
            data[subpath] = {"pkg_sha8": _sha8(src), "installed_sha8": _sha8(landing),
                             "srcdir": srcdir}
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, fp)
    print("🧭 钩子内容指纹基线已写：%d 件（升级三态判定的参照系·P12）→ %s" % (len(data), fp))
    return True


def report_hook_three_state():
    """P12 三态呈报（核验/升级窗口只读）：同 / 本机已改 / 包侧更新 / 双边已改。
    判据=装时基线（installed_sha8）分别与「盘上现状」「包内现状」比差。"""
    fp = _hook_fingerprints_path()
    if not os.path.isfile(fp):
        print("ℹ️ 钩子内容指纹基线不存在（旧装机）——下次 --deploy/安装 自动生成（P12）")
        return
    try:
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        print("⚠️ 指纹基线不可读（不阻断核验）")
        return
    same = mine = theirs = both = 0
    names = {"mine": [], "theirs": [], "both": []}
    for subpath, rec in sorted(data.items()):
        landing = os.path.join(HOOKS_ROOT, subpath)
        src = os.path.join(PKG, rec.get("srcdir", "references/scripts"), os.path.basename(subpath))
        cur_l, cur_p = _sha8(landing), _sha8(src)
        base_i, base_p = rec.get("installed_sha8", "-"), rec.get("pkg_sha8", "-")
        # ⛔不用 cur_l==cur_p 判「同」：landing 经 _fill 占位符本地化，与包内原文恒差
        #    （P12 沙箱实测 32 件假报「包侧更新」的病根）。判据=各自 vs 装时基线的位移。
        l_moved = cur_l != base_i
        p_moved = cur_p != base_p
        if not l_moved and not p_moved:
            same += 1
            continue
        if l_moved and p_moved:
            both += 1; names["both"].append(subpath)
        elif l_moved:
            mine += 1; names["mine"].append(subpath)
        else:
            theirs += 1; names["theirs"].append(subpath)
    print("钩子内容三态（vs 装时基线·P12）：状态未变 %d ｜ 本机已改 %d ｜ 包侧更新可达 %d ｜ 双边已改 %d"
          % (same, mine, theirs, both))
    for k, lab in (("mine", "本机已改（重装⛔不覆盖你的件·要收包侧新修须手工合并）"),
                   ("theirs", "包侧更新（盘上仍是装时态·重装即到达新版）"),
                   ("both", "双边已改（须人判合并）")):
        if names[k]:
            show = ", ".join(names[k][:8]) + ("…" if len(names[k]) > 8 else "")
            print("   · %s：%d 件：%s" % (lab, len(names[k]), show))


def _sweep_ghost_mc(mc, home, dry=False):
    """装后清扫：把历史版本误建的字面 `[记忆共享中心]` 幽灵目录移到备份（⛔永不删除·tiger①存量根治 2026-10-20）。

    判据（极保守）：
      - 只认字面名 `[记忆共享中心]` 的**目录**，扫描 HOME 根与 MC 根；
      - 处置=**移动**到 `<MC>/.install/ghost-sweep/<name>-<ts>/`（可逆·用户可自行还原）；
      - 移动失败只告警不中止安装（不因清扫失败坏掉主流程）；
      - 合法数据零风险：整个目录原样搬走，不做任何删除/筛选。
    """
    import time as _t
    name = "[记忆共享中心]"
    roots = [home]
    try:
        if mc and os.path.abspath(mc) != os.path.abspath(home):
            roots.append(mc)
    except Exception:
        pass
    dest_root = os.path.join(mc, ".install", "ghost-sweep") if mc else os.path.join(home, ".install", "ghost-sweep")
    ts = _t.strftime("%Y%m%d_%H%M%S")
    found = 0
    for root in roots:
        cand = os.path.join(root, name)
        if not os.path.isdir(cand):
            continue
        found += 1
        if dry:
            print("[dry-run] 装后清扫将移动: %s → %s" % (cand, dest_root))
            continue
        _root_tag = "home" if os.path.abspath(root) == os.path.abspath(home) else "mc"
        dest = os.path.join(dest_root, "%s-%s-%s" % (name, ts, _root_tag))
        try:
            os.makedirs(dest_root, exist_ok=True)
            shutil.move(cand, dest)
            print("🧹 装后清扫：已移动幽灵目录 %s → %s（可逆·⛔未删除）" % (cand, dest))
        except Exception as e:
            print("⚠️ 装后清扫：%s 移动失败（%r）——保留原位，请手动处理" % (cand, e))
    if not found and not dry:
        print("🧹 装后清扫：未发现字面占位符幽灵目录（干净）")
    return 0


def deploy_skills(mc, dry=False, only=None):
    """Skill 面程序化部署腿（2026-10-11 批次8·T16 根因 + D1 收编三件之二）。

    病根：安装器原先对 Skill 面**只数不装**（detect_assets 里 skill_count），真正落盘
    靠 INSTALL/steps 里的 `cp -r` + 手工 perl 替换 ⇒ 745 处占位符的本地化交给人/端 AI
    逐次执行。真机 Windows 演练（verify.sh 检装后产物）实测 12 件残留未替换 =
    端用户拿到死链。这是"人工步骤被当成机制"的典型：它不是失败得响亮，而是漏得安静。

    本腿做三件事（一次落地 D1 提的『留存/损失清单/探针』里的前两件）：
      ①逐件复制 references/skills/<name> → <MC>/技能配置/<name>，复制后对每个落盘件
        跑 _fill（含 .ps1/.plist/.template——TEXT_EXT 已扩，见 A2/E3 根治）；
      ②覆盖前逐件比对：目标已存在且 md5 不同 ⇒ 记入 `.install/upgrade-losses.md`
        （路径+双方 md5+备份去向），终端显形条数；⛔不阻断（升级授权在用户），但必须留痕；
      ③被覆盖件先备份进 <MC>/记忆琥珀/升级前备份_<ts>/<skill>/（命名与 rollback 的
        BACKUP_KINDS 对齐由 rollback 腿负责，本处只写不吞）。
    幂等：内容与包内件一致且无占位符残留 ⇒ 计入"跳过"，不重写不刷 mtime。
    """
    src_root = os.path.join(PKG, "references", "skills")
    dst_root = os.path.join(mc, "技能配置")
    if not os.path.isdir(src_root):
        print("!! 包内 references/skills 缺失（应报发布缺陷）：%s" % src_root)
        return 0, 0, 0
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = os.path.join(mc, "记忆琥珀", "升级前备份_" + ts)
    losses, n_deploy, n_skip = [], 0, 0
    _PATHS_CACHE = _read_install_paths(mc)  # F4：一次读取·全程复用
    names = sorted(os.listdir(src_root))
    if only:
        names = [n for n in names if n in only]
    for name in names:
        s_dir = os.path.join(src_root, name)
        if not os.path.isdir(s_dir) or not os.path.isfile(os.path.join(s_dir, "SKILL.md")):
            continue
        d_dir = os.path.join(dst_root, name)
        for cur, _dirs, files in os.walk(s_dir):
            rel = os.path.relpath(cur, s_dir)
            for fn in files:
                sp = os.path.join(cur, fn)
                rp = os.path.normpath(os.path.join(name, rel, fn)) if rel != "." else os.path.join(name, fn)
                dp = os.path.join(dst_root, rp)
                body = None
                try:
                    with open(sp, "r", encoding="utf-8") as f:
                        body = _fill_text(f.read(), mc, os.path.splitext(fn)[1], _PATHS_CACHE)
                except (UnicodeDecodeError, OSError):
                    body = None                      # 二进制件：原样复制
                if os.path.isfile(dp):
                    same = False
                    if body is not None:
                        try:
                            same = hashlib.md5(body.encode("utf-8")).hexdigest() == _md5(pathlib.Path(dp))
                        except Exception:
                            same = False
                    else:
                        same = _md5(pathlib.Path(sp)) == _md5(pathlib.Path(dp))
                    if same:
                        n_skip += 1
                        continue
                    losses.append(rp)
                    if not dry:
                        bp = os.path.join(backup_root, rp)
                        os.makedirs(os.path.dirname(bp), exist_ok=True)
                        try:
                            shutil.copy2(dp, bp)
                        except OSError:
                            pass
                if dry:
                    n_deploy += 1
                    continue
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                if body is None:
                    shutil.copy2(sp, dp)
                else:
                    tmp = dp + ".tmp-deployskills"
                    with open(tmp, "w", encoding="utf-8") as f:
                        f.write(body)
                    os.replace(tmp, dp)
                n_deploy += 1
    if not dry and losses:
        os.makedirs(os.path.join(mc, ".install"), exist_ok=True)
        lp = os.path.join(mc, ".install", "upgrade-losses.md")
        with open(lp, "w", encoding="utf-8") as f:
            f.write("# 升级将被覆盖的本机改动件（程序化部署腿生成·⛔静默覆盖）\n\n"
                    "备份去向：`%s`\n\n| 件 | 本机 md5 | 包内 md5 |\n|---|---|---|\n" % backup_root)
            for rp in losses:
                f.write("| %s | %s | %s |\n" % (rp, _md5(pathlib.Path(os.path.join(dst_root, rp))),
                                                 "-（见备份）"))
        print("⚠️ [损失清单] 本机改动件 %d 件将被包内版覆盖：.install/upgrade-losses.md（备份 %s）"
              % (len(losses), backup_root))
    return n_deploy, n_skip, len(losses)


def deploy_script_center(mc, dry=False):
    """①生成脚本中心（用户拥有的完整脚本副本）。

    🔴 **2026-10-03 补第三拷贝源 `references/digital-twin/devtools`**（hermes 端缺口根治）：

    **病根**：`runtime_paths` 的 `devtools` 键 → `<MC>/脚本中心`（安装器写死的落点），
    而 **16 个插件的全部脚本引用都走 `rp("devtools")`**。
    分身件（`doenglingz_inject_prompt.py` / `tsl_tree_hook.py` / 三只读守卫 …）
    却只由 `deploy_digital_twin` 部署到 `<MC>/数字分身/devtools/` ⇒ **两个落点**。

    ⇒ 端用户机上：`os.path.join(rp("devtools"), "doenglingz_inject_prompt.py")`
    指向一个**不存在**的文件 ⇒ `_INJECT` 悬空 ⇒ `pre_llm_call` 注入链**静默空转**
    （插件自己 `except: return None` ⇒ 不报错·不阻断·童灵恒驻核不上岗）。
    ⛔ 这正是 12 号协议 §5.7「作者机 100% 测不出」同族病：作者机 `脚本中心/`
    是开发工具的历史镜像 ⇒ 件都在 ⇒ 本机全绿。

    **修法选型（两候选）**：

    | 方案 | 动作 | 代价 |
    |:---|:---|:---|
    | **B1 部署面同步**（本函数·采用） | 分身件同源副本也落 `<MC>/脚本中心/` | 一处改动·零插件改动 |
    | B2 插件引用根改指 | 插件改走 `rp("twin")+"devtools"` | 改 N 个插件·**引入第二个取件面** |

    选 B1 的理由：`devtools` 键是**插件唯一取件面**（声明层单一真源），
    副本必须就位——**不是给键加别名**。
    `数字分身/devtools/` 那份**继续保留**（`deploy_hooks` 的 ROSTER 钩子链从那里拷，
    职责不同·不废）；两份同名同源 ⇒ sha 相同 ⇒ `devtools_single_source_guard`
    判据③不报分叉。

    """
    dst_root = os.path.join(mc, "脚本中心")
    n = 0
    # 🔴 2026-10-07 冲突显形化（皮叔「彻底根治」·病根＝平铺覆盖静默拿旧版）：
    #   三目录平铺到同一 dst_root ⇒ 同名文件**后复制者覆盖先复制者**，
    #   而遍历序 ≠ 内容新旧 ⇒ 端用户静默拿到滞后副本。
    #   实测铁证：hook_protocol.py 的 v0.2 修复标记在 dt-devtools 侧缺失，
    #   而 dt-devtools 遍历序最后 ⇒ 恒赢 ⇒ 端用户拿无修复版。
    #   修法：**同名异内容即显式失败**——⛔ 不静默覆盖、⛔ 不自动挑边
    #   （挑边＝猜；猜错＝把新版丢掉·比报错更坏）。
    #   判据＝_deident_norm 归一（路径形态差异不算冲突·脱敏本就如此）。
    _seen = {}         # name -> (dir, normalized_text)
    _conflicts = []    # [(name, first_dir, dup_dir)]
    for d in ("references/scripts", "references/hooks",
              "references/digital-twin/devtools"):   # ⛔ 第三源·见 docstring
        src_dir = os.path.join(PKG, d)
        if not os.path.isdir(src_dir):
            continue
        if not dry:
            os.makedirs(dst_root, exist_ok=True)
        for name in sorted(os.listdir(src_dir)):
            src = os.path.join(src_dir, name)
            if not os.path.isfile(src):
                continue
            try:
                with open(src, encoding="utf-8", errors="replace") as f:
                    _norm = _deident_norm(f.read())
            except Exception:
                _norm = None
            if _norm is not None and name in _seen:
                _prev = _seen[name][1]
                if _prev is not None and _prev != _norm:
                    _conflicts.append((name, _seen[name][0], d))
            elif _norm is not None:
                _seen[name] = (d, _norm)
            _copy(src, os.path.join(dst_root, name), dry)
            n += 1
    if _conflicts:
        # Fail-Loud：把「静默覆盖」变成「装包当场报错」——端用户负担＝装不上且看见原因，
        # 而非装上了却在几周后表现为「功能时灵时不灵」。
        # ⚠️ dry-run 只报告不阻断（dry-run 语义＝"看会发生什么"·阻断留给真实执行）。
        # ⚠️ 本函数返回契约是**单个 int**（main() L1932 按 int 收）⇒ 不改返回类型，
        #    改用模块级标志 _PKG_CONFLICTS，由 main() 统一 exit 1。
        global _PKG_CONFLICTS
        _PKG_CONFLICTS = list(_conflicts)
        print("!! 脚本中心同名冲突 %d 处（⛔ 不自动挑边·不静默覆盖·%s）："
              % (len(_conflicts),
                 "即将中止安装" if (not dry and os.environ.get("_BLUOLUO_PKG_CONFLICT_STRICT", "1") == "1")
                 else "仅报告·继续安装"))
        for name, a, b in _conflicts[:12]:
            print("   - %s：%s ≠ %s" % (name, a, b))
        if len(_conflicts) > 12:
            print("   ...及另外 %d 处" % (len(_conflicts) - 12))
        print("!! 修法：删掉滞后副本（三目录本应同源），或补 manifest 登记声明差异是端变体。")
        print("!! 审计工具：开发工具/buluotuo-release-sync/pkg_conflict_audit.py")
        # 硬阻断：开关打开且非 dry-run 时**在函数内**中止——
        #   放main() 里会漏（本函数可被单独调用·实测开关无效）。
        #   ✅ 默认开（2026-10-07 步4收口·QoderCN 清账完成：三目录 268 同名件 raw 全归一·audit --strict rc=0·strict 实跑 808 件 0 冲突）。
        #   逃生口：_BLUOLUO_PKG_CONFLICT_STRICT=0 显式关（仅供清障调试·⛔端用户常态不该用）。
        if not dry and os.environ.get("_BLUOLUO_PKG_CONFLICT_STRICT", "1") == "1":
            print("!! 安装中止：%d 处同名异内容未声明留哪份 —— "
                  "端用户装到未声明的版本比装不上更坏。" % len(_conflicts))
            raise SystemExit(1)
    # ③ 知识联邦引擎-min（卡生产引擎·真源独立部署 → <MC>/知识联邦引擎/·2026-10-03 从脚本中心下独立）
    #    边界确认：min版=端用户运行必需的最小集（2026-10-10 腿F案后 16 件·计数以目录实盘为准：
    #    原9件=向量构建/概念提取/碰撞扫描/阅读状态推导/索引重建/源哈希/卡片元数据同步+2环境路径助手；
    #    补收7件=SKILL.md 引用却未随包的碰撞闭环承诺资产（sync_collision_queue/lint_collision_card/
    #    concept_projection/scan_card_citations/cross_type_collision_scan/scan_citation_candidates/concept_coverage_stats）；
    #    （2026-10-07 你裁决：模型压缩件 quantize_export 撤出对外包·作者自用；量化识别逻辑保留在 build/search 内·仅产物存在时生效）
    #    完整版含作者侧运营数据（cache/logs/vectors/calibration 等）→ ⛔不入包。
    #    ⚠️ route_table.json 例外(2026-10-19 Q1 归正)：非运营数据，是 search_kb 引擎根
    #      **功能判据**(search_kb L88 靠"目录含 route_table.json"选根·缺则语义层降级 BM25)，
    #      V2.2.4 审计#1 判定为分发漏件已补入包·勿再按旧口径当"运营数据"删掉。
    #    vectors/INDEX 属派生产物(用户机 build_kb_vectors/regen 自建)·仍 ⛔ 不入包(隐私+无用)。
    kb_dst = os.path.join(mc, "知识联邦引擎")
    min_src = os.path.join(PKG, "references", "知识联邦引擎-min")
    if os.path.isdir(min_src):
        for root, dirs, files in os.walk(min_src):
            rel = os.path.relpath(root, min_src)
            tdir = kb_dst if rel == "." else os.path.join(kb_dst, rel)
            if not dry:
                os.makedirs(tdir, exist_ok=True)
            for name in sorted(files):
                _copy(os.path.join(root, name), os.path.join(tdir, name), dry)
                n += 1
        if not dry:
            for root, _dn, fs in os.walk(kb_dst):
                for name in fs:
                    if name.endswith(TEXT_EXT):
                        _fill(os.path.join(root, name), mc)
    # 占位符替换（脚本中心里的副本·全层级遍历）
    if not dry:
        for root, dirs, files in os.walk(dst_root):
            for name in files:
                p = os.path.join(root, name)
                if name.endswith(TEXT_EXT):
                    _fill(p, mc)
    return n


RULE_DATA = ["rule_triggers.yaml", "rule_conflict_signals.yaml", "match_coverage_baseline.json"]  # v2.1.3 腿F清账轮+匹配面存量账（match_coverage_check.py --check 消费·装机即有豁免基线，缺则 fail-closed exit2）
"""规则层运行时数据：铁律硬墙（rule_fragment_inject / rule_three_layer_guard）
从 `<MC>/记忆规则/` 读这些文件——缺则硬墙**静默零注入**（实测：rc=0、无输出、无报错）
或缺冲突信号（退化为内置默认组）。包内源在 references/scripts/，安装时必须落到 `<MC>/记忆规则/`。"""


def install_rule_data(mc, dry=False):
    """把规则层运行时数据装到 <MC>/记忆规则/。

    ⚠️ 2026-10-09 缺陷②根治（布洛陀2.1.0上游反馈·本机端=唯一主源，安装包=下游映射）：
    原语义＝无条件幂等覆盖，会把终端**手工维护**的 rule_triggers.yaml 真源
    冲成包内编译产物（实证：40 条→30 条，032-040 触发规格全丢＝预注入硬墙缺位）。
    新语义：覆盖前查目标文件头（前 8 行）的外部维护声明——命中「本机不引入 / 手工维护+⛔」
    任一标记 ⇒ [SKIP] 保留用户版并显形告警，⛔不静默覆盖；未命中 ⇒ 维持幂等覆盖（标准流）。
    （配套：rule_triggers.yaml / rule_conflict_signals.yaml 已入 conffiles 三路比较册。）"""
    done = []
    for name in RULE_DATA:
        src = os.path.join(PKG, "references/scripts", name)
        if not os.path.isfile(src):
            continue
        dst_dir = os.path.join(mc, "记忆规则")
        if not dry:
            os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, name)
        # 缺陷②根治：外部维护声明检测（标记判据取自用户文件头，如
        #   「# ⛔ 本机不引入 gen_rule_triggers.py 编译器」/「手工维护」）
        _maint = False
        if os.path.isfile(dst):
            try:
                _head = "\n".join(open(dst, encoding="utf-8").read(4096).splitlines()[:8])
                _maint = ("本机不引入" in _head) or ("手工维护" in _head and "⛔" in _head)
            except Exception:
                _maint = False
        if _maint:
            print("     └ [SKIP] %s：目标文件头声明外部/手工维护——保留你的版本，不覆盖（缺陷②根治·本机=主源）" % name)
            done.append(name + "(SKIP·保留本机版)")
            continue
        _copy(src, dst, dry)
        if not dry:
            _fill(dst, mc)
        done.append(name)
    return done


RULE_FILES = ["用户基本规则-铁律版.md", "用户基本规则-摘要版.md", "用户基本规则-详解存档版.md"]
# C14（2026-10-15）：摘要版三表的 [Qn·答案待注入]/[Qn·规则待派生] 是 step5 注入位，
# 装后必然 ≠模板——重跑链A 不得判"用户手改"。模式与模板占位格同源（C08 定稿格式）。
_SUMMARY_FILL_RX = r"\[Q\d+·(?:答案待注入|规则待派生)\]"
"""三层规则文件：铁律硬墙的**注入源**（rule_fragment_inject 读铁律版做预注入；
rule_three_layer_guard 读三层做版本一致性 + 冲突路由校验）。

安装语义＝**断章增量**（2026-10-02 断章引擎落地·宪法 §2.0 C1-C7）：
⛔ 不再幂等覆盖——用户在铁律版里加的条目 / 调过的顺序 / 改过的措辞**必须原样保留**，
布洛陀只写自己那一个标记段（`<!-- BULUOTUO:BEGIN rules.xxx -->`）。
升级时只替换段内正文；段外一字节不动；段内被用户手改 ⇒ 报冲突不自动覆盖。
（历史语义：幂等覆盖·见 .bak-20261002-premerge/install_scripts.py）"""


def _load_merge_engine():
    """载入断章增量引擎（references/scripts/buluotuo_merge.py）。

    ⚠️ 用 importlib 按路径载入，不加进 sys.path：⛔ 免得把整个
    references/scripts/ 目录暴露成可导入包（那里全是钩子脚本）。
    """
    import importlib.util
    mpath = os.path.join(PKG, "references", "scripts", "buluotuo_merge.py")
    if not os.path.isfile(mpath):
        raise RuntimeError("断章引擎缺失：%s（安装中止·⛔不回退到覆盖）" % mpath)
    spec = importlib.util.spec_from_file_location("buluotuo_merge", mpath)
    if spec is None or getattr(spec, "loader", None) is None:
        raise RuntimeError("断章引擎无法载入：%s（安装中止·⛔不回退到覆盖）" % mpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rule_sid(name):
    """规则文件名 → 段 id。`用户基本规则-铁律版.md` ⇒ `rules.tielu`。

    ⚠️ 段 id 必须**稳定**：一旦发出去就不能改，否则升级时找不到旧段
    ⇒ 会当成"文件里没有本段" ⇒ 追加第二个半截段（实测踩过标记不配对）。
    """
    return {
        "用户基本规则-铁律版.md": "rules.tielu",
        "用户基本规则-摘要版.md": "rules.summary",
        "用户基本规则-详解存档版.md": "rules.detail",
    }.get(name, "rules." + name.replace(".md", ""))


def _rule_version(text):
    """抽三层规则文件的版本号（正文区 `> 版本：v8.28 | 创建：…`）。

    ✅ 返回如 "v8.28"；⛔ 抽不到返回 None（调用方据此走完整合并·⛔ 不假设一致）。
    ⚠️ 版本号在**正文区不在 frontmatter**——与铁律版「三层共享同一版本号」纪律配套：
       改任一层 ⇒ 三层版本号一起升 ⇒ 比对时三件必须一起看。
    """
    import re as _re
    m = _re.search(r"^>\s*版本[：:]\s*(v[\d.]+)", text, _re.M)
    return m.group(1) if m else None


_TIELU_HEAD_RE = re.compile(r"^###\s*铁律-(\d{3})", re.M)
_HEAD_STOP_RE = re.compile(r"^#{2,3}\s", re.M)


def _norm_cmp(s):
    """条目正文归一（与断章引擎 _cmp_norm 同口径：删纯空行·rstrip·不动缩进）。"""
    return "\n".join(l.rstrip() for l in (s or "").splitlines() if l.strip())


def _rule_items(text):
    """全文解析为 {编号: 归一正文}。条目= `^### 铁律-NNN` 行至下一个 ##/### 标题行。"""
    items = {}
    for m in _TIELU_HEAD_RE.finditer(text):
        nxt = _HEAD_STOP_RE.search(text, m.end())
        end = nxt.start() if nxt else len(text)
        items[int(m.group(1))] = _norm_cmp(text[m.end():end])
    return items


def _tielu_precheck(cur_text, new_body):
    """缺陷①根治（2026-10-09·布洛陀2.1.0上游反馈）：铁律版无标记段时的号位/等价预检。

    病根：断章引擎 C5「文件已存在且无段⇒追加文末」是盲写——终端铁律版若还是
    幂等覆盖时代的 plain 文件（内容≈上游但编号/裁剪不同），首升断章包必然整file
    双份（号位错开者出现「铁律-013 两次且语义冲突」级事故；标准用户同号双份同样坏）。
    判据（本机=唯一主源，包是下游映射，⛔包侧不抢写主源号位空间）：
      上游条 vs 本机条 → 同号等值 / 换号等价 / 同号异文(冲突) / 本机没有(新增)。
    除「任一侧无铁律结构(本判据不适用)」外，任何非全等价 ⇒ 不写、只显形
    （与 C7 报告不裁决哲学同构；上游新增条目的归属由主源侧裁决，⛔不自动追加到本机上界之后）。
    返回 (verdict, lines)：verdict ∈ SAFE / EQUIV / CONFLICT
    """
    cur_items = _rule_items(cur_text)
    new_items = _rule_items(new_body)
    if not new_items or not cur_items:
        return "SAFE", []                      # 任一侧无铁律结构 ⇒ 交引擎常规路径
    norm2num = {}
    for k, v in cur_items.items():
        norm2num.setdefault(v, k)
    n_equiv = n_conflict = n_new = 0
    lines = []
    for num in sorted(new_items):
        if num in cur_items and new_items[num] == cur_items[num]:
            n_equiv += 1
            lines.append("铁律-%03d：同号等值（重复注入将双份）" % num)
        elif new_items[num] in norm2num:
            n_equiv += 1
            lines.append("铁律-%03d ↔ 本机铁律-%03d：换号等价（内容已在·跳过）" % (num, norm2num[new_items[num]]))
        elif num in cur_items:
            n_conflict += 1
            lines.append("铁律-%03d：同号异文（号位冲突·须人工裁决）⚠️" % num)
        else:
            n_new += 1
            lines.append("铁律-%03d：上游新增·本机没有（归主源侧裁决是否吸收，包不代写）" % num)
    if n_conflict or n_new:
        return "CONFLICT", lines
    if n_equiv == len(new_items):
        return "EQUIV", lines
    return "CONFLICT", lines


def install_rule_files(mc, dry=False):
    """把三层规则文件装到 <MC>/记忆规则/（**断章增量**·⛔ 不覆盖用户改动）。

    返回 [(文件名, status, msg)]，status ∈
    CREATED / UPDATED / UNCHANGED / CONFLICT。
    ⚠️ CONFLICT 不静默吞掉：调用方须把它排印给用户（C7·报告不裁决）。
    """
    bm = _load_merge_engine()
    src_dir = os.path.join(PKG, "references/templates")
    dst_dir = os.path.join(mc, "记忆规则")
    backup_dir = os.path.join(mc, "记忆琥珀", "安装前备份")
    done = []
    for name in RULE_FILES:
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        if not dry:
            os.makedirs(dst_dir, exist_ok=True)
        with open(src, "r", encoding="utf-8") as f:
            body = _fill_text(f.read(), mc)
        dst = os.path.join(dst_dir, name)
        sid = _rule_sid(name)
        # 模板原文同样过一遍占位符替换，否则冲突判定会误报（用户文件是替换后的）
        with open(src, "r", encoding="utf-8") as f:
            tpl = _fill_text(f.read(), mc)
        # ── 版本号参与判定说明（2026-10-03·你判据「和用户现有版本号不一致就是有差异」）
        #   ⚠️ **版本号只作说明·⛔ 不作跳过条件**——首版曾写成"版本一致即跳过"，
        #      实测抓到回归：用户在段内改了内容但版本号没变时，预筛直接 UNCHANGED
        #      ⇒ **用户改动被静默忽略**（与增量保护初衷相反）。已回退为"仍走段比对·版本号进 msg"。
        #   ✅ 版本号的真实价值：① 告诉用户「包内 vX → 你的是 vY」② 段级 CONFLICT 时提供上下文。
        _v_new = _rule_version(tpl)
        _v_old = _rule_version(open(dst, encoding="utf-8").read()) if os.path.isfile(dst) else None
        _vtag = ""
        if _v_new and _v_old:
            _vtag = "版本 %s→%s" % (_v_old, _v_new) if _v_new != _v_old else "版本一致 %s" % _v_new
        # ── 缺陷①根治（2026-10-09）：铁律版·无标记段·已有铁律结构 ⇒ 追加前必过号位/等价预检 ──
        if sid == "rules.tielu" and os.path.isfile(dst):
            _cur0 = open(dst, encoding="utf-8").read()
            if bm.BEGIN_TMPL.format(sid=sid) not in _cur0:
                _pv, _plines = _tielu_precheck(_cur0, body)
                if _pv != "SAFE":
                    for _l in _plines:
                        print("     ├ [号位预检] %s" % _l)
                    _pmsg = ("上游条目与本机全等价——本机已有全部内容，⛔不重复注入（缺陷①预检）"
                             if _pv == "EQUIV" else
                             "存在号位冲突或上游新增——⛔未写入你的文件（本机=主源·包不代写·请人工裁决）")
                    done.append((name, "PRECHECK_SKIP", _pmsg + ("·" + _vtag if _vtag else "")))
                    continue
        # ── F5 根治（2026-10-17·10-14 D3 复发）：用户盘若是 5d-8 裸拷（占位符未本地化），
        #    旧逻辑拿「填充后的模板 tpl」比「裸拷的用户文件」⇒ **字节完全相同也报
        #    "已被用户修改"**（沙箱实测：铁律版 md5 双侧一致仍判 CONFLICT）。
        #    纯占位符差异 = 良性本地化修复：就地填充，⛔不判冲突，⛔不当用户改动。
        if os.path.isfile(dst) and not dry:
            _cur = open(dst, encoding="utf-8").read()
            if _cur != tpl and _fill_text(_cur, mc) == tpl:
                with open(dst, "w", encoding="utf-8") as _wf:
                    _wf.write(tpl)
                done.append((name, "LOCALIZED",
                             "裸拷占位符未本地化·已就地填充（良性修复·非用户改动·不判冲突）"))
                continue
        try:
            ok, st, msg = bm.upsert_file_body(
                dst, sid, body,
                template_full=tpl,
                inject_exempt_re=(_SUMMARY_FILL_RX if name == "用户基本规则-摘要版.md" else None),
                do_backup=not dry,
                backup_dir=backup_dir,
                dry=dry,
            )
        except bm.MergeError as e:
            done.append((name, "MERGE_ERROR", str(e)))
            continue
        if not ok:                      # CONFLICT
            done.append((name, st, (msg + "·" + _vtag) if _vtag else msg))
            continue
        done.append((name, st, (msg + "·" + _vtag) if _vtag else msg))
    # ── 缺陷③根治（2026-10-09）：详解存档旧名/权威名双名并存显形（改名迁移不静默）──
    _old_nm = os.path.join(dst_dir, "用户基本规则-详解存档.md")
    _new_nm = os.path.join(dst_dir, "用户基本规则-详解存档版.md")
    if os.path.isfile(_old_nm) and os.path.isfile(_new_nm):
        print("   ⚠️ [双名并存] 记忆规则/ 下「用户基本规则-详解存档.md」(旧名)与「用户基本规则-详解存档版.md」(权威名)同时存在："
              "守卫/注入以权威名为准；旧名若含权威名没有的增量，请先并入权威名，再把旧名移入 记忆琥珀/ 归档（⛔不静默处置）")
    return done


def deploy_hooks(dry=False):
    """②部署钩子副本：ROSTER 表驱动（主件 + 同目录依赖）。
    P12 根治（作者 2026-10-19 指令·愿景最优解）：覆盖腿写侧保护——
    盘上件 ≠ 装时基线（=本机被人工动过）⇒ ⛔静默覆写，跳过并显形呈报；
    包侧新修且盘上件仍是装时态 ⇒ 照常到达（升级通道不关闭）；
    无基线（首装/历史装机）⇒ 按旧行为落件并建档。裁决入口=--verify 三态呈报。"""
    deployed, missing, protected = [], [], []
    fp = _hook_fingerprints_path()
    base = {}
    if os.path.isfile(fp):
        try:
            with open(fp, encoding="utf-8") as f:
                base = json.load(f)
        except Exception as e:
            try:
                shutil.copy2(fp, fp + ".bad")
            except OSError:
                pass
            print("⚠️ hook_fingerprints.json 存在但不可解析(%s)——本轮回退无基线行为（全量落件·改件无保护），坏基线已存证 %s.bad（F2）" % (e, fp))
            base = {}
    landed = []  # (rel, srcdir)：全量落地件（主件+依赖），供指纹基线建档
    for ev, loc, srcdir, main, deps in ROSTER:
        dst_dir = HOOKS_ROOT if loc == "." else os.path.join(HOOKS_ROOT, loc)
        for fname in [main] + list(deps):
            src = os.path.join(PKG, srcdir, fname)
            if not _status(src):
                missing.append("%s/%s" % (srcdir, fname))
                continue
            rel = "%s/%s" % (loc, fname) if loc != "." else fname
            dst = os.path.join(dst_dir, fname)
            rec = base.get(rel) if base else None
            if rec and os.path.isfile(dst) and not dry:
                cur = _sha8(dst)
                if cur not in (rec.get("installed_sha8"), rec.get("pkg_sha8"), "-"):
                    protected.append(rel)
                    continue  # 本机已改：保护不覆写，且⛔进本轮基线重写清单（F1：否则盘上改后哈希污染参照系，二次重装失去保护+三态谎报"未变"）
            _copy(src, dst, dry)
            if not dry:
                _fill(os.path.join(dst_dir, fname), MC_PATH)
            landed.append((rel, srcdir))
        deployed.append((ev, "%s/%s" % (loc, main) if loc != "." else main, srcdir, main))
    global _LANDED_INDEX
    _LANDED_INDEX = landed
    if protected:
        print("🛡️ 本机改动保护（P12 写侧根治）：%d 件未被包版覆盖：%s" % (
            len(protected), ", ".join(protected[:8]) + ("…" if len(protected) > 8 else "")))
        print("   要收包侧新版：手工合并，或删除该件后重装即回包版；差异明细见 --verify 三态呈报。")
    return deployed, missing


def _pyexe_nt():
    """Windows 侧 python 实体（原逻辑不变，抽出供 _hook_command 与迁移比对共用）。"""
    cands = glob.glob(os.path.join(
        os.path.expanduser("~"), ".workbuddy", "binaries", "python",
        "versions", "*", "python.exe"))
    return cands[0].replace("\\", "/") if cands else "python"


def _interp_for(subpath):
    """按扩展名选解释器（A3 根治·2026-10-10 刚叔 V2.1.0 提请单）。

    病根：原 `_hook_command` 无条件把钩子件交给 python——Windows 拼成
    `python.exe run_registry_guards.sh`、mac/Linux 拼成 `python3 同一件`，两者都是
    SyntaxError，Stop 守卫链入口装机即哑（ROSTER 51 件 .py + 1 件 .sh，.sh 必死）。
    判据=凡注册命令一律按扩展名分派；未知扩展名回落 bash（⛔不回落 python——
    python 能跑的件由 .py 显式表达，回落 python 等于把"不知道"当"能跑"）。
    """
    ext = subpath.rsplit(".", 1)[-1].lower() if "." in subpath.rsplit("/", 1)[-1] else ""
    # Windows 优先走同名 .ps1 承载（2026-10-11 批次6 根治）：.sh 交给 bash 属"环境推断"，
    # 包内 step6 明文禁止该推断（Git Bash 的 $ 展开与原生 bash 不同）。故只要 HOOKS_ROOT
    # 下存在同名 .ps1，Windows 就用 powershell 跑它——把"能不能跑"从假设换成有承载。
    if os.name == "nt" and ext == "sh":
        twin = os.path.join(HOOKS_ROOT, subpath.rsplit("/", 1)[-1][:-3] + ".ps1")
        if os.path.isfile(twin):
            return ("powershell -NoProfile -ExecutionPolicy Bypass -File")
    if ext == "py":
        return '"%s"' % _pyexe_nt() if os.name == "nt" else "python3"
    if ext == "ps1":
        return ("powershell -NoProfile -ExecutionPolicy Bypass -File" if os.name == "nt"
                else "pwsh -NoProfile -ExecutionPolicy Bypass -File")
    return "bash"


def _hook_command(subpath):
    """构造 settings.json 里要写的命令行（按平台 × 按脚本类型双维分派）。"""
    p = os.path.join(HOOKS_ROOT, subpath).replace("\\", "/")
    interp = _interp_for(subpath)
    if os.name == "nt":
        return ('BULUOTUO_RUNTIME_PATHS="%s" MSYS_NO_PATHCONV=1 %s "%s"'
                % ((os.path.join(_CFG_ROOT_ABS, "doenglingz", "runtime_paths.json")).replace("\\", "/"), interp, p))
    cmd = "%s %s" % (interp, p)
    # v2.0.1 多端（2026-09-30 L3审计根治）：非WB端注册分身运行时钩子时注入配置根 env——
    # 缺省回 ~/.workbuddy=state/采样台账落点错位；DOENGLINGZ_CONFIG_DIR 由本命令显式给定。
    if _PLATFORM_ID not in ("", "workbuddy") and os.path.basename(subpath).startswith(("doenglingz_", "twin_")):
        cmd = "DOENGLINGZ_CONFIG_DIR=%s %s" % (_CFG_ROOT_ABS, cmd)
    # E2E⑤空载根治(2026-10-06·条文47装机面·逐件取证实锤)：hooks 副本 rp.py 无同邻声明json——
    #   声明唯一写点=<配置根>/doenglingz/runtime_paths.json 不复制不软链(单源)，注册时走 rp 解析链第1档 env 注入；
    #   跨平台⛔symlink 依赖·未用 env 的件零副作用。
    cmd = 'BULUOTUO_RUNTIME_PATHS="%s" %s' % (
        (os.path.join(_CFG_ROOT_ABS, "doenglingz", "runtime_paths.json")).replace("\\", "/"), cmd)
    return cmd


def write_guard_baseline(deployed, dry=False):
    """C4-D 派生写入腿：期望基线 hook_baseline.json 生成（capability guard_baseline_seed=="py" 才写）。
    期望集=deploy_hooks 全量推导（⛔非注册回声=非"装了什么"而是"该装什么"）；
    调用侧已保证包内缺失(missing)非空时不调=装机器缺陷不算到用户头上(GIGO闸)。"""
    try:
        cap_p = os.path.join(PKG, "adapters", _PLATFORM_ID, "capability.yaml")
        seed = (load_capability(cap_p) or {}).get("guard_baseline_seed", "") if os.path.isfile(cap_p) else ""
    except Exception:
        seed = ""
    if seed != "py":
        return False
    fp = os.path.join(os.path.dirname(SETTINGS), "hook_baseline.json")
    if dry:
        print("[dry-run] 期望基线将写 → %s" % fp)
        return False
    exp = {}
    for ev, sub, _sd, _m in deployed:
        exp.setdefault(ev, []).append(__import__("os").path.basename(sub))
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(exp, f, ensure_ascii=False, indent=2)
    os.replace(tmp, fp)
    print("🧭 期望基线已写：%d 事件 %d 条 → %s" % (len(exp), sum(len(v) for v in exp.values()), fp))
    return True


def register_hooks(deployed, dry=False):
    """③注册 settings.json（幂等：已挂的按 basename 跳过）。"""
    data = {}
    if os.path.isfile(SETTINGS):
        try:
            with open(SETTINGS, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            print("!! settings.json 解析失败（未改动）：%s" % e)
            return -1, -1, -1  # P08：注册面不可用哨兵（三元组契约保持·F9）——调用侧据 [0]==-1 判非零
    hooks = data.setdefault("hooks", {})

    # 2026-10-20 反馈#1：改名 fork 的重复注册去重（同一注入钩子被官方+用户重放注册两次）。
    # 判据=**同内容副本**（用户改名只改文件名，内容不变）：候选命令脚本存在且 sha 与官方件一致
    # ⇒ 视为同一钩子，⛔不再追加第二条。⛔ 不用后缀族判定——kb_inject/doenglingz_inject 同后缀
    # 但不同职能，按族合并会漏注册（E2E 实锤：两件被判同族漏挂）。
    def _sha(p):
        try:
            import hashlib
            with open(p, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    def _same_hook_copy(lst, subpath):
        off = os.path.join(HOOKS_ROOT, subpath)
        off_sha = _sha(off)
        if not off_sha:
            return False
        for grp in lst:
            if not isinstance(grp, dict):
                continue
            for h in grp.get("hooks", []):
                cmd = (h.get("command") or "") if isinstance(h, dict) else ""
                cand = None
                _m = re.search(r'"([^"]+\.(?:py|sh|ps1))"', cmd)
                if _m:
                    cand = _m.group(1)
                else:
                    for tok in cmd.split():
                        t = tok.strip('"\'')
                        if t.endswith((".py", ".sh", ".ps1")):
                            cand = t
                            break
                if not cand:
                    continue
                candp = cand if os.path.isabs(cand) else os.path.join(HOOKS_ROOT, cand)
                if os.path.basename(candp) == os.path.basename(subpath):
                    continue
                if _sha(candp) == off_sha:
                    return True
        return False

    def find_hook(lst, basename):
        """返回首个命令体含 basename 的 hook dict（无则 None）——存在性判定与迁移共用。"""
        for grp in lst:
            if not isinstance(grp, dict):
                continue
            for h in grp.get("hooks", []):
                if isinstance(h, dict) and basename in h.get("command", ""):
                    return h
        return None

    added = skipped = migrated = 0
    for ev, sub, _sd, _m in deployed:
        arr = hooks.setdefault(ev, [])
        base = os.path.basename(sub)
        exist = find_hook(arr, base)
        if exist is None and _same_hook_copy(arr, sub):
            # 同族已挂（用户改名副本）：⛔不再追加第二条，保留用户原参数
            skipped += 1
            continue
        # 2026-10-10 十一轮修复：want 上提到公共前段——原只在 exist 分支赋值，
        #   新钩子分支引用未定义变量 ⇒ 全新机首装必崩（UnboundLocalError 实锤）。
        want = _hook_command(sub)
        if exist is not None:
            # 旧命令定向迁移（A3 根治二腿）：幂等键原为 basename，命令体一旦写错
            # （如 .sh 交给 python）就永久锁死——重装只"跳过"不"纠正"。现比对命令体，
            # 不一致即就地改写。⛔不动命令体不含该 basename 的用户自造条目。
            if exist.get("command") == want:
                skipped += 1
                continue
            if not dry:
                exist["command"] = want
            migrated += 1
            continue
        if not dry:
            arr.append({"hooks": [{"type": "command", "command": want}]})
        added += 1

    if not dry and (added or migrated):
        if os.path.isfile(SETTINGS):
            shutil.copy2(SETTINGS, SETTINGS + ".bak-installscripts")
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    if migrated:
        print("🔁 旧命令定向迁移：%d 条解释器/参数形态按类型纠正（升级不再锁死历史错写）" % migrated)
    return added, migrated, skipped


def _landing_bases(mc_):
    """落盘核共享基座清单（2026-10-06 G3·单一真源）：装机态=hooks 副本；作者机=档案树直连
    （5c/8 公共部署→脚本中心 + 各端 setup 指向真源）。文件必须真实存在于任一位——判据变宽不变松。"""
    return [HOOKS_ROOT,
            os.path.join(mc_ or "", "脚本中心"),
            os.path.join(mc_ or "", "开发工具"),
            os.path.join(mc_ or "", "开发工具", "知识联邦引擎", "scripts"),
            os.path.join(mc_ or "", "开发工具", "changelog-guard"),
            os.path.join(mc_ or "", "开发工具", "Skill路由引擎", "scripts"),
            os.path.join(mc_ or "", "数字分身", "devtools"),
            os.path.join(mc_ or "", "数字分身", "数字分身脚本"),
            os.path.join(mc_ or "", "数字分身", "scripts"),
            os.path.join(mc_ or "", "数字分身", "guards")]


def verify_deployed(mc=None, hooks_root=None, settings_path=None):


    """核对已装态：ROSTER 里每个钩子①文件是否落盘 ②settings.json 是否已注册；
    若给了记忆中心路径，再核 ③规则层运行时数据（铁律硬墙的数据源）是否就位。

    🔴 2026-10-09 作用域根治（闸6 第一遍 rc=1 的跨端真因）：
       原签名只收 `mc`，钩子落点读**全局** `HOOKS_ROOT`（L49 写死 `~/.workbuddy/hooks`）。
       `main()` 在 L1928 对 `HOOKS_ROOT` 的重新赋值是**函数局部变量**（Python 无 global 声明）
       ⇒ 非 WB 端（Hermes/Qoder CN/ZCode…）传 `--cfg-root` 时，本函数仍去查 **WB 的 hooks 目录**
       ⇒ 钩子明明装到了端自己的配置根，却报「未落盘/未注册」⇒ 假红 ⇒ 闸6 判「第一遍 rc=1」。
       修法＝把端实际的 hooks_root / settings_path **显式传参**（⛔不靠全局·作用域不跨函数传递）。
       调用方不传时回落全局（WB 旧行为不变·向后兼容）。
    """

    # ── B-min·包版本驱动 diff 自查（v3·2026-10-13·import版·提示层⛔不阻断）──
    # 治「新件入包→老端查不出缺」·基线：.install/versions.json vs component-versions.json
    # v3改用import调用(version_diff.run_diff)·不依赖subprocess(v2根因=安装器没import它)
    # ⛔不改 verify 的 rc 判定(diff落后≠装失败)·mc为空跳过·异常静默不阻断
    try:
        if mc:
            _vd_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "references", "scripts")
            if _vd_dir not in sys.path:
                sys.path.insert(0, _vd_dir)
            import version_diff as _vd
            _rep = _vd.run_diff(mc)
            if _rep and _rep.strip():
                print(_rep.rstrip())
    except Exception as _e:
        print("ℹ️ 版本 diff 自查跳过（提示层·不阻断）：%s" % _e)

    _hr = hooks_root if hooks_root else HOOKS_ROOT
    _st = settings_path if settings_path else SETTINGS
    report_hook_three_state()  # P12：核验即呈报差异三态（只读·不影响 rc 判定）
    # 与部署共用同一份 ROSTER/RULE_DATA —— 核查口径不可能与安装口径脱节。
    # 返回 0=全过；1=有缺失（明细打印到 stdout）。

    # ── 端SSOT 声明完整性自检（2026-10-06 新增·防同类复发机械拦）────────────────
    #   病根实证（本日两连击）：①autoclaw capability 缺 hooks_registration_face
    #     ⇒ 插件制端被判成 settings 面 ⇒ 去核不存在的 cli/config.json ⇒ 38 件全假红；
    #     ②qodercn/hermes 的 delivered 用行内 dict 写，而无 PyYAML 环境的 _mini_yaml
    #     认不出来 ⇒ 全降级 str ⇒ L962 抛 AttributeError ⇒ **整条 verify 崩**。
    #   两者同族：**端声明面缺失 ⇒ 判据面与落点面不相交 ⇒ 静默失败或全假红**。
    #   本自检把「声明缺失」在核验**开始前**显形，⛔不再让缺声明的端一路跑到崩溃/假红。
    try:
        _cp = os.path.join(PKG, "adapters", _PLATFORM_ID or "workbuddy", "capability.yaml")
        _cd = load_capability(_cp) or {}
        _capz = _cd.get("capabilities") or {}
        # 判据 v2（2026-10-06 自曝假阳后修）：**任一**注册面形态声明存在即放行——
        #   hooks_registration_face（install_scripts 分派用）/ hooks_mechanism（端声明
        #   「本端钩子走什么机制」）/ hooks_alternative（非标准机制顶替·为真）。
        #   v1 只认 hooks_registration_face ⇒ 把 zcode/traework（两者都有 hooks_mechanism
        #   + hooks_alternative + hooks_surface·声明完整）误判成缺声明 = **假红**。
        _declared = bool(_cd.get("hooks_registration_face")) \
            or bool(_capz.get("hooks_mechanism")) \
            or bool(_capz.get("hooks_alternative")) \
            or bool(_cd.get("hooks_surface"))
        if _capz and not _capz.get("hooks_event", True) and not _declared:
            print("🔴 [端SSOT声明自检] %s：capabilities.hooks_event=false（声明本端无标准 hook 面）"
                  " 但 hooks_registration_face / hooks_mechanism / hooks_alternative / hooks_surface "
                  "四者全缺 ⇒ 核验会落到错误的注册面形态（2026-10-06 autoclaw 实证：38 件全假红）。"
                  "请在该端 capability.yaml 补声明。" % _PLATFORM_ID)
    except Exception:
        pass
    # ── MC 缺省解析（2026-10-03 补·根治「无参 --verify 假红」）──────────────────
    #   病根：不带 MC 参数跑 `--verify` 时，下方 zcode 形态分支 base=sc=None
    #   ⇒ 落盘核恒 miss ⇒ 误报「脚本中心未落盘 7 件」**假红**（实盘 7 件齐备）。
    #   修法：缺省回落到标准记忆共享中心 ~/个人AI档案（存在即用；不存在才退化为仅核注册面）。
    if not mc:
        _d = os.path.expanduser("~/个人AI档案")
        if os.path.isdir(_d):
            mc = _d
    miss_file, miss_reg, miss_rd = [], [], []
    # ── 端形态分支（2026-10-03·条文19 判据与变换一致）：zcode 类端（settings_json=false + hooks_alternative=true）
    #    的 ROSTER 变换＝[5c/8]（公共部署→脚本中心 + 端 setup 注册 config.json 指向脚本中心）——
    #    ⛔ 按 settings.json+HOOKS_ROOT 旧判据核＝双错位假红（注册面错 + 落盘位置错）。
    cap = {}
    if _PLATFORM_ID:
        _cap_path = os.path.join(PKG, "adapters", _PLATFORM_ID, "capability.yaml")
        if os.path.isfile(_cap_path):
            cap = load_capability(_cap_path) or {}
    _caps = cap.get("capabilities", {})
    # ── 插件承载型端分支（2026-10-03·LobsterAI 端实证·条文13/33 扩展）──────────
    #   宿主第三方插件承载 hooks（非 settings.json / cli/config.json / launchd）——
    #   注册面=宿主 openclaw.json 的 plugins.entries/allow。按 capability
    #   hooks_registration_face 显式分派；⛔按 zcode_form 核 cli/config.json ⇒
    #   端注册面恒空 ⇒ 本端交付面全判“未注册”假红（2026-10-03 实测 39 件假红）。
    plugin_form = (_PLATFORM_ID not in (None, "", "workbuddy")
                   and cap.get("hooks_registration_face") == "openclaw_plugins")
    if plugin_form:
        _cfg_root = _CFG_ROOT_ABS or os.path.expanduser(cap.get("config_root", ""))
        ojson = os.path.join(_cfg_root, "openclaw.json")
        reg_text = ""
        if os.path.isfile(ojson):
            try:
                reg_text = open(ojson, encoding="utf-8", errors="ignore").read()
            except Exception:
                reg_text = ""
        cap_text = open(os.path.join(PKG, "adapters", _PLATFORM_ID, "capability.yaml"),
                        encoding="utf-8").read()
        # ① 插件 id 注册核（须出现在 openclaw.json 的 plugins.entries/allow）
        plugin_ids = re.findall(r"^\s*-\s*([A-Za-z0-9][A-Za-z0-9_.\-]+)\s*$", cap_text, re.M)
        for pid in plugin_ids:
            if pid not in reg_text:
                miss_reg.append("plugin:" + pid)
        # ② 交付脚本落盘核（src 分派·与 zcode 同构）
        entries = re.findall(
            r"script:\s*([A-Za-z0-9_.\-]+\.py)[^\n]*?src:\s*([A-Za-z0-9_/\-.])",
            cap_text)
        if not entries:
            entries = [(main_f, "references/scripts") for _ev, _loc, _sd, main_f, _deps in ROSTER]
        sc = os.path.join(mc, "脚本中心") if mc else None
        n_files = 0
        for fname, src_rel in entries:
            n_files += 1
            if "digital-twin" in src_rel:
                base = os.path.join(mc, "数字分身", "devtools") if mc else None
            else:
                base = sc
            if mc is not None and not (base and os.path.isfile(os.path.join(base, fname))):
                miss_file.append("%s (%s)" % (fname, src_rel))
        if mc:
            for name in RULE_DATA + RULE_FILES:
                if not os.path.isfile(os.path.join(mc, "记忆规则", name)):
                    miss_rd.append("记忆规则/%s" % name)
        print("钩子总表核查（%s 形态：注册面=%s（宿主插件表）· 落盘按 src 分派 · 核验清单=capability hooks_surface %d 件）"
              % (_PLATFORM_ID, ojson, n_files))
        if miss_reg:
            print("!! 端注册面（openclaw.json 插件表）缺 %d 项：%s" % (len(miss_reg), ", ".join(miss_reg)))
        if miss_file:
            print("!! 脚本中心未落盘 %d 件：%s" % (len(miss_file), ", ".join(sorted(set(miss_file)))))
        if miss_rd:
            print("!! 规则数据缺失 %d 件：%s" % (len(miss_rd), ", ".join(miss_rd)))
        if miss_reg or miss_file or miss_rd:
            return 1
        print("✅ 本端交付面 %d/%d 脚本已落盘 + %d 个插件已注册（宿主 openclaw.json 插件表）%s"
              % (n_files, n_files, len(plugin_ids), " · 规则层就位" if mc else ""))
        return 0
    zcode_form = (_PLATFORM_ID not in (None, "", "workbuddy")
                  and _caps.get("settings_json") is False
                  and _caps.get("hooks_alternative") is True)
    if zcode_form:
        reg_text = ""
        # ── 注册面按端分派（2026-10-03 补 Trae Work 第三形态）──────────────────
        #   Trae Work 无 config.json 注册面：注册面 = launchd plist + patrol 脚本 ROSTER 行。
        #   ⛔ 按 zcode 读 ~/.trae-cn/cli/config.json ⇒ 恒空 ⇒ 名册 7 件全判「未注册」＝假红
        #      （本端既非 settings.json 端、也非 zcode config.json 端·是 launchd 拉模式）。
        if _PLATFORM_ID == "traework":
            cfg_json = os.path.expanduser("~/Library/LaunchAgents/com.buluotuo.traework.patrol.plist")
            _parts = []
            if os.path.isfile(cfg_json):
                try:
                    _parts.append(open(cfg_json, encoding="utf-8", errors="ignore").read())
                except Exception:
                    pass
            if mc:
                # 🔴 2026-10-21 补：脚本面归拢后 patrol 实体在 `脚本中心/Skill路由引擎/scripts/`；
                #    旧两条路径（开发工具/… 、脚本中心/平铺）均已不存在 ⇒ reg_text 只剩 plist
                #    （plist 只写主脚本名，不含名册件）⇒ 7 件全判「未注册」＝假红。
                for _rel in (os.path.join("脚本中心", "Skill路由引擎", "scripts", "route_traework_patrol.sh"),
                             os.path.join("开发工具", "Skill路由引擎", "scripts", "route_traework_patrol.sh"),
                             os.path.join("脚本中心", "route_traework_patrol.sh")):
                    _p = os.path.join(mc, _rel)
                    if os.path.isfile(_p):
                        try:
                            _parts.append(open(_p, encoding="utf-8", errors="ignore").read())
                        except Exception:
                            pass
                        break
            # 🔴 2026-10-21 补：Trae CN（2026-10-09 并入单端）的真实注册面是
            #    `<配置根>/hooks.json`（PreToolUse/Stop 等事件直挂）。traework 适配器
            #    声明的是「安装包交付面」（hooks_event=false 指无 settings.json 注册），
            #    与端侧自建 hooks.json 不矛盾——核注册时必须两读，否则实挂判未挂。
            _cn_cfg = _CFG_ROOT_ABS or os.path.expanduser(cap.get("config_root", "~/.trae-cn"))
            _cn_hooks = os.path.join(_cn_cfg, "hooks.json")
            if os.path.isfile(_cn_hooks):
                try:
                    _parts.append(open(_cn_hooks, encoding="utf-8", errors="ignore").read())
                except Exception:
                    pass
            reg_text = "\n".join(_parts)
        else:
            cfg_root = _CFG_ROOT_ABS or os.path.expanduser(cap.get("config_root", "~/.zcode"))
            cfg_json = os.path.join(cfg_root, "cli", "config.json")
            if os.path.isfile(cfg_json):
                try:
                    reg_text = json.dumps(json.load(open(cfg_json, encoding="utf-8")), ensure_ascii=False)
                except Exception:
                    reg_text = ""
        cap_text = open(os.path.join(PKG, "adapters", _PLATFORM_ID, "capability.yaml"), encoding="utf-8").read() if _PLATFORM_ID else ""
        sc = os.path.join(mc, "脚本中心") if mc else None
        # 核验清单=capability hooks_surface.delivered（端交付面 SSOT·条文33）——
        # ⛔ 用 ROSTER 全集核 zcode＝把「WB 域件（作者端实盘亦未挂）」误判为 zcode 欠账
        entries = re.findall(
            r"script:\s*([A-Za-z0-9_.\-]+\.py)[^\n]*?src:\s*([A-Za-z0-9_/\-.]+)", cap_text) if cap_text else []
        if not entries:
            entries = [(main_f, "references/scripts") for _ev, _loc, _sd, main_f, _deps in ROSTER]
        n_files = 0

        def _delivered_ok(_mc, _base, _fname):
            """落盘核（2026-10-21·脚本面归拢子目录后根治假红）。
            判定顺序：①平铺原址 ②递归 脚本中心 任意子目录 ③实际交付面回落
            自定义层/待完成工作/路由家族/scripts（route_guard_audit 的真身所在）。
            ⛔ 只回答「这端有没有这件」，不回答「该不该在某个目录」——布局归拢属安装器域。"""
            if _base and os.path.isfile(os.path.join(_base, _fname)):
                return True
            if _base and os.path.isdir(_base):
                for _dp, _dn, _fs in os.walk(_base):
                    if _fname in _fs:
                        return True
            if _mc:
                for _rel in (("自定义层", "待完成工作", "路由家族", "scripts"), ("脚本中心",)):
                    if os.path.isfile(os.path.join(_mc, *_rel, _fname)):
                        return True
            return False

        for fname, src_rel in entries:
            n_files += 1
            # 落盘核按 src 分派（判据从变换规则推导·[5/8][5b/8][5c/8] 各归各位）
            if "digital-twin" in src_rel:
                base = os.path.join(mc, "数字分身", "devtools") if mc else None
            elif src_rel.startswith("adapters/"):
                base = os.path.join(_CFG_ROOT_ABS or "", "hooks") if _CFG_ROOT_ABS else None
            else:
                base = sc
            if mc is not None and not _delivered_ok(mc, base, fname):
                miss_file.append("%s (%s)" % (fname, src_rel))
            if fname not in reg_text:
                miss_reg.append(fname)
        if mc:
            for name in RULE_DATA + RULE_FILES:
                if not os.path.isfile(os.path.join(mc, "记忆规则", name)):
                    miss_rd.append("记忆规则/%s" % name)
        print("钩子总表核查（%s 形态：注册面=%s · 落盘按 src 分派 · 核验清单=capability hooks_surface %d 件）"
              % (_PLATFORM_ID, cfg_json, n_files))
        if mc is None:
            print("ℹ️ 未提供记忆共享中心路径且默认 ~/个人AI档案 不存在——仅核注册面，跳过落盘/规则核验（用法：--verify <MC>）")
        if miss_file:
            print("!! 脚本中心未落盘 %d 件：%s" % (len(miss_file), ", ".join(sorted(set(miss_file)))))
        if miss_reg:
            print("!! 端注册面未注册 %d 件：%s" % (len(miss_reg), ", ".join(miss_reg)))
        if miss_rd:
            print("!! 规则数据缺失 %d 件（铁律硬墙会静默零注入）：%s" % (len(miss_rd), ", ".join(miss_rd)))
        if miss_file or miss_reg or miss_rd:
            return 1
        # 分母=实际核验清单（n_files），⛔ 不用 len(ROSTER)——traework 交付面 7 件 ≠ 全端 ROSTER 19 件，
        #   用 ROSTER 长度会把「只核了 7 件」说成「19/19 全过」＝数字不实（G3 派生一致性）。
        print("✅ 本端交付面 %d/%d 钩子已落盘并注册（全端 ROSTER %d 件）%s"
              % (n_files, n_files, len(ROSTER), " · 规则层就位" if mc else ""))
        return 0
    # ── 无 hook 端分支（2026-10-03·条文13/20·根治无hook端verify假红）：
    #    豆包办公等端（hooks_event=false + hooks_alternative≠true）既无 settings.json
    #    也无替代钩子机制——按标准分支核 HOOKS_ROOT/SETTINGS = 双错位假红。
    #    此类端的守卫靠"端专属Skill内嵌校验"实现（非独立hook进程），
    #    verify 只核公共资产（脚本中心/数字分身/规则数据），跳过钩子核查。
    no_hook_form = (_PLATFORM_ID not in (None, "", "workbuddy")
                    and _caps.get("hooks_event") is False
                    and _caps.get("hooks_alternative") is not True)
    if no_hook_form:
        print("公共资产核查（%s 形态：无 hook 机制·守卫靠端专属Skill内嵌校验·跳过钩子核查·只核公共资产）"
              % _PLATFORM_ID)
        # 只核公共资产：脚本中心 / 数字分身 / 规则数据
        if mc:
            sc = os.path.join(mc, "脚本中心")
            dt = os.path.join(mc, "数字分身")
            if not os.path.isdir(sc):
                miss_file.append("脚本中心/（目录缺失）")
            if not os.path.isdir(dt):
                miss_file.append("数字分身/（目录缺失）")
            for name in RULE_DATA + RULE_FILES:
                if not os.path.isfile(os.path.join(mc, "记忆规则", name)):
                    miss_rd.append("记忆规则/%s" % name)
        else:
            print("ℹ️ 未提供记忆共享中心路径——仅核端形态，跳过公共资产核验（用法：--verify <MC>）")
        if miss_file:
            print("!! 公共资产缺失 %d 件：%s" % (len(miss_file), ", ".join(sorted(set(miss_file)))))
        if miss_rd:
            print("!! 规则数据缺失 %d 件（铁律硬墙会静默零注入）：%s" % (len(miss_rd), ", ".join(miss_rd)))
        if miss_file or miss_rd:
            return 1
        print("✅ 公共资产全部就位（脚本中心 + 数字分身 + 规则数据%s）·钩子本端不适用（由端专属Skill内嵌校验承载）"
              % (" · 规则层就位" if mc else ""))
        return 0
    data = {}
    if os.path.isfile(_st):
        try:
            with open(_st, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = {}
    hooks = data.get("hooks", {}) if isinstance(data, dict) else {}

    def registered(ev, base):
        for grp in hooks.get(ev, []) or []:
            if not isinstance(grp, dict):
                continue
            for h in grp.get("hooks", []):
                if isinstance(h, dict) and base in h.get("command", ""):
                    return True
        return False

    # ── 非WB settings 端按 capability 交付面核（2026-10-06 G3首轮自证·"判据未随端形态演化=假红"同族）──
    #   qodercn 等端（hooks_surface 有声明·条文33端交付面SSOT）按 ROSTER 全集核＝把 WB 域件
    #   （workbuddy_* 三件等）判成本端欠账假红。装机态不受影响：hooks 全集落盘=capability 超集，
    #   子集判据照样过——判据变准不变松。WB(_PLATFORM_ID 空/workbuddy)域行为零改动。
    _cap_surf = (cap or {}).get("hooks_surface") or {}
    _deliv = _cap_surf.get("delivered") or []
    if _PLATFORM_ID not in (None, "", "workbuddy") and _deliv:
        _bases = _landing_bases(mc)
        # ── 交付面条目双形态（2026-10-10 hermes 假绿根治）──────────────────
        # 病根实证：本节只取 `script`/`event` 两个键，而 hermes 的 delivered 是
        #   `{plugin: 名字, events: [E1,E2]}` 形态 ⇒ _fn 恒空 ⇒ 16 条全部
        #   `continue` ⇒ miss_file/miss_reg 恒空 ⇒ 打印「16/16 已落盘并注册」
        #   **一件都没检过**。这正是「判据只认一种端形态 = 对别的端恒假绿」。
        # ⇒ 按声明真实形态分别取值 + 分别核验，⛔ 不放宽成不检（必须真检）：
        #     plugin 形态：① 端注册面 ~/.hermes/plugins/<名>/plugin.yaml 存在
        #                   ② 其 provides_hooks **含声明事件**（⛔不再只对插件名）
        #                   ③ 包内有源 adapters/<端>/plugins/<名>/
        #     script 形态：维持原判据（落盘 + registered）
        _plug_reg = os.path.expanduser("~/.hermes/plugins")
        for _e in _deliv:
            # 2026-10-06 防御：端SSOT 条目若为裸字符串（capability 用了非受控子集写法
            # 或 _mini_yaml 未能还原行内 dict），按「只有文件名、无事件」降级处理，
            # ⛔不再让 .get() 抛 AttributeError 把整条 verify 打断（v1.89 口径崩过一版）。
            if isinstance(_e, dict) and _e.get("plugin"):
                _pn = str(_e.get("plugin", "")).strip()
                _pevs = _e.get("events") or []
                if isinstance(_pevs, str):
                    # ⚠️ _mini_yaml 不解析行内 list ⇒ `events: [a, b]` 会成一个
                    #   带方括号的整串（实测"[pre_llm_call, post_llm_call]"）。
                    #   ⛔ 不剥方括号 ⇒ 拆出 "[pre_llm_call" 恒不等于真事件名
                    #   ⇒ 每个多事件插件必报假红（2026-10-10 实测 3 件 6 处）。
                    _pevs = _pevs.strip().lstrip("[").rstrip("]")
                    _pevs = [x.strip().strip("\"'") for x in _pevs.split(",") if x.strip()]
                elif isinstance(_pevs, (list, tuple)):
                    _pevs = [str(x).strip().strip("\"'").lstrip("[").rstrip("]")
                             for x in _pevs if str(x).strip()]
                if not _pn:
                    continue
                _pyaml = os.path.join(_plug_reg, _pn, "plugin.yaml")
                if not os.path.isfile(_pyaml):
                    miss_reg.append("%s（插件未安装：~/.hermes/plugins/%s/plugin.yaml 不在）" % (_pn, _pn))
                    continue
                try:
                    _ptxt = open(_pyaml, encoding="utf-8").read()
                except OSError:
                    miss_reg.append("%s（plugin.yaml 不可读）" % _pn)
                    continue
                _tail = _ptxt.split("provides_hooks:")[1] if "provides_hooks:" in _ptxt else ""
                _declared_evs = re.findall(r"^\s*-\s*([a-z_]+)\s*$", _tail, re.M)
                for _ev in _pevs:
                    if _ev and _ev not in _declared_evs:
                        miss_reg.append("%s（声明事件 %s 不在其 provides_hooks %s 中）"
                                        % (_pn, _ev, _declared_evs or "[]"))
                if not os.path.isdir(os.path.join(PKG, "adapters", _PLATFORM_ID, "plugins", _pn)):
                    miss_file.append("%s（包内 adapters/%s/plugins/ 无源）" % (_pn, _PLATFORM_ID))
                continue
            if isinstance(_e, dict):
                _fn, _evn = _e.get("script", ""), _e.get("event", "")
            else:
                _fn, _evn = str(_e).strip(), ""
            if not _fn:
                continue
            if not any(b and os.path.isfile(os.path.join(b, _fn)) for b in _bases):
                miss_file.append(_fn)
            if _evn and not registered(_evn, _fn):
                miss_reg.append(_fn)
            if not _evn:
                # P08 假绿钩子根治（2026-10-19）：deliv 条目丢 event（_mini_yaml 降级/声明漂移）
                # 原 `if _evn and` 短路=注册面整件免检——恒真判据正是本卡警告的病。
                # 现 fail-loud：声明降级=判据失效，显式判红而不是放行。
                miss_reg.append("%s（deliv 条目无 event 声明·注册面不可核·⛔不静默放行）" % _fn)
        if mc:
            for _name in RULE_DATA + RULE_FILES:
                if not os.path.isfile(os.path.join(mc, "记忆规则", _name)):
                    miss_rd.append("记忆规则/%s" % _name)
        print("钩子总表核查（%s 形态：注册面=settings.json · 核验清单=capability hooks_surface %d 件·端SSOT口径）"
              % (_PLATFORM_ID, len(_deliv)))
        if miss_file:
            print("!! 未落盘 %d 件：%s" % (len(miss_file), ", ".join(sorted(set(miss_file)))))
        if miss_reg:
            print("!! 未注册 %d 件：%s" % (len(miss_reg), ", ".join(miss_reg)))
        if miss_rd:
            print("!! 规则数据缺失 %d 件：%s" % (len(miss_rd), ", ".join(miss_rd)))
        if miss_file or miss_reg or miss_rd:
            return 1
        print("✅ 本端交付面 %d/%d 钩子已落盘并注册（全端 ROSTER %d 件·端SSOT口径）"
              % (len(_deliv), len(_deliv), len(ROSTER)))
        return 0

    n_files = 0
    for ev, loc, _sd, main_f, deps in ROSTER:
        dst_dir = _hr if loc == "." else os.path.join(_hr, loc)
        _bs = _landing_bases(mc)
        for fname in [main_f] + list(deps):
            n_files += 1
            if not any(b and os.path.isfile(os.path.join(b, fname)) for b in [dst_dir] + _bs):
                miss_file.append("%s/%s" % (loc, fname) if loc != "." else fname)
        if not registered(ev, main_f):
            miss_reg.append(main_f)

    if mc:
        for name in RULE_DATA + RULE_FILES:
            if not os.path.isfile(os.path.join(mc, "记忆规则", name)):
                miss_rd.append("记忆规则/%s" % name)

    print("钩子总表核查（数据源=install_scripts.py ROSTER·%d 个钩子 / %d 个文件）" % (len(ROSTER), n_files))
    if miss_file:
        print("!! 未落盘 %d 件：%s" % (len(miss_file), ", ".join(sorted(set(miss_file)))))
    if miss_reg:
        print("!! 未注册 %d 件：%s" % (len(miss_reg), ", ".join(miss_reg)))
    if miss_rd:
        print("!! 规则数据缺失 %d 件（铁律硬墙会静默零注入）：%s" % (len(miss_rd), ", ".join(miss_rd)))
    if miss_file or miss_reg or miss_rd:
        return 1

    print("✅ %d/%d 钩子已落盘并注册%s"
          % (len(ROSTER), len(ROSTER), " · 规则层就位" if mc else ""))
    return 0


def gate_check(platform_id):
    """发版前置门禁（用户令·2026-10-03·全端通用）：端适配 100% 才放行打包该端。

    把「自身 100% 才许映射」从单端点状修补升级为全端发版门禁——任一端未达 100% → 拒绝打包。

    🔴 2026-10-10 死链根治（9/9 端恒 rc=2·git 考古 --gate 从未在 pac 里存在过）：
       旧实现委派给 `platform_adaptation_check.py --gate --pkg-root`，而 pac 的 argparse
       只有 `--src/--fix/--absorb/--absorb-selftest` ⇒ subprocess 拿到 argparse 的
       rc=2（**参数拒绝·非业务判红**），上游把 2 当「门禁拒绝」而**错误信息已被吞**。
       ⇒ 该门禁自 2026-10-03 引入起**一次都没跑通过**，却一直在宣称"放行"。
    根因不是 pac 坏，是**委派目标选错**：
       · pac = 「接入率漂移校验」（文档 vs 实盘·check_hermes 等），无三面判据；
       · 三面判据（面A 五系统文件 / 面B 钩子面 / 面C 数字分身面）**只在 verify.sh**
         （§1.5/§1.6/twin_surface·L648/650：PASS 全过 exit 0，有 FAIL exit 1）。
    ⇒ 本函数改为**委派 verify.sh**（判据真源），pac 退为附加漂移检查并如实标注其语义。
    """
    import subprocess
    _pkg_dir = os.path.dirname(os.path.abspath(__file__))
    verify = os.path.join(_pkg_dir, "verify.sh")
    if not os.path.isfile(verify):
        print("❌ 发版门禁脚本缺失: %s（三面判据真源·打包前须随包分发）" % verify)
        return 2

    print("─" * 60)
    print("🔒 发版前置门禁：端适配三面判据（verify.sh §1.5 系统文件 / §1.6 钩子面 / twin_surface）")
    r = subprocess.run(["bash", verify, "--platform", platform_id],
                       capture_output=True, text=True, errors="replace")
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        print("❌ 发版门禁未过：三面有 FAIL ⇒ 拒绝打包/发版该端（明细见上）")
        return r.returncode
    print("✅ 发版门禁通过：三面判据全过（verify.sh rc=0）")

    # ── 附加：接入率漂移（pac·语义=文档 vs 实盘·⛔ 不是三面门禁·失败只提示不拦）──
    pac = os.path.join(_pkg_dir, "platform_adaptation_check.py")
    if os.path.isfile(pac):
        # ⚠️ 源机自指噪声（2026-10-10）：包内那份 pac 的 LOG 是占位符形态
        #   `[记忆共享中心]/脚本中心/logs/…`（deident 规则4 所致·装机时才替换成用户真实路径）。
        #   在**源机**上跑它 ⇒ 占位符不被替换 ⇒ 真在包内造出
        #   `[记忆共享中心]/脚本中心/logs/platform_adaptation_check.log` ⇒ 随后被
        #   pkg_cleanliness_check 当「运行时日志 *.log」报 FAIL（门禁自己污染自己·第二类自指）。
        #   ⇒ 跑后清理该占位目录（用户机上此路径本就该指向记忆中心·不涉及真实资产）。
        _self_ref = os.path.join(_pkg_dir, PLACEHOLDER)
        p = subprocess.run([sys.executable, pac, "--src", platform_id],
                           capture_output=True, text=True, errors="replace")
        if os.path.isdir(_self_ref):
            shutil.rmtree(_self_ref, ignore_errors=True)
        if p.returncode == 0:
            print("✅ 附加检查：接入率无漂移（platform_adaptation_check.py --src %s）" % platform_id)
        else:
            print("⚠️ 附加检查：接入率漂移（platform_adaptation_check.py rc=%d）——"
                  "不影响放行，但发布前应核对" % p.returncode)
            if p.stdout:
                sys.stdout.write(p.stdout)
    return 0


def write_user_versions(mc, dry=False):
    """安装末尾：把包侧 component-versions.json 落到用户 .install/versions.json，
    供下次升级做组件级对比（命题③：对比读真实文件，不靠自报）。
    幂等：已存在则覆盖（包版本始终是最新口径）。"""
    src = os.path.join(PKG, "references", "component-versions.json")
    if not os.path.isfile(src):
        print("!! 包内 component-versions.json 缺失，跳过版本快照写入")
        return False
    dst_dir = os.path.join(mc, ".install")
    if dry:
        print("[dry-run] 将写入 %s/versions.json（组件级版本快照）" % dst_dir)
        return True
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, "versions.json"))
    # G2-2·装机归属登记：把本次判定端与 config_root 记入快照（verify/升级对账用·判定证据链回写）
    try:
        _vp = os.path.join(dst_dir, "versions.json")
        _v = json.load(open(_vp, encoding="utf-8"))
        _v["platform_installed"] = _PLATFORM_ID
        _v["config_root_installed"] = _CFG_ROOT_ABS
        json.dump(_v, open(_vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as _e:
        print("!! 装机归属登记写入失败（不阻塞·版本快照原件仍在）：%s" % _e)
    print("①c 版本快照：组件级版本已写入 %s/versions.json（供升级对比）" % dst_dir)
    return True


def _strip_inline_comment(s):
    """剥行内注释：只截「引号外、行首或空白后」的 #（YAML 规范），
    引号内的 #（如 URL #锚点）保留。"""
    out, q, prev = [], None, ""
    for ch in s:
        if q:
            out.append(ch)
            if ch == q and prev != "\\":
                q = None
        elif ch in "\"'":
            q = ch; out.append(ch)
        elif ch == "#" and (prev == "" or prev in " \t"):
            break
        else:
            out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def _yaml_cast(v):
    """把一个标量字符串转成 bool/None/数字/行内列表/字符串（受控子集）。"""
    v = v.strip()
    if v == "":
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", "none"):
        return None
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_yaml_cast(x) for x in _split_inline(inner)] if inner else []
    for num in (int, float):
        try:
            return num(v)
        except ValueError:
            pass
    return v


def _split_inline(s):
    """拆行内列表，尊重引号。"""
    out, buf, q = [], "", None
    for ch in s:
        if q:
            buf += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch; buf += ch
        elif ch == ",":
            out.append(buf); buf = ""
        else:
            buf += ch
    if buf.strip() != "":
        out.append(buf)
    return out


def _parse_inline_dict(s):
    """解析 YAML 行内映射 `{k: v, k2: v2}`（2026-10-06 新增·根治 verify 端SSOT口径全线崩）。
    病根实证：capability.yaml 的 `hooks_surface.delivered` 全部写成行内 dict
      （`- {script: kb_inject_prompt.py, event: UserPromptSubmit, src: ...}`），
      而 _mini_yaml 的列表分支只做 _yaml_cast ⇒ 26/16/29/7/35 条**全降级成 str**
      ⇒ install_scripts L962 的 `_e.get("script")` 抛 AttributeError
      ⇒ **qodercn / hermes 两端 --verify 直接崩**（PyYAML 本机不可用，兜底路径必经）。
      即：v1.89「端SSOT口径」判据在无 PyYAML 环境**从未跑通过**，工单记的
      「qodercn ✅26/26·hermes ✅16/16」是假绿。
    切分口径：按 `,` 切后 strip（⛔不能用 `", "`——capability 里存在逗号后多空格的
      对齐写法 `{script: x.py,     note: ...}`）；无 `:` 的碎段拼回上一键（值含逗号的保护）。"""
    s = s.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    inner = s[1:-1].strip()
    out = {}
    if not inner:
        return out
    for part in inner.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part and out:
            k = list(out)[-1]                     # 值里含逗号 → 拼回上一键
            out[k] = "%s, %s" % (out[k], part)
            continue
        k, _, v = part.partition(":")
        k = k.strip()
        if k:
            out[k] = _yaml_cast(_strip_inline_comment(v).strip())
    return out


def _mini_yaml(text):
    """极简 YAML 解析（仅 capability.yaml 受控子集）：缩进 map / key:value /
    行内 [..] / 行内 {..} / '- ' 列表 / '|' 多行块 / 整行 # 注释。PyYAML 缺失时兜底，零第三方依赖。"""
    root = {}
    stack = [(-1, root)]                       # (indent, container)
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        body = raw.strip()
        if body == "" or body.startswith("#"):
            i += 1; continue
        ind = len(raw) - len(raw.lstrip(" "))
        while stack and ind <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if body.startswith("- ") or body == "-":
            if isinstance(parent, list):
                item = _strip_inline_comment(body[1:]).strip()
                d = _parse_inline_dict(item)      # 2026-10-06：行内 dict 还原（根因修复）
                parent.append(d if d is not None else _yaml_cast(item))
            i += 1; continue

        key, _, val = body.partition(":")
        key = key.strip()
        val = _strip_inline_comment(val).strip()

        if val in ("|", ">"):
            block, j, base = [], i + 1, None
            while j < len(lines):
                r = lines[j]
                if r.strip() == "":
                    block.append(""); j += 1; continue
                d = len(r) - len(r.lstrip(" "))
                if d <= ind:
                    break
                if base is None:
                    base = d
                block.append(r[base:] if len(r) >= base else r.lstrip(" "))
                j += 1
            while block and block[-1] == "":
                block.pop()
            parent[key] = "\n".join(block) + "\n"
            i = j; continue

        if val == "":
            k, nxt = i + 1, None
            while k < len(lines):
                if lines[k].strip() and not lines[k].strip().startswith("#"):
                    nxt = lines[k]; break
                k += 1
            is_list = bool(nxt and nxt.strip().startswith("-")
                           and (len(nxt) - len(nxt.lstrip(" "))) > ind)
            child = [] if is_list else {}
            parent[key] = child
            stack.append((ind, child))
            i += 1; continue

        parent[key] = _yaml_cast(val)
        i += 1
    return root


def load_capability(path, mc=None):
    """读 capability：优先 PyYAML；环境缺失时走内置极简解析（端用户零安装）。

    ⚠️ **读时占位符替换**（2026-10-02 补·立规：给用户的东西必须是脱敏通用版）：
    `capability.yaml` 里的 `hooks_ssot` / `hooks_validator` 指向**记忆中心里的文件**。
    此前它们直接写死作者的目录名 ⇒ ① 泄露作者环境 ② **用户机器上根本不存在**，
    校验器永远跑不了。
    ⇒ 改用既有占位符 `[记忆共享中心]`，**在读取时**替换成本机实况。
    ⛔ 注意：capability 是**被解析**的，⛔ **不经过 `_fill()`**（那只处理被复制的文件）
    ——所以必须在这里补一步，否则占位符永远留在字面量里。
    """
    raw = open(path, encoding="utf-8").read()
    if PLACEHOLDER in raw:
        # ⚠️ **只读已有值，绝不扫描**——扫描会递归：
        #    `_detect_platform_from_env()` → 本函数 → 再扫 capability → ∞。
        #    来源优先级：显式参数 › 环境变量 › main() 已解析的 MC_PATH 全局。
        mc = mc or os.environ.get("BULUOTUO_MEMORY_CENTER") \
            or globals().get("MC_PATH") or ""
        if mc:
            raw = raw.replace(PLACEHOLDER, mc.rstrip("/"))
        # ⛔ 解析不出时**原样返回**：不炸、不静默替调用者决定；
        #    残留字面量只影响 hooks_ssot/hooks_validator 这类"校验器路径"字段，
        #    config_root 等仍正常。main() 会因 MC_PATH 必填而先于本处 fail-loud。
    return _parse_cap_text(raw)


def _parse_cap_text(raw):
    try:
        import yaml
        return yaml.safe_load(raw)
    except ModuleNotFoundError:
        return _mini_yaml(raw)




# ── 脱敏归一（2026-10-07 · deploy_script_center 同名冲突判据单一真源）──────
# 冲突清单模块级标志（deploy_script_center 写入·main() 读·⛔ 不改函数返回契约）
_PKG_CONFLICTS = []
# 为什么需要：包内三目录是同源镜像，本应逐字相同，但脱敏深度不同
#   （references/scripts 留「个人AI档案/」前缀、digital-twin/devtools 已换成「~/」）
#   → 直接比字节必然全冲突；必须先归一路径形态再比。
# ⛔ 只归一「档案路径字面量」本身 · ⛔ 不吞整个调用（否则 join 内的真实差异被吞 → 误判同源）。
# 同步真源：开发工具/buluotuo-release-sync/pkg_conflict_audit.py::normalize（两侧同判据）
import re as _re

_ARCHROOT_FULL = _re.compile(r"""["'](?:个人AI档案|\[记忆共享中心\]|~)/(?:[^"']*)["']""")
_ARCHROOT_BARE = _re.compile(r"""["'](?:个人AI档案|\[记忆共享中心\])/?["']""")
_TILDE_BARE = _re.compile(r"""["']~["']""")
_HOMEPLUS = _re.compile(r"""expanduser\(\s*HOME\s*\+\s*["'][^"']*["']\s*\)""")
# 2026-10-12 根治假红：shell ${VAR} 与 $VAR 语义等价（沙箱 R1 要求 .sh 一律花括号），
#   归一为 $VAR，与 pkg_conflict_audit.normalize 同律——缺此条会把等价写法误判同名冲突。
_BRACE = _re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')


def _deident_norm(text):
    """脱敏归一：路径形态统一 + 去注释/空行/docstring → 同名冲突判定用。"""
    out, in_doc = [], False
    for ln in text.splitlines():
        st = ln.strip()
        q3 = st[:3]
        if q3 in ('"""', "'''") and not (st.endswith(q3) and len(st) > 5):
            in_doc = not in_doc
            continue
        if in_doc:
            continue
        if q3 in ('"""', "'''") and st.endswith(q3):
            continue
        t = '' if st.startswith('#') else ln.split('#')[0]
        if not t.strip():
            continue
        t = _HOMEPLUS.sub('expanduser("ARCHROOT")', t)
        t = _ARCHROOT_FULL.sub('"ARCHROOT"', t)
        t = _ARCHROOT_BARE.sub('"ARCHROOT"', t)
        t = _TILDE_BARE.sub('"ARCHROOT"', t)
        t = _BRACE.sub(r'$\1', t)
        out.append(_re.sub(r"\s+", " ", t).strip())
    return "\n".join(out)


# ── 运行路径语义键 → 目录约定（端中立：⛔ 不含任何端名/作者目录名）──────
# ⚠️ 这些是**目录名**（相对档案根），不是绝对路径。安装器按本机实况填值。
RUNTIME_PATH_DIRS = {
    # ⚠️ **落点必须等于安装器实际写入的位置**（`deploy_script_center` 的
    #    `os.path.join(mc, "脚本中心")` / 知识联邦引擎装在其下）。
    # 🔴 2026-10-02 取证实锤：原值写 `开发工具` —— 那是**作者侧**目录，
    #    端用户机器上**根本不存在** ⇒ build_runtime_paths 因存在性过滤跳过该键
    #    ⇒ `rp("devtools")` 抛 PathKeyMissing ⇒ 16 插件里 22 处调用全炸。
    #    ⛔ 而作者机上该目录存在 ⇒ 本机三关闸门 100% 测不出来（假绿）。
    #    ⇒ 键名表达**职责**、落点由安装器事实决定，二者解耦。
    "devtools":      "脚本中心",
    # 🔴 2026-10-21 根治（Trae CN 端复检实证）：脚本面归拢后 知识联邦引擎 实盘在
    #    `脚本中心/知识联邦引擎/`，顶层并无此目录。原值 "知识联邦引擎" 会产出一个
    #    **存在于声明、不存在于磁盘**的死键（build_runtime_paths 的存在性过滤只挡
    #    安装期；已安装端不会自动重算）⇒ 消费方 rp("kb_engine") 静默取空。
    #    与本文件上方注释「知识联邦引擎装在其下」对齐为子目录元组。
    "kb_engine":     ("脚本中心", "知识联邦引擎"),
    "script_center": "脚本中心",
    "worklog":       "工作日志",
    "twin":          "数字分身",
    "blueprint":     "记忆蓝图",
    "skills":        "技能配置",
    "knowledge":     "知识库",
    "kb_root":       "知识库",   # 知识库根（⛔ 不假设 Obsidian：默认 MC/知识库·零 Obsidian 依赖；安装期自动探测用户 vault，命中即采用，否则回落 MC/知识库）
    "diary_root":    ("日记", "1-每日计划", "01-日记"),   # 日记根（⛔ 不假设 Obsidian：默认 MC/日记/1-每日计划/01-日记·零 Obsidian 依赖；安装期随 vault 探测，命中即采用，否则回落 MC/日记）
    "k2_slices":     ("数字分身", "K2切片蒸馏"),
    "twin_slices":   ("数字分身", "K2切片蒸馏", "slices"),
    "twin_spec":     ("数字分身", "童灵·人格规格书.md"),
    "custom_route":  ("自定义层", "待完成工作", "路由家族"),
    "memory_amber":  "记忆琥珀",
}
# 注意：`archive_root` 本身＝记忆中心（不进这张表·它就是根）


def detect_kb_root(archive_root):
    """知识库根探测（零配置优先·最便捷）：
    - 扫描家目录含 .obsidian 标记的目录（Obsidian vault 权威信号）⇒ 命中即采用，用户无感；
    - 否则回落 MC/知识库（装机态默认，安装器建库面）。
    ⚠️ 仅做"位置探测"，不校验卡内容、不硬编码任何作者/用户专属目录名——引擎 _first_live
       会按实际卡位自适应回落，故空 vault 也安全（回落 MC 默认）。探测异常静默回落默认，不阻断安装。
    声明优先：write_runtime_paths 在重装时保留用户已声明的 kb_root（条文47 单源真相）。"""
    root = os.path.abspath(os.path.expanduser(archive_root))
    home = os.path.expanduser("~")
    cands = []
    try:
        for d in sorted(os.listdir(home)):
            pd = os.path.join(home, d)
            if os.path.isdir(pd) and os.path.isdir(os.path.join(pd, ".obsidian")):
                cands.append(pd)
    except Exception:
        pass
    for c in cands:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return os.path.join(root, "知识库")

def detect_diary_root(archive_root):
    """日记根探测（零配置优先·最便捷）：
    - 扫描家目录含 .obsidian 标记的目录（Obsidian vault 权威信号）⇒ 命中则日记位＝该 vault/1-每日计划/01-日记，用户无感；
    - 否则回落 MC/日记/1-每日计划/01-日记（装机态默认，安装器建库面）。
    ⚠️ 仅做"位置探测"，不校验内容、不硬编码任何作者/用户专属目录名。探测异常静默回落默认，不阻断安装。
    声明优先：write_runtime_paths 在重装时保留用户已声明的 diary_root（条文47 单源真相）。"""
    root = os.path.abspath(os.path.expanduser(archive_root))
    home = os.path.expanduser("~")
    vault = None
    try:
        for d in sorted(os.listdir(home)):
            pd = os.path.join(home, d)
            if os.path.isdir(pd) and os.path.isdir(os.path.join(pd, ".obsidian")):
                vault = pd
                break
    except Exception:
        pass
    if vault:
        return os.path.join(os.path.abspath(vault), "1-每日计划", "01-日记")
    return os.path.join(root, "日记", "1-每日计划", "01-日记")

def build_runtime_paths(archive_root, cap=None, exists_check=True):
    """由「档案根 + 目录约定」算出本机的运行路径声明。

    - `archive_root` ＝ 记忆中心（用户可命名成任何东西）
    - 目录不存在 ⇒ 该键**不写入声明**（插件取它时报错，而不是指着一个空目录）
    - `exists_check=False` 时全写（用于 dry-run / 测试夹具）

    ⚠️ 为什么"目录不存在就不写"：声明里放一个不存在的路径 = 让脚本对着
    空目录跑 = **静默空转**。缺键抛错能在安装时就显形。
    """
    root = os.path.abspath(os.path.expanduser(archive_root))
    out = {"archive_root": root}
    for key, rel in RUNTIME_PATH_DIRS.items():
        p = os.path.join(root, *(rel if isinstance(rel, tuple) else (rel,)))
        if exists_check and not os.path.exists(p):
            continue
        out[key] = p
    out["kb_root"] = detect_kb_root(root)
    out["diary_root"] = detect_diary_root(root)
    return out


def write_runtime_paths(archive_root, cap=None, cfg_root=None, dry=False):
    """生成 `<配置根>/doenglingz/runtime_paths.json`（**安装器唯一写入口**）。"""
    import importlib.util as _il
    rp_path = os.path.join(PKG, "references", "scripts", "runtime_paths.py")
    if not os.path.isfile(rp_path):
        raise RuntimeError("运行路径解析器缺失：%s" % rp_path)
    spec = _il.spec_from_file_location("runtime_paths", rp_path)
    if spec is None or getattr(spec, "loader", None) is None:
        raise RuntimeError("运行路径解析器无法载入：%s" % rp_path)
    mod = _il.module_from_spec(spec)
    spec.loader.exec_module(mod)
    target_cfg = cfg_root or _CFG_ROOT_ABS
    mod.reset_cache()
    os.environ["BULUOTUO_RUNTIME_PATHS"] = os.path.join(
        os.path.expanduser(target_cfg), "doenglingz", "runtime_paths.json")
    data = build_runtime_paths(archive_root, cap)
    # 2026-10-20：kb_root/diary_root 若为默认库位且不存在 → 先建再声明
    #（不破"声明里不放不存在路径"不变量；vault 命中时本就存在，不触碰）
    if not dry:
        for _k in ("kb_root", "diary_root"):
            _p = data.get(_k)
            if _p and not os.path.isdir(_p):
                try:
                    os.makedirs(_p, exist_ok=True)
                except OSError:
                    data.pop(_k, None)
    # 声明优先：重装时保留用户已声明的 kb_root（条文47 单源真相·不重探测覆盖）
    _existing = os.path.join(os.path.expanduser(target_cfg), "doenglingz", "runtime_paths.json")
    if os.path.isfile(_existing):
        try:
            with open(_existing, encoding="utf-8") as _ef:
                _ex = json.load(_ef).get("kb_root")
            if _ex:
                data["kb_root"] = os.path.expanduser(_ex)
        except Exception:
            pass

    # 声明优先：重装时保留用户已声明的 diary_root（条文47 单源真相·不重探测覆盖）
    if os.path.isfile(_existing):
        try:
            with open(_existing, encoding="utf-8") as _ef:
                _exd = json.load(_ef).get("diary_root")
            if _exd:
                data["diary_root"] = os.path.expanduser(_exd)
        except Exception:
            pass
    if dry:
        return data, None
    written = mod.write(data)
    return data, written


SYS_FILE_NAMES = ("SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md", "自定义指令")
"""端系统文件的标准名单（step5 合成 / 落点解析 / 段 id 解析 共用单一真源）。
五件=条文32 权威口径（SSOT=01-安装包设计通用规范 条文32＋WB设计哲学02§六）：
SOUL品格/IDENTITY身份/USER画像+童灵/MEMORY导航/自定义指令（执行准则）。
C29 根治（2026-10-15）：第五件旧协议名 customPrompt.md≠条文32 的「自定义指令」，
三个读者（verify.sh／capability 声明／本名单）三套解读=键名漂移病灶；归一后段 id
经 system_file_segments 的 slug 映射保持旧派生值（⛔断章锚点漂移）。"""

# ── 路径覆盖目标：常量名 → 覆盖策略 ─────────────────────────────────
# ⚠️ 端名**只出现在这张表里**（端差异的唯一声明处·cross-platform 单一真源）。
#    公共件 ⛔ 不出现端名；安装器只照单执行。
#
# 三种覆盖策略（⛔ 不可混为一谈——首版全塞成"端家目录"是范畴错误）：
#   ("sentinel",)          作者专属资产·**恒指哨兵**（用户机上本就没有）
#   ("self",)              **包自身落点**（用户把包装哪就指哪）
#   ("end", "<家目录名>")  预留：仅当某常量真的是「某端的**配置**落点」时用
#                          ⚠️ ⛔ **不要**用它覆盖「端里的**脚本**路径」——
#                             脚本在作者侧开发工具里，指向端家目录会让
#                             `exists()` 返 True 而文件并不在 ⇒ 又一条恒真判据。
PATH_OVERRIDE_TARGETS = {
    # ── platform_adaptation_check.py（全部是**作者侧脚本/文档** ⇒ 恒哨兵）──
    "AUTOCLAW_PATROL":      ("sentinel",),
    "LOBSTERAI_PATROL":     ("sentinel",),
    "TRAEWORK_PATROL":      ("sentinel",),
    "DOUBAOWORK_PATROL":    ("sentinel",),
    "DOUBAOWORK_HEARTBEAT": ("sentinel",),
    "DSH_PLUGIN":           ("sentinel",),
    "LOG":                  ("sentinel",),   # 作者侧日志·用户机不需要
    "SSOT":                 ("sentinel",),   # 作者的跨端接入指南文档
    # ── content-gate.py ──
    # ⛔ 原为硬编码作者包路径 ⇒ 用户装别处时闸门扫空目录 = **静默放行一切污染**。
    #    覆盖成"包自身落点"后，闸门在任何安装位置都真跑。**这是本表最有价值的一条。**
    "DEFAULT_PACKAGE":      ("self",),
}


def write_path_override(cfg_root=None, dry=False):
    """生成 `path_override.py`（作者态常量 → 本机实况）。

    **为什么要这张表**：`platform_adaptation_check.py` 等把作者态落点写成
    模块级常量（`AUTOCLAW_PATROL = expanduser("~/个人AI档案/…")`）。
    拷进包后，它们在**任何用户机器上都是错的**，而且因为长得像正常绝对路径，
    **不报错、只是永远指向不存在的地方**——比抛异常更难查。

    **本表只写"本机没有的"**：把这类常量指向哨兵路径（永不存在），
    脚本里原有的 `os.path.exists(...)` 判断照常生效 ⇒ 结果是"该端未接入"，
    **既不崩、也不恒真、还能如实报告"这一端没装"**。

    ⚠️ 端中立：本函数⛔ 不含任何端名特判——端差异由 capability 的
    `path_override_keys` 声明（哪个常量对应哪个端），本函数只照单执行。
    """
    import importlib.util as _il
    po_path = os.path.join(PKG, "references", "scripts", "path_overlay.py")
    if not os.path.isfile(po_path):
        raise RuntimeError("路径覆盖层缺失：%s" % po_path)
    spec = _il.spec_from_file_location("path_overlay", po_path)
    if spec is None or getattr(spec, "loader", None) is None:
        raise RuntimeError("路径覆盖层无法载入：%s" % po_path)
    mod = _il.module_from_spec(spec)
    spec.loader.exec_module(mod)

    target_cfg = os.path.expanduser(cfg_root or _CFG_ROOT_ABS)
    os.environ["BULUOTUO_PATH_OVERRIDE"] = os.path.join(
        target_cfg, "doenglingz", "path_override.py")

    # 按策略逐项算覆盖值
    table = {}
    for const_name, spec in PATH_OVERRIDE_TARGETS.items():
        kind = spec[0]
        if kind == "sentinel":
            table[const_name] = mod.sentinel(const_name)
        elif kind == "self":
            # ⭐ 包自身落点：用户把包装哪就指哪 ⇒ content-gate 闸门任何位置都真跑
            table[const_name] = PKG
        else:  # "end"
            real = os.path.join(os.path.expanduser("~"), spec[1])
            table[const_name] = (real if os.path.exists(real)
                                 else mod.sentinel(spec[1]))
    if dry:
        return table, None
    return table, mod.write_override(table)
"""端系统文件的标准名单（step5 合成 / 落点解析 / 段 id 解析 共用单一真源）。"""


def system_file_targets(cfg_root, cap=None):
    """端系统文件落点解析：读 capability 的 `system_file_paths`，未声明的端回落配置根。

    ⚠️ **为什么需要它（2026-10-02）**：step5 原写死「4 个系统文件 → `[配置根]/`」，
    对扁平配置根的端正确，但存在**混合结构**的端——部分文件在子目录、某个文件
    无载体。写错 ⇒ 文件在盘上但端根本不读，而 verify 只查"文件在不在"
    ⇒ **恒真判据（假绿）**。

    返回 {文件名: 绝对路径 / None / 结构化目标}：
      · None = 该端**无载体**（⛔ 不许写配置根 ⇒ 会成永远不被加载的孤儿文件，
        须由调用方并入主载体）
      · {"file": …, "field": …} = 字段级目标（条文32 形态 `宿主文件::a.b.c`，
        如 WB 设置框字段——⛔ 按普通 md 整写会毁用户配置，调用方须走端设置通道）
      · {"platform": …} = 平台原生载体（`platform://…`，按平台机制信任，无文件目标可写）
    形态解析（C29·2026-10-15）：`~/` 开头=绝对路径声明（expanduser·⛔不拼 config_root）；
    其余相对值=拼 config_root（扁平端向后兼容）。
    端中立性：cap 为 None 或未声明 ⇒ 全部落配置根（**向后兼容**·扁平端行为不变）。
    ⛔ 本函数**不含任何端名特判**：端差异只经 capability 声明进入（见
    `system_file_paths`）。这是端中立性的机械保证——判据见
    `test_system_file_targets.py::t7_endpoint_neutral`。
    """
    paths = (cap or {}).get("system_file_paths") or {}
    out = {}
    for name in SYS_FILE_NAMES:
        rel = paths.get(name, name)          # 未声明 ⇒ 默认配置根（扁平端）
        if rel is None:
            out[name] = None                 # 无载体·调用方并入主载体
            continue
        rel = str(rel)
        if rel.startswith("platform://"):
            out[name] = {"platform": rel}    # 平台托管≠文件目标（verify 侧同口径判信任源）
            continue
        if "::" in rel:                      # 字段级目标：宿主文件 + 字段路径
            fpart, jpart = rel.split("::", 1)
            fpath = os.path.expanduser(fpart) if fpart.startswith("~") \
                else os.path.join(cfg_root, fpart)
            out[name] = {"file": fpath, "field": jpart}
            continue
        out[name] = os.path.expanduser(rel) if rel.startswith("~") \
            else os.path.join(cfg_root, rel)
    return out


def system_file_segments(cap=None):
    """系统文件的断章段 id（宪法 C1）。未声明 ⇒ 按文件名派生稳定 id。"""
    segs = (cap or {}).get("system_file_segments") or {}
    # C29·段 id 防漂移：键名归一只改协议层，未声明时的派生 slug 保持旧值
    # （sys.customprompt 一经断章不可改——改了找不到旧段=半截段事故，见声明该段的端 yaml 段注）
    _SEG_SLUG = {"自定义指令": "customprompt"}
    out = {}
    for name in SYS_FILE_NAMES:
        out[name] = segs.get(name) or "sys." + _SEG_SLUG.get(
            name, name.replace(".md", "").lower())
    return out


def _detect_platform_from_env():
    """G2-2 走查根治·环境自证：平台是机器环境事实，不是调用者声明（S021 声明/验证二分）。
    返回盘上实况命中的 [(端ID, config_root原始值), ...]；显式参数与此对照，缺省时以此为准。
    ⛔本函数只产出"候选+证据"，绝不静默替调用者决定——多/零命中由 main() fail-loud 转人。"""
    hits = []
    adir = os.path.join(PKG, "adapters")
    for pid in sorted(os.listdir(adir)):
        cap_p = os.path.join(adir, pid, "capability.yaml")
        if not os.path.isfile(cap_p):
            continue
        try:
            cr = load_capability(cap_p).get("config_root", "")
        except Exception:
            print("!! adapters/%s/capability.yaml 解析失败——端目录命名漂移/字段缺失在此显形（免疫层判据）" % pid)
            continue
        if not cr:
            print("!! adapters/%s/capability.yaml 缺 config_root 字段（免疫层判据·不静默跳过）" % pid)
            continue
        if os.path.isdir(os.path.expanduser(cr)):
            hits.append((pid, cr))
    return hits

def _emit_receipt(mc, cfg_root, platform, bad=None, pending=None,
                  conflicts=0, hard_err=0):
    """装后调 `install_receipt.py` 产出到货回执（唯一出口·⛔ 禁手写副本）。

    ## 为什么是**子进程**而不是 import
    回执生成器 ⛔ 不 import 安装器（避免装载期依赖倒挂），反向 import 会把
    整个安装器的模块级常量（HOOKS_ROOT/SETTINGS…）拖进回执上下文，
    那样回执的"落点"就依赖安装器的全局态——**正是台账 §1.7「同一事实两套实现」
    的温床**。子进程 = 两个程序各自的解析器互不污染。

    ⚠️ 显式传 `--degrade`/`--pending-manual`：自检发现的缺失与待收尾项
    **必须进回执**（约束3：缺项必须显式告知）。⛔ 不靠"端 AI 自己再查一遍"。
    """
    import subprocess as _sp
    # 回执生成器在包内 references/scripts/（安装器本体在包根·⛔ 两层不是一层）
    script = os.path.join(PKG, "references", "scripts", "install_receipt.py")
    if not os.path.isfile(script):
        print("[receipt] ❌ 回执生成器缺失：%s" % script)
        return 2
    argv = [sys.executable, script, "--platform", platform, "--mc", mc]
    if cfg_root:
        argv += ["--config-root", cfg_root]
    argv += ["--package", PKG]
    for b in (bad or []):
        argv += ["--degrade", "部署后自检缺失：%s" % b]
    if conflicts:
        argv += ["--degrade", "规则层冲突 %d 项（用户文件未被覆盖·需人工裁决）" % conflicts]
    if hard_err:
        argv += ["--degrade", "规则层硬失败 %d 项" % hard_err]
    for p in (pending or []):
        argv += ["--pending-manual", p]
    r = _sp.run(argv, capture_output=True, text=True, timeout=300)
    sys.stdout.write(r.stdout or "")
    if r.returncode not in (0, 1):
        sys.stderr.write(r.stderr or "")
        return r.returncode
    if r.returncode == 1:
        print("[receipt] verdict=failed（必需能力/组件缺失·⛔ 不可视为装好）")
    return 0


def print_install_summary(cfg_root, platform, health=None):
    """安装完成汇总报告（用户侧表格·从 installed_manifest.json 派生·2026-10-03·条文17）。

    结构：
      顶部：一句话结论
      中部：分类汇总表格（资产类别/状态/说明·最多3列·每格≤20字）
      底部：失败项详情（如有）+ 下一步提示

    数据单一真源=installed_manifest.json（机器侧），本函数只做展示层派生，
    ⛔ 不另抄数据、不硬编码数量。
    """
    manifest_path = os.path.join(os.path.expanduser(cfg_root or "~"),
                                  "doenglingz", "installed_manifest.json")
    if not os.path.isfile(manifest_path):
        return  # 回执不存在（dry-run或回执生成失败）→ 不打印汇总
    try:
        with open(manifest_path, encoding="utf-8") as f:
            rec = json.load(f)
    except (OSError, ValueError):
        return

    verdict = rec.get("verdict", "unknown")
    counts = rec.get("counts", {})
    components = rec.get("components", {})
    capabilities = rec.get("capabilities", [])
    degraded = rec.get("degraded", [])
    pending = rec.get("pending_manual", [])

    # ── 顶部：一句话结论 ──
    if verdict == "ok":
        conclusion = "✅ 底座全部通过：资产就位（分身未入职前，整个安装未完成）"
    elif verdict == "degraded":
        conclusion = "🟡 底座就绪（降级）：核心资产通过，%d项待收尾；分身未入职=安装未完成" % len(degraded + pending)
    else:
        conclusion = "❌ 安装未完成：%d项必需能力缺失（含分身件时同样适用「没装他=没装完」）" % counts.get("required_missing", 0)
    print()
    print("━━━━━━━━ 📋 安装报告（底座）━━━━━━━━")
    print(conclusion)
    print()

    # ── 中部：分类汇总表格 ──
    print("【安装清单】")
    print("| 资产类别 | 状态 | 说明 |")
    print("|---|---|---|")
    # 组件侧
    comp_labels = {
        "script_center": ("脚本中心", "脚本中心"),
        "digital_twin": ("数字分身", "数字分身"),
        "rule_data": ("记忆规则", "记忆规则"),
        "runtime_paths": ("运行路径声明", "运行路径"),
        "path_overlay": ("路径覆盖层", "路径覆盖"),
        "plugins": ("插件", "插件"),
    }
    for key, (label, _short) in comp_labels.items():
        c = components.get(key, {})
        status = c.get("status", "unknown")
        if status == "installed":
            print("| %s | ✅ | 就位 |" % label)
        elif status == "missing":
            print("| %s | ❌ | 缺失 |" % label)
        else:
            print("| %s | ⚪ | %s |" % (label, status))
    # 能力侧（只列required+installed的，简化展示）
    req_installed = [i for i in capabilities if i.get("severity") == "required" and i.get("status") == "installed"]
    req_missing = [i for i in capabilities if i.get("severity") == "required" and i.get("status") == "missing"]
    if req_installed:
        print("| 端能力(必需) | ✅ | %d/%d就位 |" % (len(req_installed), len(req_installed) + len(req_missing)))
    if req_missing:
        print("| 端能力(必需) | ❌ | 缺%d项 |" % len(req_missing))

    # ── 底部：失败项/待收尾 + 下一步 ──
    if degraded or pending:
        print()
        print("⚠️ 待手动收尾（不影响已装功能）：")
        for i, item in enumerate(degraded + pending, 1):
            print("  %d. %s" % (i, item[:80]))

    # 本端能力对照（**数据源 = adapters/<端>/capability.yaml·唯一真源**·2026-10-03 补）
    # ⚠️ 为什么补这一段：「装完你得到什么」此前只在安装**开头**说过（Step -0.9），
    #    装**完**只给资产表（组件/能力键），⛔ 用户拿不到"我这端拿到了什么"的人话版。
    #
    # 🔴 **⛔ 不读 CAPABILITY-MATRIX.md**（首版就是这么写的，当场翻车）：
    #   ① 它是**派生数据**（由 gen_capability_matrix.py 生成），⛔ 不是真相；
    #   ② 列位是**位置依赖**的——按 `_cells[_col]` 取值，_cells[0] 是能力名、数据从 1 开始，
    #      ⛔ 硬编码列号必然错位（首版实测：WB 端把 Trae Work 的值当成自己的报出来）；
    #   ③ 表头显示名（AutoClaw/豆包办公/ZCode）与 platform id 不是一一对应 ⇒ 还得维护映射表。
    #   ⇒ 正解：直接读本端 capability.yaml 的 capabilities + missing_semantics，
    #      ⛔ 零列位依赖 · ⛔ 零映射表 · 加端自动正确。
    _cap_path = os.path.join(PKG, "adapters", platform, "capability.yaml")
    if os.path.isfile(_cap_path):
        try:
            _cap = load_capability(_cap_path)
            _caps = _cap.get("capabilities") or {}
            _sem = _cap.get("missing_semantics") or {}
            if _caps:
                print()
                print("【本端能力对照】（数据源 = adapters/%s/capability.yaml）" % platform)
                print("| 这台机器能做的事 | 支持 | 不支持会怎样 |")
                print("|:---|:---:|:---|")
                for _k, _v in _caps.items():
                    _on = bool(_v)
                    _s = str(_sem.get(_k, "")).strip()
                    # required = 缺了用不了布洛陀本体；optional = 少一块功能（属正常态）
                    _impact = ("🔴 缺了用不了本体" if _s == "required"
                               else "🟡 少一块功能（属正常态）")
                    print("| %s | %s | %s |" % (_k, "✅" if _on else "⚪ 不涉及", _impact if _on else "—"))
                print("> ✅ 端声明支持 · ⚪ 本端形态上不涉及（⛔ 不是缺陷）· 语义按 capability 的 missing_semantics")
        except Exception as _e:
            print("   [i] 本端能力对照读取跳过：%s" % _e)

    # 下一步提示（基于体检结果和分身状态）
    print()
    print("📌 下一步：")
    if health and health.get("assets", {}).get("数字分身·已造芯"):
        print("  你的数字分身已在位，无需重复造芯。")
    else:
        print("  造出你的数字分身（答题→填模板→跑生成器），详见数字分身/onboarding/入门指南-通用版.md")
    # 记忆琥珀双轨 + 知识联邦（2026-10-03 补·原 step6.5/INSTALL 有话术但装完总账里没有）
    print("  记忆琥珀已就位：每天自动备份只留 7 天；想永久留住的，说「帮我永久保存某某文件」")
    _kb_min_n = len([f for f in os.listdir(os.path.join(PKG, "references", "知识联邦引擎-min", "scripts"))
                    if f.endswith(".py")])
    print("  知识联邦引擎（抽卡/撞卡）已装核心 %d 件：完整版大半是运行数据缓存，对你没用还占地方，故只装核心" % _kb_min_n)
    if platform == "doubaowork":
        print("  豆包办公端：将 ~/.doubaowork-config/doubaowork-paste.md 粘贴到「设置→工作模式任务设置→工作任务偏好指令」并保存（该框上限10000字符，paste.md约4700字，剩余空间充足）")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


def main():
    # ─── v2.0 多平台分发：--platform 参数 ───
    _plat_ap = argparse.ArgumentParser(add_help=False)
    _plat_ap.add_argument("--platform", default="workbuddy", help="目标平台(默认workbuddy=向后兼容)")
    # 🔴 2026-10-04 根治「隔离装污染真机声明」：
    #   病根 —— cfg_root 硬从 capability.yaml 读（如 `~/.hermes`），
    #   **⛔ 无 CLI 覆盖入口** ⇒ 隔离/夹具装（闸5 干净用户机）必然把
    #   `<cfg_root>/doenglingz/runtime_paths.json` 写成临时 MC 路径
    #   （实测：真机 12 键 → 5 键·worklog 缺失·后续只读闸全红）。
    #   ⇒ 覆盖参数 + 显形声明，隔离装从此**不碰真机配置根**。
    _plat_ap.add_argument("--cfg-root", default=None,
                          help="覆盖端配置根（隔离装/夹具用·⛔ 不传则读 capability.yaml）")
    _platform_explicit = any(a == "--platform" for a in sys.argv)  # G2-2·显式/缺省分轨（while 清除前判定）
    # F3/F21（2026-10-17）：查询模式（--list/--verify）不需要端上下文——ROSTER 是全局数据。
    _QUERY_MODE = ("--list" in sys.argv) or ("--verify" in sys.argv) or ("--sweep-ghost" in sys.argv)
    _plat_args, _ = _plat_ap.parse_known_args()
    # 从 argv 中清除 --platform 避免主 parser 报 unrecognized
    while "--platform" in __import__("sys").argv:
        i = __import__("sys").argv.index("--platform")
        __import__("sys").argv[i:i+2] = []
    if _plat_args.cfg_root:
        while "--cfg-root" in __import__("sys").argv:
            i = __import__("sys").argv.index("--cfg-root")
            __import__("sys").argv[i:i+2] = []
    global HOOKS_ROOT, SETTINGS, _PLATFORM_ID, _CFG_ROOT_ABS
    # ─── G2-2 根治·缺省不再静默回落 workbuddy：环境自证 + fail-loud 转人 ───
    _env_hits = _detect_platform_from_env()
    if not _platform_explicit:
        # F21（2026-10-17）：--list 是只读查询（ROSTER 全局·不依赖端），旧逻辑在多端机
        # 被 fail-loud 拦住 ⇒ 用户连钩子总表都查不了。查询模式跳过判定（--verify 仍需端
        # 上下文·保持 fail-loud）。
        if _QUERY_MODE and "--verify" not in sys.argv and len(_env_hits) != 1:
            _plat_args.platform = "workbuddy"
            print("ℹ️ 查询模式（--list）：跳过平台判定（钩子总表为全局数据·不依赖端上下文）")
        elif len(_env_hits) == 1:
            _plat_args.platform = _env_hits[0][0]
            print("🔌 平台自动判定：%s（依据：盘上唯一命中 config_root %s）" % _env_hits[0])
        elif len(_env_hits) == 0:
            print("❌ 未在本机发现任何端 config_root（全新机？）——拒绝按静默缺省装错端。")
            print("   请按 INSTALL Step -0.5 运行时进程证据显式传 --platform <端ID>；确为 WorkBuddy 端请显式传 --platform workbuddy。")
            sys.exit(2)
        else:
            print("❌ 本机共存多个端 config_root，机器无法自证本次在给哪个端装——拒绝静默择一：")
            for _pid, _cr in _env_hits:
                print("   · %s → %s" % (_pid, _cr))
            print("   请显式传 --platform <本次实际在装的端ID>（依据=运行时进程证据）。")
            sys.exit(2)
    elif len(_env_hits) == 1 and _env_hits[0][0] != _plat_args.platform:
        print("⚠️ 盘上环境探测命中 %s（%s），本次显式指定 %s——按显式部署；若显式值为误传，请核对运行时进程证据（判定依据已显形可抽检）。"
              % (_env_hits[0][0], _env_hits[0][1], _plat_args.platform))
    # 非 hook 端：只跳过 ②③（钩子搬运/注册）；①脚本中心 / ①a数字分身 / ①b规则层 与端无关，
    # 照常部署（2026-09-30 根治：此前委派后 sys.exit(0) 把公共资产一并吞掉——
    # 矩阵标 ✅完整、INSTALL.md 承诺「脚本体系一次装齐」，实装却零脚本零分身＝假绿）
    _skip_hooks = False
    # 端 setup 退出码约定：0=全成功；3=文件已全量落盘·仅「待手动收尾项」（如受限的 launchd 注册）
    #   未完成——降级不阻塞（条文16），安装器继续装公共资产；其余非零=真失败（中止）
    _pending_manual = []
    _delegate_fail = None  # 端 setup 退出码（非 0/3）·收尾非零上报·⛔不中止公共资产部署
    if _plat_args.platform != "workbuddy":
        # 读 capability.yaml
        cap_path = os.path.join(PKG, "adapters", _plat_args.platform, "capability.yaml")
        if not os.path.isfile(cap_path):
            print(f"❌ 平台 {_plat_args.platform} 不存在: {cap_path}"); sys.exit(2)
        cap = load_capability(cap_path)
        cfg_root = os.path.expanduser(cap.get("config_root", "~/.unknown"))
        if _plat_args.cfg_root:
            # 隔离装/夹具显式覆盖（2026-10-04）·⛔ 默认不覆盖真机配置根
            cfg_root = os.path.abspath(os.path.expanduser(_plat_args.cfg_root))
            print("[cfg-root] 覆盖为 %s（隔离装·不碰真机声明）" % cfg_root)
        HOOKS_ROOT = os.path.join(cfg_root, "hooks")
        SETTINGS = os.path.join(cfg_root, "settings.json")
        _PLATFORM_ID = _plat_args.platform
        _CFG_ROOT_ABS = cfg_root
        # v2.0.1 端专属钩子（数据化·capability.extra_hooks·ROSTER 唯一数据源不变·
        # deploy/注册/核查三处循环自动覆盖，不另抄清单）
        for _er in (cap.get("extra_hooks") or []):
            ROSTER.append(tuple(_er))
        # ⚠️ 2026-10-03 回归修正：委派只属安装模式——--verify/--list/--help/--gate 是查询面，
        #    走委派会把端 setup 真跑一遍（本端实测 --verify 触发了完整安装流程输出）。
        _install_mode = not any(a in sys.argv for a in ("--verify", "--list", "-h", "--help", "--gate", "--sweep-ghost"))
        # 钩子形态分派：hooks_event=false → 跳过标准钩子注册（端钩子由端 setup 自管·条文8）
        if not cap.get("capabilities", {}).get("hooks_event", False):
            _skip_hooks = True
            if cap.get("capabilities", {}).get("hooks_alternative", False):
                print(f"ℹ️ 本端({_plat_args.platform})为非标准 hook 机制({cap.get('hooks_mechanism', 'extensions/patrol')})·不走标准钩子注册，钩子由端 setup 部署")
            else:
                print(f"⚠️ 本端({_plat_args.platform})无 hook 机制·跳过标准钩子部署/注册")
        else:
            print(f"📦 目标平台: {cap.get('display_name', _plat_args.platform)} · 配置根: {cfg_root}")

        if _install_mode:
            # ─── 端 setup 委派 = 所有非占位端的公共步骤（2026-10-03 条文13扩展·与钩子形态解耦）───
            # 旧逻辑只在 hooks_alternative=true 时委派 ⇒ hermes(hooks_event=true)/doubaowork
            # (hooks_alternative=false) 的端部署脚本永不执行——状态表「✅完整」实装零端件（假绿·条文5）。
            # 新逻辑：一律查 install_entry（缺省回退 setup.sh，兼容 autoclaw 等既有端）；端确不适用
            # 自动委派须显式声明 setup_dispatch: manual（⛔静默不委派=隐式假绿回归）。
            _caps = cap.get("capabilities", {})
            entry = _caps.get("install_entry") or cap.get("install_entry") or "setup.sh"
            alt_setup = os.path.join(PKG, "adapters", _plat_args.platform, entry)
            if (_caps.get("setup_dispatch") or cap.get("setup_dispatch")) == "manual":
                print(f"ℹ️ 本端({_plat_args.platform})声明 setup_dispatch: manual——端专属部署由端 AI 按 adapters/{_plat_args.platform}/ 内文档执行（显式声明·非静默跳过）")
            elif os.path.isfile(alt_setup):
                import subprocess as _sp
                mech = cap.get("hooks_mechanism", "extensions/patrol")
                mc_arg = sys.argv[-1] if sys.argv[-1] and not sys.argv[-1].startswith("-") else ""
                _sp_cmd = ["bash", alt_setup]
                _env = dict(os.environ)
                # 🔴 2026-10-11 沙箱实测逮到的真污染：本委派从不传 cfg_root ⇒ setup.sh 回落
                #   它自己的默认值 `$HOME/.hermes` ⇒ 隔离验证时插件/备份/三关闸门全落在
                #   **真机运行面**（实测：真机 plugins 被包内投影覆写、doenglingz/backups 多出
                #   一份、__pycache__ 重生）。铁律「会写运行面的闸须带隔离 cfg_root」的**委派侧**
                #   欠账——闸自身有 --cfg-root，委派时没透传 = 隔离链断在中间。
                #   setup.sh 的取值入口 = DOENGLINGZ_CONFIG_DIR（其 L17·缺省 $HOME/.hermes）。
                if _CFG_ROOT_ABS:
                    _env["DOENGLINGZ_CONFIG_DIR"] = _CFG_ROOT_ABS
                # C30（2026-10-15）：装机链自证标志——安装器自己知道「此刻 MC 本就该是空的/未成型」
                # （INSTALL 主命令场景：新手先建空文件夹再跑）。端 setup 见此标志把空/未成型 MC
                # 判 ⏳ 中途态继续落端件；⛔ 非空且无指纹仍硬拒（人直跑 setup.sh 无此标志=原守卫完整）。
                _env["BLT_INSTALL_CHAIN"] = "1"
                if "--dry-run" in sys.argv:
                    # dry-run 双通道穿透：DRY=1 环境变量（traework/qodercn 等读环境变量）+
                    # --dry-run 位置参数（doubaowork/hermes 读参数）——⛔不许"看着像演练、实际写盘"
                    _sp_cmd.append("--dry-run")
                    _env["DRY"] = "1"
                if mc_arg:
                    _sp_cmd.append(mc_arg)
                print(f"ℹ️ 委派端部署入口 {entry}（install_entry 单一真源·条文13·所有非占位端统一委派）")
                rc = _sp.run(_sp_cmd, env=_env).returncode
                if rc == 3:
                    # 端 setup 退出码 3 = 文件已全量落盘·仅「待手动收尾项」(受限的 launchd 注册)未完成
                    # → 降级不阻塞(条文16)：记入 _pending_manual，继续装公共资产（⛔不整体中止）
                    _pending_manual.append(
                        "%s 端 %s：规则/分身核/patrol 脚本已落盘·仅「%s」注册待手动收尾"
                        "（按上方命令在系统终端执行）" % (_plat_args.platform, entry, mech))
                    print("   ⚠️ 端 setup(%s) 退出码 3：文件已全量落盘·仅 %s 注册待手动收尾"
                          "（降级不阻塞·公共资产继续部署）" % (entry, mech))
                elif rc not in (0, None):
                    # 2026-09-30 根治：端接入失败**不再中止**公共资产部署（降级不阻塞·对齐 rc==3 先例）。
                    # 公共资产（脚本中心/分身套件/规则层）与端接入解耦——端 setup 失败时仍落盘，
                    # 收尾以非零码显式上报（⛔非假绿：失败进 _pending_manual + 末尾 return 非零）。
                    _delegate_fail = rc
                    _pending_manual.append(
                        "%s 端 %s：退出码 %d·端接入未完成（公共资产继续部署·请在 %s 端真机复核）"
                        % (_plat_args.platform, entry, rc, _plat_args.platform))
                    print(f"   ❌ 端 setup({entry}) 退出码 {rc}·端接入未完成（降级不阻塞·公共资产继续部署·需在 {_plat_args.platform} 端复核）")
                    # C30遗留③裁决(2026-10-16·用户令按愿景最优解)：维持"解耦部署"设计（公共资产
                    #   与端接入正交·部分成功优于全失败），强化出口告知——误指目录的用户须看得见撤回路。
                    print(f"   ↳ 若本目录系误指：公共资产已落在 {mc_arg or '<MC>'}，可用包根 rollback.sh 撤回本次写入后重跑（端拒≠MC合法，两问分开核）")
                # 委派成功 ≠ 全装完——继续走下面的公共资产部署（①/①a/①b）
            else:
                print(f"⚠️ 本端({_plat_args.platform})未找到端部署入口 {entry}，且 capability 未声明 setup_dispatch: manual——端适配面不完整，请核对该端 adapter")

        else:
            # F3（2026-10-17）：本 else 配对的是「platform != workbuddy」——是 **WB 分支**
            # （WB 无独立 setup 入口·能力内建安装器本体），原文案"查询模式"在真实 WB 安装时
            # 也打印=误导。查询模式的判定在下方 _QUERY_MODE。
            if not _QUERY_MODE:
                print("ℹ️ WorkBuddy 端：无独立 setup 入口（端能力内建安装器本体·直接部署）")
    # ── 端自定义安装后喊话（2026-10-03·修：原挂在 `platform != "workbuddy"` 分支内
    #    ⇒ **WorkBuddy 端永远走不到这里·自己的 post_install_message 永远不打印**。
    #    根因：当日把喊话从 hooks_event 分支移出时，落点连同整个块一起留在了非 WB 分支内。
    #    ⛔ 端中立：任何端声明了 post_install_message 都要在安装终端呈现（WB 端尤其——
    #    它的自定义指令是「设置框字段」形态，用户看不到就等于没装）。
    _cap_for_msg = cap if _plat_args.platform != "workbuddy" else load_capability(
        os.path.join(PKG, "adapters", "workbuddy", "capability.yaml"))
    _msg = _cap_for_msg.get("post_install_message")
    if _msg and not _QUERY_MODE:  # F3：--list/--verify 只读查询真跳过喊话（旧版无条件打印）
        print()
        print(_msg)
    # ─── 以下为 WorkBuddy/有hook端的原有逻辑（HOOKS_ROOT/SETTINGS 已按需覆盖）───
    global MC_PATH
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mc", nargs="?", help="记忆共享中心绝对路径")
    ap.add_argument("--dry-run", action="store_true", help="只报告不写盘")
    ap.add_argument("--list", action="store_true", help="只打印钩子总表")
    ap.add_argument("--deploy-skills", action="store_true",
                  help="程序化部署 Skill 面（逐件复制+占位符本地化+覆盖前损失清单）·2026-10-11 批次8")
    ap.add_argument("--verify", action="store_true", help="核对已装态（文件落盘 + 已注册；带 MC 路径时再核规则数据）")
    ap.add_argument("--gate", action="store_true",
                    help="发版前置门禁（用户令·2026-10-03）：端适配 100%% 才放行打包——调 platform_adaptation_check.py --gate")
    ap.add_argument("--sweep-ghost", nargs="?", const="", default=None, metavar="HOME",
                    help="只跑装后幽灵目录清扫（tiger① 存量根治·真机验证用）：扫描 HOME 根与 MC 根的字面 [记忆共享中心] 目录并移动到 .install/ghost-sweep 备份（⛔不删除）")
    a = ap.parse_args()
    if getattr(a, "deploy_skills", False):
        _mc0 = a.mc or MC_PATH
        _d, _s, _l = deploy_skills(os.path.expanduser(str(_mc0)), dry=a.dry_run)
        print("④ Skill 面程序化部署：落位 %d 件 · 幂等跳过 %d 件 · 本机改动待覆盖 %d 件" % (_d, _s, _l))
        # P11 根治（2026-10-19）：端 setup.sh 委派的 [4/5] 建链跑在④落位之前（时序倒置恒 0/10 却 rc=0）
        # ⇒ 落位后对有 setup.sh 的端触发 --relink-skills 复链巡检；不足 10 判非零，⛔ rc=0 收场
        if not a.dry_run and _plat_args.platform not in (None, "", "workbuddy"):
            _sh = os.path.join(PKG, "adapters", str(_plat_args.platform), "setup.sh")
            if os.path.isfile(_sh):
                import subprocess as _sp2
                # F5（审查 2026-10-19）：委派三件套=expanduser + 隔离 cfg_root env + 链内标志，
                # 与 L2618 沙箱污染铁律同口径；缺 BLT_INSTALL_CHAIN 会把合法中途态误判硬拒。
                _env2 = dict(os.environ)
                _env2["BLT_INSTALL_CHAIN"] = "1"
                if _CFG_ROOT_ABS:
                    _env2["QODERCN_HOME"] = _CFG_ROOT_ABS
                _rr = _sp2.run(["bash", _sh, os.path.expanduser(str(_mc0)), "--relink-skills"], env=_env2)
                if _rr.returncode != 0:
                    print("!! Skill 复链巡检失败（rc=%d）：落位后软链必须 10/10 在位（P11）" % _rr.returncode)
                    sys.exit(1)
                print("✅ Skill 复链巡检通过（落位后 [4/5] 重跑·10 链在位）")
        sys.exit(0)

    if a.verify:
        return verify_deployed(a.mc, hooks_root=HOOKS_ROOT, settings_path=SETTINGS)

    if a.gate:
        return gate_check(_plat_args.platform)

    if getattr(a, "sweep_ghost", None) is not None:
        _home = os.path.expanduser(a.sweep_ghost or "~")
        _mc = os.path.expanduser(a.mc or "") or _home
        return _sweep_ghost_mc(mc=_mc, home=_home, dry=a.dry_run)

    if a.list:
        print("%-18s %-8s %-28s %s" % ("事件", "落位", "主件", "依赖"))
        for ev, loc, sd, main, deps in ROSTER:
            print("%-18s %-8s %-28s %s" % (ev, "hooks/"+loc if loc != "." else "hooks", main, " ".join(deps) or "-"))
        print("\n共 %d 个钩子（事件分布：%s）" % (
            len(ROSTER),
            ", ".join("%s=%d" % (e, sum(1 for r in ROSTER if r[0] == e))
                      for e in dict.fromkeys(r[0] for r in ROSTER))))
        return 0

    MC_PATH = (a.mc or "").rstrip("/")
    if not MC_PATH:
        print("用法：python3 install_scripts.py \"<记忆共享中心绝对路径>\"  [--dry-run]")
        return 2
    if not os.path.isabs(MC_PATH):
        print("!! 记忆共享中心必须是绝对路径：%s" % MC_PATH)
        return 2

    tag = "[dry-run] " if a.dry_run else ""
    print("%s记忆共享中心 = %s" % (tag, MC_PATH))

    # ─── 🔴 安装前端体检报告（2026-10-03·条文20/21）：检测端之后、部署之前 ───
    # 扫描已有资产→输出新/老/跨端用户身份+缺失清单+端能力+建议操作
    # 查询模式（--verify/--list）跳过体检（那是查询面不是安装面）
    # 2026-10-08 zwork 形态修正（D3 验收轮）：平台托管型五系统文件=端自有实体（条文48），
    # ⛔按 _CFG_ROOT_ABS（WB 落点）拼检=判据面与落点面不相交（沙盒实测 0/4 假红·verdict 仍 ok
    # 但【已有资产】四红误导端 AI 判用户身份）。传 None→函数内回落 mc+platform 锚点通道。
    _health_cfg_root = None if _plat_args.platform == "zwork" else _CFG_ROOT_ABS
    _health = pre_install_health_check(
        MC_PATH, _plat_args.platform,
        cap=locals().get("cap"),
        cfg_root=_health_cfg_root,
        dry=a.dry_run,
    )

    # 知识库骨架（2026-10-06 E2E⑤ record_card_trigger 末层归因）：`knowledge` 键消费面要求
    #   安装器写 runtime_paths 时目录存在（exists_check 跳缺目录 ⇒ 键缺=端用户 PathKeyMissing）；
    #   空目录=端侧 sucair/立场卡合法写入落点·⛔个人数据不入（P-2 投影边界）
    if not a.dry_run:
        os.makedirs(os.path.join(MC_PATH, "知识库"), exist_ok=True)
    n_center = deploy_script_center(MC_PATH, a.dry_run)
    _sc_dst = os.path.join(MC_PATH, "脚本中心")
    _sc_landed = sum(len(fs) for _r, _d, fs in os.walk(_sc_dst)) if os.path.isdir(_sc_dst) else 0
    print("%s① 脚本中心：清单 %d 条·落盘 %d 件 → %s/脚本中心/（知识联邦引擎独立部署 → %s/知识联邦引擎/）"
          % (tag, n_center, _sc_landed, MC_PATH, MC_PATH))
    # 2026-10-07 冲突显形化收口：deploy_script_center 检测到同名异内容时写 _PKG_CONFLICTS，
    #   此处决定是否中止安装。
    #   ⚠️ 本轮**只报告不阻断**——理由：现包存量 52 处冲突（27 处 scripts 侧受 manifest 管、
    #   25 处两侧均未受管·真源待定），开阻断会让**所有端用户立刻装不上**，
    #   那是把「拿到旧版」换成「装不上」·负担更大。
    #   ⇒ 分两步：①先恢复装机可用（本行只报）②存量清完后由 _BLUOLUO_PKG_CONFLICT_STRICT 切硬阻断。
    #   开关真源=环境变量 _BLUOLUO_PKG_CONFLICT_STRICT（2026-10-07 清账完成·默认开·=0 显式关）。
    #   留此开关而非删代码：⛔ 阻断机制必须先于存量清理存在，否则清完账又会被下一个副本破功。
    if _PKG_CONFLICTS:
        _strict = os.environ.get("_BLUOLUO_PKG_CONFLICT_STRICT", "1") == "1"
        if _strict and not a.dry_run:
            print("!! 安装中止：脚本中心存在 %d 处同名异内容冲突（见上）。" % len(_PKG_CONFLICTS))
            print("!! 端用户装到未声明的版本比装不上更坏 —— 请先清副本或补 manifest 登记。")
            sys.exit(1)
        print("ℹ️ 冲突阻断已被环境变量显式关闭（_BLUOLUO_PKG_CONFLICT_STRICT=0）·存量 %d 处仅报告"
              % len(_PKG_CONFLICTS))
    # 脚本中心真源唯一·各端调用方式告知（2026-10-03·条文13）
    if _skip_hooks:
        print("   ℹ️ 脚本中心真源在 %s/脚本中心/·本端无 hook 机制·守卫靠端专属Skill内嵌校验实现（非独立hook进程）·脚本可手动调用" % MC_PATH)
    else:
        print("   ℹ️ 脚本中心真源在 %s/脚本中心/·钩子已注册指向真源（不复制副本）" % MC_PATH)

    n_dt = deploy_digital_twin(MC_PATH, a.dry_run)
    print("%s①a 数字分身套件：%d 件 → %s/数字分身/{%s}/"
          % (tag, n_dt, MC_PATH, ",".join(DT_SUITE.keys())))
    for _bs in bootstrap_runtime_state(MC_PATH, a.dry_run):
        print("   %s①a+ 运行落点自举：%s" % (tag, _bs))

    rd = install_rule_data(MC_PATH, a.dry_run)
    rf = install_rule_files(MC_PATH, a.dry_run)
    # 装后清扫（tiger① 存量根治·2026-10-20）：字面 `[记忆共享中心]` 幽灵目录 → 移入备份（⛔不删除）
    _sweep_ghost_mc(mc=MC_PATH, home=os.path.expanduser("~"), dry=a.dry_run)
    _st = {"CREATED": "新建", "UPDATED": "更新", "UNCHANGED": "无变化",
           "CONFLICT": "⚠️冲突", "MERGE_ERROR": "❌硬失败",
           "PRECHECK_SKIP": "⚠️号位预检·未写"}
    n_conflict = n_err = 0
    # ── 运行路径声明（插件/脚本的唯一取路径入口）──────────────────
    # 🔴 **cap 必须在这里可及**（2026-10-02 dry-run 抓出）：
    #   上一阶段遗留 `a.cap`（argparse 里**从来没有** --cap 这个参数）
    #   ⇒ Namespace 无该属性 ⇒ write_runtime_paths 抛 AttributeError
    #   ⇒ 该异常被外层 try 吞成"[runtime_paths] ❌"，**降级不阻塞**
    #   ⇒ 用户看到的是"路径声明没生成"，但安装继续往下跑（假绿）。
    #   修法：用主流程已加载的 `cap`（L973 `cap = load_capability(...)`），
    #   并在 workbuddy 分支显式兜 None——⛔ 不再用不存在的 argparse 属性。
    try:
        rpd, rpw = write_runtime_paths(
            MC_PATH, locals().get("cap"), cfg_root=_CFG_ROOT_ABS, dry=a.dry_run)
        print("[runtime_paths] %s（%d 键）" % (rpw or "(dry-run)", len(rpd)))
    except Exception as e:
        print("[runtime_paths] ❌ %s" % e)
        n_err += 1
    # ── 路径覆盖层：把作者态常量改成本机实况（防"指向不存在处却不报错"）──
    try:
        # 🔴 **返回值是二元组 (table, written_path)**（2026-10-02 修）：
        #   旧版 `ovl_written = write_path_override(...)` 把整个 tuple
        #   交给 `"%s" % (ovl_written or ...)` ⇒ TypeError:
        #   not all arguments converted during string formatting
        #   ⇒ 被 except 吞成"[path_overlay] ❌"，而**函数其实成功了**——
        #   报错的是调用方。这是"异常信息指向错误对象"的实例：
        #   看 `[path_overlay] ❌` 会误判成"覆盖层生成失败"，实际它已在盘上。
        _ovl_table, _ovl_path = write_path_override(
            cfg_root=_CFG_ROOT_ABS, dry=a.dry_run)
        print("[path_overlay] %s" % (_ovl_path or "(dry-run · 表已算 %d 项)"
                                      % len(_ovl_table)))
    except Exception as e:
        print("[path_overlay] ❌ %s" % e)
        if os.environ.get("BULUOTUO_TRACEBACK"):
            import traceback as _tb
            _tb.print_exc()
        n_err += 1
    # 断章增量状态逐项排印（C7：冲突/硬失败必须让用户看见，⛔ 不静默吞）
    _st = {"CREATED": "新建", "UPDATED": "更新", "UNCHANGED": "无变化",
           "CONFLICT": "⚠️冲突", "MERGE_ERROR": "❌硬失败",
           "PRECHECK_SKIP": "⚠️号位预检·未写"}
    n_conflict = n_err = 0
    for _name, _stt, _msg in rf:
        print("   · %s：%s" % (_name, _st.get(_stt, _stt)))
        if _stt == "CONFLICT":
            n_conflict += 1
            print("     └ %s（你的文件未被改动·请人工裁决）" % _msg)
        elif _stt == "MERGE_ERROR":
            n_err += 1
            print("     └ %s" % _msg)
        elif _stt == "PRECHECK_SKIP":
            n_conflict += 1
            print("     └ %s（你的文件未被改动）" % _msg)
    print("%s①b 规则层：触发规格 %s + 三层规则文件 %d 件 → %s/记忆规则/（断章增量·⛔不覆盖你的改动）"
          % (tag, ", ".join(rd) if rd else "（包内无）", len(rf), MC_PATH))
    if n_conflict or n_err:
        print("   ⚠️ 规则层：%d 项冲突 · %d 项硬失败 —— 用户文件均未被覆盖（写入件才有备份："
              "记忆琥珀/安装前备份/；纯冲突=零写入·原文即在盘上）" % (n_conflict, n_err))

    if _skip_hooks:
        print("%s②③ 钩子部署/注册：跳过（本端无 hook 事件·端适配承载非标准机制·公共资产已装）" % tag)
    else:
        deployed, missing = deploy_hooks(a.dry_run)
        print("%s② 钩子部署：%d 件 → %s/" % (tag, len(deployed), HOOKS_ROOT))
        if missing:
            print("   !! 包内缺失（应报缺陷）：%s" % ", ".join(missing))

        _rh = register_hooks(deployed, a.dry_run)
        if _rh[0] == -1:
            print("!! ③ 注册失败：settings.json 不可用（上方报错）——钩子面未注册，rc 判红（P08 假绿根治）")
            return 1
        added, migrated, skipped = _rh
        if not missing:
            write_guard_baseline(deployed, a.dry_run)
            write_hook_fingerprints(deployed, a.dry_run)  # P12：内容指纹第三层基线
        else:
            print("!! 包内缺失在列 → 跳过基线写入（装机器缺陷不算到用户头上·C4-D GIGO闸）")
        print("%s③ 钩子注册：新增 %d · 迁移纠正 %d · 已存在跳过 %d → %s" % (tag, added, migrated, skipped, SETTINGS))

    # 写版本快照（供升级时组件级对比）— dry-run 也打印，不写盘
    write_user_versions(MC_PATH, a.dry_run)

    if a.dry_run:
        print("[dry-run] 跳过部署后自检（未写盘）")
        return 0

    # 自检：登记进 settings.json 的每个钩子 + 依赖件，是否真的在盘上
    # （非 hook 端本就未部署钩子 → 跳过本腿，⛔不把"设计不装"报成缺陷）
    bad = []
    if not _skip_hooks:
        for ev, loc, sd, main, deps in ROSTER:
            dst_dir = HOOKS_ROOT if loc == "." else os.path.join(HOOKS_ROOT, loc)
            for fname in [main] + list(deps):
                if not os.path.isfile(os.path.join(dst_dir, fname)):
                    bad.append("%s/%s" % (loc, fname) if loc != "." else fname)
    # 自检：数字分身套件是否落盘（Skill 正文引用它们·缺＝端用户跑 Skill 即断）
    for sub, files in DT_SUITE.items():
        sdir = os.path.join(MC_PATH, "数字分身", sub)
        if files is None:
            if not os.path.isdir(sdir):
                bad.append("数字分身/%s/（整目录缺失）" % sub)
            continue
        for name in files:
            if not os.path.isfile(os.path.join(sdir, name)):
                bad.append("数字分身/%s/%s" % (sub, name))
    # 自检：规则层（触发规格 + 三层规则文件）是否就位——缺任一件硬墙都会静默/报错
    for name in RULE_DATA + RULE_FILES:
        if not os.path.isfile(os.path.join(MC_PATH, "记忆规则", name)):
            bad.append("记忆规则/%s" % name)
    # R2 填后语法门禁（2026-10-11 _fill 转义雷根治卡）：被填 .py/.json 编译级复检
    bad.extend(fill_syntax_guard())
    if bad:
        print("!! 部署后自检发现缺失/语法雷 %d 件：%s" % (len(bad), ", ".join(sorted(set(bad)))))
        return 1
    if _skip_hooks:
        print("✅ 部署后自检：脚本中心 + 数字分身套件 + 规则数据全部落盘"
              "（钩子本端不适用·由端适配承载）")
    else:
        print("✅ 部署后自检：%d 个钩子 + 依赖件 + 规则数据全部落盘" % len(ROSTER))

    # ─── 🔴 到货回执（装后唯一出口·⛔ 禁手写副本）──────────────────
    # 放在**部署后自检之后**：自检的 `bad` 列表此时已算出，正是回执的原料。
    # ⚠️ dry-run **不写回执**——回执的语义是"到货了"，演练时写它=假到货。
    if a.dry_run:
        print("[dry-run] 跳过安装回执（未写盘·回执语义=到货·演练写它即假到货）")
    else:
        _rc = _emit_receipt(MC_PATH, _CFG_ROOT_ABS, _plat_args.platform,
                            bad=bad, pending=_pending_manual,
                            conflicts=n_conflict, hard_err=n_err)
        if _rc != 0:
            print("⚠️ 安装回执生成返回 rc=%d（见上方报错）·⛔ 回执缺失即'装成什么样'不可查" % _rc)
        # ─── 安装完成汇总报告（用户侧表格·从回执JSON派生·2026-10-03）───
        if not a.dry_run:
            print_install_summary(_CFG_ROOT_ABS, _plat_args.platform, health=_health)

    # ─── 待手动收尾项（条文16 降级不阻塞·⛔不静默：显式告知，否则端用户不知道 patrol 未注册）───
    if _pending_manual:
        print()
        print("━━━━━━━━ ⚠️ 待手动收尾项（不影响上面已落盘的功能·降级不阻塞）━━━━━━━━")
        for _it in _pending_manual:
            print("  · %s" % _it)

    # ─── 统一下一步：造你自己的数字分身（全端通用·与端接入机制无关）───
    #   造芯流程所有端一致（单一真源）；端差异只在 adapters 接入，已在上面完成。
    #   🔴 2026-10-03 跨端共享：先检测是否已在其他端造过芯——
    #      已有分身 → 跳过造芯提示，只做端接入；无分身 → 才打印造芯三步。
    ob = os.path.join(MC_PATH, "数字分身", "onboarding")
    dt_root = os.path.join(MC_PATH, "数字分身")   # 正式件落点=生成器默认读的路径（口径对齐 INSTALL.md/k2 SPEC_DEFAULT）
    gen = os.path.join(MC_PATH, "数字分身", "k2-slice-generator")
    if _detect_existing_twin(MC_PATH):
        print()
        print("━━━━━━━━ ✅ 检测到你已有数字分身（人格规格书+切片在位），跳过造芯流程 ━━━━━━━━")
        print("本端只做接入链接。你的分身文件在：%s/数字分身/" % MC_PATH)
        print("  · 人格规格书：%s" % os.path.join(dt_root, "童灵·人格规格书.md"))
        print("  · K2切片：%s" % os.path.join(dt_root, "K2切片蒸馏", "slices"))
        print("  · 入门指南（随时可查）：%s" % os.path.join(ob, "入门指南-通用版.md"))
        print("（各端「怎么接入」由本端适配器承载；分身本体跨端共享，无需重复造芯。）")
    else:
        print()
        print("━━━━━━━━ 下一步：造出你自己的数字分身 ━━━━━━━━")
        print("文件已装齐，但分身的「人格」得你自己造（不套用任何人的现成答案）。全端同一套流程：")
        print("  1) 答题：HEXACO 100 题（性情）+ 33 题 CORE（身份 / 愿景）")
        print("  1b) 计分：把答题页导出的 JSON 交给随包脚本跑（⛔AI 不心算 96 个数·手算必漂）：")
        print("       python3 \"%s\" \"<答题页导出的.json>\""
              % os.path.join(dt_root, "hexaco", "hexaco_selfbuild_scorer.py"))
        print("       （同目录先跑 --selftest 可验计分器完好；退出码 0=可进下一步，1=有直线作答告警，2=作答作废须重测）")
        print("  2) 复制模板→改名→填（模板是「空壳」，生成器只读改名后的正式文件·不认模板名）：")
        print("       源：%s" % os.path.join(ob, "童灵·人格向量-空模板.json"))
        print("       为：%s" % os.path.join(dt_root, "童灵·人格向量.json"))
        print("       源：%s" % os.path.join(ob, "童灵·人格规格书-骨架模板.md"))
        print("       为：%s" % os.path.join(dt_root, "童灵·人格规格书.md"))
        print("       然后和 AI 一起把「为」这两个文件按你自己的资料填实（⛔别在模板原件上填）。")
        print("  3) 跑生成器（确定性产出，不依赖模型发挥）：")
        print("       python3 \"%s\"" % os.path.join(gen, "hexaco_slice_generator.py"))
        print("       python3 \"%s\"" % os.path.join(gen, "k2_slice_generator.py"))
        print("  全程大白话引导 → %s" % os.path.join(ob, "入门指南-通用版.md"))
        print("（各端「怎么接入」由本端适配器承载；上面「造分身」流程所有端一致。）")
    if _delegate_fail is not None:
        print()
        print("❌ 端接入未完成（端 setup 退出码 %d）——公共资产已部署，请按上方 [X]/待收尾项在 %s 端真机复核"
              % (_delegate_fail, _plat_args.platform))
        return _delegate_fail
    return 0


if __name__ == "__main__":
    sys.exit(main())
