#!/usr/bin/env python3
"""
zwork_tsl_verify.py — Zwork 端（AutoClaw 新客户端）童灵TSL（会话级L7验证清单）机械校验器

设计哲学（来源：数字分身设计哲学/08-会话级L7验证清单.md §十 + §八·七）：
  根治＝把构造权从AI手里拿走交给脚本。AI只许逐行relay本脚本stdout，
  改一行层状态＝违规（无钩子端靠 stamp + stamps.log 事后验真）。

平台边界（诚实标注，不假装完整）：
  Zwork 无 Stop 钩子、无 UserPromptSubmit 钩子、无会话日志访问（平台托管型·06 §2.7.2.1 第四型）。
  L1身份感知 / L3上岗仪式 / L4本轮Read切片 / L5守护三查执行 属于"AI侧会话内行为"，
  脚本无法机械验证本轮是否执行——如实标 ⚪查不了（平台边界型），
  不接受AI自填✅。脚本只校验"基础设施在位性"和"产出物存在性/新鲜度"。

与豆包/Trae Work 的关系（§八·七 同构第三实例）：
  恒驻核落点不同：Zwork = ~/个人AI档案/AutoClaw/AGENTS.md 标记区段
  （core_slice+L6 成对标记·W2 doenglingz_slice_watch 自动同步）——非 USER.md / doenglingz-core.md。
  L6 自愈=W2 watcher（心跳文件判活·非 launchd）。

用法：
  python3 zwork_tsl_verify.py [--window MINUTES] [--full]
输出：标准化TSL树 + 🔏stamp + stamps.log签发账本
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import sys
import json
import hashlib
import time
from datetime import datetime

__version__ = "v0.1.0"
SCRIPT_NAME = "zwork_tsl_verify"

HOME = os.path.expanduser("~")
MC_BASE = os.environ.get("BULUOTU_MC", os.path.join(HOME, "个人AI档案"))
AGENTS_MD = os.path.join(MC_BASE, "AutoClaw", "AGENTS.md")
SOUL_MD = os.path.join(MC_BASE, "AutoClaw", "SOUL.md")
SLICES_DIR = os.path.join(MC_BASE, "数字分身", "K2切片蒸馏", "slices")
MANIFEST = os.path.join(SLICES_DIR, "manifest.json")
SPEC_MD = os.path.join(MC_BASE, "数字分身", "童灵·人格规格书.md")
W2_HEARTBEAT = os.path.join(MC_BASE, "数字分身", "scripts", "last_run_doenglingz_slice_watch.ts")
GROWTH_BOX = os.path.join(MC_BASE, "成长箱")
AI_LIB = os.path.join(HOME, "[日记仓库]", "2-知识库", "09-AI学习库")  # 2026-10-13 C''波次2迁移后路径同步
SYSLOG_DIR = os.path.join(MC_BASE, "工作日志", "系统日志")
STAMPS_LOG = os.path.join(HOME, ".cache", "tsl_verify", "stamps.log")

WINDOW_MIN = 30


def file_exists(p):
    return os.path.isfile(p)


def grep_in_file(p, needle):
    try:
        return needle in open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False


def file_mtime(p):
    try:
        return os.path.getmtime(p)
    except Exception:
        return None


def dir_latest_mtime(d, pattern="*.md"):
    import glob
    files = glob.glob(os.path.join(d, pattern))
    if not files:
        return None
    return max(file_mtime(f) or 0 for f in files)


def check_l0():
    """L0接入态：端实体 AGENTS.md 在场且含童灵配置（K2 标记区段）"""
    ok = (file_exists(AGENTS_MD)
          and grep_in_file(AGENTS_MD, "K2 core_slice 开始")
          and grep_in_file(AGENTS_MD, "童灵"))
    detail = "AGENTS.md(K2区段)=%s" % ("在位" if ok else "缺失")
    return ("L0 接入态", "✅做到" if ok else "🔴没做", detail)


def check_l1():
    """L1身份感知：平台 Memory 指针卡 Run 注入——脚本无法验证AI侧，标⚪"""
    return ("L1 身份感知", "⚪查不了", "平台 Memory Run 注入·AI侧行为（平台边界型·第四型）")


def check_l2():
    """L2规则加载：K2 标记区段含 core_slice+L6+命名红线；SOUL 卡号纪律"""
    has_core = grep_in_file(AGENTS_MD, "core_slice")
    has_l6 = grep_in_file(AGENTS_MD, "L6 反向约束 开始")
    has_naming = grep_in_file(AGENTS_MD, "Doenglingz") or grep_in_file(AGENTS_MD, "童灵")
    has_cite = grep_in_file(SOUL_MD, "把沉淀当资产")
    ok = has_core and has_l6 and has_naming and has_cite
    detail = "core_slice=%s L6=%s 命名=%s SOUL纪律=%s" % (
        "✓" if has_core else "✗", "✓" if has_l6 else "✗",
        "✓" if has_naming else "✗", "✓" if has_cite else "✗")
    return ("L2 规则加载", "✅做到" if ok else "🔴没做", detail)


def check_l3():
    return ("L3 上岗仪式", "⚪查不了", "AI侧会话内行为·脚本无会话日志访问（平台边界型）")


def check_l4():
    slices_exist = os.path.isdir(SLICES_DIR)
    slice_files = ["L2_认知风格.md", "L3_行为规则.md", "L4_表达DNA.md", "L5_盲区与边界.md"]
    found = [f for f in slice_files if file_exists(os.path.join(SLICES_DIR, f))]
    ok = slices_exist and len(found) >= 2
    detail = "切片在位%d/4·本轮Read⚪查不了" % len(found)
    return ("L4 域切片", "✅做到" if ok else "🔴没做", detail)


def check_l5():
    """L5守护三查：标记区段四行完整性可机械查；切片新鲜度"""
    n = 0
    try:
        content = open(AGENTS_MD, encoding="utf-8", errors="ignore").read()
        for marker in ("K2 core_slice 开始", "K2 core_slice 结束",
                       "L6 反向约束 开始", "L6 反向约束 结束"):
            if marker in content:
                n += 1
    except Exception:
        pass
    ok = n == 4
    detail = "标记区段%d/4·8要素/试金石执行⚪查不了（软约束·doenglingz-guard-zwork 承载）" % n
    return ("L5 守护三查", "✅做到" if ok else "🔴没做", detail)


def check_l6():
    """L6自愈同步：W2 watcher 心跳新鲜度（非 launchd·Zwork 形态）"""
    mt = file_mtime(W2_HEARTBEAT)
    fresh = mt and (time.time() - mt) / 3600 < 25  # 25h 容忍（30min 级 cron 停摆一天仍可检出）
    detail = "W2心跳=%s" % ("新鲜(%s)" % datetime.fromtimestamp(mt).strftime("%m-%d %H:%M") if mt else "缺失")
    return ("L6 自愈同步", "✅做到" if fresh else "🔴没做", detail)


def check_l7(window_min):
    results = []
    now = time.time()

    gb_latest = dir_latest_mtime(GROWTH_BOX)
    gb_fresh = gb_latest and (now - gb_latest) / 60 < window_min * 60
    results.append(("L7-1 错误→成长箱", "✅" if gb_fresh else "🔴没做",
                    "最新=" + (datetime.fromtimestamp(gb_latest).strftime("%H:%M") if gb_latest else "无")))

    rl_latest = file_mtime(os.path.join(MC_BASE, "成长箱", "铁律盲区扫描.log"))
    rl_fresh = rl_latest and (now - rl_latest) / 60 < window_min * 60
    results.append(("L7-2 铁律反哺", "✅" if rl_fresh else "🔴没做",
                    "最新=" + (datetime.fromtimestamp(rl_latest).strftime("%H:%M") if rl_latest else "无")))

    al_latest = dir_latest_mtime(AI_LIB)
    al_fresh = al_latest and (now - al_latest) / 60 < window_min * 60
    results.append(("L7-3 立场卡反哺", "✅" if al_fresh else "🔴没做",
                    "最新=" + (datetime.fromtimestamp(al_latest).strftime("%H:%M") if al_latest else "无")))

    sl_latest = dir_latest_mtime(SYSLOG_DIR)
    sl_fresh = sl_latest and (now - sl_latest) / 60 < window_min * 60
    results.append(("L7-4 系统日志", "✅" if sl_fresh else "🔴没做",
                    "最新=" + (datetime.fromtimestamp(sl_latest).strftime("%H:%M") if sl_latest else "无")))

    refl_ok = grep_in_file(SYSLOG_DIR and os.path.join(
        SYSLOG_DIR, "系统日志_%s.md" % datetime.now().strftime("%Y-%m-%d")), "[童灵思考]")
    results.append(("L7-5 反思沉淀", "✅" if refl_ok else "🔴没做",
                    "[童灵思考]段=%s（当日日志）" % ("在场" if refl_ok else "未见")))
    return results


def compute_stamp(tree_text):
    return hashlib.sha256(tree_text.encode("utf-8")).hexdigest()[:8]


def append_stamp(stamp, window_min):
    os.makedirs(os.path.dirname(STAMPS_LOG), exist_ok=True)
    with open(STAMPS_LOG, "a", encoding="utf-8") as f:
        f.write("%s | %s %s | window=%dmin | stamp=%s\n" % (
            datetime.now().isoformat(), SCRIPT_NAME, __version__, window_min, stamp))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Zwork 端童灵TSL机械校验器")
    parser.add_argument("--window", type=int, default=WINDOW_MIN, help="本会话窗口分钟数")
    parser.add_argument("--full", action="store_true", help="输出完整版")
    args = parser.parse_args()
    window = args.window

    checks = [check_l0(), check_l1(), check_l2(), check_l3(),
              check_l4(), check_l5(), check_l6()]
    l7_results = check_l7(window)
    checks.extend(l7_results)

    # 评级（严格截断制·⚪平台边界型不截断·只看🔴）
    level = 7
    for i, (name, status, detail) in enumerate(checks[:7]):
        if "🔴" in status:
            level = i - 1
            break
    l7_all_ok = all("✅" in r[1] for r in l7_results)
    if not l7_all_ok and level >= 7:
        level = 6

    lines = []
    lines.append("🧾 TSL 机械核验 %s · since=%s · window=%dmin · Zwork 端" % (
        __version__, datetime.now().strftime("%Y-%m-%d %H:%M"), window))
    lines.append("├─ 层 状态 判定依据（AI说的不算，账本/文件/mtime才算）")
    for name, status, detail in checks:
        lines.append("├─ %s %s %s" % (name, status, detail))
    red = sum(1 for _, s, _ in checks if "🔴" in s)
    white = sum(1 for _, s, _ in checks if "⚪" in s)
    lines.append("└─ 结论：🔴没做%d件 · ⚪查不了%d件（平台边界型） · 其余✅各自有账" % (red, white))

    tree_text = "\n".join(lines)
    stamp = compute_stamp(tree_text)
    lines.append("🔏 TSL-stamp %s" % stamp)
    lines.append("📄 明细：脚本stdout即明细·Zwork 端无 trees/ 存档（平台边界型·同豆包/Trae）")

    append_stamp(stamp, window)
    lines.append("\n📊 TSL会话评级：L%d（严格截断制·⚪平台边界不截断·🔴执行缺口截断）" % level)

    print("\n".join(lines))
    if red > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
