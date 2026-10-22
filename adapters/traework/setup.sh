#!/usr/bin/env bash
# ============================================================
# setup.sh — Trae Work adapter 聚合安装入口（幂等）
# 用途: install_scripts.py --platform traework 按 capability.yaml install_entry 委派到此
# 职责: ① rules 规则文件落盘(~/.trae-cn/user_rules·存在不覆盖·保本地私人版优先)
#       ①a 数字分身恒驻核组装落盘(有 K2 slices 才落·缺则诚实提示·⛔不假绿)
#       ①b 童灵专属 Skill 直落(adapters/traework/skills/* → ~/.trae-cn/skills·真目录·⛔不进共享技能配置)
#           + 全量 Skill 软链(<MC>/技能配置/* → ~/.trae-cn/skills·幂等)
#       ② patrol 脚本落盘 → [记忆共享中心]/脚本中心/Skill路由引擎/scripts/
#       ③ launchd plist 落位(占位符→真实MC) + bootstrap
#       ④ TSL 机械校验脚本落盘(adapters/traework/scripts/traework_tsl_verify.py → [记忆共享中心]/脚本中心/
#          ·童灵D3上岗时AI调用relay·构造权归脚本不归AI·对齐豆包 [5/7])
# 判据: Trae Work 纯 rules 端 + 无钩子端童灵 Skill 承载 + launchd patrol + TSL脚本 = 端特有部署链
#       (与 qodercn 对照 · traework 无 hooks = 安装器委派端特有部分·公共资产由安装器①/①a/①b 承担)
# 用法: bash setup.sh "<记忆共享中心绝对路径>"
# 来源: 布洛陀 v2.0 全平台安装包 adapters/traework/setup.sh
#       2026-09-23 根治委派缺口 / 2026-09-30 注入根订正(~/.trae→~/.trae-cn) + 补 patrol 落盘腿
#       + 占位符统一为 [记忆共享中心](与 install_scripts._fill 同源) + 规则集补齐名映射
#       2026-10-03 补 ①b：无钩子端童灵专属 Skill（doenglingz-guard/slice-nav）落盘+软链
#       ——此前 README 承诺「skills 软链」而脚本未实现＝文档与实盘脱钩（铁律-002 先计数再断言）
#       2026-10-05 补 ④：TSL 机械校验脚本落盘（童灵 D3 上岗 relay 用·构造权归脚本不归 AI）
#       2026-10-06 ①b 根治端串用：童灵专属 Skill 由 <MC>/技能配置 改直落 ~/.trae-cn/skills
#       （此前经共享权威源被 restore-my-skills.sh 全端软链分发到 Qoder 等异构端＝串端·隔离令）
#       2026-10-07 落盘形态声明：① rules 规则文件一律 `cp` **实体落盘**（⛔非软链）——
#       系统文件写入用户自己的 ~/.trae-cn/user_rules/，与记忆中心脱钩（端自己的系统文件 100% 适配）。
#       脚本行为未变（本就走 cp），本次仅补注释/文档对齐，防"共享软链"误读。
# ============================================================
set -uo pipefail

