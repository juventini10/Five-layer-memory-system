#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
note_validator.py — 读书助手（素裁）产出物合规「规则单源」

职责（单一真相源，被 生成即自检② 与 产物机检③ 共用）：
- NOTE_FIELDS / CARD_FIELDS：定义「合规的笔记 / 卡片」frontmatter 长什么样（字段+必填+约束）。
- CARD_BODY_MAX / check_body_length：定义「卡片正文字数」合规上限（600·机检真源=本常量·config.yaml=人类可读投影·#8真源反转改数两处同步）——
  生成即自检（写卡前 check_body_length）与产物机检（lint_path 扫 body）双生效，防 34/39 超限事故复发。
- build_*_frontmatter：从单源字段spec构建 frontmatter（生成器不再硬编码字段集）。
- validate_note / validate_card：校验任意 frontmatter dict 是否合规（返回违规清单）。
- parse_frontmatter / dump_frontmatter：最小 YAML frontmatter 解析/序列化（无外部依赖）。
  **本 Skill 唯一的 frontmatter 解析器**——dedup_recall.py 等脚本一律 import 本函数，
  ⛔DO NOT 另起炉灶写第二份（v4.2.0 前 dedup_recall.py 曾自带一份，两份逻辑漂移）。
- lint_path：扫描目录内 .md 文件，按 type 派发校验，输出机检报告。

