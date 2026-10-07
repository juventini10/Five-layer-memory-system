# 变更记录

> 布洛陀·全平台安装包（v2.x）· 格式遵循 keepachangelog.com
> 版本号规则：X.0 架构级 · X.Y 功能级 · X.Y.Z 修复级
> 版本串口径：**纯数字，不带发布状态后缀**（`-dev`/`-rc` 等一律禁止——发布状态只住本文件顶部段头，
> 见下方「版本传承」节的口径说明与《版本命名规范》§1 / §4.1）

## 版本传承（1.x → 本包·阅读指引）

> **本文件是「布洛陀发布包」这一条产品版本轴的续记，不是另起的新账。**
> 完整 1.x 记录（`[1.0]` 2026-06-27 → `[1.7.2]` 2026-09-21）在**上一代发布包**的
> `布洛陀-安装包/CHANGELOG.md` 里——从 1.x 升级上来的用户，手上那份旧安装包内就有这份记录。
> 本文件⛔不复制 1.x 全文：两处副本必然漂移（《安装包设计通用规范》条文 28「无主副本律」），
> 旧包 1.7.x 已于 2026-09-23 定档**维护模式**（安全修复照常，新特性并入本包），其记录就此冻结。
>
> 新装用户不需要翻旧包也能看懂来路：下表 = 每个 1.Y 节点「对用户多做了什么」的一句话。

| 版本节点 | 日期 | 对用户意味着什么 |
|:---|:---|:---|
| 1.0 | 2026-06-27 | 安装入口统一（一句"读取这个安装包，执行安装"自动分流新老用户）＋成就系统＋33 题个性化文件合成 |
| 1.1 | 2026-07-13 | 记忆琥珀物理级文件哨兵（macOS/Windows 双平台，破坏性改动可回滚） |
| 1.2 | 2026-07-20/21 | Windows 端真正可用（PowerShell 5.1/7、NSSM 服务、UTF-8 BOM 编码根治） |
| 1.3 | 2026-07-22 | 数据污染检测（装完自动清掉开发样例数据，你自己录的数据一条不丢） |
| 1.4 | 2026-07-25 | Skill 版本检测（说"检查Skill"即知哪些技能有新版本）＋5 维度发布质量门禁 |
| 1.5 | 2026-07-26/30 | 记忆琥珀永久收藏＋每日体检＋周日弹窗提醒；跨平台心跳误报修正 |
| 1.6 | 2026-09-17 | 脚本体系入包：路由引擎＋铁律硬墙＋各类守卫（说一句话自动命中该用哪个技能） |
| 1.7 | 2026-09-20/21 | 三段安装合一为 `install_scripts.py`（装完不再有空转钩子）＋端到端实装验证门禁＋数字分身可选组件首发 |
| **本包** | 2026-09-23 起 | **10 端合并一包（能力矩阵驱动分流）＋数字分身完整可用（答题造芯→落卡→检索链路）** |

> **版本号口径（《版本命名规范》§1 / §4.1）**：X.0＝核心架构不兼容变更 · X.Y＝新增独立功能模块 ·
> X.Y.Z＝修复与同步。**版本串本身只表示"功能到了哪一档"，不表示"发没发"**——
> 所以顶部段头在未发版时写作 `[未发布]`，发版那一刻 relabel 成具体号（升级检测从这里取号）。
> 曾出现的 `version.md = 2.0.0-dev` 属自造状态后缀：一个号同时存在两种宣称串，
> 实测一处后缀制造 5 处门禁红＋归档名污染（`V2.0.0-dev.zip`），已于 2026-10-01 废除并上门禁。

## [2.1.0] — 2026-10-07

### F2 · Qoder CN 端 rules 装机形态升级：软链承载→模板实体落盘（你定端哲学·"本端是被镜像的那一个"的根治）
- `adapters/qodercn/setup.sh` [2/5]：核心四件（core-identity/core-soul/core-user/execution-guidelines）由 `safe_link` 软链包内件改为**模板渲染实体**（占位符 [记忆共享中心] 替换 + tmp+mv 原子写 + 已存在实体不覆盖 + 旧装机软链自动升级 + 用户自建链不动）；记忆数据三件（快照/问卷/题目库）维持软链=数据共享单一真源（v0.9 既定，两种形态分治）
- [5/5] 自验证判据跟变：rules 核心件由 `-e`（软链可达即绿）改为**实体判定**（`[ -f && ! -L ]`），装残软链不再报绿
- `conffiles`：qodercn rules 四件进三路比较册（先例=~/.workbuddy/SOUL.md 形态·升级时用户改过的人格件不覆盖）
- 包模板 `rules/core-soul.md` 两处 WorkBuddy 串味修正（身份行去平台名·署名行焊「你的 Qoder CN 🔮」——原装机即让本端 AI 自称 WorkBuddy，身份串缺陷）
- `capability.yaml` 同步：setup.sh 职责措辞 + SOUL 字节注释更新 + IDENTITY 旧注释 6467→5648 漂移订正
- 作者机真源关系：本端 `~/.qoder-cn/rules/core-soul.md`/`core-user.md` 已实体化（v1.0-qodercn·07:15），包模板为其脱敏投影起点；本端后续演化→人工脱敏回流模板（单向律）
- 验证：`bash -n` 零错；沙盒 QODERCN_HOME=/tmp 实装（全新装实体落位/旧软链升级/实体不覆盖三分支）+ dry-run；content-gate 正文扫描
- 待填显形闸（08:30 D3 轮补装·锚 S561 快照对账/S802 独立门禁）：render_entity 落位后统计 {称呼} 类答题占位残留并显形报数 `[待填] N 个`——装机不再静默交付原始占位符；答配合成腿属装机主流程专项（本端不越权自造），显形即本端诚实终态
- 验证增补：沙盒全新装实跑 `[待填]` 命中 3 件（core-user/core-soul 等）·四件仍实体·rc=0

### F4 · Trae Work 端童灵专属 Skill 装机链三处真缺陷根治（阻断级崩溃 + 名映射缺失 + 静默失效 sed）
> 缘起：复核「童灵专属 Skill 是否落端系统文件目录 + 安装包是否同步给用户装」。核查中发现安装链**跑不到落盘那一步**——脚本在 [3/6] 即崩，用户机根本装不上童灵 Skill。

- **缺陷①（阻断级·`set -u` 下变量名吞字节）**：`adapters/traework/setup.sh` [3/6] 提示行 `$SKILLS_DST（…` —— `$VAR` 后**紧跟全角字符**时 bash 将该字符首字节并入变量名 ⇒ `SKILLS_DST<乱码>: unbound variable` ⇒ `set -u` 直接终止脚本。**实证**：`bash -c 'set -u; A=/tmp; echo "$A（x"'` → 退出码 127；改 `${A}（` → 退出码 0。影响面：该脚本 [3/6] 的落盘循环**永不执行** ⇒ 端用户装不上童灵专属 Skill（与「同步给用户安装」诉求正相反）。
- **缺陷②（同类·同包共 4 处）**：全包扫描 `$VAR` 后接非 ASCII 命中 4 处（`traework/setup.sh` ×2 · `zcode/verify.sh` ×2——后者同 `set -uo pipefail`，仅失败分支触发故此前未显形）。全部改 `${VAR}` 形态；复扫 **0 残留**。
- **缺陷③（静默失效·畸形 sed）**：`traework/setup.sh` · `doubaowork/setup.sh` 的 TSL 脚本版本比对 sed 第二段误写 `s['"].*//`（`[` 被当分隔符 ⇒ unterminated substitute pattern）⇒ `src_ver`/`dst_ver` 恒空 ⇒ **「源新于目标才更新」分支永不触发**（TSL 脚本永不更新，版本号显示为空）。改 `s/['"].*//`；实装验证：首次 `v0.1.0` · 二次人为改旧目标版本号 → `0.0.1→v0.1.0` 正确更新。
- **名映射契约补齐**：`setup.sh` [3/6] 原按 basename 直落（`doenglingz-guard`），与 `capability.yaml` 声明的 carrier 路径 `~/.trae-cn/skills/布洛陀-童灵守护` 及 README §目录结构注释**不符**（声明与实盘脱钩·铁律-002）。补 承载名→落盘名 映射（`doenglingz-guard`→`布洛陀-童灵守护` · `doenglingz-slice-nav`→`布洛陀-童灵切片导航`），README §名映射表补 2 行使其成为唯一映射真源。
- **实证（隔离 HOME 真实安装演练·launchctl 打桩不碰真机）**：`HOME=/tmp/fakehome PATH=/tmp/fakebin:$PATH bash setup.sh /tmp/mc_probe` → **rc=0** · rules 实体 6 件 · 童灵 Skill 2 件**中文名实体落盘** · TSL 脚本 v0.1.0 · patrol 脚本 · plist 落位。
- **安装器映射复核（dry-run）**：`install_scripts.py --platform traework --dry-run` → ①a 数字分身套件 **44 件** → `<MC>/数字分身/{scripts,devtools,guards,gates,k2-slice-generator,hexaco,onboarding}/`；① 脚本中心 802 件；①b 规则层；端特有链委派 `setup.sh`。
- **隔离性复核**：`~/.trae-cn/skills/` 童灵 2 件为**实体**（非软链）· `<MC>/技能配置/` 零残留 · 全机 8 端 `skills/` 扫描（Qoder CN / QoderWork / `~/.trae` / WorkBuddy 等）**无童灵外泄**。
- 全适配器 `bash -n` 零错（8 件）。

### F5 · 立场卡检索引擎·五副本 split-brain 合并根治入包（端用户态·判据指纹 5/5）
> 缘起：端用户态"同义问法也能命中立场卡"的语义层曾**结构性不可达**——`search_kb` 五份活跃副本昨日起分叉（v0.3.11 标签诚实化只落引擎副本 ⇒ D1 契约手跑路 MODEL_EFFECTIVE 恒不符、降级 BM25；v0.3.12 npy 改写误伤 PAT-080 防护 ⇒ 两副本各持一半修复）。

- **双向合并（⛔非单向覆盖）**：主源（`脚本中心/search_kb.py`）补入 v0.3.11 标签诚实化 + v0.3.12 npy 快路径 + int8 CPU EP；引擎副本补回 PAT-080 JSON 回退防护。
- **新修第四墙（判据随对象演化）**：`_env_missing_deps` 判据由 numpy/st 两项**扩面**至含 `optimum`/`onnxruntime`——量化上线后语义层依赖已变，旧判据判"无需换身" ⇒ 系统 python 直载 qint8 报 "Optimum required" ⇒ 静默降级 BM25。
- **入包面**：`references/scripts/` · `references/hooks/` · `references/digital-twin/devtools/` 三份与主源**同批写入**（2026-10-07 09:27:44）。
- **机械验证**：`kb_copy_fingerprint_guard.py` 实跑 **5/5 全绿**（F1 标签诚实化 / F2 判据扩面 / F3 npy 快路径 / F4 PAT-080 防护 / F5 CPU EP + H1 包内零作者机绝对路径）；三例成法自检（正/负/缺件）3/3。
- **如实边界**：端用户态语义层仍为**选装**——bge 模型与向量库不随包（Phase C），无模型态如实降级纯 BM25，⛔不谎称"装完即有语义增强"。

### F6 · Qoder CN 端三层硬路牌与卡号纪律入包（作者端 v1.1/v1.2/v1.5 脱敏单向回流·WB三文件法对齐）
> 缘起：皮叔令「现在就做安装包的工作，你先做你的」（2026-10-07）。作者端运行面当日已落硬路牌（SOUL层 v1.2 + 常驻指令层 v1.5 + MEMORY 层），按真身→模板单向律脱敏回流本端包模板。

- `adapters/qodercn/rules/core-soul.md`：原通用骨架**整段缺「把沉淀当资产」**（实查 grep 0 命中）⇒ 补入硬路牌+🔴卡号须来自实跑整块——文本自 `adapters/traework`（v3.15 同条款态）**程序化逐字切片**，⛔手抄，跨端同条款零漂移；行为印证表同改；尾部版本注记同步
- `adapters/qodercn/rules/core-identity.md`：「知识调用开关」行升档=自己实跑/⛔不等注入块/回复带锚点/卡号须来自实跑（路径本已合规 脚本中心/search_kb.py 扁平·无需改）
- `adapters/qodercn/templates/MEMORY.md` v1.2→v1.3：硬路牌节新增「检索与卡号纪律」压缩版（{记忆共享中心} 占位口径随文件既有风格）
- `capability.yaml`：SOUL/IDENTITY 字节注释按改后实测刷新（防注释与实盘脱钩）
- **合法性判据**：`mirror-manifest.json` `package_only_files_v2` 实查登记本端 rules/core-soul.md、rules/core-identity.md、templates/MEMORY.md 三件 ⇒ 包=其自身真源，直接改包合法、无源投影不会被镜像冲回
- **脱敏核验**：作者侧裸路径（/Users/…·~/个人AI档案）扫描 0 命中·FFFD=0·渲染仿真（setup.sh 同式 sed [记忆共享中心]/{}记忆共享中心 → /tmp）占位符替换正常，残留占位仅既有 {Q30} 类答题位（[待填]显形闸既定态）
- 边界：Hermes 端挂起（皮叔令先不管）·ZCode 端自认领中；本 F6 只动 qodercn 适配器与记账面，⛔未碰其他端

### F7 · ZCode 端检索引用防谎报条入包（作者端 v1.8 脱敏单向回流·单通道一件承载·收 F6 留下的"ZCode 端自认领中"尾巴）
> 缘起：任务卡「立场卡检索硬路牌全端补齐」步3 ZCode 端运行面当日收口（AGENTS.md v1.8 端修+auto-memory 防谎报卡+本端实跑 search_kb 出结果 18:09），按真身→模板单向律脱敏回流本端包模板。

- `adapters/zcode/templates/AGENTS.md`：「## 红线」段补入检索引用防谎报条（01规范原则17 同条款·脱敏适配版）——判断/评估/写作/方案裁决前自己实跑 `{记忆共享中心}/脚本中心/search_kb.py`（⛔不等注入块·注入送达时通时不通）/回复须带出至少一条锚点路径/没跑明说「本轮未检索」/卡号三样齐（时间戳+query+命中行）/注入锚点只给格式⛔不等于内容
- 落位判据：红线段=本端单通道架构的正确承载（AGENTS.md 一件=五系统文件合一·capability.yaml system_file_paths 声明），性质同级（诚实操作硬约束）；措辞自端上 v1.8 条适配⛔逐字照抄——路径换端用户落点（`{记忆共享中心}/脚本中心/` 扁平口径·install_scripts.py:446 deploy_script_center 七端一致）·去版本号字样防漂移，其余纪律句逐字保留
- 脚本面零重复劳动：`references/{scripts,hooks,digital-twin/devtools}` 三份 search_kb.py 已随 F5 同批 v0.3.14（本日实查三副本版本号一致），本条只动模板不碰脚本
- 合法性判据：mirror-manifest `package_only_dirs_v2` 实查 `adapters/` 整目录=包独有包直持（2026-09-30 立册·目录前缀登记·新件免逐册）⇒ 直接改包合法、无源投影不冲回
- 脱敏核验：作者侧裸路径（/Users/…·~/个人AI档案·机器名）扫描 0 命中·FFFD=0·渲染仿真（{记忆共享中心}→/tmp/mc_probe）替换正常，残留占位仅既有 {称呼} 答题位×2（F2 [待填]显形闸既定态）
- 验证：`install_scripts.py --verify --platform zcode` → 30/30 钩子落盘并注册全绿·规则层就位（模板改动不触碰钩子面与指纹册——integrity-fingerprints 实查 0 命中 AGENTS）

