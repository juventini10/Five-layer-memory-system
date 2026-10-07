#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_selfcontained_guard.py —— Skill 自包含守卫（跨目录引用机械体检）
Version: 1.0.1 (2026-09-15)

主矛盾（皮叔 2026-09-15 质询 + 令「全面检查所有 Skill · 从根本上杜绝」）：
  Skill 里的文件引用**宿主系统层路径**（`[记忆共享中心]/脚本中心/…` / `发布库/…` / 另一个 Skill）
  ⇒ 换机或开源即断链（Skill架构规范 §11.5 开放引用原则 + §11.6 自包含 litmus test）。
  人工判读不可持续（实测：初扫命中 30+ 处，其中真引用与测试样本混在一起）→ **机制化**。

判据（机械·可判定）：
  ① 越界路径引用 = 文本中出现 `[记忆共享中心]/脚本中心` / `~/[记忆共享中心]/发布库` / `技能配置/<别的Skill名>`
  ② **合规豁免**（四类，逐条机械可判）：
     - **声明豁免**：该 Skill 内有「依赖清单」节（标题含 依赖/自包含/发布自包含），且该路径出现在该节内
     - **样本豁免**：命中行处于测试/样本上下文（含 样本|示例|夹具|正例|负例|selftest|_test|tests/ 等标记）
     - **自身豁免**：路径指向本 Skill 自己（`技能配置/<self>/`）
     - **生成物豁免**（v1.0.1）：`.{*}_last_run.json` 运行时状态点文件——脚本输出物（内容=机器证据缓存，
       逐次运行重写），非 Skill 作者书写的引用，不可声明亦不可改写（CHANGELOG 同族）
  ③ 剩下未豁免的 → **违规**（报告 file:line + 路径）

⛔ 本守卫只报告，不改文件——修法（登记依赖清单 or 去路径）由人/Skill 决定。
⛔ 不阻断（exit 0）——Hook 纪律；退出码语义：0=无违规·1=有违规（供 CI/巡检消费）。

用法：
  python3 skill_selfcontained_guard.py            # 人类可读报告
  python3 skill_selfcontained_guard.py --json     # 结构化
  python3 skill_selfcontained_guard.py --check    # 仅 alar m 行（供 registry_guards 契约）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import json
import os
import re
import sys

VERSION = "1.0.1"
HOME = os.path.expanduser("~")
SKILL_ROOT = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", "技能配置")

# v1.0.1：排除类补 `}`——shell 变量展开 `${VAR:-~/…/布洛陀-安装包}` 的闭合花括号曾被吞进路径，
# 产生 `布洛陀-安装包}` 脏命中（把 Skill 文本改写去迁就正则瑕疵=尾巴 wagging the dog，修正则）。
OUTSIDE_RX = re.compile(r"(?:~|\$HOME)?/?个人AI档案/(?:开发工具|发布库)[^\s`'\"|)）}]*")
OTHER_SKILL_RX = re.compile(r"~/[记忆共享中心]/技能配置/([^/\s`'\"|)）]+)")
SAMPLE_RX = re.compile(r"样本|示例|夹具|正例|负例|selftest|_test|tests/|test_|实测形态|形态样本")
# frontmatter 元数据行豁免：upstream/source/related 等字段是**描述性元数据**（说明本 Skill 的真源或关联），
# 不是运行时路径引用——2026-09-15 实测 `upstream: ~/[记忆共享中心]/技能配置/（皮叔 Skill 真源）` 被误报（第 5 例）。
FM_RX = re.compile(r"^\s*(upstream|source|related|compatibility|dependencies|modifiable|author|allowed-tools):")
DECL_RX = re.compile(r"^#{1,4}.*(依赖|自包含)")

SCAN_EXT = (".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".json")
SKIP_DIRS = {"__pycache__", ".git", "归档", "archived", ".DS_Store"}


def skill_dirs():
    if not os.path.isdir(SKILL_ROOT):
        return []
    out = []
    for name in sorted(os.listdir(SKILL_ROOT)):
        p = os.path.join(SKILL_ROOT, name)
        if not os.path.isdir(p) or name in SKIP_DIRS or name.startswith("."):
            continue
        if os.path.isfile(os.path.join(p, "SKILL.md")):
            out.append((name, p))
    return out


def declaration_block(text):
    """返回依赖声明节的全部文本（标题含 依赖/自包含 的章节，直到下一个同级或更高级标题）。"""
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        m = DECL_RX.match(lines[i])
        if m:
            level = len(lines[i]) - len(lines[i].lstrip("#"))
            j = i + 1
            while j < len(lines):
                if re.match(r"^#{1,4} ", lines[j]):
                    lv = len(lines[j]) - len(lines[j].lstrip("#"))
                    if lv <= level:
                        break
                j += 1
            blocks.append("\n".join(lines[i:j]))
            i = j
            continue
        i += 1
    return "\n".join(blocks)


def iter_files(skill_dir, limit=400):
    """> 遍历待检文件。**测试夹具整文件豁免**——`tests/` 目录与 `test_*.py` 里的
    > 路径是**样本字面量**（不要求文件真实存在），报它们=假阳性（2026-09-15 实测：
    > growth-box 的 10 处命中全是 `test_antibody_gate.py` 与 `--selftest` 的正例样本）。"""
    n = 0
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith(SCAN_EXT):
                continue
            if fn.startswith("test_") or "selftest" in fn or os.sep + "tests" + os.sep in dirpath + os.sep:
                continue
            if fn.upper().startswith("CHANGELOG"):
                continue                  # 变更记录=历史事实（记当时引了什么），⛔不改写历史、不报
            if re.match(r"^\..*_last_run\.json$", fn):
                continue                  # v1.0.1 生成物豁免：脚本运行时状态点文件（.phaseX_last_run.json 等），
                                          # 内容=机器证据缓存逐次重写，非作者书写引用——报告它=假阳性（2026-09-15 实测）
            n += 1
            if n > limit:
                return
            yield os.path.join(dirpath, fn)


DEF_RX = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)")


