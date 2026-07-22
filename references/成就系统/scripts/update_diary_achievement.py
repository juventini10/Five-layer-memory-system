#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新日记成就模块脚本
- 运行成就检测（可选，失败不阻塞）
- 读取最新成就数据
- 精准替换当天日记「成就进度备忘」6行固定格式（不动其它内容）
- 支持指定日期的日记更新

用法：
  python3 update_diary_achievement.py              # 更新今天的日记
  python3 update_diary_achievement.py --date YYYY-MM-DD  # 更新指定日期的日记
"""

import os
import re
import json
from datetime import date, datetime
from pathlib import Path
import sys

# ─── 路径配置 ────────────────────────────────────────────────
DIARY_DIR = Path.home() / "Local_Obsidian_Vault/1-每日计划/01-日记"
ACHIEVEMENT_DIR = Path.home() / "个人AI档案/成就系统"
DATA_FILE = ACHIEVEMENT_DIR / "scripts" / "achievement_data.json"
# 优先用隔离 venv（已装 pyyaml），失败回退 bare python3
VENV_PYTHON = "~/.workbuddy/binaries/python/envs/default/bin/python"

# ─── 6行成就进度备忘配置（与 diary-template.md 严格对齐）──────
# (emoji, 行内标签, 成就名, 目标值, json字段, 单位)
ACHIEVEMENT_METRICS = [
    ("🍅", "累计", "番茄传奇", 700, "tomato_total", "🍅"),
    ("📝", "日记", "百篇文人", 100, "diary_total", "篇"),
    ("📚", "阅读", "十本学者", 10, "reading_total", "本"),
    ("😴", "早睡", "两个月睡神", 60, "sleep_early_total", "天"),
    ("🌅", "早起", "两个月日出猎人", 60, "wake_early_total", "天"),
    ("🦉", "累计熬夜", "死神契约", 40, "total_late_nights", "天"),
]

# 精准替换正则：抓「成就进度备忘」标题行 + 其后 6 个 bullet 行，
# 锚定其后紧跟的刚性规则块，避免误吞日记其它内容。
BULLET_BLOCK_RE = re.compile(
    r"(- 成就进度备忘（6行固定格式[^\n]*\n)"   # group1: 标题行（含“成就进度备忘（6行固定格式”）
    r"(?:[ \t]*- .*\n){6}"                     # 其后正好 6 个 bullet 行
    r"(?=\n+> 💡 \*\*刚性规则\*\*)",            # 锚定刚性规则块，防止越界
    re.DOTALL,
)


# ─── 工具函数 ────────────────────────────────────────────────
def load_achievement_data():
    """读取成就数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "tomato_total": 0,
        "reading_total": 0,
        "diary_total": 0,
        "sleep_early_total": 0,
        "wake_early_total": 0,
        "total_late_nights": 0,
        "unlocked": [],
        "last_updated": "",
    }


def build_six_lines(data):
    """按模板格式生成 6 行成就进度备忘文本（不含缩进的 2 空格前缀）"""
    lines = []
    for emoji, label, name, target, field, unit in ACHIEVEMENT_METRICS:
        value = data.get(field, 0) or 0
        if value >= target:
            diff = value - target
            tail = f" 已达成(+{fmt_num(diff)}{unit})"
        else:
            tail = f"差{target - value}{unit}"
        lines.append(f"{emoji} {label} {fmt_num(value)}{unit}，距{name}({target}{unit}){tail}")
    return lines


def fmt_num(v):
    """整数不显示小数，浮点保留原样（如 1292.5）"""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def find_diary_file(target_date):
    """找到指定日期的日记文件"""
    year_month = target_date.strftime("%Y-%m")
    file_name = target_date.strftime("%Y-%m-%d.md")
    diary_file = DIARY_DIR / year_month / file_name
    if diary_file.exists():
        return diary_file
    diary_file = DIARY_DIR / file_name
    if diary_file.exists():
        return diary_file
    return None


def update_diary_achievement(diary_file, achievement_data):
    """精准替换日记的「成就进度备忘」6行块，保留模板其余结构"""
    if not diary_file.exists():
        print(f"❌ 日记文件不存在：{diary_file}")
        return False

    with open(diary_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查是否有成就模块
    if "<!-- SECTION: ACHIEVEMENTS -->" not in content:
        print(f"❌ 日记中没有找到成就模块：{diary_file}")
        return False

    m = BULLET_BLOCK_RE.search(content)
    if not m:
        print(f"❌ 未匹配到「成就进度备忘」6行块（模板结构可能已变）：{diary_file}")
        return False

    header = m.group(1)  # 标题行（含“成就进度备忘（6行固定格式...）”）
    six_lines = build_six_lines(achievement_data)
    new_block = header + "".join(f"  - {line}\n" for line in six_lines)

    new_content = content[:m.start()] + new_block + content[m.end():]

    with open(diary_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ 已更新日记成就模块（6行）：{diary_file}")
    return True


def run_achievement_check():
    """运行成就检测刷新数据；失败不阻塞主流程"""
    import subprocess
    script_path = ACHIEVEMENT_DIR / "scripts" / "achievement_tracker.py"
    py = VENV_PYTHON if os.path.exists(VENV_PYTHON) else "python3"
    try:
        result = subprocess.run(
            [py, str(script_path), "--all"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout.strip():
            print("成就检测结果：")
            print(result.stdout)
        if result.stderr.strip():
            print("⚠️ 成就检测 stderr：")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"⚠️ 成就检测未执行（不影响日记更新）：{e}")
        return False


# ─── 主流程 ────────────────────────────────────────────────
def main():
    target_date = date.today()
    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            try:
                target_date = datetime.strptime(sys.argv[idx + 1], "%Y-%m-%d").date()
            except ValueError:
                print("错误：日期格式不正确，应为 YYYY-MM-DD")
                return 1

    print(f"📅 处理日期：{target_date}")

    print("🔍 运行成就检测（刷新数据）...")
    run_achievement_check()  # 失败不阻塞

    print("📊 读取成就数据...")
    achievement_data = load_achievement_data()

    diary_file = find_diary_file(target_date)
    if not diary_file:
        print(f"❌ 未找到 {target_date} 的日记文件")
        return 1

    print("📝 更新日记成就模块...")
    if update_diary_achievement(diary_file, achievement_data):
        print("✅ 任务完成！")
        return 0
    else:
        print("❌ 任务失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
