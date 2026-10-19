#!/usr/bin/env python3
"""quantize_export.py — bge-large-zh-v1.5 官方 ONNX int8 动态量化导出（一次性·launchd 环境跑）。
产物：models/bge-large-zh-v1.5-qint8-avx2/onnx/model_qint8_avx2.onnx（+config/tokenizer）。
依据：sbert.net 官方文档 export_dynamic_quantized_onnx_model（免校准集）·用户授权 2026-09-09。
生产化（C38·2026-10-17）：支持 --quant-dir 参数化目标目录（semantic_upgrade.py 编排入口），缺省=引擎内传统路径（向后兼容）。"""
import os, sys, glob
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
from sentence_transformers import SentenceTransformer

FED = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUANT_DIR = os.path.join(FED, "models", "bge-large-zh-v1.5-qint8-avx2")
if "--quant-dir" in sys.argv:
    QUANT_DIR = os.path.abspath(sys.argv[sys.argv.index("--quant-dir") + 1])
FINAL = os.path.join(QUANT_DIR, "onnx", "model_qint8_avx2.onnx")
if os.path.exists(FINAL):
    print("量化模型已存在，跳过导出"); sys.exit(0)

print("1) 加载 fp32 模型（瞬时 2GB）...")
m = SentenceTransformer("BAAI/bge-large-zh-v1.5", local_files_only=True)
print("2) save_pretrained 到量化目录（config/tokenizer/modules）...")
m.save_pretrained(QUANT_DIR)
print("3) 用 st backend=onnx 导出 fp32 ONNX（st 自动落盘 QUANT_DIR/onnx/model.onnx——实测 23:29：加 save_pretrained 会 SameFileError，⛔勿加）...")
m2 = SentenceTransformer(QUANT_DIR, backend="onnx")
onnx_cands = glob.glob(os.path.join(QUANT_DIR, "**", "*.onnx"), recursive=True)
if not onnx_cands:
    print("   本目录未找到，扩大搜索 cache 目录...")
    for extra in [os.path.expanduser("~/.cache/torch/sentence_transformers"),
                  os.path.expanduser("~/.cache/huggingface/hub"),
                  "/tmp"]:
        onnx_cands += glob.glob(os.path.join(extra, "**", "*bge-large-zh*", "**", "*.onnx"), recursive=True)
# ⚠️ 过滤须排除「最终产物 FINAL」而非按 "qint8" 子串——完整路径含目录名 qint8-avx2，
# 按子串过滤会把所有文件误判掉（2026-09-09 23:20 实弹：文件在却报"未找到"）
fp32_onnx = [p for p in onnx_cands if p != FINAL]
print(f"   导出 onnx 文件: {[os.path.relpath(p, QUANT_DIR) for p in onnx_cands]}")
if not fp32_onnx:
    # v1.1（2026-10-06 实测·17:16 无垫片复现）：optimum 新版 backend=onnx 导出**成功但不自动落盘**——
    # 只在内存持有并打警告 "Saving the exported ONNX model is heavily recommended"，glob 必然空
    # ⇒ STAGE3 假性 FAIL（17:05 首败根因·非工具链墙）。修法：显式把内存中的 ORT 模型落盘到
    # onnx/ 子目录（save_pretrained 写 <dir>/model.onnx）。⚠️ 只在 glob 为空分支走——若 onnx 已在盘，
    # auto_model 是从该文件载入的，再 save 同目录 = SameFileError（23:29 实测教训）。
    _ort = getattr(m2[0], "auto_model", None)
    if _ort is not None:
        _onnx_dir = os.path.join(QUANT_DIR, "onnx")
        os.makedirs(_onnx_dir, exist_ok=True)
        print(f"   optimum 导出未自动落盘 → 显式保存到 {_onnx_dir}")
        _ort.save_pretrained(_onnx_dir)
        onnx_cands = glob.glob(os.path.join(QUANT_DIR, "**", "*.onnx"), recursive=True)
        fp32_onnx = [p for p in onnx_cands if p != FINAL]
        print(f"   导出 onnx 文件(显式落盘后): {[os.path.relpath(p, QUANT_DIR) for p in onnx_cands]}")
    if not fp32_onnx:
        print("❌ 未找到 fp32 onnx 产物"); sys.exit(2)
src = fp32_onnx[0]
print(f"4) onnxruntime 动态 int8 量化 → {os.path.relpath(FINAL, QUANT_DIR)}")
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic(model_input=src, model_output=FINAL, weight_type=QuantType.QInt8)
print("5) 清理 fp32 大文件（保留 qint8 + tokenizer/config）...")
for junk in ["model.safetensors", "onnx/model.onnx", "onnx/model_O1.onnx",
             "onnx/model_O2.onnx", "onnx/model_O3.onnx", "onnx/model_O4.onnx"]:
    fp = os.path.join(QUANT_DIR, junk)
    if os.path.exists(fp):
        os.remove(fp); print("   removed:", junk)
print("6) 冒烟测试（量化模型编码一句）...")
m3 = SentenceTransformer(QUANT_DIR, backend="onnx",
                         model_kwargs={"file_name": "onnx/model_qint8_avx2.onnx"},
                         local_files_only=True)
v = m3.encode(["测试句子：知识库检索引擎"], normalize_embeddings=True)[0]
print(f"   dim={len(v)} norm={sum(x*x for x in v)**0.5:.4f}")
print("EXPORT OK")
