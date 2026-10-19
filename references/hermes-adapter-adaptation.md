# Hermes 端适配实证 · 机制验证参考

> **⚠️ 本文件已于 2026-10-02 全文重写。** 旧版（2026-09-30）有一处**根本性误判**：
> 它把 Trae Work 的机制约束（Trae SOLO Lite 产品门禁 ⇒ 无钩子）当成了 Hermes 的约束，
> 据此写下的「Hermes 无钩子·正确路径=恒驻注入+手动触发」全部作废。
> 2026-10-01 端自主适配已实测推翻（`adapters/hermes/rules/core-soul.md` 顶段已载纠正文）。
> ⛔ 保留本页仅为记录该次误判的**成因**，避免同类端张冠李戴再次发生。

---

## 一、已作废的错误结论（勿再引用）

| 旧版断言 | 实测反证 | 定性 |
|---|---|---|
| 「Hermes 无钩子」 | Hermes 有完整四类钩子：`pre_llm_call` / `post_llm_call` / `pre_tool_call` / `on_session_end`，经 `plugin.yaml` 的 `provides_hooks` 注册 | ❌ 把 Trae Work 的门禁当 Hermes 的 |
| 「正确路径 = 恒驻注入 + Skill 触发 + 手动调脚本」 | 正确路径 = 插件三通道：**恒驻 section + pre_llm_call 逐轮注入 + post_llm_call 守护**，全机械 | ❌ 降级方案被写成正解 |
| 「`agent-hooks.log` 十次会话 0 字节 ⇒ 无事件面」 | 那是 **Trae Work** 的日志文件；Hermes 的派发证据在 `~/.hermes/plugins/*/plugin.log` 与各守卫台账 | ❌ 跨端取证 |

### ⚠️ 追加（2026-10-02·第二层误判·同款病因复发）

上表纠正的是「**有无钩子**」。本轮又踩了它的**下一层**：「**事件名对不对**」。

布洛陀 `install_scripts.py` 的 ROSTER 对**所有端统一**登记 `PreToolUse`，
但**各端事件名体系不同**，同一份登记表在不同端含义不同：

| 端 | 工具前置事件名 | 配置文件 | 状态 |
|:---|:---|:---|:---|
| **Hermes** | **`pre_tool_call`** | `config.yaml` 的 `hooks:` 段 **或** 插件 `ctx.register_hook()` | 🔴 **无 `PreToolUse`**·ROSTER 登记项在本端**不派发** |
| WorkBuddy / Qoder CN | `PreToolUse` | `settings.json` | ✅ 真事件·真生效 |
| ZCode | `PreToolUse` | `cli/config.json` 的 `hooks.events` | ✅ 真事件（须 `enabled: true`） |

⚠️ **Hermes 端双通道**：写侧 4 守卫同时挂 ① 插件通道（`buluotuo-pretool-guards`·
事件名 `pre_tool_call`）与 ② `config.yaml` 的 `hooks:` 段（同样 `pre_tool_call`）。
`settings.json` 的 `PreToolUse` 条目 = **无效挂载**，⛔ 但**守卫本身在跑**。

**验"跑没跑"查台账**：`~/.hermes/pretool_guards_hook.log` 有无 `BLOCK` 行。
⛔ **只看 `settings.json` 会误判**（那 4 条是无效挂载，像是"没跑"）。
⛔ 只看插件也会漏（settings 那条无效条目在，但那是另一码事）——**必须双通道查**。

> **同款病因**：上次把 Trae Work 的机制当 Hermes 的，这次把 WorkBuddy 的事件名当 Hermes 的。
> **根子都是"拿别端的机制直接套过来，没查本端真值"**。
> **通用解**：新建 hook 挂点必过三门——事件名 ∈ 宿主白名单 / 写在宿主装配期真正读的文件 /
> 同意门已开；三门过后**仍须取本端运行态发射证据**才许写"已生效"。

**误判成因（可复用的教训）**：Trae 系端与 Hermes 系端在记忆蓝图里相邻，接手时未做**端自证**就沿用了邻端的实测结论。
⇒ 铁律形态：**任何"某端没有 X 机制"的断言，必须取该端自己的运行时证据**（配置文件 + 运行态日志/台账），
⛔ 邻端证据不可跨端搬运——这与铁律-016「查实盘不查看板」同源，是它的跨端版本。

---

## 二、Hermes 端机制实况（2026-10-02 实测·端自证）

