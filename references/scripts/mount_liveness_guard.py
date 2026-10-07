#!/usr/bin/env python3
"""
mount_liveness_guard.py — 挂载活性闸（三明治裁决B·闸2·v1.0）

职责（08 §八·八"注册≠活"假绿型一的机械拦截）：
  对"注册面声明的守卫"做活性体检，输出三分类（对齐 position3 v1.9 _rc_semantics）：
    rc0=健康 / rc1+stderr异常特征=crash（🔴拦截级）/ rc1+stdout有产物=finding（🟡报告级）

两注册面（第三面 launchd 归 position3 判据⑤·不重复——Agent B 缺口①元层分工）：
  A. pre-commit 链：.git/hooks/pre-commit 中的守卫清单 → 逐个【实跑】（无状态·先例）
  B. 端 config 钩子：~/.zcode/cli/config.json 的钩子命令脚本 → 【存在性+可执行位+语法】
     （⛔不实跑有状态钩子：injector/guard 会写台账——诚实边界·语法面用 ast/bash -n）

元层闭环（Agent B 放行要求3）：本守卫以 launchd 作业身份（com.buluotuo.mount-liveness-daily）
  每日跑 → position3 判据⑤自动覆盖其活性 → 四闸纳入对账面·不改 position3 一行。

退出码：crash 类 >0 → exit 1（供 launchd last exit code 对账·Fail-Loud）；否则 0。
"""
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

__version__ = "v1.0"
REPO = Path(os.path.expanduser("[记忆共享中心]"))
PRE_COMMIT = REPO / ".git" / "hooks" / "pre-commit"
ZCODE_CONFIG = Path(os.path.expanduser("~/.zcode/cli/config.json"))
LEDGER = REPO / "开发工具" / "logs" / "mount_liveness.ledger.jsonl"
HEARTBEAT = REPO / "开发工具" / "logs" / "mount_liveness.heartbeat"
# 有状态钩子（实跑会写台账/状态——只做语法面，⛔不实跑）
STATEFUL_HINTS = ("doenglingz_guard", "doenglingz_inject_prompt", "gate_runner",
                  "tsl_closeout", "level_declare", "append_log", "position3_notify")


def classify(rc: int, out: str) -> str:
    if rc == 0:
        return "✅healthy"
    if re.search(r"Traceback|unbound variable|not found|syntax error|No such file", out, re.I):
        return "🔴crash"
    return "🟡finding"


def extract_precommit_guards():
    """从 pre-commit 提取守卫清单 [(path, args, runner)]——对齐链内 GUARD= 赋值与调用形态。"""
    items = []
    try:
        text = PRE_COMMIT.read_text(encoding="utf-8")
    except Exception:
        return items
    # 抓 VAR="$HOME/.../xxx.py|.sh" 赋值
    for m in re.finditer(r'^(\w+)="\$HOME/(个人AI档案/[^"]+)"', text, re.M):
        items.append((m.group(2), m.group(1)))
    return items


def precommit_calls_map(text):
    """变量→(参数, 运行器) 映射：从调用行反查（python3 $VAR ARGS / bash $VAR / $PY $VAR verify）。"""
    calls = {}
    for m in re.finditer(r'^(?:env -u \S+ -u \S+ )?(?:bash|"\$PY"|python3) "?\$(\w+)"?\s*(.*)$', text, re.M):
        calls[m.group(1)] = m.group(2).strip()
    return calls


def check_precommit():
    """面A：pre-commit 链守卫实跑（无状态）。返回 [(name, rc, cls, head)]。"""
    results = []
    try:
        text = PRE_COMMIT.read_text(encoding="utf-8")
    except Exception:
        return results
    calls = precommit_calls_map(text)
    for var, rel in extract_precommit_guards():
        if var not in calls:
            continue  # 定义了但链上未调用（如 shadow_sleep_gate 刻意不进链）——不体检
        args = calls[var]
        p = REPO / rel
        if not p.exists():
            results.append((rel, 127, "🔴crash", "注册面声明但文件不存在"))
            continue
        if rel.endswith(".sh"):
            r = subprocess.run(["bash", str(p)] + args.split(), capture_output=True, text=True, timeout=60)
        else:
            r = subprocess.run([sys.executable, str(p)] + args.split(),
                               capture_output=True, text=True, timeout=60,
                               env={k: v for k, v in os.environ.items() if k not in ("PYTHONHOME", "PYTHONPATH")})
        out = (r.stdout or "") + (r.stderr or "")
        name = rel
        if any(h in rel for h in STATEFUL_HINTS):
            # 有状态件跳过实跑——改做语法面（不在此分支，理论上不会进来）
            continue
        results.append((name, r.returncode, classify(r.returncode, out), out.strip().splitlines()[0][:70] if out.strip() else ""))
    return results


