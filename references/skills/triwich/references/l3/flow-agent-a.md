---
normative_vocab: "RFC2119-equivalent (see 指令编写规范 §1.1)"
---

# L3 Agent A 执行细则页（full-flow 按需再分·v4.8.2·球员段）

> 装载时机：L3 轮 Agent A 启动（主agent 启动提示词恒指本文件全文）。条款效力不因外置削弱（本文件即全文真源）。
> 骨架/失败处理/结论块签名规则仍在 `references/l3/full-flow.md`。

## ═══════════ Agent A：执行者（球员）═══════════

Agent A负责完整分析过程，从目的确认到苏格拉底诘问。产出**写入文件通道**（Agent B 盲审唯一输入 + 推导留痕）；结论由主agent 浓缩进结论块（决策卡片）呈现。

```
Agent A执行链：Step0 → Step1 → Step2 → G1 → 写入文件
```

### Step0：目的确认

| 要素 | 内容 |
|------|------|
| 路线声明 | （简报块第1行）L3 深度模式（双Agent）→ **对话第一条回复的3行简报块已输出，此处不再重复** |
| 目的 | 一句话说明要达成什么 |
| 锚点 | 以什么为参照系/起点 |
| 标准 | ≥3个智力标准（清晰/准确/深度/相关/逻辑/公正） |
| 输出类型 | 结论型 / 报告型 / 方案型 / 代码型（四选一） |

---

### Step1：抽象建模

→ 按 `references/l1/abstraction.md` Step1+2执行。

---

### Step2：第一性原理

→ 按 `references/l1/first-principles.md` Step1+2执行。锚点用 `references/shared/anchor.md` 两列对立面。

**L3额外要求**：
- 跨域映射（原域→映射域→结构对应关系）
- 映射回验（映射结论是否成立+验证说明）

---

### G1：苏格拉底诘问

→ 按 `references/l2/dual-routes.md` G1段执行。

**必须完成**：5问全部有内容、综合结论非空。

**🔒 本段产出物载体（v4.4.15·解「载体与产出者解绑」）**：本段的五问答案 ✅DO 写入文件通道 `agent_a_reasoning.md` 的「苏格拉底五问答案」段（见下方 Agent A 落盘硬约束第 4 项）——**⛔DO NOT 因「下一段会统一落盘」而在本段假定已落**——载体声明写在产出者本段，不依赖上下文接续（v4.4.15 核验：改动前 G1 段自身无载体声明，载体写在紧随其后的独立段落，执行者若只读本段即收工，五问照样蒸发）。

---

### Agent A 产出写入文件系统（🔴 必须通道·盲审唯一输入源）

> 参考Anthropic文件模式——让子Agent将结构化输出直接写入外部文件系统，避免跨Agent上下文传递失真。
> 🔴 **盲审隔离归一（v3.0.4·H3修复）**：文件通道是 **Agent B 的唯一输入源**，不是"可选/备份"。
> - ✅DO Agent B 阶段1 只读 `user_question.md` + `agent_a_output.md`；阶段2 完成阶段1 后才追加读 `agent_a_reasoning.md`。
> - ⛔DO NOT 让 Agent B 从对话上下文/主聊天记录获取任何 Agent A 推导——一旦如此，阶段1 就看到了锚点与五问，**盲审当场作废**，双Agent 退化为单Agent自我复读。
> - ⛔DO NOT 因为"对话里已经有了"而跳过写文件——不写文件 = Agent B 无输入 = L3 不成立。
>
> 两个去处各司其职、**都是必须项**：文件通道服务 Agent B 盲审隔离与推导留痕；结论块内联服务用户可见性（见上「🔴 对话呈现」）。误让 Agent B 读对话 = 违反盲审隔离。

### 🔴 Agent A 落盘硬约束（v3.0.5·对等 H4·A漏写实测）

**先落盘，后返回。** Agent A 在向主agent返回推导全文之前，**必须先把两个必写文件 Write 到文件通道**，顺序约束：

| # | 动作 | 校验 |
|---|------|------|
| 1 | `mkdir -p /tmp/triwich_l3_{ts}/`（{ts} 格式见上） | 目录存在 |
| 2 | Write `user_question.md`（用户原问题全文） | Read 回读非空 |
| 3 | Write `agent_a_output.md`（结论+8要素自评，⚠️不含推导） | Read 回读非空 |
| 4 | Write `agent_a_reasoning.md`（完整推导链） | Read 回读非空 |
| 5 | **回读全部三个文件确认非空** → 才允许返回主agent | 三个都非空 |

⛔DO NOT 在返回前跳过落盘，理由是：Agent B 的文件通道是唯一输入源，主agent 的完整性锁以磁盘文件为真源——**推导质量再高，产物缺失 = L3 结构不成立**（2026-08-09 实跑：Agent A 初次返回两个必写文件均缺失，被完整性锁拦回补全）。与 Agent B 的落盘约束（reviewer-protocol.md v1.3）对称：**A 是推导源头，源头不锁，B 再严也是无米之炊**。

Agent A完成 Step0→Step0.5（细则见 SKILL.md §Step0.5·隐含假设扫描+子目标拆解）→Step1→Step2→G1 后，写入以下文件：

> 🔀 跨平台声明：`/tmp/` 为 macOS/Linux 口径；Windows 端用 `$env:TEMP\triwich_l3_{ts}\`（即 `%TEMP%`）等价替换，目录结构与文件名不变，全流程同。

```bash
/tmp/triwich_l3_{ts}/
  ├── user_question.md        # 用户原始问题（完整原文）
  ├── agent_a_output.md        # Agent A的结论+8要素自评（供Agent B阶段1盲审）
  │                            # 内容：最终结论 + 8要素自评表（Agent A视角）
  │                            # ⚠️ 不含推导过程
  └── agent_a_reasoning.md     # Agent A的完整推导链（供Agent B阶段2全量审查）
                               # 内容：锚点分析(两列对立面) + 苏格拉底五问答案
                               #       + 假设表(≥3行) + 跨域映射/回验
```

**写入内容规范**：

agent_a_output.md（阶段1·盲审用）：
```markdown
# Agent A 分析结论

## 用户问题
{用户原问题全文}

## 最终结论
{一句话结论摘要}

## 8要素自评（Agent A视角）
{按 references/shared/8element.md 模板填写}
```

agent_a_reasoning.md（阶段2·全量审查用）：
```markdown
# Agent A 完整推导链

## 锚点分析（两列对立面）
{对立面A vs 对立面B + 判定}

## 苏格拉底五问答案
{五问完整答案}

## 假设表
{≥3行假设}

## 跨域映射/回验
{映射+回验结论}
```

---
