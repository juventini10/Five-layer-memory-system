#!/usr/bin/env bash
# skill_selfcontained_guard.sh —— Skill 自包含守卫 · 巡检端适配器（Stop 钩子族）
# Version: 1.0.0 (2026-09-15)
#
# 定位：把 skill_selfcontained_guard.py（跨目录引用机械体检）接到**不依赖 AI 记得**的通道上。
#   挂载方式 = 本文件落于 changelog-guard/ 目录，由 registry_guards.sh 自动发现（零配置接入）。
#   为什么需要这一层（皮叔 2026-09-15 令「全面检查所有 Skill · 从根本上杜绝」）：
#     人工判读不可持续——实测初扫 96 处命中里混着 3 类误报（测试样本/CHANGELOG 历史/自身引用），
#     靠人逐条看必然漏且累 ⇒ 判据下沉脚本（愿景①）。
#
# 接口契约（registry_guards.sh 约定）：--check 输出含 "alarm": true|false 的 JSON；--report 人类可读。
# 依据：Skill架构规范 §11.5 开放引用原则 + §11.6 自包含 litmus test。
# 可逆性：🟢 只读扫描，⛔不改任何 Skill 文件（修法由人/Skill 决定）。

set -uo pipefail

GUARD="[记忆共享中心]/脚本中心/skill_selfcontained_guard.py"
PY=""
for c in "$(command -v python3 2>/dev/null)" /usr/bin/python3 /usr/local/bin/python3; do
  [ -n "$c" ] && [ -x "$c" ] && { PY="$c"; break; }
done

if [ -z "$PY" ] || [ ! -f "$GUARD" ]; then
  echo '{"alarm": false, "skipped": "guard 或 python3 缺失"}'
  exit 0
fi

case "${1:---check}" in
  --check)
    # ⚠️ 必须捕获输出后再判空——直接 `cmd || echo skipped` 会在 exit 1（有违规）时
    # 同时打印正常 JSON 与 skipped 行（2026-09-15 实测双输出 bug）。
    out=$("$PY" "$GUARD" --check 2>/dev/null) || true
    if [ -n "$out" ]; then printf '%s\n' "$out"; else echo '{"alarm": false, "skipped": "scan 无输出"}'; fi
    ;;
  --report)
    "$PY" "$GUARD" 2>&1 | head -40
    ;;
  *)
    echo "用法: skill_selfcontained_guard.sh [--check|--report]"
    ;;
esac

exit 0
