# amber-install-dualtrack.ps1 — 双轨定时任务注册（Windows）
# 注册两个计划任务（普通用户权限即可，不需管理员）：
#   ① MemoryAmberCheckup     每天 08:00 跑 amber-checkup.ps1（写 amber-status.txt，供唤醒Skill读盘保底）
#   ② MemoryAmberWeeklyReport 每周日 19:30 跑 amber-weekly-popup.ps1（中央弹窗周报，加强渠道可丢包）
# 幂等：重复运行 = 覆盖注册同名任务，不会产生重复任务
$ErrorActionPreference = 'Stop'

$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }
$Engine = Join-Path $MC '记忆琥珀/engine'

# 选 PowerShell 可执行体：优先 pwsh(7+)，回退 powershell.exe(5.1)
$psExe = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
# ⑨黑名单（批6h＝#136）：拒收版本化 WindowsApps 路径——商店自动更新版本号即变，路径秒失效
if ($psExe -and $psExe -like "*WindowsApps*") { $psExe = $null }
if ($psExe -match 'Microsoft\.PowerShell_') { $psExe = $null }
if (-not $psExe) { $psExe = (Get-Command powershell -ErrorAction SilentlyContinue).Source }
if (-not $psExe) { Write-Host "❌ 未找到 PowerShell 可执行体"; exit 1 }

function Register-AmberTask {
    param([string]$Name, [string]$Script, $Trigger)
    $action = New-ScheduledTaskAction -Execute $psExe -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`""
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger -Settings $settings -Force | Out-Null
    Write-Host "✅ 已注册计划任务: $Name"
}

# ① 每日体检 08:00（StartWhenAvailable=开机错过后补跑）
Register-AmberTask -Name 'MemoryAmberCheckup' `
    -Script (Join-Path $Engine 'amber-checkup.ps1') `
    -Trigger (New-ScheduledTaskTrigger -Daily -At '08:00')

# ② 周日 19:30 周报弹窗
Register-AmberTask -Name 'MemoryAmberWeeklyReport' `
    -Script (Join-Path $Engine 'amber-weekly-popup.ps1') `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '19:30')

# 立即跑一次体检，让 amber-status.txt 即刻可用（弹窗不试跑——避免安装中途弹框打断）
& $psExe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Engine 'amber-checkup.ps1')
$statusFile = Join-Path $MC '记忆琥珀/engine/amber-status.txt'
if (Test-Path $statusFile) {
    Write-Host "✅ 首次体检完成，状态文件已生成："
    Get-Content $statusFile -Encoding UTF8 | Select-Object -Last 1
} else {
    Write-Host "⚠️ 状态文件未生成，请检查 amber-checkup.ps1 输出"
}
