#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
card_reading_stats.py — 立场卡 reading_status 统计数据源（愿景仪表盘·自主进化数据源）
职责: 统计立场卡 L1-L4 分布、L3/L4 累计数量、近7日新增，输出 JSON 供面板消费。
      数据源 = INDEX.md（真实状态快照）+ 引用台账.md（真实引用事件）
      ⛔只读不写卡片，只输出 JSON。

输出字段（供 evolution_deviation 面板消费）：
  - total: 总卡片数
  - L1_count / L2_count / L3_count / L4_count: 各等级数量
  - L3_cumulative / L4_cumulative: L3/L4 累计数（愿景③自主进化可观测代理）
  - L3_new_7d / L4_new_7d: 近7日新增 L3/L4 数
  - L3_to_L4_ratio: L3→L4 转化率（内化效率）
  - pending_recheck: 待你复审降级数（负反馈标记）

用法:
  python3 card_reading_stats.py             # 输出 JSON 到 stdout
  python3 card_reading_stats.py --save      # 保存到系统日志目录
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, re, json, glob
from datetime import datetime, timedelta

HOME = os.path.expanduser("~")
AILIB_DIR = os.path.join(HOME, "~/个人AI档案", "知识库", "AI学习库")
INDEX_FILE = os.path.join(AILIB_DIR, "INDEX.md")
LEDGER_FILE = os.path.join(AILIB_DIR, "引用台账.md")
SYSLOG = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具/logs/runtime")


def parse_index_table(text):
    """解析 INDEX 表格，返回 {card_id: {status, ...}}"""
    cards = {}
    for line in text.split("\n"):
        if not line.startswith("| 立场卡"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        cid = cells[0]
        status = cells[4] if len(cells) > 4 else ""
        cards[cid] = {"status": status, "raw": line}
    return cards


def count_by_status(cards):
    """按 status 统计各等级数量"""
    counts = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "other": 0}
    for cid, info in cards.items():
        st = info["status"]
        if st.startswith("L1"):
            counts["L1"] += 1
        elif st.startswith("L2"):
            counts["L2"] += 1
        elif st.startswith("L3"):
            counts["L3"] += 1
        elif st.startswith("L4"):
            counts["L4"] += 1
        else:
            counts["other"] += 1
    return counts


def count_new_l3_l4_7d(cards):
    """统计近7日新增的 L3/L4（基于卡片内事件记录日期或 INDEX 更新日期）"""
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    l3_new = 0
    l4_new = 0
    
    # 读取所有卡片文件，查找近7日的质证/引用事件
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "立场卡*.md"))):
        base = os.path.basename(p)
        # 从文件名提取 card_id
        m = re.match(r"(立场卡#\S+?)-", base)
        if not m:
            continue
        cid = m.group(1)
        if cid not in cards:
            continue
        
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except Exception:
            continue
        
        # 查找近7日的事件记录
        cur_status = cards[cid]["status"]
        for line in text.split("\n"):
            # 匹配 YYYY-MM-DD 格式日期
            dm = re.search(r"(20\d{2}-\d{2}-\d{2})", line)
            if not dm:
                continue
            d = dm.group(1)
            if cutoff <= d <= today:
                # 检查是否为升级事件
                if cur_status.startswith("L3") and "已应用" in line:
                    l3_new += 1
                    break
                elif cur_status.startswith("L4") and "已内化" in line:
                    l4_new += 1
                    break
    return l3_new, l4_new


def count_pending_recheck():
    """统计待你复审降级数（负反馈标记）"""
    # 检查是否有负反馈事件标记的卡片
    nf_audit = []
    for p in sorted(glob.glob(os.path.join(AILIB_DIR, "立场卡*.md"))):
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
            if any(kw in text for kw in ["应用失败", "立场已过时", "你质疑降级", "质证回退"]):
                base = os.path.basename(p)
                m = re.match(r"(立场卡#\S+?)-", base)
                if m:
                    nf_audit.append(m.group(1))
        except Exception:
            continue
    return len(nf_audit)


def compute_save_ratio(l3_count, l4_count):
    """计算 L3→L4 转化率"""
    if l3_count == 0:
        return None
    return round(l4_count / l3_count, 3)


def main():
    save_mode = "--save" in sys.argv
    
    # 读取 INDEX
    if not os.path.isfile(INDEX_FILE):
        print(json.dumps({"error": "INDEX.md 不存在"}, ensure_ascii=False))
        return 1
    
    with open(INDEX_FILE, encoding="utf-8") as f:
        index_text = f.read()
    
    cards = parse_index_table(index_text)
    counts = count_by_status(cards)
    
    # 计算近7日新增
    l3_new_7d, l4_new_7d = count_new_l3_l4_7d(cards)
    
    # 待复审数
    pending = count_pending_recheck()
    
    # 转化率
    ratio = compute_save_ratio(counts["L3"], counts["L4"])
    
    today = datetime.now().strftime("%Y-%m-%d")
    result = {
        "date": today,
        "source": "card_reading_stats.py",
        "total": len(cards),
        "counts": counts,
        "L3_cumulative": counts["L3"],
        "L4_cumulative": counts["L4"],
        "L3_new_7d": l3_new_7d,
        "L4_new_7d": l4_new_7d,
        "L3_to_L4_ratio": ratio,
        "pending_recheck": pending,
        "note": "L3/L4 累计数=愿景③自主进化可观测代理·L3→L4转化率=内化效率",
    }
    
    out_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    if save_mode:
        os.makedirs(SYSLOG, exist_ok=True)
        out_path = os.path.join(SYSLOG, f"card_reading_stats_{today}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_json)
        print(f"[card_reading_stats] 已保存 {out_path}")
    
    print(out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
