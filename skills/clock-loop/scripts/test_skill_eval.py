#!/usr/bin/env python3
"""
skill_eval.py 回归测试套件

用法：python3 test_skill_eval.py
     在skill_eval.py所在目录运行
"""

import os
import sys
import json
import re
import tempfile
import unittest

# 确保能import skill_eval
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_eval import (
    WEIGHTS,
    TOTAL_MAX,
    eval_single_number_source,
    eval_cross_file_consistency,
    eval_file_clutter,
    eval_token_budget,
    eval_backup_gate,
    eval_version_uniform,
    evaluate_skill,
    RE_VERSION_BOLD,
    RE_VERSION_COLON,
    verify_dimension_consistency,
)


class TestWeights(unittest.TestCase):
    """权重一致性测试"""

    def test_total_max_is_100(self):
        """权重总和必须=100（Poka-Yoke定值法）"""
        self.assertEqual(TOTAL_MAX, 100)
        self.assertEqual(sum(WEIGHTS.values()), 100)


class TestSharedRegex(unittest.TestCase):
    """共享正则常量测试"""

    def test_version_bold_pattern(self):
        """RE_VERSION_BOLD 匹配 `**版本**：v1.2.3`"""
        m = RE_VERSION_BOLD.search('**版本**：v1.2.3')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), 'v1.2.3')

        m = RE_VERSION_BOLD.search('**版本**: 2.5.0')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '2.5.0')

    def test_version_colon_pattern(self):
        """RE_VERSION_COLON 匹配 `版本：v1.2.3`"""
        m = RE_VERSION_COLON.search('版本：v3.8.6')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), 'v3.8.6')

        m = RE_VERSION_COLON.search('版本: 2.0')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '2.0')


class TestSingleNumberSource(unittest.TestCase):
    """验证⑩ 单一数字源检测"""

    def test_clean_content_passes(self):
        """无数字声明冲突的内容应该满分"""
        content = """# Test Skill

## L1：单层思维
4步流程

## L2：双层思维
8步流程

## L3：深度模式
11步流程
"""
        ratio, detail = eval_single_number_source(content)
        self.assertEqual(ratio, 1.0, f"应该满分，但: {detail}")

    def test_step_count_mismatch_detected(self):
        """同路径步数不一致应该被检出"""
        content = """# Test Skill

## L3：深度模式（11步流程）

L3-全流程共10步完成
"""
        ratio, detail = eval_single_number_source(content)
        self.assertLess(ratio, 1.0, "步数不一致应该被检出")
        self.assertTrue(any('L3' in m for m in detail['mismatches']))

    def test_eval_count_mismatch_detected(self):
        """用例数不一致应该被检出"""
        content = """
这里有18条用例。
另一处写了16条用例。
"""
        ratio, detail = eval_single_number_source(content)
        self.assertLess(ratio, 1.0, "用例数不一致应该被检出")

    def test_g_series_gap_detected(self):
        """G系列跳号应该被检出"""
        content = """
G1 检查项
G3 检查项
G5 检查项
"""
        ratio, detail = eval_single_number_source(content)
        self.assertLess(ratio, 1.0, "G系列跳号应该被检出")

    def test_different_paths_not_mismatched(self):
        """不同子路径的步数不同不算冲突"""
        content = """
L1-第一性原理：4步
L1-抽象建模：4步
L1-批判验证：6步
L2：8步
L3：11步
"""
        ratio, detail = eval_single_number_source(content)
        self.assertEqual(ratio, 1.0, f"不同子路径步数不同不算冲突: {detail}")


class TestCrossFileConsistency(unittest.TestCase):
    """验证⑬ 跨文件声明-执行一致性"""

    def test_no_references_dir(self):
        """无references目录应该返回满分"""
        with tempfile.TemporaryDirectory() as d:
            skill_path = os.path.join(d, 'SKILL.md')
            with open(skill_path, 'w') as f:
                f.write('# Test\n---\nname: test\n---\n')
            ratio, detail = eval_cross_file_consistency(skill_path)
            self.assertEqual(ratio, 1.0)


