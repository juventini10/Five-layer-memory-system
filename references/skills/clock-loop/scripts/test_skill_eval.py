#!/usr/bin/env python3
"""
skill_eval.py 回归测试套件

用法：python3 test_skill_eval.py
     在skill_eval.py所在目录运行
"""
# v2.9.11 同步（2026-09-27）：回归是自污染源——本文件 import skill_eval 时会写其 .pyc，
# flag 须在 import 前生效（与 skill_eval.py 同款最高位设置）。
try:
    import sys as _sys_guard
    _sys_guard.dont_write_bytecode = True
except Exception: pass
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import shutil
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
    _check_refs_index_section,
    eval_direction_gate_advisory,
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
        """RE_VERSION_BOLD 匹配 `**版本**：v1.2.3`（test_*已从版本扫描排除·自匹配无害＝#185⑤）"""
        m = RE_VERSION_BOLD.search('**版本**：v1.2.3')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), 'v1.2.3')

        m = RE_VERSION_BOLD.search('**版本**: 2.5.0')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), '2.5.0')

    def test_version_colon_pattern(self):
        """RE_VERSION_COLON 匹配 `版本：vX.Y.Z` 形态（示例占位·防版本扫描自匹配＝#185⑤）"""
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


class TestRefsIndexSection(unittest.TestCase):
    """验证⑬-6 references 索引段结构强制（v4.9.0 L1候选1·三子查正负例）"""

    def _mk(self, d, index_section, with_eval_set=False, extra_md=None):
        """构造 SKILL.md + references 目录，返回 (content, refs_dir)"""
        refs = os.path.join(d, 'references')
        os.makedirs(refs, exist_ok=True)
        files = ['alpha.md', 'beta.md']
        if with_eval_set:
            files.append('eval-set.md')
        if extra_md:
            files.extend(extra_md)
        for fn in files:
            with open(os.path.join(refs, fn), 'w') as f:
                f.write('# 文件\n')
        return ('# Test\n---\nname: test\nversion: 1.0\n---\n' + index_section), refs

    def test_complete_positive(self):
        """正例：索引段存在+登记全+声明用例数 → passed且increment"""
        with tempfile.TemporaryDirectory() as d:
            idx = (
                '## references/ 目录索引\n\n'
                '| 文件 | 用途 |\n|---|---|\n'
                '| `alpha.md` | A |\n'
                '| `beta.md` | B |\n'
                '| `eval-set.md` | 评估集（用例总数 5 条） |\n'
            )
            content, refs = self._mk(d, idx, with_eval_set=True)
            r = _check_refs_index_section(content, refs)
            self.assertTrue(r['passed'], f"正例应通过: {r['detail']}")
            self.assertTrue(r['increment'], "正例应计通过")

    def test_missing_index_section_negative(self):
        """负例1：有顶层 .md 但无专用索引段 → 挂"""
        with tempfile.TemporaryDirectory() as d:
            refs = os.path.join(d, 'references')
            os.makedirs(refs, exist_ok=True)
            with open(os.path.join(refs, 'alpha.md'), 'w') as f:
                f.write('# A\n')
            content = '# Test\n---\nname: test\n---\n正文无索引段\n'
            r = _check_refs_index_section(content, refs)
            self.assertFalse(r['passed'], "缺索引段应失败")
            self.assertIsNotNone(r['mismatch'])

    def test_unregistered_top_md_negative(self):
        """负例2：索引段漏登记顶层 .md → 挂"""
        with tempfile.TemporaryDirectory() as d:
            idx = (
                '## references/ 目录索引\n\n'
                '| 文件 | 用途 |\n|---|---|\n'
                '| `alpha.md` | A |\n'
            )
            content, refs = self._mk(d, idx, extra_md=['gamma.md'])
            r = _check_refs_index_section(content, refs)
            self.assertFalse(r['passed'], "漏登记顶层md应失败")
            self.assertIn('gamma.md', r['mismatch'])

    def test_eval_set_count_undeclared_negative(self):
        """负例3：eval-set.md 存在但索引段无用例数声明 → 挂"""
        with tempfile.TemporaryDirectory() as d:
            idx = (
                '## references/ 目录索引\n\n'
                '| 文件 | 用途 |\n|---|---|\n'
                '| `alpha.md` | A |\n'
                '| `eval-set.md` | 评估集 |\n'
            )
            content, refs = self._mk(d, idx, with_eval_set=True)
            r = _check_refs_index_section(content, refs)
            self.assertFalse(r['passed'], "有eval-set而无用例数声明应失败")
            self.assertIn('用例数', r['mismatch'])

    def test_subdir_only_na_neutral(self):
        """na：references 只有子目录无顶层 .md → 中性通过不计分（不误伤）"""
        with tempfile.TemporaryDirectory() as d:
            refs = os.path.join(d, 'references')
            os.makedirs(os.path.join(refs, 'sub'), exist_ok=True)
            content = '# Test\n---\nname: test\n---\n'
            r = _check_refs_index_section(content, refs)
            self.assertTrue(r['passed'], "无顶层md应中性通过")
            self.assertFalse(r['increment'], "na态不计通过")

    def test_no_refs_dir_na_neutral(self):
        """na：无 references 目录 → 中性通过不计分"""
        with tempfile.TemporaryDirectory() as d:
            content = '# Test\n---\nname: test\n---\n'
            r = _check_refs_index_section(content, os.path.join(d, 'references'))
            self.assertTrue(r['passed'])
            self.assertFalse(r['increment'])


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
        ratio, lines, _d5 = eval_token_budget('/nonexistent/file.md')
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

    def setUp(self):
        # v3.55.1批6h（#24/.phaseX_last_run.json反复被覆盖根治）：真实Skill评估会覆写
        # scripts/.phaseX_last_run.json（运行时状态）——备份并于tearDown恢复，止住测试污染运行时
        self._rt = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.phaseX_last_run.json')
        self._bak = None
        if os.path.exists(self._rt):
            self._bak = self._rt + '.testbak'
            shutil.copy2(self._rt, self._bak)

    def tearDown(self):
        if self._bak and os.path.exists(self._bak):
            shutil.move(self._bak, self._rt)


    def test_position_risk_direct(self):
        """v4.17.0 C-08（双盲第11次）：eval_position_risk 此前无直接单测·补正负例"""
        import skill_eval
        pos = "行1\n" * 4 + "⚠️ 铁律声明：路径前置\n" + "x\n" * 44
        self.assertEqual(skill_eval.eval_position_risk(pos), 1.0, "前50行含铁律/⛔应判1.0")
        neg = "普通开头" * 60
        self.assertEqual(skill_eval.eval_position_risk(neg), 0.0, "无关键前置应判0.0")
        edge = "y\n" * 50 + "⛔DO NOT\n" + "z\n" * 10
        self.assertEqual(skill_eval.eval_position_risk(edge), 0.0, "信号在50行外判0")

    def test_clock_loop_score(self):
        """clock-loop自评：v3.31.3根改后 d5仅标注不否决 → passed=True / honest_flags=[]（v3.31.6等级根治后含grade字段）"""
        skill_dir = os.path.expanduser(
            '~/[记忆共享中心]/技能配置/clock-loop'
        )
        if not os.path.exists(skill_dir):
            self.skipTest('clock-loop目录不存在')
        # v4.17.0 C-02（双盲第11次）hermetic 化·如实口径（R复核N-1修正原过度声明）：
        # cwd=临时目录只隔离 cwd 基写方；skill_eval 存在 __file__ 基写方（L4745 phasex_dir/
        # L2620 advisory 同源），沙箱内生产 scripts/ 仍会被覆写/追加——phaseX 内容受本类
        # setUp/tearDown testbak 备份还原保护（内容恒等·mtime 会变），advisory 为 gitignore
        # 历史统计非评估真相源。彻底根治=--no-side-effects 开关（交接待办#4）。
        import subprocess as _sp, tempfile as _tf
        with _tf.TemporaryDirectory() as _td:
            _r = _sp.run(['python3', os.path.join(skill_dir, 'scripts', 'skill_eval.py'),
                          '--check-only', skill_dir + '/'],
                         cwd=_td, capture_output=True, text=True,
                         env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            result = _r.stdout + _r.stderr
        d = json.loads(result)
        # v3.31.3根改：d5行数档位仅标注不否决可用性（你拍板"长度不否决"）→ 诚实章无红字
        self.assertTrue(d['raw_pass'], f"clock-loop raw_pass应该为True（旧口径≥70）: {d}")
        self.assertTrue(d['passed'], f"clock-loop passed应该为True（v3.31.3后d5不否决·红字应为空）: {d}")
        self.assertEqual(d['honest_flags'], [], f"clock-loop 红字应为空: {d['honest_flags']}")
        self.assertEqual(d.get('grade'), 'S', f"clock-loop 机械grade应为S（v3.31.6等级唯一真相源）: {d.get('grade')}")
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
        # v4.17.0 C-02 同类扫描续（本用例=15:44 生产写真相 culprit·cwd=CL 下 skill_eval
        # 的 'scripts/.advisory_history.jsonl' 相对路径与 phaseX 写方均落生产）→ 同款沙箱化
        _skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        import subprocess as _sp2, tempfile as _tf2
        with _tf2.TemporaryDirectory() as _td2:
            _r2 = _sp2.run(['python3', os.path.join(_skill_root, 'scripts', 'skill_eval.py'),
                            '--check-only', skill_dir + '/'],
                           cwd=_td2, capture_output=True, text=True,
                           env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            result = _r2.stdout + _r2.stderr
        d = json.loads(result)
        self.assertTrue(d['passed'], f"triwich应该通过: {d}")
        self.assertGreaterEqual(d['total_score'], 93,
        # 基线95→93（2026-08-30马拉松实录：triwich v3.15.0键铸造内容合法增长致静态分94·守卫意图=拦评估器退化非锁死历史分·record_fix#MF-20260830-01）
                                f"triwich分数退化: 期望≥93，实际{d['total_score']}")


def _gs_path(name):
    """黄金样本路径解析（v3.43.1 根治）：
    ① 相对本脚本位置推导——⛔不硬编码 ~ 绝对路径（换机/换用户即静默skip·#15）
    ② 兼容 SKILL.sample.md 与 SKILL.md 两种命名——v3.41.0 为"防评估器误发现"改名后
      本测试未同步 → 两个对抗测试静默 skipTest 约 6 天而套件仍报 OK（#12·2026-09-04 git+实跑双重取证）
    Returns (path_or_None, dir_exists: bool)——dir_exists=True 但 path=None 即"目录在而样本缺"，
    调用方必须 FAIL 而⛔不得 skip（样本缺失=防线消失，与"非开发机无此目录"是两回事）。
    """
    gs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'golden_samples', name)
    if not os.path.isdir(gs_dir):
        return None, False
    for fn in ('SKILL.sample.md', 'SKILL.md'):
        p = os.path.join(gs_dir, fn)
        if os.path.exists(p):
            return p, True
    return None, True


class TestAdversarialSamples(unittest.TestCase):
    """对抗性样本测试——验证评分器不能被刷分

    v3.43.1 根治四项（2026-09-04 实测实锤·全部改为 import 直调 evaluate_skill）：
      #12 文件名漂移→_gs_path() 兼容 SKILL.sample.md/SKILL.md
      #14 输出格式物理依赖→⛔不再 os.popen+正则抓 stdout 表格（旧写法 `if m:` 才断言，
          格式一变则 m=None → 无断言 → 测试报 ok 而对抗验证静默失效）
      #15 绝对路径硬编码→相对脚本位置推导
      #18 静默 skip→目录在而样本缺失时 FAIL（仅目录整体不存在才 skip）
    """

    def test_gs1_perfect_score(self):
        """GS-1完美样本应该≥90分（import直调·断言无条件执行）"""
        from skill_eval import evaluate_skill
        path, dir_exists = _gs_path('GS-1_perfect')
        if not dir_exists:
            self.skipTest('golden_samples/GS-1_perfect 目录不存在（非开发机）')
        self.assertIsNotNone(path, 'GS-1_perfect 目录存在但无 SKILL.sample.md/SKILL.md——'
                                  '⛔不得静默skip（对抗验证是评估器天花板的唯一防线·#12教训）')
        r = evaluate_skill(path)
        self.assertGreaterEqual(r['total'], 90,
            f"GS-1完美样本应该≥90分，实际{r['total']}——评分器误杀真实现")

    def test_gs2_attack_score_below_gs1(self):
        """GS-2攻击样本分数应该<GS-1完美样本（import直调·断言无条件执行）"""
        from skill_eval import evaluate_skill
        p1, d1 = _gs_path('GS-1_perfect')
        p2, d2 = _gs_path('GS-2_keyword_stuffing')
        if not (d1 and d2):
            self.skipTest('黄金样本目录不存在（非开发机）')
        self.assertIsNotNone(p1, 'GS-1 目录在但样本文件缺失——⛔不得静默skip')
        self.assertIsNotNone(p2, 'GS-2 目录在但样本文件缺失——⛔不得静默skip')
        s1 = evaluate_skill(p1)['total']
        s2 = evaluate_skill(p2)['total']
        self.assertGreater(s1, s2, f"GS-1({s1})应该>GS-2({s2})——刷分攻击未被压制")

    def test_gs2_is_real_keyword_stuffing_attack(self):
        """GS-2重建（2026-09-05·#215配方·~478行结构完整）：行数断言转为正常断言（v3.44.0标记的expectedFailure随重建摘除·#13形态错位已修）"""
        """⚠️已知未达标（X级方案待办）——用 expectedFailure **显式标记**，⛔不用 skipTest（skip会静默·#12教训）。

        实测（2026-09-04）：GS-2 仅 **12 行**，53分失分构成中 alternatives_considered/eval_set_gate/
        five_level_annotations/fuse_mechanism/deliverable_definition/position_risk/yaml_required_fields
        共失38分——**失分主因是"该有的段落/文件全没有"，不是"关键词堆砌被识别并压制"**。
        所以上面那条 assertGreater 只证明了"12行残缺 < 551行完整"（平凡真相），
        证明不了本类 docstring 宣称的"验证评分器不能被刷分"。
        真对抗样本应：行数与GS-1相当（结构完整）+ 各段齐全但内容为关键词堆砌
        ＝ADR-005"5分钟构造的样本能拿86分"的攻击形态。
        重构GS-2后本测试应转为正常断言并摘掉 expectedFailure。"""
        from skill_eval import evaluate_skill
        p1, _ = _gs_path('GS-1_perfect')
        p2, _ = _gs_path('GS-2_keyword_stuffing')
        if not (p1 and p2):
            self.skipTest('黄金样本缺失')
        l1 = evaluate_skill(p1)['lines']
        l2 = evaluate_skill(p2)['lines']
        # 结构完整性判据：对抗样本行数须≥金样本的50%（否则失分来自"缺段落"而非"堆砌被压制"）
        self.assertGreaterEqual(l2, l1 * 0.5,
            f'GS-2仅{l2}行 vs GS-1 {l1}行——不是结构完整的关键词堆砌，归因不纯')

        # v3.54.2批6g（A30/#216首落地·防假阴）：重建GS-2攻击面天花板——评估器放宽判据致任一维度超阈=回归报警
        r2 = evaluate_skill(p2)
        s2 = r2['scores']
        ceilings = {'alternatives_considered': 3, 'fuse_mechanism': 4, 'eval_set_gate': 6,
                    'deliverable_definition': 5, 'five_level_annotations': 5, 'trigger_conditions': 7}
        for k, cap in ceilings.items():
            got = s2.get(k)
            self.assertIsNotNone(got, f'GS-2: 无检查项{k}')
            self.assertLessEqual(got, cap, f'GS-2/{k}={got}超过攻击天花板{cap}——评估器判据被放宽（防假阴回归）')
        self.assertLessEqual(r2['total'], 83, f'GS-2总分{r2["total"]}超天花板83（基线82）——抗刷分能力退化')


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


class TestFixtures(unittest.TestCase):
    """v3.15.0 P3: fixtures自动发现回归（双盲误判固化区+负控制区·见fixtures/README.md）"""

    REAL_SKILL_NAMES = {'triwich', 'daily-buddy', 'growth-box', 'system-logger',
                        'awaken-memory-system', 'meta-aletheia', 'shall-we-talk',
                        'sucair', 'clock-loop'}

    def test_fixture_names_not_colliding(self):
        """v4.11.1 防再犯（用户端 F1 取证四·2026-09-20）：评测夹具的 frontmatter name
        ⛔禁冒用真实技能名——夹具随包分发后在用户机技能扫描路径下形成同名候选
        （triwich 曾 3 候选：权威源 + GS-1 样本 SKILL.md/SKILL.sample.md·用户机
        单次注入清单观测到命中非权威源）。NC001 用 nc-sample 是正确示范。"""
        import re
        base = os.path.dirname(os.path.abspath(__file__))
        scan_dirs = [os.path.join(base, 'fixtures'),
                     os.path.join(base, '..', 'golden_samples')]
        bad = []
        for d in scan_dirs:
            if not os.path.isdir(d):
                continue
            for root, dirs, fs in os.walk(d):
                for fn in fs:
                    if not fn.startswith('SKILL'):
                        continue
                    p = os.path.join(root, fn)
                    with open(p, encoding='utf-8', errors='ignore') as _fh:
                        head = _fh.read()[:600]
                    m = re.search(r'^name:\s*(\S+)', head, re.M)
                    if m and m.group(1) in self.REAL_SKILL_NAMES:
                        bad.append(f"{os.path.relpath(p, base)}: name={m.group(1)}")
        self.assertEqual(bad, [],
                         f'评测夹具 name 冒用真实技能名（随包分发=技能注册表分叉候选）: {bad}')

    def test_all_fixtures(self):
        fx_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
        if not os.path.isdir(fx_dir):
            self.skipTest('无fixtures目录')
        ran = 0
        for name in sorted(os.listdir(fx_dir)):
            case = os.path.join(fx_dir, name)
            exp_file = os.path.join(case, 'expected.json')
            skill_file = os.path.join(case, 'SKILL.md')
            # v3.41.0: 兼容 SKILL.sample.md 命名（NC001负控制自2026-08-29起即此形态·防评估器误发现）
            if not os.path.exists(skill_file):
                alt = os.path.join(case, 'SKILL.sample.md')
                if os.path.exists(alt):
                    skill_file = alt
            if not (os.path.isdir(case) and os.path.exists(exp_file) and os.path.exists(skill_file)):
                # v3.52.1批6e（#21/#143有痕跳过根治）：缺件样本不再静默continue——输出⚪提示可观测
                # （#143：有痕跳过≠静默跳过·BD6缺expected.json曾26天无人知）
                missing = [n for n, e in (('expected.json', exp_file), ('SKILL(.sample).md', skill_file)) if not os.path.exists(e)]
                print(f'\n⚪ fixture {name}: 缺 {",".join(missing)}——跳过（有痕·补齐后自动纳入回归）')
                continue
            with open(exp_file, encoding='utf-8') as f:
                exp = json.load(f)
            result = evaluate_skill(skill_file)
            for check, rule in exp.get('checks', {}).items():
                got = result['scores'].get(check)
                self.assertIsNotNone(got, f'{name}: 无检查项{check}')
                full = WEIGHTS.get(check, 0)
                op, val = rule['op'], rule['value']
                if op == 'full':      # 满分=不误伤
                    self.assertEqual(got, full, f"{name}/{check}: 期望满分{full}实得{got}——负控制被误伤(假阳性回归)")
                elif op == '>=':
                    self.assertGreaterEqual(got, val, f'{name}/{check}')
                elif op == '==':
                    self.assertEqual(got, val, f'{name}/{check}')
                elif op == '<=':
                    self.assertLessEqual(got, val, f'{name}/{check}')
            ran += 1
        self.assertGreater(ran, 0, 'fixtures目录存在但无有效样本')


class TestVersionUniformGhostCopy(unittest.TestCase):
    """BD6（双盲第6次 P1-1 实锤·2026-08-09）：references/ 下同名 SKILL.md 幽灵副本不得覆盖主版本值。
    实锤：references/SKILL.md（v3.32.0滞后副本）在 eval_version_uniform 步骤5遍历时以 fname='SKILL.md'
    覆盖步骤1提取的主版本（3.33.2）→ versions['SKILL.md'] 输出错值。修复=步骤5跳过 fname=='SKILL.md'。
    本测试直接断言 versions 值（fixture expected.json 只支持 scores 断言，version_uniform 不在 scores 域）。"""

    def test_ghost_copy_does_not_override_main_version(self):
        with tempfile.TemporaryDirectory() as d:
            # 主 SKILL.md（版本 3.33.2）
            with open(os.path.join(d, 'SKILL.md'), 'w', encoding='utf-8') as f:
                f.write('---\nname: test\nversion: "3.33.2"\n---\n# Test\n')
            # 幽灵副本 references/SKILL.md（滞后版本 3.32.0——P1-1 实锤场景）
            os.makedirs(os.path.join(d, 'references'), exist_ok=True)
            with open(os.path.join(d, 'references', 'SKILL.md'), 'w', encoding='utf-8') as f:
                f.write('---\nname: test\nversion: "3.32.0"\n---\n# Ghost\n')
            # CHANGELOG 与主版本一致
            with open(os.path.join(d, 'references', 'CHANGELOG.md'), 'w', encoding='utf-8') as f:
                f.write('### v3.33.2 — 2026-08-09\n')
            r = eval_version_uniform(os.path.join(d, 'SKILL.md'))
            self.assertEqual(r['versions'].get('SKILL.md'), '3.33.2',
                             f'幽灵副本覆盖主版本值: {r["versions"]}')
            self.assertEqual(r['versions'].get('CHANGELOG.md'), 'v3.33.2')
            self.assertEqual(r['mismatches'], [])
            self.assertTrue(r['passed'])


class TestHonestPass(unittest.TestCase):
    """v3.19.1回归护栏：双章制计算逻辑——谁改坏honest_pass，这里当场报红（F1脚本层失效面护栏·皮叔拍板2026-07-29）"""

    def _base(self):
        result = {'total': 90, 'gate': {'g1': True}, 'd5_band': '安全',
                  'evidence': {'capped_score': 74}}
        version_result = {'passed': True, 'dependencies': [
            {'name': 'dep1', 'status': '✅ sync'},
            {'name': 'dep2', 'status': '⚪ source-unreachable'}]}
        return result, version_result

    def test_no_redflag_true(self):
        """无红字→passed=True（⚪source-unreachable不计红字）"""
        from skill_eval import compute_honest_pass
        r, v = self._base()
        passed, flags, raw_pass = compute_honest_pass(r, v)
        self.assertTrue(passed, f'无红字应True，flags={flags}')
        self.assertTrue(raw_pass)
        self.assertEqual(flags, [])

    def test_d5_band_not_redflag(self):
        """d5不可接受→不产生红字（v3.31.3根改·皮叔拍板"长度不否决可用性"）·passed不受影响"""
        from skill_eval import compute_honest_pass
        r, v = self._base()
        r['d5_band'] = '不可接受'
        passed, flags, raw_pass = compute_honest_pass(r, v)
        self.assertTrue(passed, 'v3.31.3根改后d5仅标注不否决·passed应True')
        self.assertTrue(raw_pass, '旧口径raw_pass不受影响')
        self.assertFalse(any('d5' in f for f in flags), f'd5不得入红字，flags={flags}')

    def test_drift_and_capped_redflags(self):
        """真drift+capped<70→双红字入flags·passed=False"""
        from skill_eval import compute_honest_pass
        r, v = self._base()
        r['evidence']['capped_score'] = 59
        v['dependencies'][0]['status'] = '🔴 drift'
        passed, flags, raw_pass = compute_honest_pass(r, v)
        self.assertFalse(passed)
        self.assertEqual(len(flags), 2, f'应恰两条红字，flags={flags}')

    def test_standard_corruption_escalates(self):
        """v2.9.12（v4.12.7待办落地·2026-09-27自评Loop）：标准库缺失/解析异常→红字+passed=False。
        ⚪not-evaluable(staleness)是"没法查"，但标准库是评估器自身评测前提——前提断裂≠对象侧不可查，
        沉默放行=考题基线整体失效仍出绿灯（假绿灯第五形态封堵）。"""
        from skill_eval import compute_honest_pass
        r, v = self._base()
        passed, flags, raw_pass = compute_honest_pass(
            r, v, '⚪not-evaluable(staleness): task-standards.json缺失，考题滞后检测未能评估（N5三态）')
        self.assertFalse(passed, f'标准库损坏应False，flags={flags}')
        self.assertEqual(len(flags), 1, f'应恰一条红字，flags={flags}')
        self.assertIn('标准库损坏', flags[0])
        self.assertIn('task-standards.json缺失', flags[0])
        self.assertTrue(raw_pass, 'raw旧口径不受honest升档影响（历史可比性）')

    def test_normal_staleness_no_flag(self):
        """真滞后advisory（⚠️类·你审阅闹钟）与None均不升红字——只拦前提断裂两分支"""
        from skill_eval import compute_honest_pass
        r, v = self._base()
        lag = ('⚠️ 考题可能滞后: clock-loop当前v4.13.0 vs 标准基线v4.12.13（Y位已跑2格）——'
               '旧标准测新版本=假绿灯，建议你审阅')
        for adv in (None, lag):
            passed, flags, _ = compute_honest_pass(r, v, adv)
            self.assertTrue(passed, f'adv={adv!r}不应升红字，flags={flags}')
            self.assertEqual(flags, [])


class TestReportContent(unittest.TestCase):
    """v3.21.0回归护栏：报告内容完整性分层强制（F2消费层门禁·改坏分层逻辑当场报红）"""

    def _write(self, body):
        import tempfile
        fd, path = tempfile.mkstemp(suffix='.md', text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def test_honest_pass_consumed_pass(self):
        """含honest_pass→硬门禁通过"""
        from skill_eval import eval_report_content
        p = self._write('# 报告\nhonest_pass=False\n🔧置信度\n⛔本证据不能支持: X\n')
        r = eval_report_content(p); os.remove(p)
        self.assertTrue(r['passed']); self.assertFalse(r['na'])
        self.assertEqual(r['advisories'], [])

    def test_honest_pass_missing_fail(self):
        """无honest_pass→硬门禁拦（F2漂移）"""
        from skill_eval import eval_report_content
        p = self._write('# 报告\nraw 94/capped 74\n10项全绿\n')
        r = eval_report_content(p); os.remove(p)
        self.assertFalse(r['passed']); self.assertFalse(r['na'])
        self.assertFalse(r['consumed'])

    def test_checkup_report_na(self):
        """体检报告→N/A不适用（不误伤非E/F）"""
        from skill_eval import eval_report_content
        p = self._write('# 知识库体检报告\nkb_concept_lint——机械段五检0 FAIL\n')
        r = eval_report_content(p); os.remove(p)
        self.assertTrue(r['na']); self.assertTrue(r['passed'])

    def test_soft_advisory_not_block(self):
        """有honest_pass但缺置信度/负向声明→软提示不阻断(passed仍True)"""
        from skill_eval import eval_report_content
        p = self._write('# 报告\nhonest_pass=True\n(仅硬门禁字段·其余略)\n')
        r = eval_report_content(p); os.remove(p)
        self.assertTrue(r['passed'], '硬门禁过就该passed')
        self.assertGreaterEqual(len(r['advisories']), 2, '置信度+负向声明双软提示')

    def test_m4_candidate_no_ledger_advisory(self):
        """v3.22.0 M4: 有候选证据却无处置台账段→软提示(不阻断)"""
        from skill_eval import eval_report_content
        p = self._write('# 报告\nhonest_pass=True\n🔧置信度\n⛔不能支持:X\n子Agent发现了两个问题\n')
        r = eval_report_content(p); os.remove(p)
        self.assertTrue(r['passed'])
        self.assertTrue(any('处置台账' in a for a in r['advisories']), f'应提示台账缺失，advisories={r["advisories"]}')

    def test_m4_candidate_with_ledger_clean(self):
        """v3.22.0 M4: 有候选+有台账段→不提示"""
        from skill_eval import eval_report_content
        p = self._write('# 报告\nhonest_pass=True\n🔧置信度\n⛔不能支持:X\n子Agent发现了问题\n## 候选处置台账\n采纳:X\n')
        r = eval_report_content(p); os.remove(p)
        self.assertFalse(any('处置台账' in a for a in r['advisories']), f'有台账不应提示，advisories={r["advisories"]}')


class TestEvidenceGuardMode(unittest.TestCase):
    """v4.9.0 --check-evidence 模式：取证锁 L1 证据行 + L2 断言计数（物理约束与防误 §七）"""

    def _write(self, body, suffix='.md'):
        import tempfile
        fd, path = tempfile.mkstemp(suffix=suffix, text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(body)
        return path

    def _write_source(self, body):
        return self._write(body, suffix='.md')

    def test_valid_evidence_passes(self):
        """报告含合法断言行（行号+原文命中）→ 通过"""
        from skill_eval import eval_report_evidence
        src = self._write_source('# 源\n第一行内容\n第二行内容\n')
        report = self._write(
            '# 报告\n## 逐项证据\n[causal_chain][2][第一行内容][✅]\n[causal_chain][3][第二行内容][✅]\n')
        r = eval_report_evidence(report, source_path=src, min_assertions=2)
        os.remove(report); os.remove(src)
        self.assertTrue(r['passed'], f'合法取证应通过，detail={r.get("detail")}')
        self.assertEqual(r['valid_assertions'], 2)

    def test_fake_line_number_rejected(self):
        """报告含伪造行号（超源长度）→ 拒绝（取证锁拦截·防实体填充）"""
        from skill_eval import eval_report_evidence
        src = self._write_source('# 源\n第一行内容\n')
        report = self._write('# 报告\n## 逐项证据\n[causal_chain][99][第一行内容][✅]\n')
        r = eval_report_evidence(report, source_path=src)
        os.remove(report); os.remove(src)
        self.assertFalse(r['passed'], '伪造行号必须被取证锁拦截')
        self.assertLess(r['valid_assertions'], 1)

    def test_threshold_not_met_rejected(self):
        """有效断言低于 min_assertions → 拒绝"""
        from skill_eval import eval_report_evidence
        src = self._write_source('# 源\n第一行内容\n')
        report = self._write('# 报告\n## 逐项证据\n[causal_chain][2][第一行内容][✅]\n')
        r = eval_report_evidence(report, source_path=src, min_assertions=80)
        os.remove(report); os.remove(src)
        self.assertFalse(r['passed'], '断言数不足阈值必须拒绝')
        self.assertEqual(r['valid_assertions'], 1)


class TestFinalizeReport(unittest.TestCase):
    """v3.23.0 finalize_report.py 归档封口物理锁——纯函数注入测试（root可注入·零改脚本·照validate_diary先例）。"""

    def test_path_guard_outside_root_rejected(self):
        # 负例：归档根外路径拒绝（阻断写散）
        from finalize_report import check_archive_path
        ok, reason = check_archive_path('/tmp/假报告.md', root='/tmp/不存在的归档根')
        self.assertFalse(ok)
        self.assertIn('不在归档根', reason)

    def test_path_guard_non_md_rejected(self):
        # 负例：根内但非md文件拒绝
        from finalize_report import check_archive_path
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x.txt')
            ok, reason = check_archive_path(p, root=d)
            self.assertFalse(ok)
            self.assertIn('markdown', reason)

    def test_path_guard_inside_root_ok(self):
        # 正例：根内md文件放行
        from finalize_report import check_archive_path
        with tempfile.TemporaryDirectory() as d:
            ok, _ = check_archive_path(os.path.join(d, 'a_评估报告.md'), root=d)
            self.assertTrue(ok)

    def test_finalize_missing_report_not_sealed(self):
        # 负例：报告不存在→sealed=False（不跑子检查·fail-closed）
        from finalize_report import finalize
        with tempfile.TemporaryDirectory() as d:
            block = finalize('/不存在/SKILL.md', os.path.join(d, '不存在.md'), archive_root=d)
            self.assertFalse(block['sealed'])
            self.assertEqual(block['checks']['existence'], '🔴')
            self.assertIsNone(block['report_sha8'])

    def test_finalize_full_positive_synthetic(self):
        # 全链正例：合成达标Skill+达标报告（root注入沙箱·不碰生产库）——sealed预期取决于真实check_only，
        # 故skill用生产库真实达标Skill（triwich·score=98实录，机械grade=S），报告合成五信号齐全+等级行（v3.31.6 grade_guard要求）
        from finalize_report import finalize
        skill = os.path.expanduser('[记忆共享中心]/技能配置/triwich/SKILL.md')
        if not os.path.exists(skill):
            self.skipTest('真实triwich不在本机——全链正例仅开发机跑')
        report_body = (
            '# 合成Skill v9.9.9 评估报告\n\n'
            '## 评估结论\n'
            '| 项 | 值 |\n'
            '|---|---|\n'
            '| 等级 | **S级·通过** |\n'
            '| 验证深度 | 静态文档级·未实测 |\n'
            '| 双章诚实 | honest_pass=true |\n\n'
            '🔧脚本确定性6项 + 🧠AI判断4项（置信度拆分）\n\n'
            '## ⛔ 本报告不能支持的结论\n- 本报告不能支持运行时有效结论\n\n'
            '## L1 拆解\n' + '本轮拆解：门禁四五的调用链从自觉点前移到脚本入口，封口确认块数据源锁定脚本JSON输出，不由AI自行编写字段内容。' * 2 + '\n\n'
            '## L2 自检\n' + '但是存在风险：合成报告可能高估门禁有效性，盲区在于脚本本身的判定逻辑偏差，局限性已如实声明。' * 2 + '\n\n'
            '## 候选处置台账\n'
            '| C1 | 合成候选1 | 采纳 | 已修 | 证据：合成正例\n'
            '| C2 | 合成候选2 | 合并 | 并入C1 | 证据：合成正例\n'
            '| C3 | 合成候选3 | 降级 | 保留在案 | 证据：合成正例 | 逆向论证：如果这个判定错了，合成正例会漏检一个真缺陷——后果可观测，风险已接受\n\n'
            '## 子 Agent 审查结果\n'
            '第1轮: ✅ 通过（独立审查确认·证据：合成正例）\n\n'
            '## 📢 交付摘要\n'
            '📢 评估结论\n'
            '✅ 结果: 通过 | S级(present) · 99分 | 验证深度: 实测通过（冒烟✅+特性测试9/9✅）\n'
            '冒烟证据: /etc/hosts\n'
            '一句话: 合成正例，全链门禁验证用。\n'
            '详情: 合成报告\n\n'
            '📢 接下来你可以（CTA）\n'
            '🔄 换一个评估 → 合成正例\n\n'
            '🧭 你待决（治理层·不改变上述结论）\n'
            '本轮无挂起项\n'
        )
        with tempfile.TemporaryDirectory() as d:
            report = os.path.join(d, '合成Skill_v9.9.9_评估报告_2026-07-30.md')
            with open(report, 'w', encoding='utf-8') as f:
                f.write(report_body)
            block = finalize(skill, report, archive_root=d)
            self.assertEqual(block['checks']['existence'], '✅')
            self.assertEqual(block['checks']['path_guard'], '✅')
            self.assertEqual(block['checks']['check_l1l2'], '✅', f"detail={block['detail']}")
            self.assertEqual(block['checks']['check_report_content'], '✅', f"detail={block['detail']}")
            self.assertTrue(block['sealed'], f"全链正例应sealed，detail={block['detail']}")
            self.assertIsNotNone(block['report_sha8'])

    def test_finalize_passed_false_warns_not_blocks(self):
        # 设计决策验证：passed=False（诚实章）透传警示不阻断——用clock-loop自评（d5红字实录）
        from finalize_report import finalize
        skill = os.path.expanduser('[记忆共享中心]/技能配置/clock-loop/SKILL.md')
        if not os.path.exists(skill):
            self.skipTest('clock-loop不在本机')
        with tempfile.TemporaryDirectory() as d:
            report = os.path.join(d, 'clock-loop_vX_评估报告.md')
            with open(report, 'w', encoding='utf-8') as f:
                f.write('# 报告\n诚实章 checked\n🔧置信度\n⛔不能支持:X\n## L1 拆解\n' + '实质内容拆解分析门禁机制的调用链与数据流向。' * 4 + '\n## L2 自检\n' + '但是风险在于判定逻辑可能存在盲区与局限。' * 4 + '\n')
            block = finalize(skill, report, archive_root=d)
            if block.get('passed') is False:
                self.assertIn('warning', block)
                # passed=False不单独导致sealed=False（check_only.passed才是硬门禁）
                self.assertNotIn('passed', [n for n, ok, _ in
                    [(x.split(':')[0].strip('✅🔴 '), '✅' in x, x) for x in block['detail']] if not ok])

    def test_report_sha8_idempotent_after_seal_paste(self):
        # 哈希自指悖论防护：粘贴封口确认块前后sha8不变（否则双盲复现永远对不上）
        # v1.6.1根治：⛔不再手写段格式——改调生产唯一出口 build_seal_section()。
        # 原因：v1.6.0 时本测试手写格式（无 --- 前缀）与实际回贴格式（有 --- 前缀）不一致
        # → 测试报绿而生产 9/9 报告 sha8 失效（2026-09-04 实测实锤·测的是想象形态非生产形态）。
        from finalize_report import report_sha8, build_seal_section
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'r_评估报告.md')
            body = '# 报告\n正文内容\n'
            with open(p, 'w', encoding='utf-8') as f:
                f.write(body)
            h1 = report_sha8(p)
            block = {'seal': 'test', 'timestamp': 't', 'skill': 's', 'report': p,
                     'report_sha8': h1, 'sealed': True, 'passed': True,
                     'honest_flags': [], 'human_check': {'note': 'n'}}
            with open(p, 'a', encoding='utf-8') as f:
                f.write(build_seal_section(block))   # ← 生产同一份格式（单一真相源）
            h2 = report_sha8(p)
            self.assertEqual(h1, h2, '粘贴封口块后sha8必须不变（幂等哈希·v1.6.1走生产同一代码路径）')

    def test_report_sha8_idempotent_legacy_handwritten_block(self):
        # v1.6.1 向后兼容：历史手写/旧格式封口块（无 --- 前缀）也必须能剔离
        # （存量报告里两种形态共存，剔离正则必须两者都兼容）
        from finalize_report import report_sha8
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'r_评估报告.md')
            body = '# 报告\n正文内容\n'
            with open(p, 'w', encoding='utf-8') as f:
                f.write(body)
            h1 = report_sha8(p)
            with open(p, 'a', encoding='utf-8') as f:
                f.write('\n## 🔒 归档封口确认块（v3.23.0）\n\n```json\n{"sealed": true}\n```\n')
            self.assertEqual(h1, report_sha8(p), '旧格式（无---前缀）也必须幂等')

    def test_seal_selfcheck_passes(self):
        # v1.6.1 元验证：启动自检本身必须通过（自检走生产同一代码路径·失败则 main 拒封口）
        from finalize_report import _selfcheck_idempotency
        ok, detail = _selfcheck_idempotency()
        self.assertTrue(ok, f'幂等性自检失败（SEAL_STRIP_RE 与 build_seal_section 格式漂移）: {detail}')

    def test_purity_guard_polluted_report_rejected(self):
        # v3.24.0负例：双报告污染拒封（L3沉淀07-30模式J·真实污染文件同构合成）
        from finalize_report import check_single_report
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'x_评估报告.md')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('---\ntitle: "A报告"\n---\n\n# A报告\n正文\n\n---\ntitle: "B报告副本"\n---\n\n# B报告\n混入内容\n')
            ok, reason = check_single_report(p)
            self.assertFalse(ok)
            self.assertIn('双报告污染', reason)

    def test_purity_guard_clean_report_ok(self):
        # v3.24.0正例：单frontmatter+正文含普通---分隔线不误伤
        from finalize_report import check_single_report
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'y_评估报告.md')
            with open(p, 'w', encoding='utf-8') as f:
                f.write('---\ntitle: "单报告"\n---\n\n# 报告\n正文\n\n---\n\n分隔线后续内容(非frontmatter)\n')
            ok, _ = check_single_report(p)
            self.assertTrue(ok, '普通分隔线不应误伤')

    def test_purity_guard_v326_missed_and_falsepos(self):
        # v3.26.0双盲4th实锤的漏检+误伤四场景
        from finalize_report import check_single_report
        import tempfile
        def chk(body):
            d = tempfile.mkdtemp(); p = os.path.join(d, 'r_评估报告.md')
            with open(p, 'w', encoding='utf-8') as f: f.write(body)
            ok, _ = check_single_report(p); os.remove(p); return ok
        # 场景1 漏检修：第二个frontmatter首行非title(是type)——应检出污染
        self.assertFalse(chk('---\ntitle: A\n---\n# A\n正文\n\n---\ntype: reference\ntitle: B\n---\n# B\n'),
            'v3.26漏检修：首行type的双报告应被逮')
        # 场景2 误伤修：代码块内YAML示例——应放行
        self.assertTrue(chk('---\ntitle: 单报告\n---\n# 报告\n示例：\n```yaml\n---\ntitle: 这是示例\n---\n```\n正文\n'),
            'v3.26误伤修：代码块内YAML示例不应误杀')
        # 场景3 误伤修：正文单条---分隔线(非闭合块/无frontmatter键)——应放行
        self.assertTrue(chk('---\ntitle: 单报告\n---\n# 报告\n正文一\n\n---\n\n分隔线后普通段落\n'),
            'v3.26误伤修：正文分隔线不应误杀')
        # 场景4 基线：典型首行title双报告——仍检出
        self.assertFalse(chk('---\ntitle: A\n---\n# A\n正文\n\n---\ntitle: B\n---\n# B\n'),
            'v3.26基线：首行title双报告仍应被逮')



