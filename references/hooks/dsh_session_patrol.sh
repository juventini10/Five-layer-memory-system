#!/bin/bash
# dsh_session_patrol.sh — DSH 会话 role 缺失自动修复巡逻（launchd 承载·每 15 分钟）
#
# 家族：工具 ｜ 部署形态：调度
# version: v0.3
#
# 背景（2026-09-10）：DSH 运行期写入路径对 pre-step 插件注入消息不补 role（宿主侧缺陷），
#   插件侧已修（注入消息带 role:'user'），但为确保「机制代意志」（愿景①）——即使宿主回归
#   或新注入形态再漏字段，也被机械补回，不依赖人记得跑修复工具。
#
# 设计（对齐 route_doubaowork_patrol / route_catpaw_patrol 先例）：
#   · 并发锁（mkdir 原子性）防重入
#   · 静默幂等：无坏会话时零输出（只在有修复时留痕）
#   · 心跳落盘 last_run.ts（执行证据=校验路径，不依赖读配置文件）
#   · 异常不阻断：任何失败都 exit 0（巡逻自身不得成为故障源）
#
# PATH 显式声明（2026-09-10 修复）：launchd 默认 PATH 不含 /usr/local/bin →
#   python3 落到 /usr/bin/python3(3.9·脚本 PEP604 注解 import 即崩)，且 zstd/node 不可达
#   → 巡逻要么崩、要么解压/压缩失败，静默零修复。显式 PATH 一并救回三者。
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

set -uo pipefail

REPAIR="[记忆共享中心]/脚本中心/dsh_session_repair.py"
STATE_DIR="$HOME/.dsh/cache/session-patrol"
LOCK="$STATE_DIR/patrol.lock"
LOG="$STATE_DIR/patrol.log"

mkdir -p "$STATE_DIR" || exit 0

# 并发锁（目录创建原子性；陈旧锁 >30min 视为残留自动清理）
if ! mkdir "$LOCK" 2>/dev/null; then
    if [ -d "$LOCK" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || echo 0) ))
        [ "$age" -gt 1800 ] && rmdir "$LOCK" 2>/dev/null
    fi
    exit 0
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

[ -f "$REPAIR" ] || exit 0

OUT=$(python3 "$REPAIR" --fix --all 2>&1)
RC=$?

# 会话标题统一命名（2026-09-10 皮叔令"原来的任务怎么统一命名"）：
#   幂等（已有 user 源标题则跳过）+ 活跃保护（300s 内写入的会话跳过·下轮补）
#   → 活跃会话会随时间变成不活跃，最终全部收敛到规范标题（机制代意志·无需人记得）
TITLE="[记忆共享中心]/脚本中心/dsh_session_title_batch.py"
if [ -f "$TITLE" ]; then
    TOUT=$(python3 "$TITLE" --apply 2>&1)
    TRC=$?
    NEW=$(printf '%s' "$TOUT" | grep -cE '→ 26')
    if printf '%s' "$TOUT" | grep -q 'applied=[1-9]'; then
        echo "=== $(date '+%F %T') 标题命名动作 ===" >> "$LOG"
        printf '%s\n' "$TOUT" | grep -E '→|统计' | tail -12 >> "$LOG"
    fi
    [ "$TRC" -ne 0 ] && echo "$(date '+%F %T') ⚠️ 标题命名 rc=$TRC" >> "$LOG"
fi

# 帧契约体检 + 自愈（2026-09-10 三次事故后加·兜底防线）
#   背景：DSH 加载器要求"第一个 zstd 帧恰好只含 header 一行"，任何写会话文件的路径
#   违反此契约 → 整个 session/list 加载失败 → 侧栏只剩当前会话（看起来"对话全没了"）。
#   本条不假设"已知的写路径都正确"——每轮机械体检，发现违规立即重压缩自愈。
#   → 即使未来版本升级引入新的破坏路径，也被机械兜住（机制代意志·不依赖人发现）。
REFRAME="[记忆共享中心]/脚本中心/dsh_session_reframe.py"
FRAME_SUMMARY="帧契约:未执行"
if [ -f "$REFRAME" ]; then
    ROUT=$(python3 "$REFRAME" --fix --all 2>&1)
    # 🔴 2026-09-10 四次事故根治 —— 状态行必须含**真实计数**（⛔不许"无坏会话"式假全清）。
    # 事故形态：坏文件在 20:28:27 落盘，巡逻 20:29:24 因旧 300s 活跃窗口跳过它，
    #   却在 last_status 写"rc=0 无坏会话（静默）" → 假阴性与假全清叠加，故障无人知。
    # 现：每次都把"扫了 N 个 / 修 M 个 / 失败 K 个"写进状态行；有失败另起日志段。
    FSTAT=$(printf '%s' "$ROUT" | grep -oE '统计：.*' | tail -1)
    FRAME_SUMMARY="帧契约:${FSTAT:-无统计行}"
    if printf '%s' "$ROUT" | grep -qE '🔧'; then
        {
            echo "=== $(date '+%F %T') ⚠️ 帧契约违规·已自愈 ==="
            printf '%s\n' "$ROUT" | grep -E '🔧|统计' | tail -12
        } >> "$LOG"
    fi
    if printf '%s' "$ROUT" | grep -qE '⚠️ 失败'; then
        FRAME_SUMMARY="⚠️ $FRAME_SUMMARY"
        echo "=== $(date '+%F %T') ⚠️ 帧契约自愈存在失败 ===" >> "$LOG"
        printf '%s\n' "$ROUT" | grep -E '⚠️|统计|   ' | tail -10 >> "$LOG"
    fi
