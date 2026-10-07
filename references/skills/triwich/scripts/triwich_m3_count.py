#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triwich_m3_count.py —— 三明智 M3 数据门机械计数（单一显示源）

口径（唯一裁决口径 = decision-room.md「三账分工口径表」#1·2026-09-16 L2 裁决固化）：
  M3 数据门分母（"≥20 条"数什么）= decision-room 决策卡**有效登记数**
  = `^## FU-` 条目总数 − 状态行含「作废」的条目（误封口作废声明不占计数）
  ⛔ 不数采样台账编号、不数 seal 链长——引用台账编号或链长宣称 M3 进度=口径错误（FU-12 裁决先例）。

用法：
  python3 triwich_m3_count.py            # 实时计数（口径+达成度）
  python3 triwich_m3_count.py --detail   # 追加作废/待回访明细
  python3 triwich_m3_count.py --json     # 机器可读（供面板/守卫消费）

退出码：0（只读计数·不判定达标与否——判定门规则在进度看板§五）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import sys

HOME = os.path.expanduser("~")
DECISION_ROOM = os.environ.get("TRIWICH_DECISION_ROOM") or os.path.join(
    HOME, "[记忆共享中心]/技能配置/triwich/references/decision-room.md"
)  # v4.4.9·R1-P3-07：与 seal 同 env 口——计数与登记两本账的口子关闭
M3_THRESHOLD = 20
FU_HEAD_RX = re.compile(r"^## FU-(\d+)\s*·\s*状态:([^·\n]+)", re.MULTILINE)
VOID_KW = "作废"


def load_fu(path=DECISION_ROOM):
    """返回 [(seq, status_line), ...] 按文件出现顺序。"""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    return [(int(m.group(1)), m.group(2).strip()) for m in FU_HEAD_RX.finditer(text)]


def count():
    if not os.path.isfile(DECISION_ROOM):
        return {"error": f"decision-room 不可达: {DECISION_ROOM}"}
    fuses = load_fu()
    total = len(fuses)
    void = [s for _, s in fuses if VOID_KW in s]
    valid = total - len(void)
    pending = [s for _, s in fuses if "待回访" in s and VOID_KW not in s]
    return {
        "口径": "decision-room 有效登记数（三账分工口径表#1·FU条目−作废）",
        "FU条目总数": total,
        "作废条目": len(void),
        "作废明细": [f"FU-{i}" for i, s in fuses if VOID_KW in s],
        "有效登记": valid,
        "阈值": M3_THRESHOLD,
        "达成": valid >= M3_THRESHOLD,
        "待回访": len(pending),
        "文件": DECISION_ROOM,
    }


def main():
    args = sys.argv[1:]
    res = count()
    if "error" in res:
        print(res["error"])
        return 1
    if "--json" in args:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
    print(f"📊 三明智 M3 数据门（口径=decision-room 有效登记数·三账分工口径表#1）")
    print(f"   FU 条目总数：{res['FU条目总数']}")
    if res["作废条目"]:
        print(f"   作废条目：{res['作废条目']}（{'/'.join(res['作废明细'])}·不占计数）")
    print(f"   有效登记：{res['有效登记']} / {res['阈值']} → "
          f"{'✅ 已达标（M3 数据门过·可触发 G2 判定）' if res['达成'] else '⛔ 未达标（继续采集中·满 20 当日机制触发 G2）'}")
    if "--detail" in args:
        print(f"   待回访：{res['待回访']} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
