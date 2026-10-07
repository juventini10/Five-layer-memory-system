#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_antibody_gate.py —— 抗体门禁回归测试（负例驱动 + 消费端契约）
Version: 1.0.0 (2026-09-15)

为什么用 python 写测试：一次进程内跑完全部断言，避免"每条用例一个子进程"把沙箱
文件打开预算打爆（2026-09-15 实测：growth_box_check.sh 全量实跑 exit 137 即此因）。
唯一一次外部调用 = bash 消费端契约测试（必须真跑 bash，否则测的是复制品而非契约）。

用法：python3 tests/test_antibody_gate.py   （exit 0 全通过 / 1 有失败）
立场卡依据：C-067 门禁须真机双关验证 · S167/S172 判据机制须过负例测试 · S323 检测规则不能自设自验
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import antibody_gate as G  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✅ " if cond else "  🔴 ") + name + ((" :: " + str(detail)) if (detail and not cond) else ""))


def main():
    print("🧪 antibody_gate 回归测试 v%s" % G.VERSION)
    print(f"   gate = {os.path.join(HERE, '..', 'scripts', 'antibody_gate.py')}")

    # 1) 内建自检（负例 14 + 正例 6 + 提取器防误 1）
    print("\n[1] 内建自检夹具")
    rc = G.selftest()
    check("selftest 全绿", rc == 0, "selftest rc=%s" % rc)

    # 2) 提取口径：规则叙述不得冒充抗体
    print("\n[2] 提取器防误")
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write(
        "**铁律**：任何 `\U0001F6E1 复发检测条件` 命令禁止 `&& exit 0 || exit 0`。\n"
        "- \U0001F6E1 **复发检测条件**：`test ! -f \"/abs/a.md\"` — 抗体甲\n"
        "- \U0001F6E1 **复发检测条件**：`test -f foo.md` — 抗体乙\n"
    )
    tmp.close()
    rows = G.extract_antibodies(tmp.name)
    os.unlink(tmp.name)
    check("只提取真字段行（2 条，叙述不冒充）", len(rows) == 2, rows)
    check("行号口径 = 行首计数", [r[0] for r in rows] == [2, 3], [r[0] for r in rows])
    check("取字段后第一对反引号", rows[0][1] == 'test ! -f "/abs/a.md"', rows[0][1])
    check("标题取 — 之后段", rows[0][2] == "抗体甲", rows[0][2])

    # 3) 九项判定逐码负例（每码至少一条「只有它能拦」的专属夹具·§3.9）
    print("\n[3] 九项判定逐码")
    cases = [
        ("C1", ""), ("C1", "  "), ("C1", "..."),
        ("C2", 'a\nb'),
        ("C2", 'test -f "/a.md"; grep -q x "/b.md"'),
        ("C3", 'grep -q "unterminated "$HOME/x.md"'),
        ("C4", "exit 0"), ("C4", "grep -q x \"/a.md\" || true"), ("C4", "test -f \"/a.md\"; :"),
        ("C5", "test -f config.json"), ("C5", "grep -q x ./scripts/y.sh"),
        # C7/C8/C9 各配专属负例（§3.9：每条判据要有「只有它能拦」的夹具）
        # C7 恒假=od 输出含双空格而模式写单空格（2026-09-18 真机 53 次假红原形）。本条 09-18 已从 gate 本体
        # selftest 的 good 移入 bad，但**本兄弟文件漏修**（仍当正例＝测试固化错误行为·2026-09-19 归位）
        ("C7", '! find "[记忆共享中心]/发布库" -maxdepth 2 -name setup.ps1 -print0 | xargs -0 -n1 sh -c \'head -c3 "$0" | od -An -tx1 | grep -q "ef bb bf"\''),
        ("C8", '! "[记忆共享中心]/技能配置/growth-box/scripts/antibody_gate.py" --selftest'),
        ("C9", 'grep -qE \'Status.*(pending|active)\' "[记忆共享中心]/成长箱/learnings/x.md"'),
    ]
    for code, cmd in cases:
        codes = [v.code for v in G.validate_cmd(cmd)]
        check("负例 %s :: %s" % (code, cmd[:36].replace("\n", "\\n")), code in codes, codes)

    # 4) 正例：真实存量抗体的典型形态不得误拦
    print("\n[4] 正例（存量真实形态）")
    goods = [
        'test ! -f "[记忆共享中心]/脚本中心/content-gate.py"',
        "! grep -q -- '/-卡片\\[' \"[记忆共享中心]/脚本中心/kb_index_guard.sh\"",
        '! diff <(ls "[记忆共享中心]/A") <(ls "[记忆共享中心]/B") >/dev/null',
        "grep -rqE '皮叔在记录|模板应用' ~/[记忆共享中心]/发布库",
    ]
    for cmd in goods:
        codes = [v.code for v in G.validate_cmd(cmd)]
        check("正例放行 :: %s" % cmd[:44], not codes, codes)

    # 5) 真机双关：默认双源零假阳性 + C6 同文件重复才报
    print("\n[5] 真机源扫描")
    src = G.default_sources()
    scanned, vs = G.scan_files(src)
    check("源文件可枚举", len(src) >= 2, len(src))
    check("扫到抗体（>0）", scanned > 0, scanned)
    codes = sorted({v.code for v in vs})
    check("无 C1/C2/C3/C4/C5 假阳性（仅允许 C6）", all(c == "C6" for c in codes), codes)
    check("每条违规都带行号", all(v.line > 0 for v in vs), [(v.code, v.line) for v in vs])
    dup_in_same_file = all("本文件" in v.detail for v in vs if v.code == "C6")
    check("C6 限定同文件（跨源晋升复制不报）", dup_in_same_file, [(v.code, v.detail) for v in vs])

    # 6) 消费端契约：bash 侧按 US 分隔读取并复原字段（契约破裂=下游静默错位）
    print("\n[6] bash 消费端契约")
    fx = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    fx.write(
        "- \U0001F6E1 **复发检测条件**：`test ! -f \"/abs/a.md\"` — 好抗体\n"
        "- \U0001F6E1 **复发检测条件**：`test -f foo.md` — 相对路径抗体\n"
        "- \U0001F6E1 **复发检测条件**：`test ! -f \"/abs/a.md\"` — 复用同抗体（应只进提示列）\n"
    )
    fx.close()
    script = r'''
set -eo pipefail
n=0; flagged=0; c6=0
while IFS=$'\x1f' read -r src_name lineno cmd title codes dup infos; do
  [[ -z "${cmd:-}" ]] && continue
  n=$((n+1))
  if [[ -n "${codes:-}" ]]; then flagged=$((flagged+1)); fi
  if [[ "${infos:-}" == *C6* ]]; then c6=$((c6+1)); fi
done < <("%s" "%s" --list "%s")
echo "N=$n FLAGGED=$flagged C6=$c6"
''' % (sys.executable, os.path.join(HERE, "..", "scripts", "antibody_gate.py"), fx.name)
    out = subprocess.run(["bash", "-c", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.unlink(fx.name)
    line = out.stdout.decode().strip().split("\n")[-1] if out.stdout else ""
    check("bash 读契约：3 条全读到", "N=3" in line, line)
    check("bash 读契约：仅 1 条进硬违规列（C6 已归提示列）", "FLAGGED=1" in line, line)
    check("bash 读契约：C6 进提示列 1 条", "C6=1" in line, line)

    # 7) 生成器：相对路径必须被拒（设计端消除相对路径抗体）
    print("\n[7] 生成器守卫")
    rc = subprocess.run([sys.executable, os.path.join(HERE, "..", "scripts", "antibody_gate.py"),
                         "--gen", "file-missing", "relative/path.md"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    check("生成器拒相对路径（exit 2）", rc.returncode == 2, rc.returncode)
    rc2 = subprocess.run([sys.executable, os.path.join(HERE, "..", "scripts", "antibody_gate.py"),
                          "--gen", "text-absent", "/abs/x.md", "坑"], stdout=subprocess.PIPE)
    gen = rc2.stdout.decode().strip()
    check("生成器产出可直接使用（反断言）", gen.startswith("! grep -q") and gen.endswith('"/abs/x.md"'), gen)
    check("生成物自身过门禁", not G.validate_cmd(gen), [v.code for v in G.validate_cmd(gen)])

    print("\n" + "=" * 54)
    print("结果：通过 %d · 失败 %d" % (len(PASS), len(FAIL)))
    if FAIL:
        print("失败项：" + ", ".join(FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
