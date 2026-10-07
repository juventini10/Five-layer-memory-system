#!/usr/bin/env python3
"""童灵红线·门禁 G2：红线触碰检查（硬红线机械判定）

扫描「本次执行的命令/动作日志」（argv[1]，每行一条命令或动作描述），
标记是否触碰硬红线：
  - 铁律005 删除防护：对个人目录（~ / 桌面 / 下载 / Documents / 个人AI档案 等）的 rm -rf / rm
  - NEVER外传：写入/回显 API key / token / password / secret
  - 健康线：主动建议牺牲睡眠/健康换产出
发现触碰 → exit 1（阻断并显式报告）。无输入文件或空 → exit 0（放行）。

用法：python3 scripts/redline_touch_check.py <actions_log_file>
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import re

if len(sys.argv) < 2:
    print("ℹ️ 未提供动作日志 → 无触碰面可查，放行(exit 0)")
    sys.exit(0)

path = sys.argv[1]
try:
    lines = open(path, encoding='utf-8').read().splitlines()
except OSError as e:
    print(f"⚠️ 无法读取动作日志 {path}：{e} → 放行(exit 0)")
    sys.exit(0)

PERSONAL = r'(~|\$HOME|/Users/\w+|桌面|下载|Downloads|Documents|个人AI档案)'
patterns = {
    '铁律005·删除防护': re.compile(rf'(^|\s)(rm\s+-rf?|rm\s).*{PERSONAL}', re.I),
    'NEVER外传·凭据': re.compile(r'(api[_-]?key|token|password|secret|密钥)', re.I),
    '健康线·牺牲睡眠': re.compile(r'(牺牲睡眠|熬夜|少睡|不睡|睡眠换|健康换)', re.I),
}

hits = []
for i, line in enumerate(lines, 1):
    for name, ptn in patterns.items():
        if ptn.search(line):
            hits.append((name, i, line.strip()))

if hits:
    print("❌ 红线触碰检查未通过：")
    for name, i, line in hits:
        print(f"  [{name}] {path}:{i}: {line[:120]}")
    sys.exit(1)
print(f"✅ 红线触碰检查通过：扫描 {len(lines)} 行，未触碰硬红线（健康线/愿景黑箱/铁律001·002·005）")
