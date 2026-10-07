# ============================================================
# verify.ps1 — ZCode 加强包 接入自检 v0.1.1 (Windows·只读·可随时重跑)
# 用法: powershell -ExecutionPolicy Bypass -File verify.ps1
#       沙盒: $env:ZCODE_HOME="D:\tmp\xxx"; $env:MEMORY_CENTER="D:\tmp\yyy"
# 检查 6 组: 布洛陀指纹 / AGENTS.md注入 / skills软链 / Stop钩子 / 隐私残留 / 路由落点
# 退出码 0 = 全过
# 注意:本文件必须 UTF-8 with BOM(PS5.1 中文兼容)
# ============================================================
$ErrorActionPreference

# ── 记忆中心定位（⛔ 不写死任何目录名·理由同 bash 版：本脚本被 exec，占位符不生效）
function Get-MemoryCenter {
  if ($env:BULUOTUO_MEMORY_CENTER) { return $env:BULUOTUO_MEMORY_CENTER }
  foreach ($d in @("$HOME/.hermes/doenglingz", "$HOME/.workbuddy/doenglingz")) {
    $j = Join-Path $d "runtime_paths.json"
    if (Test-Path $j) {
      try { return (Get-Content $j -Raw -Encoding UTF8 | ConvertFrom-Json).archive_root } catch {}
    }
  }
  foreach ($d in Get-ChildItem -Directory $HOME) {
    if ((Test-Path (Join-Path $d.FullName "开发工具")) -or
        (Test-Path (Join-Path $d.FullName "脚本中心")) -or
        (Test-Path (Join-Path $d.FullName "记忆规则"))) { return $d.FullName }
  }
  return ""
}
$MC = Get-MemoryCenter = "Continue"
$RED = "Red"; $GREEN = "Green"; $YELLOW = "Yellow"; $CYAN = "Cyan"
$PKG_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$MEMORY_CENTER = if ($env:MEMORY_CENTER) { $env:MEMORY_CENTER } else {
  $cand = @((Join-Path $HOME ""$MC""), (Join-Path $HOME "共享中心"), (Join-Path $HOME "记忆中心"))
  $hit = $cand | Where-Object { Test-Path (Join-Path $_ "核心层/CORE.md") } | Select-Object -First 1
  if ($hit) { $hit } elseif ($MC) { $MC } else { (Join-Path $HOME "记忆中心") }
}
$ZCODE_HOME = if ($env:ZCODE_HOME) { $env:ZCODE_HOME } else { Join-Path $HOME ".zcode" }
$AGENTS = Join-Path $ZCODE_HOME "AGENTS.md"
$CONFIG = Join-Path $ZCODE_HOME "cli\config.json"
$HOOK_DST = Join-Path $ZCODE_HOME "hooks\route_unknown_unknown.py"
$SKILLS = @("awaken-memory-system","clock-loop","daily-buddy","growth-box","meta-aletheia","shall-we-talk","sucair","system-logger","triwich")
$GLOBAL:PASS = 0; $GLOBAL:FAIL = 0
$TMP_DIR = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } elseif ($env:USERPROFILE) { $env:USERPROFILE } else { "/tmp" }  # 跨平台兜底·2026-09-30 by ZCode（macOS pwsh 真跑验证用）

function Ok([string]$m) { Write-Host "  [PASS] $m" -ForegroundColor $GREEN; $GLOBAL:PASS++ }
function Bad([string]$m) { Write-Host "  [FAIL] $m" -ForegroundColor $RED; $GLOBAL:FAIL++ }
function Warn([string]$m) { Write-Host "  [WARN] $m" -ForegroundColor $YELLOW }

# Find-Python: 实测执行探针 + 跳 WindowsApps 别名
function Find-Python {
    $cands = @()
    foreach ($cmd in @("python3", "python")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) { $cands += $found.Source }
    }
    if ($cands.Count -eq 0) { $w = & where.exe python3 python 2>$null; if ($w) { $cands += $w } }
    foreach ($c in ($cands | Select-Object -Unique)) {
        if ($c -match "WindowsApps") { continue }
        if (Test-Path $c) {
            try { & $c --version 2>$null | Out-Null; if ($LASTEXITCODE -eq 0) { return $c } } catch { }
        }
    }
    return $null
}

Write-Host "=== ZCode 加强包 接入自检 v0.1.1(只读) ===" -ForegroundColor $CYAN

