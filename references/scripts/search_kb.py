#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/search_kb.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""
search_kb.py v0.3.18 — 知识沉淀自动检索（v0.3.18·2026-10-22 Win反馈单V2 N-1：目录名形态归一兜底 _norm_layout_walk·候选链全miss后按 normalize(空格→-) 逐段扫描+漂移显形，根治历史空格形态实盘检索源静默不可达·配套实现 --status 真分支（原死接口被当查询词吃·E-1 状态头机检取）·负例夹具N1五测+E1三测·回滚点=记忆琥珀/fbkV2-fix-20261022/）（v0.3.17·2026-10-17 模块C库容治理：C-2 非卡入库排除表(_NONCARD_EXCLUDE)+缓存schema4·C-5 成长箱纯元块结构过滤(_is_meta_block·标题黑名单弃用改物理判据)·gate0 71%/0.638 前后对照零退化·回滚点=记忆琥珀/模块C-白名单-bak-20261017/）（v0.3.16·2026-10-16 门3换参 K_RRF 60→30·NDCG+3.5pp零Recall代价·标题保底floor机理·真尺n=21验证·回滚点=记忆琥珀search_kb_v0.3.15_K60_改前·母卡§八门3节）（v0.3.15·2026-10-13 技能卡专属分支·任务卡T3 判据预注册见工单§8）（v0.3.14·2026-10-07 CLI实跑落trail·原则17机械锚补全）（前值 v0.3.13·2026-10-05 布局+引擎根双自适应·P2 G4 检索面修复）（第二刀·BM25式+路由加权+ bge 向量 RRF 融合；v0.3 实体直通+单一真源）
职责: 任务描述 → ①意图路由（5类型查路由表）→ ②检索（路由加权×3 + 词面命中×IDF + 向量余弦）
      → ③Top-K（路径+命中理由+摘要）。输出带纠错标记说明（⛔ 这条没用 → 回写路由表/关键词）。
      数据源: 知识池卡(05-知识池) + 读书笔记(01-读书笔记) + 立场卡(AI学习库) + 概念卡(08-概念层) + Skill。
      ⛔只读不写任何卡片；向量库 kb_vectors.json 由 build_kb_vectors.py 构建（缺失时自动降级 v0.1 纯 BM25）。
      v0.3: search() 核心单一真源（main/eval 共用）+ 任务内实体直通（文档侧自动生长·专名硬信号 > 向量软信号）
      + RRF bm25_rank 修复（插入序→得分序）+ 桶第一优先级源加权补齐（设计-实现差）。
      v0.3.1: 查询词修复——桶全量关键词替代命中子集（借势/主角类近义书卡零命中根因，皮叔 2026-08-07 质疑触发）。
      v0.3.2: 实体池补英文 Skill 目录名（shall-we-talk 等整体入池+空格变体+大小写不敏感），皮叔 2026-08-07 介绍 shall-we-talk 触发。
v0.3.14: CLI 实跑落 trail（2026-10-07·皮叔令「调查清楚后按最优解根治」·原则17 机械锚补全）——
        main() CLI 路径经 kb_query_trail.append_trail(source="cli") 落账，AI 自跑引用从此可 grep
        复核（时间戳+query+命中行三样齐）。显式推翻 kb_query_trail 2026-09-07「⛔不改 search_kb.py」
        观测约束：当时观测面=注入流（serve/fallback）；原则17 立后 CLI 实跑=一等观测流量，写账点
        收敛为引擎出口单点——kb_serve/kb_inject_prompt 均 import search() 模块内调用不进 main，
        各自按 serve/fallback 记账如旧，零双记账。失败静默不阻断检索（对齐 _log_degrade 契约）。
v0.3.3: 内存预检 guard（2026-09-03「沙箱网络受限」误判根治）——加载 bge 语义模型峰值需 ~2GB 内存，内存不足时显式降级纯 BM25（打印原因）而非被 OS 静默 SIGKILL(137)，杜绝"引擎打不开=网络受限"误判。
v0.3.4: #1 可观测性（2026-09-03·落地）——向量降级事件写 logs/kb_degrade.jsonl，打破静默 stderr，可量化退化频率。
v0.3.6: execv→子进程委托+降级回退（2026-09-09 童灵根治②·SIGTERM 137 第四次复现定性）——模型缓存恢复后每次调用都 execv 重投
        venv torch（数百文件打开），配额耗尽会话连 --help 都被 SIGKILL(137)且无降级路径。改为轻量父进程派 venv 子进程跑语义层
        （--help/--status/--build-chunk/--drill 及 KB_NO_HEAVY=1 豁免），子进程死/超时→父进程存活降级 BM25+写 degrade 日志。
v0.3.5: 根治「模型缺失→网络探测挂死」（2026-09-09 童灵根治·SIGTERM 137 三次复现）——①HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE
        在 st import 前设置（offline 环境探测 huggingface.co 实测烧 4 分 21 秒）②_model_available 增模型缓存预检
        （缺失→毫秒级显式降级纯 BM25+大声报告+写 kb_degrade.jsonl），检索永不断粮。
v0.3.9: 降级面根治（2026-09-10 童灵·皮叔令「按符合愿景的第一性原理最优解根治」）——
        ①**判据补全**：_model_available 增环境维度预检（_env_missing_deps 探测 numpy/sentence_transformers）。
          原判据只查【资产】（模型缓存/内存），缺依赖的解释器被判"可用"→放行→执行到 import numpy 才炸
          →静默降级（vector_off_import_error 5 例实证·末次 10:29:58）。**判据必须覆盖操作前置条件全集**。
        ②**换身判据修正**：CLI 重投从"仅 sentence_transformers 缺失"改为"numpy 或 st 任一缺失"。
        ③**账本单源**：_DEGRADE_LOG 收为顶部单一常量（原重投块/钩子写 scripts/logs/、_log_degrade 写引擎根
          → 两本账分叉，只看一份=判断残缺）；历史 2 条已合并，scripts/logs/ 留迁移路牌。
        ④新增 vector_off_env_missing 事件类（环境类降级可一眼归因，不再混入 model_missing）。
用法: python3 search_kb.py "任务描述"
      例: python3 search_kb.py "写视频文案（介绍每日伙伴）"
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys, os
import importlib.util

# ── 端用户路径参数化（脱敏通用版·2026-09-30）：MC 自推导，⛔零作者硬编码路径 ──
def _find_mc():
    """记忆中心根解析（2026-10-04 根治静默回落）。
    旧实现的两个洞：①只认"目录名==脚本中心"，从 开发工具/ 跑的副本必然找不到；
    ②找不到就回落 `expanduser("~")`=家目录根，于是 `join(_MC,"脚本中心","知识联邦引擎")`
    在家根 mkdir 出幽灵树（实测 18:14 造出 [记忆共享中心]/脚本中心/知识联邦引擎/cache/doc_corpus.json）。
    本仓自己的规范明文：⛔键缺不得静默回落（runtime_paths 文档·恒真判据制造机）。"""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        if os.path.basename(d) == "脚本中心":
            return os.path.dirname(d)
        if os.path.isdir(os.path.join(d, "脚本中心")):      # 认"含脚本中心的目录"，不认自己叫什么
            return d
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    try:                                                     # 次选：安装器写的本机真源
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from runtime_paths import rp
        return os.path.dirname(os.path.dirname(rp("devtools")))
    except Exception:
        pass
    sys.stderr.write("[search_kb] 未定位到记忆中心根，已回落 ~/个人AI档案（重装或改过配置请检查）\n")
    return os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
_MC = _find_mc()
def _pick_engine_dir(_mc):
    """引擎根解析（2026-10-06 LobsterAI 端根治）：以「含 route_table.json」为功能判据。

    病根：原 `_ENGINE_DIR` 固定 `join(_MC,"脚本中心","知识联邦引擎")`。作者机该目录是
    **幽灵树残根**（仅 cache/scripts，无 route_table.json、无 .venv-st）
    ⇒ ① `_VENV_PY` 指向不存在的 venv；② 重投块 `os.path.exists(_VENV_PY)` = False
    ⇒ **语义层永挂**（只剩 BM25·检索质量下降·且只打印一行降级不易归因）。
    判据必须**在重投块之前**生效——原 fallback 块在 L214+ 才改写 `_ENGINE_DIR`，
    来得太晚（重投块已在 L96 跳过）。

    ⛔ 不用「目录存在即选」（会把幽灵树当合法根选中，等于把病灶固化进机制）；
    ✅ 以 `route_table.json` 为功能判据（原 L218 判据，此处前移复用）。
    """
    for _c in (
        os.path.join(_mc, "脚本中心", "知识联邦引擎"),                       # 端用户态（装包后落点）
        os.path.join(_mc, "知识联邦引擎"),                                   # 作者态钦定落点（2026-10-11 定论"一个家"·内部台账遗留2第1件顶层位置顶）
        os.path.join(_mc, "开发工具", "知识联邦引擎"),                       # 旧位·④批(2026-10-15)已整树退役——本候选永不命中；留二周观察窗后随阶段5清零（⛔当场删=行为改动混进注释批·哲学01 §二·二十三之二）
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "知识联邦引擎"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "知识联邦引擎"),
    ):
        if os.path.isfile(os.path.join(_c, "route_table.json")):
            return os.path.normpath(_c)
    return os.path.join(_mc, "脚本中心", "知识联邦引擎")                     # 兜底：保持旧行为
_ENGINE_DIR = _pick_engine_dir(_MC)
def _venv_py(eng_dir, sub=".venv-st"):
    # 2026-10-19 Win反馈 A-1：Windows venv 实体=Scripts/python.exe，POSIX=bin/python，
    #   写死 bin/python 在 Win 恒判 exists=False→重投分支永不进→语义层静默降级 BM25。
    _rel = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")
    return os.path.join(eng_dir, sub, *_rel)
# ── 语义层自路由（2026-08-12）── 当前解释器无 sentence_transformers → 重投专用 venv，
# 从根上杜绝「任意 python 跑本会静默降级 BM25」的回归（Intel Mac 无 torch≥2.6 wheel，
# 语义层必须用 .venv-st：py3.12+torch2.2.2+st3.4.1+transformers4.48.3，模型已本地缓存）。
_VENV_PY = _venv_py(_ENGINE_DIR)
# v0.3.5 预检前置（2026-09-09 童灵根治·SIGTERM 137 三次复现）：模型缓存缺失时连 venv 重投都不做——
# 重投 venv-st 只为 torch/st 语义层；纯 BM25 用当前轻量解释器即可（足迹 ~100MB vs 重投+torch ~800MB）。
# 内存压力下（16GB 机 free~138MB 实测）重投+torch import 即可被 macOS SIGKILL(137)，时活时死。
_HUB_CACHE_ = os.path.expanduser("~/.cache/huggingface/hub")
_ST_CACHE_ = os.path.expanduser("~/.cache/torch/sentence_transformers")
# 2026-09-10 修复：模型名硬编码 bge-large → 随 KB_MODEL/默认模型派生（切 base 后缓存预检恒 False=全端静默降级 BM25 事故根因）
_MODEL_TAG = (os.environ.get("KB_MODEL") or "BAAI/bge-base-zh-v1.5").split("/")[-1]
_MODEL_CACHED_ = (
    any(_MODEL_TAG in d for d in (os.listdir(_HUB_CACHE_) if os.path.isdir(_HUB_CACHE_) else []))
    or any(_MODEL_TAG in d for d in (os.listdir(_ST_CACHE_) if os.path.isdir(_ST_CACHE_) else []))
)

# ── 降级账本单一常量（2026-09-10 根治）：原重投块/钩子各写 scripts/logs/，
#    而 _log_degrade() 写引擎根 logs/ → 降级事件分叉成两本账，只看一份=判断残缺。──
_DEGRADE_LOG = os.path.join(_ENGINE_DIR, "logs", "kb_degrade.jsonl")


def _env_missing_deps():
    """返回当前解释器缺失的语义层依赖列表（numpy / sentence_transformers）。

    2026-09-10 根治·③号洞根因：原换身与预检判据**只查 sentence_transformers 单项**，
    缺 numpy 的解释器被判"无需换身且模型可用"→ 预检放行 → 执行到 `import numpy` 才炸
    → 静默降级纯 BM25（vector_off_import_error 5 例，末次 09-10 10:29:58）。
    判据必须覆盖语义层实际 import 的全集，否则判据与操作前置条件不同域。"""
    import importlib.util as _ilu
    miss = [m for m in ("numpy", "sentence_transformers") if _ilu.find_spec(m) is None]
    # v0.3.13（2026-10-07 Qoder CN 根治·皮叔令"彻底根治"）：量化上线后语义层走 ONNX 后端——
    #   st 在而 optimum 缺时旧判据称"无需换身"→ 主进程直载 qint8 必报 "Optimum required"
    #   →静默降级 BM25（2026-10-07 两入口实测复现·vector_off_load_error）。判据须随对象演化。
    #   量化就绪路径就地内联：模块级 _QUANT_FINAL 定义在本函数调用点（重投预检块）之后，不可引用。
    _qf = os.path.join(_ENGINE_DIR, "models", "bge-large-zh-v1.5-qint8-avx2",
                       "onnx", "model_qint8_avx2.onnx")
    if os.path.isfile(_qf):
        miss += [m for m in ("optimum", "onnxruntime") if _ilu.find_spec(m) is None]
    return miss


