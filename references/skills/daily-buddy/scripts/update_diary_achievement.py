#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动更新日记成就模块脚本
- 运行成就检测（可选，失败不阻塞）
- 读取最新成就数据
- 精准替换当天日记「本日新增达成」行（有/无由 achievement_tracker stdout 判定，不动其它内容）
- 支持指定日期的日记更新

用法：
  python3 update_diary_achievement.py              # 更新今天的日记
  python3 update_diary_achievement.py --date YYYY-MM-DD  # 更新指定日期的日记
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

# ─── 环境自愈（第一性原理根治·Hermes 沙箱 HOME 劫持 + 假 python 空跑）───
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv
# 路径全部改用 dbenv 解析（破除沙箱 HOME 指向 /tmp/hb_sb/home 的污染）
DIARY_DIR = dbenv.DIARY_DIR
ACHIEVEMENT_DIR = dbenv.ACHIEVEMENT_DIR
DATA_FILE = ACHIEVEMENT_DIR / "scripts" / "achievement_data.json"
# 优先用隔离 venv（已装 pyyaml），失败回退真实 python3（绝不裸 "python3"→沙箱假二进制）
VENV_PYTHON = dbenv.REAL_PYTHON

# ─── 成就模块更新：只写「本日新增达成」行（对齐 diary-template.md 有才显示铁律）───
# 6行"距目标差"累计进度已删除——YAML是检索索引非内容副本（双本账教训）；进度真相源在成就系统
UNLOCKED_MARK = "解锁了"          # achievement_tracker --all stdout 有新成就标记
NO_UNLOCKED_MARK = "暂无新成就解锁"
ACHIEVEMENT_LINE_RE = re.compile(r"(- 本日新增达成：).*")


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