设计依据：
- 《文件格式规范》(⛔不锚版本#142) §三 通用7必填 + §八 Schema 注册表
- 《笔记schema》v1.0.0（层3，note 类型）
- 《读书卡片schema》v1.3.1（层3，reading-card 类型，含立场扩展层 + source_type 泛化 + trigger_scene + source_count）

条件必填逻辑（2026-08-07 Wave 0.2 扩展）：
- source_type =book → 书卡规则：book/book_author 必填（source_type 已收紧为必填·Wave 2.0）
- source_type 存在且 ≠book → 文章卡规则：source_title/source_author 必填，book/book_author 选填

类型契约（v4.2.0 · H3 修复）：
- YAML 标量在 parse 时还原为 Python 原生类型：未加引号的 true/false → bool，
  未加引号的纯整数 → int，其余 → str；**加引号的一律保持 str**（YAML 语义：'true' 是字符串）。
- dump 反向对称：bool → true/false（小写），保证 parse→dump→parse 往返不变。
- 因此校验器可以直接写 isinstance(v, bool) 这类原生类型断言，
  「内存 dict 路径（生成即自检②）」与「文件解析路径（产物机检③）」类型一致。
- ⛔DO NOT 改回「校验器容忍字符串 'true'」的写法——原因是类型转换属于 I/O 边界职责，
  塞进校验器会让每个非字符串字段都要重复容错，且丢失 YAML 的引号语义。

⛔DO NOT 在 generate_note / SKILL.md 模板里再硬编码一套字段集——
所有「合规长什么样」的定义只在此文件，改规则改这一处即可（单一来源原则）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
import sys

# 标准 yaml：可选依赖（环境通常可用）。用于 _yaml_hardcheck 的权威解析裁判，
# 避免自写规则产生假阳性（如中文冒号在值中间其实合法）。不可用时降级到只查
# 裸 related 双链（最确定根因）。try/except 保证"无 yaml 也不破窗"。
try:
    import yaml as _yaml_mod
    _YAML_AVAILABLE = True
except Exception:
    _yaml_mod = None
    _YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# 单源字段定义
# 每个字段 = (key, required: bool, validator: callable|None)
# validator 返回 True 表示值合规；None 表示只检查「存在」即可。
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_STATUS_SET = ("active", "draft", "deprecated")
_READING_STATUS_SET = ("L1", "L2", "L3", "L4")
_TEMPLATE_TYPE_SET = ("A", "B")
_CARD_TYPE_SET = ("概念", "方法", "模式", "反直觉", "数据")
_SOURCE_TYPE_SET = ("book", "paper", "article-long", "article-short", "thread")

# --- 正文字数上限（2026-08-17 · 定值式防错·防超限事故复发）---
# 真源=本常量·config.yaml「永久卡片·每张卡片正文 ≤600字（含原文依据/AI理解/应用场景三段）」为人类可读投影（#8反转·改数两处同步）
# ⛔DO NOT 改此处不同步 config.yaml——两处必须一致，机检按本常量拦截。
CARD_BODY_MAX = 600

# --- schema 版本单源（v4.2.0）---
# 生成器写哪个版本、校验器认哪些版本，都从这里取。
# ⛔DO NOT 在 build_*_frontmatter 里再写一遍版本字面量——原因是 v4.1.0 实测过：
# builder 停在 v1.1.0 而校验器已到 v1.3.0，builder 产出物过不了自己的 validate_card。
NOTE_SCHEMA_VERSION = "笔记schema v1.0.0"
CARD_SCHEMA_VERSION = "读书卡片schema v1.3.4"
CARD_SCHEMA_ACCEPTED = (
    "读书卡片schema v1.0.0", "读书卡片schema v1.1.0", "读书卡片schema v1.2.0",
    "读书卡片schema v1.2.1", "读书卡片schema v1.3.0", "读书卡片schema v1.3.1", CARD_SCHEMA_VERSION,  # v1.3.1=2026-10-15 前现行版·存量合法卡兼容
)  # v1.3.0 存量卡经接受表继续合法（v1.3.1 = 追加可选 verified·2026-09-01 清零批#11）

# --- 题库 schema 版本单源（v4.7.0 · 跨Skill消费边）---
# 读书助手生成 → Shall We Talk「阅读复习模式」消费（抽due题→出题→判定→回写间隔参数）。
QUIZ_SCHEMA_VERSION = "题库schema v1.0.0"

# 题库：frontmatter 必填（body 每题段由 validate_quizbank 单独校验）
QUIZ_FIELDS = [
    ("title", True, lambda v: bool(str(v).strip())),
    ("type", True, lambda v: v == "quiz-bank"),
    ("version", True, lambda v: bool(str(v).strip())),
    ("date", True, lambda v: bool(_DATE_RE.match(str(v)))),
    ("source_title", True, lambda v: bool(str(v).strip())),
    ("source_type", True, lambda v: v in _SOURCE_TYPE_SET),
    ("complies_with", True, lambda v: v == QUIZ_SCHEMA_VERSION),
    ("question_count", True, lambda v: isinstance(v, int) or str(v).strip().isdigit()),
]

# 笔记：通用7必填 + 笔记schema 扩展（author=维护者，book_author=书作者）
NOTE_FIELDS = [
    ("title", True, lambda v: bool(str(v).strip())),
    ("type", True, lambda v: v == "note"),
    ("status", True, lambda v: v in _STATUS_SET),
    ("version", True, lambda v: bool(str(v).strip())),
    ("date", True, lambda v: bool(_DATE_RE.match(str(v)))),
    ("summary", True, lambda v: 0 < len(str(v).strip()) <= 40),
    ("source", True, lambda v: bool(str(v).strip())),
    ("author", True, lambda v: bool(str(v).strip())),          # 维护者（你/皮叔），非书作者
    ("book", False, None),
    ("book_author", False, None),                              # 书作者，独立于 author
    ("publisher", False, None),
    ("template_type", True, lambda v: v in _TEMPLATE_TYPE_SET),
    ("category", False, None),
    ("tags", False, None),
    ("reading_status", True, lambda v: v in _READING_STATUS_SET),
    ("last_updated", False, None),
    ("complies_with", True, lambda v: v == NOTE_SCHEMA_VERSION),
    # --- 可信元数据（文件格式规范 · 原则 8 · ⛔不锚版本#142 · optional）---
    ("generated", False, lambda v: bool(str(v).strip())),
]

# 卡片：通用7必填 + 卡片扩展（type=reading-card）
# 2026-08-07 Wave 0.2：book/book_author 改为字段级 optional，
# 条件必填逻辑由 validate_card() 根据 source_type 动态判定。
CARD_FIELDS = [
    ("title", True, lambda v: bool(str(v).strip())),
    ("type", True, lambda v: v == "reading-card"),
    ("status", True, lambda v: v in _STATUS_SET),
    ("version", True, lambda v: bool(str(v).strip())),
    ("date", True, lambda v: bool(_DATE_RE.match(str(v)))),
    ("summary", True, lambda v: 0 < len(str(v).strip()) <= 40),
    ("source", True, lambda v: bool(str(v).strip())),
    ("author", True, lambda v: bool(str(v).strip())),          # 维护者
    ("book", False, lambda v: bool(str(v).strip())),           # 条件必填→validate_card
    ("book_author", False, lambda v: bool(str(v).strip())),    # 条件必填→validate_card
    ("card_id", True, lambda v: bool(re.fullmatch(r"\S+-卡片\d+", str(v)))),  # v1.3.4 禁空白+标准尾缀（2026-10-15 D3根治批：全池1272张已统一·负例证过才升档#S243）
    ("kb_no", True, lambda v: bool(re.fullmatch(r"#Z\d{4}", str(v)))),  # v1.3.2 必填·Z族四位数·唯一性由 assign_kb_no.py --sync 对账保证（2026-10-13 立法轮遗留②）
    ("topic", True, lambda v: bool(str(v).strip())),
    ("card_type", True, lambda v: v in _CARD_TYPE_SET),
    ("reading_status", True, lambda v: v in _READING_STATUS_SET),
    ("template_type", True, lambda v: v in _TEMPLATE_TYPE_SET),
    ("complies_with", True, lambda v: v in CARD_SCHEMA_ACCEPTED),
    # --- 源泛化字段（schema v1.3.0 · 2026-08-07 Wave 0.2 新增）---
    ("source_type", True, lambda v: v in _SOURCE_TYPE_SET),    # Wave 2.0 收紧：回填完成后必填（Qoder CN 2026-08-07）
    ("source_title", False, lambda v: bool(str(v).strip())),   # 条件必填→validate_card
    ("source_author", False, lambda v: bool(str(v).strip())),  # 条件必填→validate_card
    ("source_url", False, lambda v: bool(str(v).strip())),
    ("source_date", False, lambda v: bool(_DATE_RE.match(str(v)))),
    ("source_count", False, lambda v: str(v).isdigit() and int(str(v)) >= 1),
    ("trigger_scene", False, lambda v: bool(str(v).strip())),
    ("related", False, None),                                   # 双链数组或字符串
    # verified（schema v1.3.1 · 2026-09-01 清零批#11）：CONFLICT 立场闭环的人工复核载体——
    # CONFLICT 新卡落 unverified，你/成长箱复核通过后改 verified（dedup-merge-gate ⑥ 对齐）。
    ("verified", False, lambda v: v in ("unverified", "verified")),
    # --- 可信元数据（文件格式规范 · 原则 8 · ⛔不锚版本#142 · 全部 optional）---
    # generated: AI 蒸馏产物自动携带，标识生产者+时间。
    # verified: 你复核后手动补（多行 YAML 数组格式，trust_of 解析含 human: 前缀 → human-reviewed）。
    # ⛔DO NOT 用内联数组 [{by:..., at:...}]——最小解析器不支持嵌套对象，会按逗号拆碎。
    ("generated", False, lambda v: bool(str(v).strip())),
    # --- 检索键（schema v1.2.0 定为必填 · v4.2.0 补进机器真源）---
    # 为什么必填：dedup_recall.py 的候选条件 = category 归一相等 且 tags 归一交集非空。
    # 缺任一 → 该卡永远召不回 → 去重合并门(Step 2.0)对它静默失效。
    # ⛔DO NOT 降回选填——原因是去重门的可靠性直接依赖这两个字段存在。
    ("category", True, lambda v: bool(str(v).strip())),
    ("tags", True, lambda v: bool(v) if isinstance(v, list) else bool(str(v).strip())),
]

# 立场扩展字段（全部 optional，v1.1.0 · 单态渐进模型）
# 来源：读书卡片schema v1.1.0 §六 立场扩展层 + 学习引擎 04 立场依据卡 schema
_CYNEFIN_SET = ("繁杂", "复杂", "混沌")
_STANCE_COMPLETENESS_SET = ("shallow", "deep")

STANCE_FIELDS = [
    # 浅立场（1次引用/碰撞信号起点）
    ("stance_main_contradiction", False, lambda v: bool(str(v).strip())),
    ("stance_position", False, lambda v: bool(str(v).strip())),
    ("stance_overturned", False, lambda v: bool(str(v).strip())),
    # 深立场（再引用/碰撞触发）
    ("stance_evidence_chain", False, lambda v: bool(str(v).strip())),
    ("stance_yield_condition", False, lambda v: bool(str(v).strip())),
    ("stance_red_line", False, lambda v: bool(str(v).strip())),
    ("stance_cynefin", False, lambda v: v in _CYNEFIN_SET),
    ("stance_steelman", False, lambda v: bool(str(v).strip())),
    ("stance_evidence_levels", False, lambda v: bool(str(v).strip())),
    # 碰撞溯源
    ("stance_source_cards", False, lambda v: bool(str(v).strip())),
    # 反证推翻
    ("stance_overturned_by", False, lambda v: bool(str(v).strip())),
    # 完成度标记
    ("has_stance", False, lambda v: isinstance(v, bool)),
    ("stance_completeness", False, lambda v: v in _STANCE_COMPLETENESS_SET),
]

CARD_FIELDS.extend(STANCE_FIELDS)

# 禁用字段（历史残留，违反《文件格式规范》§3.5#4 字段名一致）
FORBIDDEN_KEYS = ("date_created", "created_date", "created", "updated", "updated_date")


# ---------------------------------------------------------------------------
# 构建（单源 → frontmatter dict）
# ---------------------------------------------------------------------------

def build_note_frontmatter(book_name, book_info, today, summary=None,
                           title=None, source=None):
    """从 NOTE_FIELDS 单源构建笔记 frontmatter。字段集只此一处定义。

    v4.10.0 现代化（清零批#10）：精华摘要场景传 title=《书名》精华摘要 + source=输入路径；
    缺省保持 batch_extract 旧口径（title=《书名》读书笔记）。⛔ 精华/笔记 frontmatter
    一律走本 builder + dump_frontmatter（2026-09-01 起"⛔手写 frontmatter"禁令全覆盖）。
    """
    book_info = book_info or {}
    if summary is None:
        summary = f"《{book_name}》核心观点与知识关联"
        if len(summary) > 40:
            summary = f"《{book_name}》读书笔记"[:40]
    tags = book_info.get("tags", ["读书笔记"])
    if isinstance(tags, list):
        tags = tags
    else:
        tags = [str(tags)]
    fm = {
        "title": title or f"《{book_name}》读书笔记",
        "type": "note",
        "status": "active",
        "version": "v1.0.0",
        "date": today,
        "summary": summary,
        "source": source or f"batch_extract_books.py 生成（输入: {book_name}）",
        "author": "你",
        "book": book_name,
        "book_author": book_info.get("author", "未知"),
        "publisher": book_info.get("publisher", ""),
        "template_type": "A",
        "category": book_info.get("category", "未知"),
        "tags": tags,
        "reading_status": "L1",
        "last_updated": today,
        "complies_with": NOTE_SCHEMA_VERSION,
        "generated": f"sucair · {today}",
    }
    issues = validate_note(fm)
    if issues:
        raise ValueError(
            "build_note_frontmatter 产出不合规（生成器与校验器不同源即为 bug）：\n  - "
            + "\n  - ".join(issues)
        )
    return fm


def build_quizbank_frontmatter(source_title, source_type, question_count,
                               today, title=None):
    """从 QUIZ_FIELDS 单源构建题库 frontmatter（v4.10.0 新增·清零批#10）。

    quiz-bank 现代化禁令与读书卡片同规：⛔手写 frontmatter，✅DO 走本 builder。
    question_count 必须与实际出题数一致（写入前由调用方核对 ## Q 段数，
    validate_quizbank 机检兜底一致性）。
    """
    fm = {
        "title": title or f"{source_title}题库",
        "type": "quiz-bank",
        "version": "v1.0.0",
        "date": today,
        "source_title": source_title,
        "source_type": source_type,
        "complies_with": QUIZ_SCHEMA_VERSION,
        "question_count": int(question_count),
    }
    issues = _validate(fm, QUIZ_FIELDS, "quiz-bank")
    if issues:
        raise ValueError(
            "build_quizbank_frontmatter 产出不合规（生成器与校验器不同源即为 bug）：\n  - "
            + "\n  - ".join(issues)
        )
    return fm


def build_card_frontmatter(book_name, book_info, card_n, title, topic,
                           card_type, source_quote, today, summary=None,
                           source_type="book", category=None, tags=None,
                           source_title=None, source_author=None,
                           source_url=None, source_date=None, trigger_scene=None,
                           related=None, kb_no=None):
    """从 CARD_FIELDS 单源构建卡片 frontmatter（schema v1.3.0 全字段）。

    v4.2.0 修复（H2）：原实现停在 schema v1.1.0 且不产 source_type/category/tags，
    产出物过不了本文件自己的 validate_card——「规则单源」名存实亡。

    Poka-Yoke（防误层）：返回前自校验，不合规直接抛 ValueError。
    ⛔DO NOT 去掉这个自校验改成「构建完再由调用方检查」——原因是那样又回到
    「可能构建出脏数据、只是希望有人记得检查」，防误层的定义是让错误无法发生。
    """
    book_info = book_info or {}
    is_book = (source_type == "book")
    if summary is None:
        summary = f"《{book_name}》·{title}"[:40]
    resolved_author = book_info.get("author", "未知")
    _bn = re.sub(r"\s+", "", book_name)  # v1.3.3 card_id 源头去空白
    fm = {
        "title": title,
        "type": "reading-card",
        "status": "active",
        "version": "v1.0.0",
        "date": today,
        "summary": summary,
        "source": source_quote or f"《{book_name}》",
        "author": "你",
        "source_type": source_type,
        "source_title": source_title or (f"《{book_name}》" if is_book else book_name),
        "source_author": source_author or resolved_author,
        "card_id": (f"《{_bn}》-卡片{card_n}" if is_book else f"{_bn}-卡片{card_n}"),  # v1.3.3 源头去空白（_bn=book_name 去空白）

        "topic": topic,
        "card_type": card_type,
        "reading_status": "L1",
        "template_type": "A",
        # category / tags 是去重门(Step 2.0)的检索键，必须显式传入，⛔DO NOT 兜底填"未分类"。
        # 留空 → 下面的 Poka-Yoke(validate_card) 会直接抛 ValueError，由调用方补数据，
        # 而不是产出一份"字段在但无意义"的脏卡片（那样去重门对它静默失效）。
        "category": category,
        "tags": tags,
        "complies_with": CARD_SCHEMA_VERSION,
        "generated": f"sucair · {today}",
    }
    if is_book:
        # book/book_author 是 source_type=book 时的条件必填（兼容别名）
        fm["book"] = book_name
        fm["book_author"] = resolved_author
    if kb_no:
        fm["kb_no"] = kb_no  # v1.3.2 双字段制：card_id 人读家规 + kb_no 机器索引别名
    for k, v in (("source_url", source_url), ("source_date", source_date),
                 ("trigger_scene", trigger_scene)):
        if v:
            fm[k] = v
    # related：双链指针（list/tuple/单条均可传入）。
    # ⛔DO NOT 在调用方手写 `related: [[A]] [[B]]` 裸双链——那是本次 326 卡
    # YAML 非法的根因（YAML 把 [[ 当非法内联列表）。必须走本 builder，
    # 规范形=字符串 `[[A]] [[B]]`（dict 内即定形），由 dump_frontmatter 序列化为
    # 合法 `related: "[[A]] [[B]]"`——build→dump→parse 往返恒等（2026-09-01 幂等加固）。
    if related:
        links = list(related) if isinstance(related, (list, tuple)) else [related]
        fm["related"] = " ".join(str(x) for x in links)

    issues = validate_card(fm)
    if issues:
        raise ValueError(
            "build_card_frontmatter 产出不合规（生成器与校验器不同源即为 bug）：\n  - "
            + "\n  - ".join(issues)
        )
    return fm


# ---------------------------------------------------------------------------
# 解析 / 序列化（最小实现，无外部依赖）
# ---------------------------------------------------------------------------

_INT_RE = re.compile(r"^-?\d+$")


def _coerce_scalar(raw, was_quoted):
    """YAML 标量 → Python 原生类型（v4.2.0 · H3 根因修复）。

    加引号的一律保持 str —— YAML 语义：'true' 是字符串，true 是布尔。
    ⛔DO NOT 把这段搬进校验器做「容忍字符串 'true'」——原因是类型转换属于
    I/O 边界职责，塞进校验层会让每个非字符串字段都要重复容错。
    """
    if was_quoted:
        return raw
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~", ""):
        return None if low != "" else ""
    if _INT_RE.match(raw):
        return int(raw)
    return raw


def parse_frontmatter(text):
    """返回 (frontmatter_dict, body_str)。无 YAML 块则返回 ({}, text)。

    本 Skill 唯一的 frontmatter 解析器（dedup_recall.py 等一律 import 本函数）。
    支持：行内数组 `tags: [a, b]`、YAML 多行数组 `tags:\\n  - a\\n  - b`、
    标量类型还原（bool/int，引号保护）。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm = {}
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    current_key = None
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # YAML 多行数组项：`  - value`，归并进上一个键
        if stripped.startswith("- ") and current_key is not None:
            item = stripped[2:].strip().strip("'\"")
            prev = fm.get(current_key)
            if isinstance(prev, list):
                prev.append(item)
            elif prev in ("", None):
                fm[current_key] = [item]
            else:
                fm[current_key] = [prev, item]
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        current_key = key
        # 剥离 YAML 引号包裹（'2026-06-13' → 2026-06-13），并记住它曾被引号包裹
        was_quoted = len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"')
        if was_quoted:
            val = val[1:-1].replace('\\"', '"')  # 与 dump related 引号转义对称（2026-09-01 复核N2）
        if not was_quoted and val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")] if inner else []
        else:
            fm[key] = _coerce_scalar(val, was_quoted)
    body = "\n".join(lines[end + 1:])
    return fm, body


def dump_frontmatter(fm):
    """dict → YAML frontmatter 文本（不含 --- 包裹行）。

    与 parse_frontmatter 对称：bool → true/false 小写，保证 parse→dump→parse 往返不变。
    ⛔DO NOT 用 f"{k}: {v}" 直接序列化 bool——原因是 Python 的 str(True)=="True"，
    写进 YAML 后再解析回来会变成字符串 "True"，往返即失真。

    related 特判（2026-08-24 修·2026-09-01 幂等加固）：双链值如 ["[[A]]", "[[B]]"] 必须序列化为
    **字符串** `related: "[[A]] [[B]]"`，⛔DO NOT 走 list 行内 `[...]`——原因是
    [[...]] 是 Obsidian 双链语法，再包一层 [] 会变成 [[[...]]] 破坏链接且 YAML 非法。
    字符串引号包裹既合法 YAML，Obsidian 又能正常解析双链。
    幂等加固（2026-09-01·Loop评估P1修复）：字符串值含 [[ ]]（parse 回读后的形态）同样
    加引号输出——否则 MERGE 回写（parse→dump）会把合法值裸化成非法
    `related: [[A]] [[B]]`，重新产出 326 事故同款格式。
    """
    out = []
    for k, v in fm.items():
        if isinstance(v, bool):                      # 必须在 int 之前判断：bool 是 int 的子类
            out.append(f"{k}: {'true' if v else 'false'}")
        elif k == "related" and isinstance(v, list):
            out.append(f'{k}: "{ " ".join(str(x) for x in v) }"')
        elif k == "related" and isinstance(v, str) and "[[" in v and "]]" in v:
            out.append('%s: "%s"' % (k, v.replace('"', '\\"')))  # 值内引号转义（2026-09-01 复核N2）
        elif isinstance(v, list):
            out.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif v is None:
            out.append(f"{k}: null")
        else:
            out.append(f"{k}: {v}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 校验（返回违规字符串清单；空列表=合规）
# ---------------------------------------------------------------------------

def _validate(fm, fields, kind):
    issues = []
    # 禁用字段
    for fk in FORBIDDEN_KEYS:
        if fk in fm:
            issues.append(f"[{kind}] 禁用字段 '{fk}'（应改用 date/last_updated）")
    # 必填 + 约束
    for key, required, validator in fields:
        present = key in fm and str(fm[key]).strip() != "" and fm[key] is not None
        if not present:
            if required:
                issues.append(f"[{kind}] 缺必填字段 '{key}'")
            continue
        if validator is not None and not validator(fm[key]):
            issues.append(f"[{kind}] 字段 '{key}' 值不合规: {fm[key]!r}")
    return issues


def check_body_length(body):
    """卡片正文长度定值校验（≤ CARD_BODY_MAX 字）。

    口径=config.yaml「永久卡片·每张卡片正文 ≤600字（含原文依据/AI理解/应用场景三段）」——
    统计原文依据→可作为核心启发的标签之间的三段，不含标题/核心启发/关联卡片行。
    无原文依据段的旧格式卡兜底按全部 body 统计。

    供两处调用：
    ① 生成即自检——写卡前 AI 用 parse_frontmatter 取 body 后调用，超限=物理拦截；
    ② 产物机检——lint_path 对 reading-card 扫描时兜底（2026-08-17 起）。
    返回违规字符串；合规返回 None。
    """
    text = str(body)
    # 识别三段起点：新版粗体 `**原文依据**` 或存量卡二级标题 `## 原文依据`（2026-08-17 存量处理实证）
    m = re.search(r'(?:\*\*原文依据\*\*|## 原文依据)', text)
    if m:
        seg = text[m.start():]
        # 结束标记：核心启发标签 / 关联卡片（粗体或二级标题）/ 文件尾
        end = re.search(r'(?:\*\*可作为核心启发的标签\*\*|## 关联卡片|\*\*关联卡片\*\*)', seg)
        if end:
            seg = seg[:end.start()]
        n = len(seg.strip())
    else:
        n = len(text.strip())
    if n > CARD_BODY_MAX:
        return f"[card] 正文超 {CARD_BODY_MAX} 字（实际 {n}）——一卡一概念一页看完，超限须精简 AI理解/应用场景段"
    return None


def validate_card_full(fm, body):
    """frontmatter + 正文 联合校验（生成即自检用）。"""
    issues = validate_card(fm)
    body_issue = check_body_length(body)
    if body_issue:
        issues.append(body_issue)
    return issues


def validate_note(fm):
    return _validate(fm, NOTE_FIELDS, "note")


def validate_quizbank(fm, body=""):
    """题库文件合规校验（v4.7.0 · 跨Skill消费边）。

    校验 frontmatter 必填 + question_count 与正文 ## Q 段数一致（防 D4 不可验证产出物）。
    仅由 lint_path 对 type:quiz-bank 文件派发；存量笔记/卡片不受影响。
    """
    issues = _validate(fm, QUIZ_FIELDS, "quiz-bank")
    q_count = fm.get("question_count")
    q_sections = len(re.findall(r'^##\s+Q\d+', body, re.M)) if body else 0
    try:
        declared = int(q_count)
    except (TypeError, ValueError):
        declared = -1
    if declared >= 0 and q_sections != declared:
        issues.append(f"[quiz-bank] question_count={declared} ≠ 正文 ## Q 段数 {q_sections}（须一致）")
    if q_sections == 0:
        issues.append("[quiz-bank] 正文无 ## Q 题目段（每题须含 **问题**/**答案**）")
    return issues


def validate_card(fm):
    issues = _validate(fm, CARD_FIELDS, "card")    # --- 条件必填（Wave 0.2 · source_type 驱动的动态规则）---
    source_type = str(fm.get("source_type", "")).strip()
    if source_type == "" or source_type == "book":
        # 书卡规则（存量兼容）：book/book_author 必填
        if not str(fm.get("book", "")).strip():
            issues.append("[card] 书卡缺必填字段 'book'（source_type 缺失或=book 时必填）")
        if not str(fm.get("book_author", "")).strip():
            issues.append("[card] 书卡缺必填字段 'book_author'（source_type 缺失或=book 时必填）")
    else:
        # 文章/论文/推文卡规则：source_title/source_author 必填
        if not str(fm.get("source_title", "")).strip():
            issues.append(f"[card] 非书源卡缺必填字段 'source_title'（source_type={source_type} 时必填）")
        if not str(fm.get("source_author", "")).strip():
            issues.append(f"[card] 非书源卡缺必填字段 'source_author'（source_type={source_type} 时必填）")
    # --- 立场一致性机检（v2026-08-14 · b 冲突门禁·第一性原理落地）---
    # 宣称矛盾(stance_main_contradiction 非空)的卡，必须指向被矛盾对象(related 含≥1 指针)，
    # 防孤儿矛盾声明污染知识池。复用现有 stance 扩展层字段，零新 schema，现有卡 0 命中。
    if str(fm.get("stance_main_contradiction", "")).strip():
        rel = fm.get("related")
        rel_ok = bool(rel) and not (isinstance(rel, list) and len(rel) == 0) \
            and not (isinstance(rel, str) and not str(rel).strip())
        if not rel_ok:
            issues.append("[card] 宣称立场矛盾(stance_main_contradiction)但缺 related 指针（须指向被矛盾卡 card_id）")
    return issues


# ---------------------------------------------------------------------------
# 产物机检（③）：扫描目录
# ---------------------------------------------------------------------------

def _yaml_hardcheck(text):
    """硬 YAML 合法性闸（B 兜底·定值法·2026-08-24 补）。

    背景：本 Skill 的 parse_frontmatter 是容错解析器——遇到
    `related: [[A]] [[B]]` 裸双链 / `title: "X"的诊断` 裸引号 这类非法
    YAML 时，会"尽力"当成普通字符串存进 dict，**不抛异常**，导致 lint_path
    机检放行脏卡片（检索端 yaml.safe_load 解析即崩→整卡丢索引）。

    裁判策略（务实·零硬依赖破窗）：
    ① 优先用标准库 yaml（环境可用时）对整段 frontmatter 做权威解析——
       yaml.safe_load 抛异常=真实非法（零假阳性，中文冒号在值中间等
       合法写法不会被误伤）；
    ② yaml 不可用时降级：只查最确定的根因——裸 related 双链（值含 [[
       且整行未引号包裹），这是本次 326 脏卡的主流形态。
    返回违规字符串列表；空=通过。
    """
    issues = []
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.S)
    if not m:
        return issues
    fm_text = m.group(1)
    # ① 权威裁判：标准 yaml
    if _YAML_AVAILABLE:
        try:
            _yaml_mod.safe_load(fm_text)
        except Exception as e:
            issues.append(f"[frontmatter] YAML 非法（标准解析器报错：{str(e).splitlines()[0]}）")
        return issues
    # ② 降级：只查裸 related 双链（最确定根因，不需 yaml）
    for i, line in enumerate(fm_text.split('\n'), 1):
        s = line.strip()
        if not s or ':' not in s or s.startswith('#'):
            continue
        k, _, v = s.partition(':')
        k, v = k.strip(), v.strip()
        if k == 'related' and '[[' in v and not (v.startswith('"') and v.endswith('"')):
            issues.append(f"[frontmatter] 第{i}行 related 双链未用双引号包裹（'{v}' 会被 YAML 当成非法内联列表）")
    return issues


def lint_path(path, verbose=True):
    """扫描 path（文件或目录）内所有 .md，按 type 派发校验。
    返回 (total, violations_dict)。"""
    if os.path.isfile(path):
        files = [path]
    elif os.path.isdir(path):
        files = []
        for root, _, names in os.walk(path):
            for n in names:
                if n.endswith(".md"):
                    files.append(os.path.join(root, n))
    else:
        files = []

    report = {}
    total = 0
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            report[fp] = [f"读取失败: {e}"]
            total += 1
            continue
        fm, body = parse_frontmatter(text)
        if not fm:
            continue  # 无 frontmatter 的纯文档不归本机检管
        # B 兜底闸：硬 YAML 合法性（先于字段校验，脏格式优先报）
        hard = _yaml_hardcheck(text)
        t = fm.get("type")
        if t == "note":
            issues = validate_note(fm)
        elif t == "reading-card":
            issues = validate_card(fm)
            body_issue = check_body_length(body)
            if body_issue:
                issues.append(body_issue)
        elif t == "quiz-bank":
            issues = validate_quizbank(fm, body)
        else:
            # 其他类型不在本 Skill 字段校验范围，但硬 YAML 闸仍适用
            issues = []
        if hard:
            issues = hard + issues
        total += 1
        if issues:
            report[fp] = issues

    if verbose:
        if not report:
            print(f"✅ 机检通过：扫描 {total} 个笔记/卡片文件，零违规。")
        else:
            print(f"⛔ 机检发现 {len(report)} 个文件违规（共扫描 {total} 个）：")
            for fp, issues in report.items():
                print(f"\n📄 {fp}")
                for it in issues:
                    print(f"   - {it}")
    return total, report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def verify_index(pool_root, index_path=None):
    """INDEX 一致性校验（2026-08-12 反哺·SKILL-20260812-001·皮叔确认）。

    以 master 总览行为单一映射锚（链接列=目录名·书名列镜像段标题）：
      ① master 行卡片数 vs 目录实际卡片数
      ② 书目录索引段（### 标题…表格）行数 vs 目录实际卡片数
    设计：校验阻断 + 提供预期值（不自动写回——自动修正会掩盖卡片误删）。
    返回 (问题清单, 每书卡数统计)；空清单=一致。
    """
    index_path = index_path or os.path.join(pool_root, 'INDEX.md')
    issues = []
    if not os.path.isfile(index_path):
        return [f"INDEX.md 不存在: {index_path}"], {}
    index_text = open(index_path, encoding='utf-8').read()
    stats = {}
    # master 行: | 日期 | 源名 | source_type | N | [精华](dir/精华.md) | 状态 |
    # v4.10.0 泛化（清零批#14）：source_type 列不再硬编码 book——article/paper 等行
    # 一并校验"链接目标文件存在"；书行（book）继续走目录卡片数双重核对。
    master_rows = re.findall(
        r'^\|\s*[\d-]+\s*\|\s*(.+?)\s*\|\s*([a-z][a-z-]*)\s*\|\s*(\d+)\s*\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|',
        index_text, re.M)
    for title, stype, count, link in master_rows:
        link_path = os.path.join(pool_root, link)
        if not os.path.isfile(link_path):
            issues.append(f"[{title}] master 行精华链接失效（{link}）")
        dirname = os.path.basename(os.path.dirname(link))
        if stype != 'book' or dirname == '文章卡片' or not dirname:
            # 非书行（article/paper/thread）与文章卡片行：仅做链接存在性校验（上方），
            # ⛔不套书行"目录卡片数"核对——多文共居一夹（如毛选）会假阳性（2026-09-01 清零批#14）
            continue
        d = os.path.join(pool_root, dirname)
        actual = len([f for f in os.listdir(d) if f.endswith('.md') and '卡片' in f]) if os.path.isdir(d) else -1
        stats[dirname] = actual
        if actual == -1:
            issues.append(f"[{title}] 目录不存在（master 行链接指向 {dirname}）")
            continue
        if actual != int(count):
            issues.append(f"[{title}] master 行卡片数 {count} ≠ 实际 {actual} 张（{dirname}）")
        _ = stype  # 保留捕获供后续按 source_type 差异化校验扩展
        # 书目录索引段：段标题以 master 书名列开头
        seg_m = re.search(rf'^### {re.escape(title.strip())}[^\n]*$', index_text, re.M)
        if not seg_m:
            issues.append(f"[{title}] 书目录索引段缺失（实际 {actual} 卡）")
            continue
        seg_start = seg_m.end()
        seg_end = index_text.find('\n### ', seg_start)
        seg = index_text[seg_start:seg_end if seg_end > 0 else len(index_text)]
        idx_rows = len(re.findall(r'^\|\s*\d+\s*\|', seg, re.M))
        if idx_rows != actual:
            issues.append(f"[{title}] 书目录索引 {idx_rows} 行 ≠ 实际 {actual} 卡")
    return issues, stats


def main():
    if len(sys.argv) < 2:
        print("用法: python note_validator.py <文件或目录路径>")
        print("      扫描并机检笔记/卡片 frontmatter + 卡片正文长度(≤600字) 合规性")
        print("      python note_validator.py --index-check <知识池根目录> [INDEX.md路径]")
        print("      INDEX 一致性校验（书目录卡片数 vs INDEX 双重核对）")
        sys.exit(1)
    if sys.argv[1] == '--index-check':
        pool_root = sys.argv[2] if len(sys.argv) > 2 else '.'
        index_path = sys.argv[3] if len(sys.argv) > 3 else None
        issues, stats = verify_index(pool_root, index_path)
        if issues:
            print("❌ INDEX 一致性校验未通过：")
            for i in issues:
                print("  ", i)
            print(f"核对 {len(stats)} 本书")
            sys.exit(1)
        print(f"✅ INDEX 一致性校验通过：{len(stats)} 本书 卡片数全部一致")
        sys.exit(0)
    target = sys.argv[1]
    total, report = lint_path(target, verbose=True)
    sys.exit(1 if report else 0)


if __name__ == "__main__":
    main()
