#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""amber_rollback.py — 备份回滚器（记忆琥珀第三维：怎么把备份取回来）

缘起（2026-10-06）：三明治 L2 裁决——备份决策三维里「放哪」有铁律-005④、
「留多久」有记忆琥珀引擎（amber-backup.sh RETENTION_DAYS=7），
⛔**唯独「怎么取回」今天完全没有任何机制覆盖**。实证：当日 09:17 把
install_scripts.py 的备份放进记忆琥珀后，**AI 自己找错了文件名**。
本件补的就是这一维：⛔ 不依赖人记得路径，⛔ 不依赖人记得命名。

三步：
  1  list  列出该文件在记忆琥珀里的全部版本时间线（时间倒序 + 体积 + 年龄）
  2  show   显示某一版内容的前 N 行（不写盘）
  3  rollback  回滚到指定版本（**写前自动备份当前版**⇒ 回滚本身也可回滚）

降级纪律（必落·因 commands 自身也会坏）：
  任何异常路径都打印一行**可直接粘进终端**的 `ls -t` 兜底命令，
  使「命令坏掉」不等于「人只能手翻目录」。

用法：
  python3 amber_rollback.py list 系统日志_2026-10-06.md
  python3 amber_rollback.py show  系统日志_2026-10-06.md --index 1
  python3 amber_rollback.py rollback 系统日志_2026-10-06.md --index 1
  python3 amber_rollback.py find  kb_inject        # 关键字模糊搜（忘了全名时）

退出码：0=成功；1=有错（明细打印到 stdout）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import shutil
import sys
import time

HOME = os.path.expanduser("~")
AMBER = os.path.join(os.path.expanduser("[记忆共享中心]"), "记忆琥珀")
FALLBACK = "find [记忆共享中心]/记忆琥珀 -name '*%s*.bak*' -type f | xargs ls -t 2>/dev/null"   # ⛔ 保持未格式化模板：每处按 keyword 填，避免二次 % 失效


def _fmt_size(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.0f%s" % (n, u)
        n /= 1024.0
    return "%.1fTB" % n


def scan(keyword, roots=None):
    """扫记忆琥珀下所有 *.bak* 文件，命中关键字的按 mtime 倒序返回。
    刻意**不依赖引擎的命名规范**（引擎只认 `..._YYYYMMDD-HHMMSS_hash6.bak`，
    而各脚本自建的 `.bak-HHMMSS_hash` / `.bak-<时间戳>` 都不被它认）⇒
    判定锚＝**文件实况 + 关键字**，不是某个机构的登记。"""
    out = []
    base = roots or [AMBER]
    for root in base:
        if not os.path.isdir(root):
            continue
        for dp, _dn, fn in os.walk(root):
            if "/engine/" in dp + "/":
                continue                      # 引擎自身产物（amber.log/rot）不是备份
            for f in fn:
                if ".bak" not in f:
                    continue
                if keyword and keyword not in f:
                    continue
                p = os.path.join(dp, f)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                out.append((st.st_mtime, st.st_size, p))
    out.sort(reverse=True)
    return out


def find_original(candidates):
    """从备份名推原件（**只作提示·回滚路径由用户显式确认**）。

    2026-10-06 压测逮到的危险 bug：旧版「找到第一个名字匹配的就返回」在
    `知识联邦引擎_search_kb.py.bak-…` 这类**带前缀修饰**的备份名上会推错，
    把回滚目标写成另一个文件（audit_search_kb.py）——**回滚是写盘动作，
    推错一次就写坏一个文件**。故改为：
      ① 去掉 `.bak*` 后缀与 `_YYYYMMDD-HHMMSS_hash` 后缀得到 stem；
      ② 全盘收集**所有**候选，按「stem 与文件名关系」分三档打分；
      ③ **0 个或 >1 个候选都不自动采用**——回滚时直接拒绝并要求 --target 指定。
    """
    stems = set()
    for _mt, _sz, p in candidates:
        base = os.path.basename(p)
        stem = re.split(r"\.bak[-.]", base)[0]
        stem = re.sub(r"_\d{8}-\d{6}_[a-f0-9]{6}$", "", stem)
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}[_-]", "", stem)
        if stem:
            stems.add(stem)
    exact, loose = [], []
    for root in (os.path.join(os.path.expanduser("[记忆共享中心]"), "工作日志", "系统日志"),
                 os.path.join(os.path.expanduser("[记忆共享中心]"), "发布库", "五层记忆系统",
                              "布洛陀-全平台安装包"),
                 os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置"),
                 os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具"),
                 os.path.join(os.path.expanduser("[记忆共享中心]"), "脚本中心")):
        if not os.path.isdir(root):
            continue
        for dp, _dn, fn in os.walk(root):
            for f in fn:
                if f in stems:
                    exact.append(os.path.join(dp, f))
                elif any(f in s or s in f for s in stems):
                    loose.append(os.path.join(dp, f))
    if len(exact) == 1:
        return exact[0], "唯一精确匹配"
    if len(exact) > 1:
        return None, "**%d 个精确匹配·需 --target 指定**" % len(exact)
    if len(loose) == 1:
        return None, "**仅 1 个近似匹配（%s）·需 --target 确认**" % os.path.basename(loose[0])
    return None, "**无法唯一定位·需 --target 指定**"


