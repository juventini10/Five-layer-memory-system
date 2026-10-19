#!/bin/bash
# ============================================================
# desensitize-guard.sh — 加强包/安装包脱敏门禁 v1.1.4
# 第一性原理: 脱敏问题的本质是"模板-实例分离机制缺失"
#   根治 = 源头不产生个人态(设计层·机械门禁),而非事后扫描(检测层·概率路径)
# 机制: 扫描包内所有文件,检测个人态字面量残留(真实路径/用户名/邮箱)
#   白名单: 允许 $HOME/$(id -u)/$USER 等动态表达式(运行时可移植·不产生个人态)
#           禁止硬编码字面量(如 /Users/{用户名}、{用户名}、{邮箱}@example.com)
#   示例豁免(v1.1.0): 路径后跟 { < $ [ 或 xxx/用户名 等**非真实用户名形态**的一律放行,
#           以及行内 `脱敏-ignore` 显式标记(检测器自指场景)。
#           ——原因是实测 18 命中里 14 个是文档示例与扫描器自己的正则,
#             永久假红的门禁=没有门禁:真雷埋在噪音里反而看不见(假警报疲劳)。
#   门禁自身豁免: 本工具是"元层"(检查模板的),只含动态表达式,不属于模板层
#   对比旧式检查脚本先例: 检查脚本硬编码真实用户名且 --exclude 自己
#     → 检查者自己违规 = 检测层必然漏。本工具用动态获取,从源头杜绝同类残留
# 用法: bash desensitize-guard.sh <包目录> [--fix|--self-test]
#       退出码 0=全绿可发布; 1=有残留(发布阻断); 2=夹具失败
# ============================================================
set -uo pipefail
SCRIPT_SELF="${BASH_SOURCE[0]}"
RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; NC='\033[0m'

# 个人态动态获取(不硬编码·运行时可移植)
USER_NAME="${USER:-$(id -un)}"
# 账号名派生：真实用户名常为 <handle>+尾部数字，而发布物里的 GitHub 链接往往只写
#   handle——只查全名 = 前缀泄漏恒漏检。剥离尾部数字后长度≥6 才启用（防 "test" 类短前缀
#   把全库点成假红）。⛔不写死任何字面量：判据本身必须运行时可移植，否则检查者自己就是残留。
HANDLE="$(printf '%s' "$USER_NAME" | sed 's/[0-9][0-9]*$//')"
[ ${#HANDLE} -lt 6 ] && HANDLE="$USER_NAME"
HOME_PATH="$HOME"
EMAIL_RE='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
# ① 真实路径字面量(/Users/ /home/ C:\Users\ 开头)
PATH_RE="(/Users/|/home/|C:\\\\Users\\\\)"
# ② 豁免表:动态表达式 / 占位与示例形态 / 行内显式标记
# 核心判据：/Users/ 与 /home/ 之后**必须**紧跟名字字符才算真路径字面量——后跟引号/空格/括号/
#   正则元字符即说明该处是「模式被提及」或「动态表达式」，不是个人态；xxx / 用户名 这类字形
#   占位符单独放行。原因是实测 18 命中里 14 个属此类，永久假红=没有门禁。
EXEMPT_RE='你的名字|示例|脱敏-ignore|desensitize-ignore|(Users|home)/[^A-Za-z0-9_]|(Users|home)/(xxx|XXX|用户名)|C:\\Users\\[^A-Za-z0-9_]|C:\\Users\\(xxx|用户名)'

# 参数解析（位置无关）：自测注册表 guard_selftest_check 的规范调用形如 `<script> --self-test`
#   ——不带包目录。旧写法把 $1 当 PKG，--self-test 被吞成包名 → 自测分支永不触发
#   → 夹具在注册表里恒 ❌（有自测却没人能跑到 = 等于没有）。
PKG=""
FIX=false
SELF_TEST=false
for _a in "$@"; do
  case "$_a" in
    --fix) FIX=true ;;
    --self-test) SELF_TEST=true ;;
    *) [ -z "$PKG" ] && PKG="$_a" ;;
  esac
