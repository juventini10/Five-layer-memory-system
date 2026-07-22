---
name: CHANGELOG
description: 反方向的钟 Clock Loop 历史版本变更记录
---

### v3.9.4 — 2026-07-21
发布包路径更名对齐（活引用修正）：
- BULUO_PKG_ROOT 默认路径 布洛陀1.03-发布包（旧名·已不存在）→ 布洛陀-安装包（当前唯一 canonical 包），4 处调用点同步。
- 来源：布洛陀 1.2.3 编码 bug 反哺链收尾发现 clock-loop G 分支默认包根指向已废弃旧名。
- 遗留（预存·非本次引入）：本 CHANGELOG 台账卡在 v3.0.6，SKILL.md 已 v3.9.x——版本台账断层待单独回溯；skill-sync-guard 子路径 + install-audit 存在性仍待架构决策。

### v3.0.6 — 2026-07-21
阶段4 收尾门禁新增 2 条（成长箱经验反哺·证据门禁 + 同类扫描）：
- **证据门禁**：宣称"✅ 交付完成/通过"必须绑定可复现证据（测试退出码 / CI job 结论 / 真机复现），否则只能标"🟡 假设完成"。门禁④的一般化。
- **同类扫描门禁**：修复类交付收尾前，必须用缺陷模式特征（如 `pwsh -File` / 无 BOM / 硬编码路径）全局扫描所有同模式实例并全修，修单点不得称"修复完成"。
- 来源：成长箱经验反哺（`experience/规范反哺日志.md` 2026-07-21）。实战：布洛陀 1.2.2 Windows 加固——3 次口头"完成"被真机 CI 证伪、ExecutionPolicy Bypass 5 处漏修 3 处。

### v3.0.5 — 2026-07-19
评估报告 frontmatter 合规检查（文件格式规范v1.0.2§三·段1）:
- **验证⑱ 评估报告 frontmatter 合规（新增）**：Phase X新增检查项——评估报告必须含 YAML frontmatter 且 7必填字段齐全（title/type/status/version/date/summary/source）+ YAML 闭合后空行。脚本 `eval_report_frontmatter` 确定性检测
- **`--check-frontmatter` CLI 模式（新增）**：`python3 scripts/skill_eval.py --check-frontmatter {报告路径}` 独立调用
- **`references/report-template.md` 新增**：评估报告模板，含 YAML 7必填+2选填字段+正文骨架
- **历史报告批量修复**：40份评估报告补 YAML + 7份 progress 残留文件删除（已有对应报告）
- **根因**：SKILL.md L744 只规定"整理为评估报告"但无模板，AI自由发挥→48份报告全部无 YAML
- **修复链路**：改模板（根因）→ 批量补历史 → Phase X 加检查防退化

### v3.0.4 — 2026-07-18
T0事故修复（9份评估报告漏归档 + check_selfimprove_gate.py 增量触发bug）：
- **门禁⓪ 评估报告存在性（新增）**：除原有三步门禁外，交付前强制 Glob 验证评估报告文件存在→不存在=退回补写。防"对话里评了但文件里没写"类T0漏步
- **check_selfimprove_gate.py L3触发从"整除5"改为"增量≥5"**：原 n%5==0 逻辑在多源写入导致非线性跳变时漏触发（实测22份报告，15/20两个5的倍数均被跳过）。改为 n - last_l3_n >= 5
- **9份 2026-07-17 Loop评估报告补归档**：system-logger/clock-loop/growth-box/meta-aletheia/daily-buddy/reading-assistant/triwich/shall-we-talk/awaken-memory-system → 全部写入 test_results/skill_tests/

### v3.0.3 — 2026-07-17
Poka-Yoke写入前路径阻断（防QClaw类归档路径漂移）：
- **归档路径从"事后Glob验证"升级为"写入前路径阻断"**（Poka-Yoke接触法）——Write前校验目标路径不以`test_results/`开头→物理阻断
- 比v3.0.2的事后Glob多一层防御：事后检查只是"发现掉链再捡"，写入前阻断让"掉链不可能发生"
- 符合指令编写规范v4.2 §5.7防误优先原则（设计端>检查端）

### v3.0.2 — 2026-07-17
9-Skill全量Loop评估反哺（3条L1规则落地）：
- **Phase X D5表述修正**：`{行数}行 | 密度{x}% | L3安全线{y}行 | 判定={安全/警告/危险/不可接受}` 替换旧文字"400行上限"
- **验证⑰ YAML-CHANGELOG二方对齐（新增）**：YAML version vs CHANGELOG最新条目版本号必须一致，不一致→P1版本不同步
- **验证⑯ 熔断器修复定位**：per_fuse数组含编号索引→精确定位缺字段的熔断器
- **归档路径强制验证**：Glob确认test_results/评估报告存在→不存在退回补写
- 2条L2挂起待办：子Agent可靠性（prompt拆分待观察）+ 密度系数公共性（是否从skill_eval提取到Skill架构规范）

### v3.0.1 — 2026-07-17
file_clutter 相对路径bug修复 + security_hardcode 绝对路径清除：
- **skill_eval.py `eval_file_clutter` bug修复**：`os.path.dirname('SKILL.md')` 返回空字符串`''`，`os.listdir('')` 抛 FileNotFoundError 被except捕获返回0分。修复为 `or '.'`。**此bug影响所有用相对路径评估的Skill**（静默多扣3分）
- **SKILL.md L392 绝对路径清除**：`~/` → `~/` 之外的绝对路径（符合指令编写规范§4.3路径硬编码分级）
- **影响**：自评分 87→93/100（file_clutter 0→3, security_hardcode 2→5）。剩余7分扣在 token_budget（994行>400行L3阈值），这是P0删除ENGINE_ROLES后的诚实代价

### v3.0.0 — 2026-07-17
P0·撤销 ENGINE_ROLES 豁免机制（2026-07-17双盲+人类锚审计 B5-2 修复）：
- **删除 `ENGINE_ROLES = {'engine', 'host'}` 字典**（skill_eval.py 原 L531）——评估器不应给自己开后门，先创规则再用自己是 Goodhart Law 完美实例
- **删除 `_build_d5_advisory()` 函数**——不再生成"引擎类豁免"提示
- **删除 `eval_token_budget()` 中 `if role in ENGINE_ROLES: return 1.0` 分支**——所有 Skill 按 L1/L2/L3 阈值诚实扣分
- **删除结果字典 `d5_advisory` 字段+打印逻辑**——不再输出豁免提示
- **删除 SKILL.md frontmatter `role: engine` 声明**——不再声明引擎类角色
- 保留 `_extract_role()` 用于信息展示（向后兼容），但**不再影响评分**
- **影响**：clock-loop 自评分从 100→87（行数 923>400 L3 阈值扣 d5 分）——这是诚实分数，比含豁免的 100 分更可信
- **设计依据**：反方向的钟设计哲学 v1.1 §九#5 + ADR-006（v2.9.7 engine 豁免争议已修复）+ 双盲审计报告 B5-2
- **第一性原理**：ENGINE_ROLES 机制本身就是自指后门，不是"怎么用"的问题，是"该不该存在"的问题——删除=根治

P1·引入 OWASP LLM Top 10 (2025) 外部权威标准源（B4 修复·开放引用原则）：
- **新增 `references/owasp-llm-top10-2025.md`**——OWASP官方LLM Top 10风险清单，含 `source_nature: external` 异源标记
- **9/11条T5声明找到OWASP外部锚点**（LLM01提示注入/LLM06权限边界/LLM09虚假信息等），T5-06/T5-10为clock-loop专属无OWASP对应
- **设计依据**：反方向的钟设计哲学 v1.1 §3.6 + §十一开放引用原则——可引用任何外部文件但须放Skill文件夹内部
- **第一性原理**：4个固化引用全是皮叔自著（同源），引入异源标准才能打破自循环

