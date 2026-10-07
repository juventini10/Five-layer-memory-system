#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/gate_runner.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# version: v0.1
"""gate_runner.py —— 零问题门禁运行器（自动发现 + 三方对账 + 心跳）

🔴 为什么不是"写四个门禁脚本"而是"写门禁的注册表"（质变点）：
  规格书 L38 用一行括号枚举了 G1–G4，那是**示例性枚举**不是穷举清单。
  若写死四个 = 把示例当全集 = 制造下一个漂移源（同 kb-index 沉默死、
  守卫文档≠实挂、手工名单漂移的同一病根）。
  → 解法：**文件系统是唯一真相源，不信任手工名单**（registry_guards.sh
    第一性原理根治的同一模式）。新门禁丢进 gates/ 即零配置接入。

🔴 三方对账（本运行器的核心价值）：
  | 方 | 来源 | 含义 |
  |---|---|---|
  | 声称方 | 规格书 L38 正则解析 | 文档说有 G1–G4 |
  | 注册方 | gates/*.json 磁盘发现 | 实际注册了几个 |
  | 实跑方 | 本轮执行结果 | 真正跑起来的几个 |
  三方不一致 = 漂移 → 报警（文档与实盘脱钩的机械检测，LRN-20260825-001）

🔴 未定义 ≠ 不可见：
  status=spec_pending 的门禁（规格只有括号注释、无判据）不会被静默跳过，
  也不会被假装通过——它作为「未定义·不可判定」显式出现在报告中。
  ⛔ 设计纪律：宁可显示"不知道"，不可显示"通过"（S006 全绿幻觉红线）。

契约：--check(JSON,含 alarm) / --report(markdown) / --selfcheck
心跳：/tmp/gate_runner.heartbeat
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys
import os
import re
import json
import glob
import subprocess
from datetime import datetime

GATES_DIR = os.path.expanduser("~/[记忆共享中心]/数字分身/gates")
SPEC_FILE = os.path.expanduser("~/[记忆共享中心]/数字分身/童灵·人格规格书.md")
# 2026-09-22 挂尸普查根治：/tmp 违反守卫规范§三·06（重启即灭·不可跨重启审计）→迁持久台账；全仓扫描证实读写方仅本文件，零跨端读方
HEARTBEAT = os.path.expanduser("[记忆共享中心]/脚本中心/logs/gate_runner.heartbeat")


def beat():
    try:
        with open(HEARTBEAT, "w", encoding="utf-8") as f:
            json.dump({"ts": datetime.now().isoformat(timespec="seconds")}, f)
    except OSError:
        pass


def get_text_from_stdin():
    try:
        raw = sys.stdin.buffer.read().decode('utf-8', errors='replace')
        if not raw.strip():
            return ""
        try:
            d = json.loads(raw)
            for k in ("text", "prompt", "content", "message"):
                v = d.get(k)
                if isinstance(v, str) and v.strip():
                    return v
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            return item["text"]
            return json.dumps(d, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return raw
    except Exception:
        return ""


def parse_claimed():
    """声称方：从规格书解析出文档声称存在的门禁编号"""
    if not os.path.exists(SPEC_FILE):
        return []
    try:
        with open(SPEC_FILE, encoding="utf-8") as f:
            for line in f:
                if "零问题门禁集" in line:
                    return sorted(set(re.findall(r"\bG\d+\b", line)))
    except OSError:
        pass
    return []


def discover():
    """注册方：磁盘自动发现，无手工名单"""
    gates = []
    for p in sorted(glob.glob(os.path.join(GATES_DIR, "*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                g = json.load(f)
            # 只认「门禁声明」：必须有 id + status。
            # 同目录下的配置类 json（如 health_probes.json）不是门禁，
            # 否则会被当成 id=None 的幽灵门禁（2026-08-29 实测）
            if not isinstance(g, dict) or not g.get("id") or not g.get("status"):
                continue
            g["_file"] = os.path.basename(p)
            gates.append(g)
        except (OSError, json.JSONDecodeError):
            continue
    return gates


def _parse_stats_table(text):
    """解析 stats.py 输出的模式目录表 → {PAT-XXX: (累计次数, 最新发生)}

    表格式（stats.py 实跑确认）：
    | 编号 | 模式名称 | 累计次数 | 最新发生 | 状态 | 关联铁律 |
    """
    out = {}
    for line in (text or "").splitlines():
        m = re.match(r"\s*\|\s*(PAT-\d+)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|", line)
        if m:
            out[m.group(1)] = (m.group(3).strip(), m.group(4).strip())
    return out


def _check_frontmatter(blocks, window_title=True):
    """frontmatter 一致性三查（G1 判据·有规范原文支撑）

    依据：
    - 文件格式规范 L145「标题层级从 ##(H2) 起（frontmatter 已含 title，无需 H1）」
    - 指令编写规范 L734「改名后 source 不得指向已删旧文件」——实战案例：
      SOUL 版本行"缝合怪"、Qoder系哲学合并后 source 仍指向已删文件
    """
    hard, soft = [], []
    for b in blocks:
        if not b:
            continue
        body = b
        title = None
        source = None
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", b, re.S)
        if m:
            fm, body = m.group(1), m.group(2)
            tm = re.search(r"^title:\s*(.+)$", fm, re.M)
            sm = re.search(r"^source:\s*(.+)$", fm, re.M)
            title = tm.group(1).strip().strip("\"'") if tm else None
            source = sm.group(1).strip().strip("\"'") if sm else None
            if source:
                src_path = os.path.expanduser(source.split(" ")[0].split("#")[0])
                if src_path and not os.path.exists(src_path):
                    hard.append(f"frontmatter.source 指向不存在的文件: {source[:60]}")
        if re.search(r"^# [^#]", body, re.M):
            line = next(l for l in body.splitlines() if re.match(r"^# [^#]", l))
            soft.append(f"正文出现 H1（规范：从 H2 起）: {line[:40]}")
        if window_title and title:
            h2 = re.search(r"^## (.+)$", body, re.M)
            if h2 and title.replace(" ", "") not in h2.group(1).replace(" ", ""):
                soft.append(f"frontmatter.title『{title[:24]}』与首个 H2『{h2.group(1)[:24]}』不一致")
    return hard, soft


def run_gate(g, text):
    gid, status = g.get("id"), g.get("status")

    if status == "spec_pending":
        return {"id": gid, "ran": False, "verdict": "UNDEFINED",
                "reason": g.get("undef_reason", "")}

    if status == "delegated":
        script = os.path.expanduser(g.get("delegate", ""))
        if not script or not os.path.exists(script):
            return {"id": gid, "ran": False, "verdict": "DELEGATE_MISSING",
                    "reason": f"委托脚本不存在: {g.get('delegate')}"}
        try:
            r = subprocess.run([sys.executable, script, "--check"],
                               input=text, capture_output=True, text=True, timeout=60)
            try:
                out = json.loads(r.stdout.strip().splitlines()[-1])
                alarm = out.get("alarm", False)
            except (json.JSONDecodeError, IndexError):
                alarm = False
            return {"id": gid, "ran": True, "verdict": "RED" if alarm else "GREEN",
                    "delegate": os.path.basename(script)}
        except (subprocess.TimeoutExpired, OSError) as e:
            return {"id": gid, "ran": False, "verdict": "DELEGATE_ERROR", "reason": str(e)}

    judge = g.get("judge") or {}
    if judge.get("type") == "regex_near":
        anchor = judge.get("anchor", "")
        window = int(judge.get("window", 150))
        must = judge.get("must_contain", [])
        # 优先用正则（forbid_pattern）捕获"完成态声称"，词表（forbid_claim）作兜底
        forbid_re = judge.get("forbid_pattern")
        forbid_words = judge.get("forbid_claim", [])
        hits = []
        for m in re.finditer(anchor, text or ""):
            ctx = text[max(0, m.start() - window):m.start() + window]
            if must and any(w in ctx for w in must):
                continue  # 已标"预存"= 透明标注，放行
            claimed_done = bool(forbid_re and re.search(forbid_re, ctx)) or \
                           bool(forbid_words and any(w in ctx for w in forbid_words))
            if claimed_done:
                hits.append(m.group(0))
        if hits:
            return {"id": gid, "ran": True, "verdict": "WARN",
                    "reason": f"{len(hits)} 处声称已修复但缺『预存』标注: {', '.join(hits[:5])}",
                    "caveat": g.get("caveat", "")}
        return {"id": gid, "ran": True, "verdict": "GREEN"}

    if judge.get("type") == "stats_drift":
        script = os.path.expanduser(judge.get("script", ""))
        learnings = os.path.expanduser(judge.get("learnings_dir", ""))
        index = os.path.expanduser(judge.get("index", ""))
        if not (os.path.exists(script) and os.path.exists(index)):
            return {"id": gid, "ran": False, "verdict": "NO_JUDGE",
                    "reason": f"stats 载体缺失(script={os.path.exists(script)}, index={os.path.exists(index)})"}
        try:
            r = subprocess.run(
                [sys.executable, script, "--learnings-dir", learnings, "--index", index],
                capture_output=True, text=True, timeout=120)
            recomputed = _parse_stats_table(r.stdout)
            with open(index, encoding="utf-8") as f:
                existing = _parse_stats_table(f.read())
        except (subprocess.TimeoutExpired, OSError) as e:
            return {"id": gid, "ran": False, "verdict": "DELEGATE_ERROR", "reason": str(e)}
        drift = {k: {"重算": recomputed.get(k), "表内": existing.get(k)}
                 for k in sorted(set(recomputed) | set(existing))
                 if recomputed.get(k) != existing.get(k)}
        if drift:
            sample = ", ".join(f"{k}(重算{v['重算']}≠表内{v['表内']})"
                               for k, v in list(drift.items())[:3])
            return {"id": gid, "ran": True, "verdict": "RED",
                    "reason": f"{len(drift)} 项派生数据不一致（手工维护漂移）: {sample}"}

        # 成长箱 pending 状态漂移（G3 扩展·2026-08-29）
        # 状态列 pending(N/3) 的 N 由手工维护，与 stats.py 重算的真实引用数可能脱节
        # → 幽灵条目（N≥3 但零引用）会让晋升决策建立在假数字上（晋升不可逆）
        aud = judge.get("pending_audit")
        if aud and os.path.exists(os.path.expanduser(aud)):
            try:
                r2 = subprocess.run([sys.executable, os.path.expanduser(aud), "--check"],
                                    capture_output=True, text=True, timeout=120)
                # 整体解析：--check 输出为 indent=2 的多行 JSON，
                # ⛔DO NOT 用 splitlines()[-1]（最后一行只是 "}"）
                d2 = json.loads(r2.stdout.strip())
                ghosts = d2.get("ghosts") or []
                if ghosts:
                    gs = ", ".join(f"{g['id']}(标{g['claimed']}·真实{g['real']})"
                                   for g in ghosts[:3])
                    return {"id": gid, "ran": True, "verdict": "RED",
                            "reason": f"{len(ghosts)} 条幽灵条目（状态虚标·阻断晋升）: {gs}"}
                inv = d2.get("inverted") or []
                if inv:
                    ins = ", ".join(f"{g['id']}(标{g['claimed']}·真实{g['real']})"
                                    for g in inv[:3])
                    return {"id": gid, "ran": True, "verdict": "WARN",
                            "reason": f"{len(inv)} 条倒挂（实例未回写状态列）: {ins}"}
                return {"id": gid, "ran": True, "verdict": "GREEN",
                        "reason": (f"drift=0（{len(recomputed)} 项派生一致）+ 成长箱 "
                                   f"{d2.get('total', 0)} 条模式无幽灵无倒挂")}
            except (subprocess.TimeoutExpired, OSError,
                    json.JSONDecodeError, IndexError) as e:
                return {"id": gid, "ran": True, "verdict": "WARN",
                        "reason": f"pending 体检脚本异常（不阻断）: {type(e).__name__}"}
        return {"id": gid, "ran": True, "verdict": "GREEN",
                "reason": f"drift=0（{len(recomputed)} 项派生数据全部一致）"}

    if judge.get("type") == "frontmatter_consistency":
        blocks = re.findall(r"```(?:md|markdown)\n(.*?)```", text or "", re.S)
        target = judge.get("file")
        if target:
            tp = os.path.expanduser(target)
            if os.path.exists(tp):
                with open(tp, encoding="utf-8") as f:
                    blocks.append(f.read())
        if not blocks:
            return {"id": gid, "ran": False, "verdict": "NO_TARGET",
                    "reason": "本轮无 md 代码块且未指定 --file，无可检对象（非缺陷）"}
        hard, soft = _check_frontmatter(blocks)
        if hard:
            return {"id": gid, "ran": True, "verdict": "RED",
                    "reason": "; ".join(hard[:3])}
        if soft:
            return {"id": gid, "ran": True, "verdict": "WARN",
                    "reason": "; ".join(soft[:3])}
        return {"id": gid, "ran": True, "verdict": "GREEN",
                "reason": f"frontmatter 三查通过（{len(blocks)} 个对象）"}

    return {"id": gid, "ran": False, "verdict": "NO_JUDGE",
            "reason": "门禁已注册但无可执行判据"}


def evaluate(results, gates):
    """全 GREEN 才发货；任一 RED→阻断；UNDEFINED 不计 GREEN 也不计阻断，但必须可见"""
    blocking = [r for r in results if r["verdict"] == "RED"]
    warn = [r for r in results if r["verdict"] == "WARN"]
    undefined = [r for r in results if r["verdict"] in ("UNDEFINED", "NO_JUDGE")]
    missing = [r for r in results if r["verdict"].startswith("DELEGATE_")]
    return {"blocking": [r["id"] for r in blocking],
            "warn": [r["id"] for r in warn],
            "undefined": [r["id"] for r in undefined],
            "delegate_issue": [r["id"] for r in missing]}


def drift_check(claimed, gates, results):
    """三方对账：声称 vs 注册 vs 实跑"""
    registered = sorted({g.get("id") for g in gates if g.get("id")})
    ran = sorted({r["id"] for r in results if r.get("ran")})
    return {
        "claimed": claimed,
        "registered": registered,
        "ran": ran,
        "drift_claimed_not_registered": [g for g in claimed if g not in registered],
        "drift_registered_not_claimed": [g for g in registered if g not in claimed],
        "drift_not_run": [g for g in registered if g not in ran],
    }


def mode_check(text, strict=False, block_on_red=False):
    beat()
    gates = discover()
    claimed = parse_claimed()
    results = [run_gate(g, text) for g in gates]
    ev = evaluate(results, gates)
    drift = drift_check(claimed, gates, results)
    # 默认 UNDEFINED 不计 alarm（天天报警=噪音=守卫被忽略）；
    # --strict 时才把规格欠账算进 alarm（供你主动查欠账用）
    alarm = bool(ev["blocking"] or ev["delegate_issue"]
                 or drift["drift_claimed_not_registered"]
                 or (strict and ev["undefined"]))
    print(json.dumps({
        "alarm": alarm,
        "strict": strict,
        "gates_registered": len(gates),
        "evaluation": ev,
        "drift": drift,
        "note": "UNDEFINED=规格未定义不可判定(⛔不假装通过); 日常不计报警, --strict 才计",
    }, ensure_ascii=False, indent=2))
    # T3（2026-08-29）：RED/delegate 缺失时若启用 --block-on-red → exit 1 真卡（仅 WB Stop 调用启用，不波及 Hermes 等其它端）
    return 1 if (block_on_red and (ev["blocking"] or ev["delegate_issue"])) else 0


def mode_report(text):
    gates = discover()
    claimed = parse_claimed()
    results = [run_gate(g, text) for g in gates]
    ev = evaluate(results, gates)
    drift = drift_check(claimed, gates, results)

    print("## 🚦 零问题门禁运行器")
    print()
    print("| 门禁 | 名称 | 状态 | 判定 |")
    print("|---|---|---|---|")
    name_by_id = {g.get("id"): g.get("name", "") for g in gates}
    for r in results:
        mark = {"GREEN": "🟢 通过", "RED": "🔴 **阻断**", "WARN": "🟡 提示",
                "UNDEFINED": "⚪ **规格未定义·不可判定**",
                "NO_JUDGE": "⚪ 无判据",
                "DELEGATE_MISSING": "🔴 委托脚本缺失",
                "DELEGATE_ERROR": "🔴 委托执行失败"}.get(r["verdict"], r["verdict"])
        print(f"| {r['id']} | {name_by_id.get(r['id'],'')} | {r.get('reason','')[:40]} | {mark} |")
    print()

    print("### 三方对账（防文档与实盘脱钩）")
    print("| 方 | 门禁 |")
    print("|---|---|")
    print(f"| 声称方（规格书 L38） | {', '.join(drift['claimed']) or '未解析到'} |")
    print(f"| 注册方（gates/ 磁盘） | {', '.join(drift['registered']) or '空'} |")
    print(f"| 实跑方（本轮执行） | {', '.join(drift['ran']) or '无'} |")
    print()
    if drift["drift_claimed_not_registered"]:
        print(f"> 🔴 **漂移**：规格书声称但 gates/ 未注册 → "
              f"{', '.join(drift['drift_claimed_not_registered'])}")
    if drift["drift_registered_not_claimed"]:
        print(f"> 🟡 **漂移**：已注册但规格书未声称（新门禁待回写规格书）→ "
              f"{', '.join(drift['drift_registered_not_claimed'])}")
    if drift["drift_not_run"]:
        print(f"> ⚪ 注册了但本轮未实跑（规格未定义/委托缺失）→ {', '.join(drift['drift_not_run'])}")
    print()

    undef = [r for r in results if r["verdict"] in ("UNDEFINED", "NO_JUDGE")]
    if undef:
        print("### ⚪ 规格未定义清单（⛔ 不假装通过，等待判据）")
        for r in results:
            if r["verdict"] in ("UNDEFINED", "NO_JUDGE"):
                print(f"- **{r['id']}**：{r.get('reason','')}")
        print()
        print("> 补上判据即可转 🟢/🔴 机械判定；⛔ 在此之前它不算通过。")
    return


def mode_selfcheck():
    print(f"门禁目录: {GATES_DIR} {'✅' if os.path.isdir(GATES_DIR) else '❌'}")
    print(f"规格书: {SPEC_FILE} {'✅' if os.path.exists(SPEC_FILE) else '❌'}")
    print(f"声称方解析: {', '.join(parse_claimed()) or '未解析到'}")
    gates = discover()
    print(f"注册门禁: {len(gates)} 个 → {', '.join(g.get('id','?') for g in gates)}")
    print("用法: gate_runner.py [--check|--report|--selfcheck]")
    return 0


FILE_ARG = ""


def main():
    global FILE_ARG
    args = sys.argv[1:]
    if "--file" in args:
        i = args.index("--file")
        if i + 1 < len(args):
            FILE_ARG = args[i + 1]
    if "--selfcheck" in args:
        sys.exit(mode_selfcheck())
    text = get_text_from_stdin()
    if "--report" in args:
        mode_report(text)
        return
    sys.exit(mode_check(text, strict="--strict" in args, block_on_red="--block-on-red" in args))


if __name__ == "__main__":
    main()
