---
name: t5-defense-assessment
description: 好好学习 T5 对抗性防御攻击面5维度评估记录
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# T5 攻击面5维度评估

> 来源：Skill架构规范 v5.17 §二附B | 评估时间：2026-08-09 | 评估对象：good-good-study v0.10.0

| 维度 | 评级 | 依据 |
|---|:---:|---|
| D1 工具复杂度 | 高 | 8工具(Read/Write/Bash/Grep/Glob/WebSearch/WebFetch/Agent) |
| D2 写入权限 | 高 | Write+Bash |
| D3 交互深度 | 中 | 单轮多步(五阶段串行) |
| D4 外部内容输入 | 高 | 多源(悬置区+SHADOW+WebSearch+AI学习库+碰撞候选队列) |
| D5 产出物影响 | 高 | 写入AI学习库+回写显形台账+未知未知 |
| **攻击面评级** | **高** | D1+D2+D4+D5=高 → T5要求11项全填 |
