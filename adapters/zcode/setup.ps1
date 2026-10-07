# ============================================================
# setup.ps1 — ZCode 加强包 接入脚本 v0.1.1 (Windows)
# 前提:已装布洛陀五层记忆系统(~/[记忆共享中心] 已就位) + 已安装 ZCode
# 功能:检测记忆中心 → AGENTS.md注入文件 → skills软链(Junction·10) → Stop钩子注册 → 分身钩子(可选·UPS3+Stop4) → 体检 → 自验证
# 用法: powershell -ExecutionPolicy Bypass -File setup.ps1
#       沙盒测试: $env:ZCODE_HOME="D:\tmp\xxx"; $env:MEMORY_CENTER="D:\tmp\yyy"
# 设计:fail-loud + 幂等(可重跑) + 自验证 + 增量不覆盖
# 机制依据:2026-08-30 ZCode 端机制 + 千问/AutoClaw 包 v0.1.x Windows 真机先例
# 注意:本文件必须 UTF-8 with BOM(PS5.1 中文兼容·无 BOM 按 cp1252 读乱码)
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
$MC = Get-MemoryCenter = "Stop"

$RED = "Red"; $GREEN = "Green"; $YELLOW = "Yellow"; $CYAN = "Cyan"
$PKG_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$MEMORY_CENTER = if ($env:MEMORY_CENTER) { $env:MEMORY_CENTER } else {
  $cand = @((Join-Path $HOME ""$MC""), (Join-Path $HOME "共享中心"), (Join-Path $HOME "记忆中心"))
  $hit = $cand | Where-Object { Test-Path (Join-Path $_ "核心层/CORE.md") } | Select-Object -First 1
  if ($hit) { $hit } else { (Join-Path $HOME "[记忆共享中心]") }
}
$ZCODE_HOME = if ($env:ZCODE_HOME) { $env:ZCODE_HOME } else { Join-Path $HOME ".zcode" }
$SKILLS_DIR = Join-Path $ZCODE_HOME "skills"
$HOOKS_DIR = Join-Path $ZCODE_HOME "hooks"
$CONFIG = Join-Path $ZCODE_HOME "cli\config.json"
# 记忆 Skill 清单(9个=布洛陀安装包 v1.5.4 对外发布口径·与 setup.sh 同源)
$SKILLS = @("awaken-memory-system","clock-loop","daily-buddy","good-good-study","growth-box","meta-aletheia","shall-we-talk","sucair","system-logger","triwich")  # 10件=v2.0全平台包口径·2026-09-30 by ZCode
$FP_SKILLS = $SKILLS
$GLOBAL:FAIL = 0
$GLOBAL:SK = 0
$GLOBAL:DT_MISSING = 0
$TMP_DIR = if ($env:TEMP) { $env:TEMP } elseif ($env:TMPDIR) { $env:TMPDIR } else { $env:USERPROFILE }

function Write-Step([string]$msg) { Write-Host $msg -ForegroundColor $CYAN }
function Write-Ok([string]$msg) { Write-Host "  [OK] $msg" -ForegroundColor $GREEN }
function Write-Keep([string]$msg) { Write-Host "  [keep] $msg" -ForegroundColor $YELLOW }
function Write-Err([string]$msg) { Write-Host "  [X] $msg" -ForegroundColor $RED }
function Write-Skip([string]$msg) { Write-Host "  [skip] $msg" -ForegroundColor $YELLOW }
function Write-Info([string]$msg) { Write-Host "  [i] $msg" -ForegroundColor $CYAN }
function Write-Equal([string]$msg) { Write-Host "  [=] $msg" -ForegroundColor $GREEN }

