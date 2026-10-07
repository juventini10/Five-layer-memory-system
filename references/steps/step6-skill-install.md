# 步骤6：Skill安装

📦 **产出物**：全部 Skill 已安装（数量=包内 `references/skills/` 含 SKILL.md 的目录数·动态计数为唯一真源，⛔文档不硬写数字·G2-2走查教训：硬写"9个"与版本表10个漂移漏装 good-good-study）+ 软链接自愈脚本，软链接生效

> ⚠️ **Skill内容是模板直拷，不是AI生成。** 安装过程只做三件事：①复制文件 ②替换路径占位符 ③建立软链接。NEVER修改Skill的任何指令、逻辑、措辞——原因是Skill是发布包里的成品，AI改写=篡改源码。如果安装后Skill行为异常，根因在复制/路径环节，不在内容。

> **⚡ 平台检测（Poka-Yoke 接触法·物理阻断·不可跳过）**
>
> ✅DO **第一条命令必须执行**（在任何 cp/mkdir/Copy-Item 之前）：
> ```
> python3 -c "import platform; p=platform.system(); print(f'PLATFORM={p}')"
> ```
> 返回值决定后续**唯一合法路径**：
> - `PLATFORM=Darwin` 或 `PLATFORM=Linux` → **只走**下方「macOS / Linux」段，⛔禁止执行 PowerShell 命令
> - `PLATFORM=Windows` → **只走**下方「Windows」段，⛔禁止执行 bash/cp/mkdir/find/perl 命令
>
> ⛔DO NOT 凭环境推断平台（"有Git Bash所以能跑bash"=错误——Git Bash的$变量展开与原生bash不同，会创建字面量$SKILL_NAME目录）。
> ⛔DO NOT 在未执行上述 python3 命令获得 PLATFORM 值的情况下执行任何安装命令——原因是：跑错段=创建错误目录名=安装失败且用户不知道失败了（静默错误比报错更危险）。
> ⛔DO NOT 因"两段代码功能一样"而混用——bash 语法在 Windows 上行为不可预测，PowerShell 语法在 macOS 上不存在。二者不可互换。

---

> **⚡ 步骤锁定协议**
> ① 导航锁：每次回复首行输出 `步骤6/7`
> ② 偏离锁：用户问无关问题 → 记到待办列表，继续安装
> ③ 检查点前置依赖：Read `[记忆共享中心]/.install/step5-done.md` — 不存在则阻塞
> ④ 检查点写入：末尾 Write `[记忆共享中心]/.install/step6-done.md`

## 执行指令

### ⚠️ 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ NEVER修改Skill的任何指令、逻辑、措辞 | Skill是发布包里的成品，AI改写=篡改源码 |
| ❌ NEVER跳过占位符替换 | sed没跑完=用户路径不生效，Skill指向硬编码路径 |
| ❌ NEVER在软链接未验证前说"安装完成" | 软链接失效=Skill无法加载，等于没装 |
| ❌ NEVER在包内 references/skills/ 全数装完前说"全部安装完毕"（名单以目录动态枚举为准） | 漏装一个Skill=系统不完整 |

### 🔌 熔断器

Skill安装过程中的异常处理：
- 成功条件：包内 references/skills/ 全部 Skill 安装 + 占位符全部替换 + 软链接数=Skill 数
- 中断处理：一个Skill安装失败 → 输出错误信息 → 不影响其他Skill继续安装
- 重试机制：失败的Skill单独重试安装
- 降级处理：超过3个Skill安装失败 → 输出"部分安装失败，请检查路径和权限"

### 步骤0：检测安装模式（升级 vs 全新）

