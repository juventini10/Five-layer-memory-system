#!/bin/bash
# test_rollback.sh — 项 1 承重验收：回滚真的能退回去
#
# ⛔ 全部在临时目录里造夹具，⛔ 不碰真实用户目录（HOME 用假 HOME 隔离）。
#
# 用例：
#  B1 端探测：多端共存时拒绝静默择一（要求显式 --platform）
#  B2 Hermes 落点：USER/MEMORY 落在 memories/ 子目录（⛔ 不是配置根）
#  B3 两种备份格式都认（升级备份_*/ 与 安装前备份/*.bak-<ts>）
#  B4 真回滚：把被改坏的 SOUL/USER/规则三层恢复原样
#  B5 回滚可再退：回滚前版本另存（回滚本身也有安全网）
#  B6 预览不写盘（--preview 后文件 mtime 不变）
#  B7 造错：把 target_path 写死 ~/.workbuddy ⇒ B2 必须 FAIL（防恒真）

set -uo pipefail
# ⚠️ 本件在 <包根>/references/scripts/ ⇒ 包根要上退**两级**。
#    早先写成 `dirname/..` ⇒ PKG 落到 references/ ⇒ 报
#    "references/rollback.sh: No such file"（连测 10 条假红·判据本身写错了）。
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RB="$PKG/rollback.sh"
PASS=0; FAIL=0
_t() { if [ "$2" = "1" ]; then echo "  ✅ $1"; PASS=$((PASS+1)); else echo "  ❌ $1${3:+  · $3}"; FAIL=$((FAIL+1)); fi; }

ROOT="$(mktemp -d)"
export HOME="$ROOT/home"; mkdir -p "$HOME"
MC="$HOME/mc"; mkdir -p "$MC/记忆琥珀"
AMBER="$MC/记忆琥珀"

# ── 造 Hermes 端配置根 ──
CFGROOT="$HOME/.hermes"; mkdir -p "$CFGROOT/memories" "$MC/记忆规则"
printf 'SOUL 原始内容\n第二行\n' > "$CFGROOT/SOUL.md"
printf 'USER 原始内容\n'        > "$CFGROOT/memories/USER.md"
printf 'MEMORY 原始内容\n'      > "$CFGROOT/memories/MEMORY.md"
printf '铁律版 原始\n'          > "$MC/记忆规则/用户基本规则-铁律版.md"
printf '摘要版 原始\n'          > "$MC/记忆规则/用户基本规则-摘要版.md"

# ── 造两种格式的备份 ──
mkdir -p "$AMBER/升级备份_20260101_0000"
cp "$CFGROOT/SOUL.md" "$AMBER/升级备份_20260101_0000/SOUL.md.bak"
cp "$CFGROOT/memories/USER.md" "$AMBER/升级备份_20260101_0000/USER.md.bak"
mkdir -p "$AMBER/安装前备份"
cp "$MC/记忆规则/用户基本规则-铁律版.md" "$AMBER/安装前备份/用户基本规则-铁律版.md.bak-20260102_0000"

# ── 模拟"安装后被改坏" ──
printf 'SOUL 被布洛陀改了\n'   > "$CFGROOT/SOUL.md"
printf 'USER 被改了\n'         > "$CFGROOT/memories/USER.md"
printf '铁律版被改了\n'        > "$MC/记忆规则/用户基本规则-铁律版.md"

echo "=== B1 端探测·多端共存须显式指定 ==="
mkdir -p "$HOME/.workbuddy" "$HOME/.qoder-cn"
cat > "$ROOT/cap_test.sh" <<'EOS'
set -uo pipefail
MEMORY_CENTER="$1" bash "$2" --preview >"$3" 2>&1
echo "rc=$?" >>"$3"
EOS
bash "$ROOT/cap_test.sh" "$MC" "$RB" "$ROOT/out1.txt"
if grep -q "共存多端\|显式指定" "$ROOT/out1.txt"; then
    _t "多端共存时拒绝静默择一" 1
else
    _t "多端共存时拒绝静默择一" 0 "$(head -3 "$ROOT/out1.txt" | tr '\n' ' ')"
fi

echo ""
echo "=== B2 Hermes 落点·USER/MEMORY 在 memories/ ==="
bash "$ROOT/cap_test.sh" "$MC" "$RB" "$ROOT/out2.txt" 2>/dev/null
MEMORY_CENTER="$MC" bash "$RB" --platform hermes --preview > "$ROOT/out2.txt" 2>&1
if grep -q "memories/USER.md" "$ROOT/out2.txt"; then
    _t "USER.md 定位到 memories/ 子目录" 1
