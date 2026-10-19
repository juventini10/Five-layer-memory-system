#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iron_rule_antibody_verifier.py — A类候选**逐条回读核证**器（v1.0.0·2026-10-01）

## 为什么需要这个（mapper 翻车实录）
`iron_rule_antibody_mapper.py` 首跑给出「A类 20 条已有承接」，但**逐条回读注册表核证
当场推翻 3 条**（词面命中 ≠ 直接证据，同成长箱 E3.5 要素5）：
  · 005 删除防护 ← git_commit_safe.sh（实为**提交串行化**·不删文件）
  · 011 写操作安全 ← symlink_guard.sh（实为 **Skill 软链巡检**·非写穿透防护）
  · 018 变更账本   ← changelog_guard.py（部分对·但注册表自标「负例实测待补」）

## 本脚本做什么
把 mapper 的关键词候选**降级为待核证线索**，改为按「铁律编号 → 守卫全名」显式绑定核证：
每条铁律的承接守卫由**本脚本内的核证表**给出（人工逐条回读注册表后写入），
⛔ 未在核证表中显式确认的守卫**一律不算承接**。

## 输出三态（严格）
  CONFIRMED  人工回读注册表确认该守卫真的守这条铁律的物理对象 → 可补登记「承接器在岗」
  REJECTED   回读后确认不守 → 不补·转 B 类评估新建
  UNVERIFIED 未核证 → ⛔不算任何状态（默认不信任）

## 纪律
· ⛔ 本脚本**不自动改铁律**（终审红线#2：AI 不得自行写入规则文件）
· ✅ 只产出「可补登记清单」，由人/授权流程执行写入
· 核证表为空 ⇒ 覆盖率读数**不涨**（⛔不得靠放宽判据虚增）
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import io
import json
import os
import re
import sys

IRON = os.path.expanduser("[记忆共享中心]/记忆规则/用户基本规则-铁律版.md")
REG = os.path.expanduser("[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md")
__version__ = "v1.0.0"

# ══════════ 核证表（人工逐条回读注册表后写入·⛔未列=UNVERIFIED）══════════
# 格式：铁律号 → (守卫全名, 核证结论, 核证依据[回读到的判据原文摘要])
# ⚠️ 本表是**核证缓存**，⛔ 不是判据真源——判据真源永远是守卫注册表原文。
#    每条 VERIFIED 都必须能指出「注册表哪一行说了什么」，⛔不接受"看起来相关"。
VERIFIED = {
    # ── 首轮（2026-10-01 22:20 逐条回读注册表）──
    "016": ("audit_staleness.sh", "CONFIRMED",
            "注册表：「审计权威源=实盘」——audit_staleness 巡检审计台账陈旧度，正对「人工维护的状态文字会漂」"),
    "017": ("rule_fragment_inject.py", "CONFIRMED",
            "注册表：「Skill路由强制启动」——rule_fragment_inject 在路由触发时注入铁律片段，机械强制"),
    "018": ("changelog_guard.py", "CONFIRMED",
            "注册表：「变更日志写入前排除类型校验」+ 配套 changelog_guard.sh 事后检测（写入前/后双闸）；"
            "⚠️注册表自标「负例实测待补」→ 承接成立但负例证据栏待补，登记时须如实照抄不美化"),
    "021": ("change_closedloop_guard.py", "CONFIRMED",
            "注册表：「改动闭环律机械门禁·Stop 链末位校验」——正是「验证机制自验证」的物理承接"),
    "025": ("guard_doc_consistency.py", "CONFIRMED",
            "注册表：「登记一致性·guard_doc_consistency」——常只读 SSOT 声称在跑时无写入口即报，"
            "正对「常态只读 SSOT 须配合法写入口」"),
    "026": ("stamp_precheck_guard.py", "CONFIRMED",
            "注册表：「时间戳真实性·事前层」——时刻字段必实取，PreToolUse 事前拦截"),
    "001": ("rule_three_layer_guard.py", "CONFIRMED",
            "注册表：「记忆规则三层版本一致性（版本号/铁律集合上界/描述计数）」——"
            "属铁律-001 先看清的系统性承接（层间版本漂移机械检出）；"
            "⚠️限定：它守的是「层间一致性」此一物理对象，⛔不等于覆盖铁律-001 全部语义"),
    "005": (None, "REJECTED",
            "回读：git_commit_safe.sh 判据为「提交串行化+零尾巴」，systemlog_watch 为日志守护；"
            "⛔二者均不检测删除动作。删除防护的真实承接需另查（trash 类守卫）"),
    "011": (None, "REJECTED",
            "回读：symlink_guard.sh 判据为「皮叔 Skill 跨端软链接巡检（真实目录副本→告警）」，"
            "⛔属 Skill 治理域，非「写操作穿透防护」。同名不同域"),
    "020": ("antibody_gate.py", "CONFIRMED",
            "注册表：antibody_gate 判据含「C7 恒假形态」等对判据自身可靠性的机械校验；"
            "⚠️限定：它守的是「抗体命令质量」，非「改匹配脚本前 sanity check」全集"),
    # ── 第二轮（2026-10-01 22:30 按域捞候选后逐条回读）──
    "019": ("ttl_expiry_guard.py", "CONFIRMED",
            "注册表：「规则时效·ttl_expiry_guard.py 记忆规则文件 TTL 过期（首prompt提醒）」＋"
            "audit_staleness.sh「记忆规则 TTL 陈旧审计」——正是「经验调用时效闸」的物理承接。"
            "⚠️限定：覆盖「文件 TTL 过期」，非「经验/立场卡调用时效」全集"),
    "014": ("git_commit_safe.sh", "CONFIRMED",
            "注册表：「跨端 git 提交串行化门禁＋partial commit 纪律（仅 git add 指定文件·杜绝吞他端 WIP）」"
            "＋write_race_watch ——覆盖「并发写入」这一物理对象。"
            "⚠️限定：覆盖并发/串行化，⛔非「隔离压测」全链"),
    "003": ("skill_selfcontained_guard.py", "CONFIRMED",
            "注册表：「Skill 自包含机械体检：检出未声明的跨目录引用」——引用面不一致的机械承接。"
            "⚠️限定：覆盖「Skill 跨目录引用」，非铁律-003 引用验证全集"),
}


