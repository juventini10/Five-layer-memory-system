# restore-my-skills.ps1
# ─────────────────────────────────────────────────────────────
# Skill 恢复脚本（Windows 版 · 目录级联接/符号链接模式 · 跨平台通用）
# 对应 macOS / Linux 版：restore-my-skills.sh
#
# 适用平台：Windows 10+（默认用 Junction，普通用户即可，无需开发者模式/管理员）
# 不适用：macOS / Linux（请用 restore-my-skills.sh）
#
# 用法：
#   .\restore-my-skills.ps1
#       # 默认：权威源=本脚本目录；WB=$env:USERPROFILE\.workbuddy\skills
#   .\restore-my-skills.ps1 -AuthorityDir X -WorkBuddyDir Y -TraeDir Z
# ─────────────────────────────────────────────────────────────
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$AuthorityDir = $PSScriptRoot,
    [Parameter(Mandatory = $false)][string]$WorkBuddyDir = "$env:USERPROFILE\.workbuddy\skills",
    [Parameter(Mandatory = $false)][string]$TraeDir = "$env:USERPROFILE\.trae-cn\skills"
)

# 平台守卫：非 Windows 直接跳过（防误用于 macOS/Linux）
if ($env:OS -notlike "*Windows*") {
    Write-Warning "本脚本仅适用于 Windows。当前环境非 Windows，已跳过执行。"
    exit 0
}

$SKILLS = @("daily-buddy", "awaken-memory-system", "reading-assistant", "system-logger", "triwich", "growth-box", "meta-aletheia", "shall-we-talk", "skill-lookup")

function New-SkillLink {
    param([string]$SkillName, [string]$Platform, [string]$TargetDir)
    $src = Join-Path $AuthorityDir $SkillName
    $dst = Join-Path $TargetDir $SkillName

    if (-not (Test-Path $src -PathType Container)) {
        Write-Host "❌ $SkillName → $Platform 权威源不存在: $src"
        return $false
    }

    if (Test-Path $dst) {
        $item = Get-Item $dst
        $isLink = $item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
        if ($isLink) {
            $current = $item.Target
            if ($current -eq $src) {
                Write-Host "✅ $SkillName → $Platform 已是目录级联接"
                return $true
            }
            Remove-Item $dst -Force
        }
        else {
            Remove-Item $dst -Recurse -Force
        }
    }

    try {
        # 默认 Junction（普通用户可建，同盘本地适用）；失败回退 SymbolicLink
        New-Item -ItemType Junction -Path $dst -Target $src -ErrorAction Stop | Out-Null
        Write-Host "✅ $SkillName → $Platform 目录级联接(Junction)已创建"
    }
    catch {
        try {
            New-Item -ItemType SymbolicLink -Path $dst -Target $src -ErrorAction Stop | Out-Null
            Write-Host "✅ $SkillName → $Platform 目录级符号链接已创建"
        }
        catch {
            Write-Host "❌ $SkillName → $Platform 创建链接失败（可能需开发者模式或管理员）: $_"
            return $false
        }
    }
    return $true
}

Write-Host "📦 Skill 恢复脚本（Windows 目录级联接模式）"
Write-Host "   权威源: $AuthorityDir"
Write-Host "   WB目录: $WorkBuddyDir"
Write-Host ""

# 清理历史死链接（深度模式）
Write-Host "🧹 清理历史死链接..."
$deadDirs = @($WorkBuddyDir)
if ($TraeDir) { $deadDirs += $TraeDir }
foreach ($dir in $deadDirs) {
    $dead = Join-Path $dir "深度模式"
    if (Test-Path $dead) {
        $item = Get-Item $dead
        $isLink = $item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
        if ($isLink) {
            $target = $item.Target
            if (-not (Test-Path $target -PathType Container)) {
                Remove-Item $dead -Force
                Write-Host "   ✓ 已删除死链接：$dead (目标: $target)"
            }
        }
    }
}

# 检测沙箱路径软链接（/sessions/{id}/...）
Write-Host "🔍 检测沙箱路径软链接..."
$scanDirs = @($WorkBuddyDir)
if ($TraeDir) { $scanDirs += $TraeDir }
foreach ($dir in $scanDirs) {
    if (-not (Test-Path $dir)) { continue }
    Get-ChildItem $dir -Directory | ForEach-Object {
        $item = $_
        $isLink = $item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
        if ($isLink) {
            $target = $item.Target
            if ($target -like "/sessions/*" -or $target -like "*/sessions/*") {
                $skillName = $item.Name
                Remove-Item $item.FullName -Force
                $src = Join-Path $AuthorityDir $skillName
                if (Test-Path $src -PathType Container) {
                    try {
                        New-Item -ItemType Junction -Path $item.FullName -Target $src -ErrorAction Stop | Out-Null
                        Write-Host "   ✓ 修复沙箱链接：$skillName → 真实本地路径"
                    }
                    catch {
                        New-Item -ItemType SymbolicLink -Path $item.FullName -Target $src -ErrorAction Stop | Out-Null
                        Write-Host "   ✓ 修复沙箱链接：$skillName → 真实本地路径(符号链接)"
                    }
                }
                else {
                    Write-Host "   ⚠️ $skillName 权威源不存在，跳过"
                }
            }
        }
    }
}

Write-Host ""
$OK = 0
$FAIL = 0
foreach ($skillName in $SKILLS) {
    if (New-SkillLink $skillName "workbuddy" $WorkBuddyDir) { $OK++ } else { $FAIL++ }
    if ($TraeDir) {
        if (New-SkillLink $skillName "trae" $TraeDir) { $OK++ } else { $FAIL++ }
    }
}

Write-Host ""
Write-Host "─────────────────────────────"
Write-Host "✅ 完成：$OK 个成功，$FAIL 个失败"
if ($FAIL -gt 0) { Write-Host "⚠️ 失败：$FAIL 个" }
Write-Host "💡 目录级联接：权威源任何文件更新后自动同步"
