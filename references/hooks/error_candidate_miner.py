#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/error_candidate_miner.py   # 真源声明·派生面须软链指向本件（卡A 步1 补·search_kb 同族病灶根治）
"""
error_candidate_miner.py — 错误候选挖掘器（L1机械发现层·P1-1错误记录半自动化）
每天自动扫描近7天系统日志，用关键词+规则粗筛"该记没记"的错误候选，写入待确认文件。

设计原则（童灵愿景裁决2026-09-03）：
- 规则+关键词粗筛，不需要LLM在中间做判断（S014自觉是安慰剂机械是药——粗筛用机械，判断用人）
- 候选≤5条，按优先级排序（避免用户疲劳）
- 排除"已修复/已解决/已完成"等表示成功的词（避免假阳性）
- 幂等：每天运行时更新未处理的候选，已处理的保留
- 与growth-box启动自检的错误候选扫描互补（本脚本从系统日志机械挖掘，growth-box从当前对话回顾）

历史版本：
v1.0.1 (2026-09-03)：①TITLE_EXCLUDE_KEYWORDS只保留明确成功词 ②新增STRONG_ERROR_KEYWORDS ③is_error_candidate返回tuple ④系统性盲区错误加分+15→+25 ⑤MAX_CANDIDATES 5→10 ⑥ERROR_KEYWORDS加修正/修复/返工/补录等词
v1.0.2 (2026-09-03)：标题级强排除（[童灵思考]前缀/落地收口升级等完成类标题）
来源：豆包端TIML评估发现L7"错误→成长箱记录"未落地→挖掘器排除词过严；v1.0.x 三端候选反复误报 10/10 实证

v3.2.0 (2026-09-07·童灵根治·你"不能单单修复要根治")：
    四轮词表修补（v1.0.1/v1.0.2/v2.0/v2.0.2）全部失败的根治——判定模型从"词表"转为"高门槛白名单"。
    根因（实证）：系统日志 262 条/周里 258 条是"已完成工作"叙述，正文必含"修复了失败/发现缺失"等词，
    任何"扫正文找错误词"的模型都被叙述淹没（每轮换一批 10 条误报）；真错误的信号只在标题的
    "自我声明"（错误叙述 or 工作完成），且事后系统日志里"该记没记"极少——真错误发现通道是
    growth-box 启动时的对话回顾（AI 当下承认犯错）。
    本版：默认静默（宁缺毋滥）——仅当标题是"明确错误叙述且无解决动作词"才报候选；
    已入账动作（流程A/记录X错误）/巡检/例行评估/[童灵思考] 一律排除。
    回测 13/13：误报（落地/根治/修复/巡检/入账/评估类）全静默，真错误（遗漏/未检查/未配置/静默失效）全保留。
    ⛔ 真错误主通道=growth-box 对话回顾；本脚本只兜底"系统日志明确记载未解决错误"的极端情况。

v3.3.0 (2026-09-22·童灵·皮叔令「处理完毕，包括堵点」·堵点B 根治)：
    真机复现 v3.2.0 白名单 9/9 全是工作记录误报（本体实跑·非部署漂移）。根因两条：
    ① 否定/成功形态未拦——"没有问题"/"零问题"/"全绿"/"首跑通过"/"对账全 0" 带成功语义，
       但"问题"命中名词通道后只要无解决动词即放行；
    ② 自纠类解决动词缺失——"自纠一处口径错误"是已纠正，但解决动词表无「自纠/纠错」。
    修法：名词通道前加【否定/成功护栏】+ 解决动词表补「自纠/已纠/纠错/勘误」。
    回测：候选 9→3（余 3 条留 L2 人工判）；夹具 D1-D4 两向钉死（否定不报 / 真错误仍报）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import re
from pathlib import Path
from datetime import datetime, timedelta, date

SYSTEM_LOG_DIR = Path.home() / "[记忆共享中心]/工作日志/系统日志"
PENDING_FILE = Path.home() / "[记忆共享中心]/成长箱/错误候选待确认.md"

# ============================================================
# v2.0 根治（2026-09-07·童灵·你"这些问题不能单单修复而是要根治"）
# 判定模型反转：从"广撒网关键词命中 + 排除词补救"→"两级判定"
#  一级：完成态叙述（标题/类型含完成态词 或 [童灵反思/思考]前缀）→ 直接排除
#        ——落地/入账/裁决/反思/固化/更新 等是"做了什么"的成功叙述，永远不是"该记没记"的错误
#  二级：内容须含"强错误事实证据"（遗漏/漏/只检查/返工/同错N犯等已发生错误）
#        ——⛔排除"防/避免/防止/不"前缀（"防误判"≠"误判已发生"）
# 回测：10 条误报 10/10 排除（v1.0.2 残留 10/10）；真候选"端清单SSOT化修正(只检查3端遗漏5端)"保留
# 已入账条目（标题含"入账/流程A"）由一级排除自然去重——原 auto_mark_processed 词面去重失效问题消失
# ============================================================

# 高优先级关键词（命中则优先级提升——系统性盲区最值得人确认）
HIGH_PRIORITY_KEYWORDS = [
    "遗漏", "漏掉", "漏报", "漏记", "只检查", "没检查", "未检查",
    "系统性盲区", "盲区", "断链", "漂移", "不一致",
    "同错", "次犯", "第3次", "四犯", "又犯", "再犯",
    "critical", "🔴", "严重", "数据丢失", "覆盖",
]

MAX_CANDIDATES = 10  # 候选上限（避免每日候选过多淹没真实信号）
SCAN_DAYS = 7


def cell(text, limit=50):
    """把任意来源字段压成**合法表格单元**：换行折叠成空格、竖线转义、再按可见字符截断。

    根因防线（2026-09-19 实测）：c['title']/c['summary'] 取自系统日志正文（多行文本），
    直接切片会把 `\n` 带进表格行 —— 模板拼出的"一行"实际跨 4 个物理行，行尾落在下一条
    记录中间（`成长箱/错误候选待确认.md` 同型破损 09-15/09-16/09-18/09-19 连续复跑到第 5 条，
    由 md_table_shape_guard J1 判红）。"""
    flat = re.sub(r"\s+", " ", re.sub(r"[\n\r]+", " ", str(text))).strip()
    flat = flat.replace("|", "\\|")
    if len(flat) > limit:
        flat = flat[:limit].rstrip()
        if flat.endswith("\\"):        # ⛔把转义对截半（结尾剩单 `\`）＝下一轮渲染吃字
            flat = flat[:-1]
    return flat


def parse_log_entries(content: str) -> list:
    """解析系统日志文件，提取条目（以### 开头的标题为条目分隔）"""
    entries = []
    current_entry = []
    current_title = ""

    for line in content.split("\n"):
        if line.startswith("### "):
            if current_title and current_entry:
                entries.append({
                    "title": current_title,
                    "content": "\n".join(current_entry),
                })
            current_title = line[4:].strip()
            current_entry = []
        else:
            current_entry.append(line)

    if current_title and current_entry:
        entries.append({
            "title": current_title,
            "content": "\n".join(current_entry),
        })

    return entries


