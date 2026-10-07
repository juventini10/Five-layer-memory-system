#!/bin/bash
# guard_invoke.sh v2.0 -- 手动侧轻量埋点包装器 (v2.0·2026-09-03·童灵·补exit码埋点)
# 用法: guard_invoke.sh <guard名> <原命令...>
#   例: guard_invoke.sh changelog_guard bash 开发工具/changelog-guard/changelog_guard.sh --check
# 语义: 经此包装的调用记 manual; 执行完成后写exit码; 埋点失败不影响执行(fail-open)。
# v2.0变更: 从"执行前后台写日志(无exit码)"改为"执行后写日志(含exit码)"——
#   原设计exec "$@"替换进程无法捕获exit码; v2.0直接执行"$@"捕获$?后写日志再exit $RC。
#   代价: 不再用exec(信号传递略不同), 但exit码保真优先; 埋点仍后台异步不阻塞。
N="$1"; if [ -z "$N" ]; then echo "usage: guard_invoke.sh <guard名> <命令...>" >&2; exit 2; fi
shift
# 执行原命令，捕获exit码（不用exec，否则无法捕获$?）
"$@"
RC=$?
# 写日志（含exit码），后台异步不阻塞，fail-open
python3 "$HOME/脚本中心/guard_invocation_logger.py" \"
  --guard "$N" --source manual --exit "$RC" --detail "$*" >/dev/null 2>&1 &
# 用原命令的exit码退出（保真）
exit $RC
