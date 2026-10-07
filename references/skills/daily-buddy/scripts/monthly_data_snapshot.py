#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  退出码：7=环境自检失败（沙箱假python·审查P2-3补）
monthly_data_snapshot.py — 月报数据采集快照（数据可信度闭环·第一层）

设计哲学：把"数据准确呈现"从靠AI自觉变成靠系统机制强制。
AI写月报时只能引用本脚本产出的JSON快照，禁止自己去查然后写。

采集范围（8月月报所有量化指标）：
  1. 日记维度：番茄/睡眠/评级/心情/周分布（扫描该月所有日记YAML）
  2. 概念库维度：概念卡总数/碰撞队列状态/碰撞产出卡数/INDEX碰撞来源
  3. 系统维度：该月系统日志数
  4. 元信息：快照时间戳/月份/数据源路径

用法：
  python3 monthly_data_snapshot.py --month 2026-08
  python3 monthly_data_snapshot.py --month 2026-08 --output /path/to/snapshot.json

输出：带时间戳的JSON快照，每个字段自带 definition + value + source + collected_at
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys
import re
import json
import argparse
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path

# === 环境自愈（第一性原理根治·Hermes 沙箱 HOME 劫持·与其他脚本同律）===
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dbenv

# === 路径集中声明（经dbenv解析·破除沙箱 HOME 污染）===
HOME = str(dbenv.HOME)
DIARY_DIR = os.path.join(HOME, "[日记仓库]", "1-每日计划", "01-日记")
CONCEPT_DIR = os.path.join(HOME, "[日记仓库]", "2-知识库", "08-概念层")
AI_LIB_DIR = os.path.join(HOME, "[记忆共享中心]", "知识库", "AI学习库")
INDEX_PATH = os.path.join(AI_LIB_DIR, "INDEX.md")
COLLISION_JSON = os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "知识联邦引擎", "collision_candidates.json")
SYSLOG_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "工作日志", "系统日志")
SNAPSHOT_DIR = os.path.join(os.path.expanduser("[记忆共享中心]"), "技能配置", "daily-buddy", "data_snapshots")


