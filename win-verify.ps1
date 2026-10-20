# ============================================================
# win-verify.ps1 — 布洛陀·全平台安装包 v2.0 Windows 真机 harness (windows-latest)
# 母本: v1.7.2 win-verify.ps1（2026-09-23 E2 派生·derive_win_harness_v2.py 机械改造，⛔手抄双本账）
# 正例 T1-T18: 包内 Windows 资产真实可用性 + v2 平台矩阵（T17/T18=capability 驱动 dry-run/fail-loud）
# 反例 V1-V15 : 断言"应有的行为"，未修则 FAIL 检出
# v2 差异: Skill 名单动态枚举(⛔硬编码) / INSTALL.md 缺失时 V2/V3/V6 显式 SKIP（F 阶段补齐后自动生效）
# 注意: 本文件必须 UTF-8 with BOM（PS5.1 中文兼容）
# ============================================================
$ErrorActionPreference = "Continue"
$PASS = 0; $FAIL = 0
function ok([string]$m) { Write-Host "  [PASS] $m" -ForegroundColor Green; $script:PASS++ }
function no([string]$m) { Write-Host "  [FAIL] $m" -ForegroundColor Red; $script:FAIL++ }
function info([string]$m) { Write-Host "  [i] $m" -ForegroundColor Cyan }
function Clear-Env([string]$n) { [Environment]::SetEnvironmentVariable($n, $null) }

$PKG = $PSScriptRoot
# 子进程用哪个 PowerShell.exe：Windows 上 powershell.exe(5.1) 最贴近端用户实况，
# 缺失时回退 pwsh（便于在非 Windows 开发机上冒烟自测）
$PSH = (Get-Command powershell -ErrorAction SilentlyContinue).Source
if (-not $PSH) { $PSH = (Get-Command pwsh -ErrorAction SilentlyContinue).Source }
$SB = Join-Path $env:RUNNER_TEMP "blt-sandbox"
if (-not $env:RUNNER_TEMP) { $SB = Join-Path ([System.IO.Path]::GetTempPath()) "blt-sandbox" }
$MC = Join-Path $SB "mc"
$HOME_SIM = Join-Path $SB "home"
$AMBER = Join-Path $MC "记忆琥珀"
# 全局：禁止子进程在包内写 .pyc（否则污染被测包 & V6 计数失真）
$env:PYTHONPYCACHEPREFIX = Join-Path $SB "pycache"
New-Item -ItemType Directory -Path $env:PYTHONPYCACHEPREFIX -Force -ErrorAction SilentlyContinue | Out-Null

Write-Host "=== 布洛陀安装包 Windows 真机验证 ===" -ForegroundColor Cyan
Write-Host "  PKG    : $PKG" -ForegroundColor Cyan
Write-Host "  sandbox: $SB" -ForegroundColor Cyan

# ---------- python 解析（windows-latest 自带 python）----------
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source }
if ($py) { info "python: $py ($(& $py --version 2>&1))" } else { info "python: 未找到" }

# ---------- 准备模拟记忆中心 ----------
info "准备模拟记忆中心..."
foreach ($d in @("核心层","情境层","潜意识层","记忆规则","技能配置","成就系统","记忆琥珀","记忆蓝图","最伟大的我","未知未知")) {
  New-Item -ItemType Directory -Path (Join-Path $MC $d) -Force | Out-Null
}
Set-Content -Path (Join-Path $MC "核心层/CORE.md") -Value "# CORE" -Encoding UTF8
Set-Content -Path (Join-Path $MC "记忆规则/用户基本规则-铁律版.md") -Value "# 铁律版" -Encoding UTF8
Set-Content -Path (Join-Path $MC "记忆规则/用户基本规则-摘要版.md") -Value "# 摘要版" -Encoding UTF8
# v2: 动态枚举（教训「Skill 名单硬编码=版本不同步」；加强包 v1.7.2 harness 曾硬编码 9 项）
$skillNames = @(Get-ChildItem -Path (Join-Path $PKG "references/skills") -Directory -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
if ($skillNames.Count -eq 0) { no "Skill 名单枚举: references/skills/ 为空（包结构异常）" } else { info "Skill 名单(动态): $($skillNames.Count) 个" }
foreach ($s in $skillNames) {
  New-Item -ItemType Directory -Path (Join-Path $MC "技能配置/$s") -Force | Out-Null
  Set-Content -Path (Join-Path $MC "技能配置/$s/SKILL.md") -Value "# $s" -Encoding UTF8
}
New-Item -ItemType Directory -Path (Join-Path $HOME_SIM ".workbuddy") -Force | Out-Null
foreach ($f in @("SOUL.md","IDENTITY.md","USER.md","MEMORY.md")) {
  Set-Content -Path (Join-Path $HOME_SIM ".workbuddy/$f") -Value "# $f" -Encoding UTF8
}
$BAKTS = "2026-07-14_1200"
$BAKDIR = Join-Path $AMBER "升级备份_$BAKTS"
New-Item -ItemType Directory -Path $BAKDIR -Force | Out-Null
foreach ($f in @("SOUL.md","IDENTITY.md","USER.md","MEMORY.md")) {
  Set-Content -Path (Join-Path $BAKDIR "$f.bak") -Value "# bak $f" -Encoding UTF8
}
info "模拟环境就绪"

# ============================================================
# 正例 T1-T14
# ============================================================

# ---------- T1: 包内 .ps1 语法解析（真机 PS 解析器）----------
info "T1: PS 语法解析..."
$parseFail = @()
foreach ($pf in @("verify.ps1","rollback.ps1")) {
  $p = Join-Path $PKG $pf
  if (-not (Test-Path $p)) { $parseFail += "$pf(缺失)"; continue }
  $errs = $null
  [System.Management.Automation.Language.Parser]::ParseFile($p, [ref]$null, [ref]$errs) | Out-Null
  if ($errs -and $errs.Count -gt 0) { $parseFail += "$pf($($errs.Count)错:$($errs[0].Message))" }
}
if ($parseFail.Count -eq 0) { ok "T1 语法解析: verify.ps1 + rollback.ps1 (0 错误)" } else { no "T1 语法解析失败: $($parseFail -join ' / ')" }

# ---------- T2: verify.ps1 完整沙盒 → exit 0 ----------
info "T2: verify.ps1 完整沙盒..."
$env:MEMORY_CENTER = $MC
$oldHome = $env:USERPROFILE
$env:USERPROFILE = $HOME_SIM
$env:HOME = $HOME_SIM
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "verify.ps1") *> (Join-Path $SB "t2.log")
$t2Exit = $LASTEXITCODE
$t2txt = Get-Content -Encoding UTF8 (Join-Path $SB "t2.log") -Raw -ErrorAction SilentlyContinue
$t2HasStruct = ($t2txt -match "接入自检") -and ($t2txt -match "记忆Skill") -and ($t2txt -match "自检")
if ($t2HasStruct) { ok "T2 verify.ps1 真机可跑 + 输出结构完整（退出码=$t2Exit）" } else {
  no "T2 verify.ps1 真机执行异常（退出码=$t2Exit）"
  Get-Content -Encoding UTF8 (Join-Path $SB "t2.log") | Select-Object -Last 12 | ForEach-Object { Write-Host "    T2LOG: $_" }
}
if ($t2Exit -ne 0) {
  Get-Content -Encoding UTF8 (Join-Path $SB "t2.log") | Where-Object { $_ -match "\[FAIL\]" } | Select-Object -First 10 | ForEach-Object { Write-Host "    T2FAIL项: $_" }
}