# Find-Python: 实测执行探针 + 跳 WindowsApps 的 Microsoft Store 别名(千问包 v0.1.1 根治)
function Find-Python {
    $cands = @()
    foreach ($cmd in @("python3", "python")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) { $cands += $found.Source }
    }
    if ($cands.Count -eq 0) {
        $w = & where.exe python3 python 2>$null
        if ($w) { $cands += $w }
    }
    foreach ($c in ($cands | Select-Object -Unique)) {
        if ($c -match "WindowsApps") { continue }
        if (Test-Path $c) {
            try {
                & $c --version 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return $c }
            } catch { }
        }
    }
    return $null
}

# New-SafeLink: 按平台建链(Windows→Junction 免管理员 / Unix→SymbolicLink)
function New-SafeLink([string]$link, [string]$src) {
    if ($env:OS -eq "Windows_NT") { New-Item -ItemType Junction -Path $link -Target $src | Out-Null }
    else { New-Item -ItemType SymbolicLink -Path $link -Target $src | Out-Null }
}

# Safe-Link: Junction 三态(增量安全——⛔绝不覆盖实体文件;Junction 才修正指向)
# ⚠️ Test-Path 对 reparse point 不穿透(悬空也 True)——须用 Target 存在性做穿透检查
function Safe-Link([string]$link, [string]$src) {
    $nm = Split-Path -Leaf $link
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        $isLink = ($item.LinkType -eq "Junction" -or $item.LinkType -eq "SymbolicLink")
        if ($isLink) {
            $target = ($item.Target -join "")
            $targetExists = (-not [string]::IsNullOrEmpty($target)) -and (Test-Path $target)
            if ($targetExists -and $target -eq $src) {
                Write-Equal "$nm(已正确)"
            } elseif ($targetExists) {
                Remove-Item $link -Force
                New-SafeLink $link $src
                Write-Ok "$nm(更新指向)"
            } else {
                Remove-Item $link -Force
                if (-not (Test-Path $src)) {
                    Write-Skip "$nm(失效Junction且源缺失·发布口径与本机版本差异过渡态)"
                    return
                }
                New-SafeLink $link $src
                Write-Ok "$nm(修复失效链)"
            }
        } else {
            Write-Keep "$nm 已是实体目录,未覆盖(尊重用户已有)"
            $GLOBAL:SK++
            return
        }
    } else {
        New-SafeLink $link $src
        Write-Ok "$nm"
    }
    $GLOBAL:SK++
}

Write-Host "=== ZCode 加强包 接入 v0.1.1 ===" -ForegroundColor $CYAN
Write-Host "    前提:需已装布洛陀五层记忆系统(~/[记忆共享中心])+已安装 ZCode。未装则安全中止,不破坏任何东西。" -ForegroundColor $YELLOW
Write-Host "    目标工具: ZCode 🧩 | ZCode 根: $ZCODE_HOME" -ForegroundColor $CYAN

Write-Step "[1/8] 检测布洛陀记忆中心(指纹级·非仅目录存在)..."
if (-not (Test-Path $MEMORY_CENTER)) {
    Write-Err "记忆中心目录不存在: $MEMORY_CENTER"
    Write-Host "    请先完成布洛陀五层记忆系统安装,再跑本脚本。" -ForegroundColor $RED
    exit 1
}
$script:FP_FAIL = 0
function Test-FpFile([string]$rel, [string]$label, [string]$kw) {
    $f = Join-Path $MEMORY_CENTER $rel
    if (-not (Test-Path $f) -or (Get-Item $f).Length -eq 0) {
        Write-Err "[缺] $label`: $rel (不存在或为空)"; $script:FP_FAIL++
    } elseif ($kw -and -not (Select-String -Path $f -Pattern $kw -Quiet)) {
        Write-Err "[疑] $label`: $rel 存在但无`"$kw`"关键词(疑似非布洛陀文件)"; $script:FP_FAIL++
    } else {
        Write-Ok "$label`: $rel"
    }
}
Test-FpFile "核心层/CORE.md" "L1核心层" $null
Test-FpFile "情境层/动态状态快照.md" "L4情境层" $null
Test-FpFile "潜意识层/SHADOW.md" "L5潜意识层" $null
Test-FpFile "记忆规则/用户基本规则-铁律版.md" "行为规则" "铁律"
$FP_SK = 0
foreach ($s in $FP_SKILLS) { if (Test-Path (Join-Path $MEMORY_CENTER "技能配置/$s/SKILL.md")) { $FP_SK++ } }
if ($FP_SK -ge 8) { Write-Ok "记忆Skill: $FP_SK/9" } else { Write-Err "[缺] 记忆Skill仅 $FP_SK/9 (期望>=8)"; $script:FP_FAIL++ }
if ($script:FP_FAIL -gt 0) {
    Write-Err "[X] $MEMORY_CENTER 存在,但不是完整的布洛陀五层记忆系统($($script:FP_FAIL) 项指纹缺失,见上)"
    Write-Host "    可能只是通用目录。请先完成布洛陀初始化,再跑本脚本。" -ForegroundColor $RED
    exit 1
}
Write-Ok "布洛陀指纹验证通过 | 记忆中心: $MEMORY_CENTER"
if (-not (Test-Path $ZCODE_HOME)) {
    Write-Err "[X] 未探测到 ZCode 根目录: $ZCODE_HOME"
    Write-Host "    请先安装 ZCode 并至少运行一次,再跑本脚本。" -ForegroundColor $RED
    exit 1
}

