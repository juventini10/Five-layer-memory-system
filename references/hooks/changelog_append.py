#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/changelog_append.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""changelog_append.py v1.0.1 — 变更日志唯一合法写入口（append-only 账本协议）

根因（2026-08-23 DSH 三明智 L2 判定）：变更日志.md 曾被 444 幽灵权限锁定——
守卫家族全量 grep 无任何 chmod 机制 = 无主锁状态（ctime 已被现场解锁覆盖·归因永久不可考，
这恰好证明：无所有者的锁 = 不可调试的状态）。危害链条：合法追加被拒 → 各端 AI 各自解锁
（姿势漂移）或干脆不记（学习闭环断血）。

第一性原理：要保护的是【历史不可篡改】，不是【文件不可触碰】。

三层防线分工（各管一种坏事·互不越权）：
  git              → 管【改历史】（diff/log 永久可查·事后审计兜底）
  changelog_guard  → 管【漏记录】（--check 内容层检测·既有机制不动）
  本脚本           → 管【写入语义】（账本常态 444 · 校验→按需解锁→追加→try/finally 回锁）

用法：
  python3 changelog_append.py --tool "DeepSeek Harness" --file "开发工具/xxx.py" \
      --version "vA→vB" --desc "一句话说明"
退出码：0 成功 | 2 输入校验拒绝（未触碰账本） | 3 IO/回锁失败（大声报错+手动恢复指引）
设计约束：纯 stdlib 零依赖（铁律-014 写入工具安全·append-only；坏不得堵死最后的人工通道）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import datetime
import os
import stat
import sys

# v1.0.1 根治（2026-10-07）：默认值曾硬编 ~/变更日志.md——该路径不存在，任何 cwd 裸调均 exit=3。
# 现改为「脚本自身位置派生 → 家目录锚兜底」：真源面（脚本中心/开发工具）派生命中，装机面兜底命中。
_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# 2026-10-20（Q4/#5·Win 反馈）：候选面曾只有「脚本旁」+「~/个人AI档案」两处——
#   非默认记忆中心（用户自命名/异盘/中文用户名）两处全落空 ⇒ exit=3 写不进。
#   修法=沿脚本位置上溯最多 4 级 + 显式 MC 环境变量 + 家目录默认，按序取第一个存在件；
#   仍然全空时沿用"脚本旁"（保持旧报错语义可诊断），⛔不静默新建账本。
def _walk_up_dirs(start, levels=4):
    cur = start
    out = []
    for _ in range(levels):
        cur = os.path.dirname(cur)
        if not cur or cur == os.path.dirname(cur):
            break
        out.append(cur)
    return out
_CANDIDATES = [os.path.normpath(os.path.join(_SCRIPT_DIR, os.pardir, "变更日志.md"))]
# 显式 MC 环境变量优先于目录上溯（2026-10-20 审查吸收：上溯可能先命中父目录里别人的账本）
_mc_env = os.environ.get("MEMORY_CENTER") or os.environ.get("MC_PATH")
if _mc_env:
    _CANDIDATES.append(os.path.join(os.path.expanduser(_mc_env), "变更日志.md"))
for _d in _walk_up_dirs(_SCRIPT_DIR, 4):
    _CANDIDATES.append(os.path.join(_d, "变更日志.md"))
_CANDIDATES.append(os.path.expanduser("[记忆共享中心]/变更日志.md"))
# 候选全空=不猜落点（write 段对不存在目标会 fail(3) 大声报错）
DEFAULT_TARGET = next((p for p in _CANDIDATES if os.path.exists(p)), "")
LOCK_MODE = 0o444
UNLOCK_MODE = 0o644


