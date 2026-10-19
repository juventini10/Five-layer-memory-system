#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
growth_signal_collector.py — 成长箱感知层采集器（Phase 1 感知自主化 · 步骤1.1·v1.1.0·Phase 4增 S1/S3 源）

定位（方案：[记忆共享中心]/自定义层/待完成工作/成长箱升级/phase1-design.md）：
  把成长箱学习信号入口从「人说触发词」扩展为「系统自动感知」——
  每日扫描已有基础设施的输出（零新建信号源），按高门槛白名单生成候选学习项，
  写入候选暂存区 CANDIDATES.md，由人/童灵审核（终审保留·愿景红线）。

信号源（v1.0 接入两源·S825 最小闭环；现行为四源 S2+S6+S1+S3，v4.0.1 起·见 SKILL.md 启动自检段，本行为历史注）：
  S2 免疫复发记录.md —— 某坑复发 = 规则未生效/新问题（近24h产出·7天同信号≥门槛才立候选）
  S6 changelog_guard.sh --check JSON —— 版本漂移/漏记 = 流程执行缺口（候选数≥3=严重度高立候选，1-2需7天复现）

质量门禁（phase1-design §六·Poka-Yoke）：
  G1 高门槛白名单：默认静默，仅"同信号≥门槛次/7天"或"严重度=高"才立候选
  G2 去重：同指纹 ⏳待审 / ❌已拒 不再立候选；✅已入账的 7 天内不重复立
  G3 每日上限：单日最多 5 条（超限按严重度+复现次数排序截断）
  G4 人/童灵终审：候选≠记录；本脚本⛔不写 learnings/ERRORS（终审红线）
  G5 反馈调阈：拒绝率>50%收紧(+1)/<10%放宽(-1)，7天最多一次，范围[2,4]

通用性约束（phase1-design §四.一·皮叔确认）：
  纯 Python 3 标准库零第三方依赖；端无关（只读 [记忆共享中心]/ 共享文件）；
  任何端可 `python3 本脚本` 直接跑；运行时状态落持久目录（守卫编写规范 §3.0·6 ⛔不落 /tmp）。

用法：
  python3 growth_signal_collector.py              # 采集一次（默认）
  python3 growth_signal_collector.py --check      # 健康检查 JSON（含 alarm 字段·守卫家族接口约定）
  python3 growth_signal_collector.py --self-test  # 自测（夹具自清理·幂等）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta

VERSION = "1.1.0"

HOME = os.path.expanduser("~")
BASE = os.path.expanduser("[记忆共享中心]")
STAGING = os.path.join(BASE, "成长箱", "learnings", "CANDIDATES.md")
STATE = os.path.join(BASE, "成长箱", "learnings", "growth_signal_collector_state.json")
RECURRENCE = os.path.join(BASE, "成长箱", "免疫复发记录.md")
def _first_existing(*cands):
    """C1 路径归一（2026-09-20·群友问题6 根治）：作者侧"开发工具/"布局与用户侧"脚本中心/"落点
    双形态候选——首个存在者胜，全缺返回首候选（调用方以 isfile 显式降级，不静默空转）。"""
    for c in cands:
        if os.path.isfile(c):
            return c
    return cands[0]

GUARD = _first_existing(
    os.path.join(BASE, "脚本中心", "守卫", "changelog-guard", "changelog_guard.sh"),
    os.path.join(BASE, "脚本中心", "changelog_guard.sh"),
    os.path.join(BASE, "技能配置", "growth-box", "scripts", "changelog_guard.sh"),
    os.path.join(BASE, "开发工具", "changelog-guard", "changelog_guard.sh"),
)
GUARD_SELFTEST = _first_existing(
    os.path.join(BASE, "脚本中心", "守卫", "guard_selftest_check.py"),
    os.path.join(BASE, "脚本中心", "guard_selftest_check.py"),
    os.path.join(BASE, "技能配置", "growth-box", "scripts", "guard_selftest_check.py"),
    os.path.join(BASE, "开发工具", "guard_selftest_check.py"),
)
EVAL_RESULTS = os.path.join(BASE, "评估知识库", "test_results")

