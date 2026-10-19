"""布洛陀路由家族 + 知识库 · Hermes 会话结束审计钩子。

原生接入方式：Hermes 插件钩子 `on_session_end`。
当一次会话结束时，自动运行：
  - 路由家族审计（route_guard_audit.py / route_reconcile_report.py）
  - 知识库审计（audit_search_kb.py / feedback_detect.py，经 _hermes_transcript_adapter
    从 state.db 导出 transcript 喂给既有脚本——脚本逻辑不动，适配在接入层）

把"本轮是否触发了正确路由/是否漏检知识库/是否有反馈信号"写回系统日志。

Hermes 插件回调签名（实证自官方 disk-cleanup 插件）：
    def _on_session_end(session_id: str = "", **_) -> None:
框架按回调签名过滤 invoke_hook 传入的 kwargs。

注意：Hermes 没有 Claude Code 的 UserPromptSubmit 事件，因此
"路由注入"类脚本改用 Skill（buluotuo-scripts）机制承载；本插件
只负责"会话结束的守护/审计"这一可靠落点。
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List
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


# 路由家族脚本真身在 脚本中心（devtools 键直接=脚本中心·route_audit.py 等四件在册）。
# ⚠️ 2026-10-12 Hermes 适配核证根治：原 _CANDIDATE_DIRS 用 custom_route(缺键→哨兵路径)
#   + devtools/scripts(子路径不存在·devtools 直接=脚本中心) ⇒ 四候选全 exists=False
#   ⇒ _find_script 恒返 None ⇒ route_audit.py 在本端**从未执行**（审计账本 hermes 0 行实证）。
#   修法=候选直指 devtools 本体（脚本中心）+ Skill路由引擎运行位（软链真源·双保险）。
#   根因定性=挂载≠生效家族第二例（ZCode 内部台账 model-io 空转同族·挂载了但探不到脚本位）。
_CANDIDATE_DIRS = [
    rp("custom_route"),
    rp("devtools"),
    rp("script_center"),
]

# 知识库审计适配器（接入层：从 state.db 导出 transcript 喂给既有审计脚本）。
# 2026-10-12 ZCode 真源侧收口：adapter 已迁顶层（rp("kb_engine") 命中·旧位转软链）——
#   端侧旧位兜底退役（下方旧位候选块已移除·迁移见内部台账）。
#   adapter 产出 = {"role":..., "message":{"content":[{"type":"text","text":c}]}}（CC式JSONL）
#   → route_audit read_transcript 原解析直接命中（model-io 分支=ZCode 专有·与 Hermes 无关）。
_KB_ADAPTER = rp("kb_engine", "scripts", "_hermes_transcript_adapter.py")

# 平台接入率漂移校验（跨工具中立·接入不拥有：仅调用公共脚本）
_PAC_SCRIPT = rp("devtools", "platform_adaptation_check.py")
# 读文件证据检测守卫（2026-08-22 新增·检测"凭印象判断"漂移）
_READ_EVIDENCE_SCRIPT = rp("devtools", "hermes_read_evidence_guard.py")
# 自主进化误差量化信号层（跨工具中立·接入不拥有：仅调用公共脚本）
_EVO_SCRIPT = rp("devtools", "evolution_deviation.py")
# 语义路由自进化建议生成（跨工具中立·接入不拥有：仅调用公共脚本）
_RES_SCRIPT = rp("devtools", "route_evolution_suggest.py")
# 自寻优引擎（跨工具中立·接入不拥有：仅调用公共脚本）
_SO_SCRIPT = rp("devtools", "self_optimization_engine.py")
# 面板数据快照积累器（跨工具中立·接入不拥有：仅调用公共脚本）
_PS_SCRIPT = rp("devtools", "panel_snapshot.py")
# 只读巡检类守卫（跨工具中立·接入不拥有：on_session_end 扩调）
_RULE3_SCRIPT = rp("devtools", "rule_three_layer_guard.py")
_CARDID_SCRIPT = rp("devtools", "card_id_guard.py")

# on_session_end 时运行的审计脚本（按存在与否依次尝试，**逐个都跑**，不再"找到第一个即跑"）。
# 真实成员来自脚本哲学家族实例（2026-10-01 复核实测）：
#   · route_audit.py          —— 存在·15KB·吃 {"transcript_path": ...}（stdin）·写 route_audit.jsonl（分源对账账本）
#   · route_guard_audit.py    —— 存在·守卫族审计
#   · route_reconcile_report.py —— 存在·两账对账报告
# ⚠️ 历史注释称"route_audit.py 不存在"——**该断言已过时（实测文件在·2026-09-23 mtime）**，
#    致 route_audit.py 长期漏跑 ⇒ Hermes 端在分源账本里完全缺席（2026-10-01 实测 src 分布
#    无 hermes）⇒ deviation 面板算不出 Hermes 的预测-实际偏差。已按实盘补入。
_AUDIT_SCRIPTS = ["route_audit.py", "route_guard_audit.py", "route_reconcile_report.py"]


def _find_script(name: str) -> str | None:
    for d in _CANDIDATE_DIRS:
        if not d or not os.path.isdir(d):
            continue
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK) or os.path.isfile(p):
            return p
    return None


def _run_kb_audit(session_id: str) -> None:
    """知识库审计：经适配器从 state.db 导出 transcript，喂给 audit_search_kb /
    feedback_detect（脚本逻辑不动，适配在接入层）。失败静默放行。"""
    if not session_id or not os.path.isfile(_KB_ADAPTER):
        return
    log_dir = rp("worklog")
    os.makedirs(log_dir, exist_ok=True)
    for mode in ("audit", "feedback"):
        try:
            proc = subprocess.run(
                ["python3", _KB_ADAPTER, session_id, mode],
                capture_output=True,
                text=True,
                timeout=150,
            )
            out_path = os.path.join(log_dir, f"kb_audit_{mode}_{session_id}.log")
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(f"# 知识库审计({mode}) @ session {session_id}\n")
                fh.write(f"adapter: {_KB_ADAPTER}\n")
                fh.write(f"returncode: {proc.returncode}\n")
                fh.write("--- stdout ---\n")
                fh.write(proc.stdout or "")
                fh.write("--- stderr ---\n")
                fh.write(proc.stderr or "")
        except Exception as exc:
            try:
                with open(
                    rp("worklog", "kb_audit_errors.log"),
                    "a",
                    encoding="utf-8",
                ) as fh:
                    fh.write(f"{session_id}/{mode}: {exc!r}\n")
            except Exception:
                pass


def _run_one_audit(audit: str, session_id: str) -> None:
    """跑单个审计脚本，结果写系统日志。契约差异在此适配层收口·不动脚本本体。"""
    log_dir = rp("worklog")
    os.makedirs(log_dir, exist_ok=True)
    env = dict(os.environ)
    env["HERMES_SESSION_ID"] = session_id
    stdin_data = None
    # 契约适配（接入层职责·守卫规范 §二·十四 接入不拥有）：
    #   · route_audit.py  吃 stdin {"transcript_path": ...}；Hermes 无 transcript 文件
    #     （只在 state.db）⇒ 借 _KB_ADAPTER 的 db→jsonl 导出喂路径（已实测打通·2026-10-01）。
    #   · 其余脚本（route_guard_audit / route_reconcile_report）走 HERMES_SESSION_ID env。
    if os.path.basename(audit) == "route_audit.py":
        if not os.path.isfile(_KB_ADAPTER):
            return                      # 无适配器 ⇒ 无 transcript ⇒ 静默跳过（不假红）
        try:
            import importlib.util as _ilu
            spec = _ilu.spec_from_file_location("_hermes_tx_adapter", _KB_ADAPTER)
            mod = _ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            tx = mod.export_transcript(session_id)
        except Exception:
            return
        if not tx:
            return                      # 本会话无消息（如空会话）⇒ 不记
        stdin_data = __import__("json").dumps({"transcript_path": tx})
    proc = subprocess.run(
        ["python3", audit, "--src", "hermes"] if stdin_data else ["python3", audit],
        env=env,
        cwd=os.path.dirname(audit),
        input=stdin_data,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out_path = os.path.join(log_dir, f"route_audit_{session_id}.log")
    tag = os.path.basename(audit)
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"## {tag} rc={proc.returncode}\n")
        if proc.stdout:
            fh.write(proc.stdout + "\n")
        if proc.stderr:
            fh.write("STDERR:\n" + proc.stderr + "\n")


def _on_session_end(session_id: str = "", **_: Any) -> None:
    """会话结束：跑路由审计 + 知识库审计，输出写入系统日志目录。"""
    if not session_id:
        return
    # ⚠️ 2026-10-01 修复：`next(...)` 只取第一个命中 ⇒ _AUDIT_SCRIPTS 里第二、三个
    #   （route_reconcile_report.py）**从未执行过**，列表形同虚设（守卫规范 §3.12 空转显形）。
    #   改为逐个跑·各自独立 try·单个失败不拖累其余。
    for name in _AUDIT_SCRIPTS:
        audit = _find_script(name)
        if audit is None:
            continue
        try:
            _run_one_audit(audit, session_id)
        except Exception as exc:  # 审计失败绝不影响会话本身
            try:
                with open(
                    rp("worklog", "route_audit_errors.log"),
                    "a",
                    encoding="utf-8",
                ) as fh:
                    fh.write(f"{session_id}/{name}: {exc!r}\n")
            except Exception:
                pass
    # 知识库审计（独立 try，路由审计失败不影响知识库审计）
    try:
        _run_kb_audit(session_id)
    except Exception as exc:
        try:
            with open(
                rp("worklog", "kb_audit_errors.log"),
                "a",
                encoding="utf-8",
            ) as fh:
                fh.write(f"{session_id}/dispatch: {exc!r}\n")
        except Exception:
            pass
    # 平台接入率漂移校验（跨工具中立·接入不拥有：仅调用公共脚本）
    # 与路由/知识库审计同形态：独立 try，失败放行不卡主流程；守 Hook 三纪律。
    try:
        if os.path.isfile(_PAC_SCRIPT):
            subprocess.run(
                ["python3", _PAC_SCRIPT, "--src", "hermes"],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 读文件证据检测（2026-08-22·检测"凭印象/凭摘要判断"漂移）
    # 与 _PAC_SCRIPT 同形态：独立 try，失败放行不卡主流程
    try:
        if os.path.isfile(_READ_EVIDENCE_SCRIPT):
            sessions_root = os.path.expanduser("~/.hermes/sessions")
            subprocess.run(
                ["python3", _READ_EVIDENCE_SCRIPT, "--dir", sessions_root,
                 "--session-id", session_id],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 自主进化误差量化信号层（跨工具中立·接入不拥有：仅调用公共脚本）
    try:
        if os.path.isfile(_EVO_SCRIPT):
            subprocess.run(
                ["python3", _EVO_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 语义路由自进化建议生成（跨工具中立·接入不拥有：仅调用公共脚本）
    try:
        if os.path.isfile(_RES_SCRIPT):
            subprocess.run(
                ["python3", _RES_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 自寻优引擎（跨工具中立·接入不拥有：仅调用公共脚本）
    try:
        if os.path.isfile(_SO_SCRIPT):
            subprocess.run(
                ["python3", _SO_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 面板数据快照积累器（跨工具中立·接入不拥有：仅调用公共脚本）
    try:
        if os.path.isfile(_PS_SCRIPT):
            subprocess.run(
                ["python3", _PS_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # 只读巡检类守卫（on_session_end 扩调·只告警不拦截）
    try:
        if os.path.isfile(_RULE3_SCRIPT):
            subprocess.run(
                ["python3", _RULE3_SCRIPT],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    try:
        if os.path.isfile(_CARDID_SCRIPT):
            subprocess.run(
                ["python3", _CARDID_SCRIPT, "hook"],
                capture_output=True,
                text=True,
                timeout=30,
            )
    except Exception:
        pass
    # ⛔ 已退役调用位·整块删除（2026-10-01 Hermes 端自治根治·守卫规范 §3.5「崩点静默」）
    #   历史：2026-08-24 曾以 for _mode,_label in (("format",…),("l3guard",…)) 双模式
    #   经 _KB_ADAPTER 调 reply_format_guard / l3_conclusion_guard。
    #   2026-09-12 撤 l3_conclusion 调用位时**只删了 for 头、留下整个循环体**⇒ _mode/_label
    #   成为未定义名 ⇒ 每轮 on_session_end 抛 NameError；except 分支自身又引用 _mode ⇒
    #   第二个 NameError 被内层 `except Exception: pass` 静默吞掉 ⇒ **守卫从未执行、
    #   零留痕、无告警**（与 doenglingz_level_declare_guard v1.0 空转同族）。
    #   退役依据：reply_format_guard 2026-08-26 作者令完全删除（格式警察永久禁止复活·
    #   守卫规范 §3.4·扩 呈现格式禁拦律）；l3_conclusion_guard 2026-09-12 作者令全端永久关闭。
    #   ⇒ 两个 mode 的被调对象均已不存在，保留调用位无意义且必崩 ⇒ 整块删，⛔勿重挂。
    #   若未来要做格式监督：正解在 SOUL 软约束 + hermes_plugin_health_guard 的死代码扫描，
    #   ⛔ 不得以「复活格式守卫」形式回流（守卫规范 §二·十八 第一问禁设核对）。


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)
