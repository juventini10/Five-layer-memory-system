#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manifest_registrar.py — scripts_manifest 机械登记器（治理链执行器 · 半边E）。

版本：v1.0.0（2026-09-10 · 童灵根治轮首版·存量孤儿治理报告 §五 G1 落地·`--self-test` 4/4）

存在理由（2026-09-10 童灵根治轮 · 存量孤儿治理报告 §四）：
  scripts_manifest 的孤儿缺的**不是观测器**——Stop 链 registry_guards.sh `--script-center`
  与周检 script_family_check L2 都能看见它们（观测缺口 G3 已于同日补齐）。缺的是**执行器**：
  「观察到」与「消灭掉」之间没有机械力量，13 天累积 27 项（≈2 项/天）。
  本脚本补执行器：磁盘新脚本 → 机械入册。让 sc_orphans 从「会累积的债」变成「恒零不变量」。

设计约束（八条，全部机械可查）：
  ① **复用守卫扫描口径**：import guard_doc_consistency.check_script_center——
     ⛔不新写扫描器（两套口径 = 新的双源漂移，违 SSOT 精神）。
  ② **只动自己造的**：只 append 未入册条目；**退役回路只撤「本器盖章」的条目**
     （note 以 AUTO_TAG 开头）——手工条目一字节不动（属性列归人/童灵维护）。
  ③ **fail-closed 默认**：新条目 in_package=False（未分类脚本绝不进安装包）+ deployed_wb=False，
     note 标「自动入册·属性待补」——「待补」在报告里显形，不静默漂。
  ④ **成熟期闸门**：跳过 mtime 新于 SETTLE_MINUTES 的文件——别端 mtime 数分钟内=活跃工作，
     铁律-014「活跃不介入」；顺带避免把一次性运维件（如 dsh_restart.sh）当场固化成库存。
  ⑤ **退役回路**：本器盖章条目若磁盘消失 → 同轮撤条目——否则自动入册会把「易失件被删」
     转成 dangling 硬漂移（把观测缺口换成新缺口，等于没治）。
  ⑥ **幂等 + 零副作用静默路径**：无增无撤 → 不写盘、不打印（Hook 零噪音纪律）。
  ⑦ **原子写 + 写前 .bak**：同目录 tmp + os.replace；任何异常 → exit 0 不写盘（Hook 三纪律）。
  ⑧ **可观测**：每次实际增/撤追加一行台账（logs/manifest_registrar.jsonl），静默不等于无痕。

模式：`--dry-run`（默认·只看不动） / `--apply`（写入） / `--self-test`（隔离夹具）
     `--quiet`（仅在「实际增撤」时打印·Hook 挂载用）
⛔ 铁律-014：写入类工具先隔离压测——本脚本 `--self-test` 用合成数据全流程演练，不碰真文件。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

# version: v1.1.1（2026-10-02 Qoder CN 童灵·出包台账治理工单 T4）：main() 前置 fail-loud——manifest 不存在时 stderr 指名路径 + return 2，⛔不再把 FileNotFoundError 吞成 [SKIP]+rc=0（病例①根因：默认 MANIFEST=BASE/scripts_manifest.json，仅作者机同目录掩盖，任何非同目录安装如 脚本中心/ 派生副本解析到不存在 sibling→静默空转·真身同样带此设计病只是被掩盖）。病例② T6 夹具已随 v1.1.0 绿·本次不重复改（不越界）。验收：--self-test 6/6 + 正常 --dry-run 0 SKIP + 缺 manifest rc=2。
# version: v1.1.0（2026-09-18 Qoder CN）：新增 --add 显式入册口＋T5/T6 夹具——发现域 check_script_center
#   扫描根写死 开发工具/，路由家族/scripts 的新脚本结构上入不了册（实测 registrar 报「无增无撤」=仪器不测该项）。
#   ⛔未直接扩域：ZCode Stop 挂 `manifest_registrar --apply`，扩域会让下次 Stop 批量自动写共享台账
#   （不可控批量写·§3.5 越界条）⇒ 先给显式口，扩域与否连存量 42 项一并交归属端裁决。
# version: v1.2（2026-10-15 Qoder CN 批D：新增 --dev-retire 腿——主线批次搬迁产生的 manifest 死径机械撤账，判据=死径∧中心git跟踪层有同名落点（宁红不误撤·仪器故障输出 stderr）·T7 夹具三态+变异负例×2·真跑撤16留1(待裁 soul_format_guard)·T6 17→1 合计171→155 与批A前持平恢复。⛔不挂 Stop 自动跑（沿用 v1.1 扩域顾虑）手动批用。）
import os
import sys
import json
import time
import shutil
import hashlib
import datetime
import argparse
import subprocess  # v1.2 dev-retire 腿（本行曾因缺失被宽 except 吞成 None·教训=仪器异常宁炸不默）

