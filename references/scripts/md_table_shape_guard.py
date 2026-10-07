#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# REG: family=守卫 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""md_table_shape_guard.py v1.4 — markdown「写入结构」机械门禁（delta-only·表格形状 J1/J1F/J2 ＋ 条目血缘 J4）。

v1.4（2026-10-01 17:06·Qoder CN 童灵·成长箱 QCN-20261001-004／-009 同型第 3 现→升机械闸）：新增 **J4 条目身份守恒**。
  病根＝把「紧邻行的前缀」当 Edit 的 old_string 用（锚点语义＝删除面），条目行首/整条记录静默消失，
  而工具回显"1 replacements 成功"——件⑨/中央账/变更日志/决策卡/交接单/采样台账都是**多端共写的取证面**。
  判据本体＝**身份集合守恒**（HEAD 有的条目身份新态必须仍有），⛔不用"行数守恒"：行数会被"合法多行合一"
  误伤、又漏"删一行补一行"的等量替换——行数是代理指标，身份才是被保护物；用 set 不用多重集（重号修复＝合法）。
  分级＝**按身份形态分两档**（三轮回测实测定档，⛔一次回测就定级＝本件 J1「0/5 零误报」当天被两处假红推翻的同型错）：
    J4 条目头族（`- v..（`／`## [XXX-日期-序号]`／`## FU-n`／`| Tn |`／时间戳行）＝**阻断**；
    J4D 表格行族（日期｜端｜文件列）＝**⚪ 显形不拦（FU-77 定性后判定为永久显形档）**。
      `J4_PROMOTE_DEADLINE=2026-11-15` 的语义＝**复核日**，⛔"到期自动转红"：转红须另翻 `J4D_PROMOTE_READY=True`
      并附新回测证据。写成"到期即红"＝给未来埋假承诺（条文承诺会响、实际永不响＝假绿·D29 同类）。
    ①条目头族口径：488 个「提交×族文件」对 → 身份丢失 1 例，该例是真伤
      （`dba916c8` 把 LRN-20260716-001 整条覆盖成 LRN-20260822-001，当时过了全部守卫）⇒ 该口径假阳 0。
    ②域改内容驱动（HEAD 条目身份 ≥3 入域·见 lineage_family）＋加表格行族后：入断面 1182 对 → 命中 38 例（3.2%），
      其中 27 例属表格行族，抽样全是**设计使然的整写**（`K2切片蒸馏/slices/*` 生成器重写、`*_MEMORY_INDEX.md`／
      `INDEX.md` 脚本重建）⇒ 与阻断混档＝用必然误拦换信任额度，故按 J2 自家先例"承接在前·引爆在后"分档。
      抽样定性＝混合形态：`d202a159` 01 规范 v1.3.80 条目随摘要瘦身被摘／`a9eebbca` HEXACO 题库把 v1.0-v1.2
      版本史压成一句"记录保留在作者侧工程档案"／`42bd9319` 守卫规范 v1.2.149 条目消失——
      **逐例定性未完成，挂 FU-77 回访**（本件 J1 的「0/5 零误报」声明当日即被两处假红推翻，前车之鉴）。
    J4 取阻断的理由＝代价不对称：误拦一次＝一个显式 env 放行＋写理由；漏放一次＝取证被静默销毁
      且不可复原。有意删行本就该是显式动作（与 commit_sweep_guard 的 `COMMIT_SWEEP_ALLOW=1` 同族设计）。
    ⛔ 已实测的**覆盖缺口**（是边界不是缺陷·如实登记）：中央账 2026-08-05「WorkBuddy 行被截断拼接」事故窗
      （9 个「提交×变更日志.md」对）对本判据**零命中**——那是形状损坏（行没消失、内容被改写到别处），
      归 J1/J2；J4 的牙只在"整条被覆盖"与"行首被吞"两型上生效。⛔不得把本闸写成"共写面损坏已根治"。
    ⚠️ 另注：`lineage_family` 里的"派生物标记"识别（自动生成/禁手抄/auto-generated 等）已实装但**未验证有效**——
      实测命中文件头部并无这些标记，真正降噪的是 J4／J4D 分档；⛔不把它当已解决的降噪手段写进结论。
  取物口径＝**索引区**（`git show :rel`）而非工作区（pre-commit 提交的是索引·§3.4 同源律）。
  回落律＝`MD_LINEAGE_ALLOW=1` 显式放行并打 ⚪（理由写进 message），⛔不静默豁免；HEAD/索引读不出→不报。
  域说明（⚠️文件名沿用历史名）：J4 属"条目血缘"域，与本件的"写入形状"同族不同轴——J1 检"写成了什么形状"，
  J4 检"还在不在"。合并进本件而非新建件，依据＝同源律（同一病根/同一执行位/同一 staged 口径）＋零新脚本先例（QCN-20261001-006）。
  夹具 G4-G8＋变异体（`--only J1` 置假 → 同一坏暂存必须转绿）·自测含"env 键名"坑的固化注释。

v1.1（2026-09-19 10:45·Qoder CN）：新增 J1F 降级判据，修同日 J1 精度声明被 2 处假红推翻的问题。
v1.3（09-19 12:20·Qoder CN 童灵·工单 D29 拆弹）：①**到期升红原本是死代码**——main 里 `BLOCKING = BLOCKING | {"J2"}` 造局部变量遮蔽全局，cmd_report/cmd_gate 读到的仍是 {J1}，"10-31 自动转红"从未生效＝假绿；生效点收进 `blocking_set()` 单一真相源。②升红语义按判据分档 `PROMOTE_MODE`：J1=hard（到期存量也红·3 处·原承诺不变）／J2=quota（到期后名单内继续显形标 🟠未清，名单外或超额＝硬红）＝**分批收敛而非一次引爆**（实测到期硬红 3 而非 226）。③`--baseline-write` 改为按"到期日会被执行的判据集"生成名单（原按当前 BLOCKING＝J2 全成名单外新债，拆弹形同虚设）。④夹具 Q4-Q7（含变异：PROMOTE_MODE[J2]=hard→同输入必转硬红）。自测 6/6＋3 变异＋Q 组全绿 MUT:OK。
# v1.2（2026-09-19 11:28·Qoder CN 童灵·出厂 40 分钟即被自己抓到）：J1F 的豁免判据由「同形状连续 ≥3 行」改为**首格是日期时刻字段**的整行台账 idiom。
  为什么撤掉"成片"启发式：它把"格式是否有意"押在**重复次数**上，而孤例格式行照样合法——实测 §20.4 单行台账立刻又造一枚 🔴假红。
  新判据押在语义上（台账首格必为时间戳；拼接事故的首格是被截断的正文），⛔不再依赖邻接行数。

病根（成长箱 QCN-20260919-001）：往 .md 表格插行时用「行内子串」当锚点做字符串替换，
锚点不唯一也不是整行 → 表格行被塞进正文，一条 225 字的正文行从句子中间劈成三段。
当轮验收只记「文件字节数涨了 3 行」——测了"有没有写进去"，没测"写成了什么形状"，
属 §3.5「假绿·判据缺一半」在**写通道**上的新形态（此前所有守卫检的都是内容/版本，无一检形状）。

