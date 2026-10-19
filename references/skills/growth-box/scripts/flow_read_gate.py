#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_read_gate.py — 卡B 强制 Read 熔断器（机械形态·⛔不是 prose 提醒）

为什么要有本件：SKILL.md 把流程步骤本体下沉到 references/flow-*.md 后，"读到 flow 文件"
从"整份正文已在上下文里"变成"多一次 Read 动作"——这一步失败就是新的漂移点（卡B 诚实代价条）。
 prose 熔断器（"读不到就中止"）跨端能力不一、靠 AI 自觉，故升级为脚本 exit code 物理拦截
（依 铁律-021② 长流程终检须脚本拦截 + Skill架构规范 §1.1 防误>防错）。

用法：
  python3 flow_read_gate.py                 # 校验四条 flow 装载单齐在位且非空
  python3 flow_read_gate.py --only B        # 只校验单条（步2 逐条迁入时用）
  python3 flow_read_gate.py --degrade-audit # 降级方案行痕迹审计（v1.1·反哺「有痕跳过≠静默跳过」的机械消费者）
  python3 flow_read_gate.py --self-test     # 正例＋负例（缺文件/空文件必须被抓）＋变异检验
退出码：0=通过｜1=有 flow 文件缺失或为空（🔴 对应流程禁止执行，⛔不降级裸奔）｜2=用法错误
诚实边界：本件证明"文件在且非空"，不证明"内容正确"；内容对账由 SKILL 步2 完成证据＋评估器承担。
--degrade-audit 的诚实边界同构：它证明「降级方案行写了可观测输出物」，不证明「降级真会被执行」。
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import sys, os

__version__ = "v1.1"
REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "references")
FLOWS = ("A", "B", "C", "E")
MIN_BYTES = 400          # 低于此长度＝占位未落或半覆盖替换（对齐 铁律-021④"回读整块而非只看命中行"）

DEGRADE_PREFIX = "└─ 降级方案："
DEGRADE_LEGAL = ("输出", "报告", "提示", "标注", "中止", "重新输出", "计入", "补录", "无——", "痕", "落盘")
# 合法形态＝写了可观测痕迹（对话一行提示／落盘标注／明示不可降级）；只写动作名（裸「回退补写」「重试」）＝不合格。
# 立法来源：反哺「有痕跳过≠静默跳过」(2026-07-26) 在 growth-box 自身 3 处未落地，
#           2026-10-12 E7-b 批次回收逮出 ⇒ prose 规则零消费者必漂，升为审计。


def audit_degrade(files=None):
    """扫 SKILL.md＋flow-*.md 的降级方案行，返回 [(文件名, 行号, 原文)] 不合格清单。"""
    home = os.path.dirname(os.path.abspath(__file__))
    if files is None:
        files = [os.path.join(home, os.pardir, "SKILL.md")]
        files += [os.path.join(REF, "flow-%s.md" % f) for f in FLOWS]
    bad = []
    for p in files:
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
            s = line.strip()
            if not s.startswith(DEGRADE_PREFIX):
                continue
            body = s[len(DEGRADE_PREFIX):]
            if not any(k in body for k in DEGRADE_LEGAL):
                bad.append((os.path.basename(p), i, s))
    return bad


def check(flows, min_bytes=None, root=None):
    """min_bytes 默认 None → 运行时读模块全局（⛔不用 `min_bytes=MIN_BYTES` 作默认值——
    默认值在 def 时求值并冻结，改全局测不到，变异检验会假过；本件自己的 MUT 首轮就抓到这条）。"""
    if min_bytes is None:
        min_bytes = MIN_BYTES
    bad = []
    root = root or REF
    for f in flows:
        p = os.path.join(root, "flow-%s.md" % f)
        if not os.path.exists(p):
            bad.append("flow-%s.md 缺失" % f)
            continue
        n = os.path.getsize(p)
        if n < min_bytes:
            bad.append("flow-%s.md 仅 %d 字节（<%d＝疑似空壳/半覆盖）" % (f, n, min_bytes))
    return bad


