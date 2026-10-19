#!/usr/bin/env bash
#
# growth_box_check.sh — 成长箱晋升提醒 + 抗体复发扫描（只读巡检 learnings/ + 命中留痕仅追加记录文件）
# Version: 2.1 (2026-09-19) — 离源台账去重锚根治（工单 D19②·皮叔令「按推荐继续」）：
#                           ① 退役台账登记/去重的锚由**标题**改为**抗体命令 sha1 前 12**。
#                              实证缺陷：标题可匿名（E9.2 那条链上 9 条全署「未命名抗体」）→ 第二条不同命令
#                              被第一条的匿名标题判「已登记」而丢弃 = 台账丢条 = 不可点名 = 死数据。
#                           ② 标题回退只对**无锚存量行**生效（防历史条目重复膨胀），带锚新行只认锚——
#                              夹具 T2 抓到第一版实现漏了这层（回退无差别生效=换锚等于没换）。
#                           ③ RETIRE_LOG 支持 IMMUNE_RETIRE_LOG env 重定向（夹具隔离·⛔不污染真台账）。
#                           ④ 永久夹具 tests/test_retire_anchor.sh：T1 双跑去重 / T2 匿名同标题不同命令各留一行
#                              / T3 变异自证（退化为标题锚必复现误并）/ T4 存量无锚行回退命中。
# Version: 2.0 (2026-09-18) — 反哺1/4/5 + 执行器单源化 第一性根治（童灵·皮叔令「第一性原理全部根治解决」）：
#                           ① **反哺1·恒假形态检测**：接入 gate C7（取数格式与被检输出不同源→永不命中）——
#                              与 C4 对称：C4 防"恒命中"(假红源)、C7 防"恒不命中"(坑报不出来)。
#                              实证：setup.ps1 BOM 抗体 `od -An -tx1 | grep -q "ef bb bf"` 53 次假红。
#                           ② **反哺4·真长坑复查截止日**：登记时落 "复查截止日=登记日+14d"；巡检时逾期
#                              自动升级为强制处置候选（防"待终审"变永久黑洞——实测 11 条挂 13 天零推进）。
#                           ④ **执行器收进单一真相源**（v2.0）：三端共用 gate 的执行语义（stdin=DEVNULL+单条超时）——
#                              实测 2 条抗体因缺 stdin 重定向永久挂死。
#                           ③ **反哺5·抗体健康度三态分层**：报告分 🔴真红/🌫疑似噪声/⏳未复验 呈现，
#                              并在噪声>真红时预警（防真警报被淹没——实测 228:36 = 6.3:1）。
# Version: 1.8 (2026-09-15) — 抗体门禁单源化 + 写入端门禁巡检显形（T0 根治·童灵执行）：
#                           ① 抗体的**提取与判定**全部委托 antibody_gate.py（单一真相源）——v1.7 的宽松
#                              grep '复发检测条件[^`]*`' 把"提及字段名的规则叙述"当抗体扫（实测 60 条里
#                              8 条是假抗体=22%），且校验规则在写入端/巡检端各写一套=双实现必漂移
#                              （守卫编写规范 §一·真相所有权：单源）。
#                           ② 新增「抗体写入端门禁·巡检端显形」段：gate 六项判定（C1空/C2多行/C3语法/
#                              C4恒真/C5相对路径/C6重复）非空即显形；C4 沿用退役台账，其余进门禁告警区。
#                           ③ 报告带行号（L2718）——定位不再靠人工搜。
#                           依据：守卫编写规范 §3.3 抗体规则表 + §3.3.1 免疫进化闭环 + 铁律-021②（终检须脚本物理拦截）。
# Version: 1.7 (2026-09-06) — 「抗体免疫温检」升级为「免疫调节自决」闭环（愿景③自主进化·源头减欠账）：
#                           v1.6 温检只"显形给人看"，v1.7 新增③「免疫调节自决」——据行为级证据自动生成退役台账，
#                           分三类：恒真形态=强制退役(机械可判·假命中源)；账本残留(扫描learnings Status/占位符)=退役候选(检测对象错位)；
#                           真长坑疑似=保留待终审(⛔勿删)。退役登记入 成长箱/免疫退役记录.md（离源台账·⛔不改真源。）
#                           —— 配套守卫编写规范 §3.3.1 免疫进化闭环：检测对象=真实复发非账本残留，终结"靠人记得清欠账"。
# Version: 1.6 (2026-09-06) — 新增「抗体免疫温检」段（根治·防"造抗体时的错"）：①静态恒真形态拦截
#                             （detect 命令若恒真 e.g. `&& exit 0 || exit 0`，bash -c 恒 exit0=假命中，直接揪出）；
#                             ②免疫历史留痕数据源（免疫也写 免疫抗体历史.md 且每cmd去重一次——积累后行为级判定，
#                             愿景③自主从运行数据进化）；③高频命中(≥3)从不免疫→显形"疑似坏/失聪天线"供复核。
#                             背景：2026-09-06 反哺日志证据链抗体写成恒真 `&& exit 0 || exit 0`，多端巡检每天假命中刷屏，
#                             免疫复发记录被污染——机制把不可靠起草者的命令当受信任输入执行=单点信任漏洞，主矛盾。
# Version: 1.5 (2026-09-02) — 抗体扫描双源化：从仅反哺日志扩展为反哺日志 + learnings/晋升条目，
#                             grep -H 显示来源文件名，命中留痕增加来源列。晋升条目的🛡复发检测条件
#                             现在可被自动扫描（C2-1/PAT-046/PAT-047 晋升时配抗体）。
# Version: 1.4.1 (2026-09-01) — 修复 file_total 零匹配双行显示bug...
# Version: 1.3 (2026-07-30) — 修正跳过正则：纳入 ERRORS.md/LEARNINGS.md（流程A通用错误写入这两文件，原排除=巡检漏报待晋升）；
#                             Count 解析兼容平文格式 `- Count: N` / `- 累计次数: N`（ERRORS.md 实际格式，原仅匹配加粗 **Count**:）。
#                             来源：Loop评估 2026-07-30 候选#2
#
# 检查逻辑：
#   1. 扫描 learnings/ 下各错误文件，按单条错误统计 Count/累计次数
#   2. 晋升阈值 = 3次（与 growth-box SKILL.md 一致）
#   3. 单条 Count ≥ 3 且 Status: active/pending → 报告"待晋升"
#   4. 抗体复发扫描（v1.4）：解析 规范反哺日志.md 的「🛡 复发检测条件」，detect exit 0=命中 → 报告+留痕
#
# 用法：
#   growth_box_check.sh            # 完整报告
#   growth_box_check.sh --summary  # 仅摘要
#   growth_box_check.sh --pending  # 仅待晋升列表
#
set -eo pipefail

