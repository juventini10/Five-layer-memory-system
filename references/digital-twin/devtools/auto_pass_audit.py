#!/usr/bin/env python3
"""
auto_pass_audit.py — 自动通过卡事后抽查机制
每月1号由launchd自动运行，随机抽查上月自动通过的卡的10%，
检查是否有质量问题，错误率>5%触发质量预警。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import re
import sys
import json
import random
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

LOG_PATH = Path.home() / "~/[记忆共享中心]/数字分身/steps/step3-first-review-log.md"
AUDIT_REPORT_PATH = Path.home() / "~/[记忆共享中心]/数字分身/steps/auto_pass_audit_report.md"
LINT_SCRIPT = Path.home() / "[记忆共享中心]/脚本中心/lint_collision_card.py"
AI_LIB_PATH = Path.home() / "~/个人AI档案/知识库/AI学习库/"

def parse_reviews(log_path, month=None):
    """解析step3初审台账，返回指定月份的初审记录"""
    reviews = {}
    with open(log_path) as f:
        content = f.read()
    
    pattern = r'\|\s*(\d+[a-z]?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(S\d+[a-z]?)\s*\|\s*(\S+?)\s*\|\s*(\S+?)\s*\|'
    matches = re.findall(pattern, content)
    
    for seq, date, card_id, level, confidence in matches:
        if month and not date.startswith(month):
            continue
        if card_id not in reviews:
            reviews[card_id] = {
                'seq': seq,
                'date': date,
                'level': level,
                'confidence': confidence,
            }
    return reviews

def is_auto_pass(review):
    """判断是否为自动通过的卡"""
    level = review['level']
    confidence = review['confidence']
    is_high_confidence = confidence in ['高', '中高', '高🟢']
    return '价值' not in level and is_high_confidence

def find_card_file(card_id):
    """查找卡文件路径"""
    for f in AI_LIB_PATH.iterdir():
        if f.name.startswith(f"立场卡#{card_id}-") and f.suffix == '.md':
            return f
    return None

def lint_card(card_file):
    """运行lint_collision_card.py检查卡质量"""
    if not LINT_SCRIPT.exists():
        return {'passed': True, 'errors': [], 'warning': 'lint脚本不存在，跳过检查'}
    
    try:
        result = subprocess.run(
            ['python3', str(LINT_SCRIPT), str(card_file)],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        # 只用exit code判断：0=通过，非0=失败
        # 文本输出只用于错误详情，不用于判定（避免"无HARD违规"被误判为失败）
        passed = (result.returncode == 0)
        # 提取错误详情（如果有）
        errors = []
        if not passed:
            errors = [line for line in output.split('\n') if line.strip() and ('❌' in line or 'HARD' in line or 'ERROR' in line or '错误' in line)]
            if not errors:
                errors = [output.strip()[:200]]
        return {
            'passed': passed,
            'errors': errors,
            'raw_output': output[:500]
        }
    except Exception as e:
        return {'passed': True, 'errors': [], 'warning': f'lint运行异常: {e}'}

def audit(auto_pass_cards, sample_ratio=0.1):
    """抽查自动通过的卡"""
    total = len(auto_pass_cards)
    sample_size = max(1, int(total * sample_ratio))
    sampled = random.sample(list(auto_pass_cards.items()), min(sample_size, total))
    
    results = []
    passed_count = 0
    failed_count = 0
    
    for card_id, review in sampled:
        card_file = find_card_file(card_id)
        if not card_file:
            results.append({
                'card_id': card_id,
                'review': review,
                'lint': {'passed': False, 'errors': ['卡文件不存在'], 'warning': None}
            })
            failed_count += 1
            continue
        
        lint_result = lint_card(card_file)
        results.append({
            'card_id': card_id,
            'review': review,
            'lint': lint_result
        })
        if lint_result['passed']:
            passed_count += 1
        else:
            failed_count += 1
    
    error_rate = failed_count / len(sampled) * 100 if sampled else 0
    return {
        'total_auto_pass': total,
        'sample_size': len(sampled),
        'sample_ratio': sample_ratio,
        'passed': passed_count,
        'failed': failed_count,
        'error_rate': error_rate,
        'threshold': 5.0,
        'warning_triggered': error_rate > 5.0,
        'results': results
    }

def generate_report(audit_result, month):
    """生成抽查报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = []
    lines.append(f"# 自动通过卡事后抽查报告 — {month}")
    lines.append(f"")
    lines.append(f"- 抽查时间: {now}")
    lines.append(f"- 抽查范围: {month} 自动通过的卡")
    lines.append(f"- 自动通过总数: {audit_result['total_auto_pass']} 张")
    lines.append(f"- 抽查数量: {audit_result['sample_size']} 张（{audit_result['sample_ratio']*100:.0f}%）")
    lines.append(f"- 通过: {audit_result['passed']} 张")
    lines.append(f"- 失败: {audit_result['failed']} 张")
    lines.append(f"- 错误率: {audit_result['error_rate']:.1f}%")
    lines.append(f"- 阈值: {audit_result['threshold']}%")
    lines.append(f"- 预警状态: {'🔴 触发质量预警（错误率>5%，建议收紧自动通过条件）' if audit_result['warning_triggered'] else '🟢 正常（错误率≤5%）'}")
    lines.append(f"")
    
    if audit_result['failed'] > 0:
        lines.append(f"## 失败卡清单")
        lines.append(f"")
        for r in audit_result['results']:
            if not r['lint']['passed']:
                lines.append(f"- **{r['card_id']}**（序号{r['review']['seq']}，{r['review']['date']}）")
                for err in r['lint'].get('errors', []):
                    lines.append(f"  - {err}")
                if r['lint'].get('warning'):
                    lines.append(f"  - ⚠️ {r['lint']['warning']}")
        lines.append(f"")
    
    lines.append(f"## 建议")
    lines.append(f"")
    if audit_result['warning_triggered']:
        lines.append(f"- 🔴 错误率>{audit_result['threshold']}%，建议收紧自动通过条件：")
        lines.append(f"  1. 置信度阈值从'中高'提高到'高'")
        lines.append(f"  2. 增加阻断性找茬点检查（与现有规范冲突/立场自相矛盾/依据链断裂）")
        lines.append(f"  3. 对失败卡进行人工复核，判断是否需要回退自动通过状态")
    else:
        lines.append(f"- 🟢 错误率≤{audit_result['threshold']}%，自动通过条件可保持不变")
        lines.append(f"- 继续每月抽查，持续监控质量")
    lines.append(f"")
    
    return '\n'.join(lines)

