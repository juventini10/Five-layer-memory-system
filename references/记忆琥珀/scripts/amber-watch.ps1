# amber-watch.ps1 — 记忆琥珀文件监听 (Windows / PowerShell 版 · 加固轮询版)
# 等价于 macOS 版 amber-fswatch-wrapper.sh
# ─────────────────────────────────────────────────────────────
# 加固版设计（对症两个已证实的故障因）：
#   故障因 A —— 0xC000013A (STATUS_CONTROL_C_EXIT)：进程被控制台 CTRL+C 杀
#     → 本脚本内 trap 掉终止信号 + 不依赖交互控制台；根治靠 install-task 的
#       「不管用户是否登录都运行」+ pwsh 完整路径（见 amber-install-task.ps1）
#   故障因 B —— FileSystemWatcher 首次异常/缓冲区溢出即停摆：
#     → 彻底弃用事件驱动，改「轮询快照比对」，与 macOS/Windows 内核事件机制解耦
# ─────────────────────────────────────────────────────────────
# 设计：每 IntervalSec 秒扫描白名单目录 → 快照(路径→最后写入+大小) → 有变化则触发
#       amber-backup.ps1（备份脚本自带哈希去重，重复触发无害）→ 写心跳
# 可测性：支持环境变量重定向，CI/隔离测试用
#   AMBER_MC        记忆共享中心根目录（覆盖默认 $HOME\[记忆共享中心]）
#   AMBER_INTERVAL  轮询间隔秒（默认 15）
#   AMBER_ONCE      置任意值 = 只跑一轮就退出（功能测试用）
#   AMBER_MAXSEC    最长运行秒数（默认 0=永久；CI 里设个上限防挂死）

[CmdletBinding()]
param()

# 故障因 B 对策：单文件/单轮异常绝不掀翻整个循环
$ErrorActionPreference = 'Continue'

# 故障因 A 对策（脚本层兜底）：忽略 CTRL+C，别让控制台信号杀掉常驻进程
try { [Console]::TreatControlCAsInput = $true } catch { }

# ─── 路径配置（跨平台 + 环境变量可覆盖） ───
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }

$TempDir = $env:TEMP
if (-not $TempDir) { $TempDir = $env:TMPDIR }
if (-not $TempDir) { $TempDir = '/tmp' }

# 记忆中心根：环境变量优先（测试重定向），否则用默认约定路径
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }

$EngineDir    = Join-Path $MC       '记忆琥珀\engine'
$BackupScript = Join-Path $EngineDir 'amber-backup.ps1'
$LogDir       = Join-Path $EngineDir 'logs'
$WatchLog     = Join-Path $LogDir    'amber-watch.log'
$HeartbeatFile= Join-Path $LogDir    'amber-watch.heartbeat'

# 跨平台分隔符适配（Mac/Linux 上跑测试时）
if ($IsMacOS -or $IsLinux) {
    $EngineDir    = Join-Path $MC       '记忆琥珀/engine'
    $BackupScript = Join-Path $EngineDir 'amber-backup.ps1'
    $LogDir       = Join-Path $EngineDir 'logs'
    $WatchLog     = Join-Path $LogDir    'amber-watch.log'
    $HeartbeatFile= Join-Path $LogDir    'amber-watch.heartbeat'
}

$IntervalSec = 15
if ($env:AMBER_INTERVAL) { $IntervalSec = [int]$env:AMBER_INTERVAL }
$RunOnce = [bool]$env:AMBER_ONCE
$MaxSec  = 0
if ($env:AMBER_MAXSEC) { $MaxSec = [int]$env:AMBER_MAXSEC }

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

function Write-WatchLog {
    param([string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    try { Add-Content -Path $WatchLog -Value "[$ts] $Message" -Encoding UTF8 } catch { }
}

# ─── 故障因 A 根治靠 install-task；这里解析 pwsh 完整路径供子进程调用 ───
function Resolve-PwshPath {
    # 1) 已知安装位置优先（子进程 PATH 未刷新时最可靠——正是 0xC000013A 诱因之一）
    # 注：逐个判空再 拼，非 Windows 上 $env:ProgramFiles 为 null，Join-Path 会报错
    $candidates = @()
    if ($env:ProgramFiles)        { $candidates += (Join-Path $env:ProgramFiles 'PowerShell\7\pwsh.exe') }
    if ($env:ProgramW6432)        { $candidates += (Join-Path $env:ProgramW6432 'PowerShell\7\pwsh.exe') }
    if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'PowerShell\7\pwsh.exe') }
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    # 2) PATH 里找 pwsh
    $cmd = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    # 3) 回退 Windows PowerShell 5.1（一样能跑备份脚本）
    $wp = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($wp) { return $wp.Source }
    return 'powershell.exe'
}
$PwshPath = Resolve-PwshPath

