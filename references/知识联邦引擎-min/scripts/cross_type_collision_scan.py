#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cross_type_collision_scan.py v1.0 — 蓝图索引卡↔立场卡跨类型碰撞扫描
职责: 基于kb_vectors.json向量缓存，计算每张蓝图索引卡与所有立场卡的余弦相似度，
      找出top-5最相关立场卡，生成跨类型碰撞候选清单。
      零模型加载，纯向量计算，秒级完成。
设计依据: 知识库设计哲学"碰撞产生洞察"——相关卡片自动碰撞→多视角评测→reconcile→回写
用法: python3 cross_type_collision_scan.py [--top N] [--threshold 0.3] [--output path]
v1.0: 蓝图索引卡↔立场卡跨类型碰撞，纯向量计算，输出Markdown碰撞候选清单。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os, json, argparse, math
from datetime import datetime

# ==== 路径配置（端用户版（2026-10-10 腿F案入包·真源=开发工具/知识联邦引擎/scripts 同逻辑·路径收口 _paths 零硬编码）） ====
from _paths import INSTALLED, FED, AILIB_DIR
VECTORS_FILE = os.path.join(FED, "vectors", "kb_vectors.json") if FED else None
DEFAULT_OUTPUT = (os.path.join(AILIB_DIR, "跨类型碰撞候选-蓝图索引卡↔立场卡.md")
                  if AILIB_DIR else os.path.join(os.getcwd(), "跨类型碰撞候选-蓝图索引卡↔立场卡.md"))