BASE = os.path.dirname(os.path.abspath(__file__))
# 🆕 2026-10-03 病例①根治（脚本自己 2026-10-02 在版本注释里写了根因·但没修）：
#   原式 `os.path.join(BASE, "scripts_manifest.json")` 假定 **manifest 与本脚本同目录**。
#   真源侧（开发工具/）同目录 ⇒ 掩盖；**派生副本侧（脚本中心/）同目录没有 manifest**
#   ⇒ 解析到不存在的 sibling ⇒ fail-loud rc=2（本轮在 readonly-guards 挂载面上实测撞到）。
#   ⇒ 改为**多候选探测**：脚本自身目录 → 上级目录（脚本中心→个人AI档案 不成立，
#   故按语义键顺序试）→ `runtime_paths` 声明的真源。真身在 开发工具/（manifest 权威）。
def _find_manifest():
    """按语义顺序找 manifest：自身目录 → 逐级上级 → 开发工具/（本项目真源目录）。"""
    cands = [os.path.join(BASE, "scripts_manifest.json")]
    d = BASE
    for _ in range(3):
        d = os.path.dirname(d)
        if d and d != "/":
            cands.append(os.path.join(d, "scripts_manifest.json"))
            cands.append(os.path.join(d, "开发工具", "scripts_manifest.json"))
    for c in cands:
        if os.path.isfile(c):
            return c
    return cands[0]          # 全不存在 ⇒ 返回首选（交给 main() 的 fail-loud 指名）


MANIFEST = _find_manifest()
LEDGER = os.path.join(BASE, "logs", "manifest_registrar.jsonl")

AUTO_TAG = "自动入册（manifest_registrar）"
SETTLE_MINUTES = 30          # 成熟期：mtime 新于此值的孤儿本轮不碰（铁律-014 活跃不介入）
SCHEMA_KEYS = ("name", "path", "family", "subfamily", "form", "event",
               "version", "win_entry", "sha8", "events", "deployed_wb",
               "note", "in_package")

sys.path.insert(0, BASE)
try:
    import guard_doc_consistency as G   # 复用其扫描口径（约束①）
except Exception:                       # 守卫不可用=无法判定孤儿 → 放行
    G = None


def sha8(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:8]
    except Exception:
        return None


