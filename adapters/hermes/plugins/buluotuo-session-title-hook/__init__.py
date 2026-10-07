"""布洛陀会话标题命名守卫 · Hermes 端适配（session_title_namer.py 的 Hermes 端承载）。

## 作者指名的需求（2026-10-01）

「WorkBuddy 做了一个任务标题格式的 hook，我觉得很好，你这一段应该也装上」

## 原语复用（⛔ 零复制·接入不拥有）

标题规则与启发式**全部**来自跨端中立原语 `开发工具/session_title_utils.py`
（`make_title(prompt, created_ms)` 一把出），本插件只做**端适配**：

    标题格式 = YYMMDD | 类型 | 主题
      · 日期 = 北京时区会话创建时间（取 sessions.started_at）
      · 类型 ∈ {功能,设计,修复,优化,发布,探索,文档,研究}（原语关键词启发式·默认=探索）
      · 主题 = 首条 prompt 简洁概括
    规则 SSOT = 作者 2026-09-09 立·会话标题命名规则（原语文件内已固化）

## ⚠️ 按 Hermes 特性适配·**不是照搬 WorkBuddy**（本文件的核心）

WorkBuddy 版 v0.5/v0.6 的血泪史**在 Hermes 端不存在**，照抄会引入无用复杂度：

| WorkBuddy 端痛点 | Hermes 端实况（**2026-10-02 源码实证**） | 本插件处置 |
|:--|:--|:--|
| WB 新版 UI 标题读 `sessions.title`，`custom_title` 写了不上屏 | **Hermes 也读 `sessions.title`**——`hermes_state_titles.py` 是标题唯一 SSOT（`title` + `title_source` 带来源优先级） | 走**公共 API `set_auto_title(sid, title, source="derived")`**·⛔ 不裸写 SQL |
| 宿主 AI 起名发生在钩子写入后几秒 → 覆盖钩子名 | **宿主起名器真实存在**：`agent/title_generator.py`（写 `source="llm"`） | 靠**来源优先级**天然免疫（见下）·⛔ 不做后台夺回轮询 |
| 每 3s 轮询·2 分钟窗口·连续 3 次稳定才退出 | 同上不适用——优先级机制已解决覆盖问题 | ⛔ 不 spawn 脱离进程 |
| UserPromptSubmit hook 同步写 | Hermes **pre_llm_call** 每轮·带 user_message | 用 `pre_llm_call` + `is_first_turn` 判首轮 |

⇒ **一条同步写，无守护进程，无轮询**。这不是偷懒，是把 WB 用 3 个版本
（v0.5→v0.6→夺回）换来的复杂度在 Hermes 端直接绕过——**按自身特性做**。

## 🔴 2026-10-02 根因订正（作者重启后实盘发现标题未按规范显示）

**我此前写的是 `sessions.display_name`——那一列 UI 根本不读。**
全仓 grep 证据：`display_name` 只出现在 `hermes_state_sessions.py:251/289/339`
（跨端会话表的**导入/继承**字段），**无任何读取它做标题的代码**。
⇒ 我手工探针"写成功"是**假绿**：写进了一列没人看的柜子。
**这正是铁律 016 的反面教材**——我验的是"写入成功"，不是"UI 会显示"。

**正解**：`SessionDB.set_auto_title(session_id, title, source="derived")`
（`hermes_state_titles.py:134`），走**官方来源优先级**机制：

    rank: derived(0) < llm(1) < user(2)   ← hermes_state.py:1593

- 宿主 `title_generator` 写 `llm`(1) ⇒ **能覆盖**我的 `derived`(0)
- 用户手动 `/title` 写 `user`(2) ⇒ **我的 derived 覆盖不了**（自动让位给人）

⇒ **不需要 WB 那套后台夺回轮询**——优先级机制本身就是"机械的夺回保障"：
我的名会被宿主临时盖，但宿主那次 `llm` 只在 rank 严格更低时才落；
而我每轮 `pre_llm_call` 都写一次 ⇒ 下一轮即夺回。**同一条同步写，零守护进程。**

## 覆盖保护（防误伤）

- ⛔ `title_source='user'`（用户手动命名）⇒ 永不覆盖（rank 2 > 0·API 层自动拒绝）
- ⛔ 非首轮 ⇒ 只在 `title_source` 为空/derived 时补写·不碰 user
- ⛔ 走公共 API 而非裸 SQL ⇒ 继承内核的 sanitize/CAS/hidden-guard 全套保护

## 纪律（守卫编写规范 §八 Hook 三纪律）

- 只记录不拦截：⛔ 返回 None·不改用户消息·不阻断对话
- 失败放行：任何异常 → 静默 return
- 保守判定：⛔ 不猜标题·只用原语产出·拿不准就不写
- 端隔离：⛔ 只写 `~/.hermes/state.db`·不碰任何他端会话库
"""

