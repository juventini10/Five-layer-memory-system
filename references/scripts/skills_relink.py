#!/usr/bin/env python3
# version: v0.1
"""
skills_relink.py — 技能软链接自愈器（幂等·根因治理）

设计依据（你的架构哲学 / 第一性原理）：
- 唯一真源：~/[记忆共享中心]/技能配置/ 是全部技能的权威出处
- 桥接方式：用软链接把真源桥到 Hermes/各工具，保证"唯一来源"+"自动最新"
- 根因问题：历史上出现过链式指向 /tmp 临时区 → 系统清理后整批断链
         （表现为"重启后又调不出"，荒谬且复发）

本脚本一次性根治：
- 遍历真源里每个含 SKILL.md 的目录
- 在 ~/.hermes/skills/ 建立/修复软链接，目标一律为"真源绝对路径"
- 任何已存在的链接（含指向 /tmp 的死链、指向错误真源的链）一律用 ln -sf 覆盖
- 幂等：重复跑结果一致，不会制造第二份真身

用法：
    python3 skills_relink.py              # 自愈（默认 Hermes）
    python3 skills_relink.py --dry        # 只报告需要处理的，不改动
可选 --dest 指向其他工具的 skills 目录（如 lobsterai/Trae/DSH 的桥接目录）
可选 --prune-orphans 剪除孤儿链（断链/真源已无对应目录）·**默认只报告不剪**（2026-10-01 新增）

⛔ 不删除真源、不复制技能、不创建第二份真身——只维护"窗口"链接。

⚠️ 孤儿链盲区（2026-10-01 根治·Hermes 端实证触发）：
  本脚本 v0.1 的循环是 `for name in os.listdir(SRC)`——**只从真源往 dest 建链**，
  ⛔ 从不扫 dest 侧 ⇒ 「真源目录已改名/删除·链接残留」这类失效它**结构性看不见**。
  实证（Hermes 端）：真源 `技能配置/抖音选题助手` 已不存在（其 SKILL.md 后继者
  `热点捕手/SKILL.md` 明文「≠ 旧『抖音选题助手』·已废弃」），而
  `~/.hermes/skills/抖音选题助手` 断链残留至今——`--dry` 跑出「将处理 0 个链接」
  全绿，**孤儿链就在它盲区里躺着**（守卫规范 §3.12 空转显形的典型形态）。
  ✅ v0.2 增 `--prune-orphans`：扫 dest 侧，列出「dest 有 · 真源无对应 SKILL.md 目录」
  或「断链」两类孤儿。⛔ **默认只报告**（保守：孤儿也可能是端侧自装的独立技能·
  不是所有端都把 skills 根当纯桥接窗口），须显式 `--prune-orphans` 才 `--move` 隔离。
  ⛔ 永远不 `--move` 到真源（那等于删技能）；隔离区在 `<dest>/../cache/relink_orphans_<ts>/`。
  ⛔ 不碰隐藏目录（`.archive`/`.hub`/`.locks`/`.curator_*` 等端机制目录）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys
import argparse
ARGS = None  # ⚠️ 模块级默认（2026-10-02 修·被 test_skills_relink 暴露的真实缺陷）
#    `needs_fix()` 在模块级读 `ARGS.force_dir`，而 ARGS 只在 `main()` 里赋值
#    ⇒ 任何非 CLI 调用（测试/被 import）都 NameError。给默认值后
#    「没跑 main」= 未指定 force_dir ⇒ 走"实目录跳过"分支（保守·不动用户目录）。

HOME = os.path.expanduser("~")
SRC = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置")
DEFAULT_DEST = os.path.join(HOME, ".hermes", "skills")

# 仅"疑似皮叔系/需要桥接的真源"——但自愈器应为通用：真源里所有含 SKILL.md 的都桥
# 若只想桥皮叔系，可加 --author 过滤；默认全量（符合"唯一真源"全覆盖）


def real_path(p):
    return os.path.abspath(os.path.realpath(p))


def is_broken(link):
    """软链接存在但目标不可达"""
    return os.path.islink(link) and not os.path.exists(link)


def needs_fix(link, target):
    """
    返回 (need, reason)
    need: True 表示需要 ln -sf 重建
    """
    if not os.path.lexists(link):
        return True, "缺失(MISSING)"
    if os.path.islink(link):
        if not os.path.exists(link):
            return True, "断链(BROKEN)"
        cur = os.readlink(link)
        # 已经是真源绝对路径且有效 → 无需动
        if real_path(cur) == real_path(target) and os.path.isdir(target):
            return False, "已有效"
        return True, f"指向错误({cur})"
    if os.path.isdir(link):
        # 实目录（可能是 Curator 装的，或旧复制）——默认不动，除非 --force-dir
        want = bool(getattr(ARGS, "force_dir", False)) if ARGS else False
    return (True, "实目录(非链接)") if want else (False, "实目录(跳过)")
    return True, "未知类型"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=DEFAULT_DEST, help="桥接目标目录（默认 ~/.hermes/skills）")
    ap.add_argument("--dry", action="store_true", help="只报告不改动")
    ap.add_argument("--force-dir", action="store_true", help="连实目录也改成软链接（慎用）")
    ap.add_argument("--prune-orphans", action="store_true",
                    help="剪除孤儿链（断链/真源已无对应目录）·v0.2 新增·默认只报告")
    global ARGS
    ARGS = ap.parse_args()

    dest = os.path.expanduser(ARGS.dest)
    if not os.path.isdir(SRC):
        print(f"❌ 真源不存在: {SRC}")
        sys.exit(1)
    os.makedirs(dest, exist_ok=True)

    print(f"真源 : {SRC}")
    print(f"目标 : {dest}")
    print(f"模式 : {'DRY-RUN(只报告)' if ARGS.dry else '自愈(写链接)'}")
    print("-" * 70)

    fixed, skipped, errors = [], [], []
    for name in sorted(os.listdir(SRC)):
        d = os.path.join(SRC, name)
        sk = os.path.join(d, "SKILL.md")
        if not (os.path.isdir(d) and os.path.isfile(sk)):
            continue  # 非技能目录（如 andrej-karpathy-skills 这种无 SKILL.md 的）跳过
        link = os.path.join(dest, name)
        need, reason = needs_fix(link, d)
        if not need:
            skipped.append((name, reason))
            continue
        fixed.append((name, reason))
        if not ARGS.dry:
            try:
                if os.path.lexists(link):
                    os.remove(link)
                os.symlink(d, link, target_is_directory=True)
            except Exception as e:
                errors.append((name, str(e)))

    # ── 孤儿链检测（v0.2 新增·盲区根治·⛔ 默认只报告）──
    orphans = []
    try:
        src_names = {n for n in os.listdir(SRC)
                     if os.path.isfile(os.path.join(SRC, n, "SKILL.md"))}
    except OSError:
        src_names = set()
    for name in sorted(os.listdir(dest)):
        if name.startswith("."):      # ⛔ 端机制目录（.archive/.hub/.locks/.curator_*）不动
            continue
        link = os.path.join(dest, name)
        if not os.path.islink(link):
            continue                  # ⛔ 只管软链·实目录（端自装技能）不管
        broken = not os.path.exists(link)
        orphan = name not in src_names
        if broken or orphan:
            orphans.append((name, ("断链" if broken else "") +
                            ("真源无对应目录" if orphan else ""),
                            os.readlink(link)))

    if orphans:
        print()
        print(f"⚠️ 孤儿链 {len(orphans)} 条（dest 有 · 真源无 / 断链·v0.1 盲区）:")
        for name, why, tgt in orphans:
            print(f"   ✗ {name:32s} {why:18s} → {tgt}")
        if ARGS.prune_orphans and not ARGS.dry:
            import datetime
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            qdir = os.path.join(os.path.dirname(dest.rstrip("/")),
                                "cache", f"relink_orphans_{stamp}")
            os.makedirs(qdir, exist_ok=True)
            for name, _why, _tgt in orphans:
                src = os.path.join(dest, name)
                try:
                    os.rename(src, os.path.join(qdir, name))
                    print(f"   ↩ 已隔离 {name} → {qdir}")
                except Exception as e:
                    print(f"   ❌ 隔离失败 {name}: {e}")
        else:
            print("   （⛔ 默认不动·加 --prune-orphans 隔离到 cache/relink_orphans_<ts>/）")

    # 报告
    print(f"\n【需要修复/建立】{len(fixed)} 个:")
    for n, r in fixed:
        print(f"  {'→ 已建' if not ARGS.dry else '→ 将建'}  {n:28} ({r})")
    print(f"\n【无需处理】{len(skipped)} 个:")
    for n, r in skipped:
        print(f"  ✓ {n:28} {r}")
    if errors:
        print(f"\n【失败】{len(errors)} 个:")
        for n, e in errors:
            print(f"  ✗ {n}: {e}")

    print("-" * 70)
    verb = "将处理" if ARGS.dry else "已处理"
    print(f"✅ {verb} {len(fixed)} 个链接；{len(skipped)} 个已有效；{len(errors)} 个失败")
    if not ARGS.dry and errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
