---
author: 皮叔
title: Skill 模板与来源
type: reference
status: active
version: v5.8
date: 2026-07-13
summary: Skill结构模板与理论来源参考
source: ~/个人AI档案/记忆蓝图/03_开发规范/Skill架构规范/Skill模板与来源.md
---

# Skill 模板与来源

> ✍️ **作者**：皮叔
> **所属体系**：Skill架构规范 v5.8
> **本文件内容**：Skill结构模板 + 来源与参考
> **何时读**：填模板时查 / 查阅理论来源时

---

## 1. Skill结构模板

> 完整带注释版——AI按此模板填空即可生成合规SKILL.md
> 五级强制标注已嵌入模板（来源：Microsoft Azure指南）

```markdown
---
name: skill-name                    # kebab-case，max 64字符，与文件夹名一致
description: >                      # ✅DO同时包含：①做什么 ②何时用 ③排除场景
  该Skill用于[功能描述]。
  当用户提到[触发关键词/场景]时务必使用此Skill。
  NOT for [排除场景]。不适用于[不该触发的场景]。
compatibility: workbuddy, qclaw     # 声明兼容平台（攻击面声明）
allowed-tools: [Read, Write, Bash]  # 最小权限白名单
author: [作者名]
source: self-built                  # 来源：self-built/skillhub/fork/ai-generated
upstream: [路径或URL]               # 更新来源路径
modifiable: true                    # AI可修改：true/false/ask
dependencies: []                    # 依赖的其他Skill
version: "1.0.0"
---

# Skill名

## ⚠️ 铁律声明

**CRITICAL — [1-2句话核心约束]。**
**CRITICAL — 多路径Skill被触发后第一条回复必须声明当前执行的路径。**
（指令质量要求详见 `指令编写规范.md`）

## 功能定位
[一句话定义] 本Skill做[N]件事：1. xxx 2. xxx

## 触发条件
### ✅应该触发
- 用户说：[关键词列表]
- 场景：[具体场景描述]

### ⛔不应该触发
- [排除场景]

---

## 🔒 防跳步机制
本Skill使用以下机制：
- ✅ 步骤产出物锁（每步📦）
- ✅ 思考检查点（关键节点🧠）
- ✅ 熔断器（外部调用🔌）
- ✅ 完整性锁（输出前🔒）

---

## 执行流程（N步）

### 步骤1：[名称]
📦 产出物：[具体产物——可验证，⛔DO NOT写"完成分析"]
🔌 熔断器：成功=[条件] | 失败=[处理] | 重试=[N次] | 降级=[方案]
[步骤执行逻辑]

### 🧠 思考检查点
📦 产出物：五维检查清单
```
🧠 思考检查点
├─ 数据完整：
├─ 执行合规：
├─ 钩子有效：
├─ 安全合规：
└─ 预算合理：
```

### 步骤N：输出标准报告
📦 产出物：完整报告
🔒 完整性锁
- [ ] 字段1（来源：步骤X）
- [ ] 字段2（来源：步骤Y）
- [ ] 签名声称范围与实际执行步骤一致

---

## 判断标准
| 状态 | 定义 | AI怎么做 |
|:---:|------|---------|
| ✅ 正常 | [条件] | [行动] |
| 🟡 警告 | [条件] | [行动] |
| 🔴 错误 | [条件] | [行动] |

## 禁止行为
| # | ⛔DO NOT | 原因 |
|---|------|------|
| 1 | [行为] | [为什么——因果链强制] |

## 与其他Skill的关系
| Skill | 关系 | 说明 |
|-------|------|------|

## 行动倾向
[default_to_action / do_not_act_before_instructions]

---

最后更新：YYYY-MM-DD
```

### S级附加模板段

> S级Skill在上述模板基础上增加：

```markdown
## 🛡️ Poka-Yoke防误层（S级必须）
- [ ] 接触式防错：[机制描述]（来源：[Poka-Yoke接触法]）
- [ ] 定值式防错：[机制描述]（来源：[Poka-Yoke定值法]）
- [ ] 步序式防错：[机制描述]（来源：[Poka-Yoke动作步序法]）

## 📋 Alternatives Considered
| 设计决策 | 选择 | 替代方案 | 为什么不选替代 |
|---------|------|---------|--------------|
| [决策点] | [选择] | [替代] | [原因] |
```

---