# ---------- T3: verify.ps1 空记忆中心 → fail-loud ----------
info "T3: verify.ps1 空记忆中心 fail-loud..."
$env:MEMORY_CENTER = (Join-Path $SB "nonexistent-mc")
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "verify.ps1") *> (Join-Path $SB "t3.log")
$t3Exit = $LASTEXITCODE
if ($t3Exit -ne 0) { ok "T3 空记忆中心→安全中止 (exit=$t3Exit)" } else { no "T3 空记忆中心未中止 (exit=0)" }

# ---------- T4: rollback.ps1 -Preview [-Timestamp <ts>] ----------
info "T4: rollback.ps1 -Preview -Timestamp <ts>..."
$env:MEMORY_CENTER = $MC
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "rollback.ps1") -Preview -Timestamp $BAKTS *> (Join-Path $SB "t4.log")
$t4Exit = $LASTEXITCODE
$t4txt = Get-Content -Encoding UTF8 (Join-Path $SB "t4.log") -Raw
if ($t4Exit -eq 0 -and $t4txt -match "预览备份") { ok "T4 -Preview -Timestamp <ts> exit=0 + 输出预览" } else { no "T4 -Preview 异常(exit=$t4Exit)" }

# ---------- T4b: rollback.ps1 裸用 -Preview（无参）必须可用 ----------
info "T4b: rollback.ps1 裸用 -Preview..."
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "rollback.ps1") -Preview *> (Join-Path $SB "t4b.log")
$t4bExit = $LASTEXITCODE
$t4btxt = Get-Content -Encoding UTF8 (Join-Path $SB "t4b.log") -Raw -ErrorAction SilentlyContinue
if (($t4bExit -eq 0) -and ($t4btxt -notmatch "Missing an argument|缺少参数")) { ok "T4b 裸用 -Preview exit=0（switch 参数契约正确）" }
else { no "T4b 裸用 -Preview 异常(exit=$t4bExit)" }

# ---------- T5: rollback.ps1 -Restore <ts> 真回滚 + 回滚前备份 ----------
info "T5: rollback.ps1 -Restore <ts>..."
Set-Content -Path (Join-Path $HOME_SIM ".workbuddy/SOUL.md") -Value "# current soul (pre-rollback)" -Encoding UTF8
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "rollback.ps1") -Restore $BAKTS *> (Join-Path $SB "t5.log")
$t5Exit = $LASTEXITCODE
$restored = (Get-Content (Join-Path $HOME_SIM ".workbuddy/SOUL.md") -Raw -Encoding UTF8) -match "bak SOUL"
$preRollback = Get-ChildItem $AMBER -Filter "回滚前_*" -ErrorAction SilentlyContinue
if ($t5Exit -eq 0 -and $restored -and $preRollback) { ok "T5 -Restore <ts> exit=0 + 文件已还原 + 回滚前备份已留" }
else { no "T5 -Restore 异常(exit=$t5Exit 已还原=$restored 回滚前备份=$([bool]$preRollback))" }

# ---------- T6: rollback.ps1 未设 MEMORY_CENTER → fail-loud ----------
info "T6: rollback.ps1 未设 MEMORY_CENTER..."
Clear-Env "MEMORY_CENTER"
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "rollback.ps1") -Restore $BAKTS *> (Join-Path $SB "t6.log")
$t6Exit = $LASTEXITCODE
if ($t6Exit -ne 0) { ok "T6 未设 MEMORY_CENTER→安全中止 (exit=$t6Exit)" } else { no "T6 未设环境变量未中止 (exit=0)" }

# ---------- T7: bash -n 语法（Git Bash 存在时）----------
info "T7: verify.sh / rollback.sh bash 语法..."
$bash = (Get-Command bash -ErrorAction SilentlyContinue).Source
if ($bash) {
  $shFail = @()
  foreach ($sf in @("verify.sh","rollback.sh")) {
    & $bash -n (Join-Path $PKG $sf) 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $shFail += $sf }
  }
  if ($shFail.Count -eq 0) { ok "T7 bash -n: verify.sh + rollback.sh 语法通过" } else { no "T7 bash -n 失败: $($shFail -join ',')" }
} else { info "T7 跳过: 无 bash" }

# ---------- T8: 包内 .py 全量 py_compile ----------
info "T8: 包内 .py 全量语法编译..."
if ($py) {
  $pyFiles = Get-ChildItem -Path $PKG -Recurse -Filter "*.py" -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '__pycache__' }
  $bad = @()
  foreach ($f in $pyFiles) {
    & $py -m py_compile $f.FullName 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { $bad += $f.Name }
  }
  if ($bad.Count -eq 0) { ok "T8 py_compile: $($pyFiles.Count) 个 .py 全通过（0 错·缓存已导出沙盒）" } else { no "T8 py_compile 失败 $($bad.Count) 个: $($bad -join ',')" }
} else { info "T8 跳过: 无 python" }

# ---------- T9: data_contamination_check.py dry-run ----------
info "T9: data_contamination_check.py dry-run..."
if ($py) {
  $fp = Join-Path $PKG "references/integrity-fingerprints.json"
  & $py (Join-Path $PKG "data_contamination_check.py") --memory-root $MC --fingerprints $fp --template-root (Join-Path $PKG "references") *> (Join-Path $SB "t9.log")
  $t9Exit = $LASTEXITCODE
  if ($t9Exit -eq 0) { ok "T9 污染检测 dry-run exit=0" } else { no "T9 污染检测 exit=$t9Exit"; Get-Content -Encoding UTF8 (Join-Path $SB "t9.log") | Select-Object -Last 5 | ForEach-Object { Write-Host "    T9LOG: $_" } }
} else { info "T9 跳过: 无 python" }

# ---------- T10: pkg_cleanliness_check.py ----------
info "T10: pkg_cleanliness_check.py..."
if ($py) {
  & $py (Join-Path $PKG "references/scripts/pkg_cleanliness_check.py") --pkg-root $PKG *> (Join-Path $SB "t10.log")
  $t10Exit = $LASTEXITCODE
  if ($t10Exit -eq 0) { ok "T10 发布卫生检查 exit=0" } else { no "T10 发布卫生 exit=$t10Exit"; Get-Content -Encoding UTF8 (Join-Path $SB "t10.log") | Select-Object -First 8 | ForEach-Object { Write-Host "    T10LOG: $_" } }
} else { info "T10 跳过: 无 python" }

# ---------- T11: platform_compat.py 全维 ----------
info "T11: platform_compat.py 全维..."
if ($py) {
  & $py (Join-Path $PKG "references/scripts/platform_compat.py") $PKG *> (Join-Path $SB "t11.log")
  $t11Exit = $LASTEXITCODE
  if ($t11Exit -eq 0) { ok "T11 跨平台兼容检查 exit=0" } else { no "T11 跨平台 exit=$t11Exit"; Get-Content -Encoding UTF8 (Join-Path $SB "t11.log") | Where-Object { $_ -match "缺陷" } | Select-Object -First 8 | ForEach-Object { Write-Host "    T11LOG: $_" } }
} else { info "T11 跳过: 无 python" }

# ---------- T12: smoke_test.py ----------
info "T12: smoke_test.py..."
if ($py) {
  & $py (Join-Path $PKG "references/scripts/smoke_test.py") $PKG *> (Join-Path $SB "t12.log")
  $t12Exit = $LASTEXITCODE
  if ($t12Exit -eq 0) { ok "T12 结构完整性 exit=0" } else { no "T12 结构完整性 exit=$t12Exit"; Get-Content -Encoding UTF8 (Join-Path $SB "t12.log") | Select-Object -Last 8 | ForEach-Object { Write-Host "    T12LOG: $_" } }
} else { info "T12 跳过: 无 python" }

