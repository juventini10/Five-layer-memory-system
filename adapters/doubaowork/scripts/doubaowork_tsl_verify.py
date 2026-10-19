#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
doubaowork_tsl_verify.py — 豆包办公端童灵TSL（会话级L7验证清单）机械校验器

设计哲学（来源：数字分身设计哲学/08-会话级L7验证清单.md §十）：
  根治＝把构造权从AI手里拿走交给脚本。AI只许逐行relay本脚本stdout，
  改一行层状态＝违规（tsl_closeout_guard可查——豆包端无Stop钩子，
  靠stamp+stamps.log事后验真）。

平台边界（诚实标注，不假装完整）：
  豆包办公无Stop钩子、无UserPromptSubmit钩子、无标准会话日志访问。
  L3上岗仪式/L4本轮Read切片/L5守护三查执行 属于"AI侧会话内行为"，
  脚本无法机械验证本轮是否执行——如实标⚪查不了（平台边界型），
  不接受AI自填✅。脚本只校验"基础设施在位性"和"产出物存在性/新鲜度"。

用法：
  python3 doubaowork_tsl_verify.py [--window MINUTES] [--full]
  --window N  本会话窗口分钟数（默认30），用于L7产出物新鲜度判定
  --full      输出完整版（含明细），默认展开版树状

输出：标准化TSL树 + 🔏stamp + stamps.log签发账本
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path

__version__ = "v0.1.0"
SCRIPT_NAME = "doubaowork_tsl_verify"

# ── 路径配置（记忆中心根由 BULUOTU_MC 声明·⛔内置默认值=条文47违例）──
HOME = os.path.expanduser("~")
# B修源·条文47(2026-10-06·死承诺根治：注释称setup.sh替换·实setup.sh无此锚=默认值从未被换)
MC_BASE = os.environ.get("BULUOTU_MC", "")
if not MC_BASE:
    print("❌ tsl_verify: 读不到记忆中心根·请 BULUOTU_MC=<你的记忆中心路径> 前缀运行（⛔档案根默认值已删·无声明不空转）", file=sys.stderr)
    sys.exit(1)
USER_MD = os.path.join(HOME, ".doubaowork-config", "USER.md")
SLICES_DIR = os.path.join(MC_BASE, "数字分身", "K2切片蒸馏", "slices")
GROWTH_BOX = os.path.join(MC_BASE, "成长箱")
AI_LIB = os.path.join(HOME, "[日记仓库]", "2-知识库", "09-AI学习库")  # 2026-10-13 C''波次2迁移后路径同步·立场卡已迁入vault
SYSLOG_DIR = os.path.join(MC_BASE, "工作日志", "系统日志")
STAMPS_LOG = os.path.join(HOME, ".cache", "tsl_verify", "stamps.log")

WINDOW_MIN = 30  # 默认本会话窗口30分钟


def ensure_stamps_dir():
    os.makedirs(os.path.dirname(STAMPS_LOG), exist_ok=True)


def file_exists(path):
    return os.path.isfile(path)


def dir_exists(path):
    return os.path.isdir(path)


def file_age_minutes(path):
    """返回文件距今分钟数，不存在返回None"""
    if not file_exists(path):
        return None
    return (time.time() - os.path.getmtime(path)) / 60


def dir_latest_mtime(directory, pattern="*.md"):
    """返回目录下最新文件的mtime时间戳，无文件返回None"""
    import glob
    files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
    if not files:
        return None
    return max(os.path.getmtime(f) for f in files)


def grep_in_file(path, pattern):
    """简单grep，返回是否命中"""
    if not file_exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return pattern in f.read()
    except Exception:
        return False


def check_launchd(label_substring):
    """检查launchd任务是否在位"""
    try:
        import subprocess
        result = subprocess.run(
            ["launchctl", "list"], capture_output=True, text=True, timeout=5
        )
        return label_substring in result.stdout
    except Exception:
        return False


