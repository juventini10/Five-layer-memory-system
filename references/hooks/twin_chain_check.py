#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
twin_chain_check.py — 发包自检 ⑫「数字分身·卡链路三步 dry-run」（2026-09-30 终检·件4 收官）

为什么存在
----------
数字分身完整版单装（Phase B）交付「每日伙伴抽卡 → 好好学习落卡 → 碰撞」链路。
设计定稿要求终检覆盖：`抽卡 → 落卡 → 碰撞 三步 dry-run 全绿`（真源=自定义层/待完成工作/
数字分身完整版-安装流程设计-20260929.md §二·终检行）。
原 verify.sh 六项（数据污染/系统文件/规则三层/记忆Skill/干净度/版本锚点）**零覆盖**该链路
⇒ 「装了但链路断」在自检里不可见（同族：装了没装都不报）。

判据（在**隔离沙箱**里跑真链路·⛔不触碰用户真实卡库）
------------------------------------------------------
1. 沙箱 = 临时目录内造 `脚本中心/知识联邦引擎/scripts/`（复制**包内** references/知识联邦引擎-min/scripts）
   ⇒ `_paths.py` 自推导 MC=沙箱根 ⇒ 全程只在沙箱内读写。
2. 播种一张中性示例卡（`立场卡#S001-示例主题.md`·design §四「示例卡一律占位」口径）
   ⇒ 让「落卡」步有真对象（空库时 regen 本就 rc=1·无法区分「链路断」与「无数据」）。
3. 顺序执行并**逐步要求 exit 0**：
   ① 抽卡 `extract_concepts.py prepare`
   ② 落卡 `regen_ailib_index.py`（并校验 INDEX.md 真被写出）
   ③ 碰撞 `collision_scan.py status`（语义增强可选·无模型时降级态亦须 exit 0）
4. 沙箱 finally 清理。

⛔ 不测 `collision_scan.py scan`（需 bge 模型 ~600MB·可选件·属 Phase C）——只用 status
   证明碰撞件可加载可运行（降级态不崩）。
⛔ 脱敏免疫：本件正文不写任何私人标识字面量（示例卡名用 design 规定的中性占位）。

用法
----
    python3 twin_chain_check.py --pkg-root <包根> [--memory-center <MC>] [--quiet]
    --quiet  只输出总判定（供 verify 脚本内嵌调用）
退出码：0=三步全绿  1=链路断  2=参数错误  3=包内引擎-min 缺失（包结构缺陷）
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ENGINE_REL = os.path.join("references", "知识联邦引擎-min", "scripts")

# 中性示例卡（design §四：示例一律 `立场卡#S001-示例主题.md` 式占位）
SEED_CARD_NAME = "立场卡#S001-示例主题.md"
SEED_CARD_BODY = """---
card_id: 立场卡#S001
topic: 示例主题
type: 立场卡
领域分诊: 通用
reading_status: L1
date: 2026-01-01
---

# 示例主题

中性示例卡（自检沙箱播种·非真实数据）。
"""


def _child_env():
    """Windows 子进程 UTF-8 加固（2026-10-07 clock-loop 真机反哺）：子脚本中文 print
    在 cp1252 控制台下 UnicodeEncodeError 崩溃 ⇒ 透传 UTF-8 环境强制走 utf-8 编码。"""
    import os as _os
    e = dict(_os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def _run(py: str, script: str, cwd: str):
    """返回 (rc, 合并输出尾部)。"""
    try:
        p = subprocess.run([py, script], cwd=cwd, capture_output=True, text=True,
                           timeout=180, env=_child_env(), encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT(180s)"
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def main():
    ap = argparse.ArgumentParser(description="数字分身卡链路三步 dry-run 自检（隔离沙箱·只读包）")
    ap.add_argument("--pkg-root", default=os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), help="安装包根目录")
    ap.add_argument("--memory-center", default="", help="记忆共享中心（仅用于提示安装态·不参与判据）")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    pkg = os.path.abspath(os.path.expanduser(a.pkg_root))
    eng_src = os.path.join(pkg, ENGINE_REL)
    py = sys.executable

    def say(msg):
        if not a.quiet:
            print(msg)

    if not os.path.isdir(eng_src):
        print(f"  [FAIL] 分身链路: 包内引擎缺失（{ENGINE_REL}）——包结构缺陷")
        return 3

    tmp = tempfile.mkdtemp(prefix="twin-chain-")
    try:
        eng_dst = os.path.join(tmp, "脚本中心", "知识联邦引擎")
        os.makedirs(eng_dst, exist_ok=True)
        shutil.copytree(eng_src, os.path.join(eng_dst, "scripts"), dirs_exist_ok=True)

        # 沙箱布局：安装态判定依赖「脚本中心」祖先（见 _paths.py）；卡库落 知识库/AI学习库/
        ailib = os.path.join(tmp, "知识库", "AI学习库")
        os.makedirs(ailib, exist_ok=True)
        with open(os.path.join(ailib, SEED_CARD_NAME), "w", encoding="utf-8") as f:
            f.write(SEED_CARD_BODY)

        scripts = os.path.join(eng_dst, "scripts")
        steps = [
            ("抽卡", os.path.join(scripts, "extract_concepts.py"), ["prepare"]),
            ("落卡", os.path.join(scripts, "regen_ailib_index.py"), []),
            ("碰撞", os.path.join(scripts, "collision_scan.py"), ["status"]),
        ]
        failed = None
        for label, script, extra in steps:
            if not os.path.exists(script):
                failed = (label, 3, "脚本缺失")
                break
            try:
                p = subprocess.run([py, script] + extra, cwd=scripts,
                                   capture_output=True, text=True, timeout=180,
                                   env=_child_env(), encoding="utf-8", errors="replace")
                rc = p.returncode
                tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()[-2:]
            except subprocess.TimeoutExpired:
                rc, tail = 124, ["TIMEOUT(180s)"]
            say(f"       · {label}: rc={rc}  {' | '.join(tail)[:110]}")
            if rc != 0:
                failed = (label, rc, " | ".join(tail)[:160])
                break

        # 落卡真产出校验（防「rc=0 但没写 INDEX」）
        if not failed:
            idx = os.path.join(ailib, "INDEX.md")
            if not (os.path.exists(idx) and os.path.getsize(idx) > 0):
                failed = ("落卡产出", 1, f"INDEX.md 未生成（{idx}）")

        if failed:
            label, rc, detail = failed
            print(f"  [FAIL] 分身链路: 三步 dry-run 未全绿（{label} rc={rc}·{detail}）")
            return 1

        print("  [PASS] 分身链路: 抽卡→落卡→碰撞 三步 dry-run 全绿（隔离沙箱·零触真实卡库）")
        if a.memory_center:
            inst = os.path.join(os.path.expanduser(a.memory_center),
                                "脚本中心", "知识联邦引擎", "scripts")
            if not os.path.isdir(inst):
                say("       ℹ️ 本机尚未装卡引擎（Phase B）——装后此链路即在你的记忆中心可用")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
