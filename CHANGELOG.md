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
> 所以顶部段头恒写具体版本号（改完即进位，顶段=下一次发版的号；升级检测从这里取号。2026-10-09 作者裁定废止 `[未发布]` 占位备注）。
> 曾出现的 `version.md = 2.0.0-dev` 属自造状态后缀：一个号同时存在两种宣称串，
> 实测一处后缀制造 5 处门禁红＋归档名污染（`V2.0.0-dev.zip`），已于 2026-10-01 废除并上门禁。

<!-- LAST-PUBLISHED: 2.2.9 (GitHub release v2.2.9 · 2026-10-22 · 判据源=GitHub 分发仓 release 列表（发布侧实查）。本行由发布侧在每次对外发布时上移（写发布 Loop 的封口清单·G 路径报告必核该行与 GitHub 实况一致，不一致=红）。消费方=INSTALL Step -0.9 第6点「本次更新了什么」抽取区间：本行版本段(不含)→顶段(含)。） -->

## [2.2.9] — 2026-10-21（占号·⛔未发布：待下次发布批定稿最终号）

> 本版号仅登记占位（维护方 2026-10-21 令「记录更新版本号即可·2.2.9 非下次发布最终号·发布暂停」）。自 2.2.8 起已落源码、待随下次真实发布带出的变更：

- **INSTALL 第6点开屏话术改版（v4定稿·维护方 2026-10-22「认可，去修改」）**：用户屏段由单段散列改「家族块+【】小标题+逐条断行」结构；更新点按 2.2.4→2.2.9 全量重述——三明智史诗级加强（认知四象限+证据档位+缺料闸）、反方向的钟新增系统体检（指令"指令审计"）、唤醒记忆自动巡检双端上线、数字分身月度蒸馏新增系统体检凑齐五类（指令"启动童灵，做月度蒸馏"）+分身同步 L6 真状态、装省心新增升级保护手改规则文件（SD-1 用户面）、少踩坑新增 Win 误报清零+自检三态；好好学习/每日伙伴存量句按维护方裁留删；AI 抽取规则注记两行零触碰。同轮追改（维护方再批）：引擎段 3 行→4 行改双模型岗位叙事（Large 管检索·Base 管碰撞·推荐都装·都不装=文字检索兜底），术语对齐 C1 展示稿口径（文字检索/两岗/碰撞停摆）防双本账。回滚点=记忆琥珀/fbkV2-fix-20261022/INSTALL_改点6前_*.md
- **上游反馈单V2三项修复（SD-1/E-1/N-1·2026-10-22 维护方修复令·Qoder CN）**（评审轮=同日 triwich L1 批判验证·seal cc85751f）：
  ① **N-1 目录名形态归一兜底**：search_kb v0.3.17→v0.3.18 布局消费环加 `_norm_layout_walk`——候选链全 miss ≠ 目录不存在（历史包面口径曾用空格形态「10 蓝图索引卡」，
  老装机用户实盘带旧名⇒连字符 join 恒不可达·静默），逐段按 normalize(空格→-) 扫描+「形态漂移命中」显形；负例夹具 5/5（含变异自证：摘牙必红）。
  ② **SD-1 规则层判据跳过（方案A）**：install_scripts.install_rule_data 覆盖前查 `<MC>/.install/rule_data_snapshot.json` 基线——本机件 sha 指纹≠上次装机写入基线
  ⇒ 装后被手改 ⇒ SKIP+差异摘要+`.install/rule-data-conflicts.md` 冲突回执，⛔不静默覆盖；无基线老机只建线不拦（第二次装机起保护）。根治文件头关键词闸「只护知道声明的机器」
  强度分裂（实证=Win 机 2.2.4/2.2.8 两连覆盖 43→38/50→38·客户脱敏红线触发静默失效）；Skill 面 deploy_skills md5 比对先例的规则层同构。负例夹具 6/6（含变异自证）。
  ③ **E-1 验收记录状态头**：step7-verification.md 新增 §7b+ 规范（状态/模型/判据三行·「⚡语义#」为在位判据·降级态记录⛔入基线）；配套 search_kb 实现 `--status` 真分支
  ——施工中发现并根治 `--status` 原为死接口（仅在 _FAST_ARGS 豁免名单·main() 无分支·被当查询词吃掉，本窗实跑显形），现输出即状态头三行（作者机实测向量数 4157 真值直读）；夹具 3/3。
  改动面=search_kb 真源（脚本中心/知识联邦引擎·mirror-sync 三包内副本）+ install_scripts.py/step7（包自有产物面·条文49）。回滚点=记忆琥珀/fbkV2-fix-20261022/。
  ✅ Win 行为层复验：run 39731448109（windows-latest·win-fallback-4tests·2026-10-22 success·覆盖 SD-1 改动面）。
  ⚠️ Win 真机复验挂发版链 runner 项（Mac 绿≠可发布既定账：SD-1 执行体平台中性 python·N-1/E-1 无平台分支）。
- **clock-loop 快照版本死结根治**：version_truth_guard v1.5 加快照类豁免（固化件 version=源指针非内容地址·同 CHANGELOG 台账豁免理·判据与 sync_guard 同口径），根治「内容变必 bump」vs「version≡源」双闸互斥；变异测试 4/4 证明有牙不泄漏。
- **install_receipt 到货回执加严**：runtime_paths 回执从「文件在不在」升级到「声明里的键可不可达」（Trae CN 复检实证·本窗回灌 SSOT 源后三副本收敛）。
- **clock-loop 版本级联收口**：triwich 依赖声明位随本体升版对齐（消除本体/快照/依赖三处不一致）。
- **静默隐身检测与日志变体根治批**（任务卡 2026-10-21·Qoder CN）：system-logger v3.17.9 工具名变体入口封口（条目体 `- **工具**：` 值≠规范名机械改写，发生器层根治）；clock-loop v4.19.2 X-AST 谓词⑤「Skill 源隐身物理病」接入；新增 skill_source_health_check.py v1.0.3 守卫（launchd 3600s 双腿巡检，triwich frontmatter 转义隐身 3h 实证立项）；validate_buluotuo_skill 收编 AIGC/requires_twin_on_duty 两规范演化字段。
- **validate 字段口径收齐批**（维护方令「收齐」）：ALLOWED_FM_KEYS 增自有在用字段 6 个（cured_snapshot/emoji/trigger/role/dependencies_note/python_dependencies），自有 8 组件复验 FAIL=0 WARN=0；第三方组件字段口径不动。
- **双盲第18次**：clock-loop+triwich 独立盲审·揪出并闭环上述 dependencies 漏网。
- **Win 用户反馈缺陷①（心跳守卫路径正则）**：guard_heartbeat_check `script_path_of` 不剥引号 →
  Windows 引号包裹的钩子命令路径（含空格）被抽出时带前导引号/截断 → 路径存在性恒假 →
  全体钩子误判 ST_MISS 硬漂移假红。改正则优先匹配双引号内整路径、回退裸 token；mac/linux 行为不变。
- **Win 用户反馈缺陷②（verify 自污染假红）**：verify.ps1 缺 verify.sh 的 `PYTHONDONTWRITEBYTECODE`，
  自检跑包内 python 检查器时 import 兄弟 .py 自造 __pycache__ → §4 pkg_cleanliness 判污染。
  verify.ps1 补环境级禁写字节码（对齐 verify.sh L112 / win-verify.ps1 的 PYCACHEPREFIX）。
  两者同属「mac 修了·Windows 没跟」跨端对等缺口，Win 真机 pwsh 语法已验。
- **分身 L6 装机端根治（V2.2.8 用户报障·Mac/Win 同修）**：装机机 TSL 清单 L6「分身同步」此前恒显 ⚪
  「本机未启用自动同步」且注册 slice-watch 守护也不转绿——根因是 L6 账本链条的三个作者侧依赖
  （端清单 SSOT 文件不入包 / state_bus.json 无初始化种子 / 两脚本装机落点 import 分家）在用户机必断。
  state_bus_sync v2.2.0 起装机态自适应：端清单真源=本机安装事实（部署注册表派生），账本缺失自动
  种子初始化，首轮即登记分发基线并显示真状态（✅全最新/🔴M个旧版/🟡账本超龄/⚪未注册守护），
  此后新装/卸载工具每轮自动增量入账。作者侧 17 端台账行为逐字不变。验证：沙箱装机态（隔离 HOME+
  空记忆中心）首轮种子 3 端即 in_sync、L6=✅；作者态 self-test 10/10+all_in_sync 回归；e2e 门禁九项全绿。
  ⚠️ Win 真机复验待做（执行体同一份平台中性 python·ps1 未改）。
- **包面基线收口（源≡包 0 差异达成）**：mirror-manifest 补登记 `digital-twin/scripts/state_bus_sync.py`
  无主副本（此前零登记·漂移停旧版=装机 rc=4 病根之一）；triwich_closeout_guard v1.4.0×3 投影位、
  system-logger 并发写锁三件（append/reconcile/新库 systemlog_lock.py·经 mirror-manage 纳入）入包；
  consistency_guard 报 6 处存量源脏跳件漂移全部定稿收口。半成品不混入：clock-loop 4.19.1/triwich 4.7.1
  在制品 SKILL+CHANGELOG 对已还原基线，待归属窗定稿后自动投影（guard 红为设计内真状态非账外遗漏）。
- **clock-loop v4.19.0 上下文资产体检（Phase X-AST）上线**：H 路径扩双域（触发词族「循环 资产体检/loop 资产体检/上下文体检/指令审计」）+ kb-checkup.md 第五节四维度谓词表（指令互斥/触发面过宽/依赖死工具/陈旧事实·各绑机械判定式+负例）+ 处置建议表只读门禁（保留/精简/核实/弃用·删改批准权在用户）。来源=2026-10-21 K007 三源闭环评估四步案（含 better-harness 覆盖域实测排除·证据链见任务卡）。
- **资产体检调度接线**：distillation_scheduler 加「🔍 资产体检」月拍类型（寄生既有调度器·零新 launchd job·🧬同型先例·判据化见脚本规范 §二·四十）+ 蒸馏中心账行（首拍 2026-11-01）；triwich 依赖声明位 4.6.0→4.7.1 级联收口（S4 守卫配套批·version_truth 守卫并批封口）。
- **装机态蒸馏调度对等（G2·维护方令「必须让Win和Mac用户都正常使用」由灰度转施工）**：Q3路线C同款三件套第二实例——`com.buluotuo.distill-scheduler.plist.template`（Mac·StartInterval 24h+RunAtLoad·幂等静默调度器）+ `distill-scheduler-install-task.ps1`（Win·Find-Python 真机验证块 sed 原样抽取零手抄·S4U防重入·-Uninstall 对称）+ guardians.json 声明对账 + INSTALL.md 推荐注册段 + DT_SUITE 纳管。端用户装后月首待做区机械生成→童灵读区带出蒸馏三件（体检仍默认静默·用户自订才带出——2026-10-21 维护方「不替用户决定」令边界不变）。⚠️Win 真机验证=发版链预约项（Mac绿≠可发布既定账）。

- **装机态蒸馏中心账本初始化（G1）**：install_scripts bootstrap_runtime_state 新增第三 target「记忆蒸馏/蒸馏中心.md·缺才建·存量⛔不覆盖」（代码生成器形态·复用 JOB-001 台账两先例·非静态模板——账行需安装日动态计算）；入账四类型=装机态执行Skill在场者（系统日志/日记月报/成长箱/🔍资产体检），⛔统一蒸馏管道与切片管道不入账（装机态无执行实体=假待办）。端用户自此有仪器也有账：蒸馏三件到期自动提醒（产品契约节奏）；🔍体检行默认非日期=不提醒——维护方令「什么时候体检不要替用户决定」，节奏由用户改列自行订阅/退订（classify对非日期自动跳过·零新代码）。夹具5测过（创建/幂等/调度器真解析4类型/FFFD=0/形状守恒）。来源=2026-10-21 K007装机态评估·维护方「月初蒸馏带上体检」提案。

- **唤醒巡检 Win 对等件根治（awaken-memory-system 8.4.0）**：Win 用户报障「巡检趋势：日志不可用（巡检未运行或日志被清理）」根因查实——自动巡检载体三重 macOS 专属（launchd+bash+osascript），Win 装机从未有 patrol 对等件，且 plist 模板连包都没入（Mac 新用户同样从未有自动巡检，机制此前仅作者机手工装载）；文案把结构性缺失说成运行时故障属误导。落地=平台中立执行体 `awaken_patrol.py`（.sh 降薄壳·四段留痕格式不变）+ `awaken-patrol-install-task.ps1`（Task Scheduler BuluotuoAwakenPatrol·PT6H·StartWhenAvailable 补跑·S4U 加固·-Uninstall 对称）+ `com.buluotuo.awaken-patrol.plist.template` 入包 + INSTALL.md 双端注册指引 + dashboard 三态文案（未注册/未运行/被清理分说·⛔不再混贴）+ Win 触达=pending 落盘「小美」会话转述（设计决策a）+ win-verify T22 真机腿。同批自洽修复 build_advice dict↔str 恒假比较（趋势↑注记从未显示的潜伏bug）。Mac 实盘腿已验（kickstart 实跑+三态实测+Win 分支模拟），Win 真机腿待 CI/用户复验。来源=2026-10-21 唤醒巡检Win对等件根治任务卡。

- **sucair 书精华摘要文件名补书名前缀（v4.15.4）**：书籍精华摘要落盘由 `{书名}/精华摘要.md` 改为 `{书名}/{书名}-精华摘要.md`，与卡片 `{书名}-卡片N`、题库 `{书名}-题库`、文章精华 `{源标题}-精华.md` 同规（承 v3.3.1「文件名保留书名前缀=自包含标识·跨语境无歧义」教义，此前书精华是三件套唯一漏前缀者，68 本同名致 Obsidian 定位/wiki 链/复习流歧义）；config.yaml、SKILL 保存路径分流、知识池索引模板行同步。存量 68 文件已另处改名并验召回无污染。来源=2026-10-21 MemHub 评估派生的命名唯一性根治。
- **system-logger 并发写日志 fcntl 锁根治（v3.17.7）**：新增 `scripts/systemlog_lock.py`（POSIX fcntl / Win msvcrt / 否则 best-effort no-op），`append_log_entry` 的单笔 O_APPEND 与 `reconcile_overview` 的 read→os.replace 全程持同一把 `<logdir>/.systemlog.lock` 独占锁互斥（append 释放后才 spawn reconcile 避父子同锁死锁），封死 reconcile 换 inode 吞并发 append 的残窗（脚本自曝「彻底解=fcntl·pending 维护方 approval」）。验证：12 路并发 append 零丢失零挂起、4 进程临界区互斥（去锁变异必重叠，S065 判据自证）、reconcile --self-test 9/9 未回归、skill_eval+validate 双绿。⚠️Win msvcrt 真机待验（Mac 绿≠可发布）。
- **发布链 import 可达性守卫（作者侧发布工具·不随装机包分发）**：新增 `pkg_import_guard.py` 并接入 `consistency_guard`。根因：mirror-sync 的 skills-bulk 条目为 intersection_only（只同步源∩包），新文件天然漏带且 verify_parity 按设计忽略「源有包无」，本会话险酿「包内 append 已 import systemlog_lock，但锁文件未进包=装机 ImportError」。加「包内 .py 的本地 import 必在包内可解析」不变量堵整类，带 --self-test 三态（负例报1/补件正例报0/判据变异归零）。来源=2026-10-21 同上评估线。

- **verify 双端同构缺腿根治+检查⑬孪生形状对账（安装包哲学条文68落地批）**：外部评估点破「verify.sh 有、verify.ps1 没有」——实查坐实 verify.ps1 缺 §3.0 三口径/§4.6 骨架非空/§4.7 三表闭环三面（Mac 10-03~10-15 逐个根治的判据 Win 端失明·ps1 §3 目录名直配仍在中文别名目录假红病下），且既有检测全为文件级配对（L1派生式/P1资产对称），段级同构零机检=校验器的校验器缺位。根治=①判据下沉 `references/scripts/verify_pair_checks.py`（verify.sh 三段改调用壳·行为零变更+仪器未跑分态显形；verify.ps1 补同名三段·Win 端从失明转在场）；②platform_compat 新检查⑬（数据面 references/twin-sections.json·三向判据：neutral缺席红/未登记新段红/空壳豁免红·仪器故障⛔当判据绿）；③loop 安装包 G 路径 Step B1.5g（clock-loop 4.19.1）每轮自动跑；④安装包哲学条文68「孪生同构律」（维护方批「做；批」·编号记：拟号67时并行窗先入册顺68）。检查⑬首跑精准报三缺腿零过报+9测夹具全绿（含三口径中文别名/空壳点名/未登记段/空basis/台账缺失）。真源=脚本中心/守卫×2+mirror-manifest 4条目。Win 真机腿随下次 loop 安装包（T22 并轮）。来源=2026-10-21-verify双端同构缺腿与孪生对账规则-任务卡。

- **蒸馏调度器加「��️ 卡库体检」月拍（R6·闭合"产出无消费=死数据"）**：DISTILLATION_TYPES 新增卡库体检月拍（寄生调度器·⛔不新建 launchd·同资产体检/切片复检先例），执行体=童灵跑 kb_card_stats.py 出僵尸/热卡候选→维护方定归档，首拍 2026-11-01；调度器三落版（references/scripts·hooks·digital-twin/devtools）已 mirror-sync 投影、反向校验源≡包。
- **蒸馏调度器 self-test E1 假红根治**：e2e 自测段原复用被 S 用例 reminder_record 污染过的 state 文件，因周档巧合签名相同致首跑 main 误判"已提醒"→写 0→E1 恒红（HEAD 既红·非生产 bug）。改 e2e 用独立干净 state，生产逻辑零改动，MUT 转 OK（变异测试仍抓到·非侥幸）。

- **构建链 V9 三链接线补齐 + append_log 静默丢字段盲区根治（源面批·发布链两件）**：①generate_release.py 实接 build_strips.inject_console_guard（三写点全挂·幂等）——此前其注释声称「三链共用」而 generate 未接线=声明≠实现（条文68逮出的挂账项销账），实证=修复后真跑 generate 包内 awaken_patrol.py 的 V9 三流守卫存活（此前必被剥）+单元牙检3/3（无guard注入/幂等/非py不动）；②system-logger 3.17.8（源面已落）：append_log_entry 三级机械保证（无###标题层级矫正/字段注入去锚依赖/写前自证闸拒写兜底）根治「## 标题+非粗体条目」静默丢字段错组盲区，夹具 6/6 全绿（假 logdir 零污染）——包面投影按串行纪律由 system-logger 在批窗（v3.17.9 组）定稿时合并带出，本窗不夹带。来源=任务卡2026-10-21-append-log静默丢字段盲区+本窗三令收尾。

- **Win 安装体验根治（执行主体+兜底入口+检测实证）**（任务卡 2026-10-21·Win 用户"为什么让我跑 PowerShell"报障触发·Qoder CN）：INSTALL.md 增「执行主体铁律」块——所有代码块命令一律 AI 自身终端执行、⛔禁止把裸命令交给用户，附四级自救顺序（ExecutionPolicy Bypass / 解释器绝对路径探测并跳过 WindowsApps 商店别名 / bash 语义拆分与 PS 等价命令 / 双击安装兜底）与「Step 0 检测实证律」（分流检测必须贴工具原始输出，贴不出=没执行=禁进分流决策表，防"知道路径"冒充"读过路径"；PS 等价检测命令组已登记条内）。包根新增 `安装兜底.bat`（纯 ASCII 壳——cmd 按控制台代码页解析 bat，BOM/中文会坏首行）+ `fallback_install.ps1`（UTF-8 with BOM——PS 5.1 无 BOM 按 ANSI 读；WorkBuddy 端专用零询问，Find-Python 复用 win-ps1-python-resolution 真机验证模式，只调用 install_scripts.py/verify.ps1 不复制逻辑，失败停窗留截图）。验收边界：Mac 侧已静态自验，Win 真机（行为层 runner+体感层双击）未过前不判全绿。

- **path_integrity_check 段重复类明细盲区根治（R7 诊断轮逮获·第4雷）**：checker 的 hits 含 4 类（double/placeholder/tilde_prefixed/repeat）但非 quiet 打印循环只列 3 类——repeat 命中「计数进总数、明细恒静默」，verify 报「共 1 件命中」却给不出哪个文件（诊断 run 39630963441 实锤）。检测器报账不给证=同族「零命中≠不存在」的反面「有命中无数」。修复：detail 循环补第 4 类「段重复畸形」+docstring 补检查项④（判据 2026-10-10 补类时文档与打印都没跟上的两截欠账一并清）。负例实跑：构造 `a/b/a/b` 重复段产物→`[FAIL] 段重复畸形: 1 件 - bad2.py` 行级明细在场。同轮 diag 终验（run 39632195118）锁定「1 件」真身=checker 自身源码两行（正则定义行+病形注释行）自伤假阳性——补 PATH-INTEGRITY-EXEMPT 行级豁免×2，双向自证：自扫归零(rc=0)+负例仍点名。假阳性系 2026-10-21 他窗加病形注释行引入、被 detail 盲区掩护至本日——一雷双层（检测器又瞎又自伤）。真源=脚本中心/path_integrity_check.py，mirror-sync --force 双落版投影（--only 快路径判"无变化"反向校验报不一致=条文11 mtime+size 假一致同族复发，--force 立干净基线）。

- **clock-loop v4.19.4：G路径新增 Step B1.5l「Windows 行为层证据链对账」**（2026-10-22·维护方问「可以加到Loop安装包规则么」拍板）：R7-R9 五枚真雷全部由 windows-latest runner 逮出、零枚出自 Mac 静态自验——「Mac 绿≠可发布」由文档口号升为 Loop 每轮机械步（装机链改动 vs blt-win-ci-public success run 对账·run 号回实盘验真·无改动显式记⚪免检·gh 不可达判黄不判绿·红=建议发起⛔自动踢CI）。源 commit 2754e5dee+归正批，mirror-sync 定向投影三落位。

- **自检报告三态分账+兜底 Skill 落位腿补齐（R9·「彻底根除」令）**（2026-10-22·Qoder CN）：runner 全绿后终审红项拆出三类病一并根治——①verify.ps1/verify.sh 双端（条文68 孪生同改）新增 [PEND] 待办态：引导段未跑（判据=条文39 既有 step5-done 标记，零新判据）时 CORE.md/平台系统文件/目录骨架/摘要版注入类缺失报「⏳待办·答题后重跑即消」不报 FAIL，汇总行三态「机械段全绿 N · 待办 M」，⛔把结构性缺口说成运行时失败（唤醒巡检三态先例的包面推广·条文70 立法）；②fallback_install.ps1 补 [2.5] `--deploy-skills` 落位腿——Skill 落位是纯机械动作被错归 AI 段，兜底用户恒缺 10 Skill（runner 0/10 逮获，与 INSTALL 步骤6 L612 主路径同一条命令对齐）；③pkg_cleanliness_check 新增 `--exclude-runtime`（真源脚本中心/守卫·三落版投影）：装后自检排除装机过程出生物(.lock/pycache)，发版侧不传=检测力度零削弱——旧治 PYTHONDONTWRITEBYTECODE/--fix-cache 只封自检自身、装链产生源漏网的结构闭环。验收挂 runner T5。

- **fallback 链 MC 路径下传修复（runner 行为层四测逮获）**（2026-10-21·GitHub windows-latest run 39620298697）：fallback_install.ps1 调 verify.ps1 前未设 `MEMORY_CENTER`，verify 落回默认 `~/记忆共享中心`（作者机靠软链凑巧在场），全新 Win 机/CI 机上 CORE.md/规则三层/Skill/检查点链全部连坐假红——Mac 静态自验不可见、真机一跑即现形。同轮 T2 再逮二雷：本文件跳别名正则单反斜杠=坏正则（.NET 中 \p 非合法转义），伪造商店别名被无牙跳过选中——修正双反斜杠对齐真机验证块原形态（家族普查：包内其余件均双反斜杠或 -like 通配，独此一处手抄歪）。修复=调用前 `$env:MEMORY_CENTER = $mc` 一行；同轮 runner 实证：安装兜底.bat（LF 形态）cmd 全链跑通、ps1 BOM 中文零乱码、Find-Python 选中真实解释器、脚本中心 290 件部署、探针清理不毁历史 step 标记。来源=2026-10-21-Win安装体验根治-任务卡 R7。

- **写前探测硬闸（Win 装机阻塞1根治）**（任务卡 2026-10-21·Win 用户实测"E盘 mkdir Permission denied·9+条规则拦截"案·用户报障后定责评审通过、批"做我们能做的"）：install_scripts.py 加机械闸 `_mc_write_probe()`——安装/升级模式落件前对目标 MC 做 mkdir+试写+试删，被拦当场停并打印定责（安全策略误拦批量写入≠包代码出错）+ Defender 受控文件夹/第三方杀软放行指引 + 默认位替代路径 + 半安装态安抚（重跑即走修复模式不用返工）；dry-run 与查询面跳过不污染。`fallback_install.ps1` 同语义 [1.5] 探测段（⛔只删探针自身，.install 历史 step 标记不碰——施工窗自检逮到的毁账 bug 已修）。INSTALL.md 增「Step 0.7 写前探测硬闸」护栏块（AI 代跑/兜底双击/内置机械三面覆盖·机制不靠 AI 自觉）。自测：正例 rc=0、负例只读目录 rc=1 带全套指路、探针零残留（Mac 侧行为层实证；PS 语法与真拦截行为挂 Win 真机项 ⚠️）。

## [2.2.8] — 2026-10-20（分身岗位心跳机检 + launchd 漂移重指提案 + Qoder CN 钩子126风暴根治）

**变更**：
- 对账官 `position3_audit.py` v1.10→v1.11：新增**判据⑥「岗位心跳」**——数字分身各岗位按判决台账机械聚合，在册岗位连续 30 天零判决自动显形 🟡休眠（只显形不撤岗，撤留归用户）。作者端首发第 176 轮四岗全✅并实证推翻一条二手旧账。负例夹具 11-15 五例全过。
- 巡检 `launchd_health_daily.sh`：新增 1b 段「plist 脚本漂移重指提案」——脚本搬家后 plist 未跟随时自动出提案（唯一同名才提案，多义不猜）。配套工具 `plist_repoint.py` 本批**未随包**（新包件待裁），daily 段以 `[ -x ]` 缺件跳过为设计内安全态，端机不崩仅少提案。
- 用户可感变化：系统建设页的「数字分身在岗情况」从"人翻台账"变"每日对账自报"；升级者无需操作，对账作业（position3）在装机链路原有 deploy 步骤自动带上新版。

**判据**：待本轮出包+真机跑验（T20/T21 沿用上轮 harness 口径·⛔Mac 绿≠可发布）。真源 commit=ce9f52ee7。

**变更（Qoder CN 钩子126风暴根治线·交接卡 2026-10-20 21:05）**：
- `qodercn_config_guard.py` v0.27（风暴判据部分，执行位判据已在 2.2.7 收录）：
  ① 判活窗口收编轮转日志 `hooks.N.log`（按 run 目录分组·PROBE_MAX_FILES 封顶）——旧 glob 精确名致风暴 48 败中 40 条结构性不可见；
  ② 新增 `_storm_flip_scan` 双判据：FLIP_ALERT=同命令最新 run 连崩≥3 条 126/127 无成功回执（分布形态判据·不依赖绝对计数），跨 run 翻转/persistent/intra-run 三型；STORM_ATTR=libxpc 断言指纹 ±2s 配对加分路；
  ③ Stop 强提醒自带会话级自愈指引「先重新登录·⛔不怀疑文件权限」（10-20 两次实测重登录自愈，人肉判据吸收进机制）。
- `sescan_shim.py` 首次入包（references/hooks/·读模式镜像扫描钩子·PASSTHROUGH 参数透传）：官方 security-scan 插件钩子在 macOS 因无 shebang .cmd 依赖 shell fallback 间歇全崩时的本端兜底件；随 install_scripts 全量投递，⚠️ 挂载不自注入——装机端按需挂（Qoder CN settings.json PostToolUse）。
- 伴生：mirror-manifest +1 条目；doenglingz_guard 条目 src 直址化（既存断链修复）；sescan_shim 真源归位 `脚本中心/守卫/`（执行位改软链同源·先例=search_kb 派生副本口径）。

**判据（126风暴线）**：守卫自测 84/0（39 系 5 例含真机跨 run 形态夹具+双负例）；真机风暴日志直投 FLIP_ALERT 抓到（hard=48·首09:05:54末17:13:25）；consistency_guard 0 偏离；重启后产品 config loaded handlers 71 证实新挂载加载、if 过滤生效。根治效果挂 FU-209/210 回访（到期 11-03·判假式已绑）。

## [2.2.7] — 2026-10-20（路由引擎新装机根治 + 升级路径三缺口 + Windows 判据对等）

**变更**：
- 路由引擎 `router.py`：`SKILLS` 由硬编码 17 名改为**目录扫描派生**（目录含 SKILL.md 即入表）。旧表含 7 个不随包的 Skill，新装机 `get_desc` 首个缺件即 FileNotFoundError，被上层失败放行吞掉 → 路由整条静默死。新增 `BULUOTUO_SKILLS_DIR` 测试隔离缝。
- 升级路径缺口：①钩子注册增"同内容副本（sha）"去重（改名 fork 不再双注册同一注入钩子；⛔不用后缀族——kb_/doenglingz_ 同后缀不同职能）；②老用户身份判据补 `.install/versions.json`（此前漏它 → 已装用户被误判首次安装）。
- Windows 判据对等：`workbuddy_skill_health_guard` 认 Junction/reparse point（此前 junction 被当实目录报 WARN）。
- 安装器 `TEXT_EXT` 扩 .jsonl/.txt/.cmd/.swift（Skill 拷贝链未来形态的占位符本地化）。
- `verify.sh` 增"装后自检"语义头注（未安装目录运行必报失败≠包缺件）；`version_diff` 增快照滞后注记（落后判定以实盘为准）。
- 软链巡检补硬链抽查（nlink>1 非依赖件=违规，防"删文件重建"式升级静默断链）。
- Win 真机 harness 增 T21：新装机路由冒烟（SKILLS>0 且 "loop 安装包" 命中 clock-loop）。

**判据**：待本轮出包+真机跑验（T20/T21）。

## [2.2.6] — 2026-10-20（装后清扫 + 发版三一致门禁 + 变更日志写入口跨布局）

**变更**：
- 装后清扫（tiger① 存量根治）：`install_scripts.py` 新增 `--sweep-ghost` 与装后自动执行——把家目录根/记忆中心根的字面 `[记忆共享中心]` 幽灵目录**移动**到 `<MC>/.install/ghost-sweep/<name>-<ts>/`（可逆·⛔永不删除）；移动失败只告警不中止
- Win 真机 harness 增 T20：幽灵目录迁移 + 备份内容完整 + 二次清扫幂等（`-LiteralPath` 防方括号通配）
- 发版三一致门禁（Q6）：新增 `three_way_gate.py`（①manifest 声明件⊆包实有 ②zip≡包树逐件 ③未展开占位符 0 ④双向差额 ratchet 基线），接线 `generate_release` 守卫10——不通过即拒绝出包
- `changelog_append.py` 写入口候选面扩：脚本位置上溯 4 级 + `MEMORY_CENTER`/`MC_PATH` 环境变量 + 家目录默认（非默认记忆中心/异盘/中文用户名不再 exit=3）

**判据**：守卫10 本地 PASS（826 声明件全实有·zip 1486 件逐件一致·双向差额基线 436 件在册）；T20 随本轮 Win 真机跑验。

## [2.2.5] — 2026-10-19（Q1分发补件 + Q3分身周期守护路线C进包 + WorkBuddy亮牌纠黄 + 首触第6点增补）

**变更**：
- `references/知识联邦引擎-min/` 补 route_table.json + kb_query_trail.py（V2.2.4 审计#1 分发漏件根治：装机端语义检索判据+TSL L7-3 动作账）
- Q3 路线C装机周期守护进包：`references/digital-twin/guardians.json`（声明层单一真源·Q6门禁②对账源）+ `scripts/com.doenglingz.slice-watch.plist.template`（mac）+ `scripts/slice-watch-install-task.ps1`（win·Find-Python规范+间隔型触发）+ install_scripts DT_SUITE 接线 + INSTALL §slice-watch 注册段
- 阈值单源化（方案①）：state_bus_sync `--update` 写 `l6_policy.stale_days` 入账本，tsl_verify L6 读账本（fallback=3 等价旧值）——同值双写分叉根除
- `path_migration_sweep_guard.py` v1.4：字面 `[记忆共享中心]` 目录盘上实存跨端判据（影子目录根治·包面副本随正链）
- install_scripts L931 注释归一：route_table 从"⛔不入包"改判为引擎根功能判据（防下个读者按旧口径删）
- 话术与亮牌：WorkBuddy 🟢→🟡（第5件自定义指令=设置框字段需粘贴1步·与豆包办公同构·capability.yaml L45/L144 实证）；首触第6点增补检索修复与自动巡检两行（用户话术·三查定屏）；README 头 2.1→2.2.5 归位
- venv 跨端形态修复入包账（A-1~A-7）已记 2.2.4.x 系列见作者侧变更日志·本包面为其载体

**判据**：twin_chain_check 沙箱三步绿·mirror-sync 826条目/0漂移·隐私A7 RED=0·路径完整性模板面PASS·tsl_verify L6 负例🟡/复原✅。Win 真机腿（5.1语义/注册实跑）留 Q7 harness 轮，⛔Mac绿不顶真机账。

---

## [2.2.4] — 2026-10-19（安静模式实装·D3分层开关+包面安全词表同步）

**变更**：
- `references/hooks/doenglingz_inject_prompt.py` v1.24→v1.25：新增安静模式（flag 持久态·词面腿全关+事件腿粘滞压制+启动童灵穿透退出）
- `references/scripts/doenglingz_inject_prompt.py` 同步
- `references/digital-twin/devtools/doenglingz_inject_prompt.py` 同步
- `adapters/qodercn/rules/core-identity.md` 安全词表：安静模式定义更新
- `adapters/qodercn/templates/AGENTS.md` 同上
- `adapters/zcode/templates/AGENTS.md` 同上

**设计规格**：安静模式 = D3 全关（词面+粘滞），仅"启动童灵"穿透退出；D1/D2/事件腿不受影响。持久态跨窗口。

### 话术面（同批确认系列·走查窗定稿 2026-10-19）
- 首触第6点：八行用户价值翻译终稿（公开版基准=LAST-PUBLISHED锚即上次公开发布版；三查定屏+族序律入执行注记）
- T9 收口屏：新增分身"两模式"介绍段（自动上岗默认/安静模式开关），先于 D1/D2/D3 档位
- 老用户链路：播报C后第6点全文补播条款（折叠≠丢失，基准=已装版→现版）；播报B 新增记忆中心路径保险问（特名老用户免误判重答 33 题）
- WB 自定义指令双投影定稿：手册皮叔实战版=活体原文（未脱敏标注），包内粘贴版=通用化 1433 字（全字符尺·框上限1500）（第9点可读性为先/不强制形态/执规悬空指针归正）；第5件屏去手册跳，改对话内"讲讲自定义指令"零跳出口
- 分段发屏锁：每站独立消息/【】小节成段/清单逐项一行，违反判不合格（INSTALL 播报表）
- 记账说明：2.2.4 段初版由 d5edf998f 误名代发（并发窗落盘件），内容归机制线本位，此条为两线合账声明

**判据**：21/21 负例全绿（词面组 18 + 粘滞组 3），selfcheck 通过。
- 增量Loop对抗审查根治（v1.26·2026-10-19）：进入检测四修——①反向话术豁免（"关闭/退出/取消安静模式"不再翻转成开启）②疑问形态豁免（"安静模式是什么？"不误开启）③机器块过滤拉平 ④全出现位判定；负例包内载体=w1_quiet_regress.py（12用例全绿·本包可跑）。三副本同源同版。

**来源**：用户 2026-10-19 定稿「安静模式只针对D3+上岗Skill不受影响+关触发腿」→ L2 验证 → D1 实装。

## [2.2.3] — 2026-10-19（夜间修复批·V2.2.2 沙箱走查 33 卡根治·隐私脱敏+装机机制链+终点叙事归位）

（条目抽取=首触第6点执行注记·三查定屏·2026-10-19 起生效）
- 【系统文件】MEMORY 模板路径索引去他端裸写改 `[配置根]` 占位符入 5d-6 替换面（P19）；SOUL/USER 模板端名裸字面改 `[端名]` 占位符+5d-2 注入义务（P09）
- 【用户基本规则】三层规则私域叙事源侧脱敏+contamination 门禁覆盖面扩三层规则（P18）；盲审清单锚点归正·词表补 DO NOT+引用豁免+4.3 索引层对齐（P20）；摘要版模板三表 19 行 38 格作者答案占位符化（Win 真机腿逮出·P18 姊妹案）
- 【Skill】clock-loop pkg-checkup 引用归正包内实位（P01）；koujing_audit 补 Win 控制台 UTF-8 守卫（V9）
- 【脚本体系】verify 注册面异质断言+settings 解析哨兵（P08）；Skill 落位后 relink 复链判据（P11）；钩子内容指纹三态+deploy 写侧改件保护（P12 根治）；检查点链 step7-done 归位（P23）；manifest/琥珀白名单端映射机械解析（P17/P13）；launchd 现代 API+plist HOME 注入+泄监显形（P13#2#3）；体检 NEVER 哨兵人话化（P15）；dual/large venv 自建+前置缺 rc=2（P26）；zip 归档排除面同源（P04/P00）；出包 sha 单脚本入口收口（P05）
- 【数字分身】hexaco 答题页物理单源+scorer 答卷来源指纹拒收+--allow-legacy 逃生口（P28）；答题页效度字段真值计算+硬 V 强确认+localStorage 键路径隔离（P29/P07）；V2 判据降级标注制·作者定案（P30）；8 站终点叙事归位·T9 唯一终点+D5 终验收口+盲审第三出口（P21/P22/P31/P32/P33）；旧五要素表等文案双本账单源化（P25）
- 全程逐卡 commit+机检正反两腿；G 路径 Loop+GitHub Win 真机 T1-T18/V1-V15 全绿；发布判定见 评估知识库 pkg_tests V2.2.3 检查报告。

## [2.2.2] — 2026-10-18（UserPromptSubmit 钩子 stdin UTF-8 解码根治·Windows 中文标题乱码修复）

- Fixed：`session_title_namer.py`（references/hooks | scripts | digital-twin/devtools 三副本 + 开发源 脚本中心/内容创作）hook_mode 改用字节层 `sys.stdin.buffer.read().decode("utf-8", errors="replace")` 解码宿主写入的 stdin JSON，彻底不依赖文本层 `reconfigure`。根治 Windows 上 `sys.stdin` 默认按 GBK 解 UTF-8 字节导致中文主题段乱码、仅日期(ASCII)与常量「探索」幸免的问题（同类 mojibake 与 T16 verify.sh 修复同源）；旧版裸 `sys.stdin.read()` 保留为兜底回退。

## [2.2.1] — 2026-10-17（沙箱走查 21 项根治·隐私出包清零·Windows 编码防护）

- Removed：**摘要版「干净通用模板」内嵌作者 19 行真实答卷随包分发**（V2.1.3 走查 P0-C3 原样复发·本版根治）——三表 19 行全部改为 `[Qn·答案待注入]`/`[Qn·规则待派生]` 占位符，装机注入按 step5 5d-1 逐格替换；verify §4.7「模板纯净」判据在位（ROWS=19 BAD=0）。同步根治 SHADOW 模板 `author` 字段作者署名（→`用户`·v4.2）。**注意：V2.2.0 及更早的包内模板带作者画像数据，请勿再分发。**
- Fixed：安装器 `_fill_text` 扩 `[日记仓库]`/`[知识库]`/`[日记子目录]` 三占位符（括号+花括号双形态·从 step3-done 读变量）——旧版只换 `[记忆共享中心]`，技能 .py 残留 16 处字面量致日记采集/成就追踪路径错；step6 文档 glob 补 `.py`。
- Fixed：断章增量「裸拷良性本地化」——用户盘规则文件若为 5d-8 裸拷（占位符未本地化），安装器就地填充不判冲突（根治「字节相同也报已被用户修改」假冲突·10-14 D3 复发线）。
- Fixed：记忆琥珀 fswatch wrapper MC 行改脚本自定位（`$(dirname)/../..` 三级上跳）+ plist 补传 `AMBER_MC` 环境变量 + step6.5b sed 防呆——旧版装机后 launchd 崩溃循环（幽灵路径双杀）。
- Fixed：verify 软链检查假阴性（端声明支持软链但 skills/ 缺失 ⇒ 判红不跳过）；verify 摘要版注入检查 `grep -c` 双零 bug；自定义指令缺失 FAIL 补「预期态·粘贴后即消」说明。
- Fixed：体检报告「用户身份」加安装完成标记判据（`.install/version`）——旧判据把走完 step5 的在装新用户误报「老用户」。
- Fixed：`--list` 只读查询跳过平台判定（多端机不再被拒）且不再误打 50 行自定义指令喊话；WB 分支误导文案更正。
- Fixed：Windows 编码防护——win-verify.ps1 21 处、verify.ps1/amber-watch/amber-install-dualtrack/systemlog-watch 各 1 处文件 IO 补 `-Encoding UTF8`（GBK 控制台读 UTF-8 log 乱码）；8 个 Python 脚本（计分器/同步检查/知识引擎等）补 `sys.stdout.reconfigure(encoding='utf-8')`（cp1252 控制台 print 非 ASCII 崩溃）。
- Fixed：文档计数全面对齐实盘——钩子 19→38（事件分布 9/23/5/1）、「有意不激活」表纠错（7 列 6 件实际在 ROSTER）、脚本中心 65→287、洞察模板占位符正则改中文命名兼容（191 个）。
- Fixed：smoke 测试脚本自身 6 处过期/断判据（Skill 9→10、步骤 9→12、执行文件期望改现行架构、平台一致性段改多端判据、validate sed 环境免疫、§10 运行时引用语义分流）。
- Added：包根 `LICENSE`（MIT·此前缺失）。
- Changed：step5 5d-7/5d-8 补占位符替换硬指令；6.5g 触发测试改打白名单内 CORE.md（旧命令打不存在的核心层/SOUL.md 建出 stray 文件）；checkup 顶层散件判定排除装机自带 README；wrapper PATHS 补 good-good-study、去作者侧 QClaw记忆、debounce 锁按 MC 哈希；7c manifest 移除无步骤创建的 MC/README.md。

## [2.2.0] — 2026-10-17（布洛陀修包线全线·36+2 卡·模型安装方案定稿）

- Fixed：`references/scripts/verify_skill_version.py` 升 v0.2——版本对平闸形态域同步（只认 `### v` 顶标题致 sucair/system-logger/triwich 三件账一致被误判 MISMATCH·随包分发会在端用户 verify 链撞同款假红）；扩形三处+负例自测 5/5（真漂移仍抓红·⛔扩形洗红）；内置 --selftest。

### 修包线主线 36 卡（2026-10-14→15 · Qoder CN 串行施工 · 逐卡验收原始输出在任务卡集）
- P0 十卡＋P1 十五卡＋P2 十一卡：门禁链路（todo_landing/cleanliness/privacy/manifest 四件套每轮裸跑 rc 直判）、派生投影（blessed 覆盖+sha 核对）、盲审随包、摘要版填充豁免（注入豁免判据逐段重建匹配）等。

### 模型安装三形态路径 + 文案定稿（2026-10-16/17 · 用户逐轮审稿）
- 新增引擎工具 `scripts/semantic_upgrade.py`（Phase C 语义升级五步链：母体检查→依赖→本机 int8 量化→向量库重建→真机自验探针；产物驱动生效/失败自动回滚 base 态）＋ `quantize_export.py --quant-dir` 参数化（C38）。
- INSTALL Phase C 升级三岔口（只装 Base／只装 Large 压缩版／双模型两岗·推荐；都不装=纯 BM25 显式降级零静默）；模型安装文案终稿全文入 Phase C1 展示节＋手册新增「16 / 检索模型」HTML 节（note 卡+details 折叠）。
- 混合检索如实披露：BM25（常在线上）＋语义向量（模型点亮）两腿融合；BAAI BGE 开源署名+MIT；安装包不携带任何模型（体积+意愿双设计）。

### 发版轮门禁批修（2026-10-17 · 13 项 FAIL→全绿）
- relocate 占位化规则根治：`Path.home()/"个人AI档案"` 类产物保 `Path()` 壳（旧形在 pathlib 除法上下文产 str/str 运行时炸雷）；包内同型雷全网清零（session_tail 源形 MC_ROOT 锚定＋drift/skills/ggs 九处）；mirror-sync 投影后挂 py_compile 语法闸（能力边界如实注）。
- manifest 搬家断链重指 15 处；运行残料（.cache/*_tmp/pycache）出包＋mirror-sync/cleanliness 双源 class 排除；包内私人称谓残留清零；铁律版发布源（curated）description 与正文 v8.37 自洽对齐；README 端名册「适配 **8 端**」口径行；检查⑪两项降级声明（ggs 挖掘器/card-schema 审计器=发布者工具未随包分发·设计内显形）。
- C37：mirror-sync 源脏跳件闸（`_src_dirty` porcelain 文件级+目录??前缀+仓级缓存+dry-run 亦显形）＋ --self-test 六例夹具＋变异体证牙。
- WB 端自定义指令喊话补《布洛陀手册》指引（4+1 协议：四文件直装+第五件设置框粘贴·installer 无 field 写方=实况）。

### 已知边界
- Windows 真机腿由 LOOP 环节承接（用户裁定）；int8 画质税≈0 系 fp16/int8 21 题对照 v6 结案；引擎 KB_MODEL 既有接口未动（C38 只做工具链）。

## [2.1.3] — 2026-10-10（暂存态·随下次出包带走）


- **术语换面（2026-10-14 · Qoder CN · 皮叔定）**：用户面旅程术语「点火」全系换「入职」（M7 入职／两步入职／入职播报），理由：点火系引擎机械隐喻用户无感，且"上岗"一词已专属 D3 模式不可混用；历史行「点火」留原样（append-only），以本条为术语分界锚。
### 上岗机制泛化三件脱敏入包（2026-10-12 · Qoder CN · 作者令「要脱敏入包」）
- 新增 `references/digital-twin/devtools/doenglingz_skill_onduty_tier_promote.py` v2.0.1（事件腿钩子·源侧转正端中立：LOG/SKILL_ROOTS/src 全 config 根派生·`--self-test` 5/5·挂载指引=12协议§2.2.1）＋`doenglingz_skill_head_watch.py` v1.0.2（首行令投影守卫·双向夹具·无参=自愈跑）——manifest 纳管 816 条目（263→…→814→816 链上＋2）
- `references/skills/{good-good-study,system-logger,clock-loop,daily-buddy}/SKILL.md` 随源刷至 1.1.9/3.17.2/4.17.12/3.51.2（frontmatter `requires_twin_on_duty: true`＋投影上岗块入包面·mirror-sync --only 定向强刷·反向校验源≡包 0 差异）
- 端用户效果：装包后启动四件＋growth-box＝事件腿自动升 D3（各端 setup 接线为后续项，指引已 12协议§2.2.1）；未装腿端义务链不受影响（06 执行腿判据＋四态表显形）
- 真机项挂账：装机沙箱 e2e（Mac/Win）随下次发布跑，本轮为文件入包+静态门（contamination/manifest check）——⛔不宣称装机验证（发版链须含跨平台真机律·诚实分段）
- `references/digital-twin/devtools/card_mechanism_anchor_audit.py` 随包入位（2026-10-13 · Qoder CN · package_integrity 腿F 显形修复）：good-good-study `references/card-schema.md:232` 把该件声明为 mechanism_anchors 的消费端，而包内/部署面皆无 ⇒ 端用户照模板执行必落空。入包前审查：真源 `开发工具/`、`H=os.path.expanduser("~")` 派生、无写死绝对路径、自测夹具仅写 tempfile。mirror-sync 走 deident_only 投影。
- ⚠️ 同轮显形（2026-10-13）：本小节 #1 件（tier_promote 事件腿钩子）在包但各端 setup 接线未做，被 package_integrity_check 腿B 判「五通道皆无·尸体」⇒ 已登记 baseline legB 存量（9/1/0/0/0/0），口径=**已裁定挂账**非缺陷涂绿。更正（同轮·15:32）：本端 settings.json **实挂**该事件腿（PreToolUse matcher=Skill → hooks/skill_onduty_tier_promote.py，inject_state 另见 mode=skill_event 的 d_tier=D3 行双证），前句「作者端零挂载」系 grep 结果被 head 截断致误判，作废。故未写 capability.yaml 声明的真实理由=「端用户默认启用自动升 D3」属发布行为决策未定＋跨平台真机项未跑（条文「Mac 绿≠可发布」），非作者端未启用。真机项仍随下次出包跑，本条不宣称装机验证。

### 装机态运行落点自举 + batch_auto_pass 除零根治（2026-10-13 · Qoder CN ·「封包不留隐患·启动根治」令）
> 判据=包宪法命题一「端用户侧设施可达性」+ 命题二「防误>防错（设计端，非文档提醒）」+ 硬边界①「幂等·存量保护」。
> 缘起：按「评估」 2.1.x 安装包两处「未装配」是否对新装机用户构成隐患。按**活包 V2.1.3**（非陈旧 2.1.0 快照）逐脚本读 exit 绑定重查。
- **真隐患（新装机必崩·已根治）**：`job_probation_check.py` 缺 `job_probation_ledger.json`→`exit(1)`；`record` 缺岗位定义→`exit(1)`；`batch_auto_pass.py` 缺 `数字分身/steps/step3-first-review-log.md`→`exit(1)`；`job_audit_check.py` 缺台账→`exit(2)`。这三件是 JOB-001/003/004 三岗位（good-good-study+growth-box 共用）的运行落点，作者端有、包不建 ⇒ 端用户装完 A 线预筛首跑即崩。
- **根治=设计端幂等自举**：`install_scripts.py` 新增 `bootstrap_runtime_state(mc,dry)`，`deploy_digital_twin` 后主流程调用（`①a+ 运行落点自举`）。缺才建空骨架（三岗位 probation 起步·零决策；初审台账 0 态表头），**已存在绝不覆盖**（存量机用户数据保护·幂等）。⛔ 补的是空骨架非历史数据，与「不补造岗位台账」纪律正交。
- **附带根治既存潜伏雷**：`batch_auto_pass.py:111` `total=0` 时 `auto_pass/total*100` `ZeroDivisionError`——任何全新用户 0 卡跑 A 线必崩（与台账缺失独立的第二类崩溃）。加 `if total else N/A` 守护，**同步修真源(脚本中心)+包内 4 副本**（防 mirror-sync 回灌）。
- **P2 概念碰撞成就：核实为「已在包·非缺失」**（纠错·实事求是）：首版误判源自陈旧 2.1.0 快照。活包 2.1.3 内 `references/成就系统/概念碰撞成就.md` 由 `com.qclaw.mirror-sync` 从作者端实时镜像在位（含 STATE/LOG/SEAL 标记），端用户 cp-r 即得；实测真实发货件对新用户（INDEX 不存在）`check_concept_achievement.py` `exit=0`、Y 重算为 0 不崩。与同级 `阅读成就.md` 携作者基线数（"9本"）为既定「模板含基线·端用户首跑 tracker 重算覆盖」约定，**无动作**（⛔不对抗镜像、不破坏原设计）。
- **验证口径（诚实分段·不宣称装机验证）**：Mac 隔离 temp MC 全流程实跑（拷脚本+占位符本地化+bootstrap+4 脚本 record/audit/batch/check_concept）全 `exit=0`；幂等复跑全 `skipped` 不覆盖；负控（删台账后 record `exit=1`）证修复确有作用。真机 Mac/Win 装机 e2e 随封包 Loop 复跑（条文「Mac 绿≠可发布」）。
- **成就 md 出包脱敏（2026-10-13 · Qoder CN · 隐私红线·「必须脱敏·包内不含个人数据」令）**：`mirror-sync.py._normalize_runtime_ledger` 新增 `_reset_achievement_md` 分支，对 `references/成就系统/*.md` 出包时把成就**个人数据区**重置为骨架——概念碰撞 STATE/LOG 块归零清空、当前进度粗体指标行→未追踪、里程碑 `✅已完成`→⏳、达成日期单元格→`-`、《书名/专名》→《待填写》、`差N本`进度提示→清、`最后更新`时间戳→待首跑、frontmatter 作者日期→占位。里程碑**定义表**(阈值/名称/条件)属规格不动。**落点在镜像投影层（写盘+一致性双端同链）→每次 fswatch 重跑自动生效、扛回灌**（实测：源仍 Y=144，包恒 Y=0，二次同步「更新 0 文件」幂等，隐私门禁 A7 通过）。作者源保留真数据不变。
- **遗留观察（交封包定夺·非本轮涂绿）**：镜像入包的成就 .md 携本机基线数值（Y=144/历史里程碑 LOG），新用户首跑前会短暂显基线、后由 check_concept 重算覆盖 STATE 但不清 LOG——与全部同级成就同态，是否需在发布脱敏层洗成就 .md 属发布决策，未擅动。

### 成就隐私双根治：A7门禁补成就域 + 装机存量精准清洗（2026-10-13 · Qoder CN ·「只清我不清用户·发布门禁必须根治」令）
> 判据=隐私红线(G2④)+包宪法命题二防误>防错。承上轮 mirror 出包脱敏·本轮补两层。
- **任务B 发布门禁根治(假闸→真闸)**：`release_privacy_guard.py`(A7 出包后置隐私门禁·真源=脚本中心)的 PERSONAL_DIRS 原**不含成就系统**→带皮叔成就数据仍 RED=0 假绿(2026-10-05 起失明)。新增成就专项扫描:只对「成就系统」目录段下 `*成就.md` 跑内容判据(《非占位书名》/✅已完成/已填达成日期)·⛔不用同指纹(骨架与作者字节同会假阳)·⛔不误伤 成就系统设计哲学.md(非该目录段)。自测扩至 **9/9**(T8净骨架不误报/T9脏成就必红)·负控注入伪书名→RED=1 阻断。根治上轮「reset 模板自指」假闸——封包现会因成就带个人信息物理拦下。
- **任务A 装机存量精准清洗(只清我不清用户)**：历史包(备份版/存档包)曾随包带出皮叔成就数据(书名/✅已完成/达成日期/概念LOG)残留用户机。`data_contamination_check.py`(装期跑·包根内嵌免被prune·⛔不并入TARGETS=2026-10-03 no-op根治)新增 `ACHIEVE_LEGACY_HASHES`(26条皮叔确切泄露行不可逆SHA256行哈希)+`scrub_achievement_legacy`:装机 --apply 删哈希==该行·用户自录行内容不同→哈希不同→数学零误删·生产机闸(皮叔机 --apply 被拒·护真成就)。
- **验证(诚实分段)**：Mac 隔离模拟用户机全流程=皮叔行删净·用户自录行(虽同含"✅已完成"整行哈希不同)完整保留·无 traceback(重跑完整stdout才现形一处 `%s %d` 少喂参 TypeError·grep过滤曾掩盖·实事求是入账)；皮叔真机 dry-run 命中5/--apply 双闸拒·md5未变。真机 Mac/Win e2e 随封包 Loop。
- **挂账(非功能洞)**：release_privacy_guard 包内下游副本(references/scripts+hooks·334版无成就扫描)未同步·A7 实跑真源已修故封包门禁有效·下游同步留后续。

### Skill 面程序化部署腿 + L4 真机取证腿（端用户补充单 T16/D1 根治·批次8）
- `install_scripts.py --deploy-skills`：逐件复制 + 占位符本地化（含 `.ps1/.plist/.template`/无扩展名）、覆盖前逐件 md5 比对生成 `<MC>/.install/upgrade-losses.md` 并备份进 `<MC>/记忆琥珀/升级前备份_<ts>/`、幂等跳过。沙盒真跑证据：首跑 313 件落位／残留 0；二跑幂等 312＋待覆盖 1＋损失清单在盘。
- `step6-skill-install.md` 与 `INSTALL.md` 主路径改指该腿（手工 `cp -r`+perl 降为兜底说明），承条文20 三层同权——⛔文档教第二条写法。
- 跨平台四腿 L1-L4 上线（派生配对/stdin 编码/路径形态/真机运行性）；`rollback.ps1` 补 UTF-8 BOM 一处根因消解真机 5 项红；`_hook_command` 在 Windows 优先选同名 `.ps1` 承载（⛔"有 Git Bash 就能跑 bash"式推断，step6 明文禁止）。真机进度：PASS 26→31／FAIL 9→4。
- 沉淀：01规范新立「跨平台单包对等律」条文；LOOP `pkg-checkup.md` Step B1.5g 扩写取证腿四自证律；成长箱 QCN-20261011-005/006/007 + 新立 PAT-092。


### 批次3 · 跨平台对等三腿入尺（端用户补充单 11 项 → 门禁化）
> 缘起：端用户第二份实测单 + 作者令「按符合愿景的最优解推进」。判据主轴=**派生式胜过手写清单**（愿景①机制不依赖人记得）。
- **L1 跨平台脚本配对·派生式**：`platform_compat.check_script_pairing_derived` 取代手写 PAIRS 清单（旧判据只列几对，清单外 135 件 .sh 结构性失明报绿）。新判据＝目录扫描派生 + `references/platform-exemptions.json` 豁免册（reason/basis 必填，⛔空壳豁免/整目录豁免）。首跑显形 119 候选 → 有据豁免 48（件内实测引用 launchd/plist/osascript/fswatch）·**真缺口 71**（无 ps1 亦无 mac 依据，保持报红，清单落 `data/win_pairing_gaps_20261010.md`）。
- **L2 stdin 编码对等**：新抓「读 stdin 却未设 UTF-8」的件——端用户报 1 件（标题钩子中文乱码），实测 **65 件**。源侧逐件插入 `if hasattr(sys.stdin,"reconfigure"): ...` 守护（⛔直接调＝部分宿主 stdin 非 TextIOWrapper 会崩），逐件 py_compile 断言 + 改前备份；投影后包内命中 **65→0**。
- **L3 占位符路径形态卫生**：双拼畸形（家目录符号+盘符）零容忍 + 「家目录符号紧跟占位符」形态存量棘轮基线（⛔自动下调，人工 CLI 才改）。首跑 5 处命中经逐行复核**全是注释里的病历描述**＝门禁词自伤（条文18⑥ 同族）→ 判据已收窄到代码行字符串字面量，现命中 0。
- **配套收编**：`session_title_namer`/`qodercn_title_namer`/`wbai_title_namer`/`zcode_title_namer`/`tsl_tree_hook`/`kb_inject_prompt` 等 26 件守护随 mirror-sync 落包；无主副本补登记 15 条（含 5 件三目录落版需人判→定向强刷归零，同步 803 条目/更新 78 文件）。
- **自我纠偏入账**：本轮我四次踩同一族——插桩落在文件头 docstring 内致检查器**零输出 rc=0 假绿**、从 `main()` 被截断的前 10 条输出反推待治清单（致只治 10/65 件、并误判尺子失效）、长 heredoc 挂死、逐个补登记打地鼠。均入成长箱（详见 QCN-20261010 系列）。
- **如实未竟**：#2 注入钩子容错对称、#5 骨架模板生成器补「上岗身份声明全文」行、#4/#8 INSTALL 文档段、#10 分身名变量化评估、smoke_test 6 项（版本轴/rollback 标签等预存红）→ 留任务卡批次4。


### 双拼畸形路径根治·`~/` 前缀紧贴占位符（十一轮·2026-10-10 皮叔令「Mac/Win 全端用户正常安装使用」）
> 缘起：官方模板占位符带 `~/` 前缀（V1.6 仅 1 处注释孤例 → V2.1.0 实测 628 处扩散），安装器纯 replace 生成 `~` 斜杠双拼绝对路径/盘符形态 ⇒ 钩子/脚本路径引用全部 Fail-Silent。qodercn 适配面 0 处带前缀——定性 bug，非多端共享设计。
- **根因链**：deident 规则1 先把作者绝对路径 tilde 化，relocate 五形态族（`_FORMS`/`_ARCHIVE_ROOT_FORMS`/`_SUFFIX_FORMS`/`_DT_FORMS`/`_AILIB_FORMS`）只有运行时展开的绝对路径形态、缺 tilde 字面量形态 ⇒ 落裸形态规则只换 `個人AIアーカイブ/` 段、`~/` 前缀残留；`_PY_CTX` 注释声称末尾有幂等清理、代码缺失（注释与实盘不符）。
- **根治**：①五形态族补 tilde 字面量（治本）②relocate() 收尾幂等正则兜底（防御纵深）③安装器 `_fill_text`/`_fill` 加 TILDE_PREFIXED 归一化（已发布旧包重装即治愈）④deident() 收尾同款清洗（覆盖 templates/rules/adapters 的 deident_only 管辖面）。
- **存量重刷**：mirror 预检拦路根治——REPAIR_TOKENS 登记表过期纠偏（V9 构建链标记）、manifest feedback-detect 锚点归位 DEV 根、devtools 落点无主副本补登 6 件（distillation/position3/auto_pass/error_candidate/pkg_cleanliness/validate_buluotuo 三目录同源）；包自有层 11 文件持锁直洗。包内畸形前缀 627→**0**。
- **门禁防复发**：pkg_cleanliness_check.py 新增畸形前缀判据（chr 免疫构造·发布卫生闸 phase5 自动生效）；新增 path_integrity_check.py v2（运行时调用形判据+行级 PATH-INTEGRITY-EXEMPT 豁免+--pkg-template 模板模式·真源=开发工具）；verify.sh/verify.ps1 新增 §4.5 装后双拼扫描（双端同口径）。
- **附带根治**：register_hooks 新钩子分支 `want` 未定义 ⇒ 全新机首装必崩（UnboundLocalError 实证·装机面阻断缺陷），上提公共前段。
- **验证**：Mac 隔离装机实证（假 HOME+/tmp MC）——装机 rc=0／38 钩子 py+sh 冒烟全过／装后 MC 面+hooks 面路径完整性双 PASS／发布卫生闸✅全链五步绿。Win 真机按皮叔裁决交 clock-loop Loop 上 GitHub windows-latest 复跑。

### hexaco 测评件收敛+ZCode 文案工具无关化+防回流断言（隐私红线回归根治轮·2026-10-10 皮叔令）
> 缘起：皮叔令评估发布包 `references/digital-twin/hexaco/` 版本堆积。实盘 10 件 vs 9-29 脱敏声称终态 6 件——作者侧运营件（互照套件×3+探针题库）带"皮叔→你"机械替换回流进包：探针题库含本体读数 H·Fairness 4.75=脱敏红线明文清理项回归；互照提示词首句"你现在是童灵"，端用户照跑会装配**作者的分身**（身份劫持级）。装机链仅取 4 件，其余 6 件在包内零引用（60简版/runner=三悬空半制品）。
- **收敛终态=装机五件**（包内文件必须存在部署路径的零悬空判据）：答题页×2+题库+100答题卡+**ScoringKeys_100.pdf（新入包·闭合"AI 计分"链断点**——原答题卡引用计分键 PDF 未随包，用户答完无处计分）。移出 6 件→`数字分身/HEXACO测评/包内移出-20261010/`（cp+diff=0 后 mv，非 rm）；作者侧真源不动。口径变更：9-29"终态6件"废止，代之以"终态=装机白名单"单一真相。
- **ZCode 文案**：答题卡 L115+HTML 答题页 L60"交回/发给 ZCode"改"复制粘贴给当前工具的 AI"（皮叔 2026-10-10 定：ZCode 系作者习惯指称，端用户无此物=死引用）；**包侧+作者侧双侧同改**（防下次同步回退，改后双侧逐字同款）。全包其余 ZCode 命中均属 zcode 端（官方适配端名）合法语境，不动。
- **install_scripts.py**：hexaco 部署元组+注释同步五件口径。
- **同日裁定+补修（2026-10-10 皮叔）**：①60题版**裁决不入包**（挂账销）；②自建答题页 L53「整段粘贴给 WorkBuddy」属 ZCode 同病工具锚定，双侧补改为「整段粘贴给当前工具的 AI」——残留判据从词表扩为「任何具体工具名锚定」。
- **防回流断言**：verify.sh §3.8 / verify.ps1 同口径新增 hexaco 终态穷举检查（白名单外文件出现=红+点名；缺 PDF=红），承接 2026-10-03 指纹池清空后 hexaco 域缺失的机械载体。
- **验证**：替换/插入全锚点 assert count==1；bash -n 语法过；py_compile 过；移出后包内 hexaco 终态 ls 复核=5 件。备份=记忆琥珀/hexaco-converge-bak-20261010-qodercn/（包侧10件全量+作者侧2件改前态）。


### 接收完整性前置门（外部 S0 误报根治轮·文档层）
> 缘起：2026-10-09 外部 S0 体检对 V2.1.0 发版包出具"skills×10/digital-twin/知识联邦/templates/记忆蓝图均不存在"结论。本机实盘对账：官方 zip（sha256 OK·1424 条目）与 GitHub 仓库（1420 blob）五组件全在——诊断为**半包/编码致盲类接收缺陷**（夸克散文件通道断点下载可产出"根文件齐+references 子集"形态；本工作区 2026-10-09 探针副本即此形态实例）。包本体无缺陷，CHANGELOG 11 处 E2E 未实测为如实声明另计。
- **INSTALL.md**：新增 §Step -2 接收完整性前置门（zip→sha256 先验；散文件/clone→verify.sh 或 references/ 目录目测；不过=不进安装）+ 解压工具乱码提示（UTF-8 flag 全带·Win7/老WinRAR 换 Bandizip）。
- **README.md**：顶部块后加"拿到包第一步"一行指针（详规不双写，落点=INSTALL §Step -2）。
- **验证**：三处替换 assert count==1；备份=记忆琥珀/接收前置门-bak-20261010-qodercn/；纯文档增量零行为变更。
- **配套运营动作（不随包·皮叔侧）**：夸克通道后续改传 zip+sha256（与本目录 _release/ 产物形态对齐），散文件直传退役。

### 腿F案：Skill 指令面承诺资产补收（sync_collision_queue 七件套·判据面根治轮）
> 缘起：皮叔 2026-10-10 令评估「good-good-study 引用 sync_collision_queue.py 但包没带」。实盘对账：包内 SKILL.md/references 指令面共引用 7 件碰撞闭环脚本未随包（sync_collision_queue/lint_collision_card/concept_projection/scan_card_citations/cross_type_collision_scan/scan_citation_candidates/concept_coverage_stats）；深挖根因=配套完整性检查器五腿对「Skill 文档执行指令面」结构性失明（腿A 只扫运行时码内引用、腿C 只扫 INSTALL.md、腿D 只认数字分身前缀）——文档承诺与资产分离出厂而门禁全绿。
- **资产面**：7 件端用户版入 `references/知识联邦引擎-min/scripts/`（9→16 件·路径收口 _paths 零硬编码·未安装态优雅跳过）；`install_scripts.py` 静态计数"9 件"改目录实盘动态取值（防再漂移）。
- **判据面**：`package_integrity_check.py` v2.4→v2.6 新增**腿F**（skills/**.md 命令形态/部署路径形态点名件须包内∪部署面可达；CHANGELOG/ROADMAP 历史台账不入契约·v2.2 同口径）；v2.6.1 自纠两处判据缺陷（降级只判行→±4 行窗口同腿A·占位反例名 xxx.py 降噪闸）。工具落点=开发工具/buluotuo-release-sync/（不随包）。
- **双向验证**：负例=修复前包快照腿F 抓到 5/7 红（另 2 件被包内旧降级声明"安装包不携带该目录"豁免——该声明与实盘已不符，登记欠账待皮叔裁决文档修正）；正例=修复后当前包腿F 全绿；端用户态 fixture 冒烟 14 项断言全绿（含 collision_scan 焊闸 import 可达、暂存态不污染）。
- **验证**：11 处替换 assert count==1；py_compile 全过；快照/施工/fixture 三件留存 qoder-cn-work/steps/pkgfix-20261010/。
- **裁决落地补记（同日）**：collision-consumption.md 三处旧「不携带该目录」降级声明按实盘改写（源侧改+`mirror-sync --only skills-bulk-good-good-study --force` 链路重投影·⛔包内手改白改·承条文 44 治本顺序律）；「文档承诺与资产实盘一致」升格为哲学条文 57（01 规范 v1.83→1.84·教训库 L53）。

### 存量清账轮（腿F带出的两类旧账·皮叔令「符合愿景彻底根治」）
> 缘起：2.1.3 腿F案收口时显形两笔旧账——①包内三目录同名审计「⛔需人判 1」（rule_fragment_eval.py 三副本互异且≠锚点）②package_integrity_check 腿A 存量 11+新增 3 全为守卫自测夹具假名（同一条账每轮守卫改动都手工记一遍）。
- **账1·三目录漂移清账**：核实 037 冲突语料块与真源逐字相同（他轮包侧动作为已入锚点的重复劳动，零丢失）；`mirror-sync --only` 定向投影归一 rule_fragment_eval 三副本＋auto_pass_audit/error_candidate_miner/validate_buluotuo_skill/guard_selftest_check 落版（取证：被覆盖件 HEAD 与工作树差异均为锚点已提交内容的正常追平，⛔未吞他端未提交增量）；manifest 补登 hooks/dt-devtools 两落点 single_file（条文 52 同族先例 2.1.2 修法·src=本机真源）。audit 终态：需人判由 rule_fragment_eval 清零。
- **账1·挂账显形（不代治）**：新显形 1 件 `transcript_reader.py`＝他轮包侧 uncommitted 真增量（iter_messages_with_ts·PAT-087 根治轮），⛔投影会吞——挂账待该轮自收口；`match_coverage_check.py` 同挂（growth-box v4.4.11 轮活面，腿F 抓到其在册 SKILL.md 点名但脚本未入包——由该轮定入包或豁免，已计 baseline 存量不静默）。
- **账2·legA 夹具闸（v2.6→v2.7）**：package_integrity_check 新增 FIXTURE_SINK 物理判据（引用行本身＝写汇调用 `.write(`/`write(`/`write_text(`/`writerow(` ⇒ 行内 .py 名是被当场生成的自测夹具非部署承诺），fixture_exempt 留痕显形（与腿E 生成型豁免同模式）；双向变异实测：subprocess 真引用注入→红 ✓ write 夹具注入→豁免 ✓ **闸非恒真**。dict 假路径形 8 件（guard_index_pointer 等）**不扩判据防漏斗**，维持 baseline 人账。baseline 重算 11+3→8（写汇形 5 件退账），integrity 终态 rc=0（新增 0/0/0/0/0/0）。
- **验证**：负例快照复跑 legF 5 红与 15:05 记录一致（判据稳定）；integrity/audit 终态见上；施工件留存 qoder-cn-work/steps/pkgfix-20261010/。

### 双挂账根治轮（transcript_reader + match_coverage_check·皮叔令「帮我根治处理」）
> 缘起：存量清账轮挂账显形的两笔，经皮叔授权本轮根治。两案同构=承诺与资产错位，分型施治。
- **案1 transcript_reader.py**：取证显形真源（开发工具/脚本中心双实体）**早已含** iter_messages_with_ts 增量——他轮真源已提交、唯包侧投影忘跑（包侧 M 与真源逐字同＝重复劳动，非真权冲突），零丢失回滚+补登 hooks/dt-devtools 两落点+三副本 --force 投影归一。施治自查一处自伤并当场修复：首轮 --only 漏跑 scripts 落点反而加深三副本不齐（audit 需人判 1→2），补跑后归零。
- **案2 match_coverage_check.py + match_coverage_baseline.json**：growth-box SKILL.md 第10步机械终检点名件此前未入包（legF baseline 在册存量=第二笔活账）——脚本+存量豁免账两件经 manifest 补登记入 references/scripts（装至 <MC>/脚本中心/ 与 <MC>/记忆规则/），install_scripts RULE_DATA 扩列 baseline（复用 2026-10-09 外部维护声明保护语义，⛔不静默覆盖用户账）；投影形态抽查 `expanduser("[记忆共享中心]")` 由装机 _fill 展开（与包内占位符设计一致）；作者侧真源 --self-test 6/6 过（含 fail-closed 案例 rc=2 实证）。
- **连带根治（九头蛇第三显形）**：audit 终账浮现 guard_selftest_check.py 三副本停 v0.2.5/v0.3.1≠锚点 v0.3.2（已提交干净）——同病形补登两落点+三落点全投影，三副本齐 v0.3.2。
- **终态**：pkg_conflict_audit 需人判 **0**（同源等价 269/可定序 3/需人判 0）；package_integrity rc=**0**（新增 0/0/0/0/0/0·baseline 重算后 legF 存量退账）；包锁 acquire→commit→release 闭环。

## [2.1.2] — 2026-10-09

### 同名三目录落版冲突根治（童灵轮·承安装包设计哲学条文 52 互锁律）
> 缘起：端用户 strict 安装门禁（`_BLUOLUO_PKG_CONFLICT_STRICT`）中止——`host_identity_hook.sh` 与 `kb_inject_prompt.py` 在 `references/{hooks,scripts,digital-twin/devtools}` 三目录各一份应同源，manifest 仅登记 hooks/scripts 两落点、漏登 dtdevtools ⇒ 三目录机械复制出分叉版本 ⇒ 6 副本内容不一致 ⇒ strict 硬门禁（条文 52-①）直接中止安装。
- **根因**：mirror-manifest.json 对同名文件的三目录落点未全量登记 single_file entry（仅 2/3 落点有锚点）→ 漏登落点走"机械复制"而非"投影源"分支 → 分叉。
- **根治**：补登全部落点 single_file entry（hooks/scripts/dtdevtools 三处同源派生指向同一锚点：`host_identity_hook.sh`←`~/个人AI档案/脚本中心/host_identity_hook.sh`、`kb_inject_prompt.py`←`~/个人AI档案/开发工具/知识联邦引擎/scripts/kb_inject_prompt.py`），manifest entries 309→313；`mirror-sync --force` 重投影。
- **判据假阴性纠偏**：上轮 `verify_pkg.py` 仅 `deident` 不 `relocate`（锚点仍 `~/个人AI档案/` vs 包内 `[记忆共享中心]/`）→ 哈希天然不等 → 误报「sync 假绿未落锚点」。验证「源≡包」须套与写入端对称全变换链（deident→relocate→build_strips→console_guard→normalize）；复用 sync 自身 `_file_identical` 复验方得真绿。
- **验证**：经 sync 自身变换链复验 6 副本 `MATCH=True`（`kb_inject_prompt.py` 3 副本哈希均 `95ff08055d9b`、`host_identity_hook.sh` 3 副本均 `db508d57dda9`，组数=1）；`pkg_conflict_audit` 需人判=0 放行。关联：01规范条文 52 新增 2026-10-09 实证回流段、脚本哲学 v1.0.9 两模式回流、安装包设计哲学 CHANGELOG v1.3.120。


## [2.1.1] — 2026-10-09

### 上游反馈四缺陷根治（D3 童灵轮·立法「本机端=唯一主源，安装包=下游映射」）
> 缘起：端用户 Windows/WorkBuddy 端 2.1.0 全量升级 r2 实战反馈 4 条缺陷（本地存档未发送），L3 双Agent逐条实盘核验判定 4/4 全为包侧真实问题；作者令「启动童灵彻底根治所有问题，本机端是唯一主源，安装包是下游映射，逻辑关系不能错」→ 本轮按该方向律根治。
- **缺陷①根治（断章引擎迁移洞·P0）**：install_scripts.py 新增 `_tielu_precheck`——铁律版**无标记段且已有铁律结构**时，追加前逐条比对（同号等值/换号等价/同号异文/上游新增），非全等价 ⇒ 新状态 `PRECHECK_SKIP` ⛔不写盘、打印「号位冲突预检表」显形（C7 报告不裁决同构）。根治 C5「已存在且无段⇒盲追加文末」导致的整file双份（影响面=**所有**从无标记段旧包升级的用户，不止号位错开者·L3 评估修正）；上游新增条目归主源侧裁决，⛔不自动追加到本机上界之后（否决反馈建议2·防反向污染号位空间）。
- **缺陷②根治（yaml 幂等覆盖冲手工真源·P0）**：install_rule_data 覆盖前查目标文件头（前8行）外部维护声明——「本机不引入 / 手工维护+⛔」命中 ⇒ [SKIP] 保留用户版并告警；rule_triggers.yaml / rule_conflict_signals.yaml 入 conffiles 三路比较册（双保险）。
- **缺陷③根治（改名无迁移·P1）**：安装器双名并存显形告警（详解存档.md 旧名与详解存档版.md 权威名同在 ⇒ 提示先并入再归档 记忆琥珀，不静默）；rule_three_layer_guard.py 新增 ⑦ d7_dual_name 巡查（告警不进 drift）；同族工具侧根治 rules-strip.py 输入跟权威名（旧名退役即 FileNotFoundError 实证）。
- **缺陷④根治（台账漂移·P2）**：component-versions.json 源侧归实（clock-loop 4.17.4/good-good-study 1.1.0/system_rules v8.29→v8.30/script_system 274→276/as_of 10-09）+ INSTALL 模板数字归实；**发现并如实声明**：包内件手改会被 mirror-reverse-guard 从源投回（改包必须走源=主源纪律的机械确认）→ 本轮全部经 assets 源侧+mirror-sync 通道落包。
- **主源侧连带清偿**：记忆规则 rule_triggers.yaml 重编译 31→35 条（v8.30 索引表跟上·⑥门禁绿）；本机详解存档旧名退役件归档 记忆琥珀/（d7 双名清零）；包内详解存档版模板经 rules-strip+mirror 同步至 v8.30。
- **验证**：变异夹具 10/10（T1 标准用户EQUIV不写/T2 端用户形态CONFLICT拦截且文件md5未动/T3 新装SAFE不误伤+有段复装走常规/T4 手工声明SKIP+标准流覆盖/T5 双名告警）·smoke_test P1-P7 全绿 0 缺陷·rule_three_layer_guard --self-test 11/11·py_compile 全过。回滚点：记忆琥珀/2.1.0四缺陷根治前备份-20261009/。
- **版本轴归位（作者 2026-10-09 裁定）**：顶段头废止 `[未发布]` 占位备注，根治轮全部内容直接挂 `[2.1.1]`；version.md/INSTALL/rollback×2/step7/component-versions 六宣称位随真源同步 2.1.1，《版本命名规范》§4.1 同步修订 v3.3（烟测 P4 顶段==version.md 判据自动兼容·0 缺陷）。


### Zwork 端（AutoClaw 新客户端·zwork 运行时）映射启动：M1 系统文件写入段对账吸收模式入文
> 缘起：作者令「读取安装包哲学文件，为映射到安装包做准备，先自查我们自身，再安装包每一个环节」（2026-10-08）→ 映射前双端自测+M1 适配评估+端实体吸收轮三轮完成，端实践文件《附录A参考实践-Zwork端适配记录.md》v0.1 已建于安装包设计哲学夹（作者侧），adapters/zwork/ 正式适配器待 config_root 定夺后建档。
- **平台托管型第四型入 M0 导航**：INSTALL.md 主线八段导航 M0 行端变形判据补「平台托管型端（zwork）＝无盘上配置根·判端走 Memory 面证据+问答判定兜底」——本端无 hooks/无插件/无 cron/无 settings.json/无 rules 注入目录，唯一机制级注入位=平台 Memory Run 级注入；探测链 config_root 枚举对本端天然零命中·⛔按「未适配」误判。
- **端分立铁律显形**：包内既有 `adapters/autoclaw/`＝**旧客户端**（`~/.openclaw-autoclaw`·OpenClaw gateway·🦞），与本端 Zwork（🧠）相互独立（作者 2026-09-24 声明）——⛔不共用其适配器/注册面/插件链；本机两配置根并存时探测双命中须 fail-loud 问询。adapters/zwork/ 建档前⛔跑缺省探测（必 HIT 旧客户端端）。
- **M1 对账吸收模式入文**：本端五系统文件等价物=端自有实体（条文48 原生成立）——SOUL.md v1.1（卡号硬化·上游=WB customPrompt 5.5 段 10-07 版）、K2 AGENTS.md v2.5（准则节补 5.5 段·自上游直取领先于旧客户端对齐基如实声明）、Memory 执行准则卡（要点双写·supersede 补⑤.5）；端是 SSOT 包是投影·⛔覆盖端实体，只补缺失段。M7 同理=已点火态对账（童灵第 19 端·K2 终态）⛔重复造芯。
- **边界如实（首轮）**：~~capability.yaml/setup.sh/verify 判据未建~~ → **同日 D3 童灵轮已建**（见下条）。
### Zwork 端 M2 立壳：adapters/zwork/ 三件套 + 验收链 zwork 形态四修（D3 童灵轮）
> 缘起：作者令「启动童灵，继续推进自检和安装包映射工作」——自检电池实跑（platform_adaptation_check --src zwork / verify.sh --platform zwork）暴露验收器对平台托管型端形态缺口，逐项根治。
- **adapters/zwork/ 三件套入包**：capability.yaml v0.1（平台托管型声明·config_root=~/Library/Application Support/AutoClaw-official·memory_inject/k2_marked_region/exec_fallback 三新键·system_file_paths 五件=端实体+platform:// 两态·hooks_surface 诚实空集+gaps 边界说明·twin_surface active 已点火态·missing_semantics 10 键全声明）+ setup.sh 对账器（撞端防线/端实体只读对账/K2-W2 核查·三段·DRY 支持·fail-loud）+ rules/execution-guidelines.md 通用版底稿（含 5.5 检索与卡号纪律段）。
- **platform_adaptation_check.py 兼容确认**：zwork 三面（A 五件 customPrompt 等价键/B hooks_surface 段/C twin_surface）补声明后适配度 100%·--gate 放行——零代码改动（判据已按段解析·端声明补齐即绿）。
- **verify.sh 四修（验收器形态扩容·条文34③同族）**：①§1.5 补 zwork 形态 D——platform:// 伪协议与 ~/ 绝对路径 ⛔ 按 config_root 相对路径拼检（判据面与落点面不相交·平台托管型必假红），改端实体+内容锚点核（SOUL=「把沉淀当资产」/AGENTS=标记对+端身份节/Memory 两面=MERGED 信任源）；②§1.6 补 zwork 形态 E——注册面=端实体锚点串集合（规格书 Doenglingz/标记对/K2 区段/core_slice），并修 hooks_surface 段在场性判据（delivered=[]+gaps 文本行原被误判「未声明」·fail-closed 只管段缺失不管条目形态）；③§3.5 hooks/rule 硬布局检查扩形态——settings_json:false ∧ (hooks_alternative:true ∨ memory_inject:true) 均跳过硬布局（zcode 类与 zwork 平台托管型同属非硬布局·⛔双判据打架）；④§1.6 zwork 分支先于 hermes 判（避免落进 else 的 zcode config.json 兜底）。
- **脱敏三件（pkg_cleanliness 报红根治）**：adapters/zwork/capability.yaml 与 CHANGELOG Zwork 条目口语称谓→「作者」+adapters/hermes/rules/core-soul.md 同款一行（该件为他端 WIP 持有中·脱敏行已落工作区·commit 归他端）。
- **M3-M5 对账轮（作者机）**：十 Skill 10/10（MC/技能配置）·记忆琥珀 3163 件/未知未知/最伟大的我/记忆蓝图/成就系统/知识联邦引擎全在·数字分身七件套全齐（scripts 73/devtools 17/guards 3/gates 5/k2-slice-generator 3/hexaco 4/onboarding 3）——M7 已点火态成立。M2 计数差 11 件全为出包范围外有主（bad_*/good_* 测试夹具/doubaowork·traework 端专属 tsl_verify/作者侧件）。
- **验证**：verify.sh --platform zwork **23 项全绿**·platform_adaptation_check --src zwork --gate 放行·setup.sh 沙盒 4/4（DRY 零写入/真跑/幂等/负例 EXIT=2）·load_capability 解析 10 语义键·他端回归抽查 0 红（zcode verify 0 FAIL·traework 100%）·bash -n 全过·脱敏 grep 归零。

### 账实对账加固：判据入链 + 全项修正
- **新增组件账实对账判据 P1-P7**（smoke_test.py 内置·Loop G 路径与发版链守卫自动执行）：组件版本双向对账/件数对账/INSTALL 模板数字/规则四件自洽/CHANGELOG 结构/端名册一致/单数路径防复发/琥珀覆盖保护。修复前 30 项缺陷全被机械复现，修复后 0 缺陷；自测用例 16+变异 5 全绿。
- **全项修正**：component-versions 归实（5 Skill+system_rules+分身套件计数）｜三层规则 v8.29（铁律-031 归位+索引补行+执行规范段头去重）｜本文件补 [2.0.0] 归档段｜README/INSTALL 端数统一 7 端+模板数字归实+亮牌指示补 notes｜rule_triggers 31 条重编译。
- **记忆琥珀升级（7.18.0-pkg）**：监听升级 whitelist 文件级（替代目录全树递归·扫描量与误触发骤降）；新增噪声排除（.log/.tmp/缓存不计变化）与变化明细日志；安装/升级时对更新版 amber-watch.ps1 自动跳过覆盖并提示（防覆盖用户机修复版）。
- **clock-loop v4.17.3**：G 路径账实判据入链记录（详见其 references/CHANGELOG.md）。

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

## [2.0.0] — 2026-10-01

> 归档说明（2026-10-08 补·loop 安装包账实轮）：本段收纳 2.0 线建设期（2026-09-22~10-06）
> 未带版本头的开发流水段；2.1.0（2026-10-07）为 2.0 线首个对外发布版。

### 分身养成链落地：答题→计分→蒸馏→上线 全链闭环（2026-09-30·发布者质证「100题答题在哪/蒸馏环节在哪」）

- **质证成立**：原「数字分身完整版单装」只闭环基础设施部署，用户数据生产链（答题→计分→向量→蒸馏→上线）零指引——部署闭环冒充全链闭环（WB-20260930-002·引 PAT-058）。
- **install_scripts.py**：DT_SUITE 新增 `hexaco` 部署项（答题页×2＋题库＋官方答题卡四件）→ 装机态 `[记忆共享中心]/数字分身/hexaco/`——养成链第一步「答题」有装机入口（判定标准「用户更好体验」：AI 安装完主动打开答题页，用户零找路）。hexaco/ 其余件（互照报告/评测 json）确证作者侧运营产物不入部署面。
- **INSTALL.md**：新增「分身养成链（两级点火）」节——**一级点火**（装机日：D1 答题→D2 AI 计分＋效度锚定→D3 hexaco_slice_generator 基座切片上线）；**二级点火**（随用随蒸：**蒸馏清单表** 7 行——33题→L1／日记→L2+L3／月报→L2+L3+L5／立场卡→L3／SHADOW→L6／文案→L4／铁律变更→L1 重编译；资料在手随时蒸，无「等养成」门槛）；A3 由「造芯就绪检查」改指养成链。
- **verify.sh/verify.ps1**：新增 **3.8) 养成链在位**——五要素静态断言（答题页＋造芯件＋部署声明＋INSTALL 指引＋蒸馏清单），负例实测缺件转红。终态 **14 项全过 EXIT=0**。
- 教训沉淀：判「功能能否完整给端用户」＝**使用链逐步可达**（每步有入口＋指引＋产出落位），⛔部署面齐件不等于使用链闭环。

