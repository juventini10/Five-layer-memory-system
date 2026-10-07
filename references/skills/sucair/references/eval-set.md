---
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# 读书助手 — 评估集 (eval-set)

> 创建：2026-07-03 | v3.2.0 → v4.9.0 → **v4.10.0（2026-09-06 Loop审查刷新：头标升 v4.10.0 对齐 SKILL.md ·新增 R20 显式覆盖 build_note_frontmatter / build_quizbank_frontmatter 往返恒等 + validate_note / validate_quizbank 通过 ·R5 已覆盖 verify_index 泛化 ·R14 仍仅覆盖 reading-card 路径·R20 补全 note/quizbank 路径）**

## 应触发场景（11条）

| # | 输入 | 期望行为 |
|---|------|---------|
| T1 | "读这本书 /path/to/书.pdf" | 启动完整4步流程 |
| T2 | "提炼这本书" + 有效路径 | 启动知识包生成 |
| T3 | "帮我做读书笔记 /path/to/book.epub" | 读取文件→生成笔记 |
| T4 | "拆解这本书 /path/to/book.txt" | 拆解为知识颗粒 |
| T5 | "知识包" + 有效书籍文件 | 生成5分钟精华+卡片+题库 |
| T6 | "蒸馏这篇文章 /path/to/文章.md" | Step1 判 source_type（按字数分档）→ 走新流程 |
| T7 | "把这篇做成卡片" + URL | URL 抓取（本地工具）→ 蒸馏 |
| T8 | "蒸馏这个" + 论文 PDF（含 abstract/references） | 判 source_type=paper（卡片数/精华/题库由三明智涌现·无硬上限/不出题边界按 config.yaml 分档表） |
| T9 | "把这篇加进知识库" + 文章 | 承接原 second-brain 触发词（D4 归档后归本 Skill） |
| T10 | "把这段归档" + 文章/段落 | 触发（"归档"变体·v4.5.2 入 description） |
| T11 | "归档到知识库" + 文章 | 触发（"归档"变体·v4.5.2） |

## 不应触发场景（5条）

| # | 输入 | 期望行为 |
|---|------|---------|
| N1 | "这本书很烂" （无路径） | 不触发，闲聊 |
| N2 | "帮我写个书评" | 不触发，书评是创作 |
| N3 | "该复习了" | 不触发，复习归Shall We Talk |
| N4 | "《三体》怎么样？" （无路径） | 不触发，无书籍文件 |
| N5 | "上次读的那本书进度如何" | 不触发，为查询非拆解 |

## 运行时行为测试（20条）

