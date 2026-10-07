#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""shadow_ssot_guard.py v1.0 — SHADOW.md 唯一真源守卫（防 SSOT 分叉复发）

背景（根因，非"又有人忘了"）：
  SHADOW.md 是 L5 潜意识层唯一实体文件。三次分叉全部发生在"顺手修别的东西"时：
    ① 2026-07-19 删根级死软链
    ② 2026-10-01 Qoder CN 修 QClaw 悬空软链时，"顺手"把根级也补建回来
    ③ 2026-10-02 再次清理（本次）
  三次人工判断全对，但每次都能被下一个人推翻——因为路径治理没有机械硬墙。
  本守卫把"不许建软链/副本"从"靠人记得"变成"撞墙"。

机制（against 工作区实况，非 against HEAD）：
  HEAD 对账在 git 层面做（pre-commit）；本守卫做 HEAD 做不到的：
  ① 软链检测——全盘扫 SHADOW.md 的符号链接（真源自身之外任何指向真源的链接都算违规）
  ② 副本检测——内容指纹比对，同内容不同路径 = 分叉副本
  ③ 活体唯一性——真源必须存在且是实体文件（非链接）

用法：
  env -u PYTHONHOME -u PYTHONPATH python3 shadow_ssot_guard.py
  env -u PYTHONHOME -u PYTHONPATH python3 shadow_ssot_guard.py --path /任意/新路径   # 建前预检
出口：
  0 = SSOT 唯一，无违规
  1 = 检测到软链/副本分叉（打印违规清单+修复建议）
  2 = 真源本身缺失或损坏（严重·阻断）
"""
import hashlib
import os
import sys

SSOT = os.path.expanduser("[记忆共享中心]/潜意识层/SHADOW.md")

# 全盘扫描根（排除自身与归档/备份区——那些是历史快照与分发模板，不是活体分叉）
SCAN_ROOTS = [
    os.path.expanduser("~"),
]
EXCLUDE_DIR_PARTS = [
    ".git", "发布库", "记忆琥珀", "重要备份", "记忆规则/归档",
    "skills", ".venv", "缓存", "cache", "node_modules", "Trash",
]


def fail(code, msg):
    print("[shadow_ssot_guard]{}".format(msg), file=sys.stderr)
    sys.exit(code)


def sha(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def excluded(path):
    return any(part in path for part in EXCLUDE_DIR_PARTS)


def scan_all(root):
    """扫出所有名为 SHADOW.md 的实体与软链。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        if excluded(dirpath):
            dirnames[:] = []
            continue
        if "SHADOW.md" in filenames:
            p = os.path.join(dirpath, "SHADOW.md")
            found.append(p)
    return found


def scan_links_to_ssot(root):
    """扫出【所有】指向真源的软链，不限文件名。

    ⛔ 教训（2026-10-02 负例测试实证）：v1.0 初版只扫名为 SHADOW.md 的文件，
    于是 `_test_link.md -> 潜意识层/SHADOW.md` 这类"改了名的分叉"全盘漏网，
    守卫对最典型的分叉手法是瞎的。SSOT 分叉不认文件名——认目标。
    """
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        if excluded(dirpath):
            dirnames[:] = []
            continue
        # os.walk 默认不跟随软链目录，但会把软链文件列进 filenames
        for name in filenames:
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                try:
                    if os.path.realpath(p) == SSOT:
                        hits.append(p)
                except OSError:
                    pass
    return hits


def check():
    # ① 活体唯一性：真源必须存在且是实体文件
    if not os.path.exists(SSOT):
        fail(2, "🔴 真源缺失：{}\n   潜意识层是空的——这不是守卫问题，是数据丢了。查回收站/备份。".format(SSOT))
    if os.path.islink(SSOT):
        fail(2, "🔴 真源本身变成了软链：{}\n   SSOT 不能是链接，必须是实体文件。".format(SSOT))

    ssot_hash = sha(SSOT)
    if ssot_hash is None:
        fail(2, "🔴 真源不可读（权限或损坏）：{}".format(SSOT))
    violations = []

    # ② 全盘扫【所有】指向真源的软链（不限文件名）
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for p in scan_links_to_ssot(root):
            violations.append({
                "path": p, "kind": "软链(指向真源·分叉)",
                "target": os.readlink(p), "hash_match": None,
            })

    # ③ 全盘扫 SHADOW.md 副本（实体·内容与真源逐字节相同）
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for p in scan_all(root):
            if os.path.islink(p) or os.path.realpath(p) == SSOT:
                continue  # 真源自身 / 软链已在②处理
            h = sha(p)
            if h is not None and h == ssot_hash:
                violations.append({
                    "path": p, "kind": "副本(内容与真源逐字节相同)",
                    "target": "(实体文件)", "hash_match": True,
                })

    if not violations:
        print("[shadow_ssot_guard] ✅ SSOT 唯一：全盘仅真源一个实体，无软链、无副本")
        print("                   真源：{}  sha256={}".format(SSOT, ssot_hash[:12]))
        return 0

    print("[shadow_ssot_guard] 🔴 检测到 {} 处 SSOT 分叉：\n".format(len(violations)))
    for i, v in enumerate(violations, 1):
        print("  {}. {}".format(i, v["path"]))
        print("     类型：{}".format(v["kind"]))
        if v["target"] != "(实体文件)":
            print("     指向：{}".format(v["target"]))
    print("""
修复指引（⛔ 禁止 rm，用 trash / mv）：
  · 软链 = 指针，删它不丢任何数据：
      mv "<路径>" ~/.Trash/$(basename "<路径>")-$(date +%Y%m%d-%H%M%S)
  · 副本 = 先人工确认是否有意保留，确认后同样 mv 进回收站
  · 删完跑本守卫复验，应回到 exit 0
  · 根因提醒：这些分叉都是"顺手修别的东西"时产生的——修 SHADOW 相关链之前，
    先问一句"我这个动作会不会新建指向真源的路径"
""")
    return 1


def precheck(new_path):
    """建前预检：AI 要动 SHADOW 相关路径前，先跑这个。"""
    if os.path.islink(new_path):
        target = os.readlink(new_path)
        if os.path.realpath(new_path) == SSOT:
            print("[shadow_ssot_guard] 🚫 拒绝：该路径是指向真源的软链")
            print("                   {} -> {}".format(new_path, target))
            print("                   真源已可用绝对路径直接读，无需建链。")
            return 1
    if os.path.exists(new_path) and not os.path.islink(new_path):
        if sha(new_path) == sha(SSOT):
            print("[shadow_ssot_guard] 🚫 拒绝：该路径已是真源的逐字节副本")
            print("                   {}".format(new_path))
            return 1
    print("[shadow_ssot_guard] ✅ 预检通过：{} 不构成 SSOT 分叉".format(new_path))
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--path":
        sys.exit(precheck(sys.argv[2]))
    sys.exit(check())