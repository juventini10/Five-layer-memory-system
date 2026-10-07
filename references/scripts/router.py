"""P2 路由原型 v3：引号块 + 无引号列表触发词提取(高置信) + 语义标签散列匹配(兜底)
v1.4.1 (2026-08-16 · Phase 0 施工)：
  ① 负例泄漏修复：否定语境「X不触发（如"分析代码"…）」内引号负例不再进 trig（三明智 L3 复评实证）
  ② 引号残留清理：提取 token 去除首尾残留引号（'"三明治'/'主要矛盾"' 历史残留）
  ③ 匹配面过滤：系统消息/子代理消息直拒 + 本地绝对路径成分剥离（事故机制链：路径"待评估文案"→"评估"误命中）
v3.0.0 (2026-08-24 · 根治)：
  根因：原 route() 仅做引号短语「紧挨子串匹配」，自然语言把触发词拆开（"写一个关于实践论的文案"）
        导致 scriyore 的"写文案"短语无法命中 → 返回 []。属设计层缺陷非个案。
  根治：新增 semantic_tags() 从触发短语拆出核心名词标签（"写文案"→"文案"、"口播稿"→"口播"），
        hit() 高置信短语通道未命中时，降级走语义标签散列通道（散字即命中），消除自然语言离散结构盲区。
        对齐《知识库设计通用规范》原则3·确定性触发：机制兜底替代 AI 凭记忆兜底。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re, os

BASE = os.path.expanduser("[记忆共享中心]/技能配置")
SKILLS = ["awaken-memory-system","chrold","clock-loop","daily-buddy","excavator","good-good-study",
          "growth-box","meta-aletheia","scriyore","shall-we-talk","skill-forge",
          "sucair","system-logger","triwich","热点捕手","素然启镜","win-ps1-python-resolution"]

# 匹配面过滤：非用户消息前缀（防御性；Hook 层另有输入源过滤）
_NON_USER_PREFIXES = ("[SYSTEM:", "[Subagent", "[Inter-session", "<autoclaw-terminal-recovery>", "[Attached file:", "Background subagent")
# 本地绝对路径根：剥离后其子串（如路径中的"评估""分析"）不再参与技能匹配；
# 匹配到中文标点/行尾为止（路径目录名可含空格，如"02 待评估文案"）
_PATH_ROOTS = re.compile(r"/(?:Users|Volumes|tmp|private|Applications|Library|System|etc|usr|opt|dev)[^，,。；;）)]*")

# ── 系统注入块识别（2026-08-29·路由侧补齐·对齐 route_audit.strip_injected）──
# 只匹配"人话"，⛔DO NOT 拿系统注入的内容当路由信号——注入里的"记忆系统"
# 会让含"记忆"词素的 Skill（daily-buddy / awaken-memory-system）每轮双命中。
_INJECTED_BLOCK = re.compile(
    r"<system-reminder>.*?</system-reminder>"
    r"|<system[^>]*>.*?</system[^>]*>",
    re.S)
_INJECTED_LINE = re.compile(
    r"^【[^】]{0,40}】[^\n]*", re.M)          # 【路由引擎硬匹配】/【知识库激活…】/【童灵域切片…】
_MACHINE_KV = re.compile(
    r"^(?:SSOT|src_hash|命中|路径|triggers?|skills?)\s*[:：].*$", re.M)



def _sanitize(text):
    """匹配面过滤：非用户消息直拒 + 系统注入块剥离 + 本地路径成分剥离

    2026-08-29 修（daily-buddy 误命中根治）：
      原实现只剥离前缀与路径，未剥离**系统注入块**——而注入内容里含
      "布洛陀五层记忆系统"等词，其中的"记忆"是 daily-buddy 与
      awaken-memory-system 共有的 2 字词素 → 任何一轮都双命中。
      对标 route_audit.py v0.3 的 strip_injected()（审计侧早已剥离，
      路由侧漏做 → 同源失明），此处补齐：只拿**人话**去做匹配。
    """
    if text.startswith(_NON_USER_PREFIXES):
        return ""
    text = _INJECTED_BLOCK.sub(" ", text)
    text = _INJECTED_LINE.sub(" ", text)
    text = _MACHINE_KV.sub(" ", text)
    return _PATH_ROOTS.sub(" ", text)


def get_desc(skill):
    txt = open(os.path.join(BASE, skill, "SKILL.md")).read()
    m = re.search(r"^description:\s*[>|]\s*\n(.*?)^\w", txt, re.S | re.M)
    if not m:
        m = re.search(r"^description:\s*(\S.*?)(?:\n\w)", txt, re.S | re.M)
        return m.group(1).strip() if m else ""
    return re.sub(r"\n\s+", "", m.group(1)).strip()


def extract_words(desc):
    not_idx = desc.find("NOT for")
    main = desc[:not_idx] if not_idx != -1 else desc
    excl = desc[not_idx:] if not_idx != -1 else ""
    # 引号归一：所有中文/直角/英文引号统一为 "
    main = main.replace('\u201c','"').replace('\u201d','"').replace('「','"').replace('」','"').replace("'",'"')
    excl = excl.replace('\u201c','"').replace('\u201d','"').replace('「','"').replace('」','"').replace("'",'"')
    trig, excl_words = [], []
    for sec, bag in ((main, trig), (excl, excl_words)):
        # 语境限定行（"X"单独出现不触发）不参与提取
        sec = re.sub(r'"[^"]*"单独出现[^;；。]*', '', sec)
        # v1.4.1 负例泄漏修复：否定语境「不触发（如"…"）」内引号负例不参与提取
        sec = re.sub(r'不触发[^；;。]*[（(]如[^）)]*[）)]', '', sec)
        # ① 引号块
        for b in re.findall(r'"([^"]+)"', sec):
            for p in re.split(r'[/、|，,；;]', b):
                p = p.strip().strip('"').rstrip("时使用").strip()
                if p and p not in bag: bag.append(p)
        # ② 无引号短语（仅排除词段）：only when 后是触发条件非排除场景，截断
        if bag is excl_words:
            sec = re.split(r'only when|onlywhen', sec)[0]
            for seg in re.split(r'[、，,；;]', sec):
                seg = re.sub(r'[（(].*?[)）]', '', seg).strip()
                for p in re.split(r'[/、]', seg):
                    p = p.strip().strip('"').rstrip("时使用").strip()
                    if p and p not in bag: bag.append(p)
        # ② 无引号列表：触发命令/触发词/当用户说 后接的顿号列表
        m = re.search(r'(?:触发命令|触发词|当用户说|当用户提到)[：:\s]*([^。\n]+)', sec)
        if m:
            tail = re.sub(r'(时使用|时务必使用|时触发).*$', '', m.group(1))
            for p in re.split(r'[/、|，,；;]', tail):
                p = p.strip().strip('"')
                if p and p not in bag: bag.append(p)
    return trig, excl_words


# 语义核心词素表（散列兜底通道用）：覆盖各 Skill 触发短语中的名词核心
# 命中任一词素即判路由，消除"写X的文案"类自然语言离散结构盲区
_SEMANTIC_CORES = [
    "文案", "口播", "视频", "图文", "文章", "写作", "碎碎念", "配文",
    "脚本", "标题", "爆款", "借势", "主角", "故事", "共鸣", "人设", "护城河", "定位",
    "记忆", "笔记", "概念", "读书", "认知", "学习", "刻意",
    "复盘", "睡眠", "精力", "健康", "日记", "周报", "月报", "情绪",
    "评估", "决策", "判断", "风险", "分析", "对比", "验证",
    "Skill", "skill", "脚本", "架构", "开发", "工程", "钩子", "规范", "流水线",
    "记忆系统", "检索引擎", "自动化", "系统日志", "构建", "备份", "优化",
    "配色", "调色", "色", "字体",
    "邮件", "邮箱",
    "热点", "选题",
    "PPT", "演示", "幻灯片",
    "日历", "规划", "专注",
]


def semantic_tags(trig):
    """从触发短语 + 核心词素表生成语义标签（散列兜底通道）.
    返回：原触发短语(整词) ∪ 命中核心词素表的所有词素。
    例：trig含'写文案'→标签含'写文案'(整词)+'文案'(词素)；'口播稿'→'口播稿'+'口播'。
    """
    tags = set()
    for w in trig:
        if len(w) >= 2:
            tags.add(w)  # 整词保留（高置信短语通道失效时的退路）
    for core in _SEMANTIC_CORES:
        if core in trig_joined(trig):
            tags.add(core)
    return tags


def trig_joined(trig):
    return " ".join(trig)


# ══ 判定层增强（2026-10-02·本日两次自捕后的收敛做法）══════════════════════
# ⚠️ 教训（本日自捕三次·血泪）：⛔ 改 `extract_words()` / `get_desc()` 的**提取与过滤逻辑**
#   极其危险——任何一条正则宽一个字符就会**静默吃掉别的 Skill 的触发词**，
#   而你测的那个目标 Skill 一切正常。实证三轮误伤：
#     ①裸 `/` ⇒ meta-aletheia 10→0 / good-good-study 16→0
#     ②`{15,}` 长度过滤 ⇒ triwich 自身触发词 25→0
#   正解：**提取保持原样**（脏数据原样留着·不假装干净），
#        **只在 `hit()` 判定层加否决**——不改一行提取逻辑 ⇒ 零回归天然保证。
# ── ① 否定语境：自名提及 ≠ 自名使用 ────────────────────────────────────────
# 问题：Skill 自名（`三明治`/`三明智`）在触发词表内，任何**提及**都命中——
#   包括「三明治做好没有」这类**询问 Skill 自身状态**的句子。
#   v4.4.16 曾在 Skill 侧枚举 5 种排除形态，实测**5 种全漏**（问法无穷·枚举必败）⇒ 治本下沉。
_SELF_NAMES_CACHE = {}


def _self_names(desc):
    """自名词 = description 首行 Skill 名 + **同族别名**（同首字且等长的触发词）。

    同族判定的依据：命名习惯（`三明治`/`三明智` 首字相同）。新别名只要首字同即自动纳入，
    ⛔ 不必手改——这是穷举失败后换判据层的关键。
    """
    head = re.match(r"^\s*([\u4e00-\u9fa5A-Za-z]{2,6})[（(]", desc)
    primary = head.group(1) if head else None
    if not primary or len(primary) < 3:
        return set()
    names = {primary}
    for blk in re.findall(r'"([^"]+)"', desc):
        for w in re.split(r'[/、|，,；\n\s]+', blk):
            w = w.strip()
            if (len(w) == len(primary) and w != primary and w[0] == primary[0]
                    and all('\u4e00' <= c <= '\u9fa5' for c in w)):
                names.add(w)
    return names


# 谈论/询问 Skill 自身的中文形态标记
_MENTION_MARKERS = (
    "做好", "做完", "搞定", "好了吗", "好了没", "做完没", "完成没", "完成了吗",
    "进展", "进度", "状态", "怎么样", "如何", "咋样",
    "是啥", "是什么", "哪个", "哪些", "哪里", "在哪", "多少",
    "有没有", "能不能", "可以吗", "行不行", "好用吗", "靠谱吗",
    "改好了", "更新了", "升级了", "有没有改", "处理了",
    # 2026-10-02 补·你原话「你这一轮真的也没有启动三明治啊，为什么还是要用它的格式来回复呢？」
    #   ——问的是**使用方式/调用行为**，不是要分析。补「启动/调用/用了/用了它的格式」等。
    "启动", "调用", "用了", "用它", "用它的", "用了它", "触发", "路由", "拉起",
    "为什么还要", "为什么用", "干嘛用",
)


# ── 使用指令豁免（2026-10-07·Qoder CN 自捕「三明治评估被误判谈论」案）──
# 问题：v0.1.4 判据「自名+疑问句式即判谈论」对**指令式疑问**过杀——你原话
#   「用三明治评估怎么做才是符合愿景的最优解？」是**叫它干活**（祈使+自名+使用动词），
#   句末问号只是修辞 ⇒ triwich 被 suppress，good-good-study 经"评估"词素独中
#   ⇒ 引擎输出「硬匹配 good-good-study 请调用」的**错误指令**（2026-10-07 实测复现）。
# 修法：判定层加否决——命中**使用指令形态**（[用让帮请拿通过叫令]紧贴自名）且句中
#   无状态/元谈论标记（做好/进展/格式/为什么…）⇒ 判"使用"非"谈论"，豁免抑制。
#   ⛔ 只加豁免不动原判据（问法无穷·枚举必败教训仍有效——这里枚举的是**有限**的
#   祈使动词集，不是问法）；⛔ 不碰 extract_words/get_desc（血泪警示区）。
def _is_use_directive(text):
    m = re.search(r"(?<![不别要])[用让帮请拿通过叫令](?:我|你)?(?:个)?三明治", text)
    if not m:
        m = re.search(r"(?<![不别要])(?:叫|令|来)(?:我|你)?(?:个)?三(?:明[治智]|明(?:治|智))", text)
    if not m:
        m = re.search(r"(?:启动|开始)(?:个)?三(?:明[治智])", text)
    if not m:
        return False
    # 元谈论/状态标记出现 ⇒ 是"谈论使用行为"不是"指令使用"，不豁免。
    # ⚠️ 判据收窄（2026-10-07 负例「用三明治评估这个策略靠谱吗？」自捕）：
    #   只认**指向 Skill 自身的**强谈论信号（它的/这个设计/格式/为什么）与**状态类**
    #   标记（做好/进展/进度…）；⛔ 不再用全量 _MENTION_MARKERS——"靠谱吗/怎么样/能不能"
    #   这类标记在指令句里往往是冲着**分析对象**去的（评估这个策略靠谱吗），不是冲着自名。
    strong_meta = ("它的", "这个设计", "回复格式", "格式", "干嘛", "为什么")
    status_markers = ("做好", "做完", "搞定", "好了", "完成没", "做完没", "进展", "进度",
                      "状态", "改好了", "更新了", "升级了", "有没有改", "处理了")
    if any(x in text for x in strong_meta) or any(x in text for x in status_markers):
        return False
    return True


def _is_self_mention(text, desc):
    """text 是否在「谈论该 Skill 自身」。

    ⚠️ v0.1.4 判据重构（本引擎第三次踩同一个坑的修复）：此前要求「自名 + 状态问法标记」
    **同时命中**，形态有限而问法无穷——实测连续漏：
      「三明治做好没有？」/「三明治做完了没」/「三明治好了吗」/「三明治搞定了吗」/「三明治进展如何」
      「你这一轮真的也没有启动三明治啊，为什么还是要用它的格式来回复呢？」
      「为什么还是有这个三明治的回复格式呢？」        ← 本条又漏（说的是"回复格式"不是"用它的格式"）
    ⇒ **换判据层**：自名一旦命中，只要**同句含疑问/谈论结构**即判谈论，⛔ 不再要求"必须命中某个特定标记词"。
    判据 = 自名命中 **且**（疑问句式 **或** 状态/谈论标记）。
    边界（如实声明）：⛔ 这是形态启发——「用三明治分析这个方案」也含疑问式但**无自名**（自名在句中才触发），
    故正常祈使使用不受影响；⚠️ 「你觉得三明治这个设计怎么样」含自名+疑问式 ⇒ 判谈论（诚实的边界，
    宁可漏触发也不误触发——过度触发才是本轮要治的病）。
    """
    names = _self_names(desc)
    if not names:
        return False, []
    hitn = [n for n in names if n in text]
    if not hitn:
        return False, []
    # 否定拒用形态（2026-10-07 负例自捕「不要三明治了直接说」预存过触发）：
    #   拒绝/否定紧邻自名 ⇒ 判谈论（用户明说不要用，触发=逆着用户）。有限枚举·非问法侧。
    _neg_pat = "(?:(?:不要|不用|无需|不需|别再?|禁止)\\s*(?:再)?(?:用|调用|启动|拉起)?\\s*(?:%s))" % "|".join(sorted(names, key=len, reverse=True))
    if re.search(_neg_pat, text):
        return True, hitn + ["否定拒用"]
    # ① 疑问句式：句中有问号/疑问词尾/反问标记
    interrogative = any(x in text for x in ("?", "？", "吗", "呢", "吧？"))
    # ② 状态/谈论/使用方式标记
    markers = [m for m in _MENTION_MARKERS if m in text]
    evidence = hitn + markers
    if interrogative:
        evidence.append("疑问句式")
    if (interrogative or markers) and _is_use_directive(text):
        # 使用指令豁免：祈使+自名 ⇒ 判"使用"，不抑制（2026-10-07 根治）
        return False, evidence + ["使用指令豁免"]
    if interrogative or markers:
        return True, evidence
    return False, evidence


# ── ② 宾语限定：description 写了但引擎不执行的规则 ─────────────────────────
# 问题：description 明写「宾语是代码/文件/数据不触发」，但**路由不执行这条规则**——
#   负例 `"分析代码"` 被「不触发（如…）」正则正确剔除出排除词表 ⇒ 触发词「分析」
#   照样子串命中 ⇒「分析这段代码」误触发。实证：eval-set #6/#9/#10 改前改后同样红。
# 修法：从 description **自动解析**该句，句中命中该宾语即否决。
#   ⛔ 无此句的 Skill 返回空集 ⇒ 行为同改前（零回归保证）。
_OBJECT_NEG_RE = re.compile(r"宾语是([\w/、\s]+?)不触发")


def _object_negatives(desc):
    m = _OBJECT_NEG_RE.search(desc)
    if not m:
        return set()
    return {w for w in re.split(r"[\s/、，,]+", m.group(1))
            if len(w) >= 2 and re.match(r"^[\u4e00-\u9fa5A-Za-z]+$", w)}


# ── 疑问词裸奔防护（2026-10-02·本日第三处自捕）──
# 问题：疑问词类触发词（为什么/原因/靠谱吗/确定吗/真的吗…）是**任何提问**都会出现的。
#   实测你的原话「你这一轮真的也没有启动三明治啊，**为什么**还是要用它的格式来回复呢？」
#   ——句中**没有任何分析对象**，纯靠「为什么」把 triwich 拉起来 ⇒ 自证循环
#   （"问你为什么用三明治" ⇒ "为什么"命中三明治 ⇒ 拉起三明治）。
# 判据：疑问词**单独命中**（句中只有疑问词类触发词、无实义触发词）⇒ 不触发。
#   ⛔ 保留「为什么这个方案的风险在哪」这类——句中还有实义词，风险已覆盖。
_QUESTION_ONLY = {"为什么", "原因", "吗", "呢", "什么", "怎么", "如何", "怎么", "啥"}
# ⚠️ 「靠谱吗/确定吗/真的吗」**不入**此表——它们是**分析请求**不是纯提问
#   （实证：误杀 eval-set #2「靠谱吗？这个推论」⇒ 期望触发）


def _question_only_hit(hit_words):
    """命中的触发词是否**全部**属疑问词类（⇒ 纯提问·无分析对象）。"""
    return bool(hit_words) and all(w in _QUESTION_ONLY for w in hit_words)


def hit(skill, text):
    desc = get_desc(skill)
    trig, excl = extract_words(desc)
    mention, m_evidence = _is_self_mention(text, desc)
    hit_words = [w for w in trig if w and w in text]
    if not hit_words:
        # 降级：语义标签散列通道（自然语言离散结构兜底）
        tags = semantic_tags(trig)
        hit_words = [t for t in tags if t and t in text]
    if not hit_words:
        return False, [], []
    # 「纯提问」还需**句中无实义宾语**——否则「为什么这个设计有问题」会被误杀
    #   （它命中「为什么」但宾语是"这个设计"= 有分析对象）。判据：疑问词之外还出现
    #   长度 ≥2 的中文/字母实义词 ⇒ 不是纯提问。⛔ 疑问词本身已在上面被过滤。
    if _question_only_hit(hit_words):
        residue = re.sub(r"[?？。，、！!：:；;\s]", "", text)
        residue = re.sub(r"为什么|原因|什么|怎么|如何|吗|呢|吧|啥", "", residue)
        if len(residue) < 2:            # 剥掉疑问词后几乎无内容 ⇒ 纯提问
            return False, [], hit_words
    excl_hit = [w for w in excl if w and w in text]
    if excl_hit:
        return False, hit_words, excl_hit
    if mention:
        return False, hit_words, m_evidence          # 自名 + 状态问法 ⇒ 谈论
    obj_neg = _object_negatives(desc)
    if obj_neg:
        hit_obj = [o for o in obj_neg if o in text]
        if hit_obj:
            return False, hit_words, hit_obj          # 宾语是代码/文件/数据
    return True, hit_words, excl_hit


def route(text):
    text = _sanitize(text)
    if not text:
        return []
    return [s for s in SKILLS if hit(s, text)[0] and hit(s, text)[1]]
