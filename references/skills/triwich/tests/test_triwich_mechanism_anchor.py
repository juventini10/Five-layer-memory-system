#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_triwich_mechanism_anchor.py v1.0.0 —— triwich_seal v1.5.0「G2 机制回访物理锚」夹具

治什么：resolve 的 --mechanism 原先只校验枚举，AI 自报即得分 ⇒ A 值（已回访中 mechanism 占比）
可被自我拔高，违反自家规范判据 13「判据制定者≠执行者」。v1.5.0 起须由 followup 留痕做外部锚。

十一例 A1-A11（正例1+拒写族A2-A5+不误伤族A6；A7-A11 为后续扩容族见代码注释锚·v4.5.1计数追正,旧"六例"系扩容前遗留）：
  A1 无留痕 → 标 mechanism 必须被拒（正例·能红）
  A2 followup 跑过且 seq 在命中列表内 → 放行，卡头落 发起方式:mechanism
  A3 seq 不在最近一次留痕内（如留痕后又新登记一张卡）→ 拒
  A4 留痕超新鲜度窗（>MECHANISM_MAX_AGE_HOURS）→ 拒
  A5 如实标 manual → ⛔不受锚约束（诚实降级不许被惩罚，否则逼人假标 mechanism）
  A6 留痕为坏 JSON 行 → 拒（Fail-Closed·仪器坏了朝拒不朝放）
出厂动作（判据 13/14 同源纪律）：变异测试——把锚校验改成恒真后跑 A1/A3/A4，必须变红，
  证明本夹具「有牙」而非恒绿。⛔ 不得只以本文件 PASS 作为判据有效的证据。

用法：env -u PYTHONHOME -u PYTHONPATH python3 test_triwich_mechanism_anchor.py [--mutation]
退出码：0=全绿 1=有红（含变异测试未变红=夹具有缺陷）
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
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SEAL = os.path.join(HERE, "..", "scripts", "triwich_seal.py")

FALSIFY_LINE = "- 判假方式：夹具内不判定\n"

CARD = """## FU-{seq} · 状态:待回访
- 任务：夹具卡 {seq}
- 深度：L1
- 预测：X
- 到期日：2099-01-01
- 到期默认：no-op：夹具不动作
""" + FALSIFY_LINE + """- 登记：2026-01-01 00:00:00 · 发起方式:机制封口自动登记 · 会话:fixture:aaa
- 实际：（待回访）
- 偏差类型：（待回访）
- 归因：（待回访）
- 修正动作：（待回访）
"""


