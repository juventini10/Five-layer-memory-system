#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复日记YAML中的tomato字段：从正文重新提取每日番茄数，写回YAML
解决回填脚本v1错误覆盖tomato=0的问题

用法：python3 repair_tomato_yaml.py [--dry-run]
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
import yaml
from pathlib import Path

DIARY_DIR = Path.home() / "[日记仓库]" / "1-每日计划" / "01-日记"   # 2026-09-20 C3：绝对路径→home 展开（跨用户死路径根治·⑪检查实锤）


def extract_daily_tomato(content, fname):
    """从正文提取当日番茄数，返回 (value, source) 或 (0, 'NONE')"""
    
    # P0: 今日番茄（兼容 今日番茄：2🍅 / 今日番茄累计：~8🍅 / 今日番茄累计：**14🍅**）
    m = re.search(r"-?\s*今日番茄(?:累计)?[：:]\s*~?\*{0,2}(\d+(?:\.\d+)?)\*{0,2}\s*🍅", content)
    if m:
        return float(m.group(1)), "今日番茄"
    
    # P1: 今日实际**：X🍅
    m = re.search(r"\*{0,2}今日实际\*{0,2}[：:]?\s*(\d+(?:\.\d+)?)\s*🍅", content)
    if m:
        return float(m.group(1)), "今日实际"
    
    # P2: 实际完成番茄总数**：X🍅
    m = re.search(r"实际完成番茄总数[*]+[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
    if m:
        return float(m.group(1)), "实际完成番茄总数"
    
    # P3: 番茄总数**：X🍅
    m = re.search(r"番茄总数[*]+[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
    if m:
        return float(m.group(1)), "番茄总数"
    
    # P4: 总实际**：X🍅 （3月日记常用）—— 但有风险：里程碑盘点日记的"总实际"=多日累计
    m = re.search(r"\*{0,2}总实际\*{0,2}[：:]?\s*(?:约\s*)?(\d+(?:\.\d+)?)\s*🍅", content)
    if m:
        val = float(m.group(1))
        # 检测里程碑/Phase关键词，标记可疑
        if re.search(r'里程碑|Phase\s*\d|阶段\d|累计完成', content[:500]):
            if val > 20:
                print(f"  ⚠️ {fname}: 总实际={val}但检测到里程碑标记，设为0")
                return 0, "MILESTONE_SKIP"
        # 值>25才判定异常（正常日记最高可能到24左右,如4/2=22.5、4/13=21.5、5/14=20都是真值）
        if val > 25:
            table_sum = _sum_table_tomato(content)
            if 0 < table_sum < 20:
                return table_sum, f"TABLE_SUM(总实际={val}异常→降级)"
            print(f"  ⚠️ {fname}: 总实际={val}>20异常，无可靠表格兜底，设为0")
            return 0, "OUTLIER_SKIP"
        return val, "总实际"
    
    # P5: 实际执行**：X🍅
    m = re.search(r"\*{0,2}实际执行\*{0,2}[：:]\s*(\d+(?:\.\d+)?)\s*🍅", content)
    if m:
        return float(m.group(1)), "实际执行"
    
    # P6: 表格✅行求和
    table_sum = _sum_table_tomato(content)
    if table_sum > 0:
        return table_sum, "TABLE_SUM"
    
    return 0, "NONE"


def _sum_table_tomato(content):
    """从P1/P2任务表格提取✅行的实际番茄数求和"""
    total = 0
    for row in re.finditer(r"\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*P\d\s*\|\s*[^|]*\s*\|\s*[^|]*\s*\|\s*(\d+(?:\.\d+)?)\s*\|\s*✅", content):
        total += float(row.group(1))
    return total


def update_yaml_tomato(filepath, tomato_val):
    """更新日记YAML frontmatter中的achievement_data.tomato字段"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取YAML frontmatter
    m = re.match(r'^(---\s*\n)(.*?)(\n---)', content, re.DOTALL)
    if not m:
        return False, "NO_YAML"
    
    before = m.group(1)
    fm_text = m.group(2)
    after = m.group(3)
    body = content[m.end():]
    
    # 定位 achievement_data 块中的 tomato 行
    # 格式:   tomato: 0  → 替换值
    new_fm = re.sub(
        r'(\s+tomato:\s*)\d+(\.\d+)?',
        rf'\g<1>{tomato_val}',
        fm_text
    )
    
    if new_fm == fm_text:
        return False, "NO_TOMATO_LINE"
    
    new_content = before + new_fm + after + body
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True, str(tomato_val)


def main():
    dry_run = '--dry-run' in sys.argv
    files = sorted(DIARY_DIR.glob('**/2026-*.md'))
    
    stats = {"fixed": 0, "unchanged": 0, "zero_correct": 0, "errors": 0, "milestone_skip": 0}
    
    for fpath in files:
        if '备份' in fpath.name:
            continue
        
        content = fpath.read_text(encoding='utf-8')
        
        # 先读当前YAML的tomato
        m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        current_yaml_tomato = None
        if m:
            fm = yaml.safe_load(m.group(1))
            if isinstance(fm, dict):
                ad = fm.get('achievement_data', {})
                current_yaml_tomato = ad.get('tomato')
        
        # 从正文提取
        tomato_val, source = extract_daily_tomato(content, fpath.name)
        
        # 决策
        if tomato_val == 0:
            if current_yaml_tomato is None or current_yaml_tomato == 0:
                stats['zero_correct'] += 1
                continue
            # YAML有值但正文提取为0 → 保持YAML不变
            stats['unchanged'] += 1
            continue
        
        # tomato > 0，需要写回
        if current_yaml_tomato == tomato_val:
            stats['unchanged'] += 1
            continue
        
        if dry_run:
            print(f"  DRY-RUN: {fpath.name} tomato {current_yaml_tomato} → {tomato_val} [{source}]")
            stats['fixed'] += 1
        else:
            ok, detail = update_yaml_tomato(fpath, tomato_val)
            if ok:
                status = "✅" if current_yaml_tomato != tomato_val else "⏭️"
                print(f"  {status} {fpath.name}: {current_yaml_tomato} → {tomato_val} [{source}]")
                stats['fixed'] += 1
            else:
                print(f"  ❌ {fpath.name}: {detail} (want {tomato_val})")
                stats['errors'] += 1
    
    print(f"\n📊 汇总: 修复{stats['fixed']}篇 | 无需改{stats['unchanged']}篇 | 零值正确{stats['zero_correct']}篇 | 错误{stats['errors']}篇")
    if dry_run:
        print("⚠️ --dry-run模式，未实际修改文件")


if __name__ == "__main__":
    main()