# ---------- T13: 未知未知钩子真机跑（无 🕳️ 段 → 放行不崩）----------
info "T13: route_unknown_unknown.py Windows 实跑..."
if ($py) {
  $tr = Join-Path $SB "transcript.jsonl"
  '{"type":"assistant","message":{"content":[{"type":"text","text":"普通回复，无盲区段"}]}}' | Set-Content -Path $tr -Encoding UTF8
  $payload = (@{ transcript_path = $tr } | ConvertTo-Json -Compress)
  $env:UU_TARGET = Join-Path $MC "未知未知/悬置区.md"
  $env:UU_STATE  = Join-Path $MC "未知未知/.route_state.json"
  $payload | & $py (Join-Path $PKG "references/scripts/route_unknown_unknown.py") *> (Join-Path $SB "t13.log")
  $t13Exit = $LASTEXITCODE
  Clear-Env "UU_TARGET"
  Clear-Env "UU_STATE"
  $t13txt = Get-Content -Encoding UTF8 (Join-Path $SB "t13.log") -Raw -ErrorAction SilentlyContinue
  $fcntlCrash = $t13txt -match "fcntl|ImportError|Traceback"
  if ($t13Exit -eq 0 -and -not $fcntlCrash) { ok "T13 钩子 Windows 实跑 exit=0（无 fcntl 崩溃）" }
  else { no "T13 钩子异常(exit=$t13Exit fcntl崩=$fcntlCrash)"; Get-Content -Encoding UTF8 (Join-Path $SB "t13.log") | Select-Object -Last 6 | ForEach-Object { Write-Host "    T13LOG: $_" } }
} else { info "T13 跳过: 无 python" }

# ---------- T14: 铁律硬墙钩子 Windows 实跑 ----------
info "T14: rule_fragment_inject.py Windows 实跑..."
if ($py) {
  '{"prompt":"今天天气不错"}' | & $py (Join-Path $PKG "references/scripts/rule_fragment_inject.py") *> (Join-Path $SB "t14.log")
  $t14Exit = $LASTEXITCODE
  if ($t14Exit -eq 0) { ok "T14 铁律硬墙钩子实跑 exit=0（失败默认放行）" }
  else { no "T14 硬墙钩子 exit=$t14Exit"; Get-Content -Encoding UTF8 (Join-Path $SB "t14.log") | Select-Object -Last 6 | ForEach-Object { Write-Host "    T14LOG: $_" } }
} else { info "T14 跳过: 无 python" }

# ============================================================
# 反例 V1-V8
# ============================================================

info "反例：应有的行为断言（未修则 FAIL 检出）..."

# ---------- V1: 包内 .ps1 必须 UTF-8 BOM ----------
$bomBad = @()
foreach ($pf in @("verify.ps1","rollback.ps1")) {
  $p = Join-Path $PKG $pf
  if (Test-Path $p) {
    $b = [System.IO.File]::ReadAllBytes($p)
    if (-not ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)) { $bomBad += $pf }
  }
}
if ($bomBad.Count -eq 0) { ok "V1 包内 .ps1 全部含 UTF-8 BOM" } else { no "V1 BOM 缺失: $($bomBad -join ',')" }

# ---------- V2: INSTALL.md 的 powershell 代码块不得含 bash 专属语法 ----------
# v2.0: INSTALL.md 属 F 阶段待建（Step0 能力分流文档）——缺失时显式 SKIP（不静默假绿·不假红）
if (-not (Test-Path (Join-Path $PKG "INSTALL.md"))) {
  info "V2/V3/V6 跳过: INSTALL.md 未建（v2.0 F 阶段交付物·建齐后本三项自动生效）"
  $script:INSTALL_MISSING = $true
} else { $script:INSTALL_MISSING = $false }
$installRaw = if ($script:INSTALL_MISSING) { "" } else { Get-Content (Join-Path $PKG "INSTALL.md") -Raw -Encoding UTF8 }
# 先剥掉每行的 blockquote 前缀（"> ```powershell" 也是真 powershell 围栏），再扫
$dequoted = ($installRaw -split "\r?\n" | ForEach-Object { $_ -replace '^\s*>\s?', '' }) -join "`n"
$blocks = [regex]::Matches($dequoted, '(?s)```powershell\s*\r?\n(.*?)```')
$psHits = @()
foreach ($b in $blocks) {
  $body = $b.Groups[1].Value
  # 剔除 PowerShell here-string 内的内容（python -c @" ... "@ 是 Python 源码，其 MSYS 前缀是给 Git Bash 用的）
  $body = [regex]::Replace($body, '(?s)@"(.*?)"@', '')
  foreach ($line in ($body -split "\r?\n")) {
    # bash 专属：VAR=value 后跟命令（PowerShell 会把 "VAR=value" 当成命令名）
    if ($line -match '^\s*[A-Z_][A-Z0-9_]*=\S+\s+[\x22\x27$&/]') { $t = $line.Trim(); $psHits += $t.Substring(0, [Math]::Min(60, $t.Length)) }
  }
}
if ($script:INSTALL_MISSING) { }
elseif ($psHits.Count -eq 0) { ok "V2 INSTALL.md powershell 块无 bash 专属语法（扫了 $($blocks.Count) 个块）" }
else { no "V2 INSTALL.md powershell 块含 bash 专属语法 $($psHits.Count) 处（原生 PowerShell 必失败）: $($psHits[0])" }

# ---------- V3: 版本字样三方一致 ----------
# 2026-10-07 CI真机反哺修：原『version.md全文剔非数字』把注释里2026-09-01/§1/5全并入 ⇒ 输出
# 2.1.01202609014.1..752.0.0. 恒≠INSTALL标题=V3永红空转（CI run 37626430079:147实拍）。改为精准提取 version 行。
$vmRaw = Get-Content -Encoding UTF8 (Join-Path $PKG "version.md") -Raw
$mVM = [regex]::Match($vmRaw, '(?m)^\s*version:\s*"([0-9][0-9.]*)"')
$vm = if ($mVM.Success) { $mVM.Groups[1].Value } else { "" }
$installTitle = ""
$mTitle = [regex]::Match($installRaw, '(?m)^#\s*[^\r\n]*?(\d+\.\d+(?:\.\d+)?)\s*[—\-]')
if ($mTitle.Success) { $installTitle = $mTitle.Groups[1].Value }
$chgRaw = Get-Content (Join-Path $PKG "CHANGELOG.md") -Raw -Encoding UTF8
$hasUnreleased = $chgRaw -match '(?m)^##\s*\[未发布\]'
if ($script:INSTALL_MISSING) { }
elseif (($vm -eq $installTitle) -and (-not $hasUnreleased)) { ok "V3 版本字样一致 (version.md=$vm, INSTALL=$installTitle, CHANGELOG 已 relabel)" }
else { no "V3 版本字样不一致: version.md=$vm / INSTALL.md 标题=$installTitle / CHANGELOG 仍有[未发布]=$hasUnreleased" }

# ---------- V4: verify.ps1 引用的指纹文件路径必须真实存在 ----------
$vp = Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8
$mFp = [regex]::Match($vp, 'Join-Path\s+\$PKG_ROOT\s+"([^"]*integrity-fingerprints\.json)"')
if ($mFp.Success) {
  $fpRel = $mFp.Groups[1].Value -replace '\\','/'
  if (Test-Path (Join-Path $PKG $fpRel)) { ok "V4 verify.ps1 指纹路径有效: $fpRel" }
  else { no "V4 verify.ps1 指纹路径指向不存在文件: $fpRel（包内实为 references/integrity-fingerprints.json）" }
} else { info "V4 跳过" }