三条判据（互相独立·各有专属夹具·见 §3.9 四条同源纪律第 4 条）：
  J1 GLUED_PROSE  正文行（不以 | 开头）结尾带表格行片段 → 表格行被拼进句子
  J1F FIELD_RUN   J1 的形状 + 上下连续 ≥3 行同形状 → 作者有意的「整行字段列表」，降为显形
  J2 COL_MISMATCH 表体内某行列数 ≠ 该表众数列数 → 错插到别的表里 / 列数与表头脱节

扫描口径（判据六律落地）：
- 归因律：`--gate` 只拦**本轮新增行**；预存态打印「◽ 预存(非本轮引入·不拦)」回归属端。
- 回落律：文件读不出 / 非 UTF-8 / git 取不到 → 不报（保持旧行为），⛔不造假红风暴。
- 绑定律：跳过围栏代码块（``` 与 ~~~）；列数先剥行内 code span 再按**未转义**竖线切，
  并去掉首尾空段（缺尾竖线的历史行不得算异形）。
- 分级：J1 高精度→阻断（BLOCKING）；J2 存在系统性误报（单元格内未转义竖线/表尾注记）→⚪ 显形不拦，
  噪声口径清完后把 J2 加进 BLOCKING 即转红（单点改动·承接在前引爆在后）。
- 判据取形：J1 要求「行尾是完整表格行」且**该行前无冒号引导**——`xxx：| a | b |` 是有意的行内示例
  （系统日志/模板里成片存在），`Trae Work| 2026-09-18 |  | x |` 才是拼接事故。实证（09-19 上午标定）：加此判据前活跃区
  J1 误报 1/6，加后 0/5（真伤 4 条「错误候选待确认」+ 1 条中央账 1202 全留）。
- **该 0/5 精度已被 09-19 10:38 复核推翻 2 处**（`数字分身-发布依据-讨论稿` §19.5）：作者把讨论记录写成
  「- 时间 | 端 | 动作 | 待办 |」的**整行字段列表**（无表头），形状与拼接事故同类。故加 J1F，⛔不静默豁免——
  假红会烧掉报警信用，静默豁免会造新盲区（§3.5 两个亚型各打一次）。
  豁免判据的两次迭代：v1.1 用「同形状连续 ≥3 行」→ 出厂 40 分钟被 §20.4 的**单行**台账证伪（孤例格式行照样合法）；
  v1.2 改用首格语义（LEDGER_ROW_RE：`- YYYY-MM-DD HH:MM`）——拼接事故的首格是被截断的正文，不可能长得像时间戳。
- ⛔ 不判 J3「孤立 | 行」：全库 62 处里绝大多数是合法的单行字段表/空行隔开的表体行，且事故三类已被
  J1/J2 覆盖——无专属证据的判据不配出厂（§3.9 四条同源纪律第 4 条）。
- 完备律：`--scan/--check` 读全库活跃区，⛔不取物理尾部窗口。

用法：
  --scan    [目录]     全量报告（不拦·默认 BASE）
  --check   [目录]     活跃区红 → exit 1
  --gate    [文件...]   无参取 git 暂存的 *.md；有参按传入文件；只拦本轮 delta
  --only    J1,J1F,J2  只跑所列判据（变异测试用·出厂自证「每条各自可证伪」）
  --self-test          内置夹具（真 git 仓 + 真判据 + 三判据各一条变异）
退出码：0 无红 / 1 有红 / 2 参数或环境错
"""
import argparse
import os
import re
import subprocess
import sys

BASE = os.environ.get("MD_GUARD_BASE") or ""
# 派生镜像/冻结归档/历史快照：改一处随发版走，计入即同一缺陷双计（对齐 shell_cjk_guard 口径）
EXCLUDE_RE = re.compile(r"(布洛陀-安装包|加强包|/tests/fixtures/|/steps/|/golden/|\.bak|__pycache__|/logs/|记忆琥珀/|发布库/|/归档/|/.temp/|/\d{8}/)")
SEP_RE = re.compile(r"^\s*\|(?:\s*:?-{2,}:?\s*\|)+\s*$")
# 行尾完整表格行：至少两个「| 单元格」段收尾（`| a | b |` 形态）
ROW_TAIL_RE = re.compile(r"\|(?:[^|\n]*\|){2,}\s*$")   # 段间共用竖线：`| a | b | c |` 即 3 段
# 分级：J1（表格片段拼进正文）＋J4（条目身份消失）=高精度→阻断；J2（列数≠表头）=存在系统性误报（单元格内未转义竖线/表尾注记）
# →先显形不拦，待噪声口径清完再转红（§3.5「承接在前·引爆在后」·转红单点改此集合即可）
# J4 直接进阻断集的依据＝历史回测（2026-10-01·Qoder CN·488 个「提交×族文件」对实测）：
#   身份丢失 1 例，且该例是真伤（`dba916c8` 把 LRN-20260716-001 整条记录覆盖成 LRN-20260822-001，
#   取证销毁且当时过了全部守卫）⇒ 假阳率 0/488，非 J2 那种"系统性误报必须先清噪声"的形态。
BLOCKING = {"J1", "J4"}
# J1F：「- 2026-09-19 10:50 | 端 | 动作 | 待办 |」= 时间戳引导的整行台账行（本系统讨论记录/变更记录的通用idiom，
# 无表头但格式合法）。命中即降为 ⚪ 显形，⛔静默豁免。首格必须是"日期＋时刻"才算——拼接事故（`Trae Work| 2026-09-18 |`）
# 的首格是正文尾巴，不可能长得像时间戳，所以真伤仍归 J1。
# ⛔不用"同形状连续 ≥3 行"当判据：v1.1 首版用它，出厂 40 分钟就被 §20.4 的**单行**台账打成假红（孤例格式行照样合法）。
LEDGER_ROW_RE = re.compile(r"^[-*+]\s+\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}\s*$")
PSEUDO_FIRST_CELL_MAX = 40
# ⚪ 显形名单到期日：到期自动把 J2 并入阻断集（⛔不是免死金牌·对齐 TS_STOCK_DEADLINE 先例）
J2_PROMOTE_DEADLINE = "2026-10-31"
# J4（条目头族·回测 0 假阳）＝出厂即阻断；J4D（表格行族·同轮实测 27 例命中抽样全属"生成器整写/
# 索引重建＝设计使然"）＝先显形，FU-77 逐例定性把设计内整写识别掉之后，到期才允许转红。
# 到期日语义＝**最早可转红时间**，不是自动转红承诺（转红前置条件写在 blocking_set 注释与 FU-77）。
J4_PROMOTE_DEADLINE = "2026-11-15"
# 到期日语义＝**复核日**⛔自动引爆开关（FU-77 定性结论：机械识别"设计内整写"暂不可行⇒前置不成立）。
# 翻 True 的前提：拿出新的回测证据，证明转红后表格行族的假阳率降到与条目头族同一量级（0/488）。
J4D_PROMOTE_READY = False

# 到期语义**按判据分档**（D29·2026-09-19 童灵落地）：
#   hard  = 到期后存量也转红（J1 走这档·实测仅 3 处·免检≠免死·原设计不变）
#   quota = 到期后名单内继续显形并标 🟠未清；名单外／超额度＝硬红（J2 走这档）
# 为什么 J2 不走 hard：活跃区实测 223 处 J2 存量，一刀全红＝把"清噪声"变成"淹警报"
# （同案 09-18 信号比 228:36·会被绕过的门禁比没门禁更糟）。分批口径＝谁改哪个文件，
# 那个文件的未清额度就在 gate 里当场作废，红数随清理单调下降。
PROMOTE_MODE = {"J1": "hard", "J2": "quota"}


def blocking_set(today=None):
    """到期升红的唯一生效点（⛔不要在调用方写 `BLOCKING = BLOCKING | {...}`）。

    v1.2 及以前的 main 里就有这么一行——它在函数内造了个**局部变量**遮蔽全局，
    cmd_report／cmd_gate 读到的仍是 `{{"J1"}}`，于是"10-31 J2 自动转红"是死代码：
    条文承诺会响，实际永远不响＝假绿（2026-09-19 取证·夹具见自测 P1/P2）。"""
    import datetime
    d = today or datetime.date.today().isoformat()
    out = set(BLOCKING)
    if d >= J2_PROMOTE_DEADLINE:
        out.add("J2")
    # J4D：到期**不自动转红**。FU-77 定性结论（2026-10-01 同轮）＝表格行族命中集中在生成器整写与
    # 索引重建，且"机械识别派生文件"实测不可行（命中文件头部并无生成声明）⇒ 转红的技术前置条件不成立。
    # 因此到期日语义从"自动引爆"改为"复核日"；真要把 J4D 升成阻断，须先把此标志翻 True 并附新回测证据。
    if d >= J4_PROMOTE_DEADLINE and J4D_PROMOTE_READY:
        out.add("J4D")
    return out


# ────────────────────────────── J4 LINEAGE_LOST 条目身份守恒 ──────────────────────────────
# 病根（成长箱 QCN-20261001-004／-009·同型第 3 现）：往条目区/台账区插行时，把「紧邻行的前缀」当
#   Edit 的 old_string 用——替换语义里**锚点＝删除面**，于是那一行的开头（条目编号/版本号）没了，
#   而工具回执照打「1 replacements 成功」＝静默。两种形态：整行被覆盖（7/16 LRN 记录案）／行首被并入他行
#   （10-01 守卫规范 v1.2.183 案）。⛔与"表格形状"同族不同轴：J1 检"写成了什么形状"，J4 检"还在不在"。
# 判据本体＝**身份集合守恒**（HEAD 有的条目身份，新态必须仍有），⛔用"行数守恒"：
#   行数会被"合法多行合一"误伤、又漏掉"删一行补一行"的等量替换——行数只是代理指标，身份才是被保护物。
#   set 语义（非多重集）：重号修复/去重属合法减少"重复"，不是减少"身份"。
# 域判定＝内容驱动（见 lineage_family），⛔不用路径白名单：本文件初版用路径名单，
# 而当天两次真实吞行事故（守卫编写规范.md 的 v1.2.183 行／中央账注释行）都不在名单里——
# 路径白名单会把"最该被保护的规范类文件"整体漏掉＝判据自带一个与事故同型的盲区。
LINEAGE_ID_RES = (
    re.compile(r"^[ \t]*[-*][ \t]+[vV]?(\d+\.\d+(?:\.\d+)?)[ \t]*[（(]"),        # - v1.2.183（
    re.compile(r"^#{2,4}[ \t]+\d{4}-\d{2}-\d{2}[ \t]*·[ \t]*[vV]?(\d+(?:\.\d+){1,3})"),  # ## 2026-10-01 · v2.12：
    re.compile(r"^#{2,4}[ \t]*\[?([A-Z]{2,4}-\d{8}-\d{3})\]?"),                    # ## [QCN-20261001-009]
    re.compile(r"^#{2,4}[ \t]*(FU-\d+)"),                                          # ## FU-72
    re.compile(r"^[ \t]*\|[ \t]*(T\d+)[ \t]*\|"),                                   # | T17 |
    re.compile(r"^[ \t]*\|[ \t]*(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2})[ \t]*\|"),       # | 2026-10-01 12:13 |
)
# ⚠️ 命名坑自曝（本轮自己踩·`--self-test` 当场逮住）：本常量初版也叫 `LEDGER_ROW_RE`，与本文件上方
#   J1F 的同名正则冲突（后定义覆盖前定义）→ pseudo/singleton 两夹具从 J1F 退化成 J1。
#   ⇒ 派生身份三元组改用 `TRIPLE_ROW_RE`。教训与 J4 同源：**覆盖是静默的，命名必须带域前缀**。
TRIPLE_ROW_RE = re.compile(
    r"^[ \t]*\|[ \t]*(\d{4}-\d{2}-\d{2})[ \t]*\|[ \t]*([^|\n]{1,40}?)[ \t]*\|[ \t]*([^|\n]{1,80}?)[ \t]*\|")
LINEAGE_ALLOW_ENV = "MD_LINEAGE_ALLOW"
# 派生物识别（内容特征·非路径名单）：带"生成器整写/禁手抄/auto-generated"声明的文件，
# 其身份变动是设计使然（铁律-029：账本⛔落派生物 ⇒ 派生物⛔当账本护）
LINEAGE_GENERATED_RE = re.compile(
    r"(自动生成|自动分发|生成器.{0,6}整写|由\s*\S{0,24}\.py\s*单向生成|禁手抄|不可手改|"
    r"auto-?generated|DO NOT EDIT|本文件由)", re.I)


def lineage_ids(txt):
    """**条目头族**身份集合（版本号/记录编号/FU/T行/时间戳行）。逐行只取第一个命中的形态
    （一行一条目，⛔不把正文里的版本号当身份）。这一族是 J4 阻断判据的取数面——
    回测 488 对／命中 1 例且为真伤／0 假阳，就是按这一族算的（分级依据·见文件头）。"""
    out = set()
    for line in txt.split("\n"):
        for rx in LINEAGE_ID_RES:
            m = rx.match(line)
            if m:
                out.add(m.group(1))
                break
    return out


def ledger_row_ids(txt):
    """**表格行族**身份（中央账/索引/切片的「日期｜端｜文件列」三元组）。
    单独分档为 J4D（⚪ 显形不拦）的依据＝同轮回测：这一族在 1182 对里贡献 27 例命中，
    抽样全是**设计使然的整写**（K2 slices 由生成器重写、`*_MEMORY_INDEX.md`/`INDEX.md` 由脚本重建）
    ⇒ 属 J2 那种"系统性误报形态"，按本文件自家先例＝先显形、噪声口径清完再转红，⛔直接引爆。"""
    out = set()
    for line in txt.split("\n"):
        m = TRIPLE_ROW_RE.match(line)
        if m:
            out.add("|".join([m.group(1), m.group(2).strip(), m.group(3).strip()[:60]]))
    return out


def lineage_compare(old_txt, new_txt):
    """判据本体：返回 (丢失的条目头身份, 丢失的表格行身份)，各自排序·可复现。"""
    return (sorted(lineage_ids(old_txt) - lineage_ids(new_txt)),
            sorted(ledger_row_ids(old_txt) - ledger_row_ids(new_txt)))


def lineage_family(old_txt):
    """域判定＝**内容驱动**（HEAD 里存在 ≥3 个条目身份即算取证面），⛔用路径白名单。
    改内容判据的实证理由：本轮自己的两次吞行事故（守卫规范 v1.2.183 行／中央账注释行）
    都不在原路径名单里——路径白名单会把"最该被保护的规范类文件"整体漏掉，
    等于给判据自带一个与事故同型的盲区（§3.5「仪器不测这一项」的新表现）。
    阈值 3：单/两个身份的文件多为示例或正文引用，误伤面先于收益；见下方回测口径。
    ⛔派生物不入域（铁律-029 同源判据）：账本不落被生成器整写的文件，反之整写派生物是**设计使然**，
    把它判成"取证销毁"＝制造必然误拦。识别方式仍走内容特征（生成声明/禁手抄标记），⛔再挂路径名单。"""
    if len(lineage_ids(old_txt)) < 3:
        return False
    head = old_txt[:3000]
    if LINEAGE_GENERATED_RE.search(head):
        return False
    return True


def lineage_losses(root, rel):
    """返回 (可读性bool, 丢失条目头身份, 丢失表格行身份)。
    读 **索引区**（`git show :rel`）而非工作区文件——pre-commit 提交的是索引；读工作区会漏掉
    「已 add 的坏版本＋工作区随后被修好」这一形态（＝同一缺陷双本账，检查对象与提交对象不同源·§3.4 同源律）。
    回落律：HEAD 或索引读不出（新文件/删除/非文本）→ 不报，⛔不造假红。"""
    old = _git(root, ["show", "HEAD:" + rel])
    new = _git(root, ["show", ":" + rel])
    if not old or not new:
        return False, [], []
    if not lineage_family(old) and not ledger_row_ids(old):
        return True, [], []
    return True, *lineage_compare(old, new)


def _cells(line):
    """单元格数：先剥行内 code span（`A \|\| B` 里的竖线是内容不是分隔符），
    再按未转义竖线切，去掉首尾空段——缺尾竖线的历史行不得算作异形（防假红）。"""
    bare = re.sub(r"`[^`\n]*`", "§", line)
    parts = re.split(r"(?<!\\)\|", bare)
    if parts and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return len(parts)


def _in_code_span(line, col):
    """粗略判该行内 code span 是否覆盖 col（行内 `a|b` 不计）。"""
    spans = [m.span() for m in re.finditer(r"`[^`\n]*`", line)]
    return any(a <= col < b for a, b in spans)


def _field_run_cells(line):
    """该行若是时间戳引导的整行台账 → 返回单元格数；否则 None。

    与拼接事故同形状，区别取在**首格语义**：台账行首格是日期时刻字段，事故行首格是被截断的正文。
    """
    st = line.strip()
    if not (st.startswith("- ") or st.startswith("* ") or st.startswith("+ ")):
        return None
    bare = re.sub(r"`[^`\n]*`", "§", line)
    parts = re.split(r"(?<!\\)\|", bare)
    if len(parts) < 3 or len(parts[0].strip()) > PSEUDO_FIRST_CELL_MAX:
        return None
    if not LEDGER_ROW_RE.match(parts[0].strip()):
        return None
    return _cells(line)


def classify(lines):
    """返回 [(lineno, judge, detail)]。judge ∈ J1/J2/J3。"""
    hits = []
    blocks = []
    code = [False] * len(lines)   # 围栏代码块内的行不参与判定（模板/示例里的表是真表样，不是数据）
    fence = False
    for i, raw in enumerate(lines):
        st = raw.strip()
        if st.startswith("```") or st.startswith("~~~"):
            fence = not fence
            code[i] = True
            continue
        code[i] = fence
    row = [False] * len(lines)
    i = 0
    while i < len(lines):
        if code[i] or _in_code_span(lines[i], 0) or not lines[i].strip().startswith("|"):
            i += 1
            continue
        j = i
        while j < len(lines) and not code[j] and lines[j].strip().startswith("|"):
            row[j] = True
            j += 1
        blocks.append((i, j))
        i = j
    fcells = [None if (code[k] or row[k]) else _field_run_cells(lines[k]) for k in range(len(lines))]
    for a, b in blocks:
        body = [x for x in range(a, b) if not SEP_RE.match(lines[x])]
        if len(body) < 2:
            continue  # 单行「| a | b |」=字段表·无表头可比·不判（防假红）
        has_head = (b - a >= 2 and SEP_RE.match(lines[a + 1]) and _cells(lines[a]) >= 2)
        counts = [_cells(lines[x]) for x in body]
        if has_head:
            ref, basis = _cells(lines[a]), "表头"
            body = body[1:]            # 表头自身不判，只判表体
            counts = counts[1:]
        else:
            cnt = {}
            for c in counts:
                cnt[c] = cnt.get(c, 0) + 1
            top = max(cnt.values())
            if list(cnt.values()).count(top) > 1:
                continue               # 平票=本块形状本身两式并存·不判（判据不稳时宁可漏报）
            ref, basis = max(cnt, key=cnt.get), "众数"
        for ln, c in zip(body, counts):
            if c != ref:
                hits.append((ln + 1, "J2", f"单元格 {c} ≠ {basis} {ref}"))
    for idx, raw in enumerate(lines):
        if code[idx] or row[idx] or not raw.strip():
            continue
        if raw.lstrip().startswith(">"):   # 引用块表格（> | a | b |）是合法形态
            continue
        m = ROW_TAIL_RE.search(raw)
        if not m:
            continue
        lead = raw[:m.start()].rstrip()
        if lead.endswith("：") or lead.endswith(":"):
            continue          # 冒号引导=作者有意把表样写在正文里（模板/日志示例），非拼接事故
        if fcells[idx]:
            hits.append((idx + 1, "J1F", "时间戳整行台账（有意格式非拼接）·显形不拦"))
            continue
        hits.append((idx + 1, "J1", f"正文行尾拼入 {_cells(m.group(0))} 列表格片段"))
    return sorted(hits)


def scan_file(path, only):
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return None  # 回落律：读不出=不判，不造红
    lines = text.split("\n")
    hits = [(ln, k, d) for ln, k, d in classify(lines) if k in only]
    return hits


def resolve_base(explicit):
    if explicit:
        return os.path.abspath(os.path.expanduser(explicit))
    if BASE:
        return BASE
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    top = (r.stdout or b"").decode("utf-8", "replace").strip()
    return top or os.path.expanduser("~")


def walk(root, only):
    red, unreadable = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            rel = os.path.join(dirpath, fn)
            if EXCLUDE_RE.search(rel):
                continue
            h = scan_file(rel, only)
            if h is None:
                unreadable += 1
                continue
            for ln, k, d in h:
                red.append((rel, ln, k, d))
    return red, unreadable


def _src_cache(root):
    cache = {}

    def src_of(rel):
        if rel not in cache:
            f = rel if os.path.isabs(rel) else os.path.join(root, rel)
            try:
                cache[rel] = open(f, encoding="utf-8").read().split("\n")
            except OSError:
                cache[rel] = []
        return cache[rel]
    return src_of


def _key_of(root, src_of):
    def f(h):
        rel, ln, k, _ = h
        src = src_of(rel)
        base = os.path.relpath(rel if os.path.isabs(rel) else os.path.join(root, rel), root)
        return base + "␟" + k + "␟" + row_key(src[ln - 1] if 0 < ln <= len(src) else "")
    return f


def _split_by_stock(hits, stock_cnt, expired, keyf, blocking=None):
    """按 (路径,行号) 顺序消耗存量额度，额度用尽后的同键命中＝新债。返回 (全量非存量, 存量)。

    为什么不用 set 判定：生产端每日 regenerate，同文案破损的键完全相同，set 会把第 2、3 次
    一起洗成"存量"＝假绿（2026-09-19 实测：错误候选待确认.md 由 4 条涨到 5 条被吞）。
    到期后按 PROMOTE_MODE 分档：hard 档存量不再享额度（转硬红）；quota 档存量继续被额度吞住，
    但由调用方标成 🟠未清——名单外／超额的命中一律进 hard。"""
    blocking = blocking_set() if blocking is None else blocking
    left = dict(stock_cnt)
    hard, aged = [], []
    for h in sorted(hits, key=lambda x: (x[0], x[1])):
        k = keyf(h)
        quota = left.get(k, 0) > 0
        keep = (not expired) or PROMOTE_MODE.get(h[2], "hard") == "quota"
        if h[2] in blocking and quota and keep:
            left[k] -= 1
            aged.append(h)
        else:
            hard.append(h)
    return hard, aged


def cmd_report(root, only, strict):
    red, unreadable = walk(root, only)
    stock_cnt, stock_dl = load_stock()
    import datetime
    expired = datetime.date.today().isoformat() >= stock_dl
    src_of = _src_cache(root)
    blocking = blocking_set()
    hard, aged = _split_by_stock(red, stock_cnt, expired, _key_of(root, src_of), blocking)
    aged_set = {(h[0], h[1], h[2]) for h in aged}
    unclean = {(h[0], h[1], h[2]) for h in aged
               if expired and PROMOTE_MODE.get(h[2], "hard") == "quota"}
    per, perhard = {}, {}
    for _, _, k, _ in red:
        per[k] = per.get(k, 0) + 1
    for rel, ln, k, d in sorted(red, key=lambda x: (x[0], x[1])):
        is_block = k in blocking and (rel, ln, k) not in aged_set
        if is_block:
            perhard[k] = perhard.get(k, 0) + 1
        mark = "🟠未清" if (rel, ln, k) in unclean else ("⚪存量" if (rel, ln, k) in aged_set else "⚪")
        print(f"{'🔴' if is_block else mark} {k} "
              f"{os.path.relpath(rel, root)}:{ln}  {d}")
    n_hard = sum(perhard.values())
    print(f"[md_table_shape_guard] 🔴阻断级 {n_hard}（{perhard or '—'}）｜⚪显形/存量 {len(red) - n_hard}"
          f"（全量 J1={per.get('J1', 0)} J1F={per.get('J1F', 0)} J2={per.get('J2', 0)}）"
          f"｜🟠到期未清 {len(unclean)}｜未读 {unreadable}")
    return 1 if (n_hard and strict) else 0


STOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "md_shape_stock.txt")
STOCK_DEADLINE = "2026-10-31"      # 到期存量也转红（对齐 TS_STOCK/MUT_STOCK 纪律·免检≠免死）


