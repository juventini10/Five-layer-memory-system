#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1 → v0.2
"""hook_protocol.py — UserPromptSubmit 注入钩子的「输出协议」单一真源适配器。

## v0.2 病根（2026-10-07·你「上岗回复老不按模板」三问根治）

**为什么 WB 端全端注入互相覆盖**（引擎源码实证，`app.asar.unpacked/cli/dist/codebuddy-lite-wb.mjs`）：

| 宿主环节 | 源码行为 | 语义 |
|:---|:---|:---|
| `aggregateSettledResults` | `hookSpecificOutput = {...旧, ...新}` | **同 key 覆盖**（additionalContext 后者赢） |
| `aggregateSettledResults` | `stdout = 旧 + "\n" + 新` | **拼接共存** |
| UPS 消费 L6971791 | 有 additionalContext → 覆盖赋值；否则走 stdout 拼接 | 二选一 |

⇒ **json envelope = 竞争（last wins）；裸文本 = 共存**。WB 端UserPromptSubmit 实挂 11 条，
多条同时发 envelope ⇒ 排在前面的注入块**结构性必被覆盖**（童灵块排第 4，其后还有 5 个 json emitter）。

**本版修法（双保险·构造权在配置不在推断）**：
1. **argv 显式声明为主路径**——`settings.json` 每条钩子命令显式携带 `--hook-protocol=text|json`，
   argv 优先级最高（判据链第 1 级）⇒ 端形态由**配置声明**决定，⛔不再靠 env 猜。
2. **payload 路径指纹作第二腿**——WB 载荷 `transcript_path/cwd` 必含 `/.workbuddy/`（引擎
   `getHookTranscriptPath()` 保证）⇒ 加 `TEXT_HOSTS_BY_PATH` 表，命中即 text。
   治本端 env 不可信：`CLAUDE_SESSION_ID` 在 **WB 端同样存在**（CodeBuddy 兼容层导出，实测），
   v0.1 把它当 ZCode 专属判据 ⇒ **WB 被误判成 zcode → 全端走 json → 互相覆盖**（本次病根）。
   该 env 判据已降级为「无指纹无配置时的兜底」，⛔不再单独把任一端判成 json。

## 为什么存在（2026-09-04 根治·非补丁）
病灶：doenglingz_inject_prompt.py / route_inject_prompt.py / kb_inject_prompt.py /
position3_notify.py 四个注入钩子各自复制了一份一模一样的 _zcode_host()+_emit()
（四实现），判据只认 ZCode 的三个环境变量。结果 Qoder CN 端走"裸文本"分支，而
**本端产品把裸文本整轮丢弃**——实测取证：questWindow/hooks.log 里
`Hook dispatch result (event=UserPromptSubmit, winner=none (no parsed output))`
143 轮 / 143 轮（stdout 已含【童灵上岗·行为契约】全文、exitCode=0，仍判"无解析输出"）。
⇒ 注入通道在本端事实静默；且所有检核仪器（挂载自检/成熟度评估）只验到"脚本存在/
   脚本能跑"，没有一台验"产品是否收下"（S885 建好≠接入≠被用，打在评估器自己身上）。

## 判据优先级（高→低·不猜只验）
1. argv 显式声明 `--hook-protocol=json|text`（人工指定，最可审计，覆盖一切）
2. 载荷指纹：payload 任一字符串值含"已实测须 JSON"端的配置根路径
   （/.qoder-cn/ → Qoder CN）。数据自证，零配置，新端加一行表即可（愿景①）
3. env 指纹：ZCODE_PROJECT_DIR / CLAUDE_SESSION_ID / ZCODE_SESSION_ID → JSON
   （保留 2026-08-27 的 ZCode 既有判据，零回归）
4. 默认 text：未知端维持裸文本（WorkBuddy 实测吃 text，⛔不擅改他人合法形态）

冲突纪律：argv 与指纹同时在场且不一致 → 按 argv 走，但留痕标 conflict（不静默）。
保守纪律：表内只收"已实测"的端。/.qoder/(Qoder Desktop) 形态未实测→不进表，
   维持默认 text，待实测再登记（同 cross-end-guard 守卫保守判定纪律）。

## 留痕（取证=机制的一部分，不是临时脏活）
每次运行 append 一行到 logs/runtime/hook_protocol_ledger.jsonl：
{ts, script, event, mode, host, reason, conflict, bytes, payload_keys, qoder_env}
⛔ 只记键名不记值 → 不触隐私红线（正文/凭据一律不落盘）。
用途：①自动取证本端 UPS 真实载荷键（本轮未知，交给机制收，不靠人查）；
     ②供 qodercn_config_guard「注入收下率」查按 ts 对账产品回执。
体积：超 MAX_LEDGER_LINES 自动截断保留后半（钩子⛔不可因写盘膨胀失控）。

## 派发心跳（2026-09-21 端用户连坐案例·注册态查不出的死法）
病灶：端用户机器上第三方插件的 hooks.json 格式非法 → 宿主按「一条配置坏=整个
事件停摆」策略处理 → UserPromptSubmit 整事件不再派发 → 本包硬墙钩子集体失效，
settings.json 条目完好 = 注册态核查零症状（S014 判据：配了≠在跑）。
机制：本模块被 import 即留痕（宿主派发=spawn 进程=import 执行）→
     `~/.workbuddy/hooks/.heartbeats/<脚本主名>.heartbeat`。
消费方：guard_heartbeat_check.py（--brief 已接入 verify §3.6 advisory 显形）。
路径单一真源=本文件 HB_DIR；guard 侧有漂移绊线（--selfcheck）。
异常免疫：留痕失败绝不阻塞钩子主功能（全 try/except 静默）。
probe 测试运行（HOOK_PROTOCOL_TEST=1）不留痕，防伪造派发证据。

## 纪律（守卫编写规范）
纯 stdlib；任何异常 → 退回 text 并放行；不阻断对话（exit code 归调用方）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import sys
import glob
from datetime import datetime

USER_PROMPT_SUBMIT = "UserPromptSubmit"

# 须 JSON 形态的端：配置根路径指纹 → 端名（逐条登记实测来源，见模块 docstring）
JSON_HOSTS_BY_PATH = {
    "/.qoder-cn/": "qodercn",
}

# v0.2：须text（裸 stdout）形态的端：配置根路径指纹 → 端名
# WB 载荷的transcript_path/cwd 必含 `/.workbuddy/`（引擎 getHookTranscriptPath 保证），
# 故此表是**载荷自证**，不依赖 env（env 在 WB 端与ZCode 端高度重叠·不可作判据）。
TEXT_HOSTS_BY_PATH = {
    "/.workbuddy/": "workbuddy",
}

LEDGER = os.path.expanduser("[记忆共享中心]/脚本中心/logs/runtime/hook_protocol_ledger.jsonl")
MAX_LEDGER_LINES = 2000

# ── 派发心跳（2026-09-21 端用户连坐案例）──────────────────────────────────
# 路径单一真源：guard_heartbeat_check.py 动态对账本常量（--selfcheck 漂移绊线）。
HB_DIR = os.path.join(os.path.expanduser("~"), ".workbuddy", "hooks", ".heartbeats")


def touch_heartbeat(script=None):
    """被宿主派发（import 执行）即留痕。异常全免疫：心跳绝不阻塞钩子主功能。"""
    try:
        if os.environ.get("HOOK_PROTOCOL_TEST"):
            return  # probe 测试运行不留痕（防伪造派发证据）
        os.makedirs(HB_DIR, exist_ok=True)
        stem = os.path.splitext(os.path.basename(
            script or (sys.argv[0] if sys.argv else "hook_protocol")))[0]
        with open(os.path.join(HB_DIR, "%s.heartbeat" % stem), "w",
                  encoding="utf-8") as f:
            f.write(datetime.now().isoformat(timespec="seconds"))
    except Exception:
        pass


touch_heartbeat()


def _env_json_flags():
    """ZCode 专属 env（v0.2 收窄）。

    v0.1 含 `CLAUDE_SESSION_ID` —— **实测该变量在 WB 端同样存在**（CodeBuddy 兼容层导出），
    导致 WB 被判 json → 全端多钩子走 envelope → 同 key 覆盖 → 注入块结构性丢失。
    ⇒ v0.2 只认 `ZCODE_` 前缀（ZCode 专属），⛔ 不再用跨端共有变量当判据。
    """
    return [k for k in ("ZCODE_PROJECT_DIR", "ZCODE_SESSION_ID")
            if os.environ.get(k)]


def _qoder_env_keys():
    """取证：Qoder 是否向钩子子进程导出 QODER_* 变量（只取键名）。"""
    return sorted(k for k in os.environ if k.startswith("QODER"))


def _fingerprint(payload, table):
    """载荷路径指纹 → 端名。⛔只认payload 里的字符串值，不猜。"""
    if not isinstance(payload, dict):
        return ""
    for v in payload.values():
        if isinstance(v, str):
            for frag, host in table.items():
                if frag in v:
                    return host
    return ""


def _fingerprint_host(payload):
    """json 端指纹（保留旧名·调用方兼容）。"""
    return _fingerprint(payload, JSON_HOSTS_BY_PATH)


def _text_fingerprint_host(payload):
    """v0.2：text 端载荷指纹（WB `/.workbuddy/`）——优先级高于 env。"""
    return _fingerprint(payload, TEXT_HOSTS_BY_PATH)


def _argv_declared(argv):
    for i, a in enumerate(argv):
        if a.startswith("--hook-protocol"):
            if "=" in a:
                return a.split("=", 1)[1].strip().lower()
            if i + 1 < len(argv):
                return argv[i + 1].strip().lower()
    return ""


def detect(payload=None, argv=None):
    """判协议 → (mode, host, reason, conflict)。

    判据优先级（v0.2·构造权在配置不在推断）：
      ① argv 显式 `--hook-protocol=text|json`（配置声明·最高·可审计）
      ② payload 路径指纹：json 表（/.qoder-cn/）优先于 text 表（/.workbuddy/）
         —— 载荷自证，⛔ 不依赖 env（跨端共有变量不可作判据·见 _env_json_flags 病根注）
      ③ env 指纹（仅 ZCODE_ 前缀·ZCode 专属）
      ④ 默认 text（未知端维持裸文本·各端零回归）

    ⚠️ text 优先于 json 的次序在此单点固化：WB 端必须走 text，否则同事件多钩子
    envelope 同 key 覆盖 ⇒ 注入块丢失（2026-10-07 病根·引擎源码实证）。
    """
    argv = list(argv if argv is not None else sys.argv[1:])
    declared = _argv_declared(argv)
    fp_json = _fingerprint(payload, JSON_HOSTS_BY_PATH)
    fp_text = _text_fingerprint_host(payload)
    env_flags = _env_json_flags()
    if fp_json:
        derived, host = "json", fp_json
    elif fp_text:
        derived, host = "text", fp_text
    elif env_flags:
        derived, host = "json", "zcode"
    else:
        derived, host = "text", ""
    conflict = bool(declared and declared != derived)
    mode = declared if declared in ("json", "text") else derived
    if declared:
        reason = "argv:--hook-protocol"
    elif fp_json:
        reason = "fingerprint:%s" % fp_json
    elif fp_text:
        reason = "fingerprint:%s" % fp_text
    elif env_flags:
        reason = "env:%s" % ",".join(env_flags)
    else:
        reason = "default:text"
    return mode, host, reason, conflict


def _ledger(mode, host, reason, conflict, ctx, payload, event, script):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "script": script or os.path.basename(sys.argv[0]),
            "event": event,
            "mode": mode,
            "host": host,
            "reason": reason,
            "conflict": bool(conflict),
            "bytes": len(ctx or ""),
            "payload_keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
            "qoder_env": _qoder_env_keys(),
            # probe=手工单元测行（HOOK_PROTOCOL_TEST=1 导出）→ 不参与守卫对账，防测试数据假绿/假红
            "probe": bool(os.environ.get("HOOK_PROTOCOL_TEST")),
        }
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        try:
            with open(LEDGER, encoding="utf-8") as f:
                n = sum(1 for _ in f)
            if n > MAX_LEDGER_LINES:
                with open(LEDGER, encoding="utf-8") as f:
                    tail = f.readlines()[n - MAX_LEDGER_LINES // 2:]
                with open(LEDGER, "w", encoding="utf-8") as f:
                    f.writelines(tail)
        except Exception:
            pass
    except Exception:
        pass


def emit(ctx, payload=None, argv=None, event=USER_PROMPT_SUBMIT, script=""):
    """按判定协议输出 ctx 并留痕，返回 mode。空 ctx 只留痕不输出。"""
    try:
        mode, host, reason, conflict = detect(payload, argv)
    except Exception:
        mode, host, reason, conflict = "text", "", "detect-error", False
    _ledger(mode, host, reason, conflict, ctx, payload, event, script)
    if not ctx:
        return mode
    if mode == "json":
        sys.stdout.write(json.dumps(
            {"hookSpecificOutput": {"hookEventName": event, "additionalContext": ctx}},
            ensure_ascii=False))
    else:
        sys.stdout.write(ctx)
    return mode


# ── 成本读数（2026-09-04 副作用登记配套·⛔不新增文件，复用本模块留痕 + W1/W3 台账）──
INJECT_STATE = os.path.expanduser("~/.workbuddy/doenglingz_inject_state.json")


def _cost_report(hours=24, src="qodercn"):
    """量化"注入到底占了多少上下文"，并给出降噪裁剪候选（字节高×命中低）。

    用途（皮叔 2026-09-04「万一哪天觉得吵，要有溯源、也知道要怎么做」）：
      吵不吵先看读数 → 要裁先裁候选；⛔处置口径不是"关钩子"，是调 W3 窄集触发词
      （改匹配先 dry-run，见铁律-020）。条文真源见 05 §6.1·成本与降噪。
    """
    from collections import defaultdict
    cutoff = datetime.now() - __import__("datetime").timedelta(hours=hours)
    agg = defaultdict(lambda: {"n": 0, "bytes": 0, "modes": defaultdict(int)})
    layers = defaultdict(int)
    w1 = 0
    rounds = defaultdict(int)  # 按秒聚合的"轮"（同秒多脚本=同一轮）

    def _ts_ok(ts):
        try:
            return datetime.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S") >= cutoff
        except Exception:
            return False

    try:
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("probe") or not _ts_ok(d.get("ts")):
                    continue
                if int(d.get("bytes", 0)) <= 0:
                    continue
                a = agg[d.get("script", "?")]
                a["n"] += 1
                a["bytes"] += int(d["bytes"])
                a["modes"][d.get("mode", "?")] += 1
                rounds[str(d.get("ts", ""))[:16]] += 1
    except FileNotFoundError:
        print("（无留痕台账·成本未知：尚未有钩子经真源输出）")
        return

    try:
        with open(INJECT_STATE, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("src") and d.get("src") != src:
                    continue  # 端隔离：只算本端
                if not _ts_ok(d.get("ts")):
                    continue
                if d.get("w1"):
                    w1 += 1
                for l in d.get("w3_layers") or []:
                    layers[l] += 1
    except FileNotFoundError:
        pass

    total = sum(a["bytes"] for a in agg.values())
    n_rounds = max(len(rounds), 1)
    print("=== 注入成本读数（近 %dh·端=%s）===" % (hours, src))
    print("  发出合计 %d B ／ 涉及轮次 %d 轮 ／ 每轮均摊 %.1f KB"
          % (total, n_rounds, total / n_rounds / 1024))
    print("  %-32s %5s %9s %9s  %s" % ("钩子", "次数", "字节", "均B", "形态"))
    for name, a in sorted(agg.items(), key=lambda kv: -kv[1]["bytes"]):
        print("  %-32s %5d %9d %9d  %s"
              % (name[:32], a["n"], a["bytes"], a["bytes"] // max(a["n"], 1),
                 ",".join("%s:%d" % (k, v) for k, v in a["modes"].items())))
    print("  W1 上岗触发 %d 次／W3 层命中：%s" % (w1, ", ".join("%s=%d" % (k, v) for k, v in layers.items()) or "无"))
    cands = [n for n, a in sorted(agg.items(), key=lambda kv: -kv[1]["bytes"])[:2]]
    print("  降噪裁剪候选（字节最大·优先核对触发词是否过宽）：%s" % ("、".join(cands) or "无"))
    print("  ⛔处置口径=调 W3/触发词窄集（改前 dry-run·铁律-020），不是关钩子；详述见 05 §6.1·成本与降噪")


def selfcheck():
    cases = [
        ("QoderCN UPS 载荷(含本端配置根)",
         {"session_id": "x", "cwd": "/Users/y/qoder-cn-work",
          "hook_event_name": USER_PROMPT_SUBMIT,
          "transcript_path": "/Users/y/.qoder-cn/projects/a/transcript/t.jsonl",
          "prompt": "启动童灵"}),
        ("WorkBuddy UPS 载荷(路径无 .qoder-cn)",
         {"session_id": "x", "cwd": "/Users/y/wb", "hook_event_name": USER_PROMPT_SUBMIT,
          "transcript_path": "/Users/y/.workbuddy/traces/t.jsonl", "prompt": "启动童灵"}),
        ("QoderCN Stop 载荷(键集不同)",
         {"hook_event_name": "Stop", "cwd": "/Users/y/qoder-cn-work",
          "last_assistant_message": "x",
          "transcript_path": "/Users/y/.qoder-cn/projects/a/transcript/t.jsonl"}),
    ]
    print("=== hook_protocol 判定链自验 ===")
    for name, pl in cases:
        m, h, r, c = detect(pl, argv=[])
        print("  %-34s → mode=%-4s host=%-8s reason=%-24s conflict=%s" % (name, m, h or "-", r, c))
    m, h, r, c = detect(cases[1][1], argv=["--hook-protocol=json"])
    print("  %-34s → mode=%-4s reason=%-24s conflict=%s（argv 覆盖须生效且冲突留痕）"
          % ("WB 载荷 + argv 强制 json", m, r, c))
    print("  留痕台账: %s" % LEDGER)
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        print("  已留痕 %d 行；末 3 行：" % len(lines))
        for l in lines[-3:]:
            try:
                d = json.loads(l)
                print("    %s %-26s mode=%-4s reason=%-22s bytes=%-5s qoder_env=%s pkeys=%s"
                      % (d["ts"], d["script"][:26], d["mode"], d["reason"], d["bytes"],
                         ",".join(d.get("qoder_env") or []) or "[]",
                         ",".join(d.get("payload_keys") or [])[:64]))
            except Exception:
                print("    RAW:", l[:120])
    else:
        print("  ⚠️ 尚无留痕（未被任何钩子调用过）")
    print("=== 自验结束 ===")


# ── 报警侧收讫（送达律·2026-09-05 根治·与宿主收讫律互为镜像）────────────────
# 病灶（实证）：rule_three_layer_guard 第412行「只有 --strict 才 exit 1」⇒ 默认 warn-only 恒 exit 0；
#   qodercn_config_guard.hook_mode 只 sys.stdout.write 且 return 0。二者都把告警打在
#   「Stop 钩子 stdout + 零退出」上——本端 Stop 的 stdout 不回灌模型 ⇒ 对着墙说话：
#   三层漂移红了 19 天无人知（本次由皮叔三问才照出）。
# 范本（实证可送达）：l3_conclusion_guard 用 stderr 详情 + stdout 指令 + exit 2，
#   其文本确实出现在助手上下文（22:25 目击）⇒ 送达配方＝(stderr + stdout reason + 非零退出)。
# 节流：同指纹默认 24h 只送一次（防送达变骚扰）；新告警（指纹变）立即送。
ALERT_LEDGER = os.environ.get(
    "HOOK_ALERT_LEDGER",
    os.path.join(os.path.dirname(LEDGER), "hook_alert_ledger.jsonl"))
TRANSSCRIPT_GLOB = os.path.expanduser("~/.qoder-cn/projects/*/transcript/*.jsonl")
ALERT_THROTTLE_MIN = 1440
DELIVERED = "delivered"      # 已投递待收讫
SEEN = "seen"                # 已在宿主 transcript 中命中＝送达确认
LOST = "lost"                # 超时仍未命中＝报警侧未收讫（红）


def _fp(name, text):
    import hashlib
    return hashlib.sha1(("%s|%s" % (name, text)).encode("utf-8")).hexdigest()[:6]


def _append_alert(rec):
    try:
        os.makedirs(os.path.dirname(ALERT_LEDGER), exist_ok=True)
        with open(ALERT_LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def alert(name, text, argv=None, throttle_min=None, via_hook=False):
    """把告警投到能抵达宿主的通道上。返回建议退出码（2=送达·0=节流静默）。

    投法：stderr 写「[name·指纹] 详情」＋ stdout 写可执行指令（宿主对 Stop 回灌用哪条
    各有偏好，双写不猜）；同时记入投递台账，供 delivery_check() 事后核收讫。
    """
    fp = _fp(name, text)
    since = datetime.now() - __import__("datetime").timedelta(
        minutes=throttle_min if throttle_min is not None else ALERT_THROTTLE_MIN)
    try:
        with open(ALERT_LEDGER, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("fp") == fp and str(d.get("ts", "")) >= since.isoformat(timespec="seconds"):
                    return 0   # 同告警节流窗口内已投过，不重复喊
    except FileNotFoundError:
        pass
    tag = "[%s·%s]" % (name, fp)
    try:
        sys.stderr.write("%s %s\n" % (tag, text))
    except Exception:
        pass
    try:
        sys.stdout.write("%s %s\n" % (tag, text))
    except Exception:
        pass
    # via_hook：只有经钩子通道投递的告警才可能被宿主回灌；手动跑记 manual（不参与收讫核，防假红）
    _append_alert({"ts": datetime.now().isoformat(timespec="seconds"), "name": name,
                   "fp": fp, "state": DELIVERED if via_hook else "manual",
                   "via_hook": bool(via_hook), "text": text[:200]})
    return 2


def delivery_check(window_hours=6):
    """核收讫：投递过的指纹是否真出现在宿主 transcript 里（不猜语义，只搜指纹串）。

    指纹码只存在于告警文本中，不会被命令行回显误命中（区别于「某字符串出现在日志里」）。
    返回 {fp: state}：seen=送达确认 / lost=超窗未命中（该报红）/ delivered=还在窗口内待观察。
    """
    now = datetime.now()
    cut = now - __import__("datetime").timedelta(hours=window_hours)
    out = {}
    try:
        with open(ALERT_LEDGER, encoding="utf-8", errors="replace") as f:
            rows = [json.loads(l) for l in f if l.strip()]
    except Exception:
        return out
    # 收讫核只看钩子投递（manual/seen 不参与）——实证：手动跑产生的告警永远不会进 transcript，
    # 若一并核就成了"送达通道失效"假红（本轮 07:09 那条即手动产生，已按 manual 归类）
    pend = [r for r in rows if r.get("state") == DELIVERED and r.get("via_hook")]
    if not pend:
        return out
    hay = ""
    try:
        files = sorted(glob.glob(TRANSSCRIPT_GLOB), key=lambda p: os.path.getmtime(p))[-3:]
        for fp_ in files:
            try:
                with open(fp_, encoding="utf-8", errors="replace") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 1048576))   # 尾 1MB×3 文件，成本有界
                    hay += f.read()
            except Exception:
                continue
    except Exception:
        hay = ""
    for r in pend:
        fpv = str(r.get("fp", ""))
        if fpv and fpv in hay:
            out[fpv] = SEEN
            r["state"] = SEEN
        else:
            try:
                t = datetime.strptime(str(r.get("ts", ""))[:19], "%Y-%m-%dT%H:%M:%S")
            except Exception:
                t = now
            out[fpv] = LOST if t < cut else DELIVERED
    try:   # 状态回写（幂等：只重写已转 seen 的行）
        if any(v == SEEN for v in out.values()):
            with open(ALERT_LEDGER, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return out


def self_test():
    """负例夹具（守卫编写规范·原则3：绿灯需要负例证据；登记三件套件①）。

    覆盖：正例（本端必 json／WB 必 text）+ 负例（阴性载荷不误判、冲突必留痕、
    非 JSON 形态不得进 json 分支、probe 行不入生产对账）。
    """
    ok = fail = 0
    def chk(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1; print("  ✅ %s" % name)
        else:
            fail += 1; print("  ❌ %s" % name)

    CN = {"hook_event_name": USER_PROMPT_SUBMIT, "session_id": "a",
          "transcript_path": "/Users/y/.qoder-cn/projects/x/transcript/t.jsonl", "prompt": "p"}
    WB = {"hook_event_name": USER_PROMPT_SUBMIT, "session_id": "b",
          "transcript_path": "/Users/y/.workbuddy/traces/t.jsonl", "prompt": "p"}

    chk("T1 本端载荷→json", detect(CN, argv=[])[0] == "json")
    chk("T2 本端载荷 host=qodercn", detect(CN, argv=[])[1] == "qodercn")
    chk("T3 WB 载荷→text（零回归负例）", detect(WB, argv=[])[0] == "text")
    # ── v0.2 病根回归夹具（2026-10-07·多钩子同 key 覆盖）────────────────────────
    # 载荷自证必须压过 env：WB 端同样导出 CLAUDE_SESSION_ID（v0.1 病根），
    # 若把该变量当 ZCode 判据 → WB 判 json → 全端 envelope 互相覆盖。
    _saved = {k: os.environ.get(k) for k in
              ("ZCODE_PROJECT_DIR", "ZCODE_SESSION_ID", "CLAUDE_SESSION_ID")}
    try:
        os.environ.pop("ZCODE_PROJECT_DIR", None)
        os.environ.pop("ZCODE_SESSION_ID", None)
        os.environ["CLAUDE_SESSION_ID"] = "leaked-from-codebuddy-compat"
        m, h, r, c = detect(WB, argv=[])
        chk("T13 WB载荷+CLAUDE_SESSION_ID共现 → 仍text（v0.2病根回归）",
            m == "text" and h == "workbuddy")
        chk("T14 上一行 reason=fingerprint:workbuddy（载荷自证非env）",
            r == "fingerprint:workbuddy")
        os.environ["ZCODE_SESSION_ID"] = "zcode-real"
        m2, h2, r2, _ = detect(WB, argv=[])
        chk("T15 WB载荷+ZCODE_SESSION_ID共现 →载荷指纹优先（仍text）",
            m2 == "text" and h2 == "workbuddy")
        # 真·ZCode 载荷仍必 json（⛔ 修WB 不得顺带破 Qoder CN）
        m3, h3, r3, _ = detect(CN, argv=[])
        chk("T16 QoderCN载荷+ZCODE env共现 → 仍json（他端零回归）",
            m3 == "json" and h3 == "qodercn")
    finally:
        for k, v in _saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    # argv 声明压过一切（构造权在配置）
    chk("T17 argv=text 覆盖 WB 指纹", detect(WB, argv=["--hook-protocol=text"])[0] == "text")
    chk("T18 argv=json 覆盖 WB 指纹（人工覆盖合法）",
        detect(WB, argv=["--hook-protocol=json"])[0] == "json")
    chk("T4 argv 覆盖生效", detect(WB, argv=["--hook-protocol=json"])[0] == "json")
    chk("T5 argv 与指纹冲突必留痕", detect(WB, argv=["--hook-protocol=json"])[3] is True)
    chk("T6 argv 与指纹一致不标冲突", detect(CN, argv=["--hook-protocol=json"])[3] is False)
    chk("T7 空/非 dict 载荷不崩", detect(None, argv=[])[0] == "text" and detect("x", argv=[])[0] == "text")
    chk("T8 无指纹路径不误判 json",
        detect({"transcript_path": "/Users/y/.qoder/a.jsonl"}, argv=[])[0] == "text")
    # T9 emit 形态：json 模式产出合法 JSON 且带 hookEventName；text 模式产出裸文本
    import io as _io
    import contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit("TESTCTX", payload=CN, argv=[], script="hook_protocol_selftest")
    got = buf.getvalue()
    try:
        d = json.loads(got)
        good = (d["hookSpecificOutput"]["hookEventName"] == USER_PROMPT_SUBMIT
                and d["hookSpecificOutput"]["additionalContext"] == "TESTCTX")
    except Exception:
        good = False
    chk("T9 json 模式产出合规 envelope", good)
    buf2 = _io.StringIO()
    with contextlib.redirect_stdout(buf2):
        emit("TESTCTX", payload=WB, argv=[], script="hook_protocol_selftest")
    chk("T10 text 模式产出裸文本（不多包 JSON）", buf2.getvalue() == "TESTCTX")
    buf3 = _io.StringIO()
    with contextlib.redirect_stdout(buf3):
        emit("", payload=CN, argv=[], script="hook_protocol_selftest")
    chk("T11 空文本零输出（阴性例）", buf3.getvalue() == "")
    # T12 probe 隔离：带 env 的运行必须标 probe=true（防测试数据污染生产对账）
    os.environ["HOOK_PROTOCOL_TEST"] = "1"
    try:
        with contextlib.redirect_stdout(_io.StringIO()):
            emit("P", payload=CN, argv=[], script="hook_protocol_selftest")
        with open(LEDGER, encoding="utf-8") as f:
            last = json.loads([l for l in f if l.strip()][-1])
        chk("T12 probe 标记隔离生效", last.get("probe") is True)
    finally:
        os.environ.pop("HOOK_PROTOCOL_TEST", None)
    with open(LEDGER, encoding="utf-8") as f:
        rows = [l for l in f if l.strip()]
    kept = [l for l in rows if '"hook_protocol_selftest"' not in l]
    if len(kept) != len(rows):  # 自测行不留在生产台账（防自污染·同 S022 廉价命中教训）
        with open(LEDGER, "w", encoding="utf-8") as f:
            f.writelines(kept)
    print("自测结果：%d 通过 / %d 失败（自测行已从生产台账剔除）" % (ok, fail))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
        sys.exit(0)
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if "--cost-report" in sys.argv:
        h = 24
        for i, a in enumerate(sys.argv):
            if a == "--hours" and i + 1 < len(sys.argv):
                try:
                    h = int(sys.argv[i + 1])
                except Exception:
                    pass
        _cost_report(hours=h)
        sys.exit(0)
    print(__doc__)
    sys.exit(0)
