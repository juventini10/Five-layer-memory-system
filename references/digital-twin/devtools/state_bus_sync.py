#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state_bus_sync.py v2.1.0 — 童灵多端状态同步检查器（SSOT驱动·判据换向版）

设计定位（数字分身设计哲学·P1-3多端状态同步机制·2026-09-03童灵愿景裁决·v2.0.0端清单SSOT化·
v2.1.0 判据换向根治「检查者改写判据」型假绿）：
- 端清单SSOT=06-跨端适配规范.md §2.2.0端清单JSON，本脚本从该JSON读取端清单，不硬编码
- 新增端/变更端状态/变更K2恒驻核路径时，只改哲学文件JSON，本脚本自动纳入检查，不需改代码
- **字段职责分家（v2.1.0 核心）**：
    `ends.<id>.expected_hash` = 判据（分发基线），**唯一合法写者=doenglingz_slice_watch.py**，本脚本只读；
    `ends.<id>.k2_core_hash` / `k2_region_hash` = 台账（观测值），本脚本每轮刷新。
  v2.0.0 曾把观测值写回判据位（L232-234）⇒ 端侧真漂移只红一次即自愈＝假绿，已根治。
- 比对粒度＝"机器拥有的那段"（标记块或 core 首行以后），端侧改块外自维内容不再触发假红
- 不一致则报警（输出详细信息+返回非0退出码），不自动修复（各端注入机制不同，自动修复不可行）
- 分发基线新鲜度：`dispatch_at` 超龄＝watcher 停摆，端会停在旧芯却仍显同步 ⇒ 同样报警
- k2_core_type=plugin_direct_read的端（如DSH黑鲸）：插件直读slices/，天然和SSOT一致，只检查插件配置文件存在
- 头部三块（iron_rules/k2_slices/personality_spec）v2.1.0 起由本脚本机器代写（立场卡#S922：
  会演进的值⛔手写），此前该三块自 v2.0.0 起无任何写者、实测腐烂 20 天
- 纳入launchd_health_check.sh附加检查项，每天自动运行

用法：
  python3 state_bus_sync.py            # 完整检查+详细输出
  python3 state_bus_sync.py --summary  # 仅摘要
  python3 state_bus_sync.py --update   # 检查后更新state_bus.json中的各端last_verified和status
  python3 state_bus_sync.py --self-test # 判据变异自测（临时夹具·不碰真台账·不碰真端文件）

退出码：
  0 = 全部同步
  1 = 有端不一致
  2 = state_bus.json不存在或格式错误
  3 = 哲学文件端清单JSON读取失败
  4 = 判据源（watcher 模块）不可加载——检查器不许降级回自指判据
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import hashlib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = os.path.expanduser("~")
# 数字分身中心：可用 DIGITALTWIN_HOME 覆盖（对齐 due_check/drift 提醒器先例·同一体系同一变量名）
TWIN_HOME = os.environ.get("DIGITALTWIN_HOME") or os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "数字分身")
STATE_BUS_PATH = os.path.join(TWIN_HOME, "state_bus.json")
PHILOSOPHY_FILE = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆蓝图", "04_系统文件设计", "数字分身设计哲学", "06-跨端适配规范.md")

# 判据唯一来源＝分发者本体（依赖方向：检查器 import 分发者，不得反向、不得另写一份标记常量）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import doenglingz_slice_watch as _w2
except Exception as _e:  # Fail-Loud：判据源缺失时不降级回"上一轮观测值当期望"
    print("❌ 无法加载分发者模块 doenglingz_slice_watch.py，判据无源可取 → 拒绝检查（不沿用旧自指判据）: %s" % _e)
    sys.exit(4)

BASELINE_MAX_AGE_DAYS = 3  # 可回落：改此常量为 0 即关闭基线新鲜度检查（一行回落·不另开开关）


