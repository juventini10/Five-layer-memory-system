#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""semantic_upgrade.py — Phase C 语义升级工具链（C38·Large 压缩版/双模型路径）

五步链（INSTALL §数字分身完整版单装 Phase C2 的 Large/双模型分支入口）：
  ①母体检查/下载  ②依赖检查  ③本机 int8 动态量化  ④向量库重建  ⑤真机自验探针
产物驱动（与引擎既有机制咬合，⛔配置文件⛔env 持久化）：
  量化件落 models/bge-large-zh-v1.5-qint8-avx2/ 即生效（build_kb_vectors/search_kb
  均按「文件在=用 int8」自动切换）；任一步失败或回滚=删除量化目录，引擎自动回 base 态。
自验探针替代 CPU 指令集预检（C38 判据修正·卡面已注）：量化件导出后真跑一次推理，
通过才算装成——AVX2/ARM/异构平台一次覆盖，⛔CPUID 名相检测误判面。

用法：
  python3 semantic_upgrade.py --mode large|dual [--engine-root PATH] [--yes] [--dry-run]
  · large：只装压缩版（检索岗；碰撞扫描器不读量化件=停摆态，工具如实告知）
  · dual ：双模型（检索=Large 压缩版·碰撞=Base；两岗满配，推荐形态）
