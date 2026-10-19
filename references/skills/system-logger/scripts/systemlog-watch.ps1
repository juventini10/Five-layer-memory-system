# systemlog-watch.ps1 — 系统日志写时守护 (Windows / PowerShell 版 · 轮询快照)
# 等价于 macOS 版 systemlog_watch.sh（fswatch → 轮询快照比对）
# ─────────────────────────────────────────────────────────────
# 机制：每 IntervalSec 秒扫描 <MC>/工作日志/系统日志/系统日志_*.md
#       → 快照(路径→最后写入+大小)比对 → 有变化则防抖 2s 跑 systemlog_normalize_fix.py
#       （归一 emoji/描述式 ## 头 + 按 - **工具**： 字段重排归组）
# 引擎幂等：合规后不写盘 → 不产生新变化 → 不死循环（与 macOS 版同语义）。
# 塌缩绊线（2026-08-22 事故反哺的 Win 移植·简化版）：条目数较基线骤降>30%（基线>3）
#   = 疑似"整文件写回"覆盖 → ⛔不跑 normalize（防给塌缩版盖章）→ 存证 .collapse-* 侧车 + 报警。
#   与 macOS 差异（诚实声明）：Win 版无 git HEAD 自动恢复/无 checkpoint 提交
#   （前提=git 在 PATH + MC 为 git 仓，端用户机不保证）→ 只隔离报警，恢复走 git/人工。
# 路径判定：由脚本落点向上推导（scripts→system-logger→技能配置→MC），
#   ⛔不写死个人态——作者机/装机态/CI 沙盒三态同一逻辑成立。
# 可测性：支持环境变量重定向，CI/隔离测试用
#   SL_WATCH_DIR   监听目录（覆盖缺省推导值）
#   SL_ENGINE      引擎脚本路径（覆盖缺省=本脚本同目录 systemlog_normalize_fix.py）
#   SL_INTERVAL    轮询间隔秒（默认 15）
#   SL_ONCE        置任意值 = 只跑一轮就退出（功能测试用）
#   SL_MAXSEC      最长运行秒数（默认 0=永久；CI 里设上限防挂死）

[CmdletBinding()]
param()

# 故障对策：单轮异常绝不掀翻整个循环（同 amber-watch 加固语义）
$ErrorActionPreference = 'Continue'
# 忽略 CTRL+C 信号，别让控制台把它杀掉（S4U 任务上下文兜底，根治同 amber 故障因 A）
try { [Console]::TreatControlCAsInput = $true } catch { }