### 表达基调参数化：分身的腔调交给用户设定（2026-09-30·发布者拍板）

- **hexaco_slice_generator.py（作者侧真源·mirror 定向同步进包·源≡包 0 差异）**：新增 TONE_LIB 表达基调库六候选（沉稳直说[默认]／冷幽默傲娇／简洁高效／热情带劲／陪伴温和／学者思辨＋用户自定义通道）——向量 json 写「表达基调」字段即渲染对应腔调；未填=沉稳直说（中性安全默认，不再预置任何作者腔调）；非法值回落默认；「表达基调自定义文本」支持用户自定。
- **去作者语境**：模板正文与样例称谓全部通用化（原预置私人定调→用户视角）——发布者实例以数据保留：向量 json「表达基调: cold-humor」字段（原写死默认→迁移为用户选定值，机制同一）。
- **INSTALL.md**：D3 步升级「偏移＋基调协商」＋表达基调候选表（七行·含自定义）＋「起点不是终点」L4 覆盖说明——腔调与守护偏移同权：AI 只推荐，用户拍板。
- **验证**：py_compile 过；render_tone_section 单测 5/5（默认／中文／负例回落／自定义／现基调）；发布者实例重跑切片确认基调配cold-humor且称谓清零；mirror 反向校验 0 差异；verify 14 项全过 EXIT=0。