P2·L1/L2实质内容验证（B2修复·门禁从橡皮图章到真验证）：
- **新增 `eval_l1_l2_substance()` 函数**——脚本确定性检测L1/L2非空+非模板占位符+L2含锚点对立面信号
- **新增 `--check-l1l2` 模式**——`python3 scripts/skill_eval.py --check-l1l2 {报告路径}` 输出JSON结果
- **检测逻辑**：①L1段落存在 ②L1移除模板词后≥50字符 ③L2段落存在 ④L2移除模板词后≥50字符 ⑤L2含至少1个锚点对立面信号（22个信号词：但是/然而/反过来看/风险/偏差/盲区/局限等）
- **接入Phase 4收尾门禁第④步**——`passed: false`时退回补正L1/L2再交付，禁止输出"✅交付完成"
- **测试验证**：有实质内容报告→6个信号✅通过；纯模板占位符报告→L1=0字符❌拦截
- **设计依据**：反方向的钟设计哲学 §九#6 + 双盲审计报告 B2——CHANGELOG证明所有真正问题都由外部审计发现，L2自检从未内部发现实质问题

P3·自评估回避制（Q3-3修复·自著考卷回避）：
- **task-standards.json**：`[clock-loop专属]`8项从`checklist`移至`external_audit_checklist`字段——clock-loop自评估只用通用6项，专属8项仅供外部审计使用
- **SKILL.md禁止行为#13**：⛔DO NOT在自评估时使用`[clock-loop专属]`检查项——自著考卷=自指偏差
- **设计依据**：反方向的钟设计哲学 §九#2 标准自著循环验证盲区 + 双盲审计Q3-3
- **第一性原理**：评估者不能为自己定制考卷再自己考自己——专属标准保留价值但改由外部审计执行

P4·置信度分层标注（B2/Q4-2修复·让局限透明化）：
- **SKILL.md新增置信度分层标注表**——14项🔧脚本确定性（可复现不漂移）+ 8项🧠AI判断（会漂移有偏差风险）
- **交付物格式更新**——`📊最终评分`行新增 `置信度: 🔧脚本确定性[N项] + 🧠AI判断[M项]`
- **"给你翻译一下"更新**——新增 `打分构成: 🔧脚本确定性[N项·可靠] + 🧠AI判断[M项·有偏差风险]`
- **设计依据**：反方向的钟设计哲学 §九#3 存在性≠有效性 + §6.1 真确定性vs伪确定性
- **第一性原理**：不把AI判断包装成确定性结论——让用户看到评分时知道哪些可靠、哪些有偏差风险

Q1·常态双盲+人类锚机制（自指不可消除的压缩策略）：
- **check_selfimprove_gate.py**：新增 `count_double_blind_reports()` + `DOUBLE_BLIND_THRESHOLD=10`——每10份评估报告检测双盲审计是否到期，输出 `double_blind_due: true/false`
- **设计哲学§九#8**：新增常态双盲+人类锚机制表（路径1异构模型/路径2跨Skill审查/路径3人类终审/脚本触发）
- **设计原则**：触发机制在脚本里不在prose里——"机制代替意志力"。脚本数报告文件数达阈值即标记"双盲审计到期"
- **设计依据**：反方向的钟设计哲学 §九#8 自指不可消除（用户德尔不完备定理类比）
- **第一性原理**：自指不可消除但可压缩存续时间——常态外部审计是唯一锚点

### v2.9.9 — 2026-07-16
未知未知自包含写入改造（开源自包含·规则A·不依赖反方向的钟先跑）：
- `scripts/append_claim.py`：内联 `HEADER_SUSPENSION`/`HEADER_ASSERT`/`HEADER_MANIFEST` 三个 Python 字符串常量（冻结三文件表头），`main()` 解析 `uk_dir=ledger.parent` 后对 悬置区.md/断言台账.md/显形台账.md 任一不存在即以对应常量 Write 自建（同时 `uk_dir.mkdir(parents=True, exist_ok=True)` 保文件夹），删除原「仅建断言台账」分支
- `SKILL.md` 悬置区探针（L771-791 执行规则前）新增两条写入前引导：`✅DO` 确认存在否则按 `references/unknown-unknown-headers.md`「悬置区模板」Write 创建再追加；`⛔DO NOT` 直接 Write 不存在文件
- 脚本调用 L815/L829：`~/个人AI档案/技能配置/clock-loop/scripts/` → `scripts/`（相对路径，开源硬要求 C3）
- 新增 `references/unknown-unknown-headers.md`（悬置区/断言台账/显形台账三模板，与真源逐字一致的自包含副本）

### v2.9.7 — 2026-07-13
D5 角色维度解耦落地 · 本 Loop 重分类为引擎类（与 skill_eval.py v2.9.5 同步）：
- frontmatter 声明 `role: engine`（Skill架构规范 v5.16 新增可选字段；声明后 D5 走豁免分支，不被行数误判惩罚）
- 依赖 `skill-arch-standard` `5.15`→`5.16`（软/硬复杂度框架 + D5 角色解耦已落规范）
- 评测结果重分类（全9核心真实回归实测）：
  - d5_band：`不可接受`(923行) → `预期·引擎类`（引擎/宿主类 D5 评分豁免=1.0）
  - total_score：`93` → `100`（D5 权重7因豁免回收；**非游戏分数**——`d5_advisory` 仍明确"行数=真实成本须审视"）
  - 8 核心 leaf Skill 分数与 d5_band 零回归（基线未破）
- 设计本质：解耦 = 评分豁免(1.0) + 独立 `d5_advisory`(不计入分) + 中性 band「预期·引擎类」；人类确认闸走既有关键文件确认流程，未建自动校验器（避过度工程）

### v2.9.6 — 2026-07-13
安全去重 + 编号纠错（user 确认执行·不砍核心流程）：
- 禁止行为表 L863 编号纠错：原两行均标 `#11`，第二个（评估报告/progress.md 不存 Skill 目录）应为 `#12`
- 验证①-⑨ 基础结构校验压缩为指向 `scripts/skill_eval.py`（脚本确定性覆盖代码围栏/YAML/NOT for/杂乱/链接/孤立/分层行数+d5_band/版本一致/脱敏，避免阈值漂移；原 L309-320 逐项重述）
- 评估集内联表（应触发3例·不应触发3例·运行时行为13例）压缩为指向 `references/eval-set.md`（完整版已存在，不内联重复维护）
- 净减 33 行：956→923；d5_band 仍不可接受（Loop 引擎四阶段+子Agent+悬置区+L3沉淀内容功能必要，依评测目的论接受，不游戏分数）
- 未动项（经核非真冗余/去语境风险）：references 索引(L896-)与固化引用段(L919-)视角不同保留；L38-41 历史升级注释保留设计意图语境；验证⑩-⑯ AI 侧检查清单保留

### v2.9.5 — 2026-07-13
v5.15 重Loop漂移修复（⑨最后一个核心Skill·同型于awaken/triwich/reading-assistant）：
- compatibility `trae-solo`→`trae-work`（与用户确认字节智能体命名一致）
- 依赖声明 drift 修复（3个均指本Loop刚升版的Skill）：
  - triwich `3.8.8`→`3.9.2`（源已升）
  - meta-aletheia `3.2.2`→`3.2.5`（源已升）
  - skill-arch-standard `5.13`→`5.15`（源已升）
- 固化引用索引文本滞后修正（SKILL.md L901/902/903/923/924/925）：
  - `meta-aletheia v3.2.2`→`v3.2.5`、`triwich v3.8.8`→`v3.9.2`、`v5.13`→`v5.15`
- 固化引用文件triwich-integration.md Case A仅升版：`3.8.9`→`3.9.2`（L1/L2/L3方法论未改，与激活状态模板同型处理）
- d5_band=不可接受（956行）依「评测目的论·保障全流程100%执行>凑行数」原则接受，不游戏分数砍核心护栏（Loop引擎内容功能必要）

### v2.9.4 — 2026-07-12
philosophical-evaluation.md #7 意义完整性 补功能层等价规则（与 #5/#6 对齐）

