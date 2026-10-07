#!/usr/bin/env python3
"""运行时证据提取器（clock-loop C01·X级主体·2026-09-05）

从系统日志 + test_results 归档报告提取目标 skill 的运行时验证证据，
映射 EVIDENCE_LADDER 档位（present/wired/exercised）。
判据唯一源 = references/evidence-ladder-map.md（+ skill-arch-standard §2.2a 登记表）。

⛔不读运行时缓存 .phaseX_last_run.json（#24 实证会被反复覆盖·非不可变证据源）。
⛔提取器异常由消费方（skill_eval.py）捕获 → 降级 present（不因提取器 bug 虚高分数）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import glob
import json
import os
import re
import sys

DEFAULT_LOG_DIR = os.path.expanduser('[记忆共享中心]/工作日志/系统日志/')
DEFAULT_ARCHIVE_DIR = os.path.expanduser('[记忆共享中心]/评估知识库/test_results/')

# 完成态标记——证明"跑过且有结果"（bare 实跑/实测不算·须配完成态）
COMPLETED_RE = re.compile(
    r'全绿|全过|全\s?PASS|0\s?FAIL|EXIT\s?[= ]0|exit 0|验证通过|测试通过|实测通过|'
    r'全部命中|跑通|成功通过|已实测|已验证|✅')
# 未完成态——防"计划实跑"假阳性（保守排除）
UNFINISHED_RE = re.compile(r'计划|待|拟|尚未|未进行|未跑|将实[跑测]')
NUMBER_RE = re.compile(r'\d')
SEAL_SHA8_RE = re.compile(r'"report_sha8"\s*:\s*"([0-9a-f]{8})"')

GRADES = {'exercised': 94, 'wired': 84, 'present': 74}


def _is_exercised_line(line, skill):
    """行级判据（evidence-ladder-map §三）——strict：完成态+数字+skill关联+⛔未完成态。"""
    if skill and skill not in line:
        return False
    if not COMPLETED_RE.search(line):
        return False
    if UNFINISHED_RE.search(line):
        return False
    if not NUMBER_RE.search(line):
        return False
    return True


def _scan_logs(skill, log_dir):
    """系统日志扫描——返回 exercised 证据条目列表（每文件聚合）。"""
    entries = []
    if not log_dir or not os.path.isdir(log_dir):
        return entries
    for f in sorted(glob.glob(os.path.join(log_dir, '*.md'))):
        try:
            with open(f, encoding='utf-8', errors='replace') as fh:
                lines = fh.read().splitlines()
        except Exception:
            continue
        hits = [ln.strip() for ln in lines if _is_exercised_line(ln, skill)]
        if hits:
            entries.append({
                'source': 'systemlog',
                'path': os.path.basename(f),
                'type': 'exercised',
                'count': len(hits),
                'snippet': hits[0][:200],
            })
    return entries


def _verify_seal(archive_path):
    """封口块 sha8 重算验证——复用 finalize_report.py 同源剔离正则（⛔不另写=两处定义必漂移）。"""
    declared = None
    try:
        with open(archive_path, encoding='utf-8') as fh:
            txt = fh.read()
        m = SEAL_SHA8_RE.search(txt)
        if not m:
            return None, False
        declared = m.group(1)
        from finalize_report import report_sha8
        recomputed = report_sha8(archive_path)
        return declared, (declared == recomputed)
    except Exception:
        return declared, False


def _scan_archives(skill, archive_dir):
    """归档报告扫描——sealed+sha8验证通过才计 exercised；unsealed 仅统计不升档。"""
    entries, stats_unsealed = [], 0
    if not archive_dir or not os.path.isdir(archive_dir):
        return entries, stats_unsealed
    for f in sorted(glob.glob(os.path.join(archive_dir, '*.md'))):
        base = os.path.basename(f)
        if skill not in base:
            continue
        declared, ok = _verify_seal(f)
        if declared is None:
            stats_unsealed += 1
            continue
        try:
            with open(f, encoding='utf-8') as fh:
                lines = fh.read().splitlines()
        except Exception:
            continue
        hits = [ln.strip() for ln in lines if _is_exercised_line(ln, None)]
        entry = {
            'source': 'archive',
            'path': base,
            'type': 'exercised' if ok else 'seal-mismatch',
            'sealed': True,
            'sha8_ok': ok,
            'count': len(hits),
            'snippet': hits[0][:200] if hits else '',
        }
        entries.append(entry)
    return entries, stats_unsealed


def _wired_signal(skill, skill_dir, archive_dir):
    """机制接线信号——eval-set.md 存在 或 归档报告存在（但 0 条实跑）。"""
    if skill_dir:
        ev = os.path.join(skill_dir, 'references', 'eval-set.md')
        if os.path.isfile(ev):
            return True
    if archive_dir and os.path.isdir(archive_dir):
        for f in glob.glob(os.path.join(archive_dir, '*.md')):
            if skill in os.path.basename(f):
                return True
    return False


def extract_evidence(skill, skill_dir=None, log_dir=None, archive_dir=None):
    """提取运行时证据 → {'grade','ceiling','refs','stats','grade_note'}。"""
    log_dir = log_dir or DEFAULT_LOG_DIR
    archive_dir = archive_dir or DEFAULT_ARCHIVE_DIR
    log_entries = _scan_logs(skill, log_dir)
    arch_entries, n_unsealed = _scan_archives(skill, archive_dir)

    exercised = [e for e in log_entries]
    exercised += [e for e in arch_entries if e.get('type') == 'exercised']
    n_exercised = sum(e.get('count', 0) for e in exercised)

    if n_exercised >= 1:
        grade = 'exercised'
        note = (f'运行时证据注入（X级·C01）：系统日志/归档报告 {n_exercised} 条实跑记录'
                f'（完成态+具体数字+skill关联）→ exercised 档——档位解锁（证据消费）⛔非内容改进')
    elif _wired_signal(skill, skill_dir, archive_dir):
        grade = 'wired'
        note = ('机制已接线未跑（eval-set.md/归档报告存在）但 0 条运行时证据 → wired 档'
                '——⛔不升 exercised（无实跑记录）')
    else:
        grade = 'present'
        note = ('静态内容检查·四轴中仅达 presence/content——use/outcome 须运行时/跨期证据'
                '（本评估不含·0 条运行时证据）')

    refs = exercised + arch_entries
    return {
        'grade': grade,
        'ceiling': GRADES[grade],
        'refs': refs,
        'stats': {
            'log_files': len(glob.glob(os.path.join(log_dir or '', '*.md'))) if log_dir and os.path.isdir(log_dir) else 0,
            'log_hit_files': len({e['path'] for e in log_entries}),
            'exercised_lines': n_exercised,
            'archives_scanned': len(arch_entries) + n_unsealed,
            'archives_unsealed': n_unsealed,
        },
        'grade_note': note,
        'grade_source': ('runtime-evidence' if grade == 'exercised'
                         else ('mechanism-wired' if grade == 'wired' else 'static-only')),
    }


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print('用法: python3 evidence_extractor.py --skill <名> [--dump] [--log-dir D] [--archive-dir D]')
        return 0
    args = sys.argv[1:]
    skill = None
    dump = False
    log_dir = archive_dir = None
    for i, a in enumerate(args):
        if a == '--skill' and i + 1 < len(args):
            skill = args[i + 1]
        elif a == '--dump':
            dump = True
        elif a == '--log-dir' and i + 1 < len(args):
            log_dir = args[i + 1]
        elif a == '--archive-dir' and i + 1 < len(args):
            archive_dir = args[i + 1]
    if not skill:
        print('⛔缺少 --skill 参数', file=sys.stderr)
        return 2
    ev = extract_evidence(skill, log_dir=log_dir, archive_dir=archive_dir)
    out = {'skill': skill, **ev}
    if dump:
        for r in ev['refs']:
            print(f"[{r['source']}|{r.get('type','')}|sealed={r.get('sealed','-')}|sha8_ok={r.get('sha8_ok','-')}]"
                  f" {r['path']} ×{r['count']} :: {r['snippet']}")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
