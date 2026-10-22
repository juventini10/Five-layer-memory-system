#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布洛陀 Skill 合规检查器（专用 · 固化"规则不能架空"核查清单）

来源：2026-07-07 对 clock-loop v2.5.0 的合规检查——发现皮叔体系无官方校验脚本
（Anthropic quick_validate.py 只认 6 个标准字段，不认皮叔体系的扩展字段，直接报
"Unexpected key"）。每次改 Skill 只能手动核查。本脚本把本轮核查清单固化为可复跑检查，
覆盖《Skill设计模式.md》v5.8 与"规则不能架空"铁律（PAT-033）的核心要求：

  1. frontmatter 扩展字段登记视图（未知字段按文件格式规范 §127 宽容条款仅 WARN，不拒绝）
  2. Phase 每步 "✅DO" 命令锚点扫描（声明能力须有可 grep 执行锚点 → PAT-033）
  3. 引用脚本 py_compile（甩锅给解释器的真实可运行验证）
  4. CHANGELOG 版本一致性（SKILL.md version == CHANGELOG 最新条目）

用法：
  python3 validate_buluotuo_skill.py --skill-dir [记忆共享中心]/技能配置/clock-loop
  python3 validate_buluotuo_skill.py --selfcheck    # 仪器自检（正负夹具·2026-10-10 新增）
退出码：0=无 FAIL（可含 WARN） | 1=有 FAIL | 2=参数缺失

v2.2.0（2026-10-10 · Qoder CN · 门禁自噬案根治）：
  病案：10-07 判据重写（dc76404c 批·经 0928b513 auto-backup 落盘）在 CMD_ANCHORS 引入
  os.path.expanduser 却未 import os ⇒ 模块 import 即 NameError，skill-forge Step4 整条
  查侧静默死 3 天。py_compile 只查语法、查不到运行时缺名（=门禁的门禁缺位）。
  根治：①补 import os ②--selfcheck 正负夹具（仪器可运行性+判别力双证·S6 专锚
  CMD_ANCHORS 的 ~ 展开形状=本病的最小可证伪用例）③注册表行「负例实测待补」就此清账。
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

# 皮叔体系 frontmatter 已知字段集（登记视图·非拒绝清单）
# v2.1.0 (2026-08-29·对齐§127宽容条款): 未知字段由硬 FAIL 降为 WARN——
# 依据《文件格式规范》v2.4.0 §127 (2026-08-13): "消费者对未知键必须宽容保留、不得拒绝
# （对齐 OKF v0.2 宽容一致性）"。原注释声称来源=《Skill设计模式》扩展字段约定，
# 该约定在文件中查无实据=孤儿真相源，本版本起权威归属改为规范 §127。
# 本表保留"已知字段"视图职能：未知键进 WARN 提示登记与否，不再阻断。
# 2026-08-09 补：complies_with / normative_vocab 为文件格式规范 v2.0.0 标准字段
# （README/发布包/变换/守卫/引擎编写规范均使用；原 11 键缺此二字段，
#  导致所有符合 v2.0.0 的 Skill 误报"未知字段"）
ALLOWED_FM_KEYS = {
    "name", "description", "compatibility", "allowed-tools",
    "dependencies", "author", "source", "upstream", "modifiable",
    "version", "license", "complies_with", "normative_vocab",
    # 2026-10-21 你令收编（validate 滞后于规范演化型 WARN 两例·AIGC=国内合规标注字段，
    # requires_twin_on_duty=童灵 D3 上岗声明字段·clock-loop v4.19.0 批入规范实盘在先）：
    "AIGC", "requires_twin_on_duty",
    # 2026-10-21 皮叔令「收齐」：自有组件在用字段全量收编（实跑全库 validate 定数——
    # cured_snapshot=triwich/meta-aletheia 固化件声明·emoji/trigger/role=热点捕手/TimeLoom/excavator
    # 自定义触发与展示面·dependencies_note=TimeLoom 依赖备注·python_dependencies=sucair 依赖声明；
    # 第三方组件同类字段不在此列——口径只覆盖自有面）：
    "cured_snapshot", "emoji", "trigger", "role", "dependencies_note", "python_dependencies",
}

