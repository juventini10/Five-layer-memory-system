#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 真源声明：本文件＝pkg_cleanliness_check 的唯一真源（2026-09-19 收编入 开发工具/ 并入 manifest）；
# 布洛陀-安装包/references/scripts/ 下同名文件是发布副本，⛔两处各自演化（改动先改本件，重打包时由发布链导出）。
"""pkg_cleanliness_check.py — 布洛陀安装包「发布卫生」单一真源检查器（Phase X-PKG 第6检查项）

为什么存在（2026-09-17 童灵根治）
--------------------------------
原状：verify.sh §4 用 grep 实现 5 类卫生检查，verify.ps1 §4 只查 1 类（公开署名）——
**双端门禁不对称**，Windows 端等于零卫生防线；且 PS5.1 默认编码读无 BOM UTF-8
中文会假阴性（读成乱码 → 查不到），靠 PS 文本匹配本身就不可靠。
本脚本把口径收口为一份 python 实现，两端 verify 都调它 → 单源·跨端 uniform·不重复造。

⚠️ 本文件必须「脱敏免疫」（2026-09-17 实证）
------------------------------------------
包内存在自动脱敏通道（生成期 deident 全树重写）。初版本文件把私人标识写成字面量，
被自动替换成替换后词 → 检查器自己变成「查替换后词」→ 自检立刻失效（实测：误报 199 件）。
故本文件所有私人标识一律用 **\\u 转义 / 字符串拼接** 构造，使脱敏正则匹配不到
（脱敏只匹配字面词，不匹配转义序列）。⛔ 后人改本文件时不得把它们改回字面量。

检查项（命中任一 = 不干净，exit 1）
----------------------------------
1. 私人称呼（作者口语称谓）      —— 应在派生镜像层由 deident 转公开署名 / 第二人称
2. 用户名（作者系统账户名）      —— 应转「用户名」
3. 备份残留 *.bak*               —— 源侧维护产物·不进发布包（mirror-sync _source_skipped 已排除）
4. 临时残留 _tmp_* / *.tmp*      —— 工具/编辑器临时文件（含 _tmp_<旧名> 违反 doenglingz 唯一名者）
5. 运行时状态点文件              —— .advisory_history.jsonl / .phaseX_last_run.json
                                   （随技能运行生成·含作者绝对路径泄漏风险）
6. 运行时日志 *.log              —— 技能运行生成的日志（如 triwich seal.log 含会话 ID）
                                   应在包源侧排除（.gitignore 已含 **/*.log，但文件系统交付仍会带上）

白名单：发布工具自身（verify.sh/verify.ps1/INSTALL.md/data_contamination_check.py/
        本脚本）注释里必然引用规则词，非内容泄漏。

用法：
  python3 pkg_cleanliness_check.py                     # 默认包根=发布库
  python3 pkg_cleanliness_check.py --pkg-root <路径>
  python3 pkg_cleanliness_check.py --quiet             # 只输出总判定（供 verify 内嵌调用）
退出码：0=干净  1=有污染  2=参数/路径错误
"""
import os
import re
import sys
import argparse
from pathlib import Path

# Windows 控制台 UTF-8 守卫：cp1252 代码页下 print emoji/中文 会 UnicodeEncodeError
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


# 包根=脚本自身位置推导（references/scripts/ → references/ → 包根）·可移植·无作者路径
# 2026-09-30 件4 配套根治：原 else 兜底写死作者侧 `[记忆共享中心]/发布库/五层记忆系统/
#   布洛陀-安装包` —— ① 作者侧绝对路径 ② 且为**已退役**旧包名 ⇒ 包内副本经镜像变换成
#   `[记忆共享中心]/发布库/…`＝端用户侧 100% 不可达**死码**，且被发包自检 ⑪
#   （reference_path_check.py）判「引用落点断头」。改为**同源可移植推导**：非包内运行
#   （如作者侧 开发工具/ 副本）时返回同式推导路径；确需包根时由调用方 `--pkg-root`
#   显式传入（verify.sh / verify.ps1 均传）⇒ 包内不再出现任何作者侧字面量。
DEFAULT_PKG = Path(__file__).resolve().parent.parent.parent

