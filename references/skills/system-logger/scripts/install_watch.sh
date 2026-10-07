#!/usr/bin/env bash
# install_watch.sh v1.0 — 系统日志看守器（launchd）安装器 · 脱敏根治版
#
# 为什么不再随包分发 systemlog_watch.plist（2026-08-30 根治）：
#   旧做法 = 仓库里存一份写死绝对路径的 plist → 发布物含个人态字面量
#   （/Users/{用户名}/个人AI档案/…）→ desensitize 门禁 ❌ 发布阻断；
#   且别人装完路径全指向我的家目录，看守器根本起不来（静默失效）。
#   launchd 不展开 ProgramArguments 里的 $HOME，所以"把路径改成 $HOME/…"是假修
#   ——骗过扫描器却引入真故障。正确解 = 源头不产生个人态：运行时渲染。
#
# 用法：bash install_watch.sh [--self-test] [--uninstall]
set -euo pipefail

# v3.11.0 清零批#8：装前探测 fswatch（PATH + 常见 Homebrew 路径）——缺失即报警退出，
# 不渲染 plist 不 launchctl（否则 KeepAlive=true 会"exit 7→被拉起"循环·复核第2轮观察项）。
detect_fswatch() {
  local bin
  bin="$(command -v fswatch || true)"
  [ -z "$bin" ] && for c in /opt/homebrew/bin/fswatch /usr/local/bin/fswatch; do
    [ -x "$c" ] && bin="$c" && break
  done
  if [ -z "$bin" ]; then
    echo "🔴 fswatch 未安装（PATH 与 /opt/homebrew/bin、/usr/local/bin 均未命中）——拒绝安装看守器" >&2
    echo "   治理：brew install fswatch 后重跑本安装器（⛔不装=无写时守护，写入仍可用·门禁五查仍在）" >&2
    return 1
  fi
  echo "fswatch=$bin"
}

LABEL="com.buluotuo.systemlog.watch"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCH_SH="${SCRIPT_DIR}/systemlog_watch.sh"
AGENT_DIR="${HOME}/Library/LaunchAgents"
PLIST="${AGENT_DIR}/${LABEL}.plist"

render_plist() { # $1=输出路径 $2=被看守脚本路径（缺省=本脚本同目录 systemlog_watch.sh）
  local watch="${2:-${WATCH_SH}}"
  cat >"$1" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${watch}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>[记忆共享中心]/工作日志/系统日志</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>[记忆共享中心]/工作日志/系统日志/.watch.log</string>
    <key>StandardErrorPath</key>
    <string>[记忆共享中心]/工作日志/系统日志/.watch.err</string>
</dict>
</plist>
PLIST_EOF
}

do_uninstall() {
  if launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1; then
    echo "✅ 已卸载 ${LABEL}（plist 保留在 ${PLIST}，重安装=再跑本脚本）"
  else
    echo "◽ 当前无已挂载的 ${LABEL}"
  fi
  return 0
}

do_install() {
  [ -f "${WATCH_SH}" ] || { echo "⛔ 找不到看守脚本：${WATCH_SH}" >&2; return 2; }
  mkdir -p "${AGENT_DIR}"
  if [ -f "${PLIST}" ] && diff -q <(render_plist /dev/stdout) "${PLIST}" >/dev/null 2>&1; then
    echo "✅ plist 已是最新渲染结果：${PLIST}"
  else
    render_plist "${PLIST}.new"
    mv "${PLIST}.new" "${PLIST}"
    echo "✏️ 已按当前家目录渲染：${PLIST}"
  fi
  launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "${PLIST}" 2>/dev/null \
    || { echo "⚠️ bootstrap 失败，回退 launchctl load"; launchctl load "${PLIST}"; }
  # 实锤律：判"装好了"用权威状态源 launchctl print state，不用"文件写出来了"外推
  local st
  st="$(launchctl print "gui/$(id -u)/${LABEL}" 2>/dev/null | awk '/^[[:space:]]*state = /{print $3; exit}')"
  if [ "${st}" = "running" ]; then
    echo "✅ ${LABEL} state=running（launchctl 实读）"
  else
    echo "🟡 已挂载但 state='${st:-未知}'——沙箱/非 GUI 会话属正常，人查一眼 launchctl print"
  fi
}

self_test() {
  local pass=0 fail=0 tmp rendered real_home
  real_home="${HOME}"
  tmp="$(mktemp -d)"
  rendered="${tmp}/watch.rendered.plist"
  # 用临时家目录跑一遍渲染（证明路径来自 $HOME 而非写死）
  HOME="${tmp}"
  render_plist "${rendered}" "${tmp}/systemlog_watch.sh"
  # U1 渲染结果不得含个人态字面量（真实家目录绝对路径不得出现·动态取值不写死）
  if grep -qF "${real_home}/" "${rendered}" 2>/dev/null; then
    echo "❌ U1 渲染结果仍含真实家目录（脱敏失败）"; fail=$((fail + 1))
  else
    echo "✅ U1 渲染结果零个人态"; pass=$((pass + 1))
  fi
  # U2 渲染结果须含临时家目录前缀（证明确实按 $HOME 渲染，而非空串）
  if grep -q "${tmp}/个人AI档案" "${rendered}"; then
    echo "✅ U2 路径按 \$HOME 动态生成"; pass=$((pass + 1))
  else
    echo "❌ U2 未按 \$HOME 渲染"; fail=$((fail + 1))
  fi
  # U3 plist 语法合法（plutil 缺失时显式 SKIP，不混成 ✅ 也不造假红）
  if command -v plutil >/dev/null 2>&1; then
    if plutil -lint "${rendered}" | grep -q "OK"; then
      echo "✅ U3 plutil -lint OK"; pass=$((pass + 1))
    else
      echo "❌ U3 plist 语法非法"; fail=$((fail + 1))
    fi
  else
    echo "⏭️ U3 SKIP（本机无 plutil）"
  fi
  # U4 关键键齐备（少一个键=看守器静默不跑）
  local k miss=""
  for k in Label ProgramArguments WorkingDirectory KeepAlive StandardOutPath StandardErrorPath; do
    grep -q "<key>${k}</key>" "${rendered}" || miss="${miss} ${k}"
  done
  if [ -z "${miss}" ]; then
    echo "✅ U4 六键齐备"; pass=$((pass + 1))
  else
    echo "❌ U4 缺键:${miss}"; fail=$((fail + 1))
  fi
  rm -rf "${tmp}"
  echo "===== install_watch 夹具: ${pass} 通过 / ${fail} 失败 ====="
  [ "${fail}" -eq 0 ]
}

case "${1:-}" in
  --self-test) self_test ;;
  --uninstall) do_uninstall ;;
  "")
    # 装前探测（v3.11.0 清零批#8）：fswatch 缺失=拒绝安装（防 KeepAlive 拉起循环）
    FS_LOC="$(detect_fswatch)" || exit 7
    echo "✅ 装前探测通过（${FS_LOC}）"
    do_install
    ;;
  *) echo "用法: bash install_watch.sh [--self-test|--uninstall]" >&2; exit 2 ;;
esac