def row_key(line):
    """存量名单的稳定键：取行内前两段非空文本（表格行=日期+工具/字段名）。
    ⛔不用行号或整行内容——上方插行或改措辞都会让键漂移＝同一缺陷产生新债（守卫家族 v0.4 TS7 判例）。"""
    segs = [x.strip() for x in re.split(r"(?<!\\)\|", line) if x.strip()]
    return "␟".join(segs[:2])[:80]


def load_stock():
    """存量名单＝键→**允许被吞的次数**（同文案重复破损只登记一次，第二次就是新债·防假绿）。"""
    cnt, deadline = {}, STOCK_DEADLINE
    if os.path.isfile(STOCK_FILE):
        for l in open(STOCK_FILE, encoding="utf-8"):
            l = l.rstrip("\n")
            if l.startswith("#deadline:"):
                deadline = l.split(":", 1)[1].strip() or STOCK_DEADLINE
            elif l and not l.startswith("#"):
                cnt[l] = cnt.get(l, 0) + 1
    return cnt, deadline


def write_stock(keys):
    """keys 允许重复：重复次数即该键的容许额度。⛔去重——去重＝把"同文案再犯"洗成存量。"""
    with open(STOCK_FILE, "w", encoding="utf-8") as fh:
        fh.write("# md_table_shape_guard 存量名单（首跑实测·到期转红·同键多行=多个额度）\n")
        fh.write(f"#deadline: {STOCK_DEADLINE}\n")
        for k in sorted(keys):
            fh.write(k + "\n")
    print(f"存量名单已写入 {STOCK_FILE}（{len(set(keys))} 键／{len(keys)} 额度·到期 {STOCK_DEADLINE}）")


