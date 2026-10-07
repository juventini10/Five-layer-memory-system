#!/bin/bash
# host_identity_hook.sh — Trae 系「端身份运行期自识别」钩子（SessionStart / UserPromptSubmit）
#
# 为什么存在（2026-09-30 你令）：
#   Trae Work（TRAE SOLO CN·桌面端）与 TraeCode（Trae CN·IDE 端）的 dataFolderName
#   **均为 .trae-cn**，全局规则目录物理共用 → 「靠分目录做端隔离」前提不成立
#   （9-16 那次"端间隔离根治"即栽在这个错误前提上）。
#   正确做法：共享文件端中性 + 运行期自识别（本脚本即自识别载体）。
#
# 判据（环境变量·机械可判·不猜不验不写）：
#   ICUBE_APP_ROOT / ICUBE_PRODUCT_BRAND_NAME / ICUBE_USER_DATA_DIR
#   实证（2026-09-30·Trae Work 会话）：
#     ICUBE_PRODUCT_BRAND_NAME=TRAE SOLO
#     ICUBE_APP_ROOT=/Applications/TRAE SOLO CN.app/Contents/Resources/app
#     ICUBE_USER_DATA_DIR=~/.trae-cn
#     ICUBE_PEER_USER_DATA_DIRS=~/.trae   ← .trae 是 peer（本端不读）
#
# 纪律：纯 bash（免 PYTHONHOME/PYTHONPATH 污染）· 任何异常静默 · 恒 exit 0（不阻断对话）
# 留痕：~/个人AI档案/Trae记忆/hooks-probe/host_identity.log（硬证据·可抽检）
# 回滚：从 ~/.trae-cn/hooks.json 移除本脚本条目即可（改动仅此一处）

set -u
payload="$(cat 2>/dev/null || true)"
ts="$(date '+%Y-%m-%d %H:%M:%S')"

app_root="${ICUBE_APP_ROOT:-}"
brand="${ICUBE_PRODUCT_BRAND_NAME:-}"
user_data="${ICUBE_USER_DATA_DIR:-}"

# 端判定（多重判据·命中即定；未知端不输出身份声明，只留痕）
end_key="unknown"; end_name=""; end_emoji=""
case "${app_root}${brand}" in
  *"TRAE SOLO"*) end_key="traework"; end_name="Trae Work"; end_emoji="🤖" ;;
  *"Trae CN"*)   end_key="traecode"; end_name="TraeCode";  end_emoji="💡" ;;
esac

evt="$(printf '%s' "$payload" | grep -o '"hook_event_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"
sid="$(printf '%s' "$payload" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')"

log_dir="[记忆共享中心]/Trae记忆/hooks-probe"
mkdir -p "$log_dir" 2>/dev/null
printf '[%s] event=%s end=%s brand=%s app_root=%s user_data=%s sid=%s\n' \
  "$ts" "${evt:-<none>}" "$end_key" "$brand" "$app_root" "$user_data" "${sid:-<none>}" \
  >> "$log_dir/host_identity.log" 2>/dev/null

# 端身份声明（供上下文注入）——仅已知端输出；未知端静默（不编造身份）
if [ -n "$end_name" ]; then
  printf '【端身份·运行期自识别】本端=%s %s｜署名=「—— 你的 %s %s」（署名独占一行·永远最后）｜端专属记忆索引与设计哲学包按 IDENTITY.md 判定表取用｜⛔ 本回合不得使用他端署名或他端口径。判据：ICUBE_APP_ROOT=%s\n' \
    "$end_name" "$end_emoji" "$end_name" "$end_emoji" "$app_root"
fi
exit 0