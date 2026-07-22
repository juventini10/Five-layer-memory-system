#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据污染检测.py v2 — 布洛陀记忆系统『数据污染检测与清理』
=================================================================

用途
----
任何安装路径（全新 / 升级 / 覆盖重装）都应先跑一次本检测，清理早期版本
打包时误带进来的开发样例数据。**精准清理，绝不误删用户自己的记录。**

第一性原理（为什么这样设计）
----------------------------
1. 尊重用户数据 → 用完整 SHA256 精确匹配，只删哈希命中的样例块；用户自录
   条目哈希不同，数学上零误删。
2. 尊重作者隐私 → 参照物是不可逆哈希（扁平指纹池，无原文、无计数结构）。
   普通人打开只见乱码，无法读取/还原任何内容。
3. 两类文件区别对待：
   - 有用户手写记录的（SHADOW / 未知未知）→ 精准删样例块、留用户条目
   - 纯 tracker 自动生成的展示（成就系统）→ 重置为标准模板，tracker 下次重算

用法
----
    # 开发侧：生成扁平指纹池
    python3 数据污染检测.py --generate --seed-root ~/个人AI档案 \\
        --out integrity-fingerprints.json

    # 检测（dry-run）/ 清理（--apply）
    python3 数据污染检测.py --memory-root ~/个人AI档案 \\
        --fingerprints integrity-fingerprints.json \\
        --template-root <新包>/references --apply
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Windows 控制台默认非 UTF-8(cp1252)，强制 stdout/stderr 用 UTF-8，
# 否则 print emoji/中文(✅🔍⚠️) 会 UnicodeEncodeError 崩溃。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# mode: surgical=精准删样例块(留用户数据) / reset=重置为模板(tracker再生)
TARGETS = [
    {"rel": "潜意识层/SHADOW.md", "mode": "surgical", "entry_start": r"^### "},
    {"rel": "未知未知/悬置区.md", "mode": "surgical", "entry_start": r"^### 残差#"},
    {"rel": "未知未知/断言台账.md", "mode": "surgical", "entry_start": r"^### 断言#"},
    {"rel": "未知未知/显形台账.md", "mode": "surgical", "entry_start": r"^\| #\d"},
    {"rel": "成就系统/README.md", "mode": "reset", "tmpl": "成就系统/README.md"},
    {"rel": "成就系统/健康成就.md", "mode": "reset", "tmpl": "成就系统/健康成就.md"},
    {"rel": "成就系统/内容创作成就.md", "mode": "reset", "tmpl": "成就系统/内容创作成就.md"},
    {"rel": "成就系统/成就速查.md", "mode": "reset", "tmpl": "成就系统/成就速查.md"},
    {"rel": "成就系统/月亮之子成就.md", "mode": "reset", "tmpl": "成就系统/月亮之子成就.md"},
    {"rel": "成就系统/番茄成就.md", "mode": "reset", "tmpl": "成就系统/番茄成就.md"},
    {"rel": "成就系统/通用打卡成就.md", "mode": "reset", "tmpl": "成就系统/通用打卡成就.md"},
    {"rel": "成就系统/阅读成就.md", "mode": "reset", "tmpl": "成就系统/阅读成就.md"},
    {"rel": "成就系统/运动成就.md", "mode": "reset", "tmpl": "成就系统/运动成就.md"},
]

DIGIT_BLOB = re.compile(r"[0-9]{20,}")
ENV_LINE = re.compile(r"^(\s*environments:\s*)\[[^\]]*\]", re.MULTILINE)


def _norm(block: str) -> str:
    return "\n".join(ln.rstrip() for ln in block.splitlines() if ln.strip())


