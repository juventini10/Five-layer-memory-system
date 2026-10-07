#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_checklist_gate.py — 查证清单机械门禁（step3-handover-protocol §二 落地·治"机械强制未闭环"）

问题背景（handover-protocol.md line 43 实锤）:
  查证清单仅为文档级强制（批卡硬格式要求），全仓库无任何脚本门禁拒收缺字段初审
  → 整改状态=文档层落地·验证层未闭环。本脚本填补该缺口。

门禁逻辑:
  对「已初审」的立场卡/技能卡（reading_status 含 分身已质证/你已质证/待你抽检/L2），
  机械核验其正文是否含 【查证清单】 块，且该块覆盖 handover-protocol §二 要求的 4 个子项:
    - 已核
    - 未核
    - 强制找茬
    - AI扩权方向自检
  缺任一 → 计为非合规初审（门禁应拒收）。

尾巴规则（v1.2 起·状态驱动，取代 v1.1 措辞一刀切）:
  v1.1 的问题：一刀切禁止任何卡出现「待你抽检」，但 pending 卡（TODO）标"待你抽检"语义本就正确，
  而门禁实现只在清单齐全时才抓 → 规则字面与代码行为不一致（文档/代码漂移）。
  v1.2 根治：尾巴合法性改由**进度表状态机**（唯一真相源）判定，状态即语义——
    - APPROVED 态（REVIEWED/BACKFILLED/COMPLIANT）→ 卡内禁一切 pending 措辞（含「你亲质证认可」与「机制层自动通过·皮叔09-08授权」两类；两类均禁 pending，但卡内主体措辞须如实区分）
      （待你抽检/待你抽验/待你质证/待你确认/待你复核）→ 违规报「approved态残留pending措辞」
    - PENDING 态（TODO/BLOCKED/未登记）→ pending 措辞合法，不判违规（避免误伤 51 张待质证卡）
  双源交叉：进度表状态（权威）与卡内 reading_status 交叉验证，使「表说 approved、卡还 pending」
  的假闭环（S819 2026-09-02 先例）由机器发现，而非依赖人记得（对齐愿景①全自动化）。
  ⛔ 不做反向交叉（pending 表 + approved 卡）：线A已认可/线B未回填是并存的合法错位，非风险方向。

范围:
  - 默认仅校验 初审日期 ≥ 2026-08-24 的卡（查证清单于该日由三明治L3建议新增·强制）。
    历史卡（<该日）豁免，避免对存量未回填卡误报。
  - --all 关闭日期豁免，全量校验。
  - --strict 模式：发现任意非合规即 exit 1（可作 CI/derive 前门禁）；默认 report 模式 exit 0。

用法:
  python3 verify_checklist_gate.py            # 报告模式（post-2026-08-24 范围）
  python3 verify_checklist_gate.py --all      # 全量（含历史豁免卡）
  python3 verify_checklist_gate.py --strict   # 报告 + 非合规即 exit 1（门禁语义）
  python3 verify_checklist_gate.py --json     # 机读输出

设计: 只读卡文件 + 打印报告；⛔不改任何文件（门禁=检测·非修复）。
依赖: 仅标准库。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, re, sys, glob
from datetime import date

HOME = os.path.expanduser("~")
AILIB_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "知识库", "AI学习库")
MANDATE_DATE = date(2026, 8, 24)  # 查证清单强制起始日

# 初审状态标记（含 L3/L4：2026-09-11 修复——derive 可将卡升到 L3/L4 使 L2 被覆盖，
# 若标记集不含 L3/L4 则该类卡脱离门禁池→真漏检。纳入后按日期豁免历史卡，不误伤存量）
REVIEW_MARKERS = ["分身已质证", "你已质证", "待你抽检", "L2（", "L3（", "L4（"]

# 查证清单 4 个必含子项（handover-protocol §二）
REQUIRED_SUBS = [
    ("已核", re.compile(r"已核\s*[:：]")),
    ("未核", re.compile(r"未核\s*[:：]")),
    ("强制找茬", re.compile(r"强制找茬")),
    ("AI扩权方向自检", re.compile(r"AI扩权方向自检|AI\s*扩权")),
]

# ── 人类网关语义（认可=闭环·v1.2 状态驱动·根治 v1.1 字面/实现漂移）────────
# 唯一真相源 = 分身质证进度表「四 线B 进度」表的状态列。状态即语义，措辞不再一刀切。
PROGRESS_TABLE = os.path.join(os.path.expanduser("[记忆共享中心]"), "自定义层", "待完成工作", "分身质证进度表.md")

