# amber-backup.ps1 — 记忆琥珀自动备份脚本 (Windows / PowerShell 版)
# 与 amber-backup.sh 逻辑等价，遵守同一份设计哲学
# 设计原则（第一性原理）：
#   1. 备份目的 = 回滚到"能用的版本"，不是归档
#   2. 版本号 = 时间戳 + 内容哈希前6位（不依赖文件内字段）
#   3. 清理 = 同日只留1份 + 7天保留 + major永久
#   4. 去重 = 内容哈希相同则跳过（防止 touch 误触发）

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

# === 路径配置（跨平台：macOS/Linux 用 $HOME，Windows 用 $env:USERPROFILE） ===
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }

# 临时目录跨平台适配
$TempDir = $env:TEMP
if (-not $TempDir) { $TempDir = $env:TMPDIR }
if (-not $TempDir) { $TempDir = '/tmp' }

# 记忆中心根：AMBER_MC 环境变量优先（隔离测试重定向），否则默认约定路径
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }

$AmberDir       = Join-Path $MC '记忆琥珀\'
$WhitelistFile  = Join-Path $MC '记忆琥珀\engine\amber-whitelist.txt'
$LogDir         = Join-Path $MC '记忆琥珀\engine\logs'
$LogFile        = Join-Path $LogDir 'amber.log'
$LockFile       = Join-Path $TempDir 'amber-backup.lock'
$RetentionDays  = 7

# 跨平台路径分隔符适配
if ($IsMacOS -or $IsLinux) {
    $AmberDir      = Join-Path $MC '记忆琥珀/'
    $WhitelistFile = Join-Path $MC '记忆琥珀/engine/amber-whitelist.txt'
    $LogDir        = Join-Path $MC '记忆琥珀/engine/logs'
    $LogFile       = Join-Path $LogDir 'amber.log'
    $LockFile      = Join-Path $TempDir 'amber-backup.lock'
}
$AmberDir = $AmberDir.TrimEnd('\','/')

# === 初始化 ===
if (-not (Test-Path $AmberDir)) { New-Item -ItemType Directory -Path $AmberDir -Force | Out-Null }
if (-not (Test-Path $LogDir))    { New-Item -ItemType Directory -Path $LogDir    -Force | Out-Null }

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $LogFile -Value "[$ts] $Message" -Encoding UTF8
}

# === 防竞态：锁文件 ===
if (Test-Path $LockFile) {
    try {
        $lockContent = Get-Content $LockFile -ErrorAction Stop  # enc-ok: PID锁纯ASCII无需编码
        if ($lockContent -match '^\d+$') {
            $lockPid = [int]$lockContent
            $running = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
            if ($running) {
                Write-Log "已有备份进程在跑 (pid=$lockPid)，跳过"
                exit 0
            }
        }
    } catch {
        # 锁文件读取失败，忽略并清理
    }
    Remove-Item $LockFile -Force -ErrorAction SilentlyContinue
}
$PID | Out-File $LockFile -Encoding ascii
$script:CleanupLock = {
    if (Test-Path $LockFile) { Remove-Item $LockFile -Force -ErrorAction SilentlyContinue }
}
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $script:CleanupLock

# === 核心函数 ===

function Get-FileHash6 {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $h = Get-FileHash -Path $Path -Algorithm SHA256
    return $h.Hash.Substring(0, 6).ToLower()
}

function Get-BaseName {
    param([string]$Path)
    $file = Split-Path $Path -Leaf
    $parent = Split-Path (Split-Path $Path -Parent) -Leaf
    $nameNoExt = [System.IO.Path]::GetFileNameWithoutExtension($file)
    $generic = @('SKILL','MEMORY','SOUL','USER','IDENTITY','AGENTS')
    if ($generic -contains $nameNoExt) {
        return "${parent}_${nameNoExt}"
    }
    return $nameNoExt
}

function Test-NeedBackup {
    param([string]$Path)
    $base = Get-BaseName $Path
    $pattern = "${base}_*.bak"
    $latest = Get-ChildItem -Path $AmberDir -Filter $pattern -ErrorAction SilentlyContinue |
              Sort-Object Name -Descending |
              Select-Object -First 1
    if (-not $latest) { return $true }
    if ($latest.Name -match '_([a-f0-9]{6})\.bak$') {
        $latestHash = $Matches[1]
        $currentHash = Get-FileHash6 $Path
        if ($latestHash -eq $currentHash) { return $false }
    }
    return $true
}

