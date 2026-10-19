# systemlog-install-task.ps1 — 注册 Windows Task Scheduler 系统日志看守任务（加固版）
# 等价于 macOS 的 install_watch.sh (launchd com.buluotuo.systemlog.watch)
# ─────────────────────────────────────────────────────────────
# 加固模式镜像 amber-install-task.ps1（对症 0xC000013A STATUS_CONTROL_C_EXIT）：
#   ① pwsh 用【完整路径】而非裸名 —— 裸 pwsh.exe 在任务上下文里正是该错误码诱因
#   ② LogonType = S4U「不管用户是否登录都运行」—— 脱离交互控制台会话
#   ③ 双触发器 AtLogOn + AtStartup + MultipleInstances=IgnoreNew —— 补触发覆盖 + 防重入
# 可测性：SL_WATCH_SCRIPT 环境变量覆盖被看守脚本路径（CI/沙盒测试用）
# 卸载：systemlog-install-task.ps1 -Uninstall（对齐 mac 版 install_watch.sh --uninstall 语义）

[CmdletBinding()]
param([switch]$Uninstall)

$ErrorActionPreference = 'Stop'

$TaskName = 'SystemLogWatch'
$TaskDesc = '系统日志写时守护——开机自启，崩溃自动重启（轮询归一版·Win 对等 mac fswatch）'

# 被看守脚本：默认=本脚本同目录 systemlog-watch.ps1（装机态 <MC>/技能配置/system-logger/scripts/ 共置）
$WatchScript = $env:SL_WATCH_SCRIPT
if (-not $WatchScript) { $WatchScript = Join-Path $PSScriptRoot 'systemlog-watch.ps1' }

if ($Uninstall) {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 已卸载任务 ${TaskName}（重安装=再跑本脚本不带 -Uninstall）" -ForegroundColor Green
    } else {
        Write-Host "◽ 当前无已注册任务 ${TaskName}"
    }
    exit 0
}

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
    # 黑名单（与 amber/dualtrack 同款）：拒收版本化 WindowsApps 路径——商店自动更新版本号即变，路径秒失效
    if ($cmd -and $cmd.Source -like "*WindowsApps*") { $cmd = $null }
    if ($cmd -and $cmd.Source -match 'Microsoft\.PowerShell_') { $cmd = $null }
    if ($cmd) { return $cmd.Source }
    $wp = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($wp) { return $wp.Source }
    return "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
}
$PwshPath = Resolve-PwshPath

Write-Host "=== 系统日志看守 Task Scheduler 注册（加固版）===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "监听脚本: $WatchScript"
Write-Host "pwsh 完整路径: $PwshPath"

# 启动动作：完整路径 pwsh + 隐藏窗口 + 完整脚本路径（带引号防空格/中文）
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
    # 实锤律：判"装好了"用权威状态源 Get-ScheduledTask.State，不用"注册命令没报错"外推
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = $task | Get-ScheduledTaskInfo
    Write-Host "当前状态: $($task.State)" -ForegroundColor Cyan
    Write-Host "上次运行结果: 0x$('{0:X}' -f $info.LastTaskResult)"
    if ("$($task.State)" -ne 'Running') {
        Write-Host "🟡 已注册但 state=$($task.State)——沙箱/受限环境可复核 Get-ScheduledTask，不谎称绿"
    }

    Write-Host "=== 验证方法 ===" -ForegroundColor Cyan
    Write-Host "1. 改 工作日志/系统日志/ 下任一 系统日志_*.md → 等约 20 秒 → 看 .watch-ps.log 出现「跑归一」"
    Write-Host "2. 心跳: <系统日志目录>\.watch-ps.heartbeat（距今 < 90 秒）"
    Write-Host "3. 状态查询: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
    Write-Host "4. 卸载: powershell -File systemlog-install-task.ps1 -Uninstall"

} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    exit 1
}
