#!/usr/bin/env python3
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
# REG: family=守卫 | registry=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/守卫编写规范.md§四 | board=记忆蓝图/04_系统文件设计/布洛陀脚本架构设计哲学/03-进度看板.md
# -*- coding: utf-8 -*-
"""registry_precheck_guard.py v1.0 — 「改完必回流治理文档」事前钩子（PreToolUse）+ 事后核销。

补的是哪道缺口（2026-09-19 自曝）：本端上午刚给 PAT-045 建了时间戳事前钩子，而 §3.0「登记三件套」
（git入库 / 挂载实盘 / 文档登记 / 家族实例回流）至今**只有事后检测**（guard_doc_consistency 件⑥ 查已登记的
条目是否与文档一致）——**没登记**这种情况事后闸看不见（它扫的是注册表，注册表里没有它就不报）。
即"事后有闸、事前无钩"，与 PAT-045 同构。

设计（为什么不是"要求写代码前先改文档"）：PreToolUse 发生在落笔瞬间，此时要求文档已改好＝强制
先文档后代码，与现实工作序（写→测→登记）冲突且必造大量假红。故拆两半：
  ①**事前·承诺进件**：新建治理脚本（路径在治理域内·文件此前不存在·非测试夹具）落盘时，头部必须带
    `# REG:` 行声明三个登记落点（family / registry / board）。写不出这行＝还没想清它归哪个家族、
    登记在哪、进度记在哪——正是 §3.0 想拦的"先写完再说"。缺行 → exit 2 拦。
  ②**事后·核销**：`--reconcile` 拿 journal 里的承诺去查落点文件是否真出现该脚本名，未出现＝⚠️未回流
    （exit 0 不阻断，符合 Hook 三纪律；供 Stop 链/巡检显形·⛔不靠人记得）。
  ③**免检出口**：`# REG: skip <原因>` 显式豁免——绕过留痕（原因进 journal 可抽检），⛔不静默放行。

治理域（只判这三处，⛔不扩到全库）：开发工具/ 、技能配置/*/scripts/ 、数字分身/scripts/ 。
排除：tests/ fixtures/ steps/ .bak 记忆琥珀 发布库 __pycache__（夹具与派生镜像不是"新资产入库"）。
回落律：payload 非 JSON / 非 .py|.sh / 文件已存在（改既有脚本不属本判据）→ 一律放行 exit 0。
"""
import datetime
import json
import os
import re
import sys

BASE = os.path.expanduser("~")
JOURNAL = os.path.expanduser("[记忆共享中心]/脚本中心/logs/registry_promise.jsonl")
DOMAIN_RE = re.compile(r"([记忆共享中心]/脚本中心/|~/[记忆共享中心]/技能配置/[^/]+/scripts/|~/[记忆共享中心]/数字分身/scripts/)")
EXCLUDE_RE = re.compile(r"(/tests/|/fixtures/|/steps/|\.bak|记忆琥珀|发布库|__pycache__|/golden/)")
REG_RE = re.compile(r"^#\s*REG:\s*(.+)$", re.M)
FIELDS = ("family", "registry", "board")
# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"~/个人AI档案/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass


def in_domain(path):
    p = str(path).replace("\\", "/")
    return bool(DOMAIN_RE.search(p)) and not EXCLUDE_RE.search(p) and p.endswith((".py", ".sh"))


def parse_reg(text):
    """只在文件头 12 行内识别 REG 行——正文/报错文案里的示例字样不得顶罪（本文件自测实证）。"""
    """解析 `# REG: family=守卫 | registry=...§四 | board=...§看板`；skip 形态单独识别。"""
    m = REG_RE.search("\n".join((text or "").split("\n")[:12]))
    if not m:
        return None
    body = m.group(1)
    skip = re.match(r"skip\b(.*)", body.strip())
    if skip:
        return {"skip": True, "reason": skip.group(1).strip() or "（未写原因）"}
    out = {"skip": False}
    for seg in re.split(r"[|｜]", body):
        if "=" in seg:
            k, v = seg.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def judge(path, body, exists):
    """返回 (verdict, detail)。verdict ∈ pass / block / exempt / skip-domain。"""
    if not in_domain(path) or exists:
        return "skip-domain", ""
    reg = parse_reg(body)
    if reg is None:
        return "block", "缺 `# REG:` 登记声明行"
    if reg.get("skip"):
        return "exempt", reg["reason"]
    miss = [f for f in FIELDS if not reg.get(f)]
    if miss:
        return "block", "REG 行缺字段 " + ",".join(miss)
    return "pass", " ".join(f"{f}={reg[f]}" for f in FIELDS)


