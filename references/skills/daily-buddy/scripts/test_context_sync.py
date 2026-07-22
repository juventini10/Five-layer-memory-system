#!/usr/bin/env python3
"""
测试脚本：验证周报与情景层的联动流程
功能：
1. 读取最新周报
2. 读取情景层文件
3. 验证数据一致性
4. 输出验证结果
"""

import os
import re
import sys

# 路径配置
WEEKLY_REPORT_DIR = os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/Local_Obsidian_Vault/1-每日计划/02-周报"))
CONTEXT_FILE = os.path.expanduser("~/个人AI档案/情境层/动态状态快照.md")


def get_latest_weekly_report():
    """获取最新的周报文件"""
    files = [f for f in os.listdir(WEEKLY_REPORT_DIR) if f.startswith("2026-W") and f.endswith(".md")]
    if not files:
        print("错误：未找到周报文件")
        return None
    # 按文件名排序，获取最新的周报
    files.sort(reverse=True)
    return os.path.join(WEEKLY_REPORT_DIR, files[0])


def read_file(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败: {e}")
        return None


def extract_weekly_data(content):
    """从周报中提取数据"""
    data = {}
    
    # 提取90天目标对齐
    goal_alignment_match = re.search(r'## 4️⃣ 90天目标对齐.*?-(.*?)- \*\*进度评估\*\*：(.*?)(?=---)', content, re.DOTALL)
    if goal_alignment_match:
        data['goal_progress'] = goal_alignment_match.group(2).strip()
    
    # 提取情景层卡点跟进
    卡点_match = re.search(r'## 5️⃣ 情景层卡点跟进.*?\*\*当前卡点\*\*：(.*?)(?=- \*\*上周进展\*\*|$)', content, re.DOTALL)
    if 卡点_match:
        data['current_block'] = 卡点_match.group(1).strip()
    
    # 提取本周计划中的高紧急任务
    weekly_plan_match = re.search(r'## 7️⃣ 本周计划.*?### 核心目标(.*?)(?=### 关键任务分解|$)', content, re.DOTALL)
    if weekly_plan_match:
        plan_content = weekly_plan_match.group(1)
        high_priority_tasks = []
        for line in plan_content.strip().split('\n'):
            if '(紧急程度：高)' in line:
                task = line.strip().split('**')[1].split('：')[0]
                high_priority_tasks.append(task)
        data['high_priority_tasks'] = high_priority_tasks
    
    # 提取上周计划完成情况
    last_week_match = re.search(r'## 6️⃣ 上周计划完成情况.*?(?=## 7️⃣ 本周计划)', content, re.DOTALL)
    if last_week_match:
        last_week_content = last_week_match.group(0)
        # 提取核心目标完成情况
        core_goals_match = re.search(r'### 核心目标完成情况.*?\| 状态 \|(.*?)(?=### 关键任务完成情况|$)', last_week_content, re.DOTALL)
        if core_goals_match:
            goals_content = core_goals_match.group(1)
            progress_items = []
            for line in goals_content.strip().split('\n'):
                if '|' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 4:
                        goal = parts[0]
                        status = parts[3]
                        if status == '✅ 完成':
                            progress_items.append(f"✅ {goal}")
                        elif '❌' in status:
                            progress_items.append(f"⚠️ {goal}未达标")
            data['last_week_progress'] = progress_items
    
    return data


def extract_context_data(content):
    """从情景层中提取数据"""
    data = {}
    
    # 提取90天北极星
    北极星_match = re.search(r'\*\*90天北极星\*\*：(.+)', content)
    if 北极星_match:
        data['北极星'] = 北极星_match.group(1).strip()
    
    # 提取当前卡点
    卡点_match = re.search(r'\*\*当前卡点\*\*：(.+?)(?=\s+\(|$)', content)
    if 卡点_match:
        data['当前卡点'] = 卡点_match.group(1).strip()
    
    # 提取本周紧急
    紧急_match = re.search(r'\*\*本周紧急\*\*：(.+?)(?=\s+\(|$)', content)
    if 紧急_match:
        data['本周紧急'] = 紧急_match.group(1).strip()
    
    # 提取上周进展
    进展_match = re.search(r'\*\*上周进展\*\*：\n(.*?)(?=- \*\*拖延的事\*\*|$)', content, re.DOTALL)
    if 进展_match:
        进展_content = 进展_match.group(1)
        进展_items = [item.strip() for item in 进展_content.strip().split('\n') if item.strip()]
        data['上周进展'] = 进展_items
    
    # 提取目标进度
    进度_match = re.search(r'\*\*目标进度\*\*：(.+)', content)
    if 进度_match:
        data['目标进度'] = 进度_match.group(1).strip()
    
    return data


def validate_sync(weekly_data, context_data):
    """验证周报与情景层的数据一致性"""
    results = []
    
    # 验证当前卡点
    if 'current_block' in weekly_data and '当前卡点' in context_data:
        if weekly_data['current_block'] in context_data['当前卡点']:
            results.append("✅ 当前卡点同步正确")
        else:
            results.append(f"❌ 当前卡点同步错误: 周报='{weekly_data['current_block']}', 情景层='{context_data['当前卡点']}'")
    
    # 验证本周紧急任务
    if 'high_priority_tasks' in weekly_data and '本周紧急' in context_data:
        if weekly_data['high_priority_tasks']:
            high_task = weekly_data['high_priority_tasks'][0]
            if high_task in context_data['本周紧急']:
                results.append("✅ 本周紧急任务同步正确")
            else:
                results.append(f"❌ 本周紧急任务同步错误: 周报='{high_task}', 情景层='{context_data['本周紧急']}'")
    
    # 验证目标进度
    if 'goal_progress' in weekly_data and '目标进度' in context_data:
        if weekly_data['goal_progress'] in context_data['目标进度']:
            results.append("✅ 目标进度同步正确")
        else:
            results.append(f"❌ 目标进度同步错误: 周报='{weekly_data['goal_progress']}', 情景层='{context_data['目标进度']}'")
    
    # 验证上周进展
    if 'last_week_progress' in weekly_data and '上周进展' in context_data:
        # 检查周报中的进展是否在情景层中
        match_count = 0
        for weekly_item in weekly_data['last_week_progress']:
            for context_item in context_data['上周进展']:
                if weekly_item in context_item or context_item in weekly_item:
                    match_count += 1
                    break
        if match_count >= len(weekly_data['last_week_progress']) * 0.8:
            results.append("✅ 上周进展同步正确")
        else:
            results.append("❌ 上周进展同步错误: 部分进展未同步")
    
    return results


def main():
    """主函数"""
    print("=== 周报与情景层联动测试 ===")
    
    # 获取最新周报
    latest_report = get_latest_weekly_report()
    if not latest_report:
        return
    
    print(f"最新周报: {os.path.basename(latest_report)}")
    
    # 读取文件内容
    weekly_content = read_file(latest_report)
    context_content = read_file(CONTEXT_FILE)
    
    if not weekly_content or not context_content:
        return
    
    # 提取数据
    weekly_data = extract_weekly_data(weekly_content)
    context_data = extract_context_data(context_content)
    
    # 验证同步
    results = validate_sync(weekly_data, context_data)
    
    # 输出结果
    print("\n=== 验证结果 ===")
    for result in results:
        print(result)
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
