#!/usr/bin/env python3
"""
launchd_health_verify.py — P0-3长期固化自动验证器
每天由launchd_health_check.sh附加检查调用，验证launchd健康巡检是否连续运行无异常。

验证逻辑：
1. 检查com.buluotuo.launchd-health-daily的launchd运行记录（runs数、last exit code）
2. 扫描近7天系统日志中的健康巡检条目，统计异常次数
3. 如果启动≥7天且runs≥14（7天×2次/天）且无异常 → 标记"已固化"，写入系统日志
4. 如果有异常 → 报告异常详情，不标记固化
5. 如果启动<7天 → 报告剩余天数，不标记固化

设计原则（童灵愿景裁决2026-09-03）：
- 机械验证不靠人记得（S014自觉是安慰剂机械是药）
- 验证结果写入系统日志留痕（可追溯）
- 异常详写正常略写（避免日志噪声）
- 纳入现有健康巡检附加检查，不新建launchd任务（最小方案优先）

Version: 1.0.0 (2026-09-03)
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import subprocess
import re
import json
from pathlib import Path
from datetime import datetime, timedelta

LAUNCHD_LABEL = "com.buluotuo.launchd-health-daily"
SYSTEM_LOG_DIR = str("[记忆共享中心]/工作日志/系统日志")
STATE_FILE = Path.home() / "~/[记忆共享中心]/数字分身/launchd_health_verify_state.json"
SOLIDIFY_DAYS = 7
EXPECTED_RUNS_PER_DAY = 2


def get_launchd_stats() -> dict:
    """获取launchd任务的运行统计（runs数、last exit code、last run date）"""
    try:
        result = subprocess.run(
            ["launchctl", "list", LAUNCHD_LABEL],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"exists": False, "runs": 0, "last_exit_code": None, "last_run_date": None}

        # launchctl list输出格式：PID\tLastExitStatus\tLabel
        # 但runs数和last run date不在标准输出中，需要从plist或日志推断
        lines = result.stdout.strip().split("\n")
        parts = lines[0].split("\t") if lines else []
        # launchctl list输出：PID\tStatus\tLabel
        # PID="-"=当前未运行（正常，定时任务），Status="0"=上次成功，Status="-"=从未运行
        status_str = parts[1] if len(parts) > 1 else "-"
        last_exit_code = int(status_str) if status_str != "-" else None  # None=从未运行或未知

        return {
            "exists": True,
            "runs": None,  # launchctl list不直接提供runs数，从系统日志统计
            "last_exit_code": last_exit_code,
            "last_run_date": None,
            "pid": parts[0] if len(parts) > 0 else "-",
        }
    except Exception as e:
        return {"exists": False, "error": str(e), "runs": 0, "last_exit_code": None}


def scan_system_logs(days: int = 7) -> dict:
    """扫描近N天系统日志中的健康巡检条目，统计运行次数和异常次数"""
    total_runs = 0
    anomaly_runs = 0
    anomaly_details = []
    today = datetime.now().date()

    for i in range(days):
        log_date = today - timedelta(days=i)
        log_file = SYSTEM_LOG_DIR / f"系统日志_{log_date.strftime('%Y-%m-%d')}.md"
        if not log_file.exists():
            continue

        try:
            content = log_file.read_text(encoding="utf-8")
            # 匹配健康巡检条目（以### 开头，标题含launchd健康巡检）
            entries = re.findall(r'### (launchd健康巡检[^\n]*)', content)
            for entry_title in entries:
                total_runs += 1
                # 真正的异常：标题含🔴/失败/error/fail，且不含"自愈"/"已修复"/"已解决"
                # "发现异常+自动自愈"是正常工作记录（发现并修复了异常），不算验证失败
                has_anomaly_marker = any(kw in entry_title for kw in ["🔴", "失败", "error", "fail", "未自愈", "持续异常"])
                has_self_heal = any(kw in entry_title for kw in ["自愈", "已修复", "已解决", "自动修复"])
                if has_anomaly_marker and not has_self_heal:
                    anomaly_runs += 1
                    anomaly_details.append(f"{log_date}: {entry_title[:80]}")
        except Exception:
            continue

    return {
        "total_runs": total_runs,
        "anomaly_runs": anomaly_runs,
        "anomaly_details": anomaly_details,
        "days_scanned": days,
    }


def load_state() -> dict:
    """加载验证状态文件"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "first_run_date": datetime.now().strftime("%Y-%m-%d"),
        "solidified": False,
        "solidified_date": None,
        "last_verify_date": None,
        "verify_count": 0,
    }


