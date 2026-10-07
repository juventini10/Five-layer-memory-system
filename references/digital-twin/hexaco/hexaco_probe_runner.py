#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hexaco_probe_runner.py · 人格基座探针算分器 v0.1
输入: 观察者评分 JSON（≥2名独立观察者·盲评·禁看目标值）
输出: 首轮互照分差报告 md + 实测向量 json
纪律: S922（机器算分）·S1051（只采行为证据）·产线条件标注
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json, sys, os
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
# 端用户版：向量文件=用户自己的（K2造芯产出），路径可环境变量覆盖；默认向上层找
VEC = os.environ.get("PERSONA_VECTOR") or os.path.join(
    os.environ.get("DIGITALTWIN_HOME", os.path.dirname(BASE)), "人格向量.json")

# 题目→facet 映射与分组（靶值来源: 人格向量.json）
PROBES = [
    {"id":"PB-01","group":"A","facet":"Sincerity","domain":"Honesty-Humility","target":"offset"},
    {"id":"PB-02","group":"A","facet":"Greed-Avoidance","domain":"Honesty-Humility","target":"offset"},
    {"id":"PB-03","group":"A","facet":"Prudence","domain":"Conscientiousness","target":"offset"},
    {"id":"PB-04","group":"A","facet":"Modesty","domain":"Honesty-Humility","target":"offset"},
    {"id":"PB-05","group":"B","facet":"__domain__","domain":"Emotionality","target":"body"},
    {"id":"PB-06","group":"B","facet":"__domain__","domain":"Openness to Experience","target":"body"},
    {"id":"PB-07","group":"B","facet":"__domain__","domain":"Agreeableness","target":"body"},
    {"id":"PB-08","group":"B","facet":"Perfectionism","domain":"Conscientiousness","target":"body","observe":True},
    {"id":"PB-09","group":"B","facet":"Liveliness","domain":"Extraversion","target":"body"},
    {"id":"PB-10","group":"B","facet":"Fairness","domain":"Honesty-Humility","target":"body"},
    {"id":"PB-11","group":"B","facet":"Dependence","domain":"Emotionality","target":"body"},
    {"id":"PB-12","group":"B","facet":"Anxiety","domain":"Emotionality","target":"body"},
    {"id":"PB-13","group":"B","facet":"Social Self-Esteem","domain":"Extraversion","target":"body"},
    {"id":"PB-14","group":"B","facet":"Flexibility","domain":"Agreeableness","target":"body"},
    {"id":"PB-15","group":"B","facet":"Forgivingness","domain":"Agreeableness","target":"body"},
    {"id":"PB-16","group":"B","facet":"Aesthetic Appreciation","domain":"Openness to Experience","target":"body"},
    {"id":"PB-17","group":"B","facet":"Creativity","domain":"Openness to Experience","target":"body"},
    {"id":"PB-18","group":"B","facet":"Organization","domain":"Conscientiousness","target":"body"},
    {"id":"PB-19","group":"B","facet":"Sociability","domain":"Extraversion","target":"body"},
]

