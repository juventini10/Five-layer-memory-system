#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_contamination_check.py v2 — 布洛陀记忆系统『数据污染检测与清理』
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
    python3 data_contamination_check.py --generate --seed-root ~/记忆共享中心 \\
        --out integrity-fingerprints.json

    # 检测（dry-run）/ 清理（--apply）
    python3 data_contamination_check.py --memory-root ~/记忆共享中心 \\
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
#
# ── 样例面白名单（2026-10-03·根治·⛔ 不再用 glob 扫用户目录）──────────────
# 🔴 原 TARGETS 列的全是**用户数据文件**（SHADOW / 未知未知台账 / 立场卡）——
#    清理器绝不该删用户数据：那是“样例/私有”混同的根，一处爆成“私有指纹入包”、
#    一处爆成“生产机真数据被当样例清空”（见 12 号 §5.9）。
# 🔴 根治口径：清理器只清**明确的随包样例件**（按**具体件名**白名单）；
#    ⛔ 不用 glob 扫用户目录、⛔ 不碰任何“用户自产数据”面。
# 当前包内**无**随包样例件 ⇒ 白名单为空 ⇒ 清理器安全停产（no-op）。
# 若日后确有样例随包，须：① 放包内公开样例目录 ② 用具体件名列此 ③ 池从中立源生成。
TARGETS = []

DIGIT_BLOB = re.compile(r"[0-9]{20,}")
ENV_LINE = re.compile(r"^(\s*environments:\s*)\[[^\]]*\]", re.MULTILINE)


def _norm(block: str) -> str:
    return "\n".join(ln.rstrip() for ln in block.splitlines() if ln.strip())


def _hash(text: str) -> str:
    return hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()


# ── B5 划界裁决（2026-09-20·群友死循环根治）──────────────────────
# 成就系统 9 件 = tracker 管辖的运行时数据域（mode: runtime）——装机后语境下用户
#   文件内容演进（等级校准/阈值改版/打卡数据）与"样例数据"机械不可分：全文哈希
#   比对 → 重置 → tracker 再填 → 死循环（群友实锤）；结构比对 → 抹掉用户结构演进。
#   故 reset 模式整体废除，runtime 件只查存在性·永不重置——包内模板干净度归发布
#   门禁（pkg_cleanliness/check_package_health）管，装机后污染检测只管 surgical 样例块。


def split_blocks(text: str, entry_start):
    if entry_start is None:
        # 整文件＝一块（2026-09-30 件7）：卡库是「一文件一卡」，无内部条目结构，
        #   用 `^# ` 之类只能抓到标题行→1055 张卡仅产 20 块（实测）。整文件哈希才是正确粒度。
        return [(True, text)]
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
def _expand(root: Path, rel: str):
    """rel 匹配的文件列表（支持 `*` / `?` 通配·2026-09-30 件7：卡库是多文件）。"""
    if "*" in rel or "?" in rel:
        return sorted(p for p in root.glob(rel) if p.is_file())
    p = root / rel
    return [p] if p.is_file() else []


