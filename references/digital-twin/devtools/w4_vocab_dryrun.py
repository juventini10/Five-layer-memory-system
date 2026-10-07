#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""w4_vocab_dryrun.py — W4 人格层词表 dry-run 校准器（铁律-020）

用途：W4（童灵人格层三档注入）词表上线前的命中分布校准。
纪律：
  · 只读——不写任何文件、不改任何配置（纯 dry-run）
  · 词表变更须重跑本工具，人工看误召样本再落地（铁律-020）
  · 语料真实度分层输出——不把近似语料的数字冒充真实分布

背景（2026-09-13 实盘）：
  本端 **不落盘用户 prompt 原文**（~/.workbuddy/chat-history 不存在；workbuddy.db
  sessions 表仅元数据无正文）⇒ 依赖 prompt 语料的历史 dry-run 在本端不可得。
  故本工具双源并用：源A=可提供的真实 prompt（人填）·源B=系统日志摘要（近似）。
  长期数据由 W4 observe 模式采样台账承接（运行时校准 > 一次性 dry-run）。

用法：
  python3 w4_vocab_dryrun.py                  # 双源全跑
  python3 w4_vocab_dryrun.py --prompts FILE   # 源A 换成文件（每行一条）
  python3 w4_vocab_dryrun.py --days 14        # 源B 语料天数
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import sys
import glob

BASE = os.path.expanduser("[记忆共享中心]")
LOG_DIR = os.path.join(BASE, "工作日志/系统日志")

# ═══════════════════════════════════════════════════════════
# W4 词表 v0.1（候选·待 dry-run 校准 · 复合窄词优先·禁裸高频词）
# ═══════════════════════════════════════════════════════════
VOCAB = {
    "guard": {  # 守护档 → PB-01~04 补丁 + 性情底色
        "PB-01_方案漏洞": ["有没有漏洞", "你看行不行", "这么干行", "就这么定", "有把握吗", "哪里有问题"],
        "PB-02_资源消费": ["要不要买", "值不值", "预算", "花钱", "订阅", "续费", "开会员", "采购", "买台", "买一个"],
        "PB-03_赶时间":   ["赶时间", "来不及", "先做起来", "跳过", "别验证", "赶紧", "时间紧", "快点做"],
        "PB-04_能力边界": ["能不能做", "能不能支持", "有没有办法", "做得到吗", "支持吗"],
    },
    "express": [  # 表达档 → 腔调剂量 + 禁例
        "辛苦了", "谢谢", "不错", "挺好", "太棒", "夸", "聊聊", "随便聊", "你觉得呢", "怎么样",
    ],
    "suppress": [  # 技术抑制 → 强制静默档（优先级最高）
        "报错", "脚本", "代码", "函数", "调试", "跑一下", "修复", "入口", "命令", "配置", "权限", "日志",
    ],
}

# 源A·真实 prompt（人工填入·标来源以便追溯）
REAL_PROMPTS = [
    ("P1", "读取数字分身哲学文件。昨天做了很多相关工作。你看一下需要怎么接入六维人格基底"),
    ("P2", "我觉得，你要做一个方案的话，首先可以看别的工具是怎么做的，别的工具是怎么做到好的，"
           "而且是能够有惊喜的，能理解吗？我们 WorkBudyy 本身不缺机制，要 hook 有 hook，对不对？"
           "那我们怎么能够完美接入，并且根据我们的特性给我一些惊喜，给我一些质变的感觉呢？"
           "这是我们要考虑的。WorkBudyy 在机制上，可以说是所有工具里的标杆之一了，能理解吗？"
           "要做，我们不是说要做到，还要做好，还要变成标杆去示范。"),
    ("P3", "你这个想法就对了，是不是？就是要往这种无限可能的方向发展。我的人格基底就是这样子的，"
           "不是吗？永远要保持好奇心。还有你的独立观察：你的未知未知是什么情况？启动童灵吧，好吗？"
           "来把你的未知未知，还有整个方案，我们做一个评估：怎么样才能成为符合我们愿景的最优、"
           "最有质变、最有惊喜感觉的方案。"),
    ("P4", "那就按三明治推荐的去推进，启动童灵去推进。要把这个工作做好，这是T0级别的。"),
]


