# 步骤6：Skill安装

📦 **产出物**：9个Skill已安装（含完整references/）+ 软链接自愈脚本，软链接生效

> ⚠️ **Skill内容是模板直拷，不是AI生成。** 安装过程只做三件事：①复制文件 ②替换路径占位符 ③建立软链接。NEVER修改Skill的任何指令、逻辑、措辞——原因是Skill是发布包里的成品，AI改写=篡改源码。如果安装后Skill行为异常，根因在复制/路径环节，不在内容。

> **⚡ 平台检测**：执行前判定当前平台——macOS / Linux 走下方「macOS / Linux」段，Windows 走下方「Windows」段。

---

> **⚡ 步骤锁定协议**
> ① 导航锁：每次回复首行输出 `步骤6/7`
> ② 偏离锁：用户问无关问题 → 记到待办列表，继续安装
> ③ 检查点前置依赖：Read `{记忆共享中心}/.install/step5-done.md` — 不存在则阻塞
> ④ 检查点写入：末尾 Write `{记忆共享中心}/.install/step6-done.md`

## 执行指令

### ⚠️ 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ NEVER修改Skill的任何指令、逻辑、措辞 | Skill是发布包里的成品，AI改写=篡改源码 |
| ❌ NEVER跳过占位符替换 | sed没跑完=用户路径不生效，Skill指向硬编码路径 |
| ❌ NEVER在软链接未验证前说"安装完成" | 软链接失效=Skill无法加载，等于没装 |
| ❌ NEVER在全部9个Skill装完前说"全部安装完毕" | 漏装一个Skill=系统不完整 |

### 🔌 熔断器

Skill安装过程中的异常处理：
- 成功条件：9个Skill全部安装 + 占位符全部替换 + 9条软链接全部有效
- 中断处理：一个Skill安装失败 → 输出错误信息 → 不影响其他Skill继续安装
- 重试机制：失败的Skill单独重试安装
- 降级处理：超过3个Skill安装失败 → 输出"部分安装失败，请检查路径和权限"

### 步骤0：检测安装模式（升级 vs 全新）

```bash
# 先检查是否已有旧版Skill软链接
if ls ~/.workbuddy/skills/*/SKILL.md 2>/dev/null | head -1 > /dev/null; then
  # 老用户升级：从已有软链接反查记忆中心路径
  EXISTING_SKILL=$(ls -d ~/.workbuddy/skills/*/ | head -1)
  MEMORY_CENTER=$(readlink "$EXISTING_SKILL" 2>/dev/null | sed 's|/技能配置/.*||')
  # macOS readlink不支持-f时降级处理
  [ -z "$MEMORY_CENTER" ] && MEMORY_CENTER=$(cd "$EXISTING_SKILL/../.." 2>/dev/null && pwd)
  echo "🔄 升级模式 — 已检测到记忆中心：$MEMORY_CENTER"
else
  # 全新安装：MEMORY_CENTER由step3设置，直接使用
  [ -z "$MEMORY_CENTER" ] && { echo "❌ 请先完成步骤3路径配置"; exit 1; }
  echo "🆕 全新安装 — 记忆中心：$MEMORY_CENTER"
fi
```

> 💡 全新安装：MEMORY_CENTER从步骤3继承。升级用户：单独跑step6时从软链接反查。新用户中止后引导回步骤3。
>
> ⚠️ **升级用户额外步骤**：检测到升级模式后，先Read `CHANGELOG.md`（顶部最新版本条目），展示本次变更摘要（新增/升级/修复），问用户"确认升级？"——确认后才继续安装。（原引用的 `UPGRADE.md` 已删除，变更摘要改由 CHANGELOG.md 提供。）

### 安装的Skill列表

| Skill | 来源目录 | 安装到 |
|------|---------|--------|
| 唤醒记忆系统 | `skills/awaken-memory-system/` | `技能配置/awaken-memory-system/` |
| 每日伙伴 | `skills/daily-buddy/` | `技能配置/daily-buddy/` |
| 系统日志 | `skills/system-logger/` | `技能配置/system-logger/` |
| 三明智 | `skills/triwich/` | `技能配置/triwich/` |
| 迁理之外 | `skills/meta-aletheia/` | `技能配置/meta-aletheia/` |
| 成长箱 | `skills/growth-box/` | `技能配置/growth-box/` |
| Shall We Talk | `skills/shall-we-talk/` | `技能配置/shall-we-talk/` |
| 读书助手 | `skills/reading-assistant/` | `技能配置/reading-assistant/` |
| 反方向的钟 | `skills/clock-loop/` | `技能配置/clock-loop/` |

