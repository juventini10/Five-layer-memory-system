#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
sync_card_frontmatter.py — 卡文件 frontmatter reading_status 与 INDEX.md 同步脚本
职责: 从 INDEX.md status 列读取权威 status，回写到对应卡文件 frontmatter 的 reading_status 字段。
      根治双本账漂移：derive_reading_status.py 只写 INDEX 不写卡 frontmatter → 本脚本补同步。
设计: 只读 INDEX + 只写卡文件 frontmatter（不动正文）；幂等可重复跑；只升不降（rank 校验）。
用法:
  python3 sync_card_frontmatter.py             # 全量同步
  python3 sync_card_frontmatter.py --dry-run   # 只报告不写
  python3 sync_card_frontmatter.py --card S821 # 单卡同步
"""
import sys, os, re, glob

from _paths import AILIB_DIR

INDEX_FILE = os.path.join(AILIB_DIR, "INDEX.md") if AILIB_DIR else None

DRY_RUN = "--dry-run" in sys.argv
SINGLE_CARD = None
for arg in sys.argv:
    if arg.startswith("--card="):
        SINGLE_CARD = arg.split("=", 1)[1]
    elif arg == "--card" and sys.argv.index(arg) + 1 < len(sys.argv):
        SINGLE_CARD = sys.argv[sys.argv.index(arg) + 1]

STATUS_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}


def status_rank(s):
    for k, v in STATUS_RANK.items():
        if s.startswith(k):
            return v
    return 0


def parse_index():
    """解析 INDEX.md，返回 {card_id: status}"""
    result = {}
    with open(INDEX_FILE, encoding="utf-8") as f:
        for line in f:
            if not (line.startswith("| 立场卡") or line.startswith("| 技能卡")):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5:
                continue
            cid = cells[0]  # e.g. "立场卡#S821"
            status = cells[4]
            result[cid] = status
    return result


def find_card_file(cid):
    """根据 card_id 找卡文件路径"""
    # cid 格式: "立场卡#S821" 或 "技能卡#K001"
    for p in glob.glob(os.path.join(AILIB_DIR, f"{cid}-*.md")):
        return p
    # 兼容带 # 的文件名
    safe_cid = cid.replace("#", "")
    for p in glob.glob(os.path.join(AILIB_DIR, f"{safe_cid}-*.md")):
        return p
    return None


def sync_one(cid, target_status, dry_run=False):
    """同步单卡 frontmatter reading_status。返回 (changed, old, new, path)"""
    path = find_card_file(cid)
    if not path:
        return False, "", "", f"未找到文件: {cid}"

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 匹配 frontmatter 中的 reading_status 行
    pattern = re.compile(r'^(reading_status:\s*)(.+)$', re.MULTILINE)
    m = pattern.search(content)
    if not m:
        # frontmatter 中没有 reading_status 字段，在 date 行后插入
        date_pattern = re.compile(r'^(date:\s*.+)$', re.MULTILINE)
        dm = date_pattern.search(content)
        if dm:
            new_content = content[:dm.end()] + f"\nreading_status: {target_status}" + content[dm.end():]
            if not dry_run:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
            return True, "(无字段)", target_status, path
        return False, "", "", f"frontmatter 无 date 行: {cid}"

    old_status = m.group(2).strip()
    old_rank = status_rank(old_status)
    new_rank = status_rank(target_status)

    # 只升不降：同 rank 不同标签也纠正（如分身质通过 vs 皮叔已质证）
    if old_status == target_status:
        return False, old_status, target_status, path
    if new_rank < old_rank:
        return False, old_status, target_status, f"降级被阻止（只升不降）: {cid} {old_status}→{target_status}"

    new_content = pattern.sub(rf'\g<1>{target_status}', content, count=1)
    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
    return True, old_status, target_status, path


def main():
    index = parse_index()
    print(f"📚 INDEX 解析: {len(index)} 张卡")

    if SINGLE_CARD:
        # 单卡模式
        cid = SINGLE_CARD if SINGLE_CARD.startswith("立场卡#") or SINGLE_CARD.startswith("技能卡#") else f"立场卡#{SINGLE_CARD}"
        if cid not in index:
            print(f"❌ INDEX 中未找到: {cid}")
            return 1
        changed, old, new, info = sync_one(cid, index[cid], DRY_RUN)
        if changed:
            print(f"✅ {cid}: {old} → {new}")
            if DRY_RUN:
                print("   (dry-run 未写入)")
        else:
            print(f"⏭️  {cid}: 无需变更 ({old})")
        return 0

    # 全量模式
    changes = []
    skipped = 0
    for cid, status in sorted(index.items()):
        changed, old, new, info = sync_one(cid, status, DRY_RUN)
        if changed:
            changes.append((cid, old, new, info))
        elif "无需变更" in info or old == new:
            skipped += 1
        else:
            print(f"⚠️  {info}")

    print(f"\n🔧 同步变更: {len(changes)} 张")
    for cid, old, new, path in changes:
        print(f"   {cid}: {old} → {new}")
    print(f"⏭️  无需变更: {skipped} 张")

    if DRY_RUN:
        print("\nℹ️  dry-run 模式：未写入任何文件")
    elif changes:
        print(f"\n✅ 已同步 {len(changes)} 张卡的 frontmatter reading_status")
    else:
        print("\n✅ 所有卡 frontmatter 已与 INDEX 一致")
    return 0


if __name__ == "__main__":
    from _paths import INSTALLED
    if not INSTALLED:
        print("❌ 未安装态：请先完成安装（需 [记忆共享中心]/脚本中心 布局）")
        sys.exit(1)
    sys.exit(main())
