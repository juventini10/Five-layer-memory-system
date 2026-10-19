#!/usr/bin/env python3
"""growth-box/stats.py — 从错误源文件重算 INDEX.md 模式目录表

用法：
  python3 stats.py --learnings-dir [记忆共享中心]/成长箱/learnings/ --index [记忆共享中心]/成长箱/learnings/INDEX.md

功能：
  1. 扫描 learnings/ 下所有 *_errors.md / LEARNINGS.md / ERRORS.md / skill_errors.md
  2. 按独立记录统计 PAT-XXX 引用次数（同记录多次提及计1次）+ 最新发生日期
  3. 保留 INDEX.md 中现有的「状态」「关联铁律」元数据
  4. 输出更新后的模式目录表（Markdown 格式）
  5. --board <规范反哺日志路径>：进度看板计数的唯一口径源（v1.2.0·2026-10-12·治 AI 手抄漂数）

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

__version__ = "1.2.0"  # v1.2.0=--board 看板计数口径源（2026-10-12·成长箱设计哲学 v2.8 配套）


# PAT 编号正则（PAT-001, PAT-002, ...）
PAT_PTN = re.compile(r'PAT-(\d{3,})')

# ⚠️ 配置化改造须知（2026-09-03 匿名提报实证复现）：若改编号体系（如 PAT- → 端前缀+日期+序号），
# 必须同步改 3 处，否则静默出错：
#   ① 本 PAT_PTN（扫描计数）② 下方 read_index_meta 的 row_ptn（解析 INDEX 元数据，6 组硬编码 PAT-\d{3,}）
#   ③ generate_table 的表列数必须恒为 6。
# 任一漏改 → 匹配失败使 meta 为空 → 下次 --write 把「状态/关联铁律」两列静默清空；或列数漂移致列错位。
# 当前实例为作者原版 PAT 双层体系，故保持硬编码；下游实例勿直接抄本正则（详见 SKILL-stats 提报）。

# 记录ID锚点：YYYYMMDD-NNN（如 WBE-20260411-001 / 内部记录）
# 第一性原理：只有带唯一ID的「错误/学习记录」才是一个发生单元，才计入累计次数。
RECORD_ID_PTN = re.compile(r'\d{8}-\d{1,3}')


def _is_record_block(block: str) -> bool:
    """块首行是否为一条真正的记录标题（含记录ID），而非章节分隔（如 '## 分类标准'）。"""
    heading = block.split('\n', 1)[0]
    return bool(RECORD_ID_PTN.search(heading))


# 口径 v2 副产物：Logged≥2026-09-20 却缺「PAT 归属」行的记录清单（模块级·供 main 显形）
_UNANNOUNCED: list = []  # 归属行外另提编号的记录清单（供 main 非阻断提示）


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
            # ── 口径 v3（2026-10-10 定稿·零误伤）──
            # 病灶：全文扫描不区分「归属」与「类比提及」，一句类比即推高计数，可假推 3/3 阈值
            #   （2026-10-10 实测：某记录两处类比致模式 041 由 1+ 变 2+、084 由 4+ 变 5+）。
            # ⛔曾试过「只认归属行」——dry-run 证伪：09-20 后 84 条记录无归属行，
            #   改口径会使 PAT-001 62+→48+、31 个模式骤降＝把污染换成漏计（真坑消失更危险）。
            # 定稿：基线不动（零误伤）+ 显式类比豁免语法「（类比）PAT-NNN」+ 非阻断提示收敛。
            block_pats = set(PAT_PTN.findall(block.replace("（类比）PAT-", "（类比）pat-")))
            _own = set()
            for _l in block.split("\n"):
                if "PAT 归属" in _l or "PAT归属" in _l:
                    _own |= set(PAT_PTN.findall(_l))
            _extra = block_pats - _own
            if _own and _extra:  # 归属行之外还提到别的编号：可能是类比，提示加标记（不阻断·不丢账）
                _UNANNOUNCED.append("%s → 归属 %s／另提及 %s" % (
                    block.split("\n")[0][:46], ",".join(sorted(_own)), ",".join(sorted(_extra))))
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


# ── 写回判据唯一真源（B2 根治·2026-10-10 刚叔提请单 F7）──
# 原 `(?=\n## )` 要求"这段后面还得再有一个 ## 段"——单段头文件 / 该段恰为末段
#   两种形态 search=False，走 else 只打印不写回且 rc=0，派生表静默停滞两天无人知。
# `##[^#]` 保住"遇 ### 子标题不截断"的原有语义（### 后紧跟 # → [^#] 不成立 → 不在三级标题处收口），
#   `\Z` 补末段/单段头形态。
# ⚠️ main() 与 --self-test 必须共用本函数·本正则——杜绝"测试一套、生产一套"漂移（PAT-058 检查器不完备同族）。
MODE_DIR_RE = re.compile(r'(^## 模式目录[ \t]*\n)(.*?)(?=\n##[^#]|\Z)',
                         re.DOTALL | re.MULTILINE)


def rewrite_index(text: str, table: str):
    """把 table 写回 text 的「## 模式目录」区块。
    返回 (new_text, wrote:bool)。wrote=False 表示未找到该区块——调用方必须据此
    显式失败（⛔不得静默 rc=0，否则派生表停更无人知）。
    三级子标题 ### 属段内内容（随区块整体替换），⛔不作为区块终结符。"""
    if not MODE_DIR_RE.search(text):
        return text, False
    new_text = MODE_DIR_RE.sub(lambda m: m.group(1) + '\n' + table + '\n', text)
    return new_text, True


