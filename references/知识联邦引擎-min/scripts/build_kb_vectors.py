#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
build_kb_vectors.py v0.2-enduser — 语义向量库构建（卡生产引擎·端用户版）
（v0.2 2026-10-07 同步作者侧 v1.2/v1.3：标签诚实化+CPU EP+npy 双写+PAT-080 增量产物非空校验——
  否则端用户复刻量化链时 build 打 base@qint8 标签、search_kb 读 large@qint8，标签不符静默降 BM25）

与 search_kb.py 的 build_docs() 同源（BM25 索引与向量库天然对齐）：
  文档文本 = title + summary + 正文前 500 字（与 search_kb 索引文本一致）。

缓存：[记忆共享中心]/脚本中心/知识联邦引擎/vectors/kb_vectors.json
增量：文档文本 md5 变化才重算单条；模型名变化 → 整体重建。

端用户态说明：
  - 路径经 _paths.py 自推导（⛔零硬编码家目录）；未安装态不建库
  - search_kb.py 扁平部署在 [MC]/脚本中心/（本件在 脚本中心/知识联邦引擎/scripts/）→ 双路 import
  - 语义层解释器自路由（候选 venv 探测）；依赖/模型缺失 → 优雅跳过（exit 0 不阻塞调用方）
  - 由 regen_ailib_index.py 自动挂接（落卡/INDEX 重建后自动增量构建）→ 装好语义增强后自动点亮

用法：
  python3 build_kb_vectors.py            # 构建/增量更新
  python3 build_kb_vectors.py --status   # 查看缓存状态
