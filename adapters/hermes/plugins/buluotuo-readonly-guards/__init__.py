"""布洛陀只读巡检集群 · Hermes 端适配（on_session_end 通道）。

## 存在理由（作者 2026-10-01 广授权「剩下 28 项按愿景最优解处理」）

WorkBuddy Stop 链 29 个 hook 里有一批**纯只读巡检**——不依赖会话文本、
不依赖模型输出，只读文件系统/台账做一致性核验。它们的共同形态：

    python3 <脚本> [argv...]     # 无 stdin·exit 0/1·输出人读报告

这类脚本**零契约适配成本**（⛔ 不吃 stdin ⇒ Hermes kwargs 完全用不上），
只需在会话末尾按序跑一遍，把非零/告警汇进一处台账。

## 覆盖清单（12 项·对齐 WB Stop 链 + 各端专属资产）

| 脚本 | 机械化的"自觉" |
|:--|:--|
| `guard_registry_check.py --report` | 手工维护的名单漂移 |
| `guard_heartbeat_check.py --check` | 心跳源停摆嫌疑 |
| `design_family_guard.py` | 设计哲学 INDEX/看板漂移 |
| `manifest_registrar.py --apply --quiet` | 存量孤儿治理 |
| `post_change_guard.py --src hermes` | 改动后置检查 |
| `change_closedloop_guard.py` | 闭环四查（SSOT 同步 + 日志收口） |
| `change_reflux_guard.py --report` | 改触发件必回流 |
| `twin_changelog_guard.py --check` | 改了规格书却没记 CHANGELOG |
| `twin_verdict_ledger.py --check` | 分身裁决可观测 |
| `vision_gate.py --check` | 愿景判据被动显影 |
| `gate_runner.py --check` | 门禁注册表总闸 |

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：报告制恒 exit 0，⛔ 绝不阻断会话
- 失败放行：单个脚本异常 → 跳过继续下一个（⛔ 一个挂的不拖垮整批）
- 保守判定：⛔ 判据全在脚本本体·本插件零内联·不解析不改写脚本结论
- 降噪：⛔ 只在「非零退出」或「输出含告警标记」时留痕——全绿不写盘
  （否则每轮刷屏=告警疲劳·守卫规范 §3.5 明令防的正是这个）
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, List, Tuple
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
_DEVTOOLS = rp("devtools")
_LOG = os.path.join(_HOME, ".hermes", "readonly_guards_hook.log")

# 只读巡检族（脚本, argv）——⛔ 全部零 stdin 契约
_GUARDS: List[Tuple[str, List[str]]] = [
    ("guard_scan_domain_ssot.py", []),
    ("guard_registry_check.py", ["--report"]),
    ("guard_heartbeat_check.py", ["--check"]),
    ("design_family_guard.py", []),
    ("manifest_registrar.py", ["--apply", "--quiet"]),
    ("post_change_guard.py", ["--src", "hermes"]),
    ("change_closedloop_guard.py", []),
    # 🆕 2026-10-03 移出 change_reflux_guard（童灵·实测坐实·三重错配）：
    #   ① **契约违反**：本清单头明写「⛔ 全部零 stdin 契约」，而它在 main() L70
    #      调 `sys.stdin.read()`（等 PreToolUse payload）⇒ 无 stdin 环境永久阻塞
    #      （实测 8s / 45s / 280s 均未完·faulthandler 栈定位到 L70）。
    #   ② **通道错配**：它是 **PreToolUse 钩子**（要 tool_name+file_path 才判回流），
    #      on_session_end 根本不给这些字段 ⇒ 即使给了 stdin 也判不出任何东西。
    #   ③ **双重挂载**：`buluotuo-pretool-guards` 的 _GUARDS 已挂它（pre_tool_call
    #      面·适配层喂 stdin JSON）⇒ 这份是纯冗余，且是有害冗余（阻塞整批）。
    #   ⇒ 保留在 pretool 面；此处移除后本集群回到「零 stdin·零阻塞」契约。
    ("twin_changelog_guard.py", ["--check"]),
    # 🆕 2026-10-03 移出 twin_verdict_ledger / vision_gate / gate_runner（同族第2例）：
    #   三件都在 `get_text_from_stdin()`/`get_text()` 里读 `sys.stdin.buffer.read()`
    #   ⇒ on_session_end 不给 stdin ⇒ 永久阻塞（faulthandler 实测栈定位到
    #   L81 / L57 / L56）。⚠️ 我第一版扫描只查 `sys.stdin.read` ⛔ 漏了 `.buffer.read`
    #   ⇒ 首版「零风险」是**假绿**——判据的搜索面必须覆盖实现变体。
    #   ⇒ gate_runner 的零问题门禁改由 launchd 面承担（它是 cron 型·不是每轮型）。
    # Hermes 端专属注入链守卫（2026-10-02·替代误接的 qodercn 版）
    # 四检查：twin 在册 / 三通道声明 / 台账新鲜度+d_tier / **session_id 落库率**
    #   （最后一条是本端特有真缺陷的机械监控：插件走 argv 致 session_id 恒空
    #     ⇒ TSL 门控退化为全局最新行=跨会话串台）
    ("hermes_inject_chain_guard.py", ["--check"]),
    # 回复冗余守卫（2026-10-02·用户两次报障「回复重复、看不清、浪费 token」）
    # 检出两类自我复述：①模板词密度超阈值（⛔/判据/根因/实证…反复套）
    # ②同一会话内长段落重复 ≥2 次（最硬指纹）
    # ⛔ 报告制不阻断；⚠️ 它只能测「我的输出」·⛔ 测不到 SOUL/Skill 契约强制的
    #    固定模板尾巴（triwich 的「结论位置锁」等·属 SSOT 强制·不可删）
    ("reply_redundancy_guard.py", ["--limit", "20"]),
    # 五系统文件 100% 适配守卫（2026-10-02·用户要求「必须 100%·不是有增有减」）
    # 语义级逐条比对：清单 101 条 × Hermes 真实加载面（SOUL+USER+MEMORY+童灵两段恒驻）
    # rc=0 ⇔ GAP=0 ⇔ 真 100%。⚠️ 复现插件两段拼接逻辑·⛔ 简化读取=制造假绿
    # devtools 脚本解析守卫（2026-10-03·根治轮）
    # 病根：runtime_paths.devtools 指向目录曾缺 91 件脚本（含注入器）⇒ pre_llm_call
    #   每轮 fail-open（plugin.log `inject empty rc=2` 连报 21 次/10h01m）⇒ 档位判据
    #   消失 ⇒ AI 自己顶位宣布 D3（机制坏了·行为看着仍合规）
    # 判据：devtools 目录存在 + 插件引用脚本全可达 + 注入器可执行（最小实跑出档位块）
    ("devtools_script_resolve_guard.py", []),
    # 验证器保真度守卫（2026-10-03·用户「第一性原理根治」）
    # 治「验证器验证的不是运行的那份」——d_tier/w1 回归器原 TARGET 硬编码 开发工具/，
    #   而 runtime_paths.devtools=脚本中心/，两份 sha 不同 ⇒ 回归器报全绿与运行态零关联
    # 三判据：路径保真（TARGET 解析自 runtime_paths）/ 内容保真（sha 对账）/ 断言覆盖
    ("verifier_target_fidelity_guard.py", []),
    # devtools 单一真相源守卫（2026-10-03·用户「落实到位」）
    # 治「两处都有时哪处是真身」：① 功能完整性（对方独有函数更多 ⇒ 真相源是降级副本）
    #   ② 路径字面量（sed 把路径改成绝对路径·08-03 事故）③ 裸 ~/ 赋值（expanduser 包裹缺失）
    ("devtools_single_source_guard.py", []),
    ("hermes_wb_parity_check.py", ["--quiet", "--ledger",
                                   os.path.expanduser("~/.hermes/hermes_wb_parity_ledger.jsonl")]),
    # ⚠️ v3.2 端中立化后才对本端有信息量（此前查的是 ~/.workbuddy 的心跳·假绿/假红）
    #   ⚠️ 属「只读巡检」而非本集群的 post_llm_call 收口族·通道同 on_session_end
    # ── 🆕 2026-10-03 补挂三件（自纠「建了≠在跑」=HE-007 族·建完必须接进运行链）──
    # 恒驻核预算守卫：官方 register_system_prompt_section **超总预算会静默跳过**
    #   （只记一条 warning·不报错不阻断）⇒ 恒驻段无声消失而盘上一片正常、插件仍 enabled。
    #   本端实测 7600/8000=95%·余量仅 400 字符 ⇒ 第三个插件想注册一段就会被吃掉。
    ("hermes_core_budget_guard.py", []),
    # 会话层异常守卫：db 缺失/不可打开/恒驻核切片失踪/注入台账不更新 ⇒ 🔴。
    #   与 hermes_inject_chain_guard 第④腿部分重叠·本件是独立单文件检查器（⛔ 不互相顶账）。
    ("hermes_session_anomaly_guard.py", []),
    # 复用检查：起手写新守卫前先查同名/同族实现（治 HE-009「重复造轮子」）。
    # ⚠️ 参数是 `--all`（它无 `--check`；传错参 rc=2·2026-10-03 挂载时当场抓到）
    ("reuse_check.sh", ["--all"]),
]

# ⛔ 刻意排除 `guard_doc_consistency.py`（2026-10-01 实测后剔）：
#   它以**各端 settings.json 为挂载真相源**（`--settings` / 内建
#   `~/.workbuddy/settings.json` 等），而 Hermes 端的挂载真相源是
#   **config.yaml 的 plugins.enabled**（无 settings.json 结构）⇒ 结构性地
#   读不到 Hermes 挂载态，跑它只产 `settings 不存在` 噪声。
#   它承担的职责「实挂但未登记反查」在 Hermes 端由
#   `hermes_plugin_health_guard.py` 承担（配置面↔声明面↔注册面对账·已实装）。
#   ⇒ 能力不丢，只是换了更贴 Hermes 实现的载体。
#
# ⛔ 刻意排除 TSL 三件套（tsl_tree_hook / tsl_echo_hook / tsl_tree）：
#   ① 童灵 06 §1.6 规定 **D1/D2 档无 TSL 树义务**，本轮档位=D2；
#   ② `tsl_tree_hook` 硬编码写 `~/.workbuddy/tsl_last_tree.md`
#      ⇒ 直接接＝制造本轮 crossend 守卫刚修掉的同族跨端污染。
#   ⇒ 接入前须先裁决「Hermes 端 D3 上岗时树的落点」，属设计决策不由适配层擅自定。
#
# ⛔ 刻意排除 `registry_guards.sh`（WB 私有 ~/.workbuddy/hooks/ 目录·Hermes 无对应物）
# ⛔ 刻意排除 `record_card_trigger.py` / `position3_notify.py`（真身不在开发工具/·待定位）
# ⛔ 刻意排除 `session_tail_inject.py`（依赖 WorkBuddy 的 session_tail 缓存结构·Hermes 无）

_TIMEOUT = 45
# 告警标记（输出含其一才算有话可说·⛔ 不做语义解析）
# ⚠️ 自曝假阳性（实测首跑 10 条里 4 条是噪声）：多个守卫输出 JSON 含
#   `"alarm": false` —— 字面匹配 "alarm" 会把**明确报平安**的行当告警
#   ⇒ 永久噪声 ⇒ 告警疲劳。修正：alarm 须匹配 `true`/`true,` 形态，
#   ⛔ 不匹配 `"alarm": false`。
_ALARM_MARKS = ("⚠️", "❌", "RED", "缺", "漂", "未记", "不一致", "FAIL")
_ALARM_TRUE = ("alarm\": true", "alarm\":true", '"alarm": true', "alarm=true")


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _on_session_end(session_id: str = "", **_: Any) -> None:
    """跑只读巡检族。报告制恒 exit 0。"""
    if os.environ.get("HERMES_READONLY_GUARDS") == "0":
        return None                      # 逃生阀：调试时可关
    env = dict(os.environ)
    cfg = os.path.join(_HOME, ".hermes", "doenglingz")
    env["WORKBUDDY_CONFIG_DIR"] = cfg   # 端隔离：⛔ 台账不落他端
    env["DOENGLINGZ_CONFIG_DIR"] = cfg
    # ⚠️ 2026-10-01 端中立化后本守卫才真正对本端生效：
    #   `guard_heartbeat_check.py` v1.0-v3.1 硬编码 `~/.workbuddy/` ⇒ Hermes 端
    #   装上也只能查 WB 的心跳目录（报的是别端状态·对本端零信息量）。
    #   v3.2 已加三段配置根 env（GUARD_HEARTBEAT_ROOT > WORKBUDDY_CONFIG_DIR >
    #   ~/.workbuddy·⛔ 不设 env 时与 v3.1 行为完全一致⇒ WB 端零影响）⇒
    #   本端只需设 GUARD_HEARTBEAT_ROOT 即可复用公共本体（⛔ 不 fork）。
    env["GUARD_HEARTBEAT_ROOT"] = os.path.join(_HOME, ".hermes")
    # 注册清单真相源：Hermes 无 settings.json ⇒ 指向**机械派生**的 hooks_registry.json
    # （由 hermes_plugin_health_guard.export_hooks_registry() 每次从
    #   config.yaml plugins.enabled + plugins/*/__init__.py 重算·⛔ 非手写防漂移）
    # ⚠️ 诚实边界：公共守卫的 hook 腿对 Hermes 端**只能核到「名册」**——
    #   插件不是脚本（无 .py 可执行体·command 字段是 `hermes-plugin:<name>` 形态）
    #   ⇒ 它报的 script_missing 是「名册里没实体脚本」而非「本端钩子没跑」。
    #   **派发态由 hermes_plugin_health_guard 的 check_dispatch_heartbeat 独立判**
    #   （读 ~/.hermes/*.log|*.json 真实运行态产物）——两条腿互补·⛔ 不互相顶账。
    env["GUARD_HEARTBEAT_SETTINGS"] = os.path.join(_HOME, ".hermes",
                                                   "hooks_registry.json")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    for script, extra in _GUARDS:
        path = os.path.join(_DEVTOOLS, script)
        if not os.path.isfile(path):
            continue                      # 脚本不存在 → 静默跳过（不假红）
        try:
            proc = subprocess.run(
                [sys.executable, path] + extra,
                capture_output=True, text=True, timeout=_TIMEOUT,
                cwd=_DEVTOOLS, env=env,
            )
        except Exception:
            continue                      # ⛔ 单个失败不拖累整批
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        if proc.returncode != 0:
            _log(f"{script} rc={proc.returncode} :: {out[:220]}")
        else:
            hit = any(m in out for m in _ALARM_MARKS) or any(
                a in out for a in _ALARM_TRUE)
            if hit:
                first = next((l for l in out.splitlines()
                              if any(m in l for m in _ALARM_MARKS)
                              or any(a in l for a in _ALARM_TRUE)), out[:120])
                _log(f"{script} warn :: {first.strip()[:220]}")
    return None


def register(ctx) -> None:
    ctx.register_hook("on_session_end", _on_session_end)