# ⚠️ 2026-09-10 修复：整块重投逻辑仅 CLI 主程序触发——import 场景（kb_serve 常驻/构建脚本）
# 不得触发 spawn/退出副作用（否则 daemon import 即自杀）。daemon 请直接用 .venv-st/bin/python 启动。
if __name__ == "__main__" and _env_missing_deps():
    _FAST_ARGS = {"--help", "-h", "--status", "--build-chunk", "--drill"}
    _already_venv = os.path.realpath(sys.executable) == os.path.realpath(_VENV_PY)
    if (_MODEL_CACHED_ and os.path.exists(_VENV_PY) and not _already_venv
            and os.environ.get("KB_NO_HEAVY") != "1"
            and not (set(sys.argv[1:]) & _FAST_ARGS)):
        # v0.3.6 童灵根治②（2026-09-09）：execv→子进程委托+降级回退。
        # 根因：execv 换身后父进程不存在，配额耗尽会话中 venv torch import（数百文件打开）
        # 被 SIGKILL(137)——连 --help 都死，无任何降级路径（本日三次复现实锤）。
        # 改为：轻量父进程派 venv 子进程跑语义层；子进程死(137)/超时 → 父进程存活，显式降级 BM25。
        import subprocess as _sp
        import subprocess as _sp
        # v0.3.6 子进程委托+双层降级（2026-09-09 童灵根治②）：
        #   层1 spawn 前内存闸门——模型加载峰值 ~2GB，free<2.5GB 时 macOS 内存压力会整树
        #   SIGKILL(137)，父进程降级代码没机会跑（本日实测 free~884MB 三次复现）；检查点
        #   必须在 spawn 之前（v0.3.3 内部预检在 torch import 之后=死亡之后·位置性失效）。
        #   层2 子进程委托——spawn 后子进程死(137)/超时→父进程存活降级 BM25。
        #   语义层在内存健康时照常工作（行为不变），紧张时毫秒级 BM25 兜底（永不断粮）。
        _spawn_heavy = True
        import subprocess as _sp
        try:
            _vm = _sp.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
            _pgsize = int(_sp.run(["sysctl", "-n", "hw.pagesize"], capture_output=True, text=True, timeout=5).stdout.strip() or 4096)
            _pg = {}
            for _line in _vm.splitlines():
                if _line.startswith("Pages ") and ":" in _line:
                    _k, _v = _line.split(":", 1)
                    try:
                        _pg[_k.strip()] = int(_v.strip().rstrip(".").replace(",", ""))
                    except ValueError:
                        pass
            # macOS 把 free 页即时挪作文件缓存——单看 Pages free 几乎恒低（v0.3.6a 指标缺陷）；
            # 可用 = free + inactive + speculative（系统可立即回收的三类页）
            _avail_b = (_pg.get("Pages free", 0) + _pg.get("Pages inactive", 0)
                        + _pg.get("Pages speculative", 0)) * _pgsize
            if _avail_b < 1_200_000_000:  # v0.3.7 随 bge-base 切换下调（模型 2GB→~600MB）
                _spawn_heavy = False
                print(f"⚠️ 可用内存 {_avail_b // 1024 // 1024}MB < 2500MB，跳过语义层（纯 BM25 兜底）", file=sys.stderr)
                try:
                    import json as _json
                    from datetime import datetime as _dt
                    _dl = _DEGRADE_LOG
                    os.makedirs(os.path.dirname(_dl), exist_ok=True)
                    with open(_dl, "a", encoding="utf-8") as _f:
                        _f.write(_json.dumps({"ts": _dt.now().isoformat(timespec="seconds"),
                                              "event": "heavy_skipped_low_memory",
                                              "detail": f"avail={_avail_b // 1024 // 1024}MB"}) + "\n")
                except Exception:
                    pass
        except Exception:
            pass  # 内存测量失败→照常尝试子进程（保守回退原行为）
        if _spawn_heavy:
            try:
                _r = _sp.run([_VENV_PY, os.path.abspath(__file__)] + sys.argv[1:],
                             timeout=180, start_new_session=True)
                if _r.returncode == 0:
                    raise SystemExit(0)  # 语义层成功·结果已由子进程输出
                _degrade = f"heavy_child_exit_{_r.returncode}"
            except _sp.TimeoutExpired:
                _degrade = "heavy_child_timeout_180s"
            except Exception as _e:
                _degrade = f"heavy_child_error_{type(_e).__name__}"
            print(f"⚠️ 语义层子进程未完成（{_degrade}）→ 降级纯 BM25（检索永不断粮）", file=sys.stderr)
            try:
                import json as _json
                from datetime import datetime as _dt
                _dl = _DEGRADE_LOG
                os.makedirs(os.path.dirname(_dl), exist_ok=True)
                with open(_dl, "a", encoding="utf-8") as _f:
                    _f.write(_json.dumps({"ts": _dt.now().isoformat(timespec="seconds"),
                                          "event": "heavy_child_fallback", "detail": _degrade}) + "\n")
            except Exception:
                pass
    # 模型缺失或子进程失败：当前轻量解释器纯 BM25（rank_mixed 内 _model_available 显式降级+大声报告+写 degrade 日志）
# v0.3.5 根治「模型缺失→网络探测挂死」(2026-09-09 童灵根治·SIGTERM 137 三次复现)：
# 离线环境变量必须在 sentence_transformers/transformers import 前设置——杜绝 hub 网络探测。
# 实测根因：模型缓存丢失时 local_files_only=True 仍会探测 huggingface.co（st 加载链路），
# 每次连接超时重试累计烧 4 分 21 秒才抛 OSError——期间调用方超时 SIGKILL(137)，表象=引擎卡死。
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import re, glob, math, json, subprocess, itertools
from datetime import datetime

HOME = _MC  # 兼容下游引用
POOL_DIR = os.path.join(_MC, "知识库", "知识池")
NOTES_DIR = os.path.join(_MC, "知识库", "读书笔记")
CONCEPT_DIR = os.path.join(_MC, "知识库", "概念卡")
AILIB_DIR = os.path.join(_MC, "知识库", "AI学习库")
GROWTH_DIR = os.path.join(_MC, "成长箱", "learnings")
BLUEPRINT_INDEX_DIR = os.path.join(_MC, "知识库", "蓝图索引卡")  # 2026-09-08 数字分身增强计划阶段1.3：蓝图索引卡检索源接入
# ── 布局自适应（2026-10-05 P2 处方①·G4 命门）──
# 原状：_find_mc() 正确解析出记忆中心，但下方各检索源目录名只用端用户态布局
#       （知识库/知识池 等），作者机上这些目录不存在 ⇒ 候选恒 0 且 rc=0 静默。
# 现状：两种布局都探（端用户态优先，缺失则回落作者态真目录）；两边都不存在
#       ⇒ ⛔ 不静默，记入 _LAYOUT_DIAG 并在 0 候选时显形。
_LAYOUT_ALT = {
    "POOL_DIR": ("[日记仓库]", "2-知识库", "05-知识池"),
    "NOTES_DIR": ("[日记仓库]", "2-知识库", "01-读书笔记"),
    "CONCEPT_DIR": ("[日记仓库]", "2-知识库", "08-概念层"),
    "AILIB_DIR": ("[日记仓库]", "2-知识库", "09-AI学习库"),  # 2026-10-12 C''波次2迁入vault(卡内部台账·旧位软链为72h缓冲)
    "GROWTH_DIR": ("[记忆共享中心]", "成长箱", "learnings"),
    "BLUEPRINT_INDEX_DIR": ("[日记仓库]", "2-知识库", "10-蓝图索引卡"),
    # 2026-10-06 布局第三形态落位（键20261006_171708后·皮叔令"未闭环的尝试去做"）：
    #   原 "[日记仓库]" 为未解析占位符（join 后 = ~/[日记仓库]/… 字面路径·永不存在）
    #   → POOL/NOTES/CONCEPT/BLUEPRINT 四检索源自布局机制上线起恒不可达（每跑必⚠️）。
    #   实际仓根 = ~/[日记仓库]/2-知识库/（四源 ls 实证 2026-10-06）——
    #   Obsidian vault 即"日记仓库"的实际名，占位符以实名落位。
}
# 2026-10-13 B方案·功能判据替代非空判据（K007三源闭环裁决·童灵D3执行）
# 迁移后旧路径残留文件（如触发台账）会导致"非空优先"误判遮蔽新路径
# 对已迁移目录用"特征文件存在"替代"目录非空"作为在位判据
# 与下方引擎根"含route_table.json"功能判据同构（第264行先例）
_LAYOUT_FEATURE = {
    "AILIB_DIR": "立场卡#S",  # AI学习库特征文件=立场卡#S*.md（其他目录未迁移保持非空判据）
}


def _kb_root_override():
    """知识库根（⛔ 不假设 Obsidian）：优先 runtime_paths 的 kb_root 键（安装器默认指 MC/知识库，
    Obsidian 用户可改指自己的 vault）；缺或不可读则回落既有解析链（作者态/安装期占位符填充）。"""
    try:
        from runtime_paths import rp
        _r = rp("kb_root", optional=True)
        if _r and os.path.isdir(os.path.expanduser(_r)):
            return os.path.expanduser(_r)
    except Exception:
        pass
    return None

_KB_ROOT = _kb_root_override()
_LAYOUT_DIAG = []


def _norm_layout_walk(roots, tail):
    """目录名形态归一扫描（2026-10-22 Win反馈 N-1 根治）。
    病灶：包内硬写目录名与端实盘形态混用（空格/连字符）——历史包面口径曾用
      「10 蓝图索引卡」空格形态，老装机用户实盘带旧名，连字符 join 恒 miss
      ⇒ 检索源静默不可达（修复前每跑必⚠️）。路径是事实不是配置，静态检查判不出，
      故候选链全 miss 后加结构兜底：逐段按 normalize(空格→-) 比对。
    判据：每段优先精确名命中，无精确再收归一命中；返回首个全段存在的路径。
    返回 (path, drifted)：drifted=True=命中叶子段名与硬写形态不同（须显形）。"""
    for _root in roots:
        _p, _drift_leaf = _root, None
        for _seg in tail:
            if not os.path.isdir(_p):
                _p = None
                break
            _exact = os.path.join(_p, _seg)
            if os.path.isdir(_exact):
                _p = _exact
                continue
            _k = _seg.replace(" ", "-")
            _hit = None
            try:
                for _d in sorted(os.listdir(_p)):
                    if _d.replace(" ", "-") == _k and os.path.isdir(os.path.join(_p, _d)):
                        _hit, _drift_leaf = os.path.join(_p, _d), _d
                        break
            except OSError:
                _hit = None
            if not _hit:
                _p = None
                break
            _p = _hit
        if _p:
            return _p, (_drift_leaf is not None)
    return None, False


for _nm, _alt in _LAYOUT_ALT.items():
    _cur = globals().get(_nm)
    if not _cur:
        continue
    _feat = _LAYOUT_FEATURE.get(_nm)
    if _feat:
        _alive = os.path.isdir(_cur) and any(_feat in f for f in os.listdir(_cur))
    else:
        _alive = os.path.isdir(_cur) and os.listdir(_cur)
    if _alive:
        continue                                     # 在位（功能判据/非空判据），不动
    # 2026-10-06 判据加固：空目录壳（迁移残留/makedirs 误建）此前被当"在位"⇒ 检索读空库静默0命中
    #   且不告警——isdir 存在性判据与"有内容"错位（PAT-043/053 家族·实证=立场卡+概念卡整源消失4天）
    # 2026-10-19 Win反馈 A-4：_alt[0] 是安装期占位符 token（如 "[日记仓库]"），
    #   Win 装机 _fill 未供该 token 时 join 出 ~/[日记仓库]/… 字面路径·永不存在→每跑必⚠️。
    #   改候选根链（token 位由真实根替换），全不中仍如实告警；Mac 命中同一根不受影响。
    _resolved = None
    _roots = []
    if _KB_ROOT:
        _roots.append(_KB_ROOT)
    _roots += (os.path.join(os.path.expanduser("~"), "[日记仓库]"),
               os.path.join(os.path.expanduser("~"), "[记忆共享中心]"),
               os.path.join(os.path.expanduser("~"), "记忆共享中心"),
               _MC, os.path.expanduser("~"))
    for _root in _roots:
        _c = os.path.join(_root, *_alt[1:])
        if os.path.isdir(_c):
            _resolved = _c
            break
    _drifted = False
    if not _resolved:
        # N-1 兜底（2026-10-22）：候选链全 miss ≠ 目录不存在——可能只是形态混名；
        #   归一扫描命中则采用+显形，仍不中才报「两种布局均缺失」。
        _resolved, _drifted = _norm_layout_walk(_roots, _alt[1:])
    if _resolved:
        globals()[_nm] = _resolved
        _LAYOUT_DIAG.append(("%s 目录名形态漂移命中(%s)" % (_nm, os.path.basename(_resolved))) if _drifted else ("%s 回落作者态" % _nm))
    else:
        _LAYOUT_DIAG.append("⚠️%s 两种布局均缺失（检索源不可达）" % _nm)
