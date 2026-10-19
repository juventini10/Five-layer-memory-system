#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# REG: family=发布工具|registry=记忆蓝图/04_系统文件设计/安装包设计哲学/03-进度看板.md
"""test_legacy_upgrade.py — 历史形态升级夹具（条文54 的机械承载件）

病根（2026-10-09 布洛陀2.1.0上游反馈四缺陷实证）：包侧全部判据（smoke P1-P7/干净度/
账实对账）测的都是「账与结构」，没有一条测「安装器对历史文件形态的升级行为」——
四条 P0/P1 缺陷（无标记段plain双份注入、手工维护yaml被冲、双名并存误报、旧名残留）
全部藏在行为面，打包时全绿零拦截。本夹具把「用户机上真实存在过的文件形态」固化为
常驻用例：三负例（必拦截）+ 两正例（必放行），修复不配套本件=条文54违例。

用法：python3 test_legacy_upgrade.py            # 自动定位包根
      python3 test_legacy_upgrade.py --pkg-root <包根绝对路径>
退出码：0=全过；1=任一用例失败（输出逐条 ✅/❌）。⛔恒零形态禁止（抗体判据同源）。
源机可跑性（条文53）：包根四级探测 env BULUOTUO_PKG_ROOT → 自我定位（本件位于
<root>/references/scripts/ 上两级）→ 发布库默认 → 全不可得 rc=1 显形报
「包根不可定位」，⛔不静默假绿。
"""
# Win console UTF-8 guard (auto by build chain · V9)
try:
    import sys as _v9sys; _v9sys.stdout.reconfigure(encoding="utf-8"); _v9sys.stderr.reconfigure(encoding="utf-8"); _v9sys.stdin.reconfigure(encoding="utf-8")
except Exception: pass
import argparse, contextlib, hashlib, io, os, re, shutil, sys, tempfile
import importlib.util

def _detect_pkg_root():
    env = os.environ.get("BULUOTUO_PKG_ROOT")
    if env and os.path.isfile(os.path.join(env, "install_scripts.py")):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.normpath(os.path.join(here, "..", ".."))  # references/scripts 上两级=包根
    if os.path.isfile(os.path.join(cand, "install_scripts.py")):
        return cand
    default = os.path.expanduser(
        "[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包")
    if os.path.isfile(os.path.join(default, "install_scripts.py")):
        return default
    return None


def _load_isroot(pkg):
    spec = importlib.util.spec_from_file_location(
        "iscript_rootfix", os.path.join(pkg, "install_scripts.py"))
    IS = importlib.util.module_from_spec(spec)
    sys.modules["iscript_rootfix"] = IS
    spec.loader.exec_module(IS)
    return IS


def _md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg-root", default=None)
    a = ap.parse_args()
    pkg = a.pkg_root or _detect_pkg_root()
    if not pkg:
        print("❌ 包根不可定位（env/自我定位/默认三级全空）——显形不静默")
        return 1
    IS = _load_isroot(pkg)
    TL = os.path.join(pkg, "references/templates/用户基本规则-铁律版.md")

    results = []
    def ck(name, cond, extra=""):
        results.append((name, bool(cond), extra))

    tmp = tempfile.mkdtemp(prefix="legacy-upg-")
    try:
        mc = os.path.join(tmp, "mc")
        os.makedirs(os.path.join(mc, "记忆规则"))
        # fill 上下文与安装器同 mc（占位符展开一致·否则等价判定假红，夹具自身先中条文53的坑）
        filled = IS._fill_text(open(TL, encoding="utf-8").read(), mc)
        PLAIN = "\n".join(l for l in filled.splitlines()
                          if not l.strip().startswith("<!-- BULUOTUO:"))
        dst = os.path.join(mc, "记忆规则/用户基本规则-铁律版.md")

        # 负例N1：无标记段 plain 旧文件（幂等覆盖时代产物）→ 必拦（全等价不注入）
        open(dst, "w", encoding="utf-8").write(PLAIN)
        b1 = _md5(dst)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = IS.install_rule_files(mc)
        seg = [o for o in out if o[0].endswith("铁律版.md")][0]
        ck("N1 plain旧文件→PRECHECK_SKIP且不写盘",
           seg[1] == "PRECHECK_SKIP" and _md5(dst) == b1 and "全等价" in seg[2], seg[2][:48])

        # 负例N2：号位错开+同号异文（外部用户定制形态）→ 必拦且冲突行显形
        cu = re.sub(r"(### 铁律-013[^\n]*\n)", r"\g<1>【定制：脱敏红线】\n", PLAIN)
        open(dst, "w", encoding="utf-8").write(cu)
        b2 = _md5(dst)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out = IS.install_rule_files(mc)
        seg = [o for o in out if o[0].endswith("铁律版.md")][0]
        ck("N2 同号异文→拦截+文件未动",
           seg[1] == "PRECHECK_SKIP" and _md5(dst) == b2, seg[2][:48])
        ck("N2b 冲突行显形", "同号异文" in buf.getvalue())

        # 负例N3：外部维护声明 yaml → 必 SKIP 保留
        yd = os.path.join(mc, "记忆规则/rule_triggers.yaml")
        open(yd, "w", encoding="utf-8").write(
            "# ⛔ 本机不引入 gen_rule_triggers.py 编译器（手工维护）\nx: 1\n")
        b3 = _md5(yd)
        with contextlib.redirect_stdout(io.StringIO()):
            rd = IS.install_rule_data(mc)
        ck("N3 手工维护声明→SKIP未覆盖",
           any("SKIP" in x for x in rd) and _md5(yd) == b3, str(rd))

        # 正例P1：全新安装（无历史文件）→ 照常 CREATED 写入
        open(dst, "w", encoding="utf-8").write(
            "# 铁律版\n\n> 版本：v8.30 |（占位）\n")
        with contextlib.redirect_stdout(io.StringIO()):
            out = IS.install_rule_files(mc)
        seg = [o for o in out if o[0].endswith("铁律版.md")][0]
        ck("P1 新装→CREATED不被预检误伤", seg[1] == "CREATED", seg[1])

        # 正例P2：已有标记段复装 → 常规路径（UNCHANGED/UPDATED），预检不重复介入
        with contextlib.redirect_stdout(io.StringIO()):
            out = IS.install_rule_files(mc)
        seg = [o for o in out if o[0].endswith("铁律版.md")][0]
        ck("P2 有段复装→常规状态", seg[1] in ("UNCHANGED", "UPDATED"), seg[1])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    fails = [r for r in results if not r[1]]
    for name, ok, extra in results:
        print("%s %s%s" % ("✅" if ok else "❌", name, (" | " + str(extra)) if extra else ""))
    print("RESULT: %d/%d 通过" % (len(results) - len(fails), len(results)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