# ─── 路径解析（脚本落点向上推导 MC） ───
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
# <MC>/技能配置/system-logger/scripts → 上三级 = MC
$relUp = if ($IsMacOS -or $IsLinux) { '../../../' } else { '..\..\..\' }
$MC = (Resolve-Path (Join-Path $ScriptDir $relUp)).Path

$sep = if ($IsMacOS -or $IsLinux) { '工作日志/系统日志' } else { '工作日志\系统日志' }
$WatchDir = if ($env:SL_WATCH_DIR) { $env:SL_WATCH_DIR } else { Join-Path $MC $sep }
$Engine   = if ($env:SL_ENGINE) { $env:SL_ENGINE } else { Join-Path $ScriptDir 'systemlog_normalize_fix.py' }
$WatchLog = Join-Path $WatchDir '.watch-ps.log'
$HeartbeatFile = Join-Path $WatchDir '.watch-ps.heartbeat'

$IntervalSec = 15
if ($env:SL_INTERVAL) { $IntervalSec = [int]$env:SL_INTERVAL }
$RunOnce = [bool]$env:SL_ONCE
$MaxSec  = 0
if ($env:SL_MAXSEC) { $MaxSec = [int]$env:SL_MAXSEC }

if (-not (Test-Path $WatchDir)) { New-Item -ItemType Directory -Path $WatchDir -Force | Out-Null }

function Write-WatchLog {
    param([string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    try { Add-Content -Path $WatchLog -Value "[$ts] $Message" -Encoding UTF8 } catch { }
}

# ─── python 解析（Find-Python 规范·与包内 verify.ps1 同口径：⛔裸 python 会跳微软商店别名） ───
function Find-Python {
    foreach ($c in @('python3', 'python')) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -notlike '*WindowsApps*') { return $cmd.Source }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    return $null
}
$Python = Find-Python

function Get-SyslogFiles {
    # 监听对象=目录根下 系统日志_*.md（与 mac 版 case 过滤同口径）；⛔隐藏守护产物天然不在名单
    Get-ChildItem -Path $WatchDir -Filter '系统日志_*.md' -File -ErrorAction SilentlyContinue
}

function Get-Snapshot {
    $snap = @{}
    foreach ($f in (Get-SyslogFiles)) {
        $snap[$f.FullName] = "$($f.LastWriteTimeUtc.Ticks):$($f.Length)"
    }
    return $snap
}

function Get-ChangedKeys {
    param([hashtable]$Old, [hashtable]$New)
    # 首轮建基线不触发（防启动风暴）；例外：RunOnce 测试模式首轮视全部文件为变更
    #   ——引擎幂等（无变化不写盘），多跑一次零副作用，否则单轮模式永远测不到归一路径
    if ($null -eq $Old) { if ($RunOnce) { return @($New.Keys) } else { return @() } }
    $changed = @()
    foreach ($k in $New.Keys) {
        if (-not $Old.ContainsKey($k) -or $Old[$k] -ne $New[$k]) { $changed += $k }
    }
    return $changed
}

function Get-EntryCount {
    param([string]$Path)
    try { @(Get-Content $Path -Encoding UTF8 -ErrorAction Stop | Where-Object { $_ -match '^### ' }).Count }
    catch { 0 }
}

function Invoke-NormalizeOne {
    param([string]$File)
    $base = Split-Path $File -Leaf
    $st   = Join-Path $WatchDir (".watch_cnt_" + $base)
    $now  = Get-EntryCount $File
    $last = $null
    if (Test-Path $st) { $t = (Get-Content $st -Encoding UTF8 -ErrorAction SilentlyContinue | Select-Object -First 1); if ($t -match '^\d+$') { $last = [int]$t } }
    if ($null -eq $last) { $last = $now }   # 首见学习：无基线不判塌缩

    # 入线绊线：条目骤降>30%（基线>3）= 疑似整文件覆盖 → 拒跑 normalize·隔离存证
    if ($last -gt 3 -and $now -lt [math]::Floor($last * 0.7)) {
        $stamp = Get-Date -Format 'yyyyMMddHHmmss'
        Copy-Item $File (Join-Path $WatchDir ("$base.collapse-$stamp")) -ErrorAction SilentlyContinue
        Write-WatchLog "🚨 塌缩熔断(隔离报警·Win版无git自愈): $base 条目 $last→$now（降幅>30%）——已存证 .collapse-$stamp，⛔未跑 normalize（防盖章）·恢复走 git/人工"
        return
    }

    # 跑引擎（防抖 2s 后执行，同 mac 版 sleep 2 语义）
    Start-Sleep -Seconds 2
    if (-not (Test-Path $Engine)) { Write-WatchLog "🔴 引擎缺失: $Engine（⛔不静默——缺引擎=守护空转）"; return }
    if (-not $Python) { Write-WatchLog "🔴 python 未解析（PATH 无 python3/python/py）——本轮归一未执行"; return }
    try {
        & $Python $Engine $File *>> $WatchLog
    } catch {
        Write-WatchLog "引擎执行出错（非致命）: $base -> $_"
    }
    $post = Get-EntryCount $File
    # 出线绊线：normalize 写盘后骤降 = 引擎疑似退化 → 从引擎自留的最新 .bak- 回滚
    if ($now -gt 3 -and $post -lt [math]::Floor($now * 0.7)) {
        $bak = Get-ChildItem -Path $WatchDir -Filter "$base.bak-*" -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($bak) { Copy-Item $bak.FullName $File -Force }
        Write-WatchLog "🚨 出线绊线: normalize 后条目 $now→$post——已从 $($bak.Name) 回滚·引擎疑似退化待查"
        $post = Get-EntryCount $File
    }
    Set-Content -Path $st -Value $post -Encoding ascii
}

# ─── 主循环 ───
if (-not (Test-Path $Engine)) { Write-WatchLog "⚠️ 启动检查：引擎不在位 $Engine" }
Write-WatchLog "=== systemlog-watch 启动（轮询模式 interval=${IntervalSec}s dir=$WatchDir python=$Python）==="

$startTime = Get-Date
$prevSnap = $null

try {
    while ($true) {
        try {
            $snap = Get-Snapshot
            $changed = Get-ChangedKeys -Old $prevSnap -New $snap
            if ($changed.Count -gt 0) {
                $names = ($changed | ForEach-Object { Split-Path $_ -Leaf } | Select-Object -First 3) -join ', '
                Write-WatchLog "检测到 $($changed.Count) 个日志文件变化（例：$names），跑归一"
                foreach ($k in $changed) { Invoke-NormalizeOne $k }
            }
            $prevSnap = $snap
            Set-Content -Path $HeartbeatFile -Value (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -Encoding ascii
        } catch {
            Write-WatchLog "轮询循环出错（非致命，继续）: $_"
        }

        if ($RunOnce) { Write-WatchLog "SL_ONCE 已设置，跑完一轮退出"; break }
        if ($MaxSec -gt 0 -and ((Get-Date) - $startTime).TotalSeconds -ge $MaxSec) {
            Write-WatchLog "达到 SL_MAXSEC=$MaxSec，退出"; break
        }
        Start-Sleep -Seconds $IntervalSec
    }
} finally {
    Write-WatchLog "=== systemlog-watch 已停止 ==="
}