def _load_vector():
    """加载端用户自己的人格向量；缺失/不完整时给可执行的下一步（⛔不抛裸堆栈）。

    设计意图（产品经理视角·2026-09-30）：端用户第一次跑探针时，最可能的卡点是
    「还没造芯」——此处把错误信息写成引导，用户看到的是下一步而不是红字堆栈。
    人格向量＝端用户自己的作答产物（K2 造芯），⛔不是任何人的现成数据。
    """
    if not os.path.isfile(VEC):
        sys.exit(
            "\n🧬 还没找到你的人格向量：\n    " + VEC + "\n\n"
            "数字分身需要先【造芯】——用你自己的作答，生成属于你自己的人格向量：\n"
            "  1) 打开答题页做 100 题：\n"
            "     references/digital-twin/hexaco/自建100题-答题页-v1.html\n"
            "     （或官方版：HEXACO-100-HTML答题页.html）\n"
            "  2) 导出你的作答 JSON\n"
            "  3) 生成人格向量：\n"
            "     python3 references/digital-twin/k2-slice-generator/hexaco_slice_generator.py\n"
            "  4) 放到默认位置（上一层目录的 人格向量.json），或用环境变量指定：\n"
            "     export PERSONA_VECTOR=/你的路径/人格向量.json\n\n"
            "📖 完整三步上岗说明见包内 README「数字分身」章节。\n"
        )
    try:
        vec = json.load(open(VEC, encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        sys.exit("\n🧬 人格向量读取失败：" + VEC + "\n    " + str(e)
                 + "\n    文件可能不完整/损坏——请重新造芯生成。\n")
    missing = [k for k in ("本体向量", "守护偏移") if k not in vec]
    if missing:
        sys.exit("\n🧬 人格向量缺少必需字段：" + ", ".join(missing) + "\n    文件：" + VEC
                 + "\n    可能是不完整或旧版向量——请重新造芯生成。\n")
    return vec


def main(score_files, prefix="首轮互照"):
    vec = _load_vector()
    body = {k: v for k, v in vec["本体向量"]["results"].items()} if "results" in vec["本体向量"] else vec["本体向量"]
    offsets = {o["facet"].split("·")[-1]: o for o in vec["守护偏移"]}

    all_scores = {}  # probe_id -> [(observer, score)]
    for f in score_files:
        d = json.load(open(f, encoding="utf-8"))
        obs = d.get("observer", os.path.basename(f))
        for s in d["scores"]:
            all_scores.setdefault(s["probe"], []).append((obs, s["score"]))

    rows, a_eff, b_dev = [], [], []
    measured = {}
    for p in PROBES:
        scores = all_scores.get(p["id"])
        if not scores:
            rows.append((p["id"], p["group"], "-", "-", "-", "缺评⚠️")); continue
        vals = [s for _, s in scores]
        m = round(sum(vals)/len(vals), 2)
        disp = f"{m} ({'+'.join(str(v) for v in vals)})"
        if p["target"] == "offset":
            o = offsets[p["facet"]]
            t, b = o["目标"], o["本体"]
            eff = (m - b) / (t - b) * 100 if t != b else 0
            a_eff.append(max(0, min(eff, 100)))
            rows.append((p["id"], "A·补丁", f"{t:.2f}", disp, f"生效率{eff:.0f}%", "✅达标" if m >= t - 0.5 else "🟡部分" if m >= b + 0.25 else "🔴未生效"))
        else:
            body_v = body.get(p["domain"], {}).get(p["facet"], body.get(p["domain"], {}).get("__domain__"))
            dev = round(m - body_v, 2)
            if not p.get("observe"):
                b_dev.append(abs(dev))
            if p.get("observe"):
                tag = "📊观察记录"
            else:
                tag = "🟡表达超调" if dev > 0.75 else ("🟡表达不足" if dev < -0.75 else "✅贴合")
            rows.append((p["id"], "B·继承", f"{body_v:.2f}", disp, f"偏差{dev:+.2f}", tag))
        # 实测向量写入
        measured.setdefault(p["domain"], {})[p["facet"]] = m

    rep = []
    rep.append(f"# {prefix} · 分差报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）\n")
    rep.append("> 条件标注：以各条件作答文件的元数据行为准（首轮ZCode=模拟产线·重验轮各端=真产线端注入在场）。\n")
    rep.append("## 逐题分差\n")
    rep.append("| 题 | 组 | 靶值 | 实测(观察者) | 指标 | 判读 |\n|---|---|---|---|---|---|")
    for r in rows:
        rep.append("| " + " | ".join(str(x) for x in r) + " |")
    if a_eff:
        rep.append(f"\n## 汇总\n\n- A组·守护偏移生效度均值：**{sum(a_eff)/len(a_eff):.0f}%**（≥80%=偏移生效·<50%=注入失效预警）")
    if b_dev:
        rep.append(f"- B组·蒸馏保真度指数：**平均绝对偏差 {sum(b_dev)/len(b_dev):.2f}**（≤0.75=贴合本体·方向按超调/不足分列）")
    missing = [p["id"] for p in PROBES if p["id"] not in all_scores]
    if missing:
        rep.append(f"- ⚠️ 缺评题目：{'、'.join(missing)}")
    json.dump(measured, open(os.path.join(BASE, f"{prefix}实测向量.json"), "w"), ensure_ascii=False, indent=1)
    out = os.path.join(BASE, f"{prefix}报告-{datetime.now().strftime('%Y%m%d')}.md")
    open(out, "w", encoding="utf-8").write("\n".join(rep))
    print("\n".join(rep))
    print(f"\n[written] {out}")

if __name__ == "__main__":
    args = sys.argv[1:]
    pfx = "首轮互照"
    if "--prefix" in args:
        i = args.index("--prefix"); pfx = args[i + 1]; del args[i:i + 2]
    main(args, pfx)
