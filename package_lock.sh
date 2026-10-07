#!/bin/bash
# package_lock.sh —— 安装包写入串行闸（mkdir 原子锁）· v2.0 自愈版
# 协议详见同目录 PACKAGE-LOCK.md。用法:
#   bash package_lock.sh acquire <端名>    # 写前获取（他端持锁<6h=拒绝·半残锁>60s=自愈后获取）
#   bash package_lock.sh release <端名>    # 写完释放（持锁>6h=僵尸锁可强释）
#   bash package_lock.sh status            # 查看当前锁（含半残态显形）
# v2.0 根治（2026-10-07·Qoder CN·半残僵尸锁案）：acquire 若中断于 mkdir 与 holder 写入之间
#   → lock.dir 在而 holder 无 = 结构性死锁（status 假报 FREE、后续 acquire 全 REFUSED 需人工 --force）。
#   自愈判据：lock.dir 存在 ∧ (holder 缺失|空|ts 非数字) ∧ lock.dir mtime 龄 > GRACE(60s)
#   → 认定半残非活锁，AUTO-REPAIR 清理后重试一次，全程打印留痕不静默。
#   安全边界：holder 完好的真僵尸锁（>6h）不自动释放——可能对应仍在编辑的活端，保留人工 force 协议。
set -u
D="$(cd "$(dirname "$0")" && pwd)/.package-lock"
H="$D/holder"
L="$D/lock.dir"
ZOMBIE_SECS=21600   # 6h
GRACE=60            # 半残自愈宽限（防 mkdir→printf 微秒窗口误判）
now=$(date +%s)
who="${2:-}"

_dir_age() {  # lock.dir mtime 龄（秒）· BSD/GNU stat 双兼容
  local m
  m=$(stat -f %m "$L" 2>/dev/null || stat -c %Y "$L" 2>/dev/null || echo 0)
  echo $(( now - m ))
}

is_halfbaked() {  # 返回0=半残（holder 缺失/空/ts 非数字）
  [ ! -s "$H" ] && return 0
  local ts
  ts=$(cut -f3 "$H" 2>/dev/null)
  case "$ts" in ''|*[!0-9]*) return 0;; *) return 1;; esac
}

try_selfrepair() {  # 命中半残且超宽限→清理留痕·返回0=已清理可重试
  [ -d "$L" ] || return 1
  is_halfbaked || return 1
  local age
  age=$(_dir_age)
  if [ "$age" -gt "$GRACE" ]; then
    rm -f "$H"; rmdir "$L" 2>/dev/null
    echo "AUTO-REPAIR: 清理半残锁（lock.dir 无有效 holder·龄${age}s>${GRACE}s·判定=acquire 中断残迹，非活锁）"
    return 0
  fi
  return 1
}

case "${1:-}" in
  acquire)
    [ -z "$who" ] && { echo "用法: acquire <端名>"; exit 2; }
    mkdir -p "$D"
    if ! mkdir "$L" 2>/dev/null; then
      try_selfrepair
      if ! mkdir "$L" 2>/dev/null; then
        if is_halfbaked; then
          echo "REFUSED: lock.dir 半残但龄$(_dir_age)s<${GRACE}s宽限期——疑似另一 acquire 正在写入，稍后重试"
        else
          holder=$(cut -f1 "$H" 2>/dev/null || echo 未知); ts=$(cut -f3 "$H" 2>/dev/null)
          age=$(( now - ts ))
          if [ "$age" -gt "$ZOMBIE_SECS" ]; then
            echo "REFUSED: 持锁者=$holder 已${age}s=僵尸(>${ZOMBIE_SECS}s)——确认对方已死可: release $holder --force"
          else
            echo "REFUSED: 持锁者=$holder 已${age}s——写入需排队"
          fi
        fi
        exit 1
      fi
    fi
    printf '%s\t%s\t%s\n' "$who" "$(date '+%F %T')" "$now" > "$H"
    echo "ACQUIRED: $who"; exit 0;;
  release)
    [ -z "$who" ] && { echo "用法: release <端名> [--force]"; exit 2; }
    # v2.1 顺序显形（2026-10-07·执锁方 release 先于 commit 的顺序偏差自捕）：
    #   协议第2步=先 commit 后 release。release 时包目录仍有未提交改动 ⇒ 打印 WARN 显形
    #   （⛔不拦截——其中可能混他端 WIP，拦=替别人扣锁；显形即达"不静默"底线）。非 git 环境静默跳过。
    PKGROOT="$(cd "$(dirname "$D")" && pwd)"
    if command -v git >/dev/null 2>&1 && git -C "$PKGROOT" rev-parse --git-dir >/dev/null 2>&1; then
      dirty=$(git -C "$PKGROOT" status --porcelain -- "$PKGROOT" 2>/dev/null)
      [ -n "$dirty" ] && echo "WARN: 包目录仍有 $(printf '%s\n' "$dirty" | grep -c .) 项未提交改动（协议=先 commit 后 release·WARN-ONLY·他端WIP混列其中不区分）"
    fi
    holder=$(cut -f1 "$H" 2>/dev/null || true)
    ts=$(cut -f3 "$H" 2>/dev/null || echo 0)
    age=$(( now - ts ))
    if [ "${3:-}" = "--force" ]; then
      rm -f "$H"; rmdir "$L" 2>/dev/null; echo "FORCE-RELEASED by $who (was=${holder:-none} age=${age}s)"; exit 0
    fi
    if [ "$holder" != "$who" ]; then echo "REFUSED: 锁持有者是 ${holder:-无人}，非 ${who}（僵尸锁用 --force）"; exit 1; fi
    rm -f "$H"; rmdir "$L" 2>/dev/null; echo "RELEASED: $who"; exit 0;;
  status)
    if [ -d "$L" ] && is_halfbaked; then
      echo "INCONSISTENT: lock.dir 存在但 holder 缺失/损坏（半残锁·龄$(_dir_age)s）——超${GRACE}s 将在下次 acquire 自动修复"; exit 0
    fi
    if [ -f "$H" ]; then awk -F'\t' -v n="$now" '{printf "HELD: %s since %s (age %ds)\n",$1,$2,n-$3}' "$H"; else echo "FREE"; fi; exit 0;;
  *) echo "用法: package_lock.sh {acquire|release|status} [端名]"; exit 2;;
esac
