#!/usr/bin/env bash
# l3_conclusion_guard 回归测试（v1.2：F6修复+全层扩展后固化）
# 用例：neg1=普通任务含L3任务名+✅验证块+[📝]签名→放行 / neg2=正文中部引用L3签名+后续正文→放行
#       pos1=L3完成签名末尾+缺新段头结论块→拦截 / pos2=L3完成签名末尾+新段头结论块+署名→放行
#       pos3=L1完成签名末尾+缺L1结论块→拦截 / pos4=L2完成签名末尾+缺L2结论块→拦截
#       pos5=L1完成签名末尾+L1结论块+署名→放行
# v1.4（2026-09-05）：接入 triwich_seal.py 封口哈希链锁自检（fixtures/seal_*：record→verify 链通+篡改拦截）
# v1.6.1（2026-10-07·clock-loop Loop修复批）：契约漂移两轮落账：修"再跑一次即消警"不可达的永久红死锁（漂移判据自置FAIL致台账永不刷新·v4.4.10同族）；同批：判绿真捕获rc+SKIP剥夺落账资格+红轮FAIL守卫
# v1.6.0（2026-10-05·v4.5.0 启动简报块改造）：加「简报字段校验」——v4.5.0 后新轮次键文件
#   首部须含 路线声明/深度声明/验证保障 三字段（对话简报块3行的唯一真源·同源投影纪律文件侧）。
#   独立基线 .briefing_baseline.<dirkey>（防把 v4.5.0 前存量判永久红）；观测型，对话侧比对=已知边界不覆盖。
# v1.5.8（2026-10-02·T2 收口）：加「静默落盘锁校验」（形态+基线判据·观测型）——
#   审计发现 v4.4.15 的静默落盘锁是纯 prose（scripts/ 零行引用键文件）= 靠自觉问题复发。
#   判据：`### {步骤名}` 段数 − 公共段（隐含假设/思维顺序/路由判定）；基线只对新增轮次判红（防永久红）。
#   ⚠️ 观测型非拦截：存量老轮次无此锁机械不可区分，语义层真伪属通用规范 #14 B 类。
# v1.5.6（2026-10-02·T1 根治）：加「全量测试套件 + 契约漂移指纹检测」——
#   根因：v4.4.5 给 seal.py 加 FALSIFY_HARD_SINCE 硬拦时未同批跑 tests/，夹具 18 处 record
#   仅 1 处传 --falsify ⇒ 5 周后被撞见 5 例红。脚本对、夹具过时，但无任何东西会报警。
#   本脚本作用：把「跑测试」从靠记性变成跑 seal 自检时顺带跑；指纹台账=.seal_fingerprint（全绿才落账）。

# ⛔ 2026-09-12：l3_conclusion_guard 全端永久关闭（09-05 你令·判据=守卫规范 §3.4·扩 呈现格式禁拦律），
#    本体已改 exit 0 桩。本夹具随之退役：继续断言 exit 2 = 造「永久红」，正是报警层刚根治的失真类。
#    SKIP 而非删除=留档可审计。
echo "l3_conclusion_guard 回归夹具已迁出本脚本（守卫 2026-09-12 全端永久关闭·退役桩上的历史契约断言=复活必红的空转夹具，v4.4.10·R2③裁决移除归档不删）"
# v4.4.9·R1-P1-02根治：旧版此处 exit 0 把其后 seal 自检块打成永不可达死代码
#（标准把 run.sh 实测列为 E 组证据源=恒绿空证据）——改为守卫用例条件化、seal 自检恒可达

set -u
export PYTHONDONTWRITEBYTECODE=1  # v4.5.1:套件import seal/夹具会现生 scripts/__pycache__——评测器全树扫描判"编译缓存"=仪器自污染闭环；缓存是可再生物,源头不写最省
DIR="$(cd "$(dirname "$0")" && pwd)"
SEAL="${SEAL_SCRIPT:-$DIR/triwich_seal.py}"
# v4.4.10·R2-N4 根治：①删个人路径硬编码默认（换机断裂面）②L3_GUARD_PY 改为显式优先而非被 command -v 无条件覆盖
if [ -n "${L3_GUARD_PY:-}" ]; then PY="$L3_GUARD_PY"
elif [ -x "$(command -v python3)" ]; then PY="$(command -v python3)"
else PY="python3"; fi
FAIL=0
DRIFT=0
# 守卫用例（neg1..pos5）已迁出：归档位=开发工具/l3_conclusion_guard_tests/ 与 git 历史（恢复须经你重新拍板·v4.4.10·R2③）

