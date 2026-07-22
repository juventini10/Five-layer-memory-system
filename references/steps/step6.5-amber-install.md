# 步骤6.5：记忆琥珀安装（物理级文件哨兵）

📦 **产出物**：记忆琥珀物理级文件监听备份系统已安装并运行

> **定位**：step6（Skill 安装）之后、step7（系统验证）之前。
> **性质**：**必装**——记忆琥珀是五层记忆系统的物理级安全网，不装等于裸奔。
> **跨平台**：macOS 用 fswatch + launchd；Windows 用 FileSystemWatcher + Task Scheduler。

---

> **⚡ 步骤锁定协议**
> ① 导航锁：每次回复首行输出 `步骤6.5/7`
> ② 偏离锁：用户问无关问题 → 记到待办列表，继续安装
> ③ 检查点前置依赖：Read `{记忆共享中心}/.install/step6-done.md` — 不存在则阻塞
> ④ 检查点写入：末尾 Write `{记忆共享中心}/.install/step6.5-done.md`
> 🔒 门禁：备份脚本存在 + 白名单已替换占位符 + 监听服务已启动 + 首次备份成功

## 执行指令

### ⚠️ 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ NEVER跳过白名单占位符替换 | 占位符不替换=监听器找不到文件=备份永远不触发 |
| ❌ NEVER在监听服务未启动前说"安装完成" | 脚本装了但没跑=等于没装 |
| ❌ NEVER在首次备份未成功前说"已生效" | 首次备份失败=某个环节有问题，必须排查 |
| ❌ NEVER修改备份脚本的逻辑 | 脚本是发布包成品，改逻辑=篡改源码 |

### 🔌 熔断器

- **成功条件**：脚本就位 + 白名单替换 + 监听启动 + 首次备份成功（日志有"完成：备份 N / 跳过 M / 缺失 K"）
- **中断处理**：监听服务启动失败 → 输出错误 → 用户排查后重试
- **降级处理**：用户环境确实不支持 fswatch / Task Scheduler（如系统版本过低无法安装）→ 只装备份脚本，告知用户手动定期跑，写入 step6.5-done.md 标注 `mode: manual`。**除此之外不降级**——fswatch / pwsh 装不上就帮用户装上，不能跳过。

### 平台检测

```bash
# macOS 检测
uname -s | grep -q Darwin && echo "PLATFORM=macos"

# Windows 检测（在 pwsh 中）
$IsWindows -or $env:OS -eq "Windows_NT"  # 返回 true = Windows
```

---

## macOS 安装流程

### 6.5a. 检查前置：Homebrew + fswatch

> ⚠️ macOS 装 fswatch 的唯一常规途径是 Homebrew。若 Homebrew 本身缺失，必须先装它，否则 `brew install fswatch` 会直接报错。

```bash
# 先确认 Homebrew 存在（缺失则先装 Homebrew，再回来继续）
if ! command -v brew >/dev/null 2>&1; then
  echo "⚠️ 未检测到 Homebrew，先装 Homebrew："
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  echo "装完 Homebrew 后回到本步骤继续。"
fi

which fswatch || echo "NOT_INSTALLED"
```

- ✅ fswatch 已安装 → 继续 6.5b
- ❌ fswatch 未安装（Homebrew 已在）→ `brew install fswatch`，等待用户确认后重新检测
- ❌ Homebrew 缺失 → 先按上面命令装 Homebrew，再 `brew install fswatch`

### 6.5b. 复制脚本到记忆琥珀引擎目录

```bash
# 创建目标目录
mkdir -p {MEMORY_CENTER}/记忆琥珀/engine
mkdir -p {MEMORY_CENTER}/记忆琥珀/engine/logs

# 复制脚本
cp {包根目录}/references/记忆琥珀/scripts/amber-backup.sh {MEMORY_CENTER}/记忆琥珀/engine/
cp {包根目录}/references/记忆琥珀/scripts/amber-fswatch-wrapper.sh {MEMORY_CENTER}/记忆琥珀/engine/
chmod +x {MEMORY_CENTER}/记忆琥珀/engine/amber-backup.sh
chmod +x {MEMORY_CENTER}/记忆琥珀/engine/amber-fswatch-wrapper.sh
```

### 6.5c. 生成白名单（替换占位符）

读取 `amber-whitelist.txt.template`，将以下占位符替换为实际路径：

| 占位符 | 替换为 |
|:-------|:------|
| `{MEMORY_CENTER}` | 步骤3确认的记忆共享中心路径 |
| `{WORKBUDDY_HOME}` | `~/.workbuddy`（或用户自定义的 WorkBuddy 目录） |
替换后写入 `{MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt`。

