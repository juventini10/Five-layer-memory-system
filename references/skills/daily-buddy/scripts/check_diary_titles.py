#!/usr/bin/env python3
"""
日记标题格式检查脚本
验证所有日记是否符合规则：# YYYY-MM-DD(周X) 每日计划
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

import os
import re
from datetime import datetime

def _resolve_diary_root():
    """日记根解析（SSOT 优先·零 Obsidian 假设）：
    runtime_paths.diary_root（安装器写入）→ OBSIDIAN_VAULT 环境变量 → 占位默认。"""
    import json as _json
    _cands = []
    if os.environ.get("BULUOTUO_RUNTIME_PATHS"):
        _cands.append(os.path.expanduser(os.environ["BULUOTUO_RUNTIME_PATHS"]))
    elif os.environ.get("DOENGLINGZ_CONFIG_DIR"):
        _cfg = os.path.expanduser(os.environ["DOENGLINGZ_CONFIG_DIR"])
        if os.path.isfile(os.path.join(_cfg, "doenglingz", "runtime_paths.json")):
            _cands.append(os.path.join(_cfg, "doenglingz", "runtime_paths.json"))
        elif os.path.isfile(os.path.join(_cfg, "runtime_paths.json")):
            _cands.append(os.path.join(_cfg, "runtime_paths.json"))
    if not _cands:
        for _root in (os.path.expanduser("~/.workbuddy"), os.path.expanduser("~/.hermes")):
            _c = os.path.join(_root, "doenglingz", "runtime_paths.json")
            if os.path.isfile(_c):
                _cands.append(_c)
                break
    for _f in _cands:
        try:
            with open(_f, encoding="utf-8") as _fh:
                _r = _json.load(_fh).get("diary_root")
            if _r and os.path.isdir(os.path.expanduser(_r)):
                return os.path.expanduser(_r)
        except Exception:
            pass
    _ov = os.environ.get("OBSIDIAN_VAULT")
    if _ov:
        return os.path.join(os.path.expanduser(_ov), "1-每日计划", "01-日记")
    return os.path.expanduser("~/[日记仓库]/1-每日计划/01-日记/")

def check_diary_titles():
    diary_dir = _resolve_diary_root()
    
    weekday_map = {
        0: "周一", 1: "周二", 2: "周三", 3: "周四",
        4: "周五", 5: "周六", 6: "周日"
    }
    
    errors = []
    success = []
    
    for root, dirs, files in os.walk(diary_dir):
        # 跳过隐藏目录（如 .reminders/——非日记文件，2026-08-10 复审修复）
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in sorted(files):
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(root, filename)

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取日期——锚定 frontmatter 行首（防误命中 review_date 等非 date 字段，2026-08-10 复审修复）
            match = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
            if not match:
                errors.append(f"❌ {filename}: 无法提取日期（frontmatter 缺 date 字段）")
                continue

            date_str = match.group(1)

            # 计算正确的星期
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                correct_weekday = weekday_map[date_obj.weekday()]
            except Exception:
                errors.append(f"❌ {filename}: 日期格式错误")
                continue

            # 检查标题——兼容 H1/H2 两种层级（模板/骨架为 H2，历史数据为 H1，2026-08-10 复审修复）
            correct_title_h1 = f"# {date_str}({correct_weekday}) 每日计划"
            correct_title_h2 = f"## {date_str}({correct_weekday}) 每日计划"

            if correct_title_h1 in content or correct_title_h2 in content:
                success.append(f"✅ {filename}: {correct_title_h2}")
            else:
                # 查找实际标题（H1/H2 均可）
                title_match = re.search(r'^#{1,2} \d{4}-\d{2}-\d{2}.*', content, re.MULTILINE)
                if title_match:
                    actual_title = title_match.group(0)
                    errors.append(f"❌ {filename}: 标题错误\n   期望: {correct_title_h2}\n   实际: {actual_title}")
                else:
                    errors.append(f"❌ {filename}: 缺少标题")
    
    # 输出结果
    print("=" * 60)
    print("📋 日记标题格式检查结果")
    print("=" * 60)
    
    if success:
        print(f"\n✅ 通过检查 ({len(success)} 个):")
        for s in success:
            print(f"  {s}")
    
    if errors:
        print(f"\n❌ 检查失败 ({len(errors)} 个):")
        for e in errors:
            print(f"  {e}")
    
    print("\n" + "=" * 60)
    if not errors:
        print("🎉 全部日记格式正确！")
    else:
        print(f"⚠️ 发现 {len(errors)} 个错误，需要修复")
    print("=" * 60)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = check_diary_titles()
    exit(0 if success else 1)
