#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
finalize_report.py — 周期报告统一收口脚本（接触法防误·T0根治）

对标 finalize_diary.py：不调本脚本=拿不到确认JSON=蒸馏报告写不出来=完整性锁不通过。
模型无关——无论什么 LLM 都无法绕过这个物理约束。

功能（原子化·不可拆分）：
  1. 校验报告文件存在+非空+YAML frontmatter合法
  2. 校验报告模块完整性（月报13模块+审计模块 / 周报11模块）
  3. 校验五容器存在性+必含字段（月报专属，周报跳过）
  4. 生成确认JSON（AI最终输出必须包含此JSON中的确认数据）
  5. stdout 输出 JSON，stderr 输出错误详情

退出码（exit 码族统一·2026-09-11 收口·规范见 dbenv.py docstring）：
  0 = 收口成功
  1 = 报告文件缺失 / 参数错误
  2 = 报告模块不完整
  3 = 五容器文件缺失（月报专属）
  4 = 五容器必含字段缺失（月报专属）
  9 = 环境自检失败（沙箱假 python·与业务码 0-4 无歧义）

用法：
  bash $SKILL_ROOT/scripts/dbbin.sh finalize_report.py --type monthly --month 2026-08
  bash $SKILL_ROOT/scripts/dbbin.sh finalize_report.py --type weekly --week 2026-W35

设计哲学（Poka-Yoke 接触法）：
  AI 的最终输出（蒸馏报告）必须包含本脚本 JSON 中的确认数据（模块校验结果+五容器状态）。
  不调本脚本=拿不到 JSON=蒸馏报告写不出来=完整性锁不通过。
  与 finalize_diary.py 的"不调脚本=拿不到灵感=封口确认块写不出来"完全同构。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# === 环境自愈（第一性原理根治·Hermes 沙箱 HOME 劫持·与其他脚本同律）===
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv

HOME = str(dbenv.HOME)
SKILL_ROOT = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "daily-buddy")
OBSIDIAN_VAULT = os.path.join(HOME, "[日记仓库]")
GREATEST_ME = os.path.join(os.path.expanduser("[记忆共享中心]"), "最伟大的我")

# 占位符标记（校验时检测这些标记是否仍存在=AI未填充）
PLACEHOLDER_MARKERS = ["【待填充】", "【AI填充】", "TODO", "待补充", "待填写"]

# === 月报模块清单（从 monthly-review-spec.md 提取·必含模块·宽松关键词匹配）===
# 注意：实际月报可能用中文数字编号（一、二、三）或emoji编号（1️⃣、2️⃣），
# 正则匹配核心关键词，不绑定编号格式。
MONTHLY_REQUIRED_MODULES = [
    ("⚓ 北极星对齐", r"北极星对齐"),
    ("高光时刻 & 槽点", r"高光.{0,5}槽点|高光与槽点|高光时刻"),
    ("❖ 日记质量评估", r"日记质量"),
    ("核心概览｜数据真相", r"核心概览"),
    ("时间分配｜精力流向", r"时间分配"),
    ("睡眠健康+能量统计", r"睡眠健康"),
    ("账号进展", r"账号进展"),
    ("阅读与知识体系", r"阅读与知识"),
    ("系统建设", r"系统建设"),
    ("下月风险预警", r"下月风险预警|风险预警"),
    ("下月3件事", r"下月.{0,3}件事|下月3件事|下月三件事"),
    ("伙伴建议", r"伙伴建议"),
]

