# distill-scheduler-install-task.ps1 — 注册 Windows Task Scheduler 蒸馏调度月拍守护（G2装机对等件·2026-10-21）
# 等价 macOS 侧 com.buluotuo.distill-scheduler.plist.template（执行体同一份平台中性 python·单一真源⛔ps1逻辑副本）
# ─────────────────────────────────────────────────────────────
# 加固模式镜像 slice-watch-install-task.ps1（0xC000013A 对症三连：python 全路径/S4U/防重入）。
# python 解析块=从 slice-watch 真机验证版 sed 原样抽取（零手抄零漂移·皮叔2026-10-21施工纪律）。
# 可测性：DISTILL_SCHED_MC / DISTILL_SCHED_PY 环境变量覆盖（CI/沙箱用）。
# 卸载：distill-scheduler-install-task.ps1 -Uninstall（对齐 mac launchctl unload 语义）
[CmdletBinding()]
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$TaskName = 'BuluotuoDistillScheduler'
$TaskDesc = '蒸馏调度月拍守护——每日幂等检查账行并刷新待做蒸馏区（等价 mac launchd com.buluotuo.distill-scheduler）'

# 记忆共享中心根：env 优先，缺省=本脚本装机落点 <MC>/数字分身/scripts/ 上溯两级
$MC = $env:DISTILL_SCHED_MC
if (-not $MC) { $MC = (Get-Item $PSScriptRoot).Parent.Parent.FullName }
$Scheduler = Join-Path $MC '脚本中心\记忆蒸馏\distillation_scheduler.py'

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


# 解析真实 python.exe 绝对路径（跳过 Store 应用执行别名·抗 Get-Command 畸形前缀·真机验证规范函数）
function Find-Python {
  $found = $null
  foreach ($cand in @("python", "python3", "py")) {
    try {
      $raw = @(& where.exe $cand 2>$null)
      foreach ($ln in $raw) {
        foreach ($m in [regex]::Matches($ln, '[A-Za-z]:\.*?python\.exe')) {
          $p = $m.Value
          if ($p -match 'WindowsApps\python') { continue }
          if (Test-Path $p) {
            $null = & $p --version 2>$null
            if ($LASTEXITCODE -eq 0) { $found = $p; break }
          }
        }
        if ($found) { break }
      }
      if ($found) { break }
    } catch {}
  }
  return $found
}
$PyExe = $env:DISTILL_SCHED_PY
if (-not $PyExe) { $PyExe = Find-Python }
if (-not $PyExe) {
    Write-Host "❌ 未解析到可用 python.exe（where.exe 三候选全空或均不可跑）——注册中止，⛔不静默假成功" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $Scheduler)) { Write-Host "❌ 执行体不存在: $Scheduler（确认装机落点/DISTILL_SCHED_MC）" -ForegroundColor Red; exit 1 }

Write-Host "=== 蒸馏调度月拍守护 Task Scheduler 注册 ===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "python:   $PyExe"
Write-Host "执行体:   $Scheduler"

$action = New-ScheduledTaskAction -Execute $PyExe -Argument "`"$Scheduler`""

# 触发：开机+登录即注册 + 每日 8:30 起每 24h 重复（等价 mac StartInterval 86400；调度器幂等静默）
$daily = New-ScheduledTaskTrigger -Daily -At 8:30am
$daily.Repetition.Interval = 'PT24H'
$daily.Repetition.Duration = 'P3650D'
$triggers = @((New-ScheduledTaskTrigger -AtLogOn), (New-ScheduledTaskTrigger -AtStartup), $daily)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "已存在同名任务，先删旧（幂等重装）" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
try {
    Register-ScheduledTask -TaskName $TaskName -Description $TaskDesc -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "✅ 已注册: $TaskName" -ForegroundColor Green
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = $task | Get-ScheduledTaskInfo
    Write-Host "当前状态: $($task.State)" -ForegroundColor Cyan
    Write-Host "上次运行结果: 0x$('{0:X}' -f $info.LastTaskResult)"
    if ("$($task.State)" -ne 'Running') {
        Write-Host "🟡 已注册但 state=$($task.State)——沙箱/受限环境可复核 Get-ScheduledTask，不谎称绿"
    }
    Write-Host "=== 验证方法 ===" -ForegroundColor Cyan
    Write-Host "1. 状态: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
    Write-Host "2. 待做区新鲜度: $MC\记忆蒸馏\蒸馏中心.md 标记区 mtime 应 < 25h"
    Write-Host "3. 卸载: powershell -File distill-scheduler-install-task.ps1 -Uninstall"
} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    exit 1
}