def cosine_similarity(v1, v2):
    """余弦相似度"""
    dot = sum(a*b for a,b in zip(v1,v2))
    norm1 = math.sqrt(sum(a*a for a in v1))
    norm2 = math.sqrt(sum(b*b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

def extract_card_name(path):
    """从文件路径提取卡片名称"""
    basename = os.path.basename(path)
    # 蓝图索引卡-成长箱设计哲学.md → 成长箱设计哲学
    name = basename.replace("蓝图索引卡-", "").replace(".md", "")
    # 立场卡#S001-标题.md → S001-标题
    if name.startswith("立场卡#"):
        name = name.replace("立场卡#", "")
    return name

def classify_collision(score):
    """根据相似度分数分类碰撞类型（基于实测分布校准：蓝图↔立场卡平均分0.57，top1在0.65-0.74）"""
    if score >= 0.70:
        return "🔥 强共识", "立场卡与蓝图设计哲学高度一致，可互相印证（top1级别）"
    elif score >= 0.67:
        return "⚡ 互补", "立场卡补充了蓝图设计哲学的具体应用场景（top2-3级别）"
    elif score >= 0.64:
        return "💡 潜在碰撞", "可能存在共识或冲突，需人工审阅（top4-5级别）"
    else:
        return "弱相关", "相似度较低，暂不推荐碰撞"

def main():
    parser = argparse.ArgumentParser(description="蓝图索引卡↔立场卡跨类型碰撞扫描")
    parser.add_argument("--top", type=int, default=5, help="每张蓝图索引卡返回top-N立场卡")
    parser.add_argument("--threshold", type=float, default=0.64, help="最低相似度阈值")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="输出文件路径")
    args = parser.parse_args()

    if not INSTALLED or not VECTORS_FILE:
        print("未安装态（记忆共享中心自推导失败）——跳过扫描")
        return
    if not os.path.exists(VECTORS_FILE):
        raise SystemExit(f"❌ 向量缓存不存在: {VECTORS_FILE}（先跑 build_kb_vectors.py）")

    print("📊 加载向量缓存...")
    with open(VECTORS_FILE) as f:
        data = json.load(f)
    vecs = data["vectors"]
    print(f"   总向量数: {len(vecs)}")
    
    # 分离蓝图索引卡和立场卡
    blueprint_cards = {}
    stance_cards = {}
    for path, vec in vecs.items():
        if "10 蓝图索引卡" in path and path.endswith(".md") and "references" not in path:
            blueprint_cards[path] = vec
        elif "AI学习库" in path and "立场卡#" in path and path.endswith(".md"):
            stance_cards[path] = vec
    
    print(f"   蓝图索引卡: {len(blueprint_cards)} 张")
    print(f"   立场卡: {len(stance_cards)} 张")
    
    # 计算相似度
    print(f"\n🔍 计算跨类型相似度（top-{args.top}，阈值{args.threshold}）...")
    all_collisions = []
    
    for bp_path, bp_vec in blueprint_cards.items():
        bp_name = extract_card_name(bp_path)
        similarities = []
        for st_path, st_vec in stance_cards.items():
            score = cosine_similarity(bp_vec, st_vec)
            if score >= args.threshold:
                st_name = extract_card_name(st_path)
                collision_type, description = classify_collision(score)
                similarities.append({
                    "stance_card": st_name,
                    "stance_path": st_path,
                    "score": round(score, 4),
                    "collision_type": collision_type,
                    "description": description
                })
        # 按分数排序，取top-N
        similarities.sort(key=lambda x: x["score"], reverse=True)
        top_matches = similarities[:args.top]
        if top_matches:
            all_collisions.append({
                "blueprint_card": bp_name,
                "blueprint_path": bp_path,
                "matches": top_matches
            })
    
    # 统计
    total_collisions = sum(len(c["matches"]) for c in all_collisions)
    strong = sum(1 for c in all_collisions for m in c["matches"] if "强共识" in m["collision_type"])
    complementary = sum(1 for c in all_collisions for m in c["matches"] if "互补" in m["collision_type"])
    potential = sum(1 for c in all_collisions for m in c["matches"] if "潜在碰撞" in m["collision_type"])
    
    # 生成Markdown报告
    print(f"\n📝 生成碰撞候选报告...")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# 跨类型碰撞候选：蓝图索引卡↔立场卡

> **生成时间**：{now}
> **扫描范围**：{len(blueprint_cards)}张蓝图索引卡 × {len(stance_cards)}张立场卡
> **算法**：BAAI/bge-base-zh-v1.5 余弦相似度（768维向量·2026-09-10 统一单模型，纯向量计算零token）
> **参数**：top-{args.top}，阈值≥{args.threshold}
> **碰撞总数**：{total_collisions}组（🔥强共识{strong} / ⚡互补{complementary} / 💡潜在碰撞{potential}）

---

## 碰撞类型说明

| 类型 | 相似度区间 | 含义 |
|:---|:---|:---|
| 🔥 强共识 | ≥0.70 | 立场卡与蓝图设计哲学高度一致，可互相印证（top1级别） |
| ⚡ 互补 | 0.67-0.70 | 立场卡补充了蓝图设计哲学的具体应用场景（top2-3级别） |
| 💡 潜在碰撞 | 0.64-0.67 | 可能存在共识或冲突，需人工审阅（top4-5级别） |

---

"""
    for collision in all_collisions:
        md += f"## 📌 {collision['blueprint_card']}\n\n"
        for i, m in enumerate(collision["matches"], 1):
            md += f"### {i}. {m['collision_type']} | {m['stance_card']} (相似度: {m['score']})\n\n"
            md += f"- **立场卡路径**：`{m['stance_path']}`\n"
            md += f"- **碰撞说明**：{m['description']}\n"
            md += f"- **建议动作**：Read立场卡全文，判断是共识/冲突/互补，产出碰撞卡或回写\n\n"
        md += "---\n\n"
    
    # 写入文件
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)
    
    print(f"\n✅ 完成！")
    print(f"   蓝图索引卡: {len(blueprint_cards)} 张")
    print(f"   立场卡: {len(stance_cards)} 张")
    print(f"   碰撞候选: {total_collisions} 组")
    print(f"   🔥 强共识: {strong} | ⚡ 互补: {complementary} | 💡 潜在碰撞: {potential}")
    print(f"   输出文件: {args.output}")

if __name__ == "__main__":
    main()
