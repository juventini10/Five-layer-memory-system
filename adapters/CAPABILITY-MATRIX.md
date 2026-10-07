<!--
⛔⛔⛔ 本文件由脚本生成 —— 请勿手改 ⛔⛔⛔

生成器：references/scripts/gen_capability_matrix.py
唯一真源：adapters/<端>/capability.yaml 的 capabilities: 段
手改会在下一次生成时被覆盖，且**不留痕迹地漂移**——这正是铁律-016 的由来。

🔴 加端/改能力 ⇒ 改 `capability.yaml`（真源），⛔ 不要改本文件。
   本文件是**派生数据**，不是数据源。

重建命令：
    python3 "references/scripts/gen_capability_matrix.py"
    python3 "references/scripts/gen_capability_matrix.py" --check   # 只验不写
-->


# 适配层能力矩阵（🔴 脚本生成·勿手改）

> ✅=端声明支持 · ❌=端声明不支持 · `—<br>无声明`=**该端没有 capability.yaml**
> （不是「不支持」，是**没测过**——两者混同会诱导端 AI 去修不存在的问题）

生成时间口径：随包内 `capability.yaml` 变化即变·⛔ 不写死日期（避免二次漂移源）

## 一、能力矩阵（`capabilities` 段 × 各端）

| 能力 | AutoClaw | 豆包办公 | Hermes | LobsterAI | Qoder CN | qwen | teleagent | Trae Work | WorkBuddy | ZCode |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| hooks 事件驱动 | ❌ | ❌ | ✅ | ❌ | ✅ | —<br>无声明 | —<br>无声明 | ❌ | ✅ | ❌ |
| 非标准钩子机制 | ✅ | ❌ | —<br>无声明 | ✅ | —<br>无声明 | —<br>无声明 | —<br>无声明 | ✅ | —<br>无声明 | ✅ |
| settings.json 注册 | ❌ | ❌ | ❌ | ❌ | ✅ | —<br>无声明 | —<br>无声明 | ❌ | ✅ | ❌ |
| rules/ 常驻文件注入 | ✅ | ❌ | ✅ | ❌ | ✅ | —<br>无声明 | —<br>无声明 | ✅ | ✅ | ❌ |
| AGENTS.md 导航 | ✅ | ❌ | ✅ | ✅ | ✅ | —<br>无声明 | —<br>无声明 | ❌ | ✅ | ✅ |
| 自定义指令 | ✅ | ✅ | ✅ | ✅ | ✅ | —<br>无声明 | —<br>无声明 | ✅ | ✅ | ✅ |
| 钩子返回值注入 | ❌ | ❌ | ✅ | ❌ | ✅ | —<br>无声明 | —<br>无声明 | ❌ | ✅ | ✅ |
| 系统提示分段注入 | —<br>无声明 | —<br>无声明 | ✅ | —<br>无声明 | —<br>无声明 | —<br>无声明 | —<br>无声明 | —<br>无声明 | —<br>无声明 | —<br>无声明 |
| 记忆支点（session 检索等） | ✅ | ❌ | ✅ | ❌ | ❌ | —<br>无声明 | —<br>无声明 | ✅ | ✅ | ❌ |
| Skill 软链 | ✅ | ❌ | ✅ | ✅ | ✅ | —<br>无声明 | —<br>无声明 | ✅ | ✅ | ✅ |
| 定时巡逻 | ✅ | ❌ | ❌ | —<br>无声明 | —<br>无声明 | —<br>无声明 | —<br>无声明 | ✅ | —<br>无声明 | —<br>无声明 |

## 二、端清单与声明状态

| 端 | capability.yaml | 能力键数 | 语义声明数 | config_root |
|---|:---:|:---:|:---:|---|
| AutoClaw | ✅ | 10 | 10 | `~/.openclaw-autoclaw` |
| 豆包办公 | ✅ | 10 | 10 | `~/.doubaowork-config` |
| Hermes | ✅ | 16 | 13 | `~/.hermes` |
| LobsterAI | ✅ | 9 | 9 | `~/Library/Application Support/LobsterAI/openclaw/state` |
| Qoder CN | ✅ | 8 | 8 | `~/.qoder-cn` |
| qwen | 🔴 **无**（未适配/未测） | 0 | 0 | `—` |
| teleagent | 🔴 **无**（未适配/未测） | 0 | 0 | `—` |
| Trae Work | ✅ | 10 | 10 | `~/.trae-cn` |
| WorkBuddy | ✅ | 9 | 8 | `~/.workbuddy` |
| ZCode | ✅ | 9 | 9 | `~/.zcode` |

## 三、缺失语义（回执判红的依据）

| 端 | required | optional | n_a |
|---|---|---|---|
| AutoClaw | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_alternative, hooks_event, launchd_patrol, settings_json, skill_symlink | — |
| 豆包办公 | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_alternative, hooks_event, launchd_patrol, settings_json, skill_symlink | — |
| Hermes | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_event, launchd_patrol, launchd_patrol_note, parity_guard, settings_json, skill_symlink, system_prompt_section, twin_section_split | — |
| LobsterAI | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_alternative, hooks_event, settings_json, skill_symlink | — |
| Qoder CN | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_event, settings_json, skill_symlink | — |
| qwen | — | — | — |
| teleagent | — | — | — |
| Trae Work | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_alternative, hooks_event, launchd_patrol, settings_json, skill_symlink | — |
| WorkBuddy | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_event, settings_json, skill_symlink | — |
| ZCode | custom_directive, rules_inject | agents_full_inject, awareness, hook_stdout_inject, hooks_alternative, hooks_event, settings_json, skill_symlink | — |

> **怎么读这张表**（端 AI）：能力项显示 `—<br>无声明` ⇒ **不要报红**，
> 去查该端是否有 `capability.yaml`；没有就说明该端**尚未适配**，
> 这本身是缺口，但**不是本端的缺陷**。
>
> 判红只认两种：① `missing_semantics` 判 `required` 却未装上 ② 组件落点缺失。
> 两者都由 `install_receipt.py` 实测产出 ⛔ 不靠本表推断。
