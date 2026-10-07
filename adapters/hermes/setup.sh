#!/usr/bin/env bash
# hermes-adapter-setup.sh — Hermes 端部署（插件 + 路径声明 + 覆盖层 + 挂载）
#
# ⚠️ **本脚本会写用户配置**（与 2026-10-01 旧版"仅打印状态"不同）。
#    旧版理由是"挂载由用户手动完成"——实测那是**假绿**：
#    包里标"✅完整"、承诺"一次装齐"，实装却零插件。
#    ⇒ 2026-10-02 改实装，装完由 plugin_live_gate.py 三关复验。
#
# 设计原则（逐条对应《01-问题台账》）：
#   · **幂等**：重复跑不重复写、不插两份（台账 §3.2）
#   · **只增不覆盖**：已有插件目录先备份再逐文件同步（铁律005 + 宪法 C1-C7）
#   · **不猜端**：所有落点来自 capability.yaml / 环境，不硬编码（端中立）
#   · **装完必验**：调 plugin_live_gate.py，G2 实导不过 ⇒ 非零退出
set -uo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CFG="${DOENGLINGZ_CONFIG_DIR:-$HOME/.hermes}"
PLUGDIR="$CFG/plugins"
DLDIR="$CFG/doenglingz"
SRC_PLUGINS="$PKG/adapters/hermes/plugins"
SRC_SCRIPTS="$PKG/references/scripts"
DRY="${DRY:-0}"                 # 双通道：环境变量 DRY=1（安装器委派契约·2026-10-03）+ --dry-run 参数（人工直跑）
[[ "${1:-}" == "--dry-run" ]] && DRY=1

same_tree() {   # $1=src $2=dst —— ⛔ 只比 src 侧清单
  python3 - "$1" "$2" <<'PY'
import filecmp, os, sys
src, dst = sys.argv[1], sys.argv[2]
if not os.path.isdir(dst):
    print("MISSING"); raise SystemExit(0)
for root, dn, fs in os.walk(src):
    dn[:] = [d for d in dn if d != "__pycache__"]
    for f in fs:
        if f.endswith((".pyc",)) or ".bak" in f:
            continue
        a = os.path.join(root, f)
        rel = os.path.relpath(a, src)
        b = os.path.join(dst, rel)
        if not os.path.isfile(b):
            print("DIFF:" + rel); raise SystemExit(0)
        try:
            if not filecmp.cmp(a, b, shallow=False):
                print("DIFF:" + rel); raise SystemExit(0)
        except OSError:
            print("DIFF:" + rel); raise SystemExit(0)
print("SAME")
PY
}

say() { printf '%s\n' "$*"; }
run() { if [[ $DRY -eq 1 ]]; then say "  [dry] $*"; else "$@"; fi; }

say "[Hermes 端部署] pkg=$PKG"
say "[Hermes 端部署] cfg=$CFG  $( [[ $DRY -eq 1 ]] && echo '(dry-run)' )"

# ── 0. 前置：源在不在 ────────────────────────────────────────────
if [[ ! -d "$SRC_PLUGINS" ]]; then
  say "❌ 包内无插件目录：$SRC_PLUGINS"; exit 2
fi
n_src=$(find "$SRC_PLUGINS" -maxdepth 2 -name plugin.yaml | wc -l | tr -d ' ')
say "[0/7] 源插件 $n_src 个"
if [[ "$n_src" -eq 0 ]]; then say "❌ 源插件为 0——⛔ 拒绝装空"; exit 2; fi

# ── 1. 备份已有插件（只备份将被改动的）────────────────────────────
BK="$DLDIR/backups/plugins-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK"
changed=0
for src in "$SRC_PLUGINS"/*/; do
  name="$(basename "$src")"
  dst="$PLUGDIR/$name"
  if [[ "$(same_tree "$src" "$dst")" != "SAME" ]]; then
    if [[ $DRY -eq 1 ]]; then
      say "  [dry] 备份 $name"; changed=$((changed+1))
    else
      mkdir -p "$BK/$name"
      cp -a "$dst/." "$BK/$name/" 2>/dev/null || true
      say "  备份 $name → ${BK#$HOME/}"; changed=$((changed+1))
    fi
  fi
done
say "[1/8] 备份 $changed 个（无变化的不备份）"

# ── 2. 部署插件（逐目录同步·先清后拷保证删除也同步）───────────────
run mkdir -p "$PLUGDIR"
n_dep=0
for src in "$SRC_PLUGINS"/*/; do
  name="$(basename "$src")"
  dst="$PLUGDIR/$name"
  if [[ "$(same_tree "$src" "$dst")" == "SAME" ]]; then
    continue                      # 幂等：无变化不写
  fi
  run rm -rf "$dst"
  run cp -a "$src" "$dst"
  n_dep=$((n_dep+1))
  say "  部署 $name"
done
say "[2/8] 新装/更新 $n_dep 个（其余幂等跳过）· 落点 $PLUGDIR"

# ── 3. 路径解析器 + 覆盖层落位（插件头部的多路径探测会找到这里）──
run mkdir -p "$DLDIR"
run cp -f "$SRC_SCRIPTS/runtime_paths.py" "$DLDIR/runtime_paths.py"
run cp -f "$SRC_SCRIPTS/path_overlay.py"   "$DLDIR/path_overlay.py"
say "[3/8] 解析器/覆盖层 → ${DLDIR#$HOME/}"

# ── 4. 生成声明 + 覆盖表（由 install_scripts 单一真源算）──────────
if [[ $DRY -eq 1 ]]; then
  say "  [dry] 生成 runtime_paths.json + path_override.py"