def _self_test() -> int:
    """--self-test：写回四形态 + 负例的沙盒自检（tempfile，⛔不碰真实 INDEX.md）。
    经 subprocess 走真实 main() 路径，同时验退出码 rc 与落盘内容。
    退出码 0=全过，非 0=有失败。"""
    import subprocess
    import tempfile
    script = str(Path(__file__).resolve())
    py = _sys.executable
    TABLE_MARK = '| 累计次数 |'  # generate_table 表头特征串（写回成功的可判据）
    results = []

    def _mk_learnings(td):
        ld = os.path.join(td, 'learnings')
        os.makedirs(ld, exist_ok=True)
        with open(os.path.join(ld, 'selftest_errors.md'), 'w', encoding='utf-8') as f:
            f.write('## WBE-20260101-001：自检记录\n\n- **Logged**: 2026-01-01\n- PAT 归属：PAT-001\n')
        return ld

    def _run(idx_text):
        with tempfile.TemporaryDirectory() as td:
            ld = _mk_learnings(td)
            idx = os.path.join(td, 'INDEX.md')
            with open(idx, 'w', encoding='utf-8') as f:
                f.write(idx_text)
            p = subprocess.run([py, script, '--learnings-dir', ld, '--index', idx, '--write'],
                               capture_output=True, text=True)
            with open(idx, encoding='utf-8') as f:
                after = f.read()
            return p.returncode, p.stderr, after

    # 形态1·单段头（整个文件只有模式目录段）
    rc, _err, out = _run('## 模式目录\n\n| 编号 | 旧 |\n|---|---|\n')
    results.append(('单段头', rc == 0 and TABLE_MARK in out and out.startswith('## 模式目录'), rc))

    # 形态2·多段头（后继各 ## 段必须原样保留）
    rc, _err, out = _run('## 模式目录\n\n| 旧 |表 |\n\n## 第二节\nbody2\n\n## 第三节\nbody3\n')
    results.append(('多段头', rc == 0 and TABLE_MARK in out
                    and '## 第二节\nbody2' in out and '## 第三节\nbody3' in out, rc))

    # 形态3·末段无后继（模式目录恰为最后一 ## 段）
    rc, _err, out = _run('## 前言\nintro\n\n## 模式目录\n\n| 旧 |\n')
    results.append(('末段无后继', rc == 0 and TABLE_MARK in out
                    and '## 前言\nintro' in out and '| 旧 |' not in out, rc))

    # 形态4·段内含 ### 子标题：不得在 ### 处截断（### 属段内被整体替换，后继 ## 段保序不丢）
    rc, _err, out = _run('## 模式目录\n\n| 旧 |表 |\n\n### 目录附注\n这是段内三级标题\n\n## 模式详情\n详情正文保留\n')
    ok4 = (rc == 0 and TABLE_MARK in out
           and '## 模式详情\n详情正文保留' in out
           and '### 目录附注' not in out)  # 若在 ### 处截断，孤儿 ### 会残留在新表之后
    results.append(('段内###不截断', ok4, rc))

    # 负例·完全没有「## 模式目录」段：必须未写回 + 可被调用方识别（rc!=0，⛔非静默 rc=0）
    rc, err, out = _run('## 说明\n只有说明段，没有模式目录。\n')
    results.append(('负例·无模式目录段', rc != 0 and '未找到' in err and TABLE_MARK not in out, rc))

    _sys.stdout.write('== stats.py --self-test 写回四形态+负例 ==\n')
    fail = 0
    for name, ok, rcode in results:
        _sys.stdout.write(('  PASS \u2705 ' if ok else '  FAIL \u274c ') + name + '  (rc=%d)\n' % rcode)
        if not ok:
            fail += 1
    _sys.stdout.write('断言命中数：%d/%d\n' % (len(results) - fail, len(results)))
    if fail:
        _sys.stderr.write('\u26d4 自检失败 %d 项\n' % fail)
        return 1
    _sys.stdout.write('\u2705 全部通过（四形态写回成功 + 负例可识别退出）\n')
    return 0


