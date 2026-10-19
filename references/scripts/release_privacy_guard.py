#!/usr/bin/env python3
# TRUTH_OF: 脚本中心/release_privacy_guard.py   # 真源声明·派生面须软链指向本件（v1.2.227 副本声明面）
# -*- coding: utf-8 -*-
"""release_privacy_guard.py — 发布包隐私门禁（零容忍项·2026-10-05 皮叔令"隐私入库必须彻底根治，不能再犯"）

唯一真源（2026-10-05 你定·写死）：
  [记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包
其他包（存档包/备份版/旧安装包/DSH完整版）不在本门禁职责内，⛔ 不得跨包合计报账。

三档判定（防把机制引用误报成隐私）：
  RED   隐私数据本体：个人数据目录下出现真实条目（非模板、非结构说明）
  结构件：目录骨架 / _模板.md / README 概述 / 文件格式约定（告知型资产，可随包分发，只列不判红）
  机制引用：install 脚本、CHANGELOG 提到"成长箱/悬置区/日记"等目录名 ⇒ 不算泄漏（用户侧也会有）

自检 --self-test：注入伪隐私必须 RED、撤除必须转绿（出厂自证，防恒绿）。
退出码：0 干净 / 1 有 RED / 2 路径或用法错。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import os, re, sys, argparse, hashlib, json

__version__ = "1.1.0"  # 2026-10-05 建成：发布包隐私门禁（零容忍项·唯一真源=布洛陀-全平台安装包）

PERSONAL_DIRS = ["最伟大的我", "成长箱", "悬置区", "未知未知", "情境层", "SHADOW.md", "工作日志", "日记"]
PKG_DEFAULT = os.path.expanduser("[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包")
STRUCT_OK = ("_模板.md", "README.md", "文件格式约定.md")
REAL_SOURCES = {  # 个人数据真源映射（包内文件与真源同指纹 ⇒ 铁证泄漏）
    "断言台账.md": "未知未知/断言台账.md",
    "显形台账.md": "未知未知/显形台账.md",
    "悬置区.md": "未知未知/悬置区.md",
    "SHADOW.md": "潜意识层/SHADOW.md",
    "情境层-动态状态快照.md": "情境层/动态状态快照.md",
}
REC_RX = None


def _record_lines(body):
    """真实条目行＝记录型表/列表里带日期的行。

    判据看表头角色，不"见日期就报"（2026-10-05 实测：字段规范表里的示例日期被误判为隐私条目）：
      规范表（表头含 说明/示例/字段/Example/备注）内的日期 = 示例值 ⇒ 不算条目；
      记录表（表头含 日期/时间/触发/内容/来源/标题 等）内的日期 = 真实记录 ⇒ 算条目。
    """
    SPEC_HEAD = ("说明", "示例", "字段", "备注", "Example", "example")
    REC_HEAD = ("日期", "时间", "触发", "内容", "来源", "标题", "记录", "Logged", "date")
    out = []
    head = None
    for raw in body.split("\n"):
        s = raw.strip()
        if not s:
            head = None
            continue
        if s.startswith("|"):
            if head == "spec":
                continue          # 规范表内后续行不重分类（2026-10-05 T5 假红根因：行内「来源描述」被误判成记录表）
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all((not c) or set(c) <= set("-: ") for c in cells):
                continue
            if any(k in s for k in SPEC_HEAD) and not any(k in s for k in ("日期", "时间", "触发")):
                head = "spec"
            elif any(k in s for k in REC_HEAD):
                head = "rec"
            else:
                head = head or "unknown"
            if head != "rec":
                continue
        elif s.startswith(">") or re.search(r"YYYY|更新频率|待填|占位|模板", s):
            continue
        if re.search(r"20\d\d-\d\d-\d\d", s) and len(s) > 18:
            out.append(s)
    return out


def is_structural(path, txt):
    if os.path.basename(path) in STRUCT_OK:
        return True
    if len(txt.strip()) < 700 and ("待填" in txt or "示例" in txt or "模板" in txt):
        return True
    return False


def privacy_evidence(path, txt, pkg):
    """返回 (is_red, reason)。分两档，避免把结构文档的示例表当隐私：
      A 结构文档（README/格式约定/_模板）：仅当**与作者真源同指纹**才判红（示例表/字段说明不算条目）；
      B 数据文件（台账/快照/SHADOW 等）：同指纹 或 含条目形态的真实记录 ⇒ 红。
    两者皆无 ⇒ AMBER（净模板/无条目证据），⛔ 不拿假红淹没真报警。"""
    import hashlib
    base = os.path.basename(path)
    real = REAL_SOURCES.get(base)
    if real:
        rp = os.path.join(os.path.expanduser("~"), "[记忆共享中心]", real)
        if os.path.isfile(rp):
            h = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
            if h(path) == h(rp):
                return True, "与作者真源同指纹（铁证泄漏）"
    if base in STRUCT_OK:
        return False, "结构文档（无真源同指纹·表内日期为示例值）"
    body = txt.split("---", 2)[-1] if txt.startswith("---") else txt
    recs = _record_lines(body)
    if recs:
        return True, "含真实条目 %d 行（例：%s）" % (len(recs), recs[0][:40])
    return False, "无条目证据"


def scan(pkg):
    red, amber = [], []
    if not os.path.isdir(pkg):
        return None, None
    for root, dirs, files in os.walk(pkg):
        if ".bak" in root or "__pycache__" in root or os.sep + ".git" in root:
            continue
        rel_dir = os.path.relpath(root, pkg)
        hit_dir = [d for d in PERSONAL_DIRS if d in rel_dir.split(os.sep)]
        for f in files:
            if not f.endswith((".md", ".json", ".jsonl", ".txt")):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, pkg)
            if not (hit_dir or any(d.rstrip(".md") in rel for d in PERSONAL_DIRS)):
                continue
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            redflag, reason = privacy_evidence(p, txt, pkg)
            if redflag:
                red.append({"path": rel, "size": len(txt), "sha": hashlib.md5(txt.encode()).hexdigest()[:8], "why": reason})
            elif is_structural(p, txt):
                amber.append({"path": rel, "size": len(txt), "note": "结构件/模板"})
            else:
                amber.append({"path": rel, "size": len(txt), "note": "无条目证据"})
    # 成就系统专项扫描（2026-10-13 隐私红线根治·皮叔令「只清我不清用户」配套）：
    #   成就 md = auto-regen 展示文件，判据用**内容**（书名/✅已完成/已填达成日期），
    #   ⛔不用同指纹（作者骨架可能与包内字节相同⇒指纹假阳）；只扫真在「成就系统」目录段下的
    #   *成就.md，⛔不误伤 02_设计理念/成就系统设计哲学.md 这类非成就数据文档（不在该目录段）。
    for root, dirs, files in os.walk(pkg):
        if "__pycache__" in root or os.sep + ".git" in root or ".bak" in root:
            continue
        if "成就系统" not in os.path.relpath(root, pkg).split(os.sep):
            continue
        for f in files:
            if not f.endswith("成就.md"):
                continue
            p = os.path.join(root, f); rel = os.path.relpath(p, pkg)
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            body = txt.split("---", 2)[-1] if txt.startswith("---") else txt
            why = None
            if re.search(r"《(?!待填写|示例|书名)[^》]{1,60}》", body):
                why = "成就含真实书名《…》（作者个人数据）"
            elif re.search(r"✅ ?已完成", body):
                why = "成就含✅已完成达成状态（作者个人数据）"
            else:
                recs = _record_lines(body)
                if recs:
                    why = "成就含已填达成日期 %d 行（例：%s）" % (len(recs), recs[0][:30])
            if why:
                red.append({"path": rel, "size": len(txt), "sha": hashlib.md5(txt.encode()).hexdigest()[:8], "why": why})
    return red, amber


def selftest():
    import tempfile, shutil
    base = tempfile.mkdtemp(prefix="privguard-")
    pkg = os.path.join(base, "pkg")
    td = os.path.join(pkg, "references", "最伟大的我", "认知发现")
    os.makedirs(td)
    res = []
    open(os.path.join(td, "_模板.md"), "w", encoding="utf-8").write("这是一个模板，内容待填。\n" * 5)
    r0, a0 = scan(pkg)
    res.append(("T1 纯模板/骨架不误报", r0 == [], "red=%d amber=%d" % (len(r0), len(a0))))
    with open(os.path.join(td, "2026-09-12-真实个人认知发现.md"), "w", encoding="utf-8") as f:
        f.write("# 我的回避模式实录\n\n- 2026-09-12 来源：本次对话 | 内容：我回避了与团队的反馈会，具体个人反思。\n" + ("补充正文段落，确保不被长度判为模板。" * 30) + "\n")
    r1, _ = scan(pkg)
    res.append(("T2 隐私本体必 RED", len(r1) >= 1, "red=%d" % len(r1)))
    shutil.rmtree(td)
    os.makedirs(td)
    open(os.path.join(td, "_模板.md"), "w", encoding="utf-8").write("这是一个模板，内容待填。\n" * 5)
    r2, _ = scan(pkg)
    res.append(("T3 撤除后转绿", r2 == [], "red=%d" % len(r2)))
    r3, _ = scan(os.path.join(base, "notexist"))
    res.append(("T4 包路径不存在返 None（不假装通过）", r3 is None, str(r3)))
    # T5 净模板不误报（2026-10-05 假红回归：字段规范表内示例日期不得当隐私条目）
    shutil.rmtree(td); os.makedirs(td)
    open(os.path.join(td, "显形台账.md"), "w", encoding="utf-8").write(
        "---\ntitle: 未知未知 · 显形台账\n---\n\n本台账为模板，条目待填。\n\n"
        "| 字段 | 必 | 说明 | 示例 |\n|---|---|---|---|\n| `source` | 必 | 来源描述 | `2026-07-18 对话` |\n")
    r5, a5 = scan(pkg)
    res.append(("T5 净模板/示例表不误报", r5 == [], "red=%d amber=%d" % (len(r5), len(a5))))
    # T6 真条目必红（证据优先于"模板"自述）
    open(os.path.join(td, "显形台账.md"), "a", encoding="utf-8").write(
        "\n| 2026-09-12 | 我回避了与团队的反馈会，真实个人记录一条 |\n")
    r6, _ = scan(pkg)
    res.append(("T6 含真实条目必 RED", len(r6) >= 1, "red=%d" % len(r6)))
    # T7 结构文档（格式约定类）仅示例日期 ⇒ 不误报；数据文件同指纹才铁证
    shutil.rmtree(td); os.makedirs(td)
    open(os.path.join(td, "文件格式约定.md"), "w", encoding="utf-8").write(
        "---\ntitle: 文件格式约定\n---\n\n| 字段 | 示例 |\n|---|---|\n| source | `2026-07-18 对话` |\n" + ("约定说明正文。" * 60) + "\n")
    r7, _ = scan(pkg)
    res.append(("T7 结构文档示例值不误报", r7 == [], "red=%d" % len(r7)))
    # T8/T9 成就专项（2026-10-13 隐私红线根治防恒绿）：净骨架不误报·脏成就(书名/已完成)必红
    ad = os.path.join(pkg, "references", "成就系统"); os.makedirs(ad, exist_ok=True)
    open(os.path.join(ad, "阅读成就.md"), "w", encoding="utf-8").write(
        "---\ncreated: {YYYY-MM-DD}\n---\n\n# 阅读成就系统\n\n| 指标 | 数值 | 说明 |\n|---|---|---|\n"
        "| **阅读总量** | 未追踪 | 《待填写》 |\n| 🌱 萌芽 | 1 本 | ⏳ |\n")
    rc, _ = scan(pkg)
    res.append(("T8 干净成就骨架不误报", all("成就系统" not in x["path"] for x in rc), "red=%d" % len(rc)))
    open(os.path.join(ad, "阅读成就.md"), "w", encoding="utf-8").write(
        "---\ncreated: 2026-08-08\n---\n\n# 阅读成就系统\n\n| **阅读总量** | 9 本 | 《卢浮宫的猫》 |\n"
        "| �� 萌芽 | 1 本 | ✅ 已完成 |\n" + ("正文补充避免长度判模板。" * 30) + "\n")
    rd, _ = scan(pkg)
    res.append(("T9 脏成就(书名/已完成)必 RED", any("成就系统" in x["path"] for x in rd), "red=%d" % len(rd)))
    shutil.rmtree(ad, ignore_errors=True)
    shutil.rmtree(base, ignore_errors=True)

    ok = 0
    for name, passed, info in res:
        print(("✅" if passed else "❌"), name, "(" + info + ")")
        ok += 1 if passed else 0
    print("自测 %d/%d" % (ok, len(res)))
    return 0 if ok == len(res) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", default=PKG_DEFAULT)
    ap.add_argument("--self-test", action="store_true", dest="selftest")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    red, amber = scan(a.pkg)
    if red is None:
        print("❌ 包路径不存在：" + a.pkg, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"pkg": a.pkg, "red": red, "amber_count": len(amber)}, ensure_ascii=False, indent=1))
    else:
        print("🔒 发布包隐私门禁 · 唯一真源=" + a.pkg.replace(os.path.expanduser("~"), "~"))
        print("   RED（隐私本体嫌疑）=%d ｜ 结构件/模板（人眼确认）=%d" % (len(red), len(amber)))
        for x in red[:20]:
            print("   ❌ %s (%dB sha=%s) ｜ %s" % (x["path"], x["size"], x["sha"], x.get("why", "")))
        if not red:
            print("   ✅ 无隐私数据本体（个人数据目录内仅剩骨架/模板/结构说明）")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
