#!/usr/bin/env bash
# panel_live_watch.sh — 面板实时化守护（2026-08-21·愿景: 全自动化·刷新即最新）
# fswatch 监听数据源变化 → 防抖 5s → 自动重渲染 panel_live.html
# 让"已接/缺多少 + 四方向指标读数"随数据源变化自动更新，不依赖人记得手动跑 panel_snapshot.py
# v0.2（2026-08-22·你裁定"看板必须先自动化"·补全自动闭环到源头）：
#   原始数据源（免疫复发记录/规范反哺日志/变更日志/guard 日志）变化 → 幂等重算 evolution json → 重渲染
#   refresh_evolution_data 由"当日json缺失才补"改为"总是重算"（原始日志一写面板即最新·愿景①落地）
set -u
# 2026-09-27 童灵根治：launchd 环境精简 PATH（无 /usr/local/bin）→ command -v fswatch 失败 →
# 静默降级 30s 轮询。此前 fswatch 一直在跑纯因旧进程继承了手工会话环境——kickstart/重启即打回降级。
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# PYTHON 启动前用 env -u 清污染（Trae Work shell 注入 PYTHONHOME/PYTHONPATH，直接调会报 encodings 缺失）
run_py() { env -u PYTHONHOME -u PYTHONPATH python3 "$@"; }
PANEL_PY="[记忆共享中心]/脚本中心/panel_snapshot.py"
EVO_PY="[记忆共享中心]/脚本中心/evolution_deviation.py"
# 2026-09-27 童灵根治：渲染后必须补碰撞合并——panel_snapshot 重渲染会整体覆盖 HTML，
# 冲掉 07:30 链 merge_collision_viz.py 合并的碰撞仪表盘（幂等，重复跑安全）
MERGE_PY="[记忆共享中心]/可视化呈现/scripts/merge_collision_viz.py"
LOG="[记忆共享中心]/脚本中心/logs/panel_live_watch.log"

mkdir -p "$(dirname "$LOG")"

# 监听目标：平台 settings + SSOT 文档 + 指标 json + 原始数据源（免疫/抗体/变更/guard 日志）
# 覆盖全链路：原始日志变化 → refresh evolution json → 重渲染面板（真·全自动·愿景①）
WATCH=(
  "$HOME/.workbuddy/settings.json"
  "$HOME/.qoder-cn/settings.json"
  "$HOME/.qoder/settings.json"
  "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/01-脚本架构设计通用规范.md"
  "[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/04-跨端接入指南.md"
  "~/[记忆共享中心]/自定义层/待完成工作/okr_quarter.json"
  "[记忆共享中心]/脚本中心/logs/runtime/"
  "~/[记忆共享中心]/成长箱/免疫复发记录.md"
  "~/[记忆共享中心]/成长箱/experience/规范反哺日志.md"
  "~/[记忆共享中心]/变更日志.md"
  "[记忆共享中心]/脚本中心/logs/"
)

echo "[panel_live_watch] 启动 $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"

# 演化数据刷新：总是幂等重算当日 json（原始日志变化→重算→渲染·真全自动，非"缺失才补"）
refresh_evolution_data() {
  run_py "$EVO_PY" >> "$LOG" 2>&1
}

# 变更事件 → 防抖 5s → 先重算当日指标再重渲染（防编辑中途多次触发）
on_change() {
  sleep 5
  refresh_evolution_data
  run_py "$PANEL_PY" >> "$LOG" 2>&1 && \
    run_py "$MERGE_PY" >> "$LOG" 2>&1 && \
    echo "[panel_live_watch] 重渲染 $(date '+%H:%M:%S') 数据源变更自动刷新" >> "$LOG" || \
    echo "[panel_live_watch] 重渲染失败 $(date '+%H:%M:%S')" >> "$LOG"
    # v0.3（2026-10-07 野根根治轮·QoderCN）：失败必须显形——原只记日志=静默崩 4 小时无人喊
    python3 -c 'import sys; sys.path.insert(0, "[记忆共享中心]/脚本中心"); import hook_protocol; hook_protocol.alert("刷新守护", "panel_live_watch 重渲染失败·活面板停摆（详见 脚本中心/logs/panel_live_watch.log 末行）")' >> "$LOG" 2>&1 || true
}

# 冷启动自愈：守护拉起即重算当日指标并初始渲染，保证"打开网页即最新"
refresh_evolution_data
run_py "$PANEL_PY" >> "$LOG" 2>&1 && \
  run_py "$MERGE_PY" >> "$LOG" 2>&1 && \
  echo "[panel_live_watch] 初始渲染 $(date '+%H:%M:%S')" >> "$LOG"

# 只响应真正的指标数据源更新：指标 json / okr / settings / SSOT + 原始数据源
# （免疫复发记录/规范反哺日志/变更日志/guard 日志 → 触发 evolution 重算 + 重渲染）
# 双保险：
#  ① fswatch 层 include 正则（OR 集）——提前丢弃无关事件，消洪峰
#  ② should_render 后缀过滤（降级/兜底）——防 include 覆盖不足漏判
# include 是全局作用于所有 WATCH 路径，必须用 OR 集覆盖全部数据源模式，否则精确文件被误滤
FIND_REGEX='(evolution_deviation_.*\.json$|okr_quarter\.json$|settings\.json$|01-脚本架构设计通用规范\.md$|04-跨端接入指南\.md$|免疫复发记录\.md$|规范反哺日志\.md$|变更日志\.md$|platform_adaptation_check\.log$)'

should_render() {
  local changed="$1"
  case "$changed" in
    *"okr_quarter.json"|*"evolution_deviation_"*.json|*.workbuddy/settings.json|*.qoder-cn/settings.json|*.qoder/settings.json|*"01-脚本架构设计通用规范.md"|*"04-跨端接入指南.md"|*"免疫复发记录.md"|*"规范反哺日志.md"|*"变更日志.md"|*"platform_adaptation_check.log")
      return 0 ;;
    *)
      return 1 ;;
  esac
}

if command -v fswatch >/dev/null 2>&1; then
  fswatch -0 --exclude '.*\.git.*' --include "$FIND_REGEX" "${WATCH[@]}" | while IFS= read -r -d '' ev; do
    if should_render "$ev"; then
      on_change
    fi
  done
else
  echo "[panel_live_watch] fswatch 不可用，降级 30s 轮询" >> "$LOG"
  # ⛔ 禁止用 `declare -A`（关联数组）：macOS 自带 bash 3.2.57 不支持，会报
  #    `declare: -A: invalid option` 并直接退出（退出码 1）。
  #    2026-08-29 实锤：这正是崩溃重启循环的根因——KeepAlive=True 且未设
  #    ThrottleInterval，脚本一退出就被立刻拉起，日志持续刷新，
  #    把「每 5-11 秒崩一次」伪装成了「健康在跑」。
  #    修法：改用索引数组按下标对齐 WATCH（bash 3.2 兼容）。
  declare -a LAST_MT
  while true; do
    idx=0
    for f in "${WATCH[@]}"; do
      mt=$(stat -f %m "$f" 2>/dev/null || echo 0)
      prev="${LAST_MT[$idx]:-}"
      if [[ -n "$prev" && "$prev" != "$mt" ]]; then
        on_change
      fi
      LAST_MT[$idx]="$mt"
      idx=$((idx+1))
    done
    sleep 30
  done
fi
