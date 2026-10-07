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
import sys
# Windows 控制台默认 cp1252/cp936，强制 stdout/stderr UTF-8（同包 data_contamination_check.py 先例）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

PKG = os.path.dirname(os.path.abspath(__file__))
PLACEHOLDER = "[记忆共享中心]"
# 路径变量（--platform 覆盖·默认 WorkBuddy 兼容）
HOOKS_ROOT = os.path.join(os.path.expanduser("~"), ".workbuddy", "hooks")
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
    ("Stop", ".", "references/scripts", "run_registry_guards.sh", []),

    # —— 数字分身（随分身启用；未部署分身者钩子会安全空转）——
    ("UserPromptSubmit", ".", "references/digital-twin/devtools", "doenglingz_inject_prompt.py", []),
    ("Stop", ".", "references/digital-twin/devtools", "twin_verdict_ledger.py", []),
    ("Stop", ".", "references/digital-twin/devtools", "twin_changelog_guard.py", []),
]

TEXT_EXT = (".py", ".sh", ".yaml", ".yml", ".json", ".md")

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
    # 人格测评答题件（2026-09-30 补·养成链一级点火入口·判定标准「用户更好体验」）
    #   判据＝养成链第一步「答题」必须有装机态入口：AI 安装完成后直接 open 答题页，
    #   用户零找路。⛔只装测评四件（答题页×2+题库+官方答题卡）——hexaco/ 目录其余件
    #   （跨模型互照报告/评测 json/探针题库）＝作者侧运营产物 → 不进部署面。
    "hexaco": ("自建100题-分身版-题库-v1.md", "自建100题-答题页-v1.html",
               "HEXACO-100-HTML答题页.html", "HEXACO-100完整版-官方中文-答题卡.md"),
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
    # 五系统文件（在配置根或MC根）
    sys_root = cfg_root or mc
    sys_present = []
    for name in SYS_FILE_NAMES:
        if os.path.isfile(os.path.join(sys_root, name)):
            sys_present.append(name)
    assets["五系统文件"] = len(sys_present)
    assets["_sys_files"] = sys_present

    # ── 2. 判定用户身份 ──
    public_assets = ["脚本中心", "数字分身套件", "记忆规则", "Skill"]
    public_present = sum(1 for k in public_assets if assets.get(k))
    if public_present == 0 and assets["五系统文件"] == 0:
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


def _fill_text(txt, mc):
    """占位符替换（**纯函数版**·⛔ 不写盘）。

    拆出来的原因：断章增量要求「先在内存里替换好，再整块写进段里」，
    否则会出现「包模板已填、用户文件已填」两份不同占位符 ⇒ 冲突判定误报。
    """
    return (txt or "").replace(PLACEHOLDER, mc)


def _fill(path, mc, dry=False):
    """占位符替换：<记忆共享中心> → 实际绝对路径（仅文本类文件）。"""
    if not path.endswith(TEXT_EXT):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
    except (OSError, UnicodeDecodeError):
        return 0
    if PLACEHOLDER not in txt:
        return 0
    n = txt.count(PLACEHOLDER)
    if not dry:
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt.replace(PLACEHOLDER, mc))
    return n


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
    #    边界确认：min版=端用户运行必需的最小集（9个核心脚本：向量构建/概念提取/碰撞扫描/
    #    阅读状态推导/索引重建/源哈希/卡片元数据同步+2个环境/路径助手）；
    #    （2026-10-07 你裁决：模型压缩件 quantize_export 撤出对外包·作者自用；量化识别逻辑保留在 build/search 内·仅产物存在时生效）
    #    完整版含作者侧运营数据（cache/logs/vectors/calibration/route_table等）→ ⛔不入包。
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


RULE_DATA = ["rule_triggers.yaml", "rule_conflict_signals.yaml"]
"""规则层运行时数据：铁律硬墙（rule_fragment_inject / rule_three_layer_guard）
从 `<MC>/记忆规则/` 读这些文件——缺则硬墙**静默零注入**（实测：rc=0、无输出、无报错）
或缺冲突信号（退化为内置默认组）。包内源在 references/scripts/，安装时必须落到 `<MC>/记忆规则/`。"""


def install_rule_data(mc, dry=False):
    """把规则层运行时数据装到 <MC>/记忆规则/（幂等覆盖，与三层规则文件同惯例）。"""
    done = []
    for name in RULE_DATA:
        src = os.path.join(PKG, "references/scripts", name)
        if not os.path.isfile(src):
            continue
        dst_dir = os.path.join(mc, "记忆规则")
        if not dry:
            os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, name)
        _copy(src, dst, dry)
        if not dry:
            _fill(dst, mc)
        done.append(name)
    return done


