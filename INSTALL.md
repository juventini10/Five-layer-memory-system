---
name: 五层记忆系统-布洛陀1.3.1-安装入口
description: >
  统一安装入口。AI 收到"读取这个安装包，执行安装"后第一个读的文件。
  自动检测用户类型做分流——不占用户时间，不提问。
target_platform: all
author: 皮叔（五层记忆系统 · 布洛陀版本 v1.3.1）
license: MIT
version: "1.3.1"
compatibility: workbuddy
---

# 🏮 布洛陀 1.3.1 — 安装入口

> 🔴 本文件是本安装包的**宪法级入口文件**。不是建议，是硬约束。不可跳过。
> 🔴 所有安装流程从这里开始。不管用户怎么说，第一个读的文件必须是这里。

> **AI 必读：这是本安装包的唯一入口文件。**
> 不管用户怎么描述（"帮我装"、"帮我升级"、"读取安装包"），都从这里开始。
> 前 20 行分流，不需要问用户任何问题。

---

## Step -1：关键词预检（最早判定）

> 在执行任何 Bash 检测之前，先看用户说的第一句话是否包含以下模式：

| 用户说的 | 匹配模式 | 路由 |
|----------|----------|------|
| 装 daily-buddy / 安装三明智 / install clock-loop … | `装`/`安装`/`install` + **Skill 名**（中英文均可，见下方映射表） | → 跳至 §**单 Skill 安装** |
| 装记忆琥珀 / 安装记忆琥珀 / install memory amber | `装`/`安装`/`install` + `记忆琥珀`/`memory amber` | → 跳至 §**记忆琥珀单装** |
| 装成就系统 / 安装成就系统 / install achievement | `装`/`安装`/`install` + `成就系统`/`achievement` | → 跳至 §**成就系统单装** |
| 其他（帮我装、读取安装包、执行安装 …） | 无明确 Skill 名 / 记忆琥珀 | → 继续 Step 0 全包安装 |

> 🔴 命中轻量路由 → 继续读 Step 0 确定记忆中心路径，然后跳到对应章节。
> 🔴 未命中 → 正常走 Step 0→分流→全包安装。

### Skill 名映射

| 用户说的 | Skill 目录 |
|----------|-----------|
| 每日伙伴 / daily-buddy | `references/skills/daily-buddy/` |
| 三明智 / triwich / 三明治 | `references/skills/triwich/` |
| 反方向的钟 / clock-loop | `references/skills/clock-loop/` |
| 成长箱 / growth-box | `references/skills/growth-box/` |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / reading-assistant | `references/skills/reading-assistant/` |
| 系统日志 / system-logger | `references/skills/system-logger/` |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/` |
| Shall We Talk / SWT | `references/skills/shall-we-talk/` |

---

## Step 0：自动分流检测

先执行 3 个文件系统查询（Bash `ls` 实际验证，不用 Read，不用猜）：

```bash
# 检测 1：是否有已有的记忆系统文件
ls ~/.workbuddy/IDENTITY.md 2>/dev/null && echo "FOUND_IDENTITY"

# 检测 2：是否有 .install 标记（旧版布洛陀或安装过至少一次）
# ⚠️ 以下路径是已知可能位置——如果用户记忆共享中心不在这些路径，
#    检测2结果为❌不影响决策（走半安装态或全新），不阻塞流程。
ls [记忆共享中心]/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER"
ls ~/AI记忆库/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER_ALT"

