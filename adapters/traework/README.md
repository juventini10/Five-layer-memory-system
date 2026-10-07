# Trae Work Adapter（v2.0 合并包·adapters/traework/）

> Trae Work 是**纯 rules/alwaysApply 注入端**：无 CC 式 hooks（`hooks_event=false` 平台边界·非「待开启」）。
> 端特有机制 = **launchd patrol 拉模式**（30min 定时巡检，替代 hook 事件驱动）。

## 安装流程（Step0 选 traework 后）

1. `install_scripts.py --platform traework "<记忆共享中心>"` →
   - **公共资产照装**：①脚本中心（`references/scripts` + `references/hooks` + 知识联邦引擎-min）／①a 数字分身套件／①b 规则层运行时数据。
   - **②③ 钩子部署/注册跳过**（`hooks_event=false`·合法降级）。
   - 读 `capability.yaml` 的 `install_entry` 委派到本 adapter 的 `setup.sh`（条文 13：单一真源·返回码透传）。
2. **rules/ 注入**（本质承载通道·落盘到 `~/.trae-cn/user_rules/`）：
   - ⚠️ **2026-09-30 机制纠正**：Trae Work(`TRAE SOLO CN`) 与 TraeCode(`Trae CN`) 的 `product.json` `dataFolderName` **同为 `.trae-cn`** ⇒ 全局规则目录**物理共用**，目录级隔离不存在。本端规则层 = `~/.trae-cn/user_rules/`（每回合注入的实读目录）；`~/.trae/user_rules/` 是 peer 目录（`ICUBE_PEER_USER_DATA_DIRS`）·本端不读·写了不生效。
   - **落盘形态 = 实体拷贝（`cp`·⛔非软链）**：`setup.sh` 用 `cp` 把 `rules/core-soul.md` → `SOUL.md`、`core-user.md` → `USER.md` 等**实体落盘**到用户自己的 `~/.trae-cn/user_rules/`——系统文件写入用户对应目录，⛔**不做共享文件软链接**（端自己的系统文件 100% 适配·2026-10-07 去软链）。落盘后即端内实体基线，与记忆中心脱钩（共享核心后续改动不再自动同步）。
   - **名映射契约（条文 12）**：adapter 承载名 → 本端注入名，见下表；落盘时 `setup.sh` 做映射，⛔不直落承载名。**本机已有标准名档 → 存在不覆盖**（保本地真身/私人版）。
3. **skills/ 落盘**：
   - **童灵专属 Skill（2 件·`skills/doenglingz-guard` / `skills/doenglingz-slice-nav`）→ 实体直落 `~/.trae-cn/skills/`**（真目录·⛔不进 `<MC>/技能配置/`）。
     ⚠️ **2026-10-06 端串用根治**：此前落 `<MC>/技能配置/`，被 `restore-my-skills.sh` 的「全端软链」机制分发到 Qoder/WorkBuddy/Hermes/ZCode 等异构端＝串端/冒用（实测 5 端 21 条死链）。改直落端原生消费目录 ⇒ 不进共享权威源 ⇒ 全端软链机制自然不碰。
   - **通用 Skill（`references/skills/*`）→ 软链**指向记忆中心技能配置（`restore-my-skills.sh`·端中立·全端共享）。
4. **数字分身恒驻核**（`doenglingz-core.md`）：由 `setup.sh` 从 `<MC>/数字分身/K2切片蒸馏/slices/{core_slice,L6_反向约束}.md` **现场组装**——⛔包内不携带静态分身核（人格由使用者自己的规格书生成·per-user·反漂移）。
5. **launchd patrol 接入**（端独有机制·非 hook 事件）：
   - `scripts/route_traework_patrol.sh` → `<MC>/开发工具/Skill路由引擎/scripts/`（占位符 `[记忆共享中心]` 落盘时替换）
   - `scripts/com.buluotuo.traework.patrol.plist` → `~/Library/LaunchAgents/`（占位符→真实路径）
   - `scripts/install_launchd.sh` → bootstrap，沙盒被拒时打印手动指令。

## 名映射表（承载名 → 本端注入名·条文 12）

| adapter 承载名 | 本端注入名 | 说明 |
|---|---|---|
| `core-identity.md` | `IDENTITY.md` | 身份声明（端中性·双端判定表） |
| `core-memory.md` | `MEMORY.md` | 跨项目长期记忆硬路牌 |
| `core-soul.md` | `SOUL.md` | 品格核心（通用骨架·占位符待答题填充） |
| `core-user.md` | `USER.md` | 用户画像（通用骨架） |
| `execution-guidelines.md` | `trae_solo_rules.md` | 执行准则·顶层指令（通用版） |
| `intent-signature-check.md` | `intent-signature-check.md` | 同名直落 |
| `skills/doenglingz-guard/` | `布洛陀-童灵守护` | 端专属 Skill·实体直落 `~/.trae-cn/skills/`（⛔不进共享技能配置） |
| `skills/doenglingz-slice-nav/` | `布洛陀-童灵切片导航` | 端专属 Skill·实体直落 `~/.trae-cn/skills/`（⛔不进共享技能配置） |
| （不落盘） | `doenglingz-core.md` | 由 `setup.sh` 从 K2 slices 现场组装 |