Write-Host "[1/6] 布洛陀指纹" -ForegroundColor $CYAN
$FP = 0
foreach ($f in @("核心层/CORE.md","情境层/动态状态快照.md","潜意识层/SHADOW.md","记忆规则/用户基本规则-铁律版.md")) {
    $p = Join-Path $MEMORY_CENTER $f
    if ((Test-Path $p) -and (Get-Item $p).Length -gt 0) { $FP++ }
}
$FPS = 0
foreach ($s in $SKILLS) { if (Test-Path (Join-Path $MEMORY_CENTER "技能配置/$s/SKILL.md")) { $FPS++ } }
if ($FP -eq 4 -and $FPS -ge 8) { Ok "记忆中心指纹完整(核心文件4/4 + 记忆Skill $FPS/9)" }
else { Bad "记忆中心指纹不完整(核心 $FP/4 + Skill $FPS/9)——先完成布洛陀安装" }

Write-Host "[2/6] AGENTS.md 注入文件" -ForegroundColor $CYAN
if (Test-Path $AGENTS) {
    Ok "$AGENTS 存在"
    if (Select-String -Path $AGENTS -Pattern "你的 ZCode" -Quiet) { Ok "署名含「你的 ZCode」" }
    else { Bad "AGENTS.md 无 ZCode 署名——可能被改写,请比对 templates/AGENTS.md" }
} else { Bad "AGENTS.md 不存在——请跑 setup.ps1 或手动装 templates/AGENTS.md" }

Write-Host "[3/6] 记忆 Skill 软链(~/.zcode/skills/)" -ForegroundColor $CYAN
$SK = 0; $MISS = @()
foreach ($s in $SKILLS) {
    $link = Join-Path $ZCODE_HOME "skills/$s"
    $inPlace = $false
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        if ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink") {
            # Test-Path 对 reparse point 不穿透——用 Target 做穿透检查
            $target = ($item.Target -join "")
            if (-not [string]::IsNullOrEmpty($target) -and (Test-Path (Join-Path $target "SKILL.md"))) { $inPlace = $true }
        } elseif (Test-Path (Join-Path $link "SKILL.md")) { $inPlace = $true }  # 实体目录也算在册
    }
    if ($inPlace) { $SK++ } else { $MISS += $s }
}
if ($SK -ge 8) { Ok "记忆Skill在册: $SK/9" }
else { Bad "记忆Skill仅 $SK/9 (期望>=8)·缺失: $($MISS -join ' ')" }

Write-Host "[4/6] 未知未知路由 Stop 钩子" -ForegroundColor $CYAN
if ((Test-Path $HOOK_DST) -and (Get-Item $HOOK_DST).Length -gt 0) {
    Ok "钩子脚本就位: $HOOK_DST"
    if (Select-String -Path $HOOK_DST -Pattern "\[记忆共享中心\]" -Quiet) { Bad "钩子脚本含未替换占位符——残差将写不进悬置区" }
    else { Ok "路径占位符已替换" }
} else { Bad "钩子脚本缺失: $HOOK_DST——请跑 setup.ps1" }
if (Test-Path $CONFIG) {
    if (-not (Find-Python)) { Warn "未找到可用 python3,跳过 config.json 结构检查(仅做文本比对)" }
    else {
        $pyScript = @'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    print(f"JSONERR {e}"); sys.exit(0)
hooks = d.get("hooks", {})
print("ENABLED", "yes" if hooks.get("enabled") else "no")
stop = hooks.get("events", {}).get("Stop", [])
import sys as _sa, os as _o
_hook_dst = _o.path.normpath(_sa.argv[2]).replace("\\", "/") if len(_sa.argv) > 2 else ""
found = any("route_unknown_unknown.py" in h.get("command", "") and (_hook_dst in h.get("command", "").replace("\\", "/"))
            for grp in stop if isinstance(grp, dict)
            for h in grp.get("hooks", []) if isinstance(h, dict))
print("REGISTERED", "yes" if found else "no")
'@
        $PY = Find-Python
        $tmpPy = Join-Path $TMP_DIR "zcw_verify_hook_$PID.py"
        [System.IO.File]::WriteAllText($tmpPy, $pyScript, (New-Object System.Text.UTF8Encoding($false)))
        $v = (& $PY $tmpPy $CONFIG) -join "`n"
        Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
        if ($v -match "ENABLED yes") { Ok "hooks.enabled=true(钩子运行器已启用)" }
        else { Bad "hooks.enabled 未开启——config-file hooks 默认禁用,ZCode 钩子全不跑" }
        if ($v -match "REGISTERED yes") { Ok "Stop 钩子已注册(route_unknown_unknown.py)" }
        else { Bad "Stop 钩子未注册——请跑 setup.ps1 或手动追加" }
        if ($v -match "JSONERR") { Bad "config.json 解析失败: $v" }
    }
} else { Bad "config.json 不存在: $CONFIG——请跑 setup.ps1" }