DEFAULT_THRESHOLD = 2
THRESHOLD_MIN, THRESHOLD_MAX = 2, 4
DAILY_CAP = 5
SEV_RANK = {"high": 0, "medium": 1, "low": 2}

STAGING_HEADER = """# 成长箱 · 候选学习项暂存区（Phase 1 感知自主化）

> 由 `growth_signal_collector.py` 自动写入·人/童灵审核（终审保留）。
> ⛔DO NOT 跳过审核直接写入 learnings/ERRORS——候选≠记录（愿景红线·G4）。
> 审核方式：把「状态」改为 ✅已入账 / ❌已拒（噪声），并填「审核结论」一句理由；
> ✅ 的走成长箱流程A（错误）/流程E（经验）正常入口，❌ 的理由会反馈采集器调阈值。

## 采集器状态
- 同信号门槛：{threshold}
- 上次调阈：—
- 反馈规则：拒绝率>50%收紧(+1)/<10%放宽(-1)·7天最多一次·范围2-4
- 采集器版本：v{version}

## 候选清单
"""

# ---------- 通用工具 ----------

def _read(path, limit=4_000_000):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except OSError:
        return ""


def _fingerprint(source, key):
    raw = (source + "||" + key.strip()).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def _write_state(payload):
    try:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    except OSError as exc:
        # 显式降级不静默：状态文件写失败不影响主流程，但要留痕
        sys.stderr.write("growth_signal_collector: 状态文件写入失败 %s\n" % exc)


# ---------- S2 免疫复发记录 ----------

REC_LINE_RE = re.compile(
    r"^\s*-\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*\|\s*([^|]+?)\s*\|\s*(.+)$"
)


def parse_recurrence(text, today, window_days=7):
    """解析免疫复发记录。

    返回 (fresh_hits, count7, parse_errors)：
      fresh_hits   = 近24h命中的坑名列表（信号=最近产出）
      count7       = {坑名: 7天窗口内命中次数}（G1 门槛判据）
      parse_errors = 无法解析的行数（显式降级不静默）
    """
    fresh_hits, count7, parse_errors = [], {}, 0
    window_start = today - timedelta(days=window_days - 1)
    yesterday = today - timedelta(days=1)
    for line in text.splitlines():
        if not line.strip().startswith("- "):
            continue
        m = REC_LINE_RE.match(line)
        if not m:
            parse_errors += 1
            continue
        d_s, _t_s, status, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            d = datetime.strptime(d_s, "%Y-%m-%d").date()
        except ValueError:
            parse_errors += 1
            continue
        if "命中" not in status:
            continue  # 非命中行（观察/退役等）不属信号
        if " | 来源: " in rest:
            body = rest.rsplit(" | 来源: ", 1)[0]
        else:
            body = rest
        pit = body.split(" | ")[0].strip() if " | " in body else body.strip()
        if not pit:
            parse_errors += 1
            continue
        if window_start <= d <= today:
            count7[pit] = count7.get(pit, 0) + 1
        if d >= yesterday:
            fresh_hits.append(pit)
    return fresh_hits, count7, parse_errors


# ---------- S6 changelog guard ----------

def run_changelog_guard():
    """跑 changelog_guard.sh --check，返回 JSON dict；失败显式返回 error 字段。"""
    if not os.path.isfile(GUARD):
        return {"error": "guard-missing: %s" % GUARD}
    try:
        out = subprocess.run(
            ["bash", GUARD, "--check"], capture_output=True, text=True, timeout=120
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"error": "guard-run-failed: %s" % exc}
    try:
        return json.loads(out.stdout.strip() or "{}")
    except ValueError:
        return {"error": "guard-output-unparseable: %s" % out.stdout[:120]}


# ---------- 暂存区读写 ----------

HEADER_THRESHOLD_RE = re.compile(r"^- 同信号门槛：(\d+)\s*$", re.M)
HEADER_ADJUST_RE = re.compile(r"^- 上次调阈：(\d{4}-\d{2}-\d{2})|^- 上次调阈：—\s*$")
CAND_HEAD_RE = re.compile(r"^### \[CAND-(\d{8})-(\d+)\]\s*(.+)$", re.M)


