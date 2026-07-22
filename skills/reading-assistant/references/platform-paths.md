# 读书助手 — 平台路径对照表

> 本文件为 9 个 Skill 跨平台改造的**共享路径模板适配版**（基准见 daily-buddy/references/platform-paths.md）。读书助手特有路径：读书笔记 / 知识池 / 电子书目录。C2 类绝对路径统一用 `{{OBSIDIAN_VAULT}}` / `{{EBOOK_DIR}}` 占位符（打包时由用户填真实值），运行时由 `OBSIDIAN_VAULT` / `EBOOK_DIR` 环境变量解析，默认 `$HOME/Local_Obsidian_Vault` / `$HOME/电子书`。

## 共用路径（全平台一致）

| 用途 | 路径 |
|------|------|
| 读书笔记输出 | `{{OBSIDIAN_VAULT}}/2-知识库/01-读书笔记/` |
| 知识池(卡片) | `{{OBSIDIAN_VAULT}}/2-知识库/05-知识池/` |
| 知识池索引 | `{{OBSIDIAN_VAULT}}/2-知识库/05-知识池/INDEX.md` |
| 电子书目录(只读) | `{{EBOOK_DIR}}/` |
| 个人AI档案 | `[记忆共享中心]/` |

## 占位符解析约定

| 占位符 | 环境变量 | 默认值 |
|--------|---------|--------|
| `{{OBSIDIAN_VAULT}}` | `OBSIDIAN_VAULT` | `$HOME/Local_Obsidian_Vault` |
| `{{EBOOK_DIR}}` | `EBOOK_DIR` | `$HOME/电子书` |

> Windows 用户：安装后把占位符替换为自己的 Obsidian 库路径与电子书目录（或设置对应环境变量后由 Skill 运行时解析）。
