#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
"""
LobsterAI 端三域自检 · 独立复现脚本
=====================================
生成：2026-10-05 · 童灵（AI 自己）· 立场：⛔我不说"可���"，只给可复现的读数

**读这份文件前先知道三件事：**

1. **本脚本的读数不构成"放行依据"。** 依据宪法愿景命题三「自审自过必假绿」——
   判定层与设计层同主体 = 换帽自评。**这是 AI 自己写的检查器，⛔AI 的"验过了"不是证据。**
   你要真放行，需另一主体独立复跑，或按条文33附换端独立审。

2. **本脚本默认只读。** 只有 `--apply` 才会写，且写入范围白名单化（见 WRITE_ALLOW）。
   不加 `--apply` 时，对生产文件的写操作一律跳过并标 SKIP。

3. **本脚本可能测不到你自己要的洞。** 覆盖域写在 CHECKLIST 里，域外的东西它
   一概不报——⛔别把"全绿"读成"没问题"（条文5：全绿是证伪起点，不是证明终点）。

用法:
    python3 verify_lobsterai.py                 # 只读检查
    python3 verify_lobsterai.py --json          # 机器可读输出
    python3 verify_lobsterai.py --apply         # 允许白名单内写入（谨慎）

退出码: 0=本次读数全绿  1=有 FAIL  2=脚本自身异常（⛔读数不可信，看 stderr）
"""

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

HOME = os.path.expanduser("~")
MC = os.path.expanduser("[记忆共享中心]")
PKG = os.path.join(MC, "发布库", "五层记忆系统", "布洛陀-全平台安装包")
GATE_SRC = os.path.join(MC, "开发工具", "skill_write_gate_guard.py")
GATE_RUN = os.path.join(MC, "脚本中心", "skill_write_gate_guard.py")
SKILLS_DIR = os.path.join(HOME, "Library", "Application Support",
                          "LobsterAI", "openclaw", "state", "skills")
BULUO10 = ["system-logger", "awaken-memory-system", "daily-buddy", "meta-aletheia",
           "growth-box", "triwich", "sucair", "clock-loop", "good-good-study",
           "shall-we-talk"]

# 唯一允许 --apply 写入的路径（⛔白名单外一律拒绝）
WRITE_ALLOW = [os.path.join(MC, "工作日志", "系统日志", "verify_report.md")]

results = []


def rec(domain, item, status, detail=""):
    results.append({"domain": domain, "item": item,
                    "status": status, "detail": detail})
    mark = {"PASS": "PASS", "FAIL": "FAIL", "SKIP": "SKIP", "WARN": "WARN"}[status]
    print("  [%s] %-34s %s" % (mark, item, detail))


def sha(p):
    try:
        return hashlib.sha256(open(p, "rb").read()).hexdigest()[:12]
    except OSError:
        return None