def _record(path, verdict, detail):
    try:
        os.makedirs(os.path.dirname(JOURNAL), exist_ok=True)
        with open(JOURNAL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 "path": path, "verdict": verdict, "detail": detail},
                                ensure_ascii=False) + "\n")
    except OSError:
        pass


def extract(payload):
    if not isinstance(payload, dict):
        return "", ""
    ti = payload.get("tool_input") or payload.get("args") or {}
    if isinstance(ti, str):
        try:
            ti = json.loads(ti)
        except ValueError:
            return "", ""
    path = ti.get("file_path") or ti.get("path") or ti.get("target_file") or ""
    body = ""
    for key in ("content", "new_string", "newText", "text"):
        if isinstance(ti.get(key), str):
            body += ti[key] + "\n"
    return str(path), body


def reconcile():
    """核销：journal 里每条承诺，去它声明的 registry 落点查脚本名是否真登记。"""
    if not os.path.isfile(JOURNAL):
        print("✅ registry_precheck：无承诺台账（尚未有新建治理脚本落笔）")
        return 0
    done, owed, exempt = [], [], []
    seen = {}
    for l in open(JOURNAL, encoding="utf-8"):
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("verdict") in ("skip-domain",):
            continue
        seen[e["path"]] = e
    for path, e in sorted(seen.items()):
        name = os.path.basename(path)
        if e["verdict"] == "exempt":
            exempt.append((name, e["detail"]))
            continue
        if e["verdict"] != "pass":
            owed.append((name, "落笔时即被拦：" + e["detail"]))
            continue
        reg = dict(kv.split("=", 1) for kv in e["detail"].split(" ") if "=" in kv)
        hit = False
        for key in ("registry", "board"):
            target = (reg.get(key) or "").split("§")[0].strip()
            if not target:
                continue
            fp = target if os.path.isabs(target) else os.path.join(BASE, target)
            try:
                if os.path.isfile(fp) and name in open(fp, encoding="utf-8").read():
                    hit = True
            except OSError:
                pass
        (done if hit else owed).append((name, reg.get("registry", "?")))
    print(f"registry 回流核销：✅已登记 {len(done)} ｜ ⚠️未回流 {len(owed)} ｜ 🚪显式豁免 {len(exempt)}")
    for n, where in owed:
        print(f"  ⚠️ {n} → 承诺落点 {where} 未见登记（§3.0 三件套缺腿·请补文档或补 commit）")
    for n, reason in exempt:
        print(f"  🚪 {n} 豁免理由：{reason}")
    return 0            # 核销只显形不阻断（Hook 三纪律·⛔不把巡检做成绊马索）


