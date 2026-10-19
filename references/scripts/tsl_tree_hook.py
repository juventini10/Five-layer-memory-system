#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/tsl_tree_hook.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""
tsl_tree_hook.py — TSL 树强制产出件（WB 端 Stop 链·v1.4）
第一性原理：TSL 树的产出从「AI 手动跑」变为「Stop 钩子机械产出」——AI 只剩 relay 义务。
机制（v1.4·2026-10-09 Qoder CN 任务卡六改点根治·时相错根治）：
  读 stamps.log 尾行 window=（上次 since 锚）→ tsl_verify --since <锚> --full
  → 树写 ~/.workbuddy/tsl_last_tree.md（OUT）。
  ★ v1.4 时相根治（病根=原 v1.0 写文件等下回合 UPS 注入→当回合 AI 永远只有上轮树=「延迟/下次补」根因·非 AI 偷懒）：
    产树后**先查当回合回复是否已含带 stamp 树块**（复用 level_declare_guard v1.1 的
    last_assistant_message 读法 + stamps.log 尾行比对）→ 已贴→exit 0 静默；
    未贴→**exit 2 + stderr 注入「补贴指令 + 树全文」踢回**，AI 同回合末段 relay 后方可停。
    ⛔ 树全篇只出现在被踢回的那一回合末段（§3.9d 呈现点唯一性）；下回合 UPS 仅注缺账提醒（见 tsl_echo_hook）。
  ★ 防死循环：同 (sid,近期) 已 fire 过一次仍无树→降级 exit 0 放行（最坏=回现状·⛔卡死对话）。
  ★ 档位感知：仅 D3 回合产树+查贴（非 D3 不产树=物理不可越界）。
  ★ change6 联动证据：hook 真跑即写 tsl_tree_hook_ran.json（closeout 认「hook 当回合真跑」·⛔假红）。
stdout：JSON 单行（宿主兼容·不阻断）；exit 2 = 阻止停止+stderr 注入对话。
LRN-20260929-01 根治件。
v1.3（2026-10-06·WB 童灵·L5 MISS 根治配套）：--session 透传给 tsl_verify v0.11.5
      （L5 对账口径=守卫台账当轮行·会话锚由本件传入·缺省降级零回归）。
v1.4（2026-10-09·Qoder CN WB端TSL树时相根治任务卡·六改点全落地）：见上机制段。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import os, re, sys, json, subprocess
from datetime import datetime, timedelta

# v1.2（2026-09-30 by ZCode·皮叔令「遗留3项按ZCode端特性做最优适配」）：跨端适配三改——
#   ① OUT env 化（TSL_TREE_OUT·ZCode 独立树槽 ~/.zcode/tsl_last_tree.md·根除 WB/ZCode 共槽互相覆盖；
#      对齐 session_tail_inject 的 env 前缀端适配先例·默认路径不变=WB 零回归）
#   ② 门控升级 session_d_tier：优先按 stdin payload 的 session_id 过滤台账本会话最新行
#      （台账行自带 session_id/src 字段）——根除「全局最新行」跨端/跨会话串台；
#      无 session_id 的宿主退回全局最新行（向后兼容）
#   ③ VERIFY try 链：同目录自推导 → 作者侧 → 包部署面（用户侧 devtools 与本件同落点）
HOME = os.path.expanduser("~")
STAMPS = os.path.join(HOME, ".cache", "tsl_verify", "stamps.log")
OUT = os.environ.get("TSL_TREE_OUT") or os.path.join(HOME, ".workbuddy", "tsl_last_tree.md")
VERIFY_CANDIDATES = (
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsl_verify.py"),
    os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "tsl_verify.py"),
)
VERIFY = next((c for c in VERIFY_CANDIDATES if os.path.exists(c)), VERIFY_CANDIDATES[1])

INJECT_STATE = os.environ.get("TSL_INJECT_STATE") or os.path.join(HOME, ".workbuddy", "doenglingz_inject_state.json")  # env=测试隔离缝（对齐 TSL_VERIFY_CACHE 先例·守卫规范 §3.9 夹具可指向空目录）