def load_rules():
    t = io.open(IRON, encoding="utf-8").read()
    secs = re.split(r"\n### 铁律-(\d{3})", t)
    out = []
    for i in range(1, len(secs), 2):
        num, body = secs[i], secs[i + 1]
        has_ab = bool(re.search(r"承接器在岗|抗体|🛡", body))
        has_ex = bool(re.search(
            r"(?:抗体|🛡|承接器)[^。\n]{0,30}?(?:暂无|尚无|无|不适用|N/?A|未配|没有)"
            r".{0,40}?(?:理由|原因|因|系|：|:)", body, re.S))
        out.append({"num": num, "title": body.split("\n")[0].strip()[:40],
                    "bare": not (has_ab or has_ex)})
    return out


def load_registry():
    t = io.open(REG, encoding="utf-8").read()
    i = t.find("<!-- STRIP_START:守卫注册表")
    j = t.find("<!-- STRIP_END", i)
    blk = t[i:j] if j > 0 else t[i:]
    names = set()
    for line in blk.split("\n"):
        if line.startswith("| "):
            c = [x.strip() for x in line.split("|")[1:-1]]
            if c:
                names.add(c[0].split("（")[0].split("(")[0].strip())
    return names


def main():
    rules = load_rules()
    reg_names = load_registry()
    bare = [r for r in rules if r["bare"]]

    confirmed, rejected, unverified = [], [], []
    for r in bare:
        v = VERIFIED.get(r["num"])
        if v is None:
            unverified.append(r)
            continue
        guard, verdict, why = v
        if verdict == "CONFIRMED":
            # 守卫必须真实存在于注册表（防核证表写错名字）
            ok = guard in reg_names or any(guard in n for n in reg_names)
            if ok:
                confirmed.append((r, guard, why))
            else:
                unverified.append(r)
        else:
            rejected.append((r, why))

    print("iron_rule_antibody_verifier %s" % __version__)
    print("铁律 %d（无抗体 %d）· 已核证 %d / 未核证 %d"
          % (len(rules), len(bare), len(confirmed) + len(rejected), len(unverified)))
    print("=" * 78)

    print("\n✅ CONFIRMED %d 条 → ✅DO 可补登记「承接器在岗」+ 标注限定域" % len(confirmed))
    for r, g, why in confirmed:
        print("  铁律-%s %-28s ← %s" % (r["num"], r["title"][:28], g))
        print("        依据：%s" % why[:110])

    print("\n⛔ REJECTED %d 条 → 转 B 类（评估新建或显式豁免）" % len(rejected))
    for r, why in rejected:
        print("  铁律-%s %-28s" % (r["num"], r["title"][:28]))
        print("        否证：%s" % why[:110])

    print("\n⬜ UNVERIFIED %d 条 → ⛔不算任何状态·默认不信任（须逐条回读注册表）" % len(unverified))
    for r in unverified:
        print("  铁律-%s %s" % (r["num"], r["title"][:40]))

    print("\n📊 覆盖率可涨：%d%% → %d%%（仅 CONFIRMED 计入·⛔REJECTED/UNVERIFIED 不计）"
          % (round(100.0 * (len(rules) - len(bare)) / len(rules), 1),
             round(100.0 * (len(rules) - len(bare) + len(confirmed)) / len(rules), 1)))
    print("\n⚠️ 本脚本⛔不自动改铁律（终审红线#2）；核证表 VERIFIED 须随注册表变更复核。")
    if "--json" in sys.argv:
        print(json.dumps({"confirmed": [r["num"] for r, _, _ in confirmed],
                          "rejected": [r["num"] for r, _ in rejected],
                          "unverified": [r["num"] for r in unverified]},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())