def _git_bin():
    """绕开 ~/bin/git 这层 wrapper（它拦 `commit -q` 与无路径提交）：
    夹具与被测代码必须用同一个真 git，否则测试结果随 PATH 变＝不可复现。"""
    for cand in ("/usr/bin/git", "/opt/homebrew/bin/git", "/usr/local/bin/git"):
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    for w in (x for x in (os.environ.get("PATH", "").split(os.pathsep)) if "/bin" in x):
        c = os.path.join(w, "git")
        if os.path.isfile(c) and os.access(c, os.X_OK) and "/.local/bin" not in c and "/Users/" not in c.split("/bin/")[0]:
            return c
    return "git"


GIT_BIN = _git_bin()


def _git(root, args):
    r = subprocess.run([GIT_BIN, "-C", root] + args, capture_output=True)
    return (r.stdout or b"").decode("utf-8", "replace")


def cmd_gate(files, only, root):
    stock_cnt, stock_dl = load_stock()
    import datetime
    expired = datetime.date.today().isoformat() >= stock_dl
    src_of = _src_cache(root)
    if not files:
        out = _git(root, ["diff", "--cached", "--name-only", "-z"])
        files = [x for x in out.split("\0") if x.endswith(".md")]
    added_map, hit_rows = {}, []
    for rel in files:
        fp = rel if os.path.isabs(rel) else os.path.join(root, rel)
        if not os.path.isfile(fp) or EXCLUDE_RE.search(fp):
            continue
        diff = _git(root, ["diff", "--cached", "-U0", "--", rel]) or _git(root, ["diff", "-U0", "--", rel])
        added = set()
        for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
            start = int(m.group(1))
            added.update(range(start, start + int(m.group(2) or 1)))
        added_map[rel] = added
        for ln, k, d in (scan_file(fp, only) or []):
            hit_rows.append((rel, ln, k, d))
    blocking = blocking_set()
    hard, aged = _split_by_stock(hit_rows, stock_cnt, expired, _key_of(root, src_of), blocking)
    aged_set = {(h[0], h[1], h[2]) for h in aged}
    blocked = 0
    for rel, ln, k, d in sorted(hit_rows, key=lambda x: (x[0], x[1])):
        mine = ln in added_map.get(rel, set())
        is_stock = (rel, ln, k) in aged_set
        hard_hit = k in blocking and not is_stock
        if not mine:
            tag = "◽ 预存(非本轮引入·不拦)"
        elif hard_hit:
            tag = "🔴 本轮引入"
        elif is_stock:
            tag = "◽ 存量名单(到期转红·不拦)"
        else:
            tag = "⚪ 显形级(承接前不拦)"
        print(f"{tag} {k} {rel}:{ln}  {d}")
        if mine and hard_hit:
            blocked += 1
    # ── J4 条目身份守恒（两档：J4 条目头族＝阻断 ／ J4D 表格行族＝显形·到期只复核不自动转红）──
    # 分档依据＝同轮回测：条目头族 488 对／1 例真伤／0 假阳；表格行族在同窗口贡献 27 例命中，
    # 抽样全是生成器整写（K2 slices）与索引重建（*_MEMORY_INDEX.md／INDEX.md）＝设计使然
    # ⇒ 后者按 J2 先例「承接在前·引爆在后」，⛔与阻断混档＝用必然误拦换信任额度。
    j4_red = 0
    j4d_show = 0
    if not only or ("J4" in only or "J4D" in only):
        allow = os.environ.get(LINEAGE_ALLOW_ENV) == "1"
        for rel in files:
            if EXCLUDE_RE.search(rel):
                continue
            readable, lost, lost_rows = lineage_losses(root, rel)
            if not readable:
                continue
            if lost and ("J4" in (only or {"J4", "J4D"})):
                if allow:
                    print(f"⚪ J4 {rel} 条目身份消失 {len(lost)} 个（{LINEAGE_ALLOW_ENV}=1 显式放行·"
                          f"理由请写进 commit message）: {', '.join(lost[:8])}")
                elif "J4" in blocking:
                    print(f"🔴 J4 {rel} 条目身份消失 {len(lost)} 个: {', '.join(lost[:12])}")
                    j4_red += len(lost)
                else:
                    print(f"⚪ J4 {rel} 条目身份消失 {len(lost)} 个（显形档）: {', '.join(lost[:8])}")
            if lost_rows and ("J4D" in (only or {"J4", "J4D"})):
                tag = "🔴 J4D" if "J4D" in blocking else "⚪ J4D"
                print(f"{tag} {rel} 表格行身份消失 {len(lost_rows)} 个"
                      f"（生成器整写/索引重建属设计内·逐例定性未清前不拦）: "
                      f"{'; '.join(x[:52] for x in lost_rows[:3])}")
                if "J4D" in blocking:
                    j4_red += len(lost_rows)
                else:
                    j4d_show += len(lost_rows)
    if j4_red:
        print(f"[md_table_shape_guard --gate] 条目血缘红 {j4_red} ｜ 确属有意删除/合并/退役 → "
              f"`{LINEAGE_ALLOW_ENV}=1 git commit …`（理由写进 message）；"
              f"⛔勿 --no-verify（绕过＝留痕断裂，且 commit_sweep/版本真值同链会再抓）")
        print(f"   修法：把被吞的那一行按 HEAD 原文补回（`git show HEAD:<file> | sed -n 'Np'` 逐字取回），⛔不凭记忆重写。")
    elif j4d_show:
        print(f"[md_table_shape_guard --gate] J4D 表格行血缘显形 {j4d_show} 个（不拦·"
              f"转红前提＝把『设计内整写』逐例识别掉，定性挂 FU-77·到期 {J4_PROMOTE_DEADLINE}）")
    blocked += j4_red
    print(f"[md_table_shape_guard --gate] 本轮 delta 红 {blocked} ｜待检文件 {len(files)}")
    return 1 if blocked else 0


