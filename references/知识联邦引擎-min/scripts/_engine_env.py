#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_engine_env.py — 引擎解释器选择（端用户降级版）
作者侧原版：强制 re-exec 进装了 sentence_transformers 的专用 venv。
端用户版：有 .venv 就用（语义增强装好后自动生效）；没有就系统 python 直跑——
概念抽取主流程是 AI 抽卡（LLM），无模型也能完整闭环（消重降级为文本相似）。
"""
import os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_VENV_REL = ("Scripts", "python.exe") if os.name == "nt" else ("bin", "python")  # 2026-10-19 Win反馈 min
_VENV_PY = os.path.join(_HERE, ".venv", *_VENV_REL)

def ensure_engine_python():
    if os.path.exists(_VENV_PY) and ".venv" not in sys.prefix:
        os.execv(_VENV_PY, [_VENV_PY] + sys.argv)
    # 无 venv 或已在 venv 内 → 当前解释器直跑（放行）
    return
