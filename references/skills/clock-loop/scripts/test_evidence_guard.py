#!/usr/bin/env python3
"""
evidence_guard.py 回归测试套件（取证锁 L1 证据行锁 + L2 断言计数锁）

设计真源：记忆蓝图/反方向的钟设计哲学/02-实例/物理约束与防误.md §七
用法：python3 test_evidence_guard.py（在evidence_guard.py同目录运行）
"""

# v2.9.12同族根治（2026-09-27·clock-loop自评Loop R1）：v4.12.13的dont_write_bytecode只覆盖了
# test_skill_eval.py——本文件import evidence_guard同样写.pyc污染被评树（修A不修全链）。
# flag须先于一切import设置。
import sys as _sys_guard
_sys_guard.dont_write_bytecode = True
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evidence_guard import (
    verify_evidence_lines,
    count_valid_assertions,
    run_evidence_guard,
    EvidenceLine,
)


# 一段有稳定内容、可被断言引用的被测文本（行号=文本数组下标+1）
SAMPLE_SKILL = """# 样例 Skill
## 阶段一 拆解
这里是被引用的第一处原文。
## 阶段二 评分
第二个被引用的检查点。
## 阶段三 归档
第三个被引用的位置点。
"""


def _lines():
    return SAMPLE_SKILL.splitlines()


class TestEvidenceLineParsing(unittest.TestCase):
    """L1 证据行锁：断言格式解析"""

    def setUp(self):
        self.source = _lines()

    def test_parses_well_formed_assertion(self):
        """合法断言：解析出 检查项ID/行号/原文/judgment"""
        line = "[causal_chain][3][这里是被引用的第一处原文。][✅]"
        ev = EvidenceLine.parse(line)
        self.assertIsNotNone(ev)
        self.assertEqual(ev.check_id, "causal_chain")
        self.assertEqual(ev.line_no, 3)
        self.assertEqual(ev.quote, "这里是被引用的第一处原文。")
        self.assertEqual(ev.judgment, "✅")

    def test_rejects_missing_judgment(self):
        """缺 judgment 的断言拒绝解析"""
        line = "[causal_chain][3][这里是被引用的第一处原文。]"
        self.assertIsNone(EvidenceLine.parse(line))

    def test_rejects_missing_quote(self):
        """缺原文引用的断言拒绝解析"""
        line = "[causal_chain][3][][✅]"
        self.assertIsNone(EvidenceLine.parse(line))


class TestEvidenceLineVerification(unittest.TestCase):
    """L1 证据行锁：行号真实存在 + 原文逐字命中"""

    def setUp(self):
        self.source = _lines()

    def test_valid_quote_at_valid_line(self):
        """行号存在且原文逐字命中 → 通过"""
        ev = EvidenceLine.parse("[causal_chain][2][## 阶段一 拆解][✅]")
        self.assertTrue(ev.verify(self.source))

    def test_fake_line_number_rejected(self):
        """伪造行号（超出文本长度）→ 拒绝"""
        ev = EvidenceLine.parse("[causal_chain][99][## 阶段一 拆解][✅]")
        self.assertFalse(ev.verify(self.source))

    def test_wrong_quote_for_line_rejected(self):
        """引文与行号处原文不符（错置句）→ 拒绝"""
        ev = EvidenceLine.parse("[causal_chain][2][第三个被引用的位置点。][✅]")
        self.assertFalse(ev.verify(self.source))


class TestAssertionCounting(unittest.TestCase):
    """L2 断言计数锁：有效断言统计"""

    def test_valid_assertions_counted(self):
        """格式合法且通过的断言计入有效数"""
        source = _lines()
        lines = [
            "[causal_chain][2][## 阶段一 拆解][✅]",
            "[causal_chain][3][这里是被引用的第一处原文。][✅]",
        ]
        self.assertEqual(count_valid_assertions(lines, source), 2)

    def test_invalid_assertions_not_counted(self):
        """伪造行号/错置引文不计入有效断言"""
        source = _lines()
        lines = [
            "[causal_chain][99][## 阶段一 拆解][✅]",  # 伪造行号
            "[causal_chain][2][第三个被引用的位置点。][✅]",  # 错置引文
        ]
        self.assertEqual(count_valid_assertions(lines, source), 0)

    def test_pure_description_not_counted(self):
        """纯描述文字（非断言格式）不计入"""
        source = _lines()
        lines = ["这条维度整体看起来挺规范的，所以给过", "另一个凭印象的描述"]
        self.assertEqual(count_valid_assertions(lines, source), 0)


class TestRunEvidenceGuard(unittest.TestCase):
    """端到端：run_evidence_guard 聚合计总数与通过态"""

    def sample_locked_result(self):
        """构造一份"看起来已锁"但实际未过取证的 JSON（防伪锁用例）"""
        return json.dumps({"line_ok": True, "count_ok": True})

    def test_valid_lines_give_lock_ok(self):
        """全部有效断言时 guard 通过"""
        source = _lines()
        lines = [
            "[causal_chain][2][## 阶段一 拆解][✅]",
            "[causal_chain][3][这里是被引用的第一处原文。][✅]",
        ]
        result = run_evidence_guard(lines, source, min_assertions=2)
        self.assertTrue(result["passed"])
        self.assertEqual(result["valid"], 2)

    def test_threshold_not_met_gives_lock_fail(self):
        """有效断言低于阈值 → 不通过"""
        source = _lines()
        lines = [
            "[causal_chain][2][## 阶段一 拆解][✅]",
        ]
        result = run_evidence_guard(lines, source, min_assertions=2)
        self.assertFalse(result["passed"])

    def test_fake_line_ok_json_alone_not_accepted(self):
        """防伪：仅链接续的 {line_ok:true} 自我声明 ≠ guard 通过（须重跑取证）"""
        # run_evidence_guard 必须实际取 source/lines 证据，而非信任读入的 is_locked 声明
        declared = json.loads(self.sample_locked_result())
        # 即使 AI 声明 locked=true，我们仍以实测证据为准
        source = _lines()
        lines = [
            "[causal_chain][99][## 阶段一 拆解][✅]",  # 伪造行号
        ]
        result = run_evidence_guard(lines, source, min_assertions=1,
                                    predeclared_locked=declared)
        # 实测不过 → passed 仍为 False，且 recorded 里不带 ai 手写的 locked 态
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)