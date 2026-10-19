#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
# 件端覆盖矩阵扫描器 v0（试点：仅 ZCode 列实扫）·零副作用只读
# 行全量三源: ①守卫编写规范§四注册表 ②04-跨端接入指南 Hook清单14件 ③scripts_manifest(路由/引擎/变换)
import sys as _sys, os as _os; _SCROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))); _SCROOT in _sys.path or _sys.path.insert(1, _SCROOT)  # sc-rootfix-20261014 域搬补路
import json, re, os, sys
from datetime import datetime

SCAN_TIME = datetime.now().strftime("%Y-%m-%d %H:%M")

# ---------- 源① 守卫注册表 ----------
REG = os.path.expanduser("[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md")
reg_lines = open(REG).read().split("\n")
start = next(i for i, l in enumerate(reg_lines) if l.startswith("| 守卫 | 辖区 |"))
rows, glued = [], []
for i in range(start + 1, len(reg_lines)):
    l = reg_lines[i]
    if not l.startswith("|"):
        if rows and l.strip():
            if any(x.startswith("|") for x in reg_lines[i:i+3]):
                continue
            break
        continue
    cells = [c.strip() for c in l.strip().strip("|").split("|")]
    name = cells[0] if cells else ""
    if name == "" or set(name) <= {"-", ":"}:
        name = cells[1] if len(cells) > 1 else ""
        if not name:
            continue
    retired = "~~" in name
    # 规范名清洗
    clean = re.sub(r"[（(].*?$", "", name).replace("~~", "").strip()
    clean = re.sub(r"\s*⛔.*?$", "", clean).strip()
    clean = re.sub(r"\s*\*\*v[\d.]+\*\*$", "", clean).strip()
    rows.append({"raw": name, "name": clean, "line": i + 1, "retired": retired, "src": "注册表"})
    # 粘连检测: 行中 || xxx.py
    for m in re.finditer(r"\|\|\s*([A-Za-z_\-\u4e00-\u9fff]+\.(?:py|sh))", l):
        g = m.group(1)
        if g != clean:
            glued.append({"name": g, "line": i + 1, "src": "注册表(粘连行补提)"})
            rows.append({"raw": g, "name": g, "line": i + 1, "retired": False, "src": "注册表(粘连行补提)"})

# 去重（保留首现，标重复）
seen = {}
reg_unique = []
for r in rows:
    key = r["name"]
    if key in seen:
        seen[key]["dup_lines"].append(r["line"])
    else:
        r["dup_lines"] = []
        seen[key] = r
        reg_unique.append(r)

# ---------- 源② 04指南 Hook 清单 ----------
GUIDE = os.path.expanduser("[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/04-跨端接入指南.md")
guide_lines = open(GUIDE).read().split("\n")
gstart = next(i for i, l in enumerate(guide_lines) if l.startswith("| # | Hook 脚本 |"))
hook14 = []
for i in range(gstart + 1, len(guide_lines)):
    l = guide_lines[i]
    if not l.startswith("|"):
        break
    cells = [c.strip() for c in l.strip().strip("|").split("|")]
    if len(cells) < 3 or not re.match(r"^\d+$|^~~\d+~~$", cells[0]):
        continue
    name = cells[1]
    retired = ("退役" in cells[2]) or ("~~" in name) or ("永久关闭" in cells[2])
    clean = re.sub(r"[（(].*?$", "", name).replace("~~", "").strip()
    clean = re.sub(r"\s*⛔.*?$", "", clean).strip()
    hook14.append({"raw": name, "name": clean, "line": i + 1, "retired": retired, "src": "Hook清单14"})

# ---------- 源③ scripts_manifest（路由/引擎/变换）----------
# 🔧 2026-10-09 童灵根治：原式写死 `[记忆共享中心]/脚本中心/scripts_manifest.json`，
#   而 manifest 物理真源在 `开发工具/`（发布链 SSOT·⛔不可搬）⇒ 本行 `json.load(open(MAN))`
#   在派生副本侧直接 FileNotFoundError 崩栈（比静默失效好，但仍是路径基准分家病）。
#   ✅ 改经共用定位器 manifest_locator（自身→上级→runtime_paths→作者态兜底）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from manifest_locator import find_manifest
    MAN = find_manifest(__file__)
except Exception as _e:
    MAN = os.path.expanduser("[记忆共享中心]/脚本中心/scripts_manifest.json")
    print("⚠️ manifest_locator 不可用（%s）·回退原式：%s" % (_e, MAN), file=sys.stderr)