# 月报审计模块（第1.5/1.6/阅读分析/Skill健康等·必含）
MONTHLY_AUDIT_MODULES = [
    ("📖 阅读分析/知识库健康", r"阅读分析|知识库健康"),
    ("🔧 Skill健康度", r"Skill健康度|技能健康"),
    ("📋 认知画像聚合", r"认知画像|能量预判自画像|决策命中率|灵感重复"),
    ("🌀 悬置显形", r"悬置显形|显形台账"),
    # L5 潜意识层回流（2026-10-02 新增·Hermes 童灵 D3）
    # 为什么加这条：月报已查「睡眠健康」，却不查「睡眠偏差有没有回流 SHADOW」——
    # 门禁查格式不查闭环。实证 2026-09 月报 finalize 16/16 通过，
    # 但 SHADOW「月度蒸馏统计」表停在 2026-07 行（8/9 两个月整段断回流），
    # 且月报自身「层级回流总览」段也无 L5 行（8月有）。断回流与"全通过"同时发生。
    # 本条把「回流」纳入月报终检的必含面 → 漏回流当场红，不靠下一个谁恰好想起来。
    # ⚠️ 判据取「L5/潜意识/SHADOW」三选一宽松匹配：月报正文提一句即过，
    #    但【无】三个字任一出现仍算通过（当月确实无偏差时允许显式声明「无」）。
    ("🧠 L5 潜意识层回流", r"L5|潜意识|SHADOW"),
]

# === 周报模块清单（从 weekly-review-spec.md 提取·必含模块）===
WEEKLY_REQUIRED_MODULES = [
    ("📸 本周快照", r"📸\s*本周快照|本周快照"),
    ("❖ 日记质量评估", r"❖\s*📋?\s*日记质量评估"),
    ("📌 月目标对齐", r"📌\s*月目标对齐"),
    ("🎯 核心概览", r"🎯\s*核心概览"),
    ("1️⃣ 进度追踪", r"1️⃣\s*进度追踪"),
    ("2️⃣ 数据分析", r"2️⃣\s*数据分析"),
    ("3️⃣ 问题与解决方案", r"3️⃣\s*问题与解决方案"),
    ("4️⃣ 90天目标对齐", r"4️⃣\s*90天目标对齐"),
    ("5️⃣ 情景层卡点", r"5️⃣\s*情景层卡点"),
    ("6️⃣ 上周计划完成", r"6️⃣\s*上周计划完成"),
    ("7️⃣ 本周计划+伙伴建议", r"7️⃣\s*本周计划|7️⃣.*伙伴建议"),
]

# === 五容器定义（月报专属）===
def container_paths(month: str) -> dict:
    """返回五容器的文件路径定义"""
    return {
        "自画像": {
            "path": os.path.join(GREATEST_ME, "自画像", f"{month}.md"),
            "required_fields": [
                ("我现在怎么看自己", r"我现在怎么看自己"),
                ("最近做对了什么", r"最近做对了什么"),
                ("最近想通了什么", r"最近想通了什么"),
                ("我在回避什么", r"我在回避什么"),
                ("对比说明", r"对比说明"),
                ("我的指南针", r"我的指南针"),
                ("我的能量地图", r"我的能量地图"),
            ],
        },
        "变化轨迹": {
            "path": None,  # 变化轨迹是追加到现有文件的段，不是独立文件
            "dir": os.path.join(GREATEST_ME, "变化轨迹"),
            "month_pattern": rf"##\s*{re.escape(month)}",
            "required_fields": [
                ("旧认知", r"旧认知"),
                ("新认知", r"新认知"),
            ],
        },
        "认知发现": {
            "path": None,  # 认知发现是 {month}-主题.md 格式，需要glob
            "dir": os.path.join(GREATEST_ME, "认知发现"),
            "file_pattern": rf"{re.escape(month)}-.+\.md",
            "required_fields": [
                ("发现", r"发现"),
            ],
        },
        "回避模式": {
            "path": None,  # 回避模式是 {month}-主题.md 格式
            "dir": os.path.join(GREATEST_ME, "回避模式"),
            "file_pattern": rf"{re.escape(month)}-.+\.md",
            "required_fields": [
                ("模式描述", r"模式描述"),
                ("认知象限", r"认知象限"),
            ],
        },
        "成就证据": {
            "path": os.path.join(GREATEST_ME, "成就证据", f"{month}-系统建设成果.md"),
            "required_fields": [
                ("我做对了什么", r"我做对了什么"),
            ],
        },
    }