def _enclosing_func(lines, idx):
    """向上找最近的 def 名——用于豁免脚本内 selftest/sample 函数里的样本字面量。"""
    for j in range(idx, -1, -1):
        m = DEF_RX.match(lines[j])
        if m:
            return m.group(1)
    return ""


def _norm(p):
    """路径归一：去掉 ~/、$HOME/、/ 与「个人AI档案/」前缀——使声明节里的简写
    与命中行里的完整写法能对上（2026-09-15 实测：声明写 `开发工具/x.sh`、
    命中写 `[记忆共享中心]/脚本中心/x.sh`，字符串不等 → 假阳性未豁免·同族第 6 例）。"""
    s = p.replace("$HOME/", "").replace("~/", "").lstrip("/")
    if s.startswith("个人AI档案/"):
        s = s[len("个人AI档案/"):]
    return s


def scan_skill(name, path):
    decl = ""
    sk = os.path.join(path, "SKILL.md")
    try:
        decl = _norm(declaration_block(open(sk, encoding="utf-8", errors="replace").read()))
    except OSError:
        pass

    hits = []
    for fp in iter_files(path):
        rel = os.path.relpath(fp, SKILL_ROOT)
        try:
            lines = open(fp, encoding="utf-8", errors="replace").read().split("\n")
        except OSError:
            continue
        for ln, line in enumerate(lines, 1):
            paths = OUTSIDE_RX.findall(line)
            other = [m for m in OTHER_SKILL_RX.findall(line) if m != name]
            if other:
                for o in other:
                    paths.append("~/[记忆共享中心]/技能配置/%s" % o)
            if not paths:
                continue
            if SAMPLE_RX.search(line):
                continue                      # 行级样本豁免
            if FM_RX.match(line):
                continue                      # frontmatter 元数据豁免（描述性字段·非引用）
            fn_name = _enclosing_func(lines, ln - 1)
            if "selftest" in fn_name or "sample" in fn_name or "fixture" in fn_name or "_test" in fn_name:
                continue                      # 函数级样本豁免（脚本内 selftest 样本）
            undeclared = [p for p in paths if _norm(p) not in decl]
            if not undeclared:
                continue                      # 声明豁免
            hits.append({"file": rel, "line": ln, "paths": sorted(set(undeclared)),
                         "text": line.strip()[:110]})
    return hits


def main():
    argv = sys.argv[1:]
    skills = skill_dirs()
    report = {"version": VERSION, "skills": len(skills), "violations": [], "clean": []}
    for name, path in skills:
        hits = scan_skill(name, path)
        if hits:
            report["violations"].append({"skill": name, "count": len(hits), "hits": hits})
        else:
            report["clean"].append(name)
    report["total"] = sum(v["count"] for v in report["violations"])
    report["alarm"] = report["total"] > 0

    if "--check" in argv:
        print(json.dumps({"alarm": report["alarm"], "version": VERSION,
                          "skills": report["skills"], "total": report["total"]}, ensure_ascii=False))
        return 1 if report["alarm"] else 0
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["alarm"] else 0

    print("🔍 Skill 自包含体检 v%s · 扫描 %d 个 Skill" % (VERSION, report["skills"]))
    if not report["violations"]:
        print("✅ 全部 Skill 通过：无未声明的跨目录引用")
        return 0
    print("⚠️ %d 个 Skill 存在未声明的跨目录引用（共 %d 处）" % (len(report["violations"]), report["total"]))
    for v in report["violations"]:
        print("\n  ▸ %s（%d 处）" % (v["skill"], v["count"]))
        for h in v["hits"][:6]:
            print("     %s:%d  → %s" % (h["file"], h["line"], ", ".join(h["paths"])[:80]))
        if v["count"] > 6:
            print("     …… 另 %d 处" % (v["count"] - 6))
    print("\n  处置二选一：① 在 SKILL.md 增「依赖清单」节登记该路径（诚实声明降级/随包携带）")
    print("              ② 去掉路径改写中性表述（若本就不该引）")
    print("  ✅ 通过：%d 个（%s）" % (len(report["clean"]), "、".join(report["clean"][:8]) + ("…" if len(report["clean"]) > 8 else "")))
    return 1


if __name__ == "__main__":
    sys.exit(main())