G='\033[0;32m'; Y='\033[1;33m'; R='\033[0;31m'; C='\033[0;36m'; N='\033[0m'
MC=""
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
RULE_SRC="$SRC_DIR/rules"
# ⚠️ 2026-09-30 机制纠正：Trae Work(TRAE SOLO CN) 与 TraeCode(Trae CN) 的 product.json
#    dataFolderName 同为 `.trae-cn` ⇒ 全局规则目录物理共用，目录级隔离不存在。
#    本端规则层 = ~/.trae-cn/user_rules/（每回合注入的实读目录）；
#    ~/.trae/user_rules/ 是 peer 目录(ICUBE_PEER_USER_DATA_DIRS)·本端不读·写了不生效。
#    （旧值 "$HOME/.trae/user_rules" 系 2026-09-16「分目录隔离」错误前提产物·2026-09-30 订正）
RULE_DST="$HOME/.trae-cn/user_rules"
PLIST_TMPL="$SRC_DIR/scripts/com.buluotuo.traework.patrol.plist"
PLIST="$HOME/Library/LaunchAgents/com.buluotuo.traework.patrol.plist"
PATROL_SRC="$SRC_DIR/scripts/route_traework_patrol.sh"
# 恒驻核头模板（frontmatter + 定位块）——⛔ 不放 rules/（rules 目录整目录按规则落盘，会被误装成规则）
CORE_HEADER="$SRC_DIR/templates/doenglingz-core-header.md"
# 占位符单一形态：方括号 [记忆共享中心]（与 install_scripts.PLACEHOLDER 同源·条文3 单一变换）
# ⚠️ 方括号在 sed/grep 的 BRE 里是字符类 → 匹配/替换必须用字面量形态（grep -F / sed 转义）
MCP='[记忆共享中心]'
MCP_RE='\[记忆共享中心\]'
DRY="${DRY:-}"
# 参数解析：`--dry-run`/`-n` 选项 + 首个非选项=MC
# ⚠️ install_scripts.py 委派时按 `<MC> [--dry-run]` 传参（2026-10-21 订正顺序）——
#    本脚本按首个非选项取 MC（见下方参数解析），故顺序不敏感；旧注释的 `[--dry-run] <MC>` 已过时。
for _arg in "$@"; do
    case "$_arg" in
        --dry-run|-n) DRY=1 ;;
        -*) ;;                                  # 未知选项忽略
        *) [ -z "$MC" ] && MC="$_arg" ;;
    esac
done
# ⚠️ 依赖 $MC 的派生路径必须在参数解析之后赋值——否则 dry-run 下 MC 尚空 ⇒ 路径塌成 "/脚本中心/..."
# 2026-10-21：脚本面归拢后 patrol 实体在 脚本中心/（顶层 开发工具/ 已不再是脚本落点）
PATROL_DST_DIR="$MC/脚本中心/Skill路由引擎/scripts"
# TSL 机械校验脚本（童灵 D3 上岗时 AI 调用 relay·构造权归脚本不归 AI）
TSL_SRC="$SRC_DIR/scripts/traework_tsl_verify.py"
TSL_DST="$MC/脚本中心/traework_tsl_verify.py"

echo -e "${C}=== Trae Work adapter 安装（rules 落盘 + 恒驻核 + Skill + TSL脚本 + patrol + launchd） ===${N}"
[ -n "$MC" ] || { echo -e "${R}❌ 未给记忆共享中心路径（用法: bash setup.sh \"<MC>\"）${N}"; exit 2; }

# 占位符替换：文本件内 [记忆共享中心] → 真实 MC 绝对路径（与 install_scripts._fill 同一变换）
fill_ph() {
    local f="$1"
    [ -f "$f" ] || return 0
    grep -qF "$MCP" "$f" 2>/dev/null || return 0
    sed "s@${MCP_RE}@${MC}@g" "$f" > "$f.tmp.$$" && mv "$f.tmp.$$" "$f"
}

# 目录级软链（幂等·⛔不覆盖实体目录——用户自建实体优先，防误删用户内容）
link_skill_dir() {
    local src="$1" dst="$2"
    if [ -L "$dst" ]; then
        if [ "$(readlink "$dst")" = "$src" ]; then
            return 0
        fi
        rm "$dst"
    elif [ -d "$dst" ]; then
        echo -e "  ${Y}SKIP（实体目录已存在·不覆盖）: $(basename "$dst")${N}"
        return 1
    fi
    ln -s "$src" "$dst"
    return 0
}

