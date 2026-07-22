# 记忆琥珀（Memory Amber）

> 物理级文件哨兵——用机制代替意志力，让每次破坏性修改都可回滚

## 定位

五层记忆系统的**时间胶囊层**。不定义规则（铁律管）、不存运行时状态（状态层管）、不做跨文件同步（派生镜像管），只做一件事：**文件被修改时自动留底**。

与旧版"升级前整包备份"的区别：
- **旧版**：手动触发、整包备份、依赖 AI 记得跑——已废弃
- **新版**：物理级监听、单文件备份、操作系统自动触发——v1.1 起

## 跨平台实现

| 平台 | 文件监听 | 服务管理 | 备份脚本 |
|:-----|:---------|:---------|:--------|
| **macOS** | fswatch | launchd plist | amber-backup.sh + amber-fswatch-wrapper.sh |
| **Windows** | FileSystemWatcher | Task Scheduler | amber-backup.ps1 + amber-watch.ps1 + amber-install-task.ps1 |

两端哲学等价、实现各自原生、零额外依赖。

## 文件清单

```
scripts/
├── amber-backup.sh                      # macOS 备份脚本
├── amber-backup.ps1                     # Windows 备份脚本（PowerShell 7+）
├── amber-fswatch-wrapper.sh             # macOS fswatch 监听 wrapper
├── amber-watch.ps1                      # Windows FileSystemWatcher 监听
├── amber-install-task.ps1               # Windows Task Scheduler 注册
├── amber-whitelist.txt.template         # 白名单模板（含占位符）
└── com.memoryamber.backup.plist.template # macOS launchd 配置模板
```

## 安装

安装步骤见 `references/steps/step6.5-amber-install.md`。

安装时机：step6（Skill 安装）之后、step7（系统验证）之前。

## 核心设计原则

1. **物理级监听**——不依赖 AI 自觉，操作系统级触发
2. **内容哈希去重**——SHA-256 前 6 位，内容未变则跳过
3. **版本号 = 时间戳 + 哈希**——不依赖文件内字段
4. **清理三段式**——同日只留 1 份 + 7 天保留 + major 永久
5. **白名单制**——只备份不可重建的高价值文件
6. **幂等性**——连续运行多次结果相同

详细设计依据见 `记忆蓝图/02_设计理念/记忆琥珀设计哲学.md`。

## 常用操作

### macOS

```bash
# 手动触发备份
bash ~/个人AI档案/记忆琥珀/engine/amber-backup.sh

# 查看 launchd 服务状态
launchctl list | grep memoryamber

# 重启监听服务
launchctl unload ~/Library/LaunchAgents/com.memoryamber.backup.plist
launchctl load ~/Library/LaunchAgents/com.memoryamber.backup.plist

# 查看备份日志
tail -30 ~/个人AI档案/记忆琥珀/engine/logs/amber.log

# 查看所有备份
ls -lt ~/个人AI档案/记忆琥珀/*.bak

# 回滚某文件到最新备份
cp ~/个人AI档案/记忆琥珀/workspace_SOUL_20260715-043520_78d363.bak ~/个人AI档案/核心层/workspace/SOUL.md

# 手动创建 major 备份（大版本升级前）
cp ~/个人AI档案/核心层/workspace/SOUL.md ~/个人AI档案/记忆琥珀/workspace_SOUL_major_$(date '+%Y%m%d-%H%M%S')_manual.bak
```

### Windows

```powershell
# 手动触发备份
pwsh -File ~/个人AI档案/记忆琥珀/engine/amber-backup.ps1

# 查看 Task Scheduler 任务状态
Get-ScheduledTask -TaskName MemoryAmberWatch | Get-ScheduledTaskInfo

# 重启监听服务
Stop-ScheduledTask -TaskName MemoryAmberWatch
Start-ScheduledTask -TaskName MemoryAmberWatch

# 查看备份日志
Get-Content ~/个人AI档案/记忆琥珀/engine/logs/amber.log -Tail 30

# 查看所有备份
Get-ChildItem ~/个人AI档案/记忆琥珀/*.bak | Sort-Object LastWriteTime -Descending

# 回滚某文件到最新备份
$latest = Get-ChildItem ~/个人AI档案/记忆琥珀/workspace_SOUL_*.bak | Sort-Object Name -Descending | Select-Object -First 1
Copy-Item $latest.FullName ~/个人AI档案/核心层/workspace/SOUL.md -Force

# 手动创建 major 备份
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item ~/个人AI档案/核心层/workspace/SOUL.md "~/个人AI档案/记忆琥珀/workspace_SOUL_major_${ts}_manual.bak"
```

## 清理规则

| 规则 | 说明 |
|------|------|
| 同日只留 1 份 | 同一文件同一天多次备份，只保留最新的 |
| 7 天保留 | 超过 7 天的非 major 备份自动删除 |
| major 永久 | 文件名含 `_major_` 的备份永不删除 |
| 今天的不碰 | 清理只处理 1 天前的备份 |

## 添加新文件到白名单

编辑 `~/个人AI档案/记忆琥珀/engine/amber-whitelist.txt`，加一行绝对路径即可。
如果新文件所在目录不在监听列表里，还需要更新 `amber-fswatch-wrapper.sh`（macOS）或 `amber-watch.ps1`（Windows）的 `PATHS` / `$WatchPaths` 数组。

## 故障排查

### 监听没触发备份

**macOS**：
1. `launchctl list | grep memoryamber` — 服务是否在跑
2. `cat ~/个人AI档案/记忆琥珀/engine/logs/amber-fswatch.err.log` — 看错误
3. `which fswatch` — 确认 fswatch 已安装

**Windows**：
1. `Get-ScheduledTask -TaskName MemoryAmberWatch` — 任务是否存在
2. `Get-Content ~/个人AI档案/记忆琥珀/engine/logs/amber-watch.log` — 看监听日志
3. `Get-Process pwsh` — 确认 pwsh 进程在跑

### 备份没创建

1. 手动跑一次备份脚本看日志
2. 检查文件是否在白名单里
3. 检查文件内容是否真的变了（哈希对比）