RULE_FILES = ["用户基本规则-铁律版.md", "用户基本规则-摘要版.md", "用户基本规则-详解存档版.md"]
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
        try:
            ok, st, msg = bm.upsert_file_body(
                dst, sid, body,
                template_full=tpl,
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
    return done


def deploy_hooks(dry=False):
    """②部署钩子副本：ROSTER 表驱动（主件 + 同目录依赖）。"""
    deployed, missing = [], []
    for ev, loc, srcdir, main, deps in ROSTER:
        dst_dir = HOOKS_ROOT if loc == "." else os.path.join(HOOKS_ROOT, loc)
        for fname in [main] + list(deps):
            src = os.path.join(PKG, srcdir, fname)
            if not _status(src):
                missing.append("%s/%s" % (srcdir, fname))
                continue
            _copy(src, os.path.join(dst_dir, fname), dry)
            if not dry:
                _fill(os.path.join(dst_dir, fname), MC_PATH)
        deployed.append((ev, "%s/%s" % (loc, main) if loc != "." else main, srcdir, main))
    return deployed, missing


def _hook_command(subpath):
    """构造 settings.json 里要写的命令行（按平台）。"""
    p = os.path.join(HOOKS_ROOT, subpath).replace("\\", "/")
    if os.name == "nt":
        cands = glob.glob(os.path.join(
            os.path.expanduser("~"), ".workbuddy", "binaries", "python",
            "versions", "*", "python.exe"))
        pyexe = cands[0].replace("\\", "/") if cands else "python"
        return ('BULUOTUO_RUNTIME_PATHS="%s" MSYS_NO_PATHCONV=1 "%s" "%s"' % ((os.path.join(_CFG_ROOT_ABS, "doenglingz", "runtime_paths.json")).replace("\\", "/"), pyexe, p))
    cmd = "python3 " + p
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
            return 0, 0
    hooks = data.setdefault("hooks", {})

    def has(lst, basename):
        for grp in lst:
            if not isinstance(grp, dict):
                continue
            for h in grp.get("hooks", []):
                if isinstance(h, dict) and basename in h.get("command", ""):
                    return True
        return False

    added = skipped = 0
    for ev, sub, _sd, _m in deployed:
        arr = hooks.setdefault(ev, [])
        base = os.path.basename(sub)
        if has(arr, base):
            skipped += 1
            continue
        if not dry:
            arr.append({"hooks": [{"type": "command", "command": _hook_command(sub)}]})
        added += 1

    if not dry and added:
        if os.path.isfile(SETTINGS):
            shutil.copy2(SETTINGS, SETTINGS + ".bak-installscripts")
        with open(SETTINGS, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return added, skipped


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


def verify_deployed(mc=None):
    """核对已装态：ROSTER 里每个钩子①文件是否落盘 ②settings.json 是否已注册；
    若给了记忆中心路径，再核 ③规则层运行时数据（铁律硬墙的数据源）是否就位。

    与部署共用同一份 ROSTER/RULE_DATA —— 核查口径不可能与安装口径脱节。
    返回 0=全过；1=有缺失（明细打印到 stdout）。
    """
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
                for _rel in (os.path.join("开发工具", "Skill路由引擎", "scripts", "route_traework_patrol.sh"),
                             os.path.join("脚本中心", "route_traework_patrol.sh")):
                    _p = os.path.join(mc, _rel)
                    if os.path.isfile(_p):
                        try:
                            _parts.append(open(_p, encoding="utf-8", errors="ignore").read())
                        except Exception:
                            pass
                        break
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
        for fname, src_rel in entries:
            n_files += 1
            # 落盘核按 src 分派（判据从变换规则推导·[5/8][5b/8][5c/8] 各归各位）
            if "digital-twin" in src_rel:
                base = os.path.join(mc, "数字分身", "devtools") if mc else None
            elif src_rel.startswith("adapters/"):
                base = os.path.join(_CFG_ROOT_ABS or "", "hooks") if _CFG_ROOT_ABS else None
            else:
                base = sc
            if mc is not None and not (base and os.path.isfile(os.path.join(base, fname))):
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
    if os.path.isfile(SETTINGS):
        try:
            with open(SETTINGS, "r", encoding="utf-8") as f:
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
        for _e in _deliv:
            # 2026-10-06 防御：端SSOT 条目若为裸字符串（capability 用了非受控子集写法
            # 或 _mini_yaml 未能还原行内 dict），按「只有文件名、无事件」降级处理，
            # ⛔不再让 .get() 抛 AttributeError 把整条 verify 打断（v1.89 口径崩过一版）。
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
        dst_dir = HOOKS_ROOT if loc == "." else os.path.join(HOOKS_ROOT, loc)
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

    把「自身 100% 才许映射」从单端点状修补升级为全端发版门禁——任一端未达 100% →
    exit 1（拒绝打包）。判据本体=platform_adaptation_check.py（三面：五系统文件/
    钩子面/数字分身面·与 verify.sh §1.5/§1.6 同源），本函数只做同解释器委派。"""
    pac = os.path.join(os.path.dirname(os.path.abspath(__file__)), "platform_adaptation_check.py")
    if not os.path.isfile(pac):
        print("❌ 发版门禁脚本缺失: %s（打包前须随包分发）" % pac)
        return 2
    import subprocess
    r = subprocess.run(
        [sys.executable, pac, "--src", platform_id, "--gate", "--pkg-root",
         os.path.dirname(os.path.abspath(__file__))],
        capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


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
    "kb_engine":     "知识联邦引擎",
    "script_center": "脚本中心",
    "worklog":       "工作日志",
    "twin":          "数字分身",
    "blueprint":     "记忆蓝图",
    "skills":        "技能配置",
    "knowledge":     "知识库",
    "k2_slices":     ("数字分身", "K2切片蒸馏"),
    "twin_slices":   ("数字分身", "K2切片蒸馏", "slices"),
    "twin_spec":     ("数字分身", "童灵·人格规格书.md"),
    "custom_route":  ("自定义层", "路由家族"),
    "memory_amber":  "记忆琥珀",
}
# 注意：`archive_root` 本身＝记忆中心（不进这张表·它就是根）


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
    if dry:
        return data, None
    written = mod.write(data)
    return data, written


SYS_FILE_NAMES = ("SOUL.md", "IDENTITY.md", "USER.md", "MEMORY.md", "customPrompt.md")
"""端系统文件的标准名单（step5 合成 / 落点解析 / 段 id 解析 共用单一真源）。五件：SOUL品格/IDENTITY身份/USER画像+童灵/MEMORY导航/customPrompt执行准则。"""

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

    返回 {文件名: 绝对路径 或 None}；None = 该端**无载体**（⛔ 不许写配置根
    ⇒ 会成永远不被加载的孤儿文件，须由调用方并入主载体）。
    端中立性：cap 为 None 或未声明 ⇒ 全部落配置根（**向后兼容**·扁平端行为不变）。
    ⛔ 本函数**不含任何端名特判**：端差异只经 capability 声明进入（见
    `system_file_paths`）。这是端中立性的机械保证——判据见
    `test_system_file_targets.py::t7_endpoint_neutral`。
    """
    paths = (cap or {}).get("system_file_paths") or {}
    out = {}
    for name in SYS_FILE_NAMES:
        rel = paths.get(name, name)          # 未声明 ⇒ 默认配置根（扁平端）
        out[name] = None if rel is None else os.path.join(cfg_root, rel)
    return out


def system_file_segments(cap=None):
    """系统文件的断章段 id（宪法 C1）。未声明 ⇒ 按文件名派生稳定 id。"""
    segs = (cap or {}).get("system_file_segments") or {}
    out = {}
    for name in SYS_FILE_NAMES:
        out[name] = segs.get(name) or "sys." + name.replace(".md", "").lower()
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
        conclusion = "✅ 安装完成：全部资产通过"
    elif verdict == "degraded":
        conclusion = "⚠️ 安装完成（降级）：核心资产通过，%d项待收尾" % len(degraded + pending)
    else:
        conclusion = "❌ 安装未完成：%d项必需能力缺失" % counts.get("required_missing", 0)
    print()
    print("━━━━━━━━ 📋 安装完成汇总 ━━━━━━━━")
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
    print("  知识联邦引擎（抽卡/撞卡）已装核心 9 件：完整版大半是运行数据缓存，对你没用还占地方，故只装核心")
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
        if len(_env_hits) == 1:
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
        _install_mode = not any(a in sys.argv for a in ("--verify", "--list", "-h", "--help", "--gate"))
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
                # 委派成功 ≠ 全装完——继续走下面的公共资产部署（①/①a/①b）
            else:
                print(f"⚠️ 本端({_plat_args.platform})未找到端部署入口 {entry}，且 capability 未声明 setup_dispatch: manual——端适配面不完整，请核对该端 adapter")

        else:
            print("ℹ️ 查询模式（--verify/--list）——跳过端 setup 委派与安装后喊话")
    # ── 端自定义安装后喊话（2026-10-03·修：原挂在 `platform != "workbuddy"` 分支内
    #    ⇒ **WorkBuddy 端永远走不到这里·自己的 post_install_message 永远不打印**。
    #    根因：当日把喊话从 hooks_event 分支移出时，落点连同整个块一起留在了非 WB 分支内。
    #    ⛔ 端中立：任何端声明了 post_install_message 都要在安装终端呈现（WB 端尤其——
    #    它的自定义指令是「设置框字段」形态，用户看不到就等于没装）。
    _cap_for_msg = cap if _plat_args.platform != "workbuddy" else load_capability(
        os.path.join(PKG, "adapters", "workbuddy", "capability.yaml"))
    _msg = _cap_for_msg.get("post_install_message")
    if _msg:
        print()
        print(_msg)
    # ─── 以下为 WorkBuddy/有hook端的原有逻辑（HOOKS_ROOT/SETTINGS 已按需覆盖）───
    global MC_PATH
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("mc", nargs="?", help="记忆共享中心绝对路径")
    ap.add_argument("--dry-run", action="store_true", help="只报告不写盘")
    ap.add_argument("--list", action="store_true", help="只打印钩子总表")
    ap.add_argument("--verify", action="store_true", help="核对已装态（文件落盘 + 已注册；带 MC 路径时再核规则数据）")
    ap.add_argument("--gate", action="store_true",
                    help="发版前置门禁（用户令·2026-10-03）：端适配 100%% 才放行打包——调 platform_adaptation_check.py --gate")
    a = ap.parse_args()

    if a.verify:
        return verify_deployed(a.mc)

    if a.gate:
        return gate_check(_plat_args.platform)

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
    _health = pre_install_health_check(
        MC_PATH, _plat_args.platform,
        cap=locals().get("cap"),
        cfg_root=_CFG_ROOT_ABS,
        dry=a.dry_run,
    )

    # 知识库骨架（2026-10-06 E2E⑤ record_card_trigger 末层归因）：`knowledge` 键消费面要求
    #   安装器写 runtime_paths 时目录存在（exists_check 跳缺目录 ⇒ 键缺=端用户 PathKeyMissing）；
    #   空目录=端侧 sucair/立场卡合法写入落点·⛔个人数据不入（P-2 投影边界）
    if not a.dry_run:
        os.makedirs(os.path.join(MC_PATH, "知识库"), exist_ok=True)
    n_center = deploy_script_center(MC_PATH, a.dry_run)
    print("%s① 脚本中心：%d 件 → %s/脚本中心/（知识联邦引擎独立部署 → %s/知识联邦引擎/）"
          % (tag, n_center, MC_PATH, MC_PATH))
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

    rd = install_rule_data(MC_PATH, a.dry_run)
    rf = install_rule_files(MC_PATH, a.dry_run)
    _st = {"CREATED": "新建", "UPDATED": "更新", "UNCHANGED": "无变化",
           "CONFLICT": "⚠️冲突", "MERGE_ERROR": "❌硬失败"}
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
           "CONFLICT": "⚠️冲突", "MERGE_ERROR": "❌硬失败"}
    n_conflict = n_err = 0
    for _name, _stt, _msg in rf:
        print("   · %s：%s" % (_name, _st.get(_stt, _stt)))
        if _stt == "CONFLICT":
            n_conflict += 1
            print("     └ %s（你的文件未被改动·请人工裁决）" % _msg)
        elif _stt == "MERGE_ERROR":
            n_err += 1
            print("     └ %s" % _msg)
    print("%s①b 规则层：触发规格 %s + 三层规则文件 %d 件 → %s/记忆规则/（断章增量·⛔不覆盖你的改动）"
          % (tag, ", ".join(rd) if rd else "（包内无）", len(rf), MC_PATH))
    if n_conflict or n_err:
        print("   ⚠️ 规则层：%d 项冲突 · %d 项硬失败 —— 用户文件均未被覆盖，"
              "备份见 <记忆中心>/记忆琥珀/安装前备份/" % (n_conflict, n_err))

    if _skip_hooks:
        print("%s②③ 钩子部署/注册：跳过（本端无 hook 事件·端适配承载非标准机制·公共资产已装）" % tag)
    else:
        deployed, missing = deploy_hooks(a.dry_run)
        print("%s② 钩子部署：%d 件 → %s/" % (tag, len(deployed), HOOKS_ROOT))
        if missing:
            print("   !! 包内缺失（应报缺陷）：%s" % ", ".join(missing))

        added, skipped = register_hooks(deployed, a.dry_run)
        if not missing:
            write_guard_baseline(deployed, a.dry_run)
        else:
            print("!! 包内缺失在列 → 跳过基线写入（装机器缺陷不算到用户头上·C4-D GIGO闸）")
        print("%s③ 钩子注册：新增 %d · 已存在跳过 %d → %s" % (tag, added, skipped, SETTINGS))

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
    if bad:
        print("!! 部署后自检发现缺失 %d 件：%s" % (len(bad), ", ".join(sorted(set(bad)))))
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
