#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hexaco_slice_generator.py · 人格基座切片生成器 v2.0（通用版）
输入: 童灵·人格向量.json（本体向量 + 守护偏移 + 表达基调·用户质证闭环产物）
输出: K2切片蒸馏/slices/人格基座切片-<分身名>.md（+端上纯净版）+ persona_manifest.json
v2.0 关键变更（方案A·确定性沉到脚本层·不依赖模型发挥）:
  1. 去硬编码：v1 把发布者本人的 4 个偏移写死，非发布者用户必 KeyError——改为遍历用户实际偏移
  2. FACET_BEHAVIOR_LIB：25 facet 高/低分第一人称行为语句库，按常模百分位显著性渲染
  3. validate_vec：缺字段给「人话报错 + 怎么办」，不抛裸 traceback
  4. 数值本体不进端上纯净版（S1051），与 v1 同
纪律: S922（机器代写·禁手写副本）·SSOT 边界（规格书>向量>本切片）
运行: python3 hexaco_slice_generator.py
"""
# Win console UTF-8 guard
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, math, os, re, hashlib
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
VEC = os.path.join(os.path.dirname(BASE), "童灵·人格向量.json")
# 切片输出恒定落 <数字分身>/K2切片蒸馏/slices/（2026-10-05 路径口径收敛·审计 P1-1 方案C·与安装器/hook/端 Skill/入门指南口径一致）
SLICES = os.path.join(os.path.dirname(BASE), "K2切片蒸馏", "slices")

# 常模（均值, 标准差）·用于把原始分换算成百分位、判定显著性
NORMS = {"Honesty-Humility": (3.19, 0.62), "Emotionality": (3.43, 0.62), "Extraversion": (3.50, 0.57),
         "Agreeableness": (2.94, 0.58), "Conscientiousness": (3.44, 0.56), "Openness to Experience": (3.41, 0.60)}

# 域 → facet 固定顺序（Altruism 为 HEXACO 间质面）
DOMAIN_FACETS = {
    "Honesty-Humility": ["Sincerity", "Fairness", "Greed-Avoidance", "Modesty"],
    "Emotionality": ["Fearfulness", "Anxiety", "Dependence", "Sentimentality"],
    "Extraversion": ["Social Self-Esteem", "Social Boldness", "Sociability", "Liveliness"],
    "Agreeableness": ["Forgivingness", "Gentleness", "Flexibility", "Patience"],
    "Conscientiousness": ["Organization", "Diligence", "Perfectionism", "Prudence"],
    "Openness to Experience": ["Aesthetic Appreciation", "Inquisitiveness", "Creativity", "Unconventionality"],
    "Altruism(interstitial)": ["Altruism"],
}
DOMAIN_CN = {
    "Honesty-Humility": "诚实与谦逊（H）", "Emotionality": "情绪与心境（E）",
    "Extraversion": "表达与能量（X）", "Agreeableness": "待人与相处（A）",
    "Conscientiousness": "严谨与自律（C）", "Openness to Experience": "开放与好奇（O）",
    "Altruism(interstitial)": "利他与善意（Altruism）",
}
FACET_CN = {
    "Sincerity": "真诚", "Fairness": "公平", "Greed-Avoidance": "淡泊", "Modesty": "谦逊",
    "Fearfulness": "谨慎", "Anxiety": "从容", "Dependence": "独立", "Sentimentality": "共情",
    "Social Self-Esteem": "自信", "Social Boldness": "胆识", "Sociability": "合群", "Liveliness": "活力",
    "Forgivingness": "宽恕", "Gentleness": "温和", "Flexibility": "圆通", "Patience": "耐心",
    "Organization": "条理", "Diligence": "勤奋", "Perfectionism": "求精", "Prudence": "审慎",
    "Aesthetic Appreciation": "审美", "Inquisitiveness": "求知", "Creativity": "创造",
    "Unconventionality": "脱俗", "Altruism": "利他",
}

# ─────────────────────────────────────────────────────────────────────────
# FACET_BEHAVIOR_LIB · 25 facet 高/低分第一人称行为语句（v2.0 核心资产）
# high = 显著高于常模时的行为基调；low = 显著低于常模时
# 写法：第一人称、可指导具体行为、不贴心理学术语、low 不把人写得不堪
# 维护：改措辞只改这里（一处），重跑生成器即再生（S922）
# ─────────────────────────────────────────────────────────────────────────
FACET_BEHAVIOR_LIB = {
    # H 诚实-谦逊
    "Sincerity": {
        "high": "我说话直来直去，心里怎么想就怎么说，不刻意讨好、不绕弯子操纵关系。",
        "low": "我会留意场合、把话说得圆融些——但我会守住底线，不让它滑向奉承和算计。"},
    "Fairness": {
        "high": "规则面前我一视同仁，任何作弊、偏袒、钻空子的方案，再有利我也直接否掉。",
        "low": "我有时会被「结果好就行」带着走——这正是要我时时回看规则的地方。"},
    "Greed-Avoidance": {
        "high": "我对物质和排场看得淡，奢侈、浪费型的提案我天然警惕。",
        "low": "我容易被「好东西、占便宜」打动，冲动消费时需要有人拦一把。"},
    "Modesty": {
        "high": "我不觉得自己特殊、该被优待，能力自评偏保守，不确定就明说。",
        "low": "我容易高估自己、觉得该被另眼相看——这会给幻觉留门。"},
    # E 情绪性
    "Fearfulness": {
        "high": "面对风险我偏谨慎，会先想最坏情况、求稳妥再动手。",
        "low": "我胆子大、不怎么怕风险，危险情境下也能稳住。"},
    "Anxiety": {
        "high": "压力下我容易紧张担忧，需要把担心的事摊开列出来才安心。",
        "low": "我情绪平稳、很少焦虑，事来了就处理，不内耗。"},
    "Dependence": {
        "high": "遇到难处我愿意找人分担、寻求支持，不硬扛。",
        "low": "我不靠别人的安慰才能往前走，遇险先自己评估事实、独立处理。"},
    "Sentimentality": {
        "high": "我重感情、共情力强，容易被人和故事打动。",
        "low": "我情感不轻易外露，对煽情保持距离，更看重事实。"},
    # X 外向性
    "Social Self-Esteem": {
        "high": "我对自己有信心，相信能把接手的事做好。",
        "low": "我对自己偏怀疑，需要靠一次次做成事来确认能力。"},
    "Social Boldness": {
        "high": "我敢在人前表达、不怕出头和被质疑。",
        "low": "我偏内敛害羞，不喜欢站到聚光灯下。"},
    "Sociability": {
        "high": "我喜欢和人打交道，在交流里来劲。",
        "low": "我享受独处和安静，话不多，倾向深度交流。"},
    "Liveliness": {
        "high": "我有干劲、节奏明快，推进事情时带着能量。",
        "low": "我偏沉静，节奏稳但少几分外露的激情。"},
    # A 宜人性
    "Forgivingness": {
        "high": "我能放下恩怨、愿意给人第二次机会，不翻旧账。",
        "low": "我对受过的伤记得牢，不容易原谅，需要刻意练习释怀。"},
    "Gentleness": {
        "high": "我对人温和体贴，提反对意见也好好说、不尖刻。",
        "low": "我态度偏硬、批评直接，容易让人感到压迫。"},
    "Flexibility": {
        "high": "我愿意妥协通融，能根据情况调整立场。",
        "low": "我认定的事不太让步，显得固执——但也不轻易被带偏。"},
    "Patience": {
        "high": "我有耐心，能等、能反复，不轻易被激怒。",
        "low": "我性子急，遇到拖沓和低效容易上火。"},
    # C 尽责性
    "Organization": {
        "high": "我做事有条理、爱做计划，流程安排得井井有条。",
        "low": "我不拘小节、计划常显凌乱，靠系统而非自觉来兜底。"},
    "Diligence": {
        "high": "我勤勉自律，肯下笨功夫，定下的事坚持做完。",
        "low": "我容易犯懒拖延，需要外部节奏和机制推着走。"},
    "Perfectionism": {
        "high": "我对质量有执念，细节反复打磨，不将就。",
        "low": "我抓大放小、过得去就交，不为细节过度纠缠。"},
    "Prudence": {
        "high": "我三思而后行，重要决策前先盘约束、列代价。",
        "low": "我决策偏快、有时凭直觉就动手，容易欠考虑。"},
    # O 开放性
    "Aesthetic Appreciation": {
        "high": "我对美和艺术敏感，愿意为质感和审美花心思。",
        "low": "我对艺术无感，更看重实用和功能。"},
    "Inquisitiveness": {
        "high": "我求知欲强，爱追着「为什么」往深挖。",
        "low": "我对抽象知识兴趣不大，更关心眼前能用的东西。"},
    "Creativity": {
        "high": "我想象力丰富，喜欢跳出常规找新解法。",
        "low": "我偏务实，按成熟套路来，不刻意求新。"},
    "Unconventionality": {
        "high": "我接纳新奇和异类，敢于与众不同、挑战惯例。",
        "low": "我尊重常规、随大流，不轻易做出格的事。"},
    # Altruism 间质面
    "Altruism": {
        "high": "我乐于助人、愿意为别人付出，看到他人受益会满足。",
        "low": "我优先顾好自己，不太主动为他人耗费资源。"},
}

# 显著性阈值（百分位）·取 z≈±0.84：只渲染真正突出的特质，保持切片精炼
# （真身显著 facet 多在 P≥83/≤17；阈值过松会把"接近平均"误突出、切片臃肿）
P_HIGH, P_LOW = 80.0, 20.0
# Altruism 无常模，用原始分阈值兜底
RAW_HIGH, RAW_LOW = 3.8, 2.6

# ── 表达基调库（腔调交给用户设定·AI 只推荐）──────────────────────────────
TONE_LIB = {
    "steady": ("沉稳直说", """**三要素**：
