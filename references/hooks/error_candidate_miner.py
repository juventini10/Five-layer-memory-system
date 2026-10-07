#!/usr/bin/env python3
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

SYSTEM_LOG_DIR = Path.home() / "~/[记忆共享中心]/工作日志/系统日志"
PENDING_FILE = Path.home() / "~/[记忆共享中心]/成长箱/错误候选待确认.md"

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


def load_pending() -> dict:
    """加载待确认文件，返回已处理的候选标题集合（用于幂等）"""
    processed = set()
    if not PENDING_FILE.exists():
        return processed

    content = PENDING_FILE.read_text(encoding="utf-8")
    # 已处理的候选标记为 ✅已处理
    for line in content.split("\n"):
        if "✅已处理" in line:
            title_match = re.search(r'\|\s*(.+?)\s*\|', line)
            if title_match:
                processed.add(title_match.group(1).strip())

    return processed


def scan_recent_growthbox_entries() -> list:
    """扫描成长箱learnings/目录，提取最近7天新写入的错误条目标题（用于L3自动回写）"""
    learnings_dir = Path.home() / "~/[记忆共享中心]/成长箱/learnings"
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

    unprocessed = [c for c in candidates if c["title"] not in processed]

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

    new_candidates = [c for c in candidates if c["title"] not in processed]
    print(f"📋 其中 {len(new_candidates)} 条为新候选（{len(candidates)-len(new_candidates)} 条已处理）")

    # 生成待确认文件
    content = generate_pending_content(candidates, processed)
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(content, encoding="utf-8")
    print(f"✅ 待确认文件已更新: {PENDING_FILE}")

    print(f"=== 挖掘器运行完成 ===")
    return 0

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
    print("── 变异体（cell 置假＝还原修复前的直切片行为）")
    live = globals()["cell"]
    globals()["cell"] = lambda text, limit=50: str(text)[:limit]
    try:
        bad_mut = _suite()
    finally:
        globals()["cell"] = live
    flipped = bool(bad_mut) and (not bad)
    print(f"  变异后失败项={sorted(bad_mut) or '（无＝判据已死）'}｜正例失败项={sorted(bad) or '无'}")
    print("MUT:" + ("OK" if flipped else "FAIL") +
          f" 判据各自可证伪={flipped}（变异体 1 个·夹具 {globals().get('_SUITE_TOTAL', 0) - len(bad)}/{globals().get('_SUITE_TOTAL', 0)}）")
    return 1 if bad else 0
if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    exit(main())
