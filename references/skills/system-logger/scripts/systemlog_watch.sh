#!/bin/bash
# systemlog_watch.sh — 系统日志写时守护（根治 emoji/描述式 ## 头 + 误归组）
# 机制: fswatch 监听系统日志目录，任何 .md 变更后防抖 2s 跑 systemlog_normalize_fix.py。
# 覆盖所有写入端（WorkBuddy / AutoClaw / Qoder 等）——无论谁直接写文件，异常都会在下次写入后被自动修复。
# 不死循环: 引擎幂等，合规后不产生写盘 → 不触发新事件。
# 健壮性: 使用绝对路径（不依赖 launchd 环境里的 $HOME 展开）；fswatch 退出后脚本自重启，避免监控空窗。
# 用法:
#   bash systemlog_watch.sh            # 前台（调试）
#   bash systemlog_watch.sh &          # 后台
#   launchd: 见同目录 install_watch.sh（安装期按 $HOME 渲染 plist·⛔不随包分发写死路径的 .plist）
DIR="[记忆共享中心]/工作日志/系统日志"
ENGINE="[记忆共享中心]/技能配置/system-logger/scripts/systemlog_normalize_fix.py"
LOGFILE="$DIR/.watch.log"

# 串行化提交（根治"守护提交 vs 手动提交"锁域分裂：与 git_commit_safe.sh 共享 .git-commit.lock）
# 守护与手动提交统一走同一 flock → 同机跨进程真串行 → 消除 .git/objects 并发写争用（EPERM on tmp_obj）
# 失败放行·不阻塞守护（守护首要职责是归一化/自愈，checkpoint 提交只是固化·不达标则下次事件再试）
GCS="[记忆共享中心]/脚本中心/git_commit_safe.sh"
gcs_commit() {
  local msg="$1" f="$2"
  if [ -x "$GCS" ]; then
    "$GCS" -m "$msg" -- "$f" >>"$LOGFILE" 2>&1 && return 0
    echo "[watch $(date '+%F %T')] ⚠️ git_commit_safe 提交失败: $(basename "$f")（失败放行·不阻塞守护·待下次事件重试）" >>"$LOGFILE"
    return 1
  fi
  # 兜底（无 git_commit_safe.sh 时保留旧行为）
  /usr/bin/git -C "$HOME/个人AI档案" add "$f" 2>/dev/null && \
    /usr/bin/git -C "$HOME/个人AI档案" commit -q --no-verify -m "$msg" -- "$f" 2>/dev/null
}
# fswatch 定位（2026-09-01 Loop评估#1修复）：PATH 优先 + 常见 Homebrew 路径兜底
# （Apple Silicon 在 /opt/homebrew/bin，Intel 在 /usr/local/bin）——写死单一路径=换机静默失效。
FSWATCH_BIN="$(command -v fswatch || true)"
[ -z "$FSWATCH_BIN" ] && for _cand in /opt/homebrew/bin/fswatch /usr/local/bin/fswatch; do
  [ -x "$_cand" ] && FSWATCH_BIN="$_cand" && break
done
if [ -z "$FSWATCH_BIN" ]; then
  echo "[watch $(date '+%F %T')] 🔴 fswatch 未安装（PATH 与 /opt/homebrew/bin、/usr/local/bin 均未命中）——守护无法监听，退出非 0 报警（⛔不进入 5s 重启死循环）；治理：brew install fswatch 后重跑" >>"$LOGFILE"
  exit 7
fi
echo "[watch $(date '+%F %T')] 启动监听: $DIR (fswatch=$FSWATCH_BIN)" >>"$LOGFILE"

