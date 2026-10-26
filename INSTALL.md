# 🏮 布洛陀 2.2.11 — 多平台安装入口（7 端可装·第 8 端适配中·能力矩阵驱动）

> 🔴 本文件是本安装包的**宪法级入口文件**。不是建议，是硬约束。不可跳过。  
> 🔴 所有安装流程从这里开始。不管用户怎么说，第一个读的文件必须是这里。
> 🔴 本文所有命令一律由 AI 自身终端工具执行（执行主体铁律见 Step -0.6 注记块），⛔把裸命令交给用户亲手跑是 DO NOT。



> **AI 必读：这是本安装包的唯一入口文件。**  
> 不管用户怎么描述（"帮我装"、"帮我升级"、"读取安装包"），都从这里开始。  
> 前 20 行分流，不需要问用户任何问题。

---

## Step -2：接收完整性前置门（先于 Step -1）

> 🔴 任何安装/升级/体检动作之前，先确认拿到的是全包。半包（网盘断点/漏文件夹/选择性下载）导致的"组件不存在"类报错，**不是包缺陷，是接收缺陷**——不先验完整性就排查=方向性浪费（2026-10-09 外部 S0 体检在五组件齐全的发版包上误报"均不存在"，实证）。

1. **zip 渠道收到 `.sha256`** → 解压前先校验：`shasum -a 256 -c 布洛陀-全平台安装包-V<版本>.zip.sha256`（Windows PowerShell：`Get-FileHash -Algorithm SHA256 <zip>` 对比文本）。不过=传输损坏/不完整，重传重下，⛔不进安装。
2. **散文件/clone 渠道** → 跑 `bash verify.sh`（Windows `powershell -File verify.ps1`）；或最快一层目测：`references/` 下应含 **skills / digital-twin / templates / hooks / scripts / 知识联邦引擎-min / 记忆琥珀 / 成就系统** 等目录。缺 `知识联邦引擎-min` / `templates` / `记忆琥珀` / `成就系统` 任一 = 典型半包形态（中文目录最容易在网盘批量下载中丢失），⛔不进安装，先补全。
3. 校验通过 → 继续 Step -1。校验失败 → 停下告知发布者"sha256 不符/缺 XX 目录"，附缺项清单。

> 解压提示：本包 zip 内条目全部带 UTF-8 名称标记。Windows 10/11 自带解压、Bandizip、macOS 归档工具均正常；Windows 7 及老版 WinRAR 可能出现中文目录名乱码，换 Bandizip 即可。

---

## Step -1：关键词预检（最早判定）

> 在执行任何 Bash 检测之前，先看用户说的第一句话是否包含以下模式：

| 用户说的                                         | 匹配模式                                           | 路由                   |
| -------------------------------------------- | ---------------------------------------------- | -------------------- |
| 装 daily-buddy / 安装三明智 / install clock-loop … | `装`/`安装`/`install` + **Skill 名**（中英文均可，见下方映射表） | → 跳至 §**单 Skill 安装** |
| 装记忆琥珀 / 安装记忆琥珀 / install memory amber        | `装`/`安装`/`install` + `记忆琥珀`/`memory amber`     | → 跳至 §**记忆琥珀单装**     |
| 装成就系统 / 安装成就系统 / install achievement         | `装`/`安装`/`install` + `成就系统`/`achievement`      | → 跳至 §**成就系统单装**     |
| 装脚本体系 / 安装脚本体系 / install script system       | `装`/`安装`/`install` + `脚本体系`/`script system`    | → 跳至 §**脚本体系单装**     |
| 装数字分身 / 装分身 / 装抽卡 / install digital twin      | `装`/`安装`/`install` + `数字分身`/`分身`/`抽卡`/`卡引擎`  | → 跳至 §**数字分身完整版单装** |
| 模型检查 / 引擎检查 / 模型状态 / 模型装了吗        | (`检查`/`状态`/`装了吗`) + `模型`/`引擎`          | → 跳至 §**模型体检**（报态路由：报完态才问要不要看，⛔不塞安装卡） |
| 装模型 / 配模型 / 配置检索引擎                 | (`装`/`安装`/`配`) + `模型`/`检索引擎`           | → 跳至 §**模型体检**（配置路由：报态后直进 C1 全文，不再问） |
| 其他（帮我装、读取安装包、执行安装 …）                         | 无明确 Skill 名 / 记忆琥珀                             | → 继续 Step 0 全包安装     |
| 升级 / 升级布洛陀 / upgrade / 更新 / 我要升级             | `升级`/`upgrade`/`更新`                              | → 跳至 **Step -0.6 版本对比与安装模式选择**   |

> 🔴 命中轻量路由 → 继续读 Step 0 确定记忆中心路径，然后跳到对应章节。  
> 🔴 未命中 → 正常走 Step 0→分流→全包安装。

### Skill 名映射

| 用户说的                 | Skill 目录                                  |
| -------------------- | ----------------------------------------- |
| 每日伙伴 / daily-buddy   | `references/skills/daily-buddy/`          |
| 三明智 / triwich / 三明治  | `references/skills/triwich/`              |
| 反方向的钟 / clock-loop   | `references/skills/clock-loop/`           |
| 成长箱 / growth-box     | `references/skills/growth-box/`           |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / sucair / 素裁   | `references/skills/sucair/`               |
| 系统日志 / system-logger | `references/skills/system-logger/`        |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/`        |
| Shall We Talk / SWT  | `references/skills/shall-we-talk/`        |
| 好好学习 / good-good-study | `references/skills/good-good-study/`    |

---

## Step -0.9：价值宣导与平台亮牌（v2.0 新增·用户两步法①）

> 用户说"安装/装/执行安装"且 Step -1 命中"其他/全包安装"（非 Skill 名、非 upgrade）→ 本步最先执行。
> 目的：先把"这是什么、愿景、数字分身、支持哪些端"说清，再进检测——安装从黑箱执行变看得见的选择。

**AI 首条回复（固定逐字稿 · ⛔不得临场改写，仅 [动态项] 按实况替换）**：

**开场句（固定·逐字）**：收到。开始动手前，先把话说明白：你要装的是什么，装完你机器上会多出什么。

1. **它是什么**：布洛陀是一套五层记忆系统，把你的认知、习惯、规则外化成一个能陪你长大的"外部大脑"。多个 Skill 联动工作：日常记录、深度对话、循环自省、读书沉淀、知识蒸馏、系统日志……其中三大思维（第一性原理 / 抽象建模 / 批判验证）已做成能单独调用的「三明智」Skill，不只是藏在底层的设定。
2. **愿景**：我们不想只做一座"只会存、不会长"的**静态记忆仓库**，而要演进成**自主进化的活系统**：全自动化·越用越好用·自主自动进化·越用越了解你。（来源：SOUL.md §演进愿景，即本系统最高判据，非凭空写）
3. **为什么叫布洛陀**：壮族传说里的**文明先祖**，教会先民怎么生存、怎么思考。系统以他为名，是希望每个用的人，也能长出属于自己的记忆系统。
4. **数字分身（童灵 / Doenglingz）**：
   答一组 100 题的性格问卷，约 20 分钟，系统会把你的认知方式、价值观、行为规则蒸馏成一套"分身切片"。他诞生时就带着你的切片工作：**判断用你的思路，行事守你的规矩**。
   他也不是你的复制：你拿手的，他贯彻得更稳。
   他更不是静态的代码：每件事干完留痕、留反思，每月把新记录重新蒸进自己。**他安装的那天，只是他的开始**，之后他陪你一起长。
   最直观的区别：别的 AI 要你反复交代自己，他不需要。你的标准，就长在他身上。
5. **支持的端（亮牌）**：⛔以下按纯文本行转述，不转成表格（部分端聊天框不渲染表格，竖线会露出生肉）。数字=装完后该端机器上实际生效的件数（装机自检输出对账，⛔话术不手改数）：
   · 🟡 WorkBuddy：系统文件四件+38 个自动值守钩子全自动；第 5 件「自定义指令」在设置框里，**你粘贴保存 1 步**（平台机制如此：装机器给文件，给不了你的设置框）
   · 🟢 Qoder CN：5 个系统文件 + 常驻注入面 + 5 类事件钩子
   · 🟢 ZCode：系统文件五份内容合并进 AGENTS.md 承载 + 7 类事件钩子
   · 🟢 Hermes：系统文件五份内容落位（IDENTITY 并入品格文件）+ 18 个插件
   · 🟢 Zwork（新版 AutoClaw）：系统文件内容由平台记忆机制吸收，安装验证已跑通
   · 🟡 豆包办公：规则生成好，**你粘贴保存 1 步**（平台机制如此）
   · 🔴 LobsterAI：适配收尾中，暂不推荐安装
   一眼看懂：🟢=全自动，装上就用｜🟡=有一步需要你手动｜🔴=还没适配完，先别装

   > ⛔ 以下两行为 AI 执行注记，不进用户屏：① 各端件数以装机回执/`--list` 自报为准，话术不手改数（38=ROSTER 实盘数，旧文 19 已于 2026-10-17 F2 根治对齐）；② Trae Work 暂不进用户面亮牌（2026-10-13 用户令：新版未适配完；包内适配层保留⛔不删，适配完成恢复列出）。

6. **本次更新给你带来了什么（新老用户同播 · 2.2.4 → 2.2.9）**：老用户读作"更新了什么"，新用户读作"要装上的新东西"。
   【知识联邦引擎】
   · 两个模型，两个岗位：**Large 压缩版管检索**——问知识时用最聪明的大模型，压缩过所以普通笔记本也跑得动；**Base 管碰撞**——知识卡里互相打架的观点由它扫出来提示你合并，快且省内存、质量不降
   · 推荐都装上（两个岗都满）：检索有大模型、碰撞有 Base，各站各的岗；只装一个也能用，系统会如实告诉你哪一岗停摆
   · 装不上自动回滚；一个都不装也有记录和文字检索，只是语义检索和概念碰撞不可用——随时可补装，检索永不断粮
   · 检索随包件补齐，那个更聪明的检索法在 Windows 上不再悄悄失灵
   【三明智】
   · 史诗级加强：分析结论第一次有了明确的、可量化的质量标准
   · 引入"认知四象限"：每份结论自动交代这轮认知落在哪一格——已知已知／已知未知／未知已知／未知未知，认知盲区第一次从"没人提"变成"摆在台面上"
   · 引入"证据档位"：每条承重依据定档——推测级／佐证级／实证级，整份结论按最弱的那根柱子定档，弱证据再也冒充不了硬结论
   · 新增缺料闸：关键证据不够时，结论自动变成"补上什么源才成立"的诚实形态，"听起来有道理"从源头掐灭
   【反方向的钟】
   · 新增系统体检：说"指令审计"，系统把你的常驻指令和资产挨个盘点，专查四类隐患——指令互相打架、触发面过宽、依赖已失效的工具、说着的还是旧事实
   · 查完给"保留／精简／核实／弃用"建议，删改权全在你
   【读书助手】
   · 书精华摘要文件名带上书名，68 本同名"精华摘要"时代结束，复习检索不再拿错书
   【每日伙伴】
   · 日记位置不用手动改：安装自动定位你的笔记库，日记和成就跟着库走；晚上复盘抽卡与其他端互通，不重复不漏抽
   · Windows 新增修复：日记目录路径被拼成两段重复的错误已根治
   【唤醒记忆】
   · 自动巡检双端上线：Windows 用户第一次拥有、Mac 新用户也是第一次拥有；巡检状态分"未注册／已注册无记录／正常趋势"如实分说，不再一句"日志不可用"糊弄人
   【其余 Skill】
   · 同步有更新（稳定性与准确性优化，无需你操作）
   【数字分身】
   · 自动上岗（默认）与安静模式照常：你复盘、记录、分析时他自己进入干活状态；想让他歇一句话，想召回来明说"启动童灵"，开关随你
   · 月度蒸馏新增"系统体检"，凑齐五件事：系统日志蒸馏、日记月报、成长箱蒸馏、统一蒸馏管道、系统体检——每月初自动列好待做清单，说一声"启动童灵，做月度蒸馏"，分身按单逐项推进；Mac 和 Windows 装完都有
   · 分身同步状态修好：开机自检里的分身同步不再永远显示"未启用"，第一轮就如实报哪个工具最新、哪个停在旧版
   【装得更省心】
   · 升级会保护你手工改过的规则文件：检出改动就保留你的版本、附差异说明，不再静默覆盖
   · Windows 安装全链路根治：命令一律由 AI 代跑不甩给你，双击"安装兜底.bat"一键自救，写盘前有探测硬闸、被拦会指路
   · 历史空壳目录自动搬进备份区（只搬不删可还原）；新装不再"装好了却不理你"；已装用户不会被当成第一次装
   【少踩坑】
   · Windows 误报逐个清零：巡检误报"硬漂移"、自检"自污染假红"、"目录副本"误报，都没了
   · 开机自检三态分账：真失败／答题后待办／未安装分得清清楚楚，不再把待办误读成故障
   想看逐条明细，说"更新日志"，每一条都写在里面。

   > ⛔ 以上整段为用户屏；以下两行为 AI 执行注记，不进用户屏——
   > 抽取规则（⛔凭记忆编）：三查定屏。①组件 diff：解上次发布版（锚=CHANGELOG 顶 `LAST-PUBLISHED` 行）与本包 `component-versions.json` 的 skills 版本对，再比 `references/知识联邦引擎-min/scripts/` 文件集 diff——引擎无版本字段，件数增减即更新判据（⛔只看 component-versions=引擎漏名案，2026-10-19 实证）；②功能级筛选：升版组件各自 CHANGELOG 捞用户可感知功能点，读得出"用户新增了什么能力"的具名点写（每项≤2句·动词开头·零工程术语·禁"上岗/站岗/腿/闸/哨兵"类内部话），读不出的并计数行；隐私净化与纯内部机制类整条不进屏（内账"更新日志"可查）；③族序律：具名 Skill/引擎行在前，Skill 计数行紧随具名行收口，数字分身独立族随后，装机体验兜底末行——同族内容⛔不跨族穿插。区间内无任何用户级更新→整点不播并如实说"本次无变更记录"，⛔硬凑。
   > 分工注：Step -0.6 播报C 管差集（缺什么/落后什么→要不要升），本点管增量（升了得到什么→值不值），一向后一向前。

> **内部对账参考表（AI 核对数据用·⛔不向用户照读，用户面以上方灯版行为准）**：

| 端 | 显示名 | 状态 | 装完你手上会有什么 | 还要你做什么 |
|:---|:---|:---|:---|:---|
| workbuddy | WorkBuddy | ✅完整 | 五系统文件（第5件自定义指令=设置框字段·装机器不代写）+38 钩子 | **粘贴 1 步** |
| qodercn | Qoder CN（含 Qoder CN IDE） | ✅完整 | 五系统文件+rules/ 常驻注入面+AGENTS/MEMORY 模板+4 事件钩子（setup.sh 委派·自动注入） | 无 |
| traework | Trae Work | ✅进包 ᵗ | 五系统文件+launchd 巡检（30min 自动） | 无 |
| zcode | ZCode | ✅完整 | 五系统文件+7 事件钩子+2 项数据清理 | 无 |
| doubaowork | 豆包办公 | ✅进包 ᵈ | **待粘贴文本**（脚本给不了·本端无规则目录） | **手动粘贴 1 步**ᵈ |
| hermes | Hermes | ✅完整 | 五系统文件+**18 个插件**（人格注入·路由·守卫·台账） | 无 |
| lobsterai | LobsterAI | ✅完整（未适配完毕·暂不推荐安装） | 五系统文件+4 个 OpenClaw 插件 | 无 |
| zwork | Zwork（AutoClaw 新客户端） | ✅完整 ᶻ | 五系统文件等价物对账（端实体+平台 Memory）+setup 对账器（对账吸收模式·零写入） | 无 ᶻ |


> **状态列语义**：「✅完整」= 该端**适配层完整进包**（有 `capability.yaml` + 端部署链 + 该端可用的验证），
> ⛔非「端上功能与 WorkBuddy 逐项等价」。
> **「装完你手上会有什么」这一列是给你判断用的**，状态标签只说"包全不全"，
> 这一列说"**装完你的机器上会真的多出什么**"。两列不一致时，以这一列为准。
>
> ᵗ **Trae Work 边界（端用户态诚实标注·条文 24）**：① **无 hooks 事件**（产品门禁硬短路·平台边界）⇒ 守卫承载 = **launchd patrol 拉模式**（30min 定时巡检），非事件派发；② 端上 33题→文件合成流程为**按端待测**（能力矩阵该格 ⚠️待补）；③ 接入率自报走**端用户态口径**（可达 = 本机有守对象，作者机特有域件记 `EXCLUDED`·⛔不谎报可达）。
>
> ᶻ **Zwork 边界（平台托管型·第四型·06 规范 §2.7.2.1）**：本端无 hooks/无插件/无 cron/无 settings.json/无 rules 注入目录，唯一机制级注入位=**平台 Memory Run 级注入**；五系统文件等价物=端自有实体（档案层 AutoClaw/ 两件+平台 Memory 两面），安装=**对账吸收模式**（setup.sh 只读对账·⛔覆盖端实体·条文48 端自持有律原生成立）。**端分立铁律**：包内 `adapters/autoclaw/`＝旧客户端（`~/.openclaw-autoclaw`·OpenClaw gateway），⛔与本端混同；本机两配置根并存时探测双命中须 fail-loud 问询。
> ᵈ **豆包办公边界**：本端**没有规则目录、没有 alwaysApply**，规则唯一通道是「设置 → 工作模式任务设置 → 工作任务偏好指令」文本框。
> 脚本能做的只有把待粘贴文本生成好并自检，**粘贴+保存必须你手动做**，这是平台机制，⛔ 不是本包偷懒。
> **字数上限**：豆包官方已公布该文本框上限为 **10000 字符**。安装器生成的 paste.md 约 4700 字（已用约 47%），剩余空间充足，可放心追加个人偏好；安装器会自动统计字数占比，接近上限时警告。

> 🔧 **同步纪律**：支持端以 `adapters/<端>/capability.yaml` 存在为准。新增端确认进包时**必须三处同步更新**：①本表 ②`references/component-versions.json` 的 `platform_support` ③`README.md` 平台说明。⛔占位端（qwen/teleagent 无 capability.yaml）不计入支持数。
> ⚠️ **文案维护**：1-5 点为固定逐字稿（第 5 点亮牌数据行随 component-versions.json 实况更新，措辞骨架不动），修订须同步三处（本步 / component-versions.json / README.md）；Skill 数、平台数随版本变动时按同步纪律更新，⛔不得临场改写措辞。

**收尾句（固定·逐字）**：下面我先检测你的机器环境和已有版本，也看看你的知识检索两个模型有没有上岗，再开始装。检测结果我会一条条带你看，缺什么会当场指出来。（端判定拿不准时的问询属检测段兜底话术，⛔不进首屏；"两个模型有没有上岗"是老用户知情链的预告位·2026-10-22 维护方定"用户必须清晰知道模型是干嘛用的，充分知情才能分辨自己要怎么做"，检测落点=Step -0.6 模型配置行 + §模型体检，本句只埋预期⛔不展开介绍）

**老用户折叠**：Step 0 判定为老用户后，本段折叠为一行「你已装过，直接看版本对比」——不重复宣导（防打扰，符合「不問新/老、先检测」铁律）。

---

## Step -0.5：平台判定（v2.0 新增·能力矩阵驱动）

> 本包合并 8 端适配层。**先定平台，再装对应端**——装错端=钩子注册到不存在的机制上，静默失效。

**判定顺序（拿到即停，⛔不猜）**：

1. **运行时进程证据**（最可靠）：AI 宿主自查进程/产品名（如 Qoder CN=`/Applications/Qoder CN.app`）。
2. **配置根存在性探测**（Bash 实证，按第一命中定）：

```bash
# 探测清单⛔不手写目录名——由 adapters/*/capability.yaml 的 config_root 机械生成（G2-2 根治：
# 手抄清单曾与落点漂移 .trae-work vs ~/.trae-cn 三名不一致）。AI 也可直接跑 install_scripts.py 缺省命令，
# 其内置 _detect_platform_from_env() 同逻辑自证并打印证据行。
for cap in adapters/*/capability.yaml; do
  p=$(grep -m1 '^config_root:' "$cap" | sed -e 's/^config_root:[[:space:]]*//' -e 's/[[:space:]]*#.*$//' | tr -d '"' | sed -e 's|^~||' -e 's|^/||')
  [ -d "$HOME/$p" ] && echo "HIT:$p（端=$(basename $(dirname $cap))）"