class TestFileClutter(unittest.TestCase):
    """eval_file_clutter异常处理测试"""

    def test_nonexistent_dir_returns_zero(self):
        """目录不存在时应该返回0分（不是满分！）"""
        ratio, detail = eval_file_clutter('/nonexistent/path/SKILL.md')
        self.assertEqual(ratio, 0.0, "目录读取失败应该返回0分，不是满分1.0")
        self.assertTrue(any('error' in str(d) for d in detail))


class TestTokenBudget(unittest.TestCase):
    """eval_token_budget异常处理测试"""

    def test_nonexistent_file_returns_zero(self):
        """文件不存在时应该返回0分"""
        ratio, lines = eval_token_budget('/nonexistent/file.md')
        self.assertEqual(ratio, 0.0)
        self.assertEqual(lines, 0)


class TestEvaluateSkill(unittest.TestCase):
    """evaluate_skill边界情况测试"""

    def test_empty_file_does_not_crash(self):
        """空文件不应该崩溃"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('')
            f.flush()
            try:
                r = evaluate_skill(f.name)
                self.assertIn('total', r)
            except Exception as e:
                self.fail(f"空文件不应该崩溃: {e}")
            finally:
                os.unlink(f.name)

    def test_frontmatter_only_does_not_crash(self):
        """只有frontmatter不应该崩溃"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('---\nname: test\nversion: 1.0\n---\n# Test')
            f.flush()
            try:
                r = evaluate_skill(f.name)
                self.assertIn('total', r)
            except Exception as e:
                self.fail(f"只有frontmatter不应该崩溃: {e}")
            finally:
                os.unlink(f.name)

    def test_no_references_does_not_crash(self):
        """无references目录不应该崩溃"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write('---\nname: test\nversion: 1.0\n---\n# Test\n这是一个测试')
            f.flush()
            try:
                r = evaluate_skill(f.name)
                self.assertIn('total', r)
            except Exception as e:
                self.fail(f"无references不应该崩溃: {e}")
            finally:
                os.unlink(f.name)


class TestRealSkills(unittest.TestCase):
    """对真实Skill的回归测试——确保修改后分数不退化"""

    def test_clock_loop_score(self):
        """clock-loop自评分数应该=84"""
        skill_dir = os.path.expanduser(
            '~/[记忆共享中心]/技能配置/clock-loop'
        )
        if not os.path.exists(skill_dir):
            self.skipTest('clock-loop目录不存在')
        result = os.popen(
            f'python3 {skill_dir}/scripts/skill_eval.py --check-only {skill_dir}/ 2>&1'
        ).read()
        d = json.loads(result)
        self.assertTrue(d['passed'], f"clock-loop应该通过: {d}")
        # 分数应该≥84（允许未来升级后更高）
        self.assertGreaterEqual(d['total_score'], 84,
                                f"clock-loop分数退化: 期望≥84，实际{d['total_score']}")

    def test_triwich_score(self):
        """triwich评分应该=99"""
        skill_dir = os.path.expanduser(
            '~/[记忆共享中心]/技能配置/triwich'
        )
        if not os.path.exists(skill_dir):
            self.skipTest('triwich目录不存在')
        result = os.popen(
            f'python3 ~/[记忆共享中心]/技能配置/clock-loop/scripts/skill_eval.py --check-only {skill_dir}/ 2>&1'
        ).read()
        d = json.loads(result)
        self.assertTrue(d['passed'], f"triwich应该通过: {d}")
        self.assertGreaterEqual(d['total_score'], 95,
                                f"triwich分数退化: 期望≥95，实际{d['total_score']}")


class TestAdversarialSamples(unittest.TestCase):
    """对抗性样本测试——验证评分器不能被刷分"""

    def test_gs1_perfect_score(self):
        """GS-1完美样本应该≥90分"""
        path = '/tmp/golden_samples/GS-1_perfect/SKILL.md'
        if not os.path.exists(path):
            self.skipTest('GS-1样本不存在')
        result = os.popen(
            f'python3 ~/[记忆共享中心]/技能配置/clock-loop/scripts/skill_eval.py {path} 2>&1'
        ).read()
        m = re.search(r'\|(\d+)/100\|', result)
        if m:
            score = int(m.group(1))
            self.assertGreaterEqual(score, 90,
                f"GS-1完美样本应该≥90分，实际{score}——评分器误杀真实现")

    def test_gs2_attack_score_below_gs1(self):
        """GS-2攻击样本分数应该<GS-1完美样本"""
        gs1_path = '/tmp/golden_samples/GS-1_perfect/SKILL.md'
        gs2_path = '/tmp/golden_samples/GS-2_keyword_stuffing/SKILL.md'
        if not os.path.exists(gs1_path) or not os.path.exists(gs2_path):
            self.skipTest('黄金样本不存在')
        r1 = os.popen(
            f'python3 ~/[记忆共享中心]/技能配置/clock-loop/scripts/skill_eval.py {gs1_path} 2>&1'
        ).read()
        r2 = os.popen(
            f'python3 ~/[记忆共享中心]/技能配置/clock-loop/scripts/skill_eval.py {gs2_path} 2>&1'
        ).read()
        m1 = re.search(r'\|(\d+)/100\|', r1)
        m2 = re.search(r'\|(\d+)/100\|', r2)
        if m1 and m2:
            gs1_score = int(m1.group(1))
            gs2_score = int(m2.group(1))
            self.assertGreater(gs1_score, gs2_score,
                f"GS-1({gs1_score})应该>GS-2({gs2_score})——刷分攻击未被压制")


class TestDimensionConsistency(unittest.TestCase):
    """维度一致性自检测试——v2.8.8新增"""

    def test_consistency_passes_on_current_config(self):
        """当前WEIGHTS和MACRO_DIMENSIONS配置应该自检通过"""
        ok, detail = verify_dimension_consistency()
        self.assertTrue(ok, f"自检失败: {detail}")

    def test_detects_orphan_micro_dimension(self):
        """WEIGHTS中有但MACRO_DIMENSIONS未覆盖的微观维度应被检出"""
        import skill_eval
        original = dict(skill_eval.WEIGHTS)
        try:
            skill_eval.WEIGHTS['orphan_dimension'] = 3
            ok, detail = verify_dimension_consistency()
            self.assertFalse(ok)
            self.assertTrue(any('orphan_dimension' in d for d in detail))
        finally:
            skill_eval.WEIGHTS.clear(); skill_eval.WEIGHTS.update(original)

    def test_detects_weight_mismatch(self):
        """宏观声明权重与微观实际权重不一致应被检出"""
        import skill_eval
        original = dict(skill_eval.MACRO_DIMENSIONS)
        try:
            # 篡改开发规范的声明权重
            micros = skill_eval.MACRO_DIMENSIONS['开发规范'][1]
            skill_eval.MACRO_DIMENSIONS['开发规范'] = (25, micros)  # 故意改成25%，实际19%
            ok, detail = verify_dimension_consistency()
            self.assertFalse(ok)
            self.assertTrue(any('开发规范' in d for d in detail))
        finally:
            skill_eval.MACRO_DIMENSIONS.clear(); skill_eval.MACRO_DIMENSIONS.update(original)

    def test_detects_duplicate_membership(self):
        """微观维度被多个宏观维度重复归属应被检出"""
        import skill_eval
        original = dict(skill_eval.MACRO_DIMENSIONS)
        try:
            micros = list(skill_eval.MACRO_DIMENSIONS['测试覆盖'][1])
            micros.append('causal_chain')  # 故意把causal_chain也归到测试覆盖
            skill_eval.MACRO_DIMENSIONS['测试覆盖'] = (12, micros)
            ok, detail = verify_dimension_consistency()
            self.assertFalse(ok)
            self.assertTrue(any('重复归属' in d for d in detail))
        finally:
            skill_eval.MACRO_DIMENSIONS.clear(); skill_eval.MACRO_DIMENSIONS.update(original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