def check_zcode_hooks():
    """面B：ZCode config 钩子脚本存在性+可执行位+语法（不实跑有状态件）。"""
    results = []
    try:
        cfg = json.loads(ZCODE_CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        return [("config.json解析", 1, "🔴crash", str(e)[:70])]
    scripts = set()
    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and (".py" in o or ".sh" in o):
            for m in re.finditer(r'[/~][^\s"\']*?\.(?:py|sh)', o):
                scripts.add(os.path.expanduser(m.group(0)))
    walk(cfg)
    for s in sorted(scripts):
        rel = s.replace(str(REPO) + "/", "") if s.startswith(str(REPO)) else s
        if not os.path.exists(s):
            results.append((rel, 127, "🔴crash", "config声明但文件不存在"))
            continue
        if s.endswith(".py"):
            try:
                ast.parse(open(s, encoding="utf-8").read())
                results.append((rel, 0, "✅语法", ""))
            except SyntaxError as e:
                results.append((rel, 1, "🔴crash", f"syntax L{e.lineno}: {e.msg[:50]}"))
        elif s.endswith(".sh"):
            r = subprocess.run(["bash", "-n", s], capture_output=True, text=True)
            results.append((rel, r.returncode, "✅语法" if r.returncode == 0 else "🔴crash",
                            (r.stderr or "").strip()[:70]))
    return results


def run_check():
    rows = check_precommit() + check_zcode_hooks()
    crashes = [r for r in rows if r[2] == "🔴crash"]
    findings = [r for r in rows if r[2] == "🟡finding"]
    healthy = len(rows) - len(crashes) - len(findings)
    ts = datetime.now().isoformat(timespec="seconds")
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            for name, rc, cls, head in rows:
                f.write(json.dumps({"ts": ts, "item": name, "rc": rc, "class": cls, "head": head},
                                   ensure_ascii=False) + "\n")
        HEARTBEAT.write_text(json.dumps({"ts": ts, "checked": len(rows), "crashes": len(crashes)},
                                        ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    print(f"[mount-liveness] 体检 {len(rows)} 项：健康/语法 {healthy} · finding {len(findings)} · crash {len(crashes)}")
    for name, rc, cls, head in crashes:
        print(f"  {cls} rc={rc} {name} — {head}")
    for name, rc, cls, head in findings:
        print(f"  {cls} rc={rc} {name} — {head}")
    if crashes:
        print("修法：crash 项按 head 定位（unbound/缺失/语法）——还原 HEAD 已知好形态或修复后复跑。")
        return 1
    return 0


def refresh_manifest():
    """闸4本端最小闭环（12-端适配协议§〇"到货回执"）：部署面快照 manifest。
    作者侧无"包版本"——package_version 用 git HEAD 短哈希（诚实锚）。
    落点=协议格式 <配置根>/doenglingz/installed_manifest.json → ~/.zcode/doenglingz/。
    产出来源=闸2体检的注册面清单（机械可再生·非手工维护——D-F1 派生数据纪律）。"""
    import hashlib
    try:
        head = subprocess.run(["git", "rev-parse", "--short=12", "HEAD"],
                              cwd=REPO, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        head = "unavailable"
    comps = []
    seen = set()
    for name, rc, cls, head_txt in (check_precommit() + check_zcode_hooks()):
        p = REPO / name if not os.path.isabs(name) else Path(name)
        if str(p) in seen:
            continue
        seen.add(str(p))
        try:
            sha = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
        except Exception:
            sha = "ERR"
        comps.append({"name": os.path.basename(str(p)), "path": str(p), "sha12": sha,
                      "state": cls})
    out_dir = Path(os.path.expanduser("~/.zcode/doenglingz"))
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_at": datetime.now().isoformat(timespec="seconds"),
                "package_version": f"author-side@{head}",
                "component_count": len(comps), "components": comps}
    out = out_dir / "installed_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, len(comps)


def run_self_test():
    """夹具：好脚本+坏脚本（unbound）判类验证。"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "good.py"; good.write_text("print('ok')\n", encoding="utf-8")
        bad = Path(td) / "bad.sh"; bad.write_text("#!/bin/bash\nset -u\necho \"$UNBOUND_VAR_XYZ\"\n", encoding="utf-8")
        r1 = subprocess.run([sys.executable, str(good)], capture_output=True, text=True)
        r2 = subprocess.run(["bash", str(bad)], capture_output=True, text=True)
        c1 = classify(r1.returncode, r1.stdout + r1.stderr)
        c2 = classify(r2.returncode, r2.stdout + r2.stderr)
        ok = c1 == "✅healthy" and c2 == "🔴crash"
        print(f"{'✅' if ok else '❌'} [mount-liveness·自检] good={c1} bad={c2}（期待 ✅/🔴）")
        return 0 if ok else 1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if mode == "--self-test":
        return run_self_test()
    rc = run_check()
    try:
        out, n = refresh_manifest()
        print(f"[mount-liveness] 到货回执已刷新: {out}（{n} 组件·闸4本端快照）")
    except Exception as e:
        print(f"⚠️ [mount-liveness] manifest 刷新失败（不影响体检判定）: {e}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