# ---------- V5: verify.ps1 系统文件落点须与 step5 契约一致（~/.workbuddy/）----------
$usesMC = [regex]::Match($vp, 'Join-Path\s+\$MC\s+"SOUL\.md"'); if (-not $usesMC.Success) { $usesMC = [regex]::Match($vp, 'Join-Path\s+\$MC[^\n]*SOUL\.md') }
$usesWB = [regex]::Match($vp, 'Join-Path\s+\$HOME\s+\("\.workbuddy\"\s*\+\s*\$rel\)')
if (-not $usesWB.Success) { $usesWB = [regex]::Match($vp, '\.workbuddy[\\"/]|Join-Path\s+\$CFG_DIR\s+\$rel') }
if ($usesMC.Success -and -not $usesWB.Success) {
  no "V5 verify.ps1 查系统文件落点为记忆中心根，与 step5 契约不符（应查 ~/.workbuddy/）"
} elseif (-not $usesWB.Success) {
  no "V5 verify.ps1 未校验平台系统文件落点 ~/.workbuddy/{SOUL,IDENTITY,USER}.md（双端共同盲区）"
} else { ok "V5 verify.ps1 系统文件落点 = ~/.workbuddy/（对齐 step5 契约）" }

# ---------- V13: 双端支持 --platform/-Platform 配置根路由（v2.0.1·2026-09-30 L3审计根治）----------
$sh13 = Get-Content (Join-Path $PKG "verify.sh") -Raw -Encoding UTF8
$v13Sh = ([regex]::IsMatch($sh13, '--platform') -and [regex]::IsMatch($sh13, 'config_root:'))  # ⚠️改名防碰撞：原 $pSH 与全局 $PSH 同名（PS变量大小写不敏感）——T19取证轮揪出，覆盖后全部 PowerShell 调用腿变 & $true
$pPS = ([regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), '\$Platform') -and [regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), 'config_root:'))
if ($v13Sh -and $pPS) { ok "V13 双端支持 --platform/-Platform（按端 capability.yaml config_root 路由落点检查）" } else { no "V13 多端配置根路由缺失（verify 不覆盖非 WB 端落点=2026-09-30 审计病根复发）" }

# ---------- V6: 脚本数量声称 vs 实际（真语义：cp scripts/* 后再 cp hooks/* 同名覆盖）----------
$scDir = Join-Path $PKG "references/scripts"
$hkDir = Join-Path $PKG "references/hooks"
$simSc = Join-Path $SB "sc-sim"
if (Test-Path $simSc) { Remove-Item -Recurse -Force $simSc }
New-Item -ItemType Directory -Path $simSc -Force | Out-Null
if (Test-Path $scDir) { Copy-Item (Join-Path $scDir "*") $simSc -Recurse -Force -ErrorAction SilentlyContinue }
if (Test-Path $hkDir) { Copy-Item (Join-Path $hkDir "*") $simSc -Recurse -Force -ErrorAction SilentlyContinue }
$actualFiles = @(Get-ChildItem $simSc -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '__pycache__' }).Count
$actualPy = @(Get-ChildItem $simSc -Filter "*.py" -File -Recurse -ErrorAction SilentlyContinue).Count
$actualSh = @(Get-ChildItem $simSc -Filter "*.sh" -File -Recurse -ErrorAction SilentlyContinue).Count
$claimOk = $true; $claimMsg = ""
foreach ($m in [regex]::Matches($installRaw, '(?<n>\d+)\s*个\s*\*{0,2}脚本')) {
  $n = [int]$m.Groups['n'].Value
  if ($n -ne $actualFiles) { $claimOk = $false; $claimMsg += "[INSTALL 声称 $n 实 $actualFiles] " }
}
foreach ($m in [regex]::Matches($installRaw, '其余\s*(\d+)\s*个\s*\.py')) {
  $n = [int]$m.Groups[1].Value
  if ($n -ne $actualPy) { $claimOk = $false; $claimMsg += "[INSTALL 称 py=$n 实 $actualPy] " }
}
foreach ($m in [regex]::Matches($vp, '脚本中心共\s*(\d+)\s*个\D*(\d+)\s*个\s*\.py')) {
  $nf = [int]$m.Groups[1].Value; $np = [int]$m.Groups[2].Value
  if ($nf -ne $actualFiles) { $claimOk = $false; $claimMsg += "[verify.ps1 称 $nf 实 $actualFiles] " }
  if ($np -ne $actualPy) { $claimOk = $false; $claimMsg += "[verify.ps1 称 py=$np 实 $actualPy] " }
}
if ($script:INSTALL_MISSING) { }
elseif ($claimOk) { ok "V6 脚本数量声称一致 (脚本中心 $actualFiles 项 = $actualPy .py + $actualSh .sh + 其他)" }
else { no "V6 脚本数量声称不符: $claimMsg" }

# ---------- V7: rollback.ps1 按自身文档裸用 -Preview 必须可用 ----------
$env:MEMORY_CENTER = $MC
& $PSH -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PKG "rollback.ps1") -Preview *> (Join-Path $SB "v7.log")
$v7txt = Get-Content -Encoding UTF8 (Join-Path $SB "v7.log") -Raw -ErrorAction SilentlyContinue
if ($v7txt -match "Missing an argument|缺少参数") { no "V7 rollback.ps1 按自身文档裸用 -Preview 即报错（[string] 应为 [switch]）" }
else { ok "V7 rollback.ps1 裸 -Preview 可用" }

# ---------- V8: 包内不得含作者侧运行时痕迹 ----------
$stray = @()
foreach ($p in @(".install",".phaseX_last_run.json",".advisory_history.jsonl")) {
  if (Test-Path (Join-Path $PKG $p)) { $stray += $p }
}
if ($stray.Count -eq 0) { ok "V8 包内无作者侧运行时痕迹" } else { no "V8 包内含作者侧运行时痕迹: $($stray -join ',')" }