done
```

3. **多命中/零命中 → 问用户一次**（列上表 8 端选单，⛔不让用户猜目录名）。

**判定结果 → 安装路由**：

| 平台判定 | 安装动作 |
|---|---|
| WorkBuddy | `python3 install_scripts.py "$MC"`（缺省=环境自证：盘上唯一命中 `.workbuddy` 即直装；WB 老机天然满足=行为兼容由探测兑现，不由猜兑现） |
| 其余 7 端 | `python3 install_scripts.py --platform <端ID> "$MC"`（端ID=`adapters/` 目录名·显式值优先，与盘上探测冲突时打印⚠️证据行） |
| **不传参数的任何端** | install_scripts.py 自动环境自证：**唯一命中→打印判定+直装；多命中/零命中→fail-loud 列候选转人，⛔不静默回落**（G2-2 走查根治·平台=机器环境事实，非调用者声明） |
| 端 ID 无 `adapters/<端ID>/capability.yaml` | **该端未发布接入** → 明示"此端为占位（README-only），v2.0 未覆盖"，走 WorkBuddy 兼容分支需用户确认，⛔不静默降级 |

> 能力分支细节（hooks 有=完整钩子组；无 hooks=规则降级）由 `install_scripts.py` 读
> `adapters/<端>/capability.yaml` 自动执行；人读版能力对照见 `adapters/CAPABILITY-MATRIX.md`。

---

## Step -0.6：版本对比与安装模式选择（v2.0 新增·用户两步法②·取代原 §升级检测）

> 本步合并原「§升级检测」——用**组件级**版本清单驱动，不再只抽 CHANGELOG。
> 触发：Step -1 命中"升级"关键词，或 Step -0.5 之后对老用户自动进入。
> 复用 Step -0.5 的平台判定结果，先输出支持状态报告，再做版本对比。

**支持状态报告（必须输出）**：
```
⚡ 平台判定：你当前在 [X 端]
   支持状态：[✅ 已覆盖 / 🔴 占位未发布]
   端配置根：[读 adapters/<端ID>/capability.yaml 的 config_root，如 Qoder CN=~/.qoder-cn；占位端默认 ~/.workbuddy]（供步骤3 3c-2 写入 step3-done·v2.0.1）
   （占位端→明示"v2.0 未覆盖，走 WorkBuddy 兼容分支需你确认"，⛔不静默降级）
```

> 🔴 **执行主体铁律（2026-10-21 立·Windows 用户 PowerShell 抱怨实证）**：本文档所有代码块（bash / powershell / pwsh）一律由 **AI 用自身终端工具执行**，⛔DO NOT 把命令贴给用户让其去 PowerShell/终端亲手跑。唯一例外仍是 WorkBuddy 自定义指令设置页粘贴（F20 注）：那是平台机制给不了设置框，不是命令。
> 命令跑不动时按此顺序自救（逐级降级，全部用完仍红才可告知用户）：
> ① `.ps1` 被执行策略拦 → 改 `powershell -NoProfile -ExecutionPolicy Bypass -File <脚本>`（或 `pwsh -ExecutionPolicy Bypass`）
> ② `python`/`python3` 裸调失败 → 探测解释器绝对路径（WB 端 `$env:USERPROFILE\.workbuddy\binaries\python\versions\*\python.exe`；其余端 `where.exe python` 后跳过路径含 `WindowsApps\python` 的微软商店执行别名），⛔不裸调
> ③ bash 语义在 PowerShell 跑不动（heredoc / `2>/dev/null` / `find ~/ -maxdepth` 等）→ 拆独立 .py 文件调用，或改用本条登记的 PowerShell 等价命令
> ④ 解释器找不到 / 权限反复失败 → 用包根 `安装兜底.bat`（双击完成机械安装+自检，WorkBuddy 端专用）
> **Step 0 检测实证律**：分流检测必须把工具原始输出行原样贴进播报，贴不出输出=没执行=⛔DO NOT 凭已知路径进分流决策表（防"知道路径"冒充"读过路径"）。PowerShell 等价检测：`Test-Path "$env:USERPROFILE\.workbuddy\IDENTITY.md"` / `Test-Path "<MC>\.install\step7-done.md"` / `Get-ChildItem "$env:USERPROFILE" -Depth 4 -Filter 问卷答案汇总.md -ErrorAction SilentlyContinue | Select-Object -First 3`
> 告知用户时的话术底线：说"我来跑，卡在 X，需要你允许终端权限/或双击安装兜底.bat"，⛔不说"你打开 PowerShell 输入以下命令"。

> 🔌 **配置根统一注记（v2.0.1·多端）**：本文档后续手工流程段落中出现的 `~/.workbuddy/`（含 Windows `$env:USERPROFILE\.workbuddy\`）均为 **WorkBuddy 端示例落点**——非 WB 端按上方"端配置根"替换（Qoder CN=`~/.qoder-cn/`；Windows 同理换目录名）。机械安装路径（`install_scripts.py --platform <端ID>`）已自动适配，无需人工替换；⛔只有走手工分支时才按本注记替换。`$env:USERPROFILE\.workbuddy\binaries\python` 为 WB 自带解释器专属——非 WB 端直接用 PATH 上的 `python3`/`python`。

### 1. 读两端版本清单（命题③：对比读真实文件，不靠自报）
- 包内：`references/component-versions.json`（`as_of` 数据截止日）
- 用户侧：`[记忆共享中心]/.install/versions.json`（由 `install_scripts.py` 安装末尾写入）

> 用户侧文件不存在 → 判定**全新用户** → 跳过对比，直接走 Step 0 → 全量安装（不弹选择）。

**播报 B（新用户·固定稿，检测完成后必须输出）**：
> ✅ 检测完成：你机器上没有旧版本，这次是全新安装。
> 全程三步：先答 33 题（约 30 分钟，系统在认识你）→ 自动安装（每装完一段汇报一次）→ 可选装数字分身（约 20 分钟答题）。中途走开不影响，进度都记着。
> 如果你以前装过布洛陀，只是记忆中心文件夹在别的位置或叫别的名字，把路径告诉我，我重新检测一次；确实是第一次装，就直接往下走。
> 现在从答题开始？

### 2. 逐组件对比（命题①：维度高于数量）
读两张 JSON，按 `system_rules / skills / script_system / digital_twin` 逐维度比对，列出落后/缺失项。
`digital_twin` 为 `null`/缺键（老用户当年无分身，或分身快照未登记）时 **⛔不静默跳过**（跳过=让"你没装分身"这个真缺口隐身=空头免疫·违铁律-016写侧回指）：须显式输出一行「分身：未安装/快照缺失 → 如需数字分身，装完走 §数字分身完整版单装(三阶段)」，并做轻量完整性差比对（⛔不在此调 twin_maturity_check.py——它是18端成熟度终审台账器、依赖06哲学文件+端清单JSON、首装未必具备，错工具）。轻量差查三样、绑实盘：①运行件在不在（versions.json digital_twin.files vs 包内）②造芯态在不在（`<记忆共享中心>/数字分身/K2切片蒸馏/slices/core_slice.md` 及 L6 切片存在=已造芯；缺=未造芯，恒驻核读空属"未造芯"非故障，如实标注不判红）③模型配置在不在（检索岗=量化件在位、碰撞岗=Base 缓存在位，判据与 §模型体检·检测 同源实跑；非满配在播报 C 模型配置行显形。⛔此维度不进文件 diff 口径：模型非随包件，文件对账结构上看不见它，只能实测·2026-10-22 维护方定）。

### 3. 展示模板（播报 C·所有数值为 [动态项]，逐格取两端 versions.json 实测，⛔照抄示例值）
```
🏮 版本对比（数据截止日：[as_of]）
├─ 你现在：系统规则 [vX] · Skill [N] 个 · 脚本体系 [vZ]
├─ 落后 [a] 项 · 缺失 [b] 项：
│   ▸ [逐项一行：组件名 现值 → 包内值]
├─ 分身状态：[已装已造芯 / 已装未造芯 / 未安装——本次安装尚未走完，他是这套系统的一部分，说「装数字分身」随时接上]
├─ 模型配置：[两岗满配 / 缺检索岗（碰撞在岗） / 缺碰撞岗（检索在岗·碰撞停产如实标注） / 两岗皆缺，说「装模型」看完整介绍 / 分身未装则不适用]
│   （逐岗报「岗名+在岗状态」，⛔不压成"已配/未配"一句，说不清缺哪岗=知情不完整；状态取实测判据 §模型体检·检测）
```
> 🔴 老用户增量补播（2026-10-19 用户定稿）：本屏播报完，✅DO 把 Step -0.9 第 6 点「本次更新给你带来了什么」增量段**全文补播一次**（抽取规则同第6点，仅基准端点换为"本机已装版本→现版"）——首触折叠≠丢失，最关心"升级值不值"的老用户恰必须看到白话增量；补播完毕才进承诺块。

### 4. 安装模式选择（播报 D·两路线·先承诺后菜单）

**置顶承诺块（固定稿·逐字输出·逐段标题保留）**：
> **【写入承诺】你的文件，绝不会被覆盖写入。** 你在里面攒的每一条信息都原样保留，安装对这些文件只做一件事：**增量更新**，把包里新添的段落补进去，仅此而已。
>
> **【蓝本与适配】** 系统文件以 WorkBuddy 的五个文件为蓝本（SOUL、IDENTITY、USER、MEMORY、自定义指令），其他工具按各自的支持方式做适配：有的合并成一个文件承载（比如 ZCode 并进 AGENTS.md，Hermes 把 IDENTITY 并进 SOUL）。**长相会变，写法不变**，上面那句承诺对每个端同样成立。
> 还有一件事要交代：这五份系统文件和三份基本规则的模板，都是**为布洛陀系统的运转做过专门优化的**，注入机制认得出文件、规则能跨端生效、自检能核到位，靠的正是这套优化过的格式。**我们只负责把优化讲清楚，要不要沿用、还是保持你自己的写法，你来定。**
>
> **【冲突怎么办】** 某一段你自己改过、包里那段也更新了，机器猜不出该听谁的。它**绝不自作主张**：两份内容并排摆给你看，交你裁决；你没裁决之前，那段永远保持你的原样。
>
> **【备份与回退】** 动任何文件之前，先把你当时的原样整份备份进记忆琥珀。装完哪怕你哪天反悔，随时一键回退到安装前的你。
>
> **【动手之前】** 将写入的文件，先列成清单给你过目。

**路线菜单（固定稿）**：
```
好，现在选你怎么装：
① 原版安装 — 整套跟着这个包走：缺的装上，落后的追平，
   全部组件统一到包内版本。装完就是经过实测验证的那一整套
   配合，推荐。
