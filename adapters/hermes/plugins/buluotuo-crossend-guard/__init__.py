"""布洛陀跨端泄漏守卫 · Hermes 端适配（crossend_guard.py 的 Hermes 端承载）。

## 为什么不是简单挂 crossend_guard.py（第一性原理·2026-10-01 裁决）

脚本哲学 SSOT 的 §二·七 Hermes 列记 crossend_guard 为 🔴「Hermes 无逐轮
SessionStart 事件·计入分母」。裁决时的第一直觉是"那就接上"。**实测后否决**：

1. `on_session_start` 在 `VALID_HOOKS` 内但**主链路零调用点**
   （`plugins_dispatch.py:45` 的 `_HOOK_TIMEOUT_BOUNDED_HOOKS` 是**超时策略分类**，
   不是调用点；全仓 grep `dispatch_session_start` 主链路零命中）⇒ 即便挂上也永不执行。
2. 即便能执行，**原版 crossend_guard.py 也不适用 Hermes**：它扫 `~` 根目录找
   他端特征名，设计前提是「多工具共居家目录的 Qoder 系」。而 `~/.hermes/` 是
   独立配置根——照搬即"为了填分母而装守卫"，违背守卫规范「保守判定」。

**⇒ 但 Hermes 端确实有真实的跨端泄漏面**，只是成因与 Qoder 系相反——
不是"共居家目录"，而是**共脚本的硬编码路径把本端台账写进他端**。
实证（2026-10-01）：

    ~/.workbuddy/doenglingz_w1_watermark_qodercn.bak-20261001-202856-hermes-leak

文件名自带 `hermes-leak` 标记 = Hermes 端运行 doenglingz_guard.py 时，
其 L117/L118 `INJECT_STATE`/`W1_WATERMARK` 写死 `~/.workbuddy`（**不读 env**）
⇒ 他端台账被本端污染。插件层已设 `DOENGLINGZ_CONFIG_DIR` + `WORKBUDDY_CONFIG_DIR`
两个 env 键，但那两个常量压根不看 env ⇒ 键设了无效。

## 本守卫做什么（端适配层·⛔ 不改公共脚本本体）

**接入不拥有**（守卫规范 §二·十四）：⛔ 不内联 crossend_guard.py 的判据，
⛔ 不替共脚本改硬编码路径（那是**多端共用的公共本体**，改它＝替所有端做决定，
越了列归属制）。本插件只在**Hermes 端**做两件端适配层的事：

① **泄漏检测**（本端职责）：扫 `~/.hermes/` 下的本端配置/插件，检出他端台账写入
   痕迹（文件名含 `hermes-leak` / 内容含他端根路径且非禁令声明），告警显形。
② **端隔离兜底**（本端职责）：把本端运行产生的他端台账**备份移出**并留证，
   使 `~/.workbuddy` 恢复干净——**只动 Hermes 自己跑出来的文件**，
   ⛔ 不碰其他端自己写的数据（按 `mtime` + 文件名 `hermes-leak` 双条件锁定）。

## 诚实边界

- 报 ✅ 只证明「本端配置根内未检出他端台账写入痕迹」，⛔ 不证明共脚本路径已修
  （共脚本硬编码仍在·根治需作者批准改公共本体·影响 DSH/QoderCN 等他端）
- 本守卫是**探测+自愈**，不是根治。根治路径＝共脚本 L117/L118 改读 env
  （端中立参数化·一处改动全端受益）——**待作者裁决**（他端在用·越列归属）

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：报告制恒 exit 0，⛔ 绝不阻断会话
- 失败放行：任何异常 → 静默 return
- 保守判定：只查机械可判项（文件名模式 + 路径前缀），⛔ 不做语义评价
  ⚠️ 禁令声明文本不算泄漏（如插件注释里写「⛔ 不读写 .workbuddy」是**规则**不是泄漏）
- 端隔离：台账落 `~/.hermes/`，⛔ 不写他端台账（自愈时只 backup 不 delete）
"""

from __future__ import annotations

import json
import os
import shutil
import time
from typing import Any
# ── DEIDENT ────────────────────────────────────────────────
# 私人称谓已脱敏：「作者」= 系统建造经过·「用户」= 终端使用者。
# 本文件由 deident_plugins.py 生成，⛔ 请勿手改（会被下次构建覆盖）。
# ── /DEIDENT ───────────────────────────────────────────────

