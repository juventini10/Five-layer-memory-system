# WorkBuddy 平台专属配置

## 步骤4：专属文件（平台专属文件表）

| 平台 | 文件 | 刷新动作 | 说明 |
|------|------|---------|------|
| WorkBuddy | - | 🔴 跳过 | IDENTITY/SOUL/USER system prompt已注入;步骤9已检查三文件 |

## 步骤8：平台文件状态验证

1. Read `~/.workbuddy/IDENTITY.md` - 确认包含价值观/底线/思维底色/气质 + 提取版本号
2. Read `~/.workbuddy/SOUL.md` - 确认包含品格声明 + 提取版本号
3. Read `~/.workbuddy/USER.md` - 确认包含称呼/工具/系统版本 + 提取版本号 + 对比变更日志基线版本
4. 三文件版本号不一致 → 🟡告警并提示
5. USER.md 系统版本 ≠ 变更日志基线 → 自动同步（用Edit工具更新USER.md版本号行）
6. 任一文件缺失 → 报告中🟡标注,不阻塞任务
7. 同步更新 `~/.workbuddy/MEMORY.md` 激活状态行
