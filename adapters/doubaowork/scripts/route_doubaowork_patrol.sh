#!/bin/bash
# route_doubaowork_patrol.sh v0.2 — 豆包办公统一接入层（拉模式·文件级机械守卫·装机版）
# [包内装机版·与记忆中心作者态 v0.1 同源]
#
# ⚠️ 本文件是「端用户态」派生版（vs 作者态运行时版 v0.1），三处差异（对齐 traework 装机版）：
#   ① 全量占位符化：MC="[记忆共享中心]"，安装时 setup.sh 用 sed 替换真实路径；
#      守卫脚本落 "$MC/脚本中心/"（install_scripts deploy_script_center 三目录平铺），
#      本巡逻脚本落 "$MC/开发工具/Skill路由引擎/scripts/"（plist ProgramArguments 指向此）。
#   ② 缺作者侧自校验腿：⛔不跑 platform_adaptation_check --src doubaowork——
#      该件读作者侧 SSOT（4 端 patrol/five-layer-memory 等），端用户机器不存在，
#      跑了必大量 [BROKEN]；安装期由 verify.sh §1.7 跑一次即可，运行期不留误报。
#   ③ 产物落 "$MC/脚本中心/.patrol"（装机态简化·与守卫同目录）。
#
# 第一性原理接入形态：豆包办公无 CC 式 hooks、无 session_memory 文件（平台边界），
#   需 transcript 的守卫无法机械执行 → launchd 周期只跑文件级机械守卫。
# 运行 3 守卫：
#   ✅ rule_three_layer_guard（只读三文件·版本号+铁律集合一致性）
#   ✅ card_id_guard（CARD_GUARD_HOST=doubaowork·扫立场卡文件名·无库则扫空 pass）
#   ✅ doubaowork_skill_health_guard（豆包专属·Skill 软链生态健康度）
# 创建：2026-08-25（作者态 v0.1）｜ 装机派生：2026-10-12 v0.2（对齐 traework 装机版）
set -u

MC="[记忆共享中心]"
SCRIPTS="$MC/脚本中心"
PATROL_DIR="$MC/脚本中心/.patrol"
STATE="$PATROL_DIR/audit_state_doubaowork.json"
LOCK_DIR="$PATROL_DIR/audit_once_doubaowork.lock"
LOG="$PATROL_DIR/patrol_doubaowork.log"
trap 'rmdir "$LOCK_DIR" 2>/dev/null' EXIT
mkdir -p "$PATROL_DIR"

# 并发锁（mkdir 原子）：launchd 与手动同时触发只跑一个
mkdir "$LOCK_DIR" 2>/dev/null || exit 0

# 心跳（监督：对账 E 账检查连续性，>60min=断链告警）
date +%Y-%m-%dT%H:%M:%S > "$PATROL_DIR/last_run_doubaowork.ts"

# 守卫调用：独立（只读文件/扫文件名·无需转录）；缺件 SKIP 降级不阻塞
run_guard_standalone() {
  local name="$1"; shift
  local path="$1"; shift
  if [ ! -f "$path" ]; then
    echo "[$(date +%H:%M:%S)] $name SKIP（缺件·降级不阻塞）: $path" >> "$LOG"
    return 0
  fi
  env -u PYTHONHOME -u PYTHONPATH python3 "$path" "$@" >> "$PATROL_DIR/$name.out" 2>&1
  local rc=$?
  echo "[$(date +%H:%M:%S)] $name exit=$rc" >> "$LOG"
  return $rc
}

run_guard_standalone rule_three_layer_guard "$SCRIPTS/rule_three_layer_guard.py"
CARD_GUARD_HOST=doubaowork run_guard_standalone card_id_guard "$SCRIPTS/card_id_guard.py" hook
run_guard_standalone doubaowork_skill_health_guard "$SCRIPTS/doubaowork_skill_health_guard.py"

# 状态落盘
printf '{"last_run": "%s", "guards_run": 3, "guards": ["rule_three_layer_guard", "card_id_guard", "doubaowork_skill_health_guard"]}' "$(date +%Y-%m-%dT%H:%M:%S)" > "$STATE" 2>/dev/null

exit 0