function Invoke-Backup {
    param([string]$Path)
    $base = Get-BaseName $Path
    $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
    $hash6 = Get-FileHash6 $Path
    $bakName = "${base}_${ts}_${hash6}.bak"
    $bakPath = Join-Path $AmberDir $bakName
    Copy-Item -Path $Path -Destination $bakPath -Force
    Write-Log "已备份: $Path -> $bakPath"
}

function Invoke-Cleanup {
    $todayStr = Get-Date -Format 'yyyyMMdd'
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays).ToString('yyyyMMdd')

    try {
    # 1. 删除超过7天的非 major 备份（按文件名日期判断，不用 mtime）
    Get-ChildItem -Path $AmberDir -Filter '*.bak' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch '_major_' } |
        ForEach-Object {
            if ($_.Name -match '_(\d{8})-\d{6}_[a-f0-9]{6}\.bak$') {
                $bakDate = $Matches[1]
                if ([int]$bakDate -lt [int]$cutoffDate) {
                    Remove-Item $_.FullName -Force
                    Write-Log "清理-过期7天+: $($_.FullName)"
                }
            }
        }

    # 2. 同 basename + 同日期，只留时间戳最大的；跳过今天的备份
    $allBaks = Get-ChildItem -Path $AmberDir -Filter '*.bak' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch '_major_' } |
        ForEach-Object {
            if ($_.Name -match '^(.+?)_(\d{8})-(\d{6})_[a-f0-9]{6}\.bak$') {
                [PSCustomObject]@{
                    BaseName = $Matches[1]
                    DateStr  = $Matches[2]
                    TsStr    = $Matches[2] + $Matches[3]
                    FullName = $_.FullName
                }
            }
        } | Where-Object { $_.DateStr -ne $todayStr }

    if ($allBaks) {
        $allBaks | Group-Object -Property BaseName, DateStr |
            ForEach-Object {
                $sorted = $_.Group | Sort-Object TsStr -Descending
                $sorted | Select-Object -Skip 1 | ForEach-Object {
                    Remove-Item $_.FullName -Force
                    Write-Log "清理-同日去重: $($_.FullName)"
                }
            }
    }
    } catch {
        Write-Log "清理过程出错（非致命）: $_"
    }
}

# === 主流程 ===
Write-Log "=== 记忆琥珀备份开始 ==="

if (-not (Test-Path $WhitelistFile)) {
    Write-Log "错误：白名单文件不存在 $WhitelistFile"
    exit 1
}

# 白名单路径适配：如果白名单是 macOS 格式（/Users/xxx），尝试转换为当前平台
function Convert-WhitelistPath {
    param([string]$Line)
    # 跳过注释和空行
    $trimmed = ($Line -replace '#.*$', '').Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) { return $null }
    # macOS 路径 /Users/xxx -> 当前平台
    if ($trimmed -match '^/Users/([^/]+)(/.*)?$') {
        $userName = $Matches[1]
        $rest = $Matches[2]
        if ($IsMacOS -or $IsLinux) {
            return $Line  # macOS 原样
        } else {
            # Windows: /Users/xxx -> $env:USERPROFILE，路径分隔符转换
            $converted = $rest -replace '/', '\'
            return Join-Path $env:USERPROFILE $converted.Substring(1)
        }
    }
    # 已经是 Windows 格式或相对路径，原样返回
    return $trimmed
}

$backedUp = 0
$skipped  = 0
$missing  = 0

Get-Content $WhitelistFile -Encoding UTF8 | ForEach-Object {
    $path = Convert-WhitelistPath $_
    if ([string]::IsNullOrWhiteSpace($path)) { return }

    if (-not (Test-Path $path)) {
        Write-Log "警告：文件不存在 $path"
        $script:missing++
        return
    }

    try {
        if (Test-NeedBackup $path) {
            Invoke-Backup $path
            $script:backedUp++
        } else {
            Write-Log "跳过-内容未变: $path"
            $script:skipped++
        }
    } catch {
        Write-Log "错误：处理 $path 失败: $_"
        $script:missing++
    }
}

Invoke-Cleanup

Write-Log "完成：备份 $backedUp / 跳过 $skipped / 缺失 $missing"
Write-Log "=== 记忆琥珀备份结束 ==="

# 释放锁
if (Test-Path $LockFile) { Remove-Item $LockFile -Force -ErrorAction SilentlyContinue }