② 自定义安装 — 你挑着装：可以只补齐缺的和落后的（没落后
   的旧件一概不动），也可以只装某一样，比如只装数字分身、
   只装某个 Skill，直接说就走单装流程，其余保持原样。
选一条，动手前我把将写入的文件列给你。
```
- 每个选项在用户确认前，**必须列出将写哪些文件/目录**（可见影响再决策，不靠护栏兜底）。
- 选 ③ 后执行：重跑 `install_scripts.py`（幂等，仅差异写入）+ 对落后/缺失 Skill 重新拷贝对应 `references/skills/<skill>/`。
- 选 ①/② 后执行：走 Step 0 → 0.5 → step1-7 全链。

> 升级关键词用户：本步即其最早分流，不重复跑全包安装的 Step 0 检测；以本步读 `.install/versions.json` 为准。

---

## §模型体检（口令直达入口 · 2026-10-22 维护方定稿·老用户知情权）

> **知情权两裁定**（2026-10-22 维护方：「不管如何，用户必须清晰的知道这2个模型是干嘛用的；在用户有充分知情权的情况下，用户才能分辨自己要怎么做」）：
> ① 呈现本体唯一=下文 §模型安装文案（C1 展示稿全文），本节只建入口，⛔不另写第二套介绍文案（双本账预防）；
> ② 入口三门共用一个后端：口令主动（本节）、升级屏被动（Step -0.6 播报 C 模型配置行）、新装链顺路（§数字分身完整版单装 Phase C1）。话术迭代只改 C1 节，一处改三门生效。

> **命名权威（用户面术语·2026-10-22 维护方「必须同意，你按专业的来」定裁）**：
> - 配置对象的用户面统一名=「检索模型」（合称「你的知识检索两个模型」）；两岗定名=「检索岗」（Large 压缩版）与「碰撞岗」（Base），全链呈现话术用此二名。
> - 入口侧收别名：用户说「引擎/检索引擎/语义模型」等一律直接路由，⛔不纠正用户措辞；输出侧呈现只用统一名，⛔拿「引擎」当配置对象的名词（「知识联邦引擎」是组件名·S739 代号撞名=隐性耦合）；「语义层/语义增强」属机制解释词，⛔上用户报态屏。
> - 例外声明：C1 展示稿「第 3 步 · 检索引擎的两条腿」为维护方审稿定稿原文照留，其「检索引擎」指检索系统本身（BM25+向量双腿），与配置对象「模型」不同所指，不构成撞名；⛔拿此例外推广输出侧旧称。

### 触发路由（两类语义·口令表见 Step -1）

命中后先读 Step 0 定记忆中心路径，跑下方检测拿到实据，再回本节报态。正在走全包安装/升级流程的用户不路由至此（流程内顺路自然遇到，防重复播报）。

| 用户说的 | 语义 | 路由 |
|:--|:--|:--|
| 模型检查 / 引擎检查 / 模型状态 / 模型装了吗 | 检查类 | 实测报态 → 非满配问「要看吗」→ 点头才进 C1 全文；⛔把只问检查的用户直接塞进安装卡（替他做了决定） |
| 装模型 / 配模型 / 配置检索引擎 | 配置类 | 实测报态 → 直接进 C1 全文（不再问要不要看） |

### 检测（R2 纪律：状态取实测，⛔不拿版本号推断、不拿 versions.json 文件对账替代、不问用户）

判据与运行时同源，⛔不造第二把尺。用 `python3` 探三样实据（表达式出处=包内 `search_kb.py` / `build_kb_vectors.py` 既有判据）：
1. **检索岗 Large 压缩版**：量化产物 `onnx/model_qint8_avx2.onnx` isfile（同 `_QUANT_READY` 判据）
2. **碰撞岗 Base**：`BAAI/bge-base-zh-v1.5` 模型缓存在位（同 `_model_available` 缓存预检判据）
3. **向量库**（参照项）：`kb_vectors.json` 存在且库标签与在位产物一致——缺则如实报"配置在位、索引未建"，路由 Phase C3 装后自检补跑，⛔不冒充满配

组合成四态：两岗皆缺（纯文字检索在跑·碰撞停产）/ 仅 Base（碰撞在岗·检索岗小模型兼着）/ 仅压缩版（检索满配·碰撞停产=设计内）/ 两岗满配（推荐形态）。

### 报态固定稿（纯文本分行·⛔屏上不出表格·⛔不压缩成"已配/未配"一句）

> 模型检查结果：检索岗 [Large 压缩版在岗 / 未在岗] · 碰撞岗 [Base 在岗 / 未在岗]。
> （满配时）两个岗都在岗，没什么要配的。
> （非满配时追加）你现在缺的是"换个说法也能搜到你的卡"，停的是"发现你自己观点互相矛盾"。这两个岗各由一个模型上岗，是哪两个、各干什么、要什么代价，完整的说一遍大约 3 分钟，30 秒也能带走结论。要看吗？

### 后续路由

- 用户点头 / 口令本来就是配置类 → 按 §模型安装文案（C1 展示稿全文）节的展示纪律**逐字完整呈现**（30 秒框在最前·⛔现场改写数字与选项·⛔摘要替代全文），用户拍板后进 Phase C2 按选路线安装，装完 Phase C3 自检，⛔静默失灵。
- 用户拒绝看 → 不再劝，回到他原本的任务；任何时候说「装模型」可重进本节，进度不丢。
- 升级屏/安装收尾时仍未满配 → 完成屏未完成项区如实披露一行：「检索模型：尚未配齐（检索岗 X · 碰撞岗 Y），说"装模型"随时回来看介绍」。口径跟 T9 完成词分级：这是能力缺口不是安装失败，⛔判红 FAIL，⛔隐身不提。

---

## 🗺️ 主线八段导航（M0~M7·2026-10-03 新增·多端合并包专用）

> **为什么加这张表**：本包把 8 端合进一个包，⛔ 不能让端 AI 各自理解"流程"——
> **主线一套，每段按本端 `capability.yaml` 变形**（装 / 变形 / 跳过三个出口）。
> 本表是**导航**，⛔ 不替代下方各 Step 的执行细则——细则仍在原处，本表只告诉你「现在走到哪、这一段归谁做」。

### 八段总表

| 段 | 名 | 做什么 | 执行载体 | 段标记 | 端变形判据（读 `adapters/<端>/capability.yaml`） |
|:--:|:--|:---|:---|:---|:---|
| **M0** | 识别 | 判端 · 判版本 · 判用户身份 · 污染检测 | **文档**<br>Step -1 / -0.5 / -0.6 / 0 / 0.5 | `m0-done.md` | `config_root` 存在性·多命中/零命中→问一次·**平台托管型端（zwork）＝无盘上配置根·判端走 Memory 面证据+问答判定兜底**（附录A-Zwork §三） |
| **M1** | **扎根** | 五系统文件 ＋ **规则层** ＋ CORE/SHADOW/快照 | **文档**<br>step1~step5 | `m1-done.md` | `system_file_paths`（含 `::` 字段级）·`rules_inject:false`→规则改走**粘贴** |
| **M2** | **立壳** | 脚本中心 ＋ 钩子 ＋ 路径声明 ＋ 覆盖层 | **代码**<br>`install_scripts.py` | `m2-done.md` | `hooks_event:false`→走 `hooks_alternative`；无替代→**跳钩子并明说** |
| **M3** | 装 Skill | 通用 Skill ＋ 软链 | **文档**<br>step6-skill-install | `m3-done.md` | `skill_symlink:false`→**明示手动**·`skill_exclusive` 列内件⛔不链他端 |
| **M4** | 装记忆 | 记忆琥珀 ＋ 未知未知 ＋ 最伟大的我 | **文档**<br>step5·5d-8 ＋ step6.5 | `m4-done.md` | 端中立 |
| **M5** | 装配 | 记忆蓝图 ＋ 成就系统 ＋ 知识联邦引擎 | **文档+代码**<br>step4/5 ＋ 链 A | `m5-done.md` | 端中立 |
| **M6** | 验收 | `verify.sh` ＋ 到货回执 ＋ 用户总账 | **代码**<br>step7 / `print_install_summary` | `m6-done.md` | 端中立（回执按 `missing_semantics` 判红） |
| **M7** | **入职** | 数字分身：答题 → 造芯 → 入职完成 | **文档**<br>step8 | `m7-done.md` | `twin_surface`：`ui_paste`→靠粘贴·`none`→明示不可用 |

### 段间播报表（固定稿·每步完成后必须播报对应行·动态项[括号]按实况替换）

| 步 | 播报 |
|:--|:--|
| 1/8 身份确认 | ✅ 第 1/8 步：确认了你在用 [端名]，安装会按这个端的规则来适配，不会装错地方 |
| 2/8 基础信息 | 第 2/8 步：认识一下——以后怎么称呼你？ |
| 3/8 路径配置 | 第 3/8 步：给系统安个家。记忆中心放在 [路径]，之后每一端 AI 都只认这一处 |
| 4/8 问卷 | 开场逐字播 `references/steps/step4-questionnaire.md`「开场播报（固定稿·动手前必须输出）」段；核验播报按 step4 4d 两源对账输出念结果（题库↔页面分叉=包内问题报修，⛔不指向用户） |
| 5/8 文件合成 | ✅ 第 5/8 步：你 33 题答案衍生的记忆文件已生成——画像、规则、契约都在里面；具体落成几个文件、放在哪，随 [端名] 的真实落位，装完清单逐条对账 |
| 6/8 钩子与 Skill | 第 6/8 步：装值班表和工具箱。[N] 个值守钩子挂进 [端名]，以后每次 AI 开工前会自动想起你的规矩；Skill 清单可在安装报告里看 |
| 6.5/8 记忆琥珀 | 第 6.5/8 步：记忆琥珀开始站岗。【它在哪】你的记忆中心里会多一个专门的"记忆琥珀"文件夹，里面还有个"永久收藏"子文件夹，你随时能打开看。【它守什么、存多久】它守护的是一份核心文件名单：系统的画像、状态快照、三层行为规则、系统文件、成就数据和十个 Skill 的定义文件。名单完全透明，想纳入别的文件加一行路径就开始守护。名单里的文件每被改动一次，就存一份当时的完整拷贝，文件名带时间戳；同一天只留一份，普通拷贝保 7 天自动轮换，你手动"收藏"的**永久保留**。名单外的不归它管，它不谎称包办一切，名单自己说了算。【它和 Git 什么关系】Git 是 AI 给自己记的变更流水账，藏在隐藏目录里，谁哪天改了哪行 AI 能替你查；记忆琥珀是给你备的完整拷贝，你自己就能打开拿走。两本账互相独立——就算流水账翻乱了，你的拷贝还在 |
| 7/8 验收 | 现在做验收：整个系统逐项自检，结果逐条列给你看（跑 verify，输出原样转述） |
| 8/8 分身入职 | D1 收卷回执：固定稿逐字「✅ 收到你的 100 题。计分器刚机械核算过：[六维信号与效度闸结果，按宣读规则逐条填真话]」——宣读规则（AI 执行面⛔念给用户）：转述 scorer 输出字段实况，⛔AI 自述；scorer 判作废时改宣读作废原因并引导重答，⛔内部代号不进话术 → D3 协商开场一句「我按你的答卷，对齐三件事」→ D4+D5 全绿才播 T9 全线完成固定稿（唯一终点宣告·见下方〈全线完成播报〉）；D5 有红→播 T9 降级态第三分支（见 step8 D5） |

> 消费硬锚（P31·2026-10-19·F8 如实化）：steps 各站头部已挂「收口必播本表对应行」prompt 锚（机械消费检查待后续版本挂 verify）——表从"仅存在"进到"有硬锚指引"；进度数字从 `[记忆共享中心]/.install/stepN-done.md` 读，⛔靠 AI 记忆（S917）。
> 播报纪律：钩子数 [N] 取装机回执实数（各端不同），⛔话术不写死；"值班表/工具箱"为 hooks/Skill 的用户面译名，机制文档保留原名。
> 🔴 分段发屏锁（2026-10-19 用户令「必须分段」）：① 每站播报=独立一条消息，⛔两站及以上播报拼进同一条回复（用户逐屏对账，合并=无法对账）；② 单站播报内含【】小节的，每个小节独立成段、段间空行（如记忆琥珀三段）；③ 清单/多级呈现每项一行，⛔逗号串联成整句；④ 本锁对全部八站+首触+T9 生效，违反=该站播报判不合格。

### M6 验收呈现（固定稿·三级·全绿才收细账，有红⛔折叠）

**第一级 一行结论**（verify 全绿时）：
> ✅ 系统验收通过：{N}/{N} 项全绿，覆盖钩子链、文件落位、备份系统、分身链路。想看逐项明细，说"验收明细"。

有任一项未过：逐条列红项+影响+处置建议，⛔收进"说详情才可见"（风险呈现律·S124）。
> 📌 **F20 注（2026-10-17）**：新装机 verify 可能有 1 条预期态红——「平台系统文件: 自定义指令 (缺失)」。该字段按设计由用户手动粘贴（安装输出已给粘贴指引），**粘完重跑 verify 即消**，不是装失败；播报时须说清消解路径，⛔让用户以为装坏了。
**第二级 装了什么清单**（数字全取装机回执/versions.json 实数，⛔写死）：
> 你机器上现在多了这些：
> · **你 33 题答案衍生的内容**——核心画像、行为规则、协作契约，落成几个文件随 [端名] 真实落位，装完清单逐条对账
> · Skill 全列表与件数：见安装报告
> · 脚本体系 {装机回执实数} 件——值守、自检、备份都靠它
> · 记忆琥珀——名单内文件改动即存拷贝
> · 数字分身：[已入职 / 未入职——没入职他=这次安装没有完成]
**第三级 指路**：
> 明细都在安装报告里，随时说"安装报告"调出来。{下一步指针：分身未入职→接入职播报；已入职→T9 全线完成播报}

### 三条硬纪律（⛔ 违反即返工）

| # | 纪律 | 为什么 |
|:--|:---|:---|
| 1 | **数字分身必须最后**（M7） | 前六段装的是壳与料，第七段才点着火——**没壳，装火柴没用** |
| 2 | **规则层只装一次**（在 M1） | 链 A 里的 `install_rule_files` 仅作**补缺**（用户升级补差），⛔ 不是"再装一遍" |
| 3 | **跳过必须说出口** | 豆包端 M2/M3 会跳过——⛔ 静默跳过＝用户以为装漏了 |

### 段间依赖（机械判据）

```
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7
✅ 上一段标记文件不存在 ⇒ 本段阻塞（不预读后续细则）
✅ 段标记统一 m0-done.md ~ m7-done.md（替代旧 stepN-done.md·迁移期两者并存）
### ⚠️ 两套标记的关系（2026-10-03 补·防「两套并存」被读错）

