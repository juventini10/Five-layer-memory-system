#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hermes 端 · 五系统文件 100% 适配机械校验器（参照端可配置）

真源  ：语义项清单本体（作者侧 = 记忆蓝图 06-100%复刻源文件清单.md·
        端用户态用 --list 指向自备清单；⛔ 清单缺失时本脚本拒出结论，不做「无清单即全绿」）
被测  ：Hermes 端每轮真实加载面
        ① ~/.hermes/SOUL.md                       （恒定加载位）
        ② ~/.hermes/memories/USER.md               （波动层·条件加载）
        ③ ~/.hermes/memories/MEMORY.md             （波动层·条件加载）
        ④ 童灵恒驻核实际注入段                      （复现 doenglingz-twin._core_section
                                                    的 head + L6 拼接逻辑·非全量 core_slice）
参照  ：参照端的五系统文件本体（默认 ~/.workbuddy/{SOUL,IDENTITY,USER,MEMORY}.md
        + app-config.json 的 personalization.customPrompt）——⛔ 路径可由 --ref-root / --ref-prompt 覆盖

判据  ：清单每条给 anchors——``a|b|c`` = OR（任一命中即 PASS）·``a+b`` = AND 组（组内须全在）
        ⚠️ ⛔ 只锚标题=假绿机器：标题在就 PASS，内容不在也 PASS ⇒ 语义项一律用内容探针
出口  ：stdout 报告（逐条 ✅/❌ + 汇总）+ rc 0(全绿)/1(有缺口)
台账  ：--ledger <path> 时追加 JSONL（端隔离·⛔不落他端目录）

⛔ 本脚本只读不写 Hermes 端任何加载位文件——它是判据不是施工队。
   缺口的修法见清单「修法」列，改加载位是另一件事（铁律001 先看清）。
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import json
import os
import re
import sys
import time
from typing import Any

# ── 路径 ────────────────────────────────────────────────────────────────
HOME = os.path.expanduser("~")
HG = os.path.join(HOME, ".hermes")
# 参照端配置根（端用户态可覆盖：--ref-root）——默认 WorkBuddy 的本尊端
WB = os.path.join(HOME, ".workbuddy")
# 参照端 customPrompt 所在的 app-config.json（--ref-prompt 可覆盖）
REF_PROMPT = os.path.join(WB, "app", "app-config.json")
# 童灵切片目录解析序：--slices 显式 > <hermes-root>/doenglingz/runtime_paths.json
# 的 twin_slices 键（安装器写真实落点·端中立）> 占位符（未装态）
SLICES = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身", "K2切片蒸馏", "slices")


def resolve_slices(hermes_root: str, explicit: str = "") -> str:
    """切片目录解析。⛔ 找不到时**如实报**——不静默回落成「恒驻核为空 ⇒ 照样全绿」。"""
    if explicit:
        return os.path.expanduser(explicit)
    rp_path = os.path.join(hermes_root, "doenglingz", "runtime_paths.json")
    try:
        with open(rp_path, encoding="utf-8") as fh:
            key = json.load(fh).get("twin_slices")
        if key and os.path.isdir(key):
            return key
    except Exception:
        pass
    return SLICES
LIST_PATH = os.path.join(
    os.path.expanduser("~"), "[记忆共享中心]", "记忆蓝图", "02_设计理念", "02-平台端适配类",
    "Hermes布洛陀设计哲学", "06-100%复刻源文件清单.md"
)

# 童灵恒驻段上限（须与 doenglingz-twin/__init__.py 的 _SECTION_MAX_CHARS 一致）
SECTION_MAX_CHARS = 3800


