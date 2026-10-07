#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三明智结论块封口（triwich_seal v1.5.5）—— 阶段3 物理锁层 + 决策卡回访挂载

v1.5.5（2026-09-21·R6 尾批）：单横线已知 flag 别名旁路封死（-tool 类一律确定性拒）+ 注释落点措辞逐字对应。

v1.5.4+D18（2026-09-26·Qoder CN 童灵·⛔不跳版本号，同族 v1.5.x 多端共写·抢号即造新漂移）：verify 的「链尾会话≠当前会话」分支补**口径提示**——链尾键形如「端名:文本sha1前12」＝该跳由 record --text-file 封口，而 verify 未传同一文件时拿运行时会话 id 比对，两者永不可能相等，旧文案独指「可能被删除」会把审计者推向修一条根本没发生的删除。⛔判定逻辑与退出码一字未动（只加提示串）。实测判别力：真链 62 跳中 text-file 键形 58（触发提示）／sess_ 运行时段 4（不触发），正则 ^[^:]+:[0-9a-f]{12}$ 对两类零混淆。
v1.5.4（2026-09-21·R5 终批）：缺值族确定性拒绝（--text-file/--followup 空值≠未提供·静默换源/静默蒸发双洞封死）+ 单横线未知 token 并入黑名单 + 空链二因并陈 + help 行按实现拆分。

v1.5.3（2026-09-21·R4 终批）：help 契约收窄仅首参（恒真旁路/值位假成功封死）+ resolve 序号双形态归一（FU-N/n 皆可）+ verify 三态分流（"本会话未封口"≠"链尾被删"）+ 锁超时消息附 rm -rf 恢复路径。

v1.5.2（2026-09-21·clock-loop 名单#3 Loop·v4.4.9-v4.4.11 三批收口的脚本载体版本）：decision-room/seal.log 双并发锁（_acquire_path_lock 单实现泛化）+畸形行/坏留痕显形+dispatch 修复（help 前置/未知子命令拒/list 名实/SKIP 文案三分）+端数声明去手抄。

v1.5.1（2026-09-18·Qoder CN 端·同轮自我打脸后加固）：v1.5.0 落地当天即被自己的锚抓到两处缺陷——
  ① 锚判据从「最近一行留痕」改为「24h 窗口内任一行留痕含本 seq」：只看最后一行时，任何并发写者都能
     把诚实回访打成假阴性——实测触发：本端夹具泄漏行（不含 FU-34）落在最后一行，导致 FU-34 真回访被自己的锚拒掉。
  ② 前置筛查把「无判假方式」的存量卡显形为 ⚠️无判假式（此前只认「（缺…」占位符→v1.4.1 硬门禁之前的
     老卡永远静默绿·实测 16 条待回访中 15 条命中（唯一带判假式的正是本端 FU-34））。⛔筛查只显形，不替立单端代写判据（判据属立单者
     的判断，代写＝制造第二本账）。另修夹具 env 泄漏：test_triwich_decision_room.py 未覆写 FOLLOWUP_LEDGER，
     夹具行污染真 followup_ledger.log——该泄漏由本次新加的锚自己拒单抓到（外锚顺带证明了写留痕的必要性）。

v1.5.0（2026-09-18·Qoder CN 端·皮叔令「认可方案去做吧」）：**G2「机制回访」物理锚**——resolve 的 --mechanism 原仅校验枚举 ∈{mechanism,manual,AI想起}，不校验「本卡是否真由 followup 前置筛查发起」⇒ A 值（已回访中 mechanism 占比·三账分工口径表 #2）的分子是 AI 自报字符串，与自家规范判据 13「判据制定者≠执行者·三权合一则指标必然可自我拔高」相抵（A 值曾因 FU-23 记 manual 从 1.0 掉到 0.900，可见该标记有真实权重，就更不能留自报口子）。根治三步：①followup 每次运行落一行 append-only 留痕（0 命中也落=「确实查过」的证据）②resolve 标 mechanism 须同时满足「本 seq 在最近一次留痕内」+「留痕 ≤ MECHANISM_MAX_AGE_HOURS(24h)」③缺留痕/坏行/超龄/查无此 seq 一律 FAIL-Closed 并给补法（重跑 followup，或如实改标 manual/AI想起）。留痕载体 followup_ledger.log——与 seal.log 同 .gitignore 策略（运行时态不入版本库，⛔不把台账混进 git 变第二本账）。

v1.4.2（2026-09-18·Qoder CN 端·皮叔令「给我符合愿景的最优解」）：
  ① 待决卡补「不变」态——record 新增 --deadline/--default（缺则卡上自动标 ⚠️到期不显形／⚪黑洞候选），
     followup 三态显形：未到期无标／超期 🔴超期未裁／无默认 ⚪。⛔默认分支只允许 no-op，
     禁承载价值动作（发版/晋升/回滚/写规则）——否则"到期默认"从安全阀变越权通道。
  ② 未知 flag 显式拒绝（KNOWN_FLAGS 白名单）——实跑取证：record --help 被 parse_kv 吞成未知 kv，
     走无 --text-file 回退分支后对他端老会话真写了一条封口（幻影链尾·已备份后摘除）。
v1.4.1（2026-09-18 D10·Qoder CN 端）：决策卡登记新增内容门禁 --falsify 判假方式——FU-4 实测判例：
  条件式预测把本方会做的修复当前件＝恒真预测（补了就永远不可判），回访无法计分。
  分级硬拦：FALSIFY_HARD_SINCE 前 WARN＋卡片标"（缺·弱判据）"，后 FAIL 拒绝登记（单常量可回落）。
v1.4.0（2026-09-14 全端覆盖·方案C·WorkBuddy 端·你"不管哪个端启动都能记录"）：
- record 新增 --text-file：三明智收尾时把本轮结论块+签名文本写入文件传参——任何端无需
  "读本端异构会话存储"即可封口（一次覆盖全端+未来新端；session 键=端名:文本sha1前12）。
- Fail-Loud：未提供 --text-file 且读不到会话历史 → 返回 FAIL（code=1），不再静默"跳过"
  （根治"未适配端静默放行不记录"）。--followup 仅在真封口时登记（不变）。
- 设计依据（第一性原理）：输入来源不影响痕迹锁死性 → 自包含（收尾传文本）不损防伪本质；
  且"读会话文件"路线在多会话并行下按 mtime 定位必错位（2026-09-14 实测实封他会话旧签名）。

v1.3.1（2026-09-13 首封实测语义修复·ZCode 端）：
- JSONL reader 定位规则升级：从"最后一条非空文本"改为"**最近一条含三明智签名（SIG_RE）的文本**"——
  实测依据：ZCode rollout 将每段文本（中间叙述/工具调用间文本/最终结论）拆为独立 model_io，
  回复结束后的任何时点跑 record，"最后一条文本"必是后续轮次开场白（无签名）→ 封口永远放行。
  按签名定位后语义="封最近一次三明智轮"，补封场景（下轮开头补上轮）成立，verify 对账同口径自洽。