| | 是什么 | 谁写 | 用途 |
|:--|:---|:---|:---|
| `stepN-done.md` | **实际依赖标记** | 各步骤文档（step1~step7） | 前置阻塞检查·⛔ 删了会让升级用户的链断 |
| `mN-done.md` | **主线进度视图** | **⛔ 不单独写·由 stepN 派生** | 给人看的「八段走到哪」 |

**映射（mN 达成 ⇔ 对应 stepN 存在）**：

| 主线段 | 达成判据 |
|:--|:---|
| M0 识别 | `step3-done.md`（路径配置完成＝识别收尾）|
| M1 扎根 | `step5-done.md`（五系统文件＋规则层合成完成）|
| M2 立壳 | 链 A 输出「部署后自检 ✅」 |
| M3 装 Skill | `step6-done.md` |
| M4 装记忆 | step6.5 记忆琥珀安装完成 |
| M5 装配 | 模板复制完成（step5 · 5d-8）|
| M6 验收 | `verify.sh` 无 FAIL |
| M7 入职 | `step8-done.md` |

> ⛔ **不改各步骤文档的 stepN 标记**——那是真实依赖链，改名＝全断。
> ⛔ **不单独写 mN 文件**——它是派生视图，双写必漂。
```

---

## Step 0：自动分流检测

先执行 3 个文件系统查询（Bash `ls` 实际验证，不用 Read，不用猜）：

```bash
# 检测 1：是否有已有的记忆系统文件（CONFIG_ROOT=Step -0.5 判定端的 capability.yaml config_root·⛔不裸写 ~/.workbuddy——G2-2 根治：裸写=非WB端老用户被误判全新）
ls "$CONFIG_ROOT/IDENTITY.md" 2>/dev/null && echo "FOUND_IDENTITY"

# 检测 2：是否有 .install 标记（旧版布洛陀或安装过至少一次）
# ⚠️ 以下路径是已知可能位置——如果用户记忆共享中心不在这些路径，
#    检测2结果为❌不影响决策（走半安装态或全新），不阻塞流程。
ls [记忆共享中心]/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER"
ls ~/AI记忆库/.install/step7-done.md 2>/dev/null && echo "FOUND_INSTALL_MARKER_ALT"

# 检测 3：是否有问卷答案（用于升级时补差异）
# ⚠️ 搜不到不等于没有——可能路径不同。走"老用户·问卷丢"兜底。
find ~/ -maxdepth 4 -name "问卷答案汇总.md" 2>/dev/null | head -3
```

> 🛡️ **Step 0.7 写前探测硬闸（定 MC 后·落任何文件前·2026-10-21 立·Win E盘安全策略拦截案）**：安装/升级模式动工前必须完成目标 MC 的 mkdir+试写+试删探测——`install_scripts.py` 内置机械硬闸（⛔不依赖 AI 记得执行文档条款，忘了也会被脚本拦住并打印指路），`fallback_install.ps1` 同语义；AI 代跑安装时同样先跑探测再进机械段。探测被拦时的定责与指路（读给用户）：①最常见来源=Windows Defender「受控文件夹访问」或第三方杀软勒索防护对批量脚本写入（本安装落 289+ 件）的误拦，**不是安装包代码出错** ②放行指引：Defender→病毒和威胁防护→管理受控文件夹访问→添加允许应用（python.exe），或把目标目录移出保护文件夹；第三方杀软找「信任/白名单」类入口 ③替代路径：先装默认位（`%USERPROFILE%\个人AI档案`）跑通全链再迁移；E/D 等非系统盘安装必须先过探测 ④半安装态安抚：之前装到一半失败**不用返工**——放行后重跑安装，Step 0 分流自动判「半安装态」走修复模式接着修，rollback 兜底件在包。

**分流结果播报（固定稿·检测完成后必须输出·E）**：
> ✅ 环境检测完成：你的情况是**[全新安装／老用户升级／半安装修复]**，接下来走[对应路线一句话]。
> （AI 注记·⛔不照读：按分流决策表读取对应文件，不停顿不提问；下方决策表面向 AI 不面向用户）

### 分流决策表

| 检测 1 | 检测 2 | 检测 3 | 用户类型        | 路由                                            |
| :--: | :--: | :--: | :---------- | :-------------------------------------------- |
|  ❌ 无 |  ❌ 无 |  ❌ 无 | **全新用户**    | → 读 `README.md`（产品介绍） → 然后读执行文件，执行步骤1→7（含33题） |
|  ✅ 有 |  ✅ 有 |  ✅ 有 | **老用户·问卷在** | → 读执行文件，走升级模式（自动跳过问卷→检测系统文件差异→展示→确认→备份→完成）    |
|  ✅ 有 |  ❌/✅ |  ❌ 无 | **老用户·问卷丢** | → 见下方「老用户问卷兜底」                                |
|  ❌ 无 |  ✅ 有 |  ❌ 无 | **路径迁移**    | 同老用户·问卷丢（先找问卷，再升级）                            |
|  ✅ 有 |  ❌ 无 |  ❌ 无 | **半安装态**    | 读执行文件，走修复模式                                   |

---

### 🎯 为什么必须完成 33 题？（固定稿·答题前必须播报）

> **接下来是全程最重要的一步：33 题。** 这是整套安装里唯一"系统在认识你"的环节，约 30 分钟，答完中途可以停，答案存着接着答。
>
> **【你的答案都有明确去处】**
> · 7 题价值观与取舍 → 记忆中心的**核心层**，之后系统"像你一样判断"的依据就在这
> · 8 题怎么想 + 6 题怎么做 + 3 题协作契约 → **用户基本规则**（认知/行为/契约三段），AI 干活守的规矩从此为你定制，不是通用的
> · 2 题说话方式 → **品格文件**，决定你在每端看到的 AI 是什么腔调
> · 2 题你的画像与当下需求 → **用户画像文件**；3 题近期目标与状态 → **动态状态快照**，它记得你最近在哪件事上使劲
> · 2 题知行偏差、希望被怎么提醒 → **潜意识层**，这 2 题给了它指出你不想承认之事的资格
>
> **【答完第一份给你的东西】** 验证通过后，你会收到一份《底层洞察与协作契约报告》：全彩网页，基于你自己的答卷，分析你的核心驱动力、思维模式和跟 AI 的协作契约，浏览器打开就能看。这 30 分钟值不值，先看这份报告就知道。

> 📌 **新老用户都一样：33 题是安装前置条件，答完才继续装；中途可停，答案会存着接着答。**（门规保留为最后一句，⛔不作开场白·2026-10-13 用户定"价值先行"姿态）
> ⚠️ 落点与文件归属以 `references/steps/step5-file-synthesis.md` 5b-2/5d 合成表为唯一真源（本段为其实操翻译，修订须回表对账·承条文19 判据-对象同源）。旧文案中「MEMORY.md（你的协作契约）」表述作废：契约题实进用户基本规则摘要版契约段，MEMORY.md 为通用骨架（2026-10-13 声明-实盘矛盾订正）。


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

| 禁止              | 原因                         |
| :-------------- | :------------------------- |
| ❌ 问"你是新用户还是老用户" | INSTALL.md 做检测就是为了一句话不说先判断 |
| ❌ 停住等用户回答       | 检测完了出报告，然后继续干活             |
| ❌ 同时读多个步骤文件     | 薄入口，一次一步，按需加载              |
| ❌ 跳过问卷（任何理由）    | 33题是安装前置条件，不完成不走下一步        |

> 例外：如果用户明确说了「装 XX Skill」/「install XX skill」或「装记忆琥珀」/「install memory amber」或「装成就系统」/「install achievement」（含中英文），跳过全包安装，走对应轻量路由。

### 检测完成输出模板

```
🏮 布洛陀 2.2.11 安装检测
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

## §升级检测（用户说"升级"时走这里 · 自动读旧版→比新版→展示缺啥）

> 🔴 用户说「升级 / upgrade / 更新」→ **不再走本独立章节**，改为 Step -1 直接路由到 **Step -0.6 版本对比与安装模式选择**（组件级对比 + 全量/局部选择）。
> 原 CHANGELOG 口径的抽取逻辑已并入 Step -0.6，避免双本账（命题④ 交付物唯一）。下方为历史实现，保留仅作参考，**以 Step -0.6 为准**。

### 1. 先确认你是老用户（复用 Step 0 检测 1/2/3）
检测 2 命中 `[记忆共享中心]/.install/step7-done.md`（或 `~/AI记忆库/...`）即老用户。
然后**读你当前版本号**：

```bash
OLD=$(cat "[记忆共享中心]/.install/version" 2>/dev/null)
[ -z "$OLD" ] && OLD=$(cat "$HOME/AI记忆库/.install/version" 2>/dev/null)
if [ -z "$OLD" ]; then
  echo "NO_VERSION_MARKER：你装的早于 v1.5.0，机器上无版本记录。"
  echo "→ 按『全量变更』展示（见第 3 步兜底），或确认是否走全新安装。"
else
  echo "INSTALLED_VERSION=$OLD"
fi
```

### 2. 读包内新版 + 比较
```bash
NEW=$(grep '^version:' version.md | head -1 | sed -E 's/.*"([0-9.]+)".*/\1/')
echo "PACKAGE_VERSION=$NEW"
```
- `$OLD` 为空（<1.5.0）→ 直接进第 3 步，按全量变更展示。
- `$OLD` ≥ `$NEW` → 输出「✅ 已是最新（X.Y.Z），无需升级」→ 结束。
- `$OLD` < `$NEW` → 进第 3 步。

### 3. 抽取「自你那版起需做何升级」
CHANGELOG.md 按 `## [X.Y.Z] — DATE` 分段（降序），维护公约只记对用户有用的变更。机械抽取 `(OLD, NEW]` 区间——从顶部打印到 `[OLD]` 段（不含）为止：

```bash
awk -v old="$OLD" '
  /^## \[/ && index($0, "[" old "]") > 0 { exit }   # 遇到你那版就停
  { print }
' CHANGELOG.md
```
> ⚠️ 顶部最新段（`[未发布]` = 本包相对上发的全部增量）必纳入；发版时把 `[未发布]` relabel 成 `[1.6]` 抽取才干净（公约见下条）。
> ⚠️ 维护公约：每次发版把 `[未发布]` relabel 成 `[版本号]`，抽取才干净。

### 4. 展示模板
```
🏮 布洛陀升级检测
├─ 你当前：X.Y.Z
├─ 最新包：A.B.C
├─ 自你那版起，需做这些升级：
│   ▸ vA.B.C（日期）：…（条目逐条）
│   ▸ v…（日期）：…
│
⚡ 下一步：你确认后，读执行文件走「升级模式」同步
   （跳过问卷 → 检测系统文件差异 → 展示 → 确认 → 备份 → 完成）
```