### 6.5d. 更新监听目录路径

编辑 `{MEMORY_CENTER}/记忆琥珀/engine/amber-fswatch-wrapper.sh` 的 `PATHS` 数组，确保路径与白名单覆盖的目录一致。

### 6.5e. 安装 launchd 服务

读取 `com.memoryamber.backup.plist.template`，替换占位符：
- `{MEMORY_CENTER}` → 记忆共享中心绝对路径（如 `/Users/xxx/个人AI档案`）
- `{USER_HOME}` → 用户 home 目录绝对路径

写入 `~/Library/LaunchAgents/com.memoryamber.backup.plist`。

```bash
# 加载服务
launchctl load ~/Library/LaunchAgents/com.memoryamber.backup.plist

# 确认服务在跑（读真实退出状态，而非只看命令有无输出）
if launchctl list | grep -q memoryamber; then
  echo "✅ 记忆琥珀守护已注册并运行"
else
  echo "⚠️ launchctl 未能在【当前会话】确认守护在跑，见下方沙箱兜底"
fi
```

> **⚠️ 沙箱隔离兜底（关键·必读）**
> 若本步骤由 AI 工具（WorkBuddy / 类 Cursor 内嵌终端）的 Bash 执行：这些工具的终端运行在**隔离的 launchd/user 沙箱域**，`launchctl load` 只注册到沙箱域、**不会传播到你的真实登录会话**——即真实终端下 `launchctl list` 看不到守护，进程并未真正运行。
>
> **load 后验证 + 失败兜底（load 未生效时必做）**：
> 1. 在**真实终端**（系统「终端」app / iTerm，非 AI 工具内嵌 Bash）补跑一次：
>    ```bash
>    launchctl load ~/Library/LaunchAgents/com.memoryamber.backup.plist
>    launchctl list | grep memoryamber   # 应能看到 com.memoryamber.backup
>    ```
> 2. 或直接**注销并重新登录**——plist 已设 `RunAtLoad=true` + `KeepAlive=true`，登录时自动拉起、崩溃后自动重启。
> 3. 真机验证：`ps aux | grep -i[ ]fswatch` 应能看到监听进程在跑。
>
> 🔒 记住：「AI 说 load 了」≠「进程真在跑」——以真实会话的 `launchctl list` / `ps` 为准，二者一致才算安装完成。

### 6.5f. 首次备份验证

```bash
# 手动触发首次备份
bash {MEMORY_CENTER}/记忆琥珀/engine/amber-backup.sh

# 查看日志确认成功
tail -5 {MEMORY_CENTER}/记忆琥珀/engine/logs/amber.log
```

**通过条件**：日志末尾出现 `完成：备份 N / 跳过 M / 缺失 K` 且 `=== 记忆琥珀备份结束 ===`。

### 6.5f+. 占位符残留检查（硬性门禁）

> ⚠️ 这一步是设计端防错——不依赖 AI 自觉检查，用物理命令强制验证。

```bash
# 白名单中不能残留任何占位符
RESIDUAL=$(grep -c '{' {MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt)
if [ "$RESIDUAL" -gt 0 ]; then
  echo "❌ 白名单中仍有 $RESIDUAL 处占位符未替换："
  grep -n '{' {MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt
  echo "请回到 6.5c 重新替换占位符。"
  exit 1
fi

echo "✅ 白名单占位符已全部替换"
```

```powershell
# Windows 版
$residual = (Select-String -Path {MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt -Pattern '{' -AllMatches).Matches.Count
if ($residual -gt 0) {
  Write-Host "❌ 白名单中仍有 $residual 处占位符未替换：" -ForegroundColor Red
  Select-String -Path {MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt -Pattern '{'
  Write-Host "请回到 6.5c 重新替换占位符。"
  exit 1
}

Write-Host "✅ 白名单占位符已全部替换" -ForegroundColor Green
```

**通过条件**：`RESIDUAL = 0`（白名单中不包含任何 `{` 字符）。残留任何占位符都视为安装未完成，阻塞后续步骤。

### 6.5g. 触发测试（可选但推荐）

```bash
# 给某文件加一个空行触发变化
echo "" >> [记忆共享中心]/核心层/SOUL.md

# 等 5 秒让 fswatch 触发
sleep 5

# 查看日志，应该有新的备份记录
tail -3 {MEMORY_CENTER}/记忆琥珀/engine/logs/amber.log

# 回滚测试修改
perl -pi -e 'chomp if eof' [记忆共享中心]/核心层/SOUL.md
```