### F8 · 语义增强模型压缩全链配套（能兑现才对外提压缩·装/压两问独立·手册给粘贴即用提示词）
> 缘起：你 2026-10-07 链问——INSTALL 数字分身下载告知段增压缩提示 → 你定纪律「功能配套齐全才能告诉用户，不然说了干嘛」→ 拍三层分立：告知在手册、开关在知情卡、执行在包内脚本；⛔强装（不存在后台自动下载，两问都要用户点头）。

- **新件 `references/知识联邦引擎-min/scripts/quantize_export.py` v0.1-enduser（引擎最小件第 10 件）**：官方 int8 动态量化（st ONNX 导出 + onnxruntime quantize_dynamic QInt8·免校准集），1.3GB→约 311MB·运行时内存约 2GB→约 600MB；作者侧实弹教训前置进码（optimum 新版"报成功不落盘"→显式落盘分支防假 FAIL·SameFileError 防呆·冒烟强制 CPU EP·内存预检 2.2GB·幂等可重跑·⛔不自动联网下载——缺缓存报错并给镜像下载指引）。件在包但不在默认安装链：C3 第二问同意后由 AI 代跑
- **包内 `build_kb_vectors.py` v0.1→v0.2-enduser（同步作者侧 v1.1/v1.2/v1.3）**：①标签诚实化——量化库如实记 large@qint8（旧版打 base@qint8 与包内 search_kb 的 large@qint8 标签不符 ⇒ 端用户量化产物一就位即**静默降 BM25**，"复刻即断"真 bug，此件不修则对外提压缩=虚标）；②量化加载强制 CPUExecutionProvider（CoreML node132 崩墙）；③npy 二进制向量库双写+补写（与包内 search_kb v0.3.12 `_load_vectors_npy` 消费端配套）；④PAT-080 增量"已建"判定补验产物非空（防 null 向量静默烂数据）；就绪判据目录存在→文件完整存在（与 search_kb._QUANT_READY 同判）
- **INSTALL.md Phase C**：下载引导改 large 路线（⛔不承诺判据不支持的 base 压缩）+ 新增 C3 压缩第二问 + 装后自检顺延 C4（npy 双写·量化产物在位自动切·标签如实 qint8）；C1 知情同意卡五要素更新（本机缓存解释/1.3GB→311MB/效果"基本不变"口径⛔不写"无损"/默认不装不压/指路手册§12）；引擎最小件表 9→10 件；`install_scripts.py` min 版边界注释同步
- **说明手册 §12 数字分身新增「语义增强与模型压缩」小节**：三概念大白话表（模型缓存/向量库/压缩——划清"压的是模型文件，你的卡片一个字不少"）+ 实测数字 + **粘贴即用提示词卡**（带具体命令的分步执行+失败即停报原文纪律+防坑两提示内置：CPU EP 强制、导出产物验盘）；手册/包内文案零内部档案路径（设计律①零私人外露·你 2026-10-07 定：不暴露来源防"又来要文件"），对外口径=官方开源路线+发布者实测
- 验证：`py_compile` 两码件 rc=0；包内暂存态直跑 quantize_export → 显形"未安装态"rc=1（不崩不误写）；build --status 暂存态正常输出。**端用户态真模型端到端本轮⛔未实测**（作者侧生产态同路线已实跑含裁决留用；包内路径适配待沙箱 E2E+Windows 真机项，发版门禁见这条·发版前不算兑现完）

### F9 · 语义增强对外口径改「装=整链」+破碎态如实标注（你「两个模型」困惑根治·triwich L2 出品）
> 缘起：你以产品经理视角质询「用户会以为下了两个模型，怎么分别介绍」。L2 分析定位到这不是措辞问题，是两处叙事×物理态不一致，纯换词方案被反例否决。

- **病灶1（盘态矛盾）**：瘦身后 fp32 缓存（约 1.2GB）残留盘上，与"省盘"承诺冲突（quantize_export 清理清单只覆盖量化目录内部，⛔不动 HF 缓存——逐行实查）→ 新增**清理授权步**：瘦身后问一句"删原始大包？（移废纸篓·不自动删·不清空）"，INSTALL C1 卡/C3 与手册§12 话术+提示词卡第 7 步同步落地
- **病灶2（破碎态开放选择）**：端用户「只装 large-fp32 不瘦身」时，包内 search_kb 的模型缓存判据（L101-105 按 MODEL_NAME 默认 base 派生 tag）落空 → 语义层不点亮，而原文档写「不压也完全能用」=虚标承诺 → **撤掉「只装不瘦身」选项**：C1 卡改「装=整链（下载→瘦身→点亮）·卡内一次披露」，如实标注「工程修复后下版开放」；修复本身=默认模型值/判据的源-包两态裁决，挂专项待你定夺，本轮⛔不动代码
- **单一实体叙事置顶手册§12**：「1.3GB 与 311MB 是同一模型两态（胖/瘦），⛔不是两个模型、不会有第二次下载」+ 旧版 base 用户注一行（量化产物在位系统自动优先——与 search_kb._QUANT_READY 同判据，此句为真）
- 改动面：INSTALL.md 6 处（流程图 C1/C3、C1 卡标题+引言+这是什么+占用+你来决定）、手册§12 4 处（标题/引言/界线段/提示词卡）；quantize_export.py 本轮未动（清理步先由提示词卡承接，脚本内置清理选项待专项裁决）
- 验证：每处替换 assert count==1 全过；破碎态（装不瘦→BM25）真机复现 ⛔未做，随发版链 E2E 清单（如实标注，不假绿）

### G10 · 新旧模型「档位替换」关系成文（你三连问：几百兆能用为什么还下1.3G/两者联动还是互补/吸引力建立在事实）
> 缘起：你指出上轮修订仍未答用户的临门一脚问题——旧版 base（几百兆）和新版 large（1.3G→311MB）什么关系。triwich L2（键20261007_200657）定位=升级替代型产品的迁移叙事缺口：只写了新档，没写新旧关系，用户按"互补叠加"心智算成本得出"不值得装"。

- **关系定性（代码三源，非话术）**：系统任一时刻单模型——向量库 model 标签唯一、MODEL_EFFECTIVE 单值、⛔fp32/int8 向量混搭禁令（查询与语料同模型铁律）⇒「联动/互补」不成立，正确叙事=**档位替换+自动接管**（标签变更→整库自动重建，旧档退役可删）
- **吸引力口径（你红线：建在事实、⛔夸大）**：①更省=瘦身版 311MB 实测 < 旧档 391MB 实测（du）；②坐标更细=1024 维 vs 768 维（结构事实）；③发布者生产同款=维护一致性。质量句固定为「本地 24 样本评测差 1 个样本、官方口径互有胜负⇒持平不降级」——⛔写"更强"（检索设计哲学 v1.16 曾引官方 base 系≥large 口径，宣称更强即夸大）
- 落点：INSTALL C1 卡「这是什么」补替换段（新用户+旧 base 用户一句看全）、手册§12 旧版注扩为完整关系段（含「首次重建稍慢」盲区补提示）
- 认错入账：上轮把你「两个模型的区别」指称窄解为胖瘦两态、漏答档位关系——理解错位（执行准则第1条指称枚举违规），当轮落成长箱流程A
- 待你拍板（上交不代决）：第三路线「对外继续只引导 base 单档」的可行性——本轮判：作者生产已裁决留 large-qint8，对外与对内同轨优先，维持现路线为默认推荐
- 验证：两处替换 assert count==1；真机两档切换+自动重建复现 ⛔未做挂发版链 E2E（如实，不假绿）

### H11 · 对外路线回撤 base 单档（你裁决：「先去掉那个大模型吧，安装包和说明手册全部去掉，我先自己用一段时间」）
> 性质：路线回撤非返工——F8/F9/G10 的调研与数据全部留档，重开 large+压缩路线时按账恢复即可。

- **撤外面**：INSTALL Phase C 回 base 三步（模型本体 400MB 实测口径·删「整链/瘦身/删大包/档位替换」全部话术）、手册§12「语义增强与模型压缩」小节整段撤下（含提示词卡）、⑭ 脚本清单指针还原、`references/知识联邦引擎-min/scripts/quantize_export.py` 撤出包（引擎最小件 9→回 9 件口径；该件作者侧 `开发工具/知识联邦引擎/scripts/` 原件未动，你自用不受影响；包内删除有 git 历史回滚点）
- **留里面（工程修复不回滚）**：包内 `build_kb_vectors.py` v0.2 四项修复全保留——标签诚实化/CPU EP 仅在量化产物存在时生效（包默认无产物=行为零变化），**npy 双写对 base 态直接受益**（包内 search_kb v0.3.12 消费 npy·检索提速 76.8× 实测同源）；INSTALL C3 自检句保留 npy 描述
- **副产物消解（如实）**：F9 发现的「装 large 不压缩=破碎态」问题随 large 引导撤销**自然消失**——base-only 正是包内 search_kb 默认判据（MODEL_NAME=base）的原生健康态，无需改码；两档关系叙事对外不再需要（单档无对比对象）
- **回访卡处置**：FU-146/FU-147 随路线回撤 resolve 销账（实际结果=你选第三路线「先自用」，预测对象对外不复存在·非判假）
- 验证：INSTALL/手册/CHANGELOG 各切片替换 assert 全过；quantize_export 出包后引擎 scripts 目录计数=9；全包 grep「bge-large|311MB|瘦身」残留仅历史 CHANGELOG 条目（历史是事实不动）

### 2026-10-06

### F1 · 五系统文件映射进包（LobsterAI 端）
- `adapters/lobsterai/capability.yaml`：`system_file_paths` 的 key 对齐 `SYS_FILE_NAMES`
  （自造 key「自定义指令」→ 标准 `customPrompt.md`·载体仍指 `workspace-main/AGENTS.md`）；
  新增 `system_file_segments`（断章段·第五件走头部段增量）；新增 `hooks_secondary_face`（补登 `state/hooks` 面 2 handler）
- `adapters/lobsterai/setup.sh`：新增 `[4/7]` 五系统文件落盘步（端专属 → 公共回退 → 双缺报缺拒装）＋
  `[7/7]` 本端字符预算闸（OpenClaw 三上限：20,000/文件 · 60,000/总量 · `USER.md` 独立 4,000）
- `conffiles`：补 LobsterAI 五件（升级三路比较·防覆盖用户人格）
- 新增 `adapters/lobsterai/rules/`：端专属五件模板（带本端 `char_budget`·⛔不上提公共层）

### F3 · devtools 单一真相源守卫 v1.3→v1.4
- `CANDIDATE_DIRS` 写死两目录 → 实盘枚举（判据⑦）＋ `shadow_trees` 剪枝/签名名修正
- **镜像同步**：`references/hooks/` · `references/scripts/` · `references/digital-twin/devtools/`
  三份该件同步至 v1.4（原 v1.0/v1.0/v1.1·仅 1 份受 manifest 管）
- **`mirror-manifest.json`**：补 2 条 orphan entry
  （`hooks-…` / `references-scripts-…`·原仅 `scripts-devtools-single-source-guard-py` 1 目标）

### 双实体清理（漂移根因）
- `脚本中心/router.py` · `route_unknown_unknown.py`：旧实体 → 软链指本体（`Skill路由引擎/scripts/`）
- 7 件分叉同步（根 → 对照侧）；`gate_runner.py` 对照侧含 `juventini` 绝对路径（不可移植）·根侧正确

### 2026-10-05

### 根治：Trae Work 端完整性审计修复（切片路径口径收敛 + 端专属 Skill 脱敏 + 规范/文案订正）

> 缘起：Trae Work 端完整性审计报告（`个人AI档案/布洛陀安装包-Trae Work端完整性审计报告-20261005.md`）——1 真实缺陷 + 3 声明级缺口 + 1 脱敏残留，综合完整度约 88%。本次按修复路线图逐条收口。

- **P1-1 切片路径口径收敛（方案C·真实缺陷根治）**：K2/HEXACO 生成器输出**恒定落** `<数字分身>/K2切片蒸馏/slices/`（改 `OUT_DEFAULT`/`SLICES`，不论真身/部署态——真身 `K2切片蒸馏/` 与部署态 `k2-slice-generator/` 同构）；收拢 traework 适配器 5 处偏离引用（`setup.sh` / `README.md` / `templates/doenglingz-core-header.md` / 2 个端专属 Skill）到同一口径。**此前**部署态生成器输出落 `k2-slice-generator/slices`，而安装器 `_detect_existing_twin`、~15 个 hook、`plugin_path_rewrite.py`、端 Skill、《入门指南-通用版》读的**均为** `K2切片蒸馏/slices` ⇒ 跨端"已有分身"检测失效、引导路径指空。**方案C 取最小影响面**：不改 install_scripts/hooks（本就统一在 `K2切片蒸馏/slices`），只改少数偏离文件。四份生成器副本（包内 + 作者态×2）×2 逐字一致；模拟部署态端到端验证产物全部落 `K2切片蒸馏/slices`、无错落。
- **P1-2 端专属 Skill 去"皮叔"脱敏**：`adapters/traework/skills/` 下 2 个 Skill frontmatter 4 处命中（`author: 皮叔体系`→`布洛陀体系`；`upstream: ...（皮叔 Skill 真源）`→去昵称）。回归 grep `皮叔`/`juventini`/`/Users/` 在 `adapters/traework/` 内**零命中**。
- **P1-2 延伸·全端脱敏收口（回归新发现·跨端）**：`verify.sh --platform traework` 全包卫生门禁实测报红 2 件——`adapters/doubaowork/skills/` 下 `doenglingz-slice-nav-doubao` / `布洛陀-豆包办公规则` 的**版本变更行**含口语称谓裸词（`pkg_cleanliness_check.py` `PAT_PRIVATE_NAME` 判据命中）。根因：`adapters/` 为**包根直持资产·不经镜像 deident 变换**（`generate_release.py` 载明），须手工脱敏（与 P1-2 同性质，只是落在另一端）。按包内脱敏约定（「作者」，同 `作者令/作者质证` 先例）机械替换为「作者令」（口径=口语称谓裸词→公开署名，⛔本条自身不写真词以免复现同类泄漏）。
- **P2-3 06 手册 F5-1 补「全量软链端」豁免**：实测全 8 端 capability.yaml 均无 `skills` 键（系统性声明缺口），但功能不缺失——traework 端 setup.sh 对 `<MC>/技能配置/*` 全量软链到 `~/.trae-cn/skills/`。F5-1 加口径订正：`skill_symlink: true` 端**豁免白名单**，改核软链声明+软链结果，⛔不因缺键报假红（铁律-002 不假红不假绿）。
- **P2-4 05 总纲 F7 行口径消歧**：标注「**用户面**=升级+回滚+完整性校验｜**mirror-sync=发版侧工具（作者域·不随包）**」，消除清单口径与用户面定义的歧义。
- **P2-5 INSTALL.md 文案订正**：平台表 6 处「规则三文件」→「**五系统文件**」（该术语系 2026-06-04「SOUL+IDENTITY+USER 三文件拆分」时代残留，已演进为五系统文件；全表统一，防一行改一行不改）。
- **实证**：`platform_adaptation_check.py --src traework` → 面A 5/5 · 面B 7 件 · 面C 已声明 · **适配度 100%**；脱敏 grep 零命中；切片路径口径全包一致（仅剩 2 处注释留痕，非活性引用）；`pkg_cleanliness_check.py --pkg-root .` **8 类卫生全过**；`verify.sh --platform traework` **24 项全过**。