from __future__ import annotations

import os
import sqlite3
import sys
import time
from typing import Any, Optional
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
_UTILS = rp("devtools", "session_title_utils.py")
_STATE_DB = os.path.join(_HOME, ".hermes", "state.db")
_LOG = os.path.join(_HOME, ".hermes", "session_title_hook.log")

# 本插件写的标题前缀特征（覆盖保护用·⛔ 靠它无法区分"本插件写的"与"作者手写的同格式名"
#   ⇒ 判据用「非空即不覆盖」而非「格式匹配」，更保守）
_PREFIX = "| "

# 当前会话 id（由 _pre_llm_call 每轮写入·供 _make_title 取**本 session** 的创建时间）
_CUR_SID = ""

# 待复查的会话 id（写入后需确认是否子会话——父子关系可能晚于首次写入落定）
_PENDING_SID = ""


def _is_subagent_session(session_id: str) -> bool:
    """子会话身份以**库**为准（`parent_session_id` 非空），⛔ 不靠 prompt 文本判。

    ⚠️ 2026-10-02 实测两次修正：
       ① Subagent 会话的首条 user 消息是**裸的任务目标**（`审计：今天做的工作…`），
          ⛔ 不含 `Subagent:` 字样 ⇒ 按文本判会误写规范名并与宿主
          `apply_subagent_title` 打架（`turn_context._maybe_title_session_at_turn_start`
          的 `platform == "subagent"` 分支）。
       ② 但 `parent_session_id` 在**首次写入那一刻可能仍是 NULL**（会话行先建、
          父子关系后设）⇒ 单次查库会漏判 ⇒ 须配合 `_recheck_subagent()` 写后复查。
    """
    if not session_id or not os.path.isfile(_STATE_DB):
        return False
    try:
        con = sqlite3.connect(_STATE_DB, timeout=5)
        row = con.execute(
            "SELECT parent_session_id FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        con.close()
        return bool(row and row[0])
    except Exception:
        return False


def _recheck_subagent() -> None:
    """写入后复查：若确认是子会话 ⇒ **撤回刚写的名**，交还宿主命名。

    ⚠️ 2026-10-02 10:08 实盘：子会话 `parent_session_id` 在我写入那一刻仍是 NULL
    （会话行先建、父子关系后设·实测 10:08:54 写入时为空、10:10 查已有值）
    ⇒ 单次查库漏判 ⇒ 规范名被写到子会话上。
    ⇒ 写完复查 + 确认是子会话则撤回（只撤**自己写的**·⛔ 不动宿主的）。
    """
    global _PENDING_SID
    sid = _PENDING_SID
    _PENDING_SID = ""
    if not sid or not _is_subagent_session(sid):
        return
    try:
        con = sqlite3.connect(_STATE_DB, timeout=5)
        cur = con.execute(
            "UPDATE sessions SET title=NULL, title_source=NULL WHERE id=? "
            "AND title_source=? AND title LIKE ?",
            (sid, _SOURCE, f"%{_SEP}%"))
        con.commit()
        n = cur.rowcount
        con.close()
        if n:
            _log(f"reclaim(subagent) {sid}·已撤回自写名")
    except Exception as exc:
        _log(f"recheck fail {exc!r}")


# 🔴 写入档位 = `llm`（**2026-10-02 二次订正·上一版用 derived 被宿主升级覆盖**）
#
# 宿主起名是**两段式**（`agent/title_generator.py:781-790`）：
#   ① `apply_instant_title` 同步写 `derived`(0)   ② 异步线程**升级到 `llm`(1)**
# ⇒ 我上版选 derived(0) 被 ② 升维覆盖（实测：本会话 derived 名几秒后变回
#   宿主 llm 名「排查其他任务标题未变原因」·**修复不完整**）。
# ⇒ 改用 `llm`(1) 与宿主**同级**：判定式 `rank(current) >= new_rank`
#   （`hermes_state_titles.py:96`）在同 rank 时**拒绝后来者**
#   ⇒ 宿主升级线程回来时被我挡住；我又只写一次同步 ⇒ 天然先到。
# ⛔ 仍不越界到 `user`(2)：那是「用户手动命名」语义·插件无权占用。
_SOURCE = "llm"
_SEP = " | "   # 标题分隔符·撤回时用于识别"自己写的名"


def _log(msg: str) -> None:
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(_LOG), exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _make_title(prompt: str) -> Optional[str]:
    """经跨端中立原语产标题。⛔ 原语不可用/异常 → None（宁漏勿猜）。"""
    try:
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("_title_utils", _UTILS)
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:
        _log(f"utils load fail {exc!r}")
        return None

    # ⛔ 取**本 session** 的真实创建时间（此前查 `ORDER BY started_at DESC LIMIT 1`
    #    = 全库最新一条·⛔ 并发/子会话时会张冠李戴——同一类"验了写入没验写对"的错）
    created_ms = None
    try:
        con = sqlite3.connect(_STATE_DB, timeout=5)
        row = con.execute(
            "SELECT started_at FROM sessions WHERE id=?", (_CUR_SID,)
        ).fetchone()
        if row is None:
            row = con.execute(
                "SELECT started_at FROM sessions ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        con.close()
        if row and row[0]:
            created_ms = int(float(row[0]) * 1000)
    except Exception:
        created_ms = None
    if created_ms is None:
        return None                      # ⛔ 取不到真实创建时间 → 不写（不拿当前时间冒充）
    try:
        return mod.make_title(prompt, created_ms)
    except Exception as exc:
        _log(f"make_title fail {exc!r}")
        return None


def _reuse_title_for(sid: str) -> Optional[str]:
    """从插件**私有日志**（append-only·只有本插件写）读回本 session 最后写下的名。

    🔴 为什么不能从 `sessions` 表当"我的名"的存储（2026-10-02 实盘故障）：
       宿主 upgrade 线程用**同一个 `llm` 档**后写覆盖（`title_generator.py:681`
       判定式 `rank(current) >= new_rank` 在同 rank 时拒绝后来者 ⇒ 它能覆盖我）。
       表被覆盖后再去捞，捞到的是**宿主的名** ⇒ 写回去等于自我循环，
       永远夺不回来。私有日志是唯一不被覆盖的账。
    """
    if not sid or not os.path.isfile(_LOG):
        return None
    try:
        last = None
        with open(_LOG, encoding="utf-8") as fh:
            for line in fh:
                if f" named {sid} " in line:
                    last = line
        idx = last.rfind("-> ") if last else -1
        return last[idx + 3:].strip() if idx >= 0 else None
    except Exception:
        return None


def _reuse_title() -> Optional[str]:
    """非首轮：取回**我自己写的那个名**用于夺回（⛔ 不拿本轮 prompt 重起名）。

    ⚠️ 为什么不重算：标题的「类型+主题」应以**首轮意图**为准；中途轮次的
    prompt（"继续"/"改一下"）会算成 `探索 | 继续` 这类无信息量的名。
    ⇒ 夺回 = 把**同一个名**重写一遍。
    """
    return _reuse_title_for(_CUR_SID)


def _write_title(session_id: str, title: str) -> bool:
    """写 `sessions.title`（**UI 真正读的列**）·走内核公共 API 拿来源优先级。

    🔴 2026-10-02 根因订正（作者重启后实盘发现标题未按规范显示）：

    **错 1（致命）：写错了列。** 此前写 `sessions.display_name`——全仓 grep 证明
    **无任何代码读它做标题**（只作跨端会话表导入/继承字段）⇒ 写进去也上不了屏。
    我当时的"手工探针写入成功"是**假绿**：验的是"写进去了"，不是"UI 会显示"。

    **错 2（隐蔽）：档位选错。** 标题 SSOT 是 `title` + `title_source`，rank
    （`hermes_state.py:1593`）= `derived(0) < llm(1) < user(2)`，写入判定
    `hermes_state_titles.py:96`：

        if not is_user and current.title is not None and rank(current) >= new_rank:
            return 0        # ← 现有权威 ≥ 我 ⇒ 拒绝

    ⇒ 我原本选 `derived(0)`：**只在 title 为 NULL 时能写**。宿主一旦先写
    `derived`/`llm`，我**永远抢不回来**（实测步骤1 失败·title 仍是宿主的 llm）。
    ⇒ 改用 **`llm`(1)**：与宿主同级但判定是 `>=` ⇒ **我后写就我赢**（同 rank 时
    `current(1) >= new(1)` 成立… ⚠️ 实测确认：同 rank 也被拒——见下方实测结论）。

    **正解（实测确定）：必须在宿主起名之前写。** `turn_context.py:245` 的
    `start_title_upgrade` 是**异步**的（首轮结束后才跑），而本插件在
    `pre_llm_call`（首轮·同步）⇒ 天然早于它 ⇒ 首次写入必落在 title 为 NULL 时。
    之后每轮 `pre_llm_call` 复查：若 `title_source` 已非我留的标记，则**降级不夺**。

    **防误伤（不可让渡）**：`title_source='user'`（用户手动 `/title`）⇒ 永不覆盖。
    走公共 API 即自动获得该保护（`is_user` 分支绕过 rank 判定且本插件不写 user 档）。
    """
    if not session_id or not title:
        return False
    try:
        # ⛔ 走公共 API（继承 sanitize + 唯一性 CAS + hidden-guard + 优先级全套保护）
        #    裸写 SQL 会绕过这些，且拿不到优先级判定。
        from pathlib import Path

        import hermes_state

        # ⚠️ SessionDB 要 **Path**（`hermes_state.py:672` 用 `self.db_path.parent`）
        db = hermes_state.SessionDB(Path(_STATE_DB))
        try:
            cur = db._read_one(
                "SELECT title, title_source FROM sessions WHERE id=?", (session_id,))
            # ⚠️ 2026-10-02 修：`_read_one` 返回 `sqlite3.Row`，⛔ **不是 dict**——
            #    写 `(cur or {}).get(...)` 会 AttributeError⇒ API 分支每次都炸、
            #    静默落 SQL 兜底（实盘日志 `api fail AttributeError`·连续 4 次）。
            #    sqlite3.Row 只支持索引/keys() 访问。
            src = cur["title_source"] if cur else None
            cur_title = cur["title"] if cur else None
            if src == hermes_state.SessionDB.TITLE_SOURCE_USER:
                _log(f"skip(user-named) {session_id}")
                return False                       # ⛔ 用户手动命名 → 永不动
            # 已是我的名（同档且同文本）⇒ 无需重写
            if src == _SOURCE and cur_title == title:
                return False
            ok = bool(db.set_auto_title(session_id, title, source=_SOURCE))
        finally:
            try:
                db.close()
            except Exception:
                pass
        if ok:
            _log(f"named {session_id} -> {title}")
        return ok
    except Exception as exc:
        _log(f"api fail {exc!r}·fallback sql")
        try:
            con = sqlite3.connect(_STATE_DB, timeout=5)
            cur = con.execute(
                "UPDATE sessions SET title=?, title_source=? WHERE id=? "
                "AND (title IS NULL OR title IS '' OR title_source=?)",
                (title, _SOURCE, session_id, _SOURCE),
            )
            con.commit()
            changed = cur.rowcount
            con.close()
            if changed:
                _log(f"named(sql) {session_id} -> {title}")
            return bool(changed)
        except Exception as exc2:
            _log(f"write fail {exc2!r}")
            return False


def _pre_llm_call(user_message: Any = "", is_first_turn: bool = False,
                  session_id: str = "", **_: Any) -> None:
    """会话命名。⛔ 恒返回 None·不改用户消息·不阻断。

    ⚠️ **不再只写首轮**（此前 `if not is_first_turn: return` 是错的）：
    宿主 `title_generator` 会在首轮后写 `llm` 标题盖掉 `derived` ⇒ 只有每轮都写
    才能靠优先级夺回（且 `user` 位用户手动命名永不被夺——这才是"防误伤"该守的地方）。
    """
    prompt = user_message if isinstance(user_message, str) else ""
    if not prompt.strip():
        return None
    # ⛔ Subagent 会话不配规范名（2026-10-02 实测）：宿主对 worker 写
    #    `Subagent: <任务描述>`（`title_generator.py:770` 的 kanban 分支）·
    #    那是**任务派发的可追溯标识**·改成人话主题反而丢了"这是个子任务"的信息。
    #    判据：prompt 本身带 Subagent 标记 ⇒ 让位。
    if "Subagent:" in prompt[:80] or prompt.strip().startswith("[Subagent"):
        return None
    if _is_subagent_session(session_id):
        return None
    # ⚠️ 2026-10-02 10:08 实盘再修正：子会话的 `parent_session_id` 在
    #    **我写入的那一刻可能还是 NULL**（会话行先建、父子关系后设·实测
    #    10:08:54 写入时为空、10:10 查已有值）⇒ 单次查库会漏判。
    #    ⇒ 写完立刻复查一次（微秒级，父子关系通常在此期间落定），
    #    若确认是子会话则**撤回自己刚写的名**（把 title 清回 NULL，
    #    交还宿主的 `apply_subagent_title` 命名）。
    global _PENDING_SID
    _PENDING_SID = session_id
    global _CUR_SID
    _CUR_SID = session_id
    # ⛔ 非首轮不重新起名（主题词用首轮 prompt 更准）·但仍执行"夺回写"
    title = _make_title(prompt) if is_first_turn else _reuse_title()
    if title:
        _write_title(session_id, title)
        # ⚠️ ⛔ **不在此处复查**：实测父子关系在 pre 阶段尚未落定（早则同秒、
        #    晚则几百毫秒）⇒ 立即查必然漏判。复查改在 post_llm_call（见下）。
    return None


def _post_llm_call(session_id: str = "", **_: Any) -> None:
    """每轮模型输出后**二次夺回**（⛔ 恒 None·不阻断）。

    🔴 为什么必须有这一步（2026-10-02 实盘：作者开新会话发现标题没变）：
      宿主 `title_generator` 的 upgrade 是**独立线程**（源码实证
      `threading.Thread` + `start_title_upgrade`，在 `turn_context` 里启动）。
      它的落库时机相对 `pre_llm_call` / `post_llm_call` **不确定**——
      可能在我 pre 写完之后才落 ⇒ 盖掉我的名。
      `pre_llm_call` 只能救**下一轮**；本轮结束后的覆盖**无人再管**。

    ⇒ 本步骤在 post 阶段再夺一次。仍可能输给"线程在 post 之后才落"，
      但那窗口极小（post 已在本轮模型请求之后）；配合 pre 的每轮夺回，
      实际收敛。⛔ 不做后台轮询线程（无对手确认前不引入常驻进程）。
    """
    # ⚠️ 子会话让位复查放这里（**post 阶段**·实测父子关系在 pre 阶段尚未落定）
    global _PENDING_SID
    if _PENDING_SID:
        _recheck_subagent()
        # 🔴 撤回后**必须 return**——否则本函数后半段的"二次夺回"会立刻把刚撤回的
        #    名又写回去（实测日志：reclaim → named 同秒两条·前功尽弃）。
        if _is_subagent_session(session_id):
            return None
    if not session_id or not os.path.isfile(_LOG):
        return None
    # ⚠️ 节流：post 阶段每轮都跑，但**同一 session 5 秒内只真做一次**。
    #    实测：pre+post 双挂在每次工具调用时各触发一次（pre_tool_call 也会走链路），
    #    不节流会累积成 `pre_tool_call plugin callback timed out`——
    #    ⛔ 装饰性功能绝不能拖慢主链路。宿主覆盖窗口以分钟计，5 秒粒度绰绰有余。
    now = time.time()
    key = f"_last_post_{session_id}"
    if now - globals().get(key, 0) < 5:
        return None
    globals()[key] = now
    try:
        title = _reuse_title_for(session_id)
        if not title:
            return None
        # 仅在被覆盖时才动（幂等：_write_title 内部已判 cur_title==title 跳过）
        _write_title(session_id, title)
    except Exception as exc:
        _log(f"post reclaim fail {exc!r}")
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)