# --- triwich_seal 封口哈希链锁自检（独立环境·不污染实盘 seal.log）---
SEAL_TMP="$(mktemp -d)"
SEAL_HIST="$SEAL_TMP/chat-history"
mkdir -p "$SEAL_HIST"
cp "$DIR/fixtures/seal_signed.json" "$SEAL_HIST/agent%3Amain%3Asealcase.json" 2>/dev/null \
  && echo "PASS seal 正常签名·record" && : || { echo "FAIL seal fixture缺"; FAIL=1; }
if [ -f "$SEAL_HIST/agent%3Amain%3Asealcase.json" ]; then
  export TRIWICH_HIST_DIR="$SEAL_HIST"
  export TRIWICH_SEAL_LOG="$SEAL_TMP/seal.log"
  "$PY" "$SEAL" record >/dev/null 2>&1
  rc1=$?
  "$PY" "$SEAL" verify >/dev/null 2>&1
  rc2=$?
  # 篡改内容应变 verify 拦截
  sed 's/yyy/xXX/' "$SEAL_HIST/agent%3Amain%3Asealcase.json" > "$SEAL_HIST/agent%3Amain%3Asealcase.json.tmp" \
    && mv "$SEAL_HIST/agent%3Amain%3Asealcase.json.tmp" "$SEAL_HIST/agent%3Amain%3Asealcase.json"
  "$PY" "$SEAL" verify >/dev/null 2>&1
  rc3=$?
  unset TRIWICH_HIST_DIR TRIWICH_SEAL_LOG
  [ "$rc1" -eq 0 ] && [ "$rc2" -eq 0 ] && [ "$rc3" -ne 0 ] \
    && echo "PASS seal 链通+篡改拦截 (record=$rc1 verify=$rc2 tamper=$rc3)" \
    || { echo "FAIL seal 回归 (record=$rc1 verify=$rc2 tamper=$rc3)"; FAIL=1; }
fi
rm -rf "$SEAL_TMP"

# --- v1.5.6（2026-10-02·T1 根治·防复发层）：全量测试套件 + 契约漂移检测 ---
#
# 根因（实证）：v4.4.5（2026-09-18）给 seal.py 加 FALSIFY_HARD_SINCE 硬拦时，
#   **没有同批跑 tests/**，测试夹具 18 处 record 仅 1 处传 --falsify ⇒ 5 周后
#   （2026-10-02）被 T1 撞见 5 例红。脚本是对的、夹具过时了，但没有任何东西会报警。
#   同族先例：v4.4.11「修尺子的人掰断了尺子」（修复批亲手弄坏 task-standards.json）。
#
# 本段作用：把「跑测试」从"靠记性"变成"跑 seal 自检时就顺带跑了"。
#   ① 全量套件（decision_room / seal 对抗 / mechanism_anchor / closeout / 路径可移植）
#   ② 契约漂移检测：seal.py 比其 tests/ 任一文件新 ⇒ 测试从未在最新脚本上跑过
set -u
TESTS_DIR="${TRIWICH_TESTS_DIR:-$DIR/../tests}"
SUITES="test_triwich_decision_room test_triwich_seal_adversarial test_triwich_mechanism_anchor test_closeout_guard test_guard_path_portability"

echo ""
echo "--- triwich 全量测试套件（v1.5.6·T1 根治）---"
if [ ! -d "$TESTS_DIR" ]; then
  echo "SKIP tests/ 不可达（${TESTS_DIR}）——⚠️ 无法确认 seal 夹具是否与脚本同步"
  TESTS_SKIPPED=1  # v4.5.1(F11②):跳过≠通过——无夹具时剥夺指纹台账刷新资格