if _LAYOUT_DIAG:
    print("🧭 布局自适应: " + " ｜ ".join(_LAYOUT_DIAG), file=sys.stderr)
# ── 引擎根自适应（2026-10-05 P2 处方②·归因后实施·steps/p2_7_diag.py 实测）──
# 病灶：_ENGINE_DIR 原固定 join(_MC,"脚本中心","知识联邦引擎")。作者机该目录是幽灵树残根
#       （仅 cache/scripts，缺 route_table.json 与 vectors/kb_vectors.json）⇒ 向量路整条断，
#       同 query 候选 3；真根在 开发工具/知识联邦引擎（三样俱在）⇒ 候选 10。
# 判据：以「目录内含 route_table.json」为功能判据 —— ⛔ 不用"目录存在即选"，
#       否则幽灵树会被当成合法根选中，等于把病灶固化进机制。
# 兼容：端用户态（脚本中心/知识联邦引擎 带 route_table）命中第一条，行为不变。
_ENGINE_CANDIDATES = [
    os.path.join(_MC, "脚本中心", "知识联邦引擎"),        # 端用户态（装包后引擎落点）
    os.path.join(_MC, "开发工具", "知识联邦引擎"),        # 作者态旧根·④批已退役（同上一条·观察窗后清零）
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "知识联邦引擎"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "知识联邦引擎"),
]
_picked = None
for _c in _ENGINE_CANDIDATES:
    if os.path.isfile(os.path.join(_c, "route_table.json")):
        _picked = os.path.normpath(_c)
        break
if _picked and _picked != os.path.normpath(_ENGINE_DIR):
    _LAYOUT_DIAG.append("引擎根 %s→%s（原指处缺 route_table）" % (_ENGINE_DIR.replace(os.path.expanduser("~"), "~"), _picked.replace(os.path.expanduser("~"), "~")))
    _ENGINE_DIR = _picked
    _VENV_PY = _venv_py(_ENGINE_DIR)
    _DEGRADE_LOG = os.path.join(_ENGINE_DIR, "logs", "kb_degrade.jsonl")
    _ROUTE_TABLE_JSON = os.path.join(_ENGINE_DIR, "route_table.json")
    _DOC_CACHE = os.path.join(_ENGINE_DIR, "cache", "doc_corpus.json")
    VEC_FILE = os.path.join(_ENGINE_DIR, "vectors", "kb_vectors.json")
    QUANT_DIR = os.path.join(_ENGINE_DIR, "models", "bge-large-zh-v1.5-qint8-avx2")
    # （本块在模块作域执行，上述赋值直接生效；不用 eval/globals 反射——静态扇 HIGH 项已消除）
if not any(os.path.isfile(os.path.join(c, "route_table.json")) for c in _ENGINE_CANDIDATES):
    _LAYOUT_DIAG.append("⚠️ 引擎根四种候选均无 route_table.json（路由表不可达·已降级内置表）")

K = 10  # Top-K（B* 2026-08-17：抬升以容纳钦定书硬保底位，避免 k=5 截断保底卡）
CHAR_BUDGET = 2000  # 检索输出字符预算（2026-08-14 外部借鉴 TencentDB 预算截断：累计锚点字符，超预算截断低分条目；可用 env KB_CHAR_BUDGET 覆盖）
ROUTE_BOOST = 3.0  # 路由表第一优先级知识源加权
ENTITY_BOOST = 1.5  # 任务对象实体素材加权（低于路由×3，保持方法论主位）

# 实体提取停用词（通用虚词/代词，专名提取用·保守清单宁缺毋滥）
_ENTITY_STOP = {"我们", "一个", "进行", "以及", "这个", "自己", "不是", "什么", "怎么", "为什么", "可以", "需要", "就是", "如果", "没有", "这样", "应该", "可能", "都会", "通过", "已经", "但是", "因为", "所以", "虽然", "然后", "现在", "时候", "里面", "一些", "很多", "非常", "比较", "觉得", "知道", "可以", "这样", "这些"}

# ── v2 向量混合检索（第二刀）──
VEC_FILE = os.path.join(_ENGINE_DIR, "vectors", "kb_vectors.json")
MODEL_NAME = os.environ.get("KB_MODEL") or "BAAI/bge-base-zh-v1.5"  # 默认已切 base（2026-09-10 eval 22/24 通过）；回滚=KB_MODEL=BAAI/bge-large-zh-v1.5  # KB_MODEL 环境覆盖（2026-09-10 童灵·切模型用）；与概念层同模型默认（你拍板 2026-07-26）
# v0.3.6b int8 量化接入（2026-09-09 童灵·官方 export_dynamic_quantized_onnx_model 产物）：
# 量化模型存在则优先加载（内存足迹 2GB→~600MB）；向量库身份标签随之切换——
# ⛔量化/浮点向量不可混搭（查询与语料必须同版本编码），故标签区分=缓存自动失效重建。
QUANT_DIR = os.path.join(_ENGINE_DIR, "models", "bge-large-zh-v1.5-qint8-avx2")
# 就绪判据=量化文件完整存在（非目录存在）——防半成品/失败残留目录误切标签导致
# 基线评测静默降级 BM25（2026-09-09 童灵自检预演逮住：导出先于基线→基线被切 @qint8→向量不符→假对比）
_QUANT_FINAL = os.path.join(QUANT_DIR, "onnx", "model_qint8_avx2.onnx")
_QUANT_READY = os.path.isfile(_QUANT_FINAL)
# v0.3.11 标签诚实化（2026-10-06 你裁决留量化版·标签债修正·2026-10-07 根治回灌主源）：
# 量化产物=large 的 int8，标签须如实记 large——原 MODEL_NAME+@qint8 在默认 base 时把 store
# 记成 base@qint8（误导，实际向量是 large-qint8 1024 维）。量化目录硬编码即 large 身份，标签从之。
MODEL_EFFECTIVE = ("BAAI/bge-large-zh-v1.5@qint8-avx2" if _QUANT_READY else MODEL_NAME)
    # ↑2026-10-16 定案注(v6):量化缺失时 MODEL_EFFECTIVE=base 与库标签 large@qint8 不符→校验拒载→诚实降级纯 BM25。检索体系无线上替补(你裁决):base 仅=用户机正岗/库回滚锚;量化税≈0 已实证(fp16 对照未赢,母卡§八+检索设计哲学 v1.26)。勿将此分支描述为「base 兜底检索」。
_model = None



# ── v0.3.12 向量库二进制化（2026-10-06 你令·治"六脉神剑"检索不稳；2026-10-07 根治合并入主源）──
# 病灶（profile 实测·非推断）：search 7.80s 中 _load_vectors 占 6.25s（79.9%）——
#   向量库 kb_vectors.json = 70.6MB 明文，json.load 单次 6.3~7.9s；DOCS_TTL=120s 到点后
#   每次静默期首查必重载 → 实测静默 150s 后第1发 8.34s（>钩子 8s 预算=必被掐断静默放行）。
# 修法：同数据换介质=float16 .npy（6.3MB·压缩 11.2×·np.load 0.034s·加速 76.8×），
#   ⛔不动量化模型、不动召回算法、不动向量本身（float16 归一化向量余弦误差 <1e-3·远小于分档差）。
#   JSON 保留为回退 + npy 缺失自动回落。
VEC_NPY = os.path.join(_ENGINE_DIR, "vectors", "kb_vectors.npy")
VEC_NPY_META = os.path.join(_ENGINE_DIR, "vectors", "kb_vectors_meta.json")


class _NpyVectorStore:
    """npy 支撑的向量库视图——对外接口与 dict 完全一致（__iter__/__contains__/__getitem__），
    故 rank_mixed 及其下游零改动。__getitem__ 返 float32 行视图（量化模型为 fp32 算的，
    升 float32 再点积保证与原 JSON 路径数值一致）。"""

    __slots__ = ("paths", "index", "M")

    def __init__(self, paths, M):
        self.paths = paths
        self.index = {p: i for i, p in enumerate(paths)}
        self.M = M

    def __contains__(self, p):
        return p in self.index

    def __iter__(self):
        return iter(self.paths)

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, p):
        return self.M[self.index[p]]


def _load_vectors_npy():
    """二进制向量库加载：文件缺失/标签不符/形状不符/解析失败 → None（调用方回落 JSON）。"""
    if not (os.path.isfile(VEC_NPY) and os.path.isfile(VEC_NPY_META)):
        return None
    try:
        import numpy as np
        meta = json.load(open(VEC_NPY_META, encoding="utf-8"))
        if meta.get("model") != MODEL_EFFECTIVE:
            return None
        M = np.load(VEC_NPY, mmap_mode=None)
        if list(M.shape) != list(meta.get("shape") or []) or len(meta.get("paths") or []) != M.shape[0]:
            return None  # meta 与 npy 不同步（写入中途被读）→ 回落
        if M.dtype != np.float16:
            return None
        return _NpyVectorStore(meta["paths"], M.astype(np.float32, copy=False))
    except Exception:
        return None
def _load_vectors():
    """向量库加载：npy 优先 → JSON 回退。不存在/模型不符/解析失败 → None（降级纯 BM25）"""
    npy = _load_vectors_npy()
    if npy is not None:
        return {"model": MODEL_EFFECTIVE, "vectors": npy, "source": "npy"}
    if not os.path.isfile(VEC_FILE):
        return None
    try:
        c = json.load(open(VEC_FILE, encoding="utf-8"))
        if c.get("model") != MODEL_EFFECTIVE:
            return None
        c["source"] = "json"
        return c
    except Exception:
        return None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        if _QUANT_READY:
            _model = SentenceTransformer(
                QUANT_DIR, backend="onnx",
                model_kwargs={"file_name": "onnx/model_qint8_avx2.onnx",
                              "provider": "CPUExecutionProvider"},
            # v0.3.11（2026-10-06·2026-10-07 回灌主源）：强制 CPU EP——macOS 默认 CoreML EP
            # 在本机 Intel 工具链上 attention 节点必崩（node132 墙·STAGE4 实弹复现），崩=整体降级 BM25。
                local_files_only=True)  # int8 量化版（官方 export_dynamic_quantized_onnx_model 产物）
        else:
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)  # 纯本地，不走 huggingface 联网检查
    return _model


# ── v0.3.3 内存预检（2026-09-03 根治：低内存时静默 SIGKILL(137) 被误判为"沙箱网络受限"）──
# 根因：sentence_transformers 全家桶 + bge 模型加载峰值约需 ~2GB 内存；在内存受限环境（如仅数十 MB 空闲）
# import 阶段即被 OS 杀掉（137 无输出），表现为"引擎打不开"。加预检，内存不足时显式降级纯 BM25 而非静默崩溃。
_MODEL_MIN_MEM = 1_200_000_000  # 2026-09-10 随 bge-base 切换下调（base fp32 ~600MB + torch 常驻；原 2.4GB 为 large 口径）


def _free_memory_bytes():
    """Best-effort 可用内存估算（macOS vm_stat / Linux /proc/meminfo）。无法判断时返回 None。"""
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
            pages = {}
            for line in out.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    v = v.strip().rstrip(".").replace(",", "").strip()
                    try:
                        pages[k.strip()] = int(v)
                    except ValueError:
                        pass
            pg = 4096
            # free + speculative + inactive 视为可回收上限（保守估计可用内存）
            avail = pages.get("Pages free", 0) + pages.get("Pages speculative", 0) + pages.get("Pages inactive", 0)
            return avail * pg
        elif sys.platform.startswith("linux"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) * 1024
    except Exception:
        return None
    return None