### macOS / Linux 安装流程

1. 设置路径变量：
   ```bash
   MEMORY_CENTER="[记忆共享中心]"    # 用户的实际记忆中心路径
   DIARY_VAULT="[日记仓库]"           # 用户的日记/笔记路径
   KNOWLEDGE_POOL="[知识库]"          # 用户的知识库路径
  DIARY_SUBDIR="[日记子目录]"        # 日记相对仓库根的路径（如 1-每日计划/01-日记）
   ```

2. 逐个安装Skill（以每日伙伴为例）：
   ```bash
   SKILL_NAME="daily-buddy"
   
   # 升级用户：覆盖前先备份旧版
   if [ -d "$MEMORY_CENTER/技能配置/$SKILL_NAME" ]; then
     mkdir -p "$MEMORY_CENTER/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)"
     cp -r "$MEMORY_CENTER/技能配置/$SKILL_NAME" "$MEMORY_CENTER/记忆琥珀/升级前备份_$(date +%Y%m%d_%H%M%S)/"
   fi
   
   # 复制完整Skill目录（含 references/ 里的所有文件）
   mkdir -p "$MEMORY_CENTER/技能配置/$SKILL_NAME"
   cp -r skills/"$SKILL_NAME"/* "$MEMORY_CENTER/技能配置/$SKILL_NAME/"
   
   # 替换所有 .md 和 .py 文件中的路径占位符（同时处理方括号和花括号两种格式）
   find "$MEMORY_CENTER/技能配置/$SKILL_NAME/" \( -name "*.md" -o -name "*.py" \) -exec \
     perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g; s|\{记忆共享中心\}|$MEMORY_CENTER|g; s|\[日记仓库\]|$DIARY_VAULT|g; s|\[知识库\]|$KNOWLEDGE_POOL|g; s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;
   ```

3. 重复步骤2，依次安装9个Skill（替换SKILL_NAME变量）

4. **复制软链接自愈脚本**
   ```bash
   cp skills/restore-my-skills.sh "$MEMORY_CENTER/技能配置/restore-my-skills.sh"
   chmod +x "$MEMORY_CENTER/技能配置/restore-my-skills.sh"
   # 脚本内 [记忆共享中心] 占位符由 sed 替换（第5步统一处理）
   ```

5. **复制回滚脚本**（仅升级用户，新用户无旧文件可回滚）
   ```bash
   cp rollback.sh "$MEMORY_CENTER/rollback.sh"
   chmod +x "$MEMORY_CENTER/rollback.sh"
   # rollback.sh 头部含 [记忆共享中心] 占位符，由下方 sed 统一替换
   ```

6. 替换路径占位符（同时处理方括号和花括号两种格式）：
   ```bash
   find "$MEMORY_CENTER/技能配置/" \( -name "*.md" -o -name "*.sh" \) | while read -r file; do
     perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g; s|\{记忆共享中心\}|$MEMORY_CENTER|g; s|\[日记仓库\]|$DIARY_VAULT|g; s|\[知识库\]|$KNOWLEDGE_POOL|g; s|\[日记子目录\]|$DIARY_SUBDIR|g" "$file"
   done

   # 成就系统目录：.py + .sh + .md
   if [ -d "$MEMORY_CENTER/成就系统" ]; then
     find "$MEMORY_CENTER/成就系统/" \( -name "*.py" -o -name "*.sh" -o -name "*.md" \) | while read -r file; do
       perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g; s|\{记忆共享中心\}|$MEMORY_CENTER|g; s|\[日记仓库\]|$DIARY_VAULT|g; s|\[知识库\]|$KNOWLEDGE_POOL|g; s|\[日记子目录\]|$DIARY_SUBDIR|g" "$file"
     done
   fi

   # 回滚脚本（根目录，含 [记忆共享中心] 占位符）
   if [ -f "$MEMORY_CENTER/rollback.sh" ]; then
     perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g" "$MEMORY_CENTER/rollback.sh"
   fi

7. 建立软链接：
   ```bash
   # WorkBuddy
   for skill_dir in "$MEMORY_CENTER/技能配置/"*/; do
     skill_name=$(basename "$skill_dir")
     ln -sf "$MEMORY_CENTER/技能配置/$skill_name" ~/.workbuddy/skills/"$skill_name"
     # 🔒 护栏：验真为软链接(防静默降级为副本)。降级=告警,不得瞒报"验证通过"
     if [ -L ~/.workbuddy/skills/"$skill_name" ]; then
       echo "✅ $skill_name 软链接"
     else
       echo "❌ $skill_name 非软链接(疑被降级为副本)——升级前须先 rm -rf 目标避免嵌套,或本机改用真实目录副本"
     fi
   done
   ```

8. 验证软链接生效

> ⚠️ 文件内 `[记忆共享中心]`、`[日记仓库]`、`[知识库]`、`[日记子目录]` 是路径占位符，安装时必须替换为用户的真实路径（`[日记子目录]` 是仓库根到日记目录的相对路径，因人而异）。`~/` 开头的路径（如 `~/.trae/`、`~/CodeBuddy/`、`~/.workbuddy/`）为系统固定路径，无需替换。
> 💡 每个Skill的 `references/` 子目录会随SKILL.md一起安装——确保运行时所有引用文件完整可用。

---

### Windows 安装流程

> Windows 下用 PowerShell 完成同样的三步：复制文件 → 替换路径占位符 → 建立软链接。

#### 1. 确认变量

```powershell
$MEMORY_CENTER = "<步骤3确定的记忆共享中心绝对路径>"
```

#### 2. 逐个安装 Skill（以每日伙伴为例）

```powershell
$SKILL_NAME = "daily-buddy"

