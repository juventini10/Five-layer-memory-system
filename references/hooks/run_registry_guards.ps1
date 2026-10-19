# run_registry_guards.ps1 —— Stop 钩子入口（Windows 承载·与 .sh 同语义）
# 解析守卫目录：env → runtime_paths.json 的 twin 键 → 脚本同目录；⛔静默失败。
$ErrorActionPreference = "Continue"
$gd = $env:BULUOTUO_GUARD_DIR
if (-not $gd -and $env:BULUOTUO_RUNTIME_PATHS -and (Test-Path $env:BULUOTUO_RUNTIME_PATHS)) {
  try {
    $d = Get-Content -Raw -LiteralPath $env:BULUOTUO_RUNTIME_PATHS -Encoding UTF8 | ConvertFrom-Json
    if ($d.twin) { $gd = Join-Path $d.twin "guards" }
  } catch { Write-Output "[WARN] runtime_paths 解析失败：$($_.Exception.Message)" }
}
if (-not $gd -or -not (Test-Path $gd)) {
  $gd = Join-Path $PSScriptRoot "digital-twin/guards"
  if (-not (Test-Path $gd)) { $gd = $PSScriptRoot }
}
if (-not (Test-Path $gd)) { Write-Output "[WARN] 守卫目录不存在：$gd（显形，⛔不静默退出）"; exit 0 }
$env:BULUOTUO_GUARD_DIR = $gd
$impl = Join-Path $gd "registry_guards.ps1"
if (-not (Test-Path $impl)) { Write-Output "[NOT-ADAPTED] registry_guards.ps1 缺失 → 回退 bash 承载"; & bash "$gd/registry_guards.sh"; exit $LASTEXITCODE }
& powershell -NoProfile -ExecutionPolicy Bypass -File "$impl" @args
exit $LASTEXITCODE
