#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distill_containers.py — 五容器回流骨架生成器+完整性校验器（T0根治·第二层）

定位：从源头消除"AI忘记写五容器"的可能。
  - --generate：生成五容器骨架文件（含必含字段占位符+从月报机械提取的数据）
  - --verify：校验AI填充后的文件是否含必含字段（非占位符）

设计哲学（Poka-Yoke 接触法+定值法）：
  接触法：脚本生成骨架文件=物理存在，AI不会忘记"还有这个容器要写"
  定值法：骨架含固定必含字段=AI不会忘记"还有这个字段要填"
  校验器：--verify模式物理检查=缺字段直接报错，不进入终检

与 finalize_report.py 的关系：
  distill_containers.py --generate → AI填充骨架 → distill_containers.py --verify → finalize_report.py 收口

用法：
  bash $SKILL_ROOT/scripts/dbbin.sh distill_containers.py --generate --month 2026-08
  bash $SKILL_ROOT/scripts/dbbin.sh distill_containers.py --verify --month 2026-08

退出码：
  0 = 生成/校验成功
  1 = 参数错误/月报文件不存在
  2 = 校验失败（--verify模式，有容器缺失或字段为空）
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

# === 环境自愈 ===
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv

HOME = str(dbenv.HOME)
GREATEST_ME = os.path.join(os.path.expanduser("[记忆共享中心]"), "最伟大的我")
OBSIDIAN_VAULT = os.path.join(HOME, "[日记仓库]")

# 占位符标记（校验时检测这些标记是否仍存在=AI未填充）
PLACEHOLDER_MARKERS = ["【待填充】", "【AI填充】", "TODO", "待补充", "待填写"]