def is_error_candidate(entry: dict) -> tuple:
    """判断一个条目是否是错误候选——v3.0 高门槛白名单（童灵·2026-09-07 终局根治）。

    返回 (is_candidate: bool, priority_adjustment: int)

    四轮修补教训（v1.0.1/v1.0.2 词表补丁 + v2.0 两级模型 + v2.0.2 巡检排除）：
      系统日志 262 条/周里 258 条是"已完成工作"叙述——正文必含"修复了失败/发现缺失"等词，
      任何"扫正文找错误词"的模型都会被叙述性正文淹没（实测每轮都换一批 10 条误报）。
      真错误的信号只在条目的"自我声明"（标题），且事后系统日志里"该记没记"的错误极少
      ——真正的错误发现通道是 growth-box 启动时的对话回顾（AI 当下承认犯错）。

    本版定位收敛：高门槛白名单，宁缺毋滥（高精度低召回）。
      只有标题同时满足：①明确错误叙述（含错误编号 或 "X错/缺陷/故障/事故"且非完成态）
      才报候选；其余一律静默。代价=可能漏掉藏在完成记录里的错误——由 L2 对话回顾兜底。
    """
    title = entry["title"]

    # ── 排除：童灵思考/巡检/已入账动作/例行评估（100% 非待确认错误）──
    if title.startswith(("[童灵反思]", "[童灵思考]")):
        return False, 0
    if "巡检" in title:
        return False, 0
    if re.search(r'(流程A|成长箱.*(记录|入账|沉淀)|记录.*错误|错误.*入账)', title):
        return False, 0
    if re.search(r'(triwich|growth-box|clock-loop|daily-buddy).*(v\d|Loop|摸底|评估)', title):
        return False, 0

    # ── v3.3.0 补（2026-09-22·童灵·皮叔令「处理完毕，包括堵点」）──
    # 实证：v3.2.0 白名单在真机 9/9 全是「工作记录」误报（本体实跑复现·非部署漂移）。
    # 病根两条：
    #   ① **否定/成功形态未拦**——「没有问题」「对账全 0」「首跑通过」「零问题交付」带成功语义，
    #      但"问题"命中名词通道后，只要没有解决动词就被放行；
    #   ② **自纠类解决动词缺失**——「自纠一处口径错误」是**已纠正**，但解决动词表无「自纠/纠错」故未拦。
    # 修法：名词通道前加【否定/成功护栏】+ 解决动词表补「自纠/已纠/纠错/勘误」。
    # ⛔不删「问题」名词本身（真错误「XX问题未解决」仍需它）——只拦它的否定形态。
    if re.search(r'(没有问题|没问题|无问题|零问题|不见问题)', title):
        return False, 0
    if re.search(r'(首跑通过|对账全 ?0|全绿|验收通过|全部通过|闭环完成)', title):
        return False, 0

    # ── 白名单：标题须是"明确错误叙述" ──
    # 通道1：错误编号句式（QCN-/ERR-/PAT-/TE-/QD- 前缀记录）
    if re.search(r'^\s*[A-Z]+-\d{8}-\d{3}|^\s*(记录|复盘|反思).*(错误|失误|教训)', title):
        return True, 0
    # 通道2：标题含错误名词——但⛔须无"解决动作词"（根治/修复/修正/闭环/落地=已处理，
    #       不是"该记没记"；真候选=标题只有错误事实、无解决承诺）
    error_noun = re.search(r'(缺陷|故障|事故|不一致|漂移|撞号|脱钩|死循环|崩溃|失效|漏洞|问题|错误|遗漏|漏掉|漏报|漏记|未检查|没检查|只检查|漏配|零命中|未配置|没配置|空跑|静默)', title)
    if error_noun:
        # 任何解决动作词 → 已处理/处理中 → 非待记录错误
        # 解决动作词判定：⛔"已"字不单独算解决（"已接入端/已存在"≠已解决），须"已+解决动词"或明确解决词
        if re.search(r'(根治|修复|修正|闭环|解决|落地|整改|重构|加固|硬墙|防御|处理完|补完|救|弥合|补齐|同步补齐|统一|自纠|已纠|纠错|勘误)', title):
            return False, 0
        if re.search(r'(已修复|已解决|已完成|已处理|已闭环|已根治)', title):
            return False, 0
        return True, 0
    # 通道3：标题含"犯/失误/教训/错误规律/方法错误"（反思认错型）——同样要求无解决动作
    if re.search(r'(犯.*错|失误|教训|错误规律|方法错误|次错误)', title):
        if re.search(r'(根治|修复|修正|闭环|解决|落地|入账|记录|已处理)', title):
            return False, 0
        return True, 0

    return False, 0