def _model_available():
    """语义层可用性预检；不可用时返回 (False, reason) 让调用方显式降级 BM25。
    无法判断内存时返回 (True, "") 保持原行为（照常尝试加载）。"""
    # ① 环境维度预检（2026-09-10 根治·③号洞）：依赖不可 import 时资产再全也跑不起来。
    #    原判据**只查资产**（模型缓存/内存）→ 预检放行 → 执行到 `import numpy` 才炸 → 静默降级。
    #    补此判据后同类问题在**预检阶段即拦截**，并归因到 vector_off_env_missing。
    _miss = _env_missing_deps()
    if _miss:
        return False, f"当前解释器缺依赖 {'/'.join(_miss)}（语义层须在 .venv-st 内跑）"
    # ② 资产维度预检（v0.3.5 缓存预检·2026-09-09 童灵根治）：模型文件缺失时毫秒级显式降级，
    # 不再进入加载链路（此前即使 except Exception 兜底也要先烧掉网络探测/加载耗时）。
    hub_cache = os.path.expanduser("~/.cache/huggingface/hub")
    st_cache = os.path.expanduser("~/.cache/torch/sentence_transformers")
    _tag = MODEL_NAME.split("/")[-1]  # 2026-09-10 修复：随实际模型派生（原硬编码 bge-large 致切模型后恒判缺失）
    hub_hit = any(_tag in d for d in (os.listdir(hub_cache) if os.path.isdir(hub_cache) else []))
    st_hit = any(_tag.replace("/", "_") in d for d in (os.listdir(st_cache) if os.path.isdir(st_cache) else []))
    if not (hub_hit or st_hit):
        return False, f"模型缓存缺失（{MODEL_NAME} 未见于 HF/torch 缓存·须重装模型或走 BM25）"
    free = _free_memory_bytes()
    if free is None:
        return True, ""
    if free < _MODEL_MIN_MEM:
        return False, f"可用内存约 {free // 1024 // 1024}MB，低于模型所需 ~{_MODEL_MIN_MEM // 1024 // 1024}MB"
    return True, ""


# ── #1 可观测性（2026-09-03·落地）：向量降级事件写计数日志，打破静默 ──
# （_DEGRADE_LOG 常量已于文件顶部定义·2026-09-10 统一收口；此处不再重复定义）

def _log_degrade(event, detail=""):
    """向量降级/钩子回退事件追加到 logs/kb_degrade.jsonl（一行一事件）。
    失败静默吞掉——绝不因日志写入阻断检索主流程。"""
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(_DEGRADE_LOG, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"ts": ts, "event": event, "detail": detail},
                                 ensure_ascii=False) + "\n")
    except Exception:
        pass


VEC_TOPN = 30  # B''：向量全库召回并入候选的条数（v1.4·知识库改造计划 §6.1.2）
# B'' 调权：纯向量召回（BM25 因源门禁/闭词表漏掉、跨源）文档只拿 1 个 RRF 项，
# 而 BM25 命中项可再叠向量项拿双份 → 被压在后面（humanizer 排 ~20）。给单 term 乘补偿系数，
# 让强语义匹配（vec_rank 小）浮到前列，又不淹没双命中项。
# 2026-08-13 A/B 校准（L1 定性→双档）：
#   3.0 单档 = humanizer 排第 6（首屏可达）但知识池卡霸屏 Top1-5 压路由源（4 评估样本立场卡 0 出现）；
#   1.5 单档 = 路由源回位（eval 21/23=91%）但跨源 Skill 召回回归（humanizer 掉出 Top10、写视频文案-这个Skill 掉出 Top5）；
#   双档（v2·按源量分档） = 知识池（量 567 卡·霸屏唯一源头）1.5 低档 + 其余源（Skill/概念卡/立场卡/读书笔记）3.0 高档。
#   ⛔ 不能用 allowed 分档：评估桶 allowed=立场卡，知识池卡对评估桶是跨源→吃高档→霸屏重现（第一版实测）。
# 🔴 价值锚点声明（2026-08-13 第一性原理根治）：真正要保的是「跨源 Skill 语义召回」能力（B'' 核心价值），
#    正式回归锚点=eval_set 内你自建 Skill 样本（写视频文案→daily-buddy、口播稿→scriyore/lidan-writing-framework、构建Skill→skill-forge）。
#    humanizer 仅为 B''（2026-08-11）历史失败样本留下的代理测试用例，不是价值主体——
#    它恰好被点名只因当年是翻车实证；其 anti-slop 能力你已内联进 scriyore（2026-07-28 系统日志实证），本 Skill 无独立使用价值。
VEC_ONLY_BOOST = 1.5          # 知识池纯向量项（防量大的内容库霸屏压路由源）
VEC_ONLY_BOOST_CROSS = 3.0    # 其余源纯向量项（保跨源 Skill/概念卡语义召回）


def rank_mixed(scores, task, entity_docs=None, docs=None, allowed=None):
    """v3 混合检索（B''·2026-08-11）：BM25 候选 ∪ 向量全库 Top-N，真双路 RRF。

    v2 硬缺陷（A/B 实测暴露）：向量只在 BM25 候选内取（`if p in cand`），而候选已被
    「源过滤 + BM25 封闭词表 + s<=0 剔除」砍到全库的 26~32%——向量沦为候选内重排器，
    不是召回器。三查询与「向量全库 Top-5」交集 0/5、0/5、1/5：
    「写作时怎么去掉AI味」召不回 humanizer Skill；「内容运营冷启动」召不回 运营之光-卡片11。

    v3 修正（验收回炉·2026-08-11）：向量召回池 = **全库语义召回，不受意图路由 allowed
    源白名单限制**。首版曾保留源过滤（`docs[p]['src'] in allowed`），验收证明错——
    「AI味」路由写作桶（源={知识池,读书笔记,立场卡}），humanizer/book-writer 是 Skill
    源被门禁挡死，跨源语义召回这一 B'' 核心价值失效。意图路由只约束 BM25 词面路径；
    向量路拆掉源门禁，BM25 缺席者按标准 RRF `1/(K+r)` 并入候选（无额外罚分）。
    实体×3 硬信号、优雅降级、K_RRF=60 全部保留。docs=None 退回 v2 候选内重排。"""
    # v0.3.5 顺序修正（2026-09-09 童灵根治）：先预检模型可用性，再决定是否加载向量库——
    # 原顺序先 load 63MB JSON（解析后 ~500MB RAM），模型明明不可用也白扛 500MB，
    # 内存压力边境线上被 macOS/沙箱非确定性 SIGKILL(137)（时活时死·插桩实测复现）。
    # 模型缺失/内存不足 → 纯 BM25 毫秒级返回，内存足迹 ~100MB，永不断粮。
    ok, why = _model_available()
    if not ok:
        print(f"⚠️ 向量检索降级：{why}（纯 BM25）", file=sys.stderr)
        _ev = ("vector_off_low_memory" if "内存" in why
               else "vector_off_env_missing" if "缺依赖" in why
               else "vector_off_model_missing")
        _log_degrade(_ev, why)
        return scores
    vec_data = _load_vectors()
    if not vec_data:
        if os.path.isfile(VEC_FILE):
            print("⚠️ 向量检索降级：向量库存在但模型不符或解析失败（纯 BM25）", file=sys.stderr)
            _log_degrade("vector_off_model_mismatch")
        return scores
    try:
        import numpy as np
        qv = _get_model().encode([task], normalize_embeddings=True)[0]
    except ImportError as e:
        print(f"⚠️ 向量检索降级：依赖缺失 {e}（纯 BM25；pip install sentence_transformers numpy）", file=sys.stderr)
        _log_degrade("vector_off_import_error", str(e))
        return scores
    except Exception as e:
        print(f"⚠️ 向量检索降级：模型加载/编码失败 {e}（纯 BM25）", file=sys.stderr)
        _log_degrade("vector_off_load_error", str(e))
        return scores
    V = vec_data["vectors"]
    if docs is None:  # 向后兼容：旧调用（无 docs）退回 v2 候选内重排
        pool = [p for _, p, _, _ in scores if p in V]
    else:  # B'' 修正：向量召回池=全库语义召回，不受意图路由 allowed 源白名单限制
        # （原 allowed 过滤会让 Skill/概念卡 等跨源文档仍被挡，等于没拆源门禁——
        #  "写作时怎么去掉AI味" 的 humanizer(Skill) 因此永远召不回。意图路由只约束 BM25 词面路径。）
        # 2026-09-07 你令根治泛命中：成长箱 docs 仅在当前意图 allowed 含"成长箱"（[5]成长箱管理桶）
        # 时参与向量召回——工程/评估任务不再被"状态"等泛词语义拉到成长箱错误记录（BM25 路径 line 528 已堵）。
        pool = [p for p in V if p in docs and (docs[p]["src"] != "成长箱" or "成长箱" in (allowed or set()))]
    if not pool:
        return scores
    # v0.3.12 npy 快路径（2026-10-06；2026-10-07 根治合并）：按行号取矩阵子集（一次 fancy-index），
    #   避免逐行 Python 取值再 stack；⛔数值口径与 JSON 路径完全一致（同为 float32 · 同为 M[rows] @ qv）。
    if isinstance(V, _NpyVectorStore):
        rows = np.fromiter((V.index[p] for p in pool), dtype=np.int64, count=len(pool))
        sims = V.M[rows] @ np.asarray(qv)
        order = np.argsort(-sims)[:VEC_TOPN if docs is not None else len(pool)]
        vec_rank = {pool[i]: r + 1 for r, i in enumerate(order)}
    else:
        # PAT-080 根治（2026-10-06·你令彻底根治）：JSON 回退路剔除 None/维度畸变条目——
        #   np.array([V[p]...]) 遇 kb_vectors.json 里 null 或维度≠查询向量的坏条目即抛
        #   inhomogeneous shape ⇒ 整个检索崩（义务⑧立场卡检索的地基不能死）。
        #   防御层：坏条目跳过并 stderr 显形（⛔不静默），全畸则向量路降级纯 BM25（v0.1 先例）不抛。
        _qv = np.asarray(qv)
        _qdim = _qv.shape[-1]
        _good = [p for p in pool if isinstance(V.get(p), (list, tuple)) and len(V[p]) == _qdim]
        _bad = len(pool) - len(_good)
        if _bad:
            sys.stderr.write("[search_kb] ⚠️ 剔除畸变向量条目 %d 个（None 或维度≠%d）·向量路降级不崩\n" % (_bad, _qdim))
        if not _good:
            return scores
        sims = np.array([V[p] for p in _good]) @ _qv
        order = np.argsort(-sims)[:VEC_TOPN if docs is not None else len(_good)]
        vec_rank = {_good[i]: r + 1 for r, i in enumerate(order)}

    ordered = sorted(scores, key=lambda x: -x[0])  # BM25 得分降序 → 排名（插入序≠得分序，2026-08-07 修复）
    bm25_rank = {p: i + 1 for i, (_, p, _, _) in enumerate(ordered)}
    K_RRF = 30.0

    merged, seen = [], set()
    for s, p, d, matched in scores:
        s2 = 1.0 / (K_RRF + bm25_rank[p])
        if entity_docs and p in entity_docs:
            s2 *= 3.0  # 实体精确命中：BM25 分量×3（无论有无向量——专名硬信号优先于语义软信号）
        elif p in vec_rank:
            s2 += 1.0 / (K_RRF + vec_rank[p])
        merged.append((s2, p, d, matched))
        seen.add(p)
    for p, r in vec_rank.items():  # v3 新增：向量召回、BM25 未命中的文档并入候选（标准 RRF + 纯向量补偿）
        if p in seen or docs is None:
            continue
        # 2026-08-13 A/B 校准 v2：纯向量项按源量分档——知识池（量 567 卡）低档防霸屏压路由源；
        # 其余源高档保跨源语义召回（humanizer/book-writer/daily-buddy 类）。
        # ⛔ 判据不能是 allowed：跨桶样本（写作+工程）allowed 含 Skill，Skill 被误判路由源内降档；
        #    评估桶 allowed=立场卡，知识池卡被误判跨源升档霸屏（第一版双档实测双败）。
        src = docs[p].get("src", "")
        bst = VEC_ONLY_BOOST if src == "知识池" else VEC_ONLY_BOOST_CROSS
        s2 = bst / (K_RRF + r)  # 补偿：纯向量项只拿 1 份 RRF，乘系数追平双命中项
        if entity_docs and p in entity_docs:
            s2 *= 3.0
        merged.append((s2, p, docs[p], [f"⚡语义#{r}"]))
    TRUST_MULT = {"human-reviewed": 1.2, "machine-confirmed": 1.1, "unverified": 1.0}
    # 信任加权（原则 8·2026-08-13）：乘数直接乘入 score 值而非只改排序 key——
    # search() 在 rank_mixed 返回后还会按原始分数二次排序，只改 key 会被覆盖（实测 S358 未提升）。
    # 存量卡无 verified → unverified ×1.0 → 零影响（eval 23/23 保持）。
    merged = [(s * TRUST_MULT.get(d.get("trust", "unverified"), 1.0), p, d, matched)
              for s, p, d, matched in merged]
    # 标题保底通道（2026-10-11·「实现真正该命中的那一个」·对齐 pool_books 保底位范式·K007 D3 产物）：
    # 任务词面与卡标题精确包含 → 保底补偿分——抽词三源（词面∩桶/文档键词/实体）全空时词面腿
    # 空转，精确名卡被相关语义卡淹没（实证：K005 自搜 top-10 无本尊）。泛化机制非打地鼠。
    task_norm = re.sub(r"\s+", "", task)
    if task_norm:
        _tg = []
        for s, p, d, matched in merged:
            tnorm = re.sub(r"\s+", "", d.get("title", ""))
            if tnorm and (task_norm in tnorm or tnorm in task_norm):
                s = max(s, ROUTE_BOOST / (K_RRF + 1) + 0.001)
                matched = matched + ["🎯标题精确"]
            _tg.append((s, p, d, matched))
        merged = _tg
    merged.sort(key=lambda x: -x[0])
    return merged