def check_l0():
    """L0接入态：USER.md存在且包含童灵配置"""
    ok = file_exists(USER_MD) and grep_in_file(USER_MD, "童灵")
    detail = f"USER.md={'在位' if file_exists(USER_MD) else '缺失'}"
    return ("L0 接入态", "✅做到" if ok else "🔴没做", detail)


def check_l1():
    """L1身份感知：系统提示可见童灵身份——脚本无法验证AI侧系统提示，标⚪"""
    return ("L1 身份感知", "⚪查不了", "AI侧系统提示注入·脚本无访问（平台边界型）")


def check_l2():
    """L2规则加载：USER.md包含core_slice+L6+命名红线"""
    has_core = grep_in_file(USER_MD, "core_slice") or grep_in_file(USER_MD, "K2")
    has_l6 = grep_in_file(USER_MD, "L6")
    has_naming = grep_in_file(USER_MD, "Doenglingz") or grep_in_file(USER_MD, "童灵")
    ok = has_core and has_l6 and has_naming
    detail = f"core_slice={'✓' if has_core else '✗'} L6={'✓' if has_l6 else '✗'} 命名红线={'✓' if has_naming else '✗'}"
    return ("L2 规则加载", "✅做到" if ok else "🔴没做", detail)


def check_l3():
    """L3上岗仪式：本轮是否输出上岗仪式——脚本无法验证会话内行为，标⚪"""
    return ("L3 上岗仪式", "⚪查不了", "AI侧会话内行为·脚本无会话日志访问（平台边界型）")


def check_l4():
    """L4域切片：slices目录存在+文件在位；本轮是否Read——⚪"""
    slices_exist = dir_exists(SLICES_DIR)
    slice_files = ["L2_认知风格.md", "L3_行为规则.md", "L4_表达DNA.md", "L5_盲区与边界.md"]
    found = [f for f in slice_files if file_exists(os.path.join(SLICES_DIR, f))]
    ok = slices_exist and len(found) >= 2
    detail = f"切片在位{len(found)}/4·本轮Read⚪查不了"
    return ("L4 域切片", "✅做到" if ok else "🔴没做", detail)


def check_l5():
    """L5守护三查：切片新鲜度可查；8要素/试金石执行——⚪"""
    if not dir_exists(SLICES_DIR):
        return ("L5 守护三查", "🔴没做", "切片目录缺失")
    latest = dir_latest_mtime(SLICES_DIR)
    fresh = "新鲜" if latest and (time.time() - latest) / 60 < 1440 else "需更新"
    detail = f"切片{fresh}·8要素/试金石执行⚪查不了（平台边界型·软约束）"
    return ("L5 守护三查", "🟡软约束", detail)


def check_l6():
    """L6自愈同步：launchd watcher在位"""
    watcher = check_launchd("doenglingz")
    detail = f"launchd watcher={'在位' if watcher else '未检测到'}"
    return ("L6 自愈同步", "✅做到" if watcher else "🔴没做", detail)


