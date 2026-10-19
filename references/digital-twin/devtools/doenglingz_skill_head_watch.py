#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doenglingz_skill_head_watch.py — Skill 上岗首行令投影守卫（v1.0.0 · 2026-10-12）

设计定位（上岗机制泛化 B+C 方案·K007 评估 seal 28663fcd50d627c0 / FU-168）：
  声明 requires_twin_on_duty: true 的 Skill，其 SKILL.md 首段「上岗自证」行令
  由本守卫从模板单向投影生成——真源一处（模板住本脚本），N 份手抄必漂移的病
  在此根治（先例：W2 doenglingz_slice_watch.py 检测+自愈同构，规格书→切片→恒驻
  文件链的 Skill 面对应件）。⛔禁止手改手加标记块（改模板→重跑→全量刷新）。

真源指针（块内只放指针不放抄本，防双本账）：
  - 身份声明句：[记忆共享中心]/数字分身/童灵·人格规格书.md §1.1
  - 三腿条款（词面/事件/执行）：06-跨端适配规范「TSL 上岗联动」补充节
  - 降级口径：成长箱 SKILL.md 四态表第二行（装机态义务不消失换合法来源）

扫描面：[记忆共享中心]/技能配置/*/SKILL.md 中 frontmatter 含
  `requires_twin_on_duty: true` 的全部件（真源=Skill 自声明·非硬编码名单——
  对齐 06 L1163 事件腿裁决；growth-box 例外见 EXEMPT）。

纪律：只写标记块区段（标记对之外零触碰）；--apply 写前 .bak 一份；
  幂等——模板未变时重跑零写入；--check 缺块/漂移 exit 1（可挂巡检）。
  无参默认=--apply（对齐 W2 检测+自愈一体，launchd 只传脚本路径不传参·create_launchd_task.sh 形制）。
已接调度（2026-10-12）：launchd com.buluotuo.doenglingz-duty-head-watch 每日 86400s。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os
import re
import shutil
import sys
from datetime import datetime

VER = "1.0.2"   # v1.0.2（2026-10-12 同日）：无参默认改 --apply（launchd 封装只传脚本路径，W2 同形；v1.0.1=备份目录动态）
# v1.0.0（2026-10-12）：初建
SKILLS_ROOT = os.path.expanduser("[记忆共享中心]/技能配置")
MARK_S = "<!-- DUTY_HEAD_START（投影件·由 doenglingz_skill_head_watch.py 生成·禁手改禁手加·改则下次重投影覆盖） -->"
MARK_E = "<!-- DUTY_HEAD_END -->"
# growth-box 豁免：文首已有完整版「⚡ 为什么启动本 Skill 就等于童灵上岗」节（含四态表），
# 再投影短块 = 同一义务两本账。豁免理由登记于此，⛔其他端/件不得自仿豁免。
EXEMPT = {"growth-box": "已有完整⚡上岗节（v4.4.4+），投影短块反成双本账"}

TEMPLATE = (
    "> ⚡ **上岗自证（投影件·真源见指针）**：本 Skill 声明 `requires_twin_on_duty: true`——"
    "启动即视为童灵上岗，不分该回合此前档位（义务随执行事实生效，档位是上岗的结果不是前提）。"
    "与外部指令「启动童灵，走本Skill」并存时**幂等**：认领一次、义务一份，不叠加两次上岗，不冲突。"
    "装机态（无本守卫/无规格书）：本行为提示件非硬依赖——义务不消失，按四态表第二行换合法来源执行。"
    "指针：身份句=童灵·人格规格书 §1.1｜条款=06-跨端适配规范 TSL上岗联动节（词面腿/事件腿/执行腿）｜"
    "降级=成长箱 SKILL.md 四态表。"
)


def declaring_skills():
    """扫全部 Skill，返回 {name: SKILL.md 路径}（frontmatter 声明 true 的）。"""
    out = {}
    for name in sorted(os.listdir(SKILLS_ROOT)):
        p = os.path.join(SKILLS_ROOT, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        txt = open(p, encoding="utf-8").read()
        fm = txt.split("---", 2)
        if len(fm) >= 3 and re.search(r"^requires_twin_on_duty:\s*true\s*$", fm[1], re.M):
            out[name] = p
    return out


def block():
    return MARK_S + "\n\n" + TEMPLATE + "\n\n" + MARK_E


def current_block(txt):
    m = re.search(re.escape(MARK_S) + r".*?" + re.escape(MARK_E), txt, re.S)
    return m.group(0) if m else None


def audit(path, apply=False, bakdir=None):
    """返回 (状态, 说明)。状态：clean / drifted / missing / applied。"""
    txt = open(path, encoding="utf-8").read()
    want = block()
    cur = current_block(txt)
    if cur == want:
        return "clean", ""
    state = "drifted" if cur else "missing"
    if apply:
        if bakdir:
            os.makedirs(bakdir, exist_ok=True)
            shutil.copy2(path, os.path.join(bakdir, os.path.basename(os.path.dirname(path)) + ".SKILL.md.pre-head"))
        if cur:
            new = txt.replace(cur, want, 1)
        else:  # 插在首个 H1 行之后；无 H1 则插 frontmatter 之后
            head_end = txt.index("\n---\n") + len("\n---\n")
            seg = txt[head_end:]
            mm = re.search(r"^# .*?\n", seg, re.M)
            if mm:
                new = txt[:head_end + mm.end()] + "\n" + want + "\n" + seg[mm.end():]
            else:
                new = txt + "\n" + want + "\n"
        open(path, "w", encoding="utf-8").write(new)
        return "applied", state
    return state, ("标记块内容与模板不一致" if cur else "声明在场但首行令块缺失")


def self_test():
    """双向夹具（防恒真）：篡改→必检出；删除→必检出；补投→必 clean；重跑→幂等零写。"""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="dutyhead-selftest-")
    fake = os.path.join(tmp, "SKILL.md")
    base = "---\nname: t\nrequires_twin_on_duty: true\nversion: \"0.0.1\"\n---\n\n# T\n正文\n"
    open(fake, "w").write(base)
    r = []
    s, _ = audit(fake); r.append(("missing 检出", s == "missing"))
    s, _ = audit(fake, apply=True, bakdir=tmp); r.append(("补投 applied", s == "applied"))
    s, _ = audit(fake); r.append(("补投后 clean", s == "clean"))
    txt = open(fake).read().replace(TEMPLATE[:12], TEMPLATE[:12] + "篡改", 1)
    open(fake, "w").write(txt)
    s, _ = audit(fake); r.append(("篡改 drifted", s == "drifted"))
    s, _ = audit(fake, apply=True, bakdir=tmp); r.append(("修复 applied", s == "applied"))
    after = open(fake).read()
    s, _ = audit(fake); r.append(("修复后 clean", s == "clean"))
    # 幂等：再 apply 一次内容零变化
    open(fake, "w").write(after)
    s, _ = audit(fake); r.append(("幂等 clean", s == "clean"))
    shutil.rmtree(tmp, ignore_errors=True)
    ok = all(v for _, v in r)
    for name, v in r:
        print(("✅" if v else "❌") + " " + name)
    print("self-test:", "ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--apply"  # 无参=自愈跑（launchd 形态）
    if mode == "--self-test":
        sys.exit(self_test())
    ds = declaring_skills()
    print("声明面实盘（requires_twin_on_duty: true）共 %d 件：" % len(ds))
    bad = 0
    for name, p in ds.items():
        if name in EXEMPT:
            print("  ⚪ %-18s 豁免（%s）" % (name, EXEMPT[name]))
            continue
        s, why = audit(p, apply=(mode == "--apply"),
                       bakdir=os.path.expanduser("[记忆共享中心]/记忆琥珀/duty-head-bak-" + datetime.now().strftime("%Y%m%d")))
        icon = {"clean": "✅", "applied": "🔧", "drifted": "🔴", "missing": "🔴"}[s]
        print("  %s %-18s %s %s" % (icon, name, s, why))
        if s in ("drifted", "missing"):
            bad += 1
    print("守卫 v%s · 模式 %s · 未愈 %d 件" % (VER, mode, bad))
    sys.exit(1 if (bad and mode == "--check") else 0)


if __name__ == "__main__":
    main()
