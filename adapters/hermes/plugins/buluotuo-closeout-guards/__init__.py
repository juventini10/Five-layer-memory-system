"""布洛陀收口守卫集群 · Hermes 端适配（post_llm_call 通道）。

## 存在理由（作者 2026-10-01 广授权「剩下的 28 项按愿景最优解处理」）

全量对账见系统日志：WorkBuddy 端 Stop 链 29 个 hook，Hermes 端此前零接入。
其中**收口族**是愿景①（全自动化·不依赖人记得）的机械载体——它们把"AI 应该
自觉做的事"变成"机制强制显形"：

| 守卫 | 机械化的"自觉" | 病根（脚本内记载） |
|:--|:--|:--|
| `doenglingz_level_declare_guard` | 档位声明义务 + **非 D3 回合不许产 TSL 树** | 2026-09-30 作者质证「我没启动童灵为什么还有 TSL」 |
| `triwich_closeout_guard` | 三明治收口（结论块 + 追问登记） | 2026-09-15 作者质询「三明治相关技术应该可以自动…」 |
| `tsl_closeout_guard` | 说了要 TSL 树就必须真跑 `tsl_verify.py` | 声明与执行脱钩 |
| `reply_tail_guard` | 回复不许留尾巴（有风险就解决） | 作者反复强调 |
| `systemlog_stophook_check` | 做了实质工作必须记系统日志 | 今日我已因漏记被作者当面纠正 |

⚠️ **前两项与本端直接相关**：Hermes 端 `doenglingz-twin` 每轮注入档位标签
（本会话开头注入的「童灵·D2 域模式」即其产物），但**此前无任何守卫校验它
是否被正确声明 / 是否越界产树** ⇒ 童灵 06 §1.6 的强制交代义务在 Hermes 端
**纯靠我自觉**。本集群把该义务机械化。

## 通道选择（Hermes 特性·⛔ 不照搬）

WB 的 Stop = 每轮 AI 输出后 ⇒ Hermes 对应 **`post_llm_call`**（每轮·带
`assistant_response`），⛔ 不用 `on_session_end`（会话级一天一次·不同档，
与上一轮 `buluotuo-stop-hook` 同一取舍逻辑）。

## 契约适配（三处·实测踩出）

守卫脚本吃 stdin JSON 且**多键 fallback 取文本**（`output`/`assistant_message`/…），
`session_id` 单独取。Hermes 端 kwargs 是 `assistant_response` + `session_id`
⇒ 适配层把两形态键都给（冗余无害·不同脚本读法不同）。

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：⛔ 恒返回 None·不改写模型输出·不阻断
- 失败放行：任何异常 → 静默 return
- 保守判定：⛔ 判据全在脚本本体·本插件零内联
- 端隔离：⛔ 不写他端台账（脚本自持 env 时由脚本负责·本插件不越权）
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional
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
except Exception:            # ⛔ 不静默：解析器不可达时留痕交守卫报
    rp = None

    def _cand(key, *parts):
        return None
# ── /BULUOTUO-PATH-PARAM ──────────────────────────────────────


__version__ = "v1.0.0"

_HOME = os.path.expanduser("~")
_DEVTOOLS = rp("devtools")
_LOG = os.path.join(_HOME, ".hermes", "closeout_guards_hook.log")

# 收口族五守卫（⛔ argv 按各脚本实测契约填·不猜）
_GUARDS = [
    ("doenglingz_level_declare_guard.py", []),      # 档位声明 + 非D3禁产树
    ("triwich_closeout_guard.py", ["--check"]),     # 三明治收口
    ("tsl_closeout_guard.py", []),                   # TSL 声明-执行对账
    ("reply_tail_guard.py", []),                    # 回复留尾巴对账
    # 回复冗余自查（2026-10-02·用户报障「必须根治·工程师+用户经理双角度」）
    # 检「具体事实在多条回复里重列 ≥2 次」⇒ 每轮重开证据表 = 同一 token 花两遍。
    # ⛔ 报告制不阻断（只留痕·让 AI 下轮自查，别等用户自己发现）
    ("reply_redundancy_guard.py", ["--limit", "12"]),
    ("systemlog_stophook_check.py", []),            # 系统日志收口
    # ② 2026-10-01 全端横切增量（作者「其他端做了有用的我们也要适配」）：
    #   `delivery_boundary_guard.py` **WorkBuddy/ZCode/QoderCN 三端齐挂**（共识度最高）
    #   —— 治「静默取舍」：回复含"排除/保留/未动/只改"却无"刻意/范围/待决"交代 → 告警。
    #   ⚠️ **第四类契约（实测）**：它**只认 `transcript_path` 并去读文件**
    #   （`last_assistant_text(transcript_path)` + `transcript_reader`），
    #   ⛔ **不收 stdin 里的文本** ⇒ 喂文本恒 rc=0 静默（第四种契约错位·前三种见下）。
    #   ✅ 处置：`--transcript` 通道在 _post_llm_call 里临时导出本轮文本到
    #      scratch jsonl 并传路径（复用已实测的 db→jsonl 适配器同族做法）。
    #   ⛔ 本端台账在脚本内写死 `开发工具/logs/`（跨端共享目录·共享台账非他端私有
    #      状态·与 ~/.hermes 端隔离台账不同性质·故不改造）。
    ("delivery_boundary_guard.py", ["Stop"], "transcript"),
    # ③ Qoder CN 端资产·跨端中立部分（去掉 qodercn_ 前缀的通用件）：
    ("registry_precheck_guard.py", []),       # 注册表前置校验
    ("stamp_precheck_guard.py", ["--check-time"]),  # 戳记时间前置校验
    ("report_backlog_guard.py", []),          # 报告积压守卫
    # ⛔ 2026-10-02 移除 `qodercn_inject_chain_guard.py`（**上轮接错了**）：
    #   复核源码 L307-308 硬编码扫 `~/.qoder-cn/projects/*/*.jsonl` ⇒ **Qoder CN 专属**。
    #   装在本端只会恒报「注入自检 24h 未跑」（它等的 `--record` 动作只有 QoderCN
    #   端会做）= 纯假红 + 每轮噪声。**病根**：上轮横切时只按脚本名含 "guard" 就接，
    #   ⛔ 没读源码确认数据面——与「真身待定位」同族：**凭名字判断 = 猜测**。
    #   ⇒ Hermes 端注入链自检改由 `hermes_inject_chain_guard.py` 承担（端专属·
    #      判据读本端真实事实源 ~/.hermes/doenglingz/*.json + buluotuo_inject_stats.json）。
    # ④ 2026-10-01 欠账清零轮（作者「没做完就按符合愿景最优解去做」）：
    #   `record_card_trigger.py` — **立场卡触发台账**。⚠️ 本端此前零覆盖，
    #   而 Hermes 端有 875 张立场卡且本轮就引用了 S974/S394/S772 等——
    #   **「我引用了卡」这个可观测事件却无台账**⇒ 岗1/蒸馏管道拿不到触发依据。
    #   契约：stdin `{"transcript_path": ...}`·走 transcript 通道（与 delivery_boundary 同类）。
    ("record_card_trigger.py", [], "transcript"),
]

_TIMEOUT = 30


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _env() -> Dict[str, str]:
    """端隔离 env：台账落本端 ⛔ 不写他端。

    ⚠️ 实测发现（2026-10-01）：`doenglingz_level_declare_guard.py:49` 读
    `WORKBUDDY_CONFIG_DIR` env（`os.environ.get("WORKBUDDY_CONFIG_DIR") or
    expanduser("~/.workbuddy")`）⇒ **不设则台账写进 WorkBuddy 目录**
    ——与本轮 crossend 守卫查出的 `doenglingz_guard.py` L117/L118 硬编码同族病，
    但这个守卫**是可 env 化的**（写法正确），只需端侧传键。
    同理设 `DOENGLINGZ_CONFIG_DIR` 覆盖另一批脚本的读法（两键并存不对称·对齐
    doenglingz-twin 插件已实证的处置）。
    """
    env = dict(os.environ)
    cfg = os.path.join(_HOME, ".hermes", "doenglingz")
    env["WORKBUDDY_CONFIG_DIR"] = cfg
    env["DOENGLINGZ_CONFIG_DIR"] = cfg
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _export_transcript(text: str) -> str:
    """把本轮文本导成 WB 格式 transcript jsonl·返回临时路径。

    `delivery_boundary_guard` 走 `transcript_reader.last_assistant_text(path)`
    ⇒ 必须给**文件路径**，且格式为 WB/Claude 系
    `{"role","message":{"content":[{"type":"text","text":...}]}}`。
    Hermes 无 transcript 文件（消息在 state.db）⇒ 适配层现造一份
    （格式与 `_hermes_transcript_adapter` 导出的**完全同构**·已实测该格式可用）。
    """
    import tempfile
    try:
        fd, path = tempfile.mkstemp(suffix=".jsonl", prefix="hermes_tx_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "role": "assistant",
                "message": {"content": [{"type": "text", "text": text}]},
            }, ensure_ascii=False) + "\n")
        return path
    except Exception:
        return ""


def _has_alarm(text: str) -> bool:
    """告警判定：⛔ 只认 alarm 的**真值**形态（`"alarm": true`）。

    ⚠️ 字面匹配 "alarm" 会把 `"alarm": false`（守卫明确报平安）也当告警
    ⇒ 永久噪声 ⇒ 告警疲劳（守卫规范 §3.5 明令防的正是这个）。
    """
    t = text.replace(" ", "")
    if '"alarm":true' in t or '"alarm":true,' in t:
        return True
    return any(m in text for m in ("⚠️", "❌", "违规", "ALARM"))


def _ledger_tail(cfg_dir: str, name: str) -> str:
    """读守卫自持台账末行（很多守卫恒 exit 0·告警只走台账·⛔ rc 看不见）。"""
    try:
        p = os.path.join(cfg_dir, name)
        if not os.path.isfile(p):
            return ""
        with open(p, encoding="utf-8") as fh:
            lines = [x for x in fh.read().splitlines() if x.strip()]
        return lines[-1][:300] if lines else ""
    except Exception:
        return ""


def _post_llm_call(assistant_response: Any = "", session_id: str = "",
                   **_: Any) -> None:
    """每轮 LLM 输出后跑收口族。⛔ 恒 None·只记录不拦截。"""
    text = assistant_response if isinstance(assistant_response, str) else ""
    if not text.strip():
        return None
    # 载荷双形态（脚本读法不一·冗余无害）
    payload = json.dumps({
        "response": text, "assistant_response": text,
        "output": text, "assistant_message": text,   # level_declare 的 KEYS 命中项
        "session_id": session_id, "transcript_path": "",
    }, ensure_ascii=False)
    cfg = os.path.join(_HOME, ".hermes", "doenglingz")
    for item in _GUARDS:
        # 条目形态：(脚本, argv) 或 (脚本, argv, 通道标记)
        script, extra = item[0], item[1]
        channel = item[2] if len(item) > 2 else "stdin"
        path = os.path.join(_DEVTOOLS, script)
        if not os.path.isfile(path):
            continue
        # transcript 通道：现造 WB 格式 transcript 并把路径塞进载荷
        run_payload, tx_path = payload, ""
        if channel == "transcript":
            tx_path = _export_transcript(text)
            if not tx_path:
                continue
            run_payload = json.dumps({"transcript_path": tx_path,
                                      "session_id": session_id,
                                      "payload": {"transcript_path": tx_path}},
                                     ensure_ascii=False)
        try:
            proc = subprocess.run(
                [sys.executable, path] + extra,
                input=run_payload, capture_output=True, text=True,
                timeout=_TIMEOUT, cwd=_DEVTOOLS, env=_env(),
            )
            # ⚠️ 关键契约（实测踩出·2026-10-01）：**多数收口守卫恒 exit 0**
            #   （守则"只记录不拦截"·`sys.exit(0)` 硬编码）⇒ 告警**只走自持台账**。
            #   只看 rc ⇒ 告警永远看不见 ⇒ 守卫形同虚设还报"通过"。
            #   ✅ 双通道：有输出就记（有输出必有信息），无输出则查台账末行。
            msg = (proc.stderr or proc.stdout or "").strip()[:200]
            # ⚠️ 自曝噪声（实测首跑 16 条里 12 条是噪声）：台账检查原本写在
            #   **循环体内** ⇒ 每个守卫都读同一份 declare_state.json，
            #   且只看 `"alarm" in tail` ⇒ 把 `alarm: false`（明确报平安）
            #   也记成告警。两错叠加 ⇒ 10 个守卫产出 12 条重复假告警。
            # ✅ 修正：① 台账检查**移出循环**（每轮一次·只属 level_declare）
            #        ② 只认真值形态（见 _has_alarm）
            if msg and _has_alarm(msg):
                _log(f"{script} out {msg}")
            elif proc.returncode != 0:
                _log(f"{script} rc={proc.returncode}")
        except Exception:
            # ⛔ 失败放行（不阻断·守卫失灵不该锁死对话）
            continue
        finally:
            if tx_path:
                try:
                    os.unlink(tx_path)      # 临时文件不留残（scratch 会清·先清更稳）
                except Exception:
                    pass

    # 台账通道（每轮一次·归属 doenglingz_level_declare_guard·⛔ 非逐守卫）
    # ⚠️ 台账文件名实测：`doenglingz_level_declare_guard.py` 落的是
    #   `doenglingz_level_declare_state.json`（⛔ 不是 declare_state.json·
    #   我第一版猜错 ⇒ 读不到内容 ⇒ 等于没接台账通道）。
    tail = (_ledger_tail(cfg, "doenglingz_level_declare_state.json")
            or _ledger_tail(cfg, "declare_state.json"))
    if tail and _has_alarm(tail):
        _log(f"level_declare ledger {tail}")
    return None


def register(ctx) -> None:
    ctx.register_hook("post_llm_call", _post_llm_call)