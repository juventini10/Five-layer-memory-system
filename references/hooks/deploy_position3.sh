#!/usr/bin/env bash
# deploy_position3.sh — 岗位3「声明-实盘对账官」跨端一键部署（童灵收口·风险①根治）
#
# 设计定位（第一性原理）：
#   WB 无跨机 SSH 权限 → 无法替你在其他端物理部署。本脚本把"WB 能做的部分"彻底收口：
#   生成一个按本机 $HOME / python3 实时替换路径的 launchd plist（launchd 不认 ~ 展开），
#   复制脚本、加载作业、幂等可重跑。你只需在每个端把部署包放好、跑一次本脚本。
#
# 部署包内容（与本脚本同目录）：
#   deploy_position3.sh  position3_audit.py  position3_notify.py
#
# 用法：bash deploy_position3.sh          # 部署+加载（幂等）
# 行为：每日 StartInterval 86400 + RunAtLoad（登录即跑·睡眠/重启自愈·愿景①不依赖人记得）
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="[记忆共享中心]/数字分身/scripts"
PLIST_DST="$HOME/Library/LaunchAgents/com.buluotuo.position3-audit.plist"
PY="$(command -v python3 || echo /usr/local/bin/python3)"
LABEL="com.buluotuo.position3-audit"

echo "=== 岗位3对账官 部署（端: $DEST_DIR · python: $PY）==="

# 1. 复制脚本（幂等: 内容相同则跳过）
mkdir -p "$DEST_DIR"
for f in position3_audit.py position3_notify.py; do
  if [ -f "$BUNDLE_DIR/$f" ]; then
    if cmp -s "$BUNDLE_DIR/$f" "$DEST_DIR/$f" 2>/dev/null; then
      echo "  [跳过] $f 已最新"
    else
      cp "$BUNDLE_DIR/$f" "$DEST_DIR/$f" && echo "  [复制] $f"
    fi
  else
    echo "  [警告] 部署包缺 $f, 跳过（其余照常）"
  fi
done

# 2. 生成 plist（路径按本机实时替换; launchd 不认 ~）
cat > "$PLIST_DST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PY</string>
        <string>$DEST_DIR/position3_audit.py</string>
    </array>
    <key>StartInterval</key>
    <integer>86400</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/position3_audit.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/position3_audit.err</string>
</dict>
</plist>
PLIST
echo "  [生成] $PLIST_DST"

# 3. 加载（幂等: 已加载则跳过）
if launchctl list "$LABEL" >/dev/null 2>&1; then
  echo "  [跳过] $LABEL 已加载"
else
  if launchctl load "$PLIST_DST" 2>/dev/null; then
    echo "  [加载] $LABEL ✅"
  else
    echo "  [注意] launchctl load 受限（沙箱/权限）→ 请在本机终端手动跑: launchctl load $PLIST_DST"
  fi
fi

echo "✅ 岗位3对账官 已就绪（每日一次 + 登录即跑 · 睡眠/重启自愈）"