v1.3.3（2026-09-13 端真源对齐·你令抓过时口径·ZCode 端）：
- ⛔ 端清单真源=system-logger/scripts/normalize_tool.py ALLOWLIST（端数以该文件实时为准·⛔本注释不手抄计数(v4.4.11·R3-N6：旧「18 端」实已 21)·本脚本 v1.1.0 内嵌
  6 候选=过时快照·你抓"五端六端怎么一直存在"）——本脚本探测表只是"已适配实现"，
  新端适配在此登记+decision-room 自检节同步缺口，真源变动以 ALLOWLIST 为准。
  注（v4.4.9·R1-P2-08 措辞如实化）：--tool 端名=会话来源自由文本标签，本脚本不对其做
  ALLOWLIST 校验（跨包 import 脆性>收益）；⛔端名不得直接充当按端统计口径，统计须经
  normalize_tool 归一（真源在外·此声明与实装对齐）。
- load_latest_history 文件名匹配放宽：agent%3Amain%3A → agent%3A*（agent 名任意）——
  实测 AutoClaw 实盘文件为 agent%3Aauto-designer%3A* 等，旧模式实盘恒空转。
- JSONL_SOURCES +WorkBuddy AI（~/.workbuddy-ai/projects/*/*.jsonl·实测与 WB 同构·wb reader 复用）。

v1.3.2（2026-09-13 登记会话字段传递链修复+封口幂等·ZCode 端）：
- record 返回四元组（+sess），main 将真值传 register_followup——修 FU 台账"会话"字段误取
  老端 fallback 名（首封实锤：台账记 agent%3Amain%3A3144bcb2.json 而封口链实为 sess_c6c2e093）。
- record 幂等去重：链尾已是同会话同指纹 → "已封口不重复"（v1.3.1 按签名定位的副作用：
  同轮多次 record 会重复入链·实锤链长 2 同指纹双跳）；sealed=False→--followup 亦不重复登记。
- FU-1 会话字段已按铁律-002 纠错格式手工修正留痕。

v1.3.0（2026-09-13 跨端适配·G2 全端数据收口·ZCode 端）：
- 新增 JSONL reader 双端适配（load_latest_text 三 reader 分派）：
  ① WorkBuddy（~/.workbuddy/projects/*/*.jsonl·行 {"role":"assistant","content":[{type,text}]}）
  ② ZCode（~/.zcode/cli/rollout/model-io-sess_*.jsonl·行 {"type":"model_io","response":{"text"},"sessionId"}）
  ③ 老端 json 数组（AutoClaw/QoderCN/Trae 等·原 load_latest_history 不变）
- 实探依据：v1.1.0 的 WB 探测路径 ~/.workbuddy/chat-history 实盘不存在（M2 轮实锤缺口）——
  WB 真实对话在 projects/<ws>/<uuid>.jsonl；ZCode 此前完全不在探测列表（实盘 record 必空转）。
- 测试隔离：JSONL_ENABLED 开关（测试 monkeypatch 置 False 走老路径）+ JSONL_SOURCES 可注入

v1.2.0（2026-09-13 G2 回访机制 M2 接钩子·ZCode 端）：
- record 新增 --followup 参数：封口成功且本轮有可预测结论时，同轮向 references/decision-room.md
  追加一条「待回访」登记（G2 应回访标记·封口挂载=每轮物理必经点·对齐阶段A收尾协议"必填非记得才填"）
- 新增 followup 子命令：待回访前置筛查——Step0 键铸造后跑，列出全部待回访条目（命中即先回访再分析）
- 新增 resolve 子命令：回访销账——状态翻转 待回访→已回访 + 回填"实际/偏差类型(B0-B9枚举)/归因/修正"
  四件套（缺任一拒绝·Fail-Closed；按行改写禁切片拼接·指令编写规范 §1.5）
- 登记数据唯一 source = references/decision-room.md（接口mapping红线2·防双本账）；测试用
  TRIWICH_DECISION_ROOM 环境变量隔离（对齐 TRIWICH_SEAL_LOG 模式）
- record 改返回三元组（code,msg,sealed）：--followup 仅在真封口（有签名）时挂登记，无签名不登记

v1.1.1（2026-09-05 根治对抗3删链尾放行漏洞·Trae Work端实测发现）：
- 修复 verify 对账用「链中存在当前会话记录」判走导致的删尾放行——改为要求链尾=当前会话，
  任何删尾/删中间跳/改内容/改日志都被拦截（三对抗实测：改内容FAIL/改日志FAIL/删尾FAIL）
- 实测方式：fixture(伪造含三明智签名chat-history)+TRIWICH_HIST_DIR/TRIWICH_SEAL_LOG环境变量跨工具实跑

v1.1.0（2026-09-04 跨工具通用改造）：
- 自动检测当前工具的chat-history目录（AutoClaw/Qoder CN/WorkBuddy/Trae Work等）
- 符合愿景"能通用的，就不要只绑定在一个工具上"（皮叔 2026-09-04 要求）
- 优先使用环境变量TRIWICH_HIST_DIR，否则自动检测
- 位置：从开发工具目录迁移到skill本体scripts/目录（~/[记忆共享中心]/技能配置/triwich/scripts/triwich_seal.py）

模式（对齐 verify_achievement_seal.py：盐+真实数据派生+独立校验器）：
- record：从最新 chat-history 提取三明智完成签名+结论块段头 → 计算 seal 追加到哈希链日志
- verify：从 chat-history 重算 seal 与日志比对 + 校验哈希链完整性（任一跳被篡改=链断裂）

v1.0.1（2026-08-12 对抗测试修复）：指纹覆盖结论块全文（段头→签名间内容）——
  只锁签名行/段头时改内容可绕过（对抗2 实测）；verify 增加"当前会话必须有记录"检查（整链删除检测）。

链设计：entry = ts|session|seal|prev_hash|self_hash
  self_hash = sha256(ts|session|seal|prev_hash)[:16]
  篡改任何一跳（改/删/插）→ self_hash 不匹配或 prev 不连续 → verify 报断裂

强度边界（诚实声明）：本地同权限环境，AI 可同时改写 chat-history 与 seal.log——
哈希链的价值 = 使"选择性篡改"不可行（改一条须重写全链）且篡改可被检测；
真正不可伪造层 = 外部快照（root 进程/远程仓库），属可选增强（需你配置）。
已知局限（对抗3 实测）：无外部参考时无法检测"链尾部被截断"——删最后一跳后链仍完整；
  解法=外部快照（cron/root 把链尾 self_hash 抓到独立位置，verify 对账）。

威胁模型：非恶意偷懒下，seal 提供"事后审计可检测输出被改过"的证据完整性。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import json
import re
import hashlib
from datetime import datetime