def calculate_priority(entry: dict) -> int:
    """计算候选优先级（0-100，越高越优先）"""
    text = entry["title"] + " " + entry["content"]
    priority = 50  # 基础分

    # 高优先级关键词加分
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw.lower() in text.lower():
            # 系统性盲区错误（遗漏/漏报/漏记/只检查）加25分，其他加15分
            if kw in ["遗漏", "漏掉", "漏报", "漏记", "只检查", "没检查", "未检查", "系统性盲区", "盲区"]:
                priority += 25
            else:
                priority += 15
            break

    # 标题中含错误名词加分（标题级错误比内容级错误更重要——v3.2 用正则替代词表）
    if re.search(r'(缺陷|故障|事故|不一致|漂移|撞号|脱钩|死循环|崩溃|失效|漏洞|问题|错误|遗漏|漏掉|漏报|漏记|未检查|没检查|只检查|漏配|零命中|未配置|没配置|空跑|静默)', entry["title"]):
        priority += 10

    # 重复发生信号加分（同错N犯/又犯/再犯/复发——模式性最值得人确认）
    if any(kw in text for kw in ["重复", "再次", "又犯", "复发", "同错", "次犯",
                                  "第N次", "第2次", "第3次", "第4次", "四犯"]):
        priority += 20

    return min(priority, 100)


def extract_summary(entry: dict) -> str:
    """从条目中提取摘要（对话摘要或结论字段）"""
    content = entry["content"]

    # 优先取"对话摘要"字段
    summary_match = re.search(r'(?:对话摘要|摘要)[:：]\s*(.+)', content)
    if summary_match:
        return summary_match.group(1).strip()[:100]

    # 其次取"结论"字段
    conclusion_match = re.search(r'结论[:：]\s*(.+)', content)
    if conclusion_match:
        return conclusion_match.group(1).strip()[:100]

    # 最后取内容前100字
    return content.strip()[:100]


def extract_source(entry: dict, log_date: str) -> str:
    """提取来源（工具字段+日期）"""
    content = entry["content"]
    tool_match = re.search(r'(?:工具|来源AI)[:：]\s*(.+)', content)
    tool = tool_match.group(1).strip() if tool_match else "未知"
    return f"{tool} · {log_date}"


def scan_system_logs() -> list:
    """扫描近7天系统日志，提取错误候选"""
    candidates = []
    today = date.today()

    for i in range(SCAN_DAYS):
        log_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        log_file = SYSTEM_LOG_DIR / f"系统日志_{log_date}.md"

        if not log_file.exists():
            continue

        content = log_file.read_text(encoding="utf-8")
        entries = parse_log_entries(content)

        for entry in entries:
            is_cand, priority_adj = is_error_candidate(entry)
            if is_cand:
                priority = calculate_priority(entry) + priority_adj
                priority = max(0, min(priority, 100))  # 限制在0-100
                summary = extract_summary(entry)
                source = extract_source(entry, log_date)
                candidates.append({
                    "title": entry["title"],
                    "summary": summary,
                    "source": source,
                    "priority": priority,
                    "log_date": log_date,
                })

    # 按优先级排序，取前MAX_CANDIDATES条
    candidates.sort(key=lambda x: x["priority"], reverse=True)
    return candidates[:MAX_CANDIDATES]


def load_pending(path=None) -> dict:
    """加载待确认文件，返回已处理的候选标题集合（用于幂等）。
    path 仅供夹具注入临时文件；默认=生产 PENDING_FILE，行为不变。"""
    _p = Path(path) if path else PENDING_FILE
    processed = set()
    if not _p.exists():
        return processed

    content = _p.read_text(encoding="utf-8")
    # 已处理的候选标记为 ✅已处理
    # v3.4.2（QCN-20261011-027 追洞）：旧取首格用非贪婪 r'\|\s*(.+?)\s*\|'，
    # 遇表格单元内已转义的竖线（端名 \| 标题形态）会在那里截断，跳过集键被切成
    # "Qoder CN \" → 出清写了却不生效。改与 _in_pending_table 同一口径：转义感知列切分＋去转义。
    for line in content.split("\n"):
        if "✅已处理" not in line or not line.startswith("|"):
            continue
        cols = [c.strip() for c in re.split(r"(?<!\\)\|", line)]
        if len(cols) >= 2 and cols[1]:
            processed.add(cols[1])   # v3.4.3：存格原文，归一与比对统一交给 key_match

    return processed