def file_hash(path: str) -> str:
    """计算文件的sha256前12位hash。文件不存在返回空字符串。"""
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return ""
    h = hashlib.sha256()
    with open(expanded, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def load_end_manifest() -> dict:
    """从06-跨端适配规范.md §2.2.0读取端清单JSON（SSOT）。
    提取文件中第一个```json ... ```区块。
    """
    if not os.path.isfile(PHILOSOPHY_FILE):
        print(f"❌ 哲学文件不存在: {PHILOSOPHY_FILE}")
        sys.exit(3)

    with open(PHILOSOPHY_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取第一个```json ... ```区块
    match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    if not match:
        print("❌ 哲学文件中未找到端清单JSON区块（§2.2.0）")
        sys.exit(3)

    try:
        manifest = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"❌ 端清单JSON格式错误: {e}")
        sys.exit(3)

    if "ends" not in manifest:
        print("❌ 端清单JSON中缺少ends字段")
        sys.exit(3)

    return manifest


def _ssot_src_hash() -> str:
    """真源指纹（slices/manifest.json 的 src_hash＝规格书 hash）。基线的上游，判据的最终锚。"""
    try:
        with open(_w2.MANIFEST, encoding="utf-8") as f:
            return json.load(f).get("src_hash", "")
    except (OSError, json.JSONDecodeError):
        return ""


def _baseline_age(ts_str: str):
    """分发基线年龄（天）。空/不可解析 → None（交由上层按"无基线"另行处置）。"""
    if not ts_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return (datetime.now() - datetime.strptime(ts_str, fmt)).days
        except ValueError:
            continue
    return None


def check_end(end_def: dict, state_bus: dict) -> dict:
    """检查单个端的K2恒驻核状态。
    end_def: 哲学文件JSON中的端定义
    state_bus: state_bus.json内容
    """
    end_id = end_def["id"]
    name = end_def["name"]
    status = end_def["status"]
    k2_core_path = end_def.get("k2_core_path", "")
    k2_core_type = end_def.get("k2_core_type", "")
    notes = end_def.get("notes", "")

    # pending/ignored端不检查
    if status == "pending":
        return {
            "end_id": end_id,
            "name": name,
            "status": "pending",
            "issues": [],
            "actual_hashes": {},
            "note": "待接入",
        }
    if status == "ignored":
        return {
            "end_id": end_id,
            "name": name,
            "status": "ignored",
            "issues": [],
            "actual_hashes": {},
            "note": "不落地（你令）",
        }

    # completed端检查
    issues = []
    actual_hashes = {}
    w2_covered = None

    if k2_core_type == "file":
        # 独立文件类型：判据=分发基线(只读)，观测=机器拥有区段+整文件（台账职责）
        # v2.1.1 2026-10-09·SSOT演化跟随：06 v1.130 起 k2_core_path 可为双文件数组（LobsterAI分家案），
        #   消费端逐件哈希拼接成组合指纹；单文件str路径行为逐字不变（⛔改判据不跟消费端=本崩案复发结构）
        if isinstance(k2_core_path, list):
            parts = [file_hash(p) for p in k2_core_path]
            actual_hash = "+".join(p for p in parts if p) if any(parts) else ""
        else:
            actual_hash = file_hash(k2_core_path)
        actual_hashes["k2_core"] = actual_hash
        _paths = k2_core_path if isinstance(k2_core_path, list) else [k2_core_path]
        actual_hashes["k2_region"] = "+".join(_w2.k2_region_hash(os.path.expanduser(p)) for p in _paths) if actual_hash else ""
        covered = all(_w2.dispatch_covered(p) for p in _paths)
        w2_covered = covered

        if not actual_hash:
            issues.append(f"K2恒驻核文件不存在: {k2_core_path}")
        elif not covered:
            pass  # 端侧自维（06 语义）：不判红，由 w2_covered=False 在输出层显形
        else:
            end_state = state_bus.get("ends", {}).get(end_id, {})
            expected_hash = end_state.get("expected_hash", "")
            if not expected_hash:
                issues.append(f"无分发基线：W2 覆盖该端却未登记 expected_hash（watcher 从未成功部署·分发链断）")
            else:
                if actual_hashes["k2_region"] != expected_hash:
                    issues.append(f"K2芯偏离分发产物: 基线={expected_hash}, 实际区段={actual_hashes['k2_region']}"
                                  f", 基线src={end_state.get('expected_src', '?')}")
                # 基线的上游=真源。watcher bless 到旧芯（停摆后首跑）不得被 bless 成"正确"
                esrc = end_state.get("expected_src", "")
                ssot = _ssot_src_hash()
                if esrc and ssot and esrc != ssot:
                    issues.append(f"分发基线落后真源：expected_src={esrc} 而当前规格书={ssot}"
                                  f"（watcher 未把新切片分发到该端）")
                age = _baseline_age(end_state.get("dispatch_at", ""))
                if BASELINE_MAX_AGE_DAYS and age is not None and age > BASELINE_MAX_AGE_DAYS:
                    issues.append(f"分发基线陈旧 {age} 天（dispatch_at={end_state.get('dispatch_at')}）"
                                  f"→ watcher 停摆期间端会停在旧芯却仍显同步")

    elif k2_core_type == "plugin_direct_read":
        # 插件直读类型：检查插件配置文件存在（天然和SSOT一致，不需要hash比对）
        expanded_path = os.path.expanduser(k2_core_path)
        if not os.path.isfile(expanded_path):
            issues.append(f"插件配置文件不存在: {k2_core_path}")
        actual_hashes["k2_core"] = "plugin_direct_read（天然和SSOT一致）"

    else:
        issues.append(f"未知k2_core_type: {k2_core_type}")

    return {
        "end_id": end_id,
        "name": name,
        "status": "in_sync" if not issues else "out_of_sync",
        "issues": issues,
        "actual_hashes": actual_hashes,
        "w2_covered": w2_covered,
        "k2_core_path": k2_core_path,
        "k2_core_type": k2_core_type,
        "notes": notes,
    }


IRON_PATH = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "记忆规则", "用户基本规则-铁律版.md")
SPEC_PATH = os.path.join(TWIN_HOME, "童灵·人格规格书.md")
SLICES_MANIFEST = os.path.join(TWIN_HOME, "K2切片蒸馏", "slices", "manifest.json")


