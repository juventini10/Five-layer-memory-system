# 证据档位映射表（C01·X级主体·v4.0.0）

> **用途**：运行时验证证据 → EVIDENCE_LADDER 档位的机械映射判据（skill_eval.py evidence 区消费）
> **判据唯一源**：本文件（证据提取判据立法）+ `skill-arch-standard.md` §2.2a 登记表
> **消费方**：`scripts/evidence_extractor.py`（唯一实现·⛔判据改动须双处同步）
> **背景**：X级判级论证六点闭合（#227）——采集端已就位（full-flow.md:384 异常留痕规则·2026-08-08 设计"验证数据自动采集"）+ 数据已存在（系统日志 759 行含实跑/实测/冒烟）+ 消费端接口已预留 38 天（upgrade_refs）→ 本表=中间缺失的映射线。

## 一、证据源分级

| 来源 | 防伪强度 | 档位贡献 | 说明 |
|------|---------|---------|------|
| 系统日志（`~/[记忆共享中心]/工作日志/系统日志/`） | 强（full-flow:384 留痕规则·设计采集点·逐日归档） | **exercised** | 含"实跑/实测"+完成态+具体数字 的记录行（三段式 验证/来源/置信度 为典型形态） |
| 归档报告 sealed+sha8 重算验证（`~/[记忆共享中心]/评估知识库/test_results/`） | 强（report_sha8 防伪锚·剔离正则复用 finalize_report.py 同源·⛔不另写） | **exercised** | 报告内容含实跑+数字记录且 sha8 重算一致 |
| 归档报告 unsealed（封口块未粘贴） | 弱（#182③ 断链·篡改不可检测·第9次双盲审计 F1 实证 0/11） | ⚪ 仅统计不升档 | 计入 stats·⛔不参与 exercised 计数 |

## 二、档位映射（#227 施工单步骤1）

| 证据状态 | 档位 | ceiling |
|---------|:---:|:---:|
| 🟢A 实跑计数非推断（完成时态+具体数字+skill关联）≥1 条 | `exercised` | 94 |
| 机制已接线未跑（`references/eval-set.md` 存在 或 归档报告存在）但 0 条实跑 | `wired` | 84 |
| 仅文档声明（无运行时证据·评估器静态检查边界） | `present` | 74 |

## 三、exercised 行判据（严格·防假阳性）

1. 行含目标 skill 名（系统日志按行内 token；归档报告按文件名关联）
2. 行含完成态标记：`全绿|全过|全PASS|0 FAIL|EXIT=0|exit 0|验证通过|测试通过|实测通过|全部命中|跑通|成功通过|已实测|已验证|✅`
3. 行含具体数字（`\d+`）——⛔空口"跑过"不算
4. ⛔行含未完成态（`计划|待|拟|尚未|未进行|未跑|将实[跑测]`）→ 排除——把"计划实跑"当"已实跑"=假阳性（#227 步骤2风险）

## 四、⛔红线

- ⛔**不读运行时缓存** `.phaseX_last_run.json`（#24 实证会被反复覆盖·非不可变证据源）
- ⛔**提取器异常 → 降级 present**（⛔不因提取器 bug 虚高分数——评估器先吃自己的药）
- ⛔**档位解锁 ≠ 内容改进**——报告须显式区分（grade_note 标注"运行时证据注入·证据消费"非"内容质量提升"）
- ⛔**判据改动须同步**：本文件 + skill-arch-standard §2.2a 登记表 + 考题基线（负例三例：计划实跑不升档/无数字不升档/无skill关联不升档）

## 五、消费契约（skill_eval.py evidence 区）

```
evidence.grade        = 提取器实算档位（fallback: present）
evidence.ceiling      = EVIDENCE_LADDER[grade]
evidence.capped_score = min(raw_total, ceiling)
evidence.upgrade_refs = 证据引用列表 [{source,path,type,count,snippet}]
evidence.grade_source = 'runtime-evidence' | 'mechanism-wired' | 'static-only'
```
