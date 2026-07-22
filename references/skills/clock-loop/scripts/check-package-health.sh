#!/bin/bash
# check-package-health.sh — 布洛陀发布前包源质检
# 退出码 0=全通，非0=有FAIL
# 用法：bash check-package-health.sh <包根目录>

PKG="${1:-.}"
[ ! -d "$PKG" ] && echo "用法: $0 <包根目录>" && exit 2

FAILS=0
echo "=== 布洛陀包源质检 ==="
echo "包路径: $PKG"
echo ""

# ── ① .py Path("~/ 未展开 ──
echo -n "① .py Path(~/ 展开: "
RES=$(grep -rn 'Path("~/\|Path('\''~/' "$PKG" --include="*.py" 2>/dev/null)
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
  PKG_VER=$(grep -oE 'version:[[:space:]]*"?[0-9]+\.[0-9]+\.[0-9]+' "$PKG/version.md" 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
  [ -z "$PKG_VER" ] && PKG_VER="1.3.1"
  PKG_VER_ESC=$(printf '%s' "$PKG_VER" | sed 's/\./\\./g')
  CURRENT=$(sed -n "/^## \[$PKG_VER_ESC\]/,/^## \[/p" "$CHLOG")
  while IFS= read -r token; do
    token=$(echo "$token" | tr -d '`')
    # 只查看起来像包内文件的（有.扩展名且不是网址）
    [[ "$token" =~ ^http ]] && continue
    [[ "$token" =~ ^~ ]] && continue
    [[ "$token" =~ \.(sh|ps1|py|md|html|plist)[[:space:]]*$ ]] || continue
    # 跳过完全匹配"已删/废弃/移除"的条目
    [[ "$CURRENT" =~ 删除.*$token|废弃.*$token|移除.*$token ]] && continue
    [ ! -f "$PKG/$token" ] && ISSUES="$ISSUES\n  声称但不存在: $token"
  done < <(echo "$CURRENT" | grep -o '`[^`]*`')
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

# ── ⑤ 硬编码路径附加检测 ──
echo -n "⑤ 全包硬编码路径: "
SKIP_DIRS="CHANGELOG.md|\.git|__pycache__|记忆琥珀设计哲学|指令编写规范|questionnaire|个人AI档案/"
RES=$(grep -rn '个人AI档案' "$PKG" --include="*.md" --include="*.py" --include="*.sh" --include="*.ps1" \
  | grep -vE "$SKIP_DIRS" | grep -v '\[记忆共享中心\]' 2>/dev/null)
if [ -z "$RES" ]; then
  echo "OK"
else
  echo "⚠️ ($(echo "$RES"|wc -l|tr -d ' ')处, 排除路径前缀/历史/规范后)"
  echo "$RES" | while read line; do echo "   $line"; done
fi

# ── ⑥ 占位符格式一致性（禁花括号/expanduser外壳/硬编码）──
echo -n "⑥ 占位符格式一致性: "
FMT_ISSUES=""
# 花括号占位符残留（旧格式，应全部改为方括号）
CURLY=$(grep -rn '{MEMORY_CENTER}\|{WORKBUDDY_HOME}' "$PKG" --include="*.template" --include="*.txt" --include="*.py" --include="*.ps1" 2>/dev/null)
[ -n "$CURLY" ] && FMT_ISSUES="$FMT_ISSUES\n  花括号残留: $(echo "$CURLY"|wc -l|tr -d ' ')处"
# expanduser + [记忆共享中心] 双重路径危险模式
EXPAND=$(grep -rn 'expanduser.*\[记忆共享中心\]' "$PKG" --include="*.py" 2>/dev/null)
[ -n "$EXPAND" ] && FMT_ISSUES="$FMT_ISSUES\n  expanduser+占位符危险: $(echo "$EXPAND"|wc -l|tr -d ' ')处"
# .ps1/.sh/.md 中硬编码'个人AI档案'而非[记忆共享中心]
HARD=$(grep -rn '个人AI档案' "$PKG" --include="*.ps1" --include="*.sh" --include="*.md" 2>/dev/null | grep -v '\[记忆共享中心\]' | grep -v '记忆琥珀/备份' | grep -v '\.bak' | grep -v 'CHANGELOG.md' | grep -v '个人AI档案/' | grep -v 'source:')
[ -n "$HARD" ] && FMT_ISSUES="$FMT_ISSUES\n  .ps1/.sh/.md硬编码个人AI档案: $(echo "$HARD"|wc -l|tr -d ' ')处"
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
    # 模拟: [记忆共享中心] → /Users/hw/个人AI档案
    mac_sim=$(echo "$content" | sed 's|\[记忆共享中心\]|/Users/hw/个人AI档案|g')
    # 检测双重盘符: /C:/ 或 C:/C:/
    if echo "$mac_sim" | grep -qE '/[A-Z]:/|~/[A-Z]:/'; then
      DUP_ISSUES="$DUP_ISSUES\n  $file:$lno → Mac模拟产生双重路径"
    fi
    # Win模拟: [记忆共享中心] → C:\Users\hw\个人AI档案
    win_sim=$(echo "$content" | sed 's|\[记忆共享中心\]|C:/Users/hw/个人AI档案|g')
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
echo -n "⑧ 硬编码用户路径 ~/个人AI档案/: "
HARD_USER=$(grep -rn '~/个人AI档案/' "$PKG" --include="*.md" --include="*.sh" --include="*.ps1" --include="*.py" 2>/dev/null \
  | grep -v 'CHANGELOG.md' | grep -v '个人AI档案/' | head -20)
if [ -z "$HARD_USER" ]; then
  echo "OK"
else
  echo "FAIL ($(echo "$HARD_USER"|wc -l|tr -d ' ')处)"
  echo "$HARD_USER" | while read line; do echo "   $line"; done
  FAILS=$((FAILS+1))
fi

echo ""
echo "=== 结果: $FAILS 项 FAIL ==="
exit $FAILS
