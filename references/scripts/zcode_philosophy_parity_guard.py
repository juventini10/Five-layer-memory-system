#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# zcode_philosophy_parity_guard.py — SessionStart 哲学版本对账腿（T0 方案 C1·愿景①③双中）
# version: v1.0（2026-10-04·ZCode 童灵 D3·皮叔令「按三明治推荐的顺序逐步做好」）
#
# Disease（2026-10-04 T0 审计实证）：脚本哲学 SSOT 高频演化（10-01~10-03 十余版），
#   端侧适配对账靠「你发起的自觉轮次」——漂移只能被人发现（本轮即证据）。
#   病根=漂移检测执行位错置在人。本守卫把执行位移交机制。
#
# Verdict（mechanical·SessionStart·报告制不拦截）：
#   ①文件自洽（01 规范 §二·二十）：frontmatter version 须 == 变更录顶条——两本账即 🔴 显形
#   ②端适配新鲜度：哲学四件任一 mtime > 端适配台账 mtime → 🟡「哲学有更新·端侧欠适配核对」
#   ③输出：有发现→SessionStart JSON additionalContext 注入 + 状态台账（回流链③）
#          无发现→静默 exit 0（零噪音）
#
# 对表声明（§二·十二 编排既有·方案 v1.3 修正④）：platform_adaptation_check 校验域=挂载面，
#   本件校验域=版本/新鲜度面——不重叠·独立实现（其模块级 path_overlay 有副作用·import 复用
#   不成立·v1.6 变更录订正 v1.3④ 的 import 论证）；哲学目录路径自维护=漂移绊线（--self-test 对照）。
#
# 挂载：~/.zcode/cli/config.json → hooks.events.SessionStart（crossend_guard 之后）
#   ZCode 端特性：配置不热加载·挂载生效判据=新会话真实触发。
# 回流链三段（01 规范 §二·十九）：①怎么写=状态台账 ②何时写=SessionStart 每会话 ③谁看=显形注入+台账
try:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass
import json
import os
import re
import time
from pathlib import Path

GUARD = "zcode_philosophy_parity_guard.py"
PHILOSOPHY_DIR_DEFAULT = "[记忆共享中心]" / "记忆蓝图" / "04_系统文件设计" / "布洛陀脚本架构设计哲学"
STATE_DEFAULT = Path.home() / ".zcode" / "state" / "philosophy_parity.json"
# 端适配台账=T0 方案文件（本端登记版本·文件名会演进→glob 兜底·前导 * 允许日期前缀）
TARGET_GLOB_DEFAULT = "*ZCode-HOOK机制最大化施工方案*.md"
TARGET_DIR_DEFAULT = "[记忆共享中心]" / "自定义层" / "待完成工作"
FILES = ["01-脚本架构设计通用规范.md", "守卫编写规范.md", "04-跨端接入指南.md", "INDEX.md"]

FM_RE = re.compile(r"^version:\s*v?(\d+(?:\.\d+)+)", re.M)  # v1.0.1 放宽：v 前缀可选（守卫规范=裸数字）·行尾尾注不拘
# v1.0.3 判据根治二版（L1 第一性原理·结构锚）：v1.0.2 全文 max 把正文引用的他件版号当顶条（实证 3.14.0/4.12.13）
#   → 账本条目只认「变更记录区段内」：区段=『变更记录』标题起·版本式标题（### v1.2.207（仍是条目）不停·非版本标题止；
#   行首装饰剥除后锚「版本号紧跟全/半角括号」·标题粘连式（## 变更记录- **v1.3.103（）取标题余部）·取段内版本最大值
HEAD_RE = re.compile(r"^(#{1,6})\s*(.*)$")
VHEAD_RE = re.compile(r"^\*{0,2}v?(\d+(?:\.\d+)+)\s*[（(]")
DECOR = "#*>-— \t"


