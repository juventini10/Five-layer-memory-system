#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frozen_ssot_guard.py v0.1 — SSOT 冻结段守卫（通用版）

用途：拦截对已冻结口径段的编辑（防 SSOT 漂移·防"文档先行/口径被手改"幽灵事故）。
定位：通用工程防护，不绑定具体面板/设计。锚点定位（非行号），抗插入漂移。

机制（against HEAD）：
  对 FROZEN 清单里每条 (file, start_anchor, end_anchor)，
  截取 HEAD 版本与工作区版本中该锚区间的文本，逐字节对比。
  任一冻结段被改 → exit 1 + 打印该段 diff 前缀与修复提示。
用法：
  env -u PYTHONHOME -u PYTHONPATH python3 frozen_ssot_guard.py
出口：0=全部冻结段未动；1=有冻结段被改（供 pre-commit 拦截）。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import os
import subprocess
import sys
from datetime import date

# 记忆中心解析（2026-10-06 根治·LobsterAI 端实证）：
#   病灶=REPO 写成 os.path.join(expanduser("~"), expanduser("~")) ⇒ 家目录套家目录
#   ⇒ REPO=/Users/用户名（家目录）·拼接 记忆蓝图/... 必不存在
#   ⇒ 冻结段门卫**从建立起从未成功校验过**，且每次报「工作区文件不存在」
#   ——把「冻结段被改」判定完全架空（与 verify_skill_version_hook 同款：伪装成有效）。
#   正解=记忆根走 runtime_paths 声明（⛔ 不回落默认值·回落=静默失效·键哲学 §3.5）
#   兜底=脚本自身所在目录的上级（本件在 <MC>/开发工具/）⇒ 无声明也能定位。
def _resolve_mc():
    """记忆中心根：runtime_paths 声明优先·自推导兜底（⛔ 不回落 $HOME）。"""
    try:
        import importlib.util as _ilu
        _rp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime_paths.py")
        if os.path.isfile(_rp):
            _sp = _ilu.spec_from_file_location("_rtp_amb", _rp)
            _m = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_m)
            _v = _m.get("archive_root")
            if _v and os.path.isdir(_v):
                return _v
    except Exception:
        pass
    # 自推导：本件位于 <MC>/开发工具/frozen_ssot_guard.py ⇒ 上级即 MC
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MC = _resolve_mc()
REPO = MC

# 冻结段清单（SSOT 单一真相源·口径定案后冻结）：
#   file=相对仓库根路径；start/end=锚点子串（start 含，end 含，取 [start..end] 闭区间）
#   新增冻结段：①先定案口径 → ②在此登记锚点 → ③记录到变更日志。
# 2026-10-06 幽灵条目清退（三明治 L1·键 20261006_171708·你三问裁决）：
#   原条目锚点段（01规范 §二·七 分母口径规则 blockquote）经 HEAD 与工作区双查均无此形态
#   （"分母口径"命中全为 changelog 引用文字）——守卫自建立起从未匹配成功（L28 历史注记
#   与锚点病先后接力掩盖）。清退=守卫诚实待命态（空表 PASS+🟡显形）。
#   ⏳ 待注册候选（挂施工收口批次·施工期注册=假红骚扰）：
#     【考察结论 2026-10-06·你三问后实地考察·键20261006_171708】原两候选皆否决：
#     ① 06 §1.6 档位互斥律段→否决：活跃演进段（一修~四修·你每次质证追加一修至10-01）——
#        冻活跃段=堵死质证修订通道·每次追加必假红。守卫该冻"定案不再变"的段，非活跃条文。
#     ② 05 位置纪律段→否决：仅 changelog 叙述、无条文正文段可锚。
#     ③ K2 切片区（AGENTS.md 内嵌）→ 真该冻但不在仓内（~/.zcode/）·守卫 git 前提不满足；
#        且已有 slice_watch+position3 判据③ 双层覆盖。
#   ⇒ 当前仓内无合格冻结对象·空表即正确态；真冻结需求出现（你拍板"此段冻结"）再注册。
#   注册规范：start/end 用段首尾**实际措辞**（先 grep 实存再注册——本次教训：锚点串凭记忆
#   抄写=注册即失配·守卫恒红毒化 pre-commit 链逼全员绕闸）。
FROZEN = []


def _git_show_head(path):
    """取 HEAD 版本文件内容；失败返回 None（例如首次提交/未跟踪）。"""
    try:
        r = subprocess.run(
            ["git", "show", "HEAD:" + path],
            cwd=REPO, capture_output=True, text=True, check=True,
        )
        return r.stdout
    except subprocess.CalledProcessError:
        return None


def _slice(text, start, end):
    if text is None:
        return None
    i = text.find(start)
    if i < 0:
        return None
    j = text.find(end, i)
    if j < 0:
        return None
    return text[i:j + len(end)]


def main():
    failed = 0
    for item in FROZEN:
        rel = item["file"]
        head_text = _git_show_head(rel)
        wc_path = os.path.join(REPO, rel)
        if not os.path.exists(wc_path):
            # 2026-10-06 诚实化（position3 v1.9 哲学：假红淹没真红=狼来了）：守卫与对象脱钩
            # （锚点串经全仓 grep 仅存在于守卫自身=自建立起恒红·毒化 pre-commit 链逼绕闸）。
            # 脱钩=显形🟡不拦；真保护（下方"锚点定位成功且冻结段被改"）保留 rc1 拦截不变。
            print("🟡 [frozen-guard] 工作区文件不存在（守卫与对象脱钩·显形不拦·请修正锚点表或还原文件）: {}".format(rel))
            continue
        with open(wc_path, encoding="utf-8") as f:
            wc_text = f.read()
        head_seg = _slice(head_text, item["start"], item["end"])
        wc_seg = _slice(wc_text, item["start"], item["end"])
        if head_seg is None or wc_seg is None:
            print("🟡 [frozen-guard] 锚点未定位（无保护对象·显形不拦·请注册真实冻结段或修正锚点表）: {}".format(rel))
            continue
        if head_seg == wc_seg:
            print("✅ [frozen-guard] 冻结段未改动: {}".format(rel))
        else:
            failed = 1
            print("⛔ [frozen-guard] 冻结段被改动（{} - {}）: {}".format(
                item["start"], item.get("reason", ""), rel))
            print("    修复：git checkout -- {} 还原冻结段后重试，或用 git diff 确认非必要改动。".format(rel))
    print("[frozen_ssot_guard] {} · {}".format(
        "FAIL(拦截)" if failed else "PASS", date.today().isoformat()))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())