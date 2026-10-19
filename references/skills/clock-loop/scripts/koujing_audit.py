#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
# 口径对账表 v1.0 · 2026-10-12（clock-loop GGS Loop R4 产物）
# 治什么病：修 A 处只验 A 处 → 同一口径在 活体/发布包/git HEAD/派生产物 多面各存一份，人手必漏第 N+1 处
#           （R1→R4 四轮实证：每轮新候选多为上一轮修复引入，PAT-084 已 9+）
# 用法：python3 koujing_audit.py            # 出对账表（只读）
#       python3 koujing_audit.py --out F   # 同时落文件
# 设计：口径清单（可增）× 落点面（活体/包/HEAD）三方对账，任一不一致即 exit 1
import subprocess, os, re, sys, json, hashlib, datetime

import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # V9 根治(2026-10-19 Win真机腿)：cp1252 不可编码 print 必崩——UTF-8 控制台守卫
    except (AttributeError, ValueError):
        pass

H = os.path.expanduser("~")
P = f"{H}/个人AI档案"
GGS = f"{P}/技能配置/good-good-study"
CL = f"{P}/技能配置/good-good-study".replace("good-good-study", "clock-loop")
PKG = f"{P}/发布库/五层记忆系统/布洛陀-全平台安装包"
GB = f"{P}/技能配置/growth-box"

# ── 口径登记表：每条 = (口径名, 判据类型, 目标集合) ─────────────────────────
# 类型 ver   : 版本号必须处处相等
# 类型 count : 某字符串出现次数必须等于期望（期望=None 表示只报数不判）
# 类型 uniq  : 某术语只允许 1 个真源（其余处必须带"史实/降级/指针"注记）
# 类型 sync  : 同一语义在列出的落点上必须同轨（用 needle 判在/不在）
KOUJING = [
    ("GGS 版本号", "ver", [f"{GGS}/SKILL.md", f"{PKG}/references/skills/good-good-study/SKILL.md"]),
    ("clock-loop 版本号", "ver", [f"{CL}/SKILL.md", f"{PKG}/references/skills/clock-loop/SKILL.md"]),
    ("固化件 Skill架构规范版本", "ver", [f"{CL}/references/skill-arch-standard.md",
                                    f"{P}/记忆蓝图/03_开发规范/Skill架构规范/Skill架构规范.md"]),
    ("GGS 自包含清单含 batch_auto_pass", "sync", [f"{GGS}/SKILL.md", f"{PKG}/references/skills/good-good-study/SKILL.md"]),
    ("禁词·安装包不携带该目录", "count0", [f"{GGS}/SKILL.md", f"{GGS}/references/topic-selection.md",
                                       f"{PKG}/references/skills/good-good-study/SKILL.md",
                                       f"{CL}/references/machine-acceptance.md"]),
    ("needle·eval-set 当期条数（C2 分母）", "sync", [f"{GGS}/references/ROADMAP.md", f"{GGS}/SKILL.md"]),
    ("术语单源·零阻断", "uniq", [f"{GGS}/references/ROADMAP.md", f"{GGS}/references/DESIGN-PHILOSOPHY.md",
                               f"{GGS}/references/CHANGELOG.md"]),
    ("needle·技能卡双实装声明", "sync", [f"{GGS}/SKILL.md", f"{PKG}/references/skills/good-good-study/SKILL.md"]),
    # ── growth-box 口径（2026-10-12 clock-loop Loop 成长箱 R3 登记·治"修中心漏半径"：
    #    本轮 8 处缺陷由上一轮修复自身引入，全树人工复扫可抓但不可复用→收进登记表住机械位＝愿景①③）──
    ("GB 旧分母裸写·E9.2/16", "count0", [f"{GB}/SKILL.md", f"{GB}/references/flow-E.md", f"{GB}/references/呈现模板.md"]),
    ("GB 旧步号状态行裸写·B3/5", "count0", [f"{GB}/SKILL.md", f"{GB}/references/flow-B.md", f"{GB}/references/呈现模板.md"]),
    ("GB 命令位解释器错位裸写·python3跑check.sh", "count0", [f"{GB}/SKILL.md", f"{GB}/references/flow-B.md", f"{GB}/references/flow-A.md", f"{GB}/references/flow-C.md"]),
    ("GB D7 枚举镜像点计数", "cnt", [GB]),
]
import os as _os
name_rx = {"GB D7 枚举镜像点计数": [r"晋升|promoted", r"合并|merged", r"保持", r"进知识层|knowledge"]}
d_dir = {"GB D7 枚举镜像点计数": GB}
d_skip = {"GB D7 枚举镜像点计数": {"CHANGELOG.md"}}
d_decl_file = {"GB D7 枚举镜像点计数": os.path.join(GB, "references", "flow-C.md")}
d_decl_rx = {"GB D7 枚举镜像点计数": r"共 (\d+) 处·数由清单与实扫双向核对"}
NEEDLES = {   # sync 类判据：这些子串必须在每个落点上同时成立或同时不成立
    "needle·eval-set 当期条数（C2 分母）": ["43 条"],  # v1.1：原needle取ROADMAP专属措辞，SKILL侧为「43 条用例」→假红（第5次探针过窄自捕）
    "needle·技能卡双实装声明": ["**双实装**"],
    "GGS 自包含清单含 batch_auto_pass": ["batch_auto_pass.py（消费处"],
}
AUTHORITATIVE = {   # uniq 类：允许的唯一真源落点（basename）
    "术语单源·零阻断": ["ROADMAP.md"],
}
COUNT0_NEEDLES = {  # count0 类判据的 needle（缺省=禁词"安装包不携带该目录"）
    "GB 旧分母裸写·E9.2/16": "成长箱·E9.2/16",
    "GB 旧步号状态行裸写·B3/5": "成长箱·B3/5",
    "GB 命令位解释器错位裸写·python3跑check.sh": "python3 [记忆共享中心]/技能配置/growth-box/scripts/growth_box_check.sh",
}
NEEDLE_MARK = ["改判前", "历史口径", "已被 C1 改判", "指针", "现行口径见", "现行唯一真源", "史实"]  # v1.1：原词表过窄致已加注的 DP 仍判裸用（第4次探针过窄自捕）


