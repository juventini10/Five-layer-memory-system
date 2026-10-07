#!/bin/bash
# check_package_health.sh — 布洛陀发布前包源质检
# 退出码 0=全通，非0=有FAIL
# 用法：bash check_package_health.sh <包根目录>

PKG="${1:-.}"
[ ! -d "$PKG" ] && echo "用法: $0 <包根目录>" && exit 2

# ⑦ 路径模拟用占位家目录：由 SIM_USER 动态拼接，⛔不写死含姓名的完整路径字面量
# （脱敏门禁判据：/Users/ 后紧跟名字字符即判个人态残留；此处造模拟值只借路径形态，值本身无意义）
SIM_USER="${SIM_USER:-simuser}"
SIM_ROOT_MAC="/Users/${SIM_USER}/个人AI档案"
SIM_ROOT_WIN="C:/Users/${SIM_USER}/个人AI档案"

FAILS=0
echo "=== 布洛陀包源质检 ==="
echo "包路径: $PKG"
echo ""

# ── ① .py Path("~/ 未展开 ──
echo -n "① .py Path(~/ 展开: "
# ① 判据修正：原判据只看 Path("~/ 不看同行是否已 .expanduser() → 合规写法被点红
#   （2026-08-30 实测 title_format_guard.py 带 expanduser 仍报）。假红的门禁=没有门禁。
RES=$(grep -rn 'Path("~/\|Path('\''~/' "$PKG" --include="*.py" 2>/dev/null | grep -v expanduser)
if [ -z "$RES" ]; then
  echo "OK"
else
  echo "FAIL ($(echo "$RES"|wc -l|tr -d ' ')处)"
  echo "$RES" | while read line; do echo "   $line"; done
  FAILS=$((FAILS+1))
fi

# ── ② CHANGELOG 声称 - 仅检查当前版本段 ──
echo -n "② CHANGELOG 含不实声称: "
CHLOG="$PKG/CHANGELOG.md"
ISSUES=""
if [ -f "$CHLOG" ]; then
  # 提取当前版本段（动态读取 version.md，避免硬编码旧版本号）
  # v3.50.1（#32 fail-open根治）：版本读不到不再静默回退硬编码1.4.0（会框错CHANGELOG段=②项静默失效）——显式FAIL
  # 2026-09-20：版本规范 X.Y（功能级）合法——正则放宽兼容两段/三段（原三段硬性=②对 1.6 误报 fail-visible）
  PKG_VER=$(grep -oE 'version:[[:space:]]*"?[0-9]+(\.[0-9]+)?(\.[0-9]+)?' "$PKG/version.md" 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)?(\.[0-9]+)?' | head -1)
  if [ -z "$PKG_VER" ]; then
    ISSUES="$ISSUES\n  version.md 缺失或无版本号——无法确定当前版本段，②项一致性检查未能执行（fail-visible）"
  else
  PKG_VER_ESC=$(printf '%s' "$PKG_VER" | sed 's/\./\\./g')
  CURRENT=$(sed -n "/^## \[$PKG_VER_ESC\]/,/^## \[/p" "$CHLOG")
  while IFS= read -r token; do
    token=$(echo "$token" | tr -d '`')
    # 只查看起来像包内文件的（有.扩展名且不是网址）
    [[ "$token" =~ ^http ]] && continue
    [[ "$token" =~ ^~ ]] && continue
    [[ "$token" =~ \.(sh|ps1|py|md|html|plist)[[:space:]]*$ ]] || continue
    # 2026-09-20：含空格的 token=命令串（如 `bash verify.sh`）非文件名——跳过
    [[ "$token" == *\ * ]] && continue
    # 跳过完全匹配"已删/废弃/移除"的条目（v3.50.1 #34：token含.须转义后入正则·防误匹配任意字符）
    TOKEN_ESC=$(printf '%s' "$token" | sed 's/\./\\./g')
    [[ "$CURRENT" =~ 删除.*$TOKEN_ESC|废弃.*$TOKEN_ESC|移除.*$TOKEN_ESC ]] && continue
    # 2026-09-20：裸文件名 token 允许命中包内任意子目录（references/scripts/ 等落位）——
    #   原只查包根=CHANGELOG 写裸名即误报"声称但不存在"（v1.6 铁律硬墙五件实锤）
    if [ ! -f "$PKG/$token" ] && ! find "$PKG" -name "$token" ! -path "*/.git/*" -print -quit 2>/dev/null | grep -q .; then
      ISSUES="$ISSUES\n  声称但不存在: $token"
    fi
  done < <(echo "$CURRENT" | grep -o '`[^`]*`')
  fi
fi
if [ -z "$ISSUES" ]; then
  echo "OK"
else
  echo "FAIL"
  echo -e "$ISSUES"
  FAILS=$((FAILS+1))
fi

# ── ③ Windows PS1 四件套 ──
echo -n "③ Windows PS1 合规: "
PS1_ISSUES=""
while IFS= read -r ps1; do
  [ -z "$ps1" ] && continue
  if grep -q '\.openclaw' "$ps1" 2>/dev/null; then
    PS1_ISSUES="$PS1_ISSUES\n  $(basename "$ps1"): .openclaw 路径"
  fi
  if grep -q "QClawAmberWatch" "$ps1" 2>/dev/null; then
    PS1_ISSUES="$PS1_ISSUES\n  $(basename "$ps1"): 任务名 QClawAmberWatch"
  fi
  if grep -q '#Requires -Version 7\.0' "$ps1" 2>/dev/null; then
    PS1_ISSUES="$PS1_ISSUES\n  $(basename "$ps1"): #Requires -Version 7.0"
  fi
  if grep -q '& pwsh ' "$ps1" 2>/dev/null && ! grep -q 'Get-Command pwsh' "$ps1" 2>/dev/null && ! grep -q 'powershell\.exe' "$ps1" 2>/dev/null; then
    PS1_ISSUES="$PS1_ISSUES\n  $(basename "$ps1"): pwsh 无回退"
  fi
done < <(find "$PKG" -name "*.ps1" ! -path "*/.git/*" 2>/dev/null)
if [ -z "$PS1_ISSUES" ]; then
  echo "OK"
else
  echo "FAIL"
  echo -e "$PS1_ISSUES"
  FAILS=$((FAILS+1))
fi

# ── ④ sed 占位符覆盖 ──
echo -n "④ sed 覆盖全部占位符类型: "
# 含占位符的文件扩展名
PH_TYPES=$(grep -rl '\[记忆共享中心\]' "$PKG" --include="*.md" --include="*.py" --include="*.sh" --include="*.ps1" 2>/dev/null | sed 's/.*\.//' | sort -u)
# sed/find 覆盖的扩展名 (从安装步骤提取 -name "*.ext" 和 PowerShell -Include "*.ext" 模式)
SED_EXT=$(grep -rho ' -name "\*\.\w\+"\| -Include "[^"]\+"' "$PKG/references/steps/" "$PKG/INSTALL.md" 2>/dev/null | sed 's/.* -name "\*\.//;s/"//;s/.* -Include "\(\*\.\)\?//;s/"//' | sort -u)
SED_EXT="$SED_EXT
ps1"  # PS1 由 PowerShell Get-Content.Replace 处理，等效于 sed
MISSED=""
for ext in $PH_TYPES; do
  echo "$SED_EXT" | grep -qx "$ext" || MISSED="$MISSED $ext"
done
if [ -z "$MISSED" ]; then
  echo "OK"
else
  echo "FAIL (含占位符但sed未覆盖:$MISSED)"
  echo "   占位符类型: $PH_TYPES"
  echo "   sed 覆盖: $SED_EXT"
  FAILS=$((FAILS+1))
fi

# ── ⑤ 已删除（v3.46.0·2026-09-05·编号保留不重用，抄 triwich G3 范本）──
# 原「⑤ 全包硬编码路径」为**恒真检查**：SKIP_DIRS 含 `个人AI档案/`，而 grep 搜索模式就是 `个人AI档案`
#   → 命中行必含该子串 → 被自己的 grep -vE 全部排除 → RES 恒空 → **恒报 OK**。
#   实测（2026-09-04）：布洛陀-安装包 518 处命中 → 过滤后 0 处；与⑧项同构（⑧项已于 v3.44.0 修成三态分级）。
# 处置：⛔不修而**删**——与⑧项职责完全重叠且⑧项判据更严（三态分级：代码类FAIL/文档类not-evaluable/OK），
#   保留⑤项＝两个检查管同一件事·其中一个恒真 → Via Negativa「最好的零件是不存在的零件」。
# 判据源：skill-arch-standard 第452行「从没报过 NOT OK 的检查，它的 OK 不可信」。

# ── ⑥ 占位符格式一致性（禁花括号/expanduser外壳/硬编码）──
echo -n "⑥ 占位符格式一致性: "
FMT_ISSUES=""
# 花括号占位符残留（旧格式，应全部改为方括号）
CURLY=$(grep -rn '{MEMORY_CENTER}\|{WORKBUDDY_HOME}' "$PKG" --include="*.template" --include="*.txt" --include="*.py" --include="*.ps1" 2>/dev/null)
[ -n "$CURLY" ] && FMT_ISSUES="$FMT_ISSUES\n  花括号残留: $(echo "$CURLY"|wc -l|tr -d ' ')处"
# expanduser + [记忆共享中心] —— 原判据见占位符即判死，误伤合规写法（2026-09-20 v1.7 后收窄）
#   装机契约（INSTALL「MC=<记忆共享中心绝对路径>」）：占位符以绝对路径替换 → expanduser("<绝对路径>") 无 ~ 前缀 = no-op，
#   且 expanduser 恰是 Windows 端与替换漏网时的兜底，属防御性写法非危险。
#   真危险形态 = 引号内 ~ 紧跟占位符（替换后成 ~/<绝对路径> 半展开死路径）。只判这个。
#   实测（2026-09-20 布洛陀-安装包 v1.7）：安全形态 102 处 / 真危险 0 处——原判据 102:0 全假阳。
EXPAND=$(grep -rnE 'expanduser\(f?["'\''`]~/\[记忆共享中心\]' "$PKG" --include="*.py" 2>/dev/null)
[ -n "$EXPAND" ] && FMT_ISSUES="$FMT_ISSUES\n  expanduser+占位符半展开死路径: $(echo "$EXPAND"|wc -l|tr -d ' ')处"
# .ps1/.sh/.md 中硬编码'个人AI档案'而非[记忆共享中心]
# ⑥ 判据修正：只有紧跟路径分隔符的才算硬编码路径。文案/注释里出现该词不是路径残留
#   （原判据把 osascript 弹窗文案与目录导航说明全算进来 → 25 处噪音把真雷埋了）
# v3.46.0 补 --include="*.py"（2026-09-05）：原判据只扫 .ps1/.sh/.md，漏 .py——而 clock-loop 自身硬编码
#   多在 .py（skill_eval.py:103 BACKUP_DIR / :3389 output_dir / finalize_report.py:54 / record_fix.py:27 等）。
#   ⛔与⑧项不重叠：⑥判据 `(/|\\)个人AI档案` 比⑧项 `~/个人AI档案/` **更宽**（能逮非 tilde 开头的硬编码，
#   如 Path("/Users/x/个人AI档案")、Windows 反斜杠路径）→ ⑧项逮不到的这类由⑥项兜。
HARD=$(grep -rn '个人AI档案' "$PKG" --include="*.ps1" --include="*.sh" --include="*.md" --include="*.py" 2>/dev/null| grep -E '(/|\\)个人AI档案' | grep -v '\[记忆共享中心\]' | grep -v '记忆琥珀/备份' | grep -v '\.bak' | grep -v 'CHANGELOG.md' | grep -v '个人AI档案/' | grep -v 'source:')
[ -n "$HARD" ] && FMT_ISSUES="$FMT_ISSUES\n  .ps1/.sh/.md/.py硬编码个人AI档案: $(echo "$HARD"|wc -l|tr -d ' ')处"
if [ -z "$FMT_ISSUES" ]; then
  echo "OK"
else
  echo "FAIL"
  echo -e "$FMT_ISSUES"
  FAILS=$((FAILS+1))
fi

# ── ⑦ expanduser+[记忆共享中心] 双重路径模拟 ──
echo -n "⑦ 双重路径模拟(Mac/Win): "
DUP_ISSUES=""
while IFS= read -r file; do
  while IFS= read -r line; do
    lno=$(echo "$line" | cut -d: -f1)
    content=$(echo "$line" | cut -d: -f2-)
    # 模拟: [记忆共享中心] → Mac 家目录形态（值见 SIM_ROOT_MAC·动态拼接）
    mac_sim=$(echo "$content" | sed "s|\[记忆共享中心\]|${SIM_ROOT_MAC}|g")
    # 检测双重盘符: /C:/ 或 C:/C:/
    if echo "$mac_sim" | grep -qE '/[A-Z]:/|~/[A-Z]:/'; then
      DUP_ISSUES="$DUP_ISSUES\n  $file:$lno → Mac模拟产生双重路径"
    fi
    # Win模拟: [记忆共享中心] → C: 盘 Users 形态（值见 SIM_ROOT_WIN·动态拼接）
    win_sim=$(echo "$content" | sed "s|\[记忆共享中心\]|${SIM_ROOT_WIN}|g")
    if echo "$win_sim" | grep -qE '[A-Z]:/.*[A-Z]:/'; then
      DUP_ISSUES="$DUP_ISSUES\n  $file:$lno → Win模拟产生双重路径"
    fi
  done < <(grep -n 'expanduser.*\[记忆共享中心\]' "$file")
done < <(grep -rl 'expanduser.*\[记忆共享中心\]' "$PKG" --include="*.py" 2>/dev/null)
if [ -z "$DUP_ISSUES" ]; then
  echo "OK"
else
  echo "FAIL"
  echo -e "$DUP_ISSUES"
  FAILS=$((FAILS+1))
fi

# ── ⑧ 硬编码用户路径(~/个人AI档案/) —— 必须用 [记忆共享中心] 占位符 ──
# 🔧 v3.44.0 修复（2026-09-04·逻辑自杀→三态分级）：原第2道过滤 `grep -v '个人AI档案/'` 与搜索模式
#   '~/个人AI档案/' **完全重叠**（命中行必含该子串）→ 全部被自己排除 → HARD_USER 恒空 → **恒报 OK**。
#   实测后果：布洛陀-安装包内 393 处（其中 clock-loop 自身脚本 126 处）零检出；历史 187 处 → 393 处翻倍期间检查一路报 OK。
#   判据源：skill-arch-standard 第452行"从没报过 NOT OK 的检查，它的 OK 不可信"（sync_guard 报"0漂移"数周实漏2条同构）
#          + instruction-standard 第198/201行：`~/个人AI档案/` 属"伪安全"级（tilde能展开但目录名用户自起·Windows端静默失效）
#   现改为：只豁免历史记载(CHANGELOG)与规则说明文件(讲该路径分级规则本身)，其余按扩展名分**三态**（有痕跳过≠静默跳过·第645行）
echo -n "⑧ 硬编码用户路径 ~/个人AI档案/: "
HARD_RAW=$(grep -rn '~/个人AI档案/' "$PKG" --exclude="check_package_health.sh" --include="*.md" --include="*.sh" --include="*.ps1" --include="*.py" 2>/dev/null \
  | grep -v 'check_package_health.sh:' | grep -v 'CHANGELOG.md' \
  | grep -vE '/(instruction-standard|skill-arch-standard|版本命名规范|platform-paths)\.md:')
HARD_CODE=$(printf '%s\n' "$HARD_RAW" | grep -E '\.(py|sh|ps1):')
HARD_DOC=$(printf '%s\n' "$HARD_RAW" | grep -E '\.md:')
N_CODE=$(printf '%s\n' "$HARD_CODE" | grep -c . || true)
N_DOC=$(printf '%s\n' "$HARD_DOC" | grep -c . || true)
if [ "$N_CODE" -gt 0 ]; then
  echo "🔴 FAIL (代码类 ${N_CODE} 处·跨用户即死路径)"
  printf '%s\n' "$HARD_CODE" | head -20 | while read -r line; do echo "   $line"; done
  if [ "$N_DOC" -gt 0 ]; then echo "   ⚠️ 另有文档类 ${N_DOC} 处（说明性 vs 指令性需人工判·不计FAIL）"; fi
  FAILS=$((FAILS+1))
elif [ "$N_DOC" -gt 0 ]; then
  echo "⚠️ not-evaluable (仅文档类 ${N_DOC} 处·不计FAIL·需人工判是否属规则说明)"
  printf '%s\n' "$HARD_DOC" | head -10 | while read -r line; do echo "   $line"; done
else
  echo "OK (0处·已豁免 CHANGELOG 历史记载与规则说明文件)"
fi

# ── ⑨ pwsh 路径解析须拒收版本化商店路径（Resolve-PwshPath v2·1.5.2） ──
echo -n "⑨ pwsh 解析拒收版本化 WindowsApps 路径: "
PWSH_MINE=""
while IFS= read -r ps1; do
  [ -z "$ps1" ] && continue
  if grep -q 'Get-Command pwsh' "$ps1" 2>/dev/null && ! grep -qF 'Microsoft\.PowerShell_' "$ps1" 2>/dev/null; then
    PWSH_MINE="$PWSH_MINE\n  $(basename "$ps1"): Get-Command pwsh 无版本化路径黑名单(商店更新即死路径)"
  fi
done < <(find "$PKG" -name "*.ps1" ! -path "*/.git/*" 2>/dev/null)
if [ -z "$PWSH_MINE" ]; then
  echo "OK"
else
  echo "FAIL"
  echo -e "$PWSH_MINE"
  FAILS=$((FAILS+1))
fi

# ── ⑩ setup.ps1 BOM 承接（W1 抗体退役后的真承接方·2026-09-18 立）──
# 来源：成长箱免疫工单 D9——W1 抗体（"setup.ps1 BOM 丢失"）因检测对象已消失而退役，
#   但坑仍可能在发布包侧复发（PowerShell 5.1 读无 BOM 的 UTF-8 ps1 会乱码）。
#   退役不留空悬（守卫编写规范 §3.3）：改由本项在发布前包源质检机械守——抗体域⛔不再报，本域报。
# 判据：包内每个 setup.ps1 首三字节必须为 ef bb bf；缺 → FAIL 并列出；0 个对象 → not-evaluable（⛔不假绿）。
echo -n "⑩ setup.ps1 BOM 完整(承接 W1): "
BOM_TMP=$(mktemp)
BOM_N=0
while IFS= read -r ps1; do
  [ -z "$ps1" ] && continue
  BOM_N=$((BOM_N+1))
  B3=$(head -c3 "$ps1" | od -An -tx1 | tr -s " " | tr -d " ")
  if [ "$B3" != "efbbbf" ]; then
    echo "  ${ps1#$PKG/}: 首三字节=${B3:-空} 不等于 efbbbf" >> "$BOM_TMP"
  fi
done < <(find "$PKG" -name "setup.ps1" ! -path "*/.git/*" 2>/dev/null)
if [ "$BOM_N" -eq 0 ]; then
  echo "not-evaluable (包内 0 个 setup.ps1·检查没跑到对象，不算通过)"
elif [ -s "$BOM_TMP" ]; then
  echo "FAIL"
  cat "$BOM_TMP"
  FAILS=$((FAILS+1))
else
  echo "OK (${BOM_N} 个 setup.ps1 全带 BOM)"
fi
rm -f "$BOM_TMP"

# ── ⑪ 脚本内引用落点存在性（C3·2026-09-20·群友问题6 根治）──
# 占位符替换了根 ≠ 路径可达：抽包内代码类文件里的占位根相对引用，逐个三腿验证
#   （模板实体/步骤生成/运行时生长）。群友实锤：growth_signal_collector 引用"开发工具/"
#   子路径断头 → 感知层 3/4 空转——账面干净≠运行可达（S885）。
echo -n "⑪ 脚本内引用落点可达: "
RPC="$PKG/references/scripts/reference_path_check.py"
if [ -f "$RPC" ] && command -v python3 >/dev/null 2>&1; then
  RPC_OUT=$(python3 "$RPC" --pkg-root "$PKG" 2>&1)
  if [ $? -eq 0 ]; then
    echo "OK ($(echo "$RPC_OUT" | tail -1 | grep -o '[0-9]* 处引用' || echo ''))"
  else
    echo "FAIL"
    echo "$RPC_OUT" | head -13
    FAILS=$((FAILS+1))
  fi
else
  echo "not-evaluable (缺 python3 或 references/scripts/reference_path_check.py)"
fi

echo ""
echo "=== 结果: $FAILS 项 FAIL ==="
exit $FAILS
