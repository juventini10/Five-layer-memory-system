#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""distill_due_core 负例测试（v8.3.3 补记 v8.3.1 声明的 5/5 负例实物·clock-loop E路径Loop逮补）

锚定 CHANGELOG v8.3.1 五条证据，today 钉死确定性可跑（不依赖真实台账内容）。
运行：python3 -m unittest test_distill_core -v
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import datetime
import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "distill_due_core", Path(__file__).resolve().parent / "distill_due_core.py")
core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(core)

TODAY = datetime.date(2026, 10, 3)
TYPES = {"🧠 成长箱蒸馏": {"match": "成长箱蒸馏"},
         "📓 日记月报": {"match": "日记月报"},
         "📊 系统日志蒸馏": {"match": "系统日志蒸馏"},
         "🔄 统一蒸馏管道": {"match": "统一蒸馏管道"}}


def row(d, t, nxt):
    return "| %s | %s | 产物 | 摘要 | %s |" % (d, t, nxt)


class TestDistillCore(unittest.TestCase):

    def test_01_month_segment_multirow_take_last(self):
        """负例1·月段内多行取最后一行（旧due_check取第一行病·成长箱误报根因）"""
        content = "\n".join([row("2026-10-01", "🧠 成长箱蒸馏", "2026-12-31"),
                              row("2026-10-02", "🧠 成长箱蒸馏", "2026-11-01")])
        self.assertEqual(core.extract_expected(content, TYPES),
                         {"🧠 成长箱蒸馏": "2026-11-01"})

    def test_02_onetime_dash_silent(self):
        """负例2·一次性任务 `—` 静默，且⛔不许倒序回扫把执行日误当下次日"""
        only = row("2026-10-02", "🔄 统一蒸馏管道（3月补蒸馏）", "—")
        self.assertEqual(core.extract_expected(only, TYPES), {})
        with_valid = row("2026-09-30", "🔄 统一蒸馏管道", "2026-11-01") + "\n" + only
        self.assertEqual(core.extract_expected(with_valid, TYPES),
                         {"🔄 统一蒸馏管道": "2026-11-01"})

    def test_03_todo_region_excluded(self):
        """负例3·调度器自生成TODO区剔除（自读自写粘滞→假逾期）"""
        content = ("<!-- DISTILLATION-TODO:START -->\n"
                   + row("2026-10-03", "📓 日记月报", "2026-09-15")
                   + "\n<!-- DISTILLATION-TODO:END -->")
        self.assertEqual(core.extract_expected(content, TYPES), {})
        self.assertEqual(core.check_overdue(content, TYPES, TODAY), [])

    def test_04_cross_month_blindspot_eliminated(self):
        """负例4·旧月段独有类型仍可取到（scheduler旧版只扫最新月段盲区根治）"""
        content = ("# 2026-10\n" + row("2026-10-01", "🧠 成长箱蒸馏", "2026-11-01")
                   + "\n# 2026-09\n" + row("2026-09-05", "📊 系统日志蒸馏", "2026-11-01"))
        self.assertEqual(core.extract_expected(content, TYPES),
                         {"🧠 成长箱蒸馏": "2026-11-01", "📊 系统日志蒸馏": "2026-11-01"})

    def test_05_positive_four_types_zero_overdue(self):
        """正例·真实台账口径四类型全 2026-11-01 → today(10-03) 零逾期；括号后缀归并主类(5类假象不复发)"""
        content = "\n".join([row("2026-10-01", "🧠 成长箱蒸馏", "2026-11-01"),
                              row("2026-10-01", "📓 日记月报", "2026-11-01"),
                              row("2026-10-01", "📊 系统日志蒸馏", "2026-11-01"),
                              row("2026-10-01", "🔄 统一蒸馏管道（终审落地+勘误）", "2026-11-01")])
        self.assertEqual(core.check_overdue(content, TYPES, TODAY), [])
        self.assertEqual(len(core.extract_expected(content, TYPES)), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
