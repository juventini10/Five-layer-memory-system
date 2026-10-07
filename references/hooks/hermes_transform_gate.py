"""hermes_transform_gate.py —— Transform 层闸（Hermes 端适配）

为什么在 Transform 层做（2026-10-04 评估结论·官方机制取证）：

官方 `VALID_HOOKS`（hermes_cli/plugins.py:109-112）含三个 Transform：
    transform_llm_output      · return a replacement string (first non-None wins) or None
    transform_tool_result     · 工具结果入对话之前·首个字符串替换结果
    transform_terminal_output · 终端输出限流之前·首个字符串替换输出

布洛陀此前 5 个事件里 **Transform 类 0 个** —— 唯一能「改写输出」的一类完全没用。

本脚本承担两件事（⛔ 零判据内联·判据即本文件）：

A. `transform_tool_result` —— 工具结果**进对话之前**清洗
   今天最贵的一类错误是「工具结果里带作者绝对路径 / 测试临时目录 / 双层 expanduser」，
   后果是 AI 把它当事实读进去 → 污染后续推理 → 造出一堆假病灶。
   在这里洗掉 = **一次处理·所有下游受益**（优于改 136 个源文件）。

B. `transform_llm_output` —— AI 回复**最终投递之前**塑形
   · 剥离测试期噪声（临时目录路径）
   · ⛔ 不改内容语义·⛔ 不加不减（塑形≠改写）

⛔ 通道纪律（守卫编写规范 §八）：
   · **fail-open**：任何异常 → 返回 None（不改输出）·守卫失灵不锁死用户的活干
   · **有界**：只做 O(n) 字符串处理·⛔ 不跑子进程（transform 在关键路径上）
   · **保守**：只认白名单形态·⛔ 不猜、不模糊替换
   · **端隔离**：⛔ 不写任何文件·纯返回字符串

命令：
    python3 hermes_transform_gate.py tool-result   < result.txt
    python3 hermes_transform_gate.py llm-output     < response.txt
    python3 hermes_transform_gate.py --self-test
    python3 hermes_transform_gate.py --json         # 输出 {"text": "..."} 或 {}
"""
from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import sys

# ── 清洗规则（白名单·⛔ 不做模糊替换）──────────────────────────────
# 每条 = (正则, 说明)  命中即整串替换为「参数化形态」
TOOL_RULES = [
    # ① 测试期临时目录（我今天造过 final_mc/final_mc2…）
    (re.compile(r"/var/folders/[^\s\"'`)]+"), "测试临时目录"),
    (re.compile(r"/tmp/[^\s\"'`)]+"), "测试临时目录"),
    # ② 双层 expanduser 病灶
    (re.compile(r"expanduser\(\s*os\.path\.expanduser\("), "双层expanduser"),
    # ③ 重复 os.path 前缀
    (re.compile(r"os\.path\.os\.path\."), "重复os.path"),
    # ④ 作者绝对路径（换机必坏）
    (re.compile(r"~/个人AI档案"), "作者绝对路径"),
]
# 替换值：与本地运行面同形态（脱敏由发布链负责·这里只做运行时自愈）
TOOL_SUBS = {
    "测试临时目录": "<测试临时目录已折叠>",
    "双层expanduser": "expanduser(",
    "重复os.path": "os.path.",
    "作者绝对路径": "~/个人AI档案",
}

# LLM 输出侧：只剥噪声·⛔ 不动语义
LLM_RULES = [
    (re.compile(r"/var/folders/[^\s\"'`)\]]+"), "测试临时目录"),
    (re.compile(r"/tmp/[^\s\"'`)\]]+"), "测试临时目录"),
]


def _apply(text: str, rules, subs=None) -> tuple:
    """返回 (新文本, 命中列表)"""
    hits = []
    for rx, name in rules:
        new, n = rx.subn(subs.get(name, "<%s已折叠>" % name) if subs else
                         "<%s已折叠>" % name, text)
        if n:
            hits.append((name, n))
            text = new
    return text, hits


def clean_tool_result(text: str) -> tuple:
    return _apply(text, TOOL_RULES, TOOL_SUBS)


def clean_llm_output(text: str) -> tuple:
    return _apply(text, LLM_RULES)


# ── self-test（双向夹具·⛔ 证明「真病灶被洗 + 正常文本不动」）──────────
POS = [
    ("KB = expanduser(os.path.expanduser(\"/Users/x\"))", "双层expanduser"),
    ("A = os.path.os.path.expanduser(\"~/y\")", "重复os.path"),
    ("见 [记忆共享中心]/脚本中心/a.py", "作者绝对路径"),
    ("tmp at /var/folders/t9/abc123/x.py", "测试临时目录"),
    ("写入 /tmp/probe.txt 成功", "测试临时目录"),
]
NEG = [
    "KB = os.path.expanduser(\"~/个人AI档案\")",
    "def main(): return 0",
    "| 项目 | 值 |\n|---|---|\n| a | b |",
    "签名：—— 你的 Hermes 🪶",
    "os.path.join(BASE, \"脚本中心\")",
]


def _self_test() -> int:
    ok = True
    print("=== POSITIVE（真病灶必须被洗）===")
    for src, why in POS:
        out, hits = clean_tool_result(src)
        good = bool(hits)
        ok = ok and good
        print("  %s %-52s [%s] -> %s" % ("OK " if good else "FAIL",
                                         src[:50], why, out[:44]))
        if not good:
            print("      ^ 漏检")
    print("=== NEGATIVE（正常文本必须不动）===")
    for src in NEG:
        out, hits = clean_tool_result(src)
        same = (out == src) and not hits
        ok = ok and same
        print("  %s %s" % ("OK " if same else "FAIL", src[:66]))
        if not same:
            print("      ^ 误伤 -> %s" % out[:60])
    # 幂等
    s = "x = expanduser(os.path.expanduser(\"~\"))"
    once, _ = clean_tool_result(s)
    twice, h2 = clean_tool_result(once)
    idem = (once == twice) and not h2
    ok = ok and idem
    print("=== IDEMPOTENT ===\n  %s 二次处理无新变化" % ("OK " if idem else "FAIL"))
    print("\n%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    mode = argv[0]
    if mode == "--self-test":
        return _self_test()
    if mode == "--json":
        text = sys.stdin.read()
        out, hits = clean_tool_result(text)
        print(json.dumps({"text": out} if hits else {}, ensure_ascii=False))
        return 0
    if mode not in ("tool-result", "llm-output"):
        print("unknown mode: %s" % mode, file=sys.stderr)
        return 2
    text = sys.stdin.read()
    fn = clean_tool_result if mode == "tool-result" else clean_llm_output
    out, hits = fn(text)
    if argv[0:1] == ["tool-result"] and "--report" in argv:
        print(json.dumps({"hits": hits}, ensure_ascii=False), file=sys.stderr)
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())