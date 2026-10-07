#!/usr/bin/env python3
"""执行证据链路取证锁（clock-loop §七 L1 证据行锁 + L2 断言计数锁）

设计真源：记忆蓝图/反方向的钟设计哲学/02-实例/物理约束与防误.md §七
定位：对既有机制的"检测落地空缺"补强（L3/L4 已由 skill_eval 物理锁定，本域补执行动作本身）：
  - L1 证据行锁：断言 [检查项ID][行号][原文逐字匹配][✅❌] 中，行号必须真实存在、原文逐字符命中、judgment 非空
  - L2 断言计数锁：有效断言 ≥ 阈值（默认80），纯描述文字不算
防御目标：把偷懒的"绕过成本"抬到 > 遵守成本，且绕过必留痕。
⛔ L1 只验"行真+原文真"，不验 judgment 对错（对错归子Agent/你终审）。
⛔ 纯 AI 环境自觉点消灭不了——本锁不称"杜绝"，只保证取样证必穿帮。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import re
import sys


class EvidenceLine:
    """单条 L1 证据行：[check_id][line_no][quote][judgment]"""

    _PATTERN = re.compile(
        r'\[([A-Za-z0-9_]+)\]\[(\d+)\]\[([^\]]*)\]\[(✅|❌)\]'
    )

    def __init__(self, check_id, line_no, quote, judgment):
        self.check_id = check_id
        self.line_no = line_no
        self.quote = quote
        self.judgment = judgment

    @classmethod
    def parse(cls, line):
        m = cls._PATTERN.match(line.strip())
        if not m:
            return None
        check_id, line_no, quote, judgment = m.groups()
        if not quote:
            return None
        return cls(check_id, int(line_no), quote, judgment)

    def verify(self, source_lines):
        """校验行号真实存在 + 原文逐字命中（接触法·原话锚点）。"""
        idx = self.line_no - 1
        if idx < 0 or idx >= len(source_lines):
            return False
        return source_lines[idx] == self.quote


def _extract_evidence_lines(text):
    """从原始文本中抽取所有 EvidenceLine；非断言行→None 跳过。"""
    out = []
    for raw in text.splitlines() if isinstance(text, str) else text:
        ev = EvidenceLine.parse(raw)
        if ev is not None:
            out.append(ev)
    return out


def count_valid_assertions(lines, source_lines):
    """统计有效断言数：格式合法 + 行号存在 + 原文命中。纯描述不计。"""
    valid = 0
    for raw in lines:
        ev = EvidenceLine.parse(raw)
        if ev is not None and ev.verify(source_lines):
            valid += 1
    return valid


def verify_evidence_lines(lines, source_lines):
    """逐条校验证据行，返回 [(EvidenceLine|None, 布尔通过)]。"""
    return [(ev, ev.verify(source_lines)) if ev else (None, False)
            for ev in _extract_evidence_lines(lines)]


def run_evidence_guard(lines, source_lines, min_assertions=80,
                       predeclared_locked=None):
    """端到端取证：L1逐行校验 + L2有效断言计数 + 阈值门。

    predeclared_locked：外部传入的"自述已锁"JSON（如 {line_ok:true}）。
    ⛔防伪：不信任该声明，一律以实测证据为准重新取证。
    """
    parsed = [ev for ev in _extract_evidence_lines(lines) if ev is not None]
    valid = count_valid_assertions(lines, source_lines)
    all_lines_ok = all(ev.verify(source_lines) for ev in parsed)
    passed = all_lines_ok and valid >= min_assertions
    return {
        "passed": bool(passed),
        "valid": valid,
        "total_assertions": len(parsed),
        "min_assertions": min_assertions,
        "line_ok": bool(all_lines_ok),
        "count_ok": bool(valid >= min_assertions),
        # 防伪锁结论：AI 手写的 locked 声明一律不采信，以实测为准
        "sealed_from_evidence": bool(passed),
    }


if __name__ == "__main__":
    # CLI：python3 evidence_guard.py <断言文件> <源文本> [min_assertions]
    usage = "用法: evidence_guard.py <断言文件> <源文本文件> [min_assertions]"
    if len(sys.argv) < 3:
        print(usage, file=sys.stderr)
        sys.exit(2)
    src_text = open(sys.argv[2], encoding='utf-8').read().splitlines()
    lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
    min_assertions = int(sys.argv[3]) if len(sys.argv) > 3 else 80
    result = run_evidence_guard(lines, src_text, min_assertions)
    print(regex_dump(result))
    sys.exit(0 if result["passed"] else 1)


def regex_dump(result):
    """结构化的 CLI 输出（供 shell 端 exit code 拦截 + 人读）。"""
    return (
        f"已取证断言行: {result['total_assertions']}\n"
        f"有效断言: {result['valid']} / 阈值 {result['min_assertions']}\n"
        f"evidence_lines_ok: {result['line_ok']} "
        f"(count_ok: {result['count_ok']})\n"
        f"sealed_from_evidence: {result['sealed_from_evidence']}"
    )