---
name: 五层记忆系统-布洛陀1.3.1
description: >
  布洛陀 1.3.1 执行文件。引导用户完成记忆系统初始化：答题产生数据、合成个性化文件、Skill安装、未知未知路由钩子安装、记忆琥珀安装、系统验证。
  注意：这是子流程文件，AI 入口是根目录的 INSTALL.md。
target_platform: WorkBuddy
author: 皮叔（五层记忆系统 · 布洛陀版本 v1.3.1）
license: MIT
version: 1.3.1
compatibility: workbuddy
---

# 五层记忆系统 布洛陀 1.3.1 — 执行文件

> 🔴 本文件是安装流程的执行引擎。不是建议，是硬约束。不可跳过。
> 🔴 所有 7 步必须按顺序执行，每一步先读 step 文件再做。

> 📅 版本：布洛陀 1.3.1 | 🎯 目标平台：WorkBuddy | 📦 安装包结构：INSTALL.md（入口）+ references/ 按需加载
> 🆕 布洛陀 1.2.1：新增「步骤6·钩子安装」子步骤——未知未知路由兜底钩子 route_unknown_unknown.py 挂入 settings.json 的 hooks.Stop，使 🕳️ 盲区段开箱即被自动路由到悬置区（1.1.0 仅文档化未发货，本次补断层）

> 🏮 欢迎使用五层记忆系统·布洛陀 1.3.1。
> 取名源自壮族智慧先祖，新版搭载三大思维，做你的专属智囊。
> 它熟记你的点滴，懂你所思，往后相见皆是旧识。

> ⚠️ **AI 注意**：如果用户直接告诉你去读"执行文件"，你也先读 `INSTALL.md` 做分流检测再回到这里。
> INSTALL.md 包含完整的自动分流逻辑（检测+路由），不是"一段说明"——必须读，不能跳过。

---

## 📦 安装包结构

```
五层记忆系统-布洛陀1.3.1/
├── INSTALL.md                                        ← 🚪 唯一入口（AI 先读这个做分流）
├── CHANGELOG.md                                      ← 📋 版本记录
├── rollback.sh                                       ← 🔄 一键回滚脚本
├── scripts/
│   └── smoke-test.sh                                 ← 🧪 发版前冒烟测试
├── LICENSE                                           ← MIT 开源协议
├── README.md                                         ← 产品简介（给人看的）
├── 盲审检查清单.md                                    ← Agent B 独立合规审计
├── 五层记忆系统-布洛陀-执行文件-WorkBuddy版.md    ← ⚙️ 执行引擎（分流后按步骤加载）
└── references/
    ├── steps/                                    ← 初始化步骤（按需加载）
    │   ├── step1-identity-check.md               ← 系统身份校验
    │   ├── step2-basic-identity.md               ← 基础身份确认
    │   ├── step3-path-setup.md                   ← 路径配置
    │   ├── step4-questionnaire.md               ← 问卷填写（全新用户先答题产生数据）
    │   ├── step5-file-synthesis.md               ← 文件合成（答题数据+干净模板→个性化文件）
    │   ├── step6-skill-install.md                ← Skill 安装
    │   ├── step6.5-amber-install.md             ← 记忆琥珀（物理级备份）
    │   └── step7-verification.md                 ← 系统验证
    ├── questionnaire.md                          ← 33题问卷原文
    ├── templates/                                ← 系统模板（含变量占位符，安装时按需合成/复制）
    │   ├── IDENTITY.md                           ← 声明式
    │   ├── SOUL.md                               ← 品格式（五段骨架）
    │   ├── USER.md                               ← 描述式
    │   ├── MEMORY.md                             ← 跨会话记忆
    │   ├── SHADOW.md                             ← 潜意识层
    │   ├── 用户基本规则-铁律版.md
    │   ├── 用户基本规则-摘要版.md
    │   ├── 用户基本规则-详解存档版.md
    │   ├── 情境层-动态状态快照.md
    │   ├── TTL注册表.md
    │   ├── 记忆蓝图/                             ← 设计文档（整目录复制）
    │   │   ├── 五层记忆系统.md
    │   │   ├── 三大思维白皮书.md
    │   │   ├── 用户基本规则设计哲学.md
    │   │   ├── 品格设计通用规范.md
    │   │   ├── MEMORY设计哲学文件.md
    │   │   ├── 成就系统设计哲学.md               ← 新增
    │   │   ├── 品格设计/
    │   │   │   └── WorkBuddy品格设计哲学文件.md
    │   │   └── 开发规范/
    │   ├── 自定义层/README.md
    │   ├── 洞察报告-生成模板.html                ← 221个{变量名}占位符
    │   └── 底层洞察与协作契约报告模板.md          ← AI指令文件
    ├── 最伟大的我/                               ← 个人成长空间（整目录复制，含骨架+README）
    │   ├── README.md
    │   ├── 自画像/
    │   ├── 成就证据/
    │   ├── 认知发现/
    │   ├── 回避模式/
    │   └── 变化轨迹/
    ├── 成就系统/                                 ← 每日伙伴配套子系统（含scripts/ + 成就定义文件）
    │   ├── README.md
    │   ├── 成就速查.md
    │   ├── 番茄成就.md
    │   ├── 阅读成就.md
    │   ├── 健康成就.md
    │   ├── 月亮之子成就.md
    │   ├── 内容创作成就.md
    │   ├── 运动成就.md
    │   ├── 通用打卡成就.md
    │   ├── achievement_notify.sh
    │   └── scripts/
    │       ├── achievement_tracker.py            ← 成就检测引擎（含 最伟大的我 联动）
    │       ├── update_diary_achievement.py
    │       ├── achievement_hook.py
    │       ├── calculate_tomato.py
    │       ├── diary_validator.py
    │       └── check_achievements.sh
    ├── 记忆琥珀/README.md                        ← 物理级文件哨兵说明
    ├── 记忆琥珀/scripts/                         ← 备份脚本（跨平台）
    ├── references/skills/                        ← 9个Skill（每个含SKILL.md+references/）
    │   ├── 唤醒记忆系统/
    │   ├── 每日伙伴/
    │   ├── 系统日志/
    │   ├── 三明智/
    │   ├── 迁理之外/
    │   ├── 成长箱/
    │   ├── Shall We Talk/
    │   └── 读书助手/
    ├── hooks/                                    ← 未知未知路由兜底钩子
    │   └── route_unknown_unknown.py              ← Stop 钩子（占位符版，安装时 sed 替换 [记忆共享中心]）
    └── restore-my-skills.sh                      ← 软链接自愈脚本
```

