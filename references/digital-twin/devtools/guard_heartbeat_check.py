#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v3.1
"""guard_heartbeat_check.py — 统一「派发心跳」守卫（三腿·扩检测域·反盲·退役登记）

## v3.1（2026-09-23 · 退役登记腿）
有意退役的心跳源不再报「停摆嫌疑」——改读 `.guard/` 同级 `retired_sources.json`：
登记项显形为 `retired`（不计告警·仍列明细→防告警疲劳；⛔不静默消失）。
首例：collector（愿景三问全否·见登记表 basis）。你授权·童灵执行。
⚠️ 退役≠健康——「用意已裁定的无声」与「坏了没人知」必须分开表达。

## v3.0 根治（2026-09-22 · C-090 零检出盲区）
v2.0 只扫 hook 心跳（HB_DIR），漏掉路由家族 `.guard/*.ts` 与 `.patrol/*.ts`
→ collector 心跳 8-29 冻结 24 天无人知（真孤儿脚本，全库零调用方）。
v3.0 三腿统一：
  Leg A 钩子派发心跳  HB_DIR/*.heartbeat             （hook_protocol import 留痕）
  Leg B 路由组件心跳    {RCF}/.guard/*_last_run.ts      （collector/feeder/radar）
  Leg C 巡逻心跳        {RCF}/.patrol/*.ts             （各端 patrol + 通用 last_run）
RCF = os.path.expanduser("~/脚本中心")

## 反盲（C-090 不可能静默）
旧逻辑：全量 no_record = "刚装完正常" → 老机器 hook_protocol 缺失时整腿静默失明。
新逻辑：跨腿推断 machine_active（任一腿有在岗证据=机器在跑）。
  机器在跑但某源全 no_record → 升 blind_suspect（🟡守卫盲区·非安装正常），
  显形供裁决，且写入巡检日志（不可能静默）。
advisory 仍不改退出码；硬漂移（ST_MISS）才 alarm=true。

## 纪律
纯 stdlib；除自身心跳外只读；advisory 不硬失败（新鲜度无法区分休假与停摆）。
契约：--check(JSON) / --report(md) / --brief(单行) / --selfcheck / --self-test(路径解析回归锁·⑤腿消费)
      / [--days N]（仅影响 Leg A 窗口）/ [--mc <记忆中心>]
Stop hook 已挂 --check（settings.json），每次会话结束自动巡检→闭环（vision①）。
作者：皮叔 | 版本：v3.0 | 日期：2026-09-22
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_DAYS = 7
HOOK_DAYS = DEFAULT_DAYS
GUARD_DAYS = 14
PATROL_DAYS = 14

# ── 端中立参数化（v3.2·2026-10-01 Hermes 端 T0 根治·对齐 doenglingz_guard.py v1.1 形态）──
# 病根：本组常量 v1.0-v3.1 全部硬编码 `~/.workbuddy/` ⇒ **非 WorkBuddy 端零覆盖**
#       （Hermes 端 `guard_heartbeat_check.py` 装上也只能查 WB 的心跳目录）。
# 实证（Hermes 端）：HB_DIR 指向 `~/.workbuddy/hooks/.heartbeats`，
#       而 Hermes 端根本无该目录（本端钩子不 import hook_protocol）⇒ 查出来必然
#       「无记录」，而**真正的 Hermes 运行态痕迹在 `~/.hermes/*.log|*.json`**
#       ⇒ 报「全停摆」是假红，报「无记录」也不代表本端守卫没跑。
#
# ✅ 三段配置根（env 优先·形态对齐 doenglingz_guard.py v1.1 已实证的写法）：
#      GUARD_HEARTBEAT_ROOT > WORKBUDDY_CONFIG_DIR > ~/.workbuddy
#   ⛔ **向后兼容**：不设任何 env 时行为与 v3.1 **完全一致**（仍指 ~/.workbuddy）
#      ⇒ WB 端零影响（不设 env 就不用改）。
#   ⇒ 新端（如 Hermes）设 `GUARD_HEARTBEAT_ROOT=~/.hermes` 即可复用本守卫，
#      而不必 fork 一份（零复制·守卫规范 §二·十四 接入不拥有）。
_HOME_DIR = os.path.expanduser("~")
_CFG_ROOT = (os.environ.get("GUARD_HEARTBEAT_ROOT")
             or os.environ.get("WORKBUDDY_CONFIG_DIR")
             or os.path.join(_HOME_DIR, ".workbuddy"))
# SETTINGS 也需端可覆盖：Hermes 端注册清单真相源是 `config.yaml`（无 settings.json 结构）
# ⇒ 端侧可传 `GUARD_HEARTBEAT_SETTINGS` 指向本端注册清单（Hermes 侧传
#   `~/.hermes/hooks_registry.json`——由 hermes_plugin_health_guard 从
#   config.yaml plugins.enabled 机械派生·注册态≠派发态由心跳腿独立判）。
SETTINGS = (os.environ.get("GUARD_HEARTBEAT_SETTINGS")
            or os.path.join(_CFG_ROOT, "settings.json"))
# 与 hook_protocol.py HB_DIR 同式（漂移绊线见 --selfcheck）
HB_DIR = os.path.join(_CFG_ROOT, "hooks", ".heartbeats")
HOME = _HOME_DIR
RCF = os.path.expanduser("[记忆共享中心]/脚本中心")
GUARD_DIR = os.path.join(RCF, ".guard")
PATROL_DIR = os.path.join(RCF, ".patrol")
GUARD_LOG = os.path.join(PATROL_DIR, "guard_heartbeat_check.log")
EXPECTED_GUARD = ["collector", "feeder", "radar"]

ST_ON, ST_STALE, ST_NONE, ST_MISS, ST_BLIND, ST_RETIRED = (
    "on_duty", "suspected_shutdown", "no_record", "script_missing",
    "blind_suspect", "retired")
# 退役登记表（有意退出≠坏了没人知·两者必须分开表达·v3.1）
RETIRED_FILE = os.path.join(RCF, "retired_sources.json")  # v3.1.1：移出 .guard/（该目录被 .gitignore/**/.guard/ 覆盖·登记表须入 git 可追溯）


def beat():
    """本检查器自己也留心跳——否则下次它自己就是「无证据」的一员。"""
    try:
        os.makedirs(HB_DIR, exist_ok=True)
        with open(os.path.join(HB_DIR, "guard_heartbeat_check.heartbeat"), "w",
                  encoding="utf-8") as f:
            f.write(datetime.now().isoformat(timespec="seconds"))
    except OSError:
        pass


def days_old(path):
    try:
        return (datetime.now() - datetime.fromtimestamp(
            os.path.getmtime(path))).total_seconds() / 86400
    except OSError:
        return None


def script_stem(cmd):
    """从 hook command 里抽脚本主名，如 route_inject_prompt.py → route_inject_prompt"""
    m = re.search(r"([A-Za-z0-9_\-]+\.(?:py|sh))", cmd)
    return os.path.splitext(os.path.basename(m.group(1)))[0] if m else None


def script_path_of(cmd):
    # 2026-10-21 根治(Win用户反馈缺陷①)：旧 r"(\S+\.py|sh)" 对 Windows 引号路径
    #   (路径含空格必被引号包住) 把前导引号吞进捕获、遇空格还截断 → exists 恒假
    #   → 全体钩子误判 ST_MISS 硬漂移假红。改：优先匹配双引号内整路径(容空格)，回退裸 token。
    m = re.search(r'"([^"]+\.(?:py|sh))"|(\S+\.(?:py|sh))', cmd)
    if not m:
        return None
    return os.path.expanduser(m.group(1) or m.group(2))


def find_ledger(mc=None):
    cands = []
    if mc:
        cands.append(mc)
    if os.environ.get("MEMORY_CENTER"):
        cands.append(os.environ["MEMORY_CENTER"])
    cands.append(os.path.join(os.path.expanduser("~"), "记忆共享中心"))
    for base in cands:
        p = os.path.join(base, "脚本中心", "logs", "runtime",
                         "hook_protocol_ledger.jsonl")
        if os.path.isfile(p):
            return p
    return None


def ledger_freshness(ledger_path):
    """台账按脚本名归并最新 ts → {stem: days_old}。解析失败的行跳过。"""
    out = {}
    if not ledger_path:
        return out
    try:
        with open(ledger_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("probe"):
                    continue  # probe 测试行不作为派发证据
                name = str(d.get("script") or "")
                if not name:
                    continue
                stem = os.path.splitext(os.path.basename(name))[0]
                try:
                    t = datetime.strptime(str(d.get("ts", ""))[:19],
                                          "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue
                age = (datetime.now() - t).total_seconds() / 86400
                if stem not in out or age < out[stem]:
                    out[stem] = age
    except OSError:
        pass
    return out


def hb_drift_warning():
    """漂移绊线：hook_protocol.py 在场却不再提 .heartbeats = 路径可能已改而本脚本未跟。"""
    hits = glob.glob(os.path.join(os.path.expanduser("~"), ".workbuddy",
                                  "hooks", "**", "hook_protocol.py"),
                     recursive=True)
    if not hits:
        return None
    try:
        with open(hits[0], encoding="utf-8", errors="ignore") as f:
            src = f.read()
        if ".heartbeats" not in src and "HB_DIR" not in src:
            return ("hook_protocol.py 已无心跳留痕代码——留痕端与检查端可能已漂移，"
                    "两文件须同轮修改（单一真源纪律）")
    except OSError:
        return None
    return None


def check_hooks(days, ledger_path=None):
    """检查 settings.json 里注册的每个钩子 → 三态（+反盲前仍为 no_record）。"""
    results = []
    try:
        with open(SETTINGS, encoding="utf-8") as f:
            settings = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [{"name": "settings.json", "leg": "hook", "state": ST_MISS,
                 "note": "读取失败: %s" % e, "event": "", "scope": ""}]
    led = ledger_freshness(ledger_path)
    # ⚠️ v3.2 端中立化第二处：此处原硬编码 `~/.workbuddy/hooks`·⛔ 漏改则
    #   `hooks_root` 在 Hermes 端指向别端目录（跨端台账串味·守卫规范 §八 端隔离）。
    #   正解=与 HB_DIR 同根（同一配置根派生·⛔ 不引第二份路径常量）。
    hooks_root = os.path.join(_CFG_ROOT, "hooks")
    seen = set()
    for event, groups in (settings.get("hooks") or {}).items():
        for group in groups or []:
            for hook in group.get("hooks", []) or []:
                cmd = hook.get("command", "")
                stem = script_stem(cmd)
                if not stem or stem in seen:
                    continue
                seen.add(stem)
                spath = script_path_of(cmd)
                exists = bool(spath and os.path.exists(spath))
                scope = ("buluotuo" if spath and os.path.abspath(spath)
                         .startswith(os.path.abspath(hooks_root)) else "other")
                hb = os.path.join(HB_DIR, "%s.heartbeat" % stem)
                hb_age = days_old(hb)
                led_age = led.get(stem)
                if not exists:
                    state, evidence, age = ST_MISS, None, None
                elif (hb_age is not None and hb_age <= days) or \
                        (led_age is not None and led_age <= days):
                    state = ST_ON
                    if hb_age is not None and hb_age <= days:
                        evidence, age = hb, hb_age
                    else:
                        evidence, age = ledger_path, led_age
                elif hb_age is not None:
                    state, evidence, age = ST_STALE, hb, hb_age
                else:
                    state, evidence, age = ST_NONE, None, None
                results.append({"name": stem, "leg": "hook", "event": event,
                                "state": state, "scope": scope,
                                "evidence": evidence,
                                "age_days": None if age is None else round(age, 2),
                                "script_exists": exists})
    return results


def scan_ts_leg(dirpath, pattern, days, leg):
    """扫某目录下所有匹配心跳文件 → 行。仅扫已存在的文件，无文件则空（不造 no_record）。"""
    rows = []
    if not os.path.isdir(dirpath):
        return rows
    for p in glob.glob(os.path.join(dirpath, pattern)):
        name = os.path.splitext(os.path.basename(p))[0]
        age = days_old(p)
        if age is None:
            state, age_r = ST_NONE, None
        elif age <= days:
            state, age_r = ST_ON, age
        else:
            state, age_r = ST_STALE, age
        rows.append({"name": name, "leg": leg, "state": state,
                     "evidence": p,
                     "age_days": None if age_r is None else round(age_r, 2)})
    return rows


def missing_expected_guard(guard_rows, retired=()):
    """collector/feeder/radar 任一 .ts 整文件缺失 = 组件根本没在写心跳（比冻结更强）。
    已退役登记项豁免（有意退出 ≠ 未接线）。"""
    present = {r["name"].replace("_last_run", "") for r in guard_rows}
    return [e for e in EXPECTED_GUARD if e not in present and e not in retired]


def machine_active(all_rows):
    """跨腿推断：任一腿有在岗证据 = 机器在跑。用于反盲判定。"""
    return any(r["state"] == ST_ON for r in all_rows)


def load_retired():
    """读退役登记表（`.guard/` 同级 `retired_sources.json`）→ {name}。
    缺失/损坏 → 空集（保守：不豁免任何源，宁可多报）。"""
    try:
        with open(RETIRED_FILE, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()
    return set((d.get("retired") or {}).keys())


def _retired_key(name):
    """退役登记比对键：`collector_last_run` → `collector`（与 EXPECTED_GUARD 同口径）。"""
    return name[:-len("_last_run")] if name.endswith("_last_run") else name


def apply_retired(rows, retired):
    """退役登记后处理：登记项 state → retired（显形保留·不计告警；原态存 prev_state）。

    ⚠️ 退役 ≠ 健康：前者是"用意已裁定的无声"，后者是"坏了没人知"——必须分开表达，
    故退役项仍出现在 rows/输出里，只是不再计入停摆嫌疑。"""
    if not retired:
        return
    for r in rows:
        if _retired_key(r["name"]) in retired:
            r["prev_state"] = r["state"]
            r["state"] = ST_RETIRED


def apply_blind(hook_rows, active):
    """反盲：机器在跑但某 hook 全 no_record → blind_suspect（非安装正常）。"""
    if not active:
        return
    for r in hook_rows:
        if r["state"] == ST_NONE:
            r["state"] = ST_BLIND


def _classify(rows):
    return {k: [r for r in rows if r["state"] == k]
            for k in (ST_ON, ST_STALE, ST_NONE, ST_MISS, ST_BLIND, ST_RETIRED)}


def _log_write(summary, active, missing):
    """巡检日志：每次运行追加一行紧凑摘要（不可能静默·可 grep）。"""
    try:
        line = ("[%s] active=%s on=%d stale=%d none=%d blind=%d miss=%d "
                "retired=%d missing_guard=%s alarm=%s"
                % (datetime.now().isoformat(timespec="seconds"),
                   "Y" if active else "N",
                   len(summary[ST_ON]), len(summary[ST_STALE]),
                   len(summary[ST_NONE]), len(summary[ST_BLIND]),
                   len(summary[ST_MISS]),
                   len(summary[ST_RETIRED]),
                   ",".join(missing) if missing else "-",
                   "Y" if summary[ST_MISS] else "N"))
        with open(GUARD_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def mode_check(days, mc):
    beat()
    hook_rows = check_hooks(HOOK_DAYS, find_ledger(mc))
    guard_rows = scan_ts_leg(GUARD_DIR, "*_last_run.ts", GUARD_DAYS, "guard")
    patrol_rows = scan_ts_leg(PATROL_DIR, "*.ts", PATROL_DAYS, "patrol")
    all_rows = hook_rows + guard_rows + patrol_rows
    active = machine_active(all_rows)
    apply_blind(hook_rows, active)
    rows = hook_rows + guard_rows + patrol_rows
    retired = load_retired()
    apply_retired(rows, retired)
    s = _classify(rows)
    missing = missing_expected_guard(guard_rows, retired)
    _log_write(s, active, missing)
    print(json.dumps({
        "window_days": {"hook": HOOK_DAYS, "guard": GUARD_DAYS,
                        "patrol": PATROL_DAYS},
        "machine_active": active,
        "on_duty": [{"name": r["name"], "leg": r["leg"],
                    "age_days": r["age_days"]} for r in s[ST_ON]],
        "suspected_shutdown": [{"name": r["name"], "leg": r["leg"],
                                "age_days": r["age_days"]} for r in s[ST_STALE]],
        "no_record": [r["name"] for r in s[ST_NONE]],
        "blind_suspect": [r["name"] for r in s[ST_BLIND]],
        "script_missing": [r["name"] for r in s[ST_MISS]],
        "retired": [{"name": r["name"], "leg": r["leg"],
                     "age_days": r["age_days"],
                     "prev_state": r.get("prev_state")} for r in s[ST_RETIRED]],
        "missing_expected_guard": missing,
        "drift_warning": hb_drift_warning(),
        "alarm": bool(s[ST_MISS]),
        "note": "advisory 显形不改退出码；停摆嫌疑≠判死（休假同签名）；"
                "blind_suspect=机器在跑但此源零派发（反盲·非安装正常）；"
                "retired=登记在 路由家族/retired_sources.json 的**有意退出**源"
                "（不计告警·仍显形·退役≠健康）"
    }, ensure_ascii=False, indent=2))
    return 0


def mode_report(days, mc):
    beat()
    hook_rows = check_hooks(HOOK_DAYS, find_ledger(mc))
    guard_rows = scan_ts_leg(GUARD_DIR, "*_last_run.ts", GUARD_DAYS, "guard")
    patrol_rows = scan_ts_leg(PATROL_DIR, "*.ts", PATROL_DAYS, "patrol")
    all_rows = hook_rows + guard_rows + patrol_rows
    active = machine_active(all_rows)
    apply_blind(hook_rows, active)
    rows = hook_rows + guard_rows + patrol_rows
    retired = load_retired()
    apply_retired(rows, retired)
    s = _classify(rows)
    missing = missing_expected_guard(guard_rows, retired)
    _log_write(s, active, missing)
    drift = hb_drift_warning()
    print("## 💓 统一派发心跳报告（三腿·扩检测域·反盲）")
    print()
    print("新鲜度窗口：hook=%d天 · guard=%d天 · patrol=%d天" %
          (HOOK_DAYS, GUARD_DAYS, PATROL_DAYS))
    print()
    print("> 三腿：A=钩子派发 `hooks/.heartbeats/*.heartbeat` ｜ "
          "B=路由组件 `路由家族/.guard/*_last_run.ts` ｜ "
          "C=巡逻 `路由家族/.patrol/*.ts`。")
    if drift:
        print()
        print("> ⚠️ %s" % drift)
    print()
    print("| 源 | 腿 | 状态 | 时效(天) |")
    print("|---|---|---|---:|")
    for r in rows:
        mark = {ST_ON: "✅ 在岗", ST_STALE: "🔴 停摆嫌疑", ST_NONE: "⚪ 无派发记录",
                ST_MISS: "❌ 脚本缺失", ST_BLIND: "🟡 守卫盲区",
                ST_RETIRED: "⚫ 已退役"}.get(r["state"], r["state"])
        age = "—" if r.get("age_days") is None else r["age_days"]
        print("| %s | %s | %s | %s |" % (r["name"], r["leg"], mark, age))
    print()
    if missing:
        print("> ⚠️ **路由组件心跳文件缺失 %s**——`%s` 下无对应 `*_last_run.ts`，"
              "组件可能根本未接线（比冻结更强）。" % (missing, GUARD_DIR))
    if s[ST_MISS]:
        print("> ⚠️ **脚本缺失 %d 个**——注册了但磁盘无文件（硬漂移，"
              "重跑安装即修复）。" % len(s[ST_MISS]))
    if s[ST_RETIRED]:
        print("> ⚫ **已退役 %d 个**——登记于 `.guard/` 同级 `retired_sources.json` 的"
              "**有意退出**源（退役≠健康：前者用意已裁定，后者坏了没人知）。"
              "复活条件见登记表 `revive_when`。" % len(s[ST_RETIRED]))
    if s[ST_STALE]:
        print("> 🔴 **停摆嫌疑 %d 个**——曾留痕、超窗无声。若您近期一直在正常"
              "使用，可能是组件被连坐停摆，建议排查。" % len(s[ST_STALE]))
    if s[ST_BLIND]:
        print("> 🟡 **守卫盲区 %d 个**——机器其他腿在岗（在跑），唯此源零派发记录；"
              "非「刚装完正常」，而是该心跳机制未真正派发（如 hook_protocol 缺失），"
              "建议排查接线。" % len(s[ST_BLIND]))
    if not (s[ST_MISS] or s[ST_STALE] or s[ST_BLIND] or missing):
        print("> ✅ 三腿窗口内全部在岗。")
    return 0


def mode_brief(days, mc):
    beat()
    hook_rows = check_hooks(HOOK_DAYS, find_ledger(mc))
    guard_rows = scan_ts_leg(GUARD_DIR, "*_last_run.ts", GUARD_DAYS, "guard")
    patrol_rows = scan_ts_leg(PATROL_DIR, "*.ts", PATROL_DAYS, "patrol")
    all_rows = hook_rows + guard_rows + patrol_rows
    active = machine_active(all_rows)
    apply_blind(hook_rows, active)
    rows = hook_rows + guard_rows + patrol_rows
    retired = load_retired()
    apply_retired(rows, retired)
    s = _classify(rows)
    missing = missing_expected_guard(guard_rows, retired)
    _log_write(s, active, missing)
    n_on = len(s[ST_ON])
    n_stale = len(s[ST_STALE])
    n_blind = len(s[ST_BLIND])
    n_miss = len(s[ST_MISS])
    n_ret = len(s[ST_RETIRED])
    txt = ("💓 统一心跳: ✅在岗 %d · 🔴停摆嫌疑 %d · 🟡盲区 %d · ❌缺失 %d"
           % (n_on, n_stale, n_blind, n_miss))
    if n_ret:
        txt += " · ⚫已退役 %d" % n_ret
    if n_miss:
        txt += "（缺失=注册未落盘）"
    elif n_stale:
        txt += "（停摆嫌疑=曾留痕现超窗；--report 看明细）"
    elif n_blind:
        txt += "（盲区=机器在跑但此源零派发·非安装正常）"
    if missing:
        txt += " ⚠️路由组件缺失:%s" % ",".join(missing)
    drift = hb_drift_warning()
    if drift:
        txt += " ⚠️" + drift
    print(txt)
    return 0


def mode_selfcheck():
    print("settings.json: %s %s" % (SETTINGS,
          "✅" if os.path.exists(SETTINGS) else "❌"))
    print("HB_DIR(钩子心跳): %s %s" % (HB_DIR,
          "✅" if os.path.isdir(HB_DIR) else "（尚无·钩子首次被派发时自动创建）"))
    print("GUARD_DIR(路由组件心跳): %s %s" % (GUARD_DIR,
          "✅" if os.path.isdir(GUARD_DIR) else "❌缺失"))
    print("PATROL_DIR(巡逻心跳): %s %s" % (PATROL_DIR,
          "✅" if os.path.isdir(PATROL_DIR) else "❌缺失"))
    print("台账: %s" % (find_ledger(None) or "未找到（advisory·L2 证据缺席）"))
    _ret = load_retired()
    print("退役登记: %s %s" % (RETIRED_FILE,
          ("✅ %d 项 %s" % (len(_ret), ",".join(sorted(_ret)))) if _ret
          else "（无·空表）"))
    drift = hb_drift_warning()
    print("漂移绊线: %s" % (drift or "未触发"))
    print("巡检日志: %s" % GUARD_LOG)
    print("用法: guard_heartbeat_check.py [--check|--report|--brief|--selfcheck]"
          " [--days N] [--mc <记忆中心>]")
    return 0


def mode_self_test():
    """⑤腿/CI 回归锁：断言 script_path_of/script_stem 对多平台真实路径形态解析正确。
       防 defect①(2026-10-21 Win反馈)：Windows 引号包裹/含空格钩子路径被抽带前导引号或
       截断 → os.path.exists 恒假 → 全体钩子误判 ST_MISS 硬漂移假红。"""
    cases = [
        ('python3 /home/u/.wb/hooks/route.py', '/home/u/.wb/hooks/route.py', 'route'),
        ('"/usr/bin/python3" /mc/hooks/vgate.py', '/mc/hooks/vgate.py', 'vgate'),
        ('"C:\\Program Files\\python.exe" "C:\\MC\\hooks\\vgate.py"', 'C:\\MC\\hooks\\vgate.py', 'vgate'),
        ('python3 "C:\\Users\\me\\My App\\route.py"', 'C:\\Users\\me\\My App\\route.py', 'route'),
    ]
    bad = []
    for cmd, want_p, want_s in cases:
        gp, gs = script_path_of(cmd), script_stem(cmd)
        if gp != want_p: bad.append('path_of %r -> %r != %r' % (cmd, gp, want_p))
        if gs != want_s: bad.append('stem %r -> %r != %r' % (cmd, gs, want_s))
    if bad:
        print('SELF-TEST RED: 路径解析回归失败(%d/%d)' % (len(bad), len(cases)))
        for b in bad: print('  -', b)
        return 1
    print('SELF-TEST GREEN: script_path_of/script_stem 多平台形态 %d 例全对' % len(cases))
    return 0

def main():
    args = sys.argv[1:]
    days = DEFAULT_DAYS
    if "--days" in args:
        i = args.index("--days")
        if i + 1 < len(args):
            try:
                days = max(1, int(args[i + 1]))
            except ValueError:
                pass
    mc = None
    if "--mc" in args:
        i = args.index("--mc")
        if i + 1 < len(args):
            mc = args[i + 1]
    if "--self-test" in args:
        sys.exit(mode_self_test())
    if "--selfcheck" in args:
        sys.exit(mode_selfcheck())
    if "--report" in args:
        sys.exit(mode_report(days, mc))
    if "--brief" in args:
        sys.exit(mode_brief(days, mc))
    sys.exit(mode_check(days, mc))


if __name__ == "__main__":
    main()