man = json.load(open(MAN))
man_rows = []
for s in man["scripts"]:
    fam = s.get("family") or ""
    sub = s.get("subfamily") or ""
    if fam in ("引擎", "变换") or "路由" in sub:
        man_rows.append({"name": s["name"], "family": fam, "subfamily": sub,
                         "form": s.get("form"), "event": s.get("event"),
                         "path": s.get("path"), "src": "manifest"})

# manifest 内部重复检测
man_seen = {}
man_dups = []
for m in man_rows:
    man_seen.setdefault(m["name"], []).append((m["family"], m["subfamily"], m["form"]))
man_dup_names = {k: v for k, v in man_seen.items() if len(v) > 1}

# ---------- 三源并集 ----------
all_names = {}
def add(name, src, extra=None):
    if not name:
        return
    e = all_names.setdefault(name, {"name": name, "sources": [], "retired": False, "extra": []})
    if src not in e["sources"]:
        e["sources"].append(src)
    if extra:
        e["extra"].append(extra)

for r in reg_unique:
    add(r["name"], "①注册表", {"line": r["line"], "retired": r["retired"], "dup_lines": r["dup_lines"]})
    if r["retired"]:
        all_names[r["name"]]["retired"] = True
for g in glued:
    add(g["name"], "①注册表-粘连补提", {"line": g["line"]})
for h in hook14:
    add(h["name"], "②Hook清单14", {"line": h["line"], "retired": h["retired"]})
    if h["retired"]:
        all_names[h["name"]]["retired"] = True
for m in man_rows:
    add(m["name"], "③manifest", {"family": m["family"], "subfamily": m["subfamily"], "form": m["form"], "event": m["event"]})

# ---------- ZCode 承载证据 ----------
CFG = os.path.expanduser("~/.zcode/cli/config.json")
cfg = json.load(open(CFG))
zcode_mounted = {}  # scriptname -> [event...]
for ev, entries in cfg["hooks"]["events"].items():
    for e in entries:
        for h in e.get("hooks", []):
            cmd = h.get("command", "")
            m = re.search(r"([A-Za-z_0-9\-]+\.(?:py|sh))", cmd)
            if m:
                zcode_mounted.setdefault(m.group(1), []).append(ev)

# setup.sh 委派面 ROSTER
SETUP = os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包/adapters/zcode/setup.sh")
stext = open(SETUP).read()
delegated = set(re.findall(r"([A-Za-z_0-9\-]+\.(?:py|sh))", stext))

# 04指南 ZCode 列裁定（从 L174 接入通道说明提取关键裁定句）
z_rulings = {
    "l3_conclusion_guard.py": "⛔不补挂（09-05你令永久关闭·端级排除分母·SRC_EXCLUDED）",
    "reply_format_guard.py": "⛔本体08-26完全删除·退回SOUL软约束",
    "guard_registry_check.py": "⛔不挂（真相源=settings.json形态·ZCode=config.json形态·同职能zcode_config_guard覆盖·04指南L174判定记录）",
    "crossend_guard.py": "✅08-27 SessionStart三件套补实",
}

result = {
    "scan_time": SCAN_TIME,
    "counts": {
        "reg_rows": len(rows), "reg_unique": len(reg_unique),
        "reg_retired": sum(1 for r in reg_unique if r["retired"]),
        "reg_glued": len(glued),
        "hook14_rows": len(hook14),
        "manifest_in_scope": len(man_rows),
        "manifest_dup_names": man_dup_names,
        "union_total": len(all_names),
    },
    "zcode_mounted": zcode_mounted,
    "delegated_roster_sample": sorted(list(delegated))[:50],
    "rows": [],
}
for name, e in sorted(all_names.items()):
    mounted = zcode_mounted.get(name)
    row = {
        "name": name,
        "sources": e["sources"],
        "retired": e["retired"],
        "zcode_events": mounted,
        "delegated": name in delegated,
        "ruling": z_rulings.get(name),
        "extra": e["extra"][:3],
    }
    result["rows"].append(row)

out = "/tmp/coverage_audit_data.json"
json.dump(result, open(out, "w"), ensure_ascii=False, indent=1)
print("saved:", out)
print(json.dumps(result["counts"], ensure_ascii=False, indent=1))
print("\nZCode mounted scripts:", len(zcode_mounted))
for k, v in sorted(zcode_mounted.items()):
    print(f"  {k}: {v}")
