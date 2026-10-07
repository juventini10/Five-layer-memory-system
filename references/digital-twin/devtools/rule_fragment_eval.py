#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# version: v0.1
"""
rule_fragment_eval.py — rule_fragment_inject 预注入 精准率/召回率 实测台

设计（T0 任务①·2026-09-01）：
- 直接 import 真模块 rule_triggers_loader.load_triggers + rule_fragment_inject._match_triggers，
  测的是【实盘匹配逻辑】，不是重写一份。
- 对每条 非-resident 铁律(001-007,010-019)：
    positives = 语义上"应命中"的真实用户输入（标签=应注入）
    negatives = 语义上"不应命中该条"的输入（标签=不应注入）
- 全局 negatives = 完全无关输入（标签=任何条都不应注入）
- 指标：
    召回率 recall   = 该条 positives 中正确命中 / positives 总数
    误注入率 fp      = 该条 negatives 中误命中 / negatives 总数
    精准率 precision = 正确命中 / (正确命中 + 误命中)
- 008/009 resident（常驻）不进此评估（非触发式）。
输出：per-铁律表 + 宏/微聚合 + 漏命中/误命中明细（供迭代调优 match 正则）。

用法：python3 rule_fragment_eval.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rule_triggers_loader import load_triggers
from rule_fragment_inject import _match_triggers, _match_conflict

# ---- 语料（标签由设计者按"加载时机"语义标注，反映真实用户口吻）----
CORPUS = {
    "001": {
        "pos": [
            "帮我把 config.json 改成 production 模式",
            "新建一个 test.py 文件放到 scripts 下",
            "批量重命名这些下载的图片文件",
            "把这个脚本移动到 backup 目录",
        ],
        "neg": [
            "今天深圳天气怎么样",
            "解释一下什么是闭包",
            "帮我写一首关于秋天的诗",
        ],
    },
    "002": {
        "pos": [
            "这个文件有几行代码",
            "核对一下数字对不对",
            "统计一下有多少条记录",
            "写MEMORY时记得标来源",
        ],
        "neg": [
            "讲个冷笑话",
            "推荐一部科幻电影",
            "帮我翻译这段英文",
        ],
    },
    "003": {
        "pos": [
            "引用一句乔布斯的原话",
            "帮我找一句关于坚持的名言",
            "这句话是谁说的，语录出处",
        ],
        "neg": [
            "今天吃什么好",
            "怎么用 git 回退提交",
            "帮我做个番茄炒蛋",
        ],
    },
    "004": {
        "pos": [
            "读取这个新文件看看有什么不同",
            "上次我搞错了认知，这次纠正一下",
            "这个新发现和旧认知冲突了",
        ],
        "neg": [
            "周末去哪玩比较好",
            "这段代码怎么优化",
            "讲讲量子力学",
        ],
    },
    "005": {
        "pos": [
            "删除这个旧文件",
            "用 trash 把日志移走",
            "把这个配置移动到 archive 目录",
        ],
        "neg": [
            "删除这段注释里的多余空格",   # 硬负例：删的是注释非文件/目录/夹
            "帮我写个函数",
            "明天开会几点",
        ],
    },
    "006": {
        "pos": [
            "用第一性原理分析这个问题",
            "做个深度分析",
            "用三明智评估这个方案",
        ],
        "neg": [
            "帮我订个外卖",
            "这个按钮什么颜色好看",
            "讲个睡前故事",
        ],
    },
    "007": {
        "pos": [
            "这个方案靠谱吗",
            "有什么风险需要验证",
            "这个结论站得住吗",
        ],
        "neg": [
            "帮我下载这个视频",
            "今天周几",
            "写个生日祝福",
        ],
    },
    "010": {
        "pos": [
            "记忆里之前记过这个配置路径",
            "记得上次我们改过哪个文件",
            "从记忆中调出之前的方案",
        ],
        "neg": [
            "帮我泡杯咖啡",
            "这段代码报错了",
            "周末计划是什么",
        ],
    },
    "011": {
        "pos": [
            "用软链接把这个目录链过去",
            "用 dd 写这个镜像",
            "用 ffmpeg 转码这个视频",
        ],
        "neg": [
            "用 python 读这个文件",
            "帮我画画",
            "总结一下这篇文章",
        ],
    },
    "012": {
        "pos": [
            "帮我写个视频文案",
            "这个案例该怎么用",
            "创作一段关于成长的脚本",
        ],
        "neg": [
            "今天股市怎么样",
            "帮我修个水管",
            "查一下快递到哪了",
        ],
    },
    "013": {
        "pos": [
            "把这个经验沉淀到长期能力里",
            "我们要建一个审美尺子",
            "这是个战略任务要系统能力建设",
        ],
        "neg": [
            "帮我查天气",
            "翻译这句话",
            "定个闹钟",
        ],
    },
    "014": {
        "pos": [
            "这个写入工具上线前要压测",
            "脚本设计要注意并发写入",
            "append 模式写日志安全吗",
        ],
        "neg": [
            "帮我写个故事",
            "今天吃什么",
            "讲个笑话",
        ],
    },
    "015": {
        "pos": [
            "启动自动化任务跑这个发布",
            "Loop 循环执行时卡住了",
            "自主执行遇到阻塞怎么办",
        ],
        "neg": [
            "帮我查个单词",
            "这首歌叫什么",
            "推荐个餐厅",
        ],
    },
    "016": {
        "pos": [
            "审计一下这个接入是否合规",
            "看下设计哲学的进度看板",
            "这个状态结论和实盘对得上吗",
        ],
        "neg": [
            "帮我买杯奶茶",
            "写个备忘录",
            "今天几号",
        ],
    },
    "017": {
        "pos": [
            "记一笔系统日志",
            "沉淀到成长箱",
            "用 sucair 读书",
        ],
        "neg": [
            "帮我看个电影",
            "今天天气",
            "算下账",
        ],
    },
    "018": {
        "pos": [
            "追加到变更日志",
            "这个改动记到账本里",
            "更新 changelog",
        ],
        "neg": [
            "帮我写首诗",
            "修个bug",
            "吃什么",
        ],
    },
    "019": {
        "pos": [
            "调用历史经验看看上次的情况",
            "用立场卡类比这个情境",
            "这个快照还时效吗",
        ],
        "neg": [
            "帮我定机票",
            "讲个故事",
            "查快递",
        ],
    },
    # 020-028：**故意留空**（2026-10-01 Qoder CN 判定·跨端交接单收尾轮）。
    #   本轮给 029 补 match 时实测过 5 正例/10 负例，正例来自当日真实施工语句；
    #   而 020-028 手上没有真实语料——若照索引表措辞"造"句子喂进来，评测会显示
    #   "覆盖 020-029"而实际测的是我自己编的话＝**假覆盖比无覆盖更坏**（无覆盖至少知道自己瞎）。
    #   欠账已登记在案（见本文件 --report 与系统日志），取材口径＝真实会话/日志原句，逐条补。
    # 029：机器托管产物写入方向（铁律-029·2026-10-01 晋升·v8.26）
    #   ⚠️已知召回缺口 2/6（如实留痕，不当成已解决）：
    #     "这个派生物能不能直接手改"（名词化提问·无"写/存/落…"动词锚）／
    #     "重跑生成器后我这条记录还在不在"（存续性提问·不含"被覆盖/下次生成"词面）
    "029": {
        "pos": [
            "写入切片前确认方向",
            "把这条存进 core_slice",
            "manifest 里的手抄会不会被下次生成覆盖",
            "账本里落 findings.json 合适吗",
        ],
        "neg": [
            "今天写日记",
            "帮我修个 bug",
            "这个页面配色怎么调",
            "晚上吃什么",
            "跑一下测试",
            "把这段代码注释掉",
            "git 提交一下",
            "写个脚本读 csv",
            "这本书讲了什么",
            "帮我起个项目名",
        ],
    },
}

GLOBAL_NEG = [
    "你好",
    "今天心情不错",
    "帮我算 1+1",
    "晚安",
    "这个红色好看吗",
    "猫和狗哪个更聪明",
    "下周休假",
    "唱歌给我听",
    "几点了",
    "谢谢",
]

# ---- 冲突/边缘场景 → 详解版 预注入（Q2②）语料 ----
# pos = 用户输入侧命中冲突/边缘信号（应预注入"须 Read 详解存档版"指令）
# neg = 普通操作/问答（不应触发冲突预注入）
CONFLICT_POS = [
    "这两条规则冲突了怎么处理",
    "规则 005 能不能改一下",
    "这是个边缘情况吧",
    "为什么规则 001 要这样定",
    "成长箱晋升复查要注意什么",
    # 2026-09-16 扩容·自然变体回灌（实测'打架'漏检样本·三明智 L2 键 20260916_195826）
    "铁律005和铁律018在删除场景下是不是打架",
    "020和021哪个优先",
    "这两条规则谁听谁的",
]
CONFLICT_NEG = [
    "帮我把 config.json 改成 production",   # 普通文件操作→命中 001 但不属冲突域
    "今天天气怎么样",
    "写个视频文案",
    "记一笔系统日志",
    "别跟人打架，冷静点",                     # 2026-09-16 负例护栏·裸'打架'非规则语境
    "昨晚拳击比赛谁打赢了",                   # 负例护栏·'打架'近义场景
]


def main():
    triggers = load_triggers()
    by_id = {t["id"]: t for t in triggers}
    # 仅评非 resident
    eval_ids = [t["id"] for t in triggers if not t.get("resident")]
    eval_ids.sort()

    print("=" * 72)
    print("rule_fragment_inject 预注入 PRECISION / RECALL 实测")
    print(f"评估铁律条数(非resident): {len(eval_ids)}  | 全局负例: {len(GLOBAL_NEG)}")
    print("=" * 72)
    print(f"{'ID':<4} {'recall':>7} {'fp%':>7} {'prec':>7}  {'pos':>4} {'neg':>4}")
    print("-" * 72)

    tot_pos = tot_pos_hit = 0
    tot_neg = tot_neg_hit = 0
    miss_detail = []   # 应命中却漏
    fp_detail = []     # T 自身误命中 T 的负例
    cross_noise = []   # T 的负例命中了【别的】触发器（非 T 的错，信息性）

    def _hit_ids(prompt):
        return {x["id"] for x in _match_triggers(prompt, triggers)}

    for i in eval_ids:
        t = by_id[i]
        c = CORPUS.get(i)
        if not c:
            print(f"{i:<4}  ⚠️ 语料缺失")
            continue
        pos = c["pos"]
        neg = c["neg"]
        pos_hit = sum(1 for p in pos if i in _hit_ids(p))
        # fp 严格定义：T 自身是否误命中 T 的负例（不是"任何触发器命中"）
        neg_hit_T = sum(1 for p in neg if i in _hit_ids(p))
        recall = pos_hit / len(pos)
        fp = neg_hit_T / len(neg)
        prec = pos_hit / (pos_hit + neg_hit_T) if (pos_hit + neg_hit_T) else 1.0
        print(f"{i:<4} {recall*100:6.1f}% {fp*100:6.1f}% {prec*100:6.1f}%  "
              f"{len(pos):>4} {len(neg):>4}")
        tot_pos += len(pos); tot_pos_hit += pos_hit
        tot_neg += len(neg); tot_neg_hit += neg_hit_T
        for p in pos:
            if i not in _hit_ids(p):
                miss_detail.append((i, p))
        for p in neg:
            ids = _hit_ids(p)
            if i in ids:
                fp_detail.append((i, p))
            elif ids:  # 命中了别的触发器——信息性噪声，非 T 的 bug
                cross_noise.append((i, sorted(ids), p))

    # 全局负例：任何条都不应命中
    g_hit = 0
    g_detail = []
    for p in GLOBAL_NEG:
        h = _match_triggers(p, triggers)
        if h:
            g_hit += 1
            g_detail.append(([x["id"] for x in h], p))

    print("-" * 72)
    micro_recall = tot_pos_hit / tot_pos
    micro_fp = tot_neg_hit / tot_neg
    print(f"微聚合 recall={micro_recall*100:.1f}%  fp={micro_fp*100:.1f}%  "
          f"(pos {tot_pos_hit}/{tot_pos}, 负例误中T {tot_neg_hit}/{tot_neg})")
    print(f"全局负例误注入: {g_hit}/{len(GLOBAL_NEG)}")
    print("=" * 72)

    if miss_detail:
        print("\n【漏命中·应注入却未注入】")
        for i, p in miss_detail:
            print(f"  [{i}] {p}")
    else:
        print("\n【漏命中】无 ✅")

    if fp_detail:
        print("\n【误注入·T 自身误命中 T 的负例】")
        for i, p in fp_detail:
            print(f"  [{i}] {p}")
    else:
        print("\n【误注入·T 自身】无 ✅")

    if cross_noise:
        print("\n【跨触发器噪声·信息性(非 bug)·T 负例命中了别的触发器】")
        for i, ids, p in cross_noise:
            print(f"  {ids} <- 触发词属 {i} 的负例: {p}")
    else:
        print("\n【跨触发器噪声】无")

    if g_detail:
        print("\n【全局负例误命中·触发条】")
        for ids, p in g_detail:
            print(f"  {ids} <- {p}")

    # ---- 冲突/边缘场景 → 详解版 预注入（Q2②）----
    c_pos_hit = sum(1 for p in CONFLICT_POS if _match_conflict(p))
    c_neg_hit = sum(1 for p in CONFLICT_NEG if _match_conflict(p))
    c_recall = c_pos_hit / len(CONFLICT_POS)
    c_fp = c_neg_hit / len(CONFLICT_NEG)
    print("-" * 72)
    print(f"冲突/边缘→详解版 预注入(Q2②): recall={c_recall*100:.1f}%  fp={c_fp*100:.1f}%"
          f"  (pos {c_pos_hit}/{len(CONFLICT_POS)}, neg误中 {c_neg_hit}/{len(CONFLICT_NEG)})")
    if c_pos_hit < len(CONFLICT_POS):
        miss = [p for p in CONFLICT_POS if not _match_conflict(p)]
        print("  ⚠️ 漏命中:", miss)
    if c_neg_hit:
        fp = [p for p in CONFLICT_NEG if _match_conflict(p)]
        print("  ⚠️ 误命中:", fp)

    print("\n=== 评估结束 ===")


if __name__ == "__main__":
    main()