def update_diary_achievement(diary_file, achievement_names):
    """更新日记成就模块「本日新增达成」行（成就名从 achievement_tracker stdout 解析·全自动）"""
    if not diary_file.exists():
        print(f"❌ 日记文件不存在：{diary_file}")
        return False

    with open(diary_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查是否有成就模块
    if "<!-- SECTION: ACHIEVEMENTS -->" not in content:
        print(f"❌ 日记中没有找到成就模块：{diary_file}")
        return False

    m = ACHIEVEMENT_LINE_RE.search(content)
    if not m:
        print(f"❌ 未匹配到「本日新增达成」行（模板结构可能已变）：{diary_file}")
        return False

    if achievement_names:
        text = " / ".join(achievement_names)
    else:
        text = "今日无新成就解锁"
    # v3.29.1 修复：用 group0 整行替换（旧逻辑只替换前缀、残留骨架说明后缀如"___（有成就达成→…）"）
    new_content = content[:m.start()] + f"- 本日新增达成：{text}" + content[m.end():]

    with open(diary_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"✅ 已更新日记成就模块（本日新增达成）：{diary_file}")
    return True


def run_achievement_check():
    """运行成就检测刷新数据；失败不阻塞主流程。返回 (成功与否, stdout文本)"""
    import subprocess
    script_path = Path(__file__).parent / "achievement_tracker.py"
    # 🔒 防漂移校验：achievement_tracker.py 必须是指向成就系统真源的软链
    # 单源架构：真源 = [记忆共享中心]/成就系统/scripts/achievement_tracker.py，daily-buddy 侧仅软链
    # 若被编辑器物化成实体副本 / 改指别处 → 立即报错退出，杜绝静默漂移（2026-08-02 修复）
    _REAL_SRC = (Path.home() / "[记忆共享中心]/成就系统/scripts/achievement_tracker.py").resolve()
    if not script_path.is_symlink():
        raise SystemExit(
            f"❌ 漂移告警：{script_path} 已物化为实体副本（非软链）。\n"
            f"   修复：rm {script_path} && ln -s {_REAL_SRC} {script_path}"
        )
    if script_path.resolve() != _REAL_SRC:
        raise SystemExit(
            f"❌ 漂移告警：软链指向 {script_path.resolve()} 而非真源 {_REAL_SRC}。\n"
            f"   修复：rm {script_path} && ln -s {_REAL_SRC} {script_path}"
        )
    py = VENV_PYTHON if os.path.exists(VENV_PYTHON) else dbenv.REAL_PYTHON
    try:
        # 用真实 python3 + --json 结构化输出（dbenv.run_real 杜绝沙箱假 binary 空跑）
        result = dbenv.run_real(
            [str(script_path), "--all", "--json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout.strip():
            print("成就检测原始输出：")
            # JSON 行以外的普通 print 也透出（tracker 在非 --json 时纯文本，--json 时末行 JSON）
            print(result.stdout)
        if result.stderr.strip():
            print("⚠️ 成就检测 stderr：")
            print(result.stderr)
        # 解析结构化成就名（第一性原理：真相源=结构化数据，非脆弱正则刮文本）
        names = _parse_achievement_names(result.stdout)
        return result.returncode == 0, result.stdout or "", names
    except Exception as e:
        print(f"⚠️ 成就检测未执行（不影响日记更新）：{e}")
        return False, "", []


def _parse_achievement_names(stdout_text):
    """从 tracker --json 输出解析当日新解锁成就名列表。

    tracker 返回 newly_unlocked 元素结构：
      - 元组 (ach_dict, value) 经 JSON 序列化后变为 [ach_dict, value]
      - 故 item 为 list：item[0] 是含 "name" 的 dict
    """
    names = []
    for line in stdout_text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "newly_unlocked" in obj:
            for item in obj["newly_unlocked"]:
                name = None
                if isinstance(item, dict):
                    name = item.get("name")
                elif isinstance(item, (list, tuple)) and item:
                    first = item[0]
                    if isinstance(first, dict):
                        name = first.get("name")
                    elif isinstance(first, str):
                        name = first
                if name:
                    names.append(name)
    return names


def _scan_day_evidence(target_date: date):
    """第一性原理根治·按日期归属成就（幂等·不依赖 tracker 瞬态）。

    真相源 = 成就证据目录中 `{达成日期}-{成就ID}.md` 文件：
      - 文件名前缀 `{日期}-` 即持久归因（写入时由 tracker 用真实达成日命名）
      - 正文标题 `# 成就证据 · {成就名}` 即权威成就名
    扫描当日前缀文件 → 提取成就名 → 无论 tracker 是否已入账，重跑均稳定一致。
    """
    if not dbenv.EVIDENCE_DIR.exists():
        return []
    prefix = target_date.isoformat() + "-"
    names = []
    for f in sorted(dbenv.EVIDENCE_DIR.glob(prefix + "*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # 优先取标题 `# 成就证据 · 名`（最权威）
        m = re.search(r"^#\s*成就证据\s*[·・:：]?\s*(.+)$", text, re.MULTILINE)
        if m:
            name = m.group(1).strip()
            if name:
                names.append(name)
    return names


# ─── 封口签名 ──────────────────────────────────────────────
SEAL_SALT = "daily-buddy-seal-v1"


def compute_seal(date_str, achievement_data):
    """基于日期 + 6项成就数据计算确定性签名（非密码学安全，仅防跳过伪造）"""
    fields = ["diary_total", "tomato_total", "total_late_nights",
              "sleep_early_total", "wake_early_total", "reading_total"]
    seed = date_str + "|" + "|".join(
        str(achievement_data.get(f, 0) or 0) for f in fields
    ) + "|" + SEAL_SALT
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def add_review_seal(content, date_str, achievement_data):
    """在日记 YAML frontmatter 中添加/更新 review_sealed_sig 字段（唯一写者）"""
    signature = compute_seal(date_str, achievement_data)
    sig_line = f"review_sealed_sig: {date_str}:{signature}"

    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        new_yaml = f"---\n{sig_line}\n---\n\n"
        return new_yaml + content

    yaml_block = m.group(1)
    if "review_sealed_sig:" in yaml_block:
        yaml_block = re.sub(r"review_sealed_sig:.*", sig_line, yaml_block)
    else:
        yaml_block = yaml_block.rstrip() + "\n" + sig_line

    return content[:m.start(1)] + yaml_block + content[m.end(1):]


# ─── 主流程 ────────────────────────────────────────────────
def main():
    # ─── 环境自检（第一性原理根治·沙箱假 python 拒绝空跑）───
    if not dbenv.self_check(verbose=True):
        sys.exit(9)
    target_date = date.today()
    skip_seal = "--no-seal" in sys.argv
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
    _, check_stdout, tracker_names = run_achievement_check()  # 失败不阻塞

    # 第一性原理根治·成就名以「证据目录按日期归属」为准（幂等·不依赖 tracker 瞬态）
    # tracker JSON 仅作兜底（证据目录缺失时）
    evidence_names = _scan_day_evidence(target_date)
    if evidence_names:
        achievement_names = evidence_names
        print(f"📌 当日成就（证据目录归因·{len(achievement_names)}项）：{achievement_names}")
    else:
        achievement_names = tracker_names
        if achievement_names:
            print(f"⚠️ 证据目录无 {target_date} 记录，回退 tracker 瞬态判定：{achievement_names}")

    print("📊 读取成就数据...")
    achievement_data = load_achievement_data()

    diary_file = find_diary_file(target_date)
    if not diary_file:
        print(f"❌ 未找到 {target_date} 的日记文件")
        return 1

    print("📝 更新日记成就模块...")
    if update_diary_achievement(diary_file, achievement_names):
        # 封口签名（单写者·接触法防误：成就块只能由脚本产生合法签名）
        if not skip_seal:
            date_str = target_date.strftime("%Y-%m-%d")
            with open(diary_file, "r", encoding="utf-8") as f:
                content = f.read()
            sealed_content = add_review_seal(content, date_str, achievement_data)
            with open(diary_file, "w", encoding="utf-8") as f:
                f.write(sealed_content)
            sig = compute_seal(date_str, achievement_data)
            print(f"🔒 已封口：review_sealed_sig: {date_str}:{sig}")
        else:
            print("⏭️ 跳过封口（--no-seal）")
        print("✅ 任务完成！")
        return 0
    else:
        print("❌ 任务失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
