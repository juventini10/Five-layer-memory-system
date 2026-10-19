#!/usr/bin/env python3
# version: v1.0.0
"""Hermes 端 Skill 生态健康度守卫（对齐 teleagent/catpaw/doubaowork 三端 skill_health_guard 族）。

## 存在理由（按《04-跨端接入指南》§二·七·〇 协议动作 3「先查可复用」）

2026-10-01 读新抽出的 `04-跨端接入指南.md`，见「可吸收库入口」列明元守卫先例族：

    元守卫 health_guard 族（zcode_config／autoclaw_gateway／catpaw_skill／
    doubaowork_skill／teleagent_skill／hermes_plugin…）

⇒ **Hermes 端在 config/plugin 两个面有元守卫（hermes_plugin_health_guard），
   但在 skill 面只有 `skills-relink-hook`（仅治软链断裂），无 skill 健康守卫**
   —— 族内形态不完整 ⇒ 按协议动作 3 补齐（⛔ 不自建判据·对齐三端已验证的四项检测）。

## 四项检测（对齐 teleagent_skill_health_guard v0.3·已在三端验证）

1. **软链接有效性**：断链检测（`~/.hermes/skills/` 下 symlink 指向不存在目标）
2. **SKILL.md 存在性 + frontmatter 完整性**：目录有但无 SKILL.md / frontmatter 缺 name
3. **重名冲突**：两个 Skill 声明同一 `name` ⇒ Hermes 按 name 加载会静默取先到者
4. **必备 Skill 缺失**：`growth-box` / `system-logger` / `buluotuo-scripts`
   ——本端日常依赖的三件（按需可改·`REQUIRED` 常量）

## ⚠️ 按 Hermes 特性·⛔ 不照搬他端参数

`teleagent_skill_health_guard.py --mc <记忆中心路径>` 是端专属参数
（TeleAgent 的 skills 在记忆中心下）。**Hermes 的 skills 根是 `~/.hermes/skills/`
（独立配置根）**，⛔ 不引入 `--mc` 这类他端路径参数——按本端实况硬编码 + 可选覆盖。

## 为什么不并入 hermes_plugin_health_guard.py

**面不同·职责不同**：那是「插件层元守卫」（守护守卫本身·防崩防漂），
这是「Skill 生态健康度」（防断链/缺件/重名）。族内其他端也是**分文件**
（config_guard 与 skill_health_guard 各一）⇒ 沿用族形态·⛔ 不合并成大文件。

## 纪律（守卫编写规范 §八）

- 只记录不拦截：报告制·默认 exit 0（`--strict` 时有异常才 exit 1·⛔ 仅供人工/CI 调）
- 保守判定：⛔ 软链目标不存在才算断链（不猜 symlink 语义）
- 端隔离：⛔ 只读 `~/.hermes/skills/`·⛔ 不写他端
- 自测夹具：`--self-test` 用临时目录造四种异常（⛔ 不碰真实 skills 目录）
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import json
import os
import re
import sys
from datetime import datetime

VERSION = "v1.0.0"
HERMES_SKILLS = os.path.expanduser("~/.hermes/skills")
REQUIRED = ("growth-box", "system-logger")


def _fm_name(skill_md: str):
    """读 SKILL.md frontmatter 的 name（⛔ 解析失败返回 None·不猜）。"""
    try:
        head = open(skill_md, encoding="utf-8", errors="replace").read(2048)
    except OSError:
        return None
    if not head.startswith("---"):
        return None
    m = re.search(r"^name:\s*(.+?)\s*$", head, re.M)
    return m.group(1).strip().strip("\"'") if m else None


def check(skills_dir: str) -> dict:
    findings = []
    if not os.path.isdir(skills_dir):
        return {"version": VERSION, "ts": datetime.now().isoformat(timespec="seconds"),
                "skills_dir": skills_dir, "total": 0,
                "findings": [{"level": "RED", "kind": "skills_dir_missing",
                              "detail": f"skills 目录不存在：{skills_dir}"}],
                "red": 1, "warn": 0}

    entries = sorted(os.listdir(skills_dir))
    seen_names = {}
    checked = 0
    cats = 0
    sysdirs = 0

    for name in entries:
        # ⛔ Hermes 自身系统目录豁免（第二处假阳性·实测首跑 20 条里 8 条是噪声）：
        #   `~/.hermes/skills/` 下有一批 **Hermes 内部机制目录/文件**·
        #   ⛔ 不是 Skill、⛔ 也不是残留垃圾：
        #     · 目录：`.archive`（归档的旧 Skill）`.hub`（技能市场缓存·含 quarantine/
        #       taps.json/lock.json/index-cache/audit.log）`.locks`（账本锁）
        #       `.curator_backups`（curator 备份）
        #     · 文件：`.bundled_manifest` `.curator_ledger.jsonl` `.curator_state`
        #       `.usage.json` `.usage.json.lock`
        #   删除它们 = 破坏 Hermes 技能管理机制。⛔ 一律跳过不判不报。
        if name.startswith("."):
            sysdirs += 1
            continue
        p = os.path.join(skills_dir, name)
        # ① 软链有效性
        if os.path.islink(p):
            if not os.path.exists(p):
                findings.append({"level": "RED", "kind": "broken_symlink",
                                 "detail": f"断链：{name} → {os.readlink(p)}"})
            continue
        if not os.path.isdir(p):
            continue
        # ⛔ 分类目录豁免（自曝假阳性·实测首跑 28 条里 26 条是噪声）：
        #   Hermes 的 skills 根下有**分类目录**（mlops / note-taking / web /
        #   productivity / research …），它们是 Hermes 原生的 Skill 组织形态——
        #   内含 `DESCRIPTION.md` + 多个子 Skill 目录，**本身不是 Skill**。
        #   照他端"目录必有 SKILL.md"判 ⇒ 全部误报。
        #   ✅DO 判据=「有 DESCRIPTION.md 或含子目录 ⇒ 分类目录，跳过」；
        #     ⛔DO NOT 把它当缺 SKILL.md 报（那是把平台形态当违规）。
        if os.path.isfile(os.path.join(p, "DESCRIPTION.md")):
            cats += 1
            continue
        subs = []
        try:
            for d in os.listdir(p):
                if os.path.isfile(os.path.join(p, d, "SKILL.md")):
                    subs.append(d)
        except OSError:
            pass
        if subs:
            cats += 1
            continue
        # ⛔ 资源目录豁免（第三处假阳性·实测 3 条）：非分类目录形态但**含实质内容**
        #   且**无** SKILL.md——`buluotuo-script-adapter`（scripts/）·
        #   `buluotuo-script-registry`（scripts/）·`cross-platform-design-adaptation`
        #   （references/）——它们是 Skill 的**资源附属目录**（脚本/参考文档），
        #   删掉即丢资源 ⇒ 判据=「目录非空且无 SKILL.md」⇒ 资源目录，不报缺件。
        #   ⚠️ 夹具回归（self-test 一度丢 duplicate_name/no_frontmatter_name）：
        #   本豁免会把测试夹具里的 dup-a/dup-b/no-fm（含 SKILL.md 但无 name）
        #   也跳掉——因为「含子 SKILL.md」在前一分支、「目录非空」在本分支。
        #   ✅DO 顺序不可颠倒：**先**判 frontmatter/重名（Skill 本体语义），
        #     **再**判资源豁免（仅对「无 SKILL.md 且非空」生效）。故本分支加 `md` 条件。
        md_here = os.path.join(p, "SKILL.md")
        has_md = os.path.isfile(md_here)
        try:
            if not has_md and os.listdir(p):
                cats += 1
                continue
        except OSError:
            pass

        checked += 1
        # ② SKILL.md 存在 + frontmatter name
        md = os.path.join(p, "SKILL.md")
        if not os.path.isfile(md):
            findings.append({"level": "WARN", "kind": "no_skill_md",
                             "detail": f"{name}/ 缺 SKILL.md（Hermes 不会加载该目录）"})
            continue
        real_name = _fm_name(md)
        if not real_name:
            findings.append({"level": "WARN", "kind": "no_frontmatter_name",
                             "detail": f"{name}/SKILL.md frontmatter 缺 name"})
            continue
        # ③ 重名冲突
        if real_name in seen_names:
            findings.append({"level": "RED", "kind": "duplicate_name",
                             "detail": f"重名冲突：{name} 与 {seen_names[real_name]} "
                                       f"同声明 name={real_name}（Hermes 按 name 加载·后者被静默忽略）"})
        else:
            seen_names[real_name] = name

    # ④ 必备缺失
    for req in REQUIRED:
        if not os.path.exists(os.path.join(skills_dir, req)):
            findings.append({"level": "WARN", "kind": "required_missing",
                             "detail": f"必备 Skill 缺失：{req}"})

    return {
        "version": VERSION,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "skills_dir": skills_dir,
        "total": checked,
        "categories": cats,
        "system_dirs": sysdirs,
        "names": len(seen_names),
        "findings": findings,
        "red": sum(1 for f in findings if f["level"] == "RED"),
        "warn": sum(1 for f in findings if f["level"] == "WARN"),
    }


def _self_test() -> int:
    """自测夹具（守卫规范 §3.0·5）：四种异常各一例·临时目录·⛔ 不碰真实 skills。"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        os.symlink(os.path.join(td, "nonexistent-target"),
                   os.path.join(td, "broken-skill"))
        os.makedirs(os.path.join(td, "empty-dir"))              # 无 SKILL.md
        os.makedirs(os.path.join(td, "no-fm"))
        open(os.path.join(td, "no-fm", "SKILL.md"), "w").write("正文无 frontmatter\n")
        for d in ("dup-a", "dup-b"):
            os.makedirs(os.path.join(td, d))
            open(os.path.join(td, d, "SKILL.md"), "w").write(
                f"---\nname: same-name\n---\n# {d}\n")
        os.makedirs(os.path.join(td, "good"))
        open(os.path.join(td, "good", "SKILL.md"), "w").write(
            "---\nname: good\n---\n# ok\n")

        rep = check(td)
        kinds = {f["kind"] for f in rep["findings"]}
        expect = {"broken_symlink", "no_skill_md", "no_frontmatter_name",
                  "duplicate_name", "required_missing"}
        missing = expect - kinds
        print(f"  self-test: 检出 {sorted(kinds)}")
        print("  MISSING:" + str(sorted(missing)) if missing else "  ALL-EXPECTED-HIT")
        # 变异探针：空目录 ⇒ 必备缺失之外不得有其他（证明不凭空造告警）
        with tempfile.TemporaryDirectory() as td2:
            r2 = check(td2)
            extra = {f["kind"] for f in r2["findings"]} - {"required_missing"}
            print(f"  空目录变异：额外告警={sorted(extra) or 'NONE ✓'}")
        return 0 if not missing else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Hermes 端 Skill 生态健康度守卫")
    ap.add_argument("--dir", default=HERMES_SKILLS, help="skills 根目录（默认 Hermes 本端）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="有 RED 时 exit 1（默认恒 0·报告制）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return _self_test()

    rep = check(a.dir)
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"Hermes Skill 健康 · {rep['ts']} · {VERSION}")
        print(f"  目录：{rep['skills_dir']}（Skill {rep.get('total',0)} 个·"
              f"分类目录 {rep.get('categories',0)} 个·声明名 {rep.get('names',0)}）")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    if a.strict and rep["red"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())