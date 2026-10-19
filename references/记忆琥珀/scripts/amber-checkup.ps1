# amber-checkup.ps1 — 琥珀每日体检（写状态文件，供唤醒Skill读盘保底提醒）
# 设计（设计哲学§4.10 常态审计须脚本触发）：每天由 Task Scheduler 定时跑一次
#   体检两项独立指标（各自告警，不需同时满足）：
#     ① 永久收藏超 30 天无主动收藏（_major_ 件）→ 提醒
#     ② 琥珀顶层又出现手动散件（本该进永久收藏）→ 提醒
#   输出 = engine/amber-status.txt（脚本写盘、Skill读盘——复用心跳检测先例）
#   ⚠️ 只提醒不代判：收藏与否永远由人决定
$ErrorActionPreference = 'Continue'

# === 路径配置（对齐 amber-backup.ps1）===
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }
$AmberDir = Join-Path $MC '记忆琥珀'
$PermDir  = Join-Path $AmberDir '永久收藏'
$Status   = Join-Path $AmberDir 'engine/amber-status.txt'

# 指标①：距最近一次主动收藏的天数
$newestPin = Get-ChildItem -Path $PermDir -Filter '*_major_*.bak' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $newestPin) {
    $lastPinDays = 'NEVER'
} else {
    $lastPinDays = [int]((Get-Date) - $newestPin.LastWriteTime).TotalDays
}

# 指标②：顶层手动散件数（非 .bak 滚动件）
$stray = @(Get-ChildItem -Path $AmberDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike '*.bak' -and $_.Name -ne '.DS_Store' }).Count

# 永久收藏总数（排除归档清单）
$permTotal = @(Get-ChildItem -Path $PermDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike '归档清单*' -and $_.Name -ne '.DS_Store' }).Count

# 告警判定
$alert = ''
if ($lastPinDays -eq 'NEVER') {
    # P15 根治（2026-10-19·Win腿同步）：哨兵值 NEVER 不进用户话术
    $alert = "⚠️ 永久收藏还没有过第一条——最近有定稿、改好的重要文件想永久留住吗？对AI说：帮我永久保存某某文件。"
} elseif ([int]$lastPinDays -ge 30) {
    $alert = "⚠️ 永久收藏已 $lastPinDays 天没有新收藏——最近有定稿、改好的重要文件想永久留住吗？对AI说：帮我永久保存某某文件。"
}
if ($stray -gt 0) {
    if ($alert) { $alert += ' ｜ ' }
    $alert += "⚠️ 琥珀顶层出现 $stray 个手动散件，建议归进「永久收藏」。"
}
if (-not $alert) { $alert = '✅ 琥珀双轨正常。' }

$lines = @(
    "UPDATED=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "LAST_PIN_DAYS=$lastPinDays",
    "STRAY_TOPLEVEL=$stray",
    "PERM_TOTAL=$permTotal",
    "MESSAGE=$alert"
)
# 写数据文件去 BOM（发布包编写规范 §4.4：读脚本要BOM，写数据去BOM）
[System.IO.File]::WriteAllText($Status, ($lines -join "`n") + "`n", (New-Object System.Text.UTF8Encoding($false)))