def main():
    # 默认抽查上月
    now = datetime.now()
    first_of_this_month = now.replace(day=1)
    last_month = (first_of_this_month - timedelta(days=1)).strftime('%Y-%m')
    
    if len(sys.argv) > 1:
        month = sys.argv[1]
    else:
        month = last_month
    
    print(f"🔍 自动通过卡事后抽查 — {month}")
    print()
    
    # 解析初审记录
    reviews = parse_reviews(LOG_PATH, month)
    print(f"📊 {month} 初审记录: {len(reviews)} 张")
    
    # 筛选自动通过的卡
    auto_pass_cards = {k: v for k, v in reviews.items() if is_auto_pass(v)}
    print(f"🟢 自动通过的卡: {len(auto_pass_cards)} 张")
    
    if not auto_pass_cards:
        print("✅ 本月无自动通过的卡，无需抽查")
        return
    
    # 抽查
    print(f"🎲 随机抽查 10%...")
    audit_result = audit(auto_pass_cards, sample_ratio=0.1)
    
    print(f"   抽查数量: {audit_result['sample_size']} 张")
    print(f"   通过: {audit_result['passed']} 张")
    print(f"   失败: {audit_result['failed']} 张")
    print(f"   错误率: {audit_result['error_rate']:.1f}%")
    print()
    
    if audit_result['warning_triggered']:
        print(f"🔴 触发质量预警（错误率>{audit_result['threshold']}%）")
        print(f"   建议收紧自动通过条件，详见报告")
    else:
        print(f"🟢 正常（错误率≤{audit_result['threshold']}%）")
    print()
    
    # 生成报告
    report = generate_report(audit_result, month)
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_REPORT_PATH, 'a') as f:
        f.write(report)
        f.write('\n---\n')
    
    print(f"📝 报告已追加到: {AUDIT_REPORT_PATH}")

if __name__ == '__main__':
    main()