Write-Step "[2/8] 数据清理(不可跳过·强制门禁):清除开发阶段遗留样例数据(SHA256精确比对·绝不碰你的记录)..."
$PY = Find-Python
if (-not $PY) {
    Write-Err "[X] 未找到可用的 python3——数据清理无法执行(不可跳过),已中止。请先安装 Python3 再重试。"
    exit 1
}
if (-not (Test-Path (Join-Path $PKG_DIR "privacy/release_contamination_check.py")) -or -not (Test-Path (Join-Path $PKG_DIR "privacy/integrity-fingerprints.json"))) {
    Write-Err "[X] 数据清理工具/指纹缺失——此步不可跳过,已中止。请用完整加强包重试。"
    exit 1
}
& $PY (Join-Path $PKG_DIR "privacy/release_contamination_check.py") --memory-root $MEMORY_CENTER --fingerprints (Join-Path $PKG_DIR "privacy/integrity-fingerprints.json") --template-root (Join-Path $PKG_DIR "privacy/decontam-templates") --apply
if ($LASTEXITCODE -ne 0) {
    Write-Err "[X] 数据清理执行失败——此步不可跳过,已中止安装。"
    exit 1
}
Write-Ok "数据清理完成:已清理开发阶段遗留的样例数据(不是你的内容),你的记录完整保留,原文件已备份可还原"

Write-Step "[3/8] 检查 AGENTS.md 注入文件(~/.zcode/AGENTS.md·唯一常驻注入·实体不覆盖)..."
$AGENTS = Join-Path $ZCODE_HOME "AGENTS.md"
if (Test-Path $AGENTS) {
    Write-Keep "AGENTS.md 已存在,未覆盖(如需更新请手动比对 templates/AGENTS.md)"
} else {
    $tpl = Join-Path $PKG_DIR "templates/AGENTS.md"
    if (Test-Path $tpl) {
        $content = [System.IO.File]::ReadAllText($tpl, [System.Text.Encoding]::UTF8)
        $content = $content.Replace("{记忆共享中心}", $MEMORY_CENTER)
        [System.IO.File]::WriteAllText($AGENTS, $content, (New-Object System.Text.UTF8Encoding($false)))
        Write-Ok "装 AGENTS.md (骨架·{称呼}待填)"
    } else {
        Write-Err "AGENTS.md 缺失且包内无模板——请用完整加强包重试"
        $GLOBAL:FAIL++
    }
}

