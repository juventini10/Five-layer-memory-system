#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: family=包自检器 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
"""
slice_chain_check.py — 包自检 ⑬「数字分身·恒驻切片链 dry-run」（2026-10-11 增设）

为什么存在
----------
皮叔 2026-10-11 质证：包自检⑫（twin_chain_check）只测**卡链路**（抽卡→落卡→碰撞），
**切片链**（规格书→生成器→六片→各端恒驻核）在装机验收面零动态覆盖——包内仅静态查
生成器文件在不在（verify.ps1 L213），恒驻核存在性检查在 TIML（每月1号跑），都不是
「装完即检」⇒「装了分身但切片链是断的」在装机时刻不可见。与⑫建检动机同构
（2026-09-30「装了但链路断在自检里不可见」），本件补上切片链这一腿。

判据（在**隔离沙箱**里跑真生成链·⛔不触碰用户真实规格书/切片目录/任何端恒驻文件）
--------------------------------------------------------------------------------
1. 沙箱=临时目录复刻「数字分身/」相对结构：
   复制包内 references/digital-twin/k2-slice-generator/k2_slice_generator.py 与
   onboarding/童灵·人格规格书-骨架模板.md（改名 童灵·人格规格书.md）
   ⇒ 生成器自推导 BASE/SPEC/OUT 全落沙箱内（脚本路径口径·零绝对路径依赖）。
2. 断言逐步要求全真：
   ① 生成器 rc==0
   ② 六片产出齐全且非空（core_slice.md + L2..L6 五片·文件名按 slug 前缀匹配）
   ③ manifest.json 存在 · src_hash 12位hex · slices 计数==6
   ④ 骨架未填态必显形「待填占位」（空壳也能六片齐但须警告"还不像他"——
      断言显形机制活着，这是装机者对「分身像不像我」的唯一诚实信号）
   ⑤ core_slice.md 含 L1 节头且含运行时注入声明节头（提取正确性·非空壳）
3. 沙箱 finally 清理。

⛔ 脱敏免疫：本件正文不写任何私人标识字面量（同⑫纪律）。
☑ 平台中性：纯标准库，Win/mac/Linux 同码可跑（Win UTF-8 子环境加固照⑫先例）。

用法
----
    python3 slice_chain_check.py --pkg-root <包根> [--quiet]
退出码：0=五断言全过  1=切片链断（明细见输出）  2=参数错误  3=包结构缺件（生成器/模板不在包内）
"""
# Win console UTF-8 guard (same recipe as twin_chain_check precedent)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

GEN_REL = os.path.join("references", "digital-twin", "k2-slice-generator", "k2_slice_generator.py")
TPL_REL = os.path.join("references", "digital-twin", "onboarding", "童灵·人格规格书-骨架模板.md")
SPEC_NAME = "童灵·人格规格书.md"
LAYERS = ["core_slice", "L2_", "L3_", "L4_", "L5_", "L6_"]


