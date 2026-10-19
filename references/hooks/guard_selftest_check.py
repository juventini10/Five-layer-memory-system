#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard_selftest_check.py v0.3.3 — 守卫家族自测聚合元守卫（检测退化·报告制+差集检测）

v0.2.5（2026-09-18·Qoder CN·发现窗口根治）：`discover()` 原先只读文件头 20000 字节，
  而 Python 守卫的 `--self-test` 注册几乎都在文件尾部的 `main()` 里 ⇒ 有夹具却被差集判成
  "无 self-test"（实锤：guard_doc_consistency.py 已带 17 例夹具却连续列⚠️）。现整文件读取
  （上限 400KB）。抽象：**判据的读取窗口必须覆盖证据的实际位置**——"文件存在≠证据在窗口内"，
  与 route_source_scan 的 schema 盲区同族（仪器不测 ≠ 没有缺项）。
  同时打印位版本号收归 `SELF_VERSION` 单一常量（原三处硬编码 "v0.2" 与 docstring v0.2.4 双源）。

v0.2.4（2026-08-30·实锤律+归因律）：子进程输出改**字节捕获 + errors="replace" 解码**——
  旧写法 text=True 遇 macOS awk 多字节告警吐的裸字节会抛 UnicodeDecodeError，被
  `except Exception` 整体吞成 "❌ 夹具异常"，把聚合层自身的解码故障归因给被测夹具
  （实测 changelog-guard/tests/run_tests.sh 直跑 20/20 绿，聚合层却报红 → --strict 假红）。
  异常消息同时补上异常类型名，⛔ 不带原因的"异常"不合法。

机制（2026-08-22 立·changelog_guard v1.10 三缺陷案反哺）：
  changelog_guard 去重自 v1.5.1 死亡半个月无人知——守卫有 --self-test 惯例但
  ①夹具散落（/tmp 用完即丢·changelog-guard 曾无 tests/）②无聚合器（没人定期全跑）
  ③无退化检测（守卫坏了只能靠皮叔追问）。本脚本补第三环：
  自动发现两类自测资产并聚合执行——
    A. 内置 --self-test 的守卫（.py/.sh 机械 grep 发现·零登记负担）
    B. tests/run*.sh 夹具（对齐 l3_conclusion_guard_tests/run.sh + changelog-guard/tests/run_tests.sh 先例）
  与 registry_guards.sh（~/.workbuddy/hooks/·changelog-guard 族 *.sh 的 --check 体检）互补：
  它聚合"登记一致性"，本脚本聚合"自测健康"。

v0.2 新增（2026-08-22·皮叔质疑"session_memory_quality_guard.py 零 self-test"后补洞）：
  差集检测（注册表登记 vs 自测清单的差=无自测守卫显形）：
    - 读取守卫编写规范注册表（[记忆共享中心]/脚本中心/布洛陀脚本架构设计哲学/守卫编写规范.md）
    - 提取所有登记的守卫文件名（| xxx.py | 或 | xxx.sh |）
    - 对比 discover() 发现的有 self-test 的守卫
    - 差集 = 注册表有但 discover 没发现的 = 无 self-test 守卫 → 显形告警
  解决 v0.1 漏洞：只发现"有自测的"对"无自测守卫"静默→§3.0·5 纪律①被跳过无人知

设计原则（守卫三纪律）：
  - 失败默认放行（exit 0 报告制）；--strict 才以红非零退出（CI/巡检承载用）
  - 逐项 timeout（默认 60s·防 self-test 挂死拖垮调用方）
  - SKIP 名单（--skip 正则）：有副作用未自清理的自测先跳过并显形，不静默
  - 明细落 logs/guard_selftest_check.log（对齐家族日志惯例）

用法：
  python3 guard_selftest_check.py                # 全家族聚合（报告制+差集检测）
  python3 guard_selftest_check.py --strict       # 任一红→exit 1（供 patrol/CI）
  python3 guard_selftest_check.py --skip fswatch # 跳过匹配正则的自测
  python3 guard_selftest_check.py --list         # 只列发现清单不执行
  python3 guard_selftest_check.py --diff-only    # 只做差集检测（不执行自测）
