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
  python3 validate_buluotuo_skill.py --skill-dir ~/[记忆共享中心]/技能配置/clock-loop
退出码：0=无 FAIL（可含 WARN） | 1=有 FAIL
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
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
    ents = re.findall(r'^###\s+v([\d.]+)', cl.read_text(encoding="utf-8"), re.M)
    if not ents:
        fails.append("WARN CHANGELOG: 无版本条目")
        return fails
    if ents[0] != ver:
        fails.append(f"FAIL 版本不一致: SKILL.md={ver} CHANGELOG最新={ents[0]}")
    return fails


def main():
    ap = argparse.ArgumentParser(description="布洛陀 Skill 合规检查器")
    ap.add_argument("--skill-dir", required=True, help="Skill 目录（含 SKILL.md）")
    args = ap.parse_args()
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
