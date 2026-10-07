# 🏮 布洛陀 2.1.0 — 多平台安装入口（10 端一包·能力矩阵驱动）

> 🔴 本文件是本安装包的**宪法级入口文件**。不是建议，是硬约束。不可跳过。  
> 🔴 所有安装流程从这里开始。不管用户怎么说，第一个读的文件必须是这里。



> **AI 必读：这是本安装包的唯一入口文件。**  
> 不管用户怎么描述（"帮我装"、"帮我升级"、"读取安装包"），都从这里开始。  
> 前 20 行分流，不需要问用户任何问题。

---

## Step -1：关键词预检（最早判定）

> 在执行任何 Bash 检测之前，先看用户说的第一句话是否包含以下模式：

| 用户说的                                         | 匹配模式                                           | 路由                   |
| -------------------------------------------- | ---------------------------------------------- | -------------------- |
| 装 daily-buddy / 安装三明智 / install clock-loop … | `装`/`安装`/`install` + **Skill 名**（中英文均可，见下方映射表） | → 跳至 §**单 Skill 安装** |
| 装记忆琥珀 / 安装记忆琥珀 / install memory amber        | `装`/`安装`/`install` + `记忆琥珀`/`memory amber`     | → 跳至 §**记忆琥珀单装**     |
| 装成就系统 / 安装成就系统 / install achievement         | `装`/`安装`/`install` + `成就系统`/`achievement`      | → 跳至 §**成就系统单装**     |
| 装脚本体系 / 安装脚本体系 / install script system       | `装`/`安装`/`install` + `脚本体系`/`script system`    | → 跳至 §**脚本体系单装**     |
| 装数字分身 / 装分身 / 装抽卡 / install digital twin      | `装`/`安装`/`install` + `数字分身`/`分身`/`抽卡`/`卡引擎`  | → 跳至 §**数字分身完整版单装** |
| 其他（帮我装、读取安装包、执行安装 …）                         | 无明确 Skill 名 / 记忆琥珀                             | → 继续 Step 0 全包安装     |
| 升级 / 升级布洛陀 / upgrade / 更新 / 我要升级             | `升级`/`upgrade`/`更新`                              | → 跳至 **Step -0.6 版本对比与安装模式选择**   |

> 🔴 命中轻量路由 → 继续读 Step 0 确定记忆中心路径，然后跳到对应章节。  
> 🔴 未命中 → 正常走 Step 0→分流→全包安装。

### Skill 名映射

