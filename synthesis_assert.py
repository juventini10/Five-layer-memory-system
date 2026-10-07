#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""synthesis_assert.py — 步骤5「个性化文件合成」产物结构断言（机械门禁）

为什么要有它（2026-09-21 皮叔定）：
    安装流程 7 步里，步骤 5 是**唯一还在"靠 AI 现场发挥"**的环节——AI 拿答题数据 + 模板
    现场合成 SOUL/USER/CORE/摘要版等文件。其余步骤都有脚本兜底，这一步只有文档纪律
    （step5 §5f「风格合规检查」是给 AI 看的表格，AI 自己执行=自己给自己判卷）。
    → 本脚本把「结构段 / 占位符 / 表格行数 / 风格」全部机械化。

🔑 判据基准 = **包内 references/templates/ 的模板**，⛔不凭印象写段名/占位符。
    为什么：首版判据凭印象写，在作者本机跑出 6 项 FAIL 全是**误报**（枚举语法被当占位符、
    真实段名与我猜的不符、正则查错列……）。假阳性比没有检查更糟——判据必须由**被检对象的
    真源**生成，模板改了判据跟着改（单一数据源）。

判据：
    A 模板段在位   —— 模板里每个 `##` 段标题，成品必须含（模板→成品 的结构保证）
    B 占位符清零   —— 模板里出现过的 `{…}` 占位符，成品一个都不许残留（AI 漏填即现形）
    C 表格行数     —— 成品表格数据行 ≥ 模板行数（允许后续追加，不许缺）
    D 落点在位     —— 4 个系统文件在平台目录；其余在记忆共享中心
    E 风格合规     —— 仅 `--strict-style` 时启用（合成时点用）：机械化 step5 §5f

用法：
    python3 synthesis_assert.py --memory-center "<MC>" [--platform-dir "~/.workbuddy"] \
        [--pkg "<包根>"] [--strict-style] [--json]

