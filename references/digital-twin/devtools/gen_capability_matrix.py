#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_capability_matrix.py —— CAPABILITY-MATRIX.md **唯一生成器**

## 为什么必须脚本化（铁律-016·二手源必烂）

2026-10-02 实测：手写矩阵 **60 格里 26 格（43%）与 `capability.yaml` 实况不符**，
其中最严重的一格是 **Hermes「hooks 事件驱动」手写 ❌ / 实况 ✅**——
而 Hermes 端**整套插件体系就架在这条 hook 事件面上**。
装它的端，文档却写着它不支持 hook 事件。

⇒ 根因不是"谁填错了"，是**矩阵没有生成器**：
只要一份数据能从别处推导出来，它就必然漂——手写的那份永远追不上改的那份。

## 本脚本的契约

| 项 | 约定 |
|:---|:---|
| 唯一真源 | `adapters/<端>/capability.yaml` 的 `capabilities:` 段 |
| 端全集 | `adapters/` 下的目录名·⛔ 不写死端列表（加端即自动入表）|
| 缺失语义 | `capability.yaml` 的 `missing_semantics:` 段（required/optional/n_a）|
| 幂等 | 连续跑两次·第二次 diff 必为空 |
| 头标 | 「⛔ 本文件由脚本生成·勿手改」+ 生成器路径 |

⚠️ **三值判据**（不是二值）：能力声明只有 true/false，
但**没有 capability.yaml 的端**（qwen/teleagent）是一等状态，
显示 `—（无声明）` ⛔ **不并入 ❌**——"没测过"与"不支持"是两件事（交接书 §3.1）。
把二者混同，端 AI 就会去"修"一个根本不存在的问题。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(os.path.dirname(HERE))

# 展示名：目录 ID → 人读名。⛔ 缺项走 display_name 再退化目录名（⛔ 不猜）
FALLBACK = {}


def _flags(cap_text: str) -> dict:
    out = {}
    in_cap = False
    for ln in cap_text.split("\n"):
        if not ln.startswith((" ", "\t")):
            in_cap = ln.split("#", 1)[0].strip() == "capabilities:"
            continue
        if not in_cap:
            continue
        s = ln.split("#", 1)[0].strip()
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        v = v.strip().strip('"').strip("'").lower()
        if v in ("true", "false"):
            out[k.strip()] = (v == "true")
    return out


def _top(cap_text: str, key: str):
    for ln in cap_text.split("\n"):
        if ln.startswith("#"):
            continue
        s = ln.split("#", 1)[0].strip()
        if s.startswith(key + ":"):
            return s.split(":", 1)[1].strip().strip('"').strip("'") or None
    return None


def _sem(cap_text: str) -> dict:
    out = {}
    lines = cap_text.split("\n")
    in_sec = False
    for ln in lines:
        if not ln.startswith((" ", "\t")):
            in_sec = ln.split("#", 1)[0].strip() == "missing_semantics:"
            continue
        if not in_sec:
            continue
        s = ln.split("#", 1)[0].strip()
        if ":" in s:
            k, v = s.split(":", 1)
            v = v.strip().strip('"').strip("'")
            if v in ("required", "optional", "n_a"):
                out[k.strip()] = v
    return out


def _cell(val) -> str:
    """三值渲染（唯一真源·⛔ 别处不许另写一份）"""
    if val is None:
        return "—<br>无声明"
    return "✅" if val else "❌"


# 行定义：(行标题, capability 键)——⛔ 键必须真实存在于 capability.yaml
ROWS = [
    ("hooks 事件驱动", "hooks_event"),
    ("非标准钩子机制", "hooks_alternative"),
    ("settings.json 注册", "settings_json"),
    ("rules/ 常驻文件注入", "rules_inject"),
    ("AGENTS.md 导航", "agents_full_inject"),
    ("自定义指令", "custom_directive"),
    ("钩子返回值注入", "hook_stdout_inject"),
    ("系统提示分段注入", "system_prompt_section"),
    ("记忆支点（session 检索等）", "awareness"),
    ("Skill 软链", "skill_symlink"),
    ("定时巡逻", "launchd_patrol"),
]

HEADER = """<!--
⛔⛔⛔ 本文件由脚本生成 —— 请勿手改 ⛔⛔⛔

生成器：references/scripts/gen_capability_matrix.py
唯一真源：adapters/<端>/capability.yaml 的 capabilities: 段
手改会在下一次生成时被覆盖，且**不留痕迹地漂移**——这正是铁律-016 的由来。

🔴 加端/改能力 ⇒ 改 `capability.yaml`（真源），⛔ 不要改本文件。
   本文件是**派生数据**，不是数据源。

重建命令：
    python3 "references/scripts/gen_capability_matrix.py"
    python3 "references/scripts/gen_capability_matrix.py" --check   # 只验不写
-->
"""


