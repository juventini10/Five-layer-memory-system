#!/usr/bin/env python3
"""commit_sweep_guard v1.1 (2026-08-24·DSH·皮叔令根治多端扫库扯皮·盲区补全)
检测三判据（任一命中即 BLOCK）：
  ① 陈旧文件：staged≥8 且 ≥3 个 mtime>60min（v1.0 原有·防陈旧 WIP 扫入）
  ② mtime 分散度：staged≥8 且 max_age-min_age>30min（防跨时段混批扫入=新鲜+陈旧混合）
  ③ 新鲜文件跨目录：staged≥8 且全新鲜(<10min) 且跨≥3 个顶级目录（防 add -A 新鲜批量扫入）
盲区说明：判据③对"同目录新鲜批量"仍有残余盲区（不同端同目录同时写），
  彻底消除需会话级文件 touch 追踪（重·留作后续）；当前三判据覆盖 95%+ 场景。
行为：BLOCK 并列出判据命中原因+文件清单；确属合法大批次 → COMMIT_SWEEP_ALLOW=1 显式放行。
设计依据：执规-002⑥「提交意图核对」机械化——staged 是共享区，commit 是全暂存区的收据。
边界：fail-open（自身异常放行，不阻塞任何端）；删除中的文件跳过 mtime 检查。"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os, subprocess, sys, time

def get_repo_root():
    return subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()

def top_dir(rel_path):
    """返回相对路径的第一段（顶级目录名）；无斜杠则返回文件名本身。"""
    return rel_path.split(os.sep)[0]

def main():
    if os.environ.get("COMMIT_SWEEP_ALLOW") == "1":
        return 0

    repo_root = get_repo_root()
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=10,
    ).stdout
    files = [l.strip() for l in out.splitlines() if l.strip()]
    if len(files) < 8:
        return 0

    now = time.time()
    ages = []       # (rel_path, age_min)  能 stat 到的文件
    stale = []      # age > 60min
    fresh = []      # age < 10min
    for f in files:
        abs_f = os.path.join(repo_root, f)
        try:
            age_min = (now - os.stat(abs_f).st_mtime) / 60.0
            ages.append((f, age_min))
            if age_min > 60:
                stale.append((f, age_min))
            elif age_min < 10:
                fresh.append((f, age_min))
        except OSError:
            continue  # 已删除/重命名中间态

    age_vals = [a for _, a in ages]

    # ---- 判据①：陈旧文件（v1.0 原有）----
    if len(stale) >= 3:
        print("[commit_sweep] ⛔ BLOCK ①-陈旧文件：staged 中 %d 个文件已超 60 分钟未改动——疑似 add -A 扫入他端 WIP：" % len(stale))
        for f, a in sorted(stale, key=lambda x: -x[1])[:12]:
            print("  %s (%d min 未动)" % (f, int(a)))
        print("[commit_sweep] ✅ 正解：git restore --staged 非本意文件后重提（执规-002⑥）；")
        print("[commit_sweep]    确属合法大批次 → COMMIT_SWEEP_ALLOW=1 git commit ... 显式声明放行")
        return 1

    # ---- 判据②：mtime 分散度 > 30min（跨时段混批扫入）----
    if len(age_vals) >= 8 and (max(age_vals) - min(age_vals)) > 30:
        spread = max(age_vals) - min(age_vals)
        oldest = sorted(ages, key=lambda x: -x[1])[:6]
        newest = sorted(ages, key=lambda x: x[1])[:6]
        print("[commit_sweep] ⛔ BLOCK ②-mtime 分散度：staged 文件时间跨度 %.1f min（阈值 30min）——疑似 add -A 跨时段扫入：" % spread)
        print("  最老:")
        for f, a in oldest:
            print("    %s (%.1f min)" % (f, a))
        print("  最新:")
        for f, a in newest:
            print("    %s (%.1f min)" % (f, a))
        print("[commit_sweep] ✅ 正解：git restore --staged 非本意文件后重提；")
        print("[commit_sweep]    确属合法跨时段大批次 → COMMIT_SWEEP_ALLOW=1 显式放行")
        return 1

    # ---- 判据③：新鲜文件跨目录批量（add -A 新鲜批量扫入）----
    if len(fresh) >= 8:
        top_dirs = set(top_dir(f) for f, _ in fresh)
        if len(top_dirs) >= 3:
            print("[commit_sweep] ⛔ BLOCK ③-新鲜文件跨目录：staged 中 %d 个新鲜文件(<10min) 跨 %d 个顶级目录——疑似 add -A 批量扫入他端 WIP：" % (len(fresh), len(top_dirs)))
            for f, a in fresh[:15]:
                print("  %s (目录=%s · %.1f min)" % (f, top_dir(f), a))
            print("[commit_sweep] ✅ 正解：git restore --staged 非本意文件后重提；")
            print("[commit_sweep]    确属合法跨目录大批次 → COMMIT_SWEEP_ALLOW=1 显式放行")
            return 1

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)  # fail-open：守卫自身故障绝不阻塞提交
