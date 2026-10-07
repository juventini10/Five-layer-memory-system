#!/usr/bin/env python3
"""
update_snapshot_from_diary.py — 懒加载模式快照实时更新脚本（自宣版本=宿主 Skill 版本·v8.3.1）

归属：awaken-memory-system自有脚本（不依赖daily-buddy）
功能：读取日记YAML frontmatter，在动态状态快照.md的「最近变更摘要」表格中新增/更新行
      v7.35 新增：历史缺失日回填（默认回看14天窗口）——消除"多日未触发小美→快照留空→
      下次唤醒需AI逐篇读日记补数据"的读取债（2026-09-10 皮叔问"小美为什么那么久"驱动）
设计：只操作「最近变更摘要」表格，不触碰快照其他部分（安全·原子性）
依据：2026-09-02 小美轻量模式快照滞后10小时事故·童灵裁决懒加载模式
      2026-09-10 快照滞后7天（9/4-9/9无行）事故·缺失日回填
      v7.36 新增：滚动归档（默认14天窗口）——回填侧有窗口而淘汰侧无窗口，表格只进不出
      （实测 102 行/29.8KB 单调增长），把超窗行迁入 情境层/快照历史存档.md。
      与 --backfill-window 同值同源：写入侧窗口意识补齐淘汰侧对称（2026-09-20
      皮叔问"快照越积累越多"驱动·S521 判据：只许降频率/冗余，不许降判据粒度）

Exit code语义：
  0 = 已更新（新增缺失日行 和/或 更新当日行 和/或 本轮归档行>0，至少1项·v8.1.3审查N2口径同步）
  1 = 失败（快照文件不存在/「最近变更摘要」表格未找到/写入异常/--today 非法/归档守卫跳过·v8.1.4审查F-3/F-6）
  2 = 无需更新（无缺失日 且 当日行五字段一致——含"今日日记尚未生成"情形，stdout明示原因）

回填安全规则（Fail-Closed·只填可信数据）：
  ① 历史日（非今日）只回填**已封口**日记（frontmatter 有 review_sealed_sig）——
     未封口=数据未定，填入=脏数据污染蒸馏与月报。
  ② 骨架日记（未封口 且 tomato=0 且 rating∈{待评定,待填,空}）一律跳过——
     防止把"0🍅/评级待评定"这类占位骨架写成看似真实的记录行。
  ③ 跳过的日期✅DO在 stdout 逐条列出跳过原因（有痕跳过≠静默跳过·Skill架构规范§③）。

用法：
  python3 update_snapshot_from_diary.py [--snapshot PATH] [--diary PATH] [--dry-run]
                                       [--backfill-window N] [--no-backfill]
                                       [--archive-window N] [--no-archive] [--today YYYY-MM-DD]

诚实边界（P1信息降级披露）：
  更新为整行替换（说明列重建为「{番茄}🍅/睡眠…/P1 待提取/评级…」）——原行中
  其他端写入的 P1 完成信息（如「P1 3/3✅」）会被覆盖为「待提取」且脚本不回填，
  属已知降级；轻量模式输出时如需 P1 完成度以日记正文为准。
  能量字段例外（复核N2）：fm缺energy_actual时保留原行真实能量（prev_energy），
  其余字段仍整行重建。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 回填/归档窗口默认值单一常量（v8.1.2·审查A10：字面量双写"默认同值"≠"同值同源"，改一处即重新不对称）
DEFAULT_WINDOW = 14


def parse_args():
    parser = argparse.ArgumentParser(description="懒加载模式快照实时更新脚本")
    parser.add_argument("--snapshot", default=None, help="动态状态快照.md路径（默认~/[记忆共享中心]/情境层/动态状态快照.md）")
    parser.add_argument("--diary", default=None, help="当日日记路径（默认自动推导~/[日记仓库]/1-每日计划/01-日记/YYYY-MM/YYYY-MM-DD.md）")
    parser.add_argument("--dry-run", action="store_true", help="只输出将更新的内容，不实际写入")
    parser.add_argument("--backfill-window", type=int, default=DEFAULT_WINDOW, help=f"历史缺失日回看窗口（天·默认{DEFAULT_WINDOW}）")
    parser.add_argument("--no-backfill", action="store_true", help="关闭历史缺失日回填，只处理当日行（v7.34行为）")
    parser.add_argument("--archive-window", type=int, default=DEFAULT_WINDOW, help=f"「最近变更摘要」保留窗口（天·默认{DEFAULT_WINDOW}）→ 超窗行迁入历史存档（v7.36）")
    parser.add_argument("--no-archive", action="store_true", help="关闭滚动归档，保留表格全部行（v7.35行为）")
    parser.add_argument("--today", default=None, help="调试/回归用：冻结\"今日\"（YYYY-MM-DD）——eval-set#33 跨年哨兵黑盒复现入口（v8.1.3·审查A8）")
    return parser.parse_args()


def get_default_paths(today=None):
    """推导默认路径（v8.1.4·审查F-6：today 可注入——--today 必须同时冻结日记路径，否则黑盒复现入口会把真实今日数据写进冻结日）"""
    home = Path.home()
    today = today or datetime.now()
    snapshot = home / "[记忆共享中心]" / "情境层" / "动态状态快照.md"
    diary = home / "[日记仓库]" / "1-每日计划" / "01-日记" / today.strftime("%Y-%m") / f"{today.strftime('%Y-%m-%d')}.md"
    return snapshot, diary


ARCHIVE_PATH = "[记忆共享中心]" / "情境层" / "快照历史存档.md"


def diary_path_for(day):
    """按日期推导日记路径（与 get_default_paths 同口径）"""
    home = Path.home()
    return home / "[日记仓库]" / "1-每日计划" / "01-日记" / day.strftime("%Y-%m") / f"{day.strftime('%Y-%m-%d')}.md"


def read_diary_frontmatter(diary_path):
    """读取日记YAML frontmatter，提取关键字段"""
    if not diary_path.exists():
        return None, f"日记文件不存在: {diary_path}"

    content = diary_path.read_text(encoding="utf-8")
    # 提取YAML frontmatter（---之间的内容）
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None, "日记文件无YAML frontmatter"

    fm = match.group(1)

    # 提取字段（简单解析，不依赖PyYAML）
    data = {}

    # rating（顶层字段）
    rating_match = re.search(r"^rating:\s*(\S+)", fm, re.MULTILINE)
    if rating_match:
        data["rating"] = rating_match.group(1)

    # achievement_data 嵌套字段
    # tomato
    tomato_match = re.search(r"^\s+tomato:\s*(\d+)", fm, re.MULTILINE)
    if tomato_match:
        data["tomato"] = int(tomato_match.group(1))

    # sleep_duration
    sleep_match = re.search(r"^\s+sleep_duration:\s*([\d.]+)", fm, re.MULTILINE)
    if sleep_match:
        data["sleep_duration"] = float(sleep_match.group(1))

    # energy_actual
    energy_match = re.search(r"^\s+energy_actual:\s*(\d+)", fm, re.MULTILINE)
    if energy_match:
        data["energy_actual"] = int(energy_match.group(1))

    # review_sealed_sig（封口签名，用于判断日记是否已封口）
    sealed_match = re.search(r"^review_sealed_sig:\s*(\S+)", fm, re.MULTILINE)
    if sealed_match:
        data["sealed"] = True
        data["sealed_sig"] = sealed_match.group(1)
    else:
        data["sealed"] = False

    # 验证必需字段
    required = ["tomato", "sleep_duration", "rating"]
    missing = [f for f in required if f not in data]
    if missing:
        return None, f"日记frontmatter缺少必需字段: {', '.join(missing)}"

    return data, None


def is_skeleton(data):
    """骨架日记判定（Fail-Closed·v7.35）：未封口 + tomato=0 + rating 为占位值
    —— 识别"日记骨架已生成但尚未复盘填数"的状态，避免把占位数据写成记录行"""
    if data.get("sealed"):
        return False
    placeholder_ratings = {"待评定", "待填", "待提取", "", "-", '"待评定"', "''"}
    return data.get("tomato", 0) == 0 and str(data.get("rating", "")).strip() in placeholder_ratings


def format_sleep_duration(hours):
    """将睡眠时长（小时）格式化为人类可读格式，如3.95→3h57m"""
    total_minutes = int(round(hours * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}h{m}m"


def build_summary_row(data, day, prev_energy=None):
    """构建「最近变更摘要」表格的行
    prev_energy：该行已有的能量值——fm缺energy_actual时保留原值，防跨端真实数据被"?"覆盖（复核N2）"""
    date_str = day.strftime("%m-%d")
    tomato = data.get("tomato", "?")
    sleep = format_sleep_duration(data["sleep_duration"])
    rating = data.get("rating", "?")
    energy = data.get("energy_actual") if data.get("energy_actual") is not None else (prev_energy if prev_energy else "?")
    sealed = data.get("sealed", False)

    # 格式对齐现有表格：{番茄}🍅/睡眠{睡眠}/P1 待提取/评级{评级}/能量{能量}
    # P1完成情况从frontmatter中无法直接提取，标注"待提取"（后续版本可从日记正文grep）
    sealed_mark = "✓" if sealed else "⏳未封口"
    summary = f"{tomato}🍅/睡眠{sleep}/P1 待提取/评级{rating}/能量{energy}/封口{sealed_mark}"
    row = f"| {date_str} | awaken脚本 | {day.strftime('%m/%d')}日记同步 | {summary} |"
    return row


def find_recent_changes_table(snapshot_content):
    """找到「最近变更摘要」表格的位置，返回(表头行号, 分隔线行号, 第一行数据行号)"""
    lines = snapshot_content.split("\n")
    table_start = None

    for i, line in enumerate(lines):
        if "### 📝 最近变更摘要" in line:
            table_start = i
            break

    if table_start is None:
        return None, None, None

    # 找到表格头（| 日期 | 工具 | 文件 | 说明 |）
    header_idx = None
    for i in range(table_start, min(table_start + 10, len(lines))):
        if lines[i].strip().startswith("| 日期 |"):
            header_idx = i
            break

    if header_idx is None:
        return None, None, None

    # 分隔线是表头的下一行
    separator_idx = header_idx + 1

    # 第一行数据是分隔线的下一行
    first_data_idx = separator_idx + 1

    return header_idx, separator_idx, first_data_idx


DATE_ROW_PATTERN = r"^\|\s*(?:(\d{4})-)?(\d{2}-\d{2})\s*\|"


def _has_detached_date_rows(lines, stop_idx):
    """表格终止位之后是否仍存在日期行（结构性断链探测·v8.1.4b·R4-NP-3）。"""
    return any(re.match(DATE_ROW_PATTERN, ln.strip()) for ln in lines[stop_idx:] if ln.strip().startswith("|"))


def resolve_row_date(md, yr, today):
    """MM-DD(/YYYY-MM-DD) → datetime.date：带显式年直接取；裸 MM-DD 大于今日属去年（跨年回退·与仪表盘同口径）。非法日期抛 ValueError 由调用方处理。"""
    if yr:
        return datetime(int(yr), int(md[:2]), int(md[3:])).date()
    d = today.replace(month=int(md[:2]), day=int(md[3:]))
    if d.date() > today.date():
        d = d.replace(year=today.year - 1)
    return d.date()


def get_existing_dates(snapshot_content, today=None):
    """收集「最近变更摘要」表格日期 → (dict[date → 行号], 非法日期行数)
    v8.1.4·审查F-10根治：键从 MM-DD 升级为完整日期（显式年优先，裸 MM-DD 跨年回退）——
    ⛔不得只用 MM-DD 做键，原因是混合年表中 "09-20"(推断2026) 与 "2025-09-20" 碰撞，
    当日行会定位到去年那一行并被今日数据覆盖（数据污染不可逆·A/B实跑证伪v8.1.3键归一方案）。
    v8.1.3·审查N1：双格式识别（YYYY-MM-DD 跨端形态）；v8.1.3·审查N3：无行数上限。"""
    today = today or datetime.now()
    lines = snapshot_content.split("\n")
    header_idx, separator_idx, first_data_idx = find_recent_changes_table(snapshot_content)
    if header_idx is None:
        return {}, 0, 0

    dates = {}
    explicit = set()
    n_invalid = 0
    stop = None
    for i in range(first_data_idx, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            stop = i
            break  # 表格结束
        m = re.match(DATE_ROW_PATTERN, line)
        if not m:
            stop = i
            break  # 非日期列行=表格结束（保持既有语义）
        try:
            d = resolve_row_date(m.group(2), m.group(1), today)
        except ValueError:
            n_invalid += 1  # 非法日期（如02-30）有痕跳过，不参与回填/归档判定
            continue
        if d in dates:
            # 同日期双行：显式年优先于推断；同级保留更靠上（更新）行
            if m.group(1) and d not in explicit:
                dates[d] = i
                explicit.add(d)
            continue
        dates[d] = i
        if m.group(1):
            explicit.add(d)
    n_detached = sum(1 for ln in (lines[stop:] if stop is not None else [])
                     if ln.strip().startswith("|") and re.match(DATE_ROW_PATTERN, ln.strip()))
    return dates, n_invalid, n_detached


def check_today_row_exists(snapshot_content, today):
    """检查「最近变更摘要」表格中是否已有当日行（v8.1.4随键带年升级）"""
    dates, _, _ = get_existing_dates(snapshot_content, today)
    d = today.date()
    if d in dates:
        return True, dates[d]
    return False, None


def collect_missing_days(existing_dates, today, window_days):
    """计算窗口内缺失的历史日（不含今日·倒序返回）
    —— 只回看窗口内，避免首次运行把整张表按天补满"""
    missing = []
    for offset in range(1, window_days + 1):
        day = today - timedelta(days=offset)
        if day.date() not in existing_dates:  # v8.1.4·审查F-10：成员测试用完整日期（existing_dates键已带年）
            missing.append(day)
    return missing


def update_snapshot(snapshot_path, new_rows, today, today_row_idx=None, dry_run=False):
    """更新快照的「最近变更摘要」表格
    new_rows: [(datetime, row_str)] —— 待插入的新行（任意顺序，内部按日期升序插入以保证表内降序）
    today_row_idx: 当日行已存在时的行号（整行替换）"""
    if not snapshot_path.exists():
        return False, f"快照文件不存在: {snapshot_path}"

    content = snapshot_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    header_idx, separator_idx, first_data_idx = find_recent_changes_table(content)

    if header_idx is None:
        return False, "快照中未找到「最近变更摘要」表格"

    replace_row = None
    insert_rows = []
    for day, row in new_rows:
        if today_row_idx is not None and day.strftime("%m-%d") == today.strftime("%m-%d"):
            replace_row = row
        else:
            insert_rows.append((day, row))

    if dry_run:
        if replace_row is not None:
            print(f"[DRY-RUN] 将替换第{today_row_idx + 1}行:")
            print(f"  旧: {lines[today_row_idx]}")
            print(f"  新: {replace_row}")
        if insert_rows:
            print(f"[DRY-RUN] 将在第{separator_idx + 2}行起插入 {len(insert_rows)} 行（新→旧）:")
            for day, row in sorted(insert_rows, key=lambda x: x[0], reverse=True):
                print(f"  {row}")
        return True, f"dry-run：替换{1 if replace_row is not None else 0}行 + 插入{len(insert_rows)}行"

    if replace_row is not None:
        lines[today_row_idx] = replace_row
    # 按日期升序插入到表格顶部 → 表内呈现为降序（新→旧），与既有表格同构
    for day, row in sorted(insert_rows, key=lambda x: x[0]):
        lines.insert(separator_idx + 1, row)

    snapshot_path.write_text("\n".join(lines), encoding="utf-8")
    return True, f"已替换{1 if replace_row is not None else 0}行 + 新增{len(insert_rows)}行"


def archive_old_rows(snapshot_path, archive_path, window_days, dry_run=False, today=None):
    """滚动归档（v7.36）：把「最近变更摘要」中超出 window_days 的行迁入历史存档。

    表内为降序（新→旧），故自首行数据向下首个超窗日期起的全部数据行即为归档段。
    跨年纪律（v8.1.2·审查A1硬伤根治）：表内 MM-DD 先按"未来日回退去年"补全为完整日期再比较——
    降序契约（v8.1.4·审查F-5·NP-1收口后为全表校验）：表格"新在上"为硬前提，违例时守卫跳过而非推断。
    ⛔DO NOT 用 MM-DD 字符串序比较，原因是 1 月时 "01-05" < "12-22" 恒真，整表（含当日行）会被
    误判超窗清空并把重复行累积进存档（2027-01-05 合成表 dry-run 复现实锤·与仪表盘 snapshot_status 同口径）。
    写入顺序（先存档、后删表）保证任一步失败都不丢数据——Fail-Safe 而非 Fail-Loud。
    返回 (归档行数, 说明)；归档行数=0 表示无需归档（非错误）。
    """
    if not snapshot_path.exists():
        return 0, f"快照文件不存在: {snapshot_path}"
    content = snapshot_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    header_idx, separator_idx, first_data_idx = find_recent_changes_table(content)
    if header_idx is None:
        return 0, "未找到「最近变更摘要」表格"

    today = today or datetime.now()
    # v8.1.4·审查F-2：cutoff 与行日期统一到"日"粒度——显式年午夜 vs 裸日带时分两种返回值不再产生"边界行早归档一天"的差分缺陷
    cutoff = (today - timedelta(days=window_days)).date()

    # 先全段收集 (行号,日期)，再做整表降序校验——v8.1.4b·R4-NP-1收口：
    # 原实现 prev_d 校验依附于"遇到首个超窗行即 break"的路径，违例行藏在超窗行之下时校验覆盖不到=守卫缝隙
    seq = []  # [(line_no, date)]
    stop = None
    for i in range(first_data_idx, len(lines)):
        s = lines[i].strip()
        if not s.startswith("|"):
            stop = i
            break
        m = re.match(DATE_ROW_PATTERN, s)
        if not m:
            stop = i
            break
        try:
            seq.append((i, resolve_row_date(m.group(2), m.group(1), today)))
        except ValueError:  # 非法日期（如 02-30）不阻断扫描，视作不可归档行继续
            continue
    for k in range(1, len(seq)):
        if seq[k][1] > seq[k - 1][1]:
            return 0, (f"⚠️ 表内日期非降序（第{seq[k][0] - first_data_idx + 1}数据行 {seq[k][1].strftime('%m-%d')} 比上一行新）"
                       "——本轮跳过归档，请人工整理表格（v8.1.4·审查F-5守卫·NP-1收口后为全表校验）")
    if stop is not None and _has_detached_date_rows(lines, stop):
        return 0, ("⚠️ 表格在末行后存在断链日期行（结构被外部破坏）——本轮跳过归档，防止基于残缺表序推断误吞窗内行（v8.1.4b·R4-NP-3收口）")
    arch_start = None
    for i, rd in seq:
        if rd < cutoff:
            arch_start = i
            break

    if arch_start is None:
        return 0, f"无需归档（窗口 {cutoff.strftime('%m-%d')} 内无超窗行）"

    arch_rows = []
    for i in range(arch_start, len(lines)):
        if not lines[i].strip().startswith("|"):
            break
        arch_rows.append(lines[i])
    if not arch_rows:
        return 0, "无需归档（超窗段为空）"

    span = f"{arch_rows[-1][:12].strip(' |')} … {arch_rows[0][:12].strip(' |')}"
    if dry_run:
        return len(arch_rows), f"[DRY-RUN] 将归档 {len(arch_rows)} 行（{span}）→ {archive_path.name}"

    if not archive_path.exists():
        archive_path.write_text(
            "---\ntitle: 情境层 · 快照历史存档\ntype: archive\nstatus: active\n"
            f"date: {today.strftime('%Y-%m-%d')}\n"
            "summary: 从「动态状态快照.md」移出的历史沉积（里程碑/睡眠与能量流水/已闭环条目/变更摘要超窗行）。唤醒不读本文件。\n"
            "tags: [情境层, 存档, 快照历史]\n---\n\n"
            "# 情境层 · 快照历史存档\n\n> **读取纪律**：唤醒（轻量/全量）⛔不读本文件；需要历史细节时才按需 Read 或 grep。\n\n"
            "## 二、变更摘要归档\n\n"
            "| 日期 | 工具 | 文件 | 说明 |\n|------|------|------|------|\n",
            encoding="utf-8")

    arch_text = archive_path.read_text(encoding="utf-8")
    # v8.1.3·审查N7：追加依赖「变更摘要归档」为末段——结构异于预期时跳过并告警，绝不落错段（Fail-Safe）
    sec_head = "## 二、变更摘要归档"
    sec_pos = arch_text.find(sec_head)
    if sec_pos == -1:
        return 0, "⚠️ 存档文件未见「## 二、变更摘要归档」段——本轮跳过归档（防行落错段），请人工处理"
    if re.search(r"^## ", arch_text[sec_pos + len(sec_head):], re.MULTILINE):
        return 0, "⚠️ 存档「变更摘要归档」段之后出现新段落——本轮跳过归档（追加将落错段），请人工处理（v8.1.3·审查N7）"
    if not arch_text.endswith("\n"):
        arch_text += "\n"

    # v8.1.3·审查N8（patch3b改全段重算）：追加后按段内日期行实数重写段标题——新建/旧式标题统一归一，防标题说谎
    arch_text = arch_text + "\n".join(arch_rows) + "\n"
    n_total = len(re.findall(r"^\|\s*(?:\d{4}-)?\d{2}-\d{2}\s*\|", arch_text[sec_pos:], re.MULTILINE))
    arch_text = re.sub(r"^## 二、变更摘要归档[^\n]*$",
                       f"## 二、变更摘要归档（共 {n_total} 行·自动更新至 {today.strftime('%Y-%m-%d')}）",
                       arch_text, count=1, flags=re.MULTILINE)
    archive_path.write_text(arch_text, encoding="utf-8")

    del lines[arch_start: arch_start + len(arch_rows)]
    snapshot_path.write_text("\n".join(lines), encoding="utf-8")
    return len(arch_rows), f"已归档 {len(arch_rows)} 行（{span}）→ {archive_path.name}"


def row_matches_diary(old_row, diary_data):
    """五字段一致性比对（v7.32修复·审查P1-2）：番茄/睡眠/评级/能量/封口
    任何字段解析失败（含旧行缺字段）或不一致 → False → 触发更新补全
    例外（复核N2）：日记fm缺energy_actual时跳过能量比对——防止其他端写入的真实能量被"?"误判不一致后覆盖"""
    sealed_mark = "✓" if diary_data.get("sealed", False) else "⏳未封口"
    expected = {
        "tomato": f"{diary_data.get('tomato', '?')}🍅",
        "sleep": f"睡眠{format_sleep_duration(diary_data['sleep_duration'])}",
        "rating": f"评级{diary_data.get('rating', '?')}",
        "energy": f"能量{diary_data.get('energy_actual', '?')}",
        "sealed": f"封口{sealed_mark}",
    }
    patterns = {
        "tomato": r"(\d+🍅)",
        "sleep": r"(睡眠\d+h\d+m)",
        "rating": r"(评级[^/\s]+)",
        "energy": r"(能量[^/\s]+)",
        "sealed": r"(封口(?:✓|⏳未封口))",
    }
    compare_keys = list(patterns)
    if diary_data.get("energy_actual") is None:
        compare_keys.remove("energy")
    for key in compare_keys:
        m = re.search(patterns[key], old_row)
        if not m or m.group(1) != expected[key]:
            return False
    return True


def main():
    args = parse_args()
    today = datetime.now()
    if args.today:
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d")
        except ValueError:
            # v8.1.4·审查F-6：--today 非法值显式失败（裸 datetime.strptime 抛栈绕过 exit 语义）
            print(f"❌ --today 需为 YYYY-MM-DD 合法日期，收到: {args.today!r}")
            sys.exit(1)
    # v8.1.3·审查N10：窗口≤0 钳为1（与 dashboard --weeks 同钳制口径——一条误命令毁热区违反Fail-Safe）
    if args.backfill_window <= 0 or args.archive_window <= 0:
        print("⚠️ 窗口参数≤0 已钳为 1（backfill/archive 不可非正·v8.1.3审查N10）")
        args.backfill_window = max(1, args.backfill_window)
        args.archive_window = max(1, args.archive_window)

    # 推导路径
    default_snapshot, default_diary = get_default_paths(today)  # v8.1.4·审查F-6：today 贯通注入
    snapshot_path = Path(args.snapshot) if args.snapshot else default_snapshot
    today_diary_path = Path(args.diary) if args.diary else default_diary

    print(f"📔 懒加载快照实时更新（awaken-memory-system v8.3.1）")
    print(f"   快照: {snapshot_path}")
    print(f"   今日日记: {today_diary_path}")
    print(f"   日期: {today.strftime('%Y-%m-%d')} | 回填窗口: {args.backfill_window}天 | 回填: {'关闭' if args.no_backfill else '开启'}")
    print()

    # 1. 快照前置预检（审查P1-1/P3-3：快照不存在显式exit 1，不让read_text抛异常兜底）
    if not snapshot_path.exists():
        print(f"❌ 快照文件不存在: {snapshot_path}")
        print(f"   降级：跳过快照更新，轻量模式将输出快照旧数据+标注滞后")
        sys.exit(1)

    snapshot_content = snapshot_path.read_text(encoding="utf-8")
    header_idx, separator_idx, first_data_idx = find_recent_changes_table(snapshot_content)
    if header_idx is None:
        print(f"❌ 快照中未找到「最近变更摘要」表格")
        print(f"   降级：跳过快照更新，轻量模式将输出快照旧数据+标注滞后")
        sys.exit(1)

    existing_dates, n_invalid, n_detached = get_existing_dates(snapshot_content, today)
    # v8.1.4·审查F-7：最新日期改"表首行"口径（与仪表盘 snapshot_status 同源——表序约定=新在上；max()系第三口径已废）
    # 审查F-4：_md_to_disp 无异常保护的崩溃路径随本块删除一并消失；非法日期行有痕跳过
    _latest = None
    if existing_dates:
        _head_idx = min(existing_dates.values())
        _latest = next(d for d, i in existing_dates.items() if i == _head_idx)
    if n_invalid:
        print(f"⚠️ 表内 {n_invalid} 行日期非法（如02-30）已跳过，不参与回填/归档判定")
    if n_detached:
        print(f"⚠️ 表格终止位后仍发现 {n_detached} 行日期行（结构断链·多为手工编辑所致）——该行不参与去重判断，回填可能与之重复，请整理表格（v8.1.4b·R4-NP-3有痕化）")
    print(f"   表内既有行: {len(existing_dates)} 行（表首最新 {_latest.strftime('%m-%d') if _latest else '无'}）")
    print()

    new_rows = []
    skipped = []

    # 2. 当日行（可未封口——懒加载的设计目的就是盘中用实时数据覆盖过时快照）
    today_diary_data = None
    if not today_diary_path.exists():
        skipped.append((today, "今日日记尚未生成（骨架未创建）"))
    else:
        today_diary_data, error = read_diary_frontmatter(today_diary_path)
        if error:
            skipped.append((today, error))
        elif is_skeleton(today_diary_data):
            skipped.append((today, "今日日记为占位骨架（未封口+tomato=0）——不回填防脏数据"))
            today_diary_data = None
        else:
            print(f"✅ 今日日记frontmatter读取成功:")
            print(f"   评级: {today_diary_data.get('rating')} | 番茄: {today_diary_data.get('tomato')} | "
                  f"睡眠: {format_sleep_duration(today_diary_data['sleep_duration'])} | "
                  f"能量: {today_diary_data.get('energy_actual', 'N/A')} | "
                  f"封口: {'✓已封口' if today_diary_data.get('sealed') else '⏳未封口'}")

    today_exists = today.date() in existing_dates  # v8.1.4·审查F-10：当日行定位用完整日期，混合年表不再命中去年行
    today_row_idx = existing_dates.get(today.date())
    if today_diary_data is not None:
        if today_exists:
            old_row = snapshot_content.split("\n")[today_row_idx]
            if row_matches_diary(old_row, today_diary_data):
                print(f"✅ 当日行已是最新（五字段比对一致）")
            else:
                m_energy = re.search(r"(能量[^/\s]+)", old_row)
                prev_energy = m_energy.group(1)[2:] if m_energy and today_diary_data.get("energy_actual") is None else None
                print(f"📝 当日行已存在但字段不一致或缺字段，将更新补全")
                new_rows.append((today, build_summary_row(today_diary_data, today, prev_energy=prev_energy)))
        else:
            new_rows.append((today, build_summary_row(today_diary_data, today)))

    # 3. 历史缺失日回填（Fail-Closed：只填已封口且非骨架的历史日）
    if args.no_backfill:
        print(f"   历史缺失日回填：已关闭（--no-backfill）")
    else:
        missing_days = collect_missing_days(existing_dates, today, args.backfill_window)
        if missing_days:
            print(f"📋 历史缺失日: {len(missing_days)} 天 —— {', '.join(d.strftime('%m-%d') for d in missing_days)}")
        for day in missing_days:
            dpath = diary_path_for(day)
            if not dpath.exists():
                skipped.append((day, "日记文件不存在"))
                continue
            ddata, derror = read_diary_frontmatter(dpath)
            if derror:
                skipped.append((day, derror))
                continue
            if is_skeleton(ddata):
                skipped.append((day, "占位骨架（未封口+tomato=0）"))
                continue
            if not ddata.get("sealed"):
                skipped.append((day, "未封口（历史日只回填已封口数据·Fail-Closed）"))
                continue
            new_rows.append((day, build_summary_row(ddata, day)))

    # 4. 有痕跳过 ≠ 静默跳过（Skill架构规范§③）
    if skipped:
        print(f"⚠️ 跳过 {len(skipped)} 天（未回填·有痕留证）:")
        for day, reason in skipped:
            print(f"   {day.strftime('%m-%d')}: {reason}")
    print()

    # 5. 更新摘要表格
    if not new_rows:
        print(f"✅ 无需更新（无缺失可回填日 且 当日行无需变更）")
    else:
        success, message = update_snapshot(
            snapshot_path, new_rows, today,
            today_row_idx=today_row_idx if today_exists else None,
            dry_run=args.dry_run,
        )
        if not success:
            print(f"❌ {message}")
            sys.exit(1)

        print(f"✅ {message}")
        if args.dry_run:
            print(f"   (dry-run模式，未实际写入)")

    # 6. 滚动归档（v7.36）：超窗行迁入历史存档——补齐回填的对称性，防表格单调增长
    n_arch = 0
    arch_guard = False
    if args.no_archive:
        print(f"🗄 滚动归档: 已关闭（--no-archive）")
    else:
        n_arch, amsg = archive_old_rows(snapshot_path, ARCHIVE_PATH, args.archive_window, dry_run=args.dry_run, today=today)
        print(f"🗄 滚动归档: {amsg}")
        arch_guard = amsg.startswith("⚠️")

    # v8.1.3·审查N2：本轮有归档写盘即算"已更新"（exit 2 不再混入"无需更新"却已写盘的语义矛盾）
    # v8.1.4·审查F-3：守卫类告警（跳过归档待人工）落 exit 1 而非 exit 2——否则 patrol 记 uptodate、
    # 仪表盘 snap_gap 不计数，"请人工处理"被双层静默吞掉=假绿灯（A1症状经守卫路径复活）
    if arch_guard and not args.dry_run:
        sys.exit(1)
    sys.exit(0 if (new_rows or n_arch > 0) else 2)


if __name__ == "__main__":
    main()
