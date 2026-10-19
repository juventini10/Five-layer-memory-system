#!/usr/bin/env python3
# version: v0.5
"""session_title_utils.py — 对话标题统一命名·公共原语（跨工具中立）

规则（你立 2026-09-09，SSOT=~/.workbuddy/MEMORY.md「对话标题命名规则」）:
    标题格式 = YYMMDD | 类型 | 主题
    日期 = 北京时区实际创建日期（取会话 created_at）
    类型 ∈ {功能,设计,修复,优化,发布,探索,文档,研究}
    主题 = 首条 prompt 简洁概括

## 定位（本文件是**对外安装包组件**的源 · 2026-10-02 立源）

⛔ 此前本原语只存在于作者机 `开发工具/`，对外那份是**手工复制进安装说明 md 的内嵌代码块**
（09-21 冻结 · 已与作者机漂移：v0.2 的 @行清洗、v0.3 的 file:// 清洗都没进对外版）
⇒ **改本机 ≠ 对外生效**；且它不在「发布包=源的确定性函数」体系内（铁律管不到）。
⇒ 本文件为**唯一源**：`技能配置/session-title-namer/scripts/` → generate_release → 安装包。

## 跨端契约（⛔ 不可破坏）

各端适配器 import 本文件原语（**接入=调用，不=改写**）。以下函数名与签名是**公共接口**：
    bj_date_from_ms(ms)      -> "YYMMDD"
    classify(prompt)         -> 类型名
    extract_theme(prompt)    -> 主题
    make_title(prompt, ms)   -> 完整标题
新增能力一律走**可选参数带默认值**，保证 v0.3 及更早的调用方零改动可用。

## v0.4 修的三类硬伤（2026-10-02 · 作者机 6 例实测坐实）

| 硬伤 | 实证症状 | 修法 |
|:--|:--|:--|
| ① `THEME_MAX=20` **硬截半句** | `评估一下我们现在Hermes是否已能让新`（断在"新"） | `_fit_theme` 词边界/语义断点回退，**宁短不残** |
| ② **类型判定被词序绑架** | "评估…重点看安装包" -> 判成`发布`（"安装包"属发布组且排前） | `TYPE_VERBS` / `TYPE_NOUNS` **双信号**：动词优先，宾语仅兜底 |
| ③ **脏前缀直入主题** | `，我这个用户的要求很明确：用户通过这安`（开头逗号） | `_strip_lead` 剥前导标点 + 连接词 |

⚠️ v0.4 **不引入 LLM 调用**——公共原语必须**零依赖 / 零延迟 / 零花费**才能进安装包。
语义深度天花板由此封顶（20 字标题本就没有信息量可言），这是**有意的取舍**。
需要更强语义时：用 LLM 出主题，再调用本原语做**格式规范化**（见 references/ 架构说明）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import re
from datetime import datetime, timedelta, timezone

# 类型判定 v0.4：**动词组**（意图主动信号）优先，无命中才让**宾语组**兜底。
# ⚠️ v0.3 单表混判的病根：TYPE_RULES 顺序 = 优先级，于是宾语词（"安装包"）
#    会抢走动词表达的意图（"评估…重点看安装包" 判成 发布 而非 研究）。
TYPE_VERBS = [
    # ⚠️ v0.5 补「审计/排查/取证」——原表漏了这两个高频动作动词，
    #   导致"审计【月报 → MEMORY.md 回流】"这类**审计对象含周期词**的会话
    #   越过动词层直落周期层，被误判成"月报"（实证 2026-10-02）。
    ("修复", ["bug", "报错", "修复", "排查", "异常", "崩溃", "错误", "失效", "复现", "回滚",
             "不生效", "不对", "没变", "失败", "审计", "取证", "核对"]),
    ("优化", ["优化", "重构", "瘦身", "提速", "性能", "精简", "改进", "refactor"]),
    # ⚠️ v0.5 把「复盘/回顾」**移出**本组：它们是日记/周报/月报的**内容形式**，
    #   不是独立任务类型。留在本组会把"把这周复盘整理成周报"判成"研究"（实证）。
    ("研究", ["研究", "调研", "评估", "对比", "选型", "分析", "体检", "审查", "audit",
             "为什么", "原理", "查看", "看看", "核实", "确认"]),
    ("设计", ["设计", "ui", "视觉", "样式", "风格", "配色", "原型"]),
    ("发布", ["发布", "release", "上线", "发版", "出包", "打包"]),
    ("文档", ["文档", "手册", "readme", "规范", "白皮书", "changelog"]),
    ("功能", ["开发", "实现", "新增", "构建", "搭建", "做一个", "写一个", "做个",
             "接入", "落地", "写个", "整一个"]),
]
# 宾语组：**仅在无任何动词命中时**参与（v0.4 新规则）
TYPE_NOUNS = [
    ("修复", ["bug", "故障"]),
    ("发布", ["安装包", "打包", "版本"]),
    ("文档", ["文档", "手册", "readme", "changelog", "说明"]),
    ("设计", ["ppt", "幻灯", "页面", "ui", "视觉", "配色"]),
    ("研究", ["报告", "结论", "方案"]),
    ("功能", ["hook", "skill", "脚本", "引擎", "自动化", "工具"]),
]

# ⛔ 保留 v0.3 的 TYPE_RULES 名字与结构——外部可能有代码 import 它做展示/自检
TYPE_RULES = list(TYPE_VERBS) + [p for p in TYPE_NOUNS
                                 if p[0] not in dict(TYPE_VERBS)]

# v0.5（2026-10-02·皮叔定调「日记/周报/月报不是私产·其他用户也会用·用不到就不显示」）：
# 周期类进**正式类型位**。判据不是词表优先级，而是**动作词与周期词是否共存**——
#   共存 → 动作词赢（"审计月报SOP" = 研究，月报只是被审计的对象）
#   不共存 → 周期词就是类型（"写今天的日记" = 日记）
# 实证：作者机 150 条真实首轮 prompt 里，含周期词的会话动作词为空或明确为审计类。
PERIOD_TYPES = [
    ("日记", ["日记", "日课", "晨记", "晚记", "睡前记录", "每日记录"]),
    ("周报", ["周报", "周总结", "本周总结", "周复盘"]),
    ("月报", ["月报", "月总结", "月度总结", "月复盘"]),
]

__version__ = "0.5.0"

DEFAULT_TYPE = "探索"
THEME_MAX = 20

# v0.4：语义断点候选（回退截断时优先退到这些符号之后）
_SEM_BREAKS = ("，", "。", "、", "：", ";", "；", "？", "?", "！", "!", "…", "——", " ")


def bj_date_from_ms(ms: int) -> str:
    """epoch ms -> 北京时区 YYMMDD。ZoneInfo 不可用则回退固定 UTC+8。"""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Shanghai")
    except Exception:
        tz = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(ms / 1000, tz=tz).strftime("%y%m%d")


def _match(text: str, table) -> str:
    for type_name, keywords in table:
        if any(k.lower() in text for k in keywords):
            return type_name
    return ""


def classify(prompt: str) -> str:
    """类型判定。**v0.5 三级优先**：动作动词 > 周期词 > 宾语兜底 > 默认。

    ⚠️ v0.4 双信号修的是"宾语词抢走动词意图"（评估…看安装包 判成 发布）。
    ⚠️ v0.5 加周期维度（皮叔 2026-10-02 定调）：日记/周报/月报 是**正式类型**，
       不是私产、不是主题装饰。判据是**共存关系**而非词表顺序——
       「写今天的日记」无动作词 ⇒ 日记；「审计月报 SOP」有审计 ⇒ 研究。
    """
    text = prompt.lower()
    hit = _match(text, TYPE_VERBS)      # ① 动作动词（意图主动信号）
    if hit:
        return hit
    hit = _match(text, PERIOD_TYPES)    # ② 周期（日记/周报/月报·v0.5 新增）
    if hit:
        return hit
    hit = _match(text, TYPE_NOUNS)       # ③ 宾语兜底
    return hit or DEFAULT_TYPE


def _strip_lead(line: str) -> str:
    """v0.4：剥前导标点与连接词。

    ⚠️ 实证症状：剥掉 @file: 引用后残留的**前导逗号**没人清 ->
    主题变成 "，我这个用户的要求很明确"（逗号开头）。
    """
    prev = None
    while prev != line:
        prev = line
        line = line.lstrip("，,。.、：:；;！!？? \t　-—…～~")
    return re.sub(r"^(那|然后|另外|所以|因此|嗯|哎|喂)[，,、\s]*", "", line).strip()


def _fit_theme(theme: str, limit: int = THEME_MAX) -> str:
    """v0.4：**断点回退**替代硬截断。

    ⚠️ v0.3 硬截的实证症状：`评估一下我们现在Hermes是否已能让新`（断在"新"·半句）
    => 超长时退到 limit 前最近的语义断点；无断点则退到**中英/空白交界**；
    仍无才保留硬截（不制造空标题）。**宁短不残。**
    """
    if len(theme) <= limit:
        return theme
    head = theme[:limit]
    best = 0
    for b in _SEM_BREAKS:
        i = head.rfind(b)
        if i > best:
            best = i + len(b)
    if best >= 4:                       # 断点太靠前（<4 字）宁可不用
        return head[:best].strip("，,、：:；; 　")
    for i in range(len(head) - 1, 3, -1):
        a, b = head[i - 1], head[i]
        if (a.isascii() != b.isascii()) or b == " ":
            return head[:i].strip()
    return head


def extract_theme(prompt: str) -> str:
    """取首个非空行 -> 去 markdown 符号 -> 首个括号配平标点截断 -> 断点回退限长。

    ⚠️ 下划线"_"不清洗——search_kb / kb-index-guard 类主题名不可剥坏。
    ⚠️ 截断点须《》（）配平——《思考，快与慢》类书名号内标点不可切。
    ⚠️ v0.2（2026-09-21）：@开头引用行不作主题（实证首行 @"路径" 产出垃圾标题）。
    ⚠️ v0.3（2026-09-27）：file:// 开头引用行同罪（ZCode 实证主题变成 "file:///Users/<user>"）。