# ✅DO 步骤后需出现的命令锚点信号（启发式：声明能力不能只有空话）
CMD_ANCHORS = (
    "python3", "python ", "bash", "node ", "npm ", "```",
    os.path.expanduser("~"), "scripts/", ".py", "Read ", "Edit ", "Bash ", "Grep ",
)


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    return m.group(1) if m else None


def check_frontmatter(text: str):
    issues = []
    fm = parse_frontmatter(text)
    if fm is None:
        issues.append("FAIL frontmatter: 未找到 YAML frontmatter 块")
        return issues
    key_pat = re.compile(r'^([A-Za-z0-9_\-]+):', re.M)
    for k in key_pat.findall(fm):
        if k not in ALLOWED_FM_KEYS:
            issues.append(
                f"WARN frontmatter: 未知字段 '{k}'（不在已知字段登记视图；"
                f"按文件格式规范 §127 宽容条款不拒绝——建议评估是否登记入 ALLOWED_FM_KEYS）"
            )
    return issues


def check_phase_anchors(text: str):
    """只扫描 Phase 段内的 ✅DO 步骤，检查其步骤块是否含命令锚点（避免空心规则）。

    收窄范围：铁律声明段/关系表的 ✅DO 是行为准则，不含命令锚点属正常，不报。
    """
    warns = []
    lines = text.splitlines()
    # 计算 Phase 段范围（##/###/#### 标题含 "Phase" 即为段首）
    phase_ranges = []
    in_phase = False
    start = None
    for i, line in enumerate(lines):
        if re.match(r'^#{2,4}\s+.*Phase', line, re.I):
            if in_phase:
                phase_ranges.append((start, i - 1))
            in_phase = True
            start = i
        elif re.match(r'^#{2,4}\s+', line) and not re.search(r'Phase', line, re.I):
            if in_phase:
                phase_ranges.append((start, i - 1))
                in_phase = False
    if in_phase:
        phase_ranges.append((start, len(lines) - 1))

    do_lines = [i for i, l in enumerate(lines) if re.search(r'✅\s*DO', l)]
    headers = [i for i, l in enumerate(lines) if re.match(r'^#{2,4}\s+', l)]
    for di in do_lines:
        if not any(s <= di <= e for s, e in phase_ranges):
            continue  # 仅查 Phase 段内的 ✅DO
        # 步骤块范围：di 到 下一个 ✅DO / 下一个标题 / 文件末
        ends = [len(lines)]
        for j in do_lines:
            if j > di:
                ends.append(j)
                break
        for h in headers:
            if h > di:
                ends.append(h)
                break
        end = min(ends)
        block = "\n".join(lines[di:end])
        if not any(a in block for a in CMD_ANCHORS):
            warns.append(
                f"WARN 命令锚点缺失(Phase段): 行{di + 1} 的 ✅DO 其后步骤块未检测到"
                f"可执行命令锚点 → 可能空心规则（PAT-033）"
            )
    return warns


def _collect_script_refs(text: str):
    r"""从 frontmatter 的 dependencies 字段收集 .py 脚本路径（唯一权威来源）。

    支持 flow 列表 `[a, b]` 与 block 列表 `- a` 两种 YAML 风格。
    旧版对整篇文本做脆弱正则（[^\s`]+\.py），遇到
    `dependencies: [scripts/x.py, ...]` 会把开头的 '[' 吞进路径
    → 误判 [scripts/x.py 不存在。现改为只解析 dependencies 字段，
    彻底消除此类误报（方案 X），且不动任何 Skill 内容。
    """
    refs = set()
    fm = parse_frontmatter(text)
    if not fm:
        return refs
    lines = fm.splitlines()
    in_block = False
    for line in lines:
        if re.match(r'^dependencies\s*:', line):
            val = line.split(":", 1)[1].strip()
            if val.startswith("["):
                for part in val.strip("[]").split(","):
                    part = part.strip().strip('"').strip("'")
                    if part:
                        refs.add(part)
            else:
                in_block = True
            continue
        if in_block:
            if re.match(r'^\s*-\s+', line):
                refs.add(re.sub(r'^\s*-\s+', '', line).strip()
                         .strip('"').strip("'"))
            elif re.match(r'^[A-Za-z0-9_-]+:', line):
                in_block = False
    return refs