### 装机态验证修复：hexaco 生成器输出目录自建（2026-09-30·WB 装机态验证 WB-20260930-005）

- **hexaco_slice_generator.py**：写出前补 `os.makedirs(slices, exist_ok=True)`——装机态（模拟新用户 MC）无 slices/ 目录时开箱跑必 FileNotFoundError（作者侧因历史产物目录已存在从未踩到＝「部署面齐件≠使用链闭环」实证）。
- **验证**：源侧（K2切片蒸馏）改→mirror-sync --only digitaltwin-slicegen@v2 定向同步（源≡包 0 差异）→装机态真跑 RC=0，产物三件齐（切片 md 88 行＋端上纯净版＋persona_manifest.json）；渲染产物脱敏五查全 0（作者侧路径/写死用户名/作者称谓接动作动词/公开署名词/档案根前缀——判据词用指代不写字面量·门禁词自伤免疫）。
- **备份**：记忆琥珀/镜像工具/20260930-装机态验证/（源侧+包侧改前副本）。

### 装机态验证遗留项处置：判据推理留痕＋mirror 快路径根治（2026-09-30·发布者拍板「按符合愿景的最优解」）

- **公开署名词判据裁定（推理留痕进检查器）**：包内署名词全部来自脱敏变换「口语称谓→公开署名」（设计内）或署名性历史标注——真泄漏形态=口语称谓裸词（变换漏网时不会转署名·必被既有裸词判据抓）。「署名词+人称动词」形态经双向实测为**过度设计**（引号话术/「署名系」分类词均误联＝假阳性，且逻辑上无增量真检出）→ 裁定不加，推理注释落 `pkg_cleanliness_check.py` 词表段防后人重提。装机态署名词出现=公开署名，无隐私泄漏。
- **mirror-sync.py 快路径缺口根治**：新增变换规则签名机制——deident_rules/build_strips/relocate_rules 三规则文件内容 sha256 进快路径 key，签名变更 ⇒ 自动置 FORCE 全量重算（⛔不再依赖人记得 --force）；成功同步且反向校验 0 差异后落账签名。自检：伪造过期签→🔁自动强置触发 ✅；首跑无签名文件=None 态不误触 ✅。
- **CHANGELOG 自引入污染修复**：本文件此前条目曾把脱敏判据词字面量写进正文致包级干净度 FAIL——已改指代化写法，并立此存照：判据词一律指代、不写字面量（门禁词自伤免疫）。