### 2026-10-03

### 根治：LobsterAI 端适配三共件（数据清理器定义域·verify 插件承载面·指纹池去私有）

- **数据清理器定义域错位（最重）**：`data_contamination_check.py` 的指纹池由**作者档案**生成，在作者机本机 `--apply` ⇒ 真数据当样例（实测一度清空 1050 张立场卡；444 的 SHADOW 崩溃曾无意挡住）。根治三刀：① TARGETS **清空**（原列 SHADOW/未知未知/立场卡—全是用户数据，清理器绝不该碰）；② `do_generate` 白名单空则**拒绝生成**（⛔ 不得以作者档案为样例源）；③ 定义域闸（池存 `seed_root_hash`·生产机拒 + `--force-producer` 双重锁）+ 写前可写性判据 + 单文件 `try/except` 隔离。
- **隐私去私有**：`references/integrity-fingerprints.json` 原池 1329 条中 **1323 条命中作者私有面**（卡/台账）⇒ 清空并注销「只准从中立样例源生成」。
- **verify 插件承载面**：`install_scripts.py --verify` 与 `verify.sh §1.6` 补 **lobsterai 插件承载分支**（注册面 = 宿主 `openclaw.json` plugins.entries + 插件源码 ROSTER；⛔ 不再按 `cli/config.json` 核 ⇒ 39 件假红消失）。
- **verify.sh config_root 空格截断**：旧用 `awk '{print $2}'` 取 config_root ⇒ 含空格的路径被截成 `~/Library/Application` ⇒ §1.5 五件全假红；改 sed 取全值。
- **capability 声明补全**：`adapters/lobsterai/capability.yaml` 新增 `hooks_surface(20)/hooks_plugins(4)` + `system_file_paths(五件)` + `twin_surface`；`hooks_registration_face: openclaw_plugins`。
- **隐私审计加 E 腿**：`privacy_audit.py` 新增「指纹池去私有」——非空指纹池必须声明中立样例源 `sample_seed`，否则发版判红（正负例双验）。
- **模板去作者路径（⚠️ 镜像层·已回滚）**：曾改铁律版/指令编写规范/文件格式规范的 `~/个人AI档案/`→占位符，但 `references/templates/**` 是**镜像层**（buluotuo-release-sync fswatch 从源侧刷回）⇒ 改动被回滚。根=`deident_rules.py` 明载「不碰 `~/个人AI档案/` 变量化·属 #27 大工程」——留作 #27。
- **实证**：`verify.sh --platform lobsterai` **EXIT=0·24 项全过·端适配 100%**；`privacy_audit.py` **✅ 全部干净**；真装 `EXIT=0`·回执 `verdict=ok`。
- **血泪**：`修崩溃前未预演“若它不崩会怎样”`；两次对生产档案做破坏性写测试（应先副本/沙箱）——同款错误重复=流程缺陷。已写 12 号 §5.9/§5.10。

### 修复：`install_scripts.py --verify` 无 MC 参数误报「脚本中心未落盘」（假红根治 + 计数派生一致）

- **病根**：`verify_deployed(mc=None)` 在 zcode 形态分支（traework/doubaowork 等）下 `base = os.path.join(mc, "脚本中心")` ⇒ mc 缺省为 None 时 `base=None` ⇒ 落盘核恒 miss。实证：`install_scripts.py --verify --platform traework`（不带 MC）误报「脚本中心未落盘 7 件」「端注册面未注册 7 件」——实盘 7 件齐备、patrol 已注册（带 MC 复跑即全过）。与既往 `__pycache__`/`.bak*` 目录盲区同源：**判据落空 ≠ 事实缺失，须区分「没核」与「核了没有」**。
- **修复**：① `verify_deployed` 开头补 MC 缺省解析——缺省回落标准记忆共享中心 `~/个人AI档案`（存在即用）；② 落盘核加 `mc is not None` 守卫（无 MC 时跳过而非误报）；③ 无 MC 且默认路径不存在时补「仅核注册面」显式提示，不静默。
- **计数派生一致（G3）**：成功行分母由 `len(ROSTER)`（19）改为实际核验清单 `n_files`——traework 交付面 7 件 ≠ 全端 ROSTER 19 件，旧文案把「只核了 7 件」说成「19/19 全过」＝数字不实。现输出「本端交付面 7/7 钩子已落盘并注册（全端 ROSTER 19 件）」。
- **实证**：`--verify --platform traework`（无参 / 带 MC）均 `✅ 7/7`；`verify.sh --platform traework` **18 项全过**；`pkg_cleanliness_check.py --pkg-root .` PASS；`py_compile` 语法 OK。

### Trae Work 端适配器补全：五系统文件/钩子面/数字分身三线对齐（装机即用·实证过闸）

- **五系统文件本端落点**：capability.yaml 新增 `system_file_paths`——五件全走 `~/.trae-cn/user_rules/` 直落制（每回合注入的实读目录），落盘名映射由 setup.sh [1/5] 承载（core-soul→SOUL.md / core-identity→IDENTITY.md / core-user→USER.md / core-memory→MEMORY.md / execution-guidelines→trae_solo_rules.md）。内容侧对齐 WB 口径：core-soul 补愿景四方向+「把沉淀当资产」品格、core-memory 补铁律骨架+三层规则索引、core-user 补「数字分身·童灵」节。
- **钩子面等价适配（非「装不上」）**：本端无 `UserPromptSubmit`/`Stop` 事件面（产品门禁硬短路），19 项 WB 钩子按等价通道纳册——7 件走 launchd patrol 拉模式（30min 巡检）+ 常驻注入承接；HOOK-EQUIVALENCE-MAP.md 逐项映射，功能等价缺口=0。
- **数字分身落点**：新增 `templates/doenglingz-core-header.md`（frontmatter `alwaysApply:true` + 实体边界/SSOT/域切片指针）——修复旧版 printf 组装**无 frontmatter ⇒ 恒驻核不被注入**（空壳核）且缺 8 要素之 #5/#8 锚点；setup.sh [2/5] 改为「头模板 + core_slice + L6」三段组装并注入切片 src_hash。童灵专属 Skill（doenglingz-guard / doenglingz-slice-nav）脱敏入包 + [3/5] 落盘至 `<MC>/技能配置` 并目录级软链到 `~/.trae-cn/skills`（幂等·不覆盖实体目录）。
- **注册面第三形态**：本端既非 settings.json 端、也非 zcode config.json 端——verify.sh §1.6 与 install_scripts.py `verify_deployed` 补 traework 分派（注册面 = `~/Library/LaunchAgents/com.buluotuo.traework.patrol.plist` + patrol 脚本 ROSTER），根治「按 zcode 读 config.json ⇒ 名册 7 件全判未注册＝假红」。
- **guard Skill 要素5 口径订正**：旧列「机制登记指针」与生成器 `extract_core`（显式跳过 `## 🔧 机制登记`）冲突 ⇒ 恒 RED 假红；改判为「🧭 域切片按需加载」指针，L6 锚点串由 `L6 反向约束层` 改 `反向约束层`（实测空格版恒 0 命中）。
- **实证**：沙盒（HOME 重定向 + launchd 打桩）跑通 落盘/软链/占位符替换/幂等复跑；`verify.sh --platform traework` **18 项全过**；`install_scripts.py --verify --platform traework` **7/7 钩子已落盘并注册**（本端交付面 7 件·非全端 ROSTER 19 件·G3 计数派生一致）；守护三查 8要素/试金石/切片新鲜度 **全 GREEN**（src_hash 914b912b0746 FRESH·core_slice 与 L6 逐字包含）。

### 修复：bash 3.2 变量名吞多字节致安装中断（traework/doubaowork）

- **病根**：macOS 自带 bash 3.2 在 `set -u` 下把 `$VAR` 后紧跟的多字节字符（全角括号等）并入变量名 ⇒ `unbound variable` 中断。实证：`setup.sh` 第 146 行 `hash=$SLICE_HASH）` 令 traework 首装**在恒驻核步骤崩掉**，[3/5]~[5/5]（Skill 落盘 / patrol 脚本 / plist）全不执行。
- **修复**：变量一律加花括号界定 `${VAR}`——traework/setup.sh 2 处（146、125）、doubaowork/setup.sh 2 处（49 dry-run 路径、98 失败提示）。
- **防复发**：全包 `LC_ALL=C grep -E '\$[A-Za-z_][A-Za-z0-9_]*[^ -~]' --include=*.sh` 复扫，adapters 下零命中。

### 修复：发布卫生门禁 `.bak*` 目录盲区

- **盲区**：`pkg_cleanliness_check.py` 的 `is_bak` 只作用于**文件**（`for f in fn`），目录名不查 ⇒ 包根夹带 `.bak-20261002-premerge/`（内含 install_scripts.py 备份）却**全绿放行**；与 2026-09-18 `__pycache__` 目录盲区同源（跳过内容 ≠ 可不报存在）。
- **修复**：`dn` 循环补 `is_bak`/`is_tmp` 目录判定（入账并 prune），真源（`开发工具/`）与发布副本同步（hash 一致 `b12834dea4f3b554`）。
- **实证**：负例测试——造 `.bak-negtest-20261003/` 即被判 `[FAIL] 备份残留 .bak*: 1 件`，清除后复归 PASS；残留目录已按惯例移出包（→ `存档包/_改造备份-20261003-traework/包根残留-bak目录/`）。

### 端 setup 委派统一：所有非占位端一个公共步骤（条文13扩展·委派链缺口根治）

- **缺口结构**：`install_entry` 全包唯一消费点锁死在 `hooks_event=false && hooks_alternative=true` 分支内 ⇒ **hermes**（hooks_event=true·setup.sh 承载 16 插件部署+挂载+三关复验）、**doubaowork**（hooks_alternative=false·setup.sh 生成待粘贴文本）、**qodercn**（rules 软链靠端 AI 自觉读 README）三端的端部署脚本**不在任何机械链上**——状态表「✅完整」实装零端件（09-55 事故形态的结构性复发条件·条文5）。
- **根治（install_scripts.py）**：端 setup 委派从 hooks_alternative 分支提为**所有非占位端的公共步骤**（与钩子形态解耦）：一律读 install_entry（缺省回退 setup.sh 兼容 autoclaw 等既有端）；端确不适用自动委派须显式声明 `setup_dispatch: manual`（⛔静默不委派=隐式假绿回归）。`post_install_message` 同步移出 hooks_event 分支（hermes/qodercn 同样可见喊话）。
- **capability.yaml 配套**：qodercn/doubaowork/autoclaw 补显式 `install_entry` 声明（autoclaw 此前依赖回退垫片——声明后回退降级为兜底）。
- **DRY 契约根治（连带发现现存 bug）**：安装器委派只传 `DRY=1` 环境变量，但 doubaowork/hermes 读 `--dry-run` 参数、autoclaw/lobsterai/zcode **不认任何 dry 通道**——现状 `--platform zcode --dry-run` 即真写盘。修复：安装器改**双通道穿透**（DRY=1 环境变量 + --dry-run 参数）；doubaowork/hermes 补环境变量读取；autoclaw/lobsterai/zcode 加 DRY=1 显式短路（未实现零写入演练的端跳过并明说，⛔不"演练着写盘"）。

### Qoder CN：setup.sh 新建 + 端名统一（Qoder Desktop 过时字面值清除）

- **`adapters/qodercn/setup.sh` 新建**：记忆中心指纹 → rules/ 4 承载件软链（core-identity/soul/user + execution-guidelines）+ 记忆中心共享注入面 → AGENTS.md/MEMORY.md 落盘（已存在不覆盖·{记忆共享中心} 占位符替换）→ skills 软链（10）→ 自验证（rules 可达 + 模板在位 + skills 计数·0 FAIL 才算装完）。原生支持 DRY 双通道；settings.json 归安装器标准分支（⛔防双写）。rules 全扫描消费端（alwaysApply）承载名即消费名·天然豁免条文12改名。
- **端名统一（用户令）**：display_name=「Qoder CN」🔮 为唯一口径——`rules/core-identity.md`（系统名/署名/排除清单/版本注 v1.1）、`templates/AGENTS.md`（标题/身份/自检）、`templates/MEMORY.md`（source）全部清除「Qoder Desktop」+🖥️；同族残留 `~/.qoder/` 配置根路径一并改 `~/.qoder-cn/`（MEMORY 路径×2·rules 路径×1）。**有意保留**：端身份排除清单「不是…Qoder Desktop」（防混淆需列旧名）与多端通用枚举表（growth-box/system-logger 等的工具名客观枚举）。

### 判据口径错位根治（verify 判据与装载变换对齐·条文19/33）＋ --verify 委派回归修复

- **回归修复（委派重构连带）**：main() 端 setup 委派在 argparse 之前执行 ⇒ `--verify`/`--list` 查询模式也触发端 setup 真跑（本端实测 --verify 输出完整安装流程）——加 `_install_mode` 守卫（查询模式跳过委派与喊话）。
- **--verify zcode 形态分支**：verify_deployed 曾按 settings.json+HOOKS_ROOT 旧判据核 zcode 端＝双错位假红（注册面实为 cli/config.json·ROSTER 件落脚本中心）——加端形态分支（settings_json=false+hooks_alternative → 注册面=cli/config.json+落盘=脚本中心）。如实结果：ROSTER 19 件中 12 挂 ✓、7 未挂（5 公共件作者端实盘未挂+[5c/8] 忠实映射·2 分身件见 capability gaps——是否适配待定夺）。
- **verify.sh §3.5/养成链段 端形态感知**：hooks/rule/ 硬布局与 hooks/ 分身落点判据对 zcode 形态跳过/改核注册面引用可达（§1.6 三查承接）——本机 5 项错位 FAIL 归零，余 1 FAIL=真实标准差（如实显形）。
- **哲学回流**：条文 33 实据段 v2 修正（首版「29% 缺口」系半面盘点误判·通读 setup 三段证实 28 件全对齐·真 gap 仅 twin 2 件——教训「盘点双面读全」入条文）＋哲学 CHANGELOG v2.11。