def check_scripts_compile(skill_dir: Path, text: str):
    fails = []
    py_refs = _collect_script_refs(text)
    if not py_refs:
        return fails
    # 2026-08-09 修：硬编码本机绝对路径→sys.executable（六端通用；原路径
    # ~/.workbuddy/... 在非本机不存在，破坏六端兼容声明）
    py = Path(sys.executable)
    for ref in sorted(py_refs):
        ref = ref.strip().strip('"').strip("'")
        if not ref or ".py" not in ref:
            continue
        p = Path(ref).expanduser()
        if not p.is_absolute():
            p = skill_dir / ref
        if not p.exists():
            fails.append(f"FAIL 脚本不存在: {ref}")
            continue
        r = subprocess.run([str(py), "-m", "py_compile", str(p)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append(f"FAIL 脚本编译失败: {ref}\n{r.stderr.strip()}")
    return fails


def check_changelog_version(skill_dir: Path, text: str):
    fails = []
    m = re.search(r'^version:\s*"([^"]+)"', text, re.M)
    if not m:
        fails.append("FAIL 版本: SKILL.md 未找到 version 字段")
        return fails
    ver = m.group(1)
    cl = skill_dir / "references" / "CHANGELOG.md"
    if not cl.exists():
        fails.append("WARN CHANGELOG: references/CHANGELOG.md 不存在，跳过版本比对")
        return fails
    ents = re.findall(r'^#{2,3}\s+v([\d.]+)', cl.read_text(encoding="utf-8"), re.M)  # v1.1·2026-10-11 你令修复：库史格式为 ## v（42条·### v 零条）——两级标题同准入
    if not ents:
        fails.append("WARN CHANGELOG: 无版本条目")
        return fails
    # v前缀归一（2026-10-10 案：triwich SKILL.md=v4.5.2 vs CHANGELOG 捕获"4.5.2"永假红
    # ——提取正则 `### v([\d.]+)` 已吃掉 v，比较侧不吃=判据两侧不对称。假红烧报警信用
    # （岗位3 v1.9 同族教训）；归一后比较，展示保留原值。）
    if ents[0] != ver.lstrip("v"):
        fails.append(f"FAIL 版本不一致: SKILL.md={ver} CHANGELOG最新={ents[0]}")
    return fails


def _t(name, cond):
    print(("  ✅ " if cond else "  🔴 ") + name)
    return bool(cond)


def selfcheck():
    """仪器自检：正例必须绿、负例必须红、形状判据必须可证伪（2026-10-10）。
    夹具全在临时目录，⛔不碰任何真 Skill。"""
    import tempfile
    import shutil
    bad = 0
    tmp = tempfile.mkdtemp(prefix="validate-selfcheck-")
    try:
        good = Path(tmp) / "good"
        (good / "references").mkdir(parents=True)
        (good / "SKILL.md").write_text(
            '---\nname: g\ndescription: d\nversion: "v1.0.0"\n---\n'
            '## Phase 1\n\n✅DO 运行脚本\n\n```bash\npython3 scripts/a.py\n```\n',
            encoding="utf-8")
        (good / "references" / "CHANGELOG.md").write_text("### v1.0.0\n- init\n", encoding="utf-8")
        tg = (good / "SKILL.md").read_text(encoding="utf-8")
        f1 = ([i for i in check_frontmatter(tg) if i.startswith("FAIL")]
              + check_scripts_compile(good, tg) + check_changelog_version(good, tg))
        w1 = check_phase_anchors(tg)
        if not _t("S1 正例·合法最小Skill→FAIL=0", not f1):
            bad += 1
        if not _t("S2 正例·bash 围栏命令锚点不误报", not w1):
            bad += 1
        badskill = Path(tmp) / "bad"
        (badskill / "references").mkdir(parents=True)
        (badskill / "SKILL.md").write_text(
            '---\nname: b\ndescription: d\nversion: "2.0.0"\nrogue_key: x\n'
            'dependencies: [scripts/nope.py]\n---\n'
            '## Phase 1\n\n✅DO 做得漂亮\n', encoding="utf-8")
        (badskill / "references" / "CHANGELOG.md").write_text("### v1.9.9\n- old\n", encoding="utf-8")
        tb = (badskill / "SKILL.md").read_text(encoding="utf-8")
        f2 = ([i for i in check_frontmatter(tb) if i.startswith("FAIL")]
              + check_scripts_compile(badskill, tb) + check_changelog_version(badskill, tb))
        w2 = check_frontmatter(tb) + check_phase_anchors(tb)
        if not _t("S3 负例·版本不一致+缺脚本→FAIL≥2", len(f2) >= 2):
            bad += 1
        if not _t("S4 负例·未知字段→WARN不阻断(§127宽容)",
                  any("rogue_key" in i for i in w2 if i.startswith("WARN"))):
            bad += 1
        if not _t("S5 负例·空心✅DO→命令锚点WARN", any("命令锚点" in i for i in w2)):
            bad += 1
        # S6 本病专锚（10-10 NameError 复发病的最小可证伪用例）：
        # CMD_ANCHORS 里的 "~" 令牌必须由 os.path.expanduser 真实解析——
        # os 未 import 时本函数体根本进不到这里（import 期即崩）⇒ S6 存在本身=烟测。
        # （首跑S6即红逮到我判据写错：元组存的是展开后的家路径非"~"字面——
        #    selfcheck 判别力当场自证。正确形状=元组里存在 expanduser 的展开结果。）
        if not _t("S6 CMD_ANCHORS含展开后家路径（NameError案专防·import期expanduser已真执行=烟测）",
                  os.path.expanduser("~") in CMD_ANCHORS):
            bad += 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("=== validate 自检 %d/%d 通过 ===" % (6 - bad, 6))
    return bad == 0


def main():
    ap = argparse.ArgumentParser(description="布洛陀 Skill 合规检查器")
    ap.add_argument("--skill-dir", required=False, help="Skill 目录（含 SKILL.md）")
    ap.add_argument("--selfcheck", action="store_true",
                    help="仪器自检（正负夹具6例·v2.2.0·不碰真Skill）")
    args = ap.parse_args()
    if args.selfcheck:
        sys.exit(0 if selfcheck() else 1)
    if not args.skill_dir:
        print("ERROR: 需要 --skill-dir 或 --selfcheck", file=sys.stderr)
        sys.exit(2)
    sd = Path(args.skill_dir).expanduser()
    skill = sd / "SKILL.md"
    if not skill.exists():
        print(f"ERROR: {skill} 不存在", file=sys.stderr)
        sys.exit(1)
    text = skill.read_text(encoding="utf-8")

    print(f"=== 布洛陀 Skill 合规检查: {sd.name} ===\n")
    fm_issues = check_frontmatter(text)
    fm_fails = [i for i in fm_issues if i.startswith("FAIL")]
    fm_warns = [i for i in fm_issues if not i.startswith("FAIL")]
    phase_warns = check_phase_anchors(text)
    script_fails = check_scripts_compile(sd, text)
    ver_fails = check_changelog_version(sd, text)

    all_fail = fm_fails + script_fails + ver_fails
    all_warn = fm_warns + phase_warns
    for it in all_fail:
        print(it)
    for it in all_warn:
        print(it)

    if not all_fail and not all_warn:
        print("✅ 全部通过（frontmatter合法 + 命令锚点齐全 + 脚本编译OK + 版本一致）")
    elif not all_fail:
        print(f"\n⚠️ 通过但有 {len(all_warn)} 个 WARN（见上，不阻断）")
    else:
        print(f"\n❌ 有 {len(all_fail)} 个 FAIL")

    print(f"\n统计: FAIL={len(all_fail)} WARN={len(all_warn)}")
    sys.exit(1 if all_fail else 0)


if __name__ == "__main__":
    main()