"""
import os
import sys
import json
import hashlib
try:
    import fcntl          # Unix/macOS：文件锁防并发撕裂
except ImportError:
    # Windows 无 fcntl——本件属对外发布包（卡生产引擎·装到 脚本中心/知识联邦引擎/），
    # 必须能在 Win 导入并运行。降级守设计律②「降级不阻塞」：保 API 形状的空实现，
    # 锁变 no-op，缓存整写的幂等性兜住并发风险。
    # ⚠️ 同型守卫共三处（本件 / audit_search_kb / transcript_reader），改语义须三处齐改；
    #    ⚠️ 本件在 mirror-manifest 里**无登记源**（`知识联邦引擎-min/` 整块未纳管），
    #    作者侧同名件 `开发工具/知识联邦引擎/scripts/build_kb_vectors.py` 已同步同一补丁——
    #    两侧内容对齐后，任一侧被覆盖都不丢修复；根修＝为 -min 子集登记源（待归属端裁）。
    class _NoFcntl:
        LOCK_EX = LOCK_UN = LOCK_NB = 0

        @staticmethod
        def flock(fh, op):
            return None
    fcntl = _NoFcntl()
import time
from datetime import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)


def _locate_search_kb():
    """定位 search_kb.py 所在目录——覆盖三种布局：
      作者态（同目录）/ 端用户部署态（[MC]/脚本中心/ 根）/ 包内暂存态（references/scripts/）。"""
    cands = [os.path.join(_HERE, "search_kb.py")]
    d = _HERE
    for _ in range(5):
        d = os.path.dirname(d)
        cands.append(os.path.join(d, "search_kb.py"))
        cands.append(os.path.join(d, "scripts", "search_kb.py"))
        if d == os.path.dirname(d):
            break
    for c in cands:
        if os.path.isfile(c):
            return os.path.dirname(c)
    return None


skb = None
_sb_dir = _locate_search_kb()
if _sb_dir:
    sys.path.insert(0, _sb_dir)
    try:
        import search_kb as skb  # 复用 build_docs（单一文档源）
    except ImportError:
        skb = None

try:
    from _paths import FED, INSTALLED  # 路径单一真源
except ImportError:
    # 兜底：向上找「脚本中心」祖先自推导（与 search_kb._find_mc 同构·防单件被挪出引擎目录）
    _d, FED = _HERE, None
    for _ in range(6):
        _d = os.path.dirname(_d)
        if os.path.basename(_d) == "脚本中心":
            FED = os.path.join(_d, "知识联邦引擎")
            break
        if _d == os.path.dirname(_d):
            break
    INSTALLED = FED is not None

CACHE_FILE = os.path.join(FED, "vectors", "kb_vectors.json") if FED else None
# v0.2 同步 v1.3：二进制向量库双写（JSON 保留为回退；search_kb._load_vectors_npy 优先读 npy）
NPY_FILE = os.path.join(FED, "vectors", "kb_vectors.npy") if FED else None
NPY_META = os.path.join(FED, "vectors", "kb_vectors_meta.json") if FED else None
LOCK_PATH = os.path.join(FED, "vectors", ".build.lock") if FED else None  # 进程级互斥（防并发抢写）
MODEL_NAME = os.environ.get("KB_MODEL") or "BAAI/bge-base-zh-v1.5"  # KB_MODEL 环境覆盖
# 量化模型接入（与 search_kb 同判定）：量化产物在位→身份标签切换→缓存全量重建（防 fp32/int8 向量混搭）
QUANT_DIR = os.path.join(FED, "models", "bge-large-zh-v1.5-qint8-avx2") if FED else None
# v0.2 同步 v1.2 标签诚实化：量化产物=large 的 int8，标签如实记 large（原 MODEL_NAME+@qint8
# 在默认 base 时把 store 记成 base@qint8=误导，与包内 search_kb 的 large@qint8 标签不符→静默降级）。
# 就绪判据=量化文件完整存在（非仅目录存在）——防半成品误切标签（与 search_kb._QUANT_READY 同判据）。
_QUANT_READY = bool(QUANT_DIR) and os.path.isfile(os.path.join(QUANT_DIR, "onnx", "model_qint8_avx2.onnx"))
MODEL_EFFECTIVE = ("BAAI/bge-large-zh-v1.5@qint8-avx2" if _QUANT_READY else MODEL_NAME)

# ── 语义层解释器自路由 + 资产预检 ──
# 端用户 venv 建在脚本中心内（INSTALL.md Phase C2）；候选覆盖 .venv-st / .venv / scripts/.venv
_BP = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")  # 2026-10-19 Win反馈 min
_VENV_CANDIDATES = tuple(
    os.path.join(FED, *rel) for rel in (
        (".venv-st", *_BP),
        (".venv", *_BP),
        ("scripts", ".venv", *_BP),
    )
) if FED else ()
_HUB_CACHE = os.path.expanduser("~/.cache/huggingface/hub")
_ST_CACHE = os.path.expanduser("~/.cache/torch/sentence_transformers")
_MODEL_TAG = MODEL_NAME.split("/")[-1]


def _venv_python():
    for p in _VENV_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _model_cached():
    for d in (_HUB_CACHE, _ST_CACHE):
        if os.path.isdir(d) and any(_MODEL_TAG in x for x in os.listdir(d)):
            return True
    return bool(QUANT_DIR and os.path.isdir(QUANT_DIR))


def _semantic_ready():
    """语义层就绪判据：依赖 + 模型资产（缺任一 → 跳过构建·优雅降级不阻塞调用方）"""
    import importlib.util as _ilu
    if _ilu.find_spec("sentence_transformers") is None:
        return False, "未装 sentence_transformers"
    if not _model_cached():
        return False, f"模型缓存缺失（{_MODEL_TAG}）"
    return True, ""


def acquire_lock():
    """独占锁：任意两个 build 进程串行化，根除并发写竞争。
    取不到锁（另一 build 进行中）= 它会在写完时顺带刷新向量，本进程安全 no-op 退出，绝不并发写。"""
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    lf = open(LOCK_PATH, "w")
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lf
        except OSError:
            time.sleep(0.5)
    print("⚠️ 另一 build 进行中且 60s 超时，跳过（向量库由它更新）")
    sys.exit(0)


def release_lock(lf):
    try:
        fcntl.flock(lf, fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        lf.close()
    except Exception:
        pass


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def doc_text(d):
    """与 search_kb 索引对齐的编码文本"""
    return d["title"] + " " + d["summary"] + " " + d["text"]


def load_cache():
    if CACHE_FILE and os.path.isfile(CACHE_FILE):
        c = json.load(open(CACHE_FILE, encoding="utf-8"))
        if c.get("model") == MODEL_EFFECTIVE:
            return c
    return {"model": MODEL_EFFECTIVE, "generated": now_str(), "vectors": {}, "hashes": {}}


def build():
    if skb is None:
        print("⚠️ 未找到 search_kb.py（文档源单一真源）→ 跳过向量库构建")
        return 0
    docs = skb.build_docs()
    print(f"📚 文档源: {len(docs)} 条（知识池/立场卡/读书笔记/概念卡/Skill）")

    cache = load_cache()
    todo, keep = [], {}
    for p, d in docs.items():
        h = hashlib.md5(doc_text(d).encode("utf-8")).hexdigest()
        # v0.2 同步 PAT-080 根治：增量"已建"判定须同时验产物非空——只验 hash 会把 null 向量永久误跳过=静默烂数据
        if cache["hashes"].get(p) == h and cache["vectors"].get(p):
            keep[p] = cache["vectors"].get(p)  # 未变 → 复用
        else:
            todo.append((p, doc_text(d)))
    if keep:
        print(f"♻️  复用 {len(keep)} 条（未变）| 🔄 需重算 {len(todo)} 条")

    if not todo:
        # 无变化=不碰文件：改写会触发监听守护重入 → 死循环 + 并发写竞争
        print(f"✅ 无变化，缓存已是最新（未改写）: {CACHE_FILE}")
        # v0.2 同步 v1.3：npy 是 JSON 的派生镜像——JSON 已最新而 npy 缺失/过期时补写（不改 JSON）
        if not _npy_fresh(cache):
            n = _dump_npy(cache)
            print(f"🔁 已补写二进制向量库（npy 缺失/过期）: {n} 条 → {NPY_FILE}")
        else:
            print(f"✅ 二进制向量库已是最新: {NPY_FILE}")
        return 0

    from sentence_transformers import SentenceTransformer
    if _QUANT_READY:
        print(f"🧠 加载量化模型 {QUANT_DIR}（int8 onnx）...")
        model = SentenceTransformer(QUANT_DIR, backend="onnx",
                                    model_kwargs={"file_name": "onnx/model_qint8_avx2.onnx",
                                                  "provider": "CPUExecutionProvider"},
                                    local_files_only=True)
        # v0.2 同步 v1.1：强制 CPU EP——macOS CoreML EP 跑 int8 attention 节点必崩（node132 实锤），
        # 崩=向量库重建中断后静默降级；CPU int8 速度可接受。
    else:
        print(f"🧠 加载模型 {MODEL_NAME} ...")
        model = SentenceTransformer(MODEL_NAME, local_files_only=True)  # 纯本地，不走联网检查
    texts = [t for _, t in todo]
    print(f"⚙️  编码 {len(texts)} 条（首次较慢，之后增量极快）...")
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=32)

    new_hashes = dict(cache["hashes"])
    new_vectors = dict(keep)
    for (p, t), v in zip(todo, vecs):
        new_hashes[p] = hashlib.md5(t.encode("utf-8")).hexdigest()
        new_vectors[p] = [float(x) for x in v]
    # 清理已删除文档的残留向量
    live = set(docs.keys())
    for p in [k for k in new_vectors if k not in live]:
        new_vectors.pop(p, None)
        new_hashes.pop(p, None)

    cache.update({"generated": now_str(), "vectors": new_vectors, "hashes": new_hashes})
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    _atomic_dump(cache)
    _dump_npy(cache)  # v0.2 同步 v1.3：JSON 落盘后同步补二进制镜像
    print(f"✅ 向量库已更新: {len(new_vectors)} 条 | {CACHE_FILE}")
    return 0


def _npy_fresh(cache):
    """npy 是否与 JSON 同步：两件齐 + 标签同 + 条数同 + generated 同。任一不满足 → False（触发补写）。"""
    if not (NPY_FILE and NPY_META and os.path.isfile(NPY_FILE) and os.path.isfile(NPY_META)):
        return False
    try:
        meta = json.load(open(NPY_META, encoding="utf-8"))
    except Exception:
        return False
    return (meta.get("model") == cache.get("model")
            and meta.get("generated") == cache.get("generated")
            and len(meta.get("paths") or []) == len(cache.get("vectors") or {}))


def _dump_npy(cache):
    """写 float16 .npy + meta（paths 顺序=行号，单一真源=meta.paths）。原子写：.tmp + os.replace
    （半截文件被 search_kb 读到 = 静默降级 BM25）。numpy 缺失时跳过（JSON 仍是完整真源）。"""
    vecs = cache.get("vectors") or {}
    if not vecs:
        return 0
    try:
        import numpy as np
    except ImportError:
        print("⚠️ 无 numpy，跳过二进制向量库写入（JSON 真源完好·不影响降级）")
        return 0
    paths = list(vecs.keys())
    M = np.empty((len(paths), len(vecs[paths[0]])), dtype=np.float16)
    for i, p in enumerate(paths):
        M[i] = np.asarray(vecs[p], dtype=np.float16)
    meta = {"model": cache.get("model"), "generated": cache.get("generated"),
            "paths": paths, "shape": list(M.shape), "dtype": "float16",
            "note": "v0.2-enduser 二进制向量库·float16；search_kb._load_vectors_npy 读此件（JSON 为回退）"}
    os.makedirs(os.path.dirname(NPY_FILE), exist_ok=True)
    tmp = NPY_FILE + ".tmp.npy"
    with open(tmp, "wb") as f:
        np.save(f, M, allow_pickle=False)
    os.replace(tmp, NPY_FILE)
    tmpj = NPY_META + ".tmp"
    with open(tmpj, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    os.replace(tmpj, NPY_META)
    return M.shape[0]


def _atomic_dump(cache):
    """原子写：临时文件 + os.replace——⛔直接写目标文件=重建期间中间态损坏
    （写入中被 search_kb 读到半成品 JSON → 降级纯 BM25）。
    makedirs 内置：根除「vectors/ 目录不存在」崩溃路径。"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    os.replace(tmp, CACHE_FILE)