# ─── ① rules 规则文件落盘（存在不覆盖·本地私人版优先）
#     适配承载名 → 本端标准注入名映射（承载名≠注入名会让消费端认不出·qodercn 同因靠软链生效）
#     约定见 adapters/traework/README.md §名映射表；未列名者同名直落
[ -d "$RULE_SRC" ] || { echo -e "${R}❌ 找不到 rules: $RULE_SRC${N}"; exit 2; }
mkdir -p "$RULE_DST"
echo -e "${C}[1/6] rules 规则文件落盘 → $RULE_DST${N}"
for f in "$RULE_SRC"/*.md; do
    src_name="$(basename "$f")"
    dst_name="$src_name"
    case "$src_name" in
        core-identity.md)       dst_name="IDENTITY.md" ;;
        core-memory.md)         dst_name="MEMORY.md" ;;
        core-soul.md)           dst_name="SOUL.md" ;;
        core-user.md)           dst_name="USER.md" ;;
        # 执行准则：适配承载名 execution-guidelines.md（全 adapter 统一）→ 本端注入名 trae_solo_rules.md
        # （条文 12：承载名≠注入名；本端规则层实读名为 trae_solo_rules.md）
        execution-guidelines.md) dst_name="trae_solo_rules.md" ;;
    esac
    dst="$RULE_DST/$dst_name"
    if [ -f "$dst" ]; then
        echo -e "  ${Y}SKIP（已存在·保本地/私人版）: $src_name → $dst_name${N}"
    elif [ -n "$DRY" ]; then
        echo -e "  ${C}[dry-run] 将落盘: $src_name → $dst_name${N}"
    else
        cp "$f" "$dst"
        fill_ph "$dst"
        echo -e "  ${G}✅ 落盘: $src_name → $dst_name${N}"
    fi
done

# ─── ①a 数字分身恒驻核（doenglingz-core.md）组装落盘
#     单一真源 = K2 生成器产物（<MC>/数字分身/K2切片蒸馏/slices/core_slice.md + L6_反向约束.md）
#     ⛔ 包内不携带静态分身核——童灵人格由使用者自己的规格书生成（per-user·反漂移条款）
#     ⛔ 缺 slices 时诚实提示并跳过（不假绿·不落空壳核）
# ⚠️ 2026-10-05 路径口径收敛（审计 P1-1 方案C）：切片恒定落 <数字分身>/K2切片蒸馏/slices/
#    （与生成器 OUT_DEFAULT / 安装器 _detect_existing_twin / 各端 hook / 端 Skill / 入门指南 同源·单一真源）。
#    旧值 k2-slice-generator/slices 是生成器旧输出口径的残留——生成器已改落 K2切片蒸馏/slices，
#    旧路径在部署态会读空（真身 K2切片蒸馏/ 与部署态 k2-slice-generator/ 同构）。
SLICES="$MC/数字分身/K2切片蒸馏/slices"
DT_CORE="$RULE_DST/doenglingz-core.md"
echo -e "${C}[2/6] 数字分身恒驻核 → $DT_CORE${N}"
if [ -f "$DT_CORE" ]; then
    echo -e "  ${Y}SKIP（已存在·保本地/私人版）: doenglingz-core.md${N}"
elif [ -f "$SLICES/core_slice.md" ] && [ -f "$SLICES/L6_反向约束.md" ]; then
    if [ -n "$DRY" ]; then
        echo -e "  ${C}[dry-run] 将从 K2 slices 组装 doenglingz-core.md（头模板 + core_slice + L6）${N}"
    elif [ ! -f "$CORE_HEADER" ]; then
        echo -e "  ${R}❌ 缺恒驻核头模板: ${CORE_HEADER}（打包缺陷·⛔不落无头核）${N}"
    else
        # 头模板 = frontmatter(alwaysApply:true·Trae 系注入前提) + 定位块(实体边界/SSOT/域切片指针)
        # ⚠️ 2026-10-03 修：旧版 printf 组装无 frontmatter ⇒ 文件不被注入 ⇒ 恒驻核形同虚设（空壳核）
        #    且缺「实体边界」「🧭 域切片按需加载」指针 = guard 8要素之 #8 直接 RED
        SLICE_HASH="（见 slices/manifest.json）"
        if [ -f "$SLICES/manifest.json" ]; then
            SLICE_HASH="$(env -u PYTHONHOME -u PYTHONPATH python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8')).get('src_hash',''))" "$SLICES/manifest.json" 2>/dev/null)"
            [ -n "$SLICE_HASH" ] || SLICE_HASH="（manifest 读取失败）"
        fi
        {
            cat "$CORE_HEADER"
            cat "$SLICES/core_slice.md"
            printf '\n\n'
            cat "$SLICES/L6_反向约束.md"
            printf '\n'
        } > "$DT_CORE.tmp.$$"
        # 注入切片来源 hash（人工核验锚·机械校验以 doenglingz-guard 查3 为准）
        sed "s@__SLICE_HASH__@${SLICE_HASH}@g" "$DT_CORE.tmp.$$" > "$DT_CORE"
        rm -f "$DT_CORE.tmp.$$"
        fill_ph "$DT_CORE"
        echo -e "  ${G}✅ 组装落盘（头模板 + core_slice + L6·hash=${SLICE_HASH}）${N}"
    fi
else
    echo -e "  ${Y}⚠️ 未生成 K2 切片·跳过数字分身恒驻核（⛔不落空壳）${N}"
    echo -e "  ${Y}   生成后再跑一次本脚本即可（幂等）：${N}"
    echo -e "  ${C}   python3 \"$MC/数字分身/k2-slice-generator/k2_slice_generator.py\"  # 产物 → $SLICES/${N}"
fi

# ─── ①b 童灵专属 Skill 落盘（端专属·⛔不进共享技能配置·防他端串用）
#     ⚠️ 2026-10-06 根治端串用：童灵专属 Skill（doenglingz-guard/doenglingz-slice-nav）此前落
#        <MC>/技能配置/，被 restore-my-skills.sh 的「全端软链」机制分发到 Qoder 等异构端
#        （实测 ~/.qoder-cn/skills/ 出现本端专属 skill＝串端）。改：直落 Trae Work 原生 skill
#        消费目录 ~/.trae-cn/skills/（真目录），⛔不进共享权威源（技能配置）⇒ 全端软链机制
#        自然不碰＝他端不可见。
#     Trae Work 端 Skill 消费面 = ~/.trae-cn/skills/（无钩子端·每回合扫描此目录）
TRAE_SKILLS_SRC="$SRC_DIR/skills"
SKILLS_DST="$HOME/.trae-cn/skills"
echo -e "${C}[3/6] 童灵专属 Skill 直落 ${SKILLS_DST}（⛔不进共享技能配置·防他端串用）${N}"
if [ -d "$TRAE_SKILLS_SRC" ]; then
    mkdir -p "$SKILLS_DST"
    for skill in "$TRAE_SKILLS_SRC"/*; do
        [ -d "$skill" ] || continue
        src_name="$(basename "$skill")"
        # 名映射契约（条文 12·承载名 → 本端落盘名）——与 README §名映射表 / §目录结构、
        # capability.yaml 的 carrier 路径、本机实体名三方同源（单一真源）
        # ⚠️ 2026-10-07 修：此前按 basename 直落（doenglingz-guard/doenglingz-slice-nav），
        #    与 capability.yaml 声明的 carrier 路径 `~/.trae-cn/skills/布洛陀-童灵守护` 不符
        #    ＝声明与实盘脱钩（铁律-002 先计数再断言）。补齐映射，使脚本行为对齐既有声明。
        case "$src_name" in
            doenglingz-guard)     skill_name="布洛陀-童灵守护" ;;
            doenglingz-slice-nav) skill_name="布洛陀-童灵切片导航" ;;
            *)                    skill_name="$src_name" ;;
        esac
        dst="$SKILLS_DST/$skill_name"
        if [ -L "$dst" ]; then
            # 旧版残留软链（曾指向共享技能配置）⇒ 换为实体（实体不再经共享区＝根治串用）
            if [ -n "$DRY" ]; then
                echo -e "  ${C}[dry-run] 将替换软链为实体: $skill_name${N}"
            else
                rm "$dst"; cp -r "$skill" "$dst"
                find "$dst" -type f -print0 | while IFS= read -r -d '' _f; do fill_ph "$_f"; done
                echo -e "  ${G}✅ 替换软链为实体: $skill_name${N}"
            fi
        elif [ -d "$dst" ]; then
            echo -e "  ${Y}SKIP（实体已存在·保本地/私人版）: $skill_name${N}"
        elif [ -n "$DRY" ]; then
            echo -e "  ${C}[dry-run] 将落盘童灵 Skill: $skill_name → $dst${N}"
        else
            cp -r "$skill" "$dst"
            # 占位符替换（仅文本件命中·与 install_scripts._fill 同一变换）
            find "$dst" -type f -print0 | while IFS= read -r -d '' _f; do fill_ph "$_f"; done
            echo -e "  ${G}✅ 落盘童灵 Skill: $skill_name${N}"
        fi
    done
else
    echo -e "  ${Y}⚠️ 未找到适配器童灵 Skill: $TRAE_SKILLS_SRC${N}"
fi
# 全量 Skill 软链（<MC>/技能配置/* → ~/.trae-cn/skills·幂等）
# ⚠️ 童灵专属 skill 已直落 SKILLS_DST（不在 <MC>/技能配置）⇒ 本循环自然不碰＝防串用第二道
mkdir -p "$SKILLS_DST"
SK=0; TOT=0
for skill in "$MC/技能配置"/*; do
    [ -d "$skill" ] || continue
    TOT=$((TOT+1))
    if link_skill_dir "$skill" "$SKILLS_DST/$(basename "$skill")"; then
        SK=$((SK+1))
    fi
done
echo -e "  ${C}软链结果: $SK/$TOT${N}"

# ─── ④ TSL 机械校验脚本落盘（童灵 D3 上岗时 AI 调用 relay·构造权归脚本不归 AI）
#     对齐豆包 [5/7]：无钩子端靠端专属脚本机械产树，AI 只许 relay stdout（防 AI 自绘清单）
#     幂等：已存在时按 __version__ 比对，源新于目标才更新（避免重复覆盖）
#     注：脚本无 [记忆共享中心] 占位符——运行期经 os.path.expanduser("~")/BULUOTU_MC 自解析，无需 fill_ph
echo -e "${C}[4/6] TSL 机械校验脚本落盘 → $TSL_DST${N}"
if [ ! -f "$TSL_SRC" ]; then
    echo -e "${R}❌ 找不到 TSL 脚本: ${TSL_SRC}（打包缺陷·⛔不落空）${N}"
    exit 2
elif [ -n "$DRY" ]; then
    echo -e "  ${C}[dry-run] 将落盘: traework_tsl_verify.py → $MC/脚本中心/${N}"
else
    mkdir -p "$MC/脚本中心"
    if [ -f "$TSL_DST" ]; then
        src_ver="$(grep -m1 '__version__' "$TSL_SRC" | sed "s/.*= *['\"]//;s/['\"].*//")"
        dst_ver="$(grep -m1 '__version__' "$TSL_DST" | sed "s/.*= *['\"]//;s/['\"].*//")"
        if [ "$src_ver" != "$dst_ver" ]; then
            cp "$TSL_SRC" "$TSL_DST"; chmod +x "$TSL_DST"
            echo -e "  ${G}✅ TSL 脚本已更新（${dst_ver}→${src_ver}）${N}"
        else
            echo -e "  ${Y}[=] TSL 脚本已为最新（${src_ver}）${N}"
        fi
    else
        cp "$TSL_SRC" "$TSL_DST"; chmod +x "$TSL_DST"
        echo -e "  ${G}✅ TSL 脚本已落盘（$(grep -m1 '__version__' "$TSL_SRC" | sed "s/.*= *['\"]//;s/['\"].*//")）${N}"
    fi