---

## Windows 安装流程

### 6.5a. 检查 PowerShell 环境

> 脚本兼容 PowerShell 5.1+ 和 PowerShell 7+。优先使用 `pwsh`（7+），无 `pwsh` 时自动回退到 `powershell.exe`（5.1）。

```powershell
# 检查 PowerShell 版本（5.1+ 即可，7+ 更佳）
$PSVersionTable.PSVersion
```

- ✅ 版本 ≥ 5.1 → 继续 6.5b
- ❌ 版本 < 5.1 → 提示用户安装 PowerShell 7：
  ```powershell
  winget install Microsoft.PowerShell
  ```

### 6.5b. 复制脚本到记忆琥珀引擎目录

```powershell
# 创建目标目录
New-Item -ItemType Directory -Path {MEMORY_CENTER}/记忆琥珀/engine -Force
New-Item -ItemType Directory -Path {MEMORY_CENTER}/记忆琥珀/engine/logs -Force

# 复制脚本
Copy-Item {包根目录}\references\记忆琥珀\scripts\amber-backup.ps1 {MEMORY_CENTER}/记忆琥珀/engine/
Copy-Item {包根目录}\references\记忆琥珀\scripts\amber-watch.ps1 {MEMORY_CENTER}/记忆琥珀/engine/
Copy-Item {包根目录}\references\记忆琥珀\scripts\amber-install-task.ps1 {MEMORY_CENTER}/记忆琥珀/engine/
Copy-Item {包根目录}\references\记忆琥珀\scripts\amber-install-service.ps1 {MEMORY_CENTER}/记忆琥珀/engine/
Copy-Item {包根目录}\references\记忆琥珀\scripts\amber-install.ps1 {MEMORY_CENTER}/记忆琥珀/engine/
```

### 6.5b2. 替换 PS1 脚本中的占位符（Windows）

> PS1 脚本使用 `[记忆共享中心]` 占位符，安装时替换为用户的实际记忆共享中心路径。

```powershell
$MEMORY_CENTER = "<步骤3确定的记忆共享中心绝对路径>"
$scripts = @(
    "{MEMORY_CENTER}/记忆琥珀/engine/amber-backup.ps1",
    "{MEMORY_CENTER}/记忆琥珀/engine/amber-watch.ps1",
    "{MEMORY_CENTER}/记忆琥珀/engine/amber-install-task.ps1",
    "{MEMORY_CENTER}/记忆琥珀/engine/amber-install-service.ps1",
    "{MEMORY_CENTER}/记忆琥珀/engine/amber-install.ps1"
)
foreach ($s in $scripts) {
    (Get-Content $s -Raw).Replace('[记忆共享中心]', $MEMORY_CENTER) | Set-Content $s -NoNewline
}
```

> 验证（应无残留占位符）：
> ```powershell
> Select-String -Path "{MEMORY_CENTER}/记忆琥珀/engine/amber-backup.ps1" -Pattern '\[记忆共享中心\]'   # 期望无输出
> ```

### 6.5c. 生成白名单（替换占位符）

同 macOS 的 6.5c——读取模板、替换占位符、写入 `{MEMORY_CENTER}/记忆琥珀/engine/amber-whitelist.txt`。

> ⚠️ Windows 下路径分隔符为 `\`，白名单中的路径需要转换为 Windows 格式。

### 6.5d. 更新监听目录路径

编辑 `{MEMORY_CENTER}/记忆琥珀/engine/amber-watch.ps1` 的 `$WatchPaths` 数组，确保路径与白名单覆盖的目录一致。

### 6.5e. 注册后台守护（分发器自动选 NSSM 服务 / Task Scheduler 回退）

> 运行分发器 `amber-install.ps1`：有管理员权限 + nssm → **NSSM 服务**（首选，SCM 托管，最稳，与 macOS launchd 对称）；否则 → **Task Scheduler 加固版**（免提权回退）。两条路跑同一个 amber-watch.ps1（轮询）。
> nssm 可放到 `{MEMORY_CENTER}/记忆琥珀/engine/nssm/nssm.exe` 或设 `AMBER_NSSM` 环境变量；无 nssm 时自动走 Task 回退。

```powershell
# 运行分发器（自动选路径 + 注册 + 启动）
pwsh -ExecutionPolicy Bypass -File {MEMORY_CENTER}/记忆琥珀/engine/amber-install.ps1

