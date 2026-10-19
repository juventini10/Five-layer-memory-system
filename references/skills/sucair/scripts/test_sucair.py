#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_sucair.py — G2 全量回归自动载体（v4.11.0 新建·补 F13：SKILL.md:219"eval-set 全量回归"此前无脚本载体）

覆盖 eval-set 运行时用例中可机械判定的 10 组行为（绑 note_validator 实物 API，非凭印象构造）：
正文定值(R13系)/题库计数一致(R系)/fail-closed/YAML硬闸(R14/R20同族)/builder往返/规则单源(M6系)/
双源同步(#8)/分档定值/收口版本锚/必填守卫。
运行：cd scripts && python3 -m unittest test_sucair -v   （或 python3 -m unittest discover -s scripts -p "test_sucair.py"）
退出码：0=全绿（G2回归通过）；非0=有硬伤，⛔DO NOT 带红交付。
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import note_validator as nv  # noqa: E402


class TestBodyLength(unittest.TestCase):
    """eval-set R13 系·正文600定值（含 v4.10.3 R13 口径注行为）"""

    def test_t1_01_boundary_pass_and_block(self):
        self.assertIsNone(nv.check_body_length("字" * 600), "600字应放行")
        self.assertIsNotNone(nv.check_body_length("字" * 601), "601字应拦截")

    def test_t1_02_label_counted_conservative(self):
        # 口径注坐实：计数自 **原文依据** 标签起算，标签自身计入=保守向
        r = nv.check_body_length("**原文依据**：" + "字" * 600)
        self.assertIsNotNone(r, "带标签600纯内容字应因保守口径被拦")
        self.assertIn("609", r, "实际数应=600+标签9字（口径注在案）")


class TestQuizbank(unittest.TestCase):
    """eval-set 题库边（v4.7.0 消费边）·validate_quizbank"""

    def test_t2_count_mismatch_detected(self):
        fm = {"question_count": 2, "type": "quiz-bank"}
        issues = nv.validate_quizbank(fm, "## Q1 x\n## Q2 y\n## Q3 z")
        self.assertTrue(any("≠" in i for i in issues), "计数不符必须报")

    def test_t3_fail_closed_zero_section(self):
        fm = {"question_count": 0, "type": "quiz-bank"}
        issues = nv.validate_quizbank(fm, "")
        self.assertTrue(any("无 ## Q 题目段" in i for i in issues), "空题段=fail-closed")


class TestYamlHardGate(unittest.TestCase):
    """_yaml_hardcheck：裸双链非法·引号形态合法（v4.6.1 326张事故防线）"""

    def test_t4(self):
        bare = "---\ntitle: 测试\nrelated: [[A]] [[B]]\n---\n正文"
        quoted = '---\ntitle: 测试\nrelated: "[[A]] [[B]]"\n---\n正文'
        self.assertTrue(nv._yaml_hardcheck(bare), "裸双链应被硬闸拦")
        self.assertFalse(nv._yaml_hardcheck(quoted), "引号形态应放行")


class TestFrontmatterRoundTrip(unittest.TestCase):
    """builder/dump/parse 往返恒等（R14/R20 同族机械锚）"""

    def test_t5(self):
        fm = {"title": "T", "topic": "TP", "tags": "a,b", "category": "c"}
        # dump 产出不含 --- 包裹行（实物 docstring 声明）→ 往返须按 parse 入参格式包裹
        text = "---\n" + nv.dump_frontmatter(fm) + "\n---\n正文"
        parsed, _body = nv.parse_frontmatter(text)
        self.assertEqual(parsed.get("title"), "T")
        self.assertEqual(parsed.get("tags"), "a,b")


class TestRuleSingleSource(unittest.TestCase):
    """M6/规则单源：dedup_recall 不自建解析器 + 双源同步 + 定值集合 + 版本锚"""

    def test_t6_no_second_parser(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dedup_recall.py"), encoding="utf-8").read()
        self.assertEqual(src.count("def parse_frontmatter"), 0, "dedup_recall 不得自带第二份解析器")

    def test_t7_dual_source_sync(self):
        cfg = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references", "config.yaml"), encoding="utf-8").read()
        self.assertEqual(nv.CARD_BODY_MAX, 600)
        self.assertIn("≤600字", cfg, "config 投影与常量必须同数（#8改数两处同步）")

    def test_t8_source_type_fixed(self):
        self.assertEqual(nv._SOURCE_TYPE_SET, ("book", "paper", "article-long", "article-short", "thread"))

    def test_t9_schema_anchor(self):
        self.assertEqual(nv.CARD_SCHEMA_VERSION, "读书卡片schema v1.3.4", "v1.3.4 card_id 全池统一+严格机检（2026-10-15 D3根治批·负例证过#S243）")

    def test_t10_required_guard(self):
        issues = nv.validate_card({})
        s = " ".join(issues)
        self.assertIn("book", s)
        names = [f[0] for f in nv.CARD_FIELDS]  # 实物格式：(字段名, 必填bool, 谓词)三元组表
        self.assertTrue("category" in names and "tags" in names,
                        "category/tags 必填须入机检字段集（M6）")


if __name__ == "__main__":
    unittest.main(verbosity=2)