# 升级用户：覆盖前先备份旧版
$bakDir = "$MEMORY_CENTER\记忆琥珀\升级前备份_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if (Test-Path "$MEMORY_CENTER\技能配置\$SKILL_NAME") {
    New-Item -ItemType Directory -Path $bakDir -Force
    Copy-Item "$MEMORY_CENTER\技能配置\$SKILL_NAME" $bakDir -Recurse
}

# 复制完整 Skill 目录
New-Item -ItemType Directory -Path "$MEMORY_CENTER\技能配置\$SKILL_NAME" -Force
Copy-Item "references\skills\$SKILL_NAME\*" "$MEMORY_CENTER\技能配置\$SKILL_NAME\" -Recurse

# 替换所有 .md 文件中的路径占位符
Get-ChildItem "$MEMORY_CENTER\技能配置\$SKILL_NAME" -Include "*.md","*.py" -Recurse | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $content = $content.Replace('[记忆共享中心]', $MEMORY_CENTER)
    $content = $content.Replace('{记忆共享中心}', $MEMORY_CENTER)
    Set-Content $_.FullName -Value $content -NoNewline
}
```

#### 3. 重复步骤2，依次安装9个Skill

#### 4. 复制软链接自愈脚本

```powershell
Copy-Item "references\skills\restore-my-skills.sh" "$MEMORY_CENTER\技能配置\restore-my-skills.sh"
```

#### 5. 建立软链接（需管理员权限）

```powershell
$skills = @("awaken-memory-system","daily-buddy","system-logger","triwich","meta-aletheia","growth-box","shall-we-talk","reading-assistant","clock-loop")
foreach ($s in $skills) {
    $target = "$MEMORY_CENTER\技能配置\$s"
    $link   = "$env:USERPROFILE\.workbuddy\skills\$s"
    if (Test-Path $link) { Remove-Item $link -Force }
    New-Item -ItemType SymbolicLink -Path $link -Target $target -Force | Out-Null
    # 🔒 护栏：验形态(需开发者模式/管理员;失败则告警,不瞒报)
    if ((Get-Item $link -ErrorAction SilentlyContinue).LinkType -eq 'SymbolicLink') { Write-Host "OK $s 软链接" }
    else { Write-Host "WARN $s 非软链接(可能未开开发者模式/权限不足)——升级前先删目标避免嵌套" }
}
```

> 💡 Windows 上 `[记忆共享中心]` 和 `{记忆共享中心}` 两种占位符已由步骤2自动替换。

### 🔒 门禁

安装完毕后，检查四项：
1. `[记忆共享中心]/技能配置/` 下是否有 9 个 Skill 目录，每个含 SKILL.md
2. 每个Skill目录下的 `references/` 文件数与来源一致
3. `restore-my-skills.sh` 存在且可执行（`[记忆共享中心]/技能配置/restore-my-skills.sh`）
4. `[记忆共享中心]/成就系统/` 存在且 `scripts/` 下有 .py 文件

缺任一项 → 补装后重验。

> Skill安装完毕 → 写入 `{记忆共享中心}/.install/step6-done.md` → 继续步骤7

> 💡 多平台用户：安装完成后可手动为其他平台建立软链接（Trae: `~/.trae/skills/`, QClaw: `~/.qclaw/skills/` 等）。WorkBuddy链接已自动建立。
