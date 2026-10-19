#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg_claim_audit.py —— 「报告声称 vs 包内实况」对账闸

## 为什么必须有这道闸（2026-10-03 · 病根实录）

今天在布洛陀全平台安装包上实锤了**同一个根因的第三形态**：

| 形态 | 表现 | 为什么闸门测不出 |
|:---|:---|:---|
| §5.7（12 号协议） | 测试夹具产物冒充端侧实证 | 验收看的是「回执在不在」，不看回执记的来源路径 |
| 形态二 | 执行报告白纸黑字写「已重写为动态全端扫描」，**包内那份是 08-30 旧版**（grep `capability.yaml` = 0 命中） | 报告是人读的，⛔ 无任何机械交叉核 |
| 形态三（今日实锤） | 我改了包内 `references/skills/restore-my-skills.sh`（**构建产物**），被下一次 `generate_release.py` 覆盖回去 → 改了个寂寞 | 产物 ≠ 真源；改产物永远白改 |

⇒ 三形态同根：**「说了」与「做了」之间没有任何机械判据**。
⇒ 本闸门把「说了」与「做了」接上。

## 本闸门查两件事（都可机械判·⛔ 不猜）

1. **报告声称改过的文件，包内是否真的在报告生成之后被动过**
   （判据 = 文件 mtime vs 报告落款/生成时间；早于 ⇒ 「声称已改但文件未动」= 假绿）
2. **报告声称改的路径，在包内是否存在**
   （不存在 ⇒ 路径写错或文件被删）

⛔ **本闸门不判「改动内容对不对」**——那是 diff 的事，不是本闸的事。
本闸只回答一个问题：**报告里那些「已改」，是不是真的改了。**

## 用法

```bash
python3 pkg_claim_audit.py --report <执行报告.md> [--pkg <包根>]
python3 pkg_claim_audit.py --report <报告.md> --self-test   # 造反例验判据有判别力
```

退出码：`0` = 报告与包内实况一致 · `1` = 有虚假声称（⛔ 不可发包）

## ⚠️ 判据边界（诚实声明·防「它保证了一切」的错觉）

| 能判 | 不能判 |
|:---|:---|
| 声称改的文件**没被动过**（mtime 早于报告） | 改了但**改错了内容** |
| 声称改的路径**不存在** | 报告漏报了改动（只查报告里有的） |
| 报告文件**本身不存在** | 改动是否真的解决了问题 |

⇒ 它的定位是**下限闸**（挡住最常见也最恶劣的「嘴上改了」），⛔ 不是完备验证。
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import argparse
import os
import re
import sys
from datetime import datetime

# 报告里「文件清单」表格的路径提取：只取像包内路径的 token
# ⛔ 不解析 markdown 表格结构——不同报告表格列名各异，按 token 特征取更稳
PATH_TOK = re.compile(
    r'`([^`\n]*?(?:install_scripts\.py|references/[\w./-]+'
    r'|adapters/[\w./-]+|install_receipt\.py|user_machine_fixture\.py)[^`\n]*?)`'
)
# 报告生成时间：frontmatter date / 正文首行「YYYY-MM-DD」/ 文件名带日期
DATE_PAT = re.compile(r'(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})')


def report_mtime(path: str) -> datetime:
    return datetime.fromtimestamp(os.stat(path).st_mtime)