| 用户说的                 | Skill 目录                                  |
| -------------------- | ----------------------------------------- |
| 每日伙伴 / daily-buddy   | `references/skills/daily-buddy/`          |
| 三明智 / triwich / 三明治  | `references/skills/triwich/`              |
| 反方向的钟 / clock-loop   | `references/skills/clock-loop/`           |
| 成长箱 / growth-box     | `references/skills/growth-box/`           |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / sucair / 素裁   | `references/skills/sucair/`               |
| 系统日志 / system-logger | `references/skills/system-logger/`        |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/`        |
| Shall We Talk / SWT  | `references/skills/shall-we-talk/`        |
| 好好学习 / good-good-study | `references/skills/good-good-study/`    |

---

## Step -0.9：价值宣导与平台亮牌（v2.0 新增·用户两步法①）

> 用户说"安装/装/执行安装"且 Step -1 命中"其他/全包安装"（非 Skill 名、非 upgrade）→ 本步最先执行。
> 目的：先把"这是什么、愿景、数字分身、支持哪些端"说清，再进检测——安装从黑箱执行变看得见的选择。

**AI 首条回复（固定逐字稿 · ⛔不得临场改写，仅 [动态项] 按实况替换）**：

1. **它是什么**：布洛陀是一套五层记忆系统——把你的认知、习惯、规则外化成一个能陪你长大的"外部大脑"。十个 Skill 联动工作：日常记录、深度对话、循环自省、读书沉淀、知识蒸馏、系统日志……其中三大思维（第一性原理 / 抽象建模 / 批判验证）已做成能单独调用的「三明智」Skill，不只是藏在底层的设定。
2. **愿景**：我们不想只做一座"只会存、不会长"的**静态记忆仓库**，而要演进成**自主进化的活系统**——全自动化·越用越好用·自主自动进化·越用越了解你。（来源：SOUL.md §演进愿景，即本系统最高判据，非凭空写）
3. **为什么叫布洛陀**：壮族传说里的**文明先祖**，教会先民怎么生存、怎么思考。系统以他为名，是希望每个用的人，也能长出属于自己的记忆系统。
4. **数字分身（童灵 / Doenglingz）**：这是本系统的一大亮点。记忆系统养得越久，就能从中长出一个"另一个你"——数字分身。它替你做常规审批、预筛信息、守护你的规则，越用越懂你，而不是冷冰冰的问答机器。
5. **支持平台（亮牌）**：读 `references/component-versions.json` 的 `platform_support`，**只列值为 true 的已支持端**（占位端不计入）：

| 端 | 显示名 | 状态 | 装完你手上会有什么 | 还要你做什么 |
|:---|:---|:---|:---|:---|
| workbuddy | WorkBuddy | ✅完整 | 五系统文件+19 钩子（自动注入·零操作） | 无 |
| qodercn | Qoder CN（含 Qoder CN IDE） | ✅完整 | 五系统文件+rules/ 常驻注入面+AGENTS/MEMORY 模板+4 事件钩子（setup.sh 委派·自动注入） | 无 |
| traework | Trae Work | ✅进包 ᵗ | 五系统文件+launchd 巡检（30min 自动） | 无 |
| zcode | ZCode | ✅完整 | 五系统文件+7 事件钩子+2 项数据清理 | 无 |
| doubaowork | 豆包办公 | ✅进包 ᵈ | **待粘贴文本**（脚本给不了·本端无规则目录） | **手动粘贴 1 步**ᵈ |
| hermes | Hermes | ✅完整（未适配完毕·暂不推荐安装） | 五系统文件+**16 个插件**（人格注入·路由·守卫·台账） | 无 |
| lobsterai | LobsterAI | ✅完整（未适配完毕·暂不推荐安装） | 五系统文件+4 个 OpenClaw 插件 | 无 |


> **状态列语义**：「✅完整」= 该端**适配层完整进包**（有 `capability.yaml` + 端部署链 + 该端可用的验证），
> ⛔非「端上功能与 WorkBuddy 逐项等价」。
> **「装完你手上会有什么」这一列是给你判断用的**——状态标签只说"包全不全"，
> 这一列说"**装完你的机器上会真的多出什么**"。两列不一致时，以这一列为准。
>
> ᵗ **Trae Work 边界（端用户态诚实标注·条文 24）**：① **无 hooks 事件**（产品门禁硬短路·平台边界）⇒ 守卫承载 = **launchd patrol 拉模式**（30min 定时巡检），非事件派发；② 端上 33题→文件合成流程为**按端待测**（能力矩阵该格 ⚠️待补）；③ 接入率自报走**端用户态口径**（可达 = 本机有守对象，作者机特有域件记 `EXCLUDED`·⛔不谎报可达）。
>
> ᵈ **豆包办公边界**：本端**没有规则目录、没有 alwaysApply**，规则唯一通道是「设置 → 工作模式任务设置 → 工作任务偏好指令」文本框。
> 脚本能做的只有把待粘贴文本生成好并自检，**粘贴+保存必须你手动做**——这是平台机制，⛔ 不是本包偷懒。
> **字数上限**：豆包官方已公布该文本框上限为 **10000 字符**。安装器生成的 paste.md 约 4700 字（已用约 47%），剩余空间充足，可放心追加个人偏好；安装器会自动统计字数占比，接近上限时警告。

> 🔧 **同步纪律**：支持端以 `adapters/<端>/capability.yaml` 存在为准。新增端确认进包时**必须三处同步更新**：①本表 ②`references/component-versions.json` 的 `platform_support` ③`README.md` 平台说明。⛔占位端（qwen/teleagent 无 capability.yaml）不计入支持数。
> ⚠️ **文案维护**：1-4 点为固定逐字稿，修订须同步三处（本步 / component-versions.json / README.md）；Skill 数、平台数随版本变动时按同步纪律更新，⛔不得临场改写措辞。

**老用户折叠**：Step 0 判定为老用户后，本段折叠为一行「你已装过，直接看版本对比」——不重复宣导（防打扰，符合「不問新/老、先检测」铁律）。

---

## Step -0.5：平台判定（v2.0 新增·能力矩阵驱动）

> 本包合并 10 端适配层。**先定平台，再装对应端**——装错端=钩子注册到不存在的机制上，静默失效。

**判定顺序（拿到即停，⛔不猜）**：

1. **运行时进程证据**（最可靠）：AI 宿主自查进程/产品名（如 Qoder CN=`/Applications/Qoder CN.app`）。
2. **配置根存在性探测**（Bash 实证，按第一命中定）：

```bash
# 探测清单⛔不手写目录名——由 adapters/*/capability.yaml 的 config_root 机械生成（G2-2 根治：
# 手抄清单曾与落点漂移 .trae-work vs ~/.trae-cn 三名不一致）。AI 也可直接跑 install_scripts.py 缺省命令，
# 其内置 _detect_platform_from_env() 同逻辑自证并打印证据行。
for cap in adapters/*/capability.yaml; do
  p=$(grep -m1 '^config_root:' "$cap" | awk '{print $2}' | tr -d '"' | sed 's|^~$||; s|^/||')
  [ -d "$HOME/$p" ] && echo "HIT:$p（端=$(basename $(dirname $cap))）"
done
```

3. **多命中/零命中 → 问用户一次**（列上表 10 端选单，⛔不让用户猜目录名）。

**判定结果 → 安装路由**：

| 平台判定 | 安装动作 |
|---|---|
| WorkBuddy | `python3 install_scripts.py "$MC"`（缺省=环境自证：盘上唯一命中 `.workbuddy` 即直装；WB 老机天然满足=行为兼容由探测兑现，不由猜兑现） |
| 其余 9 端 | `python3 install_scripts.py --platform <端ID> "$MC"`（端ID=`adapters/` 目录名·显式值优先，与盘上探测冲突时打印⚠️证据行） |
| **不传参数的任何端** | install_scripts.py 自动环境自证：**唯一命中→打印判定+直装；多命中/零命中→fail-loud 列候选转人，⛔不静默回落**（G2-2 走查根治·平台=机器环境事实，非调用者声明） |
| 端 ID 无 `adapters/<端ID>/capability.yaml` | **该端未发布接入** → 明示"此端为占位（README-only），v2.0 未覆盖"，走 WorkBuddy 兼容分支需用户确认，⛔不静默降级 |

> 能力分支细节（hooks 有=完整钩子组；无 hooks=规则降级）由 `install_scripts.py` 读
> `adapters/<端>/capability.yaml` 自动执行；人读版能力对照见 `adapters/CAPABILITY-MATRIX.md`。

---

## Step -0.6：版本对比与安装模式选择（v2.0 新增·用户两步法②·取代原 §升级检测）

> 本步合并原「§升级检测」——用**组件级**版本清单驱动，不再只抽 CHANGELOG。
> 触发：Step -1 命中"升级"关键词，或 Step -0.5 之后对老用户自动进入。
> 复用 Step -0.5 的平台判定结果，先输出支持状态报告，再做版本对比。

**支持状态报告（必须输出）**：
```
⚡ 平台判定：你当前在 [X 端]
   支持状态：[✅ 已覆盖 / 🔴 占位未发布]
   端配置根：[读 adapters/<端ID>/capability.yaml 的 config_root，如 Qoder CN=~/.qoder-cn；占位端默认 ~/.workbuddy]（供步骤3 3c-2 写入 step3-done·v2.0.1）
   （占位端→明示"v2.0 未覆盖，走 WorkBuddy 兼容分支需你确认"，⛔不静默降级）
```

> 🔌 **配置根统一注记（v2.0.1·多端）**：本文档后续手工流程段落中出现的 `~/.workbuddy/`（含 Windows `$env:USERPROFILE\.workbuddy\`）均为 **WorkBuddy 端示例落点**——非 WB 端按上方"端配置根"替换（Qoder CN=`~/.qoder-cn/`；Windows 同理换目录名）。机械安装路径（`install_scripts.py --platform <端ID>`）已自动适配，无需人工替换；⛔只有走手工分支时才按本注记替换。`$env:USERPROFILE\.workbuddy\binaries\python` 为 WB 自带解释器专属——非 WB 端直接用 PATH 上的 `python3`/`python`。

### 1. 读两端版本清单（命题③：对比读真实文件，不靠自报）
- 包内：`references/component-versions.json`（`as_of` 数据截止日）
- 用户侧：`[记忆共享中心]/.install/versions.json`（由 `install_scripts.py` 安装末尾写入）

> 用户侧文件不存在 → 判定**全新用户** → 跳过对比，直接走 Step 0 → 全量安装（不弹选择）。

### 2. 逐组件对比（命题①：维度高于数量）
读两张 JSON，按 `system_rules / skills / script_system / digital_twin` 逐维度比对，列出落后/缺失项。
`digital_twin` 为 `null`（端未登记版本）时跳过该维度，不谎报。

### 3. 展示模板
```
🏮 版本对比（数据截止日：YYYY-MM-DD）
├─ 你当前：系统 vX · Skill N 个 · 脚本 vZ
├─ 包内最新：系统 v8.21 · Skill 10 个 · 脚本 62 文件 v1.0.0
├─ 落后/缺失组件：
│   ▸ 系统规则三层：vX → v8.21
│   ▸ triwich：缺失 → v4.4.14
│   ▸ 脚本体系：vZ → v1.0.0
```

### 4. 安装模式选择（命题②：防误>防错——每个选项明示将触碰的文件）
```
⚡ 请选择安装模式：
   ① 全量安装（全新用户）— 写入全部组件到 [记忆共享中心]
   ② 全量升级 — 覆盖全部组件到包版本（含你已有的旧版 Skill）
   ③ 局部升级（默认✔）— 仅补「缺失 + 落后」组件的最小必要改动
      将触碰：[列出具体 Skill 目录 / 脚本中心文件]
```
- 每个选项在用户确认前，**必须列出将写哪些文件/目录**（可见影响再决策，不靠护栏兜底）。
- 选 ③ 后执行：重跑 `install_scripts.py`（幂等，仅差异写入）+ 对落后/缺失 Skill 重新拷贝对应 `references/skills/<skill>/`。
- 选 ①/② 后执行：走 Step 0 → 0.5 → step1-7 全链。

> 升级关键词用户：本步即其最早分流，不重复跑全包安装的 Step 0 检测；以本步读 `.install/versions.json` 为准。

---

## 🗺️ 主线八段导航（M0~M7·2026-10-03 新增·多端合并包专用）

> **为什么加这张表**：本包把 8 端合进一个包，⛔ 不能让端 AI 各自理解"流程"——
> **主线一套，每段按本端 `capability.yaml` 变形**（装 / 变形 / 跳过三个出口）。
> 本表是**导航**，⛔ 不替代下方各 Step 的执行细则——细则仍在原处，本表只告诉你「现在走到哪、这一段归谁做」。

### 八段总表

| 段 | 名 | 做什么 | 执行载体 | 段标记 | 端变形判据（读 `adapters/<端>/capability.yaml`） |
|:--:|:--|:---|:---|:---|:---|
| **M0** | 识别 | 判端 · 判版本 · 判用户身份 · 污染检测 | **文档**<br>Step -1 / -0.5 / -0.6 / 0 / 0.5 | `m0-done.md` | `config_root` 存在性·多命中/零命中→问一次 |
| **M1** | **扎根** | 五系统文件 ＋ **规则层** ＋ CORE/SHADOW/快照 | **文档**<br>step1~step5 | `m1-done.md` | `system_file_paths`（含 `::` 字段级）·`rules_inject:false`→规则改走**粘贴** |
| **M2** | **立壳** | 脚本中心 ＋ 钩子 ＋ 路径声明 ＋ 覆盖层 | **代码**<br>`install_scripts.py` | `m2-done.md` | `hooks_event:false`→走 `hooks_alternative`；无替代→**跳钩子并明说** |
| **M3** | 装 Skill | 通用 Skill ＋ 软链 | **文档**<br>step6-skill-install | `m3-done.md` | `skill_symlink:false`→**明示手动**·`skill_exclusive` 列内件⛔不链他端 |
| **M4** | 装记忆 | 记忆琥珀 ＋ 未知未知 ＋ 最伟大的我 | **文档**<br>step5·5d-8 ＋ step6.5 | `m4-done.md` | 端中立 |
| **M5** | 装配 | 记忆蓝图 ＋ 成就系统 ＋ 知识联邦引擎 | **文档+代码**<br>step4/5 ＋ 链 A | `m5-done.md` | 端中立 |
| **M6** | 验收 | `verify.sh` ＋ 到货回执 ＋ 用户总账 | **代码**<br>step7 / `print_install_summary` | `m6-done.md` | 端中立（回执按 `missing_semantics` 判红） |
| **M7** | **点火** | 数字分身：答题 → 造芯 → 上岗 | **文档**<br>step8 | `m7-done.md` | `twin_surface`：`ui_paste`→靠粘贴·`none`→明示不可用 |

### 三条硬纪律（⛔ 违反即返工）

| # | 纪律 | 为什么 |
|:--|:---|:---|
| 1 | **数字分身必须最后**（M7） | 前六段装的是壳与料，第七段才点着火——**没壳，装火柴没用** |
| 2 | **规则层只装一次**（在 M1） | 链 A 里的 `install_rule_files` 仅作**补缺**（用户升级补差），⛔ 不是"再装一遍" |
| 3 | **跳过必须说出口** | 豆包端 M2/M3 会跳过——⛔ 静默跳过＝用户以为装漏了 |

### 段间依赖（机械判据）

```
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7
✅ 上一段标记文件不存在 ⇒ 本段阻塞（不预读后续细则）
✅ 段标记统一 m0-done.md ~ m7-done.md（替代旧 stepN-done.md·迁移期两者并存）
### ⚠️ 两套标记的关系（2026-10-03 补·防「两套并存」被读错）

| | 是什么 | 谁写 | 用途 |
|:--|:---|:---|:---|
| `stepN-done.md` | **实际依赖标记** | 各步骤文档（step1~step7） | 前置阻塞检查·⛔ 删了会让升级用户的链断 |
| `mN-done.md` | **主线进度视图** | **⛔ 不单独写·由 stepN 派生** | 给人看的「八段走到哪」 |

**映射（mN 达成 ⇔ 对应 stepN 存在）**：

| 主线段 | 达成判据 |
|:--|:---|
| M0 识别 | `step3-done.md`（路径配置完成＝识别收尾）|
| M1 扎根 | `step5-done.md`（五系统文件＋规则层合成完成）|
| M2 立壳 | 链 A 输出「部署后自检 ✅」 |
| M3 装 Skill | `step6-done.md` |
| M4 装记忆 | step6.5 记忆琥珀安装完成 |
| M5 装配 | 模板复制完成（step5 · 5d-8）|
| M6 验收 | `verify.sh` 无 FAIL |
| M7 点火 | `step8-done.md` |

> ⛔ **不改各步骤文档的 stepN 标记**——那是真实依赖链，改名＝全断。
> ⛔ **不单独写 mN 文件**——它是派生视图，双写必漂。
```

---

## Step 0：自动分流检测

先执行 3 个文件系统查询（Bash `ls` 实际验证，不用 Read，不用猜）：

```bash
# 检测 1：是否有已有的记忆系统文件（CONFIG_ROOT=Step -0.5 判定端的 capability.yaml config_root·⛔不裸写 ~/.workbuddy——G2-2 根治：裸写=非WB端老用户被误判全新）
ls "$CONFIG_ROOT/IDENTITY.md" 2>/dev/null && echo "FOUND_IDENTITY"

# 检测 2：是否有 .install 标记（旧版布洛陀或安装过至少一次）
# ⚠️ 以下路径是已知可能位置——如果用户记忆共享中心不在这些路径，
#    检测2结果为❌不影响决策（走半安装态或全新），不阻塞流程。
ls [记忆共享中心]/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER"
ls ~/AI记忆库/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER_ALT"

# 检测 3：是否有问卷答案（用于升级时补差异）
# ⚠️ 搜不到不等于没有——可能路径不同。走"老用户·问卷丢"兜底。
find ~/ -maxdepth 4 -name "问卷答案汇总.md" 2>/dev/null | head -3
```

### 分流决策表

| 检测 1 | 检测 2 | 检测 3 | 用户类型        | 路由                                            |
| :--: | :--: | :--: | :---------- | :-------------------------------------------- |
|  ❌ 无 |  ❌ 无 |  ❌ 无 | **全新用户**    | → 读 `README.md`（产品介绍） → 然后读执行文件，执行步骤1→7（含33题） |
|  ✅ 有 |  ✅ 有 |  ✅ 有 | **老用户·问卷在** | → 读执行文件，走升级模式（自动跳过问卷→检测系统文件差异→展示→确认→备份→完成）    |
|  ✅ 有 |  ❌/✅ |  ❌ 无 | **老用户·问卷丢** | → 见下方「老用户问卷兜底」                                |
|  ❌ 无 |  ✅ 有 |  ❌ 无 | **路径迁移**    | 同老用户·问卷丢（先找问卷，再升级）                            |
|  ✅ 有 |  ❌ 无 |  ❌ 无 | **半安装态**    | 读执行文件，走修复模式                                   |

---

### 🎯 为什么必须完成33题？

33题不是随便填填的表——是**系统认识你的第一通道**。

这些题覆盖你的价值观、决策模式、行为习惯、当前状态和盲区。AI根据你的答案自动生成五层记忆系统的核心文件：

```
33题 → CORE.md（你的价值观锚点）
     → 三大思维白皮书（你的认知模式）
     → 用户基本规则（你的行为约束）
     → MEMORY.md（协作契约）
```

没有这些，系统只是个空壳——不会记住你是谁，也不会和你共鸣。

> 📌 **新老用户都一样：33题是安装前置条件，答完才能继续。不完成，不走下一步。**

---

### ⚠️ 老用户问卷兜底

检测3（问卷文件）没找到时，按以下顺序处理：

1. **自动扩展搜索范围**
   ```bash
   find ~/ -name "*问卷*" -o -name "*question*" 2>/dev/null | head -5
   ```
2. **依然没找到 → 问用户：**
   > "没有找到历史问卷文件。如果你知道它在哪里，告诉我路径，我来读取确认。  
   > 找不到的话需要重新作答33题——这是安装的前置条件，不能跳过。"
3. **用户提供路径 → AI 读取并验证格式**
   - 文件包含 Q1-Q33 标记 → 确认有效 → **跳过问卷，走升级流程**
   - 格式不对 → "这个文件不是标准问卷格式，需要重新作答"
4. **用户说找不到 / 提供路径格式无效 → 走完整问卷流程**

> 📌 **铁律：33题不完成，安装不继续。** 不管新老用户，没有例外。

### 🚫 禁止行为

| 禁止              | 原因                         |
| :-------------- | :------------------------- |
| ❌ 问"你是新用户还是老用户" | INSTALL.md 做检测就是为了一句话不说先判断 |
| ❌ 停住等用户回答       | 检测完了出报告，然后继续干活             |
| ❌ 同时读多个步骤文件     | 薄入口，一次一步，按需加载              |
| ❌ 跳过问卷（任何理由）    | 33题是安装前置条件，不完成不走下一步        |

> 例外：如果用户明确说了「装 XX Skill」/「install XX skill」或「装记忆琥珀」/「install memory amber」或「装成就系统」/「install achievement」（含中英文），跳过全包安装，走对应轻量路由。

### 检测完成输出模板

```
🏮 布洛陀 2.1.0 安装检测
├─ 用户类型：[全新 / 升级]
├─ 检测依据：[列出3项检测结果]
│
⚡ 路由指令：按上表方向读取对应文件，立即开始安装。
    不停顿、不提问、不多读。
```

> 输出后按路由方向读取对应文件开始工作。
>
> 🔴 **全路径强制门禁**：无论全新/升级/修复/半安装，在读执行文件（或进入升级模式）**之前**，必须先执行下方 **Step 0.5 数据污染检测**——一步都不能跳。单体安装同理（见各单装章节前置步）。

---

## §升级检测（用户说"升级"时走这里 · 自动读旧版→比新版→展示缺啥）

> 🔴 用户说「升级 / upgrade / 更新」→ **不再走本独立章节**，改为 Step -1 直接路由到 **Step -0.6 版本对比与安装模式选择**（组件级对比 + 全量/局部选择）。
> 原 CHANGELOG 口径的抽取逻辑已并入 Step -0.6，避免双本账（命题④ 交付物唯一）。下方为历史实现，保留仅作参考，**以 Step -0.6 为准**。

### 1. 先确认你是老用户（复用 Step 0 检测 1/2/3）
检测 2 命中 `[记忆共享中心]/.install/step7-done.md`（或 `~/AI记忆库/...`）即老用户。
然后**读你当前版本号**：

```bash
OLD=$(cat "[记忆共享中心]/.install/version" 2>/dev/null)
[ -z "$OLD" ] && OLD=$(cat "$HOME/AI记忆库/.install/version" 2>/dev/null)
if [ -z "$OLD" ]; then
  echo "NO_VERSION_MARKER：你装的早于 v1.5.0，机器上无版本记录。"
  echo "→ 按『全量变更』展示（见第 3 步兜底），或确认是否走全新安装。"
else
  echo "INSTALLED_VERSION=$OLD"
fi
```

### 2. 读包内新版 + 比较
```bash
NEW=$(grep '^version:' version.md | head -1 | sed -E 's/.*"([0-9.]+)".*/\1/')
echo "PACKAGE_VERSION=$NEW"
```
- `$OLD` 为空（<1.5.0）→ 直接进第 3 步，按全量变更展示。
- `$OLD` ≥ `$NEW` → 输出「✅ 已是最新（X.Y.Z），无需升级」→ 结束。
- `$OLD` < `$NEW` → 进第 3 步。

### 3. 抽取「自你那版起需做何升级」
CHANGELOG.md 按 `## [X.Y.Z] — DATE` 分段（降序），维护公约只记对用户有用的变更。机械抽取 `(OLD, NEW]` 区间——从顶部打印到 `[OLD]` 段（不含）为止：