def scan_recent_growthbox_entries() -> list:
    """扫描成长箱learnings/目录，提取最近7天新写入的错误条目标题（用于L3自动回写）"""
    learnings_dir = Path.home() / "[记忆共享中心]/成长箱/learnings"
    if not learnings_dir.exists():
        return []

    today = date.today()
    recent_titles = []

    for f in learnings_dir.glob("*.md"):
        name = f.name
        if name in ["INDEX.md", "FEATURE_REQUESTS.md"] or name.startswith("book_"):
            continue

        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue

        entries = re.findall(r'^## \[([^\]]+)\]\s*(.+?)\s*$', content, re.MULTILINE)
        dates = re.findall(r'(?:Logged|日期)[:：]\s*(\d{4}-\d{2}-\d{2})', content)

        for i, (entry_id, title) in enumerate(entries):
            entry_date = None
            if i < len(dates):
                try:
                    entry_date = datetime.strptime(dates[i], "%Y-%m-%d").date()
                except ValueError:
                    pass

            if entry_date is None:
                try:
                    mtime = date.fromtimestamp(f.stat().st_mtime)
                    if (today - mtime).days <= SCAN_DAYS:
                        recent_titles.append(title.strip())
                except Exception:
                    pass
            elif (today - entry_date).days <= SCAN_DAYS:
                recent_titles.append(title.strip())

    return recent_titles


def auto_mark_processed(candidates: list, recent_titles: list) -> set:
    """L3自动回写：将待确认候选与成长箱最近写入的错误条目模糊匹配，匹配成功则标记已处理"""
    processed = set()

    for candidate in candidates:
        cand_title = candidate["title"].lower()
        for recent_title in recent_titles:
            rec_title = recent_title.lower()
            if len(cand_title) > 10 and len(rec_title) > 10:
                cand_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', cand_title))
                rec_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', rec_title))
                if cand_words and rec_words:
                    overlap = len(cand_words & rec_words) / len(cand_words)
                    if overlap >= 0.5:
                        processed.add(candidate["title"])
                        break
            elif cand_title[:15] in rec_title or rec_title[:15] in cand_title:
                processed.add(candidate["title"])
                break

    return processed


# ── 人工注记保留区（2026-10-10 断根轮增·与条文41 托管块副本律同一姿势）──
# 病根：本脚本整文件重写待确认表 ⇒ 人在文件里留下的裁决（如批量出清注记）每轮被冲掉。
# 根治：写前抽取 HUMAN-NOTES 标记区、写回时原样附上；⛔不依赖人记得另存（愿景①）。
HUMAN_B = "<!-- HUMAN-NOTES:BEGIN -->"
HUMAN_E = "<!-- HUMAN-NOTES:END -->"


def extract_human_notes(path):
    try:
        old = open(path, encoding="utf-8").read()
    except Exception:
        return ""
    i, j = old.find(HUMAN_B), old.find(HUMAN_E)
    return old[i:j + len(HUMAN_E)] if i >= 0 and j > i else ""


def merge_human_notes(content, notes):
    if not notes or notes in content:
        return content
    return content.rstrip() + "\n\n" + notes + "\n"


def generate_pending_content(candidates: list, processed: set) -> str:
    """生成待确认文件内容"""
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "---",
        "title: 错误候选待确认",
        "type: pending",
        "status: active",
        f"last_updated: {today_str}",
        "---",
        "",
        "# 🔔 错误候选待确认（自动生成·error_candidate_miner.py）",
        "",
        f"> 最后更新：{today_str} | 每天自动扫描近{SCAN_DAYS}天系统日志 | 关键词+规则粗筛（非LLM判断）| 候选≤{MAX_CANDIDATES}条按优先级排序",
        "> 用户确认后走成长箱流程A写入；⛔禁止手动编辑标记区域外的内容",
        "",
        "## 待确认候选",
        "",
        "| # | 优先级 | 错误标题 | 摘要 | 来源 | 状态 | 操作 |",
        "|:-:|:-----:|---------|------|------|:----:|------|",
    ]

    unprocessed = [c for c in candidates if not already_closed(c["title"], processed)]

    if not unprocessed:
        lines.append("| — | — | — | ✅ 无新错误候选 | — | — | — |")
    else:
        for i, c in enumerate(unprocessed, 1):
            priority_label = "🔴高" if c["priority"] >= 70 else ("🟡中" if c["priority"] >= 50 else "🟢低")
            lines.append(
                f"| {i} | {priority_label}({c['priority']}) | {cell(c['title'], 40)} | {cell(c['summary'], 50)} | {cell(c['source'], 20)} | ⏳待确认 | 用户确认→成长箱流程A |"
            )

    lines.extend([
        "",
        "## 已处理候选（保留7天用于追溯）",
        "",
        "| 错误标题 | 处理日期 | 处理结果 |",
        "|---------|---------|---------|",
    ])

    # 已处理的候选（从原文件中保留）
    if PENDING_FILE.exists():
        content = PENDING_FILE.read_text(encoding="utf-8")
        in_processed_section = False
        for line in content.split("\n"):
            if line.startswith("## 已处理候选"):
                in_processed_section = True
                continue
            if in_processed_section and line.startswith("|") and "✅已处理" in line:
                lines.append(line)
            elif in_processed_section and line.startswith("## "):
                break

    if not any("✅已处理" in l for l in lines):
        lines.append("| — | — | 暂无已处理候选 |")

    lines.extend([
        "",
        "## 调度说明",
        "",
        "1. **L1机械发现层**：本脚本每天由launchd自动运行（com.buluotuo.error-candidate-miner），扫描近7天系统日志，用关键词+规则粗筛错误候选",
        "2. **L2人工确认层**：每日伙伴晨间规划读取本文件呈现候选；growth-box启动自检合并呈现（从系统日志挖掘+从当前对话回顾，两者互补不重复）",
        "3. **L3自动回写层**：用户确认后走成长箱流程A写入，本文件对应候选标记为✅已处理",
        "4. **与蒸馏调度器同构**：L1机械发现（不可跳过）+L2人工确认（放权但不失控）+L3自动回写（闭环）",
        "5. ⛔本文件由脚本机械生成，禁止手动编辑候选表格内容（已处理区域可追加处理结果）",
        "",
    ])

    return "\n".join(lines)