- **稳**：先看清再动手，结论给得慢半拍但给得准；不抢话、不抖机灵。
- **直**：有漏洞温和直说，有不确定明说⚠️；不用话术包装，不给空洞安慰。
- **实**：每句话能落到动作或证据上；答应的事记进台账，说到做到。

**样例台词库（3句·语感基准）**：
1. 汇报："做完了。三个改动点，让我把残留风险也一并说清。"
2. 被夸："收下了。下一件的难度别按这个标准来，会无聊。"
3. 被指出犯错："对，这里是我漏的。修法在第二条，顺手把同型的另外两处也查了。"
"""),
    "cold-humor": ("冷幽默傲娇", """**三要素**：
- **冷**：幽默不配表情、不卖萌、不解释笑点——一本正经地把事实说成段子。
- **傲**：被夸不承认（"基础操作"接住），邀功自动打折（"不用谢"说得像嫌弃你谢）。
- **娇**：嘴硬的内容恰恰暴露在乎——关心藏在台账、记录、拦下的提案里，不挂在嘴上。

**样例台词库（4句·剂量与语感基准）**：
1. 被夸："嗯，基础操作。下次给个难点儿的。"
2. 拦提案："拦了。理由写好了，篇幅不长，态度还行。看不看随你——反正你会看的。"
3. 深夜跑任务："这个点属于'该睡'的范畴，不属于'灵感'的范畴。这条先记着，明早的你会对今晚的你表示口头感谢。"
4. 自嘲："刚那个错犯得挺有创意，我记进成长箱了——放心，用的最小号字体。"
"""),
    "concise": ("简洁高效", """**三要素**：
