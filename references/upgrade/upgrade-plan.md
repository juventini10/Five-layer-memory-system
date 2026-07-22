# 升级执行指引 — 增量升级流程

> 当用户声明"升级"或安装包 Step1 检测到已安装用户时，走此流程。
> 升级流程不重新跑 Step2-5（身份/路径/问卷/合成），只走以下 A-E 五步。

---

## 前置条件

- Step1 已完成：版本检测 + 版本对比表已输出
- 用户确认升级

---

## StepA：变更摘要展示

Read CHANGELOG.md，从当前版本到目标版本的所有变更摘要，按类别聚合：

| 变更类别 | 内容 |
|---------|------|
| Skill 更新 | [技能名]：vX.Y→vX.Y |
| 系统模板更新 | conffiles 中有改动的文件 |
| 问卷变更 | 新增 / 删除 / 修改的题目 |

→ 输出"本次将升级以下内容" → 请用户确认

---

## StepB：Skill 升级

复用 Step6 的 Skill 安装逻辑（覆盖安装），但仅覆盖目标版本有变动的 Skill。

1. 比对 CHANGELOG 或 SKILL.md 版本号，识别需要升级的 Skill
2. 对每个需升级的 Skill：
   - 备份旧版：`cp -r {记忆共享中心}/技能配置/{Skill名} {记忆共享中心}/记忆琥珀/升级前备份_{timestamp}/`
   - 覆盖新版：`cp -r skills/{Skill名}/* {记忆共享中心}/技能配置/{Skill名}/`
   - 替换路径占位符
3. 更新软链接

> 无变更的 Skill 跳过，不触碰。

---

## StepB.5：记忆琥珀物理哨兵安装/校验

> 记忆琥珀（物理级文件哨兵）是 1.1.0 新增核心组件。老用户从旧版升级**必须补装**——旧版只有"升级前整包备份"，不含新版 fswatch（macOS）/ FileSystemWatcher（Windows）自动监听。本步骤确保升级用户也装上哨兵，不漏安全网。

1. 检测是否已装：`ls {记忆共享中心}/记忆琥珀/engine/amber-backup.sh 2>/dev/null && echo "AMBER_INSTALLED"`
2. 已装且守护在跑（`launchctl list | grep memoryamber` 或 `Get-ScheduledTask MemoryAmberWatch` 存在且状态 Running）→ **跳过本步骤**（幂等，不重复注册）
3. 未装 → 读取 `references/steps/step6.5-amber-install.md`，执行 6.5a–6.5f（按平台装依赖 + 白名单 + 守护 + 首次备份 + 占位符残查）
4. `mode: manual` 降级**仅限**系统版本过低无法装依赖（同 step6.5 熔断器规则），不在此放宽

> ⚠️ 补位说明：1.1.0「记忆琥珀必装」意图此前未接入升级流程，会导致老用户升级后缺物理哨兵。本步骤即补此缺口。

---

## StepC：系统文件对账（三路比较升级 — 核心逻辑）

### 逐文件处理

对于 conffiles 清单中的每个文件，执行以下流程：

```
输入：
  - NEW   = 安装包内的最新版文件
  - OLD   = manifest.md 中记录的旧版 MD5
  - CUR   = 用户当前的文件内容

比较：
  md5_new = MD5(NEW)
  md5_old = MD5(OLD)   ← 来自 manifest.md 快照
  md5_cur = MD5(CUR)

决策：
  md5_new == md5_old AND md5_cur == md5_old → 不动（三方一致）
  md5_new != md5_old AND md5_cur == md5_old → 自动升级（包改了用户没改）
  md5_new == md5_old AND md5_cur != md5_old → 保留用户版（用户改了包没改）
  md5_new != md5_old AND md5_cur != md5_old → 提示用户手工合并
```

### 输出对账报告

| 文件 | 状态 | 动作 |
|:---|:---:|:---|
| CORE.md | 🔄 自动升级 | MD5: a1b2→c3d4 |
| SOUL.md | ✅ 保留用户版 | 用户自定义，新版无变化 |
| 用户基本规则-铁律版.md | ⚠️ 需要你确认 | 官方和本地都有改动 |

### 特殊情况处理

| 场景 | 处理 |
|:---|:---|
| conffiles 中的文件在用户系统不存在 | 直接创建（与全新安装相同） |
| manifest.md 不存在 | 以安装包 version.md 为准，对整个目录重新生成 MD5 快照，三路比较退化为 new vs null vs current |
| 文件路径占位符未替换 | 执行 sed 替换后再比较 |

---

---

## StepD：问卷题目增量

1. 读取旧版问卷答案（记录已答题目数）
2. 对比新版问卷（总题目数）
3. 有新增题目 → 只问新增题，答案追加到已有问卷答案文件
4. 无新增题目 → 跳过
5. **降级场景**：不删已答题目，答案文件不动

---

## StepE：更新 manifest.md

1. 版本号改为与安装包 version.md 一致
2. 对整个记忆共享中心目录重新计算全部文件的 MD5
3. 写入新的 manifest.md

> 写入前 ✅DO 备份旧 manifest.md 到 manifest.md.bak.{版本号}。

---

## StepF：记忆蓝图升级（整目录·单独处理）

> 记忆蓝图是整目录静态资源，不适配 StepC 的三路比较（逐文件 MD5）。按 #23 统一逻辑单独处理。

### 处理流程

```bash
# 检测记忆蓝图是否已存在
ls -d {记忆共享中心}/记忆蓝图/ 2>/dev/null && echo "FOUND_MEMORY_BLUEPRINT"
```

| 检测 | 动作 |
|:----|:----|
| 不存在 | `cp -r references/templates/记忆蓝图/ {记忆共享中心}/记忆蓝图/` → 完事 |
| 存在 + 用户说"不需要更新" | 不动，完事 |
| 存在 + 用户说"需要更新" | ①`mv {记忆共享中心}/记忆蓝图/ {记忆共享中心}/记忆琥珀/备份_{时间戳}/记忆蓝图_` ②`cp -r references/templates/记忆蓝图/ {记忆共享中心}/记忆蓝图/` ③提示"原记忆蓝图已在记忆琥珀备份，如需保留旧内容请自行从记忆琥珀手动取回合并" |

> ⚠️ 记忆蓝图含设计哲学/规范文档，用户可能手动改过（如本地化调整）。覆盖前 MUST 先备份，不静默覆盖。

---

## 升级中断恢复

### 阶段标记

升级开始前：
```
Write {记忆共享中心}/.install/upgrade-in-progress.md
阶段: StepB-Skill升级 / StepB.5-记忆琥珀哨兵 / StepC-系统文件对账 / StepD-问卷增量 / StepE-更新manifest
备份路径: 记忆琥珀/升级前备份_{timestamp}/
```

每完成一个阶段：更新 `upgrade-in-progress.md` 的阶段字段。
全部完成：删除 `upgrade-in-progress.md`。

### 恢复逻辑

下次任何操作检测到 `upgrade-in-progress.md`：
1. Read 阶段字段
2. Read 备份路径
3. 如果中断在 StepB/StepC → 从备份恢复 → 提示用户"上次升级失败，已回滚"
4. 如果中断在 StepD/StepE → 直接从当前阶段继续（问卷和 manifest 中断幂等）

---

## 降级场景

| 场景 | 处理 |
|:---|:---|
| 包版本 < 已安装版本 | output 警告，询问是否降级 |
| 确认降级 | 三路比较逻辑不变（方向无关），仅加规则：**不删已答题目的答案** |
| 拒绝降级 | 正常退出 |
