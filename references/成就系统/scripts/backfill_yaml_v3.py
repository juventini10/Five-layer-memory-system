#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回填旧日记YAML v3：从正文提取三分维度 + 生理状态 + 满意度，写入achievement_data
v3新增：能量追踪表→energy_actual，分类评分→satisfaction，睡眠→physiological
用法：python3 backfill_yaml_v3.py [--dry-run]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
import yaml
from pathlib import Path
from statistics import mean, mode

DIARY_DIR = Path.home() / "[日记仓库]/1-每日计划/01-日记"  # 2026-10-13 入包前置：死路径→home 展开（同域 C3 写法同构·跨用户死路径根治）

# ─── 能量映射 ────────────────────────────────────────────────

ENERGY_MAP = {
    "🟢高": 5, "🟢 高": 5,
    "🟢": 4, "🟢中": 4, "🟢 中": 4,
    "🟡中": 3, "🟡 中": 3, "🟡": 3,
    "🟡低": 2, "🟡 低": 2,
    "🔴低": 1, "🔴 低": 1, "🔴": 1,
}


def extract_energy_from_tables(content):
    """从能量追踪表提取每日精力预测/实测
    
    格式A: | 上午 | 🟡 中 | 🟢 高 | ✅ → 预测=🟡, 实测=🟢
    格式B: | 时段 | 预测能量 | 实际能量 |
    格式C: | 预判能量 | 实际能量 | (任务表)
    """
    pred_values = []
    actual_values = []
    
    # ── 格式A：时段能量追踪表 (3月-4月) ──
    # | 上午 | 🟡 中 | 🟢 高 | ✅ 偏高 |
    for row in re.finditer(
        r'\|\s*(?:上午|下午|晚上|凌晨|全天)\s*\|'
        r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*)\s*\|'
        r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*|-)\s*\|',
        content
    ):
        pred_raw = row.group(1).strip()
        actual_raw = row.group(2).strip()
        
        if pred_raw in ENERGY_MAP:
            pred_values.append(ENERGY_MAP[pred_raw])
        if actual_raw in ENERGY_MAP:
            actual_values.append(ENERGY_MAP[actual_raw])
        elif actual_raw == '-' or actual_raw == '—':
            continue  # 未填写实际值
    
    # ── 格式B：时段 | 预测能量 | 实际能量 (早期变体) ──
    # | 下午 | 🟢 高 | 🟢 高 | ✅ |
    # (已经被格式A覆盖，这里是另一个列排列)
    if not pred_values:
        for row in re.finditer(
            r'\|\s*(?:上午|下午|晚上|凌晨|全天)\s*\|'
            r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*)\s*\|'
            r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*)\s*\|\s*✅',
            content
        ):
            pred_raw = row.group(1).strip()
            actual_raw = row.group(2).strip()
            if pred_raw in ENERGY_MAP:
                pred_values.append(ENERGY_MAP[pred_raw])
            if actual_raw in ENERGY_MAP:
                actual_values.append(ENERGY_MAP[actual_raw])
    
    # ── 格式C：任务表预判能量/实际能量列 (5月) ──
    # | 1 | 任务名 | ... | 上午 | 🟢高 | ⚠️未完成 | 🟢高 |
    if not pred_values:
        for row in re.finditer(
            r'\|\s*\d+\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*(?:上午|下午|晚上)\s*\|'
            r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*)\s*\|'
            r'\s*[^|]+\s*\|'
            r'\s*(🟢[^\|]*|🟡[^\|]*|🔴[^\|]*)',
            content
        ):
            pred_raw = row.group(1).strip()
            actual_raw = row.group(2).strip()
            if pred_raw in ENERGY_MAP:
                pred_values.append(ENERGY_MAP[pred_raw])
            if actual_raw in ENERGY_MAP:
                actual_values.append(ENERGY_MAP[actual_raw])
    
    return pred_values, actual_values


def extract_energy_from_analysis(content):
    """从能量分析文字段提取总体精力水平
    
    格式: 能量分析：
    - 上午（...）：🟡 中
    - 下午（...）：🟢 高
    """
    analysis = re.search(r'能量分析[：:]\s*\n((?:\s*[-•].*\n)*)', content)
    if not analysis:
        return []
    
    values = []
    for line in analysis.group(1).split('\n'):
        for emoji, val in ENERGY_MAP.items():
            if emoji in line:
                values.append(val)
                break
    
    return values


