# LobsterAI Adapter（🧭·OpenClaw 引擎端）

> 阶段：**已接委派入口**（`--platform lobsterai` → `install_scripts.py` 读 `capability.yaml` 的 `install_entry` 委派到本目录 `setup.sh`）。
> 端形态：OpenClaw 引擎·bootstrap 文件制（无独立 rules 目录·无 settings.json）→ 非标准 hook 端，安装入口走委派（条文 8/13）。

## 文件构成

| 文件 | 作用 |
|---|---|
| `capability.yaml` | 能力矩阵声明（install_scripts.py Step -0.5 据此分支）+ `install_entry` |
| `setup.sh` | 聚合安装入口（幂等·fail-loud·沙盒可测） |
| `templates/execution-guidelines.md` | 执行准则通用版（脱敏·注入 AGENTS.md 头部段） |
| `plugin/lobsterai-doenglingz/` | 数字分身（童灵）运行时插件（config 驱动） |
| `plugin/lobsterai-route-inject/` | 路由注入插件（脱敏·config 驱动）——WB 端 `UserPromptSubmit` 钩子的本端等价载体，命中路由即注入 Skill 格式契约 |
| `plugin/lobsterai-buluotuo-hooks/` | 脚本体系运行面插件（脱敏·config 驱动·数据驱动 ROSTER）——WB 端 settings.json 脚本体系钩子按**事件类**映射到 OpenClaw typed hook（UserPromptSubmit→before_prompt_build · Stop→agent_end · PreToolUse→before_tool_call · SessionStart→session_start） |
| `plugin/lobsterai-kb-inject/` | 知识库注入插件（脱敏·config 驱动）——命中知识场景即注入 Top-K 锚点（含立场卡检索）；检索引擎 `search_kb` 随脚本体系入包 |

## 安装

```bash
# ① 一条命令（推荐·安装器委派）
python3 install_scripts.py --platform lobsterai "<记忆共享中心>"
# ② 或直接跑本端入口
bash adapters/lobsterai/setup.sh "<记忆共享中心>"
```

`setup.sh` 七步（幂等·可重跑）：
1. 记忆中心指纹检测（L1/铁律·非仅目录存在）
2. 数据清理（开发阶段遗留样例数据·SHA256 精确比对·⛔不碰你的记录）
3. **AGENTS.md 头部段注入**执行准则（marker 幂等·改前备份 `.bak-<date>-guidelines`·⛔不碰 App 托管段）
4. skills 软链 → 本端 `SKILLs/`（存在不覆盖·保本地版）
5. **数字分身（童灵）插件**落位 → `third-party-extensions/` + 共脚本落 `plugin/lib/` + 注册 `openclaw.json` 的 `plugins.allow/entries/load.paths`
5b. **路由注入插件**（`lobsterai-route-inject`·脱敏）落位 + `config.json` 落定（`inject` = `[记忆中心]/脚本中心/route_inject_prompt.py`）+ 注册 —— 转发公共注入器，命中即 `appendContext` 注入格式契约（⛔无硬编码作者路径）
5c. **脚本体系运行面插件**（`lobsterai-buluotuo-hooks`·脱敏）落位 + `config.json` 落定（`scripts_dir`/`dt_devtools`/`state_dir`）+ 注册 —— 按事件类承载 UserPromptSubmit/Stop/PreToolUse/SessionStart 四类脚本（数据驱动 ROSTER·单一数据源）
5d. **知识库注入插件**（`lobsterai-kb-inject`·脱敏）落位 + `config.json` 落定 + 注册 —— 转发公共注入器，知识场景注入 Top-K 锚点（检索引擎 = 脚本中心 `search_kb.py`）
6. 自验证（`platform_adaptation_check.py --src lobsterai` + AGENTS 标记）

## 能力（详见 capability.yaml）

| 项 | 状态 |
|---|---|
| AGENTS 全文注入 | ✅（每会话加载·单文件截断保头→头部段恒在场） |
| hooks | ⚠️ 走 OpenClaw 插件（非 settings.json）——`lobsterai-doenglingz`（注入/守护/红区闸）+ `lobsterai-route-inject`（路由注入）+ `lobsterai-buluotuo-hooks`（脚本体系四类事件）；`message:*` 在 webchat 不发射=平台边界 |
| 自定义指令 | ✅ 走 AGENTS.md 头部段（本端等价通道） |
| skills 软链 | ✅ |

## 数字分身（童灵）边界·务必读

- 本 adapter 装的是**运行时**（W1/W3 注入 + 守护 + 红区闸），**不含人格内核**。
- 童灵内核 = **你自己的语料蒸馏产物**，需按包内说明**自行造芯**：跑 33 题问卷 + HEXACO 100 题 →
  用 `references/digital-twin/k2-slice-generator/` 生成你的 K2 切片 → 写入本端 `AGENTS.md` / `USER.md`（每会话注入面）。
- 这正是"**发布造分身的管线、不发布分身本体**"：包内零个人数据，端用户得到的是能力而非别人的分身。

## 脱敏边界（⛔进包不变量）

- `templates/execution-guidelines.md`：通用版（#1-9 骨架 + 回复格式铁律 + 愿景三问）；**#9 表格具体数值上限剥离**，由用户本地规则层覆盖。
- 不随包：任何个人标识/个人作答数据/私人偏好数值/作者侧绝对路径。
- 来源：执行准则 ← WorkBuddy 自定义指令（SSOT: `~/<记忆中心>/...`）→ 端适配脱敏迁移。

## 来源

- 通道登记：`记忆蓝图/02_设计理念/02_平台端适配类/LobsterAI布洛陀设计哲学/01-注入通道规范.md`
- 设计依据：`记忆蓝图/04_系统文件设计/安装包设计哲学/`（条文 8/12/13·条文 6 发布面）