# ---------- V9: 包内 .py 必须带 UTF-8 控制台守卫（否则 Windows cp1252 必崩）----------
# 判据：print 内容含 cp1252 不可编码字符，却无 reconfigure(encoding=) / PYTHONIOENCODING 守卫
$enc1252 = [System.Text.Encoding]::GetEncoding(1252)
function Test-Risky([string]$t) {
  foreach ($ch in $t.ToCharArray()) {
    if ([int][char]$ch -lt 128) { continue }
    $s = [string]$ch
    try { $b = $enc1252.GetBytes($s) } catch { return $true }
    if ($enc1252.GetString($b) -ne $s) { return $true }
  }
  return $false
}
$v9 = @{ scripts = 0; hooks = 0; skills = 0; other = 0 }
$v9miss = @{ scripts = 0; hooks = 0; skills = 0; other = 0 }
$v9list = @()
foreach ($f in (Get-ChildItem -Path $PKG -Filter "*.py" -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '__pycache__' })) {
  $txt = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
  if (-not $txt -or $txt -notmatch 'print\(') { continue }
  if (-not (Test-Risky $txt)) { continue }
  $rel = $f.FullName.Replace($PKG, "").TrimStart("\", "/").Replace("\", "/")
  $k = if ($rel -like "references/scripts/*") { "scripts" } elseif ($rel -like "references/hooks/*") { "hooks" } elseif ($rel -like "references/skills/*") { "skills" } else { "other" }
  $v9[$k]++
  if ($txt -match 'reconfigure\(\)|reconfigure\(\s*encoding|PYTHONIOENCODING') { continue }
  $v9miss[$k]++
  $v9list += $rel
}
$totMiss = ($v9miss.Values | Measure-Object -Sum).Sum
if ($totMiss -eq 0) { ok "V9 含 cp1252 不可编码 print 的 .py 均带 UTF-8 控制台守卫" }
else {
  no "V9 $totMiss 个含 cp1252 不可编码 print 的 .py 缺 UTF-8 控制台守卫（Windows 控制台必崩）"
  Write-Host "       scripts $($v9miss.scripts)/$($v9.scripts) · hooks $($v9miss.hooks)/$($v9.hooks) · skills $($v9miss.skills)/$($v9.skills) · other $($v9miss.other)/$($v9.other)" -ForegroundColor DarkGray
  $v9list | Select-Object -First 8 | ForEach-Object { Write-Host "       - $_" -ForegroundColor DarkGray }
}

# ---------- V10: verify.sh 不得裸调 python3（N5：macOS 只有 python 时静默失败）----------
$sh = Get-Content (Join-Path $PKG "verify.sh") -Raw -Encoding UTF8
$barePy3 = [regex]::Matches($sh, '(?m)^\s*(?<!\S)python3\s+"')
if ($barePy3.Count -eq 0) { ok "V10 verify.sh 无裸调 python3（已用解析器回退 python）" }
else { no "V10 verify.sh 仍有 $($barePy3.Count) 处裸调 python3（应改用解析器：WorkBuddy 自带→python3→python）" }

# ---------- V11: 双端均须校验 Skill 软链接（N6：step7 #12 契约与验证器脱节）----------
$linkPS = ([regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), '\.workbuddy[\\/]skills') -or [regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), 'Join-Path\s+\$CFG_DIR\s+"skills"'))
$linkSH = ([regex]::IsMatch($sh, '\.workbuddy/skills') -or [regex]::IsMatch($sh, 'SLINK_DIR="\$CFG_DIR/skills"'))
if ($linkPS -and $linkSH) { ok "V11 双端均校验 Skill 软链接（端配置根 skills/·v2.0.1 CFG_DIR 或旧 ~/.workbuddy 形态）" }
else { no "V11 软链接校验缺失: verify.ps1=$linkPS verify.sh=$linkSH（step7 #12 要求 9 链接有效）" }

# ---------- V12: 双端均须校验 ~/.workbuddy 平台系统文件（N1：双端共同盲区）----------
$sysPS = ([regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), '\.workbuddy[\\/]?"?\s*\+?\s*\$rel|\.workbuddy\\') -or [regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), 'Join-Path\s+\$CFG_DIR\s+\$rel'))
if (-not $sysPS) { $sysPS = [regex]::IsMatch((Get-Content (Join-Path $PKG "verify.ps1") -Raw -Encoding UTF8), 'Join-Path\s+\$HOME\s+\("\.workbuddy') }
$sysSH = ([regex]::IsMatch($sh, 'HOME/\.workbuddy/\$rel|HOME/\.workbuddy/') -or [regex]::IsMatch($sh, 'CFG_DIR/\$rel'))
if ($sysPS -and $sysSH) { ok "V12 双端均校验平台系统文件落点（端配置根/旧WB形态均可）" }
else { no "V12 平台系统文件校验缺失: verify.ps1=$sysPS verify.sh=$sysSH" }

# ---------- V13: 同名双版本 route_unknown_unknown.py 必须一致（N3）----------
$h1 = Join-Path $PKG "references/hooks/route_unknown_unknown.py"
$h2 = Join-Path $PKG "references/scripts/route_unknown_unknown.py"
if ((Test-Path $h1) -and (Test-Path $h2)) {
  $d1 = (Get-FileHash $h1 -Algorithm SHA256).Hash
  $d2 = (Get-FileHash $h2 -Algorithm SHA256).Hash
  if ($d1 -eq $d2) { ok "V13 同名 route_unknown_unknown.py 双副本一致（消除复制顺序隐性契约）" }
  else { no "V13 同名 route_unknown_unknown.py 双副本不一致（安装时静默覆盖、依赖顺序）" }
} else { ok "V13 同名双副本不存在（已合并）" }

# ---------- V14: rollback.sh 参数契约（N8：与 rollback.ps1 对称）----------
$rs = Get-Content (Join-Path $PKG "rollback.sh") -Raw -Encoding UTF8
$hasPreview = [regex]::IsMatch($rs, '--preview')
$hasRestoreTs = [regex]::IsMatch($rs, '--restore=')
$hasRestore = [regex]::IsMatch($rs, '\-\-restore\)')
if ($hasPreview -and $hasRestore -and $hasRestoreTs) { ok "V14 rollback.sh 支持 --preview / --restore / --restore=<ts>" }
else { no "V14 rollback.sh 参数契约不完整: preview=$hasPreview restore=$hasRestore restore=<ts>=$hasRestoreTs" }