def extract_satisfaction(content):
    """从分类评分表提取满意度（取工作/健康/成长维度的均值映射到1-5）
    
    格式:
    | **工作** | ⭐⭐⭐⭐⭐ | 15🍅完成 |
    | **健康** | ⭐⭐⭐⭐ | 7h睡眠 |
    
    强制要求⭐存在，避免误匹配任务表格中的数字。
    """
    scores = []
    
    # 1. 分类评分表 | **工作** | ⭐⭐⭐⭐⭐ (5/5) | ...
    for m in re.finditer(
        r'\|\s*\**(?:工作|个人|成长|健康|阅读|学习)\**\s*\|\s*(⭐+)\s*(?:\(\d/?5\))?\s*\|',
        content
    ):
        stars = m.group(1)
        scores.append(stars.count('⭐'))  # ⭐⭐⭐⭐⭐ = 5, ⭐⭐⭐⭐ = 4
    
    # 2. 目标评估 **** 目标评估**: ⭐⭐⭐⭐⭐ (无/5)
    if not scores:
        m = re.search(r'目标评估\**\s*[：:]\**\s*(⭐+)', content)
        if m:
            scores.append(m.group(1).count('⭐'))
    
    # 3. 星级评分全文格式（5/9）
    if not scores:
        m = re.search(r'星级[：:].*?(\d)\s*/\s*5', content)
        if m:
            scores.append(int(m.group(1)))
    
    if not scores:
        return None
    
    # 平均后四舍五入到整数（1-5）
    avg = round(mean(scores))
    return max(1, min(5, avg))


def extract_physiological_from_sleep(sleep_quality, sleep_duration):
    """从睡眠质量和时长推导生理状态"""
    if sleep_quality is None and sleep_duration is None:
        return None
    
    score = 0  # 0-2, higher = worse
    
    # 质量
    if sleep_quality == "A":
        score += 0
    elif sleep_quality == "B":
        score += 0
    elif sleep_quality == "C":
        score += 1
    
    # 时长
    if sleep_duration is not None:
        if sleep_duration >= 7:
            score += 0
        elif sleep_duration >= 6:
            score += 0
        elif sleep_duration >= 5:
            score += 1
        else:
            score += 1
    
    if score <= 0:
        return "green"
    elif score == 1:
        return "yellow"
    else:
        return "red"