def _read(p: str) -> str:
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _core_resident() -> str:
    """复现 doenglingz-twin 的两段恒驻拼接（2026-10-02 起为 core + l1 两段）。

    段① doenglingz.core = core_slice 首个 '\\n## ' 之前 + L6
    段② doenglingz.l1   = core_slice 首个 '\\n## ' 之后（L1 身份骨架全段）

    ⛔ 两条不许简化：
      ① 不许「读整个 core_slice」当段①——那是 2026-08-20 假绿的成因；
      ② 不许只取段①而漏段②——L1 曾被静默丢弃 3 周（2026-10-02 修复）。
    """
    core = _read(os.path.join(SLICES, "core_slice.md"))
    if not core:
        return ""
    idx = core.find("\n## ")
    head = core[:idx] if idx > 0 else core
    l1 = core[idx:].lstrip() if idx > 0 else ""
    l6 = _read(os.path.join(SLICES, "L6_反向约束.md"))
    body = head.rstrip()
    if l6:
        body += "\n\n---\n\n" + l6.strip()
    if len(body) > SECTION_MAX_CHARS:
        body = body[:SECTION_MAX_CHARS].rstrip() + "\n\n（本段已按 4000 字预算截断·完整内容见 slices/）"
    if l1:
        if len(l1) > SECTION_MAX_CHARS:
            l1 = l1[:SECTION_MAX_CHARS].rstrip() + "\n\n（L1 段已按 4000 字预算截断·完整内容见 slices/core_slice.md）"
        body += "\n\n---\n\n" + l1
    return body


def resident_faces() -> dict[str, str]:
    """Hermes 端每轮真实加载面（权威源=实盘·铁律016）。"""
    return {
        "SOUL.md": _read(os.path.join(HG, "SOUL.md")),
        "memories/USER.md": _read(os.path.join(HG, "memories/USER.md")),
        "memories/MEMORY.md": _read(os.path.join(HG, "memories/MEMORY.md")),
        "童灵恒驻核(实际注入)": _core_resident(),
    }


# ── 清单解析 ────────────────────────────────────────────────────────────
# ID 前缀 → 来源文件（报告分组用·⛔ 不用逐行重复写来源列）
SRC_GROUP = {
    "S": "WB SOUL.md（三条实线）",
    "I": "WB IDENTITY.md（身份骨架）",
    "C": "WB customPrompt（顶层指令 9 条）",
    "U": "WB USER.md（画像 + 童灵内核）",
    "M": "WB MEMORY.md（跨项目长期记忆）",
}

ROW = re.compile(r"^\|\s*(?P<id>[A-Z]{1,2}-\d{2})\s*\|(?P<rest>.+)\|\s*$")


def parse_listing(path: str) -> list[dict[str, Any]]:
    """从清单 markdown 表解析条目。

    表头约定：| ID | 来源 | 语义项 | anchors | 修法 |
    anchors 列：``kw`` 反引号包裹的判据关键词；多个 ``kw`` 之间为 **OR**（任一命中即 PASS）；
    单个 ``kw`` 内的 ``a|b|c`` 亦为 OR 变体（避免表格里出现裸竖线破表）。
    例：| U-51 | ... | ``归因模式`` / ``内部不稳定归因`` | ... |   ← 二者命中任一即 PASS
    """
    txt = _read(path)
    if not txt:
        sys.exit(f"❌ 清单不存在：{path}")
    items: list[dict[str, Any]] = []
    for line in txt.split("\n"):
        m = ROW.match(line.strip())
        if not m:
            continue
        # 先把转义竖线还原成占位符，再按裸竖线切列（表格内 ``a\|b`` 不得破列）
        rest = m.group("rest").replace("\\|", "\x00")
        cells = [c.strip() for c in rest.split("|")]
        if len(cells) < 3:
            continue
        item_id = m.group("id")
        sem, anchor_cell = cells[0], cells[1]
        fix = cells[2] if len(cells) > 2 else ""
        groups: list[str] = []
        for raw in re.findall(r"``([^`]+)``", anchor_cell):
            for alt in raw.replace("\x00", "|").split("|"):
                alt = alt.strip()
                if alt:
                    groups.append(alt)
        # N/A 标记写在「修法」列首（``N/A:`` 前缀）——销账须带理由，⛔ 禁删行
        na = ""
        clean_fix = re.sub(r"[`*]", "", fix).replace("\x00", "|").strip()
        m_na = re.match(r"^N/A\s*[:：]\s*(.+)$", clean_fix, re.S)
        if m_na:
            na = m_na.group(1).strip() or "未写理由"
        items.append({
            "id": item_id,
            "src": SRC_GROUP.get(item_id.split("-")[0], item_id.split("-")[0]),
            "sem": re.sub(r"[`*]", "", sem).strip(),
            "anchors": groups,
            "fix": clean_fix,
            "na": na,
        })
    if not items:
        sys.exit(f"❌ 清单解析出 0 条：{path}（表头/ID 格式不匹配？）")
    # 自检：文件内 ID 数必须 == 解析出的条数（防「行被吞/行被并」静默漏判）
    # ⚠️ 2026-10-02 实测踩过：正则批量改修法列时把 4 行的表格分隔符吃掉，
    #    行尾 `|` 消失 ⇒ 该行解析失败 ⇒ 清单少 4 条却仍报 rc=0（假绿·自伤型）。
    file_ids = re.findall(r"^\|\s*([A-Z]{1,2}-\d{2})\s*\|", txt, re.M)
    if len(file_ids) != len(items):
        only_file = sorted(set(file_ids) - {i["id"] for i in items})
        sys.exit(
            "❌ 清单行数与解析条数不一致（⛔ 疑似表格行被吞/被并·拒绝出结论）\n"
            f"   文件内 ID {len(file_ids)} 个 / 解析出 {len(items)} 条\n"
            f"   只在文件里、未解析到：{only_file or '（重复 ID 或格式异常）'}\n"
            "   修法：检查这些行是否缺行尾 `|` 或行内混入了第二个 `| ID |`。"
        )
    return items