def refresh_header_blocks(state_bus: dict) -> None:
    """机器代写头部三块（立场卡#S922：会随真源演进的值⛔手写）。

    v2.0.0 的三块 hash 自 2026-09-03 起无任何写者，实测腐烂 20 天
    （总线记铁律 v8.8/8bf7cea63a52，盘上实为 v8.19/09c6eadd2cbe）。
    版本号一律取盘上原样，不推算、不美化。
    """
    def _head(path, n=4000):
        try:
            with open(path, encoding="utf-8") as f:
                return f.read(n)
        except OSError:
            return ""

    def _updated(path):
        try:
            return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
        except OSError:
            return ""

    iron_text = _head(IRON_PATH, None)  # 计数须读全文：只读头部曾致 count=2（实况 24·2026-09-27 自测抓出）
    m_ver = re.search(r"版本：(v[\d.]+)", iron_text)
    m_upd = re.search(r"更新：(\d{4}-\d{2}-\d{2})", iron_text)
    state_bus["iron_rules"] = {
        "ssot_path": "[记忆共享中心]/记忆规则/用户基本规则-铁律版.md",
        "ssot_version": m_ver.group(1) if m_ver else "",
        "content_hash": file_hash(IRON_PATH),
        "count": len(re.findall(r"(?m)^### 铁律-\d+", iron_text)),
        "last_updated": m_upd.group(1) if m_upd else _updated(IRON_PATH),
    }

    try:
        with open(SLICES_MANIFEST, encoding="utf-8") as f:
            man = json.load(f)
    except (OSError, json.JSONDecodeError):
        man = {}
    state_bus["k2_slices"] = {
        "slices_path": "[记忆共享中心]/数字分身/K2切片蒸馏/slices/",
        "src_hash": man.get("src_hash", ""),
        "generated": man.get("generated", ""),
        "count": len(man.get("slices", [])),
        "last_updated": _updated(SLICES_MANIFEST),
    }

    state_bus["personality_spec"] = {
        "path": "[记忆共享中心]/数字分身/童灵·人格规格书.md",
        "content_hash": file_hash(SPEC_PATH),
        "last_updated": _updated(SPEC_PATH),
    }
    state_bus["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")