# ---------- V15: 发布包不得含运行时日志 *.log（如 triwich seal.log 含会话 ID）----------
# 背景：.gitignore 有 **/*.log 但文件系统交付（zip/拷贝）不经 git，日志会随包外发。
$logHits = @(Get-ChildItem -Path $PKG -Recurse -File -Filter *.log -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\\fixtures\\' })
if ($logHits.Count -eq 0) { ok "V15 包内无运行时日志 *.log（防会话 ID/路径外发）" }
else { no "V15 包内含 $($logHits.Count) 个 .log 运行时日志: $($logHits | Select-Object -First 3 | ForEach-Object { $_.Name })" }

# ---------- T15: 端到端安装演练（按 INSTALL.md 核心动作在沙盒重建记忆中心）----------
# 目的：不只验证"脚本能跑"，而验证"Windows 用户按文档装完，verify 能过"。
# 沙盒 = RUNNER_TEMP/e2e；模拟用户 HOME=%USERPROFILE% → 沙盒 home。
info "T15: 端到端安装演练（沙盒重建记忆中心 + ~/.workbuddy）..."
$E2E = Join-Path $SB "e2e"
$E2E_MC = Join-Path $E2E "记忆共享中心"
$E2E_HOME = Join-Path $E2E "home"
if (Test-Path $E2E) { Remove-Item -Recurse -Force $E2E -ErrorAction SilentlyContinue }
# 1) 记忆中心骨架（step3 契约）
foreach ($d in @("核心层","情境层","潜意识层","记忆规则","技能配置","成就系统","记忆琥珀","记忆蓝图","最伟大的我","未知未知")) {
  New-Item -ItemType Directory -Path (Join-Path $E2E_MC $d) -Force | Out-Null
}
Copy-Item (Join-Path $PKG "references/templates/CORE.md") (Join-Path $E2E_MC "核心层/CORE.md") -Force -ErrorAction SilentlyContinue
if (-not (Test-Path (Join-Path $E2E_MC "核心层/CORE.md"))) { Set-Content (Join-Path $E2E_MC "核心层/CORE.md") "# CORE" -Encoding UTF8 }
# 2) 规则三层+规则层数据：走安装器真函数（批次9 §4-2 二抓·⛔裸拷模板）
#    病根：上轮抓到"手工拷 SKILL.md 存根"同构病——产品路径 install_rule_files 对模板跑
#    _fill_text（占位符本地化），夹具裸拷 ⇒ 装后产物带 [记忆共享中心] 假残留（铁律版/详解存档版 2 件）。
#    夹具必须走产品同一扇门，测的才是产品。
$oldH2 = $env:HOME; $oldU2 = $env:USERPROFILE
$env:HOME = $E2E_HOME; $env:USERPROFILE = $E2E_HOME
Push-Location $PKG
& $py -c "import install_scripts as I, sys; mc=sys.argv[1]; I.install_rule_files(mc); I.install_rule_data(mc)" $E2E_MC *> (Join-Path $SB "t15_rules.log")
$rulesExit = $LASTEXITCODE
Pop-Location
$env:HOME = $oldH2; $env:USERPROFILE = $oldU2
$rulesLog = Get-Content -Encoding UTF8 (Join-Path $SB "t15_rules.log") -Raw -ErrorAction SilentlyContinue
if (-not $rulesLog) { $rulesLog = "" }
Write-Host "    DIAG-T15 rules-leg rc=$rulesExit : $((($rulesLog -split "`n" | Where-Object { $_.Trim() }) | Select-Object -Last 3) -join ' | ')"
if ($rulesExit -ne 0) { no "T15 规则层安装腿（install_rule_files/install_rule_data）非零退出 rc=$rulesExit" }
else { ok "T15 规则层走安装器真函数 rc=0（占位符本地化经 _fill_text·同产品路径）" }
# 3) Skill 面：真走 --deploy-skills 安装腿（批次9 §4-2·T16 根治复验）
#    原这里手工拷 SKILL.md 存根 = 用夹具粉饰现场：占位符本地化根本没跑，
#    verify.sh 的"装后产物无占位符残留"检查测的是空气（12 件残留就是这么漏的）。
New-Item -ItemType Directory -Path (Join-Path $E2E_HOME ".workbuddy\skills") -Force | Out-Null
$oldH3 = $env:HOME; $oldU3 = $env:USERPROFILE
$env:HOME = $E2E_HOME; $env:USERPROFILE = $E2E_HOME
& $py (Join-Path $PKG "install_scripts.py") --deploy-skills $E2E_MC *> (Join-Path $SB "t15_deploy_skills.log")
$dsExit = $LASTEXITCODE
$env:HOME = $oldH3; $env:USERPROFILE = $oldU3
$dsLog = Get-Content -Encoding UTF8 (Join-Path $SB "t15_deploy_skills.log") -Raw -ErrorAction SilentlyContinue
if (-not $dsLog) { $dsLog = "" }
Write-Host "    DIAG-T15 deploy-skills rc=$dsExit : $(($dsLog -split "`n" | Where-Object { $_.Trim() }) -join ' | ')"
if ($dsExit -ne 0) { no "T15 --deploy-skills 非零退出 rc=$dsExit（安装腿本身挂了，后面不用验）" }
else { ok "T15 --deploy-skills 实跑 rc=0" }
# 软链接（无权限时复制降级——与 step6 护栏同语义；链路事实独立于部署腿）
foreach ($s in $skillNames) {
  try { New-Item -ItemType SymbolicLink -Path (Join-Path $E2E_HOME ".workbuddy\skills\$s") -Target (Join-Path $E2E_MC "技能配置/$s") -Force | Out-Null }
  catch { New-Item -ItemType Directory -Path (Join-Path $E2E_HOME ".workbuddy\skills\$s") -Force | Out-Null; Copy-Item (Join-Path $E2E_MC "技能配置/$s/SKILL.md") (Join-Path $E2E_HOME ".workbuddy\skills\$s\SKILL.md") -Force -ErrorAction SilentlyContinue }
}
# 4) 平台系统文件（step5 契约落点）
foreach ($f in @("SOUL.md","IDENTITY.md","USER.md","MEMORY.md")) {
  $tsrc = Join-Path $PKG "references/templates/$f"
  if (Test-Path $tsrc) { Copy-Item $tsrc (Join-Path $E2E_HOME ".workbuddy\$f") -Force }
  else { Set-Content (Join-Path $E2E_HOME ".workbuddy\$f") "# $f" -Encoding UTF8 }
}
# 5) 成就系统（step 契约：需 .py）
New-Item -ItemType Directory -Path (Join-Path $E2E_MC "成就系统/scripts") -Force | Out-Null
Set-Content (Join-Path $E2E_MC "成就系统/scripts/tracker.py") "# tracker" -Encoding UTF8
# 5b) 目录型骨架非空（verify §4.6 存在∧非空判据·2026-10-18 Loop轮·作者指令「做到完整」）：
#     建目录≠有文件——琥珀/蓝图/最伟大的我/未知未知 补装后最小真实态种子
Set-Content (Join-Path $E2E_MC "记忆琥珀/seed.md") "# amber seed" -Encoding UTF8
Set-Content (Join-Path $E2E_MC "记忆蓝图/seed.md") "# blueprint seed" -Encoding UTF8
Set-Content (Join-Path $E2E_MC "最伟大的我/seed.md") "# me seed" -Encoding UTF8
Set-Content (Join-Path $E2E_MC "未知未知/seed.md") "# uu seed" -Encoding UTF8
# 5c) 摘要版三表合成（模拟用户完成 step5 逐格替换·⛔夹具装"没装完的人"=判据假红）
$sumPath = Join-Path $E2E_MC "记忆规则/用户基本规则-摘要版.md"
if (-not $py) { no "T15 摘要版合成: python 未找到（$py 空·⛔不拿陈旧 LASTEXITCODE 假绿）" }
elseif (Test-Path $sumPath) {
  & $py -c "import re,sys; p=sys.argv[1]; s=open(p,encoding='utf-8').read(); s=re.sub(r'\[Q(\d+)·答案待注入\]', lambda m: '示例答案Q'+m.group(1), s); s=re.sub(r'\[Q(\d+)·规则待派生\]', lambda m: '示例规则Q'+m.group(1), s); open(p,'w',encoding='utf-8').write(s); print('SYNTH OK', len(s))" $sumPath *> (Join-Path $SB "t15_synth.log")
  if ($LASTEXITCODE -ne 0) { no "T15 摘要版合成腿 rc=$LASTEXITCODE（见 t15_synth.log）" } else { ok "T15 摘要版三表合成完成（38 格示例值·演练装后终态）" }
} else { no "T15 摘要版合成: 装后文件缺失 $sumPath" }

if (-not $PSH) { info "T15 跳过: 无 powershell" } else {
  $oldH = $env:HOME; $oldU = $env:USERPROFILE
  $env:HOME = $E2E_HOME; $env:USERPROFILE = $E2E_HOME; $env:USERDOMAIN = $null
  $env:MEMORY_CENTER = $E2E_MC
  & $PSH -NoProfile -ExecutionPolicy Bypass -Command "& '$PKG\verify.ps1'" *> (Join-Path $SB "t15.log")
  $t15Exit = $LASTEXITCODE
  $env:HOME = $oldH; $env:USERPROFILE = $oldU
  Clear-Env "MEMORY_CENTER"
  $log = Get-Content -Encoding UTF8 (Join-Path $SB "t15.log") -Raw -ErrorAction SilentlyContinue
  if (-not $log) { $log = "" }
  $t15Fail = ([regex]::Matches($log, '\[FAIL\]')).Count
  if ($t15Exit -eq 0) { ok "T15 正确安装后 verify.ps1 exit=0（$t15Fail 个 FAIL）" }
  else { no "T15 正确安装后 verify.ps1 仍 exit=$t15Exit（$t15Fail 个 FAIL）——端用户会被误判安装失败"; ($log -split "`n") | Where-Object { $_ -match '\[FAIL\]' } | Select-Object -First 8 | ForEach-Object { Write-Host "    T15FAIL: $($_.Trim())" } }
}

# ---------- T16: 端到端安装演练（bash 端同沙盒）----------
info "T16: 端到端安装演练（verify.sh 同沙盒）..."
$bash = (Get-Command bash -ErrorAction SilentlyContinue).Source
if (-not $bash -or -not (Test-Path $E2E_MC)) { info "T16 跳过: 无 bash 或沙盒未建" } else {
  $bashExe = $null
  foreach ($c in @("C:\Program Files\Git\bin\bash.exe","C:\Program Files\Git\usr\bin\bash.exe")) { if (Test-Path $c) { $bashExe = $c; break } }
  if (-not $bashExe) { $bashExe = $bash }
  $oldH = $env:HOME; $oldU = $env:USERPROFILE
  $env:HOME = $E2E_HOME; $env:USERPROFILE = $E2E_HOME
  $env:MEMORY_CENTER = $E2E_MC
  & $bashExe -c "bash '$PKG/verify.sh'" *> (Join-Path $SB "t16.log")
  $t16Exit = $LASTEXITCODE
  $env:HOME = $oldH; $env:USERPROFILE = $oldU
  Clear-Env "MEMORY_CENTER"
  $log16 = Get-Content -Encoding UTF8 (Join-Path $SB "t16.log") -Raw -ErrorAction SilentlyContinue
  if (-not $log16) { $log16 = "" }
  $t16Fail = ([regex]::Matches($log16, '\[FAIL\]')).Count
  if ($t16Exit -eq 0) { ok "T16 正确安装后 verify.sh exit=0（$t16Fail 个 FAIL）" }
  else {
    no "T16 正确安装后 verify.sh exit=$t16Exit（$t16Fail 个 FAIL）"
    # 取证腿自带现场：验点只报计数不报明细=逼人猜（真机实证：残留 2 件但哪 2 件被管道吞了）
    ($log16 -split "`n") | Where-Object { $_ -match 'FAIL|双拼|占位|残留|^\s+- |SCC-DETAIL' } | Select-Object -First 30 | ForEach-Object { Write-Host "    T16DETAIL: $($_.Trim())" }
  }
}

# ---------- T17: v2.0 平台矩阵逐端 dry-run（capability 驱动·每端 adapter 可装）----------
info "T17: 平台矩阵 dry-run（adapters/* 逐端 install_scripts --platform）..."
if ($py) {
  # 仅测已发布端（带 capability.yaml = 有接入能力声明才算矩阵成员）；README-only 占位端
  # 显形为「待迁入清单」不计数不假绿——迁入落地 capability.yaml 后自动进矩阵。
  $platDirs = @(Get-ChildItem -Path (Join-Path $PKG "adapters") -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path (Join-Path $_.FullName "capability.yaml") } | ForEach-Object { $_.Name })
  $platPending = @(Get-ChildItem -Path (Join-Path $PKG "adapters") -Directory -ErrorAction SilentlyContinue | Where-Object { -not (Test-Path (Join-Path $_.FullName "capability.yaml")) } | ForEach-Object { $_.Name })
  if ($platPending.Count -gt 0) { info "T17 待迁入端占位（无 capability.yaml·不计入矩阵）: $($platPending -join ',')" }
  $t17fail = @()
  foreach ($pt in $platDirs) {
    & $py (Join-Path $PKG "install_scripts.py") --platform $pt --dry-run $MC *> (Join-Path $SB ("t17_" + $pt + ".log"))
    if ($LASTEXITCODE -ne 0) { $t17fail += "$pt(exit=$LASTEXITCODE)" }
  }
  if ($platDirs.Count -ge 4 -and $t17fail.Count -eq 0) { ok "T17 平台矩阵 $($platDirs.Count) 已发布端 dry-run 全 exit=0" }
  elseif ($platDirs.Count -lt 4) { no "T17 已发布端仅 $($platDirs.Count)（<4·枚举或包结构异常）" }
  else { no "T17 平台 dry-run 失败: $($t17fail -join ',')"; Get-Content -Encoding UTF8 (Join-Path $SB ("t17_" + ($t17fail[0] -replace '\(exit=.*',''))) -ErrorAction SilentlyContinue | Select-Object -Last 5 | ForEach-Object { Write-Host "    T17LOG: $_" } }
} else { info "T17 跳过: 无 python" }

