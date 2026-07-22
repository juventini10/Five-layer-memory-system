# amber-install-service.ps1 — 用 NSSM 把记忆琥珀监听注册为 Windows 服务（首选方式）
# ─────────────────────────────────────────────────────────────
# 为什么用 NSSM Service 而不是 Task Scheduler（来自真机治本经验）：
#   · 长驻进程该由 SCM(服务控制管理器)管理——与 macOS 的 launchd 对称
#   · Service 无 conhost → 无弹窗；SCM 原生自愈重启，比 Task Scheduler 更稳
#   · 彻底绕开 0xC000013A(交互控制台 CTRL+C 杀进程)——服务不挂交互会话
# 前提：需要【管理员权限】注册服务。无管理员权限时请用 amber-install-task.ps1（回退）。
# ─────────────────────────────────────────────────────────────
# nssm.exe 查找顺序：AMBER_NSSM 环境变量 → engine\nssm\nssm.exe(随包) → PATH
# AMBER_MC 环境变量可覆盖记忆中心根目录（并会写入服务环境，服务进程据此定位）

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

$ServiceName = 'MemoryAmberWatch'
$ServiceDesc = '记忆琥珀文件监听服务（NSSM/SCM 管理，开机自启，崩溃 5 秒自愈）'

if (-not (Test-Path $WatchScript)) {
    Write-Host "错误：监听脚本不存在 $WatchScript" -ForegroundColor Red
    exit 1
}

# 管理员校验（注册服务必需）
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 注册 Windows 服务需要管理员权限。" -ForegroundColor Red
    Write-Host "   请以管理员身份运行 PowerShell 后重试，或改用免提权的 amber-install-task.ps1。" -ForegroundColor Yellow
    exit 2
}

# 查找 nssm.exe
function Resolve-Nssm {
    if ($env:AMBER_NSSM -and (Test-Path $env:AMBER_NSSM)) { return $env:AMBER_NSSM }
    $bundled = Join-Path $EngineDir 'nssm\nssm.exe'
    if (Test-Path $bundled) { return $bundled }
    $cmd = Get-Command nssm -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmdExe = Get-Command nssm.exe -ErrorAction SilentlyContinue
    if ($cmdExe) { return $cmdExe.Source }
    return $null
}
$Nssm = Resolve-Nssm
if (-not $Nssm) {
    Write-Host "❌ 找不到 nssm.exe。请把 nssm.exe 放到 $EngineDir\nssm\，或设 AMBER_NSSM 环境变量。" -ForegroundColor Red
    Write-Host "   （nssm 下载：https://nssm.cc/ 或 choco install nssm）" -ForegroundColor Yellow
    exit 3
}

# 解析 pwsh 完整路径（绝不用裸名）
function Resolve-PwshPath {
    $candidates = @()
    if ($env:ProgramFiles)        { $candidates += (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe') }
    if ($env:ProgramW6432)        { $candidates += (Join-Path $env:ProgramW6432 'PowerShell\7\pwsh.exe') }
    if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'PowerShell\7\pwsh.exe') }
    foreach ($c in $candidates) { if ($c -and (Test-Path $c)) { return $c } }
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
}
$PwshPath = Resolve-PwshPath

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

Write-Host "=== 记忆琥珀 NSSM 服务注册 ===" -ForegroundColor Cyan
Write-Host "服务名: $ServiceName"
Write-Host "nssm:   $Nssm"
Write-Host "pwsh:   $PwshPath"
Write-Host "脚本:   $WatchScript"
Write-Host "记忆中心: $MC"
Write-Host ""

# 已存在先删
$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "已存在同名服务，先停止并删除旧服务..." -ForegroundColor Yellow
    & $Nssm stop $ServiceName 2>$null | Out-Null
    Start-Sleep -Seconds 2
    & $Nssm remove $ServiceName confirm 2>$null | Out-Null
    Start-Sleep -Seconds 2
}

$argLine = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$WatchScript`""

& $Nssm install $ServiceName $PwshPath $argLine | Out-Null
& $Nssm set $ServiceName AppDirectory $EngineDir | Out-Null
& $Nssm set $ServiceName DisplayName $ServiceName | Out-Null
& $Nssm set $ServiceName Description $ServiceDesc | Out-Null
& $Nssm set $ServiceName Start SERVICE_AUTO_START | Out-Null          # 开机自启
& $Nssm set $ServiceName AppExit Default Restart | Out-Null           # 崩溃自动重启
& $Nssm set $ServiceName AppRestartDelay 5000 | Out-Null              # 5 秒重启（对齐 SCM 经验）
& $Nssm set $ServiceName AppStdout (Join-Path $LogDir 'amber-service.out.log') | Out-Null
& $Nssm set $ServiceName AppStderr (Join-Path $LogDir 'amber-service.err.log') | Out-Null
# 关键：把 AMBER_MC 写进服务环境，服务进程不继承当前会话变量，靠这个定位记忆中心
& $Nssm set $ServiceName AppEnvironmentExtra "AMBER_MC=$MC" | Out-Null

& $Nssm start $ServiceName | Out-Null
Start-Sleep -Seconds 3

$svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($svc -and $svc.Status -eq 'Running') {
    Write-Host "✅ 服务已注册并运行: $ServiceName (Status=$($svc.Status), StartType=$($svc.StartType))" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== 验证 ===" -ForegroundColor Cyan
    Write-Host "改白名单内任一文件 → 等 ~20 秒 → 看 $LogDir\amber-watch.log 出现「已触发备份」"
    Write-Host "心跳: $LogDir\amber-watch.heartbeat 应每轮更新"
    Write-Host ""
    Write-Host "=== 维护命令 ===" -ForegroundColor Cyan
    Write-Host "查状态: Get-Service $ServiceName"
    Write-Host "重启:   & '$Nssm' restart $ServiceName"
    Write-Host "卸载:   & '$Nssm' remove $ServiceName confirm"
    exit 0
} else {
    $st = if ($svc) { $svc.Status } else { '不存在' }
    Write-Host "❌ 服务未能进入 Running 状态（当前: $st）。查看 $LogDir\amber-service.err.log" -ForegroundColor Red
    exit 4
}
