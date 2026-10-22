# ============================================================
# verify.ps1 — 布洛陀安装包 接入自检 v1.0 (Windows·只读·不改任何文件)
# 用法: powershell -ExecutionPolicy Bypass -File verify.ps1 [-Platform <端ID>]
#       -Platform qodercn → 落点检查按该端 capability.yaml 的 config_root（v2.0.1·多端）
#       $env:MEMORY_CENTER="D:\path" ; powershell ... -File verify.ps1 (自定义记忆中心)
# 检查项: 0)数据污染(Find-Python 解析真实 python.exe) 1)系统文件 2)规则三层
#         3)记忆Skill 4)安装包干净度 5)版本锚点
#         3.1c)33 题两源对账(题库↔答题页逐字相等·C06)
#         3.1d)自陈待办在位对账(承诺面「写入 X.py→随包」必须有实物·C32 通用闸)
#         3.6)派发心跳(advisory 显形·不计分·注册≠派发)
#         3.7)分身链路(抽卡→落卡→碰撞 dry-run·包能力检查·隔离沙箱)
# 退出码 0=全过 非0=有问题
# 设计: 与 verify.sh 同构的平台分支；python 解析用 Find-Python 规范
#       (where.exe+正则+跳 WindowsApps Store 别名, 禁裸 python/Get-Command)
#       3.7 复用包内 twin_chain_check.py（⛔不触碰用户真实卡库·不要求已装 Phase B）
# ============================================================
param([string]$Platform = "")
$ErrorActionPreference = "Stop"
$PASS = 0; $FAIL = 0; $PEND = 0
function ok($t){ Write-Host "  [PASS] $t" -ForegroundColor Green; $script:PASS++ }
function no($t){ Write-Host "  [FAIL] $t" -ForegroundColor Red; $script:FAIL++ }
# 三态分账（2026-10-22 R9·条文70「自检报告三态分账律」）：引导段未跑段的缺失=⏳待办非🔴失败
function pend($t){ Write-Host "  [PEND] $t" -ForegroundColor DarkYellow; $script:PEND++ }
function miss($t){ if (-not $script:STEP5) { pend ($t + "（AI引导段未跑·答题后重跑即消）") } else { no $t } }