### 文档对齐

- `INSTALL.md` 状态表 qodercn 行：装完交付面写实（rules 注入面+模板+钩子·setup.sh 委派）。
- `step7-verification.md` 端分支注：部署表述从「已由安装器部署」改为「由安装器委派端 setup（install_entry）部署」（旧表述与实盘不符·委派化后成立）。
- `adapters/hermes/capability.yaml` post_install_message：删除对端用户误导的「已自适配」作者机状态表述，改写为装机后真实落点+验证方式；澄清包内 `rules/` 为装机参考承载件（Hermès 无独立 rules/ 注入机制·execution-guidelines 并合入端上 SOUL.md 恒定层）。
- `adapters/qodercn/README.md`：安装流程改「机械委派分工表」（setup.sh × 安装器 × 端 AI 人工面各管哪段）。

### 五系统文件端级验收 fail-closed + ZCode 端 USER 件分层适配（愿景最优解·认可落地）

- **五件口径权威化（指正采纳）**：初版名单凭 templates 目录名推断有误（把 SHADOW 当系统文件）——权威口径=`记忆蓝图/02_设计理念/02-平台端适配类/WorkBuddy布洛陀设计哲学/02-三层分离与系统文件映射规范.md` §六：**SOUL/IDENTITY/USER/MEMORY/自定义指令（customPrompt 等价物）**；SHADOW 是 L5 投影进 USER.md 的段，不算系统文件。
- **端级验收判据（用户定）**：不管什么形式，五件逐件有本端适配载体+内容百分百适配即可。verify §1.5 值形态三支：md 路径 / `path::a.b.c` JSON 字段核（WB customPrompt 即此形态）/ null（并入须注去向）；**缺键=FAIL·整表缺=FAIL·不再 SKIP 豁免**。连带实锤根治：verify 优先选中的 WB 自带解释器无 PyYAML ⇒ §1.5 曾恒 SKIP——加内置 mini 解析降级链（零依赖·_mini_yaml 同族）。
- **ZCode 端自身五件登记（首个按新判据过闸的端）**：SOUL/IDENTITY/自定义指令=并入 AGENTS.md（单通道架构·实盘取证）；MEMORY=半适配声明（~/.zcode/MEMORY.md 实测不注入 2026-08-22·auto-memory 承载）；**USER=分层适配（愿景三问裁决）**：恒定内核常驻（AGENTS.md「关于用户」锚段：身份/认知风格·内容蒸馏自 CORE Q1/Q2+动态快照）+ 演化明细走平台原生 auto-memory（每会话自动注入索引·越用越懂）——恒定常驻锁可达性、波动交给自动机制，对齐 WB 设计哲学 02§四「恒定常驻/波动按需」判据；三候选（全常驻/全 hooks/全按需）均未过愿景三问，全红。复跑 verify --platform zcode = **5/5 全绿**；hermes 补「自定义指令→null 并入 SOUL 恒定层」后 5/5 全绿。
- **端适配锚段备份**：~/.zcode/AGENTS.md.bak-20261003-useranchor（铁律005）。
- ⚠️ 其余 6 端（autoclaw/doubaowork/lobsterai/qodercn/traework/workbuddy）尚未声明 system_file_paths——verify --platform 逐端显红为预期态，逐端取证填表待推进。

### 2026-10-02

### 三案判据回流（保真度 + fail-open 面孔 + 降级副本）

- **病例①「回归器全绿但运行态错」**：回归器 TARGET 硬编码某目录而运行时真源指向另一处，两份内容不同却报 `12/12 全过`；加真阴性断言后实测指向旧件判 `D3`、指向真跑件判 `D2`，**两次都全绿**。
- **病例②「`rc=0` 零输出」**：批量把绝对路径改 `~/…` 时漏 `os.path.expanduser` 包裹 ⇒ 裸字符串永不展开 ⇒ 读取失败 ⇒ **输出全空而 `rc=0`**（比报错更贵：零输出只会让下游安静地错）。
- **病例③「较新≠较全」**：一次「归位同步」把旧件复制进真相源侧，造成 8 件降级副本（真相源侧独有函数=0，对方多 3~16 个），其中 2 件还被机械替换改了路径并丢失真逻辑。
- **判据回流**：作者侧 `守卫编写规范.md` **v1.2.207** 新增 **§3.9e**（保真三判据 + 运行时独立留痕 + 路径包裹层核对 + 函数集合差集判真伪），并补 §3.9 系列五件套索引；`01-脚本架构设计通用规范.md` **v1.3.104** 新增**推论应用实例延伸三**（三案）+ 延伸一 ⑥ 交叉引用；`INDEX.md` **v1.0.57**、进度看板 **v1.160**。端用户版 `references/templates/…/守卫编写规范.md` 同步脱敏节「三·九·3」。
- **守卫登记**：`守卫编写规范.md` §四注册表新增三行（`devtools_script_resolve_guard` / `verifier_target_fidelity_guard` / `devtools_single_source_guard`），各带首跑实证与负控证据；`buluotuo-readonly-guards` 插件 `plugin.yaml` **v1.1.0**（17 项·并去重 `guard_heartbeat_check` 重复注册）。
- **分发的三守卫**（`references/digital-twin/devtools/`）：路径可达+注入器可执行 / 验证器保真四判据 / 单一真相源四判据。负控实证：五项负控全判红、复原全绿。

### 验证器保真度守卫（新增两守卫 + 三条根治判据）

- **病根（第一性原理取证）**：验证器验证的**不是运行的那份**。`d_tier_exclusivity_dryrun.py` / `w1_vocab_dryrun.py` 的 TARGET 硬编码 `开发工具/`，而 `runtime_paths.devtools` 指向 `脚本中心/`——两份 sha256 不同，回归器却报 `12/12 全绿`。加病句断言后实测：指向旧件判 D3、指向真跑件判 D2，**两次都报全绿** ⇒ 绿灯与运行态零关联。
- **根治三条**（`references/digital-twin/devtools/verifier_target_fidelity_guard.py`）：
  ① 路径保真——TARGET 必须解析自 `runtime_paths`，⛔ 禁硬编码脚本目录
  ② 内容保真——实测件 sha256 == 运行目录同名件 sha256
  ③ 断言覆盖——档位类判据必须在回归器 CASES 里有真阴性断言
- **配套**：`devtools_script_resolve_guard.py`（devtools 目录存在 + 插件引用脚本全可达 + 注入器可执行最小实跑）·两守卫均挂 `buluotuo-readonly-guards` on_session_end ·两件随 `digital-twin/devtools/` 分发
- **注入器两条判据修复**：W1 否定前缀由固定 2 字窗改**向前扫描+连接词可跳过**（上界 6 字，超窗放弃否定判定＝宁可多召不漏召）；W3 `L2_认知风格` 触发词由裸高频词六连收窄为复合窄词（铁律-020）。
- **验证**：16 例端到端档位判组 16/16 · d_tier 回归 16/16（含新增 4 条否定语境真阴性）· w1_vocab 19/19 · d_tier `--mutant` 逮住 3 例 · 新守卫负控：变异① TARGET 退回硬编码⇒rc=1、变异② 删断言⇒rc=1、变异③ 两份同步变⇒**rc=0 抓不到**（已知盲区，如实落档）

### 判据回流：呈现点唯一性（脚本哲学 + 守卫规范 + 数字分身哲学三处同源）

- **病例**：TSL 树同回合在用户视野里出现两次 → 用户报障「老是重复显示 2 次」；改口不贴 → 再报障「你这次就没树了」；第三轮追加「不动其他端 / D3 必有 / TSL 不是 AI 想写什么就写什么」。
- **根因三条**：① **呈现路径未做排他性设计**——`tsl_echo_hook`（注入用户消息）与「AI 逐行 relay 进回复」两条路同时开 ② **把「防重复」误当「防多次呈现」**——`.consumed` stamp 幂等防的是「同一份重复投递」，**不覆盖**「同一产物两条路各呈一次」（实测 `.consumed` 一直绿、树仍每轮两次）③ **调用方自跑生产脚本**——手动跑 `tsl_verify.py` 覆盖生产槽位 ⇒ 新 stamp ⇒ 下轮注入照灌 ⇒ 刷屏。
- **判据回流（本轮）**：`守卫编写规范.md`（端用户模板）新增「三·九·2 同一产物的呈现点唯一性」——四纪律：呈现点唯一必留一条 · 幂等≠多次呈现 · ⛔调用方不自跑生产脚本 · ⛔指针行/摘要代替逐字＝构造权回流。作者侧同源回写见 `数字分身设计哲学/06` v1.113 §1.6、`08` v1.5.0、`布洛陀脚本架构设计哲学/01` v1.3.103、`守卫编写规范.md` v1.2.206 §3.9d。
- **端边界**：⛔ 不改共脚本本体 · ⛔ 不动其他端（他端呈现路径不同·须按端取证）——本判据只登记「什么样的呈现结构是错的」，⛔ 不规定各端必须关哪一条。

### Hermes 端：TSL 树「D3 必有 + 只呈现一次 + AI 无构造权」三约束同时满足

- **三约束（用户定）**：①**不动其他端**（问题只出在 Hermes 端·修法只落 Hermes 端）②**D3 必有 TSL，方法不限，但只能一次**③**TSL 的显示不是 AI 想写什么就写什么**。
- **冲突结构**：`tsl_tree_hook`（产树）→ `tsl_echo_hook`（pre_llm_call 注入**用户消息**）+ 契约要求 AI 逐行 relay（**AI 回复**）⇒ **两条呈现路径同时开 ⇒ 同一棵树必然出现两次**。⚠️ `.consumed` stamp 幂等**工作正常**——它防的是「同一 stamp 灌两次」，**不是**「树只能出现一次」。
- **裁决（端适配层·共脚本零改动·他端零影响）**：Hermes 端**停用 echo 注入通道**（改 `doenglingz-twin/__init__.py` 的 `_pre_llm_call` 一处读停用点）⇒ 树**只在 AI 回复末段呈现一次**。共脚本 `tsl_echo_hook.py` / `tsl_tree_hook.py` 本体不动 ⇒ 所有其他端行为完全不变。
- **AI 无构造权**：内容 = 脚本产出**原文**，⛔ 不改写/不摘要/不手绘/不换树；`tsl_closeout_guard` v0.8 逐行比对回复与存档 ⇒ 省略/改写/换树当场留痕。⛔ AI 亦不主动跑产树脚本（06 §1.96）。
- **作废记录**：v1.0 曾采用「末段只写一行指针」方案——**已废**。指针行 = AI 改写树 = 与「手绘」同级违规。
- **配套**：`adapters/hermes/rules/core-soul.md` 补 6.5 条（端用户可见的执行规则）。

### 2026-10-01

### 数字分身·立场卡检索链路交付修复（端用户态）

- **`build_kb_vectors.py` 进包（引擎最小件 8 → 9 件）**：端用户态此前只有 `search_kb.py` 的 `_load_vectors()`（**只读不建**），包内无向量库构建器 ⇒ `kb_vectors.json` 永不存在 ⇒ 语义层**结构性不可达**（"同义问法也能命中立场卡"的承诺无法交付）。补入端用户版构建器：路径经 `_paths.py` 自推导（⛔零作者硬编码）；`_locate_search_kb()` 覆盖作者态／端用户部署态／包内暂存态三布局；语义层解释器自路由（候选 venv）+ 依赖/模型缺失**优雅跳过**（exit 0 不阻塞调用方）；md5 增量 + 文件锁 + 原子写。由 `regen_ailib_index.py` 落卡后**自动挂接**（零新增流水线）。
- **Trae Work 端 rules 补「立场卡检索」硬路牌**：本端 hooks 被产品门禁硬短路（`capability.yaml: hooks_event=false`）⇒ `doenglingz_inject_prompt.py` 注入链路在端上不执行，端侧规则层又缺该指令 ⇒ 检索呈"**脚本可达但无触发**"。在 `adapters/traework/rules/core-memory.md` 补硬路牌（触发场景 / 数据源 `知识库/AI学习库/` / `--drill` 下钻 / 语义增强说明），由 alwaysApply 常驻注入承载，与作者侧 hook 注入口径对齐。
- **INSTALL.md**：Phase B 引擎最小件表 8 → 9 件并登记 `build_kb_vectors.py`；C3 装后自检补向量库构建步骤。
- **验证（空机沙盒端到端实跑）**：落卡（`card_id` 合规）→ `regen_ailib_index.py` 重建 INDEX（2 张卡）→ **自动挂接** `build_kb_vectors.py`（无模型态优雅跳过）→ `derive_reading_status.py` 派生 → `search_kb.py` 检索命中（"改善睡眠质量"命中「作息优先」卡·得分 10.1；"评估一下这个方案"命中·得分 7.1）。无模型态如实降级纯 BM25，装 Phase C 后语义层自动点亮。
- **如实边界（⛔本轮未做，如实标注）**：① 真实 bge 模型未下载，语义层"同义问法命中"仅以测试桩验证流程正确性，**未做真机模型加载实测**；② 其余无钩子端（AutoClaw / Hermes 等 rules_inject=true 但 hooks_event=false）规则层同样缺该指令，本轮**未同步**（待评估，见能力矩阵注⁵）。

### G2-2 走查根治·检测型环境自证

- **install_scripts.py**：缺省不再静默回落 workbuddy。新增 `_detect_platform_from_env()`：扫描 `adapters/*/capability.yaml` config_root 与盘上实况求交——唯一命中打印判定证据直装；多/零命中 fail-loud 列候选转人（exit 2）；显式参数与探测冲突打印⚠️证据行后按显式。装机归属写入 `versions.json`（platform_installed/config_root_installed）。附免疫层判据：capability 缺 config_root/解析失败当场显形，不静默跳过（.trae-work vs .trae-cn 命名漂移类病的复发免疫）。
- **verify.sh**：不传 `--platform` 时优先读装机归属登记判定端；无登记才回落 WB 且打印⚠️行（同盲区收口）。
- **INSTALL.md**：Step -0.5 探测清单改由 capability.yaml 机械生成（禁手写目录名）；路由表补"不传参数=环境自证"行；Step 0 检测1 `~/.workbuddy` 硬编码改 `$CONFIG_ROOT`。
- **step6-hook-install.md**：命令注释补环境自证语义（消灭"字面命令=只能装WB端"双账）。
- 来源：G2-2 成色走查（2026-09-30/10-01·三沙箱实测）+ triwich L1 第一性原理（seal ba25aa46e3735cae·FU-67）。改前备份：/tmp/g22_fix_backup_20261001_004539。

> ↓ 以下各批次同属本「未发布」段（本包 2026-09-23 → 09-30 施工全记录），发版时随本段一起 relabel 为具体版本号。
> 原段头 `[2.0.0-dev]` 的状态后缀已废除——发布状态只住段头，不住版本串（口径见上方「版本传承」节）。

### G2-2 首轮成色走查 7 缺陷修复批（2026-09-30 · Qoder CN 端 · 蒙眼走查报告回盘即认领）