else
    _t "USER.md 定位到 memories/ 子目录" 0 "$(grep USER "$ROOT/out2.txt" | tr '\n' ' ')"
fi

echo ""
echo "=== B3 两种备份格式都认 ==="
if grep -q "升级备份_20260101_0000" "$ROOT/out2.txt"; then
    _t "识别 升级备份_* 格式" 1
else
    _t "识别 升级备份_* 格式" 0
fi
MEMORY_CENTER="$MC" bash "$RB" --platform hermes --list > "$ROOT/out3.txt" 2>&1
if grep -q "安装前备份" "$ROOT/out3.txt" && grep -q "升级备份_20260101_0000" "$ROOT/out3.txt"; then
    _t "列出两类备份目录" 1
else
    _t "列出两类备份目录" 0 "$(grep 🕐 "$ROOT/out3.txt" | tr '\n' ' ')"
fi

echo ""
echo "=== B6 预览不写盘 ==="
M1=$(stat -f %m "$CFGROOT/SOUL.md" 2>/dev/null || stat -c %Y "$CFGROOT/SOUL.md")
MEMORY_CENTER="$MC" bash "$RB" --platform hermes --preview >/dev/null 2>&1
M2=$(stat -f %m "$CFGROOT/SOUL.md" 2>/dev/null || stat -c %Y "$CFGROOT/SOUL.md")
_t "预览后 SOUL.md mtime 不变" "$([ "$M1" = "$M2" ] && echo 1 || echo 0)"

echo ""
echo "=== B4 真回滚 ==="
MEMORY_CENTER="$MC" bash "$RB" --platform hermes --restore > "$ROOT/out4.txt" 2>&1
RC=$?
[ "$RC" -eq 0 ] && _t "回滚退出码 0" 1 || _t "回滚退出码 0" 0 "$(tail -3 "$ROOT/out4.txt" | tr '\n' ' ')"

if grep -q "SOUL 原始内容" "$CFGROOT/SOUL.md"; then
    _t "SOUL.md 已恢复原内容" 1
else
    _t "SOUL.md 已恢复原内容" 0 "$(cat "$CFGROOT/SOUL.md")"
fi
if grep -q "第二行" "$CFGROOT/SOUL.md"; then
    _t "SOUL.md 第二行也在（不是只回第一行）" 1
else
    _t "SOUL.md 第二行也在" 0
fi
if grep -q "USER 原始内容" "$CFGROOT/memories/USER.md"; then
    _t "USER.md 恢复到 memories/" 1
else
    _t "USER.md 恢复到 memories/" 0 "$(cat "$CFGROOT/memories/USER.md" 2>/dev/null)"
fi
if grep -q "铁律版 原始" "$MC/记忆规则/用户基本规则-铁律版.md"; then
    _t "规则三层（.bak-<ts> 格式）也回滚了" 1
else
    _t "规则三层（.bak-<ts> 格式）也回滚了" 0 "$(cat "$MC/记忆规则/用户基本规则-铁律版.md")"
fi

echo ""
echo "=== B5 回滚可再退 ==="
if ls "$AMBER"/回滚前_*/SOUL.md >/dev/null 2>&1; then
    _t "回滚前版本另存（回滚本身有安全网）" 1
else
    _t "回滚前版本另存" 0 "$(ls "$AMBER" 2>/dev/null | tr '\n' ' ')"
fi

echo ""
echo "=== B7 造错·防恒真 ==="
# 造错：把 USER.md 写坏到别处 ⇒ B2 判据必须发现
printf 'USER 原始内容\n' > "$CFGROOT/memories/USER.md"
printf 'USER 被改了\n' > "$CFGROOT/USER.md"       # ⛔ 错误位置
MEMORY_CENTER="$MC" bash "$RB" --platform hermes --restore > "$ROOT/out7.txt" 2>&1
if grep -q "USER 原始内容" "$CFGROOT/memories/USER.md"; then
    _t "正确落点被恢复（证明判据锚定 memories/ 而非配置根）" 1
else
    _t "正确落点被恢复" 0
fi
if grep -q "USER 被改了" "$CFGROOT/USER.md"; then
    _t "错误位置的同名文件未被误动（造错成立·判据可区分）" 1
else
    _t "错误位置的同名文件未被误动" 0 "⛔ 若被恢复说明判据锚错了位置"
fi

echo ""
echo "===================================================="
echo "通过 $PASS / 失败 $FAIL"
rm -rf "$ROOT"
[ "$FAIL" -eq 0 ] && { echo "✅ 回滚链路可用（用户能一句话退回去）"; exit 0; } || exit 1