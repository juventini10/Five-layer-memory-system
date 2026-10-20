#!/bin/bash
# Skill 恢复脚本（目录级软链接模式 · 全端动态扫描版）
# 对应 Windows 版：restore-my-skills.ps1
#
# 适用平台：macOS / Linux
#
# 🔴 **2026-10-03 重写·病根是「手写端名」**（不是「少写了一行 hermes」）：
#   旧版硬编码 WORKBUDDY_DIR / TRAE_DIR / QWENWORK_DIR 三个落点，
#   加新端时**必须记得回来加一行**，忘了就静默漏链。
#   ⇒ 10-03 实锤：Hermes 端 capability.yaml 声明 skill_symlink: true，
#     而旧版 grep 'hermes' = 0 命中 ⇒ **声明为真、机制为假**（又一次「声明 ≠ 兑现」）。
#   ⇒ 且 10-03 执行报告第 2 项白纸黑字写「已重写为动态全端扫描」，
#     **报告改了、包里没改**（同一根因第三形态：文字先于产物）。
#
# ✅ **正解：端清单从 adapters/*/capability.yaml 机械派生**。
#    加一个端目录 ⇒ 落点 + 软链开关**自动生效**，无需回来改本脚本。
#    判据取自各端 capability 已有的字段（不新增声明面）：
#      · config_root     —— 端配置根（展开 ~）
#      · skill_symlink   —— true 才建链（false 的端走该端官方安装方式，⛔不硬链）
#      · skill_dir_name  —— 可选·该端 Skill 目录名，缺省 skills（LobsterAI 非默认）
#
# 用法：
#   ./restore-my-skills.sh                      # 权威源=脚本目录·全端扫描
#   ./restore-my-skills.sh --list               # 只打印将执行的动作（⛔ 不写盘）
#   ./restore-my-skills.sh -a <dir>             # 指定权威源
#   ./restore-my-skills.sh -p <安装包根>         # 显式指定含 adapters/ 的包根
#   ./restore-my-skills.sh -r <project_rules.md> # 同步 Skill 版本号表
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTHORITY_DIR="$SCRIPT_DIR"
PKG_ROOT="${BULUOTUO_PKG_ROOT:-}"  # 允许外部预设包根(作者端LIVE技能配置不在包根内时用)；装机端不设此env=向上探测行为不变
DRY=0
PROJECT_RULES=""

usage() {
    sed -n '2,27p' "$0" | sed 's/^# \{0,1\}//'
}