def field(definition, value, source):
    """构造带定义+来源+采集时间的字段（数据自解释）"""
    return {
        "value": value,
        "definition": definition,
        "source": source,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def parse_diary_yaml(filepath):
    """解析单篇日记YAML frontmatter，返回关键指标dict"""
    result = {
        "rating": None, "tomato": 0, "sleep_duration": 0,
        "energy_pred": None, "energy_actual": None,
        "calm_pred": None, "calm_actual": None,
        "satisfaction": None
    }
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        # 提取YAML frontmatter
        m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not m:
            return result
        yaml_text = m.group(1)
        # rating
        rm = re.search(r"^rating:\s*(\S+)", yaml_text, re.MULTILINE)
        if rm:
            result["rating"] = rm.group(1).strip()
        # achievement_data 块
        am = re.search(r"achievement_data:\s*\n((?:\s+\S.*\n)+)", yaml_text)
        if am:
            block = am.group(1)
            for key in ["tomato", "sleep_duration", "energy_pred", "energy_actual",
                        "calm_pred", "calm_actual", "satisfaction"]:
                km = re.search(rf"^\s+{key}:\s*(\S+)", block, re.MULTILINE)
                if km:
                    val = km.group(1).strip().strip('"').strip("'")
                    try:
                        result[key] = float(val) if "." in val else int(val)
                    except ValueError:
                        result[key] = val
    except Exception as e:
        print(f"[WARN] 解析日记失败 {filepath}: {e}", file=sys.stderr)
    return result


def collect_diary_data(month):
    """采集该月所有日记的统计数据"""
    month_dir = os.path.join(DIARY_DIR, month)
    if not os.path.isdir(month_dir):
        return {"error": f"日记目录不存在: {month_dir}"}

    diary_files = sorted([f for f in os.listdir(month_dir)
                          if f.startswith(month) and f.endswith(".md")])
    total_days = len(diary_files)

    total_tomato = 0
    total_sleep = 0.0
    sleep_days = 0
    ratings = Counter()
    sleep_ge7 = 0
    sleep_lt6 = 0
    sleep_lt5 = 0
    weekly_tomato = defaultdict(int)
    energy_actual_list = []
    calm_actual_list = []
    satisfaction_list = []

    for fname in diary_files:
        filepath = os.path.join(month_dir, fname)
        data = parse_diary_yaml(filepath)
        date_str = fname.replace(".md", "")

        # 番茄
        if data["tomato"] and isinstance(data["tomato"], (int, float)):
            total_tomato += data["tomato"]
            # 周分布（ISO周）
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                week_num = dt.isocalendar()[1]
                weekly_tomato[f"W{week_num}"] += data["tomato"]
            except ValueError:
                pass

        # 睡眠
        if data["sleep_duration"] and isinstance(data["sleep_duration"], (int, float)):
            total_sleep += data["sleep_duration"]
            sleep_days += 1
            if data["sleep_duration"] >= 7:
                sleep_ge7 += 1
            if data["sleep_duration"] < 6:
                sleep_lt6 += 1
            if data["sleep_duration"] < 5:
                sleep_lt5 += 1

        # 评级
        if data["rating"]:
            ratings[data["rating"]] += 1

        # 心情
        if data["energy_actual"] and isinstance(data["energy_actual"], (int, float)):
            energy_actual_list.append(data["energy_actual"])
        if data["calm_actual"] and isinstance(data["calm_actual"], (int, float)):
            calm_actual_list.append(data["calm_actual"])
        if data["satisfaction"] and isinstance(data["satisfaction"], (int, float)):
            satisfaction_list.append(data["satisfaction"])

    avg_tomato = round(total_tomato / total_days, 1) if total_days > 0 else 0
    avg_sleep = round(total_sleep / sleep_days, 2) if sleep_days > 0 else 0
    total_sleep_h = round(total_sleep, 2)

    return {
        "total_days": field("该月日记总天数", total_days, f"{month_dir}/*.md"),
        "total_tomato": field("该月番茄总数", total_tomato, f"{month_dir}/*.md YAML achievement_data.tomato"),
        "avg_tomato": field("日均番茄数", avg_tomato, "total_tomato / total_days"),
        "total_sleep_hours": field("该月睡眠总时长（小时）", total_sleep_h, f"{month_dir}/*.md YAML achievement_data.sleep_duration"),
        "avg_sleep_hours": field("日均睡眠时长（小时）", avg_sleep, "total_sleep_hours / sleep_days"),
        "sleep_days_with_data": field("有睡眠数据的天数", sleep_days, f"{month_dir}/*.md"),
        "sleep_ge7_days": field("睡眠≥7h的天数", sleep_ge7, f"{month_dir}/*.md sleep_duration>=7"),
        "sleep_lt6_days": field("睡眠<6h的天数", sleep_lt6, f"{month_dir}/*.md sleep_duration<6"),
        "sleep_lt5_days": field("睡眠<5h的天数", sleep_lt5, f"{month_dir}/*.md sleep_duration<5"),
        "rating_distribution": field("评级分布（A/B/C/S各天数）", dict(ratings), f"{month_dir}/*.md YAML rating"),
        "weekly_tomato": field("周番茄分布（ISO周号→番茄数）", dict(weekly_tomato), f"{month_dir}/*.md 按isocalendar周聚合"),
        "avg_energy_actual": field("日均精力实际值", round(sum(energy_actual_list)/len(energy_actual_list), 2) if energy_actual_list else None, f"{month_dir}/*.md achievement_data.energy_actual"),
        "avg_calm_actual": field("日均平静实际值", round(sum(calm_actual_list)/len(calm_actual_list), 2) if calm_actual_list else None, f"{month_dir}/*.md achievement_data.calm_actual"),
        "avg_satisfaction": field("日均满意度", round(sum(satisfaction_list)/len(satisfaction_list), 2) if satisfaction_list else None, f"{month_dir}/*.md achievement_data.satisfaction"),
    }


def collect_concept_data():
    """采集概念库健康数据"""
    # 概念卡总数
    concept_files = [f for f in os.listdir(CONCEPT_DIR)
                     if f.startswith("C-") and f.endswith(".md")] if os.path.isdir(CONCEPT_DIR) else []
    concept_total = len(concept_files)

    # 碰撞队列状态
    collision_data = {"total": 0, "consumed": 0, "pending": 0,
                      "qualified_pending": 0, "total_concepts_in_json": 0}
    if os.path.exists(COLLISION_JSON):
        with open(COLLISION_JSON, encoding="utf-8") as f:
            cdata = json.load(f)
        candidates = cdata.get("candidates", [])
        collision_data["total"] = len(candidates)
        collision_data["total_concepts_in_json"] = cdata.get("total_concepts", 0)
        for c in candidates:
            status = c.get("status", "pending")
            if status == "consumed":
                collision_data["consumed"] += 1
            else:
                collision_data["pending"] += 1
                if c.get("cross_domain") and c.get("cross_owner"):
                    collision_data["qualified_pending"] += 1

    # 碰撞产出卡数（立场卡#S）
    collision_cards_md = [f for f in os.listdir(AI_LIB_DIR)
                          if f.startswith("立场卡#S") and f.endswith(".md")] if os.path.isdir(AI_LIB_DIR) else []
    collision_cards_all = [f for f in os.listdir(AI_LIB_DIR)
                           if f.startswith("立场卡#S")] if os.path.isdir(AI_LIB_DIR) else []
    collision_output_md = len(collision_cards_md)
    collision_output_all = len(collision_cards_all)
    # 最大编号
    max_s_num = 0
    for f in collision_cards_all:
        m = re.search(r"立场卡#S(\d+)", f)
        if m:
            max_s_num = max(max_s_num, int(m.group(1)))

    # INDEX碰撞来源统计
    index_data = {"total_cards": 0, "with_collision_source": 0, "unique_concepts_in_collision": 0}
    concepts_in_collision = set()
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            for line in f:
                if not (line.startswith("| 立场卡") or line.startswith("| 技能卡")):
                    continue
                index_data["total_cards"] += 1
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) < 6:
                    continue
                src = cells[-1]
                m = re.search(r"\[(C-[0-9]+)\s*[×x]\s*(C-[0-9]+)\]", src)
                if m:
                    index_data["with_collision_source"] += 1
                    concepts_in_collision.add(m.group(1))
                    concepts_in_collision.add(m.group(2))
        index_data["unique_concepts_in_collision"] = len(concepts_in_collision)

    collision_coverage = round(index_data["unique_concepts_in_collision"] / concept_total * 100, 1) if concept_total > 0 else 0
    concepts_not_in_collision = concept_total - index_data["unique_concepts_in_collision"]
    source_coverage_rate = round(index_data["with_collision_source"] / index_data["total_cards"] * 100, 1) if index_data["total_cards"] > 0 else 0

    return {
        "concept_total": field("概念卡总数（C-*.md）", concept_total, f"{CONCEPT_DIR}/C-*.md"),
        "collision_queue_total": field("碰撞候选配对总数", collision_data["total"], COLLISION_JSON),
        "collision_queue_consumed": field("已消费配对数（status=consumed）", collision_data["consumed"], f"{COLLISION_JSON} status=consumed"),
        "collision_queue_pending": field("真pending配对数（status≠consumed）", collision_data["pending"], f"{COLLISION_JSON} status=pending"),
        "collision_queue_qualified_pending": field("合格可碰pending数（跨域cross_domain+跨主体cross_owner）", collision_data["qualified_pending"], f"{COLLISION_JSON} pending且cross_domain+cross_owner"),
        "collision_output_cards_md": field("碰撞产出卡数（.md可读文件）", collision_output_md, f"{AI_LIB_DIR}/立场卡#S*.md"),
        "collision_output_cards_all": field("碰撞产出卡数（含非.md文件）", collision_output_all, f"{AI_LIB_DIR}/立场卡#S*"),
        "collision_output_max_s_num": field("碰撞产出卡最大S编号", max_s_num, f"{AI_LIB_DIR}/立场卡#S* 编号最大值"),
        "index_total_cards": field("INDEX中立场卡/技能卡总行数", index_data["total_cards"], INDEX_PATH),
        "index_with_collision_source": field("INDEX中有碰撞来源[C-X×C-Y]的行数", index_data["with_collision_source"], f"{INDEX_PATH} 碰撞来源列"),
        "index_source_coverage_rate": field("碰撞来源覆盖率（%）", source_coverage_rate, "index_with_collision_source / index_total_cards"),
        "concepts_in_collision": field("参与碰撞的不同概念数", index_data["unique_concepts_in_collision"], f"{INDEX_PATH} 碰撞来源列去重"),
        "collision_coverage_rate": field("概念碰撞覆盖率（%）", collision_coverage, "concepts_in_collision / concept_total"),
        "concepts_not_in_collision": field("未参与碰撞的概念数", concepts_not_in_collision, "concept_total - concepts_in_collision"),
    }


