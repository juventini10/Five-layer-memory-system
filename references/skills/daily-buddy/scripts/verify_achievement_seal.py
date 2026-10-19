#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  退出码：7=环境自检失败（沙箱假python·审查P2-3补）
成就封口独立验证脚本（不在 AI 复盘主调用链上，可独立校验）
- 读取日记 review_sealed_sig 字段
- 基于当日真实成就数据重新计算签名
- 比对一致 → exit 0；不一致/缺失 → exit 1
- 用法：python3 verify_achievement_seal.py [--date YYYY-MM-DD]
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
import json
import hashlib
from datetime import date, datetime
from pathlib import Path
import sys

# ─── 环境自愈（第一性原理根治·Hermes 沙箱 HOME 劫持）───
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv
DIARY_DIR = dbenv.DIARY_DIR
ACHIEVEMENT_DIR = dbenv.ACHIEVEMENT_DIR
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


# ── md 展示行格式断言+幂等自愈（2026-10-13 digit-blob 根治 · S1087 隐形契约 · triwich seal dfb5bf470868f380）──
# 契约：成就 md「最后更新」行只许 `**最后更新：YYYY-MM-DD HH:MM**`；写者(agent会话直编)不可枚举，读侧有牙挡一切。
import re as _re_fmt
_MD_LINE_OK = _re_fmt.compile(r'^\*{1,2}最后更新[:：]\d{4}-\d{2}-\d{2} \d{2}:\d{2}\*{1,2}$')
_MD_HEAL = _re_fmt.compile(r'^(\*{1,2}最后更新[:：]\d{4}-\d{2}-\d{2} \d{2}:\d{2})\d+\*{1,2}$')

def check_and_heal_md_lines(dry_run=False):
    """扫描 *成就.md 时间行：干净跳过(幂等)；时间后粘连数字尾缀→截掉自愈+ALERT留痕；救不了→UNRECOVERABLE。返回不可救数。"""
    fixed, bad = [], []
    try:
        names = sorted(os.listdir(ACHIEVEMENT_DIR)) if os.path.isdir(ACHIEVEMENT_DIR) else []
    except OSError:
        return 0
    for fn in names:
        if not fn.endswith("成就.md"):
            continue
        path = os.path.join(str(ACHIEVEMENT_DIR), fn)
        try:
            lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
        except OSError:
            continue
        changed = False
        for i, ln in enumerate(lines):
            if "最后更新：" not in ln or "{" in ln:
                continue  # 含{}=未填模板(合法未更新态·非脏)·不误伤
            s = ln.rstrip("\n")
            if _MD_LINE_OK.match(s):
                continue
            m = _MD_HEAL.match(s)
            if m:
                nl = m.group(1) + "**\n"
                lines[i] = nl
                changed = True
                fixed.append(fn)
            else:
                bad.append(fn)
        if changed and not dry_run:
            open(path, "w", encoding="utf-8").writelines(lines)
    if fixed:
        print(f"ALERT:FORMAT {len(fixed)}个成就md时间行曾带数字尾缀已自愈: {','.join(sorted(set(fixed)))}")
    for b in sorted(set(bad)):
        print(f"ALERT:FORMAT-UNRECOVERABLE {b} 时间行格式不可解析，需人工")
    return len(set(bad))

def _self_test():
    """双向夹具：脏行→自愈成正确形(正例)；干净行→一字不动(负例防误伤)。"""
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="seal_fmt_")
    globals()["ACHIEVEMENT_DIR"] = tmp
    try:
        dirty = tmp + "/测试成就.md"
        clean = tmp + "/干净成就.md"
        open(dirty, "w", encoding="utf-8").write("**最后更新：2026-10-12 23:2524202040403535595841414102024227**\n")
        orig_clean = "**最后更新：2026-10-12 23:25**\n"
        open(clean, "w", encoding="utf-8").write(orig_clean)
        open(tmp + "/单星成就.md", "w", encoding="utf-8").write("*最后更新：2026-10-12 23:25*\n")
        open(tmp + "/模板成就.md", "w", encoding="utf-8").write("**最后更新：{YYYY-MM-DD}**\n")
        unrecoverable = check_and_heal_md_lines()
        pos = open(dirty, encoding="utf-8").read() == orig_clean and unrecoverable == 0
        neg = open(clean, encoding="utf-8").read() == orig_clean and open(tmp + "/单星成就.md", encoding="utf-8").read() == "*最后更新：2026-10-12 23:25*\n" and open(tmp + "/模板成就.md", encoding="utf-8").read() == "**最后更新：{YYYY-MM-DD}**\n"
        print(f"[夹具·正例] 脏行自愈成正确形: {'✅' if pos else '❌'}  [夹具·负例] 干净行一字不动: {'✅' if neg else '❌'}")
        return 0 if pos and neg else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if not dbenv.self_check(verbose=True):
        sys.exit(9)
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
    check_and_heal_md_lines()  # md展示行契约自愈(2026-10-13 digit-blob根治·先于一切return路径执行)

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
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    sys.exit(main())