### 分发源同步补齐：qodercn 端执行准则第6条加「批量多步写入」压缩态（2026-10-01·Qoder CN 童灵·JOB-003-20261001-008 延伸）

- **改的是什么**：`adapters/qodercn/rules/execution-guidelines.md` v1.0→v1.1，第6条压缩态铁律新增 `002-扩批量多步写入`（步末落点回执／子命令失败即中止整链／收尾按回执逐项独立读验／中断先盘点已完成面）。真源=记忆规则铁律版执规-002 ⑤-扩（成长箱反哺落地），本条为其 T0 恒驻层投影。
- **为什么补这一刀（自查逮出的自身缺口）**：本端先只改了运行件 `~/.qoder-cn/rules/`，未同轮改分发源——按镜像同步语义，下次装机会把分发源的旧版刷回运行件=改动被静默回滚。与包内既有判据「装机态验证」同源（部署面齐 ≠ 使用链闭环），本轮补的是**分发面**。
- **验证（三条独立读验·exit 均 0）**：① `package_integrity_check.py` 五腿全绿·棘轮新增 0；② `content-gate.py --content` 单条正文干净度扫描过（特征库 v1.3.0，⛔不用全包模式以免把他端历史遗留算作本次风险）；③ 上游/下游第6条逐字 diff = 0 差异，两端仅保留既有称呼脱敏差（包内"用户"·本地私人项）。
- **如实边界（⛔本轮未做）**：包内另有 5 份同名 `execution-guidelines`（doubaowork／lobsterai／traework／hermes／autoclaw），实测六份版本标签与 md5 互不相同＝**各端各自演化的实体，非同一真源的镜像**，故不存在"改一处六端生效"；他端 adapter 未代改——需各端自认口径后由该端落，或由发布者统一收共享真源（见 CHANGELOG 之外的立项建议）。