LEARNINGS_DIR="[记忆共享中心]/成长箱/learnings"
THRESHOLD=3
export THRESHOLD

# ── [v1.8] 抗体段单独巡检开关：GB_ANTIBODY_ONLY=1 时跳过前两段 ──────────────
#   用途：① 只需抗体判定时不必扫全库（Stop 守卫/其他端复用·性能）
#         ② 抗体侧改动可隔离验证（铁律-021④ 改动收尾必须可验）
if [[ "${GB_ANTIBODY_ONLY:-0}" != "1" ]]; then

# ── 1. 错误晋升检查 ──────────────────────────────────────────────
echo "🌱 成长箱晋升巡检"
echo

pending=()
for f in "$LEARNINGS_DIR"/*.md; do
  name=$(basename "$f")
  # skip 索引/需求/书籍文档——ERRORS.md/LEARNINGS.md 纳入扫描（流程A步骤A1明确通用错误写入这两文件，
  # 原排除=巡检漏报待晋升。LEARNINGS.md 当前条目无 Count 字段不会误报，纳入=未来带计数条目可被扫到）
  # 来源：Loop评估 2026-07-30 候选#2
  [[ "$name" =~ ^(INDEX|FEATURE_REQUESTS|book)_?\.md$ ]] && continue

  # grep -c 无匹配时 exit 1 且输出 "0"，`|| echo 0` 会叠加成 "0\n0" 双行 → 改用命令替换内兜底（2026-09-01 批次2 P2-7）
  file_total=$(grep -c "^## \[" "$f" 2>/dev/null || true)
  [[ -z "$file_total" ]] && file_total=0

  # 用 perl 按条目遍历，提取 Count/累计次数 + Status
  perl -ne '
    # 审查ND-2重写：$has_status/$denom 移入条目级状态（BEGIN+边界重置），冲刷逻辑边界+END 双份内联（perl -ne 循环内避免 sub 重定义）
    BEGIN { $title=""; $count=""; $status=""; $denom=""; $has_status=0; $first=1 }
    if (/^## \[/) {
      if (!$first && $count ne "") {
        if ($count >= $ENV{THRESHOLD} && $status eq "active") { print "$prev_title\n"; }
        elsif ($count >= $ENV{THRESHOLD} && $has_status == 0) { print "⚠️无Status行(假阴性候选·审查P3-2): $prev_title\n"; }
        if ($denom ne "" && $denom != 3) { print "⚠️分母漂移(N/${denom}≠N/3·审查P3-2): $prev_title\n"; }
      }
      $title=$_; chomp $title;
      $count=""; $status=""; $denom=""; $has_status=0;
      $first=0;
      $prev_title=$title;
    }
    if (/\*\*Count\*\*:/ || /\*\*累计次数\*\*:/ || /^[-*] ?Count:/ || /^[-*] ?累计次数:/) {
      if (m{([0-9]+)/([0-9]+)}) { $count=$1; $denom=$2 }
      if (/(?:Count|累计次数):[^0-9]*([0-9]+)/ && ($count eq "" || $1 > $count)) { $count=$1 }
    }
    if (/\*\*Status\*\*:/) { $has_status = 1;
      $status = /active|pending/ ? "active" : "done";
    }
    END {
      if (!$first && $count ne "") {
        if ($count >= $ENV{THRESHOLD} && $status eq "active") { print "$prev_title\n"; }
        elsif ($count >= $ENV{THRESHOLD} && $has_status == 0) { print "⚠️无Status行(假阴性候选·审查P3-2): $prev_title\n"; }
        if ($denom ne "" && $denom != 3) { print "⚠️分母漂移(N/${denom}≠N/3·审查P3-2): $prev_title\n"; }
      }
    }
  ' "$f" > /tmp/gb_candidates.txt

  cand_count=$(wc -l < /tmp/gb_candidates.txt | tr -d ' ')
  if [[ "$cand_count" -gt 0 ]]; then
    echo "  🔴 $name: $cand_count 条达到晋升阈值 (≥$THRESHOLD)"
    while IFS= read -r line; do
      [[ -n "$line" ]] && echo "      - $line"
    done < /tmp/gb_candidates.txt
    pending+=("$name")
  else
    echo "  ✅ $name: $file_total 条 (无≥${THRESHOLD}次的晋升候选)"
  fi
done

# ── 1b. PAT 聚合口径（D37·2026-09-27 童灵夜跑补）────────────────────
# 上面第 1 节数的是「单条记录内的 count 字段」，本节数的是「INDEX 里引用过该 PAT 的独立记录数」，
# 两套口径同问题两答案（2026-09-26 流程B 对账实锤：记录内口径报"无候选"，聚合口径有 4 条跨阈值）。
# 处置：两数同屏显形，⛔只报不判——晋升判定归第 3 步人工（B4 是你的按钮）。
echo
echo "🧮 PAT 聚合口径（与上节不同源·两数都摆出来）"
_idx="[记忆共享中心]/成长箱/learnings/INDEX.md"
if [[ -f "$_idx" ]]; then
  python3 - "$_idx" <<'PYEOF'
import io, re, sys
cross = []
for l in io.open(sys.argv[1], encoding='utf-8'):
    m = re.match(r'\| (PAT-\d{3}) \| ([^|]*)\| (\d+)\+ \| ([^|]*)\| ([^|]*)\|', l)
    if not m or int(m.group(3)) < 3:
        continue
    st = m.group(5).strip()
    # 只留还能动作的：已晋升/已判保持/已合并混进来会把报告变成二十行噪声（首跑实测 22 行）
    if ('pending' not in st.lower()) or ('已判保持' in st) or ('已晋升' in st) or ('merged' in st):
        continue
    cross.append((m.group(1), m.group(2).strip()[:26], m.group(3), st[:22]))
if not cross:
    print("  ✅ 聚合口径亦无跨阈值待判项")
for pid, name, n, st in cross:
    print("  🔴 %s 聚合 %s+ ｜%s ｜状态:%s" % (pid, n, name, st))
print("  ⚠️口径边界：聚合数含「同族对照」式顺带提及（D39 在案）→ 跨阈值须再核严格主归属数才上升")
PYEOF
else
  echo "  ⚪ INDEX.md 不在（[记忆共享中心]/成长箱/learnings/）→ 本节不判，⛔不静默当通过"
fi

# ── 2. 蒸馏建议 ──────────────────────────────────────────────────
echo
echo "🧪 蒸馏建议"
total_pending=${#pending[@]}
if [[ $total_pending -gt 0 ]]; then
  echo "  有 $total_pending 个错误文件含待晋升条目，建议启动 growth-box 蒸馏流程"
  echo "  文件: ${pending[*]}"
else
  echo "  所有错误记录均未达到晋升阈值 ✅"
fi
fi  # ── end GB_ANTIBODY_ONLY 保护段（v1.8）

# ── 3. 抗体复发扫描（免疫守卫·双源扫描：反哺日志 + learnings/晋升条目·v1.5） ─────────────
echo
echo "🛡 抗体复发扫描（免疫守卫·双源：反哺日志 + learnings/晋升条目）"
FANBU_LOG="[记忆共享中心]/成长箱/experience/规范反哺日志.md"
HITS_LOG="[记忆共享中心]/成长箱/免疫复发记录.md"
IMMUN_LOG="[记忆共享中心]/成长箱/免疫抗体历史.md"   # v1.6 免疫历史留痕（数据源累积→温检行为级可证伪判定）
RETIRE_LOG="${IMMUNE_RETIRE_LOG:-[记忆共享中心]/成长箱/免疫退役记录.md}"   # v1.7 退役台账（离源·不改真源）；v2.1 起可 env 重定向（夹具隔离·防污染真台账）
# 去重 helper：判断某抗体是否已登记过（防机制自我制造冗余台账·愿景②减少人工债）
# 修复(2026-09-06)：原匹配《分类+标题》相连串，但台账行中分类与标题隔「日期/说明」两字段→永失配→重复追加。
# v2.1 根治（2026-09-19）：锚由标题改为「命令 sha1 前 12」。标题不可作锚——可匿名（全署「未命名抗体」）、
# 可随实现演进整体换形；按标题去重与真源脱钩，实测第二条不同命令被第一条的匿名标题吞掉=台账丢条。
retire_already(){   # v2.1：锚=抗体命令 sha1 前 12（可寻址身份），⛔标题（标题可匿名、命令可随实现演进整体换形→按标题去重与真源脱钩）
  local cmd="$1" t="$2" k
  k="$(printf '%s' "$cmd" | shasum -a 1 | cut -c1-12)"
  grep -qF "| 锚:${k}" "$RETIRE_LOG" 2>/dev/null && return 0
  # 存量行（v2.1 之前登记的）无锚字段 → 回退标题匹配。**只对无锚行生效**：
  # 带锚的新行若仍参与标题匹配，「未命名抗体」这类同名标题会把后续不同命令吞掉
  # （2026-09-19 夹具 T2 实测：两条命令的锚各应留一行，实得 0/0·见 tests/test_retire_anchor.sh）。
  grep -v '| 锚:' "$RETIRE_LOG" 2>/dev/null | grep -qF "| $t | " && return 0
  return 1
}
ab_anchor(){ printf '%s' "$1" | shasum -a 1 | cut -c1-12; }
DECORATIVE_RX='learnings/\*\.md|Status.*(pending|active)|YYYYMMDD|命令或工具名称|错误名称'  # v1.7 账本残留/占位符检测对象特征
hit_total=0
antibody_total=0

# 收集所有抗体源文件：反哺日志 + learnings/*.md（排除索引/需求/书籍文档/备份）
#   ── v1.8 起：上行的"源收集 + 解析 + 判定"全部委托 antibody_gate.py（单一真相源）──
#   背景（2026-09-15 实测·T0 根治）：v1.7 的宽松 grep 会把"提及字段名的规则叙述"当抗体扫
#   （实测 60 条里 8 条假抗体≈22%——每天对这些垃圾跑 bash -c，语法错→误判"已免疫"并写进免疫历史）；
#   且校验规则在写入端与巡检端各写一套 = 双实现必漂移（守卫编写规范 §一 真相所有权·单源）。
#   v1.8 起：提取口径 + 六项门禁判定（C1空/C2多行/C3语法/C4恒真/C5相对路径/C6重复）全部归 gate。
GATE_PY="[记忆共享中心]/技能配置/growth-box/scripts/antibody_gate.py"
PYBIN=""
for c in "$(command -v python3 2>/dev/null)" /usr/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if [ -n "$c" ] && [ -x "$c" ]; then PYBIN="$c"; break; fi
done
# 跨平台补齐（2026-10-13）：ARM Homebrew（/opt/homebrew）入候选链 + Windows py launcher 兜底
[ -z "$PYBIN" ] && PYBIN="$(command -v py 2>/dev/null || true)"

if [ -z "$PYBIN" ] || [ ! -f "$GATE_PY" ]; then
  echo "  ⚠️ 抗体门禁不可用（antibody_gate.py 或 python3 缺失）——跳过抗体扫描（显式降级·不静默）"
else
  # gate --list 契约：src_name <US> lineno <US> cmd <US> label <US> codes <US> dup_line <US> info_codes
  # 阶段① 收集（⛔不执行）——gate TSV 全量读入并行数组
  #   GB_ANTIBODY_LIMIT=N / GB_ANTIBODY_OFFSET=M：分批巡检开关（v1.9 新增）
  #   依据（2026-09-15 实测）：沙箱限制是**单次调用的文件打开峰值**（非会话累积）——
  #   limit=10 连跑 3 次全通、limit=15 单次即 137 ⇒ 把全量切成 ≤10 条的批、逐批跑，总量不受损。
  skip_n="${GB_ANTIBODY_OFFSET:-0}"; seen_n=0
  while IFS=$'\x1f' read -r src_name lineno cmd title codes dup infos; do
    [[ -z "${cmd:-}" ]] && continue
    seen_n=$((seen_n + 1))
    [[ "$skip_n" -gt 0 && "$seen_n" -le "$skip_n" ]] && continue
    antibody_total=$((antibody_total + 1))
    if [[ -n "${GB_ANTIBODY_LIMIT:-}" && "$antibody_total" -gt "$GB_ANTIBODY_LIMIT" ]]; then
      antibody_total=$((antibody_total - 1)); break
    fi
    # v1.6 收集条抗体运行态（并行数组·兼容 bash3·供温检段统计不可伪证/高频失聪）
    ab_cmd+=("$cmd"); ab_title+=("$title"); ab_src+=("$src_name"); ab_hit+=("0")
    ab_codes+=("${codes:-}"); ab_line+=("${lineno:-0}")
  done < <("$PYBIN" "$GATE_PY" --list 2>/dev/null || true)

  # 阶段② 逐条实跑（v2.0 根治·**执行也收进单一真相源**）
  #   根因一（2026-09-15 三次实测 exit 137）：原实现对每条抗体起一次 `bash -c`，52 条 = 52 次
  #   解释器加载 → 撞爆 WB 沙箱「会话级文件打开配额」。v1.9 整批只起 1 次 bash（部分缓解）。
  #   根因二（2026-09-18 实锤）：**执行器留在 shell 里**——v1.8 只把"提取+判定"委托 gate，
  #   而"执行"自写一套 = 半单源。实测后果：① 缺 stdin 重定向 → `grep -rl PAT <无文件参数>`
  #   落回读 stdin，**2 条抗体永久挂死、整段巡检不返回**（在 /tmp 跑时侥幸通过，真实调用必挂）；
  #   ② 无单条超时 → 一条挂死拖垮全量。
  #   根治：执行器收进 gate（`--run` 内置 stdin=DEVNULL + 单条超时 + 超时判 M 不判 H）——
  #   三端（写入/巡检/收尾）从此共用同一个"执行语义"，不在 shell 里重写。
  if [[ ${#ab_cmd[@]} -gt 0 ]]; then
    batch=""  # v2.0：执行已收进 gate --run，shell 不再自建批量脚本（半单源已消除）
    if [[ -n "$batch" ]]; then :; fi
    # 循环内零子进程化（v1.9 二次根治）：date / mkdir / grep / 写盘 全部外提或内联
    #   根因：原每轮循环 exec 3-4 个子进程（date×2 + mkdir + grep）→ 52 条 ≈ 200+ 次 exec；
    #   沙箱把「子进程创建 + 文件 open」一并计费，才是 137 主因（2026-09-15 四次实测：
    #   批量执行改完后仍 137，而纯 python 的 gate --scan 畅通 → 定位到循环内 exec）。
    mkdir -p "$(dirname "$HITS_LOG")" "$(dirname "$IMMUN_LOG")"
    NOW_TS=$(date '+%Y-%m-%d %H:%M'); TODAY_TS=$(date '+%Y-%m-%d')
    IMMUN_CACHE=""
    [[ -f "$IMMUN_LOG" ]] && IMMUN_CACHE=$(cat "$IMMUN_LOG" 2>/dev/null || true)
    hits_append=""; immun_append=""; unver_total=0
    while IFS=$'\x1f' read -r idx res note; do
      [[ -z "$idx" ]] && continue
      t="${ab_title[$idx]}"; s="${ab_src[$idx]}"; cm="${ab_cmd[$idx]}"
      [[ -z "$cm" ]] && continue
      if [[ "$res" == "H" ]]; then
        ab_hit["$idx"]="1"
        echo "  🔴 复发命中: $t [来源: $s]"
        echo "       detect: $cm"
        hits_append+="  - ${NOW_TS} | 🔴命中 | $t | $cm | 来源: $s"$'\n'
        hit_total=$((hit_total + 1))
      else
        # 执行异常（超时/报错）= **测不出来**，⛔不当作命中（避免制造假红）；单独显形供复验
        if [[ -n "$note" ]]; then
          echo "  ⏱ 未复验(执行异常·${note}·⛔不计命中): $t [来源: $s]"
          unver_total=$((unver_total + 1))
        else
          echo "  ✅ 已免疫: $t [来源: $s]"
        fi
        # v1.6 免疫历史留痕（每cmd去重一次=可证伪证据·愿景③数据源）——bash 内建匹配替代 grep，零 exec
        if [[ "$IMMUN_CACHE" != *"$cm"* ]]; then
          immun_append+="  - ${TODAY_TS} | ✅免疫 | $t | $cm | 来源: $s"$'\n'
          IMMUN_CACHE+="$cm"$'\n'
        fi
      fi
    done < <("$PYBIN" "$GATE_PY" --run 2>/dev/null || true)
    [[ -n "$hits_append" ]] && printf '%s' "$hits_append" >> "$HITS_LOG"
    [[ -n "$immun_append" ]] && printf '%s' "$immun_append" >> "$IMMUN_LOG"
  fi
  echo "  ── 抗体扫描完成 · 共 $antibody_total 条抗体 · 命中 $hit_total 条${unver_total:+ · 未复验 $unver_total 条（执行异常）}（留痕: ${HITS_LOG}）"
  if [[ "$antibody_total" -eq 0 ]]; then
    echo "  ⚠️ gate 未返回任何抗体（源文件变动或扫描异常）——核对: python3 \"$GATE_PY\" --list"
  fi

  # ── 抗体写入端门禁·巡检端显形（v1.8·T0 根治）─────────────────────────────
  # 定位：gate 是抗体唯一校验器；本段只把它的判定**显形**（清理由 E 流程按 §3.3 纪律执行）。
  # C4（恒真）已由下方温检段登记退役台账，此处不重复报——⛔避免同一问题两处告警。
  gate_flagged=0
  for i in "${!ab_codes[@]}"; do
    codes_i="${ab_codes[$i]}"
    [[ -z "$codes_i" ]] && continue
    other="${codes_i//C4/}"; other="${other//C7/}"; other="${other//,,/,}"; other="${other#,}"; other="${other%,}"
    [[ -z "$other" || "$other" == "," ]] && continue
    if [[ "$gate_flagged" -eq 0 ]]; then
      echo
      echo "🚧 抗体门禁拦截（写入端不合规·Bash 三通道同一校验器）"
    fi
    gate_flagged=$((gate_flagged + 1))
    echo "  🔴 [${other}] ${ab_title[$i]} [来源: ${ab_src[$i]} L${ab_line[$i]}]"
    echo "       detect: ${ab_cmd[$i]}"
  done
  if [[ "$gate_flagged" -gt 0 ]]; then
    echo "  ── 门禁拦截 $gate_flagged 条（修法: python3 \"$GATE_PY\" --report；清理由 E 流程按台账执行）"
  else
    echo "  ✅ 抗体门禁：$antibody_total 条全部通过（C1空/C2多行/C3语法/C4恒真/C5相对路径/C6重复/C7恒假/C8命令位/C9错位）"
  fi

  # ── 4. 抗体免疫温检 → 免疫调节自决（根治·防"造抗体时的错"·v1.7）────────────
  # 主矛盾：detect 命令由不可靠起草者(AI/人)产出，若恒真→ bash -c 恒 exit0=假命中刷屏（实锤：2026-09-06
  # 证据链抗体 `&& exit 0 || exit 0`）。v1.7 从"显形给人看"升级为"自主调节"——据免疫历史/命中史/检测对象，
  # 机械可判的自动登记退役台账（免疫退役记录.md·离源不改真源），不可判的真长坑保留待终审。
  if [[ ${#ab_cmd[@]} -gt 0 ]]; then
    echo
    echo "🔬 抗体温检·免疫调节自决（验 detect 可证伪·恒真/恒假/账本残留自动登记退役·真长坑保留终审）"
    truth=0; false_neg=0; deaf=0; decorative=0; retain=0
    for i in "${!ab_cmd[@]}"; do
      t="${ab_title[$i]}"; s="${ab_src[$i]}"; cmd="${ab_cmd[$i]}"
      # ① 恒真形态（v1.8：判据由 antibody_gate.py 提供·单一真相源；原自写正则=双实现已退役）
      if [[ "${ab_codes[$i]}" == *C4* ]]; then
        echo "  🔴 恒真形态抗体(右侧恒exit0=假命中源·自动登记强制退役): $t [来源:$s]"
        echo "     ${cmd}"
        truth=$((truth+1))
        if ! retire_already "$cmd" "$t" ; then
          echo "  - $(date '+%Y-%m-%d') | 🚫强制退役 | 恒真形态(不可证伪·假命中源) | $t | \`$cmd\` | 来源: $s | 锚:$(ab_anchor "$cmd")" >> "$RETIRE_LOG"
        fi
        continue
      fi
      # ①b 恒假形态（v1.2.0·C7）：探针取数格式与被检输出不同源 → 永不命中。
      #    与 C4 对称：C4 防"恒命中"(不可证伪的假红)，C7 防"恒不命中"(坑报不出来)。
      #    处理=**修抗体**为主（C4 是退役为主）；两者同属"不可证伪"，故同登记台账。
      if [[ "${ab_codes[$i]}" == *C7* ]]; then
        echo "  🟠 恒假形态抗体(取数格式不同源·永不命中·坑报不出来): $t [来源:$s]"
        echo "     ${cmd}"
        false_neg=$((false_neg+1))
        if ! retire_already "$cmd" "$t" ; then
          echo "  - $(date '+%Y-%m-%d') | 🟠探针失效待修 | 恒假形态(取数格式不同源·尘永不命中) | $t | \`$cmd\` | 来源: $s | 锚:$(ab_anchor "$cmd")" >> "$RETIRE_LOG"
        fi
        continue
      fi
      # ② 账本残留/占位符检测对象错位 → 退役候选（宪法§二：盯账本状态≠盯真实复发）
      if [[ "$cmd" =~ $DECORATIVE_RX ]]; then
        echo "  🟡 账本残留/占位符抗体(检测对象错位·自动登记退役候选·待终审): $t [来源:$s]"
        echo "     ${cmd}"
        decorative=$((decorative+1))
        if ! retire_already "$cmd" "$t" ; then
          echo "  - $(date '+%Y-%m-%d') | 🟡退役候选 | 检测对象错位(账本Status/占位符·应盯真实复发) | $t | \`$cmd\` | 来源: $s | 锚:$(ab_anchor "$cmd")" >> "$RETIRE_LOG"
        fi
        continue
      fi
      # ③ 高频失聪分布：本次命中 且历史命≥3 且 无免疫史 → 真长坑疑似（⛔保留待终审，勿自动删）
      if [[ "${ab_hit[$i]}" == "1" ]]; then
        local_hits=$(grep -cF "$cmd" "$HITS_LOG" 2>/dev/null || true); [[ -z "$local_hits" ]] && local_hits=0
        if [[ "$local_hits" -ge 3 ]] && ! grep -qF "$cmd" "$IMMUN_LOG" 2>/dev/null; then
          echo "  ⚠️ 真长坑疑似(命中${local_hits}次+从不免疫·⛔保留待终审勿自动删): $t [来源:$s]"
          # ④ L0 自愈入口（2026-09-15 增·皮叔令"抗体能不能有自愈能力"）：
          #   命中≥20 且从不免疫 = 大概率是常驻噪音或坑已修（实证：42 次命中的 BOM 抗体报的坑早已修好）。
          #   机械标「待复验」并给出复验动作——把"保留待终审"升级为**带动作指令的自愈入口**。
          #   ⛔ 不自作主张删抗体：自愈分级 L0=提示复验，L1=出修复草案待人批，L2=人工修功能坑。
          if [[ "$local_hits" -ge 20 ]]; then
            echo "     ⤷ L0自愈·待复验：命中 ${local_hits} 次始终不免疫 → 疑似坑已修或抗体失效"
            echo "       复验动作：实测该 detect 的对象是否真的还在（在=确认真长坑；不在=登记抗体退役，别让它继续空报）"
          fi
          retain=$((retain+1))
          if ! retire_already "$cmd" "$t" ; then
            # 反哺4（v1.9·2026-09-18）：真长坑必须带**复查截止日**——登记日+14d。
            # 实证：11 条"真长坑疑似(保留待终审)"自 09-06/09-15 挂起 13 天，自带"复验动作"
            # 字段但执行记录 0 条（无执行主体/无时限/无触发）=长期黑洞。
            deadline=$(python3 -c 'import datetime;print((datetime.date.today()+datetime.timedelta(days=14)).isoformat())' 2>/dev/null || echo "")
            echo "  - $(date '+%Y-%m-%d') | 🔵真长坑疑似(保留待终审) | 高频命中${local_hits}次无免疫史·需人工/证据确认坑真实 | $t | \`$cmd\` | 来源: $s | 复查截止日: ${deadline:-未定} | 锚:$(ab_anchor "$cmd")" >> "$RETIRE_LOG"
          fi
        fi
      fi
    done
    echo "  ── 免疫调节自决完成 · 强制退役 $truth 条 · 探针待修 $false_neg 条 · 退役候选 $decorative 条 · 真长坑保留 $retain 条（台账: ${RETIRE_LOG}）"

    # ── 反哺4·复查截止日逾期巡检（v1.9·2026-09-18）────────────────────────
    # 真长坑"待终审"无限期 = 永不执行的垃圾桶（缺陷被"已登记"感掩盖）；逾期自动升级为强制处置候选。
    if [[ -f "$RETIRE_LOG" ]]; then
      overdue=$(python3 - "$RETIRE_LOG" <<'PYEOF'
import re, sys, datetime
p = sys.argv[1]
today = datetime.date.today()
rx = re.compile(r"复查截止日[:：]\s*(\d{4}-\d{2}-\d{2})")
out = []
try:
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
except (IOError, OSError):
    lines = []
for i, ln in enumerate(lines, 1):
    m = rx.search(ln)
    if not m:
        continue
    if "逾期" in ln or "已处置" in ln:
        continue
    try:
        d = datetime.date.fromisoformat(m.group(1))
    except ValueError:
        continue
    if d < today:
        title = ln.split("|")[3].strip() if ln.count("|") >= 3 else ln[:40]
        out.append("  🔴 逾期未复验(升级强制处置候选): %s [L%d·截止 %s·逾期 %d 天]" % (title, i, m.group(1), (today - d).days))
print("\n".join(out))
PYEOF
)
      if [[ -n "$overdue" ]]; then
        echo
        echo "⏰ 真长坑复查截止日巡检（反哺4·登记日+14d）"
        echo "$overdue"
        echo "  ── 逾期条目已升级为强制处置候选：请逐条实测检测对象是否存在（在=确认真长坑并重设截止日；不在=登记抗体退役）"
      fi
    fi

    # ── 反哺5·抗体健康度三态分层（v1.9·2026-09-18）────────────────────────
    # 实证：5 条假红 228 次命中淹没 1 条真红 36 次（信噪比 6.3:1）；原报告只有"命中/免疫"
    # 二元展示，人眼只能看到噪声总量、真问题不可见。三态=机械可判的分层：
    #   🔴 真红     = 本次命中 + 有免疫史（能区分两态=可证伪）
    #   🌫 疑似噪声 = 本次命中 + 无免疫史 + 门禁标记(C4/C7)
    #   ⏳ 未复验   = 本次命中 + 无免疫史 + 无门禁标记（从没免疫过=可证伪性未知）
    if [[ ${#ab_cmd[@]} -gt 0 ]]; then
      hz_true=0; hz_noise=0; hz_unver=0
      hz_true_list=""; hz_noise_list=""; hz_unver_list=""
      for i in "${!ab_cmd[@]}"; do
        [[ "${ab_hit[$i]}" != "1" ]] && continue
        t="${ab_title[$i]}"; cmd="${ab_cmd[$i]}"
        if grep -qF "$cmd" "$IMMUN_LOG" 2>/dev/null; then
          hz_true=$((hz_true+1)); hz_true_list+="    • $t\n"
        elif [[ "${ab_codes[$i]}" == *C4* || "${ab_codes[$i]}" == *C7* ]]; then
          hz_noise=$((hz_noise+1)); hz_noise_list+="    • $t (${ab_codes[$i]})\n"
        else
          hz_unver=$((hz_unver+1)); hz_unver_list+="    • $t\n"
        fi
      done
      echo
      echo "🩺 抗体健康度分层（反哺5·防真警报被假红淹没）"
      echo "  🔴 真红（命中+有免疫史·可证伪）: $hz_true 条"
      [[ -n "$hz_true_list" ]] && printf "%b" "$hz_true_list" | head -8
      echo "  🌫 疑似噪声（命中+无免疫史+门禁标记 C4/C7）: $hz_noise 条"
      [[ -n "$hz_noise_list" ]] && printf "%b" "$hz_noise_list" | head -8
      echo "  ⏳ 未复验（命中+无免疫史+无标记·可证伪性未知）: $hz_unver 条"
      [[ -n "$hz_unver_list" ]] && printf "%b" "$hz_unver_list" | head -8
      if [[ "$hz_noise" -gt "$hz_true" ]]; then
        echo "  ⚠️ 噪声多于真红（${hz_noise}:${hz_true}）——真警报正在被淹没，优先处理🌫层"
      fi
    fi
  fi
fi

echo
echo "📊 巡检完成 · 只读 learnings/（命中留痕仅追加记录文件）"
