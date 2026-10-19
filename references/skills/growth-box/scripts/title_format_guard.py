#!/usr/bin/env python3
"""growth-box Poka-Yoke 守卫：记录标题格式校验（永久版·原 /tmp/check_title_format.py 提升）

Version 1.1 (2026-09-01) — DEFAULT 路径去硬编码（~ → Path.home()，开源安装环境
                          可用）；新增「0文件=路径错误非通过」断言（原 0 文件会误打印守卫通过）。
                          来源：Loop评估 2026-09-01 批次2 P2-10。

规则同 stats.py 扫描范围（*_errors.md / LEARNINGS.md / ERRORS.md——skill_errors.md 已被 *_errors.md 覆盖·审查P1-1去重）。
每个 `## [` 真实记录标题必须含记录ID YYYYMMDD-NNN，否则 stats.py 的 _is_record_block
会静默丢弃该块 → INDEX 漏计/显示「未知」。模板骨架（含 YYYYMMDD 占位）跳过。
发现真实条目缺格式 → exit 1（大声报错，不静默）。
扫描 0 个文件 ≠ 通过——路径错误（learnings 目录不存在/glob 全空）同样 exit 1（v1.1）。

用法：python3 scripts/title_format_guard.py [learnings_dir]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import re
from pathlib import Path

DEFAULT = (Path('[记忆共享中心]') / "成长箱" / "learnings").expanduser()
LEARNINGS = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT
RECORD_ID_PTN = re.compile(r'\d{8}-\d{1,3}')
PATTERNS = sorted(set(['*_errors.md', 'LEARNINGS.md', 'ERRORS.md']))  # 审查P1-1：去重——skill_errors.md 被 *_errors.md 覆盖，双列曾致计双

violations = []
files = []
defined_ids = {}  # v1.3 全局唯一性：定义层同一编号跨文件>1处=撞号（2026-10-11 双006事故反哺）
for pat in PATTERNS:
    files.extend(LEARNINGS.glob(pat))

for f in files:
    if f.name.endswith('.bak'):
        continue
    for i, line in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
        if not line.startswith('## ['):
            continue
        if 'YYYYMMDD' in line or 'YYYY' in line:
            continue  # 模板骨架占位，非真实条目
        if not RECORD_ID_PTN.search(line):
            violations.append(f"{f.name}:{i}: {line.strip()}")
        m = re.match(r'## \[([A-Z]{2,4}-\d{8}-\d{1,3})\]', line)
        if m:
            defined_ids.setdefault(m.group(1), []).append(f"{f.name}:{i}")

import datetime as _dt
_today = _dt.date.today().strftime('%Y%m%d')
dup = {k: v for k, v in defined_ids.items() if len(v) > 1}
# STOCK 口径（承抗体巡检 v1.7 先例·2026-10-11 首轮实跑即翻出2笔历史案实证必要）：
#   当日撞号=增量必红阻断；历史存量=显形不阻断（⛔旧账拦新工，但逐轮显形直到归位）
_today_dup = {k: v for k, v in dup.items() if _today in k}
_hist_dup = {k: v for k, v in dup.items() if _today not in k}
if _today_dup:
    print("\u274c 定义层编号撞车（当日增量·同 ID 多重定义·引用链污染·必须归位后才可过闸）：")
    for k, v in sorted(_today_dup.items()):
        print("  " + k + " @ " + " | ".join(v))
    sys.exit(1)
if _hist_dup:
    print("\u26a0\ufe0f 历史存量撞号（非本轮引入·显形待归位·不阻断增量闸门）：")
    for k, v in sorted(_hist_dup.items()):
        print("  [存量] " + k + " @ " + " | ".join(v))

if not LEARNINGS.is_dir():
    print(f"❌ learnings 目录不存在: {LEARNINGS}（路径错误非通过）")
    sys.exit(1)

if violations:
    print("❌ 发现真实记录标题缺日期-ID（将被 stats.py 静默漏计）：")
    for v in violations:
        print("  " + v)
    sys.exit(1)
if not files:
    print(f"❌ 扫描到 0 个文件（learnings={LEARNINGS}）——路径错误非通过，检查目录与 glob 模式：{PATTERNS}")
    sys.exit(1)
print(f"✅ 守卫通过：扫描 {len(files)} 文件，所有真实记录标题均含日期-ID，无静默漏计风险")
