#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/install_script_center.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
# version: v0.1
"""
install_script_center.py — 布洛陀「安装脚本体系」命令（端用户/作者通用·跨平台·幂等·脱敏·装完即用）

第一性原理定位
--------------
单一物理副本(虚拟归拢) → 安装=侦探式补齐缺口 + 幂等覆盖 + 跨平台过滤 + 脱敏 + 动态路径解析。
不破坏已有部署：源未变→跳过；源更新→备份旧版再覆盖；本地被改但源未变→保护不覆盖。

关键不变量
----------
1. 脱敏接通：复制即跑 deident_rules.deident()（优先复用发布管线 SSOT，否则内联最小集兜底）。
   规则：~/ → ~/ 、你→用户、用户名→用户名、某友人分叉→某友人分叉。
2. 动态路径解析：脚本内 `[记忆共享中心]/<dir>/` 互调引用 → `<root>/<dir>/`（root=安装位置）。
   使端用户机器上脚本间互调指向其 脚本中心，而非作者家目录。
3. 跨平台过滤：Windows 跳过无 win_entry 的 .sh（无 bash 入口）。.py 跨平台。
4. 幂等台账：install_ledger.json 记录每条的【源 sha】。重跑以源 sha 是否变化为准——
   因脱敏/重写后 dst 与源内容必然不同，绝不能比 dst 与源的内容（否则永远判"不同"）。
5. 装完即用（缺口①）：--wire-hooks 精确改写端用户 WB settings.json 中属于本清单的 Hook 命令路径，
   使其指向脚本中心；幂等(已指向则跳过) + 备份 + dry-run 安全 + JSON 校验。
   仅锚定 manifest 条目对应的 `个人AI档案/<target_rel>` 后缀，绝不整串替换，
   故 数字分身/知识联邦/.workbuddy/hooks 等不在清单内的引用一字不碰。
   非破坏兜底：始终生成 adapters/workbuddy-hooks.snippet.json（paste-ready 片段）供手动合并。

用法
----
  python3 install_script_center.py                                  # 装到默认 [记忆共享中心]/脚本中心
  python3 install_script_center.py --root ~/记忆共享中心/脚本中心   # 指定安装位置
  python3 install_script_center.py --dry-run                        # 只打印动作不写文件
  python3 install_script_center.py --force                          # 强制重装(忽略源sha, 覆盖所有)
  python3 install_script_center.py --wire-hooks                     # 装完自动改写 WB hook 指向脚本中心
  python3 install_script_center.py --settings-path ~/.workbuddy/settings.json --wire-hooks --dry-run

前置：本文件须与 scripts_manifest.json 同目录（安装包自带 registry，或作者开发工具/）。

安全提示：wire-hooks 默认关闭（opt-in）。作者本机 SSOT 为 [记忆共享中心]/脚本中心，hook 已正确指向；
端用户才需 --wire-hooks。开启后会先备份 settings.json 再改写。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import json
import shutil
import hashlib
import argparse
import platform

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "scripts_manifest.json")

# B修源·声明驱动口径v2(2026-10-05·L2裁定键20261005_185920·条文47)：
# 根唯一来源=runtime_paths 声明(作者机=runtime_paths.py build / 用户机=安装器生成)；
# ⛔消费侧默认兜底已删——默认值散落=根决定权旁落到每个脚本=唯一真源在运行期的反转。
# 无声明 hard fail(DeclNotFound 消息自带 bootstrap 指引=错误即教育)。
# ⚠️ 用 realpath 父目录非 HERE：本件有软链入口（开发工具/），abspath 不解析软链
#    会致 runtime_paths 从软链目录加载、按其自邻找声明而错位（2026-10-05 三验实抓）
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from runtime_paths import rp
_ARCHIVE_ROOT = rp("archive_root")


def sha8_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()[:8]


def load_deident():
    """优先复用发布管线脱敏(SSOT)，否则内联最小集兜底（与 deident_rules 同步）。"""
    cand = os.path.join(HERE, "buluotuo-release-sync", "deident_rules.py")
    if os.path.exists(cand):
        sys.path.insert(0, os.path.dirname(cand))
        try:
            import deident_rules  # type: ignore
            return deident_rules.deident
        except Exception:
            pass
    HOME = os.path.expanduser("~")

    def deident(text: str, rel_path: str = "") -> str:
        out = text.replace(HOME + "/", "~/")
        out = re.sub(r"你", "用户", out)
        out = re.sub(r"用户名", "用户名", out)
        out = re.sub(r"某友人分叉", "某友人分叉", out)
        return out

    return deident


def _hook_event_of(e: dict) -> str:
    """取该条目的 Hook 事件名（event 优先，否则 events[0]）。"""
    ev = e.get("event")
    if ev:
        return ev
    evs = e.get("events") or []
    return evs[0] if evs else ""


def wire_hooks(settings_path: str, entries: list, root_abs: str, dry_run: bool):
    """缺口①：精确改写 WB settings.json 中属于本清单的 Hook 命令路径 → root_abs。

    不整串替换：仅对每条 deployed_wb 脚本，用正则锚定 `个人AI档案/<target_rel>` 后缀，
    把其前面的任意基准目录(<base>/个人AI档案/)替换为 root_abs，绝不碰 数字分身/知识联邦/.workbuddy 等不在清单的路径。
    幂等：若命令已指向 root_abs 则跳过。备份 + JSON 校验 + dry-run 安全。
    返回 (changed_list[(name,old,new)], skipped_list[(name,reason)])
    """
    if not os.path.exists(settings_path):
        return ([("SETTINGS_MISSING", settings_path, "")], [])
    try:
        with open(settings_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as ex:
        print(f"  ⚠️ settings.json 解析失败, 跳过 wire-hooks: {ex}", file=sys.stderr)
        return ([("SETTINGS_PARSE_ERR", str(ex), "")], [])

    hooks = cfg.get("hooks")
    if not isinstance(hooks, dict):
        return ([("NO_HOOKS_BLOCK", settings_path, "")], [])

    root_slash = root_abs.rstrip("/") + "/"
    # 仅处理 deployed_wb 且路径在 个人AI档案/ 下的条目
    repls = []  # (event, target_rel, new_abs)
    for e in entries:
        if not e.get("deployed_wb"):
            continue
        rel = e.get("path", "")
        if not rel.startswith("个人AI档案/"):
            continue
        target_rel = center_rel(rel)
        new_abs = root_slash + target_rel
        ev = _hook_event_of(e)
        if not ev:
            continue
        repls.append((ev, target_rel, new_abs))

    changed = []
    skipped = []
    new_cfg = json.loads(json.dumps(cfg))  # 深拷贝，避免污染入参
    for ev, target_rel, new_abs in repls:
        block = new_cfg.get("hooks", {}).get(ev)
        if not isinstance(block, list):
            continue
        base = os.path.basename(target_rel)
        for item in block:
            cmd = item.get("command", "")
            if not isinstance(cmd, str):
                continue
            if new_abs in cmd:
                skipped.append((base, "已指向 root_abs"))
                continue
            # 锚定 .../个人AI档案/<target_rel>（前面任意基准目录被整体替换）
            pat = re.compile(
                r'(?P<q>[\'"]?)(?P<lead>.+?/)个人AI档案/'
                + re.escape(target_rel)
                + r'(?P<tail>[\'"\s]|$)'
            )
            if not pat.search(cmd):
                continue  # 该 hook 未引用此脚本 → 不碰
            new_cmd = pat.sub(lambda m: m.group("q") + new_abs + m.group("tail"), cmd)
            if new_cmd != cmd:
                item["command"] = new_cmd
                changed.append((base, cmd.strip(), new_cmd.strip()))

    if dry_run:
        return (changed, skipped)

    # 写回：先备份 + JSON 校验
    if changed:
        backup = settings_path + ".bak"
        try:
            json.dumps(new_cfg)  # 校验可序列化
        except Exception as ex:
            print(f"  ⚠️ 改写后 JSON 校验失败, 不写入: {ex}", file=sys.stderr)
            return (changed, skipped)
        shutil.copy2(settings_path, backup)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(new_cfg, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return (changed, skipped)


def gen_snippet(entries: list, root_abs: str) -> dict:
    """生成 paste-ready 的 hooks 片段（仅 deployed_wb 且 Hook 形态）。非破坏兜底用。"""
    root_slash = root_abs.rstrip("/") + "/"
    hooks: dict = {}
    for e in entries:
        if not e.get("deployed_wb"):
            continue
        rel = e.get("path", "")
        if not rel.startswith("个人AI档案/"):
            continue
        target_rel = center_rel(rel)
        ev = _hook_event_of(e)
        if not ev:
            continue
        new_abs = root_slash + target_rel
        hooks.setdefault(ev, []).append({"command": f"python3 {new_abs} {ev}"})
    return {"hooks": hooks}



# 2026-10-05 落点规则修正（影子树根因）：部署根（默认=脚本中心）本身即 开发工具/脚本中心 两区的等价根，
#   再拼一次区段名 ⇒ 每次装机都造出 `脚本中心/开发工具/`（干净沙箱实测 71 件·10-04 trash 过又长回来）。
#   其余区段（自定义层/数字分身/记忆蓝图）保留区段——根≠该区，剥掉会撞名且丢归属。
#   四处同源写法（wire_hooks/gen_snippet/装机/前缀重写）一并走 center_rel，⛔只改一处=留下一套语义。
CENTER_SEGS = ("开发工具", "脚本中心")


def center_rel(rel):
    r = rel[len("个人AI档案/"):] if rel.startswith("个人AI档案/") else rel
    seg = r.split("/")[0]
    if seg in CENTER_SEGS:
        return r[len(seg) + 1:] if len(r) > len(seg) + 1 else ""
    return r


def main():
    ap = argparse.ArgumentParser(description="布洛陀 安装脚本体系（幂等·跨平台·脱敏·装完即用）")
    ap.add_argument("--root", default=os.path.join(_ARCHIVE_ROOT, "脚本中心"),
                    help="安装位置（默认=声明 archive_root/脚本中心；无声明 hard fail）")
    ap.add_argument("--source-base", default=os.path.dirname(_ARCHIVE_ROOT),
                    help="manifest 路径基准（默认=声明根的父目录；条目路径带 个人AI档案/ 前缀系 manifest schema 说明）")
    ap.add_argument("--settings-path", default=os.path.join(os.path.expanduser("~"), ".workbuddy", "settings.json"),
                    help="WB settings.json 路径（wire-hooks 用；默认 ~/.workbuddy/settings.json）")
    ap.add_argument("--dry-run", action="store_true", help="只打印动作，不写任何文件")
    ap.add_argument("--force", action="store_true", help="强制重装(忽略源sha, 覆盖所有)")
    ap.add_argument("--wire-hooks", action="store_true",
                    help="装完自动改写 WB settings.json 中本清单 Hook 命令指向脚本中心（默认关闭·opt-in）")
    args = ap.parse_args()

    if not os.path.exists(MANIFEST):
        print(f"❌ 找不到 registry: {MANIFEST}", file=sys.stderr)
        sys.exit(1)

    deident = load_deident()
    is_win = (os.name == "nt") or (platform.system() == "Windows")
    with open(MANIFEST, encoding="utf-8") as f:
        mdata = json.load(f)
    entries = mdata["scripts"]

    # 派生可重写前缀：每个 manifest 条目的父目录（去 个人AI档案/ 前缀）
    prefixes = set()
    for e in entries:
        p = e.get("path", "")
        if not p.startswith("个人AI档案/"):
            continue
        d = os.path.dirname(p)
        prefixes.add(d)
        # 2026-09-17 童灵根治：运行时状态目录（.guard/ .patrol/ .snapshots/ 配置 json）与脚本同族
        # 但**不在 scripts/ 之下**，引用形式为 `[记忆共享中心]/<族根>/.guard/...` ⇒ 仅有一级 dirname
        # 前缀不命中重写 → 端用户盘上会按旧绝对路径 mkdir 出**作者侧目录结构**（实测 6 件在册硬依赖）。
        # 补「直接父级」一级覆盖。⛔不加 `个人AI档案` 本身——那会把 `[记忆共享中心]/<任意>` 整体
        # 重写到脚本中心，误伤记忆中心文件（变更日志/自定义层 USER.md 等）。
        parent = os.path.dirname(d)
        if parent.startswith("个人AI档案/") and parent != os.path.expanduser("~"):
            prefixes.add(parent)

    root_abs = os.path.abspath(os.path.expanduser(args.root))
    base_abs = os.path.abspath(os.path.expanduser(args.source_base))
    ledger_path = os.path.join(root_abs, "install_ledger.json")

    # 上轮台账：以【源 sha】判等（脱敏/重写后 dst≠源内容，绝不能比内容）
    prev_sha = {}
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, encoding="utf-8") as f:
                prev_sha = json.load(f).get("source_sha", {})
        except Exception:
            prev_sha = {}

    # 继承上轮 source_sha（跳过类条目自带保真，避免台账被清空导致重跑全量"更新"）
    ledger = {"source_sha": dict(prev_sha), "installed": [], "updated": [],
              "skipped_same": [], "skipped_missing": [], "cross_platform_skipped": [],
              "skipped_scope": []}

    for e in entries:
        name = e["name"]
        rel = e.get("path", "")
        src = os.path.join(base_abs, rel)
        if not os.path.exists(src):
            ledger["skipped_missing"].append((name, "源缺失(可能其他端专属)"))
            continue
        ext = os.path.splitext(name)[1].lower()
        if is_win and ext == ".sh" and not e.get("win_entry"):
            ledger["cross_platform_skipped"].append((name, "Win 无 .ps1 入口, 跳过 .sh"))
            continue

        if not e.get("in_package", True):
            ledger["skipped_scope"].append((name, "出包范围外(锁定 scope)"))
            continue

        target_rel = center_rel(rel)
        dst = os.path.join(root_abs, target_rel)

        with open(src, encoding="utf-8", errors="replace") as f:
            text = f.read()
        text = deident(text, rel)
        # 长前缀优先：短前缀先替换会把长前缀的尾巴吃掉（2026-09-17 童灵）
        # 形态覆盖 ①`[记忆共享中心]/<d>` ②`[记忆共享中心]/<d>` ③`[记忆共享中心]/<d>`
        # （shell 变量式——实证 route_*_patrol.sh 的 KB_SCRIPTS 用 $HOME/ 形式，只认 `~/` 会漏）
        for d in sorted(prefixes, key=len, reverse=True):
            repl = (os.path.join(root_abs, center_rel(d)) or root_abs).replace("\\", "/")
            for form in ("~/" + d, "$HOME/" + d, "${HOME}/" + d):
                f = form.replace("\\", "/")
                if f in text:
                    text = text.replace(f + "/", repl + "/")
        # 二级：不带 `~/` 的纯字面量形式 —— os.path.join(os.path.expanduser("[记忆共享中心]"), "<族根>") 拼接式
        # （实证 3 件在册硬依赖 route_feedback_collector / route_guard_audit / route_miss_feeder
        #  均用 HOME 拼接，一级 `~/` 前缀替换不命中）→ 端用户侧仍指向作者家目录。
        # 前缀均为**具体族根**（非泛化 `个人AI档案`），裸替换语义安全：脚本即装在同名相对路径下。
        for d in sorted(prefixes, key=len, reverse=True):
            if d in text:
                repl2 = (os.path.join(root_abs, center_rel(d)) or root_abs).replace("\\", "/")
                text = text.replace(d, repl2)

        src_sha = sha8_of_file(src)
        action = None
        if name in prev_sha and not args.force:
            if prev_sha[name] == src_sha:
                ledger["skipped_same"].append((name, "源未变, 已装"))
                continue
            # 源已更新 → 备份旧版再覆盖
            if os.path.exists(dst):
                shutil.copy2(dst, dst + ".bak")
            action = "updated"
        else:
            action = "updated" if os.path.exists(dst) else "installed"

        if args.dry_run:
            ledger[action].append((name, "DRY-RUN"))
            ledger["source_sha"][name] = src_sha
            continue

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(text)
        ledger[action].append((name, dst))
        ledger["source_sha"][name] = src_sha

    # ── wire-hooks（缺口①：装完即用·不靠人记得）──
    if args.wire_hooks:
        print("\n--- wire-hooks (WB settings.json 改写) ---")
        ch, sk = wire_hooks(args.settings_path, entries, root_abs, args.dry_run)
        if args.dry_run:
            for n, old, new in ch:
                print(f"  [将改写] {n}\n     - {old}\n     + {new}")
            for n, r in sk:
                print(f"  [跳过] {n}: {r}")
            print("  (dry-run: 未写入 settings.json)")
        else:
            for n, old, new in ch:
                print(f"  [已改写] {n}")
            for n, r in sk:
                print(f"  [跳过] {n}: {r}")
            if ch:
                print(f"  备份: {args.settings_path}.bak")

    # ── snippet（非破坏·paste-ready 兜底）──
    snippet = gen_snippet(entries, root_abs)
    if snippet.get("hooks"):
        if args.dry_run:
            print(f"\n  💡 [dry-run] 将生成 paste-ready 片段: {os.path.join(root_abs, 'adapters', 'workbuddy-hooks.snippet.json')}")
        else:
            adir = os.path.join(root_abs, "adapters")
            os.makedirs(adir, exist_ok=True)
            sp = os.path.join(adir, "workbuddy-hooks.snippet.json")
            with open(sp, "w", encoding="utf-8") as f:
                json.dump(snippet, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"\n  💡 首次使用片段(手动合并到 hooks 块): {sp}")

    # ── 报告 ──
    print("=== 安装脚本体系 报告 ===")
    print(f"目标(root): {root_abs}")
    print(f"平台: {'Windows' if is_win else 'Unix/macOS'}")
    print(f"[安装] {len(ledger['installed'])}  "
          f"[更新] {len(ledger['updated'])}  "
          f"[跳过·源未变] {len(ledger['skipped_same'])}  "
          f"[跳过·源缺失] {len(ledger['skipped_missing'])}  "
          f"[跨平台跳过] {len(ledger['cross_platform_skipped'])}  "
          f"[出包跳过] {len(ledger['skipped_scope'])}")
    if ledger["cross_platform_skipped"]:
        print("  跨平台跳过明细:")
        for n, r in ledger["cross_platform_skipped"]:
            print(f"    - {n}: {r}")
    if args.dry_run:
        print("(dry-run: 未写入任何文件)")
    else:
        os.makedirs(root_abs, exist_ok=True)
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, ensure_ascii=False, indent=2)
        print(f"台账: {ledger_path}")


if __name__ == "__main__":
    main()
