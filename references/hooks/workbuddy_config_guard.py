#!/usr/bin/env python3
# version: v1.0.0
"""WorkBuddy 端配置活性守卫（端薄适配器·对齐 zcode_config_guard / qodercn_config_guard 族）。

## 存在理由（§二·七·〇 动作 3「先查可复用」）

族内 ZCode / Qoder CN 各有 config_guard，**WB 端没有**——
而 WB 是**挂载最重的一端**（settings.json 实挂 46+ 条 Hook）。

## 为什么需要它（ZCode 端实证同款病）

客户端/宿主会**重写**配置文件：改一次设置 → 整份 settings.json 被覆写 →
部分 Hook 挂载被吃掉，**症状是"守卫悄悄不跑了"且零报错**。
⇒ 判据=**BASELINE 对账**：挂载条目集合与基线比，少一条即 RED。

## 检测项

| # | 项 | 级别 |
|:-:|---|:--:|
| 1 | 挂载条目较基线**减少**（被重写吃掉） | RED |
| 2 | 挂载条目较基线**增加**（漂移·可能是他端添的） | WARN |
| 3 | 命令目标脚本消失（挂了但文件没了） | RED |
| 4 | 无基线（首次运行） | ⚪ 引导 |

## 纪律

- 报告制 exit 0（`--strict` RED 才 1）
- 端隔离：基线落 `~/.workbuddy/` 本端域·⛔ 不写他端
- `--update-baseline` 显式重建基线（⛔ 不自动重建——自动重建=永远对账不响）
- `--self-test` 临时夹具（含变异：删一条挂载必须被抓）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".workbuddy", "settings.json")
BASELINE = os.path.join(HOME, ".workbuddy", "hooks", ".baseline_hooks.json")


def _mounted(cfg: dict):
    """派生挂载条目集合（事件·命令）·⛔ 不手抄清单。"""
    out = set()
    for ev, items in (cfg.get("hooks") or {}).items():
        for it in items:
            for h in (it.get("hooks") or []):
                c = h.get("command", "")
                if c:
                    out.add((ev, c.strip()))
    return out


def check(settings_path: str = SETTINGS, baseline_path: str = BASELINE):
    rep = {"version": VERSION, "ts": datetime.now().isoformat(timespec="seconds"),
           "settings": settings_path, "baseline": baseline_path,
           "mounted": 0, "findings": [], "red": 0, "warn": 0}
    add = lambda lv, k, d: rep["findings"].append(
        {"level": lv, "kind": k, "detail": d})

    if not os.path.isfile(settings_path):
        add("RED", "settings_missing", f"配置不存在：{settings_path}")
        rep["red"] = 1
        return rep
    try:
        cfg = json.load(open(settings_path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        add("RED", "settings_unreadable", f"配置不可解析：{e}")
        rep["red"] = 1
        return rep

    now = _mounted(cfg)
    rep["mounted"] = len(now)

    # ③ 命令目标脚本消失（与基线无关·硬判据）
    for ev, c in sorted(now):
        m = c.split()
        for tok in m:
            if tok.endswith(".py") or tok.endswith(".sh"):
                p = os.path.expanduser(tok)
                if os.path.isabs(p) and not os.path.exists(p):
                    add("RED", "target_missing",
                        f"挂载目标不存在：[{ev}] {os.path.basename(p)}")
                break

    # ①② BASELINE 对账
    if not os.path.isfile(baseline_path):
        add("WARN", "no_baseline",
            "无基线·首次运行请执行 --update-baseline 建立（⛔不自动建）")
    else:
        try:
            base = set(tuple(x) for x in json.load(
                open(baseline_path, encoding="utf-8"))["mounted"])
        except (OSError, json.JSONDecodeError, KeyError) as e:
            add("RED", "baseline_unreadable", f"基线不可解析：{e}")
            base = set()
        if base:
            for ev, c in sorted(base - now):
                add("RED", "mount_lost",
                    f"挂载丢失（疑似被客户端重写吃掉）：[{ev}] "
                    f"{os.path.basename(c.split()[0]) if c.split() else c}")
            for ev, c in sorted(now - base):
                add("WARN", "mount_added",
                    f"新增挂载（漂移·确认是否有意）：[{ev}] "
                    f"{os.path.basename(c.split()[0]) if c.split() else c}")

    rep["red"] = sum(1 for f in rep["findings"] if f["level"] == "RED")
    rep["warn"] = sum(1 for f in rep["findings"] if f["level"] == "WARN")
    return rep


def update_baseline(settings_path: str = SETTINGS,
                    baseline_path: str = BASELINE) -> int:
    cfg = json.load(open(settings_path, encoding="utf-8"))
    m = sorted(_mounted(cfg))
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    payload = {"version": VERSION,
               "ts": datetime.now().isoformat(timespec="seconds"),
               "settings": settings_path, "count": len(m),
               "sha": hashlib.sha256(
                   json.dumps(m, ensure_ascii=False).encode()).hexdigest()[:12],
               "mounted": [list(x) for x in m]}
    json.dump(payload, open(baseline_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"BASELINE 已建立：{len(m)} 条 · sha={payload['sha']} → {baseline_path}")
    return 0


def _self_test() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        sp = os.path.join(td, "settings.json")
        bp = os.path.join(td, "baseline.json")
        ghost = os.path.join(td, "__ghost__.py")
        real = os.path.join(td, "real.py")
        open(real, "w").write("# ok\n")
        json.dump({"hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": f"python3 {ghost}"}]}]}},
            open(sp, "w"))
        r0 = check(sp, bp)
        kinds0 = {f["kind"] for f in r0["findings"]}
        print(f"  无基线检出：{sorted(kinds0)}")
        ok &= ("no_baseline" in kinds0 and "target_missing" in kinds0)

        # 建基线改用真实存在的目标（target_missing 腿由上面单独验过）
        json.dump({"hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": f"python3 {real}"}]}]}},
            open(sp, "w"))
        update_baseline(sp, bp)
        r1 = check(sp, bp)
        drift = [f for f in r1["findings"]
                 if f["kind"] in ("mount_lost", "mount_added")]
        print(f"  建基线后：RED={r1['red']} WARN={r1['warn']} "
              f"漂移={len(drift)} 条 {'✓' if not drift else '✗'}")
        ok &= (r1["red"] == 0 and not drift)

        # 变异：删一条挂载 ⇒ 必须被抓
        json.dump({"hooks": {}}, open(sp, "w"))
        r2 = check(sp, bp)
        lost = [f for f in r2["findings"] if f["kind"] == "mount_lost"]
        print(f"  删挂载变异：mount_lost={len(lost)} 条 "
              f"{'✓' if lost else '✗'}")
        ok &= bool(lost)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="WorkBuddy 端配置活性守卫")
    ap.add_argument("--settings", default=SETTINGS)
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return _self_test()
    if a.update_baseline:
        return update_baseline(a.settings, a.baseline)

    rep = check(a.settings, a.baseline)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"WorkBuddy 配置活性 · {rep['ts']} · {VERSION}")
        print(f"  配置：{rep['settings']} · 实挂 {rep['mounted']} 条")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    if a.strict and rep["red"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