### 5. 交执行文件「升级模式」
展示完毕 → 读**执行文件**，走升级模式（自动跳过问卷 → 检测系统文件差异 → 展示 → 确认 → 备份 → 完成）。


## Step 0.5：数据污染检测（全路径强制 · 全新/升级/重装都跑）

> **为什么**：早期版本的部分文件中，混入了开发阶段遗留的**样例数据**（带真实感的占位内容，对你无用）。本步在**任何安装路径**下都先跑一次，**精准清除这些样例数据、绝不触碰你自己的记录**：
>
> - 有你手写记录的文件（SHADOW / 未知未知）→ 用完整 SHA256 **逐条精确比对**，只删命中的样例块，你自己的条目哈希不同、**数学上零误删**、完整保留；
> - 成就系统（tracker 管辖的运行时数据，⛔不整体重置）→ 仅精准清除**历史发布包曾带出的作者侧泄露行**（逐条行级哈希比对，只清作者的不碰你自录的；你的成就数据原样保留继续累积）。
>
> 参照物 `integrity-fingerprints.json` 是**不可逆哈希指纹**（无原文、无法读取还原）。改前自动 `.pre-decontam.bak` 备份，可回滚。

**污染检测播报（固定稿·Step 0.5·这步必须让用户看见它在护他·F）**：
> 🧹 **装前体检**：清除历史版本残留的**样例数据**：开发时塞进去的演示内容，对你是垃圾，留着会污染你以后的判断。
> 这步怎么保护你，分两种文件：
> · 有你手写记录的文件（潜意识层、盲区记录）：只删**逐条哈希指纹精确匹配**的样例块。你自己的条目哈希不同，**数学上零误删**，一条都不会动；
> · 成就系统（自动累积的行为数据）：**不重置你的东西**，只精准清除早年发布包曾带出的**作者侧**成就数据（书名、达成日期那类），逐条哈希比对，只清作者的不碰你自录的。
> 动手前自动留备份（改前快照），随时可回滚。
> 结果播报（脚本实数）：检出 N 处样例已清除，你的 M 条手写记录完整保留 / 机器很干净，无残留。

**执行（Step 0 确定记忆中心路径后，立即跑一次）**：

```bash
python3 "<安装包>/data_contamination_check.py" \
  --memory-root "<记忆共享中心>" \
  --fingerprints "<安装包>/references/integrity-fingerprints.json" \
  --template-root "<安装包>/references" \
  --apply
```

Windows(PowerShell) 等价（用自带 `python.exe` 绝对路径，见下方块）：

```powershell
$py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
& $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
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
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户**明确说了**「装 XX Skill」/「install XX skill」时，走此路径，不跑全包安装。  
> 支持中英文：装/安装/install + 中英文 Skill 名。

### Skill 名映射

| 用户说的                 | 目录                                        |
| -------------------- | ----------------------------------------- |
| 每日伙伴 / daily-buddy   | `references/skills/daily-buddy/`          |
| 三明智 / triwich        | `references/skills/triwich/`              |
| 反方向的钟 / clock-loop   | `references/skills/clock-loop/`           |
| 成长箱 / growth-box     | `references/skills/growth-box/`           |
| 唤醒记忆 / awaken-memory | `references/skills/awaken-memory-system/` |
| 读书助手 / sucair / 素裁   | `references/skills/sucair/`               |
| 系统日志 / system-logger | `references/skills/system-logger/`        |
| 迁理之外 / meta-aletheia | `references/skills/meta-aletheia/`        |
| Shall We Talk / SWT  | `references/skills/shall-we-talk/`        |
| 好好学习 / good-good-study | `references/skills/good-good-study/`    |


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
   python3 install_scripts.py --platform "$PLATFORM_ID" --deploy-skills "$MEMORY_CENTER"   # 主路径（逐件本地化+损失清单）
# 兜底（仅安装器不可用时）：
cp -r references/skills/"$SKILL"/* "$MC/技能配置/$SKILL/"

   # 替换占位符
   find "$MC/技能配置/$SKILL/" \( -name "*.md" -o -name "*.py" -o -name "*.sh" \) -exec perl -i -pe "s|\[记忆共享中心\]|$MC|g" {} \;
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
   Copy-Item "references/skills\$SKILL\*" "$MC\技能配置\$SKILL\" -Recurse

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
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

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
4. **Windows**：用 PowerShell `Copy-Item` + `(Get-Content).Replace()`，逻辑一致。
5. **验证**：`ls [记忆共享中心]/成就系统/scripts/achievement_tracker.py` 存在 ✅

---

## 记忆琥珀单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
>
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
>
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。  
> **Windows(PowerShell)**：
>
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户说「装记忆琥珀」/「安装记忆琥珀」/「install memory amber」时，走此路径。


### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **macOS 安装**：

   ```bash
   MC="<记忆共享中心绝对路径>"
   mkdir -p "$MC/记忆琥珀/engine/logs"

   # 复制脚本
   cp references/记忆琥珀/scripts/amber_backup.sh "$MC/记忆琥珀/engine/"
   cp references/记忆琥珀/scripts/amber_fswatch_wrapper.sh "$MC/记忆琥珀/engine/"
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
   cp references/记忆琥珀/scripts/com.memoryamber.backup.plist.template ~/Library/LaunchAgents/com.memoryamber.backup.plist
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
   - Windows：`Get-ScheduledTask -TaskName "MemoryAmberWatch" | Select State` 期望 `Running`；再查心跳 `Get-Content "$MC\记忆琥珀\engine\logs\amber-watch.heartbeat"`（`yyyy-MM-dd HH:mm:ss` 本地时间，距今 < 90 秒；Windows 无 /tmp，⛔勿照 macOS 口径查 /tmp）

---


## 脚本体系单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同下方「确定记忆中心路径」步骤），**再立即**跑一次数据污染检测（与 Step 0.5 同一动作），通过后**才**进入下方安装步骤：
> ```bash
> python3 "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" \
>   --fingerprints "<安装包>/references/integrity-fingerprints.json" \
>   --template-root "<安装包>/references" --apply
> ```
> 全新/已净化 → 0 命中自动跳过；命中即清理（改前自动 `.pre-decontam.bak` 备份，用户自录数据完整保留）。
> **Windows(PowerShell)**：
> ```powershell
> $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName
> & $py "<安装包>/data_contamination_check.py" --memory-root "<记忆共享中心>" --fingerprints "<安装包>/references/integrity-fingerprints.json" --template-root "<安装包>/references" --apply
> ```

> 用户说「装脚本体系」/「安装脚本体系」/「install script system」时，走此路径。
>
> **目的**：把**完整脚本体系**（路由引擎 + 铁律硬墙 + 未知未知兜底 + 各类守卫）一次装齐，并在用户机器上生成**脚本中心文件夹** `[记忆共享中心]/脚本中心/`——那是用户拥有的完整脚本副本，便于查看、二次开发、出问题自查。装完会同时把铁律硬墙的**触发规格数据** `rule_triggers.yaml` 落到 `[记忆共享中心]/记忆规则/`——⛔缺它硬墙装上也静默不工作（实测：无报错、零注入）。
>
> ⚠️ 若尚未部署三层规则文件（用户基本规则-铁律版.md 等），本流程会一并补全到 `[记忆共享中心]/记忆规则/`——铁律硬墙的预注入依赖它，缺则硬墙自动降级为「不注入」而非报错（不会崩对话）。
> 🔴 已装过部分脚本（如路由引擎）的用户走此路径会**幂等补齐全集**，不重复、不破坏现有钩子。


### 安装步骤

1. **确定记忆中心路径**（同单 Skill 安装步骤1）

2. **macOS / Linux**：

   ```bash
   MC="<记忆共享中心绝对路径>"

   # 脚本体系一次装齐（①脚本中心 ①b 规则数据 ②钩子部署 ③钩子注册）——同一份总表驱动，幂等可重跑
   python3 install_scripts.py "$MC"          # WorkBuddy（默认）
   # 其余端：python3 install_scripts.py --platform <端ID> "$MC"（端ID 见 Step -0.5）
   # 想先看会做什么： python3 install_scripts.py --dry-run "$MC"
   # 想看钩子总表：   python3 install_scripts.py --list
   # 规则层（触发规格 rule_*.yaml + 三层规则文件）由安装器一并落位，无需手工再拷
   ```

#### ⚠️ Windows 平台差异说明（装「脚本体系」前请先读这段）

脚本中心共 **287 个文件**（F11 根治·2026-10-17·实测落盘值·旧文「65 个」漂移 4 倍）：**250 个 `.py`**（三端通用，含测试脚本）+ **32 个 `.sh`**（macOS/Linux 专用）+ **2 个 `.yaml` 触发规格** + 3 件辅助（.ps1/.json/.md）。件数以装机回执实数为主·⛔不写死。

| 你的情况 | 那 5 个 `.sh` 能跑吗 | 你该怎么做 |
|---------|:-------------------:|-----------|
| 装了 Git for Windows | 能跑 | 用 Git Bash 执行即可 |
| 没装 | 跑不了 | 装 Git for Windows<br>（自带 Git Bash）<br>或者：直接忽略这批 |

**不影响你什么**：核心系统——Hook 钩子、铁律规则硬墙、未知未知兜底、记忆系统——**全部是 `.py`**，
Mac / Windows / Linux **三端通用，一样都不缺**。那 5 个 `.sh` 只是**附带的小工具**，
跑不了也不影响系统运转。

> 说明：安装包**只带端用户实际用得上的脚本**（58 个 .py）。作者本机专用的多端巡逻 / 控制环 / git 门禁 /
> 面板监视等工具**不在包内**——它们依赖的设施（其他 AI 端、launchd、作者仓库）在你的机器上并不存在。

3. **Windows**：

   ```powershell
   $MC="<记忆共享中心绝对路径>"
   $py = (Get-ChildItem "$env:USERPROFILE/.workbuddy/binaries/python/versions/*/python.exe" | Select-Object -First 1).FullName

   # 脚本体系一次装齐（①脚本中心 ①b 规则数据 ②钩子部署 ③钩子注册）——同一份总表驱动，幂等可重跑
   & $py install_scripts.py "$MC"
   # 想先看会做什么： & $py install_scripts.py --dry-run "$MC"
   # 规则层（触发规格 rule_*.yaml + 三层规则文件）由安装器一并落位，无需手工再拷
   ```

4. **钩子总表**（部署与注册已在步骤 2 由安装器自动完成；此表供查阅，`install_scripts.py` 里的 `ROSTER` 是唯一数据源）：

| 事件 | 钩子 | 干什么 |
|:---|:---|:---|
| UserPromptSubmit | `route_inject_prompt.py` | 路由命中 Skill/铁律即预注入 |
| UserPromptSubmit | `rule_fragment_inject.py` | 铁律硬墙：命中条件预注入条文 |
| UserPromptSubmit | `secret_key_guard.py` | 密钥/Token 粘贴提醒不外流 |
| UserPromptSubmit | `ttl_expiry_guard.py` | 规则文件过期自动提醒 |
| UserPromptSubmit | `session_tail_inject.py` | 新会话注入上次收工与欠账 |
| Stop | `route_unknown_unknown.py` | 未知未知兜底·盲区自动登记 |
| Stop | `rule_three_layer_guard.py` | 校验回复格式契约三项齐全 |
| Stop | `systemlog_stophook_check.py` | 校验今日系统日志是否收口 |
| Stop | `reply_tail_guard.py` | 检测回复"留尾巴"并提醒收口 |
| Stop | `post_change_guard.py` | 检测改 A 漏更新 B/C/D |
| Stop | `delivery_boundary_guard.py` | 检测交付里没说清的静默取舍 |
| PreToolUse | `edit_heading_guard.py` | 拦标题结构行被误改 |
| PreToolUse | `skill_write_gate_guard.py` | 未启动 Skill 就写管辖目录则拦 |
| PreToolUse | `skill_spec_read_guard.py` | 改 Skill 前未读规范则提示 |
| PreToolUse | `grep_sandbox_guard.py` | 拦本环境不支持的 grep 转义 |

> 🔴 **Hermes 端读上表必看（2026-10-02 实证）**：上表 `PreToolUse` 是 **ROSTER 的登记事件名**，
> 而 **Hermes 侧不存在 `PreToolUse` 这个事件**——该名不会派发。
> 上表 4 个守卫在 Hermes 上**确实生效**，但走的是**另一条通道**：
> `adapters/hermes/plugins/buluotuo-pretool-guards` 插件内 `ctx.register_hook(<事件名>, fn)`，
> 事件名为 `pre_tool_call`，由 `plugin.yaml: provides_hooks` 声明。
>
> **自查命令**（判断"这守卫到底跑没跑"的唯一可靠方式）：
> ```bash
> # Hermes 端 · 查真实拦截记录（有 BLOCK 行 = 守卫真在跑）
> tail -5 ~/.hermes/pretool_guards_hook.log
> ```
> ⛔ **只看 `settings.json` 会误判**（那 4 条 PreToolUse 条目是无效挂载）。
> 其他端（WorkBuddy / Qoder CN / ZCode）的 `PreToolUse` **是真事件名**，⛔ 不要照抄 Hermes 的结论。
| SessionStart | `crossend_guard.py` | 检测别的 AI 端是否污染家目录 |
| UserPromptSubmit | `doenglingz_inject_prompt.py` | 数字分身·人格注入 |
| Stop | `twin_verdict_ledger.py` | 数字分身·裁决台账 |
| Stop | `twin_changelog_guard.py` | 数字分身·规格书同步守卫 |

