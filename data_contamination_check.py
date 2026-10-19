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
3. 文件分类区别对待：
   - 有用户手写记录的（SHADOW / 未知未知）→ 精准删样例块、留用户条目
   - 纯 tracker 自动生成的展示（成就系统）→ runtime 域·⛔不整体重置（B5 死循环，见下）；
     仅对「历史发布包曾带出的作者泄露行」做 surgical 精准清除（见 scrub_achievement_legacy）；
     出包干净度主责在 mirror 投影脱敏 + A7 隐私门禁（release_privacy_guard）。

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

# ── 成就存量泄露行精准清除（2026-10-13·隐私红线·用户令「只清我不清用户」）──────
# 历史发布包曾把作者成就个人数据（书名/✅已完成/达成日期/概念碰撞LOG）随包带出。
# 已知作者泄露行的不可逆 SHA256 行级哈希池：删哈希==该行；用户自录行内容不同→哈希不同→零误删。
# ⛔不并入 TARGETS（2026-10-03 no-op 根治·勿回退）。生产机闸护作者自己的成就（真数据不清）。
ACHIEVE_LEGACY_HASHES = frozenset({
    "04ce256f2a332ae75402300ad1455245b84f3dae2a02828e681d64efc9b4c286",
    "061ae509d97f1a63a7ad04676f72fdf29d13acc3c3b17ccac40462d0624ae007",
    "1e1f3b3ac1d1223725915596510ac81f25d8aefbc5f1e0ae65e4ff22b396ddc7",
    "33af19bc119e783a58cb9c1e5c7a624bd9cda9366cc3c7a0649077ddd880d92d",
    "3576d8fa32cdaaf46eaf5dbbd22c0fcc5d1174057771f05b76d8abe4eafd7020",
    "388558233bf53f158da4fa266953d39ca6e361d48611cb647b4005471b04be32",
    "4d726d6404b58120432dc9ac9241dfcb4981421e59f89802d5092e11522fe580",
    "52eca83f8ef77377aebe30d988a5ef7ff903d36d7ab7d1e616df2b951c4fc439",
    "54bf9e8399bdd907ad10f67b424aea4a8697968693f8d17279bb8f632219cc85",
    "5e10ec2d4b46a8929acc02d24f0b0c5cd2121415ac8b2f69fbd1570aa7dc0312",
    "7dc2c18773919d501e2f0c112cf1e045a56bf404b5e589b308e3d48139fdd748",
    "7fad85f7bb880e64a7793a6ad6caa1da14e987fbcbfe0a7a1818c668ff11941e",
    "80d6d7b2643201e9aa52b259f580a328be071c3d8872aab3f7ba782ed3f5478d",
    "87c140317fbf62fc6f7f26016eaeb9e4bfeee2e07fa630081e336ebe235c3034",
    "8979e8e5b1fdba7cf8bb4e896f894ebb8b9842e1f1ecf8b8f4b020c2bd6a2793",
    "8ed0e0daaadc513468ea7f3f01328e10497d9b63dc3acfc89893e699b55f5b62",
    "9118d57e92c626e31bb5480b5252ee74551d6c3332f429189ef62247e0a65cf7",
    "920b2a27cbf39bdca6fc17c4ca78634fcc7d5ccd7118f2b72e73e283eaa374c4",
    "a294b06bfa39447d443da4683c03d5039c9e5cb4677c3979480d072a02af63d8",
    "b78af28ba089048983fcbe63e2cd41cd6fab6f0df4a5cbed1a60d886caeb0967",
    "c0fd8f64f7b9370543573e586f86e7d1885870968992faa8e6b92568cbfd916c",
    "cbc1a71d1ff83a9cca043af2e5ff4a2b43020e8f31f2dd9d0dc5514ac2add061",
    "e087cbbbe5f6f07349f7dfc1df87a9bd9d2fbf734b6767c6383ba409885d8343",
    "f41fd26898bb7d4dcb90fff2b4d2aeec4209f09202d5a36f20cdba9cadf8ea5c",
    "fbbfb55743049324aef538646f9a354284ba434e8f9d76e43ce679299c0283e5",
    "fbf822d28a0375a87b6ec026ec1877fd779989b04e3eb3ae79018444b02a4de2",
})
# C31 声明：本路径＝作者侧旧包标记（生产机有该目录才命中）；端用户机器恒不存在属预期，
#   已登记 personal-path-whitelist.json（唯一登记处）——门禁长期共账，⛔ 另开豁免口。
_ACH_LEAK_MARKER_DIR = os.path.expanduser("~/个人AI档案/发布库/布洛陀-安装包-备份版")

def _ach_h(t):
    return hashlib.sha256(chr(10).join(ln.rstrip() for ln in t.splitlines() if ln.strip()).encode(chr(117)+chr(116)+chr(102)+chr(45)+chr(56))).hexdigest()

def scrub_achievement_legacy(memory_root, apply, force_producer=False):
    ad = Path(memory_root) / "成就系统"
    if not ad.is_dir():
        return 0
    if apply and not force_producer and os.path.isdir(_ACH_LEAK_MARKER_DIR):
        print("  info 成就存量清除：生产机检测作者侧旧包，跳过 apply（作者成就=真数据，--force-producer 强制）")
        return 0
    total = 0
    for p in sorted(ad.glob("*.md")):
        try:
            lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
        except OSError:
            continue
        kept = [ln for ln in lines if not (ln.strip() and _ach_h(ln) in ACHIEVE_LEGACY_HASHES)]
        removed = len(lines) - len(kept)
        if removed:
            total += removed
            print("   %s: 命中作者泄露行 %d 条 %s" % (p.name, removed, "(已删.bak)" if apply else "(dry-run)"))
            if apply:
                if not os.access(p, os.W_OK):
                    continue
                p.with_suffix(p.suffix + ".pre-achscrub.bak").write_text("".join(lines), encoding="utf-8")
                p.write_text("".join(kept), encoding="utf-8")
    return total


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
# 【2026-10-13 补·隐私红线】上述「永不重置」指整文件 reset；对**已知作者泄露行**的 surgical
#   行级哈希清除（scrub_achievement_legacy·见 ACHIEVE_LEGACY_HASHES）是本裁决的窄例外——只删哈希==
#   作者确切泄露行、用户自录行哈希不同→零误删、生产机闸护作者自己成就，与「不误删用户」一致。


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
    ach = scrub_achievement_legacy(os.path.expanduser(a.memory_root), a.apply, force_producer=a.force_producer)
    if ach:
        print("  scrub 成就存量泄露行 %s %d 条（用户自录行完整保留）" % (("已清除" if a.apply else "命中待清"), ach))
    sys.exit(1 if ((hits or ach) and not a.apply) else 0)


if __name__ == "__main__":
    main()
