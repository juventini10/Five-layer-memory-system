#!/usr/bin/env bash
# run_registry_guards.sh — Stop 钩子入口·守卫族自动体检（2026-10-03·端中立）
#
# 机制：registry_guards.sh 是「文件系统即真相源」——扫 GUARD_DIR 下全部 *guard.sh 自动跑。
#       本文件只做两件事：①定位用户机上的守卫目录 ②把输出交给 Stop 链。
#
# ⚠️ 落点错配（2026-10-03 修·实测抓到）：本文件被 ROSTER 复制到 <配置根>/hooks/，
#    而 registry_guards.sh 由 DT_SUITE 落在 <记忆中心>/数字分身/guards/ —— **两者不同目录**。
#    若用「脚本同目录」作缺省 ⇒ exec 找不到文件 ⇒ **静默失败（最坏的一类：装了≠活了）**。
#    ⇒ 守卫目录必须从 runtime_paths 的 twin 键解析（安装器唯一写入口保证该文件存在）。
#
# ⛔ 端中立：无作者侧路径；解析顺序 = 环境变量 → runtime_paths(twin) → 脚本同目录。
set -uo pipefail
_self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ① 显式环境变量优先（测试/特殊部署用）
GUARD_DIR="${BULUOTUO_GUARD_DIR:-}"

# ② 读运行路径声明的 twin 键（安装器 write_runtime_paths 生成·单一真源）
if [ -z "$GUARD_DIR" ] && [ -n "${BULUOTUO_RUNTIME_PATHS:-}" ] && [ -f "${BULUOTUO_RUNTIME_PATHS}" ]; then
  GUARD_DIR="$(python3 - "${BULUOTUO_RUNTIME_PATHS}" <<'PYEOF' 2>/dev/null
import json, sys, os
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    twin = d.get("twin")
    print(os.path.join(twin, "guards") if twin else "")
except Exception:
    print("")
PYEOF
)"
fi

# ③ 缺省：脚本同目录（守卫与入口同放时成立）
[ -z "$GUARD_DIR" ] && GUARD_DIR="$_self_dir"
export BULUOTUO_GUARD_DIR="$GUARD_DIR"

if [ ! -f "$GUARD_DIR/registry_guards.sh" ]; then
  echo "[i] 守卫族未安装（查 $GUARD_DIR）·跳过·不影响其他功能"
  exit 0
fi
exec bash "$GUARD_DIR/registry_guards.sh" 2>&1