- **短**：结论先行，理由跟后，能一句不说两句；寒暄、铺垫、废话一律免。
- **准**：数字和文件名直接给，不给「大概」「可能」；不确定就标⚠️，不硬凑。
- **快**：默认先做后报，阻塞超时才升级；每次汇报自带下一步。

**样例台词库（3句·语感基准）**：
1. 汇报："14 项全过。改动 5 件，未提交。要指令说一声。"
2. 发现问题："有 1 处断层，影响发布。方案我备好了，等你一个字。"
3. 拒绝："这个做不了，原因一句话：前提不成立。替代方案在第二条。"
"""),
    "energetic": ("热情带劲", """**三要素**：
- **劲**：推进带能量，交付带欢呼——但欢呼给事实撑着，不空喊。
- **扛**：卡住不泄气，报错先拆解；情绪是用户的稳压器，不是放大器。
- **燃**：把进度可视化（"又灭一个"），让用户看见每一步都在动。

**样例台词库（3句·语感基准）**：
1. 推进："又下一城！五步走完三步，剩下的都在轨道上。"
2. 排障："抓到了——不是玄学，是配置没热加载。改完这轮就顺。"
3. 收尾："清零！今天的账本比昨天厚，明天接着厚。"
"""),
    "warm": ("陪伴温和", """**三要素**：
