#!/bin/bash
# TRUTH_OF: 脚本中心/verify_skill_version_hook.sh   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# pre-commit 门禁：强制同步 技能版本单一真理源
#   (SKILL.md frontmatter.version == references/CHANGELOG.md 顶部版本)
# 检测本次 staged 的技能目录（改动 SKILL.md 或 references/CHANGELOG.md），逐个跑
# verify_skill_version.py；任一 mismatch → exit 1 拦截提交。
# 无技能改动 → 直接通过（最小摩擦）。
set -u
# 解释器解析（2026-10-06 根治·LobsterAI 端实证）：
#   病灶=原 PY="~/..." 硬编某端 WorkBuddy 解释器 → 引号内 ~ 不展开 + 换端即死。
#   实测 verify_skill_version.py 在 py3.9/3.11/3.14 行为逐字一致 ⇒ 无版本依赖 ⇒ 硬编纯负债。
#   正解=自解析链（$HOME → command -v → 报错），⛔ 不绑任何端/版本。
#   自证：打印实际用的解释器，坏没坏一眼可见（⛔不再"自己坏了却报别人缺声明"）。
_PY_CAND=(
  "${BULUOTUO_PY:-}"
  "$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
  "$(command -v python3 2>/dev/null)"
  "$(command -v python 2>/dev/null)"
)
PY=""
for _c in "${_PY_CAND[@]}"; do
  [ -n "$_c" ] && [ -x "$_c" ] && { PY="$_c"; break; }
done
if [ -z "$PY" ]; then
  echo "❌ verify_skill_version_hook: 找不到可用的 python3（设 BULUOTUO_PY 指定）" >&2
  exit 1
fi
echo "[verify_skill_version_hook] 解释器：${PY}（$("$PY" -V 2>&1)）" >&2
# B修源·声明驱动口径v2(2026-10-05·条文47·L2键20261005_194734下沉轮)：记忆根唯一来源=runtime_paths 声明
# （解析器与本件同目录可达·软链/pre-commit 入口靠 realpath 下沉解析·无声明 hard fail 即教育）。
# ⛔消费侧默认兜底已删。PY行=解释器选择（非记忆根·批裁范围外·WB 解释器 PyYAML 先例·保持不动）。
_RP="$(dirname "$0")/runtime_paths.py"
_GUIDE="❌ verify_skill_version_hook: 读不到 runtime_paths 声明·作者机先跑 脚本中心/runtime_paths.py build / 端用户机跑安装器(条文47)"
# 🔴 rc 判定非变量判定(2026-10-05 负例实跑逮出假绿洞·第3支正确形态回补)：
#    rp 失败时教育文案走 stdout，$(...) 会把它捕成非空变量——[ -n ] 判不住；赋值命令退出码=命令替换rc，用 || 才物理成立。
VERIFY_DIR="$("$PY" "$_RP" get devtools 2>/dev/null)" || { echo "$_GUIDE" >&2; exit 1; }
REPO="$("$PY" "$_RP" get archive_root 2>/dev/null)" || { echo "$_GUIDE" >&2; exit 1; }
VERIFY="$VERIFY_DIR/verify_skill_version.py"
RC=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    */SKILL.md|SKILL.md)
      d=$(dirname "$f")
      ;;
    */references/CHANGELOG.md|references/CHANGELOG.md)
      d=$(dirname "$(dirname "$f")")
      ;;
    *)
      continue
      ;;
  esac
  d="$REPO/$d"
  if [ -f "$d/SKILL.md" ]; then
    if ! "$PY" "$VERIFY" "$d"; then
      echo "⚠️ [pre-commit] 技能版本未同步: $d"
      echo "   请对齐 SKILL.md frontmatter version 与 references/CHANGELOG.md 顶部版本后再提交"
      RC=1
    fi
  fi
done < <(git -C "$REPO" diff --cached --name-only --diff-filter=ACMR 2>/dev/null)
exit $RC