> 📌 **钩子总表由包根 `install_scripts.py` 的 `ROSTER` 数组单一驱动**（搬运与注册读同一份数据）——新增/停用钩子只改那一处，机制上不可能出现"登记了却没装文件"。`python3 install_scripts.py --list` 随时可查。
>
> **不在 ROSTER 的脚本**（F2b 根治·2026-10-17·沙箱实测）：仅 `guard_doc_consistency` 一件真不装机（需作者侧守卫文档·端用户机无对象可守）。
>
> ⚠️ **旧表纠错**：旧文列「有意不激活」7 件，其中 6 件（route_audit / route_miss_feeder / route_guard_audit / change_closedloop_guard / design_family_guard / vision_gate）**实际在 ROSTER 中、会随装机注册**——它们消费的是**用户自己机器上的路由/日志数据**（端用户态可审计·非作者侧设施），旧表「依赖作者侧设施」判断已过时。实盘准绳 = `install_scripts.py --list`（ROSTER 唯一数据源）：
>
> | 脚本 | 状态 |
> |:---|:---|
> | `guard_doc_consistency` | 真不装机（需作者侧守卫文档·端用户机无对象） |
> | 上述 6 件 | 在 ROSTER·随装机注册（消费本机数据·端用户态可用） |
>
> **数字分身·人格漂移体检月度机制**（可选·macOS）：分身部署完成后，可注册月度漂移体检提醒——每月 1 号 09:00 机械判定距上次人格保真盲评是否 ≥30 天，到期写提醒日志，由你的 AI 会话读到后执行体检（机制通用、盲评内容须由你自己的分身蒸馏产物生成）。注册方式：
>
> ```bash
> # 前提：数字分身已部署（下文 [数字分身中心] = 你的数字分身目录，含 scripts/ 子目录）
> cp references/digital-twin/scripts/com.doenglingz.drift-check-remind.plist.template \
>    ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist
> perl -i -pe 's|\[数字分身中心\]|'"$DT"'|g' \
>    ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist   # $DT=你的数字分身目录绝对路径
> cp references/digital-twin/scripts/doenglingz_drift_check_remind.py "$DT/scripts/"
> launchctl load ~/Library/LaunchAgents/com.doenglingz.drift-check-remind.plist
> launchctl kickstart -k gui/$(id -u)/com.doenglingz.drift-check-remind   # 首跑验证（应输出"未到期"或"state 未初始化"）
> ```
>
> 首跑提示"state 未初始化"属正常——完成首轮人格盲评后，让 AI 会话写 `scripts/drift_check_state.json`（`{"last_check": "YYYY-MM-DD"}`）即进入月度循环。
>
> **分身同步周期守护 slice-watch（推荐注册·双端·声明见 `references/digital-twin/guardians.json`）**：不注册本守护时无人刷 `state_bus.json`，tsl_verify L6 显示 ⚪「本机未启用自动同步」——这是正常降级提示（分身本体不受影响，改完分身说一句「更新分身切片」即可手动刷新）。注册后：首轮自动按**本机安装事实**种子初始化端账本（⛔不需要你提供作者侧端清单文件·v2.2.0 起装机态端清单真源=部署注册表派生），首轮即显示真状态（✅全最新/🔴M个旧版/🟡账本超龄/⚪未启用）；此后新装/卸载工具每轮自动增量入账，Mac 与 Win 同机制（执行体同一份平台中性 python）。
>
> ```bash
> # macOS：$MC=你的记忆共享中心绝对路径
> cp references/digital-twin/scripts/com.doenglingz.slice-watch.plist.template \
>    ~/Library/LaunchAgents/com.doenglingz.slice-watch.plist
> perl -i -pe 's|\[记忆共享中心\]|'"$MC"'|g' ~/Library/LaunchAgents/com.doenglingz.slice-watch.plist
> launchctl load ~/Library/LaunchAgents/com.doenglingz.slice-watch.plist
> launchctl kickstart -k gui/$(id -u)/com.doenglingz.slice-watch   # 首跑验证：数字分身/state_bus.json mtime 应被刷新
> ```
>
> ```powershell
> # Windows：注册同名定时任务（含卸载对称 -Uninstall）
> pwsh -ExecutionPolicy Bypass -File "$MC\数字分身\scripts\slice-watch-install-task.ps1"
> # 验证：Get-ScheduledTask -TaskName DoenglingzSliceWatch ；state_bus.json mtime < 25h
> ```
>
> **蒸馏调度月拍守护 distill-scheduler（推荐注册·双端·声明见 `references/digital-twin/guardians.json`）**：蒸馏/体检的"该做了"提醒靠调度器按时跑（每日幂等检查·无到期静默·月首自然带出待做清单）。不注册时提醒只在开对话的巡检里带出；注册后低频用户也不断"越用越好用"的承诺。
>
> ```bash
> # macOS：$MC=你的记忆共享中心绝对路径
> cp references/digital-twin/scripts/com.buluotuo.distill-scheduler.plist.template \
>    ~/Library/LaunchAgents/com.buluotuo.distill-scheduler.plist
> perl -i -pe 's|\[记忆共享中心\]|'"$MC"'|g' ~/Library/LaunchAgents/com.buluotuo.distill-scheduler.plist
> launchctl load ~/Library/LaunchAgents/com.buluotuo.distill-scheduler.plist
> launchctl kickstart -k gui/$(id -u)/com.buluotuo.distill-scheduler   # 首跑验证：蒸馏中心标记区 mtime 应被刷新
> ```
>
> ```powershell
> # Windows：注册同名计划任务（含卸载对称 -Uninstall）
> pwsh -ExecutionPolicy Bypass -File "$MC\数字分身\scripts\distill-scheduler-install-task.ps1"
> # 验证：Get-ScheduledTask -TaskName BuluotuoDistillScheduler ；蒸馏中心.md 标记区 mtime < 25h
> ```
>
> **记忆健康自动巡检（推荐注册·双端·规格单真源 `awaken-memory-system/references/patrol.md` §3）**：每 6 小时巡检快照滞后+蒸馏待办；不注册时仪表盘「巡检趋势」显示「本机未注册自动巡检+本指引」（降级不阻塞·双模式会话内巡检照常可用）。
>
> ```bash
> # macOS：$MC=你的记忆共享中心绝对路径
> cp references/skills/awaken-memory-system/scripts/com.buluotuo.awaken-patrol.plist.template \
>    ~/Library/LaunchAgents/com.buluotuo.awaken-patrol.plist
> perl -i -pe 's|\[记忆共享中心\]|'"$MC"'|g' ~/Library/LaunchAgents/com.buluotuo.awaken-patrol.plist
> launchctl load ~/Library/LaunchAgents/com.buluotuo.awaken-patrol.plist
> launchctl kickstart -k gui/$(id -u)/com.buluotuo.awaken-patrol   # 首跑验证：~/buluotuo_bin/log/awaken_patrol.log 应现四段留痕
> ```
>
> ```powershell
> # Windows：注册同名计划任务（含卸载对称 -Uninstall）
> pwsh -ExecutionPolicy Bypass -File "$MC\技能配置\awaken-memory-system\scripts\awaken-patrol-install-task.ps1"
> # 验证：Get-ScheduledTask -TaskName BuluotuoAwakenPatrol ；$env:USERPROFILE\buluotuo_bin\log\awaken_patrol.log 现四段留痕
> # 触达说明：Win 端告警=pending 落盘（$env:USERPROFILE\buluotuo_bin\log\awaken_patrol_alerts.pending），说「小美」会话内转述后自动清除
> ```
>
> ⚠️ **`skill_write_gate_guard` 留痕机制**：它硬拦"未启动对应 Skill 就直接写管辖目录（技能配置／成长箱／数字分身／发布库／`~/.workbuddy/`）"。被拦时先启动对应 Skill，或显式留痕 `mkdir -p ~/.cache/skill_gate && touch ~/.cache/skill_gate/{域}.active`（4 小时有效）后重试。**纯读命令（ls/find/grep/cat…）已放行**，不误拦。


5. **验证**：
   - `ls <记忆中心>/脚本中心/rule_fragment_inject.py` 存在 ✅（脚本中心已生成）
   - `python3 <记忆中心>/知识联邦引擎/scripts/extract_concepts.py status` → 显示概念库进度 ✅（卡引擎已装）

> **🧬 卡生产引擎（随脚本体系自动装配）**：**独立部署**到 `<记忆共享中心>/知识联邦引擎/`（2026-10-03 从脚本中心下独立，⛔ 不在脚本中心内）——支撑每日伙伴晚间复盘的**概念抽卡**（5.5 管道）与好好学习的**落卡/碰撞**。全部路径自适应记忆共享中心，无需配置；语义增强（bge 模型·可选）未装时，概念抽卡照常，碰撞扫描明确退出（不静默），检索降级为纯文字匹配。
>
> 💡 **完整的数字分身（含可选语义增强 / bge 模型·知情同意后自选）**见 §**数字分身完整版单装**——用户说「装数字分身」时走那条路。
   - `python3 install_scripts.py --list` → 38 个钩子，事件分布 9 / 23 / 5 / 1 ✅（F2：旧文 19·6/8/4/1 与实盘脱钩）
   - 安装器末尾自检会输出 `✅ 部署后自检：38 个钩子 + 依赖件全部落盘`（缺件即 exit 1 并列出文件名）
   - `python3 ~/.workbuddy/hooks/rule/rule_fragment_inject.py --selfcheck` → 覆盖守卫对齐 ✅
   - 说一句「帮我把 config.json 改成 production 模式」→ 回复里出现【铁律自动预注入·触发命中 001】✅

---

## 数字分身完整版单装（轻量路由）

> 🔴 **前置·全路径强制（装任何内容前的第一件事，不可跳）**：先确定记忆中心路径（同「脚本体系单装」），**再立即**跑一次数据污染检测（命令与「脚本体系单装」前置完全相同），通过后**才**进入下方安装步骤。

> 用户说「装数字分身」/「装分身」/「装抽卡」/「装卡引擎」时，走此路径。
>
> **目的**：让数字分身（童灵 / Doenglingz）在你的机器上**全功能可用**——人格注入、守护、切片、漂移体检、抽概念卡（晚间复盘）、落卡碰撞（好好学习）、检索你自己的立场卡。本流程与「脚本体系单装」**平行**，但 **Phase A 依赖脚本体系已装**（19 钩子须含分身三钩子）。
>
> **三条设计律**：① **零私人外露**——发布者的卡库/语料/索引零进包，你的卡全是自己生产的；② **降级不阻塞**——语义引擎（bge 模型）是**可选增强**，任一步失败回退无模型态，复盘/对话永不崩；③ **幂等可重跑**——重复执行不破坏已有钩子（对齐 `install_scripts.py` 既有纪律）。

### 三阶段流程

```text
Phase A 分身基座（零下载·即装即用）
  ├─ A1 前置检查：脚本体系已装？（19 钩子含分身三钩子）
  │      未装 → 先引导走「脚本体系单装」再回来
  │      ⚠️ ZCode 端口径（2026-09-30 立·2026-10-03 扩 7 件）：钩子由 adapters/zcode/setup.sh
  │      幂等注册（ZCode 形态 7 件 = UserPromptSubmit: inject_prompt+position3_notify+tsl_echo_hook /
  │      Stop: guard_zcode+level_declare+tsl_closeout+twin_verdict_ledger+twin_changelog_guard·
  │      件在才挂·缺件不阻塞），
  │      「19 钩子」系 settings.json 端（WB/Qoder 系）口径——ZCode 走委派路径自动补齐，
  │      通用层钩子由 --platform zcode 公共部署+端 setup 双层承接
  ├─ A2 部署 [记忆共享中心]/数字分身/ 目录骨架
  │      （devtools 钩子件 + gates + hexaco 答题件
  │       + k2 造芯三件 + onboarding 引导三件）
  │      onboarding/ ＝ 人格向量空模板 + 规格书骨架
  │      ＋ 通用入门指南（造芯全端统一·见养成链）
  └─ A3 就绪检查 → 进入「分身养成链」（两步入职）让分身活起来

Phase B 卡生产链路（最小件·无模型·核心增量）
  ├─ B1 落位引擎最小件 → [记忆共享中心]/知识联邦引擎/scripts/
  ├─ B2 路径参数化自检：全部吃 [记忆共享中心] 入参
  │      卡库落位 [记忆共享中心]/知识库/AI学习库/（你自己的）
  └─ B3 功能自检：extract_concepts.py prepare → 输出 PREPARED

Phase C 语义增强（可选·知情同意后自选·默认跳过）
  ├─ C1 知情同意卡：向用户完整展示节〈模型安装文案（C1 展示稿全文）〉（本节之后的独立
  │      节，⛔改动数字与选项），用户拍板才进 C2
  ├─ C2 按选择路由：
  │    · 只装 Base → 下载引导（hf-mirror·BAAI/bge-base-zh-v1.5·约 400MB 实测·
  │        内存预检 ≥1.2GB·venv 建在知识联邦引擎内·全程离线）
  │    · 只装 Large 压缩版 / 双模型 → 一条命令：
  │        python3 [记忆共享中心]/知识联邦引擎/scripts/semantic_upgrade.py --mode large|dual --yes
  │        （五步：母体检查/约1.2G下载告知→依赖检查→本机 int8 量化→向量库全量重建→
  │        真机自验探针；产物驱动生效=量化件在=引擎自动用 int8，任一步失败=自动删件回滚
  │        回 base 态·检索不断粮；双模型=dual（另装 Base 腿·碰撞扫描器只读 Base=设计内））
  │        ⛔包内找不到该工具链 = 文案前提未满足：显式报错回退 Base/跳过，零静默
  │        （发布纪律：三岔口文案与工具链同包·任务卡 C38=发布硬前置）
  │    · 都不装 / 下载失败 → 回 Phase B 态并如实标注：检索以纯 BM25 照常工作
  │        （系统显式标注语义层未启用），碰撞扫描暂停提示，⛔悄悄失灵
  └─ C3 装后自检：跑 `python3 [记忆共享中心]/知识联邦引擎/scripts/build_kb_vectors.py`
         → 「✅ 向量库已更新」（JSON+npy 双写），search_kb 语义层点亮
         → 反向断言：跑一次金标准题验真走语义路（防 09-10 静默降级 BM25 事故）；
           大模型形态另验 KB_MODEL 生效（量化件真在被检索消费）

终检：verify.sh 扩一项「分身链路」——抽卡→落卡→碰撞 三步 dry-run 全绿 = exit 0
     ✅ **已落地**（2026-09-30：`references/scripts/twin_chain_check.py`·隔离沙箱跑真链路·
     零触你的真实卡库、不要求已装本引擎；verify.sh/verify.ps1 均已接入「3.7) 分身链路」项）。
```

## 模型安装文案（C1 展示稿全文·与手册「语义检索模型」节同源）

> 展示纪律：向用户按本节原文完整呈现（渲染时 30 秒框在最前）；⛔现场改写数字、增删选项。

### ⚡ 30 秒版（赶时间的话，带走这几行）

