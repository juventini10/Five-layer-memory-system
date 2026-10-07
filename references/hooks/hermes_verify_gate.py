#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hermes_verify_gate.py —— 改码验证闸（Hermes `pre_verify` 通道）

## 为什么有它（病灶·可复现·不是「看着不错」）

**病**：本端（Hermes）今日实证三笔「改完没验就交付/交付了才发现没改」的错——
- HE-20261003-006：改了构建产物非真源，改动被生成器静默覆盖，**全程零报错**
- HE-20261003-007：吸收别端只产出文档、零个可跑件，**文档对但行为零变化**
- HE-20261003-008：拿「只读了 1/3」当免责声明提交半成品

共性：**没有一个机制在「我以为改好了」的那一刻提醒我。**

**宿主已给的闸（此前我没用）**：官方 `pre_verify` 事件——
「Fires once per turn **when the agent edited code**, just before it finishes…
a callback can keep the agent going — run a check, defer it, tidy the diff —
instead of letting it stop.」

⇒ 本件 = 把「改完该验什么」从**自觉**变成**机制**。

## 官方契约（逐字对齐·⛔ 凭印象写签名必踩官方警告的坑）

回调签名（docs §`pre_verify`）：
`my_callback(session_id, platform, model, coding, attempt, final_response, changed_paths, **kwargs)`

- `coding: bool` —— 是否在代码工作区（用它 scope，避免误伤非代码回合）
- `attempt: int` —— 本回合已被 nudge 次数（**用它做 one-shot，否则会 nudge 到上限**）
- `changed_paths: list[str]` —— 本回合编辑的文件（排序·此处必非空）
- 返回 `{"action": "continue", "message": "..."}` ⇒ 追加一个 synthetic user turn 让 loop 继续跑
- 官方：**Claude-Code Stop 形态** `{"decision":"block","reason":"..."}`（blocking the stop means *keep going*）也接受
- 官方：连续 continue 由 `agent.max_verify_nudges`（默认 3）兜底 ⇒ **hook 挂死也困不住 loop**

⚠️ **官方两条硬要求，本件逐条遵守**：
1. 「Always accept `**kwargs` for forward compatibility」—— 签名写错字段名会被 WARNING 一次后转 DEBUG（假绿）
2. 「make it idempotent: gate on `attempt`」—— 否则 nudge 到上限

## 本件做什么（只做机械可判的·⛔ 不做主观评价）

判据（三条，全部可机械判；任一命中 ⇒ 要求补验）：
1. **语法未验**：改动的 `.py` 未经 `py_compile`
2. **产品未验**：改动的产物路径（package）未经真源-产物对账（本端已有 `pkg_claim_audit.py` 可复用）
3. **闭环未验**：本回合既没跑过 `terminal`（=没有任何实跑证据）又声称「已修复/已完成」

⚠️ **本件⛔ 不阻断、只 nudge**：符合官方「observer 不裁决」+ 02 规范「只观察不裁决」。
判定为**疑似未验**才 nudge；确认未验不成立则静默放行（⛔ 不刷屏·铁律-021）。

## 隔离压测（铁律-014：未隔离验证绝不直跑真实文件）

```bash
python3 hermes_verify_gate.py --self-test        # 变异体双向夹具
python3 hermes_verify_gate.py --dry-run --json    # 只判不打
```
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from typing import Any

VERSION = "v1.0.0"
CODE_EXT = (".py", ".sh", ".js", ".ts", ".tsx", ".jsx")
# 声称已完成的措辞（⛔ 只认明确的完成声明，不做语气推断）
CLAIM_RE = re.compile(r"(已修复|已完成|已通过|已落地|已生效|全部通过|验证通过)")
# 本回合实跑证据的工具名（与 Hermes 内置工具名对齐）
EXEC_TOOLS = {"terminal", "execute_code"}