FIXTURES = {
    # 文件名 → (内容, 期望命中的判据集合)。每条判据各有"只有它能拦"的专属夹具（§3.9 四条同源纪律第 4 条）
    "glued.md": ("- 🔧 **反哺工具**：Trae Work| 2026-09-18 |  | x |  | 🔴 待整合 |\n"
                 "- 🎯 正常正文行，含竖线但不以竖线结尾 | 不该报\n", {"J1"}),
    "cols.md": ("| A | B |\n|:--|:--|\n| 1 | 2 |\n| 1 | 2 | 3 |\n", {"J2"}),
    "pseudo.md": ("### 讨论记录追加\n\n"
                  "- 2026-09-19 10:50 | ZCode | 动作一 | 待你看 |\n"
                  "- 2026-09-19 11:20 | ZCode | 动作二 | 待办：双源重跑 |\n"
                  "- 2026-09-19 11:40 | ZCode | 动作三（结论降级）| 待办 |\n"
                  "- 2026-09-19 12:10 | ZCode | 动作四·对照实验 | 待你裁决 |\n", {"J1F"}),
    "singleton.md": ("### 20.4 讨论记录追加\n\n"
                     "- 2026-09-19 12:50 | ZCode | 分层一致性三件落地 | 待你裁决：①②③ |\n"
                     "\n普通正文一句，不含竖线。\n", {"J1F"}),
    "quote.md": ("> | 列 | 列 |\n>|----|----|\n> | a | b |\n\n- 引用示例：| 值 | 值 | 值 | 值 | 值 |\n", set()),
    "clean.md": ("| A | B |\n|:--|:--|\n| 1 | 2 |\n\n正文里有 `a|b|c` 行内码。\n\n"
                 "| 律 | 条文 |\n|:--|:--|\n| 短路律 | ⛔DO NOT 用 `A && { … } \\|\\| B` |\n", set()),
}


