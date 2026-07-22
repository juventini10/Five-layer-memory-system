# CHANGELOG

### v3.17.2 — 2026-07-18
Skill 自包含化——成就脚本移入 Skill 目录（用户只装 daily-buddy 即可跑全流程）：
- `scripts/` 新增：`achievement_tracker.py`（63KB）+ `update_diary_achievement.py`（7KB），从 `[记忆共享中心]/成就系统/scripts/` 拷贝。
- `SKILL.md` frontmatter dependencies 更新：`[记忆共享中心]/成就系统/scripts/achievement_tracker.py` → `scripts/achievement_tracker.py, scripts/update_diary_achievement.py`。
- `references/platform-paths.md`：成就脚本路径改为 `scripts/`（自包含）。
- `scripts/update_diary_achievement.py` L137：内部引用 `achievement_tracker.py` 改为 `Path(__file__).parent / "achievement_tracker.py"`（兄弟引用，不再依赖外部 ACHIEVEMENT_DIR）。
- `references/monthly-review-sop.md` L141：断言台账监控回看增加前提2——clock-loop 未安装则跳过并标注（避免月报因缺失跨 Skill 脚本而中断）。

### v3.17.1 — 2026-07-18
次日骨架生成机制从"AI 手动 Write"改为"脚本自动写盘·静默副作用"（用户零负担原则）：
- `scripts/create_skeleton.py`：新增 `--out` 参数，直接写盘（幂等——文件已存在则跳过）；不传 `--out` 兼容旧 stdout 用法。
- `references/工作流C-晚间复盘.md`：步骤6.1 改为 `--out` 一条命令自动写盘 + 删步骤7回读锁 + 弱化步骤6系统级升声明。
- `SKILL.md`：删完整性锁中"次日骨架已建且Read回验通过"句（防错→防误）；工作流C入口加"次日骨架·静默副作用"规则。
- 根因根治：原 `create_skeleton.py` 只 print 不写盘，漏建由 AI 误把 stdout 当副作用触发；现脚本直接写盘后，骨架作为写日记的自然副产品产生，无法遗漏。

### v3.17.0 — 2026-07-18
灵感闪现过载根治 + 步骤6跳过防护升系统级（两批功能级改动合并入账）：
- 灵感闪现无库回退修复（scripts/create_skeleton.py）：`load_quote_pool` 原误读缓存键 `daily_quotes`（仅6条稀疏按日期填充），改为主读 `quote_library`（123条随包名言池）；新增14天防重复（`get_recent_quotes` 扫近14天日记灵感闪现）、按日期 md5 确定性轮换（`rotate_pick`）、关键词优先匹配（`select_inspiration`）。无个人库用户现能按昨日日记关键词匹配随包名言池、14天不重复、跨天铺开——回退机制从形同虚设变真正可用。
- 4处文档一致化（diary-template.md L81 / 工具与参考.md L18 / create_skeleton.py docstring / 工作流C-晚间复盘.md L26）：统一描述"有库用库、无库回退 daily_quotes_cache.json 名言池"，消除旧"grep核心启发库"单一描述。
- 步骤6硬防护（B方案·路由级升系统级）：工作流C 步骤6头部+6.1 加不可跳过系统级硬约束 + 幂等 guard；步骤7校验锁显式"对所有日期一视同仁·⛔DO NOT 以日期已过降级"；SKILL.md L372 完整性锁扩写为"次日骨架已建且 Read 回验通过（无论复盘哪天/追溯均适用·⛔DO NOT 以日期已过豁免）"。根因=AI 自创"日期已过"豁免的判断空间被路由级升系统级剥夺。

