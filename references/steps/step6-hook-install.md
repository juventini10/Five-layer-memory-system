# 步骤6·钩子安装（未知未知路由兜底）

📦 **产出物**：`[配置根]/hooks/route_unknown_unknown.py` 已拷贝 + 占位符已替换 + `[配置根]/settings.json` 的 `hooks.Stop` 已追加该钩子（幂等、保留现有钩子）；另含铁律硬墙五件套（`[配置根]/hooks/rule/` → UserPromptSubmit 挂 `rule_fragment_inject.py`、Stop 挂 `rule_three_layer_guard.py` ⑥覆盖守卫）与用户侧**脚本中心文件夹** `[记忆共享中心]/脚本中心/`。

> 🔴 **本步骤是步骤6（Skill安装）的必然后续，不独立计步序。** 步骤6 完成后、步骤6.5（记忆琥珀）之前自动执行。
> 目的：把「未知未知路由 A+B」真正落到执行机——使 SOUL.md 的 `【🕳️ 我的未知未知】` 段在全新安装后即可被 Stop 钩子兜底自动路由到 `悬置区.md`，而非「说明书写了功能、包裹里没发货」。

---

> **⚡ 步骤锁定协议**
> ① 导航锁：每次回复首行输出 `步骤6-钩子（随步骤6执行）`
> ② 偏离锁：用户问无关问题 → 记到待办列表，继续安装
> ③ 检查点前置依赖：Read `[记忆共享中心]/.install/step6-done.md`（全新）或 `[记忆共享中心]/.install/step5-done.md`（升级，因不走步骤6）— 均不存在则阻塞
> ④ 检查点写入：末尾 Write `[记忆共享中心]/.install/step6-hook-done.md`

## 执行指令

### ⚠️ 平台检测（先决）

执行前判定当前平台：

- **macOS / Linux** → 走下方「macOS / Linux」段
- **Windows** → 走下方「Windows」段

---

### macOS / Linux

#### ⚠️ 禁止行为

| 禁止 | 原因 |
|:----|:-----|
| ❌ NEVER覆盖 `[配置根]/settings.json` 的现有钩子 | 活体已挂 `route_audit.py` 等钩子（⛔原例 `l3_conclusion_guard.py` 已于 2026-09-12 全端下线），整文件重写=误删其他钩子=破坏对话质量 |
| ❌ NEVER用硬编码绝对路径替换占位符 | 必须用步骤3确定的记忆共享中心路径，否则钩子指向错误目录，残差写不进用户的悬置区 |
| ❌ NEVER跳过幂等检查 | 二次安装/升级重跑会重复追加同一条钩子命令 |
| ❌ NEVER在验证通过前说"钩子安装完成" | 钩子未挂上=🕳️段无人兜底，等于功能没交付 |

### 🔌 熔断器

- 成功条件：钩子脚本就位可执行 + settings.json `hooks.Stop` 含该命令 + 占位符已替换为真实路径
- 中断处理：任一步失败 → 输出已完成项 + 标注失败点 → 引导回到对应子步骤修复
- 重试机制：修正后从失败的子步骤继续，不需要重跑整个步骤6
- 降级处理：settings.json 解析异常 → 输出原始内容 + 提示用户手动按下方格式追加，不静默吞错

### 0. 确认记忆共享中心路径（macOS / Linux）

> 本步骤所有路径替换以**步骤3确定的记忆共享中心绝对路径**为准（即 `[记忆共享中心]` 占位符的真实值，例如 `/Users/xxx/[记忆共享中心]`）。
> 若该路径尚未确定（步骤3未完成），先回退步骤3。

记此路径为后续 `MEMORY_CENTER` 变量（末尾不带 `/`）。

### ⚠️ 安装前必读：为什么这里只有一条命令

钩子的「拷贝」与「注册」此前由**三处各自维护的清单**驱动（INSTALL.md / 执行文件 / 本文件）——
三份清单长期不同步，实证后果：**注册进 `settings.json` 的钩子指向根本不存在的文件**，装机后静默失效且不报错。

现在唯一数据源 = 包根 `install_scripts.py` 的 `ROSTER` 数组：搬什么、注册什么读同一份数据，机制上不可能脱节。
新增/停用钩子只改那一处。查看清单：`python3 install_scripts.py --list`。

---

### 1. 一条命令装齐

**macOS / Linux**：
```bash
MC="<步骤3确定的记忆共享中心绝对路径>"
python3 install_scripts.py "$MC"          # G2-2 根治后：缺省=环境自证（唯一命中直装/多零命中fail-loud转人）
# Step -0.5 拿到运行时进程证据的端，显式传参优先：python3 install_scripts.py --platform <端ID> "$MC"
```

**Windows**：
```powershell
$MC="<步骤3确定的记忆共享中心路径>"
$py = (Get-ChildItem "$env:USERPROFILE\.workbuddy\binaries\python\versions\*\python.exe" | Select-Object -First 1).FullName  # WorkBuddy端自带python；非WB端（如Qoder CN）直接用 PATH 上的 python3
& $py install_scripts.py "$MC"
```

> 该命令一次做完三件事（幂等·可重跑）：
> ① **生成脚本中心** `[记忆共享中心]/脚本中心/`（完整脚本副本·用户可查看/二次开发）
> ①b **装规则层** —— 触发规格 `rule_triggers.yaml` + `rule_conflict_signals.yaml` + 三层规则文件（铁律/摘要/详解存档版）→ `[记忆共享中心]/记忆规则/`。⛔缺触发规格＝硬墙静默零注入（实测 rc=0、无报错）；缺三层规则文件＝覆盖守卫每次 Stop 报 `[ERR] 文件缺失`
> ② **部署钩子副本** —— 19 个钩子 + 同目录依赖件 → `[配置根]/hooks/`（含 `route/`、`rule/` 两个子域）
> ③ **注册 settings.json** —— 按事件幂等追加（已挂的跳过，⛔不覆盖你现有的其他钩子）
>
> 先看会做什么：`python3 install_scripts.py --dry-run "$MC"`

