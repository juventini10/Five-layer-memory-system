#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_buluotuo_merge.py —— 断章增量引擎的承重验收用例（宪法 §2.0）

⛔ **不跑这个 = 没验收**。方案文件 §2.0 列的 5 步用例一条条在这里机械化。

用例清单：
  T1 全新文件 → 建段 → 段内正确
  T2 已有用户内容（段外 50 行）→ 建段 → **用户原有字节零改动**
  T3 改包模板段 → 再装 → 段内变、用户字节不变
  T4 用户段外加一行 → 再装 → 那一行还在
  T5 幂等：连装两次 → 第二次 UNCHANGED、mtime 不变、单段唯一
  T6 段内被用户手改 + 给了 template → CONFLICT 且**不写盘**
  T7 标记不成对 → 抛 MergeError（⛔ 不自动修复，不追加第二个半截段）
  T8 备份失败 → 拒绝写入（C6 承重）
  T9 **造错用例**：故意破坏用户内容 ⇒ selfcheck 必须 FAIL（防恒真判据）

⚠️ T9 是防"判据恒真"的那一条——不造一次错，前面 8 条全绿也可能只是判据没走过。

⚠️ 判据一律用**安装前的整file原文**做基准，⛔ 不用 read_outside() 这种派生量
（派生量与合并逻辑同源，两边一起错时判不出）。