# v1.4（2026-10-09）：fire 状态文件——记录「本轮是否已 kick 过 / 是否降级缺树」
#   env 可重定向（夹具隔离·⛔污染真状态）
FIRE_STATE = os.environ.get("TSL_FIRE_STATE") or os.path.join(HOME, ".workbuddy", "tsl_tree_fire_state.json")
# v1.4（2026-10-09·change6 联动）：hook 当回合真跑证据（closeout 认「hook 代跑」·⛔假红）
HOOK_RAN = os.environ.get("TSL_HOOK_RAN") or os.path.join(HOME, ".workbuddy", "tsl_tree_hook_ran.json")

# v1.4（2026-10-09）：last_assistant_message 读法——与 level_declare_guard v1.1 同源（⛔另起炉灶=双尺子）
# 教训：同域已有能跑的件，新建件必须先对齐它的接口（见 level_declare_guard v1.1 注释）。
KEYS = ("last_assistant_message", "responseText", "text", "prompt", "content",
        "response", "message", "last_message", "responsePreview",
        "output", "assistant_message")


def _read_payload():
    """读 Stop stdin 全量一次（⛔不得多次 read·否则后续读为空）。"""
    try:
        if hasattr(sys.stdin, "reconfigure"): sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def _stdin_session_id(payload):
    return payload.get("session_id", "") if isinstance(payload, dict) else ""


def _get_assistant_text(payload):
    """复用 level_declare_guard v1.1 的 last_assistant_message 读法；transcript 回退仅 best-effort。"""
    if not isinstance(payload, dict):
        return ""
    for k in KEYS:
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # 回退：transcript（同 level_declare_guard v1.9 位置性假红根治的读本回合 assistant 正文）
    tp = payload.get("transcript_path")
    if tp and os.path.isfile(tp):
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import transcript_reader as _tr
            return "\n".join(_tr.assistant_texts(tp))
        except Exception:
            return ""
    return ""


def _assistant_pasted_tree(text, stamp):
    """v1.4 change①：本回合回复是否已含合法 TSL 树（已 relay）。
    判据：含 TSL 形态标记 + 至少一个真实 stamp（在 stamps.log 中·非手绘）。
    优先比对本回合产出的 stamp；回退到「任一 stamp 真实存在于 stamps.log」（=脚本产出）。"""
    if not text:
        return False
    if not any(_mk in text for _mk in ("TSL-stamp", "🧾 TSL 机械核验", "├─ L0", "├─ L7-", "TSL会话评级")):
        return False
    stamps = re.findall(r"TSL-stamp\s+([0-9a-f]{8})", text)
    if stamp and stamp in stamps:
        return True
    if stamps and os.path.isfile(STAMPS):
        try:
            blob = open(STAMPS, encoding="utf-8", errors="replace").read()
            if any(s in blob for s in stamps):
                return True
        except Exception:
            pass
    # v1.5 判据③（2026-10-14 你「彻底解决双树」）：AI 自跑树的 stamp 接受 trees/ 落盘文件为机械证据
    # 根因：tsl_verify 被管道消费致 SIGKILL 时 stamps.log 可缺写，但 trees/{stamp}.txt 先写后打印仍可存在；
    #       原判据只认本回合钩子 stamp+stamps.log，同窗自跑树 stamp 必与钩子后跑树不同→死性双树。
    # 防伪造：手填假 stamp 无对应 trees 文件（文件由 tsl_verify 产出·非 AI 可写路径约定）→ 仍拒。
    trees_dir = os.path.join(os.path.dirname(STAMPS), "trees")
    for s in stamps:
        if os.path.isfile(os.path.join(trees_dir, s + ".txt")):
            return True
    return False