### frozen_ssot_guard 真源诚实化·包内副本镜像待同步（2026-10-06·ZCode 童灵）

- **改的是什么**：共脚本真源 `脚本中心/frozen_ssot_guard.py` 诚实化——锚点串指向从未存在的段形态（HEAD×工作区双查实证）→自建立起恒红 rc1 假红毒化 pre-commit 链（逼全员绕闸）→脱钩显形🟡不拦、真拦截（锚点定位成功且冻结段被改）保留 rc1·幽灵条目清退+候选登记（守卫规范 v1.2.231 ③）。
- **包内 5 份副本处置**：references/ 下副本为出厂态镜像（不在运行链上）——**不手改副本**（mirror-sync 机制管·下次发包随真源同步）；包内 references 含 `~//Users` 形态 26 行已在迁移残留扫查闸豁免清单（归档快照类·显形不拦）。
- **验证**：真源实跑 PASS rc0（空表待命态）·mount_liveness 35 项全绿。来源：你令「先把问题处理吧·并且是根治处理」链。

### frozen_ssot_guard 真源诚实化·包内副本镜像待同步（2026-10-06·ZCode 童灵·你令「未闭环的尝试去做」）

- **改的是什么**：真源 `脚本中心/frozen_ssot_guard.py`（作者侧运行件）——锚点串指向从未存在的段形态（HEAD×工作区双查实证）→自建立起恒红假红毒化 pre-commit 链→脱钩显形不拦/真拦截保留+幽灵条目清退+候选登记（详见 守卫编写规范 v1.2.231 §3.5 案例）。
- **包内副本处置**：`references/` 下 frozen_ssot_guard.py 副本（scripts/hooks/digital-twin/devtools 多处）为**出厂态镜像·本轮不手改**（mirror-sync 机制管·下次发包随真源同步）——与包内既有判据「分发面齐≠使用链闭环」同源。
- **验证**：真源实跑 PASS rc0（空表待命态）·mount_liveness 35 项全绿。来源：你令「先把问题处理吧·并且是根治处理」链。