# ── 判据 1：改动的 .py 语法是否可编译（机械·零歧义）──────────────
def py_syntax_ok(path: str) -> tuple[bool, str]:
    try:
        with open(path, "rb") as fh:
            ast.parse(fh.read(), filename=path)
        return True, ""
    except SyntaxError as e:
        return False, "语法错误 line %s: %s" % (e.lineno, e.msg)
    except Exception as e:                      # 编码/IO 类：不算语法红
        return True, ""


# ── 判据 2：产物路径是否已过真源-产物对账（复用既有守卫·⛔不另造）──
_PKG_AUDIT = os.path.expanduser("[记忆共享中心]/脚本中心/pkg_claim_audit.py")


def product_audited(path: str) -> bool:
    """改的是不是构建产物？是 ⇒ 要求已跑过 pkg_claim_audit。

    ⛔ **不在本件里复制产物清单**（那会变成第二本账·HE-006 同族病）：
    真源↔产物映射唯一真源 = `pkg_claim_audit.generated_artifact_roots()`。
    取不到 ⇒ 返回 True（不误报红·fail-open·判据缺席≠违规）。
    """
    if not os.path.isfile(_PKG_AUDIT):
        return True
    try:
        import importlib.util as il
        spec = il.spec_from_file_location("pkg_claim_audit", _PKG_AUDIT)
        if spec is None or spec.loader is None:
            return True
        mod = il.module_from_spec(spec)
        spec.loader.exec_module(mod)
        pkg_root = os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包")
        roots = mod.generated_artifact_roots(pkg_root)   # 取不到会抛(FileNotFoundError)
    except Exception:
        return True                                  # 判据缺席 ⇒ 不报红
    rel = os.path.relpath(path, pkg_root)
    for prefix in roots:
        if rel.startswith(prefix):
            return False                              # 是产物 ⇒ 需对账
    return True


# ── 主判据 ────────────────────────────────────────────────────────
def evaluate(*, changed_paths: list[str], final_response: str,
             tools_used: list[str], turn_id: str = "") -> dict[str, Any]:
    """返回 {'action': 'continue'|'pass', 'message': str, 'reasons': [...]}"""
    reasons: list[str] = []

    # ⚠️ **先决判据：本回合没改任何文件 ⇒ 三条判据全部不适用 ⇒ 直接 pass**
    # （自测负例2 当场抓到的真 bug：「无改动 + 声称已完成」曾误报 continue。
    #   根因：判据③缺 `changed_paths` 非空前置 ⇒ 「没改文件却声称完成」被当成
    #   「改完没验」。⛔ 假红比漏红更坏——守卫自己误报，会被当噪音整体关掉。）
    if not changed_paths:
        return {"action": "pass", "message": "", "reasons": [],
                "checked": 0, "note": "本回合无文件改动·三条判据均不适用"}

    py_bad = [p for p in changed_paths if p.endswith(".py")
              and not py_syntax_ok(p)[0]]
    for p in py_bad:
        reasons.append("改动 %s 语法不可编译（%s）" % (os.path.basename(p),
                                                  py_syntax_ok(p)[1]))

    prod = [p for p in changed_paths if not product_audited(p)]
    if prod:
        reasons.append("改动落在**构建产物**上（%s）——会被下次构建覆盖回去，"
                       "须改真源并跑 pkg_claim_audit 对账"
                       % os.path.basename(prod[0]))

    if not tools_used and CLAIM_RE.search(final_response or ""):
        reasons.append("回复含「已修复/已完成」类完成声明，但本回合**无任何实跑证据**"
                       "（未调用 terminal/execute_code）")

    if not reasons:
        return {"action": "pass", "message": "", "reasons": [],
                "checked": len(changed_paths)}

    lines = [
        "🛑 布洛陀改码验证闸（hermes_verify_gate %s）—— 检测到「疑似未验」，"
        "请先补以下机械判据再宣告完成：" % VERSION,
        "",
    ]
    lines += ["  %d. %s" % (i + 1, r) for i, r in enumerate(reasons)]
    lines += [
        "",
        "补验方式：跑对应命令 → 把真实输出贴进回复（⛔ 不接受「应该没问题」）。",
        "本闸只 nudge 不阻断（符合 observer 不裁决纪律）；"
        "若本回合已确实验过但闸未识别，在回复中显式说明「已跑 XXX·输出 YYY」。",
    ]
    return {"action": "continue", "message": "\n".join(lines),
            "reasons": reasons, "checked": len(changed_paths)}