else
  # ⚠️ 端中立：⛔ **不把任何作者目录名当默认值**（09:55 事故同族问题）
  MC="${BULUOTUO_MEMORY_CENTER:-}"
  if [[ -z "$MC" || ! -d "$MC" ]]; then
    # 退化：找 HOME 下唯一含「开发工具」的目录，找不到就报错（⛔ 不猜）
    for cand in "$HOME"/*/; do
      [[ -d "${cand}开发工具" ]] || continue
      [[ -n "${_found:-}" ]] && { say "❌ 多个候选记忆中心，拒绝猜：${_found} / ${cand%/}"; exit 2; }
      _found="${cand%/}"
    done
    if [[ -z "${_found:-}" ]]; then
      say "❌ 未找到记忆中心（HOME 下无含「开发工具」的目录）"
      say "   请设 BULUOTUO_MEMORY_CENTER=<你的记忆中心路径> 后重跑"; exit 2
    fi
    MC="$_found"
  fi
  say "  记忆中心 = $MC"
  # ⛔ 直接调函数（不经 CLI：参数面未验证的路径不拿来当主路径）
  run python3 - "$PKG" "$MC" "$CFG" <<'PY'
import importlib.util as il, os, sys
pkg, mc, cfg = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, pkg)
import install_scripts as I
I._CFG_ROOT_ABS = cfg
tbl, w = I.write_runtime_paths(mc, None, cfg_root=cfg)
print("  runtime_paths.json：%d 键 → %s" % (len(tbl), w))
t2, w2 = I.write_path_override(cfg_root=cfg)
print("  path_override.py：%d 键 → %s" % (len(t2), w2))
PY
fi
say "[4/8] 声明与覆盖表就位"

# ── 5. 三关复验（⛔ 装完必验·这是 09:55 事故的直接产物）──────────
if [[ $DRY -eq 1 ]]; then
  say "[5/8] [dry] 跳过复验"
elif [[ -f "$SRC_SCRIPTS/plugin_live_gate.py" ]]; then
  if python3 "$SRC_SCRIPTS/plugin_live_gate.py"; then
    say "[5/8] ✅ 三关全过"
  else
    say "[5/8] ❌ 三关未过——⛔ 装完不可用（详见上方）"; exit 1
  fi
else
  say "[5/8] ⚠️ 闸门脚本缺失——⛔ 无法证明装完能跑（不可视为成功）"; exit 1
fi

# ── 6. 挂载进 plugins.enabled（只增不删·保注释·幂等）──────────────
if [[ $DRY -eq 1 ]]; then
  say "[6/8] [dry] 跳过挂载"
elif [[ -f "$SRC_SCRIPTS/mount_plugins.py" ]]; then
  if python3 "$SRC_SCRIPTS/mount_plugins.py" \
        --config "$CFG/config.yaml" --plugins-dir "$PLUGDIR"; then
    say "[6/8] 挂载完成"
  else
    say "[6/8] ❌ 挂载失败——插件装了但没进 enabled ⇒ 不会生效"; exit 1
  fi
else
  say "[6/8] ❌ 挂载器缺失——⛔ 不可视为成功（插件在盘上但不会被加载）"; exit 1
fi

# ── 7. 运行态三层验证（注册/加载/派发）·⛔ 端上真跑才算装完 ──────
if [[ $DRY -eq 1 ]]; then
  say "[7/8] [dry] 跳过运行态验证"
elif [[ -f "$SRC_SCRIPTS/verify_hermes_runtime.py" ]]; then
  if python3 "$SRC_SCRIPTS/verify_hermes_runtime.py" \
        --config "$CFG/config.yaml" --plugins-dir "$PLUGDIR" \
        --expect-from "$SRC_PLUGINS"; then
    say "[7/8] ✅ 运行态三层全过"
  else
    say "[7/8] ❌ 运行态验证未过——⛔ 装了但用不了（详见上方）"; exit 1
  fi
else
  say "[7/8] ❌ 验证器缺失——⛔ 无法证明端上真能用（不可视为成功）"; exit 1
fi

# ── 8. Skill 软链（端中立·由包内 restore-my-skills.sh 全端扫描）────────
# ⚠️ 2026-10-03 补：此前 7 步全过但 Skill 一个没链上，且**不报错**——
#    「插件装了 ≠ Skill 可用」。Skill 是布洛陀能力的第一入口，漏这一步
#    = 用户拿到一个「装好了但不会用」的包（= 假绿）。
#    权威源（Skill 本体）＝ $MC/技能配置（由安装器先部署），本步只建软链。
if [[ $DRY -eq 1 ]]; then
  say "[8/8] [dry] 跳过 Skill 软链"
elif [[ -f "$PKG/references/skills/restore-my-skills.sh" ]]; then
  if bash "$PKG/references/skills/restore-my-skills.sh" -p "$PKG"; then
    say "[8/8] ✅ Skill 软链完成"
  else
    say "[8/8] ❌ Skill 软链失败——⛔ 插件能用但 Skill 不可用（能力入口断了）"; exit 1
  fi
else
  say "[8/8] ❌ 恢复脚本缺失——⛔ 无法建 Skill 软链（不可视为完整交付）"; exit 1
fi

say ""
say "✅ Hermes 端部署完成。"
say "   插件落点：${PLUGDIR/#$HOME/\~}（$n_dep 个新装/更新，其余幂等跳过）"
say "   声明落点：${DLDIR/#$HOME/\~}/（runtime_paths.json + path_override.py）"
say "   回滚：cp -a '${BK/#$HOME/\~}/<插件名>/.' '${PLUGDIR/#$HOME/\~}/<插件名>/'（本次备份 $changed 个）"
exit 0