def board_census(feedback_log: Path) -> int:
    """v1.2.0：成长箱设计哲学 03-进度看板 两行（反哺整合/验证执行）的唯一计数源。
    口径全部显式打印；三个登记面（### 块／含📅日期条目块／总追踪表行）**不同面⛔相加**
    ——依据 QCN-20261011-032（混面数字比没数更坏）＋主线 7（派生数据不由 AI 手抄）。"""
    import collections
    text = feedback_log.read_text(encoding="utf-8")
    blocks = [b for b in re.split(r"(?=^### )", text, flags=re.M) if b.startswith("### ")]
    dated = [b for b in blocks if re.search(r"^- 📅 日期[：:]\s*\d{4}-\d{2}-\d{2}", b, re.M)]

    def bucket(line, table):
        for key, pat in table:
            if pat in line:
                return key
        return "（缺/异形）"

    def field(block, name):
        m = re.search(r"^- " + name + r"[：:]\s*(.+)$", block, re.M)
        return m.group(1).strip() if m else ""

    ST = (("待整合", "🔴"), ("独立落地", "📌"), ("否决", "否决"), ("已整合", "✅"), ("已整合", "已整合"))
    VR = (("待验证", "⏳"), ("需修正", "⚠️"), ("不适用", "❌"), ("适用", "✅"))
    st = collections.Counter(bucket(field(b, "🚦 状态"), ST) for b in dated)
    vr = collections.Counter(bucket(field(b, "🔍 验证状态"), VR) for b in dated)
    rows = len(re.findall(r"^\| \d\d-\d\d \|", text, re.M))
    shield = len(re.findall(r"^- 🛡 复发检测条件[：:]\s*\S", text, re.M))
    print("BOARD 口径声明（stats.py --board 产出·⛔ 看板手抄/⛔ 三面相加）：文件 %s" % feedback_log.name)
    print("  面1 `### ` 块总数 = %d（含批次小标题·schema_check 计数同此口径）" % len(blocks))
    print("  面2 含 `- 📅 日期：` 的真条目块 = %d（本命令的状态分布即按此面）" % len(dated))
    print("  面3 总追踪表 `| MM-DD |` 行 = %d（另一面·不与面2 相加）" % rows)
    print("  🚦 状态分布（面2）: " + "·".join("%s %d" % (k, v) for k, v in sorted(st.items(), key=lambda x: -x[1])))
    print("  🔍 验证状态分布（面2）: " + "·".join("%s %d" % (k, v) for k, v in sorted(vr.items(), key=lambda x: -x[1])))
    print("  🛡 复发检测条件在册 = %d 条（growth_box_check 可扫面）" % shield)
    return 0