def update_yaml_fields(filepath, fields):
    """更新日记YAML frontmatter中的achievement_data字段
    
    fields: dict of field_name → value (None means skip)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    m = re.match(r'^(---\s*\n)(.*?)(\n---)', content, re.DOTALL)
    if not m:
        return False, "NO_YAML"
    
    before = m.group(1)
    fm_text = m.group(2)
    after = m.group(3)
    body = content[m.end():]
    
    # 对每个field执行替换
    new_fm = fm_text
    for field, value in fields.items():
        if value is None:
            continue
        
        # 替换 achievement_data 块内的 field 行
        # 匹配:   field_name: 0 或   field_name: 3
        old_val = re.search(
            rf'(\s+{field}:\s*)(-?\d+(?:\.\d+)?|null|None|"[^"]*"|\'[^\']*\')?(.*)',
            new_fm
        )
        if old_val:
            new_fm = re.sub(
                rf'(\s+{field}:\s*)(-?\d+(?:\.\d+)?|null|None|"[^"]*"|\'[^\']*\')?(\s*#.*)?$',
                rf'\g<1>{value}',
                new_fm,
                flags=re.MULTILINE
            )
    
    if new_fm == fm_text:
        return False, "NO_CHANGE"
    
    new_content = before + new_fm + after + body
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, "OK"


def fmt_val(v):
    """格式化值为可读字符串"""
    if v is None:
        return "N/A"
    if isinstance(v, float):
        return str(round(v, 1))
    return str(v)


def main():
    dry_run = '--dry-run' in sys.argv
    files = sorted(DIARY_DIR.glob('**/2026-*.md'))
    
    stats = {
        "energy": 0, "calm": 0, "satisfaction": 0, "physio": 0,
        "skipped": 0
    }
    
    for fpath in files:
        if '备份' in fpath.name:
            continue
        
        content = fpath.read_text(encoding='utf-8')
        
        m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not m:
            continue
        
        fm = yaml.safe_load(m.group(1))
        ad = fm.get('achievement_data', {}) if isinstance(fm, dict) else {}
        body = content[m.end():]
        
        fields_to_write = {}
        
        # ── energy_pred / energy_actual ──
        ep_cur = ad.get('energy_pred', 'MISSING')
        ea_cur = ad.get('energy_actual', 'MISSING')
        
        if ep_cur == 0 or ep_cur == 'MISSING':
            # 先尝试标准三分维度格式 (v2已支持)
            m_energy = re.search(r'精力.*?预测\s*[\[（(]?(\d)[\]）)]?.*?实测\s*[\[（(]?(\d)[\]）)]?', body)
            if m_energy:
                fields_to_write['energy_pred'] = int(m_energy.group(1))
                fields_to_write['energy_actual'] = int(m_energy.group(2))
            else:
                # 从能量表格提取
                pred_vals, actual_vals = extract_energy_from_tables(body)
                if pred_vals:
                    fields_to_write['energy_pred'] = round(mean(pred_vals))
                if actual_vals:
                    fields_to_write['energy_actual'] = round(mean(actual_vals))
                elif pred_vals:
                    # 无实际值，pred=actual (保守策略)
                    fields_to_write['energy_actual'] = round(mean(pred_vals))
        
        if fields_to_write.get('energy_pred') is not None:
            stats['energy'] += 1
        
        # ── calm_pred / calm_actual ──
        cp_cur = ad.get('calm_pred', 'MISSING')
        ca_cur = ad.get('calm_actual', 'MISSING')
        
        if cp_cur == 0 or cp_cur == 'MISSING':
            m_calm = re.search(r'平静.*?预测\s*[\[（(]?(\d)[\]）)]?.*?实测\s*[\[（(]?(\d)[\]）)]?', body)
            if m_calm:
                fields_to_write['calm_pred'] = int(m_calm.group(1))
                fields_to_write['calm_actual'] = int(m_calm.group(2))
                stats['calm'] += 1
        elif cp_cur != 0:
            stats['calm'] += 1  # already has data
        
        # ── satisfaction ──
        sat_cur = ad.get('satisfaction', 'MISSING')
        
        if sat_cur == 0 or sat_cur == 'MISSING':
            # 先尝试标准格式
            m_sat = re.search(r'满意.*?[预实]测\s*[\[（(]?(\d)[\]）)]?', body)
            if m_sat:
                fields_to_write['satisfaction'] = int(m_sat.group(1))
            else:
                sat = extract_satisfaction(body)
                if sat is not None:
                    fields_to_write['satisfaction'] = sat
        
        if fields_to_write.get('satisfaction') is not None:
            stats['satisfaction'] += 1
        
        # ── physiological ──
        phys_cur = ad.get('physiological', 'MISSING')
        
        if phys_cur == 0 or phys_cur == 'MISSING' or phys_cur == '':
            # 先尝试从正文提取
            m_phys = re.search(r'生理状态[^:：]*[：:]\s*(🟢|🟡|🔴)', body)
            if m_phys:
                mapping = {"🟢": "green", "🟡": "yellow", "🔴": "red"}
                fields_to_write['physiological'] = mapping[m_phys.group(1)]
            else:
                # 从睡眠推导
                sleep_q = ad.get('sleep_quality')
                sleep_d = ad.get('sleep_duration')
                phys = extract_physiological_from_sleep(sleep_q, sleep_d)
                if phys:
                    fields_to_write['physiological'] = phys
        
        if fields_to_write.get('physiological_status') is not None:
            stats['physio'] += 1
        
        # ── 写入 ──
        if not fields_to_write:
            stats['skipped'] += 1
            continue
        
        if dry_run:
            detail = [f"{k}={fmt_val(v)}" for k, v in fields_to_write.items()]
            print(f"  DRY-RUN: {fpath.name} → {', '.join(detail)}")
        else:
            ok, detail = update_yaml_fields(fpath, fields_to_write)
            if ok:
                detail = [f"{k}={fmt_val(v)}" for k, v in fields_to_write.items()]
                print(f"  ✅ {fpath.name}: {', '.join(detail)}")
            else:
                print(f"  ❌ {fpath.name}: {detail}")
    
    print(f"\n📊 汇总: 精力{stats['energy']}篇 | 平静{stats['calm']}篇 | 满意{stats['satisfaction']}篇 | 生理{stats['physio']}篇 | 跳过{stats['skipped']}篇")
    if dry_run:
        print("⚠️ --dry-run模式，未实际修改文件")


if __name__ == "__main__":
    main()
