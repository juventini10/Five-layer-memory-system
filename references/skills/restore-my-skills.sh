#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# Skill 恢复脚本（目录级软链接模式 · 跨平台通用版）
# 对应 Windows 版：restore-my-skills.ps1
#
# 适用平台：macOS / Linux
# 路径策略：默认从脚本所在目录动态推导权威源——放哪默认就是哪，
#           不再硬编码任何用户路径，任何用户拿去即可用。
#
# 用法：
#   ./restore-my-skills.sh
#       # 默认：权威源=本脚本目录；WB=~/.workbuddy/skills；Trae=~/.trae-cn/skills
#       # 同时自动更新 project_rules.md 的 Skill 版本号表
#   ./restore-my-skills.sh -a /path/to/技能配置 -w /path/to/.workbuddy/skills -t /path/to/.trae-cn/skills
# ─────────────────────────────────────────────────────────────

# ── 参数解析 ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

AUTHORITY_DIR="$SCRIPT_DIR"
WORKBUDDY_DIR="$HOME/.workbuddy/skills"
TRAE_DIR="$HOME/.trae-cn/skills"
PROJECT_RULES="$HOME/.trae/rules/project_rules.md"

while getopts ":a:w:t:r:" opt; do
  case $opt in
    a) AUTHORITY_DIR="$OPTARG" ;;
    w) WORKBUDDY_DIR="$OPTARG" ;;
    t) TRAE_DIR="$OPTARG" ;;
    r) PROJECT_RULES="$OPTARG" ;;
    \?) echo "❌ 未知参数: -$OPTARG" >&2; exit 1 ;;
    :) echo "❌ 参数 -$OPTARG 需要值" >&2; exit 1 ;;
  esac
done

# ── 自动扫描权威源目录下所有 Skill（含 SKILL.md 的子目录）──
SKILLS=()
for d in "$AUTHORITY_DIR"/*/; do
    skill_name=$(basename "$d")
    # 排除隐藏目录和非Skill目录
    if [ -f "$d/SKILL.md" ]; then
        SKILLS+=("$skill_name")
    fi
done

link_skill() {
    local skill_name="$1"
    local platform="$2"
    local target_dir="$3"

    local src="$AUTHORITY_DIR/$skill_name"
    local dst="$target_dir/$skill_name"

    if [ ! -d "$src" ]; then
        echo "❌ $skill_name → $platform 权威源不存在: $src"
        return 1
    fi

    if [ -L "$dst" ]; then
        local current
        current=$(readlink "$dst")
        if [ "$current" = "$src" ]; then
            echo "✅ $skill_name → $platform 已是目录级软链接"
            return 0
        fi
        rm "$dst"
    elif [ -d "$dst" ]; then
        rm -rf "$dst"
    fi

    ln -s "$src" "$dst"
    echo "✅ $skill_name → $platform 目录级软链接已创建"
    return 0
}

# ── 从 SKILL.md 的 YAML frontmatter 提取版本号 ──
get_skill_version() {
    local skill_md="$1"
    # 尝试提取 version 字段（兼容 "1.0.0" 和 1.0.0 两种格式）
    local ver=$(grep -m1 "^version:" "$skill_md" 2>/dev/null | sed 's/^version:[[:space:]]*//' | tr -d '"' | tr -d "'")
    if [ -z "$ver" ]; then
        ver="未知"
    fi
    echo "$ver"
}

# ── 从 SKILL.md 的 YAML frontmatter 提取 name 字段 ──
get_skill_display_name() {
    local skill_md="$1"
    local name=$(grep -m1 "^name:" "$skill_md" 2>/dev/null | sed 's/^name:[[:space:]]*//' | tr -d '"' | tr -d "'")
    if [ -z "$name" ]; then
        name=$(basename "$(dirname "$skill_md")")
    fi
    echo "$name"
}