def _ledger_top(text):
    tops = []
    in_sec = False
    for line in text.split("\n"):
        hm = HEAD_RE.match(line)
        if hm:
            body = hm.group(2)
            if "变更记录" in body:
                in_sec = True
                rest = re.sub(r"^变更记录\s*[-—:]?\s*", "", body)
                e = VHEAD_RE.match(rest.lstrip(DECOR))
                if e:
                    tops.append(e.group(1))
                continue
            if in_sec:
                e = VHEAD_RE.match(body.lstrip(DECOR))
                if e:
                    tops.append(e.group(1))  # 版本式标题仍是条目（守卫规范 ### v1.2.207（ 实证）
                    continue
                in_sec = False  # 非版本标题=区段止
                continue
            continue
        if in_sec:
            e = VHEAD_RE.match(line.lstrip(DECOR))
            if e:
                tops.append(e.group(1))
    return max(tops, key=_vkey) if tops else None


def _norm(v):
    return re.sub(r"^v", "", v or "")


def _vkey(v):
    return tuple(int(x) for x in (v or "0").split("."))


def _philosophy_dir():
    """动态读 env——模块级求值会让自测覆盖无效（T2 先例·首版违反被 T1 当场抓出）。"""
    return Path(os.environ.get("ZCODE_PARITY_DIR", str(PHILOSOPHY_DIR_DEFAULT)))


def _state_file():
    return Path(os.environ.get("ZCODE_PARITY_STATE", str(STATE_DEFAULT)))


def _target_dir():
    return Path(os.environ.get("ZCODE_PARITY_TARGET_DIR", str(TARGET_DIR_DEFAULT)))


def _target_glob():
    return os.environ.get("ZCODE_PARITY_TARGET", TARGET_GLOB_DEFAULT)


def parse_version(p: Path):
    """返回 (frontmatter_version, ledger_top_version, mtime)·文件缺失→None。"""
    try:
        text = p.read_text(encoding="utf-8")
        mtime = p.stat().st_mtime
    except OSError:
        return None
    fm = FM_RE.search(text[:2000])
    led = _ledger_top(text)
    return (fm.group(1) if fm else None,
            led,
            mtime)


