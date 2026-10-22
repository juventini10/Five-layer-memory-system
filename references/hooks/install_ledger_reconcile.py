#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
# TRUTH_OF: 脚本中心/install_ledger_reconcile.py   # 真源声明·派生面须软链指向本件
# -*- coding: utf-8 -*-
"""install_ledger_reconcile.py v1.0.5 — install_ledger 台账对账器（幂等缓存自动追平·分叉隔离·自诊断腿）

v1.0.5 自诊断腿（2026-10-20 人工批「符合愿景最优解那就去做」·中央账存续裁决的机制落地）：
  --check 在 LEDGER_DRIFT 行后追加 LEDGER_SELFDIAG 行——把上轮只能手跑的三条死活判据
  （账本心跳/消费者计数/包侧verify腿）+ pending 积压 30 天不降判红，焊进已有节奏而非新守卫：
  判红=显形不阻断（本件是报告者非门禁·退出码语义 v1.0.0 起不变）；历史读数字段
  reconcile_history.jsonl append-only·封顶180行·QCN_RECON_HISTORY 隔离缝。
  消费者判据取注册表制（预期名单逐件验在岗·⛔全树扫描——本件被 generate_release 热消费，
  扫全树读文件=发包卡顿；铁律-016 精神：名单会漂，所以每个注册件必须实读验关键词，缺位即红）。
  ⛔不建 launchd 常驻（禁设族·S825 按拆解定步骤：先长在最稳节奏上）；包侧同步两处副本随改更新。

v1.0.4 夹具归位（v1.0.3 首轮修复自身缺陷·如实记账）：v1.0.3 把 conflict 条目的 path 填成
脚本中心目标面路径，致 src==dst 被误判 auto；本轮按真机口径重排（path=作者仓源侧·dst=投递面）。
v1.0.3 自测夹具对齐

v1.0.3 自测夹具对齐（2026-10-08 根治 src_missing:7 假红）：v1.0.2 判据改造后 src 口径=
相对 base(家目录) 或绝对路径（与真 manifest「个人AI档案/...」一致），但 self_test 夹具仍用
旧「[记忆共享中心]/」前缀——该前缀无任何映射逻辑，7 条全判 src_missing=夹具与判据分叉。
纯测试面修复，reconcile() 判定逻辑零改动；missing 夹具改为「源在开发工具·脚本中心无 dst」
真 pending 形态。

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
    FIX_ROOT = "个人AI" + "档案"   # 夹具目录名两段拼接·防发布投影词表改写（审查🔴-1根治2026-10-20·源/包同形）
    arc = os.path.join(base, FIX_ROOT)   # 与真 manifest「个人AI档案/...」相对家目录口径一致（v1.0.3）
    dev = os.path.join(arc, "开发工具")
    ctr = os.path.join(arc, "脚本中心")
    os.makedirs(dev); os.makedirs(ctr)
    def put(d, n, c):
        p = os.path.join(d, n)
        open(p, "w", encoding="utf-8").write(c)
        return p
    # 口径与真机一致：path=源（作者仓侧），dst=dst_root(脚本中心)/<name>（安装投递面）
    put(dev, "auto_src.py", "AUTO_CONTENT_1"); put(ctr, "auto.py", "AUTO_CONTENT_1")   # auto: 账滞后·源与dst内容同
    put(dev, "noop_src.py", "NOOP_CONTENT_2"); put(ctr, "noop.py", "NOOP_CONTENT_2")   # noop: 账实一致
    put(dev, "pending_src.py", "PENDING_CONTENT_3")                                    # pending: 源在·dst缺
    put(dev, "conflict_src.py", "CONFLICT_SRC_A"); put(ctr, "conflict.py", "CONFLICT_DST_B")  # redeploy: 源与dst内容异
    # src_missing：ledger 有 gone.py 的 key 但条目路径指向不存在的文件（无需落盘夹具）
    put(dev, "twin_a_src.py", "TWIN_FACE_1")
    put(arc, "twin_b_src.py", "TWIN_FACE_2")  # 多面组：同名两面内容异
    entries = [
        {"name": "auto.py", "path": f"{FIX_ROOT}/脚本中心/auto.py"},   # auto 语义=源与dst同内容·账滞后·path 即目标面
        {"name": "noop.py", "path": f"{FIX_ROOT}/开发工具/noop_src.py"},
        {"name": "pending.py", "path": f"{FIX_ROOT}/开发工具/pending_src.py"},
        {"name": "conflict.py", "path": f"{FIX_ROOT}/开发工具/conflict_src.py"},
        {"name": "gone.py", "path": f"{FIX_ROOT}/开发工具/deleted.py"},
        {"name": "twin.py", "path": f"{FIX_ROOT}/开发工具/twin_a_src.py"},
        {"name": "twin.py", "path": f"{FIX_ROOT}/twin_b_src.py"},
    ]
    mp = put(dev, "scripts_manifest.json", json.dumps({"scripts": entries}))
    led = {"source_sha": {
        "auto.py": "00000000", "noop.py": sha8(os.path.join(dev, "noop_src.py")),
        "pending.py": "00000000", "conflict.py": "00000000", "gone.py": "00000000",
        "twin.py": "00000000"}}
    lp = put(ctr, "install_ledger.json", json.dumps(led))
    counts, new_sha, pend, red = reconcile(mp, lp, base, ctr)
    assert counts == {"noop": 1, "auto": 1, "pending": 1, "redeploy": 1,
                      "src_missing": 1, "multi_face": 1}, counts
    assert new_sha["twin.py"] == "00000000", "多面组不得动账"
    assert new_sha["auto.py"] == sha8(os.path.join(dev, "auto_src.py"))
    assert new_sha["conflict.py"] == "00000000", "redeploy 不得刷账"
    assert new_sha["pending.py"] == "00000000", "pending 不得刷账"
    assert len(pend) == 1 and len(red) == 2, red  # redeploy 1 + multi_face 1 同列红清单
    bk = os.path.join(base, "bk")
    write_ledger(lp, new_sha, bk)
    got = json.load(open(lp, encoding="utf-8"))
    assert got["source_sha"]["auto.py"] != "00000000" and got["source_sha"]["conflict.py"] == "00000000"
    assert len(os.listdir(bk)) == 1, "备份缺失"
    # 幂等二跑：auto 归入 noop
    counts2, *_ = reconcile(mp, lp, base, ctr)
    assert counts2["auto"] == 0 and counts2["noop"] == 2, counts2
    # === v1.0.5 自诊断腿夹具（隔离压测·铁律-014①）===
    # S1 正例：注册表三坑全造在岗（镜像真实布局：install_script_center/收口闸/generate_release）+包侧腿在→绿
    put(ctr, "install_script_center.py", 'x="install_ledger"')
    put(os.path.join(ctr, "守卫"), "脚本体系收口闸.py", 'y="install_ledger"') if os.makedirs(os.path.join(ctr, "守卫"), exist_ok=True) is None else None
    put(os.path.join(arc, "开发工具", "buluotuo-release-sync"), "generate_release.py", "install_ledger_reconcile --check") if os.makedirs(os.path.join(arc, "开发工具", "buluotuo-release-sync"), exist_ok=True) is None else None
    pkg_dir = os.path.join(arc, "发布库", "五层记忆系统", "布洛陀-全平台安装包")
    os.makedirs(pkg_dir, exist_ok=True)
    put(pkg_dir, "install_scripts.py", "import version_diff as _vd")
    os.environ["QCN_RECON_HISTORY"] = os.path.join(base, "hist.jsonl")
    hist_file = os.environ["QCN_RECON_HISTORY"]
    reds, info = selfdiag(counts, base, arc, ctr)
    assert reds == [], reds
    assert info["consumers"] == 3 and info["verify_leg"] == 1, info
    assert os.path.exists(hist_file), "读数未落盘"
    # S2 判假负例：塞一条 ≥30 天前 pending=0 的旧读数→当前 pending(1)>=0 必翻红 PENDING_BACKLOG
    old_ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - 31 * 86400))
    open(hist_file, "w", encoding="utf-8").write(json.dumps({"ts": old_ts, "pending": 0}) + "\n")
    reds2, _ = selfdiag(counts, base, arc, ctr)
    assert any(r.startswith("PENDING_BACKLOG") for r in reds2), reds2
    # S3 负例：包侧 import 改述→VERIFY_LEG 红（心跳不误报：ledger 刚写 mtime 新）
    put(pkg_dir, "install_scripts.py", "no import here")
    reds3, _ = selfdiag(counts, base, arc, ctr)
    assert any(r.startswith("VERIFY_LEG") for r in reds3), reds3
    # S4 负例：注册表拆一坑（收口闸改名=失词/缺席）→CONSUMERS 计数降但不红（3→2 仍≥2）；再拆一坑→1 红
    put(pkg_dir, "install_scripts.py", "import version_diff as _vd")
    os.remove(os.path.join(ctr, "守卫", "脚本体系收口闸.py"))
    reds4a, _ = selfdiag(counts, base, arc, ctr)
    assert not any(r.startswith("CONSUMERS") for r in reds4a), reds4a
    os.remove(os.path.join(arc, "开发工具", "buluotuo-release-sync", "generate_release.py"))
    reds4, _ = selfdiag(counts, base, arc, ctr)
    assert any(r.startswith("CONSUMERS") for r in reds4), reds4
    # S5 历史封顶：灌 200 行→裁到 ≤180+本次
    open(hist_file, "w", encoding="utf-8").write("\n".join(
        json.dumps({"ts": old_ts, "pending": 9}) for _ in range(200)) + "\n")
    selfdiag(counts, base, arc, ctr)
    assert len(open(hist_file, encoding="utf-8").read().splitlines()) <= 181, "历史封顶失效"
    os.environ.pop("QCN_RECON_HISTORY", None)
    shutil.rmtree(base, ignore_errors=True)
    print("SELF-TEST GREEN: 五态判定+redeploy/pending保护+原子写+备份+幂等二跑+v1.0.5自诊断(S1注册表正例/S2积压红/S3腿红/S4阈值双向/S5封顶) 全通过")
    return 0


def selfdiag(counts, H, arc, ctr):
    """账本消费方健康自诊断（v1.0.5）：三查+pending积压趋势·只显形不阻断不抛异常。
    返回 (reds, info)·info 供行输出；任何内部失败降级为一条 red=SELFDIAG_BROKEN（不拖垮 --check）。"""
    try:
        hist_path = os.environ.get("QCN_RECON_HISTORY") or os.path.join(ctr, "reconcile_history.jsonl")
        now = time.time()
        # 三查：①心跳 30 天内 ②消费者(除自身)≥2 ③包侧 install_scripts import version_diff
        reds = []
        lp = os.path.join(ctr, "install_ledger.json")
        age_d = (now - os.path.getmtime(lp)) / 86400.0 if os.path.exists(lp) else 999
        if age_d > 30:
            reds.append("HEARTBEAT(%.0fd>30d)" % age_d)
        consumers = 0
        # 注册表制：预期消费者名单（相对 arc 或绝对路径），逐件实读验关键词——缺席/失词即不计
        # 名单外新增消费者不计入（诚实边界：注册表需随布局更新，漏更新=计数偏小→偏红不偏绿，fail-closed 方向安全）
        for relp in ("脚本中心/install_script_center.py", "脚本中心/守卫/脚本体系收口闸.py",
                     "开发工具/buluotuo-release-sync/generate_release.py"):
            p = relp if relp.startswith("/") else os.path.join(arc, relp)
            try:
                if "install_ledger" in open(p, encoding="utf-8", errors="replace").read():
                    consumers += 1
            except Exception:
                pass
        if consumers < 2:
            reds.append("CONSUMERS(%d<2)" % consumers)
        pkg_imp = 0
        for pkg_scripts in (os.path.join(arc, "发布库", "五层记忆系统",
                                         "布洛陀-全平台安装包", "install_scripts.py"),):
            try:
                pkg_imp = 1 if "import version_diff" in open(pkg_scripts, encoding="utf-8", errors="replace").read() else 0
            except Exception:
                pkg_imp = 0
        if not pkg_imp:
            reds.append("VERIFY_LEG(absent)")
        # pending 积压趋势：找 ≥30 天前的最近一次读数·当前 pending 未下降→红
        pend_now = counts["pending"]
        old = None
        hist = []
        if os.path.exists(hist_path):
            hist = [l for l in open(hist_path, encoding="utf-8").read().splitlines() if l.strip()]
        for line in hist:
            try:
                r = json.loads(line)
                if now - time.mktime(time.strptime(r["ts"], "%Y-%m-%d %H:%M")) >= 30 * 86400:
                    old = r  # 顺序扫过全部·留最老的一条满足窗口的（更老=更强证据）
            except Exception:
                pass
        if old is not None and pend_now >= old.get("pending", 0):
            reds.append("PENDING_BACKLOG(%d→%d·30d不降)" % (old.get("pending", -1), pend_now))
        # 读数 append-only·封顶 180 行（C-236 可更新账与取证件分层·旧读数被趋势判据消费完即可甄）
        entry = json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M"), "pending": pend_now,
                            "auto": counts["auto"], "redeploy": counts["redeploy"],
                            "noop": counts["noop"], "src_missing": counts["src_missing"]},
                           ensure_ascii=False)
        try:
            with open(hist_path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
            lines = open(hist_path, encoding="utf-8").read().splitlines()
            if len(lines) > 180:
                tmp = hist_path + ".tmp"
                open(tmp, "w", encoding="utf-8").write("\n".join(lines[-180:]) + "\n")
                os.replace(tmp, hist_path)
        except Exception as e:
            reds.append("HIST_WRITE(%r)" % e)
        return reds, {"consumers": consumers, "age_d": round(age_d, 1),
                      "verify_leg": pkg_imp, "hist": os.path.basename(hist_path)}
    except Exception as e:
        return ["SELFDIAG_BROKEN(%r)" % e], {}


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
    arc = os.path.join(H, "个人AI" + "档案")   # 两段拼接防投影词表（同 self_test FIX_ROOT 口径·审查🔴-1）
    mp = os.path.join(arc, "开发工具", "scripts_manifest.json")
    lp = os.path.join(arc, "脚本中心", "install_ledger.json")
    ctr = os.path.join(arc, "脚本中心")
    counts, new_sha, pend, red = reconcile(mp, lp, H, ctr)
    drift = counts["auto"] + counts["pending"] + counts["redeploy"] + counts["multi_face"]
    if a.check:
        print("LEDGER_DRIFT total=%d auto=%d pending=%d redeploy=%d multi_face=%d noop=%d src_missing=%d" % (
            drift, counts["auto"], counts["pending"], counts["redeploy"], counts["multi_face"],
            counts["noop"], counts["src_missing"]))
        reds, info = selfdiag(counts, H, arc, ctr)
        if reds:
            print("LEDGER_SELFDIAG 🔴 %s | consumers=%s ledger_age=%sd verify_leg=%s" % (
                " ".join(reds), info.get("consumers"), info.get("age_d"), info.get("verify_leg")))
        else:
            print("LEDGER_SELFDIAG ✅ 三查全命中(心跳%ss/消费者%s/verify腿%s)·pending积压窗口内无读数或未形成" % (
                info.get("age_d"), info.get("consumers"), info.get("verify_leg")))
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
            json.dump({"generated_by": "install_ledger_reconcile.py v1.0.5",
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