# ── Hermes plugin 入口 ─────────────────────────────────────────────
def _mk_hook():
    def _pre_verify(session_id: str = "", platform: str = "", model: str = "",
                    coding: bool = False, attempt: int = 0,
                    final_response: str = "", changed_paths: list[str] | None = None,
                    **kwargs: Any) -> dict | None:
        # 官方硬要求①：非代码回合不 scope（本端全程在代码仓库，但仍按官方口径判）
        if not coding:
            return None
        # 官方硬要求②：one-shot，否则 nudge 到 max_verify_nudges 上限
        if attempt:
            return None
        tools_used = list(kwargs.get("_buluotuo_tools_used") or [])
        verdict = evaluate(changed_paths=list(changed_paths or []),
                           final_response=final_response or "",
                           tools_used=tools_used, turn_id=session_id)
        if verdict["action"] == "pass":
            return None
        return {"action": "continue", "message": verdict["message"]}
    return _pre_verify


def register(ctx):            # noqa: N802 - 宿主要求的接口名
    ctx.register_hook("pre_verify", _mk_hook())


# ── 自测（变异体双向夹具·铁律-014 隔离压测）─────────────────────────
def self_test() -> int:
    T = tempfile.mkdtemp(prefix="hvg_")
    ok_py = os.path.join(T, "good.py")
    bad_py = os.path.join(T, "bad.py")
    with open(ok_py, "w") as f:
        f.write("x = 1\n")
    with open(bad_py, "w") as f:
        f.write("def f(:\n")

    cases = [
        ("正例1 语法坏 → 应 continue", dict(
            changed_paths=[bad_py], final_response="改完了",
            tools_used=["terminal"]), "continue"),
        ("正例2 无实跑却声称完成 → 应 continue", dict(
            changed_paths=[ok_py], final_response="✅ 已修复完成",
            tools_used=[]), "continue"),
        ("正例3 改产物 → 应 continue", dict(
            changed_paths=[os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包"
                "/references/skills/restore-my-skills.sh")],
            final_response="改了", tools_used=["terminal"]), "continue"),
        ("负例1 语法好+有实跑+无完成声明 → 应 pass", dict(
            changed_paths=[ok_py], final_response="先看一下这个文件",
            tools_used=["terminal"]), "pass"),
        ("负例2 无改动 → 应 pass", dict(
            changed_paths=[], final_response="已修复完成",
            tools_used=[]), "pass"),
        ("负例3 有实跑+完成声明 → 应 pass", dict(
            changed_paths=[ok_py], final_response="已修复，夹具 rc=0",
            tools_used=["terminal"]), "pass"),
    ]
    fails = 0
    for name, kw, want in cases:
        got = evaluate(**kw)["action"]
        ok = got == want
        fails += (0 if ok else 1)
        print("  %s %-46s want=%-8s got=%s" % ("✅" if ok else "❌", name, want, got))
    print("\n%s  self-test: %d/%d" % ("✅ 通过" if not fails else "❌ 失败",
                                      len(cases) - fails, len(cases)))
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    payload = {"changed_paths": [], "final_response": "", "tools_used": []}
    if not sys.stdin.isatty():
        try:
            payload.update(json.loads(sys.stdin.read() or "{}"))
        except Exception:
            pass
    v = evaluate(**payload)
    print(json.dumps(v, ensure_ascii=False, indent=2))
    return 1 if v["action"] == "continue" else 0


if __name__ == "__main__":
    sys.exit(main())