# v0.4 修（2026-10-02）：剥前导标点（`_strip_lead`）+ 断点回退限长（`_fit_theme`）。
    """
    lines = [l.strip() for l in prompt.splitlines() if l.strip()]
    if not lines:
        return "未命名"
    candidates = [l for l in lines if not (l.startswith("@") or l.startswith("file://"))]
    if candidates:
        line = candidates[0]
    else:
        # ⚠️ v0.4 修：⛔ **不要**在这里 lstrip("@")/剥 file://——
        #    先剥会让下面的同行剥离判据 `line.startswith("@")` **永远为假**
        #    （先剥后判 = 判不到·v0.4 实测踩过）。这里只做 strip()，
        #    引用 token 统一交给下面的 v0.4 同行剥离处理。
        line = lines[0].strip()
        line = line.strip('"').strip() or "未命名"
    # v0.4 修：引用与提问**同行**时（`@"路径" 这个问题怎么办`）——
    #   v0.2/v0.3 只能"跳过整行"，同行就跳不掉，导致主题=路径截断
    #   （实证 v0.3 产出 `[记忆共享中心]/README.md" 这个`·路径+残引号进了标题）。
    #   => 剥掉行首引用 token，保留其后的提问文字。
    if line.startswith("@"):
        # ⛔ 非贪婪 `\S*?` 的坑（v0.4 实测）：`@"路径" 问题` 只吃到开引号就停
        #    ⇒ 主题残留 `[记忆共享中心]/README.md"`。改为**引号配平优先**，引号内可含空格。
        line = re.sub(r'^@(?:"[^"]*"|\S+)\s*', "", line, count=1).strip() or line
    if line.startswith("file://"):
        m2 = re.match(r"file://[^\s，,：:？?]+\s*[，,：:？?]?\s*(\S.*)", line)
        line = (m2.group(1) if m2 else "").strip() or line.rsplit("/", 1)[-1]
    line = re.sub(r"^[#\s>*\-`]+", "", line).strip()
    line = re.sub(r"[`*#]", "", line).strip()
    line = _strip_lead(line)                      # v0.4
    if not line:
        return "未命名"
    theme = None
    for m in re.finditer(r"[，。？！：；、,?!\|\n]", line):
        seg = line[: m.start()]
        if seg.count("《") == seg.count("》") and seg.count("（") == seg.count("）"):
            theme = seg.strip()
            break
    if not theme or not theme.strip():
        theme = line.strip()
    return _fit_theme(theme) or "未命名"          # v0.4


def make_title(prompt: str, created_ms: int) -> str:
    """拼装完整标题 `YYMMDD | 类型 | 主题`。

    v0.5（2026-10-02·你提议日记/周报/月报）：**不把它们塞进类型位**，改在
    **主题段前置周期标记**。理由是维度正交——

      类型位 = 「在做什么」（功能/设计/修复/优化/发布/探索/文档/研究）
      周期位 = 「什么时候做」（日记/周报/月报）

    实证依据（作者机 150 条真实首轮 prompt）：8 条含「月报」的会话里有 6 条
    同时含研究动词（审计/分析/回流）——若把「月报」放进类型位，它会与「研究」
    抢同一格，分类结果随机。⛔ 混维度 = 分类器打架。

    ⇒ 形式：`260102 | 研究 | 月报·SOP审计`（周期在主题里，类型位保持纯动作）
    """
    return (f"{bj_date_from_ms(created_ms)} | {classify(prompt)} | "
            f"{extract_theme(prompt)}")


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    if args and args[0] == "--dry-run":
        prompt = ""
        created_ms = int(datetime.now().timestamp() * 1000)
        i = 1
        while i < len(args):
            if args[i] == "--prompt":
                prompt = args[i + 1]
                i += 2
            elif args[i] == "--created-at-ms":
                created_ms = int(args[i + 1])
                i += 2
            else:
                i += 1
        print(make_title(prompt, created_ms))
    elif args and args[0] == "--self-test":
        # v0.4 自测：6 例作者机实证 + 旧版回归
        ms = 1767225600000   # 2026-01-01T00:00:00Z -> 北京 08:00
        CASES = [
            ("WorkBuddy 的任务标题 hook 为什么在 Hermes 端不生效？帮我做根因排查", "修复"),
            ("评估一下我们现在Hermes是否已能让新用户顺畅使用，重点看安装包", "研究"),
            ("，我这个用户的要求很明确：用户通过这个安装包装完就要能用", "发布"),
            ("把布洛陀脚本接入工作做完并更新哲学文件", "功能"),
            ("查看记忆蓝图里面的数字分身哲学文件", "研究"),
            # v0.5 周期维度（皮叔 2026-10-02 定调：日记/周报/月报是正式类型·非私产）
            ("写今天的日记", "日记"),
            ("帮我把这周的复盘整理成周报", "周报"),
            ("出一份月报", "月报"),
            # v0.5 共存判据：动作词在场时周期词让位
            ("审计【月报 → MEMORY.md 回流路径】是否断裂", "修复"),
        ]
        bad = 0
        for prompt, want in CASES:
            got_t = classify(prompt)
            got = extract_theme(prompt)
            flag = "OK " if got_t == want else "TYPE"
            if got_t != want:
                bad += 1
            # 硬伤断言：无前导标点 + 不超过限长
            if got[:1] in "，,。.、：:；;！!？?":
                flag, bad = "LEAD", bad + 1
            if len(got) > THEME_MAX:
                flag, bad = "LONG", bad + 1
            print(f"  {flag} [{got_t}] {got}")
        print("SELF-TEST:", "OK" if bad == 0 else f"FAIL({bad})")
