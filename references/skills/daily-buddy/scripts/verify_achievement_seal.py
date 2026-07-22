#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成就封口独立验证脚本（不在 AI 复盘主调用链上，可独立校验）
- 读取日记 review_sealed_sig 字段
- 基于当日真实成就数据重新计算签名
- 比对一致 → exit 0；不一致/缺失 → exit 1
- 用法：python3 verify_achievement_seal.py [--date YYYY-MM-DD]
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
import re
import json
import hashlib
from datetime import date, datetime
from pathlib import Path
import sys

# ─── 路径配置 ────────────────────────────────────────────────
DIARY_DIR = Path.home() / "Local_Obsidian_Vault/1-每日计划/01-日记"
ACHIEVEMENT_DIR = Path.home() / "个人AI档案/成就系统"
DATA_FILE = ACHIEVEMENT_DIR / "scripts" / "achievement_data.json"
SEAL_SALT = "daily-buddy-seal-v1"

# 6 项成就指标（与 update_diary_achievement.py 一致）
SEAL_FIELDS = ["diary_total", "tomato_total", "total_late_nights",
               "sleep_early_total", "wake_early_total", "reading_total"]


def extract_seal_from_diary(diary_file):
    """从日记 YAML frontmatter 提取 review_sealed_sig 字段"""
    if not diary_file or not diary_file.exists():
        return None, "日记文件不存在"
    with open(diary_file, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return None, "日记无 YAML frontmatter"
    yaml_block = m.group(1)
    match = re.search(r"review_sealed_sig:\s*(.+)", yaml_block)
    if not match:
        return None, "review_sealed_sig 字段缺失（未封口）"
    raw = match.group(1).strip()
    parts = raw.split(":")
    if len(parts) < 2:
        return None, f"签名格式异常: {raw}"
    return raw, None


def compute_seal(date_str, data):
    seed = date_str + "|" + "|".join(
        str(data.get(f, 0) or 0) for f in SEAL_FIELDS
    ) + "|" + SEAL_SALT
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def find_diary_file(target_date):
    year_month = target_date.strftime("%Y-%m")
    file_name = target_date.strftime("%Y-%m-%d.md")
    diary_file = DIARY_DIR / year_month / file_name
    if diary_file.exists():
        return diary_file
    diary_file = DIARY_DIR / file_name
    return diary_file if diary_file.exists() else None


def load_achievement_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    target_date = date.today()
    if "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            try:
                target_date = datetime.strptime(sys.argv[idx + 1], "%Y-%m-%d").date()
            except ValueError:
                print("VERIFY:ERR 日期格式不正确，应为 YYYY-MM-DD")
                return 1

    date_str = target_date.strftime("%Y-%m-%d")

    # 1. 找日记文件
    diary_file = find_diary_file(target_date)
    if not diary_file:
        print(f"VERIFY:NOENTRY {date_str} 日记不存在，无法校验")
        return 1

    # 2. 读封口签名
    seal_raw, err = extract_seal_from_diary(diary_file)
    if seal_raw is None:
        print(f"VERIFY:MISSING {date_str} {err}")
        return 1

    # 3. 读成就数据
    data = load_achievement_data()
    if data is None:
        print(f"VERIFY:ERR {date_str} 成就数据缺失 (achievement_data.json 不存在)")
        return 1

    # 检查 last_updated 是否当天
    last_updated = data.get("last_updated", "")
    if not last_updated.startswith(date_str):
        print(f"VERIFY:STALE {date_str} 成就数据最后更新于 {last_updated}，非今日，可能成就检测未跑")
        return 1

    # 4. 重新计算签名
    expected = f"{date_str}:{compute_seal(date_str, data)}"

    # 5. 比对
    if seal_raw == expected:
        print(f"VERIFY:PASS {date_str} 成就封口验证通过✅")
        return 0
    else:
        print(f"VERIFY:FAIL {date_str}")
        print(f"  日记存值: {seal_raw}")
        print(f"  重新计算: {expected}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
