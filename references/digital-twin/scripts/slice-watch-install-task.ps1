# slice-watch-install-task.ps1 — 注册 Windows Task Scheduler 分身同步周期守护（Q3路线C装机对等件·2026-10-19）
# 等价 macOS 侧 com.doenglingz.slice-watch.plist（执行体同一份平台中性 python·单一真源⛔ps1逻辑副本）
# ─────────────────────────────────────────────────────────────
# 加固模式镜像 systemlog-install-task.ps1（0xC000013A 对症三连：python 全路径/S4U/防重入）。
# 与 systemlog 差异：slice_watch/state_bus_sync 为**间隔执行型**（跑完即退·非常驻轮询），
#   故触发器=时间触发+RepetitionInterval 24h（⛔不用 RestartCount 常驻语义）。
# python 解析=win-ps1-python-resolution 真机验证 Find-Python（where.exe+正则+跳 WindowsApps 别名）。
# 可测性：SLICE_WATCH_MC / SLICE_WATCH_PY 环境变量覆盖（CI/沙箱用）。
# 卸载：slice-watch-install-task.ps1 -Uninstall（对齐 mac launchctl unload 语义）
[CmdletBinding()]
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'

$TaskName = 'DoenglingzSliceWatch'
$TaskDesc = '分身同步周期守护——刷新 state_bus.json 端账本（等价 mac launchd com.doenglingz.slice-watch）'

# 记忆共享中心根：env 优先，缺省=本脚本装机落点 <MC>/数字分身/scripts/ 上溯两级
$MC = $env:SLICE_WATCH_MC
if (-not $MC) { $MC = (Get-Item $PSScriptRoot).Parent.Parent.FullName }
$SliceWatch = Join-Path $MC '脚本中心\doenglingz_slice_watch.py'
$StateBus   = Join-Path $MC '数字分身\scripts\state_bus_sync.py'

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
$PyExe = $env:SLICE_WATCH_PY
if (-not $PyExe) { $PyExe = Find-Python }
if (-not $PyExe) {
    Write-Host "❌ 未解析到可用 python.exe（where.exe 三候选全空或均不可跑）——注册中止，⛔不静默假成功" -ForegroundColor Red
    exit 1
}
foreach ($s in @($SliceWatch, $StateBus)) {
    if (-not (Test-Path $s)) { Write-Host "❌ 执行体不存在: $s（确认装机落点/SLICE_WATCH_MC）" -ForegroundColor Red; exit 1 }
}

Write-Host "=== 分身同步周期守护 Task Scheduler 注册 ===" -ForegroundColor Cyan
Write-Host "任务名称: $TaskName"
Write-Host "python:   $PyExe"
Write-Host "执行体1:  $SliceWatch"
Write-Host "执行体2:  $StateBus --update"

# 双 Action：先切片守望、后端账本刷新（Task Scheduler 原生多动作·间隔型语义）
$action1 = New-ScheduledTaskAction -Execute $PyExe -Argument "`"$SliceWatch`""
$action2 = New-ScheduledTaskAction -Execute $PyExe -Argument "`"$StateBus`" --update"

# 触发：开机+登录即注册 + 每日 9:00 起每 24h 重复（等价 mac StartInterval 86400）
# Repetition 是 trigger 的 CIM 属性·文档正解直接赋 ISO8601 字符串（⛔ New-ScheduledTaskRepetitionTrigger 不存在·真机爆点已拆）
$daily = New-ScheduledTaskTrigger -Daily -At 9:00am
$daily.Repetition.Interval = 'PT24H'
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
    Register-ScheduledTask -TaskName $TaskName -Description $TaskDesc -Action @($action1,$action2) -Trigger $triggers -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "✅ 已注册: $TaskName" -ForegroundColor Green
    Start-ScheduledTask -TaskName $TaskName
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
    Write-Host "1. 状态: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
    Write-Host "2. 账本新鲜度: $MC\数字分身\state_bus.json 的 mtime 应 < 25h"
    Write-Host "3. L6 口径: python3 tsl_verify.py 应显示 ✅/🔴/🟡 而非 ⚪(本机未启用)"
    Write-Host "4. 卸载: powershell -File slice-watch-install-task.ps1 -Uninstall"
} catch {
    Write-Host "❌ 注册失败: $_" -ForegroundColor Red
    exit 1
}