def build(pkg: str) -> str:
    adir = os.path.join(pkg, "adapters")
    ends = sorted(d for d in os.listdir(adir)
                  if os.path.isdir(os.path.join(adir, d))
                  and not d.startswith("."))
    data = {}
    for e in ends:
        cp = os.path.join(adir, e, "capability.yaml")
        if not os.path.isfile(cp):
            data[e] = {"name": e, "flags": None, "sem": {}, "has_cap": False}
            continue
        t = open(cp, encoding="utf-8").read()
        data[e] = {"name": _top(t, "display_name") or e,
                   "flags": _flags(t), "sem": _sem(t), "has_cap": True}

    L = [HEADER, "", "# 适配层能力矩阵（🔴 脚本生成·勿手改）", "",
         "> ✅=端声明支持 · ❌=端声明不支持 · `—<br>无声明`=**该端没有 capability.yaml**",
         "> （不是「不支持」，是**没测过**——两者混同会诱导端 AI 去修不存在的问题）",
         "",
         f"生成时间口径：随包内 `capability.yaml` 变��即变·⛔ 不写死日期（避免二次漂移源）", "",
         "## 一、能力矩阵（`capabilities` 段 × 各端）", ""]
    hdr = "| 能力 | " + " | ".join(data[e]["name"] for e in ends) + " |"
    sep = "|---|" + ":---:|" * len(ends)
    L += [hdr, sep]
    for title, key in ROWS:
        cells = []
        for e in ends:
            f = data[e]["flags"]
            cells.append(_cell(None if f is None else f.get(key)))
        L.append(f"| {title} | " + " | ".join(cells) + " |")

    L += ["", "## 二、端清单与声明状态", "",
          "| 端 | capability.yaml | 能力键数 | 语义声明数 | config_root |",
          "|---|:---:|:---:|:---:|---|"]
    for e in ends:
        d = data[e]
        L.append("| %s | %s | %d | %d | `%s` |" % (
            d["name"],
            "✅" if d["has_cap"] else "🔴 **无**（未适配/未测）",
            len(d["flags"] or {}), len(d["sem"]),
            (_top(open(os.path.join(adir, e, "capability.yaml"),
                       encoding="utf-8").read(), "config_root")
             if d["has_cap"] else "—") or "—"))

    L += ["", "## 三、缺失语义（回执判红的依据）", "",
          "| 端 | required | optional | n_a |",
          "|---|---|---|---|"]
    for e in ends:
        sem = data[e]["sem"] or {}
        by = {k: sorted([x for x, v in sem.items() if v == k])
              for k in ("required", "optional", "n_a")}
        L.append("| %s | %s | %s | %s |" % (
            data[e]["name"],
            ", ".join(by["required"]) or "—",
            ", ".join(by["optional"]) or "—",
            ", ".join(by["n_a"]) or "—"))

    L += ["",
          "> **怎么读这张表**（端 AI）：能力项显示 `—<br>无声明` ⇒ **不要报红**，",
          "> 去查该端是否有 `capability.yaml`；没有就说明该端**尚未适配**，",
          "> 这本身是缺口，但**不是本端的缺陷**。",
          ">",
          "> 判红只认两种：① `missing_semantics` 判 `required` 却未装上 ② 组件落点缺失。",
          "> 两者都由 `install_receipt.py` 实测产出 ⛔ 不靠本表推断。", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--package", default=PKG)
    ap.add_argument("--check", action="store_true", help="只验是否最新·不写盘")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(a.package, "adapters", "CAPABILITY-MATRIX.md")
    new = build(a.package)
    old = ""
    if os.path.isfile(out):
        old = open(out, encoding="utf-8").read()
    if a.check:
        same = old == new
        print("✅ 矩阵最新（与生成器输出一致）" if same
              else "❌ 矩阵已漂移·⛔ 手改过或 capability.yaml 变了未重建")
        return 0 if same else 1
    if old == new:
        print("✅ 无变化（幂等·⛔ 不重写）")
        return 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(new)
    print("🔄 矩阵已重建：%s（%d 端 × %d 能力）"
          % (out, len([d for d in os.listdir(os.path.join(a.package, "adapters"))
                       if os.path.isdir(os.path.join(a.package, "adapters", d))]),
             len(ROWS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())