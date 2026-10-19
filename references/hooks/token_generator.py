#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用令牌生成器（token_generator.py）
=====================================
起源：system-logger Skill v3.13.0 的🔖流程完成令牌机制
2026-09-03 童灵评估后扩大化为通用脚本验证机制
设计哲学：《布洛陀脚本架构设计通用规范》§二·十「执行验证机制：令牌物理锚定」

本质：用物理锚定的证据（🔖令牌）代替AI的自觉声明，防止AI偷懒、说谎、伪造执行结果。
四要素：物理锚定 + 必须relay + 无法伪造 + 可追溯

用法：
  python3 token_generator.py --action <动作名> --detail <详情>
  python3 token_generator.py --action "文件写入" --detail "evolution_deviation.py 修改"
  python3 token_generator.py --verify <令牌>  # 验证令牌是否存在于执行日志

输出：
  🔖 令牌：{8位十六进制}
  （同时写入执行日志 token_log_YYYY-MM.jsonl）

边界声明：
  令牌验证"做了没做"，不验证"做得好不好"——与质量验证正交分工。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = os.path.expanduser("[记忆共享中心]/脚本中心")
LOG_DIR = os.path.join(BASE_DIR, "logs", "runtime")
TOKEN_LOG_PREFIX = "token_log_"


def ensure_log_dir():
    """确保执行日志目录存在"""
    os.makedirs(LOG_DIR, exist_ok=True)


def get_token_log_path():
    """获取当月执行日志路径"""
    now = datetime.now()
    filename = "%s%s.jsonl" % (TOKEN_LOG_PREFIX, now.strftime("%Y-%m"))
    return os.path.join(LOG_DIR, filename)


def generate_token(action, detail=""):
    """
    生成唯一令牌（物理锚定·AI无法伪造）
    
    令牌种子：日期 + 时间 + 动作名 + 随机数
    令牌哈希：sha256(种子)前8位十六进制
    
    与 system-logger append_log_entry.py 的令牌生成逻辑保持一致
    """
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")
    now_full = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 令牌种子：日期 + 时间 + 动作名 + 随机数（与system-logger一致）
    token_seed = "%s%s%s%s" % (today, now_hm, action, secrets.token_hex(8))
    token_hash = hashlib.sha256(token_seed.encode("utf-8")).hexdigest()[:8]
    
    # 写入执行日志（可追溯）
    ensure_log_dir()
    log_path = get_token_log_path()
    log_entry = {
        "token": token_hash,
        "timestamp": now_full,
        "action": action,
        "detail": detail,
        "tool": "token_generator",
        "version": "v1.0.0"
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return token_hash, log_path


def verify_token(token):
    """
    验证令牌是否存在于执行日志（可追溯·无法伪造）
    
    返回：(存在, 日志条目)
    """
    log_path = get_token_log_path()
    if not os.path.exists(log_path):
        return False, None
    
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("token") == token:
                    return True, entry
            except json.JSONDecodeError:
                continue
    
    return False, None


def list_tokens(limit=10):
    """列出最近的令牌记录"""
    log_path = get_token_log_path()
    if not os.path.exists(log_path):
        print("（暂无令牌记录）")
        return
    
    entries = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    # 按时间倒序，取最近N条
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    entries = entries[:limit]
    
    print("最近 %d 条令牌记录：" % len(entries))
    print("-" * 80)
    for entry in entries:
        print("🔖 %s | %s | %s | %s" % (
            entry.get("token", "???"),
            entry.get("timestamp", "???"),
            entry.get("action", "???"),
            entry.get("detail", "")[:40]
        ))


def main():
    parser = argparse.ArgumentParser(
        description="通用令牌生成器——物理锚定的执行验证机制（v1.0.0）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 token_generator.py --action "文件写入" --detail "evolution_deviation.py 修改"
  python3 token_generator.py --action "命令执行" --detail "python3 panel_snapshot.py"
  python3 token_generator.py --verify 7e0863a7
  python3 token_generator.py --list

设计哲学：《布洛陀脚本架构设计通用规范》§二·十「执行验证机制：令牌物理锚定」
边界声明：令牌验证"做了没做"，不验证"做得好不好"。
        """
    )
    
    parser.add_argument("--action", type=str, help="动作名（如：文件写入/命令执行/测试运行）")
    parser.add_argument("--detail", type=str, default="", help="动作详情（可选）")
    parser.add_argument("--verify", type=str, metavar="TOKEN", help="验证令牌是否存在于执行日志")
    parser.add_argument("--list", action="store_true", help="列出最近的令牌记录")
    parser.add_argument("--limit", type=int, default=10, help="--list 时显示的条数（默认10）")
    
    args = parser.parse_args()
    
    # --list 模式
    if args.list:
        list_tokens(args.limit)
        return 0
    
    # --verify 模式
    if args.verify:
        exists, entry = verify_token(args.verify)
        if exists:
            print("✅ 令牌有效：🔖 %s" % args.verify)
            print("   时间：%s" % entry.get("timestamp", "???"))
            print("   动作：%s" % entry.get("action", "???"))
            print("   详情：%s" % entry.get("detail", ""))
            return 0
        else:
            print("❌ 令牌无效或不存在：🔖 %s" % args.verify)
            print("   （该令牌未在执行日志中找到，可能是伪造或已过期）")
            return 1
    
    # 生成模式
    if not args.action:
        parser.print_help()
        print("\n❌ 错误：生成模式必须指定 --action")
        return 1
    
    token, log_path = generate_token(args.action, args.detail)
    
    print("🔖 令牌：%s" % token)
    print("   动作：%s" % args.action)
    if args.detail:
        print("   详情：%s" % args.detail)
    print("   日志：%s" % log_path)
    print("")
    print("（AI必须在回复中relay此令牌作为'已执行'的证据，缺一个=对应动作未执行）")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