# ⛔ **手动解析参数**（不用 getopts）：`--list` 这类长选项会把 getopts 逼进
#    「未知参数」分支退掉（bash 实测踩过）。参数面小，手写更稳。
LIST=0
while [ $# -gt 0 ]; do
    case "$1" in
        --list)   LIST=1; shift ;;
        -a)       [ $# -ge 2 ] || { echo "❌ -a 需要值" >&2; exit 1; }
                  AUTHORITY_DIR="$2"; shift 2 ;;
        -p)       [ $# -ge 2 ] || { echo "❌ -p 需要值" >&2; exit 1; }
                  PKG_ROOT="$2"; shift 2 ;;
        -r)       [ $# -ge 2 ] || { echo "❌ -r 需要值" >&2; exit 1; }
                  PROJECT_RULES="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *)        echo "❌ 未知参数: $1" >&2; exit 1 ;;
    esac
done
[ "$LIST" = "1" ] && DRY=1

# ── 探测安装包根（找含 adapters/*/capability.yaml 的祖先）────────────
if [ -z "$PKG_ROOT" ]; then
    d="$SCRIPT_DIR"
    for _ in 1 2 3 4 5 6; do
        if ls "$d"/adapters/*/capability.yaml >/dev/null 2>&1; then
            PKG_ROOT="$d"; break
        fi
        [ "$d" = "/" ] && break
        d="$(dirname "$d")"
    done
fi

if [ -z "$PKG_ROOT" ]; then
    echo "❌ 未找到安装包根（向上 6 层内无 adapters/*/capability.yaml）" >&2
    echo "   请用 -p <安装包根> 显式指定。" >&2
    exit 2
fi

# ── 端清单：从 capability.yaml 派生（⛔ 本脚本不硬写任何端名）─────────
# 输出 TSV： 端ID \t 显示名 \t skills目录绝对路径 \t 是否软链
EP_TSV="$(PKG_ROOT="$PKG_ROOT" python3 - <<'PYEOF'
import glob, os, re, sys

root = os.environ["PKG_ROOT"]

def field(txt, key):
    """取字段（容忍缩进）。

    ⚠️ **踩坑记录（2026-10-03·当场自曝）**：首版正则写成 `^key:`（不容忍缩进）
    ⇒ capability.yaml 的 **capabilities 段键全是缩进的**（`  skill_symlink: true`）
    ⇒ 8 个端全被判 skill_symlink=false ⇒ 脚本「正确地一个链都不建」。
    ⛔ **假成功比假失败更坏**：输出全是「跳过」，看着像跑通了。
    ⇒ 是 `--list` 输出里「8 端全 false」这个不合理模式暴露的，不是推演出来的。
    ⇒ 判据沉淀：**闸门自己也要被抽查**，尤其是「全部跳过」这种输出。
    """
    m = re.search(r'^[ \t]*%s:[ \t]*(.+?)$' % re.escape(key), txt, re.M)
    if not m:
        return ""
    return m.group(1).split('#')[0].strip().strip('"').strip("'")

for cap in sorted(glob.glob(os.path.join(root, "adapters", "*", "capability.yaml"))):
    pid = os.path.basename(os.path.dirname(cap))
    txt = open(cap, encoding="utf-8", errors="replace").read()
    cr = field(txt, "config_root")
    if not cr:
        print("  # 跳过 %s：无 config_root" % pid, file=sys.stderr)
        continue
    cr = os.path.expanduser(cr)
    dirname_ = field(txt, "skill_dir_name") or "skills"
    sym = field(txt, "skill_symlink").lower() == "true"
    disp = field(txt, "display_name") or pid
    # 🔴 端专属 Skill 白名单（本端**独占**的 Skill，不链到别的端）
    # ⚠️ 2026-10-03 实测踩到：豆包专属的两个 Skill 被链到 Hermes ⇒
    #    Hermes 端 AI 加载到「署名 —— 你的 豆包 🍵」的规则 = 串端。
    #    ⛔ 不在本脚本里硬编码排除名单（加端必忘·又是第二本账）
    #    ⇒ 判据放 capability 的 `skill_exclusive`（端自己声明它独占什么）。
    excl = field(txt, "skill_exclusive")
    excl_list = [x.strip().strip("'\"") for x in excl.split(",") if x.strip()]
    print("\t".join([pid, disp, os.path.join(cr, dirname_),
                     "true" if sym else "false",
                     ",".join(excl_list)]))
PYEOF
)"

if [ -z "$EP_TSV" ]; then
    echo "❌ 未枚举到任何端：$PKG_ROOT/adapters/*/capability.yaml 全缺 config_root" >&2
    exit 2
fi