# ── 自动更新 project_rules.md 的 Skill 版本号表 ──
update_project_rules() {
    if [ ! -f "$PROJECT_RULES" ]; then
        echo "⚠️ project_rules.md 不存在: $PROJECT_RULES，跳过版本号同步"
        return 0
    fi

    echo ""
    echo "📝 更新 project_rules.md 版本号表..."

    # 构建 skill:version 列表（用换行分隔，传入Python）
    local skill_versions=""
    for skill_name in "${SKILLS[@]}"; do
        local skill_md="$AUTHORITY_DIR/$skill_name/SKILL.md"
        local ver=$(get_skill_version "$skill_md")
        skill_versions+="${skill_name}:${ver}"$'\n'
    done

    # 用 Python 做正则替换（bash 处理多行替换太脆弱）
    # 清除 PYTHONHOME/PYTHONPATH 污染（TRAE SOLO CN 会注入）
    SKILL_VERSIONS="$skill_versions" PROJECT_RULES_PATH="$PROJECT_RULES" \
    env -u PYTHONHOME -u PYTHONPATH python3 << 'PYEOF'
import re
import os

rules_path = os.environ.get("PROJECT_RULES_PATH", "")
skill_versions_raw = os.environ.get("SKILL_VERSIONS", "")

if not rules_path or not os.path.exists(rules_path):
    print("   ⚠️ project_rules.md 不存在，跳过")
    exit(0)

with open(rules_path, "r", encoding="utf-8") as f:
    content = f.read()

# 构建新表格行
lines = []
for line in skill_versions_raw.strip().split("\n"):
    if ":" not in line:
        continue
    name, ver = line.rsplit(":", 1)
    if not ver or ver == "未知":
        ver_str = "未知"
    else:
        ver_str = f"v{ver}"
    lines.append(f"| {name} | {ver_str} | `[记忆共享中心]/技能配置/{name}/` |")

new_rows = "\n".join(lines)

# 匹配：从表头行到"版本不一致时运行"前的所有表格行
# 表头是 "| Skill | 版本 | 权威源路径 |" 和 "|-------|------|-----------|"
pattern = r'(\| Skill \| 版本 \| 权威源路径 \|\n\|-------\|------\|-----------\|\n)(.*?)(\n版本不一致时运行)'

replacement = r'\g<1>' + new_rows + r'\g<3>'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("   ⚠️ 未匹配到版本号表，跳过")
else:
    with open(rules_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("   ✅ 版本号表已自动更新")
PYEOF
}

echo "📦 Skill 恢复脚本（目录级软链接模式 · 自动扫描版）"
echo "   权威源: $AUTHORITY_DIR"
echo "   WB目录: $WORKBUDDY_DIR"
echo "   Trae目录: $TRAE_DIR"
echo "   发现Skill: ${#SKILLS[@]} 个"
echo ""

# 清理历史死链接（深度模式）
echo "🧹 清理历史死链接..."
for dead_link in "$WORKBUDDY_DIR/深度模式" "$TRAE_DIR/深度模式"; do
    if [ -L "$dead_link" ]; then
        target=$(readlink "$dead_link" 2>/dev/null || echo "")
        if [ ! -d "$target" ]; then
            rm "$dead_link"
            echo "   ✓ 已删除死链接：$dead_link (目标: $target)"
        fi
    fi
done

# 检测沙箱路径软链接（/sessions/{id}/workspace/...）
echo "🔍 检测沙箱路径软链接..."
for dir in "$WORKBUDDY_DIR" "$TRAE_DIR"; do
    while IFS= read -r link; do
        target=$(readlink "$link" 2>/dev/null || echo "")
        if [[ "$target" == /sessions/* ]]; then
            skill_name=$(basename "$link")
            rm "$link"
            src="$AUTHORITY_DIR/$skill_name"
            if [ -d "$src" ]; then
                ln -s "$src" "$link"
                echo "   ✓ 修复沙箱链接：$skill_name → 真实本地路径"
            else
                echo "   ⚠️ $skill_name 权威源不存在，跳过"
            fi
        fi
    done < <(find "$dir" -maxdepth 1 -type l 2>/dev/null)
done
echo ""

OK=0
FAIL=0

for skill_name in "${SKILLS[@]}"; do
    link_skill "$skill_name" "workbuddy" "$WORKBUDDY_DIR" && OK=$((OK+1)) || FAIL=$((FAIL+1))
    link_skill "$skill_name" "trae" "$TRAE_DIR" && OK=$((OK+1)) || FAIL=$((FAIL+1))
done

echo ""
echo "─────────────────────────────"
echo "✅ 软链接：$OK 个成功，$FAIL 个失败"
[ $FAIL -gt 0 ] && echo "⚠️ 失败：$FAIL 个"

# 自动更新 project_rules.md 版本号表
update_project_rules

echo ""
echo "💡 目录级软链接：权威源任何文件更新后自动同步"