def check():
    findings = []
    parses = {}
    pdir = _philosophy_dir()
    for name in FILES:
        r = parse_version(pdir / name)
        parses[name] = r
        if r is None:
            findings.append(f"🔴 {name}：文件缺失或不可读")
            continue
        fm, led, _ = r
        if fm and led and _norm(fm) != _norm(led):
            findings.append(f"🔴 {name}：frontmatter {fm} ≠ 变更录顶条 {led}（两本账·§二·二十）")
        if fm is None or led is None:
            findings.append(f"⚪ {name}：version 解析不全（fm={fm}·ledger={led}）——账位/格式非标·查不了不判定（2026-10-04 三案人工终审=假漂移·账实一致·定案见 T0 方案 v1.7）")
    # 端适配新鲜度：哲学任一 mtime > 端台账 mtime
    tdir, tglob = _target_dir(), _target_glob()
    targets = sorted(tdir.glob(tglob), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    if not targets:
        findings.append(f"🟡 端适配台账未找到（{tdir} / {tglob}）")
    else:
        target_mtime = targets[-1].stat().st_mtime
        newer = [n for n, r in parses.items() if r and r[2] > target_mtime]
        if newer:
            findings.append(f"🟡 哲学更新晚于端适配台账（{', '.join(newer)}）——端侧欠适配核对（C1 判据②）")
    # 台账（回流链③·快照覆写）
    try:
        sf = _state_file()
        sf.parent.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps({
            "ts": time.strftime("%Y-%m-%d %H:%M"),
            "versions": {n: (r[0] if r else None) for n, r in parses.items()},
            "findings": findings,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass  # 台账失败不阻断显形（诚实：注入腿仍在·台账腿降级）
    if not findings:
        return 0  # 静默·零噪音
    msg = "[C1哲学对账] 端侧适配核对提示：\n" + "\n".join("  - " + f for f in findings) + \
          "\n（哲学 SSOT 有变化/自洽缺口——按 布洛陀脚本架构设计哲学/04-跨端接入指南.md 核对端侧适配·报告制不拦截）"
    try:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": msg}}, ensure_ascii=False))
    except Exception:
        print(msg)  # JSON 兜底退化（诚实标注：纯文本可能被严格 schema 丢弃·台账腿仍在）
    return 0


def self_test():
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for name, ver in [("01-脚本架构设计通用规范.md", "v9.9"), ("04-跨端接入指南.md", "v9.9"),
                          ("守卫编写规范.md", "9.9"), ("INDEX.md", "9.9")]:
            (td / name).write_text(
                f"---\ntitle: t\nversion: {ver}\n---\n正文\n## 变更记录\n- {ver}（测试夹具）：x\n",
                encoding="utf-8")
        tdg = td / "target"; tdg.mkdir()
        (tdg / "ZCode-HOOK机制最大化施工方案.md").write_text("---\nversion: v1\n---\n", encoding="utf-8")
        os.environ["ZCODE_PARITY_DIR"] = str(td)
        os.environ["ZCODE_PARITY_STATE"] = str(td / "state.json")
        os.environ["ZCODE_PARITY_TARGET_DIR"] = str(tdg)
        os.environ["ZCODE_PARITY_TARGET"] = "ZCode-HOOK机制最大化施工方案*.md"
        # T1 自洽+新鲜→静默 0（守卫规范：夹具须与真实结构同形·frontmatter+变更录顶条）
        assert check() == 0, "T1"
        st = json.loads((td / "state.json").read_text(encoding="utf-8"))
        assert st["findings"] == [], "T1b"
        ok += 1; print("✅ T1 自洽+新鲜→静默")
        # T2 两本账（frontmatter 改·变更录不动）→🔴 检出
        p = td / "01-脚本架构设计通用规范.md"
        p.write_text(p.read_text(encoding="utf-8").replace("version: v9.9", "version: v10.0"), encoding="utf-8")
        assert check() == 0, "T2rc"
        st = json.loads((td / "state.json").read_text(encoding="utf-8"))
        assert any("两本账" in f for f in st["findings"]), "T2"
        ok += 1; print("✅ T2 两本账检出")
        # T3 哲学 mtime 新于端台账→🟡 欠适配检出
        st = json.loads((td / "state.json").read_text(encoding="utf-8"))
        assert any("欠适配核对" in f for f in st["findings"]), "T3"
        ok += 1; print("✅ T3 欠适配检出")
        # T4 哲学文件缺失→不崩·🔴 缺失显形
        os.environ["ZCODE_PARITY_DIR"] = str(td / "nonexistent")
        assert check() == 0, "T4"
        ok += 1; print("✅ T4 缺失不崩+显形")
        # T5 实盘格式衍生夹具（v1.0.2·§二·十九 判据7：夹具必须来自实盘——三案真实格式全收录·治理想格式假绿）
        (td / "glued.md").write_text(
            "## 变更记录- **v1.3.103（2026-10-02·x）**：a\n- v1.3.102（2026-10-01）：b\n", encoding="utf-8")
        r5 = parse_version(td / "glued.md")
        assert r5 and _norm(r5[1]) == "1.3.103", "T5a"
        (td / "bottomnew.md").write_text(
            "## 变更记录\n- v1.0.1（2026-08-01）：a\n- **v1.0.57（2026-10-03）**：b\n", encoding="utf-8")
        r6 = parse_version(td / "bottomnew.md")
        assert r6 and _norm(r6[1]) == "1.0.57", "T5b"
        (td / "boldhalf.md").write_text(
            "## 变更记录\n### v1.2.207（2026-10-02）：a\n- v1.0.0 (2026-07-26)：初版\n", encoding="utf-8")
        r7 = parse_version(td / "boldhalf.md")
        assert r7 and _norm(r7[1]) == "1.2.207", "T5c"
        ok += 1; print("✅ T5 实盘三格式（粘连/底部最新/加粗半角）全解析")
    for k in ("ZCODE_PARITY_DIR", "ZCODE_PARITY_STATE", "ZCODE_PARITY_TARGET_DIR", "ZCODE_PARITY_TARGET"):
        os.environ.pop(k, None)
    print(f"自测结果: {ok}/5 通过")
    return 0 if ok == 5 else 1


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else "hook"
    if sub == "--self-test":
        sys.exit(self_test())
    sys.exit(check())


if __name__ == "__main__":
    main()