# 检测 3：是否有问卷答案（用于升级时补差异）
# ⚠️ 搜不到不等于没有——可能路径不同。走"老用户·问卷丢"兜底。
find ~/ -maxdepth 4 -name "问卷答案汇总.md" 2>/dev/null | head -3
```

### 分流决策表

| 检测 1 | 检测 2 | 检测 3 | 用户类型 | 路由 |
|:------:|:------:|:------:|:--------|:----|
| ❌ 无 | ❌ 无 | ❌ 无 | **全新用户** | → 读 `README.md`（产品介绍） → 然后读执行文件，执行步骤1→7（含33题） |
| ✅ 有 | ✅ 有 | ✅ 有 | **老用户·问卷在** | → 读执行文件，走升级模式（自动跳过问卷→检测系统文件差异→展示→确认→备份→完成） |
| ✅ 有 | ❌/✅ | ❌ 无 | **老用户·问卷丢** | → 见下方「老用户问卷兜底」 |
| ❌ 无 | ✅ 有 | ❌ 无 | **路径迁移** | 同老用户·问卷丢（先找问卷，再升级） |
| ✅ 有 | ❌ 无 | ❌ 无 | **半安装态** | 读执行文件，走修复模式 |

---

### 🎯 为什么必须完成33题？

33题不是随便填填的表——是**系统认识你的第一通道**。

这些题覆盖你的价值观、决策模式、行为习惯、当前状态和盲区。AI根据你的答案自动生成五层记忆系统的核心文件：

```
33题 → CORE.md（你的价值观锚点）
     → 三大思维白皮书（你的认知模式）
     → 用户基本规则（你的行为约束）
     → MEMORY.md（协作契约）
```

没有这些，系统只是个空壳——不会记住你是谁，也不会和你共鸣。

> 📌 **新老用户都一样：33题是安装前置条件，答完才能继续。不完成，不走下一步。**

---

### ⚠️ 老用户问卷兜底

检测3（问卷文件）没找到时，按以下顺序处理：

1. **自动扩展搜索范围**
   ```bash
   find ~/ -name "*问卷*" -o -name "*question*" 2>/dev/null | head -5
   ```

2. **依然没找到 → 问用户：**
   > "没有找到历史问卷文件。如果你知道它在哪里，告诉我路径，我来读取确认。
   > 找不到的话需要重新作答33题——这是安装的前置条件，不能跳过。"

3. **用户提供路径 → AI 读取并验证格式**
   - 文件包含 Q1-Q33 标记 → 确认有效 → **跳过问卷，走升级流程**
   - 格式不对 → "这个文件不是标准问卷格式，需要重新作答"

4. **用户说找不到 / 提供路径格式无效 → 走完整问卷流程**

> 📌 **铁律：33题不完成，安装不继续。** 不管新老用户，没有例外。

### 🚫 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ 问"你是新用户还是老用户" | INSTALL.md 做检测就是为了一句话不说先判断 |
| ❌ 停住等用户回答 | 检测完了出报告，然后继续干活 |
| ❌ 同时读多个步骤文件 | 薄入口，一次一步，按需加载 |
| ❌ 跳过问卷（任何理由） | 33题是安装前置条件，不完成不走下一步 |

> 例外：如果用户明确说了「装 XX Skill」/「install XX skill」或「装记忆琥珀」/「install memory amber」或「装成就系统」/「install achievement」（含中英文），跳过全包安装，走对应轻量路由。

### 检测完成输出模板

```
🏮 布洛陀 1.3.1 安装检测
├─ 用户类型：[全新 / 升级]
├─ 检测依据：[列出3项检测结果]
│
⚡ 路由指令：按上表方向读取对应文件，立即开始安装。
    不停顿、不提问、不多读。
```

> 输出后按路由方向读取对应文件开始工作。
>
> 🔴 **全路径强制门禁**：无论全新/升级/修复/半安装，在读执行文件（或进入升级模式）**之前**，必须先执行下方 **Step 0.5 数据污染检测**——一步都不能跳。单体安装同理（见各单装章节前置步）。

---

## Step 0.5：数据污染检测（全路径强制 · 全新/升级/重装都跑）

> **为什么**：早期版本的部分文件中，混入了开发阶段遗留的**样例数据**（带真实感的占位内容，对你无用）。本步在**任何安装路径**下都先跑一次，**精准清除这些样例数据、绝不触碰你自己的记录**：
> - 有你手写记录的文件（SHADOW / 未知未知）→ 用完整 SHA256 **逐条精确比对**，只删命中的样例块，你自己的条目哈希不同、**数学上零误删**、完整保留；
> - 纯自动生成的展示文件（成就系统）→ 重置为标准模板，你的真实数据由 tracker 下次自动重算，无手写损失。
>
> 参照物 `integrity-fingerprints.json` 是**不可逆哈希指纹**（无原文、无法读取还原）。改前自动 `.pre-decontam.bak` 备份，可回滚。

**执行（Step 0 确定记忆中心路径后，立即跑一次）**：

```bash
python3 "<安装包>/数据污染检测.py" \
  --memory-root "<记忆共享中心>" \
  --fingerprints "<安装包>/references/integrity-fingerprints.json" \
  --template-root "<安装包>/references" \
  --apply