def run_quota_probe():
    """存量额度判据的两向探针（⛔只测"能检出"＝§3.5 判据缺一半）：
    同一键的两条命中，额度 1 必须漏 1 条成新债；额度 2 必须全放过。"""
    hits = [("a.md", 1, "J1", ""), ("a.md", 2, "J1", "")]
    keyf = lambda h: "K"
    h1, a1 = _split_by_stock(hits, {"K": 1}, False, keyf)
    h2, a2 = _split_by_stock(hits, {"K": 2}, False, keyf)
    h3, a3 = _split_by_stock(hits, {}, True, keyf)      # 到期：hard 档（J1）存量也得转红
    ok = (len(h1) == 1 and len(a1) == 1 and len(h2) == 0 and len(a2) == 2 and len(h3) == 2)
    print(f"  夹具 Q1 额度1→新债 1 ｜ Q2 额度2→全放过 ｜ Q3 到期→全转红 ：{'✅' if ok else '❌ 实得 %d/%d/%d' % (len(h1), len(h2), len(h3))}")
    # ── Q4-Q7：quota 档（J2·D29 分批升红）与生效点遮蔽 bug 的专属证据 ──────────
    j2 = [("c.md", 1, "J2", ""), ("c.md", 2, "J2", "")]
    bl = blocking_set("2026-11-01")          # 模拟 10-31 之后
    h4, a4 = _split_by_stock(j2, {"K": 2}, True, keyf, bl)   # 名单内额度足→未清不炸
    h5, a5 = _split_by_stock(j2, {"K": 1}, True, keyf, bl)   # 额度只 1→第 2 条成新债
    q45 = (len(h4) == 0 and len(a4) == 2 and len(h5) == 1)
    print(f"  夹具 Q4 到期·quota 档名单内→🟠未清(0 硬红) ｜ Q5 额度1→新债 1 ：{'✅' if q45 else '❌ 实得 hard=%d aged=%d/%d' % (len(h4), len(a4), len(h5))}")
    # Q6 生效点唯一：到期集合含 J2，而全局 BLOCKING 必须仍不含（证明升红靠 blocking_set，不是靠全局被改）
    q6 = ("J2" in bl) and ("J2" not in BLOCKING) and ("J2" not in blocking_set("2026-09-19"))
    print(f"  夹具 Q6 升红生效点＝blocking_set(到期) 而非全局 BLOCKING（死代码遮蔽 bug 已封）：{'✅' if q6 else '❌'}")
    # 变异：把 J2 划回 hard 档 → Q4 的两条必须双双转硬红（否则"分批"这条分支从未被执行＝假绿）
    global PROMOTE_MODE
    keep = PROMOTE_MODE
    try:
        PROMOTE_MODE = {"J1": "hard", "J2": "hard"}
        hm, am = _split_by_stock(j2, {"K": 2}, True, keyf, bl)
    finally:
        PROMOTE_MODE = keep
    q7 = len(hm) == 2
    print(f"  变异体 PROMOTE_MODE[J2]=hard → Q4 同一输入 {'转硬红 2 条 ✅ 分批分支活着' if q7 else '实得 hard=%d ❌' % len(hm)}")
    return 0 if (ok and q45 and q6 and q7) else 1