# 发布工具自身：注释/规则串必然含检查词，非泄漏
TOOL_WHITELIST = re.compile(
    r"(verify\.sh|verify\.ps1|INSTALL\.md|data_contamination_check\.py|"
    r"pkg_cleanliness_check\.py)$"
)
TEXT_EXT = {".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".txt", ".html"}
# 2026-09-18 童灵根治：原只列两个 ⇒ 漏 .finalize_last_run.json（clock-loop 第三个运行时
#   点文件·含作者路径+运行时间戳+report_sha8·实证已进包并绕过 §4 检查=假绿）。
#   ⛔与 mirror-sync.py `_source_skipped` 同源——两处必须一起改（判定漂移=假绿）。
RUNTIME_DOTFILES = {".advisory_history.jsonl", ".phaseX_last_run.json", ".finalize_last_run.json"}

# 作者侧实验/运营件名（2026-09-30 补盲区）：作者造评测集/调研/草案的产物，端用户零用途、
#   体量巨大（d4_behavior 数百文件）。DT_SUITE 本就不部署它们，但若物理包源树夹带，
#   原检查器只查文本内容/称呼、不查件名 ⇒ 显式列名兜底（目录名/文件名都查）。
AUTHOR_SIDE_ARTIFACTS = {
    "d4_behavior", "build_d1_manifest.py", "k2_poc_simulate.py",
    "各端切换分发话术.md", "D4-端侧执行交接单.md",
    "Hermes注入配置草案.md", "接入评估",
}

# ── 私人标识：脱敏免疫构造（见头部⚠️）────────────────────────────
# 私人称呼（U+54E5）：用转义序列，使脱敏正则匹配不到本行
PAT_PRIVATE_NAME = "\u54e5"
# 用户名：运行时动态派生（2026-10-05 隐私根治：拼接构造仍含 HANDLE 子串，desensitize-guard 抓=假免疫；
#   动态派生=作者侧零字面量·判据可移植，本机语义不变）
import os as _os, getpass as _gp
PAT_USERNAME = _os.environ.get("USER") or _gp.getuser()

LABEL_PRIVATE_NAME = "私人称呼（作者口语称谓）"
# ── 判据推理留痕（2026-09-30 装机态验证·防后人重提「署名词+人称动词」形态判据）──
# 包内公开署名词（U+76AE U+53D4）全部来自 deident「口语称谓→公开署名」变换（设计内），
#   或作者手写署名性历史标注（令/日期/问/授权）。真泄漏形态=口语称谓裸词（deident 漏网
#   时不会转署名·必被 PAT_PRIVATE_NAME 抓）。故「署名词+须/待/供需/催」形态在包内逻辑上
#   不构成增量真检出，实测反产生假阳性（引号内话术示例/「署名系」分类词均误联）→ ⛔不加。
#   装机态出现署名词=公开署名，无隐私泄漏（无真名/无路径/无私域数据）。

LABEL_USERNAME = "用户名（作者系统账户名·应转「用户名」）"

# 畸形前缀判据（2026-10-10 十一轮·双拼病门禁）
# 病：包内残留 tilde 前缀紧贴占位符，安装器纯 replace 后变 `~//Users/...`（Mac）/
#   `~/C:/Users/...`（Win）⇒ expanduser 静默失效。
# 判据串动态派生（chr 构造），源码零字面量 ⇒ 包内 relocate 兜底洗不掉本判据
#   （防「检查器自己变成查替换后词→自检失效」·头部 L17 警告的同族病）。
TILDE_PAT = "~/" + chr(0x5B) + "记忆共享中心" + chr(0x5D)


def is_bak(name: str) -> bool:
    """备份残留：.bak / .bak-* / .bak_* / *.testbak"""
    return ".bak" in name or ".testbak" in name


def is_tmp(name: str) -> bool:
    """临时残留：_tmp_* / *.tmp / *.tmp.*"""
    return name.startswith("_tmp_") or name.endswith(".tmp") or ".tmp." in name


def is_log(name: str) -> bool:
    """运行时日志：*.log（技能运行生成·可能含会话/路径泄漏）。fixtures/ 下的静态夹具不适用。"""
    return name.endswith(".log")



def check_conffiles(pkg_root: Path):
    """conffiles 条目存在性校验（2026-09-18 群友反馈根治）。

    conffiles 是升级时**三路比较**的清单：条目指向的目标必须真实存在，否则：
      - 无从比较 → 被静默跳过（无害但无用，纯噪声）
      - 更糟：该文件**本该被保护**（用户改过则保留）却因路径写错而按"不在清单内=直接覆盖"
        ⇒ 用户修改被静默覆盖（2026-09-18 实证：`品格设计通用规范.md` 路径漏前缀）
    ⛔ 判据纪律：`~/个人AI档案/X` 必须先替换为**对应根**再查——包内为 `references/templates/X`
       及其扁平化 `references/templates/<basename>`；⛔不可当包根相对路径（否则假全红）。
    """
    bad = []
    cf = Path(pkg_root) / "conffiles"
    if not cf.is_file():
        return None                      # 无 conffiles（非该形态包）→ 不适用
    tpl = Path(pkg_root) / "references" / "templates"
    # 三条腿（2026-09-18 首测假阳性修正）：端用户侧的文件有两个来源——
    #   ① 包内模板复制（references/templates/…）② **安装时由步骤文件生成**（step5 合成等）
    #   ⛔ 只查 ① 会把"生成型"文件误判为幽灵（首测 3 条假阳性实证：CORE.md / 动态状态快照.md /
    #      用户基本规则-详解存档.md 均存在于本机，由步骤生成）⇒ 必须叠加 ③ 步骤文件提及。
    steps_txt = ""
    sdir = Path(pkg_root) / "references" / "steps"
    if sdir.is_dir():
        for f in sdir.glob("*.md"):
            try:
                steps_txt += f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    # 腿③语料（2026-10-07 童灵修盲区）：安装脚本生成目标——
    #   adapters/*/setup.sh（各端部署·如 qodercn 渲染 rules 四件）与根 install_scripts.py（中央安装器）。
    #   实锤盲区：conffiles 4 条 ~/.qoder-cn/rules/*.md 由 adapters/qodercn/setup.sh 的
    #   `for r in core-identity.md core-soul.md core-user.md execution-guidelines.md` 渲染落盘
    #   （QODERCN_HOME 默认 $HOME/.qoder-cn），门卫原只扫 steps/*.md 看不到 ⇒ 误判幽灵。
    install_txt = ""
    for _sp in list(Path(pkg_root).glob("adapters/*/setup.sh")) + [Path(pkg_root) / "install_scripts.py"]:
        if _sp.is_file():
            try:
                install_txt += _sp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    for ln in cf.read_text(encoding="utf-8", errors="replace").splitlines():
        e = ln.strip()
        if not e or e.startswith("#"):
            continue
        rel = e.replace(os.path.expanduser("~/"), "", 1)
        base = os.path.basename(rel)
        # 腿①0（2026-10-05 补·假幽灵根治）：[记忆共享中心]/ 前缀形态 → templates/<去前缀路径>。
        #   实锤：conffiles 行 `[记忆共享中心]/记忆蓝图/04_…/01-品格设计通用规范.md`，
        #   包内源在 templates/记忆蓝图/04_…/ 子树——既非 rel 直拼（带前缀）也非 base 扁平
        #   （templates 直下无同名）⇒ 两腿全空判幽灵（verify 报 FAIL·实为清单-源映射盲区）。
        rel_nc = rel.replace("[记忆共享中心]/", "", 1)
        if (tpl / rel).exists() or (tpl / base).exists() or (tpl / rel_nc).exists():
            continue                     # 腿①：包内模板
        if base in steps_txt or rel in steps_txt:
            continue                     # 腿②：安装步骤生成
        if base in install_txt:
            continue                     # 腿③：安装脚本生成（setup.sh / install_scripts.py）
        bad.append(e)
    return bad


def scan(pkg_root: Path) -> dict:
    hits = {"private_name": [], "username": [], "bak": [], "tmp": [], "runtime": [], "log": [], "pycache": [], "conffiles": [], "author_side": [], "tilde_prefixed": []}
    for dp, dn, fn in os.walk(pkg_root):
        parts = Path(dp).parts
        if ".git" in parts:
            continue
        # 2026-09-18 童灵补（模拟安装实跑发现的门禁盲区）：原 `"__pycache__" in parts: continue`
        #   跳过缓存目录的**内容**，但也因此**不报它的存在**——实证源包夹带 13 目录/133 个 .pyc
        #   （编译缓存不该进包：体积 + 陈旧字节码）。改为「跳过内容但**记录目录本身**」。
        #   mirror-sync._source_skipped 已排除 __pycache__ ⇒ 属**历史残留**，须包侧兜底清理。
        if "__pycache__" in parts:
            rel_d = str(Path(dp).relative_to(pkg_root) if str(dp).startswith(str(pkg_root)) else dp)
            if rel_d not in hits["pycache"]:
                hits["pycache"].append(rel_d)
            continue
        # 作者侧目录：记录并 prune（不进入遍历）
        # 2026-10-03 补门禁盲区：.bak*/.tmp* **目录**此前不被记录（is_bak 只查文件名）——
        #   实证包根夹带 .bak-20261002-premerge/（内含 install_scripts.py 备份）却全绿放行。
        #   与 2026-09-18 __pycache__ 目录盲区同源：跳过内容 ≠ 可以不报它的存在 ⇒ 目录名同样入账并 prune。
        for _adn in list(dn):
            _r = str((Path(dp) / _adn).relative_to(pkg_root))
            if _adn in AUTHOR_SIDE_ARTIFACTS:
                if _r not in hits["author_side"]:
                    hits["author_side"].append(_r)
                dn.remove(_adn)
            elif is_bak(_adn):
                if _r not in hits["bak"]:
                    hits["bak"].append(_r)
                dn.remove(_adn)
            elif is_tmp(_adn):
                if _r not in hits["tmp"]:
                    hits["tmp"].append(_r)
                dn.remove(_adn)
        for f in fn:
            p = Path(dp) / f
            try:
                rel = str(p.relative_to(pkg_root))
            except ValueError:
                rel = str(p)
            if f in AUTHOR_SIDE_ARTIFACTS:
                hits["author_side"].append(rel)
                continue
            if is_bak(f):
                hits["bak"].append(rel)
                continue
            if is_tmp(f):
                hits["tmp"].append(rel)
                continue
            if f in RUNTIME_DOTFILES or (f.startswith('.') and f.endswith('_tmp')) or f.endswith('_runs.jsonl'):  # 2026-10-18 与 mirror-sync._source_skipped 同源补册
                hits["runtime"].append(rel)
                continue
            if is_log(f) and "fixtures" not in parts:
                hits["log"].append(rel)
                continue
            if f.endswith(".lock") or ".zcode" in parts:  # 2026-09-30 类级收口：运行时锁(.git-commit.lock)+端工具workflow缓存(.zcode)——与 mirror-sync._source_skipped 同源
                hits["runtime"].append(rel)
                continue
            if TOOL_WHITELIST.search(rel):
                continue
            if p.suffix.lower() not in TEXT_EXT:
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if PAT_PRIVATE_NAME in t:
                hits["private_name"].append(rel)
            if PAT_USERNAME in t:
                hits["username"].append(rel)
            if TILDE_PAT in t:                # 十一轮：畸形前缀（双拼病门禁）
                hits["tilde_prefixed"].append(rel)
    cf_bad = check_conffiles(pkg_root)
    if cf_bad:
        hits["conffiles"] = list(cf_bad)

    return hits


def fix_pycache(root: Path, hits: dict) -> int:
    """清理 `__pycache__` 目录并返回清理数。

    ## 为什么只有 pycache 能自动清（2026-10-02·Hermes 端实测四踩）
    `hits` 里的 8 类污染中，pycache 是**唯一可安全自动清理**的：
    它是 Python 的**可再生编译缓存**，⛔ 不含任何用户数据或发布内容。
    其余 7 类（.bak / _tmp_ / 运行时点文件 / .log / 私人标识 …）
    都可能夹带用户内容 ⇒ **⛔ 一律只报不动**，删它们是越权。

    ## 为什么需要它（真实事故形态）
    包内任何脚本被运行（跑闸门、跑回归、甚至人手动跑一次）
    ⇒ Python 自动在包内写 `__pycache__`
    ⇒ **闸门制造了它自己要检的缺陷** ⇒ 人被迫反复手工清理 = 假绿治理。
    已修的一层：`release_gates.py` 给子进程设 `PYTHONDONTWRITEBYTECODE`
    （闸门不再自污染）。但**闸门管不住外部调用方**（CI、测试、用户手跑）
    ⇒ 本函数是兜底：可重复执行、零副作用、幂等。

    ⚠️ 用 `shutil.rmtree` 而非 `/usr/bin/trash`：
       本函数只删**可再生缓存**（删了即刻可重建），不走回收站是安全的；
       铁律-005 的 trash 纪律针对的是**可能有价值的内容**。
    """
    import shutil
    n = 0
    for rel in hits.get("pycache", []):
        d = (root / rel) if not os.path.isabs(rel) else Path(rel)
        if d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="布洛陀安装包发布卫生检查（只读·双端单一真源）")
    ap.add_argument("--pkg-root", default=str(DEFAULT_PKG), help="安装包根目录")
    ap.add_argument("--quiet", action="store_true", help="只输出总判定（供 verify 脚本内嵌调用）")
    ap.add_argument("--fix-cache", action="store_true",
                    help="只清理 __pycache__（可再生编译缓存·⛔不动其余 7 类）")
    ap.add_argument("--exclude-runtime", action="store_true",
                    help="装后用户机自检专用（2026-10-22 R9）：runtime/pycache 两类装机过程自身产物不算包卫生缺陷·发版侧⛔不传（检测力度不削弱）")
    args = ap.parse_args()

    root = Path(os.path.expanduser(args.pkg_root))
    if not root.is_dir():
        print(f"[FAIL] 包根不存在: {root}", file=sys.stderr)
        return 2

    hits = scan(root)
    # 🟡 --fix-cache 只清 pycache 一类，其余命中**照报**——
    #    ⛔ 不许"清了一半就说干净"，那是把红读成绿（§1.10 标签真≠诚实）。
    if args.fix_cache and hits.get("pycache"):
        fixed = fix_pycache(root, hits)
        if fixed:
            print(f"  [FIX] 已清理 __pycache__ {fixed} 处（可再生编译缓存）")
        hits = scan(root)   # 重扫：清理后必须以实况判红绿
    # --exclude-runtime（2026-10-22 R9·条文70三态分账的卫生检查时序变体）：
    #   verify 在用户装后跑，装机链 import 生成 pycache、git wrapper 触生 .lock——
    #   这些是**装机过程出生物**不是**发布包夹带物**，混在一起报=把时序差说成卫生缺陷。
    #   发版链（generate_release/author 面）不传此 flag ⇒ 真夹带照样红，检测力度零削弱。
    if args.exclude_runtime:
        hits["runtime"] = []
        hits["pycache"] = []
    labels = {
        "private_name": LABEL_PRIVATE_NAME,
        "username": LABEL_USERNAME,
        "bak": "备份残留 .bak*",
        "tmp": "临时残留 _tmp_*/*.tmp*",
        "runtime": "运行时状态点文件",
        "log": "运行时日志 *.log",
        "author_side": "作者侧实验/运营件（应移出包·端用户零用途）",
        "tilde_prefixed": "畸形前缀占位符（双拼病·装后路径必坏，见 relocate_rules 十一轮注）",
    }
    total = sum(len(v) for v in hits.values())
    if total and not args.quiet:
        for k, label in labels.items():
            if hits[k]:
                print(f"  [FAIL] {label}: {len(hits[k])} 件")
                for r in hits[k][:8]:
                    print(f"         - {r}")
                if len(hits[k]) > 8:
                    print(f"         ... 另有 {len(hits[k]) - 8} 件")
    if total == 0:
        print("  [PASS] 安装包干净度: 无私人称呼/无用户名/无 .bak 残留/无临时残留/无运行时状态文件/无运行时日志")
        return 0
    if hits["pycache"]:
        # 2026-09-18 童灵补：pycache 通道的**输出**（原只加了收集通道，未加打印 ⇒ 报"1 件污染"
        #   却看不出是什么 = 看不懂的红）。独立打印，不依赖上方遍历结构。
        print(f"  [FAIL] 运行期缓存 __pycache__: {len(hits['pycache'])} 件（编译缓存不该进包）")
        for r in hits["pycache"][:8]:
            print(f"         - {r}")
        if len(hits["pycache"]) > 8:
            print(f"         ... 另有 {len(hits['pycache']) - 8} 件")
    if hits.get("conffiles"):
        # 2026-09-18 补：conffiles 幽灵条目（指向本机/包内均无实体）
        print(f"  [FAIL] conffiles 幽灵条目: {len(hits['conffiles'])} 条（指向不存在的目标）")
        for r in hits["conffiles"][:8]:
            print(f"         - {r}")
    print(f"  [FAIL] 安装包干净度: 共 {total} 件污染")
    return 1


if __name__ == "__main__":
    sys.exit(main())