def ver_of(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'^version:\s*"?v?([0-9][0-9.]*)"?', t, re.M)
    return m.group(1) if m else "?"


RUNS_LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".koujing_runs.jsonl")


def _append_run_ledger(total, red, rows):
    """落运行账本（v1.3 新增·封口门禁17的核验源）。run_id=内容散列，不可凭空编。"""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw = f"{ts}|{total}|{red}|" + ";".join(r[:60] for r in rows)
    rid = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:8]
    rec = {"run_id": rid, "ts": ts, "total": total, "red": red}
    with open(RUNS_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rid


def main():
    out, bad = [], 0
    for name, kind, files in KOUJING:
        missing = [f for f in files if not os.path.exists(f)]
        rows = []
        if kind == "ver":
            vals = ["文件缺失" if f in missing else ver_of(f) for f in files]
            ok = len(set(v for v in vals if v != "?")) <= 1 and not missing
        elif kind == "count0":
            nd = COUNT0_NEEDLES.get(name, "安装包不携带该目录")  # v1.2：count0 泛化——原硬编码单 needle，新对象登记必误判
            vals = [0 if f in missing else open(f, encoding="utf-8", errors="ignore").read().count(nd) for f in files]
            ok = sum(vals) == 0
        elif kind == "sync":
            nd = NEEDLES[name]
            vals = []
            for f in files:
                t = "" if f in missing else open(f, encoding="utf-8", errors="ignore").read()
                vals.append("有" if all(x in t for x in nd) else "无")
            ok = len(set(vals)) == 1
        elif kind == "cnt":   # v1.3 新增：声明数字 vs 实扫计数（D7 镜像点口径的机械看护）
            rx = [re.compile(pt, re.I) for pt in name_rx[name]]
            n = 0
            for root_, dnames, fns in os.walk(d_dir[name]):
                if "__pycache__" in root_:
                    continue
                for fn in fns:
                    if not fn.endswith(".md") or fn in d_skip[name]:
                        continue
                    for line in open(os.path.join(root_, fn), encoding="utf-8", errors="ignore"):
                        st = line.lstrip()
                        if st.startswith(">") and not st.startswith("> |"):
                            continue   # 定义/解释层（块引用）不算镜像点·与 flow-C D7 口径一致
                        if all(r.search(line) for r in rx):
                            n += 1
            dm = re.search(d_decl_rx[name], open(d_decl_file[name], encoding="utf-8", errors="ignore").read())
            declared = int(dm.group(1)) if dm else -1
            vals = [f"实扫={n}", f"声明={declared}"]
            ok = n == declared and declared > 0
        else:  # uniq
            vals = []
            for f in files:
                t = "" if f in missing else open(f, encoding="utf-8", errors="ignore").read()
                n = len(re.findall("零阻断", t))
                marked = any(k in t for k in NEEDLE_MARK)
                auth = os.path.basename(f) in AUTHORITATIVE[name]
                vals.append(("真源" if auth else ("注记降级" if (n and marked) else ("裸用" if n else "无"))))
            ok = vals.count("真源") == 1 and all(v in ("真源", "注记降级", "无") for v in vals)
        out.append(f'{"✅" if ok else "🔴"} {name:<28} {vals}')
        bad += 0 if ok else 1
    # eval-set 实际条数（防"账上 43 实际 40"型漂移）
    ev = open(f"{GGS}/references/eval-set.md", encoding="utf-8").read()
    n_real = len([l for l in ev.splitlines() if re.match(r"^\| \d+ \|", l)])
    claimed = re.findall(r"当期 (\d+) 条", open(f"{GGS}/references/ROADMAP.md", encoding="utf-8").read())
    okc = bool(claimed) and str(n_real) == claimed[-1]
    out.append(f'{"✅" if okc else "🔴"} eval-set 实数 vs 宣称          实={n_real} 宣称={claimed[-1] if claimed else "??"}')
    bad += 0 if okc else 1
    # INDEX 抬头账实
    idxp = f"{P}/AI学习库/INDEX.md"
    it = open(idxp, encoding="utf-8").read()
    body = len([l for l in it.splitlines() if re.match(r"^\|\s*(立场卡|技能卡)#", l)])
    disk = len([f for f in os.listdir(f"{P}/AI学习库") if re.match(r"^(立场卡|技能卡)#", f) and f.endswith(".md")])
    head = re.findall(r"磁盘实盘 \*\*(\d+)[ 张]*\*\*", it)   # v1.1 修：原正则要求数字后紧跟**，实盘为「**1060 张**」→ 探针假阴性（R4 自捕·第3次坏探针）
    oki = bool(head) and int(head[0]) == body == disk and "账实一致" in it
    # ⚪ 三态：已建工单的他域项不判红也不判绿（假绿=掩盖 / 永久假红=麻木，两者都失真）
    TICKET = "2026-10-12-GGS-Loop挂账与转你清单.md R4"
    st = "✅" if oki else f"⚪工单"
    out.append(f'{st} INDEX 抬头/表体/磁盘 三数同轨  抬头={head[0] if head else "??"} 表体={body} 磁盘={disk}'
               + ("" if oki else f'  ← regen 重算属引擎域·{TICKET}'))
    bad += 0 if oki else 0

    print("📐 口径对账表 v1.0（只读·可重跑·Loop 每轮开跑前先跑它）")
    print("\n".join(out))
    print(f"\n结论：{len(KOUJING) + 2} 条口径 · 🔴{bad} 条不同轨")
    rid = _append_run_ledger(len(KOUJING) + 2, bad, out)
    print(f"口径复扫凭证 run_id={rid}（已落 .koujing_runs.jsonl·封口门禁17核验此值）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
