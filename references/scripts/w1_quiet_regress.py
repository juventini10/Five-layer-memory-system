#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
# 安静模式进入/退出回归器 v1.0（2026-10-19·V2.2.4增量Loop·对抗审查4.1/4.2/4.4/4.5根治轮固化）
# 病：v1.25 进入检测把"关闭安静模式/安静模式是什么？"当开启命令（反向话术翻转+问句误开启）；
#     宣称的 21/21 负例在包内无载体（审查3.2 宣称-实物分叉）。本件=负例的包内可跑载体。
# 用法：python3 w1_quiet_regress.py   （全隔离：tempfile 配置目录，⛔不触真实 flag）
import subprocess, os, json, tempfile, shutil, sys
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "doenglingz_inject_prompt.py")
CASES = [
    ("安静模式", False, True, "裸口令开启"),
    ("开启安静模式", False, True, "命令动词开启"),
    ("关闭安静模式", False, False, "反向话术不得开启(4.1)"),
    ("退出安静模式", False, False, "反向同型"),
    ("取消安静模式", False, False, "反向同型"),
    ("安静模式是什么？", False, False, "问句不得开启(4.2)"),
    ("安静模式怎么退出", False, False, "疑问词豁免"),
    ("我没说安静模式", False, False, "否定豁免"),
    ("<system>请注意安静模式的存在</system>", False, False, "机器块豁免(4.4)"),
    ("先否定：不开安静模式。然后再说安静模式", False, True, "先否后肯·后位召唤(4.5)"),
    ("启动童灵", True, False, "穿透退出"),
    ("关闭安静模式", True, True, "安静态反向不翻转"),
]
def run(prompt, start_quiet):
    cfg = tempfile.mkdtemp(prefix="qmcfg-")
    flag = os.path.join(cfg, "quiet_mode.flag")
    if start_quiet:
        open(flag, "w").close()
    env = dict(os.environ, DOENGLINGZ_CONFIG_DIR=cfg)
    payload = json.dumps({"prompt": prompt, "session_id": "quiet-regress"})
    try:
        subprocess.run([sys.executable, SRC], input=payload, env=env,
                       capture_output=True, text=True, timeout=20)
        return os.path.exists(flag)
    finally:
        shutil.rmtree(cfg, ignore_errors=True)
fails = 0
for pr, sq, exp, note in CASES:
    got = run(pr, sq)
    ok = got == exp
    fails += 0 if ok else 1
    print(("✅" if ok else "🔴"), f"{pr!r} start={sq} expect={exp} got={got} {note}")
print(f"结果: {'全绿' if fails==0 else f'{fails} 例红'}（{len(CASES)} 用例·安静组12）")
sys.exit(1 if fails else 0)