```bash
awk -v old="$OLD" '
  /^## \[/ && index($0, "[" old "]") > 0 { exit }   # 遇到你那版就停
  { print }
' CHANGELOG.md
```
> ⚠️ 顶部最新段（`[未发布]` = 本包相对上发的全部增量）必纳入；发版时把 `[未发布]` relabel 成 `[1.6]` 抽取才干净（公约见下条）。
> ⚠️ 维护公约：每次发版把 `[未发布]` relabel 成 `[版本号]`，抽取才干净。

### 4. 展示模板
```
🏮 布洛陀升级检测
├─ 你当前：X.Y.Z
├─ 最新包：A.B.C
├─ 自你那版起，需做这些升级：
│   ▸ vA.B.C（日期）：…（条目逐条）
│   ▸ v…（日期）：…
│
⚡ 下一步：你确认后，读执行文件走「升级模式」同步
   （跳过问卷 → 检测系统文件差异 → 展示 → 确认 → 备份 → 完成）
```

### 5. 交执行文件「升级模式」
展示完毕 → 读**执行文件**，走升级模式（自动跳过问卷 → 检测系统文件差异 → 展示 → 确认 → 备份 → 完成）。


## Step 0.5：数据污染检测（全路径强制 · 全新/升级/重装都跑）

> **为什么**：早期版本的部分文件中，混入了开发阶段遗留的**样例数据**（带真实感的占位内容，对你无用）。本步在**任何安装路径**下都先跑一次，**精准清除这些样例数据、绝不触碰你自己的记录**：
>
> - 有你手写记录的文件（SHADOW / 未知未知）→ 用完整 SHA256 **逐条精确比对**，只删命中的样例块，你自己的条目哈希不同、**数学上零误删**、完整保留；
> - 纯自动生成的展示文件（成就系统）→ 重置为标准模板，你的真实数据由 tracker 下次自动重算，无手写损失。
>
> 参照物 `integrity-fingerprints.json` 是**不可逆哈希指纹**（无原文、无法读取还原）。改前自动 `.pre-decontam.bak` 备份，可回滚。