# ── 知识路由表（v3·2026-08-07 实测重定·意图路由优先于向量） ──
ROUTE_TABLE = [
    {
        "name": "写作/文案",
        "keywords": ["写作", "文案", "视频", "文章", "口播", "脚本模型", "标题", "爆款", "借势", "主角", "故事", "IP", "抖音", "小红书", "图文", "配音", "PPT", "公众号", "种草", "碎碎念", "定位", "护城河", "人设", "共鸣", "自嘲", "吐槽", "红海", "活人感", "素材", "内容"],
        "sources": ["POOL", "NOTES", "AILIB"],
        "pool_books": ["短视频爆款文案", "打造个人IP", "借势", "主角", "故事", "学会写作", "南方周末写作课", "运营之光", "文章卡片", "洞见卡"],
    },
    {
        "name": "评估/决策",
        "keywords": ["评估", "决策", "判断", "靠谱", "方案", "选择", "值不值", "验证", "分析", "风险", "对比"],
        "sources": ["AILIB", "CONCEPT"],
    },
    {
        "name": "系统建设/工程",
        "keywords": ["Skill", "skill", "脚本", "架构", "开发", "工程", "钩子", "hook", "版本", "规范", "构建", "自动化", "流水线", "触发逻辑", "系统日志", "记忆系统", "检索引擎", "备份", "构建", "优化", "设计哲学", "蓝图", "为什么这么设计"],
        "sources": ["CONCEPT", "AILIB", "POOL", "SKILL", "BLUEPRINT"],  # 2026-09-08 蓝图索引卡加入系统建设桶
    },
    {
        "name": "方法/学习",
        "keywords": ["学习", "方法", "记忆", "笔记", "概念", "掌握", "练习", "理解", "读书", "认知", "刻意"],
        "sources": ["NOTES", "CONCEPT", "POOL"],
    },
    {
        "name": "健康/复盘",
        "keywords": ["复盘", "睡眠", "精力", "健康", "日记", "周报", "月报", "疲劳", "早起", "情绪", "冥想", "总结"],
        "sources": ["AILIB", "NOTES", "POOL", "SKILL"],
    },
]

# ── P0 配置外置（2026-08-13·检索自进化方案 v0.2）──
# ROUTE_TABLE 可由外部 route_table.json 覆盖：只外置"读法"（源码默认 + 外部覆盖），⛔不改检索逻辑。
# 数据一致时行为零变化（回归 eval 23/23 可验证）；覆盖失败 → 用源码默认，绝不崩。
_ROUTE_TABLE_JSON = os.path.join(_ENGINE_DIR, "route_table.json")
if os.path.isfile(_ROUTE_TABLE_JSON):
    try:
        _ext_rt = json.load(open(_ROUTE_TABLE_JSON, encoding="utf-8"))
        if (isinstance(_ext_rt, list) and _ext_rt
                and all(isinstance(b, dict) and b.get("name") and isinstance(b.get("keywords"), list)
                        and isinstance(b.get("sources"), list) for b in _ext_rt)):
            ROUTE_TABLE = _ext_rt
        else:
            print("⚠️ 路由表外置覆盖被拒（结构校验不过）：用源码默认", file=sys.stderr)
    except Exception as _e:
        print(f"⚠️ 路由表外置覆盖失败（用源码默认）：{_e}", file=sys.stderr)


def parse_fm(text):
    """frontmatter 解析：仅取 --- 到 ---，支持单值/列表。"""
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    cur = None
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            cur = k.strip()
            v = v.strip().strip('"')
            fm[cur] = [v] if v else []
        elif cur and line.strip().startswith("- "):
            fm[cur].append(line.strip()[2:].strip())
    return fm


def trust_of(fm):
    """信任层级（OKF 借鉴·2026-08-13 原则 8）：verified 含 human: 前缀 → human-reviewed；
    verified 存在但非 human → machine-confirmed；无 verified → unverified。
    存量卡无 verified 字段 → unverified → 检索零影响（eval 23/23 保持）。"""
    v = fm.get("verified", [])
    if any("human:" in str(x) for x in v):
        return "human-reviewed"
    if v:
        return "machine-confirmed"
    return "unverified"


# ── B' 承重字段抽取（v1.3·知识库改造计划 §6.1）──
# 立场卡真实 bold 头带限定符（如 **立场（结论）** / **自测题×3**），用前缀匹配兼容
LOAD_BEARING = ["主要矛盾", "立场", "依据链", "让步合法条件", "顶住红线",
                "推翻了我哪个旧认知", "反方最强论证", "自测题"]

def extract_section(body, key):
    """按 schema 承重字段从正文抽段（直读原文，不盲截）。前缀匹配兼容 **key(限定)** 写法。"""
    import re as _re
    m = _re.search(r"\*\*" + _re.escape(key) + r"[^*]*\*\*[：: ]*(.*?)(?=\n\*\*|\Z)", body, _re.S)
    return m.group(1).strip() if m else ""

def brief(s, n=80):
    """摘要首句化（B''）：去 md 标记 → 取首句 → 截断。用于 366/366 立场卡无 summary 字段的回退。"""
    if not s:
        return ""
    import re as _re
    s = _re.sub(r"[*`>#\[\]|]", "", s).replace("\n", " ")
    s = _re.sub(r"\s+", " ", s).strip()
    return _re.split(r"[。！？；]", s)[0][:n]


def extract_section_ln(body, key):
    """行级溯源（借 kb-pilot #2）：抽承重字段并记录源文件正文行号，供 '依据链' 引用 file#Lxx"""
    import re as _re
    m = _re.search(r"\*\*" + _re.escape(key) + r"[^*]*\*\*[：: ]*(.*?)(?=\n\*\*|\Z)", body, _re.S)
    if not m:
        return "", None
    ln = body[:m.start()].count("\n") + 1   # 相对正文行号（已去 frontmatter）
    return m.group(1).strip(), ln




# ── v0.3.15 技能卡专属分支（任务卡 2026-10-13 T3·判据先写后改·预注册见工单 §8）──
# 根因：技能卡（技能卡#K*）此前混走立场卡分支——LOAD_BEARING 是立场卡 bold 字段表，
#   技能卡承重节是 `## 标题` 结构（核心方法/适用边界/反例），提取全空 → 正文仅前 300 字入索（≈3%）。
# 判据纪律：模板里不许出现机制不读的字段（card-schema §八）；本分支只消费真实存在的节。
LOAD_K_CARD = ["核心方法", "适用边界", "反例"]

def _extract_md_section(body, key):
    """技能卡标题级抽段：`## key…` 起（含标题行——标题词本身是检索面）到下一 ## 或文末。"""
    m = re.search(r"^##\s*" + re.escape(key) + r"[^\n]*\n(.*?)(?=\n##\s|\Z)", body, re.M | re.S)
    if not m:
        return ""
    head = m.group(0)[:m.group(0).index("\n")].lstrip("#").strip()
    return head + " " + m.group(1).strip()

def skill_card_view(raw, fm):
    """技能卡检索 text 构造（harness_t3 H1 测量对象·⛔返回值形态勿改）：
    cat + summary（fm 优先·缺则核心方法首句回退）+ 承重节（含节名） + 正文前 300。"""
    body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)
    segs = [x for x in (_extract_md_section(body, k) for k in LOAD_K_CARD) if x]
    cat = " ".join(fm.get("topic", []) + fm.get("type", []) + fm.get("领域分诊", []))
    sm = fm.get("summary", [""])
    sm = sm[0] if isinstance(sm, list) else sm
    sm = sm or (brief(segs[0]) if segs else "")
    return " ".join([x for x in (cat, sm) if x]) + " " + " ".join(segs) + " " + body[:300]

# ── v0.3.5 索引磁盘缓存（2026-09-09 童灵根治·SIGKILL 137 实锤归因）──
# 根因：WB 沙箱对进程文件打开次数设配额，实测 build_docs 逐个 open ~2400 源文件，
# 读到 ~650 个即被 SIGKILL(137)（monkeypatch open 打点抓到死亡现场·毛选目录段）。
# 根治：索引落盘缓存——命中时只 open 1 个缓存文件（秒级），指纹对账用 os.stat（不 open 文件体），
# 指纹失配才全量重建。愿景三问：强化闭环（检索永不断粮）/减少人工（零维护）/越用越好用（重复检索提速）。
_DOC_CACHE = os.path.join(_ENGINE_DIR, "cache", "doc_corpus.json")

_CHUNK = 200  # 每分片文件数（沙箱文件监视配额实测 ~400-650 漂移·200 留双倍安全余量）

def _glob_patterns():
    """与 _build_docs_full 完全一致的 7 源 glob（单一真源·分片与指纹共用）。"""
    return [
        os.path.join(POOL_DIR, "*", "*.md"),
        os.path.join(NOTES_DIR, "*.md"),
        os.path.join(CONCEPT_DIR, "*.md"),
        os.path.join(AILIB_DIR, "*.md"),
        os.path.join(GROWTH_DIR, "*.md"),
        os.path.join(BLUEPRINT_INDEX_DIR, "*.md"),
        os.path.join(_MC, "技能配置", "*", "SKILL.md"),
    ]

def _corpus_paths():
    return sorted(set(itertools.chain.from_iterable(glob.glob(pt) for pt in _glob_patterns())))

# ── 模块C·库容治理 C-2 入库排除表（2026-10-17·专项卡 2026-10-17-模块C库容治理 §附 A级清单）──
# 病灶（母卡新病⑥）：台账/评测/规范/bak 等"工作文件"被当卡入索引，占候选位稀释精度（合并台账.md 霸题4第1 实锤）。
# 纪律：⛔物理文件不动，只动入库判定（归属与位置解耦律 S199）；逐条显式排除（不做模式猜测——防误伤真卡）。
# 台账型源（成长箱 learnings/）B级存疑件本期不排：该源设计定位=台账可检，排出误伤"该中的中"（卡面存证备你复核）。
_NONCARD_EXCLUDE = {
    "AILIB_DIR": {"合并台账.md", "引用台账.md", "技能卡候选台账.md", "碰撞卡多视角评测.md",
                  "触发台账.md", "跨类型碰撞候选-蓝图索引卡↔立场卡.md"},
    "BLUEPRINT_INDEX_DIR": {"00-蓝图索引卡格式规范.md", "蓝图索引卡-.bak-20260923-acregistry.md"},
    "GROWTH_DIR": {"批量归属复核表-2026-09-26.md"},  # C-5 终判（2026-10-17 广授权）：一次性复核交付物=历史档案，非可检经验
}
def _is_noncard(p_):
    _b = os.path.basename(p_)
    for _dk, _names in _NONCARD_EXCLUDE.items():
        if _b in _names and os.path.normpath(os.path.dirname(p_)) == os.path.normpath(globals().get(_dk, "")):
            return True
    return False

# ── C-5 病⑦根治（2026-10-17·专项卡§二C-5）：成长箱切块过滤纯结构元块 ──
# 病灶：learnings 按 `## ` 切块时，"## 状态/Metadata"类模板元块被切成独立 doc 占候选位（C-3 全库 sim=1.0 双写的成因）。
# 判据选型：⛔标题黑名单（会烂——变体标题即漏网），✅纯字段行结构判据——块体非空行 100% 为状态/计数字段行才排除；
#          Summary 类正文句、裁定前言类 prose 天然不命中（不误伤内容本体，防误伤真卡红线同 C-2）。
_META_LINE_RE = re.compile(
    r"^\s*(?:-\s*\[[ x]\]|✅\s*已|-\s*\*{0,2}(?:出现次数|同类错误|Source|Tags|Related|状态|Error Count|Promoted to)|\*{0,2}本次：第\d|第\d+次(?:[（(]|$)|fixed\s*→)")
