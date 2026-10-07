#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_box_schema_check.py — 错误归档 Schema 机械断言（守卫类·按需部署）
设计依据: growth-box SKILL.md「Poka-Yoke 防误层」节 + references/错误记录模板.md（v2.0·Body三段式）
职责: 校验错误归档文件必填字段齐全 + 枚举取值合法（Area 5级/Status 3态/Priority 4档/认知象限 2值）。
      从"提示词级约束（AI 自觉）"升级为"脚本机械断言（exit 非0=拒写/回补）"——依据 Skill架构规范
      §1.1 核心分层（防误>防错）+ 诚实边界（纯AI环境无绝对杜绝·措辞=绕过成本>遵守成本+绕过留痕）。
      ⛔本脚本只校验不改写（语义活归 AI·机械断言只做闸门）——与 normalize_tool/kb_concept_lint 零直写同理。
用法:
  python3 growth_box_schema_check.py <错误归档文件路径>   # 校验指定文件，全过 exit 0
适用范围:
  ⚠️ 适用于单条错误归档文件与多条目聚合文件（如 learnings/ERRORS.md、{tool}_errors.md）。
  📝 实现读取【整个文件】并校验「文件中至少存在每个必填字段各一处」——字段齐全的聚合文件可正常通过（exit 0）。
  ⚠️ 局限性：闸门按整文件校验，无法隔离【本次新写入的条目】——若仅有新条目缺字段、但文件中其他历史条目字段齐全，
     闸门会漏报（假阴性）。写入后请确认本次新条目字段完整，或按条目拆分逐条校验。
  📝 工具专属错误文件（{tool}_errors.md / skill_errors.md）按「错误记录模板.md 字段说明」可省略「来源 AI」，
     本脚本对 *_errors.md（非 ERRORS.md/LEARNINGS.md）自动跳过「来源 AI」硬校验。
退出码:
  0 = 校验通过（字段齐全 + 枚举合法 + 联动合法）
  1 = 文件不存在/不可读/无错误条目
  2 = 必填字段缺失（输出缺失清单）
  3 = 枚举取值非法 / 联动非法（输出非法清单）
联动校验（v1.1·2026-09-01 批次2 P2-11·你裁决补齐）:
  Status=promoted/resolved 的条目，认知象限须为「已知已知」——Poka-Yoke 3.1 联动规则
  （Status=resolved/promoted → 认知象限=已知已知（已解决/已蒸馏））。
  ⚠️ 整文件语义（与上方局限性声明同族）：按条目块分别匹配 Status 与认知象限，
  同一条目 Status=promoted/resolved 但认知象限=已知未知 → exit 3。
  存量宽容：历史 `Status: active`（枚举外取值）按祖父化跳过联动校验（见 P2-13 裁决，
  存量数据不迁移，新条目禁止 active）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re

# 必填加粗字段（错误记录模板.md 通用错误格式·v2.0）
REQUIRED_BOLD_FIELDS = ["Logged", "Priority", "Status", "Area", "来源 AI", "认知象限"]
# 必填小节（### 标题）
REQUIRED_SECTIONS = ["Summary", "Details", "Root Cause", "Rule", "Why", "How to apply"]

# 枚举（宽容匹配：前缀/包含，兼容真实文件后缀注释与多标签——如 Status: promoted (2026-06-19 蒸馏)、Area: 流程 | 工具）
ENUMS = {
    "Priority": ("high", "medium", "low", "critical"),
    "Status": ("pending", "resolved", "promoted"),
    "Area": ("流程", "验证", "身份认知", "技术实现", "其他"),
    "认知象限": ("已知未知", "已知已知"),
}

