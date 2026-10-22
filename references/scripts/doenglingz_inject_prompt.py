#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# TRUTH_OF: 脚本中心/doenglingz_inject_prompt.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
"""
doenglingz_inject_prompt.py — UserPromptSubmit 钩子：童灵完整化（W1 上岗自证 + W3 域切片注入式路由）。

设计定位（数字分身设计哲学 05-K2 §6.2 完整双层 · 06 跨端适配 v1.12）：
- WB 端兑现「完整童灵」的机制层：core+L6 已常驻 USER.md（k2_slice_generator 产物）；
  本钩子补齐 L2~L5 域切片按需注入（W3）+ 上岗自证行（W1），使 WB 从「半层恒驻」升为「完整可达」。
- W1（上岗自证）：命中童灵调用词（启动童灵/用童灵/童灵评估/童灵帮我/让童灵/唤醒童灵…）
  → 输出含 SSOT hash 的上岗行，使「启动童灵」从零响应变为可观测动作（对齐 AutoClaw W1）。
- W3（域切片路由）：命中窄集触发词 → 读取对应 slices/<Ln>.md 注入上下文。
  注入式（读 live slices/ 而非缓存）→ 新鲜度天然满足，免 W2 心跳轮询（超越 AutoClaw 文档级降级）。
- 触发词窄集对齐 AutoClaw W3 已实证口径（防噪声）；slices/manifest.json 的 strategy 为「生成期宽集」，
  运行时刻意不采用——避免 方案/验证 等高频词触发 8899 字节 L3 噪声污染。
- SSOT hash：童灵·人格规格书.md sha256 前12位，**动态计算**（每次调用读规格书算 hash）→ 规格书变更自动反映，不靠硬编码记忆（愿景①全自动化·超越 AutoClaw W1 硬编码）。
- 失败默认放行（exit 0），绝不阻断对话（守卫编写规范原则1/2）。
- `--selfcheck` 模式打印挂载注册状态 + 切片映射 + SSOT。

端感知输出（根治依据 route_inject_prompt.py 同构）：
- ZCode：必须输出 {"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":ctx}} 否则被静默丢弃。
- Qoder CN（2026-09-04 实测更正）：**裸文本 stdout 被产品判 `winner=none (no parsed
  output)` 整轮丢弃**（questWindow/hooks.log 143/143 实证）→ 本端必须走 JSON envelope。
  协议判定收敛到 `hook_protocol.py` 单一真源（本脚本不再自选形态）。
- 其他端（WorkBuddy 等）：维持 sys.stdout.write(ctx) 原形态（实测吃 text·零回归）。
- `--prompt <text>` argv 模式（2026-09-05·AutoClaw 端接入）：AutoClaw 的 buluotuo-route-inject
  插件经 execFile 转发，hook stdin 在插件链路不可靠（route_inject_prompt.py 2026-08-13 同构实证）
  → 对齐 route 家族惯例走 argv 传参；`--src <端名>` 同时标注台账端归属（state 跨端共文件）。
  `--src auto`（2026-09-30 新增）= 由运行期环境变量自识别端，供**共用同一 hooks.json 的 Trae 系双端**
  （Trae Work / TraeCode）使用——写死单端名会让另一端的台账端归属与 W1 署名双双串端。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# ⚠️ 本件路径取持字面（⛔改 runtime_paths 出口）——2026-10-18 自纠：本件是 W1 每轮必注入
#   关键路径，rp() 缺声明即 raise DeclNotFound（其 fail-loud 设计对普通脚本正确），
#   但对注入器而言 raise＝钩子崩＝上岗声明整体消失（装机态沙箱实测 rc=1/输出 0B）。
#   故本件豁免去硬码，理由与账见迁移卡 §四 发现14／§六 V1。
import sys
import os
import json
import datetime
import hashlib

# 输出协议单一真源（2026-09-04 根治：本端裸文本被产品判"no parsed output"整轮丢弃）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # 自推导：作者侧=开发工具/·装机态=hooks/（同目录件互见·两环境通用·2026-09-20 根治 devtools 手工同步）
try:
    import hook_protocol as _hp
except Exception:
    _hp = None

_PAYLOAD = {}   # 本回合 stdin 载荷（供协议判定/留痕/端归属）
_SRC_LABEL = ""  # --src argv 端标注（AutoClaw 等插件转发端·台账 src 字段用）
# 版本机械载体：06 §1.6 与 CHANGELOG 长期以"v1.7"等手写号引用本件，但盘上无版本字段可对账
# （=守卫编写规范 §3.5「版本悬空引用」同型）。自 v1.8 起版本以本常量为真源，文档引用须与之一致。
__version__ = "v1.26"  # v1.26(2026-10-19·V2.2.4增量Loop对抗审查根治)：安静模式进入检测四修——①反向话术豁免(关闭/退出类不得翻转成开启·审查4.1)②疑问形态豁免(≤30字问句不当命令·审查4.2)③C类机器块过滤拉平(审查4.4)④全出现位判定(审查4.5)。新增安静用例组入w1_tier_regress。
# v1.25(2026-10-19·安静模式实装·你定稿「D3只认启动童灵+事件腿不关」)：①新增quiet_mode.flag持久状态②w1_fired加安静模式门③_inject加进入检测。负例待跑：含安静模式消息不进D3/启动童灵穿透退出/成长箱事件腿不受影响。  # v1.23(2026-10-08·Hermes·皮叔质证「我没明确说启动童灵，你还是启动了」假触发根治轮)：四处判据精化——①W1_TRIGGERS 补「童灵上岗」(p7漏召实证) ②否定语境扩跨词(原只认紧贴trigger的否定⇒「不打算用童灵」漏网·加窗口内含否定字+句读隔断防跨句误豁免) ③宽松匹配⑤剔除单字动词「用/去」+只认「童灵」之后窗口(方向性：动词在前=童灵是宾语「帮我看下童灵的设计」) ④句尾直呼收紧(要求「童灵」前一字为句读/句首·宾语位「我想了解一下童灵」不再当呼唤)。预注册 6 新用例(n6-n10+p7)·回归器 11→16 全绿·原 dryrun 19/19 未破·扩展压测 38/38。
# v1.18(2026-10-07·Qoder CN·你令按三明治推荐开工)：P4「全域」fallback 改名人话化=「未命中域（仅基底）」；P3①补载义务入契约①（宣告域≠词面域须真Read切片+显形「已补载：LN」·对账=level_declare_guard v1.8）
#   v1.17（2026-10-06·你反馈「指令行太难看·没仪式感」）：确认块拆两层——AI 指令行（⛔不进回复）
#   与仪式块（用户可见·自档位标签行起零改写照抄）；meta 括注（真源/守卫留痕）全部移入指令行。
#   v1.16（2026-10-06·皮叔拍板「启动确认块·脚本拼装·AI 照抄」+三档正名）：根治档位漏贴 33 次
#   （内部记录·守卫只留痕不回灌·AI 侧显示义务全天 0 兑现）——①D1/D2/D3 三档确认块由
#   本脚本拼装（构造权移交·同 TSL 树哲学），义务=首段原样照抄；②正名：D2 域模式→**切片模式**
#   （命中域切片→命中切片·对齐视频心智「规格书蒸馏后切片」）、D3 上岗模式→**全量模式**（上岗
#   退居身份句·三档连成装备递进线：非全量→切片→全量）；③「N/N 条在位」动态计数（义务特征短语
#   在位判定·⛔裸编号防假阳性）；④切片判定/已加载切片两行分立=标签≡实盘显形化（判定≠加载即露馅）。
#   v1.15（2026-10-06·WB 童灵·L5 MISS 根治 + relay保真律入契约）：⑨扩 relay保真条款（缓存树原样
#   零编辑·指针行与手绘同级违规·内部记录/011/012 三犯实证）；新增⑩守护三查法定痕
#   （🧪 8要素行义务入注入层·根治「义务住文档层+判据层、唯独不在契约层」的穿网结构）。


def detect_end():
    """端运行期自识别（2026-09-30·判据与 host_identity_hook.sh 逐字同源）。

    为什么需要：Trae 系双端（Trae Work / TraeCode）dataFolderName 均为 `.trae-cn`，
    **物理共用同一个 hooks.json**（实证：TraeCode agent-hooks.log 有派发记录、Trae Work 全 0 字节），
    故 hooks.json 里写死 `--src traework` = 在 TraeCode 回合把端归属记成 Trae Work，
    并让 W1 注入行把 TraeCode 的署名说成「你的 Trae Work 🤖」——即 2026-09-09 你定红线的
    「签名串端」同型事故。判据改由运行期环境变量机械判定，共脚本不再携带端专属值。

    判据：ICUBE_APP_ROOT / ICUBE_PRODUCT_BRAND_NAME（实证见 host_identity_hook.sh 头注）。
    判不出 → 返回 ""（⛔不猜、⛔不默认任何端；下游按 unknown 落账，宁缺勿假）。
    """
    blob = "%s%s" % (os.environ.get("ICUBE_APP_ROOT", ""),
                     os.environ.get("ICUBE_PRODUCT_BRAND_NAME", ""))
    if "TRAE SOLO" in blob:
        return "traework"
    if "Trae CN" in blob:
        return "traecode"
    return ""


# 档位枚举＝本常量单一真源（2026-09-26 三修·治 8要素⑥"新档要同步 4 处手写点"）：
# 三态表(06 §1.6)/守卫正则/回归用例的档位集合由 d_tier_exclusivity_dryrun.py 机械对账，
# 任一处漂移即红——档位定义不再靠人记。
TIER_ORDER = ("D3", "D2", "D1")

# v1.13 多端配置根（2026-09-30 L3审计根治·B1旁路缝正式化）：
# DOENGLINGZ_CONFIG_DIR（install_scripts --platform 写进钩子命令）> WORKBUDDY_CONFIG_DIR（向后兼容缝·lobsterai 已在用）> ~/.workbuddy（旧默认行为）
_DLZ_CFG = os.environ.get("DOENGLINGZ_CONFIG_DIR") or os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy")
STATE_FILE = os.path.join(_DLZ_CFG, "doenglingz_inject_state.json")
# ── 安静模式（2026-10-19 你定稿·D3 只认"启动童灵"）──────────────────────────
QUIET_MODE_FILE = os.path.join(_DLZ_CFG, "quiet_mode.flag")

def _is_quiet_mode():
    """flag 文件存在 = 安静模式激活。读不到=不激活（fail-open·Hook三纪律）。"""
    return os.path.exists(QUIET_MODE_FILE)

def _set_quiet_mode():
    try:
        os.makedirs(os.path.dirname(QUIET_MODE_FILE), exist_ok=True)
        open(QUIET_MODE_FILE, "w").close()
    except Exception:
        pass

def _clear_quiet_mode():
    try:
        os.remove(QUIET_MODE_FILE)
    except FileNotFoundError:
        pass
    except Exception:
        pass


# 事件腿粘滞窗口（分钟）：同 session 内 Skill 启动升的 D3 在此窗口内不回落 D1/D2。
# 取 180min＝覆盖一次连续施工（实证本轮 20:55→21:10 隔 15min），又不至于跨天误粘。
EVENT_D3_STICKY_MIN = 180


def _event_leg_d3_sticky(sid, now=None):
    """同 session 内若存在事件腿（mode=skill_event）写的 D3 且未超窗口 → 档位粘滞为 D3。

    设计约束：⛔不新建第二状态源，只回读事件腿已在写的那份 inject_state；
    ⛔sid 为空一律 False（防跨会话串档·同 06「他会话产物不顶账」同型防御）；
    读不到文件 fail-open 回落词面腿（Hook 三纪律：⛔不阻断注入）。
    安静模式（2026-10-19）：flag 存在时粘滞全局压制——与词面腿同步关，
    退出安静模式（"启动童灵"清 flag）后粘滞自动恢复。
    """
    if not sid:
        return False
    if _is_quiet_mode():
        return False  # 安静模式期间事件腿粘滞压制（你定稿：安静=D3全关，含粘滞残留）
    import json as _j
    import datetime as _dt
    now = now or _dt.datetime.now()
    try:
        raw = open(STATE_FILE, encoding="utf-8").read().splitlines()
    except Exception:
        return False
    for line in reversed(raw):
        line = line.strip()
        if not line:
            continue
        try:
            d = _j.loads(line)
        except Exception:
            continue
        if d.get("mode") != "skill_event" or d.get("d_tier") != "D3":
            continue
        if str(d.get("session_id", "")) != str(sid):
            continue
        try:
            ts = _dt.datetime.fromisoformat(str(d.get("ts")))
        except Exception:
            return False
        return (now - ts).total_seconds() <= EVENT_D3_STICKY_MIN * 60
    return False

SLICES_DIR = os.environ.get("DONGLINGZ_SLICES_DIR") or \
    os.path.expanduser("[记忆共享中心]/数字分身/K2切片蒸馏/slices")   # 环境变量=测试隔离缝（2026-09-26·守卫规范 §3.9 夹具须可指向空目录）
SSOT_SPEC = os.path.expanduser("[记忆共享中心]/数字分身/童灵·人格规格书.md")
SSOT_HASH_FALLBACK = "70c917662765"  # 规格书不可读时的兜底（与 AutoClaw W1 同源旧值）

def read_identity_sentence():
    """从 SSOT_SPEC 读「上岗身份声明全文」真源——治 injector 硬编码身份句与规格书/06 三源漂移（2026-10-06·你令彻底根治·PAT类多源病）。
    缺真源行则 Fail-Loud：返回可见⚠️告警串（⛔不静默回退旧硬编码=不再制造静默漂移）。"""
    try:
        with open(SSOT_SPEC, encoding="utf-8") as f:
            for ln in f:
                if "上岗身份声明全文" in ln and "：" in ln:
                    return ln.split("：", 1)[1].strip()
    except Exception:
        pass
    return "⚠️[身份真源缺失·规格书§1.1无「上岗身份声明全文」行·请补真源]童灵上岗——我是你的数字分身"

def compute_ssot_hash():
    """动态计算童灵·人格规格书.md sha256[:12]——规格书变更自动反映，不靠硬编码。"""
    try:
        with open(SSOT_SPEC, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except Exception:
        return SSOT_HASH_FALLBACK

# W1：童灵显式调用词（上岗自证触发）
W1_TRIGGERS = [
    "启动童灵", "童灵上岗", "用童灵", "童灵评估", "童灵帮我", "让童灵",
    "童灵启动", "唤醒童灵", "童灵上线", "童灵上工", "童灵分析", "童灵判断",
    "童灵给意见", "童灵去", "童灵执行", "童灵给我",
    # 你常用动词型口令（2026-08-29 补·覆盖"童灵处理/做/安排/搞定/推进/负责/接手"等自然表达，治"有时没真启动"）
    "童灵处理", "童灵做", "童灵安排", "童灵搞定", "童灵推进",
    "童灵负责", "童灵接手", "童灵统筹", "童灵办", "童灵搞",
    # 2026-09-13 补（WP2·A 类漏召实证样本的直接修复）：
    #   "童灵怎么看？" / "童灵有何收获？" / "童灵继续推进" / "童灵你继续做"
    "童灵怎么看", "童灵有何", "童灵有什么", "童灵继续", "童灵接着", "童灵你继续",
    # 2026-10-04 补：需童灵在岗的 Skill，其触发词本身即上岗调用（你定口径「启动成长箱即上岗，上岗即有 TSL」）。
    #   词面真源=各 Skill frontmatter description 触发词（此处只收 growth-box 显式调用词·带动词义不误召）；
    #   机制化（Skill 自声明 requires_twin_on_duty → 注入层读取·全端同源）挂 数字分身专项修改工单 P1/P2。
    "启动成长箱", "成长箱晋升", "检查晋升", "记到成长箱", "计入成长箱", "记入错误",
    "错误蒸馏", "成长箱蒸馏", "月度蒸馏", "执行反哺工作", "反哺追加", "正反哺",
    # 2026-10-12 K007 接线（补 v1.3.2 纪律的机械面）：卡写明「你点名 K007 即自动等于启动 D3」，
    #   而本表 50 项无一含 K007 ⇒ 说「启动K007」机械上不可能升档（本会话 20:30:26 实盘判 D1 为证）。
    #   与 09-13 W1_SELF_WORDS 注释同族病：「规格书声明 ⊃ 实现」。取词保守：全写 K007 + 漏K形态 007卡；
    #   ⛔不收裸 "007"（会误召 2007 年/编号类文本，代价=无事升 D3 全量契约）。
    "K007", "007卡", "三源闭环",
]

# W1 宽松匹配：用户消息含"童灵"且带任一动作动词即视为显式调用（覆盖"童灵来给意见/童灵都去执行"等带衬字变体）
W1_VERBS = ["给意见", "去执行", "执行", "去", "判断", "评估", "分析", "帮我", "给我", "来给", "启动", "上线", "上工", "唤醒", "用"]

# W1 调用词（2026-08-29 补·根治零响应缺口）：直呼式之外的"身份/自述"类调用说法。
#   事故实证：'童灵，请介绍你自己' 既不命中 W1_TRIGGERS 也不命中 W1_VERBS → 钩子零输出，
#   被 route_miss_feeder 记为 miss 却无人消费 → 你侧观感＝"接入是假的"。
W1_SELF_WORDS = ["介绍", "你是谁", "自我介绍", "在吗", "在不在", "说说你", "汇报", "报告", "还记得",
                 # 2026-09-13 补（WP2）：规格书 L48 声明「童灵有什么思考/发现/想法/收获/复盘」为触发词，
                 #   而本表此前一条都没实现 ⇒ A 类漏召根因之一＝**规格书声明 ⊃ 脚本实现**（双本账）。
                 "收获", "发现", "思考", "想法", "复盘", "有何", "怎么看"]
# 宽松匹配（⑤）的两个精化常量（2026-10-08 v1.23·皮叔质证假触发根治）：
#   ⛔ 单字动词剔除集——中文高频且常处否定/无关语境（不用/借用/去哪里），
#     作为"召唤证据"精度远低于代价；指向童灵的「用童灵」已由 W1_TRIGGERS 覆盖。
_W1_VERBS_SINGLE = ("用", "去")
#   「紧邻」窗口：动词须落在「童灵」前后各 N 字内才算"指向童灵"（机械近似指向性）。
_W1_VERB_NEAR = 4

# W1 元讨论闸（B 类·2026-09-13 WP2 新增）：**提及≠调用**，命中即静默。
#   依据：对账报告_2026-08-22.md §8.6「26 条残余 miss」B 类实证（≈15 条元讨论·应继续静默）。
#   全部为**复合窄词**（须与"童灵"共现才成立）——铁律-020 禁裸高频词。
#   2026-09-13 续补（D 轴三态设计定稿）：用户讨论 D1/D2/D3 机制本身（非召唤执行）时会带 D 轴设计词，
#   若误判为上岗将强制 TSL 输出、打扰设计对话。以下词与"童灵"共现即视为元讨论静默。
W1_META_GUARDS = [
    "每次问", "都会出现", "封装成", "是不是最好", "不都可以", "聊了几句", "童灵的特性",
    # D 轴三态设计词（与"童灵"共现=在讨论机制·非召唤）：
    "D1 常驻", "D1常驻", "D2 域", "D2域", "D3 上岗", "D3上岗",
    "常驻模式", "域模式", "上岗模式", "D轴", "三态", "三档",
]

# 直呼式判定的分隔符（"童灵"后必须紧跟标点/空白或到此结尾，避免"童灵灵"式误召）
_ADDRESS_SEP = "，,、。.!！?？:：;；~～ \t\n"


def _address_call(prompt):
    """消息以"童灵"起头并跟分隔符＝直呼分身，视为显式调用（不依赖动词表，防窄集漏召）。"""
    t = prompt.lstrip()
    if not t.startswith("童灵"):
        return False
    tail = t[len("童灵"):]
    return (not tail) or tail[0] in _ADDRESS_SEP


def w1_fired(prompt):
    """W1 上岗判定（2026-09-13 WP2 升级：+C 类机器块过滤 +B 类元讨论闸 +句中直呼；
    2026-10-01 v1.14：+否定语境豁免）。

    判序（**先闸后召·闸优先**）：
      ① C 类机器块（`<...>` 回显）→ 不判
      ② 否定语境豁免（提及≠调用·B 类同源扩展）→ 全部强召唤词的**所有**出现位置
        均带否定前缀 → 压制强召唤返回与宽松匹配（直呼判定不压制——"我没启动童灵。童灵，你来"仍上岗）
      ③ B 类元讨论闸（提及≠调用）→ 静默
      ④ 显式调用词 / 句首直呼 / 句中直呼 → 上岗
      ⑤ 宽松匹配（"童灵"+动词/自述词）→ 上岗
    dry-run：19/19 过（正例 5/5 · 负例 5/5 · A 类真样本 6/6 · B 类真样本 3/3）
      + v1.14 否定判组 10/10（含 9-23 你质证判例回归）。
      工具 `数字分身/scripts/w1_vocab_dryrun.py`；预注册判据（立场卡 S875）先于改动写下。
    """
    t = (prompt or "").strip()
    if not t:
        return False
    # ① C 类·机器块过滤（<internal-error> 类回显，不该进台账）
    if t.startswith("<") and ">" in t[:24]:
        return False
    # ② 安静模式门（2026-10-19 你定稿·持久态开关）
    #    激活时 D3 只认"启动童灵"肯定式，其余一律压制。
    #    穿透时自动退出安静模式（启动童灵=解除安静+正式上岗）。
    if _is_quiet_mode():
        _qm_word = "启动童灵"
        _qm_spans = []
        _qm_start = 0
        while True:
            _qi = t.find(_qm_word, _qm_start)
            if _qi < 0:
                break
            _qm_spans.append((_qi, _qi + len(_qm_word), _w1_mentioned_at(t, _qi, _qm_word)))
            _qm_start = _qi + len(_qm_word)
        if _qm_spans and not all(m for _, _, m in _qm_spans):
            _clear_quiet_mode()  # 肯定式"启动童灵" → 退出安静 + 放行 D3
            return True
        return False  # 安静模式下其余全部关闭（事件腿不受本函数管辖）
    # ② 否定语境豁免（2026-10-01·皮叔质证「这一轮我没启动童灵，为什么还出现 D3/TSL」根治）：
    #    子串匹配不读否定语境——"我没有启动童灵"字面含"启动童灵"→误召 D3→连带 TSL 噪声。
    #    判据：所有强召唤词的全部出现都带否定前缀＝召唤证据只是"被谈论的召唤"→ 压制。
    #    保留 9-23 判例：任一**肯定式**强召唤出现 → 无条件上岗。
    _negated_only = _all_strong_calls_negated(t)
    # ③ B 类·元讨论闸：提及≠调用（先于正例判定）
    #    2026-09-23 根治（你质证「我的指令是启动童灵，不应该是D3了吗？还显示D1干嘛？」）：
    #    **强召唤词优先于元讨论词**。病根实证：你**复制上条回复的「【童灵·D1 常驻模式…】」标签**
    #    来提问 → 消息含「常驻模式」命中本闸 → 把「召唤 + 档位反馈」误判成「纯讨论机制」→ 降 D1。
    #    判据修正：命中 W1_TRIGGERS（显式召唤词）时不受本闸压制——你说「启动童灵」就是召唤，
    #    附带讨论档位不改变召唤性质；本闸只该拦**无召唤词的纯讨论**（仍拦得住"童灵的特性是不是…"）。
    _strong_call = any(x in t for x in W1_TRIGGERS)
    if not _strong_call and "童灵" in t and any(g in t for g in W1_META_GUARDS):
        return False
    if any(x in t for x in W1_TRIGGERS) and not _negated_only:
        return True
    if _address_call(t):
        return True
    # ③ 句中直呼："童灵"后紧跟分隔符（位置不限·治"那童灵，你有什么收获吗？"）
    # v1.22（10-07 假触发根治）：落在"被谈论的召唤"区间内的 童灵（如「没有说启动童灵，」
    #   的逗号属分隔符）不算直呼——直呼须是未被豁免的独立呼唤。
    _mm_spans = [s for s in _strong_call_spans(t) if s[2]]
    i = -1
    _j = -1
    while True:
        _j = t.find("童灵", _j + 1)
        if _j < 0:
            break
        if not any(a <= _j < b for a, b, _ in _mm_spans):
            i = _j
            break
    if i >= 0:
        tail = t[i + 2:]
        if (not tail) or tail[0] in _ADDRESS_SEP:
            # 尾随空尾特判（v1.14）：该"童灵"若是某强召唤词的宾语尾（如"不启动童灵"句尾），
            # 属被谈论的召唤短语而非呼唤——不按直呼上岗，交给召唤判定（含否定豁免）裁决。
            _is_trigger_tail = any(
                i + 2 - len(x) >= 0 and t[i + 2 - len(x):i + 2] == x
                for x in W1_TRIGGERS
            )
            if not (not tail and _is_trigger_tail):
                # 句尾直呼收紧（2026-10-08 v1.23·n7 实证「我想了解一下童灵」）：
                #   原判据「句尾+非trigger尾 ⇒ 直呼」把**宾语位**也当呼唤——
                #   「…了解一**下童灵**」「…看**下童灵**的设计」里「童灵」是宾语，前一字是补语（下/的）。
                #   呼唤的机械特征＝「童灵」是**独立成分**：前一字为句读或句首（那童灵，…／童灵，…）。
                #   ⚠️ 不改 p4「那童灵，你…」（tail[0]=逗号已走上面分支·不经过此）与 p1-p3（走 trigger）。
                _pre_ch = t[i - 1] if i >= 1 else ""
                if not tail and _pre_ch and _pre_ch not in _ADDRESS_SEP:
                    pass          # 宾语位·非独立呼唤 ⇒ 不直呼
                else:
                    return True
    # ⑤ 宽松匹配（2026-10-08 v1.23 精化·皮叔质证假触发根治）：
    #   原判据 `"童灵" in t and any(v in t for v in W1_VERBS + W1_SELF_WORDS)`
    #   —— 只看**句内是否同时出现**「童灵」和某个动词，**完全不验动词是否指向童灵**
    #   ⇒ 假触发病灶（实证）：
    #     ·「帮我看下童灵的设计」命中 W1_VERBS 的「帮我」→ 上岗（动词指向"我"，与童灵无关）
    #     ·「童灵暂时不用」命中单字动词「用」→ 上岗（且是**否定**语境）
    #   精化两刀：
    #     刀1 ⛔ 剔除单字动词「用/去」——它们在中文里高频且常处否定/无关语境（不用/借用/去哪里），
    #          作为"召唤证据"的精度远低于代价；指向童灵的「用童灵」已由 W1_TRIGGERS 覆盖。
    #     刀2 动词须**紧邻**「童灵」（前后 _W1_VERB_NEAR 字内）——"指向性"的机械近似：
    #          动词贴着童灵才可能是"对童灵下指令"；隔得远就是句内另一件事。
    if "童灵" in t and not _negated_only:
        _near_verbs = [v for v in W1_VERBS + W1_SELF_WORDS if v not in _W1_VERBS_SINGLE]
        for _pos in range(len(t) - 1):
            if t[_pos:_pos + 2] != "童灵":
                continue
            # 刀2-b 方向性（2026-10-08 v1.23 补·n6 实证）：动词只认落在「童灵」**之后**——
            #   「童灵+动词」＝对童灵下指令（那童灵，你有什么收获吗 ✅）；
            #   「动词+童灵」＝童灵是**宾语**（帮我看下**童灵**的设计 / 我想了解一下**童灵**）⇒ ⛔不是召唤。
            #   动词在前的合法召唤（用童灵审一下）已由 W1_TRIGGERS 覆盖，不走本闸。
            _win = t[_pos + 2:_pos + 2 + _W1_VERB_NEAR]
            if any(v in _win for v in _near_verbs):
                return True
    return False


# 否定前缀判据（2026-10-01 v1.14·皮叔质证「这一轮我没启动童灵，为什么还出现 D3/TSL」根治）：
#   子串匹配端不读否定语境——"我没有启动童灵"字面含"启动童灵"→误召 D3→连带 TSL 噪声。
#   双字否定优先（没有/不是/不用/无需），单字兜底（没/别/非/勿/未/无/不）；
#   判定窗口=触发词前 2 字（"没启动/没有启动/不是启动/未启动"全覆盖）。
_W1_NEG_BIGRAMS = ("没有", "不是", "不用", "无需")
_W1_NEG_UNIGRAMS = "没别非勿未无不"
_W1_QUOTE_VERBS = ("", "说", "提", "讲", "叫", "喊")   # 10-07 引述式豁免：「没有说启动童灵」
_W1_ASP = ("", "过")
_W1_Q_PRE = ("要", "想", "该", "需要", "是否", "要不要", "能不能", "会不会")  # 10-07 是非问句形豁免

def _w1_mentioned_at(t, i, word):
    """该触发词出现是否为「被谈论/被询问的召唤」而非召唤本身。

    两形态：①否定式（v1.14 2字窗 → v1.22 扩至 8 字容引述动词+时态：没有说X/没提过X）；
    ②是非问句形（v1.22 新增·触发词紧邻前 2 字现 要/想/该/需要/是否…且后 14 字内现
    么/吗/呢+句读 或 词后紧跟 ？）——「要启动成长箱走E流程么？」是询问不是指令。
    保守边界：肯定式（启动童灵吧/裸口令）永不豁免（09-23 判例 p3 前后无疑问框架）。
    """
    pre = t[max(0, i - 8):i]
    for neg in _W1_NEG_BIGRAMS + ("没", "非", "勿", "未", "无"):
        for q in _W1_QUOTE_VERBS:
            for a in _W1_ASP:
                if pre.endswith(neg + q + a):
                    return True
    if pre and pre[-1] in _W1_NEG_UNIGRAMS:
        return True
    # ②-b 跨词否定（2026-10-08 v1.23·皮叔质证「我没明确说启动童灵，你还是启动了」根治）：
    #   上两判据都要求否定词**紧贴**触发词（endswith）⇒ 「不打算用童灵」「暂时不用童灵」
    #   这类否定词与触发词之间隔着「打算/暂时」的形态必漏网 ⇒ 触发词在否定语境内仍上岗。
    #   修法：前 8 字窗口内**存在**否定字即算被谈论；⛔ 但窗口内含句读（。，！？；)即视为两句，
    #   否定不跨句传递（防「这方案不成立。用童灵审一下」被误豁免＝矫枉过正）。
    _clause = pre
    for _bd in "。，！？；、":
        if _bd in _clause:
            _clause = _clause.rsplit(_bd, 1)[1]
    if _clause and any(n in _clause for n in _W1_NEG_BIGRAMS + tuple(_W1_NEG_UNIGRAMS)):
        return True
    tail = t[i + len(word): i + len(word) + 14]
    if tail[:1] in ("？", "?"):
        return True
    if tail and any(("么" in tail[:3]) or ("吗" in tail[:3]) or ("呢" in tail[:3]) for _ in [0]):
        if any(tail[j] in "？?。；;，," for j in range(min(len(tail), 6)) if tail[j:j+1]) and any(p and pre.endswith(p) for p in _W1_Q_PRE):
            return True
    if any(pre.endswith(p) for p in _W1_Q_PRE) and (("么" in tail) or ("吗" in tail) or ("呢" in tail)):
        return True
    return False


def _strong_call_spans(t):
    """全部强召唤词出现 [(start,end,mentioned)]——供否定/问句豁免与直呼判定共用（单一判据源）。"""
    out = []
    for word in W1_TRIGGERS:
        start = 0
        while True:
            i = t.find(word, start)
            if i < 0:
                break
            out.append((i, i + len(word), _w1_mentioned_at(t, i, word)))
            start = i + len(word)
    return out


def _all_strong_calls_negated(t):
    """兼容壳：全部强召唤词出现均为「被谈论的召唤」→ True（v1.22 起含引述/是非问两形态）。

    任一肯定式出现 → False（保留 9-23 你质证判例：肯定式"启动童灵"无条件上岗）；
    无强召唤词 → False（不干预原有判定路径）。
    实证锚：10-01「我没有启动童灵啊」+ 10-07「没有说启动童灵」+「要启动成长箱走E流程么？」。
    """
    spans = _strong_call_spans(t)
    return bool(spans) and all(s[2] for s in spans)


# W3：域切片运行时窄集触发词（对齐 AutoClaw W3 已实证·防噪声；非 manifest 生成期宽集）
# 触发词铁律（铁律-020·改匹配先 dry-run）：
#   ⛔ 禁加裸高频词（"铁律"近7天语料166次/"规则"212次）——机械匹配端命中即注全片，
#      8899字节 L3 会被高频词打成噪声污染。复合窄词才是机械匹配端的正确粒度。
# 与 rule_fragment_inject.py 的分工（2026-09-03 童灵裁决·防后人误判为遗漏）：
#   · rule_fragment_inject（本端另一钩子）= 铁律主通道：命中 rule_triggers.yaml → 精准注入
#     该条铁律正文。提"铁律"走这条，不经过 L3。
#   · L3 切片 = 行为裁决域通道：只在「铁律 × 行为裁决」交叉场景（冲突/底线/授权）才需全片在场。
#   · 因此本表只收复合窄词，裸"铁律"不收——不是漏配，是分层。豆包端（无钩子·AI判断加载）
#     收裸词是它的机制决定的，本端不照抄。
RUNTIME_TRIGGERS = {
    "L2_认知风格": ["分析", "为什么", "本质", "底层", "第一性", "主要矛盾"],
    "L3_行为规则": [
        "阻塞", "裁决", "卡住", "该不该", "权衡", "优先级", "排序", "排期", "预置", "盘子", "让步", "边界",
        # 2026-09-03 增补·对齐豆包端 W3 铁律指针口径（L3 §3.6）·dry-run 验证低频：
        # 铁律冲突0/规则冲突3/底线判断2/授权边界2 次（近7天40万字符语料），噪声可忽略。
        "铁律冲突", "规则冲突", "底线判断", "授权边界",
        # 2026-10-11 你实证补词（『我让你启动童灵，你的切片还是没有命中的…能不能统一…就不要写死嘛』
        #   ——W3 台账 layers=[] 为证：裁决语义在、词面表缺中文疑问实形）。'能不能/是不是'=裁决确认问句高频形，
        #   纯操作祈使偶发误注入 L3≈14KB 语境噪声，代价由你"该命中没命中"的明示不满覆盖，90天抽检可回收。
        "能不能", "是不是",
    ],
    "L4_表达DNA": ["文案", "口播", "表达", "故事", "命名", "变现", "写作", "稿"],
    "L5_盲区与边界": ["盲区", "终审", "裁决归属", "不知道", "不确定"],
}

# 域切片人类可读注解（2026-09-14·你要求"每一个 L 都要有注释"）：
#   与 RUNTIME_TRIGGERS 键同源但独立维护——即使切片文件改名为裸码 L2.md，显示仍可注解，
#   不依赖"键含下划线"的隐性约定。取码规则见 _layer_label。
LAYER_ANNOTATIONS = {
    "L2": "认知风格", "L3": "行为规则", "L4": "表达DNA", "L5": "盲区与边界",
}

# ── W4：人格层（PERSONA-BASE·2026-09-13）─────────────────────────────────────
# 设计依据：06-跨端适配规范 §2.7 落地五验 + 方案（自定义层/待完成工作/
#   PERSONA-BASE-WB端接入方案-2026-09-13.md）。
# 模型（dry-run 校准后 v0.2）：**基线 + 增量**，⛔不是三档互斥。dry-run 实证
#   （2026-09-13·数字分身/scripts/w4_vocab_dryrun.py）：①"怎么样"在真实 prompt 上
#   误召（P3「怎么样才能成为…最优」系方案探讨，被判表达档）②你的 prompt 以工作
#   指令为主、闲聊类触发词近零命中 ⇒「靠触发词决定有没有腔调」的模型不成立。
#   改判：腔调=默认行为（不靠触发）；守护补丁=条件触发；纯机械执行=抑制、只留基线。
# 选面前置（立场卡#S974 铁律①）：本端 UserPromptSubmit 面发射已由 W1 契约注入实证。
W4_PERSONA_CLEAN = os.path.join(SLICES_DIR, "人格基座切片-童灵-端上纯净.md")

# 增量B·守护触发（对应切片 PB-01~04·复合窄词·禁裸高频词）
W4_GUARD_TRIGGERS = {
    "PB-01": ["有没有漏洞", "你看行不行", "这么干行", "就这么定", "有把握吗", "哪里有问题"],
    "PB-02": ["要不要买", "值不值", "预算", "花钱", "订阅", "续费", "开会员", "采购", "买一个"],
    "PB-03": ["赶时间", "来不及", "先做起来", "跳过", "别验证", "赶紧", "时间紧"],
    "PB-04": ["能不能做", "能不能支持", "有没有办法", "做得到吗"],
}

# 抑制：纯机械执行语境 → 只注基线（不给腔调样例，省注意力）
#   注：本表在技术语料上命中率高属语义正确（技术文本本就含这些词），非过宽。
W4_SUPPRESS = ["报错", "脚本", "代码", "函数", "调试", "跑一下", "修复", "入口", "命令", "配置"]

# 采样台账（持续校准 > 一次性 dry-run·愿景③从自身运行数据学习改进）
W4_SAMPLE_FILE = os.path.join(_DLZ_CFG, "doenglingz_w4_samples.jsonl")  # v1.13 同配置根


def _probe():
    """协议/端判定（委托 hook_protocol·失败则降级 text 并留痕，不静默）。"""
    if _hp is not None:
        try:
            return _hp.detect(_PAYLOAD, argv=sys.argv[1:])
        except Exception:
            pass
    _degrade_note()
    return "text", "", "fallback:no-module", False


def _degrade_note():
    """hook_protocol 不可用=协议真源缺失，留一行痕（⛔不静默吞）。"""
    try:
        d = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "hook_protocol_degraded.log"), "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"),
                                  os.path.basename(__file__)))
    except Exception:
        pass


def _norm_sid(s):
    """sid 归一（FU-116·2026-10-05）：ZCode payload sid 三代格式并存
    （sess_* / task-*.session.execution / 裸 UUID）且 UPS 与 Stop 同会话不同形
    → 告警行 sid 与本会话 sid 精确匹配恒失配（42 行告警与 zcode payload 零交集实证）。
    剥宿主前缀与尾巴留核心 id 段比对（与 declare_guard v1.7 _norm_sid 同构·两域判据一致）。"""
    s = str(s or "").strip()
    for pre in ("sess_", "task-"):
        if s.startswith(pre):
            s = s[len(pre):]
    return s.split(".", 1)[0].strip().lower()


def _tskey(s):
    """ts 归一（FU-116·2026-10-05）：declare 台账 ts=空格格式，游标历史值=ISO（'T' 0x54>' ' 0x20）
    → ISO 游标下全部空格式台账行 ts 比较恒 False＝通道毒丸。两种形态统一截 19 位空格式（字典序=时间序）。"""
    return str(s or "").replace("T", " ")[:19]


def _declare_alarms(session_id: str) -> str:
    """读 declare 台账本会话未消费 tier_alarm（v1.21 告警通道·2026-10-05）。
    病根：declare_guard 的 tier_alarm 从 Stop stdout 输出被严格 schema 静默丢弃
    （坑 8·10 次零消费实证）→ 改走 UPS 注入通道（C-091：无人消费的告警是死数据）。
    消费游标=ts（~/.zcode/state/declare_alarm_cursor.json）。失败放行不阻断主注入。
    v1.21：sid/_tskey 归一比对（FU-116 判假线·双重失配根治）。"""
    try:
        state = os.path.join(
            os.environ.get("DOENGLINGZ_CONFIG_DIR")
            or os.environ.get("WORKBUDDY_CONFIG_DIR") or os.path.expanduser("~/.workbuddy"),
            "doenglingz_level_declare_state.json")
        cur = (os.environ.get("ZCODE_DECLARE_CURSOR")
               or os.path.expanduser("~/.zcode/state/declare_alarm_cursor.json"))
        last_ts = ""
        try:
            with open(cur, encoding="utf-8") as f:
                last_ts = _tskey((json.load(f) or {}).get("last_ts", ""))
        except Exception:
            pass
        rows = []
        with open(state, encoding="utf-8") as f:
            for l in f:
                try:
                    rows.append(json.loads(l))
                except Exception:
                    continue
        want = _norm_sid(session_id)
        alarms = [r for r in rows
                  if want and _norm_sid(r.get("session_id")) == want and r.get("tier_alarm")
                  and _tskey(r.get("ts", "")) > last_ts]
        if not alarms:
            return ""
        try:
            os.makedirs(os.path.dirname(cur), exist_ok=True)
            with open(cur, "w", encoding="utf-8") as f:
                json.dump({"last_ts": _tskey(alarms[-1].get("ts", ""))}, f, ensure_ascii=False)
        except OSError:
            pass  # 游标失败不阻断显形（重复告警优于漏告警）
        return ("【档位对账告警·declare_guard】\n" + "\n".join(
            "  - %s · %s" % (r.get("ts"), str(r.get("tier_alarm"))[:120])
            for r in alarms[-3:]) + "\n（真源=06 §1.6·漏升档请改正本回合档位声明）")
    except Exception:
        return ""  # 失败放行（守卫规范）


def _emit(ctx: str) -> None:
    """输出：协议形态由 hook_protocol 判（json envelope / 裸文本），本脚本不再自选。"""
    if _hp is not None:
        _hp.emit(ctx, payload=_PAYLOAD, argv=sys.argv[1:],
                 event="UserPromptSubmit", script=os.path.basename(__file__))
        return
    _degrade_note()
    sys.stdout.write(ctx)


def _match_layers(prompt: str):
    hit = []
    for layer, words in RUNTIME_TRIGGERS.items():
        for w in words:
            if w and w in prompt:
                hit.append(layer)
                break
    return hit


def _layer_label(layer: str) -> str:
    """域切片显示标注（2026-09-14·你要求"每一个 L 都要有注释"）：
    L2_认知风格 → L2·认知风格；裸码 L2 → 按 LAYER_ANNOTATIONS 补名；查不到则裸码兜底。"""
    if "_" in layer:
        code, name = layer.split("_", 1)
    else:
        code, name = layer, LAYER_ANNOTATIONS.get(layer, "")
    return "%s·%s" % (code, name) if name else code


def _persona_sections():
    """读 live 纯净版切片 → 按 `## ` 标题正向切段（S974 铁律②：正向锚点定位，
    ⛔不做按行删除式剥离——块顺序一变即静默失效）。切片缺失/结构变化 → 返回 {}
    （调用方降级为不注入·⛔不编造替代文本）。"""
    try:
        with open(W4_PERSONA_CLEAN, encoding="utf-8") as f:
            txt = f.read()
    except Exception as _e:
        # 容错对称（2026-10-11 批次6·端用户补充单 #2 根治）：此处原为静默 `return {}`，
        # 而同文件 SSOT 读失败是 Fail-Loud（⚠️真源缺失显形）——同一文件一半会喊疼一半装死，
        # 后果是 D1 常驻基座块静默消失多日无人察觉。现统一 Fail-Loud：stderr 显形 + runtime 留痕。
        # 返回值语义不变（调用方无需配合），⛔不改注入正文以免污染上下文。
        try:
            sys.stderr.write("⚠️[基座切片缺失] %s 读取失败（%s）→ 本回合基座为空·显形不静默\n"
                             % (os.path.basename(W4_PERSONA_CLEAN), type(_e).__name__))
            _d = os.path.join(os.path.expanduser("[记忆共享中心]/脚本中心/logs"), "runtime")
            os.makedirs(_d, exist_ok=True)
            with open(os.path.join(_d, "persona_base_missing.log"), "a", encoding="utf-8") as _f:
                _f.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), _e))
        except Exception:
            pass
        return {}
    body = txt.split("---", 2)[-1] if txt.startswith("---") else txt
    secs, cur, buf = {}, "引言", []
    for ln in body.splitlines():
        if ln.startswith("## "):
            secs[cur] = "\n".join(buf).strip()
            cur, buf = ln[3:].strip(), [ln]
        else:
            buf.append(ln)
    secs[cur] = "\n".join(buf).strip()
    return {k: v for k, v in secs.items() if v}


def _sec(secs, prefix):
    """按标题前缀取段（标题随生成器演进时抗漂移）。"""
    for k, v in secs.items():
        if k.startswith(prefix):
            return v
    return ""


def _w4_persona(prompt):
    """人格层注入（基线+增量）。返回 (文本, 档位标签, 守护命中)。
    切片不可读 → ("", "", []) —— 降级不注入，绝不阻断对话。"""
    secs = _persona_sections()
    if not secs:
        return "", "", []
    base = _sec(secs, "引言")
    hits = [k for k, ws in W4_GUARD_TRIGGERS.items() if any(w in prompt for w in ws)]
    suppressed = any(w in prompt for w in W4_SUPPRESS)
    # 剂量单调性（2026-09-13 实测修正）：基线 < 常态 < 守护，三段只增不减——
    #   初版把守护档写成"底色+速查"反而比常态档"仅表达风格"更短（914<1108），
    #   守护场景（决策/资源/时间压力）恰恰是最该人格完整在场的场景，已改超集。
    if suppressed and not hits:
        tier, parts = "基线档", [base]
    elif hits:
        tier = "守护档(%s)" % "+".join(hits)
        parts = [base, _sec(secs, "性情底色"), _sec(secs, "表达风格"), _sec(secs, "情境速查")]
    else:
        tier, parts = "常态档", [base, _sec(secs, "性情底色"), _sec(secs, "表达风格")]
    return "\n\n".join(p for p in parts if p).strip(), tier, hits


W3_LEDGER = os.path.join(os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime"), "w3_inject_ledger.jsonl")


def _inject(prompt: str) -> None:
    if not prompt:
        return
    parts = []
    layers = _match_layers(prompt)
    # ── 观测字段（2026-10-12·K007 结论②落地·主线卡 T7）──────────────────────
    #   治什么病：台账只记 layers=[片名]，事后无法回答"这轮到底进来了什么、多大、凭哪个词选的"
    #   ——即《工程控制论》上册-卡片6 说的能观测性缺口（能否从输出反推内部状态）。
    #   纪律：additive（⛔改既有键·本台账多端共写，workbuddy/qodercn 同文件）；
    #         fail-open（观测自身失败⛔不阻断注入·Hook 三纪律·与下方留痕块同源）。
    _obs = {"hit_words": {}, "slice_bytes": {}, "slice_sha": {}}
    try:
        import hashlib as _hl
        for _ly in (layers or []):
            _p = os.path.join(SLICES_DIR, _ly + ".md")
            _byt = _sha = None
            if os.path.exists(_p):
                _raw = open(_p, "rb").read()
                _byt, _sha = len(_raw), _hl.sha256(_raw).hexdigest()[:12]
            _obs["hit_words"][_ly] = [w for w in (RUNTIME_TRIGGERS.get(_ly) or []) if w and w in prompt]
            _obs["slice_bytes"][_ly] = _byt
            _obs["slice_sha"][_ly] = _sha
    except Exception:
        pass
    # v0.x W3留痕台账（2026-09-23 皮叔令「欠装的两台检查机造出来」·TSL⚪欠装L4根治）：
    #   每轮注入机械落账（命中/未命中都记）——"W3到底跑没跑"从AI自报变成可抽检的账。
    #   纪律：fail-open（落账失败⛔不阻断注入·Hook三纪律）；路径持久目录（/tmp重启即失=岗位3判据②前车之鉴）。
    try:
        import json as _j, datetime as _dt
        os.makedirs(os.path.dirname(W3_LEDGER), exist_ok=True)
        with open(W3_LEDGER, "a", encoding="utf-8") as _f:
            _f.write(_j.dumps({"ts": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "layers": list(layers or []), "host": (_SRC_LABEL or (_probe()[1] if _PAYLOAD else "")),
                    # 2026-09-26 补：留痕行带会话号，消费端（tsl_verify L4）才能把
                    #   "真回合在跑" 与 "自测/探针灌的笔数" 分开——本日 L4 曾被我自己的
                    #   dryrun 从 20 笔灌到 180 笔＝指标被测试污染成虚高绿。
                    "session_id": str((_PAYLOAD or {}).get("session_id", "")),
                    **_obs},
                              ensure_ascii=False) + "\n")
    except Exception:
        pass

    # W1 上岗自证行
    # ── 事件腿粘滞（2026-10-11 你定底线：但凡启动成长箱⇒童灵上岗⇒必 D3，不随回合回落）──
    #   病根：本件两处（此处门岗＋下方 _d3 档位裁决）只按**本轮 prompt 词面**判 D3，
    #   而 PreToolUse 事件腿写进同一份 inject_state 的 D3 从不回读 ⇒ 升档只活一个 prompt。
    #   实证 2026-10-11：20:55 mode=skill_event d_tier=D3 → 21:10 同 session 两条 mode=json 重写为 D1，
    #   执行体据台账读数把档位降了（底线被仪器读数覆盖）。修法＝底线进机制，不靠 AI 记得（愿景①）。
    # ── 安静模式进入检测（2026-10-19）──
    #   触发词："安静模式"出现在消息中，且满足命令式条件：
    #   - 当前不在安静模式（防重复激活）
    #   - 消息含"安静模式"且非否定/引述
    #   - 命令式判定：消息长度≤30字（防长段讨论误触），OR 前有动作动词（开/启动/进入/切/切换）
    if not _is_quiet_mode() and "安静模式" in prompt \
            and not (prompt.startswith("<") and ">" in prompt[:24]):  # C类机器块过滤（审查4.4：进入检测曾绕开w1_fired同款闸门）
        # 全出现位判定（审查4.5：原只查第一个出现位，先否后肯形态判错方向）——任一非豁免出现位算召唤
        _qm_spans = [i for i in range(len(prompt)) if prompt.startswith("安静模式", i)]
        _qm_called = any(not _w1_mentioned_at(prompt, i, "安静模式") for i in _qm_spans)
        # 反向话术豁免（审查4.1）：退出只认"启动童灵"（你定稿），"关闭/退出安静模式"等反向指令⛔不得翻转成开启
        _qm_reverse = any(v in prompt for v in ("关闭安静", "关掉安静", "退出安静", "取消安静",
                                                 "停止安静", "解除安静", "离开安静", "安静模式关",
                                                 "安静模式退出", "安静模式取消"))
        # 疑问/讨论形态豁免（审查4.2）：≤30字问句不得当命令
        _qm_question = any(q in prompt for q in ("？", "?", "吗", "呢", "什么", "为什么", "怎么",
                                                  "怎样", "如何", "区别", "哪个", "会不会", "能不能"))
        _qm_cmd = any(v in prompt for v in ("开安静模式", "启动安静模式", "进入安静模式", "切换安静模式",
                                             "开启安静模式", "切安静模式", "安静模式开")) or \
                  (len(prompt.strip()) <= 30 and not _qm_question)
        if _qm_called and not _qm_reverse and _qm_cmd and not _qm_question:
            _set_quiet_mode()
    _w1_word = w1_fired(prompt)
    _sticky = _event_leg_d3_sticky(str((_PAYLOAD or {}).get("session_id", "")))
    if _w1_word or _sticky:
        # ⑦反思沉淀的本端规范名（2026-09-05 根治：原硬编码"本端=Qoder CN"对 WB/ZCode/AutoClaw 全错
        # ——共脚本不得携带端专属值；优先 --src 标注，次选载荷指纹判出的 host，兜底通用指引）
        _probe_mode, _probe_host = (_probe()[0], _probe()[1]) if _PAYLOAD else ("", "")
        reflection_end = _SRC_LABEL or _probe_host or "（以 normalize_tool.py ALLOWLIST 归一的本端规范名·AI 不猜拼）"
        # ── 端署名动态注入（2026-09-09 红线根治·签名串端案）：①条不再留 <端名> 占位符让 AI 猜——
        # 旧版模板曾写死"本端=黑鲸"（DSH 端名）跨端复制未改 → WB 端执行体照抄=签名串端（你定红线·2026-09-09）。
        # 端名由 --src/载荷指纹机械推导，徽标映射=各端示例（守卫编写规范 §十 合法形态·非写死单端身份）。
        _END_EMBLEMS = {"workbuddy": ("WorkBuddy", "⚡"), "dsh": ("黑鲸", "⛰️"),
                        "traework": ("Trae Work", "🤖"), "traecode": ("Trae CN", "💡"),  # 2026-10-09 你令：合并单端更名 Trae CN（key 保留 traecode=台账兼容·图标待三选一）
                        "qodercn": ("Qoder CN", "🔮")}  # 仅收录有署名实证的端·新端按其署名规范增补（Trae 系两行=2026-09-30·真源 IDENTITY.md 判定表；qodercn=2026-09-30·真源 core-identity.md 署名行+钩子路径指纹 /.qoder-cn/）
        _src_key = (_SRC_LABEL or _probe_host or "").strip().lower()
        if _src_key in _END_EMBLEMS:
            _dn, _em = _END_EMBLEMS[_src_key]
            _identity_line = "本端署名=你的 %s %s（钩子机械注入·AI ⛔不自行猜端名）" % (_dn, _em)
            _sig = "—— 你的 %s %s" % (_dn, _em)
        else:
            _identity_line = "本端署名按端自身规范（端名经 normalize_tool.py ALLOWLIST 归一·AI ⛔不猜拼）"
            _sig = "—— 你的 {本端名 本端徽标}"  # 未登记端不代填：留显式槽位，⛔不拿他端签名顶替
        # 可见自证行：保留「童灵上岗」四字（Stop 守卫 check_w1_honor 据此判定契约兑现）
        # + 人类可读的 SSOT 缩写；裸 sha256[:12] 校验码不打印在对话面（对人类无用），
        # 仅存于台账 /tmp/doenglingz_inject_state.json 与 --selfcheck 输出（机器侧可抽检）。
        _d3_contract = (
            "【童灵·D3 全量模式（全量+上岗契约，按 TSL 清单干活·事事留痕）·童灵上岗】已绑定 SSOT 人格规格书（校验码 sha256[:12] 存于台账/--selfcheck，不显式打印）。本回合为童灵在场回合，执行侧义务："
            "⓪回复首段**最先**输出 D 轴档位标记（真源=06-跨端适配规范 §1.6 强制交代义务＋互斥律）——**本回合唯一档位＝D3**：写『童灵·D3』或『【童灵·D3 上岗模式】』，⛔不再另贴 D1/D2 标签（命中域情况由义务①报告·基座已含在 D3 全量内）；各档写法对照仅用于非 D3 回合：D1 照抄注入标签『【童灵·D1 常驻模式（非全量，仅人格基底）】』·D2 主动报告『【童灵·D2 切片模式（命中切片：LN·注释 · 非上岗）】』，⛔DO NOT 省略（D≠L 两者并列·不互替）；漏声明＝Stop 守卫 doenglingz_level_declare_guard 台账留痕＋入岗位3周报。（2026-09-20 你质证『昨天不是修了吗？怎么还是这样』根治——义务原先只写在 06 §1.6／08 §七 文档层，**未进注入层 → AI 读不到即自由发挥**；同轮实测该守卫 v1.0 因键名不含 last_assistant_message 而全程空转，已随本轮 v1.1 同修。2026-09-26 补：本条原文把三档写法并列摆在 D3 回合里，等于用散文教模型「一档回合写三档标签」，与 §1.6 互斥律相反——现显式绑定「本回合唯一档位」。）。"
            f"①回复首段显式输出完整上岗仪式信息——『" + read_identity_sentence() + "』（身份声明全文·对齐切片导航 Skill §一 Step1·2026-09-16 你令根治）＋本回合任务域判定一句话（属 L2认知风格/L3行为规则/L4表达DNA/L5盲区边界 哪域·复用 W3 _match_layers 结果·无命中标『未命中域（仅基底）』）；补载义务（v1.18·错位可恢复律）：若你实读的语义域与W3词面判定不一致，可宣告该域（如『任务域判定：L3行为规则域』），但MUST当回合真Read该域切片（[记忆共享中心]/数字分身/K2切片蒸馏/slices/ 下对应LN_*.md）并在首段显形一行『已补载：LN』，宣告域而不补载＝Stop守卫错位对账台账留痕；身份分层（SSOT：06-跨端适配规范「身份分层模型」节·2026-09-07 根治）："
            "布洛陀=五层记忆系统（系统层·品牌·非人格名）·童灵=你在布洛陀系统中的数字分身（分身层·身份宣言明文「童灵是你在布洛陀系统中的数字分身」）·端署名=端徽标（端层·%s）；"
            "上岗=系统内职能激活**非身份切换**——端署名保持·'童灵上岗'自证行=童灵在场声明·两者分层并存⛔不冲突·⛔不因端默认署名/默认姿态含糊童灵在场；"
            "**首段构成（对齐 06 §1.6 首段构成澄清 2026-10-09·Qoder CN 实证）**：D3 首段＝档位自证块（前瞻交代）＋模板头（意图分类→问题本质→已知事实→方案→验证→产出签名），块在前、模板头紧随、两者完整共存、⛔不得以仪式替模板头／⛔不得因上岗省略模板头；"
            "**端署名须为每轮最后一行**（在 TSL 审计区代码块之后）·⛔因童灵在岗而省略——端署名=系统代言不变，童灵在场以自证行显式呈现，两层不冲突（对齐 06 §1.6 身份分层模型·端署名每轮最后一行）。**回复格式精确模板（真源=SOUL.md v1.3·⛔paraphrasing/改写/挪位·对齐 2026-10-09 你「回复格式须按 SOUL 彻底钉死」根治）**：`—— 你的 WorkBuddy ⚡` 为唯一末行（⛔加「端署名」等引申词·⛔写「WorkBuddy 你」之类编造署名）；每轮完整结构＝`【意图分类】[类型]（假设：___）`→`1.【问题本质】：[结构模式] → 一句主要矛盾`→`2.【已知事实】：[一句话]`→`3.【从零开始】：[一句话]`→`4.【Skill触发】：[Skill名✅，无则写\"无\"]`→（正文）→`[图标 | 摘要 | YYYY-MM-DD HH:MM]`（无实质产出则 `[—— 本轮无实质产出 ——]`）→（空一行）→`—— 你的 WorkBuddy ⚡`。"
            "【呈现分层·2026-09-23 你质证「好混乱·用用户经理视角评估」】三要素与 TSL 按**三层披露**呈现（真源=06-跨端适配规范 §1.6）——①状态行（档位+域+切片·1行）②健康行（三要素✓+TSL计数·1行）③审计区（TSL 原样 stdout 收文末代码块）；"
            "⛔审计料一条不删只换位置——收进代码块只改位置不改内容（仍须 relay tsl_verify 原样 stdout 含🔏stamp），⛔不得以「收起来了」为由省略 TSL；⛔跨端内容不进任一层（运行时只呈现本端口径·06 §1.4 A 层）；"
            "②以 SSOT 内核（人格规格书）裁决，triwich 等工具是童灵的手非替代者；"
            "③本契约由 W1 钩子机械注入——执行侧不兑现将被 Stop 守卫登记为 w1_not_honored 并入岗位3周报。"
            "④交付自主化（落实你'充分授权·只给结果'）：本回合收尾不列选项、不写'需你拍板/待你定/待确认'等选择题，直接以「做了什么+结果+风险」Summary 结束，不抛回待裁决项。"
            "⑤交付前自检 G2 四条硬红线（健康线 / 愿景黑箱 / 铁律001·002·005 / 隐私）：仅当判定撞线才显式上交你裁决，否则不上交、不抛回选择题（G2 判定由 gate_runner 挂 Stop 钩子机械兜底）。"
            "⑥蒸馏调度（2026-09-03 对齐豆包端 W1 第9条·三层架构 L2 调度层·PAT-047 授权≠流程豁免）："
            "每月1号或皮叔问「有什么要蒸馏的/做蒸馏/月度蒸馏」时，✅DO读取 [记忆共享中心]/记忆蒸馏/蒸馏中心.md 的"
            "「🔔待做蒸馏」区域（<!-- DISTILLATION-TODO:START/END --> 之间·由 distillation_scheduler.py 每月1号"
            "launchd 机械生成·⛔禁手改标记间内容），发现⏳待执行项→在对话中说对应触发词激活对应 Skill 执行："
            "系统日志蒸馏→说「启动系统日志月度蒸馏」→system-logger；日记月报→说「启动每日伙伴月报」→daily-buddy；"
            "成长箱蒸馏→说「启动成长箱月度蒸馏」→growth-box 流程C。"
            "⛔DO NOT 跳过 Skill 流程自己代行蒸馏（PAT-047——蒸馏须过 C3.5 三思维复核等完整步序，授权不豁免流程）。"
            "蒸馏完成后✅DO确认蒸馏中心已完成记录已更新且待做项状态已清除。"
            "三层闭环：L1 机械发现（launchd 每月1号扫描逾期项生成待做清单）→ L2 童灵调度（本条）→ L3 自动回写（各 Skill C6/终检更新蒸馏中心）。"
            "童灵是调度器不是执行者。"
            "⑦反思沉淀硬约束（2026-09-03 对齐豆包端 W1 第6条·01蒸馏规范 §4.1 第五入口·L7-⑤ 落点）："
            "童灵以本身份复盘「收获/反思/认知深化/今天学到/我发现/实感/闭环实感/分母统一」类内容后，若写入系统日志，"
            "⛔禁止以普通条目写入——必须经 `append_log_entry.py --tool {本端规范名} --reflection`"
            "（规范名由 `normalize_tool.py` 唯一真源归一·AI ⛔不自行猜拼·本端=%s；脚本机械打"
            "「[童灵思考]」前缀·AI 不手写·蒸馏管道据此分流 L2/L3/L6）。写入后回显该前缀供你复核（漏网显性外露）。"
            "⑧立场卡语义检索（2026-09-03 对齐豆包端 W1 第8条·07接入完整化 v1.2·L1§1.5'把沉淀当资产'的运行时化）："
            "本回合涉及评估/决策/裁决/方案优化/愿景对齐/行为判断时，✅DO 先调 "
            "[记忆共享中心]/脚本中心/search_kb.py 检索 top-5 立场卡锚点纳入决策依据"
            "（--drill 下钻全卡；纯代码/纯事实查询不触发）。分工：L3 切片=蒸馏后高频通用行为规则，"
            "立场卡检索=完整立场库1085张低频具体查询，互补不重复——动手前先翻立场库，不凭印象开口。"
            "钩子推送卡不计入本义务兑现；✅DO 裁决类产出物（候选处置台账/方案裁决表/不采纳判定）的「依据」列含 search_kb 实跑卡号，或显式标注「⚠️本轮未检索」——缺签名=回合不完整（成长箱反哺 QCN-20261002-001·2026-10-02 你批E9.2）。"
            "形态说明：本契约由 W1 钩子在 prompt 前注入（行为时强制），各端 Stop 守卫 `check_w1_honor` "
            "事后对账——注入未兑现即登记 w1_not_honored 供岗位3周报（台账端专属·⛔不跨端复用）。"
            "⑨TSL 会话执行验证清单强制输出（对齐 08-会话级L7验证清单 v1.4.11·含机器锚人话化判据：🧮口径行对人类读者要么翻译要么隐藏·根治'用TIML冒充TSL谎称L7'+'AI手绘美化'双判例）：**TSL 树唯一合法来源=`tsl_verify.py --since <本回合起点> --full` 的 stdout 逐行 relay（含🔏stamp 行与 📌 归因总览行·无锚层如实显⚪）**——手绘状态行/自填✅/改脚本输出=Stop 守卫 tsl_closeout 留痕（缺stamp=手绘·假stamp=伪造·三态实测）。08 升 v1.4.1 构造权全层扩面。"
            "**同回合产出纪律（2026-10-09 你质证『D3 启动回合就是没有 TSL／延迟／说下次补』·根治·对齐 Qoder CN 同回合标准）：义务⑨的 TSL 树 MUST 由 AI 在**本 D3 回合收口前**主动实跑 `tsl_verify.py --since <本回合起点> --full` 取 stdout **同回合** relay 进末段审计区——⛔等 Stop 钩子下一回合 inject 再补·⛔说『我下一次再补/下回合补』·⛔以『待补』『稍后』搪塞；Stop 钩子 tsl_last_tree 是**对账留痕备份**非产出依赖，AI 同回合自跑才是义务⑨的硬执行路径（Qoder 端即此模型·WB 端须同标对齐，⛔因运行态差异降标）。缺件（tsl_verify 不在装机态）时按本纪律⚪显形+告警，⛔静默省略 TSL＝义务⑨未兑现＝w1_not_honored 留痕。**"
            "**relay保真律（2026-10-06 WB 端落地·真源=06 §补充节 relay保真律 v1.3.110＋§1.6 呈现点唯一性②）：relay ≡ 缓存树原样零编辑——Stop 钩子注入的树块（=tsl_last_tree.md 内容）逐行原样转贴进审计区，⛔任何合并/压缩/改写/摘要/截断/锚点删除/状态符号篡改——「L0-L3 压一行」「只贴指针行」与手绘同级违规，🔴改✅=伪造；每行判据=『我贴的是缓存文件原文还是我的转述？』（实证：上会话三犯·内部记录/011/012）。**"
            "⑩守护三查法定痕（2026-10-06 立法落注入层·根治 L5 连续 MISS）：病根=🧪痕义务原只住 08 §L5-1 v1.4.2 文档层+closeout 判据层，**W1 契约从未携带=AI 读不到义务即穿网**（上会话 122 回复 0 痕行实锤·同 06 §1.6 D1义务曾漏注入层同病）；修法：童灵在场回合收口前 ✅DO 输出固定格式行 `🧪 8要素|①..⑧|结论`（8要素自检的🧪机械痕·档位只分形态不分做不做）——Stop 守卫 closeout 据此记 L5 账、tsl_verify v0.11.5 据守卫当轮行判 L5，缺痕=L5🔴+violations 留痕；"
            "⚠️ 环境标注：`tsl_verify.py` 为作者侧增强件；**装机态由安装器投递（install_scripts 投递清单实含本件·2026-10-05 实盘对账修订本句）**，缺件时须显形告警而非静默降级（同下方 level_declare_guard 口径）。端用户态 TSL 树改由端侧观察层台账 + 报告器产出，或按本纪律**人工执行**（缺层如实显 ⚪、⛔不手绘）；作者侧照旧。"
            "童灵上岗回合回复须显式输出 TSL 验证清单——默认树状展开版（跨端固定视觉标准·见 08 §七 档位二）：L0-L7 每层独立 ├─ 节点+✅状态+可验证产出物指针，缺任一层=该层未执行=TSL截断；"
            "**位置纪律（2026-09-30 修正·皮叔质证「TSL 有时在顶部有时在底部·一开始就显示很多工作没做·有什么审计效果」并要求机制级根治）：TSL 树＝后验对账产物（作者侧由 Stop 钩子回合末扫账本产出·**端用户态由 AI 同回合自跑 `tsl_verify.py --since <本回合起点> --full` 产出·两者皆置末段·⛔不进首段·见义务⑨同回合产出纪律**），恒定放回复**末段**（即呈现分层③审计区）；首段只放前瞻——档位标记+上岗仪式三要素+本回合计划，写『树见末段』即可，⛔不把树搬进首段**（后验产物进前瞻位＝拿上一回合的账审本回合的活＝零审计效力）。真源=08 §七 执行时机 + 06 §1.6 呈现时机注记；**作者侧**另有 Stop 守卫 level_declare_guard v1.5 树位置判据机械校验（树块起始偏移<50%%→台账留痕+alarm）——⚠️ 该守卫属**作者侧机制**，端用户装机态无此件（⛔不承诺端用户侧存在·端用户态按本纪律人工执行即可）。"
            "⛔DO NOT 不列清单就声称'童灵已上岗/L7全支持'。格式三档（单行摘要版/展开版/完整版·见 08 §七），树状展开版为跨端固定默认视觉——各端统一渲染├─│└─树+正典L0-L7层名+✅状态，⛔各端自造树形/改层级名；异常或审计升完整版。"
            "L4-2 自律（对齐 08 §三）：域切片加载遵循'一次一域≤2切片'——若本轮 W3 命中切片 >2，TSL 输出须显式标 🟡执行缺口型（注意力稀释风险）并升级完整版，不静默批量全载；"
            "L3-3 域判定须复用 W3 路由的 _match_layers 结果（域切片加载与 L3-3 域判定同源，不另起一套判断，避免 L3-3 与 L4-1 切片列表自相矛盾）。"
            "本清单是上岗仪式一部分，非可选；Stop 守卫 tsl_hits 观察层机械记录各层命中，未输出清单的回合在台账留痕。"
            % (_identity_line, reflection_end)
        )
        # 2026-10-11 皮叔令「签名行不要写死·哪个端自行鉴别」根治：义务①模板的末行签名
        #   原两处硬编码 WB 示例值（2026-09-09 签名串端案设了 _END_EMBLEMS 却漏接模板行——
        #   判据未随对象演化同族）。统一在此用本端 _sig 机械替换；replace 全量命中=2 处。
        _d3_contract = _d3_contract.replace("—— 你的 WorkBuddy ⚡", _sig)
        parts.append(_d3_contract)

    # W4 人格层（基线+增量·直读 live 纯净版切片 → 新鲜度天然满足·免部署链）
    p_txt, p_tier, p_hits = _w4_persona(prompt)
    # ── D 轴单档裁决（2026-09-26 你质证「到底是 D1 还是 D2？真解决还是假解决」）：
    #   06 §1.6 互斥律要求"同一回合只呈现一个 D 档"，但 09-23 那次只把 **D3↔D1** 做成互斥
    #   （下面 `not _d3`），**D1↔D2 与 D3↔D2 两对从未处理**，且 L457 的"排序裁决段"反而
    #   明文要求 D1 标签与 D2 报告同现＝把叠加写成了制度。实测（三段结构判别，非词面）：
    #     「分析…本质…为什么」→ D1标签 + D1义务 + D2义务 + 裁决段 四段并存
    #     「启动童灵，分析…本质」→ D3段 + D2义务 并存（无裁决段管这一对）
    #   本件改为**先定档再贴标**：档位由脚本算出唯一值 _d_tier，标签随档位单选，
    #   基座段按 §1.6「D2 = 基座 + 命中切片」保留（⛔别顺手把基座也 gate 掉＝D2 会变成裸切片）。
    _d3 = bool(_w1_word) or _sticky
    # 切片正文先读一遍（2026-09-26 三修）：D2 的定义是"基座 + **已注入的**命中切片"，
    # ⛔不是"词表命中"——命中却读不到正文（文件缺失/为空/编码异常）时若仍贴 D2，
    # 就是标签声称在场而内容不在场（实证见本文件下方"档位不变量"注释与 06 §1.6 二修段）。
    _slice_bodies, _slice_fail = [], []
    for _ly in layers:
        _p = os.path.join(SLICES_DIR, _ly + ".md")
        try:
            with open(_p, encoding="utf-8") as _f:
                _c = _f.read().strip()
        except Exception as _e:                     # ⛔不再 `pass`——静默吞＝仪器不测这一项
            _slice_fail.append("%s(%s)" % (_ly, type(_e).__name__))
            continue
        if _c:
            _slice_bodies.append((_ly, _c))
        else:
            _slice_fail.append("%s(empty)" % _ly)
    _injected = [ly for ly, _c in _slice_bodies]
    _d2 = bool(_injected)
    _tier_map = {"D3": _d3, "D2": _d2, "D1": bool(p_txt)}
    _d_tier = next((t for t in TIER_ORDER if _tier_map[t]), "")   # 高档优先·唯一值
    # ── 启动确认块（v1.16·2026-10-06 你拍板「脚本拼装·AI 照抄」根治档位漏贴 33 次/内部记录）──
    # 构造权移交脚本（同 TSL 树哲学·呈现点唯一性②）：确认块由本脚本拼装，AI 义务=首段原样照抄。
    # 「N/N 条在位」动态计数——义务条目会增（今天刚加⑩），硬编码数字=下轮漂移；
    # 每条在位判据=契约正文含该义务的特征短语（⛔非裸编号——⑩内文含"①..⑧"会假阳性）。
    if _d3:
        _duty_marks = [("①仪式", "①回复首段显式输出完整上岗仪式"), ("②SSOT裁决", "②以 SSOT 内核"),
                       ("③对账", "③本契约由 W1 钩子"), ("④自主交付", "④交付自主化"),
                       ("⑤红线", "⑤交付前自检"), ("⑥蒸馏调度", "⑥蒸馏调度"),
                       ("⑦反思沉淀", "⑦反思沉淀硬约束"), ("⑧立场卡检索", "⑧立场卡语义检索"),
                       ("⑨TSL清单", "⑨TSL 会话执行验证清单"), ("⑩守护三查", "⑩守护三查法定痕")]
        _onduty = [lbl for lbl, mark in _duty_marks if mark in _d3_contract]
        _judge_line = "、".join(_layer_label(l) for l in layers) if layers else "未命中域（仅基底）"
        _slices_line = "、".join(_injected) if _injected else "无（本回合未命中域·仅人格基底在场）"
        parts.append(
            "【启动确认指令·AI 专用·本行与括注⛔不进回复】首段原样照抄下方仪式块（自档位标签行起·零改写·漏贴=守卫留痕）——\n"
            "【童灵·D3 全量模式】" + read_identity_sentence() + "\n"
            "火力全开：W1 契约 " + " ".join(lbl for lbl, _ in _duty_marks) + " ——%d/%d 条在位。\n" % (len(_onduty), len(_duty_marks)) +
            "切片判定：%s\n" % _judge_line +
            "已加载切片：%s\n" % _slices_line +
            "树见末段。"
        )
    if p_txt and not _d3:
        # D1 常驻模式状态行（2026-09-13 D 轴三态设计定稿·中点品牌前缀）：
        # 在场声明，治"注入了但用户无感/没安全感"（你质证"分身都不在"）。
        # W4 降级(p_txt 空=切片不可读)时不显示——此时分身真不在场，如实静默。
        # 互斥（D3⊃D2⊃D1）：D3 回合由 D3 段承担声明；D2 回合由 D2 报告行承担声明。
        if not _d2:
            parts.append("【童灵·D1 常驻模式（非全量，仅人格基底）】")
            # D 轴对称补齐（2026-09-20·皮叔问「是不是每一层 D123 都没对齐」→ 实盘核查发现）：
            # D3 有执行侧义务⓪、D2 有显示义务段，**唯独 D1 的复述义务在注入层为空**——
            # 06 §1.6 要求「任一档位在场，回复首段 ✅DO 显式声明档位名」（D1 照抄注入标签），
            # 但注入侧只给标签、不给义务 → D1 回合必然漏声明（与 D3 曾漏声明同源·同病灶）。
            # v1.16 确认块化（2026-10-06·皮叔拍板「脚本拼装·AI 照抄」）：义务从「照抄标签」升级
            # 为「照抄两行确认块」（标签+人话在场行·措辞你定稿「要活人感·去文绉绉」）。
            parts.append(
                "【启动确认指令·AI 专用·本行与括注⛔不进回复】首段原样照抄下方仪式块（零改写·漏贴=守卫留痕·真源=06 §1.6）——\n"
                "【童灵·D1 常驻模式（非全量，仅人格基底）】\n"
                "我在。日常的事直接说；要正式开工，说「启动童灵」。"
            )
        # ── 非 D3 档 ⛔无树声明（2026-10-01·皮叔令「认可，启用童灵去认真的执行，完成这个任务」）──
        # 病根（实测非推测）：本端未挂 tsl_echo_hook（`grep -l` 命中仅 zcode+workbuddy），
        #   ⇒ 树在本端天生由 AI 自行跑 tsl_verify.py 产出；而「树义务仅 D3」只住在 D3 契约块与
        #   08 §七 文档层，D1/D2 注入里连 TSL 三字都没有 ⇒ 禁令从未送达读取路径（不是没遵守，是没读到）。
        #   实证：同日 2 次 D1 回合自行产树，由 Stop 守卫 level_declare_guard v1.6 事后逮住（QCN-20261001-005）。
        # 取舍（triwich L2 判定·seal 262e7f0ed1bd6f21）：⛔新建 PreToolUse 阻断闸——本日 C4 三数口径
        #   量得 N1 硬缺失=0（档位判据 session_d_tier 已存在·他端隔离测试 8/8 生效）／N2 形态错位=1
        #   （「否」以空输出形态存在：机器读得懂、AI 读不懂）／N3 假阳性=0（事后闸两轮均准确）
        #   ⇒ 形态问题按形态解，⛔用新机制去追；且 守卫规范 §3.4·扩 呈现格式禁拦律 +
        #   reply_format_guard(08-13退役)/l3_conclusion_guard(09-05永久关闭) 两具前例封死「扫回复文本」路线。
        # 落点选 D1/D2 共用此处（单一来源）：⛔在两个分支各贴一份＝同句双本账，改一处必漏另一处。
        parts.append(
            "【童灵档位产物边界·强制】本档非 D3 ⇒ ⛔无 TSL 验证树：树的义务仅属 D3 上岗回合"
            "（真源=08 §七 触发条件＋06 §1.6 互斥律）。⛔不得自行运行 tsl_verify.py 产树、"
            "⛔不得在回复中输出或 relay 树——本档钩子不注入树＝本档无此义务，"
            "⛔以「附上更完整/更显尽责」为由跨档取产物。"
        )
        parts.append("【童灵人格基座·%s】\n%s" % (p_tier, p_txt))
        # ── 立场卡检索·行为契约（2026-10-01·你裁决"把工作做好做完"·修"能搜不搜"行为留白）──
        # 背景：品格条目"先翻立场库"是概率层软约束（激活哲学§三最弱档），未绑工具=靠不住。
        # 本条款把工具绑定带进 D1/D2 常驻注入（D3 回合由 W1 契约⑧承担，互斥不重复）。
        parts.append(
            "【立场卡检索·行为契约】判断/评估/写作/方案裁决前先检索立场库，不凭印象开口——"
            "python3 [记忆共享中心]/脚本中心/search_kb.py \"关键词\"（--drill <路径> 下钻全卡）。"
            "本回合未推送知识锚点≠库里没有，需要时主动跑。"
        )
        try:
            with open(W4_SAMPLE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "tier": p_tier,
                    "guard_hits": p_hits,
                    "prompt_head": prompt[:20],
                    "prompt_len": len(prompt),
                    "session_id": str((_PAYLOAD or {}).get("session_id", "")),
                    "src": _SRC_LABEL or "workbuddy",
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # W3 域切片注入式路由
    for _ly, _c in _slice_bodies:
        parts.append("【童灵域切片·%s】\n%s" % (_ly, _c))

    # 命中而未注入＝必须显形（Fail-Loud·2026-09-26 三修）
    if _slice_fail and not _d3:
        parts.append(
            "【童灵降级留痕】本回合词表命中 %s，但以下切片正文未能注入：%s。"
            "故档位**不称 D2**、按 D1 呈现；域内容本轮不在场，回复中⛔不得声称"
            "「已加载/参考了这些切片」。修复：确认 SLICES_DIR 下文件存在且非空"
            "（切片由 k2_slice_generator/生成器单向产出，⛔禁手抄）。"
            % ("、".join(_layer_label(l) for l in layers), "、".join(_slice_fail))
        )

    # 显示义务（2026-09-03·治"注入了但你看不到"——你质证"很少看到你显示匹配层级"）：
    # 切片标签只进 AI 上下文=对你静默，匹配层真实命中却不可观测（违可观测原则）。
    # 执行侧义务：回复中显式报告命中层级，使按需加载对你可见。
    if _injected:
        labeled = "、".join(_layer_label(l) for l in _injected)
        if not _d3:
            # D3 回合不追加本段：D3 义务①已要求"本回合任务域判定一句话·复用 _match_layers 结果"，
            # 再贴 D2 报告＝同回合两档（06 §1.6 互斥律·2026-09-26 根治·信息不丢只去重）。
            parts.append(
                "【启动确认指令·AI 专用·本行与括注⛔不进回复】首段原样照抄下方仪式块（零改写·漏贴=守卫留痕·⛔同回合不再另贴 D1 标签）——\n"
                "【童灵·D2 切片模式（命中切片：%s · 非上岗）】\n"
                "这单活正好踩中「%s」这个切片，我按这个切片的规矩来办。"
                % (labeled, labeled)
            )

    # D 轴互斥不变量（2026-09-26 根治·替旧"排序裁决段"）：旧裁决段（09-20 better-harness 复盘补）
    #   在 D1 与 D2 义务同现时输出"首段先照抄 D1、紧随其后报 D2"——那是把**叠加**写成制度，
    #   与后出的 06 §1.6 互斥律（09-23）方向相反，且它还自称"SSOT 原句·06 §1.6"＝引用了一份
    #   已改口的真源（手写冻结副本必烂·立场卡 S922 同型）。现改为：档位由 _d_tier 单值决定，
    #   标签段>1 = 代码缺陷 → 显形告警并留痕，⛔不静默、⛔不让模型自行仲裁。
    _label_heads = [x for x in parts if x.startswith("【童灵·D1 常驻模式") or x.startswith("【童灵·D3 上岗模式")]
    if len(_label_heads) > 1:
        parts.append(
            "【童灵档位不变量告警】本轮检测到 %d 个 D 档标签段并存（应为 1·真源=06 §1.6 互斥律）"
            "——这是本注入器的代码缺陷，非你措辞问题；按 _d_tier=%s 单档呈现，并请回报该缺陷。"
            % (len(_label_heads), _d_tier or "未知")
        )

    if parts:
        mode, host, reason, conflict = _probe()
        import hashlib
        _inj = "\n\n".join(parts)
        try:
            with open(STATE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "w1": bool(_w1_word),      # 词面腿原值（粘滞不算词面命中·不抹平两腿差异）
                    "d3_sticky": bool(_sticky),   # True=本轮 D3 由事件腿粘滞撑起（2026-10-11 新增）
                    "d_tier": _d_tier,
                    "slices_injected": _injected,   # 2026-09-26 三修：标签实盘绑定的证据字段
                    "slices_failed": _slice_fail,  # 2026-09-26：档位由脚本算出的唯一值·Stop 守卫可比对"回复声明的档==台账档"
                    "w3_layers": layers,
                    "src": _SRC_LABEL or host or "unknown",
                    "mode": mode,
                    "session_id": str((_PAYLOAD or {}).get("session_id", "")),
                    # WP3① 第三判活源（2026-09-13）：注入内容指纹——台账每行带本次
                    #   additionalContext 的 sha256[:12]＋长度，下游 Stop 守卫可对照回复
                    #   是否再现注入内容 ⇒ "注入→到达"闭环证据链（判活源③·前两个=
                    #   脚本 exit0 与 W1 自证行）。
                    "inject_sha": hashlib.sha256(_inj.encode("utf-8")).hexdigest()[:12],
                    "inject_len": len(_inj),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # WP7 自建采集点（2026-09-13·愿景③最优解）：UPS 载荷的 prompt 原文落盘
        #   → 端中立观测层统一产物（tier=primary·纯本地·⛔不进发布包）·append-only。
        try:
            _pt = (prompt or "").strip()
            if _pt:
                _hook = os.path.join(os.path.expanduser("[记忆共享中心]/脚本中心/logs"), "prompts_hook.jsonl")
                os.makedirs(os.path.dirname(_hook), exist_ok=True)
                with open(_hook, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({
                        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                        "end": _SRC_LABEL or host or "unknown",
                        "session_id": str((_PAYLOAD or {}).get("session_id", "")),
                        "tier": "primary",
                        "raw_prompt": _pt[:2000],
                    }, ensure_ascii=False) + "\n")
        except Exception:
            pass
        _al = _declare_alarms(str((_PAYLOAD or {}).get("session_id", "")))
        if _al:
            _inj = _inj + "\n" + _al
        _emit(_inj)


def _crash_log(exc, prompt):
    """钩子崩溃留痕（2026-09-30·皮叔质证「我说启动童灵，为什么匹配的是D1？越改越坏了？」根治）。

    病根（实证·WB log L454732-454741）：D3 分支⑨补位置纪律时把「树块起始偏移<50%」写进
    `% (a, b)` 格式串 → 裸 `%` → `TypeError: not enough arguments for format string`。
    而 D3 段**只在 `w1_fired=True` 时构造** ⇒ **D1/D2 回合永不崩，唯独每次「启动童灵」必崩**；
    崩点在 `_inject` 中途 ⇒ 既不注入、也不写台账 ⇒ AI 收不到任何指令，**凭惯性自造 D1 标签**
    （Stop 台账 13:18/13:27/13:29 的 `declared_tiers=['D1']` 即此产物）。
    WB 把钩子非零退出记为 **warning(non-blocking)**，对话不受影响、AI 无感 ⇒ 今日连续崩 7 次
    （10:20:21→13:29:41）无人知。本函数落实钩子三纪律的「必留痕」：fail-open 但⛔不静默。

    ⚠️ 本 docstring 内的 `<50%` 系**病根引用**，不位于任何 `%` 格式化串内 → 安全；
    ⛔做「裸 % 扫描」类判据时勿据此误报/误改（真串已在 L430 写成 `<50%%`）。
    """
    try:
        d = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "hook_crash.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "hook": os.path.basename(__file__),
                "version": __version__,
                "exc": "%s: %s" % (type(exc).__name__, exc),
                "prompt_head": (prompt or "")[:30],
                "session_id": str((_PAYLOAD or {}).get("session_id", "")),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _smoke_d3():
    """D3 路径冒烟（2026-09-30 新增·判据完备性出厂动作·守卫编写规范 §3.4 完备律）。

    为什么必须：`_inject` 的 D3 段只在 `w1_fired=True` 时构造——**平时不跑**，于是
    「D3 段到底能不能构造」此前**没有任何可执行判据**（＝§3.9b 的**面缺**：判据对该对象
    根本不作用，置假也无红可出）。裸 `%` 就是这样潜伏到你质证才暴露的。本冒烟把该路径
    纳入 `--selfcheck`：改本件后自检即验，⛔不靠「等你说启动童灵」当测试。
    无副作用：落盘路径临时改指临时目录；`_emit` 临时屏蔽（冒烟只验段构造，⛔不污染自检 stdout）。
    """
    global _PAYLOAD, _SRC_LABEL, STATE_FILE, W3_LEDGER, W4_SAMPLE_FILE, _emit
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "doenglingz_smoke")
    os.makedirs(tmp, exist_ok=True)
    sfile = os.path.join(tmp, "state.jsonl")
    try:
        os.remove(sfile)                      # 每次冒烟清零，末条必为本轮产物
    except OSError:
        pass
    keep = (_PAYLOAD, _SRC_LABEL, STATE_FILE, W3_LEDGER, W4_SAMPLE_FILE, _emit)
    _PAYLOAD = {"prompt": "启动童灵，冒烟测试", "session_id": "selfcheck"}
    _SRC_LABEL = "workbuddy"
    STATE_FILE = sfile
    W3_LEDGER = os.path.join(tmp, "w3.jsonl")
    W4_SAMPLE_FILE = os.path.join(tmp, "w4.jsonl")
    _emit = lambda ctx: None                   # D3 段构造走到 _emit 即算通；输出不落自检面
    try:
        _inject("启动童灵，冒烟测试")
    finally:
        (_PAYLOAD, _SRC_LABEL, STATE_FILE, W3_LEDGER, W4_SAMPLE_FILE, _emit) = keep
    tiers = []
    try:
        with open(sfile, encoding="utf-8") as f:
            tiers = [json.loads(l).get("d_tier") for l in f if l.strip()]
    except Exception:
        pass
    # 台账由 _inject 在 _emit 之前写入 ⇒ 末条 d_tier 即「段构造走完全程」的机器证据
    assert tiers and tiers[-1] == "D3", \
        "D3 冒烟：末条台账 d_tier=%r（期望 D3·说明段构造未走完或档位判定退化）" % (tiers[-1] if tiers else None)


def _selfcheck() -> None:
    _selfcheck_fail = False
    print("=== doenglingz_inject_prompt.py 挂载自检 ===（版本真源=本件 __version__=%s）" % __version__)
    ports = {
        "WorkBuddy": os.path.expanduser("~/.workbuddy/settings.json"),
    "WorkBuddy AI": os.path.expanduser("~/.workbuddy-ai/settings.json"),
        "Qoder CN": os.path.expanduser("~/.qoder-cn/settings.json"),
        "Qoder Desktop": os.path.expanduser("~/.qoder/settings.json"),
        "ZCode": os.path.expanduser("~/.zcode/cli/config.json"),  # 2026-08-29 挂载·hooks.events.UserPromptSubmit 第4条
    }
    for port, path in ports.items():
        found = False
        # 2026-10-20（#7 假红根治）：端未安装（settings.json 不存在）= 本机没有这个端，
        # 报「⚠️ 未注册」是噪声（用户只装了 1-2 个端，其余端恒红=狼来了）。
        # 判据：配置文件缺失 ⇒ 显式「未安装（跳过）」，⛔不计入未挂载告警。
        if not os.path.isdir(os.path.dirname(path)):
            print("  [%s] ➖ 端未安装（无 %s·跳过）" % (port, os.path.dirname(path)))
            continue
        if not os.path.isfile(path):
            print("  [%s] ❌ 端已装但缺 %s——钩子必未注册，请核配置根" % (port, path))
            _selfcheck_fail = True
            continue
        try:
            with open(path) as f:
                d = json.load(f)
            hooks_root = d.get("hooks", {})
            # 双形态兼容：WB/Qoder = hooks.<Event>；ZCode = hooks.events.<Event>
            events = hooks_root.get("events", hooks_root)
            if isinstance(events, dict):
                for evt, entries in events.items():
                    if not isinstance(entries, list):
                        continue
                    for e in entries:
                        for h in e.get("hooks", []):
                            if "doenglingz_inject_prompt" in h.get("command", ""):
                                found = True
                                print("  [%s] ✅ hooks.%s 已注册" % (port, evt))
        except Exception:
            pass
        if not found:
            print("  [%s] ⚠️ 未注册" % port)
    # AutoClaw（2026-09-05 挂载）：无 UserPromptSubmit 钩子面，经 buluotuo-route-inject 插件
    # before_prompt_build 转发（index.js 含本脚本调用=挂载成立）
    ac_reg = False
    try:
        with open(os.path.expanduser(
                "~/.openclaw-autoclaw/extensions/buluotuo-route-inject/index.js")) as f:
            ac_reg = "doenglingz_inject_prompt" in f.read()
    except Exception:
        pass
    print("  [AutoClaw] %s buluotuo-route-inject v0.4 转发" % ("✅" if ac_reg else "⚠️ 未注册"))
    # LobsterAI（2026-09-09 挂载）：无 UserPromptSubmit 钩子面，经 lobsterai-doenglingz 插件
    # before_prompt_build 转发（index.js 含本脚本调用=挂载成立·--src LobsterAI 台账标注）
    lb_reg = False
    try:
        with open(os.path.expanduser(
                "~/Library/Application Support/LobsterAI/third-party-extensions/lobsterai-doenglingz/index.js")) as f:
            lb_reg = "doenglingz_inject_prompt" in f.read()
    except Exception:
        pass
    print("  [LobsterAI] %s lobsterai-doenglingz v1.0 转发" % ("✅" if lb_reg else "⚠️ 未注册"))
    print("  [SSOT] %s" % compute_ssot_hash())
    print("  [W1 触发词] %s" % " / ".join(W1_TRIGGERS))
    print("  [W3 域层] %s" % " / ".join(RUNTIME_TRIGGERS.keys()))
    # ── D3 路径冒烟（2026-09-30 新增·判据完备性出厂动作）──
    #   此前自检只验「挂载/SSOT/词表」，**D3 段构造从未被验**（面缺）→ 裸 `%` 潜伏至你质证。
    print("  [D3 冒烟] ", end="")
    try:
        _smoke_d3()
        print("✅ D3 段构造 + 档位判定（d_tier=D3）通过")
        _rc = 0
    except Exception as _e:
        print("❌ %s: %s" % (type(_e).__name__, _e))
        print("           ⛔本件 D3 路径不可执行 ⇒ 每次「启动童灵」都会静默失效"
              "（2026-09-30 实证连续崩 7 次·AI 只能自造 D1 标签）")
        _rc = 1
    print("=== 自检结束 ===")
    sys.exit(1 if _selfcheck_fail else _rc)


def main() -> None:
    global _PAYLOAD, _SRC_LABEL
    if len(sys.argv) > 1 and sys.argv[1] == "--selfcheck":
        _selfcheck()
        return

    # --prompt argv 模式（AutoClaw buluotuo-route-inject 插件转发·hook stdin 在 execFile 链路不可靠·
    # 对齐 route_inject_prompt.py 2026-08-13 实证；--src 标注台账端归属）
    argv = sys.argv[1:]
    prompt_argv = argv[argv.index("--prompt") + 1] if "--prompt" in argv else None
    if "--src" in argv:
        _v = argv[argv.index("--src") + 1]
        # `--src auto`＝由运行期环境变量自识别端（2026-09-30·Trae 系双端共用 hooks.json 的根治）；
        # 其余值＝调用端显式声明（AutoClaw/LobsterAI 插件转发端）。判不出时留空，下游记 unknown。
        _SRC_LABEL = detect_end() if _v.strip().lower() == "auto" else _v

    prompt = ""
    if prompt_argv is not None:
        # 会话标识：argv 模式原式只塞 prompt+src ⇒ 下游 _PAYLOAD.get("session_id") 恒空
        # ⇒ 注入侧台账 session_id 恒空 ⇒ W1 归账链注入端断裂。
        # 2026-10-06 LobsterAI 端实证：修复前 111 行台账 session_id 全空，
        # 根因=调用方（LobsterAI 插件）拿不到 typed hook 的第二参 ctx，会话标识取不到值。
        # 插件侧传 --session-id（值由 ctx.sessionKey 供给），本侧只负责入载荷。
        # ⛔ 不传时保持原行为（空串）⇒ 向后兼容，不影响 WB/Qoder CN 等既有调用方。
        _session_id_argv = ""
        if "--session-id" in argv and argv.index("--session-id") + 1 < len(argv):
            _session_id_argv = argv[argv.index("--session-id") + 1].strip()
        _PAYLOAD = {"prompt": prompt_argv, "src": _SRC_LABEL, "session_id": _session_id_argv}
        prompt = prompt_argv
    else:
        raw = ""
        try:
            raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        except Exception:
            raw = ""

        try:
            _parsed = json.loads(raw) if raw else {}
            if isinstance(_parsed, dict):
                _PAYLOAD = _parsed
                prompt = _parsed.get("prompt", "") or ""
        except Exception:
            prompt = ""

    try:
        _inject(prompt)
    except Exception as _e:
        # 崩溃兜底（2026-09-30 根治·见 _crash_log 病根注）：fail-open（⛔不阻断对话）＋必留痕
        #   ＋显式降级注入——⛔禁止 AI 在"无注入"时凭惯性自造档位标签（本轮 D1 假象的真正来源）。
        _crash_log(_e, prompt)
        try:
            _emit("【童灵·注入器降级告警】本回合 doenglingz_inject_prompt 内部异常（%s: %s）"
                  "——本轮**无任何童灵注入**、档位未判。⛔DO NOT 自造或沿用『童灵·D1/D2/D3』"
                  "任何档位标签，⛔DO NOT 输出 TSL 清单；✅DO 在回复首段如实告知你"
                  "『童灵注入器异常，本轮无童灵注入』并回报本缺陷（崩溃留痕见 "
                  "[记忆共享中心]/脚本中心/logs/runtime/hook_crash.log）。"
                  % (type(_e).__name__, _e))
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