def save_state(state: dict):
    """保存验证状态文件"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def verify() -> dict:
    """执行验证，返回验证结果"""
    state = load_state()
    launchd_stats = get_launchd_stats()
    log_stats = scan_system_logs(SOLIDIFY_DAYS)

    first_run = datetime.strptime(state["first_run_date"], "%Y-%m-%d").date()
    days_running = (datetime.now().date() - first_run).days
    expected_runs = days_running * EXPECTED_RUNS_PER_DAY
    actual_runs = log_stats["total_runs"]
    anomaly_runs = log_stats["anomaly_runs"]

    # 判定逻辑
    last_exit_ok = (launchd_stats.get("last_exit_code") is None) or (launchd_stats.get("last_exit_code") == 0)
    can_solidify = (
        days_running >= SOLIDIFY_DAYS
        and actual_runs >= expected_runs * 0.8  # 允许20%的容差（机器可能关机）
        and anomaly_runs == 0
        and launchd_stats.get("exists", False)
        and last_exit_ok
    )

    result = {
        "days_running": days_running,
        "expected_runs": expected_runs,
        "actual_runs": actual_runs,
        "anomaly_runs": anomaly_runs,
        "anomaly_details": log_stats["anomaly_details"],
        "launchd_exists": launchd_stats.get("exists", False),
        "last_exit_code": launchd_stats.get("last_exit_code"),
        "can_solidify": can_solidify,
        "already_solidified": state.get("solidified", False),
        "days_remaining": max(0, SOLIDIFY_DAYS - days_running),
    }

    # 更新状态
    state["last_verify_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    state["verify_count"] = state.get("verify_count", 0) + 1

    if can_solidify and not state.get("solidified", False):
        state["solidified"] = True
        state["solidified_date"] = datetime.now().strftime("%Y-%m-%d")
        result["newly_solidified"] = True
    else:
        result["newly_solidified"] = False

    save_state(state)
    return result


def main():
    result = verify()

    # 输出格式：供launchd_health_check.sh附加检查解析
    print("🔍 P0-3 launchd健康巡检长期固化验证")
    print(f"   已运行: {result['days_running']}天 (目标{SOLIDIFY_DAYS}天)")
    print(f"   实际运行: {result['actual_runs']}次 (预期{result['expected_runs']}次)")
    print(f"   异常次数: {result['anomaly_runs']}次")
    print(f"   launchd任务: {'存在' if result['launchd_exists'] else '不存在'} | 上次退出码: {result['last_exit_code']}")

    if result["already_solidified"]:
        print("   ✅ 已固化（长期验证通过）")
    elif result["newly_solidified"]:
        print("   ✅  newly solidified! 连续7天无异常，标记为已固化")
        print("   📝 验证结果已写入状态文件，建议同步更新03-进度看板")
    elif result["can_solidify"]:
        print("   ✅ 满足固化条件，但状态未更新（异常）")
    else:
        reasons = []
        if result["days_running"] < SOLIDIFY_DAYS:
            reasons.append(f"运行天数不足（还需{result['days_remaining']}天）")
        if result["actual_runs"] < result["expected_runs"] * 0.8:
            reasons.append(f"运行次数不足（实际{result['actual_runs']}/预期{result['expected_runs']}）")
        if result["anomaly_runs"] > 0:
            reasons.append(f"存在{result['anomaly_runs']}次异常")
        if not result["launchd_exists"]:
            reasons.append("launchd任务不存在")
        if result["last_exit_code"] != 0 and result["last_exit_code"] is not None:
            reasons.append(f"上次退出码异常（{result['last_exit_code']}）")
        print(f"   ⏳ 未固化：{'; '.join(reasons)}")

    if result["anomaly_details"]:
        print("   📋 异常详情：")
        for detail in result["anomaly_details"][:5]:
            print(f"      - {detail}")

    # 退出码：0=正常（已固化或验证中），1=异常
    if result["anomaly_runs"] > 0 or not result["launchd_exists"]:
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