Write-Host "[5/6] 隐私残留(随包脱敏门禁·扫包内文件)" -ForegroundColor $CYAN
$guard = Join-Path $PKG_DIR "privacy/desensitize-guard.sh"
if (Test-Path $guard) {
    $bashExe = Get-Command bash -ErrorAction SilentlyContinue
    if (-not $bashExe) { Warn "bash 不可用,隐私检查跳过(显式降级·非静默PASS)" }
    if ($bashExe) {
        & $bashExe.FullName $guard $PKG_DIR *> $null
        if ($LASTEXITCODE -eq 0) { Ok "包内无个人态字面量残留(路径/用户名/邮箱)" }
        else { Bad "包内检测到个人态残留——请用官方完整包重装(勿使用来路不明的副本)" }
    } else { Warn "无 bash(Git Bash)环境,跳过本项——可在 WSL/macOS 上复验" }
} else { Warn "脱敏门禁脚本缺失,跳过本项" }

Write-Host "[5b/6] 数字分身钩子(advisory·可选组件·缺件不阻塞)" -ForegroundColor $CYAN
$DT_DEV = Join-Path $MEMORY_CENTER "数字分身/devtools"
$DT_ALL = $true; $DT_REG_N = 0
foreach ($h in @("doenglingz_inject_prompt.py","position3_notify.py","doenglingz_guard_zcode.py","doenglingz_level_declare_guard.py","tsl_closeout_guard.py","tsl_verify.py","tsl_echo_hook.py","tsl_tree_hook.py")) {
    if (-not (Test-Path (Join-Path $DT_DEV $h))) { $DT_ALL = $false }
}
if ($DT_ALL) {
    Ok "分身钩子件 8/8 在部署面(数字分身/devtools)"
    foreach ($h in @("doenglingz_inject_prompt.py","position3_notify.py","tsl_echo_hook.py","doenglingz_guard_zcode.py","doenglingz_level_declare_guard.py","tsl_closeout_guard.py","tsl_tree_hook.py")) {
        if ((Select-String -Path $CONFIG -Pattern ([regex]::Escape($h)) -Quiet)) { $DT_REG_N++ }
    }
    if ($DT_REG_N -eq 7) { Ok "分身钩子已注册 7/7(UPS 3 + Stop 4)" }
    else { Warn "分身钩子注册 $DT_REG_N/7——跑 setup.ps1 补注册(分身为可选组件)" }
} else {
    Warn "分身件未部署——完整安装:给 AI 说「装数字分身」(可选组件·不影响核心)"
}

Write-Host "[6/6] 路由落点" -ForegroundColor $CYAN
if (Test-Path (Join-Path $MEMORY_CENTER "未知未知/悬置区.md")) { Ok "悬置区落点存在" }
else { Warn "悬置区.md 不存在——AI 触发未知未知时自动创建" }
if (Test-Path (Join-Path $MEMORY_CENTER "未知未知/.route_heartbeat.json")) { Ok "路由心跳文件存在(事件驱动)" }
else { Warn "路由心跳未创建——首次触发【🕳️ 我的未知未知】后自动生成" }

Write-Host ""
Write-Host "=== 结果: PASS=$GLOBAL:PASS FAIL=$GLOBAL:FAIL ===" -ForegroundColor $CYAN
if ($GLOBAL:FAIL -eq 0) {
    Write-Host "✅ 接入正常。验证效果:新开 ZCode 会话回复应带【意图分类】开头、署名「—— 你的 ZCode 🧩」;说「我美吗」测记忆唤醒。" -ForegroundColor $GREEN
    exit 0
} else {
    Write-Host "❌ $GLOBAL:FAIL 项未过——按上方 [FAIL] 项修复后重跑。" -ForegroundColor $RED
    exit 1
}