def load_seal(room, ledger):
    spec = importlib.util.spec_from_file_location("ts_fixture", SEAL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.DECISION_ROOM_PATH = room
    m.FOLLOWUP_LEDGER = ledger
    return m


def resolve_kw(m, seq, mech):
    return m.resolve(str(seq), {"actual": "A", "bias": "B0", "cause": "C", "fix": "F", "mechanism": mech})


def run_cases(label):
    tmp = tempfile.mkdtemp(prefix="ts_anchor_")
    room = os.path.join(tmp, "decision-room.md")
    ledger = os.path.join(tmp, "followup_ledger.log")
    results = []
    try:
        # A1：无留痕 → mechanism 必拒
        open(room, "w", encoding="utf-8").write(CARD.format(seq=1))
        m = load_seal(room, ledger)
        code, msg = resolve_kw(m, 1, "mechanism")
        results.append(("A1 无留痕标 mechanism → 拒（正例·能红）", code == 1 and "物理锚" in msg, "code=%d %s" % (code, msg[:60])))

        # A2：followup 留痕含该 seq → 放行
        open(ledger, "w", encoding="utf-8").write(json.dumps(
            {"ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "count": 1, "seqs": ["1"]}) + "\n")
        code, msg = resolve_kw(m, 1, "mechanism")
        head_ok = "状态:已回访" in open(room, encoding="utf-8").read() and "发起方式:mechanism" in open(room, encoding="utf-8").read()
        results.append(("A2 留痕命中 seq → 放行且卡头记 mechanism", code == 0 and head_ok, "code=%d %s" % (code, msg[:60])))

        # A3：留痕里没有这张卡（登记后没重跑 followup）→ 拒
        open(room, "a", encoding="utf-8").write("\n" + CARD.format(seq=2))
        code, msg = resolve_kw(m, 2, "mechanism")
        results.append(("A3 seq 不在窗口内任一次留痕 → 拒（防「登记完直接自标」）", code == 1 and "不在窗口内任一次" in msg, "code=%d %s" % (code, msg[:70])))

        # A4：留痕超新鲜度窗 → 拒
        old = (datetime.now() - timedelta(hours=m.MECHANISM_MAX_AGE_HOURS + 3)).strftime("%Y-%m-%dT%H:%M:%S")
        open(ledger, "w", encoding="utf-8").write(json.dumps({"ts": old, "count": 1, "seqs": ["2"]}) + "\n")
        code, msg = resolve_kw(m, 2, "mechanism")
        results.append(("A4 留痕超 %dh 窗 → 拒（防「半年前跑过一次」长期有效）" % m.MECHANISM_MAX_AGE_HOURS,
                        code == 1 and "新鲜度窗" in msg, "code=%d %s" % (code, msg[:70])))

        # A5：如实标 manual → 不受锚约束（无留痕也放行）
        open(ledger, "w", encoding="utf-8").write("")
        code, msg = resolve_kw(m, 2, "manual")
        results.append(("A5 如实标 manual → 放行（诚实降级不受罚·⛔不逼人假标）", code == 0, "code=%d %s" % (code, msg[:60])))

        # A6：坏留痕行 → 拒
        open(ledger, "w", encoding="utf-8").write("{坏 JSON\n")
        open(room, "w", encoding="utf-8").write(CARD.format(seq=3))
        code, msg = resolve_kw(m, 3, "mechanism")
        results.append(("A6 留痕坏行 → 拒（Fail-Closed·仪器坏朝拒）", code == 1, "code=%d %s" % (code, msg[:70])))

        # A7：followup_list 本身会落留痕（机制自证·不靠 AI 手写）
        os.remove(ledger)
        open(room, "w", encoding="utf-8").write(CARD.format(seq=4))
        m.followup_list()
        wrote = os.path.exists(ledger) and "4" in open(ledger, encoding="utf-8").read()
        results.append(("A7 followup 运行即自动留痕（外部锚由脚本产·AI 零构造权）", wrote, ""))

        # A8：并发遮蔽反例——最近一行不含本 seq，但窗口内早一行含 → 仍须放行
        #     （多端/多窗共用一台机器时，别人一次不同范围的筛查不得把自己的锚点挤掉）
        open(room, "w", encoding="utf-8").write(CARD.format(seq=5))
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        earlier = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        with open(ledger, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": earlier, "count": 1, "seqs": ["5"]}) + "\n")
            f.write(json.dumps({"ts": now, "count": 1, "seqs": ["77"]}) + "\n")  # 别人的筛查盖在后面
        code, msg = resolve_kw(m, 5, "mechanism")
        results.append(("A8 最近一行不含本 seq 但窗内早先命中 → 仍放行（防并发遮蔽）", code == 0, "code=%d %s" % (code, msg[:70])))

        # A9：全部留痕超龄 → 拒（加固后不得退化成"历史上出现过一次就算"）
        old_ts = (datetime.now() - timedelta(hours=m.MECHANISM_MAX_AGE_HOURS + 5)).strftime("%Y-%m-%dT%H:%M:%S")
        open(room, "w", encoding="utf-8").write(CARD.format(seq=6))
        with open(ledger, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": old_ts, "count": 1, "seqs": ["6"]}) + "\n")
            f.write(json.dumps({"ts": old_ts, "count": 1, "seqs": ["6"]}) + "\n")
        code, msg = resolve_kw(m, 6, "mechanism")
        results.append(("A9 两行留痕全部超龄 → 拒（新鲜度仍硬）", code == 1 and "无一在" in msg, "code=%d %s" % (code, msg[:70])))

        # A10/A11：筛查必须把"无判假式"的存量卡显形（v1.4.1 硬门禁之前的老卡没这行→旧代码静默通过）
        # 删行引用 CARD 里的原文（FALSIFY_LINE）——改 fixture 时判据自动跟着动，不留第二份字符串
        seed = CARD.format(seq=7)
        nocard = seed.replace(FALSIFY_LINE, "", 1)
        open(room, "w", encoding="utf-8").write(nocard + "\n" + CARD.format(seq=8))
        _c, out = m.followup_list()
        lines = out.split(" · ")
        nolaw = [x for x in lines if "FU-7「" in x]
        withlaw = [x for x in lines if "FU-8「" in x]
        results.append(("A10 无判假方式的存量卡 → 筛查显形弱判据（不再静默绿）",
                        bool(nolaw) and "无判假式" in nolaw[0], str(nolaw)[:120]))
        results.append(("A11 有判假方式的卡 → 不误标（只数该数的）",
                        bool(withlaw) and "无判假式" not in withlaw[0], str(withlaw)[:120]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = 0
    for name, good, detail in results:
        ok += bool(good)
        print("  %s %s%s" % ("✅" if good else "❌", name, "" if good else "  ← " + detail))
    return ok, len(results)


MUTANTS = [
    # (说明, 原样行, 变异行)
    ("锚校验短路（G2 A 值物理锚被短路）",
     '        ok, why = _mechanism_anchored(seq)\n',
     '        ok, why = True, "变异：锚校验被短路"\n'),
    ("弱判据显形短路（无判假式不再显形）",
     '        if not it["falsify"]:\n',
     '        if False:\n'),
]


def mutation():
    """出厂动作：逐条判据各造一个变异体——判据被短路时对应夹具必须变红。

    全绿的变异体＝该判据无夹具证据（恒真夹具），因此每个变异体都必须出现红项。
    """
    src = open(SEAL, encoding="utf-8").read()
    all_ok = True
    for label, old, new in MUTANTS:
        mutated = src.replace(old, new, 1)
        if mutated == src:
            print("  ❌ 变异未生效（%s）——原样行未命中，夹具证据不成立" % label)
            all_ok = False
            continue
        tmp = tempfile.mkdtemp(prefix="ts_mut_")
        mpath = os.path.join(tmp, "triwich_seal_mut.py")
        open(mpath, "w", encoding="utf-8").write(mutated)
        globals()["SEAL"] = mpath
        print("\n  ── 变异体：%s" % label)
        try:
            ok, tot = run_cases("变异体")
            red = ok < tot
            all_ok = all_ok and red
            print("  变异体结果：%d/%d 绿 ⇒ %s" % (ok, tot,
                  "❌ 该判据无夹具证据（短路仍全绿=恒真夹具）" if not red else
                  "✅ 判据可证伪（短路后出现红项·夹具有牙）"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            globals()["SEAL"] = SEAL
    return 0 if all_ok else 1


def main():
    if "--mutation" in sys.argv:
        return mutation()
    print("=== triwich_seal v1.5.0 G2 机制回访物理锚 夹具 ===")
    ok, tot = run_cases("线上本体")
    print("自测 %d/%d %s" % (ok, tot, "全绿" if ok == tot else "有红"))
    print("提示：出厂动作=再跑 `--mutation` 证明本夹具可证伪（判据被短路时必须变红）")
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main())
