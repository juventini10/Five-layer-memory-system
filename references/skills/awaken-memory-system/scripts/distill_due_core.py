"""蒸馏逾期判定 · 公共口径单一真源（distill_due_core.py）

【为什么有这个文件】
2026-10-02 实测：同一份蒸馏中心，两个判定器给出相反答案——
  · distillation_scheduler.py（数字分身）→ 无逾期
  · awaken_distill_due_check.py（唤醒记忆）  → 7 项逾期
根因：同一判定口径被实现两次，抄文档的那个抄错了
（patrol.md §2 写的是"月段内最近一行"，B 写成了"月段内第一行"）。
依据：Skill架构规范 §6.1 指令编写规范「单一来源原则」——一个东西不出现在两个文件里。

【口径定义（唯一真源·patrol.md §2 的可执行形态）】——口径三要素，缺一即漂移
1. **分桶规则**：按类型字面归一化（`normalize_type`：括号/方括号内的轮次说明不构成新类型），
   或调用方指定 match 子串；⛔ 不可按 cells[1] 字面直接分桶（括号后缀会自成一类）
2. **取行规则**：剔除本脚本自生成的 TODO 标记区（否则调度器回读自己的输出 → 已完成项粘滞），
   全文按文档顺序倒序扫（文档天然时序=时间序），每种类型取**最后一条**账行的「预期下次」
3. **阈值判定**：非 YYYY-MM-DD 单元格跳过（一次性任务的 `—` 天然静默）；今天 >= 预期日期

【v8.3.1 修正·2026-10-02 终验逮到第二处口径漂移】
首版只把「取哪一行」上移，「怎么分桶」仍留在各脚本内，于是：
  · due_check 按 cells[1] 字面分桶 → 5 类（多出「统一蒸馏管道（终审落地+勘误）」）
  · scheduler 按 match 子串分桶 → 4 类（括号后缀归入主类）
同一天同结论、两套分桶 = 换了张脸的口径漂移。修法=分桶规则也上移（normalize_type 单一真源）。
教训：**口径 = 分桶 + 取行 + 阈值，三者缺一不可共；只上移其中一两个，下一轮照样漂。**

【与旧实现的口径差·显式声明】
scheduler 旧版只扫「最新月段」→ 类型在最新月段无行时整体隐身=调度盲区
（v1.1 已修）。本模块统一走全文倒序，消除该盲区且不再依赖月段切分。

【本模块不硬编码蒸馏类型】
类型表由调用方传入（各 Skill 的类型登记可能不同），本模块只管
"给定类型表 → 给出每种的预期下次 + 逾期判定"。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import datetime
import re
from typing import Dict, List, Optional, Tuple

TODO_REGION = re.compile(
    r"<!-- DISTILLATION-TODO:START -->.*?<!-- DISTILLATION-TODO:END -->",
    re.DOTALL,
)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
ROW_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

LEVEL_ORDER = {"🔴严重逾期": 0, "🟡已逾期": 1, "🔵即将到期": 2}


def strip_todo_region(content: str) -> str:
    """剔除调度器自生成的待做区，避免自读自写粘滞。"""
    return TODO_REGION.sub("", content)


def normalize_type(raw: str) -> str:
    """类型字面归一：括号内的轮次/批次说明不构成新类型。

    例：
      「🔄 统一蒸馏管道（3月补蒸馏）」      → 「🔄 统一蒸馏管道」
      「🔄 统一蒸馏管道（终审落地+勘误）」  → 「🔄 统一蒸馏管道」
      「🧠 成长箱蒸馏」                    → 「🧠 成长箱蒸馏」（无括号原样返回）
    依据：括号内容是「哪一轮/哪一批」的说明，不是另一种蒸馏类型（v8.3.1 单一真源）。
    """
    return re.split(r"[（(【\[]", raw, maxsplit=1)[0].strip()


def extract_expected(content: str, types_config: Dict[str, dict]) -> Dict[str, str]:
    """全文倒序扫，每种类型取最后一条账行的「预期下次」。

    types_config: {类型名: {"match": <行内子串>, "normalize": <bool·默认True>}}
      · match 由调用方定义（各 Skill 类型登记可能不同），本模块不硬编码
      · normalize=True（默认）时按 normalize_type() 归并括号后缀；
        调用方若要区分历史批次，可设 False 保留字面
    返回 {归一后类型名: expected_date_str}；无有效账行的类型不出现在结果中。
    """
    scan = strip_todo_region(content)
    lines = [l for l in scan.split("\n") if "|" in l]
    out: Dict[str, str] = {}
    for dtype, cfg in types_config.items():
        needle = cfg["match"]
        do_norm = cfg.get("normalize", True)
        for line in reversed(lines):
            if needle not in line:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            # ⚠️ 索引口径：strip('|') 后再 split，首尾空串被去掉 ⇒
            #    cells[0]=执行日期 cells[1]=类型 … cells[4]=预期下次
            #    （与 awaken_distill_due_check.parse_center 同写法·口径一致）
            #    2026-10-02 负例实证：直接 split('|') 会整体错位一位 → 类型名被当日期取走
            if len(cells) < 5 or not ROW_DATE_RE.match(cells[0]):
                continue  # 非账行（表头/分隔线/子节标题）
            raw_type = cells[1]
            # 「预期下次」= 末字段，⛔ 不倒序回扫找日期：
            #   一次性任务末字段为 `—`，回扫会一路退到 cells[0]（执行日期），
            #   把「执行日」误当「下次日」→ 刚做完就报逾期（2026-10-02 负例实证）。
            #   非日期 = 该行无预期下次 = 跳过本行，继续找更早的有效行。
            nxt = cells[-1].strip()
            if not ROW_DATE_RE.match(nxt):
                continue
            key = normalize_type(raw_type) if do_norm else raw_type
            out.setdefault(key, nxt)  # 倒序扫：先遇见的=最后一条
            break
    return out


def classify(expected_str: str, today: Optional[datetime.date] = None) -> Tuple[Optional[str], Optional[str]]:
    """三级阈值：🔵提前3天 / 🟡逾期1-7天 / 🔴逾期>7天。

    返回 (level|None, detail|None)；未到阈值返回 (None, None)。
    """
    if today is None:
        today = datetime.date.today()
    try:
        expected = datetime.datetime.strptime(expected_str, "%Y-%m-%d").date()
    except ValueError:
        return None, None
    days = (expected - today).days
    if days < 0:
        overdue = -days
        return ("🔴严重逾期" if overdue > 7 else "🟡已逾期", f"逾期{overdue}天")
    if days <= 3:
        return "🔵即将到期", ("今天到期" if days == 0 else f"{days}天后到期")
    return None, None


def check_overdue(content: str, types_config: dict, today: Optional[datetime.date] = None) -> list:
    """返回 [(级别, 类型, 预期日期, 说明)]，按级别升序（严重在前）。"""
    if today is None:
        today = datetime.date.today()
    rows = []
    for dtype, exp in extract_expected(content, types_config).items():
        level, detail = classify(exp, today)
        if level:
            rows.append((LEVEL_ORDER[level], level, dtype, exp, detail))
    return sorted(rows, key=lambda r: (r[0], r[2]))