# ⚠️ 更正（2026-09-21·一词一义根治）：下句把 APPROVED 单义为"你已质证认可"不准确——
#   APPROVED 实含两类主体：①你亲质证认可 ②机制层自动通过（皮叔 2026-09-08 分层终审授权）。
#   两类同禁 pending 措辞，但卡内主体措辞须如实区分：①写「你已质证」；②写「机制层自动通过·皮叔09-08授权」，
#   ⛔②禁写「你已质证」（虚报你的动作·铁律-022③）。该单义化是 14 张卡（S976-S990）伪债的判据源头。
# APPROVED = 你已质证认可 → 卡必须闭环，禁一切 pending 措辞
APPROVED_STATES = {"REVIEWED", "BACKFILLED", "COMPLIANT"}
# PENDING = 待你质证 / 卡住待决策 → pending 措辞合法（不误伤）
PENDING_STATES = {"TODO", "BLOCKED"}

# pending 措辞：approved 态卡内出现即违规（含 reading_status / 4子项 / 反例）
PENDING_TAIL = re.compile(r"待你\s*(抽[验检]|质证|确认|复核)|待你.{0,8}?抽[验检]")
TAIL_PATTERN = PENDING_TAIL  # v1.1 命名兼容别名

# 卡 ID 提取：文件名或表格卡名列 → S819 / K001
CARD_ID_RE = re.compile(r"^.*?#\s*([SK]\d+)", re.I)

CHECKLIST_HEAD = re.compile(r"【?查证清单】?|查证清单\s*$|\*\*查证清单\*\*", re.M)


def parse_frontmatter(text):
    """提取 frontmatter 字段。返回 dict（key 小写化）。"""
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip()
    return fm


def is_reviewed(fm):
    """reading_status 是否表示已初审。"""
    rs = fm.get("reading_status", "")
    return any(mk in rs for mk in REVIEW_MARKERS)