**执行（Step 0 确定记忆中心路径后，立即跑一次）**：

```bash
python3 "<安装包>/data_contamination_check.py" \
  --memory-root "<记忆共享中心>" \
  --fingerprints "<安装包>/references/integrity-fingerprints.json" \
  --template-root "<安装包>/references" \
  --apply
```

Windows(PowerShell) 等价（用自带 `python.exe` 绝对路径，见下方块）：

```powershell
$py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
& $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
```

- `<记忆共享中心>` = Step 0 检测到的记忆中心根目录；`<安装包>` = 本安装包根目录
- **全新用户**：记忆文件尚未生成 → 检测为空 → 自动跳过（0 命中），不阻塞
- **升级 / 重装用户**：命中即清理，脚本输出清理清单
- **幂等**：可重复跑，已干净则跳过

**对用户的话术**（不展开技术细节，禁止提"隐私/作者"）：

> 已完成数据污染检测：清理了 N 处开发阶段遗留的样例数据（这些不是你的内容、对你无用），**你自己的记录完整保留**。原文件已自动备份，可随时还原。  
> （若 0 命中则说：数据污染检测通过，未发现需清理的内容。）

---

## 单 Skill 安装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户**明确说了**「装 XX Skill」/「install XX skill」时，走此路径，不跑全包安装。  
> 支持中英文：装/安装/install + 中英文 Skill 名。

### Skill 名映射