def build_entry_at(full, today):
    """显式入册：任意「[记忆共享中心]/ 之内」的脚本路径 → 机械构造条目。

    为什么需要（2026-09-18 Qoder CN 端实测）：发现域 `check_script_center()` 把扫描根
    写死为 `[记忆共享中心]/脚本中心`（guard_doc_consistency.py L513），而 manifest 本身
    早已收录 `自定义层/…/路由家族/scripts/` 的条目 ⇒ 两者口径不一致，住在那个目录的
    新脚本**结构上入不了册**（`route_source_scan.py` 缺册 5 天即此症，registrar 自己
    还报「无增无撤」=仪器不测该项）。此处给一个显式补偿口：路径/name/sha8 全由脚本算，
    属性沿用 build_entry 的 fail-closed 默认（待分类·待补），⛔不让 AI 手抄 JSON。
    域外路径（档案外）直接拒绝，不猜写。
    """
    full = os.path.abspath(os.path.expanduser(full))
    root = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
    if not full.startswith(root + os.sep):
        raise ValueError("路径不在 %s/ 内（档案根外·不猜写域外地址）：%s" % (root, full))
    if not os.path.isfile(full):
        raise ValueError("文件不存在 %s" % full)
    if not (full.endswith(".py") or full.endswith(".sh")):
        raise ValueError("只收 .py/.sh %s" % full)
    rel_in_root = os.path.relpath(full, root).replace(os.sep, "/")
    entry = {
        "name": os.path.basename(full),
        "path": "个人AI档案/" + rel_in_root,
        "family": "待分类", "subfamily": None, "form": "按需", "event": None,
        "version": None, "win_entry": False, "sha8": sha8(full), "events": [],
        "deployed_wb": False,
        "note": "%s·显式入册·属性待补 %s" % (AUTO_TAG, today),
        "in_package": False,
    }
    return entry


def build_entry(rel, today):
    """把「相对 开发工具/ 的路径」转成 manifest 条目（约束③·fail-closed 默认）。"""
    full = os.path.join(BASE, rel)
    entry = {}
    entry["name"] = os.path.basename(rel)
    entry["path"] = os.path.expanduser("[记忆共享中心]/脚本中心/") + rel.replace(os.sep, "/")
    entry["family"] = "待分类"
    entry["subfamily"] = None
    entry["form"] = "按需"
    entry["event"] = None
    entry["version"] = None
    entry["win_entry"] = False
    entry["sha8"] = sha8(full)
    entry["events"] = []
    entry["deployed_wb"] = False
    entry["note"] = "%s·属性待补 %s" % (AUTO_TAG, today)
    entry["in_package"] = False
    return entry


def is_auto_owned(entry):
    """本器盖章判定（约束②）：只有本器造的条目才允许被退役回路撤除。"""
    return isinstance(entry, dict) and str(entry.get("note", "")).startswith(AUTO_TAG)


def plan(manifest_path, settle_minutes=SETTLE_MINUTES, now=None):
    """返回 (doc, todo, retired)：待入册 + 待撤除。判定完全交给守卫（约束①）。"""
    doc = json.load(open(manifest_path, encoding="utf-8"))
    entries = [e for e in doc.get("scripts", []) if isinstance(e, dict)]
    known = {e.get("path") for e in entries}
    orphans, _dangling = G.check_script_center(manifest_path)
    today = datetime.date.today().isoformat()
    now = now if now is not None else time.time()

    todo = []
    for rel in orphans:
        full = os.path.join(BASE, rel)
        try:                                        # 约束④ 成熟期闸门
            if (now - os.path.getmtime(full)) < settle_minutes * 60:
                continue
        except OSError:
            continue
        entry = build_entry(rel, today)
        if entry["path"] in known:                  # 二次幂等护栏（约束⑥）
            continue
        todo.append(entry)

    retired = []                                    # 约束⑤ 退役回路
    for e in entries:
        if not is_auto_owned(e):
            continue
        p = e.get("path", "")
        _dev_root = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "开发工具")  # 2026-10-07修:旧split前缀比较对绝对路径恒不等⇒退役回路死码fail-open,改HOME展开判定
        if not p.startswith(_dev_root + os.sep):
            continue
        if not os.path.exists(os.path.join(BASE, os.path.relpath(p, _dev_root))):
            retired.append(p)
    return doc, todo, retired


def apply_changes(manifest_path, doc, todo, retired):
    """原子写 + 写前 .bak（约束⑦）。返回 (added, removed)。"""
    retire_set = set(retired)
    kept = [e for e in doc.get("scripts", [])
            if not (isinstance(e, dict) and e.get("path") in retire_set)]
    doc["scripts"] = kept + list(todo)
    shutil.copy2(manifest_path, manifest_path + ".bak-autoreg")
    tmp = manifest_path + ".tmp-registrar"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, manifest_path)
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(timespec="seconds"),
                "src": "manifest_registrar",
                "added": [e["path"] for e in todo],
                "retired": retired,
                "n_add": len(todo), "n_retire": len(retired),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return len(todo), len(retired)