# ── 扫描权威源下所有 Skill（含 SKILL.md 的子目录）────────────────────
SKILLS=()
for d in "$AUTHORITY_DIR"/*/; do
    [ -d "$d" ] || continue
    b="$(basename "$d")"
    case "$b" in .*) continue ;; esac
    [ -f "$d/SKILL.md" ] || continue
    SKILLS+=("$b")
done

# 全端独占 Skill 并集（任一端声明独占 ⇒ ⛔ 不链到其它端）
ALL_EXCL="$(printf '%s\n' "$EP_TSV" | awk -F'\t' '{print $5}' | tr ',' '\n' | sed '/^$/d' | sort -u)"
N_EP="$(printf '%s\n' "$EP_TSV" | wc -l | tr -d ' ')"
N_LINK="$(printf '%s\n' "$EP_TSV" | awk -F'\t' '$4=="true"' | wc -l | tr -d ' ')"

echo "📦 Skill 恢复（目录级软链 · 全端动态扫描 · $(date '+%Y-%m-%d %H:%M')）"
echo "   权威源：${AUTHORITY_DIR}"
echo "   安装包：${PKG_ROOT}"
if [ "$DRY" = "1" ]; then echo "   模式：--list（⛔ 不写盘）"; fi
echo "   Skill：${#SKILLS[@]} 个 × 端：${N_EP} 个（其中软链端 ${N_LINK} 个）"
echo "   端清单由 capability.yaml 派生 ⛔ 本脚本不硬写端名"
echo ""

printf '%s\n' "$EP_TSV" | while IFS=$'\t' read -r pid disp skdir sym excl; do
    if [ "$sym" = "true" ]; then
        printf '   ✅ %-11s %-12s → %s\n' "${pid}" "${disp}" "${skdir}"
    else
        printf '   ⛔ %-11s %-12s → skill_symlink=false（走该端官方安装方式·本脚本不建链）\n' "${pid}" "${disp}"
    fi
done
echo ""

if [ "${#SKILLS[@]}" -eq 0 ]; then
    echo "❌ 权威源下无任何含 SKILL.md 的目录：${AUTHORITY_DIR}" >&2
    exit 2
fi

# ⛔ **合理性抽查（防「全部跳过」式假成功）**
# 若一个软链端都没有 ⇒ 说明 capability 解析失败 ⇒ ⛔ 直接退出，不假装跑完。
if [ "$N_LINK" = "0" ]; then
    echo "❌ 零个软链端 —— capability.yaml 的 skill_symlink 全未解析为 true。" >&2
    echo "   ⛔ 这是解析失败，不是「所有端都不支持软链」——⛔ 拒绝假装成功。" >&2
    exit 2
fi

# ── 沙箱路径链接自愈（/sessions/<id>/workspace/…）────────────────────
# 病根：某些端会把 skills 目录建在沙箱路径下 ⇒ 换机器即死链。
# 修法：检出后原地重指向权威源（不改目录位置）。
echo "🔍 沙箱路径软链自愈..."
healed=0
for d in $(printf '%s\n' "$EP_TSV" | awk -F'\t' '$4=="true"{print $3}'); do
    [ -d "$d" ] || continue
    for link in "$d"/*; do
        [ -L "$link" ] || continue
        tgt="$(readlink "$link" 2>/dev/null || true)"
        case "$tgt" in
            /sessions/*|*/sessions/*)
                sn="$(basename "$link")"
                src="$AUTHORITY_DIR/$sn"
                if [ "$DRY" = "1" ]; then
                    echo "   [list] 将修复沙箱链接：${sn}"
                elif [ -d "$src" ]; then
                    rm -f "$link" && ln -s "$src" "$link"
                    echo "   ✓ 已修复：${sn} → 权威源"; healed=$((healed+1))
                else
                    echo "   ⚠️ ${sn} 权威源不存在，跳过（不删死链）"
                fi
                ;;
        esac
    done
done
[ "$healed" = "0" ] && echo "   （无沙箱链接）"
echo ""

# ── 建链 ────────────────────────────────────────────────────────────
OK=0; SKIP=0; FAIL=0

link_one() {
    # $1=skill  $2=端ID  $3=端skills目录
    local skill="$1" pid="$2" skdir="$3"
    local src="$AUTHORITY_DIR/$skill"
    local dst="$skdir/$skill"

    if [ ! -d "$src" ]; then
        echo "   ❌ ${skill} → ${pid} 权威源不存在：${src}"; FAIL=$((FAIL+1)); return 1
    fi
    if [ -L "$dst" ]; then
        local cur; cur="$(readlink "$dst")"
        if [ "$cur" = "$src" ]; then
            return 0                       # 幂等·已正确·静默
        fi
        if [ "$DRY" = "1" ]; then
            echo "   [list] ${skill} → ${pid}：更新指向（现 ${cur}）"; OK=$((OK+1)); return 0
        fi
        rm -f "$dst"
    elif [ -e "$dst" ]; then
        # 🔒 端重复安装护栏：实体目录/文件 ⇒ 该端已单独装过 ⛔ 不覆盖（增量保护 C1-C7）
        echo "   ⚠️  ${skill} → ${pid} 端内已存在实体（非软链），⛔跳过不覆盖"
        echo "       若要改为软链：自行备份并删除 ${dst} 后重跑"
        SKIP=$((SKIP+1)); return 0
    fi
    if [ "$DRY" = "1" ]; then
        echo "   [list] ${skill} → ${pid}：建链"; OK=$((OK+1)); return 0
    fi
    if ln -s "$src" "$dst" 2>/dev/null; then
        if [ -L "$dst" ]; then
            OK=$((OK+1))
        else
            echo "   ❌ ${skill} → ${pid} 建链后非软链（疑降级为副本）"; FAIL=$((FAIL+1)); return 1
        fi
    else
        echo "   ❌ ${skill} → ${pid} 建链失败"; FAIL=$((FAIL+1)); return 1
    fi
}

while IFS=$'\t' read -r pid disp skdir sym excl; do
    [ "$sym" = "true" ] || continue        # ⛔ 非软链端一律不碰
    echo "── ${pid}（${disp}）→ ${skdir}"
    if [ "$DRY" = "1" ]; then
        :
    else
        # C15(2026-10-15)：自愈只碰"端配置根已存在"的端——配置根不在=该端未装，跳过⛔不mkdir占地
        #   （旧实现给未装端 mkdir skdir：一次自愈在 qodercn 机长出他端 skills 目录=step6 全端扫描同族病）
        if [ ! -d "$(dirname "$skdir")" ]; then
            echo "   ⏭️ ${pid} 配置根不存在（该端未装）——跳过不建链"
            continue
        fi
        mkdir -p "$skdir" 2>/dev/null || true
        if [ ! -d "$skdir" ]; then
            echo "   ❌ 无法创建 ${skdir}（路径权限？）"
            FAIL=$((FAIL+${#SKILLS[@]})); continue
        fi
    fi
    for s in "${SKILLS[@]}"; do
        # ⛔ 别端独占的 Skill ⛔ 不链过来（防串端：豆包专属链到 Hermes = 署名都错端）
        if [ -n "$ALL_EXCL" ] && printf '%s\n' "$ALL_EXCL" | grep -qx -- "$s" \
           && ! printf '%s\n' "$excl" | grep -qx -- "$s"; then
            continue
        fi
        link_one "$s" "$pid" "$skdir"
    done
    echo "   → ${pid} 完成"
done <<EOF
$EP_TSV
EOF

echo ""
echo "─────────────────────────────"
echo "软链：成功/已正确 ${OK} · 跳过(端内实体) ${SKIP} · 失败 ${FAIL}"
[ "$FAIL" -gt 0 ] && echo "⚠️ 有失败项，请查上方明细"

# ── project_rules.md Skill 版本号表同步（可选·文件不存在则跳过）──────
if [ -n "$PROJECT_RULES" ]; then
    echo ""
    if [ ! -f "$PROJECT_RULES" ]; then
        echo "⚠️ project_rules.md 不存在：${PROJECT_RULES}（跳过版本号同步）"
    elif [ "$DRY" = "1" ]; then
        echo "📝 [list] 将同步 Skill 版本号表 → ${PROJECT_RULES}"
    else
        echo "📝 同步 Skill 版本号表 → ${PROJECT_RULES}"
        kv=""
        for s in "${SKILLS[@]}"; do
            md="$AUTHORITY_DIR/$s/SKILL.md"
            v="$(grep -m1 '^version:' "$md" 2>/dev/null | sed 's/^version:[[:space:]]*//' | tr -d '"'"'" | tr -d '[:space:]')"
            kv+="$s:${v:-未知}"$'\n'
        done
        SKILL_VERSIONS="$kv" PROJECT_RULES_PATH="$PROJECT_RULES" \
        env -u PYTHONHOME -u PYTHONPATH python3 <<'PYEOF'