def self_test() -> int:
    """判据变异自测：临时夹具·不碰真台账·不碰真端文件。夹具形状照抄真机文件。

    覆盖"门禁三态"里的假绿与假红两侧：
      T1 基线一致→必须绿  T2 区段内被改→必须连续两轮红（不许自愈）
      T3 标记块外被改→必须不红（根治整文件比对的假红）
      T4 基线超龄→必须红  T8 基线 bless 旧芯→必须红（锚在真源非分发快照）
      T5 无基线→必须红  T6 自维端→不判红但显形
      T7 静态判据位禁写断言（防 v2.0.0 型回归）
    """
    import shutil
    import tempfile

    fixture_src = os.path.join(HOME, ".zcode", "AGENTS.md")
    if not os.path.isfile(fixture_src):
        print("❌ 自测缺真机夹具（~/.zcode/AGENTS.md），拒绝用编造形状自测")
        return 1

    tmp = tempfile.mkdtemp(prefix="k2_baseline_selftest_")
    real_home = _w2.MARKED_HOMES[:]
    results = []
    try:
        fx = os.path.join(tmp, "AGENTS.md")
        shutil.copyfile(fixture_src, fx)
        _w2.MARKED_HOMES.append(fx)

        def end_def():
            return {"id": "fx", "name": "夹具端", "status": "completed",
                    "k2_core_path": fx, "k2_core_type": "file", "notes": ""}

        def bus(expected, dispatch_at, src=None):
            e = {}
            if expected:
                e["expected_hash"] = expected
                e["expected_src"] = src or ssot
            if dispatch_at:
                e["dispatch_at"] = dispatch_at
            return {"ends": {"fx": e}}

        def issues_of(bus_obj):
            return check_end(end_def(), bus_obj)["issues"]

        def text():
            return open(fx, encoding="utf-8").read()

        def write(t):
            with open(fx, "w", encoding="utf-8") as f:
                f.write(t)

        good = _w2.k2_region_hash(fx)
        ssot = _ssot_src_hash()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # T1 基线一致 → 绿
        results.append(("T1 一致判绿", issues_of(bus(good, now)) == []))
        # T2 机器拥有区内被改 → 连续两轮都红（判据不被观测值覆盖＝不再自愈）
        i1 = text().find(_w2.CORE_START)
        cut = text().find("\n", i1) + 1
        write(text()[:cut] + "\n<!-- tampered inside K2 region -->\n" + text()[cut:])
        i_a = issues_of(bus(good, now))
        i_b = issues_of(bus(good, now))
        results.append(("T2 区段篡改持续报红", bool(i_a) and bool(i_b)))
        # T3 标记块外被改 → 不红（还原真机判例：皮叔 09-26 改 AGENTS.md 块外索引，整文件比对误报红）
        shutil.copyfile(fixture_src, fx)
        write("端侧自维段：新增一行说明。\n" + text())
        results.append(("T3 块外改动不假红", issues_of(bus(good, now)) == []))
        # T4 基线超龄 → 红
        old = (datetime.now() - __import__("datetime").timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        results.append(("T4 基线超龄报红", any("陈旧" in x for x in issues_of(bus(good, old)))))
        # T8 基线 bless 的是旧芯（watcher 停摆后首跑）→ 必须红：判据最终锚在真源，不在分发快照
        results.append(("T8 bless旧芯报红",
                        any("落后真源" in x for x in issues_of(bus(good, now, src="stale00000000")))))
        # T5 W2 覆盖但无基线 → 红
        results.append(("T5 无基线报红", any("无分发基线" in x for x in issues_of(bus("", now)))))
        # T6 不在覆盖内的端 → 不判红，w2_covered=False 显形
        _w2.MARKED_HOMES.remove(fx)
        r6 = check_end(end_def(), bus(good, now))
        results.append(("T6 自维端不判红且显形", r6["issues"] == [] and r6["w2_covered"] is False))
        _w2.MARKED_HOMES.append(fx)
        # T7 判据位静态禁写：main 的写路径里不得出现对 expected_*/dispatch_at 的赋值
        import inspect
        mainsrc = inspect.getsource(main)
        results.append(("T7 判据位无写路径",
                        not re.search(r"\[[\"'](?:expected_hash|expected_src|dispatch_at)[\"']\]\s*=", mainsrc)))
        # T9 头部机器代写值须与独立计数一致（截断读文件曾致 count=2 vs 实况 24）
        blk = {}
        refresh_header_blocks(blk)
        try:
            indep = int(subprocess.run(["grep", "-c", "-E", "^### 铁律-[0-9]", IRON_PATH],
                                       capture_output=True, text=True).stdout.strip() or "-1")
        except Exception:
            indep = -1
        results.append(("T9 头部铁律计数=独立计数", blk.get("iron_rules", {}).get("count") == indep and indep > 0))
        results.append(("T9b 头部规格书 hash=独立现算",
                        blk.get("personality_spec", {}).get("content_hash") ==
                        hashlib.sha256(open(SPEC_PATH, "rb").read()).hexdigest()[:12]))
    finally:
        _w2.MARKED_HOMES[:] = real_home
        shutil.rmtree(tmp, ignore_errors=True)

    ok = sum(1 for _, p in results if p)
    for name, p in results:
        print(f"  {'✅' if p else '❌'} {name}")
    print(f"self-test: {ok}/{len(results)}")
    return 0 if ok == len(results) else 1


def main():
    summary_mode = "--summary" in sys.argv
    update_mode = "--update" in sys.argv

    # 读取state_bus.json
    if not os.path.isfile(STATE_BUS_PATH):
        print(f"❌ state_bus.json不存在: {STATE_BUS_PATH}")
        sys.exit(2)

    try:
        with open(STATE_BUS_PATH, "r", encoding="utf-8") as f:
            state_bus = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ state_bus.json格式错误: {e}")
        sys.exit(2)

    # 从哲学文件读取端清单（SSOT）
    manifest = load_end_manifest()
    ends_def = manifest["ends"]

    if not summary_mode:
        print("🔄 童灵多端状态同步检查 v2.1.0（SSOT驱动·判据换向：基线由分发者写，本脚本只读）")
        print(f"   端清单SSOT: 06-跨端适配规范.md §2.2.0（{len(ends_def)}端登记）")
        print("=" * 60)

    # 检查各端
    results = [check_end(end_def, state_bus) for end_def in ends_def]

    # 统计（只统计completed端）
    completed_results = [r for r in results if r["status"] in ("in_sync", "out_of_sync")]
    in_sync = sum(1 for r in completed_results if r["status"] == "in_sync")
    out_of_sync = sum(1 for r in completed_results if r["status"] == "out_of_sync")
    pending = sum(1 for r in results if r["status"] == "pending")
    ignored = sum(1 for r in results if r["status"] == "ignored")
    total_completed = len(completed_results)

    # 输出
    if not summary_mode:
        for r in results:
            if r["status"] == "in_sync":
                print(f"  ✅ {r['name']}: 同步")
                if r.get("k2_core_type") == "plugin_direct_read":
                    print(f"     （插件直读slices/·天然和SSOT一致）")
                elif r.get("w2_covered") is False:
                    print(f"     （端侧自维·不在 W2 分发覆盖内→无基线可依·不判红）")
            elif r["status"] == "out_of_sync":
                print(f"  ❌ {r['name']}: 不同步")
                for issue in r["issues"]:
                    print(f"     - {issue}")
            elif r["status"] == "pending":
                print(f"  ⏳ {r['name']}: 待接入（跳过检查）")
            elif r["status"] == "ignored":
                print(f"  ⛔ {r['name']}: 不落地（你令·跳过检查）")
        print()
        print(f"📊 检查结果: 已接入{total_completed}端, ✅同步={in_sync}, ❌不同步={out_of_sync}, ⏳待接入={pending}, ⛔不落地={ignored}")
    else:
        status_str = "all_in_sync" if out_of_sync == 0 else f"{out_of_sync}_out_of_sync"
        print(f"state_bus_sync: {status_str} ({in_sync}/{total_completed} in sync, {pending} pending, {ignored} ignored)")

    # 更新state_bus.json
    if update_mode:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for r in results:
            end_id = r["end_id"]
            if end_id not in state_bus["ends"]:
                state_bus["ends"][end_id] = {}
            state_bus["ends"][end_id]["name"] = r["name"]
            state_bus["ends"][end_id]["status"] = r["status"]
            state_bus["ends"][end_id]["last_verified"] = now
            if r.get("k2_core_path"):
                state_bus["ends"][end_id]["k2_core_path"] = r["k2_core_path"]
            if r.get("k2_core_type"):
                state_bus["ends"][end_id]["k2_core_type"] = r["k2_core_type"]
            if r.get("notes"):
                state_bus["ends"][end_id]["notes"] = r["notes"]
            # 只写观测值（台账职责）。⛔expected_hash / expected_src / dispatch_at 属判据位，
            # 唯一合法写者=doenglingz_slice_watch.py。v2.0.0 在此把观测值覆盖进判据位＝假绿根因。
            for key, value in r["actual_hashes"].items():
                if key == "k2_core":
                    state_bus["ends"][end_id]["k2_core_hash"] = value
                elif key == "k2_region":
                    state_bus["ends"][end_id]["k2_region_hash"] = value
        refresh_header_blocks(state_bus)
        state_bus["sync_check"]["last_check"] = now
        state_bus["sync_check"]["last_result"] = "all_in_sync" if out_of_sync == 0 else f"{out_of_sync}_out_of_sync"
        state_bus["sync_check"]["total_ends"] = len(ends_def)
        state_bus["sync_check"]["completed_ends"] = total_completed

        with open(STATE_BUS_PATH, "w", encoding="utf-8") as f:
            json.dump(state_bus, f, ensure_ascii=False, indent=2)

        if not summary_mode:
            print(f"  📝 state_bus.json已更新 ({now})")

    # 退出码
    sys.exit(0 if out_of_sync == 0 else 1)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    main()