def run_self_test(only=None):
    import tempfile
    import shutil
    root = tempfile.mkdtemp(prefix="mdshape-")
    mut = (only or {"J1", "J1F", "J2", "J3"})
    try:
        for fn, (body, _) in FIXTURES.items():
            open(os.path.join(root, fn), "w", encoding="utf-8").write(body)
        rc = 0
        detail = []
        for fn, (_, expect) in FIXTURES.items():
            got = {k for _, k, _ in (scan_file(os.path.join(root, fn), mut) or [])}
            want = expect & mut
            if got != want:
                rc = 1
                detail.append(f"❌ {fn}: 期望{sorted(want)} 实得{sorted(got)}")
            else:
                detail.append(f"✅ {fn}: {sorted(want) or '无红（负例）'}")
        # 变异：逐条判据置假 → 该判据的夹具必须转绿（否则它没有专属证据）
        mut_lines = []
        for target in ("J1", "J2"):
            others = {k for k in ("J1", "J2") if k != target}
            fn = {"J1": "glued.md", "J2": "cols.md"}[target]
            still = {k for _, k, _ in (scan_file(os.path.join(root, fn), others) or [])}
            mut_lines.append(f"  变异体 {target} 置假 → {fn} {'转绿 ✅ 判据活着' if not still else '仍红 ❌ ' + str(sorted(still))}")
        # J1F 是"降级"判据，专属变异＝把 idiom 正则整体置假：pseudo/singleton 必须回退成 J1，
        # 否则降级分支从未执行过（该夹具即假绿·§3.9 出厂动作）
        global LEDGER_ROW_RE
        keep = LEDGER_ROW_RE
        back = set()
        try:
            LEDGER_ROW_RE = re.compile(r"(?!x)x")          # 恒不匹配
            for fn in ("pseudo.md", "singleton.md"):
                back |= {k for _, k, _ in (scan_file(os.path.join(root, fn), mut) or [])}
        finally:
            LEDGER_ROW_RE = keep
        ok_f = back == {"J1"}
        mut_lines.append(f"  变异体 J1F 置假（idiom 正则恒假）→ pseudo+singleton {'双双回退成 J1 ✅ 降级分支活着' if ok_f else '实得 ' + str(sorted(back)) + ' ❌'}")
        if not ok_f:
            rc = 1
        print("\n".join(detail))
        print("\n".join(mut_lines))
        rc_gate = run_gate_fixtures()
        rc_q = run_quota_probe()
        rc = rc or rc_gate or rc_q
        alive = all(("✅" in l and "❌" not in l) for l in mut_lines)
        print("MUT:" + ("OK" if (alive and rc == 0) else "FAIL") +
              f" 判据各自可证伪={alive}（{len(mut_lines)} 个变异体）｜夹具={'全绿' if rc == 0 else '有红'}")
        return rc
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_gate_fixtures():
    """真 git 仓 + 真 --gate：验「本轮 delta 才拦」这条归因律在写通道上真的成立。
    缺这一段＝只在 commit 时跑的分支零覆盖（§3.5 假绿·判据缺一半）。"""
    import tempfile
    import shutil
    import subprocess
    scripts = {"bad.md": "- 🔧 **反哺工具**：Trae Work| 2026-09-18 |  | x |  | 🔴 待整合 |\n",
               "good.md": "- 🔧 **反哺工具**：Trae Work\n- 🎯 正文\n"}
    gitenv = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                  GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    root = tempfile.mkdtemp(prefix="mdshape-gate-")
    try:
        subprocess.run([GIT_BIN, "init", "-q"], cwd=root, capture_output=True)
        for fn, body in scripts.items():
            open(os.path.join(root, fn), "w", encoding="utf-8").write(body)
        subprocess.run([GIT_BIN, "add", "good.md"], cwd=root, capture_output=True)
        me = os.path.abspath(__file__)
        env = dict(os.environ, MD_GUARD_BASE=root)
        r0 = subprocess.run([sys.executable, me, "--gate"], cwd=root, capture_output=True, env=env)
        ok_clean = (r0.returncode == 0)
        # 造一次「本轮引入」的拼接事故
        open(os.path.join(root, "good.md"), "a", encoding="utf-8").write(scripts["bad.md"])
        subprocess.run([GIT_BIN, "add", "good.md"], cwd=root, capture_output=True)
        r1 = subprocess.run([sys.executable, me, "--gate"], cwd=root, capture_output=True, env=env)
        out = (r1.stdout + r1.stderr).decode("utf-8", "replace")
        ok_block = (r1.returncode == 1 and "J1" in out)
        # 预存态（HEAD 里已有·本轮未新增行）不得拦
        subprocess.run([GIT_BIN, "commit", "-q", "-m", "seed", "--", "good.md"],
                       cwd=root, capture_output=True, env=gitenv)
        open(os.path.join(root, "good.md"), "a", encoding="utf-8").write("- 🎯 又一行正常正文\n")
        subprocess.run([GIT_BIN, "add", "good.md"], cwd=root, capture_output=True)
        r2 = subprocess.run([sys.executable, me, "--gate"], cwd=root, capture_output=True, env=env)
        ok_stock = (r2.returncode == 0 and "预存" in (r2.stdout + r2.stderr).decode("utf-8", "replace"))
        print(f"  夹具 G1 干净暂存 → rc={r0.returncode} {'✅' if ok_clean else '❌'}")
        print(f"  夹具 G2 本轮拼接 → rc={r1.returncode} {'✅' if ok_block else '❌'}")
        print(f"  夹具 G3 预存不拦 → rc={r2.returncode} {'✅' if ok_stock else '❌'}")
        # ── J4 条目身份守恒（真 git 仓·HEAD↔索引 对照；每条各有专属例·§3.9 第 4 条）──
        j4 = {}
        ledger = os.path.join(root, "变更日志.md")

        def _seed(text):
            open(ledger, "w", encoding="utf-8").write(text)
            subprocess.run([GIT_BIN, "add", "变更日志.md"], cwd=root, capture_output=True)
            subprocess.run([GIT_BIN, "commit", "-q", "-m", "seed", "--", "变更日志.md"],
                           cwd=root, capture_output=True, env=gitenv)

        def _stage(text):
            open(ledger, "w", encoding="utf-8").write(text)
            subprocess.run([GIT_BIN, "add", "变更日志.md"], cwd=root, capture_output=True)
            return subprocess.run([sys.executable, me, "--gate"], cwd=root,
                                  capture_output=True, env=env)

        def _stage_only(text, only):
            open(ledger, "w", encoding="utf-8").write(text)
            subprocess.run([GIT_BIN, "add", "变更日志.md"], cwd=root, capture_output=True)
            return subprocess.run([sys.executable, me, "--gate", "--only", only], cwd=root,
                                  capture_output=True, env=env)
        HEAD2 = ("- v1.0（2026-01-01）：甲条目\n"
                 "- v1.1（2026-01-02）：乙条目\n"
                 "- v1.9（2026-01-09）：丙条目\n")     # 三条起判（lineage_family 阈值＝HEAD 身份 ≥3）
        _seed(HEAD2)
        r_drop = _stage(HEAD2.replace("- v1.0（2026-01-01）：甲条目\n", ""))   # G4 整条被覆盖/删
        o_drop = (r_drop.stdout + r_drop.stderr).decode("utf-8", "replace")
        j4["G4 条目消失→拦"] = (r_drop.returncode == 1 and "J4" in o_drop and "1.0" in o_drop)
        r_add = _stage(HEAD2 + "- v1.2（2026-01-03）：丁条目\n")     # G5 纯追加＝合法
        j4["G5 纯追加→放行"] = (r_add.returncode == 0 and "J4" not in (r_add.stdout + r_add.stderr).decode("utf-8", "replace"))
        _seed(HEAD2)
        # G6＝009 原案：条目行的**行首**被并进上一行尾部（内容没丢、身份锚没了）
        r_merge = _stage("- v1.0（2026-01-01）：甲条目\n- v1.9（2026-01-09）：丙条目。尾巴：**乙条目\n")
        o_merge = (r_merge.stdout + r_merge.stderr).decode("utf-8", "replace")
        j4["G6 行首被并入他行(009 原案)→拦"] = (r_merge.returncode == 1 and "1.1" in o_merge)
        r_word = _stage("- v1.0（2026-01-01）：甲条目改写法\n- v1.1（2026-01-02）：乙条目\n"
                        "- v1.9（2026-01-09）：丙条目\n")
        j4["G7 同身份改措辞→放行(防假红)"] = (r_word.returncode == 0)
        _seed(HEAD2)
        # ⛔ 坑（本轮自犯·已固化成注释）：dict(env, NAME="1") 的键是**字面量 NAME**，不是变量的值——
        # env 注入必须写 dict(env, **{LINEAGE_ALLOW_ENV: "1"})，否则回落例测的是"没设 env"。
        env_allow = dict(env, **{LINEAGE_ALLOW_ENV: "1"})
        open(ledger, "w", encoding="utf-8").write(HEAD2.replace("- v1.0（2026-01-01）：甲条目\n", ""))
        subprocess.run([GIT_BIN, "add", "变更日志.md"], cwd=root, capture_output=True)
        r_allow = subprocess.run([sys.executable, me, "--gate"], cwd=root, capture_output=True, env=env_allow)
        o_allow = (r_allow.stdout + r_allow.stderr).decode("utf-8", "replace")
        j4["G8 env 显式回落→⚪ 不拦"] = (r_allow.returncode == 0 and "⚪ J4" in o_allow)
        r_mut = _stage_only(HEAD2.replace("- v1.0（2026-01-01）：甲条目\n", ""), "J1")   # 变异：J4 划出判据集
        j4["变异体 判据置假→G4 同输入转绿"] = (r_mut.returncode == 0)
        # G9＝域判定回归：只有 2 个身份的文件（阈值未达）⛔进入判据；≥3 才判（防"示例文件全红"）
        _seed("- v2.0（2026-02-02）：唯一条目\n- v2.1（2026-02-03）：第二条\n")
        r_two = _stage("- v2.1（2026-02-03）：第二条\n")
        j4["G9 身份数<3 不入域→放行(阈值语义自证)"] = (r_two.returncode == 0)
        # G10＝J4D 分档回归：表格行族身份丢失 → ⚪ 显形不拦（生成器整写/索引重建属设计内）
        ROWS = ("| 2026-05-01 | WorkBuddy | 某件A.md | v1 | 甲描述 |\n"
                "| 2026-05-02 | ZCode | 某件B.md | v2 | 乙描述 |\n"
                "| 2026-05-03 | Qoder CN | 某件C.md | v3 | 丙描述 |\n")
        _seed(ROWS)
        r_row = _stage(ROWS.replace("| 2026-05-02 | ZCode | 某件B.md | v2 | 乙描述 |\n", ""))
        o_row = (r_row.stdout + r_row.stderr).decode("utf-8", "replace")
        j4["G10 表格行身份丢失→⚪ 显形不拦(J4D 分档)"] = (r_row.returncode == 0 and "⚪ J4D" in o_row)
        # G11＝升红闸的**两向**自证（只测"能转红"或只测"不转红"都算判据缺一半·§3.5）
        global J4D_PROMOTE_READY
        keep_ready = J4D_PROMOTE_READY
        try:
            late_off = blocking_set("2026-12-01")                       # 到期但前置未满足
            J4D_PROMOTE_READY = True
            late_on = blocking_set("2026-12-01")                        # 到期且前置满足
            early_on = blocking_set("2026-10-01")                       # 未到期但前置满足（两因各留一false）
        finally:
            J4D_PROMOTE_READY = keep_ready
        j4["G11a 到期·前置未满足→不转红（复核日语义）"] = ("J4D" not in late_off)
        j4["G11b 到期·前置满足→转红（开关承重·非死代码）"] = ("J4D" in late_on and "J4D" not in BLOCKING)
        j4["G11c 未到期→不转红"] = ("J4D" not in early_on)
        for k, v in j4.items():
            print(f"  夹具 {k}：{'✅' if v else '❌'}")
        ok_j4 = all(j4.values())
        return 0 if (ok_clean and ok_block and ok_stock and ok_j4) else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--baseline-write", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("paths", nargs="*")
    a, unknown = ap.parse_known_args()
    if unknown:
        print("MD_GUARD:FAIL 未知参数 " + " ".join(unknown), file=sys.stderr)
        return 2
    global BLOCKING
    import datetime
    only = {x.strip().upper() for x in a.only.split(",") if x.strip()} or {"J1", "J1F", "J2", "J4", "J4D"}
    # ⛔ 此处原先写 `BLOCKING = BLOCKING | {"J2"}`——函数内赋值造局部变量，全局从未变，
    # "到期自动转红"因此是死代码（假绿）。生效点收进 blocking_set() 单一真相源（D29）。
    bad = only - {"J1", "J1F", "J2", "J4", "J4D"}
    if bad:
        print(f"MD_GUARD:FAIL --only 取值非法 {sorted(bad)}", file=sys.stderr)
        return 2
    root = resolve_base(a.paths[0] if a.paths and (a.scan or a.check or a.baseline_write) else None)
    if a.baseline_write:
        # 名单必须按**到期日那天会被执行的判据集**生成：只按当前 BLOCKING 生成＝J2 的 223 处
        # 在 10-31 当天全是"名单外新债"，分批升红退化成一次引爆（D29 拆弹·2026-09-19）。
        red, _ = walk(root, {"J1", "J1F", "J2"})
        enforce_at_dl = blocking_set(J2_PROMOTE_DEADLINE)
        srcs = {}
        keys = []
        for rel, ln, k, _ in red:
            if k not in enforce_at_dl:
                continue
            f = rel if os.path.isabs(rel) else os.path.join(root, rel)
            if f not in srcs:
                try:
                    srcs[f] = open(f, encoding="utf-8").read().split("\n")
                except OSError:
                    srcs[f] = []
            keys.append(f"{os.path.relpath(f, root)}␟{k}␟{row_key(srcs[f][ln - 1] if ln - 1 < len(srcs[f]) else '')}")
        write_stock(keys)
        return 0
    if a.self_test:
        return run_self_test(only)
    if a.scan:
        return cmd_report(root, only, strict=False)
    if a.check:
        return cmd_report(root, only, strict=True)
    if a.gate:
        files = [p for p in a.paths if p.endswith(".md")]
        return cmd_gate(files, only, root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
