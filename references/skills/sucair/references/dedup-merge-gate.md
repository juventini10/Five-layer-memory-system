# Step 2.0 去重合并门 · 执行细则

> 定位：SKILL.md Step 2.0 的完整执行细则（SKILL.md 只留核心指令）。v4.0.0 新增。
> 来源：蒸馏扩大化方案 §5.4（借鉴 mem0 两阶段思路）+ G4 实体归一落项。
> 立法本意：书是封闭批次（一本书内部不重复），文章是开放流（10 篇讲 Agent 记忆的文章会产 10 张几乎一样的卡）。写卡前必须过此门。

## 执行步骤（按序，不可跳）

```
Step 2.0 去重合并门
  ⓪ 实体归一（G4·召回前置）：新卡草稿的 topic/tags 先做归一
     ——大小写/空格/全半角统一（"Agent 记忆"/"Agent记忆"/"agent memory" 归一为同一候选键；实测：全角空格/连字符/下划线均归一，全角字母（Ａ）不归一——与 dedup_recall.py normalize 实现一致：小写+剥空白/连字符/下划线）
     验收用例：上述三种写法必须召回同一候选集
  ① 脚本按 category + tags 交集，检索 05-知识池 已有卡片（确定性，非语义）
  ② 候选为空 → 全部 ADD，直接进 2.2
  ③ 候选非空 → AI 逐张比对新卡草稿 vs 候选卡，三选一（去重三决策；CONFLICT 立场一致性决策独立共址，见⑥·非去重第4态·2026-09-01 Loop评估#2澄清）：
       ADD    完全新概念               → 新建卡片
       MERGE  同一概念的新论据/新出处   → ⛔不新建；在原卡追加
                                          「补充来源」段 + frontmatter
                                          source_count +1，原卡 date 不动
       SKIP   同一概念且无新信息        → 不写，在本次交付里报告"已跳过 N 张（重复）"
  ④ 三种决策全部计入完成确认输出，⛔DO NOT 静默跳过——原因是静默 SKIP = 你不知道卡片没产出 = 信任损耗。SKIP 必须显式计数并列出被跳过的卡（见下方 熔断器「成功条件」）
 ⑤ SPLIT（候选卡本身塞入多个原子概念时拆为独立 ADD 候选）为 MERGE 的对称动作，按需触发不单列第四态（定义见 SKILL.md Step 2.0）——本细则不再展开
 ⑥ 立场一致性分支（CONFLICT · v2026-08-14 第一性原理落地）：本分支与 ADD/MERGE/SKIP **语义独立、机械共址**——复用 ① 已确定性召回的同一候选集，不新增检索基建。
     判定：对每张高相似候选 C_old，AI 判「新卡草稿 vs C_old 是否同域高相似 + 立场对立」（对立=新卡主张推翻/否定 C_old 核心立场；仅补充不同角度论据≠对立）。
       - 命中对立 → 决策 **CONFLICT**（⛔不是去重第4态，是独立的立场一致性决策）
       - 未命中 → 维持 ③ 的 ADD/MERGE/SKIP
     CONFLICT 落地规则：
       - 新卡写 **unverified**（⛔DO NOT 自动 verified——信任分层：机器无权裁决人类级矛盾，须人工/成长箱复核）
       - 新卡 frontmatter **复用现有 stance 扩展层**（note_validator.py STANCE_FIELDS 已定义但此前未用）：
         `stance_main_contradiction: <与 C_old 的具体对立点>` + `related: [[C_old card_id]]`（指针必填，机检守卫见 ⑦）
       - 三决议之一闭环（⛔DO NOT 仅拦截成孤儿）：
           1) **推翻**：新证据更强 → C_old 补 `stance_overturned_by: <新卡 card_id>` + 置 deprecated；新卡人工复核后补 `verified`（全复用现有字段，零新 schema）
           2) **辩证**：二者在不同语境都成立 → 两卡均 active，新卡保留 `stance_main_contradiction` + related 指针，张力作为一等立场记录保留
           3) **拒收**：新卡误/低置信 → SKIP（不写）
       - CONFLICT 决策须计入 Step 4 完成确认输出（同 SKIP 显式计数，⛔静默）
 ⑦ 机检守卫（note_validator.py v2026-08-14 落地）：`stance_main_contradiction` 非空的卡，`related` 必含≥1 指针——防孤儿矛盾声明污染知识池。复用现有字段，零新增 schema。
```

🔌 熔断器（v4.2.0 补：与 SKILL.md Step1/2/3/4 熔断器格式对齐——原 Step 2.0 细则缺此块）

├─ 成功条件：① 召回脚本跑通（命中候选集 或 输出 EMPTY）+ 新卡草稿逐张完成三决策（ADD/MERGE/SKIP·CONFLICT 独立共址见⑥非第4态）+ 各决策计数全部计入本次完成确认输出（SKIP/CONFLICT 须显式列出，不得静默）
├─ 失败处理：中止——⛔DO NOT 跳过门直接写卡（绕过门=去重失效+重复卡污染知识池）
├─ 可修正参数：category / tags 归一键 → 检查 G4 实体归一是否漏（大小写/空格/全半角[含全角空格]/连字符）；召回为空但确信有重复 → 归一键修正后重跑 `dedup_recall.py`
├─ 重试次数：1（仅限归一键修正后）
└─ 降级方案：召回脚本异常 → 回退人工全候选集比对并报告，⛔DO NOT 无门写卡

## 为什么 ① 用脚本而不是让 AI 全库扫

05-知识池 基数持续增长（执行时刻 find 实测，⛔不硬编码数字）。让 AI 读全库比对 = token 爆炸且不可靠。`category + tags` 交集检索是确定性的 BM25 式召回，脚本 20 行就能写，AI 只在小候选集上做语义判断。这就是你的「可规则化的交脚本，需判断的交模型」——防误层设计（让错误无法发生），不是事后检查。

## MERGE 是这套设计的价值点

同一个概念被 3 篇文章从 3 个角度讲过，卡片会自动积累 3 条出处（source_count=3）——这本身就是**交叉验证信号**，可以直接喂给立场层的 `stance_evidence_chain`。GitHub 上 mem0/graphiti 做的是"更新事实"，你这里做的是"加厚论据"，后者认知价值更高。

## MERGE 操作规范

- 原卡 body 追加「补充来源」段：`- {source_title}（{source_author}）：{一句话新论据}`
- frontmatter `source_count: N → N+1`；⛔DO NOT 动原卡 date/title/card_id——原因是原卡的消费端引用（日记/INDEX/wikilink）依赖这些字段稳定
- MERGE 后跑 `python scripts/note_validator.py` 对该卡机检

## 召回脚本（已建成 · 2026-08-07 Wave 3）

① 的确定性召回已实装：`scripts/dedup_recall.py <知识池根目录> --category <领域> --tags "词1,词2"`——category 归一相等且 tags 归一交集非空即候选，按命中数降序输出；无候选输出 EMPTY（=全部 ADD）。内置 G4 实体归一（小写+剥空格/连字符/下划线），兼容 YAML 行内与多行数组两种 tags 格式。验证：正例召回存量真卡✅/三变体同集✅/负例EMPTY✅。⛔DO NOT 用语义搜索替代本脚本做召回——原因是确定性召回保证可复现，语义搜索每次结果不同=去重门不可审计。
