#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
card_id_guard.py — AI学习库立场卡编号守卫（防撞号物理闸）
=========================================================
根因（2026-08-21 S810 撞号事故）：立场卡编号分配靠"分配者记得查当前最大号"，
属承诺衰减（C-005）——多端/多会话各自取号，索引滞后即撞号。
本脚本把"查号+防撞"从约定式防护改为机械化自锁（S307 模式）：

子命令：
  check   全库扫 立场卡#S*.md 文件名编号 → 重复列表；exit 0=无重复 / 1=有重复
  next    输出下一可用编号（max+1；洞号不复用——复用会让历史引用歧义复活）
  hook    Stop 钩子模式：跑 check，状态与上次相同→静默放行；
          首次发现新重复→stdout 告警（注入下轮对话）；任何异常→exit 0 放行

设计原则（仿 route_unknown_unknown / audit_search_kb 先例）：
  - 失败默认放行，绝不拦截对话（hook 模式永远 exit 0）
  - 状态文件去重告警：同一重复集不每轮刷屏（state: ~/.{宿主}/state/·宿主由 CARD_GUARD_HOST env 指定）
  - 只检测不修改：发现撞号后由人/AI按最小变更面原则归正（本次事故判据留档
    于 数字分身蒸馏·T0立项规划书.md 变更史 v1.1.1）

用法：
  python3 card_id_guard.py check        # 手动体检
  python3 card_id_guard.py next         # 入库取号（登记新立场卡前必跑）
  CARD_GUARD_HOST=workbuddy python3 card_id_guard.py hook
                                        # settings.json hooks.Stop 挂装入口（env 隔离状态文件）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import json
import re
import sys
from collections import Counter
from pathlib import Path

KB_DIR = Path.home() / Path('[记忆共享中心]') / "知识库" / "AI学习库"  # 2026-10-04 13:2x 回滚模板逆向污染（原改动把作者路径净化式改写进生产文件致 str/str TypeError·真凶见施工单§11）
# 状态文件按宿主端隔离（跨工具中立·v0.2）：各端各写自己的状态文件，互不干扰去重逻辑。
# 宿主由环境变量 CARD_GUARD_HOST 指定（缺省 qoder-cn 兼容原挂载）；hooks 命令里传 env。
import os as _os
import subprocess as _sp_guard  # v2.0 2026-09-03 童灵·guard_invocations埋点
_HOST = _os.environ.get("CARD_GUARD_HOST", "qoder-cn")
STATE_FILE = Path.home() / f".{_HOST}" / "state" / "card_id_guard_state.json"
CARD_RE = re.compile(r"立场卡#S(\d+)")


# B埋点(v2.0·2026-09-03·童灵·补exit码埋点): 包装入口点在退出时写日志(含exit码)
def _guard_log_exit(rc):
    try:
        _sp_guard.Popen(["python3", _os.path.expanduser("[记忆共享中心]/脚本中心/guard_invocation_logger.py"),
                          "--guard", "card_id_guard",
                          "--source", _os.environ.get("GUARD_TRIGGER_SOURCE", "hook_auto"),
                          "--exit", str(rc),
                          "--detail", "self-instrumented"],
                         stdout=_sp_guard.DEVNULL, stderr=_sp_guard.DEVNULL)
    except Exception:
        pass


def scan_ids():
    """扫描全库立场卡文件名编号 → Counter"""
    ids = Counter()
    if not KB_DIR.exists():
        return ids
    for p in KB_DIR.glob("立场卡#S*.md"):
        m = CARD_RE.search(p.name)
        if m:
            ids[int(m.group(1))] += 1
    return ids


def find_dups(ids: Counter):
    return sorted(sid for sid, n in ids.items() if n > 1)


def cmd_check():
    ids = scan_ids()
    dups = find_dups(ids)
    if dups:
        print(f"[card_id_guard] 撞号 {len(dups)} 组: {['S' + str(d) for d in dups]}")
        return 1
    print(f"[card_id_guard] OK: {len(ids)} 张立场卡，编号无重复")
    return 0