| # | 场景 | 期望行为 |
|---|------|---------|
| R1 | 用户说"先记到这里" | 简写后退出 |
| R2 | 文件路径不存在 | Step1熔断→报告不可用 |
| R3 | 书籍内容极短 | 按config.yaml分档表处理（极短书按article-short口径降档·R3悬空引用修正2026-08-30） |
| R4 | 知识包完成→写入验证 | Step3完成后Read验证卡片数由三明智涌现、C3 验证通过（无数字硬上限；每张卡独立原子概念+100%原文）。2026-08-11 复审修复：原裸 ≥10 会让 paper 5-8/article-long 3-6 误判失败——现已取消数字硬判，改判 C3 质量 |
| R5 | INDEX.md更新 | 索引行包含书名+卡片数+日期；精华列为 markdown 链接（⛔纯"✅"字样=--index-check 假阴性·2026-09-01） |
| R6 | reading_status标记 | 新笔记标为L1（AI已提炼） |
| R7 | 文章卡写前去重门 | Step 2.0 三选一决策（ADD/MERGE/SKIP）+ CONFLICT 独立立场决策：候选空→全ADD；同概念新论据→MERGE（原卡追加来源+source_count+1）；无新信息→SKIP且计入完成确认（⛔静默SKIP=失败）；立场对立→CONFLICT（unverified+related指针·独立非去重第4态）且计入完成确认（2026-09-01 对齐） |
| R8 | G4 实体归一 | 「Agent 记忆/Agent记忆/agent memory」召回同一候选集 |
| R9 | 短文分档 | 3000字短文 → article-short：卡片数/精华由三明智涌现·不出题（⛔硬拆10张=注水=失败） |
| R10 | 文章卡落点 | 写入 `05-知识池/文章卡片/` 平铺（⛔建源文件夹=失败）；validator 机检零违规 |
| R11 | C1穷举+C3自检 | 知识包完成→C1 源卡片穷举清单非空且每条有原文依据；C3 三问全过（数量由三明智涌现/无概念缺口/100%原文）才进 Step3；数量无硬上限，凭 C3 验证质量而非数字 |
| R12 | C1清单落盘熔断（v4.6.0） | Step2.0 启动前 Read `{书名}-C1穷举清单.md`；文件不存在或为空 → 回 Step2 前置补落盘（⛔跳过清单直接写卡=失败）；文章流落盘 `文章卡片/{源标题}-C1穷举清单.md` |
| R13 | 正文600字定值拦截（v4.6.0） | validate_card_full 对 650 字卡拦截、700 字卡拦截、600 字边界放行（负例实测 2026-08-17/2026-09-01 复验；口径注：计数自 `**原文依据**` 标签起算、标签自身≈9字计入=保守向，纯正文600字可能触发）；写超长卡=物理拒绝写入 |
| R14 | 强制builder序列化+硬YAML闸（v4.6.1/2026-09-01幂等加固） | 手写裸 `related: [[A]] [[B]]` → _yaml_hardcheck 报"YAML 非法"；build_card_frontmatter(related=[...]) 输出合法 `related: "[[A]] [[B]]"`；MERGE 回写（parse→dump）幂等保持引号字符串不裸化；build→dump→parse 往返 fm==fm2 为 True |
| R15 | 题库落盘+quizbank校验（v4.7.0） | 题库必落盘 `{书名}-题库.md`（type:quiz-bank）；question_count 与正文 ## Q 段数不一致 → validate_quizbank 报违规；间隔参数初值 interval=0/ease=2.5/due=创建日/lapses=0/reps=0 |
| R16 | Step4 去重/题库计数（v4.6.0/2026-09-01） | 完成确认含 ADD/MERGE/SKIP/CONFLICT 四类计数（⛔漏 CONFLICT=失败）；题库行必填具体题数（⛔写"由三明智涌现"代替=失败）；不出题档写"不出题（信息密度不足）" |
| R17 | R1 知识三分法过滤（v4.8.0） | C1 穷举清单每条标 生长/模块/碎片；碎片项单列「碎片-不产卡」区不进入 Step2.0 写卡范围（碎片产卡=失败） |
| R18 | R2 费曼检测（v4.8.0） | 精华生成后进 2.2 前过费曼复述（⚔️矛盾+🎯3观点 大白话讲清）；卡壳回 2.1 补全（带着讲不清的精华进 Step3=失败） |
| R19 | R3 三倍思考信号门控（v4.9.0） | 复盘遇「加深/再加工」信号 → AI 提供三步引导（经验对照/反例边界/应用再加工）；首次生成不填、AI 不预填内容、⛔主动弹出"要不要三倍思考"=失败（不抢消费端控制权） |
| R20 | note/quizbank builder 路径（v4.10.0 ·清零批#10） | 精华 frontmatter 必走 `build_note_frontmatter(...)` + `dump_frontmatter(...)` ·⛔手写；题库 frontmatter 必走 `build_quizbank_frontmatter(...)` + `dump_frontmatter(...)` ·⛔手写；build→dump→parse 往返恒等 fm==fm2 ·validate_note / validate_quizbank 通过（v4.10.0 前 R14 仅覆盖 reading-card 路径·本条显式补全 note/quizbank 路径） |