退出码：0=成功（含幂等已在位）；1=失败已回滚（引擎回 base 态，检索不断粮）；2=前置缺（显式指引）
"""
import argparse
import os
import shutil
import time
import subprocess
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ENGINE = os.path.dirname(HERE)          # scripts/ 的上一级=引擎根
QUANT_SUB = os.path.join("models", "bge-large-zh-v1.5-qint8-avx2")
MOTHER = "BAAI/bge-large-zh-v1.5"


def say(tag, msg):
    print("%s %s" % (tag, msg), flush=True)


def run(cmd, timeout=None):
    # F4（审查 2026-10-19）：FileNotFoundError/TimeoutExpired 不再裸 traceback——
    # 兜成 returncode≠0 的 CompletedProcess，让调用侧走显式 rc=2/回滚路径（契约 §退出码）。
    try:
        return subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
    except (OSError, subprocess.TimeoutExpired) as e:
        import subprocess as _s
        return _s.CompletedProcess(cmd, 1, "", "%s: %s" % (type(e).__name__, e))


def engine_paths(root):
    return {"root": root,
            "quant_dir": os.path.join(root, QUANT_SUB),
            "final": os.path.join(root, QUANT_SUB, "onnx", "model_qint8_avx2.onnx"),
            "scripts": os.path.join(root, "scripts")}


def pick_python(root):
    """解释器选择：优先引擎 venv（_engine_env 单一真源），⛔本工具不建 venv（建 venv 归 Phase C 选择装 Base 的那条腿）。"""
    sys.path.insert(0, os.path.join(root, "scripts"))
    try:
        import _engine_env as ee
        p = getattr(ee, "VENV_PY", None) or getattr(ee, "venv_python", lambda: None)()
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass
    cand = os.path.join(root, ".venv-st", "bin", "python")
    return cand if os.path.isfile(cand) else sys.executable


def ensure_venv(root, dry):
    """P26 路线交叉盲区根治（2026-10-19）：venv 创建职责原只挂 Base 腿，dual/large
    直接消费 venv=假指引（让用户在⛔不存在的 venv 里 pip）。本函数把建 venv+装依赖
    补进 dual/large 前置——复用 Base 腿已定稿设计（venv 建在引擎内），⛔不新发明。
    返回 venv python 路径；失败返回 None（调用侧按 前置缺 rc=2 处置）。"""
    venv_dir = os.path.join(root, "scripts", ".venv")
    # F4：Windows venv 实体=Scripts\python.exe，POSIX=bin/python——写死 bin/ 在 Win 恒判不存在+pip 必炸
    vpy = os.path.join(venv_dir, "Scripts", "python.exe") if os.name == "nt" \
        else os.path.join(venv_dir, "bin", "python")
    if os.path.isfile(vpy):
        return vpy
    say("②", "引擎 venv 不在位（P26 根治：dual/large 自建，不再让用户在⛔不存在的 venv 里 pip）→"
              "自动创建 venv + 安装工具链（onnxruntime/optimum-onnx/sentence-transformers·含 torch 级依赖·"
              "下载量数百MB级·全程可见可中断·F10 告知如实）")
    if dry:
        say("②", "[DRY] python -m venv %s && bin/pip install onnxruntime optimum-onnx sentence-transformers" % venv_dir)
        return vpy
    r = run([sys.executable, "-m", "venv", venv_dir], timeout=300)
    if r.returncode != 0:
        say("②", "❌ venv 创建失败（前置缺）：%s" % (r.stderr or "").strip()[-200:])
        return None
    # ⛔不手动钉 optimum 版本（09-09 实弹教训沿用）；装 base 腿同款依赖闭包
    r = run([vpy, "-m", "pip", "install", "--quiet", "onnxruntime", "optimum-onnx", "sentence-transformers"], timeout=1800)
    if r.returncode != 0:
        say("②", "❌ 工具链安装失败（前置缺·显式报错）：%s" % (r.stderr or "").strip()[-240:])
        return None
    say("②", "venv 自建完成：%s" % vpy)
    return vpy


def rollback(q):
    """资产回滚纪律（C38 事故修正 2026-10-17）：⛔ rmtree 删除——验证/回滚误判曾瞬时删掉
    生产量化件；改改名移走（原件保留可恢复/复查），failed 目录不挡幂等重跑。"""
    if os.path.isdir(q["quant_dir"]):
        dst = q["quant_dir"] + ".failed-" + time.strftime("%Y%m%d_%H%M%S")
        try:
            os.rename(q["quant_dir"], dst)
            print("   （回滚=移走保留 %s，⛔未删除，可人工找回）" % os.path.basename(dst))
        except OSError:
            pass


# ── ① 母体检查/下载 ──
def step1_mother(py, yes, dry):
    import glob as _g
    hub = os.path.expanduser("~/.cache/huggingface/hub/models--BAAI--bge-large-zh-v1.5")
    ok = bool(_g.glob(os.path.join(hub, "snapshots", "*", "config.json")))
    if ok:
        say("①", "large 母体缓存已在位，跳过下载")
        return True
    if dry:
        say("①", "[DRY] snapshot_download(%s)（约 1.2GB·下载前告知=本行）" % MOTHER)
        return True
    if not yes:
        say("①", "需下载 large 母体（约 1.2GB）。确认后加 --yes 重跑；网络受限可手动放置缓存后重跑。")
        return False
    r = run([py, "-c", "from huggingface_hub import snapshot_download; snapshot_download('%s')" % MOTHER],
            timeout=7200)
    if r.returncode != 0:
        say("①", "❌ 母体下载失败（显形，⛔不静默绕路）：%s" % (r.stderr or "").strip()[-240:])
        return False
    say("①", "母体下载完成")
    return True


# ── ② 量化依赖检查 ──
def step2_deps(py):
    r = run([py, "-c", "import onnxruntime, optimum, sentence_transformers"])
    if r.returncode != 0:
        say("②", "❌ 当前解释器 %s 缺 onnx/optimum 工具链。完整两步命令："
                  "`python3 -m venv <引擎根>/scripts/.venv && <引擎根>/scripts/.venv/bin/pip install onnxruntime optimum-onnx`"
                  "（⛔手动钉 optimum 版本——09-09 实弹：钉版本与 optimum-onnx 冲突致 pip 解析空转卡死）。"
                  "装毕重跑本工具；或直接重跑由 ② 自建腿自动安装（P26 已把建 venv+装依赖补进全自动）。" % py)
        return False
    say("②", "量化依赖在位")
    return True


# ── ③ 导出+动态量化（复用引擎内已验证工艺件，本工具只做编排与回滚） ──
def step3_quantize(py, q, dry):
    if os.path.isfile(q["final"]):
        say("③", "量化件已在位（幂等跳过）：%s" % os.path.relpath(q["final"], q["root"]))
        return True
    if dry:
        say("③", "[DRY] quantize_export.py → 落 %s" % os.path.relpath(q["final"], q["root"]))
        return True
    src = os.path.join(q["scripts"], "quantize_export.py")
    if not os.path.isfile(src):
        say("③", "❌ 引擎内缺 quantize_export.py（导出工艺件）。缺件=不猜实现，显式止步（引擎保持 base 态）。")
        return False
    r = run([py, src, "--quant-dir", q["quant_dir"]], timeout=7200)
    if r.returncode != 0:
        say("③", "❌ 量化导出失败 → 清半成品，引擎回 base 态：%s" % (r.stderr or "").strip()[-240:])
        rollback(q)
        return False
    if not os.path.isfile(q["final"]):
        say("③", "❌ 导出件宣称成功但产物缺失（声明≠验证二分测试）→ 清半成品：%s" % q["final"])
        rollback(q)
        return False
    say("③", "量化件产出：%s" % os.path.relpath(q["final"], q["root"]))
    return True


# ── ④ 向量库全量重建（引擎按产物自动切 int8；失败=回滚+回 base 重建） ──
def step4_rebuild(py, q, dry):
    if dry:
        say("④", "[DRY] build_kb_vectors.py 全量重建（标签=int8 形态·768→1024 维旧向量作废）")
        return True
    r = run([py, os.path.join(q["scripts"], "build_kb_vectors.py")], timeout=14400)
    if r.returncode != 0:
        say("④", "❌ 重建失败 → 自动回滚（删量化目录回 base 态并重建 base 向量库，检索不断粮）："
                 "%s" % (r.stderr or "").strip()[-200:])
        rollback(q)
        run([py, os.path.join(q["scripts"], "build_kb_vectors.py")], timeout=14400)
        return False
    say("④", "向量库已按新形态重建（JSON+npy 双写）")
    return True


# ── ⑤ 真机自验探针（推理实证替代 CPU 预检） ──
def step5_probe(py, q, dry):
    if dry:
        say("⑤", "[DRY] onnxruntime 加载量化件跑一次编码；向量库标签核对（期望 qint8 在标签）")
        return True
    code = ("# -*- coding: utf-8 -*-\n"
            "import onnxruntime as o, numpy as np\n"
            "s = o.InferenceSession(r\'%s\', providers=[\'CPUExecutionProvider\'])\n"
            "feeds = {}\n"
            "for x in s.get_inputs():\n"
            "    if x.type == \'tensor(int64)\':\n"
            "        feeds[x.name] = np.zeros((1, 8), dtype=\'int64\')\n"
            "s.run(None, feeds)\n"
            "print(\'ORT_OK\')\n" % q["final"])
    import tempfile
    tf = tempfile.NamedTemporaryFile("w", suffix=".probe.py", delete=False, encoding="utf-8")
    tf.write(code); tf.close()
    try:
        r = run([py, tf.name], timeout=600)
    finally:
        os.unlink(tf.name)
    if "ORT_OK" not in (r.stdout or ""):
        say("⑤", "❌ 量化件真机推理未过（本机运行环境不支持该形态，无 AVX2 机型即在此拦下）"
                 "→ 回滚 base 态：%s" % (r.stderr or "").strip()[-160:])
        rollback(q)
        return False
    st = run([py, os.path.join(q["scripts"], "build_kb_vectors.py"), "--status"], timeout=180)
    out = (st.stdout or "")
    say("⑤", "自验通过：真机推理 OK；向量库标签核对：%s" %
        ("含 qint8 ✓" if "qint8" in out else "⚠️ 未见 qint8 标签（若为幂等旧库请重跑步骤④）"))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["large", "dual"])
    ap.add_argument("--engine-root", default=os.environ.get("KB_ENGINE_ROOT") or DEFAULT_ENGINE)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--dry-run", action="store_true", dest="dry")
    a = ap.parse_args()
    root = os.path.abspath(os.path.expanduser(a.engine_root))
    if not os.path.isdir(os.path.join(root, "scripts")):
        say("前置", "❌ 引擎根无效（缺 scripts/）：%s——请先完成 Phase B（引擎最小件落位）" % root)
        sys.exit(2)
    q = engine_paths(root)
    # P26：venv 缺 → 自建（成功即用 venv 解释器）；自建失败=前置缺 → rc=2（与 1=失败已回滚 区分）
    _vp = ensure_venv(root, a.dry)
    if _vp is None:
        say("结论", "❌ 前置缺：引擎 venv 无法自建（网络/磁盘/pip 源问题）。修好后重跑本工具（幂等）。")
        sys.exit(2)
    py = _vp if os.path.isfile(_vp) else pick_python(root)
    say("模式", "%s（%s）·引擎根 %s·解释器 %s%s" % (
        a.mode, "检索+碰撞两岗满配" if a.mode == "dual" else "仅检索岗（碰撞扫描将停摆=设计内）",
        root, py, "·[DRY-RUN]" if a.dry else ""))
    steps = [lambda: step1_mother(py, a.yes, a.dry),
             lambda: step2_deps(py),
             lambda: step3_quantize(py, q, a.dry),
             lambda: step4_rebuild(py, q, a.dry),
             lambda: step5_probe(py, q, a.dry)]
    for s in steps:
        if not s():
            say("结论", "❌ 升级未完成（已回滚或止步前置）。引擎保持/回到 base 态，检索不断粮；"
                        "原因见上方带 ❌ 的步骤行，修好后可直接重跑本工具（幂等）。")
            sys.exit(1)
    say("结论", "✅ 语义升级完成：检索岗=Large 压缩版（量化精度损失实测≈0·2026-10-16 v6 结案）。"
                + ("双模型两岗均已满配。" if a.mode == "dual" else "如需碰撞岗，重跑 --mode dual。"))


if __name__ == "__main__":
    main()
