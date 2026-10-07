#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/verifier_target_fidelity_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
r"""verifier_target_fidelity_guard.py — 验证器保真度守卫（Hermes 端 · 2026-10-03 立）

═══ 病根（第一性原理取证 · 非推测）═══
2026-10-03 用户连问三轮「这个数字分身的启动逻辑到底怎么回事」，根因链：
  ① `runtime_paths.json` 的 `devtools` 指向 `脚本中心/`，注入器真跑那一份；
  ② 布洛陀脚本族历史上散落 `脚本中心/` 与 `开发工具/` 两处，**无同步机制**；
  ③ `doenglingz_inject_prompt.py` 只在 `开发工具/` ⇒ 注入器每轮静默 fail-open
     （插件日志 `inject empty rc=2` 从 10-02 21:45 连报 21 次 / 10:01:30）；
  ④ 注入器停摆 ⇒ AI 拿不到档位判据 ⇒ **自己顶位宣布「D3 上岗」**（假绿：行为看着仍合规）。

═══ 本守卫治的是更深一层 ═══
④ 修好之后仍留下一类**结构性假绿**：**验证器验证的不是运行的那份**。
实测（2026-10-03）：`数字分身/scripts/d_tier_exclusivity_dryrun.py` 的
`TARGET = [记忆共享中心]/脚本中心/doenglingz_inject_prompt.py`（**旧件·无修复**），
而真跑件是 `脚本中心/doenglingz_inject_prompt.py`（**有修复**）——两件 sha256 不同。
该回归器报 `12/12 过 · ✅ 全过`。加入病句断言后实测：
  · 指向旧件 → 病句判 **D3** ❌
  · 指向真跑件 → 病句判 **D2** ❌（W1 已修好·但 W3 裸高频词仍误召）
**两份都不对，而回归器两次都报全绿**——绿灯与运行态零关联。

═══ 判据（三条 · 全机械可跑 · 全绿才放行）═══
  ① **路径保真**：每个验证器的脚本 TARGET 必须解析自 `runtime_paths`，
     ⛔ 不得硬编码 `开发工具/` 或任何绝对脚本目录（键名/日志目录不在此列）。
  ② **内容保真**：验证器实测的脚本件 sha256 == `runtime_paths.devtools` 下同名件 sha256。
     ⛔ 不同即为「测了另一份」——即使它自己报全绿。
  ③ **断言覆盖**：档位类判据（否定语境/档位互斥）必须在回归器 CASES 里有真阴性断言；
     ⛔ 「全绿但无该断言」= 未覆盖，不等于通过。

═══ 能力边界（如实声明 · 2026-10-03 负控实测）═══
  · 变异①「验证器 TARGET 退回硬编码旧目录」→ **rc=1 逮住** ✅
  · 变异②「删掉否定语境真阴性断言」        → **rc=1 逮住** ✅
  · 变异③「给真跑件加一行（两份一起变）」  → **rc=0 抓不到** ⛔
    原因：内容保真判据比较的是「验证器实测件」与「运行目录同名件」的 sha256；
    当两者本就是同一份文件时，二者同步变化 ⇒ 无从区分。
    ⛔ 这是本守卫的**已知盲区**，不是通过。治它需要「运行实例加载时的 sha 留痕」
    （即 hook 侧记 inject_sha + 验证器记被测件 sha，二者对账）——属独立改造项，
    本轮未做，按最小方案原则不擅自扩范围。

═══ 为什么必须是守卫而不是改一次 ═══
一次性修 = 下一个新写的验证器照样硬编码。按铁律-016（审计权威源=实盘·⛔不信文字）
与通用规范「机制优于自觉」，路径纪律必须**可机械检出**，否则靠自觉必熵减。

出口：rc=0 全绿 / rc=1 有缺口（逐条列出文件:行 + 修法）
用法：python3 verifier_target_fidelity_guard.py [--json]
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

HOME = os.path.expanduser("~")
ARCHIVE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")  # 2026-10-04 修：第二参被脱敏批删空 ⇒ rp 取址全退化为家目录（本守卫专管回归器 TARGET 保真，自己带 A 型病灶）
RUNTIME_PATHS = os.path.join(HOME, ".hermes", "doenglingz", "runtime_paths.json")

# 扫描面：一切可能验证档位/触发词/注入行为的 .py
SCAN_ROOTS = [
    os.path.join(ARCHIVE, "数字分身", "scripts"),
    os.path.join(ARCHIVE, "脚本中心"),
    os.path.expanduser(os.path.join(HOME, ".hermes", "plugins")),
]
# 被验证的脚本名（决定一个文件「是不是验证器」）
TARGET_SCRIPTS = (
    "doenglingz_inject_prompt.py", "doenglingz_guard.py", "doenglingz_level_declare_guard.py",
    "gate_runner.py", "tsl_verify.py", "twin_verdict_ledger.py",
    "guard_registry_check.py", "twin_changelog_guard.py",
)
# 允许硬编码的目录角色：日志/账本落点（不是被测脚本）
NON_TARGET_DIRS = ("logs", "log", "账本", "ledger", "heartbeat", "changelog-guard")
# 档位判据的关键否定语境（判据③用）
NEGATION_PROBES = (
    "我没有启动童灵",              # 10-01 用户质证原判例
    "我不是在启动童灵",            # 10-03 扩窗病句（否定与动作间有助词）
    "这一轮的对话我没有启动童灵啊",  # 10-01 原判例完整句
)

RE_TARGET = re.compile(
    r"""expanduser\(\s*['"]([^'"]*(?:开发工具|脚本中心)/[^'"]+\.py)['"]"""
)
RE_ANY_PY_PATH = re.compile(r"""['"]([^'"]*(?:开发工具|脚本中心)/[^'"]+\.py)['"]""")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_runtime_paths() -> dict:
    try:
        with open(RUNTIME_PATHS, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def iter_py_files():
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn:
                if f.endswith(".py") and ".bak-" not in f and ".bak" not in f:
                    yield os.path.join(dp, f)


def rel(p: str) -> str:
    try:
        return os.path.relpath(p, ARCHIVE)
    except ValueError:
        return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    rp = load_runtime_paths()
    live_dir = rp.get("devtools", "")
    gaps = []
    out = {"runtime_devtools": live_dir, "checks": [], "gaps": []}

    if not live_dir or not os.path.isdir(live_dir):
        msg = "runtime_paths.devtools 缺失或目录不存在=%r" % (live_dir,)
        gaps.append(msg)
        out["gaps"].append({"kind": "runtime_paths", "detail": msg})
        print("❌ " + msg)
        return 1

    print("真跑 devtools = %s" % live_dir)
    print("扫描面 = %d 个目录" % len(SCAN_ROOTS))

    n_verifier = 0
    n_live_hash = {}
    for p in iter_py_files():
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                t = fh.read()
        except OSError:
            continue
        if not any(s in t for s in TARGET_SCRIPTS):
            continue
        # 本件自身是被验证脚本则跳过
        if os.path.basename(p) in TARGET_SCRIPTS:
            continue
        n_verifier += 1

        reads_rp = "runtime_paths" in t   # 仅作报告标注：⛔ 不再据此跳过判据（洞：文件里写了 _resolve_devtools 就算 True，硬编码反而被放过）

        # ── 判据① 路径保真 ──
        # self-test / _selftest 区块内的路径串是**故意构造的测试夹具**，⛔ 不算运行路径
        # （实证：`zcode_config_guard.py` 的 T6 用例故意拼 `/Users/x//Users/...` 测正则匹配）
        _cut = len(t)
        for _m in re.finditer(r"^def (?:_?self_?test|run_self_?test)\(", t, re.M):
            _cut = min(_cut, _m.start())
        t_scan = t[:_cut]

        hard = []
        for m in RE_ANY_PY_PATH.finditer(t_scan):
            seg = m.group(1)
            if any(k in seg for k in NON_TARGET_DIRS):
                continue
            hard.append(seg)
        if hard:
            uniq = sorted(set(hard))
            gaps.append("%s 硬编码脚本路径（应解析自 runtime_paths）：%s" % (rel(p), uniq[:3]))
            out["gaps"].append({
                "kind": "path_fidelity", "file": rel(p),
                "detail": "硬编码 %d 处" % len(uniq), "paths": uniq[:5],
                "fix": "改为从 runtime_paths['devtools'] 解析",
            })
            print("  ❌ [路径保真] %s" % rel(p))
            for s in uniq[:3]:
                print("        %s" % s)
        elif reads_rp:
            print("  ✅ [路径保真] %s" % rel(p))

        # ── 判据② 内容保真：验证器实测件的 sha == 真跑件 sha ──
        if True:
            for m in RE_ANY_PY_PATH.finditer(t_scan):
                seg = m.group(1)
                if any(k in seg for k in NON_TARGET_DIRS):
                    continue
                probe = os.path.expanduser("~/" + seg.lstrip("~/")) if seg.startswith("~/") else seg
                if not os.path.isabs(probe):
                    probe = os.path.join(ARCHIVE, seg)
                base = os.path.basename(probe)
                live = os.path.join(live_dir, base)
                if not (os.path.isfile(probe) and os.path.isfile(live)):
                    continue
                if os.path.abspath(probe) == os.path.abspath(live):
                    continue
                hp, hl = sha256(probe), sha256(live)
                if hp != hl:
                    gaps.append(
                        "%s 测的是另一份：%s(%s) != 真跑 %s(%s)"
                        % (rel(p), seg, hp[:8], base, hl[:8])
                    )
                    out["gaps"].append({
                        "kind": "content_fidelity", "file": rel(p),
                        "detail": "探测件 sha=%s 真跑件 sha=%s" % (hp[:8], hl[:8]),
                        "fix": "TARGET 改读 runtime_paths['devtools']",
                    })
                    print("  ❌ [内容保真] %s 测 %s(%s) ≠ 真跑 %s(%s)"
                          % (rel(p), base, hp[:8], base, hl[:8]))
                    n_live_hash[base] = hl

    print("\n验证器 = %d 个" % n_verifier)

    # ── 判据③ 断言覆盖：否定语境真阴性必须在回归器 CASES 里 ──
    reg = os.path.join(ARCHIVE, "数字分身", "scripts", "d_tier_exclusivity_dryrun.py")
    if os.path.isfile(reg):
        with open(reg, encoding="utf-8", errors="ignore") as fh:
            rt = fh.read()
        missing = [p for p in NEGATION_PROBES if p not in rt]
        if missing:
            gaps.append("d_tier 回归器 CASES 缺否定语境真阴性断言（%d 条）" % len(missing))
            out["gaps"].append({
                "kind": "assertion_coverage", "file": rel(reg),
                "detail": "缺 %d 条否定语境断言：%s" % (len(missing), missing[:2]),
                "fix": "CASES 补否定式提及→仅 D1 断言",
            })
            print("  ❌ [断言覆盖] d_tier 回归器缺否定语境真阴性（%d 条）" % len(missing))
        else:
            print("  ✅ [断言覆盖] d_tier 回归器含否定语境真阴性")

    print()
    out["checks"] = {"verifiers": n_verifier, "live_hashes": n_live_hash}
    out["gap_count"] = len(gaps)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    if gaps:
        print("❌ 缺口 %d 项：" % len(gaps))
        for g in gaps:
            print("   · %s" % g)
        return 1
    print("✅ 验证器保真度全绿（路径保真 + 内容保真 + 断言覆盖）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