def _fire_state_get():
    try:
        with open(FIRE_STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _fire_state_set(sid, since, stamp, status):
    try:
        os.makedirs(os.path.dirname(FIRE_STATE), exist_ok=True)
        with open(FIRE_STATE, "w", encoding="utf-8") as f:
            json.dump({"sid": sid, "since": since, "stamp": stamp,
                       "status": status,
                       "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, f)
    except Exception:
        pass


def _fire_state_clear():
    try:
        os.remove(FIRE_STATE)
    except Exception:
        pass


def _fire_recent(fs, window=600):
    """FIRE_STATE 是否近期（同 round 判据·⛔用时间窗而非 since·防 since 漂移致失配）。"""
    if not isinstance(fs, dict) or fs.get("sid") is None:
        return False
    try:
        _ts = datetime.strptime(fs.get("ts", ""), "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - _ts).total_seconds() <= window
    except Exception:
        return False


def _mark_hook_ran(sid, stamp):
    """v1.4 change⑥：hook 真跑 tsl_verify 即留证据（closeout 认「hook 当回合代跑」·⛔假红）。"""
    try:
        os.makedirs(os.path.dirname(HOOK_RAN), exist_ok=True)
        with open(HOOK_RAN, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "stamp": stamp, "sid": sid}, f)
    except Exception:
        pass


def session_d_tier(sid):
    """v1.2：本会话最新档位（按 session_id 过滤台账）——sid 为空退全局最新行（WB 兼容）。
    TSL 树义务仅 D3（08 §七·与 tsl_echo_hook 门控同源）。

    2026-09-30 你质证根治：本件原为 Stop 链**无条件产树**——文件一直躺在
    ~/.workbuddy/tsl_last_tree.md，即使注入侧门控正确（非 D3 不注入），
    AI 仍可能**自行 cat 并 relay**（你看到的「没启动 D3 怎么还有 TSL」＝AI 越界产树）。
    修法＝把「AI 不该 relay」从**判据**（事后报警·靠自觉）升级为**物理不可达**（文件不存在）。
    """
    try:
        with open(INJECT_STATE, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        for line in reversed(lines):
            d = json.loads(line)
            # 🔴 2026-10-08 空值漏洞根治（Hermes 端实证·与 tsl_echo_hook 同源同修）：
            #   病灶：原式 `if sid and d.get("session_id") and d.get("session_id") != sid: continue`
            #     —— 第三个条件 `d.get("session_id")` 在**空 session_id** 时为假 ⇒ 整条 if 不成立
            #     ⇒ 空 sid 行**绕过本会话过滤** ⇒ 下一句 `if d.get("d_tier")` 直接把它的档位返回。
            #   实测：本机台账 161 行「空 sid + d_tier=D3」（探针噪声行）⇒ 非 D3 回合被回判 D3
            #     ⇒ 树在 D1/D2 回合照样产出（tsl_hook.log 13:56 / 14:31 两次 `written` 铁证）。
            #   修法（判据**收窄**·⛔非放宽）：有 sid 时只认 session_id **精确等于** sid 的行，
            #     空 sid / 他会话行一律 continue。无 sid（旧宿主兼容）行为逐字不变。
            if sid and d.get("session_id") != sid:
                continue  # v1.3：只认本会话的注入行（空 sid 行不再放行·根除档位误判）
            if d.get("d_tier"):
                return d.get("d_tier")
        if sid:  # 本会话无注入行 → 本会话非 D3（⛔不退全局——那正是串台源）
            return ""
        for line in reversed(lines):
            d = json.loads(line)
            if d.get("d_tier"):
                return d.get("d_tier")
    except Exception:
        pass
    return ""


def last_window():
    """stamps.log 尾行 window=<since>（上次跑的 since=本回合要 relay 的窗口）

    2026-10-02 未来窗口防御（Hermes 端实证）：stamps.log 尾 3 行 window=2026-10-02 10:00，
    而写入时刻是 09:27/09:39 —— **锚点晚于当前时间 20 分钟**。该值被原样当 since 传给
    `tsl_verify --since` ⇒ 所有当日产出（系统日志 92KB/24 条 [童灵思考] 等）都判在
    "窗口外" ⇒ L7 五项全红「本回合未写（他方 N 条不顶账）」＝**假红比不判更坏**。
    病灶：window 值无来源校验，谁写错就永久传染（last_window 读尾行·尾行是错值）。
    修法：读到 window 后与 now 比对，**晚于当前时间即视为污染值**→回退到「尾行时间戳 -1 分钟」
    （时间戳是脚本自己写的 datetime.now()·可信），全表无合法 window 时才落 -1 小时兜底。
    ⛔ 早于窗口是合法的（跨零点回看），⛔ 只挡未来值。
    """
    try:
        with open(STAMPS, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        now = datetime.now()
        for line in reversed(lines):
            m = re.search(r"window=([\d\- :]+)", line)
            if m:
                raw = m.group(1).strip()
                try:
                    if datetime.strptime(raw, "%Y-%m-%d %H:%M") > now:
                        # 未来窗口＝污染 → 改用本行首字段时间戳（脚本自写·可信）-1分钟
                        t = re.findall(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                        if t:
                            return (datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S")
                                    - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
                return raw
        # 老格式无 window=：取尾行首字段时刻-1分钟兜底
        if lines:
            t = re.findall(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", lines[-1])
            if t:
                dt = datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S") - timedelta(minutes=1)
                return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")


def main():
    payload = _read_payload()
    sid = _stdin_session_id(payload)
    tier = session_d_tier(sid)
    if tier != "D3":
        # 档位门控：非 D3 **不产树**（08 §七·D1/D2 ⛔无树）。
        _fire_state_clear()   # v1.4：清残留（防跨回合误触发·非 D3 无树义务）
        print(json.dumps({"tsl_tree": "skip",
                          "reason": "non-D3 (%s): TSL tree only for D3" % (tier or "no-tier")}))
        return
    if not os.path.exists(VERIFY):
        print(json.dumps({"tsl_tree": "skip", "reason": "tsl_verify.py not found"}))
        return
    since = last_window()
    # v1.3（2026-10-06·L5 MISS 根治配套）：--session 透传——tsl_verify v0.11.5 的 L5
    # 对账口径=守卫台账当轮行（本会话+ts>=since），会话锚由本件从 Stop 载荷取得后传入；
    # 缺省（无 sid）verify 自动降级痕账本旧口径，零回归。
    cmd = [sys.executable, VERIFY, "--since", since, "--full"]
    if sid:
        cmd += ["--session", sid]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    tree = (r.stdout or "").strip()
    if not tree:
        print(json.dumps({"tsl_tree": "skip", "reason": "empty verify output"}))
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    stamp = ""
    m = re.search(r"TSL-stamp (\w+)", tree)
    if m:
        stamp = m.group(1)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(f"<!-- tsl_tree since={since} stamp={stamp} session={sid or 'legacy'} written={datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->\n"
                f"【TSL 上回合核验树 · ⛔必须在回复中逐行 relay·本块由 Stop 钩子机械产出·AI 无省略权】\n\n"
                f"{tree}\n")
    _mark_hook_ran(sid, stamp)   # v1.4 change⑥：留 hook 当回合真跑证据（closeout 联动·⛔假红）

    # ── 六改点①：查贴（复用 level_declare_guard v1.1 的 last_assistant_message 读法）──
    text = _get_assistant_text(payload)
    if _assistant_pasted_tree(text, stamp):
        # 已贴→静默 exit 0（⛔ 不再等下回合 UPS 注入·时相错根治）
        _fire_state_clear()
        print(json.dumps({"tsl_tree": "written", "pasted": True,
                          "out": OUT, "since": since, "stamp": stamp}))
        return

    # ── 六改点③：防死循环（同 round 已 fire 过仍无树→降级 exit 0 放行·⛔卡死对话）──
    fs = _fire_state_get()
    if fs.get("status") == "missing" and _fire_recent(fs):
        # 本轮已判降级（仍无树）→ 不再 exit 2（防死循环）·直接放行
        print(json.dumps({"tsl_tree": "degrade",
                          "reason": "already degraded this round (tree still missing)",
                          "out": OUT, "since": since, "stamp": stamp}))
        return
    if fs.get("sid") == sid and fs.get("status") == "kicked" and _fire_recent(fs):
        # 同 round 第二次 Stop 仍无树→降级（留 status=missing 供下回合 echo 提醒）
        _fire_state_set(sid, since, stamp, "missing")
        print(json.dumps({"tsl_tree": "degrade",
                          "reason": "re-fire same round without tree -> fail-open (keep missing for echo reminder)",
                          "out": OUT, "since": since, "stamp": stamp}))
        return

    # ── 六改点②：未贴→exit 2 + stderr 注入「补贴指令 + 树全文」踢回 ──
    _fire_state_set(sid, since, stamp, "kicked")
    sys.stderr.write(
        "\n【TSL 树缺失·必须补贴·Stop 钩子拦截】本轮为 D3 上岗回合，TSL 核验树已由 Stop 钩子机械产出，"
        "但你的回复末段未逐行 relay。请在本轮回复末段**原样粘贴**以下 TSL 核验树"
        "（⛔省略/改写/压缩＝违反义务⑨·relay保真律），然后方可停止：\n\n"
        + tree + "\n")
    sys.exit(2)


if __name__ == "__main__":
    main()
