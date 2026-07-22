# =============================================================================
# rollback.ps1 — 布洛陀 1.10 · 系统文件回滚脚本（Windows / PowerShell 等价实现）
# -----------------------------------------------------------------------------
# 用途：从记忆琥珀备份中恢复系统核心文件（SOUL/IDENTITY/USER/MEMORY）到
#       WorkBuddy 平台目录 ~/.workbuddy/（系统文件专属落点）。
#
# 用法：
#   .\rollback.ps1                          # 列出可用备份
#   .\rollback.ps1 -Preview                 # 预览最近一次备份的文件差异
#   .\rollback.ps1 -Restore                 # 恢复最近一次备份
#   .\rollback.ps1 -Restore 2026-07-14_12   # 恢复指定时间戳的备份
#
# 环境变量：
#   $MEMORY_CENTER = 你的记忆共享中心（归档根）路径
#
# ⚠️ 本文件已用 pwsh（macOS 本机）做语法与逻辑验证；原生 Windows 行为以 pwsh 跨平台兼容为准。
# =============================================================================

param(
  [string]$Preview,
  [string]$Restore
)

$ErrorActionPreference = 'SilentlyContinue'

$MEMORY_CENTER = $env:MEMORY_CENTER
if (-not $MEMORY_CENTER) {
  Write-Host "❌ 未设置 MEMORY_CENTER"
  Write-Host "   运行前设置：\$env:MEMORY_CENTER = '你的记忆共享中心路径'"
  exit 1
}
$BACKUP_DIR = Join-Path $MEMORY_CENTER "记忆琥珀"
$WB = Join-Path $HOME ".workbuddy"
$CORE_FILES = @("SOUL.md","IDENTITY.md","USER.md","MEMORY.md")

function Check-Path {
  if (-not (Test-Path $BACKUP_DIR -PathType Container)) {
    Write-Host "❌ 备份目录不存在：$BACKUP_DIR"
    Write-Host "   你还没有运行过升级备份，或者记忆共享中心路径不对"
    exit 1
  }
}

function List-Backups {
  Check-Path
  Write-Host "📦 可用备份："
  Write-Host ""
  $count = 0
  $dirs = Get-ChildItem $BACKUP_DIR -Directory -Filter "升级备份_*"
  foreach ($d in $dirs) {
    $ts = $d.Name -replace "升级备份_", ""
    $files = 0
    foreach ($f in $CORE_FILES) { if (Test-Path (Join-Path $d.FullName "$f.bak")) { $files++ } }
    Write-Host "  🕐 $ts  →  $files/4 个系统文件已备份"
    $count++
  }
  if ($count -eq 0) { Write-Host "  (无备份记录)" }
}

function Get-RestoreDir([string]$ts) {
  if ($ts) { return Join-Path $BACKUP_DIR "升级备份_$ts" }
  $latest = Get-ChildItem $BACKUP_DIR -Directory -Filter "升级备份_*" | Sort-Object Name -Descending | Select-Object -First 1
  if ($latest) { return $latest.FullName } else { return $null }
}

function Preview-Diff([string]$ts) {
  Check-Path
  $rd = Get-RestoreDir $ts
  if (-not $rd) { Write-Host "❌ 备份不存在"; List-Backups; exit 1 }
  $resolvedTs = (Split-Path $rd -Leaf) -replace "升级备份_", ""
  Write-Host "🔍 预览备份：$resolvedTs"
  Write-Host ""
  foreach ($file in $CORE_FILES) {
    $bak = Join-Path $rd "$file.bak"
    $current = Join-Path $WB $file
    if ((Test-Path $bak) -and (Test-Path $current)) {
      Write-Host "─── $file ───"
      $diff = Compare-Object (Get-Content $bak -Encoding UTF8) (Get-Content $current -Encoding UTF8)
      if ($diff) { $diff | ForEach-Object { Write-Host "  $($_.SideIndicator) $($_.InputObject)" } }
      else { Write-Host "  （无差异）" }
      Write-Host ""
    } elseif (Test-Path $bak) {
      Write-Host "⚠️  $file：备份存在但当前文件不存在（可能已删除）"
      Write-Host ""
    } else {
      Write-Host "⚠️  $file：备份不存在"
      Write-Host ""
    }
  }
}

function Do-Restore([string]$ts) {
  Check-Path
  $rd = Get-RestoreDir $ts
  if (-not $rd) { Write-Host "❌ 备份不存在"; List-Backups; exit 1 }
  $resolvedTs = (Split-Path $rd -Leaf) -replace "升级备份_", ""
  Write-Host "🔄 正在回滚到备份：$resolvedTs"
  Write-Host ""
  $ok = 0; $fail = 0
  foreach ($file in $CORE_FILES) {
    $bak = Join-Path $rd "$file.bak"
    $target = Join-Path $WB $file
    if (Test-Path $bak) {
      if (Test-Path $target) { Copy-Item $target (Join-Path $BACKUP_DIR "回滚前_${ts}_$file") -Force }
      Copy-Item $bak $target -Force
      Write-Host "  ✅ $file → 已恢复（当前版本已备份到 回滚前_${ts}_$file）"
      $ok++
    } else {
      Write-Host "  ⚠️  $file → 备份文件不存在，跳过"
      $fail++
    }
  }
  Write-Host ""
  Write-Host "─────────────────────────────"
  Write-Host "✅ 回滚完成：$ok/4 个文件已恢复，$fail 个跳过"
  if ($fail -gt 0) { Write-Host "⚠️ 部分文件未恢复，可能不完整" }
  else { Write-Host "🎉 你的系统文件已回滚到升级前的状态" }
  Write-Host ""
  Write-Host "💡 运行后建议：说'我美吗'重新唤醒记忆系统"
}

# ── 入口 ──
if ($Preview -ne "") { Preview-Diff $Preview }
elseif ($Restore -ne "") { Do-Restore $Restore }
else { List-Backups }