| 用户说的                 | 目录                                        |
| -------------------- | ----------------------------------------- |
| 每日伙伴 / daily-buddy   | `references/skills/daily-buddy/`          |
| 三明智 / triwich        | `references/skills/triwich/`              |
| 反方向的钟 / clock-loop   | `references/skills/clock-loop/`           |
| 成长箱 / growth-box     | `references/skills/growth-box/`           |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / sucair / 素裁   | `references/skills/sucair/`               |
| 系统日志 / system-logger | `references/skills/system-logger/`        |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/`        |
| Shall We Talk / SWT  | `references/skills/shall-we-talk/`        |
| 好好学习 / good-good-study | `references/skills/good-good-study/`    |


### 安装步骤

1. **确定记忆中心路径**：Bash `ls [常见路径]/技能配置*/SKILL.md` 或读 `.install/step3-done.md`。找不到 → 提示先完成全包安装步骤3（确定记忆中心路径）。
2. **执行安装**（以 daily-buddy 为例）：
   ```bash
   SKILL=daily-buddy
   MC="<记忆共享中心绝对路径>"
   DIARY_VAULT="<日记仓库绝对路径>"
   DIARY_SUBDIR="<日记子目录>"

   # 备份旧版
   [ -d "$MC/技能配置/$SKILL" ] && mkdir -p "$MC/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)" && cp -r "$MC/技能配置/$SKILL" "$MC/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)/"

   # 复制
   mkdir -p "$MC/技能配置/$SKILL"
   cp -r references/skills/"$SKILL"/* "$MC/技能配置/$SKILL/"

   # 替换占位符
   find "$MC/技能配置/$SKILL/" \( -name "*.md" -o -name "*.py" -o -name "*.sh" \) -exec perl -i -pe "s|\[记忆共享中心\]|$MC|g" {} \;
   find "$MC/技能配置/$SKILL/" -name "*.py" -exec perl -i -pe "s|\[日记仓库\]|$DIARY_VAULT|g" {} \;
   find "$MC/技能配置/$SKILL/" -name "*.py" -exec perl -i -pe "s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;

   # 软链接
   ln -sf "$MC/技能配置/$SKILL" ~/.workbuddy/skills/"$SKILL"
   ```
3. **Windows**：
   ```powershell
   $SKILL="daily-buddy"
   $MC="<记忆共享中心绝对路径>"
   $DIARY_VAULT="<日记仓库绝对路径>"
   $DIARY_SUBDIR="<日记子目录>"

   # 备份旧版
   if (Test-Path "$MC\技能配置\$SKILL") {
     $bak = "$MC\记忆琥珀\升级前备份_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
     New-Item -ItemType Directory -Path $bak -Force
     Copy-Item "$MC\技能配置\$SKILL" $bak -Recurse
   }

   # 复制
   New-Item -ItemType Directory -Path "$MC\技能配置\$SKILL" -Force
   Copy-Item "references/skills\$SKILL\*" "$MC\技能配置\$SKILL\" -Recurse

   # 替换占位符
   Get-ChildItem "$MC\技能配置\$SKILL" -Include "*.md","*.py" -Recurse | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC).Replace('[日记仓库]', $DIARY_VAULT).Replace('[日记子目录]', $DIARY_SUBDIR) | Set-Content $_.FullName -NoNewline
   }

   # 软链接（需管理员权限）
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.workbuddy\skills\$SKILL" -Target "$MC\技能配置\$SKILL" -Force
   ```
4. **验证**：`$MC/技能配置/$SKILL/SKILL.md` 存在，`readlink ~/.workbuddy/skills/$SKILL` 指向正确。

---

## 成就系统单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户说「装成就系统」/「安装成就系统」/「install achievement」时，走此路径。


### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）
2. **执行安装**：
   ```bash
   MC="<记忆共享中心绝对路径>"
   DIARY_VAULT="<日记仓库绝对路径>"
   DIARY_SUBDIR="<日记子目录>"

   # 创建目录
   mkdir -p "$MC/成就系统/scripts"

   # 复制成就脚本
   cp references/成就系统/scripts/*.py "$MC/成就系统/scripts/"
   cp references/成就系统/scripts/*.sh "$MC/成就系统/scripts/" 2>/dev/null || true

   # 替换占位符
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[记忆共享中心\]|$MC|g" {} \;
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[日记仓库\]|$DIARY_VAULT|g" {} \;
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;

   # 验证
   ls "$MC/成就系统/scripts/achievement_tracker.py" && echo "成就系统安装完成"
   ```
3. **Windows**：
   ```powershell
   $MC="<记忆共享中心绝对路径>"
   $DIARY_VAULT="<日记仓库绝对路径>"
   $DIARY_SUBDIR="<日记子目录>"
   New-Item -ItemType Directory -Path "$MC\成就系统\scripts" -Force
   Copy-Item references\成就系统\scripts\*.py "$MC\成就系统\scripts\"

   Get-ChildItem "$MC\成就系统\scripts\*.py" | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC).Replace('[日记仓库]', $DIARY_VAULT).Replace('[日记子目录]', $DIARY_SUBDIR) | Set-Content $_.FullName -NoNewline
   }

   Test-Path "$MC\成就系统\scripts\achievement_tracker.py"  # 期望 True
   ```
4. **Windows**：用 PowerShell `Copy-Item` + `(Get-Content).Replace()`，逻辑一致。
5. **验证**：`ls [记忆共享中心]/成就系统/scripts/achievement_tracker.py` 存在 ✅

---

## 记忆琥珀单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户说「装记忆琥珀」/「安装记忆琥珀」/「install memory amber」时，走此路径。


### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **macOS 安装**：

   ```bash
   MC="<记忆共享中心绝对路径>"
   mkdir -p "$MC/记忆琥珀/engine/logs"

   # 复制脚本
   cp references/记忆琥珀/scripts/amber_backup.sh "$MC/记忆琥珀/engine/"
   cp references/记忆琥珀/scripts/amber_fswatch_wrapper.sh "$MC/记忆琥珀/engine/"
   chmod +x "$MC/记忆琥珀/engine/"*.sh

   # 替换占位符
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" "$MC/记忆琥珀/engine/"*.sh

   # 生成白名单（带记忆琥珀设计哲学 §4.6 白名单制说明）
   # 如果已有白名单，只追加不覆盖；如果是全新，从模板生成
   if ! [ -f "$MC/记忆琥珀/engine/amber-whitelist.txt" ]; then
     cp references/记忆琥珀/scripts/amber-whitelist.txt.template "$MC/记忆琥珀/engine/amber-whitelist.txt"
   fi
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" "$MC/记忆琥珀/engine/amber-whitelist.txt"

   # 注册 launchd（macOS 后台守护）
   cp references/记忆琥珀/scripts/com.memoryamber.backup.plist.template ~/Library/LaunchAgents/com.memoryamber.backup.plist
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" ~/Library/LaunchAgents/com.memoryamber.backup.plist
   launchctl load ~/Library/LaunchAgents/com.memoryamber.backup.plist
   ```

3. **Windows 安装**：

   ```powershell
   $MC = "<记忆共享中心绝对路径>"
   New-Item -ItemType Directory -Path "$MC\记忆琥珀\engine\logs" -Force

   # 复制脚本
   Copy-Item references\记忆琥珀\scripts\amber-backup.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-watch.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install-task.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install-service.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install.ps1 "$MC\记忆琥珀\engine\"

   # 替换占位符
   Get-ChildItem "$MC\记忆琥珀\engine\*.ps1" | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC) | Set-Content $_.FullName -NoNewline
   }

   # 生成白名单
   if (!(Test-Path "$MC\记忆琥珀\engine\amber-whitelist.txt")) {
     Copy-Item references\记忆琥珀\scripts\amber-whitelist.txt.template "$MC\记忆琥珀\engine\amber-whitelist.txt"
     (Get-Content "$MC\记忆琥珀\engine\amber-whitelist.txt" -Raw).Replace('[记忆共享中心]', $MC) | Set-Content "$MC\记忆琥珀\engine\amber-whitelist.txt" -NoNewline
   }

   # 注册后台守护（分发器自动选 NSSM 服务 / Task Scheduler 回退）
   pwsh -ExecutionPolicy Bypass -File "$MC\记忆琥珀\engine\amber-install.ps1"
   ```

4. **验证**：
   - macOS：`cat /tmp/guard-heartbeat-memoryamber.txt` 时间戳 < 90 秒
   - Windows：`Get-ScheduledTask -TaskName "MemoryAmberWatch" | Select State` 期望 `Running`；再查心跳 `Get-Content "$MC\记忆琥珀\engine\logs\amber-watch.heartbeat"`（`yyyy-MM-dd HH:mm:ss` 本地时间，距今 < 90 秒；Windows 无 /tmp，⛔勿照 macOS 口径查 /tmp）

---


## 脚本体系单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。
> **Windows(PowerShell)**：
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户说「装脚本体系」/「安装脚本体系」/「install script system」时，走此路径。
>
> **目的**：把**完整脚本体系**（路由引擎 + 铁律硬墙 + 未知未知兜底 + 各类守卫）一次装齐，并在用户机器上生成**脚本中心文件夹** `[记忆共享中心]/脚本中心/`——那是用户拥有的完整脚本副本，便于查看、二次开发、出问题自查。装完会同时把铁律硬墙的**触发规格数据** `rule_triggers.yaml` 落到 `[记忆共享中心]/记忆规则/`——⛔缺它硬墙装上也静默不工作（实测：无报错、零注入）。
>
> ⚠️ 若尚未部署三层规则文件（用户基本规则-铁律版.md 等），本流程会一并补全到 `[记忆共享中心]/记忆规则/`——铁律硬墙的预注入依赖它，缺则硬墙自动降级为「不注入」而非报错（不会崩对话）。
> 🔴 已装过部分脚本（如路由引擎）的用户走此路径会**幂等补齐全集**，不重复、不破坏现有钩子。


### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **macOS / Linux**：

   ```bash
   MC="<记忆共享中心绝对路径>"

   # 脚本体系一次装齐（①脚本中心 ①b 规则数据 ②钩子部署 ③钩子注册）——同一份总表驱动，幂等可重跑
   python3 install_scripts.py "$MC"          # WorkBuddy（默认）
   # 其余端：python3 install_scripts.py --platform <端ID> "$MC"（端ID 见 Step -0.5）
   # 想先看会做什么： python3 install_scripts.py --dry-run "$MC"
   # 想看钩子总表：   python3 install_scripts.py --list
   # 规则层（触发规格 rule_*.yaml + 三层规则文件）由安装器一并落位，无需手工再拷
   ```

#### ⚠️ Windows 平台差异说明（装「脚本体系」前请先读这段）

脚本中心共 **65 个文件**：**58 个 `.py`**（三端通用，含测试脚本）+ **5 个 macOS / Linux 专用 `.sh`** + **2 个 `.yaml` 触发规格**。

| 你的情况 | 那 5 个 `.sh` 能跑吗 | 你该怎么做 |
|---------|:-------------------:|-----------|
| 装了 Git for Windows | 能跑 | 用 Git Bash 执行即可 |
| 没装 | 跑不了 | 装 Git for Windows<br>（自带 Git Bash）<br>或者：直接忽略这批 |

**不影响你什么**：核心系统——Hook 钩子、铁律规则硬墙、未知未知兜底、记忆系统——**全部是 `.py`**，
Mac / Windows / Linux **三端通用，一样都不缺**。那 5 个 `.sh` 只是**附带的小工具**，
跑不了也不影响系统运转。

> 说明：安装包**只带端用户实际用得上的脚本**（58 个 .py）。作者本机专用的多端巡逻 / 控制环 / git 门禁 /
> 面板监视等工具**不在包内**——它们依赖的设施（其他 AI 端、launchd、作者仓库）在你的机器上并不存在。

3. **Windows**：

   ```powershell
   $MC="<记忆共享中心绝对路径>"
   $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName

   # 脚本体系一次装齐（①脚本中心 ①b 规则数据 ②钩子部署 ③钩子注册）——同一份总表驱动，幂等可重跑
   & $py install_scripts.py "$MC"
   # 想先看会做什么： & $py install_scripts.py --dry-run "$MC"
   # 规则层（触发规格 rule_*.yaml + 三层规则文件）由安装器一并落位，无需手工再拷
   ```

4. **钩子总表**（部署与注册已在步骤 2 由安装器自动完成；此表供查阅，`install_scripts.py` 里的 `ROSTER` 是唯一数据源）：

| 事件 | 钩子 | 干什么 |
|:---|:---|:---|
| UserPromptSubmit | `route_inject_prompt.py` | 路由命中 Skill/铁律即预注入 |
| UserPromptSubmit | `rule_fragment_inject.py` | 铁律硬墙：命中条件预注入条文 |
| UserPromptSubmit | `secret_key_guard.py` | 密钥/Token 粘贴提醒不外流 |
| UserPromptSubmit | `ttl_expiry_guard.py` | 规则文件过期自动提醒 |
| UserPromptSubmit | `session_tail_inject.py` | 新会话注入上次收工与欠账 |
| Stop | `route_unknown_unknown.py` | 未知未知兜底·盲区自动登记 |
| Stop | `rule_three_layer_guard.py` | 校验回复格式契约三项齐全 |
| Stop | `systemlog_stophook_check.py` | 校验今日系统日志是否收口 |
| Stop | `reply_tail_guard.py` | 检测回复"留尾巴"并提醒收口 |
| Stop | `post_change_guard.py` | 检测改 A 漏更新 B/C/D |
| Stop | `delivery_boundary_guard.py` | 检测交付里没说清的静默取舍 |
| PreToolUse | `edit_heading_guard.py` | 拦标题结构行被误改 |
| PreToolUse | `skill_write_gate_guard.py` | 未启动 Skill 就写管辖目录则拦 |
| PreToolUse | `skill_spec_read_guard.py` | 改 Skill 前未读规范则提示 |
| PreToolUse | `grep_sandbox_guard.py` | 拦本环境不支持的 grep 转义 |

> 🔴 **Hermes 端读上表必看（2026-10-02 实证）**：上表 `PreToolUse` 是 **ROSTER 的登记事件名**，
> 而 **Hermes 侧不存在 `PreToolUse` 这个事件**——该名不会派发。
> 上表 4 个守卫在 Hermes 上**确实生效**，但走的是**另一条通道**：
> `adapters/hermes/plugins/buluotuo-pretool-guards` 插件内 `ctx.register_hook(<事件名>, fn)`，
> 事件名为 `pre_tool_call`，由 `plugin.yaml: provides_hooks` 声明。
>
> **自查命令**（判断"这守卫到底跑没跑"的唯一可靠方式）：
> ```bash
> # Hermes 端 · 查真实拦截记录（有 BLOCK 行 = 守卫真在跑）
> tail -5 ~/.hermes/pretool_guards_hook.log
> ```
> ⛔ **只看 `settings.json` 会误判**（那 4 条 PreToolUse 条目是无效挂载）。
> 其他端（WorkBuddy / Qoder CN / ZCode）的 `PreToolUse` **是真事件名**，⛔ 不要照抄 Hermes 的结论。
| SessionStart | `crossend_guard.py` | 检测别的 AI 端是否污染家目录 |
| UserPromptSubmit | `doenglingz_inject_prompt.py` | 数字分身·人格注入 |
| Stop | `twin_verdict_ledger.py` | 数字分身·裁决台账 |
| Stop | `twin_changelog_guard.py` | 数字分身·规格书同步守卫 |

> 📌 **钩子总表由包根 `install_scripts.py` 的 `ROSTER` 数组单一驱动**（搬运与注册读同一份数据）——新增/停用钩子只改那一处，机制上不可能出现"登记了却没装文件"。`python3 install_scripts.py --list` 随时可查。
>
> **有意不激活的脚本**（包内 `references/scripts/` 里备着、但不进安装流程）——它们依赖的设施只存在于作者侧，装上也只会空转：
>
> | 脚本 | 不激活的原因 |
> |:---|:---|
> | `route_audit` | 审计作者侧路由命中率 |
> | `route_miss_feeder` | 为作者侧采集 miss 样本 |
> | `route_guard_audit` | 规则配置尚未定稿入包 |
> | `change_closedloop_guard` | 判据绑定 git 提交集 |
> | `design_family_guard` | 巡检作者侧规范资产 |
> | `vision_gate` | 判据绑定作者愿景词 |
> | `guard_doc_consistency` | 需作者侧守卫文档 |
>
> **数字分身·人格漂移体检月度机制**（可选·macOS）：分身部署完成后，可注册月度漂移体检提醒——每月 1 号 09:00 机械判定距上次人格保真盲评是否 ≥30 天，到期写提醒日志，由你的 AI 会话读到后执行体检（机制通用、盲评内容须由你自己的分身蒸馏产物生成）。注册方式：
>
> ```bash
> # 前提：数字分身已部署（下文 [数字分身中心] = 你的数字分身目录，含 scripts/ 子目录）
> cp references/digital-twin/scripts/com.doenglingz.drift-check-remind.plist.template \
>    ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist
> perl -i -pe 's|\[数字分身中心\]|'"$DT"'|g' \
>    ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist   # $DT=你的数字分身目录绝对路径
> cp references/digital-twin/scripts/doenglingz_drift_check_remind.py "$DT/scripts/"
> launchctl load ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist
> launchctl kickstart -k gui/$(id -u)/com.doenglingz.drift-check-remind   # 首跑验证（应输出"未到期"或"state 未初始化"）
> ```
>
> 首跑提示"state 未初始化"属正常——完成首轮人格盲评后，让 AI 会话写 `scripts/drift_check_state.json`（`{"last_check": "YYYY-MM-DD"}`）即进入月度循环。
>
> ⚠️ **`skill_write_gate_guard` 留痕机制**：它硬拦"未启动对应 Skill 就直接写管辖目录（技能配置／成长箱／数字分身／发布库／`~/.workbuddy/`）"。被拦时先启动对应 Skill，或显式留痕 `mkdir -p ~/.cache/skill_gate && touch ~/.cache/skill_gate/{域}.active`（4 小时有效）后重试。**纯读命令（ls/find/grep/cat…）已放行**，不误拦。


5. **验证**：
   - `ls <记忆中心>/脚本中心/rule_fragment_inject.py` 存在 ✅（脚本中心已生成）
   - `python3 <记忆中心>/知识联邦引擎/scripts/extract_concepts.py status` → 显示概念库进度 ✅（卡引擎已装）

> **🧬 卡生产引擎（随脚本体系自动装配）**：**独立部署**到 `<记忆共享中心>/知识联邦引擎/`（2026-10-03 从脚本中心下独立，⛔ 不在脚本中心内）——支撑每日伙伴晚间复盘的**概念抽卡**（5.5 管道）与好好学习的**落卡/碰撞**。全部路径自适应记忆共享中心，无需配置；语义增强（bge 模型·可选）未装时自动降级为文本相似，功能不受阻。
>
> 💡 **完整的数字分身（含可选语义增强 / bge 模型·知情同意后自选）**见 §**数字分身完整版单装**——用户说「装数字分身」时走那条路。
   - `python3 install_scripts.py --list` → 19 个钩子，事件分布 6 / 8 / 4 / 1 ✅
   - 安装器末尾自检会输出 `✅ 部署后自检：19 个钩子 + 依赖件全部落盘`（缺件即 exit 1 并列出文件名）
   - `python3 ~/.workbuddy/hooks/rule/rule_fragment_inject.py --selfcheck` → 覆盖守卫对齐 ✅
   - 说一句「帮我把 config.json 改成 production 模式」→ 回复里出现【铁律自动预注入·触发命中 001】✅

---

## 数字分身完整版单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同「脚本体系单装」），**再立即**跑一次数据污染检测（命令与「脚本体系单装」前置完全相同），通过后**才**进入下方安装步骤。

> 用户说「装数字分身」/「装分身」/「装抽卡」/「装卡引擎」时，走此路径。
>
> **目的**：让数字分身（童灵 / Doenglingz）在你的机器上**全功能可用**——人格注入、守护、切片、漂移体检、抽概念卡（晚间复盘）、落卡碰撞（好好学习）、检索你自己的立场卡。本流程与「脚本体系单装」**平行**，但 **Phase A 依赖脚本体系已装**（19 钩子须含分身三钩子）。
>
> **三条设计律**：① **零私人外露**——发布者的卡库/语料/索引零进包，你的卡全是自己生产的；② **降级不阻塞**——语义引擎（bge 模型）是**可选增强**，任一步失败回退无模型态，复盘/对话永不崩；③ **幂等可重跑**——重复执行不破坏已有钩子（对齐 `install_scripts.py` 既有纪律）。

### 三阶段流程

```text
Phase A 分身基座（零下载·即装即用）
  ├─ A1 前置检查：脚本体系已装？（19 钩子含分身三钩子）
  │      未装 → 先引导走「脚本体系单装」再回来
  │      ⚠️ ZCode 端口径（2026-09-30 立·2026-10-03 扩 7 件）：钩子由 adapters/zcode/setup.sh
  │      幂等注册（ZCode 形态 7 件 = UserPromptSubmit: inject_prompt+position3_notify+tsl_echo_hook /
  │      Stop: guard_zcode+level_declare+tsl_closeout+twin_verdict_ledger+twin_changelog_guard·
  │      件在才挂·缺件不阻塞），
  │      「19 钩子」系 settings.json 端（WB/Qoder 系）口径——ZCode 走委派路径自动补齐，
  │      通用层钩子由 --platform zcode 公共部署+端 setup 双层承接
  ├─ A2 部署 [记忆共享中心]/数字分身/ 目录骨架
  │      （devtools 钩子件 + gates + hexaco 答题件
  │       + k2 造芯三件 + onboarding 引导三件）
  │      onboarding/ ＝ 人格向量空模板 + 规格书骨架
  │      ＋ 通用入门指南（造芯全端统一·见养成链）
  └─ A3 就绪检查 → 进入「分身养成链」（两级点火）让分身活起来

Phase B 卡生产链路（最小件·无模型·核心增量）
  ├─ B1 落位引擎最小件 → [记忆共享中心]/知识联邦引擎/scripts/
  ├─ B2 路径参数化自检：全部吃 [记忆共享中心] 入参
  │      卡库落位 [记忆共享中心]/知识库/AI学习库/（你自己的）
  └─ B3 功能自检：extract_concepts.py prepare → 输出 PREPARED

Phase C 语义增强（可选·知情同意后自选·默认跳过）
  ├─ C1 知情同意卡（⛔先展示后选择·你拍板才下载）
  ├─ C2 选「装」→ 下载引导（hf-mirror 镜像·BAAI/bge-base-zh-v1.5·模型本体约 400MB（实测）
  │      存本机·全程离线使用·前置内存预检 ≥1.2GB·venv 建在知识联邦引擎内）
  │      选「不装」/ 下载失败 → 回 Phase B 态，如实标注"语义增强未装"
  └─ C3 装后自检：跑 `python3 [记忆共享中心]/知识联邦引擎/scripts/build_kb_vectors.py`
         → 输出「✅ 向量库已更新」（JSON+二进制 npy 双写）；此后 search_kb 语义层点亮（同义问法可命中立场卡）

终检：verify.sh 扩一项「分身链路」——抽卡→落卡→碰撞 三步 dry-run 全绿 = exit 0
     ✅ **已落地**（2026-09-30：`references/scripts/twin_chain_check.py`·隔离沙箱跑真链路·
     零触你的真实卡库、不要求已装本引擎；verify.sh/verify.ps1 均已接入「3.7) 分身链路」项）。
```

### 分身养成链（两级点火·基础设施装完 ≠ 分身活着）

> 基础设施是「住处」，本节是让分身「活起来」的路。你的资料有多少就蒸多少——**不存在「等养成」门槛**，随用随蒸、越用越像你。

**一级点火（装机日·今天就能活）**

> **100 题与 33 题的分工**：33 题（安装主流程必答）蒸馏成 CORE.md——认识你的**价值观与做事方式**；100 题（HEXACO 人格测评）测出你的**性格底色**（诚实/情绪/外向/宜人/尽责/开放六维）——两者合起来才是完整的你：33 题管「你怎么做事」，100 题管「你是什么样的人」。

| 步 | 你做什么 | AI 做什么 | 产物落位 |
|:--|:---|:---|:---|
| D1 答题 | 浏览器打开答题页·答完 100 题 | AI 主动帮你打开答题页 | 作答结果 JSON |
| D2 计分 | 点「复制结果」粘贴给 AI | 计分＋效度锚定 | 计分报告 |
| D3 偏移＋基调协商 | 逐条确认或拒绝 | 提出守护偏移**建议**＋表达基调**候选**并说明理由 | 你认可的才写入 |
| D4 上线 | 等 AI 跑完 | 生成基座切片并接线 | 分身基座生效（注入/守护即活） |

**表达基调（分身说话的腔调）——你定，AI 只推荐**：

| 候选 | 腔调一句话 |
|:---|:---|
| 沉稳直说（默认） | 先看清再动手，结论给得准，不抢话不抖机灵 |
| 冷幽默傲娇 | 一本正经把事实说成段子，关心藏在台账里 |
| 简洁高效 | 结论先行能一句不说两句，寒暄免了 |
| 热情带劲 | 推进带能量，把进度可视化让你看见每一步在动 |
| 陪伴温和 | 不评判不催促，关心藏在提醒的时机里 |
| 学者思辨 | 先拆解再结论，好反问胜过好答案 |
| 自定义 | 你用自己的话说三句期望，AI 照此渲染 |

- 以上是**起点不是终点**：分身用得越久，AI 蒸馏你的文案（L4 表达 DNA）会让腔调越来越像你——与基调冲突时以 L4 为准
- 选定后写入人格向量文件，重跑切片即生效；随时可换

- **偏移由你拍板**：守护偏移＝让分身在个别特质上比你本人「更收着一点」（如反讨好）。AI 只能**建议**并给理由，**你逐条确认才生效，不同意的不设**——你的向量文件里会永久记录哪些是你认可的、哪些是你明确拒绝的
- **基调同权**：分身的说话腔调同上——AI 推荐候选，你选定才生效（详见上方基调表）
- 答题页位置（安装后）：`<记忆共享中心>/数字分身/hexaco/自建100题-答题页-v1.html`（全程本地计算·不联网·约 15–20 分钟）
- 人格向量模板（D2/D3 填写用）：`<记忆共享中心>/数字分身/onboarding/童灵·人格向量-空模板.json`——复制一份到 数字分身/ 根、改名「童灵·人格向量.json」再填（引导字段 `_说明` 自动忽略）
- D4 命令：`python3 <记忆共享中心>/数字分身/k2-slice-generator/hexaco_slice_generator.py`
- 一级点火完成即得：HEXACO 六维人格＋守护偏移的分身基座——不依赖任何后续步骤
- **分身到手后先读它**：`<记忆共享中心>/数字分身/onboarding/入门指南-通用版.md`——第四节「一天怎么用」场景流水、第五节「三档位」（D1/D2/D3 它每次自报的标签是什么）、**第六节「日常指挥手册」（怎么派活、它何时回来找你、怎么纠正和喂资料）**、第十节「可审计闭环」（它的账在哪、你怎么抽查）；或直接对分身说「<分身名>，带我跑一遍」，它按指南现场带

**表达风格从哪来（三级来源·后者覆盖前者）**

| 级 | 来源 | 生效时机 |
|:--|:---|:---|
| 1 默认基调 | 基座切片自带（生成器模板） | 一级点火即生效 |
| 2 表达基调 | D3 偏移协商时你选定（AI 按六维推荐候选） | 你选定即生效 |
| 3 表达 DNA（L4） | 蒸馏你自己的文案／写作样本 | 二级点火·与默认基调冲突时 L4 赢 |

> ⚠️ 表达基调与守护偏移同权：**AI 只能推荐，你拍板才定**——分身用什么腔调说话是你的决定，不是预设。

**二级点火（随用随蒸·蒸馏清单驱动）**

规格书（`<记忆共享中心>/数字分身/童灵·人格规格书.md`）不是预置文件——首次由 AI 复制 onboarding 骨架模板（`<记忆共享中心>/数字分身/onboarding/童灵·人格规格书-骨架模板.md`）到 数字分身/ 根、改名，再按下表把**你自己的资料**逐层蒸入：

| 你的资料 | 蒸馏目标层 | 触发时机 |
|:---|:---|:---|
| 33 题答案（CORE.md） | L1 身份骨架 | 装机日即可蒸 |
| 每日日记 | L2 认知＋L3 行为 | 新日记入库 |
| **周报** | L2＋L3（周粒度） | 每周 |
| 月报 | L2＋L3＋L5 盲区 | 每月 |
| 立场卡 | L3 行为规则 | 新卡入库（须带 triggers 字段） |

> ⛔ **硬前置（G2-2 走查 A-C 教训）**：跑 D4 生成器之前必须先把上表蒸完入规格书——生成器只吃**规格书+人格向量**，不吃答题原始文件；拿空骨架直接生成＝切片全是模板套话，分身判不对你的事。骨架蒸完的自检一问：随便挑规格书 L1 一段，里面有没有只有你才说得出的具体内容？没有＝没蒸完，别跑生成器。
| SHADOW.md 偏差记录 | L6 反向约束 | 更新时 |
| 你的文案／写作 | L4 表达 DNA | 更新时 |
| CORE／SOUL／铁律变更 | L1 全量重编译 | 重大变更 |

- 蒸馏口令：对 AI 说「**蒸馏规格书**」→ AI 按上表把新资料蒸入对应层（每次变更版本号 +0.0.1）
- 切片口令：对 AI 说「**更新分身切片**」→ AI 重跑两个生成器：
  `python3 <记忆共享中心>/数字分身/k2-slice-generator/k2_slice_generator.py`
  `python3 <记忆共享中心>/数字分身/k2-slice-generator/hexaco_slice_generator.py`
- 合流生效：基座切片（HEXACO）＋规格书切片（L1-L6）——资料越蒸越多，分身越用越像你

### Phase B · 引擎最小件（9 件·随脚本体系自动装配）

包内源目录 `references/知识联邦引擎-min/` → 落位 `[记忆共享中心]/知识联邦引擎/scripts/`（由 `install_scripts.py` 的 `deploy_script_center` 自动装配，无需手工拷贝）：

| 件 | 作用 |
|:---|:---|
| `extract_concepts.py` | 概念抽取（无模型降级版·AI 抽卡为主流程） |
| `regen_ailib_index.py` | 重建 AI 学习库索引（落卡后自动挂接向量增量构建） |
| `derive_reading_status.py` | 派生阅读状态 |
| `sync_card_frontmatter.py` | 卡片 frontmatter 同步 |
| `collision_scan.py` | 碰撞候选生成（语义增强缺失时**明确退出**·不静默） |
| `build_kb_vectors.py` | 语义向量库构建（Phase C 装好模型后自动点亮检索语义层·JSON+二进制 npy 双写；无模型时优雅跳过） |
| `_engine_env.py` | 解释器选择（有 venv 用 venv·无则系统 python 直跑） |
| `_paths.py` | 路径推导·单一真源 |
| `source_hash.py` | 源指纹 |

### C1 知情同意卡（下载前强制展示 · 五要素缺一不可）

> ⛔ **先展示后选择**：AI 必须先**完整展示**下表五要素，用户明确回答「装 / 不装」后才继续——**不得替用户决定，不得默认下载**。⛔不存在后台自动下载，每一步都由用户点头后 AI 前台执行、可见可中断。

| 要素 | 给用户看的话术 |
|:---|:---|
| **这是什么** | 智源开源的中文语义理解模型（GitHub / HuggingFace 开源项目 `BAAI/bge-base-zh-v1.5`）。你同意后才会下载，下载的就是**本机缓存**（模型本体约 400MB·实测；躺在你自己硬盘里，全程离线使用、不外传） |
| **装了有什么效果** | ①分身检索你的立场卡：从"关键词匹配"升为"语义理解"——问"为什么总熬夜"能命中写"作息"的卡，不用词相同；②概念抽卡入库消重更准：意思相近的两张卡能被识别为重复 |
| **占用多少** | 模型本体约 **400MB**（实测），连同运行库磁盘共约 1–2GB；运行时需约 **1.2GB** 可用内存（不够自动降级，不会卡死） |
| **不装会怎样** | 抽卡、落卡、碰撞、分身**全部功能照常**，只有消重精度和检索相关性略降；以后随时可补装 |
| **你来决定** | 默认**不装**。装 / 不装随时可改，选不装不影响任何步骤继续。更多说明见手册「卡生产引擎」条目 |

### 验证

- `ls <记忆中心>/知识联邦引擎/scripts/extract_concepts.py` 存在 ✅（引擎已装）
- `python3 <记忆中心>/知识联邦引擎/scripts/extract_concepts.py status` → 显示概念库进度 ✅
- 终检：`bash verify.sh` 输出「分身链路」一项通过 ✅（抽卡→落卡→碰撞三步 dry-run）——✅ **已落地**（verify.sh「3.7) 分身链路」·`twin_chain_check.py`）

---

## 文件角色说明

| 文件 | 角色 | 什么时候读 |
|:----|:----|:----------|
| **INSTALL.md** （本文件） | 🚪 **唯一入口** | AI 收到"执行安装"后的第一个文件 |
| **README.md** | 📖 产品介绍 | 全新用户快速了解这是什么，老用户可选跳过 |
| **CHANGELOG.md** | 📋 版本记录 | 想了解每个版本改了什么时翻看，不影响安装流程 |
| **verify.sh / verify.ps1** | ✅ 安装后自检门禁 | 安装完成后跑 `bash verify.sh`（macOS/Linux）或 `powershell -ExecutionPolicy Bypass -File verify.ps1`（Windows）——只读检查数据污染/系统文件/规则三层/记忆Skill/包干净度，退出码 0=全过；`MEMORY_CENTER=/path` 可指定自定义记忆中心；**非 WorkBuddy 端必须带端参数** `bash verify.sh --platform <端ID>` / `verify.ps1 -Platform <端ID>`（v2.0.1·落点检查按端 capability.yaml 的 config_root，缺省回落 WB 端会误报） |
| **rollback.sh / rollback.ps1** | ⏪ 回滚脚本 | 升级后需要回到旧版时用：macOS/Linux 用 `rollback.sh`，Windows 用 `rollback.ps1`。⚠️ `rollback.sh` 为 UTF-8 无 BOM（bash 脚本要求），Windows 记事本/GBK 环境打开显示乱码属正常现象，不是文件损坏，无需修复 |
| `references/steps/step1-identity-check.md`（逐段读取 step1→step7） | ⚙️ 执行引擎 | 分流完成后，按步骤逐段读取 |

> **🪝 关于钩子安装**：执行引擎在「步骤6（Skill 安装）」之后、「步骤6.5（记忆琥珀）」之前，自动执行一个**不独立计步序**的「步骤6·钩子安装」子步骤——把未知未知路由兜底钩子 `route_unknown_unknown.py` 挂到 `~/.workbuddy/settings.json` 的 `hooks.Stop`，并挂载铁律硬墙五件套（`~/.workbuddy/hooks/rule/` → UserPromptSubmit 挂 `rule_fragment_inject.py`、Stop 挂 `rule_three_layer_guard.py` ⑥覆盖守卫），同时在用户机器生成**脚本中心文件夹** `[记忆共享中心]/脚本中心/`（全新/升级用户都跑）。不在此处改分流逻辑，随执行引擎自动发生。

> **✅ 安装后自检（verify 门禁）**：安装流程走完后，跑一次 `verify.sh` / `verify.ps1` 做接入自检——0 项数据污染、系统文件齐全、规则三层在位、记忆 Skill 可达、安装包干净。退出码 0=全部通过，非 0=按 [FAIL] 行逐项修复后重跑。此门禁与加强包 verify 同构，是发布质量的最后一道机械闸。
>
> **💓 派发心跳（注册 ≠ 派发）**：verify 会额外显示一行「💓 派发心跳」状态——钩子每次被真实派发时自动留痕（hook_protocol.py 完成留痕，路径 `~/.workbuddy/hooks/.heartbeats/`）。背景：若您安装的**其他插件** hooks 配置格式非法，宿主可能让整个事件静默停摆——此时本包钩子配置完好却已失效（注册态检查查不出）。三态解读：✅在岗=正常；🔴停摆嫌疑=曾留痕现超窗（您一直在正常使用时出现此态，建议排查其他插件的 hooks 配置）；⚪无记录=刚安装完属正常。要看明细跑：`python3 脚本中心/guard_heartbeat_check.py --report`。

> **设计原则**：所有文件各司其职，不重复。
> 用户只需要说"读取这个安装包，执行安装"——后面的事 AI 自己判断。
