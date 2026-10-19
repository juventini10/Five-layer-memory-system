#!/bin/bash
# ============================================================
# install_launchd.sh — 豆包办公 launchd patrol 调度注册（adapter 归入版）
# 功能:检测 plist → 尝试 bootstrap → 失败则给出精确手动指令
# 背景:launchctl bootstrap 在某些受限终端常被拒(Bootstrap failed: 5)，
#       本脚本尽力自动注册，失败时把命令打印给用户去系统终端手动执行。
# 用法: bash install_launchd.sh
# 来源: 对齐 traework adapter install_launchd.sh（豆包端·2026-10-12）
# ============================================================
set -uo pipefail
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; C='\033[0;36m'; N='\033[0m'
PLIST="$HOME/Library/LaunchAgents/com.buluotuo.doubaowork.patrol.plist"
LABEL="com.buluotuo.doubaowork.patrol"

echo -e "${C}=== 豆包办公 launchd 调度注册 ===${N}"

# 1) plist 存在性
if [ ! -f "$PLIST" ]; then
  echo -e "${R}[X] plist 不存在: $PLIST${N}"
  echo -e "    请先跑 setup（安装 plist），再跑本脚本。"; exit 1
fi
echo -e "${G}[OK] plist 存在: $PLIST${N}"

# 2) 已注册检测(launchctl print 直查 GUI 域——受限终端 launchctl list 看不到用户域会误报)
if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  echo -e "${G}[OK] launchd 任务已注册($LABEL)${N}"
  launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -E "state|path" | head -3
  exit 0
fi
echo -e "${Y}[i] launchd 任务未注册,尝试 bootstrap...${N}"

# 3) 尝试 bootstrap(受限终端可能被拒)
if launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/tmp/doubaowork_ld_err.txt; then
  echo -e "${G}[OK] bootstrap 成功!任务已注册${N}"
  launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -E "state|path" | head -3
  exit 0
fi
LD_ERR=$(cat /tmp/doubaowork_ld_err.txt 2>/dev/null); rm -f /tmp/doubaowork_ld_err.txt
echo -e "${Y}[i] bootstrap 被拒(${LD_ERR:-无输出})——请在系统终端手动执行:${N}"
echo ""
echo -e "${C}    launchctl bootstrap gui/\$(id -u) $PLIST${N}"
echo -e "${C}    验证: launchctl print gui/\$(id -u)/$LABEL${N}"
echo ""
echo -e "${Y}    也可先卸载旧任务再重装: launchctl bootout gui/\$(id -u)/$LABEL 2>/dev/null; launchctl bootstrap gui/\$(id -u) $PLIST${N}"
exit 1