SEAL_SALT = "triwich-seal-v1"
LOG_PATH = os.path.expanduser("[记忆共享中心]/技能配置/triwich/scripts/seal.log")  # 2026-09-04随guard迁移：器官随Skill走（历史日志留原开发工具目录）
# 自动检测当前工具的chat-history目录（跨工具通用·符合愿景"能通用的，就不要只绑定在一个工具上"）
def detect_chat_history_dir():
    """自动检测当前工具的chat-history目录"""
    candidates = [
        ("~/.openclaw-autoclaw/autoclaw/chat-history", "AutoClaw"),
        ("~/Library/Application Support/QoderCN/chat-history", "Qoder CN"),
        ("~/.workbuddy/chat-history", "WorkBuddy"),
        ("~/.trae/work/chat-history", "Trae Work"),
        ("~/.qoder-cn/chat-history", "Qoder CN IDE"),
        ("~/.qoderworkcn/chat-history", "QoderWork CN"),
    ]
    for path, tool in candidates:
        expanded = os.path.expanduser(path)
        if os.path.isdir(expanded):
            return expanded, tool
    return None, None

# 优先使用环境变量，否则自动检测
HIST_DIR_ENV = os.environ.get("TRIWICH_HIST_DIR")
if HIST_DIR_ENV:
    HIST_DIR = os.path.expanduser(HIST_DIR_ENV)
    TOOL_NAME = "环境变量指定"
else:
    HIST_DIR, TOOL_NAME = detect_chat_history_dir()
    if HIST_DIR is None:
        HIST_DIR = os.path.expanduser("~/.openclaw-autoclaw/autoclaw/chat-history")
        TOOL_NAME = "AutoClaw (default fallback)"
LOG_PATH = os.environ.get("TRIWICH_SEAL_LOG", LOG_PATH)
# 决策卡台账（G2 回访闭环唯一 source）——环境变量仅测试隔离用
DECISION_ROOM_PATH = os.environ.get("TRIWICH_DECISION_ROOM") or os.path.expanduser(
    "~/[记忆共享中心]/技能配置/triwich/references/decision-room.md")

# —— G2「机制回访」物理锚（v1.5.0·2026-09-18 Qoder CN·L2 裁决）——
# 病灶：resolve 的 --mechanism 仅校验枚举，不校验「这张卡是否真由 followup 前置筛查发起过」
#   ⇒ A 值（已回访中 mechanism 占比·三账分工口径表 #2）的分子可被 AI 自报，与自家规范判据 13
#   「判据制定者≠执行者·三权合一则指标必然可自我拔高」相抵（A 值曾因 FU-23 记 manual 从 1.0 掉到 0.900）。
# 根治：followup 每次运行落一行 append-only 留痕；resolve 标 mechanism 时须在该留痕里查得到本 seq。
# 载体取 .log 后缀 —— 运行时状态不入版本库（triwich/.gitignore 具名两条 .log（seal/followup）+ **/*.lock 通配 · 假想新 .log 由仓库根 **/*.log 兜底·v4.4.14·R6② 措辞与实盘文件逐字对应），
#   ⛔ 不把台账数据混进 git（那是另一本账）。
FOLLOWUP_LEDGER = os.environ.get("TRIWICH_FOLLOWUP_LEDGER") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "followup_ledger.log")
MECHANISM_MAX_AGE_HOURS = 24  # 留痕新鲜度上限：筛查与销账须在同一工作时段内（防"半年前跑过一次"长期有效）

BIAS_ENUM = {f"B{i}" for i in range(0, 10)}  # B0 待归类 + B1-B9（决策卡schema定稿 §二·⛔不现场造枚举）
# JSONL 端探测源（v1.3.0·顺序即优先级）：(工具名, 根目录, glob pattern, 行格式kind)
# v1.3.3：⛔ 端清单真源=normalize_tool.py ALLOWLIST（端数实时为准·v4.4.11 R3-N6 去手抄）——本表=已适配实现；待适配端清单见 decision-room.md 自检节
JSONL_SOURCES = [
    ("WorkBuddy", "~/.workbuddy/projects", "*/*.jsonl", "wb"),
    ("WorkBuddy AI", "~/.workbuddy-ai/projects", "*/*.jsonl", "wbai"),  # 国际版·type:message 行结构（非同构 WB）
    ("ZCode", "~/.zcode/cli/rollout", "model-io-sess_*.jsonl", "zcode"),
]
JSONL_ENABLED = True  # 测试隔离开关：monkeypatch 置 False 强制走老 load_latest_history 路径

SIG_RE = re.compile(r'\[🧠\s*三明智\s*L[123][^\]]*[✅❌][^\]]*\]')
BLOCK_RE = re.compile(r'^## L[123][^\n]* 结果\s*$', re.M)


def load_latest_history():
    if not os.path.isdir(HIST_DIR):
        return None, None
    files = [f for f in os.listdir(HIST_DIR)
             if f.startswith("agent%3A") and f.endswith(".json")]  # v1.3.3：agent 名任意（实测 AutoClaw=agent%3Aauto-designer%3A*）·旧模式仅 main 恒空转
    if not files:
        return None, None
    latest = max(files, key=lambda f: os.path.getmtime(os.path.join(HIST_DIR, f)))
    try:
        with open(os.path.join(HIST_DIR, latest), encoding="utf-8") as fh:
            msgs = json.load(fh)
    except Exception:
        return None, None
    return latest, msgs


def extract_last_assistant(msgs):
    for m in reversed(msgs or []):
        if m.get("role") == "assistant":
            return m.get("content") or ""
    return ""