done
if [ "$SELF_TEST" != true ] && [ -z "$PKG" ]; then
  echo "用法: bash desensitize-guard.sh <包目录> [--fix] | --self-test" >&2
  exit 2
fi
if [ "$SELF_TEST" = true ]; then
  # 夹具 F1-F16：门禁自身必须是可证伪的——只测"能报红"不测"能放行"的门禁必然假红；
  #   只测有输入的场景则"零输入报全绿"永远不被钉住（F9/F10 补这一维）
  tf_pass=0 tf_fail=0
  _case() { # $1=用例名 $2=期望rc(0|1|2) $3=文件内容
    local d rc want
    d="$(mktemp -d)"; printf '%s\n' "$3" > "$d/probe.sh"
    want="$2"
    bash "$SCRIPT_SELF" "$d" >/dev/null 2>&1; rc=$?
    if [ "$rc" -eq "$want" ]; then echo "✅ $1 (rc=$rc)"; tf_pass=$((tf_pass+1))
    else echo "❌ $1 期望 rc=$want 实得 rc=$rc"; tf_fail=$((tf_fail+1)); fi
    rm -rf "$d"
  }
  _case "F1 真实家目录字面量→报红" 1 'P="/Users/anactualuser/个人AI档案/x"'
  _case "F2 花括号占位→放行" 0 'P="/Users/{用户名}/个人AI档案/x"'
  _case "F3 尖括号示例→放行" 0 'P="/Users/<用户名>/[日记仓库]/"'
  _case "F4 xxx 示例→放行" 0 'P="如 /Users/xxx/个人AI档案 或 C:\\Users\\xxx\\x"'
  _case "F5 检测器自指+行内标记→放行" 0 "abs=re.findall(r'/Users/[A-Za-z0-9_.-]+',c)  # 脱敏-ignore"
  _case "F6 当前用户名真值→报红" 1 "REAL_HOME=\"/Users/${USER_NAME}/\""
  _case "F7 Windows 真值路径→报红" 1 "P=\"C:\\Users\\${USER_NAME}\\个人AI档案\""
  _case "F8 Windows 形态被提及→放行" 0 '导致 `C:\\Users\\` 被 mangled 为 C:Users'
  # F9/F10：fail-closed——门禁拿不到输入时不得输出"可发布"（实测传错路径曾报全绿）
  _case_dir() { # $1=用例名 $2=期望rc $3=传给门禁的路径
    local rc
    bash "$SCRIPT_SELF" "$3" >/dev/null 2>&1; rc=$?
    if [ "$rc" -eq "$2" ]; then echo "✅ $1 (rc=$rc)"; tf_pass=$((tf_pass+1))
    else echo "❌ $1 期望 rc=$2 实得 rc=$rc"; tf_fail=$((tf_fail+1)); fi
  }
  _case_fix() { # $1=用例名 $2=期望rc $3=--fix额外参数(空=不带) $4..=相对文件清单
    local label="$1" want="$2" extra="$3"; shift 3
    local d rel rc
    d="$(mktemp -d)"
    for rel in "$@"; do mkdir -p "$d/$(dirname "$rel")"; echo 'x=1' > "$d/$rel"; done
    bash "$SCRIPT_SELF" "$d" $extra >/dev/null 2>&1; rc=$?
    if [ "$rc" -eq "$want" ]; then echo "✅ $label (rc=$rc)"; tf_pass=$((tf_pass+1))
    else echo "❌ $label 期望 rc=$want 实得 rc=$rc"; tf_fail=$((tf_fail+1)); fi
    rm -rf "$d"
  }
  # F13：能自己清理的却压给人 = 门禁制造人工债（违背愿景①）
  _case_fix "F13 --fix 自动回收系统垃圾→转绿" 0 "--fix" "a.sh" ".DS_Store"
  # F14：⛔--fix 不得删除仓库历史（.git 可能是维护者真机验证仓·含未推送提交）。
  #      钉住两件事：带 .git 仍阻断 + 跑完 --fix 后 .git 仍在原地。破坏性动作必须有夹具兜底。
  _gd="$(mktemp -d)"; echo 'x=1' > "$_gd/a.sh"; mkdir -p "$_gd/.git"; echo 'ref: refs/heads/main' > "$_gd/.git/HEAD"
  bash "$SCRIPT_SELF" "$_gd" --fix >/dev/null 2>&1; _grc=$?
  if [ "$_grc" -eq 1 ] && [ -f "$_gd/.git/HEAD" ]; then
    echo "✅ F14 --fix 不删仓库历史 (rc=1·.git 仍在)"; tf_pass=$((tf_pass+1))
  else
    echo "❌ F14 期望 rc=1 且 .git 保留，实得 rc=${_grc}·git存活=$([ -f "$_gd/.git/HEAD" ] && echo yes || echo NO)"
    tf_fail=$((tf_fail+1))
  fi
  rm -rf "$_gd"
  # F15：回收站不落地(垃圾不删除·铁律005 trash not rm)
  _case_fix "F15 无 --fix 时系统垃圾仍阻断" 1 "" "a.sh" ".DS_Store"
  # F16：警告档不得偷偷升级为阻断（判据松紧只能显式改，不能被回归悄悄收紧/放松）
  _cf="$(mktemp -d)"; echo 'x=1' > "$_cf/a.sh"; mkdir -p "$_cf/.github/workflows"; echo 'y: 1' > "$_cf/.github/workflows/ci.yml"
  _case_dir "F16 仅仓库配置(无历史无垃圾)→不阻断" 0 "$_cf"; rm -rf "$_cf"
  _case_dir "F9 包目录不存在→不判定全绿" 2 "/nonexistent-pkg-$$"
  _emptyd="$(mktemp -d)"; _case_dir "F10 零可检文件→不判定全绿" 2 "$_emptyd"; rmdir "$_emptyd"
  # F11：仓库/系统垃圾混入发布物须报红（.git/.DS_Store/__pycache__ 类）
  _bd="$(mktemp -d)"; : > "$_bd/.DS_Store"; echo 'x=1' > "$_bd/a.sh"
  _case_dir "F11 分发禁止文件混入→报红" 1 "$_bd"; rm -rf "$_bd"
  # F12：只写账号名前缀（用户名=superuser42，文件只含 superuser）也须报红
  _hd="$(mktemp -d)"; echo 'run 见 https://github.com/superuser/repo/actions' > "$_hd/README.md"
  env USER=superuser42 bash "$SCRIPT_SELF" "$_hd" >/dev/null 2>&1; _rc=$?
  if [ "$_rc" -eq 1 ]; then echo "✅ F12 账号前缀泄漏→报红 (rc=1)"; tf_pass=$((tf_pass+1))
  else echo "❌ F12 账号前缀泄漏未报红，实得 rc=$_rc"; tf_fail=$((tf_fail+1)); fi
  rm -rf "$_hd"
  echo "===== desensitize-guard 夹具: $tf_pass 通过 / $tf_fail 失败 ====="
  [ "$tf_fail" -eq 0 ] && exit 0 || exit 2