else
  for t in $SUITES; do
    if [ -f "$TESTS_DIR/$t.py" ]; then
      _full="$("$PY" "$TESTS_DIR/$t.py" 2>&1)"; rc=$?  # v4.5.1(F11①):rc取python本体的码(旧版$(...|tail)的$?是tail的=假捕获);正则判据仍只见末3行(措辞口径不变)
      out=$(printf '%s\n' "$_full" | tail -3)
      # 判绿口径（v1.5.6 二次修正·首版两处写窄了·自曝）：各套件成功措辞不统一
      #   ——"结果: 18/18 通过 ✅" / "自测 11/11 全绿" / "全部通过" / "通过 6 · 失败 0"。
      #   ⛔ 不用"✅"单独判绿：对抗套件的**负例用例本身**就输出"[PASS] 对抗3 删链尾 FAIL ✅"
      #      （"删链尾被成功拦截"是期望行为，字面含 FAIL 但整 suite 是绿的）。
      #   判据=「有成功措辞」且「无失败计数字样」；零通过用"失败 0|0 失败"兜。
      if [ "$rc" -eq 0 ] \
         && echo "$out" | grep -qE "[0-9]+/[0-9]+ (通过|全绿)|全部通过|通过 [0-9]+ · 失败 0|失败 0|0 失败" \
         && ! echo "$out" | grep -qE "❌"; then
        echo "PASS $t"
      else
        echo "FAIL $t" ; echo "$out" | head -4
        FAIL=1
      fi
    else
      echo "SKIP 套件缺失：$t.py"; TESTS_SKIPPED=1  # v4.5.1(N2收口):文件级缺失同剥落账资格——旧版只封目录级
    fi
  done

  # 契约漂移检测（防「改了脚本没跑测试」复发）
  # 口径三次收紧（v1.5.6 自曝三轮·假警比不报警更坏）：
  #   ① 首版拿 seal.py 比**所有** tests/——但 tests/ 同时测 closeout_guard（宿主件·包外），
  #      那些脚本没动也会因改 tests/ 而误报 ⇒ 收到 SEAL_SUITES 两个直接测 seal 的套件。
  #   ② 二次：mtime 差 ≠ 缺口。实测 09-26 那次 seal.py 比对抗夹具新，但改的是
  #      **verify 文案串**（v1.5.4+D18，判定逻辑与退出码一字未动），对抗夹具测的是
  #      改内容/改日志/删链尾三场景，**本就不覆盖文案** ⇒ 报它是假警。
  #   ③ 三次：⛔ **mtime 会被"恢复操作"掩盖**——实测负例 A 用 `cp` 还原夹具时顺手刷新了
  #      夹具 mtime，与 `touch seal.py` 撞同一秒，判据 `<` 相等不报 ⇒ 一次真实漏跑被静默放过。
  #      改用**内容指纹**：脚本 sha256 记入指纹台账，测试全绿时才刷新台账。
  #      指纹变 + 台账里没有该指纹 ⇒ 脚本改过但没在最新版上跑过测试（判据与"跑过"绑死）。
  FINGERPRINT_FILE="${TRIWICH_FINGERPRINT_FILE:-$DIR/.seal_fingerprint}"
  PENDING_FILE="${FINGERPRINT_FILE}.pending"
  SEAL_FP=$(shasum -a 256 "$SEAL" 2>/dev/null | cut -c1-16)
  [ -z "$SEAL_FP" ] && SEAL_FP="unavailable-$(wc -c < "$SEAL" 2>/dev/null || echo 0)"

  # --- 静默落盘锁机械校验（v4.4.15 收口·2026-10-02）---
  # 缺口：v4.4.15 的「产出物静默落盘锁」是**纯 prose**，scripts/ 零行引用键文件
  #   ⇒ 与 v3.14.0 呈现豁免同构的"靠自觉"问题在执行层复发。
  # 机械判据（不自证同体·按 v4.4.6 教训）：拿**本工作区真实跑过的键文件**当样本，
  #   检查 v4.4.15 生效后（10-02 10:33 之后）铸造的轮次是否含思维产出物段。
  #   ⛔ 存量轮次（v4.4.15 之前）不判——它们当时没有这条锁，红了是历史不是回归。
  echo ""
  echo "--- 静默落盘锁校验（v4.4.15·观测型）---"
  # 路径基准（v4.4.15 收口·自曝缺陷修复）：⛔ 不可用 $PWD/steps——run.sh 的 cwd 是 Skill 安装目录，
  #   而 SKILL.md §路径基准声明规定「裸 steps/ = **当前执行工作区**」（v3.12.0 同一坑复发）。
  #   实测：skill 目录/steps/ 有 0 份键文件，真盘在 ~/steps/（本机工作区）。
  #   探测序：显式 env → Skill 目录的同级工作区候选 → HOME（对齐 triwich_closeout_guard 根探测思路）
  if [ -n "${TRIWICH_STEPS_DIR:-}" ]; then
    STEPS_DIR="$TRIWICH_STEPS_DIR"  # 已由 [ -n "${TRIWICH_STEPS_DIR:-}" ] 守卫，非空
  elif [ -d "$PWD/steps" ] && [ -n "$(ls -A "$PWD/steps"/step0-determination-*.md 2>/dev/null)" ]; then
    STEPS_DIR="$PWD/steps"
  else
    STEPS_DIR="$HOME/steps"
  fi
  # 基线文件（存量不判红·只对基线后新增轮次判红）——⛔ 须在循环前定义：脚本头部 set -u
  # 基线按 steps 目录分键（C4 根治 2026-10-02·你批）：单一 .landing_baseline 只覆盖建基线时的目录，
  #   换 cwd（=换 STEPS_DIR）后全部样本被判"新轮次"→ 历史轮次判红 30/40 现场复实在案。
  #   键 = 目录绝对路径哈希前8位；旧无键基线自动迁移到 $HOME/steps 名下（38 份基线实归该目录·不洗真红）。
  _dirkey=$(printf '%s' "$STEPS_DIR" | md5 -q 2>/dev/null | cut -c1-8 || true)
  [ -n "$_dirkey" ] || _dirkey=$(printf '%s' "$STEPS_DIR" | md5sum 2>/dev/null | cut -c1-8)
  BASELINE_FILE="${TRIWICH_LANDING_BASELINE:-$DIR/.landing_baseline.${_dirkey:-fallback}}"
  if [ ! -f "$BASELINE_FILE" ] && [ -f "$DIR/.landing_baseline" ] && [ "$STEPS_DIR" = "$HOME/steps" ]; then
    cp "$DIR/.landing_baseline" "$BASELINE_FILE"   # 迁移：旧基线归属 $HOME/steps（防把其"新轮次"误判红/防洗真红）
  fi
  if [ ! -d "$STEPS_DIR" ]; then
    echo "SKIP ${STEPS_DIR} 不可达——无法校验静默落盘锁（本轮 cwd 无 steps/）"
  else
    # ⛔ 判据不能用「键文件 mtime ≥ SKILL.md mtime」——本脚本自己每次改判据都会刷新 SKILL.md/run.sh 的
    #   mtime ⇒ 把全部真实样本排除在外（实测：改判据后 SKIP 0 份·5 份真实键文件全被跳过）。
    #   改用**形态判据**：v4.4.15 规定思维产出物按 `### {步骤名}` 分段，公共段（隐含假设/思维顺序/路由判定）
    #   之外还有实质段。存量老轮次（v4.4.15 之前）天然段数少，但**无法机械区分"老轮次"与"新轮次跳步"**——
    #   故本校验只报**观测**，并显式说明口径局限（诚实边界·对齐 §1.1 L106），不冒充"拦截"。
    CHECKED=0; VIOLATION=0; VIOL_FILES=""
    # ── 基线机制（v4.4.15 收口·防"永久红"）──
    # 31/38 份红里绝大多数是 v4.4.15 生效**前**的历史轮次（当时无此锁）——
    #   把历史全算红 = 造"永久红" = 报警器永久失效（v4.4.10 撤销 l3_conclusion_guard 的同一教训）。
    # 口径：首跑建立基线（记下当前键文件清单与数量），此后**只对基线之后新增的轮次**判红。
    if [ ! -f "$BASELINE_FILE" ]; then
      ls -1 "$STEPS_DIR"/step0-determination-*.md 2>/dev/null | xargs -n1 basename 2>/dev/null | sort > "$BASELINE_FILE" 2>/dev/null || true
      echo "INFO 静默落盘锁基线已建立（$(wc -l < "$BASELINE_FILE" | tr -d ' ') 份历史轮次）——本次不判红"
      echo "     今后只对基线之后新增的轮次判红（存量红=历史·非回归）"
      VIOLATION=0; CHECKED=0
    fi

    for kf in "$STEPS_DIR"/step0-determination-*.md; do
      [ -f "$kf" ] || continue
      # 只看 v4.4.15 生效后铸造的键（文件名内嵌 ts = YYYYMMDD_HHMMSS）
      ts=$(basename "$kf" | sed -n 's/^step0-determination-\([0-9]\{8\}\).*/\1/p')
      [ -n "$ts" ] || continue
      bn=$(basename "$kf")
      # ⛔ 不按 mtime 过滤（见上方口径说明：改判据会刷新 mtime 把样本全排除）
      if [ -f "$BASELINE_FILE" ] && ! grep -qxF "$bn" "$BASELINE_FILE"; then
        : # 新轮次（基线之后）→ 计入判红
      else
        continue   # 存量轮次 → 不判（当时无此锁）
      fi
      CHECKED=$((CHECKED+1))
      # 思维产出物段 = 有 ### {步骤名} 且非「隐含假设/思维顺序/route」等公共段
      # ⛔ 不可用 `grep -c ... || echo 0`：grep 零匹配时 rc≠0，`|| echo 0` 会再补一个 0
      #   ⇒ 变量变成 "0\n0"（首版自曝缺陷：整数比较报错 + 报"全有产出物段"的**假绿**）。
      #   口径修正：思维产出物段 = `^### ` 段**减去**公共段（隐含假设/思维顺序/路由判定）。
      real=$(grep '^### ' "$kf" 2>/dev/null | grep -vE '隐含假设|思维顺序|路由判定' | wc -l | tr -d ' ')
      [ -n "$real" ] || real=0
      if [ "$real" -eq 0 ]; then
        VIOLATION=$((VIOLATION+1)); VIOL_FILES="$VIOL_FILES $(basename "$kf")"
      fi
    done
    if [ "$CHECKED" -eq 0 ]; then
      echo "SKIP 未找到任何键文件样本（${STEPS_DIR}）——⚠️ 落盘锁尚未被真实轮次验证"
    elif [ "$VIOLATION" -gt 0 ]; then
      echo "FAIL 静默落盘锁：$VIOLATION/$CHECKED 份键文件无思维产出物段 ——$VIOL_FILES"
      echo "     ⇒ 呈现豁免在执行层复发（v3.14.0 同构问题）。查：是否只写了 Step0/0.5 就收工？"
      FAIL=1
    else
      echo "PASS 静默落盘锁（$CHECKED 份键文件均有思维产出物段）"
      echo "     口径：只对基线之后新增的轮次判红（存量历史不判）"
    fi
  fi

  # --- 简报字段校验（v4.5.0·观测型·2026-10-05 启动简报块改造）---
  # 判据：v4.5.0 生效后新铸造键文件✅DO含 路线声明/深度声明/验证保障 三字段
  #   （对话3行简报块的唯一真源——SKILL.md §Step0 · 启动简报块·同源投影纪律）。
  #   基线机制与落盘锁同构：首跑建基线不判红，此后只对基线后新增轮次判红（防"永久红"
  #   ——v4.4.10 撤销 l3_conclusion_guard 的教训）。⛔不检测对话侧逐字比对（跨端能力不一·已知边界，见 eval #53）。
  echo ""
  echo "--- 简报字段校验（v4.5.0·观测型）---"
  if [ ! -d "$STEPS_DIR" ]; then
    echo "SKIP ${STEPS_DIR} 不可达——无法校验简报字段（本轮 cwd 无 steps/）"
  else
    BRIEF_BASELINE="${TRIWICH_BRIEFING_BASELINE:-$DIR/.briefing_baseline.${_dirkey:-fallback}}"
    BF=0; BV=0; BV_FILES=""
    if [ ! -f "$BRIEF_BASELINE" ]; then
      ls -1 "$STEPS_DIR"/step0-determination-*.md 2>/dev/null | xargs -n1 basename 2>/dev/null | sort > "$BRIEF_BASELINE" 2>/dev/null || true
      echo "INFO 简报字段基线已建立（$(wc -l < "$BRIEF_BASELINE" | tr -d ' ') 份存量）——本次不判红，今后只对基线后新增轮次判红"
    fi
    for kf in "$STEPS_DIR"/step0-determination-*.md; do
      [ -f "$kf" ] || continue
      bn=$(basename "$kf")
      if [ -f "$BRIEF_BASELINE" ] && ! grep -qxF "$bn" "$BRIEF_BASELINE"; then
        : # 新轮次（基线之后）→ 计入判红
      else
        continue   # 存量轮次（v4.5.0 前无此锁）→ 不判
      fi
      BF=$((BF+1))
      MISS=0
      grep -q '\*\*路线声明\*\*' "$kf" || MISS=1
      grep -q '\*\*深度声明\*\*' "$kf" || MISS=1
      grep -q '\*\*验证保障\*\*' "$kf" || MISS=1
      if [ "$MISS" -eq 1 ]; then
        BV=$((BV+1)); BV_FILES="$BV_FILES $bn"
      fi
    done
    if [ "$BF" -eq 0 ]; then
      echo "SKIP 未找到基线后新增键文件样本（${STEPS_DIR}）——⚠️ 简报字段锁尚未被真实轮次验证"
    elif [ "$BV" -gt 0 ]; then
      echo "FAIL 简报字段：$BV/$BF 份新轮次键文件缺 路线声明/深度声明/验证保障 字段 ——$BV_FILES"
      echo "     ⇒ v4.5.0 同源投影在文件侧断裂（对话3行失去唯一真源）。查 SKILL.md §Step0 · 启动简报块"
      FAIL=1
    else
      echo "PASS 简报字段（$BF 份基线后新键文件三字段齐全）"
    fi
  fi

  if [ -f "$FINGERPRINT_FILE" ] && [ "$(cat "$FINGERPRINT_FILE" 2>/dev/null)" != "$SEAL_FP" ]; then
    # v1.6.1（2026-10-07 clock-loop Loop修复批·永久红根治）：旧实现在此无条件 FAIL=1，
    #   而台账只在 FAIL==0 时刷新 ⇒ 漂移判据自己每轮把 FAIL 置 1，"再跑一次即消警"机械上
    #   不可达=永久红报警器（v4.4.10 同族病——本脚本注释刚引用过该教训）。
    #   两轮落账：漂移首见轮写 .pending 记名并保持红（⛔不同轮洗白，反"自我消解报警器"设计不变）；
    #   次轮若仍全绿且指纹==pending ⇒ 视为"已在改后版本上全绿跑过"，落账消警。
    if [ "$FAIL" -eq 0 ] && [ "${TESTS_SKIPPED:-0}" -eq 0 ] && [ -f "$PENDING_FILE" ] && [ "$(cat "$PENDING_FILE" 2>/dev/null)" = "$SEAL_FP" ]; then  # v4.5.1(P2红轮不落账+N1收口:SKIP轮同样不落账,与L275刷新闸口径对齐)
      echo "✅ 契约漂移落账：指纹 ${SEAL_FP} 已在改后版本上连续两轮全绿（轮2兑现'再跑一次即消警'）"
      echo "$SEAL_FP" > "$FINGERPRINT_FILE" 2>/dev/null || true
      rm -f "$PENDING_FILE" 2>/dev/null || true
    else
      echo "FAIL 契约漂移：seal.py 指纹 ${SEAL_FP} ≠ 上次全绿时的 $(cat "$FINGERPRINT_FILE")"
      echo "     ⇒ 脚本改过，但测试未在该版本上跑过。**这正是 v4.4.5→10-02 的漏跑形态**。"
      echo "     请重跑一次让本次结果落账（本次 exit≠0 即为提醒，不是噪声）。"
      echo "$SEAL_FP" > "$PENDING_FILE" 2>/dev/null || true
      DRIFT=1
      FAIL=1
    fi
  elif [ -f "$PENDING_FILE" ]; then
    # 指纹回到台账值（如旧脚本被恢复）⇒ 清掉 stale pending，防残留污染台账目录
    rm -f "$PENDING_FILE" 2>/dev/null || true
  fi
fi

if [ "$FAIL" -eq 0 ] && [ "${TESTS_SKIPPED:-0}" -eq 0 ]; then
  # 全绿才刷新指纹台账：指纹 = "测试在这个脚本版本上全绿过"的唯一凭据（判据与跑过绑死）
  echo "$SEAL_FP" > "${TRIWICH_FINGERPRINT_FILE:-$DIR/.seal_fingerprint}" 2>/dev/null || true
  echo "✅ 全部通过（seal.py 指纹 $SEAL_FP 已登记）"
elif [ "${TESTS_SKIPPED:-0}" -eq 1 ] && [ "$FAIL" -eq 0 ]; then
  echo "⚠️ 未落账：tests/ 被跳过（SKIP≠通过），指纹台账保持旧值——请在有夹具的环境重跑"
elif [ "${DRIFT:-0}" = "1" ]; then
  # ⚠️ 漂移轮**故意不刷新指纹**：首版此处在告警后同轮刷新 = 跑一次就洗白（自我消解的报警器）
  echo "❌ 契约漂移未落账（指纹保持 ${SEAL_FP} 旧值）——再跑一次即消警"
else
  echo "❌ 有失败用例"
fi
exit "$FAIL"