> ⚠️ 本文件和 references/ 目录配套分发。

---

## 🚀 执行指令

你现在是一份记忆系统初始化执行引擎。你的任务：**执行 7 步初始化流程，每一步必须按序完成。**

### 执行铁律

1. **加载即执行**：读完本文件后，立即从步骤1开始执行。不停顿、不提问。
2. **每步必读**：NEVER跳步——执行每一步前，必须对应的读 `references/steps/stepX.md`。
3. **全部自动化**：用户只回答问题，所有文件创建、目录建立、Skill安装由你完成。NEVER让用户做"你来做"之外的操作。
4. **模板直拷不改写**：所有模板、Skill、附件都是发布包里的成品。安装过程只做 复制+路径替换，NEVER修改内容——原因是这些文件已经过修订验证，AI改写=篡改成品。

### 🔒 流程锁规则

> 安装流程执行时，AI 没有权利跳过步骤或改变顺序。每步的检查点文件是唯一的通行证。

1. **步骤顺序不可逆**：必须按 1→2→3→4→5→6→7 依次执行，不允许跳步。
   正确做法：每一步结束后，确认产出物已生成，Write 检查点文件，然后自动进入下一步。

2. **前置步骤未完成 → 阻塞**：执行当前步骤前，必须 Read 上一步的检查点文件 `{记忆共享中心}/.install/stepX-done.md`。文件不存在 → 提示"请先完成第X步"，不执行。
   正确做法：先 Read 检查点 → 文件存在则继续 → 文件不存在则提示用户完成上一步 → 等确认后继续。

3. **检查点文件必须写入**：每步执行完毕后，Write `{记忆共享中心}/.install/stepX-done.md`（内容：步骤名+完成时间+产出物简述），作为步骤完成的唯一凭证。
   正确做法：每步收尾时，先确认产出物已实质性完成 → 再 Write 检查点文件 → 然后进入下一步。
   
4. **产出物验证**：每步的 `📦 产出物` 必须实质性完成（文件写入成功 / 用户确认），不能仅"在对话中讨论过"就算完成。
   正确做法：每步的 📦 声明了什么，就 Read 验证该文件是否存在且有内容。不能只看"AI说过做完了"。

---

## 初始化流程

### 步骤1：系统身份校验
> 读取 `references/steps/step1-identity-check.md`

确认当前平台为 WorkBuddy，输出版本信息和系统架构。检测是否为老用户。

### 步骤2：基础身份确认
> 读取 `references/steps/step2-basic-identity.md`

询问用户的称呼、基本画像。记录到 USER.md。

### 步骤3：路径配置
> 读取 `references/steps/step3-path-setup.md`

确认记忆文件存放路径（记忆共享中心），创建目录结构。

### 步骤4：问卷填写（先答）
> 读取 `references/steps/step4-questionnaire.md` → 问卷原文见 `references/questionnaire.md`

**必须完成** 33 题问卷，每题依次提问，全部答完才能进入下一步。

**升级用户**：走4b旧版拆分 → 步骤5升级合并 → **步骤6·钩子安装**（与 Skill 无关，全新/升级都须执行，使 🕳️ 路由闭环生效）→ **步骤6.5 记忆琥珀哨兵安装（未装则装、已装则校验跳过）** → 步骤7验证。Skill 升级见 upgrade-plan.md StepB（不走步骤6，但钩子安装仍须独立跑）。