def read_file(path: str) -> str:
    """读取文件内容，不存在则返回空字符串"""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def check_yaml_frontmatter(content: str) -> tuple:
    """检查YAML frontmatter是否合法，返回(是否合法, 缺失字段列表)"""
    if not content.startswith("---"):
        return False, ["无YAML frontmatter（文件不以---开头）"]
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return False, ["YAML frontmatter格式错误（无闭合---）"]
    yaml_text = m.group(1)
    missing = []
    # 必留字段检查（对齐文件格式规范v2.2.0分层）
    for field in ["type", "date", "summary", "source", "complies_with"]:
        if not re.search(rf"^{field}\s*:", yaml_text, re.MULTILINE):
            missing.append(f"YAML缺必留字段：{field}")
    return len(missing) == 0, missing


def check_modules(content: str, modules: list) -> tuple:
    """检查报告模块是否齐全，返回(通过数, 缺失模块列表)"""
    missing = []
    for name, pattern in modules:
        if not re.search(pattern, content):
            missing.append(name)
    return len(modules) - len(missing), missing


def check_container(container_def: dict, month: str) -> dict:
    """检查单个五容器，返回状态dict"""
    result = {"status": "unknown", "missing_fields": [], "file": None, "has_placeholder": False}

    def check_placeholders(content: str) -> bool:
        """检查内容中是否含未填充占位符"""
        return any(p in content for p in PLACEHOLDER_MARKERS)

    # 自画像/成就证据：独立文件
    if container_def.get("path"):
        path = container_def["path"]
        result["file"] = path
        if not os.path.exists(path):
            result["status"] = "missing"
            return result
        content = read_file(path)
        if len(content) < 50:
            result["status"] = "incomplete"
            result["missing_fields"] = ["文件内容过少（可能为空模板）"]
            return result
        # 占位符检测（整体）
        if check_placeholders(content):
            result["has_placeholder"] = True
            result["status"] = "incomplete"
            result["missing_fields"].append("文件含未填充占位符（【待填充】等），AI未完成蒸馏")
            return result
        # 检查必含字段
        for field_name, field_pattern in container_def["required_fields"]:
            if not re.search(field_pattern, content):
                result["missing_fields"].append(field_name)
        result["status"] = "pass" if not result["missing_fields"] else "incomplete"
        return result

    # 变化轨迹：追加到现有文件的段
    if container_def.get("month_pattern"):
        dir_path = container_def["dir"]
        if not os.path.isdir(dir_path):
            result["status"] = "missing"
            result["file"] = dir_path
            return result
        # 扫描目录下所有.md文件，查找是否有本月段
        month_found = False
        month_content = ""
        for fname in os.listdir(dir_path):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(dir_path, fname)
            content = read_file(fpath)
            if re.search(container_def["month_pattern"], content):
                month_found = True
                # 提取本月段内容
                m = re.search(
                    rf"(##\s*{re.escape(month)}.*?)(?=\n##\s|\Z)",
                    content, re.DOTALL
                )
                if m:
                    month_content = m.group(1)
                result["file"] = fpath
                break
        if not month_found:
            result["status"] = "missing"
            result["file"] = dir_path
            return result
        # 占位符检测
        if check_placeholders(month_content):
            result["has_placeholder"] = True
            result["status"] = "incomplete"
            result["missing_fields"].append("本月段含未填充占位符（【待填充】等），AI未完成蒸馏")
            return result
        # 检查必含字段
        for field_name, field_pattern in container_def["required_fields"]:
            if not re.search(field_pattern, month_content):
                result["missing_fields"].append(field_name)
        result["status"] = "pass" if not result["missing_fields"] else "incomplete"
        return result

    # 认知发现/回避模式：{month}-主题.md 格式
    if container_def.get("file_pattern"):
        dir_path = container_def["dir"]
        if not os.path.isdir(dir_path):
            result["status"] = "missing"
            result["file"] = dir_path
            return result
        # 扫描目录下匹配本月的文件
        matched_files = []
        for fname in os.listdir(dir_path):
            if re.match(container_def["file_pattern"], fname):
                matched_files.append(os.path.join(dir_path, fname))
        if not matched_files:
            result["status"] = "missing"
            result["file"] = dir_path
            return result
        # 检查所有匹配文件中是否至少有一个含必含字段
        all_content = "\n".join(read_file(f) for f in matched_files)
        result["file"] = matched_files[0]
        # 占位符检测（整体）
        if check_placeholders(all_content):
            result["has_placeholder"] = True
            result["status"] = "incomplete"
            result["missing_fields"].append("文件含未填充占位符（【待填充】等），AI未完成蒸馏")
            return result
        for field_name, field_pattern in container_def["required_fields"]:
            if not re.search(field_pattern, all_content):
                result["missing_fields"].append(field_name)
        result["status"] = "pass" if not result["missing_fields"] else "incomplete"
        return result

    return result