def load_jsonl_last(root, pattern, kind):
    """JSONL 端读取：root 下按 pattern 取 mtime 最新文件，解析最后一条 assistant 文本（v1.3.0）。
    kind=wb：行 {"role":"assistant","content":[{type,text}...]}
    kind=zcode：行 {"type":"model_io","response":{"text":...},"sessionId":...}（tool-calls 轮 text 为空·跳过只取真文本轮）
    无匹配文件/无 assistant 文本 → (None, None)"""
    import glob as _glob
    files = [f for f in _glob.glob(os.path.join(root, pattern)) if os.path.isfile(f)]
    if not files:
        return None, None
    latest = max(files, key=os.path.getmtime)
    sess, text = None, ""
    try:
        with open(latest, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    o = json.loads(ln)
                except Exception:
                    continue
                if kind == "wb" and o.get("role") == "assistant":
                    c = o.get("content")
                    t = "".join(i.get("text", "") for i in c if isinstance(i, dict)) if isinstance(c, list) else (c or "")
                    if t and SIG_RE.search(t):  # v1.3.1：按签名定位（最近一次三明智轮）——"最后一条文本"在多轮拆段流里必是后续开场白
                        text, sess = t, os.path.basename(latest)
                elif kind == "wbai" and o.get("type") == "message" and o.get("role") == "assistant":
                    # v1.3.3：WB-AI 行结构 type:"message"（非顶层 role）·content 同 WB·行内 sessionId
                    c = o.get("content")
                    t = "".join(i.get("text", "") for i in c if isinstance(i, dict)) if isinstance(c, list) else (c or "")
                    if t and SIG_RE.search(t):
                        text = t
                        sess = o.get("sessionId") or os.path.basename(latest)
                elif kind == "zcode" and o.get("type") == "model_io":
                    resp = o.get("response") or {}
                    t = resp.get("text") or ""
                    if isinstance(resp, dict) and t and SIG_RE.search(t):  # v1.3.1 同上
                        text = t
                        sess = o.get("sessionId") or os.path.basename(latest)
    except Exception:
        return None, None
    return (sess, text) if (sess and text) else (None, None)


def load_latest_text(tool=None):
    """统一取 (session_key, 最后一条 assistant 文本)——三 reader 分派（v1.3.0）：
    ① TRIWICH_HIST_DIR 显式指定或 JSONL 开关关闭 → 老路径（测试兼容）
    ② JSONL 端（WB/ZCode）——tool 指定时只探测该端源（多端并行防错位封口：mtime 最新≠当前端）
    ③ 兜底老端探测（AutoClaw/QoderCN/Trae 等 json 数组）
    无可用源 → (None, None)"""
    tool_n = tool.casefold() if tool else None
    if os.environ.get("TRIWICH_HIST_DIR") or not JSONL_ENABLED:
        sess, msgs = load_latest_history()
        return (sess, extract_last_assistant(msgs)) if sess else (None, None)
    for name, root, pat, kind in JSONL_SOURCES:
        if tool_n and name.casefold() != tool_n:
            continue
        sess, text = load_jsonl_last(os.path.expanduser(root), pat, kind)
        if sess:
            return sess, text
    if tool_n:
        return None, None  # v1.3.3：定向指定端未命中→不落无差别兜底（防他端会话误配给该端·实锤于 WB-AI 首测）
    sess, msgs = load_latest_history()
    return (sess, extract_last_assistant(msgs)) if sess else (None, None)


def compute_seal(session_id, text):
    """指纹 = 会话ID + 签名行 + 结论块全文（段头→签名之间的内容）+ 盐。
    无三明智完成签名 → None。⛔ 指纹必须覆盖结论块内容本身——只锁签名行/段头，
    改内容但保留签名即可绕过（2026-08-12 对抗测试 2 实测缺陷，v1.0.1 修复）。"""
    sig_m = SIG_RE.search(text)
    if not sig_m:
        return None
    block_m = BLOCK_RE.search(text)
    if block_m and block_m.start() < sig_m.start():
        block_content = text[block_m.start():sig_m.start()].strip()
    else:
        block_content = ""
    seed = session_id + "|" + sig_m.group(0) + "|" + block_content + "|" + SEAL_SALT
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def read_chain():
    if not os.path.exists(LOG_PATH):
        return []
    chain = []
    with open(LOG_PATH, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split("|")
            if len(parts) >= 5:
                chain.append(parts)
            else:
                # v4.4.10·R2-N3：畸形行静默跳过→显形（撕裂并发写/手工误改此前不可见；仍不计入链）
                print(f"⚠️ seal.log 跳过畸形行({len(parts)}字段): {ln[:40]}…（显形不封口·建议人工核对是否并发撕裂）", file=sys.stderr)
    return chain


def self_hash(ts, session, seal, prev):
    return hashlib.sha256(f"{ts}|{session}|{seal}|{prev}".encode("utf-8")).hexdigest()[:16]


def record(tool=None, text_file=None):
    """封口。v1.4.0（方案C 全端覆盖）：优先 --text-file（收尾传文本·不依赖读会话存储）；
    未提供则回退旧探测；两者皆无 → FAIL（Fail-Loud·不再静默跳过）。"""
    if text_file:
        try:
            with open(os.path.expanduser(text_file), encoding="utf-8") as fh:
                text = fh.read()
        except Exception as e:
            return 1, f"--text-file 读取失败（{text_file}）：{e}", False, None
        if not text.strip():
            return 1, f"--text-file 内容为空（{text_file}）——拒绝封口（Fail-Closed·空文本不可封）", False, None
        # session 键 = 端名:文本sha1前12（稳定·幂等去重；--text-file 路径下不依赖会话文件）
        sess = f"{(tool or 'unknown')}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"
    else:
        sess, text = load_latest_text(tool)
        if not sess:
            return 1, "无会话历史且未提供 --text-file——封口失败（v1.4.0 Fail-Loud：改用 --text-file 传本轮结论块，勿依赖读会话存储）", False, None
    seal = compute_seal(sess, text)
    if seal is None:
        return 0, "无三明智完成签名（合规放行，不记录）", False, None
    if not _acquire_path_lock(LOG_PATH + ".lock"):  # v4.4.10·R2根治：读链→算prev→append 临界区（24并发分叉实测复现——v4.4.9只锁了DR锁没锁链=修面不修链第五实例·本Loop自逮）
        return 1, (f"seal.log 锁获取超时——本次封口拒绝，请重试（Fail-Closed·防链分叉）"
                   f"；若锁残留且目录非空(持锁者崩溃于写入前)人工恢复：rm -rf '{LOG_PATH}.lock'（v4.4.12·R4-TW-05）"), False, None
    try:
        chain = read_chain()
        if chain and chain[-1][1] == sess and chain[-1][2] == seal:
            return 0, f"已封口（同会话同指纹·链尾即本轮）不重复入链", False, sess
        prev = chain[-1][4] if chain else "GENESIS"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{now}|{sess}|{seal}|{prev}|{self_hash(now, sess, seal, prev)}"
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(entry + "\n")
    finally:
        _release_path_lock(LOG_PATH + ".lock")
    return 0, f"已记录 seal={seal}（链长 {len(chain) + 1}）", True, sess


def verify(tool=None, text_file=None):
    """校验（v1.4.0·与 record 同口径）：--text-file 优先（收尾传文本·session 派生同 record），
    否则回退会话探测。两者口径一致才能对账成功。"""
    if text_file:
        try:
            with open(os.path.expanduser(text_file), encoding="utf-8") as fh:
                text = fh.read()
        except Exception as e:
            return 1, f"--text-file 读取失败（{text_file}）：{e}"
        if not text.strip():
            return 1, f"--text-file 内容为空（{text_file}）"
        sess = f"{(tool or 'unknown')}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]}"
    else:
        sess, text = load_latest_text(tool)
        if not sess:
            return 1, "无会话历史"
    seal = compute_seal(sess, text)
    if seal is None:
        return 0, "最新消息无三明智完成签名（无需校验）"
    chain = read_chain()
    if not chain:
        # v4.4.13·R5-N6：TW-07 分流漏做的第 4 支——新机器/新端首跑（seal.log 运行时态不入库，clone 后必空）
        # 旧版单方指控"可能被清空"=对无害常态的假指控同型复发。二因并陈，⛔不选边。
        return 1, "seal.log 为空但检测到三明智签名——二因并陈：本机从未封口（seal.log 运行时态不入库·换机/新端重起链=常态，跑 record 即起链）或既有链被清空（若本机曾封口=事故，查备份+mtime）；链自身不可分辨（v4.4.13·R5-N6）"

    # 链完整性逐跳校验
    for i, entry in enumerate(chain):
        ts, session, s, prev, h = entry[:5]
        exp_prev = chain[i - 1][4] if i > 0 else "GENESIS"
        exp_h = self_hash(ts, session, s, prev)
        if prev != exp_prev:
            return 1, f"链断裂 @{i}：prev 不连续（{prev} ≠ {exp_prev}）——日志被篡改/删除过"
        if h != exp_h:
            return 1, f"链断裂 @{i}：self_hash 不匹配（{h} ≠ {exp_h}）——该条被改写"

    # 最新会话指纹对账——根治对抗3（删链尾放行漏洞 v1.1.1）：
    # 不能用「链中存在当前会话记录」判走（会放行删尾），必须要求当前会话记录=链最后一条，
    # 任何删尾/删中间跳都会使「最后一条≠当前会话」或中断 prev/self_hash 而拦截。
    tail = chain[-1]
    if tail[1] != sess:
        # v4.4.12·R4-TW-07：三态分流——旧版把"本会话根本没封口"也报成"链尾可能被删除"，
        # 完好链上跑裸 verify 的只读审计者被指控删档（R4 实测 68 跳完好链中招即为证）。
        if not any(t[1] == sess for t in chain):
            # 二因并陈不选边：链上无本会话记录，"没封过口"与"封过但被删(链尾/中间跳)"同态——
            # 旧版武断报"可能被删除"=对未封口者假指控(R4-TW-07 本体)；反向只报"未封口"=稀释删档警报(对抗3考题抓住的过冲)。
            return 1, f"链完整（{len(chain)} 跳）但链中无当前会话记录——二因并陈：本会话未封口（无害·跨会话对账请 --tool 指名或先 record）或本会话记录已从链上被删除（若此前已封口=事故，链尾/他跳删档皆此态，查备份+mtime）；链自身不可分辨此二态，⛔不假称定论（v4.4.12·R4-TW-07 中性化）"
        _txt_key = re.match(r'^[^:]+:[0-9a-f]{12}$', str(tail[1]))
        _hint = ('；⚠️口径不同源（非删除）：链尾键形如「端名:文本sha1前12」＝该跳由 record --text-file 封口，'
                 '而本次 verify 未传同一文件＝用运行时会话 id 比对，两者永不相等；'
                 '要复现一致请 `verify --text-file <同一文件>`（D18·v4.4.13 只补文案·判定与退出码未变）'
                 ) if _txt_key else ''
        return 1, f"链完整（{len(chain)} 跳）但链尾会话 {tail[1]} ≠ 当前会话 {sess}——当前会话记录不在链尾（可能被删除/被他会话后来居上）{_hint}"
    if tail[2] != seal:
        return 1, f"当前会话指纹与日志不一致——输出被改过（记录值 {tail[2]} ≠ 重算值 {seal}）"
    return 0, f"链完整（{len(chain)} 跳）且链尾=当前会话指纹一致 ✅"


# ---------- 决策卡回访挂载（v1.2.0 · G2 回访机制 M2 工具层） ----------

# v1.4.2 实跑取证：`record --help` 被 parse_kv 当成未知 kv 吞掉 → 走无 --text-file 的回退分支
# → 对探测到的**他端老会话**真写了一条封口（幻影链尾）。未知 flag 必须显式拒绝，⛔不猜测。
KNOWN_FLAGS = {"tool", "text-file", "followup", "predict", "falsify", "deadline",
               "default", "window", "depth", "bias", "actual", "cause", "fix", "mechanism"}


def parse_kv(args):
    """解析 --key value 参数对（轻量·不引 argparse 保持脚本极简）。"""
    kv, i = {}, 0
    while i < len(args):
        tok = args[i]
        if tok.startswith("--"):
            kv[tok[2:]] = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif tok.startswith("-") and len(tok) > 1:
            # v4.4.13·R5-N5：单横线 token 旧版被 else 静默跳过——`record --tool X -h --text-file f`
            # 曾 rc=0 照常写链（-h 吞进跳过通道），与 :390"未知 flag 必须显式拒绝·⛔不猜测"不自洽。
            # v4.4.14·R6①补全：lstrip 后直接做键会被已知 flag 别名旁路（`-tool W` 剥出 tool 键→
            # 躲过黑名单、值被吞、tool 降级空值走 mtime 探测=削弱多端定向保证）。
            # 现统一加"·"前缀成永不合法键——单横线无论是否已知 flag 别名，一律确定性拒绝。
            kv["·" + tok.lstrip("-")] = ""
            i += 1
        else:
            i += 1
    return kv


def _dr_lock_path():
    return DECISION_ROOM_PATH + ".lock"


def _acquire_path_lock(lp, timeout_s=5.0):
    """路径级 mkdir 原子锁（v4.4.10·R2-seal分叉根治时泛化——DR/SEAL 两把锁同一实现，⛔不复制锁逻辑成第二本账）。
    os.mkdir 各平台原子；持锁者崩溃由 30s stale 夺取兜底；超时 False=调用方 Fail-Closed。"""
    import time as _t
    deadline = _t.time() + timeout_s
    while True:
        try:
            os.mkdir(lp)
            return True
        except FileExistsError:
            try:
                if _t.time() - os.path.getmtime(lp) > 30:
                    os.rmdir(lp)
                    continue
            except OSError:
                pass
            if _t.time() > deadline:
                return False
            _t.sleep(0.05)


def _release_path_lock(lp):
    try:
        os.rmdir(lp)
    except OSError:
        pass


def _acquire_dr_lock(timeout_s=5.0):
    """decision-room 锁（v4.4.9·R1-P1-01）。"""
    return _acquire_path_lock(_dr_lock_path(), timeout_s)


def _release_dr_lock():
    _release_path_lock(_dr_lock_path())


def next_seq():
    """扫描现有 FU-{seq} 最大值 +1（缺号不回填——台账序号只增不重排）。
    ⛔调用方必须先持 _acquire_dr_lock()（v4.4.9·R1-P1-01：扫描与追加须同一临界区）。"""
    mx = 0
    if os.path.exists(DECISION_ROOM_PATH):
        with open(DECISION_ROOM_PATH, encoding="utf-8") as fh:
            for ln in fh:
                m = re.match(r"^## FU-(\d+)", ln.strip())
                if m:
                    mx = max(mx, int(m.group(1)))
    return mx + 1


# 判假方式（可证伪性）硬拦起点 = 工单 §六 D10 到期日。起点前只 WARN，
# 起点后缺字段拒绝登记——多端收尾契约不当场打断，但欠账有明确到期。改此一行即可回落。
FALSIFY_HARD_SINCE = "2026-09-25"


def register_followup(kv, session=None):
    """向 decision-room.md 追加一条「待回访」登记（G2 应回访标记·封口时机械落账）。
    Fail-Closed：台账缺失→拒绝（不静默造头部，防脚本头与文档版漂移）；任务简述为空→拒绝。"""
    if not os.path.exists(DECISION_ROOM_PATH):
        return 1, f"decision-room.md 不存在（{DECISION_ROOM_PATH}）——先建台账再登记"
    task = kv.get("followup", "").strip()
    if not task:
        return 1, "--followup 任务简述为空——拒绝登记（缺字段=退回）"
    if session is None:
        sess, _ = load_latest_history()
        session = sess or "未知会话"
    deadline = kv.get("deadline", "").strip() or "（未填·⚠️到期不显形，只能靠人记得）"
    default = kv.get("default", "").strip() or "（无·⚠️黑洞候选：无默认分支=未裁定时系统不知道该干什么）"
    falsify = kv.get("falsify", "").strip()
    warn = ""
    if not falsify:
        if datetime.now().strftime("%Y-%m-%d") >= FALSIFY_HARD_SINCE:
            return 1, ("--falsify 判假方式缺失——拒绝登记（自 " + FALSIFY_HARD_SINCE +
                       " 起硬拦）。写清『出现什么观测结果即证明本预测错了』——"
                       "FU-4 判例：条件式预测把本方会做的修复当前件＝恒真预测，不可回访计分")
        falsify = "（缺·弱判据·" + FALSIFY_HARD_SINCE + " 起缺则拒绝登记）"
        warn = " ⚠️弱判据（未写判假方式）"
    # ── 幂等去重（2026-10-06 修复·FU-129 丢卡根因 L2）──
    # 病根：register_followup 本无去重 ⇒ N 次重跑 = N 条垃圾卡（实测 3 次→3 条）。
    # 键 = 会话 + 任务 + 预测 + 判假方式（四元组·语义身份）
    # ⛔ 只用"任务名"作键实测翻车（同任务名+不同预测的两张真卡被误吞成 1 条·误吞比造垃圾更隐蔽）
    # 降级：历史空占位卡（"- 预测：（未填）"/"- 判假方式：（缺"）走任务名键；
    #       ⛔ 降级条件须严格，"含任务名即命中"会让误吞回归（实测翻车二次）。
    try:
        with open(DECISION_ROOM_PATH, "r", encoding="utf-8") as fh:
            _dr_text = fh.read()
        _pv = kv.get("predict", "").strip()
        if task:
            for _blk in _dr_text.split("\n## FU-"):
                if f"- 任务：{task}" not in _blk or f"会话:{session}" not in _blk:
                    continue
                _blk_pv_empty = ("- 预测：（未填）" in _blk) or ("- 判假方式：（缺" in _blk)
                if _blk_pv_empty:
                    _hit = True          # 历史空占位卡：任务名+会话 足以判同一条
                else:
                    _hit = (f"- 预测：{_pv}" in _blk) and (f"- 判假方式：{falsify}" in _blk)
                if _hit:
                    return 0, "已登记过（幂等命中·四元组或降级键·不重复建卡）"
    except OSError:
        pass
    if not _acquire_dr_lock():  # v4.4.9·R1-P1-01：next_seq→append 原子临界区起点
        return 1, (f"decision-room 锁获取超时——本次登记拒绝，请重试（Fail-Closed，不产同秒双序号）"
                   f"；残留非空锁人工恢复：rm -rf '{DECISION_ROOM_PATH}.lock'（v4.4.12·R4-TW-05）")
    seq = next_seq()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    depth = kv.get("depth", "").strip() or "未标"
    entry = (
        f"\n## FU-{seq} · 状态:待回访\n"
        f"- 任务：{task}\n"
        f"- 深度：{depth}\n"
        f"- 预测：{kv.get('predict', '').strip() or '（未填）'}\n"
        f"- 到期日：{deadline}\n"
        f"- 到期默认：{default}\n"
        f"- 判假方式：{falsify}\n"
        f"- 回访窗口：{kv.get('window', '').strip() or '（未填）'}\n"
        f"- 登记：{now} · 发起方式:机制封口自动登记 · 会话:{session}\n"
        f"- 实际：（待回访）\n"
        f"- 偏差类型：（待回访）\n"
        f"- 归因：（待回访）\n"
        f"- 修正动作：（待回访）\n"
    )
    try:
        with open(DECISION_ROOM_PATH, "a", encoding="utf-8") as fh:
            fh.write(entry)
    finally:
        _release_dr_lock()  # 临界区终点：seq扫描+落盘成对（R1-P1-01）
    return 0, f"已登记 FU-{seq}（待回访）{warn}"


def _ledger_append(seqs, count):
    """followup 留痕：追加一行 {ts, count, seqs}。写失败不炸筛查，但把原因回传供显形。"""
    try:
        with open(FOLLOWUP_LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                                 "count": count, "seqs": list(seqs)}, ensure_ascii=False) + "\n")
        return ""
    except Exception as e:
        return "%s: %s" % (type(e).__name__, str(e)[:100])