Write-Step "[4/8] 软链记忆系统 Skills(9个=布洛陀安装包发布口径·Junction·平台内置Skill不碰)..."
if (-not (Test-Path $SKILLS_DIR)) { New-Item -ItemType Directory -Path $SKILLS_DIR -Force | Out-Null }
foreach ($s in $SKILLS) {
    $src = Join-Path $MEMORY_CENTER "技能配置/$s"
    if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
        if ($s -eq "sucair" -and (Test-Path (Join-Path $MEMORY_CENTER "技能配置/reading-assistant/SKILL.md"))) {
            $src = Join-Path $MEMORY_CENTER "技能配置/reading-assistant"
            Write-Info "sucair 源缺失→回退旧发布名 reading-assistant"
        } else {
            Write-Skip "$s (源缺失·指纹门禁已保证>=8装全,个别缺失为发布口径与本机版本差异)"
            continue
        }
    }
    Safe-Link (Join-Path $SKILLS_DIR $s) $src
}
Write-Ok "记忆Skill软链: $GLOBAL:SK/$($SKILLS.Count)"

Write-Step "[5/8] 安装未知未知路由 Stop 钩子(~/.zcode/hooks/ + config.json 幂等注册)..."
if (-not (Test-Path $HOOKS_DIR)) { New-Item -ItemType Directory -Path $HOOKS_DIR -Force | Out-Null }
$cliDir = Join-Path $ZCODE_HOME "cli"
if (-not (Test-Path $cliDir)) { New-Item -ItemType Directory -Path $cliDir -Force | Out-Null }
$HOOK_SRC = Join-Path $PKG_DIR "hooks/route_unknown_unknown.py"
$HOOK_DST = Join-Path $HOOKS_DIR "route_unknown_unknown.py"
if (-not (Test-Path $HOOK_SRC)) {
    Write-Err "[X] 包内钩子脚本缺失——请用完整加强包重试"
    $GLOBAL:FAIL++
} else {
    $isSelfHook = $false
    if (Test-Path $HOOK_DST) {
        $isSelfHook = (Select-String -Path $HOOK_DST -Pattern "route_unknown_unknown" -Quiet)
    }
    if ($isSelfHook) {
        Write-Keep "钩子脚本已存在,仅刷新路径占位符"
    } else {
        Copy-Item $HOOK_SRC $HOOK_DST -Force
        Write-Ok "钩子脚本已安装"
    }
    $hc = [System.IO.File]::ReadAllText($HOOK_DST, [System.Text.Encoding]::UTF8)
    $hc = $hc.Replace("[记忆共享中心]", $MEMORY_CENTER)
    [System.IO.File]::WriteAllText($HOOK_DST, $hc, (New-Object System.Text.UTF8Encoding($false)))
    if (Select-String -Path $HOOK_DST -Pattern "\[记忆共享中心\]" -Quiet) {
        Write-Err "[X] 占位符替换失败——钩子将写不进你的悬置区"
        $GLOBAL:FAIL++
    } else {
        Write-Ok "路径占位符已替换为 $MEMORY_CENTER"
    }
    # 注册到 config.json:幂等按脚本名匹配·保留全部现有钩子·enabled 缺失才补 true(不覆盖用户显式关闭)
    $pyScript = @'
import json, sys, os
p = sys.argv[1]
# ── 并发写闸（2026-09-30 by ZCode·多端 setup 并发实证治理）：读-改-写全程持独占锁·close 释放 ──
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None
data = {}
if os.path.isfile(p):
    try:
        with open(p, "r", encoding="utf-8") as f: data = json.load(f)
    except Exception as e:
        print(f"FAIL_JSON:{e}"); sys.exit(1)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
enabled_missing = "enabled" not in hooks
if enabled_missing: hooks["enabled"] = True
stop = hooks.setdefault("events", {}).setdefault("Stop", [])
import sys as _sa
_hook_dir = _sa.argv[2] if len(_sa.argv) > 2 else os.path.expanduser("~/.zcode/hooks").replace("\\", "/")
already = any(
    "route_unknown_unknown.py" in h.get("command", "") and (".zcode/hooks" in h.get("command", "") or _hook_dir in h.get("command", ""))
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
foreign = any(
    "route_unknown_unknown.py" in h.get("command", "") and not (".zcode/hooks" in h.get("command", "") or _hook_dir in h.get("command", ""))
    for grp in stop if isinstance(grp, dict)
    for h in grp.get("hooks", []) if isinstance(h, dict)
)
if already:
    print("SKIPPED:registered")
else:
    if foreign:
        print("INFO:检测到其他实现的同名路由钩子,并存注册(本钩子内置盲区文本去重·不会重复写入)")
    hook_cmd = _sa.argv[3] + " " + os.path.join(_hook_dir, "route_unknown_unknown.py").replace("\\", "/")
    stop.append({"hooks": [{"type": "command", "command": hook_cmd}]})
    print("APPENDED")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
if enabled_missing: print("ENABLED_SET")
try:
    if _lk is not None:
        _lk.close()  # close 即释放锁（POSIX fcntl/Windows 句柄锁随句柄关闭释放）
except Exception:
    pass
'@
    $tmpPy = Join-Path $TMP_DIR "zcw_hook_register_$PID.py"
    [System.IO.File]::WriteAllText($tmpPy, $pyScript, (New-Object System.Text.UTF8Encoding($false)))
    $hooksDirFwd = ($HOOKS_DIR -replace "\\", "/")
    & $PY $tmpPy $CONFIG $hooksDirFwd $PY.replace("\\", "/")
    $regExit = $LASTEXITCODE
    Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
    if ($regExit -ne 0) {
        Write-Err "[X] config.json 解析/写入失败——请手动把本钩子追加到 $CONFIG 的 hooks.events.Stop"
        $GLOBAL:FAIL++
    } elseif (Test-Path $CONFIG) {
        if (Select-String -Path $CONFIG -Pattern "route_unknown_unknown.py" -Quiet) { Write-Ok "Stop 钩子已注册(幂等·现有钩子完整保留)" }
        else { Write-Err "[X] 注册验证失败"; $GLOBAL:FAIL++ }
    }
}

Write-Step "[5b/8] 数字分身钩子(可选组件·件在才挂·缺件不阻塞·条文16降级不阻塞)..."
$DT_DEV = Join-Path $MEMORY_CENTER "数字分身/devtools"
$DT_SRC = Join-Path $PKG_DIR "references/digital-twin/devtools"
if (-not (Test-Path $DT_SRC)) { $DT_SRC = Join-Path $PKG_DIR "..\..\references\digital-twin\devtools" }
$DT_HOOKS_UPS = @("doenglingz_inject_prompt.py","position3_notify.py","tsl_echo_hook.py")
$DT_HOOKS_STOP = @("doenglingz_guard_zcode.py","doenglingz_level_declare_guard.py","tsl_closeout_guard.py","tsl_tree_hook.py")
$DT_MISSING = 0
foreach ($h in ($DT_HOOKS_UPS + $DT_HOOKS_STOP + @("tsl_verify.py"))) {
    $dst = Join-Path $DT_DEV $h; $srcF = Join-Path $DT_SRC $h
    if (-not (Test-Path $dst)) {
        if (Test-Path $srcF) {
            if (-not (Test-Path $DT_DEV)) { New-Item -ItemType Directory -Path $DT_DEV -Force | Out-Null }
            Copy-Item $srcF $dst -Force
            $c = [System.IO.File]::ReadAllText($dst, [System.Text.Encoding]::UTF8)
            $c = $c.Replace("[记忆共享中心]", $MEMORY_CENTER)
            [System.IO.File]::WriteAllText($dst, $c, (New-Object System.Text.UTF8Encoding($false)))
            Write-Ok "$h 已从包内部署到 数字分身/devtools/"
        } else { Write-Skip "[skip] $h (包内与部署面皆缺·分身为可选组件)"; $GLOBAL:DT_MISSING = 1 }
    } else { Write-Ok "[=] $h (部署面已在)" }
}
if ($GLOBAL:DT_MISSING -eq 0) {
    $dtPy = @'
import json, sys, os
p, dt_dev = sys.argv[1], sys.argv[2]
# ── 并发写闸（2026-09-30 by ZCode·多端 setup 并发实证治理）：读-改-写全程持独占锁·close 释放 ──
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None
data = {}
if os.path.isfile(p):
    try:
        with open(p, "r", encoding="utf-8") as f: data = json.load(f)
    except Exception as e:
        print(f"FAIL_JSON:{e}"); sys.exit(1)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
hooks.setdefault("enabled", True)
events = hooks.setdefault("events", {})
plan = {
    "UserPromptSubmit": ["doenglingz_inject_prompt.py", "position3_notify.py", "tsl_echo_hook.py"],
    "Stop": ["doenglingz_guard_zcode.py", "doenglingz_level_declare_guard.py", "tsl_closeout_guard.py", "tsl_tree_hook.py"],
}
for evt, names in plan.items():
    lst = events.setdefault(evt, [])
    for nm in names:
        already = any(nm in h.get("command", "") for grp in lst if isinstance(grp, dict) for h in grp.get("hooks", []) if isinstance(h, dict))
        if already:
            print(f"SKIPPED:{evt}:{nm}")
        else:
            lst.append({"hooks": [{"type": "command", "command": "python3 " + os.path.join(dt_dev, nm).replace("\\", "/")}]})
            print(f"APPENDED:{evt}:{nm}")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
try:
    if _lk is not None:
        _lk.close()  # close 即释放锁（POSIX fcntl/Windows 句柄锁随句柄关闭释放）
except Exception:
    pass
'@
    $tmpPy = Join-Path $TMP_DIR "zcw_dt_register_$PID.py"
    [System.IO.File]::WriteAllText($tmpPy, $dtPy, (New-Object System.Text.UTF8Encoding($false)))
    $dtDevFwd = ($DT_DEV -replace "\\", "/")
    & $PY $tmpPy $CONFIG $dtDevFwd
    $dtExit = $LASTEXITCODE
    Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
    if ($dtExit -ne 0) {
        Write-Host "  [!] config.json 写入失败——分身钩子未注册(可选组件·手动补见 INSTALL 数字分身完整版单装)"
        $GLOBAL:DT_MISSING = 1
    } else {
        $DT_REG = 0
        foreach ($h in ($DT_HOOKS_UPS + $DT_HOOKS_STOP)) {
            if ((Select-String -Path $CONFIG -Pattern ([regex]::Escape($h)) -Quiet)) { $DT_REG++ }
        }
        Write-Ok "分身钩子注册: $DT_REG/7 (幂等·现有钩子完整保留·Windows共槽由session过滤防串台)"
        Write-Host "  [i] 分身激活≠装文件:完成养成链(答题→计分→造芯)后分身才活,见 INSTALL 数字分身完整版单装" -ForegroundColor $CYAN
    }
} else {
    Write-Host "  [i] 分身件缺——未注册钩子(避免悬空引用)。完整安装:给 AI 说「装数字分身」" -ForegroundColor $CYAN
}

Write-Step "[5c/8] 布洛陀通用层钩子注册(20条·脚本中心路径·幂等按名·缺件skip)..."
$SC = Join-Path $MEMORY_CENTER "脚本中心"
$GEN_SRC = Join-Path $PKG_DIR "..\..\references\scripts"
$genPy = @'
import json, sys, os
p, sc, gen_src = sys.argv[1], sys.argv[2], sys.argv[3]
_lk = None
try:
    import fcntl as _fcntl
    _lk = open(p + ".lock", "w")
    _fcntl.flock(_lk.fileno(), _fcntl.LOCK_EX)
except ImportError:
    try:
        import msvcrt as _msvcrt
        _lk = open(p + ".lock", "w")
        _msvcrt.locking(_lk.fileno(), 0, 1)
    except Exception:
        _lk = None
except Exception:
    _lk = None
data = {}
if os.path.isfile(p):
    with open(p, encoding="utf-8") as f: data = json.load(f)
if not isinstance(data, dict): data = {}
hooks = data.setdefault("hooks", {})
hooks.setdefault("enabled", True)
events = hooks.setdefault("events", {})
# Windows 版：env 前缀语法不可用→session_tail/ttl_expiry/card_id 走默认台账路径（可接受降级）
PLAN = {
    "SessionStart": [("crossend_guard.py", "", "")],
    "PreToolUse": [("edit_heading_guard.py", "--hook", ""), ("skill_write_gate_guard.py", "", "")],
    "PostToolUse": [("zcode_config_guard.py", "postedit", "")],
    "UserPromptSubmit": [
        ("route_inject_prompt.py", "UserPromptSubmit", ""), ("route_miss_feeder.py", "", ""),
        ("kb_inject_prompt.py", "UserPromptSubmit", ""), ("rule_fragment_inject.py", "UserPromptSubmit", ""),
        ("session_tail_inject.py", "UserPromptSubmit", ""), ("zcode_title_namer.py", "UserPromptSubmit", ""),
        ("secret_key_guard.py", "UserPromptSubmit", ""), ("ttl_expiry_guard.py", "UserPromptSubmit", ""),
    ],
    "Stop": [
        ("audit_search_kb.py", "", ""), ("route_audit.py", "--src zcode", ""), ("route_guard_audit.py", "", ""),
        ("card_id_guard.py", "hook", ""), ("feedback_detect.py", "", ""), ("rule_three_layer_guard.py", "--deliver", ""),
        ("zcode_config_guard.py", "hook", ""), ("delivery_boundary_guard.py", "Stop", ""),
        ("manifest_registrar.py", "--apply --quiet", ""),
    ],
}
for evt, items in PLAN.items():
    lst = events.setdefault(evt, [])
    for nm, args, env in items:
        if not os.path.isfile(os.path.join(gen_src, nm)):
            print(f"SKIP_MISSING:{evt}:{nm}")
            continue
        if any(nm in h.get("command", "") for grp in lst if isinstance(grp, dict) for h in grp.get("hooks", []) if isinstance(h, dict)):
            print(f"SKIPPED:{evt}:{nm}")
            continue
        cmd = "python3 " + os.path.join(sc, nm).replace("\\", "/") + ((" " + args) if args else "")
        lst.append({"hooks": [{"type": "command", "command": cmd}]})
        print(f"APPENDED:{evt}:{nm}")
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
if _lk is not None:
    try: _lk.close()
    except Exception: pass
'@
$tmpPy5c = Join-Path $TMP_DIR "zcw_gen_register_$PID.py"
[System.IO.File]::WriteAllText($tmpPy5c, $genPy, (New-Object System.Text.UTF8Encoding($false)))
& $PY $tmpPy5c $CONFIG (($SC -replace "\\", "/")) (($GEN_SRC -replace "\\", "/"))
Remove-Item $tmpPy5c -Force -ErrorAction SilentlyContinue
Write-Ok "通用层钩子注册完成(幂等·缺件显形 SKIP_MISSING)"

Write-Step "[6/8] 检测未知未知路由落点(悬置区+心跳)..."
$HB = Join-Path $MEMORY_CENTER "未知未知/.route_heartbeat.json"
if (Test-Path $HB) { Write-Ok "路由心跳文件存在(事件驱动·闲置属正常)" }
else { Write-Info "未找到路由心跳 $HB——首次触发一次【🕳️ 我的未知未知】即自动创建" }
if (Test-Path (Join-Path $MEMORY_CENTER "未知未知/悬置区.md")) { Write-Ok "悬置区落点存在(未知未知/悬置区.md)" }
else { Write-Info "悬置区.md 不存在——AI 触发未知未知时自动创建,或手动建空文件" }

Write-Step "[7/8] 体检:新功能/版本(缺则指路,不代装)..."
if (-not (Test-Path (Join-Path $MEMORY_CENTER "成就系统"))) {
    Write-Info "未装成就系统 → 用布洛陀安装包安装"
} else { Write-Ok "成就系统已装" }
if (-not (Test-Path (Join-Path $MEMORY_CENTER "记忆琥珀"))) {
    Write-Info "未装记忆琥珀 → 布洛陀安装包 step6.5-amber-install 安装"
} else {
    Write-Ok "记忆琥珀已装"
    if (Test-Path (Join-Path $MEMORY_CENTER "记忆琥珀/永久收藏")) { Write-Ok "记忆琥珀为双轨新版" }
    else { Write-Info "记忆琥珀是旧版(无「永久收藏」双轨) → 用布洛陀安装包升级" }
}
Write-Info "如需最新 Skill:去网盘下最新布洛陀安装包(含最新 skill,可单独装)"

Write-Step "[8/8] 自验证..."
$AG_OK = Test-Path $AGENTS
$SIGN_OK = "no"
if ($AG_OK) { if (Select-String -Path $AGENTS -Pattern "你的 ZCode" -Quiet) { $SIGN_OK = "yes" } }
$HK_FILE = "no"; if ((Test-Path $HOOK_DST) -and (Get-Item $HOOK_DST).Length -gt 0) { $HK_FILE = "yes" }
$HK_REG = "no"; if ((Test-Path $CONFIG) -and (Select-String -Path $CONFIG -Pattern "route_unknown_unknown.py" -Quiet)) { $HK_REG = "yes" }
$EN_OK = "no"
if ((Test-Path $CONFIG) -and $PY) {
    $pyScript2 = @'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("yes" if d.get("hooks", {}).get("enabled") else "no")
'@
    $tmpPy2 = Join-Path $TMP_DIR "zcw_enabled_check_$PID.py"
    [System.IO.File]::WriteAllText($tmpPy2, $pyScript2, (New-Object System.Text.UTF8Encoding($false)))
    $EN_OK = (& $PY $tmpPy2 $CONFIG | Select-Object -Last 1).Trim()
    Remove-Item $tmpPy2 -Force -ErrorAction SilentlyContinue
}
Write-Host "  AGENTS.md: $AG_OK | 署名ZCode: $SIGN_OK | skills软链: $GLOBAL:SK/$($SKILLS.Count) | 钩子脚本: $HK_FILE | 钩子注册: $HK_REG | hooks启用: $EN_OK | 跳过: $GLOBAL:FAIL"
if ($AG_OK -and $SIGN_OK -eq "yes" -and $GLOBAL:SK -ge 8 -and $HK_FILE -eq "yes" -and $HK_REG -eq "yes" -and $EN_OK -eq "yes" -and $GLOBAL:FAIL -eq 0) {
    Write-Host "=== [OK] ZCode 接入完成!新开 ZCode 会话即生效 ===" -ForegroundColor $GREEN
    Write-Host "    验证:新会话回复应带【意图分类】开头、署名「—— 你的 ZCode 🧩」;说「我美吗」测记忆唤醒;说「小美」测轻量模式。" -ForegroundColor $GREEN
    Write-Host "    待办:{称呼}占位符替换(若新装了 AGENTS.md 骨架)——对话中告诉 AI 你的称呼即可。" -ForegroundColor $GREEN
} else {
    Write-Host "[X] 接入不完整: AGENTS=$AG_OK 署名=$SIGN_OK skills=$GLOBAL:SK(期望>=8) 钩子=$HK_FILE/$HK_REG enabled=$EN_OK 跳过=$GLOBAL:FAIL" -ForegroundColor $RED
    Write-Host "    请检查上方 [skip]/[X]/[!] 项(多为源文件缺失=布洛陀未装全,或 config.json 需手动补)。" -ForegroundColor $RED
    exit 1
}