class TestPokaDepthNaRerating(unittest.TestCase):
    """v3.42.0 na改判+📦密度回退回归测试（方案C·治"5分照拿"）"""

    NEG_CONTENT = """---
name: neg-test-skill
description: >
  测试用负例Skill。哲学视角分析类。NOT for 真实使用。
author: 皮叔
source: self-built
version: "1.0.0"
---

# 负例测试Skill

这是一个模拟分析型但核心动作无锁定字段的Skill。
它有哲学、逻辑链、推演等分析型信号词。

## 功能定位

分析问题，给出视角。
"""

    def test_na_items_not_counted_in_denominator(self):
        """na项不再计入分母——无终检声明的分析型Skill，D1/D2/D4应标na"""
        import skill_eval
        # meta-aletheia类分析型：D1-D4全na→回退📦密度
        depth_r, detail = skill_eval.eval_poka_yoke_depth(self.NEG_CONTENT)
        scoring = detail.get('_scoring', {})
        self.assertEqual(scoring.get('mode'), 'all_na_fallback',
                         "干净分析型负例应走全na回退模式")

    def test_bare_skill_intercepted_not_full_score(self):
        """裸奔Skill（全na且📦=0）→depth_r=0+显式拦截警告（不可能静默·C-090）"""
        import skill_eval
        depth_r, detail = skill_eval.eval_poka_yoke_depth(self.NEG_CONTENT)
        self.assertEqual(depth_r, 0.0, "📦=0裸奔应depth_r=0（非旧版5分照拿）")
        self.assertIn('D6_fallback_intercept', detail, "应有显式拦截警告（不可能静默）")
        self.assertFalse(detail['D6_fallback_intercept']['pass'])

    def test_pkg_lock_present_not_intercepted(self):
        """有产出物声明的同型Skill→不拦截（判定区分度·非误伤）"""
        import skill_eval
        pos = self.NEG_CONTENT.replace("## 功能定位", "## 功能定位\n\n📦 **产出物**：分析结论卡")
        depth_r, detail = skill_eval.eval_poka_yoke_depth(pos)
        self.assertGreater(depth_r, 0.0, "有📦应>0")
        self.assertNotIn('D6_fallback_intercept', detail, "有📦不应拦截")

    def test_process_type_behavior_preserved(self):
        """流程型Skill（D1-D4有适用项）→applicable模式（原行为保持）"""
        import skill_eval
        flow_content = self.NEG_CONTENT + """
## 终检清单
必须全部✅才能输出。自动校验由脚本检查执行。
`python3 scripts/check.py` exit code 非零则中止输出。
工作流A：步骤1。工作流B：步骤2。
"""
        depth_r, detail = skill_eval.eval_poka_yoke_depth(flow_content)
        scoring = detail.get('_scoring', {})
        self.assertEqual(scoring.get('mode'), 'applicable',
                         "含终检声明的流程型应走applicable模式（非回退）")
        self.assertGreaterEqual(scoring.get('applicable_count', 0), 2,
                                "D1/D3等应适用")