fi

# ─── ② patrol 脚本落盘（plist 的 ProgramArguments 指向此路径·缺则 launchd 跑空=守卫全死）
[ -f "$PATROL_SRC" ] || { echo -e "${R}❌ 找不到 patrol 脚本: $PATROL_SRC${N}"; exit 2; }
echo -e "${C}[5/6] patrol 脚本落盘 → $PATROL_DST_DIR/${N}"
if [ -n "$DRY" ]; then
    echo -e "  ${C}[dry-run] 将落盘: route_traework_patrol.sh${N}"
else
    mkdir -p "$PATROL_DST_DIR"
    cp "$PATROL_SRC" "$PATROL_DST_DIR/route_traework_patrol.sh"
    chmod +x "$PATROL_DST_DIR/route_traework_patrol.sh"
    fill_ph "$PATROL_DST_DIR/route_traework_patrol.sh"
    echo -e "  ${G}✅ 落盘: route_traework_patrol.sh（占位符已替换为真实MC）${N}"
fi

# ─── ③ launchd plist 落位（幂等：仅在缺失/含模板占位符时从模板重建；已真实安装则跳过）
[ -f "$PLIST_TMPL" ] || { echo -e "${R}❌ 找不到 plist 模板: $PLIST_TMPL${N}"; exit 2; }
echo -e "${C}[6/6] launchd plist 落位 → $PLIST${N}"
if [ -n "$DRY" ]; then
    echo -e "  ${C}[dry-run] 将落位 plist（占位符→真实MC）${N}"