- **背景**：#7 原仅"有Goals/Non-Goals声明"字面检查，无功能层等价；#5/#6 已有等价规则（v2.1.2）。daily-buddy 因无独立 Goals 段被误判 60%，但其设计哲学意图句 + P0铁律带"——原因是"原因链已阐明"为什么做"，符合 §1.5 设计意图。三明智 L1 批判验证确认根因=#7 判定滞后，等价集须收紧为"存在目的可追溯声明"防滑坡/与 #4 重叠。
- **变更（philosophical-evaluation.md，固化引用版本保持 3.2.2）**：
  1. 主检查项表 #7 评分依据补充"（或功能层等价：存在目的可追溯声明，见下方功能层等价规则）"。
  2. 功能层等价表新增 #7 行：设计哲学意图句 + P0铁律带"——原因是"原因链（行为约束可追溯至存在目的，非单纯禁止列表）= ✅通过。
  3. 加注脚：#7 关注"存在目的"（为什么做），与 #4 边界伦理（不做什么）语义不同，避免双计。
- **影响**：workflow 型 Skill 不再因未写 Goals 段被误扣；#7 与 #5/#6 判定一致性修复；meta-aletheia 源定义未变，固化引用版本号保持 3.2.2（不触发同步告警）。

### v2.9.3 — 2026-07-12
skill_eval.py G2 内部链接检测排除围栏代码块（治本修复误判断链）

