#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: skip 包自检判据件（verify.sh/verify.ps1 双端共用检查器·mirror登记 scripts-verify-pair-checks-py），
#      非守卫族常驻监听件；版本纪律随安装包 CHANGELOG（同 path_integrity_check.py 形态先例）。
"""verify_pair_checks.py — 安装包双端共用检查器（平台中立单源·检查⑬孪生形状对账+三缺腿判据）

先例判据：twin_chain_check.py/slice_chain_check.py「双端 verify 共用包内 py，⛔不各端手搓」。
本案定位（任务卡 2026-10-21-verify双端同构缺腿与孪生对账规则）：
  ① verify.sh §3.0/§4.6/§4.7 三面手搓 bash 判据下沉本 py（verify.sh 改调用=行为零变更，
     verify.ps1 补同名段调用=Win 端从失明转在场）；
  ② 检查⑬「孪生形状对账」本体：读包内 references/twin-sections.json 台账，
     对每个 .sh↔.ps1 孪生对比对「已登记中立段单侧缺席=红」「任一端出现未登记新段=红」
     「专属段缺 basis=红（⛔空壳豁免·承 platform-exemptions 同规）」。
真源：脚本中心/守卫/（与 platform_compat 同树·mirror 投影包内 references/{scripts,hooks,digital-twin/devtools}/）。
纪律：标准库 only；只读不写；输出单行机器形（调用方映射 ok/no）；仪器故障与判据红分态
     （⛔把仪器故障伪装成判据结论=verify.sh §4.7 2026-10-18 教训同款）。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import json
import re
import sys
from pathlib import Path

EXIT_OK, EXIT_FAIL, EXIT_INSTRUMENT = 0, 1, 2


# ───────────────────────── ①三缺腿判据（自 verify.sh 逐段移植·行为零变更） ─────────────────────────

def skill_present(pkg_skill_dir: Path, root_dir: Path) -> int:
    """§3.0 Skill 落点三口径判定：目录名直配 / frontmatter name 直配 / 扫描目标目录 SKILL.md frontmatter。
    病形（10-03 根治）：端用户本地以中文别名目录部署，按 basename 直配把「已装」误报「缺失」。
    返回 0=在场 1=缺席（exit 语义与 bash 版 _skill_present 逐字一致）。"""
    name = pkg_skill_dir.name
    if (root_dir / name).exists():
        return 0
    fm = _frontmatter_name(pkg_skill_dir / "SKILL.md")
    if fm and (root_dir / fm).exists():
        return 0
    if fm:
        for d in root_dir.iterdir() if root_dir.is_dir() else []:
            if not d.is_dir():
                continue
            if _frontmatter_name(d / "SKILL.md") == fm:
                return 0
    return 1


def _frontmatter_name(skill_md: Path) -> str:
    """取 SKILL.md frontmatter 首个 name: 值（剥引号·截空白），与 sh 的 sed 口径一致。"""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    m = re.search(r"^name:[ \t]*[\"']?([^\"' \t\n]+)", text, re.M)
    return m.group(1) if m else ""


SKELETON_DIRS = ("记忆蓝图", "最伟大的我", "未知未知", "成就系统", "记忆琥珀")


def skeleton_check(mc: Path) -> int:
    """§4.6 目录型骨架 存在∧非空（C16·10-14）。断言取 ≥1 ⛔硬编码件数（老用户删减=正常态）。
    病形：step3 预建空目录 + step5「目录是否存在」判跳过 → 模板永不落盘一路绿灯。"""
    fails = []
    for name in SKELETON_DIRS:
        d = mc / name
        if not d.is_dir():
            fails.append(f"缺失 {name}/（step3建目录或step5整目录复制未执行）")
            continue
        n = sum(1 for p in d.rglob("*") if p.is_file())
        if n < 1:
            fails.append(f"空壳 {name}/ 目录在位但0文件（旧判据'目录是否存在'在此谎报通过）")
    if fails:
        print("DETAILS=" + " ; ".join(fails))
        return EXIT_FAIL
    print("OK %d 处全过（存在∧非空）" % len(SKELETON_DIRS))
    return EXIT_OK


TABLE_RE = re.compile(r"^\|\s*(Q\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")


def summary_tables(tpl_path: Path, inst_path) -> int:
    """§4.7 摘要版三表占位符闭环（C08·双向：出厂纯净 + 装机注入完整）。
    输出单行：ROWS=<n> BAD=<非占位符格数|逗号清单> LEFT=<装机残留数|NA>
    rc=2 仪器未跑（模板不可读等）——⛔不得伪装成污染结论（10-18 教训）。"""
    if not tpl_path.is_file():
        print("INSTRUMENT=模板不可读 %s" % tpl_path)
        return EXIT_INSTRUMENT
    n, bad = 0, []
    try:
        for i, line in enumerate(tpl_path.read_text(encoding="utf-8").splitlines(), 1):
            m = TABLE_RE.match(line)
            if not m:
                continue
            n += 1
            q, ans, rule = m.group(1), m.group(3).strip(), m.group(4).strip()
            if ans != "[%s·答案待注入]" % q or rule != "[%s·规则待派生]" % q:
                bad.append("L%d %s" % (i, q))
    except OSError as exc:
        print("INSTRUMENT=模板读取异常 %s" % exc)
        return EXIT_INSTRUMENT
    left = "NA"
    if inst_path:
        p = Path(inst_path)
        if p.is_file():
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                left = str(len(re.findall(r"\[Q\d+·(?:答案待注入|规则待派生)\]", txt)))
            except OSError:
                pass
    print("ROWS=%d BAD=%s LEFT=%s" % (n, ",".join(bad) if bad else "0", left))
    # rc 只反映模板纯净（19行全占位）；LEFT 判定由调用方映射（与 sh 两段输出结构一致）
    return EXIT_OK if (n == 19 and not bad) else EXIT_FAIL


# ───────────────────────── ② 检查⑬ 孪生形状对账（platform_compat 消费） ─────────────────────────

def sections_of(filepath: Path, pattern: str):
    """按台账给定正则在文件内扫「检查段号」集合。返回 set。
    容噪：段号集合去重——头注释清单行命中的号必落在正文真实段号内，不虚增。"""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    return set(m.group(1) for m in re.finditer(pattern, text, re.M))


def twin_check(pkg: Path, ledger_path=None):
    """检查⑬主体：包内 references/twin-sections.json 台账 vs 两端文件实际段集合。
    返回 issues 列表（platform_compat 检查函数同形·空=通过）。
    判据三向：中立段单侧缺席=红 / 任一端未登记新段=红 / 专属段无 basis=红。"""
    issues = []
    lp = Path(ledger_path) if ledger_path else pkg / "references" / "twin-sections.json"
    if not lp.exists():
        return ["孪生台账缺失: %s（检查⑬判据数据面=references/twin-sections.json·随源投影）" % lp.name]
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ["孪生台账解析失败（不静默吞）: %s" % exc]
    pairs = data.get("pairs", [])
    if not pairs:
        return ["孪生台账 pairs 为空（登记制失效=假绿仪器）"]
    for pair in pairs:
        shp, psp = pkg / pair["sh"], pkg / pair["ps1"]
        label = "%s↔%s" % (pair["sh"], pair["ps1"])
        for f in (shp, psp):
            if not f.exists():
                issues.append("%s 孪生件不可读: %s" % (label, f.name))
        if not shp.exists() or not psp.exists():
            continue
        pat = pair.get("section_pattern", r"^#\s*(\d+\.\d+[a-z]?|\d+)\)")
        s_sh, s_ps = sections_of(shp, pat), sections_of(psp, pat)
        if s_sh is None or s_ps is None:
            issues.append("%s 仪器未跑（读取失败·⛔不当判据绿）" % label)
            continue
        neutral = set(pair.get("neutral", []))
        sh_only = {r.get("section"): r for r in pair.get("sh_only", [])}
        ps_only = {r.get("section"): r for r in pair.get("ps1_only", [])}
        known = neutral | set(sh_only) | set(ps_only)
        # 面1：已登记中立段单侧缺席
        for sec in sorted(neutral - s_sh):
            issues.append("%s 中立段 Mac 侧缺席: §%s（判据平台中立·⛔一端失明=用户端假绿继承）" % (label, sec))
        for sec in sorted(neutral - s_ps):
            issues.append("%s 中立段 Win 侧缺席: §%s（判据平台中立·⛔一端失明=用户端假绿继承）" % (label, sec))
        # 面2：未登记新段（单向加段必被逮——本判据的反漂移灵魂）
        for sec in sorted(s_sh - known):
            issues.append("%s Mac 侧新增未登记段 §%s（须入台账分类：neutral 双端补建 / *_only 附 basis）" % (label, sec))
        for sec in sorted(s_ps - known):
            issues.append("%s Win 侧新增未登记段 §%s（须入台账分类·同上）" % (label, sec))
        # 面3：专属豁免须有依据（⛔空壳豁免=把假绿从清单搬进台账·承 platform-exemptions 同规）
        for book, s_set, side in (("sh_only", s_sh, "Mac"), ("ps1_only", s_ps, "Win")):
            for sec, rec in sorted((sh_only if book == "sh_only" else ps_only).items()):
                if not rec or not str(rec.get("basis", "")).strip():
                    issues.append("%s %s 侧专属段 §%s 无 basis（空壳豁免=同罪·须机械依据如 launchd/osascript/平台差异告知）"
                                  % (label, side, sec))
                if sec not in s_set:
                    issues.append("%s %s 侧专属段 §%s 台账在册但文件里已不存在（台账须随实盘清账）" % (label, side, sec))
    return issues


# ───────────────────────── CLI ─────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cmd = args[0]
    if cmd == "skill-present" and len(args) == 3:
        return skill_present(Path(args[1]), Path(args[2]))
    if cmd == "skeleton" and len(args) == 2:
        return skeleton_check(Path(args[1]))
    if cmd == "summary-tables" and len(args) >= 2:
        return summary_tables(Path(args[1]), args[2] if len(args) > 2 else None)
    if cmd == "twin" and len(args) >= 2:
        iss = twin_check(Path(args[1]), args[2] if len(args) > 2 else None)
        for i in iss:
            print("TWIN-ISSUE:", i)
        return EXIT_FAIL if iss else EXIT_OK
    if cmd == "sections" and len(args) == 2:
        s = sections_of(Path(args[1]), r"^#\s*(\d+\.\d+[a-z]?|\d+)\)")
        print(",".join(sorted(s)) if s else "INSTRUMENT=none")
        return EXIT_OK if s else EXIT_INSTRUMENT
    print("用法: skill-present <pkg_skill_dir> <root> | skeleton <mc> | summary-tables <tpl> [inst] | twin <pkg> | sections <file>")
    return 2


if __name__ == "__main__":
    sys.exit(main())