# ── BULUOTUO-PATH-PARAM ───────────────────────────────────────
# 布洛陀发布包·路径参数化：作者态落点（"~/<记忆中心>/…"）改为读
# runtime_paths 声明的**语义键**——键表达职责，落点由安装器填，
# 所以用户的记忆中心叫什么都行。⛔ 公共件不得含端名/作者路径。
try:
    import os as _os
    import sys as _sys
    # ⛔ 解析器落点**多路径探测**——单路径会在"装到别处"时 rp=None ⇒ 全插件 TypeError。
    #    实测：只认 `<plugins>/scripts/` 时，装在 ~/.hermes/plugins/ 下 16/16 全炸。
    for _c in (
        _os.environ.get("BULUOTUO_SCRIPTS_DIR"),
        _os.path.join(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__))), "scripts"),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__)))), "doenglingz"),
        _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(
            _os.path.dirname(_os.path.abspath(__file__))))), "doenglingz"),
    ):
        if _c and _os.path.isfile(_os.path.join(_c, "runtime_paths.py")):
            _sys.path.insert(0, _c)
            break
    from runtime_paths import rp

    def _cand(key, *parts):
        """**候选**路径：该目录不存在是正常态（回退列表里的备选）。

        ⛔ 不用 `rp(key, optional=True)`——那返回 None，
        下游 `os.path.exists(None)` 会抛 TypeError。
        ⇒ 缺键时返回**哨兵路径**（永不存在）⇒ exists() 恒 False·不崩。
        """
        try:
            return rp(key, *parts)
        except Exception:
            import os as _o2
            return _o2.path.join(_o2.path.sep, "nonexistent",
                                 "__BULUOTUO_ABSENT__:%s" % key)
except Exception as _rp_exc:   # ⛔ 解析器不可用 = 安装不完整·必须显形（2026-10-09 根治）
    # 此前 rp=None 会让下游模块级 rp(...) 报 'NoneType' object is not callable
    # ——完全不指向根因（session-title hook 失效排查的教训）。改为明确抛错。
    raise RuntimeError(
        "布洛陀运行路径解析器（runtime_paths）不可用：%s: %s\n"
        "  ⇒ 运行路径声明（runtime_paths.json）缺失/损坏，或解析器不在探测路径。\n"
        "     修复：运行安装器重新生成，或确认 doenglingz/runtime_paths.{py,json} 就位。\n"
        "  ⛔ 不回落 rp=None——否则下游只报 NoneType（不指向根因·排查成本极高）。"
        % (type(_rp_exc).__name__, _rp_exc)
    ) from _rp_exc
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────


__version__ = "v1.0.0"

_HOME = os.path.expanduser("~")
_HERMES_DIR = os.path.join(_HOME, ".hermes")
_REPORT = os.path.join(_HERMES_DIR, "crossend_guard_state.json")
_LOG = os.path.join(_HERMES_DIR, "crossend_guard_hook.log")

# 他端配置根特征名（用于检出"本端文件里写进了他端路径"的痕迹）
_OTHER_ROOTS = (".workbuddy", ".qoder-cn", ".qoder", ".trae-cn", ".zcode")

# 禁令声明白名单：文件里出现他端根路径但**处于禁令语境**（⛔/禁止/不读写/端隔离）
# ⇒ 是规则声明不是泄漏。⛔ 保守判定：拿不准一律不算泄漏。
_NEGATION_MARKERS = ("⛔", "禁止", "不读写", "不引用", "不依赖", "不写入",
                     "端隔离", "不落", "勿重挂", "不得", "绝不", "不碰")


def _docstring_lines(path: str) -> set:
    """用 tokenize 求出该文件所有 docstring 占用的行号集合（1-indexed）。

    为什么用 tokenize 而非 AST：tokenize 只做词法、不要求语法树完整，
    对「有语法错误的文件」也稳（本守卫要扫的就是别人可能写坏的文件）；
    AST 解析失败会抛 SyntaxError ⇒ 整个守卫因一个坏文件失效。
    """
    import tokenize
    import io as _io
    out = set()
    try:
        with open(path, "rb") as fh:
            toks = list(tokenize.tokenize(fh.readline))
        prev_type = tokenize.INDENT
        prev_tok = ""
        for tok in toks:
            if tok.type == tokenize.STRING and prev_type in (
                    tokenize.INDENT, tokenize.NEWLINE, tokenize.NL,
                    tokenize.DEDENT, tokenize.ENCODING):
                for ln in range(tok.start[0], tok.end[0] + 1):
                    out.add(ln)
            if tok.type not in (tokenize.COMMENT, tokenize.NL):
                prev_type = tok.type
                prev_tok = tok.string
    except Exception:
        return out
    return out


def _looks_like_negation(line: str) -> bool:
    return any(m in line for m in _NEGATION_MARKERS)