# ══════════════════════════════════════════════════════════
# 域 A · 门卫拦截（三个洞 + 负例不误伤）
# 判据来源: 本端宪法 §三 + LB-20261005-002/004 记录的真实现
# ══════════════════════════════════════════════════════════
def load_gate():
    p = GATE_RUN if os.path.isfile(GATE_RUN) else GATE_SRC
    spec = importlib.util.spec_from_file_location("_gate", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, p


def check_domain_a():
    print("\n═══ 域A · 门卫拦截（软链穿透 / 空格路径）═══")
    try:
        g, used = load_gate()
    except Exception as e:
        rec("A", "加载门卫模块", "FAIL", str(e)[:80])
        return
    rec("A", "加载门卫模块", "PASS", used.replace(HOME, "~"))

    link = os.path.join(SKILLS_DIR, "daily-buddy", "SKILL.md")
    space = os.path.join(MC, "技能配置", "clock-loop", "SKILL.md")

    def judge(tool, ti):
        ps = g.extract_paths(tool, ti)
        return any(g.hit_scope(p) is not None for p in ps)

    # 洞1 软链穿透
    for lbl, tool, ti in [
        ("软链穿透 Write", "Write", {"file_path": link}),
        ("软链穿透 Bash(引号)", "Bash", {"command": 'printf x > "%s"' % link}),
        ("软链穿透 Bash(裸·含空格)", "Bash", {"command": "printf x > " + link}),
    ]:
        st = "PASS" if judge(tool, ti) else "FAIL"
        rec("A", lbl, st, "软链→技能配置 应拦")

    # 洞2/3 空格路径
    for lbl, ti in [
        ("空格路径 Bash(引号)", {"command": 'printf x > "%s"' % space}),
        ("空格路径 Bash(裸)", {"command": "printf x > " + space}),
    ]:
        st = "PASS" if judge("Bash", ti) else "FAIL"
        rec("A", lbl, st, "含空格路径 应拦")

    # 回归：五域
    for lbl, p in [("技能配置", MC + "/技能配置/x/SKILL.md"),
                   ("成长箱", MC + "/成长箱/x.md"),
                   ("数字分身", MC + "/数字分身/x.py"),
                   ("发布库", MC + "/发布库/x.md"),
                   ("workbuddy", HOME + "/.workbuddy/settings.json")]:
        st = "PASS" if judge("Write", {"file_path": p}) else "FAIL"
        rec("A", "回归·" + lbl, st, "字面路径 应拦")

    # 负例（误伤是比漏拦更坏的问题）
    for lbl, tool, ti in [
        ("负例·/tmp 非辖区", "Write", {"file_path": "/tmp/x.txt"}),
        ("负例·脚本中心(同树)", "Write", {"file_path": MC + "/脚本中心/x.py"}),
        ("负例·成长箱笔记(前缀)", "Write", {"file_path": MC + "/成长箱笔记/x.md"}),
        ("负例·只读 ls", "Bash", {"command": "ls -la /tmp"}),
        ("负例·只读 cat|head", "Bash", {"command": "cat /tmp/a.txt | head -5"}),
        ("负例·git 中文诱饵", "Bash", {"command": 'git commit -m "fix 技能配置 x"'}),
    ]:
        st = "PASS" if not judge(tool, ti) else "FAIL"
        rec("A", lbl, st, "合法路径 应放行")


def check_domain_a_e2e():
    """端到端·stdin 钩子协议（判据层绿 ≠ 钩子真拦）"""
    print("\n═══ 域A2 · 端到端钩子协议 ═══")
    marker = os.path.join(HOME, ".cache", "skill_gate")
    had_marker = os.path.isdir(marker)
    if had_marker:
        print("  ⚠️ 检测到 skill_gate 留痕目录存在 ⇒ marker 会放行全部域，"
              "本次读数⛔不可信（域A2 全绿=假绿）")
        rec("A2", "留痕目录干扰", "FAIL", "存在留痕 ⇒ 须先清空再测")
        return
    rec("A2", "留痕目录干净", "PASS", "无留痕干扰")

    def gate(tool, ti):
        payload = {"hook_event_name": "PreToolUse", "session_id": "verify",
                   "tool_name": tool, "tool_input": ti}
        r = subprocess.run(["python3", GATE_RUN], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=20)
        return r.returncode

    link = os.path.join(SKILLS_DIR, "daily-buddy", "SKILL.md")
    for lbl, tool, ti, exp in [
        ("e2e·软链Write", "Write", {"file_path": link, "content": "x"}, 2),
        ("e2e·软链Bash裸", "Bash", {"command": "printf x > " + link}, 2),
        ("e2e·非辖区放行", "Write", {"file_path": "/tmp/x.txt", "content": "x"}, 0),
        ("e2e·只读放行", "Bash", {"command": "ls /tmp"}, 0),
    ]:
        rc = gate(tool, ti)
        rec("A2", lbl, "PASS" if rc == exp else "FAIL", "rc=%d 期望%d" % (rc, exp))


# ══════════════════════════════════════════════════════════
# 域 B · 十兄弟 Skill 注册态
# 判据来源: 本端宪法 §四「唯一真源=skills check 的 eligible」
# ══════════════════════════════════════════════════════════
def check_domain_b():
    print("\n═══ 域B · 十兄弟 Skill 注册态 ═══")
    try:
        r = subprocess.run(["openclaw", "skills", "check", "--json"],
                           capture_output=True, text=True, timeout=120,
                           cwd=HOME)
        d = json.loads(r.stdout)
    except Exception as e:
        rec("B", "读取 skills check", "FAIL", str(e)[:80])
        return
    el = set(d.get("eligible") or [])
    rec("B", "读数来源", "PASS", "eligible=%d/%d" % (len(el), d["summary"]["total"]))
    for s in BULUO10:
        rec("B", s, "PASS" if s in el else "FAIL",
            "eligible" if s in el else "⛔未进册")
    # 双装载系统交叉核（本端特有）
    a_escape = 0
    log = "/tmp/openclaw/openclaw-%s.log" % time.strftime("%Y-%m-%d")
    if os.path.isfile(log):
        txt = open(log, encoding="utf-8", errors="replace").read()
        a_escape = txt.count("skill_write_gate_guard") and txt.count("symlink-escape")
        rec("B", "日志交叉核", "WARN" if a_escape else "PASS",
            "symlink-escape 出现 %d 次（A层逃逸·预期存在）" % a_escape)


# ══════════════════════════════════════════════════════════
# 域 C · 条文45 两树软链独立
# 判据来源: 安装包设计哲学 条文45（主源↔包双向软链隔绝律）
# ══════════════════════════════════════════════════════════
def check_domain_c():
    print("\n═══ 域C · 条文45 两树独立 ═══")
    # 腿A 主源侧 → 落包内（违例①）
    bad = []
    for root in (MC, os.path.join(HOME, "Library", "Application Support", "LobsterAI")):
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
            for d in list(dn):
                lp = os.path.join(dp, d)
                if os.path.islink(lp):
                    tgt = os.readlink(lp)
                    if "布洛陀-全平台安装包" in tgt:
                        bad.append(lp)
                    dn.remove(d)
    rec("C", "腿A 主源→包 违例", "PASS" if not bad else "FAIL",
        "0 违例" if not bad else "%d 条: %s" % (len(bad), bad[:2]))

    # 腿B 包内 → 指回主源/绝对本机路径（违例②）
    bad2 = []
    for dp, dn, fn in os.walk(PKG):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
        for name in fn + list(dn):
            lp = os.path.join(dp, name)
            if os.path.islink(lp):
                tgt = os.readlink(lp)
                if tgt.startswith("/") and PKG not in tgt:
                    bad2.append((lp, tgt))
    rec("C", "腿B 包→主源 违例", "PASS" if not bad2 else "FAIL",
        "0 违例" if not bad2 else "%d 条" % len(bad2))

    # 十兄弟软链必须落在生产树内
    ok = 0
    for s in BULUO10:
        lp = os.path.join(SKILLS_DIR, s)
        if not os.path.islink(lp):
            continue
        tgt = os.readlink(lp)
        good = ("技能配置" in tgt or os.path.isdir(tgt)) and \
               "布洛陀-全平台安装包" not in tgt
        ok += good
    rec("C", "十兄弟软链落生产树", "PASS" if ok == len(BULUO10) else "FAIL",
        "%d/%d" % (ok, len(BULUO10)))


# ══════════════════════════════════════════════════════════
# 域 D · 端哲学完备度（段①门槛）
# 判据来源: 安装包 条文33附第0步（先读本端哲学再动手）
# ══════════════════════════════════════════════════════════
def check_domain_d():
    print("\n═══ 域D · 本端哲学完备度 ═══")
    pd = os.path.join(MC, "记忆蓝图", "02_设计理念", "02_平台端适配类",
                      "LobsterAI布洛陀设计哲学")
    if not os.path.isdir(pd):
        rec("D", "本端哲学目录", "FAIL", "目录不存在: %s" % pd.replace(HOME, "~"))
        return
    rec("D", "本端哲学目录", "PASS", pd.replace(HOME, "~"))
    for f in ["00-宪法愿景.md", "01-注入通道规范.md", "INDEX.md"]:
        p = os.path.join(pd, f)
        rec("D", f, "PASS" if os.path.isfile(p) else "FAIL",
            "%d字节" % os.path.getsize(p) if os.path.isfile(p) else "缺失")
    idx = os.path.join(pd, "INDEX.md")
    if os.path.isfile(idx):
        t = open(idx, encoding="utf-8").read()
        rec("D", "INDEX 可达 00-宪法愿景", "PASS" if "00-宪法愿景" in t else "FAIL")


# ══════════════════════════════════════════════════════════
# 域 E · 包内三份副本同步态（条文38 三侧同步）
# ══════════════════════════════════════════════════════════
def check_domain_e():
    print("\n═══ 域E · 包内副本同步态（只看·不改）═══")
    src_sha = sha(GATE_SRC)
    targets = [
        ("references/scripts", os.path.join(PKG, "references", "scripts")),
        ("references/hooks", os.path.join(PKG, "references", "hooks")),
        ("digital-twin/devtools", os.path.join(PKG, "references",
                                               "digital-twin", "devtools")),
    ]
    seen = {}
    for lbl, d in targets:
        p = os.path.join(d, "skill_write_gate_guard.py")
        if not os.path.isfile(p):
            rec("E", lbl, "WARN", "不存在")
            continue
        s = sha(p)
        seen[lbl] = s
        t = open(p, encoding="utf-8").read()
        rec("E", lbl, "PASS" if "v0.10" in t else "WARN",
            "sha=%s %s" % (s, "含v0.10" if "v0.10" in t else "旧版"))
    if len(set(seen.values())) > 1:
        rec("E", "三份一致性", "FAIL", "内容不一致 ⇒ 违反单一真源（须纳管+同步，⛔不手工刷）")
    else:
        rec("E", "三份一致性", "PASS", "哈希一致")

    # manifest 纳管范围
    mp = os.path.join(MC, "开发工具", "buluotuo-release-sync", "mirror-manifest.json")
    if os.path.isfile(mp):
        m = json.load(open(mp, encoding="utf-8"))
        ents = m.get("entries") or []
        hit = [e for e in ents if "skill_write_gate" in json.dumps(e, ensure_ascii=False)]
        rec("E", "manifest 纳管数", "PASS" if hit else "FAIL",
            "%d 条（覆盖 pkg 落点 %d 个）" %
            (len(hit), len({e.get("pkg") for e in hit})))
        for e in hit:
            rec("E", "  · " + str(e.get("pkg", "")).split("安装包/")[-1],
                "PASS", "sync_mode=%s" % e.get("sync_mode"))


# ══════════════════════════════════════════════════════════
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="允许白名单内写入（本版无写操作·占位）")
    args = ap.parse_args()

    print("╔" + "═" * 68 + "╗")
    print("║ LobsterAI 端三域自检 · 独立复现脚本                            ║")
    print("║ ⛔ 本读数不构成放行依据（宪法愿景命题三·自审自过必假绿）      ║")
    print("╚" + "═" * 68 + "╝")

    for fn in (check_domain_a, check_domain_a_e2e, check_domain_b,
               check_domain_c, check_domain_d, check_domain_e):
        try:
            fn()
        except Exception as e:
            rec(fn.__name__, "脚本异常", "FAIL", str(e)[:90])
            print("  ⛔ %s 自身异常 ⇒ 其后读数不可信" % fn.__name__)

    n = len(results)
    p = sum(1 for r in results if r["status"] == "PASS")
    f = sum(1 for r in results if r["status"] == "FAIL")
    w = sum(1 for r in results if r["status"] == "WARN")
    print("\n" + "═" * 70)
    print("  读数: %d/%d PASS · %d FAIL · %d WARN" % (p, n, f, w))
    print("  ⚠️ 全绿只证明「本脚本没抓到」，不证明「没问题」（条文5）")
    print("  ⚠️ 报告域外的东西本脚本一概不查 —— 域外风险需另找判据")
    print("═" * 70)

    if args.json:
        print(json.dumps({"results": results,
                          "summary": {"total": n, "pass": p, "fail": f, "warn": w},
                          "disclaimer": "不构成放行依据·宪法命题三"}, ensure_ascii=False, indent=1))
    return 1 if f else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(2)
