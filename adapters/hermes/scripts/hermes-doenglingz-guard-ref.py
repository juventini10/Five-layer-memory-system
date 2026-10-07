#!/usr/bin/env python3
"""
hermes-doenglingz-guard-ref.py — Hermes 端数字分身守卫参考调用接口

⛔ 2026-10-01 订正：旧版 main() 只 print 静态字符串，**不读规格书、不调守护本体**——
   属装饰性假机制（06 §1.3 反模式「机制在跑不能靠注释」）。现改为真调本体。

真实承载（⛔本文件不是执行本体）：
  执行本体 = Hermes 用户插件 ~/.hermes/plugins/doenglingz-twin/
    · post_llm_call 钩子 → subprocess doenglingz_guard.py --src hermes（每轮机械·等价 Stop）
本文件用途：安装/排障时**离线手动**跑一次守护三查并落可观测证据。

零复制：只 subprocess 调共脚本，⛔不内联任何判定逻辑。
"""
import datetime
import json
import os
import subprocess
import sys

HOME = os.path.expanduser("~")
GUARD = os.path.join(HOME, "[记忆共享中心]", "开发工具", "doenglingz_guard.py")
SPEC = os.path.join(HOME, "[记忆共享中心]", "数字分身", "童灵·人格规格书.md")
CONFIG_ROOT = os.path.join(HOME, ".hermes", "doenglingz")


def main() -> int:
    env = dict(os.environ)
    # 端隔离：两个键都设（guard.py 只认 WORKBUDDY_CONFIG_DIR）
    env["DOENGLINGZ_CONFIG_DIR"] = CONFIG_ROOT
    env["WORKBUDDY_CONFIG_DIR"] = CONFIG_ROOT
    env["PYTHONIOENCODING"] = "utf-8"
    os.makedirs(CONFIG_ROOT, exist_ok=True)

    text = sys.stdin.read() if not sys.stdin.isatty() else ""
    text = text.strip() or "【手动触发·无文本输入·仅验证挂载与台账落点】"

    evidence = {
        "spec_exists": os.path.isfile(SPEC),
        "spec_path": SPEC,
        "guard_script": GUARD,
        "guard_exists": os.path.isfile(GUARD),
        "config_root": CONFIG_ROOT,
    }

    proc = subprocess.run(
        [sys.executable, GUARD, "--check", "--src", "hermes", "--text", text],
        capture_output=True, text=True, timeout=60, env=env,
    )
    evidence["guard_rc"] = proc.returncode
    evidence["guard_stdout"] = (proc.stdout or "").strip()[:800]
    evidence["ledger"] = os.path.join(CONFIG_ROOT, "doenglingz_guard_state_hermes.json")

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print("[📋 | Hermes 端童灵守护手动触发验证 | %s]" % ts)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