```

Windows(PowerShell) 等价（`python3`→`python`、写成一行、路径用 `/` 即可）：

```powershell
python "<安装包>/数据污染检测.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
```

- `<记忆共享中心>` = Step 0 检测到的记忆中心根目录；`<安装包>` = 本安装包根目录
- **全新用户**：记忆文件尚未生成 → 检测为空 → 自动跳过（0 命中），不阻塞
- **升级 / 重装用户**：命中即清理，脚本输出清理清单
- **幂等**：可重复跑，已干净则跳过

**对用户的话术**（不展开技术细节，禁止提"隐私/作者"）：

> 已完成数据污染检测：清理了 N 处开发阶段遗留的样例数据（这些不是你的内容、对你无用），**你自己的记录完整保留**。原文件已自动备份，可随时还原。
> （若 0 命中则说：数据污染检测通过，未发现需清理的内容。）

---

## 单 Skill 安装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
> ```bash
> python3 "<安装包>/数据污染检测.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。
> **Windows(PowerShell)**：同一条命令，把 `python3` 换成 `python`、写成一行（去掉行尾 `\`），路径用 `/` 即可。

> 用户**明确说了**「装 XX Skill」/「install XX skill」时，走此路径，不跑全包安装。
> 支持中英文：装/安装/install + 中英文 Skill 名。

### Skill 名映射

| 用户说的 | 目录 |
|----------|------|
| 每日伙伴 / daily-buddy | `references/skills/daily-buddy/` |
| 三明智 / triwich | `references/skills/triwich/` |
| 反方向的钟 / clock-loop | `references/skills/clock-loop/` |
| 成长箱 / growth-box | `references/skills/growth-box/` |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / reading-assistant | `references/skills/reading-assistant/` |
| 系统日志 / system-logger | `references/skills/system-logger/` |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/` |
| Shall We Talk / SWT | `references/skills/shall-we-talk/` |

### 安装步骤

1. **确定记忆中心路径**：Bash `ls [常见路径]/技能配置*/SKILL.md` 或读 `.install/step3-done.md`。找不到 → 提示先完成全包安装步骤3（确定记忆中心路径）。

2. **执行安装**（以 daily-buddy 为例）：

   ```bash
   SKILL=daily-buddy
   MC="<记忆共享中心绝对路径>"
   DIARY_VAULT="<日记仓库绝对路径>"
   DIARY_SUBDIR="<日记子目录>"

   # 备份旧版
   [ -d "$MC/技能配置/$SKILL" ] && mkdir -p "$MC/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)" && cp -r "$MC/技能配置/$SKILL" "$MC/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)/"

   # 复制
   mkdir -p "$MC/技能配置/$SKILL"
   cp -r references/skills/"$SKILL"/* "$MC/技能配置/$SKILL/"

   # 替换占位符
   find "$MC/技能配置/$SKILL/" \( -name "*.md" -o -name "*.py" \) -exec perl -i -pe "s|\[记忆共享中心\]|$MC|g" {} \;
   find "$MC/技能配置/$SKILL/" -name "*.py" -exec perl -i -pe "s|\[日记仓库\]|$DIARY_VAULT|g" {} \;
   find "$MC/技能配置/$SKILL/" -name "*.py" -exec perl -i -pe "s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;

   # 软链接
   ln -sf "$MC/技能配置/$SKILL" ~/.workbuddy/skills/"$SKILL"
   ```