## 能力（对照 qodercn）

| 能力 | Qoder CN | Trae Work |
|---|:---:|:---:|
| hooks 事件驱动 | ✅ | ❌ `hooks_event=false`（产品门禁硬短路·平台边界） |
| settings.json 注册 | ✅ | ❌ |
| rules/ 常驻注入 | ✅ | ✅（本质承载） |
| AGENTS.md 全文注入 | ✅ | ❌（无 global_context） |
| skills 软链 | ✅ | ✅（通用 Skill 软链·童灵专属 2 件实体直落 `~/.trae-cn/skills/` 隔离） |
| launchd patrol | ⛔无此机制 | ✅（端独有·替代 hook） |
| 记忆中心软链 | ✅ | ⛔ 无（SOUL/USER 走 `cp` 实体落盘·2026-10-07 去软链） |

## SSOT 对账（§二·七 Trae Work 列）

- 接入率 **5/12 (42%) + 专属 1**——上对齐 `platform_adaptation_check.py --src traework`（作者侧口径）。
- ✅ patrol 降级接入 5：`route_audit` / `route_guard_audit` / `audit_search_kb` / `rule_three_layer_guard` / `card_id_guard`。
- 🔴 无 hook 事件装不上（计入分母）：`route_inject` / `miss_feeder` / `kb_inject`（无 UserPromptSubmit）+ `unknown_unknown` / `feedback_detect`（无完整转录）。
- ❌ N/A 排除分母：`crossend`（无多工作区跨端场景）。
- ⚠️ **端用户态口径**：patrol 每次自报的是**本机可达口径**（名册件是否真在脚本中心落盘），非作者侧 SSOT 数字。端用户侧 `audit_search_kb`（知识库域）与 `card_id_guard`（AI学习库域）**设计不装**时按缺件**静默降级 SKIP**——⛔非故障、⛔不报成告警。

## 目录结构

```
adapters/traework/
├── capability.yaml                     # hooks_event=false → install_scripts 跳过钩子段
├── README.md
├── rules/                              # 承载名（落盘过 setup.sh 名映射·条文 12）
│   ├── core-identity.md                # → IDENTITY.md
│   ├── core-memory.md                  # → MEMORY.md
│   ├── core-soul.md                    # → SOUL.md（通用骨架）
│   ├── core-user.md                    # → USER.md（通用骨架）
│   ├── execution-guidelines.md         # → trae_solo_rules.md（通用版·剥离私人偏好）
│   └── intent-signature-check.md       # → 同名直落
├── setup.sh                            # 聚合入口（rules 落盘 + 分身核组装 + 童灵Skill直落 + patrol 落盘 + launchd）
├── skills/                             # 端专属 Skill 源（实体直落 ~/.trae-cn/skills/·⛔不进共享技能配置）
│   ├── doenglingz-guard/               # → 布洛陀-童灵守护（守护三查）
│   └── doenglingz-slice-nav/           # → 布洛陀-童灵切片导航（域切片按需加载+上岗激活）
└── scripts/                            # 端独有机制（launchd patrol）
    ├── route_traework_patrol.sh        # 拉模式接入层（v0.7 装机版·全量占位符 + 缺件降级 + 接入率自报）
    ├── install_launchd.sh              # launchd bootstrap 助手
    └── com.buluotuo.traework.patrol.plist  # launchd plist 模板（[记忆共享中心] 占位符）
```

## 来源
- 现有加强包：`Trae Work加强包`（setup.sh/verify.sh/scripts/launchd/privacy）。
- 执行准则：`rules/execution-guidelines.md` **通用版**（v1.1-generic）——只含跨用户通用骨架（表格"可读控宽"原则），**剥离私人偏好**（表格控宽列数/字数上限，仅本机 `~/.trae-cn/user_rules/trae_solo_rules.md` 本地版生效·不随包分发）。SSOT=WorkBuddy 原始定义。
- 2026-09-30：注入根订正（`~/.trae` → `~/.trae-cn`）＋ 名映射补齐（execution-guidelines→trae_solo_rules）＋ 补 `intent-signature-check.md` ＋ 分身核改现场组装。
- 2026-10-06：**端串用根治**——童灵专属 Skill（doenglingz-guard/slice-nav）由 `<MC>/技能配置/` 改**实体直落 `~/.trae-cn/skills/`**，切断 `restore-my-skills.sh` 全端软链分发路径（用户令「默认存放地＝系统默认指定处，不占公共技能配置，避免他端串用冒用」）。连带清理 **6 异构端**（Qoder CN / WorkBuddy / Hermes / ZCode / openclaw-autoclaw / workbuddy-ai）共 **25 条**残留软链 ＋ 本端 5 条旧软链，留档 `记忆琥珀/2026-10-06-TraeWork专属skill迁出/`。
- 2026-10-07：**去软链·端实体化**——SOUL/USER 由软链→`记忆规则/共享核心/` 改为**端内实体**（用户令「不做软链·端自己的系统文件 100% 适配」）；安装包本就走 `cp` 实体落盘（未变），本次订正 README「记忆中心软链」错述 → 「SOUL/USER 走 `cp` 实体落盘」并补落盘形态声明，使文档与实盘一致。