#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_record_fix.py — record_fix.py 考题基线（v1.1.0 C07 #55·pending_review 超期自动化）。

判据源=record_fix.check_pending_review_overdue docstring（#55"pending_review 积压 26 天无报警"——
载体 counter_pending_review.md 建了不接线=第二张纸锁→本函数读 fix_ledger.json 实算最旧 pending
条目积压天数+阈值报警：≥7 ⚠提示 / ≥14 🔴阻断 exit4 / <7 静默）。
⛔数据源唯一=fix_ledger.json（not 对话/报告正文）·载体只是计算结果落盘点（防双本账）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# v2.9.12同族根治（2026-09-27·clock-loop自评Loop R1）：v4.12.13的dont_write_bytecode只覆盖了
# test_skill_eval.py——本文件import record_fix同样写.pyc污染被评树（file_clutter candidate-found实锤）。
# flag须先于一切import设置（模块体内的设置拦不住被import模块自身那次写入）。
import sys as _sys_guard
_sys_guard.dont_write_bytecode = True
import os
import json
import tempfile
import unittest
from datetime import date, timedelta

from record_fix import check_pending_review_overdue, WARN_DAYS, BLOCK_DAYS


def _ledger(tmp, created_str=None, status="pending_review", fix_id="FIX-001"):
    """构造最小 fix_ledger.json。created_str=None 则跳过 fixes（空表）。"""
    d = {"revision": 1, "fixes": []}
    if created_str is not None:
        d["fixes"] = [{"id": fix_id, "status": status, "created": created_str}]
    p = os.path.join(tmp, "fix_ledger.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    return p


def _d_ago(days):
    return (date(2026, 9, 5) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M")


class TestOverdueCheck(unittest.TestCase):
    TODAY = date(2026, 9, 5)

    def _run(self, ledger_path, counter_path):
        return check_pending_review_overdue(
            ledger=ledger_path, counter_path=counter_path, today=self.TODAY)

    def test_missing_ledger_creates_counter(self):
        """正例①：ledger 缺失→视为 N=0 并创建载体（幂等·full-flow 第258行原则·不误报）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = os.path.join(tmp, "fix_ledger.json")  # 不存在
            counter = os.path.join(tmp, "counter_pending_review.md")
            days, oldest_id, n, msg = self._run(ledger, counter)
            self.assertEqual((days, oldest_id, n), (0, None, 0))
            self.assertTrue(os.path.isfile(counter))
            with open(counter, encoding="utf-8") as f:
                self.assertIn("pending_review_overdue_days: 0", f.read())

    def test_no_pending_silent(self):
        """正例②：无 pending_review 条目→0 静默（无积压·不打扰）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str=None)
            counter = os.path.join(tmp, "counter.md")
            days, oldest_id, n, msg = self._run(ledger, counter)
            self.assertEqual((days, oldest_id, n), (0, None, 0))
            self.assertIn("无积压", msg)

    def test_below_warn_silent(self):
        """正例③：积压 5 天 <7→未到闹钟阈值（数值正确·不误报）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str=_d_ago(5))
            counter = os.path.join(tmp, "counter.md")
            days, oldest_id, n, msg = self._run(ledger, counter)
            self.assertEqual(days, 5)
            self.assertEqual(oldest_id, "FIX-001")
            self.assertIn("未到闹钟阈值", msg)

    def test_warn_at_threshold(self):
        """负例①：积压 7 天 =WARN_DAYS→⚠️提示（交付声明须含欠账行）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str=_d_ago(WARN_DAYS))
            counter = os.path.join(tmp, "counter.md")
            days, _, n, msg = self._run(ledger, counter)
            self.assertEqual(days, WARN_DAYS)
            self.assertIn("欠账", msg)
            self.assertIn("交付声明须含欠账行", msg)

    def test_block_at_threshold(self):
        """负例②：积压 14 天 =BLOCK_DAYS→🔴阻断（exit4·先复核再交付）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str=_d_ago(BLOCK_DAYS))
            counter = os.path.join(tmp, "counter.md")
            days, _, n, msg = self._run(ledger, counter)
            self.assertEqual(days, BLOCK_DAYS)
            self.assertIn("阻断'✅交付完成'声明", msg)

    def test_carrier_updates_existing_key(self):
        """正例④：载体已存在且含 key 行→只更新数值（⛔不重写头·防误删人工记录）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str=_d_ago(9))
            counter = os.path.join(tmp, "counter.md")
            with open(counter, "w", encoding="utf-8") as f:
                f.write("# 持久化计数器：pending_review 超期闹钟\n\n"
                        "pending_review_overdue_days: 3\n# 人工备注行\n")
            self._run(ledger, counter)
            with open(counter, encoding="utf-8") as f:
                txt = f.read()
            self.assertIn("pending_review_overdue_days: 9", txt)
            self.assertNotIn("pending_review_overdue_days: 3", txt)
            self.assertIn("人工备注行", txt)  # 台账段未被重写

    def test_corrupt_ledger_fail_closed(self):
        """负例③：ledger 损坏→fail-closed（None·无法确认积压天数·须人工核查）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = os.path.join(tmp, "fix_ledger.json")
            with open(ledger, "w", encoding="utf-8") as f:
                f.write("{ 不是合法 json")
            counter = os.path.join(tmp, "counter.md")
            days, oldest_id, n, msg = self._run(ledger, counter)
            self.assertIsNone(days)
            self.assertIn("fail-closed", msg)

    def test_bad_created_format_fail_closed(self):
        """负例④：created 日期格式异常→fail-closed（⛔不静默当 0 天·须人工核查）"""
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(tmp, created_str="2026/09/01")
            counter = os.path.join(tmp, "counter.md")
            days, oldest_id, n, msg = self._run(ledger, counter)
            self.assertIsNone(days)
            self.assertIn("日期格式异常", msg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
