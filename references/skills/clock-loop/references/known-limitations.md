> **来源**：外置自 SKILL.md（2026-09-04 重构·渐进式加载第三级·原文机械搬运未改一字·⛔本处不写版本号·以 SKILL.md frontmatter 为唯一真相源＝#142防漂移）
> **加载时机**：评估交付时/审计核对时Read（Known Limitation+修复闭环三分权+审查独立性+评估器自我改进包）
> **返回导航**：SKILL.md §执行流程骨架 / §references目录索引

---

**Known Limitation（已知边界·2026-07-27双盲终审落地·M3#5）**:
- 本Skill的AI判断部分(哲学检查/语义评估/子Agent审查)无外部锚点、会漂移——结论须经外部审计(常态双盲+人类终审)校准,交付物按🔧/🧠置信度分层标注
- 脚本确定性部分(skill_eval.py)可复现可信——任何人跑同一脚本得同一结果
- 自指边界:clock-loop无法在自身框架内发现"自著标准本身错了"——此为结构性事实非缺陷(你德尔第二定理),由每10份报告1次的双盲审计承接
- **修复闭环三分权(v3.14.0·P2·源=02对标§一#7-10)**：审计/评估发现的问题(finding)进入修复流程时——①修复者只能经 `scripts/record_fix.py --record` 建档(status恒pending_review·脚本无判决入口)②状态只经该writer落盘(--expected-revision乐观锁·revision不符拒写)③判决只能由**未参与修复的独立复核**(子Agent或你)经 `--review` 落盘,verdict限窄 verified|partial|blocked 三态,已判决条目拒绝二次判决。⛔DO NOT 修复交付时自写"已修复✅"入报告——原因是自写自验已被双盲第2次实锤(弱点③),状态必须走台账。**两本账**:fix_ledger只记修复状态;Skill评分是另一本账——修复verified也不改上份报告分数,评分变化等下次完整评估("同窗口修好不涨分"·防修复冲分)。复核不可用时→状态留pending_review,⛔DO NOT主体代写复核结论(宁挂账不合成)
- **审查独立性+声明纪律(v3.17.0·P4·源=02对标§一#11+12+17+22)**：阶段2步骤4审查按 `references/review-protocol.md` 执行——①信息隔离：finding系可传(标准/清单/严格度/对象/上轮问题清单)、结论系禁传(自评分数/自评结论/修复宣称/上轮通过判定)，按信息性质非字段名判定——原因是审查者见自评结论=锚定效应=双盲第2次弱点①实锤；②分权：审查Agent只产问题候选(证据+不确定性+初判严重度)，最终严重度+七态处置(采纳/合并[四同判据]/降级/证据不支持/挂起/路由×2)归lead且必须入progress.md候选处置台账——⛔DO NOT静默丢候选(QD-016制度解)；③审查报告以"⛔本证据不能支持的结论"清单收尾(≥1条)；④三层声明边界：opportunity(候选)/readiness(fix_ledger verified既有)/effectiveness(仅跨期台账有权声明)——⛔DO NOT把verified写成"改进已生效"。NoAgent降级时隔离条款失效须如实记录
- **评估器自我改进包(v3.15.0·P3·源=02对标§一#13-15)**：①**误判固化**——双盲审计实锤的skill_eval误判(假阳/假阴)必须固化为 `scripts/fixtures/BD{n}-*/` 回归样本(规则见fixtures/README.md·⛔造假案例凑数);②**改规则先跑回归**——修改任何检查项判定逻辑前后必须跑 `python3 -m unittest test_skill_eval`(含TestFixtures自动发现),结论三选一adopt/retain/rollback——原因是评估器改规则无回归=修一个洞开三个洞;③**校准台账**——每次双盲审计交付时必须向 `评估知识库/test_results/calibration_ledger.json` 追加分歧记录(机检结论vs盲审结论+根因),累积成校准曲线——原因是分歧不留档,评估器永远不知道自己系统性偏在哪

---

**Known Limitations v4.12.2 新增（R2 复审登记·⛔不假装已解决）**：
1. **合并域语义相关性不可机械判定**——结构类检查（fuse/deliverable/poka/mech_sel/poka_depth）吃"被指针引用文件"的合并文本后，装饰性堆砌（同一块复制×N）、否定式指针（⛔DO NOT Read）、稀释式（外置N块拉高密度）三形态仍得分（R2 合成实跑 +9/+10/0.92→0.95）。机械域判"特征存在"不判"内容与执行相关"；真实防线=双盲审查+D1 真阳性核对，非评分本身。
2. **pending_review 阈值语义**——门禁15 在 7-13 天窗口"汇报不阻断"系 #55 载体既定设计（给人复核窗口），非 fail-open 复发；≥14 才物理阻断。
3b′. **门禁17 复扫凭证=消费性校验，非覆盖性校验**（v4.18.0·L3反哺T2登记）：`run_id` 只证「登记表口径确实跑过且全绿」，⛔不证「登记表本身口径齐全」——新口径漏登记仍会假绿，覆盖度归 flow-C C4 的 N0 扫描域完备数；同族于 3b 的「存在性≠归属」。
3b. **门禁16 冒烟证据=存在性校验，非归属校验**（v4.12.4·R4-F-A登记）：`冒烟证据:` 路径可指向任何存在且非自指的文件——本门把「零证据/指向不存在/自指」三类纯伪造挡在门外，但挡不住「拿无关真实文件冒充」；产物归属相关性属机械域外（同§1 合并域语义局限族）。真实防线仍=双盲审查+D1 核对+门禁14取证锁。诚实措辞：门禁16 note 已改「只证存在性不证相关性」。
3a. **.phaseX_last_run.json 全局单文件跨对象互覆盖**（v4.12.3·R3-N-08登记）：机检运行时产物「最后跑谁谁说话」——跨对象复跑覆盖 target。防线=①finalize 门禁4封口时对被评对象重跑实录 ②candidate_verdict 全路径身份绑定（v4.12.2）③消费历史机检数字前必核对 target==被评对象；该文件永不可当不可变证据源（evidence_extractor L8 已明示）。
3. **calibration_ledger 归因消费节奏**——attribution 三分法（v1.1）的消费位=双盲到期时 calibration_review.py 聚合（月频·人在场），非常驻脚本自动消费；本轮分歧已入账，归因到期前显示"待归因"属设计态非断链。

---

**Known Limitations v2.9.12 注销（2026-09-27·clock-loop自评Loop R1·待办显形后落地）**：
- ~~v4.12.7"判据联动"待办：`_check` 读 task-standards.json 失败时除 ⚪ 外应升 honest 观察~~ → **已落地**：`compute_honest_pass(result, version_result, staleness_advisory=None)`——缺失/解析异常两分支升红字`标准库损坏(...)`（前提断裂≠对象侧"没法查"，N5三态不适用于评估器内脏）。**登记更正**：该待办 v4.12.7 时声称"登记入 known-limitations"但本文件从未实际登记（声称-落地脱钩·本轮评审判定=未落地的第2形态），本次补记全过程。回归护栏：TestHonestPass.test_standard_corruption_escalates / test_normal_staleness_no_flag。