def _is_meta_block(blk):
    # 双判据（v2 实跑数据驱动·2026-10-17）：体长≤200字 且 非空行100%为状态/计数字段行——
    # 变体标题/无bullet勾选/裸"第N次"/fixed→promoted 箭头全收；prose 行（如"第2次时AI主动提醒…"）天然不命中。
    body_lines = [l for l in blk.splitlines()[1:] if l.strip()]
    if not body_lines or sum(len(l) for l in body_lines) > 200:
        return False
    return all(_META_LINE_RE.match(l) for l in body_lines)

def _fingerprint(paths):
    """stat 指纹（mtime_ns+size）——不 open 文件体，不触发读配额。"""
    fp = {}
    for _p in paths:
        try:
            _st = os.stat(_p)
            fp[_p] = [_st.st_mtime_ns, _st.st_size]
        except OSError:
            fp[_p] = None
    return fp

def build_docs():
    """缓存包装层：命中=1 次 open；失配=全量重建并回写缓存（直接 write·沙箱 rename 有 EPERM 前科）。"""
    paths = _corpus_paths()
    fp = _fingerprint(paths)
    try:
        if os.path.isfile(_DOC_CACHE):
            c = json.load(open(_DOC_CACHE, encoding="utf-8"))
            if c.get("schema") == 4 and c.get("fingerprint") == fp and isinstance(c.get("docs"), dict):
                return c["docs"]
    except Exception:
        pass  # 缓存损坏=视作未命中，走全量重建
    # ── 重建走分片子进程：每个子进程只 open ~_CHUNK 个文件（配额内），本进程零源文件 open ──
    parts_dir = os.path.join(os.path.dirname(_DOC_CACHE), "parts")
    try:
        os.makedirs(parts_dir, exist_ok=True)
        for _old in glob.glob(os.path.join(parts_dir, "part_*.json")):
            os.remove(_old)  # 清陈旧分片（防脏并）
        pats = _glob_patterns()
        total = max((len(glob.glob(pt)) for pt in pats), default=0)
        chunks = (total + _CHUNK - 1) // _CHUNK
        docs = {}
        _ok = True
        for _k in range(chunks):
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--build-chunk", str(_k)],
                               capture_output=True, text=True, timeout=300)
            partf = os.path.join(parts_dir, "part_%d.json" % _k)
            if not os.path.isfile(partf):
                print("⚠️ 索引分片构建失败 chunk=%d %s" % (_k, (r.stderr or "")[-120:]), file=sys.stderr)
                _ok = False
                break
            docs.update(json.load(open(partf, encoding="utf-8")))
        if _ok and docs:
            with open(_DOC_CACHE, "w", encoding="utf-8") as _f:
                json.dump({"schema": 4, "fingerprint": fp, "docs": docs}, _f, ensure_ascii=False)
            return docs
    except Exception as _e:
        print("⚠️ 分片重建异常 %s（退回当前解释器直建·可能触发读配额）" % _e, file=sys.stderr)
    docs = _build_docs_full()
    try:
        os.makedirs(os.path.dirname(_DOC_CACHE), exist_ok=True)
        with open(_DOC_CACHE, "w", encoding="utf-8") as _f:
            json.dump({"schema": 4, "fingerprint": fp, "docs": docs}, _f, ensure_ascii=False)
    except Exception:
        pass  # 缓存写失败不阻断检索主流程（下次重建即可）
    return docs

def _build_docs_chunk(k):
    """单分片构建（子进程模式）：glob 切片后走原 _build_docs_full，解析逻辑单一真源不复制。"""
    pats = _glob_patterns()
    real = {pt: glob.glob(pt) for pt in pats}
    _orig = glob.glob
    def _patched(pattern, *a, **kw):
        if pattern in real:
            return real[pattern][k * _CHUNK:(k + 1) * _CHUNK]
        return _orig(pattern, *a, **kw)
    glob.glob = _patched
    try:
        return _build_docs_full()
    finally:
        glob.glob = _orig

def _build_docs_full():
    """全库扫描建索引：{path: {"title","text","cat","src","summary"}}（v0.3.5 起由 build_docs 缓存包装调用）"""
    docs = {}

    # 知识池卡片（含文章卡片）：frontmatter category/tags + 标题 + summary + 正文前缀
    for p in glob.glob(os.path.join(POOL_DIR, "*", "*.md")):
        base = os.path.basename(p)
        if base == "INDEX.md":
            continue
        raw = open(p, encoding="utf-8").read()
        fm = parse_fm(raw)
        cat = fm.get("category", []) + fm.get("tags", [])
        summary = fm.get("summary", [""])[0]
        title = base.replace(".md", "")
        body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)[:500]
        docs[p] = {"title": title, "text": " ".join(cat) + " " + title + " " + summary + " " + body,
                   "cat": " ".join(cat), "src": "知识池", "summary": summary or title, "trust": trust_of(fm)}

    # 读书笔记：category/tags + 标题 + 正文（B' 修复：原 0 字入索 → 补正文）
    for p in glob.glob(os.path.join(NOTES_DIR, "*.md")):
        raw = open(p, encoding="utf-8").read()
        fm = parse_fm(raw)
        cat = fm.get("category", []) + fm.get("tags", [])
        title = os.path.basename(p).replace(".md", "")
        body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)[:800]   # ← B' 修复：原 0 字，现补正文
        summary = fm.get("summary", [""])[0]
        docs[p] = {"title": title, "text": " ".join(cat) + " " + (summary or "") + " " + body,
                   "cat": " ".join(cat), "src": "读书笔记", "summary": summary or title, "trust": trust_of(fm)}

    # 立场卡：topic/type/领域分诊 + 承重字段优先（B' 修复：原 300 字盲截+summary=title → 承重字段多向量）
    for p in glob.glob(os.path.join(AILIB_DIR, "*.md")):
        if os.path.basename(p) == "INDEX.md":
            continue
        raw = open(p, encoding="utf-8").read()
        fm = parse_fm(raw)
        cat = fm.get("topic", []) + fm.get("type", []) + fm.get("领域分诊", [])
        title = os.path.basename(p).replace(".md", "")
        body_full = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)
        if title.startswith("技能卡#"):
            # v0.3.15·T3：技能卡走专属 text（核心方法/适用边界/反例+summary 入面）。
            #   src 桶保持「立场卡」不变——rank_mixed 分档与 ROUTE_TABLE 源名都按 src 认路，
            #   新增 src=未经要求的改路由（最小方案纪律）。
            _sk = fm.get("summary", [""])
            _sk = _sk[0] if isinstance(_sk, list) else _sk
            _sk = _sk or brief(_extract_md_section(body_full, "核心方法")) or title
            docs[p] = {"title": title, "text": skill_card_view(raw, fm),
                       "cat": " ".join(cat), "src": "立场卡", "summary": _sk, "trust": trust_of(fm)}
            continue
        sec = {k: extract_section(body_full, k) for k in LOAD_BEARING}
        segs = [s for s in sec.values() if s]  # 承重字段优先
        # B'' 修复：366/366 立场卡 frontmatter 无 summary 字段 → 回退承重字段首句（主要矛盾 > 立场），非 title
        summary = fm.get("summary", [""])[0] or brief(sec.get("主要矛盾") or sec.get("立场")) or title
        docs[p] = {"title": title,
                   "text": " ".join(cat) + " " + " ".join(segs) + " " + body_full[:300],
                   "cat": " ".join(cat), "src": "立场卡", "summary": summary, "trust": trust_of(fm)}

    # 概念卡：标题 + 正文前缀
    for p in glob.glob(os.path.join(CONCEPT_DIR, "*.md")):
        raw = open(p, encoding="utf-8").read()
        fm = parse_fm(raw)
        title = os.path.basename(p).replace(".md", "")
        body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)[:300]
        docs[p] = {"title": title, "text": title + " " + body,
                   "cat": "", "src": "概念卡", "summary": title, "trust": trust_of(fm)}

    # 成长箱 learnings：错误模式与实证记录（2026-08-29 扩·GROWTH 源）
    # 依据：分身判据层的证据应"可达"——此前成长箱 45 条模式 + 59 条记录完全检索不到，
    #       与愿景④"越用越好用"冲突。按 `## ` 记录块切条，一条一 doc（对齐 stats.py 口径）。
    for _p in sorted(glob.glob(os.path.join(GROWTH_DIR, "*.md"))):
        if os.path.basename(_p) == "INDEX.md":
            continue
        if _is_noncard(_p):      # C-5：一次性复核表等工作文件出库（归属与位置解耦·物理不动）
            continue
        try:
            _raw = open(_p, encoding="utf-8").read()
        except OSError:
            continue
        _blocks = re.split(r"\n(?=## )", _raw)
        for _bi, _blk in enumerate(_blocks):
            _blk = _blk.strip()
            if not _blk:
                continue
            if _is_meta_block(_blk):   # C-5 病⑦：纯状态/Metadata 模板元块不入库
                continue
            _title = _blk.splitlines()[0].lstrip("#").strip()[:80] or os.path.basename(_p)
            docs[f"{_p}#{_bi}"] = {"title": _title, "text": _blk[:1200],
                                   "cat": "", "src": "成长箱", "summary": _title[:120],
                                   "trust": "unverified"}

    # 蓝图索引卡（2026-09-08 数字分身增强计划阶段1.3）：记忆蓝图→知识库的桥梁层
    # 核心承重字段=core_principles（设计断言），其次summary+tags+正文（设计背景/使用场景/常见误区）
    # 设计依据：知识库设计通用规范原则4（渐进式分层加载——先召回索引卡锚点，再下钻蓝图原文）
    for p in glob.glob(os.path.join(BLUEPRINT_INDEX_DIR, "*.md")):
        base = os.path.basename(p)
        if base.startswith("00-"):  # 跳过格式规范等元文件
            continue
        try:
            raw = open(p, encoding="utf-8").read()
        except OSError:
            continue
        fm = parse_fm(raw)
        if fm.get("type", [""])[0] != "blueprint-index":  # 只索引蓝图索引卡类型
            continue
        title = fm.get("title", [base.replace(".md", "")])[0]
        core_principles = fm.get("core_principles", [])
        summary = fm.get("summary", [""])[0]
        tags = fm.get("tags", [])
        source_path = fm.get("source_path", [""])[0]
        body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)[:600]
        # 承重字段优先：core_principles > summary > tags > 正文
        text = " ".join(core_principles) + " " + summary + " " + " ".join(tags) + " " + body + (" 常见问法 " + " ".join(fm.get("retrieval_queries", [])) if fm.get("retrieval_queries") else "")
        docs[p] = {"title": title, "text": text,
                   "cat": " ".join(tags), "src": "蓝图索引卡",
                   "summary": summary or title, "trust": trust_of(fm)}

    # Skill 一手 SKILL.md：工程类第一优先级知识源（方案 v3 §3.1）
    for p in glob.glob(os.path.join(_MC, "技能配置", "*", "SKILL.md")):
        if not os.path.isfile(p):
            continue
        raw = open(p, encoding="utf-8").read()
        fm = parse_fm(raw)
        title = os.path.basename(os.path.dirname(p))
        first_line = ""
        body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)  # 跳过 frontmatter（首行是 ---）
        for line in body.split("\n"):  # 正文首个非空行（# 标题）→ 中文实体提取源（目录名多为英文）
            if line.strip():
                first_line = line.strip().lstrip("# ").strip()
                break
        # ── 2026-09-07 eval 92% 根治（童灵·键 20260907_205652）：Skill 中文功能名入 cat ──
        # 根因：任务写中文名（"介绍每日伙伴"）时实体池只有英文目录名 daily-buddy → 不命中 → 无直通置顶；
        #       BM25 词表也无中文名（cat 空）→ 纯向量被扩容库稀释 → Top-5 外（eval 22/24 漂移实证）。
        # 修法：从 frontmatter description 提取首个中文功能名（2-8 字，剥"核心工作流/自动化视频流水线"等后缀）
        #       → cat 参与实体池扫描 + BM25 检索词表（双通道一次打通）；向量 doc_text 用 text 非 cat → 无需重建向量库。
        # ⚠️ parse_fm 对 YAML 折叠块（description: >）只取 ">" 符号 → 用 raw 正则直抓首行（通用：普通行与折叠块首行皆可）。
        # 折叠块若首行为 "-"（列表符）则顺延下一行（scriyore 先例）。
        _m_desc = re.search(r"description:\s*>?\s*\n?\s*([^\n]+)", raw)
        _desc_txt = _m_desc.group(1) if _m_desc else ""
        if _desc_txt.strip() == "-":
            _m_desc2 = re.search(r"description:[\s\S]*?\n\s*-?\s*([^\n]+)", raw)
            if _m_desc2:
                _desc_txt = _m_desc2.group(1)
        # 抓 description 开头的功能名：中文 2-8 字，止于分隔符（：:空格——/（）·，等），
        # 且剥已知功能后缀（核心工作流/工作流/自动化视频流水线/引擎/助手等）——"每日伙伴核心工作流：…"→"每日伙伴"
        _cn = re.match(r"\s*([\u4e00-\u9fff]{2,8})", _desc_txt)
        _cat_cn = ""
        if _cn:
            _cand = _cn.group(1)
            for _suf in ("核心工作流", "自动化视频流水线", "核心工作", "工作流", "强制刷新器", "强制刷新", "自动化", "引擎", "助手", "工具", "系统", "设计", "管理", "导航", "刷新器"):
                if _cand.endswith(_suf) and len(_cand) > len(_suf):
                    _cand = _cand[: -len(_suf)]
                    break
            if len(_cand) >= 2 and _cand not in _ENTITY_STOP:
                _cat_cn = _cand
        docs[p] = {"title": title, "text": title + " " + raw[:400],
                   "cat": _cat_cn, "src": "Skill", "summary": title,
                   "first_line": first_line, "trust": trust_of(fm)}
    # C-2 入库排除（见 _NONCARD_EXCLUDE 注释块）：分片/全量两路都汇到此 chokepoint
    _ex = [k for k in docs if _is_noncard(k)]
    for k in _ex:
        docs.pop(k)
    if _ex and os.environ.get("KB_DEBUG"):
        print("🧹 C-2 排除非卡 %d 条: %s" % (len(_ex), ", ".join(sorted(os.path.basename(x) for x in _ex))), file=sys.stderr)
    return docs