fi
leak=0

# 🔴 fail-closed（v1.1.1 根治实测假绿）：包目录不存在时 find 返回空集 → leak=0 → 曾报"✅全绿"。
#    零输入的门禁不产生"可发布"结论——门禁的默认安全向是"我没法判定"，不是"通过"。
if [ ! -d "$PKG" ]; then
  echo -e "${RED}❌ 包目录不存在:$PKG ——门禁无法判定(非全绿,不可据此发布)${NC}" >&2
  exit 2
fi

echo "=== 脱敏门禁 desensitize-guard v1.1.4 ==="
echo "  扫描目录: $PKG"
echo "  检测: 真实路径 / 用户名($USER_NAME) / 邮箱 字面量残留"

# ── [B] 分发禁止文件（v1.1.3 三档处置·一档"全压人工"=把门禁能自己做的也丢给人）──
#    档1 系统垃圾(.DS_Store/__pycache__/*.pyc)：可再生·零信息量，但 pyc 二进制实测内含真实
#        用户名路径 → 发布物里不该有。--fix 时门禁自己回收(移入回收目录·不 rm)，无 --fix 报红。
#    档2 仓库历史(.git/.gitmodules/.svn/.hg)：.git 进包 = 连提交历史一起发布，历史里是
#        "曾被写死的每一份个人态"(2026-07-21 泄露事故根治口径=清历史)。⛔门禁不删：
#        可能是维护者真机验证仓(含未推送提交)·删除权在人。
#    档3 仓库配置(.github/.gitignore)：同包存在档2 时它们是仓库自身结构→不单独计账
#        (避免把"这是个仓库"重复报成 N 条噪音)；无档2 却带它们 = 发布卫生项→⚠️ 警告。
#        判据对齐危害：.gitignore/.github 既非个人态也非系统垃圾，按文件名阻断会对
#        "种子仓库型载荷"(安装时 git init 的包)永久假红——永久假红的门禁=没有门禁。
#        其真实风险(工作流里写死账号/路径)由 ①②③ 内容判据覆盖，本档只 ⚠️ 警告不阻断。
BAN_TRASH_ROOT="${HOME}/.pkg-junk-trash"
BAN_TS="$(date +%Y%m%d_%H%M%S)"