def _ledger_rows():
    """读全部留痕行 → [(ts_str, seqs_list)]；坏行跳过、文件缺失/不可读 → []（由调用方朝拒不放行）。"""
    rows = []
    try:
        with open(FOLLOWUP_LEDGER, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    d = json.loads(ln)
                except Exception:
                    # v4.4.11·R3-N7：留痕坏行从静默跳过改显形（与 seal.log 畸形行显形同族口径·仍 Fail-Closed 不放行）
                    print(f"⚠️ followup 留痕跳过坏行: {ln[:40]}…（显形不封口·mechanism 判定不受影响）", file=sys.stderr)
                    continue
                if isinstance(d, dict) and d.get("ts"):
                    rows.append((str(d["ts"]), [str(x) for x in d.get("seqs", [])]))
    except Exception:
        return []
    return rows


def _mechanism_anchored(seq):
    """判「本 seq 是否由机制发起的回访」：新鲜度窗内**任一次** followup 留痕命中该 seq。
    返回 (bool, 说明)。缺留痕/全坏行/无一新鲜/查无此 seq → 一律 False（Fail-Closed·⛔不静默放行）。
    为何取"窗内任一行"而不是"仅最近一行"：多端多窗并发下，别人一次不同范围的筛查不得把自己的
    锚点挤掉（实锤：本端夹具漏隔离，写进实盘留痕后把真筛查那行盖掉→真卡被误拒）。
    ⛔ 但新鲜度仍是硬条件，不得退化成"历史上出现过一次就算"。"""
    rows = _ledger_rows()
    if not rows:
        return False, ("无可用 followup 留痕（%s 不存在/为空/全坏行）——标 mechanism 无外部锚。"
                       "先跑 `python3 scripts/triwich_seal.py followup` 再由机制发起回访；"
                       "若本次确由人工/记忆发起，请如实改填 --mechanism manual 或 AI想起" % FOLLOWUP_LEDGER)
    now = datetime.now()
    min_age, hit, fresh = None, False, 0
    for ts, seqs in rows:
        try:
            age = (now - datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")).total_seconds() / 3600.0
        except Exception:
            continue
        if age > MECHANISM_MAX_AGE_HOURS:
            continue
        fresh += 1
        if min_age is None or age < min_age:
            min_age = age
        if str(seq) in seqs:
            hit = True
    if hit:
        return True, "留痕锚定 OK（%.1f 小时前有筛查命中本 seq·窗内新鲜留痕 %d 行）" % (min_age, fresh)
    if min_age is None:
        return False, ("留痕 %d 行无一在 %dh 新鲜度窗内——该 seq 的 mechanism 声明缺当期外部锚，"
                       "重跑 followup 后再销账（或如实改标 manual/AI想起）"
                       % (len(rows), MECHANISM_MAX_AGE_HOURS))
    return False, ("FU-%s 不在窗口内任一次 followup 留痕的命中列表内（最近一次筛查于 %.1f 小时前·新鲜留痕 %d 行）——"
                   "未经前置筛查的销账不得标 mechanism（或如实改标 manual/AI想起）"
                   % (seq, min_age, fresh))


def followup_list():
    """待回访前置筛查：列出全部 状态:待回访 条目（Step0 键铸造后跑·命中即先回访再分析）。
    无待回访也 exit 0（筛查本身不阻塞，命中后的处置由步序约束）。"""
    if not os.path.exists(DECISION_ROOM_PATH):
        return 0, "decision-room.md 不存在——无待回访（台账未建）"
    items, cur = [], None
    with open(DECISION_ROOM_PATH, encoding="utf-8") as fh:
        for ln in fh:
            s = ln.strip()
            m = re.match(r"^## FU-(\d+) · 状态:(\S+)", s)
            if m:
                cur = {"seq": m.group(1), "pending": m.group(2) == "待回访",
                       "task": "", "predict": "", "window": "", "falsify": "",
                       "deadline": "", "default": ""}
                if cur["pending"]:
                    items.append(cur)
            elif cur and cur["pending"]:
                for pre, key in (("- 任务：", "task"), ("- 预测：", "predict"),
                                 ("- 回访窗口：", "window"), ("- 判假方式：", "falsify"),
                                 ("- 到期日：", "deadline"), ("- 到期默认：", "default")):
                    if s.startswith(pre):
                        cur[key] = s[len(pre):].strip()
    if not items:
        _ledger_append([], 0)  # 空结果同样留痕=「这次确实查过」的证据
        return 0, "无待回访条目（0 条）"
    parts = [f"{len(items)} 条待回访"]
    for it in items:
        weak = ""
        if not it["falsify"]:
            # 存量卡在 v1.4.1「--falsify 硬门禁」之前登记，卡上根本没有判假方式行 →
            # 只认"（缺…"占位符＝这类卡静默通过筛查，到点凭印象写「实际」（FU-4 恒真预测同型）。
            # 处置边界：⛔筛查只显形，不替立单端代写判据（判据属立单者的判断，代写=制造第二本账）。
            weak += " ⚠️无判假式(回访无法计分·请立单端自补·v1.4.1 起 record 已硬拒此类)"
        elif it["falsify"].startswith("（缺"):
            weak += " ⚠️弱判据"
        dl = it["deadline"].strip()
        md = re.match(r"^(\d{4}-\d{2}-\d{2})", dl)
        if md and md.group(1) < datetime.now().strftime("%Y-%m-%d"):
            weak += " 🔴超期未裁(到期%s)" % md.group(1)
        elif not it["default"] or it["default"].startswith("（无"):
            # 存量卡根本没有"- 到期默认："行（解析成空串）时同样必须显形——
            # 只认新格式占位符＝老卡永远静默绿，正是本机制要根治的那个洞（2026-09-18 自查抓到）
            weak += " ⚪无到期默认(黑洞候选)"
        parts.append(f"FU-{it['seq']}「{it['task']}」默认:{it['default'][:26]}{weak}")
    warn = _ledger_append([it["seq"] for it in items], len(items))
    if warn:
        parts.append("⚠️followup 留痕写入失败(%s)——本次销账将无法标注 mechanism（A 值口径依赖留痕）" % warn)
    return 0, " · ".join(parts)


def resolve(seq, kv):
    """回访销账：按 FU-{seq} 定位，状态翻转 待回访→已回访 + 回填四件套（实际/偏差/归因/修正）。
    按行改写（readlines→改行→writelines·指令编写规范 §1.5 禁切片拼接）；重复销账拒绝。"""
    # v4.4.12·R4-TW-01：序号双形态兼容——help/文档/台账展示均为 FU-N，实现内部曾是裸数字，
    # "文档教你按它走它拒你"+错误消息 FU-FU 双前缀=同一函数体三处口径打架。归一后三种写法皆可用。
    seq = str(seq).strip()
    if seq.upper().startswith("FU-"):
        seq = seq[3:]
    if not os.path.exists(DECISION_ROOM_PATH):
        return 1, "decision-room.md 不存在——无从销账"
    bias = kv.get("bias", "").strip()
    if bias not in BIAS_ENUM:
        return 1, f"偏差类型 {bias!r} 不在 B0-B9 枚举内——拒绝销账（Fail-Closed·防现场造枚举）"
    actual, cause, fix = kv.get("actual", "").strip(), kv.get("cause", "").strip(), kv.get("fix", "").strip()
    if not (actual and cause and fix):
        return 1, "缺 actual/cause/fix 任一项——拒绝销账（回访四件套须齐全·对齐决策卡schema）"
    mech = kv.get("mechanism", "manual").strip()
    if mech not in ("mechanism", "manual", "AI想起"):
        return 1, f"发起方式 {mech!r} 非法（mechanism/manual/AI想起）——拒绝（A 统计口径依赖此标记如实）"
    if mech == "mechanism":
        ok, why = _mechanism_anchored(seq)
        if not ok:
            return 1, "mechanism 声明被拒（G2 A 值物理锚）：" + why
    if not _acquire_dr_lock():  # v4.4.9·R1-P1-01：销账读改写与登记追加互斥
        return 1, (f"decision-room 锁获取超时——本次销账拒绝，请重试（Fail-Closed）"
                   f"；残留非空锁人工恢复：rm -rf '{DECISION_ROOM_PATH}.lock'（v4.4.12·R4-TW-05）")
    try:
        with open(DECISION_ROOM_PATH, encoding="utf-8") as fh:
            lines = fh.readlines()
        head = f"## FU-{seq} · "
        _hits = sum(1 for ln in lines if ln.startswith(head))
        if _hits > 1:
            # 锁前时代的历史碰撞善后（防线二）：同序号多卡=无法定向，⛔绝不前缀全量改写（一次销账双翻转）
            return 1, (f"存在 {_hits} 张 FU-{seq}（锁前时代碰撞遗留）——拒绝按序号全量翻转；"
                       "请人工把其中一张的卡号改为带后缀（如 FU-4b）消歧后重试（v4.4.9·R1-P1-01）")
        in_scope, hit = False, False
        today = datetime.now().strftime("%Y-%m-%d")
        out = []
        for ln in lines:
            if ln.startswith(head):
                if "状态:已回访" in ln:
                    return 1, f"FU-{seq} 已销过账——拒绝重复销账"
                hit, in_scope = True, True
                out.append(f"## FU-{seq} · 状态:已回访({today}) · 发起方式:{mech}\n")
                continue
            if in_scope and ln.startswith("## "):
                in_scope = False  # 进入下一节——停止回填
            if in_scope:
                if ln.startswith("- 实际："):
                    ln = f"- 实际：{actual}\n"
                elif ln.startswith("- 偏差类型："):
                    ln = f"- 偏差类型：{bias}\n"
                elif ln.startswith("- 归因："):
                    ln = f"- 归因：{cause}\n"
                elif ln.startswith("- 修正动作："):
                    ln = f"- 修正动作：{fix}\n"
            out.append(ln)
        if not hit:
            return 1, f"FU-{seq} 不存在——检查序号"
        with open(DECISION_ROOM_PATH, "w", encoding="utf-8") as fh:
            fh.writelines(out)
    finally:
        _release_dr_lock()
    return 0, f"FU-{seq} 已销账（发起方式:{mech}·偏差:{bias}）"


def main():
    args = sys.argv[1:]
    mode = args[0] if args else "verify"
    # v4.4.12·R4-TW-03/06：help 契约收窄为「仅首参」——旧版 ("--help" in args) 全行扫描 + `or True` 恒真式
    # 制造两类假成功：①`bogus --help` 中性化白名单闸 ②值位混入 -h/--help → rc=0 但动作没做。
    # 非首参的 --help/-h 现按未知参数确定性拒绝（bad-flag 消息附"用法=首参--help"指引）。
    # （旧注释里"未知 flag 拒绝不等于把 --help 也拒了"的诉求由首参通道满足，不再以旁路实现。）
    if mode in ("--help", "-h"):
        print(__doc__.strip().split("\n\n")[0])
        print("用法：triwich_seal.py record|verify --tool 端名 --text-file 结论文本文件 "
              "[--followup 任务 --predict 预测 --falsify 判假方式 --deadline YYYY-MM-DD --default no-op：… "
              "--window 窗口 --depth L1|L2|L3]")
        print("       triwich_seal.py followup | list | resolve 序号(裸数字或 FU-N 均可·如 3 / FU-3) --bias B? --actual … --cause … --fix … [--mechanism …]")
        return 0
    if mode not in ("record", "verify", "followup", "list", "resolve"):
        # v4.4.11·缝合修复：TW-3 help 闸上移时白名单闸被融丢（=R3-N2 修面不修链当场复发·被抓现行）——两闸并存：help 先给用法，未知子命令仍拒
        print(f"SEAL:FAIL 未知子命令 {mode!r}（可选 record/verify/followup/list/resolve·--help 看用法）")
        return 2
    kv = parse_kv(args[2:] if mode == "resolve" else args[1:])
    bad = sorted(set(kv) - KNOWN_FLAGS)
    if bad:
        print(f"SEAL:FAIL 未知参数 {bad}——拒绝执行（不猜拼错的 flag·⛔不静默写入·用法=首参 --help）")
        return 1
    if mode in ("record", "verify") and "text-file" in kv and not kv["text-file"].strip():
        # v4.4.13·R5-N1（P2·缺值族）：已知 flag 缺值/空值旧版 ≡ 未提供 → record/verify 静默换源
        # 封/对账了他会话（R5 实锤 `record --tool T --text-file`漏值→rc0 封进 agent%3Amain%3Aoldsession
        # =v1.4.2 幻影链尾同伤害级）。空值≠未提供：未提供才允许回退会话探测，空值=传参事故，确定性拒绝。
        print("SEAL:FAIL --text-file 给了值位但值为空——拒绝执行（空值≠未提供·⛔不静默换源；未提供时才回退会话探测·v4.4.13·R5-N1）")
        return 1
    if mode == "record":
        if "tool" in kv and not kv["tool"].strip():
            print("⚠️ --tool 空值=未定向（多端并发下将走 mtime 探测·跨会话错位封口面）——本次继续但请补端名（v4.4.13·R5-N1 显形）", file=sys.stderr)
        code, msg, sealed, sess = record(kv.get("tool"), kv.get("text-file"))
        out = f"SEAL:{'OK' if code == 0 else 'FAIL'} {msg}"
        if "followup" in kv and not str(kv["followup"]).strip():
            # v4.4.13·R5-N1：--followup 空值旧版被 if kv.get() 真值门整体吞掉=回访登记静默蒸发
            # （SKILL 宣称"任务简述为空=FAIL 退回补填"位于 register_followup 内，旧结构永远到不了那行）
            out += "\nFOLLOWUP:FAIL --followup 给了参数但值为空——退回补填（空值≠未提供·登记是收尾义务，⛔静默丢失=A值分母失真）"
            code = code or 1
        elif kv.get("followup"):
            if sealed or code == 0:
                # 2026-10-06 修复（FU-129 丢卡根因 L1）：原判据 sealed=False 有三来源
                # （无签名/幂等命中/锁失败），把"FU 不登记"一律挂在它上面 ⇒ 幂等重跑必丢卡。
                # 语义应取"链已闭合"= code==0；register_followup 已幂等（见上），重复调用不再建卡。
                fcode, fmsg = register_followup(kv, session=sess)  # v1.3.2：session 用 record 真值（修台账会话字段误取老端 fallback）
                out += f"\nFOLLOWUP:{'OK' if fcode == 0 else 'FAIL'} {fmsg}"
                code = code or fcode  # 登记是收尾义务·任一失败→非零（Fail-Closed）
            else:
                # v4.4.11·R3-N8：sealed=False 有三来源（无签名/链尾即本轮幂等命中/锁超时失败），旧文案一律说"无封口签名"=失真
                out += f"\nFOLLOWUP:SKIP 本轮未入链·不登记（原因见上一行：{msg[:40]}）"
    elif mode in ("followup", "list"):
        # v4.4.11·R3-N2：list 曾列 allow-list 却无 dispatch=静默落 verify（P3-08"消息错位"同型残留）——名实对齐
        code, msg = followup_list()
        out = f"FOLLOWUP-LIST:{'OK' if code == 0 else 'FAIL'} {msg}"
    elif mode == "resolve":
        code, msg = resolve(args[1] if len(args) > 1 else "", kv)
        out = f"RESOLVE:{'OK' if code == 0 else 'FAIL'} {msg}"
    else:
        code, msg = verify(kv.get("tool"), kv.get("text-file"))
        out = f"SEAL:{'OK' if code == 0 else 'FAIL'} {msg}"
    print(out)
    return code


if __name__ == "__main__":
    sys.exit(main())
