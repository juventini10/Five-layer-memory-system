# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iron_rule_antibody_mapper.py — 铁律 ↔ 已有守卫 映射分析（v1.0.0·2026-10-01）

## 目的
回答「27 条纯文本铁律能不能转抗体」——**先查已有 113 个注册守卫**，
⛔ 不为凑覆盖率新建重复抗体（C4恒真/C7恒假是更坏的下场）。

## 判据
对每条无抗体铁律，用「该条正文里的可检测对象关键词」去匹配注册表的
「守卫名 + 辖区 + 守什么对象」三列。命中 = **可能已有承接**（候选·需人工确认口径）。

## ⚠️ 定位声明（2026-10-01 首跑后补·必读）
本脚本是**候选生成器，不是判据**。首跑产出「A 类 20 条」后逐条回读注册表核证，
**当场推翻三条**：
  · 铁律-005 删除防护 ← 匹配到 `git_commit_safe.sh`（实为**提交串行化**·不删文件）
  · 铁律-011 写操作安全 ← 匹配到 `symlink_guard.sh`（实为 **Skill 软链巡检**·非写穿透防护）
  · 铁律-018 变更账本   ← 匹配到 `changelog_guard.py`（**部分对**，但注册表自标「负例实测待补」）
⇒ **词面命中 ≠ 直接证据**（与成长箱 E3.5 要素5「⛔勿词面 grep 代替读落点全文」同源）。
✅ 本脚本的产物只能进入「人工逐条回读核证」队列，⛔ 不得直接当作「已补登记」的依据。

## 输出三分类
  A类·已有承接候选：命中已有守卫 → **补登记即可·⛔不新建**
  B类·无命中：需评估能否新建抗体
  C类·不可转：无物理可测对象（如「批判性思维」）→ 应显式豁免

⚠️ 本脚本只做**候选映射**，不自动改铁律（终审红线：AI不得自行写入规则文件）。
"""

import io
import re
import sys

IRON = os.path.expanduser("[记忆共享中心]/记忆规则/用户基本规则-铁律版.md")
REG = ("[记忆共享中心]/脚本中心/"
       "布洛陀脚本架构设计哲学/守卫编写规范.md")
__version__ = "v1.0.0"

# 每条铁律 → 可检测对象关键词（命中即拿去做守卫匹配）
# ⛔ 只列**物理可测对象**（文件/格式/计数/钩子/落点），不列纯思维要求
OBJ_MAP = {
    "001": ["读", "grep", "先看清", "取证", "证据", "读源"],
    "002": ["计数", "数字", "断言", "实测", "标注", "读后"],
    "003": ["引用", "查源", "来源", "验证"],
    "004": ["防复发", "认知更新", "旧认知"],
    "005": ["删除", "trash", "rm ", "git commit", "备份"],
    "006": ["结构化", "深度", "强制"],
    "007": ["批判", "自我批判", "编造"],
    "008": ["意图分类", "署名", "格式", "产出签名"],
    "009": [],
    "010": ["召回", "检索", "回读"],
    "011": ["软链", "写穿透", "写操作", "readlink"],
    "012": ["查源", "素材", "来源"],
    "013": ["不退档", "自我要求"],
    "014": ["写入", "并发", "append", "隔离压测"],
    "015": ["证据", "锚点", "回执", "宿主收讫"],
    "016": ["体检", "报告", "快照", "时点"],
    "017": ["门禁", "pre-commit", "提交"],
    "018": ["变更账本", "changelog", "唯一入口"],
    "019": ["备份", "不可逆", "恢复"],
    "020": ["sanity", "匹配", "改脚本", "dry-run"],
    "021": ["验证", "换一把尺", "机械", "自觉"],
    "022": ["授权", "标注", "可核验"],
    "023": ["认错", "自触发", "Channel C"],
    "024": ["豁免", "报名", "自评"],
    "025": ["只读", "写入口", "注册表"],
    "026": ["验证", "事后闸", "事前"],
    "027": ["生图", "对抗"],
    "028": [],  # 已有承接器
    "029": [],  # 已有承接器
    "030": [],  # 已有承接器
}


def load_rules():
    t = io.open(IRON, encoding="utf-8").read()
    secs = re.split(r"\n### 铁律-(\d{3})", t)
    out = []
    for i in range(1, len(secs), 2):
        num, body = secs[i], secs[i + 1]
        has_ab = bool(re.search(r"承接器在岗|抗体|🛡", body))
        has_ex = bool(re.search(
            r"(?:抗体|🛡|承接器)[^。\n]{0,30}?(?:暂无|尚无|无|不适用|N/?A|未配|没有).{0,40}?(?:理由|原因|因|系|：|:)",
            body, re.S))
        out.append({"num": num, "title": body.split("\n")[0].strip()[:44],
                    "body": body, "bare": not (has_ab or has_ex)})
    return out


def load_registry():
    t = io.open(REG, encoding="utf-8").read()
    i = t.find("<!-- STRIP_START:守卫注册表")
    j = t.find("<!-- STRIP_END", i)
    blk = t[i:j] if j > 0 else t[i:]
    rows = []
    for line in blk.split("\n"):
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.split("|")[1:-1]]
        if len(c) >= 6 and ("." in c[0]):
            rows.append({"name": c[0], "zone": c[1], "object": c[2],
                         "truth": c[3], "timing": c[4], "neg": c[5]})
    return rows


def main():
    rules = load_rules()
    reg = load_registry()
    bare = [r for r in rules if r["bare"]]
    print("iron_rule_antibody_mapper %s" % __version__)
    print("铁律 %d 条（无抗体 %d）· 注册守卫 %d 个" % (len(rules), len(bare), len(reg)))
    print("=" * 78)

    a, b, c = [], [], []
    for r in bare:
        kws = OBJ_MAP.get(r["num"], [])
        hits = []
        for g in reg:
            blob = (g["name"] + " " + g["zone"] + " " + g["object"]).lower()
            for k in kws:
                if k.lower() in blob:
                    hits.append((g["name"], k))
                    break
        if hits:
            a.append((r, hits))
        elif not kws:
            c.append(r)
        else:
            b.append(r)

    print("\n【A类·已有承接候选 %d 条】→ ✅DO 补登记「承接器在岗」·⛔DO NOT 新建抗体")
    for r, hits in a:
        print("  铁律-%s %-30s ← %s" % (r["num"], r["title"][:30],
                                        "; ".join("%s(%s)" % (h[0][:26], h[1]) for h in hits[:3])))
    print("\n【B类·无现成承接 %d 条】→ 需评估能否新建（须过 antibody_gate C1-C10）" % len(b))
    for r in b:
        print("  铁律-%s %-30s ← 关键词 %s" % (r["num"], r["title"][:30], OBJ_MAP.get(r["num"], [])))
    print("\n【C类·无可测对象 %d 条】→ ⛔不可转·应显式豁免+理由（转不了就别硬造）" % len(c))
    for r in c:
        print("  铁律-%s %s" % (r["num"], r["title"][:40]))

    print("\n覆盖率预判：当前 %d%% → 若 A 类全部补登记可达 %.1f%%"
          % (round(100.0 * 3 / len(rules), 1), round(100.0 * (3 + len(a)) / len(rules), 1)))
    print("⚠️ 本脚本只出候选·⛔不自动改铁律（终审红线#2）")
    return 0


if __name__ == "__main__":
    sys.exit(main())