def extract_entity_pool(docs):
    """任务对象实体池：从文档 title + cat + Skill 首行标题提取 2-8 字纯中文片段。
    开放集合自动生长——新 Skill/书/概念加入知识库即自动成为实体，无需维护关键词表。
    v0.3.2: 英文 Skill 目录名整体入池（shall-we-talk → shall-we-talk / shall we talk 两变体），
    匹配时大小写不敏感（皮叔 2026-08-07 介绍 shall-we-talk 触发——中文实体池覆盖不到英文专名）。"""
    pool = {}
    for p, d in docs.items():
        segs = re.split(r"[\s\-–—()（）《》「」\"'，,。.、：:；;！!？?/\\|·~*#]+",
                        d["title"] + " " + d.get("cat", "") + " " + d.get("first_line", ""))
        for s in segs:
            s = s.strip()
            if 2 <= len(s) <= 8 and re.fullmatch(r"[\u4e00-\u9fff]+", s) and s not in _ENTITY_STOP:
                pool.setdefault(s, []).append(p)
        # v0.3.2：英文 Skill 目录名整体入池（纯小写字母/数字/连字符，≥3 字符）
        if d.get("src") == "Skill" and re.fullmatch(r"[a-z0-9-]{3,}", d["title"]):
            pool.setdefault(d["title"], []).append(p)
            pool.setdefault(d["title"].replace("-", " "), []).append(p)  # 空格变体（shall we talk）
    return pool


def intent_route(task):
    """意图分类：命中多个桶=复合意图（多标签预留）。返回 [(桶, 命中关键词)]"""
    hits = []
    for bucket in ROUTE_TABLE:
        kw = [k for k in bucket["keywords"] if k in task]
        if kw:
            hits.append((bucket, kw))
    return hits or [(ROUTE_TABLE[1], [])]  # 兜底：无法分类时默认评估桶


def idf_scores(docs, terms):
    """简化 IDF：log((N+1)/(df+1))+1，df=包含该词的文档数"""
    N = len(docs)
    df = {t: 0 for t in terms}
    for d in docs.values():
        for t in terms:
            if t in d["text"]:
                df[t] += 1
    return {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in terms}


def search(task, k=K):
    """检索核心（单一真源）：main CLI 与 eval 评测共用。
    任务内实体识别（文档侧自动生长）→ 实体命中文档豁免源过滤 + 小加权（对象素材刚需）。
    返回 (sorted_scores[:k], buckets)。"""
    docs = build_docs()
    buckets = intent_route(task)
    entity_pool = extract_entity_pool(docs)

    # 任务内实体识别：任务文本包含实体词 → 该实体文档直通（对象素材刚需；v0.3.2 大小写不敏感）
    hit_entities = [e for e in entity_pool if e.lower() in task.lower()]
    entity_docs = set()
    for e in hit_entities:
        entity_docs.update(entity_pool[e])

    # 查询词 = 任务词面∩桶关键词（词表封闭）∪ 文档键词∩任务 ∪ 任务内实体（开放集合）
    # v0.3.10 童灵根治·职责分离（2026-09-11）：v0.3.1 用桶全量关键词 term_pool.update(b["keywords"])
    #   ——把"路由判桶"（全量·宽）与"抽检索词"（任务词面·准）混为一谈：工程桶全量含 控制论/反馈/熵
    #   等纯术语，"构建Skill"任务误带术语 → 工程控制论卡词面霸屏挤出 skill-forge；
    #   移除术语矫枉过正 → "参考反馈闭环稳定性"任务路由不到工程桶（保底位不激活）。
    #   正解=职责分离：路由仍走全量（intent_route 内判定），检索词表只用 kw（任务词面∩桶关键词），
    #   近义词召回由 pool_books 保底位承担（"写碎碎念文案"→写作桶保底带出 借势/主角 书卡）。
    term_pool = set()
    for b, kw in buckets:
        term_pool.update(kw)
    for d in docs.values():
        for w in d["cat"].split():
            if w in task:
                term_pool.add(w)
    term_pool.update(hit_entities)
    # v0.3.2 实体变体展开：命中"shall we talk"(空格)时，连字符变体"shall-we-talk"也要进查询词
    # ——文档 text 的 title 是连字符目录名，只加命中变体则词面零命中（实体词 idf 7+ 白算）
    hit_variants = set()
    for e in hit_entities:
        if " " in e:
            hit_variants.add(e.replace(" ", "-"))
        elif "-" in e:
            hit_variants.add(e.replace("-", " "))
    term_pool.update(hit_variants)
    terms = [t for t in term_pool if len(t) >= 1]
    idf = idf_scores(docs, terms)

    # 路由加权：桶第一优先级源 ×3（写作桶=pool_books 书级；其他桶=sources[0] 源级——2026-08-07 补齐设计-实现差）
    SRC_MAP = {"POOL": "知识池", "NOTES": "读书笔记", "AILIB": "立场卡", "CONCEPT": "概念卡", "SKILL": "Skill", "GROWTH": "成长箱", "BLUEPRINT": "蓝图索引卡"}  # 2026-09-08 蓝图索接卡接入
    allowed = set()
    boost_srcs = set()
    for b, _ in buckets:
        allowed.update(SRC_MAP[x] for x in b["sources"])
        if b["name"] != "写作/文案" and b["sources"]:
            boost_srcs.update(SRC_MAP[x] for x in b["sources"][:1])  # 第一优先级知识源
    boosted = set()
    for b, _ in buckets:
        if b.get("pool_books"):  # B*：保底与桶名解耦——任意含 pool_books 的桶都触发钦定书保底
            for book in b["pool_books"]:
                boosted.add(book)

    scores = []
    for p, d in docs.items():
        if d["src"] not in allowed and (p not in entity_docs or d["src"] == "成长箱"):
            continue  # 实体命中文档豁免源过滤（对象素材刚需）·⛔成长箱例外（2026-09-07 你令根治泛命中：错误记录不因"分析/验证"等泛词实体豁免·只走 allowed 源过滤）
        s = 0.0
        matched = []
        for t in terms:
            c = d["text"].count(t)
            if c > 0:
                s += (1 + math.log(c)) * idf[t]
                matched.append(t)
        # B*：钦定书卡（boosted）即使零词面命中也强制入候选池（地板分 1e-4），由硬保底位抬升可见区；
        # 否则 BM25 零命中卡被 s<=0 剔除，保底位无法作用于它（原软保底三重残缺②）
        is_pool_card = (d["src"] == "知识池" and any(bk in d.get("title", "") for bk in boosted)) or any(f"/{bk}/" in p for bk in boosted)
        if s <= 0:
            if not is_pool_card:
                continue
            s = 1e-4
            matched = ["保底注入"]
        if (d["src"] == "知识池" and any(b in d["title"] for b in boosted)) or d["src"] == "Skill":
            s *= ROUTE_BOOST
        elif d["src"] in boost_srcs:
            s *= ROUTE_BOOST  # 桶第一优先级源（评估→立场卡/工程→概念卡/方法→读书笔记/健康→立场卡）
        elif p in entity_docs:
            s *= ENTITY_BOOST  # 实体素材小加权（不抢方法论主位）
        scores.append((s, p, d, matched))

    scores = rank_mixed(scores, task, entity_docs, docs=docs, allowed=allowed)  # B''：传全库+源白名单
    # ── pool_books 钦定书单硬保底位（B*·2026-08-17 三明智 L2 愿景对齐·硬保底解耦版）──
    # 根因升级（L2 实测 search_kb.py 457-493）：原保底位是"软保底三重残缺"——
    #   ① 仅写作桶触发（line 430 原写死 写作/文案；B* 改为任意含 pool_books 的桶）
    #   ② 软加分 0.013 远小于正常卡 7+ 分，且零词面命中卡被 line 446 s<=0 剔除、进不了候选池
    #   ③ 默认 K=5 截断，保底卡升入 Top-10~12 仍被切
    # B* 修复：保底与桶路由解耦（内容意图即触发 + ROUTE_TABLE 补全你内容词）+
    #          零命中池卡强制入池（line 446 地板分）+ 硬抬升可见区底（不依赖 AI 记触发词）
    # 防霸屏（继承 Agent B 修正）：总保底位上限 POOL_BOOK_MAX，保底卡贴可见 Top-K 底部、低于自然高相关卡
    POOL_BOOK_MAX = 6           # 总保底位上限（防霸屏；覆盖更多钦定书单）
    pool_guaranteed = []        # 保底卡收集（rank 插入在最终排序后执行·2026-09-11）
    if boosted:
        # 收集每本钦定书单在候选池内的最高分卡（含 line 446 强制入池的零命中卡）
        by_book = {}
        for s, p, d, matched in scores:
            if d.get("src") != "知识池":
                continue
            for book in boosted:
                # 书卡判定：title 含书名（如"主角-卡片9-品牌故事三要素"含"主角"）或路径含书名目录
                if book in d.get("title", "") or f"/{book}/" in p:
                    cur = by_book.get(book)
                    if cur is None or s > cur[0]:
                        by_book[book] = (s, p, d, matched)
                    break
        in_topk = {d.get("title", "") for _, _, d, _ in scores[:K]}
        for book, (s, p, d, matched) in sorted(by_book.items(), key=lambda kv: -kv[1][0]):
            if len(pool_guaranteed) >= POOL_BOOK_MAX:
                break
            if d.get("title", "") in in_topk:
                continue  # 已在 Top-K 出场，不浪费保底名额
            pool_guaranteed.append((s, p, d, matched))
    scores.sort(key=lambda x: -x[0])
    # v0.3.2 实体直通置顶：专名级实体（中文≥3字或英文目录名，且关联文档≤3）的对象素材直接置顶——
    # RRF 排名级融合救不动 BM25 rank 差（写作卡 100+ 分 vs 对象卡 20+ 分），
    # 而对象素材是任务刚需（皮叔 2026-08-07 介绍 shall-we-talk 触发，三明智/每日伙伴同样 30 名外）。
    # 2 字泛词（记忆/钩子/机制/系统）不置顶——"优化记忆系统的钩子机制"实测：
    # 泛词置顶挤占 Top5 使 eval target 掉出（22/23 失败样本）。
    strong = set()
    for e in hit_entities:
        is_name = len(e) >= 3 or "-" in e or " " in e
        if is_name and len(entity_pool[e]) <= 3:
            strong.update(entity_pool[e])
    if strong:
        strong_scores = [x for x in scores if x[1] in strong]
        rest = [x for x in scores if x[1] not in strong]
        scores = strong_scores + rest

    # ── tool_skills 工具置顶（2026-09-07·你诉求"写周报直接命中 Skill 省打字"）──
    # 场景词→执行工具的路由信号：桶声明 tool_skills（skill + triggers），任务词面命中 trigger
    # 时把该工具 Skill 卡提升到自然 Top 前——像点名 Skill 一样强，但用"场景词"触发免打字。
    # ⛔ triggers 是子集非桶全关键词（daily-buddy 管周报/复盘/日记，不管睡眠/精力/冥想——
    #    "改善睡眠质量"不该置顶 daily-buddy，eval 防回归）。
    # 对齐先例：pool_books（内容保底）+ 实体直通（对象置顶）；本机制=工具场景置顶。
    tool_skills_hits = []
    for b, _ in buckets:
        for ts in b.get("tool_skills", []):
            if not any(t in task for t in ts.get("triggers", [])):
                continue
            tname = ts.get("skill", "")
            for x in scores:
                if x[2].get("src") == "Skill" and (tname in x[1] or tname in x[2].get("title", "")):
                    if x not in tool_skills_hits:
                        tool_skills_hits.append(x)
                    break
    if tool_skills_hits:
        # 工具卡提到自然 Top 前（保留原排序，置于所有非工具卡前）
        tool_paths = {x[1] for x in tool_skills_hits}
        rest2 = [x for x in scores if x[1] not in tool_paths]
        scores = tool_skills_hits + rest2
    # ── pool_books 保底卡 rank 强制插入可见区底部（2026-09-11 童灵修复·降级模式 anchor 分数锚定失效根治）──
    # 原实现 new_s = scores[target_rank][0] + 1e-3 假设 RRF 融合后 rank 级分数（差异微小）；
    # 向量降级纯 BM25 模式下自然卡分数悬殊（立场卡 603 vs 书卡 11.9），anchor+1e-3 完全不够，
    # 保底卡被自然高分卡碾压掉出 Top-K（实证：注入 pool_books 后 0 张进 Top-12）。
    # 改 rank 插入：保底卡置入可见区底部 n 位（Top-K 最后 n 位），任何分数尺度下稳定出场；
    # 不高于自然高相关卡（保底卡居后）、防霸屏不变（POOL_BOOK_MAX 上限 + 已在 Top-K 不占名额）。
    if pool_guaranteed:
        gpaths = {x[1] for x in pool_guaranteed}
        rest = [x for x in scores if x[1] not in gpaths]
        insert_at = min(K - len(pool_guaranteed), len(rest))
        # A4 nat_rank(2026-10-17·外部二轮评审"强插位污染反馈信号"采纳):插位卡记无插自然位
        _natmap = {x[1]: i + 1 for i, x in enumerate(rest)}
        _NAT.d = {x[1]: _natmap.get(x[1]) for x in pool_guaranteed}  # None=自然零出场
        scores = rest[:insert_at] + pool_guaranteed + rest[insert_at:]
    else:
        _NAT.d = {}
    return scores[:k], buckets


