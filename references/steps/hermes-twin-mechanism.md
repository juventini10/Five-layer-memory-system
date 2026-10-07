---
描述: "Hermes 端童灵机制激活参考 — 三装载通道 + 恒驻核双段 + 档位纪律"
状态: 机制说明 · 与 adapters/hermes/capability.yaml + 插件实现一致（2026-10-03 重写）
来源: 实测对齐 doenglingz-twin/__init__.py + capability.yaml（⛔ 不再引 Trae 系门禁结论）
依据: 守卫编写规范 §二·十四「接入不拥有」· 06-跨端适配规范 §1.6 D档位声明
---

# Hermes 端童灵机制激活（端 AI 执行参考）

> **身份声明（D 档位，每回合按 06 §1.6 声明）**：工具名 Hermes，署名 `—— 你的 Hermes 🪶`。
> **本端装载形态 = 插件通道（三通道），⛔ 不是「无钩子端」。**

## 〇、🔴 2026-10-03 重写声明（为什么旧版整段作废）

| 项 | 旧版写法 | 实况（`adapters/hermes/capability.yaml` + 插件源码） |
|:---|:---|:---|
| 钩子机制 | 「本端无运行时钩子（Trae SOLO Lite 门禁恒关）」 | **错**。本端 16 个插件经 `plugin.yaml` 的 `provides_hooks` 注册，事件面 = `pre_llm_call` / `post_llm_call` / `pre_tool_call` / `on_session_end` / `UserPromptSubmit` / `Stop` |
| 混淆源 | 把 **Trae SOLO Lite 的 hooks 门禁**结论搬到了 Hermes 端 | 两端是不同产品：Trae 系的门禁结论 ⛔ 不可外推到 Hermes |
| 后果 | 端 AI 读到本文件 ⇒ 得出「Hermes 没钩子·只能手动触发」⇒ **主动放弃已装的自动能力** | 装完的 16 插件被当成摆设 |

> **判据沉淀**：**跨端结论不可搬运**。能力面判据只能来自「本端 capability.yaml + 本端插件源码」，
> ⛔ 不得引用他端门禁/机制结论作本端依据（与 12 号协议 §5.8「⛔ 跨端边界」同源）。

---

## 一、三装载通道（装载分态 · 内核不分端）

| 通道 | Hermes 机制 | 承载什么 | 落在哪 |
|:--|:---|:---|:---|
| ① **恒驻核** | `register_system_prompt_section(id, callable, position="after_memory")` | `doenglingz.core`（愿景判据+品格底色+三步+非职能域+零问题红线+L6 反向约束）<br>`doenglingz.l1`（身份骨架全段） | `adapters/hermes/plugins/doenglingz-twin/__init__.py` |
| ② **W1/W3 注入** | `pre_llm_call`（返回值注入**用户消息**，逐轮） | 上岗契约 W1 + 域切片按需注入 W3 | 同上 `_pre_llm_call` |
| ③ **守护/收尾** | `post_llm_call`（每轮 LLM 输出后，带 `assistant_response`） | 守护三查 + W1 兑现对账 + 指针卡漂移探针 + TSL 收尾 + TSL 树产出 | 同上 `_post_llm_call` |

⚠️ **恒驻核为什么必须拆两段**（⛔ 不可合回一段）：
`register_system_prompt_section` 的 `max_chars` **硬上限 4000**
（`hermes_cli/plugins_dispatch.py:69-70`），而 `core_slice.md` 全文超 4000。
⛔ 首版单段注册且只取 `head` ⇒ **L1 身份骨架整段静默丢弃**（假绿根因之一）。
⇒ 现按 `doenglingz.core` / `doenglingz.l1` 两段注册，各段预算 3800。

---

## 二、本端能力面（判据源 = capability.yaml · ⛔ 不凭印象）

| 键 | 值 | 依据 |
|:---|:---|:---|
| `hooks_event` | ✅ true | `plugin.yaml` 的 `provides_hooks` 机制 |
| `hook_stdout_inject` | ✅ true | `pre_llm_call` 返回值注入用户消息（`agent/turn_context.py:754-777`） |
| `system_prompt_section` | ✅ true | `register_system_prompt_section`（`hermes_cli/plugins.py:998`） |
| `skill_symlink` | ✅ true | `~/.hermes/skills/` → `<记忆中心>/技能配置/` |
| `launchd_patrol` | ❌ false | 本端无 launchd；定时能力走内置 `cronjob` |
| `settings_json` | ❌ false | 形态差异（本端用 `plugin.yaml`），**非能力缺失** |