# ---------- T18: 未知平台必须 fail-loud（exit≠0·防静默装错端）----------
info "T18: 未知平台 fail-loud..."
if ($py) {
  & $py (Join-Path $PKG "install_scripts.py") --platform no-such-platform-zz --dry-run $MC *> (Join-Path $SB "t18.log")
  if ($LASTEXITCODE -ne 0) { ok "T18 未知平台→拒绝 (exit=$LASTEXITCODE)" } else { no "T18 未知平台被静默放行 (exit=0)" }
} else { info "T18 跳过: 无 python" }

# ---------- T19: systemlog 写时守护 Win 真机腿（2026-10-11 Win对等任务卡 DoD-5）----------
# 判据：⛔不停在"任务注册+exit 0"——须实证 触发后归一真发生（违例 ## 头被引擎实际清洗）。
# 链路全程走产品路径：两 .ps1 由 T15 --deploy-skills 落盘（引擎占位符已本地化到沙盒）→
#   install-task 注册 SystemLogWatch（S4U+IgnoreNew）→ watch 按脚本落点推导监听目录→
#   心跳现身(=基线轮完成)后再放违例夹具→等归一。卸载腿收尾防污染 runner。
info "T19: systemlog 看守 Win 真机（注册+触发+归一真发生）..."
$SL_SCRIPTS = Join-Path $E2E_MC "技能配置\system-logger\scripts"
$SL_DIR     = Join-Path $E2E_MC "工作日志\系统日志"
$SL_INSTALL = Join-Path $SL_SCRIPTS "systemlog-install-task.ps1"
$SL_TASK    = 'SystemLogWatch'
if (-not (Test-Path $SL_INSTALL)) {
  no "T19 deploy_skills 未落盘 systemlog Win 守护件（缺 $SL_INSTALL）"
} elseif (-not $PSH) { info "T19 跳过: 无 pwsh/powershell" } else {
  # 0) pwsh 自身可用性探针（分层取证：区分"pwsh 起不来"与"脚本没执行"两坑位）
  & $PSH -NoProfile -Command "exit 7"; $probeRc = $LASTEXITCODE
  if ($probeRc -ne 7) { no "T19 pwsh 探针异常 rc=$probeRc (期望7) PSH=$PSH" } else {
  # 1) 注册 + 启动（-Command 形态＝T15 实证可出日志的调用形；⛔-File 形态首轮 rc=0+空日志+任务缺席，待排中文路径/启动坑）
  & $PSH -NoProfile -ExecutionPolicy Bypass -Command "& '$SL_INSTALL'" *> (Join-Path $SB "t19_install.log")
  $t19rc = $LASTEXITCODE
  $task19 = Get-ScheduledTask -TaskName $SL_TASK -ErrorAction SilentlyContinue
  if ($t19rc -ne 0 -or -not $task19) {
    no "T19 注册失败 rc=$t19rc task=$(if ($task19) {'在位'} else {'缺席'})"
    $tl = Get-Content -Encoding UTF8 (Join-Path $SB "t19_install.log") -ErrorAction SilentlyContinue
    if (-not $tl) { Write-Host "    T19LOG: （t19_install.log 空——子 pwsh 零输出，查 -File/-Command/中文路径层）PSH=$PSH INSTALL=$SL_INSTALL" }
    else { $tl | Select-Object -First 30 | ForEach-Object { Write-Host "    T19LOG: $_" } }
  } else {
    ok "T19 $SL_TASK 已注册（state=$($task19.State)·schtasks 实读）"
    # 2) 等心跳现身=watch 进程活且基线轮已建（先建基线后放夹具，防夹具被当基线永不触发）
    $hb = Join-Path $SL_DIR ".watch-ps.heartbeat"
    $deadline = (Get-Date).AddSeconds(60); $hbSeen = $false
    while ((Get-Date) -lt $deadline) { Start-Sleep -Seconds 3; if (Test-Path $hb) { $hbSeen = $true; break } }
    if (-not $hbSeen) { no "T19 心跳60s未现身——watch 进程未起或监听目录推导错（$SL_DIR）" }
    else {
      ok "T19 心跳现身（watch 进程活·基线轮完成·路径推导实证）"
      # 3) 放违例夹具（结构同 Mac 沙盒实证过的形态）
      $fx = Join-Path $SL_DIR "系统日志_2020-01-02.md"
      Set-Content -Path $fx -Encoding UTF8 -Value @'
# 系统日志 2020-01-02

## 概览

- **任务总数**：2 条

## 📝 今日任务随手记（描述式违例头）

### 任务甲
- **完成**：10:00
- **工具**：WorkBuddy
- **类型**：验证
- **涉及文件**：ci-fixture
- **对话摘要**：T19夹具条目甲
- **结论**：夹具
- **来源**：🟢验证
- **置信度**：🟢A

### 任务乙
- **完成**：10:05
- **工具**：Qoder CN
- **类型**：验证
- **涉及文件**：ci-fixture
- **对话摘要**：T19夹具条目乙
- **结论**：夹具
- **来源**：🟢验证
- **置信度**：🟢A
'@
      # 4) 等归一真发生：违例 ## 头消失（interval=15s+防抖2s，窗口60s）
      $deadline2 = (Get-Date).AddSeconds(60); $normalized = $false
      while ((Get-Date) -lt $deadline2) {
        Start-Sleep -Seconds 5
        $head = Get-Content $fx -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($head -and @(($head | Where-Object { $_ -match '^## 📝' })).Count -eq 0) { $normalized = $true; break }
      }
      if ($normalized) {
        ok "T19 触发后归一真发生：违例头<90s内被引擎实际清洗（非仅 exit 0）"
      } else {
        no "T19 超时60s违例头仍在——守护已注册但归一未实际发生"
        Get-Content -Encoding UTF8 (Join-Path $SL_DIR ".watch-ps.log") -ErrorAction SilentlyContinue | Select-Object -Last 8 | ForEach-Object { Write-Host "    T19WLOG: $_" }
      }
      # 5) 卸载腿（幂等清理，防任务残留污染 runner / 复跑冲突）
      & $PSH -NoProfile -ExecutionPolicy Bypass -Command "& '$SL_INSTALL' -Uninstall" *> (Join-Path $SB "t19_uninstall.log")
      if (-not (Get-ScheduledTask -TaskName $SL_TASK -ErrorAction SilentlyContinue)) { ok "T19 -Uninstall 卸载干净" }
      else { no "T19 卸载失败（$SL_TASK 仍在）——手动清: Unregister-ScheduledTask -TaskName $SL_TASK -Confirm:0" }
    }
  }
  }
}

