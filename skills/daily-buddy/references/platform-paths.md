# 每日伙伴 — 平台路径对照表

> 本文件为 9 个 Skill 跨平台改造的**共享路径模板基准**。其余 Skill 复制此结构建同名 `references/platform-paths.md`，仅改平台专属路径值。C2 类绝对路径统一用 `{{OBSIDIAN_VAULT}}` 占位符（打包时由用户填真实值），运行时脚本读 `OBSIDIAN_VAULT` 环境变量、默认 `$HOME/Local_Obsidian_Vault`。

> 六端通用路径保持一致，仅记忆日志归档路径按平台不同。

## 共用路径（全平台一致）

| 用途 | 路径 |
|------|------|
| 日记目录 | `{{OBSIDIAN_VAULT}}/1-每日计划/01-日记/` |
| 核心启发库 | `~/Local_Obsidian_Vault/2-知识库/01-读书笔记/核心启发库.md` |
| 成就脚本 | `scripts/`（自包含于 daily-buddy Skill 目录内，运行时从 Skill 根目录调用） |
| 个人AI档案 | `[记忆共享中心]/` |
| 动态状态快照 | `[记忆共享中心]/情境层/动态状态快照.md` |
| SHADOW.md | `[记忆共享中心]/潜意识层/SHADOW.md` |

## 平台专属路径

| 平台 | 记忆归档路径 | 说明 |
|------|------|------|
| WorkBuddy | `~/.workbuddy/memory/{YYYY-MM-DD}.md` | 激活状态同时写入 `~/.workbuddy/MEMORY.md` |
| QClaw | `~/.qclaw/memory/{YYYY-MM-DD}.md` | 待确认 |
| Trae | `~/.trae/memory/{YYYY-MM-DD}.md` | |
| Trae Work | `~/.trae-solo/memory/{YYYY-MM-DD}.md` | 原名Trae Solo，路径暂不变 |
| 悟空 | `[记忆共享中心]/wukong 记忆/{YYYY-MM-DD}.md` | |
| QoderWork | 待确认 | |

## 六端署名库

| 平台 | 署名 | emoji |
|------|------|-------|
| WorkBuddy | 你的 WorkBuddy ⚡ | ⚡ |
| QClaw | 你的 QClaw 🦞 | 🦞 |
| Trae | 你的 Trae 💡 | 💡 |
| Trae Work | 你的 Trae Work 🤖 | 🤖 |
| 悟空 | 你的 悟空 🐒 | 🐒 |
| QoderWork | 你的 QoderWork 🦉 | 🦉 |
