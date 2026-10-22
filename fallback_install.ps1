# ===================================================================
# fallback_install.ps1 - Buluotuo Windows install fallback (WorkBuddy platform)
# Launched by 安装兜底.bat. Mechanical install + verify only; quiz/guided flow stays in AI chat.
# Keep this file UTF-8 WITH BOM: PS 5.1 decodes no-BOM as ANSI, Chinese strings break.
# ===================================================================
try { Unblock-File -LiteralPath $PSCommandPath -ErrorAction SilentlyContinue } catch {}
$ErrorActionPreference = 'Continue'
$pkgRoot = $PSScriptRoot

Write-Host '======================================================='
Write-Host ' 布洛陀安装兜底（WorkBuddy 端·机械安装段）'
Write-Host ' 本脚本只落机械件。答题与引导流程请在安装完成后回 AI 对话窗继续。'
Write-Host '======================================================='

# [1/3] 记忆共享中心路径（回车=默认）
$mc = Join-Path $env:USERPROFILE '个人AI档案'
$in = Read-Host ('记忆共享中心路径（回车=默认 ' + $mc + '）')
if ($in -and $in.Trim()) { $mc = $in.Trim() }
if (-not (Test-Path $mc)) { New-Item -ItemType Directory -Path $mc -Force | Out-Null }

# [1.5] 写前探测硬闸（2026-10-21·Win安全策略拦截案·与 install_scripts.py 的 _mc_write_probe 同语义）
$probeDir = Join-Path $mc '.install\.probe-tmp'
try {
  New-Item -ItemType Directory -Path $probeDir -Force -ErrorAction Stop | Out-Null
  Set-Content -LiteralPath (Join-Path $probeDir 'p.tmp') -Value 'probe' -ErrorAction Stop
  Remove-Item -LiteralPath $probeDir -Recurse -Force -ErrorAction Stop   # ⛔只删探针自身，.install 里用户的历史 step 标记不许碰
} catch {
  Write-Host '[FAIL] 写前探测被拦：你的安全策略阻止程序写入' $mc
  Write-Host ('  原始错误: ' + $_.Exception.Message)
  Write-Host '  最常见来源：Windows Defender「受控文件夹访问」或杀软勒索防护对批量脚本写入的误拦。'
  Write-Host '  放行：设置→病毒和威胁防护→管理受控文件夹访问→添加允许应用(python.exe)，或把该目录移出保护。'
  Write-Host '  替代：先装默认位（用户目录下个人AI档案）跑通全链再迁移；E/D 盘安装必须先过本探测。'
  Write-Host '  之前装到一半失败过不用返工：放行后重跑本脚本或回 AI 对话窗走修复模式即可。'
  Read-Host '按回车关闭窗口'
  exit 2
}
Write-Host '  写前探测通过：目标目录允许程序写入。'

# [2/3] Python 解释器探测（复用 win-ps1-python-resolution 真机 Find-Python 模式）
Write-Host '[1/3] 探测 Python 解释器...'
$cands = @()
$cands += (Get-ChildItem (Join-Path $env:USERPROFILE '.workbuddy\binaries\python\versions\*\python.exe') -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
foreach ($name in @('python', 'python3', 'py')) {
    $w = (& where.exe $name 2>$null)
    foreach ($p in $w) { if ($p) { $cands += $p.Trim() } }
}
$py = $null
foreach ($p in $cands) {
    if (-not $p -or -not (Test-Path $p)) { continue }
    if ($p -match 'WindowsApps\\python') { continue }   # 微软商店执行别名·裸调会跳商店（T2 实测：单反斜杠=坏正则，别名无牙跳过——runner 逮到）
    & $p --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $p; break }
}
if (-not $py) {
    Write-Host '[FAIL] 未找到可用 Python 解释器（请先安装 Python 或 WorkBuddy 再重试）'
    Read-Host '按回车关闭窗口'
    exit 1
}
Write-Host ('  使用解释器: ' + $py)

# [3/3] 机械安装 + 自检（只调用包根脚本，不复制其逻辑）
Write-Host '[2/3] 执行机械安装（install_scripts.py --platform workbuddy）...'
& $py (Join-Path $pkgRoot 'install_scripts.py') $mc --platform workbuddy
if ($LASTEXITCODE -ne 0) {
    Write-Host ('[FAIL] 机械安装失败 rc=' + $LASTEXITCODE + '，请保留本行截图反馈，先别关窗')
    Read-Host '按回车关闭窗口'
    exit $LASTEXITCODE
}
# [2.5] Skill 面程序化部署（2026-10-22 R9 补腿：此腿=INSTALL 步骤6 的机械动作·不依赖答题·
#       漏调则兜底用户恒缺 10 Skill——凡不依赖用户输入的机械步骤必须纳入兜底范围）
Write-Host '[2.5] Skill 面落位（install_scripts.py --deploy-skills）...'
& $py (Join-Path $pkgRoot 'install_scripts.py') --platform workbuddy --deploy-skills $mc
if ($LASTEXITCODE -ne 0) {
    Write-Host ('[FAIL] Skill 落位失败 rc=' + $LASTEXITCODE + '，请保留本行截图反馈，先别关窗')
    Read-Host '按回车关闭窗口'
    exit $LASTEXITCODE
}
Write-Host '[3/3] 执行装后自检（verify.ps1）...'
$env:MEMORY_CENTER = $mc   # 2026-10-21 runner四测逮到的真缺陷：不传则 verify 默认 ~/记忆共享中心，全新Win机整链假红
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pkgRoot 'verify.ps1')
$rc = $LASTEXITCODE
if ($rc -eq 0) {
    Write-Host '[OK] 机械安装段完成（若上方出现待办行=答题段未跑非故障，回 AI 对话窗继续引导流程后重跑即消）。'
} else {
    Write-Host ('[WARN] 自检未全绿 rc=' + $rc + '，上方红绿明细是结果的一部分，请先拍照反馈再关窗')
}
Read-Host '按回车关闭窗口'
exit $rc
