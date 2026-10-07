#!/usr/bin/env python3
"""
finalize_diary.py — 日记封口脚本（物理约束·模型无关）

用法：
  python3 scripts/finalize_diary.py --date 2026-07-24

功能（原子化·不可拆分）：
  1. 读取当天日记，校验 5 个核心 SECTION 非空
  2. 生成次日骨架（复用 create_skeleton 逻辑，幂等）
  3. 将今日「明日目标」写入次日骨架续接锚点
  4. stdout 输出 JSON 确认块（AI 输出格式物理依赖此数据）

退出码：
  0 = 封口成功
  1 = 文件缺失 / 参数非法 / 日记完整性校验失败（缺失 SECTION，多路径共用）
  2 = 次日骨架生成失败
  3 = 概念进料门禁阻断（当日无 ingest 条目且未显式 --skip-ingest·v3.20.1）
  4 = 评级门禁阻断（rating 为待评定/非法值 或 rating_reason 为空·v3.22.0 无跳过选项）
  5 = 参数错误（argparse 缺参/未知参数；日期格式非法归 exit 1·2026-09-01 实测复核）
  6 = 格式门禁阻断（v4.1.0 全模块格式校验不过：速读层/含金量/睡眠紧凑/心情/伙伴建议/来源/有才显示/结尾/年度进度条·皮叔 2026-08-07 认可"格式合规从AI自律下沉为物理校验"）
  7 = 环境自检失败（沙箱假python·审查P2-2：原误用2与骨架失败双义，2026-09-03拆分）

  ⚠️ 版本命名空间注：上方 v4.1.0 = finalize_diary 内置格式校验模块自身的版本号，
  与 Skill 主版本（SKILL.md frontmatter version，如 3.44.x）独立演进，勿混淆。

设计原理（Poka-Yoke 接触法）：
  AI 的"日记完成"输出必须包含本脚本产出的灵感原文。
  不调本脚本 = 拿不到灵感 = 输出格式不完整 = 完整性锁不通过。
  模型无关——无论什么 LLM 都无法绕过这个物理约束。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import calendar
import datetime
import json
import os
import re
import sys
from pathlib import Path

# === Import create_skeleton 核心函数 ===
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv  # 环境自愈：破除沙箱 HOME 劫持
from create_skeleton import (
    build_skeleton,
    diary_path_for_date,
    weekday_cn,
    DIARY_BASE,
)

# 概念进料 log 路径改用 dbenv 解析（破除沙箱 HOME 污染）
FED_LOG = dbenv.HOME / "[记忆共享中心]" / "开发工具" / "知识联邦引擎" / "log.md"

# === 常量 ===
REQUIRED_SECTIONS = [
    ("SLEEP", "睡眠质量"),
    ("GOALS", "今日工作"),
    ("MOOD_ENERGY", "心情与能量"),
    ("INSIGHTS", "今日感悟"),
    ("SUMMARY", "今日总结"),
]

# 判定 SECTION 为空的标志词（骨架占位符）
EMPTY_MARKERS = [
    "待填写", "待明早数据", "待晚间复盘", "⚠️ 待",
    "（待填写）", "— | —",
]


def read_concept_ingest(date: datetime.date):
    """读知识联邦 log.md 当日 ingest 条目。
    返回: (status, text)
      status: "ok"=有条目(含合法跳过) / "missing"=引擎在但当日无条目 / "no-engine"=引擎不可用
    """
    if not FED_LOG.exists():
        return ("no-engine", "⚠️ 知识联邦引擎不可用（分享版无引擎属正常）")
    try:
        lines = FED_LOG.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return ("no-engine", f"⚠️ log.md 读取失败: {e}")
    prefix = f"## [{date}] ingest"
    hits = [ln.strip() for ln in lines if ln.strip().startswith(prefix)]
    if hits:
        return ("ok", hits[-1].lstrip("# ").strip())
    return ("missing", "⚠️ 概念抽取未跑")


def read_diary(date: datetime.date) -> str:
    """读取指定日期的日记文件内容"""
    path = diary_path_for_date(date)
    if not path.exists():
        print(f"❌ 日记文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def extract_section(content: str, section_name: str) -> str:
    """提取指定 SECTION 的内容（从标记到下一个 --- 分隔线）"""
    pattern = rf'<!-- SECTION: {section_name} -->\n(.*?)(?=\n---|\Z)'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ""


def is_section_filled(section_content: str) -> bool:
    """判断 SECTION 是否有实际内容（非空且非占位符）"""
    if not section_content:
        return False
    # 去掉标题行后看剩余内容
    lines = [l.strip() for l in section_content.split('\n')
             if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return False
    # 检查是否全是占位符
    text = '\n'.join(lines)
    for marker in EMPTY_MARKERS:
        text = text.replace(marker, "")
    # 去掉表格框架（|---|）和空表格行
    text = re.sub(r'\|[-\s:]+\|', '', text)
    text = re.sub(r'\|\s*\|', '', text)
    text = text.replace('|', '').replace('>', '').replace('-', '').strip()
    return len(text) > 5  # 至少有一些有意义的内容


def validate_diary(content: str) -> list:
    """校验日记核心 SECTION，返回缺失列表"""
    missing = []
    for section_id, section_name in REQUIRED_SECTIONS:
        section_content = extract_section(content, section_id)
        if not is_section_filled(section_content):
            missing.append(section_name)
    return missing


def extract_tomorrow_goals(content: str) -> str:
    """从今日日记中提取「明日目标」内容"""
    pattern = r'<!-- SECTION: TOMORROW -->.*?##[^\n]*\n(.*?)(?=\n---|\Z)'
    m = re.search(pattern, content, re.DOTALL)
    if m:
        text = m.group(1).strip()
        # 去掉 > 引用标记和"待晚间复盘"占位符
        if "待晚间复盘" in text or not text:
            return ""
        # 提取要点，合并为一行
        items = []
        for line in text.split('\n'):
            line = line.strip().lstrip('->•● ')
            if line and "待" not in line:
                items.append(line)
        return " / ".join(items) if items else ""
    return ""


def extract_rating(content: str) -> str:
    """从日记 YAML 提取评级"""
    m = re.search(r'^rating:\s*"?([^"\n]+)"?', content, re.MULTILINE)
    if m:
        r = m.group(1).strip()
        return r if r != "待评定" else "未评定"
    return "未评定"


VALID_RATINGS = {"S", "A", "B", "C", "N"}  # achievement-rules.md 定义的全部合法等级（YAML存储层仅核心字母，+/-修饰符只入callout）


def extract_rating_reason(content: str) -> str:
    """从日记 YAML 提取评级理由"""
    m = re.search(r'^rating_reason:\s*"?([^"\n]*)"?', content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def rating_callout_type(rating: str) -> str:
    """评级 → callout 分色类型（v3.33 唯一版：S/A→success、B→note、C→warning、N→info）"""
    if rating in ("S", "A"):
        return "success"
    if rating == "B":
        return "note"
    if rating == "C":
        return "warning"
    return "info"


def fill_rating_callout(content: str, rating: str, reason: str) -> str:
    """回填正文「待评定」占位为正文 callout 分色评级（物理写入，消除 AI 漏填隐患）。
    若正文已是正确的分色 callout 则保持不变（幂等）。"""
    ctype = rating_callout_type(rating)
    new_line = f"> [!{ctype}] 🏆 今日含金量：**{rating}**（{reason}）"
    # 匹配旧的「待评定」占位或旧的任意分色 callout（无论评级是否一致，统一按 YAML 重写）
    pattern = re.compile(
        r'^>\s*\[!(?:success|note|warning|info)\]\s*🏆 今日含金量：\*\*[^\*]*\*\*（[^）]*）',
        re.MULTILINE,
    )
    if pattern.search(content):
        return pattern.sub(new_line, content, count=1)
    return content


def check_speedread(content: str) -> list:
    """速读层格式校验（v3.33.0 + v4.0.0·皮叔 2026-08-07 诊断：8/2、8/3 速读层空白/格式漂移）。
    返回违规列表；空列表=通过。
    校验项：
      1. 速读层标题存在（模板一致性）
      2. 速读层区域不含『待晚间复盘』占位符（未生成=头版空白）
      3. 速读层区域含信号表表头 `| 信号 |`（格式唯一版=表格版，禁文本版漂移）
      4. 速读层区域含 7天趋势 sparkline 行（v4.0.0 零依赖可视化·`📈 近7天趋势`）
    """
    violations = []
    m = re.search(r'【今日速读[^\n]*】\n(.*?)(?=\n---|\Z)', content, re.DOTALL)
    if not m:
        return ["速读层标题缺失（模板不一致）"]
    section = m.group(1)
    if "待晚间复盘" in section:
        violations.append("速读层仍为『待晚间复盘』占位符（未生成）")
    if "| 信号 |" not in section:
        violations.append("速读层缺信号对比表（| 信号 | 表头）——非表格版格式")
    if "近7天趋势" not in section:
        violations.append("速读层缺 7天趋势 sparkline 行（📈 近7天趋势）——v4 零依赖可视化未生成")
    if "📅 今年已过" not in section or "█" not in section:
        violations.append("速读层年度进度行缺 20 格进度条（v4.1.0：📅 今年已过 ██████░░ {P}% (Day N/365)）")
    return violations


def check_diary_format(content: str) -> list:
    """全模块格式门禁（v4.1.0·皮叔 2026-08-07 认可：格式合规从 AI 自律下沉为物理校验）。
    返回违规列表；空列表=通过。逐模块对照 diary-template.md v4 标准。"""
    v = check_speedread(content)  # 速读层：标题/占位符/信号表/sparkline/进度条
    # 含金量行：callout 分色 + 评级 + 括号理由（评级必须为合法等级字母，杜绝「待评定」占位漏网）
    if not re.search(r'^>\s*\[!(?:success|note|warning|info)\]\s*🏆 今日含金量：\*\*(?:S|A|B|C|N)\*\*（', content, re.M):
        v.append("含金量行非 callout 分色格式（[!success/note/warning/info] 🏆 **S/A/B/C/N**（理由））")
    # 睡眠区：紧凑三件套（无文字墙残留）+ 评级行 + 有设备字符条
    m = re.search(r'<!-- SECTION: SLEEP -->\n(.*?)(?=\n<!-- SECTION:|\Z)', content, re.DOTALL)
    if m:
        sec = m.group(1)
        for k in ["睡眠目标预设", "各阶段明细", "一致性复盘", "日记评级联动"]:
            if k in sec:
                v.append(f"睡眠模块含文字墙残留「{k}」（v4 紧凑三件套：指标表+字符条+评级行）")
        if "最终睡眠质量客观评级" not in sec:
            v.append("睡眠模块缺「最终睡眠质量客观评级」行")
        if "估算" not in sec and "📊 睡眠结构" not in sec:
            v.append("有设备日睡眠缺字符条形图（📊 睡眠结构）")
    # YAML sleep_duration 单位门禁（v4.2.0·2026-08-25根治：AI曾写入分钟数如390而非小时数如6.5·diary-template.md规范单位=小时）
    m_sd = re.search(r'^\s*sleep_duration:\s*([\d.]+)', content, re.M)
    if m_sd:
        sd_val = float(m_sd.group(1))
        if sd_val > 24:
            v.append(f"YAML sleep_duration 单位错误（值={sd_val}>24，应为小时数如6.5，禁止分钟数如{int(sd_val)}·diary-template.md规范）")
        elif sd_val == 0:
            v.append("YAML sleep_duration 为0（睡眠数据未填写）")
    # 心情区：三分三行 + 生理状态分 + 联动分析
    m = re.search(r'<!-- SECTION: MOOD_ENERGY -->\n(.*?)(?=\n---\n\n<!-- SECTION:|\Z)', content, re.DOTALL)
    mood = m.group(1) if m else ''
    if mood:
        for k in ["**⚡ 精力**：预测", "**🧘 平静**：预测", "**😌 满意**：实测", "生理状态分", "联动分析"]:
            if k not in mood:
                v.append(f"心情模块缺「{k}」（模板：三分维度三行+生理状态分+联动分析）")
    # 伙伴建议：三段式 + 署名
    m = re.search(r'<!-- SECTION: BUDDY_ADVICE -->\n(.*?)(?=\n---\s*\n?$)', content, re.DOTALL)
    adv = m.group(1) if m else ''
    if adv:
        for k in ["我看见的", "我想问的", "需关注"]:
            if k not in adv:
                v.append(f"伙伴建议缺「{k}」（仅👁️/❓/📌三段式）")
        if not re.search(r'^—— .*[\U0001F000-\U0001FAFF]', adv, re.M):
            v.append("伙伴建议缺署名（—— 你的 {动态前缀} {工具名} {emoji}）")
    # 灵感来源限字
    for line in content.split("\n"):
        if line.strip().startswith("> 来源：") and len(line.strip()) > 30:
            v.append("灵感来源行超长（>30字，v4 限一行≤15字·书名+来源）")
    # 有才显示：里程碑/悬置空表残留
    m = re.search(r'<!-- SECTION: MILESTONES -->\n(.*?)(?=\n<!-- SECTION:|\Z)', content, re.DOTALL)
    if m and re.search(r'\|\s*—\s*\|\s*—\s*\|\s*—\s*\|', m.group(1)):
        v.append("里程碑为空表未省略（v4 有才显示：无变更整块删）")
    m = re.search(r'<!-- SECTION: SUSPENSION -->\n(.*?)(?=\n<!-- SECTION:|\Z)', content, re.DOTALL)
    if m and re.search(r'\|\s*1\s*\|\s*\|\s*\|\s*\|\s*悬置\(未闭合\)\s*\|', m.group(1)) and "T5" not in m.group(1):
        v.append("悬置区为空表未省略（v4 有才显示：无残差整块删）")
    # 结尾铁律
    if not content.rstrip().endswith("---"):
        v.append("日记结尾非 `---`（v4 结尾铁律：署名 + ---）")
    return v


def extract_inspiration_from_file(path: Path) -> str:
    """从骨架文件中提取灵感闪现原文"""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    m = re.search(r'💡\s*\*\*灵感闪现\*\*：(.+?)(?:\n|$)', text)
    if m:
        quote = m.group(1).strip()
        if "待填入" not in quote:
            return quote
    return ""


def write_anchor_to_skeleton(skeleton_path: Path, anchor_text: str):
    """将续接锚点写入次日骨架"""
    if not skeleton_path.exists() or not anchor_text:
        return
    content = skeleton_path.read_text(encoding="utf-8")
    old = '> 📌 昨天说今天要做：（待填写）'
    new = f'> 📌 昨天说今天要做：{anchor_text}'
    if old in content:
        content = content.replace(old, new)
        skeleton_path.write_text(content, encoding="utf-8")


def main():
    # ─── 环境自检（第一性原理根治·沙箱假 python 拒绝空跑·exit 码族统一：环境故障=9）───
    if not dbenv.self_check(verbose=True):
        sys.exit(9)
    parser = argparse.ArgumentParser(description='日记封口（物理约束）')
    parser.add_argument('--date', required=True, help='当天日期，格式 YYYY-MM-DD')
    parser.add_argument('--skip-ingest', action='store_true',
                        help='显式跳过概念进料门禁（有痕跳过·封口块将如实标注未跑）')
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse 参数错误默认 exit 2——与语义 exit 2（次日骨架生成失败）冲突
        # 重映射为专用 exit 5（参数错误·2026-08-10 第一性原理根治：exit 数字语义唯一）
        raise SystemExit(5)

    try:
        today = datetime.date.fromisoformat(args.date)
    except ValueError as e:
        print(f"❌ 日期格式错误: {e}", file=sys.stderr)
        sys.exit(1)

    # === Step 1: 读取并校验今日日记 ===
    diary_content = read_diary(today)
    missing = validate_diary(diary_content)

    if missing:
        print(f"❌ 日记完整性校验失败，以下 SECTION 为空:", file=sys.stderr)
        for s in missing:
            print(f"   - {s}", file=sys.stderr)
        print(f"请先补齐以上内容，再调用本脚本封口。", file=sys.stderr)
        sys.exit(1)

    # === Step 1.5: 概念进料门禁（D-F9 · v3.20.1 物理阻断） ===
    ingest_status, ingest_text = read_concept_ingest(today)
    if ingest_status == "missing" and not args.skip_ingest:
        print("❌ 概念进料门禁：知识联邦 log.md 无当日 ingest 条目。", file=sys.stderr)
        print("   先执行工作流C步骤5.5：extract_concepts.py prepare → AI抽概念 → commit", file=sys.stderr)
        print("   （无源日 prepare 会自动写 skipped 条目，同样可过门禁）", file=sys.stderr)
        print("   确需跳过：加 --skip-ingest（封口块将如实标注'未跑·显式跳过'）", file=sys.stderr)
        sys.exit(3)
    if ingest_status == "missing" and args.skip_ingest:
        ingest_text = "⚠️ 概念抽取未跑（--skip-ingest 显式跳过）"

    # === Step 1.6: 评级门禁（v3.22.0 物理阻断·无跳过选项） ===
    # 背景：2026-07-31 错评事故（适用不存在的"番茄<16硬项"）+ 2026-07-10 待评定漏网封口。
    # 评级=全流程含金量最高判定，文本层门禁可被跳（7/26 实证），故下沉脚本层。
    # 设计：不提供 --skip 选项——评级无合法跳过场景（休整日有 N 级，不存在"不评级的日记"）。
    diary_rating = extract_rating(diary_content)
    diary_rating_reason = extract_rating_reason(diary_content)
    if diary_rating not in VALID_RATINGS:
        print(f"❌ 评级门禁：rating 当前为「{diary_rating}」，合法值为 S/A/B/C/N（不带引号·不带+/-）。", file=sys.stderr)
        print("   评级前先 Read references/achievement-rules.md（唯一权威源）+ sleep-module.md §四，再回填 YAML。", file=sys.stderr)
        sys.exit(4)
    if not diary_rating_reason:
        print("❌ 评级门禁：rating_reason 为空——评级必须附可追溯理由（引条款依据），否则拒绝封口。", file=sys.stderr)
        sys.exit(4)

    # === Step 1.65: 回填正文含金量 callout（v3.40.2 新增·消除 AI 漏填「待评定」占位） ===
    # 在格式门禁前先按 YAML 评级重写正文「待评定」占位，保证正文与 YAML 一致。
    diary_content = fill_rating_callout(diary_content, diary_rating, diary_rating_reason)
    diary_path = DIARY_BASE / today.strftime("%Y-%m") / f"{today}.md"
    diary_path.write_text(diary_content, encoding="utf-8")
    print(f"✅ 正文含金量 callout 已回填为「{diary_rating}」（{rating_callout_type(diary_rating)}）", file=sys.stderr)

    # === Step 1.7: 全模块格式门禁（v4.1.0 物理阻断·无跳过选项） ===
    # 背景：2026-08-07 你诊断"格式合规无物理约束、靠AI自律不可靠"——8/2/3 速读层空白、
    # 8/5/6 格式漂移、8/1 睡眠文字墙、伙伴建议4种格式并存、W31 错误信息抄4天。
    # 修法：把"模板格式"从文本层指导下沉为脚本层物理校验，与评级门禁(exit 4)同级。
    format_violations = check_diary_format(diary_content)
    if format_violations:
        print("❌ 格式门禁：日记未达 diary-template.md v4 模板标准：", file=sys.stderr)
        for vv in format_violations:
            print(f"   - {vv}", file=sys.stderr)
        print("   按模板逐模块修正后重新封口（速读层/含金量/睡眠紧凑/心情/伙伴建议/来源/有才显示/结尾/年度进度条）。", file=sys.stderr)
        sys.exit(6)

    # === Step 2: 生成次日骨架（幂等） ===
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_str = str(tomorrow)
    tomorrow_path = DIARY_BASE / tomorrow.strftime("%Y-%m") / f"{tomorrow}.md"

    if tomorrow_path.exists():
        print(f"ℹ️ 次日骨架已存在（幂等跳过）: {tomorrow_path}", file=sys.stderr)
    else:
        try:
            skeleton = build_skeleton(tomorrow_str)
            tomorrow_path.parent.mkdir(parents=True, exist_ok=True)
            tomorrow_path.write_text(skeleton, encoding="utf-8")
            print(f"✅ 次日骨架已生成: {tomorrow_path}", file=sys.stderr)
        except Exception as e:
            print(f"❌ 次日骨架生成失败: {e}", file=sys.stderr)
            sys.exit(2)

    # === Step 3: 写入续接锚点 ===
    anchor = extract_tomorrow_goals(diary_content)
    if anchor:
        write_anchor_to_skeleton(tomorrow_path, anchor)
        print(f"✅ 续接锚点已写入次日骨架", file=sys.stderr)

    # === Step 4: 提取确认数据并输出 JSON ===
    inspiration = extract_inspiration_from_file(tomorrow_path)
    rating = extract_rating(diary_content)

    # === Step 5: 计算年度进度 ===
    day_of_year = today.timetuple().tm_yday
    days_in_year = 366 if calendar.isleap(today.year) else 365
    year_progress = round(day_of_year / days_in_year * 100, 1)
    # 生成进度条（20格）
    filled = int(year_progress / 5)
    bar = '█' * filled + '░' * (20 - filled)
    year_progress_display = f"{bar} {year_progress}% (Day {day_of_year}/{days_in_year})"

    result = {
        "status": "sealed",
        "today": str(today),
        "today_rating": rating,
        "tomorrow_skeleton": f"{tomorrow}.md",
        "tomorrow_inspiration": inspiration,
        "tomorrow_anchor": anchor if anchor else "（今日未设明日目标）",
        "year_progress": year_progress_display,
        "concept_ingest": ingest_text,
    }

    # stdout 输出 JSON — AI 必须从此处取数据填入封口确认块
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