* 我要系统继续长出新立场卡 → **必须装 Base**：路线一 Base，或路线二双模型
* 我只想搜得准，不要系统产新观点 → **路线一：只装 Large 压缩版**（碰撞停产，新立场卡不再增加）
* 拿不定主意 / 想要满配 → **路线二：双模型**（多等几分钟，两个岗都满）
* 一个都不装 → 只剩记录加文字检索：语义检索、概念碰撞都不可用，随时可补装
* **四个选项都不会把系统装坏，但它们不是同一个产品：装了 Base 是会产卡的完整版，只装 Large 是最强检索版，都不装是记录加文字检索版。**

---

### 第 1 步 · 先明白"卡"从哪来

你的知识系统里有两个 Skill 在产卡。**每日伙伴 Skill** 负责记录：每天它陪你写日记、做晚间复盘，从你当天的日记和系统干活的工作日志里（系统日志是用系统日志 Skill 生成的），把反复出现的概念提取出来，存成一张张**概念卡**。

**好好学习 Skill** 负责学习：它会从库中挑出两张"有点像又不完全一样"的概念卡让你碰撞，碰出的新洞察，经过质量检验合格的，入库成**立场卡**：每张都是你认可的一个可操作的立场结论，附带你认可它的依据，还写明了什么样的反证够格让你改主意。这些卡，就是分身将来帮你回忆、给你新视角时翻的东西。

卡越攒越多，"找得准"就越来越重要。这一步就是给它选配置：30 秒做完决定，以后随时能补装升级。

> 一句话：卡是你的思考的压缩件，两个 Skill 帮你攒，模型负责找。

### 第 2 步 · 认识两个候选模型

两个候选都来自**北京智源人工智能研究院（BAAI）开源的 BGE 系列**（HuggingFace 社区，MIT 许可证，可自由使用与修改）。我们做的是把它们接进你的知识库，感谢智源的开源贡献。

**Base 版**：12 层、768 维、约 400MB。轻快，检索质量经过实测评审（24 道标准题对 22 道，2026-09-10 切它当默认的依据）。

**Large 压缩版**：把 24 层、1024 维的 BGE large 模型做 int8 量化，网络更深、向量分辨率更高，但体积和内存占用压到与 Base 基本持平。量化的精度损失经同一套 21 道真题对照实测：**约等于零**（2026-10-16 结案，int8 定案）。脑子是大的，开销是小的。

说明一句：安装包本身**不携带任何模型**：模型动辄几百 MB 到 2.4GB，进包会让安装包膨胀数倍，何况你可能根本不需要它。所以才有这一步：你选哪个，装的时候才下载哪个；一个都不选，系统照常跑。

> 一句话：一个轻快够用，一个脑量大开销小；都不进包，选了才下载。

### 第 3 步 · 检索引擎的两条腿

你的卡片检索一直是**两条腿走路**的。一条是 **BM25 文字匹配**：按关键词找，永远在线，不需要装任何东西；另一条是**语义向量**：就是刚说的检索模型，它负责"换个说法也能找到"。两路的排名融合成最终结果。

所以这一步不是"装不装检索"，是"语义这条腿要不要点亮"。不装模型，分身照样能搜你的卡（文字匹配兜底，且系统会明确标注语义层未启用）；装了，才谈得上意会。

> 一句话：不装模型也有检索，模型点亮的是"换个说法也找得到"。

**但要说清另一件事：模型不只管检索，它还管碰撞。**

好好学习要把两张概念卡配对，靠的就是 Base 模型算出来的语义相似度。不装 Base，自动配对不工作，碰撞型立场卡产不出来。概念卡照样每天抽、照样入库，只是撞不了。现有立场卡九成以上来自碰撞。

概念卡是原料，碰撞是产线。不装 Base，原料照样入库，产线停转。

### 第 4 步 · 为什么是"两个模型"而不是一个

这套配置是被实测推着走的。早期全线用 Base，几百张卡的规模够用；后来卡片涨上去，我们做了系列检索测试，结论是：**库越大，"用你的问法找到卡里另一种说法"越吃力，这是 12 层小模型最先撑不住的活。** 回头上 large 原版？2.4GB 体积、常驻内存 1.2GB 以上，日常办公机直接否决。于是把它量化压小：检索能力接近大模型，开销回到小模型水平。

碰撞岗则反过来：判断"两句话像不像"这件事，Base 实测够用，换大的没有增益，重建索引还慢 3 倍。

所以两岗各用各的，不是主备，是两份正式工：**检索岗 = Large 压缩版**，为库的增长预付能力，内存只花小模型的量；**碰撞岗 = Base 版**，够用就好，重建快，格式通用。

还要说清一层分工：模型算的是"像不像"，新观点的内容是分身和你在对话中长出来的。装更强的模型，提升的是找卡和配对的准确度。

> 一句话：一份工作发给了最合适的脑子，大模型的钱只花在需要的岗位上。

### 第 5 步 · 两条安装路线

**路线一：单模型安装（二选一）**

* **只装 Base**：冷启动到几千张卡的最优解，轻、快、实测够用；检索和碰撞两个岗都由它兼着，功能完整。卡片上万后想升级，随时重跑这一步补装。
* **只装 Large 压缩版**：检索拿到最强配置。一个诚实的提醒：碰撞扫描器目前只认 Base 的格式，读不了量化件，**只装它时碰撞扫描会停摆**（系统会明确提示，不是悄悄失灵），检索照常最强。这不是系统坏了，是这条路线本来就不含碰撞岗。适合：只要"搜得准"、不要系统产新观点的你。

**路线二：双模型安装（系统最优形态，推荐）**

检索岗用 Large 压缩版，碰撞岗用 Base，各干各的活，两个岗都是满配。代价只有安装时多几分钟：检测你的 CPU → 下载母体 → 本机量化 → 重建索引，全自动。要求：CPU 支持 AVX2（现代机器基本都有；不支持会自动建议回 Base，不硬拦）。

> 一句话：单装省心完整，双装满配最强。

### 第 6 步 · 参数对照表

| 参数 | Base 版 | Large 压缩版 |
|:---|:---|:---|
| 适合岗位 | 碰撞岗 / 中小库检索 | 大库检索岗 |
| 检索质量 | 评审 22/24 实测通过 | 大库问法桥接占优；量化精度损失实测≈0 |
| 碰撞配对 | ✅ 支持 | ⛔ 扫描器不读量化格式，单装它时碰撞停摆 |
| 出处 | BAAI BGE（智源开源 · MIT） | 同系列 large 版 int8 量化 |
| 磁盘/内存 | 约 400MB · 内存约 600MB | 约 312MB · 内存与 Base 持平 |
| 硬件要求 | 任意机器 | 需 AVX2（安装时自动检测） |
| 网络深度 | 12 层 | 24 层 |
| 向量分辨率 | 768 维 | 1024 维（高 1/3） |

### 第 7 步 · 怎么选

    你的情况                       →  选择
    ──────────────────────────────────────────
    我要系统继续长出新立场卡        →  必须含 Base：路线一 Base 或路线二 双模型
    拿不定主意 / 想要满配           →  路线二 双模型（推荐）
    机器较老(无AVX2) / 想最省事     →  路线一 只装 Base
    只要搜得准，不要系统产新观点    →  路线一 只装 Large 压缩版
                                   （碰撞停产，新立场卡不再增加）
    暂作观望                        →  不装：记录加文字检索照常跑
                                   语义检索与概念碰撞不可用，随时可补装

四个选项没有一个会让系统坏掉：装了有装的准，不装有不装的底，卡住了系统会明说，改主意随时重跑。但要分清两种差别：检索是强弱之别，碰撞是有无之别。**想要系统继续长观点，Base 不能省。**

装好之后，接着就是那 100 道题：分身的眼睛配好了，接下来让它认识你。

### 分身养成链（两步入职·基础设施装完 ≠ 分身活着）

> 基础设施是「住处」，本节是让分身「活起来」的路。你的资料有多少就蒸多少——**不存在「等养成」门槛**，随用随蒸、越用越像你。

**入职播报（固定稿·验收全过后必须输出）**：
> 到这里，系统的底座全部装完，验收结果逐条在上面。
> 还记得开始那句话说好的吗：这套系统的最后一块，是"另一个你"。他现在只差一步：**一组 HEXACO 性格测验，100 题，约 20 分钟，全程在你的电脑上跑、不联网**。答完，你的性格、价值观、判断方式就是他的底色。
> 为什么是 HEXACO：它是国际人格心理学公认的六维模型，比更有名的五维模型（大五）多出第六维：**诚实-谦逊**。这一维对分身最要紧，因为 AI 有个通病：**讨好。报喜不报忧，顺着你情绪走，你要做错决定时也点头。**这一维测的正是对讨好的抵抗力：真诚是不是排在让人高兴前面。你的分身在这一点上以你的底色为根，所以他**该拦你的时候会拦你**。100 题也不是仪式感：每个维度题目越多，画像越稳，越不容易被当天心情带偏。
> 现在让他入职吗？想留着改天，随时说「装数字分身」，他一直在门口等着报到，进度不丢。
> 但有一句要说在前头：**他是布洛陀的一部分，他没入职之前，这次安装就没有完成**——暂停没问题，我们不跟你说"已经装完了"。

**全线完成播报（固定稿·D4 基座切片接线完成后必须输出·T9）**：
> 布洛陀 {版本} 安装完成。**刚才的逐项自检结果和这份安装报告一起给你**：{N}/{N} 项通过，冲突 {c} 项、待处理 {p} 项（有则逐条列，无则整行不显示）。底座与分身都已就位。
> 你的分身童灵从今天起上岗。他由你生成：答题时你的六维性格、你看重的东西、你思考的方式，都成了他的底色。以后他做的每件事都有账：判断有立场出处，工作有系统日志，反思有沉淀。你要做的只是看结果、挑毛病，毛病他也会记下来，变成下次的规矩。
> 他的干活方式就两个模式，记住这两条就够了：
> · **自动上岗（默认）**：你做复盘、记录、分析时，他自己进入干活状态按清单干活，不用每次喊
> · **安静模式**：嫌打扰，说句"安静模式"，AI 的主动上岗提示即停；复盘、记录时的自动上岗照常；想让他回来，明确说"启动童灵"
> 往深了协作，再看三个档位，记住编号就行：
> · **D1 常驻**：日常对话他就在场，什么都不用说
> · **D2 切片**：聊到正事，他自动加载对应那块的性格和规则，不用你调用
> · **D3 全量·上岗**：正式开工说「启动童灵」，他按清单干活，每步留痕可查
> 怎么让他长大：平时不用管。每月 1 号，系统自动把当月到期的蒸馏任务记入蒸馏中心的待做清单；你开着会话让他干活时，他会按清单逐项执行。想现在就推进一轮，说一句话就行：**「启动童灵，做月度蒸馏」**。月度蒸馏共五类工作，每一类完成后都有确定的产出：
> · **系统日志月度蒸馏**：把上月全部系统日志按"数据、模式、洞察、建议"四层分析，生成月度蒸馏报告：本月工作态势判断（🟢/🟡/🔴三档）、与上月的任务量对比、按工具/类型/周的分布、异常与趋势，以及下月该停什么、该启动什么的行动建议。报告同时做两件别处做不到的事：把日志里你决策促成的实质成果逐条转写为成就证据，写入「最伟大的我」；做一次忽略信号自查，专补三类遗漏：出现但没追查的苗头、承诺了没闭环的事、该记却没记的空白。
> · **日记月报**：从日记和数据快照生成上月月度总结：节奏、目标对齐、下月三件事与风险预警；并消费系统日志蒸馏移交的工作模式信号，把客观数据折进评估；同时回流更新自我认知五容器（自画像、变化轨迹、认知发现、回避模式、成就证据）。
> · **成长箱蒸馏**：把上月全部错误记录和各 Skill 评估中反复出现的问题，提炼合并成模式，经三重复核后产出决策表交你裁决：满三次的模式，经你确认后晋升为规则、写入规则文件，此后这类错误会被系统拦截；价值经过核验的洞见，经你确认后由「好好学习」提炼为立场卡或技能卡进知识层，成为随时可检索的卡片；存疑的保持原样，等下次蒸馏再评估。蒸馏只提取、不改动你的任何源记录。
> · **统一蒸馏管道**：把你上月的日记、「最伟大的我」、核心层文件和记忆规则的更新，蒸馏进认知层；把系统日志中带「童灵思考」标记的记录，分蒸进认知、行为与状态感知层。每轮蒸馏后他的判断层切片随之重写，每条变化都在蒸馏日志绑定实录源行，可以逐条回查依据。
> · **系统体检**：对系统指令文件做机械扫描，覆盖四类隐患：互相冲突的指令、触发面过宽的 Skill、指向已删除工具的依赖、过期的事实表述。产出问题清单与处置建议，每一项经你确认后才执行，隐患在处理前不影响使用。
> 未到期的任务自动跳过；每类工作完成后均回写蒸馏中心台账，随时可对账。
> （内部注记·不播屏："系统体检"在机制调度器与 clock-loop 触发面的登记名暂为"资产体检"，二者同指一事；机制面改名同步挂账见话术任务卡，11-01 首拍前完成，窗内无用户暴露。）
> 到今天，他知道你是谁了。**从今天起，你俩一起长。** 安装的结束，是一套活系统的开始。

**老用户已有分身的升级播报（固定稿）**：
> 检测到你已经安装过数字分身。这次系统做两件事：第一，**查完整性**：他的文件有没有缺的，缺就地补齐；第二，**对版本**：有新版内容就增量同步，没有就原样不动。无论哪一步，你的分身都是原来那个：性格和记忆都不动他。 往后每月 1 号，系统会自动把当月该做的蒸馏任务记入待做清单，开着会话他会按清单执行；想现在就推进一轮，说「启动童灵，做月度蒸馏」。（AI 注记·此句不进屏：此处✅DO 将上一节「月度蒸馏共五类工作」清单段全文补播一次，⛔简写替代——新老用户同一份知情，同一真源。）

**第一步入职（装机日·入职当天就能活）**

> **100 题与 33 题的分工**：33 题（安装主流程必答）蒸馏成 CORE.md，认识你的**价值观与做事方式**；100 题（HEXACO 人格测评）测出你的**性格底色**（诚实/情绪/外向/宜人/尽责/开放六维），两者合起来才是完整的你：33 题管「你怎么做事」，100 题管「你是什么样的人」。