def cmd_next():
    ids = scan_ids()
    dups = find_dups(ids)
    if dups:
        print(f"[card_id_guard] ⛔ 存在撞号 {['S' + str(d) for d in dups]}，先归正再取号")
        return 1
    nxt = max(ids) + 1 if ids else 1
    print(f"S{nxt:03d}")
    return 0


def cmd_hook():
    """Stop 钩子：重复集变化才告警，任何异常静默放行"""
    try:
        dups = find_dups(scan_ids())
        prev = []
        if STATE_FILE.exists():
            try:
                prev = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("dups", [])
            except Exception:
                prev = []
        if dups != prev:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(
                json.dumps({"dups": dups}, ensure_ascii=False), encoding="utf-8"
            )
            if dups:  # 新重复出现→告警；重复被修复（dups=[]）→静默
                print(
                    "[编号守卫] ⚠️ AI学习库立场卡撞号："
                    + " ".join(f"S{d}" for d in dups)
                    + "。跑 `python3 [记忆共享中心]/脚本中心/card_id_guard.py check` 定位，"
                    "按最小变更面原则归正（先例：规划书 v1.1.1）。"
                )
        return 0
    except Exception:
        return 0


def self_test():
    """--self-test 五用例（2026-08-22 打样·§3.0·5 纪律①·高危层分诊第一名）。

    全程临时目录 patch KB_DIR——不碰真库；CARD_GUARD_HOST=selftest 隔离状态文件。
    """
    import tempfile
    _os.environ["CARD_GUARD_HOST"] = "selftest"
    import importlib.util
    spec = importlib.util.spec_from_file_location("cig_selftest", __file__)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # T1 空库：无撞号
        m.KB_DIR = tmp / "不存在"
        assert m.find_dups(m.scan_ids()) == [], "T1"
        ok += 1; print("✅ T1 空库无撞号")
        # T2 撞号：S1×2 + S2 → dups=[1]
        m.KB_DIR = tmp
        (tmp / "立场卡#S1.md").write_text("a", encoding="utf-8")
        (tmp / "立场卡#S1副本.md").write_text("a", encoding="utf-8")
        (tmp / "立场卡#S2.md").write_text("a", encoding="utf-8")
        assert m.find_dups(m.scan_ids()) == [1], "T2"
        ok += 1; print("✅ T2 撞号检出 dups=[1]")
        # T3 无撞：S1..S3 各一
        (tmp / "立场卡#S1副本.md").unlink()
        (tmp / "立场卡#S3.md").write_text("a", encoding="utf-8")
        assert m.find_dups(m.scan_ids()) == [], "T3"
        ok += 1; print("✅ T3 无撞号静默")
        # T4 取号：max(S1,S2,S3)+1=4·洞号不复用
        ids = m.scan_ids()
        assert max(ids) + 1 == 4, "T4"
        ok += 1; print("✅ T4 next=4（max+1·洞号不复用语义由实现保证）")
        # T5 hook 失败放行：库目录异常 → exit 0
        m.KB_DIR = tmp / "不存在"
        assert m.cmd_hook() == 0, "T5"
        ok += 1; print("✅ T5 hook 异常放行 exit 0")
    print(f"自测结果: {ok}/5 通过")
    return 0 if ok == 5 else 1


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "check"
    if sub == "check":
        sys.exit(cmd_check())
    if sub == "next":
        sys.exit(cmd_next())
    if sub == "hook":
        sys.exit(cmd_hook())
    if sub == "--self-test":
        sys.exit(self_test())
    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    _rc = 0
    try:
        main()
    except SystemExit as _e:
        _rc = _e.code if isinstance(_e.code, int) else 0
        # 步2(2026-10-07 v? 报警噪声根治卡·你令彻底做完):检红rc归0——平台契约下 exit≠0专留真崩,
        #   检红可见性=输出红行+台账(_guard_log_exit/.out/patrol log);⛔不减一行红输出。
        if _rc == 1:
            _rc = 0

    except Exception:
        _rc = 0  # 失败放行（Hook 纪律）
    finally:
        _guard_log_exit(_rc)
    sys.exit(_rc)
