# ZCode 端适配器（布洛陀 2.0 全平台安装包 · 10 端一包）

> 本目录 = 布洛陀 2.0 全平台安装包的 **ZCode 端适配器**（2026-09-26 融入自 ZCode 加强包 v0.1.1·脚本同源）。
> ZCode = Z.AI 交互式编程助手。macOS / Linux / Windows 全平台支持。

## 它做什么

把 ZCode 接到你已装好的布洛陀五层记忆系统（增量安全·不重装、不覆盖用户文件）：

- `~/.zcode/AGENTS.md` 注入文件骨架（ZCode 唯一常驻注入通道·实体存在则不覆盖）
- 9 个记忆 Skill 软链（`~/.zcode/skills/`·放置即发现·平台内置 Skill 不碰）
- 未知未知路由 Stop 钩子（脚本 → `~/.zcode/hooks/` + 幂等注册 `~/.zcode/cli/config.json`·`hooks.enabled` 缺失才补 true）
- 数据清理（SHA256 精准删除开发样例·用户记录不动·自动备份）+ 体检成就系统/记忆琥珀（缺则指路）

## 怎么装

1. **先完成布洛陀基础安装**：把整个安装包丢给 ZCode 对话框说「读取安装包，执行安装」——AI 按 INSTALL.md 走（含 33 题建档）。
2. ZCode 端注入由安装流程自动委派本目录 `setup.sh`（Windows: `setup.ps1`）；也可手动跑：
   - macOS / Linux：`bash adapters/zcode/setup.sh`
   - Windows：`powershell -ExecutionPolicy Bypass -File adapters/zcode/setup.ps1`
3. 验收：`bash verify.sh`（本目录·FAIL=0 即过）；或新开 ZCode 会话——回复应带【意图分类】开头、署名 `—— 你的 ZCode 🧩`；说「我美吗」测记忆唤醒、「小美」测轻量模式。

## ZCode 端机制速查（与 WorkBuddy/AutoClaw 等端不同·实测口径）

| 机制 | ZCode 实况 |
|------|------|
| 注入 | 单文件 `~/.zcode/AGENTS.md` 常驻；`~/.zcode/MEMORY.md` 实测不注入；`rules/*.md` 无 alwaysApply 语义 |
| 配置 | `~/.zcode/cli/config.json`（hooks+plugins）；**config-file hooks 默认禁用，必须 `hooks.enabled:true`**（脚本自动补·不覆盖显式关闭） |
| Skills | 软链目录 `~/.zcode/skills/` 放置即发现，无 entries 开关 |
| 钩子事件 | 恰 7 个：SessionStart / UserPromptSubmit / PreToolUse / PermissionRequest / PostToolUse / PostToolUseFailure / Stop；matcher 大小写敏感正则；command 钩子 `timeout` 单位=秒 |
| UPS 注入 | stdout 必须严格 JSON `{"additionalContext": ...}`，纯文本被静默丢弃 |
| 署名 | `—— 你的 ZCode 🧩` |

## 脱敏与数据清理

- 本目录资产随包过**脱敏门禁**：`bash privacy/desensitize-guard.sh adapters/zcode` = 0 残留（真实路径/用户名/邮箱字面量一律报红）。
- 安装第 2 步数据清理不可跳过：按 SHA256 指纹精准删除开发阶段遗留样例块，用户自录条目完整保留，原文件自动备份 `.pre-decontam.bak`。

## 边界（本适配器不装什么）

- **知识库/知识联邦引擎**：作者个人进阶生态，不随包分发、不注册其钩子。
- **数字分身**：规格书/切片/守卫脚本一律不进包（个人态边界）。
- 以上若你已在其他端自建，本适配器接入不会触碰或删除它们。

## 沙盒测试（维护者）

```bash
ZCODE_HOME=/tmp/fake_zcode MEMORY_CENTER=/tmp/fake_mc bash setup.sh   # 可重复跑·不碰真机
ZCODE_HOME=/tmp/fake_zcode MEMORY_CENTER=/tmp/fake_mc bash verify.sh
```