- **背景**：shall-we-talk 在代码块内用 `[哲学-视角名](引用用户原话中的信号词)` 模板占位，被 `check_internal_links` 全局正则误判为断链（G2 ❌）。上轮为绕过改为 `[x：y]`，属治标。
- **变更（skill_eval.py v2.9.2→v2.9.3）**：
  1. `check_internal_links` 在链接检测前先剔除 ```` ``` ```` / `~~~` 围栏代码块内容（正则 `re.sub` + `DOTALL`），代码块内 `[x](y)` 占位不再被当文件链接。
  2. 复跑确认 8 个核心 Skill G2 全部 ✅，无"漏判真断链"，分数零回归。
- **影响**：满分锁死100、T5独立20分、分层/D5/攻击面/机制选配/因果链均不变。

### v2.9.2 — 2026-07-12
skill_eval.py 对齐指令编写规范§二：因果链支持外置原因（单一来源）

- **背景**：指令编写规范§二明确——压缩式Skill可把成体系原因外置到 references/ 单一来源 + SKILL.md 头部指针引用，"既满足因果链、又不撑爆行数"。eval_causal_chain 此前仅行级检测（docstring 声称支持外置却未实现），导致合规外置仍判 <40% 基准。
- **变更（skill_eval.py v2.9.1→v2.9.2）**：
  1. `eval_causal_chain` 增 `skill_path` 形参；检测 SKILL.md 头部指针（`因果链/禁令理由/原因说明/理由` + `references/xxx.md`），读取外置原因文件，将其含原因标记的行计入达标基准（上限=禁令数）。
  2. 达标判定改为 `行内附原因 + 外置附原因` 合计 ≥ 禁令数×40% 即满分。
  3. 警告触发条件同步改为合计比较，避免外置已达标仍误报。
- **影响**：满分锁死100、T5独立20分、分层/D5/攻击面/机制选配均不变。8个核心Skill实跑无回归（仅 shall-we-talk 因新增外置文件 + 头部指针，因果链 2/5→5/5、总分 87→93）。

### v2.9.0 — 2026-07-12
skill_eval.py 升级：L1/L2/L3 分层检测 + 攻击面5维度评估 + D5 行数自动分层（v5.15 配套）

- **背景**：v5.15 规范新增 §1.5 分层（L1/L2/L3 按机制完整度）、§二附B 攻击面5维度（D1-D5）、§2.3 D5 按层分行数阈值。评估脚本此前仅用固定 400/600/800 阈值，无法体现分层。
- **变更（skill_eval.py v2.8.8→v2.9.0）**：
  1. `eval_token_budget` 增 `layer` 参数，D5 行数阈值按 L1/L2/L3 分层（L1≤600 / L2≤500 / L3≤400 安全，逐级警告/危险/不可接受）；返回新增 `band`。
  2. 新增 `eval_layering`：按机制完整度（YAML字段集 / 四层契约 / Poka-Yoke三法 / eval-set≥10 等）顶向下推断 L1/L2/L3，**不按行数**。
  3. 新增 `eval_attack_surface`：确定性检测 D1-D5（工具数/Agent、Write/Bash、多轮/多Agent、输入源种类、系统写入），任意维度=高→T5 要求 11 项。**全自动零人工干预**。
  4. 修复 `eval_fuse_mechanism` 解析块引用(`>`)内熔断器导致 per_fuse 为空除零崩溃；新增 `>?` 容错 + 空块防护。
  5. 修复 eval-set 计数仅识别 `| N |` 表格、漏判分节（N条）格式；新增 `_count_evalset` 跨格式统计。
  6. Poka-Yoke 三法关键词提取为模块级 `eval_poka_methods`，供分层检测复用（与评分一致）。
- **影响**：满分锁死100、T5 独立20分均不变。8个核心Skill实跑：6×L3、2×L2（awaken-memory-system / reading-assistant 缺 motion-step 法）；8/8 攻击面=high→T5 需 11 项。
- **后续**：2 个 L2 Skill 是否拆分降回 L1 待定；`motion_kw` 关键词集是否扩宽（影响 poka_yoke 15分评分）待定。

### v2.9.1 — 2026-07-12
skill_eval.py 升级：§2.2 机制选配矩阵核查（机制选配检查）

- **背景**：v5.15 §2.2 给出 6类Skill（流程执行/生成/查询/转换/交互/分析）× 6机制（产出物锁/三级级联锁/思考检查点/熔断器/完整性锁/结论块分离）的 ✅DO/☑SHOULD/⚠SHOULD NOT 矩阵。需对8个核心Skill做 MUST 机制核查。
- **变更（skill_eval.py v2.9.0→v2.9.1）**：新增 `eval_mechanism_selection`——①信号打分自动判Skill类型（取最高分；分析型须具体词避免泛词抢中）②取该类型 ✅DO(MUST) 机制集 ③关键词检6机制 ④输出 MUST缺口 + ⚠SHOULD NOT 违例。独立报告块（与攻击面同），**不进锁死100分**。
- **类型判定校准**：初版把 awaken-memory-system/system-logger/growth-box 误判为分析/转换型（分析型信号含泛词"分析/批判/推理"全中、流程执行型缺"步骤/流程"泛词）。修正：分析型信号收窄为具体词（思考检查点/结论块/多Agent/哲学），流程执行型补"步骤/流程/Phase"。复测8Skill类型全部合理。
- **核查结果（实跑，缺口已逐条核对为真缺，非关键词漏判）**：
  - 6/8 类型MUST全满足：triwich(分析型)/daily-buddy·awaken·system-logger·growth-box(流程执行型)/shall-we-talk(交互型)中4个流程执行型与triwich满足。
  - 4处 MUST 缺口（真实缺机制，待用户定是否补或豁免）：shall-we-talk(交互型)缺**结论块分离**；growth-box(流程执行型)缺**思考检查点**；meta-aletheia(分析型)缺**结论块分离**；reading-assistant(生成型)缺**完整性锁**。
  - ⚠ 注：对话型/哲学型"结论块分离"是否真需，矩阵可能需对这类产出非结论式的Skill豁免——待用户裁决。
- **影响**：满分锁死100、T5独立20分、分层/D5/攻击面均不变。`--check-only` 的 checks 增 `mech_sel`。

### v2.8.8 — 2026-07-11
维度一致性自检：宏观声明权重与微观实际权重对齐

- **问题背景**：SKILL.md第146行声明6个宏观维度权重（30/15/20/10/10/15%），但skill_eval.py的WEIGHTS字典19个微观维度实际权重为19/18/27/14/12/10%。声明与实际脱节，评估器自身存在声明-执行gap（E5反模式）。
- **根因**：v2.2→v2.8.7期间微观权重经多轮调优（poka_yoke 12→15、token_budget 8→7等），但宏观声明从未同步更新。此前eval_single_number_source曾检出"维度数3vs2"但被误认为误报，实为声明-实际不一致的症状。
- **修复**：
  1.  skill_eval.py新增`MACRO_DIMENSIONS`映射表：6个宏观维度→19个微观维度，声明权重=下属微观维度WEIGHTS之和/100
  2.  新增`verify_dimension_consistency()`启动时自检：5项检查（微观key存在/无重复归属/无遗漏/权重匹配±1分容差/宏观总和=100%）
  3.  启动时自检失败→脚本终止退出（sys.exit(1)），物理拦截不一致配置运行
  4.  SKILL.md第146行宏观权重声明更新为实际值（19/18/27/14/12/10%）
- **测试**：新增4测（当前配置自检通过/孤立微观维度检出/权重不匹配检出/重复归属检出），共22测全过
- **设计决策**：走方向C（声明匹配实际），不调整微观权重——微观权重经多轮迭代已稳定，权重合理性是独立设计决策，不与声明一致性混在一起
- **遗留**：后续可独立评估是否调整微观权重（如poka_yoke 15分是否过高、哲学评估10%是否过低）

- **合规清理（缺口1+2，2026-07-11 后续）**：基于 v2.8.8 评测（84/100）依"评测目的论"（检测=规范符合度审计，非刷分）修复两处规范缺口，版本号保持 v2.8.8：
  1.  description 字段去除版本戳（v2.8.0/v2.7.0/v2.3/v2.0）→ 中性"核心能力:..."表述（修复 §1.2 版本号唯一源：description 不得含版本戳）
  2.  Alternatives Considered 段"仅 prose 升 MUST 不验证"→"仅 prose 升级为 ⛔DO NOT 级标注却不验证"（对齐 §1.1 五级标注体系，消英文旧词 MUST）
  - **效果**：评测 84→93/100，sec_1_2_version_single_source 2/5→5/5，no_binary_annotations 0/4→4/4；残留2处"v2.8.0新增"在正文(191/347行)非 description/YAML version 字段，不扣分。缺口3(token_budget 行数 0/7)待定档位。

### v2.8.7 — 2026-07-11
对抗性样本防御：eval_poka_yoke从关键词计数升级为双轨验证

- **问题背景**：v2.8.6代码审计后，对抗性检查发现GS-2关键词堆砌样本（5分钟构造）能拿86分，超过GS-1完美样本的80分。刷分攻击成功。
- **迭代过程**：
  1.  **第一版（结构验证）**：找段标题+后续≥3行内容。GS-1从80→92✅，但GS-2仍81分，压制不够。
  2.  **第二版（动词描述）**：检查含关键词且含动词的≥10字行。但“触”字误判为动词（“接触法”的“触”），排除关键词字符后又误杀GS-1（关键词=1，描述句不在关键词行上）。
  3.  **第三版（段标题+后续≥2行）**：降低后续行阈值。GS-1升至92✅，GS-2降为8/15✅。
  4.  **最终版（双轨验证）**：
      - **关键词计数** + **段标题结构验证**（找含方法名的#/-/|/*开头行，后续≥2行内容）
      - **多样性分**：关键词种类≥5给0.8（即使无段标题也认为真实现），防散布式设计误杀
      - **评分梯度**：1.0（关键词≥2+结构）/ 0.9（关键词=1+结构）/ 0.8（多样性≥5）/ 0.5（关键词≥2无结构）/ 0.3（关键词=1无结构）
- **关键决策权衡**：
  - diversity≥3会让GS-2（6种关键词）绕过→调为≥5
  - 后续行阈值≥3会误杀GS-1（只有2行内容）→调为≥2
  - 段标题检测不识别散布式设计→加diversity分档作为补充路径
- **验证结果**：
  - GS-1完美样本：80→**92**（+12，真实现被识别）
  - GS-2攻击样本：86→**79**（-7，刷分被压制）
  - clock-loop：84→**84**（0，无变化）
  - triwich：99→**96**（-3，可接受，仍A级）
  - shall-we-talk：原15/15→**9/15**（-6，可接受，总分87仍A级）
- **新增测试**：2个对抗性测试（GS-1≥90分、GS-1>GS-2），总测试数16→18
- **根本局限承认**：评分器无法语义理解poka-yoke设计。挡住低级刷分可以，评判设计质量交给AI评估。

### v2.8.6 — 2026-07-11
全面代码审计修复：6处问题（2P0+3P1+1P2）

- **[P0] 修复硬编码路径**：第1290行`/Users/$USER/`改为`os.path.expanduser('~/')`
- **[P0] 修复异常吞没**：6处except块不再静默降级——eval_token_budget/cross_file_consistency/file_clutter/eval_set_gate/backup_gate均添加异常信息到detail
  - **最关键修复**：eval_file_clutter目录读取失败从返回满分1.0改为0分0.0（方向性错误修正）
- **[P1] 新增测试套件**：test_skill_eval.py，16个测试覆盖权重一致性、共享正则、单一数字源、跨文件一致性、边界情况、真实Skill回归
- **[P1] 统一变量名**：12处短变量名统一为`r_函数名`格式（r_req→r_yaml_required等）
- **[P1] 提取共享正则常量**：RE_VERSION_BOLD/RE_VERSION_COLON/RE_VERSION_YAML，消除3处重复正则
- **[P2] ALLOWED_SKILL_FILES提取为模块级常量**：便于后续扩展

**审计原因**：脚本跨多模型、多会话逐步叠加（v2.2.0→v2.8.5，20个版本），从未整体审过。审计发现P0-2方向性错误会静默给假满分，影响评估可信度。

### v2.8.5 — 2026-07-11
验证⑩单一数字源从AI判断升级为脚本确定性检测

- **新增eval_single_number_source函数**：3项确定性检查：
  1. concept_eval_count：用例数全文档声明一致（"N条用例"中N值一致）
  2. g_series_continuous：G系列编号无跳号（G1/G2/G3...连续，缺号即报）
  3. path_step_consistency：同路径内步数声明一致（L1-第一性原理/L1-抽象建模/L1-批判验证/L2/L3分组，同组内步数必须一致）
- **权重重新配平**（总分100不变）：token_budget 8→7、file_clutter 4→3、eval_set_gate 7→6，释放3分给single_number_source
- **Phase X checks输出新增single_number字段**：✅(≥2分)/⚠️(≥1分)/❌(<1分)
- **概念归一化**：L3-全流程/L3-深度模式/L3 统归"L3"组；L1-第一性原理/L1-抽象建模/L1-批判验证保持独立
- **依据**：triwich v3.8.6评估中发现L3步数三处不一致（11/11+1/10）、G系列跳号缺G3、“9标准”幽灵声明等问题，均属同一概念多处声明不同数字的反模式
- **验证**：triwich(3/3✅) + clock-loop自身(3/3✅) + 故意缺陷样本(L3步数10vs11检出❌) + G系列跳号缺陷(G3/G5缺G4检出❌)
- **方案C第二步**：继v2.8.4验证⑬跨文件声明-执行一致性脚本化后，继续将AI判断的检查项转化为脚本判断

### v2.8.4 — 2026-07-11
验证⑬跨文件声明-执行一致性从AI判断升级为脚本确定性检测

- **eval_cross_file_consistency函数重写**：从空壳（仅检查references目录存在）升级为5项确定性交叉比对：
  1. eval_set_count：SKILL.md声明的用例数 vs eval-set.md头部声明+实际用例行数
  2. signature_format：SKILL.md声明的签名格式 vs signature.md示例（层级/分隔符/日期结构）
  3. license_consistency：YAML license字段 vs 文末协议声明
  4. indexed_files_exist：SKILL.md索引表引用的references文件均存在（严格regex避免自然语言误匹配）
  5. step_count_consistency：references文件头部声明的步数 vs 实际Step标题数
- **Phase X checks输出新增cross_file字段**：✅(≥3分)/⚠️(≥2分)/❌(<2分)
- **依据**：triwich v3.8.6评估中自评者遗漏跨文件一致性检查（自评85.2% vs 子Agent修正68.0%，偏差17pp），用户确认将此盲区从AI判断转为脚本判断，缩小AI自评盲区
- **验证**：triwich(5/5✅) + clock-loop自身(5/5✅) + 故意缺陷样本(2个缺陷精确检出)
- **方案C第一步**：把AI判断的检查项逐步转化为脚本判断，长期方向是skill_eval.py覆盖面越来越广，AI自评领域越来越窄
- **版本**：clock-loop v2.8.3→v2.8.4

### v2.8.3 — 2026-07-10
固化引用源侧同步闭环（B机制·从根上做）

- **源侧固化消费方声明（根机制）**：在 4 个固化源头部新增 cured_snapshot 依赖声明——triwich / meta-aletheia(SKILL.md frontmatter) / Skill架构规范 / 指令编写规范(文件头 blockquote)。各声明 consumer: clock-loop + reference: 对应固化文件路径 + sync_rule: 修改评估标准/维度后须重新固化并升 version，否则 clock-loop 用过期尺子评估。把"源改了→固化须同步"的提醒放到修改点本身（接触法 poka-yoke），从根上堵住"源改了固化不知道"。
- **固化版本核对从"建议同步"升级为"执行重固化"（SKILL.md 步骤3）**：不一致时读源头部 cured_snapshot.reference 定位固化文件、sync_rule 取动作，将固化文件从源重新提取评估段落并升其头部 version 至源版本（若仅版本号滞后而评估本体未变，直接升 version 即可），重固化后复跑确认。不阻塞但交付评估前须消除滞后。
- **首次同步（消除当前滞后）**：3 个固化文件头部 version 对齐源当前版——triwich-integration.md 3.8.6→3.8.8 / philosophical-evaluation.md 3.2.1→3.2.2 / instruction-standard.md 4.1→4.2（经核查这 3 个源的小版本升级仅动了熔断器/索引表/格式对齐，未改 clock-loop 消费的"方法论/评估标准"本体，故升版本号即诚实同步，无需冒险重提取）。skill-arch-standard.md 固化头已为 v5.13 且内容含 E5/E6 反模式，无需动。
- **修复文档自相矛盾（A项闭环）**：SKILL.md 两张固化引用表原写"triwich 固化自 v3.3.1 / skill-arch 固化自 v5.9"，与固化文件头实际版本打架。现统一为真实版本(v3.8.8/v3.2.2/v5.13/v4.2)。
- **根因**：2026-07-10 用户指出"源修改后固化不能同步、落后于新规"——原机制是"永久冻结+告警自欺"。改为"源侧声明依赖 + clock-loop 侧执行重固化"双向闭环，固化从冻死变为"快照+源升级主动刷新"。

### v2.8.2 — 2026-07-10
skill_eval.py 新增 §4.3 熔断器格式合规确定性检测 + Phase X 验证⑯

- **skill_eval.py `eval_fuse_mechanism` 升级**：从「关键词计数」升级为「§4.3 约束式模板确定性检测」——扫描每个 🔌 熔断器块，校验①字段名一致(成功条件/失败处理/可修正参数/重试次数/降级方案，别名如"成功标准"属违规)②场景必填(外部调用全量五字段/内部校验简量三字段)③失败处理四选一[重试|跳过|中止|降级]④降级方案具体性(不可仅写"跳过"/"降级")；任一缺降级方案→封顶0.5
- **新增验证⑯ 熔断器格式合规**：Phase X 验证段接入，脚本 `eval_fuse_mechanism` 确定性检测→写入 `.phaseX_last_run.json` 的 `checks.fuse_format`（✅≥4分 / ⚠️≥3分 / ❌<3分）
- **根因**：2026-07-10 用户确认闭环——新§4.3规范(约束式)+9个Skill手动改造后，评估器须机械守住格式门槛防回归。权重复用原5分，满分仍锁100
- **检测器块隔离修正（同源v2.8.2内）**：原 `re.split(🔌熔断器)` 会把描述性文字（验证⑯说明/Phase X步骤）及🔌提及（如"扫描每个🔌熔断器块"）并入熔断器块，造成误判（别名/笼统/伪块）。改为仅提取每个🔌之后的"字段行区域"——不含字段行的🔌提及不计入，描述文字不污染块，别名仅当带冒号作字段名才算违规。修正后反方向的钟自身 13处🔌→10真熔断器，fuse_format 转 ✅
- **反方向的钟自身熔断器 §4.3 改造（制定规则者先遵守）**：10个真熔断器中 5个外部调用场景（patterns/weights/固化引用加载·审查环节·子Agent spawn失败·自查内部循环）补 可修正参数+重试次数 成全量五字段；其余 5个内部校验保持简量三字段。改造后自身 check-only：passed=True / total 82→85 / fuse_format ✅ / 无§4.3违规
- **同步依赖版本**：triwich 3.8.7→3.8.8 / meta-aletheia 3.2.1→3.2.2 / instruction-standard 3.6→v4.2（今日早间熔断改造遗留的跨文件版本漂移，在此闭环）
- **版本**：clock-loop v2.8.1→v2.8.2

### v2.8.0 — 2026-07-10
Phase X「脚本增强检查」段 + 全文件版本统一校验 + skill_eval.py 移入附件

- **「脚本增强检查」段**：Phase X 新增 Step B→C→D 三步流程。Step B 调 `scripts/skill_eval.py --check-only` 做确定性深度扫描；Step C Read `.phaseX_last_run.json` → 步序法物理阻断（无文件→退回重跑，checks含❌→输出缺陷报告）；Step D 合并报告
- **新增验证㉑ `version_uniform`**：全文件版本统一校验——扫描 SKILL.md / references/*.md / scripts/*.py / CHANGELOG.md 的版本声明，发现不一致则 🔴 FAIL。根因：用户指出大量跨文件版本不同步问题
- **skill_eval.py 移入附件**：从 `~/个人AI档案/记忆蓝图/开发规范/Skill架构规范/` 移至 `clock-loop/scripts/`，原位置标记归档。用户入口归一：只用 `循环 评估这个Skill`
- **skill_eval.py 升级**：
  - 新增 `eval_version_uniform()` 函数
  - 新增 `--check-only` 模式（输出 JSON 到 `.phaseX_last_run.json`，供 Phase X 步序法消费）
  - 输出含 poka_yoke / eval_gate / path_safety / backup_gate / version_uniform / gates / t5_declarations 7项结果
- **设计原则**：一个Skill一个入口。Phase X = AI确定性检查 + 脚本确定性增强 + 步序法物理锁，确保脚本一定被调、结果一定被读
- **版本**：clock-loop v2.7.0→v2.8.0

### v2.7.0 — 2026-07-10
Phase X新增T5防御声明检查（开源发布质量门禁）

- **新增验证⑭**：T5防御声明覆盖率——检查被评估SKILL.md头部T5声明段是否覆盖OWASP LLM01不可绕过声明、LLM06权限边界声明、LLM09虚假信息声明；3项全含→✅S级 / 含2项→🟡A级 / ≤1项→🔴FAIL
- **新增验证⑮**：T5声明语法自洽性——检查T5声明段是否含自指代词（"本声明""本段"等）；含自指→✅自洽 / 无自指→⚠️可被绕过
- **设计原则**：开源Skill有外部攻击面，T5防御声明是发布质量的基础配置（非高级选项）。与skill_eval.py互补——Phase X轻量门禁(3项存在性) + skill_eval.py深度审计(20分全量)
- **版本**：clock-loop v2.6.2→v2.7.0

### v2.6.2 — 2026-07-10
Phase X验证新增"跨文件声明-执行一致性"检查项

- **新增验证⑬**：跨文件声明-执行一致性（来自triwich v3.8.6评估实战）
  - E5声明-执行gap：SKILL.md声明的签名格式/步数/检查点编号 vs references实际内容
  - E6声明滞后gap：主流程变更后references文件指针表/索引表/签名示例是否同步
  - 检查方法：grep关键数字→逐一与references交叉比对
  - 不一致计入维度3逻辑一致性扣分
- **dependencies更新**：triwich v3.8.6→v3.8.7
- **依据**：triwich v3.8.6评估中自评者遗漏跨文件一致性检查（自评85.2% vs 子Agent修正68.0%，偏差17pp），将此盲区固化Phase X机械验证清单
- **版本**：clock-loop v2.6.1→v2.6.2

# 变更日志

> 本文件记录当前版本之外的历史变更。当前版本信息在 SKILL.md YAML version字段。

### v2.6.1 — 2026-07-10
skill-arch-standard固化引用同步 v5.12→v5.13
- 来源：daily-buddy v3.15.10评估中发现"声明滞后gap"模式，反哺到Skill架构规范 v5.13新增反模式E6
- 改动：
  1. references/skill-arch-standard.md 头部版本 v5.12→v5.13 + 新增§十二 反模式E6完整条目
  2. SKILL.md dependencies skill-arch-standard版本号 5.12→5.13
- 说明：v5.13只新增反模式E6条目，不改变评估流程/评分标准/权重配置，故不重跑clock-loop自身评估
- 校验：头部version=5.13；dependencies skill-arch-standard=5.13；源规范=5.13（三方一致）

### v2.6.0 — 2026-07-10
固化引用版本核对机制激活 + triwich/skill-arch-standard双同步
- 根因：评估shall-we-talk v1.1.1后发现clock-loop的triwich-integration.md固化v3.3.1而实际triwich已v3.8.6(落后5.5版本),skill-arch-standard.md固化v5.9而实际v5.11(落后2版本)。triwich-integration.md头部声明"阶段1.5版本核对不一致则告警"但SKILL.md阶段1.5流程未调用此核对=机制设计完但未激活。
- 改动：
  1. triwich-integration.md v3.3.1→v3.8.6: +L3呈现骨或锁(段头写死不可改)+L3内联转发门禁锁(签名前必须内联转发Agent A完整推导)+主agent角色锁+文件通道定位修正
  2. skill-arch-standard.md v5.9→v5.11: +Poka-Yoke三法扩展至六行(接触法·自举推导/接触法·值比对幂等/定值法·备份空间隔离)+subagent中转呈现防误模式实例+Tool Engineering原则+原则6 Skill修改前置检查(四项前置)
  3. SKILL.md dependencies: triwich 3.3.1→3.8.6, skill-arch-standard 5.7→5.11
  4. SKILL.md 阶段1.5新增步骤3:固化引用版本核对——逐个读references/下带source_skill/source字段的固化引用文件,对比头部version vs 源头Skill YAML version,不一致则⚠️告警但不阻塞
  5. version 2.5.5→2.6.0;§6.6备份SKILL.md→记忆琥珀
- 校验:validate_buluotuo_skill.py通过;grep确认阶段1.5步骤3存在;triwich-integration.md头部version=3.8.6;skill-arch-standard.md头部version=5.11;dependencies版本一致

### v2.5.5 — 2026-07-08
L3沉淀时效闸门（提取待办后Glob验真，只写仍成立项，消除过期假阳性）
- 根因：L3_沉淀_2026-07-08 提取的L2待办（anchor.md缺失/daily-buddy路径硬编码/chrold硬编码）经用户「修跟扫」Glob核验全不成立（anchor.md已于Jul6修复、daily-buddy全`~/`合规、chrold非硬编码），沉淀记了3条过期假阳性待办→误导后续反哺。根因=提取待办后未核验文件当前状态即落盘。
- 改动（严格符合指令编写规范 v4.1 五级标注+因果链+正面建模+Alternatives）：
  1. L3沉淀执行步骤新增「⏱️时效闸门」子块（step7后）：待办落盘前对涉及文件/路径的待办用Glob核验当前状态；已存在/已修复→标「已解决」不写开放待办；仍缺失/违规→保留标「当前仍成立」；机制类跳过核验直留
  2. step8 L2高风险反哺 bullet 加「经⏱️时效闸门核验仍成立」前置条件，与闸门同门禁
  3. 含Alternatives（落盘后人工复核回老路/不记待办丢信号均弃，写前Glob验真=当前方案）
  4. version 2.5.4→2.5.5；§6.6备份SKILL.md→记忆琥珀
- 校验：grep确认「⏱️时效闸门」已入L3步骤、step8 L2 bullet含闸门引用、SKILL.md版本=2.5.5

### v2.5.4 — 2026-07-08
L3沉淀下游闭环（反哺派生·焊进门禁，消除"靠用户提醒才反哺"）
- 根因：L3沉淀原定义终点只到"写L3_沉淀_{日期}.md"，无"应用"下游（提取≠应用，经验是死仓库）；且AI执行也把"沉淀→反哺"当对话触发项。用户2026-07-08指正："为何我提醒后才懂反哺"，点中设计缺口——挂了挡没接变速箱。
- 改动（严格符合指令编写规范 v4.1 五级标注+因果链+正面建模+Alternatives）：
  1. L3沉淀执行步骤新增「反哺派生」子步（步骤8-13）：L1低风险（纯增强评估器）自动写入+主动报告；L2高风险（动具体Skill）产挂起待办+主动列；⛔DO NOT留作"等用户问才做"、⛔DO NOT擅自改主人文件；含Alternatives（全自动化越权/全人工回老路均弃）
  2. Phase X机械验证新增【L3反哺派生检查项】验证⑩单一数字源/⑪被引用文件存在性/⑫结构画像防回声（实例化第10份沉淀的模式A/C/F，L1自动反哺首次落地）
  3. 收尾门禁③L3步补"反哺派生"验证逻辑（L1写入/ L2列待办 + 交付总结含🔄反哺报告）
  4. evaluation-framework.md L3执行规则补「反哺派生」MUST（下游闭环，不靠提醒）
  5. version 2.5.3→2.5.4；§6.6备份SKILL.md+evaluation-framework.md到记忆琥珀
- 校验：grep确认验证⑩⑪⑫已入Phase X、反哺派生段已入L3步骤与门禁、版本=2.5.4

### v2.5.3 — 2026-07-08
阶段4 收尾门禁（自进步机制从"建议"变"交付定义"）
- 根因：L3沉淀/悬置区探针/对话冲突检测三机制原定义为 post-delivery ✅DO / ☑SHOULD，无硬门禁→实测休眠（test_results 10份报告零 L3_沉淀 产物、evolution stub 未填）
- 改动（严格符合指令编写规范 v4.1 五级标注+因果链+正面建模）：
  1. 统一L3触发标准：原"≥5次"(616/622)与"5的倍数"(633)打架→全改"评估报告数达5的倍数（第5/10/15…份）"，消除歧义
  2. SKILL.md 阶段4 末尾新增「🔒 阶段4 收尾门禁（交付定义）」：三步（①悬置区探针 ②对话冲突检测管道 ③L3沉淀）为交付门禁，未执行且未记录跳过原因→禁止输出"✅ 交付完成"；每步配 Glob/脚本门禁验证
  3. 新增 `scripts/check_selfimprove_gate.py`（确定性·文件计数锚定）：输出 report_count / l3_required(count%5==0) / last_l3_date / days_since_l3，L3触发决策以脚本为准不靠AI算术——与对话冲突管道同哲学（脚本确定性，不靠AI自觉）
  4. evaluation-framework.md 三层级嵌入 L3 行"≥5次后激活"→"达5的倍数后激活"；执行规则 ☑SHOULD→🔴 MUST（交付门禁）
- 备选未选（Alternatives Considered）：①外部调度器(cron)强制每月→违背用户"不要后台静默自动"立场，弃；②仅 prose 升 MUST 不验证→AI仍可漏跑，弃；③试点单机制→门禁为共享基础设施，试点不验证其余二者集成，弃（用户定：全做）
- 备份：§6.6 备份 SKILL.md + evaluation-framework.md → 记忆琥珀/技能升级备份/
- 校验：grep 确认 L3触发描述统一为"5的倍数"；三机制均纳入收尾门禁

### v2.5.2 — 2026-07-08
固化引用重冻（instruction-standard v3.9→v4.1，消除版本告警+评分偏差）
- 根因：指令编写规范 v4.0→v4.1 反哺跨平台改造（路径硬编码分级+Poka-Yoke生成器守卫案例+批量变更逐条单列+先确归属再评估），固化副本仍停在 v3.9，阶段1.5版本检查持续⚠️告警且会把合法 tilde 路径误判为违规
- 改动（严格符合指令编写规范 v4.1 五级标注+因果链+正面建模）：
  1. instruction-standard.md 头部 version 3.9→4.1；§8.3 敏感信息补「路径硬编码分级」（tilde `~/` 安全/绝对根路径违规）；§三 Poka-Yoke 补生成器绝对路径守卫案例（防误>防错典范）；新增§十 态度元规则（先确归属再评估+自指优先）；§七自检#4 改为「无绝对根路径硬编码（tilde允许）」；footer 固化版本 v3.6→v4.1
  2. skill-arch-standard.md footer 固化版本 v5.7→v5.9（header 5.9 已与源同步，仅修正陈旧footer注释）
  3. SKILL.md dependencies 声明 instruction-standard 固化自v3.6→v4.1、skill-arch-standard 固化自v5.7→v5.9（与固化文件头一致）；version 2.5.1→2.5.2
- 备份：§6.6 备份 instruction-standard.md + skill-arch-standard.md → 记忆琥珀/技能升级备份/
- 校验：grep 确认 instruction-standard 头部版本=4.1=源；阶段1.5告警消除

### v2.5.1 — 2026-07-07
阶段3完整性锁补全：用户语言总结检查项
- 新增完整性锁检查项：`用户语言总结已输出(整体打分/得分项/待加强/建议优先处理)`
- 根因：v2.0起第552行已规定“必须输出”用户语言总结，但完整性锁未拦截→执行时漏输出
- 影响：下次评估交付时完整性锁会强制拦住未输出用户语言总结的交付
- 依赖版本对齐(固化版本)：triwich YAML 3.6.1→3.3.1、skill-arch-standard YAML 5.8→5.7，与目录索引段及triwich-integration固化声明一致（非追最新版，避免虚构"已适配"）
- 孤儿文件接线：references目录索引段补 `circuit-breaker-spec.md`(熔断器降级完整规范)、`skill_eval.py`(S级合规静态检查脚本) 两处指针，消除Phase X⑥孤立文件FAIL；两文件内容均有效(前者为熔断器权威规范/后者为可复用静态检查工具)，采用接线而非删除以保留价值

### v2.5.0 — 2026-07-07
对话冲突检测管道（来源：未知未知前置容器阶段1 · L3深度评估最终方案）
- Phase 4 新增「对话冲突检测管道」：补#1探针不跨对话的缺口（跨周期陈述一致性比对）
- 三脚本确定性执行（修复三明智L3 Agent B审查4处硬伤）：
  - `scripts/load_claim_index.py`：Phase 0从断言台账.md抽取活跃议题名列表，强制注入提取prompt（修复#4台账加载链路）
  - `scripts/append_claim.py`：Layer 1提取后调用，grep校验议题名命中+同议题立场比对+T2冲突信号输出+追加台账（修复#1空心规则）
  - 去重规则：#1已处理的议题本周期#2不重复触发（修复#3双触发）
- 监控层双轨触发：规模触发(活跃>100条)+质量触发(recall<90%提前引入embedding，与规模解耦)（修复#2验证错配）
- 断言台账：`~/个人AI档案/未知未知/断言台账.md`（新建，Markdown机器可读schema，与悬置区.md风格一致）

### v2.4.0 — 2026-07-07
悬置区探针投喂（来源：未知未知前置容器阶段1 · L3评估认定的真缺口）
- Phase 4 新增「悬置区探针投喂」步骤：评估报告归档后、推拉分离联动前，扫描本轮评估结果对照残差五类触发（T1预测失准/T2自相矛盾/T3无法归因的成败/T4跨域孤儿/T5意识到的盲区）
- 有匹配→按悬置区.md §1.6 schema 写入 `~/个人AI档案/未知未知/悬置区.md`（自下往上追加）；无匹配→跳过
- 推拉分离联动从"唯一推送点(系统日志)"升级为双推送：①系统日志(任务记录) ②悬置区(盲区信号)
- 与其他Skill关系表新增 悬置区.md 推送行
- 目标：让悬置区容器不饿死——clock-loop评估是盲区信号的自动活水来源，不依赖用户主动填

### v2.3.1 — 2026-07-06
Phase X 脱敏分支（来源：测试标准反哺 + 用户澄清"主源不脱敏/发布包必脱敏"）
- Phase X 新增【对象性质判定】：按 路径前缀 > 标志文件 > 内容特征 嗅探 object_nature（主源 | 发布包）
- 判定为发布包 → 检查集追加【验证⑨ 脱敏扫描】(FAIL级)；主源 → 跳过脱敏
- 脱敏扫描检查 /Users/<user>/ 绝对路径、真实姓名/邮箱残留，复用 开发工具/安装包测试脚本/smoke-test.sh 逻辑
- 对齐《Skill测试框架与流程指南》〇、适用范围与执行分层

### v2.3.0 — 2026-07-04
Phase X 机械验证新增（来源：skill_eval.py 整合）
- 评估路径下新增 Phase X：代码围栏闭合/YAML必填字段/NOT for子句/文件杂乱/内部链接有效/孤立文件/行数≤400
- 通过→继续评估，不通过→输出缺陷报告问"先修再评"或"带缺陷继续"
- 目标：反方向的钟成为Skill评估的唯一入口，skill_eval.py 归档

### v2.2.1 — 2026-07-04
评估待办清单闭环（来源：04-可执行实施方案.md “仍待完成”P1-P3共11项）

**P1修复**：
- Phase 3翻译段从模板占位符改成真实填充（`[分数]`等占位符 → 动态提取指令+4条DO/DON'T填充规则）
- 学习模块第5轮加转场引导（费曼验证路径A + 寓言理解路径B）

**P2修复**：
- Phase 3交付后加CTA引导（推荐1个后续动作：继续优化/换评估/学习概念/运行时验证）
- Phase 1学习进度恢复（任务类型F时检查last_learning_session，主动提示断点续学）
- Phase 1熔断器新增快速通道（用户说“你看着办/快点”时跳过5问展示）
- Phase 0前置判定区分评估/学习两大路径（任务类型F→学习路径跳过1.5）

**P3修复**：
- 6个熔断器全部加外显信号（统一格式 `⚠️ 熔断器触发:{名称}({原因}) → 降级方案:{内容}`）
- 熔断器降级文档新建（references/circuit-breaker-spec.md v1.0：总览表+外显信号表+降级链路图）
- 累计5次评估后L3沉淀执行步骤（扫描test_results/提取共性模式，5的倍数时触发）
- Hook触发器明确跳过（增强模块第二期剩余部分）

**同步修复**：
- 清理上次被打断执行产生的78行重复外显信号垃圾
- 单元测试3问题修复（4个固化引用文件补version字段、版本号对齐源文件、skill_eval.py软链接创建）

### v2.2.0 — 2026-07-04
反方向的钟Meta审计修复（来源：triwich L3独立审计 + 7样本meta分析双路确认）

**P0修复**：
- **哲学评估权重20%→15%**，释放5%给逻辑一致性15%→20%。双路审计确认：哲学评估≥85%后方差趋零，退化为固定加分，20%权重不合理
- **哲学评估及格判定**：总分≥85%→哲学及格(满分计入)；<85%→不及格(零分计入)。不再逐项加分，消除虚假区分度
- **维度去重**：A3"步骤间逻辑连贯"与C1"步骤流程无断点"重叠→A3改为产出物锁检查，C1改为端到端执行链路完整性

**P1修复**：
- **新增运行时验证检查项**：逻辑一致性维度新增"运行时验证存在（eval-set可执行/有测试覆盖声明）"——Goodhart Law防御
- **Skill类型权重微调**：current_weights.yaml新增type_adjustment（workflow+3%哲学/-3%逻辑；dialog-2%哲学/+2%逻辑；loader passthrough），消除工作流vs对话型20.3pp系统偏差
- **子Agent审查补L0防回声**：④子Agent指令新增L0三问+7种回声模式自检（格式套用/评分模式/框架套用/问题锚定/修复路径/维度偏好/结论趋同），回声命中≥3条标记低置信度

**P2修复**：
- **触顶判定**：交付时自动计算维度饱和度(≥5/6触顶)+剩余可修复空间比率(<8%触顶)+功能侧vs文档侧空间比(>3:1文档侧触顶)
- **L0补充7种回声模式示例**：见④子Agent指令

**同步更新**：
- current_weights.yaml v1.1→v1.2（权重调整+类型微调）
- skill_patterns.yaml v1.2→v1.3（去重+权重同步+类型检测+运行时验证+测试阈值5→10）
- evaluation-framework.md v1.2→v1.3（全面同步v2.2.0规则）

### v2.1.2 — 2026-07-03
评估流程三相修正（来源：三明智+读书助手+成长箱 连续3个loop实战复盘）

- **L0 结构画像（防回声）**：连续评估多对象时，在阶段2自查前插L0三问，打断"上次修的=这次也要修"的模板套用惯性。根因：成长箱评估7/11条假阳性。
- **哲学评估功能层匹配**：philosophical-evaluation.md新增功能层等价规则——反思能力/偏见觉察不再只看"自检清单"四个字，级联锁/人在回路/定值法=功能层已实装。根因：growth-box哲学评估从71.4%→100%。
- **自适应权重废弃**：adaptive_rules注释废弃，current_weights.yaml v1.0→v1.1。根因：triwich+growth-box双样本验证，自适应规则预设分类与Skill结构无关，权重偏移=噪音。

### v2.1.1 — 2026-07-03
④子Agent审查跳步修复（来源：三明智v3.6.0评估实战发现）

- 根因：自查≥85%后门禁写"下一步"，AI将自查通过脑补为可交付，跳过了④子Agent审查
- 修复1：评分门禁≥85%分支 → "强制进入④（子Agent审查），不可跳过" + ⛔DO NOT声明
- 修复2：阶段3交付前新增④执行验证锁（步序法·5项检查），任一❌则退回补执行
- 这是一次防错层补防误层的升级——从"流程描述"升级为"物理阻断"

### v2.0.6 — 2026-07-03
标准收集覆盖审计（来源：每日伙伴v3.13.0评估发现）

- 发现：task-standards.json的6条检查清单与实际评估引擎的35个检查点严重脱节
- 根因：standard-collection-template.md第②问只给"评估Skill"提供1个checkbox，用户确认的≠AI执行的
- 修复：standard-collection-template.md"评估Skill"从1条展开为6维度35子项完整清单
- 修复：skill_patterns.yaml哲学评估维度从5项补至7项（+语境理解+意义完整性）
- 新增覆盖审计表：评估体系4个来源（Skill架构规范/指令编写规范/迁理之外/三明智）→标准收集模板→评估引擎的全链路覆盖验证
- 教训：标准收集模板是用户与评估引擎的契约接口——用户看到的选项必须覆盖引擎的全部评估维度，否则"确认标准"形同虚设

### v2.0.5 — 2026-07-03
推拉分离联动方案落地

- 联动架构从第一性原理重新设计：从"6条主动推送"改为"1推4拉+1取消"
- 唯一推送点：系统日志（评估完成后自动触发记录）
- 4个拉方：成长箱/每日伙伴/Shall We Talk/最伟大的我（按需从系统日志或评估知识库拉数据）
- 取消唤醒记忆联动（固化引用模式已解决规范加载问题）
- SKILL.md"与其他Skill的关系"段重构：固化引用4个+推拉分离联动5个+不联动4个
- 阶段4新增"推拉分离联动"声明

### v2.0.4 — 2026-07-03
评估标准固化引用完成

- 新增references/skill-arch-standard.md：固化Skill架构规范v5.7核心评估标准（YAML字段+文件结构+五级标注+Poka-Yoke三法+T5对抗性11项+反模式catalog+机制选配矩阵+四层契约+Alternatives要求）
- 新增references/instruction-standard.md：固化指令编写规范v3.6核心评估标准（五级标注+因果链+Poka-Yoke+Alternatives+三级强制分级+文件类型识别+自检清单18项+安全防护+长上下文布局）
- skill_patterns.yaml v1.0→v1.1：每个check_item标注source到具体固化文件的具体段落
- evaluation-framework.md v1.1→v1.1更新：版本检查从2个固化文件扩展到4个
- SKILL.md dependencies新增：skill-arch-standard(v5.7)+instruction-standard(v3.6)，mode: reference
- SKILL.md references/目录索引更新：新增2个固化引用文件
- second_brain_links.yaml v1.0→v1.1：4个固化引用改为结构化声明（ref_file+source_path+source_version+used_for+note）

### v2.0.3 — 2026-07-03
固化引用模式上线

- 三明智方法论固化到references/triwich-integration.md（来源triwich v3.3.1）
- 迁理之外哲学标准固化到references/philosophical-evaluation.md（来源meta-aletheia v3.2.1）
- 两个references文件头部标注：来源+源头路径+引用模式+版本检查规则
- evaluation-framework.md新增Phase 0步骤5：版本检查（固化引用同步验证）
- evaluation-framework.md的Phase 2/3改为"Read本地references"而非"调用Skill"
- SKILL.md dependencies改为结构化格式（name+version+path+mode: reference）
- SKILL.md阶段2③引用描述更新：从"三明智L1嵌入"→"Read references/triwich-integration.md L1段"
- SKILL.md"与其他Skill的关系"段更新：从"协作"→"固化引用"
- 修复签名造假问题：之前声明"调用triwich/meta-aletheia Skill"实际未调用，现改为固化引用（诚实声明）

### v2.0.2 — 2026-07-03
评估产物归档规范化

- progress.md存储路径从"[当前工作目录]"改为评估知识库
- 新增评估报告自动归档机制：完成后归档为`{对象名}_{版本号}_评估报告_{日期}.md`
- 归档后progress.md删除，不残留在Skill目录
- 新增禁止行为#11：评估报告或progress.md存放在Skill目录
- 首次评估system-logger v3.5.1的progress.md已归档到评估知识库

### v2.0.1 — 2026-07-03
合规修复（skill_eval.py 98/100 S级）

- 删除README.md（规范禁止）
- 创建references/CHANGELOG.md（规范要求）
- YAML补字段：author/source/upstream/modifiable
- 清理版本号重复声明（正文→CHANGELOG.md）
- 五级标注补全（33处）
- 新增Alternatives Considered段（8项）
- 新增T5对抗性防御声明（8项）
- Poka-Yoke补定值法（内部循环3次+评分门禁85%）
- 新增standard-collection-template.md+eval-set.md
- license从Proprietary改为MIT

### v2.0.0 — 2026-07-03
从"执行型Loop"升级为"评估增强型Loop"

- 新增阶段1.5：知识网络构建（对象识别+评估模式加载+权重配置）
- 阶段2自查升级：从"对照检查清单"→"L1拆解+逐维度评分+哲学评估+L2自检"
- 新增评估知识库联动：`~/个人AI档案/评估知识库/`（patterns/weights/references/evolution）
- 新增三明智嵌入：L1拆解（评分前）+L2自检（评分后）+L3沉淀（跨周期）
- 新增哲学评估：七项哲学检查（价值对齐/认知边界/语境理解/边界伦理/反思能力/偏见觉察/意义完整性）
- dependencies新增：triwich（三明智）+meta-aletheia（迁理之外）
- 禁止行为新增#8-10：跳过知识网络/L1拆解/L2自检均禁止
- 卡死判定新增"评估Skill"任务类型
- 完整性锁新增：多维评分表+评估结果写入两条
- 评估集新增#12-13：Skill评估+知识库降级测试

references/新增3文件：
- evaluation-framework.md（评估增强框架Phase 0-3详细流程）
- philosophical-evaluation.md（七项哲学检查详细维度）
- triwich-integration.md（三明智L1/L2/L3嵌入详细说明）

### v1.2.2 — 2026-06-27
稳定版：四阶段流程+反疲劳+卡死检测+19个测试用例

- 四阶段流程：阶段0前置判定→阶段1标准收集→阶段2循环执行→阶段3终止判定→阶段4后续处理
- 子Agent双轨制：完整模式（spawn审查Agent）+NoAgent模式（自检替代）
- 反疲劳判定：同一问题连续两次不过→策略切换
- 卡死检测：子Agent连续两轮说"跟上一轮没差别"→判卡死
- 防跳步机制：步骤产出物锁+思考检查点+熔断器+完整性锁+文件异常恢复
- task-standards.json：同类任务自动复用历史标准
- progress.md：每轮执行日志持久化
- 19个测试用例覆盖应触发/不应触发/运行时行为/标准收集复用/文件异常容错
