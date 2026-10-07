#!/usr/bin/env python3
"""
unified_distill_apply.py — 统一蒸馏管道L3自动回写辅助脚本
写入蒸馏日志（唯一真源）+ 绑实录源行 + 幂等去重。

设计原则（P0-4·2026-09-03童灵愿景裁决）：
- 复用不新建（01-蒸馏设计通用规范§4.1）
- 方向隔离（防二阶折射，宪法愿景§二）
- 绑实录源行（可追溯，S074断言绑实录）
- 幂等（重复运行结果一致）
- 只更新标记区域，不影响其他内容

v1.1.0 (2026-10-01) 变更——切片回写废止（统一蒸馏管道2026-09轮发现的结构性缺陷·皮叔授权按愿景最优解处置）：
- 病灶：本脚本原把蒸馏记录追加进 slices/L2·L3·L6.md，而 k2_slice_generator.py 以
  open(path, "w") 整文件重写切片（L107）。切片是规格书的派生产物，派生物不承载账本——
  写进切片的记录会在下一次生成时被抹除。
- 实证：8月三条回写记录已消失；本轮 10:05 写入切片的 9 条 DISTILLATION-RECENT 区在
  10:30 watcher 重跑生成器后 grep=0（当场重现），而 distillation_log.md 记录完好。
- 解态：distillation_log.md = 唯一真源（不受生成器管辖·git 跟踪·含来源类型列）；
  --target 参数保留，语义由"写入目标文件"改为"记录归属层标签"（供方向隔离校验与检索）。

Version: 1.1.0 (2026-10-01)
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import hashlib
from pathlib import Path

BASE = str("[记忆共享中心]")
# 唯一真源：蒸馏日志（git 跟踪·不受 k2_slice_generator 覆盖管辖）
DISTILL_LOG = BASE / "数字分身/distillation_log.md"


def generate_record_id(source: str, date: str, summary: str) -> str:
    """生成幂等记录ID（source+date+summary的hash前8位）"""
    raw = f"{source}|{date}|{summary}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def write_distillation_log(args) -> None:
    """写入蒸馏日志（统一日志，所有蒸馏记录都在这里）"""
    record_id = generate_record_id(args.source, args.date, args.summary)

    # 确保日志文件存在
    if not DISTILL_LOG.exists():
        DISTILL_LOG.parent.mkdir(parents=True, exist_ok=True)
        header = "# 统一蒸馏管道日志\n\n"
        header += "> P0-4统一蒸馏管道的所有蒸馏记录（入口3你的文件 + 入口5童灵思考）\n"
        header += "> 绑实录源行·方向隔离·幂等去重\n\n"
        header += "| 日期 | 源文件 | 目标层 | 摘要 | 方向 | 来源类型 | 记录ID |\n"
        header += "|------|--------|--------|------|------|---------|--------|\n"
        DISTILL_LOG.write_text(header, encoding="utf-8")

    content = DISTILL_LOG.read_text(encoding="utf-8")

    # 幂等检查
    if record_id in content:
        print(f"✅ 蒸馏日志记录已存在（幂等跳过）: {record_id}")
        return

    # 追加记录（在表格最后一行之后）
    source_type = args.source_type or "你自述"
    log_record = (
        f"| {args.date} | `{args.source}` | {args.target} | {args.summary} | "
        f"{args.direction} | {source_type} | `{record_id}` |\n"
    )

    lines = content.split("\n")
    # 表尾定位：插到"最后一个以 | 开头的行"之后。
    # ⛔ 不再插到分隔线之前——v1.0.0 该写法把记录堆进表头与分隔线之间，
    #    导致 Markdown 表格渲染断裂（预存破损态 2026-10-01 复位）。
    insert_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith("|"):
            insert_idx = i + 1
            break

    lines.insert(insert_idx, log_record.rstrip())
    new_content = "\n".join(lines)

    if args.dry_run:
        print(f"[dry-run] 将写入蒸馏日志: {log_record.strip()}")
        return

    DISTILL_LOG.write_text(new_content, encoding="utf-8")
    print(f"✅ 已写入蒸馏日志（记录ID: {record_id}）")


def main():
    parser = argparse.ArgumentParser(description="统一蒸馏管道L3自动回写辅助脚本")
    parser.add_argument("--source", required=True, help="源文件相对路径（如 greatest/自画像/2026-08.md）")
    parser.add_argument("--target", required=True, choices=["L2", "L3", "L6"], help="目标层")
    parser.add_argument("--summary", required=True, help="蒸馏内容摘要")
    parser.add_argument("--date", required=True, help="蒸馏日期（YYYY-MM-DD）")
    parser.add_argument("--direction", required=True, choices=["你→童灵", "童灵→童灵"], help="方向（用于方向隔离标注）")
    parser.add_argument("--source-type", default="你自述", choices=["你自述", "AI观察"], help="来源类型（默认你自述）")
    parser.add_argument("--dry-run", action="store_true", help="只输出不写入")

    args = parser.parse_args()

    print(f"🔄 统一蒸馏管道L3回写")
    print(f"   源文件: {args.source}")
    print(f"   目标层: {args.target}")
    print(f"   摘要: {args.summary}")
    print(f"   日期: {args.date}")
    print(f"   方向: {args.direction}")
    print(f"   来源类型: {args.source_type}")
    print()

    # 方向隔离校验（工作流§四-1）
    if args.direction == "童灵→童灵" and args.target == "L2" and "系统日志" not in args.source:
        print("⚠️ 方向隔离警告：童灵→童灵方向的L2认知风格更新，源文件应为系统日志[童灵思考]")
    if args.direction == "你→童灵" and args.target != "L2":
        # v1.1.0 收紧：原判据 `target not in [L2,L3,L6]` 与 choices 恒等=永不触发的死判据，
        # 方向隔离这条散文纪律从未进机械层。现按工作流§四-1 收紧为"你→童灵只可 L2"。
        print("⚠️ 方向隔离警告：你→童灵方向只能分流到L2认知风格/铁律，不得写 L3/L6")

    print()

    # 写入蒸馏日志（唯一真源·v1.1.0 起不再写切片——切片是生成器派生物，
    # 写进去会被下一次 k2_slice_generator 整文件重写抹除·2026-09轮实证）
    write_distillation_log(args)

    print()
    print("✅ 回写完成（真源=distillation_log.md；切片不承载记录，--target 仅作归属层标签）")


if __name__ == "__main__":
    main()