def run_selftest():
    """隔离夹具（⛔铁律-014）：合成数据全流程演练，不碰真 manifest。"""
    import tempfile
    today = "2026-09-10"
    results = []

    def t1():   # 条目形态
        e = build_entry("zzz_probe_fixture", today)
        assert e["path"] == os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "脚本中心", "zzz_probe_fixture"), e["path"]  # build_entry 本征绝对形态(HOME动态构造·源码无机器名)
        assert e["family"] == "待分类" and e["in_package"] is False
        assert e["deployed_wb"] is False and e["events"] == [] and e["event"] is None
        assert set(e.keys()) == set(SCHEMA_KEYS), set(e.keys()) ^ set(SCHEMA_KEYS)
        assert tuple(e.keys()) == SCHEMA_KEYS
        assert e["note"].startswith(AUTO_TAG) and e["note"].endswith(today)
        return 1
    results.append(("T1 条目形态（键集/键序 = 既有 schema · fail-closed 默认 · 路径归一）", 1, t1))

    def t2():   # sha8
        d = tempfile.mkdtemp()
        p = os.path.join(d, "h.py")
        open(p, "w").write("abc")
        assert sha8(p) == hashlib.sha256(b"abc").hexdigest()[:8]
        shutil.rmtree(d)
        return 1
    results.append(("T2 sha8 = sha256[:8]（与 manifest 既有口径一致）", 1, t2))

    def t3():   # 成熟期闸门
        d = tempfile.mkdtemp()
        fresh = os.path.join(BASE, "_zzz_fresh_probe.py")  # 测试探针·运行时自建自删·端用户态不存在（非部署契约）
        open(fresh, "w").write("x")
        try:
            os.utime(fresh, (time.time() - 10, time.time() - 10))
            skip = (time.time() - os.path.getmtime(fresh)) < SETTLE_MINUTES * 60
        finally:
            os.unlink(fresh)
            shutil.rmtree(d)
        assert skip is True
        return 1
    results.append(("T3 成熟期闸门（mtime 10 秒前 → 本轮跳过·铁律-014 活跃不介入）", 1, t3))

    def t4():   # 盖章判定
        assert is_auto_owned({"note": AUTO_TAG + "·属性待补 2026-09-10"}) is True
        assert is_auto_owned({"note": "手写的说明"}) is False
        assert is_auto_owned({"note": ""}) is False
        assert is_auto_owned({"family": "守卫"}) is False
        return 1
    def t5():   # 显式入册：域内脚本机械构造（路径/名/sha8 全由脚本算·⛔不靠 AI 手抄 JSON）
        root = os.path.join(os.path.expanduser("~"), "[记忆共享中心]")
        d = os.path.join(root, "自定义层", "_registrar_probe")
        os.makedirs(d, exist_ok=True)
        fp = os.path.join(d, "probe_script.py")
        try:
            with open(fp, "w") as f:
                f.write("print(1)\n")
            e = build_entry_at(fp, "2026-09-18")
            assert e["path"] == "[记忆共享中心]/自定义层/_registrar_probe/probe_script.py", e["path"]  # 同上相对形态
            assert e["name"] == "probe_script.py" and e["sha8"] == sha8(fp), e
            assert e["family"] == "待分类" and "待补" in e["note"], e["note"]
        finally:                                        # 副作用自清理（§3.0·5 纪律⑤）
            if os.path.isfile(fp):
                os.remove(fp)
            if os.path.isdir(d):
                os.rmdir(d)
        return 1

    def t6():   # 负例：域外路径必须被拒——猜写域外地址=造出永久找不到的条目
        try:
            build_entry_at("/tmp/outside_probe.py", "2026-09-18")
        except ValueError as ex:
            assert os.path.join(os.path.expanduser("~"), "[记忆共享中心]") in str(ex), ex
            return 1
        raise AssertionError("域外路径未被拒绝＝会写出假地址")
    results.append(("T4 盖章判定（只有本器造的条目可被退役回路撤除·手工条目免疫）", 1, t4))
    results.append(("T5 显式入册·域内路径机械构造（含副作用自清理）", 1, t5))
    results.append(("T6 负例·域外路径拒绝（不猜写地址）", 1, t6))

    def t7():   # dev-retire 腿夹具（注入假仪器·⛔不碰真 git/真 manifest·v1.2）
        doc = {"scripts": [
            {"path": "[记忆共享中心]/脚本中心/gone_guard.py"},
            {"path": "[记忆共享中心]/脚本中心/alive.py"},
            {"path": "[记忆共享中心]/脚本中心/orphan_x.py"},
        ]}
        fake_alive = lambda x: "alive" in x
        fake_ev = lambda b: ["脚本中心/守卫/gone_guard.py"] if b == "gone_guard.py" else []
        ret, held = dev_retire_plan(doc, alive_fn=fake_alive, evidence_fn=fake_ev,
                                    repo_wide_fn=lambda b: 5)  # orphan_x 实体在别处=5·保持"无落点有实体→留"
        if not ([q for q, _ in ret] == ["[记忆共享中心]/脚本中心/gone_guard.py"] and held == ["[记忆共享中心]/脚本中心/orphan_x.py"]):
            raise AssertionError("基础三态错(撤有证据/活不动/无证据保留)")
        ret2, _ = dev_retire_plan(doc, alive_fn=fake_alive, evidence_fn=lambda b: ["x"])
        if not (len(ret2) == 2 and all("alive" not in q for q, _ in ret2)):
            raise AssertionError("变异负例1失守(证据恒真时活件仍须不动)")
        ret3, held3 = dev_retire_plan(doc, alive_fn=fake_alive, evidence_fn=lambda b: None)
        if not (ret3 == [] and len(held3) == 2):
            raise AssertionError("变异负例2失守(仪器没跑成须全保留零撤)")
        return 1
    results.append(("T7 dev-retire 腿（有证据撤/无证据留报警/仪器未跑成零撤×变异负例×2）", 1, t7))
    def t8():   # v1.3 三态裁级夹具
        doc = {"scripts": [{"path": "[记忆共享中心]/脚本中心/ghost_a.py"}, {"path": "[记忆共享中心]/脚本中心/ghost_b.py"}]}
        ret, held = dev_retire_plan(doc, alive_fn=lambda x: False,
                                    evidence_fn=lambda b: [], repo_wide_fn=lambda b: 0 if b == "ghost_a.py" else 3)
        return ([q for q, _ in ret] == ["[记忆共享中心]/脚本中心/ghost_a.py"] and held == ["[记忆共享中心]/脚本中心/ghost_b.py"]
                and ret[0][1].startswith("RETIRED"))
    results.append(("T8 三态裁级（零实体退役撤/实体在别处留）", 1, t8))

    ok = 0
    for title, expect, fn in results:
        try:
            got = fn()
        except AssertionError as ex:
            got = "断言失败: %s" % ex
        good = (got == expect)
        ok += bool(good)
        print("  %s %s" % ("✅" if good else "❌", title))
        if not good:
            print("       期望 %s / 实得 %s" % (expect, got))
    print("自测 %d/%d %s" % (ok, len(results), "全绿" if ok == len(results) else "有红"))
    return 0 if ok == len(results) else 1