def ensure_staging(threshold):
    """暂存区不存在则初始化（含头部门槛字段）。"""
    if not os.path.isfile(STAGING):
        os.makedirs(os.path.dirname(STAGING), exist_ok=True)
        with open(STAGING, "w", encoding="utf-8") as f:
            f.write(STAGING_HEADER.format(threshold=threshold, version=VERSION))
    return STAGING


def load_staging():
    """解析暂存区：返回 (entries, threshold, last_adjust)。

    entries: [{id, fingerprint, source, title, status, first_seen}]
    解析失败/文件缺失 → 显式降级：返回 ([] , DEFAULT_THRESHOLD, None) 并由调用方留痕。
    """
    text = _read(STAGING)
    if not text:
        return [], DEFAULT_THRESHOLD, None
    m = HEADER_THRESHOLD_RE.search(text)
    threshold = int(m.group(1)) if m else DEFAULT_THRESHOLD
    adj = None
    ma = re.search(r"^- 上次调阈：(\d{4}-\d{2}-\d{2})", text, re.M)
    if ma:
        try:
            adj = datetime.strptime(ma.group(1), "%Y-%m-%d").date()
        except ValueError:
            adj = None
    entries = []
    blocks = re.split(r"(?=^### \[CAND-)", text, flags=re.M)
    for b in blocks:
        hm = re.match(r"### \[CAND-(\d{8})-(\d+)\]\s*(.+)", b)
        if not hm:
            continue
        fp = re.search(r"\*\*指纹\*\*：([0-9a-f]{16})", b)
        src = re.search(r"\*\*来源信号\*\*：\s*(S\d)", b)
        st = re.search(r"\*\*状态\*\*：\s*([⏳✅❌])", b)
        fs = re.search(r"\*\*首次发现\*\*：(\d{4}-\d{2}-\d{2})", b)
        entries.append({
            "id": "CAND-%s-%s" % (hm.group(1), hm.group(2)),
            "date": hm.group(1),
            "title": hm.group(2).strip(),
            "fingerprint": fp.group(1) if fp else "",
            "source": src.group(1) if src else "",
            "status": st.group(1) if st else "⏳",
            "first_seen": fs.group(1) if fs else "%s-%s-%s" % (hm.group(1)[:4], hm.group(1)[4:6], hm.group(1)[6:]),
        })
    return entries, threshold, adj


def next_seq(entries, today_s):
    """当日候选序号续位（幂等：同日重跑不撞号）。"""
    seq = 0
    for e in entries:
        if e["date"] == today_s:
            try:
                seq = max(seq, int(e["id"].rsplit("-", 1)[1]))
            except (IndexError, ValueError):
                pass
    return seq + 1


def adjust_threshold(entries, threshold, last_adjust, today):
    """G5 反馈调阈：拒绝率驱动，7天最多一次，范围[2,4]。"""
    reviewed = [e for e in entries if e["status"] in ("✅", "❌")]
    if len(reviewed) < 3:
        return threshold, last_adjust, "样本不足未调阈（已审核%d条）" % len(reviewed)
    if last_adjust and (today - last_adjust).days < 7:
        return threshold, last_adjust, "7天内已调过不再调"
    rejected = sum(1 for e in reviewed if e["status"] == "❌")
    rate = rejected / float(len(reviewed))
    if rate > 0.5 and threshold < THRESHOLD_MAX:
        return threshold + 1, today, "拒绝率%.0f%%>50%% 收紧门槛→%d" % (rate * 100, threshold + 1)
    if rate < 0.1 and threshold > THRESHOLD_MIN:
        return threshold - 1, today, "拒绝率%.0f%%<10%% 放宽门槛→%d" % (rate * 100, threshold - 1)
    return threshold, last_adjust, "拒绝率%.0f%% 在合理区间维持%d" % (rate * 100, threshold)


# ---------- 采集主流程 ----------

