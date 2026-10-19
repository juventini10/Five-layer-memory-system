#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""awaken-memory-system 8.0 阶段③ — 蒸馏待办三级阈值检测（patrol.md §2 逻辑·脚本化）

输入：蒸馏中心.md 路径（默认 [记忆共享中心]/记忆蒸馏/蒸馏中心.md·可用位置参数覆盖）
输出：每行一条待办 DUE|<级别>|<蒸馏类型>|<预期下次>|<说明>；无待办输出 NONE
退出码：0=检测成功（含无待办）；1=文件缺失/读取失败
设计约束：⛔不硬编码蒸馏类型（动态解析·未来新增类型自动支持·patrol.md §2）；
          ⛔只读不写（检测不越界写入·跨 Skill 边界）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import datetime
import re
import sys
from pathlib import Path

DEFAULT_CENTER = Path('[记忆共享中心]') / "记忆蒸馏" / "蒸馏中心.md"
TODAY = datetime.date.today()

LEVEL_ORDER = {"🔴严重逾期": 0, "🟡已逾期": 1, "🔵即将到期": 2}


def parse_center(path: Path):
    """提取 (月段, 蒸馏类型, 预期下次) 三元组。

    ⛔ 判定口径已上移至 distill_due_core（单一真源）——本函数仅做
       「月段标签归属」的兼容层，供 latest_expected() 的旧签名使用；
       真值取数一律走 core.extract_expected（全量倒序，消除跨月盲区）。
    依据：指令编写规范 §6.1 单一来源原则（同口径两处实现=必漂移·2026-10-02 实锤）。
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR 读取失败: {exc}", file=sys.stderr)
        return None

    rows = []
    month = None
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            m = re.match(r"^## (\d{4}-\d{2})\s*$", stripped)
            month = m.group(1) if m else None
            continue
        if month is None or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        dm = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", cells[4])
        if not dm:
            continue
        nxt = datetime.date(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
        rows.append((month, cells[1], nxt))
    return rows


def _core():
    """加载公共口径模块 distill_due_core.py（与本脚本同目录·随 Skill 自分发）。

    🔴 2026-10-03 位置根治：原为 `Path.home()/"[记忆共享中心]"/"开发工具"/...` 硬编码绝对路径
       ⇒ ① 开发工具/ 是作者侧资产·不入包 ⇒ 端用户装完必然 ModuleNotFoundError
       ② 依赖记忆中心目录名叫「个人AI档案」，换名即失效。
       现改为同目录相对解析 —— 本脚本与 core 同住 awaken/scripts/，随 Skill 走·到哪都能加载。
       判据依据：triwich L2 裁决「逻辑中立 / 物理位置 / 路径解析」三属性正交：
       中立性由「双方消费同一份代码」保证，不依赖代码躺在哪个目录。
    """
    import importlib.util
    p = Path(__file__).resolve().parent / "distill_due_core.py"
    if not p.exists():
        raise FileNotFoundError(
            f"蒸馏判定公共口径模块缺失: {p} —— 本 Skill 自包含件，请检查 awaken/scripts/ 是否完整"
        )
    spec = importlib.util.spec_from_file_location("distill_due_core", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def types_from_rows(rows):
    """由已解析账行反推类型配置（match = 类型字面 · 归一化由 core 负责）。

    ⛔ 不可在此处按字面分桶——括号后缀会自成一类（2026-10-02 终验实证）。
       归一化统一交给 distill_due_core.normalize_type()，口径单真源。
    """
    return {typ: {"match": typ, "normalize": True} for (_m, typ, _n) in rows}


def expected_from_center(path: Path):
    """公共口径入口：读蒸馏中心 → {类型: 预期下次字符串}。失败返回 None。"""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR 读取失败: {exc}", file=sys.stderr)
        return None
    rows = []
    month = None
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("#"):
            m = re.match(r"^## (\d{4}-\d{2})\s*$", s)
            month = m.group(1) if m else None
            continue
        if month is None or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 5 or not re.match(r"^\d{4}-\d{2}-\d{2}$", cells[0]):
            continue
        rows.append((month, cells[1], None))
    cfg = {typ: {"match": typ} for (_m, typ, _n) in rows}
    return _core().extract_expected(content, cfg)


def latest_expected(rows):
    """兼容层：保持旧签名 (月段, 预期下次)，真值委托公共口径 distill_due_core。

    ⛔ 原实现为「月段内取第一行」，与 patrol.md §2 声明的「月段内最近一行」
       相反 —— 2026-10-02 实锤致 1 项误报 + 6 项补蒸馏噪音。
    依据：指令编写规范 §6.1 单一来源原则 · 真源 = distill_due_core。
    """
    import datetime as _dt
    if not rows:
        return {}
    # 从 rows 反推类型表后走公共口径（归一化在 core 内完成·此处不自行分桶）
    cfg = {typ: {"match": typ, "normalize": True} for (_m, typ, _n) in rows}
    center = Path('[记忆共享中心]') / "记忆蒸馏" / "蒸馏中心.md"
    try:
        content = center.read_text(encoding="utf-8")
    except OSError:
        content = ""
    exp = _core().extract_expected(content, cfg) if content else {}
    # 保留月段归属（取 rows 里该类型最后一次出现的月段）
    seg = {}
    for m, typ, _n in rows:
        seg[typ] = m
    out = {}
    for typ, s in exp.items():
        try:
            y, mo, d = (int(x) for x in s.split("-"))
            out[typ] = (seg.get(typ, ""), _dt.date(y, mo, d))
        except (ValueError, AttributeError):
            continue
    return out


def classify(nxt: datetime.date):
    """三级阈值（patrol.md §2）·口径真源 = distill_due_core.classify（FU-81 丙方案落地 2026-10-10）。

    原实现为本文件私有一份，与 core.classify 同构（同一逻辑双写）——
    口径=分桶+取行+阈值三要素，10-02 v8.3.1 只上了前两者，阈值是残留的结构欠账
    （改一处阈值另一处必漂）。本次落地=三要素全链单真源；
    dashboard（awaken_health_dashboard 经 ddc.classify）自动随本行同口径。
    """
    return _core().classify(nxt.isoformat(), TODAY)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CENTER
    rows = parse_center(path)
    if rows is None:
        sys.exit(1)
    due = []
    for typ, (_month, nxt) in latest_expected(rows).items():
        level, detail = classify(nxt)
        if level:
            due.append((LEVEL_ORDER[level], f"DUE|{level}|{typ}|{nxt.isoformat()}|{detail}"))
    if not due:
        print("NONE")
        return
    for _, line in sorted(due, key=lambda x: (x[0], x[1])):
        print(line)


if __name__ == "__main__":
    main()
