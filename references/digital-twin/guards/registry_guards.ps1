# registry_guards.ps1 —— Stop 钩子·守卫族自动体检（Windows / PowerShell 等价实现）
# 与 registry_guards.sh 同源语义（2026-10-11 批次6·端用户 Windows 补充单反哺）：
#   ①文件系统=唯一真相源：扫 GUARD_DIR 下全部 *guard.*（sh/ps1），⛔手工名单
#   ②审计类守卫（件内声明 AUDIT_CLASS=1）跳过但必须显形汇总，⛔沉默失败
#   ③单守卫超时预算（默认 20s），超时显形不静默
#   ④Windows 差异：只有 .sh 的守卫——有 bash 则跑，无 bash 则输出 [NOT-ADAPTED]
#     显形登记（这是"装了≠活了"的可观测化，⛔不静默 continue——静默正是本守卫族
#     2026-08-11 根治过的那类病）。
param([switch]$report)
$ErrorActionPreference = "Continue"
$GUARD_DIR = if ($env:BULUOTUO_GUARD_DIR) { $env:BULUOTUO_GUARD_DIR } else { $PSScriptRoot }
$timeoutS = [int]($(if ($env:GUARD_TIMEOUT) { $env:GUARD_TIMEOUT } else { 20 }))
$alarms = @(); $skipped = @(); $notad = @(); $lines = @()
$bash = $null
if (-not (Get-Command bash -ErrorAction SilentlyContinue)) { $bash = $null } else { $bash = "bash" }
$guards = Get-ChildItem -Path $GUARD_DIR -Filter "*guard.*" -File |
          Where-Object { ($_.Name -like "*guard.sh" -or $_.Name -like "*guard.ps1") -and $_.Name -notlike "*.bak*" } |
          Sort-Object Name
foreach ($g in $guards) {
  $name = $g.Name
  $txt = Get-Content -Raw -LiteralPath $g.FullName -Encoding UTF8
  if ($txt -match "AUDIT_CLASS=1") { $skipped += $name; continue }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  if ($g.Extension -eq ".ps1") {
    $psi.FileName = "powershell"; $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$($g.FullName)`" --check"
  } elseif ($bash) {
    $psi.FileName = $bash; $psi.Arguments = "`"$($g.FullName)`" --check"
  } else { $notad += $name; continue }
  $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  try {
    $p = [System.Diagnostics.Process]::Start($psi)
    if (-not $p.WaitForExit($timeoutS * 1000)) {
      try { $p.Kill() } catch {}
      $alarms += "$name 超时>${timeoutS}s"; continue
    }
    $outp = $p.StandardOutput.ReadToEnd()
    if ($outp -match '"alarm"\s*:\s*true' -or $outp -match "alarm=true" -or $p.ExitCode -ne 0) {
      $alarms += $name
      if ($report) { $lines += "---- $name ----"; $lines += $outp }
    }
  } catch { $alarms += "$name 执行异常:$($_.Exception.Message)" }
}
if ($alarms.Count -eq 0 -and $notad.Count -eq 0) {
  Write-Output "✅ registry_guards: $($guards.Count) 守卫全过$(if($skipped.Count){「审计类 $($skipped -join ',') 由定时任务承载」})"
} else {
  if ($alarms.Count) { Write-Output ("⚠️ registry_guards alarm: " + ($alarms -join " | ")) }
  if (-not $report -and $alarms.Count) { Write-Output "（详细：powershell -File registry_guards.ps1 -report）" }
  foreach ($n in $notad) { Write-Output "[NOT-ADAPTED] $n —— Windows 无 bash 承载，该守卫未运行（已显形在册，⛔非静默跳过）" }
  foreach ($n in $skipped) { Write-Output "[AUDIT-SKIPPED] $n —— 审计类，由定时任务承载" }
}