### ZCode 端质检轮·双腿全绿收口：verify v0.2.0 三态判据 + capability 30 件口径 + setup 补载 2 通用件（2026-10-06·ZCode 童灵·你令「让用户在这一端完整享受布洛陀所有功能·第一个通过质检」）

- **改的是什么（adapters/zcode/ 三件）**：① `verify.sh` v0.1.1→v0.2.0——[4/6] 落盘位判据三态化（用户机态 HOOK_DST 可执行 / T0 迁移态正本在 Skill路由引擎·$HOME 形态零个人态字面 / 墓碑兜底态），注册面判据去 `_hook_dst` 强绑（command 含脚本名即 registered），[5b/6] 清单改 **config.json 运行时提取**（磁盘真源驱动·零手写件名·部署面 6 件+注册面 7 件含 twin 台账 2 件）；② `capability.yaml`——delivered 补 2 件通用件（triwich_closeout_guard/systemlog_stophook_check·源 references/hooks·端实盘在挂而包无承载的真欠账）+新增 endogenous 段 5 件端元守卫（grep_sandbox/memory_size/skill_health/philosophy_parity/failure_ledger·T0 施工产物·端自建不随包·条文33三态显式防漏配假绿）+删 guard_zcode 分叉残留条目（SSOT 归一后幂等恢复≠意图恢复的活例）→ 31 条=30 件口径，数字注释 28→30/20→22 全链同步；③ `setup.sh` [5c/8]——PLAN 补同 2 件（存在性检查加 references/hooks 回退）+段头 20条→22条。
- **质检抓出的 4 个缺口（06 手册腿实跑实证）**：① verify.sh 两假红（判据锚旧位+强绑旧路径·检查器漂移非本体故障）；② 2 件通用件端实挂/包不载（漏交付·qodercn/lobsterai/workbuddy/hermes/traework 全有）；③ 7 件端实挂/capability 零声明（条文33盘点义务违反·5 件端元件无 endogenous 归态）；④ capability 分叉残留条目（旧形态未清=假欠账）。
- **验证**：腿1 `adapters/zcode/verify.sh` PASS=12 FAIL=0；腿2 `install_scripts.py --verify --platform zcode` 30/30 钩子已落盘并注册（全端 ROSTER 38 件）；腿3 脱敏门禁包内零残留（[5/6] PASS）。遗留待跑：F2-6 守卫收讫真触发、F3-4 user_machine_fixture 幂等真跑、F7 manifest 对账+容灾恢复演练（下轮补，不谎报全绿）。
- **事故留痕**：verify.sh 曾含先前批次未提交改动 14+/8-，本轮误 git checkout 丢失后按 config 真源+实跑验证重建（v0.2.0 判据更严：注册面 5→7 件）；重建过程三次 NameError 自纠（噪声环境长脚本质量纪律教训）。

