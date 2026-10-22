# awaken-patrol-install-task.ps1 — 注册 Windows Task Scheduler 记忆健康自动巡检（8.4.0 Win对等件·2026-10-21）
# 等价 macOS 侧 com.buluotuo.awaken-patrol.plist（执行体同一份平台中性 python awaken_patrol.py·单一真源⛔ps1逻辑副本）
# ─────────────────────────────────────────────────────────────
# 加固模式镜像 slice-watch-install-task.ps1（0xC000013A 对症三连：python 全路径/S4U/防重入）。
# 间隔执行型（跑完即退·非常驻）：触发器=Daily + RepetitionInterval PT6H（等价 mac StartInterval 21600）。
# StartWhenAvailable：睡眠/关机错过的轮次在可用后补跑（笔记本场景·治 Repetition 漏跑）。
# python 解析=win-ps1-python-resolution 真机验证 Find-Python（where.exe+正则+跳 WindowsApps 别名）。
# 可测性：AWAKEN_PATROL_MC / AWAKEN_PATROL_PY 环境变量覆盖（CI/沙箱用）。
# 触达说明：Win 端非交互会话弹不出 toast——巡检告警落 %USERPROFILE%\buluotuo_bin\log\awaken_patrol_alerts.pending，
#   由唤醒轻量巡检（说"小美"）会话内转述（patrol.md §3/§4·设计决策a）。
# 卸载：awaken-patrol-install-task.ps1 -Uninstall（对齐 mac launchctl unload 语义）
[CmdletBinding()]
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$TaskName = 'BuluotuoAwakenPatrol'
$TaskDesc = '记忆健康自动巡检——快照滞后+蒸馏待办+触达留痕（等价 mac launchd com.buluotuo.awaken-patrol·每6小时）'

# 执行体定位：env 优先，缺省=本脚本装机落点 <MC>/技能配置/awaken-memory-system/scripts/ 同目录
$ScriptDir = $env:AWAKEN_PATROL_MC
if ($ScriptDir) { $ScriptDir = Join-Path $ScriptDir '技能配置\awaken-memory-system\scripts' }
else { $ScriptDir = $PSScriptRoot }
$PatrolPy = Join-Path $ScriptDir 'awaken_patrol.py'

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
        foreach ($m in [regex]::Matches($ln, '[A-Za-z]:\\.*?python\.exe')) {
          $p = $m.Value
          if ($p -match 'WindowsApps\\python') { continue }
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
$PyExe = $env:AWAKEN_PATROL_PY
if (-not $PyExe) { $PyExe = Find-Python }
if (-not $PyExe) {
    Write-Host "❌ 未解析到可用 python.exe（where.exe 三候选全空或均不可跑）——注册中止，⛔不静默假成功" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $PatrolPy)) { Write-Host "❌ 执行体不存在: $PatrolPy（确认装机落点/AWAKEN_PATROL_MC）" -ForegroundColor Red; exit 1 }

Write-Host "=== 记忆健康自动巡检 Task Scheduler 注册 ===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "python:   $PyExe"
Write-Host "执行体:   $PatrolPy"

$action = New-ScheduledTaskAction -Execute $PyExe -Argument "`"$PatrolPy`""

# 触发：开机+登录 + 每日 3:00 起每 6h 重复（等价 mac StartInterval 21600·凌晨低干扰时段起算）
# Repetition 是 trigger 的 CIM 属性·文档正解直接赋 ISO8601 字符串（⛔ New-ScheduledTaskRepetitionTrigger 不存在）
$daily = New-ScheduledTaskTrigger -Daily -At 3:00am
$daily.Repetition.Interval = 'PT6H'
$daily.Repetition.Duration = 'P3650D'
$triggers = @((New-ScheduledTaskTrigger -AtLogOn), (New-ScheduledTaskTrigger -AtStartup), $daily)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew

# S4U：不管是否登录都运行（脱离交互控制台·根治 CTRL+C 猝死系）
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
    # 实锤律：判"装好了"用权威状态源 Get-ScheduledTask.State + 日志产出反证，不用"注册命令没报错"外推
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = $task | Get-ScheduledTaskInfo
    Write-Host "当前状态: $($task.State)" -ForegroundColor Cyan
    Write-Host "上次运行结果: 0x$('{0:X}' -f $info.LastTaskResult)"
    $logPath = Join-Path $env:USERPROFILE 'buluotuo_bin\log\awaken_patrol.log'
    if (Test-Path $logPath) {
        Write-Host "✅ 巡检日志已产出: $logPath" -ForegroundColor Green
    } else {
        Write-Host "🟡 巡检日志尚未出现（首轮可能仍在跑/排队）——稍后复核 $logPath 与仪表盘巡检趋势行" -ForegroundColor Yellow
    }
    Write-Host "=== 验证方法 ===" -ForegroundColor Cyan
    Write-Host "1. 状态: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
    Write-Host "2. 日志: $logPath 应有四段留痕（[快照]/[蒸馏]/[触达]/[完成]）"
    Write-Host "3. 仪表盘: python3 awaken_health_dashboard.py 的「巡检趋势」应出真实数字（非降级文案）"
    Write-Host "4. 卸载: powershell -File awaken-patrol-install-task.ps1 -Uninstall"
} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    exit 1
}