def card_date(fm):
    """卡日期（frontmatter date:），解析失败返回 None。"""
    d = fm.get("date", "")
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", d)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def load_progress_status():
    """解析进度表线B表格 → {card_id: 状态}。

    降级语义：进度表读不到/解析不出 → 返回空 dict → 所有卡按 PENDING 处理（不误伤），
    但会在报告中显式标注「进度表不可达」，⛔ 不静默降级。
    """
    status_map = {}
    if not os.path.exists(PROGRESS_TABLE):
        return status_map
    with open(PROGRESS_TABLE, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s.startswith("|"):
                continue
            cols = [c.strip() for c in s.strip("|").split("|")]
            if len(cols) < 3:
                continue
            m = CARD_ID_RE.match(cols[1])          # 卡名列 e.g. 立场卡#S819-xxx
            if not m:
                continue
            st = cols[2].upper()                    # 状态列
            if st in APPROVED_STATES or st in PENDING_STATES:
                status_map[m.group(1).upper()] = st
    return status_map


def checklist_compliant(text, status=None):
    """正文是否含合规的【查证清单】块（4 子项齐全 + 按状态判 pending 尾巴）。

    status: 进度表状态（APPROVED/PENDING/None=未登记）。None 按 PENDING 处理（不误伤）。
    """
    # 2026-09-13 根治：正文提及「【查证清单】」字样（如「查证清单从台账#240 初审实录结构化转录」）
    #   会抢占块起点 ⇒ 真块被判缺子项（S921/S922/S923 实锤；S979 正文提及同型）。
    #   改为**遍历所有匹配，取第一个四子项齐全的块**；全不齐才报最后一个的缺失。
    found_any = False
    result_ok = False
    last_missing = "无【查证清单】块"
    for m in CHECKLIST_HEAD.finditer(text):
        found_any = True
        rest = text[m.end():]
        nxt = re.search(r"\n#{1,2}\s", rest)
        block = rest[:nxt.start()] if nxt else rest
        missing = [name for name, pat in REQUIRED_SUBS if not pat.search(block)]
        if not missing:
            result_ok = True
            break
        last_missing = "缺子项: " + "/".join(missing)
    if not found_any:
        return False, "无【查证清单】块"
    if not result_ok:
        return False, last_missing
    # 尾巴规则（v1.2 状态驱动）：仅 APPROVED 态禁 pending 措辞——你已认可即闭环
    if status in APPROVED_STATES and PENDING_TAIL.search(text):
        return False, "approved态残留pending措辞(认可未闭环)"
    return True, "ok"


def writeback(compliant, noncompliant):
    """把线B 两数写回进度表（2026-09-13 WP5·治「同轴三数·手抄必烂」S922 同构）。

    ⛔ 只改这三处数字，不碰文件其他内容；写前备份 `<文件>.bak-writeback`。
    判据：写回后「进度表数字 == 脚本实算」⇒ 任何"表里一个数、脚本另一个数"都可被机械消除。
    """
    if not os.path.exists(PROGRESS_TABLE):
        print("⚠️ 进度表不可达，跳过 writeback：%s" % PROGRESS_TABLE)
        return False
    orig = open(PROGRESS_TABLE, encoding="utf-8").read()
    txt = re.sub(r"(- 线B_已合规:\s*)\d+", lambda m: m.group(1) + str(compliant), orig)
    txt = re.sub(r"(- 线B_非合规:\s*)\d+", lambda m: m.group(1) + str(noncompliant), txt)
    txt = re.sub(r"(✅COMPLIANT\s*)\d+(\s*/\s*TODO\s*)\d+",
                 lambda m: m.group(1) + str(compliant) + m.group(2) + str(noncompliant), txt)
    if txt == orig:
        print("✅ 进度表线B 数字已与脚本一致（合规 %d / 非合规 %d），未改动" % (compliant, noncompliant))
        return False
    with open(PROGRESS_TABLE + ".bak-writeback", "w", encoding="utf-8") as f:
        f.write(orig)
    with open(PROGRESS_TABLE, "w", encoding="utf-8") as f:
        f.write(txt)
    print("✅ 已写回进度表：线B 合规 %d / 非合规 %d（备份 .bak-writeback）" % (compliant, noncompliant))
    return True


def main():
    args = sys.argv[1:]
    strict = "--strict" in args
    all_cards = "--all" in args
    as_json = "--json" in args

    cards = []
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "*.md"))):
        base = os.path.basename(p)
        if base == "INDEX.md" or not (base.startswith("立场卡") or base.startswith("技能卡")):
            continue
        cards.append(p)

    status_map = load_progress_status()
    table_reachable = bool(status_map)

    total = reviewed = compliant = noncompliant = exempt = 0
    approved_in_scope = 0
    noncompliant_list = []
    exempt_list = []

    for p in cards:
        with open(p, encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        if not is_reviewed(fm):
            continue
        reviewed += 1
        cd = card_date(fm)
        # 日期豁免：非 --all 且 日期 < 强制日 → 豁免（历史卡）
        if not all_cards and cd is not None and cd < MANDATE_DATE:
            exempt += 1
            exempt_list.append((os.path.basename(p), str(cd)))
            continue
        cid_m = CARD_ID_RE.match(os.path.basename(p))
        status = status_map.get(cid_m.group(1).upper()) if cid_m else None
        if status in APPROVED_STATES:
            approved_in_scope += 1
        ok, reason = checklist_compliant(text, status)
        if ok:
            compliant += 1
        else:
            noncompliant += 1
            noncompliant_list.append((os.path.basename(p), reason))

    total = reviewed
    summary = {
        "scoped": not all_cards,
        "mandate_date": str(MANDATE_DATE),
        "reviewed_total": total,
        "compliant": compliant,
        "noncompliant": noncompliant,
        "exempt_historical": exempt,
        "noncompliant_rate": (noncompliant / (compliant + noncompliant) * 100.0)
                              if (compliant + noncompliant) else 0.0,
        "progress_table_reachable": table_reachable,
        "progress_registered": len(status_map),
        "approved_in_scope": approved_in_scope,
    }

    if as_json:
        import json
        print(json.dumps({
            **summary,
            "noncompliant_samples": noncompliant_list[:50],
            "exempt_samples": exempt_list[:20],
        }, ensure_ascii=False, indent=2))
    else:
        print("═══ 查证清单机械门禁 v1.2（状态驱动·认可=闭环）═══")
        print(f"范围: {'全量' if all_cards else 'post-' + str(MANDATE_DATE) + '（历史卡豁免）'}")
        print(f"已初审卡(纳入门禁): {total}")
        print(f"  ✅ 合规(含查证清单四子项): {compliant}")
        print(f"  ❌ 非合规(缺查证清单/子项): {noncompliant}")
        print(f"  ⏭️  历史豁免(<{MANDATE_DATE}): {exempt}")
        print(f"  🔗 进度表状态: 登记 {len(status_map)} 张 · scope内APPROVED态 {approved_in_scope} 张（禁pending措辞）")
        if not table_reachable:
            print("  ⚠️  进度表不可达/解析为空 → 尾巴规则降级为不判（⛔不静默：检查 PROGRESS_TABLE 路径）")
        if (compliant + noncompliant):
            print(f"  非合规率: {summary['noncompliant_rate']:.1f}%")
        if noncompliant_list:
            print("\n── 非合规卡（前 30，完整见 --json）──")
            for name, reason in noncompliant_list[:30]:
                print(f"  - {name}: {reason}")
        if exempt_list and not all_cards:
            print(f"\n⏭️  历史豁免 {exempt} 张（<{MANDATE_DATE} 初审·未强制查证清单），例: "
                  + ", ".join(n for n, _ in exempt_list[:5]))
        # 门禁结论
        if noncompliant == 0 and compliant > 0:
            print("\n✅ 门禁通过：所有在scope内已初审卡均含合规查证清单")
        elif noncompliant == 0 and compliant == 0:
            print("\nℹ️  无在scope内已初审卡（或全豁免）")
        else:
            print(f"\n🔴 门禁未过：{noncompliant} 张已初审卡缺查证清单 → 应拒收并补登")

    # ── WP5 write-back（2026-09-13）：线B 两数改**脚本代写**（治「同轴三数·手抄必烂」）──
    if "--writeback" in sys.argv:
        writeback(compliant, noncompliant)

    # 退出语义：strict 模式非合规即失败；默认 report 模式 exit 0（仅报告）
    if strict and noncompliant > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
