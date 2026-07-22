# amber-install-task.ps1 — 注册 Windows Task Scheduler 开机自启任务（加固版）
# 等价于 macOS 的 com.memoryamber.backup.plist (launchd)
# ─────────────────────────────────────────────────────────────
# 加固版对症 0xC000013A (STATUS_CONTROL_C_EXIT)：
#   ① pwsh 用【完整路径】而非裸名 —— 裸 pwsh.exe 在任务上下文里正是该错误码诱因
#   ② LogonType = S4U「不管用户是否登录都运行」—— 脱离交互控制台会话，
#      登录瞬态控制台关闭时不会把 CTRL+C 打到本进程（根治 A 的关键）
#   ③ 双触发器 AtLogOn + AtStartup + MultipleInstances=IgnoreNew —— 补触发覆盖 + 防重入
# ─────────────────────────────────────────────────────────────
# 可测性：AMBER_MC 环境变量覆盖记忆中心根目录

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }

$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }

$EngineDir   = Join-Path $MC '记忆琥珀\engine'
$WatchScript = Join-Path $EngineDir 'amber-watch.ps1'
$LogDir      = Join-Path $EngineDir 'logs'
$WatchLog    = Join-Path $LogDir 'amber-watch.log'

$TaskName = 'MemoryAmberWatch'
$TaskDesc = '记忆琥珀文件监听服务——开机自启，崩溃自动重启（加固轮询版）'

if (-not (Test-Path $WatchScript)) {
    Write-Host "错误：监听脚本不存在 $WatchScript" -ForegroundColor Red
    exit 1
}

# ① pwsh 完整路径解析（已知安装位置优先，绝不用裸名）
function Resolve-PwshPath {
    $candidates = @()
    if ($env:ProgramFiles)        { $candidates += (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe') }
    if ($env:ProgramW6432)        { $candidates += (Join-Path $env:ProgramW6432 'PowerShell\7\pwsh.exe') }
    if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'PowerShell\7\pwsh.exe') }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $wp = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($wp) { return $wp.Source }
    # 最后兜底：Windows PowerShell 5.1 的确定路径
    return "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
}
$PwshPath = Resolve-PwshPath

Write-Host "=== 记忆琥珀 Task Scheduler 注册（加固版）===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "监听脚本: $WatchScript"
Write-Host "pwsh 完整路径: $PwshPath"
Write-Host "日志文件: $WatchLog"
Write-Host ""

# 启动动作：完整路径 pwsh + 隐藏窗口 + 完整脚本路径（全部带引号防空格/中文）
$action = New-ScheduledTaskAction `
    -Execute $PwshPath `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$WatchScript`""

# ③ 双触发器：开机 + 登录，双保险覆盖
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn),
    (New-ScheduledTaskTrigger -AtStartup)
)

# 设置：崩溃自动重启 + 防重入（同时只跑一个实例）
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

# ② 主体：S4U「不管用户是否登录都运行」—— 脱离交互控制台，根治 CTRL+C 猝死
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType S4U `
    -RunLevel Limited

# 注册（已存在先删）
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "已存在同名任务，先删除旧任务..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $TaskDesc `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    Write-Host "✅ Task Scheduler 任务已注册: $TaskName" -ForegroundColor Green

    Start-ScheduledTask -TaskName $TaskName
    Write-Host "✅ 任务已启动" -ForegroundColor Green

    Start-Sleep -Seconds 3
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = $task | Get-ScheduledTaskInfo
    Write-Host ""
    Write-Host "当前状态: $($task.State)" -ForegroundColor Cyan
    Write-Host "上次运行结果: 0x$('{0:X}' -f $info.LastTaskResult)"
    Write-Host "最后运行时间: $($info.LastRunTime)"
    Write-Host ""
    Write-Host "=== 验证方法 ===" -ForegroundColor Cyan
    Write-Host "1. 改白名单内任一文件 → 等 ~20 秒 → 看 $WatchLog 出现「已触发备份」"
    Write-Host "2. 心跳文件应每轮更新: $LogDir\amber-watch.heartbeat"
    Write-Host "3. 状态查询: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"

} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    exit 1
}
