#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_rule_triggers.py — 铁律版「加载时机索引表」→ rule_triggers.yaml 编译生成器

设计定位（2026-09-16 童灵执行·FU-3 销账落地）：
- FU-3 预测（doubao 端 2026-09-15 L2 评估封口）："童灵执行后产出两个脚本：
  索引表→yaml自动生成 + 文档实盘一致性检查"。
- ② 文档实盘一致性检查 = rule_doc_drift_check.py（豆包端童灵 2026-09-15 产出）。
- ① 本脚本 = 索引表→yaml 编译生成器（AutoClaw 童灵 2026-09-16 补齐）。

机制定位（单一真源纪律·S659/C-085 同族）：
- SSOT = 记忆规则/用户基本规则-铁律版.md 头部「加载时机索引表」。
- rule_triggers.yaml = 索引表的【编译产物】，不是第二本账。
- 索引表可机械编译的字段：id / name / resident / source_anchor（确定性派生）。
- match 正则列表 = 人工调优资产（v1 关键词集·铁律-020：改匹配先 dry-run），
  ⛔ 生成器不凭索引表编造正则——既有 match 原样保留，索引表新增行 emit 空 match+TODO 标注，
  由人/童灵按铁律-020 流程补正则后重跑本脚本。

用法：
  python3 gen_rule_triggers.py            # dry-run：只打印漂移报告，不写盘
  python3 gen_rule_triggers.py --write    # 编译写盘 + 自动跑 ⑥门禁复验

退出码：0=无漂移（dry-run）或写盘+门禁复验通过；1=有漂移/门禁失败。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import subprocess

HOME = os.path.expanduser("~")
TIELU_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆规则", "用户基本规则-铁律版.md")
YAML_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆规则", "rule_triggers.yaml")
GUARD_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具", "rule_three_layer_guard.py")

