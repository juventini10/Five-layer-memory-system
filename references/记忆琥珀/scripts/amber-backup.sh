#!/bin/bash
# amber-backup.sh — 记忆琥珀自动备份脚本（共享引擎 · macOS）
# 归属：记忆琥珀/engine/（所有工具共用的中性位置，不绑定任何单一工具）
# 设计原则（第一性原理）：
#   1. 备份目的 = 回滚到"能用的版本"，不是归档
#   2. 版本号 = 时间戳 + 内容哈希前6位（不依赖文件内字段）
#   3. 清理 = 同日只留1份 + 7天保留 + major永久
#   4. 去重 = 内容哈希相同则跳过（防止 touch 误触发）

set -euo pipefail

AMBER_DIR="$HOME/个人AI档案/记忆琥珀"
WHITELIST="$HOME/个人AI档案/记忆琥珀/engine/amber-whitelist.txt"
LOG_FILE="$HOME/个人AI档案/记忆琥珀/engine/logs/amber.log"
LOCK_FILE="/tmp/amber-backup.lock"
RETENTION_DAYS=7

mkdir -p "$AMBER_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# 防竞态：如果已有备份在跑，直接退出
if [ -f "$LOCK_FILE" ]; then
  pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    log "已有备份进程在跑 (pid=$pid)，跳过"
    exit 0
  fi
  # 锁文件残留，清理
  rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# 计算文件内容哈希前6位
compute_hash() {
  local file="$1"
  shasum -a 256 "$file" 2>/dev/null | awk '{print substr($1, 1, 6)}'
}

# 获取文件标识（用父目录+文件名，避免不同 Skill 的 SKILL.md 冲突）
get_base_name() {
  local file="$1"
  local parent
  parent=$(basename "$(dirname "$file")")
  local filename
  filename=$(basename "$file")
  # 去掉 .md / .py / .json 后缀
  local name_no_ext
  name_no_ext="${filename%.*}"
  # 如果文件名是 SKILL.md 这种通用名，用 父目录_文件名
  if [ "$name_no_ext" = "SKILL" ] || [ "$name_no_ext" = "MEMORY" ] || [ "$name_no_ext" = "SOUL" ] || [ "$name_no_ext" = "USER" ] || [ "$name_no_ext" = "IDENTITY" ] || [ "$name_no_ext" = "AGENTS" ]; then
    echo "${parent}_${name_no_ext}"
  else
    echo "$name_no_ext"
  fi
}

# 检查是否需要备份（跟最新 .bak 的哈希比）
need_backup() {
  local file="$1"
  local basename
  basename=$(get_base_name "$file")

  # 找最新的同 basename 备份
  local latest_bak
  latest_bak=$(ls -t "$AMBER_DIR"/${basename}_*.bak 2>/dev/null | head -1)

  if [ -z "$latest_bak" ]; then
    return 0  # 没有备份，需要备份
  fi

  # 从最新备份文件名提取哈希
  # 文件名格式：{basename}_{YYYYMMDD-HHMMSS}_{hash6}.bak
  local latest_hash
  latest_hash=$(echo "$latest_bak" | sed -E 's/.*_([a-f0-9]{6})\.bak$/\1/')

  local current_hash
  current_hash=$(compute_hash "$file")

  if [ "$latest_hash" = "$current_hash" ]; then
    return 1  # 哈希相同，跳过
  fi
  return 0  # 哈希不同，需要备份
}

# 执行备份
do_backup() {
  local file="$1"
  local basename
  basename=$(get_base_name "$file")

  local timestamp
  timestamp=$(date '+%Y%m%d-%H%M%S')

  local hash6
  hash6=$(compute_hash "$file")

  local bak_name="${basename}_${timestamp}_${hash6}.bak"
  local bak_path="$AMBER_DIR/$bak_name"

  cp "$file" "$bak_path"
  log "已备份: $file → $bak_path"
}