def collect(today=None, verbose=False):
    today = today or date.today()
    today_s = today.strftime("%Y-%m-%d")
    sources_health = {}

    # --- 暂存区（不存在则初始化）---
    ensure_staging(DEFAULT_THRESHOLD)
    entries, threshold, last_adjust = load_staging()
    if entries == [] and not _read(STAGING):
        sources_health["staging"] = "missing-or-unparseable（已重建）"
        ensure_staging(DEFAULT_THRESHOLD)
        entries, threshold, last_adjust = load_staging()

    dedup_pending = {e["fingerprint"] for e in entries if e["status"] == "⏳"}
    dedup_rejected = {e["fingerprint"] for e in entries if e["status"] == "❌"}
    recent_ok = {}
    for e in entries:
        if e["status"] == "✅":
            recent_ok.setdefault(e["fingerprint"], []).append(e["first_seen"])

    proposals = []  # [{source, key, title, strength, severity, detail}]

    # --- S2 免疫复发记录 ---
    rec_text = _read(RECURRENCE)
    if not rec_text:
        sources_health["S2"] = "missing: %s（显式降级·本轮无S2信号）" % RECURRENCE
        fresh, count7, parse_errors = [], {}, 0
    else:
        fresh, count7, parse_errors = parse_recurrence(rec_text, today)
        sources_health["S2"] = "ok fresh=%d parse_errors=%d" % (len(set(fresh)), parse_errors)
    seen_fresh = []
    for pit in fresh:
        if pit in seen_fresh:
            continue
        seen_fresh.append(pit)
        c7 = count7.get(pit, 0)
        if c7 < threshold:
            continue  # G1 高门槛：同信号7天内不足门槛次→不立候选
        sev = "high" if c7 >= 5 else "medium"
        proposals.append({
            "source": "S2", "key": pit,
            "title": "免疫坑复发：%(pit)s" % {"pit": pit[:80]},
            "strength": "重复%d次/7天" % c7, "severity": sev,
            "detail": RECURRENCE,
        })

    # --- S6 changelog guard ---
    guard = run_changelog_guard()
    if "error" in guard:
        sources_health["S6"] = guard["error"] + "（显式降级·本轮无S6信号）"
    else:
        c = int(guard.get("candidates", 0))
        alarm = bool(guard.get("alarm", False))
        hist7 = sum(
            1 for e in entries
            if e["source"] == "S6"
            and (today - datetime.strptime(e["first_seen"], "%Y-%m-%d").date()).days < 7
        )
        sev = "high" if c >= 3 else "medium"
        gated = c >= 3 or (hist7 + 1) >= threshold
        sources_health["S6"] = "ok candidates=%d alarm=%s hist7=%d gated=%s" % (c, alarm, hist7, gated)
        if alarm and c > 0 and gated:
            proposals.append({
                "source": "S6", "key": "changelog-unrecorded",
                "title": "changelog 未记账文件 %d 个（版本漂移/漏记·流程执行缺口）" % c,
                "strength": "%d个未记账" % c + ("/严重度高" if c >= 3 else "/7天复现第%d次" % (hist7 + 1)),
                "severity": sev,
                "detail": "bash 脚本中心/changelog_guard.sh --report（或技能包同伴路径·随安装落点）",
            })

    # --- S1 守卫自测聚合器（Phase 4·守卫域健康缺口）---
    if not os.path.isfile(GUARD_SELFTEST):
        sources_health["S1"] = "missing: %s（显式降级·本轮无S1信号）" % GUARD_SELFTEST
    else:
        try:
            r = subprocess.run(["python3", GUARD_SELFTEST, "--strict"],
                               capture_output=True, text=True, timeout=900)  # v-s7 2026-10-10: 聚合器v0.3.2扩容后全量5:27>300s，防超时降级成新静默失效
            red = r.returncode != 0
            sources_health["S1"] = "ok strict_rc=%d（0=全绿·1=有红项）" % r.returncode
            if red:
                sev = "high"  # 守卫域红项=检查网有洞=高严重度（G1高通道）
                proposals.append({
                    "source": "S1", "key": "guard-selftest-red",
                    "title": "守卫自测聚合器有红项（守卫域检查网缺口·%d项待修）" % 1,
                    "strength": "strict模式exit 1",
                    "severity": sev,
                    "detail": "python3 脚本中心/guard_selftest_check.py（重跑看红项清单·随安装落点）",
                })
        except subprocess.TimeoutExpired:
            sources_health["S1"] = "timeout 300s（显式降级·本轮无S1信号）"
        except OSError as exc:
            sources_health["S1"] = "run-failed: %s（显式降级）" % exc

    # --- S3 评估报告新鲜度（Phase 4·评估域工作信号·低严重度）---
    if not os.path.isdir(EVAL_RESULTS):
        sources_health["S3"] = "missing: %s（显式降级）" % EVAL_RESULTS
    else:
        fresh_evals = []
        cutoff = datetime.combine(today, datetime.min.time()) - timedelta(hours=24)
        try:
            for name in os.listdir(EVAL_RESULTS):
                if not name.endswith(".md") or name.startswith("."):
                    continue
                p = os.path.join(EVAL_RESULTS, name)
                try:
                    mt = datetime.fromtimestamp(os.path.getmtime(p))
                except OSError:
                    continue
                if mt >= cutoff:
                    fresh_evals.append(name)
        except OSError as exc:
            sources_health["S3"] = "list-failed: %s（显式降级）" % exc
        fresh_evals.sort()
        sources_health["S3"] = "ok fresh24h=%d" % len(fresh_evals)
        if fresh_evals:
            proposals.append({
                "source": "S3", "key": "eval-fresh:" + ",".join(fresh_evals[:3]),
                "title": "评估域24h新报告 %d 份（评估发现反复问题=晋升候选素材）" % len(fresh_evals),
                "strength": "%d份新鲜报告" % len(fresh_evals),
                "severity": "low",
                "detail": "评估知识库/test_results/: " + " · ".join(fresh_evals[:3]),
            })

    # --- G2 去重 ---
    new_ones = []
    for p in proposals:
        fp = _fingerprint(p["source"], p["key"])
        p["fingerprint"] = fp
        if fp in dedup_pending:
            continue  # 同信号已在待审
        if fp in dedup_rejected:
            continue  # 已判噪声
        ok_dates = [d for d in recent_ok.get(fp, [])]
        if ok_dates and min(
            (today - datetime.strptime(d, "%Y-%m-%d").date()).days for d in ok_dates
        ) < 7:
            continue  # ✅后7天内不重复立（防入账后噪声回灌）
        if any(e["fingerprint"] == fp and e["date"] == today.strftime("%Y%m%d") for e in entries):
            continue  # 今日已立（幂等）
        new_ones.append(p)

    # --- G3 每日上限：当日累计（含历史写入）不超过 DAILY_CAP，严重度→复现强度排序截断 ---
    existing_today = sum(1 for e in entries if e["date"] == today.strftime("%Y%m%d"))
    quota = max(0, DAILY_CAP - existing_today)
    new_ones.sort(key=lambda p: (SEV_RANK.get(p["severity"], 9), p["strength"]), )
    truncated = new_ones[quota:]
    new_ones = new_ones[:quota]

    # --- 写入暂存区（追加·幂等）---
    if new_ones:
        seq = next_seq(entries, today.strftime("%Y%m%d"))
        lines = ["\n"]
        for i, p in enumerate(new_ones):
            cand_id = "CAND-%s-%03d" % (today.strftime("%Y%m%d"), seq + i)
            lines.append("### [%s] %s" % (cand_id, p["title"]))
            lines.append("- **来源信号**：%s · %s" % (p["source"], p["detail"]))
            lines.append("- **信号强度**：%s" % p["strength"])
            lines.append("- **建议分类**：%s" % ("错误型" if p["source"] == "S2" else "流程缺口型"))
            lines.append("- **建议处置**：记入Flow A（审核后按现有流程走）")
            lines.append("- **首次发现**：%s" % today_s)
            lines.append("- **累计出现**：%s" % p["strength"])
            lines.append("- **指纹**：%s" % p["fingerprint"])
            lines.append("- **状态**：⏳待审")
            lines.append("- **审核结论**：\n")
        with open(STAGING, "a", encoding="utf-8") as f:
            f.write("\n".join(lines).rstrip("\n") + "\n")

    # --- G5 反馈调阈（写回头部·按行替换防丢段·指令编写规范§1.5）---
    new_threshold, new_adjust, adjust_note = adjust_threshold(entries, threshold, last_adjust, today)
    if new_threshold != threshold:
        text = _read(STAGING)
        text = re.sub(
            r"^- 同信号门槛：\d+\s*$",
            "- 同信号门槛：%d" % new_threshold, text, count=1, flags=re.M,
        )
        text = re.sub(
            r"^- 上次调阈：.*$",
            "- 上次调阈：%s（%s）" % (today_s, adjust_note), text, count=1, flags=re.M,
        )
        with open(STAGING, "w", encoding="utf-8") as f:
            f.write(text)

    # --- 运行时状态落盘（持久目录·§3.0·6）---
    pending = sum(1 for e in load_staging()[0] if e["status"] == "⏳")
    _write_state({
        "version": VERSION,
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "today": today_s,
        "threshold": new_threshold,
        "threshold_note": adjust_note,
        "candidates_added": len(new_ones),
        "truncated": len(truncated),
        "pending_total": pending,
        "sources": sources_health,
    })

    if new_ones:
        print("growth_signal_collector: 新增%d条候选（pending=%d，门槛=%d）" % (len(new_ones), pending, new_threshold))
        for p in new_ones:
            print("  + [%s][%s] %s" % (p["source"], p["severity"], p["title"]))
    else:
        print("growth_signal_collector: 无新候选（S2 fresh=%d·S6 见状态；门槛=%d）" % (
            len(set(fresh)) if rec_text else 0, new_threshold))
    if truncated:
        print("growth_signal_collector: 超每日上限截断%d条（G3）" % len(truncated))
    return 0