### 步骤5：文件合成（后建）→ 升级合并
> 读取 `references/steps/step5-file-synthesis.md`

**全新用户**：答题数据 + 干净通用模板 → 合成完整个性化文件（摘要版认知层/行为层/协作契约 + SOUL.md品格注入 + USER.md + CORE.md + SHADOW.md + MEMORY.md通用骨架）。

> 📍 **落点分工**：IDENTITY / SOUL / USER / MEMORY 4 个系统文件写入 `~/.workbuddy/`（平台系统文件专属落点）；其余内容文件（CORE/SHADOW/记忆规则/情境层/记忆蓝图/最伟大的我/README/开发工具）写入 `[记忆共享中心]`。系统文件写别处即不生效。

**升级用户**：备份4个系统文件 → 模板骨架+旧数据注入 → 写入v1.0标准版。详见 step5 的 5g 段。

### 步骤6：Skill 安装
> 读取 `references/steps/step6-skill-install.md`

安装 9 个 Skill 到技能配置目录，建立软链接。

### 步骤6·钩子安装（未知未知路由兜底）
> 读取 `references/steps/step6-hook-install.md`（步骤6 完成后、步骤6.5 之前自动执行，**不独立计步序**）

拷贝 `references/hooks/route_unknown_unknown.py` 到 `~/.workbuddy/hooks/` + sed 替换 `[记忆共享中心]` 占位符 + 对 `~/.workbuddy/settings.json` 的 `hooks.Stop` **幂等追加**（保留现有钩子，不覆盖）。
使 SOUL.md 的 `【🕳️ 我的未知未知】` 段在全新安装后即可被 Stop 钩子兜底自动路由到 `悬置区.md`——把「说明书写了功能、包裹里没发货」的断层补上。

### 步骤6.5：记忆琥珀安装
> 读取 `references/steps/step6.5-amber-install.md`

安装物理级文件哨兵——fswatch（macOS）/ FileSystemWatcher（Windows）自动监听白名单文件变化，内容哈希去重，让每次破坏性修改都可回滚。跨平台支持，零额外依赖。

### 步骤7：系统验证
> 读取 `references/steps/step7-verification.md`

验证所有文件已创建、Skill 已安装、规则已注入。输出初始化完成报告。

### 步骤7.5：身份文件注入 & 盲审验证
> 读取 `references/steps/step7-verification.md` 的"步骤7.5"段 + `盲审检查清单.md`（发布包根目录）

**新用户（IDENTITY.md不存在）**：验证步骤5生成的文件是否完整正确 → 全量33题映射核对 + 风格合规检查 + Agent B盲审

**升级用户（IDENTITY.md存在，step5已合并4系统文件）**：step5已完成IDENTITY/SOUL/USER/MEMORY.md的模板合并，本步骤处理剩余文件 + 盲审验证。两个选择：
- 🅰️ 轻量注入 — 仅升级CORE/SHADOW/摘要版/动态状态快照 + 三层.mdc规则注入 + 盲审
- 🅱️ 完全重构 — 从 `问卷答案汇总.md` 重新合成CORE/SHADOW/摘要版/动态状态快照 + .mdc规则注入 + 盲审

两条路径都输出统一验证报告，通过Agent B独立盲审后才能写入。

---

## 初始化完成后

1. **输出完成报告**：列出所有已创建的文件和已安装的 Skill
2. **提示说"我美吗"**：测试系统是否正常工作
3. **提示配置自定义指令**：在 WorkBuddy 设置中添加意图分类格式

---

## 🔒 门禁规则

| 门禁位置 | 检查内容 | 不通过则 |
|:--:|------|------|
| 检查点链 | 每步执行前Read前置检查点`.install/stepX-done.md` | 文件不存在 → 阻塞，提示先完成上一步 |
| 步骤4后 | 33题是否全部答完 + 两段验证（题目+答案）| 回到步骤4补答 |
| 步骤5后 | `[记忆共享中心]/核心层/CORE.md` 已创建且有内容 | 回到步骤5重写 |
| 步骤5后 | `~/.workbuddy/` 下 IDENTITY/SOUL/USER/MEMORY 4 文件已生成且有内容 | 回到步骤5重写 |
| 步骤6后 | `[记忆共享中心]/技能配置/` 下有 9 个 Skill 目录 + restore-my-skills.sh 存在可执行 + `成就系统/`存在且scripts/有.py | 补装后重验 |
| 步骤6·钩子后 | `~/.workbuddy/hooks/route_unknown_unknown.py` 存在可执行 + `~/.workbuddy/settings.json` 的 `hooks.Stop` 含该钩子命令（占位符已替换为真实路径） | 回到步骤6·钩子重装 |
| 步骤7后 | CORE.md 有内容 + 目录结构完整 + 9 个 Skill 软链接全部生效 | 回到对应步骤修复 |

---

## 📖 配套文档


---

版本：布洛陀 1.3.1（2026-07-22）