# ---------- T20: 装后清扫——字面占位符幽灵目录必须被移入备份（tiger① 存量根治·可逆不删除） ----------
info "T20: 装后清扫（幽灵目录迁移）..."
if ($py) {
  # 前置清场：同一 $SB 复跑会累积多份备份 → $bak 变数组，Test-Path 数组恒真（审查 2026-10-20）
  $gsRoot = Join-Path $MC ".install/ghost-sweep"
  if (Test-Path -LiteralPath $gsRoot) { Remove-Item -LiteralPath $gsRoot -Recurse -Force -ErrorAction SilentlyContinue }
  $ghost = Join-Path $HOME_SIM "[记忆共享中心]"
  $glog = Join-Path $ghost "logs"
  New-Item -ItemType Directory -Path $glog -Force | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $glog "probe.jsonl"), '{"t":1}')
  $r20 = & $py (Join-Path $PKG "install_scripts.py") $MC --sweep-ghost $HOME_SIM 2>&1 | Out-String
  $ghostGone = -not (Test-Path -LiteralPath $ghost)
  $bak = @(Get-ChildItem -Path (Join-Path $MC ".install/ghost-sweep") -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*记忆共享中心*" }) | Select-Object -Last 1
  if ($ghostGone -and $bak) {
    if (Test-Path -LiteralPath (Join-Path $bak.FullName "logs/probe.jsonl")) {
      ok "T20 幽灵目录已移入备份且内容完整（可逆·未删除）"
    } else {
      no "T20 备份内容缺失——清扫吞数据"
    }
  } else {
    no "T20 幽灵目录未被清走（gone=$ghostGone bak=$([bool]$bak)）"
    Write-Host "    T20OUT: $r20" -ForegroundColor DarkGray
  }
  $r20b = & $py (Join-Path $PKG "install_scripts.py") $MC --sweep-ghost $HOME_SIM 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0 -and $r20b -match "未发现") { ok "T20 二次清扫幂等（干净）" }
  else { no "T20 二次清扫不幂等/rc=$LASTEXITCODE"; Write-Host "    T20OUT2: $r20b" -ForegroundColor DarkGray }
} else { info "T20 跳过: 无 python" }

# ---------- T21: 新装机路由引擎可用（SKILLS 目录派生·防硬编码缺件静默死） ----------
info "T21: 路由引擎新装机冒烟..."
if ($py -and (Test-Path -LiteralPath (Join-Path $PKG "references/scripts/router.py"))) {
  $probe = Join-Path $SB "t21_router_probe.py"
  $code = "import sys; sys.path.insert(0, sys.argv[1]); import router; m=router.route('loop 安装包，检查发布包'); print('N=%d' % len(router.SKILLS)); print('M=%s' % (','.join(m)))"
  [System.IO.File]::WriteAllText($probe, $code, (New-Object System.Text.UTF8Encoding($false)))
  # 技能面用 T15 真装机产物（$E2E_MC/技能配置，含 description）；$MC 是空壳桩，⛔不能用
  $env:BULUOTUO_SKILLS_DIR = (Join-Path $E2E_MC "技能配置")
  $r21 = & $py $probe (Join-Path $PKG "references/scripts") 2>&1 | Out-String
  $n21 = if ($r21 -match 'N=(\d+)') { [int]$Matches[1] } else { -1 }
  $ok21 = ($r21 -match 'M=.*clock-loop')
  if ($LASTEXITCODE -eq 0 -and $n21 -gt 0 -and $ok21) {
    ok "T21 新装机路由可用（SKILLS=$n21·'loop 安装包'命中 clock-loop）"
  } else {
    no "T21 路由冒烟失败（N=$n21 hit=$ok21 rc=$LASTEXITCODE）"
    Write-Host "    T21OUT: $r21" -ForegroundColor DarkGray
  }
  Clear-Env "BULUOTUO_SKILLS_DIR"
} else { no "T21 无法执行：包内 router.py 缺失或无 python（跳过=判据未跑，按红处理）" }

# ---------- 收尾 ----------
$env:USERPROFILE = $oldHome
$env:HOME = $oldHome
Clear-Env "MEMORY_CENTER"
Clear-Env "PYTHONPYCACHEPREFIX"
# 自清：确保被测包内无残留 .pyc 目录（被测包应保持只读）
foreach ($d in @((Join-Path $PKG "references/scripts"), (Join-Path $PKG "references/hooks"), $PKG)) {
  $cd = Join-Path $d "__pycache__"
  if (Test-Path $cd) { Remove-Item -Recurse -Force $cd -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "=== Windows 真机结果: PASS=$PASS FAIL=$FAIL ===" -ForegroundColor Cyan
if ($FAIL -eq 0) { Write-Host "OK 全部通过" -ForegroundColor Green } else { Write-Host "NG $FAIL 项失败" -ForegroundColor Red }
exit $(if ($FAIL -eq 0) { 0 } else { 1 })