- **走查结论**：B 中断恢复✅；A/C 未达（4 高危+3 中）→ G2 保持 🔴。报告三表已回填判据/中央账/日志（执行端令牌 a6a29c5e）。
- **修复 7+2**：①step6.5 engine/*.sh 占位符替换步骤补上 + 5 个 amber 脚本加**自我文本 fail-loud 守卫**（未替换拒跑 rc=1·变异实测；文档修防本轮、脚本守卫防下轮未知缝=防误优先）②step6 "9个Skill"6处硬写→references/skills/ 动态计数（good-good-study 漏装根因）③skill_version_check.py 字面 `~/记忆共享中心` 默认值→候选探测+找不到 exit 2 拒报假红（实测 10/10 认知+fail-loud 双验）④step1 四处 WorkBuddy 硬编码→Step -0.5 判定端 ⑤IDENTITY 模板签名占位符化 `[端名][端徽标]`+step5 端名注入指令（capability display_name/emoji）⑥synthesis_assert B判据页脚声明行豁免（条文19「修判据不修产物」直接应用·自测双向过）⑦step7 项8 关键词与模板段名对齐（北极星）⑧step7 221→模板自提口径+CSS括号防误伤⑨INSTALL 养成链加「蒸表硬前置」（C 1/3 定性：管线通道文档在、执行序失守→硬前置+自检一问，二跑复测定性）。
- **纪律**：全部机械可复验（bash -n/ast/selftest/guard 变异）；走查红线"只记不修"适用走查窗口本身，修复由认领端（本端）在锁内进行；G2 判绿=第二轮回归后，**修完≠过闸**。
- **备份**：`记忆琥珀/g2fix-pre-20260930/`（8件改前快照）。

### LobsterAI 端·脱敏路由注入插件补全（2026-09-30 · LobsterAI 端 · 发布者令「第一个缺的插件就补上，必须是脱敏的」）

- **缺口定性**：本端 `capability.yaml` 声明的实盘接入面依赖 `lobsterai-route-inject` / `lobsterai-kb-inject` 两插件，但**两件均未进包**——端用户经安装包装完只有童灵插件（注入/守护/红区闸），WB 端 `UserPromptSubmit` 的**路由注入（命中 Skill 即注入格式契约）在本端缺失**＝文件面有脚本、运行面不生效。
- **本轮补全（第一件·route-inject）**：新增 `adapters/lobsterai/plugin/lobsterai-route-inject/`（index.js + openclaw.plugin.json + package.json）——`before_prompt_build` 转发用户消息给公共注入器 `route_inject_prompt.py`（置信门控/SSOT 契约/留痕全在公共脚本·插件纯转发）；`setup.sh` 增 `[5b/6]` 段：落位 + 写 `config.json` + 注册 `openclaw.json`（幂等）。
- **脱敏（⛔进包不变量）**：删除原件的作者硬编码路径（`~/个人AI档案/开发工具/Skill路由引擎/scripts/...`）与 `/tmp` 写死——改为**同目录 `config.json` 驱动**（`setup.sh` 落定 `inject=[记忆中心]/脚本中心/route_inject_prompt.py`），对齐包内童灵插件既成范式；零个人数据、零作者路径。
- **验证（隔离沙箱·未触真实位置）**：假 HOME + 临时记忆中心 → `setup.sh` rc=0；插件落位 + `config.json` 指向部署态脚本 + `openclaw.json` 的 allow/entries/load.paths 三处注册齐（幂等重跑不重复）；`node --check` 语法通过；全链 `install_scripts.py --platform lobsterai` 部署脚本中心 83 件 + 数字分身套件 39 件 + 规则层后，部署态 `route_inject_prompt.py --prompt` rc=0。
- **如实边界**：`lobsterai-kb-inject`（第二件）**未补**——它依赖知识引擎 `search_kb`（不在包内），需一并评估；本轮只补发布者点名的「第一个」。**未真机验证**：本端仍缺 `33题→文件合成` 真机跑（矩阵 ⚠️待补），且发现主流程鲁棒性问题——`setup.sh` 任一步 FAIL（如技能未装）会使 `install_scripts.py` 委派后 `sys.exit` 中止，公共资产（脚本中心/分身套件/规则层）不再部署（本轮沙箱复现），属结构性风险待治理。

### LobsterAI 端·脚本体系运行面插件（事件类映射·2026-09-30 · LobsterAI 端 · 发布者令「根据系统特性做到最好的适配，所有全部做完」）

- **定性**：本端无 settings.json、19 钩子不注册 → 脚本体系此前只有「文件面」。本轮把 WB 端 settings.json 脚本体系钩子按**事件类**翻译成本端 OpenClaw typed hook，补齐**运行面**（「根据系统特性做到最好的适配」的机制层，而非逐条硬搬）。
- **新增 `lobsterai-buluotuo-hooks` 插件**（数据驱动 ROSTER·纯转发·脱敏通用版）：`UserPromptSubmit→before_prompt_build`（stdout非空→appendContext）·`Stop→agent_end`（观察型·日志落 state_dir）·`PreToolUse→before_tool_call`（脚本 exit2→block）·`SessionStart→session_start`（观察型）。ROSTER 与 `install_scripts.py` ROSTER 同构·单一数据源·缺件跳过·失败放行。
- **本端→CC 语义垫片**：工具名映射（exec→Bash / read→Read / grep→Grep / glob→Glob / write→Write / edit&apply_patch→Edit）+ 参数整形（edit `edits[]`→old_string/new_string；apply_patch ±行→新旧串），使 CC 形态守卫可在本端生效。
- **setup.sh 增 `[5c/6]`**：插件落位 + `config.json`（scripts_dir/dt_devtools/state_dir）+ 注册 `openclaw.json`（幂等）；并置 `entries.hooks.allowConversationAccess=true`（before_prompt_build/agent_end 授权所需）。
- **补 DT_SUITE devtools**：`twin_verdict_ledger.py`/`twin_changelog_guard.py` 此前 WB ROSTER 已注册、非 WB 端却不在部署契约 → 端用户钩子指针悬空；本轮纳入 DT_SUITE。
- **验证（隔离沙箱·未触真实位置）**：`install_scripts.py --platform lobsterai` rc=0 → 三插件（童灵/路由/脚本体系）落位+注册齐；逐类功能实跑：铁律硬墙预注入（命中铁律-001）·密钥提醒·标题结构守卫 exit2·Stop 三件 rc0·Skill写入门卫 exit2·分身裁决台账 rc0；`node --check` 通过。
- **如实边界**：⛔ `agent_end` 是 OpenClaw **观察型**钩子、不可注入 → Stop 类脚本语义降级为「观察+落日志」，与 WB「Stop 提示回灌」不等价（已登记）；⛔ PreToolUse 的 `apply_patch` 单件无 old/new_string 分离语义，以 ±行近似，`edit_heading_guard` 对该形态为**近似判定**。

### LobsterAI 端·端用户检索补全（kb-inject + search_kb）（2026-09-30 · LobsterAI 端 · 发布者令「不入包新用户怎么用数字分身搜立场卡」）

- **缘起**：包内此前只有造卡引擎（知识联邦引擎-min），无**检索**引擎——`kb-inject` 插件与 `search_kb` 均缺，端用户无法用数字分身搜自己的立场卡。
- **① 端用户版 `search_kb`**：以作者版为基做 MC 参数化——删全部 `~/个人AI档案`/`Local_Obsidian_Vault` 硬编码 → `_find_mc()` 走「脚本中心」祖先自推导；检索源落 `[MC]/知识库/{AI学习库,概念卡,读书笔记,知识池,蓝图索引卡}` + 成长箱 + 技能配置；向量/bge 缺失自动降级纯 BM25（`_VENV_PY`/`VEC_FILE` 改 `[MC]/脚本中心/知识联邦引擎` 下）。落 `references/scripts/`→部署到 `[MC]/脚本中心/`，供 `kb_inject_prompt.py` import。
- **② `lobsterai-kb-inject` 插件**（脱敏·config 驱动·镜像 route-inject）：`before_prompt_build` 转发用户消息给 `kb_inject_prompt.py`，知识场景注入 Top-K 锚点；`setup.sh` 增 `[5d/6]`。
- **③ hooks argv 修复（狗粮实跑所得）**：给 PreToolUse/Stop/Session 类脚本传位置实参（`PreToolUse`/`Stop`/`SessionStart`）会顶到 argparse 报错 exit 2 → 被判成拦截（**实测误拦 write/edit**）。修＝这三类改传**空 argv**（脚本本从 stdin 读 payload）；ups 类仍传 `--prompt`。
- **验证（隔离沙箱 + 本机冒烟）**：`install_scripts.py --platform lobsterai` rc=0 → 四插件（童灵/路由/脚本体系/知识库）落位+注册齐；`py_compile search_kb`；`node --check` 两插件；本机 `kb_inject_prompt --prompt "写视频文案…"` 冒烟出锚点。
- **如实边界**：`search_kb` 端用户版为 **BM25 优先**（bge 语义层为选装·Phase C）；本机 dogfood 亦揭示「OpenClaw **配置热重载** vs 重启重写 `openclaw.json`」现象，已记成长箱。

### ZCode 适配器·通用层钩子注册面补全（2026-09-30 · ZCode 端 · 发布者令「新用户最终确认」）

- **缺口定性**：此前 ZCode 用户经安装包装完仅得 8 条钩子（route_unknown+分身 7）——布洛陀通用层约 20 条钩子（意图分类注入/铁律预注入/知识库激活/三层触发链/卡守卫等）件已随脚本中心部署但**零注册**＝装了不跑。
- **补全**：setup.sh/ps1 各增 [5c/8] 通用层钩子注册段——20 条命令形态照 2026-09-30 作者侧 ZCode 实盘（参数 --src zcode/--deliver/CARD_GUARD_HOST 等·env 前缀 macOS 照搬·Windows 语法不支持→默认路径降级）；幂等按名+并发写闸（flock）+缺件 SKIP_MISSING 显形；存在性检查查**包内源**（脚本中心由公共部署在委派后落位·钩子配置下次会话加载=时序天然兼容）。
- **配套纳管 7 件**（scripts 域 manifest 母×7+@v2×7）：zcode_config_guard/kb_inject_prompt（venv 缺失自动降级）/zcode_title_namer/card_id_guard/feedback_detect/manifest_registrar/audit_search_kb——全部零脏词·tilde 形态由 relocate 管线处理。
- **验收（沙盒）**：setup 后用户 config.json 终态 **29 条钩子与作者侧逐条同构**（SS 1+Pre 2+Post 1+Stop 14+UPS 11）·SKIP_MISSING 0·sh/ps1 双真跑 exit 0·verify PASS=11 FAIL=0。

### 入门指南三板块扩充＋双触点接线（2026-09-30 · Qoder CN 端 · 用户令「启动童灵，认认真真把这个事情做到位」）

- **起因**：豆包端在数字分身模块加了 onboarding 三件套（含入门指南-通用版），角度被用户点名好评——本轮追平其可用性视角并补齐三缺口（评估轮结论落地）。
- **指南 10 节→13 节**：新增「四、一天怎么用（场景流水）」「五、三档位 D1/D2/D3 大白话（回复首行档位标签的用户侧解释·此前零覆盖）」「九、它记了什么你怎么看（可观测/可抽检/可收回+否决权）」；旧四~十顺延重编号，内部引用无断链，FAQ 无冲突。
- **双触点**：INSTALL 一级点火完成段 +「分身到手后先读它」；step7 §7d 完成提示 + 第 5 项——告知从装机单点变「装机/点火/收口」三点。
- **单一真源**：源侧 `数字分身/入门指南-通用版.md` 为 SSOT，包内 onboarding 镜像字节一致（diff 0）；DT_SUITE 装载清单未变=零机制改动。
- **如实声明**：本轮改包前未先 acquire PACKAGE-LOCK（先改后补），「协议在位≠协议被走」复发已落成长箱；同轮 cleanliness 检查器被并发端收紧后显出 k2-slice-generator 7 件作者侧残留（F10 审计在案存量·非本轮引入·清理归属其维护端）。

### 数字分身造芯·全端通用化（方案 A·确定性沉脚本层）（2026-09-30 · 全端 · 发布者令「不管哪端，安装数字分身的通用流程必须一致；端接入方式各自适配」）

- **缘起（审计真断点）**：包内 `hexaco_slice_generator.py` v1 把作者本人 4 个守护偏移（Sincerity/Greed-Avoidance/Modesty/Prudence）与为其量身写的行为语句**硬编码**进 main——实测构造「一个偏移都不设的新用户」当场 `KeyError: 'Sincerity'`，非作者用户必崩，即便不崩产出的也是作者的行为语句。
- **① hexaco 生成器 v1→v2.0（通用·stdlib only）**：内置 **25 facet 高/低分第一人称行为语句库**（六域各 4 facet + 间质 Altruism），按常模百分位显著性机械渲染（P_HIGH 80 / P_LOW 20·z≈±0.84；Altruism 无常模用原始分 3.8/2.6 兜底）；守护偏移**动态遍历用户实际偏移**、按方向取语句并生成探针表；缺字段给「人话报错 + 怎么办」并 `sys.exit`，不抛裸 traceback。
- **② k2 生成器增强**：默认路径改为**相对 `__file__`**（真身 K2切片蒸馏/ 与部署态 k2-slice-generator/ 同构，删除写死的作者绝对路径）；新增 `strip_meta()` 机械剔除规格书 HTML 引导注释（跨行），弱模型没删干净也不残留。
- **③ onboarding 引导三件（新增·全端共享一份）**：`童灵·人格向量-空模板.json`（`_说明`/`_范例` 承载人话引导、自动过滤；常模均值中性占位）＋ `童灵·人格规格书-骨架模板.md`（精确匹配切片正则；每层标注「蒸什么、装机日能否填」；内置去个人化分身通用底线）＋ `入门指南-通用版.md`（脱敏十节；工具表只列包内 10 个 Skill，去掉作者卡片数量/面板/launchd）。`DT_SUITE` 新增 `onboarding` 子目录。
- **④ 安装器统一引导 + 依赖兜底**：`install_scripts.py` 主流程结尾（自检通过后）打印**全端统一「下一步·造分身」**三步引导（答题→填 onboarding 模板→跑生成器）；新增 `load_capability()`——优先 PyYAML，环境缺失走**内置极简 YAML 解析**（缩进 map/键值/行内列表/`-`列表/`|`块/注释，只覆盖 capability 受控子集），端用户**零第三方依赖**。
- **⑤ 各端适配（具体问题具体分析）**：修复 `traework/setup.sh` 切片路径硬 bug（`K2切片蒸馏/slices`→`k2-slice-generator/slices`，原路径即使用户跑了生成器也找不到切片）；`lobsterai/setup.sh` 造芯提示由「包内 references 源目录」改为部署态 onboarding；其余端经主流程统一引导覆盖。
- **⑥ 清洁**：移出 7 项作者侧件（d4_behavior 数百文件/build_d1_manifest/k2_poc_simulate/各端分发话术/D4交接单/Hermes草案/接入评估）→ `数字分身/包内移出-20260930/`（真身 K2切片蒸馏 有权威源）；`pkg_cleanliness_check.py` 新增**作者侧件名检测**（目录+文件双查，补原盲区）；修复 2 处私人称呼（`adapters/hermes/rules/core-soul.md`、`references/hermes-adapter-adaptation.md`）。
- **验证（全隔离·未触作者真实位置）**：3 种虚构人格（空偏移/均衡/单偏移）exit=0、切片精炼探针准确；空模板端到端通过；骨架模板 HTML 注释故意不删→6 切片零残留；豆包办公端完整部署（脚本中心 76 + 数字分身 39 + 规则层 + 统一引导）；清洁检查当前包 PASS、反向测试准确抓 3 件作者侧件。

### ZCode 适配器·遗留三项收官（2026-09-30 · ZCode 端 · 发布者令「按ZCode端特性做最优适配」）

- **TSL 呈现自动化 ZCode 落地（对齐 v1.93 机制·06 v1.98）**：`tsl_tree_hook.py` v1.2（Stop 产树）+`tsl_echo_hook.py` v1.1（UPS 回显）入 ZCode 端链（`TSL_TREE_OUT` env 独立树槽·对齐 env 前缀端适配先例）；共脚本升级＝**session 门控根治跨端/跨会话串台**（stdin payload session_id 过滤台账本会话行·无 session_id 退全局＝旧宿主兼容·本会话无行判非 D3 ⛔不退全局）+树头 session 比对（旧格式跳过＝兼容）+VERIFY try 链；隔离测试 **8/8**（WB 零回归 3 向+串台根治 5 向）；tsl_verify/echo/tree 纳管部署面（devtools 12 件·mirror 母×3+@v2×3·DT_SUITE 同步）。
- **Windows 安装面补全（ps1 真跑验证）**：setup.ps1 分身段（UPS 3+Stop 4·Windows 共槽由 session 过滤防串台）+skills 9→10+verify.ps1 分身 advisory 组；**pwsh 沙盒真跑 setup/verify 双 PASS=11 FAIL=0**（首次真跑即抓两真缺陷并修：`Write-Warn` 函数不存在→Write-Skip；verify.ps1 `$TMP_DIR` macOS 下解析失败→跨平台 TMPDIR 兜底·Windows 行为不变）——Windows 用户数字分身安装面从无到有。
- **desensitize-guard v1.1.5 豁免表（豁免三要素 name+basis+date 留痕）**：①单字母 x/y 占位用户名（hook_protocol 测试夹具/clock-loop 文档示例·与 xxx 同族）②pkg_cleanliness_check.py 自身行内 `EXEMPT-desensitize-ignore` 标记（检查器防自命中设计·元层豁免同族）③用户名判据同挂豁免通路（通路统一）——真包扫描全绿；顺带修 F14 夹具断言（机制已进化为隔离可收回·断言仍测原地保留·**部分修复·回收路径断言待对齐**）。
- **多端并发实录（本轮三撞）**：①看板 v1.140 被 Qoder CN 并发占用→顺延 v1.141；②derive_manifest_v2 20:29 版 UnboundLocalError（WB 域·@v2 孪生按 twin_of 机械规则等价生成+移交 WB 修）；③config.json 曾被并发写回 route_unknown_unknown 并存注册 1 条（已再清·config.json 多端无锁=结构性风险待治理）。
- **终验收**：五腿 0 新增 rc=0+twin_chain 三步全绿+pkg_cleanliness（hermes 域 2 件系 WB 并行施工带入·列归属移交）+sh/ps1 双链沙盒幂等全绿。

### ZCode 适配器·分身安装面补全 ＋ 脚本体系 10 Skill 口径（2026-09-30 · ZCode 端 · 发布者令「评估ZCode能否经安装包完整安装·特别脚本体系与数字分身」）

- **数字分身面（ZCode 形态）**：①4 件钩子件纳管入包（`doenglingz_guard_zcode`/`position3_notify`/`doenglingz_level_declare_guard`/`tsl_closeout_guard` → references/digital-twin/devtools/·白名单 9→13）——源侧先自推导改造（STATE env 化/steps 相对推导/sys.path 双路径·两环境同构·作者侧行为零变化）再 mirror force 同步占位化；②`transcript_reader.py` 连带纳管（references/scripts/·tsl_closeout 硬依赖·腿A 引用可达）·日志路径自推导；③mirror-manifest 母条目×5 + derive_manifest_v2 孪生×5（⛔裸 cp 教训：copy2 保 mtime 触发 `_file_identical` 快路径假一致 → relocate 变换被跳过 → `--force` 绕过）；④`install_scripts.py` DT_SUITE devtools 部署契约 5→9 件；⑤adapters/zcode/setup.sh 新增 [5b/8] 分身段（UPS 2+Stop 3·幂等按名·件在才挂·缺件不阻塞·条文 16）+ skills 9→10；⑥verify.sh 新增分身 advisory 组（PASS 9→11）；⑦INSTALL.md A1 补 ZCode 口径注记（19 钩子=settings.json 端·ZCode 走委派）；⑧component-versions.json `digital_twin` null→首个登记态（件数+分端钩子形态）。
- **验收（沙盒·假记忆中心+假 ZCODE_HOME）**：setup×2 幂等 exit 0（第二跑 SKIPPED×5 无重复注册）+ verify **PASS=11 FAIL=0** + 部署面占位符 0 残留 + 钩子命令悬空引用 0 + pkg_cleanliness PASS + 五腿（A/B/C/D/E）0 新增 rc=0 + twin_chain 抽卡→落卡→碰撞三步全绿。
- **脱敏事故与修复（诚实记录）**：install_scripts.py 纳管注释曾引入发布者称谓字面量 1 处（19:55·ZCode 直写未过自查），WB 端同日冲突通报并修复为「发布者令」；全包复扫 0 残留 + pkg_cleanliness 复跑 PASS。**教训＝包内直写必须先过与出包侧同判据的裸词自查**；WB 提案「ZCode 写包流程补 deident 环节」列为待办。同轮 ZCode 误跑 install_scripts 委派（传参姿势错·委派落真机）——精确清理 3 处（config 并存注册 1 条移除/数字分身-devtools 尸体 trash/钩子脚本幂等覆盖无害保留），数据清理步骤实测对作者机零文件触碰（琥珀 .bak 群系并行系统常规备份非本次产物）。
- **⚠️ 待办（如实标注）**：①setup.ps1/verify.ps1 未同步本轮 sh 改动（无分身段·Windows 用户暂装不到分身钩子·沿 v0.1.1 Win 真机先例待 pwsh 重测）；②tsl_echo_hook/tsl_tree_hook 呈现自动化为 WB 载体（ZCode 端未挂·非 06 §1.6 硬义务·呈现暂沿 AI relay+守卫反查留痕）。

### Qoder CN 端完整安装·三链断点根治（2026-09-30 · Qoder CN 端 · 用户令「启动童灵，先做完所有工作，确保这一端 OK」）

- **缘起**：三明智 L3 双 Agent 只读审计（键 20260930_190951·seal a4f2d7736f29676d）判定 🟡——装载底座就绪但「分身一级点火 / 人格运行时 / 验收门禁」三链断 + INSTALL 与矩阵双本账漂移。本轮全部修复。
- **① steps 落点参数化**（step3 新增 3c-2 端配置根：读 `adapters/<端ID>/capability.yaml` 的 `config_root` 写入 step3-done `CONFIG_ROOT`；step5 十六处、step6-hook 九处、step6-skill、step6.5、step7 全部改 `[配置根]`/`$CFG_DIR`，⛔禁裸写 `~/.workbuddy`；step7 `.mdc` 段加端分支判据=WB 专属·rules 通道端跳过改看 `[配置根]/rules/`）。
- **② 验收门禁多端化**：`verify.sh --platform <端ID>` / `verify.ps1 -Platform <端ID>`——§1.5 平台系统文件、§3.2 Skill 软链、§3.5 钩子落点按端 config_root 路由（缺省=~/.workbuddy 向后兼容）；§3.5 调 `install --verify` 透传端参（核查与安装同源同端）；**B8 根治**：§3.8 养成链由五要素全包静态检查升六要素——增装机态落点断言（已装脚本中心 ⇒ `config_root/hooks/doenglingz_inject_prompt.py` 必须在位，⛔不再只 grep 文档文本）。
- **③ 分身运行时接端**：`doenglingz_inject_prompt.py` v1.12→v1.13——`DOENGLINGZ_CONFIG_DIR` 配置根 env 正式化（Agent B 逮出的 `WORKBUDDY_CONFIG_DIR` 旁路缝升为接口·向后兼容保留）；`_END_EMBLEMS` 增 `qodercn: ("Qoder CN", "🔮")`（真源 core-identity 署名行+hook 路径指纹 `/.qoder-cn/`）；`install_scripts.py` 注册命令对 `doenglingz_`/`twin_` 钩子自动带 env 前缀（非 WB 端）。**双侧同步**：作者侧 `开发工具/` 与包内件同版。
- **④ capability 声明兑现**：`qodercn_inject_chain_guard.py` 入包 `adapters/qodercn/hooks/`（脱敏：私人称谓 5 处清零·路径 `[记忆共享中心]` 占位符化·OBSERVED_LOG 改落 `<mc>/脚本中心/logs`）；`capability.yaml` 新增 `extra_hooks` 字段，`install_scripts.py` 将其并入 **ROSTER 唯一数据源**（deploy/注册/核查三循环自动覆盖·不另抄清单）——qodercn 钩子总数 19→20。
- **⑤ 双本账对齐**：CAPABILITY-MATRIX QoderCN「33题→文件合成」⚠️待补→✅³（注³如实声明：沙箱验机制面·干净机人机全流程真机未做·与 L44 口径一致）；INSTALL L636 计数 62→**65**（58 `.py`+5 `.sh`+2 `.yaml`·Agent B B5 补获的第二处承诺漂移）+ 配置根统一注记 + verify 端参数用法。
- **验证链（全机械可复现）**：沙箱A（假 HOME+独立 mc）`install --platform qodercn` → 20/20 钩子落盘注册 + 部署后自检绿；`verify.sh --platform qodercn` **19 项全过 EXIT=0**；沙箱B WB 无参数向后兼容回归 **19 项全过**；**B8 变异测试**：删除沙箱分身钩子 → 三条 FAIL 显形（钩子总表/分身运行时落点/养成链）后还原；`pkg_cleanliness_check` rc=0（含新入包 guard）；`bash -n` + `ast.parse` 全件通过；inject_prompt `--selfcheck`（作者侧 v1.13）D3 冒烟绿。
- **如实边界**：verify.ps1/win-verify.ps1 的 PS 改动本机无 pwsh 未执行——Windows 真机属**发布前待办**（发版链须含跨平台真机项·Mac 绿≠可发布）；qodercn **Windows** config_root 形态未实测；干净机真人 steps 1→7 全流程未跑（注³）。
- **备份与并发**：改前快照 `记忆琥珀/steps-pre-s1param-20260930/`（6 件）+ `verify-pre-s2-20260930/`（4 件）；PACKAGE-LOCK 按协议 acquire/release（Trae Work 僵尸锁 8.2h 依协议 force-release 留痕）。

### 数字分身完整版·件4/5/终检 收官 ＋ 镜像路径族根治（2026-09-30 · WorkBuddy 端 · 皮叔令「按符合愿景的第一性原理最优解去处理·我只要零问题结果」）

- **件4 AI学习库路径通用化（源侧·`relocate_rules.py` 新增 `_AILIB_CTX`）**：收口「AI学习库 出现在**路径构造上下文**」形态（`os.path.join(HOME, "<档案根>", "AI学习库")` 等四形态）——原 `_AILIB_FORMS` 刻意只吃**带尾斜杠连写**形态（判据安全）⇒ 该形态**全规则不命中** ⇒ 端用户侧解析成 `mc/AI学习库` ＝**缺级·不可达**。⛔ 顺序敏感：必须**先于** `_DT_FORMS`/`_AILIB_FORMS`/引号根规则（否则`<档案根>`先被吃掉、AI学习库子级留空 ⇒ 错形态）。单测 **12 例 0 异常**（含幂等 + 判据安全：清单外形态不动）。
- **件5 daily-buddy 5.5 熔断器文案**：引擎在位＝正常流程步 / 缺失＝保留降级；已落包（一致性由 `_file_identical` 的**文本比对**腿确认，size 差 114B 纯属编码）。
- **件6 手册**：`⑯ 卡生产引擎` 节齐备（09-29 对账备份为证）——**无动作**。
- **终检 ⑫（新建）**：`references/scripts/twin_chain_check.py` —— 在**隔离沙箱**内复制**包内**引擎跑真链路（抽卡→落卡→碰撞 三步 dry-run，逐步要求 exit 0 ＋ 校验 `INDEX.md` 真写出）；⛔零触用户真实卡库、⛔不要求已装 Phase B。实跑 `EXIT=0`。`verify.sh` / `verify.ps1` 各新增 **3.7) 分身链路** 项（rc：0＝全绿 / 3＝包内引擎缺失（包结构缺陷）/ 1＝链路断）。
- **同轮抓出并根治 4 处新缺陷**：①`reference_path_check.py` 判据面缺 `知识库` 级 ⇒ **正确路径反被判断头**（4 处错红）＋3 处假阳性（sed 分隔符 `|` / 自测夹具 `x.md` / 越出中心 `..`）②`pkg_cleanliness_check.py` 的 `DEFAULT_PKG` 兜底为**作者侧绝对路径且指向已退役旧包名** ⇒ 包内副本变换后 100% 不可达**死码**（改**可移植推导** `Path(__file__).resolve().parent.parent.parent`·源＋包双改）③**包内作者口语称谓（U+54E5）泄漏 12 处**（`CHANGELOG.md` 8 行 ＋ `sync_card_frontmatter.py` 注释 1 处·脱敏红线一票否决）④`__pycache__` 污染包根（门禁抓到后隔离清理·铁律-005 trash 不用 rm）。
- **镜像变换族补齐（`relocate_rules.py` 新增 `_AUTHOR_SHIPPED`）**：端用户文档以**作者侧相对前缀**引用**已随包**件（`shadow_append.py`）⇒ 本模块全部规则无一命中（一级只吃 manifest 脚本族根、二级只吃档案根前缀形态）⇒ 原样残留；而发布包**不铺**该目录（`INSTALL.md` 零引用·实证）⇒ 端用户侧 **100% 悬空引用**（同族：腿D 路径形态 / 件4 路径通用化）。正解＝**映射到真实落点** `[记忆共享中心]/数字分身/devtools/`（⛔非加降级声明——声明＝承认不可用，与事实不符）。⛔ 只吃**具体件名**（非通配 `开发工具/*`）⇒ 检查⑪-治本 对**清单外**新脚本引用**仍然有效**，不把检测器治成假绿。定向同步 3 文件（含件4 `monthly_data_snapshot.py` 的**补同步**）→ 检查⑪-治本 **0 缺陷**。
- **`verify.sh` §0 域外降级（**结构性**判据·⛔无作者侧字面量）**：数据污染项判据＝「端用户记忆中心不应含随包样例数据」；当记忆中心恰为**安装包源码树之祖先**（＝源码机自检）时，指纹池与本地卡库**同源** ⇒ 全量命中属**判据域外**（非缺陷）→ 降级 advisory；端用户机（包解压位与记忆中心分离）行为**完全不变**。
- **登记补**：`scripts_manifest.json` 的 `package_only_assets` 补 `twin_chain_check.py`（共 8 件）；作者侧 `知识联邦引擎/scripts/regen_ailib_index.py` **同源移植**缺件自愈（`_DEFAULT_INDEX_SKELETON`），防「同一逻辑两处实现」判据漂移。
- **自检终态**：`bash verify.sh` → **13 项全过 · EXIT=0**；`platform_compat --only-author-path` **0 缺陷**；`pkg_cleanliness_check` 全过；`twin_chain_check` 实跑三步全绿。

### 数据污染检测·卡数据指纹面（件7）（2026-09-30 · WorkBuddy 端 · 皮叔令「必须做完」）

- **`data_contamination_check.py` 三改**：①`TARGETS` 增两条卡库路径（端用户 `知识库/AI学习库/立场卡*.md` ＋ 作者侧 `AI学习库/立场卡*.md`）②新增 `_expand()` 支持 `*`/`?` 通配（原只支持单文件）③`split_blocks()` 支持 `entry_start=None` ＝ **整文件一块**（卡是「一文件一卡」，无内部条目结构）。
- **指纹池重生成**：`references/integrity-fingerprints.json` **91 → 1329 条**（含 1055 张立场卡 + 274 台账块）。旧池备份 → `记忆琥珀/20260930-fingerprints-v2.0.0-91条.bak.json`。
- **同轮抓出两处真缺陷（实测·非推断）**：①**旧池已失效**——生成于 09-29，但 SHADOW / 未知未知台账**持续增长**，块哈希随内容变化 → 旧池 91 条对当前作者侧数据 **零命中**（逐 target 实测），即**污染检测早已形同虚设**；教训：**对"运行时增长的文件"用固定哈希池，池必然过期** → 池须随发布重生成（本次已恢复）。②**卡粒度错**——首版 `entry_start=r"^# "` 下 1055 张卡**仅产 20 块**（实测）；改整文件哈希后 1055 条。
- **双向验证（实跑）**：模拟用户目录（1 张自写卡 ＋ 混入作者卡 1 张）→ dry-run **1/2 命中**：作者卡被识别（正例）＋ 用户卡**零误伤**（假阳性抑制·`cat` 回读内容未变）。

### 数字分身完整版单装节（INSTALL）（2026-09-30 · WorkBuddy 端 · 皮叔令「你来做」）

- **INSTALL.md 新增「数字分身完整版单装」节**：补上 2026-09-29 定稿三阶段的**用户可见落地**——Phase A 分身基座（零下载）/ B 卡生产链路（引擎最小件 8 件·无模型）/ C 语义增强（`BAAI/bge-base-zh-v1.5` ~600MB·可选·默认跳过·失败回 B 态）+ **C1 知情同意卡五要素**（是什么 / 效果 / 占用 / 不装后果 / 你来决定·默认不装·**先展示后选择**）+ 验证三行。此前该设计**只在任务书（设计态）·未进 INSTALL（实施态）**，皮叔质证「昨天还在处理，怎么说没解决」暴露「设计态 vs 实施态」错位（只查包内 = 只看实施态·必漏源侧）。
- **Step -1 关键词路由**：新增「装数字分身 / 装分身 / 装抽卡 / install digital twin」→ 跳 §数字分身完整版单装。
- **脚本体系节交叉引用**：卡生产引擎段补指引行（完整数字分身含可选语义增强见新节）。
- **哲学回流**：安装包设计哲学 `01-安装包设计通用规范.md` v1.12→**v1.13** 新增条文 16「可选重型组件＝分阶段安装＋降级不阻塞＋知情同意」＋看板/CHANGELOG v1.5；数字分身设计哲学 `02-治理与灰度设计规范.md` v1.7→**v1.8** 新增 §8.12「数字分身完整版端用户安装设计依据」＋看板 v2.29 / CHANGELOG v2.02。
- **⏳ 未完成（交下批）**：件4 good-good-study 路径通用化、件5 daily-buddy 5.5 降级声明——二者均为**镜像条目**（源=`技能配置/`），须改源侧 + `mirror-sync`，涉占位符语义与 Skill 前置规范，单独立项。

### 安装入口体验改版（2026-09-30 · WorkBuddy 端 · 皮叔令「价值先行·不黑箱」）

- **入口职责扩展（Step -0.9 / -0.6）**：INSTALL.md 由「纯分流路由」扩为「价值先行 + 分流路由」——Step -0.9 首触先讲系统是什么 / 愿景 / 为何叫布洛陀 / 数字分身 / 支持端，再进类型检测（黑箱执行 → 可见选择）；Step -0.6 组件级版本对比 + 安装模式（全量 / 局部）选择。首条回复锁固定逐字稿（4 点），仅 `[动态项]` 替换，防临场改写导致首触面随 AI 状态波动。
- **平台亮牌不绝对化**：Step -0.9 读 `references/component-versions.json` 的 `platform_support`，只列 8 个在册端（qwen / teleagent 占位端不计）；README 标题「全平台版」→「多平台版」（皮叔判「全平台过于绝对」）。
- **组件版本单一真源**：新增 `references/component-versions.json`（真实扫描生成·非手抄）；`install_scripts.py` 新增 `write_user_versions()`——安装末尾把它落 `<记忆共享中心>/.install/versions.json`，供下次升级做组件级对比（对比读真实文件·不靠自报）。
- **README 同步**：Skill 表增「一句话介绍」栏并拆两张（≤3 列）·「关于开源」段提炼为「布洛陀精神」·读书助手更名「素裁 / sucair」并回读 SKILL.md 本体重写简介（AI 替你读 → 知识包写入知识池）。
- **哲学/规范回流**：①`记忆蓝图/04_系统文件设计/安装包设计哲学/01-安装包设计通用规范.md` v1.11→**v1.12** 新增条文 15「安装入口 = 可见的选择」（价值先行两步法 / 亮牌不绝对化 / 首条锁固定稿）+ 03-进度看板 + CHANGELOG v1.4；②`记忆蓝图/03_开发规范/发布包编写规范.md` v1.18→**v1.19** §2.6 入口文件规则补「价值先行段」（映射表 row 37 第二落点）。

### 数字分身模块 T0 施工（2026-09-29 · WorkBuddy 端 · 皮叔令「启动童灵执行·脱敏是底线红线」）

- **脱敏红线层**：①`references/digital-twin/hexaco/` 清除皮叔本体数据 79 件（本体答卷/互照全套/v12 评测/观察者/self/calibration——备份 diff=0 存 `数字分身/HEXACO测评/包内移出-20260929/`），终态白名单 6 件（HTML 答题页×2/官方量表卡×2/探针运行器/题库净版）；②题库/runner 双侧脱敏清零（含皮叔本体向量读数 H4.75·`related` 引用已去作者侧路径）；③`references/digital-twin/` 从约 220 件收敛至 29 件白名单（移出 scripts 38+d4_behavior 270+Hermes 草案·备份 diff=0）——作者工作区拷贝不随包；④指纹池 `integrity-fingerprints.json` 84→91（本体答卷/六维读数/标题特征入池·防回流）。
- **卡生产引擎落地**：新增 `references/知识联邦引擎-min/scripts/` 8 件端用户版（_paths 自推导双态/_engine_env 降级/概念抽取/落卡三件套/碰撞扫描）——支撑每日伙伴晚间复盘抽卡与好好学习落卡/碰撞；`install_scripts.py` deploy_script_center 改造（子目录保持结构部署→`[记忆共享中心]/脚本中心/知识联邦引擎/`+占位符替换改 os.walk 全层级）；端到端实装验证 81 件·INSTALLED 自推导·私人路径零残留。
- **文档同步**：`INSTALL.md` 脚本体系节补卡引擎说明+验证行；说明手册新增「⑯ 卡生产引擎」节。
- **⚠️ 边界口径更新（修正本文件 09-26 段旧表述）**：09-26 段写「数字分身/知识联邦仍不进包」——该表述已被 **09-19 皮叔终裁（数字分身融包·双模式）+ 09-20 方案A（运行件随包·本体内容件仍禁）** 取代。当前口径：**数字分身域运行件（L1 管线骨架·含本次卡引擎-min）✅ 随包；皮叔本体内容件（答卷/向量读数/工作区拷贝）⛔ 仍禁**。历史段保留作留痕，以本节为现行口径。

### ZCode adapter 落地（2026-09-26 · 融合自 ZCode 加强包 v0.1.1 · 皮叔令三阶段）

- **融合前置（皮叔令：先修自己 → 再更新哲学 → 再脱敏做安装包）**：①ZCode 端修 `~/.zcode/AGENTS.md` v1.6（共享文件索引 8 处断链实盘验活修复 + 补压缩保护声明行 + 版本行对齐 v1.5 遗漏·备份 .bak-20260926-premergefix）②元守卫 `zcode_config_guard` BASELINE 14→22 补录（2026-09-12~09-23 增量 8 钩子此前只改 config 未同步 BASELINE·实跑验证 "✅ 22 条 hooks 完整"）③ZCode布洛陀设计哲学 01/02/03/INDEX/CHANGELOG 实盘对齐回写（钩子 17→25 实挂全登记）。
- **adapters/zcode/ 从 42 字节占位 → 完整适配器**：`capability.yaml`（hooks_alternative 委派端 setup.sh·`rules_inject:false` 实证口径·ZCode 钩子真实存在且 7 事件全支持但注册面是 cli/config.json 非 settings.json）+ `setup.sh/.ps1` + `verify.sh/.ps1`（加强包 v0.1.1 同源脚本·布局相对零改动）+ `templates/AGENTS.md` + `hooks/route_unknown_unknown.py`（源=本包 references/hooks 占位符版·包内自含）+ `privacy/` 脱敏件四件套（desensitize-guard + release_contamination_check + integrity-fingerprints + decontam-templates）。
- **验收（沙盒·不碰真机）**：假记忆中心+假 ZCode_HOME → setup exit 0 ×2（幂等）+ verify **PASS=9 FAIL=0** + 包内个人态字面量 0 残留 + desensitize-guard 放行 + bash -n / py_compile / yaml / ps1-BOM 全过；Windows 脚本沿加强包 v0.1.1 Win 真机先例（本机无 pwsh 未重测·如实标注）。构建自引入产物（__pycache__/.DS_Store）被门禁抓到后已隔离清理——门禁闭环实证。
- **CAPABILITY-MATRIX ZCode「rules/ 常驻文件注入」格 ✅→❌¹ 纠正**（实测无 alwaysApply 注入语义·铁律-016）。
- **边界**：加强包（发布库/ZCode加强包 v0.1.1）原样保留服务已装 v1.5.4 老用户；新装统一走本包 `--platform zcode`；数字分身/知识联邦仍不进包（个人态边界）。

### 发版链（2026-09-23 · Qoder CN · E/F 阶段）
- **E1 镜像双树接入**：mirror-sync 为 v2.0 包派生 55 条 @v2 孪生条目（derive_manifest_v2.py 机械生成·幂等），v2.0 核心资产自此随发版链自动同步（实证根治：接入前 v2.0 ggs 0.12.2 静默滞后一版）；relocate 占位化 scope 扩 v2.0（配套实证=install_scripts.py 占位符替换）
- **E1 守卫9/9b 上线**：generate_release 发版链新增第 9 环「覆盖度反查」（双树 manifest 登记失明=红·判据源=manifest_coverage_check.py 本体）+ 9b「v2.0 内容级清洁」（条文9）；双向变异 4/4 绿
- **E2 Win CI 矩阵**：win-verify.ps1 v2.0 派生（T17 平台矩阵=动态发现 capability.yaml 端·T18 未知端 fail-loud·INSTALL 缺失显式 SKIP）+ .github/workflows/ci-matrix.yml（discover→per-端 dry-run→win-full 三 job）；本机 pwsh 冒烟 PASS=30 FAIL=1(=T12·F 补齐即消)
- **E2 UTF-8 守卫存量清零**：V9 实测双树 112+64 个直跑 .py 缺 Win 控制台守卫（v1.7.2 注入器当年只覆盖 scripts 域的既存缺口）——源侧批量注入 269 文件（v1.7.2 模板同构·py_compile 先行验·.bak+git 双恢复面）；mirror-sync 加 .tmp- 中间文件防复发 skip
- **F 文档**：INSTALL.md 派生自 v1.7.2 母本+新增 Step -0.5 平台判定（进程证据→配置根探测→问用户；端ID→--platform 路由；无 capability.yaml=未发布端明示不静默降级）；README 全平台口径；conffiles 同源

### 架构（里程碑）
- **全平台合并**：WorkBuddy + Qoder CN + Trae Work + 千问 + ZCode + 豆包 + AutoClaw + Hermes + LobsterAI + TeleAgent（10端合一包）
- **能力矩阵驱动**：Step0 检测端能力（hook/rules/settings）→按能力分支注入，非按端名硬编码
- **全量自洽**：任何端独立装完整核心，不依赖"先装 WorkBuddy"

### 治理（2026-09-23 · 童灵根治·作者令"没人在动了，启动童灵根治所有"）
- **git 基线首次纳管**：全包入个人AI档案仓库版本控制——覆盖事故从"不可恢复"降级为"diff 可见可回滚"（触发事件：06:41 脱敏评估修订节被对端跨端版旧副本覆盖丢失）
- **PACKAGE-LOCK.md + package_lock.sh**：写入串行闸三层防线（mkdir 原子编辑锁 / git index.lock / 版本基线）；写侧三步协议 acquire→编辑+自验→commit 后 release；6h 僵尸锁可 --force。锁全生命周期自测 5/5 PASS（含自测抓出 trap EXIT 自毁 bug 当场修复）
- **两判口径全包收口**：qodercn #9 硬规格剥离（3列/20字→可读控宽原则+个人偏好标注）；评估文档追记节私人称呼→中性化跟随包内脱敏惯例。复扫 adapters 各端执行准则：意图分类/愿景三问/私参数三项全绿
### 新增（2026-09-22）
- **LobsterAI adapter 落地**（阶段C 半自动）：`adapters/lobsterai/` = capability.yaml + README + `templates/execution-guidelines.md`（执行准则通用版：#1-8 私人称呼→用户，#9 只留「可读控宽」原则，具体上限统一标"用户个人偏好·由各端本地规则层按既有规范覆盖"；不进包（09-23 作者两判后）：仅表格3列20字规格——回复格式铁律/愿景三问均改判进包）
- **执行准则 LobsterAI 端融入实盘**：本地真身（含私人偏好全量）已落 workspace AGENTS.md 头部段，注入探针 4/4；CAPABILITY-MATRIX 该端 自定义指令/AGENTS.md 导航 两格 ⚠️→✅（需实证格改实证格）
- **2026-09-23 作者裁决修订**：回复格式铁律（【意图分类】结构）由"不进包"改判"进包"（本质=普适自验格式非个人审美）——通用版正文补入、脱敏评估追记、README/本CHANGELOG同步；愿景三问同日二判亦进包（认知入口·用户可见可自改），仍不进包仅表格具体规格。⚠️脱敏评估同日被对端跨端版移至包根·旧修订节被覆盖已在新路径重建追记

## 分身养成链落地：答题→计分→蒸馏→上线 全链闭环（2026-09-30·发布者质证「100题答题在哪/蒸馏环节在哪」）

- **质证成立**：原「数字分身完整版单装」只闭环基础设施部署，用户数据生产链（答题→计分→向量→蒸馏→上线）零指引——部署闭环冒充全链闭环（WB-20260930-002·引 PAT-058）。
- **install_scripts.py**：DT_SUITE 新增 `hexaco` 部署项（答题页×2＋题库＋官方答题卡四件）→ 装机态 `[记忆共享中心]/数字分身/hexaco/`——养成链第一步「答题」有装机入口（判定标准「用户更好体验」：AI 安装完主动打开答题页，用户零找路）。hexaco/ 其余件（互照报告/评测 json）确证作者侧运营产物不入部署面。
- **INSTALL.md**：新增「分身养成链（两级点火）」节——**一级点火**（装机日：D1 答题→D2 AI 计分＋效度锚定→D3 hexaco_slice_generator 基座切片上线）；**二级点火**（随用随蒸：**蒸馏清单表** 7 行——33题→L1／日记→L2+L3／月报→L2+L3+L5／立场卡→L3／SHADOW→L6／文案→L4／铁律变更→L1 重编译；资料在手随时蒸，无「等养成」门槛）；A3 由「造芯就绪检查」改指养成链。
- **verify.sh/verify.ps1**：新增 **3.8) 养成链在位**——五要素静态断言（答题页＋造芯件＋部署声明＋INSTALL 指引＋蒸馏清单），负例实测缺件转红。终态 **14 项全过 EXIT=0**。
- 教训沉淀：判「功能能否完整给端用户」＝**使用链逐步可达**（每步有入口＋指引＋产出落位），⛔部署面齐件不等于使用链闭环。

## 表达基调参数化：分身的腔调交给用户设定（2026-09-30·发布者拍板）

- **hexaco_slice_generator.py（作者侧真源·mirror 定向同步进包·源≡包 0 差异）**：新增 TONE_LIB 表达基调库六候选（沉稳直说[默认]／冷幽默傲娇／简洁高效／热情带劲／陪伴温和／学者思辨＋用户自定义通道）——向量 json 写「表达基调」字段即渲染对应腔调；未填=沉稳直说（中性安全默认，不再预置任何作者腔调）；非法值回落默认；「表达基调自定义文本」支持用户自定。
- **去作者语境**：模板正文与样例称谓全部通用化（原预置私人定调→用户视角）——发布者实例以数据保留：向量 json「表达基调: cold-humor」字段（原写死默认→迁移为用户选定值，机制同一）。
- **INSTALL.md**：D3 步升级「偏移＋基调协商」＋表达基调候选表（七行·含自定义）＋「起点不是终点」L4 覆盖说明——腔调与守护偏移同权：AI 只推荐，用户拍板。
- **验证**：py_compile 过；render_tone_section 单测 5/5（默认／中文／负例回落／自定义／现基调）；发布者实例重跑切片确认基调配cold-humor且称谓清零；mirror 反向校验 0 差异；verify 14 项全过 EXIT=0。

## 装机态验证修复：hexaco 生成器输出目录自建（2026-09-30·WB 装机态验证 WB-20260930-005）

- **hexaco_slice_generator.py**：写出前补 `os.makedirs(slices, exist_ok=True)`——装机态（模拟新用户 MC）无 slices/ 目录时开箱跑必 FileNotFoundError（作者侧因历史产物目录已存在从未踩到＝「部署面齐件≠使用链闭环」实证）。
- **验证**：源侧（K2切片蒸馏）改→mirror-sync --only digitaltwin-slicegen@v2 定向同步（源≡包 0 差异）→装机态真跑 RC=0，产物三件齐（切片 md 88 行＋端上纯净版＋persona_manifest.json）；渲染产物脱敏五查全 0（作者侧路径/写死用户名/作者称谓接动作动词/公开署名词/档案根前缀——判据词用指代不写字面量·门禁词自伤免疫）。
- **备份**：记忆琥珀/镜像工具/20260930-装机态验证/（源侧+包侧改前副本）。

## 装机态验证遗留项处置：判据推理留痕＋mirror 快路径根治（2026-09-30·发布者拍板「按符合愿景的最优解」）

- **公开署名词判据裁定（推理留痕进检查器）**：包内署名词全部来自脱敏变换「口语称谓→公开署名」（设计内）或署名性历史标注——真泄漏形态=口语称谓裸词（变换漏网时不会转署名·必被既有裸词判据抓）。「署名词+人称动词」形态经双向实测为**过度设计**（引号话术/「署名系」分类词均误联＝假阳性，且逻辑上无增量真检出）→ 裁定不加，推理注释落 `pkg_cleanliness_check.py` 词表段防后人重提。装机态署名词出现=公开署名，无隐私泄漏。
- **mirror-sync.py 快路径缺口根治**：新增变换规则签名机制——deident_rules/build_strips/relocate_rules 三规则文件内容 sha256 进快路径 key，签名变更 ⇒ 自动置 FORCE 全量重算（⛔不再依赖人记得 --force）；成功同步且反向校验 0 差异后落账签名。自检：伪造过期签→🔁自动强置触发 ✅；首跑无签名文件=None 态不误触 ✅。
- **CHANGELOG 自引入污染修复**：本文件此前条目曾把脱敏判据词字面量写进正文致包级干净度 FAIL——已改指代化写法，并立此存照：判据词一律指代、不写字面量（门禁词自伤免疫）。

## 分发源同步补齐：qodercn 端执行准则第6条加「批量多步写入」压缩态（2026-10-01·Qoder CN 童灵·JOB-003-20261001-008 延伸）

- **改的是什么**：`adapters/qodercn/rules/execution-guidelines.md` v1.0→v1.1，第6条压缩态铁律新增 `002-扩批量多步写入`（步末落点回执／子命令失败即中止整链／收尾按回执逐项独立读验／中断先盘点已完成面）。真源=记忆规则铁律版执规-002 ⑤-扩（成长箱反哺落地），本条为其 T0 恒驻层投影。
- **为什么补这一刀（自查逮出的自身缺口）**：本端先只改了运行件 `~/.qoder-cn/rules/`，未同轮改分发源——按镜像同步语义，下次装机会把分发源的旧版刷回运行件=改动被静默回滚。与包内既有判据「装机态验证」同源（部署面齐 ≠ 使用链闭环），本轮补的是**分发面**。
- **验证（三条独立读验·exit 均 0）**：① `package_integrity_check.py` 五腿全绿·棘轮新增 0；② `content-gate.py --content` 单条正文干净度扫描过（特征库 v1.3.0，⛔不用全包模式以免把他端历史遗留算作本次风险）；③ 上游/下游第6条逐字 diff = 0 差异，两端仅保留既有称呼脱敏差（包内"用户"·本地私人项）。
- **如实边界（⛔本轮未做）**：包内另有 5 份同名 `execution-guidelines`（doubaowork／lobsterai／traework／hermes／autoclaw），实测六份版本标签与 md5 互不相同＝**各端各自演化的实体，非同一真源的镜像**，故不存在"改一处六端生效"；他端 adapter 未代改——需各端自认口径后由该端落，或由发布者统一收共享真源（见 CHANGELOG 之外的立项建议）。

## frozen_ssot_guard 真源诚实化·包内副本镜像待同步（2026-10-06·ZCode 童灵）

- **改的是什么**：共脚本真源 `脚本中心/frozen_ssot_guard.py` 诚实化——锚点串指向从未存在的段形态（HEAD×工作区双查实证）→自建立起恒红 rc1 假红毒化 pre-commit 链（逼全员绕闸）→脱钩显形🟡不拦、真拦截（锚点定位成功且冻结段被改）保留 rc1·幽灵条目清退+候选登记（守卫规范 v1.2.231 ③）。
- **包内 5 份副本处置**：references/ 下副本为出厂态镜像（不在运行链上）——**不手改副本**（mirror-sync 机制管·下次发包随真源同步）；包内 references 含 `~//Users` 形态 26 行已在迁移残留扫查闸豁免清单（归档快照类·显形不拦）。
- **验证**：真源实跑 PASS rc0（空表待命态）·mount_liveness 35 项全绿。来源：你令「先把问题处理吧·并且是根治处理」链。

## frozen_ssot_guard 真源诚实化·包内副本镜像待同步（2026-10-06·ZCode 童灵·你令「未闭环的尝试去做」）

- **改的是什么**：真源 `脚本中心/frozen_ssot_guard.py`（作者侧运行件）——锚点串指向从未存在的段形态（HEAD×工作区双查实证）→自建立起恒红假红毒化 pre-commit 链→脱钩显形不拦/真拦截保留+幽灵条目清退+候选登记（详见 守卫编写规范 v1.2.231 §3.5 案例）。
- **包内副本处置**：`references/` 下 frozen_ssot_guard.py 副本（scripts/hooks/digital-twin/devtools 多处）为**出厂态镜像·本轮不手改**（mirror-sync 机制管·下次发包随真源同步）——与包内既有判据「分发面齐≠使用链闭环」同源。
- **验证**：真源实跑 PASS rc0（空表待命态）·mount_liveness 35 项全绿。来源：你令「先把问题处理吧·并且是根治处理」链。

## ZCode 端质检轮·双腿全绿收口：verify v0.2.0 三态判据 + capability 30 件口径 + setup 补载 2 通用件（2026-10-06·ZCode 童灵·你令「让用户在这一端完整享受布洛陀所有功能·第一个通过质检」）

- **改的是什么（adapters/zcode/ 三件）**：① `verify.sh` v0.1.1→v0.2.0——[4/6] 落盘位判据三态化（用户机态 HOOK_DST 可执行 / T0 迁移态正本在 Skill路由引擎·$HOME 形态零个人态字面 / 墓碑兜底态），注册面判据去 `_hook_dst` 强绑（command 含脚本名即 registered），[5b/6] 清单改 **config.json 运行时提取**（磁盘真源驱动·零手写件名·部署面 6 件+注册面 7 件含 twin 台账 2 件）；② `capability.yaml`——delivered 补 2 件通用件（triwich_closeout_guard/systemlog_stophook_check·源 references/hooks·端实盘在挂而包无承载的真欠账）+新增 endogenous 段 5 件端元守卫（grep_sandbox/memory_size/skill_health/philosophy_parity/failure_ledger·T0 施工产物·端自建不随包·条文33三态显式防漏配假绿）+删 guard_zcode 分叉残留条目（SSOT 归一后幂等恢复≠意图恢复的活例）→ 31 条=30 件口径，数字注释 28→30/20→22 全链同步；③ `setup.sh` [5c/8]——PLAN 补同 2 件（存在性检查加 references/hooks 回退）+段头 20条→22条。
- **质检抓出的 4 个缺口（06 手册腿实跑实证）**：① verify.sh 两假红（判据锚旧位+强绑旧路径·检查器漂移非本体故障）；② 2 件通用件端实挂/包不载（漏交付·qodercn/lobsterai/workbuddy/hermes/traework 全有）；③ 7 件端实挂/capability 零声明（条文33盘点义务违反·5 件端元件无 endogenous 归态）；④ capability 分叉残留条目（旧形态未清=假欠账）。
- **验证**：腿1 `adapters/zcode/verify.sh` PASS=12 FAIL=0；腿2 `install_scripts.py --verify --platform zcode` 30/30 钩子已落盘并注册（全端 ROSTER 38 件）；腿3 脱敏门禁包内零残留（[5/6] PASS）。遗留待跑：F2-6 守卫收讫真触发、F3-4 user_machine_fixture 幂等真跑、F7 manifest 对账+容灾恢复演练（下轮补，不谎报全绿）。
- **事故留痕**：verify.sh 曾含先前批次未提交改动 14+/8-，本轮误 git checkout 丢失后按 config 真源+实跑验证重建（v0.2.0 判据更严：注册面 5→7 件）；重建过程三次 NameError 自纠（噪声环境长脚本质量纪律教训）。

## ZCode 端质检轮·三项遗留全清+收讫真触发抓出跨端静默失效（2026-10-06·ZCode 童灵·你令「要做就做完·做完了才能 loop」）

- **F2-6 收讫真触发（06 手册判据=真实执行结果非挂载声明）**：--prompt 正门喂必命中载荷 → 0 输出 → 顺藤抓出**真缺口**：rule_fragment_inject.py L41 RULES_DIR 硬编码 `~/记忆规则/`，该 HOME 级软链**本机不存在**（10-06 下午真源消副本工程动 HOME 层余波）→ rule_triggers.yaml（30 条触发规格·SSOT 编译产物）加载失败 → **UPS 铁律硬墙全端静默失效**（rc=0 无输出无报错——install_scripts.py L493 注释早已预警此形态）。判定层实测完好（真源 30 条加载+探针命中 001/005），缺口=落点断链。**修复**：重建全局软链 `~/记忆规则 → ~/个人AI档案/记忆规则`（端中立·零代码改动）→ ZCode 端 --prompt 真命中输出铁律-001/005 注入文本+决策留痕 mtime 14:45→21:34；**WB 端同款守卫同步复活**（同真源脚本·跨端共性缺口一次根治）。机制面欠账登记：fixture 测声明面不测守卫读取面=盲区（本次由收讫腿补上——真触发检查腿价值的实证）；守卫读取面路径解析律（HOME 直拼 vs runtime_paths 声明面）未立规=后续条文候选。
- **F3-4 user_machine_fixture 沙盒真跑**：模拟用户机（无作者侧目录）跑安装器本体部署 834 件（脚本中心 264+分身套件）+14 键 runtime_paths 声明（devtools 键在位）+rp() 37 处+拼接式 47 目标全可取+18 插件真导入全过，rc=0；**幂等**：三跑输出结构一致。
- **F7 同步与容灾**：① integrity-fingerprints.json fingerprints=[] = 10-03 脱敏根治**有意态**（deidentified 字段留痕"1329→0"·防作者私有面进包·防误>防错正面案例；smoke_test.py L61 自证不收其 version 作判据）非缺口；② **恢复演练**：rollback.sh --platform zcode --preview 真跑（非破坏）——SOUL/IDENTITY/USER/MEMORY 无备份如实标注+三层规则备份在位（差异 19/4/10 行可预览）=恢复通道可用；③ manifest 显目制/mirror-sync 0 差异=发版侧（作者域）工具端侧 N/A 如实标注。
- **质检腿读数终态**：F1-F7 全项+映射+流程匹配已跑，06 自检手册口径全绿（发版侧项 N/A 如实标注不谎报）；端收口，可进 loop（G 路径「loop 安装包」）。