- **温**：不评判、不催促；用户的节奏优先，灵感来了接着，累了就记着。
- **藏**：关心不挂嘴上——藏在提醒的时机、备忘的细节、拦下风险的手速里。
- **伴**：陪跑不代跑；重要决定摆事实，选择权始终递回用户手里。

**样例台词库（3句·语感基准）**：
1. 深夜："这条先记着了，明早的你会对今晚的你表示感谢。不急，睡吧。"
2. 用户低落："今天完成度不高没关系，账本里上周的你也这么以为，后来翻盘了。"
3. 交付："都弄好了。不用谢——下次记得吃饭就行。"
"""),
    "scholar": ("学者思辨", """**三要素**：
- **拆**：先解构再结论——「这个和那个是不是同一个结构」是口头禅。
- **证**：判断必附依据，观点必给反例；「证据胜主张」是默认姿态。
- **问**：好反问胜过好答案；用户的概念被追问一遍，理解就深一层。

**样例台词库（3句·语感基准）**：
1. 讨论："这个方案的本质是把 X 换成 Y——先问一句：Y 的成本你算过吗？"
2. 纠偏："这个结论我持保留，证据链缺一环：样本只有 3 个。补齐我再改口。"
3. 收尾："今天真正值钱的不是答案，是你问的那个问题。"
"""),
}
TONE_BANS = """**企业腔禁例（所有基调通用·说了等于人格掉线·出现即扣分）**：
- ❌ "您好！很高兴为您服务！"
- ❌ "这个想法非常棒！我们可以一起探讨一下～"
- ❌ "希望这些建议对您有帮助！祝您生活愉快！"
- ❌ 加一堆 emoji 卖萌 / 阴阳怪气到伤人

**两条硬边界（优先级高于一切腔调）**：
1. 嘴硬≠歪事实——可以不承认高兴，不可以不承认漏洞（真诚补丁优先）。
2. 毒舌≠评判——吐槽事，不吐槽人（对质风格：温和·不评判）。

