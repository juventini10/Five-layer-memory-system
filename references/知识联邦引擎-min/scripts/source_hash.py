#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
source_hash.py — 三库联邦·源解析与内容哈希（唯一真相住所）
设计依据: 知识库体检设计 §五决策位（哈希谓词设计）
守卫编写规范原则1: 源解析与hash算法只住本模块——extract_concepts(写入方)与knowledge_lint(校验方)均import，⛔DO NOT各自内联副本
三型hash（2026-07-28探测11条源实测定型）:
  diary   → 今日感悟段内容hash（段落regex与extract_diary_insight同源）
  syslog带小节 → ###小节段内容hash；小节失联→返回None(调用方退mtime·有痕)
  ailib   → 整文hash
  syslog无小节 → 返回None（追加型文件整文hash与mtime同病·退mtime并建议补小节名）
"""
import os, re, hashlib

from _paths import diary_dir as _diary_dir, SYSLOG_DIR, AILIB_DIR

def DIARY_DIR():
    return _diary_dir()


def resolve_source(src):
    """source_cards条目 → (源文件路径|None, 类型)。解析规则来自真卡实测格式(2026-07-27)。
    未识别格式返回(None,'unknown')——调用方报warning不算孤儿(防误杀)。"""
    if m := re.match(r'^日记感悟\s+(\d{4}-\d{2}-\d{2})', src):
        d = m.group(1)
        return os.path.join(DIARY_DIR(), d[:7], f"{d}.md"), "diary"
    if m := re.match(r'^系统日志\s+(\d{4}-\d{2}-\d{2})', src):
        return os.path.join(SYSLOG_DIR, f"系统日志_{m.group(1)}.md"), "syslog"
    if src.startswith("AI学习库/"):
        rel = src.split("/", 1)[1]
        p = os.path.join(AILIB_DIR, rel)
        return (p if os.path.exists(p) else p + ".md"), "ailib"
    return None, "unknown"


def _diary_insight(text):
    """日记'今日感悟'段（与extract_concepts.extract_diary_insight同一regex·若改须两处同步——TODO后续让extract也import本函数消除双份）"""
    m = re.search(r"##[^\n]*今日感悟[^\n]*\n(.*?)(?=\n## |\Z)", text, re.S)
    return m.group(1).strip() if m else None


def _section_text(text, sec_name):
    """###小节定位：标题行含sec_name子串 → 取到下一个##/###标题前。失联返回None。"""
    m = re.search(r'^(#{2,4})[^\n]*' + re.escape(sec_name) + r'[^\n]*$', text, re.M)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r'^#{2,4}\s', text[start:], re.M)
    return text[start:start + nxt.start()] if nxt else text[start:]


def source_content_hash(src):
    """源条目 → (hash|None, 原因)。None=hash不可算，调用方退mtime（有痕降级）。
    hash=sha256前16位，原文不归一化——格式性修改仍触发为已知噪音。"""
    path, typ = resolve_source(src)
    if typ == "unknown" or not path or not os.path.exists(path):
        return None, f"{typ}:源不可解析或缺失"
    text = open(path, encoding="utf-8").read()
    if typ == "diary":
        seg = _diary_insight(text)
        if seg is None:
            return None, "diary:感悟段缺失"
        return hashlib.sha256(seg.encode()).hexdigest()[:16], "diary段"
    if typ == "ailib":
        return hashlib.sha256(text.encode()).hexdigest()[:16], "ailib整文"
    # syslog
    sec = src.split("/", 1)[1].strip() if "/" in src else None
    if not sec:
        return None, "syslog:无小节名(建议source用'系统日志 YYYY-MM-DD/小节名'格式)"
    seg = _section_text(text, sec)
    if seg is None:
        return None, f"syslog:小节'{sec}'失联(标题可能已改名)"
    return hashlib.sha256(seg.encode()).hexdigest()[:16], "syslog小节"
