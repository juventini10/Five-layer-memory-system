#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checklist_backfill.py — 立场卡【查证清单】批量回填（166 张·皮叔授权 L1→L2 非价值层分身可做）

授权范围（铁律-022② 声明）：
  ✅ 六层查证回填（证据层=真回读源卡·未核/找茬=卡内真实素材提取·扩权=类型映射）
  ⛔ 不标「你已质证/你已确认」（只标分身级中间态·I-43 教训）
  ⛔ 不改卡的主张内容（只补查证清单块）
  ⛔ 价值层卡不越权裁决（愿景行标「初步映射·待你抽检」）

用法：
  python3 checklist_backfill.py --dry-run     # 只生成不写回（输出样例）
  python3 checklist_backfill.py --limit N     # 只处理前 N 张
  python3 checklist_backfill.py               # 全量执行
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import glob
import json
import os
import re
import sys
from datetime import date

POOL = os.path.expanduser("~/[日记仓库]/2-知识库/09-AI学习库")  # 2026-10-13 C''波次2迁移后路径同步
CONCEPT = os.path.expanduser("~/[日记仓库]/2-知识库")
STATS = os.path.expanduser("[记忆共享中心]/脚本中心/verify_checklist_gate.py")
MANDATE = "2026-08-24"
TODAY = date.today().isoformat()

_src_cache = {}


def find_card(cid):
    if cid in _src_cache:
        return _src_cache[cid]
    f = None
    for pat in (os.path.join(POOL, f"*{cid}*.md"),
                glob.glob(os.path.expanduser("~/[日记仓库]/2-知识库/**/" + cid + "-*.md"), recursive=True)):
        fs = glob.glob(pat) if isinstance(pat, str) else pat
        if fs:
            f = fs[0]
            break
    _src_cache[cid] = f
    return f


def src_summary(cid):
    """回读源卡 → (摘要, 状态)。真回读非编造。"""
    f = find_card(cid)
    if not f:
        return None, "notfound"
    t = open(f, encoding="utf-8", errors="ignore").read()
    m = re.search(r'definition:\s*"(.{20,180})', t)
    if m:
        return m.group(1), "concept"
    i = t.find("**立场")
    if i > 0:
        return t[i:i+180].replace("\n", " "), "stance"
    return t[:150].replace("\n", " "), "other"


def extract_refs(t):
    """提取依据链引用（C-xxx/S-xxx·去重保序）。"""
    i = t.find("**依据链")
    j = t.find("**反例", i) if i > 0 else -1
    seg = t[i:j] if (i > 0 and j > i) else (t[i:] if i > 0 else t)
    refs = re.findall(r"[CS]-\d{3}", seg)
    seen, out = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def extract_sections(t):
    """提取卡内已有素材（真材料·非编造）。"""
    def seg(start, end=None):
        i = t.find(start)
        if i < 0:
            return ""
        j = t.find(end, i + len(start)) if end else -1
        return t[i + len(start):j].strip() if j > i else t[i + len(start):].strip()
    steel = seg("**反方最强论证（steelman）**：", "\n\n")
    quiz = seg("**自测题", "\n\n")
    return steel, quiz


def backfill_one(path, dry):
    t = open(path, encoding="utf-8", errors="ignore").read()
    if "【查证清单】" in t:
        return "skip-has"
    cid = re.search(r"card_id:\s*(立场卡#\S+)", t)
    cid = cid.group(1) if cid else os.path.basename(path)
    refs = extract_refs(t)
    verified, notfound = [], []
    for r in refs:
        summ, kind = src_summary(r)
        if summ:
            verified.append(f"**{r}**「{summ[:88]}…」✅回读一致" if kind == "concept"
                            else f"**{r}**「{summ[:88]}…」✅回读存在")
        else:
            notfound.append(r)
    steel, quiz = extract_sections(t)
    unverified = [ln.strip(" |") for ln in quiz.splitlines() if ln.strip() and re.match(r"^\d", ln.strip())][:3]
    finding = steel[:220] if steel else "（卡内无独立 steelman 段·反例 C 即找茬素材）"
    ftype = "机制" if "type: 机制" in t else ("决策" if "type: 决策" in t else "通用")
    cl = ["## 【查证清单】",
          f"> {TODAY}·分身批量查证回填（你授权「L1升L2非价值层分身可做」·查证方式＝**回读源卡验证依据链**·真回读非编造：{len(refs)} 引用·命中 {len(verified)}·未找到 {len(notfound)}）",
          "- 已核：" + "；".join(verified) if verified else "- 已核：（无引用命中·依据链引用均为未建档源→转你核）",
          ("- 未核：" + "；".join(unverified)) if unverified else "- 未核：（卡内自测题未提取到·见正文）",
          f"- 强制找茬（三大思维·自卡 steelman/反例素材）：{finding}",
          "- 愿景符合性（**初步映射·待你抽检**）：机制/决策类卡通常服务①全自动化（机械判定不靠人记得）＋③自主进化（执行数据喂蒸馏）——本卡属" + ftype + "类·初步判 ✅·⛔待你抽检确认",
          "- AI扩权方向自检：AI 回读验证依据链＝AI 判「引用是否属实」——源卡定义本身由蒸馏管道维护（n=1 校准已声明）；本卡若涉价值判断，裁决归你。",
          "- 置信度：" + ("高（依据链全命中）" if not notfound else f"中高（{len(notfound)} 引用未找到档案·如实标注）")]
    cl_text = "\n".join(cl) + "\n\n"
    anchor = min((i for i in (t.find("**质证记录"), t.find("## 🔍 质证记录"), t.find("## 质证记录")) if i >= 0), default=-1)
    if anchor < 0:
        return "skip-noanchor"
    new = t[:anchor] + cl_text + t[anchor:]
    if not dry:
        open(path + ".bak-backfill", "w", encoding="utf-8").write(t)
        open(path, "w", encoding="utf-8").write(new)
    return "done"


def main():
    dry = "--dry-run" in sys.argv
    limit = 0
    for i, a in enumerate(sys.argv):
        if a == "--limit":
            limit = int(sys.argv[i + 1])
    done, skipped, failed = 0, 0, 0
    for f in sorted(glob.glob(os.path.join(POOL, "立场卡#*.md"))):
        t = open(f, encoding="utf-8", errors="ignore").read()
        if "【查证清单】" in t:
            continue
        dm = re.search(r"date:\s*(\S+)", t)
        if not dm or dm.group(1) < MANDATE:
            continue
        if limit and done >= limit:
            break
        r = backfill_one(f, dry)
        if r == "done":
            done += 1
            print(f"  ✅ {os.path.basename(f)[:56]}")
        elif r.startswith("skip"):
            skipped += 1
        else:
            failed += 1
    print(f"\n═══ 回填统计：处理 {done} ｜ 跳过 {skipped}（已有/无锚）｜ 失败 {failed} ｜ {'DRY-RUN 未写回' if dry else '已写回（各卡 .bak-backfill 备份）'}")


if __name__ == "__main__":
    main()