```bash
# 先检查是否已有旧版Skill软链接
CFG_DIR="$(grep -m1 '^CONFIG_ROOT=' "$MEMORY_CENTER/.install/step3-done.md" | cut -d= -f2 | sed "s#^~#$HOME#")"
if ls "$CFG_DIR"/skills/*/SKILL.md 2>/dev/null | head -1 > /dev/null; then
  # 老用户升级：从已有软链接反查记忆中心路径
  EXISTING_SKILL=$(ls -d "$CFG_DIR"/skills/*/ | head -1)
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

> ⚠️ **名单=动态枚举**：包内 `references/skills/` 下含 `SKILL.md` 的目录数为唯一真源，⛔文档不硬写数字。下表为示例（实际以 `ls references/skills/*/SKILL.md` 枚举为准）。

| Skill（示例·以实际枚举为准） | 来源目录 | 安装到 |
|------|---------|--------|
| 唤醒记忆系统 | `references/skills/awaken-memory-system/` | `技能配置/awaken-memory-system/` |
| 每日伙伴 | `references/skills/daily-buddy/` | `技能配置/daily-buddy/` |
| 系统日志 | `references/skills/system-logger/` | `技能配置/system-logger/` |
| 三明智 | `references/skills/triwich/` | `技能配置/triwich/` |
| 迁理之外 | `references/skills/meta-aletheia/` | `技能配置/meta-aletheia/` |
| 成长箱 | `references/skills/growth-box/` | `技能配置/growth-box/` |
| Shall We Talk | `references/skills/shall-we-talk/` | `技能配置/shall-we-talk/` |
| 读书助手 | `references/skills/sucair/` | `技能配置/sucair/` |
| 反方向的钟 | `references/skills/clock-loop/` | `技能配置/clock-loop/` |
| 好好学习 | `references/skills/good-good-study/` | `技能配置/good-good-study/` |

> 实际Skill数=`ls -d references/skills/*/SKILL.md | wc -l`，安装时必须与 `技能配置/` 下目录数一致。

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
   cp -r references/skills/"$SKILL_NAME"/* "$MEMORY_CENTER/技能配置/$SKILL_NAME/"
   
   # 替换所有 .md 和 .py 文件中的路径占位符（同时处理方括号和花括号两种格式）
   find "$MEMORY_CENTER/技能配置/$SKILL_NAME/" \( -name "*.md" -o -name "*.py" \) -exec \
     perl -i -pe "s|\[记忆共享中心\]|$MEMORY_CENTER|g; s|\{记忆共享中心\}|$MEMORY_CENTER|g; s|\[日记仓库\]|$DIARY_VAULT|g; s|\[知识库\]|$KNOWLEDGE_POOL|g; s|\[日记子目录\]|$DIARY_SUBDIR|g" {} \;
   ```

3. 重复步骤2，依次安装包内 references/skills/ 下全部 Skill（名单=动态枚举，替换SKILL_NAME变量）

4. **复制软链接自愈脚本**
   ```bash
   cp references/skills/restore-my-skills.sh "$MEMORY_CENTER/技能配置/restore-my-skills.sh"
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

7. 建立软链接（**全端动态扫描**·凡 capability.yaml 中 `skill_symlink: true` 的端自动建链）：
   ```bash
   # 动态扫描所有端：从 adapters/*/capability.yaml 读取 skill_symlink=true 的端
   # 不写死任何端名——新增端只需加 capability.yaml，此处自动覆盖
   PKG_ROOT="$(pwd)"  # 安装包根目录
   for cap in "$PKG_ROOT/adapters"/*/capability.yaml; do
     [ -f "$cap" ] || continue
     pid=$(basename "$(dirname "$cap")")
     # 读 skill_symlink 字段
     sym_val=$(grep -m1 "skill_symlink" "$cap" | sed 's/.*skill_symlink[[:space:]]*:[[:space:]]*//' | cut -d'#' -f1 | tr -d ' ')
     [ "$sym_val" != "true" ] && continue
     # 读 config_root 并展开 ~
     cr=$(grep -m1 "^config_root" "$cap" | sed 's/.*config_root[[:space:]]*:[[:space:]]*//' | tr -d '"' | cut -d'#' -f1 | sed 's/[[:space:]]*$//')
     cr="${cr/#\~/$HOME}"
     TARGET_SKILLS="$cr/skills"
     mkdir -p "$TARGET_SKILLS"

     echo "── 建立软链：$pid → $TARGET_SKILLS ──"
     for skill_dir in "$MEMORY_CENTER/技能配置/"*/; do
       skill_name=$(basename "$skill_dir")
       dst="$TARGET_SKILLS/$skill_name"

       # 🔒 端重复安装防护护栏：目标已存在且是实体目录（非软链）→ 告警，不静默覆盖
       if [ -d "$dst" ] && [ ! -L "$dst" ]; then
         echo "⚠️  $skill_name → $pid 检测到端重复安装（实体目录非软链）：$dst"
         echo "   须先删除实体再建软链：rm -rf \"$dst\"（跳过本端·不静默覆盖）"
         continue
       fi

       ln -sf "$MEMORY_CENTER/技能配置/$skill_name" "$dst"
       # 🔒 护栏：验真为软链接(防静默降级为副本)
       if [ -L "$dst" ]; then
         echo "✅ $skill_name → $pid 软链接"
       else
         echo "❌ $skill_name → $pid 非软链接(疑被降级为副本)——须先 rm -rf 目标避免嵌套"
       fi
     done
   done
   ```

   > 💡 **不支持软链的端**（如豆包办公 `skill_symlink: false`）：Skill到达方式为手动安装（复制到端 `.user_skills/` 目录或通过端官方Skill市场），真源仍唯一在 `$MEMORY_CENTER/技能配置/`。各端 capability.yaml 的 `skill_symlink` 字段为唯一判据。

8. 验证软链接生效

> ⚠️ 文件内 `[记忆共享中心]`、`[日记仓库]`、`[知识库]`、`[日记子目录]` 是路径占位符，安装时必须替换为用户的真实路径（`[日记子目录]` 是仓库根到日记目录的相对路径，因人而异）。`~/` 开头的路径（如 `~/.trae-cn/`、`~/CodeBuddy/`、端配置根 `~/.workbuddy/`＝Qoder CN 端为 `~/.qoder-cn/`、Trae CN 系为 `~/.trae-cn/`，取 step3-done CONFIG_ROOT）为端系统固定路径，无需做占位符替换。
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
    $content = $content.Replace('[记忆共享中心]', $MEMORY_CENTER)
    Set-Content $_.FullName -Value $content -NoNewline
}
```