# 解析真实 python.exe 绝对路径，跳过 Windows Store 应用执行别名，抗 Get-Command 畸形前缀
# 2026-09-17 收口：优先 WorkBuddy 自带解释器绝对路径（INSTALL.md 反复强调的落点），
# 再回退 PATH（where.exe）。原实现只走 PATH —— 装了 WorkBuddy 但自带 python 未进 PATH 时
# 被误判 "未找到可用 python" → 端用户正确安装也会看到 FAIL（T15 端到端演练检出）。
function Find-Python {
  $found = $null
  # 1) WorkBuddy 自带解释器（单真源·与 INSTALL.md 同口径）
  try {
    $bundled = @()
    $base = Join-Path $HOME ".workbuddy\binaries\python\versions"
    if (Test-Path $base) { $bundled = @(Get-ChildItem -Path $base -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName) }
    foreach ($p in @($bundled | Sort-Object -Descending)) {
      if ($p -match 'WindowsApps\python') { continue }
      if (Test-Path $p) {
        $null = & $p --version 2>$devnull
        if ($LASTEXITCODE -eq 0) { $found = $p; break }
      }
    }
  } catch {}
  if ($found) { return $found }
  # 2) Get-Command 解析（跨平台·比 where.exe 更可靠）
  foreach ($cand in @("python", "python3")) {
    try {
      $c = Get-Command $cand -ErrorAction SilentlyContinue
      if ($c -and $c.Source -and $c.Source -notmatch 'WindowsApps') {
        $null = & $c.Source --version 2>$devnull
        if ($LASTEXITCODE -eq 0) { $found = $c.Source; break }
      }
    } catch {}
  }
  if ($found) { return $found }
  # 3) 回退 PATH 解析（where.exe）
  foreach ($cand in @("python", "python3", "py")) {
    try {
      $raw = @(& where.exe $cand 2>$devnull)
      foreach ($ln in $raw) {
        foreach ($m in [regex]::Matches($ln, '[A-Za-z]:\\.*?python\.exe')) {
          $p = $m.Value
          if ($p -match 'WindowsApps\\python') { continue }   # 跳过 Store 应用执行别名
          if (Test-Path $p) {
            $null = & $p --version 2>$devnull
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

$PKG_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$MC = if ($env:MEMORY_CENTER) { $env:MEMORY_CENTER } else { Join-Path $HOME "记忆共享中心" }
# STEP5 判定必须挂 $MC 赋值之后（R9 首轮 runner 逮到时序倒置：挂函数区时 $MC 未定义·Stop 模式 Join-Path 空参崩·教训=判定行跟着数据源走）
$script:STEP5 = Test-Path (Join-Path $MC '.install\step5-done.md')

# ── v2.0.1 多端配置根（与 verify.sh --platform 同语义；不传=~/.workbuddy 向后兼容）──
if ($Platform -ne "") {
  $capYml = Join-Path $PKG_ROOT ("adapters\" + $Platform + "\capability.yaml")
  if (-not (Test-Path $capYml)) { Write-Host "❌ -Platform $Platform ：$capYml 不存在（占位端未接入）"; exit 2 }
  $mCap = [regex]::Match((Get-Content $capYml -Raw -Encoding UTF8), '(?m)^config_root:\s*"?([^"\r\n]+)"?')
  $CONFIG_ROOT = if ($mCap.Success) { $mCap.Groups[1].Value.Trim('"') } else { "" }
} else { $CONFIG_ROOT = "~/.workbuddy" }
if ($CONFIG_ROOT -eq "") { $CONFIG_ROOT = "~/.workbuddy" }
$CFG_DIR = if ($CONFIG_ROOT.StartsWith("~")) { Join-Path $HOME ($CONFIG_ROOT.Substring(1).TrimStart('\', '/')) } else { $CONFIG_ROOT }
Write-Host ("=== 布洛陀安装包 接入自检 | 记忆中心: $MC | 端: " + $(if ($Platform -ne '') { $Platform } else { 'workbuddy' }) + " 配置根: $CONFIG_ROOT ===") -ForegroundColor Cyan

# 🔴 2026-10-21 根治(Win用户反馈缺陷②·对齐 verify.sh L112)：本自检跑包内 python
#    检查器会 import 兄弟 .py → 自造 __pycache__ → §4 pkg_cleanliness 判污染 = 假红。
#    从产生源封死：环境级禁写字节码，覆盖本脚本全部 & $py 调用。
$env:PYTHONDONTWRITEBYTECODE = "1"

# 0) 数据污染检测（dry-run 只读·Find-Python 解析）
#    域外降级判据（2026-09-30 终检·**结构性**·⛔无作者侧字面量）：
#      本项判据=「端用户记忆中心不应含随包样例数据」。若 MC 恰为**安装包源码树之祖先**
#      （包住在 MC 之下）＝源码机自检；而指纹池正是从该卡库生成 ⇒ 全量命中属**判据域外**
#      （非缺陷）→ 降级为 advisory。端用户机（包解压位与记忆中心分离）行为**完全不变**。
$mcN = $MC.TrimEnd('\','/'); $pkgN = $PKG_ROOT.TrimEnd('\','/')
$MCOwnsPkg = ($pkgN.StartsWith($mcN + '\')) -or ($pkgN.StartsWith($mcN + '/'))
$py = Find-Python
if ($py) {
  $fp = Join-Path $PKG_ROOT "references\integrity-fingerprints.json"
  $tpl = Join-Path $PKG_ROOT "references"
  & $py (Join-Path $PKG_ROOT "data_contamination_check.py") --memory-root $MC --fingerprints $fp --template-root $tpl | Out-Null
  if ($LASTEXITCODE -eq 0) { ok "数据污染检测: 无污染" }
  elseif ($MCOwnsPkg) { Write-Host "  [i] 数据污染检测: 判据域外·降级（记忆中心即安装包源码树之根 ⇒ 指纹池与本地卡库同源·全量命中属预期）；本项仅对端用户新装记忆中心有意义" -ForegroundColor Cyan }
  else { no "数据污染检测: 命中污染(需 --apply 清理或人工核对)" }
} else { no "未找到可用 python.exe(跳过污染检测)" }

# 1) 系统文件（发布包模板齐全）+ 记忆中心核心层
#    2026-09-17 童灵根治：原查 $MC/SOUL.md 等与 step5 契约不符——SOUL/IDENTITY/USER/MEMORY
#    是 WorkBuddy 平台专属落点（~/.workbuddy/），非记忆中心根。已与 verify.sh 同口径。
foreach ($e in @(@("references\templates\SOUL.md", "人格模板"), @("references\templates\IDENTITY.md", "身份模板"), @("references\templates\USER.md", "用户画像模板"))) {
  $rel = $e[0]; $lb = $e[1]
  $p = Join-Path $PKG_ROOT $rel
  if ((Test-Path $p) -and ((Get-Item $p).Length -gt 0)) { ok "发布模板 ${lb}: $rel" } else { no "发布模板 ${lb}: $rel (缺失)" }
}
$coreMd = Join-Path $MC "核心层\CORE.md"
if ((Test-Path $coreMd) -and ((Get-Item $coreMd).Length -gt 0)) { ok "记忆中心 核心层: CORE.md" } else { miss "记忆中心 核心层: CORE.md (缺失/为空)" }

# 1.5) 平台系统文件（step5 契约落点 = 端配置根 $CONFIG_ROOT\）
#     2026-09-17 新增·2026-09-30 多端化：SOUL/IDENTITY/USER/MEMORY 写入端配置根目录（WB=.workbuddy、Qoder CN=.qoder-cn），而非记忆中心根。
foreach ($rel in @("SOUL.md", "IDENTITY.md", "USER.md")) {
  $p = Join-Path $CFG_DIR $rel
  if ((Test-Path $p) -and ((Get-Item $p).Length -gt 0)) { ok "平台系统文件: $CONFIG_ROOT/$rel" } else { miss "平台系统文件: $CONFIG_ROOT/$rel (缺失)" }
}

# 1.6) 端功能面 twin_surface（条文33·fail-closed·与 verify.sh §1.6 同口径·2026-10-11 Q1补Win验收对等）
#   null-safe：$capYml 仅 -Platform 分支赋值，不带 platform 时为 null→Test-Path 抛(真机T2实证)，故自算默认端路径
$twinPlat = $(if ($Platform -ne '') { $Platform } else { 'workbuddy' })
$twinCap = if ($capYml) { $capYml } else { Join-Path $PKG_ROOT ("adapters\" + $twinPlat + "\capability.yaml") }
if ($twinCap -and (Test-Path $twinCap)) {
  $capTxt = Get-Content $twinCap -Raw -Encoding UTF8
  if ($capTxt -match "twin_surface:") { ok "分身功能面: twin_surface 已声明" } else { no "分身功能面: twin_surface 未声明（条文33·fail-closed）" }
} else { no "分身功能面: capability.yaml 缺失（$twinCap）" }

# 1.7) 接入率漂移附加检查（platform_adaptation_check.py --src·与 verify.sh §1.7 同口径·漂移advisory不拦）
$pac = Join-Path $PKG_ROOT "platform_adaptation_check.py"
if ($py -and (Test-Path $pac)) {
  $platArg = $(if ($Platform -ne '') { $Platform } else { 'workbuddy' })
  $pacOut = & $py $pac --src $platArg 2>&1
  if ($LASTEXITCODE -eq 0) { ok "接入率漂移: 无漂移（platform_adaptation_check.py --src $platArg）" }
  else {
    Write-Host "  [i] 接入率漂移: 有漂移（rc=$LASTEXITCODE）—— 不影响本文件三面判据；发布前请核对" -ForegroundColor Yellow
    ($pacOut -split "`n") | Where-Object { $_.Trim() } | Select-Object -First 8 | ForEach-Object { Write-Host "      $_" -ForegroundColor Yellow }
  }
}

# 2) 规则三层
foreach ($rel in @("记忆规则/用户基本规则-铁律版.md", "记忆规则/用户基本规则-摘要版.md")) {
  $rp = Join-Path $MC $rel; if ((Test-Path $rp) -and ((Get-Item $rp).Length -gt 0)) { ok "规则三层 $rel" } else { no "规则三层 $rel (缺失/为空)" }
}

# 3.0) Skill 落点三口径判定（2026-10-21 双端补腿·与 verify.sh §3.0 同 verify_pair_checks 源）
#      旧 ps1 仅目录名直配（Test-Path），sh 10-03 已根治中文别名目录误报——孪生同判据单端演化
#      正是条文68孪生同构律针对的病形活例；判据住 py，本壳只调用。
$VPC = Join-Path $PKG_ROOT "references\scripts\verify_pair_checks.py"
function Test-SkillPresent($pkgSkillDir, $rootDir) {
  if (-not $py -or -not (Test-Path $VPC)) { return 2 }
  & $py $VPC skill-present "$pkgSkillDir" "$rootDir" | Out-Null
  $rc = $LASTEXITCODE
  if ($rc -eq 0 -or $rc -eq 1) { return $rc } else { return 2 }
}

# 3) 记忆 Skill（2026-09-21 改「名单同源」：从包内 references/skills/ 动态枚举，⛔不再硬编码
#    9 个名字——硬编码导致新增 Skill 长期不在验证覆盖内=装了没装都不报）
$skillSrc = Join-Path $PKG_ROOT "references\skills"
$names = @()
if (Test-Path $skillSrc) {
  $names = Get-ChildItem -Path $skillSrc -Directory | Where-Object { Test-Path (Join-Path $_.FullName "SKILL.md") } | ForEach-Object { $_.Name }
}
$SKILLS_TOTAL = $names.Count
$FSK = 0; $SKI = 0
foreach ($s in $names) {
  switch (Test-SkillPresent (Join-Path $skillSrc $s) (Join-Path $MC "技能配置")) {
    0 { $FSK++ }
    1 { }
    default { $SKI++ }
  }
}
if ($SKI -gt 0) { no "记忆Skill落点判定: 仪器未跑 $SKI 件（python/verify_pair_checks 不可用·⛔失明期间不得代报缺失——与 verify.sh §3 同判据同口径）" }
elseif ($SKILLS_TOTAL -gt 0 -and $FSK -eq $SKILLS_TOTAL) { ok "记忆Skill: $FSK/$SKILLS_TOTAL（名单源=包内 references/skills/·三口径=verify_pair_checks 双端单源）" }
elseif ($SKILLS_TOTAL -eq 0) { no "记忆Skill: 包内 references/skills/ 无可枚举 Skill（包结构异常）" }
else { no "记忆Skill仅 $FSK/$SKILLS_TOTAL（比对包内 references/skills/ 与 技能配置/）" }

# 3.1) systemlog 写时守护双轨在位（2026-10-11 Win对等任务卡·mac .sh + Win .ps1 配对）
$SLD = Join-Path $PKG_ROOT "references\skills\system-logger\scripts"
$slMiss = @()
foreach ($f in @("systemlog_watch.sh","install_watch.sh","systemlog-watch.ps1","systemlog-install-task.ps1")) {
  if (-not (Test-Path (Join-Path $SLD $f))) { $slMiss += $f }
}
if ($slMiss.Count -eq 0) { ok "systemlog看守双轨: 包内 4/4 在位（mac .sh ×2 + Win .ps1 ×2）" }
else { no "systemlog看守缺包内件: $($slMiss -join ',')" }
$slDst = Join-Path $MC "技能配置\system-logger\scripts"
if (-not (Test-Path (Join-Path $MC "技能配置\system-logger\SKILL.md"))) { Write-Host "  [i] system-logger 未装此记忆中心——跳过 Win 件落盘检查" }
elseif (-not (Test-Path (Join-Path $slDst "append_log_entry.py"))) { Write-Host "  [i] system-logger scripts 面未部署（桩/装机中途态）——跳过 Win 件落盘检查（T2 仿真守卫·2026-10-19 Win真机腿反例根治）" }
elseif ((Test-Path (Join-Path $slDst "systemlog-watch.ps1")) -and (Test-Path (Join-Path $slDst "systemlog-install-task.ps1"))) { ok "systemlog看守 Win 件装机落盘 2/2（deploy_skills 逐目录复制实证）" }
else { no "systemlog看守 Win 件装机未落盘（$slDst 缺 .ps1）" }

# 3.1b) 装后语法面全量扫描（2026-10-11 _fill转义地雷根治卡 R2 verify腿·存量面）
if ($py -and (Test-Path (Join-Path $PKG_ROOT "fill_syntax_scan.py"))) {
  & $py (Join-Path $PKG_ROOT "fill_syntax_scan.py") "$MC" --quiet *> $null
  if ($LASTEXITCODE -eq 0) { ok "装后语法面: 装机面 .py/.json 编译级全绿" }
  else { no "装后语法面有雷（跑 fill_syntax_scan.py $MC 看逐行明细）" }
} elseif (-not (Test-Path (Join-Path $PKG_ROOT "fill_syntax_scan.py"))) { no "fill_syntax_scan.py 缺件（根治卡 R2 腿未入包）" }
else { Write-Host "  [i] 装后语法扫描: 跳过（无 python）" -ForegroundColor Cyan }

# 3.1c) 33 题两源对账（C06·与 verify.sh §3.1c 同口径——⛔只挂 mac 端＝Windows 端零防线，
#       先例教训见 pkg_cleanliness_check 头注「原 PS 侧只查 1 类」）
if ($py -and (Test-Path (Join-Path $PKG_ROOT "questionnaire_sync_check.py"))) {
  & $py (Join-Path $PKG_ROOT "questionnaire_sync_check.py") --quiet *> $null
  if ($LASTEXITCODE -eq 0) { ok "33 题两源对账: 题库↔答题页 33/33 逐字相等" }
  else { no "33 题两源分叉（跑 questionnaire_sync_check.py 看逐题明细·修完前 step4 第1关不可信）" }
} elseif (-not (Test-Path (Join-Path $PKG_ROOT "questionnaire_sync_check.py"))) { no "questionnaire_sync_check.py 缺件（C06 对账腿未入包）" }
else { Write-Host "  [i] 33 题两源对账: 跳过（无 python）" -ForegroundColor Cyan }

# 3.1d) 自陈待办在位对账（C32·与 verify.sh §3.1d 同口径——通用闸：承诺面 md 写「写入 X.py→随包」
#       则 X 必须在包内；CHANGELOG／golden_samples／fixtures＝记录面跳过并计数显形）
if ($py -and (Test-Path (Join-Path $PKG_ROOT "todo_landing_check.py"))) {
  & $py (Join-Path $PKG_ROOT "todo_landing_check.py") --quiet *> $null
  if ($LASTEXITCODE -eq 0) { ok "自陈待办对账: 承诺面待办全部有实物（或已带 reason 登记）" }
  else { no "自陈待办无实物（跑 todo_landing_check.py 看逐条·待办挂空＝文档与实盘脱钩）" }
} elseif (-not (Test-Path (Join-Path $PKG_ROOT "todo_landing_check.py"))) { no "todo_landing_check.py 缺件（C32 通用闸未入包）" }
else { Write-Host "  [i] 自陈待办对账: 跳过（无 python）" -ForegroundColor Cyan }

# 3.2) Skill 软链接（step7 检查清单 #12·N6）
#      2026-09-17 新增：原双端均不验，契约与验证器脱节。
#      2026-09-21：名单同步改为动态枚举（同 §3）。
#      原生 Windows 建 SymbolicLink 需开发者模式/管理员，step6 已声明降级（WARN 不瞒报）
$skillHome = Join-Path $CFG_DIR "skills"
if (Test-Path $skillHome) {
  $linkOk = 0
  foreach ($s in $names) {
    if (Test-Path (Join-Path $skillHome $s)) { $linkOk++ }
  }
  if ($SKILLS_TOTAL -gt 0 -and $linkOk -eq $SKILLS_TOTAL) { ok "Skill软链接: $linkOk/$SKILLS_TOTAL 有效（$CONFIG_ROOT\skills\）" }
  else { Write-Host "  [WARN] Skill软链接 $linkOk/$SKILLS_TOTAL（需开发者模式/管理员；step6 降级护栏已声明）" -ForegroundColor Yellow }
} else {
  Write-Host "  [i] $CONFIG_ROOT\skills\ 不存在·跳过软链接检查（未装 Skill 或其他落点）" -ForegroundColor Cyan
}
# 3.5) 脚本体系部署（可选·装了才查；未装「脚本中心/」则跳过不计分）
$scriptCenter = Join-Path $MC "脚本中心\rule_fragment_inject.py"
if (Test-Path $scriptCenter) {
  ok "脚本中心: rule_fragment_inject.py 已部署"
  if (Test-Path (Join-Path $CFG_DIR "hooks\rule\rule_fragment_inject.py")) { ok "运行钩子: $CONFIG_ROOT\hooks\rule\rule_fragment_inject.py" } else { no "运行钩子: $CONFIG_ROOT\hooks\rule\rule_fragment_inject.py (缺失)" }
  if (Test-Path (Join-Path $CFG_DIR "hooks\rule\rule_triggers.yaml")) { ok "触发规格: $CONFIG_ROOT\hooks\rule\rule_triggers.yaml" } else { no "触发规格: $CONFIG_ROOT\hooks\rule\rule_triggers.yaml (缺失)" }
  # 2026-09-21 根治：核查口径改为「与安装共用同一数据源」——直接调 install_scripts.py --verify
  # （读其 ROSTER 数组），不再在 verifier 里另抄一份钩子清单——另抄一份正是「登记了却没装文件」的复发土壤。
  $IS = Join-Path $PKG_ROOT "install_scripts.py"
  if ((Test-Path $IS) -and $py) {
    if ($Platform -ne "") { & $py $IS --verify $MC --platform $Platform | Out-Null } else { & $py $IS --verify $MC | Out-Null }  # v2.0.1 透传端
    if ($LASTEXITCODE -eq 0) { ok "钩子总表: 全部落盘并已注册（数据源=install_scripts.py ROSTER）" }
    else { no "钩子总表: 有钩子未落盘/未注册，或规则数据缺失（跑 python install_scripts.py --verify `"<记忆中心>`" 看明细）" }
  } else { no "install_scripts.py 缺失（无法核对钩子总表）" }

  # 3.6) 派发心跳（advisory 显形·注册 ≠ 派发·2026-09-21 端用户连坐案例）
  #      病灶：第三方插件 hooks.json 格式非法 → 宿主整事件连坐停摆 → 钩子静默失效，
  #      注册态检查（§3.5）零症状。心跳证据=钩子被真派发时自动留痕
  #      （hook_protocol.py import 即留痕；路径单一真源=其 HB_DIR）。
  #      ⛔ 有意不计 FAIL：新鲜度无法区分「停摆」与「用户休假」，假阳性比没有检查更糟。
  $HBC = Join-Path $PKG_ROOT "references\scripts\guard_heartbeat_check.py"
  if ($py -and (Test-Path $HBC)) {
    $env:MEMORY_CENTER = $MC
    $hbLine = & $py $HBC --brief 2>$null
    Remove-Item Env:\MEMORY_CENTER -ErrorAction SilentlyContinue
    if ($hbLine) { Write-Host "  [i] $hbLine" -ForegroundColor Cyan }
  }
} else {
  Write-Host "  [i] 脚本体系未安装(脚本中心/缺失)·跳过硬墙部署检查" -ForegroundColor Cyan
}

# 3.7) 数字分身·卡链路三步（抽卡→落卡→碰撞·2026-09-30 终检·件4 收官）
#      病灶：数字分身完整版 Phase B 交付「抽卡→落卡→碰撞」链路，原六项自检**零覆盖**
#      ⇒ 装了但链路断=不可见（同族「装了没装都不报」）。本项为**包能力检查**：在隔离沙箱内复制
#      **包内**引擎跑真链路 ⇒ ⛔不要求端用户已装 Phase B、⛔不触碰其真实卡库；
#      判据由 twin_chain_check.py 自证（三步逐步 exit 0 + INDEX.md 真写出）。
#      rc：0=全绿 3=包内引擎缺失(包结构缺陷) 1=链路断 2=参数错。
$TCC = Join-Path $PKG_ROOT "references\scripts\twin_chain_check.py"
if ($py -and (Test-Path $TCC)) {
  & $py $TCC --pkg-root $PKG_ROOT --memory-center $MC --quiet | Out-Null
  $tccRc = $LASTEXITCODE
  switch ($tccRc) {
    0 { ok "分身链路: 抽卡→落卡→碰撞 三步 dry-run 全绿（隔离沙箱·零触真实卡库）" }
    3 { no "分身链路: 包内引擎缺失（references/知识联邦引擎-min/scripts）——包结构缺陷" }
    1 { no "分身链路: 三步 dry-run 未全绿（跑 python references/scripts/twin_chain_check.py --pkg-root `"$PKG_ROOT`" 看明细）" }
    default { no "分身链路: 检查器异常退出 rc=$tccRc" }
  }
} elseif (-not $py) {
  no "未找到可用 python.exe(跳过分身链路检查)"
} else {
  no "分身链路检查器缺失: references/scripts/twin_chain_check.py"
}

# 3.7b) 数字分身·恒驻切片链 dry-run（2026-10-11 包自检⑬·与 verify.sh §3.7b 同口径·同病同治）
$SCC = Join-Path $PKG_ROOT "references\scripts\slice_chain_check.py"
if ($py -and (Test-Path $SCC)) {
  & $py $SCC --pkg-root $PKG_ROOT --quiet | Out-Null
  $sccRc = $LASTEXITCODE
  switch ($sccRc) {
    0 { ok "切片链: 规格书→生成器→六片 ⑬ dry-run 五断言全绿（包骨架沙箱·零触真实档案）" }
    3 { no "切片链: 包内生成器/骨架模板缺失——包结构缺陷" }
    1 { no "切片链: ⑬ 五断言未全绿（跑 python references/scripts/slice_chain_check.py --pkg-root `"$PKG_ROOT`" 看明细）" }
    default { no "切片链: 检查器异常退出 rc=$sccRc" }
  }
} else {
  no "切片链检查器缺失: references/scripts/slice_chain_check.py"
}

# 3.8) 养成链在位（答题→计分→蒸馏→上线·五要素静态断言·与 verify.sh §3.8 同口径）
$lcm = 0
if (-not (Test-Path (Join-Path $pkgN "references/digital-twin/hexaco/自建100题-答题页-v1.html"))) { $lcm = 1 }
if (-not (Test-Path (Join-Path $pkgN "references/digital-twin/k2-slice-generator/k2_slice_generator.py"))) { $lcm = 1 }
$is = Join-Path $pkgN "install_scripts.py"
if (-not (Test-Path $is) -or -not (Select-String -Path $is -Pattern '"hexaco":' -Quiet)) { $lcm = 1 }
$im = Join-Path $pkgN "INSTALL.md"
if (-not (Test-Path $im) -or -not ((Select-String -Path $im -Pattern '分身养成链' -Quiet) -and (Select-String -Path $im -Pattern '蒸馏目标层' -Quiet))) { $lcm = 1 }
# 2026-10-10 hexaco 终态穷举断言（与 verify.sh §3.8 同口径·防作者侧回流）
# P28裁决(2026-10-18)：官方壳页移出包面——Win腿清单同步7件（注释⛔入 @() 单行表达式，PS 无行中括号内注释·T1 实证）
$hx = Join-Path $pkgN "references/digital-twin/hexaco"
$hxExp = @('自建100题-分身版-题库-v1.md','自建100题-答题页-v1.html','HEXACO-100完整版-官方中文-答题卡.md','ScoringKeys_100.pdf','hexaco_selfbuild_scorer.py','hexaco_official_scorer.py','hexaco_official_keytable-100.json')
if (Test-Path $hx) {
  # 双向对账（与 verify.sh §3.8 同口径）：清单里有→包内必须在位；包内有→清单里必须声明
  $hxBad = @(Get-ChildItem $hx -File | Where-Object { $hxExp -notcontains $_.Name } | ForEach-Object { "白名单外:$($_.Name)" })
  foreach ($hd in $hxExp) { if (-not (Test-Path (Join-Path $hx $hd))) { $hxBad += "缺:$hd" } }
  # 引导面断言：脚本在包但没人被引导去跑=死件
  # ⚠️ 计分器「在位」不再在此逐件硬编码——题库 §八 第4条那句自陈待办已由 §3.1d 通用闸覆盖，
  #    此处的清单是**终态声明表**（回流防线），两份并存各管各的判据，⛔不重复记同一本账
  if (-not (Select-String -Path $im -Pattern 'hexaco_selfbuild_scorer' -Quiet)) { $hxBad += '缺:INSTALL.md 未引导跑自建计分器' }
  if (-not (Select-String -Path $im -Pattern 'hexaco_official_scorer' -Quiet)) { $hxBad += '缺:INSTALL.md 未引导跑官方计分器' }
  if ($hxBad.Count -gt 0) { $lcm = 1; no ("hexaco终态对账: " + ($hxBad -join ' ')) }
}
if ($lcm -eq 0) { ok "养成链在位: 答题页+造芯件+部署声明+INSTALL指引+蒸馏清单 五要素齐" }
else { no "养成链缺件: 答题页/造芯件/部署声明/INSTALL指引/蒸馏清单 有缺失" }

# 3.9) 检查点链完整性（改造③·2026-10-13·补条文39 明载欠账——与 verify.sh §3.9 同口径镜像·条文61 L1 脚本配对腿）
#      判据=$MC\.install\stepN-done.md 链（step1~step8 含 6.5）连续：
#      中段断裂=no() 报红列断裂点（进度不可信）；尾部缺失=[i] advisory（verify 跑在 step7 时点·step8 未到=防假红）
#      无 .install=主线未开工显形跳过；占位防（39§4）done<16字节=advisory（⛔无实证不升硬判）
#      ⛔AI 对话段内容 quality 不脚本化（39§3）——本节只对账检查点文件存在性与连续性
$chain = @('step1','step2','step3','step4','step5','step6','step6.5','step7','step8')
$instDir = Join-Path $MC '.install'
if (Test-Path $instDir) {
  $present = @($chain | Where-Object { Test-Path (Join-Path $instDir ($_ + '-done.md')) })
  $lastIdx = -1
  for ($ci = 0; $ci -lt $chain.Count; $ci++) { if ($present -contains $chain[$ci]) { $lastIdx = $ci } }
  $gaps = @()
  for ($ci = 0; $ci -lt $lastIdx; $ci++) { if (-not ($present -contains $chain[$ci])) { $gaps += $chain[$ci] } }
  if ($gaps.Count -gt 0) { no ("检查点链断裂: 主线缺 " + ($gaps -join ',') + "（后续步骤已落 done 而前置缺失=进度不可信·补做缺失步骤后重验·判据源=条文39）") }
  elseif ($lastIdx -lt 0) { Write-Host "  [i] 检查点链: .install 未落任何步骤检查点（安装主线未开跑·零步落账——条文39①）" -ForegroundColor Cyan }
  elseif ($lastIdx -lt 8) { Write-Host ("  [i] 检查点链: 连续至 " + $chain[$lastIdx] + "（尾部未落=step7 跑 verify 时 step8 尚未来·正常时点）") -ForegroundColor Cyan }
  else { ok "检查点链完整性: step1~step8 含 6.5 九段全在·无断裂" }
  $tiny = @(Get-ChildItem $instDir -Filter 'step*-done.md' -File | Where-Object { $_.Length -lt 16 } | ForEach-Object { $_.Name })
  if ($tiny.Count -gt 0) { Write-Host ("  [i] 检查点疑似占位（条文39§2: 须为实查结果非「已完成」三字）: " + ($tiny -join ' ')) -ForegroundColor Cyan }
} else {
  Write-Host ("  [i] 检查点链: 未见 " + $instDir + "（安装主线未开始·对账跳过）") -ForegroundColor Cyan
}

# 4) 安装包干净度（发布卫生·单一真源=pkg_cleanliness_check.py·与 verify.sh §4 同口径）
#    2026-09-17 童灵根治：原仅查 1 类（公开署名）且 PS5.1 无BOM中文易假阴性 → 改调 python 单源。
$DIRT = 0
$cleaner = Join-Path $PKG_ROOT "references\scripts\pkg_cleanliness_check.py"
if (-not $py) {
  no "未找到可用 python.exe(跳过干净度检查)"; $DIRT = 1
} elseif (Test-Path $cleaner) {
  & $py $cleaner --pkg-root $PKG_ROOT --exclude-runtime   # 2026-10-22 R9：装后自检排除装机过程出生物(lock/pycache)·发版侧不传
  if ($LASTEXITCODE -ne 0) { no "安装包干净度: 检查器报污染（上方 [FAIL] 行=分类明细·本汇总按检查器级计 1 项·B6 口径）"; $DIRT = 1 }
} else { no "卫生检查器缺失: references/scripts/pkg_cleanliness_check.py"; $DIRT = 1 }
$compat = Join-Path $PKG_ROOT "references\scripts\platform_compat.py"
if ($py -and (Test-Path $compat)) {
  & $py $compat --only-author-path $PKG_ROOT | Out-Null
  if ($LASTEXITCODE -ne 0) { no "安装包含未声明的作者侧路径引用"; $DIRT = 1 }
}
if ($DIRT -eq 0) { ok "安装包干净度: 8 类卫生项全过 + 无未声明作者侧路径" }

# 4.5) 装后双拼产物扫描（2026-10-10 十一轮·与 verify.sh §4.5 同口径·装机面）
$integrity = Join-Path $PKG_ROOT "references\scripts\path_integrity_check.py"
if ($py -and (Test-Path $integrity)) {
  & $py $integrity --root $MC --quiet | Out-Null
  if ($LASTEXITCODE -ne 0) {
    & $py $integrity --root $MC | Out-Host
    no "装后产物含双拼/占位符残留（上方 [FAIL] 行=明细）"
  } else { ok "装后产物路径完整性: 无双拼形态、无占位符残留" }
}

# 4.6) 目录型骨架在位且非空（C16·与 verify.sh §4.6 同 verify_pair_checks 源·2026-10-21 双端补腿）
if ($py -and (Test-Path $VPC)) {
  $sklOut = (& $py $VPC skeleton $MC 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -eq 0) { ok "目录型骨架在位且非空: $sklOut" } else { miss "目录型骨架: $sklOut" }
} else { no "目录型骨架: 仪器未跑（python/verify_pair_checks 不可用·⛔失明期间不得判无）" }

# 4.7) 摘要版三表占位符闭环（C08·与 verify.sh §4.7 同 verify_pair_checks 源·双向：出厂纯净+装机注入完整）
$tplPath = Join-Path $PKG_ROOT "references\templates\用户基本规则-摘要版.md"
$instSum = Join-Path $MC "记忆规则\用户基本规则-摘要版.md"
if ($py -and (Test-Path $VPC) -and (Test-Path $tplPath)) {
  $st = (& $py $VPC summary-tables $tplPath $instSum 2>&1 | Out-String)
  if ($LASTEXITCODE -eq 2 -or $st -match '^INSTRUMENT=') {
    no "模板纯净: python 腿未跑（仪器未跑·$($st.Trim())·⛔此为仪器故障非包污染）"
  } else {
    $rows = if ($st -match 'ROWS=(\d+)') { [int]$Matches[1] } else { -1 }
    $bad  = if ($st -match 'BAD=(\S+)')  { $Matches[1] } else { "?" }
    $left = if ($st -match 'LEFT=(\S+)') { $Matches[1] } else { "NA" }
    if ($rows -eq 19 -and $bad -eq '0') { ok "模板纯净: 摘要版三表 19 行 38 格全为占位符（⛔不携带任何具体答案·含选项名）" }
    else { no "模板被污染: 摘要版三表应为 19 行全占位符，实测 行数=$rows 非占位符格=$bad（作者/选项内容不得随包出）" }
    if ((Test-Path $instSum) -and $left -ne 'NA') {
      if ([int]$left -gt 0) { miss "摘要版答案未注入: 残留占位符 $left 处（step5 三表逐格替换未完成·用户画像不完整）" }
      else { ok "摘要版答案已注入: 无残留占位符" }
    }
  }
} elseif (-not (Test-Path $tplPath)) { no "模板纯净: 模板缺失 $tplPath（包结构异常）" }
else { no "模板纯净: 仪器未跑（python/verify_pair_checks 不可用·⛔失明期间不得判通过）" }

# 5) 版本锚点（不计分·信息）
$BV = if (Test-Path (Join-Path $MC ".install\version")) { Get-Content (Join-Path $MC ".install\version") -Encoding UTF8 -Raw | ForEach-Object { $_.Trim() } } else { "未知(未完成安装或无锚点)" }
Write-Host "  [i] 布洛陀版本: $BV" -ForegroundColor Cyan

# 5.5) Windows 平台差异告知（不参与评分·信息项）
Write-Host ""
Write-Host "  === Windows 平台差异 ===" -ForegroundColor Cyan
Write-Host "  核心系统（Hook钩子/规则硬墙/未知未知/记忆系统）全部是 .py ---- 三端通用，一样不缺。" -ForegroundColor Green
$scFiles = @(Get-ChildItem -Path (Join-Path $PKG_ROOT "references/scripts") -Recurse -File -EA SilentlyContinue)
$scPy = @($scFiles | Where-Object { $_.Extension -eq ".py" }).Count
$scSh = @($scFiles | Where-Object { $_.Extension -eq ".sh" }).Count
$scYaml = @($scFiles | Where-Object { $_.Extension -eq ".yaml" }).Count
Write-Host "  脚本中心共 $($scFiles.Count) 个：$scPy 个 .py（三端通用）+ $scSh 个 .sh（macOS/Linux 专用）+ $scYaml 个 .yaml（触发规格）"
Write-Host "    那 5 个 .sh：装了 Git for Windows 就能用（用 Git Bash 跑）；没装就忽略，不影响系统。"
Write-Host "  作者本机专用工具（多端巡逻/控制环/git门禁/面板监视）不在包内 ---- 不占你的磁盘。"
Write-Host ""

Write-Host ""
if ($FAIL -eq 0 -and $PEND -eq 0) { Write-Host "=== 自检通过: $PASS 项全过 ===" -ForegroundColor Green; exit 0 }
elseif ($FAIL -eq 0) { Write-Host "=== 机械段全绿: $PASS 项 · 待办 $PEND 项（AI 引导段未完成·答完题回来重跑 verify 即清零·待办不是故障）===" -ForegroundColor DarkYellow; exit 0 }
else { Write-Host "=== 自检未过: $FAIL 项失败(见上) ===" -ForegroundColor Red; exit 1 }
