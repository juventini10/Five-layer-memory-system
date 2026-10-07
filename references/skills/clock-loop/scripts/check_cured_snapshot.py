#!/usr/bin/env python3
"""check_cured_snapshot.py — 固化版本对账脚本（v2.0 自动扫描版）

自动扫描 clock-loop/references/ 下所有带 source/source_skill/source_path 字段的
.md/.yaml 文件（v3.48.0 起 yaml 纳入扫描域），与对应源文件版本号比对。不一致 = 固化过期 = clock-loop 正在用过期的尺子评估。

用法：
  python3 check_cured_snapshot.py
  → exit 0 = 全部一致
  → exit 1 = 有固化过期（输出差异清单到 stdout）

v2.0（2026-09-01）：从硬编码 CHECKS 列表改为自动扫描 references/ 目录——
新增固化引用文件不再需要手动加清单，零维护成本。
同时去除 PyYAML 依赖（改用 regex），纯 stdlib 运行，全工具端通用。

路径解析优先级：
  1. source_path: ~/xxx → 直接展开 ~
  2. source_skill: xxx → ~/[记忆共享中心]/技能配置/xxx/SKILL.md
  3. source: ~/xxx → 直接展开 ~（但排除 clock-loop 自身路径和 http URL）
  4. source: 中文名 + source_path → 用 source_path
  跳过：source 为 URL / source 指向 clock-loop 自身 / 无 version 字段
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import sys
import re
import os
from pathlib import Path

SKILL_BASE = Path(__file__).parent.parent  # clock-loop/
REFS = SKILL_BASE / "references"
HOME = Path.home()


def read_frontmatter_version(path: Path) -> str | None:
    """从 YAML frontmatter 读 version 字段（regex 解析，零依赖）"""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = parts[1]
    # 匹配 version: "x.y.z" / version: x.y.z / version: "vx.y.z" / version: v5.31（两段或三段）
    m = re.search(r'version:\s*["\']?(v?\d+\.\d+(?:\.\d+)?)["\']?\s*$', fm, re.MULTILINE)
    if m:
        return m.group(1)
    return None


def resolve_source_path(cured_path: Path) -> Path | None:
    """从固化文件的 frontmatter 解析源文件路径"""
    text = cured_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = parts[1]

    # 1. source_path: ~/xxx → 直接展开
    m = re.search(r'source_path:\s*(~[^\n]+)', fm)
    if m:
        p = m.group(1).strip().strip('"\'')
        p = p.replace('~', str(HOME))
        return Path(p)

    # 2. source_skill: xxx → ~/[记忆共享中心]/技能配置/xxx/SKILL.md
    m = re.search(r'source_skill:\s*(\S+)', fm)
    if m:
        skill_name = m.group(1).strip().strip('"\'')
        return HOME / "[记忆共享中心]" / "技能配置" / skill_name / "SKILL.md"

    # 3. source: ~/xxx → 直接展开（但排除 clock-loop 自身和 URL）
    m = re.search(r'source:\s*(~[^\n]+)', fm)
    if m:
        p = m.group(1).strip().strip('"\'')
        if 'clock-loop' in p:
            return None  # 自身路径，跳过
        p = p.replace('~', str(HOME))
        return Path(p)

    return None


def scan_current_version_lines(path: Path, src_ver: str) -> tuple[list[str], int]:
    """扫描固化文件正文的当前状态声明行版本滞后

    v3.48.0（#115 fail-open第三形态根治）：返回 (issues, matched_count)——
    matched_count=0 时调用方必须报"⚪无可比对"而非"一致"（零命中≠一致）。
    正则同时扩第三种格式 `> 版本：vN.N`（尾注式·6文件在用·#115实测）。
    """
    issues = []
    matched = 0
    if not path.exists():
        return [f"固化文件不存在: {path}"], 0
    text = path.read_text(encoding="utf-8")
    src_ver = src_ver.lstrip("v")
    pat = re.compile(
        r"(\*\*来源\*\*：\s*[^\s|]+\s*v(\d+\.\d+(?:\.\d+)?))"
        r"|(固化版本：\s*v(\d+\.\d+(?:\.\d+)?))"
        r"|(版本：\s*v(\d+\.\d+(?:\.\d+)?))"
    )
    for i, line in enumerate(text.splitlines(), 1):
        for m in pat.finditer(line):
            ver = m.group(2) or m.group(4) or m.group(6)
            matched += 1
            if ver != src_ver:
                issues.append(
                    f"  L{i}: 正文当前声明版本 v{ver} ≠ 源 v{src_ver}"
                    f"（{line.strip()[:60]}）"
                )
    return issues, matched


def main():
    errors = []
    checked = 0
    skipped = 0

    # 自动扫描 references/ 下所有 .md + .yaml 文件
    # v3.48.0（#205④逃脱路径第4条根治）：glob 扩为 md + **/*.yaml（含 eval-knowledge/ 子目录·
    # 权重权威源不再整体逃逸对账扫描域。⚠如实记：当前存量 yaml 均无 frontmatter version+source
    # → 走下方过滤仍为跳过＝本次为预防性覆盖扩大（A10-⑥同型·⛔不得声称新增检出）；
    # 未来任何带 frontmatter 的 yaml 固化文件自动纳入。
    if not REFS.is_dir():
        print(f"❌ references/ 目录不存在: {REFS}")
        sys.exit(1)

    cured_files = sorted(REFS.rglob("*.md")) + sorted(REFS.rglob("*.yaml"))  # v4.12.3·R3攻6：md与yaml同权rglob——旧顶层glob使子层固化件整体隐身
    for cured_path in cured_files:
        # 跳过 CHANGELOG（有自己版本体系）
        if cured_path.name == "CHANGELOG.md":
            continue

        fm_text = cured_path.read_text(encoding="utf-8")
        parts = fm_text.split("---", 2)
        if len(parts) < 3:
            continue  # 无 frontmatter，跳过

        fm = parts[1]

        # 必须有 version 字段才检查
        cured_ver = read_frontmatter_version(cured_path)
        if not cured_ver:
            continue

        # 必须有 source/source_skill/source_path 才检查
        if not any(k in fm for k in ['source:', 'source_skill:', 'source_path:']):
            continue

        # 解析源文件路径
        source_path = resolve_source_path(cured_path)
        if source_path is None:
            skipped += 1
            continue

        # 跳过 URL（http/https 开头的 source）
        source_str = str(source_path)
        if source_str.startswith('http'):
            skipped += 1
            continue

        name = cured_path.stem  # 文件名（不含 .md）

        src_ver = read_frontmatter_version(source_path)

        if src_ver is None:
            # 源文件不可达——记录但不计为错误
            # v4.12.2·R2-N-10：⚪不可达不计入分母（旧实现 checked+=1 早于本判定→"8项检查/1跳过+全绿"的分母含不可查项=fail-open第三形态残留·checked 与 skipped 双计）
            print(f"⚪ {name}: 源文件不可达（{source_path}）")
            skipped += 1
            continue
        checked += 1

        # 归一化比较
        src_norm = src_ver.lstrip("v")
        cured_norm = cured_ver.lstrip("v")

        if src_norm != cured_norm:
            errors.append(
                f"⚠️ {name}: 固化过期 —— 源 v{src_norm} ≠ 固化 v{cured_norm}"
                f"（{source_path.name}）"
            )
        else:
            print(f"✅ {name}: {src_ver} == {cured_ver}")
            # 正文当前声明行核对（v3.48.0：零命中→⚪无可比对·⛔不再把"没查到"当"一致"）
            body_issues, matched = scan_current_version_lines(cured_path, src_norm)
            if body_issues:
                for iss in body_issues:
                    errors.append(f"❌ {name}: {iss}")
            elif matched == 0:
                print(f"   ⚪ 正文无可核对版本声明行（零命中·无法核验≠一致·#115 fail-open第三形态防护）")
            else:
                print(f"   └ 正文当前声明行版本一致（命中{matched}处）")

    print(f"\n扫描完成：{checked} 项检查 / {skipped} 项跳过（URL/自身/无源路径）")

    if errors:
        print("\n".join(errors))
        print(f"\n🔴 固化版本对账失败：{len(errors)} 项不一致")
        print("→ 需重新固化到 clock-loop/references/ 并升 version")
        sys.exit(1)

    if checked == 0:
        print("⚪ 无可对账文件（0项）——不判全绿（v4.12.3·R3攻6：空集绿=集合绿与存在性绿混同）")
        # v4.17.0 C-01（双盲第11次）：文案承诺"不判全绿"此前未兑现——空集 exit 0 经
        # skill_eval L2993 returncode==0→cured_passed=True 传播=对账不可用时不阻断（fail-open）。
        # 修：空集 exit 2（=无法核验≠通过，#115 fail-open 同族第三形态收口）；正常态(checked>0)不受影响。
        sys.exit(2)
    else:
        print("✅ 固化版本全绿（%d 项）" % checked)
    sys.exit(0)


if __name__ == "__main__":
    main()