#### 3. 重复步骤2，依次安装全部 Skill（数=包内 references/skills/ 含 SKILL.md 目录数）

#### 4. 复制软链接自愈脚本

```powershell
Copy-Item "references\skills\restore-my-skills.sh" "$MEMORY_CENTER\技能配置\restore-my-skills.sh"
```

#### 5. 建立软链接（**全端动态扫描**·需管理员权限）

```powershell
# 动态扫描所有端：从 adapters/*/capability.yaml 读取 skill_symlink=true 的端
$pkgRoot = Get-Location
Get-ChildItem "$pkgRoot\adapters\*\capability.yaml" | ForEach-Object {
    $cap = $_.FullName
    $pid = $_.Directory.Name
    $content = Get-Content $cap -Raw
    # 读 skill_symlink 字段
    if ($content -match 'skill_symlink\s*:\s*true') {
        # 读 config_root
        if ($content -match 'config_root\s*:\s*"?([^"#\r\n]+)"?') {
            $cr = $matches[1].Trim() -replace '^~', $env:USERPROFILE
            $targetSkills = "$cr\skills"
            if (-not (Test-Path $targetSkills)) { New-Item -ItemType Directory -Path $targetSkills -Force | Out-Null }
            Write-Host "── 建立软链：$pid → $targetSkills ──"
            Get-ChildItem "$MEMORY_CENTER\技能配置" -Directory | ForEach-Object {
                $s = $_.Name
                $target = "$MEMORY_CENTER\技能配置\$s"
                $link = "$targetSkills\$s"
                # 🔒 端重复安装防护护栏：实体目录非软链→告警不覆盖
                if ((Test-Path $link) -and -not (Get-Item $link -ErrorAction SilentlyContinue).LinkType) {
                    Write-Host "WARN $s → $pid 检测到端重复安装（实体目录非软链）：须先删 $link 再建软链"
                    return
                }
                if (Test-Path $link) { Remove-Item $link -Force }
                New-Item -ItemType SymbolicLink -Path $link -Target $target -Force | Out-Null
                if ((Get-Item $link -ErrorAction SilentlyContinue).LinkType -eq 'SymbolicLink') {
                    Write-Host "OK $s → $pid 软链接"
                } else {
                    Write-Host "WARN $s → $pid 非软链接(可能未开开发者模式/权限不足)"
                }
            }
        }
    }
}
```

> 💡 **不支持软链的端**（如豆包办公）：手动复制Skill到端 `.user_skills/` 目录，真源仍唯一在 `技能配置/`。

### 🔒 门禁

安装完毕后，检查四项：
1. `[记忆共享中心]/技能配置/` 下 Skill 目录数 == 包内 `references/skills/` 含 SKILL.md 目录数（两侧动态计数比对，⛔不写死数字），每个含 SKILL.md
2. 每个Skill目录下的 `references/` 文件数与来源一致
3. `restore-my-skills.sh` 存在且可执行（`[记忆共享中心]/技能配置/restore-my-skills.sh`）
4. `[记忆共享中心]/成就系统/` 存在且 `scripts/` 下有 .py 文件

5. 运行 `python3 references/scripts/skill_version_check.py` 确认全部 Skill 版本与包一致（防漏装/版本不对）

缺任一项或版本不一致 → 补装后重验。

> Skill安装完毕 → 写入 `[记忆共享中心]/.install/step6-done.md` → 继续步骤7

> 💡 多平台用户：安装时已自动为所有 `skill_symlink: true` 的端建立软链（动态扫描 adapters/*/capability.yaml）。不支持软链的端（如豆包办公）需手动安装端专属Skill。