def _in_pending_table(lines, title):
    """存在性判据：只在「待确认候选」表的**错误标题列**（第3格）里找，⛔ 全文子串搜索。
    2026-10-11 生产实测教训：曾用 `title in line or cell(title,40) in line` 全文判据，把一条
    本不在出清名单的候选（其字样出现在别行的摘要格里）误判命中并写了孤儿行——误闭=擅自
    压掉别人的真候选，比不闭更糟。截断形态用 cell(title,40)，与渲染处同一定义。"""
    for l in lines:
        if not l.startswith("| ") or "\u23F3待确认" not in l:
            continue
        parts = [c.strip() for c in re.split(r"(?<!\\)\|", l)[1:-1]]
        if len(parts) >= 3 and key_match(parts[2], title):
            return True
    return False


# ── L2 裁决回写通道（v3.4.0·2026-10-11 卡A 步1·根治「出清裁决落 prose 注记区→每日复活」）──
# 病根：load_pending() 只认**状态通道**（含 ✅已处理 的行取首格）做幂等，而人工出清裁决
#       写在 HUMAN-NOTES prose（措辞「判不记」）→ 匹配不到 → 已出清候选每天 07:38 复活。
# 职责边界：把裁决落到**既有**「已处理候选」表（本文件调度说明第5条早已声明
#       "已处理区域可追加处理结果"）；⛔ 不新建第二状态源、⛔ 不改待确认表结构、⛔ 不解析 prose。
_CLOSE_STRICT = True   # 变异位：_self_test 置 False＝还原「未命中也照写」的静默旧行为


def _unesc(s):
    """去表格转义：把 \\| 还原成 |（v3.4.1 新增·QCN-20261011-027）。"""
    return re.sub(r"\\([|])", r"\1", s or "")


def _esc_cell(s):
    """竖线转义成合法表格单元（幂等：已转义的不重复转·v3.4.1 新增）。"""
    return re.sub(r"(?<!\\)\|", r"\\|", s or "")


# 命中形态留痕（截断命中＝前缀相同，存在误闭他人真候选的风险·必须可抽检）
_KEY_HITS = []
KEY_MIN_PREFIX = 20   # 前缀匹配下限（字符）；低于此长度不足以认定同一条候选


def _norm(t):
    """候选标题的归一形态：去表格转义＋折叠空白（三处比对共用此唯一口径）。"""
    return re.sub(r"\s+", " ", _unesc(str(t or ""))).strip()


def key_match(a, b):
    """判定两个标题是否同一条候选：'exact'｜'prefix'｜None（v3.4.3·QCN-20261011-028）。

    病根：写侧存的是渲染后的截断格（cell 已转义＋截 40 字，且 cell 不幂等），读侧拿到的是全长标题，
    旧版用字面相等比 ⇒ rc=0 却出清不生效。现统一走 _norm 后先精确比、再前缀比。
    ⛔ 不许静默前缀命中：prefix 命中一律记入 _KEY_HITS 并显形（防两条候选共享前 20 字时误闭）。
    """
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return None
    if na == nb:
        return "exact"
    n = min(len(na), len(nb))
    if n >= KEY_MIN_PREFIX and na[:n] == nb[:n]:
        _KEY_HITS.append(("prefix", (na[:44]), n))
        return "prefix"
    return None


def already_closed(title, processed):
    """跳过集成员判定的唯一入口（⛔各处再自造 `in set` 字面比对）。"""
    return any(key_match(title, p) for p in processed)


