> **来源**：外置自 SKILL.md（2026-09-04 重构·渐进式加载第三级·原文机械搬运未改一字·⛔本处不写版本号·以 SKILL.md frontmatter 为唯一真相源＝#142防漂移）
> **加载时机**：阶段2多维评分时Read（评估示例+置信度分层🔧🧠+证据档位五档天花板）
> **返回导航**：SKILL.md §执行流程骨架 / §references目录索引

---

**v2.0评估示例:**
```
循环 评估这个Skill
→ 阶段1:收集标准(任务类型=评估Skill/检查清单/严格度/轮次)
→ 阶段1.5:加载skill_patterns.yaml + current_weights.yaml
→ 阶段2:
  L1拆解:核心功能/依赖/输出/核心矛盾
  逐维度评分(6个宏观维度→19个微观检查项＝len(WEIGHTS)·v4.12.2随实盘，详见skill_eval.py的MACRO_DIMENSIONS映射表):
    开发规范19%+指令准确性21%+逻辑一致性29%+文档完整性14%+测试覆盖7%+哲学评估10%（v4.12.2随双源实值·旧数系规范v5.16.0改权前快照未注明=E6残留）
    [v2.8.8]宏观声明权重=下属微观维度WEIGHTS之和/100，由verify_dimension_consistency()启动时自检
    [v3.0.0]置信度分层标注——每个维度标注🔧脚本确定性/🧠AI判断（见下表）
  L2自检:锚点对立面/证据链/假设验证/结论块门禁锁
→ 阶段3:交付结果+执行履历+评分表
```

**置信度分层标注表（v3.0.0新增·B2/Q4-2修复）:**

> 评估结果必须区分"脚本确定性检查"（可复现、不漂移）与"AI语义判断"（会漂移、有偏差风险）。交付物中每个维度须标注置信度层级。

| 置信度 | 含义 | 包含的微观检查项 | 可靠性 |
|:------:|:-----|:-----|:------:|
| 🔧 脚本确定性 | 纯算术/字符串/文件系统状态，可复现不漂移（代表性清单，非 20 微观项精确枚举） | version_single_source, version_uniform, single_number_source, cross_file_consistency, internal_links, file_clutter, token_budget, eval_set_gate, trigger_coverage, path_safety, backup_gate, fuse_mechanism, layering, attack_surface, l1_l2_substance（T5声明条目计数由attack_t5检查承担·其"声明实效"语义判断归🧠行——2026-09-02消解双行列同名冲突） | 🟢高 |
| 🧠 AI判断 | 需语义理解，会受上下文/模型版本影响 | yaml_required(字段语义), causal_chain(原因质量), poka_yoke(设计质量), binary_annotations(标注合理性), t5_adversarial(声明实效), mechanism_selection(选配合理性), 哲学评估, Alternatives质量 | 🟡中 |

✅DO 在评分表每行末尾标注 `🔧` 或 `🧠`。⛔DO NOT 把AI判断项与脚本确定性项混在一起不加区分——原因是你需要知道哪些分数可靠、哪些有偏差风险。

**证据档位与评分天花板（v3.13.0·P1证据状态学·源=02对标§一#1-6）**：
- skill_eval输出 `evidence` 区：`grade`（本次评估证据档）+`ceiling`（该档分数天花板）+`raw_total`与`capped_score`**并列**（raw保历史可比·capped为诚实上限）+`per_check_reason`（每项理由码三分：checked-clean/candidate-found/**not-evaluable-missing-***——"没查""查了没事""没法查"三态永久可区分·v3.16.0）+`posture`（≥2项不可查→**evidence-limited**：报告措辞必须降档⛔说"全部通过"——优点不得均值掩盖未验证项）
- 五档天花板：missing/unobserved/na≤59 · **present≤74（skill_eval静态检查的证据边界——全部20项只能证明"机制声明存在且内容合格"）** · wired≤84 · exercised≤94 · outcome-supported=100
- ⛔DO NOT 把capped_score当"扣分"申诉——原因是它不是惩罚，是证据边界的如实声明："文档写得好"最多证明present档，实测跑过才配94（五档原则即本文件第35行五档天花板·历史溯源=agent-work-loop.md（已不存在·2026-09-05 A24标注死引用＝#182）→02-better-harness深读对标·evaluator先吃自己的药：clock-loop自评raw 95/capped 74·present档[来源: .phaseX_last_run.json 2026-09-02实录·每次自评后刷新（运行时缓存）；**不可变证据源=归档评估报告（report_sha8防伪锚·2026-09-05批6h补＝#182③）**]）
- 升档接口：`upgrade_refs` 注入运行时证据（eval-set真跑记录/负例实测·P3接线）后grade方可上调

---
