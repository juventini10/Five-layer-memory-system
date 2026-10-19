#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_paths.py — 卡引擎·路径单一真源（端用户版·双部署位置兼容·存储双态自适应）
所有目录从记忆共享中心(MC)自推导。支持两种安装位置：
  旧路径：[MC]/脚本中心/知识联邦引擎/scripts/（向后兼容）
  新路径：[MC]/知识联邦引擎/scripts/（2026-10-03 独立部署·真源唯一）
存储目录双态自适应（存在∧非空判据）：先探作者态实位，回落装机态默认；
  空壳目录（存在但空）不判在位——原「知识库/概念卡」空壳骗过 isdir 致整源静默消失
  4 天的事故（2026-10-05/06）本判据机械化免疫。
用户自定义覆盖：[引擎目录]/config.json（如 {"diary_dir": "/path/to/日记"}）
⛔DO NOT 在任何脚本里硬编码家目录结构——一律 import 本模块
"""
import os, json, sys

_HERE = os.path.dirname(os.path.abspath(__file__))

def _find_mc_and_fed():
    """向上推导MC和引擎工作区(FED)。
    找到「知识联邦引擎」目录时：
      - 其父目录为「脚本中心」→ 旧路径：MC=脚本中心的上级，FED=脚本中心/知识联邦引擎
      - 其父目录非「脚本中心」→ 新路径：MC=知识联邦引擎的上级，FED=知识联邦引擎
    暂存态（安装包内 references/知识联邦引擎-min/）：无匹配 → (None, None)
    """
    d = _HERE
    for _ in range(6):
        d = os.path.dirname(d)
        base = os.path.basename(d)
        if base == "知识联邦引擎":
            parent = os.path.dirname(d)
            if os.path.basename(parent) == "脚本中心":
                # 旧路径：[MC]/脚本中心/知识联邦引擎/
                return os.path.dirname(parent), d
            else:
                # 新路径：[MC]/知识联邦引擎/（独立部署·2026-10-03）
                return parent, d
        if d == os.path.dirname(d):  # 到根
            break
    return None, None

MC, FED = _find_mc_and_fed()

def _mc_path(*parts):
    """安装态返回拼接路径；未安装态返回 None（调用方据此跳过写动作）"""
    if MC is None:
        return None
    return os.path.join(MC, *parts)

def _first_live(candidates, default):
    """首个「存在∧非空」候选；全不满足→default（可建库面）。
    空壳事故机械化免疫（2026-10-05 立场卡+概念卡两检索源静默消失 4 天）。"""
    for c in candidates:
        if c and os.path.isdir(c) and os.listdir(c):
            return c
    return default

KB = _mc_path("知识库")                                  # 用户知识库根（安装态假设·作者机卡库直挂MC下）
CONCEPTS_DIR = _first_live(
    [os.path.expanduser("~/Local_Obsidian_Vault/2-知识库/08-概念层"),  # 作者态实位（2026-10-08 轮次1实证修复）
     _mc_path("知识库", "概念卡")],                                    # 装机态默认（安装器建库面）
    _mc_path("知识库", "概念卡"))
AILIB_DIR = _first_live(
    [os.path.expanduser("~/Local_Obsidian_Vault/2-知识库/09-AI学习库"),  # 作者态实位（2026-10-12 C''波次2迁移·立场卡1095张迁入vault）
     _mc_path("AI学习库"),                                             # 旧作者态（向后兼容）
     _mc_path("知识库", "AI学习库")],                                  # 装机态默认
    _mc_path("知识库", "AI学习库"))
INDEX_FILE = _mc_path("知识库", "知识总索引.md")           # 编译产物·脚本生成
SYSLOG_DIR = _mc_path("工作日志", "系统日志")              # 系统日志落点
INSTALLED = MC is not None

_CONFIG_FILE = os.path.join(FED, "config.json") if FED else None

def _config():
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def ensure_dirs():
    """首次使用自动建库（幂等·仅安装态；暂存态跳过=不污染安装包）"""
    if not INSTALLED:
        return False
    for d in (CONCEPTS_DIR, AILIB_DIR, SYSLOG_DIR):
        os.makedirs(d, exist_ok=True)
    return True

def diary_dir():
    """日记目录：config.json 可覆盖；缺省 [MC]/ObsidianVault/1-每日计划/01-日记"""
    c = _config()
    if c.get("diary_dir"):
        return os.path.expanduser(c["diary_dir"])
    return _mc_path("ObsidianVault", "1-每日计划", "01-日记")