def close_candidate(title, verdict="不记", reason="", path=None):
    """把一条候选的 L2 裁决落到「已处理候选」表（状态通道）。
    rc：0=写入成功或幂等已在位｜1=标题零命中（拒写·防孤儿行）｜2=参数/结构错误（拒写）"""
    _p = Path(path) if path else PENDING_FILE   # 顶部是 from pathlib import Path，⛔ 写 pathlib.Path
    if not title or not str(title).strip():
        print("error: --close 标题为空", file=sys.stderr); return 2
    if "\n" in title or "\r" in title:
        print("error: 标题含换行——拒写（表格行必须单行·2026-09-19 md_table_shape 同型病）", file=sys.stderr)
        return 2
    # v3.4.1（QCN-20261011-027）：竖线不再拒写。待确认表里现存标题就带转义竖线形态，
    # 旧实现只拦不接＝正门对唯一在册候选不可达，出清退回 prose 老路。改为写前转义、比对时去转义。
    title_out = _esc_cell(title)
    if not _p.exists():
        print(f"error: 待确认文件不存在 {_p}", file=sys.stderr); return 2
    lines = _p.read_text(encoding="utf-8").split("\n")
    head = next((i for i, l in enumerate(lines) if l.startswith("## 已处理候选")), None)
    if head is None:
        print("error: 文件缺「## 已处理候选」节——拒写（不自动造结构·防误覆盖既有文件）", file=sys.stderr)
        return 2
    sep = next((i for i in range(head, len(lines)) if re.match(r"^\|[-: |]+\|$", lines[i])), None)
    if sep is None:
        print("error: 已处理节缺表格分隔行——拒写", file=sys.stderr); return 2
    if any(l.startswith("| ") and len(re.split(r"(?<!\\)\|", l)) > 2
           and key_match(re.split(r"(?<!\\)\|", l)[1].strip(), title)
           for l in lines[head:]):
        print(f"ℹ️ 幂等：「{title[:30]}」已在已处理表，未重复追加"); return 0
    if _CLOSE_STRICT and not _in_pending_table(lines, title):
        print(f"error: 标题「{title[:40]}」在文件中零命中——⛔ 拒绝写入（拼错或候选已被清理，不造孤儿行）",
              file=sys.stderr)
        return 1
    if sep + 1 < len(lines) and "暂无已处理候选" in lines[sep + 1]:
        lines.pop(sep + 1)                       # 真行进来，占位行退场
    date_str = datetime.now().strftime("%Y-%m-%d")  # 日期归脚本，⛔ 不采信调用方手填
    res = f"✅已处理({verdict}" + (f"·{reason}" if reason else "") + ")"
    lines.insert(sep + 1, f"| {title_out} | {date_str} | {res} |")
    _p.write_text("\n".join(lines), encoding="utf-8")
    _ph = [h for h in _KEY_HITS if h[0] == "prefix"]
    if _ph:
        print("⚠️ 命中形态=前缀（匹配长度 %d 字·两条不同候选共享前缀时会误闭他人真候选；"
              "✅DO 改传全长标题复核）·样本：%s" % (_ph[0][2], _ph[0][1]), file=sys.stderr)
    print(f"✅ 裁决已落状态通道：{title_out[:40]} → {res}（{date_str}）")
    return 0


def _close_cli(argv):
    if "--close-title-file" in argv:              # 长标题走文件，避免 shell 引号地狱
        tp = Path(argv[argv.index("--close-title-file") + 1])
        title = tp.read_text(encoding="utf-8").strip()
    else:
        i = argv.index("--close")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print('error: --close 后须紧跟完整标题（或用 --close-title-file <路径>）', file=sys.stderr)
            return 2
        title = argv[i + 1]
    g = lambda k, d="": (argv[argv.index(k) + 1] if k in argv else d)
    return close_candidate(title, g("--verdict", "不记"), g("--reason"),
                           g("--file") or None)


def main():
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"=== 错误候选挖掘器 {today_str} ===")

    # 扫描系统日志
    candidates = scan_system_logs()
    print(f"📊 扫描近{SCAN_DAYS}天系统日志，发现 {len(candidates)} 条错误候选（≤{MAX_CANDIDATES}）")

    for i, c in enumerate(candidates, 1):
        print(f"  {i}. [{c['priority']}] {c['title'][:50]} ({c['source']})")

    # 加载已处理的候选（幂等·手动标记）
    processed = load_pending()

    # L3自动回写：扫描成长箱最近7天新写入的错误条目，与待确认候选模糊匹配，自动标记已处理
    recent_growthbox = scan_recent_growthbox_entries()
    auto_processed = auto_mark_processed(candidates, recent_growthbox)
    if auto_processed:
        print(f"🔄 L3自动回写：发现 {len(auto_processed)} 条候选已在成长箱中写入，自动标记已处理")
        for title in auto_processed:
            print(f"  - {title[:50]}")
    processed = processed | auto_processed  # 合并手动已处理和自动已处理

    new_candidates = [c for c in candidates if not already_closed(c["title"], processed)]
    print(f"📋 其中 {len(new_candidates)} 条为新候选（{len(candidates)-len(new_candidates)} 条已处理）")

    # 生成待确认文件
    content = generate_pending_content(candidates, processed)
    content = merge_human_notes(content, extract_human_notes(str(PENDING_FILE)))  # 人工裁决跨重写存活
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(content, encoding="utf-8")
    print(f"✅ 待确认文件已更新: {PENDING_FILE}")

    print(f"=== 挖掘器运行完成 ===")
    return 0

def _mk_fixture():
    """造一份最小待确认文件到临时目录，⛔ 不碰生产文件（夹具隔离·kb-index-guard 同源纪律）"""
    import tempfile
    d = tempfile.mkdtemp(prefix="ecm_fixture_")
    f = Path(d) / "错误候选待确认.md"
    f.write_text("# t\n\n## 待确认候选\n\n| # | 优先级 | 错误标题 | 摘要 | 来源 | 状态 | 操作 |\n"
                 "|:-:|:-:|--|--|--|:-:|--|\n| 1 | \U0001F534高(100) | 甲标题 | s | 未知 | \u23F3待确认 | x |\n\n"
                 "## 已处理候选（保留7天用于追溯）\n\n| 错误标题 | 处理日期 | 处理结果 |\n"
                 "|---------|---------|---------|\n| \u2014 | \u2014 | 暂无已处理候选 |\n", encoding="utf-8")
    return f