def collect_syslog_data(month):
    """采集该月系统日志数据"""
    syslog_files = [f for f in os.listdir(SYSLOG_DIR)
                     if f.startswith(f"系统日志_{month}") and f.endswith(".md")] if os.path.isdir(SYSLOG_DIR) else []
    return {
        "syslog_count": field("该月系统日志文件数", len(syslog_files), f"{SYSLOG_DIR}/系统日志_{month}-*.md"),
    }


def collect_video_data(month):
    """采集视频发布数据（严格完成态检测）"""
    month_dir = os.path.join(DIARY_DIR, month)
    video_publish_days = []
    if os.path.isdir(month_dir):
        for fname in sorted(os.listdir(month_dir)):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(month_dir, fname)
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                # 严格完成态检测：rating_reason或正文中包含"发布了/已发布/发布完成/发了" + "视频"
                # 排除"计划/准备/要/打算/明天/下周"等未来态
                publish_patterns = [
                    r"发布了.{0,20}视频",
                    r"视频.{0,10}发布了",
                    r"已发布.{0,20}视频",
                    r"视频.{0,10}已发布",
                    r"发了.{0,10}视频",
                    r"视频.{0,10}上线",
                ]
                future_patterns = [r"计划发布", r"准备发布", r"要发布", r"打算发布", r"明天发布", r"下周发布", r"即将发布"]
                is_published = False
                for pat in publish_patterns:
                    if re.search(pat, content):
                        # 排除未来态
                        if not any(re.search(fp, content) for fp in future_patterns):
                            is_published = True
                            break
                if is_published:
                    date_str = fname.replace(".md", "")
                    # 提取视频标题
                    title_m = re.search(r"发布[了]?[「\"']?(.+?)[」\"']?视频", content)
                    title = title_m.group(1) if title_m else "未命名"
                    video_publish_days.append({"date": date_str, "title": title})
            except Exception:
                pass
    return {
        "video_publish_count": field("该月视频发布条数（严格完成态检测）", len(video_publish_days), f"{month_dir}/*.md 完成态发布标记检测"),
        "video_publish_details": field("视频发布详情（日期+标题）", video_publish_days, f"{month_dir}/*.md"),
    }