退出码：0=全过；1=有 FAIL（明细打印）；2=前置错误。
"""

import argparse
import json
import os
import re
import sys
# Windows 控制台 UTF-8 守卫
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BRACE = re.compile(r"\{[^{}\n]{1,40}\}")

# 期望文件 → (落点类别, 模板相对路径, 备选成品路径)
#   落点类别 mc = <记忆共享中心>/… ；platform = <平台目录>（默认 ~/.workbuddy）
SPEC = [
    ("IDENTITY.md", "platform", "templates/IDENTITY.md", ["IDENTITY.md"]),
    ("SOUL.md", "platform", "templates/SOUL.md", ["SOUL.md"]),
    ("USER.md", "platform", "templates/USER.md", ["USER.md"]),
    ("MEMORY.md", "platform", "templates/MEMORY.md", ["MEMORY.md"]),
    ("摘要版", "mc", "templates/用户基本规则-摘要版.md", ["记忆规则/用户基本规则-摘要版.md"]),
    ("铁律版", "mc", "templates/用户基本规则-铁律版.md", ["记忆规则/用户基本规则-铁律版.md"]),
    ("CORE.md", "mc", None, ["核心层/CORE.md"]),
    ("SHADOW.md", "mc", "templates/SHADOW.md", ["潜意识层/SHADOW.md", "情境层/SHADOW.md", "SHADOW.md"]),
    ("动态状态快照", "mc", "templates/情境层-动态状态快照.md", ["情境层/动态状态快照.md"]),
]


def _read(p):
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


# 合成类文件（模板 + 注入 → 占位符必须清零）。
# 「直拷类」（铁律版/详解存档/记忆蓝图等）不做占位符判据——它们不进注入流程，
# 文中 `{流程A/B/C/E}` 之类是**用法示例**，不是待填占位符（首版判据在此误报 3 项）。
SYNTHETIC = {"IDENTITY.md", "SOUL.md", "USER.md", "MEMORY.md", "摘要版", "动态状态快照"}

_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]")


def _norm(s):
    """段标题归一化：去 markdown 记号/emoji/括号补充/`{}`占位符/空白。

    为什么：成品会演进（模板「工具列表」→ 本机「多工具体系」；模板段名自带
    `{YYYY-MM-DD}`）。精确匹配必然误报——**判据要抓"段还在不在"，不是"标题一字不差"**。
    """
    s = s.strip().lstrip("#").strip()
    s = re.sub(r"[（(][^（()）]*[)）]", "", s)
    s = re.sub(r"\{[^{}]*\}", "", s)
    s = _EMOJI.sub("", s)
    s = re.sub(r"[\s:：、,，·\-—|]+", "", s)
    return s


def _seg_keys(txt):
    """段标题归一化集合。⛔排除归一化后为空的（如 `### {YYYY-MM-DD} ⚠️{偏差摘要}` → 空）。"""
    keys = set()
    for l in txt.split("\n"):
        if not re.match(r"^#{2,3}\s+\S", l.strip()):
            continue
        k = _norm(l)
        if len(k) >= 2:
            keys.add(k)
    return keys


def _template_base(tpl_text):
    """从模板推导基准：段标题集合、占位符集合、表格行数。"""
    if tpl_text is None:
        return None
    secs = [l.strip() for l in tpl_text.split("\n") if re.match(r"^#{2,3}\s+\S", l.strip())]
    placeholders = sorted(set(BRACE.findall(tpl_text)))
    rows = len([l for l in tpl_text.split("\n") if l.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|$", l.strip())])
    return {"secs": secs, "placeholders": placeholders, "rows": rows}


def _selftest(pkg):
    """自验证（铁律-021①：验证脚本必须先自验证）。

    用包内模板造一份"刚合成"的模拟产物 → 跑本脚本判据 → 必须全过。
    这样**判据本身**（而非被检对象）也被机械验证：模板与判据若脱节，此处立刻红。
    """
    import subprocess
    import tempfile
    refs = os.path.join(pkg, "references")
    tpl = os.path.join(refs, "templates")
    if not os.path.isdir(tpl):
        print("!! 自验证失败：包内 references/templates/ 不存在")
        return 2
    tmp = tempfile.mkdtemp(prefix="synth-selftest-")
    mc, pd = os.path.join(tmp, "mc"), os.path.join(tmp, "pd")
    mapping = [
        ("SOUL.md", "templates/SOUL.md", os.path.join(pd, "SOUL.md")),
        ("USER.md", "templates/USER.md", os.path.join(pd, "USER.md")),
        ("MEMORY.md", "templates/MEMORY.md", os.path.join(pd, "MEMORY.md")),
        ("IDENTITY.md", "templates/IDENTITY.md", os.path.join(pd, "IDENTITY.md")),
        ("摘要版", "templates/用户基本规则-摘要版.md", os.path.join(mc, "记忆规则/用户基本规则-摘要版.md")),
        ("铁律版", "templates/用户基本规则-铁律版.md", os.path.join(mc, "记忆规则/用户基本规则-铁律版.md")),
        ("SHADOW.md", "templates/SHADOW.md", os.path.join(mc, "潜意识层/SHADOW.md")),
        ("快照", "templates/情境层-动态状态快照.md", os.path.join(mc, "情境层/动态状态快照.md")),
    ]
    for _n, rel, dst in mapping:
        src = os.path.join(refs, rel)
        if not os.path.isfile(src):
            print("!! 自验证失败：模板缺失 %s" % src)
            return 2
        t = open(src, encoding="utf-8").read()
        t = BRACE.sub("（示例值）", t).replace("[记忆共享中心]", mc)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(t)
    os.makedirs(os.path.join(mc, "核心层"), exist_ok=True)
    open(os.path.join(mc, "核心层/CORE.md"), "w", encoding="utf-8").write(
        "# CORE.md\n\n## 价值观\n.\n\n## 自我认知\n.\n")

    def _run(extra=()):
        return subprocess.run([sys.executable, os.path.abspath(__file__),
                               "--memory-center", mc, "--platform-dir", pd, "--pkg", pkg,
                               "--strict-style"] + list(extra), capture_output=True).returncode

    # 第一向：正常产物必须全过
    rc_ok = _run()
    # 第二向：注入缺陷必须被抓（否则判据=摆设）
    #   ⚠️ 首版只做第一向 → 改模板后两边同步变、**恒绿**，证明不了判据能抓问题。
    soul = os.path.join(pd, "SOUL.md")
    t = open(soul, encoding="utf-8").read().replace("## 我怎么说话", "## 说话方式")
    open(soul, "w", encoding="utf-8").write(t)                    # 段名被改 → 应报缺段
    user = os.path.join(pd, "USER.md")
    t = open(user, encoding="utf-8").read().replace("（示例值）", "{Step2 Q1}", 1)
    open(user, "w", encoding="utf-8").write(t)                    # 留占位符 → 应报残留
    rc_bad = _run()

    print("=== synthesis_assert 自验证（双向） ===")
    if rc_ok == 0 and rc_bad != 0:
        print("  ✅ 正例过 + 缺陷被抓（判据有效，非摆设）")
        result = 0
    else:
        print("  ❌ 正例 rc=%d（应 0） / 注入缺陷 rc=%d（应非 0）" % (rc_ok, rc_bad))
        result = 1
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-center", help="记忆共享中心（--selftest 时可省）")
    ap.add_argument("--platform-dir", default=os.path.expanduser("~/.workbuddy"))
    ap.add_argument("--pkg", default=HERE, help="发布包根（判据基准=其 references/templates/）")
    ap.add_argument("--strict-style", action="store_true", help="加跑 step5 §5f 风格合规（合成时点用）")
    ap.add_argument("--selftest", action="store_true", help="自验证：用模板造模拟产物跑判据")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return _selftest(os.path.abspath(os.path.expanduser(a.pkg)))
    if not a.memory_center:
        print("!! 缺少 --memory-center（或用 --selftest）")
        return 2

    mc = os.path.abspath(os.path.expanduser(a.memory_center))
    pd = os.path.abspath(os.path.expanduser(a.platform_dir))
    refs = os.path.join(os.path.abspath(os.path.expanduser(a.pkg)), "references")
    if not os.path.isdir(mc):
        print("!! 前置错误：记忆共享中心不存在 %s" % mc)
        return 2
    if not os.path.isdir(refs):
        print("!! 前置错误：包内 references/ 不存在 %s（判据基准缺失=拒绝判定·fail-closed）" % refs)
        return 2

    fails, checks = [], 0
    texts = {}

    for name, kind, tpl_rel, cands in SPEC:
        base = mc if kind == "mc" else pd
        found = None
        for c in cands:
            p = os.path.join(base, c)
            if os.path.isfile(p):
                found = p
                break
        # D 落点
        checks += 1
        if found is None:
            fails.append("D ①%s 不在预期落点：%s" % ("平台目录" if kind == "platform" else "记忆中心", os.path.join(base, cands[0])))
            continue
        texts[name] = _read(found)

        # A 模板段在位（归一化模糊匹配）/ B 占位符清零（仅合成类文件）
        tpl = _read(os.path.join(refs, tpl_rel)) if tpl_rel else None
        if tpl is None:
            continue          # 无模板基准（如 CORE.md 由答题生成）→ 跳过结构判据
        body = texts[name] or ""
        tpl_keys, body_keys = _seg_keys(tpl), _seg_keys(body)
        checks += 1
        miss = sorted(k for k in tpl_keys if k not in body_keys)
        if miss:
            fails.append("A %s 缺模板段 %d 个：%s" % (name, len(miss), "、".join(miss[:4])))
        if name in SYNTHETIC:
            checks += 1
            # G2-2 走查缺陷修（条文19 同型·修判据不修产物）：模板页脚「版本：」行里的
            # `{...}` 是**关于占位符的声明**非待填占位符——照模板合成必假红。声明行豁免出 B 基准。
            tpl_declared = set()
            for _l in tpl.split("\n"):
                if re.match(r"^版本[：:]", _l.strip()):
                    tpl_declared.update(BRACE.findall(_l))
            res = [ph for ph in sorted(set(BRACE.findall(tpl)) - tpl_declared)
                   if ph in body and "/" not in ph]
            if res:
                fails.append("B %s 残留模板占位符 %d 个：%s" % (name, len(res), "、".join(res[:4])))

    # E 风格合规（可选·合成时点）
    if a.strict_style:
        checks += 1
        soul = texts.get("SOUL.md") or ""
        body = _strip_code_and_quote(soul)
        hit = [w for w in ("MUST", "NEVER", "CRITICAL") if w in body]
        if hit:
            fails.append("E SOUL.md 正文含规则式词（应品格式）：%s" % "、".join(hit))
        if soul and "你是一个" not in soul:
            fails.append("E SOUL.md 缺「你是一个」身份宣言句式")
        # ⛔ USER.md 的「无指令」判据**不机械化**：模板自身含「接下来3个月必须达成的目标」这类
        #    内容性自然语言，机械判据分不清「内容里的必须」与「给 AI 的指令」，必出假阳性。
        #    该条留在 step5 §5f 由 AI 判断（诚实声明边界，⛔不用假阳性换"看着全绿"）。

    if a.json:
        print(json.dumps({"checks": checks, "fails": fails}, ensure_ascii=False, indent=2))
    else:
        print("=== 步骤5 合成产物结构断言 ===")
        print("  记忆中心: %s" % mc)
        print("  平台目录: %s" % pd)
        print("  判据基准: %s/references/templates/" % os.path.abspath(os.path.expanduser(a.pkg)))
        if fails:
            print("  ❌ FAIL %d 项：" % len(fails))
            for f in fails:
                print("     - %s" % f)
        else:
            print("  ✅ 全过（%d 组判据 / %d 件产物）" % (checks, len(SPEC)))
    return 1 if fails else 0


def _strip_code_and_quote(txt):
    """去掉代码块与引用块——引用里的演示文字不该被当违规正文。"""
    out, in_code = [], False
    for l in txt.split("\n"):
        if l.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or l.strip().startswith(">") or l.strip().startswith("|"):
            continue
        out.append(l)
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
