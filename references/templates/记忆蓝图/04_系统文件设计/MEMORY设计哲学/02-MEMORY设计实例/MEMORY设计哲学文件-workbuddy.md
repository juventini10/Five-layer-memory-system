---
title: WorkBuddy MEMORY 设计哲学（实例）
type: explanation
status: active
version: v2.2-S
date: 2026-07-10
summary: WorkBuddy 平台 MEMORY.md 设计哲学与适配
source: ~/个人AI档案/记忆蓝图/04_系统文件设计/MEMORY设计哲学/02-MEMORY设计实例/MEMORY设计哲学文件-workbuddy.md
author: 皮叔
---

# WorkBuddy MEMORY 设计哲学（实例）

> **版本**：v2.2-S → 实例化 v1.0 | **日期**：2026-07-10 | **作者**：皮叔（五层记忆系统·布洛陀版）
> **遵循规范**：`01-MEMORY设计通用规范.md`（通用规则唯一权威源，本文件仅做 WorkBuddy 平台适配）
> **关联文档**：`~/.workbuddy/MEMORY.md`（成品 v3.x）、`~/.workbuddy/SOUL.md`（品格载体）

> **适配声明**：本文件不重复通用规范中的学术基础 / 设计原则 / 战略定位 / 参考资料，仅呈现 WorkBuddy 端实测数据与平台适配。通用内容见 `01-MEMORY设计通用规范.md`。

---

## 一、WorkBuddy 端问题起源与实测

### 1.1 触发契机

2026-06-15，排查 WorkBuddy 回复格式执行不稳定时提出核心假设："如果文件在注入链条中排得靠前，LLM 注意力权重更高，执行率就会更高。" 需先回答：用户可编辑的系统文件里，谁排第一？（通用动机见 `01-MEMORY设计通用规范.md` §一）

### 1.2 注入标志法实测（🟢 直接验证）

在每个候选文件头部插入唯一注入标志，观察系统提示中的出现顺序：

```
实测注入顺序（用户可编辑文件）：
  1. MEMORY.md         ← <user_memory> 块，最先注入
  2. SOUL.md           ← <identity_context> 块，紧随其后
     IDENTITY.md
     USER.md
  3. 自定义指令         ← <user_custom_instructions> 块，第三顺位
  4. user_query        ← 用户输入，最后
```

**关键发现**：MEMORY.md 排第1，落在 U 型曲线左端高点——系统原生 `<user_memory>` 通道赋予的结构性优势。

---

## 二、平台适配要点

### 2.1 与三大文件配合（WorkBuddy 具体路径）

```
MEMORY.md ← 第1顺位（~/.workbuddy/MEMORY.md）
  ↓ 指向
SOUL.md（~/.workbuddy/SOUL.md）← 品格引擎 + 完整回复格式
  ↓ 指向
IDENTITY.md / USER.md（~/.workbuddy/）← 身份锚点 + 用户档案
  ↓ 指向
自定义指令 ← 执行准则
  ↓ 指向
铁律版 ← 按需读取（MEMORY.md 硬路牌仅放铁律骨架，008/009 已内置）
```

### 2.2 第一顺位实证（WorkBuddy 实例）

- 触发开关（如 skill-lookup 指令）在复杂任务启动时确实被优先读取——首因效应实证支持（通用原理见 `01-MEMORY设计通用规范.md` §五）。
- 硬指令（"意图分类跳过=回复不完整"）在第一顺位 + 硬约束下执行率最强；软指令（"自动运行 skill-lookup"）大半不跑。

### 2.3 不放的内容（WorkBuddy 落地）

格式模板 → SOUL.md「我怎么产出」段；完整铁律 → 铁律版按需读取（MEMORY.md 硬路牌仅放骨架）。自举悖论修正（2026-06-22）：无骨架→AI 不知有哪些铁律→永不触发 Read→细则成死数据；路由级→系统级升级消除判断空间（详见通用规范 §4.3 / §5.3）。

---

> **适配结论**：WorkBuddy 的 `<user_memory>` 独立通道使 MEMORY.md 排第1，是五产品中位置优势最强者。通用战略定位、两层模型、设计原则均完全适用，无平台特有偏离。

> **最后更新**：2026-07-10（基于 v2.2-S 实例化处理）