def check(items: list[dict[str, Any]], faces: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for it in items:
        hits: list[str] = []
        for face, body in faces.items():
            if not body or not it["anchors"]:
                continue
            # AND 组（``a+b``）组内须全在；OR 组任一命中即可
            ok = any(
                all(part in body for part in kw.split("+"))
                for kw in it["anchors"]
            )
            if ok:
                hits.append(face)
        if it.get("na"):
            # 销账条目：不判 PASS 也不判 GAP，单列 N/A——⛔ 删行=判据消失，防此
            out.append({**it, "pass": False, "hits": [], "na_hit": True})
        else:
            out.append({**it, "pass": bool(hits), "hits": hits, "na_hit": False})
    return out


def plugin_registers_l1() -> bool:
    """断言插件源码真的注册了段② `doenglingz.l1`。

    ⚠️ 为什么必须单独查：校验器读的是 **slices 文件**，⛔ 不读插件代码。
    若有人把 `ctx.register_system_prompt_section("doenglingz.l1", ...)` 删掉
    （负控C 实测过），内容仍全在 slices 里 ⇒ 校验器照样 rc=0 ⇒ **假绿**。
    ⇒ 恒驻面 = 「切片内容在」× 「插件真注册」两件事的交集，缺一即 GAP。
    """
    plug = _read(os.path.join(HG, "plugins/doenglingz-twin/__init__.py"))
    return '"doenglingz.l1"' in plug and "_l1_section" in plug


def report(rows: list[dict[str, Any]], quiet: bool = False) -> str:
    out: list[str] = []
    cur = None
    for r in rows:
        if r["na_hit"]:
            if quiet:
                continue
            if r["src"] != cur:
                cur = r["src"]
                out.append(f"\n── 来源：{cur} " + "─" * max(0, 46 - len(cur)))
            out.append(f"➖ {r['id']}  {r['sem'][:46]:<46}  N/A·{r['na'][:44]}")
            continue
        if r["pass"] and quiet:
            continue
        if r["src"] != cur:
            cur = r["src"]
            out.append(f"\n── 来源：{cur} " + "─" * max(0, 46 - len(cur)))
        mark = "✅" if r["pass"] else "❌"
        where = ("命中 " + "、".join(r["hits"])) if r["pass"] else "零命中"
        out.append(f"{mark} {r['id']}  {r['sem'][:46]:<46}  {where}")
        if not r["pass"] and r["fix"]:
            out.append(f"      ↳ 修法：{r['fix']}")
    judged = [r for r in rows if not r["na_hit"]]
    na = [r for r in rows if r["na_hit"]]
    tot = len(judged)
    ok = sum(1 for r in judged if r["pass"])
    out.append("\n" + "=" * 64)
    out.append(f"判 {tot} 条 · N/A {len(na)} 条 · PASS {ok} · GAP {tot - ok}"
               f" · 适配率 {ok / tot * 100:.1f}%" if tot else "清单为空")
    out.append("判据：「✅ 100%」当且仅当 GAP = 0。GAP>0 时禁止对外声称已 100% 适配。")
    # ⛔ quiet 模式（守卫批跑）：全绿时⛔ 不打 N/A 提示行——该行含「缺口」二字会被
    #    守卫的 _ALARM_MARKS 误判成告警（实测假阳性·降噪纪律：全绿不写盘）
    if na and not quiet:
        out.append("N/A 条目已销账（带理由）· ⛔ 禁删行——删行=判据消失，下次又判不出缺口。")
    return "\n".join(out)


def main() -> int:
    global WB, REF_PROMPT, HG, SLICES, LIST_PATH  # noqa: PLW0603 · 端用户态参数化
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=LIST_PATH, help="清单路径（默认 Hermes 设计哲学 06-）")
    ap.add_argument("--ledger", default="", help="JSONL 台账路径（端隔离·建议 ~/.hermes/hermes_wb_parity_ledger.jsonl）")
    ap.add_argument("--quiet", action="store_true", help="只输出汇总+GAP 明细（⛔ 不打 ✅ 行·守卫批跑用）")
    ap.add_argument("--ref-root", default=WB,
                    help="参照端配置根（默认 ~/.workbuddy·端用户态指向自己参考的端）")
    ap.add_argument("--ref-prompt", default="",
                    help="参照端 customPrompt 所在的 app-config.json（默认 <ref-root>/app/app-config.json）")
    ap.add_argument("--hermes-root", default=HG, help="Hermes 配置根（默认 ~/.hermes）")
    ap.add_argument("--slices", default="", help="童灵切片目录（默认读 <hermes-root>/doenglingz/runtime_paths.json 的 twin_slices）")
    args = ap.parse_args()
    WB = os.path.expanduser(args.ref_root)
    REF_PROMPT = os.path.expanduser(args.ref_prompt) if args.ref_prompt else os.path.join(WB, "app", "app-config.json")
    HG = os.path.expanduser(args.hermes_root)
    SLICES = resolve_slices(HG, args.slices)
    # 切片目录不存在 ⇒ 童灵恒驻核测不了 ⇒ 该腿报缺（⛔ 不当空字符串继续跑）
    slices_missing = not os.path.isdir(SLICES)
    # 清单不存在 ⇒ 拒出结论（⛔ 不做「无清单即全绿」——那正是假绿制造机）
    if not os.path.isfile(os.path.expanduser(args.list)):
        sys.exit("❌ 语义项清单不存在：" + os.path.expanduser(args.list)
                 + "\n   ⛔ 无清单不出结论：把「没清单」当「全绿」是最大的假绿。")

    items = parse_listing(args.list)
    rows = check(items, resident_faces())
    gaps = [r["id"] for r in rows if not r["na_hit"] and not r["pass"]]
    # 恒驻面第二腿：插件是否真注册段②（负控C 揭穿的假绿通道）
    l1_ok = plugin_registers_l1()
    if not l1_ok:
        gaps.append("PLUGIN-L1-REG")
    if slices_missing:
        gaps.append("SLICES-MISSING")
    print(f"清单：{args.list}")
    print(report(rows, quiet=args.quiet))
    if not l1_ok:
        print("❌ PLUGIN-L1-REG  插件未注册段② doenglingz.l1"
              "（L1 身份骨架在 slices 里但没进 system prompt ⇒ 假绿）")
    if slices_missing:
        print("❌ SLICES-MISSING  童灵切片目录不存在：" + SLICES
              + "\n   ⛔ 恒驻核测不了就不出 100% 结论（--slices 指定，或装出 runtime_paths.json 的 twin_slices 键）")

    if args.ledger:
        rec = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "judged": sum(1 for r in rows if not r["na_hit"]),
            "na": sum(1 for r in rows if r["na_hit"]),
            "pass": sum(1 for r in rows if r["pass"]),
            "plugin_l1_registered": l1_ok,
            "gaps": gaps,
        }
        os.makedirs(os.path.dirname(args.ledger), exist_ok=True)
        with open(args.ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