def _close_probes():
    """返回四例结果 dict：正例/负例/幂等/形状防护"""
    f = _mk_fixture()
    r = {}
    r["F1_正例"] = (close_candidate("甲标题", "不记", "miner粗筛误报", str(f)) == 0
                    and "✅已处理(不记·miner粗筛误报)" in f.read_text(encoding="utf-8")
                    and "甲标题" in load_pending(str(f)))
    f2 = _mk_fixture(); b2 = f2.read_bytes()
    r["F2_负例"] = (close_candidate("查无此标题", path=str(f2)) == 1 and f2.read_bytes() == b2)
    f3 = _mk_fixture()
    close_candidate("甲标题", path=str(f3)); close_candidate("甲标题", path=str(f3))
    r["F3_幂等"] = sum(1 for l in f3.read_text(encoding="utf-8").split("\n")
                       if l.startswith("| 甲标题 |")) == 1
    f4 = _mk_fixture(); b4 = f4.read_bytes()
    # v3.4.1 契约变更：换行才是形状杀手；竖线改走 F7 正例（不再当负例）
    r["F4_形状防护"] = (close_candidate("含\n换行标题", path=str(f4)) == 2 and f4.read_bytes() == b4)
    # F7 生产样本正例（QCN-20261011-027）：表格内标题带转义竖线 → close 须可达且写出不破行形状
    f7 = _mk_fixture()
    s7 = f7.read_text(encoding="utf-8").replace("| 甲标题 |", "| 端X \\| 归位标题 |")
    f7.write_text(s7, encoding="utf-8")
    rc7 = close_candidate("端X | 归位标题", path=str(f7))
    row7 = [l for l in f7.read_text(encoding="utf-8").split("\n") if l.startswith("| 端X")]
    p7 = re.split(r"(?<!\\)\|", row7[0])[1:-1] if row7 else []
    r["F7_竖线转义正例"] = (rc7 == 0 and len(p7) == 3 and p7[0].strip() == "端X \\| 归位标题")
    # F8 读侧追洞（v3.4.2）：转义形态写入后，load_pending 的跳过集键必须＝原始标题（不被 \| 截断）
    close_candidate("端X | 归位标题", path=str(f7))
    # v3.4.3：F8 判据改走唯一入口（跳过集现存表格原文，字面 `in` 属旧契约）
    r["F8_读侧跳过集键完整"] = already_closed("端X | 归位标题", load_pending(str(f7)))
    # F9 端到端（v3.4.3·QCN-20261011-028）：表格里只存 40 字截断格，用它出清后，
    #     扫描侧拿全长标题仍须判为已处理（旧版此处 rc=0 却复活＝假绿）
    f9 = _mk_fixture()
    long9 = "端Y | 超长归位标题" + "续" * 30
    f9.write_text(f9.read_text(encoding="utf-8").replace("| 甲标题 |", "| %s |" % cell(long9, 40)),
                  encoding="utf-8")
    close_candidate(cell(long9, 40), path=str(f9))
    r["F9_端到端截断出清真生效"] = already_closed(long9, load_pending(str(f9)))
    # F10 负例（防放宽）：两条都全长、仅前缀相同的候选不得互认；真截断（短为长之前缀）才互认
    r["F10_前缀下限防误闭"] = (key_match("abcdefghijklmnopqrstuAAA",
                                        "abcdefghijklmnopqrstuBBB") is None
                              and key_match("abcdefghijklmnopqrstu",
                                            "abcdefghijklmnopqrstuXXXX") == "prefix"
                              and key_match("short-A", "short-B") is None
                              and KEY_MIN_PREFIX >= 20)
    # F5：表格里只存截断标题（cell(title,40)）时，close 全标题仍须命中（2026-10-11 生产实测逮出的形态）
    f5 = _mk_fixture()
    long_t = "甲标题" + "很长" * 30
    s5 = f5.read_text(encoding="utf-8").replace("| 甲标题 |", f"| {cell(long_t, 40)} |")
    f5.write_text(s5, encoding="utf-8")
    r["F5_截断形态"] = close_candidate(long_t, path=str(f5)) == 0
    # F6 防误闭（本轮实测缺陷）：标题字样只出现在**别的行的摘要格**时，必须 rc1 且不写
    f6 = _mk_fixture()
    s6 = f6.read_text(encoding="utf-8").replace("| 甲标题 |", "| 无关标题 |").replace(
        " s | 未知", " 甲标题的字样出现在摘要里 | 未知")
    f6.write_text(s6, encoding="utf-8"); b6 = f6.read_bytes()
    r["F6_防误闭"] = (close_candidate("甲标题", path=str(f6)) == 1 and f6.read_bytes() == b6)
    return r