| 机制 | 实况 | 证据 |
|---|---|---|
| 钩子 | ✅ 四类全在 | `~/.hermes/config.yaml` 的 `plugins.enabled` 实挂 18 个插件（2026-10-11 订正：旧记 16·capability delivered 曾漏登 `buluotuo-transform-gate` / `buluotuo-verify-gate`） |
| 恒驻注入 | ✅ `register_system_prompt_section`（每新会话冻结） | `hermes_cli/plugins.py:998` |
| 逐轮注入 | ✅ `pre_llm_call` 返回值注入**用户消息** | `agent/turn_context.py:754-777` `_collect_pre_llm_call_context` |
| 守护 | ✅ `post_llm_call` | `buluotuo-stop-hook` / `doenglingz-twin` |
| 系统文件落点 | 混合结构（**非**扁平配置根） | SOUL.md 在配置根；USER.md / MEMORY.md 在 `memories/`（`hermes_cli/doctor_state.py:234-238`）；IDENTITY.md 无载体 ⇒ 并入 SOUL.md |

⚠️ 最后一行是**形态差异不是能力缺失**——旧版把「IDENTITY.md 没有独立文件」当成缺口，
实为 Hermes 的加载设计（单一恒定位）。落点表见 `adapters/hermes/capability.yaml` 的 `system_file_paths`。

---

## 三、五系统文件「100% 适配」的判据化（2026-10-02 新增）

**问题**：2026-08-20 曾判定「五文件已 100% 实现」——该判定只验了**机制存在**（三文件被加载），
⛔ 未验**内容等价**。建语义级判据后首跑实测：**102 条语义项 / PASS 48 / 适配率 47.1%**。

| 三处硬缺口 | 修法 | 位置 |
|---|---|---|
| 顶层指令 §7「禁止改述规避」整条断档（编号 1-6,8,9；同名不同义的替身不算等价） | SOUL 补独立 §7 | `~/.hermes/SOUL.md` |
| 童灵 L1 身份骨架被插件**代码静默截断**（`_core_section` 只取 head，注释谎称「已由 SOUL 承载」） | 拆两段注册 `doenglingz.core` + `doenglingz.l1` | `adapters/hermes/plugins/doenglingz-twin/__init__.py` |
| USER.md 非同一投影（认知风格/行为画像/铁律-022/触发句/隐私红线等整节缺失） | 画像层全量重写 + SOUL §6 补铁律红线 | `~/.hermes/memories/USER.md` |

**判据（可复用范式）**：
- 语义项清单 × anchors × 修法 → 机械校验器 → **rc=0 ⇔ GAP=0 ⇔ 真 100%**
- 校验器挂在只读巡检集群（`on_session_end`），**全绿不写盘**防告警疲劳
- ⛔ **校验器必须自带负控腿并实测**：本实现有四条（内容删改 ×2 / 插件注册断言 / 清单行数自检）
- 端用户态副本：`references/scripts/hermes_wb_parity_check.py`（路径参数化 `--ref-root` / `--hermes-root` / `--slices`；
  ⛔ 清单或切片缺失 ⇒ 拒出结论，**不做「无清单即全绿」**）

---

## 四、后续同类任务直接执行列表

1. **端自证先行**：动某端适配前，先取该端自己的运行时证据（配置 + 日志/台账）——⛔ 邻端结论不可搬运。
2. 读 `adapters/hermes/capability.yaml`（`system_file_paths` / `runtime_path_keys` / `missing_semantics` 三张表是 SSOT，不复制）。
3. 改包前按 `PACKAGE-LOCK.md` 走三层防线：`package_lock.sh acquire` → 编辑 → 校验 → commit → release。
4. 同步本地真身 → 包时**先脱敏**（私人称谓/绝对路径/端专属 ID），脱敏后的包内副本才是分发物。
5. 签名格式：产出签名 → 空行 → `—— 你的 Hermes 🪶`（独占最后行，后无字）。
6. 声明「已落地」必须附**可机械复跑的判据与 rc**，⛔ 禁止只写「已实现」。

---

参考：`adapters/hermes/rules/core-soul.md`（端机制实况的端侧投影）· `adapters/hermes/capability.yaml`（落点与能力 SSOT）·
`references/scripts/hermes_wb_parity_check.py`（100% 判据校验器）· 记忆蓝图 `Hermes布洛陀设计哲学/06-100%复刻源文件清单.md`（作者侧清单本体）