class TestEvidenceExtractor(unittest.TestCase):
    """C01（v4.0.0·X级主体）考题基线：evidence_extractor 档位判据负例三例+正例。
    判据源=references/evidence-ladder-map.md（§三）+ skill-arch-standard §2.2a 登记表。"""

    def _extractor(self):
        from evidence_extractor import (_is_exercised_line, _scan_logs,
                                        _scan_archives, _verify_seal, extract_evidence)
        return _is_exercised_line, _scan_logs, _scan_archives, _verify_seal, extract_evidence

    def test_plan_not_run_not_exercised(self):
        """负例①：计划实跑→不升档（把'计划实跑'当'已实跑'=假阳性·#227步骤2风险）"""
        is_ex, *_ = self._extractor()
        self.assertFalse(is_ex('计划实跑 4 类用例验证 clock-loop', 'clock-loop'))
        self.assertFalse(is_ex('待实测 clock-loop 全绿用例', 'clock-loop'))
        self.assertFalse(is_ex('clock-loop 将实跑冒烟测试', 'clock-loop'))

    def test_no_number_not_exercised(self):
        """负例②：无具体数字→不升档（空口'跑过'不算·判据§三.3）"""
        is_ex, *_ = self._extractor()
        self.assertFalse(is_ex('clock-loop 实测验证通过', 'clock-loop'))

    def test_no_skill_assoc_not_exercised(self):
        """负例③：无 skill 关联→不升档（证据必须可归因）"""
        is_ex, *_ = self._extractor()
        self.assertFalse(is_ex('4 类用例全绿验证通过', 'clock-loop'))

    def test_completed_with_number_exercised(self):
        """正例：完成态+具体数字+skill关联→exercised 行"""
        is_ex, *_ = self._extractor()
        self.assertTrue(is_ex('clock-loop 实跑自测 4 类用例全绿——19 条代表 prompt 全部命中', 'clock-loop'))
        self.assertTrue(is_ex('验证：skill_eval 回归 EXIT=0 clock-loop 全过 42 条', 'clock-loop'))

    def test_extract_grade_present_when_no_evidence(self):
        """空目录→present 降级（提取器不因目录缺失虚高）"""
        import tempfile
        _, _, _, _, extract = self._extractor()
        with tempfile.TemporaryDirectory() as d:
            ev = extract('no-such-skill-xyz', log_dir=d, archive_dir=d)
        self.assertEqual(ev['grade'], 'present')
        self.assertEqual(ev['ceiling'], 74)


