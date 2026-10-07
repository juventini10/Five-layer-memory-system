#!/usr/bin/env bash
# TRUTH_OF: 脚本中心/脚本体系验收.sh   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# 脚本体系验收入口：先同步 → 再验收（⛔ 严禁并发·否则出写/读竞态假红）
#
# 🔴 2026-10-04 病根复盘：一天内 6 次「单独跑守卫 rc=0·收口闸却红」——
#   全部是**并发写/读竞态**（同步器正在改脚本中心·收口闸同时在读）。
# ⇒ 本脚本把「同步 → 验收」绑成**单一串行入口**·消除竞态。
set -euo pipefail

# B修源·声明驱动口径v2(2026-10-05·条文47·解链取实体旁·LRN-016别名面已前置核)：根唯一来源=声明；rc 判定非变量判定。
_SELF="${BASH_SOURCE[0]:-$0}"
while [ -L "$_SELF" ]; do _L="$(readlink "$_SELF")"; case "$_L" in /*) _SELF="$_L";; *) _SELF="$(cd "$(dirname "$_SELF")" && cd "$(dirname "$_L")" && pwd)/$(basename "$_L")";; esac; done
_ROOT="$(python3 "$(dirname "$_SELF")/runtime_paths.py" get archive_root 2>/dev/null)" \
  || { echo "❌ 脚本体系验收: 读不到 runtime_paths 声明·作者机先跑 脚本中心/runtime_paths.py build / 端用户机跑安装器(条文47)" >&2; exit 1; }
MC="${BULUOTUO_MC:-$_ROOT}"   # v2:env测试缝保留·缺省走声明(2026-10-05)
RS="$MC/开发工具/buluotuo-release-sync"

echo "═══ ① 源侧清洁 + 单向同步 ═══"
python3 "$RS/单向真源同步.py"

echo
echo "═══ ② 收口闸验收（6 条机械判据）═══"
python3 "$MC/开发工具/脚本体系收口闸.py"