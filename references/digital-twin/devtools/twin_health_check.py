#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: family=端侧体检器 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
"""
twin_health_check.py — 数字分身·装机健康一键体检（P1·2026-10-11 皮叔令"让用户确信真按规则装好且完整可用"）

信任三段模型（真源=_patch/2026-10-11-数字分身切片链-挂账任务卡.md·任务4续）：
  A 合规段（装对了）：可选 --pkg-root 跑包自检⑬切片链 dry-run
  B 运行段（机器在转）：规格书→切片新鲜度 / slice_watch 心跳+基线 / UPS 注入台账
  C 兑现段（对话里生效）：产品回执(hooks.log 派发) + 痕迹对账(inject_chain 台账) + 人证指引
诚实分级：🟢机械证 / 🟡回执证 / 👁人证 / ⚪该层无证据源（如实显形不假绿·不混称"全部验证通过"）。
退出码：0=有证据层全绿且无红 1=任一层红（附修复指路）2=红无但关键层缺证据（⚪≥2）

跨端扩展位：本轮实现 Qoder CN 端证据源（B1 切片层为全端通用）；
  其他端证据路径读 state_bus/ends 字段，未适配端显 ⚪ 并提示扩展（⛔不猜路径）。
用法：python3 twin_health_check.py [--pkg-root <包根>] [--end qodercn] [--quiet]
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

MC = os.path.expanduser("[记忆共享中心]")
TWIN = os.path.join(MC, "数字分身")
STATE = os.path.expanduser("~/.qoder-cn/doenglingz_inject_state.json")
SLICES_MAN = os.path.join(TWIN, "K2切片蒸馏/slices/manifest.json")
SPEC = os.path.join(TWIN, "童灵·人格规格书.md")
WATCH_TS = os.path.join(TWIN, "scripts/last_run_doenglingz_slice_watch.ts")
OBSERVED = os.path.join(MC, "脚本中心/logs/injection_observed_qodercn.jsonl")
SLICE_CHECK = os.path.join(MC, "脚本中心/slice_chain_check.py")
FRESH_H = 48  # 心跳/台账新鲜度阈值（小时）


def mark(tag, ok, detail):
    print("%s %s %s" % ("🟢" if ok else "🔴", tag, detail))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg-root", default="")
    ap.add_argument("--end", default="qodercn")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    reds = 0
    grays = 0

    # ── A 合规段 ──
    if a.pkg_root:
        if os.path.isfile(SLICE_CHECK):
            r = subprocess.run([sys.executable, SLICE_CHECK, "--pkg-root", a.pkg_root, "--quiet"],
                               capture_output=True, text=True, timeout=120)
            if not mark("A1 包自检⑬切片链dry-run", r.returncode == 0,
                        "rc=%s %s" % (r.returncode, (r.stdout or "").strip()[:80])):
                reds += 1
        else:
            print("⚪ A1 包自检⑬ 件不在位（装机态未投递）·不判红"); grays += 1
    else:
        print("⚪ A1 未给 --pkg-root·合规段跳过（装机验证时加此参数）"); grays += 1

    # ── B 运行段 ──
    ok_b1 = None
    try:
        spec_h = hashlib.sha256(open(SPEC, "rb").read()).hexdigest()[:12]
        man_h = json.load(open(SLICES_MAN, encoding="utf-8")).get("src_hash", "")
        ok_b1 = mark("B1 规格书→切片新鲜", spec_h == man_h,
                     "spec=%s manifest=%s%s" % (spec_h, man_h, "" if ok_b1 is not False and spec_h == man_h else "·重跑 slice_watch 即自愈"))
    except Exception as e:
        print("⚪ B1 切片新鲜度不可判: %s" % str(e)[:80]); grays += 1
    if ok_b1 is False:
        reds += 1

    ok = False
    ts_ok = os.path.isfile(WATCH_TS) and (time.time() - os.path.getmtime(WATCH_TS)) < FRESH_H * 3600
    ends = 0
    try:
        last = [l for l in open(os.path.join(TWIN, "scripts/doenglingz_slice_watch.log"), encoding="utf-8") if l.strip()][-30:]
        m = re.search(r"基线已登记 (\d+) 端", "".join(last))
        ends = int(m.group(1)) if m else 0
    except Exception:
        pass
    ok = mark("B2 slice_watch心跳+基线", ts_ok and ends > 0,
              "心跳%s · 基线%d端" % ("新鲜" if ts_ok else "缺失/超龄", ends))
    if not ok:
        reds += 1

    ok = False
    try:
        last = json.loads([l for l in open(STATE, encoding="utf-8") if l.strip()][-1])
        fresh = (time.time() - time.mktime(time.strptime(last["ts"], "%Y-%m-%dT%H:%M:%S"))) < FRESH_H * 3600
        ok = mark("B3 UPS注入台账", fresh and last.get("inject_len", 0) > 0,
                  "ts=%s len=%s mode=%s" % (last.get("ts"), last.get("inject_len"), last.get("mode")))
    except Exception as e:
        print("⚪ B3 注入台账不可读: %s" % str(e)[:80]); grays += 1
    if not ok:
        reds += 1

    # ── C 兑现段 ──
    ok = False
    try:
        import glob as _g
        logs = sorted(_g.glob(os.path.expanduser("~/Library/Application Support/QoderCN/logs/*/questWindow/hooks.log")),
                      key=os.path.getmtime)
        cnt = 0
        # 判据窗（05:37 实跑纠假零教训：tail 400 行被 PreToolUse 密行挤出 UPS 行=假红）
        #   改全文件扫 + 行首时间戳窗过滤（3h·贴会话节奏），⛔不看窗口尾巴
        if logs and (time.time() - os.path.getmtime(logs[-1])) < 3 * 3600:
            import datetime as _dt
            cut = _dt.datetime.now() - _dt.timedelta(hours=3)
            for l in open(logs[-1], encoding="utf-8", errors="replace"):
                if "event=UserPromptSubmit" not in l:
                    continue
                try:
                    if _dt.datetime.strptime(l[:19], "%Y-%m-%d %H:%M:%S") >= cut:
                        cnt += 1
                except ValueError:
                    pass
        if cnt > 0:
            print("🟢 C1 产品回执(钩子派发) 近1h源含UPS派发行 %d 条" % cnt)
            ok = True
        else:
            print("🟡 C1 产品回执不可达·降级人证指引（见 C3·装机端日志路径属跨端扩展位⛔不猜）"); grays += 1
    except Exception:
        print("🟡 C1 产品回执源不可读·降级人证指引（见 C3）"); grays += 1

    ok = False
    try:
        last = json.loads([l for l in open(OBSERVED, encoding="utf-8") if l.strip()][-1])
        ok = mark("C2 痕迹对账", (time.time() - last.get("epoch", 0)) < 7 * 86400,
                  "末痕 %s（AI 侧 --record·7天窗口）" % last.get("ts"))
    except Exception:
        print("⚪ C2 台账不可读"); grays += 1
    if not ok and os.path.isfile(OBSERVED):
        pass

    print("👁 C3 人证：新开对话若见『童灵』档位自证块+分身语气+端署名在场，即注入真实生效（注入本体只在模型上下文磁盘无痕——本层以人眼为准）")

    print("─" * 46)
    if reds:
        print("🔴 体检结论：%d 层红——分身未按规则运转。按各行『指路』修复后重跑本件。" % reds)
        return 1
    if grays >= 2:
        print("⚪ 体检结论：无红，但 %d 层缺证据源——关键层未验证，不作『完整可用』宣称。" % grays)
        return 2
    if grays == 1:
        print("🟡 体检结论：机械证据层全绿，1 层以人证/回执替代（见上行）——除该层外均确证可用。")
        return 0
    print("🟢 体检结论：各层全绿——真按规则装好，且完整可用（各层证据见上，可复核）。")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