def _self_test():
    global MIN_BYTES
    import tempfile
    ok = True
    root = tempfile.mkdtemp(prefix="flowgate_")
    for f in FLOWS:
        open(os.path.join(root, "flow-%s.md" % f), "w", encoding="utf-8").write("x" * (MIN_BYTES + 10))
    p1 = check(FLOWS, root=root)
    print("  %s P1 正例：四件齐在且够长 → 通过（bad=%s）" % ("✅" if not p1 else "❌", p1))
    ok &= not p1
    os.remove(os.path.join(root, "flow-C.md"))
    p2 = check(FLOWS, root=root)
    print("  %s N1 负例：删掉 flow-C.md 必须被抓（bad=%s）" % ("✅" if p2 else "❌", p2))
    ok &= bool(p2)
    open(os.path.join(root, "flow-C.md"), "w", encoding="utf-8").write("# 空壳\n")   # N1 已删过，此处重建为"存在但空壳"形态
    p3 = check(FLOWS, root=root)
    print("  %s N2 负例：空壳文件必须被抓（bad=%s）" % ("✅" if p3 else "❌", p3))
    ok &= bool(p3)
    keep = MIN_BYTES
    MIN_BYTES = 1
    p4 = check(("C",), root=root)          # 阈值改坏 → 空壳正例必过（证明判据不是恒真）
    MIN_BYTES = keep
    mutated = (not p4)
    print("  %s MUT 变异：阈值降为 1 后空壳不再被抓（＝该判据真的在起作用）" % ("✅" if mutated else "❌"))
    ok &= mutated
    droot = tempfile.mkdtemp(prefix="flowgate_d_")
    dfile = os.path.join(droot, "d.md")
    D_LINE = "└─ 降级方案："
    open(dfile, "w", encoding="utf-8").write(
        D_LINE + "对话输出 ⚠️ 扫描失败" + chr(10) + D_LINE + "无——阻断门禁不可降级" + chr(10))
    d1 = audit_degrade([dfile])
    print("  %s D-P1 正例：可观测输出／明示不可降级两类均放行（bad=%d）" % ("✅" if not d1 else "❌", len(d1)))
    ok &= not d1
    open(dfile, "a", encoding="utf-8").write(D_LINE + "回退补写" + chr(10))
    d2 = audit_degrade([dfile])
    print("  %s D-N1 负例：裸「回退补写」必须被抓（bad=%d）" % ("✅" if len(d2) == 1 else "❌", len(d2)))
    ok &= len(d2) == 1
    keep_kw = DEGRADE_LEGAL
    globals()["DEGRADE_LEGAL"] = ()          # 判据短路→正例也被抓＝证明判据非恒真
    d3 = audit_degrade([dfile])
    globals()["DEGRADE_LEGAL"] = keep_kw
    print("  %s D-MUT 变异：关键词集清空后 3 行全被抓（＝该判据真的在起作用）" % ("✅" if len(d3) == 3 else "❌"))
    ok &= len(d3) == 3
    print("✅✅ --self-test 全过" if ok else "❌ --self-test 有项不过")
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if "--self-test" in a:
        return _self_test()
    if "--degrade-audit" in a:
        bad = audit_degrade()
        if bad:
            print("❌ 降级方案痕迹审计：%d 行只写动作名、无可观测输出物" % len(bad))
            for f, ln, s in bad:
                print("   · %s:%d %s" % (f, ln, s))
            print("   → 补法：写明降级时打哪一行提示／落哪一处痕迹（例：对话输出 ⚠️…／标注🟡降级／计入 drafts/）")
            return 1
        print("✅ 降级方案痕迹审计通过（SKILL＋flow 四件：各降级分支均写了可观测输出物或明示不可降级）")
        return 0
    flows = FLOWS
    if "--only" in a:
        i = a.index("--only")
        if i + 1 >= len(a):
            print("error: --only 后须跟流程字母 A/B/C/E", file=sys.stderr); return 2
        flows = tuple(x for x in a[i + 1].upper() if x in FLOWS)
        if not flows:
            print("error: --only 取值非法（须 A/B/C/E）", file=sys.stderr); return 2
    bad = check(flows)
    if bad:
        print("❌ 强制 Read 熔断器：flow 装载单不合格 → 对应流程 🔴 禁止执行（⛔不降级裸奔）")
        for b in bad:
            print("   ·", b)
        print("   → 回到 SKILL.md 步2 补齐该流程正文（本件只证「在且非空」，不证内容正确）")
        return 1
    print("✅ flow 装载单在位（%s·各 ≥%d 字节）— 熔断器放行" % ("/".join(flows), MIN_BYTES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