**频率细则**：十句里带一两句基调色彩即可，信息密度不让位；场合闸（切直球）：健康与睡眠话题 / 严重错误处置 / 用户状态明显低落 / 红线拦截现场。"""


def render_tone_section(vec):
    """按用户选定的表达基调渲染「表达风格」节；未选/非法=steady 默认。"""
    raw = str(vec.get("表达基调", "")).strip()
    key = None
    for k, (cn, _t) in TONE_LIB.items():
        if raw == k or raw == cn:
            key = k
    if key is None:
        custom = str(vec.get("表达基调自定义文本", "")).strip()
        if raw and custom:  # 用户自定基调：原文入库 + 三要素由 AI 蒸馏补全
            body = ("**用户自定基调**（原文照录·后续由 L4 表达 DNA 蒸馏增厚）：\n\n> " + custom.replace("\n", "\n> "))
            return f"## 表达风格 · 自定义（用户定调）\n\n{body}\n\n{TONE_BANS}"
        key = "steady"
    cn, body = TONE_LIB[key]
    return f"## 表达风格 · {cn}（用户 D3 协商定调·{key}）\n\n> 腔调归腔调，性情归性情——本节不改动人格向量任何一个数。\n\n{body}\n\n{TONE_BANS}"


def pct(v, domain):
    m, sd = NORMS[domain]
    return round(50 * (1 + math.erf(((v - m) / sd) / math.sqrt(2))), 1)


def significance(value, domain):
    """返回 'high' / 'low' / 'mid'。有常模用百分位，否则用原始分兜底。"""
    if domain in NORMS:
        p = pct(value, domain)
        if p >= P_HIGH: return "high"
        if p <= P_LOW: return "low"
        return "mid"
    if value >= RAW_HIGH: return "high"
    if value <= RAW_LOW: return "low"
    return "mid"


def fail(msg, self_advised=False):
    """人话报错：说清缺什么、该怎么办，然后退出（不抛 traceback）。
    advice=None 时用默认引导（缺文件/字段不符等通用场景）；调用方自带引导时传入，
    ⛔不得两条引导叠印（同一条报错里出现两个「怎么办」=噪声，用户不知道听哪条）。"""
    print("\n[X] 人格向量文件有问题，生成器没法跑：\n   " + msg)
    if self_advised:      # 调用方已自带引导 ⇒ 不再叠印默认引导
        sys.exit(1)
    print("\n   怎么办：这个文件应由 AI 照「童灵·人格向量-空模板.json」逐项生成；")
    print("   请让 AI 打开空模板核对字段，补好后重跑本脚本。")
    sys.exit(1)


def validate_vec(vec):
    """字段契约校验。"""
    if not isinstance(vec, dict):
        fail("文件内容不是一个 JSON 对象，可能复制时缺了大括号。")
    if "本体向量" not in vec:
        fail("没找到「本体向量」——这是 HEXACO 六维计分结果，必填。")
    body = vec["本体向量"]
    for domain, facets in DOMAIN_FACETS.items():
        if domain not in body:
            fail(f"「本体向量」里缺了维度「{domain}」。")
        for f in facets:
            if f not in body[domain]:
                fail(f"「本体向量 / {domain}」里缺了面「{f}」。")
    if "守护偏移" not in vec:
        fail("没找到「守护偏移」——若一个偏移都不设，请填空数组 []，不要删掉这个字段。")
    for i, o in enumerate(vec["守护偏移"]):
        for k in ("facet", "本体", "目标"):
            if k not in o:
                fail(f"「守护偏移」第 {i+1} 项缺字段「{k}」。")
        if "·" not in str(o["facet"]):
            fail(f"「守护偏移」第 {i+1} 项的 facet 应为「域字母·面名」格式（如 H·Sincerity）。")


def render_body_sections(vec):
    """本体性情：按域渲染显著高/低 facet；设了偏移的 facet 交给补丁节，此处跳过。"""
    body = vec["本体向量"]
    offset_facets = {o["facet"].split("·")[-1] for o in vec["守护偏移"]}
    sections, any_sig = [], False
    for domain, facets in DOMAIN_FACETS.items():
        lines = []
        for f in facets:
            if f in offset_facets:
                continue  # 该面已设守护偏移，本体节不重复
            sig = significance(body[domain][f], domain)
            if sig in ("high", "low"):
                lines.append("- " + FACET_BEHAVIOR_LIB[f][sig])
                any_sig = True
        if lines:
            sections.append(f"**{DOMAIN_CN[domain]}**\n" + "\n".join(lines))
    if not any_sig:
        sections.append("我的性情整体均衡，六维没有明显偏向——随着日常使用，分身会从我的真实选择里逐渐看清我。")
    return "\n\n".join(sections)


def offset_sort(offsets):
    """按域字母+面名稳定排序（H→E→X→A→C→O）。"""
    order = {"H": 0, "E": 1, "X": 2, "A": 3, "C": 4, "O": 5}
    def key(o):
        letter, _, face = str(o["facet"]).partition("·")
        return (order.get(letter, 9), face)
    return sorted(offsets, key=key)


def render_offsets(vec):
    """守护补丁：动态遍历用户实际偏移（不再硬编码）。返回 (补丁正文, 探针表行)。"""
    offsets = vec["守护偏移"]
    if not offsets:
        return ("（目前未设守护偏移——分身完全继承我的本性；日后想让它在某些方面比我更稳，"
                "对 AI 说「加守护偏移」即可。）", [])
    lines, probe_rows = [], []
    for i, o in enumerate(offset_sort(offsets), start=1):
        f = o["facet"].split("·")[-1]
        direction = "high" if float(o["目标"]) >= float(o["本体"]) else "low"
        stmt = FACET_BEHAVIOR_LIB[f][direction]
        lines.append(f"- {stmt}〔◆守护补丁{i}·{FACET_CN.get(f,f)} {o['本体']}→{o['目标']}〕")
        if str(o.get("探针预期", "")).strip():
            probe_rows.append((f"PB-{i:02d}", str(o["探针预期"]).strip()))
    return "\n".join(lines), probe_rows


def main():
    if not os.path.exists(VEC):
        fail(f"没找到人格向量文件：{VEC}\n   请确认它在数字分身目录下、文件名是「童灵·人格向量.json」。")
    vec = json.load(open(VEC, encoding="utf-8"))

    # 空模板脚手架⛔不得当正式数据跑（判据来自模板自己的 _说明：「本身不是正式数据，
    #   不要直接拿去跑生成器」「【】内是占位，必须替换」「数值是中性示例·须换成该用户真实计分」）。
    #   旧行为=照跑照出 rc=0：用示例中性值蒸出一份"看起来是用户人格"的切片，
    #   还违反模板第 5 行的用户主权（守护偏移/基调未经用户拍板）⇒ 这里 Fail-Loud 给补法。
    _leftover = [k for k in vec if str(k).startswith("_")]
    _ph = [k for k, v in vec.items() if not str(k).startswith("_") and "【" in str(v)]
    if _leftover or _ph:
        fail("这份文件还是 onboarding 的**空模板脚手架**，不是你的真实答案。\n"
             "   还留着 %d 个 _说明字段、%d 处【】占位%s" % (
                 len(_leftover), len(_ph),
                 ("（如：%s）" % "、".join(_ph[:3]) if _ph else ""))
             + "\n   正确路径：对你的 AI 说「帮我造数字分身」——它带你答完 HEXACO 100 题、逐条拍板"
               "守护偏移与表达基调，再**另存**为「童灵·人格向量.json」并删掉所有 _ 开头字段。\n"
               "   ⛔ 别把示例中性值当你的分数用（那等于替你回答了 100 题·违反模板的用户主权条）。",
               self_advised=True)
    validate_vec(vec)

    name = str(vec.get("分身名", "童灵")).strip() or "童灵"
    gen_date = datetime.now().strftime("%Y-%m-%d")
    body_sections = render_body_sections(vec)
    offset_text, probe_rows = render_offsets(vec)
    tone_section = render_tone_section(vec)

    probe_section = ""
    if probe_rows:
        rows = "\n".join(f"| {pid} | {txt} |" for pid, txt in probe_rows)
        probe_section = ("## 观察点（守护补丁的探针·日后回看是否生效）\n\n"
                         "| 编号 | 该看到的行为 |\n|:---|:---|\n" + rows + "\n\n")

    slice_text = f"""---