# ---------- 健康检查 ----------

def health_check():
    entries, threshold, _ = load_staging()
    state = {}
    try:
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}
    rec_exists = os.path.isfile(RECURRENCE)
    guard_exists = os.path.isfile(GUARD)
    pending = sum(1 for e in entries if e["status"] == "⏳")
    out = {
        "version": VERSION,
        "staging": STAGING,
        "staging_entries": len(entries),
        "pending": pending,
        "threshold": threshold,
        "last_run": state.get("last_run", ""),
        "last_run_sources": state.get("sources", {}),
        "S2_recurrence_file": rec_exists,
        "S6_guard_file": guard_exists,
        "alarm": pending > 0,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


# ---------- 自测（守卫编写规范 §3.0·5：夹具幂等自清理）----------

def self_test():
    failures = []
    tmp = tempfile.mkdtemp(prefix="gsc_selftest_")
    try:
        today = date(2026, 9, 16)

        # T1 解析：同坑7天2次→进count7；坑A在7天外→不计；坏行→parse_errors
        lines = [
            "- 2026-09-15 23:39 | 🔴命中 | 坑甲 | cmd1 | 来源: 规范反哺日志.md",
            "- 2026-09-15 23:42 | 🔴命中 | 坑甲 | cmd2 | 来源: 规范反哺日志.md",
            "- 2026-09-01 10:00 | 🔴命中 | 坑乙 | cmd3",
            "- 这是一行坏行没有格式",
            "- 2026-09-16 01:00 | 🔴命中 | 坑丙带 | 竖线 | cmd5 | 来源: LEARNINGS.md",
            "- 2026-09-15 23:30 | 🔴命中 | 坑丙 | cmd4b | 来源: LEARNINGS.md",
        ]
        fresh, count7, perr = parse_recurrence("\n".join(lines), today)
        if count7.get("坑甲", 0) != 2:
            failures.append("T1a 坑甲7天计数=%r 期望2" % count7.get("坑甲"))
        if "坑乙" in count7:
            failures.append("T1b 坑乙在7天窗口外被计入")
        if perr < 1:
            failures.append("T1c 坏行未计入parse_errors")
        if "坑丙" not in fresh:
            failures.append("T1d 坑丙近24h未入fresh")
        if any("cmd" in p or "竖线" in p for p in fresh):
            failures.append("T1e 命令段泄漏进坑名: %r" % fresh)

        # T2 指纹：同源同键=同指纹，异源异键=不同
        if _fingerprint("S2", "x") != _fingerprint("S2", "x"):
            failures.append("T2a 同键指纹不一致")
        if _fingerprint("S2", "x") == _fingerprint("S6", "x"):
            failures.append("T2b 异源指纹撞车")

        # T3 调阈：全拒→收紧；全过→放宽；样本<3不动；范围封顶
        mk = lambda st: {"status": st, "first_seen": "2026-09-01"}
        t, la, note = adjust_threshold([mk("❌")] * 4, 2, None, today)
        if t != 3:
            failures.append("T3a 拒绝率100%%未收紧 t=%r" % t)
        t2, _, _ = adjust_threshold([mk("✅")] * 5, 3, None, today)
        if t2 != 2:
            failures.append("T3b 拒绝率0%%未放宽 t=%r" % t2)
        t3, _, _ = adjust_threshold([mk("✅"), mk("❌")], 2, None, today)
        if t3 != 2:
            failures.append("T3c 样本<3被调阈")
        t4, _, _ = adjust_threshold([mk("❌")] * 9, 4, None, today)
        if t4 != 4:
            failures.append("T3d 门槛超出上限 t=%r" % t4)

        # T4 暂存区初始化与幂等序号
        global STAGING, STATE
        real_staging, real_state = STAGING, STATE
        STAGING = os.path.join(tmp, "CANDIDATES.md")
        STATE = os.path.join(tmp, "state.json")
        ensure_staging(2)
        text1 = _read(STAGING)
        if "同信号门槛：2" not in text1:
            failures.append("T4a 头部门槛缺失")
        ents, thr, _ = load_staging()
        if thr != 2 or ents != []:
            failures.append("T4b 初始化解析异常 %r" % thr)

        # T5 采集端到端（夹具信号源）：S2两坑一次7天复现+S6高严重度→立候选；重跑→幂等零新增
        # T7 S1守卫聚合器红项立候选；T8 S3评估域新鲜报告立候选
        global RECURRENCE, GUARD, GUARD_SELFTEST, EVAL_RESULTS
        real_rec, real_guard = RECURRENCE, GUARD
        real_s1, real_s3 = GUARD_SELFTEST, EVAL_RESULTS
        RECURRENCE = os.path.join(tmp, "免疫复发记录.md")
        GUARD = os.path.join(tmp, "guard.sh")
        GUARD_SELFTEST = os.path.join(tmp, "selftest_missing.py")  # 缺失→S1显式降级不干扰夹具
        EVAL_RESULTS = os.path.join(tmp, "evalresults_empty")      # 不存在→S3显式降级
        with open(RECURRENCE, "w", encoding="utf-8") as f:
            f.write("\n".join([
                "- 2026-09-15 08:00 | 🔴命中 | 测试坑X | c1 | 来源: t",
                "- 2026-09-14 08:00 | 🔴命中 | 测试坑X | c2 | 来源: t",
                "- 2026-09-16 07:00 | 🔴命中 | 测试坑X | c3 | 来源: t",
            ]))
        with open(GUARD, "w", encoding="utf-8") as f:
            f.write('#!/bin/bash\necho \'{"candidates": 4, "alarm": true}\'\n')
        devnull = open(os.devnull, "w")
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            collect(today=today)
            text2 = _read(STAGING)
            collect(today=today)  # 同日重跑
            text3 = _read(STAGING)
        finally:
            sys.stdout = old_stdout
        n_cand = len(re.findall(r"^### \[CAND-", text2, re.M))
        n_cand_rerun = len(re.findall(r"^### \[CAND-", text3, re.M))
        if n_cand != 2:  # 测试坑X(7天3次) + S6(4>=3高严重度)
            failures.append("T5a 首跑候选数=%d 期望2" % n_cand)
        if n_cand_rerun != n_cand:
            failures.append("T5b 同日重跑不幂等 %d→%d" % (n_cand, n_cand_rerun))
        if "测试坑X" not in text2:
            failures.append("T5c S2候选标题缺失")
        if "指纹" not in text2:
            failures.append("T5d 候选缺指纹字段（G2依赖）")

        # T6 G3当日累计上限：清空夹具暂存区，6个独立坑→只立5条；额度满后再跑→不新增
        if os.path.isfile(STAGING):
            os.remove(STAGING)
        ensure_staging(2)
        rec_lines = []
        for i in range(6):
            rec_lines.append("- 2026-09-%02d 08:00 | 🔴命中 | 独立坑%d | c | 来源: t" % (10 + i, i))
            rec_lines.append("- 2026-09-15 09:00 | 🔴命中 | 独立坑%d | c2 | 来源: t" % i)
        with open(RECURRENCE, "w", encoding="utf-8") as f:
            f.write("\n".join(rec_lines))
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            collect(today=today)
            text4 = _read(STAGING)
            collect(today=today)  # 当日额度已满·同日再跑
            text5 = _read(STAGING)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        n_day = len(re.findall(r"^### \[CAND-20260916-", text4, re.M))
        n_day2 = len(re.findall(r"^### \[CAND-20260916-", text5, re.M))
        if n_day != 5:
            failures.append("T6a 当日累计上限失效 %d≠5" % n_day)
        if n_day2 != 5:
            failures.append("T6b 当日额度满后仍写入 %d→%d" % (n_day, n_day2))

        # T7 S1守卫聚合器红项→立候选（缺失/绿/红三态）；T8 S3评估新鲜报告→立候选
        GUARD_SELFTEST = os.path.join(tmp, "fake_selftest.py")
        with open(GUARD_SELFTEST, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\nimport sys; sys.exit(1)\n")
        if os.path.isfile(STAGING):
            os.remove(STAGING)
        ensure_staging(2)
        with open(RECURRENCE, "w", encoding="utf-8") as f:
            f.write("")  # 清空S2信号
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            collect(today=today)
            text6 = _read(STAGING)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        if "守卫自测聚合器有红项" not in text6:
            failures.append("T7a S1红项未立候选")
        # S1绿态→不立
        with open(GUARD_SELFTEST, "w", encoding="utf-8") as f:
            f.write("#!/usr/bin/env python3\nimport sys; sys.exit(0)\n")
        if os.path.isfile(STAGING):
            os.remove(STAGING)
        ensure_staging(2)
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            collect(today=today)
            text7 = _read(STAGING)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        if "守卫自测聚合器有红项" in text7:
            failures.append("T7b S1绿态不应立候选")
        # S3新鲜评估报告→立候选
        EVAL_RESULTS = os.path.join(tmp, "evalresults")
        os.makedirs(EVAL_RESULTS, exist_ok=True)
        with open(os.path.join(EVAL_RESULTS, "fresh_eval.md"), "w", encoding="utf-8") as f:
            f.write("# 评估报告\n")
        if os.path.isfile(STAGING):
            os.remove(STAGING)
        ensure_staging(2)
        old_stdout = sys.stdout
        sys.stdout = devnull = open(os.devnull, "w")
        try:
            collect(today=today)
            text8 = _read(STAGING)
        finally:
            sys.stdout = old_stdout
            devnull.close()
        if "评估域24h新报告" not in text8:
            failures.append("T8 S3新鲜报告未立候选")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        STAGING = globals().get("real_staging", STAGING) if "real_staging" in globals() else STAGING

    # 恢复全局（T4/T5已换全局路径，finally里按序还原·含T5新增的S1/S3）
    try:
        STAGING, STATE, RECURRENCE, GUARD = real_staging, real_state, real_rec, real_guard
        GUARD_SELFTEST, EVAL_RESULTS = real_s1, real_s3
    except NameError:
        pass

    if failures:
        print("SELF-TEST FAIL（%d）:" % len(failures))
        for f_ in failures:
            print("  ✗ " + f_)
        return 1
    print("SELF-TEST PASS（T1-T8 全绿·含S1守卫域/S3评估域源·夹具已自清理）")
    return 0


def main():
    ap = argparse.ArgumentParser(description="成长箱感知层采集器 v%s" % VERSION)
    ap.add_argument("--check", action="store_true", help="健康检查 JSON")
    ap.add_argument("--self-test", action="store_true", help="自测（夹具自清理）")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return health_check()
    return collect()


if __name__ == "__main__":
    sys.exit(main())