def check_l7(window_min):
    """L7闭环五通道：检查本窗口内产出物存在性/新鲜度"""
    results = []
    now = time.time()

    # L7-1 错误→成长箱
    gb_latest = dir_latest_mtime(GROWTH_BOX, "*.md")
    gb_fresh = gb_latest and (now - gb_latest) / 60 < window_min
    results.append(("L7-1 错误→成长箱", "✅" if gb_fresh else "🔴没做",
                    f"本窗口{'有' if gb_fresh else '无'}新增（窗口{window_min}min）"))

    # L7-2 铁律反哺
    rule_log = os.path.join(GROWTH_BOX, "experience", "规范反哺日志.md")
    rl_age = file_age_minutes(rule_log)
    rl_fresh = rl_age is not None and rl_age < window_min
    results.append(("L7-2 铁律反哺", "✅" if rl_fresh else "🔴没做",
                    f"规范反哺日志{'本窗口有更新' if rl_fresh else '本窗口无更新'}"))

    # L7-3 立场卡反哺
    sc_latest = dir_latest_mtime(AI_LIB, "立场卡*.md")
    sc_fresh = sc_latest and (now - sc_latest) / 60 < window_min
    results.append(("L7-3 立场卡反哺", "✅" if sc_fresh else "🔴没做",
                    f"立场卡{'本窗口有新增' if sc_fresh else '本窗口无新增'}"))

    # L7-4 系统日志
    today = datetime.now().strftime("%Y-%m-%d")
    syslog_today = os.path.join(SYSLOG_DIR, f"系统日志_{today}.md")
    sl_age = file_age_minutes(syslog_today)
    sl_fresh = sl_age is not None and sl_age < window_min
    results.append(("L7-4 系统日志", "✅" if sl_fresh else "🔴没做",
                    f"今日日志{'本窗口有追加' if sl_fresh else '本窗口无追加'}"))

    # L7-5 反思沉淀
    reflection_found = False
    if file_exists(syslog_today):
        try:
            with open(syslog_today, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # 检查最近窗口内的[童灵思考]前缀
                reflection_found = "[童灵思考]" in content
        except Exception:
            pass
    results.append(("L7-5 反思沉淀", "✅" if reflection_found else "🔴没做",
                    "[童灵思考]前缀" + ("存在" if reflection_found else "不存在（今日日志）")))

    return results


def compute_stamp(tree_text):
    """计算TSL树的stamp（sha256前8位）"""
    return hashlib.sha256(tree_text.encode("utf-8")).hexdigest()[:8]


def append_stamp(stamp, window_min):
    """追加stamp到签发账本"""
    ensure_stamps_dir()
    with open(STAMPS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {SCRIPT_NAME} {__version__} | window={window_min}min | stamp={stamp}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="豆包办公端童灵TSL机械校验器")
    parser.add_argument("--window", type=int, default=WINDOW_MIN, help="本会话窗口分钟数")
    parser.add_argument("--full", action="store_true", help="输出完整版")
    args = parser.parse_args()

    window = args.window

    # 执行各层检查
    checks = []
    checks.append(check_l0())
    checks.append(check_l1())
    checks.append(check_l2())
    checks.append(check_l3())
    checks.append(check_l4())
    checks.append(check_l5())
    checks.append(check_l6())
    l7_results = check_l7(window)
    checks.extend(l7_results)

    # 计算评级（严格截断制：第一个🔴或⚪之后截断）
    # 但⚪是平台边界型，不截断；只看🔴
    level = 7
    layer_names = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
    for i, (name, status, detail) in enumerate(checks[:7]):
        if "🔴" in status:
            level = i - 1
            break
    # L7五通道全过才算L7
    l7_all_ok = all("✅" in r[1] for r in l7_results)
    if not l7_all_ok and level >= 7:
        level = 6

    # 构建输出树
    lines = []
    lines.append(f"🧾 TSL 机械核验 {__version__} · since={datetime.now().strftime('%Y-%m-%d %H:%M')} · window={window}min · 豆包办公端")
    lines.append("├─ 层 状态 判定依据（AI说的不算，账本/文件/mtime才算）")
    for name, status, detail in checks:
        lines.append(f"├─ {name} {status} {detail}")

    red_count = sum(1 for _, s, _ in checks if "🔴" in s)
    white_count = sum(1 for _, s, _ in checks if "⚪" in s)
    yellow_count = sum(1 for _, s, _ in checks if "🟡" in s)
    lines.append(f"└─ 结论：🔴没做{red_count}件 · ⚪查不了{white_count}件（平台边界型） · 🟡软约束{yellow_count}件 · 其余✅各自有账")

    tree_text = "\n".join(lines)
    stamp = compute_stamp(tree_text)
    lines.append(f"🔏 TSL-stamp {stamp}")
    lines.append(f"📄 明细（长判据全文）：脚本stdout即明细·豆包端无trees/存档（平台边界型）")

    # 签发
    append_stamp(stamp, window)

    # 评级行
    lines.append(f"\n📊 TSL会话评级：L{level}（严格截断制·⚪平台边界不截断·🔴执行缺口截断）")

    output = "\n".join(lines)
    print(output)

    # 异常时非零退出
    if red_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