def main():
    parser = argparse.ArgumentParser(description='从错误源文件重算 INDEX.md 模式目录表')
    parser.add_argument('--learnings-dir', required=False, help='成长箱 learnings/ 目录')
    parser.add_argument('--index', required=False, help='INDEX.md 文件路径（用于读取元数据状态/铁律）')
    parser.add_argument('--write', action='store_true', help='自动写回 INDEX.md（替换模式目录表区块）')
    parser.add_argument('--self-test', action='store_true', help='跑写回四形态+负例沙盒自检（tempfile，不碰真实 INDEX）')
    parser.add_argument('--board', metavar='FEEDBACK_LOG', help='成长箱设计哲学进度看板计数（唯一口径源·v1.2.0）')
    parser.add_argument('--next-id', metavar='PREFIX', help='输出该前缀当日下一个可用编号（扫描 learnings 定义标题全局 read-max·2026-10-11 撞号事故根治·发号唯一入口）')
    args = parser.parse_args()
    if args.board:
        _bp = Path(args.board).expanduser()
        if not _bp.exists():
            print('❌ 反哺日志不存在:', args.board)
            return 1
        return board_census(_bp)

    if getattr(args, 'next_id', None):
        import datetime as _dt, re as _re
        today = _dt.date.today().strftime('%Y%m%d')
        # 2026-10-11 发号域第二载体并入（QCN-012 补记第7案根治·你批「愿景最优」）：
        # 病=反哺条目与 learnings 同 QCN- 号段但住 experience/规范反哺日志.md，且标题
        #   `### QCN-x-y·` 无方括号——原尺（glob learnings/*.md + 强制\[）两头都看不见它，
        #   「用了正门仍撞号」。修=方括号可选 + 反哺日志存在即自动入扫（零配置·跨端同构目录）。
        ptn = _re.compile(r'^#{2,3} \[?' + _re.escape(args.next_id) + '-' + today + r'-(\d{1,3})\]?', _re.M)
        mx = 0
        _ld = Path(args.learnings_dir) if args.learnings_dir else (Path("[记忆共享中心]") / '成长箱' / 'learnings')
        _scan = sorted(_ld.glob('*.md'))
        _fb = _ld.parent / 'experience' / '规范反哺日志.md'
        if _fb.is_file():
            _scan.append(_fb)
        for f in _scan:
            if f.name.endswith('.bak'):
                continue
            for mm in ptn.finditer(f.read_text(encoding='utf-8', errors='ignore')):
                mx = max(mx, int(mm.group(1)))
        print('%s-%s-%03d' % (args.next_id, today, mx + 1))
        return

    if args.self_test:
        _sys.exit(_self_test())

    if not args.learnings_dir or not args.index:
        parser.error('--learnings-dir 与 --index 为必填（除 --self-test 外）')

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
        text = index.read_text(encoding='utf-8')
        # 写回走唯一真源 rewrite_index（与 --self-test 同一函数·防双套正则漂移）
        new_text, wrote = rewrite_index(text, table)
        if wrote:
            # 保留标题行，替换表格内容（标题后空行+表格）
            index.write_text(new_text, encoding='utf-8')
            print(f"✅ INDEX.md 已更新（模式目录表写回）: {index}")
            print(f"   共 {len(pats)} 个 PAT 条目")
        else:
            # 静默降级根治：未找到区块时打印表格到 stdout 供人读，
            # 并以专属退出码 3 显式告知调用方"未写回"（⛔不再 rc=0 骗过对账）
            print(f"⚠️ 未找到「## 模式目录」区块，未写回。输出表格如下：", file=__import__('sys').stderr)
            print(table)
            _sys.exit(3)
    else:
        print(table)

    # 口径 v2 显形：缺归属行的新条目=聚合层看不见，⛔不静默吞（愿景①可观测）
    if _UNANNOUNCED:
        print("\nℹ️ [口径v3] %d 条记录在「PAT 归属」行之外还提到其他编号（若属类比，改写为「（类比）PAT-NNN」即不计数；"
              "当前仍按全文口径计入，⛔不丢账）：" % len(_UNANNOUNCED), file=__import__('sys').stderr)
        for _m in _UNANNOUNCED[:12]:
            print("   · " + _m, file=__import__('sys').stderr)


if __name__ == '__main__':
    main()
