#!/usr/bin/env python3
"""closeout_guard 路径可移植性回归（2026-09-18 第一性根治配套）。

背景：guard 原把 HOME 下个人绝对路径写死（[记忆共享中心]/...）→ 换机/换用户名/对外
分发后 S1/S3 全部静默放行，**看起来在岗实际零判定**。根治手段=根探测（env → 自我
定位 → HOME 候选）+ 显式 failsafe。

本测试的职责不是"再验一次当前实现能跑"，而是**把退化场景机械拦住**：
  [1] 源码级：guard.py 不得出现硬编码个人绝对路径（注释/探测候选除外）
  [2] 负向注入：模拟"探测全失败"→ 必须显式 skipped，⛔不得静默当正常
  [3] env 覆盖：显式意图必须压过自动探测（否则沙盒测试改不动目标）
  [4] 自我定位：随包安装到 <MC>/技能配置/triwich/scripts/ 仍能命中

运行：python3 tests/test_guard_path_portability.py   （退出码 0=全过）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
GUARD_SRC = os.path.join(os.path.expanduser("~"), "[记忆共享中心]/脚本中心/triwich_closeout_guard.py")

PASS, FAIL = [], []


def ok(msg):
    PASS.append(msg)
    print("  ✅ " + msg)


def bad(msg):
    FAIL.append(msg)
    print("  ❌ " + msg)


def _load(path, env=None):
    """在受控 env 下加载 guard 模块（模拟换机/沙盒）。"""
    saved = {k: os.environ.get(k) for k in ("TRIWICH_MC", "MEMORY_CENTER", "HOME")}
    try:
        if env:
            for k, v in env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        spec = importlib.util.spec_from_file_location("guard_under_test", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_source_no_hardcoded_path():
    """[1] 源码级反例：硬编码个人绝对路径必须为 0（本轮根治的核心不变量）。"""
    print("\n[1] 源码级：不得硬编码个人绝对路径")
    src = open(GUARD_SRC, encoding="utf-8").read()
    offenders = []
    for i, line in enumerate(src.splitlines(), 1):
        code = line.split("#", 1)[0]
        # 探测候选常量（MC_CANDIDATES_HOME）是唯一合法出现点
        if "MC_CANDIDATES_HOME" in line:
            continue
        if re.search(r'["\'][^"\']*个人AI档案[^"\']*["\']', code):
            offenders.append((i, line.strip()[:90]))
        if re.search(r'["\']/Users/[^"\']*["\']', code):
            offenders.append((i, line.strip()[:90]))
    if offenders:
        for i, s in offenders:
            bad("硬编码路径 %d: %s" % (i, s))
    else:
        ok("零硬编码个人绝对路径")


def test_negative_injection_no_mc():
    """[2] 负向注入：探测全失败 → 显式 skipped，⛔不得静默当正常。

    注意：必须在**孤立安装位置**跑（subprocess + 无 技能配置/ 祖先的临时目录）。
    直接在开发端（[记忆共享中心]/开发工具/）加载会命中自我定位，那是**正确行为**——
    自我定位不应被 HOME 影响，否则开发端换 HOME 反而失效（2026-09-18 实测纠正）。
    """
    print("\n[2] 负向注入：无记忆中心环境")
    tmp = tempfile.mkdtemp()
    try:
        bare = os.path.join(tmp, "bare")
        os.makedirs(bare)
        copied = os.path.join(bare, "guard.py")
        shutil.copy2(GUARD_SRC, copied)
        env = {k: v for k, v in os.environ.items()
               if k not in ("TRIWICH_MC", "MEMORY_CENTER")}
        env["HOME"] = os.path.join(tmp, "ghost-home")
        os.makedirs(env["HOME"])
        probe = (
            "import importlib.util,sys,json;"
            "s=importlib.util.spec_from_file_location('g',sys.argv[1]);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
            "print(json.dumps({'mc':m.MC,'skipped':m.check(None).get('skipped') or ''}))"
        )
        r = subprocess.run([sys.executable, "-c", probe, copied],
                           capture_output=True, text=True, env=env)
        out = (r.stdout or "").strip().splitlines()
        d = json.loads(out[-1]) if out else {}
        if d.get("mc") is None:
            ok("MC=None（孤立位置，未回落真实目录）")
        else:
            bad("探测全失败时 MC 应为 None，实得 %r" % d.get("mc"))
        sk = d.get("skipped") or ""
        if sk and ("探测失败" in sk or "TRIWICH_MC" in sk):
            ok("显式 skipped 说明：%s" % sk[:48])
        else:
            bad("探测失败未显式说明（静默放行）skipped=%r" % sk)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_env_overrides_autodetect():
    """[3] env 覆盖：显式意图优先于自动探测（沙盒测试的前提）。"""
    print("\n[3] env 覆盖优先")
    tmp = tempfile.mkdtemp()
    try:
        mc = os.path.join(tmp, "sandbox-mc")
        os.makedirs(os.path.join(mc, "技能配置", "triwich", "references"))
        mod = _load(GUARD_SRC, env={"TRIWICH_MC": mc})
        if mod.MC == os.path.realpath(mc):
            ok("TRIWICH_MC 命中 %s" % mod.MC)
        else:
            bad("env 未生效：MC=%r 期望 %r" % (mod.MC, os.path.realpath(mc)))
        if mod.DECISION_ROOM and mod.DECISION_ROOM.startswith(os.path.realpath(mc)):
            ok("派生路径全部落在沙盒内")
        else:
            bad("派生路径泄漏到沙盒外：%r" % mod.DECISION_ROOM)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_self_location():
    """[4] 自我定位：随包安装（<MC>/技能配置/triwich/scripts/）仍命中。"""
    print("\n[4] 自我定位（位置无关安装）")
    tmp = tempfile.mkdtemp()
    try:
        scripts = os.path.join(tmp, "技能配置", "triwich", "scripts")
        os.makedirs(scripts)
        copied = os.path.join(scripts, "guard.py")
        shutil.copy2(GUARD_SRC, copied)
        r = subprocess.run([sys.executable, "-c",
                            "import importlib.util,sys;"
                            "s=importlib.util.spec_from_file_location('g',sys.argv[1]);"
                            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                            "print(m.MC)", copied],
                           capture_output=True, text=True,
                           env={k: v for k, v in os.environ.items()
                                if k not in ("TRIWICH_MC", "MEMORY_CENTER")})
        got = (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else r.stderr[:80]
        if got == os.path.realpath(tmp):
            ok("自我定位命中 %s" % got)
        else:
            bad("自我定位失败，得 %r，期望 %r" % (got, os.path.realpath(tmp)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 54)
    print("closeout_guard 路径可移植性回归")
    print("=" * 54)
    if not os.path.isfile(GUARD_SRC):
        print("  ⚠️ 守卫源不存在，跳过：%s" % GUARD_SRC)
        sys.exit(0)
    test_source_no_hardcoded_path()
    test_negative_injection_no_mc()
    test_env_overrides_autodetect()
    test_self_location()
    print("\n" + "=" * 54)
    print("结果：通过 %d · 失败 %d" % (len(PASS), len(FAIL)))
    print("=" * 54)
    sys.exit(1 if FAIL else 0)
