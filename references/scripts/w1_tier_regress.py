#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""w1_tier_regress.py v1.0（2026-10-07 童灵D3·假触发根治轮·预注册判据先行·铁律-020/S875）
引擎本体回归网：直接 import doenglingz_inject_prompt.w1_fired 跑判组。
用例来源全绑实录：POS=真召唤应上岗；NEG=被谈论的召唤应静默。
预注册期望（改动写下前锁定）：
  - n2「没有说启动童灵」引用式、n3「要启动成长箱…么？」是非问句形 = 本轮两假触发实录，修复前应红
  - p3 09-23 判例、p1/p2 肯定式口令 修复后必须仍绿（防矫枉过正）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import importlib.util, os, sys

# ── 被测脚本路径解析（2026-10-08·判据=verifier_target_fidelity_guard 路径保真）──
# 病根：原式硬编码 `[记忆共享中心]/脚本中心/...` ⇒ 换落点/多端时测到另一份，回归器仍可能报全绿。
# 判据：脚本 TARGET 必须解析自 runtime_paths；降级按候选探测 + stderr 显形。
def _resolve_devtools(name):
    import json as _json
    base = None
    rp = os.path.expanduser("~/.hermes/doenglingz/runtime_paths.json")
    if os.path.isfile(rp):
        try:
            with open(rp, encoding="utf-8") as fh:
                base = _json.load(fh).get("devtools")
        except Exception:
            base = None
    cands = []
    if base:
        cands.append(os.path.join(base, name))
    cands.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), name))
    for c in cands:
        if os.path.isfile(c):
            return c
    sys.stderr.write("[w1_tier_regress][WARN] 未定位 %s\n" % name)
    return cands[0]


ENG = _resolve_devtools("doenglingz_inject_prompt.py")
spec = importlib.util.spec_from_file_location("dg", ENG)
dg = importlib.util.module_from_spec(spec)
sys.argv = ["dg"]
spec.loader.exec_module(dg)

POS = [
    ("p1", "启动童灵"),
    ("p2", "启动成长箱，检查晋升"),
    ("p3", "我的指令是启动童灵，不应该是D3了吗？还显示D1干嘛？"),   # 09-23 判例
    ("p4", "那童灵，你有什么收获吗？"),                              # 直呼
    ("p5", "启动童灵吧，把这单干完"),
    ("p6", "用童灵审一下这个方案"),
]
NEG = [
    ("n1", "这一轮的对话我没有启动童灵啊，怎么又出TSL了"),            # 10-01 v1.14 锚
    ("n2", "首先第一个我不等了执行吧；为什么我的指令没有说启动童灵，但是你走了童灵D3的流程呢？是真触发还是假触发"),  # 10-07 实录·引述式
    ("n3", "什么意思？意思是要启动成长箱走E流程么？2、这个又是什么操作？"),  # 10-07 实录·是非问
    ("n4", "我和童灵儿聊了几句"),
    ("n5", "讨论：现在基于童灵的特性，是不是封装成 Skill 是最好的选择？"),
    # ── 2026-10-08 预注册（你质证「我没明确说启动童灵，你还是启动了」·v1.23 假触发根治轮）──
    # 分母 11→15；改动前先锁期望（铁律-020）。四类根因各一条：
    ("n6", "帮我看下童灵的设计"),            # 根因A：⑤宽松匹配命中高频动词「帮我」·动词不指向童灵
    ("n7", "我想了解一下童灵"),              # 根因B：③句中直呼把句尾宾语位当呼唤
    ("n8", "我不打算用童灵"),                # 根因C：②否定窗口只查前2字·「不打算」跨词否定漏网
    ("n9", "童灵暂时不用"),                  # 根因D：W1_VERBS 含单字「用」·否定语境亦命中
    ("n10", "童灵的人格切片在哪"),           # 根因E：句尾宾语位·属性问句（补边界·防矫枉过正）
]
POS_EXTRA = [
    # ── 2026-10-08 预注册：明确上岗口令漏触发（W1_TRIGGERS 缺「童灵上岗」）──
    ("p7", "童灵上岗"),
]
def main():
    bad = 0
    for tag, p in POS + POS_EXTRA:
        got = dg.w1_fired(p)
        if got is not True: bad += 1
        print(("✅" if got else "❌"), tag, "期望上岗", "实跑", got)
    for tag, p in NEG:
        got = dg.w1_fired(p)
        if got is not False: bad += 1
        print(("✅" if not got else "❌"), tag, "期望静默", "实跑", got)
    print("结果:", "全绿" if bad == 0 else "%d 红" % bad)
    return 1 if bad else 0
if __name__ == "__main__":
    sys.exit(main())