### v3.16.5 — 2026-07-16
未知未知自包含写入改造（开源自包含·规则A·不依赖反方向的钟先跑）：
- `references/工作流C-晚间复盘.md` L79-89：第2条写入悬置区前新增「确认文件夹+悬置区.md 存在，否则按 `references/unknown-unknown-headers.md`「悬置区模板」Write 创建（含表头）再追加」+ `⛔DO NOT 直接写不存在文件`
- `references/monthly-review-sop.md`：L126-129 两处「不存在则跳过」→「按模板 Write 创建含表头再继续」（悬置区/断言台账）；L138 显形台账写入前加「不存在则按模板创建」；L141「不存在则本步跳过」→「不存在则跳过并月报标注『断言台账未启用』」保留跳过逻辑
- `SKILL.md`：在「禁止行为」前插入「🌀 未知未知写入前置（自包含引导）」段，说明工作流C 3.9 写悬置区、月报SOP 1.6 写显形台账，两处均内置「文件夹+三文件不存在则按模板自建」引导
- 新增 `references/unknown-unknown-headers.md`（三模板自包含副本）

### v3.16.4 — 2026-07-13
+ 月报蒸馏第5步：月报教训滚动覆盖机制(旧"保留最近3个月"→"保留最近1个月+沉淀检查")——月报时检查上月教训是否已沉淀到铁律版/MEMORY，已沉淀直接覆盖，未沉淀先升格再覆盖

### v3.16.3 — 2026-07-12
+ Clock Loop v2.9.3 按 v5.15 标准重评估（通用6项全PASS + DB专属9项全PASS + 上次3条P0修复核验真修）：修文件指针表CHANGELOG描述标签滞后(v3.11→v3.14→v3.16)，消除E6声明滞后gap。评估结论：通过（A级→S级门槛）。

### v3.16.2 — 2026-07-12
+ 正文开头格式改造（v5.15 §1.6）：删除作者署名行+创建日期/更新日期描述，新增设计哲学行+CHANGELOG指向。459→458行
+ T5攻击面5维度评估落地（v5.15 §二附B）：新增评估表（D1高/D2高/D3低/D4高/D5高→攻击面高→T5要求11项全填）。458→469行

### v3.16.1 — 2026-07-10
+§4.3 熔断器合规改造：3个熔断器按新规范重写（外部调用→全量五字段/内部校验→简量三字段）。配合 Skill标准规范§4.3约束式重写（2026-07-10用户确认闭环防回归）

### v3.16.0
- 设计端防误——工作流C新增步骤7.5「快照每日情境刷新」。快照CONTEXTUAL层（睡眠/能量/SHADOW）和META层（最近变更摘要/核心文件健康）此前仅在唤醒记忆系统全量模式步骤3c更新（偶发→六天空窗），现改为每晚间复盘必然写入3个子步骤（7.5a刷新CONTEXTUAL层、7.5b追加最近变更摘要行、7.5c刷新核心文件天数）+校验锁（来源：2026-07-10轻量唤醒读到7/5过期数据的根因修复）。

### v3.15.11
- Clock Loop v2.6.0评估修复：3处声明滞后gap。①工作流C-晚间复盘.md步骤7上步校验锁引用'回溯执行步骤6b'→'步骤6'（v3.15.10合并6a/6b时漏改）；②SKILL.md文件指针表'含6a/6b拆分'→'含步骤6合并'；③eval-set.md声明'18条'→'19条'（新增第19条月报自画像测试时未同步头部声明）。评估得分84.38→87.78（A级通过）。

### v3.15.10
- 接触法防误·消除跳步：步骤6a/6b合并为一个不可拆分的"伙伴建议+次日骨架"步骤。伙伴建议必须包含对脚本生成的灵感闪现的情境呼应（用今日实际内容赋温），物理上需要先建骨架、再读灵感、后写建议——骨架不存则建议写不出。根因：v3.15.0拆6a/6b后AI频繁在6a后心理"结束"，不到6b；接触法把"立交桥"建在产出物依赖上而非检查点上。

### v3.15.9
- 为通过 validate 硬门禁补建 references/CHANGELOG.md（版本记录须置于 references/ 下）；日常迭代历史见 SKILL.md 内联 `> **vX变更**` 注释。