def read_full(path):
    """渐进式加载·阶段2下钻（2026-08-14 落地·外部校准 TencentDB Agent Memory）：
    读取指定卡片完整正文（去 frontmatter）。路径支持相对 HOME 或绝对。
    对应 TencentDB 的 anchor→drill-down：search() 阶段1 返回锚点(title+summary+path)，
    AI/路由判定某卡相关后，阶段2 用本函数拉全卡注入，避免一次性平铺全库正文撑爆上下文。"""
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        p = os.path.join(HOME, path)
    if not os.path.isfile(p):
        return None, f"❌ 文件不存在: {p}"
    raw = open(p, encoding="utf-8").read()
    body = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)
    return body.strip(), p


import threading as _threading  # A4 反馈去污染(2026-10-17):daemon 一连接一线程,thread-local 防串账
_NAT = _threading.local()

def _log_cli_trail(task, scores, buckets):
    """CLI 实跑落 kb_query_trail（source=cli·v0.3.14·2026-10-07 原则17 机械锚补全）。
    推翻 kb_query_trail 2026-09-07「⛔不改 search_kb.py」旧约束（当时观测面=注入流）：
    原则17「引用须绑实跑」立后，CLI 实跑=一等观测流量，写账点收敛为引擎出口单点。
    kb_serve/kb_inject_prompt 均 import search() 模块内调用（不进 main），各自按
    serve/fallback 记账如旧——零双记账。失败静默（观测层不阻断·对齐 _log_degrade）。"""
    try:
        import kb_query_trail as _qt
    except Exception:
        _qt = None
        try:
            _p = os.path.join(_ENGINE_DIR, "scripts")
            if _p not in sys.path:
                sys.path.insert(0, _p)
            import kb_query_trail as _qt
        except Exception:
            pass
    if _qt is None:
        return
    try:
        _qt.append_trail(task, scores, [b[0]["name"] for b in buckets] if buckets else [], source="cli", nat=getattr(_NAT, "d", None))
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    if not args:
        print("用法: python3 search_kb.py \"任务描述\"")
        print("     python3 search_kb.py --drill <相对HOME的路径>   # 渐进式加载·阶段2下钻全卡")
        return 1
    if args[0] == "--build-chunk":
        _k = int(args[1])
        _docs = _build_docs_chunk(_k)
        _parts = os.path.join(os.path.dirname(_DOC_CACHE), "parts")
        os.makedirs(_parts, exist_ok=True)
        with open(os.path.join(_parts, "part_%d.json" % _k), "w", encoding="utf-8") as _f:
            json.dump(_docs, _f, ensure_ascii=False)
        print("chunk %d: %d docs" % (_k, len(_docs)))
        return 0
    if args[0] == "--drill":
        if len(args) < 2:
            print("用法: python3 search_kb.py --drill <相对HOME的路径>"); return 1
        body, p = read_full(args[1])
        if body is None:
            print(p); return 1
        print(f"📂 下钻: {os.path.relpath(p, HOME)}\n")
        print(body)
        return 0
    if args[0] == "--status":
        # E-1 根治（2026-10-22 上游反馈单V2）：验收记录状态头三行——落记录当时机检取
        # 运行状态，⛔不凭印象；降级态不得混入基线（口径同源=包内 references/steps/
        # step7-verification.md §7b+；此前 --status 仅在 _FAST_ARGS 豁免名单、main()
        # 无分支=被当查询词吃掉的死接口，本批补真实现）。
        _ok_model, _why = _model_available()
        _nv = -1
        try:
            if os.path.isfile(VEC_NPY_META):
                _nv = len(json.load(open(VEC_NPY_META, encoding="utf-8")).get("paths", []))
            elif os.path.isfile(VEC_FILE):
                _nv = len(json.load(open(VEC_FILE, encoding="utf-8")))
        except Exception:
            _nv = -1
        print("# 状态: %s" % ("语义层在位" if _ok_model else "降级（纯BM25）·原因: %s" % _why))
        print("# 模型: %s ｜ 向量数: %s" % (MODEL_EFFECTIVE, _nv if _nv >= 0 else "读取失败"))
        print("# 判据: 输出含「⚡语义#」标记=在位；无该标记=降级态记录，不得写入基线")
        return 0
    # CLI 快通道（2026-10-11·kb_serve 常驻引擎客户端·「该命中的→毫秒拿到」最后一公里）：
    # socket 在位→驻留引擎毫秒返回（实测 0.09-0.15s vs 冷路径 18.5s）；任何异常→回退冷路径
    # （kb_serve 设计约束"失败默认放行"同款·不阻塞）。trail 记 source=serve（诚实源分布账）。
    _task0 = args[0]
    if not _task0.startswith("--"):
        try:
            import time as _time
            import socket as _socket
            _sock_cands = [
                os.path.join(_ENGINE_DIR, "scripts", "kb.sock"),
                os.path.join(_MC, "开发工具", "知识联邦引擎", "scripts", "kb.sock"),
                os.path.join(_MC, "脚本中心", "知识联邦引擎", "scripts", "kb.sock"),
            ]
            _sock_path = next((c for c in _sock_cands if os.path.exists(c)), None)
            if _sock_path:
                _t0 = _time.time()
                _c = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
                _c.settimeout(10)
                _c.connect(_sock_path)
                _c.sendall((json.dumps({"task": _task0, "k": K}) + "\n").encode("utf-8"))
                _buf = b""
                while not _buf.endswith(b"\n"):
                    _chunk = _c.recv(65536)
                    if not _chunk:
                        break
                    _buf += _chunk
                _c.close()
                _resp = json.loads(_buf.decode("utf-8"))
                if _resp.get("ok"):
                    _dt = _time.time() - _t0
                    _hits = _resp.get("hits", [])
                    print(f"⏱ {datetime.now().strftime('%H:%M')} | 意图路由: {', '.join(_resp.get('buckets', []))} | 候选: {len(_hits)} | 快通道 {_dt:.2f}s")
                    print(f"任务: {_task0}\n")
                    _budget = int(os.environ.get("KB_CHAR_BUDGET", CHAR_BUDGET))
                    _used = 0
                    _pscores = []
                    for _i, _h in enumerate(_hits, 1):
                        _pscores.append((_h.get("score", 0), _h.get("path", ""),
                                         {"src": _h.get("src", ""), "title": _h.get("title", ""),
                                          "summary": _h.get("summary", ""), "trust": "unverified"},
                                         _h.get("matched") or []))
                        _sc = f"{_h.get('score', 0):.4f}" if _h.get("score", 0) < 1 else f"{_h.get('score', 0):.1f}"
                        _rel = os.path.relpath(_h.get("path", ""), HOME) if _h.get("path") else ""
                        _entry = (f"[{_i}] 得分{_sc} | {_h.get('src', '')} | {_h.get('title', '')}\n"
                                  f"    {_rel}\n"
                                  f"    命中: {', '.join((_h.get('matched') or [])[:8])} | {(_h.get('summary') or '')[:50]}\n"
                                  f"    ⛔ 这条没用 → 回写路由表/关键词（反馈闭环）")
                        if _used + len(_entry) > _budget:
                            print("    …（字符预算已用尽，低分条目已省略）")
                            break
                        _used += len(_entry)
                        print(_entry)
                    try:
                        import kb_query_trail as _qt2
                    except Exception:
                        _qt2 = None
                        try:
                            _tp = os.path.join(_ENGINE_DIR, "scripts")
                            if _tp not in sys.path:
                                sys.path.insert(0, _tp)
                            import kb_query_trail as _qt2
                        except Exception:
                            _qt2 = None
                    if _qt2 is not None:
                        try:
                            _qt2.append_trail(_task0, _pscores, [b for b in _resp.get("buckets", [])], source="serve", nat=_resp.get("nat"))  # A4修正:nat在daemon进程生成,经协议透传(本地_NAT恒None)
                        except Exception:
                            pass  # 观测层不阻断（对齐 _log_cli_trail）
                    print(f"\nTop-K={K} · 快通道（kb_serve 常驻引擎·异常自动回退冷路径）")
                    return 0
        except Exception:
            pass  # 快通道任何失败→回退冷路径（设计律：失败默认放行·kb_serve 同款）
    task = args[0]
    scores, buckets = search(task)
    _log_cli_trail(task, scores, buckets)
    print(f"⏱ {datetime.now().strftime('%H:%M')} | 意图路由: {', '.join(b[0]['name'] for b in buckets)} | 候选: {len(scores)}")
    if not scores:
        print("⚠️ 0 候选——检索源不可达或语料为空（⛔ 不代表库里没有，勿据此判定）"
              + ("；诊断: " + " ｜ ".join(_LAYOUT_DIAG) if _LAYOUT_DIAG else ""))
    print(f"任务: {task}\n")
    budget = int(os.environ.get("KB_CHAR_BUDGET", CHAR_BUDGET))
    used = 0
    truncated = False
    for i, (s, p, d, matched) in enumerate(scores, 1):
        rel = os.path.relpath(p, HOME)
        sc = f"{s:.4f}" if s < 1 else f"{s:.1f}"  # RRF 分数<1 用 4 位小数
        entry = (
            f"[{i}] 得分{sc} | {d['src']} | {d['title']}\n"
            f"    {rel}\n"
            f"    命中: {', '.join(matched[:8])} | {d['summary'][:50]}\n"
            f"    ⛔ 这条没用 → 回写路由表/关键词（反馈闭环）"
        )
        if used + len(entry) > budget:
            truncated = True
            break
        used += len(entry)
        print(entry)
    if truncated:
        print(f"    …（字符预算 {budget} 已用尽，低分条目已省略，可用 --drill 按需下钻）")
    print(f"\nTop-K={K} · 先本地后外搜 · 来源可追溯")
    print(f"💡 渐进式加载：上面是锚点层(title+summary+path)；要全卡正文用 → python3 search_kb.py --drill <上列路径>")
    # 写作桶参考书单（你钦定 pool_books·2026-08-07 你质疑"借势/主角也可以参考"后补）
    books = []
    for b, _ in buckets:
        if b["name"] == "写作/文案" and b.get("pool_books"):
            books = b["pool_books"]
    if books:
        print(f"📚 参考书单（写作桶钦定·可整书参考）: {' / '.join(books)}")


if __name__ == "__main__":
    sys.exit(main())