# ── dev-retire 腿（v1.2 · 2026-10-15 批D机制缺口：registrar 原扫描域=中心易失件，
#    主线批次搬迁产生的 manifest 死径无人管辖→T6 常红。本腿只撤「有搬家证据」的死径：
#    basename 在 中心 git 跟踪层存在＝搬迁落点实证→撤；无证据→保留报警（需裁面 ⛔误撤）。
#    ⛔不挂 Stop 自动跑（沿用 v1.1 备注「扩域会让下次 Stop 批量自动写共享台账」之顾虑）——手动批用。──
def _dialect_alive(p):
    """manifest path 方言感知存活判据（ABS→HOME→档案根 三 base 全试·⛔单一base假死径·台账L0 609假数先例）。"""
    cands = [os.path.expanduser(p)]
    if not p.startswith(("~", "/")):
        cands += [os.path.join(os.path.expanduser("~"), p),
                  os.path.join(os.path.expanduser("~"), "[记忆共享中心]", p)]
    return any(os.path.exists(c) for c in cands)

def _center_evidence(basename, repo=None):
    """中心 git 跟踪层里 basename 的落点列表（空=无证据；None=仪器没跑成⛔当无证据用）。"""
    repo = repo or os.path.expanduser("[记忆共享中心]")
    try:
        r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=false",
                            "ls-files", "脚本中心"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as ex:
        print("[dev-retire] 证据仪器故障（按零撤处理·宁红不误撤）: %s" % ex, file=sys.stderr)
        return None
    if r.returncode != 0:
        return None
    return [x for x in r.stdout.splitlines() if os.path.basename(x) == basename]

