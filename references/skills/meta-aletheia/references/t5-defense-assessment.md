---
name: t5-defense-assessment
description: 迁理之外 T5 对抗性防御攻击面5维度评估记录
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# T5 攻击面5维度评估

> 来源：Skill架构规范 v5.15 §二附B | 评估时间：2026-08-09 | 评估对象：meta-aletheia v3.5.0（v3.5.1 未改攻击面五维度——维度评级沿用本评估·2026-09-01 核对）

| 维度 | 评级 | 依据 |
|---|:---:|---|
| D1 工具复杂度 | 高 | 5工具+Agent(Read/Write/Bash/Grep/Agent) |
| D2 写入权限 | 高 | Write+Bash |
| D3 交互深度 | 高 | 多轮对话+3 Agent哲学家辩论 |
| D4 外部内容输入 | 高 | 多源（用户输入+记忆文件+哲学文本） |
| D5 产出物影响 | 中 | 对话内可见+哲学报告写入 |
| **攻击面评级** | **高** | D1+D2+D3=高 → T5要求11项全填 |