def _hash(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


def split_blocks(text: str, entry_start: str):
    rx = re.compile(entry_start)
    blocks, cur, is_entry = [], [], False
    for ln in text.splitlines(keepends=True):
        if rx.search(ln):
            if cur:
                blocks.append((is_entry, "".join(cur)))
            cur, is_entry = [ln], True
        elif is_entry and re.match(r"^## ", ln):
            blocks.append((is_entry, "".join(cur)))
            cur, is_entry = [ln], False
        else:
            cur.append(ln)
    if cur:
        blocks.append((is_entry, "".join(cur)))
    return blocks


def _read(p: Path) -> str:
    with open(p, "r", encoding="utf-8-sig") as f:
        return f.read()


# ── 生成扁平指纹池（开发侧）─────────────────────────────────────
def do_generate(seed_root: Path, out_path: Path):
    pool = set()
    for t in TARGETS:
        if t["mode"] != "surgical":
            continue
        src = seed_root / t["rel"]
        if not src.exists():
            continue
        for is_entry, blk in split_blocks(_read(src), t["entry_start"]):
            if is_entry:
                pool.add(_hash(blk))
    data = {
        "note": "不可逆完整性指纹（SHA256）。用于识别需清理的开发样例数据块。"
                "本文件不含任何可读内容，无法还原或读取原始数据。",
        "version": "2.0.0",
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "fingerprints": sorted(pool),  # 扁平池，无文件归属、无计数结构
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"✅ 扁平指纹池已生成: {out_path}（{len(pool)} 条不可逆指纹，无结构无原文）")


def generic_clean(text: str):
    acts = []
    new = ENV_LINE.sub(lambda m: m.group(1) + "[WorkBuddy]", text)
    if new != text:
        acts.append("environments 归一化"); text = new
    if DIGIT_BLOB.search(text):
        text = DIGIT_BLOB.sub("", text); acts.append("清除长数字块")
    return text, acts


def _backup(path: Path):
    bak = path.with_suffix(path.suffix + ".pre-decontam.bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def clean_file(path: Path, cfg: dict, pool: set, tmpl_root: Path, apply: bool):
    text = _read(path); orig = text; acts = []

    if cfg["mode"] == "reset":
        tmpl = (tmpl_root / cfg["tmpl"]) if tmpl_root else None
        if tmpl and tmpl.exists() and _hash(text) != _hash(_read(tmpl)):
            if apply:
                _backup(path); shutil.copy2(tmpl, path)
            return ["重置为标准模板（成就展示由 tracker 自动重算，无手写数据损失）"]
        return []

    # surgical：只删哈希命中样例块，用户自录条目保留
    kept, removed = [], 0
    for is_entry, blk in split_blocks(text, cfg["entry_start"]):
        if is_entry and _hash(blk) in pool:
            removed += 1; continue
        kept.append(blk)
    if removed:
        text = "".join(kept)
        acts.append(f"精准清除 {removed} 个开发样例块（用户自录条目完整保留）")
    text, gc = generic_clean(text); acts.extend(gc)

    if text != orig and apply:
        _backup(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return acts


def do_scan(memory_root: Path, fp_path: Path, tmpl_root: Path, apply: bool):
    pool = set()
    if fp_path.exists():
        pool = set(json.loads(fp_path.read_text(encoding="utf-8")).get("fingerprints", []))
    hits, scanned = 0, 0
    print(f"🔍 数据污染{'清理' if apply else '检测(dry-run)'} · {memory_root}\n")
    for cfg in TARGETS:
        path = memory_root / cfg["rel"]
        if not path.exists():
            continue
        scanned += 1
        acts = clean_file(path, cfg, pool, tmpl_root, apply)
        if acts:
            hits += 1
            print(f"  ⚠️  {cfg['rel']}")
            for a in acts:
                print(f"       - {a}")
    print(f"\n{'─'*52}")
    if hits == 0:
        print(f"✅ 未检测到数据污染（扫描 {scanned} 文件）— 跳过")
    elif apply:
        print(f"✅ 已清理 {hits}/{scanned} 文件（原文件 .pre-decontam.bak 备份，可还原）")
    else:
        print(f"⚠️  {hits}/{scanned} 文件含样例数据 — 加 --apply 清理")
    return hits


def main():
    ap = argparse.ArgumentParser(description="布洛陀 数据污染检测与清理 v2")
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--seed-root"); ap.add_argument("--out")
    ap.add_argument("--memory-root"); ap.add_argument("--fingerprints")
    ap.add_argument("--template-root"); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if a.generate:
        if not a.seed_root or not a.out:
            print("❌ --generate 需 --seed-root 和 --out"); sys.exit(2)
        do_generate(Path(os.path.expanduser(a.seed_root)), Path(os.path.expanduser(a.out)))
        return
    if not a.memory_root or not a.fingerprints:
        print("❌ 需 --memory-root 和 --fingerprints"); sys.exit(2)
    tr = Path(os.path.expanduser(a.template_root)) if a.template_root else None
    hits = do_scan(Path(os.path.expanduser(a.memory_root)),
                   Path(os.path.expanduser(a.fingerprints)), tr, a.apply)
    sys.exit(1 if (hits and not a.apply) else 0)


if __name__ == "__main__":
    main()
