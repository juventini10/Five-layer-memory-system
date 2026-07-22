# amber-install.ps1 — 记忆琥珀 Windows 安装分发器（单一入口）
# ─────────────────────────────────────────────────────────────
# 目标：所有 Windows 用户都能装成功——不管有没有管理员权限。
#   有管理员权限 + 有 nssm  → NSSM Service（首选，最稳，与 macOS launchd 对称）
#   否则                    → Task Scheduler 加固版（免提权回退，S4U+完整路径pwsh+双触发）
# 两条路跑的都是同一个 amber-watch.ps1（轮询），只是"谁来托管"不同。
# ─────────────────────────────────────────────────────────────
# 环境变量：AMBER_MC 覆盖记忆中心根；AMBER_FORCE=task 可强制走 Task 回退（测试用）

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path $PSCommandPath -Parent

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# nssm 是否可用（AMBER_NSSM / engine\nssm\nssm.exe / PATH）
$HomeDir = $env:USERPROFILE; if (-not $HomeDir) { $HomeDir = $HOME }
$MC = $env:AMBER_MC; if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }
$bundledNssm = Join-Path $MC '记忆琥珀\engine\nssm\nssm.exe'
$hasNssm = ($env:AMBER_NSSM -and (Test-Path $env:AMBER_NSSM)) -or `
           (Test-Path $bundledNssm) -or `
           ($null -ne (Get-Command nssm -ErrorAction SilentlyContinue)) -or `
           ($null -ne (Get-Command nssm.exe -ErrorAction SilentlyContinue))

Write-Host "=== 记忆琥珀 Windows 安装分发 ===" -ForegroundColor Cyan
Write-Host "管理员权限: $isAdmin   nssm 可用: $hasNssm   强制回退: $($env:AMBER_FORCE)"
Write-Host ""

if ($env:AMBER_FORCE -ne 'task' -and $isAdmin -and $hasNssm) {
    Write-Host "→ 走首选路径：NSSM Service（SCM 托管，最稳）" -ForegroundColor Green
    & (Join-Path $ScriptDir 'amber-install-service.ps1')
    exit $LASTEXITCODE
} else {
    $reason = if ($env:AMBER_FORCE -eq 'task') { 'AMBER_FORCE=task 指定' }
              elseif (-not $isAdmin) { '无管理员权限' }
              else { '未找到 nssm' }
    Write-Host "→ 走回退路径：Task Scheduler 加固版（原因：$reason）" -ForegroundColor Yellow
    Write-Host "  说明：回退版免提权也能装；若想要最稳的 SCM 托管，请以管理员身份 + 放置 nssm.exe 后重装。" -ForegroundColor DarkGray
    & (Join-Path $ScriptDir 'amber-install-task.ps1')
    exit $LASTEXITCODE
}
