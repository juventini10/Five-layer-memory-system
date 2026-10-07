# amber-weekly-popup.ps1 — 琥珀周报弹窗（加强渠道，保底仍是唤醒Skill读盘）
# 设计：每周日 19:30 由 Task Scheduler 定时触发（amber-install-dualtrack.ps1 注册）
#   出口 = WinForms MessageBox 中央模态框 + 系统提示音（对齐成就系统 Windows 弹窗先例，
#          等价 macOS 版 display dialog：中间弹出+确认按钮）
#   文案规范：大白话——零AI基础、零电脑基础的人也能看懂要做什么
#     禁用词：pin / 滚动区 / 永久区 / major —— 对人只说"临时备份 / 永久收藏"
#     行动指引必须带位置：说了怎么存，就要说存在哪
#   ⚠️ 只提醒不代判：收藏与否永远由人决定
$ErrorActionPreference = 'Continue'

# === 路径配置（对齐 amber-backup.ps1）===
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }
$AmberDir = Join-Path $MC '记忆琥珀'
$PermDir  = Join-Path $AmberDir '永久收藏'
$LogFile  = Join-Path $AmberDir 'engine/logs/weekly-popup.log'

# 临时备份：本周（7天内）新增数
$bakWeek = @(Get-ChildItem -Path $AmberDir -Filter '*.bak' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }).Count

# 永久收藏：总件数 + 最近一次主动收藏距今天数
$permTotal = @(Get-ChildItem -Path $PermDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notlike '归档清单*' -and $_.Name -ne '.DS_Store' }).Count
$newestPin = Get-ChildItem -Path $PermDir -Filter '*_major_*.bak' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $newestPin) {
    $permMsg = "「永久收藏」里有 $permTotal 份文件，但你还没主动收藏过新东西。"
} else {
    $ageDays = [int]((Get-Date) - $newestPin.LastWriteTime).TotalDays
    $permMsg = "「永久收藏」里有 $permTotal 份文件，最近一次收藏是 $ageDays 天前。"
}

$body = @"
这一周，我自动帮你临时备份了 $bakWeek 次。
（临时备份只保留 7 天，之后会自动清掉）

$permMsg

如果这周有写完、改好的重要文件，想永远留住——
就对 AI 说：帮我永久保存某某文件。

收藏好的文件都在这里：
记忆共享中心 → 记忆琥珀 → 永久收藏
"@
$title = "🟠 每周备份小管家 · $(Get-Date -Format 'MM月dd日')"

# 系统提示音 + 中央模态框（点"确定"关闭）
try { [System.Media.SystemSounds]::Asterisk.Play() } catch {}
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show($body, $title,
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null

# 日志（写数据去 BOM）
$logLine = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 周报弹窗已发送：临时备份+$bakWeek / $permMsg`n"
$logDir = Split-Path $LogFile -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
[System.IO.File]::AppendAllText($LogFile, $logLine, (New-Object System.Text.UTF8Encoding($false)))