TABLE_RE = re.compile(r"^\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
RESIDENT_RE = re.compile(r"已通过.*强启动|已常驻|已合并入")


def parse_index_table():
    """从铁律版解析加载时机索引表 → [(id, name, resident, trigger_prose)]"""
    with open(TIELU_FILE, encoding="utf-8") as f:
        lines = f.readlines()
    rows = []
    in_table = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("##") and "加载时机索引表" in s:
            in_table = True
            continue
        if in_table:
            if s.startswith("#"):  # 下一节=表结束
                break
            m = TABLE_RE.match(s)
            if m:
                rid, name, trigger, _koujue = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
                rows.append({"id": rid, "name": name, "resident": False, "trigger": trigger})
    return rows


# resident 语义裁定（2026-09-16 童灵·机械口径收窄）：
# 索引表口径"已通过…强启动"≠ yaml 的 resident:true。yaml 的 resident 由消费方
# rule_fragment_inject.py 定义：resident=true = ⛔跳过匹配永不注入。
# 因此仅"已合并入/占位行"（无独立注入体）机械可译为 true；
# "强启动"行（001/002/005/008）仍是可用注入体，归 false（命中即注入片段，与强启动不冲突·渐进披露）。
# 参考：yaml 原注释"008 标 resident 因已内置强启动"为历史口径，但实盘 inject 仅跳过 resident——
# 008 若标 true 则 reply 格式守卫外的注入通道永不触发。为零行为变更，resident 编译规则如上。
MERGED_RE = re.compile(r"已合并入|占位")


def compile_resident(trigger, name):
    return bool(MERGED_RE.search(name) or MERGED_RE.search(trigger))


def parse_existing_yaml():
    """解析现有 yaml 的 match 调优资产 + 元数据 → {id: {name, resident, match_lines}}"""
    if not os.path.exists(YAML_FILE):
        return {}
    with open(YAML_FILE, encoding="utf-8") as f:
        text = f.read()
    blocks = re.split(r"\n(?=  - id: )", text)
    out = {}
    for b in blocks:
        m = re.match(r"\s*- id: \"(\d{3})\"", b)
        if not m:
            continue
        rid = m.group(1)
        name_m = re.search(r"name:\s*(.+)", b)
        res_m = re.search(r"resident:\s*(true|false)", b)
        match_lines = []
        in_match = False
        for ln in b.splitlines():
            if re.match(r"\s*match:", ln):
                in_match = True
                continue
            if in_match:
                if re.match(r"\s*- ", ln):
                    match_lines.append(ln.rstrip())
                else:
                    in_match = False
        out[rid] = {
            "name": name_m.group(1).strip() if name_m else "",
            "resident": (res_m.group(1) == "true") if res_m else False,
            "match": match_lines,
        }
    return out


def render_yaml(rows, existing):
    """编译：header 保留原文件说明（至 version: 行重写日期）+ triggers 全量重排

    字段编译权划分（2026-09-16 童灵定·零行为变更原则）：
    - name / source_anchor：SSOT 编译（索引表权威）
    - resident：yaml 现值优先（消费方语义·rule_fragment_inject 以 resident 决定注入跳过，
      索引表散文口径不机械可译——历史裁定 008/009 resident:true 保留）
      yaml 无该 id 时才按 SSOT 派生（已合并入/占位→true）
    - match：调优资产原样保留；仅非 resident 且无 match 的行标 TODO（覆盖守卫会拦非resident缺match·resident 行禁 match）
    """
    header = f"""# rule_triggers.yaml — 用户基本规则「加载时机」机器可执行触发规格
#
# ⚠️ 编译产物声明：本文件由 gen_rule_triggers.py 从 SSOT 编译生成——
#   SSOT = ~/[记忆共享中心]/记忆规则/用户基本规则-铁律版.md 头部「加载时机索引表」
#   ⛔DO NOT 手工编辑本文件的 id/name/resident/source_anchor（编译时会被 SSOT 覆盖）
#   ✅DO match 正则调优可直接编辑本文件（调优资产·铁律-020：改匹配先 dry-run 看命中）
#   重新编译：python3 [记忆共享中心]/脚本中心/gen_rule_triggers.py（dry-run 预览）→ --write 落盘
#   ⑥门禁：rule_three_layer_guard.py 机械校验 索引表条数 == 本文件条数 防漂移
#
# 编译时间：__TS__
version: 2
source: 用户基本规则-铁律版.md 加载时机索引表 (SSOT·编译产物)
triggers:
"""
    import datetime
    header = header.replace("__TS__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    body = []
    warns = []
    for r in rows:
        ex = existing.get(r["id"], {})
        match_lines = ex.get("match", [])
        if not match_lines:
            warns.append(r["id"])
        entry = [f"  - id: \"{r['id']}\""]
        nm = r["name"].replace("（已合并入008·v8.8）", "（已合并入008·占位）")
        entry.append(f"    name: {nm}")
        if r["id"] in existing:
            is_resident = existing[r["id"]]["resident"]
        else:
            is_resident = bool(re.search(r"已合并入|占位", r["name"] + r["trigger"]))
        entry.append(f"    resident: {'true' if is_resident else 'false'}")
        entry.append(f"    source_file: 用户基本规则-铁律版.md")
        entry.append(f"    source_anchor: \"### 铁律-{r['id']}\"")
        if match_lines:
            entry.append("    match:")
            entry.extend(match_lines)
        elif is_resident:
            entry.append("    match: []  # resident 行禁 match（覆盖守卫约束）")
        else:
            entry.append("    match: []  # TODO: 索引表新增行·match 正则待补（铁律-020 流程）")
        body.append("\n".join(entry))
    return header + "\n".join(body) + "\n", warns


def main():
    write_mode = "--write" in sys.argv
    rows = parse_index_table()
    existing = parse_existing_yaml()
    if not rows:
        print("❌ 索引表解析失败（0 行）——检查铁律版.md 表结构")
        return 1
    table_ids = {r["id"] for r in rows}
    yaml_ids = set(existing.keys())
    new_in_table = sorted(table_ids - yaml_ids)
    orphans_in_yaml = sorted(yaml_ids - table_ids)
    resident_drift = [
        r["id"] for r in rows
        # resident 保留现值原则：yaml 有该 id 时以现值为权威（消费方语义），不报告漂移；
        # 仅 yaml 缺行（无法保留现值）且 SSOT 判占位≠true 才算漂移（即：需人工确认的新增 resident 行）
        if r["id"] not in existing and bool(re.search(r"已合并入|占位", r["name"] + r["trigger"])) != True
    ]
    print(f"📊 SSOT 索引表: {len(rows)} 行 | 现有 yaml: {len(existing)} 条")
    print(f"   索引表新增（yaml 缺）: {new_in_table or '无'}")
    print(f"   yaml 孤儿（索引表无）: {orphans_in_yaml or '无'}")
    print(f"   resident 语义: yaml 现值优先（消费方 rule_fragment_inject 权威·保留 008/009=true）；新增行按 SSOT 派生")
    yaml_text, warns = render_yaml(rows, existing)
    if warns:
        print(f"   ⚠️ 空 match 行（待铁律-020 流程补正则）: {warns}")
    if not write_mode:
        print("🟡 dry-run：未写盘。加 --write 编译落盘（写后自动跑 ⑥门禁复验）")
        # 漂移存在才 exit 1（dry-run 报告漂移是它的职责）
        return 1 if (new_in_table or orphans_in_yaml or resident_drift) else 0
    with open(YAML_FILE, "w", encoding="utf-8") as f:
        f.write(yaml_text)
    print(f"✅ 已编译写盘: {YAML_FILE}（{len(rows)} 条）")
    r = subprocess.run([sys.executable, GUARD_FILE], capture_output=True, text=True)
    tail = (r.stdout or r.stderr).strip().splitlines()[-3:]
    print("— ⑥门禁复验 —")
    for ln in tail:
        print("  " + ln)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