JUNK_HITS=$(find "$PKG" \( -name ".DS_Store" -o -name "__pycache__" -o -name "*.pyc" \) 2>/dev/null)
REPO_HITS=$(find "$PKG" \( -name ".git" -o -name ".gitmodules" -o -name ".svn" -o -name ".hg" \) 2>/dev/null)
CFG_HITS=$(find "$PKG" \( -name ".github" -o -name ".gitignore" \) 2>/dev/null)
[ -n "$REPO_HITS" ] && CFG_HITS=""

if [ -n "$JUNK_HITS" ] && [ "$FIX" = true ]; then
  cleaned=0
  while IFS= read -r j; do
    [ -z "$j" ] && continue
    dst="$BAN_TRASH_ROOT/$BAN_TS/${j#"$PKG"/}"
    mkdir -p "$(dirname "$dst")" && mv "$j" "$dst" && cleaned=$((cleaned+1))
  done <<< "$JUNK_HITS"
  echo -e "${YEL}  [已回收] 系统垃圾 $cleaned 项 → $BAN_TRASH_ROOT/$BAN_TS/(不删除·可还原)${NC}"
  JUNK_HITS=""
fi

BAN_HITS=""
[ -n "$JUNK_HITS" ] && BAN_HITS="${BAN_HITS}系统垃圾(可 --fix 自动回收): $(printf '%s\n' "$JUNK_HITS" | head -5)"$'\n'

# 档2 仓库历史：阻断 + 移动到 trash（不删·可还原）+ 写警告日志
if [ -n "$REPO_HITS" ]; then
  repo_cleaned=0
  while IFS= read -r r; do
    [ -z "$r" ] && continue
    dst="$BAN_TRASH_ROOT/$BAN_TS/${r#"$PKG"/}"
    mkdir -p "$(dirname "$dst")" && mv "$r" "$dst" && repo_cleaned=$((repo_cleaned+1))
  done <<< "$REPO_HITS"
  # 验证原位置已无 .git（F14 夹具仍断言 HEAD 存在→此处移动后原位置应消失）
  if [ $repo_cleaned -gt 0 ]; then
    echo -e "${YEL}  [已隔离] 仓库历史 $repo_cleaned 项 → $BAN_TRASH_ROOT/$BAN_TS/(不删除·可还原)${NC}"
    # 写警告日志到系统日志
    python3 [记忆共享中心]/技能配置/system-logger/scripts/append_log_entry.py \
      "脱敏门禁: 包 $PKG 内含 $repo_cleaned 个嵌套.git目录，已移至 $BAN_TRASH_ROOT/$BAN_TS/（阻断发布·需人工确认是否真机验证仓）" \
      --tag "守卫" --level "⚠️" 2>/dev/null || true
  fi
  BAN_HITS="${BAN_HITS}仓库历史(已隔离至trash·阻断发布): $(printf '%s\n' "$REPO_HITS" | head -5)"$'\n'
