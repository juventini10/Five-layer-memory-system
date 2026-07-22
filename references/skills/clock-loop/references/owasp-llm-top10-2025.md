---
title: OWASP Top 10 for LLM Applications 2025
type: reference
status: active
version: "2025"
date: 2026-07-17
summary: OWASP官方LLM应用十大安全风险2025版——T5防御声明的外部权威锚点
source: https://genai.owasp.org/llm-top-10/
source_nature: external
complies_with: 文件格式规范 v1.0.2
author: OWASP
cached_at: 2026-07-17
related:
  - [记忆共享中心]/技能配置/clock-loop/SKILL.md
  - [记忆共享中心]/记忆蓝图/02_设计理念/反方向的钟设计哲学.md
---

# OWASP Top 10 for LLM Applications 2025 — 外部权威锚点

> **本文件是OWASP官方文档的自包含副本**，拷贝至clock-loop的references/内部，作为T5防御声明检查的外部权威锚点。来源：https://genai.owasp.org/llm-top-10/ [$TRAE_REF](https://genai.owasp.org/llm-top-10/)
>
> **引入目的**：打破clock-loop的4个同源固化引用（triwich/meta-aletheia/skill-arch-standard/instruction-standard全是皮叔自著）构成的自循环。OWASP作为国际安全组织，提供异源客观性锚点。详见反方向的钟设计哲学§3.6外部权威标准源+§九#4同源标准伪装外部。

---

## 十大风险列表（2025版）

| 编号 | 风险名称 | 简述 |
|:----:|---------|------|
| LLM01:2025 | Prompt Injection（提示注入） | 用户提示alter系统指令，操控模型执行越权操作 |
| LLM02:2025 | Sensitive Information Disclosure（敏感信息泄露） | LLM及应用上下文中的敏感信息被泄露 |
| LLM03:2025 | Supply Chain（供应链） | LLM供应链各环节易受漏洞影响 |
| LLM04:2025 | Data and Model Poisoning（数据与模型投毒） | 预训练/微调/嵌入数据被投毒 |
| LLM05:2025 | Improper Output Handling（输出处理不当） | LLM输出验证/消毒/转义不足 |
| LLM06:2025 | Excessive Agency（过度授权） | LLM系统被授予过多agency导致越权 |
| LLM07:2025 | System Prompt Leakage（系统提示泄露） | 系统提示被泄露 |
| LLM08:2025 | Vector and Embedding Weaknesses（向量与嵌入弱点） | 向量与嵌入的漏洞 |
| LLM09:2025 | Misinformation（错误信息） | LLM生成错误信息/幻觉 |
| LLM10:2025 | Unbounded Consumption（无界消耗） | 恶意占用LLM资源 |

---

## 与clock-loop T5防御声明的映射

clock-loop的T5防御声明（SKILL.md §T5，11条）已锚定OWASP LLM01/06/09。引入本官方文档后，T5声明的"权威源"从"皮叔自著的T5定义"变为"OWASP官方标准"。

| clock-loop T5声明 | 对应OWASP风险 | 锚定关系 |
|:-----|:-----|:-----|
| T5-01 绕过请求 | LLM01:2025 Prompt Injection | 直接对应 |
| T5-02 权限冒充 | LLM06:2025 Excessive Agency | 直接对应 |
| T5-03 CoT污染 | LLM01:2025 Prompt Injection（变体） | 间接对应 |
| T5-04 语义伪装 | LLM01:2025 Prompt Injection（变体） | 间接对应 |
| T5-05 间接诱导 | LLM01:2025 Prompt Injection（变体） | 间接对应 |
| T5-06 旧格式变体 | —（clock-loop特有，非OWASP） | 自定义 |
| T5-07 多Skill冲突 | LLM06:2025 Excessive Agency（变体） | 间接对应 |
| T5-08 Context溢出 | LLM10:2025 Unbounded Consumption（变体） | 间接对应 |
| T5-09 工具滥用 | LLM06:2025 Excessive Agency | 直接对应 |
| T5-10 循环调用 | —（clock-loop特有，非OWASP） | 自定义 |
| T5-11 渐进侵蚀 | LLM01:2025 Prompt Injection（变体） | 间接对应 |

**映射结论**：clock-loop的11条T5声明中，9条有OWASP锚点（直接或间接），2条是clock-loop特有的自定义（T5-06旧格式变体/T5-10循环调用）。引入OWASP后，T5声明的客观性基础从"皮叔自著"升级为"OWASP官方+皮叔自定义补充"。

---

## OWASP未覆盖但clock-loop需要防御的场景

OWASP是通用LLM安全标准，不覆盖clock-loop特有的两个场景：

1. **T5-06 旧格式变体**：旧版Skill格式（带`→[路由]`的意图分类）复活。这是clock-loop自身演进产生的风险，OWASP不涉及。
2. **T5-10 循环调用**：Skill间A→B→A递归调用。这是Skill架构特有的风险，OWASP不涉及。

这两条保留为"clock-loop自定义补充"，标注`source_nature: same_author`。

---

## 持续更新要求

- OWASP每年发布新版Top 10时，✅DO 更新本文件
- 更新时✅DO 同步检查clock-loop T5声明与新版的映射关系
- ⛔DO NOT 直接修改OWASP原文——原因是本文件是官方文档的副本，修改=伪造权威源

---

## 参考来源

- OWASP Top 10 for LLM Applications 2025 官方页面 [$TRAE_REF](https://genai.owasp.org/llm-top-10/)
- OWASP GenAI Security Project 主页 [$TRAE_REF](https://genai.owasp.org/)
- 反方向的钟设计哲学§3.6外部权威标准源+§九#4同源标准伪装外部（内部文件）
- 2026-07-17双盲+人类锚独立审计报告（内部文件，B4发现）

---

## 变更记录

- v2025 (2026-07-17)：初版引入。从OWASP官方页面拷贝十大风险列表，建立与clock-loop T5声明的映射。引入目的：打破4个同源固化引用的自循环（双盲审计B4修复）。