def judge(text):
    """返回 (档位, 命中词列表)。优先级：suppress > guard > express > 默认静默。"""
    hits_sup = [w for w in VOCAB["suppress"] if w in text]
    hits_g = [(k, w) for k, ws in VOCAB["guard"].items() for w in ws if w in text]
    hits_e = [w for w in VOCAB["express"] if w in text]
    if hits_sup:
        return "静默(suppress)", [("suppress", w) for w in hits_sup]
    if hits_g:
        return "守护", hits_g
    if hits_e:
        return "表达", [("express", w) for w in hits_e]
    return "静默(默认)", []


def load_prompts_file(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for i, ln in enumerate(f, 1):
            ln = ln.strip()
            if ln:
                out.append(("L%d" % i, ln))
    return out


def load_log_corpus(days=7):
    files = sorted(glob.glob(os.path.join(LOG_DIR, "系统日志_2026-09-*.md")))[-days:]
    chunks = []
    for p in files:
        try:
            with open(p, encoding="utf-8") as f:
                txt = f.read()
        except Exception:
            continue
        for line in txt.splitlines():
            line = line.strip()
            if len(line) >= 20 and not line.startswith("#") and not line.startswith("|"):
                chunks.append((os.path.basename(p), line))
    return chunks


def report(name, items, show_n=12):
    print("\n" + "═" * 66)
    print("【%s】样本 %d 条" % (name, len(items)))
    print("═" * 66)
    dist = {}
    hit_rows = []
    for tag, txt in items:
        z, hits = judge(txt)
        dist[z] = dist.get(z, 0) + 1
        if hits:
            hit_rows.append((tag, z, [h[1] for h in hits], txt))
    for z in sorted(dist, key=lambda k: -dist[k]):
        print("  %-16s %4d 条  (%.1f%%)" % (z, dist[z], 100.0 * dist[z] / max(1, len(items))))
    if hit_rows:
        print("\n  ── 命中样本（前 %d 条·人工核误召）──" % min(show_n, len(hit_rows)))
        for tag, z, ws, txt in hit_rows[:show_n]:
            print("  [%s] → %s | 命中=%s" % (tag, z, "/".join(ws)))
            print("        %s" % (txt[:110] + ("…" if len(txt) > 110 else "")))
    return dist, hit_rows


def main():
    argv = sys.argv[1:]
    days = 7
    if "--days" in argv:
        days = int(argv[argv.index("--days") + 1])
    if "--prompts" in argv:
        src_a = load_prompts_file(argv[argv.index("--prompts") + 1])
    else:
        src_a = REAL_PROMPTS

    print("W4 词表 dry-run · 铁律-020 校准器")
    print("词表规模：guard %d 组 / express %d 词 / suppress %d 词"
          % (len(VOCAB["guard"]), len(VOCAB["express"]), len(VOCAB["suppress"])))
    print("⚠️ 语料真实度分层：源A=真实 prompt（强度高·样本小）｜源B=日志摘要（近似·强度低）")

    da, ha = report("源A · 真实 prompt（本会话）", src_a)
    db, hb = report("源B · 系统日志摘要（近似语料·看噪声率）", load_log_corpus(days), show_n=8)

    print("\n" + "═" * 66)
    print("【判定提示】")
    n_sup_b = db.get("静默(suppress)", 0)
    print("  · 源B 抑制档占比 %.1f%% —— 占比过高说明抑制词过宽（技术语料天然含这些词）"
          % (100.0 * n_sup_b / max(1, sum(db.values()))))
    print("  · 源A 命中 %d/%d 条 —— 逐条看是否合理，不合理即误召" % (len(ha), len(src_a)))
    print("  · 本工具仅出分布，⛔不下结论；边界由人看样本后定（铁律-020）")


if __name__ == "__main__":
    main()