import os, re
p = os.environ.get("PROJECT_RULES_PATH", "")
raw = os.environ.get("SKILL_VERSIONS", "")
if not p or not os.path.exists(p):
    print("   ⚠️ project_rules.md 不存在，跳过"); raise SystemExit(0)
rows = []
for line in raw.strip().split("\n"):
    if ":" not in line:
        continue
    name, ver = line.rsplit(":", 1)
    rows.append("| %s | %s | `[记忆共享中心]/技能配置/%s/` |" % (name, ver or "未知", name))
content = open(p, encoding="utf-8").read()
pat = re.compile(r'(\| Skill \| 版本 \| 权威源路径 \|\n\|-------\|------\|-----------\|\n)(.*?)(\n版本不一致时运行)', re.S)
new = pat.sub(lambda m: m.group(1) + "\n".join(rows) + m.group(3), content, count=1)
if new == content:
    print("   ⚠️ 未匹配到版本号表，跳过")
else:
    open(p, "w", encoding="utf-8").write(new)
    print("   ✅ 版本号表已同步（%d 行）" % len(rows))
PYEOF
    fi
fi

echo ""
echo "💡 目录级软链：权威源任何文件更新后自动同步（端清单随包演进·本脚本不用改）"
[ "$DRY" = "1" ] && echo "   （本次 --list，⛔ 未写任何盘）"
[ "$FAIL" -gt 0 ] && exit 1
exit 0