class TestSimilarScanAdvisory(unittest.TestCase):
    """C05（v4.0.2·承诺核销制）考题基线：同类扫描核销 advisory 判据。
    判据源=skill_eval.eval_similar_scan_advisory docstring（#129"挂了挡没接变速箱"·07-21 prose纪律被违反≥3次
    → 机械化闹钟：修复类条目须附"同类扫描"核销证据·advisory 级不计分·None=无异常）。"""

    def _advisory(self, cl_body):
        import tempfile
        from skill_eval import eval_similar_scan_advisory
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, 'references'), exist_ok=True)
            with open(os.path.join(d, 'references', 'CHANGELOG.md'), 'w', encoding='utf-8') as f:
                f.write('### v1.0.0 — 2026-09-05\n' + cl_body + '\n')
            return eval_similar_scan_advisory(os.path.join(d, 'SKILL.md'))

    def test_fix_without_scan_advisory(self):
        """负例①：修复类条目无"同类扫描"证据→advisory 提示补核销（修了不扫=承诺无核销·#129病根）"""
        msg = self._advisory('修复了 scoring 计算错误')
        self.assertIsNotNone(msg)
        self.assertIn('同类扫描核销提示', msg)

    def test_non_fix_entry_no_advisory(self):
        """负例②：非修复类条目→None 静默（新增功能不触发核销要求·不误报）"""
        self.assertIsNone(self._advisory('新增 evidence 档位映射机制'))

    def test_fix_with_scan_word_ok(self):
        """正例①：修复类条目含"同类扫描"→None（已核销·扫描证据在案）"""
        self.assertIsNone(self._advisory('修复了 scoring 计算错误——同类扫描逮住同族 3 处'))

    def test_missing_changelog_silent(self):
        """正例②：CHANGELOG 缺失→None（幂等静默·不因文件缺失误报）"""
        import tempfile
        from skill_eval import eval_similar_scan_advisory
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(eval_similar_scan_advisory(os.path.join(d, 'SKILL.md')))


class TestVersionWatermark(unittest.TestCase):
    """C07（v4.1.0·并发写入协调）考题基线：版本水位线 advisory 判据。
    判据源=skill_eval.eval_version_watermark docstring（#184 09-05 并发会话实锤——
    两会话同时改 clock-loop 资产，发现时 SKILL.md 已是并发方推进的 v3.47.0。
    修法候选机械化：载体 steps/version_watermark.md 记"上次本会话见过的版本"，
    比对实盘三态判定——推进→🔴先同步再动手 / 回退→⚠️查误操作 / 相等或缺失→静默）。
    载体路径=SKILL.md 同级 steps/version_watermark.md（生产同构·不注入参数测真实路径）。"""

    def _setup(self, cur_ver='4.1.0', wm_ver=None, has_frontmatter=True):
        import tempfile
        d = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(d.name, 'steps'), exist_ok=True)
        if has_frontmatter:
            with open(os.path.join(d.name, 'SKILL.md'), 'w', encoding='utf-8') as f:
                f.write(f'---\nversion: "{cur_ver}"\n---\n')
        else:
            with open(os.path.join(d.name, 'SKILL.md'), 'w', encoding='utf-8') as f:
                f.write('# 无 frontmatter 的 Skill\n')
        if wm_ver is not None:
            with open(os.path.join(d.name, 'steps', 'version_watermark.md'), 'w', encoding='utf-8') as f:
                f.write(f'# 持久化计数器：版本水位线（C07 #184）\n\nlast_seen_version: {wm_ver}\nlast_seen_at: 2026-09-05 10:00\n')
        return d

    def test_missing_watermark_silent(self):
        """正例①：载体缺失→None 静默（首次运行·由 --update-watermark 显式初始化·不误报）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver=None)
        try:
            self.assertIsNone(eval_version_watermark(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_equal_version_silent(self):
        """正例②：载体版本==实盘→None（无跨会话推进·正常开工不打扰）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver='4.1.0')
        try:
            self.assertIsNone(eval_version_watermark(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_version_advance_advisory(self):
        """负例①：载体版本<实盘→🔴版本推进 advisory（跨会话/并发方已升级·先同步再动手·#184实锤损害）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver='4.0.2')
        try:
            msg = eval_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('跨会话/并发推进', msg)
            self.assertIn('先同步', msg)
        finally:
            d.cleanup()

    def test_version_regress_advisory(self):
        """负例②：载体版本>实盘→⚠️版本回退异常（检查是否误回滚/覆盖）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.0.2', wm_ver='4.1.0')
        try:
            msg = eval_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('版本回退异常', msg)
        finally:
            d.cleanup()

    def test_missing_last_seen_fail_visible(self):
        """负例③：载体缺 last_seen_version 行→fail-visible advisory（⛔不静默当一致）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver=None)
        try:
            with open(os.path.join(d.name, 'steps', 'version_watermark.md'), 'w', encoding='utf-8') as f:
                f.write('# 持久化计数器：版本水位线\n\n# 空载体·无 last_seen_version 行\n')
            msg = eval_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('缺 last_seen_version 行', msg)
        finally:
            d.cleanup()

    def test_missing_frontmatter_fail_visible(self):
        """负例④：SKILL.md 缺 frontmatter version→fail-visible advisory（无法比对·不静默）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver='4.1.0', has_frontmatter=False)
        try:
            msg = eval_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('缺 frontmatter version', msg)
        finally:
            d.cleanup()

    def test_unparsable_version_fail_visible(self):
        """负例⑤：版本号无法解析（任一侧）→fail-visible advisory（⛔不静默当相等）"""
        from skill_eval import eval_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver='not-a-version')
        try:
            msg = eval_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('无法解析', msg)
        finally:
            d.cleanup()

    def test_update_watermark_creates_carrier(self):
        """正例③：update_version_watermark 首次写入→载体创建且含 last_seen_version 行"""
        from skill_eval import update_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver=None)
        try:
            ok, msg = update_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertTrue(ok)
            wp = os.path.join(d.name, 'steps', 'version_watermark.md')
            self.assertTrue(os.path.isfile(wp))
            with open(wp, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('last_seen_version: 4.1.0', content)
            self.assertIn('last_seen_at:', content)
        finally:
            d.cleanup()

    def test_update_watermark_missing_frontmatter_fails(self):
        """负例⑥：SKILL.md 缺 frontmatter version→写水位线失败（fail-visible·不写脏载体）"""
        from skill_eval import update_version_watermark
        d = self._setup(cur_ver='4.1.0', wm_ver=None, has_frontmatter=False)
        try:
            ok, msg = update_version_watermark(os.path.join(d.name, 'SKILL.md'))
            self.assertFalse(ok)
            self.assertFalse(os.path.exists(os.path.join(d.name, 'steps', 'version_watermark.md')))
        finally:
            d.cleanup()


class TestLessonsRecall(unittest.TestCase):
    """C06（v4.2.0·跨周期学习断裂）考题基线：教训召回 advisory 判据。
    判据源=skill_eval.eval_lessons_recall_advisory docstring（#68"教训入账却从未阻止下一次"——
    每次教训都入账（PAT/CHANGELOG）却从没被新会话读到→新会话读不到就等于没发生（愿景③④核心缺口）。
    机械化：读 steps/lessons_ledger.md 召回活跃教训（最近犯日距今 ≤30 天·Top 3），
    --check-only 开工上下文可见。判定——载体缺失→None 静默｜无活跃→None 静默｜
    有活跃→🔴列出 Top3+活跃总数｜全条目解析失败→fail-visible ⚠️（⛔不静默当无教训）。"""

    def _setup(self, ledger_text=None):
        import tempfile
        d = tempfile.TemporaryDirectory()
        if ledger_text is not None:
            with open(os.path.join(d.name, 'lessons_ledger.md'), 'w', encoding='utf-8') as f:
                f.write(ledger_text)
        return d

    @staticmethod
    def _lesson(lesson_id, last_date, first_date='2026-08-01', mode='猜 API', times=3):
        return (f"- **{lesson_id}**\n"
                f"  - 错误模式：{mode}\n"
                f"  - 正确姿势：先读实际\n"
                f"  - 防法：断言+写后复验\n"
                f"  - 首犯：{first_date} ｜ 最近犯：{last_date} ｜ 次数：{times}")

    def test_missing_ledger_silent(self):
        """正例①：载体缺失→None 静默（幂等·首次由 AI 登记后生效·不因文件缺失误报）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        d = self._setup()
        try:
            self.assertIsNone(eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5)))
        finally:
            d.cleanup()

    def test_all_inactive_silent(self):
        """正例②：全部最近犯 >30 天→None 静默（无活跃教训·开工不打扰）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        ledger = '# 教训台账\n\n' + self._lesson('LESSON-001', '2026-08-01')
        d = self._setup(ledger)
        try:
            self.assertIsNone(eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5)))
        finally:
            d.cleanup()

    def test_active_lessons_advisory(self):
        """正例③：有活跃教训→🔴召回 advisory（含活跃总数+Top3 教训编号·开工先复习）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        ledger = ('# 教训台账\n\n'
                  + self._lesson('LESSON-001', '2026-09-05')
                  + '\n' + self._lesson('LESSON-002', '2026-09-04', mode='中文错字'))
        d = self._setup(ledger)
        try:
            msg = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5))
            self.assertIsNotNone(msg)
            self.assertIn('跨周期教训召回：2 条活跃教训', msg)
            self.assertIn('LESSON-001', msg)
            self.assertIn('LESSON-002', msg)
        finally:
            d.cleanup()

    def test_active_top3_truncation(self):
        """边界①：4 条活跃→计数=4·仅列 Top3（按最近犯日倒序截断）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        ledger = ('# 教训台账\n\n'
                  + self._lesson('LESSON-001', '2026-09-01')
                  + '\n' + self._lesson('LESSON-002', '2026-09-02', mode='错字')
                  + '\n' + self._lesson('LESSON-003', '2026-09-03', mode='单法')
                  + '\n' + self._lesson('LESSON-004', '2026-09-05', mode='无扫描'))
        d = self._setup(ledger)
        try:
            msg = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5))
            self.assertIsNotNone(msg)
            self.assertIn('4 条活跃教训', msg)
            self.assertIn('LESSON-004', msg)
            self.assertIn('LESSON-003', msg)
            self.assertNotIn('LESSON-001', msg)  # Top3 截断·最旧活跃不列
        finally:
            d.cleanup()

    def test_unparsable_lessons_fail_visible(self):
        """负例①：载体存在但全条目解析失败→fail-visible advisory（⛔不静默当无教训）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        d = self._setup('# 教训台账\n\n- LESSON-001（缺 ** 编号格式·不可解析）\n  错误模式：xxx\n')
        try:
            msg = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5))
            self.assertIsNotNone(msg)
            self.assertIn('无可解析条目', msg)
        finally:
            d.cleanup()

    def test_bad_date_skip_fail_safe(self):
        """负例②：last 日期格式非法→跳过该条目不崩溃（其余活跃仍召回·无其余→None）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        ledger = '# 教训台账\n\n- **LESSON-001**\n  - 错误模式：猜 API\n  - 正确姿势：先读实际\n  - 防法：断言\n  - 首犯：2026-08-01 ｜ 最近犯：not-a-date ｜ 次数：3\n'
        d = self._setup(ledger)
        try:
            msg = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'),
                ledger_path=os.path.join(d.name, 'lessons_ledger.md'),
                today=date(2026, 9, 5))
            self.assertIsNone(msg)  # 坏日期条目跳过→无活跃→静默·不崩溃
        finally:
            d.cleanup()

    def test_today_boundary_30_31(self):
        """边界②：最近犯恰 30 天→活跃（≤30）；31 天→不活跃（None）"""
        from datetime import date
        from skill_eval import eval_lessons_recall_advisory
        ledger = '# 教训台账\n\n' + self._lesson('LESSON-001', '2026-08-06')
        d = self._setup(ledger)
        try:
            lp = os.path.join(d.name, 'lessons_ledger.md')
            msg30 = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'), ledger_path=lp, today=date(2026, 9, 5))
            self.assertIsNotNone(msg30)  # 2026-08-06→09-05 恰 30 天→活跃
        finally:
            d.cleanup()
        ledger = '# 教训台账\n\n' + self._lesson('LESSON-001', '2026-08-05')
        d = self._setup(ledger)
        try:
            lp = os.path.join(d.name, 'lessons_ledger.md')
            msg31 = eval_lessons_recall_advisory(
                os.path.join(d.name, 'SKILL.md'), ledger_path=lp, today=date(2026, 9, 5))
            self.assertIsNone(msg31)  # 31 天→不活跃
        finally:
            d.cleanup()