3. **Windows**：

   ```powershell
   $SKILL="daily-buddy"
   $MC="<记忆共享中心绝对路径>"
   $DIARY_VAULT="<日记仓库绝对路径>"
   $DIARY_SUBDIR="<日记子目录>"

   # 备份旧版
   if (Test-Path "$MC\技能配置\$SKILL") {
     $bak = "$MC\记忆琥珀\升级前备份_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
     New-Item -ItemType Directory -Path $bak -Force
     Copy-Item "$MC\技能配置\$SKILL" $bak -Recurse
   }

   # 复制
   New-Item -ItemType Directory -Path "$MC\技能配置\$SKILL" -Force
   Copy-Item "references\skills\$SKILL\*" "$MC\技能配置\$SKILL\" -Recurse

   # 替换占位符
   Get-ChildItem "$MC\技能配置\$SKILL" -Include "*.md","*.py" -Recurse | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC).Replace('[日记仓库]', $DIARY_VAULT).Replace('[日记子目录]', $DIARY_SUBDIR) | Set-Content $_.FullName -NoNewline
   }

   # 软链接（需管理员权限）
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.workbuddy\skills\$SKILL" -Target "$MC\技能配置\$SKILL" -Force
   ```

4. **验证**：`$MC/技能配置/$SKILL/SKILL.md` 存在，`readlink ~/.workbuddy/skills/$SKILL` 指向正确。

---