> ⚠️ **Windows 运行期环境**（安装器已内置，此处仅供排查）：WorkBuddy 调度命令时可能走 Git Bash(MSYS)——裸 `python`
> 会被「应用执行别名」劫持到微软商店（失败 code=49），且 `C:/...` 路径会被 MSYS 误转。安装器写入的命令行已固定为
> `MSYS_NO_PATHCONV=1 "<自带 python.exe 绝对路径>" "<钩子绝对路径>"`，无需手工处理。

### 2. 🔒 门禁验证

```bash
# 2a. 钩子总表核查（判据与安装同源·不另抄清单）
python3 install_scripts.py --verify "<记忆共享中心绝对路径>"   # 期望：✅ 19/19 钩子已落盘并注册 · 规则层就位

# 2b. 关键钩子实跑自检
CFG_DIR="$(grep -m1 '^CONFIG_ROOT=' "$MEMORY_CENTER/.install/step3-done.md" | cut -d= -f2 | sed "s#^~#$HOME#")"  # 配置根→绝对目录
test -x "$CFG_DIR/hooks/route/route_inject_prompt.py" && echo "OK_HOOK_FILE"
python3 "$CFG_DIR/hooks/rule/rule_fragment_inject.py" --selfcheck
python3 "$CFG_DIR/hooks/rule/rule_three_layer_guard.py" 2>&1 | tail -3

# 2c. 脚本中心已生成
test -f "<记忆共享中心绝对路径>/脚本中心/rule_fragment_inject.py" && echo "OK_脚本中心已生成"
```

- `--verify` 输出 `✅ 19/19` + 自检表正常 → 写入检查点，进入步骤6.5
- `--verify` 报 `!! 未落盘 / 未注册` → 按它列出的文件名重跑 `install_scripts.py`（幂等，不会重复注册）

### 3. 包里有、但有意不装的脚本

| 脚本 | 不激活的原因 |
|:---|:---|
| `route_audit` | 审计作者侧路由命中率 |
| `route_miss_feeder` | 为作者侧采集 miss 样本 |
| `route_guard_audit` | 规则配置尚未定稿入包 |
| `change_closedloop_guard` | 判据绑定 git 提交集 |
| `design_family_guard` | 巡检作者侧规范资产 |
| `vision_gate` | 判据绑定作者愿景词 |
| `guard_doc_consistency` | 需作者侧守卫文档 |

> 这些脚本依赖的设施只存在于作者机器上，装到端用户机器只会空转——故留在脚本中心备查，不进安装流程。



---

## 写入检查点

验证全部通过后，Write `[记忆共享中心]/.install/step6-hook-done.md`：

```
步骤：步骤6·钩子安装（19 个钩子 + 脚本中心·单一数据源驱动）
完成时间：<当前时间>
数据源：包根 install_scripts.py 的 ROSTER 数组（19 个钩子 / 30 个文件）
产出物：
- [配置根]/hooks/ 下 19 个钩子 + 同目录依赖件（含 route/、rule/ 两个子域）
- [配置根]/settings.json 对应事件已注册（UserPromptSubmit 6 / Stop 8 / PreToolUse 4 / SessionStart 1）
- [记忆共享中心]/脚本中心/（完整脚本体系·用户拥有的副本）
- [记忆共享中心]/记忆规则/（触发规格 rule_triggers.yaml + rule_conflict_signals.yaml + 三层规则文件）
验证：python3 install_scripts.py --verify "<记忆共享中心>" → ✅ 19/19 钩子已落盘并注册 · 规则层就位
```

> 🔴 **⛔ "已注册" ≠ "已生效"——本段的成功条件按端分述（2026-10-02 Hermes 端实证）**
>
> `install_scripts.py` 的 ROSTER 对**所有端统一**写 `settings.json` 的 `PreToolUse`，
> 但**各端对该事件名的支持不同**，照抄会得到静默失效：
>
> | 端 | `PreToolUse` 是否真事件 | 真生效通道 | 验收判据 |
> |:--|:---|:---|:---|
> | WorkBuddy / Qoder CN | ✅ 是 | `settings.json` hooks | 安装后**造一次违规 Edit** ⇒ 应被 exit2 拦下 |
> | ZCode | ✅ 是 | `cli/config.json` 的 `hooks.events` | 同上（须 `enabled: true`） |
> | **Hermes** | 🔴 **否·该名不存在** | **插件通道** `ctx.register_hook()` + `plugin.yaml: provides_hooks` | 查 `~/.hermes/pretool_guards_hook.log` 有**真实拦截行** |
>
> **Hermes 端特别注意**：`settings.json` 里那 4 条 `PreToolUse` 条目**不会被派发**，
> 但**同名 4 个守卫确实在跑**——因为它们同时被 `adapters/hermes/plugins/buluotuo-pretool-guards`
> 插件经插件通道挂载。⛔ **只看 `settings.json` 会误判成"没挂"**（假红），
> 只看插件会漏掉 settings 那条无效条目（假绿）——**必须双通道查**。
>
> **通用三门自检**（新建挂点时必走，⛔ 不许凭"配置写好了"判生效）：
> ① 事件名 ∈ 宿主白名单？ ② 写在宿主装配期真正读的那个文件？ ③ 同意/安全门开了吗？
> 三门全过**仍不算生效**——⛔ 必须取到**本端运行态发射证据**（台账新增行 + 正例 + 负例）
> 才许写"已生效"。详见 `记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md §8.6`。
