#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# TRUTH_OF: 脚本中心/tsl_tree_hook.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""
tsl_tree_hook.py — TSL 树强制产出件（WB 端 Stop 链·v1.0）
第一性原理：TSL 树的产出从「AI 手动跑」变为「Stop 钩子机械产出」——AI 只剩 relay 义务。
机制：读 stamps.log 尾行 window=（上次 since 锚）→ tsl_verify --since <锚> --full
      → 树写 ~/.workbuddy/tsl_last_tree.md（下回合 UserPromptSubmit 注入回显）
stdout：JSON 单行（宿主兼容·不阻断）。
LRN-20260929-01 根治件。
v1.3（2026-10-06·WB 童灵·L5 MISS 根治配套）：--session 透传给 tsl_verify v0.11.5
      （L5 对账口径=守卫台账当轮行·会话锚由本件传入·缺省降级零回归）。
"""
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

def _stdin_session_id():
    """v1.2：从 stdin Stop payload 取 session_id（读不到=''＝旧宿主/无载荷·fail-open）。"""
    try:
        d = json.loads(sys.stdin.read() or "{}")
        return d.get("session_id", "") if isinstance(d, dict) else ""
    except Exception:
        return ""


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
            if sid and d.get("session_id") and d.get("session_id") != sid:
                continue  # v1.2：只认本会话的注入行（根除跨端/跨会话串台）
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
    sid = _stdin_session_id()
    tier = session_d_tier(sid)
    if tier != "D3":
        # 档位门控：非 D3 **不产树**（08 §七·D1/D2 ⛔无树）。
        #
        # 2026-10-02 死锁根治（Hermes 端三次实测定位·WB/ZCode 同脚本同病）：
        #   原实现在此 `os.remove(OUT)` 清残留 ⇒ **时序死锁**——树在 post_llm（回合末）产出、
        #   在下一次 pre_llm 注入，而任何一句 D1/D2 插在中间就把树擦掉。实测
        #   09:53:27 产树（stamp=27d26f40）→ 09:54:01 一个 D1 回合即删除 → 下一个 D3
        #   回合读槽已空 ⇒ 你看到的现象＝「启动童灵但 TSL 不出来」，反复四轮修不好。
        # 判据分工（§八 第五腿「每个读数口径各配可证伪用例」）：
        #   · 「该不该产树」＝档位门控（唯一裁决·此处）
        #   · 「该不该让 AI 看到」＝`tsl_echo_hook` 的档位门控 + stamp 幂等消费
        #   ⛔ 文件存在 ≠ AI 能看到 ⇒ 删文件既治不了「AI 越界 relay」，又制造跨回合死锁。
        #     真防 AI 手 relay 的是 closeout_guard（说了要树是否真跑）+ stamp 逐行绑验。
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
    print(json.dumps({"tsl_tree": "written", "out": OUT, "since": since, "stamp": stamp}))

if __name__ == "__main__":
    main()