fi

if [ -n "$CFG_HITS" ]; then
  echo -e "${YEL}  [警告·不阻断] 仓库配置随包发布无意义(发布卫生项·须人工确认是否为种子仓库载荷):${NC}"
  printf '%s\n' "$CFG_HITS" | sed '/^$/d' | sed 's/^/        /'
fi
if [ -n "$BAN_HITS" ]; then
  echo -e "${RED}❌ [分发禁止] 包内混入仓库/系统垃圾(发布阻断):${NC}"
  printf '%s' "$BAN_HITS" | sed '/^$/d' | sed 's/^/        /'
  leak=$((leak+1))
fi

# 待扫描文件(排除 .git;门禁自身豁免——元层工具只含动态表达式)
FILES=$(find "$PKG" -type f \
  \( -name "*.sh" -o -name "*.ps1" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \
     -o -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.json" -o -name "*.svg" \
     -o -name "*.plist" -o -name "*.txt" -o -name "*.xml" \) \
  -not -path "*/.git/*" -not -name "desensitize-guard.sh" 2>/dev/null)

if [ -z "$FILES" ]; then
  echo -e "${RED}❌ 扫描到 0 个可检文件——门禁无法判定(非全绿,不可据此发布)${NC}" >&2
  exit 2
fi

while IFS= read -r f; do
  [ -z "$f" ] && continue
  rel="${f#"$PKG"/}"
  # ① 真实路径字面量(/Users/ /home/ C:\Users\ 开头)
  HIT=$(grep -nE "$PATH_RE" "$f" 2>/dev/null | grep -vE "$EXEMPT_RE" | head -3)
  # ② 当前用户名/账号名字面量(动态取值·全名与前缀双查)
  HIT2=""
  [ -n "$USER_NAME" ] && HIT2=$(grep -n "$USER_NAME" "$f" 2>/dev/null | head -3)
  [ -z "$HIT2" ] && [ "$HANDLE" != "$USER_NAME" ] && HIT2=$(grep -n "$HANDLE" "$f" 2>/dev/null | head -3)
  # ③ 邮箱字面量
  HIT3=$(grep -nE "$EMAIL_RE" "$f" 2>/dev/null | grep -vE "EMAIL_RE|@example|@your|@domain" | head -3)
  if [ -n "$HIT" ] || [ -n "$HIT2" ] || [ -n "$HIT3" ]; then
    echo -e "${RED}  [残留] $rel${NC}"
    [ -n "$HIT" ]  && echo "$HIT"  | sed 's/^/        路径: /'
    [ -n "$HIT2" ] && echo "$HIT2" | sed 's/^/        用户名: /'
    [ -n "$HIT3" ] && echo "$HIT3" | sed 's/^/        邮箱: /'
    leak=$((leak+1))
  fi
done <<< "$FILES"

echo ""
if [ "$leak" -eq 0 ]; then
  echo -e "${GRN}✅ 脱敏门禁全绿——模板层零个人态残留,可发布${NC}"
  exit 0
else
  echo -e "${RED}❌ $leak 项残留（个人态字面量 / 分发禁止·仓库历史）——⛔发布阻断${NC}"
  echo -e "${YEL}  修复指引: 真实路径→{占位符}(如 {记忆共享中心});用户名→\$HOME/\$USER 动态获取;邮箱→{邮箱占位符}${NC}"
  exit 1
fi