def main(argv):
    if "--self-test" in argv:
        return self_test()
    if "--reconcile" in argv:
        return reconcile()
    if "--seed" in argv:                      # 存量收编：钩子上线前落盘的脚本，按其文件头已有的 REG 行补建承诺
        i = argv.index("--seed")
        for rel in argv[i + 1:]:
            fp = rel if os.path.isabs(rel) else os.path.join(BASE, rel)
            if not os.path.isfile(fp):
                print(f"  🚫 seed 跳过（文件不在盘）：{rel}")
                continue
            try:
                body = open(fp, encoding="utf-8").read()
            except OSError:
                continue
            v, d = judge(fp, body, False)
            if v in ("pass", "exempt"):
                _record(fp.replace(BASE + "/", ""), v, d)
                print(f"  ✅ seed：{os.path.basename(fp)} ← {v} {d}")
            else:
                print(f"  ⚠️ seed 拒收：{os.path.basename(fp)} 头部无合格 REG 行（{d}）→ 请补声明或改写 skip 理由")
        return 0
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        print("registry_precheck: payload 非 JSON → fail-open 放行", file=sys.stderr)
        return 0
    path, body = extract(payload)
    if not path:
        return 0
    v, d = judge(path, body, os.path.exists(path))
    if v == "skip-domain":
        return 0
    # 台账只收"承诺/豁免"两类；被拦的落笔没产出物，记进去＝永久假欠账（核销永远扫不平）
    if v in ("pass", "exempt"):
        _record(path.replace(BASE + "/", ""), v, d)
    if v == "block":
        print(f"⛔ [registry_precheck] 新建治理脚本未带登记承诺（§3.0 三件套·事前钩子）：{path}\n"
              f"   缺因：{d}\n"
              f"   改法：文件头加一行 `# REG: family=守卫|registry=记忆蓝图/…/守卫编写规范.md§四|board=记忆蓝图/…/03-进度看板.md`；\n"
              f"        确属不需登记（如临时探针）→ 改写 `# REG: skip <一句话原因>`（豁免会留痕可抽检，⛔静默放行）。\n"
              f"   ⛔不要静默卸载本钩子；改口径请改脚本并在 守卫编写规范 §3.0 留痕。", file=sys.stderr)
        return 2
    print(f"registry_precheck: {v} {path}")
    return 0


def self_test():
    """夹具测线上本体 judge()（§3.0·5）＋真变异（把域判据置假→新建脚本必不再被拦）。"""
    cases = [
        ("N1 新建守卫脚本带全 REG → pass", judge("/x/[记忆共享中心]/脚本中心/foo_guard.py", "# REG: family=守卫|registry=a.md§四|board=b.md", False)[0] == "pass"),
        ("N2 新建缺 REG → block", judge("/x/[记忆共享中心]/脚本中心/foo.py", "#!/usr/bin/env python3\nprint(1)", False)[0] == "block"),
        ("N3 REG 缺字段 → block", judge("/x/[记忆共享中心]/脚本中心/foo.py", "# REG: family=守卫", False)[0] == "block"),
        ("N4 显式豁免带原因 → exempt", judge("/x/[记忆共享中心]/脚本中心/foo.py", "# REG: skip 一次性探针·落盘后即删", False)[0] == "exempt"),
        ("N5 既有文件被改 → 不判（域外）", judge("/x/[记忆共享中心]/脚本中心/foo.py", "print(1)", True)[0] == "skip-domain"),
        ("N6 tests/ 夹具 → 不判", judge("/x/[记忆共享中心]/脚本中心/tests/t_foo.py", "print(1)", False)[0] == "skip-domain"),
        ("N7 治理域外（~/[记忆共享中心]/工作日志） → 不判", judge("/x/~/[记忆共享中心]/工作日志/a.py", "print(1)", False)[0] == "skip-domain"),
    ]
    bad = 0
    for name, ok in cases:
        print(("  ✅ " if ok else "  ❌ ") + name)
        bad += 0 if ok else 1
    global DOMAIN_RE
    live = DOMAIN_RE
    DOMAIN_RE = re.compile(r"(?!x)x")            # 变异：域判据永不命中 → N2 必须从 block 变 skip-domain
    try:
        mut = judge("/x/[记忆共享中心]/脚本中心/foo.py", "#!/usr/bin/env python3\nprint(1)", False)[0]
    finally:
        DOMAIN_RE = live
    print(f"  变异体 域判据置假 → N2 结果={mut}（应为 skip-domain＝判据已死，证原判据在干活）")
    print("MUT:" + ("OK" if (mut == "skip-domain" and bad == 0) else "FAIL") +
          f" 夹具 {len(cases) - bad}/{len(cases)}｜变异自证 1 例")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