# 清理过期备份（同日只留最后1份 + 超过7天删除，major 永久保留）
cleanup() {
  # 1. 先删超过7天的非 major 备份（用文件名里的时间戳判断，不用 mtime）
  local today_date
  today_date=$(date '+%Y%m%d')
  local cutoff_date
  cutoff_date=$(date -v-${RETENTION_DAYS}d '+%Y%m%d' 2>/dev/null || date -d "-${RETENTION_DAYS} days" '+%Y%m%d' 2>/dev/null || echo "")
  while IFS= read -r f; do
    local fname
    fname=$(basename "$f")
    # 从文件名提取 YYYYMMDD
    local bak_date
    bak_date=$(echo "$fname" | sed -E 's/.*_([0-9]{8})-([0-9]{6})_([a-f0-9]{6})\.bak$/\1/')
    # 如果提取不出来跳过
    [[ ! "$bak_date" =~ ^[0-9]{8}$ ]] && continue
    # 对比日期（字符串比较即可，YYYYMMDD 格式）
    if [ -n "$cutoff_date" ] && [ "$bak_date" -lt "$cutoff_date" ]; then
      rm -f "$f"
      log "清理-过期7天+: $f"
    fi
  done < <(find "$AMBER_DIR" -name "*.bak" -not -name "*_major_*" 2>/dev/null)

  # 2. 同 basename + 同日期，只留时间戳最大的
  #     只处理 1 天前的备份（今天创建的不碰，防止刚备份就被删）
  #     用文件名里的 YYYYMMDD-HHMMSS 排序，不用 mtime
  local today
  today=$(date '+%Y%m%d')
  local tmpfile
  tmpfile=$(mktemp)
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    local fname
    fname=$(basename "$f")
    # 提取 basename、YYYYMMDD 和 YYYYMMDD-HHMMSS
    local base_part date_part ts_part
    base_part=$(echo "$fname" | sed -E 's/^(.+)_([0-9]{8})-[0-9]{6}_[a-f0-9]{6}\.bak$/\1/')
    date_part=$(echo "$fname" | sed -E 's/^(.+)_([0-9]{8})-[0-9]{6}_[a-f0-9]{6}\.bak$/\2/')
    ts_part=$(echo "$fname" | sed -E 's/^(.+)_([0-9]{8})-([0-9]{6})_[a-f0-9]{6}\.bak$/\2\3/')
    # 跳过今天的备份
    [ "$date_part" = "$today" ] && continue
    printf '%s|%s|%s|%s\n' "$base_part" "$date_part" "$ts_part" "$f"
  done < <(find "$AMBER_DIR" -maxdepth 1 -name "*.bak" -not -name "*_major_*" 2>/dev/null) > "$tmpfile"

  # 对每组 (base_part, date_part)，按 ts_part 降序，保留最大的，其余删除
  sort -t'|' -k1,1 -k2,2 -k3,3nr "$tmpfile" | awk -F'|' '
    {
      key = $1 "|" $2
      path = ""
      for (i=4; i<=NF; i++) path = path (i>4 ? "|" : "") $i
      if (key != prev_key) {
        prev_key = key
        next  # 保留该组第一行（时间戳最大）
      }
      print path  # 其余打印路径，待删除
    }
  ' | while IFS= read -r to_del; do
    [ -z "$to_del" ] && continue
    rm -f "$to_del"
    log "清理-同日去重: $to_del"
  done
  rm -f "$tmpfile"
}

# 全局计数器（供 backup_one 递增，main 之外也可见）
BACKED_UP=0
SKIPPED=0
MISSING=0

# 备份单个文件
#   $1 = 文件路径
#   $2 = 根目录（目录条目递归时传入，用于生成含相对路径的唯一 basename；空=顶层文件）
backup_one() {
  local file="$1"
  local root="${2%/}"   # 去掉尾部斜杠，便于 ${file#$root/} 截取相对路径
  local bn
  if [ -n "$root" ]; then
    # 用相对路径作 basename（/ → __），避免不同子目录下同名文件冲突
    bn=$(echo "${file#$root/}" | sed 's#/#__#g; s/\.[^.]*$//')
  else
    bn=$(get_base_name "$file")
  fi

  local latest_bak
  latest_bak=$(ls -t "$AMBER_DIR"/${bn}_*.bak 2>/dev/null | head -1 || true)
  local current_hash
  current_hash=$(compute_hash "$file")

  if [ -n "$latest_bak" ]; then
    local latest_hash
    latest_hash=$(echo "$latest_bak" | sed -E 's/.*_([a-f0-9]{6})\.bak$/\1/')
    if [ "$latest_hash" = "$current_hash" ]; then
      SKIPPED=$((SKIPPED + 1))
      log "跳过-内容未变: $file"
      return
    fi
  fi

  local timestamp
  timestamp=$(date '+%Y%m%d-%H%M%S')
  local bak_name="${bn}_${timestamp}_${current_hash}.bak"
  local bak_path="$AMBER_DIR/$bak_name"
  cp "$file" "$bak_path"
  log "已备份: $file → $bak_path"
  BACKED_UP=$((BACKED_UP + 1))
}

# 主流程
main() {
  log "=== 记忆琥珀备份开始 ==="

  if [ ! -f "$WHITELIST" ]; then
    log "错误：白名单文件不存在 $WHITELIST"
    exit 1
  fi

  while IFS= read -r line || [ -n "$line" ]; do
    # 跳过注释和空行
    line=$(echo "$line" | sed 's/#.*//' | xargs)
    [ -z "$line" ] && continue

    # 目录条目：递归备份内部所有文件（支持记忆蓝图等目录级守护）
    if [ -d "$line" ]; then
      while IFS= read -r -d '' f; do
        [ -f "$f" ] || continue
        case "$(basename "$f")" in
          ".DS_Store") continue ;;
        esac
        backup_one "$f" "$line"
      done < <(find "$line" -type f -print0)
      continue
    fi

    if [ ! -f "$line" ]; then
      log "警告：文件不存在 $line"
      MISSING=$((MISSING + 1))
      continue
    fi

    backup_one "$line" ""
  done < "$WHITELIST"

  cleanup

  log "完成：备份 $BACKED_UP / 跳过 $SKIPPED / 缺失 $MISSING"
  log "=== 记忆琥珀备份结束 ==="
}

main "$@"
