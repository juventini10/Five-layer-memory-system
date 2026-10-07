#!/usr/bin/env python3
# drift_check_remind.py v1.0 — 童灵人格漂移体检·月度到期提醒器
# 创建: 2026-09-20 (WorkBuddy·皮叔拍板例行化)
#
# 职责（单一·机械触发层）: 判定距上次人格漂移体检是否 ≥30 天，到期则写提醒日志。
#   ⛔ 本脚本不做体检本身——盲评是 LLM 语义工作，触发归脚本、语义执行归会话代理
#   （分工红线：填值权归脚本，语义提取归 LLM·同蒸馏监视器先例）。
#
# 判定数据源（单一真源）: scripts/drift_check_state.json 的 last_check 字段
#   - 体检完成后由执行代理更新（约定见 数字分身/README.md 接续入口）
#   - state 缺失 = 视为超期，提醒中注明"未初始化"
#
# 输出: scripts/drift_check_remind.log
#   - 到期: 非空提醒行（会话代理读到非空即执行体检）
#   - 未到期: 空文件（静默）
# 退出码: 恒 0（提醒器不阻塞系统，到期与否看日志）

# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

def _scripts_dir() -> Path:
    env = os.environ.get("DIGITALTWIN_HOME")  # 自定义数字分身中心（安装包用户可配置）
    base = Path(env).expanduser() if env else Path.home() / "~/个人AI档案" / "数字分身"
    return base / "scripts"


SCRIPTS = _scripts_dir()
STATE_FILE = SCRIPTS / "drift_check_state.json"
REMIND_LOG = SCRIPTS / "drift_check_remind.log"
INTERVAL_DAYS = 30


def read_last_check() -> tuple[str | None, str | None]:
    """返回 (last_check_iso, note)。state 缺失/损坏返回 (None, 原因)。"""
    if not STATE_FILE.exists():
        return None, "state 未初始化"
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        last = data.get("last_check")
        date.fromisoformat(last)  # 校验格式
        return last, data.get("note")
    except Exception as e:  # noqa: BLE001
        return None, f"state 损坏: {e}"


def main() -> int:
    today = date.today()
    last, note = read_last_check()

    lines: list[str] = []
    if last is None:
        lines.append(
            f"⚠️ 漂移体检提醒（{today.isoformat()}）: {note}。"
            "请执行首次/修复初始化: 按 steps/step2-eval-protocol.md 跑盲评，"
            "完成后写 scripts/drift_check_state.json {last_check: YYYY-MM-DD, note: ...}"
        )
        overdue = True
    else:
        days = (today - date.fromisoformat(last)).days
        overdue = days >= INTERVAL_DAYS
        if overdue:
            lines.append(
                f"🔔 漂移体检到期（{today.isoformat()}）: 上次体检 {last}，已 {days} 天（阈值 {INTERVAL_DAYS}）。"
                "执行: 复用 steps/step2.8-blind-items.md 同套盲题 → 童灵盲判落盘 → 独立隔离上下文判分"
                "（先例 steps/step2.9-drift-{judgments,report}.md）→ 更新 drift_check_state.json"
            )

    if overdue:
        REMIND_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[drift-check-remind] 到期提醒已写入: {REMIND_LOG.name}")
    else:
        REMIND_LOG.write_text("", encoding="utf-8")  # 静默
        days = (today - date.fromisoformat(last)).days if last else -1
        print(f"[drift-check-remind] 未到期（上次 {last}·{days} 天前），日志已清空")

    return 0


if __name__ == "__main__":
    sys.exit(main())
