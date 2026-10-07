#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.20（2026-10-07 Qoder CN·报警噪声根治任务卡步1·皮叔令"彻底做完"）：**提醒面分级**——delta 两类成员分流：具名真崩照进 Stop 强提醒（⛔不放宽红线保持），归因缺口(unattributed·r[3] None)降级 hook_alert_deferred.jsonl 台账不敲门。判据与渲染同源(r[3]即"exit="渲染位)，⛔不新建取数集；report 面零改动（对账仍在）；分级逻辑抽纯函数 _split_alert_tiers+自测2例钉双向（缺口降级+混崩不静默）。步2退出码语义统一后此类源头收敛，deferred台账=步2排雷清单。\n# version: v0.19（2026-10-07 Qoder CN·Stop 提醒面"🔴真崩1(unattributed grep_sand)"同族假红根治）：具名通道 unk_re 要求 `, stderr: ` 后缀，而产品对**空 stderr 的阻断钩子**只落 `  <cmd>: unknown error, exit code N`（真机取证 qodercli.log 12:32/12:35 两例，grep_sandbox_guard exit=2 拦截成功、stderr 段缺省）⇒ 具名证据漏扫、batch 声明永不配对 ⇒ 差额恒记"⚠️产品声明失败、无具名证据"、每轮 Stop 跟喊=狼来了（守卫自身反模式）。修法=UNK_RE 提为模块级、stderr 组改可选 `(?:, stderr: (.*))?`（⛔判据强度不动：真无具名证据照记 unattributed，32b 钉住）；变异位 32e=置回严格正则→32 必翻。BLOCK_SIGNALS=100 对照证明其余拦截配对本正常，本案是形状残差非通路全断。自测 53→57/0。
# version: v0.18（2026-10-07 Qoder CN·Stop 守卫报警处置）：①**mount_args_smoke 委托真源假红根治**——判活行「🔴挂载参数脚本不认识3条(每轮崩)」系假红：06:57 一笔未提交的"去机名"半截改动把 hps 指到 ~/脚本中心/hook_protocol.py（该处只有 logs/runtime 共享台账·⛔无 .py 本体），委托例外永不生效；反证=产品日志 unrecognized arguments 计数 0 + 三钩子本会话注入真实到达。修法=hps 改本脚本同目录推导（去机名+不断链双目标同时满足），~/脚本中心 留作回退。sys.path/HP_LEDGER 两处同批改动经与真源 hook_protocol.py L67 比对为**正确**（台账确实写 ~/脚本中心/logs·今日 07:01 实写在场），不动。②**BASELINE 收编 6 条实挂未登记**（实挂63>基准57）：SubagentStop subagent_evidence_guard、Stop path_landing_truth_guard --report/devtools_single_source_guard --json/asyncrewake_probe、PreToolUse hook_probe/asyncrewake_probe——本文件自己写过五次的教训「挂载与基准登记必须同轮」第五次重演。⚠️ 探针两枚（hook_probe/asyncrewake_probe）为临时资产，**退役时须同轮从基准销账**（否则 MISSING「应挂未挂」反向假红）。自测+真机 check 复跑验证。
# version: v0.15（2026-10-02 Qoder CN 童灵 D3·哲学读侧完整性专项 P0）：BASELINE 的 UserPromptSubmit 收编 `philosophy_radar_inject.py`——哲学变更雷达到达腿钩子（读 logs/philosophy_radar.jsonl，非空则会话首轮注入 ≤5 行·空则静默零开销·launchd com.buluotuo.philosophy-radar 每日承载）。按 v0.5/v0.8/v0.11/v0.12 血案教训：挂载与基准登记同轮，本轮 settings.json UPS +1 与 BASELINE +1 一并落。收编非放宽：脚本在盘 + py_compile 通过 + seed 登记承诺 + 双向实测（首轮注入JSON／同会话二轮静默／空雷达静默）。
# version: v0.14（2026-10-02 Qoder CN 童灵 D3·工单 2026-10-02-configguard提醒面假红修复）：**提醒面与 report 窗口判据同源**——同族病「判据对、展示错」的收尾（声明/具名 key 不同源→展示未绑恢复→提醒面取存量，三案一个根）。案件地面真值：13:13 Stop 提醒「🔴钩子真崩1(最近:qodercn_config_guard.py exit=—)」而 report 窗口真崩0/check OK/CLI runs grep 零命中。修A=unattributed 差额行 ts 落回**其自身声明时刻**（`_pair_unproven` 尾贪心配对），⛔不再取「该 key 最近一次声明时刻」借壳——该形状 v0.13 头注点过名但只修 key 未修 ts（真机探针复现：存量差额+窗口内新声明有证据→旧实现真崩1，修复后落 ⚪ 存量）。修B=超时豁免补「当轮自证」证据源（`_self_probe_exempts`：本钩子正在执行=「同命令其后成功」的硬事实，仅同脚本名适用）——v0.11 只看落盘回执，对「确认恢复的回执恰由当轮写入、扫描时物理不可见」结构性失明=恢复确认滞后一轮，本案真凶。验收双向夹具钉死（30-pre/30/30b/30e+31/31e）：存量有旧崩+窗口零崩→提醒静默；窗口内真崩→照常红 ⛔不修成失明。自测 47→53/0·变异两处→四处（30e/31e 入 _mut）。**存量 12 条定谳**（清头注 v0.2「⛔也不等于已修」欠账）：①09-02 rule_three_layer_guard TypeError×7 + 09-12 --deliver×1=v0.2（09-12）已修；②09-12 l3_conclusion_guard exit2×1=该守卫 09-05 你令永久退役（规范 §3.4·扩 呈现格式禁拦律），退役即终态·无法追认销账；③09-26 tsl_closeout×1=同日 UnboundLocalError `_tr` 撞名已修（系统日志 09-26·E2E 用例 11/11 承接）；④09-12 unattributed×3=v0.2/v0.13 同源对账清路。全部 12 条=历史已清·⛔不再以「未修」复报。真机 check OK·提醒行复跑静默。
# version: v0.13（2026-10-01 Qoder CN·"🔴钩子真崩3"假红归因根治）：**声明侧对账 key 与具名侧同源**——batch 通道（产品聚合行 `Hook execution for E: N succeeded, M failed (<cmd>)`）原先用 BASELINE 短针子造 key，具名通道（hr_re/unk_re）走 `_match` 实盘优先最长匹配 ⇒ 同一钩子两份证据各归各 key，永远对不上。病灶实锤：`rule_three_layer_guard.py` 声明 9 条 = 具名 6（短针子）+ 3（实挂带 `--deliver` 的长针子），差额恒 3 全记"⚠️产品声明失败、无具名证据"，且 ts 取最近一次声明 ⇒ 三条假红**同时钟**落进当前窗口 → "🔴钩子真崩3 exit=—"（真崩 0）。v0.9 把判活改绑实盘时漏了这一路（守卫病2「判据未随对象演化」同族）。修法=换 key 归属，⛔不改判据强度：真拿不到具名证据时差额照记 unattributed（自测 29b 钉住）。自测 43→46/0，新增 29-pre/29/29b 三例；⚠️夹具两枚地雷已写进注释（日志须 `<runs>/<run>/*.log` 两层；QCN_SETTINGS 此处已被 GUI 用例切走，写回 sfile 是惰性操作→首版 29 在变异体上照样绿＝自测恒真，加 29-pre 分辨条件自证）。真机 liveness 真崩 0/check OK。
# version: v0.12（2026-09-26 Qoder CN 童灵·自查）：Stop 基准收编 doenglingz_level_declare_guard.py + tsl_closeout_guard.py（本端补挂两件·实挂 30→32→基准同步）。**第四次重演本文件自己写的教训**"挂载与基准登记必须同轮"（v0.5/v0.8/v0.11 三次），已记 LRN-20260926-013·主挂 PAT-042。
# version: v0.11（2026-09-22 Qoder CN 童灵 D3·皮叔令「落实立场卡触发台账 3 工作」）：BASELINE 的 Stop 收编 record_card_trigger.py（立场卡触发事件自动登记钩子·基准 Stop 18→19 条）。按 v0.5/v0.8/v0.9 同轮登记教训：挂载与基准登记必须同轮，否则新钩子首响即被报「⚠️多余1」。脚本在盘 + 自测 PASS（strip 注入防虚报 / 幂等 / fail-open）+ settings.json Stop 已挂（11→12 组）。
# version: v0.11（2026-09-23 Qoder CN·Stop 09:54 超时击杀反哺）：**超时自恢复豁免**——crash 分类不动（超时仍朝红 L649 原意），仅当同命令其后出现成功/送达回执时该条降 ⚪（偶发 IO 抖动已自恢复，⛔无链改动时单次超时挂红数天=09-12"狼来了"案变体）。夹具双反例 10b/10c（无恢复必红/有恢复才免）。触发实录：本端守卫自身 Stop 执行 09:54:37 被产品 timed out，窗口内红挂起；10:05 同链成功回执后应回落。真机 check OK·全量自测复跑不降。
# version: v0.10（2026-09-21 Qoder CN·Stop 自激假红反哺）：**回显过滤补"终端命令回显"形状**——`"command":`/`"command_names":`/`Handling plugin command`/`Running command:`/`actualCommand`/`ExecuteStrategy` 六特征并入 isecho 通道。根因实锤：排查"exit=126 真崩"告警的 grep 命令文本被产品回写日志，unk_re 匹配 JSON 转位子串 → 守卫把告警排查读成真崩（假红自激环）。真机 check OK·全量自测复跑不降。
# version: v0.9（2026-09-20 11:45·Qoder CN 童灵 D3·皮叔令「启动童灵，彻底根治解决」）：①**判活对象由 BASELINE 改绑实盘挂载**——v0.7 把事件归属改读实盘后，实挂针子（带 --hook-protocol=json/--deliver 等参数）比 BASELINE 针子长 ⇒ _match 最长匹配把回执全记到实挂针子名下，BASELINE 短针子自 09-02T15:47 冻结 ⇒ 5 钩子假红 18 天（route/kb_inject/doenglingz/position3/rule_three_layer·守卫病2「判据未随对象演化=假红」同族）。修法：liveness 判活按实盘 (evt,needle) 逐钩评估，BASELINE 针子被同事件实挂针子包含时跳过（superseded——回执已归实挂针子，单判=重复计账），BASELINE 未挂载条目保留（never 检测=「应挂未挂」仍在场）。②**协议留痕 host 异常判据收窄到本端发送**——hook_protocol_ledger 机器本地多端共写（zcode 866 条实测混入本端报警），本端行 qoder_env 非空、他端行 []，不收窄=跨端仪器污染。真机 check OK·超龄0/多余0。
# version: v0.4（2026-09-18 Qoder CN）：Stop 基准 +1 条 delivery_boundary_guard（实挂 23→24·报警系 EXTRA 非 MISSING）
# version: v0.9（2026-09-20 Qoder CN 童灵 D3）：BASELINE 的 UserPromptSubmit 收编 `qodercn_title_namer.py`——会话标题自动命名适配器（session_title_utils 原语接入·本端第 4 端落地）。⚠️ 重演 v0.5/v0.8 已写明的教训：挂载（11:36）与基准登记未同轮 → 新钩子被 Stop 守卫首响报「⚠️多余1」。收编非放宽：脚本在盘 + git tracked（6e6eb00c）+ 系统日志有条目。
# version: v0.5（2026-09-19 08:40 Qoder CN 童灵·皮叔令「启动童灵，根治这个风险」）：BASELINE 补 PreToolUse 键收 stamp_precheck_guard.py——该钩子每次成功拦截都被本守卫报成「🔴钩子真崩」（无名缩进续行不带事件名，靠基准反查；缺基准⇒exit2 落 HARD_EXIT_CODES）；自测 +27/27b/27c 三例（阻断归因·异常证据优先仍判崩·未登记钩子仍判崩＝证明绿来自登记而非放宽）→ 37/37；真机 check 由 FAIL 转 OK
# version: v0.8（09-19 12:20·Qoder CN 童灵·皮叔令「剩下的按三明智建议做完」）：**BASELINE 的 Stop 收编 `triwich_closeout_guard.py --report`**——本端首次挂载三明智收尾守卫（Stop 16→17）。今日两次报警教训反哺用法：挂载与基准登记**必须同轮**，否则新钩子首响即被报成真崩（D22/D23 同型）；本版按 v0.7 的实盘归属口径挂载，归属不再依赖登记，但欠账对账仍需基准。自测 41/41·check OK（真崩0/超龄0/多余0）。
# version: v0.7（2026-09-19 11:14·Qoder CN 童灵·皮叔令「按符合愿景的最优解＋别再重演三明智那条脚本被永久关闭」·工单 D23 裁决）：**事件归属的权威源由 BASELINE 改为实盘 settings.json**——登记面退回只管"有无欠账"（MISSING/EXTRA 双向不变）。为什么必须改：v0.5/v0.6 靠 BASELINE 反查事件，未登记的阻断型钩子每成功 exit2 拦一次就被报一次「🔴钩子真崩」，即**拿假红当逼迫器**；l3_conclusion_guard 就是被三次误拦推到全端永久关闭的（§3.4·扩 呈现格式禁拦律同族：判据不可穷尽时不得进阻断层，而"命令→事件"的映射空间本就有限可穷尽，没有理由用反查凑数）。27c 拆双向＋27e 两向变异（置假实盘归属⇒同一条判据必须翻假·反证 B 实现下 27c/27e 双双转红）＋27d 回落负例。同轮另抓出并删除 126 行**逐字遮蔽副本**（check/HARD_EXIT_CODES/_classify_record 等 9 符号×2，v0.6 撤销不彻底所致，且 v0.6 头部"经符号唯一性清点确认无重复定义残留"一说是**只点了自己想到的三个符号**——已就此作废并补自测第 28 例「本体顶层符号唯一」当物理承接器）。自测 37→41/41、真机 check OK。
# version: v0.6（2026-09-19 10:24·Qoder CN 童灵·本端自己踩出）：①BASELINE 的 PreToolUse 收编 `registry_precheck_guard.py`（本端 10:18 挂载后未登记 → 同时报「⚠️多余1」与「🔴钩子真崩1」，而该 exit=2 其实是它**成功拦下**一次无登记承诺的落笔）。②曾尝试把「事件归属」改读实挂配置（让分类不再依赖登记），被本文件 v0.5 的既有用例 27c 顶回——该用例显式断言「未登记钩子的 exit2 仍判真崩·证明 27 的绿来自登记不是靠放宽」＝有意的逼迫式设计。**已撤销该改动**（⛔不在并发对手正在改的同一文件里静默翻转其判据），分歧带证据立案 **D23** 待一次裁决，不在两处各写一半；撤销后经符号清点确认无重复定义残留（见 QCN-20260919-003）。
"""
qodercn_config_guard.py — Qoder CN 专属守卫：配置形态完整性 + 产品回执活性（防本端静默脱网）
==========================================================================================
根因（2026-08-29 立·皮叔令"你说的两点要从根上解决·符合愿景"）：
  ①「声明-实盘脱钩已在本端实锤」：settings.json 里 9 条 Stop 项写成扁平
    `{"command": ...}`（缺 `hooks:[...]` 包裹），产品 schema 只认包裹形态 →
    其中 4 条唯一守卫（platform_adaptation_check / post_change_guard /
    qodercn_inject_chain_guard / doenglingz_guard）**从未被执行**，产品回执 0 条。
    而 platform_adaptation_check.py:153 的宽松读取（`elif "command" in h`）
    把死挂载计入"已挂"→ 面板 13/13 与实盘 9 条背离（仪器盲区）。
  ②「活性不可证」：旧 liveness 靠 route_audit.jsonl 出现 src 记录做代理，
    静默通道（如 position3_notify 在 red=0 时不输出）永远无法自证。
    实测发现产品自己在 `~/.qoder-cn/logs/runs/*/qodercli.log` 留了
    `hook.started/hook.finished` 回执（含 display_text/exit_code/duration_ms）
    → 每条钩子"是否真被调用"变成机械可判定，⛔不需要等异常发生、不依赖人记得。

子命令：
  check      校验 settings.json 钩子：条数=基准 + 形态合法（包裹在 hooks[] 内）
             → 缺失 / 死形态（扁平不执行）/ 意外多余；exit 0=干净 / 1=有异常
  liveness   解析产品回执台账：基准每条命令的 started 命中数 + 最近时间；
             user 源 finished 里的失败回执计数 → 零回执分两类：
             🔴从未执行 / ⏳待首个周期（settings.json 比该链最近回执更新且未过 24h 宽限）
  hook       Stop 钩子模式：跑 check+liveness，异常→stdout 一行强提醒；
             任何失败 exit 0 放行（Hook 三纪律·报告制不拦截·只检测不修改）；
             ⏳待周期不进入强提醒（防"狼来了"致报警贬值）
  --self-test 53 用例（临时 HOME/日志目录·不碰真配置·含显式「负例」证明会报警；
                ⚠️ 此处数字是快照·会以滞后，例数唯一真源=`--self-test` 末行"自测结果：N 通过"）

用法：
  python3 qodercn_config_guard.py check
  python3 qodercn_config_guard.py liveness
  python3 qodercn_config_guard.py hook          # Stop 挂装入口
 env 覆盖（自测用）：QCN_SETTINGS / QCN_LOG_RUNS / QCN_GUARD_STATE
 基准真相源：本文件 BASELINE（端专属·不计入 12-Hook 共享分母·先例 zcode_config_guard）

变更记录
  v0.5（2026-09-19 08:40·Qoder CN 童灵 D22 根治）：**BASELINE 补 PreToolUse 键**收 stamp_precheck_guard.py。根因不是分类器缺 block 分支（BLOCKABLE_EVENTS 早已含 PreToolUse），而是产品的 `  <cmd>: unknown error, exit code N, stderr: ...` 续行**不带事件名**，本守卫靠 _match(cmd) 从 BASELINE 反查事件——钩子未登记 ⇒ evt="" ⇒ `code==2 and evt in BLOCKABLE_EVENTS` 不成立 ⇒ 落 HARD_EXIT_CODES 判真崩。⇒ 一条欠账同时造出两个症状（EXTRA 未入库 + 🔴真崩假红），补基准后两红同消。自测 34→37/37：27（阻断归因）·27b（异常证据优先·不得把崩溃一起放绿）·27c（未登记钩子仍判崩＝证明修复是登记而非放宽）。⚠️ 本文件既有欠账：变更记录只到 v0.2，v0.3/v0.4 明细缺失（版本行领先记录面）——本轮如实点名不代补写历史。
  v0.2（2026-09-12·皮叔令"按愿景第一性原理最优解根治"）：报警层三缺陷根治——
    ① 崩溃判据由无名异步的 hook.finished 改绑产品**具名**通道（[HookRunner] + 裸缩进
       unknown-error 行），自家 --deliver/hook 的 exit 2 归送达/阻断（假红源头）；
    ② 真崩计数加时间窗 _hook_chain_mtime()，窗口前旧账降 ⚪存量单列（告警随修复回落）；
    ③ GUI 判活源 0 字节空转 → 🟡单源降级显形（⛔不再按双源静默结案）；
    ④ 声明-归因对账按 (event, needle) 逐钩子，差额记 unattributed 朝红；一条回执只归
       一个基准（最长子串匹配）；两源共用 _classify_record 与同一记录形状；
    ⑤ 证据裁剪 _clip_err 取代 stderr[:120] 前缀（原因在末行），GUI stderr 块按行保留。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import json
import os
import re
import subprocess
import sys
from collections import namedtuple
from datetime import datetime

# 送达律（2026-09-05·报警侧收讫）：投递/节流/收讫核逻辑收敛在协议真源，避免双实现漂移
sys.path.insert(0, os.path.expanduser("[记忆共享中心]/脚本中心"))
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

SETTINGS_DEFAULT = os.path.expanduser("~/.qoder-cn/settings.json")
LOG_RUNS_DEFAULT = os.path.expanduser("~/.qoder-cn/logs/runs")
STATE_DEFAULT = os.path.expanduser("~/.qoder-cn/logs/qodercn_config_guard_state.json")
# 2026-09-04 新增两源：注入协议留痕台账 + GUI 真实回执日志（questWindow）
HP_LEDGER_DEFAULT = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime/hook_protocol_ledger.jsonl")
GUI_HOOKS_LOG_DEFAULT = os.path.expanduser("~/Library/Application Support/QoderCN/logs")
INJECT_ROUNDS_WINDOW_MIN = 30   # 对账窗口（分钟）
RUNS_STALE_HOURS = 6            # CLI 判活源停更阈值（小时）
STALE_DAYS = 7
# 宽限期：settings.json 刚被改过、该事件周期尚未到来时，零回执属"待观察"而非"真失效"
# （2026-08-29 实测：修复后本进程仅有 UPS/SessionStart 回执，Stop 周期一次没跑过——
#   把这种态判成 🔴 会让守卫天天喊狼来了，报警价值归零）
PENDING_GRACE_HOURS = 24
# 官方文档：仅这两个事件可阻断（exit 2 = 阻断信号）；其余事件的 exit 2 属脚本报错。
# ⚠️ 族名判据（2026-08-29 20:33 全量 tally 实测）：本端真实出现过的 hook_name 只有
#    "UserPromptSubmit" / "SessionStart:<kind>" / "Stop" / "PreToolUse[:<tool>]"。曾疑似存在
#    变体 "PreToolUseMatcher"——实为**本会话自己的 grep 命令被 tool.requested 回显**进日志，
#    严格式（\] hook\.started hook_name=…）匹配数为 0。教训：本端日志全文回显工具命令行，
#    ⛔"某字符串在日志里出现"≠"产品产生了该回执"，必须锚 hook.started/hook.finished 全式。
BLOCKABLE_EVENTS = ("UserPromptSubmit", "PreToolUse")

# 基准条数 = sum(len(BASELINE)) 由代码动态求（⛔注释里不写死数字——清单一演化注释就与代码自相矛盾）
# 2026-09-18 补：UserPromptSubmit 两条实挂守卫入基准（secret_key_guard / ttl_expiry_guard）——
#   逐条核过：脚本在盘 + git tracked + §四注册表有行 + 产品回执 hook.started 命中 ⇒ 判定为「基准滞后」，
#   ⛔不是「越权挂载」。补基准前若只按报警删钩子＝把在跑的隐私/时效守卫静默拆掉（真红被当噪声处理）。
# 历史注：2026-09-05 补 Stop 一条——gate_runner.py 报告制挂载（契约⑤「G2 由 gate_runner 挂 Stop 机械兜底」在本端取得载体；⛔不带 --block-on-red）
# 比对用"脚本名+关键参数"子串——命令绝对路径前缀允许变化（先例 zcode_config_guard）
BASELINE = {
    # 2026-10-04 T0 官方事件派发探针（推进文件B段·qodercn_hook_probe.py 恒exit0报告制·探针期条目·收口后挂载与基准同轮摘除）
    "SessionEnd": ["qodercn_hook_probe.py"],
    "PostToolUse": ["qodercn_hook_probe.py"],
    "PostToolUseFailure": ["qodercn_hook_probe.py"],  # v0.17(10-04) B3负证据定谳：prompt/agent型本端不派发(parallel=1+零回执)，挂载与基准同轮摘除
    "PermissionRequest": ["qodercn_hook_probe.py"],
    "PermissionDenied": ["qodercn_hook_probe.py"],
    "StopFailure": ["qodercn_hook_probe.py"],
    "SubagentStart": ["qodercn_hook_probe.py"],
    "SubagentStop": ["qodercn_hook_probe.py",
                     "qodercn_subagent_evidence_guard.py"],  # v0.18 补：W1 对账链证据守卫（实挂未登记）
    "PreCompact": ["qodercn_hook_probe.py"],
    "PostCompact": ["qodercn_hook_probe.py"],
    "Notification": ["qodercn_hook_probe.py"],
    "InstructionsLoaded": ["qodercn_hook_probe.py"],
    "ConfigChange": ["qodercn_hook_probe.py"],
    "CwdChanged": ["qodercn_hook_probe.py"],
    "FileChanged": ["qodercn_hook_probe.py"],
    "SessionStart": [
        "crossend_guard.py",
    ],
    # PreToolUse（2026-09-19 v0.5 补键）：⛔漏登记的症状分两段史——
    # v0.5 时代：产品的 unknown-error 缩进续行**不带事件名**，事件靠 _match(cmd) 从基准反查，查不到 ⇒ evt=""
    #   ⇒ 阻断型钩子每次成功 exit2 都被报「🔴钩子真崩」（08:11 stamp_precheck、10:18 registry_precheck 两次实测）。
    #   当时的处置=补基准。v0.7（工单 D23 裁决）把**归属**改读实盘 settings.json，本表退回只管"有无欠账"——
    #   "报警说谎"与"欠账显形"是两件事，⛔不该用前者给后者付账（假红攒够＝守卫被永久关闭，l3_conclusion_guard 先例）。
    "PreToolUse": [
        # v0.18（2026-10-07）补登记：实挂63>基准57 六条欠账（挂载早基准迟=同轮教训再重演）
        "qodercn_hook_probe.py",            # T0 派发探针·探针期条目·退役须同轮销账
        "qodercn_asyncrewake_probe.py",     # asyncRewake 效力探针（10-06 挂载·双事件）
        "stamp_precheck_guard.py",
        "registry_precheck_guard.py",
        # 2026-10-03 v2.0.0 全平台安装器补装·同轮登记（挂载与基准同轮·v0.8 先例）
        "edit_heading_guard.py",
        "grep_sandbox_guard.py",
        "skill_spec_read_guard.py",
        "skill_write_gate_guard.py",
    ],
    "UserPromptSubmit": [
        "route_inject_prompt.py UserPromptSubmit",
        "route_miss_feeder.py",
        "kb_inject_prompt.py UserPromptSubmit",
        "doenglingz_inject_prompt.py",
        "position3_notify.py",
        "secret_key_guard.py",
        "ttl_expiry_guard.py",
        "qodercn_title_namer.py",
        "philosophy_radar_inject.py UserPromptSubmit",
        # 2026-10-03 v2.0.0 安装器补装·同轮登记
        "rule_fragment_inject.py",
        "session_tail_inject.py",
        "qodercn_hook_probe.py",
    ],
    # 2026-10-03 "crossend_guard.py --stop" 孤儿挂载撤除（新版脚本不读argv·Stop侧第一类扫描职责
    #   由 doenglingz_guard 每轮承载且带台账 leak_entry_files 字段；ROSTER 亦无此条——本端向新用户装机态对齐）
    "Stop": [
        "route_unknown_unknown.py",
        "audit_search_kb.py",
        "route_audit.py --src qodercn",
        "route_guard_audit.py",
        "card_id_guard.py hook",
        "feedback_detect.py",
        "rule_three_layer_guard.py",
        "platform_adaptation_check.py --src qoder-cn --fix",
        "post_change_guard.py --src qoder-cn",
        "qodercn_inject_chain_guard.py",
        "doenglingz_guard.py",
        "qodercn_config_guard.py hook",
        "systemlog_stophook_check.py",
        "gate_runner.py",
        "delivery_boundary_guard.py",
        "triwich_closeout_guard.py --report",
        # v0.12（2026-09-26·Qoder CN）：本端补挂 TSL/D 轴两件守卫并同轮登记基准。
        #   ⛔本文件 changelog 已三次写"挂载与基准登记必须同轮，否则新钩子首响即被报⚠️多余1"
        #   （v0.5/v0.8/v0.11），本轮第四次重演——补挂当轮只改了 settings.json 没动基准，
        #   于是 tsl_closeout 一上线就同时吃了「多余1」与「真崩 exit=1」两条报警。
        "doenglingz_level_declare_guard.py",
        "tsl_closeout_guard.py",
        "report_backlog_guard.py --json",
        "record_card_trigger.py",
        # 2026-10-03 v2.0.0 安装器补装·同轮登记
        "reply_tail_guard.py",
        "twin_changelog_guard.py",
        "twin_verdict_ledger.py",
        # v0.18（2026-10-07）补登记：常驻守卫两条 + asyncRewake 探针（探针退役须同轮销账）
        "path_landing_truth_guard.py --report",
        "devtools_single_source_guard.py --json",
        "qodercn_asyncrewake_probe.py",
    ],
}


def _settings_path():
    """动态读 env——模块级求值会让自测覆盖无效（zcode_config_guard T2 教训）。"""
    return os.environ.get("QCN_SETTINGS", SETTINGS_DEFAULT)


def _runs_dir():
    return os.environ.get("QCN_LOG_RUNS", LOG_RUNS_DEFAULT)


def _state_path():
    return os.environ.get("QCN_GUARD_STATE", STATE_DEFAULT)


def _ts_to_dt(ts):
    """回执时间戳（2026-08-29T19:57:40.203+08:00）→ naive datetime（本机即 +08:00）。"""
    try:
        return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def _cfg_mtime():
    """settings.json 的修改时间——用于区分"真失效"与"刚挂载、该事件周期还没到"。"""
    try:
        return datetime.fromtimestamp(os.path.getmtime(_settings_path()))
    except Exception:
        return None


# 2026-09-19 v0.7 归属说明：本文件曾有 126 行逐字重复的遮蔽副本（check/HARD_EXIT_CODES/_classify_record 等 9 个符号×2，
# 后定义吃前定义·自测 37/37 分辨不出），由 QCN-20260919-003 的 grep 清点抓到并删除。防复发＝自测第 28 例「本体符号唯一性」。


def _needle_of(cmd):
    """实挂命令 → BASELINE 同格式的判别子串：`脚本基名 + 关键参数`（去解释器与路径前缀）。

    不这样归一的话，消费方（declared/named 对账、明细显示）会拿到整条绝对路径命令＝与他处口径不同源。
    """
    toks = cmd.strip().split()
    for i, t in enumerate(toks):
        if t.endswith((".py", ".sh", ".js", ".ps1")):
            return " ".join([os.path.basename(t)] + toks[i + 1:]).strip()
    return cmd.strip()


_MOUNT_MEM = {"key": None, "pairs": None}


def _mounted_pairs():
    """实挂 (事件, 判别子串) 列表——事件归属的**权威源**（settings.json）。

    读不到/解析失败 → 返回 None，由 `_match()` 回落到 BASELINE 反查（回落律：无从对账=保持旧行为，
    ⛔不静默失明也不造假红）。扁平死形态同样收录：它带事件字段，分类不该因挂载形态而瞎。
    """
    key = (_settings_path(), _cfg_mtime())
    if _MOUNT_MEM["key"] == key:
        return _MOUNT_MEM["pairs"]
    pairs = None
    try:
        root = json.load(open(key[0], encoding="utf-8"))
        pairs = []
        for evt, groups in (root.get("hooks") or {}).items():
            for g in (groups if isinstance(groups, list) else []):
                if not isinstance(g, dict):
                    continue
                inner = g.get("hooks")
                src_ = inner if isinstance(inner, list) else [g]
                for h in src_:
                    if not isinstance(h, dict):
                        continue
                    c = h.get("command", "")
                    if c:
                        pairs.append((evt, _needle_of(c)))
                    elif h.get("name"):
                        # N1(2026-10-04)：非command型钩子以 name 为判别针子
                        pairs.append((evt, h.get("name")))
    except Exception:
        pairs = None
    _MOUNT_MEM["key"], _MOUNT_MEM["pairs"] = key, pairs
    return pairs


def _match(cmd):
    """命令串 → (事件, 判别子串) 取**最长匹配**；均不命中返回 (None, None)。

    归属权威源 = 实盘 settings.json，BASELINE 只作回落与欠账对账（v0.7·工单 D23 裁决）。
    为什么不再让登记面单独决定归属：登记是"有没有欠账"的证据源，不是"这条命令属于哪个事件"的证据源。
    产品的 unknown-error 续行不带事件名，旧实现只能从 BASELINE 反查 ⇒ 未登记的阻断型钩子
    **每成功 exit 2 拦一次就被报一次「🔴钩子真崩」**——报警说谎的代价由谁付？由下一个想关掉
    这条守卫的人付（l3_conclusion_guard 就是这么被永久关闭的，见 §3.4·扩 呈现格式禁拦律）。
    漏登记的逼迫器不取消，改由 `check()` 的「⚠️实挂>基准」显形承担：27c 双向钉住"分类不失真 且 欠账仍在"。
    同长度时实盘优先（src=1）——实盘比基准更近真相。
    """
    cands = [(n, evt, 1) for evt, n in (_mounted_pairs() or [])] + \
            [(n, evt, 0) for evt, needles in BASELINE.items() for n in needles]
    best = (None, None)
    rank = (-1, -1)
    for n, evt, src in cands:
        if n in cmd:
            r = (len(n), src)
            if r > rank:
                rank, best = r, (evt, n)
    return best


def check():
    """返回 (缺失列表, 死形态列表, 意外多余列表, 已挂总数)。"""
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            root = json.load(f)
    except Exception as e:
        return ["⛔ settings.json 读取失败: %s" % e], [], [], 0
    hooks = root.get("hooks", {})
    missing, dead_shape, mounted = [], [], 0
    live_cmds = []
    for evt, groups in hooks.items():
        for g in groups:
            if isinstance(g, dict) and "hooks" in g:
                for h in g["hooks"]:
                    c = h.get("command", "") if isinstance(h, dict) else ""
                    if not c and isinstance(h, dict) and h.get("name"):
                        c = "@%s:%s" % (h.get("type", "?"), h.get("name"))
                    live_cmds.append((evt, c))
            elif isinstance(g, dict) and "command" in g:
                # 扁平形态：产品不执行 → 死挂载
                dead_shape.append("%s: %s" % (evt, g["command"]))
    mounted = len(live_cmds)
    for evt, needles in BASELINE.items():
        have = [c for e, c in live_cmds if e == evt]
        for n in needles:
            if not any(n in c for c in have):
                missing.append("%s: %s" % (evt, n))
    expect = sum(len(v) for v in BASELINE.values())
    extra = []
    if mounted > expect:
        extra.append("实挂 %d 条 > 基准 %d 条（有新增未登记守卫·须补基准）" % (mounted, expect))
    return missing, dead_shape, extra, mounted


HARD_EXIT_CODES = (2, 126, 127, 128, 130)  # 2=Stop 侧打不开文件(08-29 实测)；126/127=不可执行/找不到；128/130=信号终止

# 崩溃证据（2026-09-12 根治·判据绑定被检对象）：产品在同一条 [HookRunner] 行里
# 同时给出 命令名 + 事件 + exit code + stderr 首行，所以"是不是崩了"看 stderr 证据，
# ⛔不再靠 exit code 猜——旧判据把 exit 1（守卫"我检出了问题"的设计语义）与
# Traceback（真崩）混为一谈，又把自家 --deliver 的 exit 2 记成崩溃。
CRASH_EVIDENCE_RE = re.compile(
    r"Traceback|can't open file|No such file or directory|UsageError|unrecognized arguments|"
    r"SyntaxError|IndentationError|MemoryError|Killed|Segmentation fault")
DELIVERY_CMD_MARKS = ("--deliver", " hook")  # 送达模式：钩子用 exit 2 把告警顶进会话

# v0.19：具名通道正则提为模块级（自测 32e 可整路置假——§3.9 与 _declared_key 同构）。
# stderr 段=可选：产品对空 stderr 的阻断钩子只落 `  <cmd>: unknown error, exit code N`
# （真机 grep_sandbox_guard 两例取证），旧版要求 `, stderr: ` 后缀→具名漏扫→声明永不配对。
UNK_RE = re.compile(r"^\s{2,}(.+?): unknown error, exit code (-?\d+)(?:, stderr: (.*))?")


def _delivery_mode(cmd):
    return any(m in cmd for m in DELIVERY_CMD_MARKS)


def _classify_record(code, evt, cmd, stderr=""):
    """回执分类 → "ok"/"crash"/"block"/"delivery"/"design"。

    顺序即判据强度：①有异常证据一律真崩（⛔不因带 --deliver 就吞掉——旧 GUI 分支
    踩过这个坑，argparse 用法错误也是非零）；②可阻断事件的 exit 2 = 阻断信号；
    ③不可阻断事件（Stop）上送达模式的 exit 2 = 投递信号，非崩溃；④跑不起来类退出码；
    ⑤其余非零 = 守卫按设计报问题。
    """
    if code is None or code == 0:
        return "ok"
    if CRASH_EVIDENCE_RE.search(stderr or ""):
        return "crash"
    if code == 2 and evt in BLOCKABLE_EVENTS:
        return "block"
    if code == 2 and _delivery_mode(cmd):
        return "delivery"
    if code in HARD_EXIT_CODES:
        return "crash"
    return "design"


def _hook_chain_mtime():
    """真崩计数时间窗起点 = max(settings.json mtime, 所有被挂载钩子脚本 mtime)。

    病灶（2026-09-12 实测）：真崩计数全量扫历史回执、无时间窗 ⇒ TypeError 修完后
    `liveness` 仍报 CRASH_FAILURES 8（其中 6 条属 09-02 已 10 天），告警不随修复回落
    = 每轮喊狼来了，数轮内报警信用归零（与"预存态不算本端违规"归因律同族）。
    起点取"整条钩子链最后一次改动"：早于它的崩溃，其代码/配置都已不存在，
    不可归给现存形态；链上任一脚本改过即重开窗口——真崩若没修好会立刻在新窗口复发。
    取不到起点时返回 None ⇒ 全部计入 delta（⛔不放宽=朝红失败）。
    """
    marks = []
    try:
        marks.append(os.path.getmtime(_settings_path()))
    except Exception:
        pass
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            root = json.load(f)
    except Exception:
        root = {}
    for items in (root.get("hooks") or {}).values():
        for g in items if isinstance(items, list) else []:
            for h in (g.get("hooks") or [g]) if isinstance(g, dict) else []:
                cmd = h.get("command", "") if isinstance(h, dict) else ""
                for tok in cmd.split():
                    if not tok.endswith(".py"):
                        continue
                    try:
                        marks.append(os.path.getmtime(os.path.expanduser(tok)))
                    except Exception:
                        pass
    if not marks:
        return None
    return datetime.fromtimestamp(max(marks))


def _split_by_window(records, since):
    """按时间窗拆 (本轮 delta, 存量旧账)。since=None ⇒ 全归 delta（朝红）。

    记录形状 = (ts, cmd, evt, code, kind, stderr_head)。
    ts 为空（由聚合行倒推的无法归因项）一律归 delta——归因失败本身是病灶，
    ⛔不得因"没有时刻"就被判成存量而静默降级。
    """
    if since is None:
        return list(records), []
    cut = since.strftime("%Y-%m-%dT%H:%M:%S")
    fresh, old = [], []
    for r in records:
        ts = (r[0] or "")[:19]
        (old if ts and ts <= cut else fresh).append(r)
    return fresh, old


REC_FIELDS = ("ts", "cmd", "evt", "code", "kind", "stderr")

# 判活结果（2026-09-12 加 detail）：⛔不用裸 8 元组——新增字段会让旧位置解包静默错位，
# failures 的口径（本轮 delta vs 全量）必须能被消费方显式看到，故 detail 与 failures 同返。
Liveness = namedtuple("Liveness", "never stale failures blocks skipped hits pending nonzero detail")


def _clip_err(text, n=120):
    """证据裁剪：⛔不取前缀——崩溃原因在**最后一行**，首行只说"这里有个 traceback"。

    病灶（2026-09-12 自测 case 21 抓到）：`_RecSet.add` 曾写 `stderr[:120]`，中文长路径
    把 120 字符全部吃光 ⇒ 报警只剩 "Traceback (most recent call last): File \"/Users/…"，
    有证据却说不出的原因＝看得见红了、查不出为什么红。
    保留三段：首行（哪类异常）+ 最深的 .py 帧（哪个文件）+ 末行（为什么）；仍超预算先丢头部。
    输出恒为单行（换行折成 " … "）——告警走 Hook 通道，多行会破坏单行强提醒纪律。
    """
    body = [l.strip() for l in (text or "").splitlines() if l.strip()]
    if not body:
        return ""
    if len(body) == 1:
        return body[0][:n]
    frame = next((l for l in reversed(body[1:]) if ".py" in l), "")
    parts = []
    for p in [body[0], frame, body[-1]]:
        if p and p not in parts:
            parts.append(p)
    out = " … ".join(parts)
    while len(out) > n and len(parts) > 1:
        parts.pop(0)
        out = " … ".join(parts)
    return out[:n]


class _RecSet:
    """回执记录收集器：按 (evt, kind) 存，供逐条打印 + 按钩子对账。"""

    def __init__(self):
        self.records = []
        # (evt, 基准子串) → 产品聚合行数出的该钩子失败**声明时刻清单**（v0.14 由「计数+最近ts」改清单：
        # 差额行的 ts 必须落回它自己那条未证明声明的时刻，⛔不再用「该 key 最近一次声明」整把盖壳——
        # 旧差额借新声明壳落进当前窗口=狼来了，该形状 v0.13 头注/§3.4 同源律点过名，
        # 但 v0.13 只修了 key 维度没修 ts 维度（本案 2026-10-02 工单补全））。
        # ⚠️必须按钩子对账而非按事件汇总（2026-09-12 自审）：按事件比 "声明数 vs 本会话全部非零具名数"
        # 会被别的钩子的非零回执顶掉，产品明明报某钩子失败、我却没有它的证据，差额照样归零=假绿。
        self.declared_times = {}

    def add(self, ts, cmd, evt, code, kind, stderr=""):
        self.records.append((ts, cmd, evt, code, kind, _clip_err(stderr or "")))

    def of(self, *kinds):
        return [r for r in self.records if r[4] in kinds]


def _declared_key(evt, n, names):
    """产品聚合行（batch）声明的失败钩子 → 对账 key。v0.13 归因对齐的**唯一落点**。

    ✅DO 与具名侧同源（同走 `_match`·实盘优先最长匹配），⛔不得用 BASELINE 针子另造一套 key。
    病灶实测（2026-10-01 11:37）：实挂针子 `rule_three_layer_guard.py --deliver` 比 BASELINE 针子
    `rule_three_layer_guard.py` 长 ⇒ 9 条声明全记在短针子 key 上，其中 3 条的具名证据被 `_match`
    归到长针子名下 ⇒ 差额恒 3 判"⚠️无具名证据"，且 ts 取最近一次声明 ⇒ 三条假红**同时钟**进窗口
    （真机核对：声明 9 = 具名 6 + 3，真崩 0）。v0.9 只把判活改绑实盘、漏了这一路。
    单独成函数＝让自测能把"这一路"整体置假做变异（§3.9·换实现不换输入）。
    """
    for cmd in names.split(", "):
        if n in cmd:
            evt2, n2 = _match(cmd)
            if n2:
                return (evt2 or evt, n2)
            break
    return (evt, n)


def _pair_unproven(decl_ts, named_ts):
    """逐 key 求**未证明声明的时刻清单**：尾贪心配对——最新的声明由最新的具名证据优先作证，
    剩下的（更旧的）声明才是未证明的。

    v0.14（2026-10-02 提醒面假红工单·修A）：差额行的 ts 由此函数给出（=其声明自身时刻），
    ⛔不得取「该 key 最近一次声明时刻」——存量旧差额会借窗口内新声明的壳每次落进当前告警
    （真机探针复现：8 月声明无证据 + 窗口内声明有证据 ⇒ 旧实现把差额记到最新声明时刻=进窗）。
    窗口内的无证据声明照落自身时刻进 delta（🔴照常，⛔修展示不修成失明·用例 30b）。
    单独成函数＝让自测能把「这一路」整体置假做变异（§3.9 与 _declared_key 同构）。
    """
    return list(decl_ts[:max(0, len(decl_ts) - len(named_ts))])


def _self_probe_exempts(r, self_name):
    """当轮自证（v0.14·2026-10-02 案件·修B）：超时类崩溃记录 r，当前正在执行的钩子是否同命令。

    病灶（真机 13:07→13:13 实录）：确认超时「已恢复」的成功回执正是**当轮**写的——
    而 hook_mode 的扫描发生在当轮内部，该回执物理尚未落盘 ⇒ v0.11 只看「已落盘回执」的
    豁免必然滞后一轮：上一轮超时（按 09-23 语义已恢复的存量旧账）被提醒面摆进当前告警，
    人工复跑 report 时回执已落又消失=「判据对、展示取数时点错」。本钩子「正在执行」本身
    =「同命令其后成功」的硬事实，作为与落盘回执同源的证据源采信
    （⛔不放宽判据：语义仍是 09-23 的「其后有成功才豁免」，只是补上仪器看不见的事实面）。
    限定：仅同脚本名适用（自证自己的账，⛔钩子间不互免）；仅超时类调用（gate 在调用侧）。
    单独成函数=变异落点（§3.9 同构）。
    """
    return bool(self_name) and _who(r[1]) == self_name


def _parse_receipts(session_id=None):
    """产品回执（单次全量扫描，实测 36MB/313 日志）。

    返回 (stat, rs, skipped_runs, user_runs, cur_runs)：
      stat = {脚本子串→[次数, 最近ts]}（判活用），rs = _RecSet（崩溃/送达/阻断/设计）。

    实测依据（2026-08-29，106 个 run）：'User hooks skipped' 出现于 90 个 run，
    其中 89 个是压缩/标题等内部进程（本就不加载 user 源）——故不按全局布尔报警，
    改为按 run 目录归因，只由当前会话所在 run 判定。

    崩溃判据（2026-09-12 根治·判据绑定被检对象）：⛔不再读 hook.finished 的
    exit_code/success=false 猜崩溃。实测该形状 942 条 exit=0、7 条 exit=1、2 条 exit=2，
    `success=false` 与"脚本崩了"不等价（自家 --deliver 的 exit 2 也在其中＝假红），
    且这条行**没有命令名**、按完成顺序异步落盘⇒无法归因。产品另有具名通道：
      `[HookRunner] Hook "<cmd>" (event: E) exited with code N. stderr: <首行>`  ← 名+码+证据
      `  <cmd>: unknown error, exit code N, stderr: <首行>`                      ← 阻断侧同料
      `Hook execution for E: N succeeded, M failed (<命令名…>)`                   ← 产品自己数的数
    前两条按证据分类，第三条只做对账：M（限基准内名字）> 已具名条数 ⇒ 差额记
    unattributed（🔴仍在 delta，⚠️标"归因未定"）——⛔不得静默丢弃，也不得拿它顶崩溃数。
    ⚠️日志回显污染：本端把工具输出整段写回日志（preview=/session_message/tool.shell），
    这些串里会出现本脚本正在用的正则字面量 ⇒ 必须 isecho 过滤，否则自造假回执。
    """
    started_re = re.compile(r'\] hook\.started hook_name=.*source="user".*display_text="((?:[^"\\]|\\.)*)"')
    ts_re = re.compile(r"^(\S+)\s")
    hr_re = re.compile(r'\[HookRunner\] Hook "(.*?)" \(event: ([A-Za-z]+)\) '
                       r'exited with code (-?\d+)\. stderr: (.*)')
    unk_re = UNK_RE   # v0.19 模块级（stderr 可选+32e 可置假），形状说明见定义处
    batch_re = re.compile(r"Hook execution for ([A-Za-z]+): (\d+) succeeded, (\d+) failed \((.*?)\)")
    stat = {}
    rs = _RecSet()
    named_times = {}               # (evt, needle) → 已具名非零回执时刻清单（v0.14 配对用）
    skipped_runs = set()
    user_runs = set()
    cur_runs = set()
    for path in sorted(glob.glob(os.path.join(_runs_dir(), "*", "*.log"))):
        run = os.path.basename(os.path.dirname(path))
        prev_ts = ""               # 本文件最近一条带时间戳的行（供裸续行借时）
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            continue
        if session_id and session_id in content:
            cur_runs.add(run)
        for line in content.splitlines():
            if line[:4].isdigit():
                prev_ts = line.split(None, 1)[0]
            if ("hook." not in line and "[HookRunner]" not in line
                    and "unknown error, exit code" not in line
                    and "Hook execution for" not in line
                    and "User hooks skipped" not in line):
                continue          # 成本纪律：全量 36MB ⇒ 先子串预筛再上正则
            if ("preview=" in line or "session_message" in line or "tool.shell" in line
                    or '"command":' in line or '"command_names":' in line
                    or "Handling plugin command" in line or "Running command:" in line
                    or "actualCommand" in line or "ExecuteStrategy" in line):
                # v0.10（2026-09-21·Qoder CN·Stop 假红实锤反哺）：旧三关键词漏掉"终端命令回显"形状——
                # 本会话排查一条 exit=126 告警时，grep 命令文本（含"unknown error, exit code 126"字样）
                # 被产品 TerminalResultHandle/JSON dump 整段写回日志 ⇒ unk_re 匹配 JSON 内转位子串
                # ⇒ 守卫把自己的告警排查过程读成"真崩1"=自激假红（守卫病·回显过滤漏形状）。
                # 真回执（HookRunner/hook.started/batch 行）不含这些命令回显特征，过滤不误伤。
                continue
            ts = ts_re.match(line)
            ts = ts.group(1) if ts else prev_ts
            if "User hooks skipped" in line:
                skipped_runs.add(run)
            m = started_re.search(line)
            if m:
                user_runs.add(run)
                # 一条回执只归一个基准（_match 最长匹配）：⛔不能"命令里出现哪个子串就都算一条"——
                # Stop 的 `crossend_guard.py --stop` 同时含 SessionStart 的 `crossend_guard.py`，
                # 旧写法让一条回执替两个事件作证（SessionStart 从未执行也照样绿=假绿）。
                _evt, n = _match(m.group(1))
                if n:
                    e = stat.setdefault(n, [0, ""])
                    e[0] += 1
                    if ts > e[1]:
                        e[1] = ts
                continue
            hm = hr_re.search(line)
            if hm:
                cmd, evt, code, err = hm.group(1), hm.group(2), int(hm.group(3)), hm.group(4)
                rs.add(ts, cmd, evt, code, _classify_record(code, evt, cmd, err), err)
                _e, n = _match(cmd)
                if n:
                    named_times.setdefault((evt, n), []).append(ts)
                continue
            um = unk_re.search(line)
            if um:
                cmd, code, err = um.group(1), int(um.group(2)), (um.group(3) or "")
                evt, n = _match(cmd)            # 该通道无事件字段→按基准最长匹配归属
                rs.add(ts, cmd, evt or "", code, _classify_record(code, evt or "", cmd, err), err)
                if n:
                    named_times.setdefault((evt or "", n), []).append(ts)
                continue
            bm = batch_re.search(line)
            if bm:
                evt, names = bm.group(1), bm.group(4)
                # 产品自己列的失败钩子名逐个记账（一周期一条钩子一次）；基准外的名字不归本守卫管
                for n in BASELINE.get(evt, []):
                    if n in names:
                        # v0.13 归因对齐：key 统一由 `_declared_key` 解析（与具名侧同源），⛔在此
                        #   内联造 key——该处正是"两通道各归各账"的发生地，判据理由见函数 docstring。
                        key = _declared_key(evt, n, names)
                        rs.declared_times.setdefault(key, []).append(ts)
    # 对账：产品说"这个钩子失败了" vs 本守卫为**它**拿到几条证据——
    # v0.14 修A：差额行 ts=其自身声明时刻（_pair_unproven 尾贪心配对），⛔不再取「该 key
    # 最近一次声明时刻」——存量旧差额借新声明壳每次落进当前窗口=提醒面假红（工单 2026-10-02）。
    for key, dlist in sorted(rs.declared_times.items()):
        evt, n = key
        for uts in _pair_unproven(dlist, named_times.get(key, [])):
            rs.add(uts, "⚠️产品声明失败、无具名证据（%s）" % n,
                   evt, None, "unattributed")
    return stat, rs, skipped_runs, user_runs, cur_runs


def _parse_gui_receipts(stat, rs):
    """双源升级（2026-09-04·童灵）→ 具名归因版（2026-09-12 根治·童灵）。

    病灶（实测）：`logs/runs/*/qodercli.log`（liveness 曾有的唯一源）末次 user 回执停在
    09-04 14:33，而 GUI 的 questWindow/hooks.log 同期仍在写 ⇒ CLI 源对 GUI 会话是瞎的。

    GUI 行格式（真机 20260904T183655/questWindow/hooks.log 实测）：
      `[info] Hook execute started (command=<cmd>, actualCmd=..., cwd=...)`
      `[info] Hook execute completed (event=<Evt>, exitCode=<N>, command=<cmd>, cost=..)`
      `[warning] Hook execute failed (timeout) (command=<cmd>, timeout=30s)`
      `[warning] Hook execute failed (event=<Evt>, command=<cmd>, error=<原因>, cost=..)`
      `[warning] --- stderr ---` + **裸文本续行**（无时间戳、无级别）
      `[info] Hook dispatch result (event=<Evt>, winner=...)` ← 一轮的边界
    分类与 CLI 同源：同一 `_classify_record` + 同一记录形状，
    ⛔两源各用一套判据=同一事件两种结论=假红/假绿随读哪个源而定。

    本函数旧实现的三个失明点（2026-09-12 逐条取证）：
      ① 只扫含 `[info] ` 的行 ⇒ `--- stderr ---` 与 `failed` 都挂在 `[warning]` 上，
         对应分支永不触发 ⇒ 崩溃证据在 GUI 源结构性不可得（写了判据却拿不到证据）；
      ② 证据不可得 ⇒ rule_three_layer_guard 的 TypeError 真崩
         （18:42:09.919 exitCode=1）被降级判成 "design"=按设计 = **假绿**；
      ③ 超时/取消类失败行根本没有 exitCode ⇒ 完全不入账。
    并行钩子的 stderr 块与别人的 completed 行交错 ⇒ 证据按 traceback 内**脚本名**归因，
    ⛔不按行位置猜；归不上任何非零回执的崩溃证据记 unattributed（朝红），不静默吞。
    返回 (最近 GUI 回执 ISO 时刻, 产品重载 ISO 时刻)。
    """
    head_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+\s+\[(\w+)\]\s+(.*)$")
    completed_re = re.compile(r"Hook execute completed \(event=([A-Za-z]+),\s*exitCode=(-?\d+),"
                              r"\s*command=(.*?)(?:,\s*cost=.*|)$")
    failed_to_re = re.compile(r"Hook execute failed \(timeout\) \(command=(.*?),\s*timeout=")
    failed_ev_re = re.compile(r"Hook execute failed \(event=([A-Za-z]+),\s*command=(.*?),"
                              r"\s*error=(.*?)(?:,\s*cost=.*|)$")
    started_pre = "Hook execute started (command="
    config_pre = "Hook config loaded"
    last_iso = ""
    reload_iso = ""
    for path in _gui_hooks_logs(3):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            continue
        err_pool = []      # 本轮已闭合的 stderr 块文本
        cycle_pending = []  # 本轮非零/失败回执，等 stderr 归因 [(iso, evt, cmd, code, kind, tail)]
        raw = None         # 正在收集的裸 stderr 续行

        def _collect_raw():
            if raw:
                text = "\n".join(raw).strip()   # ⛔不按空格压平：崩溃原因在最后一行，压平就没了
                if text:
                    err_pool.append(text)
                raw.clear()

        def _flush(flush_iso):
            """一轮结束：把 stderr 证据按脚本名归给本轮回执，归不上的朝红显形。"""
            claimed = set()
            for (iso, cmd, evt, code, kind, tail) in list(cycle_pending):
                base = _who(cmd)
                for i, bt in enumerate(err_pool):
                    if base != "?" and base in bt:
                        tail = bt
                        claimed.add(i)
                        break
                rs.add(iso, cmd, evt, code,
                       kind or _classify_record(code, evt, cmd, tail), tail)
            for i, bt in enumerate(err_pool):
                if i not in claimed and CRASH_EVIDENCE_RE.search(bt):
                    rs.add(flush_iso, "⚠️未归因（GUI stderr 里崩的脚本不在本轮回执中）", "",
                           None, "unattributed", bt)
            cycle_pending.clear()
            del err_pool[:]

        for line in lines:
            hm = head_re.match(line.rstrip("\n"))
            if not hm:                      # 裸 stderr 续行
                if raw is not None:
                    raw.append(line.rstrip("\n"))
                continue
            iso, _lvl, body = hm.group(1).replace(" ", "T", 1), hm.group(2), hm.group(3).strip()
            if raw is not None and not (body.startswith("--- ") or body.startswith("Hook ")):
                raw.append(line)            # 少见的无换行拼接：保守并入证据
                continue
            _collect_raw()
            raw = [] if body.startswith("--- stderr ---") else None
            if body.startswith("--- stdout ---"):
                continue                    # stdout 不作崩溃证据（守卫的正常报告都在这）
            if body.startswith(config_pre):
                # 「Hook config loaded (events=4, handlers=23)」＝配置被产品读取生效的时刻。
                # 判活宽限以此为准而非文件 mtime：实测 09-04 23:34 写入 → 09-05 05:39
                # 才 handlers 22→23（跨夜才重载），用 mtime 当参照会把"已重载、还没轮到"
                # 误判成 🔴从未执行（假红=假绿同族，只是方向相反）。
                if iso > reload_iso:
                    reload_iso = iso
                continue
            if body.startswith(started_pre):
                cmd = body[len(started_pre):].split(",")[0].strip()
                if iso > last_iso:
                    last_iso = iso
                # 与 CLI 源同判据：一条回执只归一个基准（见 _parse_receipts 同处注释）
                _evt, n = _match(cmd)
                if n:
                    e = stat.setdefault(n, [0, ""])
                    e[0] += 1
                    if iso > e[1]:
                        e[1] = iso
                continue
            m_evt = completed_re.match(body)
            if m_evt:
                evt, code, cmd = m_evt.group(1), int(m_evt.group(2)), m_evt.group(3).strip()
                if code == 0:
                    rs.add(iso, cmd, evt, code, "ok", "")
                else:
                    # ⛔不当场定性：并行钩子的 stderr 块可能还没轮到写入，等证据归因
                    cycle_pending.append((iso, cmd, evt, code, None, ""))
                continue
            m_to = failed_to_re.match(body)
            m_ev = failed_ev_re.match(body) if not m_to else None
            if m_to or m_ev:
                cmd = (m_to.group(1) if m_to else m_ev.group(2)).strip()
                evt = "" if m_to else m_ev.group(1)
                reason = "timed out" if m_to else m_ev.group(3)
                # 超时无 exitCode：钩子被产品掐死=本轮注入/守卫没跑完，属真失效（朝红）；
                # 取消多由用户中断触发，属噪声，仅留痕不计报警。
                kind = "crash" if m_to else "design"
                cycle_pending.append((iso, cmd, evt, None, kind, reason))
                continue
            if body.startswith("Hook execute failed (canceled)"):
                continue
            if body.startswith("Hook dispatch result") or body.startswith("Hook execute started (event="):
                _flush(iso)                 # 产品自己划的一轮边界=归因边界
        _collect_raw()
        _flush(last_iso)
    return last_iso, reload_iso


def liveness(session_id=None, self_name=None):
    """判活 + 真崩计数（口径=本轮 delta）。返回 Liveness 具名字段，见 `Liveness` 定义。

    `self_name`（v0.14·修B）=本守卫脚本名，仅 hook 实时路径传入——令超时类崩溃获得
    「当轮自证」豁免（确认恢复的回执由当轮写、扫描时物理不可见，详见 _self_probe_exempts）；
    report/手动路径不传=行为如旧（手动复跑时当轮回执本已落盘，落盘判据自足）。

    `failures` = 窗口起点后被归因的真崩条数 + 无法归因条数（⛔不含修复前的存量旧账——
    病灶实测：全量扫历史使 TypeError 修完后仍报"真崩 8"，其中 6 条属 10 天前，
    告警不随修复回落＝每轮喊狼来了）。存量保留并另栏打印（⚪不删除、不谎称已修）。
    """
    stat, rs, skipped_runs, user_runs, cur_runs = _parse_receipts(session_id)
    # 双源合并（2026-09-04）：GUI 回执与 CLI 回执共用同一判据与记录形状——
    # CLI 源停更时判活结论仍真；GUI 零回执时"从未执行"照报（不再被瞎源掩盖）
    gui_last, gui_reload = _parse_gui_receipts(stat, rs)
    since = _hook_chain_mtime()
    # v0.11（2026-09-23·Stop 09:54 超时击杀实录·第9轮反哺）：超时朝红设计保留（L649：
    # 被产品掐死=本轮没跑完，⛔不得静默），但**同命令其后有成功/送达回执** ⇒ 该超时属
    # 偶发 IO 抖动已自恢复，降 ⚪ 存量不计 delta——"告警随修复回落"同族（09-12 案变体：
    # 无链改动时单次超时将挂红数天=狼来了）。⛔其后无成功回执的超时照旧计红（朝红不放宽）。
    def _timeout_recovered(r):
        if (r[5] if len(r) > 5 else "") != "timed out":
            return False
        if _self_probe_exempts(r, self_name):   # v0.14 修B：当轮正在执行同命令=恢复事实已成立
            return True
        return any(x[1] == r[1] and (x[0] or "") > (r[0] or "") and x[4] in ("ok", "delivery")
                   for x in rs.records)
    _crash_all = rs.of("crash")
    _crash_fresh = [r for r in _crash_all if not _timeout_recovered(r)]
    detail_timeout_recovered = len(_crash_all) - len(_crash_fresh)
    crash_delta, crash_backlog = _split_by_window(_crash_fresh, since)
    un_delta, un_backlog = _split_by_window(rs.of("unattributed"), since)
    failures = len(crash_delta) + len(un_delta)
    now = datetime.now()
    cfg_mt = _cfg_mtime()
    # 事件级最近回执时间：宽限期只对"这条链历史上跑过、只是配置改后还没轮到"成立
    # 判活对象=实盘挂载（2026-09-20 v0.9·守卫病2「判据未随对象演化=假红」同族根治）：
    # v0.7 把事件归属改读实盘后，实挂命令带参（--hook-protocol=json / --deliver 等）
    # ⇒ 实挂针子比 BASELINE 针子长 ⇒ _match 最长匹配把回执全记到实挂针子名下，
    # BASELINE 短针子自此冻结（实测 09-02T15:47 起 5 钩子假红 18 天）。判活改按实盘
    # (evt, needle) 逐钩评估；BASELINE 针子被同事件实挂针子**包含**时跳过（superseded——
    # 回执已归实挂针子，单判=重复计账）；BASELINE 未挂载条目保留（never=应挂未挂仍在场）。
    _judge, _seen = [], set()
    for _e, _n in (_mounted_pairs() or []):      # 读不到实盘→回落纯 BASELINE（回落律·不静默失明）
        if (_e, _n) not in _seen:
            _seen.add((_e, _n))
            _judge.append((_e, _n))
    for _e, _ns in BASELINE.items():
        for _n in _ns:
            if any(_e2 == _e and _n in _m and _n != _m for _e2, _m in _judge):
                continue          # superseded：实挂针子已含本针子
            if (_e, _n) not in _seen:
                _seen.add((_e, _n))
                _judge.append((_e, _n))
    evt_last = {}
    for evt, n in _judge:
        d = _ts_to_dt(stat.get(n, [0, ""])[1])
        if d and (evt_last.get(evt) is None or d > evt_last[evt]):
            evt_last[evt] = d
    never, stale, pending = [], [], []
    for evt, n in _judge:
        cnt, last = stat.get(n, [0, ""])
        if cnt == 0:
            e_last = evt_last.get(evt)
            # 生效起点取"配置 mtime 与产品重载时刻的较晚者"（⛔不用单 mtime·见上注）
            graced_from = cfg_mt or _ts_to_dt(gui_reload)
            r_dt = _ts_to_dt(gui_reload)
            if r_dt and (graced_from is None or r_dt > graced_from):
                graced_from = r_dt
            if graced_from and e_last and graced_from > e_last and \
                    (now - graced_from).total_seconds() < PENDING_GRACE_HOURS * 3600:
                pending.append("%s: %s（生效起点 %s（配置 mtime/产品重载取较晚），该链最近回执 %s）"
                               % (evt, n, graced_from.strftime("%m-%d %H:%M"),
                                  e_last.strftime("%m-%d %H:%M")))
            else:
                never.append("%s: %s" % (evt, n))
            continue
        try:
            d = datetime.strptime(last[:10], "%Y-%m-%d")
            if (now - d).days > STALE_DAYS:
                stale.append("%s: %s（末次 %s）" % (evt, n, last[:16]))
        except Exception:
            pass
    # 真告警判据：本会话确实执行过钩子回执行的 run 全被跳过，且一条 user 回执都没有
    skipped = bool(cur_runs) and cur_runs <= skipped_runs and not (cur_runs & user_runs)
    detail = {
        "delta": crash_delta + un_delta,
        "backlog": crash_backlog + un_backlog,
        "since": since,
        "delivery": rs.of("delivery"),
        "design": rs.of("design"),
        "declared": {"%s:%s" % k: len(v) for k, v in rs.declared_times.items()},
        "last_nonzero": max([r[0] for r in rs.records if r[0]] or [""]),
        "gui_last": gui_last,
    }
    return Liveness(never, stale, failures, len(rs.of("block")), skipped,
                    sum(v[0] for v in stat.values()), pending, len(detail["design"]), detail)


def _hp_ledger_path():
    return os.environ.get("QCN_HP_LEDGER", HP_LEDGER_DEFAULT)


def _gui_logs_root():
    return os.environ.get("QCN_GUI_LOGS", GUI_HOOKS_LOG_DEFAULT)


def _gui_hooks_logs(limit=3):
    """最近 N 个 GUI（questWindow）钩子日志——按 mtime 降序，成本有界。

    ⚠️跳过 0 字节文件（2026-09-12 实测病灶）：产品自 09-05 17:47 起新建的
    `questWindow/hooks.log` 全是 0 字节（建了文件不写回执），"取最近 3 个"= 取到 3 份
    空文件 ⇒ GUI 源对判活实际失明，而 liveness 仍按"零回执"结案（=拿瞎源结的案的复发形态）。
    全为空时退回最新一份，让"看不见"显形于 source_freshness，⛔不静默当真。
    """
    try:
        cands = glob.glob(os.path.join(_gui_logs_root(), "*", "questWindow", "hooks.log"))
        cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        nonempty = [p for p in cands if os.path.getsize(p) > 0]
        return (nonempty or cands)[:limit]
    except Exception:
        return []


def _newest_gui_hooks():

    """GUI（questWindow）钩子日志——本端真实回执源（实测：runs/ 14:33 停更，
    而 questWindow/hooks.log 22:17 仍在写 ⇒ CLI 源对 GUI 会话是瞎的）。"""
    ls = _gui_hooks_logs(1)
    return ls[0] if ls else ""


def injection_receipt():
    """查⑦ 注入收下率（2026-09-04 根治·愿景①「不靠人记得」）。

    病灶：本端 UPS 钩子的裸文本 stdout 被产品判 `winner=none (no parsed output)`
    整轮丢弃（实测 143/143），而挂载自检/成熟度评估只验"脚本存在"，**没有任何一环
    验"输出是否被产品收下"** ⇒ 注入静默失效无人知晓。本查把"收下"变成每轮机械对账。

    对账两侧：
      A 侧 = hook_protocol 留痕（我们发出了什么：mode/bytes/host）
      B 侧 = GUI 回执（产品收下了什么：`dispatch result ... additionalContext=` vs
             `winner=none (no parsed output)`）
    返回 (reds, warns, info_dict)。任何异常 → 整体放行（Hook 三纪律）。
    """
    reds, warns = [], []
    info = {"sent_json": 0, "sent_text": 0, "accepted": 0, "dropped": 0, "gui_log": ""}
    try:
        cutoff = datetime.now() - __import__("datetime").timedelta(minutes=INJECT_ROUNDS_WINDOW_MIN)
        with open(_hp_ledger_path(), encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("probe"):
                    continue  # 手工测试行不参与对账（防自欺）
                try:
                    if datetime.strptime(str(d.get("ts", ""))[:19], "%Y-%m-%dT%H:%M:%S") < cutoff:
                        continue
                except Exception:
                    continue
                if int(d.get("bytes", 0)) <= 0:
                    continue
                if d.get("mode") == "json":
                    info["sent_json"] += 1
                    # host 异常只对本端发送生效（2026-09-20 v0.9）：ledger 机器本地多端共写，
                    # 他端（zcode 866 条实测）host 天然非 qodercn——不按 qoder_env 收窄=跨端
                    # 仪器污染（本端警报被他端留痕顶红）。本端行 qoder_env 非空（QODER_* 导出），
                    # 他端行 qoder_env=[]。
                    if d.get("host") not in ("qodercn", "", None) and d.get("qoder_env"):
                        warns.append("协议留痕 host 异常: %s" % d.get("host"))
                else:
                    info["sent_text"] += 1
                    if d.get("host") == "qodercn" or str(d.get("reason", "")).startswith("fingerprint"):
                        reds.append("本端仍按裸文本输出（协议声明/指纹漏配）：%s"
                                    % d.get("script", "?"))
        gl = _newest_gui_hooks()
        info["gui_log"] = gl
        if gl:
            accepted = dropped = 0
            with open(gl, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-400:]
            for l in lines:
                if "Hook dispatch result (event=UserPromptSubmit" not in l:
                    continue
                try:
                    ts = datetime.strptime(l[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
                if ts < cutoff:
                    continue
                if "winner=none" in l:
                    dropped += 1
                else:
                    accepted += 1
            info["accepted"], info["dropped"] = accepted, dropped
            if dropped and not accepted:
                reds.append("产品对 UserPromptSubmit 输出整轮判弃（%d 轮全 winner=none）"
                            "⇒ 注入通道未生效%s" % (dropped,
                            "，且我方已按 JSON 发出 %d 次 ⇒ JSON 亦不被接受，属平台边界须降级方案"
                            % info["sent_json"] if info["sent_json"] else
                            "，且我方无 JSON 留痕 ⇒ 协议未声明"))
            elif dropped and accepted:
                warns.append("注入收下不稳定：收 %d / 弃 %d（近 %d 分钟）"
                             % (accepted, dropped, INJECT_ROUNDS_WINDOW_MIN))
    except FileNotFoundError:
        warns.append("协议留痕台账不存在（尚无钩子经真源输出）")
    except Exception:
        return [], [], info  # 失败放行
    return reds, warns, info


def source_freshness(gui_last=""):
    """查⑧ 判活源新鲜度（2026-09-04 根治·治"仪器假装正常"；2026-09-12 补反向盲区）。

    实测：`logs/runs/*/qodercli.log`（liveness() 的唯一回执源）最新 user 回执停在
    2026-09-04T14:33:56，而 GUI 的 questWindow/hooks.log 22:17 仍在写 ⇒ liveness 报
    "从未执行 0 条=全绿"靠的是**历史累计**，源已瞎而表仍绿。本查显式报出源停更。

    反向盲区（2026-09-12 实测补）：旧判据只盯"GUI 比 CLI 新"这一向，GUI 侧 0 字节/停摆
    时静默放行——实测最近 3 份 `questWindow/hooks.log`（09-05 17:47/09-07/09-08 新建）
    **全为 0 字节**，产品建了文件没写回执 ⇒ 所谓"双源合并"实际只剩 CLI 单源，
    而对外结论仍按双源口径结案。方向相反的失明同样是失明，故本查双向都报。
    """
    warns = []
    try:
        # 成本纪律：本查每轮 Stop 都跑 ⇒ ⛔不全量读 36MB 日志（那会把"守卫变慢"
        # 当成新病灶）。改用 run 目录 mtime 作"最近回执写入时刻"的代理（写入即更新 mtime）。
        runs_latest = ""
        try:
            mt = max((os.path.getmtime(f) for f in
                      glob.glob(os.path.join(_runs_dir(), "*", "*.log"))), default=None)
            runs_latest = datetime.fromtimestamp(mt).strftime("%Y-%m-%d %H:%M:%S") if mt else ""
        except Exception:
            runs_latest = ""
        gfiles = sorted(glob.glob(os.path.join(_gui_logs_root(), "*", "questWindow", "hooks.log")),
                        key=lambda p: os.path.getmtime(p), reverse=True)
        g_all = gfiles[:3]
        gl = _newest_gui_hooks()
        gui_mt = ""
        if gl:
            gui_mt = datetime.fromtimestamp(os.path.getmtime(gl)).strftime("%Y-%m-%d %H:%M:%S")
        if g_all and all(os.path.getsize(p) == 0 for p in g_all):
            newest_all = datetime.fromtimestamp(os.path.getmtime(g_all[0])).strftime("%Y-%m-%d %H:%M")
            warns.append("🟡 单源降级：GUI 判活源最近 %d 份 hooks.log 全 0 字节"
                         "（最新一份 %s 建而未写·GUI 会话钩子回执不可见）"
                         "⇒ 本轮判活实际仅由 CLI 源支撑（产品侧未写，非本守卫可修）"
                         % (len(g_all), newest_all))
        elif gui_mt:
            g_dt = datetime.strptime(gui_mt, "%Y-%m-%d %H:%M:%S")
            r_dt = (datetime.strptime(runs_latest, "%Y-%m-%d %H:%M:%S") if runs_latest else None)
            gap_h = (g_dt - r_dt).total_seconds() / 3600 if r_dt else 9e9
            if gap_h > RUNS_STALE_HOURS:
                warns.append("CLI 判活源停更 %.1fh（runs 末次 %s ｜ GUI hooks.log %s 仍活）"
                             "⇒ 已由双源合并兜住（liveness 现读 CLI+GUI），本行为信息级；"
                             "⛔勿再退回单 CLI 源判活" % (gap_h, runs_latest or "无", gui_mt))
        elif not gl:
            warns.append("GUI hooks.log 未找到（查⑦/⑧ 降级为不可判）")
    except Exception:
        return []
    return warns


def protocol_declared():
    """查⑨ 注入钩子协议声明缺失（⚠️ 非 🔴：载荷指纹可兜底，但声明丢失=降级运行）。"""
    warns = []
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            root = json.load(f)
        for g in root.get("hooks", {}).get("UserPromptSubmit", []):
            for h in (g.get("hooks") or [g] if isinstance(g, dict) else []):
                cmd = h.get("command", "") if isinstance(h, dict) else ""
                if any(n in cmd for n in BASELINE["UserPromptSubmit"][:1] +
                       ["kb_inject_prompt.py", "doenglingz_inject_prompt.py",
                        "position3_notify.py"]) and "--hook-protocol" not in cmd:
                    warns.append("注入钩子未声明协议（靠载荷指纹兜底）：%s" % cmd[:70])
    except Exception:
        return []
    return warns


SCRIPT_RE = re.compile(r"([~/][^\s\"';&|)]+\.(?:py|sh|js))")


def _repo_root(path):
    """向上找 owning 仓库根——家目录非单仓库（个人AI档案 / .qoder-cn 分库各管各）。"""
    cur = os.path.dirname(os.path.abspath(path))
    while cur and cur != os.path.dirname(cur):
        if os.path.isdir(os.path.join(cur, ".git")):
            return cur
        cur = os.path.dirname(cur)
    return None


def git_backing():
    """查⑥ 实挂未入库：钩子链引用的脚本必须被其所属仓库跟踪。

    病灶（2026-08-30 皮叔令「剩下的两个工作按第一性原理最优根治」）：本端新建守卫上线即
    "实挂在 Stop 链 + 仓库未跟踪"，而全系统唯一的孤儿检测器 `guard_doc_consistency.py`
    只挂在 WorkBuddy 的 Stop 链——本端要等你哪天打开 WB 才会看到 ❌，等于"新守卫没入库
    可以无限期静默"。挂在链上却无版本控制 = 容灾快照（memory-amber 只提交已跟踪文件）
    永不含它，一次误删即永久丢失。
    判据口径：⛔ 不扫全仓库（会把各端 WIP 报成噪声），只查"本端实挂的脚本"——
    检测范围与危害同源（实测本端 19 个挂载脚本零假警报）。
    文件不存在者跳过：那属"挂了跑不了"，由活性查（回执崩溃/从未执行）负责，不重复报。
    返回 (untracked, outside_repo)。
    """
    untracked, outside = [], []
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            root = json.load(f)
    except Exception:
        return untracked, outside
    paths = set()
    for groups in root.get("hooks", {}).values():
        for g in groups:
            if not isinstance(g, dict):
                continue
            entries = g["hooks"] if "hooks" in g else [g]
            for h in entries:
                if not isinstance(h, dict):
                    continue
                for mo in SCRIPT_RE.finditer(h.get("command", "")):
                    p = os.path.expanduser(mo.group(1))
                    if os.path.exists(p):
                        paths.add(p)
    for p in sorted(paths):
        repo = _repo_root(p)
        if repo is None:
            outside.append(p)
            continue
        rel = os.path.relpath(p, repo)
        try:
            rc = subprocess.run(["git", "-C", repo, "ls-files", "--error-unmatch", "--", rel],
                                capture_output=True)
        except Exception:
            return [], []  # git 不可用 → 本查整体放行（Hook 三纪律：失败不误报不拦截）
        if rc.returncode != 0:
            untracked.append("%s::%s" % (repo, rel))
    return untracked, outside



def mount_args_smoke():
    """查⑪ 挂载参数冒烟（2026-09-05·送达律反例自食，根因级防复发）。

    病灶：我把 `--deliver` 写进 settings.json 挂载命令却没跑过一次带该参数的真调用
    ⇒ argparse `unrecognized arguments` 每轮崩；而 argparse 错误也是 exit 2，
    会被「带 --deliver 的 exit2＝送达」读成投递成功＝自己吞掉自己的故障。
    判据：取命令行里的 `--flag`，在脚本**源码文本**里搜该字面串——搜不到即脚本不认识此参数→报红。
    ⛔不用 `--help` 比对：本端有 4 个钩子是手工解析 argv（--hook-protocol 不出现在 argparse 帮助里），
      用 --help 会把它们全判成假红——修复引入噪声，等于把刚治的病换个方向再犯一遍。
    """
    warns = []
    try:
        with open(_settings_path(), encoding="utf-8") as f:
            root = json.load(f)
    except Exception:
        return warns
    cache = {}
    for groups in root.get("hooks", {}).values():
        if not isinstance(groups, list):
            continue
        for g in groups:
            for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                cmd = h.get("command", "") if isinstance(h, dict) else ""
                toks = cmd.split()
                script = next((x for x in toks if x.endswith((".py", ".sh"))), "")
                flags = [x.split("=")[0] for x in toks if x.startswith("--")]
                if not script or not flags:
                    continue
                sp = os.path.expanduser(script)
                if not os.path.isfile(sp):
                    continue
                if sp not in cache:
                    try:
                        with open(sp, encoding="utf-8", errors="replace") as f:
                            cache[sp] = f.read()
                    except Exception:
                        cache[sp] = None
                src = cache[sp]
                if src is None:
                    continue
                # 委托真源例外（实测假红纠正）：本端注入钩子把 argv 解析委托给
                # hook_protocol.detect()，参数字面串只存在于真源里——委托即视为已声明
                if "hook_protocol" in src:
                    # v0.18 假红根治：真源本体与本脚本同目录（作者机=[记忆共享中心]/脚本中心）；
                    # ~/脚本中心 只有 logs/runtime 共享台账、无 .py 本体（实测不在场⇒原写法
                    # 例外永不生效⇒委托型钩子全被报「每轮崩」假红，产品日志 unrecognized
                    # arguments=0 反证没崩）。同目录推导=去机名+不断链，回退仅作兜底。
                    hps = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hook_protocol.py")
                    if not os.path.isfile(hps):
                        hps = os.path.expanduser("[记忆共享中心]/脚本中心/hook_protocol.py")
                    if hps not in cache:
                        try:
                            with open(hps, encoding="utf-8", errors="replace") as f:
                                cache[hps] = f.read()
                        except Exception:
                            cache[hps] = None
                    if cache.get(hps):
                        src = src + cache[hps]
                for fl in flags:
                    if fl not in src:
                        warns.append("%s 使用了脚本源码中不存在的参数 %s（argparse/手工解析都不认→每轮崩）"
                                     % (os.path.basename(sp), fl))
    return warns


def _fmt_receipt(r):
    """一条回执记录 → 可行动的一行明细（谁/哪个事件/退出码/何时/错在哪）。"""
    ts, cmd, evt, code, kind, stderr = r
    return "[%s] %s exit=%s @%s%s" % (evt or "?", cmd or "?",
                                      "—" if code is None else code, ts or "时刻未知",
                                      " :: " + stderr.replace("\n", " ")[:110] if stderr else "")


def _who(cmd):
    """整条钩子命令行 → 认得出的脚本名（告警只有一行，放不下命令行）。"""
    for tok in (cmd or "").split():
        if tok.endswith(".py"):
            return os.path.basename(tok)
    return (cmd or "?")[:24]


def report():
    """人读报告（check + liveness 汇总），exit code 由 main 决定。"""
    missing, dead, extra, mounted = check()
    lv = liveness()
    never, stale, failures, blocks = lv.never, lv.stale, lv.failures, lv.blocks
    skipped, hits, pending, nonzero = lv.skipped, lv.hits, lv.pending, lv.nonzero
    d = lv.detail
    untracked, outside = git_backing()
    ir_reds, ir_warns, ir_info = injection_receipt()
    sf_warns = source_freshness(d.get("gui_last", ""))
    pd_warns = protocol_declared()
    ms_warns = mount_args_smoke()
    print("qodercn_config_guard — Qoder CN 钩子配置 + 产品回执活性")
    print("  配置：实挂 %d 条（基准 %d）" % (mounted, sum(len(v) for v in BASELINE.values())))
    print("  回执：双源命中 %d 次｜真崩（窗口内）%d 条｜存量旧账 %d 条｜送达 %d 次｜按设计非零 %d 条｜阻断信号 %d 条｜待首个周期 %d 条%s"
          % (hits, failures, len(d["backlog"]), len(d["delivery"]), nonzero, blocks, len(pending),
             "｜🔴 本会话 user hooks 被跳过" if skipped else ""))
    print("  注入对账：我方发 JSON %d 次/裸文本 %d 次｜产品收下 %d 轮/判弃 %d 轮（近 %d 分钟）"
          % (ir_info["sent_json"], ir_info["sent_text"], ir_info["accepted"],
             ir_info["dropped"], INJECT_ROUNDS_WINDOW_MIN))
    bad = bool(missing or dead or extra or never or stale or failures or skipped
               or untracked or outside or ir_reds or ir_warns or sf_warns or pd_warns
               or any("不存在" in w for w in ms_warns))
    for label, items in (("🔴 配置缺失", missing), ("🔴 死形态（扁平·产品不执行）", dead),
                         ("🔴 从未被产品执行", never), ("⚠️ 活性超龄>%d天" % STALE_DAYS, stale),
                         ("⚠️ 意外多余", extra),
                         ("🔴 注入被判弃（输出没进对话=机制静默失效）", ir_reds),
                         ("🔴 实挂未入库（挂了但仓库未跟踪·容灾不含它）", untracked),
                         ("⚠️ 实挂无所属仓库（版本控制未纳管）", outside)):
        for it in items:
            print("  %s：%s" % (label, it))
    for it in (ir_warns + sf_warns + pd_warns + ms_warns):
        print("  ⚠️ %s" % it)
    for it in pending:
        print("  ⏳ 待首个周期（未过 %d 小时宽限·不算异常）：%s" % (PENDING_GRACE_HOURS, it))
    if failures:
        print("  🔴 user/GUI 源钩子真崩 %d 条（判据=产品具名失败行 + 异常证据，窗口起点后）" % failures)
        for r in d["delta"][:10]:
            print("     %s%s" % (_fmt_receipt(r),
                                 "" if r[4] != "unattributed" else
                                 "  ⚠️无法归因：产品只给了聚合计数未给钩子名——归因缺口本身是病灶，⛔不当无事"))
        if len(d["delta"]) > 10:
            print("     …另有 %d 条同类" % (len(d["delta"]) - 10))
    if d["backlog"]:
        print("  ⚪ 存量旧账 %d 条（早于窗口起点 %s·链改动前的历史崩溃，其代码/配置已不存在）——不计本轮报警（v0.14 存量定谳见头注：当时 12 条历史已清·新增者按同判据逐条再谳）"
              % (len(d["backlog"]),
                 d["since"].strftime("%Y-%m-%d %H:%M") if d["since"] else "取不到（全量计入）"))
    if len(d["delivery"]):
        print("  ℹ️ 守卫自身告警送达 %d 次（Stop 上 exit 2 = 投递信号，非崩溃）" % len(d["delivery"]))
    if nonzero:
        print("  ℹ️ 按设计非零退出 %d 条（守卫用 exit≠0 表达\"检出问题\"，不计报警·判据见 _classify_record）" % nonzero)
    print("  ✅ 全部干净" if not bad else "  —— 处置：补齐包裹形态/重建挂载后重跑本脚本")
    return 0 if not bad else 1


def _split_alert_tiers(delta):
    """步1分级纯函数（可测·无副作用）：具名真崩 vs 归因缺口。
    判据与渲染口径同源：r[3]=exit码，None=产品只给聚合计数未给钩子名(unattributed)。"""
    hard = [r for r in delta if r[3] is not None]
    un = [r for r in delta if r[3] is None]
    return hard, un


def _defer_alerts(un, path=None):
    """归因缺口降级台账（append-only·ts/cmd/kind），Stop 不敲门但排雷有原料。
    路径可注入（自测夹具用 temp）；写失败静默不反噬主流程（Hook 三纪律：失败不误报）。"""
    import datetime as _dt
    p = path or os.path.join(os.path.expanduser("~"),
                             "[记忆共享中心]/脚本中心/logs/runtime/hook_alert_deferred.jsonl")
    try:
        with open(p, "a", encoding="utf-8") as _fh:
            for r in un:
                _fh.write(json.dumps({"ts": r[0], "cmd": _who(r[1]),
                                      "kind": "unattributed_deferred"},
                                     ensure_ascii=False) + "\n")
    except OSError:
        pass


def hook_mode():
    """Stop 钩子模式：只读 stdin（可为空），有问题输出一行，永远 exit 0。"""
    try:
        try:
            raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        except Exception:
            raw = ""
        sid = ""
        try:
            sid = str(json.loads(raw).get("session_id", "")) if raw.strip() else ""
        except Exception:
            sid = ""
        missing, dead, extra, _ = check()
        lv = liveness(sid or None, os.path.basename(os.path.abspath(__file__)))
        never, stale, failures = lv.never, lv.stale, lv.failures
        skipped = lv.skipped
        untracked, outside = git_backing()
        ir_reds, ir_warns, _ir = injection_receipt()
        sf_warns = source_freshness(lv.detail.get("gui_last", ""))
        pd_warns = protocol_declared()
        ms_bad = [w for w in mount_args_smoke() if "不存在" in w]
        parts = []
        unreadable = any("读取失败" in m for m in missing)   # 守卫自身不可判→放行（Hook 三纪律：失败不误报）
        if missing or never:
            parts.append("🔴配置缺%d/从未执行%d" % (len(missing), len(never)))
        if dead:
            parts.append("🔴死形态%d条(扁平不执行)" % len(dead))
        if untracked:
            parts.append("🔴实挂未入库%d(容灾不含)" % len(untracked))
        if outside:
            parts.append("⚠️实挂无仓库归属%d" % len(outside))
        if failures:
            # v0.20 步1报警分级（2026-10-07 任务卡·皮叔令"彻底做完"·三明治🟡补线①落地）：
            #   delta 两类成员分流——具名真崩(r[3]=exit码非None)照常进 Stop 强提醒，
            #   ⛔红线不放宽：真崩永不静默（v0.14 双向夹具30e/31e语义保持）；
            #   归因缺口(r[3] is None·产品聚合无具名行·多为守卫检红rc≠0被记failed)→降级
            #   deferred台账，不敲门（此类由步2退出码语义统一从源头消解，台账供排雷清单）。
            _hard, _un = _split_alert_tiers(lv.detail["delta"])
            if _hard:
                top = max(_hard, key=lambda r: r[0] or "")
                parts.append("🔴钩子真崩%d(最近:%s exit=%s)%s"
                             % (len(_hard), _who(top[1]), top[3],
                                ("｜归因缺口%d条已降级台账" % len(_un)) if _un else ""))
            elif _un:
                _defer_alerts(_un)
                # 提醒面静默；report 面照常显形（同源判据不动，仅通道分级）
        if skipped:
            parts.append("🔴本会话 user hooks 被跳过(产品未加载用户设置源)")
        if stale or extra:
            parts.append("⚠️超龄%d/多余%d" % (len(stale), len(extra)))
        if ir_reds:
            parts.append("🔴注入被判弃%d(输出没进对话)" % len(ir_reds))
        # v0.16(2026-10-04) 提醒面卫生根治：自称「本行为信息级」的源滞后行不进 Stop 报警面
        # （双源已兜住=liveness 判据未受影响；保留单源降级/其他真停更行）。告警疲劳先例：l3_conclusion_guard。
        sf_alert = [w for w in sf_warns if "本行为信息级" not in w]
        if sf_alert:
            parts.append("⚠️判活源%s" % ("单源降级(GUI源0字节空转)"
                                       if any("单源降级" in w for w in sf_alert)
                                       else "停更(详见report)"))
        if pd_warns:
            parts.append("⚠️协议未声明%d" % len(pd_warns))
        if ms_bad:
            parts.append("🔴挂载参数脚本不认识%d条(每轮崩)" % len(ms_bad))
        if parts and not unreadable:
            msg = ("🔧 本端钩子守卫：%s → 跑 `python3 [记忆共享中心]/脚本中心/qodercn_config_guard.py check` 看明细（settings.json 形态/丢失会在下一轮生效）" % "｜".join(parts))
            if _hp is not None:
                return _hp.alert("配置守卫", msg, via_hook=True)   # 送达：stderr+stdout+exit2；同告警 24h 节流
            sys.stdout.write(msg + "\n")
        # 查⑩ 报警侧收讫（宿主收讫律的镜像）：投出去的告警，宿主真收下了吗？
        # 只搜指纹串不猜语义——指纹码仅存在于告警文本，不会被命令行回显误命中。
        if _hp is not None:
            try:
                st = _hp.delivery_check()
                lost = sorted(k for k, v in st.items() if v == _hp.LOST)
                if lost:
                    return _hp.alert("配置守卫", "🔴 报警侧未收讫：%d 条告警投递后未在宿主会话出现（指纹 %s）"
                                     "⇒ 送达通道疑失效（钩子/退出码语义变更），须人工核验，⛔不默认无事", via_hook=True
                                     % (len(lost), ",".join(lost)))
            except Exception:
                pass
    except Exception:
        pass
    return 0


def self_test():
    import shutil
    import tempfile
    root = tempfile.mkdtemp(prefix="qcn_cfg_guard_")
    ok = fail = 0

    def case(name, cond):
        nonlocal ok, fail
        print(("  ✅ " if cond else "  ❌ ") + name)
        ok += 1 if cond else 0
        fail += 0 if cond else 1

    try:
        sfile = os.path.join(root, "settings.json")
        runs = os.path.join(root, "runs")
        os.makedirs(runs)
        os.environ["QCN_GUARD_STATE"] = os.path.join(root, "state.json")
        # 每条命令单独一组，保证 check 的按事件聚合成立
        full = {"hooks": {evt: [{"hooks": [{"type": "command", "command": "python3 x/%s" % n}]}
                                for n in v] for evt, v in BASELINE.items()}}
        os.environ["QCN_SETTINGS"] = sfile
        os.environ["QCN_LOG_RUNS"] = runs
        gui_root = os.path.join(root, "gui")   # 隔离 GUI 源：默认空目录（不读真机日志）
        os.makedirs(gui_root, exist_ok=True)
        os.environ["QCN_GUI_LOGS"] = gui_root
        if _hp:
            # 自测⛔不得污染真机告警台账（原本第二处才改，第一处 hook_mode 已把假告警写进真账）
            _hp.ALERT_LEDGER = os.path.join(root, "alerts.jsonl")

        def write_runs(cmd_lines):
            d = os.path.join(runs, "run1")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "qodercli.log"), "w", encoding="utf-8") as f:
                for t, text in cmd_lines:
                    f.write('%s INFO  [session=s turn=t] hook.started hook_name="UserPromptSubmit" '
                            'hook_event_name="UserPromptSubmit" source="user" hook_index=1 total_hooks=1 '
                            'display_text="%s"\n' % (t, text))

        def cli(t, body):
            """往 CLI 源追加一行产品日志（body 须含被扫描子串，形状照真机）。"""
            with open(os.path.join(runs, "run1", "qodercli.log"), "a", encoding="utf-8") as f:
                f.write('%s WARN  [session=s turn=t] %s\n' % (t, body))

        def cli_raw(text):
            """裸行（无时间戳前缀）——真机的 `  <cmd>: unknown error, …` 就是这个形状
            （取证 qodercli.log:7324），unk_re 按 ^\\s{2,} 锚定，用 cli() 拼会造出假形状。
            """
            with open(os.path.join(runs, "run1", "qodercli.log"), "a", encoding="utf-8") as f:
                f.write(text + "\n")

        json.dump(full, open(sfile, "w"), ensure_ascii=False)
        m, d, x, mounted = check()
        case("1 正常配置→check 无异常", not m and not d and not x)

        broken = json.loads(json.dumps(full))
        broken["hooks"]["UserPromptSubmit"] = [g for g in broken["hooks"]["UserPromptSubmit"]
                                               if "position3_notify" not in json.dumps(g)]
        json.dump(broken, open(sfile, "w"), ensure_ascii=False)
        m, d, x, _ = check()
        case("2 负例·缺 position3_notify→check 报缺失", any("position3_notify" in i for i in m))

        flat = json.loads(json.dumps(full))
        flat["hooks"]["Stop"].append({"command": "python3 x/doenglingz_guard.py"})
        flat["hooks"]["Stop"] = [g for g in flat["hooks"]["Stop"]
                                 if not (isinstance(g, dict) and "hooks" in g
                                         and any("doenglingz_guard" in h["command"] for h in g["hooks"]))]
        json.dump(flat, open(sfile, "w"), ensure_ascii=False)
        m, d, x, _ = check()
        case("3 负例·扁平形态→check 报死挂载", any("doenglingz_guard" in i for i in d))
        json.dump(full, open(sfile, "w"), ensure_ascii=False)

        def freeze_cfg(ts="2026-08-29T09:00:00"):
            """json.dump 会把 mtime 刷成"现在"→零回执会被判成待首个周期；liveness 断言前固定。"""
            t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S").timestamp()
            os.utime(sfile, (t, t))

        write_runs([("2026-08-29T10:00:00.000+08:00", "python3 x/position3_notify.py")])
        freeze_cfg()
        lv = liveness()
        case("4 有回执→该条判为已执行", not any("position3_notify" in i for i in lv.never))
        case("5 负例·其余基准零回执→报从未执行",
             len(lv.never) == sum(len(v) for v in BASELINE.values()) - 1)
        case("5b 配置早于回执→不误判为待周期", not lv.pending)

        # ── 6-12 真崩判据（2026-09-12 根治）：产品**具名**通道 + stderr 异常证据 ──────────
        # ⛔夹具不再写 hook.finished：该通道没有命令名、按完成顺序异步落盘，读它猜崩溃
        #   就是本轮病灶的母体（同一个 exit2 既可能是阻断，也可能是自家送达）。
        HR = '[HookRunner] Hook "%s" (event: %s) exited with code %s. stderr: %s'

        # 6 真崩：exit1 本身不是判据，stderr 里的 Traceback 才是
        cli("2026-08-29T10:01:00.000+08:00",
            HR % ("python3 x/rule_three_layer_guard.py", "Stop", 1,
                  "Traceback (most recent call last): TypeError: expected string or bytes-like object"))
        lv = liveness()
        case("6 具名 Traceback→🔴真崩（判据=异常证据·非退出码）",
             lv.failures == 1 and lv.detail["delta"][0][4] == "crash")

        # 7 exit1 无异常证据=守卫按设计报"我检出了问题"→不计崩溃（把假绿换成假红不算根治）
        cli("2026-08-29T10:01:10.000+08:00",
            HR % ("python3 x/audit_search_kb.py", "Stop", 1, "本轮检索审计发现 2 条待补记"))
        lv = liveness()
        case("7 exit1 无异常证据→按设计非零·不计崩溃", lv.failures == 1 and lv.nonzero >= 1)
        # v0.20 步1分级双向夹具（工单2026-10-07任务卡·防"降级降成真崩也静默"）
        _tiers_hard, _tiers_un = _split_alert_tiers(
            [("t1", "a.py --x", 2, 126), ("t2", "b.py --y", 1, None)])
        case("36a 分级纯函数：具名崩与归因缺口分流不混",
             _tiers_hard == [("t1", "a.py --x", 2, 126)] and _tiers_un == [("t2", "b.py --y", 1, None)])
        import tempfile as _tf
        with _tf.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as _tj:
            _tp = _tj.name
        _defer_alerts([("t9", "zz_guard.py --json", 1, None)], path=_tp)
        _tl = open(_tp, encoding="utf-8").read()
        os.remove(_tp)
        case("36b 归因缺口降级：入deferred台账且带ts/cmd", '"kind": "unattributed_deferred"' in _tl and "zz_guard.py" in _tl)
        case("36c 混合delta不吞真崩：hard非空时un仅作附注(提醒分支以_hard为门)",
             _split_alert_tiers([("t", "x", 1, 127), ("t2", "y", 1, None)])[0] != [])

        # 8 可阻断事件 exit2=阻断信号；两条具名通道（HookRunner / unknown error 缩进行）都要认
        cli("2026-08-29T10:01:20.000+08:00",
            HR % ("python3 x/position3_notify.py", "UserPromptSubmit", 2, "deny"))
        cli_raw("  python3 x/position3_notify.py: unknown error, exit code 2, stderr: 阻断：需先跑三问")
        lv = liveness()
        case("8 可阻断事件 exit2→阻断信号（两条具名通道同判·不污染真崩数）",
             lv.failures == 1 and lv.blocks == 2)
        # 8b 裸续行没有时间戳 ⇒ 必须借上一行产品日志的时刻：ts 空的记录被 _split_by_window
        #    一律判 delta（朝红），修好后仍永远红 = 狼来了。取证 qodercli.log:7324 该通道确无时间戳。
        _s8, rs8, _k8, _u8, _c8 = _parse_receipts()
        blk = [r for r in rs8.records if r[4] == "block"]
        case("8b 裸续行借上一行时刻→能随修复回落（⛔永久红）",
             len(blk) == 2 and all(r[0].startswith("2026-08-29T10:01") for r in blk))

        # 9 真实反例（2026-08-29 实测）：python3 打不开文件时 exit 恰为 2——
        #    Stop 不可阻断，其 exit2 必须判崩溃，否则挂载写错路径=静默"看起来没事"
        cli("2026-08-29T10:01:30.000+08:00",
            HR % ("python3 x/doenglingz_guard.py", "Stop", 2,
                  "python3: can't open file '/tmp/x/doenglingz_guard.py': No such file or directory"))
        lv = liveness()
        case("9 Stop 上 exit2 + 打不开文件→仍判真崩（不判阻断/送达）", lv.failures == 2)

        # 10 自家告警用 exit2 顶进会话=送达；旧判据把它记成真崩＝对着自己的喊话报警
        cli("2026-08-29T10:01:40.000+08:00",
            HR % ("python3 x/feedback_detect.py --deliver", "Stop", 2, "配置守卫·2a38a3 本端钩子守卫"))
        lv = liveness()
        case("10 送达模式 exit2→计送达不计真崩",
             lv.failures == 2 and len(lv.detail["delivery"]) == 1)

        # 11 产品聚合行声明某钩子失败，而本守卫为**它**拿不到具名证据 ⇒ 差额朝红显形
        cli("2026-08-29T10:01:50.000+08:00",
            'Hook execution for Stop: 15 succeeded, 1 failed (python3 x/gate_runner.py)')
        lv = liveness()
        case("11 声明失败>具名证据→⚠️无法归因进 delta（不静默丢也不顶崩溃数）",
             lv.failures == 3 and any(r[4] == "unattributed" for r in lv.detail["delta"]))

        # 12 修复后告警必须回落：窗口起点推到所有崩溃之后 → 🔴delta 归零、⚪存量另栏可数
        t_noon = datetime.strptime("2026-08-29T12:00:00", "%Y-%m-%dT%H:%M:%S").timestamp()
        os.utime(sfile, (t_noon, t_noon))
        lv = liveness()
        case("12 链改动后旧崩溃→⚪存量（报警随修复回落）",
             lv.failures == 0 and len(lv.detail["backlog"]) == 3)
        case("12b 存量不谎称已修（仍在 detail 里可数、窗口起点可核对）",
             len(lv.detail["backlog"]) == 3 and lv.detail["since"].strftime("%m-%d") == "08-29")
        freeze_cfg()

        # 13 跳过标记按 run 归因：run1 有 user 回执（真会话不空报）；run2 只跳过（后台进程/换代失效态）
        d2 = os.path.join(runs, "run2")
        os.makedirs(d2, exist_ok=True)
        with open(os.path.join(d2, "qodercli.log"), "w", encoding="utf-8") as f:
            f.write('2026-08-29T10:03:00.000+08:00 INFO  debug.message User hooks skipped: '
                    'not in --setting-sources\n')
            f.write('2026-08-29T10:03:01.000+08:00 INFO  [session=bg turn=bg] hook.started '
                    'hook_name="Stop" hook_event_name="Stop" source="system" hook_index=1 '
                    'total_hooks=1 display_text="internal"\n')
        case("13 负例·skipped 归因（有回执会话不报/零回执会话报）",
             liveness("s").skipped is False and liveness("bg").skipped is True)

        # 14 宽限期（2026-08-29 实测态）：配置刚改、该链历史上有回执但改后还没轮到 → ⏳ 不算🔴；
        #    整条事件历史上零回执（SessionStart 未写过）→ 不豁免，仍 🔴
        t_now = datetime.now().timestamp()
        os.utime(sfile, (t_now, t_now))
        lv = liveness()
        # 待周期条数天然 = UPS 基准条数 − 夹具里已有回执的 1 条（position3）。
        # ⛔不得写死数字：pending 是遍历 BASELINE 算的（见 _liveness 内 `for evt, needles in BASELINE`），
        #    补一条基准，写死的期望就假红（2026-09-18 补 secret_key/ttl_expiry 两条时实测踩中·§三第5问同族）
        ups_expect = len(BASELINE["UserPromptSubmit"]) - 1
        case("14a 配置晚于该链最近回执→待周期（UPS=%d 条·扣已有回执 1 条）" % ups_expect,
             len(lv.pending) == ups_expect and not any("position3" in i for i in lv.pending))
        case("14b 负例·整条事件历史零回执不豁免（SessionStart/Stop 仍 🔴）",
             any("Stop" in i for i in lv.never) and any("SessionStart" in i for i in lv.never))

        # 14c 一条回执只替一个事件作证：Stop 的 crossend_guard.py --stop 不得同时点亮 SessionStart
        # （2026-10-03 改·判据不变只换前提：真机 --stop 孤儿挂载已撤除——该 needle ⛔不再依赖实挂存在，
        #   由夹具自建注入；撤挂载后若不注入，Stop 回执会经短子串匹配误点亮 SessionStart=本例要防的病本身）
        BASELINE["Stop"].append("crossend_guard.py --stop")
        try:
            d3 = os.path.join(runs, "run3")
            os.makedirs(d3, exist_ok=True)
            with open(os.path.join(d3, "qodercli.log"), "w", encoding="utf-8") as f:
                f.write('2026-08-29T11:00:00.000+08:00 INFO  [session=s3 turn=t] hook.started '
                        'hook_name="Stop" hook_event_name="Stop" source="user" hook_index=1 '
                        'total_hooks=1 display_text="python3 ~/.qoder-cn/hooks/crossend_guard.py --stop"\n')
            freeze_cfg()
            lv = liveness()
            cond_14c = (any("SessionStart: crossend_guard.py" in i for i in lv.never)
                        and not any("crossend_guard.py --stop" in i for i in lv.never))
        finally:
            BASELINE["Stop"].remove("crossend_guard.py --stop")
        case("14c 负例·Stop 侧 crossend_guard.py --stop 不替 SessionStart 作证（假绿回归）", cond_14c)

        # 15-17 查⑥ 实挂未入库（S064：守卫必须被证明会报警）
        repo = os.path.join(root, "repo")
        os.makedirs(repo, exist_ok=True)
        subprocess.run(["git", "init", "-q", repo], capture_output=True)
        os.makedirs(os.path.join(repo, "开发工具"), exist_ok=True)
        scripted = os.path.join(repo, "开发工具", "new_guard.py")
        with open(scripted, "w", encoding="utf-8") as f:
            f.write("# 新建守卫（自测夹具）\n")
        loose = os.path.join(root, "loose_guard.py")
        with open(loose, "w", encoding="utf-8") as f:
            f.write("# 无版本控制归属（自测夹具）\n")
        sfile2 = os.path.join(root, "settings_backing.json")
        json.dump({"hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": "python3 %s" % scripted}]},
            {"hooks": [{"type": "command", "command": "python3 %s" % loose}]},
        ]}}, open(sfile2, "w"), ensure_ascii=False)
        os.environ["QCN_SETTINGS"] = sfile2
        ut, out = git_backing()
        case("15 负例·实挂未入库→报（挂在链上但仓库没跟踪它）",
             any("new_guard.py" in i for i in ut) and not any("new_guard" in i for i in out))
        case("16 负例·实挂无仓库归属→显形（⛔不静默当作已纳管）",
             any("loose_guard.py" in i for i in out))
        subprocess.run(["git", "-C", repo, "add", "--", "开发工具/new_guard.py"],
                       capture_output=True)
        ut2, _ = git_backing()
        case("17 入库后不报（证明测的是「跟踪与否」而非「文件存在与否」）",
             not any("new_guard.py" in i for i in ut2))
        os.environ["QCN_SETTINGS"] = sfile
        rc = hook_mode()
        import json as _j
        _bad = {"hooks": {"SessionStart": _j.loads(_j.dumps([{"hooks": [{"type": "command",
            "command": "python3 x/crossend_guard.py"}]}]) * 1)}}
        _sf = os.path.join(root, "settings_bad.json")
        _j.dump(_bad, open(_sf, "w"))
        os.environ["QCN_SETTINGS"] = _sf
        rc_bad = hook_mode()
        # 18b/18c：真告警必须走送达通道（不得退回 stdout+exit0＝对着墙说话）
        case("18 真告警必须以 exit2 送达（⛔不得退回 stdout+exit0）", rc_bad == 2)
        _al = os.path.join(root, "alerts.jsonl")
        case("18b 投递须留收讫台账（供查⑩事后核送达）",
             os.path.exists(_al) and '"delivered"' in open(_al, encoding="utf-8").read())
        os.environ["QCN_SETTINGS"] = os.path.join(root, "不存在.json")
        rc = hook_mode()
        case("19 配置读取失败→hook 仍 exit 0 放行", rc == 0)

        # ── 20-25 GUI 源（questWindow/hooks.log）：第二只眼 + 三个失明点回归 ─────────────
        # 病灶（2026-09-12 逐条取证）：旧实现只扫 `[info] ` 行 ⇒ `--- stderr ---` 与
        # `Hook execute failed` 都挂在 `[warning]` 上、分支永不触发 ⇒ rule_three_layer_guard
        # 的 TypeError 真崩被降级判成 "design"=按设计 = **假绿**；超时行根本没有 exitCode ⇒ 完全不入账。
        from datetime import timedelta as _td
        gdir = os.path.join(gui_root, "20260101T000000", "questWindow")
        os.makedirs(gdir, exist_ok=True)
        glog = os.path.join(gdir, "hooks.log")
        sf_g = os.path.join(root, "settings_gui.json")
        json.dump(full, open(sf_g, "w"), ensure_ascii=False)
        t_win = (datetime.now() - _td(hours=6)).timestamp()
        os.utime(sf_g, (t_win, t_win))          # 窗口起点=6h 前 ⇒ 3h 前的回执算本轮
        os.environ["QCN_SETTINGS"] = sf_g
        stop_needles = BASELINE["Stop"]
        now_dt = datetime.now()
        h3 = (now_dt - _td(hours=3)).strftime("%Y-%m-%d %H:%M:%S.000")

        def gui(kind, body, ts=h3):
            with open(glog, "a", encoding="utf-8") as f:
                f.write("%s [%s] %s\n" % (ts, kind, body))

        def gui_bare(text):
            with open(glog, "a", encoding="utf-8") as f:
                f.write(text)

        def gui_reset():
            open(glog, "w").close()

        # 20 GUI started 回执计入 stat（CLI 源停更时判活不再瞎）
        gui_reset()
        for n in stop_needles:
            if "systemlog_stophook_check" in n:
                continue
            gui("info", "Hook execute started (command=python3 [记忆共享中心]/脚本中心/%s, cwd=/tmp)" % n)
        gui("info", "Hook execute completed (event=Stop, exitCode=0, "
                    "command=python3 [记忆共享中心]/脚本中心/audit_search_kb.py, cost=1ms)")
        gui("info", "Hook dispatch result (event=Stop, winner=none (no parsed output))")
        st_x, rs_x = {}, _RecSet()
        last_iso, _reload = _parse_gui_receipts(st_x, rs_x)
        case("20 GUI 回执被计入 stat 且 exit0 不报警（CLI 停更源不再等于看不见）",
             any(st_x.get(n, [0, ""])[0] > 0 for n in stop_needles)
             and len(rs_x.of("crash")) == 0 and last_iso != "")
        # 20b/20c 超时自恢复豁免（v0.11·2026-09-23 真机案：本端守卫自身 Stop 09:54 被
        #      产品 timed out，偶发 IO 抖动不该在无链改动时挂红数天=09-12"狼来了"案变体；
        #      ⛔朝红底线不动：无后续成功回执的超时照旧计红，豁免只认同命令其后成功硬证据）
        gui_reset()
        gui("warning", "Hook execute failed (timeout) "
                       "(command=python3 [记忆共享中心]/脚本中心/to_timeout_probe.py, timeout=30s)")
        lv = liveness()
        case("20b 超时且其后无成功→真崩计红（朝红不放宽）",
             any(r[5] == "timed out" for r in lv.detail["delta"]))
        _h2 = (now_dt - _td(hours=2)).strftime("%Y-%m-%d %H:%M:%S.000")  # 严格晚于 h3=其后
        gui("info", "Hook execute completed (event=Stop, exitCode=0, "
                    "command=python3 [记忆共享中心]/脚本中心/to_timeout_probe.py, cost=1ms)", ts=_h2)
        lv = liveness()
        case("20c 同命令其后成功回执→该超时豁免出红（告警随恢复回落）",
             not any(r[5] == "timed out" for r in lv.detail["delta"]))

        # 21 假绿回归：[warning] --- stderr --- 的裸续行 Traceback 必须归因成真崩
        gui_reset()
        gui("info", "Hook execute started (command=python3 [记忆共享中心]/脚本中心/"
                    "rule_three_layer_guard.py, cwd=/tmp)")
        gui("warning", "--- stderr ---")
        gui_bare('Traceback (most recent call last):\n'
                 '  File "/Users/x/[记忆共享中心]/脚本中心/rule_three_layer_guard.py", line 416, in <module>\n'
                 "    sys.exit(main())\n"
                 "TypeError: expected string or bytes-like object, got 'dict'\n")
        gui("info", "Hook execute completed (event=Stop, exitCode=1, "
                    "command=python3 [记忆共享中心]/脚本中心/rule_three_layer_guard.py, cost=527ms)")
        gui("info", "Hook dispatch result (event=Stop, winner=none (no parsed output))")
        st_y, rs_y = {}, _RecSet()
        _parse_gui_receipts(st_y, rs_y)
        case("21 GUI stderr 块按脚本名归因→exit1 判真崩（⛔不再降级成 design=假绿）",
             len(rs_y.of("crash")) == 1 and "TypeError" in rs_y.of("crash")[0][5])
        case("21b 同一轮一条崩溃只报一次（started/completed/stderr 不重复计）",
             len([r for r in rs_y.records if r[1].endswith("rule_three_layer_guard.py")]) == 1)

        # 22 无 exitCode 的失败类：超时=本轮没跑完（朝红），取消=用户中断（噪声，不计）
        gui_reset()
        gui("warning", "Hook execute failed (timeout) (command=python3 [记忆共享中心]/脚本中心/"
                       "知识联邦引擎/scripts/kb_inject_prompt.py UserPromptSubmit, timeout=30s)",
            ts=(now_dt - _td(minutes=40)).strftime("%Y-%m-%d %H:%M:%S.000"))
        gui("info", "Hook dispatch result (event=UserPromptSubmit, winner=none (no parsed output))",
            ts=(now_dt - _td(minutes=40)).strftime("%Y-%m-%d %H:%M:%S.000"))
        gui("warning", "Hook execute failed (canceled) (command=python3 [记忆共享中心]/脚本中心/"
                       "知识联邦引擎/scripts/kb_inject_prompt.py UserPromptSubmit)")
        st_z, rs_z = {}, _RecSet()
        _parse_gui_receipts(st_z, rs_z)
        case("22 超时无 exitCode 仍判真失效；取消不计（⛔不再完全不入账）",
             len(rs_z.of("crash")) == 1 and len(rs_z.records) == 1)

        # 23 归不上任何回执的崩溃证据 → unattributed（朝红），不静默吞
        gui_reset()
        gui("warning", "--- stderr ---")
        gui_bare('Traceback (most recent call last):\n'
                 '  File "/x/rogue_not_in_baseline.py", line 1, in <module>\n'
                 'ZeroDivisionError: division by zero\n')
        gui("info", "Hook dispatch result (event=Stop, winner=none (no parsed output))")
        st_w, rs_w = {}, _RecSet()
        _parse_gui_receipts(st_w, rs_w)
        case("23 无人认领的崩溃证据→⚠️无法归因（不静默吞）", len(rs_w.of("unattributed")) == 1)

        # 24 生效起点=产品重载时刻（真机 09-04 23:34 写入、09-05 05:39 才 handlers 22→23）
        gui_reset()
        for n in stop_needles:
            if "systemlog_stophook_check" in n:
                continue
            gui("info", "Hook execute started (command=python3 [记忆共享中心]/脚本中心/%s, cwd=/tmp)" % n)
        gui("info", "Hook config loaded (events=4, handlers=23)",
            ts=(now_dt - _td(minutes=10)).strftime("%Y-%m-%d %H:%M:%S.000"))
        lv_g = liveness()
        case("24 重载后尚未到 Stop 周期→判 ⏳ 不判 🔴（生效起点=重载时刻而非 mtime）",
             any("systemlog_stophook_check" in i for i in lv_g.pending)
             and not any("systemlog_stophook_check" in i for i in lv_g.never))

        # 25 重载发生在 30h 前且至今该守卫零执行 → 真 🔴（证明 24 不是万能宽限）
        gui_reset()
        for n in stop_needles:
            if "systemlog_stophook_check" in n:
                continue
            gui("info", "Hook execute started (command=python3 [记忆共享中心]/脚本中心/%s, cwd=/tmp)" % n)
        gui("info", "Hook config loaded (events=4, handlers=23)",
            ts=(now_dt - _td(hours=30)).strftime("%Y-%m-%d %H:%M:%S.000"))
        lv_h = liveness()
        case("25 宽限过期仍零执行→🔴从未执行（不沦为万能免罪）",
             any("systemlog_stophook_check" in i for i in lv_h.never))

        # 26 方向相反的失明：最近 3 份 GUI hooks.log 全 0 字节 ⇒ 双源实际只剩单源，必须显形
        gui_root2 = os.path.join(root, "gui_empty")
        for i in range(3):
            gd = os.path.join(gui_root2, "2026010%dT000000" % i, "questWindow")
            os.makedirs(gd, exist_ok=True)
            open(os.path.join(gd, "hooks.log"), "w").close()
        os.environ["QCN_GUI_LOGS"] = gui_root2
        case("26 GUI 源最近 3 份全 0 字节→🟡单源降级（⛔不再按双源口径静默结案）",
             any("单源降级" in w for w in source_freshness("")))
        case("26b 全空时仍退回 3 份空文件，让「看不见」可被 source_freshness 抓到",
             len(_gui_hooks_logs(3)) == 3
             and all(os.path.getsize(p) == 0 for p in _gui_hooks_logs(3)))

        # ── 27/27b PreToolUse 阻断型钩子的归因（2026-09-19 v0.5 立·v0.7 改造）──────────
        # 病灶形状：真机行是**无时间戳的裸缩进续行**、且**不带事件名**，事件只能反查。
        # 夹具用 x/ 假路径：真脚本刚改过 mtime 会重开真崩窗口，那样这条用例测不到判据。
        b0 = liveness()
        cli_raw("  python3 x/stamp_precheck_guard.py: unknown error, exit code 2, "
                "stderr: ⛔ [stamp_precheck] 变更记录行的落笔时间不是实取值（PAT-045 事前钩子）")
        lv27 = liveness()
        case("27 PreToolUse 入基准后：无名缩进行 exit2→阻断（⛔不落 HARD_EXIT_CODES 假红）",
             lv27.blocks == b0.blocks + 1 and lv27.failures == b0.failures)
        _e27, _n27 = _match("python3 x/stamp_precheck_guard.py")
        case("27b 负例·已登记钩子带异常证据→仍判真崩（认阻断不得把崩溃一起放绿）",
             _classify_record(1, _e27 or "", "python3 x/stamp_precheck_guard.py",
                              "Traceback (most recent call last): KeyError") == "crash"
             and _n27 == "stamp_precheck_guard.py" and _e27 == "PreToolUse")
        # 27c v0.7 改造（工单 D23 裁决）：原断言「未登记钩子的 exit2 仍判真崩」＝拿假红当逼迫器——
        # 报警每说谎一次，就多给下一个人关掉这条守卫的理由（l3_conclusion_guard 就是这么被永久关闭的）。
        # 现拆双向：①分类不失真（实挂未登记 → 归真实事件 → block）②欠账仍在（「实挂>基准」必须非空）。
        # 旧夹具的实挂集恰等于基准集，两套实现对它零分辨力（＝A 方案的风险被掩盖处），故必须造「挂载≠基准」形状。
        ghost = "some_unregistered_hook.py"
        _keep_settings = os.environ.get("QCN_SETTINGS")
        os.environ["QCN_SETTINGS"] = sfile          # 本段自管 settings 指向（前一组用例把它切去了 sf_g）

        def _judge27c():
            """27c 的可翻转判据本体：把同一形状分别在"实盘归属在岗/被置假"两态下各判一次。"""
            e, n = _match("python3 x/" + ghost)
            return (e == "PreToolUse" and n == ghost
                    and _classify_record(2, e or "", "python3 x/" + ghost, "阻断：需先跑三问") == "block")

        _mount_extra = json.loads(json.dumps(full))
        _mount_extra["hooks"].setdefault("PreToolUse", []).append(
            {"hooks": [{"type": "command", "command": "python3 x/%s" % ghost}]})
        json.dump(_mount_extra, open(sfile, "w"), ensure_ascii=False)
        _MOUNT_MEM["key"] = None
        _live27c = _judge27c()
        _e27c, _n27c = _match("python3 x/%s" % ghost)
        _m27_miss, _m27_dead, _m27_extra, _ = check()
        case("27c v0.7·实挂未登记的阻断型钩子：exit2 归到真实事件判阻断（分类不被登记绑架）",
             _live27c and _n27c == ghost)
        case("27c-2 同一形状下欠账照报（⚠️实挂>基准非空＝绿来自登记，只是换了诚实通道）",
             bool(_m27_extra) and "实挂" in _m27_extra[0])
        # 变异体（§3.9 出厂动作·两向探针）：把「实盘归属」这一路整体置假 ⇒ 27c 的**同一条判据必须转假**。
        # 若置假后 27c 仍为真，说明它的绿不是来自读实盘（＝靠放宽/来自恒真）。换输入不算变异，故换实现。
        _real_mounted = globals()["_mounted_pairs"]
        globals()["_mounted_pairs"] = lambda: None
        _MOUNT_MEM["key"] = None
        _stub27c = _judge27c()
        globals()["_mounted_pairs"] = _real_mounted
        _MOUNT_MEM["key"] = None
        case("27e 变异等价·实盘归属置假→27c 同一条判据必须翻假（证明它的绿来自读实盘，不是靠放宽）",
             _live27c and not _stub27c)
        json.dump(full, open(sfile, "w"), ensure_ascii=False)
        _MOUNT_MEM["key"] = None
        # 27d 回落律：settings 读不到 → 归属退回基准反查 → 未登记仍判崩（保持旧行为，不静默失明也不新增红）
        os.environ["QCN_SETTINGS"] = os.path.join(root, "读不到.json")
        _MOUNT_MEM["key"] = None
        _e27d, _n27d = _match("python3 x/" + ghost)
        case("27d 负例·settings 读不到→回落基准反查（未登记仍判真崩＝旧行为，⛔不静默也不加码）",
             _e27d is None and _classify_record(2, "", "python3 x/" + ghost, "阻断：需先跑三问") == "crash")
        os.environ["QCN_SETTINGS"] = _keep_settings
        _MOUNT_MEM["key"] = None
        # 29 归因对齐回归（v0.13·2026-10-01 真机假红"🔴钩子真崩3"）：夹具⛔不得让实挂集=基准集，
        #    否则对"声明侧 key"这类改动零分辨力（同 28 的教训）。这里照真机形状把 Stop 针子写成
        #    `rule_three_layer_guard.py --deliver`（比 BASELINE 长），batch 行 + 裸续行同命令。
        #  ⚠️夹具地雷（本轮实测踩过两次）：①日志须落 `<runs_dir>/<run>/*.log` 两层（glob=`*/*.log`），
        #    浅一层=空转；②settings✅DO另建专用文件并显式指 QCN_SETTINGS——此处 QCN_SETTINGS 已被 GUI
        #    用例切到 settings_gui.json，写回 sfile 是**惰性操作**，实挂集仍是"针子=基准"的恒等形状
        #    ⇒ 用例在变异体上照样绿（=自测恒真·S353 同族）。故 29 前置加"分辨条件自证"一条。
        div29 = json.loads(json.dumps(full))
        for _g in div29["hooks"]["Stop"]:
            for _h in _g.get("hooks", []):
                if "rule_three_layer_guard.py" in _h["command"]:
                    _h["command"] = "python3 x/rule_three_layer_guard.py --deliver"
        s29 = os.path.join(root, "settings29.json")
        json.dump(div29, open(s29, "w"), ensure_ascii=False)
        _keep_set29 = os.environ.get("QCN_SETTINGS")
        os.environ["QCN_SETTINGS"] = s29
        _MOUNT_MEM["key"] = None
        _keep_runs = os.environ["QCN_LOG_RUNS"]
        _b29 = ('2026-10-01T11:37:24.751+08:00 WARN  debug.message Hook execution for Stop: 21 succeeded, '
                '1 failed (python3 x/rule_three_layer_guard.py --deliver), total duration: 21745ms')
        _c29 = ('  python3 x/rule_three_layer_guard.py --deliver: unknown error, exit code 2, '
                'stderr: [三层守卫·5617cd] 记忆规则三层漂移：铁律集合上界不一致')

        def _runs_with(name, lines):
            d = os.path.join(root, name, "run1")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "qodercli.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            os.environ["QCN_LOG_RUNS"] = os.path.join(root, name)

        case("29-pre 分辨条件自证·实挂针子确比基准长（针子相同则 29 无意义）",
             ("Stop", "rule_three_layer_guard.py --deliver") in (_mounted_pairs() or [])
             and "rule_three_layer_guard.py --deliver" not in BASELINE.get("Stop", []))

        def _judge29():
            """29 的可翻转判据本体：真机形状下，声明侧与具名侧是否归到**同一个** key。"""
            _runs_with("runs29a", [_b29, _c29])
            _st, rsx, _sk, _ur, _cr = _parse_receipts()
            return (not [r for r in rsx.records if r[4] == "unattributed"]
                    and any(r[4] in ("block", "delivery") for r in rsx.records))

        _live29 = _judge29()
        case("29 声明侧与具名侧同 key→差额归零（实挂针子带 --deliver 的真机形状·v0.13 归因对齐）",
             _live29)
        # 29b 负例·同一形状下真拿不到具名证据 ⇒ 差额照记 unattributed（改 key⛔不放松判据）
        _runs_with("runs29b", [_b29])
        _s29b, rs29b, _k29b, _u29b, _c29b = _parse_receipts()
        case("29b 负例·带 --deliver 的声明无具名证据→仍显形（假红修掉，真失明不放过）",
             len([r for r in rs29b.records if r[4] == "unattributed"]) == 1)
        # 29e 变异等价（§3.9 出厂动作·换实现不换输入）：把「声明侧 key 对齐」整体置假＝退回 v0.12
        #    用基准针子造 key 的实现 ⇒ 29 的**同一条判据必须转假**。置假后仍为真＝29 是恒真用例
        #    （本轮首版实测正是如此：夹具 settings 写回被上游用例切走的共享路径⇒绿得没有对象）。
        _real_declared = globals()["_declared_key"]
        globals()["_declared_key"] = lambda evt, n, names: (evt, n)
        _stub29 = _judge29()
        globals()["_declared_key"] = _real_declared
        case("29e 变异等价·声明侧 key 对齐置假→29 必翻假（证明它的绿来自同源，不是靠放宽）",
             _live29 and not _stub29)
        os.environ["QCN_LOG_RUNS"] = _keep_runs
        os.environ["QCN_SETTINGS"] = _keep_set29
        _MOUNT_MEM["key"] = None

        # ── 30/31 提醒面同源回归（v0.14·2026-10-02 工单「🔴钩子真崩1(最近:… exit=—)」假红）──────
        # 修A：unattributed 差额行 ts 落回其自身声明时刻（尾贪心配对），⛔不再借「该 key 最近
        # 一次声明时刻」的壳——真机探针复现病灶形状：8 月声明无证据 + 窗口内声明有证据 ⇒
        # 旧实现把存量差额记到最新声明时刻=落进当前窗口（工单「提醒面取存量」的机械本体之一）。
        s30 = os.path.join(root, "settings30.json")
        json.dump(full, open(s30, "w"), ensure_ascii=False)
        _t30w = datetime.strptime("2026-08-29T11:00:00", "%Y-%m-%dT%H:%M:%S").timestamp()
        os.utime(s30, (_t30w, _t30w))            # 窗口起点=11:00 ⇒ 10:01 声明在存量侧
        _keep_set30 = os.environ.get("QCN_SETTINGS")
        os.environ["QCN_SETTINGS"] = s30
        _old_b30 = ('2026-08-29T10:01:50.000+08:00 WARN  [session=s turn=t] '
                    'Hook execution for Stop: 15 succeeded, 1 failed (python3 x/gate_runner.py)')
        _new_b30 = ('2026-08-29T11:30:00.000+08:00 WARN  [session=s turn=t] '
                    'Hook execution for Stop: 20 succeeded, 1 failed (python3 x/gate_runner.py --deliver)')
        _new_h30 = ('2026-08-29T11:30:01.000+08:00 WARN  [session=s turn=t] '
                    + HR % ("python3 x/gate_runner.py --deliver", "Stop", 2,
                            "配置守卫·a1b2c3 本端钩子守卫"))

        def _judge30():
            """修A 的可翻转判据本体：同 key 两条声明、最新一条有具名证据 ⇒ 差额=更旧声明（⚪存量）不落当前窗口。"""
            _runs_with("runs30a", [_old_b30, _new_b30, _new_h30])
            lv30x = liveness()
            return (lv30x.failures == 0 and len(lv30x.detail["backlog"]) == 1
                    and lv30x.detail["backlog"][0][0].startswith("2026-08-29T10:01"))

        # 30-pre 分辨条件自证（§3.0·5·29-pre 同型）：夹具两条声明必须真的跨窗口起点——
        # 若都在窗口内，借壳也红/配对也红=零分辨力，30 的绿没有对象。
        _runs_with("runs30p", [_old_b30, _new_b30, _new_h30])
        _st30p, rs30p, _k30p, _u30p, _c30p = _parse_receipts()
        _dtl30p = rs30p.declared_times.get(("Stop", "gate_runner.py"), [])
        case("30-pre 分辨条件自证·同 key 两条声明跨窗口起点（无借壳形状则 30 无意义）",
             len(_dtl30p) == 2 and _dtl30p[0] < "2026-08-29T11:00" < _dtl30p[1])
        _live30 = _judge30()
        case("30 窗口内声明已具名·存量差额 ts 落回自身声明（⚪存量不进当前窗口不朝红）",
             _live30)
        # 30b 负例·验收判据的另一侧：窗口内声明无具名证据 ⇒ 差额行照进 delta（⛔修展示不修成失明）
        _runs_with("runs30b", [_old_b30, _new_b30])
        lv30b = liveness()
        case("30b 负例·窗口内声明无证据→unattributed 照常红（修A 不附带失明）",
             lv30b.failures == 1 and lv30b.detail["delta"][0][0].startswith("2026-08-29T11:30"))
        # 30e 变异等价（§3.9 换实现不换输入）：ts 配对整路置假=退回旧「取最近声明借壳」实现
        #   ⇒ 30 同一条判据必须翻假；置假后不翻=30 恒真（29e 同训）。
        _real_pair30 = globals()["_pair_unproven"]
        globals()["_pair_unproven"] = lambda d, nm: [max(d)] * max(0, len(d) - len(nm))
        _stub30 = _judge30()
        globals()["_pair_unproven"] = _real_pair30
        case("30e 变异等价·差额 ts 配对置假→30 必翻（证明它的绿来自同源，不是靠放宽）",
             _live30 and not _stub30)

        # 31 超时当轮自证（修B·真机实录：13:07 超时击杀→13:13 当轮成功回执物理未落盘 ⇒
        #   v0.11 只看落盘回执的判据必然滞后一轮——已恢复的存量旧账被提醒面摆进当前告警，
        #   人工复跑 report 时回执已落又消失=本案「真崩1 vs 真崩0」的生成机制）。
        #   双向断言钉验收：无自证侧照常红（=20b 同形，防「当轮自证沦为万能免罪」）| 自证侧豁免。
        # ⚠️夹具地雷（29 注释同款教训的复发防御）：26 系列把 QCN_GUI_LOGS 切到全空目录
        # （gui_root2·单源降级夹具）后未复位——写入端 gui() 走 glog 常量不受影响、
        # 读取端 _gui_hooks_logs 走 env ⇒ 不复位=31 的 timeout 行物理读不到（假红=用例自污染）。
        os.environ["QCN_GUI_LOGS"] = gui_root
        gui_reset()
        gui("info", "Hook execute started (command=python3 x/qodercn_config_guard.py hook, cwd=/tmp)")
        gui("warning", "Hook execute failed (timeout) "
                       "(command=python3 x/qodercn_config_guard.py hook, timeout=30s)")
        gui("info", "Hook dispatch result (event=Stop, winner=none (no parsed output))")

        def _judge31():
            """修B 的可翻转判据本体：同一形状，仅差「当轮自证在/不在」⇒ 红↔豁免必须翻转。"""
            _no31 = liveness()
            _yes31 = liveness(None, "qodercn_config_guard.py")
            return (any(r[5] == "timed out" for r in _no31.detail["delta"])
                    and not any(r[5] == "timed out" for r in _yes31.detail["delta"]))

        _live31 = _judge31()
        case("31 超时无自证照常红（30-pre 式形状自证并入）| 同命令当轮自证→存量超时出红（恢复确认不滞后一轮）",
             _live31)
        # 31e 变异等价·当轮自证整路置假 ⇒ 31 必翻（证明它的绿来自新证据源，不是豁免后门）
        _real_probe31 = globals()["_self_probe_exempts"]
        globals()["_self_probe_exempts"] = lambda r, s: False
        _stub31 = _judge31()
        globals()["_self_probe_exempts"] = _real_probe31
        case("31e 变异等价·当轮自证置假→31 必翻（落盘回执判据本体未动·自证是事实源非放宽）",
             _live31 and not _stub31)
        os.environ["QCN_SETTINGS"] = _keep_set30
        _MOUNT_MEM["key"] = None

        # 32 空 stderr 阻断形状配对（v0.19·真机 grep_sandbox_guard 两例）：batch 声明+无 stderr 续行
        #    ⇒ 具名应扫到、差额归零、分类=block（非崩）。32-pre 形状自证防夹具造错（旧严格正则必须
        #    匹配不上本形状，否则夹具=旧已支持形状、32 零分辨力）；32b 负例钉"判据不放宽"。
        _b32 = ('2026-10-07T12:35:48.452+08:00 WARN  debug.message Hook execution for PreToolUse: '
                '8 succeeded, 1 failed (python3 x/grep_sandbox_guard.py), total duration: 8275ms')
        _c32 = '  python3 x/grep_sandbox_guard.py: unknown error, exit code 2'
        case("32-pre 分辨条件自证·本形状确无 stderr 段（严格旧正则匹配不上）",
             re.compile(r"^\s{2,}(.+?): unknown error, exit code (-?\d+), stderr: (.*)").search(_c32) is None)

        def _judge32():
            """32 的可翻转判据本体：无 stderr 具名行在场时，声明↔具名配对且归 block。"""
            _runs_with("runs32a", [_b32, _c32])
            _st, rsx, _sk, _ur, _cr = _parse_receipts()
            return (not [r for r in rsx.records if r[4] == "unattributed"]
                    and any(r[4] == "block" and "grep_sandbox" in (r[1] or "") for r in rsx.records))

        _live32 = _judge32()
        case("32 空 stderr 阻断续行被具名扫到→声明配对、差额归零、归 block（v0.19）", _live32)
        _runs_with("runs32b", [_b32])   # 负例·真无具名证据
        _s32b, rs32b, _k32b, _u32b, _c32b = _parse_receipts()
        case("32b 负例·声明在场具名真缺→差额照记 unattributed（补形状⛔不放松判据）",
             len([r for r in rs32b.records if r[4] == "unattributed"]) == 1)
        # 32e 变异等价（§3.9）：整路置回严格正则 ⇒ 32 必翻，证明绿来自可选组不是别处放宽
        _real_unk32 = globals()["UNK_RE"]
        globals()["UNK_RE"] = re.compile(r"^\s{2,}(.+?): unknown error, exit code (-?\d+), stderr: (.*)")
        _stub32 = _judge32()
        globals()["UNK_RE"] = _real_unk32
        case("32e 变异等价·可选 stderr 组置假→32 必翻（绿来自形状补扫，非判据放宽）",
             _live32 and not _stub32)
        os.environ["QCN_LOG_RUNS"] = _keep_runs
        _MOUNT_MEM["key"] = None

        # 28 本体符号唯一性＝QCN-20260919-003 的物理承接器。撤销/回滚类补丁的病是"后定义遮蔽前定义"，
        #    而自测的输入域由被检代码自己构造（实挂集=基准集）时对两版实现零分辨力——commit e0515508 那次
        #    留了 126 行逐字副本、9 个顶层符号×2，37/37 全绿照样看不出来。只数自己文件的顶层符号，
        #    重复即红：门禁检测域✅DO含"撤销动作的产物"本身（与 2026-08-27 覆盖式 Write 清空正文同族）。
        import ast as _tree
        import collections as _cnt
        _own = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            os.path.basename(__file__))
        _names = []
        for _node in _tree.parse(open(_own, encoding="utf-8").read()).body:
            if isinstance(_node, (_tree.FunctionDef, _tree.AsyncFunctionDef, _tree.ClassDef)):
                _names.append(_node.name)
            elif isinstance(_node, _tree.Assign):
                _names += [t.id for t in _node.targets if isinstance(t, _tree.Name)]
        _dups = sorted(k for k, v in _cnt.Counter(_names).items() if v > 1)
        case("28 本体顶层符号唯一（遮蔽副本存活=撤销不彻底·%d 个符号在检）" % len(_names), not _dups)
        # §3.9 承接标记（guard_selftest_check v0.3 消费）：四处判据各自置假→对应功能例必须翻转，
        #   任一不翻转＝那条用例恒真＝MUT:FAIL（rc 仍 0 也算红，⛔PASS 不算交付证据）。
        #   ⚠️本行✅DO留在 try 内：中途抛异常则标记不落＝聚合器按"未承接"归因本件（Fail-Closed），
        #   ⛔DO NOT 挪进 finally（那会让崩掉的自测也印出 MUT:OK＝自证式假绿）。
        _mut = (bool(_live27c and not _stub27c) and bool(_live29 and not _stub29)
                and bool(_live30 and not _stub30) and bool(_live31 and not _stub31)
                and bool(_live32 and not _stub32))
        print("  %s MUT:%s 变异自检五处（27e 实盘归属置假／29e 声明侧 key 置假／30e 差额 ts 配对置假／31e 当轮自证置假／32e 可选 stderr 组置假）→ 功能例均翻转"
              % ("✅" if _mut else "❌", "OK" if _mut else "FAIL"))
        os.environ["QCN_SETTINGS"] = sfile
    finally:
        for k in ("QCN_SETTINGS", "QCN_LOG_RUNS", "QCN_GUARD_STATE", "QCN_GUI_LOGS"):
            os.environ.pop(k, None)

        shutil.rmtree(root, ignore_errors=True)
    print("自测结果：%d 通过 / %d 失败" % (ok, fail))
    return 0 if fail == 0 else 1


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "check"
    if a == "check":
        missing, dead, extra, _ = check()
        for i in missing:
            print("MISSING " + i)
        for i in dead:
            print("DEAD_SHAPE " + i)
        for i in extra:
            print("EXTRA " + i)
        print("check OK" if not (missing or dead or extra) else "check FAIL")
        return 0 if not (missing or dead or extra) else 1
    if a == "liveness":
        lv = liveness()
        for i in lv.never:
            print("NEVER_RAN " + i)
        for i in lv.pending:
            print("PENDING_FIRST_CYCLE " + i)
        for i in lv.stale:
            print("STALE " + i)
        if lv.failures:
            print("CRASH_FAILURES %d" % lv.failures)
        for r in lv.detail["delta"]:
            print("CRASH_DETAIL " + _fmt_receipt(r))
        if lv.detail["backlog"]:
            print("BACKLOG_COUNT %d" % len(lv.detail["backlog"]))
        un = [r for r in lv.detail["delta"] if r[4] == "unattributed"]
        if un:
            print("UNATTRIBUTED_COUNT %d" % len(un))
        if lv.detail["delivery"]:
            print("DELIVERY_COUNT %d" % len(lv.detail["delivery"]))
        if lv.nonzero:
            print("NONZERO_BY_DESIGN %d" % lv.nonzero)
        if lv.blocks:
            print("BLOCK_SIGNALS %d" % lv.blocks)
        if lv.skipped:
            print("USER_HOOKS_SKIPPED true")
        print("liveness hits=%d never=%d" % (lv.hits, len(lv.never)))
        return 0 if not (lv.never or lv.stale or lv.failures or lv.skipped) else 1
    if a == "hook":
        return hook_mode()
    if a == "--self-test":
        return self_test()
    if a in ("report", "--report"):
        return report()
    print(__doc__)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as e:
        print("guard 异常（不阻塞）：%s" % e)
        # ⛔只写 stdout = 产品丢弃 = 守卫自身崩了没人知道（exit 0 假成功同族）⇒ 走告警通道
        rc = 0
        try:
            if _hp is not None:
                rc = _hp.alert("配置守卫·自身异常",
                               "🔴 钩子守卫自身异常，判活已失明：%s" % e, via_hook=True)
        except Exception:
            pass
    sys.exit(rc)
