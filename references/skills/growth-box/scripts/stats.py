#!/usr/bin/env python3
"""growth-box/stats.py — 从错误源文件重算 INDEX.md 模式目录表

用法：
  python3 stats.py --learnings-dir ~/[记忆共享中心]/成长箱/learnings/ --index ~/[记忆共享中心]/成长箱/learnings/INDEX.md

功能：
  1. 扫描 learnings/ 下所有 *_errors.md / LEARNINGS.md / ERRORS.md / skill_errors.md
  2. 按独立记录统计 PAT-XXX 引用次数（同记录多次提及计1次）+ 最新发生日期
  3. 保留 INDEX.md 中现有的「状态」「关联铁律」元数据
  4. 输出更新后的模式目录表（Markdown 格式）

设计原则（指令§6.1 单一来源）：
  INDEX.md 的模式目录表是从错误源文件派生的数据。手工维护计数=双本账迟早漂移。
  本脚本只读源文件、实时计算派生数据，不另建独立写入源。
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
import re
import os
from pathlib import Path
from datetime import date


# PAT 编号正则（PAT-001, PAT-002, ...）
PAT_PTN = re.compile(r'PAT-(\d{3,})')

# ⚠️ 配置化改造须知（2026-09-03 匿名提报实证复现）：若改编号体系（如 PAT- → 端前缀+日期+序号），
# 必须同步改 3 处，否则静默出错：
#   ① 本 PAT_PTN（扫描计数）② 下方 read_index_meta 的 row_ptn（解析 INDEX 元数据，6 组硬编码 PAT-\d{3,}）
#   ③ generate_table 的表列数必须恒为 6。
# 任一漏改 → 匹配失败使 meta 为空 → 下次 --write 把「状态/关联铁律」两列静默清空；或列数漂移致列错位。
# 当前实例为作者原版 PAT 双层体系，故保持硬编码；下游实例勿直接抄本正则（详见 SKILL-stats 提报）。

# 记录ID锚点：YYYYMMDD-NNN（如 WBE-20260411-001 / LRN-20260427-001）
# 第一性原理：只有带唯一ID的「错误/学习记录」才是一个发生单元，才计入累计次数。
RECORD_ID_PTN = re.compile(r'\d{8}-\d{1,3}')


def _is_record_block(block: str) -> bool:
    """块首行是否为一条真正的记录标题（含记录ID），而非章节分隔（如 '## 分类标准'）。"""
    heading = block.split('\n', 1)[0]
    return bool(RECORD_ID_PTN.search(heading))


def scan_error_files(learnings_dir: Path) -> dict:
    """扫描错误文件，返回 {pat_id: {count, latest_date}}

    第一性原理（根治 P2-5 残留虚增）：累计次数 = 该模式被多少条「独立记录」引用。
    - 记录 = 一个带唯一ID的 `## ` 标题块（发生单元）；一条记录内多处提及同一PAT = 同一次发生 → 计1。
    - 旧 P2-5 按 `### ` 子节分块，但 `### ` 是记录内子节（发生了什么/根因/关联PAT…），
      同一记录跨多子节自引会被重复计 → 虚增。现改为按 `## ` 记录边界分块，从根消除。
    - 非记录类 `## ` 标题（章节分隔，如 '## 分类标准'）不含记录ID → 不计。
    - 兼容：文件无 `## ` 记录标题（旧格式）→ 全文作单条记录，防丢计数。
    """
    error_files = []
    # 审查P1-1修复：'_errors.md' 已匹配 skill_errors.md，显式第四项曾致该文件全量计双（INDEX虚增实证28→29）——glob集合去重
    for pattern in sorted(set(['*_errors.md', 'LEARNINGS.md', 'ERRORS.md'])):
        error_files.extend(learnings_dir.glob(pattern))

    pats = {}
    for f in error_files:
        text = f.read_text(encoding='utf-8')
        # 按 ## / ### 记录边界分块（第一性原理：记录=发生单元）
        # 2026-09-20 修复：原为 `\n(?=## )`——只切二级标题，而 **LEARNINGS.md 的记录标题是
        #   `### LRN-...`（三级）**，`## `（两井号+空格）匹配不到它 → 全文被当**单块** →
        #   所有 PAT 各计 1、最新发生日取到全文第一个 `**Logged**`（实测 PAT-049 被记成 09-18）。
        #   判据改为 `#{2,4}`：块的"是不是记录"仍由 `_is_record_block`（首行含记录ID）定夺——
        #   故 `##` 文件里的 `### 子节`（无记录ID）照旧被排除，不引入虚增。
        raw_blocks = re.split(r'\n(?=#{2,4} )', text)
        # 2026-09-20 二次修复（PAT 引用漏计根治）：`#{2,4}` 会把记录内 `### 子节`
        #（Summary/Details/How to apply/关联 PAT…）也切成独立块，而 _is_record_block
        #（首行含记录ID）把它们全排除 → 记录内子节的 PAT 引用全部丢失（实证：A2.5 指引
        # "PAT 写进 Details/How to apply"在旧逻辑下永不计数，只有落在标题+元数据块才生效）。
        # 修法：非记录块向上并入最近记录块 —— 记录块 = 标题 + 全部子节，计数口径不变
        # （仍=「独立记录数」·块内 set 去重），虚增面为零：子节只归其所属记录，不跨记录。
        merged = []
        for b in raw_blocks:
            if _is_record_block(b) or not merged:
                merged.append(b)
            else:
                merged[-1] = merged[-1] + b
        record_blocks = [b for b in merged if _is_record_block(b)]
        if not record_blocks:
            # 兼容旧格式：无 ## 记录标题 → 全文单块
            record_blocks = [text]
        for block in record_blocks:
            block_pats = set(PAT_PTN.findall(block))  # 记录内去重：一记录一计
            if not block_pats:
                continue
            block_dates = []
            # 优先取 **Logged** 字段的日期——记录正文里的其他日期（如晋升标注
            # `[TTL: 90d | 过期: YYYY-MM-DD]`）是元数据不是发生日，全文取 max 会让
            # 未来的过期日盖过真实发生日（2026-08-29 实证：PAT-044 最新发生被记成 2026-11-27）
            lm = re.search(r'\*\*Logged\*\*\s*[:：]\s*(\d{4}-\d{2}-\d{2})', block)
            if lm:
                try:
                    block_dates.append(date.fromisoformat(lm.group(1)))
                except ValueError:
                    pass
            if not block_dates:  # 无 Logged 字段才回退全文扫描（兼容旧格式）
                for d in re.findall(r'(\d{4}-\d{2}-\d{2})', block):
                    try:
                        block_dates.append(date.fromisoformat(d))
                    except ValueError:
                        pass
            block_latest = max(block_dates) if block_dates else None
            for m in block_pats:
                pat_id = f'PAT-{m}'
                if pat_id not in pats:
                    pats[pat_id] = {'count': 0, 'latest': None}
                pats[pat_id]['count'] += 1
                if block_latest and (pats[pat_id]['latest'] is None or block_latest > pats[pat_id]['latest']):
                    pats[pat_id]['latest'] = block_latest
    return pats


def read_index_meta(index_path: Path) -> dict:
    """读取 INDEX.md 现有模式目录表，提取状态和关联铁律"""
    text = index_path.read_text(encoding='utf-8')
    meta = {}
    # 匹配表行：| PAT-XXX | 名称 | 次数 | 日期 | 状态 | 铁律 |
    row_ptn = re.compile(
        r'^\|\s*(PAT-\d{3,})\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|'
        r'\s*(.+?)\s*\|',
        re.MULTILINE
    )
    for m in row_ptn.finditer(text):
        pat_id = m.group(1)
        name = m.group(2).strip()
        status = m.group(5).strip()
        rule = m.group(6).strip()
        meta[pat_id] = {'name': name, 'status': status, 'rule': rule}
    return meta


def generate_table(pats: dict, meta: dict) -> str:
    """生成模式目录表（Markdown）"""
    header = '| 编号 | 模式名称 | 累计次数 | 最新发生 | 状态 | 关联铁律 |\n|------|---------|---------|---------|------|---------|'
    rows = []

    # 按 PAT 编号排序
    for pat_id in sorted(pats.keys()):
        info = pats[pat_id]
        m = meta.get(pat_id, {})
        name = m.get('name', '（未知·请手动填写）')
        cn = info['count']
        status = m.get('status', 'pending')
        # status-count-sync v1: 状态列 pending(N/3) 数字部分按机械计数刷新（裁决字样保留）
        # 2026-10-01 反哺 JOB-003-20261001-006：派生计数不独立存储，防计数-状态双本账漂移
        status = re.sub(r'pending\(\d+/3\)', f'pending({cn}/3)', status)
        rule = m.get('rule', '-')
        latest = info['latest'].isoformat() if info['latest'] else '未知'
        count = f"{info['count']}+"
        rows.append(f'| {pat_id} | {name} | {count} | {latest} | {status} | {rule} |')

    return header + '\n' + '\n'.join(rows) if rows else '(无 PAT 条目)'


def main():
    parser = argparse.ArgumentParser(description='从错误源文件重算 INDEX.md 模式目录表')
    parser.add_argument('--learnings-dir', required=True, help='成长箱 learnings/ 目录')
    parser.add_argument('--index', required=True, help='INDEX.md 文件路径（用于读取元数据状态/铁律）')
    parser.add_argument('--write', action='store_true', help='自动写回 INDEX.md（替换模式目录表区块）')
    args = parser.parse_args()

    learnings = Path(args.learnings_dir).expanduser().resolve()
    index = Path(args.index).expanduser().resolve()

    if not learnings.is_dir():
        print(f"❌ learnings 目录不存在: {learnings}", file=__import__('sys').stderr)
        __import__('sys').exit(1)

    pats = scan_error_files(learnings)
    meta = read_index_meta(index) if index.exists() else {}

    # 断裂检测（根治提报②静默失效）：扫描 0 条但 INDEX 已有目录 = 编号体系脱节 → 硬失败阻断写回
    if len(pats) == 0:
        if meta:
            _sys.stderr.write(
                f"⚠️ 扫描到 0 个条目 —— 但 INDEX.md 已存在 {len(meta)} 个模式目录行。\n"
                f"   疑似编号体系与当前正则（PAT-\\d{{3,}}）脱节，已阻断写回以防覆盖真数据。\n"
            )
            _sys.exit(2)
        else:
            _sys.stderr.write("(无 PAT 条目) —— 冷启动：learnings/ 与 INDEX.md 均为空，属正常初始状态。\n")

    # 合并：保留 INDEX 中的 PAT（即使 error 文件中暂时没扫到）
    for pat_id in meta:
        if pat_id not in pats:
            pats[pat_id] = {'count': 0, 'latest': None}

    table = generate_table(pats, meta)

    if args.write and index.exists():
        # 自动写回 INDEX.md：找到「## 模式目录」区块，替换到下一个「## 」标题
        text = index.read_text(encoding='utf-8')
        # 匹配从「## 模式目录」到下一个「## 」标题（不含）
        pattern = re.compile(r'(## 模式目录\n)(.*?)(?=\n## )', re.DOTALL)
        if pattern.search(text):
            # 保留标题行，替换表格内容（标题后空行+表格）
            new_text = pattern.sub(lambda m: m.group(1) + '\n' + table + '\n', text)
            index.write_text(new_text, encoding='utf-8')
            print(f"✅ INDEX.md 已更新（模式目录表写回）: {index}")
            print(f"   共 {len(pats)} 个 PAT 条目")
        else:
            print(f"⚠️ 未找到「## 模式目录」区块，未写回。输出表格如下：", file=__import__('sys').stderr)
            print(table)
    else:
        print(table)


if __name__ == '__main__':
    main()
