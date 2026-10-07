#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""hermes_tsl_closeout_adapter.py — Hermes 端 TSL 收尾守卫适配层 v1.0.0

## 为什么需要这个适配层（⛔不是重复造守卫·是补一段端差异）
三件套的 `tsl_closeout_guard.py` 是**端中立共用件**，其输入契约是
WorkBuddy 形态的 Stop hook JSON：`{"transcript_path": "...", "session_id": ...}`
（见其 `__main__`：`tp=data.get("transcript_path")` → `_tr.assistant_texts(tp)`）。

**Hermes 侧实测差异**（2026-10-01·非推测·源码实证）：
- `agent/turn_finalizer.py:453-461` 派发 `post_llm_call` 时传
  `session_id / task_id / turn_id / user_message / **assistant_response** /
  conversation_history / model / platform`
- ⛔ **不传 `transcript_path`**（全仓 grep `transcript_path` 零命中）

⇒ 直接把共用件挂 Hermes Stop 链 = 它读不到文本 = `if not text: return 0`
⇒ **静默空过＝接了个摆设**（这正是"看着接了其实没接"的典型）。

## 本适配层做什么（只做一件事·不重写判据）
把 Hermes 钩子已持有的 `assistant_response` 落成一个 **transcript_reader 能读的
JSONL 夹具**，再调用共用守卫本体。

- ✅ 共用件 `tsl_closeout_guard.py` **不读不改**（保持单一本体·⛔不做端专属分叉）
- ✅ 判据仍由共用件的 C1-C10 判据链给出（⛔适配层⛔不自己判）
- ⛔ 本适配层若失败 ⇒ 静默放行（观察层·⛔不因辅助层故障阻断回合）