def main():
    if not dbenv.self_check(verbose=True):
        sys.exit(9)
    parser = argparse.ArgumentParser(description="月报数据采集快照")
    parser.add_argument("--month", required=True, help="月份，格式YYYY-MM，如2026-08")
    parser.add_argument("--output", help="输出JSON路径（默认保存到data_snapshots目录）")
    args = parser.parse_args()

    month = args.month
    now = datetime.now()

    # 采集所有维度
    snapshot = {
        "snapshot_meta": {
            "month": month,
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "generator": "monthly_data_snapshot.py v1.0",
            "purpose": "月报数据可信度闭环·AI写月报时只能引用本快照数据",
            "data_sources": {
                "diary": DIARY_DIR,
                "concept": CONCEPT_DIR,
                "collision": COLLISION_JSON,
                "ai_lib": AI_LIB_DIR,
                "index": INDEX_PATH,
                "syslog": SYSLOG_DIR,
            }
        },
        "diary": collect_diary_data(month),
        "concept_health": collect_concept_data(),
        "syslog": collect_syslog_data(month),
        "video": collect_video_data(month),
    }

    # 输出
    if args.output:
        output_path = args.output
    else:
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        output_path = os.path.join(SNAPSHOT_DIR, f"{month}_data_snapshot.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"✅ 数据快照已生成: {output_path}")
    print(f"   月份: {month}")
    print(f"   日记天数: {snapshot['diary']['total_days']['value']}")
    print(f"   番茄总数: {snapshot['diary']['total_tomato']['value']} (日均{snapshot['diary']['avg_tomato']['value']})")
    print(f"   睡眠日均: {snapshot['diary']['avg_sleep_hours']['value']}h")
    print(f"   评级分布: {snapshot['diary']['rating_distribution']['value']}")
    print(f"   概念卡总数: {snapshot['concept_health']['concept_total']['value']}")
    print(f"   碰撞队列: total={snapshot['concept_health']['collision_queue_total']['value']} consumed={snapshot['concept_health']['collision_queue_consumed']['value']} pending={snapshot['concept_health']['collision_queue_pending']['value']} (合格{snapshot['concept_health']['collision_queue_qualified_pending']['value']})")
    print(f"   碰撞产出卡: {snapshot['concept_health']['collision_output_cards_md']['value']}张.md ({snapshot['concept_health']['collision_output_cards_all']['value']}个文件·最大S{snapshot['concept_health']['collision_output_max_s_num']['value']})")
    print(f"   概念碰撞覆盖率: {snapshot['concept_health']['collision_coverage_rate']['value']}%")
    print(f"   视频发布: {snapshot['video']['video_publish_count']['value']}条")
    print(f"   系统日志: {snapshot['syslog']['syslog_count']['value']}篇")
    return 0


if __name__ == "__main__":
    sys.exit(main())
