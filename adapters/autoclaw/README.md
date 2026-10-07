# autoclaw adapter · OpenClaw gateway 端适配

> 平台底座：OpenClaw gateway（AutoClaw.app 分发）· 配置根 `~/.openclaw-autoclaw/`
> 设计哲学：`记忆蓝图/02_设计理念/02-平台端适配类/AutoClaw布洛陀设计哲学/`（本端最高宪法）

## 注入通道（本端第一性）

OpenClaw 的常驻注入 = **workspace bootstrap 文件**：平台把每个 agent workspace 下的
`AGENTS.md / SOUL.md / IDENTITY.md / USER.md / MEMORY.md / TOOLS.md / HEARTBEAT.md`
作为 "Workspace Files (injected)" 装配进每轮 system prompt——**机制保证在场，不依赖 AI 自觉 Read**。

| SSOT 通道（WorkBuddy 口径） | AutoClaw 等价物 |
|---|---|
| `<user_custom_instructions>`（app-config 顶层执行准则） | **workspace/AGENTS.md 注入节**（本 adapter） |
| `<identity_context>`（SOUL/IDENTITY/USER） | workspace 同名 bootstrap 文件（平台原生） |
| `<user_memory>`（MEMORY.md） | workspace/MEMORY.md（平台原生·主会话注入） |
| Skill 触发注入 | `~/.openclaw-autoclaw/skills/` 托管技能（平台原生） |
| Hook 守卫链 | ⚠️ 无 hook 注册面——走 `extensions/` 插件（before_prompt_build）+ crontab patrol 降级（见设计哲学 01-注入通道规范 §二/§四） |

**多 agent 工作区**：`openclaw.json → agents.list[].workspace` 每个 agent 一个独立 workspace，
各自装配自己的 bootstrap 文件；执行准则须逐 workspace 落位（setup.sh --all 自动枚举）。

**截断护栏**：单文件注入上限默认 20000 字符（`agents.defaults.bootstrapMaxChars`）；
注入节须置于 AGENTS.md **头部**（截断吃尾不吃头）。

## 文件

| 文件 | 用途 |
|---|---|
| `rules/execution-guidelines.md` | 执行准则·通用版（脱敏：个人签名格式/表格控宽数值不随包） |
| `capability.yaml` | install_scripts.py --platform autoclaw 能力声明 + 安装后喊话 |
| `setup.sh` | 注入器：枚举 agents.list[].workspace + defaults.workspace，幂等注入 |

## 用法

```bash
# 全量（枚举 openclaw.json 全部 workspace）
bash adapters/autoclaw/setup.sh

# 指定 workspace
bash adapters/autoclaw/setup.sh --workspace ~/.openclaw-autoclaw/agents/<agent-id>/workspace
```

## 验证

1. 行为验证：新开会话问「你必须遵守哪几条执行准则」→ 答出 9 条即生效。
2. 文件验证：`grep -c "buluotuo:execution-guidelines-v1" <workspace>/AGENTS.md` → ≥2（成对标记）。
3. 机械校验：`python3 platform_adaptation_check.py --src autoclaw` → exit=0。

## 私人偏好边界（⛔不随包分发）

个人签名式回复格式（意图分类容器/产出签名/署名）、第 9 条表格控宽具体数值（列数/字数/折行上限）、愿景三问判据——只存在于用户本机 workspace
AGENTS.md 本地真身，见 `adapters/execution-guidelines-脱敏评估.md`。