def extract_report_time(path: str, text: str) -> datetime | None:
    """取报告的「声明时间」。

    取值优先级：frontmatter `date:` → 正文首个 YYYY-MM-DD → 文件 mtime。
    ⚠️ 用**声明时间**而非 mtime：报告常被二次编辑，mtime 会晚于它描述的改动。
    ⛔ 但若声明时间缺失则回落 mtime，并在输出里标注（不假装确定）。
    """
    m = re.search(r'^date:\s*["\']?([\d-]+)', text, re.M)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    m = DATE_PAT.search(text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    return None


def generated_artifact_roots(pkg_root: str) -> dict[str, str]:
    """🔴 **找出包内哪些路径是「构建产物」（改它们 = 白改）。**

    **病根实录（2026-10-03·当日实锤第三形态）**：
    我改了包内 `references/skills/restore-my-skills.sh`，写入成功（12821 字节）、
    5 秒内被 `generate_release.py` 的拷贝覆盖回 08-30 旧版（8417 字节）——
    改了个寂寞，且**没有任何一行报错**。

    ⇒ 病根：`references/skills/` 下的文件是 `generate_release.py` 从
      `[记忆共享中心]/技能配置/`（`SRC_ROOT`）**单向拷贝**的产物。
    ⇒ 判据：**报告若声称改的是产物路径 ⇒ 必须提示「改真源，不改产物」**。

    真源/产物映射取自 `generate_release.py` 自身声明（`SRC_ROOT` + `SKILLS`
    + `ROOT_SCRIPTS`），⛔ 不在本闸里另抄一份清单（那又是第二本账）。

    ⚠️ **找不到时的处置**：⛔ 不静默返回空（空 = 「没有产物路径」= 恒真判据）
    ⇒ 抛 `FileNotFoundError`，让调用方看到「本闸门失去判别力」而不是「全绿」。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    # ⛔ generate_release.py 是**作者侧**资产（发布流水线），⛔ 不在包内
    #    ⇒ 候选必须含包外路径；否则端用户机上本闸门永远 FileNotFoundError。
    #    「包外找不到就 fail-loud」是**作者侧运行**的正确行为；
    #    端用户机上则由调用方选择不跑此闸（它是发布侧闸，不是安装侧闸）。
    home = os.path.expanduser("~")
    cands = [
        os.path.join(pkg_root, "开发工具", "buluotuo-release-sync",
                     "generate_release.py"),
        os.path.join(os.path.dirname(here), "generate_release.py"),
        os.path.join(here, "generate_release.py"),
        # 🔴 2026-10-09 修（判据② 结构性失效·本闸自测正例3 当场抓出）：
        #   原第 4 候选 `os.path.join(home, os.path.expanduser("~"), ...)` 把**绝对路径**
        #   又拼到家目录下 ⇒ 产出 `<home>~/…` 这种永不存在的垃圾路径；
        #   而**真正在用的那条**（`[记忆共享中心]/脚本中心/`）根本没进候选
        #   ⇒ 四候选全落空 ⇒ FileNotFoundError ⇒ 调用方 except 吞掉 → fail-open 返回 True
        #   ⇒ **产物检测恒真**：改构建产物永远放行（正是本闸要拦的形态三）。
        #   修法：①补真实路径（`[记忆共享中心]/…`·发布流水线真身处）②删垃圾拼接候选。
        os.path.join(os.path.expanduser("[记忆共享中心]"), "开发工具", "buluotuo-release-sync",
                     "generate_release.py"),
        # 兜底：全盘找一次（⛔ 只在上面都落空时用·贵但准）
    ]
    for gen in cands:
        if os.path.isfile(gen):
            break
    else:
        raise FileNotFoundError(
            "generate_release.py 未找到（试过：%s）\n"
            "  ⛔ 本闸门**失去产物检测能力**——拒绝返回空映射冒充「无产物路径」。\n"
            "  💡 请用 --pkg 指向包根，或把 generate_release.py 的路径补进 cands。"
            % " / ".join(cands))
    out = {}
    txt = open(gen, encoding="utf-8", errors="replace").read()
    m = re.search(r'^SKILLS\s*=\s*\[(.*?)\]', txt, re.M | re.S)
    if m:
        for s in re.findall(r'"([^"]+)"', m.group(1)):
            out["references/skills/%s/" % s] = "技能配置/%s/" % s
    m = re.search(r'^ROOT_SCRIPTS\s*=\s*\[(.*?)\]', txt, re.M | re.S)
    if m:
        for s in re.findall(r'"([^"]+)"', m.group(1)):
            out["references/skills/%s" % s] = "技能配置/%s" % s
    if not out:
        raise RuntimeError(
            "从 %s 未解析出任何产物路径（SKILLS/ROOT_SCRIPTS 清单为空或格式已变）\n"
            "  ⛔ 拒绝返回空映射——那会让产物检测变成恒真判据。" % gen)
    return out


def audit(report: str, pkg_root: str) -> int:
    text = open(report, encoding="utf-8", errors="replace").read()
    rtime = extract_report_time(report, text)
    src = "报告声明时间" if rtime else "文件 mtime（报告无日期·⚠️ 判据降级）"
    if not rtime:
        rtime = report_mtime(report)

    cands = sorted({m.group(1).strip() for m in PATH_TOK.finditer(text)})
    # 归一到包内绝对路径（报告里可能是包相对，也可能是绝对）
    paths = []
    for c in cands:
        p = c if os.path.isabs(c) else os.path.join(pkg_root, c)
        paths.append((c, os.path.normpath(p)))

    artifacts = generated_artifact_roots(pkg_root)

    print("=" * 68)
    print("📋 报告声称 × 包内实况 · 对账闸")
    print("   报告：%s" % report)
    print("   包根：%s" % pkg_root)
    print("   判据时间：%s（%s）" % (rtime.strftime("%Y-%m-%d %H:%M"), src))
    print("   报告提及路径：%d 条" % len(paths))
    print("   构建产物映射：%d 条（来自 generate_release.py 自身声明）"
          % len(artifacts))
    print("=" * 68)

    missing, untouched, warned = [], [], []
    for rel, p in paths:
        if not os.path.exists(p):
            missing.append(rel)
            print("   ❌ 路径不存在      %s" % rel)
            continue
        # 🔴 产物检测（优先于 mtime——它抓的是更隐蔽的「改错地方」）
        for pref, srcpref in artifacts.items():
            if rel.startswith(pref):
                warned.append(rel)
                print("   ⚠️  这是**构建产物** %s" % rel)
                print("       ⛔ 改产物会被下次构建覆盖回去（generate_release.py"
                      " 从 SRC_ROOT 单向拷贝）")
                print("       真源 = 个人AI档案/%s" % srcpref)
                break
        # mtime 必须**晚于**报告声明时间当日零点（当日内的改动算已改）
        day0 = rtime.replace(hour=0, minute=0, second=0, microsecond=0)
        mt = report_mtime(p)
        if mt < day0:
            untouched.append((rel, mt))
            print("   ❌ 声称已改但未动  %s  (mtime %s < 判据日 %s)"
                  % (rel, mt.strftime("%m-%d %H:%M"), day0.strftime("%m-%d")))

    ok = len(paths) - len(missing) - len(untouched)
    print("-" * 68)
    if missing or untouched:
        print("❌ 虚假声称：%d 条路径不存在 + %d 条声称已改但文件未动"
              % (len(missing), len(untouched)))
        print("   ⛔ 报告与实况脱节 —— 这类报告不可作为验收依据。")
        return 1
    if warned:
        print("⚠️ 无虚假声称，但有 %d 条改的是**构建产物**——报告与包内实况一致，"
              % len(warned))
        print("   ⛔ **但这些改动活不过下一次构建**（会被 generate_release.py 覆盖）。")
        print("   💡 正解：改真源（技能配置/…），再跑 generate_release.py 重生成。")
        return 1
    print("✅ 报告提及的 %d 个路径均存在、在判据日之后被动过、且非构建产物" % ok)
    if not paths:
        print("   ⚠️ 报告里没提取到任何包内路径 —— 本闸门对这份报告**无判别力**")
        print("      （⛔ 别把「无告警」当「已核实」）")
    return 0


def self_test(pkg_root: str) -> int:
    """判别力自测：造一份「声称改了但文件未动」的反例，闸门必须报红。"""
    import tempfile
    real = os.path.join(pkg_root, "install_scripts.py")
    T = tempfile.mkdtemp(prefix="pkgclaim_")
    fake_report = os.path.join(T, "反例报告.md")
    with open(fake_report, "w", encoding="utf-8") as f:
        f.write("---\ndate: 2099-01-01\n---\n\n"
                "| 文件 | 改动摘要 |\n|---|---|\n"
                "| `install_scripts.py` | 声称已改（但真实文件是旧的） |\n")
    print("=== 自测：造反例（声称 2099 年已改 · 真实文件是今天之前）===")
    rc = audit(fake_report, pkg_root)
    if rc == 1:
        print("\n✅ 自测通过：反例被判红 ⇒ 本闸门**有判别力**（不是恒真判据）")
        return 0
    print("\n❌ 自测失败：反例没被抓到 ⇒ 本闸门是恒真判据，必须修")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    # ⚠️ 2026-10-03 修：--report 曾 required=True ⇒ `--self-test` 被 argparse
    #   挡在门外（rc=2「the following arguments are required: --report」），
    #   导致 guard_selftest_check 元守卫把它判红。判据：自测模式不需要报告。
    ap.add_argument("--report")
    ap.add_argument("--pkg", default=os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test(a.pkg)
    if not a.report:
        print("❌ 缺 --report（自测模式请用 --self-test）", file=sys.stderr)
        return 2
    if not os.path.isfile(a.report):
        print("❌ 报告不存在：%s" % a.report, file=sys.stderr)
        return 2
    return audit(a.report, a.pkg)


if __name__ == "__main__":
    sys.exit(main())