### ZCode 端质检轮·三项遗留全清+收讫真触发抓出跨端静默失效（2026-10-06·ZCode 童灵·你令「要做就做完·做完了才能 loop」）

- **F2-6 收讫真触发（06 手册判据=真实执行结果非挂载声明）**：--prompt 正门喂必命中载荷 → 0 输出 → 顺藤抓出**真缺口**：rule_fragment_inject.py L41 RULES_DIR 硬编码 `~/记忆规则/`，该 HOME 级软链**本机不存在**（10-06 下午真源消副本工程动 HOME 层余波）→ rule_triggers.yaml（30 条触发规格·SSOT 编译产物）加载失败 → **UPS 铁律硬墙全端静默失效**（rc=0 无输出无报错——install_scripts.py L493 注释早已预警此形态）。判定层实测完好（真源 30 条加载+探针命中 001/005），缺口=落点断链。**修复**：重建全局软链 `~/记忆规则 → ~/个人AI档案/记忆规则`（端中立·零代码改动）→ ZCode 端 --prompt 真命中输出铁律-001/005 注入文本+决策留痕 mtime 14:45→21:34；**WB 端同款守卫同步复活**（同真源脚本·跨端共性缺口一次根治）。机制面欠账登记：fixture 测声明面不测守卫读取面=盲区（本次由收讫腿补上——真触发检查腿价值的实证）；守卫读取面路径解析律（HOME 直拼 vs runtime_paths 声明面）未立规=后续条文候选。
- **F3-4 user_machine_fixture 沙盒真跑**：模拟用户机（无作者侧目录）跑安装器本体部署 834 件（脚本中心 264+分身套件）+14 键 runtime_paths 声明（devtools 键在位）+rp() 37 处+拼接式 47 目标全可取+18 插件真导入全过，rc=0；**幂等**：三跑输出结构一致。
- **F7 同步与容灾**：① integrity-fingerprints.json fingerprints=[] = 10-03 脱敏根治**有意态**（deidentified 字段留痕"1329→0"·防作者私有面进包·防误>防错正面案例；smoke_test.py L61 自证不收其 version 作判据）非缺口；② **恢复演练**：rollback.sh --platform zcode --preview 真跑（非破坏）——SOUL/IDENTITY/USER/MEMORY 无备份如实标注+三层规则备份在位（差异 19/4/10 行可预览）=恢复通道可用；③ manifest 显目制/mirror-sync 0 差异=发版侧（作者域）工具端侧 N/A 如实标注。
- **质检腿读数终态**：F1-F7 全项+映射+流程匹配已跑，06 自检手册口径全绿（发版侧项 N/A 如实标注不谎报）；端收口，可进 loop（G 路径「loop 安装包」）。
