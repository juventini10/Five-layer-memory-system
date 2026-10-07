#!/usr/bin/env bash
# registry_guards.sh —— Stop 钩子·登记一致性守卫族自动体检（changelog-guard 族）
# 会话结束自动跑 GUARD_DIR 下全部 *guard.sh（排除 *.bak*）守卫：
#   changelog-guard(变更日志) / skill-version-guard(SKILL↔CHANGELOG) / kb-index-guard(知识池↔INDEX)
#   注: 回复格式合规守卫已迁为 reply_format_guard.py 直接挂 Stop(2026-08-20 单一实装·退役 format_compliance_guard.sh)
# 任何 alarm=true → 输出该守卫 --report 详情；全过 → 一行 ✅（验收可见性：你要看机制真的在跑）。
# 设计: 机械(检测+报警)脚本自动;修正动作留AI/你。挂载=settings.json hooks.Stop 追加(2026-08-06你"挂吧").
# 依据: 记忆琥珀设计哲学§4.10(常态审计须脚本触发) + 守卫族迁移(你"还能用到哪里") + 触发可靠度排序(品格<脚本<机制兜底·你实证签名漏时间).
# 注意: macOS bash 3.2 UTF-8 坑——中文紧跟变量后必须用 ${var},否则多字节字符被误判进变量名.
#
# 【第一性原理根治·2026-08-11】kb-index 守卫静默死（根治一类, 非修一例）
# 旧版用硬编码 GUARDS 数组声明守卫名, 须人工与磁盘文件保持同步 →
#   "kb-index-guard.sh"(连字符) 与磁盘 "kb_index_guard.sh"(下划线) 命名不一致 →
#   `[ -x ] || continue` 静默跳过 → 知识池↔INDEX 一致性 4 天从未自动跑(沉默失败).
# 根因 = "手工维护的名单" 不是单一真相源, 必然漂移(同今早 schema≠pipeline / changelog brace 污染 / WBE-20260529-002 同类根因:
#   "文档/名单的期望" 与 "文件系统/机制的真相" 脱钩, 且无人机械校验一致性).
# 根治 = 让文件系统成为单一真相源: 自动发现 GUARD_DIR 下全部 *guard.sh(排除备份),
#   名单不可能再与磁盘不一致; 新增守卫零配置自动接入. 发现文件不可执行=显式报警(不再静默 continue).
set -uo pipefail
GUARD_DIR="${BULUOTUO_GUARD_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
# 单守卫耗时预算（v2·2026-09-23 童灵根治）：原实现逐个 `bash "$g" --check` **无任何超时保护**——
# 单个守卫卡死即拖垮整条 Stop 链（实证：changelog_guard --check 实测 3 分 24 秒 / 180s user CPU）。
# 20s = 正常守卫秒级完成，超此即性能回归，须**显形**（⛔不静默 continue——那正是本文件
# 开头 §第一性原理根治 批判过的"沉默失败"）。用 perl alarm（macOS 自带·无 GNU timeout）。
GUARD_TIMEOUT="${GUARD_TIMEOUT:-20}"

# —— 第一性原理根治: 文件系统是唯一真相源, 不信任会漂移的手工名单 ——
GUARDS=()
while IFS= read -r f; do GUARDS+=("$f"); done < <(find "$GUARD_DIR" -maxdepth 1 -name '*guard.sh' ! -name '*.bak*' | sort)