def fail(code, msg):
    print("[changelog_append]{}".format(msg), file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description="变更日志唯一合法写入口（append-only 协议）")
    ap.add_argument("--tool", required=True, help="执行端工具名（规范名·如 DeepSeek Harness）")
    ap.add_argument("--file", required=True, help="本次变更涉及的主文件/范围（表内第3列）")
    ap.add_argument("--version", default="—", help="版本变化（表内第4列·无则填 —）")
    ap.add_argument("--desc", required=False, help="一句话说明（表内第5列）")
    ap.add_argument("--desc-file", default=None,
                  help="从文件读取说明（含 emoji／长文本优先用它·绕开 argv 传输层丢字符）")
    ap.add_argument("--target", default=DEFAULT_TARGET, help="账本路径（默认中央变更日志·可用于隔离压测）")
    a = ap.parse_args()

    # ① 输入校验（不合格 exit 2·此时账本一个字节都没动）
    today = datetime.date.today().isoformat()
    if bool(a.desc) == bool(a.desc_file):
        fail(2, "[拒写] --desc 与 --desc-file 必须二选一")
    _raw_desc = a.desc
    if a.desc_file:
        _p = os.path.expanduser(a.desc_file)
        if not os.path.exists(_p):
            fail(2, "[拒写] --desc-file 不存在: {}".format(_p))
        with open(_p, encoding="utf-8") as _f:
            _raw_desc = _f.read()
    tool, file_, desc = a.tool.strip(), a.file.strip(), " ".join(str(_raw_desc).split())
    version = (a.version or "—").strip() or "—"
    # v1.5.4 U+FFFD 写前闸（2026-10-12 成长箱 Loop 亲造实证）：命令行 argv 经传输层会把 astral emoji
    # 打成两个 U+FFFD 落进账本＝静默 mojibake；同一病已让 反哺日志 R-20261012-03 的 📅 隐身、
    # 整条条目躲过全部闸门校验（schema_check v2.2.2 首跑才逮住）。拒写不照收——坏字节进不了 444 账本；
    # 正路是长文本走 --desc-file（读文件不走 argv）。
    for _nm, _v in (("tool", tool), ("file", file_), ("version", version), ("desc", desc)):
        if "\ufffd" in _v:
            fail(2, "[拒写] {} 字段含 U+FFFD 替换符（传输层 mojibake）——含 emoji 的说明请改走 "
                    "--desc-file <路径>，或去掉 emoji 重跑".format(_nm))

    if not tool or not file_ or not desc:
        fail(2, "[拒写] --tool/--file/--desc 均不能为空")
    row = "| {} | {} | {} | {} | {} |".format(today, tool, file_, version, desc)
    if not row.startswith("| {} | ".format(today)) or not row.endswith(" |"):
        fail(2, "[拒写] 行格式异常：{}".format(row))

    # ② 受控追加（按需解锁 → O_APPEND → finally 回锁）
    target = a.target
    if not os.path.exists(target):
        fail(3, "[拒写] 账本不存在: {}".format(target))
    try:
        cur = stat.S_IMODE(os.stat(target).st_mode)
        if cur & 0o222 == 0:            # 只读态才解锁（已是可写则不动）
            os.chmod(target, UNLOCK_MODE)
        needs_nl = False
        try:
            with open(target, "rb") as fb:
                fb.seek(-1, os.SEEK_END)
                needs_nl = fb.read(1) != b"\n"
        except OSError:
            pass                        # 空文件
        with open(target, "a", encoding="utf-8") as f:
            f.write(("\n" if needs_nl else "") + row + "\n")
    except Exception as e:
        fail(3, "[错误] 追加失败: {}\n手动恢复指引: chmod 644 '{}' 后人工补行:\n{}".format(e, target, row))

    # ③ 回锁断言（裸奔 = 最严重的失败模式·必须大声喊出来）
    try:
        if stat.S_IMODE(os.stat(target).st_mode) != LOCK_MODE:
            os.chmod(target, LOCK_MODE)
    except Exception as e:
        fail(3, "[严重] 回锁失败: {} —— 账本正在裸奔！立即执行: chmod 444 '{}'".format(e, target))
    end_mode = stat.S_IMODE(os.stat(target).st_mode)
    print("APPENDED {} bytes -> {}".format(len(row.encode("utf-8")), target))
    print("TIME {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("ROW {}".format(row))
    if end_mode != LOCK_MODE:
        fail(3, "[严重] 结束模式 {:o} != 444 —— 账本未回锁！".format(end_mode))
    print("LOCK 444 ok")


if __name__ == "__main__":
    main()