## 2. 来源与参考

### 原有来源（v4.2）

| 来源 | 可靠性 | 关键贡献 | 应用 |
|------|:----:|---------|------|
| **Anthropic Skills Complete Guide** (2025-2026) | 🟢官方 | YAML frontmatter、Progressive Disclosure、description engineering、测试体系、5种模式 | 设计层全部 |
| **Anthropic Prompting Best Practices** (2026) | 🟢官方 | 四层契约、评估门禁、因果链、正面+禁令双轨、可逆性分级 | 可靠性+行为设计 |
| **OpenAI Prompt Engineering 6策略** (2025) | 🟢官方 | 清晰指令、任务拆解、思考空间、系统测试、参考文本、外部工具 | 结构+测试 |
| **OWASP LLM Top 10 + Agentic Top 10** (2025) | 🟢官方 | 提示注入、过度代理、供应链、敏感信息泄露等10维安全 | 安全十维 |
| **DAIR AI Prompt Engineering Guide** | 🟡可参考 | 18种提示技术+代理组件+风险维度目录 | 技术参考 |
| **MCP Architecture Spec** (Anthropic, 2025) | 🟢官方 | 极易构建、可组合、有限可见性、能力协商、最小权限 | 安全设计+协作 |
| **Microsoft AgentFactory** (2025) | 🟢官方 | 5种Agent设计模式（Circuit Breaker/Reflection/Multi-agent等） | 熔断器+模式目录 |
| **AgentOps Maturity Model** (2025) | 🟡可参考 | 5级成熟度框架 | 生命周期管理 |
| **IIT Gandhinagar论文** (2026) | 🟡可参考 | 多步执行准确率随步骤数指数衰减（5步61%→95步20%） | 防跳步机制 |
| **认知工程/反粉红大象效应** | 🟡可参考 | 正面约束比负面约束有效30%+ | 正面建模 |
| **唤醒记忆系统+三明智实战** (2026) | 🟡可参考 | 路径声明审计、深度认知合规返工、Poka-Yoke防错 | 全部机制的实战验证 |
| **每日伙伴 v3.9.3 实战** (2026-06-05) | 🟡可参考 | 三级级联锁+三段验证 | 执行层进阶 |
| **MEMORY设计哲学 S级报告** (2026-06-15) | 🟡可参考 | 首因效应+U型曲线+注意力预算 | 渐进披露 |
| **Liu et al. "Lost in the Middle"** (TACL 2024) | 🟢官方 | U型注意力曲线——位置决定回忆准确率 | 渐进披露学术依据 |

### 新增来源（v5.0）

| 来源 | 可靠性 | 关键贡献 | 应用 |
|------|:----:|---------|------|
| **Diátaxis文档框架** | 🟢官方 | 四象限信息架构（学习/实操/参考/理解） | 顶层架构 |
| **Google设计文档** (Malte Ubl) | 🟢官方 | Goals/Non-Goals、Alternatives Considered、约束度光谱 | Goals层+设计流程 |
| **Google API Improvement Proposals (AIPs)** | 🟢官方 | 原则先行、渐进披露、稳定性等级 | 设计原则 |
| **Microsoft Azure REST API Guidelines** | 🟢官方 | 五级强制标注（DO/SHOULD/MAY/SHOULD NOT/DO NOT） | 强制标注体系 |
| **Kubernetes KEP Template** | 🟢官方 | UNRESOLVED标记、Graduation Criteria（alpha→beta→GA） | UNRESOLVED+质量分级 |
| **Poka-Yoke防错法** (Shigeo Shingo) | 🟢官方 | 防误vs防错、三方法（接触/定值/动作步序） | 防错哲学层 |
| **Tool Engineering vs Prompt Engineering** (toutiao AI Agent研究) | 🟡可参考 | Tool Engineering > Prompt Engineering | 防误层方法论 |
| **Shall We Talk v0.6.0实战** (2026-06-28) | 🟡可参考 | 问题生成声明（设计端Poka-Yoke）→检查端→设计端范式转换 | 防误层实战验证 |
| **指令编写规范 §5.5 v3.7+** (2026-07-03) | 🟢官方 | 宪法级声明支持上下文相对性（Skill文件可加上下文级宪法声明） | §1.3 上下文级宪法声明格式依据 |

---

> **返回主文件**：`Skill架构规范.md`