# 验证任务已注册且处于就绪/运行态（读真实状态，而非只看脚本有没有报错）
$task = Get-ScheduledTask -TaskName "MemoryAmberWatch" -ErrorAction SilentlyContinue
if ($task) {
  $state = (Get-ScheduledTaskInfo -TaskName "MemoryAmberWatch").State
  Write-Host "✅ 记忆琥珀任务已注册，状态：$state" -ForegroundColor Green
} else {
  Write-Host "⚠️ 未能在【当前会话】确认任务注册，见下方沙箱/权限兜底" -ForegroundColor Yellow
}
```

脚本会自动：
1. 注册 `MemoryAmberWatch` 任务（开机自启 + 崩溃重启）
2. 立即启动任务
3. 输出状态验证信息

> **⚠️ 沙箱/权限兜底（关键·必读）**
> 若本步骤由 AI 工具内嵌的 pwsh 执行：部分工具的运行上下文被隔离、或缺少管理员令牌，可能导致 `Register-ScheduledTask` **注册成功却未计入你真实用户会话的任务计划程序库**，或被静默拒绝。
>
> **注册后验证 + 失败兜底（未生效时必做）**：
> 1. 在**真实 PowerShell 7（以管理员身份）** 补跑一次：
>    ```powershell
>    pwsh -ExecutionPolicy Bypass -File {MEMORY_CENTER}/记忆琥珀/engine/amber-install-task.ps1
>    ```
> 2. 真机验证：`Get-ScheduledTask -TaskName "MemoryAmberWatch" | Select-Object TaskName, State` 应返回 `Ready` 且已在运行。
> 3. 权限不足 → 确认以管理员身份运行 PowerShell；企业策略禁用计划任务时，退而求其次用 `mode: manual` 标注（仅手动定期跑，记入 step6.5-done.md）。
>
> 🔒 原则同 macOS：「AI 说注册了」≠「任务真在跑」——以真实会话的 `Get-ScheduledTask` 为准。

### 6.5f. 首次备份验证

```powershell
# 手动触发首次备份
pwsh -ExecutionPolicy Bypass -File {MEMORY_CENTER}/记忆琥珀/engine/amber-backup.ps1

# 查看日志确认成功
Get-Content {MEMORY_CENTER}/记忆琥珀/engine/logs/amber.log -Tail 5
```

**通过条件**：日志末尾出现 `完成：备份 N / 跳过 M / 缺失 K` 且 `=== 记忆琥珀备份结束 ===`。

### 6.5g. 触发测试（可选但推荐）

```powershell
# 给某文件加一个空行触发变化
Add-Content [记忆共享中心]/核心层/SOUL.md ""

# 等 5 秒让 FileSystemWatcher 触发
Start-Sleep -Seconds 5

# 查看日志
Get-Content {MEMORY_CENTER}/记忆琥珀/engine/logs/amber.log -Tail 3

# 回滚测试修改
$content = Get-Content [记忆共享中心]/核心层/SOUL.md -Raw
$content = $content.TrimEnd()
Set-Content [记忆共享中心]/核心层/SOUL.md $content
```

---

## 安装完成确认

无论哪个平台，安装完成后向用户输出：

```
✅ 记忆琥珀已安装并运行

平台：{macOS / Windows}
监听方式：{fswatch + launchd / FileSystemWatcher + Task Scheduler}
白名单文件数：{N}
首次备份结果：备份 {X} / 跳过 {Y} / 缺失 {Z}

备份存储位置：[记忆共享中心]/记忆琥珀/
日志位置：{MEMORY_CENTER}/记忆琥珀/engine/logs/amber.log

💡 记忆琥珀会在你修改白名单文件时自动备份，无需任何手动操作。
   如需手动触发：{对应平台的命令}
```

---

## 异常处理（不降级）

记忆琥珀是必装项。遇到问题时优先修复，**不跳过**：

| 问题 | 处理 |
|:-----|:-----|
| fswatch 未装（macOS） | `brew install fswatch` 装上后继续 |
| pwsh 未装或版本低（Windows） | `winget install Microsoft.PowerShell` 装上后继续 |
| launchd 加载失败 | 查看错误日志 → 修复 plist → 重新 load |
| Task Scheduler 注册失败 | 以管理员身份运行 pwsh → 重新执行 amber-install-task.ps1 |
| 占位符替换不全 | 回到 6.5c 重新替换 → 6.5f+ 硬性检查拦截 |
| 首次备份失败 | 查看日志 → 修复问题 → 重新跑 bash amber-backup.sh |

**唯一允许降级的情况**：用户系统版本过低（如 macOS < 10.13 不支持 fswatch、Windows 7 不支持 PowerShell 7+），且无法升级系统。此时只装备份脚本，标注 `mode: manual`，告知用户手动定期跑。
