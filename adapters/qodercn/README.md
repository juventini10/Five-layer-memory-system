# Qoder CN Adapter

## 安装流程（Step0 选 qodercn 后·2026-10-03 机械委派化）

主链 = `python3 install_scripts.py --platform qodercn "<记忆共享中心>"`，安装器自动委派 `setup.sh`
（install_entry·条文13扩展：hooks_event=true 端同样统一委派）+ 注册标准钩子 + 装公共资产。
端 AI 人工面只剩不可机械部分：问卷后把 {称呼} 等占位符填入 core-user/AGENTS 占位符。

| 步骤 | 承接方 | 内容 |
|:---|:---|:---|
| 1 | setup.sh | 检测 ~/.qoder-cn/ 存在 → 不存在则创建基础骨架 |
| 2 | setup.sh | rules/ 软链（core-identity/soul/user + execution-guidelines ← 包内承载件；动态状态快照/问卷答案/题目库 ← 记忆中心） |
| 3 | setup.sh | AGENTS.md / MEMORY.md 实体写入（全文注入通道·已存在不覆盖） |
| 4 | 安装器 | settings.json hooks 注册（4 事件×对应脚本 + extra_hooks Stop 守卫·setup ⛔不碰 settings.json 防双写） |
| 5 | setup.sh | skills/ 软链指向 记忆中心/技能配置/ |
| 6 | setup.sh | 自验证 → 0 FAIL = 端专属面完整 |

## 能力
- hooks: ✅ (Stop/UserPromptSubmit/PreToolUse/SessionStart)
- rules: ✅ (alwaysApply)
- AGENTS: ✅ (global_context 全文注入)
- custom_directive: ✅ (走 rules/ 通道 = execution-guidelines.md)

## 来源
- 现有加强包: Qoder系加强包 v0.4.2（仅 CN 分支）
- 执行准则: WorkBuddy 自定义指令 → 09-22 同步
- 端名口径: 本端显示名 Qoder CN 🔮（2026-10-03 统一·Qoder Desktop 为过时字面值，仅存于排除清单/多端枚举表）