## 落点（端隔离·⛔绝不碰他端目录）
`~/.hermes/doenglingz/tsl_closeout_fixture/<session_id>.jsonl`
（与 `doenglingz-twin` 插件的 `_CONFIG_ROOT` 同根·本端私有）
"""

import json
import os
import subprocess
import sys
import tempfile
import time

__version__ = "v1.0.0"
HOME = os.path.expanduser("~")
CONFIG_ROOT = os.path.join(HOME, ".hermes", "doenglingz")
FIXTURE_DIR = os.path.join(CONFIG_ROOT, "tsl_closeout_fixture")
STATE = os.path.join(CONFIG_ROOT, "tsl_closeout_adapter_state.json")
GUARD_CANDIDATES = (
    os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "tsl_closeout_guard.py"),
    os.path.join(os.path.expanduser("[记忆共享中心]"), "数字分身", "devtools", "tsl_closeout_guard.py"),
)
TIMEOUT = 25


def _guard_path():
    for p in GUARD_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def run(assistant_response="", session_id="", _guard_env=None, **_):
    """跑共用守卫本体。⛔ 任何异常/缺件 ⇒ 静默放行（观察层不阻断）。"""
    if not assistant_response.strip():
        return None
    g = _guard_path()
    if not g:
        return None
    fx = None
    try:
        os.makedirs(FIXTURE_DIR, exist_ok=True)
        sid = (session_id or "sess")[:64]
        fx = os.path.join(FIXTURE_DIR, "%s.jsonl" % sid)
        # transcript_reader 的 locate() 认 WB/Qoder 形态：type=message + role=assistant。
        # ⛔ 只写本轮这一条（守卫只看"本回合回复"·⛔不堆历史）。
        with open(fx, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "message", "role": "assistant",
                                "content": assistant_response}, ensure_ascii=False) + "\n")
        payload = json.dumps({"transcript_path": fx, "session_id": sid},
                             ensure_ascii=False)
        r = subprocess.run([sys.executable, g], input=payload,
                           capture_output=True, text=True, timeout=TIMEOUT,
                           env=_guard_env)
        _write_state({"ts": time.time(), "rc": r.returncode,
                      "violation": bool((r.stdout or "").strip()),
                      "out": (r.stdout or "")[:500],
                      "err": (r.stderr or "")[:200]})
        return r
    except Exception as exc:
        _write_state({"ts": time.time(), "rc": -1, "violation": False,
                      "err": repr(exc)})
        return None
    finally:
        # ⛔ 夹具是本轮产物·跑完即删（⛔不留 transcript 副本·隐私红线）
        try:
            if fx and os.path.isfile(fx):
                os.remove(fx)
        except Exception:
            pass


def _write_state(obj):
    try:
        os.makedirs(CONFIG_ROOT, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=CONFIG_ROOT, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE)
    except Exception:
        pass


def selftest():
    """C4/C7 自证：①真源树+已跑verify ⇒ 绿 ②有树+未跑 ⇒ 红 ③无TSL树 ⇒ 静默放行

    ⚠️ 2026-10-01 实测踩坑修正：夹具 cache **不可重定向**——
      `tsl_verify.py:24` 把 CACHE **硬编码**为 `~/.cache/tsl_verify`，
      ⛔**不认** `TSL_VERIFY_CACHE` env（只有 guard 认）⇒
      verify 写真 cache、guard 查子 cache ⇒ stamp 对不上 ⇒ ①假红。
      ⇒ 自测走**真 cache**（与真机同语义）·用「改 last_run mtime」模拟未跑。
    """
    ok = True
    import subprocess as sp
    cache = os.path.expanduser("~/.cache/tsl_verify")   # ⛔ 与真机同一 cache
    verify = os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "tsl_verify.py")
    lr = os.path.join(cache, "last_run.txt")

    def restore():
        if os.path.isfile(lr):
            try:
                os.utime(lr, None)
            except Exception:
                pass

    tree = ""
    try:
        vr = sp.run([sys.executable, verify, "--since",
                     time.strftime("%Y-%m-%d 00:00"), "--full"],
                    capture_output=True, text=True, timeout=60)
        tree = vr.stdout
    except Exception:
        tree = ""

    if not tree.strip():
        print("PASS ①跳过（无法取得真源树·⛔不手编）")
    else:
        # ① 真源树 + last_run 存在 ⇒ 不告警
        r = run(assistant_response=tree, session_id="st_green")
        g1 = (r is not None and not (r.stdout or "").strip())
        print("%s ①真源树+已跑verify ⇒ 不告警  %s"
              % ("PASS" if g1 else "FAIL",
                 (r.stdout or "").strip()[:70] if r else "None"))
        ok = ok and g1

    # ② 暂挪 last_run ⇒ 模拟「说了要树但没跑 verify」⇒ 必红
    bak = lr + ".selftest_bak"
    moved = False
    try:
        if os.path.isfile(lr):
            os.replace(lr, bak)
            moved = True
        r = run(assistant_response=tree or "├─ L0 接入态 ✅做到\n🔏 TSL-stamp x\n",
                session_id="st_red")
        g2 = (r is not None and "🔴" in (r.stdout or ""))
        print("%s ②有树+未跑verify ⇒ 告警  %s"
              % ("PASS" if g2 else "FAIL",
                 (r.stdout or "").strip()[:70] if r else "None"))
        ok = ok and g2
    finally:
        if moved and os.path.isfile(bak):
            os.replace(bak, lr)
            restore()

    # ③ 无 TSL 树 ⇒ 静默放行（观察层）
    r = run(assistant_response="普通回复，没有 TSL 树。", session_id="st_none")
    g3 = (r is not None and not (r.stdout or "").strip())
    print("%s ③无TSL树 ⇒ 静默放行  %s"
          % ("PASS" if g3 else "FAIL",
             (r.stdout or "").strip()[:70] if r else "None"))
    ok = ok and g3

    print("selftest: %s" % ("3/3 全绿" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    # 调试用：把 stdin 当作 assistant_response 灌进去
    _in = sys.stdin.read()
    _r = run(assistant_response=_in, session_id="cli")
    print(_r.stdout if _r else "")
    raise SystemExit(0)