## 成就系统单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
> ```bash
> python3 "<安装包>/数据污染检测.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。
> **Windows(PowerShell)**：同一条命令，把 `python3` 换成 `python`、写成一行（去掉行尾 `\`），路径用 `/` 即可。

> 用户说「装成就系统」/「安装成就系统」/「install achievement」时，走此路径。

### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **执行安装**：

   ```bash
   MC="<记忆共享中心绝对路径>"
   DIARY_VAULT="<日记仓库绝对路径>"
   DIARY_SUBDIR="<日记子目录>"

   # 创建目录
   mkdir -p "$MC/成就系统/scripts"

   # 复制成就脚本
   cp references/成就系统/scripts/*.py "$MC/成就系统/scripts/"
   cp references/成就系统/scripts/*.sh "$MC/成就系统/scripts/" 2>/dev/null || true

   # 替换占位符
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[记忆共享中心\]|$MC|g" {} \;
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[日记仓库\]|$DIARY_VAULT|g" {} \;
   find "$MC/成就系统/" -name "*.py" -exec perl -i -pe "s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;

   # 验证
   ls "$MC/成就系统/scripts/achievement_tracker.py" && echo "成就系统安装完成"
   ```

3. **Windows**：

   ```powershell
   $MC="<记忆共享中心绝对路径>"
   $DIARY_VAULT="<日记仓库绝对路径>"
   $DIARY_SUBDIR="<日记子目录>"
   New-Item -ItemType Directory -Path "$MC\成就系统\scripts" -Force
   Copy-Item references\成就系统\scripts\*.py "$MC\成就系统\scripts\"

   Get-ChildItem "$MC\成就系统\scripts\*.py" | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC).Replace('[日记仓库]', $DIARY_VAULT).Replace('[日记子目录]', $DIARY_SUBDIR) | Set-Content $_.FullName -NoNewline
   }

   Test-Path "$MC\成就系统\scripts\achievement_tracker.py"  # 期望 True
   ```

3. **Windows**：用 PowerShell `Copy-Item` + `(Get-Content).Replace()`，逻辑一致。

4. **验证**：`ls [记忆共享中心]/成就系统/scripts/achievement_tracker.py` 存在 ✅

---

## 记忆琥珀单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
> ```bash
> python3 "<安装包>/数据污染检测.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。
> **Windows(PowerShell)**：同一条命令，把 `python3` 换成 `python`、写成一行（去掉行尾 `\`），路径用 `/` 即可。

> 用户说「装记忆琥珀」/「安装记忆琥珀」/「install memory amber」时，走此路径。

### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **macOS 安装**：

   ```bash
   MC="<记忆共享中心绝对路径>"
   mkdir -p "$MC/记忆琥珀/engine/logs"

   # 复制脚本
   cp references/记忆琥珀/scripts/amber-backup.sh "$MC/记忆琥珀/engine/"
   cp references/记忆琥珀/scripts/amber-fswatch-wrapper.sh "$MC/记忆琥珀/engine/"
   chmod +x "$MC/记忆琥珀/engine/"*.sh

   # 替换占位符
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" "$MC/记忆琥珀/engine/"*.sh

   # 生成白名单（带记忆琥珀设计哲学 §4.6 白名单制说明）
   # 如果已有白名单，只追加不覆盖；如果是全新，从模板生成
   if ! [ -f "$MC/记忆琥珀/engine/amber-whitelist.txt" ]; then
     cp references/记忆琥珀/scripts/amber-whitelist.txt.template "$MC/记忆琥珀/engine/amber-whitelist.txt"
   fi
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" "$MC/记忆琥珀/engine/amber-whitelist.txt"

   # 注册 launchd（macOS 后台守护）
   cp references/记忆琥珀/scripts/com.memoryamber.backup.plist ~/Library/LaunchAgents/
   perl -i -pe "s|\[记忆共享中心\]|$MC|g" ~/Library/LaunchAgents/com.memoryamber.backup.plist
   launchctl load ~/Library/LaunchAgents/com.memoryamber.backup.plist
   ```

3. **Windows 安装**：

   ```powershell
   $MC = "<记忆共享中心绝对路径>"
   New-Item -ItemType Directory -Path "$MC\记忆琥珀\engine\logs" -Force

   # 复制脚本
   Copy-Item references\记忆琥珀\scripts\amber-backup.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-watch.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install-task.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install-service.ps1 "$MC\记忆琥珀\engine\"
   Copy-Item references\记忆琥珀\scripts\amber-install.ps1 "$MC\记忆琥珀\engine\"

   # 替换占位符
   Get-ChildItem "$MC\记忆琥珀\engine\*.ps1" | ForEach-Object {
     (Get-Content $_.FullName -Raw).Replace('[记忆共享中心]', $MC) | Set-Content $_.FullName -NoNewline
   }

   # 生成白名单
   if (!(Test-Path "$MC\记忆琥珀\engine\amber-whitelist.txt")) {
     Copy-Item references\记忆琥珀\scripts\amber-whitelist.txt.template "$MC\记忆琥珀\engine\amber-whitelist.txt"
     (Get-Content "$MC\记忆琥珀\engine\amber-whitelist.txt" -Raw).Replace('[记忆共享中心]', $MC) | Set-Content "$MC\记忆琥珀\engine\amber-whitelist.txt" -NoNewline
   }

   # 注册后台守护（分发器自动选 NSSM 服务 / Task Scheduler 回退）
   pwsh -ExecutionPolicy Bypass -File "$MC\记忆琥珀\engine\amber-install.ps1"
   ```

4. **验证**：
   - macOS：`cat /tmp/guard-heartbeat-memoryamber.txt` 时间戳 < 90 秒
   - Windows：`Get-ScheduledTask -TaskName "MemoryAmberWatch" | Select State` 期望 `Running`

---

## 文件角色说明

| 文件 | 角色 | 什么时候读 |
|:----|:----|:----------|
| **INSTALL.md** （本文件） | 🚪 **唯一入口** | AI 收到"执行安装"后的第一个文件 |
| **README.md** | 📖 产品介绍 | 全新用户快速了解这是什么，老用户可选跳过 |
| **CHANGELOG.md** | 📋 版本记录 | 想了解每个版本改了什么时翻看，不影响安装流程 |
| **五层记忆系统-布洛陀-执行文件-WorkBuddy版.md** | ⚙️ 执行引擎 | 分流完成后，按步骤逐段读取 |

> **🪝 关于钩子安装**：执行引擎在「步骤6（Skill 安装）」之后、「步骤6.5（记忆琥珀）」之前，自动执行一个**不独立计步序**的「步骤6·钩子安装」子步骤——把未知未知路由兜底钩子 `route_unknown_unknown.py` 挂到 `~/.workbuddy/settings.json` 的 `hooks.Stop`（全新/升级用户都跑）。不在此处改分流逻辑，随执行引擎自动发生。

> **设计原则**：所有文件各司其职，不重复。
> 用户只需要说"读取这个安装包，执行安装"——后面的事 AI 自己判断。