def get_report_path(report_type: str, month: str = None, week: str = None) -> str:
    """根据类型和周期返回报告文件路径"""
    if report_type == "monthly":
        return os.path.join(OBSIDIAN_VAULT, "1-每日计划", "03-月报", f"{month}-月总结.md")
    elif report_type == "weekly":
        return os.path.join(OBSIDIAN_VAULT, "1-每日计划", "02-周报", f"{week}-周报.md")
    return ""


def main():
    # ─── 环境自检（第一性原理根治·沙箱假 python 拒绝空跑·exit 码族统一：环境故障=9）───
    if not dbenv.self_check(verbose=True):
        sys.exit(9)

    parser = argparse.ArgumentParser(description="周期报告统一收口（接触法防误）")
    parser.add_argument("--type", required=True, choices=["monthly", "weekly"],
                        help="报告类型：monthly=月报 / weekly=周报")
    parser.add_argument("--month", help="月份 YYYY-MM（月报必填）")
    parser.add_argument("--week", help="周次 YYYY-WXX（周报必填）")
    parser.add_argument("--skip-containers", action="store_true",
                        help="显式跳过五容器校验（月报专属·有痕跳过·封口块将如实标注）")
    try:
        args = parser.parse_args()
    except SystemExit as e:
        raise SystemExit(1)

    # 参数校验
    if args.type == "monthly" and not args.month:
        print("❌ 参数错误：月报必须提供 --month YYYY-MM", file=sys.stderr)
        sys.exit(1)
    if args.type == "weekly" and not args.week:
        print("❌ 参数错误：周报必须提供 --week YYYY-WXX", file=sys.stderr)
        sys.exit(1)

    period = args.month if args.type == "monthly" else args.week
    report_path = get_report_path(args.type, args.month, args.week)

    # === Step 1: 校验报告文件存在+非空 ===
    if not os.path.exists(report_path):
        print(f"❌ 报告文件不存在: {report_path}", file=sys.stderr)
        print("   请先完成报告生成（第1步），再调用本脚本收口。", file=sys.stderr)
        sys.exit(1)

    report_content = read_file(report_path)
    if len(report_content) < 500:
        print(f"❌ 报告文件内容过少（{len(report_content)}字节），可能为空模板或未完成", file=sys.stderr)
        sys.exit(1)

    # === Step 2: 校验YAML frontmatter ===
    yaml_ok, yaml_missing = check_yaml_frontmatter(report_content)
    if not yaml_ok:
        print("❌ YAML frontmatter校验失败：", file=sys.stderr)
        for m in yaml_missing:
            print(f"   - {m}", file=sys.stderr)
        sys.exit(1)

    # === Step 3: 校验报告模块完整性 ===
    if args.type == "monthly":
        required_modules = MONTHLY_REQUIRED_MODULES + MONTHLY_AUDIT_MODULES
    else:
        required_modules = WEEKLY_REQUIRED_MODULES

    modules_passed, modules_missing = check_modules(report_content, required_modules)
    modules_total = len(required_modules)

    if modules_missing:
        print(f"❌ 报告模块不完整（{modules_passed}/{modules_total}通过），缺失模块：", file=sys.stderr)
        for m in modules_missing:
            print(f"   - {m}", file=sys.stderr)
        print("", file=sys.stderr)
        print("🔄 【自动补全指令】（自主进化·AI可自动执行）：", file=sys.stderr)
        period_flag = "--week" if args.type == "weekly" else "--month"
        print(f"   1. 回溯报告生成步骤，补齐缺失模块：{', '.join(modules_missing)}", file=sys.stderr)
        print(f"   2. 确保报告文件路径：{report_path}", file=sys.stderr)
        print(f"   3. 补齐后重新运行：bash {SKILL_ROOT}/scripts/dbbin.sh finalize_report.py --type {args.type} {period_flag} {period}", file=sys.stderr)
        sys.exit(2)

    # === Step 4: 校验五容器（月报专属）===
    containers_check = {}
    if args.type == "monthly" and not args.skip_containers:
        containers = container_paths(args.month)
        missing_containers = []
        incomplete_containers = []

        for cname, cdef in containers.items():
            cresult = check_container(cdef, args.month)
            containers_check[cname] = cresult
            if cresult["status"] == "missing":
                missing_containers.append(cname)
            elif cresult["status"] == "incomplete":
                incomplete_containers.append(cname)

        if missing_containers:
            print(f"❌ 五容器文件缺失（{len(missing_containers)}/5）：", file=sys.stderr)
            for c in missing_containers:
                print(f"   - {c}（路径: {containers_check[c]['file']}）", file=sys.stderr)
            print("", file=sys.stderr)
            print("🔄 【自动补全指令】（自主进化·AI可自动执行）：", file=sys.stderr)
            print(f"   1. 调用骨架生成器：bash {SKILL_ROOT}/scripts/dbbin.sh distill_containers.py --generate --month {args.month}", file=sys.stderr)
            print(f"   2. AI填充五个骨架文件中的【待填充】内容（按月报SOP第6.5步6.5.1-6.5.5规范）", file=sys.stderr)
            print(f"   3. 校验完整性：bash {SKILL_ROOT}/scripts/dbbin.sh distill_containers.py --verify --month {args.month}", file=sys.stderr)
            print(f"   4. 校验通过后重新收口：bash {SKILL_ROOT}/scripts/dbbin.sh finalize_report.py --type monthly --month {args.month}", file=sys.stderr)
            sys.exit(3)

        if incomplete_containers:
            print(f"❌ 五容器必含字段缺失/含占位符（{len(incomplete_containers)}/5不完整）：", file=sys.stderr)
            for c in incomplete_containers:
                print(f"   - {c}：缺失字段 {containers_check[c]['missing_fields']}", file=sys.stderr)
            print("", file=sys.stderr)
            print("🔄 【自动补全指令】（自主进化·AI可自动执行）：", file=sys.stderr)
            print(f"   1. 回溯补齐以下容器的缺失字段：", file=sys.stderr)
            for c in incomplete_containers:
                print(f"      - {c}：{', '.join(containers_check[c]['missing_fields'])}", file=sys.stderr)
            print(f"   2. 确保文件中无【待填充】等占位符（AI未完成蒸馏的标记）", file=sys.stderr)
            print(f"   3. 校验完整性：bash {SKILL_ROOT}/scripts/dbbin.sh distill_containers.py --verify --month {args.month}", file=sys.stderr)
            print(f"   4. 校验通过后重新收口：bash {SKILL_ROOT}/scripts/dbbin.sh finalize_report.py --type monthly --month {args.month}", file=sys.stderr)
            sys.exit(4)

    elif args.type == "monthly" and args.skip_containers:
        containers_check = {"_skip": "显式跳过五容器校验（--skip-containers）"}

    # === Step 5: 生成确认JSON ===
    result = {
        "status": "sealed",
        "type": args.type,
        "period": period,
        "report_path": report_path,
        "report_check": {
            "modules_total": modules_total,
            "modules_passed": modules_passed,
            "yaml_valid": True,
        },
        "sealed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    if args.type == "monthly":
        result["containers_check"] = {
            k: {"status": v["status"], "file": v.get("file")}
            for k, v in containers_check.items()
            if k != "_skip"
        }
        if args.skip_containers:
            result["containers_check"] = {"_skip": "显式跳过五容器校验（--skip-containers）"}

    # stdout 输出 JSON — AI 必须从此处取数据填入蒸馏报告确认块
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # stderr 输出成功摘要
    print(f"✅ {args.type}报告收口成功：{period}", file=sys.stderr)
    print(f"   模块校验：{modules_passed}/{modules_total} 通过", file=sys.stderr)
    if args.type == "monthly" and not args.skip_containers:
        print(f"   五容器校验：5/5 通过", file=sys.stderr)


if __name__ == "__main__":
    main()