class TestRemovalAdvisory(unittest.TestCase):
    """L3反哺C-A2（2026-08-12·sucair v4.5.0/v4.5.1 两轮漏网实证）考题基线：数字护栏移除类变更残留扫描判据。

    判据源=skill_eval.eval_removal_advisory docstring（B2 检查器卫生审计 v4.6.0 逮住无直接测试引用·补登）：
    命中——CHANGELOG 最新条目含移除类词（移除/取消/撤销/删除/废除）+ 上限类词（上限/护栏/数字/分档/硬编码/硬封）
    → advisory 提示检查 eval-set/细则/论证文字是否残留数字硬判（闹钟级不计分·None=无异常）。
    机械化：_changelog_semantic_entries 取最新语义条目（位置无关·语义版本排序）。"""

    @staticmethod
    def _setup(changelog_body=None, with_changelog=True):
        import tempfile
        d = tempfile.TemporaryDirectory()
        refs = os.path.join(d.name, 'references')
        if with_changelog:
            os.makedirs(refs, exist_ok=True)
            with open(os.path.join(refs, 'CHANGELOG.md'), 'w', encoding='utf-8') as f:
                f.write(f"### v4.8.0 (2026-09-05·测试条目)\n\n{changelog_body or ''}\n")
        return d

    def test_removal_plus_limit_trigger(self):
        """正例：最新条目含移除类词+上限类词→advisory 非 None（残留扫描提示）"""
        from skill_eval import eval_removal_advisory
        d = self._setup('移除「总分上限」的硬编码判定，改为档位动态计算')
        try:
            msg = eval_removal_advisory(os.path.join(d.name, 'SKILL.md'))
            self.assertIsNotNone(msg)
            self.assertIn('移除', msg)
            self.assertIn('残留数字硬判', msg)
        finally:
            d.cleanup()

    def test_removal_without_limit_silent(self):
        """负例①：含移除类词但无上限类词→None 静默（移除与护栏双条件缺一不触发）"""
        from skill_eval import eval_removal_advisory
        d = self._setup('移除一处过时的示例文案，改用新示例')
        try:
            self.assertIsNone(eval_removal_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_limit_without_removal_silent(self):
        """负例②：含上限类词但无移除类词→None 静默（仅涉及护栏新增/调整不触发）"""
        from skill_eval import eval_removal_advisory
        d = self._setup('新增「输出长度上限」护栏声明，防生成过长')
        try:
            self.assertIsNone(eval_removal_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_no_keywords_silent(self):
        """负例③：最新条目无移除也无上限词→None 静默（普通变更不打扰）"""
        from skill_eval import eval_removal_advisory
        d = self._setup('修复一处文案措辞，补充说明段落')
        try:
            self.assertIsNone(eval_removal_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_missing_changelog_silent(self):
        """负例④：无 CHANGELOG.md→None 静默（载体缺失幂等·不因文件缺失误报）"""
        from skill_eval import eval_removal_advisory
        d = self._setup(with_changelog=False)
        try:
            self.assertIsNone(eval_removal_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()


class TestCeilingIndicators(unittest.TestCase):
    """C12（v4.3.0·触顶链条）考题基线：触顶判定三指标机械化判据。
    判据源=skill_eval.compute_ceiling_indicators docstring + phase3-termination.md v2.2.0
    （#198"交付时自动计算"实测无脚本·"自动计算"是假的→触顶永不宣告→第52行
    "⛔DO NOT继续建议文档修补"成为永远无法触发的禁令——本函数将三指标机械化：
      指标1 维度饱和度 = 得分≥90%的维度数/总维度数 ≥16/20（0.8 比率）
      指标2 剩余可修复空间比率 = Σ(1-各维度达成率)/维度数 <8%
      指标3 功能侧vs文档侧空间比 = Σ功能侧剩余/Σ文档侧剩余 >3:1 → 文档侧触顶
    三指标任一触发 → ceiling=True。advisory 级不计分（闹钟响了由 AI 终判）。"""

    ALL_KEYS = None  # 惰性填充（WEIGHTS 键）

    @classmethod
    def _keys(cls):
        from skill_eval import WEIGHTS
        return list(WEIGHTS.keys())

    @staticmethod
    def _scores(ratios):
        """ratios: {维度键: 达成率} → scores（权重×达成率·与 evaluate_skill 换算同构）"""
        from skill_eval import WEIGHTS
        return {k: WEIGHTS[k] * r for k, r in ratios.items()}

    def _uniform(self, r):
        """全维统一达成率 r 的 scores"""
        return self._scores({k: r for k in self._keys()})

    def test_all_half_not_ceiling_silent(self):
        """正例①：全维达成率 0.5→三指标均不触发→ceiling=False·format 静默 None"""
        from skill_eval import compute_ceiling_indicators, format_ceiling_advisory
        scores = self._uniform(0.5)
        ci = compute_ceiling_indicators(scores)
        self.assertFalse(ci['ceiling'])
        self.assertEqual(ci['indicators']['saturation'], 0.0)  # 0/20 高维度
        self.assertIsNone(format_ceiling_advisory(scores))  # 未触顶→None 静默

    def test_15_high_dims_not_ceiling(self):
        """边界下：恰 15 高维度（15/19=0.789<0.8）且其余指标不触发→未触顶·v5.16.0 19维(token_budget移出)"""
        from skill_eval import compute_ceiling_indicators
        keys = self._keys()
        # 低分 4 维：1 功能侧（fuse_mechanism）+3 文档侧·token_budget 已移出 WEIGHTS（v5.16.0）
        low = ['fuse_mechanism', 'yaml_frontmatter',
               'causal_chain', 'trigger_conditions']
        ratios = {k: 0.5 if k in low else 1.0 for k in keys}
        ci = compute_ceiling_indicators(self._scores(ratios))
        self.assertFalse(ci['ceiling'])
        ind = ci['indicators']
        self.assertEqual(ind['saturation_n'], 15)  # 15/19=0.789<0.8
        self.assertAlmostEqual(ind['remain_pct'], 10.53, places=2)  # 4*0.5/19*100
        self.assertEqual(ind['func_doc_ratio'], 0.33)  # 功能剩余0.5/文档剩余1.5=0.33（round 2位）

    def test_16_high_dims_ceiling(self):
        """边界上：恰 16 高维度（16/19=0.842≥0.8）→指标1触发→触顶·format 非 None·v5.16.0 19维"""
        from skill_eval import compute_ceiling_indicators, format_ceiling_advisory
        keys = self._keys()
        # 低分 3 维：1 功能侧（fuse_mechanism）+2 文档侧·token_budget 已移出 WEIGHTS（v5.16.0）
        low = ['fuse_mechanism', 'yaml_frontmatter', 'causal_chain']
        ratios = {k: 0.5 if k in low else 1.0 for k in keys}
        scores = self._scores(ratios)
        ci = compute_ceiling_indicators(scores)
        self.assertTrue(ci['ceiling'])
        self.assertEqual(ci['indicators']['saturation_n'], 16)  # 恰达阈 16/19=0.842
        msg = format_ceiling_advisory(scores)
        self.assertIsNotNone(msg)
        self.assertIn('文档侧已触顶', msg)  # 文案可被 AI 终判消费
        self.assertIn('ℹ️', msg)  # v4.7.0 降级：状态行·非告警（B1 常响根治·分级错误修正）
        self.assertIn('状态行·非告警', msg)

    def test_indicator2_remain_pct(self):
        """指标2：全维达成率 0.93→剩余 7%<8%→触顶（断言 remain_pct 机械计算=7.0）"""
        from skill_eval import compute_ceiling_indicators
        ci = compute_ceiling_indicators(self._uniform(0.93))
        self.assertTrue(ci['ceiling'])
        self.assertAlmostEqual(ci['indicators']['remain_pct'], 7.0, places=4)  # Σ0.07/20=7%

    def test_indicator3_doc_side_full(self):
        """指标3：文档侧全满（剩余0）+功能侧 0.5→fd=inf>3:1→文档侧触顶（sat/remain 均不触发）"""
        from skill_eval import compute_ceiling_indicators
        keys = self._keys()
        # 功能侧 5 维=CEILING_FUNCTIONAL_DIMS（v5.16.0 token_budget 移出）·文档侧 14 维=CEILING_DOC_DIMS
        functional = {'fuse_mechanism', 'file_clutter',
                      'eval_set_gate', 'trigger_coverage', 'security_hardcode'}
        ratios = {k: (0.5 if k in functional else 1.0) for k in keys}
        ci = compute_ceiling_indicators(self._scores(ratios))
        self.assertTrue(ci['ceiling'])
        ind = ci['indicators']
        self.assertEqual(ind['func_doc_ratio'], 'inf')  # 文档侧剩余=0→fd=inf
        self.assertEqual(ind['saturation_n'], 14)  # 文档侧 14 维全高=14/19=0.737<0.8 指标1不触发
        self.assertAlmostEqual(ind['remain_pct'], 13.16, places=2)  # 5*0.5/19*100=13.16%>8% 指标2不触发
        # → 仅指标3触发·证明"文档侧已触顶"结论成立

    def test_empty_scores_no_ceiling(self):
        """边界③：空 scores/无可算维度→ceiling=False·detail 显式说明（⛔不误报触顶）"""
        from skill_eval import compute_ceiling_indicators
        ci = compute_ceiling_indicators({})
        self.assertFalse(ci['ceiling'])
        self.assertIn('无维度得分可算', ci['detail'])


class TestMergedScan(unittest.TestCase):
    """C09路A+C13（v4.4.0·合并扫描）考题基线：内容类检查吃"主文件+被指针引用细则"判据。
    判据源=skill_eval._build_merged_content docstring（#237④瘦身覆盖率矛盾 + #187-189
    评估覆盖率与文件布局耦合：#188实测"受检的那份反而可能更差"→外置细则逃出内容检查
    → 本函数合并 SKILL.md 被指针引用的细则文件，排除 CHANGELOG（历史记录）+
    normative_vocab 规范文档（RFC2119 MUST/NEVER 合法·全量合并实测误报源）。"""

    @staticmethod
    def _setup(refs_names=('detail.md',), refs_text='', skill_body=''):
        """构造 fixture：SKILL.md 引用 references/{refs_names}"""
        import tempfile
        d = tempfile.TemporaryDirectory()
        refs_dir = os.path.join(d.name, 'references')
        os.makedirs(refs_dir)
        refs_lines = '\n'.join(f'- 细则 → references/{n}' for n in refs_names)
        with open(os.path.join(d.name, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write('---\nname: probe\n---\n\n# Probe\n\n' + refs_lines
                    + '\n\n' + skill_body)
        return d, os.path.join(d.name, 'SKILL.md'), refs_dir

    def test_no_refs_identity(self):
        """正例①：无被引用 references→merged==content（幂等·不合并=零影响）"""
        from skill_eval import _build_merged_content
        d, skill, _ = self._setup(refs_names=())
        try:
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            merged, files, excluded = _build_merged_content(skill, content)
            self.assertEqual(merged, content)
            self.assertEqual(files, [])
            self.assertEqual(excluded, [])
        finally:
            d.cleanup()

    def test_detail_must_scanned(self):
        """正例②：细则含 MUST/NEVER→no_binary 合并逮到（主文件不含时主检查仍满分·#188病根防）"""
        from skill_eval import _build_merged_content, eval_no_binary_annotations
        d, skill, refs_dir = self._setup(
            refs_text='细则正文：本细则 MUST 遵守。')
        try:
            with open(os.path.join(refs_dir, 'detail.md'), 'w', encoding='utf-8') as f:
                f.write('细则正文：本细则 MUST 遵守。')
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            self.assertEqual(eval_no_binary_annotations(content), 1.0)  # 主文件无 MUST
            merged, files, _ = _build_merged_content(skill, content)
            self.assertIn('detail.md', files)
            self.assertEqual(eval_no_binary_annotations(merged), 0.0)  # 合并逮到细则残留
        finally:
            d.cleanup()

    def test_changelog_excluded(self):
        """正例③：CHANGELOG.md（历史变更记录）恒排除·不合并"""
        from skill_eval import _build_merged_content
        d, skill, refs_dir = self._setup(refs_names=('CHANGELOG.md', 'detail.md'))
        try:
            for n, txt in (('CHANGELOG.md', '旧版本 MUST 表述'),
                           ('detail.md', '细则正文')):
                with open(os.path.join(refs_dir, n), 'w', encoding='utf-8') as f:
                    f.write(txt)
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            merged, files, excluded = _build_merged_content(skill, content)
            self.assertNotIn('CHANGELOG.md', files)
            self.assertIn('detail.md', files)
            self.assertTrue(any('CHANGELOG' in e for e in excluded))
        finally:
            d.cleanup()

    def test_normative_vocab_excluded(self):
        """正例④：frontmatter 声明 normative_vocab 的规范文档排除（RFC2119 术语合法·防误报）"""
        from skill_eval import _build_merged_content
        d, skill, refs_dir = self._setup(refs_names=('standard.md',))
        try:
            with open(os.path.join(refs_dir, 'standard.md'), 'w', encoding='utf-8') as f:
                f.write('---\nnormative_vocab: "RFC2119-equivalent"\n---\n\n正文 MUST。')
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            merged, files, excluded = _build_merged_content(skill, content)
            self.assertNotIn('standard.md', files)
            self.assertTrue(any('normative_vocab' in e for e in excluded))
        finally:
            d.cleanup()

    def test_cross_file_number_drift(self):
        """负例①：细则跨文件数字漂移→single_number 合并逮到（档2"6处计数漂移全逮不到"目标）"""
        from skill_eval import _build_merged_content, eval_single_number_source
        d, skill, refs_dir = self._setup(
            skill_body='共 10 条用例。')
        try:
            with open(os.path.join(refs_dir, 'detail.md'), 'w', encoding='utf-8') as f:
                f.write('细则声称 12 条用例。')
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            self.assertEqual(eval_single_number_source(content)[0], 1.0)  # 主文件单值
            merged, files, _ = _build_merged_content(skill, content)
            self.assertIn('detail.md', files)
            ratio, detail = eval_single_number_source(merged)
            self.assertLess(ratio, 1.0)  # 10 vs 12 漂移逮到
            self.assertTrue(any('用例数声明不一致' in m for m in detail['mismatches']))
        finally:
            d.cleanup()

    def test_missing_ref_skip(self):
        """边界：引用文件缺失→跳过不崩溃·excluded 标注缺失"""
        from skill_eval import _build_merged_content
        d, skill, _ = self._setup(refs_names=('ghost.md',))
        try:
            with open(skill, encoding='utf-8') as _fh:
                content = _fh.read()
            merged, files, excluded = _build_merged_content(skill, content)
            self.assertEqual(files, [])
            self.assertTrue(any('缺失' in e for e in excluded))
        finally:
            d.cleanup()


class TestCompletenessAdvisory(unittest.TestCase):
    """C14（v4.5.0·完整性兜底核对机械化）考题基线：completeness.md 9项「❌人工核对」→脚本化 advisory 判据。

    判据源=skill_eval.eval_completeness_advisory docstring + references/completeness.md
    判据表 v1.2（#178 建档25天从未机械执行·机械化它=评估范式由"查自己定义过的可查项"扩到
    "查覆盖充分性"·#940）。⚠advisory 级不计分不计 pass（同 eval_selfdesc_advisory 族·人终判）。
    ⛔覆盖 6 项粗筛；#2/#7（自检清单自省/自举回归）由 completeness 判据表保留人工核对位。"""

    @staticmethod
    def _setup(skill_body='', refs=None, scripts=None):
        """构造 fixture：optional references/scripts 目录与内容。返回 cleanup() 的 tempdir 封装。"""
        import tempfile
        d = tempfile.TemporaryDirectory()
        if refs:
            refs_dir = os.path.join(d.name, 'references')
            os.makedirs(refs_dir)
            for name, text in refs.items():
                with open(os.path.join(refs_dir, name), 'w', encoding='utf-8') as f:
                    f.write(text)
        if scripts:
            scripts_dir = os.path.join(d.name, 'scripts')
            os.makedirs(scripts_dir)
            for name in scripts:
                with open(os.path.join(scripts_dir, name), 'w', encoding='utf-8') as f:
                    f.write('x')
        with open(os.path.join(d.name, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write(skill_body)
        return d, os.path.join(d.name, 'SKILL.md')

    def test_clean_returns_none(self):
        """正例：无 references scripts 目录且 SKILL.md 无可运行性/指标声明→None 静默（§7.5幂等）"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='---\nname: x\n---\n普通内容。')
        try:
            self.assertIsNone(eval_completeness_advisory(skill))
        finally:
            d.cleanup()

    def test_evalset_declared_vs_actual_drift(self):
        """负例：分析型#3 eval-set 声明条数 vs 实际表格行数漂移（差≥3）→ advisory"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='x', refs={'eval-set.md': '共 10 条用例。\n| 1 | a |\n| 2 | b |'})
        try:
            s = eval_completeness_advisory(skill)
            self.assertIsNotNone(s)
            self.assertIn('分析型#3', s)
        finally:
            d.cleanup()

    def test_claim_without_assets(self):
        """负例：分析型#5 声明"已验证"但 references/ 与 scripts/ 皆无实务→advisory"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='本 Skill 已验证、已交付。无资产目录。')
        try:
            s = eval_completeness_advisory(skill)
            self.assertIsNotNone(s)
            self.assertIn('分析型#5', s)
        finally:
            d.cleanup()

    def test_runtime_files_detected(self):
        """负例：流程执行型#4 scripts/ 含运行时状态文件 → advisory"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='x', scripts=['.phaseX_last_run.json', 'app.py'])
        try:
            s = eval_completeness_advisory(skill)
            self.assertIsNotNone(s)
            self.assertIn('流程执行型#4', s)
        finally:
            d.cleanup()

    def test_template_reference_missing(self):
        """负例：通用增项#5 正文引用 references/template.md 但指向物缺失 → advisory"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='按 references/report-template.md 产出。')
        try:
            s = eval_completeness_advisory(skill)
            self.assertIsNotNone(s)
            self.assertIn('通用增项#5', s)
        finally:
            d.cleanup()

    def test_metric_without_formula(self):
        """负例：通用增项#6 量化指标声明无计算式/口径关键词 → advisory（半机械·人终判）"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(skill_body='本 Skill 的完成率指标应达 90%。')
        try:
            # 需命中 "指标" 且无公式词
            s = eval_completeness_advisory(skill)
            self.assertIsNotNone(s)
            self.assertIn('通用增项#6', s)
        finally:
            d.cleanup()


class TestCompletenessGitignore(unittest.TestCase):
    """v4.7.0（B1 常响根治·completeness 误报修正）考题基线：流程执行型#4 gitignore 识别判据。

    病根：completeness_advisory 100% 常响（B1 首轮识别）——scripts/ 下 .phaseX_last_run.json/
    .finalize_last_run.json 已被个人AI档案 .gitignore `**/*_last_run.json` 排除（不随包分发=合规），
    检查器只看磁盘存在性→误报。判据源=eval_completeness_advisory docstring + .gitignore 实测。"""

    @staticmethod
    def _setup(skill_body='x', scripts=None):
        import tempfile
        d = tempfile.TemporaryDirectory()
        if scripts:
            scripts_dir = os.path.join(d.name, 'scripts')
            os.makedirs(scripts_dir)
            for name in scripts:
                with open(os.path.join(scripts_dir, name), 'w', encoding='utf-8') as f:
                    f.write('x')
        with open(os.path.join(d.name, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write(skill_body)
        return d, os.path.join(d.name, 'SKILL.md')

    def test_ignored_runtime_file_silent(self):
        """正例：运行时文件被 git 忽略（ignore_fn=True）→ 静默（被忽略=不随包分发=合规）"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(scripts=['.phaseX_last_run.json'])
        try:
            s = eval_completeness_advisory(skill, ignore_fn=lambda _d, _n: True)
            self.assertIsNone(s)
        finally:
            d.cleanup()

    def test_unignored_runtime_file_advisory(self):
        """负例：运行时文件未被忽略（ignore_fn=False）→ 流程执行型#4 提示"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(scripts=['.phaseX_last_run.json'])
        try:
            s = eval_completeness_advisory(skill, ignore_fn=lambda _d, _n: False)
            self.assertIsNotNone(s)
            self.assertIn('流程执行型#4', s)
        finally:
            d.cleanup()

    def test_ignore_fn_exception_conservative(self):
        """边界：ignore_fn 抛异常 → 保守视为未忽略→提示（防漏报·宁可多报不漏报）"""
        from skill_eval import eval_completeness_advisory

        def boom(_d, _n):
            raise RuntimeError('probe')

        d, skill = self._setup(scripts=['last_run.json'])
        try:
            s = eval_completeness_advisory(skill, ignore_fn=boom)
            self.assertIsNotNone(s)
            self.assertIn('流程执行型#4', s)
        finally:
            d.cleanup()

    def test_default_non_git_repo_conservative(self):
        """边界：默认实现（_git_check_ignored）在非 git 目录 → 无法确认忽略→提示（保守）"""
        from skill_eval import eval_completeness_advisory
        d, skill = self._setup(scripts=['.phaseX_last_run.json'])
        try:
            s = eval_completeness_advisory(skill)  # tempdir 非 git 仓库→git check-ignore 失败→False
            self.assertIsNotNone(s)
            self.assertIn('流程执行型#4', s)
        finally:
            d.cleanup()


class TestAdvisoryFrequency(unittest.TestCase):
    """B1（v4.6.0·advisory触发率统计）考题基线：狼来了治理——常响advisory折叠提示判据。
    判据源=eval_advisory_frequency docstring（#隐忧②狼来了病根·12项advisory全响=没响·
    X级收尾后第一轮"系统观察自己"·愿景③自主进化在评估器身上落地）。"""

    def _mk_history(self, lines):
        d = tempfile.TemporaryDirectory()
        p = os.path.join(d.name, '.advisory_history.jsonl')
        with open(p, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return d, p

    def _line(self, triggers):
        return json.dumps({'ts': '2026-09-05 10:00', 'target': 'probe', 'triggers': triggers})

    def test_no_history_none(self):
        """边界：历史文件不存在 → None 静默（幂等·样本不足不判定）"""
        from skill_eval import eval_advisory_frequency
        self.assertIsNone(eval_advisory_frequency(history_path='/tmp/__nonexist_x__.jsonl'))

    def test_insufficient_samples_none(self):
        """边界：有效样本 < min_samples(5) → None 静默（⛔小样本不判定）"""
        from skill_eval import eval_advisory_frequency
        d, p = self._mk_history([self._line({'a': True})] * 3)
        try:
            self.assertIsNone(eval_advisory_frequency(history_path=p))
        finally:
            d.cleanup()

    def test_ratio_computed(self):
        """正例：8次中5次触发 → n=5·ratio=0.62·非常响（触发率计算正确）"""
        from skill_eval import eval_advisory_frequency
        lines = [self._line({'foo': i < 5}) for i in range(8)]
        d, p = self._mk_history(lines)
        try:
            r = eval_advisory_frequency(history_path=p)
            self.assertIsNotNone(r)
            self.assertEqual(r['freq']['foo']['n'], 5)
            self.assertEqual(r['freq']['foo']['ratio'], 0.62)  # 5/8
            self.assertNotIn('foo', r['frequent'])
        finally:
            d.cleanup()

    def test_frequent_flag(self):
        """负例：7/8次触发=87.5% ≥80% → 常响清单命中（狼来了·建议折叠/转自动）"""
        from skill_eval import eval_advisory_frequency
        lines = [self._line({'bar': i < 7}) for i in range(8)]
        d, p = self._mk_history(lines)
        try:
            r = eval_advisory_frequency(history_path=p)
            self.assertIn('bar', r['frequent'])
        finally:
            d.cleanup()

    def test_record_append(self):
        """正例：_record_advisory_history 追加写且 triggers 落盘可回读（不覆盖历史）"""
        from skill_eval import _record_advisory_history
        d = tempfile.TemporaryDirectory()
        p = os.path.join(d.name, '.advisory_history.jsonl')
        try:
            self.assertTrue(_record_advisory_history('probe', {'x': True}, history_path=p))
            self.assertTrue(_record_advisory_history('probe', {'x': False}, history_path=p))
            with open(p, encoding='utf-8') as f:
                self.assertEqual(len(f.read().splitlines()), 2)
        finally:
            d.cleanup()


class TestCheckerHygiene(unittest.TestCase):
    """B2（v4.6.0·检查器卫生审计）考题基线：带v4.版本标注的检查函数须有直接测试引用。
    判据源=eval_checker_hygiene docstring（l3_conclusion_guard 事故制度化预防·#隐忧②·
    判据立法化=考题基线+负控制·skill-arch-standard §2.2a）。"""

    def _mk(self, src_body, test_body):
        d = tempfile.TemporaryDirectory()
        src = os.path.join(d.name, 'skill_eval.py')
        test = os.path.join(d.name, 'test_skill_eval.py')
        with open(src, 'w', encoding='utf-8') as f:
            f.write(src_body)
        with open(test, 'w', encoding='utf-8') as f:
            f.write(test_body)
        return d, src, test

    def test_missing_files_none(self):
        """边界：源/测试文件缺失 → None 静默（幂等）"""
        from skill_eval import eval_checker_hygiene
        self.assertIsNone(eval_checker_hygiene(src_path='/tmp/__no__.py', test_path='/tmp/__no2__.py'))

    def test_tested_func_clean(self):
        """正例：带v4.标注函数已被测试直接引用 → None（无违规·考题基线在）"""
        from skill_eval import eval_checker_hygiene
        d, src, test = self._mk(
            'def eval_probe_advisory(x):\n    """v4.6.0 判据"""\n    return None\n',
            'from skill_eval import eval_probe_advisory\n')
        try:
            self.assertIsNone(eval_checker_hygiene(src_path=src, test_path=test))
        finally:
            d.cleanup()

    def test_untested_func_flagged(self):
        """负例：带v4.标注函数无测试引用 → ⚪提示（判据无考题基线=立法缺口）"""
        from skill_eval import eval_checker_hygiene
        d, src, test = self._mk(
            'def eval_probe_advisory(x):\n    """v4.6.0 判据"""\n    return None\n',
            'print("no ref")\n')
        try:
            s = eval_checker_hygiene(src_path=src, test_path=test)
            self.assertIsNotNone(s)
            self.assertIn('eval_probe_advisory', s)
        finally:
            d.cleanup()

    def test_old_func_not_flagged(self):
        """边界：无v4.标注的存量函数未被引用 → 不提示（只盯新判据·防存量噪音·间接覆盖存在）"""
        from skill_eval import eval_checker_hygiene
        d, src, test = self._mk(
            'def eval_legacy_check(x):\n    """旧函数"""\n    return None\n',
            'print("no ref")\n')
        try:
            self.assertIsNone(eval_checker_hygiene(src_path=src, test_path=test))
        finally:
            d.cleanup()


class TestCheckerComplexity(unittest.TestCase):
    """B3（v4.6.0·评估器复杂度度量）考题基线：ast 统计自身体量（瘦身前提·先测量再拆）。
    判据源=compute_checker_complexity docstring（210KB/20维度·体量须可观测·#隐忧②）。"""

    def test_missing_file_none(self):
        """边界：源文件缺失 → None 静默"""
        from skill_eval import compute_checker_complexity
        self.assertIsNone(compute_checker_complexity(src_path='/tmp/__no__.py'))

    def test_counts_correct(self):
        """正例：2函数文件 → func_count=2·max=3·heaviest=b（行数统计正确）"""
        from skill_eval import compute_checker_complexity
        d = tempfile.TemporaryDirectory()
        p = os.path.join(d.name, 'probe.py')
        with open(p, 'w', encoding='utf-8') as f:
            f.write('def a():\n    pass\n\n\ndef b():\n    x = 1\n    return x\n')
        try:
            r = compute_checker_complexity(src_path=p)
            self.assertEqual(r['func_count'], 2)
            self.assertEqual(r['max_func_lines'], 3)  # b 占3行
            self.assertEqual(r['heaviest'][0]['name'], 'b')
            self.assertEqual(r['total_lines'], 7)
        finally:
            d.cleanup()

    def test_heaviest_topn(self):
        """正例：top_n=1 → 只返回最重一个"""
        from skill_eval import compute_checker_complexity
        d = tempfile.TemporaryDirectory()
        p = os.path.join(d.name, 'probe.py')
        with open(p, 'w', encoding='utf-8') as f:
            f.write('def a():\n    pass\n\n\ndef b():\n    pass\n')
        try:
            r = compute_checker_complexity(src_path=p, top_n=1)
            self.assertEqual(len(r['heaviest']), 1)
        finally:
            d.cleanup()


class TestEvidenceSummary(unittest.TestCase):
    """A1（v4.6.0·证据复核入口）考题基线：exercised 档人可读汇总（自举分数可查证）。
    判据源=format_evidence_summary docstring（#隐忧①自举100分黑箱·最后一公里）。"""

    def test_none_evidence(self):
        """边界：无证据档位 → 'na（无证据档位）'"""
        from skill_eval import format_evidence_summary
        self.assertEqual(format_evidence_summary(None), 'na（无证据档位）')

    def test_exercised_summary(self):
        """正例：exercised+2条证据 → 汇总含条数/ceiling/明细指针（人可一键复核）"""
        from skill_eval import format_evidence_summary
        s = format_evidence_summary({
            'grade': 'exercised', 'ceiling': 94, 'capped_score': 94,
            'upgrade_refs': [{'source': 'systemlog'}, {'source': 'archive'}],
        })
        self.assertIn('2条运行时证据', s)
        self.assertIn('ceiling=94', s)
        self.assertIn('evidence.upgrade_refs', s)

    def test_wired_summary(self):
        """正例：wired → 简洁行含'不升exercised'（⛔无实跑不升档·诚实）"""
        from skill_eval import format_evidence_summary
        s = format_evidence_summary({'grade': 'wired', 'ceiling': 84})
        self.assertIn('wired', s)
        self.assertIn('不升exercised', s)

    def test_present_summary(self):
        """正例：present → 静态简洁行"""
        from skill_eval import format_evidence_summary
        s = format_evidence_summary({'grade': 'present', 'ceiling': 74})
        self.assertIn('present', s)
        self.assertIn('静态', s)


class TestDesignPhilosophyBatchAdvisories(unittest.TestCase):
    """2026-09-05设计哲学反哺批A/B/C：五个新 advisory 的 negative-case 冒烟闸。
    判据源=skill_eval 各函数 docstring（P1 honest_boundary/evidence_tier_verification·
    P2 pseudo_determinism/output_format_physical·批C unwired_interface）。
    负例验证：构造"会触发"的输入 → 必须返回非None（advisory显形）·⛔不得静默假绿。
    对应台账#295起·设计哲学§五 P1×2/P2×3 落地核对。"""

    def _write(self, content, name='SKILL.md'):
        import tempfile
        d = tempfile.TemporaryDirectory()
        with open(os.path.join(d.name, name), 'w', encoding='utf-8') as f:
            f.write(content)
        return d

    def test_honest_boundary_no_decl_causes_advisory(self):
        """负例①：honest_boundary 通篇无边界声明→advisory（非None）"""
        from skill_eval import eval_honest_boundary_advisory
        d = self._write('# 测试 skill\n\n| 检查项 | 通过 |\n| 自动检查 | ✅ |\n| 机械校验 | ✅ |\n')
        try:
            self.assertIsNotNone(eval_honest_boundary_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_honest_boundary_decl_silent(self):
        """正例①：honest_boundary 已有边界声明+语境锚→None 静默"""
        from skill_eval import eval_honest_boundary_advisory
        body = ('名称: x\n\n本脚本确定性边界：⛔判断部分由 AI 终判，机制部分由脚本保证。\n')
        d = self._write(body)
        try:
            self.assertIsNone(eval_honest_boundary_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_pseudo_determinism_over_half_advisory(self):
        """负例②：pseudo_determinism 伪确定性占比>50%→advisory（非None）"""
        from skill_eval import eval_pseudo_determinism_advisory
        body = ('# s\n\n10 项检查（关键词命中检查、计数出现检查、正则命中检查均计）\n'
                '另含 1 项结构校验、1 项一致性校验。\n')
        d = self._write(body)
        try:
            self.assertIsNotNone(eval_pseudo_determinism_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_pseudo_determinism_no_declares_silent(self):
        """正例②：pseudo_determinism 无声明检查类→None 静默"""
        from skill_eval import eval_pseudo_determinism_advisory
        d = self._write('# s\n\n无任何检查声明。\n')
        try:
            self.assertIsNone(eval_pseudo_determinism_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_output_format_physical_no_bind_advisory(self):
        """负例③：output_format_physical 有交付声明但无脚本产物依赖→advisory（非None）"""
        from skill_eval import eval_output_format_physical_advisory
        body = '# s\n\n## 交付\n报告模板说明如下，AI 生成最终文档格式。\n'
        d = self._write(body)
        try:
            self.assertIsNotNone(eval_output_format_physical_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_output_format_physical_bound_silent(self):
        """正例③：output_format_physical 已有物理依赖→None 静默"""
        from skill_eval import eval_output_format_physical_advisory
        body = '# s\n\n## 交付\n报告模板各项字段引用脚本输出 JSON 一键复制即可。\n'
        d = self._write(body)
        try:
            self.assertIsNone(eval_output_format_physical_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_unwired_interface_unresolved_advisory(self):
        """负例④：unwired_interface 预留但 60 行内未落地→advisory（非None）
        ⛔措辞规避 done 信号词（已接线/已实现/实装）——否则窗口检查误判'已解决'假静默"""
        from skill_eval import eval_unwired_interface_advisory
        body = '# s\n\n本机制预留扩展点，未来版本再接入使用。\n' + 'x\n' * 70
        d = self._write(body)
        try:
            self.assertIsNotNone(eval_unwired_interface_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_unwired_interface_wired_silent(self):
        """正例④：unwired_interface 预留且已实现→None 静默"""
        from skill_eval import eval_unwired_interface_advisory
        body = '# s\n\n预留接口已接线：x 机制已实装。\n'
        d = self._write(body)
        try:
            self.assertIsNone(eval_unwired_interface_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_evidence_tier_claim_vs_actual_advisory(self):
        """负例⑤：evidence_tier 声称实跑级证据但实算档位不足→advisory（非None）"""
        from skill_eval import eval_evidence_tier_verification_advisory
        # 虚构名字（不进系统日志）→ 实算只会是 present/wired·与声称的 exercised 不符→告警
        content = ('name: nonexist_skill_zz_evidence\n'
                   '运行时证据已收集 exercised 档位解锁 实测通过 100分\n')
        d = self._write(content)
        try:
            self.assertIsNotNone(
                eval_evidence_tier_verification_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()

    def test_evidence_tier_no_claim_silent(self):
        """正例⑤：evidence_tier 无高档声称→None 静默"""
        from skill_eval import eval_evidence_tier_verification_advisory
        content = 'name: nonexist_skill_zz_quiet\nplain doc, no evidence claim\n'
        d = self._write(content)
        try:
            self.assertIsNone(
                eval_evidence_tier_verification_advisory(os.path.join(d.name, 'SKILL.md')))
        finally:
            d.cleanup()


class TestV4121CLFixes(unittest.TestCase):
    """v4.12.1 CL批考题基线（§2.2a 判据立法化：正例+负控制·awaken Loop #040教训应用——
    同类扫描升维度到"守卫自身是否被自己的扫描域漏掉"）"""

    def _tmp_skill(self, files):
        import tempfile, os
        d = tempfile.mkdtemp(prefix="cl4121_")
        files = dict(files)
        files.setdefault('SKILL.md', "---\nname: tmpskill\nversion: 1.0.0\n---\n\n# tmp\n")
        for rel, text in files.items():
            p = os.path.join(d, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(text)
        return os.path.join(d, 'SKILL.md')

    def test_fuse_in_module_counted(self):
        """E-1正例：合规熔断器在外置模块（被指针引用）→ 合并域应吃到"""
        from skill_eval import _build_merged_content, eval_fuse_mechanism
        fuse_block = (
            "### 步骤X：读配置\n📦 产出物：cfg\n"
            "🔌 熔断器\n├─ 成功条件：Read返回非空\n├─ 失败处理：中止\n"
            "├─ 可修正参数：路径 → 检查 config.yaml 是否存在\n├─ 重试次数：1\n"
            "└─ 降级方案：无——中止本路径\n")
        skill = self._tmp_skill({
            'SKILL.md': "---\nname: modular\nversion: 1.0.0\n---\n\n# modular\n\n"
                        "✅DO Read `references/detail.md` 执行细则后再跑。\n",
            'references/detail.md': fuse_block})
        with open(skill, encoding='utf-8') as _fh:
            body = _fh.read()
        fused, _mf, _ex = _build_merged_content(skill, body)
        r_mod, _ = eval_fuse_mechanism(fused)
        r_main, _ = eval_fuse_mechanism(body)
        self.assertGreater(r_mod, 0.9, '外置模块含五字段熔断器→合并域应≈满分')
        self.assertLess(r_main, r_mod, '主文-only应低于合并域（回退merged_content接线本考题必红·R2-N-09修复）')
        import skill_eval as _se
        _res = _se.evaluate_skill(skill)  # 全链路接线断言：evaluate_skill 顶层结果必须吃到外置熔断器
        self.assertGreater(_res['scores'].get('fuse_mechanism', 0), 0,
                           'R2-N-09：回退 L3624 merged_content→content 此断言必红（此前考题测不到接线）')

    def test_eval_set_dup_declared_selfconsistent(self):
        """E-2正例：同名声明重复两处（34+34）→ 新自洽不变式不报 mismatch"""
        from skill_eval import _check_eval_set_count
        skill = self._tmp_skill({})
        with open(skill, encoding='utf-8') as _fh:
            body2 = _fh.read() + "\n（34条用例/5类）\n（34条用例/5类：应触发/不应触发/运行时/边界/触发集）\n"
        d = os.path.dirname(skill)
        rows = "\n".join(f"| {i} | x | y |" for i in range(1, 35))
        os.makedirs(os.path.join(d, 'references'), exist_ok=True)
        with open(os.path.join(d, 'references', 'eval-set.md'), 'w', encoding='utf-8') as f:
            f.write("## 用例\n\n| # | 输入 | 期望 |\n|---|---|---|\n" + rows + "\n")
        c = _check_eval_set_count(body2, os.path.join(d, 'references'))
        self.assertIsNone(c.get('mismatch'), f"重复同名声明不应报不一致: {c}")
        self.assertTrue(c['passed'] and c['increment'], '且真正比对通过')

    def test_eval_set_wrong_count_still_caught(self):
        """E-2负控制：改错数字仍须逮到（修复不转瞎）"""
        from skill_eval import _check_eval_set_count
        skill = self._tmp_skill({})
        with open(skill, encoding='utf-8') as _fh:
            body2 = _fh.read() + "\n（99条用例）\n"
        d = os.path.dirname(skill)
        rows = "\n".join(f"| {i} | x | y |" for i in range(1, 35))
        os.makedirs(os.path.join(d, 'references'), exist_ok=True)
        with open(os.path.join(d, 'references', 'eval-set.md'), 'w', encoding='utf-8') as f:
            f.write("| # | 输入 | 期望 |\n|---|---|---|\n" + rows + "\n")
        c = _check_eval_set_count(body2, os.path.join(d, 'references'))
        self.assertIsNotNone(c.get('mismatch'), '99声明vs34实盘必须报不一致')

    def test_t_numbered_rows_counted(self):
        """E-2第四形态：T编号表不再恒0行（旧内联正则盲区·唯一实现迁移验证）"""
        from skill_eval import _evalset_rows
        text = "\n".join(f"| T{i} | x | y |" for i in range(1, 6))
        self.assertEqual(_evalset_rows(text), 5)
        import tempfile as _tf, os as _os
        from skill_eval import _check_eval_set_count
        d = _tf.mkdtemp(prefix="cl4122_")
        _os.makedirs(_os.path.join(d, 'references'))
        with open(_os.path.join(d, 'references', 'eval-set.md'), 'w', encoding='utf-8') as f:
            f.write("| # | 输入 |\n|---|---|\n" + text + "\n")
        c = _check_eval_set_count("（5条用例）", os.path.join(d, 'references'))
        self.assertTrue(c.get('increment'), 'R2-N-09：T编号表必须被真正比对（回退旧内联正则→actual=0→increment False 本断言必红）')

    def test_gate_step_conflict_caught(self):
        """F-STEP：同一主题"收尾门禁N步"五/七冲突须发红"""
        from skill_eval import eval_single_number_source
        ratio, detail = eval_single_number_source("收尾门禁五步(⓪-⑤) … 收尾门禁七步(⓪-⑥)")
        self.assertLess(ratio, 1.0, f'应逮到不一致: {detail}')

    def test_honest_flag_label_is_dependency_not_cured(self):
        """E-3第四形态：红字标签与被查事实同名（依赖声明漂移≠固化副本漂移）"""
        from skill_eval import compute_honest_pass
        r = {'total': 90, 'gate': {'g': True}, 'evidence': {}}
        v = {'passed': True, 'dependencies': [{'name': 'x', 'status': '🔴 drift'}]}
        _p, flags, _rp = compute_honest_pass(r, v)
        self.assertTrue(any(f.startswith('依赖声明漂移') for f in flags), flags)
        self.assertFalse(any('固化引用漂移' in f for f in flags), '固化字样不得冒名dependencies漂移')

    def test_gate_count_declarations_match_impl(self):
        """F-GATENOCHECK：封口道数声明（SKILL/finalize docstring/phase4）==实现硬门禁最大编号"""
        import re as _re
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/ -> skill root（本套件为仓内自测·不可独立拷贝运行·R2-N-08声明边界注）
        with open(os.path.join(root, 'scripts', 'finalize_report.py'), encoding='utf-8') as _f:
            fr = _f.read()
        n_impl = max(int(x) for x in _re.findall(r'硬门禁(\d+)', fr))
        n_appends = fr.count("detail.append(('")
        self.assertEqual(n_appends, n_impl,
                         f'门禁装配数{n_appends}≠编号{n_impl}——删append摘线即红（R3攻1看护·v4.12.3三线一致断言）')
        for path, pat in ((os.path.join(root, 'SKILL.md'), r'(\d+)道检查'),
                          (os.path.join(root, 'references', 'phase4-followup.md'), r'跑(\d+)道检查'),
                          (os.path.join(root, 'scripts', 'finalize_report.py'), r'"""(\d+)道检查'),
                          (os.path.join(root, 'references', 'machine-acceptance.md'), r'(\d+)道'),
                          (os.path.join(root, 'scripts', 'pkg_report_check.py'), r'(\d+)道检查'),
                          (os.path.join(root, 'references', 'task-standards.json'), r'单入口(\d+)道检查')):  # R2-N-08：声明点全集入域（v4.12.1 漏2处教训）
            with open(path, encoding='utf-8') as _f2:
                txt = _f2.read()
            nums = set(_re.findall(pat, txt))
            self.assertTrue(nums and all(int(n) == n_impl for n in nums),
                            f'{os.path.basename(path)} 道数声明{sorted(nums)}≠实现{n_impl}（F-GATE13回归哨兵·v4.12.2全域版）')

    def test_clutter_catches_scripts_bak(self):
        """F-CLUTTER：scripts/ 下 .bak 残留须被扩展后的扫描域逮到"""
        from skill_eval import eval_file_clutter
        skill = self._tmp_skill({})
        d = os.path.dirname(skill)
        os.makedirs(os.path.join(d, 'scripts'), exist_ok=True)
        with open(os.path.join(d, 'scripts', 'evil.py.bak-20260920'), 'w') as _fw:
            _fw.write('x')
        ratio, detail = eval_file_clutter(skill)
        self.assertTrue(any('evil.py.bak' in str(x) for x in detail), f'scripts .bak应入细节: {detail}')
        self.assertLess(ratio, 1.0)

    def test_clutter_clean_skill_unhurt(self):
        """F-CLUTTER负控制：干净skill不误伤"""
        from skill_eval import eval_file_clutter
        skill = self._tmp_skill({})
        ratio, _ = eval_file_clutter(skill)
        self.assertGreaterEqual(ratio, 0.9, '新建tmp skill除可能的登记类提示外不应有.bak误报')





class TestV4124R4Closure(unittest.TestCase):
    """v4.12.4 R4收口考题：rc纯函数三态/自指证据红/载体-1可达（MUT-5类存活面清零）"""

    def _rf(self):
        import os, importlib.util
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location('rf_v4124', os.path.join(root, 'scripts', 'record_fix.py'))
        m = importlib.util.module_from_spec(spec)
        _obw = sys.dont_write_bytecode; sys.dont_write_bytecode = True  # v4.12.4b 防测试写pyc污染被评树
        try:
            spec.loader.exec_module(m)
        finally:
            sys.dont_write_bytecode = _obw
        return m

    def test_overdue_rc_three_states(self):
        m = self._rf()
        self.assertEqual(m.overdue_rc(None), 5, 'fail-closed必须是专用码5（MUT-5摘rc5回退即红）')
        self.assertEqual(m.overdue_rc(14), 4)
        self.assertEqual(m.overdue_rc(0), 0)

    def test_carrier_minus_one_written_on_failclosed(self):
        import os, tempfile
        m = self._rf()
        d = tempfile.mkdtemp()
        led = os.path.join(d, 'fix_ledger.json')
        cp = os.path.join(d, 'c.md')
        with open(led, 'w') as f:
            f.write('{ broken')
        days, *_ = m.check_pending_review_overdue(ledger=led, counter_path=cp)
        self.assertIsNone(days)
        with open(cp, encoding='utf-8') as _fh:
            txt = _fh.read()
        self.assertIn('pending_review_overdue_days: -1', txt,
                      'fail-closed必落载体-1（R4-F-C：案发现场进台账，载体不得留旧值假健康）')

    def test_smoke_guard_rejects_self_reference(self):
        import os, tempfile, importlib.util
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = importlib.util.spec_from_file_location('fr_v4124', os.path.join(root, 'scripts', 'finalize_report.py'))
        fm = importlib.util.module_from_spec(spec)
        _obw = sys.dont_write_bytecode; sys.dont_write_bytecode = True  # v4.12.4b 防测试写pyc污染被评树
        try:
            spec.loader.exec_module(fm)
        finally:
            sys.dont_write_bytecode = _obw
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'r.md')
        with open(p, 'w') as f:
            f.write('验证深度: 实测通过\n冒烟证据: %s\n' % p)
        ok, note = fm.check_smoke_evidence(p)
        self.assertFalse(ok, f'自指证据必须红（R4-F-A）: {note}')


class TestV4123Guards(unittest.TestCase):
    """v4.12.3 R3收口考题：共享实装/冒烟绑定/fail-closed（回退必红·族状看护）"""

    def test_gate15_shared_impl_no_dup_parser(self):
        import os
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'scripts', 'finalize_report.py'), encoding='utf-8') as f:
            fr = f.read()
        self.assertIn('record_fix_g15', fr, '门禁15必须走record_fix共享实装（R3攻3双算法回退即红）')
        self.assertNotIn("os.path.expanduser('[记忆共享中心]/评估知识库/test_results/fix_ledger.json')", fr,
                         'finalize 内不得再自带 fix_ledger 解析（双实现=相反结论之源）')

    def test_smoke_guard_tripass(self):
        import os, tempfile
        import importlib.util as ilu
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = ilu.spec_from_file_location('fr_g16', os.path.join(root, 'scripts', 'finalize_report.py'))
        m = ilu.module_from_spec(spec); spec.loader.exec_module(m)
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'r.md')
        with open(p, 'w') as f:
            f.write('验证深度: 实测通过（冒烟✅）\n')
        ok2, n2 = m.check_smoke_evidence(p)
        self.assertFalse(ok2, f'宣称实测无证据行必须红（门禁16回退即红）: {n2}')
        with open(p, 'w') as f:
            f.write('验证深度: 实测通过\n冒烟证据: %s\n' % os.path.abspath(__file__))
        ok3, _ = m.check_smoke_evidence(p)
        self.assertTrue(ok3, '路径实存应绿')
        with open(p, 'w') as f:
            f.write('验证深度: 实测通过\n冒烟证据: /nonexistent_zs/xx.log\n')
        ok4, _ = m.check_smoke_evidence(p)
        self.assertFalse(ok4, '路径不存在必须红')
        with open(p, 'w') as f:
            f.write('验证深度: 静态文档级\n')
        ok5, _ = m.check_smoke_evidence(p)
        self.assertTrue(ok5, '非实测通过标签为合法终态')

    def test_overdue_failclosed(self):
        import os, tempfile, importlib.util as ilu
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        spec = ilu.spec_from_file_location('rf_g', os.path.join(root, 'scripts', 'record_fix.py'))
        rf = ilu.module_from_spec(spec); spec.loader.exec_module(rf)
        d = tempfile.mkdtemp()
        led = os.path.join(d, 'fix_ledger.json')
        with open(led, 'w') as f:
            f.write('{ broken json')
        days, _o, _n, _m = rf.check_pending_review_overdue(ledger=led, counter_path=os.path.join(d, 'c.md'))
        self.assertIsNone(days, '损坏台账→None（fail-closed）不得为0')
        with open(os.path.join(d, 'absent.json.corrupt.t'), 'w') as f:
            f.write('{}')  # 侧车名须随被检ledger口径
        days2, *_rest = rf.check_pending_review_overdue(ledger=os.path.join(d, 'absent.json'), counter_path=os.path.join(d, 'c.md'))
        self.assertIsNone(days2, '.corrupt侧车在位→None（案发现场不得被吃掉·R3攻2）')



class TestDirectionGateAdvisory(unittest.TestCase):
    """方向闸 advisory 回归（v4.13.2 首建·v4.14.0 扩 A1 载体核验·首版误定v4.13.3已随判级改正）。

    背景：v4.13.2 的五负例只**手工实证**跑过·`test_skill_eval.py` 里 direction_gate
    出现 0 次 ⇒ 那不是回归（本套件挂了照样发现不了）。v4.14.0 固化入正式套件。
    守卫编写规范 原则3：绿灯需要负例证据——从没报过 NOT OK 的守卫，其 OK 不可信。

    ⛔ 本 advisory 只检**声明-执行一致性**（声明了就有没有·防护被没被摘），
      ⛔ 不检语义（守卫编写规范 L706：脚本不许校验语义）——故无「方向问得对不对」的用例。
    """

    def _fixture(self, mutate=None, drop_std=False, decl=True, broken_json=False):
        """造临时被评侧 Skill 副本（不碰真实 clock-loop）"""
        d = tempfile.mkdtemp(prefix='dgfix_')
        self.addCleanup(shutil.rmtree, d, True)
        if decl:
            with open(os.path.join(d, 'SKILL.md'), 'w') as f:
                f.write('# T\n\n阶段0.5 方向闸 direction_gate A1 A2 A3\n')
        std_path = os.path.join(d, 'references', 'task-standards.json')
        if drop_std:
            return d
        os.makedirs(os.path.dirname(std_path), exist_ok=True)
        if broken_json:
            with open(std_path, 'w') as f:
                f.write('{ not valid json')
            return d
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'references', 'task-standards.json')
        with open(src) as f:
            std = json.load(f)
        if mutate:
            mutate(std)
        with open(std_path, 'w') as f:
            json.dump(std, f, ensure_ascii=False, indent=2)
        return d

    def _cidx(self, std, cid):
        for i, c in enumerate(std['direction_gate']['checks']):
            if c.get('id') == cid:
                return i
        self.fail('direction_gate 缺 %s 项' % cid)

    # ---- 正例 ----
    def test_01_self_compliant_silent(self):
        """clock-loop 自身合规 → 静默（advisory 不许对自家噪声）"""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertIsNone(eval_direction_gate_advisory(root))

    def test_02_unrelated_skill_silent(self):
        """无关 Skill（只写「阶段0.5」）→ 静默·不得全库狼来了"""
        d = tempfile.mkdtemp(prefix='dgfix_')
        self.addCleanup(shutil.rmtree, d, True)
        with open(os.path.join(d, 'SKILL.md'), 'w') as f:
            f.write('# 普通 Skill\n\n阶段0.5 就是个普通小节\n')
        self.assertIsNone(eval_direction_gate_advisory(d))

    # ---- 负例（本批核心：A1 载体被摘必报错）----
    def test_03_a1_carrier_removed_detected(self):
        """🔺 A1 载体被摘（source 没了）→ advisory 必须报错"""
        def mut(std):
            std['direction_gate']['checks'][self._cidx(std, 'A1')].pop('source')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out, 'A1 载体被摘·必须捕获')
        self.assertIn('checks[A1].source', out)

    def test_04_a1_carrier_field_removed_detected(self):
        """🔺 A1 carrier 字段被摘 → 退回纯启发·必须报错"""
        def mut(std):
            std['direction_gate']['checks'][self._cidx(std, 'A1')].pop('carrier')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out, 'A1 carrier 被摘·必须捕获')
        self.assertIn('checks[A1].carrier', out)

    def test_05_a1_mechanical_anchor_empty_detected(self):
        """🔺 A1 carrier.mechanical_anchor 清空 → 机械锚声明失效·必须报错"""
        def mut(std):
            c = std['direction_gate']['checks'][self._cidx(std, 'A1')]
            c['carrier']['mechanical_anchor'] = ''
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('mechanical_anchor', out)

    def test_06_a1_check_removed_detected(self):
        """🔺 整个 A1 项被删 → 三条不同构·必须报错"""
        def mut(std):
            std['direction_gate']['checks'].pop(self._cidx(std, 'A1'))
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('checks[A1]', out)

    def test_07_a2_source_removed_detected(self):
        """🔺 A2 source 被摘 → 同构核验须覆盖 A2（不得厚此薄彼）"""
        def mut(std):
            std['direction_gate']['checks'][self._cidx(std, 'A2')].pop('source')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('checks[A2].source', out)

    def test_08_a3_source_removed_detected(self):
        """🔺 A3 source 被摘 → 同构核验须覆盖 A3"""
        def mut(std):
            std['direction_gate']['checks'][self._cidx(std, 'A3')].pop('source')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('checks[A3].source', out)

    # ---- v4.13.2 既有四项·防本批回归 ----
    def test_09_dangling_pointer_detected(self):
        """🔺 声明了方向闸但无 task-standards.json → 悬空指针"""
        out = eval_direction_gate_advisory(self._fixture(drop_std=True))
        self.assertIsNotNone(out)
        self.assertIn('悬空指针', out)

    def test_10_broken_json_detected(self):
        """🔺 标准库 JSON 损坏 → 方向闸失效必须报错"""
        out = eval_direction_gate_advisory(self._fixture(broken_json=True))
        self.assertIsNotNone(out)
        self.assertIn('不可解析', out)

    def test_11_governance_field_removed_detected(self):
        """🔺 not_a_governance_tool 被摘 → 防降级陷阱失守"""
        def mut(std):
            std['direction_gate'].pop('not_a_governance_tool')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('not_a_governance_tool', out)

    def test_12_machine_gap_removed_detected(self):
        """🔺 machine_gap 被摘 → 假装已机检"""
        def mut(std):
            std['direction_gate']['execution'].pop('machine_gap')
        out = eval_direction_gate_advisory(self._fixture(mutate=mut))
        self.assertIsNotNone(out)
        self.assertIn('machine_gap', out)

    # ---- 载体一致性·机械可验 ----
    def test_13_a1_carrier_parity_with_a2_a3(self):
        """验收项「不厚此薄彼」：A1 与 A2/A3 键结构同构（source 齐·carrier 为 A1 专有补充）"""
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(root, 'references', 'task-standards.json')) as f:
            checks = {c['id']: c for c in json.load(f)['direction_gate']['checks']}
        for cid in ('A1', 'A2', 'A3'):
            self.assertIn('source', checks[cid], '%s 缺 source' % cid)
            self.assertTrue(str(checks[cid]['source']).strip(), '%s source 为空' % cid)
            self.assertIn('question', checks[cid])
            self.assertIn('gate', checks[cid])
            self.assertIn('fail_action', checks[cid])
        self.assertIn('carrier', checks['A1'], 'A1 必须有 carrier（载体形态声明）')
        self.assertNotIn('carrier', checks['A2'], '⛔ 不得借本批给 A2/A3 乱加字段')


class TestDerivedStalenessAdvisory(unittest.TestCase):
    """派生态无锚裸奔 advisory 回归（v4.15.0 L3反哺T1·2026-10-03 你令落地）。

    只判形态存续（锚字段在不在），⛔不判新鲜度语义（守卫规范 L706）——
    故负例=无锚裸奔必须响，正例=有锚/非派生态/超范围必须静默。
    """

    def _mk(self, files):
        from skill_eval import eval_derived_staleness_advisory
        d = tempfile.mkdtemp(prefix='dsfix_')
        self.addCleanup(shutil.rmtree, d, True)
        for name, body in files.items():
            fp = os.path.join(d, name)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(body)
        return eval_derived_staleness_advisory(d)

    # ---- 正例（静默） ----
    def test_01_no_derived_files_silent(self):
        self.assertIsNone(self._mk({'SKILL.md': '# T\n', 'references/a.md': 'x'}))

    def test_02_snapshot_with_timestamp_anchor_silent(self):
        self.assertIsNone(self._mk({'data_snapshots/snap_2026-10.json':
                                    '{"timestamp": "2026-10-03 09:00", "v": 1}'}))

    def test_03_cache_md_with_cn_anchor_silent(self):
        self.assertIsNone(self._mk({'_cache_report.md': '生成时间：2026-10-03\n内容\n'}))

    def test_04_non_text_scope_silent(self):
        # 非文本扩展名不入扫描域（.png 不进包检查范围）
        self.assertIsNone(self._mk({'snapshot.png': 'binary-ish'}))

    def test_08_date_key_cache_silent(self):
        # N3假阳性收编：日期键缓存（daily_quotes_cache 形态）自带新鲜度锚
        self.assertIsNone(self._mk({'scripts/daily_quotes_cache.json':
                                    '{"daily_quotes": {"2026-03-13": {"quote": "x"}}}'}))

    def test_09_readme_declaration_silent(self):
        # N3假阳性收编：data_snapshots/README.md 是目录声明文书非实体
        self.assertIsNone(self._mk({'data_snapshots/README.md': '本目录为运行产物，发布排除'}))

    # ---- 负例（必须响） ----
    def test_05_snapshot_naked_fires(self):
        out = self._mk({'data_snapshots/rates.json': '{"rejection_rate": 100.0, "note": "快照"}'})
        self.assertIsNotNone(out, '无锚快照必须报（ggs stats 实证同族）')
        self.assertIn('rates.json', out)

    def test_06_last_run_naked_fires(self):
        out = self._mk({'scripts/.foo_last_run.json': '{"ok": true}'})
        self.assertIsNotNone(out, 'last_run 无锚必须报')

    def test_07_mixed_counts_correct(self):
        # 两个无锚一个有锚→报2个；计数真实
        out = self._mk({'data_snapshots/a.json': '{}',
                        'data_snapshots/b.json': '{"collected_at": 1}',
                        'scripts/c_last_run.json': '{}'})
        self.assertIsNotNone(out)
        self.assertIn('2 个', out)
        self.assertNotIn('b.json', out.split('——')[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)