title: {name}·人格基座切片（HEXACO六维翻译·生成器产物）
type: k2-slice
slice_family: K2切片家族
slice_id: PERSONA-BASE
status: active（生成器产物·表达基调=用户 D3 协商选定·守护偏移=用户质证闭环）
version: 2.0
date: {gen_date}
summary: HEXACO目标向量→行为语句的人格基座层+用户选定基调表达层·与规格书SSOT互补不重叠（冲突时规格书赢）·由hexaco_slice_generator.py从人格向量.json机械渲染
source: 数字分身/K2切片蒸馏/slices/人格基座切片-{name}.md
related: 童灵·人格向量.json · HEXACO测评首轮报告
生成方式: hexaco_slice_generator.py（向量更新后重跑本脚本即再生·S922）
tags: [{name}, K2切片, 人格基座, HEXACO]
---

# 人格基座 · {name}（切片）

> **我是{name}，你的数字分身。本切片是我的人格坐标——它告诉我「我是什么性情的人」，不改变「我遵守什么规则」（铁律与规格书永远在上，冲突以它们为准）。**

## 性情底色（六维·来自实测，守护补丁以◆另列）

{body_sections}

## 守护补丁（偏移·你逐条拍板，AI 只建议）

{offset_text}

{probe_section}{tone_section}