def _child_env():
    """Windows 子进程 UTF-8 加固（沿⑫先例：cp1252 控制台中文 print 崩→强制 utf-8）。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def run_check(pkg_root, quiet=False):
    def say(msg):
        if not quiet:
            print(msg)

    gen_src = os.path.join(pkg_root, GEN_REL)
    tpl_src = os.path.join(pkg_root, TPL_REL)
    if not (os.path.isfile(gen_src) and os.path.isfile(tpl_src)):
        missing = [p for p in (gen_src, tpl_src) if not os.path.isfile(p)]
        print("❌ 包结构缺件（切片链无源可跑）: %s" % "; ".join(missing))
        return 3

    fails = []
    tmp = tempfile.mkdtemp(prefix="slice_chain_check_")
    try:
        # 复刻「数字分身/」相对结构（沙箱内自推导路径·⛔不落真实档案）
        twin = os.path.join(tmp, "数字分身")
        os.makedirs(os.path.join(twin, "k2-slice-generator"))
        shutil.copy2(gen_src, os.path.join(twin, "k2-slice-generator", "k2_slice_generator.py"))
        shutil.copy2(tpl_src, os.path.join(twin, SPEC_NAME))

        # ① 生成器 rc==0
        r = subprocess.run([sys.executable,
                            os.path.join(twin, "k2-slice-generator", "k2_slice_generator.py")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60, env=_child_env())  # 批次9: 父进程读管道也须UTF-8——子进程已utf-8但父按locale(cp1252)解码=UnicodeDecodeError崩读者(真机实证run38098363933)
        if r.returncode != 0:
            print("❌ ① 生成器 rc=%s（链断）stderr=%s" % (r.returncode, (r.stderr or "")[:300]))
            return 1
        say("✅ ① 生成器 rc=0（沙箱内规格书→切片跑通）")

        sdir = os.path.join(twin, "K2切片蒸馏", "slices")
        files = os.listdir(sdir) if os.path.isdir(sdir) else []

        # ② 六片齐全且非空
        miss, empty = [], []
        for pat in LAYERS:
            hit = [f for f in files if f.startswith(pat) and f.endswith(".md")]
            if not hit:
                miss.append(pat)
            elif all(os.path.getsize(os.path.join(sdir, f)) == 0 for f in hit):
                empty.append(pat)
        if miss or empty:
            fails.append("② 六片不齐: 缺%s 空%s" % (miss or "无", empty or "无"))
        else:
            say("✅ ② 六片产出齐全非空（core+L2..L6）")

        # ③ manifest 健康
        mpath = os.path.join(sdir, "manifest.json")
        if not os.path.isfile(mpath):
            fails.append("③ manifest.json 缺失")
        else:
            man = json.load(open(mpath, encoding="utf-8"))
            if not re.fullmatch(r"[0-9a-f]{12}", str(man.get("src_hash", ""))):
                fails.append("③ manifest.src_hash 非12位hex")
            elif len(man.get("slices", [])) != 6:
                fails.append("③ manifest.slices 计数=%s≠6" % len(man.get("slices", [])))
            else:
                say("✅ ③ manifest src_hash=%s · slices=6" % man["src_hash"])

        # ④ 待填占位显形（骨架未填态的唯一诚实信号，机制必须活着）
        if "待填占位" not in (r.stdout or ""):
            fails.append("④ 待填占位显形未输出（装机者将误以为一次填满=假像风险）")
        else:
            say("✅ ④ 待填占位显形在位（「还不像他」诚实信号可用）")

        # ⑤ core 提取正确性（注入声明+L1 两节头必须在，非截空壳）
        cpath = os.path.join(sdir, "core_slice.md")
        ctxt = open(cpath, encoding="utf-8").read() if os.path.isfile(cpath) else ""
        if not ("运行时注入声明" in ctxt and re.search(r"^## L1 · ", ctxt, re.M)):
            fails.append("⑤ core_slice 缺注入声明/L1 节头（提取正则与规格书结构脱钩）")
        else:
            say("✅ ⑤ core 含注入声明+L1 节（提取正确）")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        for f in fails:
            print("❌ " + f)
        print("切片链自检未过（%d 断言红）→ 装机的分身恒驻核不会随规格书更新，链路须先修" % len(fails))
        return 1
    say("🟢 切片链 dry-run 五断言全过——装完即可证明：规格书骨架能蒸出六片、manifest/显形/core 提取全健康")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg-root", required=True)
    ap.add_argument("--quiet", action="store_true", help="只输出总判定（供 verify 内嵌调用）")
    args = ap.parse_args()
    root = os.path.expanduser(args.pkg_root)
    if not os.path.isdir(root):
        print("参数错误：包根不存在 %s" % root)
        return 2
    return run_check(root, args.quiet)


if __name__ == "__main__":
    sys.exit(main() or 0)