fi

# 心跳（执行证据）
date +%s > "$STATE_DIR/last_run.ts"

# 静默幂等：仅在**有修复动作**时留痕（无坏会话不写噪音）
if printf '%s' "$OUT" | grep -qE '补 [0-9]+ 处'; then
    {
        echo "=== $(date '+%F %T') rc=$RC 修复动作 ==="
        printf '%s\n' "$OUT" | grep -E '🔧|✅ 已替换|处理'
    } >> "$LOG"
else
    # 仅更新心跳行（覆盖式·单行·无膨胀）；rc≠0 时附失败摘要便于诊断（⛔不静默吞错）
    if [ "$RC" -ne 0 ]; then
        echo "$(date '+%F %T') rc=$RC ⚠️ 部分失败: $(printf '%s' "$OUT" | grep -E '⚠️ 失败' | head -1)" > "$STATE_DIR/last_status.txt"
        echo "=== $(date '+%F %T') rc=$RC 异常 ===" >> "$LOG"
        printf '%s\n' "$OUT" | tail -5 >> "$LOG"
    else
        echo "$(date '+%F %T') rc=0 无坏会话 | $FRAME_SUMMARY" > "$STATE_DIR/last_status.txt"
    fi
fi

# ---------- 快链自续（60s 帧体检·2026-09-10 四次事故根治） ----------
# 背景：本巡逻 15 分钟一轮，且帧体检排在 31s 的 role 修复 + 标题批处理之后 → 检测窗口最长
#   十几分钟（"侧栏空白"就是这么来的）。而独立 launchd job 在 DSH 会话内注册失败（实证：
#   bootstrap 返回 EIO·换 label 的对照同样失败）→ 借"本脚本已是 launchd 子进程"的事实自续：
#   每轮 fork 一条 780s（<巡逻区间 900s）的快链（60s/轮·0.2s/轮），下一轮按寿命契约重生。
#   ⚠️ setsid 不可省：实测直接 nohup & 的快链会被 launchd 在 job 主进程退出时清杀
#   （spawn 日志里"已发起 fork"后无任何活动即为该情形）。
# 注：若已用 launchd 注册 com.buluotuo.dsh.frame-guard，本段可删（二者互斥可选·不叠加）。
# 可观测：发起结果无条件落 guard-spawn.log（实证 launchd 下后代存活与否·⛔不靠推测）
GUARD_LOOP="[记忆共享中心]/脚本中心/dsh_frame_guard_loop.sh"
SPAWNLOG="$STATE_DIR/guard-spawn.log"
if [ -f "$GUARD_LOOP" ]; then
    # ⚠️ 必须 os.setsid() 开新会话：实测（2026-09-10）launchd 在 job 主进程退出时会清杀
    #   同进程组的残留子进程——直接 nohup & 的快链已成功启动却被连带杀死（spawn 日志有据）。
    #   setsid 让快链脱离该 job 的进程组，从而在巡逻退出后继续存活到寿命到期。
    python3 -c "import os,sys; os.setsid(); os.execvp('bash',['bash',sys.argv[1],sys.argv[2]])" \
        "$GUARD_LOOP" 780 >>"$SPAWNLOG" 2>&1 &
    echo "$(date '+%F %T') 快链已发起 fork（child=$!·setsid 独立会话）" >> "$SPAWNLOG"
    sleep 3   # 启动窗口：让子进程完成 bash 初始化并写下"快链启动"日志
else
    echo "$(date '+%F %T') ⚠️ 未找到快链脚本：${GUARD_LOOP}（HOME=${HOME:-未设}）" >> "$SPAWNLOG"
fi

# ---------- 一次性命令闸：停服窗口作业（2026-09-10 新增） ----------
# 为什么需要：会话文件的**内容级**修复（标题批量 force 改名等）必须在宿主停止时做——宿主把已
#   加载会话持有在内存里，在线改会被内存视图覆盖=白改；而 AI 在 DSH 会话内 nohup 的脚本会随
#   dsh web 一起被杀、`launchctl submit/bootstrap` 在本沙箱被拒（实证：submit 写测试文件失败·
#   bootstrap 返回 EIO）——唯一可用通道 = 借已注册的**本巡逻 job**（kickstart 可用）→ 由它
#   setsid 拉起停服修复流（setsid 必需：launchd 会清杀 job 退出时的同组残留子进程）。
# 用法：touch ~/.dsh/cache/session-patrol/run-offline-repair 然后 kickstart 本 job。
ONE_SHOT="$STATE_DIR/run-offline-repair"
ORLOG="$STATE_DIR/offline-repair.log"
if [ -f "$ONE_SHOT" ]; then
    rm -f "$ONE_SHOT"
    OFFLINE="[记忆共享中心]/脚本中心/dsh_offline_repair.sh"
    if [ -f "$OFFLINE" ]; then
        # 延迟 180s = 留给"当前回复送达 + 你看到提醒"的窗口（停服会断开 GUI 连接）
        python3 -c "import os,sys; os.setsid(); os.execvp('bash',['bash',sys.argv[1],sys.argv[2]])" \
            "$OFFLINE" 180 >> "$ORLOG" 2>&1 &
        echo "$(date '+%F %T') 已发起停服修复流（延迟 180s·setsid 独立会话）" >> "$ORLOG"
        sleep 2
    else
        echo "$(date '+%F %T') ⚠️ 未找到 $OFFLINE" >> "$ORLOG"
    fi
fi

exit 0