def _suite():
    """夹具集（cell 与真产物各测一遍）：返回失败项列表。拆成函数是为了能被**真变异**复用。"""
    bad = []
    cases = [
        ("C1 换行不带进表格行", "\n" not in cell("T0校对\n铁律版收口\n- **完成**：17:41", 50)),
        ("C2 竖线被转义不吃列", cell("a|b|c", 50) == "a\\|b\\|c"),
        ("C3 截断不留半个转义对", not cell("x" * 49 + "|y", 50).endswith("\\")),
        ("C4 正常短文本原样通过", cell("普通标题", 40) == "普通标题"),
        # v3.3.0 判据夹具（2026-09-22·堵点B 修据配套）
        ("D1 否定形态「没有问题」→ 不报", is_error_candidate({"title": "安装包没有问题", "content": ""})[0] is False),
        ("D2 成功形态「对账全 0 / 零问题」→ 不报", is_error_candidate({"title": "出包范围五向对账全 0（零问题交付）", "content": ""})[0] is False),
        ("D3 自纠类「自纠一处口径错误」→ 不报", is_error_candidate({"title": "机械口径复核 + 自纠一处口径错误", "content": ""})[0] is False),
        ("D4 真错误「遗漏/未检查」→ 仍报（防过度收窄）", is_error_candidate({"title": "端清单遗漏5端未检查", "content": ""})[0] is True),
        # v3.4.0 --close 回写通道夹具（卡A 步1·正/负/幂等/形状四例）
        ("F1 close 正例：裁决落已处理表且状态通道可读回", _close_probes()["F1_正例"]),
        ("F2 close 负例：未命中必须 rc1 且文件零改动", _close_probes()["F2_负例"]),
        ("F3 close 幂等：同标题两次只落一行", _close_probes()["F3_幂等"]),
        ("F4 close 形状防护：标题含换行 rc2 且零改动", _close_probes()["F4_形状防护"]),
        ("F7 close 竖线转义正例：现存转义形态可达且列数=3", _close_probes()["F7_竖线转义正例"]),
        ("F8 读侧跳过集键完整（转义形态出清真生效）", _close_probes()["F8_读侧跳过集键完整"]),
        ("F9 端到端：表内截断形态出清后扫描侧全长标题仍判已处理", _close_probes()["F9_端到端截断出清真生效"]),
        ("F10 前缀下限防误闭：两条全长不互认·真截断才互认", _close_probes()["F10_前缀下限防误闭"]),
        ("F5 close 截断形态：表格存 cell(title,40) 时全标题仍命中", _close_probes()["F5_截断形态"]),
        ("F6 close 防误闭：标题只在别行摘要格出现→rc1 且零改动", _close_probes()["F6_防误闭"]),
    ]
    globals()["_SUITE_TOTAL"] = len(cases)          # 夹具总数动态化（⛔不硬编码——加夹具后报告数须自跟）
    for name, ok in cases:
        print(("  ✅ " if ok else "  ❌ ") + name)
        if not ok:
            bad.append(name)
    content = generate_pending_content(
        [{"title": "T0校对续轮\n铁律版收口", "summary": "- **完成**：17:41\n- **类型**：校对修复（机械）",
          "priority": 60, "source": "系统日志\n2026-09-16"}], set())
    rows = [l for l in content.split("\n") if l.startswith("| ") and "待确认" in l]
    widths = {len([c for c in re.split(r"(?<!\\)\|", l)[1:-1]]) for l in rows}
    ok_e2e = bool(rows) and widths == {7}
    print(("  ✅ " if ok_e2e else "  ❌ ") + f"E2E 真产物表格区 {len(rows)} 行·列数集合={sorted(widths)}（应为 [7]·⛔跨行）")
    if not ok_e2e:
        bad.append("E2E")
    return bad


def _self_test():
    """出厂动作按 §3.9：先跑**变异**（把 cell 换成修复前的直切片），夹具必须转红；再跑正例。
    ⛔不拿"证明字符串里有换行"这类假变异冒充自证（§3.9 红线点名的形态）。"""
    print("── 正例（线上本体）")
    bad = _suite()
    print("── 变异体2（_CLOSE_STRICT=False＝还原「未命中也照写」的静默旧行为）")
    globals()["_CLOSE_STRICT"] = False
    try:
        p2 = _close_probes()
        f2_rev = p2["F2_负例"]           # 关掉严格位后，未命中应变成"写进去且rc0"→ 该例必须转红
    finally:
        globals()["_CLOSE_STRICT"] = True
    print("── 变异体（cell 置假＝还原修复前的直切片行为）")
    live = globals()["cell"]
    globals()["cell"] = lambda text, limit=50: str(text)[:limit]
    try:
        bad_mut = _suite()
    finally:
        globals()["cell"] = live
    flipped = bool(bad_mut) and (not bad) and (not f2_rev)   # 变异2 下 F2 转红才算两条判据各自可证伪
    print(f"  变异后失败项={sorted(bad_mut) or '（无＝判据已死）'}｜正例失败项={sorted(bad) or '无'}")
    print("MUT:" + ("OK" if flipped else "FAIL") +
          f" 判据各自可证伪={flipped}（变异体＝cell直切片＋strict关闭·夹具 {globals().get('_SUITE_TOTAL', 0) - len(bad)}/{globals().get('_SUITE_TOTAL', 0)}）")
    return 1 if bad else 0
USAGE = """usage: error_candidate_miner.py [--self-test | --close "<标题>" [--verdict 不记] [--reason <理由>] [--file <路径>] [--close-title-file <路径>]]
  无参数＝每日 07:38 launchd 全量挖掘并写 错误候选待确认.md（会写生产账本）
  v3.4.1 起：--help 只打印用法，未知 flag 拒绝（rc=2）——原因是旧分发对未识别 flag 无拒绝分支，
  把 --help 当安全探针＝直接执行一次全量扫描并写账本（QCN-20261011-026 实证）。"""


def _cli_guard(argv):
    """flag 白名单分发：未知 flag 拒执行（v3.4.1·QCN-20261011-026）。"""
    known = {"--self-test", "--close", "--close-title-file", "--verdict", "--reason",
             "--file", "--help", "-h"}
    unknown = [a for a in argv[1:] if a.startswith("-") and a not in known]
    if unknown:
        print(f"error: 未识别的 flag {unknown}——拒绝执行（本脚本无参数即全量挖掘写盘）", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    import sys
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(USAGE); sys.exit(0)
    _rc = _cli_guard(sys.argv)
    if _rc:
        sys.exit(_rc)
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    if "--close" in sys.argv:
        sys.exit(_close_cli(sys.argv))
    exit(main())
