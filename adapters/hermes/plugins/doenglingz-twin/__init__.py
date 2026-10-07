"""童灵（Doenglingz）· Hermes 端接入插件 —— 端自主适配 · 零复制共脚本。

## 端定位（06-跨端适配规范 §2.2「各端按自己机制选最优路径」）

Hermes 端**不是无钩子端**。实盘依据（Hermes 源码，非文档推断）：
- `hermes_cli/plugins.py:109` `VALID_HOOKS` 含 `pre_llm_call` / `pre_tool_call` /
  `post_llm_call` / `on_session_end` / `on_session_start`。
- `agent/turn_context.py:754-777` `_collect_pre_llm_call_context()`：插件返回值注入
  **用户消息**（每轮）——等价 WB 的 `UserPromptSubmit`。
- `agent/turn_finalizer.py:454-463` `post_llm_call` 带 `assistant_response=final_response`
  （每轮 LLM 输出后）——等价 WB 的 `Stop`。
- `hermes_cli/plugins.py:998` `register_system_prompt_section(id, content, position="after_memory")`
  每新会话冻结进 system prompt——等价 WB 的 `USER.md` 恒驻注入。

⛔ **本文件不引用、不依赖、不写入任何他端目录**（`.trae-cn` / `.workbuddy` / `.qoder-cn` /
`.zcode` …）。台账落 `~/.hermes/doenglingz/`（端隔离），共脚本经
`DOENGLINGZ_CONFIG_DIR` 指向本端配置根。

## 三条装载通道（装载分态 · 内核不分端）

| 通道 | Hermes 机制 | 等价（WB） | 承载 |
|:--|:--|:--|:--|
| ① 恒驻核 | `register_system_prompt_section` | USER.md 常驻 | core_slice「运行时注入声明」段 + L6 |
| ② W1+W3 | `pre_llm_call` → 共脚本 | UserPromptSubmit | 上岗契约 + 域切片按需 |
| ③ 守护 | `post_llm_call` → 共脚本 | Stop 链 | 守护三查 + W1 兑现对账 |

## 纪律

- **零复制**：只 subprocess 调 `~/<记忆中心>/开发工具/doenglingz_*.py`，⛔不内联任何逻辑。
- **失败放行**：任何异常 → 返回空/None，⛔绝不阻断对话。
- **台账端隔离**：`DOENGLINGZ_CONFIG_DIR=~/.hermes/doenglingz`，⛔不写他端台账。
- **切片只读**：content 用 callable 运行时读 `slices/`，⛔不缓存不复制不手抄。
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

# ── 路径（全部为本端或平台无关真源，⛔无他端路径）──
_HOME = os.path.expanduser("~")
_DEVTOOLS = rp("devtools")
_INJECT = os.path.join(_DEVTOOLS, "doenglingz_inject_prompt.py")
_GUARD = os.path.join(_DEVTOOLS, "doenglingz_guard.py")
# ⛔ 用 _cand 不用 rp：slices/ 是**分身建好后才生成**的目录，
#    新用户刚装完时不存在是**正常态**——用 rp() 会抛 PathKeyMissing ⇒ 整插件挂。
_SLICES = _cand("twin_slices")
_CORE_SLICE = os.path.join(_SLICES, "core_slice.md")
_L6_SLICE = os.path.join(_SLICES, "L6_反向约束.md")

# 端标识：Hermes 端不共用任何 hooks.json（Trae 系才需要 --src auto），故固定具名。
_SRC = "hermes"

# 本端配置根（台账落点）——端隔离的关键：共脚本默认 ~/.workbuddy/，
# 本端必须覆盖，否则会把 Hermes 的注入/守护台账写进 WorkBuddy 目录。
# ⛔ 实测踩坑记录（2026-10-01）：共脚本两套 env 键并存且不对称——
#   · doenglingz_inject_prompt.py  读 DOENGLINGZ_CONFIG_DIR > WORKBUDDY_CONFIG_DIR > ~/.workbuddy
#   · doenglingz_guard.py          只读 WORKBUDDY_CONFIG_DIR（⛔不认 DOENGLINGZ_CONFIG_DIR）
# 只设 DOENGLINGZ_CONFIG_DIR 会让 inject 落本端、guard 仍落 ~/.workbuddy（实测污染已还原）。
# ⇒ 本端两个键都设成同一路径，跨共脚本版本也成立。
# ⛔ 诚实缺口：guard.py 的 INJECT_STATE / W1_WATERMARK 仍写死 ~/.workbuddy（不读 env），
#   故本端 W1 兑现对账（check_w1_honor）读不到本端台账 → 恒返回 None（放行，不误判）。
#   这是**共脚本全端缺陷**（非 Hermes 独有），已登记待作者裁决是否批共脚本修复。
_CONFIG_ROOT = os.path.join(_HOME, ".hermes", "doenglingz")

_ENV = dict(os.environ)
_ENV["DOENGLINGZ_CONFIG_DIR"] = _CONFIG_ROOT
_ENV["WORKBUDDY_CONFIG_DIR"] = _CONFIG_ROOT  # guard/level_declare 侧只认这个键
_ENV["PYTHONIOENCODING"] = "utf-8"

_TIMEOUT_INJECT = 25  # 秒；共脚本含规格书 hash 计算，超时即放弃本轮注入（fail-open）
_TIMEOUT_GUARD = 20
# 本会话 id（模块级顶部定义·⛔必须早于 _pre_llm_call 使用·否则 NameError）
# 由 pre_llm_call 首轮写入（Hermes 每轮派发带 session_id·实证 turn_finalizer.py:453-461）
_session_id = ""

# 恒驻段预算：register_system_prompt_section 的 max_chars 硬上限 4000
# （hermes_cli/plugins_dispatch.py:69-70 DEFAULT=MAX=4_000）。
# core_slice 全文 4344 字符 > 单段上限 ⇒ ⛔ 单段装不下，必须拆两段注册：
#   段① doenglingz.core = 「运行时注入声明」(head·1686) + L6(472) ≈ 2168
#        —— 先于一切裁决的最高判据（愿景/品格底色/三步/非职能域/零问题交付）
#   段② doenglingz.l1   = L1 身份骨架全段(2658)
#        —— 身份正名/意志归属/金句铁律/核心价值观/资源导向妥协/品格内核
# ⚠️ 2026-10-02 修复：此前单段注册且只取 head，把 L1 整段静默丢弃，
#    同时注释谎称「L1 已由 SOUL.md 承载」——实测 SOUL 里
#    Doenglingz/意志归属/金句铁律/核心价值观 四项全零命中（假绿·2026-08-20 误判同型）。
#    ⛔ 今后 SOUL/Skill 文档不得再声称「L1 已由 SOUL 承载」，除非 anchors 实测命中。
_SECTION_MAX_CHARS = 3800
_SECTION_MAX_CHARS_L1 = 3800


def _log(msg: str) -> None:
    """插件自留痕（端中立目录）。⛔ 不写系统日志（那是 Skill 通道的事，插件不越权）。"""
    try:
        os.makedirs(_CONFIG_ROOT, exist_ok=True)
        from datetime import datetime

        with open(os.path.join(_CONFIG_ROOT, "plugin.log"), "a", encoding="utf-8") as fh:
            fh.write("%s %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def _read(path: str, limit: int = 20000) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read(limit)
    except Exception:
        return ""


# ── ① 恒驻核（每新会话冻结进 system prompt）──

def _core_section(_session_info: Optional[Dict[str, Any]] = None) -> str:
    """运行时读 slices/ 拼恒驻段①。⛔ 不缓存（改切片下个会话即生效 = 天然新鲜）。

    段① = core_slice「运行时注入声明」段（首个 '\\n## ' 之前：愿景最高判据 + 品格底色
    + 三步思考 + 非职能域应答纪律 + 零问题交付红线）+ L6 反向约束。这是"先于一切裁决"的真源。
    L1 身份骨架走**独立段②**（见 _l1_section）——⛔ 不许再静默丢弃。
    """
    core = _read(_CORE_SLICE)
    if not core:
        return ""
    idx = core.find("\n## ")
    head = core[:idx] if idx > 0 else core
    l6 = _read(_L6_SLICE)
    body = head.rstrip()
    if l6:
        body += "\n\n---\n\n" + l6.strip()
    if len(body) > _SECTION_MAX_CHARS:
        body = body[:_SECTION_MAX_CHARS].rstrip() + "\n\n（本段已按 4000 字预算截断·完整内容见 slices/）"
    return body


def _l1_section(_session_info: Optional[Dict[str, Any]] = None) -> str:
    """恒驻段② = L1 身份骨架全段（首个 '\\n## ' 之后的全部内容）。

    ⚠️ 2026-10-02 新增。L1 是童灵硬约束（身份正名 / 意志归属 / 金句铁律 /
    实事求是态度 / 核心价值观 / 资源导向妥协 / 品格内核 10 条）——恒驻核丢它 =
    分身不知道自己是谁。⛔ 单段 4000 字上限装不下 core 全量，故拆段而非截断。
    """
    core = _read(_CORE_SLICE)
    if not core:
        return ""
    idx = core.find("\n## ")
    if idx <= 0:
        return ""  # 无 L1 段（切片结构变了）——⛔ 静默返回空，不伪造
    l1 = core[idx:].lstrip()
    if len(l1) > _SECTION_MAX_CHARS_L1:
        l1 = l1[:_SECTION_MAX_CHARS_L1].rstrip() + "\n\n（L1 段已按 4000 字预算截断·完整内容见 slices/core_slice.md）"
    return l1


# ── ② W1 上岗契约 + W3 域切片（每轮注入用户消息）──

def _pre_llm_call(user_message: Any = "", is_first_turn: bool = False,
                  session_id: str = "", **_: Any) -> Optional[Dict[str, str]]:
    """等价 UserPromptSubmit。返回 {"context": ...} 注入本轮用户消息。

    ⛔ 任何异常 → 返回 None（无注入），⛔绝不阻断对话。
    ⛔ 注入器自身崩了由共脚本内部 fail-open 兜底并降级告警（其 _crash_log 机制）。

    ⚠️ 2026-10-01 改用 **stdin 载荷**（原 argv `--prompt`）：为让注入台账带上
       `session_id`——`tsl_tree_hook`/`tsl_echo_hook` v1.2 的档位门控
       （`session_d_tier(sid)`）**靠 session_id 过滤台账**，本端此前传 argv
       ⇒ 注入器走 `prompt_argv` 分支 ⇒ `_PAYLOAD` 恒 `{}` ⇒ 台账 `session_id` 恒空
       ⇒ 门控退化成「全局最新行」＝**跨会话串台**（v1.2 明确要根除的那个病）。
       注入器 stdin 分支会 `_PAYLOAD = _parsed`（含 session_id）⇒ 正解。
       ⛔ 不改公共注入器本体（端适配层解决·守卫规范 §二·十四 接入不拥有）。
    """
    prompt = user_message if isinstance(user_message, str) else ""
    if not prompt.strip():
        return None
    global _session_id
    if session_id:
        _session_id = str(session_id)
    try:
        payload = json.dumps(
            {"prompt": prompt, "session_id": str(session_id or ""), "src": _SRC},
            ensure_ascii=False,
        )
        proc = subprocess.run(
            [sys.executable, _INJECT, "--src", _SRC, "--hook-protocol=text"],
            input=payload,
            capture_output=True, text=True, timeout=_TIMEOUT_INJECT, env=_ENV,
        )
        ctx = (proc.stdout or "").strip()
        # ── 件二：TSL 树强制回显（TSL 三件套之二）──────────────────────
        # 闭环末环：Stop 链机械产的树 ⇒ 本回合必须被逐行 relay ⇒ 写 .consumed。
        # ⛔ 核心意义：**我没法「不跑就说跑了」**——树是上一回合机制产的，
        #    stamp 在 stamps.log 可查；这直接封死 2026-10-01 那次手绘。
        try:
            # ── 2026-10-02 件二重构：调共脚本 tsl_echo_hook，⛔不再自研读树 ──
            # 病灶（本插件自研 `_read_tsl_tree` 无档位门槛）：它只判 stamp 有没有消费过，
            #   **不看本回合是不是 D3** ⇒ 非 D3 回合也会把上回合残留树注进对话。
            #   此前被 `tsl_tree_hook` 的 `os.remove(OUT)` 掩盖（残留树先被删，自研版就读不到），
            #   2026-10-02 删掉 os.remove 后掩盖物消失 ⇒ D1 回合收到 D3 的树，暴露。
            # 修法：**判据归共脚本**（守卫规范 §二·十四「接入不拥有」）。共脚本
            #   `tsl_echo_hook.main()` 自带 `session_d_tier(sid) != "D3"` 门槛 + stamp 幂等
            #   + 跨会话过滤，本插件**已定义 `_TSL_ECHO_HOOK` 但此前零调用**——改为真调用它。
            # 附带收益：⛔ 本插件不再需要 `_current_d_tier()`（曾复制共脚本判据·已随本次重构删除）。
            # ── 2026-10-02 撤销 echo 注入（用户两次报障后裁决·端适配层·不动共脚本）──
            # ⛔ 原 `_run_tsl_echo()` 把树注入**用户消息**，契约又要求 AI 在回复里逐行 relay
            #    ⇒ 同一棵树在用户视野里必然出现两次（消息一次 + 回复一次）。
            #    ⚠️ 这不是 bug，是跨端设计的固有结果：`.consumed` 防的是「同一 stamp 灌两次」，
            #    不是「树只能出现一次」。我此前把这两件事混了。
            # ✅ 裁决：**echo 通道在 Hermes 端停用**，树改为**只在 AI 回复里呈现一次**——
            #    · 只读停用点（_pre_llm_call 内），共脚本 `tsl_echo_hook.py` 本体零改动（跨端资产）
            #    · 树由 `tsl_tree_hook`（post_llm_call）产出到本端树槽，AI 从树槽读**原文**
            #      逐行 relay（08 §八第2腿：树由脚本产出，AI 只许逐行 relay，⛔ 不得改写/摘要/指针化）
            #    · `tsl_closeout_guard` v0.8 逐行比对回复与存档 ⇒ AI 省略/改写/换树当场留痕
            #    · ⛔ AI ⛔不主动跑 `tsl_verify.py` 产树（06 §1.6 v1.96）——树由 Stop 钩子产
            #    · 非 D3 回合不呈现（D3 门控改由 `doenglingz_level_declare_guard` 侧判据守住）
            tree = ""   # 故意留空：⛔ 端层停用，非遗漏
            if tree:    # pragma: no cover · 保留形态以便回滚
                ctx = (ctx + "\n\n" if ctx else "") + tree
        except Exception as exc:
            _log("tsl echo fail %r" % (exc,))
        if not ctx:
            _log("inject empty rc=%s stderr=%s" % (proc.returncode, (proc.stderr or "")[:120]))
            return None
        _log("inject ok len=%d" % len(ctx))
        return {"context": ctx}
    except Exception as exc:
        _log("inject fail %r" % (exc,))
        return None


# ── ③ 守护（等价 Stop：每轮 LLM 输出后）──

def _post_llm_call(assistant_response: Any = "", **_: Any) -> None:
    """等价 Stop 链。跑共脚本 doenglingz_guard.py --check。

    ⛔ 只观察不裁决（守护自限 · 02规范§五.3）：value/漂移类软信号不静默裁决。
    ⛔ 返回 None：不改写模型输出。
    """
    text = assistant_response if isinstance(assistant_response, str) else ""
    if not text.strip():
        return
    try:
        subprocess.run(
            [sys.executable, _GUARD, "--check", "--src", _SRC, "--text", text[:60000]],
            capture_output=True, text=True, timeout=_TIMEOUT_GUARD, env=_ENV,
        )
    except Exception as exc:
        _log("guard fail %r" % (exc,))
    # ── 本端 Stop 链的另外三件事（2026-10-01 接入·全部 ⛔只观察不裁决）──
    # ① 指针卡漂移对账（C-100 改动闭环律·愿景①全自动化）
    #    guard_index_pointer.py v1.1.0 生成的 GUARD_INDEX.md 若不跟着 manifest 更新
    #    ⇒ 卡静默过期 ⇒ AI 照过期卡找守卫。
    _check_guard_index_drift()
    # ② TSL 收尾守卫（TSL 三件套之三·⭐本回合接入的核心）
    #    ⚠️ 必须经适配层：共用件 `tsl_closeout_guard.py` 输入契约是 WB 形态的
    #    `{"transcript_path": ...}`，而 Hermes `post_llm_call` 派发参数里
    #    ⛔**没有 transcript_path**（实证：agent/turn_finalizer.py:453-461）。
    #    ⛔ 直接挂共用件 = 它走 `if not text: return 0` = **静默空过的摆设**。
    #    ⇒ 适配层 hermes_tsl_closeout_adapter.py：把钩子已持有的 assistant_response
    #       落成共用件读得懂的夹具（跑完即删·⛔不留 transcript 副本），判据仍归共用件。
    _run_tsl_closeout(assistant_response=text, session_id=_session_id)
    # ③ TSL 树机械产出（TSL 三件套之一·⭐把"AI手动跑"变"机制机械产"）
    #    ⛔ 只把树写到本端槽位（TSL_TREE_OUT 指本端目录·⛔绝不写 ~/.workbuddy）
    #    ⇒ AI 下一回合只多一条 relay 义务，⛔不替我编树。
    _run_tsl_tree_hook()

    # ⚠️ 独立分隔行（防上面任一挂载异常阻断后面）


# ── 指针卡漂移探针（模块级·节流）──────────────────────────────────────────
_GI = os.path.join(_DEVTOOLS, "guard_index_pointer.py")
_GI_STATE = os.path.join(_CONFIG_ROOT, "guard_index_drift_state.json")
_GI_INTERVAL = 1800   # 30 分钟节流·⛔ 每回合都读盘是浪费


def _check_guard_index_drift() -> None:
    """GUARD_INDEX.md 与 scripts_manifest.json 是否已漂移（Fail-Closed 只观察）。

    ⛔ 只写本端台账（~/.hermes/doenglingz/）·⛔ 不碰他端。
    ⛔ 探针缺失/超时/异常 → 静默放行（⛔ 不因辅助探针故障打断回合）。
    """
    try:
        import time
        state = {}
        if os.path.isfile(_GI_STATE):
            try:
                state = json.loads(open(_GI_STATE, encoding="utf-8").read())
            except Exception:
                state = {}
        last = float(state.get("ts") or 0)
        if (time.time() - last) < _GI_INTERVAL:
            return                      # 节流：⛔ 不每回合读盘
        if not os.path.isfile(_GI):
            return                      # 探针不在本端 → 不裁决
        r = subprocess.run([sys.executable, _GI, "--check"],
                           capture_output=True, text=True, timeout=20, env=_ENV)
        _write_state({"ts": time.time(), "rc": r.returncode,
                      "drift": r.returncode != 0,
                      "out": (r.stdout or "")[:400]})
        if r.returncode != 0:
            _log("GUARD_INDEX drift rc=%d（只观察·不裁决）" % r.returncode)
    except Exception as exc:
        _log("guard_index probe fail %r" % (exc,))


def _write_state(obj: dict) -> None:
    """写本端探针台账（原子写·⛔ 失败静默）。"""
    import tempfile
    try:
        os.makedirs(_CONFIG_ROOT, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=_CONFIG_ROOT, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _GI_STATE)
    except Exception:
        pass


# ── TSL 三件套·本端接线（2026-10-01 接入·⭐作者令）────────────────────────
# 设计纪律（承接既有三件）：
#   · **共用件本体一个字不改**（端中立判据·⛔不做端专属分叉）
#   · 端差异只落在「怎么把本端已有数据喂给它」这一层
#   · 三件全部 ⛔只观察不裁决：留痕、不改写模型输出、不阻断回合（02规范§五.3）
#   · ⛔ 端隔离：所有写入落 ~/.hermes/doenglingz/·⛔绝不写 ~/.workbuddy 或他端目录
_TSL_TREE_SLOT = os.path.join(_CONFIG_ROOT, "tsl_last_tree.md")
_TSL_ADAPTER = os.path.join(_DEVTOOLS, "hermes_tsl_closeout_adapter.py")
_TSL_TREE_HOOK = os.path.join(_DEVTOOLS, "tsl_tree_hook.py")
_TSL_ECHO_HOOK = os.path.join(_DEVTOOLS, "tsl_echo_hook.py")


def _tsl_env() -> dict:
    """本端 TSL 三件套的环境变量（⛔端隔离的关键：树槽/状态/台账全指本端）。"""
    env = dict(_ENV)
    env["TSL_TREE_OUT"] = _TSL_TREE_SLOT
    env["TSL_INJECT_STATE"] = os.path.join(_CONFIG_ROOT, "tsl_echo_state.json")
    return env


def _run_tsl_echo() -> str:
    """件二·调共脚本 `tsl_echo_hook` 取本回合该注入的树（⛔端中立判据不在本插件）。

    2026-10-02 取代自研 `_read_tsl_tree`：共脚本自带三道门槛（本回合 D3 / stamp 幂等 /
    跨会话 session 匹配），本插件重复实现会漏门槛（实证：D1 回合收到 D3 的树）。
    返回可直接拼进 additionalContext 的文本；不注入时返 ""。
    """
    if not os.path.isfile(_TSL_ECHO_HOOK):
        return ""
    try:
        r = subprocess.run(
            [sys.executable, _TSL_ECHO_HOOK],
            input=json.dumps({"session_id": _session_id, "prompt": ""}, ensure_ascii=False),
            capture_output=True, text=True, timeout=45, env=_tsl_env(),
        )
        out = json.loads((r.stdout or "").strip() or "{}")
        hso = out.get("hookSpecificOutput") or {}
        return hso.get("additionalContext") or ""
    except Exception as exc:
        _log("tsl_echo hook fail %r" % (exc,))
        return ""


def _run_tsl_closeout(assistant_response: str = "", session_id: str = "") -> None:
    """TSL 收尾守卫（件三）·经适配层跑共用判据。⛔ 异常静默放行。"""
    if not assistant_response.strip():
        return
    try:
        subprocess.run(
            [sys.executable, _TSL_ADAPTER],
            input=json.dumps({"assistant_response": assistant_response,
                              "session_id": session_id or "hermes"},
                             ensure_ascii=False),
            capture_output=True, text=True, timeout=45, env=_tsl_env(),
        )
    except Exception as exc:
        _log("tsl_closeout fail %r" % (exc,))


def _run_tsl_tree_hook() -> None:
    """TSL 树机械产出（件一）·把「AI手动跑」变「Stop 钩子机械产」。⛔ 异常静默。"""
    if not os.path.isfile(_TSL_TREE_HOOK):
        return
    try:
        subprocess.run(
            [sys.executable, _TSL_TREE_HOOK],
            input=json.dumps({"session_id": _session_id, "src": _SRC},
                             ensure_ascii=False),
            capture_output=True, text=True, timeout=60, env=_tsl_env(),
        )
    except Exception as exc:
        _log("tsl_tree_hook fail %r" % (exc,))


def register(ctx) -> None:
    ctx.register_system_prompt_section(
        "doenglingz.core", _core_section, position="after_memory", max_chars=_SECTION_MAX_CHARS,
    )
    # 段②（2026-10-02 新增）：L1 身份骨架。⛔ 不可省——省了=恒驻核丢分身身份（见常量区注释）
    ctx.register_system_prompt_section(
        "doenglingz.l1", _l1_section, position="after_memory", max_chars=_SECTION_MAX_CHARS_L1,
    )
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)