def main():
    if len(sys.argv) < 2:
        print("用法: python3 growth_box_schema_check.py <错误归档文件路径>")
        return 1
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        return 1
    text = open(path, encoding="utf-8").read()

    # 工具专属错误文件（{tool}_errors.md / skill_errors.md）按模板可省略「来源 AI」——见错误记录模板.md 字段说明
    basename = os.path.basename(path)
    is_tool_specific = basename.endswith("_errors.md") and basename not in ("ERRORS.md", "LEARNINGS.md")
    required_bold = [f for f in REQUIRED_BOLD_FIELDS if not (f == "来源 AI" and is_tool_specific)]

    # ① 必填字段存在性（硬校验：加粗字段名 + 小节标题）
    missing = [f for f in required_bold
               if not re.search(rf"^\*\*{re.escape(f)}\*\*", text, re.M)]
    missing += [s for s in REQUIRED_SECTIONS
                if not re.search(rf"^###\s+{re.escape(s)}\s*$", text, re.M)]
    if missing:
        print(f"❌ 必填字段缺失 {len(missing)} 个: {', '.join(missing)}")
        print("   → 回到步骤A2按 references/错误记录模板.md 补齐后再写（脚本闸门·exit 2）")
        return 2

    # ② 枚举取值合法（宽容匹配：值以合法项开头 / 含合法项）
    #    存量宽容（v1.1·P2-13 你裁决数据祖父化）：历史 `Status: active`（枚举外取值）跳过枚举硬校验——
    #    存量归档不迁移（零功能收益+事实漂移风险），新条目禁止 active（模板枚举三态不变）
    is_legacy_active = re.search(r"^\*\*Status\*\*\s*:\s*active\b", text, re.M)
    illegal = []
    for field, allowed in ENUMS.items():
        if field == "Status" and is_legacy_active:
            continue
        m = re.search(rf"^\*\*{re.escape(field)}\*\*\s*:\s*(.+)$", text, re.M)
        if not m:
            continue  # 已由①兜住
        val = m.group(1).strip()
        if not any(val.startswith(a) or a in val for a in allowed):
            illegal.append(f"{field}={val}（应 ∈ {'/'.join(allowed)}）")
    if illegal:
        print(f"❌ 枚举取值非法 {len(illegal)} 个: " + " | ".join(illegal))
        print("   → 按 SKILL.md 步骤A2 枚举修正（脚本闸门·exit 3）")
        return 3

    # ③ 联动校验（v1.1·P2-11）：按 `## [` 条目块切分，块内 Status=promoted/resolved → 认知象限须含「已知已知」
    #    整文件语义下条目块切分失败（无 ## [ 标题）则跳过联动（历史裸文件宽容），由①②兜底
    #    存量祖父化（P2-13 同族裁决）：Logged < 2026-07-01 的历史条目（认知象限字段引入前写入）跳过联动——
    #    存量不迁移（零功能收益+漂移风险），新条目（≥2026-07-01）强制联动
    blocks = re.split(r"(?=^## \[)", text, flags=re.M)
    linkage_bad = []
    for b in blocks:
        if not b.startswith("## ["):
            continue
        m_status = re.search(r"^\*\*Status\*\*\s*:\s*(\S+)", b, re.M)
        if not m_status or m_status.group(1) in ("active",):  # active=存量祖父化跳过（P2-13）
            continue
        if m_status.group(1) not in ("promoted", "resolved"):
            continue  # pending 无联动要求
        m_log = re.search(r"^\*\*Logged\*\*\s*:\s*(\d{4}-\d{2}-\d{2})", b, re.M)
        if m_log and m_log.group(1) < "2026-07-01":
            continue  # 字段引入前历史条目，祖父化跳过
        m_quad = re.search(r"^\*\*认知象限\*\*\s*:\s*(.+)$", b, re.M)
        quad = m_quad.group(1).strip() if m_quad else ""
        if "已知已知" not in quad:
            title = b.splitlines()[0].strip()[:60]
            linkage_bad.append(f"{title}… Status={m_status.group(1)} 但认知象限={quad or '（缺失）'}（应=已知已知）")
    if linkage_bad:
        print(f"❌ Status↔认知象限联动非法 {len(linkage_bad)} 条: " + " | ".join(linkage_bad))
        print("   → 按 Poka-Yoke 3.1 修正认知象限（脚本闸门·exit 3）")
        return 3

    print(f"✅ 归档 Schema 校验通过：字段 {len(required_bold)}+{len(REQUIRED_SECTIONS)} 齐全 + 枚举合法 + 联动合法 — {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