elif [ -f "$PLIST" ] && ! grep -qF "$MCP" "$PLIST"; then
    # 已存在且占位符已替换（真实安装档）→ 跳过，防覆盖/防重复 sed 叠写
    echo -e "  ${Y}SKIP（已安装·占位符已替换）: $PLIST${N}"
else
    # 不存在 / 残留模板档（含占位符）→ 从模板重建并替换，幂等收敛
    mkdir -p "$(dirname "$PLIST")"
    sed "s@${MCP_RE}@${MC}@g" "$PLIST_TMPL" > "$PLIST"
    echo -e "  ${G}✅ 落位(模板→真实MC)${N}"
fi

# ─── ④ bootstrap（尽力自动·失败打手动指令·不假绿） ───
# 退出码约定（供 install_scripts.py 消费·条文16「降级不阻塞」）：
#   0 = 端特有链全成功（含 launchd 已注册）
#   3 = 文件已全量落盘(①rules/①a分身核/②patrol脚本/③plist)·仅「launchd 调度注册」待手动收尾
#       ——⛔非失败·⛔不阻塞安装器继续装公共资产(脚本中心/数字分身套件/规则层)
#   2 = 真失败（缺 MC 路径 / 缺源件·文件未落盘）
echo -e "${C}[+] launchd bootstrap（自动·失败则给手动指令）${N}"
if [ -n "$DRY" ]; then
    echo -e "  ${C}[dry-run] 跳过 bootstrap${N}"
    exit 0
fi
if [ -f "$SRC_DIR/scripts/install_launchd.sh" ]; then
    bash "$SRC_DIR/scripts/install_launchd.sh"
    rc=$?
    if [ $rc -eq 0 ]; then
        echo -e "${G}✅ launchd patrol 已注册${N}"
        exit 0
    else
        echo -e "${R}⚠️ launchd 需手动注册（见上方命令）·未假绿${N}"
        echo -e "${Y}   （规则/分身核/patrol 脚本已全量落盘·仅调度注册待手动——本脚本退出码 3）${N}"
        exit 3
    fi
else
    # 包内缺 install_launchd.sh（打包缺陷）——文件仍已落盘，按「待手动收尾」处理并给出等价命令
    echo -e "${Y}⚠️ 缺 install_launchd.sh（launchd 注册阶段不可用·打包缺陷）${N}"
    echo -e "${C}    手动等价命令：launchctl bootstrap gui/\$(id -u) $PLIST${N}"
    exit 3
fi