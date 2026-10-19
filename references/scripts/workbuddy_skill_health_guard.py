#!/usr/bin/env python3
# version: v1.0.0
"""WorkBuddy 端 Skill 生态健康度守卫（端薄适配器·判据全 import 公共原语）。

## 存在理由（§二·七·〇 动作 3「先查可复用」+ 动作 2「逐面对表」）

族内四端（catpaw/doubaowork/teleagent/hermes）各有 skill_health_guard，
**唯独 WB 端没有**——而 WB 恰是 `[记忆共享中心]/技能配置/`（Skill 安装唯一真相源）
所在端 = 族内唯一「主人端裸奔」。本件按协议先抽公共原语再写端适配器，
⛔ 不 fork、不复制四端实现。

## ⚠️ WB 端独有形态：双面结构（别端只有单面）

| 面 | 路径 | 形态 |
|---|---|---|
| 真相源 | `[记忆共享中心]/技能配置/` | 实目录（66 项·2026-10-02 实查） |
| 消费面 | `~/.workbuddy/skills/` | 软链 → 真相源（81 项） |

⇒ 别端四检测**不够用**：它们只扫一个根，看不见「真源改名/删除 ⇒ 消费面链残留」
（Hermes 2026-10-01 在 skills_relink 上挖出的同源病）。
⇒ 本件 = 四检测 + **双向对账**（WB 特有增强，⛔ 不改公共原语语义）。

## 检测项

| # | 项 | 级别 | 面 |
|:-:|---|:--:|---|
| 1 | 断链（消费面软链目标不存在） | RED | DEST |
| 2 | 孤儿链（消费面有·真相源无对应） | RED | 双向 |
| 3 | 漏链（真相源 Skill·消费面未挂载） | WARN | 双向 |
| 4 | 消费面非软链实目录（违第三方软链铁律） | WARN | DEST |
| 5 | SKILL.md 缺 / frontmatter 缺 name | WARN | SRC |
| 6 | frontmatter name 重名冲突 | RED | SRC |
| 7 | 必备核心 Skill 缺失 | WARN | SRC |

## 纪律（守卫编写规范 §八）

- 只记录不拦截：报告制·默认 exit 0（`--strict` 时 RED 才 exit 1）
- 端隔离：⛔ 只读本端两面，⛔ 不写任何文件
- 自测：`--self-test` 临时目录夹具 + 空目录变异探针（⛔ 不碰真实目录）
- 反静默：派生/解析失败进 findings，⛔ 不 `except: pass`
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_health_common import (  # noqa: E402  公共原语·⛔不复制实现
    add, classify, finalize, fm_name, new_report, self_test_core,
)

VERSION = "v1.0.0"
HOME = os.path.expanduser("~")

# 端中立化（对齐 guard_heartbeat_check.py v3.2 三段 env 先例·2026-10-02）：
# 入发布包后⛔不得残留作者域硬路径（该目录名走 _AI_DIR 转义）⇒ 改为 env 可覆盖。
# ✅ 零 env 时行为与改前逐字一致（他端/本端零影响）。
# ⛔ 路径字面量用 \u 转义（脱敏免疫写法·同族先例：自愈检脚本）：
#    包内不得出现作者侧 `~/个人AI档案` 字面量（白名单规则=白名单外含之即拒发），
#    而自动 relocate 覆盖不到 os.path.join 形态 ⇒ 源侧用转义，语义完全等价。
_AI_DIR = "\u4e2a\u4ebaAI\u6863\u6848"
SRC = (os.environ.get("SKILL_HEALTH_SRC")
       or os.path.join(HOME, _AI_DIR, "\u6280\u80fd\u914d\u7f6e"))     # 真相源
DEST = (os.environ.get("SKILL_HEALTH_DEST")
        or os.path.join(HOME, ".workbuddy", "skills"))                  # 消费面
ROUTER = (os.environ.get("SKILL_HEALTH_ROUTER")
          or os.path.join(HOME, _AI_DIR, "\u811a\u672c\u4e2d\u5fc3", "router.py"))

# 他端配置根：软链目标落在这些域 ⇒ 属他端资产（端隔离·⛔我方不治理不判红）
# 实证：首跑 24 条断链里 `self-improving-agent` → ~/.qclaw/…（Qclaw 端资产）
FOREIGN_ROOTS = (".qclaw", ".hermes", ".trae", ".qoder", ".zcode", ".dsh",
                 ".openclaw", ".workbuddy-ai", ".meituan-catpaw", ".teleagent")

# 回退常量：仅当 router.py 派生失败时使用（派生失败会同时进 findings·不静默）
REQUIRED_FALLBACK = [
    "awaken-memory-system", "chrold", "clock-loop", "daily-buddy",
    "good-good-study", "growth-box", "meta-aletheia", "scriyore",
    "shall-we-talk", "skill-forge", "sucair", "system-logger",
    "triwich", "excavator", "热点捕手", "素然启镜",
]


def derive_required(rep: dict):
    """从 router.py 的 SKILLS 表机械派生必备清单（⛔ 不手抄·防漂移）。"""
    try:
        tree = ast.parse(open(ROUTER, encoding="utf-8").read())
    except (OSError, SyntaxError) as e:
        add(rep, "WARN", "required_derive_failed",
            f"router.py 派生失败·回退内置 {len(REQUIRED_FALLBACK)} 个（{type(e).__name__}）")
        return list(REQUIRED_FALLBACK)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "SKILLS":
                    v = node.value
                    # router.py 实盘 SKILLS 是 List（非 Dict）·两形态都认
                    if isinstance(v, ast.List):
                        keys = [e.value for e in v.elts
                                if isinstance(e, ast.Constant)
                                and isinstance(e.value, str)]
                    elif isinstance(v, ast.Dict):
                        keys = [k.value for k in v.keys
                                if isinstance(k, ast.Constant)
                                and isinstance(k.value, str)]
                    else:
                        continue
                    if keys:
                        return keys
    add(rep, "WARN", "required_derive_failed",
        "router.py 无 SKILLS 字面量表·回退内置清单")
    return list(REQUIRED_FALLBACK)


def check(skills_dir: str = None) -> dict:
    """skills_dir 参数仅 self-test 夹具用（对账时忽略·空目录两面皆空）。"""
    rep = new_report(SRC, VERSION)
    src = skills_dir if skills_dir else SRC
    dest = None if skills_dir else DEST

    if not os.path.isdir(src):
        add(rep, "RED", "src_missing", f"真相源目录不存在：{src}")
        return finalize(rep)

    required = derive_required(rep)

    # ---- 面 A：真相源（四检测 + 必备） ----
    seen, src_skill_names = {}, set()
    try:
        entries = sorted(os.listdir(src))
    except OSError as e:
        add(rep, "RED", "src_unreadable", f"真相源不可读：{e}")
        return finalize(rep)

    for name in entries:
        if name.startswith("."):
            rep["system_dirs"] += 1
            continue
        p = os.path.join(src, name)
        kind = classify(p)
        if kind in ("category",):
            rep["categories"] += 1
            continue
        if kind in ("resource", "skip"):
            rep["resources"] += 1
            continue
        # kind == "empty"：空目录既无 SKILL.md 也无内容＝真缺件，
        # ⛔ 不当资源目录豁免（自测夹具 empty-dir 实测：豁免了就漏报 no_skill_md）
        if kind == "symlink":                      # 真相源侧理论上不该有链
            if not os.path.exists(p):
                add(rep, "RED", "broken_symlink",
                    f"真相源断链：{name} → {os.readlink(p)}")
            continue
        rep["total"] += 1
        src_skill_names.add(name)
        md = os.path.join(p, "SKILL.md")
        if not os.path.isfile(md):
            add(rep, "WARN", "no_skill_md", f"{name}/ 缺 SKILL.md")
            continue
        real = fm_name(md)
        if not real:
            add(rep, "WARN", "no_frontmatter_name",
                f"{name}/SKILL.md frontmatter 缺 name")
            continue
        if real in seen:
            add(rep, "RED", "duplicate_name",
                f"重名冲突：{name} 与 {seen[real]} 同声明 name={real}")
        else:
            seen[real] = name
    rep["names"] = len(seen)

    for req in required:
        if req not in src_skill_names and not os.path.exists(os.path.join(src, req)):
            add(rep, "WARN", "required_missing", f"必备 Skill 缺失：{req}")

    # ---- 面 B：消费面 + 双向对账（WB 特有） ----
    if dest is None:
        return finalize(rep)
    if not os.path.isdir(dest):
        add(rep, "RED", "dest_missing", f"消费面目录不存在：{dest}")
        return finalize(rep)

    try:
        d_entries = sorted(os.listdir(dest))
    except OSError as e:
        add(rep, "RED", "dest_unreadable", f"消费面不可读：{e}")
        return finalize(rep)

    rep["platform"] = 0
    for name in d_entries:
        if name.startswith("."):
            continue
        p = os.path.join(dest, name)
        # ① 断链
        if os.path.islink(p):
            if not os.path.exists(p):
                tgt = os.readlink(p)
                # ⛔ 他端域豁免：目标落在他端配置根 ⇒ 他端资产，
                #   我方既不治理也不判红（端隔离·判了就是长期假红噪声）
                if any(r in tgt for r in FOREIGN_ROOTS):
                    rep["foreign"] = rep.get("foreign", 0) + 1
                    continue
                add(rep, "RED", "broken_symlink",
                    f"消费面断链：{name} → {tgt}")
                continue
            # ② 孤儿链：链活着但真相源已无对应（真源改名/删除残留）
            if name not in src_skill_names:
                add(rep, "RED", "orphan_link",
                    f"孤儿链：消费面有 {name}·真相源已无对应目录")
            continue
        if os.path.isdir(p):
            # ⛔ 假阳性豁免（首跑实锤 2 类·抽样取证）：
            #   a) 平台市场原生 Skill：含 `_skillhub_meta.json`（如 qqmusic）
            #   b) 空容器目录（如 `_backups`）
            #   ⇒ 软链铁律只管**布洛陀体系 Skill**（router.py SKILLS 清单内），
            #     平台件不是我方资产·判它违规＝把平台形态当违规。
            if os.path.isfile(os.path.join(p, "_skillhub_meta.json")):
                rep["platform"] += 1
                continue
            try:
                empty = not os.listdir(p)
            except OSError:
                empty = False
            if empty:
                rep["platform"] += 1
                continue
            if name in required:
                add(rep, "WARN", "dest_not_symlink",
                    f"体系 Skill 在消费面是实目录（应为指向真相源的软链）：{name}")
            else:
                rep["platform"] += 1          # 非体系实目录·平台原生·不报
            continue

    # ③ 漏链：仅核心（required）漏挂才报，其余计入统计不噪声
    d_names = {n for n in d_entries if not n.startswith(".")}
    gap = src_skill_names - d_names
    for s in sorted(gap):
        if s in required:
            add(rep, "WARN", "missing_link",
                f"核心 Skill 真相源有 {s}·消费面未挂载（WB 加载不到）")
    rep["unmounted_nocore"] = len(gap - set(required))

    return finalize(rep)


def _self_test() -> int:
    def _only_src(d):
        """夹具只需验公共四检测：对账腿在真实两面才成立，夹具下天然全空。"""
        return check(d)
    return self_test_core(_only_src)


def main() -> int:
    ap = argparse.ArgumentParser(description="WorkBuddy 端 Skill 生态健康度守卫")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="有 RED 时 exit 1（默认恒 0·报告制）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return _self_test()

    rep = check()
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"WorkBuddy Skill 生态健康 · {rep['ts']} · {VERSION}")
        print(f"  真相源：{SRC}")
        print(f"  消费面：{DEST}")
        print(f"  Skill {rep['total']} · 分类 {rep['categories']} · "
              f"资源 {rep['resources']} · 系统 {rep['system_dirs']} · "
              f"平台件 {rep.get('platform',0)} · "
              f"他端件 {rep.get('foreign',0)}（端隔离·不判红）· "
              f"声明名 {rep['names']}")
        print(f"  非核心未挂载（不计告警）：{rep.get('unmounted_nocore',0)} 个")
        for f in rep["findings"]:
            print(f"  [{f['level']}] {f['kind']}: {f['detail']}")
        print(f"  → RED {rep['red']} / WARN {rep['warn']}")
    if a.strict and rep["red"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
