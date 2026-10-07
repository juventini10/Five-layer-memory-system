#!/usr/bin/env bash
# skill-version-guard.sh v1.0 —— Skill 版本↔CHANGELOG 一致性守卫（changelog-guard 族·登记一致性守卫模式）
# 零第三方依赖(bash+find+grep+sed)。用法: --check(JSON) / --report(明细,供AI补)
# 设计: 比对 技能配置/{skill}/SKILL.md frontmatter `version:` 与 references/CHANGELOG.md 中出现过的最大版本号。
#   不一致两类——SKILL领先(CHANGELOG漏记新版本,升版未记) / CHANGELOG领先(SKILL头部滞后,改版未同步frontmatter)。
#   双向检测,治"升版漏CHANGELOG"与"改版忘升frontmatter"两个方向的漂移。
# 依据: 变更日志"记/不记"规则 + changelog-guard v1.6 合记契约同源(登记一致性守卫模式,2026-08-06作者"还能用到哪里"迁移）。
# 边界: 无 CHANGELOG 文件的 Skill → 报"无CHANGELOG"(提示级,不计违规,因其可能用头部版本单账); 版本号从全文提取(兼容 ## v1.0.0 — 日期 / ### v1.0.0 / v1.0.0 · 日期 三种标题风格)。
set -uo pipefail
# 2026-10-03 端中立化（包内副本·⛔ 不含任何作者侧路径字面量）：
#   原写法把档案根硬编码成作者机家目录下的固定目录名 ⇒ 端用户机没有该目录 ⇒ 守卫无对象可守。
#   解析序：① 环境变量 BULUOTUO_ARCHIVE_ROOT（测试/多实例）
#          ② runtime_paths 的 script_center 键上溯一级（<MC>/脚本中心 ⇒ <MC>）——安装器保证该文件存在
#          ③ 脚本上溯两级（与脚本中心同放时的兜底）
__gd="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "${BULUOTUO_ARCHIVE_ROOT:-}" ] && [ -n "${BULUOTUO_RUNTIME_PATHS:-}" ] \
   && [ -f "${BULUOTUO_RUNTIME_PATHS}" ]; then
  BULUOTUO_ARCHIVE_ROOT="$(python3 - "${BULUOTUO_RUNTIME_PATHS}" <<'PYEOF' 2>/dev/null
import json, os, sys
try:
    sc = json.load(open(sys.argv[1], encoding="utf-8")).get("script_center")
    print(os.path.dirname(sc) if sc else "")
except Exception:
    print("")
PYEOF
)"
  export BULUOTUO_ARCHIVE_ROOT
fi
BASE="${BULUOTUO_ARCHIVE_ROOT:-$(cd "$__gd/../.." && pwd)}"
SKILLS="$BASE/技能配置"

mode="${1:---check}"

# 版本号规范化比较(零填充三位段)
vt() { printf '%s\n' "$1" | sed -E 's/^v//' | awk -F. '{printf "%03d %03d %03d", $1+0, $2+0, $3+0}'; }
vg() { [ "$(vt "$1")" \> "$(vt "$2")" ]; }   # $1 > $2

# 从 CHANGELOG 提取最大版本号(只认版本标题行 `^#+ v`,防正文引用其他版本号如schema/规范混入)
# v1.0.1(2026-08-06·Stop钩子超时修复): 一次性grep管道取最大,废弃逐行read+spawn grep——根因:44 Skill×数百行=数万次子进程spawn,43s超时
#   (同 changelog-guard v1.5.1 教训:逐文件spawn 27ms/文件×3181=86s);修复后 43s→~1.5s。
maxver_in() {
  grep -E '^#{1,3}[[:space:]]+v[0-9]+(\.[0-9]+){1,2}' 2>/dev/null \
    | grep -oE 'v[0-9]+(\.[0-9]+){1,2}' \
    | sed 's/^v//' \
    | awk -F. '{k=$1*10000+$2*100+$3; if(k>max){max=k; v=$0}} END{print v}'
}

report=""
n_skill=0; n_ok=0; n_skill_lead=0; n_log_lead=0; n_no_cl=0
while IFS= read -r skill; do
  [ -f "$skill/SKILL.md" ] || continue
  n_skill=$((n_skill+1))
  sname=$(basename "$skill")
  v=$(grep -m1 -iE '^version:' "$skill/SKILL.md" 2>/dev/null | sed -E 's/^version:[[:space:]]*//; s/["'"'"']//g')
  [ -z "$v" ] && continue   # 无版本号的Skill(第三方/未版本化)跳过
  cl="$skill/references/CHANGELOG.md"
  if [ -f "$cl" ]; then
    clv=$(maxver_in < "$cl")
    if [ -z "$clv" ]; then report+="| $sname | v$v | — | ⚠️ CHANGELOG无版本条目 |\n"; n_log_lead=$((n_log_lead+1)); continue; fi
    if vg "$v" "$clv"; then
      report+="| $sname | v$v | v$clv | ⚠️ SKILL领先·CHANGELOG漏记新版本(升版未记) |\n"; n_skill_lead=$((n_skill_lead+1))
    elif vg "$clv" "$v"; then
      report+="| $sname | v$v | v$clv | ⚠️ CHANGELOG领先·SKILL头部滞后(改版忘升frontmatter) |\n"; n_log_lead=$((n_log_lead+1))
    else
      n_ok=$((n_ok+1))
    fi
  else
    report+="| $sname | v$v | 无CHANGELOG | ℹ️ 无CHANGELOG文件(提示级·非违规) |\n"; n_no_cl=$((n_no_cl+1))
  fi
done < <(find "$SKILLS" -maxdepth 1 -mindepth 1 -type d | sort)

if [ "$mode" = "--check" ]; then
  n_bad=$((n_skill_lead+n_log_lead))
  alarm=$([ "$n_bad" -gt 0 ] && echo true || echo false)
  printf '{"skills_with_version": %d, "consistent": %d, "skill_lead": %d, "log_lead": %d, "no_changelog": %d, "alarm": %s}\n' "$n_skill" "$n_ok" "$n_skill_lead" "$n_log_lead" "$n_no_cl" "$alarm"
  [ "$n_bad" -gt 0 ] && exit 1 || exit 0
elif [ "$mode" = "--report" ]; then
  n_bad=$((n_skill_lead+n_log_lead))
  if [ "$n_bad" -eq 0 ]; then echo "✅ 全部带版本 Skill 的 SKILL.md ↔ CHANGELOG 一致（${n_ok} 个一致 · ${n_no_cl} 个无CHANGELOG提示级）"; exit 0; fi
  echo "## ⚠️ 检测到 ${n_bad} 个 Skill 版本↔CHANGELOG 不一致（${n_skill} 个带版本 Skill）"
  echo ""
  echo "| Skill | SKILL.md版本 | CHANGELOG最新 | 问题 |"
  echo "|------|:---:|:---:|------|"
  printf "%b" "$report"
  echo ""
  echo "> 机械部分脚本已填;修正动作(SKILL升frontmatter / CHANGELOG补条目)须 AI 执行。"
else echo "用法: skill-version-guard.sh [--check|--report]"; exit 2; fi