⚠️ **`launchd_patrol=false` 与 `hooks_event=true` 不矛盾**：前者只说「没有 launchd 巡逻」，
后者说「有事件派发面」。**不可由前者推后者为假**（旧版正犯此错）。

---

## 三、档位纪律（06 §1.6 · ⛔ 每回合必须守）

| 档 | 何时 | 产物义务 |
|:--|:---|:---|
| **D1** | 常态（人格基底常驻） | 声明 D1 ⛔ **不产 TSL 树** |
| **D2** | 命中域切片、按需加载 | 声明 D2 ⛔ 不产树 |
| **D3** | 上岗激活（执行童灵职能） | 声明 D3 + **必须 relay Stop 钩子产出的 TSL 树原文** |

🔴 **TSL 树的三条硬纪律**：
1. 树由 `tsl_tree_hook`（`post_llm_call`）机械产出到本端树槽
   `~/.hermes/doenglingz/tsl_last_tree.md` —— **AI 不得自行运行 `tsl_verify.py` 产树**。
2. relay 时**逐行贴原文**：⛔ 不得改写/摘要/指针化/手绘/换一棵更绿的树。
3. **只呈现一次**（回复末段）。⚠️ 本端 `pre_llm_call` 的 **TSL echo 通道已停用**
   （2026-10-02·用户两次报障后裁决：同一棵树在消息与回复各出现一次 = 重复刷屏）。

---

## 四、装完自检（⛔ 协议是规范，不是实况）

**先 `cat` 回执，再下结论**：

```bash
cat ~/.hermes/doenglingz/installed_manifest.json
```

| verdict | 怎么说 |
|:---|:---|
| `ok` | 「装好了，能力齐全」+ 从 `capabilities[].status` 列能力（⛔ 不凭印象） |
| `degraded` | 「能用，但少了这几样」+ 逐条列 `degraded` / `missing(optional)` |
| `failed` | 「⛔ 没装好」+ 逐条列 required 缺失与组件缺失 |

⛔ **回执不存在 ⇒ 报「本端未装/未实证」**，⛔ 不得凭空造一份（12 号协议 §2.3）。
⛔ **「哪些能力没装上」只能取 `capabilities[].status`**，⛔ 不从 `CAPABILITY-MATRIX.md` 推断（派生数据·会漂）。

---

## 五、⚠️ 已知缺口（如实登记·不粉饰）

| 缺口 | 现状 | 影响 |
|:---|:---|:---|
| 恒驻核**内容面**依赖用户造芯 | `core_slice.md` / `L6_反向约束.md` 是**用户数据**（33 题 → `k2_slice_generator` 生成），**不在包内** | 新用户装完插件在位，但**恒驻核两段读不到切片 ⇒ 返回空串 ⇒ 童灵人格未注入**（非故障，是「未造芯」态） |
| 知识卡池 | 卡池内容不入包（只发引擎 min 版 9 件） | 新用户 `search_kb` **检索源为空** ⇒ 引擎在、库空 |
| `parity_guard` | 语义登记，清单本体属作者资产、不分发 | 「五系统文件 100% 适配」在用户机无本地判据可跑 |
| USER.md 字符预算 | 本端默认 `user_char_limit=1375`（`hermes_cli/config_defaults.py:1321-1322`） | 画像层写满会触限 ⇒ 需用户自行放宽 `~/.hermes/config.yaml` 的 memory 段（⛔ 改后需重启 Hermes） |

> **诚实边界**：以上四条都是**如实边界**，⛔ 不得写成「已完整支持」。

---

## 变更记录

- **2026-10-03（v2）· 全文重写**：作废旧版「本端无运行时钩子」的错误结论。
  实测对齐 `adapters/hermes/capability.yaml`（`hooks_event`/`hook_stdout_inject`/`system_prompt_section` 三项 true）
  与 `doenglingz-twin` 插件三通道实现；补恒驻核双段必拆的 `max_chars=4000` 依据、
  档位纪律与 TSL 树三条硬纪律、回执自检口径、**已知缺口如实登记**。
  ⚠️ 旧版的病根 = **跨端结论搬运**（拿 Trae 系门禁结论当 Hermes 结论）⇒ 已立判据防复发。