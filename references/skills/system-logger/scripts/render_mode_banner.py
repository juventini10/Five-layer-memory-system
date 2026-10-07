#!/usr/bin/env python3
"""打印 system-logger 触发横幅（段1）。

v3.12.0(2026-09-02·愿景①根治回复呈现层漂移): 横幅由脚本产出，AI 只许逐字 relay，
接触不到构造权（防误·设计消除错误）。与 append_log_entry.py 的验证块同构——
回复呈现层格式全部收归脚本，AI 无权自创。

用法:
  python3 render_mode_banner.py --mode 日写入
  python3 render_mode_banner.py --mode 月度蒸馏
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import sys

BANNERS = {
    "日写入": "📝 系统日志 · 日写入模式已启动",
    "月度蒸馏": "📝 系统日志 · 月度蒸馏模式已启动",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=list(BANNERS.keys()),
                    help="执行路径：日写入 / 月度蒸馏")
    args = ap.parse_args()
    print(BANNERS[args.mode])
    return 0


if __name__ == "__main__":
    sys.exit(main())
