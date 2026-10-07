#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
collision_scan.py — 三库联邦·概念碰撞检测（D-F8实现）
设计依据: 08-三库联邦设计.md D-F8（检测与生成解耦·三条硬修正）
架构: scan=纯向量数学·零token·跨域加权·写候选队列（缓存性质·可随概念层重建重扫）
模型: BAAI/bge-base-zh-v1.5（2026-09-10 统一单模型·本地·768维·KB_MODEL 可回滚）
铁律: 阈值必须本地模型实测校准，⛔不可直接抄0.6-0.75 / 跨域中等相似=火花，同域降权 / 时间=系统时钟
用法:
  python3 collision_scan.py scan       # 全量扫描概念层→写碰撞候选队列
  python3 collision_scan.py calibrate  # 用已知好/坏配对实测校准阈值（首跑前必做）
  python3 collision_scan.py status     # 查看候选队列状态
"""
import os
import sys, os, json, glob, re, itertools
from datetime import datetime, date

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ==== 路径配置（布洛陀发布时替换为占位符 {{USER_HOME}} 等） ====
from _paths import FED, CONCEPTS_DIR, INSTALLED
VECTOR_CACHE = os.path.join(FED, "vectors", "concept_vectors.json") if FED else None
CANDIDATES_FILE = os.path.join(FED, "collision_candidates.json") if FED else None
CALIBRATION_FILE = os.path.join(FED, "calibration.json") if FED else None
LOG_FILE = os.path.join(FED, "log.md") if FED else None

MODEL_NAME = os.environ.get("KB_MODEL") or "BAAI/bge-base-zh-v1.5"  # 2026-09-10 统一单模型（原 bge-large·切 base 省内存且质量不降）；换模型→向量缓存整体作废重建（D-F2）
DEFAULT_BAND = (0.60, 0.75)            # 参考区间，仅calibrate缺失时的临时兜底并强制告警
CROSS_DOMAIN_BONUS = 0.05              # 跨域加权：跨域配对相似度+bonus后再比阈值（同域不加=相对降权）

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def append_log(entry_type, detail):
    if not LOG_FILE:
        return
    with open(LOG_FILE, "a") as f:
        f.write(f"\n## [{date.today().isoformat()}] {entry_type} | {detail} | 记录时间:{now_str()}\n")

def load_concepts():
    """读概念层全部概念卡 → [{id,name,definition,domain,owner}]"""
    out = []
    for p in sorted(glob.glob(os.path.join(CONCEPTS_DIR, "C-*.md"))):
        t = open(p, encoding="utf-8").read()
        g = lambda k: (m.group(1).strip().strip('"') if (m := re.search(rf'{k}:\s*"?([^"\n]+)"?', t)) else None)
        if g("concept_id") and g("definition"):
            out.append({"id": g("concept_id"), "name": g("concept_name"),
                        "definition": g("definition"), "domain": g("domain") or "未分类",
                        "owner": g("source_owner") or "未知"})
    return out

def get_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise SystemExit("ℹ️ 语义增强（bge 模型）未安装——碰撞扫描需要它。"
                         "Phase B 全功能不受影响；要启用语义级碰撞请装语义增强（见 INSTALL Phase C）。")
    return SentenceTransformer(MODEL_NAME)

def build_vectors(concepts, model):
    """向量缓存=派生数据（D-F2）：标注模型名，模型不符整体重建。
    缓存以当前概念层为准：已删除卡的 stale 条目自动剔除（v2 根治·2026-08-11 删卡后残留）"""
    cache = {}
    if os.path.exists(VECTOR_CACHE):
        c = json.load(open(VECTOR_CACHE))
        if c.get("model") == MODEL_NAME:
            cache = c.get("vectors", {})
        else:
            print(f"模型变更({c.get('model')}→{MODEL_NAME})，向量缓存整体重建")
    current_ids = {c["id"] for c in concepts}
    stale = [k for k in cache if k not in current_ids]
    for k in stale:
        del cache[k]
    if stale:
        print(f"清理失效缓存: {len(stale)}条({', '.join(sorted(stale))})")
    todo = [c for c in concepts if c["id"] not in cache]
    if todo:
        vecs = model.encode([c["definition"] for c in todo], normalize_embeddings=True)
        for c, v in zip(todo, vecs):
            cache[c["id"]] = [round(float(x), 6) for x in v]
    os.makedirs(os.path.dirname(VECTOR_CACHE), exist_ok=True)
    json.dump({"model": MODEL_NAME, "generated": now_str(), "vectors": cache},
              open(VECTOR_CACHE, "w"))
    return cache

def load_band():
    """阈值来源=calibration.json（实测校准）。缺失→临时兜底+强制告警（不可直接抄未校准区间）"""
    if os.path.exists(CALIBRATION_FILE):
        c = json.load(open(CALIBRATION_FILE))
        if c.get("model") == MODEL_NAME:
            return tuple(c["band"]), True
    print("⚠️ 未找到本模型的校准记录，临时用参考区间——首跑前必须执行 calibrate")
    return DEFAULT_BAND, False

def cmd_scan():
    concepts = load_concepts()
    if len(concepts) < 2:
        append_log("scan", f"skipped: 概念数不足({len(concepts)})")
        print(f"SKIP-LOGGED: 概念层仅{len(concepts)}个概念，无可碰撞"); return
    import numpy as np
    model = get_model()
    vectors = build_vectors(concepts, model)
    (lo, hi), calibrated = load_band()
    candidates = []
    for a, b in itertools.combinations(concepts, 2):
        sim = float(np.dot(np.array(vectors[a["id"]]), np.array(vectors[b["id"]])))
        cross = a["domain"] != b["domain"]
        eff = sim + (CROSS_DOMAIN_BONUS if cross else 0)  # 跨域加权（D-F8修正2）
        if lo <= eff <= hi:
            candidates.append({
                "pair": [a["id"], b["id"]], "names": [a["name"], b["name"]],
                "raw_sim": round(sim, 4), "effective_sim": round(eff, 4),
                "cross_domain": cross, "domains": [a["domain"], b["domain"]],
                "cross_owner": a["owner"] != b["owner"],  # 跨主体=联邦最高价值碰撞
                "status": "pending", "detected": now_str()})
    candidates.sort(key=lambda c: (-c["cross_domain"], -c["cross_owner"], -c["effective_sim"]))
    json.dump({"model": MODEL_NAME, "band": [lo, hi], "calibrated": calibrated,
               "scanned": now_str(), "total_concepts": len(concepts),
               "candidates": candidates},
              open(CANDIDATES_FILE, "w"), ensure_ascii=False, indent=2)
    append_log("scan", f"概念{len(concepts)} 候选{len(candidates)} 区间[{lo},{hi}]"
                       f"{'' if calibrated else ' ⚠️未校准'}")
    print(f"SCANNED: {len(concepts)}概念 → {len(candidates)}候选（跨域优先排序）→ {CANDIDATES_FILE}")
    if not calibrated:
        print("⚠️ 本次使用未校准参考区间，结果仅供参考——先跑 calibrate")
    # 焊闸（2026-09-03·写侧根治）：scan 后自动对账，假 pending 结构性不可能复发
    # 重扫即对账·幂等单向（INDEX 权威→队列对齐），不再依赖任何人记得跑对账
    try:
        import sync_collision_queue
        sync_collision_queue.main()
    except Exception as e:
        print(f"⚠️ scan 后自动对账失败（候选队列已写入，对账需手工补跑 sync_collision_queue.py）: {e}")

def cmd_calibrate():
    """阈值校准（）：已知好配对(跨域有火花)应落入区间，坏配对(同义废话/完全无关)应落出区间。
    配对基准需人工确认——脚本给出全部配对相似度分布+建议区间，最终区间经确认后写入calibration.json"""
    concepts = load_concepts()
    if len(concepts) < 2:
        print(f"概念层仅{len(concepts)}个概念，校准需≥2（建议首批真跑入库后再校准）"); return
    import numpy as np
    model = get_model()
    vectors = build_vectors(concepts, model)
    sims = []
    for a, b in itertools.combinations(concepts, 2):
        sim = float(np.dot(np.array(vectors[a["id"]]), np.array(vectors[b["id"]])))
        sims.append((round(sim, 4), a["domain"] == b["domain"],
                     f'{a["name"]} × {b["name"]}'))
    sims.sort(reverse=True)
    print(f"=== 全配对相似度分布（{len(concepts)}概念·{len(sims)}对·模型{MODEL_NAME}）===")
    for s, same, label in sims:
        print(f"  {s:.4f} {'[同域]' if same else '[跨域]'} {label}")
    vals = [s for s, _, _ in sims]
    import statistics
    print(f"\n统计: max={max(vals):.4f} min={min(vals):.4f} "
          f"median={statistics.median(vals):.4f} mean={statistics.mean(vals):.4f}")
    print("\n下一步：人工看分布——「有火花的跨域对」聚在哪个区间就取哪段。")
    print(f"确认后写入: python3 {os.path.abspath(__file__)} set-band <lo> <hi>")

def cmd_set_band(lo, hi):
    json.dump({"model": MODEL_NAME, "band": [float(lo), float(hi)],
               "set_at": now_str(), "note": "实测校准区间"},
              open(CALIBRATION_FILE, "w"), ensure_ascii=False, indent=2)
    append_log("scan", f"阈值校准落定 band=[{lo},{hi}] model={MODEL_NAME}")
    print(f"CALIBRATED: band=[{lo},{hi}] 已写入 {CALIBRATION_FILE}")

def cmd_status():
    if not os.path.exists(CANDIDATES_FILE):
        print("候选队列: 尚未扫描"); return
    d = json.load(open(CANDIDATES_FILE))
    pending = [c for c in d["candidates"] if c["status"] == "pending"]
    print(f"候选队列: 总{len(d['candidates'])} 待消费{len(pending)} | "
          f"上次扫描:{d['scanned']} | 区间{d['band']}{'✅已校准' if d['calibrated'] else '⚠️未校准'}")
    for c in pending[:5]:
        tag = ("🌐跨域" if c["cross_domain"] else "同域") + ("·👥跨主体" if c["cross_owner"] else "")
        print(f"  [{tag}] {c['names'][0]} × {c['names'][1]} (sim={c['raw_sim']})")

if __name__ == "__main__":
    if not INSTALLED:
        print("ℹ️ 未安装态（包内暂存）——碰撞扫描在安装后可用；语义增强可选。")
        sys.exit(0)
    from _engine_env import ensure_engine_python; ensure_engine_python()  # v2026-08-05: 根治PATH漂移
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "scan": cmd_scan()
    elif cmd == "calibrate": cmd_calibrate()
    elif cmd == "set-band": cmd_set_band(sys.argv[2], sys.argv[3])
    elif cmd == "status": cmd_status()
    else: print(__doc__)