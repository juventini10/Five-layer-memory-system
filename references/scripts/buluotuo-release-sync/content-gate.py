#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content-gate.py — 布洛陀发布包『内容门禁』
==========================================================

第一性原理
----------
路径脱敏（deident_only）只能把 /Users/<name>/ 换成 ~/，管不住正文里的
真实感数据。发布模板应当只含 {占位符} 与 #000 演示条目——任何带真实
日期戳、连续计数、进度分数、私有实例名、账号名、或长数字块的内容，
都是『开发测试阶段遗留的样例数据』，不应随包分发。

本门禁读取 contamination-signatures.json（遗留样例数据特征库 + 结构检查
配置），扫描发布包，命中即拒绝发布（退出码 1）。两道检查：
1. 文本特征（global_patterns/targets）——遗留样例数据，不应随包分发；
2. 结构检查（structural_checks·仅全包模式生效）——文件系统级缺陷：
   0 字节主名、12 位 hex 副本（同步/写入中断残留）、已知测试残渣名、
   版本三标记漂移（version.md / CHANGELOG 最新条目 / 执行文件 frontmatter）。
这是版本号门禁之外的第二、三道闸——版本号防漂移，文本门禁防样例数据
外泄，结构门禁防损坏包与混合版本发货（2026-09-20 群友 V1.6 实装反馈
驱动新增：其安装包内现 72 个 0 字节主名 + 72 个 hex 副本）。

用法
----
    python3 content-gate.py                 # 扫描发布包，命中则退出码 1
    python3 content-gate.py --package DIR    # 指定包根目录
    python3 content-gate.py --json           # 机器可读输出
    python3 content-gate.py --quiet          # 只输出结论行
    python3 content-gate.py --file X --content Y   # 单文件/待写内容模式
        （release-guard 钩子用·仅文本特征·结构检查不适用）

依赖：仅标准库。特征库默认取同目录 contamination-signatures.json。
发布前强制调用：generate_release.py 生成器已内置本门禁全包扫描为守卫6，
不依赖人记得手动跑。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Windows 控制台默认非 UTF-8(cp1252)，强制 stdout/stderr 用 UTF-8，
# 否则 print emoji/中文(✅🔍⚠️) 会 UnicodeEncodeError 崩溃。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

THIS_DIR = Path(__file__).resolve().parent
DEFAULT_SIGNATURES = THIS_DIR / "contamination-signatures.json"
DEFAULT_PACKAGE = Path(os.path.expanduser(
    "[记忆共享中心]/发布库/五层记忆系统/布洛陀-全平台安装包"
))  # 2026-09-30 退役断线：手跑默认扫唯一发布线（generate_release 显式传参优先）