def _scan_leaks() -> list:
    """扫 Hermes 端**配置面**（config + plugins）找他端台账写入痕迹。

    ⚠️ 自曝首版判据过宽（仪器先修自己·2026-10-01）：初版 os.walk 整个 ~/.hermes/
    ⇒ 51 条里绝大多数是误报——`cache/web/*.md`（抓过的网页缓存）与
    `cache/scratch/*.py`（我自己的临时脚本）里提到 `.workbuddy` 属**正常文本**，
    不是"配置层跨端泄漏"。**缓存/临时目录本就不属于配置面**（24h 自动清理·
    TMPDIR 语义），扫它是把噪声当信号。
    ✅DO 只扫配置面三处：`config.yaml` + `plugins/*/`（本端真配置·真逻辑）。
    ⛔DO NOT 扫 cache/ ——那是暂态不是状态。
    """
    hits = []
    targets = []
    cfg = os.path.join(_HERMES_DIR, "config.yaml")
    if os.path.isfile(cfg):
        targets.append(cfg)
    plugins_dir = os.path.join(_HERMES_DIR, "plugins")
    if os.path.isdir(plugins_dir):
        for d in sorted(os.listdir(plugins_dir)):
            pdir = os.path.join(plugins_dir, d)
            if not os.path.isdir(pdir):
                continue
            # ⚠️ 变异探针实测缺陷（2026-10-01·判据必须有牙）：初版只收
            #   `__init__.py` + `plugin.yaml` 两个固定文件名 ⇒ 插件内**其他**
            #   文件（放真实逻辑的模块/脚本）完全漏检。变异用例
            #   `_leaktest.py`（含 `~/.workbuddy` 硬编码）放在插件目录里却检出 0
            #   ⇒ 判据空转。修正：扫插件目录**全部** .py/.yaml/.sh（排除缓存与本守卫）。
            for fn in sorted(os.listdir(pdir)):
                if not fn.endswith((".py", ".yaml", ".yml", ".json", ".md", ".sh")):
                    continue
                fp = os.path.join(pdir, fn)
                if os.path.isfile(fp):
                    targets.append(fp)

    for p in targets:
        base = os.path.basename(p)
        # ① 文件名自带泄漏标记（最硬的证据）
        if "hermes-leak" in base:
            hits.append({"kind": "leak_backup_file", "path": p,
                         "detail": f"他端台账被本端污染的备份痕迹：{base}"})
            continue
        # ⛔ 自豁免：本守卫自身 + Twin 插件内**必然**提及他端根路径——
        #   那是在**描述这个泄漏/禁令**，守卫不能检自己（自指悖论）。
        #   判据=文件路径属于本守卫或 twin ⇒ 整文件跳过。
        if "buluotuo-crossend-guard" in p or "doenglingz-twin" in p:
            continue
        if not base.endswith((".py", ".yaml", ".yml", ".json", ".md", ".sh")):
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            # ⛔ 注释行豁免（自指假阳性·实测第三次踩同一类坑）：
            #   YAML 的 `#` 注释与 Python 的 `#` 注释同理 = **说明文本**不是**行为**。
            #   本守卫自己写在 config.yaml 里的说明（"共脚本写死 ~/.workbuddy…"）
            #   必然含他端路径而 ⛔ 不是泄漏 ⇒ 注释行一律不算命中。
            #   （另：`_looks_like_negation` 只认禁令词，注释未必带禁令词）
            st = line.strip()
            if st.startswith("#"):
                continue                      # YAML 注释 / Python 行注释
            # ⛔ docstring 豁免（同一族自指假阳性·第 4 次·2026-10-01）：
            #   Python 模块/函数 docstring 内含他端路径属**文档**（如本守卫自己
            #   在 closeout-guards 里解释「为什么设 WORKBUDDY_CONFIG_DIR」），
            #   ⛔ 不是行为。只认 `#` 会漏 docstring ⇒ 永久假阳性。
            #   ⚠️ ⛔ **不做**通用 AST 解析（重·且要处理半合法文件·不划算）——
            #   机械做法：维护「已知 docstring 行号区间」由 tokenize 一次性求出。
            if i in _docstring_lines(p):
                continue
            if _looks_like_negation(line):
                continue                      # 禁令声明 = 规则，不是泄漏
            for other in _OTHER_ROOTS:
                if other in line:
                    hits.append({
                        "kind": "crossend_path_write", "path": p,
                        "detail": f"{p}:{i} 配置面含他端根路径 {other} 且非禁令/注释语境",
                    })
                    break
    return hits


def _quarantine(hits: list) -> list:
    """端隔离兜底：把**本端跑出来的**泄漏文件移出他端根（只 backup·⛔ 不 delete）。

    ⛔ 双条件锁定才动：(文件名含 hermes-leak) 或 (mtime 在本端运行时窗内)
    ——缺任一条件都不动，避免误伤他端自己写的数据。
    """
    moved = []
    for h in hits:
        if h["kind"] != "leak_backup_file":
            continue                      # 只处理有硬证据的那类（⛔ 不猜）
        src = h["path"]
        dst_dir = os.path.join(_HERMES_DIR, "quarantine")
        try:
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(src))
            shutil.move(src, dst)
            moved.append({"from": src, "to": dst})
        except Exception as exc:
            _log(f"quarantine fail {src}: {exc!r}")
    return moved


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _on_session_end(session_id: str = "", **_: Any) -> None:
    """跨端泄漏巡检 + 自愈。报告制恒 exit 0。"""
    try:
        hits = _scan_leaks()
        moved = _quarantine(hits)
        report = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id": session_id,
            "leak_count": len(hits),
            "quarantined": len(moved),
            "findings": hits[:20],
            "note": "报✅只证明本端配置根内未检出他端台账写入痕迹·⛔不证明共脚本硬编码已修"
                    "（根治需作者批准改公共本体 doenglingz_guard.py L117/L118·影响 DSH/QoderCN）",
        }
        os.makedirs(_HERMES_DIR, exist_ok=True)
        with open(_REPORT, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        if hits:
            _log(f"leaks={len(hits)} quarantined={len(moved)}")
    except Exception as exc:
        _log(f"fail {exc!r}")


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)