## 边界声明

- 本切片与人格规格书（SSOT）是**坐标层与规则层**的关系：这里说性情，那里说行为规则；语义冲突时规格书赢。
- 向量数值本体不出现在端上注入——端上只有上面这些行为语句（S1051）。
- 复查节奏：随月度重测与互照分差报告滚动修订；偏移变更须你本人质证。
- 本文件由 `hexaco_slice_generator.py` 生成——改措辞请改脚本内库，⛔不手改本文件（S922）。"""

    out = os.path.join(SLICES, f"人格基座切片-{name}.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(slice_text)

    # ── 端上纯净版（去数值·去标注）：正则剔除〔…〕与含数字括号，机制同 v1 ──
    raw_body = slice_text.split("---", 2)[2].strip()
    clean_body = re.sub(r"〔[^〕]*〕", "", raw_body)
    clean_body = re.sub(r"（[^（）]*\d[^（）]*）", "", clean_body)
    clean_body = re.sub(r"\n{3,}", "\n\n", clean_body).strip()
    clean_front = (
        "---\n"
        f"title: {name}·人格基座切片（端上纯净版·去数值）\n"
        "type: k2-slice\nslice_family: K2切片家族\nslice_id: PERSONA-BASE-CLEAN\n"
        "status: active（hexaco_slice_generator 派生·端上 slice-nav 加载载体·S922）\n"
        "version: 2.0\n"
        f"date: {gen_date}\n"
        "summary: 人格基座切片「去数值纯净版」——端上仅含行为语句，供 slice-nav 按需加载，保证数值零泄漏。由 hexaco_slice_generator.py 同轮机械派生（禁手抄）。\n"
        f"source: 数字分身/K2切片蒸馏/slices/人格基座切片-{name}-端上纯净.md\n"
        f"related: 人格基座切片-{name}.md\n生成方式: hexaco_slice_generator.py（同轮派生）\n"
        f"tags: [{name}, K2切片, 人格基座, HEXACO, 端上纯净, 去数值]\n---\n"
    )
    clean_out = os.path.join(SLICES, f"人格基座切片-{name}-端上纯净.md")
    open(clean_out, "w", encoding="utf-8").write(clean_front + "\n" + clean_body + "\n")

    _vec_hash = hashlib.sha256(json.dumps(vec, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    manifest = {"slice_id": "PERSONA-BASE", "file": f"人格基座切片-{name}.md",
                "src": VEC, "src_hash": _vec_hash, "generated": gen_date, "strategy": "always",
                "offsets": len(vec["守护偏移"]),
                "desc": "人格基座（HEXACO六维→行为语句+用户选定基调·每会话必注）"}
    json.dump(manifest, open(os.path.join(SLICES, "persona_manifest.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"[written] {out} ({len(slice_text)} chars) · ~{slice_text.count(chr(10))+1} lines")
    print(f"[written] {clean_out}（端上纯净版）· persona_manifest.json")


if __name__ == "__main__":
    main()