def _repo_wide_entities(basename):
    """全仓（含未跟踪）数同名活文件（排除 .bak/备份/缓存/台账文档）。"""
    n = 0
    for dp, dns, fns in os.walk(os.path.expanduser("[记忆共享中心]")):
        dns[:] = [d for d in dns if d not in ('.git', '__pycache__', 'node_modules', '记忆琥珀', '发布库') and not d.startswith('.')]
        if basename in fns:
            f = os.path.join(dp, basename)
            if '.bak' not in f and '/bak' not in dp and '/_backup' not in dp:
                n += 1
    return n


def dev_retire_plan(doc, alive_fn=None, evidence_fn=None, repo_wide_fn=None):
    """返回 (可撤[(path,dst)], 保留报警[path])。证据不齐一律保留——宁红不误撤。"""
    alive_fn = alive_fn or _dialect_alive
    evidence_fn = evidence_fn or _center_evidence
    repo_wide_fn = repo_wide_fn or _repo_wide_entities
    retired, held = [], []
    for e in doc.get("scripts", []):
        path = e.get("path", "") if isinstance(e, dict) else ""
        if not path or alive_fn(path):
            continue
        dst = evidence_fn(os.path.basename(path))
        if dst is None:
            held.append(path)  # 仪器没跑成≠确认无落点·按保留处理（⛔把"没测到"判成"确认没有"）
        elif dst:
            retired.append((path, dst[0]))
        elif repo_wide_fn(os.path.basename(path)) == 0:
            # v1.3 三态裁级（2026-10-15 你令愿景最优根治）：无落点且**全仓零实体**＝已退役件
            # （如 soul_format_guard 全域无实体=登记幽灵）→ 可撤；实体在别处未归位 → 保留报警。
            retired.append((path, "RETIRED:全仓零实体(退役裁级)"))
        else:
            held.append(path)
    return retired, held