def status():
    if not CACHE_FILE:
        print("未安装态：本件需位于 [记忆共享中心]/脚本中心/知识联邦引擎/scripts/ 内运行")
        return 0
    if not os.path.isfile(CACHE_FILE):
        print("向量库不存在（装好语义增强后由落卡/索引重建自动构建·或手动跑 build_kb_vectors.py）")
        return 0
    c = json.load(open(CACHE_FILE, encoding="utf-8"))
    print(f"模型: {c['model']} | 生成: {c['generated']} | 向量数: {len(c['vectors'])}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        sys.exit(status())
    if not INSTALLED:
        print("❌ 未安装态：请先完成安装（本脚本需位于 [记忆共享中心]/脚本中心/知识联邦引擎/scripts/ 内运行）")
        sys.exit(1)
    # 语义层自路由：当前解释器缺依赖/资产 → 重投候选 venv。
    # 重投后仍不就绪（venv 内也没装）→ realpath 相等不再重投 → 显式跳过，⛔不阻塞调用方（regen check=False）。
    _ok, _why = _semantic_ready()
    if not _ok:
        _vp = _venv_python()
        if _vp and os.path.realpath(sys.executable) != os.path.realpath(_vp):
            os.execv(_vp, [_vp, os.path.abspath(__file__)] + sys.argv[1:])
        print(f"⚠️ 语义层不可用（{_why}）→ 跳过向量库构建（检索降级纯 BM25）")
        sys.exit(0)
    lf = acquire_lock()
    try:
        sys.exit(build())
    finally:
        release_lock(lf)