alarm_total=0
AUDIT_SKIPPED=()
for g in "${GUARDS[@]}"; do
  name=$(basename "$g")
  # 审计类守卫跳过（v2·2026-09-23 童灵根治）：脚本头部声明 `AUDIT_CLASS=1` = 耗时超 Stop
  # 预算（如 changelog_guard 实测 49s）+ 语义允许滞后 → 不进每轮 Stop，改由定时任务承载。
  # ⛔ 显形不静默：跳过的必须在收尾汇总里列出（否则又是"沉默失败"）。
  if grep -q 'AUDIT_CLASS=1' "$g" 2>/dev/null; then
    AUDIT_SKIPPED+=("$name")
    continue
  fi
  # 发现文件但不可执行 = 显式报警(不再静默 continue)
  [ -x "$g" ] || { echo "⚠️ [$name] 守卫存在但不可执行(chmod +x 缺失)——已跳过并报警"; alarm_total=$((alarm_total+1)); continue; }
  start=$(date +%s)
  # 单守卫超时保护（v2·2026-09-23 童灵根治·根治"无超时即拖垮 Stop 链"）
  # perl alarm = macOS 自带超时原语（无 GNU timeout）；SIGALRM 终止时 exit code = 142
  out=$(perl -e 'alarm shift; exec @ARGV' "$GUARD_TIMEOUT" bash "$g" --check 2>/dev/null)
  rc=$?
  elapsed=$(( $(date +%s) - start ))
  if [ "$rc" -eq 142 ]; then
    alarm_total=$((alarm_total+1))
    echo "⚠️ [$name] 超时 ${GUARD_TIMEOUT}s 被终止（超出耗时预算）——性能回归，须优化或移出 Stop 链"
    continue
  fi
  # 耗时预算断言（2026-08-07 立·根除静默失败）：守卫超 10s = 性能回归，须大声报警非静默超时
  if [ "$elapsed" -gt 10 ]; then
    echo "⚠️ [$name] 耗时 ${elapsed}s 超预算(>10s)——性能回归！检查 O(n²)/循环内子进程"
  fi
  if printf '%s' "$out" | grep -q '"alarm": true'; then
    alarm_total=$((alarm_total+1))
    echo "⚠️ [$name] 登记一致性告警："
    bash "$g" --report 2>/dev/null | head -25
    echo ""
  fi
done

# —— 守卫文档↔机制一致性巡检（2026-08-20 根治"手工名单漂移"）——
# 复用本运行器：每次 Stop 自动比对 §二 声称挂载 vs settings.json 实挂，漂移即报警（可见性对齐 kb-index 沉默死根治）
# 2026-10-03 端中立化：文档核对器优先读脚本中心副本·缺省同目录（⛔ 不指向作者侧目录）
DOC_CHECK="${BULUOTUO_DOC_CHECK:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/guard_doc_consistency.py}"
if [ -f "${DOC_CHECK}" ]; then
  dout=$(python3 "${DOC_CHECK}" 2>&1); drc=$?
  if [ "${drc}" -ne 0 ]; then
    alarm_total=$((alarm_total+1))
    echo "⚠️ [守卫文档一致性·正向] §二 声称的挂载未在 settings.json 落地（虚报）："
    printf '%s\n' "${dout}" | head -20
  fi
  rout=$(python3 "${DOC_CHECK}" --reverse 2>&1)
  if printf '%s' "${rout}" | grep -q '未登记'; then
    alarm_total=$((alarm_total+1))
    echo "⚠️ [守卫文档一致性·反向] 实挂守卫未在 §二 登记（文档遗漏）："
    printf '%s' "${rout}" | grep '未登记' | head -10
  fi
fi

# —— 脚本中心 ↔ scripts_manifest 库存一致性（2026-08-27 半边D·机械对账·防死文档漂移）——
# 每次 Stop 自动比对脚本中心真实脚本 vs scripts_manifest 在册条目：
#   悬空(声称在·磁盘无)=硬漂移报警；孤儿(磁盘有·未入册)=提示(须补登·不阻断).
sc_out=$(python3 "${DOC_CHECK}" --script-center 2>&1)
if printf '%s' "${sc_out}" | grep -q 'scripts_manifest 悬空条目（声称存在'; then
  alarm_total=$((alarm_total+1))
  echo "⚠️ [脚本中心库存·硬漂移] scripts_manifest 声称的脚本磁盘不存在："
  printf '%s\n' "${sc_out}" | grep -A 30 'scripts_manifest 悬空条目（声称存在' | head -20
fi
if printf '%s' "${sc_out}" | grep -q '未入册脚本（提示'; then
  echo "🔍 [脚本中心库存·孤儿] 脚本中心存在未入册脚本（建议补登 scripts_manifest）："
  printf '%s\n' "${sc_out}" | grep -A 30 '未入册脚本（提示' | head -15
fi

if [ "${#AUDIT_SKIPPED[@]}" -gt 0 ]; then
  echo "⏸ 审计类守卫（AUDIT_CLASS=1·超 Stop 预算·由定时任务承载）：$(printf '%s ' "${AUDIT_SKIPPED[@]}")"
fi

if [ "$alarm_total" -eq 0 ]; then
  echo "✅ 登记一致性守卫：自动发现 ${#GUARDS[@]} 个守卫全部通过（$(printf '%s ' "${GUARDS[@]}" | xargs -n1 basename | tr '\n' ' '))"
else
  echo "⚠️ 登记一致性守卫：${alarm_total} 个守卫报不一致（明细如上，须 AI 补记/修复）"
fi
exit 0