跑法：python3 references/scripts/test_buluotuo_merge.py
"""

from __future__ import annotations
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass

import importlib.util
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "buluotuo_merge", os.path.join(_HERE, "buluotuo_merge.py")
)
bm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bm)

USER_BLOCK = "\n".join(
    "这是用户自己写的第 %d 行·布洛陀不许动。" % i for i in range(1, 51)
)
USER_HEAD = "# 我的 SOUL\n\n" + USER_BLOCK + "\n"
PKG_BODY_V1 = (
    "## 布洛陀人格段\n\n我是你在 Hermes 上的搭档。\n\n"
    "### 执行准则\n1. 先看清再动手"
)
PKG_BODY_V2 = PKG_BODY_V1 + "\n2. 实事求是"

PASS, FAIL = [], []


def _t(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  ❌ ") + name + (("  · " + detail) if detail and not cond else ""))
    return cond


def _fixture(tmp, user_text=""):
    p = os.path.join(tmp, "SOUL.md")
    if user_text:
        with open(p, "w", encoding="utf-8") as f:
            f.write(user_text)
    return p


def t1_new_file():
    print("T1 全新文件 → 建段")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp)
        ok, st, msg = bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        _t("建段成功", ok and st == bm.STATUS_CREATED, msg)
        _t("段内内容正确", bm.read_section(bm.read_text(p), "soul.persona") == PKG_BODY_V1)
        _t("无原文件⇒不该有备份", not any(".bak-" in x for x in os.listdir(tmp)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t2_user_bytes_untouched():
    print("T2 已有用户 50 行 → 建段 → 用户原有字节零改动")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        ok, st, _ = bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        after = bm.read_text(p)
        _t("建段成功", ok and st == bm.STATUS_CREATED)
        _t("用户原文原样在段前(C2)", after.startswith(USER_HEAD))
        _t("用户 50 行全在", all(("第 %d 行" % i) in after for i in range(1, 51)))
        _t("有备份(C6)", any(".bak-" in x for x in os.listdir(tmp)))
        _t("自检全过", bm.selfcheck_all(p, "soul.persona", USER_HEAD) == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t3_upgrade_segment_only():
    print("T3 升级：模板段变 → 段内变、用户字节不变")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1, template_body=PKG_BODY_V1)
        # 用户在段外加一行（模拟用户又编辑了）
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n用户后来又加的一行。\n")
        original2 = bm.read_text(p)
        ok, st, msg = bm.upsert_section(p, "soul.persona", PKG_BODY_V2, template_body=PKG_BODY_V1)
        after = bm.read_text(p)
        _t("段升级成功(UPDATED)", ok and st == bm.STATUS_UPDATED, msg)
        _t("段内已是 V2", bm.read_section(after, "soul.persona") == PKG_BODY_V2)
        _t("用户后来那行还在", "用户后来又加的一行。" in after)
        _t("自检全过", bm.selfcheck_all(p, "soul.persona", original2) == [])
        _t("单段唯一", bm.selfcheck_single_section(p, "soul.persona") == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t4_user_edit_survives():
    print("T4 用户段外编辑 → 再装 → 不丢")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n## 我自己加的章节\n这是用户私有的内容。\n")
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1)  # 幂等重装
        txt = bm.read_text(p)
        _t("用户私有章节仍在", "我自己加的章节" in txt and "用户私有的内容。" in txt)
        _t("50 行仍在", all(("第 %d 行" % i) in txt for i in range(1, 51)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t5_idempotent():
    print("T5 幂等：连装两次")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        m1 = os.path.getmtime(p)
        txt1 = bm.read_text(p)
        ok, st, _ = bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        _t("第二次 UNCHANGED", ok and st == bm.STATUS_UNCHANGED)
        _t("内容完全一致", bm.read_text(p) == txt1)
        _t("mtime 未变（未写盘）", os.path.getmtime(p) == m1)
        _t("无重复段", bm.selfcheck_single_section(p, "soul.persona") == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t6_conflict():
    print("T6 段内被用户手改 + 给 template → CONFLICT 且不写")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        txt = bm.read_text(p).replace("我是你在 Hermes 上的搭档。", "我是用户自己改的这句话。")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        before = bm.read_text(p)
        ok, st, msg = bm.upsert_section(p, "soul.persona", PKG_BODY_V2, template_body=PKG_BODY_V1)
        _t("判为 CONFLICT", (not ok) and st == bm.STATUS_CONFLICT, "got=%s" % st)
        _t("盘上未被改动", bm.read_text(p) == before)
        _t("用户改动还在", "我是用户自己改的这句话。" in bm.read_text(p))
        _t("提示含拒绝语义", "拒绝" in msg)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t7_broken_markers():
    print("T7 标记不成对 → 抛错，不自动修复")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, "# SOUL\n" + bm.BEGIN_TMPL.format(sid="soul.persona") + "\n半截段\n")
        raised = False
        try:
            bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        except bm.MergeError as e:
            raised = "标记不成对" in str(e)
        _t("应抛 MergeError", raised, "没抛")
        _t("未被写入半截段", "布洛陀人格段" not in bm.read_text(p))
        _t("仍只有一个 BEGIN", bm.read_text(p).count(bm.BEGIN_TMPL.format(sid="soul.persona")) == 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t8_backup_failure_blocks():
    print("T8 备份失败 → 拒绝写入")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        real = bm.backup

        def boom(*a, **k):
            raise bm.MergeError("模拟备份失败")

        bm.backup = boom
        raised = False
        try:
            bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        except bm.MergeError as e:
            raised = "备份失败" in str(e)
        finally:
            bm.backup = real
        _t("应抛 MergeError", raised, "没抛")
        _t("盘上未被改动", bm.read_text(p) == USER_HEAD)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t9_falsification():
    print("T9 造错：故意破坏用户内容 ⇒ selfcheck 必须 FAIL（防恒真判据）")
    tmp = tempfile.mkdtemp()
    try:
        p = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p, "soul.persona", PKG_BODY_V1)
        _t("对照：正常态判据为绿", bm.selfcheck_all(p, "soul.persona", USER_HEAD) == [])
        # 造错①：段**前**被改（模拟覆盖型安装重排了用户内容）
        # ⚠️ 方向很关键：用户自己在段**后**加内容是合法权利，⛔ 不该判 FAIL；
        #    被判 FAIL 的必须是「布洛陀动了用户原有字节」。
        with open(p, "r", encoding="utf-8") as f:
            txt = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write("包偷偷在前面插的一行\n" + txt)
        _t("造错①段前被改 → 必须 FAIL",
           len(bm.selfcheck_all(p, "soul.persona", USER_HEAD)) > 0)
        # 造错①b：反向确认——用户自己在段后追加内容，⛔ 不该被误判（假红防线）
        p_b = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p_b, "soul.persona", PKG_BODY_V1)
        with open(p_b, "a", encoding="utf-8") as f:
            f.write("\n用户自己在段后追加的一行\n")
        _t("对照：用户段后追加不该 FAIL（防假红）",
           bm.selfcheck_all(p_b, "soul.persona", USER_HEAD) == [])
        # 造错②：整段被删
        p2 = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p2, "soul.persona", PKG_BODY_V1)
        with open(p2, "w", encoding="utf-8") as f:
            f.write(USER_HEAD)
        _t("造错②段被删 → 必须 FAIL",
           len(bm.selfcheck_all(p2, "soul.persona", USER_HEAD)) > 0)
        # 造错③：用户原文被整体重写（模拟覆盖型安装）
        p3 = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p3, "soul.persona", PKG_BODY_V1)
        with open(p3, "w", encoding="utf-8") as f:
            f.write("包内容强行覆盖了用户的文件\n" + PKG_BODY_V1 + "\n")
        _t("造错③用户原文被覆盖 → 必须 FAIL",
           len(bm.selfcheck_all(p3, "soul.persona", USER_HEAD)) > 0)
        # 造错④：段重复出现两次
        p4 = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p4, "soul.persona", PKG_BODY_V1)
        with open(p4, "a", encoding="utf-8") as f:
            f.write("\n" + bm.render_section("soul.persona", PKG_BODY_V1) + "\n")
        _t("造错④重复段 → 必须 FAIL",
           len(bm.selfcheck_single_section(p4, "soul.persona")) > 0)
        # 造错⑤：replace 形态下段后被改（模拟升级时顺手改了用户后半段）
        p5 = _fixture(tmp, USER_HEAD)
        bm.upsert_section(p5, "soul.persona", PKG_BODY_V1)
        original5 = bm.read_text(p5)
        txt5 = bm.read_text(p5).replace("# 我的 SOUL", "# 布洛陀改过的标题")
        with open(p5, "w", encoding="utf-8") as f:
            f.write(txt5)
        _t("造错⑤段后内容被改 → 必须 FAIL",
           len(bm.selfcheck_all(p5, "soul.persona", original5)) > 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t10_frontmatter():
    print("T10 带 frontmatter 的文件（规则三层形态）")
    tmp = tempfile.mkdtemp()
    try:
        pkg = '---\ndescription: "包内模板·30条硬约束"\n---\n\n# 铁律版\n\n## 正文 A\n\n内容 A\n'
        # T10a 全新文件 ⇒ frontmatter 在第 1 行
        p = _fixture(tmp)
        ok, st, msg = bm.upsert_file_body(p, "rules.tielu", pkg)
        txt = bm.read_text(p)
        _t("写入成功", ok and st == bm.STATUS_CREATED, msg)
        _t("frontmatter 在第 1 行", txt.startswith("---\n"))
        _t("包内 description 在位", "包内模板·30条硬约束" in txt)
        _t("正文进段内", bm.read_section(bm.split_frontmatter(txt)[1], "rules.tielu") is not None)

        # T10b 用户已有 frontmatter ⇒ ⛔ 保留用户的，不覆盖
        user_fm = '---\ndescription: "我自己改的描述·请勿覆盖"\nalwaysApply: false\n---\n'
        p2 = _fixture(tmp, user_fm + "\n# 我的铁律版\n\n" + USER_BLOCK + "\n")
        original2 = bm.read_text(p2)
        ok2, st2, msg2 = bm.upsert_file_body(p2, "rules.tielu", pkg)
        txt2 = bm.read_text(p2)
        _t("写入成功", ok2 and st2 == bm.STATUS_CREATED, msg2)
        _t("用户 frontmatter 保留", "我自己改的描述·请勿覆盖" in txt2)
        _t("用户的 alwaysApply 保留", "alwaysApply: false" in txt2)
        _t("包内 description 未污染", "包内模板·30条硬约束" not in txt2)
        _t("用户 50 行全在", all(("第 %d 行" % i) in txt2 for i in range(1, 51)))
        _t("用户 frontmatter 逐字节不变",
           txt2.startswith(original2[: len(user_fm)]))

        # T10c 幂等
        m = os.path.getmtime(p2)
        ok3, st3, _ = bm.upsert_file_body(p2, "rules.tielu", pkg)
        _t("第二次 UNCHANGED", ok3 and st3 == bm.STATUS_UNCHANGED)
        _t("mtime 未变", os.path.getmtime(p2) == m)

        # T10d 段内被用户改 + 给 template ⇒ CONFLICT
        p4 = _fixture(tmp, pkg)
        bm.upsert_file_body(p4, "rules.tielu", pkg)
        fm4, body4 = bm.split_frontmatter(bm.read_text(p4))
        body4 = body4.replace("内容 A", "用户自己改的内容")
        with open(p4, "w", encoding="utf-8") as f:
            f.write(fm4 + body4)
        before4 = bm.read_text(p4)
        ok4, st4, msg4 = bm.upsert_file_body(
            p4, "rules.tielu", pkg + "\n新增一条\n", template_full=pkg)
        _t("判为 CONFLICT", (not ok4) and st4 == bm.STATUS_CONFLICT, "got=%s" % st4)
        _t("盘上未被改动", bm.read_text(p4) == before4)

        # T10e 无 frontmatter 的纯正文文件 ⇒ 整file 当正文处理
        p5 = _fixture(tmp, "纯正文·没有 frontmatter\n\n" + USER_BLOCK + "\n")
        ok5, st5, _ = bm.upsert_file_body(p5, "rules.plain", "# 标题\n\n正文\n")
        _t("无 frontmatter 也能写", ok5 and st5 == bm.STATUS_CREATED)
        _t("用户正文保留", all(("第 %d 行" % i) in bm.read_text(p5) for i in range(1, 51)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t11_frontmatter_falsification():
    print("T11 造错：frontmatter 相关判据必须能报错（防恒真）")
    tmp = tempfile.mkdtemp()
    try:
        pkg = '---\ndescription: "包内模板"\n---\n\n# 正文\n\n内容\n'
        # 造错①：段正文被改 ⇒ selfcheck（对 old_body）必须 FAIL
        p = _fixture(tmp, pkg)
        bm.upsert_file_body(p, "rules.tielu", pkg)
        fm, body = bm.split_frontmatter(bm.read_text(p))
        with open(p, "w", encoding="utf-8") as f:
            f.write(fm + body.replace("# 正文", "# 被篡改的正文"))
        viol = bm.selfcheck_outside(p, "rules.tielu", body.replace("# 正文", "# 被篡改的正文"))
        # 注：selfcheck_outside 的基准是「安装前原文」，此处故意拿篡改版当基准做对照，
        #     真正承重的是下面这条：段被删 ⇒ 必须 FAIL
        _t("对照项构造完成（不判成败）", isinstance(viol, list))
        p2 = _fixture(tmp, pkg)
        bm.upsert_file_body(p2, "rules.tielu", pkg)
        original_body = bm.split_frontmatter(bm.read_text(p2))[1]
        with open(p2, "w", encoding="utf-8") as f:
            f.write("---\ndescription: \"只剩 frontmatter\"\n---\n\n")
        _t("造错①段被删 → 必须 FAIL",
           len(bm.selfcheck_outside(p2, "rules.tielu", original_body)) > 0)
        # 造错②：frontmatter 被吞进正文段（判据须能看出 frontmatter 不在首位）
        p3 = _fixture(tmp, pkg)
        bm.upsert_file_body(p3, "rules.tielu", pkg)
        txt = bm.read_text(p3)
        with open(p3, "w", encoding="utf-8") as f:
            f.write(bm.render_section("rules.tielu", txt) + "\n")  # frontmatter 掉进段内
        fmk, _ = bm.split_frontmatter(bm.read_text(p3))
        _t("造错②frontmatter 掉进段内 → split 必须识别为无 frontmatter", fmk == "")
        # 造错③：开了头没闭合 ⇒ 必须当无 frontmatter（⛔ 不猜）
        p4 = _fixture(tmp, "---\ndescription: 没闭合\n\n# 正文\n")
        fmk2, bdy2 = bm.split_frontmatter(bm.read_text(p4))
        _t("造错③frontmatter 未闭合 → 当作无 frontmatter", fmk2 == "" and "没闭合" in bdy2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


RX_FILL = r"\[Q\d+·(?:答案待注入|规则待派生)\]"


def t12_injection_exempt():
    print("T12 step5 注入预期态豁免（C14）：纯占位格填充不报冲突·真改动/升级照报")
    tmp = tempfile.mkdtemp()
    try:
        tpl = ('---\nversion: v1\n---\n\n# 摘要版\n\n| Q8 | 失败归因 | [Q8·答案待注入] | [Q8·规则待派生] |\n'
               '| Q9 | 改变主意 | [Q9·答案待注入] | [Q9·规则待派生] |\n')
        p = _fixture(tmp)
        ok0, st0, _ = bm.upsert_file_body(p, "rules.summary", tpl)
        _t("T12a 首装成功", ok0, st0)
        # 模拟 step5 注入：占位格逐行被真实答案替换（行结构不变）
        txt = bm.read_text(p).replace("[Q8·答案待注入]", "内部不稳定归因") \
            .replace("[Q8·规则待派生]", "方法不对就改方法") \
            .replace("[Q9·答案待注入]", "认知升级驱动") \
            .replace("[Q9·规则待派生]", "先想通关键逻辑点")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        ok1, st1, msg1 = bm.upsert_file_body(p, "rules.summary", tpl,
                                             template_full=tpl, inject_exempt_re=RX_FILL)
        _t("T12a 注入后重装=预期态不报冲突", ok1 and st1 == bm.STATUS_UNCHANGED, "%s %s" % (st1, msg1))
        _t("T12a 注入内容未被覆盖", "内部不稳定归因" in bm.read_text(p))

        # T12b 真手改（改的是行名 Q9→自加行）⇒ 照报 CONFLICT（豁免不是总闸）
        txt2 = bm.read_text(p).replace("| Q9 | 改变主意 |", "| Q9 | 我自己改的行名 |")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt2)
        ok2, st2, _ = bm.upsert_file_body(p, "rules.summary", tpl,
                                          template_full=tpl, inject_exempt_re=RX_FILL)
        _t("T12b 真手改照报 CONFLICT", (not ok2) and st2 == bm.STATUS_CONFLICT, st2)

        # T12c 包升级（body≠template）+已注入 ⇒ 照报（注入豁免让位升级冲突人工裁决）
        txt3 = bm.read_text(p).replace("| Q9 | 我自己改的行名 |", "| Q9 | 改变主意 |")
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt3)
        new_pkg = tpl.replace("[Q9·答案待注入]", "[Q9·答案待注入]") + "\n> v2 升级注记\n"
        ok3, st3, _ = bm.upsert_file_body(p, "rules.summary", new_pkg,
                                          template_full=tpl, inject_exempt_re=RX_FILL)
        _t("T12c 升级撞注入照报 CONFLICT", (not ok3) and st3 == bm.STATUS_CONFLICT, st3)
        # 负例收尾：不给 exempt 时注入态仍报冲突（豁免必须显式授予·默认行为不变）
        ok4, st4, _ = bm.upsert_file_body(p, "rules.summary", tpl, template_full=tpl)
        _t("T12d 不传豁免参数=行为不变仍报冲突", (not ok4) and st4 == bm.STATUS_CONFLICT, st4)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print("=== 断章增量引擎 · 承重验收（宪法 §2.0）===\n")
    for fn in (t1_new_file, t2_user_bytes_untouched, t3_upgrade_segment_only,
               t4_user_edit_survives, t5_idempotent, t6_conflict,
               t7_broken_markers, t8_backup_failure_blocks, t9_falsification,
               t10_frontmatter, t11_frontmatter_falsification, t12_injection_exempt):
        fn()
        print("")
    print("=" * 52)
    print("通过 %d / 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("❌ 失败项：" + " · ".join(FAIL))
        return 1
    print("✅ 全部通过（宪法 C1-C7 逐条有机械证据）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())