def _load_signatures(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except (UnicodeDecodeError, ValueError, OSError):
        return ""


def _scan_text(text: str, patterns: list) -> list:
    """返回命中列表：[(pattern_id, desc, 首个命中行号, 命中片段)]。"""
    hits = []
    for pat in patterns:
        rx = re.compile(pat["regex"])
        m = rx.search(text)
        if m:
            line_no = text.count("\n", 0, m.start()) + 1
            snippet = m.group(0).replace("\n", "\\n")[:60]
            hits.append((pat["id"], pat.get("desc", ""), line_no, snippet))
    return hits


# ── 结构检查（文件系统级·仅全包模式）────────────────────────────────────
# 2026-09-20 群友 V1.6 实装反馈驱动：文本特征管不住"文件本身坏了"——
# 0 字节主名 + hex 副本是分发/写入中断的形态，版本三标记漂移是混合版本
# 发货的形态。配置驱动（contamination-signatures.json → structural_checks），
# 新增检查类型只改 JSON 不改代码。

def _walk_files(pkg_root: Path):
    """遍历包内全部文件（排除 .git/__pycache__ 内部件）。"""
    for p in sorted(pkg_root.rglob("*")):
        if not p.is_file():
            continue
        if "__pycache__" in p.parts or ".git" in p.parts:
            continue
        yield p


def _frontmatter_version(text: str):
    m = re.search(r'^version:\s*"?([^"\s]+)"?', text, re.MULTILINE)
    return m.group(1) if m else None


# ── 版本轴判据（2026-10-01 修判据·你裁定"不存在发布前/发布后两个版本状态"）────
# 依据《版本命名规范》：§1 版本串统一纯数字（2026-09-01 已废意象后缀），
# §4.1 发布包内强制同步「version.md / INSTALL / CHANGELOG 顶段头」，其中
# **CHANGELOG 顶段头发布前为 `[未发布]`、发版时 relabel 为 `[X.Y.Z]`**。
# 原实现把 `[未发布]` 当成与 version.md 竞争的"版本串"，于是：
#   ① 任何尚未发布的包 100% 报 version-drift（真包实测 1 红 + 连带 4 处 label-miss）；
#   ② 有人为消红把状态塞进版本串（version.md=2.0.0-dev）⇒ 状态住了两个载体、
#      且 `-dev` 会随归档文件名叫成 `V2.0.0-dev.zip`（用户可见）⇒ 宣称位反而更乱。
# 现判据：状态**只住 CHANGELOG 段头**；版本串必须纯数字 X.Y(.Z)，带后缀即红。
_UNRELEASED_MARKS = {"未发布", "unreleased"}
_VERSION_PURE_RX = re.compile(r"\d+\.\d+(?:\.\d+)?")


def _is_version_str(s):
    """纯数字版本号（X.Y 或 X.Y.Z）为真；含 -dev / + 等状态后缀为假。"""
    return bool(_VERSION_PURE_RX.fullmatch((s or "").strip()))


def _is_unreleased_mark(s):
    """CHANGELOG 顶段头是否为 §4.1 授权的未发布状态词。"""
    return (s or "").strip().lower() in _UNRELEASED_MARKS


def structural_scan(pkg_root: Path, sig: dict) -> list:
    """结构检查：0 字节主名 / 12 位 hex 副本 / 测试残渣名 / 版本三标记漂移。
    返回与文本特征同构的 findings 列表（scope=structural）。"""
    cfg = sig.get("structural_checks", {})
    findings = []

    def add(cid: str, desc: str, rel: str, extra: str = ""):
        findings.append({
            "scope": "structural", "file": rel, "pattern": cid,
            "desc": desc, "line": 0, "snippet": extra,
        })

    # 1) 0 字节主名（allow_names 例外·如 .gitkeep 约定空文件）
    c = cfg.get("zero_byte_files", {})
    if c.get("enabled"):
        allow = set(c.get("allow_names", []))
        for p in _walk_files(pkg_root):
            try:
                if p.stat().st_size == 0 and p.name not in allow:
                    add("zero-byte-file", c.get("desc", ""),
                        str(p.relative_to(pkg_root)), "0 字节")
            except OSError:
                pass

    # 2) 12 位 hex 副本名（同步/写入中断残留）
    c = cfg.get("hash_copy_suffix", {})
    if c.get("enabled"):
        rx = re.compile(c.get("regex", r"-[0-9a-f]{12}\.[^./]+$"))
        for p in _walk_files(pkg_root):
            if rx.search(p.name):
                add("hash-copy-suffix", c.get("desc", ""),
                    str(p.relative_to(pkg_root)), p.name)

    # 3) 已知测试残渣文件名（证据驱动·见一个加一个）
    c = cfg.get("residue_names", {})
    if c.get("enabled"):
        names = set(c.get("names", []))
        for p in _walk_files(pkg_root):
            if p.name in names:
                add("residue-name", c.get("desc", ""),
                    str(p.relative_to(pkg_root)), p.name)

    # 4) 版本三标记一致（version.md = CHANGELOG 顶条 = 执行文件 frontmatter）
    #    2026-10-01 修判据：[未发布] 段头属 §4.1 授权的状态标记，不参与版本串比对；
    #    version.md 带状态后缀（-dev/+…）单独开火 version-state-suffix（一因一报）。
    c = cfg.get("version_consistency", {})
    if c.get("enabled"):
        marks = {}
        vf_name = c.get("version_file", "version.md")
        vf = pkg_root / vf_name
        ssot_pure = True
        if vf.is_file():
            v = _frontmatter_version(_read_text(vf))
            if v:
                marks[vf_name] = v
                if not _is_version_str(v):
                    ssot_pure = False
                    add("version-state-suffix",
                        "版本串必须纯数字 X.Y(.Z)（《版本命名规范》§1 已废一切后缀）。"
                        "发布状态只许住 CHANGELOG 顶段头（§4.1：发布前 [未发布]、发版时 relabel）。"
                        "实测后果：一处 -dev 连带制造 version-drift + 4 处 label-miss 共 5 红，"
                        "并让归档名变成 V2.0.0-dev.zip（用户可见）",
                        vf_name, "version.md=" + v)
        cf_name = c.get("changelog_file", "CHANGELOG.md")
        cf = pkg_root / cf_name
        if cf.is_file():
            m = re.search(r"^##\s*\[([^\]]+)\]", _read_text(cf), re.MULTILINE)
            if m:
                top = m.group(1).strip()
                if _is_unreleased_mark(top):
                    pass  # §4.1 授权的未发布态标记——不参与版本串比对（发版时 relabel 后自动回到比对）
                elif not _is_version_str(top):
                    add("version-changelog-head-bad",
                        "CHANGELOG 顶段头既不是 [未发布] 状态词、也不是纯版本号 X.Y(.Z)——"
                        "升级检测与三标记比对都从这里取号，形态非法＝这两项检查失明",
                        cf_name, "顶段头=[" + top + "]")
                else:
                    marks[cf_name] = top
        ff_name = c.get("frontmatter_file", "")
        if ff_name:
            ff = pkg_root / ff_name
            if ff.is_file():
                v = _frontmatter_version(_read_text(ff))
                if v:
                    marks[ff_name] = v
        if len(marks) >= 2 and len(set(marks.values())) > 1:
            detail = " / ".join(f"{k}={v}" for k, v in marks.items())
            add("version-drift", c.get("desc", ""), detail)

        # 4b) 用户可见版本文案声称必须含 SSOT 版本（label_claims·存在性检查）
        # {version} 占位符 → re.escape 后的 SSOT 版本值（防正则元字符误伤）
        # 2026-10-01：SSOT 含状态后缀时跳过本项——真因已由 version-state-suffix 报出，
        #   此处再报 4 条衍生红只是把"宣称位没抄对"的同一个因拆成噪声（一因一报）。
        #   ⛔ 不是放松：后缀修回纯数字后本项照常全量开火（夹具 T4 证承重）。
        lc = c.get("label_claims", {})
        if lc.get("enabled") and ssot_pure:
            ssot = marks.get(vf_name)
            if ssot:
                for item in lc.get("files", []):
                    rel_path = item.get("path", "")
                    rx_tpl = item.get("regex", "")
                    if not rel_path or not rx_tpl:
                        continue
                    f = pkg_root / rel_path
                    if not f.is_file():
                        continue
                    rx = re.compile(rx_tpl.replace("{version}", re.escape(ssot)))
                    if not rx.search(_read_text(f)):
                        add("version-label-miss", lc.get("_comment", ""), rel_path,
                            f"缺 SSOT 版本声称 {ssot}（regex: {rx_tpl}）")

    # 5) 禁入文件名模式（本体数据类·类级拦截·2026-09-30 隐私抢救根治）
    # 背景：HEXACO 本体数据（作答/向量/观察者/校准/互照报告）曾共 142 件漏入 git、
    #       616 件滞留包内——根因=门禁只认「模板样例数据」特征，不认「作者本体数据类文件名」。
    # 判据：类级正则（不含具体日期/批次）→ 未来任何批次的同类文件自动拦截，不靠人工逐次清理
    #       （配套：.gitignore v4 全局同源规则 + 源侧隔离，三处同源防复发）。
    c = cfg.get("forbidden_name_patterns", {})
    if c.get("enabled"):
        for rule in c.get("rules", []):
            rx = re.compile(rule.get("regex", r"(?!x)x"))
            for p in _walk_files(pkg_root):
                if rx.search(p.name):
                    add(rule.get("id", "forbidden-name"),
                        rule.get("desc", c.get("desc", "")),
                        str(p.relative_to(pkg_root)), p.name)

    return findings


def personal_path_findings(pkg_root: Path) -> list:
    """个人路径白名单对账（v1.3.0·2026-09-20·事前变换漏网的出包机械拦截层）。

    背景：content-gate 特征库不含「[记忆共享中心]」路径字面量（2026-09-20 16:23 实锤）
    ——变换规则(relocate/deident)漏新形态时，出包环节此前零机械拦截。
    白名单外新文件含「[记忆共享中心]」→ findings（拒发）。
    白名单: personal-path-whitelist.json（当日人工定性结论固化·53 文件四类）。
    判据单一真源 = personal_path_audit.scan（同目录·命令行/本门禁两入口共用）。
    fail-closed：审计器缺失或白名单缺失 = 返回 findings 拒发（拒绝盲放）。
    """
    try:
        import personal_path_audit
    except ImportError:
        return [{"pattern": "personal_path_audit_missing", "file": "<gate>",
                 "desc": "个人路径审计器缺失——发布机必须部署 personal_path_audit.py（拒发）"}]
    wl_path = Path(__file__).resolve().parent / "personal-path-whitelist.json"
    if not wl_path.exists():
        return [{"pattern": "personal_path_whitelist_missing", "file": "<gate>",
                 "desc": f"白名单不存在: {wl_path}——拒绝盲放（先定性建白名单再出包）"}]
    try:
        hits = personal_path_audit.scan(str(pkg_root))
        allowed = set(json.load(open(wl_path, encoding="utf-8")).get("files", {}))
    except Exception as e:
        return [{"pattern": "personal_path_audit_broken", "file": "<gate>",
                 "desc": f"个人路径审计器故障: {e}——fail-closed 拒发（修好再出包）"}]
    return [{"pattern": "personal_path_new_file", "file": f,
             "desc": f"白名单外新出现「[记忆共享中心]」×{n}——定性后:合法保留入白名单(留痕)/否则修源侧走 relocate 占位化"}
            for f, n in sorted(hits.items()) if f not in allowed]


def scan_all(pkg_root: Path) -> list:
    """完整包扫描 = 文本特征 + 结构检查 + 个人路径白名单对账。发布前门禁总入口
    （generate_release.py 守卫6 调用；返回 findings 列表，空=通过）。"""
    sig = _load_signatures(DEFAULT_SIGNATURES)
    return scan_package(pkg_root, sig) + structural_scan(pkg_root, sig) + personal_path_findings(pkg_root)


def scan_package(pkg_root: Path, sig: dict) -> list:
    """扫描整个包，返回命中记录列表。"""
    findings = []

    # 1) 全局特征：扫所有 .md（作者署名类正当归属由特征库精确措辞规避）
    global_patterns = sig.get("global_patterns", [])
    if global_patterns:
        for md in sorted(pkg_root.rglob("*.md")):
            if "__pycache__" in md.parts or ".git" in md.parts:
                continue
            text = _read_text(md)
            for pid, desc, ln, snip in _scan_text(text, global_patterns):
                findings.append({
                    "scope": "global",
                    "file": str(md.relative_to(pkg_root)),
                    "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                })

    # 2) 定点特征：按 target 的 file / file_glob 精确扫描
    for target in sig.get("targets", []):
        patterns = target.get("patterns", [])
        rels = []
        if "file" in target:
            rels = [target["file"]]
        elif "file_glob" in target:
            rels = [str(p.relative_to(pkg_root))
                    for p in sorted(pkg_root.glob(target["file_glob"]))]
        for rel in rels:
            fpath = pkg_root / rel
            if not fpath.exists():
                continue
            text = _read_text(fpath)
            for pid, desc, ln, snip in _scan_text(text, patterns):
                findings.append({
                    "scope": "target",
                    "file": rel,
                    "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                })
    # 3) 结构检查（文件系统级·仅全包模式）：0字节/hash副本/测试残渣/版本漂移
    findings.extend(structural_scan(pkg_root, sig))
    return findings


def main():
    parser = argparse.ArgumentParser(description="布洛陀发布包 内容门禁")
    parser.add_argument("--package", default=str(DEFAULT_PACKAGE),
                        help="发布包根目录")
    parser.add_argument("--file", default=None,
                        help="单文件模式：只扫这一个文件（pre_tool_call 拦截用，"
                             "避免扫全包把历史遗留当成本次写的风险）")
    parser.add_argument("--content", default=None,
                        help="待写内容模式：直接扫这段即将写入的内容（write_file 的"
                             "content 参数），无需文件已存在即可拦'将要写的内容'")
    parser.add_argument("--signatures", default=str(DEFAULT_SIGNATURES),
                        help="特征库 JSON 路径")
    parser.add_argument("--json", action="store_true", help="机器可读输出")
    parser.add_argument("--quiet", action="store_true", help="只输出结论行")
    parser.add_argument("--self-test", action="store_true",
                        help="版本轴判据自测：正例必绿 + 4 类负例必红 + 3 处变异证承重")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_version_selftest())

    sig_path = Path(os.path.expanduser(args.signatures))

    if not sig_path.exists():
        print(f"❌ 特征库不存在: {sig_path}")
        sys.exit(2)

    sig = _load_signatures(sig_path)

    # 待写内容模式优先：直接扫即将写入的内容（write_file 的 content 参数）
    # 无需文件存在即可拦'将要写的内容'，是 pre_tool_call 拦新文件的正确姿势。
    # 注意：必须优先于 --file 分支——release-guard 会同时传 --content 和 --file
    # （--file 仅用于 target 文件名匹配），若先判 --file 会因文件不存在而误放行。
    if args.content is not None:
        text = args.content
        findings = []
        for pat in sig.get("global_patterns", []):
            for pid, desc, ln, snip in _scan_text(text, [pat]):
                findings.append({
                    "scope": "global", "file": args.file or "<pending-write>",
                    "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                })
        for target in sig.get("targets", []):
            patterns = target.get("patterns", [])
            tf = target.get("file")
            if tf and args.file and os.path.basename(args.file) == os.path.basename(tf):
                for pid, desc, ln, snip in _scan_text(text, patterns):
                    findings.append({
                        "scope": "target", "file": args.file,
                        "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                    })
    # 单文件模式：只扫本次要写的文件（release-guard pre_tool_call 调用）
    elif args.file:
        fpath = Path(os.path.expanduser(args.file))
        if not fpath.is_file():
            # pre_tool_call 在 write_file 执行前触发：新建文件尚不存在，
            # 无内容可扫 → 放行（失败放行原则，不误拦未写出的新文件）
            print(f"✅ 内容门禁通过 — 目标文件尚未写出，无可扫内容（特征库 v{sig.get('version')}）")
            sys.exit(0)
        text = _read_text(fpath)
        findings = []
        for pat in sig.get("global_patterns", []):
            for pid, desc, ln, snip in _scan_text(text, [pat]):
                findings.append({
                    "scope": "global", "file": str(fpath),
                    "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                })
        for target in sig.get("targets", []):
            patterns = target.get("patterns", [])
            tf = target.get("file")
            if tf and fpath.name == os.path.basename(tf):
                for pid, desc, ln, snip in _scan_text(text, patterns):
                    findings.append({
                        "scope": "target", "file": str(fpath),
                        "pattern": pid, "desc": desc, "line": ln, "snippet": snip,
                    })
    else:
        pkg_root = Path(os.path.expanduser(args.package))
        if not pkg_root.is_dir():
            print(f"❌ 包根目录不存在: {pkg_root}")
            sys.exit(2)
        findings = scan_package(pkg_root, sig) + personal_path_findings(pkg_root)

    if args.json:
        print(json.dumps({
            "package": str(pkg_root),
            "signatures_version": sig.get("version"),
            "clean": len(findings) == 0,
            "hit_count": len(findings),
            "findings": findings,
        }, ensure_ascii=False, indent=2))
        sys.exit(1 if findings else 0)

    if not findings:
        print(f"✅ 内容门禁通过 — 未发现遗留样例数据（特征库 v{sig.get('version')}）")
        sys.exit(0)

    if not args.quiet:
        print(f"🚫 内容门禁拦截 — 发现 {len(findings)} 处问题（样例数据/结构缺陷）：\n")
        for f in findings:
            loc = f["file"] + (f":{f['line']}" if f.get("line") else "")
            print(f"  [{f['pattern']}] {loc}")
            print(f"      {f['desc']}")
            if f.get("snippet"):
                print(f"      命中: {f['snippet']}")
    print(f"\n🚫 拒绝发布：请先修复上述问题（命中 {len(findings)} 处）")
    sys.exit(1)


# ── 版本轴判据自测（2026-10-01 新增）─────────────────────────────────────
# 三态纪律（门禁必须自证有牙）：
#   正例必绿＝不出现"判据恒红"（否则真包永远红→红警疲劳→真漂移被淹没）；
#   负例必红＝不出现"判据恒绿"（假绿比假红危险：它看起来是"检查跑过了"）；
#   变异必红＝把判据分支逐个短路后，对应正/负例必须翻转（证明这几行真承重，
#   不是注释装饰）。⛔ 变异体若与源文件逐字相同＝自测恒真（本函数显式拒绝该形态）。
_SELFTEST_SIG = {
    "structural_checks": {
        "version_consistency": {
            "enabled": True,
            "version_file": "version.md",
            "changelog_file": "CHANGELOG.md",
            "frontmatter_file": "",
            "desc": "三标记一致",
            "label_claims": {
                "enabled": True, "_comment": "宣称位存在性",
                "files": [{"path": "INSTALL.md",
                           "regex": "布洛陀[\\s]*{version}", "desc": "入口标题"}],
            },
        }
    }
}


def _mk_fixture(root, ver, cl_head, install_claim):
    """造最小假包：version.md + CHANGELOG 顶段头 + INSTALL 宣称位。"""
    p = Path(root)
    (p / "version.md").write_text('version: "%s"\n' % ver, encoding="utf-8")
    (p / "CHANGELOG.md").write_text("# 变更记录\n\n## [%s] — 2026-10-01\n\n### 新增\n- x\n"
                                    % cl_head, encoding="utf-8")
    (p / "INSTALL.md").write_text("# 🏮 布洛陀 %s — 多平台安装入口\n" % install_claim,
                                  encoding="utf-8")
    return p


def _ver_findings(scan_fn, root):
    got = scan_fn(Path(root), _SELFTEST_SIG)
    return sorted(f["pattern"] for f in got if f["pattern"].startswith("version-"))


def _version_selftest() -> int:
    import tempfile
    here = Path(__file__).resolve()
    src = here.read_text(encoding="utf-8")

    def _load(mut_from=None, mut_to=None):
        code = src
        if mut_from is not None:
            n = src.count(mut_from)
            if n != 1:
                raise AssertionError("变异锚点命中 %d 次（应为 1）：%r" % (n, mut_from[:40]))
            code = src.replace(mut_from, mut_to)
            if code == src:
                raise AssertionError("变异体与源逐字相同＝自测恒真，拒绝出结论")
        ns = {"__name__": "content_gate_selftest_ns", "__file__": str(here)}
        exec(compile(code, "<cg-selftest>", "exec"), ns)
        return ns["structural_scan"]

    cases = [
        # (名, version.md, CHANGELOG 段头, INSTALL 宣称, 期望开火的 pattern 列表)
        ("T1 未发布态正例（§4.1 状态词不参与比对）", "2.0.0", "未发布", "2.0.0", []),
        ("T2 版本串带状态后缀 -dev", "2.0.0-dev", "未发布", "2.0.0",
         ["version-state-suffix"]),
        ("T3 真漂移不被豁免吞（CHANGELOG 已定号且≠真源）", "2.0.0", "1.7.2", "2.0.0",
         ["version-drift"]),
        ("T4 纯号下宣称位撒谎仍开火（豁免≠总关）", "2.0.0", "未发布", "1.7.2",
         ["version-label-miss"]),
        ("T5 段头形态非法（既非状态词也非版本号）", "2.0.0", "进行中", "2.0.0",
         ["version-changelog-head-bad"]),
    ]
    fails = 0
    scan = _load()
    with tempfile.TemporaryDirectory() as td:
        print("── 版本轴判据自测 ──")
        for name, ver, head, claim, expect in cases:
            root = _mk_fixture(td, ver, head, claim)
            got = _ver_findings(scan, root)
            ok = got == sorted(expect)
            print(("  ✅ " if ok else "  ❌ ") + name +
                  " → 开火=%s 期望=%s" % (got or "无", expect or "无"))
            if not ok:
                fails += 1
        # 变异三向：逐条短路判据分支，对应用例必须翻转
        # ⚠️ 变异锚点必须拆成相邻字面量拼接写：整行写死时本函数自身就是源码里的
        #    第二处命中（2026-10-01 自测实跑抓到 count=2），锚点计数判据会失真。
        muts = [
            ("M1 未发布豁免短路",
             "                if _is_unreleased_" "mark(top):",
             "                if False:",
             ("T1", "2.0.0", "未发布", "2.0.0", "version-drift")),
            ("M2 状态后缀判据短路",
             "                if not _is_version_" "str(v):",
             "                if False:",
             ("T2", "2.0.0-dev", "未发布", "2.0.0", "version-state-suffix")),
            ("M3 宣称位腿短路", "        if lc.get(\"enabled\") and ssot_pure:",
             "        if False:", ("T4", "2.0.0", "未发布", "1.7.2", "version-label-miss")),
        ]
        print("── 变异测试（证明判据分支承重）──")
        for mname, a, b, (_t, ver, head, claim, should_disappear) in muts:
            try:
                mscan = _load(a, b)
            except AssertionError as exc:
                print("  ❌ %s — 变异锚点失效：%s" % (mname, exc))
                fails += 1
                continue
            root = _mk_fixture(td, ver, head, claim)
            got = _ver_findings(mscan, root)
            ok = should_disappear not in got
            print(("  ✅ " if ok else "  ❌ ") + "%s — 短路后 %s 应消失，实得 %s"
                  % (mname, should_disappear, got or "无"))
            if not ok:
                fails += 1
    print(("\n🟢 版本轴自测全绿（用例 5 + 变异 3）" if fails == 0
           else "\n🔴 版本轴自测 %d 项失败——判据有假绿/假红，勿据此发货" % fails))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    main()

# ── 布洛陀发布包·路径覆盖层 ──────────────────────────────────
# 装包时安装器生成本机实况的 path_override.py，把上面这些
# **作者态落点**（"[记忆共享中心]/…"）改成本机值或哨兵路径。
# ⛔ 本块必须留在**所有模块级常量之后**——插早了会被后面的定义覆盖回去。
# 作者侧运行（开发工具/ 下）时 path_overlay 不可达 ⇒ ImportError ⇒ 原样运行。
try:
    from path_overlay import apply_override
    apply_override(globals())
except ImportError:
    pass