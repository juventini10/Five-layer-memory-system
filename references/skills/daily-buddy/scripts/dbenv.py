#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dbenv.py — daily-buddy 环境自愈模块（第一性原理根治·Hermes 沙箱劫持）

问题本质：
  Hermes 沙箱的 `python3` 被重定向到 /tmp/hb_fakebin（假 no-op 二进制），
  且 `HOME` 被指向 /tmp/hb_sb/home。这导致：
    ① 脚本内 Path.home()/expanduser("~") 解析到错误 HOME → 读不到日记/成就
    ② 脚本内 subprocess 再调 "python3" → 调到假二进制 → 空跑
  两次踩坑（08-19 空跑、08-20 成就模块错位）均源于此。

根治原则（符合愿景"机制自动运转·不依赖人记得"）：
  1. Authoritative Home：HOME 唯一真相源，默认 /Users/用户名（硬编码兜底真值，
     脚本加载即修正，不依赖调用方记得设环境变量）；发布/其他机器可用环境变量
     DB_HOME 覆盖（优先级：DB_HOME > 默认值）——沙箱防线不变（默认值仍防劫持）。
  2. Real Python：子进程一律用真实解释器（默认 /usr/local/bin/python3，可用
     DB_PYTHON 覆盖），绝不裸 "python3"。
  3. 调用层兜底：AI 仍应经 dbbin.sh 启动（双保险），但即便被直接调，
     脚本也能自愈路径 + 拒绝假 python 子进程。

exit 码统一规范（全 daily-buddy 脚本同律·2026-09-11 收口）：
  0 = 成功
  1 = 参数/用法错误
  2 = 内容/数据不完整（校验失败）
  3 = 依赖文件缺失
  4 = 依赖字段缺失
  9 = 环境自检失败（沙箱假 python）——本模块 self_check 返回 False 时，调用方
      必须 sys.exit(9)，与业务 exit 码（0-7）无歧义。

本模块只做一件事：把"环境"这件事从每个脚本里抽出来、做成确定性函数。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import sys
import subprocess
from pathlib import Path

# ─── 唯一真相源：真实 HOME（用户主目录恒定位·DB_HOME 可覆盖）───
AUTHORITATIVE_HOME = os.environ.get("DB_HOME", "").strip() or "~"

# ─── 真实 python3（Hermes 沙箱 python3 是 /tmp/hb_fakebin 的 no-op·DB_PYTHON 可覆盖）───
REAL_PYTHON = os.environ.get("DB_PYTHON", "").strip() or "/usr/local/bin/python3"

# ─── 沙箱污染特征（用于自检告警）───
_SANDBOX_HOME_MARKERS = ("/tmp/hb_sb", "/tmp/hb_fakebin", "/tmp/hb_")


def resolve_home() -> Path:
    """
    解析权威 HOME。
    - DB_HOME 环境变量显式设置（发布/其他机器适配）→ 直接采用
    - 否则：os.path.expanduser("~") 命中沙箱标记 → 返回 AUTHORITATIVE_HOME
    - 否则返回 expanduser 原值（兼容非沙箱环境）
    确定性、无副作用、不修改 os.environ（避免波及同进程其他逻辑）
    """
    explicit = os.environ.get("DB_HOME", "").strip()
    if explicit:
        return Path(explicit)
    raw = os.path.expanduser("~")
    for marker in _SANDBOX_HOME_MARKERS:
        if marker in raw:
            return Path(AUTHORITATIVE_HOME)
    return Path(raw)


# ─── 暴露路径常量（替代各脚本散落的 Path.home()/expanduser）───
HOME = resolve_home()
DIARY_DIR = HOME / "[日记仓库]/1-每日计划/01-日记"
ACHIEVEMENT_DIR = HOME / "[记忆共享中心]/成就系统"
SITUATION_SNAPSHOT = HOME / "[记忆共享中心]/情境层/动态状态快照.md"
FED_DIR = HOME / "[记忆共享中心]/脚本中心/知识联邦引擎"
GREATEST_DIR = HOME / "[记忆共享中心]/最伟大的我"
EVIDENCE_DIR = GREATEST_DIR / "成就证据"


def running_on_fake_python() -> bool:
    """检测当前解释器是否为沙箱假二进制。"""
    exe = sys.executable or ""
    return any(m in exe for m in _SANDBOX_HOME_MARKERS)


def real_python_cmd() -> str:
    """返回真实 python3 路径（内部子进程统一用此，杜绝假二进制空跑）。"""
    return REAL_PYTHON


def run_real(cmd_list, **kwargs):
    """
    用真实 python3 跑子进程（替代裸 subprocess.run([py, ...])）。
    cmd_list 形如 ["script.py", "--all"]，会自动在前面补 REAL_PYTHON。
    返回 subprocess.CompletedProcess。
    """
    if not cmd_list:
        return subprocess.run(cmd_list, **kwargs)
    head = cmd_list[0]
    # 若首个 token 已是 python 解释器（真实路径或裸 python3/python），保持
    if head == REAL_PYTHON or head in ("python3", "python"):
        pass
    else:
        # 首个 token 是脚本(.py)或任意可执行路径 → 前置真实 python3
        cmd_list = [REAL_PYTHON] + list(cmd_list)
    return subprocess.run(cmd_list, **kwargs)


def self_check(verbose: bool = True) -> bool:
    """
    脚本启动时自检：当前是否在假 python 上跑。
    返回 True=环境健康；False=在假 python 上跑（应终止）。
    """
    if running_on_fake_python():
        if verbose:
            sys.stderr.write(
                "🔴 环境自检失败：当前 python 解释器为沙箱假二进制"
                f"({sys.executable})，脚本无法正确运行。\n"
                f"   请经 dbbin.sh 启动，或显式用 {REAL_PYTHON} 运行本脚本。\n"
            )
        return False
    return True


if __name__ == "__main__":
    print(f"HOME(resolved) = {HOME}")
    print(f"DIARY_DIR      = {DIARY_DIR}")
    print(f"ACHIEVEMENT_DIR= {ACHIEVEMENT_DIR}")
    print(f"REAL_PYTHON    = {REAL_PYTHON}")
    print(f"fake_python?   = {running_on_fake_python()}")
