# amber-pin.ps1 — 手动标记"重要·永久"备份（人工指定，永不被 cleanup 删）
# 设计：重要=价值判断，只能人指定，脚本不自动判定。
#   pin  = 把某文件当前最新的普通备份，复制一份为 _major_keep 版（永久保留）
#   复制而非重命名：普通备份仍走 7天/同日清理，major 版独立永久
#   命名含 _major_ 子串，精确匹配 amber-backup.ps1 清理的 -notmatch '_major_' 排除
# 用法：
#   amber-pin.ps1 <关键词>        标记：匹配琥珀库中含关键词的最新普通备份为 major
#   amber-pin.ps1 --list          列出当前所有 major 永久备份
#   amber-pin.ps1 --unpin <名字>  取消某 major 备份的永久标记（删除该 major 副本）
$ErrorActionPreference = 'Continue'

# === 路径配置（对齐 amber-backup.ps1：Win 用 $env:USERPROFILE + [记忆共享中心]） ===
$HomeDir = $env:USERPROFILE
if (-not $HomeDir) { $HomeDir = $HOME }
$MC = $env:AMBER_MC
if (-not $MC) { $MC = Join-Path $HomeDir '[记忆共享中心]' }
$AmberDir = Join-Path $MC '记忆琥珀'

function Show-Usage {
    Write-Host "amber-pin.ps1 — 标记\"重要·永久\"备份（人工指定，永不被 cleanup 删）"
    Write-Host "用法："
    Write-Host "  amber-pin.ps1 <关键词>       标记：含关键词的最新普通备份为 major（永久保留）"
    Write-Host "  amber-pin.ps1 --list         列出所有 major 永久备份"
    Write-Host "  amber-pin.ps1 --unpin <名字> 取消永久标记（删 major 副本，原备份不动）"
    exit 0
}
if ($args.Count -eq 0) { Show-Usage }

switch ($args[0]) {
    '--list' {
        Write-Host "=== 当前 major 永久备份 ==="
        $found = Get-ChildItem -Path $AmberDir -Filter '*_major_*.bak' -File -ErrorAction SilentlyContinue | Sort-Object Name
        if (-not $found) { Write-Host "（无。用 amber-pin.ps1 <关键词> 标记）" }
        else { $found | ForEach-Object { Write-Host $_.Name } }
    }
    '--unpin' {
        if ($args.Count -lt 2) { Write-Host "❌ 用法: amber-pin.ps1 --unpin <major备份名>"; exit 1 }
        $t = Get-ChildItem -Path $AmberDir -Filter "*$($args[1])*_major_*.bak" -File -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $t) { Write-Host "❌ 没找到匹配 '$($args[1])' 的 major 备份"; exit 1 }
        Remove-Item $t.FullName -Force
        Write-Host "✅ 已取消永久标记（删除 major 副本）: $($t.Name)"
        Write-Host "   注：原普通备份不受影响，仍按正常规则清理"
    }
    default {
        $kw = $args[0]
        $latest = Get-ChildItem -Path $AmberDir -Filter "*$kw*.bak" -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch '_major_' } | Sort-Object Name | Select-Object -Last 1
        if (-not $latest) {
            Write-Host "❌ 琥珀库里没找到含 '$kw' 的普通备份"
            Write-Host "   提示：先确认该文件在白名单里、且已被备份过（改动一次会自动备份）"
            exit 1
        }
        $bn = $latest.Name
        $majorName = ($bn -replace '\.bak$','') + '_major_keep.bak'
        $majorPath = Join-Path $AmberDir $majorName
        if (Test-Path $majorPath) {
            Write-Host "🟡 已存在该备份的 major 版，无需重复标记: $majorName"; exit 0
        }
        Copy-Item $latest.FullName $majorPath -Force
        Write-Host "✅ 已标记为重要·永久（永不被清理）"
        Write-Host "   源: $bn"
        Write-Host "   major: $majorName"
    }
}
