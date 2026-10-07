---
name: t5-defense-assessment
description: T5 对抗性防御的攻击面 5 维度评估记录（SKILL.md T5 声明段的评估依据）
dependencies: []
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# T5 攻击面评估（v5.15）

> **版本**：v1.0 | **创建日期**：2026-08-08 | **来源**：自 SKILL.md T5 段外移（文档瘦身·零风险档）

## 攻击面 5 维度评估表

| 维度 | 评级 | 依据 |
|---|:---:|---|
| D1 工具复杂度 | 高 | 5工具(Read/Write/Bash/Glob/Grep) |
| D2 写入权限 | 高 | Write+Bash |
| D3 交互深度 | 高 | 多轮对话+信号触发（深度4层+双轨B介入） |
| D4 外部内容输入 | 高 | 多源（L4快照+Obsidian日记7天+SHADOW+系统日志+思维库） |
| D5 产出物影响 | 中 | 写入五层记忆+最伟大的我+知识池卡片frontmatter(质证回写) |
| **攻击面评级** | **高** | D1+D2+D3+D4=高 → T5要求11项全填 |

## 与 SKILL.md 的关系

- 本文件是 SKILL.md「安全声明(T5对抗性测试)」段的评估依据。
- 攻击面评级结论（高 → 11 项声明全填）已保留在 SKILL.md T5 段头部引用行。
- 11 项防御声明本体在主文件（已部分外置，主文件仅剩 LLM06/LLM10/ASI02 三项）。
