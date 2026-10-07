#!/bin/bash
# release 门禁：扫描 技能配置/ 下全部技能，校验版本单一真理源
#   (SKILL.md frontmatter.version == references/CHANGELOG.md 顶部版本)。
# 任一 mismatch → exit 1。发布 / 镜像同步前运行，确保无版本漂移漏网。
# 无 CHANGELOG 的技能无第二副本可漂，自动跳过（verify_skill_version.py 返回 0）。
PY="~/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
VERIFY="$HOME/脚本中心/verify_skill_version.py"
BASE="$HOME/技能配置"
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