def cmd_list(keyword):
    c = scan(keyword)
    if not c:
        print("未在记忆琥珀找到含「%s」的备份。" % keyword)
        print("兜底（可直接粘进终端）：")
        print("  " + (FALLBACK % keyword))
        return 1
    print("═══ 记忆琥珀备份时间线：%s（%d 版 · 时间倒序）" % (keyword, len(c)))
    print("   %-4s %-17s %-9s %s" % ("#", "时间", "体积", "路径"))
    for i, (mt, sz, p) in enumerate(c, 1):
        age = (time.time() - mt) / 86400.0
        print("   %-4d %-17s %-9s %s"
              % (i, time.strftime("%m-%d %H:%M:%S", time.localtime(mt)),
                 _fmt_size(sz), p.replace(HOME, "~")))
    orig, why = find_original(c)
    print("\n   原件定位：%s"
          % (("%s  %s" % (orig.replace(HOME, "~"), why)) if orig else why))
    print("\n   回滚：python3 %s rollback %s --index <#>" % (os.path.basename(__file__), keyword))
    return 0


def cmd_show(keyword, index):
    c = scan(keyword)
    if not c or index < 1 or index > len(c):
        print("索引越界（共 %d 版）" % len(c))
        return 1
    mt, sz, p = c[index - 1]
    print("── %s（%s · %s）" % (p.replace(HOME, "~"),
                                time.strftime("%Y-%m-%d %H:%M", time.localtime(mt)),
                                _fmt_size(sz)))
    try:
        t = open(p, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print("读失败：%s" % e)
        return 1
    lines = t.splitlines()
    for l in lines[:30]:
        print("   " + l[:150])
    if len(lines) > 30:
        print("   …（共 %d 行）" % len(lines))
    return 0


def cmd_rollback(keyword, index, dry=False, rest=()):
    c = scan(keyword)
    if not c or index < 1 or index > len(c):
        print("索引越界（共 %d 版）" % len(c))
        return 1
    _mt, _sz, src = c[index - 1]
    tgt = None
    for i, a in enumerate(rest):
        if a == "--target" and i + 1 < len(rest):
            tgt = os.path.expanduser(rest[i + 1])
    if not tgt:
        _auto, why = find_original(c)
        print("⛔ 拒绝自动回滚：%s" % why)
        print("   （回滚是写盘动作·推错一次就写坏一个文件·⛔不猜）")
        print("   请显式指定：python3 %s rollback %s --index %d --target <原件路径>"
              % (os.path.basename(__file__), keyword, index))
        print("   兜底（可直接粘）：open '%s'" % src.replace(HOME, "~"))
        return 1
    orig = tgt
    if not os.path.exists(orig):
        print("⚠️ 原件不在盘：%s" % orig.replace(HOME, "~"))
        print("   若它已改名/移走，请手工指定目标；本件⛔不猜。")
        return 1
    if dry:
        print("[dry] 将 %s ← %s" % (orig.replace(HOME, "~"), src.replace(HOME, "~")))
        return 0
    # 回滚前先备份当前版（回滚本身也可回滚——不留单向门）
    cur_dir = os.path.join(AMBER, "系统日志备份", time.strftime("%Y-%m-%d"))
    os.makedirs(cur_dir, exist_ok=True)
    cur_bak = os.path.join(
        cur_dir, "%s.bak-%s" % (os.path.basename(orig),
                                time.strftime("%H%M%S_%f")))
    shutil.copy2(orig, cur_bak)
    shutil.copy2(src, orig)
    print("✅ 已回滚：%s" % orig.replace(HOME, "~"))
    print("   回滚前版本已存：%s" % cur_bak.replace(HOME, "~"))
    return 0


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    act, rest = a[0], a[1:]
    kw = rest[0] if rest else ""
    idx = 1
    if "--index" in rest:
        try:
            idx = int(rest[rest.index("--index") + 1])
        except (IndexError, ValueError):
            print("⚠️ --index 需要一个整数")
            return 1
    if act == "list":
        return cmd_list(kw)
    if act == "show":
        return cmd_show(kw, idx)
    if act == "rollback":
        return cmd_rollback(kw, idx, dry="--dry" in rest, rest=rest)
    if act == "find":
        return cmd_list(kw)
    print("未知动作：%s（list/show/rollback/find）" % act)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as _e:                      # ⛔ 任何异常都给兜底，不吞
        print("⚠️ 命令自身异常：%s" % _e)
        print("兜底（可直接粘进终端）：")
        print("  " + (FALLBACK % ""))
        sys.exit(1)
