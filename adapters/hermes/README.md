# hermes adapter · 执行准则已迁入 + 童灵端自主接入（2026-10-01）

> ⚠️ **归因订正**：本目录早期版本把 Hermes 写成「无钩子端（Trae SOLO Lite 门禁恒关）」——
> 那是 **Trae Work 的机制约束，不是 Hermes 的**。Hermes 实盘有完整钩子
> （`pre_llm_call`/`post_llm_call`/`pre_tool_call`/`on_session_end` + `register_system_prompt_section`），
> 已按**钩子端范式**完成接入，见 `rules/core-soul.md`「数字分身接入」节与
> `~/.hermes/plugins/doenglingz-twin/`（执行本体）。


> 状态：已从 WorkBuddy `personalization.customPrompt` 迁移至 Hermès 端，完成自适配（`~/.hermes/SOUL.md` 1-9 全点含个人偏好），包内脱敏评估已落盘（`execution-guidelines-脱敏评估.md`）。

## 此 adapter 对应内容

- **本地真身（含个人偏好）**：`~/.hermes/SOUL.md` §执行准则 1-9（含表格控宽个人参数：≤3列/≤20字/br折2-4行/禁横向滚动）
- **通用包版（脱敏）**：`布洛陀-全平台安装包/execution-guidelines-脱敏评估.md`（通用骨架，个人数值剥离，标注“由各端本地覆盖”）
- **签名**：`—— 你的 Hermes 🪶`

## 迁移验证

- 源：WorkBuddy `app/app-config.json` → `personalization.customPrompt`（1338 字符，9 点）
- 适配：Hermès 设计哲学 `01-注入通道规范.md` §二（SOUL.md 恒定层合并五系统文件）
- 自适配：`~/.hermes/SOUL.md` 补 8+9（原缺，已补）；签名保持 `Hermes 🪶`
- 脱敏评估：包根文件已写；无个人态数字残留；源头追溯到 SOUL.md
- 设计哲学回流：已同步 Hermès `01-注入通道规范.md`

## 使用说明

1. 安装/更新时，确保 `~/.hermes/SOUL.md` 已含执行准则 1-9（自适配完成）
2. 嗜好差异由本地 SOUL.md 覆盖；包内通用版不写死参数
3. 改 SOUL/IDENTITY/铁律版时需告知 `{称呼}`（个人识别）

---
_由 Hermes 🪶 生成 · 2026-09-22 · 基于 WorkBuddy 自定义指令脱敏迁移 · 个人偏好保留在本地 SOUL.md · 签名 `Hermes 🪶`_
