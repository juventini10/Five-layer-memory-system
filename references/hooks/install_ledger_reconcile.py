#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# TRUTH_OF: 脚本中心/install_ledger_reconcile.py   # 真源声明·派生面须软链指向本件
# -*- coding: utf-8 -*-
"""install_ledger_reconcile.py v1.0.2 — install_ledger 台账对账器（幂等缓存自动追平·分叉隔离）

v1.0.2 多面隔离（首跑 --apply 后二跑 --check 显形 redeploy=10 的根因）：同名多条目各面 src
内容异 → 单键台账逐条处理必随遍历顺序交替刷（二跑又红）；改为整组识别、⛔不动账、归布局治理。

v1.0.1 判据纠偏（自批判实测 v1.0.0 conflict=14 系误判）：installer 自家注释（L267）声明
「脱敏/重写后 dst≠源内容，绝不能比内容」——台账真口径=ledger[name]==sha(src)，
dst 内容差异是投递改写产物/本端演化的正常态，不是分叉。改态后：ledger==sha(src)→noop；
ledger≠sha(src) 且 dst 缺→pending；dst 在且严格等于 src→auto（纯缓存滞后刷账）；
其余→redeploy_needed（安装器本职·⛔reconcile 不越权投递、不刷账、不动文件）。

根因（2026-10-07 童灵D3 全量根治）：install_script_center.py 的 source_sha 台账是幂等比较
缓存，唯一刷新路径=全量跑安装器（会连带补投 64 个 dst 缺失文件+1 个覆盖·动作面远超"刷账"），
导致作者侧长期"账实分离不敢刷"——本端哲学（皮叔 2026-10-07 重申）：一切文件源侧唯一真源，
呈现物=映射派生；台账这类机器缓存也必须由机器代写（锚: 立场卡#S922 手写演进值副本必烂），
⛔ 人肉凑数、⛔ 一次性全量覆盖。

三态判据（与 installer 的 sha8=sha256[:8] 口径逐字一致）：
  noop     ledger==sha(src)                 → 安装器语义已同步（dst 为改写产物不追究）
  auto     ledger≠sha(src) 且 dst==src     → 纯缓存滞后·--apply 机械追平（零内容动作）
  pending  ledger≠sha(src) 且 dst 不存在    → 需重新投递/补投·列入待裁决清单（不刷账）
  redeploy ledger≠sha(src) 且 dst 存在内容异 → 源已变未重投·安装器本职·列入清单不动
  src_missing 源不存在                       → 他端专属/已移除·不动
  multi_face 同名多条目且各面 src 内容异     → installer 台账单键结构交替（非文件病）·⛔不动账·只报告

用法：
  python3 install_ledger_reconcile.py --check     # 只报计数（generate_release 守卫9c 软探测·exit恒0除非内部错）
  python3 install_ledger_reconcile.py --dry-run   # 计数+清单（默认）
  python3 install_ledger_reconcile.py --apply     # 追平 auto + 写 pending 清单（先备份台账至记忆琥珀）
  python3 install_ledger_reconcile.py --self-test # /tmp 夹具五态压测（铁律-014·不碰真实文件）
退出码：0 正常（含"有漂移"——对账器是报告者不是门禁·拦不拦由调用方定）| 1 内部错误
设计约束：纯 stdlib·原子写(tmp+os.replace)·append-only 台账语义不适用（缓存整体重算是设计内动作· installer 同姿势）。
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time

def sha8(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:8]
    except Exception:
        return None


def reconcile(manifest_path, ledger_path, base, dst_root):
    """核心三态判定——self-test 与真机共用同一函数（⛔两套逻辑=判据分叉）。"""
    man = json.load(open(manifest_path, encoding="utf-8"))["scripts"]
    led = json.load(open(ledger_path, encoding="utf-8"))
    src_sha = led.get("source_sha", {})
    counts = {"noop": 0, "auto": 0, "pending": 0, "redeploy": 0, "src_missing": 0, "multi_face": 0}
    pend, red = [], []
    new_sha = dict(src_sha)
    # 预扫：同名分组，多面且内容异者整组隔离（⛔不逐条处理——单键台账下逐条处理会随遍历顺序交替漂）
    groups = {}
    for e in man:
        if e.get("name") and e.get("path"):
            groups.setdefault(e["name"], []).append(e)
    multi = set()
    for nm, es in groups.items():
        shas = set()
        for e in es:
            rp = e["path"]
            if "待完成工作" in rp:      # 草稿工作区非运行面/派生面·分叉=在途常态，豁免（2026-10-07 实测4组假警报根因）
                continue
            sp = rp if rp.startswith("/") else os.path.join(base, rp)
            if os.path.exists(sp):
                try:
                    shas.add(sha8(sp))
                except Exception:
                    pass
        if len(shas) > 1:
            multi.add(nm)
            counts["multi_face"] += 1
            red.append({"name": nm, "faces": len(es),
                        "verdict": "同名多面内容异=installer 单键台账结构交替·归布局治理非对账职责"})
    for e in man:
        name = e.get("name")
        rel = e.get("path", "")
        if not name or not rel or name in multi:
            continue
        if "待完成工作" in rel:      # 草稿面不作 src 判定（与预扫豁免同源·2026-10-07 二修）
            continue
        src = os.path.join(base, rel) if not rel.startswith("/") else rel
        dst = os.path.join(dst_root, name)
        if not os.path.exists(src):
            counts["src_missing"] += 1
            continue
        s = sha8(src)
        if src_sha.get(name) == s:
            counts["noop"] += 1
            continue
        if not os.path.exists(dst):
            counts["pending"] += 1
            pend.append({"name": name, "src": rel, "src_sha": s,
                         "ledger_sha": src_sha.get(name),
                         "verdict": "需投递/补投——安装器本职·本端当前运转正常·存在即证据；如后续有引用再跑 installer"})
            continue
        if sha8(dst) == s:
            # dst 内容已等于 src·仅台账滞后 → auto
            counts["auto"] += 1
            new_sha[name] = s
            continue
        counts["redeploy"] += 1
        red.append({"name": name, "src": rel, "src_sha": s, "dst_sha": sha8(dst),
                    "ledger_sha": src_sha.get(name),
                    "verdict": "源已变未重投（或 dst 本端演化待回流）·⛔reconcile 不投递不覆盖·跑 installer 前须先定性方向"})
    return counts, new_sha, pend, red


def write_ledger(ledger_path, new_sha, backup_dir):
    led = json.load(open(ledger_path, encoding="utf-8"))
    led["source_sha"] = new_sha
    led["reconcile_at"] = time.strftime("%Y-%m-%d %H:%M")
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(ledger_path, os.path.join(
            backup_dir, "install_ledger.json.pre-reconcile-%s" % time.strftime("%H%M%S")))
    tmp = ledger_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(led, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ledger_path)


def self_test():
    import tempfile
    base = tempfile.mkdtemp(prefix="reconcile_selftest_")
    arc = os.path.join(base, "[记忆共享中心]")
    dev = os.path.join(arc, "开发工具")
    ctr = os.path.join(arc, "脚本中心")
    os.makedirs(dev); os.makedirs(ctr)
    def put(d, n, c):
        p = os.path.join(d, n)
        open(p, "w", encoding="utf-8").write(c)
        return p
    put(dev, "auto.py", "X"); put(ctr, "auto.py", "X")            # auto: 账滞后·文件同
    put(dev, "noop.py", "Y"); put(ctr, "noop.py", "Y")            # noop: 账实一致
    put(dev, "missing.py", "Z")                                    # pending: 无dst
    put(dev, "conflict.py", "A"); put(ctr, "conflict.py", "B")    # redeploy: 源变未重投
    put(dev, "gone.py", "C")  # src_missing 需要 ledger 有 key 但 src 无 → 用假条目路径
    put(dev, "twin_a.py", "T1")
    put(arc, "twin_b.py", "T2")  # 多面组：同名两面内容异
    entries = [
        {"name": "auto.py", "path": "[记忆共享中心]/脚本中心/auto.py"},
        {"name": "noop.py", "path": "[记忆共享中心]/脚本中心/noop.py"},
        {"name": "missing.py", "path": "[记忆共享中心]/脚本中心/missing.py"},
        {"name": "conflict.py", "path": "[记忆共享中心]/脚本中心/conflict.py"},
        {"name": "gone.py", "path": "[记忆共享中心]/脚本中心/deleted.py"},
        {"name": "twin.py", "path": "[记忆共享中心]/脚本中心/twin_a.py"},
        {"name": "twin.py", "path": "个人AI档案/twin_b.py"},
    ]
    mp = put(dev, "scripts_manifest.json", json.dumps({"scripts": entries}))
    led = {"source_sha": {
        "auto.py": "00000000", "noop.py": sha8(os.path.join(dev, "noop.py")),
        "missing.py": "00000000", "conflict.py": "00000000", "gone.py": "00000000",
        "twin.py": "00000000"}}
    lp = put(ctr, "install_ledger.json", json.dumps(led))
    counts, new_sha, pend, red = reconcile(mp, lp, base, ctr)
    assert counts == {"noop": 1, "auto": 1, "pending": 1, "redeploy": 1,
                      "src_missing": 1, "multi_face": 1}, counts
    assert new_sha["twin.py"] == "00000000", "多面组不得动账"
    assert new_sha["auto.py"] == sha8(os.path.join(dev, "auto.py"))
    assert new_sha["conflict.py"] == "00000000", "redeploy 不得刷账"
    assert new_sha["missing.py"] == "00000000", "pending 不得刷账"
    assert len(pend) == 1 and len(red) == 2, red  # redeploy 1 + multi_face 1 同列红清单
    bk = os.path.join(base, "bk")
    write_ledger(lp, new_sha, bk)
    got = json.load(open(lp, encoding="utf-8"))
    assert got["source_sha"]["auto.py"] != "00000000" and got["source_sha"]["conflict.py"] == "00000000"
    assert len(os.listdir(bk)) == 1, "备份缺失"
    # 幂等二跑：auto 归入 noop
    counts2, *_ = reconcile(mp, lp, base, ctr)
    assert counts2["auto"] == 0 and counts2["noop"] == 2, counts2
    shutil.rmtree(base, ignore_errors=True)
    print("SELF-TEST GREEN: 五态判定+redeploy/pending保护+原子写+备份+幂等二跑 全通过")
    return 0


def main():
    ap = argparse.ArgumentParser(description="install_ledger 三态对账器")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只报计数行（发包链软探测）")
    g.add_argument("--dry-run", action="store_true", help="计数+清单（默认动作）")
    g.add_argument("--apply", action="store_true", help="追平 auto + 写 pending 清单 + 备份台账")
    g.add_argument("--self-test", action="store_true", help="fixture 五态压测")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    H = os.path.expanduser("~")
    arc = os.path.join(H, "[记忆共享中心]")
    mp = os.path.join(arc, "开发工具", "scripts_manifest.json")
    lp = os.path.join(arc, "脚本中心", "install_ledger.json")
    ctr = os.path.join(arc, "脚本中心")
    counts, new_sha, pend, red = reconcile(mp, lp, H, ctr)
    drift = counts["auto"] + counts["pending"] + counts["redeploy"] + counts["multi_face"]
    if a.check:
        print("LEDGER_DRIFT total=%d auto=%d pending=%d redeploy=%d multi_face=%d noop=%d src_missing=%d" % (
            drift, counts["auto"], counts["pending"], counts["redeploy"], counts["multi_face"],
            counts["noop"], counts["src_missing"]))
        return 0
    print("=== install_ledger 对账 ===")
    print("noop(账实一致)=%d  auto(纯缓存滞后)=%d  pending(缺位待投)=%d  redeploy(源变未重投)=%d  multi_face(同名多面异)=%d  src_missing=%d"
          % (counts["noop"], counts["auto"], counts["pending"], counts["redeploy"], counts["multi_face"], counts["src_missing"]))
    for r in red:
        if "faces" in r:
            print("🟠 MULTI_FACE: %s（%d面同名异内容·归布局治理不动账）" % (r["name"], r["faces"]))
        else:
            print("🟡 REDEPLOY: %s src=%s dst=%s ledger=%s" % (r["name"], r.get("src_sha"), r.get("dst_sha"), r.get("ledger_sha")))
    if a.apply:
        write_ledger(lp, new_sha, os.path.join(arc, "记忆琥珀", "reconcile-根治-20261007"))
        pj = os.path.join(ctr, "install_pending_adjudication.json")
        tmp = pj + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"generated_by": "install_ledger_reconcile.py v1.0.2",
                       "generated_at": time.strftime("%Y-%m-%d %H:%M"),
                       "pending_missing_dst": pend, "redeploy_or_multi_face": red},
                      f, ensure_ascii=False, indent=1)
        os.replace(tmp, pj)
        print("APPLIED: 台账追平 %d 条·裁决清单已落 %s" % (counts["auto"], pj))
    else:
        print("(dry-run: 未写任何文件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