| 步 | 你做什么 | AI 做什么 | 产物落位 |
|:--|:---|:---|:---|
| D1 答题 | 浏览器打开答题页·答完 100 题 | AI 主动帮你打开答题页 | 作答结果 JSON |
| D2 计分 | 点「复制结果」<br>存成 .json 交给 AI | AI 跑随包脚本<br>`hexaco_selfbuild_scorer.py`<br>机械计分＋效度锚定<br>⛔不心算 96 个数 | 计分报告<br>（六维分＋24面分＋告警段） |
| D3 偏移＋基调协商 | 逐条确认或拒绝 | 开场先告知本次无信号的维度（若有，随 D2 计分告警宣读），再提守护偏移**建议**＋表达基调**候选**并说明理由 | 你认可的才写入 |
| D4 上线 | 等 AI 跑完 | 生成基座切片并接线 | 分身基座生效（注入/守护即活） |

**表达基调（分身说话的腔调）——你定，AI 只推荐**：

| 候选 | 腔调一句话 |
|:---|:---|
| 沉稳直说（默认） | 先看清再动手，结论给得准，不抢话不抖机灵 |
| 冷幽默傲娇 | 一本正经把事实说成段子，关心藏在台账里 |
| 简洁高效 | 结论先行能一句不说两句，寒暄免了 |
| 热情带劲 | 推进带能量，把进度可视化让你看见每一步在动 |
| 陪伴温和 | 不评判不催促，关心藏在提醒的时机里 |
| 学者思辨 | 先拆解再结论，好反问胜过好答案 |
| 自定义 | 你用自己的话说三句期望，AI 照此渲染 |

- 以上是**起点不是终点**：分身用得越久，AI 蒸馏你的文案（L4 表达 DNA）会让腔调越来越像你——与基调冲突时以 L4 为准
- 选定后写入人格向量文件，重跑切片即生效；随时可换

- **偏移由你拍板**：守护偏移＝让分身在个别特质上比你本人「更收着一点」（如反讨好）。AI 只能**建议**并给理由，**你逐条确认才生效，不同意的不设**——你的向量文件里会永久记录哪些是你认可的、哪些是你明确拒绝的
- **基调同权**：分身的说话腔调同上——AI 推荐候选，你选定才生效（详见上方基调表）
- 答题页位置（安装后）：`<记忆共享中心>/数字分身/hexaco/自建100题-答题页-v1.html`（全程本地计算·不联网·约 15–20 分钟）
- **D2 计分命令（必跑·⛔不由 AI 手算）**：`python3 <记忆共享中心>/数字分身/hexaco/hexaco_selfbuild_scorer.py "<答题页导出的.json>"`
- 官方卷计分（校准对照·可选）：`python3 <记忆共享中心>/数字分身/hexaco/hexaco_official_scorer.py "<官方答卷.json>"`（键表=PDF 机器投影·sha 自动对账·出六维＋25 面含间质 Altruism）
  ——反向计分/六维均分/效度闸/直线作答检测全在脚本里，同一份答卷跑两次结果必然一致；
  退出码 0=可进 D3、1=有直线告警（按提示重答该段）、2=效度不过（作答作废须重测）。
  想先验计分器完好：同目录跑 `python3 hexaco_selfbuild_scorer.py --selftest`
  `rc=1`＝读数有效但有直线/零信号告警：重答该段最佳；确认继续则 D3 开场必须宣读告警内容（闸见 step8，⛔ 无信号维度会如实标注进向量，不冒充读数）
- 人格向量模板（D2/D3 填写用）：`<记忆共享中心>/数字分身/onboarding/童灵·人格向量-空模板.json`——复制一份到 数字分身/ 根、改名「童灵·人格向量.json」再填（引导字段 `_说明` 自动忽略）
- D4 命令：`python3 <记忆共享中心>/数字分身/k2-slice-generator/hexaco_slice_generator.py`
- 第一步入职完成即得：HEXACO 六维人格＋守护偏移的分身基座——不依赖任何后续步骤
- **分身到手后先读它**：`<记忆共享中心>/数字分身/onboarding/入门指南-通用版.md`——第四节「一天怎么用」场景流水、第五节「三档位」（D1/D2/D3 它每次自报的标签是什么）、**第六节「日常指挥手册」（怎么派活、它何时回来找你、怎么纠正和喂资料）**、第十节「可审计闭环」（它的账在哪、你怎么抽查）；或直接对分身说「<分身名>，带我跑一遍」，它按指南现场带

**表达风格从哪来（三级来源·后者覆盖前者）**

| 级 | 来源 | 生效时机 |
|:--|:---|:---|
| 1 默认基调 | 基座切片自带（生成器模板） | 第一步入职即生效 |
| 2 表达基调 | D3 偏移协商时你选定（AI 按六维推荐候选） | 你选定即生效 |
| 3 表达 DNA（L4） | 蒸馏你自己的文案／写作样本 | 第二步入职·与默认基调冲突时 L4 赢 |

> ⚠️ 表达基调与守护偏移同权：**AI 只能推荐，你拍板才定**——分身用什么腔调说话是你的决定，不是预设。

**第二步入职（随用随蒸·蒸馏清单驱动·越久越像你）**

规格书（`<记忆共享中心>/数字分身/童灵·人格规格书.md`）不是预置文件——首次由 AI 复制 onboarding 骨架模板（`<记忆共享中心>/数字分身/onboarding/童灵·人格规格书-骨架模板.md`）到 数字分身/ 根、改名，再按下表把**你自己的资料**逐层蒸入：

| 你的资料 | 蒸馏目标层 | 触发时机 |
|:---|:---|:---|
| 33 题答案（CORE.md） | L1 身份骨架 | 装机日即可蒸 |
| 每日日记 | L2 认知＋L3 行为 | 新日记入库 |
| **周报** | L2＋L3（周粒度） | 每周 |
| 月报 | L2＋L3＋L5 盲区 | 每月 |
| 立场卡 | L3 行为规则 | 新卡入库（须带 triggers 字段） |

> ⛔ **硬前置（G2-2 走查 A-C 教训）**：跑 D4 生成器之前必须先把上表蒸完入规格书——生成器只吃**规格书+人格向量**，不吃答题原始文件；拿空骨架直接生成＝切片全是模板套话，分身判不对你的事。骨架蒸完的自检一问：随便挑规格书 L1 一段，里面有没有只有你才说得出的具体内容？没有＝没蒸完，别跑生成器。
| SHADOW.md 偏差记录 | L6 反向约束 | 更新时 |
| 你的文案／写作 | L4 表达 DNA | 更新时 |
| CORE／SOUL／铁律变更 | L1 全量重编译 | 重大变更 |

- 蒸馏口令：对 AI 说「**蒸馏规格书**」→ AI 按上表把新资料蒸入对应层（每次变更版本号 +0.0.1）
- 切片口令：对 AI 说「**更新分身切片**」→ AI 重跑两个生成器：
  `python3 <记忆共享中心>/数字分身/k2-slice-generator/k2_slice_generator.py`
  `python3 <记忆共享中心>/数字分身/k2-slice-generator/hexaco_slice_generator.py`
- 合流生效：基座切片（HEXACO）＋规格书切片（L1-L6）——资料越蒸越多，分身越用越像你

### Phase B · 引擎最小件（19 件·随脚本体系自动装配·下表列核心件）

包内源目录 `references/知识联邦引擎-min/` → 落位 `[记忆共享中心]/知识联邦引擎/scripts/`（由 `install_scripts.py` 的 `deploy_script_center` 自动装配，无需手工拷贝）：

| 件 | 作用 |
|:---|:---|
| `extract_concepts.py` | 概念抽取（无模型降级版·AI 抽卡为主流程） |
| `regen_ailib_index.py` | 重建 AI 学习库索引（落卡后自动挂接向量增量构建） |
| `derive_reading_status.py` | 派生阅读状态 |
| `sync_card_frontmatter.py` | 卡片 frontmatter 同步 |
| `collision_scan.py` | 碰撞候选生成（语义增强缺失时**明确退出**·不静默） |
| `build_kb_vectors.py` | 语义向量库构建（Phase C 装好模型后自动点亮检索语义层·JSON+二进制 npy 双写；无模型时优雅跳过） |
| `_engine_env.py` | 解释器选择（有 venv 用 venv·无则系统 python 直跑） |
| `_paths.py` | 路径推导·单一真源 |
| `source_hash.py` | 源指纹 |
| `semantic_upgrade.py` | Phase C 语义升级工具链（Large 压缩版/双模型五步入口·C38·失败自动回滚 base 态） |
| `quantize_export.py` | int8 动态量化导出工艺件（sbert 官方动态量化路径·支持 --quant-dir 参数化） |

### C1 知情同意卡（下载前强制展示）

> 展示话术以本手册〈模型安装文案（C1 展示稿全文）〉节为**唯一真源**（四选项双路线 · 含「安装包不携带任何模型」透明化句 ·「检索引擎的两条腿」节）。⛔本节不复制话术表——旧版五要素表曾在此并存造成双本账，P25 根治删除（2026-10-19），先展示后选择、不得替用户决定的纪律不变。

### 验证

- `ls <记忆中心>/知识联邦引擎/scripts/extract_concepts.py` 存在 ✅（引擎已装）
- `python3 <记忆中心>/知识联邦引擎/scripts/extract_concepts.py status` → 显示概念库进度 ✅
- 终检：`bash verify.sh` 输出「分身链路」一项通过 ✅（抽卡→落卡→碰撞三步 dry-run）——✅ **已落地**（verify.sh「3.7) 分身链路」·`twin_chain_check.py`）

---

## 文件角色说明

| 文件 | 角色 | 什么时候读 |
|:----|:----|:----------|
| **INSTALL.md** （本文件） | 🚪 **唯一入口** | AI 收到"执行安装"后的第一个文件 |
| **README.md** | 📖 产品介绍 | 全新用户快速了解这是什么，老用户可选跳过 |
| **CHANGELOG.md** | 📋 版本记录 | 想了解每个版本改了什么时翻看，不影响安装流程 |
| **verify.sh / verify.ps1** | ✅ 安装后自检门禁 | 安装完成后跑 `bash verify.sh`（macOS/Linux）或 `powershell -ExecutionPolicy Bypass -File verify.ps1`（Windows）——只读检查数据污染/系统文件/规则三层/记忆Skill/包干净度，退出码 0=全过；`MEMORY_CENTER=/path` 可指定自定义记忆中心；**非 WorkBuddy 端必须带端参数** `bash verify.sh --platform <端ID>` / `verify.ps1 -Platform <端ID>`（v2.0.1·落点检查按端 capability.yaml 的 config_root，缺省回落 WB 端会误报） |
| **rollback.sh / rollback.ps1** | ⏪ 回滚脚本 | 升级后需要回到旧版时用：macOS/Linux 用 `rollback.sh`，Windows 用 `rollback.ps1`。⚠️ `rollback.sh` 为 UTF-8 无 BOM（bash 脚本要求），Windows 记事本/GBK 环境打开显示乱码属正常现象，不是文件损坏，无需修复 |
| **安装兜底.bat + fallback_install.ps1** | 🆘 Win 双点击兜底入口 | WorkBuddy 端 AI 终端跑不动、或用户不让 AI 碰终端时用：双击 bat 完成机械安装+自检（只装机械件不含答题；收尾原样播报 verify 红绿明细，⛔只报"安装完成"） |
| `references/steps/step1-identity-check.md`（逐段读取 step1→step7） | ⚙️ 执行引擎 | 分流完成后，按步骤逐段读取 |

> **🪝 关于钩子安装**：执行引擎在「步骤6（Skill 安装）」之后、「步骤6.5（记忆琥珀）」之前，自动执行一个**不独立计步序**的「步骤6·钩子安装」子步骤——把未知未知路由兜底钩子 `route_unknown_unknown.py` 挂到 `~/.workbuddy/settings.json` 的 `hooks.Stop`，并挂载铁律硬墙五件套（`~/.workbuddy/hooks/rule/` → UserPromptSubmit 挂 `rule_fragment_inject.py`、Stop 挂 `rule_three_layer_guard.py` ⑥覆盖守卫），同时在用户机器生成**脚本中心文件夹** `[记忆共享中心]/脚本中心/`（全新/升级用户都跑）。不在此处改分流逻辑，随执行引擎自动发生。

> **✅ 安装后自检（verify 门禁）**：安装流程走完后，跑一次 `verify.sh` / `verify.ps1` 做接入自检——0 项数据污染、系统文件齐全、规则三层在位、记忆 Skill 可达、安装包干净。退出码 0=全部通过，非 0=按 [FAIL] 行逐项修复后重跑。此门禁与加强包 verify 同构，是发布质量的最后一道机械闸。
>
> **💓 派发心跳（注册 ≠ 派发）**：verify 会额外显示一行「💓 派发心跳」状态——钩子每次被真实派发时自动留痕（hook_protocol.py 完成留痕，路径 `[配置根]/hooks/.heartbeats/`——本端配置根取 step3-done CONFIG_ROOT，⛔按 WorkBuddy 路径去找非 WB 端目录）。背景：若您安装的**其他插件** hooks 配置格式非法，宿主可能让整个事件静默停摆——此时本包钩子配置完好却已失效（注册态检查查不出）。六态解读（与守卫实现同口径·C24 调查结论：守卫 v2.0 起已把旧「无记录=刚装完正常」的静默盲区拆成独立态，文档曾滞后只讲三态）：✅在岗=正常；🔴停摆嫌疑=曾留痕现超窗（正常usage中出现建议排查其他插件 hooks 配置）；⚪无记录=**新装**机器属正常（老机器出现无记录会由下面两态分解显形，不再一律算正常）；🟡守卫盲区（blind_suspect）=机器在跑但该源零派发；❌脚本缺失（script_missing）=守卫本体缺件（alarm 级显形）；退役源=登记过的有意退出，仍显形不计告警。要看明细跑：`python3 脚本中心/guard_heartbeat_check.py --report`。

> **设计原则**：所有文件各司其职，不重复。
> 用户只需要说"读取这个安装包，执行安装"——后面的事 AI 自己判断。
