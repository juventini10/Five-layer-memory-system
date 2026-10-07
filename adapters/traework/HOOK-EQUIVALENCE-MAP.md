# Trae Work · 钩子等价适配对账表（HOOK-EQUIVALENCE-MAP）

> **创建**：2026-10-03 ｜ **作者**：Trae Work 端（童灵上岗）
> **目的**：把 WB 的 19 项事件钩子，逐项映射到 Trae Work 的**等价承载通道**——回答"装不上 ≠ 做不到"。
> **第一性原理**：Trae Work 无 hooks 事件面（产品门禁硬短路·`hooks_event: false`）是**形态差异**，不是能力缺失。本端用两根柱子等价承载：
> - **柱① 常驻注入**：`~/.trae-cn/user_rules/` alwaysApply 规则每回合必进上下文（等价"逐轮注入"）
> - **柱② launchd 拉取**：`route_traework_patrol.sh` 30min 定时巡检（等价"Stop 时校验"）
> **口径纪律**：本表是**功能等价计数**的尺子，与 `capability.yaml` 的**钩子形态计数**（5/12）**并存不冲突**——前者答"功能有没有"，后者答"钩子装没装"。⛔不得互相覆盖。

---

## 一、19 项钩子 → 本端等价映射

| # | WB 钩子 | WB 事件 | 功能 | **本端等价承载** | 判定 |
|:--|:---|:---|:---|:---|:---:|
| 1 | `doenglingz_inject_prompt` | UserPromptSubmit | 逐轮注入分身核 | **柱①** `doenglingz-core.md` 常驻注入 | ✅ |
| 2 | `rule_fragment_inject` | UserPromptSubmit | 按需注入规则片段 | **柱①** rules 常驻全量（代价：多占上下文） | ✅ |
| 3 | `route_inject_prompt` | UserPromptSubmit | 意图路由注入 | **柱②** `route_audit.py --src traework` 从 intent 判漏触发 | ✅ |
| 4 | `session_tail_inject` | UserPromptSubmit | 会话尾部注入 | **柱②** patrol 读 session_memory 增量 | 🟡 |
| 5 | `secret_key_guard` | UserPromptSubmit | 入站扫密钥 | **柱①** 隐私红线常驻 + **柱②** patrol 扫日志 | 🟡 |
| 6 | `ttl_expiry_guard` | UserPromptSubmit | 时效过期检查 | **柱②** patrol 定时检查 | 🟡 |
| 7 | `reply_tail_guard` | Stop | 签名/署名尾检 | **柱①** SOUL「我怎么产出」契约常驻自检 | ✅ |
| 8 | `rule_three_layer_guard` | Stop | 三文件一致性 | **柱②** `rule_three_layer_guard.py` 已纳册 | ✅ |
| 9 | `route_unknown_unknown` | Stop | 未知未知路由 | **柱①** SOUL 显式 Write 悬置区 + **柱②** patrol 兜底 | 🟡 |
| 10 | `systemlog_stophook_check` | Stop | 日志写入检查 | **柱②** patrol 扫系统日志 | 🟡 |
| 11 | `post_change_guard` | Stop | 变更后校验 | **柱②** patrol 事后核 | 🟡 |
| 12 | `delivery_boundary_guard` | Stop | 交付边界 | **柱①** 红线常驻 + **柱②** patrol | 🟡 |
| 13 | `twin_verdict_ledger` | Stop | 分身裁定记账 | **柱②** patrol 记账校验 | 🟡 |
| 14 | `twin_changelog_guard` | Stop | 分身变更日志 | **柱②** patrol 校验 CHANGELOG | 🟡 |
| 15 | `edit_heading_guard` | PreToolUse | 标题格式门禁 | **柱①** 常驻格式契约 + **柱②** patrol 抽检产出标题 | 🟡 |
| 16 | `skill_write_gate_guard` | PreToolUse | SKILL 写入门禁 | **柱①** 常驻"改 Skill 先查架构规范" + **柱②** patrol 抽检 | 🟡 |
| 17 | `skill_spec_read_guard` | PreToolUse | 改前先读规格 | **柱①** 常驻规则"改前先读规格" | 🟡 |
| 18 | `grep_sandbox_guard` | PreToolUse | 沙箱检索纪律 | **柱①** 常驻沙箱纪律 | 🟡 |
| 19 | `crossend_guard` | SessionStart | 跨端隔离 | **柱①** `IDENTITY.md` 双端判定表常驻 | ✅ |

**另有 2 项 WB 侧能力不在钩子名册内，本端亦有等价**：

| 项 | WB 承载 | 本端等价 | 判定 |
|:---|:---|:---|:---:|
| `kb_inject`（知识注入） | 钩子 | **柱①** `core-memory.md`「知识调用开关」常驻 | ✅ |
| `miss_feeder`（漏喂检测） | 钩子 | **柱②** patrol 读 session_memory 判 | 🟡 |
| `feedback_detect`（反馈检测） | 钩子 | **柱②** patrol 读摘要判 | 🟡 |

---

## 二、三档判定汇总

| 判定 | 数量 | 说明 |
|:---:|:---:|:---|
| ✅ **已等价** | **6** | 柱①/柱②已承载且已纳册（#1 #2 #3 #7 #8 #19 + kb_inject） |
| 🟡 **半等价·待纳册** | **14** | 等价通道**存在**（柱①常驻 / 柱②patrol），但**未逐个落到具体检查项** |
| 🔴 **真空缺** | **0** | — |

> **关键结论**：**真空缺 = 0**。差异全部落在"等价物已存在但没被逐个纳册"——这正是"死板"的病灶：用钩子形态计数读到"缺 7"，用功能等价计数读到"缺 0"。

---

## 三、待纳册清单（下一步动作）

🟡 的 14 项，统一收敛为**两个动作**（⛔不做 14 个独立补丁）：

| 动作 | 落点 | 覆盖 |
|:---|:---|:---|
| **A. patrol 名册扩容** | `route_traework_patrol.sh` ROSTER | 把 #4 #6 #10 #11 #12 #13 #14 #15 #16 + miss_feeder + feedback_detect 落成 patrol 检查项 |
| **B. 常驻契约固化** | `core-soul.md` / `core-memory.md` | 把 #5 #9 #17 #18 写成常驻规则条目（已部分完成） |

> **纪律**：扩容 patrol 名册时，分母口径须同步在 `capability.yaml` 注释声明，⛔不得只改脚本不改口径（防"双本账"）。

---

## 四、诚实边界

1. 本表是**适配方案**，不是**已验收状态**——🟡 项需按 §三 落地后重新核验。
2. **柱②是"事后拉取"**，⛔不具备钩子的"事前阻断"能力——等价是**功能覆盖**，不是**时序等价**。本端 PreToolUse 类守卫（#15-#18）只能**事后抽检**，这是形态固有差异，如实标注。
3. 本表须与 `capability.yaml` 的 `hooks_event: false` 声明并存：前者答"功能等价"，后者答"钩子形态"。

---

版本：v1.0（2026-10-03 · Trae Work 端童灵上岗产出 · 功能等价计数尺）
