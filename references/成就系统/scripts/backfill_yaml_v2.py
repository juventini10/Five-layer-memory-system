#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回填旧日记YAML：从正文提取数据 → 写入achievement_data的v2.0 12字段
用法：python3 backfill_yaml_v2.py [--dry-run] [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
import yaml
from pathlib import Path

DIARY_DIR = Path.home() / "[日记仓库]/1-每日计划/01-日记"  # 2026-10-13 入包前置：死路径→home 展开（同域 C3 写法同构·跨用户死路径根治）

# ─── 提取函数 ────────────────────────────────────────────────

def extract_sleep_table(content):
    """从睡眠表格提取入睡/起床/时长/质量"""
    result = {}
    
    # 定位睡眠区域：旧日记用 ## 🛏，新日记用 <!-- SECTION: SLEEP -->
    sleep_section_start = None
    patterns = [
        r'<!-- SECTION: SLEEP -->',
        r'## 😴 睡眠',
        r'## 🛏 睡眠',
        r'## 🛏️ 睡眠',
        r'## 1️⃣ 😴 睡眠',
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            sleep_section_start = m.start()
            break
    
    section = content[sleep_section_start:] if sleep_section_start else content
    # 截断到下一个 SECTION 标记（不按##截断，避免误匹配睡眠section自身的子标题）
    next_sec = re.search(r'<!-- SECTION:', section[5:])
    if next_sec:
        section = section[:5 + next_sec.start()]
    else:
        section = section[:800]
    
    # ── 精准格式优先（不会抓到偏差列） ──
    
    # F5: 6/3+ | 入睡时间 | 01:10 |（单值表格）
    m = re.search(r"\|\s*入睡时间\s*\|\s*(\d{1,2}:\d{2})", section)
    if m:
        result["sleep_time"] = m.group(1)
    m = re.search(r"\|\s*(?:起床时间|醒来时间)\s*\|\s*(\d{1,2}:\d{2})", section)
    if m:
        result["wake_time"] = m.group(1)
    
    # F6: 三列表格 | 核心指标 | 预设目标 | 实际数据 |
    # | 入睡/起床时间 | 23:30前/07:30前 | 19:50/07:20 |
    if not result.get("sleep_time"):
        m = re.search(r"\|\s*入睡/起床时间\s*\|\s*[^\|]*\|\s*(\d{1,2}:\d{2})/(\d{1,2}:\d{2})", section)
        if m:
            result["sleep_time"] = m.group(1)
            result["wake_time"] = m.group(2)
    
    # F7: 加粗文字 **入睡时间**：23:05
    if not result.get("sleep_time"):
        m = re.search(r'\*\*入睡时间\*\*[：:]\s*(\d{1,2}:\d{2})', section)
        if m:
            result["sleep_time"] = m.group(1)
    if not result.get("wake_time"):
        m = re.search(r'\*\*(?:起床时间|醒来时间)\*\*[：:]\s*(\d{1,2}:\d{2})', section)
        if m:
            result["wake_time"] = m.group(1)
    
    # F3: 5/13+ | 入睡/醒来 | 23:33/03:41 |（单行对栏）
    if not result.get("sleep_time"):
        m = re.search(r"\|\s*入睡.*?醒来.*?\|\s*(\d{1,2}:\d{2})/(\d{1,2}:\d{2})", section)
        if m:
            result["sleep_time"] = m.group(1)
            result["wake_time"] = m.group(2)
    
    # F4: 5/12+ 三列对比表
    # | 入睡/起床时间 | 23:30/07:30 | 23:38/05:55 |
    if not result.get("sleep_time"):
        m = re.search(r"\|\s*入睡.*?起床时间.*?\|\s*\d{1,2}:\d{2}/\d{1,2}:\d{2}\s*\|\s*(\d{1,2}:\d{2})/(\d{1,2}:\d{2})", section)
        if m:
            result["sleep_time"] = m.group(1)
            result["wake_time"] = m.group(2)
    
    # ── 模糊格式（只在上面都失败时才用） ──
    
    # F1: 早期表格 | 入睡 | 起床 | 时长 | 质量 |
    if not result.get("sleep_time"):
        m = re.search(r"\|\s*(\d{1,2}:\d{2})\s*\|\s*(\d{1,2}:\d{2})\s*\|\s*([^\|\n]*?)\s*\|(?:\s*([^\|\n]*?)\s*\|)", section)
        if m:
            result["sleep_time"] = m.group(1)
            result["wake_time"] = m.group(2)
            result["_raw_duration"] = m.group(3).strip() if not result.get("_raw_duration") else result["_raw_duration"]
            if m.group(4) and not result.get("_raw_quality"):
                result["_raw_quality"] = m.group(4).strip()
    
    # F2: 简单两列数字
    if not result.get("sleep_time"):
        m = re.search(r"\|\s*(\d{1,2}:\d{2})\s*\|\s*(\d{1,2}:\d{2})\s*\|", section)
        if m:
            result["sleep_time"] = m.group(1)
            result["wake_time"] = m.group(2)
    
    # 提取时长（各种格式）— 优先匹配时长行
    if not result.get("_raw_duration"):
        # 中文全称：**总睡眠时长**：6小时25分钟 / 总时长：7h42m
        m = re.search(r'(?:总睡眠时长|总时长|总睡眠)\*{0,2}[：:]\s*(?:\*{0,2})?(\d+)\s*小时\s*(\d+)\s*分钟', section)
        if m:
            result["_raw_duration"] = f"{m.group(1)}h{m.group(2)}m"
        else:
            m = re.search(r'(?:总时长|总睡眠时长|实际睡眠时长|睡眠时长).*?\|\s*\*{0,2}(\d+)h(\d+)(?:min|m)', section)
            if m:
                result["_raw_duration"] = f"{m.group(1)}h{m.group(2)}m"
            else:
                # 纯小时
                m = re.search(r'(?:总时长|总睡眠时长|实际睡眠时长|睡眠时长)[^\n]*?(\d+(?:\.\d+)?)\s*h', section, re.IGNORECASE)
                if m:
                    result["_raw_duration"] = f"{m.group(1)}h"
                else:
                    m = re.search(r'(\d+)\s*h(?:our)?', section, re.IGNORECASE)
                    if m:
                        result["_raw_duration"] = f"{m.group(1)}h"
    
    # 提取质量评级（新版日记）
    if not result.get("_raw_quality"):
        m = re.search(r'(?:睡眠评级|最终评级)[：:]\s*([^\n]+)', section)
        if m:
            result["_raw_quality"] = m.group(1).strip()
    
    return result


def parse_duration(raw, sleep_t, wake_t):
    """计算睡眠时长（小时），优先从raw解析，失败则算时间差"""
    if raw:
        # "7h18m" / "3h56min"
        m = re.search(r'(\d+(?:\.\d+)?)\s*h\s*(\d+)\s*(?:min|m)\b', raw, re.IGNORECASE)
        if m:
            return round(float(m.group(1)) + int(m.group(2)) / 60, 1)
        # 纯小时
        m = re.search(r'(\d+(?:\.\d+)?)\s*[hH]', raw)
        if m:
            return round(float(m.group(1)), 1)
        # 中文格式 "6小时25分钟"
        m = re.search(r'(\d+)\s*小时\s*(\d+)\s*分', raw)
        if m:
            return round(int(m.group(1)) + int(m.group(2)) / 60, 1)
    
    if sleep_t and wake_t:
        try:
            sh, sm = map(int, sleep_t.split(":"))
            wh, wm = map(int, wake_t.split(":"))
            sleep_min = sh * 60 + sm
            wake_min = wh * 60 + wm
            if wake_min <= sleep_min:
                wake_min += 24 * 60
            return round((wake_min - sleep_min) / 60, 1)
        except:
            pass
    return None


def parse_sleep_quality(raw):
    """从质量列文字提取A/B/C"""
    if not raw:
        return None
    raw_up = raw.strip().upper()
    if raw_up in ("A", "B", "C"):
        return raw_up
    # 正面
    if "✅" in raw or "优秀" in raw or "达标" in raw or "深睡" in raw or "良好" in raw:
        return "A"
    # 中性/一般
    if "🟡" in raw or "一般" in raw or "及格" in raw or "中等" in raw:
        return "B"
    # 负面
    if "⚠" in raw or "🔴" in raw or "不足" in raw or "严重" in raw or "差" in raw:
        return "C"
    return raw.strip()


def extract_three_dimensions(content):
    """提取三分维度（精力预测/实测、平静预测/实测、满意度）"""
    result = {}
    
    # 格式1：标准格式 **⚡ 精力**：预测 [3] → 实测 [4]  
    m = re.search(r'精力.*?预测\s*[\[（(]?(\d)[\]）)]?.*?实测\s*[\[（(]?(\d)[\]）)]?', content)
    if m:
        result["energy_pred"] = int(m.group(1))
        result["energy_actual"] = int(m.group(2))
    
    m = re.search(r'平静.*?预测\s*[\[（(]?(\d)[\]）)]?.*?实测\s*[\[（(]?(\d)[\]）)]?', content)
    if m:
        result["calm_pred"] = int(m.group(1))
        result["calm_actual"] = int(m.group(2))
    
    # 满意度：标准/无括号格式
    m = re.search(r'满意.*?[预实]测\s*[\[（(]?(\d)[\]）)]?', content)
    if m:
        result["satisfaction"] = int(m.group(1))
    
    return result


def extract_physiological(content):
    """提取生理状态"""
    m = re.search(r'生理状态[^:：]*[：:]\s*(🟢|🟡|🔴)', content)
    if m:
        raw = m.group(1)
        return {"🟢": "green", "🟡": "yellow", "🔴": "red"}.get(raw, "green")
    return None


def parse_existing_yaml(content):
    """解析已有YAML frontmatter"""
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if m:
        try:
            return yaml.safe_load(m.group(1)) or {}, m.start(), m.end()
        except yaml.YAMLError:
            return {}, m.start(), m.end()
    return {}, -1, -1


# ─── YAML序列化 ──────────────────────────────────────────────

def fmt_val(val):
    if isinstance(val, str):
        if val == "":
            return '""'
        return f'"{val}"'
    if isinstance(val, (int, float)):
        return str(val)
    if val is None:
        return '""'
    return f'"{val}"' 


def dump_yaml(obj):
    """手工序列化YAML，保持字段顺序"""
    lines = []
    for key in ["date", "day_of_week", "tags", "rating", "rating_reason"]:
        if key in obj:
            if isinstance(obj[key], list):
                items = ", ".join(obj[key])
                lines.append(f"{key}: [{items}]")
            elif isinstance(obj[key], str):
                lines.append(f'{key}: "{obj[key]}"' if (obj[key] and any(c in obj[key] for c in ':#{}[],&*?!')) else f'{key}: {obj[key]}')
            else:
                lines.append(f"{key}: {obj[key]}")
    
    if "achievement_data" in obj:
        lines.append("achievement_data:")
        ad = obj["achievement_data"]
        for f in ["tomato", "sleep_time", "wake_time", "sleep_duration",
                   "sleep_quality", "energy_pred", "energy_actual",
                   "calm_pred", "calm_actual", "satisfaction", "physiological"]:
            lines.append(f"  {f}: {fmt_val(ad.get(f, ''))}")
    
    return "\n".join(lines) + "\n"


# ─── 回填单篇 ────────────────────────────────────────────────

def backfill_one(filepath, dry_run=True):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    existing, yaml_start, yaml_end = parse_existing_yaml(content)
    if yaml_end <= 0:
        return str(filepath), 0, ["无YAML块"]
    
    sleep_data = extract_sleep_table(content)
    dim_data = extract_three_dimensions(content)
    physio = extract_physiological(content)
    
    ad = existing.get("achievement_data", {}) or {}
    if not isinstance(ad, dict):
        ad = {}
    
    # 取旧值用于比较
    old_ad = dict(ad)
    
    # 【关键】老字段不覆盖：tomato/sleep_time/wake_time由每日伙伴维护，回填只补新字段
    if not ad.get("tomato"):
        ad["tomato"] = 0
    
    # 睡眠时间：正文表格优先（只在原YAML没有sleep_time时补）
    if sleep_data.get("sleep_time") and not ad.get("sleep_time"):
        ad["sleep_time"] = sleep_data["sleep_time"]
    if sleep_data.get("wake_time") and not ad.get("wake_time"):
        ad["wake_time"] = sleep_data["wake_time"]
    
    # 新8字段：从正文提取（如果之前没有值）
    dur = parse_duration(sleep_data.get("_raw_duration", ""), ad.get("sleep_time"), ad.get("wake_time"))
    if dur is not None and (ad.get("sleep_duration") in (None, 0)):
        ad["sleep_duration"] = dur
    
    qual = parse_sleep_quality(sleep_data.get("_raw_quality", ""))
    if qual and not ad.get("sleep_quality"):
        ad["sleep_quality"] = qual
    
    for k in ["energy_pred", "energy_actual", "calm_pred", "calm_actual", "satisfaction"]:
        if dim_data.get(k) is not None and ad.get(k) in (None, 0):
            ad[k] = dim_data[k]
    
    if physio and not ad.get("physiological"):
        ad["physiological"] = physio
    
    # 补默认值
    for k in ["tomato", "sleep_time", "wake_time", "sleep_duration",
              "sleep_quality", "energy_pred", "energy_actual",
              "calm_pred", "calm_actual", "satisfaction", "physiological"]:
        if k not in ad or ad[k] is None:
            ad[k] = "" if k in ("sleep_time", "wake_time", "sleep_quality", "physiological") else 0
    
    # 统计变化
    changes = []
    for k in ["sleep_duration", "sleep_quality", "energy_pred", "energy_actual",
              "calm_pred", "calm_actual", "satisfaction", "physiological"]:
        old = old_ad.get(k)
        new = ad.get(k)
        if str(old) != str(new) and str(new) not in ("0", ""):
            changes.append(f"{k}: {old}→{new}")
    
    if not dry_run:
        existing["achievement_data"] = ad
        # 保留rating
        if "rating" not in existing:
            existing["rating"] = ""
        if "rating_reason" not in existing:
            existing["rating_reason"] = ""
        
        new_yaml = dump_yaml(existing)
        rest = content[yaml_end:]
        new_content = f"---\n{new_yaml}---" + rest
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
    
    return filepath.name, len(changes), changes


# ─── 入口 ────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv
    start_date = end_date = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--start" and i + 1 < len(args):
            start_date = args[i + 1]
        if a == "--end" and i + 1 < len(args):
            end_date = args[i + 1]
    
    files = sorted(DIARY_DIR.glob("2026-*/2026-*.md"))
    files = [f for f in files if "备份" not in f.name]
    if start_date:
        files = [f for f in files if f.stem >= start_date]
    if end_date:
        files = [f for f in files if f.stem <= end_date]
    
    print(f"{'🔍 [DRY RUN] ' if dry_run else ''}处理 {len(files)} 篇日记...\n")
    
    total_changes = 0
    no_change = 0
    changed = []
    
    for fp in files:
        fname, n, chgs = backfill_one(fp, dry_run=dry_run)
        if n > 0:
            total_changes += n
            changed.append((fname, chgs))
            print(f"  ✅ {fname}: +{n}字段 {chgs}")
        else:
            no_change += 1
    
    print(f"\n{'🔍 [DRY RUN] ' if dry_run else '✅ '}"
          f"完成：{len(changed)}篇更新 / {no_change}篇无需变更 / {total_changes}个字段")


if __name__ == "__main__":
    main()