"""
# Win console UTF-8 guard (auto by clock-loop 1.7.2)
try:
    import sys; sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
except Exception: pass
import argparse
import glob
import os
import re
import subprocess
import sys
from datetime import datetime

BASE = os.path.expanduser("[记忆共享中心]")
DEV = os.path.join(BASE, "开发工具")
# 扫描根：开发工具（公共目录）+ 路由家族 scripts（注册表 v1.2.12 登记的自测守卫住址·2026-08-13 去内联化）
#   + 技能配置（各 Skill scripts/ 自带夹具，如 system-logger/install_watch.sh）
#   + 脱敏门禁（发布阻断门禁·v1.1.1 起带 F1-F10 夹具）
# ——原因是 2026-08-30 实测：新写的两个自测都住在旧扫描域外，注册表报"19 项全绿"
#    却一项没跑到 = 自测资产脱管（有自测≠有人跑）。根按目录结构声明，新增夹具自动入册。
SCAN_ROOTS = [
    DEV,
    os.path.join(BASE, "自定义层", "待完成工作", "路由家族", "scripts"),
    os.path.join(BASE, "技能配置"),
    os.path.join(BASE, "发布库", "五层记忆系统", "存档包", "脱敏门禁"),
    os.path.join(BASE, "数字分身", "数字分身脚本"),
    os.path.join(BASE, "数字分身", "scripts"),
]
# [C] pytest 裸夹具发现域（v0.3.2·2026-10-10 Loop反哺：17件 test_*.py 夹具因本机无执行器从未被跑=结构性静默）
C_ROOTS = [
    os.path.join(BASE, "脚本中心"),
    DEV,
    os.path.join(BASE, "技能配置"),
    os.path.join(BASE, "数字分身", "数字分身脚本"),
    os.path.join(BASE, "数字分身", "scripts"),
    os.path.join(BASE, "自定义层", "待完成工作", "路由家族", "scripts"),
]
C_SKIP_SEG = ("/.venv", "/node_modules", "/_vendored/", "/site-packages", "/extensions/", "/记忆琥珀/", "/_archive/", "/归档/", "/tests/")
LOG = os.path.join(DEV, "logs", "guard_selftest_check.log")
TIMEOUT_DEFAULT = 60
SELF_VERSION = "v0.3.3"  # 打印位唯一真源（与 docstring 首行同源·⛔不在 print 里另写死）

# v0.3.3（同日S8：[C]tests段off-by-one修正+第三方pip依赖域剔除·deepseek/pyJianYingDraft 8件出网）
# v0.3.2（同日①批：数字分身域入网+[C]pytest裸夹具批跑）
# v0.3.1（同日R3补刀：--selftest拼写族/R-B业务参数门/差集CJK/版本同源）
# v0.3.0（2026-10-10·clock-loop 自检接线对账 Loop 反哺·两病同治）：
#   ①结构性盲区：旧 SELFTEST_RE 只认 self[-_]test，对 --selfcheck 族全盲（实锤：候选140件中
#     45% 自检入口吃不到，position3/heartbeat/inject 族均在盲区）。现扩族 self[-_]test|selfcheck；
#     --check-only 不纳入自动执行（语义可能是产品模式非自检·P10待人工复核，宁漏不假跑）。
#   ②假发现：旧判据整文件正则把注释/函数名里的 self-test 字样当真入口（实锤：末run 3 件
#     unrecognized arguments 假红）。现收紧：旗须出现在参数解析语境行（add_argument/==/in/case/argv），
#     纯注释行剔除；执行命令按件选旗。
# 痕迹粗筛（差集检测兼容用；真入选以 detect_entry_flag 为准）
SELFTEST_RE = re.compile(r'self[-_]?test|selfcheck', re.IGNORECASE)
_SELF_FLAG_LINE = re.compile(
    # v0.3.1 R-B：add_argument 须是开关形态（带action/nargs，或120字符内无default=）——
    # 业务参数型 --selfcheck（shadow_append案：default="—"的内容字段）不再算自检入口
    r'(?:add_argument\(\s*["\']--?(?:self[-_]?test|selfcheck)["\'](?![^)]{0,120}default=)[^)]{0,120}(?:action|nargs)'
    r'|add_argument\(\s*["\']--?(?:self[-_]?test|selfcheck)["\']\s*\)'
    r'|["\']--?(?:self[-_]?test|selfcheck)["\']\s+in\s'
    r'|(?:==|!=)\s*["\']--(?:self[-_]?test|selfcheck)'
    r'|["\']--?(?:self[-_]?test|selfcheck)["\']\s*(?:==|in\b)'
    r'|\bin\s*\([^)]{0,80}--(?:self[-_]?test|selfcheck)'
    r'|argv[^\n]{0,50}--?(?:self[-_]?test|selfcheck)'
    r'|--(?:self[-_]?test|selfcheck)[^)\s]*\)'
    r'|case[^\n]{0,40}--?(?:self[-_]?test|selfcheck))', re.IGNORECASE)


def detect_entry_flag(text):
    """返回该文件真实注册的自检旗（'--self-test'/'--selfcheck'/None）；纯注释行不算。"""
    best = None
    for ln in text.splitlines():
        if ln.lstrip().startswith("#"):
            continue
        if _SELF_FLAG_LINE.search(ln):
            low = ln.lower()
            m = re.search(r"--(?:self[-_]?test|selfcheck)", low)
            if m and "test" in m.group(0):
                return m.group(0)          # --self-test / --selftest / --self_test 原样回传
            if m:
                best = best or m.group(0)  # --selfcheck
    return best


def discover():
    """返回 [(类型, 路径, 执行命令)]：A=内置 self-test 守卫；B=tests/run*.sh 夹具。
    ⛔ 排除自身（docstring 提及 self-test 会自指误发现·2026-08-22 首跑实证）。"""
    self_real = os.path.realpath(__file__)
    items = []
    # A. 内置 self-test 守卫（各扫描根两层深度：根 + 子目录 scripts/）
    candidates = []
    for root in SCAN_ROOTS:
        for pat in ("*.py", "*.sh", "*/*.py", "*/*.sh", "*/*/*.py", "*/*/*.sh"):
            candidates.extend(glob.glob(os.path.join(root, pat)))
    for p in sorted(set(candidates)):
        rp = os.path.realpath(p)
        if rp == self_real:
            continue
        if "/tests/" in p or "/__pycache__/" in p or ".bak" in p or "/logs/" in p:
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                # 整文件读取：Python 守卫的 --self-test 注册在 main()（文件尾部），
                # 原先只读头 20000 字节 ⇒ 有夹具却被判"无自测"（实锤 guard_doc_consistency.py 17 例）。
                text = f.read(400000)
        except Exception:
            continue
        if not SELFTEST_RE.search(text):
            continue
        flag = detect_entry_flag(text)
        if not flag:
            continue  # 入口语境收紧：注释/函数名字样不再算发现（v0.3.0 假发现根治）
        if p.endswith(".py"):
            items.append(("A", p, ["python3", p, flag]))
        else:
            items.append(("A", p, ["bash", p, flag]))
    # B. tests 夹具（run*.sh）
    for p in sorted(glob.glob(os.path.join(DEV, "**", "tests", "run*.sh"), recursive=True)):
        items.append(("B", p, ["bash", p]))
    # B'. 家族先例：l3 夹具目录无 tests/ 子层（本体即夹具目录）
    l3 = os.path.join(DEV, "l3_conclusion_guard_tests", "run.sh")
    if os.path.isfile(l3):
        items.append(("B", l3, ["bash", l3]))
    # C. pytest 裸夹具（v0.3.2：test_*.py 递归发现·缺 pytest 由执行端显式 SKIP·⛔不静默）
    try:
        import pytest as _pt  # noqa: F401
        _has_pytest = True
    except Exception:
        _has_pytest = False
    if _has_pytest:
        for cr in C_ROOTS:
            if not os.path.isdir(cr):
                continue
            for dirpath, dirnames, filenames in os.walk(cr):
                dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("__pycache__", "node_modules", "logs", "cache")]
                # v0.3.3：tests 段判定修正——dirpath 恰以 /tests 结尾时旧写法漏剔（off-by-one·
                # 本行缺陷由 [C] 首跑逮住：deepseek-harness sdk/tests 第三方件入网=仪器自犯其病·登记自证律实证）
                _dp = dirpath + "/"
                if any(seg in _dp for seg in ("/.venv", "/node_modules", "/_vendored/", "/site-packages", "/extensions/", "/记忆琥珀/", "/_archive/", "/归档/", "/tests/", "/deepseek-harness/", "/video-shotcraft", "/jianying-export/")):
                    continue
                for f in filenames:
                    if re.match(r"^(test_.+|.+_test|.+_selftest)\.py$", f):
                        items.append(("C", os.path.join(dirpath, f),
                                      ["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", os.path.join(dirpath, f)]))
    else:
        log_line("[C] pytest 不可用——裸夹具批本轮显式SKIP（非静默：见运行报告⏭️行）")
    # 去重
    seen, out = set(), []
    for t, p, cmd in items:
        rp = os.path.realpath(p)
        if rp in seen:
            continue
        seen.add(rp)
        out.append((t, p, cmd))
    return out


def log_line(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except Exception:
        pass


def extract_registry_guards():
    """
    从守卫编写规范注册表提取所有登记的守卫文件名（v0.2 差集检测）
    
    Returns:
        set of 守卫文件名（如 {'session_memory_quality_guard.py', 'dsh_session_anomaly_guard.py', ...}）
    """
    registry_path = os.path.join(
        BASE, "记忆蓝图", "04_系统文件设计", "布洛陀脚本架构设计哲学", "守卫编写规范.md"
    )
    guards = set()
    try:
        with open(registry_path, encoding="utf-8") as f:
            for line in f:
                # 匹配注册表行：| xxx.py | 或 | xxx.sh |
                # 注册表格式：| 守卫文件名 | 辖区 | ...
                m = re.match(r'^\|\s*([a-zA-Z0-9_\u4e00-\u9fff-]+\.(?:py|sh))\s*\|', line)
                if m:
                    guards.add(m.group(1))
    except Exception as e:
        log_line(f"[WARN] 读取注册表失败: {e}")
    return guards


def fixture_covered_guards(items):
    """B 类夹具所覆盖的守卫文件名（v0.2.2·§3.0·5 二选一语义闭环：夹具也算已自测）。

    v0.2.1 缺陷：discovered 只收夹具脚本 basename（run_tests.sh），不映射到它覆盖的守卫
    （changelog_guard.sh），导致有夹具的守卫被误报"无 self-test 违反"。
    推导规则：夹具目录及其父目录内的 .py/.sh 守卫，文件名（kebab↔snake 归一后）
    与目录名互相包含即视为该夹具覆盖——changelog-guard/tests/ → changelog_guard.sh ✓，
    l3_conclusion_guard_tests/ → ~~l3_conclusion_guard.py~~ ✓（该守卫 2026-09-12 已全端下线·上例仅示匹配规则），同目录无关脚本不收。
    """
    covered = set()
    for t, p, cmd in items:
        if t != "B":
            continue
        d = os.path.dirname(os.path.realpath(p))
        for root in (d, os.path.dirname(d)):
            try:
                names = os.listdir(root)
            except OSError:
                continue
            dir_norm = re.sub(r"[\W_]", "", os.path.basename(root)).lower()
            if not dir_norm:
                continue
            for n in names:
                if not (n.endswith(".py") or n.endswith(".sh")):
                    continue
                if n.startswith("run") or ".bak" in n:
                    continue
                stem_norm = re.sub(r"[\W_]", "", n.rsplit(".", 1)[0]).lower()
                if not stem_norm:
                    continue
                if stem_norm in dir_norm or dir_norm in stem_norm:
                    covered.add(n)
    return covered


def main():
    ap = argparse.ArgumentParser(description="守卫家族自测聚合元守卫（v0.2·差集检测）")
    ap.add_argument("--strict", action="store_true", help="任一红→exit 1（默认报告制 exit 0）")
    ap.add_argument("--skip", default="", help="跳过路径匹配此正则的自测（显形计数·不静默）")
    ap.add_argument("--list", action="store_true", help="只列发现清单不执行")
    ap.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT, help="单项超时秒数")
    ap.add_argument("--diff-only", action="store_true", help="只做差集检测（不执行自测）")
    args = ap.parse_args()

    items = discover()

    # v0.2 差集检测：注册表登记 vs 自测清单的差=无自测守卫显形
    # v0.2.2 修正：--self-test 与 tests/ 夹具二选一（§3.0·5 原文）——夹具覆盖的守卫不算违反
    registry_guards = extract_registry_guards()
    discovered_guards = {os.path.basename(p) for t, p, cmd in items}
    no_selftest = registry_guards - discovered_guards - fixture_covered_guards(items)
    
    if args.diff_only:
        if no_selftest:
            print(f"[guard_selftest_check {SELF_VERSION}] 差集检测：{len(no_selftest)} 个守卫无 self-test")
            for g in sorted(no_selftest):
                print(f"  ⚠️ {g}")
        else:
            print(f"[guard_selftest_check {SELF_VERSION}] 差集检测：全部守卫均有 self-test ✅")
        return 1 if no_selftest else 0
    
    if args.list:
        for t, p, cmd in items:
            print(f"[{t}] {os.path.relpath(p, DEV)}  →  {' '.join(cmd[1:])}")
        print(f"共发现 {len(items)} 项自测资产")
        if no_selftest:
            print(f"\n⚠️ 差集检测：{len(no_selftest)} 个守卫无 self-test（注册表有但自测清单无）")
            for g in sorted(no_selftest):
                print(f"  ⚠️ {g}")
        return 0

    skip_re = re.compile(args.skip) if args.skip else None
    ok = bad = skip = 0
    details = []
    for t, p, cmd in items:
        rel = os.path.relpath(p, DEV)
        if skip_re and skip_re.search(rel):
            skip += 1
            details.append(f"SKIP [{t}] {rel}")
            continue
        try:
            # v0.2.4（实锤律+归因律）：字节流捕获 + errors="replace"，⛔ 不用 text=True。
            # 病根：macOS awk 多字节告警往 stderr 吐裸字节，text=True 严格解码抛
            # UnicodeDecodeError → 被下面 except 吞成 "❌ 异常" = 把聚合层自己的解码故障
            # 记在夹具头上（夹具实跑 20/20 绿）。假红比没门禁更糟。
            r = subprocess.run(cmd, capture_output=True, timeout=args.timeout, cwd=os.path.dirname(p))
            out = (r.stdout or b"").decode("utf-8", "replace")
            errb = (r.stderr or b"").decode("utf-8", "replace")
            rc, tail = r.returncode, out.strip().splitlines()[-1:]
            tail = tail[0][:80] if tail else ""
            if rc == 0:
                ok += 1
                details.append(f"✅ [{t}] {rel} :: {tail}")
            else:
                bad += 1
                err = (errb or out).strip().splitlines()
                errtail = err[-1][:120] if err else ""
                details.append(f"❌ [{t}] {rel} rc={rc} :: {errtail}")
        except subprocess.TimeoutExpired:
            bad += 1
            details.append(f"❌ [{t}] {rel} 超时(>{args.timeout}s)")
        except Exception as e:
            bad += 1
            details.append(f"❌ [{t}] {rel} 异常: {type(e).__name__}: {str(e)[:120]}")

    total = ok + bad
    verdict = "全绿" if bad == 0 else f"{bad} 项红"
    print(f"[guard_selftest_check {SELF_VERSION}] 自测资产 {len(items)} 项：✅{ok} ❌{bad} ⏭️{skip} —— {verdict}")
    for d in details:
        print("  " + d)
    
    # v0.2 差集检测结果
    if no_selftest:
        print(f"\n⚠️ 差集检测：{len(no_selftest)} 个守卫无 self-test（§3.0·5 纪律①违反）")
        for g in sorted(no_selftest):
            print(f"  ⚠️ {g}")
    
    log_line(f"[{'OK' if bad == 0 else 'BAD'}] 自测聚合 {len(items)} 项：✅{ok} ❌{bad} ⏭️{skip}")
    log_line("  " + " | ".join(details))
    if no_selftest:
        log_line(f"[WARN] 差集检测：{len(no_selftest)} 个守卫无 self-test: {', '.join(sorted(no_selftest))}")
    
    # v0.2 严格模式：差集非空也视为失败
    # v0.2.3 修正（ZCode·postedit 闸反哺）：strict 只看**执行红**（bad）——差集是历史欠账
    # （49 个存量无自测），计入 strict=欠账清零前 --strict 恒红=所有依赖方（zcode_config_guard
    # postedit 闸等）永久误报=闸不可用（狼来了）。差集显形已有独立通道（--diff-only 退出码）。
    return (1 if bad else 0) if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
