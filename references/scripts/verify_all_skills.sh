#!/bin/bash
# release 门禁：扫描 技能配置/ 下全部技能，校验版本单一真理源
#   (SKILL.md frontmatter.version == references/CHANGELOG.md 顶部版本)。
# 任一 mismatch → exit 1。发布 / 镜像同步前运行，确保无版本漂移漏网。
# 无 CHANGELOG 的技能无第二副本可漂，自动跳过（verify_skill_version.py 返回 0）。
# 2026-10-15 ⑥死字面批根治三处：①引号内 ~ 不展开（10-15 卡同型病·执行必假失败）
# ②VERIFY/BASE 层级校正（记忆共享中心根下的 脚本中心/、技能配置/ 均不存在·真源=脚本中心/安装发布/）
# ③WB 解释器单点→候选序（VERIFY_ALL_PY→/usr/bin→command -v→WB末位兜底·同②法）
if [ -n "${VERIFY_ALL_PY:-}" ]; then   # 显式指定=独占·坏即显形即停（⛔静默降级·同②原则）
  [ -x "${VERIFY_ALL_PY}" ] || { echo "❌ verify_all_skills: VERIFY_ALL_PY 不可执行: ${VERIFY_ALL_PY}" >&2; exit 2; }
  PY="${VERIFY_ALL_PY}"
else
  PY=""
  for _c in /usr/bin/python3 "$(command -v python3 || true)" \
    "$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"; do
    [ -n "${_c:-}" ] && [ -x "${_c}" ] && { PY="${_c}"; break; }
  done
fi
[ -n "${PY:-}" ] || { echo "❌ verify_all_skills: 找不到可用 python3（设 VERIFY_ALL_PY 指定）" >&2; exit 2; }
VERIFY="[记忆共享中心]/脚本中心/verify_skill_version.py"
BASE="[记忆共享中心]/技能配置"
RC=0
while IFS= read -r d; do
  [ -f "$d/SKILL.md" ] || continue
  if ! "$PY" "$VERIFY" "$d" >/dev/null 2>&1; then
    "$PY" "$VERIFY" "$d"
    RC=1
  fi
done < <(find "$BASE" -name SKILL.md -exec dirname {} \;)
if [ "$RC" -eq 0 ]; then
  echo "✅ 全部技能版本单一真理源校验通过"
fi
exit $RC