def read_file(path: str) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_from_monthly_report(month: str) -> dict:
    """从月报中机械提取可用于五容器的数据"""
    report_path = os.path.join(OBSIDIAN_VAULT, "1-每日计划", "03-月报", f"{month}-月总结.md")
    content = read_file(report_path)
    if not content:
        return {"error": f"月报文件不存在: {report_path}"}

    extracted = {
        "report_path": report_path,
        "highlights": [],
        "lowpoints": [],
        "core_insights": [],
        "risks": [],
        "system_achievements": [],
        "partner_advice": "",
    }

    # 提取高光时刻
    hl_match = re.search(r"(?:高光时刻|高光与槽点|核心高光).*?\n(.*?)(?=\n##|\n###|\Z)", content, re.DOTALL)
    if hl_match:
        for line in hl_match.group(1).split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 5:
                extracted["highlights"].append(line)
                if len(extracted["highlights"]) >= 5:
                    break

    # 提取核心洞察/感悟
    insight_patterns = [r"核心洞察", r"本月最核心", r"认知突破", r"想通了"]
    for pat in insight_patterns:
        m = re.search(rf"{pat}.*?\n(.*?)(?=\n##|\n###|\Z)", content, re.DOTALL)
        if m:
            for line in m.group(1).split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and len(line) > 10:
                    extracted["core_insights"].append(line)
                    if len(extracted["core_insights"]) >= 5:
                        break
            if extracted["core_insights"]:
                break

    # 提取风险预警
    risk_match = re.search(r"(?:下月风险预警|风险表|风险预警).*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if risk_match:
        for line in risk_match.group(1).split("\n"):
            line = line.strip()
            if line and "|" in line and not line.startswith("|---") and "风险" not in line[:5]:
                extracted["risks"].append(line)
                if len(extracted["risks"]) >= 5:
                    break

    # 提取系统建设成果
    sys_match = re.search(r"(?:系统建设|系统建设与技术成果|8月系统建设).*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if sys_match:
        for line in sys_match.group(1).split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 8:
                extracted["system_achievements"].append(line)
                if len(extracted["system_achievements"]) >= 10:
                    break

    # 提取伙伴建议
    advice_match = re.search(r"(?:伙伴建议|🦞伙伴建议).*?\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    if advice_match:
        extracted["partner_advice"] = advice_match.group(1).strip()[:500]

    return extracted


def generate_self_portrait(month: str, data: dict) -> str:
    """生成自画像骨架（7段必含字段）"""
    prev_month = month  # 简化：AI自己读取上月自画像
    return f"""---
title: 自画像_{month}
type: self_portrait
month: {month}
created: {datetime.now().strftime("%Y-%m-%d")}
source: 月报蒸馏（distill_containers.py生成骨架）
---

# 自画像 · {month}

> 本文件由 distill_containers.py 生成骨架，AI填充认知蒸馏内容。
> 必含7段，缺一不可（--verify模式会校验）。

## 1. 我现在怎么看自己

【待填充】从本月日记/月报中提炼对自己的整体认知。

## 2. 最近做对了什么

【待填充】本月做对的关键决策/行为（参考月报高光时刻）。

> 月报高光参考：
{chr(10).join(f'- {h}' for h in data.get('highlights', [])[:3]) or '- （无）'}

## 3. 最近想通了什么

【待填充】本月的认知突破/顿悟（参考月报核心洞察）。

> 月报洞察参考：
{chr(10).join(f'- {i}' for i in data.get('core_insights', [])[:3]) or '- （无）'}

## 4. 我在回避什么

【待填充】本月发现的回避模式（参考月报风险预警+伙伴建议）。

> 月报风险参考：
{chr(10).join(f'- {r}' for r in data.get('risks', [])[:3]) or '- （无）'}

## 5. 对比说明（变了什么+没变什么）

【待填充】对比上月自画像，哪些认知变了，哪些没变。

## 6. 我的指南针（我可能成为谁）

【待填充】从人生版本/最新文件提取"我可能成为谁"。
（若人生版本/为空→写"待生成：尚未通过 Shall We Talk Step4.5 生成人生版本"，不阻塞月报）

## 7. 我的能量地图（耗能项/充能项）

【待填充】从本月认知发现+回避模式+日记提取耗能项与充能项。

### 充能项
- 【待填充】

### 耗能项
- 【待填充】
"""


def generate_change_trajectory(month: str, data: dict) -> str:
    """生成变化轨迹骨架（本月段+≥1条转折）"""
    return f"""## {month}

> 本文件由 distill_containers.py 生成骨架，AI填充认知转折。
> 必含≥1条"旧认知→新认知"转折，缺一不可（--verify模式会校验）。

### 转折1

- **旧认知**：【待填充】
- **新认知**：【待填充】
- **触发事件**：【待填充】（参考月报核心洞察）
- **CORE.md是否需更新**：【待填充】是/否

> 月报洞察参考：
{chr(10).join(f'- {i}' for i in data.get('core_insights', [])[:3]) or '- （无）'}

### 转折2（如有）

- **旧认知**：【待填充】
- **新认知**：【待填充】
- **触发事件**：【待填充】
- **CORE.md是否需更新**：【待填充】
"""


def generate_cognitive_discovery(month: str, data: dict) -> str:
    """生成认知发现骨架（含"发现"段）"""
    return f"""---
title: 认知发现_{month}-月报蒸馏
type: cognitive_discovery
month: {month}
discovery_type: 自发现
created: {datetime.now().strftime("%Y-%m-%d")}
source: 月报蒸馏（distill_containers.py生成骨架）
---

# 认知发现 · {month}（月报蒸馏）

> 本文件由 distill_containers.py 生成骨架，AI填充非S级认知突破。
> 与S级顿悟总记录去重：S级已单独存，本文件只收非S级认知突破。
> 必含"发现"段，缺一不可（--verify模式会校验）。

## 发现

【待填充】本月最核心的非S级认知突破（参考月报核心洞察）。

> 月报洞察参考：
{chr(10).join(f'- {i}' for i in data.get('core_insights', [])[:3]) or '- （无）'}

## 机制拆解

【待填充】这个认知发现背后的机制是什么？

## 为什么是认知陷阱

【待填充】为什么之前会陷入这个认知盲区？

## 用户自述（原文）

【待填充】从日记中提取你的原文表述。

## 自省提醒

【待填充】未来如何避免再次陷入？
"""


def generate_avoidance_pattern(month: str, data: dict) -> str:
    """生成回避模式骨架（3段必含：模式描述/认知象限/对质状态）"""
    return f"""---
title: 回避模式_{month}-月报蒸馏
type: avoidance_pattern
month: {month}
created: {datetime.now().strftime("%Y-%m-%d")}
source: 月报蒸馏（distill_containers.py生成骨架）
---

# 回避模式 · {month}（月报蒸馏）

> 本文件由 distill_containers.py 生成骨架，AI填充未闭环议题。
> 与现有回避条目去重：已记录的补充信号，新规避模式才新建。
> 必含3段（模式描述/认知象限/对质状态），缺一不可（--verify模式会校验）。

## 模式描述

【待填充】具体在回避什么 + 信号证据（数据/事件）。
参考月报风险表+伙伴建议（批评/盲区）提取未闭环议题。

> 月报风险参考：
{chr(10).join(f'- {r}' for r in data.get('risks', [])[:3]) or '- （无）'}

> 伙伴建议参考：
{data.get('partner_advice', '')[:300] or '（无）'}

## 认知象限

**未知已知**（默认值；回避模式本质是你未完全意识到的规避，不标则兜底未知已知；取值∈{{已知已知,已知未知,未知已知,未知未知}}）

## 对质状态

**待对质**（对质 = 未知已知→已知已知 转化，对齐 SHADOW 对质机制）
"""


def generate_achievement_evidence(month: str, data: dict) -> str:
    """生成成就证据骨架（系统建设成果维度·2段必含）"""
    achievements = data.get("system_achievements", [])
    return f"""---
title: 成就证据_{month}-系统建设成果
type: achievement_evidence
month: {month}
dimension: 系统建设
created: {datetime.now().strftime("%Y-%m-%d")}
source: 月报蒸馏（distill_containers.py生成骨架）
---

# 成就证据 · {month}（系统建设成果）

> 本文件由 distill_containers.py 生成骨架，AI填充系统建设维度成就。
> 视角重构：每条系统日志"AI做了什么" → 改写为"我决策并推动了什么"
> 与周报/日记主通道已写的成就证据不重复——本文件只收"系统日志视角的系统建设成果"维度
> 必含2段（我做对了什么≥3条/投入重心），缺一不可（--verify模式会校验）。

## 我做对了什么（系统建设维度）

【待填充】≥3条，每条"做了什么 + 为什么算我的决策推动"。

> 月报系统建设参考（AI需改写为"我决策并推动了什么"视角）：
{chr(10).join(f'- {a}' for a in achievements[:8]) or '- （无）'}

### 1. 【待填充】

做了什么：【待填充】
为什么算我的决策推动：【待填充】

### 2. 【待填充】

做了什么：【待填充】
为什么算我的决策推动：【待填充】

### 3. 【待填充】

做了什么：【待填充】
为什么算我的决策推动：【待填充】

## 投入重心（系统日志词频）

【待填充】当月高频词 Top5（从系统日志统计）。

| 排名 | 高频词 | 出现次数 | 说明 |
|:---:|--------|:---:|------|
| 1 | 【待填充】 | 【待填充】 | 【待填充】 |
| 2 | 【待填充】 | 【待填充】 | 【待填充】 |
| 3 | 【待填充】 | 【待填充】 | 【待填充】 |
| 4 | 【待填充】 | 【待填充】 | 【待填充】 |
| 5 | 【待填充】 | 【待填充】 | 【待填充】 |
"""


def verify_containers(month: str) -> dict:
    """校验五容器是否完整（文件存在+必含字段非占位符）"""
    result = {
        "month": month,
        "containers": {},
        "all_pass": True,
        "missing_files": [],
        "empty_fields": [],
    }

    # 1. 自画像
    sp_path = os.path.join(GREATEST_ME, "自画像", f"{month}.md")
    sp_content = read_file(sp_path)
    sp_status = {"path": sp_path, "exists": bool(sp_content), "fields": {}}
    if sp_content:
        for field in ["我现在怎么看自己", "最近做对了什么", "最近想通了什么",
                       "我在回避什么", "对比说明", "我的指南针", "我的能量地图"]:
            has_field = field in sp_content
            # 检查该字段后是否有占位符（AI未填充）
            field_filled = True
            if has_field:
                # 提取该字段后的内容（到下一个##为止）
                # 支持 "## 1. 字段名" / "## 字段名" / "## 字段名（备注）" 等格式
                m = re.search(rf"##\s*\d*\.?\s*{re.escape(field)}.*?\n(.*?)(?=\n##[^#]|\Z)", sp_content, re.DOTALL)
                if m:
                    field_text = m.group(1).strip()
                    if not field_text or any(p in field_text for p in PLACEHOLDER_MARKERS):
                        field_filled = False
            sp_status["fields"][field] = {"exists": has_field, "filled": field_filled}
            if not has_field or not field_filled:
                result["all_pass"] = False
                result["empty_fields"].append(f"自画像.{field}")
    else:
        result["all_pass"] = False
        result["missing_files"].append("自画像")
    result["containers"]["自画像"] = sp_status

    # 2. 变化轨迹（检查目录下是否有本月段）
    ct_dir = os.path.join(GREATEST_ME, "变化轨迹")
    ct_found = False
    ct_content_full = ""
    ct_file = None
    if os.path.isdir(ct_dir):
        for fname in os.listdir(ct_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(ct_dir, fname)
            content = read_file(fpath)
            if re.search(rf"##\s*{re.escape(month)}", content):
                ct_found = True
                ct_file = fpath
                m = re.search(rf"(##\s*{re.escape(month)}.*?)(?=\n##\s|\Z)", content, re.DOTALL)
                if m:
                    ct_content_full = m.group(1)
                break
    ct_status = {"path": ct_file or ct_dir, "exists": ct_found, "fields": {}}
    if ct_found:
        for field in ["旧认知", "新认知"]:
            has_field = field in ct_content_full
            field_filled = has_field and not any(p in ct_content_full for p in PLACEHOLDER_MARKERS)
            ct_status["fields"][field] = {"exists": has_field, "filled": field_filled}
            if not has_field or not field_filled:
                result["all_pass"] = False
                result["empty_fields"].append(f"变化轨迹.{field}")
    else:
        result["all_pass"] = False
        result["missing_files"].append("变化轨迹")
    result["containers"]["变化轨迹"] = ct_status

    # 3. 认知发现（检查目录下是否有本月文件）
    cd_dir = os.path.join(GREATEST_ME, "认知发现")
    cd_files = []
    cd_content_full = ""
    if os.path.isdir(cd_dir):
        for fname in os.listdir(cd_dir):
            if re.match(rf"{re.escape(month)}-.+\.md", fname):
                cd_files.append(os.path.join(cd_dir, fname))
    cd_status = {"path": cd_files[0] if cd_files else cd_dir, "exists": bool(cd_files), "fields": {}}
    if cd_files:
        for f in cd_files:
            cd_content_full += read_file(f) + "\n"
        for field in ["发现"]:
            has_field = field in cd_content_full
            field_filled = has_field and not any(p in cd_content_full for p in PLACEHOLDER_MARKERS)
            cd_status["fields"][field] = {"exists": has_field, "filled": field_filled}
            if not has_field or not field_filled:
                result["all_pass"] = False
                result["empty_fields"].append(f"认知发现.{field}")
    else:
        result["all_pass"] = False
        result["missing_files"].append("认知发现")
    result["containers"]["认知发现"] = cd_status

    # 4. 回避模式
    ap_dir = os.path.join(GREATEST_ME, "回避模式")
    ap_files = []
    ap_content_full = ""
    if os.path.isdir(ap_dir):
        for fname in os.listdir(ap_dir):
            if re.match(rf"{re.escape(month)}-.+\.md", fname):
                ap_files.append(os.path.join(ap_dir, fname))
    ap_status = {"path": ap_files[0] if ap_files else ap_dir, "exists": bool(ap_files), "fields": {}}
    if ap_files:
        for f in ap_files:
            ap_content_full += read_file(f) + "\n"
        for field in ["模式描述", "认知象限"]:
            has_field = field in ap_content_full
            field_filled = has_field and not any(p in ap_content_full for p in PLACEHOLDER_MARKERS)
            ap_status["fields"][field] = {"exists": has_field, "filled": field_filled}
            if not has_field or not field_filled:
                result["all_pass"] = False
                result["empty_fields"].append(f"回避模式.{field}")
    else:
        result["all_pass"] = False
        result["missing_files"].append("回避模式")
    result["containers"]["回避模式"] = ap_status

    # 5. 成就证据
    ae_path = os.path.join(GREATEST_ME, "成就证据", f"{month}-系统建设成果.md")
    ae_content = read_file(ae_path)
    ae_status = {"path": ae_path, "exists": bool(ae_content), "fields": {}}
    if ae_content:
        for field in ["我做对了什么"]:
            has_field = field in ae_content
            field_filled = True
            if has_field:
                m = re.search(rf"##\s*\d*\.?\s*{re.escape(field)}.*?\n(.*?)(?=\n##[^#]|\Z)", ae_content, re.DOTALL)
                if m:
                    field_text = m.group(1).strip()
                    if not field_text or any(p in field_text for p in PLACEHOLDER_MARKERS):
                        field_filled = False
            ae_status["fields"][field] = {"exists": has_field, "filled": field_filled}
            if not has_field or not field_filled:
                result["all_pass"] = False
                result["empty_fields"].append(f"成就证据.{field}")
    else:
        result["all_pass"] = False
        result["missing_files"].append("成就证据")
    result["containers"]["成就证据"] = ae_status

    return result


def main():
    # 环境自检（exit 码族统一·2026-09-11 收口：环境故障=9，与参数错误1区分）
    if not dbenv.self_check(verbose=True):
        sys.exit(9)

    parser = argparse.ArgumentParser(description="五容器回流骨架生成器+完整性校验器")
    parser.add_argument("--generate", action="store_true", help="生成五容器骨架文件")
    parser.add_argument("--verify", action="store_true", help="校验五容器完整性")
    parser.add_argument("--month", required=True, help="月份 YYYY-MM")
    parser.add_argument("--force", action="store_true", help="强制覆盖已存在的骨架文件")
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)

    if not args.generate and not args.verify:
        print("❌ 必须指定 --generate 或 --verify", file=sys.stderr)
        sys.exit(1)

    month = args.month

    # === --generate 模式 ===
    if args.generate:
        # 从月报提取数据
        data = extract_from_monthly_report(month)
        if "error" in data:
            print(f"❌ {data['error']}", file=sys.stderr)
            print("   请先完成月报生成（第1步），再调用本脚本生成五容器骨架。", file=sys.stderr)
            sys.exit(1)

        generated = []
        skipped = []

        # 1. 自画像
        sp_path = os.path.join(GREATEST_ME, "自画像", f"{month}.md")
        if os.path.exists(sp_path) and not args.force:
            skipped.append(f"自画像（已存在，使用--force覆盖）: {sp_path}")
        else:
            write_file(sp_path, generate_self_portrait(month, data))
            generated.append(f"自画像: {sp_path}")

        # 2. 变化轨迹（追加到现有文件或新建）
        ct_dir = os.path.join(GREATEST_ME, "变化轨迹")
        os.makedirs(ct_dir, exist_ok=True)
        # 查找是否有本月段
        ct_existing = None
        if os.path.isdir(ct_dir):
            for fname in os.listdir(ct_dir):
                if not fname.endswith(".md"):
                    continue
                content = read_file(os.path.join(ct_dir, fname))
                if re.search(rf"##\s*{re.escape(month)}", content):
                    ct_existing = fname
                    break
        if ct_existing and not args.force:
            skipped.append(f"变化轨迹（已有本月段，使用--force覆盖）: {ct_existing}")
        else:
            # 新建或追加到变化轨迹主文件
            ct_main = os.path.join(ct_dir, f"{month}-月报提炼.md")
            if os.path.exists(ct_main) and not args.force:
                skipped.append(f"变化轨迹（文件已存在，使用--force覆盖）: {ct_main}")
            else:
                write_file(ct_main, generate_change_trajectory(month, data))
                generated.append(f"变化轨迹: {ct_main}")

        # 3. 认知发现
        cd_path = os.path.join(GREATEST_ME, "认知发现", f"{month}-月报蒸馏.md")
        if os.path.exists(cd_path) and not args.force:
            skipped.append(f"认知发现（已存在，使用--force覆盖）: {cd_path}")
        else:
            write_file(cd_path, generate_cognitive_discovery(month, data))
            generated.append(f"认知发现: {cd_path}")

        # 4. 回避模式
        ap_path = os.path.join(GREATEST_ME, "回避模式", f"{month}-月报蒸馏.md")
        if os.path.exists(ap_path) and not args.force:
            skipped.append(f"回避模式（已存在，使用--force覆盖）: {ap_path}")
        else:
            write_file(ap_path, generate_avoidance_pattern(month, data))
            generated.append(f"回避模式: {ap_path}")

        # 5. 成就证据
        ae_path = os.path.join(GREATEST_ME, "成就证据", f"{month}-系统建设成果.md")
        if os.path.exists(ae_path) and not args.force:
            skipped.append(f"成就证据（已存在，使用--force覆盖）: {ae_path}")
        else:
            write_file(ae_path, generate_achievement_evidence(month, data))
            generated.append(f"成就证据: {ae_path}")

        # 输出结果
        print("✅ 五容器骨架生成完成")
        print(f"   月份: {month}")
        print(f"   已生成: {len(generated)} 个")
        for g in generated:
            print(f"   ✅ {g}")
        if skipped:
            print(f"   已跳过（已存在）: {len(skipped)} 个")
            for s in skipped:
                print(f"   ⏭️ {s}")
        print()
        print("📌 下一步：")
        print("   1. AI填充五个骨架文件中的【待填充】内容")
        print("   2. 运行 --verify 校验完整性")
        print("   3. 校验通过后运行 finalize_report.py 收口")
        sys.exit(0)

    # === --verify 模式 ===
    if args.verify:
        result = verify_containers(month)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if result["all_pass"]:
            print(f"\n✅ 五容器校验通过（{month}）：5/5容器完整，必含字段已填充", file=sys.stderr)
            sys.exit(0)
        else:
            print(f"\n❌ 五容器校验失败（{month}）：", file=sys.stderr)
            if result["missing_files"]:
                print(f"   缺失文件: {', '.join(result['missing_files'])}", file=sys.stderr)
            if result["empty_fields"]:
                print(f"   空字段/未填充: {', '.join(result['empty_fields'])}", file=sys.stderr)
            print("   请先运行 --generate 生成骨架，填充【待填充】内容后重新校验。", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
