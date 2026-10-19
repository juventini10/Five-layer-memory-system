#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# version: v0.1
"""
doenglingz_guard_dsh.py — DSH 端童灵守护三查适配器（B 方案·06规范§2.2各端自行适配）。

设计定位：DSH 端 Stop 通道（agent/turn-stopping）经 index.js runGuard 传 {transcript_path} stdin，
而 doenglingz_guard.py（共脚本·Qoder CN 版）期待 --text argv 或 stdin Stop 载荷（.text/.prompt/.content）。
本适配器=thin wrapper：读 transcript_path→提取最后 assistant text→调 doenglingz_guard.py --check（stdin 传 JSON），
复用共脚本全部 scan 逻辑（红区六类/铁律触线/认知深化信号），零改共脚本·零回归。

台账：写 ~/.dsh/doenglingz_guard_state.json（DSH 端专属·与 Qoder CN 的 ~/.workbuddy/ 区分）。
失败默认放行（exit 0）·提示性扫描不阻断（对齐 doenglingz_guard.py 守护自限·02规范§五.3）。

来源：你授权「按符合愿景第一性原理做完工作」·2026-09-07。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import sys
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

STATE_FILE = os.path.expanduser("~/.dsh/doenglingz_guard_state.json")


def _resolve_guard_core():
    """解析 doenglingz_guard.py（判据=verifier_target_fidelity_guard.py：须自 runtime_paths）。

    2026-10-08：原式硬编码 `[记忆共享中心]/脚本中心/doenglingz_guard.py`
      ⇒ 换落点后测的是另一份。改为 ① runtime_paths.devtools → ② 同目录 → ③ 双候选显形。
    """
    import json as _json
    name = "doenglingz_guard.py"
    cands = []
    rp = os.path.expanduser("~/.hermes/doenglingz/runtime_paths.json")
    if os.path.isfile(rp):
        try:
            with open(rp, encoding="utf-8") as fh:
                base = _json.load(fh).get("devtools")
            if base:
                cands.append(os.path.join(base, name))
        except Exception:
            pass
    cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), name))
    cands += [os.path.expanduser("[记忆共享中心]/脚本中心/" + name),
              os.path.expanduser("[记忆共享中心]/脚本中心/" + name)]
    for c in cands:
        if os.path.isfile(c):
            return c
    return cands[0]


GUARD_CORE = _resolve_guard_core()


def extract_last_assistant_text(transcript_path):
    """读 transcript 提取最后一条 assistant 正文。

    2026-09-23 童灵根治：取值路径改走**共享解析层**（原硬编码 `d["message"]["content"]`
    ＝端绑定；同类病在 WB 端已实证 5 例空转）。DSH/CC 嵌套式与 WB 顶层式均由共享层自适应，
    新增端只改共享层一处（守卫编写规范 §3.12 单一入口律）。
    """
    import sys as _sys
    _root = os.path.expanduser("[记忆共享中心]/脚本中心")
    if _root not in _sys.path:
        _sys.path.insert(0, _root)
    try:
        import transcript_reader as _tr
    except Exception:
        return ""
    return _tr.last_assistant_text(transcript_path)


def write_state(text_len, stdout_snippet, error=None):
    """写 DSH 端专属台账（可观测·06规范§1.3 机制在跑不能靠注释自证）。"""
    try:
        state = {
            "last_run": datetime.now().isoformat(timespec="seconds"),
            "text_len": text_len,
            "core_stdout": stdout_snippet[:500] if stdout_snippet else "",
            "error": error or "",
            "host": "dsh",
        }
        Path(STATE_FILE).write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass  # 台账失败不阻塞


def main():
    raw = sys.stdin.buffer.read().decode('utf-8', errors='replace') or "{}"
    try:
        payload = json.loads(raw)
    except Exception:
        payload = {}
    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.exists(transcript_path):
        print(json.dumps({"alarm": False, "error": "no transcript_path"}, ensure_ascii=False))
        write_state(0, "", "no transcript_path")
        return
    text = extract_last_assistant_text(transcript_path)
    if not text:
        print(json.dumps({"alarm": False, "error": "no assistant text in transcript"}, ensure_ascii=False))
        write_state(0, "", "no assistant text")
        return
    # 调共脚本 doenglingz_guard.py --check（stdin 传 JSON {text: ...}·复用全部 scan 逻辑·零改共脚本）
    try:
        result = subprocess.run(
            [sys.executable, GUARD_CORE, "--check"],
            input=json.dumps({"text": text}),
            capture_output=True, text=True, timeout=30,
        )
        stdout = result.stdout.strip()
        write_state(len(text), stdout, None if result.returncode == 0 else f"core exit={result.returncode}")
        # 透传共脚本 stdout（含 alarm JSON）·exit 0 不阻断（提示性扫描·守护自限）
        if stdout:
            print(stdout)
    except subprocess.TimeoutExpired:
        write_state(len(text), "", "core timeout 30s")
        print(json.dumps({"alarm": False, "error": "core timeout"}, ensure_ascii=False))
    except Exception as e:
        write_state(len(text), "", f"core exception: {e}")
        print(json.dumps({"alarm": False, "error": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
