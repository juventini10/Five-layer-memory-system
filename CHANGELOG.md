# 变更记录

> 本文件记录五层记忆系统·布洛陀版本的版本发布历史。
> 格式遵循 [keepachangelog.com](https://keepachangelog.com)。
>
> 版本号规则：X.0（架构级变更）· X.Y（功能级变更）· X.Y.Z（修复）
>
> **记录口径（维护公约）**：
> - ✅ 记什么：版本间新增的能力、对用户有意义的功能变更、Skill / 模板 / 规则的非脱敏类文件增改与版本同步。
> - 🚫 不记什么：脱敏处理、隐私清理、绝对路径 / 个人标识替换等内部技术操作——用户无需知晓，严禁入档。
> - 每条变更默认从「对用户有什么用」视角写，纯内部保洁动作不写。

---

## [1.3.0] — 2026-07-22

> 新增数据污染检测机制 + 跨平台加固。

### ✨ 新增

- **数据污染检测**：任何安装路径（全量 / 单体 / 重装）启动时自动检测并清理**早期版本遗留的开发样例数据**，还原为标准空白模板；用户自己录入的数据经逐条哈希精确比对**完整保留**，改动前自动 `.pre-decontam.bak` 备份。（`数据污染检测.py` + INSTALL Step 0.5，全量硬门禁 + 三单装前置命令块）
- **模板标准化**：SHADOW / 未知未知 / 成就系统等模板统一为占位符标准形态。

### 🔧 加固

- **数据污染检测脚本跨平台**：强制 UTF-8 stdout，Windows 下不再因输出崩溃；真机 CI（windows-latest）8/8 job 通过。

---

## [1.2.4] — 2026-07-21

> 修复 [1.2.1] 声称已修、实则未落地（或已复活）的成就系统路径 bug——群友真机反馈照出。

### 🐛 修复（成就系统 · [1.2.1] 漏网/复活）

- **成就脚本 `Path("~/...")` 不展开 `~` → 成就读写全失效** — deident 将源码 `/Users/<user>/` 转为 `~/`，但 Python `Path("~/x")` 不自动展开 `~`，致 `DATA_FILE.exists()` 恒 False、`.mkdir()` 在 CWD 造字面 `~` 幽灵目录，成就数据写入错位。[1.2.1] CHANGELOG 声称"修复6文件 `Path("~/x")`→`Path.home()/"x"`"，但发货文件未改（声明与发货不符）。本版真正落地：成就系统 4 脚本 + daily-buddy 同源 2 脚本，共 14 处 `Path("/Users/<user>/x")` → `Path.home() / "x"`，源侧修改经 deident 后进包即正确。
- **影响范围核实**：achievement_tracker.py(4) / update_diary_achievement.py(2) / diary_validator.py(1) / calculate_tomato.py(1) + daily-buddy 同源 achievement_tracker.py(4) / update_diary_achievement.py(2)。仅终端用户受影响（皮叔本机为绝对路径，假阴性）。

### ✨ 新增（发版门禁）

- **smoke-test.sh §13 Python 路径门禁** — 扫描包内 `.py`，命中 `Path("~/...")`/`Path('~/...')` 字面路径（无 expanduser、无 `# path-ok` 豁免）即 FAIL，杜绝此类"deident 后功能坏"的路径再进包。与 §12 编码/BOM 门禁并列。

## [1.2.3] — 2026-07-21

> V1.2.2 Windows 加固的两处漏网补丁——真实用户物理测试（记忆琥珀哨兵）在 PowerShell 5.1 中文环境下抓出。

### 🐛 修复（Windows 记忆琥珀守护 · V1.2.2 漏网）

- **白名单读取中文路径乱码 → 误报"文件缺失"、备份 0** — `amber-backup.ps1` 用 `Get-Content` 读白名单未指定编码，Windows PowerShell 5.1 默认按系统 ANSI(GBK) 解码 UTF-8 中文路径 → 路径乱码 → `Test-Path` 全部落空 → 全量误报缺失、零备份。修复：`Get-Content $WhitelistFile -Encoding UTF8`。（V1.2.2 只给 .ps1 **自身**加了 BOM，未覆盖脚本**读取外部数据**的解码口径——两码事。）
- **`rollback.ps1` 缺失 UTF-8 BOM** — V1.2.2 声称"所有 .ps1 统一存为 UTF-8 with BOM"，`rollback.ps1` 被漏；含中文脚本在 PS5.1 下存在解析/显示乱码风险。修复：补齐 BOM。

### 🔧 变更

- 统一编码口径，消除中文乱码：`amber-backup.ps1` 日志写入、`amber-watch.ps1` watch 日志写入、`rollback.ps1` 差异预览读取（两处）均补 `-Encoding UTF8`。

### ✅ 验证

- 源（`~/.openclaw/scripts`）→ 派生镜像（安装包 `references/`）全链逐行一致；全部 12 个 .ps1 统一 UTF-8 with BOM；无残留未指定编码的中文相关文件 IO（锁文件 PID 为纯 ASCII，不受影响）。

---

## [1.2.2] — 2026-07-21

> 本版聚焦 Windows 端记忆琥珀守护的系统性加固——修复原版在 Windows 上"装完静默失败"的多个根因，并补齐 macOS Apple Silicon 适配。全部改动经真机 CI（Windows PowerShell 5.1/7 + macOS Intel/arm64）验证。

### 🐛 修复（Windows 记忆琥珀守护）

- **进程猝死根因（0xC000013A / STATUS_CONTROL_C_EXIT）** — 原 Task Scheduler 任务动作用裸 `pwsh` + 依赖交互登录会话，登录瞬态控制台关闭时进程被 CTRL+C 信号杀死（34秒~数分钟静默死）。修复：任务动作改用 pwsh **完整路径** + **S4U 登录类型**（脱离交互控制台）+ 双触发器（AtLogOn+AtStartup）+ IgnoreNew 防重入。
- **Windows PowerShell 5.1 中文脚本解析崩溃** — .ps1 存为无 BOM 的 UTF-8 时，5.1 用系统 ANSI 码页误读中文导致解析失败、守护静默不启。修复：所有 .ps1 统一存为 **UTF-8 with BOM**；派生镜像管线（mirror-sync / reverse-guard）同步支持 .ps1 写 BOM，保证不被同步冲掉。
- **ExecutionPolicy=Restricted 下静默失败** — 默认 Restricted 策略下 `pwsh -File 脚本` 被拦。修复：**全链路 4 类调用点**（任务动作 / NSSM / watch→backup 子进程 / 安装命令）统一补 `-ExecutionPolicy Bypass`。
- **watch 事件驱动不稳** — FileSystemWatcher 首次异常/缓冲区溢出即停摆。改为**轮询快照比对**（ErrorActionPreference=Continue + 逐轮 try-catch），与 macOS 同哲学、与内核事件机制解耦。
- **未知未知路由钩子语法错修复（DOA）** — `references/hooks/route_unknown_unknown.py` 因脱敏时剥离 `os.path.expanduser(` 残留 3 处孤儿 `)`，Python 加载即 SyntaxError → 装包用户的 🕳️ 盲区路由钩子从未生效（fail-open 静默）。修复：去孤儿 `)` + parse 通用化（`content is None 才取 message`，兼容 Qoder `{role,message}` 与 WorkBuddy `{role,content}` 两种 transcript 格式）。经真机 CI（Windows + macOS）双格式实测路由成功。

### ✨ 新增

- **NSSM 服务安装（首选路径）+ 安装分发器** — 新增 `amber-install.ps1` 分发器：有管理员权限 + nssm → **NSSM 服务**（SCM 托管，与 macOS launchd 对称，最稳、无 conhost 弹窗、崩溃 5 秒自愈）；否则 → **Task Scheduler 加固版**（免提权回退）。新增 `amber-install-service.ps1`（NSSM 注册）。`scripts/nssm/README.md` 说明可选 NSSM 升级方式。
- **macOS Apple Silicon 适配 + 零依赖回退** — `amber-fswatch-wrapper.sh` 自动探测 fswatch（Intel `/usr/local/bin` / Apple Silicon `/opt/homebrew/bin`）；无 fswatch 时自动退回**轮询模式**（零外部依赖）。

### 🔧 变更

- 记忆琥珀路径模型改为**绝对路径占位符**（`[记忆共享中心]` 安装时替换为绝对路径），兼容 `D:\` 等异盘/自定义记忆中心路径（原"相对家目录拼接"对绝对路径会拼坏）。
- `amber-backup.ps1` 支持 `AMBER_MC` 环境变量重定向（隔离测试 / 服务环境定位）。
- INSTALL.md / step6.5 Windows 分支改调 `amber-install.ps1` 分发器，并拷贝全部 5 个 ps1。

### ✅ 验证

- 真机 CI 6 job 全绿：Windows PowerShell 5.1 功能 / PowerShell 7 功能 / NSSM 服务冒烟 / Task Scheduler 冒烟 / **Restricted 5.1 专项** / macOS(arm64) fswatch探测+轮询回退。

---

## [1.2.1] — 2026-07-20

### ✨ 新增

- **记忆琥珀目录备份引擎** — `amber-backup.sh` 升级支持目录级递归备份。白名单中现在可以写目录路径（如 `记忆规则/`、`记忆蓝图/`），引擎自动递归目录内所有文件，用 `__` 分隔层级生成唯一备份名。用户加一行目录路径即可守护整个目录，无需逐文件列举。
- **记忆琥珀 whitelist 模板扩容** — 新增「记忆规则」段（用户基本规则铁律/详解/摘要 3 份，AI 行为底线）和「记忆蓝图」段（设计依据库，目录级守护，默认注释——有则手动激活，无则不报错）。

- **发布包新增 `.gitignore`** — 防止 macOS `.DS_Store` / Python `__pycache__` / 备份 `.bak` 等杂物进入公开仓库，保持对外发布的仓库干净。

### 🔧 变更

- **成就系统路径 bug 修复** — 成就脚本（含 daily-buddy 同源副本）中 `Path("~/x")` 不自动展开 `~`，导致 `DATA_FILE.exists()` 永久 False、成就读写全失效。修复 6 文件：`Path("~/x")` → `Path.home() / "x"`，安装后成就系统可正常运行。

- **clock-loop 发布版精简** — 剥离「loop 安装包 / 发布包闭环检查」功能（该功能是开发者发布前自检工具，终端用户用不上，且其检查脚本不随包发货）。发布版 clock-loop 聚焦评估 / 循环工程核心能力，行为更清晰。

- **全 Skill 路径泛化** — 9 个 Skill 的 SKILL.md 及 references 中 187 处 `~/个人AI档案/` 硬编码路径全部替换为 `[记忆共享中心]` 占位符。安装步骤 step6 自动将占位符替换为用户真实记忆中心路径（macOS sed + Windows PowerShell 双分支）。彻底解决 Windows / 自定义路径用户的 Skill 文件联动功能静默失效问题。

- **Windows 安装全面补齐** — step6（Skill 安装）与 step6.5（记忆琥珀）新增完整 Windows 分支（PowerShell 复制 + 占位符替换 + 软链接 / Task Scheduler 注册），macOS / Windows 双平台安装流程全覆盖。

### 🐛 修复

- **Windows PS1 脚本全面修复** — 修复群友实测发现的多个缺口：① 路径从 `.openclaw` 改为 `[记忆共享中心]\记忆琥珀\engine\` ② Task Scheduler 任务名 `QClawAmberWatch` → `MemoryAmberWatch` ③ 移除 `#Requires -Version 7.0` 限制（兼容 PowerShell 5.1+）④ `pwsh` 硬编码改为自动检测回退

- **Hook 安装 JSON 反斜杠 bug** — Windows 下 settings.json 中钩子命令路径使用 `\` 与 JSON 转义冲突，导致 `C:\Users\` 被 mangled 为 `C:Users`。修复：路径写入前统一转换为 `/`（Windows 完全兼容）。

- **CHANGELOG 诚实修正** — 删除 [1.1.0] 中 `install-audit.sh` / `install-audit.ps1` 的不实声称（两文件从未进入发布包）。

- **awaken-memory-system 安装缺失修复** — `skills/` 根目录下误置裸 `SKILL.md`（内容为 awaken-memory-system），导致安装脚本无法发现该 Skill。修复：创建 `skills/awaken-memory-system/` 子目录并归位文件，与其他 9 个 Skill 目录结构一致。

- **成就脚本全面硬编码清理** — 包内成就系统 `references/成就系统/scripts/` 和 daily-buddy `scripts/` 共 7 个 Python 脚本中 15 处 `Local_Obsidian_Vault` 个人 vault 名硬编码全部改为 `[日记仓库]` / `[日记子目录]` 占位符。新用户安装时由 step6 自动替换为实际路径，不再因 vault 名不匹配导致日记成就检测静默失效。

- **INSTALL.md 日记占位符双平台补全** — 此前 step6 的 sed（macOS）/ Replace（Windows）链路只替换 `[记忆共享中心]`，遗漏 `[日记仓库]` 和 `[日记子目录]`。修复：macOS bash 和 Windows PowerShell 双分支各补 2 行占位符替换 + `DIARY_VAULT` / `DIARY_SUBDIR` 变量声明，安装后成就系统日记路径可正常解析。

- **发布包垃圾清理** — 清除 `skills/`、`references/skills/` 下残留的 `.DS_Store`（macOS 系统自动生成）和 `.bak`（历史备份共 4 份），确保对外发布的包目录干净。

### 📚 文档

- **记忆琥珀设计哲学 v1.5** — 新增 §十「自救指南·安装与运行故障排查」，覆盖 macOS（心跳检测/监听验证/reload/依赖/日志）和 Windows（任务状态/Python 命令/执行策略/路径占位符）双平台故障诊断流程。

- **指令编写规范 v4.3** — 路径硬编码分级从两级扩至三级：新增「伪安全」档（tilde 路径，目录名为用户自起的不通用名 → 应改为 `[记忆共享中心]/` 占位符）。此前 187 处 `~/个人AI档案/` 被旧版两级判定放行，新规则下将被拦截。

### 🧹 修正

- **安装包 fswatch 去硬编码** — 清除 `amber-fswatch-wrapper.sh` 中开发者本机路径残留，改为通用注释模板「在此追加要受保护的目录」。不影响引擎能力，只是不让私有路径随包发货。

---

## [1.2.0] — 2026-07-19

### ✨ 新增

- **未知未知路由兜底钩子进包（补 1.1.0 断层）** — 1.1.0 在 `references/未知未知/悬置区.md` 文档化了 `route_unknown_unknown.py` 功能（含 macOS 实证），但包裹里既没有装脚本、也没装 hooks、更没有安装步骤——「说明书写了功能、包裹里没发货」。本次把功能真正落到执行机：
  - 新增 `references/hooks/route_unknown_unknown.py`（从活体拷贝，默认路径用 `[记忆共享中心]` 占位符，安装时 sed 替换为真实路径；支持 `UU_TARGET`/`UU_STATE`/`UU_HEARTBEAT` 环境变量重定向便于隔离测试）。
  - 新增安装步骤 `references/steps/step6-hook-install.md`（步骤6 Skill 安装后、步骤6.5 记忆琥珀前自动执行，**不独立计步序**）：拷贝脚本到 `~/.workbuddy/hooks/` + `chmod +x` + sed 替换占位符 + 对 `~/.workbuddy/settings.json` 的 `hooks.Stop` **幂等追加**（保留 `l3_conclusion_guard.py` 等现有钩子，绝不覆盖、按命令去重）。
  - 使 SOUL.md 的 `【🕳️ 我的未知未知】` 段在全新安装后即被 Stop 钩子兜底自动路由到 `悬置区.md`（T5 / AI盲区 / 来源对话 schema），与规范层显式 Write 形成去重双保险。

### 🔧 变更

- **SOUL.md 模板 v1.2→v1.3** — `【🕳️ 我的未知未知】` 段升级为路由闭环三行（规范层须按 §1.6 schema 显式 Write 悬置区.md + Stop 钩子 route_unknown_unknown.py 兜底自动路由 + 去重不重复写入）；版本行补 v1.3 说明。
- **步骤5 补 未知未知/ 安装拷贝** — 5b（全新）复制清单补一行 `cp -r references/未知未知/ [记忆共享中心]/未知未知/`（含悬置区.md/显形台账.md/断言台账.md，钩子写入目标）；5g（升级）补一行（已存在则跳过、不覆盖用户残差条目）。
- **执行文件同步** — 结构树新增 `references/hooks/route_unknown_unknown.py`；步骤流新增「步骤6·钩子安装」段；门禁规则表新增「步骤6·钩子后」检查项；升级路径说明补「步骤6·钩子安装也须执行」。
- **INSTALL.md 入口提及** — 文件角色说明补一句钩子安装随执行引擎自动发生，不改分流逻辑。
- **包版本全链路 1.1.0→1.2.0** — version.md / 执行文件（frontmatter + 标题 + 末尾版本行）/ INSTALL.md（frontmatter + 标题 + 检测输出模板）/ 盲审检查清单 / step1 身份校验输出模板 / step7 验证报告模板 全部同步。

### 🧹 清理

- 无（本次为功能闭环，无残留清理项）。

---

## [1.1.0] — 2026-07-13

### ✨ 新增

- **记忆琥珀物理级文件哨兵（跨平台）** — 新增 fswatch（macOS）/ FileSystemWatcher（Windows）自动监听白名单文件变化，内容哈希去重，让每次破坏性修改都可回滚。与旧版"升级前整包备份"完全不同——新版是物理级、单文件、操作系统自动触发，不依赖 AI 自觉。
  - **跨平台支持**：macOS 用 fswatch + launchd；Windows 用 FileSystemWatcher + Task Scheduler + PowerShell 7+。两端哲学等价、实现各自原生、零额外依赖。
  - **新增文件**（7个）：
    - `references/记忆琥珀/scripts/amber-backup.sh` — macOS 备份脚本
    - `references/记忆琥珀/scripts/amber-backup.ps1` — Windows 备份脚本（PowerShell 7+）
    - `references/记忆琥珀/scripts/amber-fswatch-wrapper.sh` — macOS fswatch 监听 wrapper
    - `references/记忆琥珀/scripts/amber-watch.ps1` — Windows FileSystemWatcher 监听
    - `references/记忆琥珀/scripts/amber-install-task.ps1` — Windows Task Scheduler 注册
    - `references/记忆琥珀/scripts/amber-whitelist.txt.template` — 白名单模板（含占位符）
    - `references/记忆琥珀/scripts/com.memoryamber.backup.plist.template` — macOS launchd 配置模板（中性守护，不绑定单一工具）
  - **新增安装步骤**：`references/steps/step6.5-amber-install.md` — 位于 step6 和 step7 之间，必装（仅在系统版本过低无法安装 fswatch/pwsh 时降级为手动模式）
  - **更新文件**：
    - `references/记忆琥珀/README.md` — 从旧版"升级前整包备份"说明改为新版"物理级文件哨兵"文档
    - `五层记忆系统-布洛陀-执行文件-WorkBuddy版.md` — 新增步骤6.5段落 + 更新文件树
- **设计依据**：`记忆蓝图/02_设计理念/记忆琥珀设计哲学.md` v1.1
- **3 个 Skill 同步进包（未知未知自包含写入改造）**：clock-loop / daily-buddy / shall-we-talk 的未知未知写入逻辑已升级为「自包含」——任一写入方 Skill 在写 `~/个人AI档案/未知未知/` 三文件前，若文件夹或某文件缺失，按包内 `references/unknown-unknown-headers.md` 模板副本自建（含正确表头）再写入，**不再依赖反方向的钟先跑**。
  - clock-loop：悬置区探针写入前加「确认存在否则按模板 Write 创建」引导；`scripts/append_claim.py` 内联 `HEADER_SUSPENSION/HEADER_ASSERT/HEADER_MANIFEST` 三常量，对悬置区.md/断言台账.md/显形台账.md 任一缺失即自建；脚本调用改相对路径 `scripts/`（开源硬要求）。
  - daily-buddy：工作流C 晚间复盘 + 月报 SOP 写入前自检自建（原「不存在则跳过」→「按模板创建再继续」）；SKILL.md 加「🌀 未知未知写入前置」段。
  - shall-we-talk：新增「🌀 盲区轴 T5 路由」段（意识到的盲区→悬置区），含 ⚠️术语区分（区别于本 Skill T5 对抗性测试声明）；锁二路径映射加盲区轴分支。
  - 3 份 `references/unknown-unknown-headers.md`（悬置区/断言台账/显形台账三模板自包含副本）随包分发；SWT 版额外含「⚠️术语区分」段防 T5 歧义。
- **彩蛋保持不动**：本包不含五层说明页 HTML（无 mirrorItems emoji / awk 私人彩蛋文件），本次同步仅涉及 3 个 Skill 代码与模板副本，未触碰任何彩蛋。
- **版本同步**：clock-loop 2.9.9 / daily-buddy 3.16.5 / shall-we-talk 1.1.7（与活源逐字节一致）。
- **clock-loop 正式进包** — 反方向的钟 v2.9.7 加入发布包白名单
- **最伟大的我扩展** — 目录从5扩至8（人生版本/已接受边界/原型试验），README目录说明同步
- **四象限设计确认** — 四象限设计哲学已完成(知识无知矩阵)；未知未知/悬置区确认Skill运行时自动生成(不进包)，clock-loop探针+append_claim.py自动创建目录和文件
- **认知边界探测协议 v1.1** — 信号体系全面升级，从共享引用/迁至记忆蓝图/01_思维方法论/
- **Windows 验证脚本**：`rollback.ps1` 提供 PowerShell 等价实现（⚠️ 本机无 Windows 环境，未实机测试）。

### 🔧 变更

- **记忆琥珀 README.md 全面重写** — 从旧版"升级前整包备份"改为新版"物理级文件哨兵"，新增跨平台操作命令、故障排查、清理规则说明
- **执行文件新增步骤6.5** — 在步骤6（Skill 安装）之后、步骤7（系统验证）之前插入记忆琥珀安装步骤
- **系统文件落点修正**：IDENTITY / SOUL / USER / MEMORY 4 个平台系统文件安装时写入 `~/.workbuddy/`（原错误写入 `[记忆共享中心]`/归档根，导致不生效）。安装器（step5/执行文件）、回滚（rollback.sh）、成就同步（achievement_tracker.py）全链路对齐。
- **老用户迁移步骤**：5g 升级前检测归档根残留的系统文件并迁移至 `~/.workbuddy/`。
- **9个Skill全量同步** — 全部同步至权威源最新版本（含clock-loop新增）
- **系统文件模板升级** — SOUL.md v1.1→v1.2（🕳️+敢于说出来+品格版提醒）/ MEMORY.md v1.0→v1.2（硬路牌+最伟大/未知未知路径）/ 情境层快照新增v1.0（核心文件健康+成长箱速览）
- **用户基本规则 v7.8.1→v7.8.2** — 三层同步：执规-004扩展"改核心文件前须先确认"、摘要版补「🕳️🕳️」
- **SOUL.md品格化** — 系统日志提醒从✅DO指令转为品格宣言（本地v3.8→v3.9）
- **共享引用目录删除** — 认知边界探测协议迁入记忆蓝图后，共享引用/目录移除
- **盲审检查清单移根目录** — 从references/移至发布包根目录
- **包版本 → 1.1.0（对外发布起始点）** — 3 Skill 未知未知写入不再绑定反方向的钟，开箱即用更稳；本段合并 1.0.3 之后的内部迭代（原 [1.1.0]×2 与不规范 [1.10] 段）。

### 🧹 清理

- .DS_Store清理、路径一致性校验通过、零残留

---

## [1.0.3] — 2026-07-06

### 🔧 变更

- **8个核心Skill全量同步** — daily-buddy(v3.14.0)、shall-we-talk(v0.6.3→v0.8.0)、triwich(v3.8.0)、awaken-memory-system(v7.9)、growth-box(v1.4.1)、system-logger(v3.5.2)、reading-assistant(v3.13.0)、meta-aletheia(v3.2.1)
- **Shall We Talk 升级至 v0.8.0** — 新增铁律0（AI不附和用户）、Step 2.5起点角度选择（元规则+AB实测数据）、盘点点机制（第4问轻扫描+第6问强制）、第7/8问接力结构（挑战→方向盘）
- **Skill目录名英文化** — 8个Skill目录从中文名改为英文名（如每日伙伴→daily-buddy）
- **记忆蓝图同步** — 16个已有文件更新到最新版本，无新增
- **用户基本规则三层文件同步** — 摘要版/铁律版/详解存档版与主源对齐
- **最伟大的我/README.md** — 蒸馏流程自包含化，移除外部文档依赖
- **CHANGELOG版本号更新** — 同步各Skill实际版本号（原v1.0.2记录的版本号已过期）
- **SOUL模板版本号 v1.0→v1.1** — 产出签名时间格式已更新

### 📦 文件变更

| 文件 | 变更 |
|:-----|:-----|
| `references/skills/*/` | 🔄 目录名英文化（8个Skill） |
| `references/skills/shall-we-talk/SKILL.md` | 🔄 v0.6.3→v0.8.0 |
| `references/templates/记忆蓝图/` | 🔄 全量同步（16个文件） |
| `references/templates/用户基本规则-*.md` | 🔄 更新（3个文件） |
| `references/最伟大的我/README.md` | 🔄 蒸馏流程自包含化 |
| `CHANGELOG.md` | 🔄 新增v1.0.3条目 |

---

## [1.0.2] — 2026-06-30

### 🔧 变更

- **8个核心Skill同步到最新版本** — 唤醒记忆系统(v7.9)、每日伙伴(v3.12.0)、系统日志(v3.5.0)、三明智(v3.4.3)、迁理之外(v3.2.1)、成长箱(v1.3.1)、Shall We Talk(v0.4.0)、读书助手(v3.1.1)
- **Skill架构规范升级为四文件体系** — v4.2→v5.1，新增`Skill标准规范.md`+`Skill设计模式.md`+`Skill模板与来源.md`+`README.md`
- **开发规范目录更新** — README.md路由规则更新+五层记忆系统.md文件结构图更新
- **署名统一整改** — 全包所有规范文件/Skill文件署名统一为"皮叔"
- **指令编写规范引用更新** — 3处引用从`Skill架构规范.md`→`Skill架构规范/`（目录）
- **铁律声明格式升级** — CRITICAL→✅DO/⛔DO NOT（五级强制标注）
- **新增内容** — 质量与证据声明+Alternatives Considered段+Poka-Yoke防误层
- **Skill架构规范自治性修复** — 5文件8处改动：元文档声明/阅读引导合入/D5补Lost in the Middle引用/500行诚实标注(经验值)/删除200行矛盾/U型曲线补论文引用/Progressive Disclosure经验平衡点/删除README.md
- **Skill架构规范 v5.1→v5.2** — 质量评分体系全面升级（13维度×100分制+T1-T4权重+闯关制G1-G3+S5跨文件一致性检查）+ skill_eval.py v1.1 + 新增 references/CHANGELOG.md 头部瘦身
- **增量升级体系建立** — 新增 version.md + conffiles 清单 + upgrade-plan.md(StepA-E三路比较升级流程) + manifest-template.md + Step1版本检测及升级路径决策 + Step7 manifest.md 自动生成
- **系统日志统一命名：任务日志→系统日志** — 文件名/格式/模板/概念引用全面统一，消除口头叫法（系统日志）与文件名（任务日志）的矛盾。涉及系统日志SKILL.md（10处）+ 每日伙伴references（6处）+ 发布包同步 + 43个旧文件重命名
- **指令编写规范升级 v3.2→v3.5** — 同步五级标注体系、§5.7 Poka-Yoke、§5.8 Alternatives Considered、§5.9 文件类型识别，自检清单16→17项（新增"每条规则正文含⛔DO NOT/✅DO标注"检查）
- **用户基本规则三层文件对齐指令规范v3.5** — 摘要版+铁律版+详解存档版全面改写：五级标注对齐（必须→⛔DO NOT/✅DO+因果链）、摘要版补三张答题表+信号表+12行速查、铁律版补五层防线+记忆排除清单+自检清单、详解版标注改写。版本v1.0→v1.1，反哺本地版
- **每日伙伴SKILL.md v3.11.1→v3.12.0** — 日记模板新增📊里程碑SECTION+工作流C新增7a反哺快照步骤+禁止行为#5扩至四段+语义假阳性修复
- **系统日志SKILL.md v3.4.2→v3.5.0** — 日志模板新增`完成`字段（时间HH:MM取自产出签名），必填字段7→8，格式校验同步
- **SOUL模板签名格式更新** — 产出签名`[图标｜摘要｜YYYY-MM-DD HH:MM]`+行为印证品格追加时间来源
- **系统日志SKILL.md v3.5.0→v3.5.1** — 新增步骤6：追加调用计数器（自动化链路闭合），在完整性锁之后、月度蒸馏之前执行

### 🐛 修复

- **问卷Q18选项渲染问题** — 移除选项前的emoji（🌿😣💪🌀），避免腾讯问卷平台解析失败
- **每日伙伴月报/周报路径错误** — 3类路径修复：日记目录 `每日日记/`→`01-日记/`、WorkBuddy日志指向旧CodeBuddy路径、系统日志文件名格式（`{当月}`→`YYYY-MM-DD`），共6处

### 📦 文件变更

| 文件 | 变更 |
|:-----|:-----|
| `references/skills/*/SKILL.md` | 🔄 同步（8个Skill） |
| `references/skills/*/references/` | 🔄 同步（references文件） |
| `references/templates/记忆蓝图/开发规范/Skill架构规范/` | 🆕 新增（四文件体系） |
| `references/templates/记忆蓝图/开发规范/Skill架构规范.md` | 🔴 删除（被目录替代） |
| `references/templates/记忆蓝图/开发规范/README.md` | 🔄 更新（路由规则） |
| `references/templates/记忆蓝图/开发规范/指令编写规范.md` | 🔄 更新（引用修正） |
| `references/templates/记忆蓝图/五层记忆系统.md` | 🔄 更新（文件结构图） |
| `references/questionnaire.md` | 🔧 修复（Q18选项） |
| `references/skills/系统日志/SKILL.md` | 🔄 统一命名（10处：文件名/格式/模板 → 任务日志改系统日志） |
| `references/skills/每日伙伴/references/monthly-review-sop.md` | 🔧 修复（3类路径校正） |
| `references/skills/每日伙伴/references/monthly-review-spec.md` | 🔄 统一命名（4处概念引用修正） |
| `references/skills/每日伙伴/scripts/check_diary_titles.py` | 🔧 修复（每日日记→01-日记） |
| `references/templates/记忆蓝图/开发规范/指令编写规范.md` | 🔄 更新（v3.2→v3.5+自检清单17项） |
| `references/templates/用户基本规则-摘要版.md` | 🔄 更新（v1.0→v1.1：补三张答题表+信号表+12行速查+禁止因果链） |
| `references/templates/用户基本规则-铁律版.md` | 🔄 更新（v1.0→v1.1：五层防线+记忆排除清单+自检清单+标注对齐） |
| `references/templates/用户基本规则-详解存档版.md` | 🔄 更新（v1.0→v1.1：标注改写+因果链补充） |

---

## [1.0.1] — 2026-06-27

### 🔧 变更

- **平台声明诚实化** — INSTALL.md compatibility 从六端（workbuddy, qclaw, trae, trae-solo, wukong, qoderwork）→ 仅 workbuddy。1.0 实际只支持 WorkBuddy，声明应与事实一致。
- **开发规范同步** — 包内 Skill架构规范 v4.1→v4.2（§三CHANGELOG显式列出+§九自检第11项）、指令编写规范 v3.1→v3.2（互引版本号漂移修复）
- **版本号全包统一** — INSTALL.md / 执行文件 / 脚本（smoke-test / integration-test / rollback / restore-my-skills）/ step文件（step1 / step7）/ 盲审检查清单 全部从 1.0→1.0.1；执行文件重命名（`布洛陀1.0` → `布洛陀1.0.1`）；模板出处声明（"布洛陀1.0通用骨架"等）保留原值不变
- **Skill 全量同步** — 以开发源为权威版本，同步至最新：迁理之外（补5个哲学追问指南）、系统日志（spec版本引用更新）、读书助手（name字段+历史格式）、每日伙伴（QUICKSTART/SKILL.md/monthly-review-sop/weekly-review-sop 内容同步）

### 🆕 新增

- **validate-template.sh** — 洞察报告 HTML 模板变量验证脚本（218 个唯一变量 · 23 章节覆盖 · 模拟填充测试）
- **integration-test.sh** — 端到端集成测试（模拟 7 步安装流程：创建目录 → 问卷 → 文件合成 → Skill安装 → 系统验证 → 洞察报告 → 冒烟联动）
- **sync-check.sh** — 开发源 vs 发布包差异检查脚本，发布前跑一遍快速发现哪些文件需要同步
- **smoke-test.sh 增强** — 新增 §7 平台一致性检查 + §8 洞察报告模板验证，修复 PACKAGE_DIR 指向
- **5个Skill CHANGELOG补全** — Shall We Talk（v0.1→v0.2.3完整迭代史）、成长箱（v1.0→v1.2.0）、迁理之外（v2.1→v3.1.5）、系统日志（v3.0→v3.4.1）、读书助手（v2.1→v3.0.0），数据源：更新日志.md + SKILL.md header

### 🐛 修复

- smoke-test.sh PACKAGE_DIR 指向 scripts/ 而非包根目录

---

## [1.0] — 2026-06-27

### 🆕 新增

- **成就系统** — 8类正向轨（番茄/阅读/日记/早睡/早起/内容创作/运动/通用打卡）+ 1类反向轨（月亮之子），联动最伟大的我
- **INSTALL.md** — 统一安装入口，AI 收到"执行安装"后自动检测并分流新老用户
- **path_utils.py** — 统一路径配置，非标日记路径用户改一行即可
- **情境层目录** — 记忆系统 L4 层独立，动态状态快照迁移至此
- **restore-my-skills.sh** — 软链接自愈脚本，由唤醒记忆系统调用自动修复死链接
- **CHANGELOG.md** — 版本发布变更记录（本文件）

### 🔧 变更

- **安装流程重构** — 从"新老用户不同命令" → 统一一句 `"读取这个安装包，执行安装"`
- **五大升级** — 记忆扎根 / 规则分层 / 八大Skill联动 / 行为反馈 / 记忆蓝图
- **step4/step5 对调重命名** — 问卷→文件合成顺序优化（step4-questionnaire.md / step5-file-synthesis.md）
- **用户基本规则-铁律版** — 6处加强：易漏提醒块、思考链编号列表、产出签名条件强化、空行分隔要求、署名回头看、铁律-009口诀补全

### 🐛 修复

- 3 处字面字串修复（diary_validator.py）
- `[记忆中心]` → `[记忆共享中心]` 全局统一
- SHADOW.md 路径统一到 `潜意识层/SHADOW.md`
- 动态状态快照路径统一到 `情境层/动态状态快照.md`

### 📦 文件变更

| 文件 | 变更 |
|:---|:---:|
| `INSTALL.md` | 🆕 新增（统一入口） |
| `CHANGELOG.md` | 🆕 新增（本文件） |
| `UPGRADE.md` | 🔴 删除（功能由 INSTALL.md 自动分流替代） |
| `references/成就系统/` | 🆕 新增（17文件） |
| `references/记忆蓝图/成就系统设计哲学.md` | 🆕 新增 |
| `references/steps/step4-file-check.md` | 改名为 `step4-questionnaire.md` |
| `references/steps/step5-questionnaire.md` | 改名为 `step5-file-synthesis.md` |

### ⚠️ 安装说明

> 新老用户统一命令：
>
> ```
> 读取这个安装包，执行安装
> ```
>
> AI 自动检测用户类型并路由到对应流程：
> - **新用户**：引导回答 33 题 → 生成系统文件 → 完成安装
> - **老用户**：自动搜索历史问卷 → 比对系统文件差异 → 展示确认 → 备份旧文件 → 更新完成