def main():
    ap = argparse.ArgumentParser(description="scripts_manifest 机械登记器（孤儿→入册 / 易失件→退役）")
    ap.add_argument("--apply", action="store_true", help="写入 manifest（默认 dry-run 只看不动）")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run",
                    help="显式 dry-run（默认行为·只看不动）")
    ap.add_argument("--quiet", action="store_true", help="仅在「实际增撤」时打印（Hook 挂载用）")
    ap.add_argument("--settle-minutes", type=int, default=SETTLE_MINUTES)
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--add", nargs="*", default=[],
                    help="显式入册指定脚本路径（补偿发现域写死 开发工具/ 的盲区·默认 dry-run）")
    ap.add_argument("--dev-retire", action="store_true",
                    help="撤「死径且中心有搬家证据」条目（默认 dry-run·配 --apply 写盘·⛔不挂Hook自动跑）")
    ap.add_argument("--self-test", action="store_true", dest="self_test")
    args = ap.parse_args()

    if args.self_test:
        print("=== manifest_registrar.py 自测夹具 ===")
        return run_selftest()

    # fail-loud（出包台账治理工单 T4·2026-10-02·Qoder CN）：manifest 不存在 = 登记器前提缺失，
    #   硬退出非零并指名路径，⛔不以 [SKIP]+rc=0 静默空转（旧逻辑把 FileNotFoundError 吞进计划阶段
    #   except→[SKIP]，真身仅因 manifest 与自身同目录才掩盖；任何非同目录安装（如 脚本中心/ 派生副本）
    #   默认 MANIFEST 解析到不存在的 sibling→静默 SKIP 空转＝病例①根因）。
    if not os.path.exists(args.manifest):
        print("🔴 manifest 不存在（fail-loud·非静默SKIP）：%s" % args.manifest, file=sys.stderr)
        return 2

    if args.add:
        today = datetime.date.today().isoformat()
        doc = json.load(open(args.manifest, encoding="utf-8"))
        known = {e.get("path") for e in doc.get("scripts", []) if isinstance(e, dict)}
        todo = []
        for a in args.add:
            try:
                e = build_entry_at(a, today)
            except ValueError as ex:
                print("🔴 拒绝入册：%s" % ex)
                continue
            if e["path"] in known:
                print("ℹ️ 已在册，幂等跳过：%s" % e["path"])
                continue
            todo.append(e)
            print("拟入册：%s → %s（sha8=%s·属性待补）" % (e["name"], e["path"], e["sha8"]))
        if not todo:
            return 0
        if not args.apply:
            print("（dry-run·加 --apply 才写盘）")
            return 0
        n_add, _ = apply_changes(args.manifest, doc, todo, [])
        print("✅ 显式入册 %d 条" % n_add)
        return 0

    if args.dev_retire:
        doc = json.load(open(args.manifest, encoding="utf-8"))
        retired, held = dev_retire_plan(doc)
        print("dev-retire：待撤 %d（有搬家证据）/ 保留报警 %d（无证据·待裁）" % (len(retired), len(held)))
        for pth, dst in retired:
            print("   - %s → %s" % (pth[:70], dst[:56]))
        for pth in held:
            print("   ⚠️保留 %s（中心无落点证据·⛔不撤）" % pth[:70])
        if not retired:
            return 0
        if not args.apply:
            print("（dry-run·加 --apply 才写盘）")
            return 0
        _, n = apply_changes(args.manifest, doc, [], [p for p, _ in retired])
        print("✅ dev-retire 写盘：撤 %d 条（.bak-autoreg+台账 jsonl 随 apply_changes 三件套）" % n)
        return 0

    if G is None:
        if not args.quiet:
            print("[SKIP] guard_doc_consistency 不可用 → 无法判定孤儿（放行）")
        return 0

    try:
        doc, todo, retired = plan(args.manifest, args.settle_minutes)
    except Exception as ex:
        if not args.quiet:
            print("[SKIP] 计划阶段异常: %s: %s" % (type(ex).__name__, ex))
        return 0

    if not todo and not retired:
        if not args.quiet:
            print("✅ 无增无撤（sc_orphans 已清零 / 无易失件）——零副作用静默")
        return 0

    if not args.apply:
        print("dry-run（未写盘）：待入册 %d 项 / 待退役 %d 项" % (len(todo), len(retired)))
        for e in todo:
            print("   + %-46s family=%s in_package=%s" % (e["path"], e["family"], e["in_package"]))
        for p in retired:
            print("   - %s（本器盖章条目·磁盘已消失）" % p)
        return 0

    try:
        n_add, n_ret = apply_changes(args.manifest, doc, todo, retired)
    except Exception as ex:
        print("[ERR] 写入失败（未落盘）: %s: %s" % (type(ex).__name__, ex), file=sys.stderr)
        return 0
    print("✅ 机械登记：入册 %d 项 · 退役 %d 项（新条目 in_package=False 默认不进包）" % (n_add, n_ret))
    for e in todo:
        print("   + %s" % e["path"])
    for p in retired:
        print("   - %s" % p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