def do_generate(seed_root: Path, out_path: Path):
    # 2026-10-03 根治：⛔ 样例源不得是“作者/用户档案”——那会把私有数据打指纹入包。
    #   白名单为空 ⇒ 无事可生成：直接拒绝（防再有人拿作者档案跑 --generate）。
    if not TARGETS:
        print("⛔ 样例面白名单为空——无可生成（清理器已安全停产）。")
        print("   ⛔ 不得以作者/用户档案为样例源（会把私有数据打指纹入包）；")
        print("   如确需样例，请先在 TARGETS 列明**包内公开样例件**的具体件名。")
        return
    pool = set()
    for t in TARGETS:
        if t["mode"] != "surgical":
            continue
        for src in _expand(seed_root, t["rel"]):
            for is_entry, blk in split_blocks(_read(src), t["entry_start"]):
                if is_entry:
                    pool.add(_hash(blk))
    data = {
        "note": "不可逆完整性指纹（SHA256）。用于识别需清理的开发样例数据块。"
                "本文件不含任何可读内容，无法还原或读取原始数据。",
        "version": "2.0.0",
        "generated": datetime.now().strftime("%Y-%m-%d"),
        # 定义域闸锚（2026-10-03）：池由本机（生产机）哪些块生成——存 seed_root 的
        #   SHA256（⛔存明文路径=泄敏）。清理器据此拒绝在**生产机自身**上清理
        #   （生产机上"样例"与真数据同源 ⇒ 清=误删）。
        "seed_root_hash": hashlib.sha256(str(seed_root.resolve()).encode("utf-8")).hexdigest(),
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

    if cfg["mode"] == "runtime":
        # 2026-09-20 B5 根治：成就系统=tracker 管辖的运行时数据域——用户文件内容演进
        #   （等级校准/阈值改版）与"样例数据"在机械上不可分，任何内容比对都会误判
        #   （全文哈希→死循环实锤；结构哈希→抹掉用户结构演进）。装机后语境唯一合理
        #   判定=存在且 tracker 会重算，内容对错归 tracker/用户管，污染检测无权重置。
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
        # 2026-10-03 根治（LobsterAI 端真装实证·共件）：写入前✅DO先判「目标可写性」这一面
        #   ——命中样例指纹 ≠ 可改（用户可能对 SSOT 设 444 只读、或文件被锁/非本用户所有）。
        #   不可写 ⇒ ⛔不崩、⛔不静默：显式上报"跳过(只读)"并继续其余文件（降级粒度=单文件）。
        #   原则：尊重用户对文件的保护态——⛔不用 chmod 强改用户权限。
        if not os.access(path, os.W_OK):
            acts.append(f"⚠️ 目标只读·跳过写入（{path.name}）——样例块保留·需用户放开权限后重跑 --apply")
        else:
            try:
                _backup(path)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError as e:
                acts.append(f"⚠️ 写入失败·跳过（{path.name}: {e}）——不阻塞其余文件")
    return acts


def do_scan(memory_root: Path, fp_path: Path, tmpl_root: Path, apply: bool, force_producer: bool = False):
    pool = set()
    producer_hash = None
    if fp_path.exists():
        _fp = json.loads(fp_path.read_text(encoding="utf-8"))
        pool = set(_fp.get("fingerprints", []))
        producer_hash = _fp.get("seed_root_hash")
    # ── 定义域闸（2026-10-03·LobsterAI 端真装事故根治·承条文 18“定义域”）────────
    #   指纹池由**生产机**（作者记忆中心）生成的“样例”块哈希。在**生产机自身**上
    #   跑 --apply：生产机的真数据与“样例”同源（同一批块）⇒ 全命中 ⇒ 清=误删
    #   （实测：1050 张立场卡被清空）。故：目标根 == 池的生产根 ⇒ 拒绝执行。
    #   判据=哈希比对（⛔不泄露明文路径）。端用户机根本不同 ⇒ 不受影响。
    if producer_hash:
        target_hash = hashlib.sha256(str(memory_root.resolve()).encode("utf-8")).hexdigest()
        if target_hash == producer_hash and not force_producer:
            print("🛑 定义域闸：本机即指纹池的**生产机**（作者记忆中心）。")
            print("   在此清理会把本机真数据当成样例清掉——已拒绝执行（安全 no-op）。")
            print("   端用户机根路径不同，不受影响。")
            return 0
        # 双重确认（2026-10-03·Agent B 独立审查补）：--force-producer 单旗标易被脚本误传
        #   ⇒ 须**同时**设环境变量 BULUOTUO_I_KNOW_PRODUCER=1，否则拒绝（防后门误触自毁）。
        if target_hash == producer_hash and force_producer \
                and os.environ.get("BULUOTUO_I_KNOW_PRODUCER") != "1":
            print("🛑 定义域闸：--force-producer 需同时设环境变量 BULUOTUO_I_KNOW_PRODUCER=1"
                  "（双重确认·防脚本误传）。已拒绝。")
            return 0
    hits, scanned = 0, 0
    print(f"🔍 数据污染{'清理' if apply else '检测(dry-run)'} · {memory_root}\n")
    for cfg in TARGETS:
        for path in _expand(memory_root, cfg["rel"]):
            scanned += 1
            # 2026-10-03 根治（共件）：单文件处理失败⛔不得拖垮整轮扫描——
            #   原逻辑 PermissionError 直接冒泡中止，setup.sh [2/6] 连带中止整轮端 setup。
            #   改为逐文件隔离：异常显式上报并继续（fail-soft·但可见）。
            try:
                acts = clean_file(path, cfg, pool, tmpl_root, apply)
            except Exception as e:
                hits += 1
                print(f"  ⚠️  {path.name}")
                print(f"       - ⚠️ 处理异常·跳过：{type(e).__name__}: {e}")
                continue
            if acts:
                hits += 1
                print(f"  ⚠️  {path.name}")
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
    ap.add_argument("--force-producer", action="store_true",
                    help="在指纹池的生产机上也执行清理（⛔危险·仅调试）")
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
                   Path(os.path.expanduser(a.fingerprints)), tr, a.apply,
                   force_producer=a.force_producer)
    sys.exit(1 if (hits and not a.apply) else 0)


if __name__ == "__main__":
    main()