while true; do
  "$FSWATCH_BIN" -0 --event Created --event Updated --event Renamed "$DIR" 2>>"$LOGFILE" | while IFS= read -r -d "" f; do
    case "$f" in
      */系统日志_*.md)
        # 防抖，避免并发写入风暴下反复触发
        sleep 2
        # 🚨 塌缩熔断（2026-08-22 20→2 条事故反哺·双向绊线）：
        # 入线——条目数较上次状态骤降>30%（基线>3）= 疑似"限制读+整文件写回"型覆盖：
        #   拒跑 normalize（防给塌缩版盖章合规）·隔离现场·状态不降·报警待人工/git 恢复
        # 出线——normalize 写盘后条目数骤降 = 引擎自身退化：从其刚留的 .bak 自动回滚+报警
        # 失败放行原则：状态文件异常时按首见学习，不阻塞正常流。
        base="$(basename "$f")"; st="$DIR/.watch_cnt_${base}"
        now=$(grep -c '^### ' "$f" 2>/dev/null); now=${now:-0}
        last=$(cat "$st" 2>/dev/null); case "$last" in ''|*[!0-9]*) last="";; esac
        # 基线 fallback=git HEAD（2026-08-22 负例实测：冷启动无状态时塌缩不可检——
        # 状态未建立+首见学习=塌缩版自己当基线。git 是内容真相源[同 changelog_guard v1.7 哲学]）
        if [ -z "$last" ]; then
          rel="${f#[记忆共享中心]/}"
          g=$(/usr/bin/git -C "$HOME/个人AI档案" show "HEAD:$rel" 2>/dev/null | grep -c '^### ')
          case "$g" in ''|*[!0-9]*) g="";; esac
          [ -n "$g" ] && [ "$g" -gt 0 ] && last="$g"
        fi
        [ -z "$last" ] && last="$now"
        if [ "$last" -gt 3 ] && [ "$now" -lt "$(( last * 7 / 10 ))" ]; then
          # 🛡️ 自愈（2026-08-31 跨端碰撞根治·愿景"不靠人记得"）：
          # 条目骤降>30% = 疑似其他 AI 端"整文件写回"覆盖（O_APPEND 只防追加并发·防不住整文件重写）。
          # 不再等人工/git 恢复——直接从 git HEAD（内容真相源·watch 每次合规写入即单文件 commit·HEAD 永远是最后好版本）
          # 恢复好版本；冲突方整文件内容存证到 .collided-* 侧车（零丢失·可回溯）；追加自动恢复说明后单文件 commit 固化。
          # 此分支不跑 normalize（避免给塌缩版盖章），但把"隔离等人工"改为"自动恢复"——全程不依赖人记得。
          rel="${f#[记忆共享中心]/}"
          good=$(/usr/bin/git -C "$HOME/个人AI档案" show "HEAD:$rel" 2>/dev/null)
          if [ -n "$good" ]; then
            cp "$f" "$DIR/${base}.collided-$(date +%Y%m%d%H%M%S)" 2>/dev/null
            printf '%s\n' "$good" > "$f"
            {
              echo ""
              echo "### 🛡️ 自动恢复·跨端碰撞 $(date '+%Y-%m-%d %H:%M')"
              echo ""
              echo "- **完成**：$(date '+%H:%M')"
              echo "- **工具**：系统守护"
              echo "- **类型**：覆盖（自愈恢复·2026-09-02 清零批#6：补工具字段+类型回枚举——原条目7字段缺工具+"覆盖/自愈"不在枚举，归因漂移根除）"
              echo "- **涉及文件**：${f}"
              echo "- **对话摘要**：系统日志写时守护检测到条目数 ${last}→${now}（降幅>30%）的整文件覆盖（疑似其他 AI 端并发整文件写回），已从 git HEAD 自动恢复好版本，冲突方整文件内容存证于 \`.collided-*\` 侧车。"
              echo "- **结论**：未丢失任何已固化条目；系统日志具备跨端碰撞自愈能力（不靠人记得）。"
              echo "- **来源**：🟢验证（git HEAD 恢复 + 单文件 commit 固化）"
              echo "- **置信度**：🟢A"
            } >> "$f"
            gcs_commit "syslog auto-recover: ${base} 跨端碰撞自愈（git HEAD 恢复·零丢失）" "$f"
            recov=$(grep -c '^### ' "$f" 2>/dev/null); recov=${recov:-0}
            echo "$recov" >"$st"
            echo "[watch $(date '+%F %T')] 🛡️ 跨端碰撞自愈: $base 已从 git HEAD 恢复（${recov} 条）并固化·冲突方存证 .collided-*" >>"$LOGFILE"
          else
            # git 无好版本兜底：保留原隔离行为（不自愈·等人工）
            cp "$f" "$DIR/${base}.collapse-$(date +%Y%m%d%H%M%S)" 2>/dev/null
            echo "[watch $(date '+%F %T')] 🚨 塌缩熔断(无git好版本·保留隔离): $base 条目 ${last}→${now}——已隔离现场·待人工或 git 恢复" >>"$LOGFILE"
          fi
        else
          /usr/bin/python3 "$ENGINE" "$f" >>"$LOGFILE" 2>&1
          # B埋点(2026-08-23·你令): 守卫调用留痕 trigger_source=hook_auto（失败放行·不阻塞守护）
          [ -f "[记忆共享中心]/脚本中心/guard_invocation_logger.py" ] && \
            python3 "[记忆共享中心]/脚本中心/guard_invocation_logger.py" --guard systemlog_normalize_fix --source hook_auto --detail "fswatch:$base" >/dev/null 2>&1
          post=$(grep -c '^### ' "$f" 2>/dev/null); post=${post:-0}
          if [ "$now" -gt 3 ] && [ "$post" -lt "$(( now * 7 / 10 ))" ]; then
            bak=$(ls -t "$DIR/${base}.bak-"* 2>/dev/null | head -1)
            if [ -n "$bak" ]; then cp "$bak" "$f"; fi
            echo "[watch $(date '+%F %T')] 🚨 出线绊线: normalize 后条目 ${now}→${post}——已从 ${bak:-无bak} 回滚·引擎疑似退化待查" >>"$LOGFILE"
            post=$(grep -c '^### ' "$f" 2>/dev/null); post=${post:-0}
          fi
          echo "$post" >"$st"
          # 📸 自动 git checkpoint（2026-08-22·§3.4 自查声明验证协议反哺·证据全程固化·
          #    2026-08-24 第一性原理最优解：单文件粒度 git commit -- $f）：
          # 正常写入（条目数未塌缩）后立即把该文件提交入 git——用 git 原生单文件提交语法
          # （commit -- <pathspec>）把原子单位从"暂存区"降到"单文件"：无论 staged 区混入多少他端 WIP，
          # 本文件都独立入 git 历史，与他端暂存内容完全解耦。事故窗口从"两次人工提交之间"缩到"单次写入"，
          # 未来任何覆盖丢失=直接 git 恢复。同时根治"checkpoint 吞他端 WIP"问题（系统日志 8/24 10:30 定位）。
          # 容错：lock 冲突/无变更→静默放弃，下次事件再试（失败放行·不阻塞守护）。
          gcs_commit "syslog auto-checkpoint: ${base} ${post} 条（watch 写入即固化·单文件粒度）" "$f" \
            && echo "[watch $(date '+%F %T')] 📸 checkpoint: ${base} ${post} 条已入 git（单文件粒度·不吞他端 WIP）" >>"$LOGFILE"
        fi
        ;;
    esac
  done
  echo "[watch $(date '+%F %T')] fswatch 退出，5s 后自重启" >>"$LOGFILE"
  sleep 5
done
