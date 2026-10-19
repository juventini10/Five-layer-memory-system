#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assign_kb_no.py — 知识卡 kb_no 机器编号发号与台账同步（2026-10-13 立法轮遗留③·2026-10-15 落地）

用法：
  python3 assign_kb_no.py --allocate N    # 领 N 个连续号（读池内实况+台账 max+1·只读不改任何文件）
  python3 assign_kb_no.py --sync          # 池内缺号卡补插 #Z 号（紧插 card_id 下一行）+ 重跑 kb_no_map.build() 刷台账 + 双向对账

纪律：
- 发号唯一入口（本脚本）；台账 kb_no_map.json 由 kb_no_map.py build() 重建，本脚本不手写台账键值。
- 显示面零改动：只增 frontmatter 一行，card_id/文件名/正文一字不动。
- 幂等：--sync 对已带号卡零改动；--allocate 纯只读。
"""
import os, re, sys, glob, json, importlib.util
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass  # Windows cp1252 控制台防非ASCII print 崩（F2 根治·2026-10-17）

HOME = os.path.expanduser("~")
POOL = os.path.join(HOME, "[日记仓库]", "2-知识库", "05-知识池")
MAP_PY = os.path.join(os.path.expanduser("[记忆共享中心]"), "脚本中心", "kb_no_map.py")
MAP_JSON = os.path.join(os.path.expanduser("[记忆共享中心]"), "脚本中心", "data", "kb_no_map.json")
PAT = re.compile(r"^#Z\d{4}$")


def pool_cards():
    """[(path, fm, raw)] 全部 reading-card（含书夹与文章卡片）"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from note_validator import parse_frontmatter
    out = []
    for fp in sorted(glob.glob(POOL + "/*/*.md")):
        if os.path.basename(fp) == "INDEX.md":
            continue
        t = open(fp, encoding="utf-8").read()
        fm, _ = parse_frontmatter(t)
        if fm.get("type") == "reading-card":
            out.append((fp, fm, t))
    return out


def current_max():
    nums = [0]
    for _, fm, _ in pool_cards():
        k = str(fm.get("kb_no", ""))
        if PAT.match(k):
            nums.append(int(k[2:]))
    try:
        m = json.load(open(MAP_JSON, encoding="utf-8"))
        for v in m.values():
            if PAT.match(str(v)):
                nums.append(int(str(v)[2:]))
    except Exception:
        pass
    return max(nums)


def cmd_allocate(n):
    mx = current_max()
    print(" ".join(f"#Z{mx + i:04d}" for i in range(1, n + 1)))


def cmd_sync():
    cards = pool_cards()
    missing = [(fp, fm, t) for fp, fm, t in cards if not PAT.match(str(fm.get("kb_no", "")))]
    mx = current_max()
    taken = {str(fm.get("kb_no")) for _, fm, _ in cards if PAT.match(str(fm.get("kb_no", "")))}
    print(f"池内 reading-card {len(cards)} 张；缺号 {len(missing)} 张；当前最大号 #Z{mx:04d}")
    for i, (fp, fm, t) in enumerate(missing, 1):
        no = f"#Z{mx + i:04d}"
        assert no not in taken, f"发号撞号: {no}"
        lines = t.split("\n")
        idx = next(j for j, ln in enumerate(lines) if ln.strip().startswith("card_id:"))
        lines.insert(idx + 1, f"kb_no: {no}")
        open(fp, "w", encoding="utf-8").write("\n".join(lines))
        taken.add(no)
        print(f"  插号 {no} → {os.path.relpath(fp, POOL)}")
    # 刷台账（kb_no_map.build 只读池重建 json）
    spec = importlib.util.spec_from_file_location("kb_no_map", MAP_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = mod.build()
    os.makedirs(os.path.dirname(MAP_JSON), exist_ok=True)
    json.dump(m, open(MAP_JSON, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"台账已刷：{len(m)} 键")
    # 双向对账
    after = pool_cards()
    nos = [str(fm.get("kb_no")) for _, fm, _ in after]
    dup = sorted({x for x in nos if nos.count(x) > 1})
    no_kb = [os.path.relpath(fp, POOL) for fp, fm, _ in after if not PAT.match(str(fm.get("kb_no", "")))]
    map_vals, card_nos = set(m.values()), set(nos)
    print(f"对账：卡 {len(after)} / 唯一号 {len(set(nos))} / 重号 {dup if dup else '无'} / 仍缺号 {len(no_kb)}")
    print(f"map↔卡：map独有 {sorted(map_vals - card_nos)[:5]}；卡独有 {sorted(card_nos - map_vals)[:5]}")
    if dup or no_kb:
        sys.exit(1)
    print("SYNC_OK")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--allocate" and sys.argv[2].isdigit():
        cmd_allocate(int(sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == "--sync":
        cmd_sync()
    else:
        print(__doc__)
        sys.exit(2)