# ─── 监听目录列表（与 amber-whitelist.txt 覆盖目录一致） ───
function Get-WatchPaths {
    $rel = @(
        '核心层','QClaw记忆','潜意识层','情境层','记忆规则',
        '成就系统\scripts',
        '技能配置\daily-buddy','技能配置\shall-we-talk','技能配置\triwich',
        '技能配置\clock-loop','技能配置\growth-box','技能配置\awaken-memory-system',
        '技能配置\reading-assistant','技能配置\system-logger','技能配置\meta-aletheia'
    )
    $paths = @(
        (Join-Path $HomeDir '.workbuddy')
    )
    foreach ($r in $rel) {
        $seg = if ($IsMacOS -or $IsLinux) { $r -replace '\\','/' } else { $r }
        $paths += (Join-Path $MC $seg)
    }
    return $paths
}

# ─── 轮询快照：枚举监听目录下所有文件的 (FullName → LastWrite.Ticks + Length) ───
function Get-Snapshot {
    param([string[]]$Paths)
    $snap = @{}
    foreach ($p in $Paths) {
        if (-not (Test-Path $p)) { continue }
        try {
            Get-ChildItem -Path $p -Recurse -File -Force -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $snap[$_.FullName] = "$($_.LastWriteTimeUtc.Ticks):$($_.Length)"
                }
        } catch {
            Write-WatchLog "扫描目录出错（非致命）: $p -> $_"
        }
    }
    return $snap
}

function Test-SnapshotChanged {
    param([hashtable]$Old, [hashtable]$New)
    if ($null -eq $Old) { return $false }   # 首轮建基线，不触发
    if ($Old.Count -ne $New.Count) { return $true }
    foreach ($k in $New.Keys) {
        if (-not $Old.ContainsKey($k)) { return $true }
        if ($Old[$k] -ne $New[$k])     { return $true }
    }
    return $false
}

function Invoke-BackupOnce {
    if (-not (Test-Path $BackupScript)) {
        Write-WatchLog "错误：备份脚本不存在 $BackupScript"
        return
    }
    try {
        $outLog = Join-Path $LogDir 'amber-fswatch.out.log'
        & $PwshPath -NoProfile -ExecutionPolicy Bypass -File $BackupScript *>> $outLog
        Write-WatchLog "已触发备份（pwsh=$PwshPath）"
    } catch {
        Write-WatchLog "触发备份出错（非致命）: $_"
    }
}

# ─── 主循环 ───
$watchPaths = Get-WatchPaths
$existing = $watchPaths | Where-Object { Test-Path $_ }
Write-WatchLog "=== 记忆琥珀监听启动（轮询模式 interval=${IntervalSec}s，$($existing.Count)/$($watchPaths.Count) 个目录存在）==="
Write-WatchLog "pwsh 路径: $PwshPath"

$startTime = Get-Date
$prevSnap = $null

try {
    while ($true) {
        # 每轮包 try-catch：任何异常只记录，不退出循环（故障因 B 对策）
        try {
            $snap = Get-Snapshot -Paths $watchPaths
            if (Test-SnapshotChanged -Old $prevSnap -New $snap) {
                Write-WatchLog "检测到变化，触发备份"
                Invoke-BackupOnce
            }
            $prevSnap = $snap
            Set-Content -Path $HeartbeatFile -Value (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -Encoding ascii
        } catch {
            Write-WatchLog "轮询循环出错（非致命，继续）: $_"
        }

        if ($RunOnce) { Write-WatchLog "AMBER_ONCE 已设置，跑完一轮退出"; break }
        if ($MaxSec -gt 0 -and ((Get-Date) - $startTime).TotalSeconds -ge $MaxSec) {
            Write-WatchLog "达到 AMBER_MAXSEC=$MaxSec，退出"; break
        }
        Start-Sleep -Seconds $IntervalSec
    }
} finally {
    Write-WatchLog "=== 记忆琥珀监听已停止 ==="
}
